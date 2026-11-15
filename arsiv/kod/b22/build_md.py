# -*- coding: utf-8 -*-
"""Bolum 22 parcalarini birlestirir ve Kod Okuma kesitini yerlestirir."""
import os

S = os.path.dirname(os.path.abspath(__file__))
ROOT = "D:/Mevcut Projeler/Kitap"
SRC = os.path.join(S, "..", "src", "logging_init.py")

parts = []
for i in range(1, 7):
    with open(os.path.join(S, "p%d.md" % i), encoding="utf-8") as f:
        parts.append(f.read())
md = "".join(parts)

with open(SRC, encoding="utf-8") as f:
    lines = f.read().split("\n")
kesit = lines[1745:1774]                      # 1746..1774 (1-tabanli)
assert kesit[0].startswith("    def callHandlers"), kesit[0]
assert kesit[-1].strip() == "self.manager.emittedNoHandlerWarning = True"
cikti = []
for ln in kesit:
    if ln.startswith("    "):
        ln = ln[4:]
    if ln.lstrip().startswith("elif raiseExceptions and not"):
        ind = ln[: len(ln) - len(ln.lstrip())]
        cikti.append(ind + "elif raiseExceptions and \\")
        cikti.append(ind + "        not self.manager.emittedNoHandlerWarning:")
        continue
    cikti.append(ln.rstrip())
kod = "\n".join(cikti)
assert "@@CALLHANDLERS@@" in md
md = md.replace("@@CALLHANDLERS@@", kod)
md = md.replace("\r\n", "\n")

out = os.path.join(ROOT, "bolumler", "bolum_22.md")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(md)
print("yazildi:", out, "satir:", md.count("\n"))
