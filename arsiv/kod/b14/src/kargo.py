def gun_sayisi(agirliklar, kapasite):
    """Paketleri sırayla, kapasiteyi aşmadan günlere doldur."""
    gun, yuk = 1, 0
    for w in agirliklar:
        if yuk + w > kapasite:
            gun += 1
            yuk = 0
        yuk += w
    return gun


def min_kapasite(agirliklar, d, iz=False):
    lo = max(agirliklar)         # en ağır paket tek başına sığmalı
    hi = sum(agirliklar)         # hepsi tek günde: her zaman yeterli
    while lo < hi:
        orta = lo + (hi - lo) // 2
        g = gun_sayisi(agirliklar, orta)
        if iz:
            print(lo, hi, orta, g, "uygun" if g <= d else "yetmez")
        if g <= d:
            hi = orta
        else:
            lo = orta + 1
    return lo


if __name__ == "__main__":
    w = list(range(1, 11))
    print("min kapasite:", min_kapasite(w, 5))
    # kontrol: kapasite 14 ve 15 ile gun sayilari
    print("14 -> %d gun, 15 -> %d gun" % (gun_sayisi(w, 14),
          gun_sayisi(w, 15)))
