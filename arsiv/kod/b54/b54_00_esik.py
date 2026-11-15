import numpy as np

rng = np.random.default_rng(54)
# Sensor sicakligi (C) ve gercek alarm durumu (1: alarm gerekli)
sicaklik = rng.uniform(60, 100, 200)
gercek = (sicaklik > 85).astype(int)
gurultu = rng.random(200) < 0.08          # %8 etiket hatasi
etiket = np.where(gurultu, 1 - gercek, gercek)

def dogruluk(esik):
    tahmin = (sicaklik > esik).astype(int)
    return np.mean(tahmin == etiket)

# Elle yazilmis kural (bir muhendisin tahmini): 90.
# Ogrenme: esigi veriden ara.
adaylar = np.arange(60, 100, 0.5)
skor = [dogruluk(t) for t in adaylar]
en_iyi = adaylar[int(np.argmax(skor))]
print("elle kural (90) dogrulugu: %.3f" % dogruluk(90))
print("ogrenilen esik:           %.1f" % en_iyi)
print("ogrenilen esik dogruluk: %.3f" % max(skor))
