# -*- coding: utf-8 -*-
"""Icerik-adresli veri deposu: DVC'nin kucuk bir benzeri.

Dosya adina degil icerigin SHA-256 ozetine gore saklanir.
Git'e buyuk veri yerine yalnizca kucuk bir isaretci (.veri) girer.
"""
import glob
import hashlib
import json
import os
import shutil

DEPO = "calisma/depo_veri"


def ozet(yol):
    """Dosyanin SHA-256 ozetini parca parca hesaplar."""
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def nesne_yolu(d, depo=DEPO):
    return os.path.join(depo, d[:2], d[2:])


def ekle(yol, depo=DEPO):
    """Dosyayi depoya koyar ve yanina isaretci (.veri) yazar."""
    d = ozet(yol)
    hedef = nesne_yolu(d, depo)
    if not os.path.exists(hedef):          # ayni icerik tek kez
        os.makedirs(os.path.dirname(hedef), exist_ok=True)
        shutil.copyfile(yol, hedef)
    isaret = {"yol": os.path.basename(yol), "sha256": d,
              "boyut": os.path.getsize(yol)}
    with open(yol + ".veri", "w", encoding="utf-8") as f:
        json.dump(isaret, f, indent=2, ensure_ascii=False)
    return d


def dogrula(isaret_yolu, depo=DEPO):
    """Depodaki nesne, isaretcideki ozetle hala eslesiyor mu?"""
    with open(isaret_yolu, encoding="utf-8") as f:
        d = json.load(f)["sha256"]
    yol = nesne_yolu(d, depo)
    return os.path.exists(yol) and ozet(yol) == d


def getir(isaret_yolu, hedef, depo=DEPO):
    """Isaretciye karsilik gelen nesneyi hedef yola geri koyar."""
    with open(isaret_yolu, encoding="utf-8") as f:
        d = json.load(f)["sha256"]
    kaynak = nesne_yolu(d, depo)
    if ozet(kaynak) != d:
        raise IOError("nesne bozulmus: " + d[:12])
    shutil.copyfile(kaynak, hedef)
    return d


if __name__ == "__main__":
    shutil.rmtree(DEPO, ignore_errors=True)       # temiz baslangic
    os.makedirs("calisma", exist_ok=True)
    yol = "calisma/telemetri.csv"
    with open(yol, "w", encoding="utf-8") as f:
        f.write("sicaklik,akim\n31.2,9.8\n28.7,10.4\n")
    d1 = ekle(yol)
    shutil.copyfile(yol + ".veri", "calisma/v1.veri")
    print("v1 ozeti      :", d1[:16])
    shutil.copyfile(yol, "calisma/kopya.csv")
    d2 = ekle("calisma/kopya.csv")
    print("kopya ayni mi :", d1 == d2)
    print("depoda nesne  :", len(glob.glob(DEPO + "/*/*")))
    with open(yol, "a", encoding="utf-8") as f:
        f.write("30.1,10.0\n")
    d3 = ekle(yol)
    print("v2 ozeti      :", d3[:16])
    print("depoda nesne  :", len(glob.glob(DEPO + "/*/*")))
    with open("calisma/v1.veri", encoding="utf-8") as f:
        isaret = json.load(f)
    print("isaretci      :", isaret["yol"], isaret["boyut"],
          isaret["sha256"][:16] + "...")
    with open(nesne_yolu(d1), "ab") as f:      # depoyu elle boz
        f.write(b"x")
    print("v1 dogrula    :", dogrula("calisma/v1.veri"))
    try:
        getir("calisma/v1.veri", "calisma/geri.csv")
    except IOError as e:
        print("getir hatasi  :", e)
