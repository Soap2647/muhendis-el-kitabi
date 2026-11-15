# -*- coding: utf-8 -*-
"""Bölüm 70 - Bayt düzeyi BPE: UTF-8 baytlarının okunabilir simgelere
eşlenmesi. Eşleme, kurulu transformers 4.57.6 kaynağındaki
bytes_to_unicode() fonksiyonudur; burada yalnızca içe aktarılır."""

from transformers.models.gpt2.tokenization_gpt2 import (
    bytes_to_unicode,
)

eslem = bytes_to_unicode()
print("eşleme boyutu:", len(eslem))
for metin in ["ğ", "ı", "ü", "a", " ", "çözüm"]:
    baytlar = list(metin.encode("utf-8"))
    simgeler = [eslem[b] for b in baytlar]
    print(
        "%-7r bayt=%s simge=%s" % (metin, baytlar, "".join(simgeler))
    )
