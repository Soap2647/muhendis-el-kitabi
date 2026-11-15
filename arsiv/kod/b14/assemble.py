import os, re, subprocess

TMP = r"C:\Users\merty\AppData\Local\Temp\b14"
SRC = os.path.join(TMP, "src")
OUT = r"D:\Mevcut Projeler\Kitap\bolumler\bolum_14.md"
PARTS = ["p1.md", "p2.md", "p3.md"]
WSL_SRC = "/mnt/c/Users/merty/AppData/Local/Temp/b14/src"

HEADER = ("%% kisim_no: IV\n%% kisim_ad: Algoritmalar\n"
          "%% bolum_no: 14\n%% baslik: Arama\n\n")


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return [l.rstrip("\r\n") for l in f]


def slice_lines(lines, rng):
    if not rng:
        return lines
    if rng.endswith("-"):
        a = int(rng[:-1])
        return lines[a - 1:]
    a, b = rng.split("-")
    return lines[int(a) - 1:int(b)]


def fence(lang, body):
    return "```%s\n%s\n```" % (lang, "\n".join(body))


def run_c(fname, args):
    stem = os.path.splitext(fname)[0]
    cmd = ("cd %s && gcc -O2 -Wall -Wextra -std=c11 %s -o %s && ./%s %s"
           % (WSL_SRC, fname, stem, stem, args)).strip()
    p = subprocess.run(["wsl", "-e", "bash", "-c", cmd],
                       capture_output=True, text=True, encoding="utf-8")
    out = (p.stdout + p.stderr).rstrip("\n")
    head = ("$ gcc -O2 -Wall -Wextra -std=c11 %s -o %s\n$ ./%s %s"
            % (fname, stem, stem, args)).rstrip()
    return head + "\n" + out


def run_py(fname):
    p = subprocess.run(["python", fname], cwd=SRC,
                       capture_output=True, text=True, encoding="utf-8")
    out = (p.stdout + p.stderr).rstrip("\n")
    return "$ python %s\n%s" % (fname, out)


def sub(m):
    kind, arg = m.group(1), m.group(2)
    if kind in ("C", "PY", "GO"):
        if ":" in arg:
            fname, rng = arg.split(":", 1)
        else:
            fname, rng = arg, ""
        lines = read_lines(os.path.join(SRC, fname))
        if kind == "GO":
            lines = read_lines(os.path.join(SRC, fname))
        body = slice_lines(lines, rng)
        lang = {"C": "c", "PY": "python", "GO": "go"}[kind]
        return fence(lang, body)
    if kind == "TERMC":
        if "|" in arg:
            fname, args = arg.split("|", 1)
        else:
            fname, args = arg, ""
        return "```term\n%s\n```" % run_c(fname, args)
    if kind == "TERMPY":
        return "```term\n%s\n```" % run_py(arg)
    if kind == "TERMRAW":
        with open(os.path.join(TMP, "raw", arg + ".txt"), encoding="utf-8") as f:
            return "```term\n%s\n```" % f.read().rstrip("\n")
    raise ValueError(kind)


def main():
    text = "\n\n".join(open(os.path.join(TMP, "parts", p), encoding="utf-8").read().rstrip("\n")
                       for p in PARTS) + "\n"
    text = re.sub(r"^@@(C|PY|GO|TERMC|TERMPY|TERMRAW):([^@]+)@@$", sub, text,
                  flags=re.M)
    left = re.findall(r"@@[^@]*@@", text)
    assert not left, left
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(HEADER + text)
    print("wrote", OUT, len(text.splitlines()), "lines")


if __name__ == "__main__":
    main()
