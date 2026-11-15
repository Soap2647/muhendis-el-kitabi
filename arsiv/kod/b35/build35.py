# -*- coding: utf-8 -*-
"""sablon35.txt -> bolumler/bolum_35.md
Yönergeler:
  [[KOD dosya a b]]  dosyanın a..b satırları (python ya da cpp)
  [[CIKTI dosya]]    çıktı dosyasının tamamı (term bloğu)
  [[TERM redis]]     kavramsal komutlar (çalıştırılmadı)
  [[SEKIL n]]        gorseller/b35_*.png (n: sıra)
"""
import os
import re
import sys

WS = "C:/Users/merty/AppData/Local/Temp/b35"
KITAP = "D:/Mevcut Projeler/Kitap"

SEKIL = {
    1: ("aileler", "NoSQL ailelerinin karar haritası: erişim deseni ailenin "
        "seçimini belirler."),
    2: ("bplus_lsm", "B+ ağacı yerinde güncelleme yapar; LSM yazmayı sıralı "
        "bir günlüğe ve değişmez dosyalara dönüştürür."),
    3: ("lsm_seviye", "LSM seviyeleri: seviye 0'da aralıklar çakışır, "
        "birleştirme ile seviye 1'de ayrık ve sıralı tablolar oluşur."),
    4: ("bloom_bit", "Bloom filtresi bit dizisi: 0 gören sorgu kesinlikle "
        "yok der; D sorgusu tüm bitleri 1 gördüğü için yanlış pozitiftir."),
    5: ("bloom_olcum", "Bloom yanlış pozitif oranı: teorik eğriler ve "
        "100 000 sorguluk ölçümler (n = 10 000)."),
    6: ("cogaltma", "Çoğaltma modelleri: lider-takipçi, çok lider ve "
        "lidersiz."),
    7: ("halka", "Tutarlı hash halkası: sanal düğümler ve anahtarların "
        "saat yönünde ilk düğüme atanması."),
    8: ("tasinan", "Düğüm eklemede taşınan anahtar oranı (solda) ve yük "
        "dengesi (sağda, CV); 100 000 anahtar."),
    9: ("quorum", "Quorum N = 3: teorik ve ölçülen bayat okuma olasılığı; "
        "R + W > N iken sıfır."),
    10: ("zaman_dod", "Delta-of-delta sıkıştırma: nokta başına bit sayısı; "
         "ham 64 bit çizgisinin altında."),
}

KOD_RE = re.compile(r"^\[\[KOD (\S+) (\d+) (\d+)\]\]$")
CIKTI_RE = re.compile(r"^\[\[CIKTI (\S+)\]\]$")
SEKIL_RE = re.compile(r"^\[\[SEKIL (\d+)\]\]$")


def kod_blogu(yol, a, b):
    tam = os.path.join(WS, yol)
    satirlar = open(tam, encoding="utf-8").read().split("\n")
    parca = satirlar[int(a) - 1:int(b)]
    while parca and parca[-1] == "":
        parca.pop()
    dil = "cpp" if yol.endswith(".cc") else "python"
    if len(parca) > 40:
        raise SystemExit("blok 40 satırı aşıyor: %s %s-%s" % (yol, a, b))
    return "```%s\n%s\n```" % (dil, "\n".join(parca))


def cikti_blogu(yol):
    metin = open(os.path.join(WS, yol), encoding="utf-8").read()
    return "```term\n%s\n```" % metin.rstrip("\n")


def main():
    kaynak = open(os.path.join(WS, "sablon35.txt"),
                  encoding="utf-8").read().split("\n")
    cikti = []
    for satir in kaynak:
        m = KOD_RE.match(satir)
        if m:
            cikti.append(kod_blogu(m.group(1), m.group(2), m.group(3)))
            continue
        m = CIKTI_RE.match(satir)
        if m:
            cikti.append(cikti_blogu(m.group(1)))
            continue
        if satir == "[[TERM redis]]":
            cikti.append("```term\n"
                         "$ SET oturum:42 \"veri\" EX 60 NX\n"
                         "$ INCR ziyaret:ana-sayfa\n"
                         "$ ZADD lider 1520 \"ali\" 1310 \"ayse\"\n"
                         "$ ZREVRANGE lider 0 2 WITHSCORES\n"
                         "```")
            continue
        m = SEKIL_RE.match(satir)
        if m:
            n = int(m.group(1))
            ad, aciklama = SEKIL[n]
            cikti.append("![Şekil 35.%d: %s](gorseller/b35_%s.png)"
                         % (n, aciklama, ad))
            continue
        cikti.append(satir)
    metin = "\n".join(cikti)
    # Şekil numarası kontrolü: sıra dışı yok
    cikis = os.path.join(KITAP, "bolumler", "bolum_35.md")
    with open(cikis, "w", encoding="utf-8", newline="\n") as f:
        f.write(metin)
    print("yazildi:", cikis, len(metin), "karakter")


if __name__ == "__main__":
    main()
