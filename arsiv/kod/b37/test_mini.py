# -*- coding: utf-8 -*-
"""Rastgele (seed=37) ifadelerle VM ve ağaç yorumcusu karşılaştırması.

Bağımsız referans: her ifade için Python tarafında da bir değerlendirme
üretilir. Bölme/mod için math.trunc (C anlamı) kullanılır; derleyicinin
kendi c_bol fonksiyonu KULLANILMAZ.
"""
import math
import random
import sys
from mini import vm_ile_calistir, agacla_calistir
from mini_on import HataDerleme
from derle import CalismaHatasi


def tr_bol(a, b):
    return math.trunc(a / b)


def tr_mod(a, b):
    return a - b * tr_bol(a, b)


def uret(rng, d):
    """(mini_kaynak, python_ifadesi) ciftini üret."""
    if d == 0 or rng.random() < 0.25:
        if rng.random() < 0.5:
            return "a", "a"
        if rng.random() < 0.5:
            return "b", "b"
        n = str(rng.randint(0, 20))
        return n, n
    r = rng.random()
    if r < 0.1:
        m, p = uret(rng, d - 1)
        return f"(-{m})", f"(-{p})"
    op = rng.choice(["+", "-", "*", "/", "%"])
    sm, sp = uret(rng, d - 1)
    if op in "/%":
        k = rng.randint(1, 9)
        if rng.random() < 0.5:
            k = -k
        km, kp = str(k), f"({k})"
        if op == "/":
            return f"({sm} / {km})", f"tr_bol({sp}, {kp})"
        return f"({sm} % {km})", f"tr_mod({sp}, {kp})"
    tm, tp = uret(rng, d - 1)
    return f"({sm} {op} {tm})", f"({sp} {op} {tp})"


def uyumlu_testler(n=3000, seed=37):
    rng = random.Random(seed)
    for k in range(n):
        a = rng.randint(-50, 50)
        b = rng.randint(-50, 50)
        m, p = uret(rng, 4)
        kaynak = f"let a = {a};\nlet b = {b};\nprint {m};\n"
        # eval: yalnız bu dosyanın ürettiği metni çalıştırır
        beklenen = eval(p, {"tr_bol": tr_bol, "tr_mod": tr_mod,
                            "a": a, "b": b})
        vm = vm_ile_calistir(kaynak).ciktilar
        ag = agacla_calistir(kaynak)
        if vm != [beklenen] or ag != [beklenen]:
            print("UYUSMAZLIK", k, kaynak, beklenen, vm, ag)
            sys.exit(1)
    return n


HATA_DURUMLARI = [
    ("print 1 + ;", "ifade bekleniyordu"),
    ("print x;", "tanımsız değişken 'x'"),
    ("print 1 + true;", "tür uyuşmazlığı"),
    ("let a = 1; let a = 2;", "zaten var"),
    ("return 3;", "yalnız fn içinde"),
    ("print f(1);", "tanımsız fonksiyon"),
    ("fn f(x) { return x; } print f(1, 2);", "argüman ister"),
    ("if (1) { print 2; }", "tür uyuşmazlığı"),
]


def hata_testleri():
    for kaynak, parca in HATA_DURUMLARI:
        try:
            vm_ile_calistir(kaynak)
        except HataDerleme as e:
            assert parca in str(e), (kaynak, str(e))
        else:
            raise AssertionError("hata bekleniyordu: " + kaynak)
    # Sifira bölme: iki yurutucu de ayni hatayi vermeli
    for kaynak in ["print 5 / (3 - 3);", "print 5 % (3 - 3);"]:
        for f in (vm_ile_calistir, agacla_calistir):
            try:
                f(kaynak)
            except CalismaHatasi as e:
                assert "sıfıra bölme" in str(e)
            else:
                raise AssertionError(kaynak)
    # Kapsam gölgeleme: ic blokta ayni ad serbest
    k = "let x = 1; if (true) { let x = 5; print x; } print x;"
    assert vm_ile_calistir(k).ciktilar == [5, 1]
    assert agacla_calistir(k) == [5, 1]
    # Fonksiyon kapsamı: ust duzey değişkeni goremez
    try:
        vm_ile_calistir("let g = 1; fn h() { return g; } print h();")
    except HataDerleme as e:
        assert "tanımsız değişken 'g'" in str(e)
    else:
        raise AssertionError("kapsam hatasi bekleniyordu")


if __name__ == "__main__":
    n = uyumlu_testler()
    hata_testleri()
    print(f"{n} rastgele ifade: VM = agac = referans  (seed=37)")
    print("hata durumlari: tamam")
