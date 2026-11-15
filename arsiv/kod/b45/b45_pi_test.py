# -*- coding: utf-8 -*-
"""b45_pi_test.py: EV Dashboard Pi tarafini (telemetri.py, kadran.py)
GERCEK dosyalari degistirmeden, sahte (fake) seri port ve soketle
calistirip davranisini olcer. Simulasyondur.
"""
import asyncio
import importlib.util
import sys
import types

KOK = ("D:/Mevcut Projeler/0-Bitmiş Projeler/Elektrikli Araba "
       "Dökümantasyon/ev-dashboard/rpi")


def modul_yukle(ad):
    yol = KOK + "/" + ad + ".py"
    spec = importlib.util.spec_from_file_location(ad, yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Bitti(Exception):
    pass


class SahteZaman:
    def __init__(self, zamanlar):
        self.z = list(zamanlar)

    def time(self):
        if not self.z:
            raise Bitti()
        return self.z.pop(0)


class SahteSeri:
    """readline: satirlari sirayla verir; bitince Bitti firlatir."""
    kayit = []

    def __init__(self, port, hiz, timeout=1):
        self.port = port
        self.satirlar = list(SahteSeri.girdi) if port == "/dev/ttyAMA2" else []
        self.yazilan = []
        SahteSeri.kayit.append(self)

    def readline(self):
        if not self.satirlar:
            raise Bitti()
        return self.satirlar.pop(0)

    def write(self, b):
        self.yazilan.append(b)
        return len(b)

    def flush(self):
        pass


def telemetri_calistir(satirlar, zamanlar):
    """telemetri.basla() gercek kodu; STM32 girdisi 'satirlar'."""
    m = modul_yukle("telemetri")
    SahteSeri.girdi = satirlar
    SahteSeri.kayit = []
    m.serial = types.SimpleNamespace(Serial=SahteSeri,
                                     SerialException=OSError)
    # son_gonderim=0.0 ile baslar; gercek time.time() epoch degeri verir
    m.time = SahteZaman([1000.0 + z for z in zamanlar])
    m.time.sleep = lambda s: None
    hata = None
    try:
        m.basla()
    except Bitti:
        pass
    except Exception as e:                  # servis cokusu
        hata = e
    rfd = [s for s in SahteSeri.kayit if s.port == "/dev/ttyUSB0"][0]
    return rfd.yazilan, hata


def telemetri_testleri():
    print("== telemetri.py (gercek kod, sahte seri) ==")
    iyi = b'{"spd":12,"bat":87}\n'
    # 1) normal: 200 ms araliklarla 3 paket
    yz, h = telemetri_calistir([iyi, iyi, iyi],
                               [0.0, 0.21, 0.42, 0.63, 0.84])
    print("1) 3 paket, 210 ms araliklı: iletilen=%d hata=%s" %
          (len(yz), h))
    yz, h = telemetri_calistir([iyi, iyi, iyi],
                               [0.0, 0.2, 0.4, 0.6, 0.8])
    print("1b) 3 paket, tam 200 ms: iletilen=%d (kayan nokta/jitter)" %
          len(yz))
    # 2) 0.19 s aralik: oran dusuyor (hiz siniri 200 ms)
    zam = [0.19 * k for k in range(12)]
    yz, h = telemetri_calistir([iyi] * 10, zam)
    print("2) 10 paket, 190 ms araliklı: iletilen=%d (siniri asan"
          " araliklar atilir)" % len(yz))
    # 3) bozuk JSON: sessizce atlanir
    yz, h = telemetri_calistir([b'{"spd":12', iyi],
                               [0.0, 0.3, 0.6])
    print("3) bozuk + iyi: iletilen=%d hata=%s" % (len(yz), h))
    # 4) gecersiz UTF-8: yakalanir
    yz, h = telemetri_calistir([b"\xff\xfe\n", iyi], [0.0, 0.3, 0.6])
    print("4) gecersiz UTF-8 + iyi: iletilen=%d hata=%s" % (len(yz), h))
    # 5) JSON ama sozluk degil ('5'): veri.get() cokusu
    yz, h = telemetri_calistir([b"5\n", iyi], [0.0, 0.3, 0.6])
    print("5) '5' satiri: iletilen=%d, servis hatasi = %s: %s" %
          (len(yz), type(h).__name__, h))


class SahteSoket:
    def __init__(self, ad):
        self.ad = ad
        self.gonderilen = []

    async def send(self, mesaj):
        await asyncio.sleep(0.01)
        self.gonderilen.append(mesaj)


def kadran_testi():
    print("\n== kadran.py yayinla (gercek kod) ==")
    k = modul_yukle("kadran")

    async def senaryo():
        k.istemciler.clear()
        k.istemciler.update({SahteSoket("A"), SahteSoket("B")})

        async def yeni_istemci():
            await asyncio.sleep(0.005)   # yayin 1. gonderimde
            k.istemciler.add(SahteSoket("C"))   # istemci_kayit ekler

        gorev = asyncio.create_task(yeni_istemci())
        try:
            await k.yayinla({"spd": 12})
            print("yeni baglanti yok: tamam")
        except RuntimeError as e:
            print("yayin sirasinda yeni baglanti -> RuntimeError: %s"
                  % e)
        await gorev
        # ikinci tur: kopan istemci de ayni hatayi uretir
        k.istemciler.clear()
        a, b = SahteSoket("A"), SahteSoket("B")
        k.istemciler.update({a, b})

        async def kopus():
            await asyncio.sleep(0.005)
            k.istemciler.discard(a)     # istemci_kayit'in finally'si

        gorev = asyncio.create_task(kopus())
        try:
            await k.yayinla({"spd": 13})
            print("kopus yok: tamam")
        except RuntimeError as e:
            print("kopus sirasinda -> RuntimeError: %s" % e)
        await gorev

    asyncio.run(senaryo())


if __name__ == "__main__":
    telemetri_testleri()
    kadran_testi()
    sys.exit(0)
