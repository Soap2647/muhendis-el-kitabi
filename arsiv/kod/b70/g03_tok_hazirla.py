# -*- coding: utf-8 -*-
"""Bölüm 70 - GPT ve n-gram için ortak tokenizer ve token dizileri.

Tokenizer yalnızca EĞİTİM bölümlerinden öğrenilir (sızıntı yok).
Sözlük: alfabe 245 + birleştirme 1903 + <unk> = 2149.
Çıktılar: bpe_b70.json, tok_egitim.npy, tok_dogrulama.npy,
tok_test.npy
"""

import json, os
import numpy as np
from bpe_sifirdan import BPE

K = os.path.dirname(os.path.abspath(__file__))
oku = lambda a: open(os.path.join(K, a), encoding="utf-8").read()
egitim = oku("korpus_egitim.txt")
b = BPE(egitim, 1903)
print("sözlük boyutu (unk dahil):", b.boyut())
json.dump(
    {"alfabe": b.alfabe, "kurallar": b.kurallar},
    open(os.path.join(K, "bpe_b70.json"), "w", encoding="utf-8"),
    ensure_ascii=False,
)
for ad, dosya in [
    ("egitim", "korpus_egitim.txt"),
    ("dogrulama", "korpus_dogrulama.txt"),
    ("test", "korpus_test.txt"),
]:
    ids = np.array(b.kodla(oku(dosya)), dtype=np.uint16)
    np.save(os.path.join(K, "tok_%s.npy" % ad), ids)
    print(
        "%-10s token=%d  unk=%d"
        % (ad, len(ids), int((ids == b.unk).sum()))
    )
