# bolme_2b.py -- 2B veride eksene paralel bolme kutulari (CSV)
import csv
from sklearn.datasets import make_moons
from agac import KararAgaci

X, y = make_moons(n_samples=300, noise=0.25, random_state=59)
agac = KararAgaci(max_derinlik=3).fit(X, y)
kutular = []


def gez(d, sinir):
    # Her yaprak icin bolge sinirlarini (x1 ve x2 araligi) topla
    if d.sol is None:
        kutular.append((sinir, d.derinlik, int(d.deger.argmax())))
        return
    x0, x1, y0, y1 = sinir
    if d.ozellik == 0:
        gez(d.sol, (x0, d.esik, y0, y1))
        gez(d.sag, (d.esik, x1, y0, y1))
    else:
        gez(d.sol, (x0, x1, y0, d.esik))
        gez(d.sag, (x0, x1, d.esik, y1))


gez(agac.kok, (-1.5, 2.5, -1.0, 1.5))
print("yaprak (kutu) sayisi:", len(kutular))
with open("D:/Mevcut Projeler/Kitap/engine/veri/"
          "b59_bolme_2b.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["tur", "x1", "x2", "x3", "x4", "etiket", "derinlik"])
    for i in range(len(X)):
        w.writerow(["nokta", "%.5f" % X[i, 0], "%.5f" % X[i, 1],
                    "", "", int(y[i]), ""])
    for (a, b, c, d), dd, lab in kutular:
        w.writerow(["kutu", "%.5f" % a, "%.5f" % b, "%.5f" % c,
                    "%.5f" % d, lab, dd])
