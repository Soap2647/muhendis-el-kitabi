# -*- coding: utf-8 -*-
"""Bolum 71 - Acgozlu (greedy) spekulatif cozme: taslak n-gram + hedef
GPT."""

import csv
import os
import random
from collections import Counter, defaultdict

import torch

from lm71 import KucukGPT, TEMP, metin_al
from ortak import VERI

torch.set_num_threads(4)
durum = torch.load(TEMP + "/lm71.pt", weights_only=False)
kars = durum["kars"]
si = {c: i for i, c in enumerate(kars)}
hedef = KucukGPT(len(kars))
hedef.load_state_dict(durum["durum"])
hedef.eval()

metin = metin_al()
egitim = metin[: int(len(metin) * 0.9)]
test = metin[int(len(metin) * 0.9) :]


def ngram_kur(metin, n=4):
    """Baglam (n-1 karakter) -> sonraki karakter sayilari."""
    sayac = defaultdict(Counter)
    for i in range(len(metin) - n + 1):
        sayac[metin[i : i + n - 1]][metin[i + n - 1]] += 1
    return sayac


TASLAK = ngram_kur(egitim, 4)


def taslak_tahmin(baglam):
    """Son 3 karakterin en sik sonraki karakteri; yoksa bosluk."""
    sayac = TASLAK.get(baglam[-3:])
    if sayac:
        return sayac.most_common(1)[0][0]
    return " "


@torch.no_grad()
def hedef_argmax(seq):
    """seq icinde her konumun greedy tahmini (uzunluk len(seq))."""
    logit = hedef(torch.tensor([[si[c] for c in seq]]))
    return [kars[i] for i in logit[0].argmax(dim=-1).tolist()]


@torch.no_grad()
def duz_uret(istem, n):
    """Referans: hedef modelin dogrudan greedy uretimi."""
    seq = istem
    for _ in range(n):
        seq += hedef_argmax(seq)[-1]
    return seq[len(istem) :]


def spekulatif(istem, n, gamma):
    seq = istem
    uretilen, cagri, onerilen, kabul = 0, 0, 0, 0
    cikti = ""
    while len(cikti) < n:
        taslak = []
        s = seq + cikti
        for _ in range(gamma):
            c = taslak_tahmin((s + "".join(taslak))[-3:])
            taslak.append(c)
        tam = s + "".join(taslak)
        tahmin = hedef_argmax(tam)
        cagri += 1
        onerilen += gamma
        k = 0
        while k < gamma and taslak[k] == tahmin[len(s) + k - 1]:
            k += 1
        kabul += k
        # kabul edilenler + hedefin bir sonraki (duzeltme ya da bonus)
        # belirteci
        cikti += "".join(taslak[:k])
        cikti += tahmin[len(s) + k - 1]
    return cikti[:n], cagri, kabul, onerilen


if __name__ == "__main__":
    rng = random.Random(71)
    baslangic = [rng.randrange(0, len(test) - 300) for _ in range(20)]
    istemler = [test[b : b + 40] for b in baslangic]
    N = 64
    referans = ["".join(duz_uret(i, N)) for i in istemler]
    satirlar = []
    print(
        "%5s %10s %10s %12s %14s"
        % (
            "gamma",
            "kabul_a",
            "belirt/cagri",
            "hedef_cagri",
            "ayni_cikti",
        )
    )
    for gamma in [1, 2, 4, 8]:
        toplam_cagri, toplam_kabul, toplam_onr, ayni = 0, 0, 0, 0
        for i, ist in enumerate(istemler):
            cikti, cagri, kabul, onr = spekulatif(ist, N, gamma)
            toplam_cagri += cagri
            toplam_kabul += kabul
            toplam_onr += onr
            ayni += int(cikti == referans[i])
        alfa = toplam_kabul / toplam_onr
        bcg = N * len(istemler) / toplam_cagri
        print(
            "%5d %10.3f %12.3f %12d %10d/%d"
            % (gamma, alfa, bcg, toplam_cagri, ayni, len(istemler))
        )
        satirlar.append(
            {
                "gamma": gamma,
                "kabul_orani": round(alfa, 4),
                "belirtec_per_cagri": round(bcg, 4),
                "hedef_cagri": toplam_cagri,
                "ayni_cikti": ayni,
            }
        )
    with open(
        os.path.join(VERI, "b71_spekulatif.csv"),
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
