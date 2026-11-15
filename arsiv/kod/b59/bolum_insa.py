# bolum_insa.py -- sablon_b59.md icindeki @@KOD ve @@CIKTI isaretlerini
# gercek dosya icerigi ve gercek komut ciktisiyla degistirir.
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = r"C:\Users\merty\AppData\Local\Temp\b59"
os.chdir(BASE)
env = dict(os.environ, PYTHONIOENCODING="utf-8")
src = open("sablon_b59.md", encoding="utf-8").read().split("\n")
pat = re.compile(r"^@@(KOD|CIKTI)\|(.*)@@$")
out = []
for line in src:
    m = pat.match(line)
    if not m:
        out.append(line)
        continue
    tur, icerik = m.group(1), m.group(2)
    if tur == "KOD":
        parca = icerik.split("|")
        if len(parca) == 2:
            dosya, dil = parca
            a = b = None
        else:
            dosya, a, b, dil = parca
        satirlar = open(dosya, encoding="utf-8").read().split("\n")
        if a is not None:
            satirlar = satirlar[int(a) - 1:int(b)]
        while satirlar and satirlar[-1].strip() == "":
            satirlar.pop()
        out.append("```" + dil)
        out += [s.rstrip() for s in satirlar]
        out.append("```")
        print("KOD:", dosya, a, b, len(satirlar))
    else:
        komut = icerik
        r = subprocess.run(komut, shell=True, cwd=BASE, env=env,
                           capture_output=True, timeout=900)
        metin = r.stdout.decode("utf-8", "replace")
        if r.returncode != 0:
            metin += r.stderr.decode("utf-8", "replace")
            print("HATA:", komut, r.returncode)
        metin = metin.replace("\r", "").rstrip("\n")
        out.append("```term")
        out.append("$ " + komut)
        out += [s.rstrip() for s in metin.split("\n")]
        out.append("```")
        print("CIKTI:", komut, "satir:", metin.count("\n") + 1)
open("bolum_59_uretilmis.md", "w", encoding="utf-8", newline="\n").write(
    "\n".join(out))
print("yazildi")
