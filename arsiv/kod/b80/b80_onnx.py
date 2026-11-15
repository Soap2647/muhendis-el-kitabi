# -*- coding: utf-8 -*-
# b80_onnx.py: BatchNorm katlama, ONNX disa aktarma, ONNX Runtime
# eslesme testi ve statik int8 kuantizasyon (QDQ). Kalibrasyon
# verisi egitimden ve test kumelerinden ayri bir tohumdan gelir.
import os
import time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import onnx
import onnxruntime as ort
from onnxruntime.quantization import (
    quantize_static,
    CalibrationDataReader,
    QuantType,
    QuantFormat,
)
import logging

logging.basicConfig(level=logging.ERROR)
ort.set_default_logger_severity(3)
from b80_veri import veri_seti, EGITIM, NOMINAL, DRIFT
from b67_04_yolo_mini import MiniYolo, degerlendir, decode, G, A, C

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ONNX32 = os.path.join(KLASOR, "yolo_fp32.onnx")
ONNX8 = os.path.join(KLASOR, "yolo_int8.onnx")


def katla(conv, bn):
    """Conv2d (bias yok) + BatchNorm2d (eval) -> (W', b').
    s = gamma / sqrt(var + eps); W' = W * s; b' = beta - mu * s."""
    s = bn.weight / torch.sqrt(bn.running_var + bn.eps)
    w = conv.weight * s[:, None, None, None]
    b = bn.bias - bn.running_mean * s
    return w.detach(), b.detach()


class Dagitim(nn.Module):
    """BN'siz, yalnizca Conv + ReLU + 1x1 bas.

    Cikti: (B, A*(5+C), G, G)."""

    def __init__(self, model):
        super().__init__()
        self.convs = nn.ModuleList()
        self.adim = []
        for blk in model.govde:
            conv, bn = blk[0], blk[1]
            w, b = katla(conv, bn)
            c = nn.Conv2d(
                conv.in_channels,
                conv.out_channels,
                3,
                conv.stride,
                1,
                bias=True,
            )
            c.weight.data.copy_(w)
            c.bias.data.copy_(b)
            self.convs.append(c)
        self.bas = nn.Conv2d(64, A * (5 + C), 1)
        self.bas.load_state_dict(model.bas.state_dict())

    def forward(self, x):
        for c in self.convs:
            x = F.relu(c(x))
        return self.bas(x)


def ham_to_cikti(ham):
    """(B, A*(5+C), G, G) -> (B, G, G, A, 5+C), b67 ile ayni duzen."""
    b = ham.shape[0]
    return ham.reshape(b, A, 5 + C, G, G).transpose(0, 3, 4, 1, 2)


class Veri(CalibrationDataReader):
    """Kalibrasyon: egitimden ayri tohum, 200 sahne (sadece girdi)."""

    def __init__(self, X):
        self.X = X
        self.i = 0

    def get_next(self):
        if self.i >= len(self.X):
            return None
        girdi = {"girdi": self.X[self.i : self.i + 1]}
        self.i += 1
        return girdi


def ort_oturum(yol, threads=4):
    opt = ort.SessionOptions()
    opt.intra_op_num_threads = threads
    opt.inter_op_num_threads = 1
    return ort.InferenceSession(
        yol, opt, providers=["CPUExecutionProvider"]
    )


def ort_tahmin(oturum, X):
    """ONNX ciktisi -> b67 decode'u ile kutular."""
    ciktilar = []
    ad = oturum.get_inputs()[0].name
    for i in range(0, len(X), 64):
        ham = oturum.run(None, {ad: X[i : i + 64]})[0]
        ciktilar.append(ham_to_cikti(ham))
    return decode(np.concatenate(ciktilar))


def main():
    base = MiniYolo()
    base.load_state_dict(
        torch.load(
            os.path.join(KLASOR, "yolo_t1.pt"), map_location="cpu"
        )
    )
    base.eval()
    dag = Dagitim(base).eval()
    Xte, Yte = veri_seti(500, seed=777, ayar=NOMINAL)
    Xdr, Ydr = veri_seti(500, seed=888, ayar=DRIFT)
    Xod, Yod = veri_seti(500, seed=999, ayar=NOMINAL, kus=1)
    Xcal, _ = veri_seti(200, seed=4242, ayar=EGITIM)

    # 1) BN katlama dogrulamasi (PyTorch, CPU)
    with torch.no_grad():
        x = torch.tensor(Xte[:200])
        a = base(x)
        b = ham_to_cikti(dag(x).numpy())
        a = a.numpy()
    fark = float(np.abs(a - b).max())
    print("BN katlama maks |fark| = %.2e" % fark)

    # 2) ONNX disa aktarma
    dummy = torch.zeros(1, 1, 96, 96)
    torch.onnx.export(
        dag,
        dummy,
        ONNX32,
        input_names=["girdi"],
        output_names=["cikti"],
        opset_version=17,
        dynamic_axes={
            "girdi": {0: "n", 2: "h", 3: "w"},
            "cikti": {0: "n", 2: "oh", 3: "ow"},
        },
        dynamo=False,
    )
    onnx.checker.check_model(onnx.load(ONNX32))
    print("ONNX fp32 boyut: %d bayt" % os.path.getsize(ONNX32))

    # 3) Statik int8 kuantizasyon (QDQ, kanal basina agirlik)
    quantize_static(
        ONNX32,
        ONNX8,
        Veri(Xcal),
        quant_format=QuantFormat.QDQ,
        per_channel=True,
        weight_type=QuantType.QInt8,
        activation_type=QuantType.QUInt8,
    )
    print("ONNX int8 boyut: %d bayt" % os.path.getsize(ONNX8))

    # 4) Dogruluk: PyTorch, ONNX fp32, ONNX int8
    satirlar = []
    sess32 = ort_oturum(ONNX32)
    sess8 = ort_oturum(ONNX8)
    ps = {}
    for ad, (X, Y) in {
        "test": (Xte, Yte),
        "drift": (Xdr, Ydr),
        "ood": (Xod, Yod),
    }.items():
        with torch.no_grad():
            pt = decode(
                np.concatenate(
                    [
                        base(torch.tensor(X[i : i + 64])).numpy()
                        for i in range(0, len(X), 64)
                    ]
                )
            )
        p32 = ort_tahmin(sess32, X)
        p8 = ort_tahmin(sess8, X)
        for yontem, pred in [
            ("pytorch", pt),
            ("onnx_fp32", p32),
            ("onnx_int8", p8),
        ]:
            m50, m5095 = degerlendir(pred, Y)
            satirlar.append((yontem, ad, m50, m5095))
            print(
                "%-10s %-6s mAP@0.5=%.4f  mAP@[.5:.95]=%.4f"
                % (yontem, ad, m50, m5095)
            )
        ps[ad] = (pt, p32, p8)
    # ONNX fp32 ile PyTorch arasindaki kutu farki (test)
    d = 0.0
    for (kp, sp, cp), (kq, sq, cq) in zip(
        ps["test"][0], ps["test"][1]
    ):
        if len(kp) and len(kq) and len(kp) == len(kq):
            d = max(d, float(np.abs(kp - kq).max()))
    print("test: ONNX fp32 ile PyTorch kutu maks farki = %.2e" % d)
    boyut = {
        "pytorch": os.path.getsize(
            os.path.join(KLASOR, "yolo_t1.pt")
        ),
        "onnx_fp32": os.path.getsize(ONNX32),
        "onnx_int8": os.path.getsize(ONNX8),
    }
    with open(
        os.path.join(VERI, "b80_onnx.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("yontem,kume,map50,map5095,boyut_bayt\n")
        for yontem, ad, m50, m5095 in satirlar:
            f.write(
                "%s,%s,%.4f,%.4f,%d\n"
                % (yontem, ad, m50, m5095, boyut[yontem])
            )


if __name__ == "__main__":
    main()
