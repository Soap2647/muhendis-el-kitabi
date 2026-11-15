# -*- coding: utf-8 -*-
"""b45_i2c.py: I2C bit duzeyi simulasyonu (acik-drenaj, wired-AND).

Her adim yarim bit suresidir. Cihazlar uretec (generator) olarak
calisir ve yalnizca kendi SDA/SCL cekme durumlarini ayarlar. Hat,
cihazlardan herhangi biri 0 cektiyse 0, aksi halde direnc 1 verir.
Cihazlar bir onceki adimin hat durumunu okur (bir adim gecikmeli).
SIMULASYONDUR; gercek bir osiloskop olcumu degildir.
"""
import csv
import math


class Cihaz:
    def __init__(self, ad=None):
        self.ad = ad
        self.sda_cek = False       # True: SDA'yi 0'a ceker
        self.scl_cek = False       # True: SCL'i 0'a ceker
        self.gen = None
        self.bellek = [0] * 256    # uydu: kayit alani
        self.ptr = 0
        self.germe = 0             # uydu: ACK'ta SCL'i kac adim tut
        self.okunan = []           # ana: okunan baytlar
        self.ana = False           # bitince simulasyonu durdurur mu


class Otobus:
    def __init__(self, cihazlar):
        self.cihazlar = cihazlar
        self.son = (1, 1)          # (scl, sda) onceki adim
        self.t = 0
        self.kayit = []            # (t, scl, sda, cek_1, cek_2, ...)
        self.olaylar = []          # (t, etiket)

    def hat(self):
        scl = 0 if any(c.scl_cek for c in self.cihazlar) else 1
        sda = 0 if any(c.sda_cek for c in self.cihazlar) else 1
        return scl, sda

    def olay(self, etiket):
        self.olaylar.append((self.t, etiket))

    def calistir(self, azami=3000):
        while self.t < azami:
            canli = False
            for c in self.cihazlar:
                if c.gen is None:
                    continue
                canli = True
                try:
                    next(c.gen)
                except StopIteration:
                    c.gen = None
            self.son = self.hat()
            self.t += 1
            self.kayit.append(
                (self.t, self.son[0], self.son[1]) +
                tuple(int(c.sda_cek) for c in self.cihazlar))
            analar = [c for c in self.cihazlar if c.ana]
            if not canli or (analar and all(c.gen is None for c in analar)):
                break


def kenar(bus, mod):
    """Hat olaylarini bekler.
    'RISE'      : SCL 0->1
    'FALL'      : SCL 1->0
    'OLAY'      : RISE veya (SCL=1 iken) START/STOP
    'FALL_OLAY' : FALL veya (SCL=1 iken) START/STOP
    'START'     : yalnizca (SCL=1 iken) START
    START: SDA 1->0, STOP: SDA 0->1 (SCL=1 iken).
    Donus: 'RISE' 'FALL' 'START' 'STOP'."""
    prev = bus.son
    while True:
        yield
        cur = bus.son
        if mod in ("RISE", "OLAY") and prev[0] == 0 and cur[0] == 1:
            return "RISE"
        if mod in ("FALL", "FALL_OLAY") and prev[0] == 1 and cur[0] == 0:
            return "FALL"
        if prev[0] == 1 and cur[0] == 1 and prev[1] != cur[1]:
            if prev[1] == 1 and cur[1] == 0:
                return "START"
            if mod != "START":
                return "STOP"
        prev = cur


# ---------------- ANA (master) ----------------
def bit_yaz(bus, c, bit):
    c.sda_cek = (bit == 0)            # SCL dusukken veri hazirla
    c.scl_cek = True
    yield
    c.scl_cek = False                 # SCL'i birak
    yield
    while bus.son[0] == 0:            # saat germe
        yield
    okunan = bus.son[1]
    yield
    c.scl_cek = True
    yield
    return okunan


def bayt_yaz(bus, c, bayt, etiket):
    for i in range(7, -1, -1):
        bit = (bayt >> i) & 1
        okunan = yield from bit_yaz(bus, c, bit)
        if bit == 1 and okunan == 0:  # tahkim: 1 yazdim, 0 okudum
            bus.olay("KAYIP %s" % etiket)
            c.sda_cek = c.scl_cek = False
            return "KAYIP"
    c.sda_cek = False                 # ACK biti: SDA birak
    c.scl_cek = True
    yield
    c.scl_cek = False
    yield
    while bus.son[0] == 0:
        yield
    cevap = "ACK" if bus.son[1] == 0 else "NACK"
    yield
    c.scl_cek = True
    yield
    return cevap


def bayt_oku(bus, c):
    c.sda_cek = False
    deger = 0
    for _ in range(8):
        c.scl_cek = True
        yield
        c.scl_cek = False
        yield
        while bus.son[0] == 0:
            yield
        deger = (deger << 1) | bus.son[1]
        yield
        c.scl_cek = True
        yield
    return deger


def ana_islem(bus, c, islemler):
    """islemler: ('S',) ('W', bayt) ('R', n) ('P',)."""
    c.sda_cek = c.scl_cek = False
    yield
    for op in islemler:
        if op[0] == "S":              # SCL dusukken SDA birak, sonra
            c.scl_cek = True          # SCL yuksek iken SDA dusur
            yield
            c.scl_cek = False
            yield
            c.sda_cek = True
            bus.olay("START")
            yield
            c.scl_cek = True
            yield
        elif op[0] == "W":
            sonuc = yield from bayt_yaz(bus, c, op[1], "0x%02X" % op[1])
            if sonuc == "KAYIP":
                return
            bus.olay("%s 0x%02X" % (sonuc, op[1]))
        elif op[0] == "R":
            for k in range(op[1]):
                deger = yield from bayt_oku(bus, c)
                c.okunan.append(deger)
                son = (k == op[1] - 1)
                c.sda_cek = not son   # ACK=0 (SDA cek), son=NACK
                c.scl_cek = True
                yield
                c.scl_cek = False
                yield
                while bus.son[0] == 0:
                    yield
                c.scl_cek = True
                yield
                c.sda_cek = False
                bus.olay("OKU 0x%02X" % deger)
        elif op[0] == "P":
            c.sda_cek = True          # SCL dusukken SDA dusur
            c.scl_cek = True
            yield
            c.scl_cek = False         # SCL yuksek
            yield
            c.sda_cek = False         # SDA yuksel: STOP
            bus.olay("STOP")
            yield
    c.sda_cek = c.scl_cek = False


# ---------------- UYDU (slave) ----------------
def bayt_al(bus):
    """8 bit oku. Donus: (olay, bayt) olay = 'BAYT' | 'START' | 'STOP'."""
    deger = 0
    for _ in range(8):
        r = yield from kenar(bus, "OLAY")
        if r != "RISE":
            return r, None
        bit = bus.son[1]
        r = yield from kenar(bus, "FALL_OLAY")
        if r != "FALL":                # STOP/START: bit sayilmaz
            return r, None
        deger = (deger << 1) | bit
    return "BAYT", deger


def ack_ver(bus, c):
    """9. bit: SDA'yi cek. Istenirse SCL'i gerip (saat germe)."""
    c.sda_cek = True
    for _ in range(c.germe):
        c.scl_cek = True
        yield
    c.scl_cek = False
    yield from kenar(bus, "RISE")
    yield from kenar(bus, "FALL")
    c.sda_cek = False
    c.germe = 0


def bayt_gonder(bus, c, bayt):
    for i in range(7, -1, -1):
        c.sda_cek = ((bayt >> i) & 1) == 0
        yield from kenar(bus, "RISE")
        yield from kenar(bus, "FALL")
    c.sda_cek = False


def ack_al(bus):
    yield from kenar(bus, "RISE")
    ack = (bus.son[1] == 0)
    yield from kenar(bus, "FALL")
    return ack


def kole(bus, c, ad):
    """7 bit adres ad. Yaz: ilk bayt isaretci, sonrasi veri.
    Oku: bellekten ardisik bayt gonderir."""
    bekleyen = None                   # START olayi zaten geldi mi?
    while True:
        if bekleyen != "START":
            yield from kenar(bus, "START")
        bekleyen = None
        olay, adres = yield from bayt_al(bus)
        if olay != "BAYT":
            bekleyen = olay if olay == "START" else None
            continue
        if (adres >> 1) != ad:
            continue                  # bu hedef degil: ACK yok
        yield from ack_ver(bus, c)
        bus.olay("ACK(uydu) 0x%02X" % adres)
        if adres & 1 == 0:
            ilk = True
            while True:
                olay, b = yield from bayt_al(bus)
                if olay != "BAYT":
                    bekleyen = olay if olay == "START" else None
                    break
                if ilk:
                    c.ptr = b
                    ilk = False
                else:
                    c.bellek[c.ptr] = b
                    c.ptr = (c.ptr + 1) & 0xFF
                yield from ack_ver(bus, c)
        else:
            while True:
                yield from bayt_gonder(bus, c, c.bellek[c.ptr])
                c.ptr = (c.ptr + 1) & 0xFF
                if not (yield from ack_al(bus)):
                    break             # NACK: ana okumayi bitirdi
            # ana STOP/START gonderecek; bir sonraki olayi bekle


# ---------------- Senaryolar ----------------
def yaz_oku_senaryosu(germe=0):
    """Uydu 0x50. Ana: 0x10'a iki bayt yaz, tekrarlanan START ile oku."""
    ana = Cihaz("ana")
    ana.ana = True
    uydu = Cihaz("uydu50")
    uydu.germe = germe
    bus = Otobus([ana, uydu])
    ana.gen = ana_islem(bus, ana, [
        ("S",), ("W", 0xA0), ("W", 0x10), ("W", 0x5A), ("W", 0x6B),
        ("P",), ("S",), ("W", 0xA0), ("W", 0x10),
        ("S",), ("W", 0xA1), ("R", 2), ("P",)])
    uydu.gen = kole(bus, uydu, 0x50)
    bus.calistir()
    return ana, uydu, bus


def tahkim_senaryosu():
    """Iki ana ayni anda basliyor: 0x50 (0xA0) ve 0x51 (0xA2) yazma.
    Ilk farkli bit: bit 1 (LSB'den bir ust). 0x51 kaybeder."""
    a = Cihaz("anaA")
    a.ana = True
    b = Cihaz("anaB")
    b.ana = True
    u = Cihaz("uydu50")
    bus = Otobus([a, b, u])
    a.gen = ana_islem(bus, a, [("S",), ("W", 0xA0), ("W", 0x10),
                               ("P",)])
    b.gen = ana_islem(bus, b, [("S",), ("W", 0xA2), ("W", 0x10),
                               ("P",)])
    u.gen = kole(bus, u, 0x50)
    bus.calistir()
    return a, b, u, bus


def adres_yok_senaryosu():
    """0x77 adresli aygit yok: ana NACK alir."""
    ana = Cihaz("ana")
    ana.ana = True
    uydu = Cihaz("uydu50")
    bus = Otobus([ana, uydu])
    ana.gen = ana_islem(bus, ana, [("S",), ("W", 0xEE), ("P",)])
    uydu.gen = kole(bus, uydu, 0x50)
    bus.calistir()
    return bus


def kurtarma_senaryosu():
    """Uydu, 8 bit boyunca SDA'yi 0'da tutar (hat kilitli).
    Ana 9 saat darbesi uygular; 9. darbeden sonra SDA serbest kalir."""
    ana = Cihaz("ana")
    ana.ana = True
    kilit = Cihaz("kilit")
    bus = Otobus([ana, kilit])

    def kilitli(c, bus_):
        c.sda_cek = True
        sayac = 0
        while sayac < 8:
            yield from kenar(bus_, "RISE")
            sayac += 1
            yield from kenar(bus_, "FALL")
        c.sda_cek = False

    def darbe(c, bus_):
        c.sda_cek = False
        for k in range(9):
            c.scl_cek = True
            yield
            c.scl_cek = False
            yield
            while bus_.son[0] == 0:
                yield
            bus_.olay("darbe %d, SDA=%d" % (k + 1, bus_.son[1]))
            yield
        c.scl_cek = False

    ana.gen = darbe(ana, bus)
    kilit.gen = kilitli(kilit, bus)
    bus.calistir()
    return bus


def pullup_yukselme(R, C, VDD=3.3):
    """RC ile yukselme suresi %30 -> %70 (saniye). Sayisal integral."""
    tau = R * C
    dt = tau / 20000.0
    t, t30, t70 = 0.0, None, None
    while True:
        v = VDD * (1 - math.exp(-t / tau))
        if t30 is None and v >= 0.3 * VDD:
            t30 = t
        if v >= 0.7 * VDD:
            t70 = t
            break
        t += dt
    return t70 - t30


def pullup_sinirlari(Cb=400e-12, VDD=3.3, tr_max=300e-9, IOL=3e-3,
                     VOL=0.4):
    """UM10204 'de: Rmax = tr/(0.8473 Cb), Rmin = (VDD-VOL)/IOL."""
    rmax = tr_max / (0.8473 * Cb)
    rmin = (VDD - VOL) / IOL
    return rmin, rmax


if __name__ == "__main__":
    import sys
    yaz = "--yaz" in sys.argv
    ana, uydu, bus = yaz_oku_senaryosu()
    print("1) yaz/oku: ana aldi =", [hex(x) for x in ana.okunan])
    print("   uydu bellek[0x10..0x11] =",
          [hex(uydu.bellek[0x10]), hex(uydu.bellek[0x11])])
    print("   olaylar:", [o[1] for o in bus.olaylar][:12])
    ana, uydu, bus = yaz_oku_senaryosu(germe=4)
    print("2) saat germe (4 adim): ana aldi =",
          [hex(x) for x in ana.okunan], " adim sayisi =", bus.t)
    a, b, u, tbus = tahkim_senaryosu()
    print("3) tahkim:", [o[1] for o in tbus.olaylar if "KAYIP" in o[1]])
    bus = adres_yok_senaryosu()
    print("4) adres yok:", [o[1] for o in bus.olaylar])
    bus = kurtarma_senaryosu()
    print("5) kurtarma:", [o[1] for o in bus.olaylar])
    rmin, rmax = pullup_sinirlari()
    print("pull-up Rmin=%.0f ohm  Rmax(hizli)=%.0f ohm" % (rmin, rmax))
    tr = pullup_yukselme(4700, 100e-12)
    print("R=4.7k C=100p: tr=%.1f ns, 0.8473RC=%.1f ns" %
          (tr * 1e9, 0.8473 * 4700 * 100e-12 * 1e9))
    if yaz:
        import os
        veri = "D:/Mevcut Projeler/Kitap/engine/veri"
        _, _, _, tb = tahkim_senaryosu()
        with open(veri + "/b45_i2c_tahkim.csv", "w", newline="",
                  encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["t", "scl", "sda", "ana_a_cek", "ana_b_cek",
                        "uydu_cek"])
            w.writerows(tb.kayit)
        ana, uydu, bus = yaz_oku_senaryosu()
        with open(veri + "/b45_i2c_iz.csv", "w", newline="",
                  encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["t", "scl", "sda", "ana_cek", "uydu_cek"])
            w.writerows(bus.kayit)
        with open(veri + "/b45_i2c_olay.csv", "w", newline="",
                  encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["t", "olay"])
            w.writerows(bus.olaylar)
        print("CSV yazildi")
