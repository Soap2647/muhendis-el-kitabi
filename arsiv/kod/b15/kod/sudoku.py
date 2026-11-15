"""Sudoku cozucu: naif sira ve en kisitli hucre (MRV) sezgisi."""
import sys


def adaylar(tahta, r, c):
    kullanilan = set(tahta[r])
    kullanilan.update(tahta[i][c] for i in range(9))
    br, bc = 3 * (r // 3), 3 * (c // 3)
    for i in range(3):
        for j in range(3):
            kullanilan.add(tahta[br + i][bc + j])
    return [d for d in range(1, 10) if d not in kullanilan]


def coz(tahta, mrv, sinir):
    """Dondurur: (cozum_tahtasi veya None, dugum, asildi_mi)."""
    dugum = [0]
    asildi = [False]

    def dfs():
        dugum[0] += 1
        if dugum[0] > sinir:
            asildi[0] = True
            return False
        secim = None
        secim_adaylar = None
        for r in range(9):
            for c in range(9):
                if tahta[r][c] != 0:
                    continue
                ad = adaylar(tahta, r, c)
                if not mrv:
                    secim, secim_adaylar = (r, c), ad
                    break
                if secim is None or len(ad) < len(secim_adaylar):
                    secim, secim_adaylar = (r, c), ad
            if secim is not None and not mrv:
                break
        if secim is None:
            return True                 # bos hucre kalmadi
        r, c = secim
        for d in secim_adaylar:
            tahta[r][c] = d
            if dfs():
                return True
            if asildi[0]:
                break
        tahta[r][c] = 0                 # geri al
        return False

    ok = dfs()
    return (tahta if ok else None), dugum[0], asildi[0]


def ayristir(metin):
    return [[int(metin[9 * r + c]) for c in range(9)]
            for r in range(9)]


def gecerli(tahta, metin):
    kume = set(range(1, 10))
    satirlar = all(set(s) == kume for s in tahta)
    sutunlar = all(set(tahta[r][c] for r in range(9)) == kume
                   for c in range(9))
    kutular = all(
        set(tahta[br + i][bc + j] for i in range(3) for j in range(3))
        == kume
        for br in (0, 3, 6) for bc in (0, 3, 6))
    verilen = ayristir(metin)
    korunur = all(verilen[r][c] in (0, tahta[r][c])
                  for r in range(9) for c in range(9))
    return satirlar and sutunlar and kutular and korunur


PULMACALAR = {
    "kolay": "530070000600195000098000060800060003400803001"
             "700020006060000280000419005000080079",
    "zor": "800000000003600000070090200050007000000045700"
           "000100030001000068008500010090000400",
}

if __name__ == "__main__":
    sinir = int(sys.argv[1]) if len(sys.argv) > 1 else 300000
    for ad, metin in PULMACALAR.items():
        for mrv in (False, True):
            tahta = ayristir(metin)
            cozum, dugum, asildi = coz(tahta, mrv, sinir)
            if asildi:
                durum = "sinir asildi"
            else:
                durum = ("gecerli" if gecerli(cozum, metin)
                     else "HATALI")
            print("%-6s mrv=%-5s dugum=%7d  %s"
                  % (ad, mrv, dugum, durum))
