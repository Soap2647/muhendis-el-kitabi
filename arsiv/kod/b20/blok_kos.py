# -*- coding: utf-8 -*-
"""Kitaptaki terminal bloklarini GERCEK komutlarla calistirir.

Her blok: ad -> [(komut, calistirici)], calistirici: 'wsl' veya 'py'.
Cikti: cikti/<ad>.txt  (her komut icin '$ komut' satiri + gercek cikti)
"""
import os
import subprocess
import sys

KLASOR = os.path.dirname(os.path.abspath(__file__))
CIKTI = os.path.join(KLASOR, "cikti")
WSL_DIR = "/mnt/c/Users/merty/AppData/Local/Temp/b20"

BLOKLAR = {
    "c_vtable": [
        ("gcc -O2 -Wall -Wextra -std=c11 c_vtable.c -o c_vtable", "wsl"),
        ("./c_vtable", "wsl"),
    ],
    "cpp_vtable": [
        ("g++ -O2 -Wall -Wextra -std=c++17 cpp_vtable.cpp -o cpp_vtable",
         "wsl"),
        ("./cpp_vtable", "wsl"),
        ("nm -C cpp_vtable | grep 'vtable for [DS]'", "wsl"),
    ],
    "dizgi_test": [
        ("g++ -O1 -g -Wall -Wextra -std=c++17 -fsanitize=address,undefined "
         "dizgi_test.cpp -o dizgi_test", "wsl"),
        ("./dizgi_test", "wsl"),
    ],
    "dizgi_hata": [
        ("g++ -O1 -g -std=c++17 -fsanitize=address dizgi_hata.cpp "
         "-o dizgi_hata", "wsl"),
        ("./dizgi_hata 2>&1 | head -n 6", "wsl"),
    ],
    "yikici": [
        ("g++ -O0 -g -std=c++17 -Wall -Wextra yikici.cpp -o yikici_sizinti",
         "wsl"),
        ("./yikici_sizinti", "wsl"),
        ("g++ -O0 -g -std=c++17 -fsanitize=address yikici.cpp "
         "-o yikici_asan", "wsl"),
        ("ASAN_OPTIONS=new_delete_type_mismatch=0 ./yikici_asan 2>&1 "
         "| head -n 9", "wsl"),
        ("g++ -O0 -g -std=c++17 -fsanitize=address -DSANAL_YIKICI "
         "yikici.cpp -o yikici_sanal", "wsl"),
        ("./yikici_sanal", "wsl"),
    ],
    "dilimleme": [
        ("g++ -O2 -Wall -Wextra -std=c++17 dilimleme.cpp -o dilimleme",
         "wsl"),
        ("./dilimleme", "wsl"),
    ],
    "offs": [
        ("g++ -O2 -Wall -Wextra -std=c++17 offs.cpp -o offs", "wsl"),
        ("./offs", "wsl"),
    ],
    "sanal_olcum": [
        ("g++ -O2 -Wall -Wextra -std=c++17 sanal_olcum.cpp -o sanal_olcum",
         "wsl"),
        ("./sanal_olcum 1048576", "wsl"),
    ],
    "kesir_test": [
        ("g++ -O1 -g -Wall -Wextra -std=c++17 -fsanitize=address,undefined "
         "kesir_test.cpp -o kesir_test", "wsl"),
        ("./kesir_test", "wsl"),
    ],
    "py_kesir": [("python py_kesir.py", "py")],
    "raii": [
        ("g++ -O1 -g -Wall -Wextra -std=c++17 -fsanitize=address,undefined "
         "raii.cpp -o raii", "wsl"),
        ("./raii", "wsl"),
    ],
    "py_mro": [("python py_mro.py", "py")],
    "py_bellek": [("python py_bellek.py", "py")],
    "py_esitlik": [("python py_esitlik.py", "py")],
    "py_kaynak": [("python py_kaynak.py", "py")],
    "py_cokbicim": [("python py_cokbicim.py", "py")],
    "py_uretim": [("python py_uretim.py", "py")],
    "py_kirilgan": [("python py_kirilgan.py", "py")],
    "dizgi_iz": [
        ("g++ -O1 -g -Wall -Wextra -std=c++17 -fsanitize=address,undefined "
         "dizgi_iz.cpp -o dizgi_iz", "wsl"),
        ("./dizgi_iz", "wsl"),
    ],
    "el_ile": [
        ("g++ -O1 -g -Wall -Wextra -std=c++17 -fsanitize=address,undefined "
         "el_ile.cpp -o el_ile", "wsl"),
        ("./el_ile", "wsl"),
    ],
    "py_kopya": [("python py_kopya.py", "py")],
    "py_hash": [("python py_hash.py", "py")],
    "py_ad": [("python py_ad.py", "py")],
}


def calistir(cmd, ortam):
    if ortam == "wsl":
        tam = ["wsl", "bash", "-c", "cd %s && %s" % (WSL_DIR, cmd)]
    else:
        tam = ["cmd", "/c", "set PYTHONIOENCODING=utf-8 && cd /d %s && %s" % (KLASOR, cmd)]
    sonuc = subprocess.run(tam, capture_output=True, timeout=110)
    cikti = (sonuc.stdout + sonuc.stderr).decode("utf-8", "replace")
    return cikti.replace("\r\n", "\n").replace("\r", "\n")


def main():
    os.makedirs(CIKTI, exist_ok=True)
    secilen = sys.argv[1:] or list(BLOKLAR)
    for ad in secilen:
        parcalar = []
        for cmd, ortam in BLOKLAR[ad]:
            cikti = calistir(cmd, ortam)
            parcalar.append("$ " + cmd + "\n" + cikti.rstrip("\n") + "\n"
                            if cikti.strip() else "$ " + cmd + "\n")
        metin = "".join(parcalar)
        with open(os.path.join(CIKTI, ad + ".txt"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write(metin)
        print("== %s (%d satir)" % (ad, metin.count("\n")))


if __name__ == "__main__":
    main()
