# -*- coding: utf-8 -*-
"""commit-msg denetimi: konvansiyonel commit biçimi."""
import re
import sys

DESEN = re.compile(
    r"^(feat|fix|docs|refactor|test|chore)(\([a-z0-9-]+\))?: .+")


def main(yol):
    with open(yol, encoding="utf-8") as f:
        ilk = f.readline().rstrip("\n")
    if not DESEN.match(ilk):
        print("commit-msg: biçim hatalı -> '%s'" % ilk)
        print("beklenen: tür(kapsam): kısa açıklama")
        return 1
    if len(ilk) > 72:
        print("commit-msg: ilk satır 72 karakteri aşıyor")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
