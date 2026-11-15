# -*- coding: utf-8 -*-
import io, re, sys
T = r"C:/Users/merty/AppData/Local/Temp/b60/"
K = "D:/Mevcut Projeler/Kitap/"
parts = ["md/p1.md", "md/p2.md", "md/p3.md", "md/p4.md", "md/p5.md"]
src = "".join(io.open(T + p, encoding="utf-8").read().rstrip("\n") + "\n\n" for p in parts)
def lines(path):
    return io.open(path, encoding="utf-8").read().split("\n")
def code(name, a, b):
    L = lines((T if name == "sifirdan" else T) + ("b60_deney.py" if name == "deney" else "b60_sifirdan.py"))
    body = L[a-1:b]
    assert len(body) <= 40, (name, a, b, len(body))
    return "```python\n" + "\n".join(body).rstrip() + "\n```"
def term(a, b, cmd=None):
    L = lines(T + "b60_final.out")
    body = L[a-1:b]
    if cmd:
        body = ["$ " + cmd] + body
    assert len(body) <= 40
    return "```term\n" + "\n".join(body) + "\n```"
def rep(m):
    t = m.group(1).split()
    if t[0] == "CODE":
        return code(t[1], int(t[2]), int(t[3]))
    if t[0] == "TERM":
        cmd = " ".join(t[3:]) if len(t) > 3 else None
        return term(int(t[1]), int(t[2]), cmd)
    raise SystemExit("bad marker " + m.group(1))
out = re.sub(r"@@(.+?)@@", rep, src)
# hedef: kod satirlarindan ≤70, terminal ≤74 kontrolu build\check_code_width.py ile
io.open(K + "bolumler/bolum_60.md", "w", encoding="utf-8", newline="\n").write(out)
print("yazildi", out.count("\n"), "satir")
