"""Çalıştırma uzunluğu kodlaması (run-length encoding)."""


def kodla(s):
    cikti = []
    for ch in s:
        if cikti and cikti[-1][0] == ch:
            cikti[-1] = (ch, cikti[-1][1] + 1)
        else:
            cikti.append((ch, 1))
    return cikti


def coz(parcalar):
    return "".join(ch * k for ch, k in parcalar)
