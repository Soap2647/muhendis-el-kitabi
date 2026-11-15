# c_uret.py -- egitilmis KararAgaci'ni C if-else koduna cevirir
import numpy as np


def c_kodu_uret(kok, ad="agac_tahmin", ozellik_say=3):
    satirlar = []
    satirlar.append("/* otomatik uretildi: c_uret.py */")
    satirlar.append("#include <stdint.h>")
    satirlar.append("")
    satirlar.append("uint8_t %s(const float x[%d]) {"
                    % (ad, ozellik_say))

    def yaz(d, girinti):
        bosluk = "    " * girinti
        if d.sol is None:
            sinif_no = int(np.argmax(d.deger))
            satirlar.append(bosluk + "return %d;" % sinif_no)
            return
        kosul = "if (x[%d] <= %.9gf) {" % (d.ozellik, float(d.esik))
        satirlar.append(bosluk + kosul)
        yaz(d.sol, girinti + 1)
        satirlar.append(bosluk + "} else {")
        yaz(d.sag, girinti + 1)
        satirlar.append(bosluk + "}")

    yaz(kok, 1)
    satirlar.append("}")
    return "\n".join(satirlar) + "\n"


def esigi_float32_yap(kok):
    # C'de float karsilastirmasi icin esikleri float32 yap
    d = [kok]
    while d:
        n = d.pop()
        if n.sol is not None:
            n.esik = float(np.float32(n.esik))
            d.extend([n.sol, n.sag])


def ayni_yapraklari_birlestir(d):
    # Ayni sinifa giden iki yaprak varsa dugumu yaprak yap
    if d.sol is None:
        return d
    d.sol = ayni_yapraklari_birlestir(d.sol)
    d.sag = ayni_yapraklari_birlestir(d.sag)
    if (d.sol.sol is None and d.sag.sol is None
            and int(np.argmax(d.sol.deger))
            == int(np.argmax(d.sag.deger))):
        d.sol = None
        d.sag = None
    return d
