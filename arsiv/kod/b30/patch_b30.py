# -*- coding: utf-8 -*-
import os

B = "C:/Users/merty/AppData/Local/Temp/b30"


def degistir(dosya, pairs):
    yol = os.path.join(B, dosya)
    s = open(yol, encoding="utf-8").read()
    for a, b in pairs:
        if s.count(a) != 1:
            print("UYARI", dosya, s.count(a), a[:50])
        s = s.replace(a, b)
    open(yol, "w", encoding="utf-8").write(s)


degistir("b30_7_dhcp_sema.py", [
    ('"""b30_7_dhcp_sema.py: DHCP OFFER paketini cevrimdisi kurar/ayristirir.',
     '"""b30_7_dhcp_sema.py: DHCP OFFER paketini cevrimdisi kurar, okur.'),
    ('    print("Ilk 32 bayt:", p[:32].hex(" "))',
     '    print("Ilk 32 bayt:")\n'
     '    for i in range(0, 32, 16):\n'
     '        print("  %02x  %s" % (i, p[i:i + 16].hex(" ")))'),
])

degistir("b30_2_http_ham.py", [
    ('print("Gonderilen (%d bayt):" % len(istek))\nprint(repr(istek))',
     'print("Gonderilen (%d bayt):" % len(istek))\n'
     'for satir in istek.split(b"\\r\\n")[:-2]:\n'
     '    print(satir.decode("ascii") + "\\\\r\\\\n")'),
    ('print(cozulmus[:120].decode("utf-8", "replace"))',
     'print(cozulmus[:60].decode("utf-8", "replace"))'),
    ('print("Ilk 120 karakter:")', 'print("Ilk 60 karakter:")'),
])
print("patch tamam")
