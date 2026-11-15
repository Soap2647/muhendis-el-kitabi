# -*- coding: utf-8 -*-
"""LSM deposunu dict modeline karşı test eder ve ölçüm yapar."""
import random
import shutil
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lsm import LSM

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_dizin")


def dizin(ad):
    yol = os.path.join(KOK, ad)
    shutil.rmtree(yol, ignore_errors=True)
    return yol


def rastgele_islemler(seed, adet, anahtar_say):
    rnd = random.Random(seed)
    for _ in range(adet):
        k = "k%04d" % rnd.randrange(anahtar_say)
        r = rnd.random()
        if r < 0.55:
            yield ("put", k, "v%d" % rnd.randrange(10 ** 6))
        elif r < 0.75:
            yield ("sil", k, None)
        else:
            yield ("get", k, None)


def model_karsilastir(seed, adet=20000):
    # esik küçük: sık flush, sık birleştirme; bloom açık
    db = LSM(dizin("tst_%d" % seed), esik=50, m=2048, k=4)
    model = {}
    hata = 0
    kontrol = 0
    islemler = rastgele_islemler(seed, adet, 400)
    for i, (op, k, v) in enumerate(islemler):
        if op == "put":
            db.put(k, v)
            model[k] = v
        elif op == "sil":
            db.sil(k)
            model.pop(k, None)
        else:
            kontrol += 1
            if db.get(k) != model.get(k):
                hata += 1
        if i % 2500 == 2499 and i != adet - 1:
            db.birlestir()
    # son tam karşılaştırma
    for k in sorted({"k%04d" % j for j in range(400)}):
        kontrol += 1
        if db.get(k) != model.get(k):
            hata += 1
    return hata, kontrol, db.tablo_sayisi()


def yukseltme_olcumu():
    rnd = random.Random(35)
    db = LSM(dizin("olcum"), esik=256, m=1 << 17, k=7)
    for _ in range(20000):
        k = "k%05d" % rnd.randrange(5000)
        db.put(k, "x" * 20)
    yaz_once = db.say["disk_yazma"]
    kul = db.say["kullanici"]
    tablo_once = db.tablo_sayisi()
    db.birlestir()
    yaz_sonra = db.say["disk_yazma"]
    return {"kullanici": kul, "flush_yazma": yaz_once,
            "birlestirme_sonra": yaz_sonra, "tablo_once": tablo_once,
            "tablo_sonra": db.tablo_sayisi(),
            "wa_once": yaz_once / kul, "wa_sonra": yaz_sonra / kul}


def okuma_olcumu(bloom):
    rnd = random.Random(35)
    db = LSM(dizin("okuma_%d" % bloom), esik=256, m=1 << 11, k=6,
             bloom_kullan=bool(bloom))
    for _ in range(20000):
        db.put("k%05d" % rnd.randrange(20000), "x" * 20)
    db.say["sorgu_disk_okuma"] = 0
    db.say["bloom_red"] = 0
    sorgu = 2000
    for _ in range(sorgu):  # yalnızca YOK olan anahtarlar
        db.get("y%05d" % rnd.randrange(10 ** 5))
    return db.say["sorgu_disk_okuma"] / sorgu, db.tablo_sayisi(), \
        db.say["bloom_red"]


if __name__ == "__main__":
    print("== Model karşılaştırması (dict modeline karşı) ==")
    toplam_hata = 0
    for seed in range(1, 6):
        hata, kont, tab = model_karsilastir(seed)
        toplam_hata += hata
        print("tohum %d: kontrol=%d hata=%d son_tablo=%d"
              % (seed, kont, hata, tab))
    print("Toplam hata:", toplam_hata)

    print("\n== Yazma yükseltmesi ==")
    y = yukseltme_olcumu()
    print("kullanıcı bayt      : %d" % y["kullanici"])
    print("flush ile diske     : %d  (tablo=%d)"
          % (y["flush_yazma"], y["tablo_once"]))
    print("birleştirme sonrası : %d  (tablo=%d)"
          % (y["birlestirme_sonra"], y["tablo_sonra"]))
    print("yazma yük. (önce)   : %.2f" % y["wa_once"])
    print("yazma yük. (sonra)  : %.2f" % y["wa_sonra"])

    print("\n== Okuma yükseltmesi: var olmayan anahtar ==")
    for b in (1, 0):
        r, tab, red = okuma_olcumu(b)
        print("bloom=%d  sorgu başına disk okuma=%.3f  tablo=%d  "
              "bloom_red=%d" % (b, r, tab, red))
    shutil.rmtree(KOK, ignore_errors=True)
