%% kisim_no: XIV
%% kisim_ad: Makine Öğrenmesi
%% bolum_no: 57
%% baslik: Değerlendirme & Deney Tasarımı

## Giriş: Doğru ölçüt, doğru kararın yarısıdır

Bir İHA'nın kamerasındaki bir kareye bakıp hedefin dost mu düşman mı olduğunu söyleyen bir model düşün. Ya da bir elektrikli aracın batarya sensör verisinden arızayı önceden haber veren bir model. Modelin çıktısı her iki durumda da bir sayıdır. Ama o sayının karar sistemine ne kadar değer kattığı, büyük ölçüde hangi ölçütle ölçüldüğüne bağlıdır. Yanlış ölçüt seçen bir ekip, kendi açısından başarılı görünen ama sahada işe yaramayan bir model üretir.

Bölüm 54'te model çerçevesini, veri bölmesini ve baseline kavramını gördün. Orada bir yanılgıyı da gösterdik: %92 doğruluk sevindirici görünse de sınıflar dengesizse hiçbir şey öğrenmemiş bir modelin doğruluğu bu kadar yüksek çıkabilir. Bu bölüm o tuzağın üzerine kurulu: karışıklık matrisi, kesinlik, duyarlılık, MCC, ROC ve PR eğrileri, eşik seçimi, olasılıkların kalibrasyonu, regresyon ölçütleri ve çapraz doğrulamanın derinliği. En sonunda da "bu model gerçekten daha iyi mi?" sorusuna dürüstçe nasıl cevap verileceğini, yani karşılaştırma testlerini ve A/B deneylerini göreceğiz.

Mülakatlarda ve savunma sanayiinde ölçüt bir istatistik değil, bir sözleşmedir. "Yanlış alarm oranı yüzde birin altındayken tespit oranı ne kadar?" cümlesi bir ekipten bir başkasına yazılı olarak verilen bir garantidir. Bu garantinin nasıl ölçüldüğünü bilmeden verilen sözün bir anlamı yoktur. Bölüm 78'de güvenilirlik ve belirsizlik tarafına gireceğiz; burada o sözün ölçümünü kuruyoruz.

Bu bölümde iki ilke sürekli karşına çıkacak. Birincisi: her metriği önce sıfırdan yazacağız, sonra sklearn ile birebir eşleştirip doğrulayacağız. İkincisi: her ölçüm bir belirsizlik taşır; tek bir sayı yerine güven aralığı ve dilim bazlı sonuç raporlayacağız. Bölümdeki tüm rastgele deneyler sabit tohumla çalışır. Kullanılan sürümler: Python 3.12.10, numpy 2.3.5, scikit-learn 1.8.0, scipy 1.17.1 ve matplotlib 3.10.9.

::: not
Bu bölümde gördüğün her sayı, metinde adı verilen bir programın çıktısıdır. Önce programı çalıştır, sonra metni oku. Kendi makinende farklı bir sayı görürsen önce sürüm numaralarını karşılaştır, sonra kodu oku. Ölçmeden inanmamak bu bölümün ilk dersidir.
:::

## 57.1 Hata maliyetleri: "doğru" ölçüt neden bir iş kararıdır

Bir sınıflandırıcının iki tür hatası vardır. Pozitif sınıfı (aradığımız durumu) kaçırmak **yanlış negatiftir** (FN). Negatif bir örneği pozitif sanmak **yanlış pozitiftir** (FP). Bu iki hatanın bedeli çoğu zaman eşit değildir ve bu eşitsizlik, hangi ölçütün "doğru" olduğunu belirler.

İHA dost/düşman tanımada pozitif sınıfı "düşman hedef" olarak alalım. Bir düşmanı kaçırmak (FN), görevin amacına ve belki de birliğin güvenliğine doğrudan zarar verebilir. Bir dostu düşman sanmak (FP) ise gereksiz bir müdahaleye, kaynak israfına ya da operatör güveninin kaybına yol açar. İkisi aynı ağırlıkta değildir ve bunu sayıya dökmek bizim işimizdir.

Elektrikli araçta arıza alarmına bakalım. Pozitif sınıf "yakında arıza olacak" durumudur. Bir arızayı kaçırmak (FN) batarya kaynaklı bir olayın önüne geçememek demektir. Gereksiz alarm (FP) ise aracın servise gitmesine, sürücünün sistemi kullanmayı bırakmasına yol açar. Bu alanda doğru ölçüt, hangi hatanın daha pahalı olduğuna göre değişir. Mert'in EV Dashboard projesindeki sensör akışında bu iki hata sayısal olarak nasıl tartılır? Bu tartıyı 57.6'da sayıya dökeceğiz.

| Alan | Pozitif sınıf | FN (kaçan) bedeli | FP (yanlış alarm) bedeli |
|---|---|---|---|
| İHA dost/düşman | Düşman hedef | Görev ve güvenlik kaybı | Dosta müdahale, güven kaybı |
| EV arıza alarmı | Yakında arıza | Yolda kalma, yangın riski | Gereksiz servis, güven kaybı |
| Meme kanseri taraması | Kötü huylu tümör | Gecikmiş tedavi | Gereksiz biyopsi, kaygı |

Bu tablo bir kuralı gösteriyor: hangi ölçütün kullanılacağı, modelin kendisinden önce iş kararıyla belirlenir. "Doğruluk" çoğu zaman bu kararı göz ardı eden bir ölçüttür, çünkü her hatayı eşit sayar. Bu bölümde FN ve FP'yi ayrı ayrı görmeyi, sonra da onları maliyet oranıyla birleştirmeyi öğreneceksin (57.6).

## 57.2 Karışıklık matrisi ve ikili metrikler

Bir ikili sınıflandırıcının tüm hatalarını ve doğrularını tek bir tabloda toplamak mümkündür. Bu tabloya **karışıklık matrisi** (confusion matrix) denir. Satırlar gerçek sınıfı, sütunlar tahmini gösterir (scikit-learn'ün sırası budur). Dört hücre vardır: TP (doğru pozitif), TN (doğru negatif), FP ve FN.

Dört sayıdan bütün temel ölçütler türetilir. Doğruluk, tüm örnekler içinde doğru bildiklerimizin oranıdır: (TP + TN) / N. Kesinlik (precision), "pozitif dediklerimizin kaçı gerçekten pozitif?" sorusunu yanıtlar: TP / (TP + FP). Duyarlılık (recall, aynı zamanda doğru pozitif oranı, TPR), "gerçek pozitiflerin kaçını yakaladık?" sorusunu yanıtlar: TP / (TP + FN). Özgüllük (TNR) negatiflerin tarafındaki karşılığıdır: TN / (TN + FP). Yanlış pozitif oranı (FPR) ise 1 eksi özgüllüktür.

Kesinlik ve duyarlılık arasında doğal bir gerilim vardır. Eşiği düşürürsen daha çok pozitif yakalarsın (duyarlılık artar) ama yanlış alarmlar da artar (kesinlik düşer). İkisini tek bir sayıda birleştirmek için **F1** kullanılır: F1 = 2PR / (P + R), yani kesinlik ve duyarlılığın harmonik ortalaması. Harmonik ortalama küçük olana yakın durur; bu yüzden birini tamamen sıfırlayan bir model F1 ile de yüksek görünmez. Genel hâlde **Fβ** = (1 + β²)PR / (β²P + R) yazılır. β > 1 duyarlılığa, β < 1 kesinliğe daha çok ağırlık verir. β = 2, kaçan bir tehdidin yanlış alarmdan daha pahalı olduğu durumlarda sık kullanılır.

Bu formülleri ezberlemek yerine nereden geldiklerini bil: her biri dört hücreden birinin bir oranıdır. Aşağıdaki şekil bu ilişkiyi gösteriyor.

![Şekil 57.1: İkili karışıklık matrisi ve türetilen ölçütler. Doğruluk tüm hücreleri, kesinlik ve duyarlılık ise tek bir sütun ya da satırı kullanır.](gorseller/b57_karisiklik.png)

Doğruluğun neden yanıltıcı olabileceğini görmek için basit bir tahminci düşün: her zaman "iyi huylu" diyen bir model. Meme kanseri veri setinin test kümesinde bu tahminci %62,6 doğruluk verir. Model hiçbir şey öğrenmediği hâlde iyi görünür. Ölçütü bu tahminciye karşı sınamak, Bölüm 54'teki baseline fikrinin ölçütlere uygulanmasıdır: model, anlamlı bir şey öğrenip öğrenmediğini kanıtlamak zorundadır.

Aşağıdaki program meme kanseri verisiyle (569 örnek, sklearn'de hedef 0 = kötü huylu) bir lojistik regresyon eğitiyor. Pozitif sınıfı kötü huylu olarak tanımlamak için hedefi 1 - hedef ile çeviriyoruz: tespit etmek istediğimiz şey kötü huylu tümördür. Tüm ölçütleri önce kendi yazdığımız fonksiyonlarla hesaplayıp sklearn ile karşılaştırıyoruz. Önce yardımcı fonksiyonlar ve ortalama hesapları gelir.

```python
# b57_01_metrikler.py
# Karisiklik matrisi ve siniflandirma metrikleri: sifirdan + sklearn
import numpy as np
from sklearn import metrics as M
from sklearn.datasets import load_breast_cancer, load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

def karisiklik(gercek, tahmin, siniflar):
    """K[i, j]: gercek i, tahmin j olan ornek sayisi."""
    idx = {s: i for i, s in enumerate(siniflar)}
    K = np.zeros((len(siniflar), len(siniflar)), dtype=int)
    for g, t in zip(gercek, tahmin):
        K[idx[g], idx[t]] += 1
    return K

def bol(a, b):
    return float(a) / float(b) if b > 0 else 0.0

def f_beta(p, r, beta=1.0):
    b2 = beta * beta
    return bol((1 + b2) * p * r, b2 * p + r)

def sinif_metrikleri(K):
    """Her sinif icin TP, FP, FN, kesinlik, duyarlilik, F1."""
    tp = np.diag(K).astype(float)
    fp = K.sum(axis=0) - tp          # sutun toplami - TP
    fn = K.sum(axis=1) - tp          # satir toplami - TP
    p = np.array([bol(a, b) for a, b in zip(tp, tp + fp)])
    r = np.array([bol(a, b) for a, b in zip(tp, tp + fn)])
    f1 = np.array([f_beta(a, b) for a, b in zip(p, r)])
    return tp, fp, fn, p, r, f1
```

Karışıklık matrisini sayan `karisiklik` fonksiyonu, her örnek için bir sayaç artırır. Bu, `confusion_matrix`'in yaptığının en açık hâlidir. `sinif_metrikleri` her sınıf için TP, FP ve FN değerlerini satır ve sütun toplamlarından çıkarır: FP sütun toplamının TP'nin dışındaki kısmı, FN ise satır toplamının TP'nin dışındaki kısmıdır. Paydası sıfır olan durumlarda (hiç tahmin yoksa) sonuç sıfır sayılır; sklearn'ün varsayılanı da budur.

```python
def ortalamalar(K):
    """Makro, mikro, agirlikli ortalamalar (P, R, F1)."""
    tp, fp, fn, p, r, f1 = sinif_metrikleri(K)
    destek = K.sum(axis=1)
    w = destek / destek.sum()
    mp = bol(tp.sum(), tp.sum() + fp.sum())   # mikro kesinlik
    mr = bol(tp.sum(), tp.sum() + fn.sum())   # mikro duyarlilik
    return {
        "makro_F1": f1.mean(),
        "mikro_F1": f_beta(mp, mr),
        "agirlikli_F1": (w * f1).sum(),
        "makro_kesinlik": p.mean(),
        "mikro_kesinlik": mp,
        "agirlikli_kesinlik": (w * p).sum(),
    }

def kappa(K):
    """Cohen kappa: gozlenen uyum, sansa bagli uyumla duzeltilmis."""
    n = K.sum()
    po = np.trace(K) / n
    pe = (K.sum(axis=0) * K.sum(axis=1)).sum() / float(n) ** 2
    return (po - pe) / (1 - pe)

def mcc_ikili(tp, tn, fp, fn):
    """Matthews korelasyon katsayisi: -1..+1, 0 = rastgele."""
    pay = float(tp) * tn - float(fp) * fn
    payda = np.sqrt(float(tp + fp) * (tp + fn)
                    * (tn + fp) * (tn + fn))
    return pay / payda if payda > 0 else 0.0
```

Makro, mikro ve ağırlıklı ortalamaları ve kappa ile MCC'yi sonraki alt bölümde açıklayacağız. Şimdi ikili sınıflandırmaya dönüyoruz: modeli eğitip test kümesinde tahmin alıyoruz ve dört hücreyi okuyoruz.

```python
# ---------- 1) Ikili siniflandirma: meme kanseri verisi ----------
veri = load_breast_cancer()
# sklearn'de hedef 0 = kotu huylu (malignant). Pozitif sinifi
# "kotu huylu" yapiyoruz: tespit etmek istedigimiz sey bu.
y = (veri.target == 0).astype(int)
X_tr, X_te, y_tr, y_te = train_test_split(
    veri.data, y, test_size=0.3, stratify=y, random_state=57)
model = make_pipeline(StandardScaler(),
                      LogisticRegression(max_iter=1000))
model.fit(X_tr, y_tr)
skor = model.predict_proba(X_te)[:, 1]
tahmin = (skor >= 0.5).astype(int)

K = karisiklik(y_te, tahmin, [0, 1])
tp, fp, fn, tn = K[1, 1], K[0, 1], K[1, 0], K[0, 0]
print("Karisiklik matrisi (satir=gercek, sutun=tahmin)")
print("           tahmin:0  tahmin:1")
print("gercek:0 %9d %9d" % (K[0, 0], K[0, 1]))
print("gercek:1 %9d %9d" % (K[1, 0], K[1, 1]))
print("TP=%d FP=%d FN=%d TN=%d" % (tp, fp, fn, tn))

acc = (tp + tn) / K.sum()
pre = bol(tp, tp + fp)
rec = bol(tp, tp + fn)
spe = bol(tn, tn + fp)
f1 = f_beta(pre, rec, 1.0)
f2 = f_beta(pre, rec, 2.0)
f05 = f_beta(pre, rec, 0.5)
mcc = mcc_ikili(tp, tn, fp, fn)
kap = kappa(K)

print("\nScratch metrikler (ikili):")
print("dogruluk   %.4f" % acc)
print("kesinlik   %.4f" % pre)
print("duyarlilik %.4f" % rec)
print("ozgulluk   %.4f" % spe)
print("F1         %.4f  F2 %.4f  F0.5 %.4f" % (f1, f2, f05))
print("MCC        %.4f" % mcc)
print("kappa      %.4f" % kap)
```

Kodun ikinci yarısı, ölçütleri tek tek hesaplayıp sklearn'ün karşılığıyla eşleştirir. `assert` satırları eşleşmeyen bir sayı varsa programı durdurur; bu, kendi kodunun doğrulanmış olduğu anlamına gelir.

```python
# sklearn ile birebir karsilastirma
esit = [
    ("dogruluk", acc, M.accuracy_score(y_te, tahmin)),
    ("kesinlik", pre, M.precision_score(y_te, tahmin)),
    ("duyarlilik", rec, M.recall_score(y_te, tahmin)),
    ("ozgulluk", spe, M.recall_score(y_te, tahmin, pos_label=0)),
    ("F1", f1, M.f1_score(y_te, tahmin)),
    ("F2", f2, M.fbeta_score(y_te, tahmin, beta=2)),
    ("F0.5", f05, M.fbeta_score(y_te, tahmin, beta=0.5)),
    ("MCC", mcc, M.matthews_corrcoef(y_te, tahmin)),
    ("kappa", kap, M.cohen_kappa_score(y_te, tahmin)),
]
print("\nsklearn ile karsilastirma:")
en_buyuk = 0.0
for ad, bizim, sk in esit:
    en_buyuk = max(en_buyuk, abs(bizim - sk))
    print("%-11s bizim %.6f  sklearn %.6f" % (ad, bizim, sk))
print("en buyuk fark: %.2e" % en_buyuk)
assert en_buyuk < 1e-9
assert np.array_equal(K, M.confusion_matrix(y_te, tahmin))

# Dengesizlik: her zaman "iyi huylu" diyen tahminci
sabit = np.zeros_like(y_te)
print("\nHer zaman 'iyi huylu' diyen tahminci:")
print("dogruluk = %.4f  MCC = %.4f  kappa = %.4f" % (
    M.accuracy_score(y_te, sabit),
    M.matthews_corrcoef(y_te, sabit),
    M.cohen_kappa_score(y_te, sabit)))
```

```term
$ python b57_01_metrikler.py
Karisiklik matrisi (satir=gercek, sutun=tahmin)
           tahmin:0  tahmin:1
gercek:0       104         3
gercek:1         4        60
TP=60 FP=3 FN=4 TN=104

Scratch metrikler (ikili):
dogruluk   0.9591
kesinlik   0.9524
duyarlilik 0.9375
ozgulluk   0.9720
F1         0.9449  F2 0.9404  F0.5 0.9494
MCC        0.9124
kappa      0.9123

sklearn ile karsilastirma:
dogruluk    bizim 0.959064  sklearn 0.959064
kesinlik    bizim 0.952381  sklearn 0.952381
duyarlilik  bizim 0.937500  sklearn 0.937500
ozgulluk    bizim 0.971963  sklearn 0.971963
F1          bizim 0.944882  sklearn 0.944882
F2          bizim 0.940439  sklearn 0.940439
F0.5        bizim 0.949367  sklearn 0.949367
MCC         bizim 0.912399  sklearn 0.912399
kappa       bizim 0.912327  sklearn 0.912327
en buyuk fark: 1.11e-16

Her zaman 'iyi huylu' diyen tahminci:
dogruluk = 0.6257  MCC = 0.0000  kappa = 0.0000
```

Çıktının ilk bölümü ikili kısmın sonucudur. `karisiklik` ile sayılan matris, ölçütlerin hepsi için sklearn ile en fazla 10⁻¹⁶ (kayan noktanın doğal hassasiyeti) fark verir; bu, eşleşme olarak kabul edilir. Sayılar meme kanseri verisinin test kümesinden geliyor: 171 test örneğinde 60 gerçek kötü huylu tümör doğru bulundu (TP), 4 tanesi kaçtı (FN), 3 iyi huylu tümör yanlışlıkla kötü huylu sanıldı (FP). Kesinlik %95,2, duyarlılık %93,8. Son satırdaki tahminci, her zaman "iyi huylu" diyerek doğruluk %62,6 alıyor ama MCC ve kappa sıfır: ölçütler bu tahminciyi model olarak kabul etmiyor.

## 57.3 Çok sınıflı ortalamalar; kappa ve MCC

Rakam veri setinde 10 sınıf vardır. Her sınıf için ayrı bir kesinlik, duyarlılık ve F1 hesaplanır; bunları tek sayıya indirmek için üç ortalama yaygındır. **Makro** ortalama sınıfların ölçütlerini eşit ağırlıkla ortalar: nadir bir sınıf da, çok örneği olan bir sınıf kadar etki eder. **Mikro** ortalama önce bütün TP, FP ve FN değerlerini toplar, sonra tek bir oran hesaplar: örneği çok olan sınıflar baskın olur. **Ağırlıklı** ortalama makro gibidir, ama her sınıfı destek (gerçek örnek sayısı) ile çarpar.

Tek etiketli çok sınıflı problemde mikro F1 her zaman doğruluğa eşittir; çünkü bir yanlış tahmin hem bir FP hem bir FN üretir ve toplamda bu iki sayı birbirini dengeler. Rakam veri setinde sınıflar dengeli olduğu için üç ortalama birbirine yakın çıkar (makro F1 0,9779, mikro F1 0,9778). Ortalamalar arasındaki asıl fark dengesiz sınıflarda ortaya çıkar. Bunu görmek için programın sonuna üç sınıflı bir oyuncak matris ekledik. Satırlar gerçek, sütunlar tahmin. Birinci sınıfta 95 örnek var, üçüncü sınıf yalnızca 5 örnekle temsil ediliyor ve ikinci sınıf zayıf öğreniliyor.

```python
# ---------- 2) Cok sinifli: el yazisi rakamlari (10 sinif) ----------
d = load_digits()
Xd_tr, Xd_te, yd_tr, yd_te = train_test_split(
    d.data, d.target, test_size=0.3, stratify=d.target,
    random_state=57)
md = make_pipeline(StandardScaler(),
                    LogisticRegression(max_iter=2000))
md.fit(Xd_tr, yd_tr)
td = md.predict(Xd_te)
Kd = karisiklik(yd_te, td, list(range(10)))
o = ortalamalar(Kd)
print("\nCok sinifli (10 rakam): makro/mikro/agirlikli")
for ad in ["makro_kesinlik", "mikro_kesinlik", "agirlikli_kesinlik",
           "makro_F1", "mikro_F1", "agirlikli_F1"]:
    print("%-20s %.4f" % (ad, o[ad]))
print("dogruluk             %.4f" % M.accuracy_score(yd_te, td))
print("kappa                %.4f" % kappa(Kd))
print("MCC (cok sinif)      %.4f" % M.matthews_corrcoef(yd_te, td))

# sklearn ile eslesme (average parametresi)
sk_makro = M.f1_score(yd_te, td, average="macro")
sk_mikro = M.f1_score(yd_te, td, average="micro")
sk_agir = M.f1_score(yd_te, td, average="weighted")
assert abs(o["makro_F1"] - sk_makro) < 1e-9
assert abs(o["mikro_F1"] - sk_mikro) < 1e-9
assert abs(o["agirlikli_F1"] - sk_agir) < 1e-9
assert abs(o["mikro_F1"] - M.accuracy_score(yd_te, td)) < 1e-12
print("\nsklearn makro/mikro/agirlikli F1 ile birebir eslesti.")
print("Mikro F1 = dogruluk (tek etiketli cok sinifta).")
```

Bu kısım rakam verisini eğitir ve test eder; ardından sınıf bazlı en zayıf üç sınıfı listeler. Eğitimi ve sayım mantığını daha önce gördün; burada yeni olan, ortalamaların nasıl birleştiği.

```python
# Dilim: her sinifin F1'i, en zayif olanlar
_, _, _, _, _, f1s = sinif_metrikleri(Kd)
sira = np.argsort(f1s)[:3]
print("En zayif 3 sinif (F1):", [(int(i), round(float(f1s[i]), 3))
                                  for i in sira])

# Sekil verisi: karisiklik matrisi (ikili, meme kanseri test kumesi)
import os as _os
_veri = r"D:\Mevcut Projeler\Kitap\engine\veri"
_os.makedirs(_veri, exist_ok=True)
with open(_os.path.join(_veri, "b57_karisiklik.csv"), "w",
          encoding="utf-8") as _f:
    _f.write("gercek,tahmin,sayi\n")
    for _i in range(2):
        for _j in range(2):
            _f.write("%d,%d,%d\n" % (_i, _j, K[_i, _j]))
```

Oyuncak matristeki gerçek örnek sayıları `np.full` ve `np.repeat` ile yeniden üretilip sklearn'ün `average="macro"`, `"micro"` ve `"weighted"` seçenekleriyle karşılaştırılıyor. Son satırda doğruluğun mikro F1 ile aynı çıktığını da görüyorsun.

```python
# Dengesiz cok sinifli oyuncak: makro ve mikro farki
K3 = np.array([[90, 5, 0], [3, 2, 0], [0, 1, 4]])
o3 = ortalamalar(K3)
print("\nOyuncak 3 sinif (satir=gercek):")
for ad in ["makro_F1", "mikro_F1", "agirlikli_F1"]:
    print("%-14s %.4f" % (ad, o3[ad]))
y3 = np.concatenate([np.full(K3[i].sum(), i) for i in range(3)])
t3 = np.concatenate(
    [np.repeat(np.arange(3), K3[i]) for i in range(3)])
sk = M.f1_score(y3, t3, average="macro")
assert abs(o3["makro_F1"] - sk) < 1e-9
sk = M.f1_score(y3, t3, average="micro")
assert abs(o3["mikro_F1"] - sk) < 1e-9
assert abs(o3["agirlikli_F1"]
           - M.f1_score(y3, t3, average="weighted")) < 1e-9
acc3 = M.accuracy_score(y3, t3)
print("Dogruluk = %.4f (mikro F1 ile ayni)" % acc3)
```

```term
Cok sinifli (10 rakam): makro/mikro/agirlikli
makro_kesinlik       0.9782
mikro_kesinlik       0.9778
agirlikli_kesinlik   0.9781
makro_F1             0.9779
mikro_F1             0.9778
agirlikli_F1         0.9778
dogruluk             0.9778
kappa                0.9753
MCC (cok sinif)      0.9753

sklearn makro/mikro/agirlikli F1 ile birebir eslesti.
Mikro F1 = dogruluk (tek etiketli cok sinifta).
En zayif 3 sinif (F1): [(3, 0.954), (9, 0.955), (5, 0.964)]

Oyuncak 3 sinif (satir=gercek):
makro_F1       0.7180
mikro_F1       0.9143
agirlikli_F1   0.9232
Dogruluk = 0.9143 (mikro F1 ile ayni)
```

Çıktının son bölümü dengesizliği sayıya çeviriyor. Oyuncak matriste doğruluk %91,4 ve mikro F1 de aynı değer. Makro F1 ise %71,8'de: ikinci sınıfın F1'i 0,31 olduğu için eşit ağırlıkla ortalandığında tüm ortalamayı aşağı çekiyor. Ağırlıklı F1 (%92,3) ise çoğunluk sınıfını öne çıkarıyor. Hangi ortalamayı raporlayacağın, "az görülen sınıf için de başarılı olmalı mıyız?" sorusunun cevabına bağlıdır. Savunma tespitinde nadir ama kritik bir sınıf (örneğin yeni bir tehdit tipi) genellikle makro ile izlenir.

**Kappa ve MCC.** Doğruluğun ve F1'in yanıltıcı olduğu yerde iki ölçüt daha dürüsttür. Cohen kappa, gözlenen uyumu (doğruluk) sansa bağlı beklenen uyumla karşılaştırır: κ = (p₀ − pₑ) / (1 − pₑ). Burada pₑ, gerçek ve tahmin dağılımlarının çarpımlarından gelen şansa bağlı uyumdur. Her zaman tek sınıf tahmin eden bir model kappa sıfır alır, çünkü pₑ ile p₀ tam olarak çakışır.

Matthews korelasyon katsayısı (MCC) ise dört hücrenin tamamını tek bir sayıda birleştirir: MCC = (TP·TN − FP·FN) / √((TP+FP)(TP+FN)(TN+FP)(TN+FN)). Değeri −1 ile +1 arasındadır; +1 mükemmel, 0 rastgele tahmin, −1 tersine tahmindir. Hiçbir hücresini görmezden gelmediği için dengesiz veride kesinlik ve duyarlılığın tek başına verdiği yanılsamayı kırar. Programın çıktısında bu, pratik bir sonuç veriyor: aynı tahminci için doğruluk %62,6 görünürken MCC 0,0000'dır.

## 57.4 Skor, eşik ve ROC eğrisi

Çoğu modelin doğal çıktısı bir karar değil, bir **skordur**: lojistik regresyonda olasılık, ağaç topluluğunda oy oranı, bir sinir ağında son katmanın sigmoid değeri. Karar, bir **eşik** (threshold) ile verilir: skor ≥ t ise pozitif. Eşik 0'dan 1'e çıkarken her eşik kendi TPR ve FPR değerini verir. Bu noktaların kümesi bir eğri çizer: **ROC eğrisi** (Receiver Operating Characteristic). Eşik 1'den başlayıp 0'a inerse nokta (0,0)'dan (1,1)'e gider. Eşik yüksekse hiçbir şey pozitif sayılmaz; eşik düşükse her şey pozitif sayılır.

Eşikleri tek tek denemek yerine sıralamak yeterlidir. Skorları büyükten küçüğe sıralayıp her noktada TP ve FP sayılarını kümülatif olarak artırırsan, bütün eşikler tek bir geçişte gelir. Bu, n örnek için O(n log n) (sıralama) + O(n) (tarama) maliyet demektir. Her eşik için tüm örnekleri yeniden tarayan kaba kuvvet yaklaşımı ise O(n·u) (u farklı skor sayısı) çalışır. Programda ikisini karşılaştırıyoruz.

**AUC** (eğrinin altındaki alan), ROC eğrisinin altında kalan alandır ve tüm eşikler üzerinden tek bir sayı verir. Bunu yamuk kuralıyla hesaplayabilirsin. Asıl önemli yorumu ise sıralamadır: AUC, rastgele seçilen bir pozitif örneğin, rastgele seçilen bir negatif örnekten daha yüksek skor alma olasılığıdır (eşitlikte yarım sayılır). Bu, Mann–Whitney U istatistiğinin normalleştirilmiş hâlidir. Yani AUC bir eşik ölçütü değil, bir sıralama ölçütüdür: skorun değerini değil, sıralamasını ölçer. Bu yüzden monoton (artan) her dönüşüm AUC'yi değiştirmez; yalnızca olasılıkların ölçeği değişirse ROC-AUC sabit kalır. Bunu kalibrasyonda (57.7) yeniden göreceğiz.

Aşağıdaki kodda önce sekiz örnekli bir oyuncak veriyle yamuk alanını, Mann–Whitney eşdeğerliğini ve sklearn'ü karşılaştırıyoruz. Sonra 400 rastgele örnekte aynı üç yolun aynı sonucu verdiğini gösteriyoruz.

```python
# b57_02_roc_pr.py
# ROC ve PR egrileri sifirdan; AUC = Mann-Whitney; dengesizlik
import os
import numpy as np
from sklearn import metrics as M
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"

def esik_sayaclari(y, skor):
    """Her farkli skor esigi icin TP ve FP sayilari."""
    sira = np.argsort(-skor, kind="mergesort")
    y_s, s_s = y[sira], skor[sira]
    # Ayni skorlu ornekler tek bir esik olusturur: grup sonlari
    son = np.r_[np.where(np.diff(s_s))[0], len(s_s) - 1]
    tp = np.cumsum(y_s)[son]
    fp = (son + 1) - tp
    return s_s[son], tp, fp

def roc_noktalari(y, skor):
    P, N = y.sum(), len(y) - y.sum()
    _, tp, fp = esik_sayaclari(y, skor)
    tpr = np.r_[0.0, tp / P]
    fpr = np.r_[0.0, fp / N]
    return fpr, tpr

def pr_noktalari(y, skor):
    P = y.sum()
    _, tp, fp = esik_sayaclari(y, skor)
    precision = tp / (tp + fp)
    recall = tp / P
    return precision, recall
```

Yukarıdaki üç fonksiyon, skorları sıralayıp her grup sonunda TP ve FP değerlerini verir (`esik_sayaclari`). ROC ve PR noktaları bu iki diziden hesaplanır. Eşit skorlu örnekler tek bir eşik oluşturur; bu yüzden `np.diff` ile skorun değiştiği yerler bulunur.

```python
def roc_naif(y, skor):
    """O(n*u) kaba kuvvet: her esik icin tum ornekleri tara."""
    P, N = y.sum(), len(y) - y.sum()
    fpr, tpr = [0.0], [0.0]
    for t in np.unique(skor)[::-1]:
        tahmin = skor >= t
        tpr.append(np.sum(tahmin & (y == 1)) / P)
        fpr.append(np.sum(tahmin & (y == 0)) / N)
    return np.array(fpr), np.array(tpr)

def auc_trapez(fpr, tpr):
    return np.trapezoid(tpr, fpr)

def ortalama_kesinlik(precision, recall):
    """AP = sum (R_n - R_{n-1}) * P_n, R_0 = 0 (sklearn tanimi)."""
    r_onc = np.r_[0.0, recall[:-1]]
    return np.sum((recall - r_onc) * precision)

def auc_mann_whitney(y, skor):
    """P(pozitif skor > negatif skor) + 0.5 * P(esit)."""
    poz, neg = skor[y == 1], skor[y == 0]
    fark = poz[:, None] - neg[None, :]
    return ((fark > 0).sum() + 0.5 * (fark == 0).sum()) / (
        len(poz) * len(neg))
```

Kaba kuvvet (`roc_naif`) ile sıralama tabanlı yöntem aynı noktaları üretir; bunu programda `allclose` ile doğruluyoruz. `auc_mann_whitney` ise pozitif-negatif çiftlerinin tamamını karşılaştırır: O(n₊·n₋) maliyetli ama anlaşılması en kolay tanımdır.

```python
# ---------- 1) Kucuk ornek: elle izlenebilir ----------
y_k = np.array([1, 0, 1, 1, 0, 0, 1, 0])
s_k = np.array([0.9, 0.8, 0.7, 0.7, 0.4, 0.3, 0.2, 0.1])
fpr_k, tpr_k = roc_noktalari(y_k, s_k)
print("Kucuk ornek: esik, TPR, FPR")
esikler, tp, fp = esik_sayaclari(y_k, s_k)
for e, a, b in zip(esikler, tpr_k[1:], fpr_k[1:]):
    print("%.2f   %.3f   %.3f" % (e, a, b))
print("AUC (yamuk)      = %.4f" % auc_trapez(fpr_k, tpr_k))
print("AUC (Mann-Whitney)= %.4f" % auc_mann_whitney(y_k, s_k))
print("sklearn roc_auc   = %.4f" % M.roc_auc_score(y_k, s_k))
assert abs(auc_trapez(fpr_k, tpr_k)
           - M.roc_auc_score(y_k, s_k)) < 1e-12
```

Sekiz örnekli oyuncakta pozitif örnekler 0,9; 0,7; 0,7 ve 0,2 skorlarını almıştır; iki 0,7 aynı eşiği paylaştığı için tek bir basamak oluşturur. Her eşik için TPR ve FPR elle hesaplanabilir; programın çıktısı bunların tablosudur. Alanı yamuklarla topladığımızda 0,6875 çıkar; Mann–Whitney sayımı da aynı değeri verir.

```python
# ---------- 2) Rastgele 400 ornek: uc yol ayni ----------
rng = np.random.default_rng(57)
y_r = rng.integers(0, 2, 400)
s_r = rng.normal(loc=0.8 * y_r, scale=1.0)   # pozitifler biraz yuksek
a1 = auc_trapez(*roc_noktalari(y_r, s_r))
a2 = auc_mann_whitney(y_r, s_r)
a3 = M.roc_auc_score(y_r, s_r)
print("\nRastgele 400 ornek:")
print("yamuk %.6f  MW %.6f  sklearn %.6f" % (a1, a2, a3))
assert abs(a1 - a2) < 1e-12 and abs(a2 - a3) < 1e-12

# Kaba kuvvet ve siralama ayni eglriyi uretiyor mu?
f_n, t_n = roc_naif(y_r, s_r)
f_s, t_s = roc_noktalari(y_r, s_r)
print("kaba kuvvet ile siralama ayni nokta sayisi: %d = %d"
      % (len(f_n), len(f_s)))
assert np.allclose(f_n, f_s) and np.allclose(t_n, t_s)
fs_sk, ts_sk, _ = M.roc_curve(y_r, s_r, drop_intermediate=False)
assert np.allclose(fs_sk, f_s) and np.allclose(ts_sk, t_s)
print("sklearn roc_curve(drop_intermediate=False) ile birebir.")
# Sklearn 1.8 cekirdek sayaclari (confusion_matrix_at_thresholds)
tns, fps_sk, fns, tps_sk, esik_sk = M.confusion_matrix_at_thresholds(
    y_r, s_r)
esik_b, tp_b, fp_b = esik_sayaclari(y_r, s_r)
assert np.allclose(tps_sk, tp_b) and np.allclose(fps_sk, fp_b)
assert np.allclose(esik_sk, esik_b)
print("TP/FP dizileri ve esikler confusion_matrix_at_thresholds")
print("ile ayni.")
```

Rastgele 400 örnekte pozitifler hafifçe daha yüksek skorlu üretilmiştir. Üç yöntem (yamuk, Mann–Whitney ve sklearn) 0,696593 değerinde birleşir. Kaba kuvvet ile sıralama tabanlı yöntemin nokta sayıları da aynıdır (401). Son doğrulamada sklearn'ün `confusion_matrix_at_thresholds` fonksiyonunun TP ve FP dizilerini de bizimkilerle karşılaştırıyoruz; bu, Kod Okuma egzersizinin konusudur.

## 57.5 Precision–recall eğrisi ve dengesizlikte ROC'un yanılgısı

ROC eğrisi, FPR = FP / N paydasını kullanır. N, negatif örneklerin sayısıdır. Pozitifler çok nadirse (ör. %1) N çok büyür, FP'nin payı ne kadar büyük olursa olsun FPR küçük kalır ve eğri yukarıya, sol üst köşeye yapışır. Sonuç: ROC-AUC iyimser görünür. **Kesinlik–duyarlılık (PR) eğrisi** ise FP'yi yalnızca pozitif tahminlere oranlar: kesinlik = TP / (TP + FP). Negatiflerin sayısı burada yer almaz. Bu yüzden nadir pozitif sınıfta gerçek performansı PR daha dürüst gösterir.

PR eğrisinin bir taban çizgisi vardır: rastgele bir tahminci için kesinlik, pozitif oranına (prevalans) eşit olur. %1 pozitif bir veride bu çizgi 0,01'dir; ROC'un 0,5 olan "rastgele çizgisiyle" karşılaştırmak yanıltıcıdır. Eğrinin altındaki alanın yaklaşık hesabı için **ortalama kesinlik** (AP) kullanılır: AP = Σ (Rₙ − Rₙ₋₁) · Pₙ. sklearn'ün `average_precision_score` tanımı budur; yamuk değil, basamaklı bir toplamdır. Bu iki ölçüt arasındaki farkı görmek için programın üçüncü bölümünde iki model karşılaştırılıyor.

```python
# ---------- 3) Dengesiz veri: %1 pozitif ----------
X, y = make_classification(
    n_samples=100000, n_features=20, n_informative=6, n_redundant=2,
    weights=[0.99], flip_y=0.0, class_sep=1.0, random_state=57,
    shuffle=False)
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=57)
print("\nDengesiz veri: pozitif orani train=%.4f test=%.4f"
      % (y_tr.mean(), y_te.mean()))

# Model A: tum oznitelikler. Model B: yalnizca ilk 3 oznitelik.
mA = make_pipeline(StandardScaler(),
                    LogisticRegression(max_iter=1000))
mB = make_pipeline(StandardScaler(),
                    LogisticRegression(max_iter=1000))
mA.fit(X_tr, y_tr)
mB.fit(X_tr[:, :3], y_tr)
sA = mA.predict_proba(X_te)[:, 1]
sB = mB.predict_proba(X_te[:, :3])[:, 1]
```

Veri 100.000 örnekli, %1 pozitifli sentetik bir kümedir (`make_classification` ile `weights=[0.99]`). Model A tüm 20 özniteliği, model B yalnızca ilk üç özniteliği kullanır. Bilgilendirici öznitelikleri `shuffle=False` ile en başta tutuyoruz; aksi hâlde ilk üç sütunun gerçekte bilgisiz olabileceğini bu bölümü yazarken gördük.

```python
print("\nModel        ROC-AUC    PR-AUC (AP)   taban (oran)")
satirlar = []
for ad, s in [("A (20 oznitelik)", sA), ("B (3 oznitelik)", sB)]:
    fpr, tpr = roc_noktalari(y_te, s)
    pre, rec = pr_noktalari(y_te, s)
    roc = auc_trapez(fpr, tpr)
    ap = ortalama_kesinlik(pre, rec)
    assert abs(roc - M.roc_auc_score(y_te, s)) < 1e-9
    assert abs(ap - M.average_precision_score(y_te, s)) < 1e-9
    print("%-16s %.4f     %.4f        %.4f"
          % (ad, roc, ap, y_te.mean()))
    satirlar.append((ad, fpr, tpr, rec, pre))

print("\nScratch ROC-AUC ve AP sklearn roc_auc_score ve")
print("average_precision_score ile birebir eslesti.")

# ROC farki, AP farki: hangisi daha cok ayiriyor?
roc_A = M.roc_auc_score(y_te, sA)
roc_B = M.roc_auc_score(y_te, sB)
ap_A = M.average_precision_score(y_te, sA)
ap_B = M.average_precision_score(y_te, sB)
print("\nFark (A - B): ROC-AUC %.4f, AP %.4f"
      % (roc_A - roc_B, ap_A - ap_B))

# Dogru pozitif sayisi ve FP: %1 de 100 kisiden 1 pozitif
P_test = y_te.sum()
N_test = len(y_te) - P_test
print("Test: P=%d N=%d. Yanlis alarm orani %%1 olsa bile"
      % (P_test, N_test))
print("%.0f negatif ornekte %.0f yanlis alarm demek."
      % (N_test, 0.01 * N_test))
```

Burada iki model için ROC-AUC ve AP'yi iki yoldan hesaplıyoruz: kendi yazdığımız fonksiyonlarla ve sklearn ile. Sonra dengeli bir veride (%50 pozitif) aynı tür modelin sonuçlarını alıyoruz. Son satır, bir CSV dosyasını şekil için yazar; ROC ve PR noktalarını ayrı sütunlarda tutuyoruz ve dosya boyutu için noktaları seyrekleştiriyoruz.

```python
# Ayni model A, pozitifleri %50 yapilmis (dengeli) veride
X2, y2 = make_classification(
    n_samples=20000, n_features=20, n_informative=6, n_redundant=2,
    weights=[0.5], flip_y=0.0, class_sep=1.0, random_state=57,
    shuffle=False)
X2_tr, X2_te, y2_tr, y2_te = train_test_split(
    X2, y2, test_size=0.3, stratify=y2, random_state=57)
mD = make_pipeline(StandardScaler(),
                    LogisticRegression(max_iter=1000))
mD.fit(X2_tr, y2_tr)
sD = mD.predict_proba(X2_te)[:, 1]
print("\nDengeli veri (%50 pozitif), ayni tur model:")
print("ROC-AUC %.4f  AP %.4f  taban %.4f"
      % (M.roc_auc_score(y2_te, sD),
         M.average_precision_score(y2_te, sD), y2_te.mean()))

# ---------- Egri verisi (sekil icin) ----------
os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_roc_pr_egri.csv")
with open(yol, "w", encoding="utf-8") as f:
    f.write("model,fpr,tpr,recall,precision\n")
    for ad, fpr, tpr, rec, pre in satirlar:
        ad_kisa = "A" if ad.startswith("A") else "B"
        # ROC ve PR noktalari farkli uzunlukta; ayri yazilir
        # Dosya boyutu icin ~300 noktaya seyreltilmis
        k_roc = max(1, len(fpr) // 300)
        for a, b in list(zip(fpr, tpr))[::k_roc]:
            f.write("%s,%.6f,%.6f,,\n" % (ad_kisa, a, b))
        k_pr = max(1, len(rec) // 300)
        for r, p in list(zip(rec, pre))[::k_pr]:
            f.write("%s,,,%.6f,%.6f\n" % (ad_kisa, r, p))
print("\nEgri verisi yazildi:", os.path.basename(yol))

# Sekil verisi: 8 ornekli kucuk ornek, esik bazinda
_e, _tp, _fp = esik_sayaclari(y_k, s_k)
with open(os.path.join(VERI, "b57_kucuk_ornek.csv"), "w",
          encoding="utf-8") as _f:
    _f.write("esik,tpr,fpr,kesinlik,duyarlilik\n")
    _P, _N = y_k.sum(), len(y_k) - y_k.sum()
    for _a, _t, _b in zip(_e, _tp, _fp):
        _f.write("%.2f,%.5f,%.5f,%.5f,%.5f\n" % (
            _a, _t / _P, _b / _N, _t / (_t + _b), _t / _P))
```

```term
$ python b57_02_roc_pr.py
Kucuk ornek: esik, TPR, FPR
0.90   0.250   0.000
0.80   0.250   0.250
0.70   0.750   0.250
0.40   0.750   0.500
0.30   0.750   0.750
0.20   1.000   0.750
0.10   1.000   1.000
AUC (yamuk)      = 0.6875
AUC (Mann-Whitney)= 0.6875
sklearn roc_auc   = 0.6875

Rastgele 400 ornek:
yamuk 0.696593  MW 0.696593  sklearn 0.696593
kaba kuvvet ile siralama ayni nokta sayisi: 401 = 401
sklearn roc_curve(drop_intermediate=False) ile birebir.
TP/FP dizileri ve esikler confusion_matrix_at_thresholds
ile ayni.

Dengesiz veri: pozitif orani train=0.0100 test=0.0100

Model        ROC-AUC    PR-AUC (AP)   taban (oran)
A (20 oznitelik) 0.9368     0.5698        0.0100
B (3 oznitelik)  0.6851     0.2101        0.0100

Scratch ROC-AUC ve AP sklearn roc_auc_score ve
average_precision_score ile birebir eslesti.

Fark (A - B): ROC-AUC 0.2516, AP 0.3597
Test: P=300 N=29700. Yanlis alarm orani %1 olsa bile
29700 negatif ornekte 297 yanlis alarm demek.

Dengeli veri (%50 pozitif), ayni tur model:
ROC-AUC 0.9382  AP 0.9301  taban 0.5000

Egri verisi yazildi: b57_roc_pr_egri.csv
```

Yukarıdaki çıktı dengesiz veriyi açıkça gösteriyor. Model A'nın ROC-AUC'si 0,937 (iyi görünüyor), AP'si 0,570 (yarısından fazla alarm yanlış olabilir). Model B'nin ROC-AUC'si 0,685, AP'si 0,210. ROC farkı 0,25 iken AP farkı 0,36 çıkıyor: dengesizlikte PR, modeller arasındaki gerçek farkı daha büyük gösteriyor. Dengeli veride (%50 pozitif) aynı tür model 0,938 ROC ve 0,930 AP veriyor; iki ölçüt birbirine yakın. Dengesizlik ROC'u şişirir, AP'yi ise değiştirir.

Sayıları somutlaştıralım. Test kümesinde 29.700 negatif örnek var. Yanlış alarm oranı %1 olsa bile bu 297 yanlış alarm demektir. Eğer 300 pozitifin 240'ını yakalıyorsan (duyarlılık %80), FPR 0,01 çıkar ama alarmların (240 + 297 = 537) %55'i yanlıştır (297 / 537). Operatör alarmın yarısından fazlasının yanlış olduğunu görür; ROC'un "%1 yanlış alarm" cümlesi bunu gizler.

![Şekil 57.2: Sekiz örnekli oyuncakta esik taramasi. Sol: ROC eğrisi ve her eşiğin etiketi (AUC 0,6875). Sağ: PR eğrisi (AP 0,7679). Basamaklar, eşik düştükçe pozitiflerin sırayla eklenmesidir.](gorseller/b57_kucuk_roc_pr.png)

![Şekil 57.3: %1 pozitifli veride iki modelin ROC (sol) ve PR (sağ) eğrileri. ROC'ta model A açıkça üstündür; PR'da model B'nin zayıflığı ve taban çizgisine (0,01) yakınlığı çok daha belirgindir.](gorseller/b57_dengesiz_roc_pr.png)

Şekil 57.2'de sekiz örnekli oyuncağın eğrileri yan yana. Sol panelde her basamak, bir eşik değişiminde gelen pozitif (yukarı) ya da negatif (sağa) örneği gösterir. Sağ panelde aynı eşikler kesinlik ve duyarlılık olarak görünür. Şekil 57.3 ise dengesiz veride iki modelin iki eğrisini gösterir: sol panelde ROC iki modeli nispeten yakın gösterirken, sağ panelde PR eğrisi model B'nin gerçek zayıflığını ortaya koyar.

**Pratik kural.** Pozitif sınıf nadirse (ör. %1'in altında), raporunda ROC-AUC'yi tek başına verme. AP, kesinlik–duyarlılık eğrisi ve bir çalışma noktasında (57.6) FP/gün gibi mutlak sayılar birlikte verilmelidir. Ve pozitif oranını (taban çizgisini) her zaman yanında belirt.

## 57.6 Maliyet temelli eşik ve çalışma noktası

Bir eşik seçmek, bir maliyet kararı vermektir. Her yanlış alarmın bedeli c_FP, her kaçan tespitin bedeli c_FN olsun. Beklenen maliyet, örnek başına şöyle yazılır: (c_FP · FP + c_FN · FN) / N. Bu ifadeyi en küçük yapan eşik, kalibre olasılıklar varsayımı altında bir formülle verilir. Bir örnek için iki seçeneği karşılaştır. Pozitif diyersen beklenen maliyet (1 − p) · c_FP; negatif diyersen p · c_FN. Pozitif demek, ancak birinci maliyet ikincisinden küçükse mantıklıdır. Eşitlik noktası şudur:

t* = c_FP / (c_FP + c_FN)

Bölüm 54'te bu formülü bir İHA bakım örneğinde 1/51 olarak görmüştük (c_FN = 50, c_FP = 1). Türetmenin koşulu önemlidir: p'nin gerçek olasılığa eşit olması, yani model kalibre olmalıdır. Kalibre değilse t* yanlış bir karara götürür; bunu 57.7'de göreceğiz.

Aşağıdaki programda bilinen bir lojistik olasılık modelinden 300.000 örnek üretiyoruz. Pozitif oranı yaklaşık %1. Bu şekilde "gerçek" olasılığı biliyoruz ve teorik t*'ın gerçekten en düşük beklenen maliyeti verip vermediğini sınayabiliyoruz. Sonra bir lojistik regresyonu eğitip aynı taramayı test kümesinde tekrarlıyoruz.

```python
# b57_03_esik_maliyet.py
# Maliyet temelli esik secimi ve calisma noktasi (Neyman-Pearson)
import os
import numpy as np
from sklearn import metrics as M
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
rng = np.random.default_rng(57)

# Gercek olasilik modeli bilinen: lojistik. Kalibre olasiliklar.
n = 300000
X = rng.normal(size=(n, 3))
w = np.array([1.2, -0.8, 0.5])
b = -5.6
p_gercek = 1.0 / (1.0 + np.exp(-(X @ w + b)))
y = (rng.random(n) < p_gercek).astype(int)
print("Pozitif orani: %.4f" % y.mean())

c_fp, c_fn = 1.0, 50.0          # yanlis alarm 1, kacan tespit 50
t_teori = c_fp / (c_fp + c_fn)  # kalibre olasiliklarda en iyi esik
print("Teorik esik t* = c_FP/(c_FP+c_FN) = 1/51 = %.5f" % t_teori)

def maliyet(p, y, t):
    """Ornek basina beklenen maliyet, esik t'de."""
    tahmin = p >= t
    fp = np.sum(tahmin & (y == 0))
    fn = np.sum(~tahmin & (y == 1))
    return (c_fp * fp + c_fn * fn) / len(y)
```

Önce gerçek olasılıklarla bir tarama yapılıyor ve her eşikte maliyet hesaplanıyor. `maliyet` fonksiyonu, verilen olasılık dizisi ile gerçek etiketlerden FP ve FN sayılarını çıkarır; karar kuralı `p >= t`.

```python
# 1) Gercek olasiliklar uzerinde esik taramasi
esikler = np.linspace(0.001, 0.2, 2000)
mal_gercek = np.array([maliyet(p_gercek, y, t) for t in esikler])
en_iyi = esikler[np.argmin(mal_gercek)]
print("Gercek olasilikla taramada en iyi esik: %.4f" % en_iyi)
print("Bu esikteki maliyet: %.5f" % mal_gercek.min())
print("t* = 0.0196'daki maliyet: %.5f"
      % maliyet(p_gercek, y, t_teori))

# 2) Ogrenilmis model: lojistik regresyon (egitim/test ayrimi)
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.4, random_state=57, stratify=y)
model = LogisticRegression(C=1e6, max_iter=5000).fit(X_tr, y_tr)
p_mod = model.predict_proba(X_te)[:, 1]
print("\nModelin katsayilari:", np.round(model.coef_[0], 3),
      "b=%.3f" % model.intercept_[0])

mal_mod = np.array([maliyet(p_mod, y_te, t) for t in esikler])
en_iyi_mod = esikler[np.argmin(mal_mod)]
print("Model olasiliklariyla en iyi esik (test): %.4f" % en_iyi_mod)
print("Bu esikteki maliyet: %.5f" % mal_mod.min())
print("t* = 0.0196'daki maliyet (test): %.5f" % maliyet(p_mod, y_te,
                                                         t_teori))

# 3) Calisma noktasi: FPR en fazla %1 iken en yuksek tespit
fpr, tpr, esik_roc = M.roc_curve(y_te, p_mod, drop_intermediate=False)
uygun = fpr <= 0.01
i = np.argmax(np.where(uygun, tpr, -1))
print("\nFPR <= 0.01 kisitinda en yuksek TPR = %.4f" % tpr[i])
print("Bu nokta icin esik = %.4f (FPR=%.5f)" % (esik_roc[i], fpr[i]))
```

Modelin olasılıklarıyla yapılan tarama, gerçek olasılıklarınkine çok yakın bir sonuç verir. Çalışma noktası kısmı ise farklı bir soru sorar: "yanlış alarm oranı en fazla %1 olsun; bu koşulda en çok tespit hangisi?" Bu, ROC eğrisi üzerinde yatay bir kesit almaktır. `roc_curve` ile FPR ≤ 0,01 olan noktalar arasından en büyük TPR seçilir.

```python
# 4) Esik tablosu
print("\n  esik    TPR     FPR    maliyet/ornek")
for t in [0.005, 0.01, 0.0196, 0.05, 0.1, 0.2]:
    tah = p_mod >= t
    tp = np.sum(tah & (y_te == 1))
    fp = np.sum(tah & (y_te == 0))
    P = y_te.sum()
    N = len(y_te) - P
    print("%6.4f  %6.3f  %6.4f   %10.5f" % (
        t, tp / P, fp / N, maliyet(p_mod, y_te, t)))

# Sklearn ile dogrulama: en iyi esikte TP/FP sayilari
t = en_iyi_mod
tah = p_mod >= t
assert np.sum(tah & (y_te == 1)) == np.sum((p_mod >= t) & (y_te == 1))
assert abs(M.recall_score(y_te, tah.astype(int))
           - np.sum(tah & (y_te == 1)) / y_te.sum()) < 1e-12

# Maliyet egrisi verisi (sekil icin)
os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_esik_maliyet.csv")
ilk = np.geomspace(0.001, 0.2, 300)
with open(yol, "w", encoding="utf-8") as f:
    f.write("esik,maliyet_model,maliyet_gercek\n")
    for t in ilk:
        f.write("%.6f,%.6f,%.6f\n" % (t, maliyet(p_mod, y_te, t),
                                      maliyet(p_gercek, y, t)))
print("\nMaliyet verisi yazildi:", os.path.basename(yol))
```

```term
$ python b57_03_esik_maliyet.py
Pozitif orani: 0.0109
Teorik esik t* = c_FP/(c_FP+c_FN) = 1/51 = 0.01961
Gercek olasilikla taramada en iyi esik: 0.0199
Bu esikteki maliyet: 0.32292
t* = 0.0196'daki maliyet: 0.32356

Modelin katsayilari: [ 1.196 -0.779  0.546] b=-5.603
Model olasiliklariyla en iyi esik (test): 0.0212
Bu esikteki maliyet: 0.32562
t* = 0.0196'daki maliyet (test): 0.32666

FPR <= 0.01 kisitinda en yuksek TPR = 0.1860
Bu nokta icin esik = 0.1016 (FPR=0.00999)

  esik    TPR     FPR    maliyet/ornek
0.0050   0.902  0.4145      0.46375
0.0100   0.788  0.2486      0.36167
0.0196   0.636  0.1294      0.32670
0.0500   0.368  0.0367      0.38174
0.1000   0.190  0.0103      0.45315
0.2000   0.061  0.0020      0.51535

Maliyet verisi yazildi: b57_esik_maliyet.csv
```

Sonuçlar teoriyi doğruluyor. Gerçek olasılıklarla en iyi eşik 0,0199 çıktı; teorik t* = 1/51 = 0,0196. İki eşikteki maliyet arasındaki fark %0,2 (0,32292 ile 0,32356). Bu, eğrinin bu bölgede çok yassı olduğunu gösterir: yanlış eşiği biraz seçmenin cezası küçüktür, ama büyük sapmalar (0,005 ya da 0,05) belirgin bir maliyet artışı getirir. Tablodaki satırlar bunu gösteriyor: eşik 0,005'te 0,464, 0,05'te 0,382.

Model olasılıklarıyla en iyi eşik test kümesinde 0,0212 çıktı. Bu değer teorik değere yakındır, çünkü lojistik model bu verinin gerçek yapısıyla uyumludur. Gerçek bir projede ise eşiği test kümesinde seçmek, Bölüm 54'te öğrendiğimiz kuralı çiğnemek olur: eşik doğrulama kümesinde seçilir, test kümesi yalnızca son raporda kullanılır.

**Çalışma noktası.** Savunmada ya da sağlıkta çoğu zaman maliyet oranını bilmezsin; bunun yerine bir sözleşme vardır: "yanlış alarm oranı %1'i geçmesin". Bu koşulda en yüksek tespit oranını veren eşik, Neyman–Pearson ilkesinin pratik bir sezgisidir: sabit bir hata olasılığında en güçlü testi seçmek (genel bilgi). Çıktıdaki satır bunu sayıya döküyor: FPR ≤ 0,01 koşulunda en yüksek TPR 0,186'dır ve bunu sağlayan eşik 0,1016'dır. Yani yanlış alarmı yüzde birde tutmak için eşiği teorik t*'ın beş katından fazla yükseltmen gerekiyor ve tespitin yalnızca beşte biri yakalanıyor. Bu, modelin bu veride ne kadar yetersiz olduğunu gösteren dürüst bir sayıdır.

![Şekil 57.4: Ornek basina beklenen maliyet, esik boyunca (log olcek). Kesikli eğri gerçek olasılıklarla, düz eğri modelin olasılıklarıyla hesaplanır. Dikey çizgi t* = 1/51 eşiğidir.](gorseller/b57_esik_maliyet.png)

## 57.7 Olasılık kalitesi: log-kayıp, Brier ve kalibrasyon

Bir model iki şeyi aynı anda yapabilir: doğru sınıfları doğru sıraya koyabilir (AUC bunu ölçer) ve olasılıkları gerçek sıklıklara uygun verebilir (kalibrasyon). İkisi bağımsızdır. Bir model "%70 eminim" dediğinde, o gruptaki örneklerin gerçekten yaklaşık %70'i pozitif olmalıdır. Olasılık kalitesini ölçen iki kural tabanlı ölçüt vardır.

**Log-kayıp** (çapraz entropi): −(1/N) Σ [y log p + (1 − y) log(1 − p)]. Bu, Bölüm 51'de gördüğün çapraz entropinin ta kendisidir. Yanlış bir tahmin ne kadar emin verilmişse o kadar pahalıdır: p = 0,999 iken y = 0 olması, p = 0,6 iken aynı hatadan çok daha büyük ceza üretir. **Brier skoru** ise aynı işi kare hatayla yapar: (1/N) Σ (p − y)². İkisi de olasılık tahminlerini ödüllendiren "uygun" (proper) skor kurallarıdır: gerçek olasılığı bildirmek ortalama olarak en iyi skoru verir (genel bilgi).

Kalibrasyonu görmek için **güvenilirlik diyagramı** çizilir. Örnekler tahmin olasılığına göre kutulara (ör. 10 eşit aralığa) bölünür; her kutu için ortalama tahmin ile gözlenen pozitif oranı yan yana konur. Mükemmel kalibrasyonda noktalar köşegen üzerinde durur. Bu özet tek bir sayıya indirilmek istenirse **beklenen kalibrasyon hatası** (ECE) kullanılır: kutu ağırlıklı ortalama |ortalama tahmin − gözlenen oran|. Kutu sayısına ve örnek sayısına duyarlıdır; sonuçları raporlarken her ikisini de belirt.

Aşağıdaki programda üç model karşılaştırılıyor. Birincisi verinin gerçek yapısına uyan lojistik regresyon. İkincisi küçük bir veriyle, öğrenme oranı yüksek bir gradyan artırma (400 ağaç, derinlik 4), yani aşırı güvenli bir model. Üçüncüsü bu aşırı güvenli modelin olasılıklarını ayrı bir kalibrasyon kümesiyle düzeltilmiş hâli: Platt (sigmoid) ve izotonik. Kalibrasyon kümesi eğitimden ayrıdır; aynı veriyle hem model eğitip hem kalibre etmek, Bölüm 54'teki sızıntının bir biçimi olurdu.

```python
# b57_04_kalibrasyon.py
# Olasilik kalitesi: log-kayip, Brier, ECE, guvenilirlik diyagrami
import os
import numpy as np
from sklearn import metrics as M
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.linear_model import LogisticRegression

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
rng = np.random.default_rng(57)

def uret(n):
    X = rng.normal(size=(n, 4))
    w = np.array([1.0, -1.0, 0.6, 0.0])
    p = 1.0 / (1.0 + np.exp(-(X @ w - 0.8)))   # gercek olasilik
    y = (rng.random(n) < p).astype(int)
    return X, y, p

def log_kayip(y, p):
    eps = np.finfo(float).eps
    p = np.clip(p, eps, 1 - eps)
    return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))

def brier(y, p):
    return np.mean((p - y) ** 2)

def ece(y, p, kutu=10):
    """Beklenen kalibrasyon hatasi (ECE): kutu basina fark."""
    kenar = np.linspace(0, 1, kutu + 1)
    toplam = 0.0
    for a, b in zip(kenar[:-1], kenar[1:]):
        m = (p > a) & (p <= b) if a > 0 else (p >= a) & (p <= b)
        if m.sum() > 0:
            fark = abs(p[m].mean() - y[m].mean())
            toplam += m.sum() / len(p) * fark
    return toplam
```

`ece` fonksiyonu kutuları eşit aralıklarla kurar; `guvenilirlik` her kutunun ortalama tahminini ve gözlenen oranını döndürür. `log_kayip` sayısal taşmayı önlemek için olasılığı makine epsilon'una kıstırır; sklearn de aynısını yapar, bu yüzden iki değer eşleşir.

```python
def guvenilirlik(y, p, kutu=10):
    """Her kutu icin (ort tahmin, gozlenen oran, sayi)."""
    kenar = np.linspace(0, 1, kutu + 1)
    satirlar = []
    for a, b in zip(kenar[:-1], kenar[1:]):
        m = (p > a) & (p <= b) if a > 0 else (p >= a) & (p <= b)
        if m.sum() > 0:
            satirlar.append((p[m].mean(), y[m].mean(), int(m.sum())))
    return satirlar

# Gercek olasilik bilinir: kalibre model "gercek p" kullanilir.
X_tr, y_tr, _ = uret(3000)
X_te, y_te, p_te = uret(60000)
print("Pozitif orani (test): %.4f" % y_te.mean())

# 1) Kalibre model: dogru lojistik model (ozellikler bilinir)
lr = LogisticRegression(C=1e6, max_iter=5000).fit(X_tr, y_tr)
p_lr = lr.predict_proba(X_te)[:, 1]

# 2) Asiri guvenli model: kucuk veriyle derin gradyan artirma
gb = GradientBoostingClassifier(n_estimators=400, learning_rate=1.0,
                                max_depth=4, random_state=57)
gb.fit(X_tr, y_tr)
p_gb = gb.predict_proba(X_te)[:, 1]

# 3) Platt (sigmoid) ve izotonik kalibrasyon: AYNI gradyan modeli,
#    ayri bir kalibrasyon kumesiyle (X_ka). Model dondurulur.
X_ka, y_ka, _ = uret(3000)
cal_p = CalibratedClassifierCV(FrozenEstimator(gb),
                               method="sigmoid").fit(X_ka, y_ka)
cal_i = CalibratedClassifierCV(FrozenEstimator(gb),
                               method="isotonic").fit(X_ka, y_ka)
p_pl = cal_p.predict_proba(X_te)[:, 1]
p_iz = cal_i.predict_proba(X_te)[:, 1]

modeller = [("gercek-lojistik", p_lr), ("gradyan-artirma", p_gb),
            ("platt", p_pl), ("izotonik", p_iz)]
print("\nModel              log-kayip   Brier    ECE    ROC-AUC")
for ad, p in modeller:
    print("%-18s %8.4f  %7.4f  %6.4f  %7.4f" % (
        ad, log_kayip(y_te, p), brier(y_te, p), ece(y_te, p),
        M.roc_auc_score(y_te, p)))
```

Asıl deney, kalibre edilmemiş ve kalibre edilmiş modelleri aynı test kümesinde karşılaştırır. `CalibratedClassifierCV` ile `FrozenEstimator` kullanmak, gradyan artırma modelinin yeniden eğitilmesini önler: model yalnızca kalibrasyon kümesiyle dönüştürülür. Platt yöntemi lojistik bir dönüşüm, izotonik yöntem ise artan bir basamaklı fonksiyon öğrenir.

```python
# sklearn ile birebir karsilastirma
for ad, p in modeller:
    assert abs(log_kayip(y_te, p) - M.log_loss(y_te, p)) < 1e-9
    assert abs(brier(y_te, p) - M.brier_score_loss(y_te, p)) < 1e-12
print("\nLog-kayip ve Brier sklearn ile birebir eslesti.")

# Gercek olasiliklar (oracle): en iyi mumkun kalibrasyon
print("oracle (gercek p) log-kayip: %.4f  Brier: %.4f  ECE: %.4f" % (
    log_kayip(y_te, p_te), brier(y_te, p_te), ece(y_te, p_te)))

# Monoton donusum ROC-AUC'yi degistirmez: Platt icin tam esitlik
print("\nROC-AUC Platt - ham: %.2e" % (
    M.roc_auc_score(y_te, p_pl) - M.roc_auc_score(y_te, p_gb)))
print("ROC-AUC izotonik - ham: %.2e" % (
    M.roc_auc_score(y_te, p_iz) - M.roc_auc_score(y_te, p_gb)))
print("Izotonik ciktida benzersiz olasilik sayisi: %d (ham: %d)" % (
    len(np.unique(p_iz)), len(np.unique(p_gb))))

# Guvenilirlik tablosu: asiri guvenli model
print("\nGuvenilirlik (gradyan artirma): ort tahmin, gozlenen, sayi")
for a, b, c in guvenilirlik(y_te, p_gb):
    print("%.3f   %.3f   %6d" % (a, b, c))

# Sekil verisi
os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_kalibrasyon.csv")
with open(yol, "w", encoding="utf-8") as f:
    f.write("model,ort_tahmin,gozlenen,sayi\n")
    for ad in ["gradyan-artirma", "platt"]:
        p = dict(modeller)[ad]
        for a, b, c in guvenilirlik(y_te, p):
            f.write("%s,%.5f,%.5f,%d\n" % (ad, a, b, c))
print("\nKalibrasyon verisi yazildi:", os.path.basename(yol))
```

```term
$ python b57_04_kalibrasyon.py
Pozitif orani (test): 0.3623

Model              log-kayip   Brier    ECE    ROC-AUC
gercek-lojistik      0.4892   0.1616  0.0153   0.8236
gradyan-artirma      1.5051   0.2619  0.2385   0.7340
platt                0.5926   0.1966  0.0303   0.7340
izotonik             0.6209   0.1961  0.0192   0.7322

Log-kayip ve Brier sklearn ile birebir eslesti.
oracle (gercek p) log-kayip: 0.4881  Brier: 0.1613  ECE: 0.0054

ROC-AUC Platt - ham: 1.80e-09
ROC-AUC izotonik - ham: -1.80e-03
Izotonik ciktida benzersiz olasilik sayisi: 344 (ham: 59844)

Guvenilirlik (gradyan artirma): ort tahmin, gozlenen, sayi
0.010   0.216    33165
0.144   0.382     2553
0.248   0.410     1682
0.348   0.417     1313
0.450   0.450     1144
0.550   0.454     1156
0.651   0.441     1216
0.752   0.485     1397
0.854   0.492     1974
0.984   0.634    14400

Kalibrasyon verisi yazildi: b57_kalibrasyon.csv
```

Tablo üç şeyi gösteriyor. Birincisi, aşırı güvenli model ECE'de 0,2385 ve log-kayıpta 1,5051 ile en kötü durumda: olasılıklarının çoğu gerçek sıklığın çok üstünde. Güvenilirlik tablosunda en düşük kutu (ort. tahmin 0,010) gerçekte %21,6 pozitif çıkıyor; en yüksek kutu (0,984) ise %63,4. İkincisi, Platt kalibrasyonu ECE'yi 0,0303'e, izotonik ise 0,0192'ye indiriyor. Ama izotonik, Platt'tan daha yüksek log-kayıp veriyor (0,6209 > 0,5926). Bunun nedeni basamaklı fonksiyonun, 3.000 kalibrasyon örneğinde aşırı uyum yapması ve olasılıkları 344 değere sıkıştırmasıdır (ham modelde 59.844 farklı değer var). Üçüncüsü, en iyi mümkün ECE bile sıfır değil: gerçek olasılıklarla bile 0,0054 çıkıyor. Bu, 60.000 test örneğinde kutu başına örnek sayısının sınırlı olmasından gelen gürültüdür.

Bu tablodan bir ayrım çıkıyor. Platt dönüşümü monoton (artan) olduğu için sıralamayı korur: ROC-AUC farkı 1,8·10⁻⁹, yani sayısal gürültü düzeyinde sıfırdır. İzotonik dönüşüm ise çok sayıda eşitlik (aynı olasılığa sahip örnek) üretir; bu, sıralamayı bozar ve AUC'yi 0,0018 düşürür. Yani kalibrasyon, sıralama yeteneğini genelde korur ama her yöntem bunu aynı şekilde yapmaz.

Bu bölümün en önemli çıkarımı şudur: kalibrasyon bir "doğruluk" meselesi değildir. Aşırı güvenli modelin doğruluğu bile iyi olabilir; ama olasılığını karar sürecine (ör. "bu kareyi %90 güvenle hedef say") veriyorsan, o olasılığın anlamı kalibrasyonla korunur. Savunma ya da sağlık uygulamasında olasılık sayısını eşik olarak kullanacaksan, kalibrasyon raporunu baştan hazırlamak zorundasın.

![Şekil 57.5: Guvenilirlik diyagramlari. Solda aşırı güvenli gradyan artırma modeli (ECE 0,238): noktalar köşegenden çok uzak. Sağda Platt kalibrasyonu sonrası (ECE 0,030): noktalar köşegene yakın, ama en yüksek kutuda bozulma var. Nokta boyu kutudaki örnek sayısını gösterir.](gorseller/b57_kalibrasyon.png)

## 57.8 Regresyon metrikleri ve artık analizi

Sürekli bir hedefi tahmin ederken ölçütler farklı bir soruya cevap verir: hatanın büyüklüğü ne kadar, ve hatalar nasıl dağılıyor? **MAE** (ortalama mutlak hata) hataya doğrusal ceza verir ve yorumu en kolay olanıdır: birimi hedefle aynıdır. **MSE** ve **RMSE** büyük hataları daha sert cezalandırır; aykırı değerlere karşı hassastır. **MAPE** yüzde hatayı ölçer, ama hedef sıfıra yakınken patlar: hata sabit kalsa bile y küçüldükçe yüzde hata sınırsız büyür. **R²** = 1 − SS_res / SS_tot, modelin ortalama tahmininden ne kadar iyi olduğunu söyler. Model ortalamadan kötüyse negatif olabilir; bunu aşağıda görüyorsun.

Doğrusal bir veri üretip en küçük kareler ile katsayıları buluyoruz. Gürültünün sabit olmadığına dikkat et: standart sapma x ile arttıkça büyüyor. Bu, **heteroskedastisite** adı verilen durumdur ve artık analizinin asıl konusudur.

```python
# b57_05_regresyon.py
# Regresyon metrikleri, MAPE'nin patlamasi, negatif R2, artiklar
import numpy as np
from sklearn import metrics as M

rng = np.random.default_rng(57)

def mae(y, t):
    return np.mean(np.abs(y - t))

def mse(y, t):
    return np.mean((y - t) ** 2)

def rmse(y, t):
    return np.sqrt(mse(y, t))

def mape(y, t):
    """Yuzde ortalama mutlak hata. y = 0 ise tanimsiz."""
    return np.mean(np.abs((y - t) / y)) * 100

def r2(y, t):
    """1 - SS_res/SS_tot. Model ortalamadan kotuyse negatif olur."""
    ss_res = np.sum((y - t) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    return 1 - ss_res / ss_tot
```

Ölçütlerin tanımları doğrudan formüllerdir. `mape` içinde paydaki y'nin sıfır olması durumu tanımsızdır; bu yüzden kullanmadan önce hedefin sıfıra yakın olmadığını kontrol etmek gerekir.

```python
# ---------- 1) Dogrusal veri, heteroskedastik gurultu ----------
n = 400
x = rng.uniform(-3, 3, n)
sd = 0.2 + 0.5 * np.abs(x)              # gurultu x ile buyuyor
y = 2.0 * x + 1.0 + rng.normal(scale=sd)
X = np.c_[np.ones(n), x]
beta = np.linalg.lstsq(X, y, rcond=None)[0]   # kapali form kestirim
t = X @ beta
print("Katsayilar (sabit, egim): %.3f %.3f" % (beta[0], beta[1]))

print("MAE  %.4f" % mae(y, t))
print("MSE  %.4f" % mse(y, t))
print("RMSE %.4f" % rmse(y, t))
print("R2   %.4f" % r2(y, t))
for ad, a, b in [("MAE", mae(y, t), M.mean_absolute_error(y, t)),
                 ("MSE", mse(y, t), M.mean_squared_error(y, t)),
                 ("R2", r2(y, t), M.r2_score(y, t))]:
    assert abs(a - b) < 1e-9, ad
print("sklearn ile birebir eslesti (MAE, MSE, R2).")

# ---------- 2) MAPE: hedef sifira yakinken patlar ----------
yy = np.array([100.0, 50.0, 10.0, 1.0, 0.1, 0.01])
tt = yy + np.array([5.0, -5.0, 1.0, 0.5, 0.1, 0.05])  # ayni mutlak
print("\nHata sabit ama hedef kuculunce APE artiyor:")
for a, b in zip(yy, tt):
    print("y=%8.2f  tahmin=%8.2f  |hata|=%.3f  APE=%8.2f%%"
          % (a, b, abs(a - b), abs(a - b) / a * 100))
print("MAPE (ilk iki satir) = %.2f%%"
      % mape(yy[:2], tt[:2]))
print("MAPE (tum 6 satir)   = %.2f%%" % mape(yy, tt))
sk_mape = M.mean_absolute_percentage_error(yy, tt) * 100
assert abs(mape(yy, tt) - sk_mape) < 1e-6
```

Regresyon katsayılarını kapalı formla (`lstsq`) buluyoruz. Ardından MAE, MSE, R² ölçütlerini sklearn ile karşılaştırıyoruz. Aynı hataya iki farklı yüzde değeri veren bir MAPE tablosu da burada: hata her satırda 5 birim (ilk iki satır) ama hedef küçüldükçe yüzde hata 5%'ten 500%'e çıkıyor.

```python
# ---------- 3) Negatif R2: sabit tahmin bile kotu olabilir ----------
y_test = rng.normal(loc=0.0, scale=1.0, size=500)
y_egitim_ort = 3.0     # egitim verisinin ortalamasi 3 olsun (kayma)
sabit = np.full_like(y_test, y_egitim_ort)
print("\nSabit tahmin (egitim ortalamasi = 3), test ortalamasi = 0:")
print("R2 = %.4f" % r2(y_test, sabit))
assert abs(r2(y_test, sabit) - M.r2_score(y_test, sabit)) < 1e-9
print("R2 sabit tahmin icin ort(test) ile yapilsaydi: %.4f"
      % r2(y_test, np.full_like(y_test, y_test.mean())))

# ---------- 4) Artiklar: heteroskedastisite ----------
artik = y - t
print("\ncorr(artik, x)     = %.4f  (OLS artiklari x ile dik)"
      % np.corrcoef(artik, x)[0, 1])
print("corr(|artik|, |x|) = %.4f  (pozitif: varyans x ile artiyor)"
      % np.corrcoef(np.abs(artik), np.abs(x))[0, 1])
for lo, hi in [(-3, -1), (-1, 1), (1, 3)]:
    m = (x >= lo) & (x < hi)
    print("x in [%2d,%2d): artik sd = %.3f  (gercek sd ort = %.3f)"
          % (lo, hi, artik[m].std(), sd[m].mean()))

# ---------- 5) Kantil (pinball) kaybi ve tahmin araligi ----------
def pinball(y, t, q):
    fark = y - t
    return np.mean(np.maximum(q * fark, (q - 1) * fark))

q = 0.9
print("\nq=0.9 pinball (bizim) = %.4f  sklearn = %.4f" % (
    pinball(y, t, q), M.mean_pinball_loss(y, t, alpha=q)))
sk_pin = M.mean_pinball_loss(y, t, alpha=q)
assert abs(pinball(y, t, q) - sk_pin) < 1e-9
```

İkinci bölümde R²'nin negatif olabileceğini görüyorsun: test kümesinin ortalaması 0 iken eğitim ortalamasını (3) sabit tahmin etmek R² = −8,72 veriyor. Model ortalamayı bile tutturamadığında karesel ceza hatayı test varyansının çok üstüne çıkarır. Son bölümde artık analizi ve kantil kaybı (pinball) var. Pinball kaybı, q kantilini tahmin etmek için kullanılır; aralık tahmini bununla yapılır.

```python
# Artik kantillerinden %80'lik aralik (10. ve 90. kantil)
alt, ust = np.quantile(artik, [0.1, 0.9])
yeni_x = rng.uniform(-3, 3, 4000)
yeni_sd = 0.2 + 0.5 * np.abs(yeni_x)
yeni_y = 2.0 * yeni_x + 1.0 + rng.normal(scale=yeni_sd)
yeni_t = beta[0] + beta[1] * yeni_x
kapsama = np.mean((yeni_y >= yeni_t + alt) & (yeni_y <= yeni_t + ust))
print("Her x icin sabit aralik [%.3f, %.3f]:" % (alt, ust))
print("test kapsama orani = %.3f (hedef 0.80)" % kapsama)
print("Heteroskedastik oldugu icin x'e gore kapsama bozulur:")
for lo, hi in [(-3, -1), (-1, 1), (1, 3)]:
    m = (yeni_x >= lo) & (yeni_x < hi)
    k = np.mean((yeni_y[m] >= yeni_t[m] + alt) &
                (yeni_y[m] <= yeni_t[m] + ust))
    print("  x in [%2d,%2d): kapsama = %.3f" % (lo, hi, k))
```

```term
$ python b57_05_regresyon.py
Katsayilar (sabit, egim): 0.991 1.988
MAE  0.7432
MSE  0.9669
RMSE 0.9833
R2   0.9230
sklearn ile birebir eslesti (MAE, MSE, R2).

Hata sabit ama hedef kuculunce APE artiyor:
y=  100.00  tahmin=  105.00  |hata|=5.000  APE=    5.00%
y=   50.00  tahmin=   45.00  |hata|=5.000  APE=   10.00%
y=   10.00  tahmin=   11.00  |hata|=1.000  APE=   10.00%
y=    1.00  tahmin=    1.50  |hata|=0.500  APE=   50.00%
y=    0.10  tahmin=    0.20  |hata|=0.100  APE=  100.00%
y=    0.01  tahmin=    0.06  |hata|=0.050  APE=  500.00%
MAPE (ilk iki satir) = 7.50%
MAPE (tum 6 satir)   = 112.50%

Sabit tahmin (egitim ortalamasi = 3), test ortalamasi = 0:
R2 = -8.7183
R2 sabit tahmin icin ort(test) ile yapilsaydi: 0.0000

corr(artik, x)     = 0.0000  (OLS artiklari x ile dik)
corr(|artik|, |x|) = 0.4661  (pozitif: varyans x ile artiyor)
x in [-3,-1): artik sd = 1.114  (gercek sd ort = 1.173)
x in [-1, 1): artik sd = 0.498  (gercek sd ort = 0.457)
x in [ 1, 3): artik sd = 1.188  (gercek sd ort = 1.207)

q=0.9 pinball (bizim) = 0.3716  sklearn = 0.3716
Her x icin sabit aralik [-1.168, 1.225]:
test kapsama orani = 0.777 (hedef 0.80)
Heteroskedastik oldugu icin x'e gore kapsama bozulur:
  x in [-3,-1): kapsama = 0.674
  x in [-1, 1): kapsama = 0.978
  x in [ 1, 3): kapsama = 0.681
```

Artıkların sonucu, sabit varyans varsayımının bozulduğunu gösteriyor. OLS artıkları x ile dik olduğu için korelasyon sıfır çıkıyor (bu bir kontrol); ama |artık| ile |x| arasındaki korelasyon 0,4661: hata büyüklüğü x'in uzaklığıyla artıyor. Bin bazında artık standart sapması 1,11 ile 1,19 arasında (orta bölümde 0,50), gerçek gürültü sapmasıyla (1,17, 0,46, 1,21) uyumlu. Bunun pratik sonucu, sabit bir genişlikte tahmin aralığının bütün x'lerde aynı kapsamayı vermemesidir: %80 hedeflenen bir aralık genel olarak %77,7 kapsıyor, ama uç bölgelerde %67 ile %68'e, orta bölgede %98'e çıkıyor. Ortalama kapsamaya bakmak, bu eşitsizliği saklar. Dilim bazlı raporlama (57.12) bu yüzden zorunludur.

Pinball kaybının tanımı ile sklearn'ün `mean_pinball_loss` çıktısı aynı (0,3716). Kantil tahmini ile aralık oluştururken kantil kaybı, asimetrik bir ceza verir; q = 0,9 için üst kantilde kalmak yerine altta kalmanın cezası dokuz kat fazladır. Bu ölçütü Bölüm 78'de belirsizlik tahmini için yeniden kullanacağız.

## 57.9 Çapraz doğrulamanın derinliği

Bölüm 54'te k-katlı çapraz doğrulamayı (CV) tanıttık: veriyi k parçaya bölüp her parçayı sırayla test olarak kullandık, skoru ortalamayla özetledik. Bu bölümde onun dört derinliğe bakacağız: k'nın seçimi, tekrarlı bölme, iç içe CV ve zaman ile grup yapısı.

Önce k'nın ne yaptığını ayıralım. Ortalama skor, k arttıkça daha az yanlı olur, çünkü her eğitim kümesi tam veriye yaklaşır. Ama iki kat arasında bölme rastgeleliğine bağlı bir değişkenlik de vardır: aynı veriyi farklı bir rastgele bölmeyle tekrar değerlendirirsen skor değişir. Bu değişkenlik, tahmin edilen ortalamanın kendisinin ne kadar güvenilir olduğunu gösterir; veri örneklemine bağlı belirsizlikle karıştırılmamalıdır. Aşağıdaki program meme kanseri verisinde, 30 farklı bölme tohumu üzerinden her k için ortalama skoru ve bölmeler arası standart sapmayı hesaplıyor.

```python
# b57_06_cv_derinlik.py
# Cross-validation derinligi: k, tekrarli CV, ic ice CV, zaman serisi
import os
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (GridSearchCV, KFold, LeaveOneOut,
                                     RepeatedStratifiedKFold,
                                     StratifiedKFold, TimeSeriesSplit,
                                     cross_val_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"

# ---------- 1) k secimi: yanlilik ve tahmin degiskenligi ----------
veri = load_breast_cancer()
X, y = veri.data, veri.target
model = make_pipeline(StandardScaler(),
                      LogisticRegression(max_iter=2000))

print("k    ort skor   std (30 bolme tohumu)")
for k in [2, 5, 10, 20]:
    skorlar = []
    for sd in range(30):
        cv = StratifiedKFold(k, shuffle=True, random_state=sd)
        skorlar.append(cross_val_score(model, X, y, cv=cv).mean())
    skorlar = np.array(skorlar)
    print("%2d   %.4f     %.4f" % (k, skorlar.mean(), skorlar.std()))

# LOO: bolme rastgeleligi yok; tek bir deterministik sonuc
loo = cross_val_score(model, X, y, cv=LeaveOneOut()).mean()
print("LOO  %.4f     (deterministik, tek sonuc)" % loo)

# ---------- 2) Tekrarli CV: bolme sansini azaltmak ----------
tekrar = RepeatedStratifiedKFold(n_splits=5, n_repeats=10,
                                 random_state=57)
skor_t = cross_val_score(model, X, y, cv=tekrar)
print("\n5-kat x 10 tekrar: %d skor, ort %.4f, std %.4f"
      % (len(skor_t), skor_t.mean(), skor_t.std()))
print("10 tekrarin kendi ortalamalarinin std = %.4f"
      % (skor_t.reshape(10, 5).mean(axis=1).std()))
print("Not: tekrarlar ayni veriyi kullanir; bagimsiz ornek degildir.")
```

`cross_val_score`'a her seferinde farklı bir `StratifiedKFold` veriyoruz; `random_state` bölmeyi belirler. Leave-one-out (LOO) bölme rastgeleliği taşımaz: her örnek tek başına test edilir ve sonuç deterministiktir. Bu yüzden LOO satırında standart sapma yok.

```python
# ---------- 3) Ic ice CV: iyimserlik olcumu ----------
# Gurultu verisi: gercek sinyal yok. Dogru tahmin: ~%50.
Cgrid = {"logisticregression__C": 10.0 ** np.arange(-3, 4)}
iyimser, dogru = [], []
for sd in range(20):
    rng = np.random.default_rng(sd)
    Xg = rng.normal(size=(100, 200))
    yg = np.repeat([0, 1], 50)
    rng.shuffle(yg)
    p = make_pipeline(StandardScaler(),
                      LogisticRegression(max_iter=2000))
    dis = StratifiedKFold(5, shuffle=True, random_state=sd)
    ara = StratifiedKFold(5, shuffle=True, random_state=100 + sd)
    # Iç içe DEGIL: ayni katlarla hem C secimi hem skor
    gs = GridSearchCV(p, Cgrid, cv=dis).fit(Xg, yg)
    iyimser.append(gs.best_score_)
    # Ic ice: dis katlar hic gorulmemis test, C ic katlarda secilir
    gs2 = GridSearchCV(p, Cgrid, cv=ara)
    dogru.append(cross_val_score(gs2, Xg, yg, cv=dis).mean())
iyimser, dogru = np.array(iyimser), np.array(dogru)
print("\nGurultu verisi, 20 tohum, 13 C degeri:")
print("ic ice OLMAYAN (best_score_) ort = %.4f" % iyimser.mean())
print("ic ice (dogru)               ort = %.4f" % dogru.mean())
print("iyimserlik (fark)            ort = %.4f"
      % (iyimser - dogru).mean())
print("ilk 5 tohum (olmayan / ic ice):")
for sd in range(5):
    print("  %d   %.3f   %.3f" % (sd, iyimser[sd], dogru[sd]))
```

Tekrarlı CV (`RepeatedStratifiedKFold`) aynı 5 katlı bölmeyi 10 farklı rastgele düzenle tekrarlar. Burada dikkat edilmesi gereken nokta: 50 skor bağımsız değildir, çünkü her tekrar aynı veriyi kullanır. Tekrarların ortalamalarının kendi standart sapmasını ayrıca hesapladık: tekrarlar arasındaki gürültü azaldı, ama bu veri örneğindeki belirsizlik değişmedi.

Üçüncü bölümde iç içe CV'nin etkisini ölçüyoruz. Bu deneyde gerçek bir sinyal yok: rastgele 100 × 200 bir özellik matrisi ve rastgele etiketler. Doğru tahmin %50'dir. Lojistik regresyonun C parametresini on üç değer arasından seçiyoruz. Yöntem iki yoldan çalışıyor: ilk yolda aynı katlarla hem C'yi seçip hem de skoru raporluyoruz (`best_score_`); ikinci yolda dış katlar hiç görmediği bir test kümesi olarak kalır ve C yalnızca iç katlarla seçilir.

```python
# ---------- 4) Zaman serisi CV: gelecek gecmisi goremez ----------
t = np.arange(20)
zs = TimeSeriesSplit(n_splits=4)
print("\nTimeSeriesSplit(4) on 20 zaman adimi:")
for tr, te in zs.split(t):
    assert tr.max() < te.min()     # egitim her zaman testten once
    print("egitim %2d..%2d   test %2d..%2d" % (
        tr.min(), tr.max(), te.min(), te.max()))
print("Egitim her zaman testten once: assert gecti.")
# Karistirilmis KFold ise gelecek verisi egitime girer:
kf = KFold(4, shuffle=True, random_state=0)
gelecek_sizinti = [bool(np.any(tr > te.max()))
                   for tr, te in kf.split(t)]
print("Karistirilmis KFold'da gelecek egitime girer mi?",
      gelecek_sizinti)

# Sekil verisi: ic ice / olmayan iyimserlik
os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_ic_ice_cv.csv")
with open(yol, "w", encoding="utf-8") as f:
    f.write("tohum,ic_ice_olmayan,ic_ice\n")
    for sd in range(20):
        f.write("%d,%.5f,%.5f\n" % (sd, iyimser[sd], dogru[sd]))
print("\nIc ice CV verisi yazildi:", os.path.basename(yol))
```

```term
$ python b57_06_cv_derinlik.py
k    ort skor   std (30 bolme tohumu)
 2   0.9754     0.0045
 5   0.9785     0.0029
10   0.9788     0.0026
20   0.9792     0.0020
LOO  0.9789     (deterministik, tek sonuc)

5-kat x 10 tekrar: 50 skor, ort 0.9761, std 0.0154
10 tekrarin kendi ortalamalarinin std = 0.0032
Not: tekrarlar ayni veriyi kullanir; bagimsiz ornek degildir.

Gurultu verisi, 20 tohum, 13 C degeri:
ic ice OLMAYAN (best_score_) ort = 0.5375
ic ice (dogru)               ort = 0.5180
iyimserlik (fark)            ort = 0.0195
ilk 5 tohum (olmayan / ic ice):
  0   0.540   0.530
  1   0.510   0.470
  2   0.560   0.540
  3   0.560   0.520
  4   0.630   0.630

TimeSeriesSplit(4) on 20 zaman adimi:
egitim  0.. 3   test  4.. 7
egitim  0.. 7   test  8..11
egitim  0..11   test 12..15
egitim  0..15   test 16..19
Egitim her zaman testten once: assert gecti.
Karistirilmis KFold'da gelecek egitime girer mi? [False, True, True, True]

Ic ice CV verisi yazildi: b57_ic_ice_cv.csv
```

Çıktının ilk tablosu, k arttıkça ortalama skorun 0,9754'ten 0,9792'ye kaydığını gösteriyor: yanlılık azalıyor. Bölme varyansı ise 0,0045'ten 0,0020'ye iniyor. k = 20'de iyileşme küçüktür, buna karşılık beş yerine yirmi model eğitmek gerekir: maliyet dört kat artar. Bu yüzden pratikte k = 5 ya da 10 yaygın bir tercihtir. LOO sonucu (0,9789) k = 10'a çok yakın ve deterministiktir; ama bölme olmadığı için bölme varyansını ölçemez.

Tekrarlı CV'nin 50 skoru ortalaması 0,9761 ve standart sapması 0,0154. Tekrarların kendi ortalamalarının standart sapması ise 0,0032. İlk sayı, tek bir 5 katlı bölmenin ne kadar gürültülü olduğunu, ikincisi ise tekrarların ortalamasının ne kadar stabil olduğunu gösterir.

Asıl dikkat çekici sonuç üçüncü bölümde. Gürültü verisinde en iyi C'yi seçip o katlarda raporlayan yöntem ortalama 0,5375 veriyor; yani %50'nin üstünde. Ama dış katlar hiç görmediği bir test kümesi olarak tutulduğunda ortalama 0,5180 çıkıyor. Fark, 0,0195: seçimi ve değerlendirmeyi aynı verilerle yapmanın iyimserliği. Ortalama fark 0,0195. Yönü ise 20 tohumun 16'sında iç içe olmayan skorun yüksek olmasıyla tutarlı; üçünde iki skor eşit, birinde ters yönde. Yani yanlılık sistematik ama her tohumda aynı büyüklükte değil. Şekil 57.6, tohum başına iki skoru gösteriyor.

![Şekil 57.6: Gürültü verisinde 20 tohum için iç içe olmayan (koyu) ve iç içe (açık) CV skorları. Koyu noktalar sistematik olarak sağda; yani aynı katlarda seçim yapmak skoru yükseltiyor. Kesikli çizgi gerçek 0,5 doğruluğudur.](gorseller/b57_ic_ice_cv.png)

Zaman serisinde rastgele karıştırma açık bir sızıntıdır: gelecekteki bir örnek eğitim kümesine girebilir. Dördüncü bölümde `TimeSeriesSplit` ile genişleyen pencere kuruyoruz: her katta eğitim hep test'ten önce gelir ve eğitim kümesi katlar ilerledikçe büyür. Programda bunun her kat için `assert` ile doğrulandığını gördün. Karıştırılmış bir KFold'un ise gelecek örneklerini eğitime aldığını, dört kattan üçünde `True` çıktısıyla görüyorsun. Grup yapısı (aynı hastanın ya da uçuşun birden fazla kaydı) için `GroupKFold` kullanılır; bu, Bölüm 54.8'de sızıntı olarak ölçülmüş ve bu bölümde yeniden kullanılacak bir ilkedir.

**Ölçüm yanılgısı.** Bölme standart sapması, bir CV sonucunun "kesinliğini" değil, yalnızca bölme gürültüsünü gösterir. Aynı veriyle başka bir örnek almış olsaydın sonuç da değişirdi. Bu yüzden CV skorunu, bölme sonucunun güven aralığıyla birlikte raporla; veri belirsizliği için 57.11'deki bootstrap ve karşılaştırma testlerine dön.

## 57.10 Hiperparametre arama ve doğrulamaya aşırı uyum

Bir modelin hiperparametrelerini (C, derinlik, öğrenme oranı) seçmek, bir arama problemidir. En yaygın iki yöntem ızgara araması ve rastgele aramadır. Izgara, her boyutta eşit aralıklı değerler dener ve tüm kombinasyonları tek tek çalıştırır. Rastgele arama, her denemede her boyuttan bağımsız bir değer çeker. Bergstra ve Bengio (2012), bir problemde yalnızca birkaç boyut önemliyse rastgele aramanın ızgaradan genellikle verimli olduğunu savunur (genel bilgi).

Bu iddiayı küçük bir simülasyonla sınıyoruz. Amaç fonksiyonu g(x, y) = −(x − 0,3)² − 0,05 (y − 0,6)² olsun: x önemli, y neredeyse önemsiz. Bütçe 9 deneme. Izgara, 3 × 3 noktayı kullanır; yani önemli boyut x yalnızca üç farklı değer alır. Rastgele arama ise 9 farklı x değeri dener. 2.000 tekrar üzerinden en iyi değerin optimumdan farkını ölçüyoruz.

```python
# b57_07_arama.py
# Izgara vs rastgele arama; dogrulamaya asiri uyum (secim yanliligi)
import os
import numpy as np

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"

# ---------- 1) Izgara mi, rastgele mi? ----------
# Amac: g(x, y) = -(x - 0.3)^2 - 0.05 (y - 0.6)^2. Yalnizca x onemli
# (sekil: boyut x etkili, boyut y az etkili). Butce: 9 deneme.
def g(x, y):
    return -(x - 0.3) ** 2 - 0.05 * (y - 0.6) ** 2

OPT = g(0.3, 0.6)                      # = 0 (en iyi deger)
rng = np.random.default_rng(57)
tekrar = 2000
izgara_pay = np.linspace(0, 1, 3)      # 3 x 3 = 9 nokta
izgara_x, izgara_y = np.meshgrid(izgara_pay, izgara_pay)
izgara_en = g(izgara_x, izgara_y).max()
izgara_ptk = []
rastgele_ptk = []
for _ in range(tekrar):
    # Izgara: sabit, her tekrarda ayni (deterministik)
    izgara_ptk.append(OPT - izgara_en)
    # Rastgele: 9 bagimsiz uniform nokta
    xr, yr = rng.uniform(size=9), rng.uniform(size=9)
    rastgele_ptk.append(OPT - g(xr, yr).max())
izgara_ptk = np.array(izgara_ptk)
rastgele_ptk = np.array(rastgele_ptk)
print("Butce = 9 deneme; ptk = en iyiden fark (kucuk iyi)")
print("Izgara (3x3): ptk = %.5f" % izgara_ptk.mean())
print("Rastgele (9) : ort ptk = %.5f, medyan = %.5f"
      % (rastgele_ptk.mean(), np.median(rastgele_ptk)))
print("Rastgele daha iyi olma orani: %.3f"
      % np.mean(rastgele_ptk < izgara_ptk[0]))
# Ayni 9 noktada onemli boyuttaki ayri deger sayisi
print("Izgarada x icin ayri deger: %d, rastgelede: 9"
      % len(np.unique(izgara_x)))
```

Simülasyonda ızgara sabittir; ama rastgele arama her tekrarda yeni noktalar çeker. Bu yüzden ortalama fark hesabı tekrarlarla yapılır. `g` fonksiyonunun maksimumu 0 olduğu için fark (ptk) doğrudan en iyi değerden uzaklığı verir.

```python
# ---------- 2) Dogrulamaya asiri uyum: secim yanliligi ----------
# Tum M konfigurasyonun GERCEK skoru 0.5 (hicbiri ise yaramiyor).
# Gozlenen dogrulama skoru: 0.5 + gurultu, n_val = 200 ornek.
n_val = 200
s = np.sqrt(0.5 * 0.5 / n_val)   # ikili dogruluk std hatasi
n_test = 2000
s_test = np.sqrt(0.5 * 0.5 / n_test)
print("\nGercek skor 0.5. Dogrulama std = %.4f" % s)
print("M     secilen dogrulama skoru   secilenin test skoru")
satirlar = []
for M in [1, 10, 100, 1000]:
    sec_val, sec_test = [], []
    for _ in range(1000):
        val = 0.5 + rng.normal(scale=s, size=M)
        i = np.argmax(val)                     # en iyi dogrulama
        sec_val.append(val[i])
        # bagimsiz test kumesi
        sec_test.append(0.5 + rng.normal(scale=s_test))
    print("%4d  %.4f                    %.4f"
          % (M, np.mean(sec_val), np.mean(sec_test)))
    satirlar.append((M, np.mean(sec_val), np.mean(sec_test)))

# Teorik kontrol: M normalin maksimumunun beklenen degeri (yaklasik)
# M=10: ~1.54 std; M=100: ~2.51 std; M=1000: ~3.24 std
print("beklenen sapma (std cinsinden) M=10: 1.54, M=100: 2.51")

# ---------- 3) Ornek: tek bir deneme ile bir cok deneme ----------
bir = 0.5 + rng.normal(scale=s)
print("\nTek deneme dogrulama skoru: %.4f" % bir)
print("1000 denemede en iyi (dogrulama): %.4f"
      % (0.5 + rng.normal(scale=s, size=1000).max()))
```

İkinci bölüm, doğrulamaya aşırı uyumu simüle ediyor. Diyelim ki 10, 100 ya da 1000 farklı konfigürasyon denedin ve hepsinin gerçek skoru 0,5 (hiçbiri gerçekten yardımcı olmuyor). Her birinin gözlenen doğrulama skoru 200 örneklik bir doğrulama kümesinde gürültülüdür (standart sapma 0,0354). En iyi doğrulama skorunu seçersen, seçtiğin değer gürültünün en yüksek ucudur. Bağımsız bir test kümesinde ise hep 0,5 çıkar. Seçim yanlılığının büyüklüğü, denenen sayısı M ile büyür.

```python
os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_asiri_uyum.csv")
with open(yol, "w", encoding="utf-8") as f:
    f.write("M,secilen_dogrulama,secilen_test\n")
    for M, v, t in satirlar:
        f.write("%d,%.5f,%.5f\n" % (M, v, t))
print("Asiri uyum verisi yazildi:", os.path.basename(yol))

# Sekil verisi: 9 izgara ve 9 rastgele nokta (ayri tohum, tek deneme)
_r2 = np.random.default_rng(7)
_xr, _yr = _r2.uniform(size=9), _r2.uniform(size=9)
with open(os.path.join(VERI, "b57_arama_noktalar.csv"), "w",
          encoding="utf-8") as _f:
    _f.write("yontem,x,y\n")
    for _a, _b in zip(izgara_x.ravel(), izgara_y.ravel()):
        _f.write("izgara,%.5f,%.5f\n" % (_a, _b))
    for _a, _b in zip(_xr, _yr):
        _f.write("rastgele,%.5f,%.5f\n" % (_a, _b))
```

```term
$ python b57_07_arama.py
Butce = 9 deneme; ptk = en iyiden fark (kucuk iyi)
Izgara (3x3): ptk = 0.04050
Rastgele (9) : ort ptk = 0.00810, medyan = 0.00549
Rastgele daha iyi olma orani: 0.988
Izgarada x icin ayri deger: 3, rastgelede: 9

Gercek skor 0.5. Dogrulama std = 0.0354
M     secilen dogrulama skoru   secilenin test skoru
   1  0.4989                    0.4996
  10  0.5550                    0.4999
 100  0.5885                    0.5000
1000  0.6145                    0.5003
beklenen sapma (std cinsinden) M=10: 1.54, M=100: 2.51

Tek deneme dogrulama skoru: 0.4892
1000 denemede en iyi (dogrulama): 0.6179
Asiri uyum verisi yazildi: b57_asiri_uyum.csv
```

Izgara ile rastgele arama arasındaki fark çarpıcı: ızgaranın ortalama farkı 0,0405, rastgele aramanınki 0,0081. Rastgele arama, 9 denemede ızgaradan daha iyi bir nokta bulma olasılığı %98,8. Sebebi, önemli boyutta 9 farklı değer denemesi; ızgara ise yalnızca üç. Şekil 57.7, aynı fonksiyonda iki yöntemin noktalarını gösteriyor: ızgara sütunları önemli boyutu kaba örnekliyor, rastgele noktalar ise dağılmış.

![Şekil 57.7: g(x, y) fonksiyonunun eş yükseklik eğrileri. Kare noktalar 3 × 3 ızgara, daireler 9 rastgele deneme, yıldız en iyi noktadır. Önemli boyut x'te ızgara yalnızca üç değer deniyor.](gorseller/b57_arama_noktalari.png)

Aşırı uyum sonucu daha da çarpıcı. Gerçek skor 0,5 iken seçilen doğrulama skoru M = 10'da 0,555'e, M = 100'de 0,589'a, M = 1000'de 0,615'e çıkıyor. Test skoru ise 0,500 civarında kalıyor. Bu, daha çok deneme yapmanın bir kazanç değil, yalnızca doğrulama kümesine özgü gürültüye uyum olduğunu gösteriyor. Beklenen maksimum, bağımsız normal değerlerin maksimumu gibi davranır: M = 10 için yaklaşık 1,54 standart sapma, M = 100 için 2,51, M = 1000 için 3,24 (genel bilgi). Şekil 57.8 bu eğriyi gösteriyor.

![Şekil 57.8: Denenen konfigürasyon sayısı arttıkça seçilen en iyi doğrulama skoru (kırmızı) yükseliyor, oysa bağımsız test skoru (mavi) gerçek 0,5 değerinde kalıyor.](gorseller/b57_asiri_uyum.png)

Bu sonuçtan üç pratik kural çıkıyor. Birincisi: hiperparametre aramasını doğrulama kümesinde ya da iç CV'de yap, test kümesinde değil. İkincisi: deneme sayısını ve arama uzayını raporla; M = 1000 ile elde edilen 0,615 ile M = 1 ile elde edilen 0,499 aynı şey değildir. Üçüncüsü: son değerlendirmeyi, seçim sürecine hiç dokunmamış bir test kümesinde bir kez yap. Eğitim sırasında doğrulama kaybını izleyip en iyi noktada durmak (erken durdurma; eğitim ayrıntıları Bölüm 64'te) da aynı yanlılığa maruz kalır, çünkü o noktayı doğrulama kümesinde seçiyorsun.

## 57.11 Modelleri karşılaştırmak: anlamlı mı, yoksa şans mı?

İki model arasındaki fark iki sayının farkıdır; ama o farkın gerçek mi yoksa örnekleme şansı mı olduğu ayrı bir sorudur. Bölüm 49'da bootstrap, permütasyon testi ve p-değerini gördün. Burada bunları sınıflandırıcılara uyguluyoruz ve üç yaklaşımı karşılaştırıyoruz.

**Eşleştirilmiş ikili sonuçlar için McNemar testi.** İki model aynı test örneklerinde tahmin yapıyorsa, sonuçlar bağımsız değildir; bu yüzden iki bağımsız oran testi yanlıştır. Her örnek için dört durum olur: ikisi de doğru (a), yalnızca birincisi doğru (b), yalnızca ikincisi doğru (c), ikisi de yanlış (d). Yalnızca b ve c fark bilgisi taşır. H₀: b = c. b + c küçükse tam (exact) binom testi kullanılır: X ~ Bin(b + c, 1/2), iki yönlü p = 2·P(X ≤ min(b, c)). Büyük örneklemde süreklilik düzeltmeli ki-kare yaklaşımı da kullanılır: χ² = (|b − c| − 1)² / (b + c).

**Bootstrap farkı.** Test örneklerini yerine koyarak yeniden örnekleyip her seferinde iki modelin doğruluk farkını hesaplarsın; yüzdelik %2,5 ve %97,5 güven aralığı verir. Eşleştirme korunur: aynı örnek iki modelde birlikte seçilir.

**5 × 2 çapraz doğrulama t testi.** Veriyi iki katlı 5 kez bölersin; her bölmede iki modelin hata farkını alırsın ve bu 10 farktan bir t istatistiği üretirsin (Dietterich, 1998; genel bilgi). Test için 5 serbestlik derecesi kullanılır. Katların bağımsız olmadığı için bu test yaklaşıktır; yine de eğitim verisinin değişkenliğini de hesaba kattığı için tek bir test kümesi McNemar'dan daha bilgilendiricidir.

```python
# b57_08_karsilastirma.py
# Iki model farkli mi? McNemar (sifirdan), bootstrap, 5x2 CV
import math
import numpy as np
from sklearn import metrics as M
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (StratifiedKFold,
                                     train_test_split)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

def mcnemar(dogru1, dogru2):
    """Eslestirilmis ikili sonuclar. b: 1 dogru, 2 yanlis; c tersi."""
    b = int(np.sum(dogru1 & ~dogru2))
    c = int(np.sum(~dogru1 & dogru2))
    n = b + c
    if n == 0:
        return b, c, 0.0, 1.0
    chi2 = (abs(b - c) - 1) ** 2 / n          # sureklilik duzeltmeli
    p_ki = math.erfc(math.sqrt(chi2 / 2))     # 1 serbestlik derecesi
    # Tam (exact) iki yonlu binom p-degeri: Bin(n, 1/2)
    alt = sum(math.comb(n, k) for k in range(min(b, c) + 1))
    p_tam = min(1.0, 2 * alt / 2 ** n)
    return b, c, chi2, p_ki, p_tam

def bootstrap_fark(d1, d2, B=2000, seed=57):
    """Test ornekleri yeniden orneklenerek fark icin %95 GA."""
    rng = np.random.default_rng(seed)
    n = len(d1)
    fark = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        fark.append(d1[i].mean() - d2[i].mean())
    return np.percentile(fark, [2.5, 97.5])
```

`mcnemar` fonksiyonu b ve c'yi sayar, süreklilik düzeltmeli ki-kare ve tam binom p değerlerini döndürür. Tam p, `math.comb` ile sayılan binom toplamıdır; sonucu scipy'nin `binomtest` ile de doğruluyoruz. Bootstrap, aynı indeksleri iki modele birlikte uygular.

```python
veri = load_breast_cancer()
y = (veri.target == 0).astype(int)
X_tr, X_te, y_tr, y_te = train_test_split(
    veri.data, y, test_size=0.3, stratify=y, random_state=57)

m1 = make_pipeline(StandardScaler(),
                    LogisticRegression(max_iter=2000))
m2 = DecisionTreeClassifier(max_depth=3, random_state=57)
m1.fit(X_tr, y_tr)
m2.fit(X_tr, y_tr)
t1, t2 = m1.predict(X_te), m2.predict(X_te)
d1, d2 = (t1 == y_te), (t2 == y_te)
print("Test ornegi: %d" % len(y_te))
print("Model 1 (lojistik) dogruluk: %.4f" % d1.mean())
print("Model 2 (agac, derinlik 3) dogruluk: %.4f" % d2.mean())

# ---------- McNemar ----------
b, c, chi2, p_ki, p_tam = mcnemar(d1, d2)
print("\nMcNemar: b = %d (1 dogru, 2 yanlis), c = %d" % (b, c))
print("chi2 (sureklilik duzeltmeli) = %.4f, p = %.4f" % (chi2, p_ki))
print("Tam binom p = %.4f" % p_tam)
# Kontrol: scipy (sklearn'in bagimliligi) ile ayni binom p-degeri
from scipy.stats import binomtest
p_sc = binomtest(min(b, c), b + c, 0.5,
                  alternative="two-sided").pvalue
print("scipy binomtest p = %.4f (cross-check)" % p_sc)
assert abs(p_sc - p_tam) < 1e-9
# Yonelim tablosu (karisiklik)
print("\nTablo: model1/model2 (dogru,yanlis):")
print("dogru-dogru %d  dogru-yanlis %d" % (np.sum(d1 & d2), b))
print("yanlis-dogru %d  yanlis-yanlis %d"
      % (c, np.sum(~d1 & ~d2)))

# ---------- Bootstrap farki ----------
lo, hi = bootstrap_fark(d1.astype(float), d2.astype(float))
print("\nDogruluk farki (1-2) = %.4f" % (d1.mean() - d2.mean()))
print("Bootstrap %%95 GA (eslestirilmis yeniden ornekleme): "
      "[%.4f, %.4f]" % (lo, hi))
```

Program meme kanseri verisinde lojistik regresyonu (doğruluk %95,9) bir derinlik 3 karar ağacıyla (doğruluk %92,4) karşılaştırıyor. 5 × 2 bölümünde her bölme katmanlıdır; bu, sınıf oranlarının her katta korunmasını sağlar (Bölüm 54.7).

```python
# ---------- 5x2 CV t-testi (Dietterich 1998) ----------
# 5 tekrar x 2 kat. Her tekrarda iki modelin hata farki.
farklar = []
varyanslar = []
for tekrar in range(5):
    kat = StratifiedKFold(2, shuffle=True, random_state=tekrar)
    p = []
    for tr, te in kat.split(veri.data, y):
        a = make_pipeline(StandardScaler(),
                          LogisticRegression(max_iter=2000)).fit(
            veri.data[tr], y[tr])
        bb = DecisionTreeClassifier(max_depth=3, random_state=57).fit(
            veri.data[tr], y[tr])
        hata_a = np.mean(a.predict(veri.data[te]) != y[te])
        hata_b = np.mean(bb.predict(veri.data[te]) != y[te])
        p.append(hata_a - hata_b)
    p = np.array(p)
    ort = p.mean()
    varyanslar.append((p[0] - ort) ** 2 + (p[1] - ort) ** 2)
    farklar.append(p[0])
t_stat = farklar[0] / math.sqrt(np.mean(varyanslar))
print("\n5x2 CV: t = %.4f (serbestlik 5)" % t_stat)
print("Kritik deger (iki yonlu, %5, df=5) = 2.571")
print("Karar:", "fark anlamli" if abs(t_stat) > 2.571
      else "fark anlamli degil (bu veride)")
print("Not: 5x2 CV katlari bagimsiz degil; t-testi bu yuzden")
print("yaklasik. Ayrintilarini kaynaktan okuyun (Dietterich 1998).")
```

```term
$ python b57_08_karsilastirma.py
Test ornegi: 171
Model 1 (lojistik) dogruluk: 0.9591
Model 2 (agac, derinlik 3) dogruluk: 0.9240

McNemar: b = 9 (1 dogru, 2 yanlis), c = 3
chi2 (sureklilik duzeltmeli) = 2.0833, p = 0.1489
Tam binom p = 0.1460
scipy binomtest p = 0.1460 (cross-check)

Tablo: model1/model2 (dogru,yanlis):
dogru-dogru 155  dogru-yanlis 9
yanlis-dogru 3  yanlis-yanlis 4

Dogruluk farki (1-2) = 0.0351
Bootstrap %95 GA (eslestirilmis yeniden ornekleme): [0.0000, 0.0760]

5x2 CV: t = -4.6936 (serbestlik 5)
Kritik deger (iki yonlu, %5, df=5) = 2.571
Karar: fark anlamli
Not: 5x2 CV katlari bagimsiz degil; t-testi bu yuzden
yaklasik. Ayrintilarini kaynaktan okuyun (Dietterich 1998).
```

Çıktıda iki test çelişiyor gibi görünüyor: McNemar p = 0,146 (anlamlı değil), 5 × 2 t testi ise |t| = 4,69 > 2,571 (kritik değer, df = 5, %5 iki yönlü) ile anlamlı. Bu bir hata değil, iki farklı soruya verilen iki cevaptır. McNemar, bu tek test kümesindeki 171 örnekte iki modelin ne kadar farklı davrandığını sorar; uyumsuz çift sayısı yalnızca 12'dir (9 + 3), dolayısıyla gücü düşüktür. 5 × 2 testi ise veri setinden yapılan yarı boyutlu eğitimlerin on farkına bakar; yani "bu algoritma ailesi bu veride tutarlı olarak farklı mı?" sorusunu sorar. Hangi soruyu sorduğunu bilmeden sonuç yorumlanamaz.

Bootstrap güven aralığı [0,0000; 0,0760] (fark 0,0351): alt sınır sıfırda, bu da McNemar'ın "anlamlı değil" sonucuyla uyumlu. Yani tek test kümesinde fark, bir tarafta yakın sıfıra kadar uzanıyor. Burada raporlanacak doğru cümle şudur: "lojistik regresyon, bu test kümesinde ağaca göre %3,5 daha doğru; güven aralığı [0,0, 7,6] puan; fark kesin değil." Bu cümle, tek bir p-değerinden daha fazla bilgi taşır.

**Çoklu karşılaştırma.** Yirmi ayrı karşılaştırma yapıp her birinde %5 anlamlılık düzeyi kullanırsan, en az bir yanlış "anlamlı" bulgu olasılığı 1 − 0,95²⁰ ≈ 0,64'tür. Bölüm 49.10'daki bakıp durdurma ve çoklu karşılaştırma tuzağı burada da geçerlidir. Bonferroni düzeltmesi (her test için α/m) bu olasılığı kontrol altında tutar; ama fazla muhafazakârdır. Bir sürü model arasından "en iyisini" seçtiysen, seçilen modelin skorunu seçilmemiş bir kümede yeniden raporlamalısın (57.10'daki aşırı uyum deneyi bunu gösterir).

**Etki büyüklüğü.** İstatistiksel anlamlılık, farkın büyüklüğünü söylemez. 3,5 puanlık bir doğruluk farkı, bir İHA tespit sisteminde ya çok büyük ya da önemsiz olabilir; bu, hata maliyetine (57.1) bağlıdır. Fark ile birlikte güven aralığını ve maliyet tablosunu raporla.

## 57.12 Öğrenme eğrileri ve hata analizi: model neden başarısız?

Bir modelin skorunu okumak yetmez; neden o skoru verdiğini de anlaman gerekir. Bunun iki aracı var. Birincisi **öğrenme eğrisi**: eğitim boyutu arttıkça eğitim ve doğrulama performansının nasıl değiştiğini gösterir. İkincisi **hata analizi**: hataların hangi sınıflarda, hangi koşullarda ve hangi örneklerde toplandığını inceler.

Öğrenme eğrisinin okunması, Bölüm 54.6'daki sapma–varyans ayrımına doğrudan bağlanır. İki eğri de düşük ve birbirine yakınsa model yetersizdir (yüksek sapma): daha fazla veri çok az yardım eder, model ya da öznitelikler değişmelidir. Eğitim eğrisi yüksek, doğrulama eğrisi düşükse ve aralık büyükse model ezberliyordur (yüksek varyans): daha fazla veri, düzenlileştirme ya da daha basit bir model yardım eder. İkisi de yüksek ve aralık küçükse model dengelidir ve son ayarlara geçilebilir.

Aşağıdaki program rakam verisinde üç farklı modeli eğitim boyutuna göre ölçüyor. Birincisi C = 10⁻⁴ ile aşırı düzenlenmiş bir lojistik regresyon (yüksek sapma), ikincisi sınırsız derinlikte bir karar ağacı (yüksek varyans), üçüncüsü C = 0,1 ile dengeli bir lojistik regresyon. Her eğitim boyutu için 5 katlı katmanlı CV kullanılıyor.

```python
# b57_10_tani_dilim.py
# Ogrenme egrisi tanisi (sapma/varyans) ve dilim bazli hata analizi
import os
import numpy as np
from sklearn import metrics as M
from sklearn.datasets import load_breast_cancer, load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (StratifiedKFold, learning_curve,
                                     train_test_split)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"

# ---------- 1) Ogrenme egrisi: uc tani ----------
d = load_digits()
X, y = d.data, d.target
cv = StratifiedKFold(5, shuffle=True, random_state=57)
boyutlar = np.linspace(0.1, 1.0, 6)
modeller = [
    ("yuksek sapma", make_pipeline(
        StandardScaler(), LogisticRegression(C=1e-4, max_iter=2000))),
    ("yuksek varyans", DecisionTreeClassifier(random_state=57)),
    ("dengeli", make_pipeline(
        StandardScaler(), LogisticRegression(C=0.1, max_iter=2000))),
]
satirlar = []
for ad, m in modeller:
    n_tr, tr_skor, va_skor = learning_curve(
        m, X, y, cv=cv, train_sizes=boyutlar, scoring="accuracy")
    print("\n%s" % ad)
    print("  n_egitim  egitim   dogrulama  (std)")
    for n_i, a, b in zip(n_tr, tr_skor.mean(1), va_skor.mean(1)):
        s = va_skor[list(n_tr).index(n_i)].std()
        print("  %6d    %.3f    %.3f      %.3f" % (n_i, a, b, s))
        satirlar.append((ad, n_i, a, b, s))
    print("  son boy: egitim-dogrulama farki = %.3f"
          % (tr_skor[-1].mean() - va_skor[-1].mean()))
```

`learning_curve`, her eğitim boyutu için CV'yi tekrarlar ve eğitim ile doğrulama skorlarını matris olarak döndürür; ortalama ve standart sapma buradan alınır. Son satırda 1-NN ile 200 örnekte eğitim skorunun 1,000 çıkması, ezberlemenin en uç biçimidir: her eğitim örneği kendi en yakın komşusu olarak kendini bulur.

```python
# Yuksek varyans: 1-NN, cok az veriyle ezber
X_s, _, y_s, _ = train_test_split(X, y, train_size=200,
                                  stratify=y, random_state=57)
knn = KNeighborsClassifier(n_neighbors=1)
print("\n1-NN, 200 ornek: egitim = %.3f"
      % knn.fit(X_s, y_s).score(X_s, y_s))

# ---------- 2) Dilim bazli hata analizi ----------
v = load_breast_cancer()
yb = (v.target == 0).astype(int)     # 1 = kotu huylu (pozitif)
Xb_tr, Xb_te, yb_tr, yb_te = train_test_split(
    v.data, yb, test_size=0.3, stratify=yb, random_state=57)
mb = make_pipeline(StandardScaler(),
                   LogisticRegression(max_iter=2000))
mb.fit(Xb_tr, yb_tr)
tb = mb.predict(Xb_te)
print("\nGenel: dogruluk %.4f, duyarlilik %.4f"
      % (M.accuracy_score(yb_te, tb), M.recall_score(yb_te, tb)))

# Dilim: "mean radius" (ozellik 0) ceyreklerine gore
r = Xb_te[:, 0]
kenar = np.quantile(r, [0.25, 0.5, 0.75])
dilim = np.digitize(r, kenar)
print("\nDilim (mean radius ceyreklerine gore) - test:")
print("dilim  sinir-aralik          n   dogruluk  "
      "duyarlilik  pozitif")
for k in range(4):
    m = dilim == k
    if k == 0:
        aralik = "< %.2f" % kenar[0]
    elif k == 3:
        aralik = ">= %.2f" % kenar[2]
    else:
        aralik = "[%.2f, %.2f)" % (kenar[k - 1], kenar[k])
    print("%d     %-18s %4d   %.4f     %.4f      %3d" % (
        k, aralik, m.sum(), M.accuracy_score(yb_te[m], tb[m]),
        M.recall_score(yb_te[m], tb[m], zero_division=0),
        yb_te[m].sum()))
```

Dilim bazlı hata analizi için meme kanseri verisinde test kümesini "mean radius" özniteliğinin dört çeyreğine böldük. Her dilimde örnek sayısı, dogruluk, duyarlılık ve gerçek pozitif sayısını hesaplıyoruz. En kötü dilimin karmaşıklık matrisini de yazdırıyoruz; böylece hangi hataların yapıldığını görebilirsin.

```python
# Ortalama tek basina yaniltir: en kotu dilimin karisikligi
en_kotu = min(range(4), key=lambda k: M.recall_score(
    yb_te[dilim == k], tb[dilim == k], zero_division=0))
m = dilim == en_kotu
print("\nEn kotu dilim: %d. Karisiklik (satir=gercek, sutun=tahmin):"
      % en_kotu)
print(M.confusion_matrix(yb_te[m], tb[m], labels=[0, 1]))

# En guvenli yanlislar: pozitif iken dusuk olasilik verilenler
p_pos = mb.predict_proba(Xb_te)[:, 1]
kacan = np.where((yb_te == 1) & (tb == 0))[0]
kacan = kacan[np.argsort(p_pos[kacan])][:3]
print("\nKacan 3 pozitif (en dusuk olasilik): p =",
      np.round(p_pos[kacan], 3))

# ---------- Sekil verisi ----------
os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_ogrenme_egrisi.csv")
with open(yol, "w", encoding="utf-8") as f:
    f.write("model,n_egitim,egitim,dogrulama,std\n")
    for ad, n_i, a, b, s in satirlar:
        f.write("%s,%d,%.5f,%.5f,%.5f\n" % (ad, n_i, a, b, s))
print("\nOgrenme egrisi verisi yazildi:", os.path.basename(yol))
```

```term
$ python b57_10_tani_dilim.py
yuksek sapma
  n_egitim  egitim   dogrulama  (std)
     143    0.171    0.137      0.034
     402    0.565    0.497      0.061
     661    0.712    0.666      0.033
     919    0.810    0.779      0.038
    1178    0.846    0.821      0.035
    1437    0.849    0.839      0.015
  son boy: egitim-dogrulama farki = 0.010

yuksek varyans
  n_egitim  egitim   dogrulama  (std)
     143    1.000    0.553      0.025
     402    1.000    0.701      0.037
     661    1.000    0.782      0.020
     919    1.000    0.791      0.011
    1178    1.000    0.846      0.024
    1437    1.000    0.851      0.008
  son boy: egitim-dogrulama farki = 0.149

dengeli
  n_egitim  egitim   dogrulama  (std)
     143    0.994    0.790      0.011
     402    0.993    0.915      0.014
     661    0.994    0.946      0.004
     919    0.993    0.955      0.008
    1178    0.992    0.958      0.011
    1437    0.989    0.965      0.011
  son boy: egitim-dogrulama farki = 0.023
```
```term
1-NN, 200 ornek: egitim = 1.000

Genel: dogruluk 0.9591, duyarlilik 0.9375

Dilim (mean radius ceyreklerine gore) - test:
dilim  sinir-aralik          n   dogruluk  duyarlilik  pozitif
0     < 11.82              43   0.9535     0.0000        2
1     [11.82, 13.43)       42   0.9762     0.8000        5
2     [13.43, 15.75)       43   0.9302     1.0000       16
3     >= 15.75             43   0.9767     0.9756       41

En kotu dilim: 0. Karisiklik (satir=gercek, sutun=tahmin):
[[41  0]
 [ 2  0]]

Kacan 3 pozitif (en dusuk olasilik): p = [0.001 0.085 0.284]

Ogrenme egrisi verisi yazildi: b57_ogrenme_egrisi.csv
```

Öğrenme eğrisi tablosu üç davranışı açıkça gösteriyor. C = 10⁻⁴ modelinde eğitim ve doğrulama skorları 1437 örnekte 0,849 ve 0,839: aradaki fark 0,010, iki eğri de düşük ve yakın. Yani bu model veriyi yeterince öğrenemiyor; veriyi çoğaltmak yerine modeli değiştirmek gerekir. Karar ağacında ise eğitim skoru her boyutta 1,000 ve son boyutta bile doğrulama 0,851; aralık 0,149. Bu klasik yüksek varyanstır. Dengeli modelde eğitim 0,989, doğrulama 0,965; aralık 0,023. Burada dikkat edilmesi gereken: dengeli modelin doğrulama eğrisi hâlâ yükseliyor (0,915'ten 0,965'e), yani daha fazla veri biraz daha yardımcı olabilir.

![Şekil 57.9: Üç modelin öğrenme eğrileri. Üstte soldan: yüksek sapma (iki eğri düşük ve yakın), yüksek varyans (aralık büyük). Altta: dengeli model. Gölgeli bant doğrulama skorunun standart sapmasını gösterir.](gorseller/b57_ogrenme_egrisi.png)

Hata analizinin çıktısı, genel ortalamanın neyi sakladığını gösteriyor. Test genelinde doğruluk %95,9 ve duyarlılık %93,8. Ama "mean radius" çeyreklerine bakınca tablo değişiyor. En düşük çeyrekte (43 örnek) yalnızca iki kötü huylu tümör var ve model ikisini de kaçırıyor: duyarlılık 0,000. İki pozitifle bu sonuç çok gürültülüdür: tek bir örneğin değişmesi duyarlılığı %0'dan %50'ye taşıyabilir. Bu yüzden dilim raporlarında her zaman pozitif sayısını (n_pozitif) ve belirsizliği birlikte vermelisin. Yüksek çeyrekte (41 pozitif) duyarlılık 0,976.

En kötü dilimin karmaşıklık matrisi [[41, 0], [2, 0]] şeklinde: iki gerçek pozitif de negatif tahmin edilmiş, hiçbir yanlış alarm yok. Model bu dilimde ihtiyatlı davranıyor; ama kaçırdığı iki örnek tam da tehlikeli olanlar. Kaçan pozitiflerin olasılıkları 0,001, 0,085 ve 0,284. Bu üç örneği incelemek, modelin hangi öznitelik kombinasyonlarında körleştiğine dair bir ipucu verir. Hata analizi bu yüzden sayılardan başlar ama örneklere bakarak biter.

Dilim analizinin adalet ve kayma ile bağı açık: bir dilim "kötü performans gösteriyorsa" bu, belirli bir kullanıcı grubunun, sensörün ya da koşulun modelden kötü faydalandığı anlamına gelebilir. Bu konu Bölüm 78'de güvenilirlik ve adalet başlığında yeniden ele alınacak.

## 57.13 Çevrimiçi değerlendirme, A/B testi ve raporlama

Çevrimdışı ölçütler (test kümesi üzerinde AUC, F1) bir modelin tarihsel veride ne kadar iyi olduğunu söyler. Ama iş hedefi çoğu zaman başka bir şeydir: bir dönüşüm oranı, bir operatörün tepki süresi, günde yapılan gereksiz müdahale sayısı. Çevrimdışı bir artış, bu iş metriğinde karşılık bulmayabilir; çünkü test verisi üretimdeki dağılımı tam temsil etmez ve model kararları insanların tepkisini değiştirir. Bu nedenle yeni bir modeli üretime alırken üç aşamadan geçmek yaygındır.

İlk aşama **gölge dağıtım**dır (shadow): yeni model canlı girdiyi alır, tahmin üretir ama kararı yalnızca kaydeder; mevcut sistem kararını vermeye devam eder. Bu aşamada gecikme, bellek ve hata oranı gibi mühendislik ölçütleri ölçülür (Bölüm 42'deki dağıtım pratikleri). İkinci aşama **kanarya**dır: trafiğin küçük bir yüzdesi yeni modele yönlendirilir ve sonuçlar izlenir. Üçüncü aşama **A/B testi**dir: kullanıcılar ya da olaylar rastgele iki gruba ayrılır, biri eski modeli, biri yeni modeli görür.

A/B testinin gücü, Bölüm 49.10'da gördüğün örneklem büyüklüğü formülüyle hesaplanır. Dönüşüm oranı %10'dan %12'ye çıkan bir değişikliği α = 0,05 ve güç %80 ile yakalamak için grup başına yaklaşık 3841 örnek gerekir. Aşağıdaki programda bu sayıyı yeniden hesaplıyoruz ve asıl tehlikeye bakıyoruz: **erken bakma** (peeking). Eğer testi her gün kontrol edip p-değeri 0,05'in altına inince durdurursan, gerçek bir etki olmadığında bile yanlış pozitif oranı artar. Program bunu bir A/A testinde (iki grubun gerçekte aynı olduğu durumda) simüle ediyor: 10.000 örnek, 100 bakış noktası ve 4000 tekrar.

```python
# b57_09_ab_erken_bakma.py
# A/B testinde erken bakma (peeking): yanlis pozitif
import os
import numpy as np

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"

# ---------- Orneklem buyuklugu formulu (Bolum 49) ----------
p1, p2 = 0.10, 0.12
za, zb = 1.96, 0.8416
pbar = (p1 + p2) / 2
n_grup = ((za * np.sqrt(2 * pbar * (1 - pbar))
           + zb * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))
          / (p2 - p1)) ** 2
print("Grup basina n = %.1f  (yukari yuvarla: %d)"
      % (n_grup, int(np.ceil(n_grup))))

# ---------- Erken bakma simulasyonu: gercek fark YOK ----------
# A ve B ayni oranli (p = 0.10). Toplam N = 10000 ornek / grup.
# Her chunk 100 ornek; 100 chunk = 100 "bakis" noktasi araligi.
rng = np.random.default_rng(57)
N, p = 10000, 0.10
chunk_n = 100
chunks = N // chunk_n                 # 100 bakis araligi
tekrar = 4000
alpha_z = 1.959964                    # iki yonlu, alfa = 0.05

# Her tekrar icin her chunk'taki basari sayisi (A ve B)
basari_a = rng.binomial(chunk_n, p, size=(tekrar, chunks))
basari_b = rng.binomial(chunk_n, p, size=(tekrar, chunks))
kum_a = np.cumsum(basari_a, axis=1)
kum_b = np.cumsum(basari_b, axis=1)
```

Formül doğrudan Bölüm 49'daki ifadenin uygulamasıdır: z(α/2) = 1,96, z(β) = 0,8416, p₁ = 0,10 ve p₂ = 0,12. Sonuç 3840,9'dur; kullanılacak sayı bir üst tam sayıya yuvarlanır (3841).

```python
def z_istatistik(xa, xb, na, nb):
    pa, pb = xa / na, xb / nb
    pp = (xa + xb) / (na + nb)
    se = np.sqrt(pp * (1 - pp) * (1 / na + 1 / nb))
    return np.where(se > 0, (pa - pb) / np.where(se > 0, se, 1), 0.0)

def yanlis_pozitif(K):
    """K esit bakis; herhangi birinde |z| > 1.96 ise anlamli."""
    adim = chunks // K
    bakis = np.arange(adim, chunks + 1, adim)     # chunk sonlari
    n_bakis = bakis * chunk_n                  # ornek sayisi
    xa = kum_a[:, bakis - 1]
    xb = kum_b[:, bakis - 1]
    z = z_istatistik(xa, xb, n_bakis, n_bakis)
    anlamli = np.any(np.abs(z) > alpha_z, axis=1)
    return anlamli.mean()

print("\nBakis sayisi K    yanlis pozitif orani (hedef 0.05)")
sonuc = []
for K in [1, 2, 5, 10, 20, 50, 100]:
    fpr = yanlis_pozitif(K)
    sonuc.append((K, fpr))
    print("%3d              %.3f" % (K, fpr))

# K=1 (sabit orneklem) gercek alfa ~0.05 olmali
assert abs(sonuc[0][1] - 0.05) < 0.01

# Sabit orneklemde (yalnizca son bakis) z dagilimi kontrolu
z_son = z_istatistik(kum_a[:, -1], kum_b[:, -1], N, N)
print("\nSon bakis z std = %.3f (N(0,1) icin 1.000)" % z_son.std())
```

Simülasyon her grubun başarılarını 100 örneklik parçalarla üretir ve kümülatif toplamları alır. `yanlis_pozitif(K)`, testi K eşit aralıkta bakarak yürütür: herhangi bir bakışta |z| > 1,96 çıkarsa "anlamlı" kabul edilir. Gerçek fark sıfır olduğu için her anlamlı sonuç yanlış pozitiftir.

```python
# Sekil verisi
os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_erken_bakma.csv")
with open(yol, "w", encoding="utf-8") as f:
    f.write("bakis_sayisi,yanlis_pozitif\n")
    for K, fpr in sonuc:
        f.write("%d,%.5f\n" % (K, fpr))
print("Erken bakma verisi yazildi:", os.path.basename(yol))
```

```term
$ python b57_09_ab_erken_bakma.py
Grup basina n = 3840.9  (yukari yuvarla: 3841)

Bakis sayisi K    yanlis pozitif orani (hedef 0.05)
  1              0.048
  2              0.080
  5              0.140
 10              0.188
 20              0.243
 50              0.321
100              0.374

Son bakis z std = 0.981 (N(0,1) icin 1.000)
Erken bakma verisi yazildi: b57_erken_bakma.csv
```

Sabit örneklemde (K = 1) yanlış pozitif oranı 0,048: α = 0,05'e uygun. Ama her bakışta test edersen bu oran hızla büyür: iki bakışta 0,080, on bakışta 0,188, yüz bakışta 0,374. Yani yüz kez bakıp anlamlı çıkınca duran bir deneyin gerçek hata oranı %37'dir; rapor edilen %5 değildir. Şekil 57.10 bu artışı gösteriyor.

![Şekil 57.10: Gerçek fark yokken bakış sayısına göre yanlış pozitif oranı. Sabit örneklem (K = 1) hedef 0,05'i tutuyor; sık bakış oranı hızla şişiriyor.](gorseller/b57_erken_bakma.png)

Çözüm, testi baştan doğru tasarlamaktır. Ya örneklem büyüklüğü önceden sabitlenir ve test yalnızca o noktada yapılır; ya da sıralı testler kullanılır, burada hata bütçesi (α) bakışlara dağıtılır (Pocock ya da O'Brien–Fleming sınırları gibi; genel bilgi). Anlık geçerli p-değerleri (always-valid) gibi daha yeni yaklaşımlar da var; ama hepsinin ortak noktası, "ne zaman bakacağına" önceden karar vermektir.

**Raporlama.** Deneyin sonucu tek bir sayı olarak verilmez. Bir rapor en azından şunları içerir: ana ölçüt ile birlikte güven aralığı (Bölüm 49.9'un bootstrap'i), örnek sayıları ve pozitif sayıları, dilim bazlı sonuçlar, maliyet ya da iş etkisi tablosu, eşik ve sürüm bilgisi. Yüzdelik ölçütler de raporun parçası olmalıdır: gecikme için ortalama yerine p99 kullanmak, Bölüm 41'de ve Bölüm 49.11'de gördüğün kuyruk davranışının gereğidir. Son olarak **deney günlüğü** tutulur: her koşu için tohum, veri sürümü, kod sürümü, hiperparametreler ve sonuçlar kaydedilir. Bu günlük, Bölüm 54'te gördüğün tekrarlanabilirliğin ve Bölüm 77'deki MLOps izlemenin temelidir. Bir sonuç yeniden üretilemiyorsa, yayınlanmamış sayılmalıdır.

## Çözümlü Örnekler

Aşağıdaki dört örnek, bölümdeki kavramları elle izlenebilir küçük verilerle uygular. Her örneği önce kâğıt üzerinde çöz; sonra kodu oku ve tabloyu karşılaştır. Örnekler zorluk sırasına göre ★, ★★, ★★, ★★★ diye dizilidir.

### Örnek 1 (★): 200 kişilik taramanın metrikleri

**Adım 1 — Anla.** Bir hastane 200 kişiyi tarıyor. Gerçek durumu bilinen 24 kişiden 18'i model tarafından doğru yakalandı. Model 9 kişiyi yanlış yere "hasta" dedi. Doğruluk, kesinlik, duyarlılık, özgüllük, F1, F2, MCC ve kappa'yı hesapla.

**Adım 2 — Örnekle.** Karışıklık matrisi: TP = 18, FN = 6, FP = 9, TN = 167. Kontrol: 18 + 6 = 24 gerçek hasta, 9 + 167 = 176 sağlıklı, toplam 200.

**Adım 3 — Kaba çöz.** Her ölçütü dört hücreden formülle hesapla: doğruluk (18+167)/200; kesinlik 18/27; duyarlılık 18/24; özgüllük 167/176. F1 ve F2 kesinlik ile duyarlılıktan, MCC ve kappa ise dört hücreden hesaplanır.

**Adım 4 — Örüntü.** Doğruluk (%92,5) tek başına iyi görünüyor, ama "hep sağlıklı" diyen bir tahminci %88 alır: modelin kazancı yalnızca %4,5'tir. Kesinlik 0,667 olduğu için her üç alarmdan biri yanlış; duyarlılık 0,75 olduğu için dört hastadan biri kaçıyor. MCC ve kappa bu iki yönü birlikte tartar.

**Adım 5 — İyileştir.** Elle hesaplamanın hatasını önlemek için her ölçütü bir kez sayılardan hesaplayıp, aynı etiket dizilerini sklearn'e verip karşılaştıran bir program yazalım. Etiket dizileri 24 pozitif ve 176 negatiften oluşur; tahminler sayılara uygun şekilde dizilir.

```python
# b57_ornek1.py: karisiklik matrisinden metrikler (elle + sklearn)
import numpy as np
from sklearn import metrics as M

TP, FN, FP, TN = 18, 6, 9, 167        # 200 kayit
N = TP + FN + FP + TN
print("N = %d, gercek pozitif = %d" % (N, TP + FN))

dogruluk = (TP + TN) / N
kesinlik = TP / (TP + FP)
duyarlilik = TP / (TP + FN)
ozgulluk = TN / (TN + FP)
f1 = 2 * kesinlik * duyarlilik / (kesinlik + duyarlilik)
f2 = 5 * kesinlik * duyarlilik / (4 * kesinlik + duyarlilik)
pay = TP * TN - FP * FN
payda = np.sqrt((TP + FP) * (TP + FN) * (TN + FP) * (TN + FN))
mcc = pay / payda
pe = ((TP + FP) * (TP + FN) + (TN + FN) * (TN + FP)) / N ** 2
kappa = (dogruluk - pe) / (1 - pe)

print("dogruluk   = %.4f" % dogruluk)
print("kesinlik   = %.4f" % kesinlik)
print("duyarlilik = %.4f" % duyarlilik)
print("ozgulluk   = %.4f" % ozgulluk)
print("F1         = %.4f" % f1)
print("F2         = %.4f" % f2)
print("MCC        = %.4f" % mcc)
print("kappa      = %.4f" % kappa)
print("hep 0 diyen dogruluk = %.4f" % ((TN + FP) / N))

# sklearn ile kontrol: ayni sayilardan etiket dizileri
y = np.r_[np.ones(TP + FN), np.zeros(FP + TN)].astype(int)
t = np.r_[np.ones(TP), np.zeros(FN),
           np.ones(FP), np.zeros(TN)].astype(int)
assert abs(M.accuracy_score(y, t) - dogruluk) < 1e-12
assert abs(M.f1_score(y, t) - f1) < 1e-12
assert abs(M.fbeta_score(y, t, beta=2) - f2) < 1e-12
assert abs(M.matthews_corrcoef(y, t) - mcc) < 1e-12
assert abs(M.cohen_kappa_score(y, t) - kappa) < 1e-12
print("sklearn ile birebir eslesti.")
```

**Adım 6 — Doğrula.** Program çıktısı ve elle iz tablosu:

```term
$ python b57_ornek1.py
N = 200, gercek pozitif = 24
dogruluk   = 0.9250
kesinlik   = 0.6667
duyarlilik = 0.7500
ozgulluk   = 0.9489
F1         = 0.7059
F2         = 0.7317
MCC        = 0.6646
kappa      = 0.6631
hep 0 diyen dogruluk = 0.8800
sklearn ile birebir eslesti.
```

| Adım | Hesap | Sonuç |
|---|---|---|
| Doğruluk | (18 + 167) / 200 | 0,9250 |
| Kesinlik | 18 / (18 + 9) | 0,6667 |
| Duyarlılık | 18 / (18 + 6) | 0,7500 |
| Özgüllük | 167 / (167 + 9) | 0,9489 |
| F1 | 2 · 0,6667 · 0,75 / (0,6667 + 0,75) | 0,7059 |
| F2 | 5 · 0,6667 · 0,75 / (4 · 0,6667 + 0,75) | 0,7317 |
| MCC | (18·167 − 9·6) / √(27·24·176·173) | 0,6646 |
| Kappa | (0,9250 − 0,7774) / (1 − 0,7774) | 0,6631 |

Kappa'daki şansa bağlı uyum pₑ = (27·24 + 173·176) / 200² = 0,7774. Elle hesap ile programın çıktısı aynıdır.

**Bunu AI'sız yazabilir misin?** Aynı 200 kişilik taramada FN'i 6'dan 3'e düşürdüğünü ve TP'nin 21 olduğunu, FP'nin ise 9'da kaldığını varsay. Duyarlılık ve kesinlik ne olur? Hangisi daha fazla değişir?

### Örnek 2 (★★): Altı skordan ROC noktaları ve AUC

**Adım 1 — Anla.** Bir model altı uçuşa risk skoru veriyor. Gerçek durumlar: 1, 0, 1, 1, 0, 0 (1 = arıza). Skorlar 0,95; 0,85; 0,70; 0,60; 0,40; 0,20. Her eşik için TPR ve FPR'yi bul, ROC eğrisinin altındaki alanı (AUC) hesapla.

**Adım 2 — Örnekle.** Pozitifler: 0,95, 0,70, 0,60 (üç tane). Negatifler: 0,85, 0,40, 0,20 (üç tane). P = 3, N = 3.

**Adım 3 — Kaba çöz.** Skorları büyükten küçüğe sıralayıp her skoru eşik kabul et. Eşik t'de skor ≥ t olanlar pozitif sayılır. Her adımda TP ve FP sayılarını ekle, TPR = TP/3 ve FPR = FP/3 hesapla.

**Adım 4 — Örüntü.** Eşik düştükçe TPR ve FPR birlikte artar. AUC için iki yol var: yamuk kuralı ya da Mann–Whitney. Mann–Whitney'e göre AUC, rastgele bir pozitifin rastgele bir negatiften yüksek skor alma olasılığıdır: 9 çiftten kaçında pozitif kazanıyor?

**Adım 5 — İyileştir.** Tüm adımları elle yapmak yerine skorları sıralayıp TP ve FP'yi kümülatif sayan bir program yazalım; yamuk alanını ve Mann–Whitney sayımını ayrı ayrı hesaplayıp sklearn ile karşılaştıralım.

```python
# b57_ornek2.py: 6 ornekle ROC noktalari, AUC ve Mann-Whitney
import numpy as np
from sklearn import metrics as M

skor = np.array([0.95, 0.85, 0.70, 0.60, 0.40, 0.20])
y = np.array([1, 0, 1, 1, 0, 0])
P, N = y.sum(), len(y) - y.sum()
print("P = %d, N = %d" % (P, N))
print("esik   TP  FP   TPR     FPR")
tp = fp = 0
noktalar = [(0.0, 0.0)]
for e in np.sort(skor)[::-1]:
    tp = np.sum((skor >= e) & (y == 1))
    fp = np.sum((skor >= e) & (y == 0))
    noktalar.append((fp / N, tp / P))
    print("%.2f   %d   %d   %.3f   %.3f"
          % (e, tp, fp, tp / P, fp / N))

x = np.array([p[0] for p in noktalar])
yy = np.array([p[1] for p in noktalar])
auc = np.sum((x[1:] - x[:-1]) * (yy[1:] + yy[:-1]) / 2)
print("AUC (yamuk) = %.4f  (= 7/9 = %.4f)" % (auc, 7 / 9))

poz, neg = skor[y == 1], skor[y == 0]
cift = [(a > b) + 0.5 * (a == b) for a in poz for b in neg]
print("Mann-Whitney: %d/9 = %.4f" % (sum(cift), np.mean(cift)))
assert abs(auc - M.roc_auc_score(y, skor)) < 1e-12
assert abs(np.mean(cift) - auc) < 1e-12
print("sklearn roc_auc_score ile birebir.")
```

**Adım 6 — Doğrula.** Program çıktısı:

```term
$ python b57_ornek2.py
P = 3, N = 3
esik   TP  FP   TPR     FPR
0.95   1   0   0.333   0.000
0.85   1   1   0.333   0.333
0.70   2   1   0.667   0.333
0.60   3   1   1.000   0.333
0.40   3   2   1.000   0.667
0.20   3   3   1.000   1.000
AUC (yamuk) = 0.7778  (= 7/9 = 0.7778)
Mann-Whitney: 7/9 = 0.7778
sklearn roc_auc_score ile birebir.
```

| Eşik | TP | FP | TPR | FPR |
|---|---|---|---|---|
| 0,95 | 1 | 0 | 0,333 | 0,000 |
| 0,85 | 1 | 1 | 0,333 | 0,333 |
| 0,70 | 2 | 1 | 0,667 | 0,333 |
| 0,60 | 3 | 1 | 1,000 | 0,333 |
| 0,40 | 3 | 2 | 1,000 | 0,667 |
| 0,20 | 3 | 3 | 1,000 | 1,000 |

Yamuk alanı: eğri (0; 0) → (0; 0,333) → (0,333; 0,333) → (0,333; 0,667) → (0,333; 1) → (0,667; 1) → (1; 1) noktalarından geçer. Dikey parçaların genişliği sıfır olduğu için alan katmaz. Geri kalan üç yatay parçanın katkısı: (0,333 · 0,333) = 1/9; (0,333 · 1) = 1/3; (0,333 · 1) = 1/3. Toplam 1/9 + 1/3 + 1/3 = 7/9 = 0,7778. Mann–Whitney sayımı da 9 çiftten 7'sini pozitif kazanır: 0,95 üç negatifi de geçer (3); 0,70 iki negatifi geçer (2); 0,60 iki negatifi geçer (2). Toplam 7.

**Bunu AI'sız yazabilir misin?** Skorların hepsini 0,5 yaparsan AUC kaç olur? Peki iki pozitif ile bir negatif aynı skoru alırsa Mann–Whitney sayımında her eşitlik nasıl sayılır?

### Örnek 3 (★★): Maliyet matrisine göre en iyi eşik

**Adım 1 — Anla.** Sekiz uçuşta model arıza olasılığı p veriyor. Kaçan arıza (FN) 4 birim, gereksiz bakım (FP) 1 birim maliyetli. Hangi eşik en düşük maliyeti verir? Teorik eşik nedir?

**Adım 2 — Örnekle.** p = 0,90; 0,70; 0,55; 0,40; 0,30; 0,20; 0,10; 0,05. Gerçek etiketler y = 1; 1; 0; 1; 0; 0; 1; 0. Pozitifler: 0,90; 0,70; 0,40; 0,10 (dört tane). Negatifler: 0,55; 0,30; 0,20; 0,05 (dört tane).

**Adım 3 — Kaba çöz.** Her eşik için hem beklenen maliyeti (olasılıkları doğru kabul ederek) hem gözlenen maliyeti (gerçek etiketlerle FP ve FN sayarak) hesapla. Beklenen maliyet: Σ_{p≥t} (1−p)·c_FP + Σ_{p<t} p·c_FN, bölü N.

**Adım 4 — Örüntü.** Teori t* = c_FP / (c_FP + c_FN) = 1/5 = 0,20 verir. Beklenen maliyet bu noktada minimumdur; çünkü her örnek için iki seçeneğin beklenen maliyetleri bu eşikte eşitlenir. Gözlenen maliyet ise sekiz örnekte gürültülüdür; en düşük değeri 0,05'te verebilir.

**Adım 5 — İyileştir.** Beklenen ve gözlenen maliyeti yan yana gösteren bir tarama yazalım; böylece teori ile örnek gürültüsünü ayırabilelim.

```python
# b57_ornek3.py: maliyet matrisine gore en iyi esik
import numpy as np

p = np.array([0.90, 0.70, 0.55, 0.40, 0.30, 0.20, 0.10, 0.05])
y = np.array([1, 1, 0, 1, 0, 0, 1, 0])
c_fp, c_fn = 1, 4
t_star = c_fp / (c_fp + c_fn)
print("c_FP = %d, c_FN = %d, t* = %.3f" % (c_fp, c_fn, t_star))
print("esik   beklenen   gozlenen")
print("       maliyet    maliyet")
for t in [0.05, 0.15, 0.20, 0.25, 0.35, 0.50, 0.80]:
    karar = p >= t
    # Beklenen maliyet: olasiliklari dogru kabul ederek
    bek = np.sum(karar * (1 - p) * c_fp
                 + (~karar) * p * c_fn) / len(p)
    # Gozlenen maliyet: gercek etiketlerle
    fp = int(np.sum(karar & (y == 0)))
    fn = int(np.sum(~karar & (y == 1)))
    goz = (c_fp * fp + c_fn * fn) / len(p)
    print("%.2f   %.4f     %.4f" % (t, bek, goz))
```

**Adım 6 — Doğrula.** Program çıktısı. Eşik 0,20'deki iz: p ≥ 0,20 olan altı örnek pozitif sayılır. Bunların beklenen maliyeti (1−p) toplamı 0,10 + 0,30 + 0,45 + 0,60 + 0,70 + 0,80 = 2,95; p < 0,20 olan iki örneğin (0,10 ve 0,05) toplamı 0,15 ve bunun c_FN = 4 ile çarpımı 0,60; toplam 3,55, bölü 8 = 0,4437.

```term
$ python b57_ornek3.py
c_FP = 1, c_FN = 4, t* = 0.200
esik   beklenen   gozlenen
       maliyet    maliyet
0.05   0.6000     0.5000
0.15   0.4437     0.8750
0.20   0.4437     0.8750
0.25   0.4437     0.7500
0.35   0.5062     0.6250
0.50   0.6312     1.1250
0.80   1.1625     1.5000
```

**Bunu AI'sız yazabilir misin?** Maliyet oranını c_FN = 9, c_FP = 1 yaparsan teorik eşik kaça düşer? Bu eşikte beklenen maliyeti, yukarıdaki tabloya ekleyip hesapla. Gözlenen maliyet hâlâ gürültülü mü?

### Örnek 4 (★★★): İki modelin farkı anlamlı mı? McNemar testi

**Adım 1 — Anla.** İki sınıflandırıcı aynı 40 test örneğini sınıflandırdı. Birincisi 38 örneği, ikincisi 33 örneği doğru bildi. Farkın şans olup olmadığını McNemar testiyle sına. Tam (exact) ve süreklilik düzeltmeli ki-kare sonuçlarını karşılaştır.

**Adım 2 — Örnekle.** Eşleştirilmiş tablo: a = 31 (ikisi de doğru), b = 7 (birinci doğru, ikinci yanlış), c = 2 (birinci yanlış, ikinci doğru), d = 0 (ikisi de yanlış). Kontrol: 31 + 7 + 2 + 0 = 40. Birinci model 31 + 7 = 38 doğru, ikinci 31 + 2 = 33 doğru.

**Adım 3 — Kaba çöz.** H₀: b = c (iki model aynı oranda çelişiyor). Yalnızca uyumsuz çiftler (b + c = 9) bilgi taşır. Tam test: X ~ Bin(9, ½), iki yönlü p = 2·P(X ≤ 2). Ki-kare: χ² = (|b − c| − 1)² / (b + c).

**Adım 4 — Örüntü.** Uyumsuz çiftler 9 tane ve bunların 7'si birinci modelin lehine. Tam test, küçük örneklemde ki-kare yaklaşımından daha güvenilirdir. Ama iki sonuç da "anlamlı değil" (p ≈ 0,18) diyor: 9 uyumsuz çift, 7'ye 2'lik bir farkı kesin kılmak için yetersiz.

**Adım 5 — İyileştir.** Hem elle hesabı hem de scipy'nin tam binom testini aynı programda karşılaştıralım; eşitlik çıkmalı.

```python
# b57_ornek4.py: iki modelin eslestirilmis McNemar testi
import math
from scipy.stats import binomtest

a, b, c, d = 31, 7, 2, 0   # a: ikisi dogru; b, c: uyumsuz
n = a + b + c + d
print("Tablo: a=%d b=%d c=%d d=%d, n=%d" % (a, b, c, d, n))
print("Model 1 dogruluk = %.4f" % ((a + b) / n))
print("Model 2 dogruluk = %.4f" % ((a + c) / n))
print("Fark (1-2)       = %.4f" % ((b - c) / n))

chi2 = (abs(b - c) - 1) ** 2 / (b + c)
p_ki = math.erfc(math.sqrt(chi2 / 2))
print("chi2 (sureklilik duzeltmeli) = %.4f, p = %.4f" % (chi2, p_ki))

m = b + c
alt = sum(math.comb(m, k) for k in range(min(b, c) + 1))
p_tam = min(1.0, 2 * alt / 2 ** m)
print("tam binom: X ~ Bin(%d, 0.5), P(X<=%d) = %d/%d"
      % (m, min(b, c), alt, 2 ** m))
print("tam iki yonlu p = %.4f" % p_tam)
print("scipy binomtest = %.4f" % binomtest(min(b, c), m, 0.5).pvalue)
```

**Adım 6 — Doğrula.** Program çıktısı ve iz tablosu:

```term
$ python b57_ornek4.py
Tablo: a=31 b=7 c=2 d=0, n=40
Model 1 dogruluk = 0.9500
Model 2 dogruluk = 0.8250
Fark (1-2)       = 0.1250
chi2 (sureklilik duzeltmeli) = 1.7778, p = 0.1824
tam binom: X ~ Bin(9, 0.5), P(X<=2) = 46/512
tam iki yonlu p = 0.1797
scipy binomtest = 0.1797
```

| Adım | Hesap | Sonuç |
|---|---|---|
| Birinci model doğruluğu | (31 + 7) / 40 | 0,9500 |
| İkinci model doğruluğu | (31 + 2) / 40 | 0,8250 |
| χ² (düzeltmeli) | (|7 − 2| − 1)² / 9 = 16/9 | 1,7778 |
| p (ki-kare) | erfc(√(χ²/2)) | 0,1824 |
| Tam p | 2 · (1 + 9 + 36) / 512 | 0,1797 |

Burada tam p (0,1797), ki-kare p'den (0,1824) biraz küçüktür; küçük örneklemde ki-kare yaklaşımı tam testten hafifçe farklı çıkar. Sonuç iki yöntemde de %5'in üstünde: fark yok diyemeyiz, ama "birinci model daha iyi" diyebilecek kanıt da yok.

**Bunu AI'sız yazabilir misin?** Aynı tabloda b = 14 ve c = 4 olsaydı (a = 22, d = 0, n = 40), tam p değeri yaklaşık olarak ne olurdu? Hangi b ve c kombinasyonu %5 düzeyinde anlamlı çıkar; bunu binom toplamından bul.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde önce kendi tasarımını yap; yapay zekâ araçlarına, kendin bir taslak çıkarana kadar başvurma. Aşağıdaki "önerilen yaklaşım" bölümleri yalnızca bir ipucudur, tam çözüm değildir. Başarı kriterlerini tamamlamadan projeyi bitmiş sayma.
:::

### Proje 1 (★★): Kendi değerlendirme kütüphanen

**Amaç.** Bu bölümdeki ölçütleri tek bir modül hâline getirmek: karışıklık matrisi, ikili ve çok sınıflı ölçütler, kappa ve MCC, ROC ve PR eğrileri, AP, Brier, ECE, bootstrap güven aralığı ve McNemar testi. Her fonksiyonu sıfırdan yaz; sonra sklearn ile birebir karşılaştıran bir test dosyası hazırla.

**Beklenen davranış.** Modül, bir etiket ve skor dizisi alıp bir rapor üretir: ana ölçütler, güven aralıkları (bootstrap), ROC ve PR için AUC ve AP, kalibrasyon özeti ve bir güvenilirlik diyagramı. Test dosyası rastgele veriler ve sabit tohumla, her ölçütün sklearn'den farkının 10⁻⁹'dan küçük olduğunu göstermeli.

**Önerilen yaklaşım.** Önce ikili karışıklık matrisini yaz ve tüm ölçütleri bu dört sayıdan hesapla. Sonra eşik taramasını sıralama ile yap; kaba kuvvetli sürümle karşılaştırmayı unutma. Bootstrap için test örneklerini indeksle yeniden örnekle ve her seferinde aynı indeksleri iki modele uygula. ECE için kutu aralıklarının uç noktalarına dikkat et: 1,0 değeri hangi kutuya düşüyor?

**Başarı kriterleri.** (1) Her ölçüt, sklearn ile en fazla 10⁻⁹ farkla eşleşiyor. (2) Dengesiz veride (%1 pozitif) raporda ROC-AUC ile AP ayrı ayrı ve taban oranı yanında görünüyor. (3) Bootstrap güven aralığı 2000 yeniden örnekle üretiliyor ve tohum raporda yazıyor. (4) Güvenilirlik diyagramı, aşırı güvenli bir modelle ve kalibre edilmiş hâliyle iki panelde karşılaştırılmış. (5) Kütüphane, sürüm numaralarını (Python, numpy, scikit-learn) raporun başına yazıyor.

### Proje 2 (★★★): İHA tehdit sınıflandırıcısı için çalışma noktası raporu

**Amaç.** Dengesiz sentetik bir veride (tehdit oranı %1 ya da daha az) iki sınıflandırıcı eğitip, savunma sözleşmesi biçiminde bir çalışma noktası raporu üretmek: "yanlış alarm oranı en fazla %x iken en yüksek tespit oranı nedir, ve bu koşulda kaç yanlış alarm günde beklenir?"

**Beklenen davranış.** Rapor şunları içermeli: iki modelin PR ve ROC eğrileri (taban çizgisiyle birlikte); yanlış alarm kısıtı altında en iyi eşik ve o noktadaki tespit oranı; her iki model için kalibrasyon diyagramı; mesafe ya da yükseklik gibi bir öznitelik üzerinde dilim analizi (her dilimde n ve pozitif sayısı); maliyet oranına göre beklenen maliyet tablosu; ve en az 5 tohum üzerinden tespit oranının dağılımı.

**Önerilen yaklaşım.** Veriyi önce üretip eğitim, doğrulama ve test olarak ayır; çalışma noktasını doğrulama kümesinde seç, test kümesinde yalnızca raporla. Bir modelin olasılıklarını bir kalibrasyon kümesiyle düzelt ve iki durumun (kalibre ve kalibre edilmemiş) çalışma noktasını nasıl etkilediğine bak. Dilimleri yalnızca bir öznitelik çeyreklerine göre kurma; her dilimin pozitif sayısını raporla ve küçük dilimlerde sonucu yorumlamadan önce belirsizliği hesapla.

**Başarı kriterleri.** (1) Çalışma noktası, test kümesinde değil doğrulama kümesinde seçilmiş ve bu süreç raporda belgeli. (2) Her dilim için n ve pozitif sayısı var; pozitifi 10'un altında olan dilimler açıkça "yorumlanamaz" diye işaretli. (3) Yanlış alarm oranı ile tespit oranı arasındaki takas bir eğri olarak sunulmuş. (4) Kalibrasyon hatası (ECE) ve log-kayıp her iki model için raporlanmış. (5) Tohumlar arası dağılım en az beş değerle verilmiş ve raporun sonunda "bu sonuç hangi koşullarda geçerli değil?" sorusuna dürüst bir paragraf var.

## Ek Alıştırmalar

Aşağıdaki problemler kademelidir. ★ olanlar kavramı yoklar, ★★ olanlar bir türetme ya da küçük bir hesap ister, ★★★ olanlar birden çok konuyu birleştirir. (Mülakat) etiketli olanlar klasik sorulardır.

1. ★ 1000 örneğin 20'si pozitif. Her zaman negatif diyen modelin doğruluğu nedir, dengeli doğruluğu (duyarlılık ile özgüllüğün ortalaması) nedir? (Mülakat)
2. ★ Bir sınıfta hiç TP yoksa, o sınıfın kesinliği ve F1'i neden sıfır sayılır? Bu bir tanım mı, yoksa bir sonuç mu? (Mülakat)
3. ★ Bir model her örneğe "pozitif" dediğinde duyarlılığı ve kesinliği ne olur? Bu iki sayıyı tek başına okumanın neden yanıltıcı olduğunu açıkla.
4. ★★ Kare kaybı (1/N) Σ (y − c)² bir sabit c için en küçük yapan değer nedir? MAE için aynı soruyu sor. Hangisi neden medyan ya da ortalama üretir? (Mülakat)
5. ★★ AUC = 0,5 ne anlama gelir? AUC = 0,3 olan bir modeli nasıl "düzeltirsin", ve bu düzeltme ROC-AUC'yi nasıl değiştirir? (Mülakat)
6. ★★ Pozitif oranı %1 olan bir veride bir modelin PR-AUC'si 0,01'in altında olabilir mi? Hangi koşulda olur?
7. ★★ FPR = 0,01, TPR = 0,8; negatif sayısı 1000, pozitif sayısı 100. TP, FP ve kesinliği hesapla. Kesinlik neden FPR'dan çok farklı görünüyor?
8. ★★ Bir yanlış tahmin için log-kaybı nedir: p = 0,999 ile y = 0 ve p = 0,6 ile y = 0 durumlarında? Hangi tahmin daha pahalıdır ve neden? (Mülakat)
9. ★★ Bir kalibrasyon kümesinde model her örneğe p = 0,9 veriyor, ama gerçekte örneklerin %60'ı pozitif. ECE'yi hesapla ve bu durumun hangi tür bir kalibrasyon hatası olduğunu söyle.
10. ★★ k = 5 ile k = 10 katlı CV'yi karşılaştır: hangisi daha yanlı, hangisi daha değişken olur? Bu iki özelliği ölçmek için hangi deney gerekir?
11. ★★★ Bir arama 50 konfigürasyon deniyor; hepsinin gerçek skoru 0,5 ve doğrulama skoru standart sapması 0,02. En iyi gözlenen skorun beklenen değerini yaklaşık hesapla (50 bağımsız normalin maksimumu için yaklaşık 2,25 standart sapma; genel bilgi). Bu değer, test skorunun 0,5 çıkacağı anlamına mı gelir? (Mülakat)
12. ★★★ Bir A/B testinde 2000 gözlemden sonra p = 0,04 görüyorsun ve testi durdurmak istiyorsun. Ardından 4000 gözlem daha alıp tekrar bakıyorsun. Bu süreçte hangi hata yapılıyor, yanlış pozitif oranı neden artar, ve doğru tasarım ne olmalı? (Mülakat)

## Kod Okuma Egzersizi

Aşağıdaki kesit, scikit-learn 1.8.0 paketinden alındı: `sklearn/metrics/_ranking.py`, `confusion_matrix_at_thresholds` fonksiyonu (satır 853–985; sürüm notu `versionadded:: 1.8`). Bu fonksiyon, ROC, PR ve DET eğrilerinin hepsinin altında yatan TP ve FP sayımını yapar. Kesit, kaynaktaki satırların birebir kopyasıdır; atlanan satırlar `...` ile işaretlidir. Satır 951, 964 ve 974 sayfaya sığsın diye bölünmüştür; ifadede değişiklik yoktur. Girdi doğrulamasını ve `sample_weight` dalını atladık.

```python
    # make y_true a boolean vector
    y_true = y_true == pos_label
    ...
    # sort scores and corresponding truth values
    desc_score_indices = xp.argsort(y_score, stable=True,
                                    descending=True)
    y_score = y_score[desc_score_indices]
    y_true = y_true[desc_score_indices]
    ...
    distinct_value_indices = xp.nonzero(xp.diff(y_score))[0]
    threshold_idxs = xp.concat(
        [distinct_value_indices,
         xp.asarray([size(y_true) - 1], device=device)]
    )
    ...
    y_true = xp.astype(y_true, max_float_dtype)
    tps = xp.cumulative_sum(y_true * weight,
                            dtype=max_float_dtype)[threshold_idxs]
    ...
    else:
        fps = 1 + xp.astype(threshold_idxs, max_float_dtype) - tps
    tns = fps[-1] - fps
    fns = tps[-1] - tps
    return tns, fps, fns, tps, y_score[threshold_idxs]
```

**Sorular — cevaplamadan geçme:**

1. `argsort(..., stable=True, ...)` çağrısı neden kararlı sıralama istiyor? Eşit skorlu örneklerin göreli sırası, son eşik dizisini değiştirir mi?
2. `xp.diff(y_score)` sıfır olmayan yerleri nerede işaretler? `threshold_idxs` dizisine neden son örnek ayrıca eklenir?
3. Ağırlıksız durumda `fps = 1 + threshold_idxs - tps` ifadesi neden doğrudur? `threshold_idxs + 1` neyi sayar, `tps` neyi çıkarır?
4. `tns = fps[-1] - fps` ve `fns = tps[-1] - tps` satırları hangi toplamları kullanır? Bu sayede tüm eşikler neden tek bir geçişte gelir?
5. `sample_weight` varken `fps`'in `cumsum` ile yeniden hesaplanmasının gerekçesi kaynaktaki yorumda nedir? (Yorumu kendi cümlelerinle açıkla.)
6. Bu bölümde yazdığın `esik_sayaclari` fonksiyonu ile yukarıdaki satırlar arasında birebir karşılık bul. Hangi satır `argsort`'a, hangi satır `np.r_[np.where(np.diff(...))]`'e denk düşüyor? Kendi kodunda fark olan bir şey var mı?

## Bölüm Özeti

- Metrik, bir iş kararıdır: FN ve FP'nin maliyetleri farklıysa "doğru" ölçüt de farklıdır. Doğruluk, bu asimetriyi göz ardı eder.
- Karışıklık matrisinin dört hücresinden kesinlik, duyarlılık, özgüllük, F1 ve Fβ türetilir. Dengesiz veride MCC ve kappa, doğruluktan daha dürüst bir özet verir.
- Çok sınıflı ortalamalarda makro, mikro ve ağırlıklı ortalamalar farklı sorulara cevap verir; mikro F1 tek etiketli çok sınıfta doğruluğa eşittir.
- ROC-AUC bir sıralama ölçütüdür ve Mann–Whitney sayımına eşdeğerdir. Nadir pozitif sınıfta ROC iyimser kalır; PR ve AP gerçekçi performansı gösterir.
- Beklenen maliyeti en küçük yapan eşik t* = c_FP / (c_FP + c_FN) formülüyle verilir; bu, olasılıkların kalibre olduğunu varsayar. Savunmada yanlış alarm kısıtı altında en yüksek tespit, ROC üzerinde bir kesitle bulunur.
- Olasılık kalitesi ayrı bir konudur: log-kayıp, Brier ve ECE kalibrasyonu ölçer. Platt dönüşümü sıralamayı korur, izotonik dönüşüm ise eşitlik üretebilir.
- Çapraz doğrulama skoru bölme ve seçim gürültüsü taşır; hiperparametre seçimi iç içe CV ile yapılmazsa skor iyimser çıkar. Çok deneme, doğrulama kümesine aşırı uyum üretir.
- Modeller arası fark, eşleştirilmiş testlerle (McNemar, bootstrap, 5 × 2 CV) ve güven aralığıyla raporlanır; tek bir p-değeri yetmez.
- A/B testlerinde örneklem büyüklüğü önceden hesaplanır; sürekli bakmak yanlış pozitif oranını hızla şişirir. Raporlama, belirsizlik, dilim, maliyet ve deney günlüğü ile birlikte yapılır.

**Sonraki bölümde:** Bölüm 58, Doğrusal Modeller ile devam ediyor. Bu bölümde lojistik regresyonun olasılıklarını ve kayıp fonksiyonunu kullandık; bir sonraki bölümde lineer ve lojistik regresyonu sıfırdan kuracak, softmax'i ve L1/L2 düzenlileştirmesini göreceğiz.

::: mulakat
1. Bir sınıflandırıcının doğruluğu %97 ama kesinliği %40. Bu nasıl mümkün olur? Hangi veri ve hangi model davranışı bunu açıklar?
2. ROC-AUC ile PR-AUC'nin nadir pozitif sınıfta neden farklı sonuç verdiğini, FPR ve kesinlik tanımlarını kullanarak anlat.
3. Bir modelin olasılıklarını kalibre etmek neden sıralamayı değiştirmeden yapılabilir? Platt ve izotonik kalibrasyonu karşılaştır.
4. İç içe çapraz doğrulama neden gereklidir? Hiperparametre seçimi ile performans tahminini aynı katlarda yaparsan hangi yanlılık oluşur?
5. Bir ekip 200 farklı konfigürasyon deneyip en iyisini raporluyor. Bu rakamı nasıl yorumlarsın, ve hangi ek deneyle doğrulamak istersin?
6. Bir modelin güven aralığı [0,0; 7,6] puan. Farkın anlamlı olup olmadığı hakkında ne söylersin? Tek bir p-değeri yerine hangi bilgiyi de raporlarsın?
7. Bir A/B testinde her gün baktın ve p-değeri ilk kez 0,05'in altına inince durdurdun. Bu sonucu neden güvenilir bulmazsın? Doğru tasarım ne olmalıydı?
8. Bir savunma sisteminde "yanlış alarm oranı yüzde birin altında, en yüksek tespit" sözü verilmek isteniyor. Bu sözün ölçümünü ve doğrulamasını hangi veri ve hangi raporla yaparsın?
:::

