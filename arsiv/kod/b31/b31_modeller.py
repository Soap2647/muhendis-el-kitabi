# -*- coding: utf-8 -*-
"""b31_modeller.py: ayni yanki sunucusunun 6 eszamanlilik modeli.

Protokol: uzunluk onekli cerceve (b31_cerceve), 64 baytlik yuk, yanki.
Kullanim (WSL2, Linux'ta calistirilir: fork ve epoll Linux'a ozgu):
  python3 b31_modeller.py sunucu MODEL PORT
  python3 b31_modeller.py olc CSV_YOLU       # tum modelleri olcer
  python3 b31_modeller.py tek MODEL N         # tek olcum
Modeller: iteratif, fork, thread, havuz, epoll, asyncio
"""

import asyncio
import multiprocessing as mp
import os
import random
import select
import signal
import socket
import struct
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b31_cerceve import cerceve_al, cerceve_gonder, tam_oku

MODELLER = ["iteratif", "fork", "thread", "havuz", "epoll", "asyncio"]
YUK_BOYU = 64
HAVUZ_ISCI = 16
BEKLEME_BACKLOG = 1024


def dinleyici(port):
    ls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ls.bind(("127.0.0.1", port))
    ls.listen(BEKLEME_BACKLOG)
    return ls


# ---------- Sunucu modelleri (bloklayan kod) ---------------- #


def baglanti_dongusu(c):
    """Tek bir baglantida: al, yanki, tekrarla. Karsi taraf kapaninca
    donus. Bloklayici soket: her cagri bu is parcacigini uyutur."""
    try:
        while True:
            yuk = cerceve_al(c)
            cerceve_gonder(c, yuk)
    except (EOFError, ConnectionError, OSError):
        pass
    finally:
        c.close()


def sunucu_iteratif(port):
    ls = dinleyici(port)
    while True:
        c, _ = ls.accept()
        baglanti_dongusu(c)  # bitene kadar baskasina bakmaz


def sunucu_fork(port):
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)  # zombi olusmasin
    ls = dinleyici(port)
    while True:
        c, _ = ls.accept()
        pid = os.fork()
        if pid == 0:  # cocuk: dinleyiciyi kapat, isi yap
            ls.close()
            baglanti_dongusu(c)
            os._exit(0)
        c.close()  # ebeveyn: kopyasini kapat


def sunucu_thread(port):
    ls = dinleyici(port)
    while True:
        c, _ = ls.accept()
        threading.Thread(
            target=baglanti_dongusu, args=(c,), daemon=True
        ).start()


def sunucu_havuz(port):
    ls = dinleyici(port)
    havuz = ThreadPoolExecutor(max_workers=HAVUZ_ISCI)
    while True:
        c, _ = ls.accept()
        havuz.submit(
            baglanti_dongusu, c
        )  # is = baglanti; havuz sinirli


# ---------- Olay tabanli modeller -------------------------- #


class Baglanti:
    __slots__ = ("soket", "gelen", "giden", "kapanacak")

    def __init__(self, soket):
        self.soket = soket
        self.gelen = bytearray()  # okunmamis ham bayt
        self.giden = bytearray()  # henuz gonderilmemis cikti
        self.kapanacak = False


def sunucu_epoll(port):
    ls = dinleyici(port)
    ls.setblocking(False)
    ep = select.epoll()
    ep.register(ls.fileno(), select.EPOLLIN)
    baglar = {}
    dinl = ls.fileno()
    while True:
        for fd, olay in ep.poll():
            if fd == dinl:
                while True:  # kenar degil ama tum bekleyenleri al
                    try:
                        c, _ = ls.accept()
                    except BlockingIOError:
                        break
                    c.setblocking(False)
                    c.setsockopt(
                        socket.IPPROTO_TCP, socket.TCP_NODELAY, 1
                    )
                    baglar[c.fileno()] = Baglanti(c)
                    ep.register(c.fileno(), select.EPOLLIN)
                continue
            b = baglar[fd]
            if olay & (select.EPOLLERR | select.EPOLLHUP):
                _kapat(ep, baglar, fd)
                continue
            if olay & select.EPOLLIN:
                _oku_cerceveleri(b)
                if b.kapanacak and not b.giden:
                    _kapat(ep, baglar, fd)
                    continue
            if b.giden:
                _yaz(b)
            if b.giden:
                ep.modify(fd, select.EPOLLIN | select.EPOLLOUT)
            else:
                ep.modify(fd, select.EPOLLIN)
                if b.kapanacak:
                    _kapat(ep, baglar, fd)


def _oku_cerceveleri(b):
    """Olan tum baytlari oku; tam cerceveleri yanki kuyruguna koy."""
    while True:
        try:
            parca = b.soket.recv(65536)
        except BlockingIOError:
            break
        if not parca:  # karsi taraf FIN gonderdi
            b.kapanacak = True
            break
        b.gelen += parca
    while len(b.gelen) >= 4:
        (n,) = struct.unpack_from("!I", b.gelen, 0)
        if len(b.gelen) < 4 + n:
            break  # yarim cerceve: sonraki olayi bekle
        yuk = bytes(b.gelen[4 : 4 + n])
        del b.gelen[: 4 + n]
        b.giden += struct.pack("!I", n) + yuk


def _yaz(b):
    """Yazmayi mumkun oldugu kadar yap; kalanlar giden'de kalir."""
    try:
        k = b.soket.send(b.giden)
        del b.giden[:k]
    except BlockingIOError:
        pass


def _kapat(ep, baglar, fd):
    ep.unregister(fd)
    baglar.pop(fd).soket.close()


async def _asyncio_el(reader, writer):
    try:
        while True:
            (n,) = struct.unpack("!I", await reader.readexactly(4))
            yuk = await reader.readexactly(n)
            writer.write(struct.pack("!I", n) + yuk)
            await writer.drain()
    except (asyncio.IncompleteReadError, ConnectionError):
        pass
    finally:
        writer.close()


async def _asyncio_ana(port):
    srv = await asyncio.start_server(
        _asyncio_el, "127.0.0.1", port, backlog=BEKLEME_BACKLOG
    )
    async with srv:
        await srv.serve_forever()


def sunucu_asyncio(port):
    asyncio.run(_asyncio_ana(port))


SUNUCULAR = {
    "iteratif": sunucu_iteratif,
    "fork": sunucu_fork,
    "thread": sunucu_thread,
    "havuz": sunucu_havuz,
    "epoll": sunucu_epoll,
    "asyncio": sunucu_asyncio,
}


# ---------- Yuk uretici (istemci) -------------------------- #


def _istemci_is(port, istek, yuk, gecikmeler):
    # Ilk isteğin gecikmesi baglanti kurulumunu da kapsar: sunucu
    # kuyrukta bekleyen istemciyi yavaslatir ve bu olcume girmelidir.
    t0 = time.perf_counter()
    s = socket.create_connection(("127.0.0.1", port))
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    for i in range(istek):
        if i:
            t0 = time.perf_counter()
        cerceve_gonder(s, yuk)
        cerceve_al(s)
        gecikmeler.append(time.perf_counter() - t0)
    s.close()


def _grup(port, baglanti, istek, tohum):
    """Bir surecte birden cok istemci iş parçacığı."""
    rnd = random.Random(tohum)
    yuk = bytes(rnd.getrandbits(8) for _ in range(YUK_BOYU))
    gecikmeler = []
    ths = [
        threading.Thread(
            target=_istemci_is, args=(port, istek, yuk, gecikmeler)
        )
        for _ in range(baglanti)
    ]
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    return gecikmeler


def yuk_olc(port, n, istek, surec=4):
    """n eşzamanli baglanti, her biri istek kez yanki yapar."""
    pay = [
        n // surec + (1 if i < n % surec else 0) for i in range(surec)
    ]
    pay = [p for p in pay if p > 0]
    t0 = time.perf_counter()
    with mp.Pool(len(pay)) as pool:
        sonuclar = pool.starmap(
            _grup,
            [(port, p, istek, 31 + i) for i, p in enumerate(pay)],
        )
    sure = time.perf_counter() - t0
    gec = sorted(x for g in sonuclar for x in g)
    toplam = len(gec)
    p50 = gec[toplam // 2] * 1000
    p99 = gec[int(toplam * 0.99) - 1] * 1000
    return toplam / sure, p50, p99, gec[-1] * 1000


def _bekle(port):
    for _ in range(300):
        try:
            socket.create_connection(("127.0.0.1", port)).close()
            return
        except OSError:
            time.sleep(0.02)
    raise RuntimeError("sunucu acilmadi")


def tek_olcum(model, n, istek, port):
    p = subprocess.Popen(
        [
            sys.executable,
            os.path.abspath(__file__),
            "sunucu",
            model,
            str(port),
        ]
    )
    try:
        _bekle(port)
        return yuk_olc(port, n, istek)
    finally:
        p.terminate()
        p.wait()


def olc(csv_yolu):
    # Ayni yanki protokolu: N eşzamanli istemci, her biri 200 istek.
    # Tekrar: 3 kez; medyan alinir. Port: her olcum icin ayri.
    istek = 200
    dizi = [1, 16, 64, 256]
    satirlar = ["model,n,istek_s,p50_ms,p99_ms,maks_ms"]
    port = 9100
    for model in MODELLER:
        for n in dizi:
            sonuc = []
            for _ in range(3):
                port += 1
                sonuc.append(tek_olcum(model, n, istek, port))
            ist = sorted(s[0] for s in sonuc)[1]
            p50 = sorted(s[1] for s in sonuc)[1]
            p99 = sorted(s[2] for s in sonuc)[1]
            mks = sorted(s[3] for s in sonuc)[1]
            satir = "%s,%d,%.0f,%.3f,%.3f,%.3f" % (
                model,
                n,
                ist,
                p50,
                p99,
                mks,
            )
            print(satir, flush=True)
            satirlar.append(satir)
    with open(csv_yolu, "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")


if __name__ == "__main__":
    kip = sys.argv[1]
    if kip == "sunucu":
        SUNUCULAR[sys.argv[2]](int(sys.argv[3]))
    elif kip == "olc":
        olc(sys.argv[2])
    elif kip == "tek":
        m, n = sys.argv[2], int(sys.argv[3])
        ist, p50, p99, mks = tek_olcum(m, n, 200, 9500)
        print(
            "%s n=%d: %.0f istek/s, p50=%.3f ms, p99=%.3f ms, "
            "maks=%.3f ms" % (m, n, ist, p50, p99, mks)
        )
