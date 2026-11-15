import re, os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
MD = "D:/Mevcut Projeler/Kitap/bolumler/bolum_11.md"
V = "C:/Users/merty/AppData/Local/Temp/b11/verify"
text = open(MD, encoding="utf-8").read().split("\n")
blocks = []
inb = False
lang = None
buf = []
for line in text:
    s = line.strip()
    if s.startswith("```"):
        if not inb:
            inb = True
            lang = s[3:].strip().lower()
            buf = []
        else:
            inb = False
            blocks.append((lang, "\n".join(buf) + "\n"))
    elif inb:
        buf.append(line)
# group C
groups = []
cur = None
for lang, code in blocks:
    if lang == "c":
        if "#include" in code:
            cur = [code]
            groups.append(cur)
        elif cur is not None:
            cur.append(code)
    elif lang == "python":
        pass
def wslpath(p):
    return "/mnt/c/" + p.split(":/", 1)[1] if p.startswith("C:") else p
for i, g in enumerate(groups, 1):
    src = os.path.join(V, "prog%d.c" % i)
    open(src, "w", encoding="utf-8").write("\n".join(g))
    exe = "prog%d" % i
    r = subprocess.run(["wsl", "bash", "-c",
        "cd %s && gcc -std=c11 -Wall -Wextra -fsanitize=address,undefined -o %s prog%d.c 2>&1 && ./%s" % (wslpath(V), exe, i, exe)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("=== C group %d (rc=%d)" % (i, r.returncode))
    print(r.stdout + r.stderr)
# python blocks
for j, (lang, code) in enumerate(blocks):
    if lang == "python":
        p = os.path.join(V, "py%d.py" % j)
        open(p, "w", encoding="utf-8").write(code)
        r = subprocess.run(["python", p], capture_output=True, text=True, encoding="utf-8", errors="replace")
        print("=== PY block %d (rc=%d)" % (j, r.returncode))
        print(r.stdout + r.stderr)
