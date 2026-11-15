# -*- coding: utf-8 -*-
"""Ortam kaydi: tekrarlanabilirlik icin surumleri dondur."""
import hashlib
import platform
import sys
from importlib import metadata

PAKETLER = ["numpy", "pandas", "scikit-learn", "scipy", "pytest"]


def ortam_satirlari():
    satirlar = ["python==" + platform.python_version()]
    for paket in PAKETLER:
        satirlar.append("%s==%s" % (paket, metadata.version(paket)))
    return satirlar


if __name__ == "__main__":
    metin = "\n".join(ortam_satirlari()) + "\n"
    with open("requirements.lock", "w", encoding="utf-8") as f:
        f.write(metin)
    print(metin, end="")
    ozet = hashlib.sha256(metin.encode()).hexdigest()
    print("ortam parmak izi:", ozet[:16])
    print("platform:", platform.system(), "|", sys.platform)
