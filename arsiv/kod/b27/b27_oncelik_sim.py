# -*- coding: utf-8 -*-
"""b27_oncelik_sim.py - oncelik terslemesi ve kalitim simulasyonu.

Tek CPU, sabit oncelikli, onleyici zamanlayici; tek muteks.
Gercek zamanli zamanlama (SCHED_FIFO) bu ortamda izinli degil;
senaryo bu yuzden deterministik bir simulasyonla gosterilir.
Zaman birimi = 1 tick.

Calistirma: python -I b27_oncelik_sim.py
"""


class Gorev:
    def __init__(self, ad, oncelik, varis, islem):
        self.ad = ad
        self.taban = oncelik        # sabit (baz) oncelik
        self.varis = varis          # ne zaman hazir olur
        # islem: ("cpu", n) | ("kilit",) | ("birak",)
        self.islem = list(islem)
        self.kilit_bekliyor = False
        self.bitti = False


def etkin_oncelik(g, muteks, kalitim):
    p = g.taban
    if kalitim and muteks["sahip"] is g and muteks["bekleyen"]:
        p = max([p] + [w.taban for w in muteks["bekleyen"]])
    return p


def simul(kalitim):
    muteks = {"sahip": None, "bekleyen": []}
    L = Gorev("L", 1, 0, [("kilit",), ("cpu", 3), ("birak",)])
    H = Gorev("H", 3, 1, [("kilit",), ("cpu", 1), ("birak",)])
    M = Gorev("M", 2, 2, [("cpu", 4)])
    gorevler = [L, H, M]
    satirlar = []
    h_bekleme = 0
    t = 0
    while not all(g.bitti for g in gorevler):
        notlar = ""
        secilen = None
        # bloke olan gorev ayni tick'te yerini birakir
        while secilen is None:
            hazir = [g for g in gorevler
                     if g.varis <= t and not g.bitti
                     and not g.kilit_bekliyor]
            if not hazir:
                break
            g = max(hazir,
                    key=lambda x: etkin_oncelik(x, muteks, kalitim))
            while g.islem and g.islem[0][0] != "cpu":
                op = g.islem.pop(0)
                if op[0] == "kilit":
                    if muteks["sahip"] is None:
                        muteks["sahip"] = g
                        notlar += " [%s aldi]" % g.ad
                    else:
                        g.kilit_bekliyor = True
                        muteks["bekleyen"].append(g)
                        notlar += " [%s bekliyor]" % g.ad
                        g.islem.insert(0, op)
                        break
                else:  # birak
                    muteks["sahip"] = None
                    notlar += " [%s birakti]" % g.ad
                    if muteks["bekleyen"]:
                        en = max(muteks["bekleyen"],
                                 key=lambda x: x.taban)
                        muteks["bekleyen"].remove(en)
                        en.kilit_bekliyor = False
                        en.islem.pop(0)
                        muteks["sahip"] = en
                        notlar += " -> %s'e gecti" % en.ad
            if g.kilit_bekliyor:
                continue            # bu gorev bekliyor; yeniden sec
            secilen = g
        if secilen is None:
            satirlar.append("t=%d  CPU bos%s" % (t, notlar))
            t += 1
            continue
        g = secilen
        if g.islem and g.islem[0][0] == "cpu":
            n = g.islem[0][1]
            if n == 1:
                g.islem.pop(0)
            else:
                g.islem[0] = ("cpu", n - 1)
        if not g.islem:
            g.bitti = True
            notlar += " [%s bitti]" % g.ad
        if H.kilit_bekliyor:
            h_bekleme += 1
        sahip = muteks["sahip"].ad if muteks["sahip"] else "-"
        bekleyen = ",".join(w.ad for w in muteks["bekleyen"]) or "-"
        satirlar.append("t=%d  CPU: %s  sahip: %s  bekleyen: %s%s"
                        % (t, g.ad, sahip, bekleyen, notlar))
        t += 1
    return satirlar, h_bekleme, t


def yazdir(baslik, satirlar, h_bekleme, bitis):
    print("== " + baslik)
    for s in satirlar:
        print(s)
    print("H'nin kilit bekleme suresi: %d tick" % h_bekleme)
    print("tum gorevler %d. tick'te bitti" % bitis)
    print()


if __name__ == "__main__":
    s1, b1, e1 = simul(kalitim=False)
    yazdir("Oncelik kalitimi YOK", s1, b1, e1)
    s2, b2, e2 = simul(kalitim=True)
    yazdir("Oncelik kalitimi VAR (PTHREAD_PRIO_INHERIT benzeri)",
           s2, b2, e2)
