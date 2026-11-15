# assemble.py: md parcalarini birlestirir, @@KOD ve @@CIKTI yonergelerini doldurur
import re, os, sys
T = "C:/Users/merty/AppData/Local/Temp/b19"
OUT = os.path.join(T, "out")
parts = ["p1.md", "p2.md", "p3.md", "p4.md"]
text = "\n\n".join(open(os.path.join(T, "md", p), encoding="utf-8").read().strip() + "\n" for p in parts)

def kod(m):
    fn, rng = m.group(1), m.group(2)
    lines = open(os.path.join(T, fn), encoding="utf-8").read().split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    if rng:
        a, b = map(int, rng.split("-"))
        lines = lines[a-1:b]
    lang = "c" if fn.endswith(".c") else "python"
    return "```%s\n%s\n```\n" % (lang, "\n".join(l.rstrip() for l in lines))

def cikti(m):
    cmd, fn = m.group(1), m.group(2)
    body = open(os.path.join(OUT, fn), encoding="utf-8").read().split("\n")
    body = [l.rstrip() for l in body if l.strip() and not l.startswith("ASAN_EXIT") and not l.startswith("OLCUM")]
    return "```term\n$ %s\n%s\n```\n" % (cmd, "\n".join(body))

text = re.sub(r"@@KOD:([^:@]+)(?::(\d+-\d+))?@@\n?", lambda m: kod(m) , text)
text = re.sub(r"@@CIKTI:([^:@]+):([^@]+)@@\n?", cikti, text)
assert "@@" not in text, "kalan yonerge var"
dst = "D:/Mevcut Projeler/Kitap/bolumler/bolum_19.md"
open(dst, "w", encoding="utf-8").write(text)
print("yazildi", dst, "satir:", text.count("\n"))
