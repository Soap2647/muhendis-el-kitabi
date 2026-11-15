# -*- coding: utf-8 -*-
"""Bölüm 70 - Örnekleme yöntemleri, tekrar ve ezberleme ölçümü.
(a) El ile logit örneği: sıcaklık, top-k, top-p dağılımları.
(b) ana_0 GPT'sinden üretim: açgözlü, sıcaklık, top-k, top-p.
(c) Ezberleme: üretilen 8-token dizilerinin eğitim verisinde birebir
geçmesi,
    doğrulama metninin kendi örtüşme taban oranıyla
    karşılaştırılır."""

import math, os, random
import numpy as np
import torch
import torch.nn.functional as F
from bpe_sifirdan import BPE
from gpt_b70 import MiniGPT

K = os.path.dirname(os.path.abspath(__file__))
V = 2149

# (a) El ile logit örneği
logit = np.array([2.0, 1.0, 0.5, -1.0, 0.0])


def softmax(z):
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


print("(a) logit =", logit)
for T in [1.0, 0.5, 2.0]:
    print("  T=%.1f p=" % T, np.round(softmax(logit / T), 4))


def topk(z, k):
    m = np.full_like(z, -np.inf)
    idx = np.argsort(-z)[:k]
    m[idx] = z[idx]
    return softmax(m)


print("  top-k=2 p=", np.round(topk(logit, 2), 4))


def topp(z, p):
    s = softmax(z)
    o = np.argsort(-s)
    c = np.cumsum(s[o])
    son = np.searchsorted(c, p) + 1
    m = np.full_like(z, -np.inf)
    m[o[:son]] = z[o[:son]]
    return softmax(m), son


pp, son = topp(logit, 0.9)
print("  top-p=0.9 çekirdek boyutu=%d p=" % son, np.round(pp, 4))

# (b) Üretim
cihaz = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ck = torch.load(
    os.path.join(K, "gpt_ana_0.pt"),
    map_location="cpu",
    weights_only=True,
)
model = MiniGPT(
    V, ctx=ck["ctx"], d=ck["d"], L=ck["L"], bas=ck["bas"], dusme=0.0
)
model.load_state_dict(ck["state"])
model.to(cihaz).eval()
bj = __import__("json").load(
    open(os.path.join(K, "bpe_b70.json"), encoding="utf-8")
)
b = BPE.yukle(bj["alfabe"], bj["kurallar"])


@torch.no_grad()
def uret(model, baslangic, n, yontem, T=1.0, k=40, p=0.9, tohum=0):
    g = torch.Generator(device=cihaz).manual_seed(tohum)
    idx = torch.tensor([baslangic], device=cihaz)
    for _ in range(n):
        ctx = idx[:, -model.ctx :]
        z = model(ctx)[0][:, -1, :].float()[0]
        if yontem == "acgozlu":
            nxt = int(z.argmax())
        else:
            z = z / T
            if yontem == "topk":
                v, _ = torch.topk(z, k)
                z[z < v[-1]] = -float("inf")
            if yontem == "topp":
                s, o = torch.sort(z, descending=True)
                c = torch.cumsum(F.softmax(s, 0), 0)
                # ilk p'yi aşan belirteç hariç
                maske = c - F.softmax(s, 0) > p
                s[maske] = -float("inf")
                z = torch.full_like(z, -float("inf"))
                z[o] = s
            nxt = int(
                torch.multinomial(F.softmax(z, 0), 1, generator=g)
            )
        idx = torch.cat([idx, torch.tensor([[nxt]], device=cihaz)], 1)
    return idx[0].tolist()


def d2(ids):
    bigram = list(zip(ids, ids[1:]))
    return len(set(bigram)) / max(1, len(bigram))


ba = b.kodla("Bölüm 70: dil modelleri")
print(
    "\n(b) üretim (300 token), baslangic: 'Bölüm 70: dil modelleri'"
)
for ad, yon, T in [
    ("açgözlü", "acgozlu", 1.0),
    ("sıcaklık 0.8", "sicaklik", 0.8),
    ("top-k 40", "topk", 1.0),
    ("top-p 0.9", "topp", 1.0),
]:
    ids = (
        uret(
            model,
            ba,
            300,
            "topk" if yon == "sicaklik" else yon,
            T=T,
            tohum=1,
        )
        if yon != "sicaklik"
        else None
    )
    if yon == "sicaklik":
        ids = uret(model, ba, 300, "topp", T=T, p=1.0, tohum=1)
    print(
        "  %-14s distinct-2=%.3f  metin: %s..."
        % (
            ad,
            d2(ids[len(ba) :]),
            b.coz(ids[len(ba) :])[:90].replace("\n", " "),
        )
    )
print(
    "  not: sıcaklık satırı p=1.0 top-p ile yalnız sıcaklık "
    "etkisini ölçer"
)

# (c) Ezberleme
tr = np.load(os.path.join(K, "tok_egitim.npy")).tolist()
va = np.load(os.path.join(K, "tok_dogrulama.npy")).tolist()
N = 8
egitim_ngram = set(tuple(tr[i : i + N]) for i in range(len(tr) - N))


def oran(dizi):
    top = len(dizi) - N
    return (
        sum(
            1
            for i in range(top)
            if tuple(dizi[i : i + N]) in egitim_ngram
        )
        / top
    )


print(
    "\n(c) ezberleme (%d-token dizi, eğitimde birebir geçen oranı)"
    % N
)
print("  doğrulama (taban örtüşme)  = %.4f" % oran(va[:20000]))
rng = random.Random(0)
uretim = uret(model, ba, 3000, "topp", T=1.0, p=0.9, tohum=7)[
    len(ba) :
]
print("  üretim (top-p 0.9, 3000 token)   = %.4f" % oran(uretim))
ilk = [model] * 0
rastgele = MiniGPT(
    V, ctx=ck["ctx"], d=ck["d"], L=ck["L"], bas=ck["bas"], dusme=0.0
)
rastgele.to(cihaz).eval()
ru = uret(rastgele, ba, 3000, "topp", T=1.0, p=0.9, tohum=7)[
    len(ba) :
]
print("  rastgele (ilklenmemiş) model     = %.4f" % oran(ru))
open(
    os.path.join(K, "ornek_uretim.txt"), "w", encoding="utf-8"
).write(b.coz(uretim[:600]))
