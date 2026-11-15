# Turing makinesi simülatörü: ikili sayıyı 1 artırır.
# Geçiş: (durum, okunan) -> (yazılacak, hareket, yeni durum)
DELTA = {
    ("q0", "0"): ("0", "R", "q0"),     # sağa git, sonu bul
    ("q0", "1"): ("1", "R", "q0"),
    ("q0", "_"): ("_", "L", "q1"),     # sonda: geri dön
    ("q1", "1"): ("0", "L", "q1"),     # 1 + 1 = 0, taşı sürer
    ("q1", "0"): ("1", "L", "dur"),    # 0 + 1 = 1, dur
    ("q1", "_"): ("1", "L", "dur"),    # baştan taştı: yeni basamak
}


def calistir(girdi, adim_siniri=10000):
    """Sonucu (boşlukları atılmış bant) ve adım sayısını döndürür."""
    bant = dict(enumerate(girdi))
    kafa, durum, adim = 0, "q0", 0
    while durum != "dur":
        sembol = bant.get(kafa, "_")
        yaz, hareket, yeni = DELTA[(durum, sembol)]
        bant[kafa] = yaz
        kafa += 1 if hareket == "R" else -1
        durum = yeni
        adim += 1
        if adim > adim_siniri:
            raise RuntimeError("durmadı")
    son = [bant.get(i, "_") for i in range(min(bant), max(bant) + 1)]
    return "".join(son).strip("_"), adim


def izle(girdi):
    """Her adımda (durum, bant metni, başlık konumu) döndürür."""
    bant = dict(enumerate(girdi))
    kafa, durum, iz = 0, "q0", []
    while durum != "dur":
        iz.append((durum, dict(bant), kafa))
        sembol = bant.get(kafa, "_")
        yaz, hareket, yeni = DELTA[(durum, sembol)]
        bant[kafa] = yaz
        kafa += 1 if hareket == "R" else -1
        durum = yeni
    iz.append((durum, dict(bant), kafa))
    return iz


def dogrula(n_max=1000):
    for n in range(0, n_max + 1):
        sonuc, _ = calistir(format(n, "b"))
        assert sonuc == format(n + 1, "b"), n
    return n_max + 1


if __name__ == "__main__":
    for durum, bant, kafa in izle("1011"):
        son = [bant.get(i, "_") for i in range(-1, 5)]
        print("%-4s %s  kafa=%2d" % (durum, "".join(son), kafa))
    print("1011 + 1 =", calistir("1011"))
    print("dogrulanan:", dogrula())
