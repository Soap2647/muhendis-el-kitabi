# assemble.py - Bolum 17 kaynak parcalarini birlestirir.
#  [[KOD:dosya]]        dosyanin tamami (```python / ```c blogu)
#  [[KOD:dosya:a:b]]    dosyanin a..b satirlari (1-tabanli, dahil)
#  [[TERM:anahtar]]     komutlari calistirir; ```term blogu olarak gomer
import os
import re
import subprocess
import sys

B = r"C:\Users\merty\AppData\Local\Temp\b17"
CODE = os.path.join(B, "code")
SRC = os.path.join(B, "src")
OUT = r"D:\Mevcut Projeler\Kitap\bolumler\bolum_17.md"
PARTS = ["p1.md", "p2.md", "p3.md"]

ENV = dict(os.environ, PYTHONIOENCODING="utf-8", MSYS_NO_PATHCONV="1")


def wsl(cmd):
    """WSL'de bash komutu; Windows yolu /mnt/c ... olarak gecilir."""
    yol = "/mnt/c/Users/merty/AppData/Local/Temp/b17/code"
    r = subprocess.run(["wsl", "bash", "-lc", "cd %s && %s" % (yol, cmd)],
                       capture_output=True, env=ENV)
    out = r.stdout.decode("utf-8", "replace")
    if r.returncode != 0:
        raise SystemExit("WSL HATA: %s\n%s" % (cmd, r.stderr.decode()))
    return out


def py(dosya):
    r = subprocess.run([sys.executable, dosya], cwd=CODE,
                       capture_output=True, env=ENV)
    out = r.stdout.decode("utf-8", "replace")
    if r.returncode != 0:
        raise SystemExit("PY HATA %s:\n%s" % (dosya, r.stderr.decode()))
    return out


import textwrap


def _sar(s):
    if len(s) <= 74:
        return [s]
    return textwrap.wrap(s, 74, subsequent_indent="    ",
                         break_long_words=False, break_on_hyphens=False)


def term_blok(komutlar_ve_cikti):
    satirlar = []
    for kom, cikti in komutlar_ve_cikti:
        satirlar.extend(_sar("$ " + kom))
        if cikti:
            for s in cikti.rstrip("\n").split("\n"):
                satirlar.extend(_sar(s))
    return "```term\n" + "\n".join(satirlar) + "\n```"


TERMS = {
    "dfs": lambda: term_blok([
        ("gcc -std=c11 -Wall -Wextra -O2 dfs.c -o dfs", None),
        ("./dfs", wsl("./dfs"))]),
    "dfs_asan": lambda: term_blok([
        ("gcc -fsanitize=address,undefined -std=c11 -g dfs.c -o dfs_asan",
         None),
        ("./dfs_asan > /dev/null; echo $?",
         wsl("./dfs_asan > /dev/null; echo $?"))]),
    "dfs_dogrula": lambda: term_blok([
        ("./dfs | tail -3", wsl("./dfs | tail -3"))]),
}
for _f in ["dijkstra", "bellman", "floyd", "mst", "tarjan", "topo",
           "bipartite", "astar", "cross_test", "ornek1_ders",
           "ornek2_gecikme", "ornek3_sehir", "ornek4_arbitraj",
           "graphlib_demo"]:
    TERMS[_f] = (lambda f=_f: term_blok([("python %s.py" % f,
                                          py(f + ".py"))]))
TERMS["graphlib"] = TERMS["graphlib_demo"]
TERMS["cross"] = TERMS["cross_test"]


def kod(dosya, a=None, b=None):
    with open(os.path.join(CODE, dosya), encoding="utf-8") as f:
        satirlar = f.read().rstrip("\n").split("\n")
    if a is not None:
        satirlar = satirlar[int(a) - 1:int(b)]
    dil = "c" if dosya.endswith(".c") else "python"
    return "```%s\n%s\n```" % (dil, "\n".join(satirlar))


def expand(metin):
    def r1(m):
        parca = m.group(1).split(":")
        if parca[0] == "KOD":
            return kod(*parca[1:])
        if parca[0] == "TERM":
            return TERMS[parca[1]]()
        raise SystemExit("bilinmeyen yer tutucu " + m.group(0))
    return re.sub(r"\[\[([^\]]+)\]\]", r1, metin)


def main():
    birlesik = []
    for p in PARTS:
        with open(os.path.join(SRC, p), encoding="utf-8") as f:
            birlesik.append(f.read())
    metin = expand("\n\n".join(birlesik))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(metin)
    # genislik denetimi
    sorunlar = 0
    icinde, sinir = False, 70
    for no, s in enumerate(metin.split("\n"), 1):
        if s.startswith("```"):
            if not icinde:
                icinde = True
                sinir = 74 if s[3:].strip() == "term" else 70
            else:
                icinde = False
            continue
        if icinde and len(s) > sinir:
            sorunlar += 1
            print("UZUN SATIR", no, len(s), s[:50])
    print("yazildi:", OUT, "uzun satir:", sorunlar,
          "bayt:", len(metin.encode("utf-8")))


if __name__ == "__main__":
    main()
