# -*- coding: utf-8 -*-
"""
Bölüm 70 - Aşağı akış görevi: bir paragrafın hangi KISIMDAN geldiğini
sınıflandırmak (15 sınıf, Kısım I..XV). Etiket: %% kisim_no ön
bilgisi.

Modlar:
  sifirdan  : aynı mimari, rastgele ilk değerler, tüm ağırlıklar
  eğitilir
  tam       : ön-eğitimli GPT, tüm ağırlıklar eğitilir (tam ince ayar)
  dogrusal  : ön-eğitimli GPT donuk, yalnızca sınıflandırma başlığı
  (linear probe)
  lora      : ön-eğitimli GPT donuk, LoRA (A, B) + başlık eğitilir

Kullanım: python g06_ince_ayar.py --mod lora --r 8 --lr 1e-3 --seed 0
Sonuç satırı: sonuc_ince_ayar.jsonl (ek yazılır).
"""

import argparse, json, math, os, time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import f1_score
from bpe_sifirdan import BPE
from gpt_b70 import MiniGPT
from lora_b70 import lora_uygula, egitilebilir_say, adaptor_durumu

K = os.path.dirname(os.path.abspath(__file__))
V, CTX, SINIF = 2149, 128, 15
cihaz = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def veri_hazirla():
    par = json.load(
        open(os.path.join(K, "paragraflar.json"), encoding="utf-8")
    )
    bol = json.load(
        open(os.path.join(K, "bolum_bolme.json"), encoding="utf-8")
    )
    bj = json.load(
        open(os.path.join(K, "bpe_b70.json"), encoding="utf-8")
    )
    b = BPE.yukle(bj["alfabe"], bj["kurallar"])
    out = {}
    for anahtar in ("egitim", "dogrulama", "test"):
        idler = bol[anahtar]
        X = torch.zeros(len(idler), CTX, dtype=torch.long)
        M = torch.zeros(len(idler), CTX)
        y = torch.zeros(len(idler), dtype=torch.long)
        for j, i in enumerate(idler):
            t = b.kodla(par[i]["metin"])[:CTX]
            X[j, : len(t)] = torch.tensor(t)
            M[j, : len(t)] = 1.0
            y[j] = par[i]["kisim"]
        out[anahtar] = (X, M, y)
    return out


def taban_yukle():
    ck = torch.load(
        os.path.join(K, "gpt_ana_0.pt"),
        map_location="cpu",
        weights_only=True,
    )
    m = MiniGPT(
        V,
        ctx=ck["ctx"],
        d=ck["d"],
        L=ck["L"],
        bas=ck["bas"],
        dusme=0.1,
    )
    m.load_state_dict(ck["state"])
    return m


class Siniflandirici(nn.Module):
    def __init__(self, gpt):
        super().__init__()
        self.gpt = gpt
        self.baslik = nn.Linear(gpt.tok.embedding_dim, SINIF)

    def forward(self, x, m):
        h = self.gpt.gizli(x)  # (B, T, d)
        m = m.unsqueeze(-1)
        ortalama = (h * m).sum(1) / m.sum(1).clamp(
            min=1.0
        )  # maskeli ortalama
        return self.baslik(ortalama)


def modeli_kur(mod, r, seed, alpha=16.0):
    torch.manual_seed(seed)
    if mod == "sifirdan":
        gpt = MiniGPT(V, ctx=CTX, d=128, L=4, bas=4, dusme=0.1)
    else:
        gpt = taban_yukle()
    sn = Siniflandirici(gpt)
    if mod == "dogrusal":
        for p in sn.gpt.parameters():
            p.requires_grad = False
    elif mod == "lora":
        for p in sn.gpt.parameters():
            p.requires_grad = False
        lora_uygula(sn.gpt, r, alpha)
        for ad, p in sn.gpt.named_parameters():
            if ad.endswith((".A", ".B")):
                p.requires_grad = True
    return sn.to(cihaz)


@torch.no_grad()
def dogruluk(sn, X, M, y):
    sn.eval()
    tahmin = []
    for i in range(0, len(X), 128):
        tahmin.append(
            sn(X[i : i + 128].to(cihaz), M[i : i + 128].to(cihaz))
            .argmax(1)
            .cpu()
        )
    sn.train()
    t = torch.cat(tahmin)
    return (t == y).float().mean().item(), f1_score(
        y.numpy(), t.numpy(), average="macro"
    )


@torch.no_grad()
def dil_ppl(gpt, bloklar):
    """Ön-eğitim görevi (sonraki token): felaket unutmayı ölçer."""
    gpt.eval()
    toplam, say = 0.0, 0
    for i in range(0, len(bloklar), 64):
        b = bloklar[i : i + 64].to(cihaz)
        x, y = b[:, :-1], b[:, 1:]
        _, kayip = gpt(x, y)
        toplam += kayip.item() * y.numel()
        say += y.numel()
    gpt.train()
    return math.exp(toplam / say)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mod", default="lora")
    p.add_argument("--r", type=int, default=8)
    p.add_argument("--alpha", type=float, default=16.0)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--batch", type=int, default=32)
    a = p.parse_args()

    veri = veri_hazirla()
    sn = modeli_kur(a.mod, a.r, a.seed, a.alpha)
    egitilebilir = egitilebilir_say(sn)
    toplam = sum(q.numel() for q in sn.parameters())
    params = [q for q in sn.parameters() if q.requires_grad]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.01)
    Xtr, Mtr, ytr = [t.to(cihaz) for t in veri["egitim"]]
    Xva, Mva, yva = veri["dogrulama"]
    Xte, Mte, yte = veri["test"]
    # Ön-eğitim doğrulama bloklarından 400 blok (LM kaybı, felaket
    # unutma)
    dva = np.load(os.path.join(K, "tok_dogrulama.npy")).astype(
        np.int64
    )
    n = len(dva) // 129
    lm_blok = torch.tensor(dva[: n * 129].reshape(n, 129))[:400]
    lm_taban = (
        dil_ppl(sn.gpt, lm_blok)
        if a.mod != "sifirdan"
        else float("nan")
    )

    en_iyi = (-1.0, None, 0)
    t0 = time.time()
    gecmis = []
    for ep in range(a.epochs):
        sira = torch.randperm(len(Xtr), device=cihaz)
        for i in range(0, len(sira), a.batch):
            s = sira[i : i + a.batch]
            logit = sn(Xtr[s], Mtr[s])
            kayip = F.cross_entropy(logit, ytr.to(cihaz)[s])
            opt.zero_grad(set_to_none=True)
            kayip.backward()
            opt.step()
        dv_acc, dv_f1 = dogruluk(sn, Xva, Mva, yva)
        gecmis.append(round(dv_acc, 4))
        if dv_acc > en_iyi[0]:
            en_iyi = (
                dv_acc,
                {
                    k: v.detach().clone()
                    for k, v in sn.state_dict().items()
                },
                ep + 1,
            )
    sn.load_state_dict(en_iyi[1])
    te_acc, te_f1 = dogruluk(sn, Xte, Mte, yte)
    lm_son = (
        dil_ppl(sn.gpt, lm_blok)
        if a.mod != "sifirdan"
        else float("nan")
    )
    # Adaptör kapalıyken LM ppl (LoRA ise): taban W'nin değişmediğini
    # gösterir
    lm_kapali = float("nan")
    if a.mod == "lora":
        adaptor_durumu(sn.gpt, False)
        lm_kapali = dil_ppl(sn.gpt, lm_blok)
        adaptor_durumu(sn.gpt, True)
    sonuc = {
        "mod": a.mod,
        "r": a.r if a.mod == "lora" else 0,
        "lr": a.lr,
        "seed": a.seed,
        "egitilebilir": egitilebilir,
        "toplam": toplam,
        "dogrulama_acc_gecmis": gecmis,
        "en_iyi_epoch": en_iyi[2],
        "dogrulama_acc": round(en_iyi[0], 4),
        "test_acc": round(te_acc, 4),
        "test_f1": round(te_f1, 4),
        "lm_ppl_once": round(lm_taban, 3),
        "lm_ppl_sonra": round(lm_son, 3),
        "lm_ppl_adaptor_kapali": round(lm_kapali, 3),
        "sure_sn": round(time.time() - t0, 1),
    }
    with open(
        os.path.join(K, "sonuc_ince_ayar.jsonl"),
        "a",
        encoding="utf-8",
    ) as f:
        f.write(json.dumps(sonuc, ensure_ascii=False) + "\n")
    print(json.dumps(sonuc, ensure_ascii=False))


if __name__ == "__main__":
    main()
