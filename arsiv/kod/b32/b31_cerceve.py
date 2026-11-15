# -*- coding: utf-8 -*-
"""b31_cerceve.py: TCP uzerinde cerceveleme (framing) kutuphanesi.

Kullanim:
  python b31_cerceve.py test     # sahte soketle deterministik testler
  python b31_cerceve.py kisa     # kisa okuma, birlesen mesajlar
"""

import random
import socket
import struct
import sys
import threading
import time

MAKS = 1 << 20  # tek cerceve icin ust sinir: 1 MiB


class ParcaliSoket:
    """Gelen baytlari parcalar halinde teslim eden sahte soket.
    recv(n) en fazla bir parca dondurur ve n'den fazlasini vermez."""

    def __init__(self, parcalar):
        self.parcalar = [bytearray(p) for p in parcalar]

    def recv(self, n):
        if not self.parcalar:
            return b""  # karsi taraf kapandi
        ilk = self.parcalar[0]
        k = min(n, len(ilk))
        cikti = bytes(ilk[:k])
        del ilk[:k]
        if not ilk:
            self.parcalar.pop(0)
        return cikti


def tam_oku(s, n):
    """Tam n bayt okuyana kadar recv dongusu (kisa okumaya karsi)."""
    parcalar = []
    kalan = n
    while kalan > 0:
        b = s.recv(kalan)
        if not b:
            raise EOFError("karsi taraf yarim cercevede kapandi")
        parcalar.append(b)
        kalan -= len(b)
    return b"".join(parcalar)


def cerceve_gonder(s, yuk):
    """Uzunluk onekli cerceve: 4 bayt ag sirali uzunluk + yuk."""
    if len(yuk) > MAKS:
        raise ValueError("yuk sinirin uzerinde: %d" % len(yuk))
    s.sendall(struct.pack("!I", len(yuk)) + yuk)


def cerceve_al(s):
    (n,) = struct.unpack("!I", tam_oku(s, 4))
    if n > MAKS:  # guvenlik: bellek ayirmadan once sinir
        raise ValueError("cerceve uzunlugu sinirin uzerinde: %d" % n)
    return tam_oku(s, n)


def naif_cerceve_al(s):
    """YANLIS: tek recv cagrisi. Kisa okumada hatali sonuc verir."""
    (n,) = struct.unpack("!I", s.recv(4))
    return s.recv(n)


class SatirOkuyucu:
    """Ayraclı (satir sonu) cerceveleme; tamponu kendi tutar."""

    def __init__(self, s):
        self.s = s
        self.tampon = bytearray()

    def satir(self):
        while True:
            i = self.tampon.find(b"\n")
            if i >= 0:
                satir = bytes(self.tampon[:i])
                del self.tampon[: i + 1]
                return satir
            parca = self.s.recv(4096)
            if not parca:
                if self.tampon:
                    raise EOFError("yarim satir")
                return None
            self.tampon += parca


def test():
    rnd = random.Random(31)
    # 1) Uzunluk onekli: rastgele bolunmus akis
    mesajlar = [
        bytes(rnd.getrandbits(8) for _ in range(rnd.randint(0, 300)))
        for _ in range(200)
    ]
    akis = b"".join(struct.pack("!I", len(m)) + m for m in mesajlar)
    kesim = sorted(rnd.sample(range(1, len(akis)), 500))
    parca, onceki = [], 0
    for k in kesim:
        parca.append(akis[onceki:k])
        onceki = k
    parca.append(akis[onceki:])
    s = ParcaliSoket(parca)
    alinan = [cerceve_al(s) for _ in mesajlar]
    assert alinan == mesajlar, "uzunluk onekli cerceve hatali"
    print(
        "uzunluk onekli: %d mesaj, %d parcaya bolunmus akis: tamam"
        % (len(mesajlar), len(parca))
    )

    # 2) Naif okuyucu: baslik 2+2 bolunurse yanlis olur
    try:
        naif_cerceve_al(ParcaliSoket([b"\x00\x00", b"\x00\x03abc"]))
        print("naif: hata yok (beklenmiyordu)")
    except struct.error as e:
        print("naif: struct.error -> %s" % e)

    # 3) Ayni bolunmus akis, dogru okuyucu ile sorunsuz
    s = ParcaliSoket([b"\x00\x00", b"\x00\x03abc"])
    print("dogru: %r" % cerceve_al(s))

    # 4) Ayracli akis: satir sonu bolunsa bile dogru satirlar
    metin = "birinci\nikinci satır\nüçüçü\n".encode("utf-8")
    kesim = sorted(rnd.sample(range(1, len(metin)), 9))
    parca, onceki = [], 0
    for k in kesim:
        parca.append(metin[onceki:k])
        onceki = k
    parca.append(metin[onceki:])
    oku = SatirOkuyucu(ParcaliSoket(parca))
    satirlar = []
    while True:
        s_ = oku.satir()
        if s_ is None:
            break
        satirlar.append(s_)
    assert satirlar == metin.split(b"\n")[:-1], satirlar
    print("ayracli: %d satir, parcalara ragmen dogru" % len(satirlar))

    # 5) Sinir: asiri buyuk uzunluk reddedilir (bellek ayrilmadan)
    try:
        cerceve_al(ParcaliSoket([struct.pack("!I", 0xFFFFFFFF)]))
    except ValueError as e:
        print("sinir: reddedildi -> %s" % e)
    print("TUM TESTLER GECTI")


def kisa():
    """Gercek TCP: iki gonderim tek recv'de birlesir; tek gonderim
    birden cok recv'e bolunur."""
    ls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ls.bind(("127.0.0.1", 0))
    ls.listen(4)
    port = ls.getsockname()[1]
    istemci = socket.create_connection(("127.0.0.1", port))
    sunucu, _ = ls.accept()

    # Iki ayri sendall: TCP bunlari tek bir bayt akisi olarak tutar.
    istemci.sendall(b"ilk mesaj")
    istemci.sendall(b"ikinci mesaj")
    time.sleep(0.2)  # ikisi de alici tamponuna gelsin
    print("iki sendall -> tek recv: %r" % sunucu.recv(4096))

    # Tek 10000 baytlik gonderim, recv(1024) ile okunur.
    istemci.sendall(b"A" * 10000)
    toplam, cagri, boyutlar = 0, 0, []
    while toplam < 10000:
        b = sunucu.recv(1024)
        boyutlar.append(len(b))
        toplam += len(b)
        cagri += 1
    print(
        "10000 bayt, recv(1024): %d cagri, en buyuk parca %d"
        % (cagri, max(boyutlar))
    )
    print("son parca boyutu: %d, toplam: %d" % (boyutlar[-1], toplam))

    istemci.close()
    sunucu.close()
    ls.close()


if __name__ == "__main__":
    kip = sys.argv[1] if len(sys.argv) > 1 else "test"
    if kip == "test":
        test()
    elif kip == "kisa":
        kisa()
    else:
        print("kullanim: test | kisa")
