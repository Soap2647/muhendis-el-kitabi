"""Geri izleme (backtracking): alt kumeler, permutasyonlar,
kombinasyonlar ve kombinasyon toplami."""


def altkumeler(a):
    sonuc = []
    secili = []

    def dfs(i):
        if i == len(a):
            sonuc.append(secili[:])
            return
        dfs(i + 1)              # a[i] secilmez
        secili.append(a[i])     # sec
        dfs(i + 1)              # kesfet
        secili.pop()            # geri al

    dfs(0)
    return sonuc


def tekrarsiz_permutasyonlar(a):
    a = sorted(a)
    n = len(a)
    kullanildi = [False] * n
    yol = []
    sonuc = []

    def dfs():
        if len(yol) == n:
            sonuc.append(yol[:])
            return
        for i in range(n):
            if kullanildi[i]:
                continue
            # Ayni deger, onceki kopyasi bu dalda
            # kullanilmadiysa atlanir: tekrar yok.
            if i > 0 and a[i] == a[i - 1] and not kullanildi[i - 1]:
                continue
            kullanildi[i] = True
            yol.append(a[i])
            dfs()
            yol.pop()
            kullanildi[i] = False

    dfs()
    return sonuc


def kombinasyonlar(n, k):
    sonuc = []
    yol = []

    def dfs(baslangic):
        if len(yol) == k:
            sonuc.append(yol[:])
            return
        for v in range(baslangic, n + 1):
            yol.append(v)
            dfs(v + 1)
            yol.pop()

    dfs(1)
    return sonuc


def kombinasyon_toplami(adaylar, hedef, buda=True):
    a = sorted(adaylar)
    sonuc = []
    yol = []
    dugum = [0]

    def dfs(i, kalan):
        dugum[0] += 1
        if kalan == 0:
            sonuc.append(yol[:])
            return
        if kalan < 0:
            return
        for j in range(i, len(a)):
            if buda and a[j] > kalan:
                break               # sirali: sonrakiler de buyuk
            yol.append(a[j])
            dfs(j, kalan - a[j])    # ayni aday tekrar secilebilir
            yol.pop()

    dfs(0, hedef)
    return sonuc, dugum[0]


if __name__ == "__main__":
    print("altkumeler([1, 2, 3]):")
    for s in altkumeler([1, 2, 3]):
        print(" ", s)
    print("tekrarsiz([1, 1, 2]):",
          tekrarsiz_permutasyonlar([1, 1, 2]))
    print("kombinasyonlar(4, 2):", kombinasyonlar(4, 2))
    print("toplam([2, 3, 6, 7], 7):",
          kombinasyon_toplami([2, 3, 6, 7], 7)[0])
    aday = [2, 3, 5, 7, 11, 13, 17, 19]
    for buda in (False, True):
        sonuc, dugum = kombinasyon_toplami(aday, 40, buda)
        print("budama=%-5s cozum=%4d dugum=%6d"
              % (buda, len(sonuc), dugum))
