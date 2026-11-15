# -*- coding: utf-8 -*-
"""Bolum 71 - Kisitli cozme (izinli karakter maskesi) ve cikti
dogrulama."""

import json
import math
import random
import re

import torch

from lm71 import TEMP
from lm71 import KucukGPT

torch.set_num_threads(4)
durum = torch.load(TEMP + "/lm71.pt", weights_only=False)
kars = durum["kars"]
hedef = KucukGPT(len(kars))
hedef.load_state_dict(durum["durum"])
hedef.eval()

TURK_HARF = (
    "abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"
)
HARF = [c for c in kars if c in TURK_HARF]
RAKAM = [c for c in kars if c in "0123456789"]
ONEK = '{"ad":"'
ARA = ',"yas":'
SON = "}"


def izinli(s):
    """Simdiye kadarki metin s icin izinli sonraki karakter kumesi."""
    if len(s) < len(ONEK):
        return {ONEK[len(s)]}
    govde = s[len(ONEK) :]
    if '"' not in govde:  # ad alani aciktir
        if len(govde) < 12:
            return set(HARF) | ({'"'} if govde else set())
        return {'"'}
    ad_bitti = govde.index('"')
    kalan = govde[ad_bitti + 1 :]
    if len(kalan) < len(ARA):  # sabit ayirici
        return {ARA[len(kalan)]}
    sayi = kalan[len(ARA) :]
    if not sayi:  # JSON: bas sifir yok
        return set(RAKAM) - {"0"}
    if len(sayi) < 3:  # 1-3 rakam, sonra '}'
        return set(RAKAM) | {SON}
    return {SON}


@torch.no_grad()
def dagit(seq_str, n=32, kisitli=False, rng=None, sicaklik=1.0):
    """Karakter karakter uretir. kisitli=True ise maske uygulanir."""
    s = seq_str
    for _ in range(n):
        x = torch.tensor([[si[c] for c in s]])
        logit = hedef(x)[0, -1] / sicaklik
        if kisitli:
            izin = izinli(s)
            if not izin:
                break
            maske = torch.full_like(logit, float("-inf"))
            for c in izin:
                maske[si[c]] = 0.0
            logit = logit + maske
        p = torch.softmax(logit, dim=-1)
        c = kars[int(torch.multinomial(p, 1, generator=rng))]
        s += c
        if s.endswith(SON) and s.startswith(ONEK):
            break
    return s


si = {c: i for i, c in enumerate(kars)}


def dogrula(metin):
    """Sema: {"ad": harf dizisi 1-12, "yas": 1-3 haneli tamsayi}."""
    try:
        veri = json.loads(metin)
    except json.JSONDecodeError:
        return False, "json"
    if set(veri) != {"ad", "yas"}:
        return False, "anahtar"
    if not (
        isinstance(veri["ad"], str)
        and 1 <= len(veri["ad"]) <= 12
        and all(c in TURK_HARF for c in veri["ad"])
    ):
        return False, "ad"
    if not (isinstance(veri["yas"], int) and 0 <= veri["yas"] <= 999):
        return False, "yas"
    return True, "tamam"


if __name__ == "__main__":
    izin = sorted(izinli('{"ad":"'))
    print("ad alani ilk karakter izinleri:", len(izin), "adet")
    print("ornek:", " ".join(izin[:12]))
    print("harf sayisi:", len(HARF), " rakam sayisi:", len(RAKAM))
    N, DENEME = 200, 3
    for kisitli in [False, True]:
        rng = torch.Generator().manual_seed(71)
        ilk, son, sebep = 0, 0, {}
        for _ in range(N):
            ok_ilk = False
            for d in range(DENEME):
                cikti = dagit(ONEK, 32, kisitli, rng)
                ok, neden = dogrula(cikti)
                if d == 0:
                    ok_ilk = ok
                    sebep[neden] = sebep.get(neden, 0) + 1
                if ok:
                    son += 1
                    break
            ilk += int(ok_ilk)
        print(
            "kisitli=%-5s ilk=%3d/%d 3deneme=%3d/%d %s"
            % (kisitli, ilk, N, son, N, sebep)
        )
    ornek = dagit(ONEK, 32, True, torch.Generator().manual_seed(71))
    print("kisitli ornek:", ornek, dogrula(ornek))
