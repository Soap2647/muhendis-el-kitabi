# -*- coding: utf-8 -*-
"""Bölüm 41.8 - Devre kesici (circuit breaker) ve durum izi.

Durumlar: KAPALI (istek geçer), AÇIK (istek reddedilir),
YARI AÇIK (tek deneme isteğine izin verilir).
Saat: tam sayı tick. Hata ardışık `esik` kez olursa AÇIK olur;
AÇIK'ta `bekleme` tick geçince YARI AÇIK'a geçilir.
"""

KAPALI = "KAPALI"
ACIK = "AÇIK"
YARI = "YARI AÇIK"


#@@
class DevreKesici:
    def __init__(self, esik=3, bekleme=5):
        self.esik = esik
        self.bekleme = bekleme
        self.durum = KAPALI
        self.ardisik = 0
        self.acilis = None

    def _ac(self, t):
        self.durum = ACIK
        self.acilis = t
        self.ardisik = 0

    def cagir(self, t, islem):
        """islem() bir istisna fırlatırsa hata sayılır."""
        if self.durum == ACIK:
            if t - self.acilis < self.bekleme:
                return "REDDEDİLDİ"
            self.durum = YARI  # bekleme doldu: tek deneme
        deneme = self.durum == YARI
        try:
            islem()
        except Exception:
            if deneme:
                self._ac(t)  # deneme başarısız: yeniden aç
                return "DENEME HATA"
            self.ardisik += 1
            if self.ardisik >= self.esik:
                self._ac(t)
            return "HATA"
        self.durum = KAPALI  # başarı: kapat ve sayacı sıfırla
        self.ardisik = 0
        return "DENEME BAŞARI" if deneme else "BAŞARI"


#@@
def hata():
    raise IOError("bağlantı yok")


def basari():
    return "tamam"


#@@
if __name__ == "__main__":
    # Her tick'te bir çağrı yapılır. "H" hata, "B" başarı.
    # Reddedilen tick'lerde arka uç çağrılmaz.
    dizi = "BHHHHBHHHBBBBBBHHBBB"
    cb = DevreKesici(esik=3, bekleme=5)
    print("tick  önce        çağrı  sonuç         sonra")
    for t, c in enumerate(dizi):
        onceki = cb.durum
        islem = hata if c == "H" else basari
        sonuc = cb.cagir(t, islem)
        print(
            "%-5d %-12s  %s      %-14s %s"
            % (t, onceki, c, sonuc, cb.durum)
        )
