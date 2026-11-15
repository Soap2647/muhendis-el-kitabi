# -*- coding: utf-8 -*-
"""Model kayit defteri: surum, asama, ozet ve geri alma.

Her surum bir dosyadir; kayit defteri dosyanin SHA-256 ozetini saklar.
Yukleme sirasinda ozet yeniden hesaplanir; eslesmezse model yuklenmez.
"""
import json
import os

import joblib

from b77_veri import ozet


class KayitDefteri:
    def __init__(self, kok="calisma/kayit"):
        self.kok = kok
        self.dosya = os.path.join(kok, "index.json")
        os.makedirs(kok, exist_ok=True)
        self.idx = {}
        if os.path.exists(self.dosya):
            with open(self.dosya, encoding="utf-8") as f:
                self.idx = json.load(f)

    def _kaydet(self):
        with open(self.dosya, "w", encoding="utf-8") as f:
            json.dump(self.idx, f, indent=2, ensure_ascii=False)

    def kaydet(self, ad, model, deney, veri):
        """Yeni surum yazar; asamasi 'kayitli' olarak baslar."""
        surumler = self.idx.setdefault(ad, [])
        n = len(surumler) + 1
        yol = os.path.join(self.kok, ad, "v%d.joblib" % n)
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        joblib.dump(model, yol)
        surumler.append({"surum": n, "dosya": yol,
                         "sha256": ozet(yol),
                         "deney": deney, "veri": veri,
                         "asama": "kayitli"})
        self._kaydet()
        return n

    def asama_ata(self, ad, n, asama):
        """Asama atar. 'production' ise eski surum arsive gider."""
        for s in self.idx[ad]:
            if asama == "production" and s["asama"] == "production":
                s["asama"] = "arsiv"
            if s["surum"] == n:
                s["asama"] = asama
        self._kaydet()

    def yukle(self, ad, asama):
        """Asamadaki surumu yukler; once ozeti dogrular."""
        for s in self.idx[ad]:
            if s["asama"] == asama:
                if ozet(s["dosya"]) != s["sha256"]:
                    raise ValueError(
                        "%s v%d bozulmus" % (ad, s["surum"]))
                # yalniz kendi dosyani yukle
                return joblib.load(s["dosya"])
        raise KeyError("%s icin %s surumu yok" % (ad, asama))

    def geri_al(self, ad):
        """Uretimdeki surumu, son arsiv surumuyle degistirir."""
        surumler = self.idx[ad]
        uretim = [s for s in surumler if s["asama"] == "production"]
        arsiv = [s for s in surumler if s["asama"] == "arsiv"]
        if not uretim or not arsiv:
            raise KeyError("geri alinacak surum yok")
        hedef = max(arsiv, key=lambda s: s["surum"])
        uretim[0]["asama"] = "geri_alindi"
        hedef["asama"] = "production"
        self._kaydet()
        return hedef["surum"]

    def goster(self, ad):
        for s in self.idx[ad]:
            print("  v%d  %-12s deney=%s veri=%s" %
                  (s["surum"], s["asama"], s["deney"], s["veri"][:8]))


if __name__ == "__main__":
    import shutil

    import numpy as np

    from b77_telemetri import model_kur, uret
    shutil.rmtree("calisma/kayit", ignore_errors=True)
    kd = KayitDefteri()
    veri = ozet("calisma/egitim.csv")
    X, y = uret(2000, np.random.default_rng(3))
    for i, C in enumerate([1.0, 0.1, 10.0], 1):
        n = kd.kaydet("batarya", model_kur(C).fit(X, y), i, veri)
        kd.asama_ata("batarya", n, "production")
        print("v%d kaydedildi ve uretime alindi (C=%s)" % (n, C))
    print("--- durum (geri alma oncesi)")
    kd.goster("batarya")
    print("geri alinan surum:", kd.geri_al("batarya"))
    print("--- durum (geri alma sonrasi)")
    kd.goster("batarya")
    m = kd.yukle("batarya", "production")
    print("uretim modeli yuklendi:", type(m).__name__)
    with open(kd.idx["batarya"][1]["dosya"], "ab") as f:
        f.write(b"!")                          # v2 dosyasini bozalim
    try:
        kd.yukle("batarya", "production")
    except ValueError as e:
        print("yukleme reddedildi:", e)
