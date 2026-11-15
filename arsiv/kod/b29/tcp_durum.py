# -*- coding: utf-8 -*-
# tcp_durum.py - TCP durumlarını ss ile izler (root gerekmez).
# Sunucu port 0 ile açılır; eski soketler çıktıya karışmaz.
import socket
import subprocess
import time


def ss_goster(port, baslik):
    filtre = "( sport = :%d or dport = :%d )" % (port, port)
    cikti = subprocess.run(["ss", "-tan", filtre],
                           capture_output=True, text=True).stdout
    print("--- " + baslik)
    print(cikti.rstrip())


def main():
    sunucu = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sunucu.bind(("127.0.0.1", 0))
    sunucu.listen(5)
    port = sunucu.getsockname()[1]
    ss_goster(port, "1. listen() sonrası")

    istemci = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    istemci.connect(("127.0.0.1", port))
    baglanti, _ = sunucu.accept()
    time.sleep(0.05)
    ss_goster(port, "2. connect() + accept() sonrası")

    istemci.close()          # istemci önce kapatır: aktif kapanış
    time.sleep(0.05)
    print("--- 3. Sunucu EOF'u okuyana kadar (recv b'') ...")
    veri = baglanti.recv(16)
    print("    recv döndü:", veri)
    ss_goster(port, "3. istemci close() sonrası")

    baglanti.close()         # sunucu da kapatır
    time.sleep(0.05)
    ss_goster(port, "4. sunucu close() sonrası")

    sunucu.close()


if __name__ == "__main__":
    main()
