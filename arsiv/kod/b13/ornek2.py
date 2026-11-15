def araliklari_birlestir(aralik):
    """Kapali araliklari [s, e] birlestirir. O(n log n)."""
    if not aralik:
        return []
    aralik = sorted(aralik)
    sonuc = [list(aralik[0])]
    for s, e in aralik[1:]:
        if s <= sonuc[-1][1]:
            sonuc[-1][1] = max(sonuc[-1][1], e)
        else:
            sonuc.append([s, e])
    return sonuc


if __name__ == "__main__":
    print(araliklari_birlestir([(1, 3), (8, 10), (2, 6),
                                (15, 18), (17, 20)]))
    print(araliklari_birlestir([(1, 4), (4, 5)]))
