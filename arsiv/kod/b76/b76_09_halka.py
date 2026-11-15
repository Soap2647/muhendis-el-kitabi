# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 9: halka all-reduce ve boru hatti kabarcigi."""

import csv
import os
import numpy as np

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"


def halka_allreduce(vekt):
    """vekt: N dugumun vektorleri. Her dugumun sonucu toplamdir.
    Her adimda mesajlar once toplanir, sonra uygulanir.
    """
    n = len(vekt)
    buf = [
        np.array_split(v.astype(np.float64).copy(), n) for v in vekt
    ]
    gonderilen = 0  # dugum basina gonderilen eleman
    # 1) Reduce-scatter: N-1 adim
    for s in range(n - 1):
        mesaj = [buf[i][(i - s) % n].copy() for i in range(n)]
        for i in range(n):
            j = (i - 1) % n
            buf[i][(j - s) % n] = buf[i][(j - s) % n] + mesaj[j]
        gonderilen += mesaj[0].size
    # 2) All-gather: N-1 adim
    for s in range(n - 1):
        mesaj = [buf[i][(i + 1 - s) % n].copy() for i in range(n)]
        for i in range(n):
            j = (i - 1) % n
            buf[i][(j + 1 - s) % n] = mesaj[j]
        gonderilen += mesaj[0].size
    sonuc = [np.concatenate(b) for b in buf]
    return sonuc, gonderilen


def kabarcik(p, m):
    """GPipe ileri gecisi: asama s, batch j'yi t = s + j'de isler.
    Zaman izgarasinda mesgul hucreleri sayar; kabarcik = bos oran."""
    t_son = m + p - 1  # son meşgul zaman dilimi + 1
    mesgul = {(s, s + j) for s in range(p) for j in range(m)}
    return 1 - len(mesgul) / (p * t_son), (p - 1) / (m + p - 1)


def main():
    rng = np.random.default_rng(76)
    m_eleman = 1200  # gradyan vektoru uzunlugu
    rows = []
    print(
        "N   simulasyon-dogru   gonderim/dugum(eleman)  "
        "2(N-1)/N * M"
    )
    for n in [2, 4, 8]:
        vekt = [rng.standard_normal(m_eleman) for _ in range(n)]
        hedef = np.sum(vekt, axis=0)
        sonuc, gon = halka_allreduce(vekt)
        dogru = all(np.allclose(s, hedef) for s in sonuc)
        formul = 2 * (n - 1) / n * m_eleman
        print(f"{n:<3} {str(dogru):<18}  {gon:<22} {formul:.1f}")
        rows.append(("halka", n, dogru, gon, round(formul, 1)))
    print(
        "\np (asama)  m (mikro-batch)  "
          "kabarcik (simulasyon)  (p-1)/(m+p-1)"
    )
    for p in [4]:
        for m in [1, 4, 8, 16, 32]:
            sim, formul = kabarcik(p, m)
            print(f"{p:<10} {m:<16} {sim:<22.4f} {formul:.4f}")
            rows.append(
                ("kabarcik", p, m, round(sim, 4), round(formul, 4))
            )
    with open(
        os.path.join(VERI, "b76_halka_kabarcik.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["tur", "a", "b", "c", "d"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
