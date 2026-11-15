# ornek3_sehir.py - Sehirleri en ucuz baglama (Kruskal + Union-Find).
from mst import UnionFind

SEHIR = ["A", "B", "C", "D", "E", "F"]
KENAR = [(7, 0, 1), (5, 0, 2), (8, 1, 2), (9, 1, 3), (7, 2, 3),
         (5, 3, 4), (15, 2, 5), (6, 4, 5), (8, 3, 5)]


def kruskal_izli(n, kenar):
    uf = UnionFind(n)
    toplam, secilen = 0, []
    for w, u, v in sorted(kenar):
        ku, kv = uf.bul(u), uf.bul(v)
        durum = "KABUL" if ku != kv else "RED  "
        print(f"  {SEHIR[u]}-{SEHIR[v]} ({w:>2})  "
              f"kok {SEHIR[ku]}/{SEHIR[kv]}"
              f"  {durum}")
        if ku != kv:
            uf.birlestir(u, v)
            toplam += w
            secilen.append((SEHIR[u], SEHIR[v], w))
    return toplam, secilen


if __name__ == "__main__":
    toplam, secilen = kruskal_izli(len(SEHIR), KENAR)
    print("Toplam maliyet:", toplam)
    print("Secilen kenarlar:", secilen)
