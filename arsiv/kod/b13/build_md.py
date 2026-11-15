# -*- coding: utf-8 -*-
"""Bolum 13 taslagini (p1..p4) kod/cikti yer tutucularini doldurarak derler."""
import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
T = "C:/Users/merty/AppData/Local/Temp/b13"
OUT = "D:/Mevcut Projeler/Kitap/bolumler/bolum_13.md"

def satirlar(path):
    with open(path, encoding="utf-8") as f:
        return f.read().split("\n")

def kirp(xs):
    while xs and xs[0].strip() == "":
        xs = xs[1:]
    while xs and xs[-1].strip() == "":
        xs = xs[:-1]
    return xs

C_SRC = satirlar(os.path.join(T, "siralama.c"))
L_SRC = satirlar("C:/Users/merty/AppData/Local/Temp/b13/listobject.c")
kapsam = set()
for a, b in [(1,34),(36,81),(83,113),(115,137),(139,176),(178,201),
             (203,223),(225,267),(269,335),(337,378),(380,402),(404,435)]:
    kapsam.update(range(a, b + 1))
bos = [i for i in range(1, len(C_SRC) + 1) if i not in kapsam]
assert all(C_SRC[i-1].strip() == "" for i in bos), "kapsam disi dolu satir var"

def ornek_kod(xs):
    return "```c\n" + "\n".join(kirp(xs)) + "\n```"

def repl(m):
    tag, args = m.group(1), m.group(2).strip()
    if tag == "C":
        a, b = map(int, args.split())
        return ornek_kod(C_SRC[a-1:b])
    if tag == "L":
        a, b = map(int, args.split())
        kesit = []
        for satir in L_SRC[a-1:b]:
            if satir == "count_run(MergeState *ms, PyObject **lo, PyObject **hi, int *descending)":
                kesit += ["count_run(MergeState *ms, PyObject **lo, PyObject **hi,",
                          "          int *descending)"]
            elif satir.strip().startswith("Py_ssize_t r = 0;"):
                kesit += ["    Py_ssize_t r = 0;           /* becomes 1 if any 1 bits are shifted",
                          "                                   off */"]
            else:
                kesit.append(satir)
        return ornek_kod(kesit)
    if tag == "PY":
        body = "\n".join(kirp(satirlar(os.path.join(T, args))))
        return "```python\n" + body + "\n```"
    if tag == "T":
        cmd, fn = args.split("|", 1)
        cikti = ""
        if fn != "/dev/null":
            cikti = "\n".join(kirp(satirlar(os.path.join(T, fn))))
        govde = "$ " + cmd + ("\n" + cikti if cikti else "")
        return "```term\n" + govde + "\n```"
    raise ValueError(tag)

parcalar = []
for p in ["p1.md", "p2.md", "p3.md", "p4.md"]:
    parcalar.append(open(os.path.join(T, p), encoding="utf-8").read().rstrip("\n"))
metin = "\n\n".join(parcalar) + "\n"
metin = re.sub(r"^@@(C|L|PY|T) (.*?)@@$", repl, metin, flags=re.M)
kalan = re.findall(r"@@.*?@@", metin)
assert not kalan, kalan[:5]
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(metin)
print("yazildi:", OUT, "satir:", metin.count("\n"))
