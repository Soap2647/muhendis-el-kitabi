# test_dogruluk.py: eğitim doğruluğu ile ayrı tutulmuş test doğruluğu.
# Model yalnızca 80 eğitim noktasında eğitilir; test için aynı
# dağılımdan, farklı tohumla 1000 yeni nokta üretilir.
import numpy as np

from mlp_skaler import BOYUTLAR, DONEM, ORANI
from ortak import veri_uret, agirlik_uret
from vektor import ileri, egit_vektor, numpy_al


def dogruluk(K, X, Y):
    out = ileri(K, X)[-1].ravel()
    return float(np.mean((out > 0) == (Y.ravel() > 0)))


Xe, Ye = veri_uret(80, tohum=55)          # eğitim (bölümdeki veri)
Xt, Yt = veri_uret(1000, tohum=5555)      # test: hiç görülmedi
Xe, Xt = np.array(Xe), np.array(Xt)
Ye = np.array(Ye).reshape(-1, 1)
Yt = np.array(Yt).reshape(-1, 1)
K, _ = egit_vektor(numpy_al(agirlik_uret(BOYUTLAR)), Xe, Ye,
                   DONEM, ORANI)
print("egitim dogrulugu (80 nokta):  %.3f" % dogruluk(K, Xe, Ye))
print("test dogrulugu   (1000 nokta): %.3f" % dogruluk(K, Xt, Yt))
