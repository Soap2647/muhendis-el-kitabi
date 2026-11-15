# -*- coding: utf-8 -*-
"""Bolum 75: ONNX disa aktarma, ONNX Runtime ile sayisal eslesme,
BatchNorm katlama (sifirdan) ve calisma zamani graf optimizasyonu."""

import os
import numpy as np
import torch
import torch.nn as nn
import onnx
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType
from b75_ortak import veri, mlp_t, egit, dogruluk

KLASOR = "C:/Users/merty/AppData/Local/Temp/b75/onnx"


def bn_katla(conv, bn):
    """Conv2d + BatchNorm2d (egitim sonrasi, eval modu) -> tek Conv2d.
    s = gamma / sqrt(var + eps); W' = W * s; b' = (b - mu) * s + beta.
    """
    s = bn.weight / torch.sqrt(bn.running_var + bn.eps)
    yeni = nn.Conv2d(
        conv.in_channels,
        conv.out_channels,
        conv.kernel_size,
        stride=conv.stride,
        padding=conv.padding,
        bias=True,
    )
    b = (
        conv.bias
        if conv.bias is not None
        else torch.zeros_like(bn.running_mean)
    )
    with torch.no_grad():
        yeni.weight.copy_(conv.weight * s.view(-1, 1, 1, 1))
        yeni.bias.copy_((b - bn.running_mean) * s + bn.bias)
    return yeni


def op_say(yol):
    m = onnx.load(yol)
    sayac = {}
    for n in m.graph.node:
        sayac[n.op_type] = sayac.get(n.op_type, 0) + 1
    return sayac


def ort_calistir(yol, X):
    s = ort.InferenceSession(yol, providers=["CPUExecutionProvider"])
    ad = s.get_inputs()[0].name
    return s.run(None, {ad: X})[0]


def mlp_testi():
    print("== 1) MLP: PyTorch -> ONNX -> ONNX Runtime ==")
    Xtr, ytr, Xte, yte = veri(0)
    m = mlp_t(0)
    egit(m, Xtr, ytr, tohum=0)
    m.eval()
    yol = os.path.join(KLASOR, "mlp.onnx")
    torch.onnx.export(
        m,
        torch.randn(1, 64),
        yol,
        opset_version=17,
        input_names=["giris"],
        output_names=["cikis"],
        dynamic_axes={"giris": {0: "B"}, "cikis": {0: "B"}},
        dynamo=False,
    )
    onnx.checker.check_model(onnx.load(yol))
    with torch.no_grad():
        py = m(Xte).numpy()
    ox = ort_calistir(yol, Xte.numpy())
    print("en buyuk mutlak fark: %.3e" % np.abs(py - ox).max())
    print(
        "cikti buyuklugu max|y|: %.3f  bagil fark: %.3e"
        % (np.abs(py).max(), np.abs(py - ox).max() / np.abs(py).max())
    )
    print(
        "ONNX dogruluk: %.4f  PyTorch dogruluk: %.4f"
        % (
            (ox.argmax(1) == yte.numpy()).mean(),
            dogruluk(m, Xte, yte),
        )
    )
    print("op sayilari:", op_say(yol))
    yol8 = os.path.join(KLASOR, "mlp_int8.onnx")
    quantize_dynamic(yol, yol8, weight_type=QuantType.QInt8)
    o8 = ort_calistir(yol8, Xte.numpy())
    print(
        "ORT dinamik int8 dogruluk: %.4f  boyut: %d -> %d bayt"
        % (
            (o8.argmax(1) == yte.numpy()).mean(),
            os.path.getsize(yol),
            os.path.getsize(yol8),
        )
    )


def bn_testi():
    print("== 2) Conv + BatchNorm katlama ==")
    torch.manual_seed(0)
    conv = nn.Conv2d(1, 8, 3, padding=1)
    bn = nn.BatchNorm2d(8)
    with torch.no_grad():  # egitilmis gibi ayarla
        bn.weight.uniform_(0.5, 1.5)
        bn.bias.uniform_(-0.3, 0.3)
        bn.running_mean.uniform_(-0.2, 0.2)
        bn.running_var.uniform_(0.5, 2.0)
    bn.eval()
    conv.eval()
    kat = bn_katla(conv, bn).eval()
    x = torch.randn(4, 1, 8, 8)
    with torch.no_grad():
        fark = (bn(conv(x)) - kat(x)).abs().max().item()
    print("katlama oncesi/sonrasi en buyuk fark: %.3e" % fark)
    yol_a = os.path.join(KLASOR, "conv_bn.onnx")
    yol_b = os.path.join(KLASOR, "conv_katli.onnx")
    seq = nn.Sequential(conv, bn)
    torch.onnx.export(
        seq,
        x,
        yol_a,
        opset_version=17,
        dynamo=False,
        do_constant_folding=False,
    )
    torch.onnx.export(
        kat,
        x,
        yol_b,
        opset_version=17,
        dynamo=False,
        do_constant_folding=False,
    )
    print("ONNX (katlanmamis):", op_say(yol_a))
    print("ONNX (katli)      :", op_say(yol_b))
    so = ort.SessionOptions()
    so.graph_optimization_level = (
        ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    )
    so.optimized_model_filepath = os.path.join(
        KLASOR, "conv_bn_opt.onnx"
    )
    ort.InferenceSession(
        yol_a, so, providers=["CPUExecutionProvider"]
    )
    print(
        "ORT ENABLE_ALL sonrasi (katlanmamis):",
        op_say(so.optimized_model_filepath),
    )
    oa = ort_calistir(yol_a, x.numpy())
    ob = ort_calistir(yol_b, x.numpy())
    print(
        "ORT: katlanmamis ile katli fark: %.3e"
        % np.abs(oa - ob).max()
    )


if __name__ == "__main__":
    torch.set_num_threads(4)
    os.makedirs(KLASOR, exist_ok=True)
    mlp_testi()
    bn_testi()
