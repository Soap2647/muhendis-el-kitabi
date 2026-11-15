# redos.py: katastrofik geri izleme ölçümü, desen (a+)+b
# Kullanım: python redos.py <veri_klasörü>
import csv
import os
import re
import sys
import time

sys.setrecursionlimit(10000)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regex import Motor, ayristir

ADIM = [0]


def esle(ag, w, i, k):
    """Naif geri izleme. Her çağrı bir adım sayılır."""
    ADIM[0] += 1
    t = ag[0]
    if t == "chr":
        return i < len(w) and w[i] == ag[1] and k(i + 1)
    if t == "cat":
        return seq(ag[1], 0, w, i, k)
    if t == "alt":
        return any(esle(d, w, i, k) for d in ag[1])
    if t == "?":
        return esle(ag[1], w, i, k) or k(i)
    if t == "*":
        def tekrar(j):
            return j > i and esle(ag, w, j, k)
        return esle(ag[1], w, i, tekrar) or k(i)
    if t == "+":
        return esle(ag[1], w, i,
                    lambda j: esle(("*", ag[1]), w, j, k))


def seq(parca, idx, w, i, k):
    if idx == len(parca):
        return k(i)
    return esle(parca[idx], w, i,
                lambda j: seq(parca, idx + 1, w, j, k))


def naif_adim(desen, w):
    ADIM[0] = 0
    ok = esle(ayristir(desen), w, 0, lambda j: j == len(w))
    return ok, ADIM[0]


def en_kisa_sure(f, tekrar=3):
    """Üç ölçümün en küçüğü (gürültüyü azaltmak için)."""
    en = float("inf")
    for _ in range(tekrar):
        t0 = time.perf_counter()
        f()
        en = min(en, time.perf_counter() - t0)
    return en


if __name__ == "__main__":
    DESEN = "(a+)+b"
    VERI = sys.argv[1] if len(sys.argv) > 1 else "."
    print("python", sys.version.split()[0])
    with open(os.path.join(VERI, "b36_redos.csv"), "w", newline="",
              encoding="utf-8") as f:
        yaz = csv.writer(f)
        yaz.writerow(["n", "naif_adim", "re_ms"])
        for n in range(10, 25, 2):
            w = "a" * n
            ok, adim = naif_adim(DESEN, w)
            assert ok is False
            t = en_kisa_sure(lambda: re.fullmatch(DESEN, w))
            yaz.writerow([n, adim, round(t * 1000, 3)])
            print("n=%2d naif=%9d re_ms=%.3f" % (n, adim, t * 1000))
    m = Motor(DESEN)
    with open(os.path.join(VERI, "b36_thompson.csv"), "w", newline="",
              encoding="utf-8") as f:
        yaz = csv.writer(f)
        yaz.writerow(["n", "thompson_ms"])
        for n in [1000, 2000, 4000, 8000, 16000]:
            w = "a" * n
            assert m.tam_eslesir(w) is False
            t = en_kisa_sure(lambda: m.tam_eslesir(w))
            yaz.writerow([n, round(t * 1000, 3)])
            print("thompson n=%6d ms=%.2f" % (n, t * 1000))
