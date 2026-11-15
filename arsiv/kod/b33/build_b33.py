# -*- coding: utf-8 -*-
import glob, os, re, subprocess, sys
D = "C:/Users/merty/AppData/Local/Temp/b33"
os.chdir(D)
env = dict(os.environ, PYTHONIOENCODING="utf-8")
parts = sorted(glob.glob(os.path.join(D, "parts", "p*.md")),
               key=lambda p: int(re.findall(r"p(\d+)\.md", p)[0]))
text = "\n\n".join(open(p, encoding="utf-8").read().strip()
                   for p in parts) + "\n"
cache = {}


def cikti(dosya):
    if dosya not in cache:
        r = subprocess.run([sys.executable, dosya], capture_output=True, encoding="utf-8",
                           text=True, env=env, cwd=D)
        if r.returncode != 0:
            raise SystemExit("HATA %s\n%s" % (dosya, r.stderr))
        cache[dosya] = r.stdout.rstrip("\n")
    return cache[dosya]


def kod(m):
    dosya, a, b = m.group(1), int(m.group(2)), int(m.group(3))
    satirlar = open(os.path.join(D, dosya), encoding="utf-8").read().split("\n")
    parca = satirlar[a - 1:b]
    if parca and parca[0].startswith("# -*- coding"):
        parca = parca[1:]
    while parca and parca[-1] == "":
        parca = parca[:-1]
    return "```python\n" + "\n".join(parca) + "\n```"


def term(m):
    dosya = m.group(1)
    cik = cikti(dosya)
    return ("```term\n$ python %s\n" % dosya) + cik + "\n```"


text = re.sub(r"\[\[KOD:([^:\]]+):(\d+):(\d+)\]\]", kod, text)
text = re.sub(r"\[\[CIKTI:([^\]]+)\]\]", term, text)
out = os.path.join("D:/Mevcut Projeler/Kitap/bolumler/bolum_33.md")
open(out, "w", encoding="utf-8").write(text)
print("yazildi:", out, "satir:", text.count("\n"))
