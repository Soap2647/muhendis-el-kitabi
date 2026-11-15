%% kisim_no: XIV
%% kisim_ad: Makine Öğrenmesi
%% bolum_no: 60
%% baslik: SVM & Kernel Yöntemleri

## Giriş: Doğruyu bulmak yetmez, en güvenli doğruyu bulmak gerekir

Bölüm 58'de iki sınıfı ayıran bir doğrusal sınır çizdik ve lojistik regresyonla her noktaya bir olasılık atadık. Orada hangi doğrunun seçileceği sorusunu bilerek erteledik. Veri doğrusal olarak ayrılabiliyorsa sonsuz sayıda ayırıcı doğru vardır ve hepsi eğitim kümesini hatasız sınıflandırır. Bunlardan birini seçmek, yeni bir nokta sınırın hemen yakınına düştüğünde ne olacağını da seçmek demektir.

Destek vektör makinesi (SVM, Support Vector Machine) bu seçimi açıkça yapar: iki sınıf arasında en geniş boşluğu bırakan doğruyu arar. Bu fikir, bir kez anlaşıldığında, kernel yöntemlerinin tamamının kapısını açar. Doğrusal bir sınır yetersiz kaldığında veriyi daha yüksek boyutlu bir uzaya taşımak gerekir; SVM bunu, taşımayı hiç yapmadan, yalnızca iç çarpımları hesaplayarak yapar. Bu hileye çekirdek hilesi (kernel trick) denir ve bu bölümün merkezindedir.

Savunma sanayiinde bu konu sık karşına çıkar. Bir sensör imzasının "hedef" ya da "hedef değil" olarak sınıflandırılması, bir arıza belirtisinin "normal" ya da "arıza" olarak etiketlenmesi, genellikle birkaç yüz ya da birkaç bin örnekle yapılır ve yüksek boyutlu özniteliklerden oluşur. Bu koşullarda SVM, derin ağlar eğitmeden güçlü ve iyi anlaşılmış bir referans sunar. EV Dashboard projesindeki STM32 sensör öznitelikleri gibi bir veri kümesini birkaç yüz örnekle sınıflandırmak istediğinde, bu bölümdeki araçların doğrudan karşılığı vardır.

Mülakatlarda "SVM nedir, marj nedir, destek vektörü neden önemlidir, kernel trick nedir, neden RBF kullanılır" soruları çok sık gelir. Bu soruları ezberlemek yerine aynı sorulara bir cevabın nasıl kurulduğunu bu bölümde adım adım göreceksin: geometri, optimizasyon (Bölüm 50'deki Lagrange ve KKT koşulları), iç çarpım ve Gram matrisi (Bölüm 48), ardından ölçeklenebilirlik.

Bölüm şu sırayla ilerler: önce en geniş marj fikri, sert ve yumuşak marj, menteşe kaybıyla SVM'nin bir kayıp fonksiyonu olarak okunuşu. Sonra birincil problemi alt-gradyan inişiyle, ikincil (dual) problemi ise basitleştirilmiş SMO ile çözeceğiz. Çekirdekler, Mercer koşulu ve RBF'nin γ ve C parametreleriyle davranışı ardından gelir. Son bölümde ölçeklenebilirlik, pratik ayarlar ve gömülü sistemlerde çıkarım bütçesi ele alınır.

::: not
Bu bölümdeki her kod, NumPy ile sıfırdan yazılmış bir gerçekleme ile scikit-learn 1.8.0'ın karşılığı yan yana karşılaştırılarak doğrulanmıştır. Sayısal sonuçlar ayrı test kümelerinde ve birden çok sabit tohum (random_state) ile ölçülmüştür; her sonucun üretildiği betik bu bölümde tam olarak verilmiştir. Eğitim skorları test skorundan ayrıca etiketlenmiştir.
:::

## 60.1 En geniş marj fikri

İki sınıfın noktaları düzlemde duruyor ve bir doğru bulmak istiyoruz. Her doğru, bu noktaları iki yana ayırabiliyorsa geçerlidir. Ama geçerli doğrular arasında bir fark var: bazıları bir sınıfın noktalarına çok yakın geçer, bazıları ise iki sınıfın ortasından geniş bir koridor bırakır. İkinci tür doğru, bir noktanın küçük bir gürültüyle yanlış tarafa geçme ihtimalini azaltır.

Bu sezgi, genelleme (generalization) kavramıyla bağlantılıdır. Eğitim kümesindeki noktalar gerçek dağılımdan bir örnektir; yeni noktalar bu dağılımdan gelir ve tam olarak aynı yerlerde değildir. Sınıfların arasında geniş bir boşluk bırakan bir sınır, yeni noktaların ufak sapmalarına karşı daha dayanıklıdır. Bu düşünce, Vapnik'in istatistiksel öğrenme kuramında yapısal risk minimizasyonu adıyla resmîleşmiştir (genel bilgi; bu bölümde ispatına girmiyoruz).

Önce bir geometri tanımı yapalım. Bir doğru `wᵀx + b = 0` ile verilsin; burada `w` doğruya dik yönü, `b` ise kaymayı belirler. Bir `x` noktasının bu doğruya işaretli uzaklığı `(wᵀx + b) / ‖w‖` dir. Eğer etiket `y` ∈ {−1, +1} ise, doğru doğruysa `y(wᵀx + b)` pozitiftir. Bir doğrunun marjı, o doğruya en yakın noktanın uzaklığıdır.

Aşağıdaki şekilde aynı dört nokta için üç farklı dikey doğru var. Üçü de sınıfları hatasız ayırıyor, ama yalnızca ortadaki doğru iki sınıfa da eşit uzaklıkta duruyor ve en geniş boşluğu bırakıyor. Şekildeki sayılar, bu dört nokta için hesaplanmış marjlardır; hesabı Bölüm 60.2'de ve Çözümlü Örnek 1'de yapacağız.

![Şekil 60.1: Birçok doğru ayırır; yalnızca ortadaki en geniş marjlıdır](gorseller/b60_en_genis_marj.png)

Şekil 60.1'de sol dış doğru (c = 0,5) C noktasına yakındır, sağ dış doğru (c = 1,5) ise A noktasına. Her iki durumda da marj 1,0 çıkar. Ortadaki doğru (c = 1) iki tarafa da 1 birim uzaklıkta, marj 2,0'dır. Bu, "en geniş" kriterinin tam olarak ne anlama geldiğini gösteriyor: boşluğu en büyük yapan doğru, en yakın iki noktanın ikisine de eşit uzaklıkta olan doğrudur.

Burada bir uyarı gerekli. Bu geometrik sezgi ile genelleme arasındaki bağ genel bir sezgidir; bu bölümde onu sayılarla kanıtlamıyoruz. Ölçülebilir olan şey, marjın belirlediği çözümün yeni verilerdeki performansıdır ve bunu Bölüm 60.3 ve 60.9'daki deneylerde test kümesinde gözlemleyeceğiz.

## 60.2 Sert marjlı SVM: marj formülü ve destek vektörleri

Veri doğrusal olarak ayrılabiliyorsa, her eğitim noktası için `yᵢ(wᵀxᵢ + b) > 0` koşulu sağlanır. Ölçek belirsizliğini ortadan kaldırmak için bir normalizasyon seçelim: sınıfların en yakın noktalarında `yᵢ(wᵀxᵢ + b) = 1` olsun. Bu seçim, `w` ve `b`'yi aynı anda bir sayıyla çarparak değiştirmeyi engellemez; ama sınır noktalarında değeri sabitler. Bu normalizasyonla, en yakın noktalar `wᵀx + b = +1` ve `wᵀx + b = −1` doğrularının üzerinde durur. Bu iki doğru marjın sınırlarıdır.

Marjın genişliğini hesaplayalım. Pozitif sınır doğrusu `wᵀx + b = 1` üzerindeki bir `x₊` noktası ile karar doğrusu `wᵀx + b = 0` arasındaki uzaklık, `1 / ‖w‖` dir. Negatif sınır doğrusu için aynı uzaklık, `1 / ‖w‖` dir. Toplam genişlik, yani marj, `2 / ‖w‖` olur. Bu formül bütün SVM'in özüdür: marjı büyütmek, `‖w‖` yi küçültmekle aynı şeydir.

Bu nedenle sert marjlı SVM'in birincil (primal) problemi şöyle yazılır:

`minimize ½‖w‖²`, koşul: `yᵢ(wᵀxᵢ + b) ≥ 1` her `i` için.

Karesi alınmış `½‖w‖²` tercih edilir, çünkü karesel bir amaç fonksiyonu dışbükeydir ve türevi basittir. Koşullar doğrusaldır. Bu yapıya dışbükey karesel program (QP, quadratic program) denir. Dışbükeylik sayesinde yerel bir minimum, aynı zamanda global minimumdur; bu, Bölüm 50'de gördüğümüz konveksitenin doğrudan sonucudur.

Koşullardan bazıları eşitlik olarak sağlanır: `yᵢ(wᵀxᵢ + b) = 1`. Bu koşulu tam sağlayan noktalara destek vektörleri denir. Çözümü yalnızca bu noktalar belirler. Marjın dışında kalan bir noktayı silmek çözümü değiştirmez; destek vektörünü silmek değiştirir. Bu gözlem, SVM'in neden "destek vektör" makinesi olarak adlandırıldığını açıklar, ve dualde (Bölüm 60.6) bu durum doğrudan görünür hâle gelir.

Şimdi iki noktası ve tek bir doğrusu olan en basit örneğe bak. İki nokta `x₊ = (1, 0)` ve `x₋ = (−1, 0)` olsun. Bu iki noktanın etiketleri sırasıyla `+1` ve `−1` dir. Doğru `x₁ = 0` ise iki noktaya eşit uzaklıkta olur; `w = (1, 0)`, `b = 0` seçimiyle `y₊(w·x₊ + b) = 1` ve `y₋(w·x₋ + b) = 1` sağlanır. Marj `2/‖w‖ = 2` dir. İki nokta arasındaki mesafe 2'dir ve marj da bu mesafenin tamamına eşittir; bu durum, iki destek vektörünün marjı tamamen belirlediği en basit hâldir.

Aşağıdaki program, dört noktalı gerçek bir örnekte sklearn'in sert marjlı SVM'ini (çok büyük C ile) çağırır ve destek vektörlerini, `w`'yi, `b`'yi ve marjı yazdırır. Betiğin ilk bölümü ortak başlığı içerir: veri yükleme ve gerekli kütüphaneler. Betik, bu bölümün sonunda ayrıntılı olarak verilen deney dosyasının ilk kısmıdır; bu aşamada yalnızca sklearn kullanılıyor.

```python
# -*- coding: utf-8 -*-
# Bolum 60 - olcum deneyleri (b60_sifirdan.py ile ayni klasorde).
# CSV'ler ./veri/ altina yazilir; tohumlar sabittir.
import os
import time
import numpy as np
from sklearn.svm import SVC, LinearSVC
from sklearn.datasets import (load_breast_cancer, make_moons,
                              make_circles, make_blobs,
                              make_classification, load_digits)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.kernel_approximation import RBFSampler
from sklearn.kernel_ridge import KernelRidge
from b60_sifirdan import (pegasos_dogrusal, smo_basit, rff_olustur,
                          rff_donustur, krr_fit, krr_tahmin)

os.makedirs("veri", exist_ok=True)


def csv_yaz(ad, bas, satirlar):
    with open(os.path.join("veri", ad), "w", encoding="utf-8") as f:
        f.write(",".join(bas) + "\n")
        for r in satirlar:
            f.write(",".join(str(x) for x in r) + "\n")


Xb, yb = load_breast_cancer(return_X_y=True)
yb = 2 * yb - 1.0
```

Betiğin ikinci kısmı, dört noktalı örneği ve ayrılabilir bir blob verisini çözer. Dört nokta, Bölüm 60.1'deki şekildeki noktalar: A = (2, 1) ve B = (2, 3) pozitif; C = (0, 1) ve D = (−1, 0) negatiftir. Blob verisi ise `make_blobs` ile üretilen, iki sınıf arasında açık bir boşluk bulunan 20 noktadır. `C = 1000` çok büyük olduğu için yumuşak marj cezası neredeyse sıfırdır ve çözüm sert marja yakındır.

```python
# ---- 1. Dort nokta: en buyuk marj ----
X4 = np.array([[2., 1.], [2., 3.], [0., 1.], [-1., 0.]])
y4 = np.array([1, 1, -1, -1.])
s4 = SVC(kernel="linear", C=1e6).fit(X4, y4)
w4 = s4.coef_[0]
b4 = round(float(s4.intercept_[0]), 4)
print("[1] w=", np.round(w4, 4), "b=", b4)
print("[1] SV=", s4.support_, "marj=",
      round(2 / np.linalg.norm(w4), 4))
print("[1] alpha*y=", np.round(s4.dual_coef_[0], 4))

# ---- 2. Ayrilabilir blob: marj ve destek vektorleri ----
Xbl, ybl = make_blobs(n_samples=20, centers=[[0, 0], [3, 3]],
                      cluster_std=0.6, random_state=1)
ybl = 2 * ybl - 1.0
sm = SVC(kernel="linear", C=1000).fit(Xbl, ybl)
svmask = np.zeros(len(ybl), int)
svmask[sm.support_] = 1
wm = sm.coef_[0]
b5 = round(float(sm.intercept_[0]), 4)
print("[2] w=", np.round(wm, 4), "b=", b5)
print("[2] marj=", round(2 / np.linalg.norm(wm), 4),
      "SV=", svmask.sum())
csv_yaz("b60_marj_veri.csv", ["x1", "x2", "y", "sv"],
        [[round(Xbl[i, 0], 4), round(Xbl[i, 1], 4), int(ybl[i]),
          svmask[i]] for i in range(len(ybl))])
csv_yaz("b60_marj_hat.csv", ["w1", "w2", "b", "marj"],
        [[wm[0], wm[1], sm.intercept_[0], 2 / np.linalg.norm(wm)]])
```

Programın çıktısı şöyledir. İlk üç satır dört noktalı örneğe, sonraki iki satır blob verisine aittir.

```term
$ python b60_deney.py
[1] w= [1. 0.] b= -1.0
[1] SV= [2 0] marj= 2.0
[1] alpha*y= [-0.5  0.5]
[2] w= [0.3707 0.49  ] b= -1.181
[2] marj= 3.2551 SV= 3
```

Dört noktalı örnekte `SV = [2 0]` çıktısı, destek vektörlerinin C = (0, 1) ve A = (2, 1) noktaları olduğunu söyler. `alpha*y` satırındaki `−0,5` ve `+0,5` değerleri, Bölüm 60.6'da türeteceğimiz dual katsayılardır. `w = (1, 0)` ve `b = −1` ile marj `2,0` olur; bu, Şekil 60.1'deki ortadaki doğrudur. Blob verisinde ise marj 3,26 ve destek vektörü sayısı 3'tür. Her iki çözüm de, yalnızca birkaç noktanın belirlediği bir sınırı gösterir.

Aşağıdaki şekil blob verisini ve çözümü gösterir. Dolu noktalar eğitim verisidir; daireyle işaretli olanlar destek vektörleridir. Kesik çizgiler `f = ±1` doğrularıdır ve marjın sınırlarını gösterir.

![Şekil 60.2: Marj bandı ve destek vektörleri; yalnızca üç nokta çözümü belirler](gorseller/b60_marj_destek.png)

Şekil 60.2 bir şeyi açıkça gösterir: sınır doğrusu marjın içindeki noktalardan değil, bandın kenarına değen birkaç noktadan belirlenir. Bu nedenle sert marjlı SVM, aykırı değerlere (outlier) karşı çok hassastır; tek bir yanlış etiketli nokta bile çözümü tamamen değiştirebilir. Bu sorunu bir sonraki bölümde yumuşak marj ile çözeceğiz.

## 60.3 Yumuşak marj: gevşek değişkenler ve C parametresi

Gerçek veri nadiren kusursuz ayrılabilir. Gürültü, etiket hatası ya da örtüşen sınıflar varsa, `yᵢ(wᵀxᵢ + b) ≥ 1` koşulunu her nokta için sağlayan bir `w` yoktur. Çözüm, her noktaya bir gevşeklik (slack) değişkeni `ξᵢ ≥ 0` tanımlamaktır:

`yᵢ(wᵀxᵢ + b) ≥ 1 − ξᵢ`

`ξᵢ = 0` olan nokta marjın doğru tarafında, dışında kalır. `0 < ξᵢ < 1` olan nokta marjın içinde ama doğru tarafta durur. `ξᵢ ≥ 1` olan nokta ise yanlış tarafta sınıflandırılmıştır. Gevşeklikleri toplayıp bir cezayla dengeleriz:

`minimize ½‖w‖² + C · Σᵢ ξᵢ`

Burada `C > 0` bir hiperparametredir ve iki şeyi dengeler. Büyük `C`, hata yapmayı çok pahalı kılar; model marjı daraltıp eğitim noktalarının çoğunu doğru tarafta tutmaya çalışır. Küçük `C` ise hataya daha çok izin verir ve marjı genişletmeyi tercih eder. Sınır iki uçta da farklı davranır: `C → ∞` sert marjlı SVM'e yaklaşır, `C → 0` ise `w`'yi neredeyse sıfıra çeker ve sınıflandırıcı çok az bilgi taşır.

Bu parametrenin ne anlama geldiğini deneyle görelim. Aşağıdaki deney, gürültülü iki boyutlu bir veri kümesinde (200 nokta, etiketlerin %10'u çevrilmiş) C değerini 0,01'den 100'e kadar tarar. Her C için beş farklı tohumla veriyi böler, lineer SVM'i eğitir ve iki sonucu toplar: marjın büyüklüğü (`2/‖w‖`) ve destek vektörü sayısı.

Aşağıdaki kod, bu tarama için tam deney betiğinin üçüncü kısmıdır. `SVC(kernel="linear", C=Cv)` çağrısı, sklearn'in dual problemi çözen lineer SVM'ini kullanır. sklearn'de `C`, gevşekliklerin toplamının önündeki çarpandır ve veri sayısına bölünmez; bu nokta, Bölüm 60.5'te birincil problemle karşılaştırma yaparken önemli olacak.

```python
# ---- 3. C taramasi (gurultulu dogrusal veri, 5 tohum) ----
print("[3] C taramasi")
tab, hatlar = [], []
for Cv in [0.01, 0.1, 1, 10, 100]:
    nsv, marj, tr, te = [], [], [], []
    for sd in range(5):
        X, y = make_classification(
            n_samples=200, n_features=2, n_redundant=0,
            n_informative=2,
            n_clusters_per_class=1, flip_y=0.1, class_sep=1.0,
            random_state=sd)
        y = 2 * y - 1.0
        Xtr, Xte, ytr, yte = train_test_split(
            X, y, test_size=0.3, stratify=y, random_state=sd)
        m = SVC(kernel="linear", C=Cv).fit(Xtr, ytr)
        nsv.append(m.n_support_.sum())
        marj.append(2 / np.linalg.norm(m.coef_[0]))
        tr.append(np.mean(m.predict(Xtr) == ytr))
        te.append(np.mean(m.predict(Xte) == yte))
        if sd == 0:
            hatlar.append([Cv, m.coef_[0][0], m.coef_[0][1],
                           m.intercept_[0]])
            csv_yaz("b60_c_veri.csv", ["x1", "x2", "y"],
                    [[a, b, 2 * int(c) - 1]
                     for (a, b), c in zip(X, y)])
    print("  C=%g SV=%.1f marj=%.3f egitim=%.3f test=%.3f+-%.3f"
          % (Cv, np.mean(nsv), np.mean(marj), np.mean(tr),
             np.mean(te), np.std(te)))
    tab.append([Cv, np.mean(nsv), np.mean(marj), np.mean(tr),
                np.mean(te), np.std(te)])
csv_yaz("b60_c_tarama.csv",
        ["C", "sv", "marj", "egitim", "test", "test_sd"], tab)
csv_yaz("b60_c_hat.csv", ["C", "w1", "w2", "b"], hatlar)
```

Programın çıktısı şöyledir.

```term
[3] C taramasi
  C=0.01 SV=107.8 marj=2.924 egitim=0.876 test=0.873+-0.062
  C=0.1 SV=53.8 marj=1.531 egitim=0.917 test=0.897+-0.078
  C=1 SV=36.0 marj=1.122 egitim=0.926 test=0.903+-0.068
  C=10 SV=32.8 marj=0.988 egitim=0.926 test=0.897+-0.074
  C=100 SV=31.6 marj=0.960 egitim=0.926 test=0.897+-0.074
```

Tablo, C'nin davranışını net gösteriyor. Marj 2,92'den 0,96'ya düşüyor ve destek vektörü sayısı 108'den 32'ye iniyor: C büyüdükçe model daha az noktayı marjın içine alıyor. Eğitim doğruluğu 0,876'dan 0,926'ya çıkıyor ve sonra sabit kalıyor. Test doğruluğu ise C = 1 civarında en yüksek görünüyor (0,903), ama tohumlar arası standart sapma 0,06 ile 0,08 arasında. Bu fark, beş tohumun ortalamasının bile gürültüsü içinde kalır. Yani bu veride "en iyi C" yoktur; doğru C, çapraz doğrulamayla (Bölüm 57) seçilmelidir.

Aşağıdaki şekil, aynı veri üzerinde dört farklı C değeri için karar sınırını ve marj çizgilerini gösterir. Şekildeki her panel, eğitim kümesinden öğrenilen `w` ve `b` ile çizilmiştir; noktaların tümü gösterilmiştir.

![Şekil 60.3: C küçükken marj geniş ve çok hata vardır; C büyüdükçe marj daralır](gorseller/b60_c_etkisi.png)

Şekil 60.3'te marjın kalınlığı C ile değişiyor: C = 0,01'de marj 3,08 gibi geniş bir bant, C = 100'de 1,28 gibi dar bir bant oluşuyor. Bu, `C` parametresinin bir "düzenlileştirme gücü" olduğunu gösterir; Bölüm 58'deki L2 cezasının `λ`'sıyla bağlantılıdır, ama ters yönde çalışır: büyük `C` az düzenlileştirme, küçük `C` çok düzenlileştirme anlamına gelir.

## 60.4 Menteşe kaybı: SVM'yi bir kayıp fonksiyonu olarak okumak

Yumuşak marj probleminde gevşeklik `ξᵢ`, optimizasyonda serbest bir değişkendir. Ama amaç fonksiyonu içinde bir kez yerine konunca, `ξᵢ` için en iyi değer kendiliğinden ortaya çıkar. `yᵢ(wᵀxᵢ + b) ≥ 1 − ξᵢ` koşulunu sağlayan en küçük `ξᵢ ≥ 0` değeri

`ξᵢ = max(0, 1 − yᵢ(wᵀxᵢ + b))`

dir. Bu ifade, `zᵢ = yᵢ f(xᵢ)` ile yazılır, `f(x) = wᵀx + b`. Böylece SVM, `ξ`'yi ortadan kaldırıp tek bir kayıp fonksiyonuna indirgenir:

`minimize ½‖w‖² + C · Σᵢ max(0, 1 − yᵢ f(xᵢ))`

İkinci terim, menteşe kaybı (hinge loss) olarak bilinir: `ℓ(z) = max(0, 1 − z)`. Bu, Bölüm 58'deki lojistik kayıptan farklı bir kayıptır. Eğer her iki tarafı `C·n` ile bölersek, `λ = 1/(C·n)` tanımıyla

`minimize (λ/2)‖w‖² + (1/n) Σᵢ max(0, 1 − yᵢ f(xᵢ))`

biçimine gelir. Bu, Bölüm 58'de gördüğümüz düzenlileştirmeli kayıp biçiminin aynısıdır: bir ortalama kayıp artı bir L2 cezası. Farkı tek bir kayıp fonksiyonunda görelim.

Bu karşılaştırmayı Bölüm 58'deki lojistik regresyonla ve sınıflandırmanın ideal ama işe yaramayan kaybı olan 0-1 kaybıyla birlikte yapalım. Burada `z = y f(x)` çok önemlidir: `z > 0` doğru tahmin, `z < 0` yanlış tahmin demektir.

- 0-1 kaybı, `z < 0` iken 1, değilse 0'dır. Tam olarak istediğimiz şey budur, ama türevi yoktur ve dışbükey değildir; bu yüzden doğrudan optimize edilemez.
- Menteşe kaybı, `z ≥ 1` için tamamen 0'dır. Yani doğru tarafta ve marjın dışında kalan bir nokta hiçbir ceza üretmez. Bu özellik, çözümün yalnızca destek vektörlerine bağlı olmasının kaynağıdır. Menteşe kaybı dışbükeydir ve 0-1 kaybının dışbükey bir üst sınırıdır.
- Lojistik kayıp, `ln(1 + e^{−z})`, her noktaya bir ceza verir. Hiçbir zaman tam 0 olmaz, bu yüzden lojistik regresyonun çözümü bütün noktalara bağlıdır.
- Kare kayıp, `(1 − z)²`, regresyonda kullanılan karedir. Doğru ve marjın ötesinde olan noktaları da cezalandırır; sınıflandırma için iyi bir seçim değildir.

![Şekil 60.4: Menteşe kaybı, 0-1 kaybının dışbükey üst sınırıdır ve z ≥ 1 için sıfırdır](gorseller/b60_kayip_karsilastirma.png)

Şekil 60.4'te menteşe (kırmızı) `z = 1`'e kadar eğimli ve sonra sıfırdır. Bu kırılma noktasında menteşe kaybı türevlenebilir değildir. Bu nedenle gradyan inişinde bir alt-gradyan (subgradient) kullanılır; bu, Bölüm 50'de tanıttığımız gradyanın dışbükey fonksiyonlara uygulanan genelleştirilmiş hâlidir (genel bilgi). Lojistik kayıp (mavi) ise her yerde türevlenebilir ve `z` büyüdükçe üstel olarak küçülür; bu yüzden `z` değeri büyük olan noktalar bile çözüme az da olsa katkı verir.

Bu fark, SVM'in pratik davranışında önemli bir sonuç doğurur. Menteşe kaybı büyük `z` değerleri için tamamen sıfır olduğundan, eğitim kümesindeki çoğu nokta çözümü etkilemez. Lojistik regresyonda ise her nokta bir miktar etkilidir. SVM'in "seyrek" çözümü (sparse solution), yani az sayıda destek vektörü ile tanımlanması, buradan gelir.

::: ipucu
Lojistik regresyon ile SVM'in tek farkı kayıp fonksiyonu değildir. Lojistik regresyon olasılık üretir, SVM üretmez; SVM'in çıktısı `f(x)`, bir işaret ve bir büyüklüktür. Olasılık gerekiyorsa SVM'e ayrıca bir kalibrasyon eklemek gerekir (Bölüm 60.12).
:::


## 60.5 Birincil problemi alt-gradyan inişiyle çözmek

Menteşe kaybı ile yazılmış SVM amacını, Bölüm 50'deki gradyan inişiyle doğrudan çözebiliriz. Tek sorun, menteşe kaybının `z = 1` noktasında türevlenemez olmasıdır. Bu noktada bir alt-gradyan seçeriz: bir nokta marjın içindeyse (`yᵢ f(xᵢ) < 1`) onun katkısını hesaba katarız, değilse katkısı sıfırdır. Bu seçim, Bölüm 50'deki izdüşümlü gradyan fikriyle birlikte düşünüldüğünde, dışbükey bir problemde yakınsamayı garanti eder (genel bilgi).

Her adımda tüm veriyi kullanmak yerine rastgele tek bir nokta seçen stokastik sürüme Pegasos denir (Shalev-Shwartz ve arkadaşları, 2007; genel bilgi). Bizim sürümümüzde amaç `(λ/2)‖w‖² + (1/n) Σ menteşe` biçimindedir ve `λ = 1/(C·n)` dir. Bir `i` noktası seçildiğinde, aktif ise (`yᵢ(wᵀxᵢ + b) < 1`) gradyan şöyledir:

`∇_w = λw − yᵢxᵢ`, `∇_b = −yᵢ`

Aktif değilse, yalnızca `λw` terimi kalır. Adım büyüklüğü `η_t = 1/(λt)` seçilir ve güncelleme şöyle olur:

`w ← (1 − η λ) w + η yᵢ xᵢ` (yalnızca aktifse ikinci terim eklenir), `b ← b + η yᵢ` (yalnızca aktifse)

Pegasos'un bir başka parçası izdüşümdür: `‖w‖` değeri `1/√λ` yarıçaplı bir küreyi aşarsa `w` bu küreye geri çekilir. İlk adımlarda `η = 1/λ = C·n` olduğu için `w` çok büyük bir değere sıçrar; izdüşüm bu sıçramayı sınırlar.

Aşağıdaki kod, kitabın sıfırdan yazılan kütüphanesinin ilk parçasıdır. Dosyanın başındaki açıklama ve `import` satırı ile `pegasos_dogrusal` işlevi burada verilmiştir. Diğer işlevler sonraki alt bölümlerde gelecek ve dosya, bütün parçalar bir araya getirildiğinde tam olarak çalışır.

```python
# -*- coding: utf-8 -*-
"""Bolum 60 - SVM ve cekirdek yontemleri: sifirdan (NumPy).

Iceriik:
  pegasos_dogrusal : birincil problem, alt-gradyan (Pegasos benzeri)
  smo_basit        : basitlestirilmis SMO (dual problem, cekirdekli)
  rff_olustur, rff_donustur : rastgele Fourier oznitelikleri (RBF)
  krr_fit, krr_tahmin       : kernel ridge regresyonu (kapali form)
"""
import numpy as np


def pegasos_dogrusal(X, y, C, epoch=50, seed=0):
    """min (lam/2)|w|^2 + ortalama menteşe kaybi ; lam = 1/(C n).
    Bias (b) cezalandirilmaz. y in {-1, +1}."""
    n, d = X.shape
    lam = 1.0 / (C * n)
    R = 1.0 / np.sqrt(lam)              # Pegasos izdusum yaricapi
    rng = np.random.default_rng(seed)
    w = np.zeros(d)
    b = 0.0
    t = 0
    for _ in range(epoch):
        for i in rng.permutation(n):
            t += 1
            eta = 1.0 / (lam * t)
            aktif = y[i] * (X[i] @ w + b) < 1.0
            w = (1.0 - eta * lam) * w
            if aktif:
                w += eta * y[i] * X[i]
                b += eta * y[i]
            nrm = np.linalg.norm(w)
            if nrm > R:
                w *= R / nrm
    return w, b
```

İşlev bias `b`'yi düzenlileştirmez; `b` cezasız güncellenir. Bu, dual problemdeki eşitlik kısıtı `Σ αᵢ yᵢ = 0` ile tutarlıdır (Bölüm 60.6); iki çözümü aynı amaç üzerinden karşılaştırmak için bias'ı ayrıca düzenlileştirmedik.

Şimdi bu işlevi sklearn ile karşılaştıralım. Veri meme kanseri veri kümesidir (569 örnek, 30 öznitelik; `load_breast_cancer`). Her tohum için veri %70 eğitim ve %30 test olarak tabakalı bölünür (`stratify`), öznitelikler yalnızca eğitim kümesi üzerinde öğrenilen `StandardScaler` ile ölçeklenir. Amaç değeri, sklearn'in çözümü için hesaplanan değere göre yüzde olarak ölçülür. Tabloda bu fark "boşluk" olarak verilir.

```python
# ---- 4. Pegasos yakinsamasi (5 tohum) ----
C = 1.0
print("[4] Pegasos (meme kanseri, olcekli, C=1, 5 tohum)")
for ep in [50, 200, 1000, 3000]:
    gap, acc, sure = [], [], []
    for sd in range(5):
        Xtr, Xte, ytr, yte = train_test_split(
            Xb, yb, test_size=0.3, stratify=yb, random_state=sd)
        sc = StandardScaler().fit(Xtr)
        Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)

        def obj(w, b):
            return (0.5 * w @ w
                    + C * np.maximum(0,
                                     1 - ytr * (Xtr @ w + b)).sum())

        ref = SVC(kernel="linear", C=C, tol=1e-8).fit(Xtr, ytr)
        oref = obj(ref.coef_[0], ref.intercept_[0])
        t0 = time.time()
        w, b = pegasos_dogrusal(Xtr, ytr, C, epoch=ep, seed=sd)
        sure.append(time.time() - t0)
        gap.append(100 * (obj(w, b) - oref) / oref)
        acc.append(np.mean(np.sign(Xte @ w + b) == yte))
    print("  epoch=%d bosluk%%=%.3f+-%.3f test=%.4f+-%.4f sure=%.2fs"
          % (ep, np.mean(gap), np.std(gap), np.mean(acc),
             np.std(acc), np.mean(sure)))
```

Çıktı, Pegasos'un epoch sayısına göre nasıl yakınsadığını gösterir.

```term
[4] Pegasos (meme kanseri, olcekli, C=1, 5 tohum)
  epoch=50 bosluk%=12.041+-3.086 test=0.9661+-0.0094 sure=0.09s
  epoch=200 bosluk%=1.903+-0.494 test=0.9626+-0.0088 sure=0.34s
  epoch=1000 bosluk%=0.727+-0.275 test=0.9626+-0.0088 sure=1.66s
  epoch=3000 bosluk%=0.179+-0.019 test=0.9626+-0.0088 sure=5.05s
```

Tablo üç şey söylüyor. Birincisi, amaç değeri (boşluk) epoch sayısı arttıkça düşüyor: 50 epoch'ta yüzde 12 uzakta, 3000 epoch'ta yüzde 0,18 uzakta. Pegasos'un bu hızı, düzenli gradyan inişinden yavaştır; stokastik adım, her seferinde tek bir noktaya bakar ve gürültülüdür. İkincisi, test doğruluğu 0,9626 ile 0,9661 arasında hiç anlamlı değişmiyor. Üçüncüsü ve en önemlisi: 50 epoch'lık, amaç değerinden yüzde 12 uzak olan model, yakınsamış modelden daha yüksek test doğruluğuna sahip. Bu "daha iyi model" anlamına gelmez; test kümesi 171 örnekten oluşur ve 0,0035'lik fark, ortalama yaklaşık 0,6 örnektir; tohum sapması bunun çok üstündedir.

Bu sonuç, bir optimizasyon hatasını ölçmekle bir modelin kalitesini ölçmek arasındaki farkı gösterir. Amaç değerinin yakınsaması, tahmin doğruluğunun yakınsaması demek değildir. Bu yüzden deneylerde her zaman hem amaç değeri hem de test performansı raporlanmalıdır.

## 60.6 Dual problem: Lagrange, KKT ve SMO

Birincil problemi bir de dual biçiminde yazmak, SVM'i bu kadar güçlü kılan şeyi açığa çıkarır. Hard marj için Lagrange fonksiyonu (Bölüm 50'deki kısıtlı optimizasyon) şöyledir:

`L(w, b, α) = ½‖w‖² − Σᵢ αᵢ [yᵢ(wᵀxᵢ + b) − 1]`, burada `αᵢ ≥ 0`.

`w` ve `b`'ye göre türevleri sıfıra eşitlemek iki koşul verir:

`w = Σᵢ αᵢ yᵢ xᵢ` ve `Σᵢ αᵢ yᵢ = 0`.

İlk koşul, `w`'nin eğitim noktalarının doğrusal bir bileşimi olduğunu söyler. Bunu Lagrangian'a geri yerleştirirsek dual problemi elde ederiz:

`maximize Σᵢ αᵢ − ½ Σᵢ Σⱼ αᵢ αⱼ yᵢ yⱼ (xᵢᵀxⱼ)`, koşullar: `αᵢ ≥ 0` ve `Σᵢ αᵢ yᵢ = 0`.

Yumuşak marj için tek fark, her `αᵢ`'nin üstten `C` ile sınırlanmasıdır: `0 ≤ αᵢ ≤ C`. Bu kutu kısıtı, `C` parametresinin dual karşılığıdır.

Dual problemin üç özelliği bu bölümün geri kalanını belirler.

Birincisi, veri yalnızca `xᵢᵀxⱼ` iç çarpımları olarak görünür. Bu iç çarpımları bir matriste topladığımızda, Bölüm 48'deki Gram matrisi `G` elde edilir: `Gᵢⱼ = xᵢᵀxⱼ`. Dual problem tamamen `G` ile ifade edilebilir. Bu gözlem, çekirdek hilesinin kapısıdır: `xᵢᵀxⱼ` yerine başka bir iç çarpım koyarsak, örtük olarak başka bir öznitelik uzayında çalışmış oluruz (Bölüm 60.7).

İkincisi, Karush–Kuhn–Tucker (KKT) koşulları tamamlayıcı gevşekliği verir: `αᵢ [yᵢ f(xᵢ) − 1] = 0`. Bu, bir noktanın ya `αᵢ = 0` (marjın dışında, çözüme katkısı yok) ya da `yᵢ f(xᵢ) = 1` (marjın üzerinde) olduğunu söyler. Yani `αᵢ > 0` olan noktalar tam olarak destek vektörleridir. Yumuşak marjda KKT şöyle okunur: `αᵢ = 0` ise `yᵢ f(xᵢ) ≥ 1`; `0 < αᵢ < C` ise `yᵢ f(xᵢ) = 1`; `αᵢ = C` ise `yᵢ f(xᵢ) ≤ 1`. Son durum, marjın içinde ya da yanlış tarafta kalan noktaları, yani gevşekliği olan noktaları tanımlar.

Üçüncüsü, karar fonksiyonu da yalnızca destek vektörlerini kullanır:

`f(x) = Σᵢ αᵢ yᵢ (xᵢᵀx) + b`

Eğitim kümesinin büyük bölümü, `αᵢ = 0` olduğu için toplamda yer almaz. Bu, SVM'in bellekte ve tahminde verinin yalnızca küçük bir kısmını tutmasının nedenidir.

Dual problem bir QP'dir ve `n` değişkene sahiptir. Genel bir QP çözücüsü, `n` büyüdükçe pahalıdır. SMO (Sequential Minimal Optimization) bu sorunu, her adımda yalnızca iki `α` değişkenini güncelleyerek çözer. Bu fikir Platt'ın 1998 makalesine dayanır (genel bilgi).

İki değişkeni neden birlikte güncelleriz? Çünkü `Σ αᵢ yᵢ = 0` eşitlik kısıtı yüzünden tek bir `αᵢ`'yi tek başına değiştiremeyiz: değişirse toplam bozulur. Bir çift `(αᵢ, αⱼ)` seçersek, kısıt, bu iki değişkenin toplamını ya da farkını sabit tutar ve tek boyutlu bir problem kalır. Bu tek boyutlu problem kapalı formda çözülür ve sonra kutu sınırlarına `[L, H]` kırpılır.

Her adımda `E_k = f(x_k) − y_k` hatasını kullanırız ve iki değişken için şu büyüklükleri hesaplarız. Kodda `η` adı verilen büyüklük `2K_ij − K_ii − K_jj` dir ve pozitif yarı tanımlı bir çekirdekte negatif ya da sıfırdır (Bölüm 60.8'de Mercer koşulunu göreceğiz). Pozitif tanımlı yazılmış `η' = K_ii + K_jj − 2K_ij = −η` ile aynı güncelleme `α_j ← α_j + y_j (E_i − E_j) / η'` biçimindedir. Güncelleme sonrası `α_i`, kısıtı koruyacak şekilde `α_i ← α_i + y_i y_j (α_j^eski − α_j^yeni)` ile bulunur. Son olarak `b`, güncellenen değişkenlerden biri sınırda değilse oradan hesaplanır.

Aşağıdaki kod, basitleştirilmiş SMO'yu tanımlayan işlevin ilk yarısıdır. Bu fonksiyon, basitleştirilmiş bir SMO'dur: birinci `i` seçimi, KKT'yi ihlal eden bir noktadan yapılır; ikinci `j` rastgele seçilir. Platt'ın özgün yöntemi `j` için daha akıllı bir heuristik kullanır; burada onu bilerek kullanmadık, çünkü algoritmanın özü için gerekli değildir.

```python
def smo_basit(K, y, C, tol=1e-3, max_pas=10, seed=0):
    """Basitlestirilmis SMO (Platt 1998'in sadelestirilmis hali).
    K: n x n cekirdek (Gram) matrisi, y in {-1,+1}.
    Dondurur: alpha (n,), b."""
    n = len(y)
    alpha = np.zeros(n)
    b = 0.0
    rng = np.random.default_rng(seed)
    pas = 0
    while pas < max_pas:
        degisen = 0
        for i in range(n):
            Ei = (alpha * y) @ K[:, i] + b - y[i]
            if not ((y[i] * Ei < -tol and alpha[i] < C) or
                    (y[i] * Ei > tol and alpha[i] > 0)):
                continue
            j = i
            while j == i:
                j = rng.integers(n)
            Ej = (alpha * y) @ K[:, j] + b - y[j]
            ai, aj = alpha[i], alpha[j]
            if y[i] != y[j]:
                L, H = max(0.0, aj - ai), min(C, C + aj - ai)
            else:
                L, H = max(0.0, ai + aj - C), min(C, ai + aj)
```

Fonksiyonun ikinci yarısı, `b` güncellemesini, kutu sınırlarını ve sonucu döndürmesini içerir.

```python
            if L == H:
                continue
            eta = 2 * K[i, j] - K[i, i] - K[j, j]
            if eta >= 0:
                continue
            aj_yeni = np.clip(aj - y[j] * (Ei - Ej) / eta, L, H)
            if abs(aj_yeni - aj) < 1e-5:
                continue
            ai_yeni = ai + y[i] * y[j] * (aj - aj_yeni)
            b1 = (b - Ei - y[i] * (ai_yeni - ai) * K[i, i]
                  - y[j] * (aj_yeni - aj) * K[i, j])
            b2 = (b - Ej - y[i] * (ai_yeni - ai) * K[i, j]
                  - y[j] * (aj_yeni - aj) * K[j, j])
            if 0 < ai_yeni < C:
                b = b1
            elif 0 < aj_yeni < C:
                b = b2
            else:
                b = 0.5 * (b1 + b2)
            alpha[i], alpha[j] = ai_yeni, aj_yeni
            degisen += 1
        pas = pas + 1 if degisen == 0 else 0
    return alpha, b
```

SMO'nun dualinin, sklearn'in libsvm çözücüsünün dual amacıyla aynı değere yakınsadığını görmek için aşağıdaki deneyi yapıyoruz. Veri ay (moons) kümesidir; 200 nokta, gürültü 0,25, tohum 0'dan 4'e. Çekirdek RBF'dir, `γ = 1`, `C = 1`. Dual amaç, `½ (α∘y)ᵀK(α∘y) − Σα` olarak hesaplanır; sklearn için `α`, `dual_coef_` değerlerinin mutlak değeridir.

```python
# ---- 5. Basit SMO ve sklearn (moons, gamma=1, C=1) ----
print("[5] SMO vs SVC(rbf)")
for sd in range(5):
    Xm, ym = make_moons(n_samples=200, noise=0.25, random_state=sd)
    ym = 2 * ym - 1.0
    K = rbf_kernel(Xm, gamma=1.0)
    al, bb = smo_basit(K, ym, 1.0, seed=sd)
    ref = SVC(kernel="rbf", gamma=1.0, C=1.0, tol=1e-6).fit(Xm, ym)
    a_sk = np.zeros(len(ym))
    a_sk[ref.support_] = np.abs(ref.dual_coef_[0])

    def dual(a):
        return 0.5 * (a * ym) @ K @ (a * ym) - a.sum()

    f_my = K @ (al * ym) + bb
    f_sk = ref.decision_function(Xm)
    isaret = np.mean(np.sign(f_my) == np.sign(f_sk))
    print("  t%d dual SMO=%.4f sk=%.4f SV=%d/%d isaret=%.3f"
          % (sd, dual(al), dual(a_sk), np.sum(al > 1e-8),
             len(ref.support_), isaret))
```

Çıktı şöyledir.

```term
[5] SMO vs SVC(rbf)
  t0 dual SMO=-46.7033 sk=-46.7034 SV=64/63 isaret=1.000
  t1 dual SMO=-42.2710 sk=-42.2720 SV=59/58 isaret=1.000
  t2 dual SMO=-44.4446 sk=-44.4447 SV=58/58 isaret=1.000
  t3 dual SMO=-38.6425 sk=-38.6440 SV=54/54 isaret=1.000
  t4 dual SMO=-36.7747 sk=-36.7776 SV=51/50 isaret=1.000
```

Dual amaç değerleri, SMO ve sklearn arasında 10⁻⁴ ile 10⁻³ arasında ayrılıyor; en büyük fark beşinci tohumda 0,0029'dur. Karar fonksiyonlarının işaretleri her tohumda tamamen aynıdır (isaret=1,000). Destek vektörü sayıları ise bazı tohumlarda bir fark gösteriyor (64'e karşı 63 ve 51'e karşı 50). Bu farkın kaynağını bu bölümde doğrulamadık. Olası nedenler, `α` için sıfır eşiği (10⁻⁸) ve SMO'nun durdurma toleransıdır; ama bu bir tahmindir, kesin değildir. Önemli olan, çözümün dual amacı ve karar işareti açısından sklearn ile uyuşmasıdır.

Çözümlü Örnek 4, bu SMO'nun tek bir adımını elle izler ve adımın sonucunun KKT koşullarını sağladığını gösterir.

::: baglanti
Dual problemdeki `Σ αᵢ yᵢ = 0` kısıtı, Bölüm 50'deki Lagrange çarpanı yönteminin doğrudan bir uygulamasıdır. KKT tamamlayıcı gevşekliği, Bölüm 50'deki kısıtlı optimizasyonda aktif ve pasif kısıtların ayrımıyla aynı mantığı kullanır. Dualite ve Lagrange türevinin ayrıntısı Bölüm 50'de vardır.
:::


## 60.7 Çekirdek hilesi: öznitelik eşlemesi ve iç çarpım

Şimdiye kadar sınırlarımız doğrusaldı. Gerçek veride bu yetmez. Bölüm 58'de doğrusal modelin sınırını, yani XOR ve iç içe halkalar gibi örnekleri, temel fonksiyonlarla aşmayı denemiştik. Burada aynı fikri, ama açık bir eşleme yapmadan, SVM ile uygulayacağız.

En açık örnek iç içe iki halkadır. Veri `make_circles` ile üretilmiş, iki eşmerkezli çemberden oluşan 300 noktadır (gürültü 0,05). İçteki çemberin noktaları bir sınıf, dıştaki çemberin noktaları diğer sınıftır. Bu veri iki boyutta doğrusal olarak ayrılamaz: hiçbir doğru iki çemberi ayıramaz.

Şimdi her noktayı üç boyuta taşıyalım: `φ(x₁, x₂) = (x₁, x₂, x₁² + x₂²)`. Üçüncü koordinat, noktanın merkeze uzaklığının karesidir. İçteki noktaların üçüncü koordinatı küçük, dıştakilerin büyüktür. Böylece `z = 0,4` gibi bir düzlem iki sınıfı ayırır. Bu, veriyi değiştirmeden, sadece öznitelik uzayında bir şey yapmakla mümkündür.

Aşağıdaki şekil bu eşlemeyi gösterir. Solda iki boyutlu veri, sağda üç boyutlu öznitelik uzayındaki aynı noktalar ve bir düzlem vardır.

![Şekil 60.5: İç içe halkalar 2B'de ayrılamaz; (x₁, x₂, x₁²+x₂²) uzayında düzlem ayırır](gorseller/b60_daire_esleme.png)

Bunu sayılarla da görelim. Aşağıdaki program, aynı veri üzerinde iki şey yapar. Birincisi, iki boyutlu ham veriyle lineer bir SVM eğitir; ikincisi üç boyutlu eşlemeyle. İki deneyin test doğruluğunu karşılaştırır. Aynı betik, polinom çekirdeğin açılımını da doğrular; bunu hemen sonra açıklayacağız.

```python
# ---- 6. Daire: 2B -> 3B ----
Xc, yc = make_circles(n_samples=300, factor=0.5, noise=0.05,
                      random_state=0)
yc = 2 * yc - 1.0
zc = Xc[:, 0] ** 2 + Xc[:, 1] ** 2
csv_yaz("b60_daire.csv", ["x1", "x2", "z", "y"],
        [[Xc[i, 0], Xc[i, 1], zc[i], int(yc[i])]
         for i in range(len(yc))])
A, B, cA, cB = train_test_split(Xc, yc, test_size=0.3,
                                stratify=yc, random_state=0)
m2 = LinearSVC(C=1.0, max_iter=20000).fit(A, cA)
ZA = np.c_[A, A[:, 0] ** 2 + A[:, 1] ** 2]
ZB = np.c_[B, B[:, 0] ** 2 + B[:, 1] ** 2]
m3 = LinearSVC(C=1.0, max_iter=20000).fit(ZA, cA)
print("[6] 2B test=%.3f  3B test=%.3f"
      % (np.mean(m2.predict(B) == cB), np.mean(m3.predict(ZB) == cB)))

# ---- 7. Polinom cekirdek: (x.z+1)^2 = phi(x).phi(z) ----
def phi(x):
    x1, x2 = x
    r2 = np.sqrt(2.0)
    return np.array([1, r2 * x1, r2 * x2, x1 * x1, x2 * x2,
                     r2 * x1 * x2])


rng = np.random.default_rng(1)
mf = 0.0
for _ in range(1000):
    x, z = rng.normal(size=2), rng.normal(size=2)
    mf = max(mf, abs((x @ z + 1) ** 2 - phi(x) @ phi(z)))
print("[7] maks fark = %.2e" % mf)
x, z = np.array([1., 2.]), np.array([3., -1.])
print("[7] k(x,z)=", (x @ z + 1) ** 2,
      " phi(x).phi(z)=", round(phi(x) @ phi(z), 10))
```

Çıktının ilgili satırları şöyledir.

```term
[6] 2B test=0.456  3B test=1.000
[7] maks fark = 1.42e-14
[7] k(x,z)= 4.0  phi(x).phi(z)= 4.0
```

İki boyutlu lineer SVM'in test doğruluğu 0,456'dır; bu, rastgele tahmine yakındır. Üç boyutlu öznitelik ile aynı model test kümesinde 1,000 doğruluğa ulaşıyor. Burada `LinearSVC` kullandık; sklearn'in varsayılanı karesel menteşe kaybıdır (`loss="squared_hinge"`), ama bu örnekte amaç yalnızca ayrılabilirliği göstermektir.

Bu fikir ilk bakışta pahalı görünüyor: öznitelik sayısı arttıkça eşleme büyür. Ama SVM dual formunda yalnızca iç çarpımlara ihtiyaç duyar. `φ(x)ᵀφ(z)` iç çarpımını doğrudan veren bir fonksiyon varsa, `φ`'yi hiç hesaplamadan dual problemi çözebiliriz. Bu fonksiyona çekirdek (kernel) denir: `k(x, z) = φ(x)ᵀφ(z)`.

Polinom çekirdek bunun en açık örneğidir. İki boyutlu `x` ve `z` için `k(x, z) = (xᵀz + 1)²` olsun. Açarak yazalım:

`(xᵀz + 1)² = (x₁z₁ + x₂z₂ + 1)²`
`= x₁²z₁² + x₂²z₂² + 2x₁x₂z₁z₂ + 2x₁z₁ + 2x₂z₂ + 1`

Bu açılım, şu altı bileşenli `φ` ile tam olarak eşleşir:

`φ(x) = (1, √2·x₁, √2·x₂, x₁², x₂², √2·x₁x₂)`

Gerçekten de `φ(x)ᵀφ(z)` her terimi verir: `√2x₁·√2z₁ = 2x₁z₁`, `√2x₁x₂ · √2z₁z₂ = 2x₁x₂z₁z₂` gibi. `√2` faktörü bu yüzden vardır: çapraz terim `x₁x₂` iki kez sayılmasın diye. Aynı çekirdek `d` boyutlu veri ve `p` dereceli polinom için `C(d+p, p)` boyutlu bir `φ` üretir; `d = 20`, `p = 3` için bu 1771'dir. Çekirdek ise yine yalnızca iki vektör arasında `d` çarpma ile hesaplanır.

Aşağıdaki kod ve çıktı, bu açılımın sayısal doğrulamasını yapar: 1000 rastgele çift için `(xᵀz + 1)²` ile `φ(x)ᵀφ(z)` arasındaki en büyük fark makine hassasiyeti düzeyindedir.

::: ipucu
Açılımı önce kâğıt üzerinde kendin yap, sonra aşağıdaki sayısal kontrolle karşılaştır. Sayıya güvenmek yerine açılımı çıkarabilmek, mülakatta asıl beklenen beceridir.
:::

Polinom için sayısal kontrolün sonucu, yukarıdaki çıktının son iki satırındadır: `k(x, z) = 4` ve `φ(x)ᵀφ(z) = 4` (x = (1, 2), z = (3, −1) için). Maksimum fark `1,42·10⁻¹⁴` tür; bu, kayan noktada yuvarlama hatasıdır.

Çekirdek hilesinin asıl değeri, `φ`'nin boyutundan bağımsız olmasıdır. Polinom çekirdekte açık eşleme `C(d+p, p)` boyuta çıkabilir, ama çekirdek değeri her zaman `d` çarpmayla hesaplanır. RBF çekirdeğinde ise `φ` sonsuz boyutludur; buna rağmen hesaplama yine tek bir uzaklıktır. Bu, bir sonraki alt bölümün konusudur.

## 60.8 Yaygın çekirdekler ve Mercer koşulu

Bir fonksiyonun çekirdek olabilmesi için her zaman bir `φ` eşlemesine karşılık gelmesi gerekir. Bunu doğrudan kontrol etmek kolay değildir, ama Mercer koşulu sonlu noktalar üzerinde kontrol edilebilecek bir ölçüt verir.

Bir `k` fonksiyonu ve `x₁, …, xₙ` noktaları için Gram matrisi `K` şöyle tanımlanır: `Kᵢⱼ = k(xᵢ, xⱼ)`. Mercer koşuluna göre `k` bir çekirdektir, ancak ve ancak her nokta kümesi için `K` simetrik ve pozitif yarı tanımlıdır (PSD). Bu, Bölüm 48'deki tanımın doğrudan uygulamasıdır: bütün özdeğerler sıfır ya da pozitif olmalıdır. (Mercer teoremi bunun sürekli fonksiyonlar için genel hâlidir; genel bilgi.)

Yaygın çekirdekler şunlardır:

| Çekirdek | Formül | Not |
|---|---|---|
| Doğrusal | `xᵀz` | Eşleme yok; `φ = x` |
| Polinom | `(γ xᵀz + r)^d` | Derece `d`; açılımı yukarıda gördük |
| RBF (Gauss) | `exp(−γ ‖x − z‖²)` | Sonsuz boyutlu `φ`; en yaygın |
| Sigmoid | `tanh(κ xᵀz + c)` | Bazı parametrelerde PSD değil (genel bilgi) |

RBF'nin neden bir çekirdek olduğu, bir Taylor açılımıyla görülebilir (genel bilgi). `exp(−γ‖x − z‖²) = exp(−γ‖x‖²) · exp(−γ‖z‖²) · exp(2γ xᵀz)` yazılır. Son çarpan, `xᵀz`'nin kuvvetlerinin toplamı olarak yazılır ve her kuvvet bir çekirdektir; pozitif yarı tanımlı çekirdeklerin toplamı ve çarpımı da çekirdektir. Dıştaki iki çarpan ise pozitif sabitlerle çarpmadır. Bu yüzden RBF bir çekirdektir ve `φ`'si sonsuz boyutludur.

Sigmoid çekirdeğin PSD olmadığı durumlar genel bilgidir; burada bunu kendimiz göstermiyoruz. Asıl ilgimiz, Mercer koşulunun bir çekirdeğin geçerli olup olmadığını nasıl gösterdiğidir.

Aşağıdaki deney beş nokta (0, 1, 2, 3, 4) için iki Gram matrisinin özdeğerlerini hesaplar: biri RBF (γ = 1), diğeri `−(x − z)²`. İkincisi, bir uzaklık ölçüsünün negatifi gibi görünür ama bir çekirdek değildir.

```python
# ---- 8. Mercer: Gram ozdegerleri ----
xs = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
Krbf = rbf_kernel(xs[:, None], gamma=1.0)
Kbad = -(xs[:, None] - xs[None, :]) ** 2
e1 = np.sort(np.linalg.eigvalsh(Krbf))[::-1]
e2 = np.sort(np.linalg.eigvalsh(Kbad))[::-1]
print("[8] RBF ozdegerler:", np.round(e1, 5))
print("[8] -(x-z)^2 ozdeger:", np.round(e2, 4) + 0.0)
print("[8] iz =", round(float(np.trace(Kbad)), 4))
csv_yaz("b60_mercer.csv", ["sira", "rbf", "gecersiz"],
        [[i + 1, e1[i], e2[i]] for i in range(len(xs))])
```

Çıktı şöyledir.

```term
[8] RBF ozdegerler: [1.65869 1.35871 0.97558 0.62297 0.38404]
[8] -(x-z)^2 ozdeger: [ 20.       3.0384   0.       0.     -23.0384]
[8] iz = 0.0
```

RBF Gram matrisinin özdeğerleri beşinin hepsi pozitiftir; en küçüğü 0,384'tür. Bu, Mercer koşulunun bu nokta kümesinde sağlandığını gösterir. `−(x − z)²` matrisinin özdeğerleri ise 20, 3,04, 0, 0 ve −23,04'tür. Negatif özdeğer, bu fonksiyonun bir çekirdek olmadığının kanıtıdır.

Bu kanıtı bir satırda görebilirsin: `−(x − z)²` Gram matrisinin köşegeni `k(xᵢ, xᵢ) = 0`'dır. Yani izi (trace) sıfırdır. Bir matris özdeğerlerinin toplamıdır; izi sıfır olan ve sıfır olmayan bir matrisin negatif özdeğeri olmak zorundadır. Matris pozitif yarı tanımlı olsaydı tüm özdeğerler sıfır ya da pozitif olurdu, toplamları sıfır olduğu için hepsi sıfır olurdu ve matris sıfır olurdu. Matris sıfır değil, bu yüzden bu bir çekirdek olamaz.

Şekil 60.6 iki matrisin özdeğerlerini yan yana gösterir.

![Şekil 60.6: Geçerli RBF çekirdeğinin özdeğerleri pozitif; geçersiz çekirdeğin bir özdeğeri negatiftir](gorseller/b60_mercer_ozdeger.png)

Bu kontrolün pratik önemi nedir? SVM'in dual problemi, `K` PSD olduğunda dışbükeydir. PSD olmayan bir `K` ile dual problem dışbükey değildir; çözücü yerel bir çözüme takılabilir ya da yakınsamayabilir (genel bilgi). Bu yüzden kendi yazdığın bir çekirdeği kullanmadan önce bu kontrolü yapmak, mülakatta ve projede kolay kazanılacak bir doğrulamadır.

## 60.9 RBF çekirdeği: γ ve C'nin birlikte etkisi

RBF çekirdeği `exp(−γ‖x − z‖²)` biçiminde yazılır ve iki noktanın birbirine ne kadar yakın olduğunu bir benzerlik olarak ölçer. Yakın noktalar 1'e, uzak noktalar 0'a yaklaşır. `γ` bu benzerliğin ne kadar hızlı azaldığını belirler. Kolaylık için `γ = 1/(2σ²)` yazılarak `σ` bir "genişlik" (bandwidth) olarak düşünülebilir: küçük `γ` (büyük `σ`) geniş bir etki alanı, büyük `γ` (küçük `σ`) dar bir etki alanı demektir.

Böylece iki hiperparametre vardır: `γ` ve `C`. `γ` sınırın ne kadar esnek olacağını, `C` ise hataya ne kadar ceza verileceğini belirler. Bu ikisi birlikte davranır: büyük `γ` ile büyük `C` birleşince model eğitim noktalarını ezberlemeye yatkın olur; küçük `γ` ile küçük `C` ise eksik uydurmaya (underfitting) yol açar.

sklearn'in `SVC` çağrısında `gamma="scale"` varsayılandır ve bu değer `1 / (n_features · X.var())` olarak hesaplanır. Bu, veri ölçeğine göre `γ`'yı kabaca doğru büyüklükte başlatmak için bir kolaylıktır; yine de ayarlanmalıdır.

Aşağıdaki deney, ay (moons) veri kümesinde `γ` için 0,1, 1, 10 ve `C` için 0,1, 1, 100 değerlerinin 3×3 ızgarasını dener. Her kombinasyon için karar sınırı, bir ızgara üzerinde değerlendirilir ve 5 tohum üzerinde eğitim ve test doğruluğu ortalaması alınır. Veri 200 nokta, gürültü 0,25 ve tohum 0'dır; her tohumda %70 eğitim ve %30 test olarak tabakalı bölünür.

```python
# ---- 9. RBF gamma x C izgarasi (moons) ----
Xm, ym = make_moons(n_samples=200, noise=0.25, random_state=0)
ym = 2 * ym - 1.0
A, B, cA, cB = train_test_split(Xm, ym, test_size=0.3,
                                stratify=ym, random_state=0)
with open(os.path.join("veri", "b60_moons.csv"), "w") as f:
    f.write("x1,x2,y,egitim\n")
    for X_, y_, e in [(A, cA, 1), (B, cB, 0)]:
        for (a, b), c in zip(X_, y_):
            f.write("%.4f,%.4f,%d,%d\n" % (a, b, int(c), e))
gx = np.linspace(-2.0, 3.0, 40)
gy = np.linspace(-1.5, 2.0, 40)
GX, GY = np.meshgrid(gx, gy)
grid = np.c_[GX.ravel(), GY.ravel()]
izg, skor = [], []
print("[9] RBF izgarasi (test: 5 tohum ortalamasi)")
for g in [0.1, 1.0, 10.0]:
    for Cv in [0.1, 1.0, 100.0]:
        m = SVC(kernel="rbf", gamma=g, C=Cv).fit(A, cA)
        f = m.decision_function(grid)
        izg += [[g, Cv, round(a, 4), round(b, 4), round(c, 4)]
                for (a, b), c in zip(grid, f)]
        tr, te = [], []
        for sd in range(5):
            P, Q, cP, cQ = train_test_split(
                Xm, ym, test_size=0.3, stratify=ym, random_state=sd)
            mm = SVC(kernel="rbf", gamma=g, C=Cv).fit(P, cP)
            tr.append(np.mean(mm.predict(P) == cP))
            te.append(np.mean(mm.predict(Q) == cQ))
        skor.append([g, Cv, round(np.mean(tr), 4),
                     round(np.mean(te), 4), round(np.std(te), 4),
                     m.n_support_.sum()])
        print("  g=%g C=%g egitim=%.3f test=%.3f+-%.3f SV=%d"
              % (g, Cv, np.mean(tr), np.mean(te), np.std(te),
                 m.n_support_.sum()))
csv_yaz("b60_rbf_izgara.csv", ["gamma", "C", "gx", "gy", "f"], izg)
csv_yaz("b60_rbf_skor.csv",
        ["gamma", "C", "egitim", "test_ort", "test_sd", "sv"], skor)
```

Çıktı şöyledir.

```term
[9] RBF izgarasi (test: 5 tohum ortalamasi)
  g=0.1 C=0.1 egitim=0.796 test=0.803+-0.046 SV=120
  g=0.1 C=1 egitim=0.833 test=0.820+-0.041 SV=72
  g=0.1 C=100 egitim=0.916 test=0.907+-0.040 SV=47
  g=1 C=0.1 egitim=0.874 test=0.887+-0.049 SV=100
  g=1 C=1 egitim=0.937 test=0.943+-0.027 SV=50
  g=1 C=100 egitim=0.949 test=0.930+-0.024 SV=26
  g=10 C=0.1 egitim=0.946 test=0.930+-0.027 SV=140
  g=10 C=1 egitim=0.951 test=0.933+-0.021 SV=75
  g=10 C=100 egitim=0.983 test=0.910+-0.020 SV=48
```

Tablo iki şeyi açıkça gösteriyor. Birincisi, en iyi test doğruluğu `γ = 1, C = 1` kombinasyonunda, 0,943 ± 0,027 değeridir. İkincisi, `γ = 10, C = 100` kombinasyonunda eğitim doğruluğu 0,983'e çıkarken test doğruluğu 0,910'a düşer: model eğitim kümesini ezberlemiştir. Aradaki fark, eğitim ve test arasındaki 0,07'lik boşluk, aşırı uydurmanın (overfitting) ölçüsüdür.

Dikkat edilmesi gereken bir şey daha var: `γ = 1` satırındaki üç C değeri arasındaki test farkları (0,887, 0,943, 0,930) tohum standart sapmalarından (0,024 ile 0,049) çok büyük değildir. Bu yüzden "en iyi" seçimi kesin değildir; hiperparametreleri seçmenin doğru yolu, Bölüm 57'deki iç içe çapraz doğrulamadır. Test kümesi, seçimden sonra yalnızca bir kez kullanılmalıdır.

Aşağıdaki şekil, 3×3 ızgaranın karar sınırlarını gösterir. Her panelin başlığındaki test değeri, 5 tohumun ortalamasıdır; sınır ise tohum 0'ın eğitim kümesinden çizilmiştir. Arka plan rengi sınıf tahminini, siyah çizgi `f(x) = 0` sınırını gösterir.

![Şekil 60.7: RBF'de küçük γ düz sınır, büyük γ ve büyük C ise aşırı kıvrımlı sınır üretir](gorseller/b60_rbf_izgara.png)

Şekil 60.7'de sol üst panel (γ = 0,1, C = 0,1) neredeyse düz bir çizgidir: eksik uydurma. Orta satır (γ = 1) iki sınıfı yumuşak bir eğriyle ayırır. Sağ alt panel (γ = 10, C = 100) ise en küçük nokta kümelerini bile çevreleyen kıvrımlı bir sınır çiziyor; bu, aşırı uydurmanın görsel hâlidir. Bu panelde destek vektörü sayısı 48'dir; sınır, bazı noktaların etrafında ayrı yuvalar açar.

## 60.10 Diğer çekirdek yöntemleri: kernel ridge, SVR, kernel PCA ve GP

SVM bir çekirdek yöntemidir, ama tek değildir. Çekirdek fikri, herhangi bir doğrusal yönteme uygulanabilir. Bunu en açık gösterebileceğimiz yöntem kernel ridge regresyonudur.

Bölüm 58'de doğrusal ridge regresyonunu, `Σ(yᵢ − wᵀxᵢ)² + λ‖w‖²` amacını minimize ederek görmüştük. Çekirdek sürümünde `f(x)` bir çekirdek fonksiyonu uzayında aranır ve bir temsil teoremi (representer theorem; genel bilgi), çözümün `f(x) = Σᵢ αᵢ k(xᵢ, x)` biçiminde olduğunu söyler. Eğitim noktalarında `f` değerleri `Kα` vektörüdür. Amaç `‖y − Kα‖² + λ αᵀKα` olur. Gradyanı sıfıra eşitlersek, `K` simetrik olduğu için

`Kᵀ(y − Kα) = λKα`, yani `K(Kα − y) + λKα = 0`, yani `K[(K + λI)α − y] = 0`

ve `λ > 0` olduğunda `(K + λI)` tersinir olduğundan çözüm kapalı formda bulunur:

`α = (K + λI)⁻¹ y`

Eğitim, `n × n` boyutlu bir doğrusal sistemi çözmektir; tahmin ise `f(x) = Σ αᵢ k(xᵢ, x)` hesabıdır. Bu yöntem, Bölüm 60.11'de göreceğimiz ölçeklenebilirlik sorununu paylaşır.

Aşağıdaki kod, bu kapalı formu sıfırdan uygular ve sklearn'in `KernelRidge` sınıfıyla karşılaştırır. Dosyanın bu parçası ayrıca, Bölüm 60.11'de kullanılacak rastgele Fourier öznitelik işlevlerini de içerir (onları orada kullanacağız).

```python
def rff_olustur(d, D, gamma, seed=0):
    """RBF cekirdegi icin D rastgele Fourier ozniteligi."""
    rng = np.random.default_rng(seed)
    W = np.sqrt(2.0 * gamma) * rng.normal(size=(d, D))
    b = rng.uniform(0.0, 2.0 * np.pi, size=D)
    return W, b


def rff_donustur(X, W, b):
    D = W.shape[1]
    return np.sqrt(2.0 / D) * np.cos(X @ W + b)


def krr_fit(K, y, lam):
    """Kernel ridge: alpha = (K + lam I)^-1 y (kapali form)."""
    n = K.shape[0]
    return np.linalg.solve(K + lam * np.eye(n), y)


def krr_tahmin(K_test, alpha):
    """K_test: (m x n) test-egitim cekirdek matrisi."""
    return K_test @ alpha
```

Kernel ridge kontrolü aşağıdaki deneydedir. 80 noktalı bir sinüs verisi, RBF çekirdeği (`γ = 0,5`) ve `λ = 0,1` ile iki yöntem de eğitilir.

```python
# ---- 10. Kernel ridge: sifirdan ve sklearn ----
rng = np.random.default_rng(0)
Xr = np.sort(rng.uniform(0, 6, 80))[:, None]
yr = np.sin(Xr[:, 0]) + 0.1 * rng.normal(size=80)
Kr = rbf_kernel(Xr, gamma=0.5)
al = krr_fit(Kr, yr, 0.1)
kr = KernelRidge(alpha=0.1, kernel="rbf", gamma=0.5).fit(Xr, yr)
print("[10] KRR max fark = %.2e"
      % np.abs(krr_tahmin(Kr, al) - kr.predict(Xr)).max())
```

Çıktı tek satırdır.

```term
[10] KRR max fark = 2.66e-15
```

Sıfırdan yazılan kapalı form ile sklearn'in sonuçları arasındaki en büyük fark `2,66·10⁻¹⁵`tir; yani ikisi aynı çözümü üretir. Kernel ridge, SVM'den farklı olarak tüm eğitim noktalarını çözüme katar (`α` seyrek değildir); bunun bedeli, tahminde her zaman `n` çekirdek değerlendirmesi yapmaktır.

Bu yöntemin SVM'in regresyon karşılığı, destek vektör regresyonudur (SVR). SVR, `ε`-duyarsız kayıp kullanır: `max(0, |y − f(x)| − ε)`. Bu kayıp, tahmin hedeften `ε` kadar uzaklaşana kadar ceza vermez; bu bir "boru" (tube) oluşturur. Boru içindeki noktalar çözüme katkı vermez ve destek vektörleri boru dışına çıkan noktalardır. Böylece SVR, sınıflandırmadaki seyrekliğini regresyona taşır (genel bilgi; sklearn'de `SVR` sınıfı).

Kernel PCA, Bölüm 61'deki temel bileşen analizinin çekirdek sürümüdür. Gram matrisi merkezlenir, özdeğer ayrışımı yapılır ve yüksek boyutlu eşlemenin doğrusal bileşenleri çıkarılır (genel bilgi). Bu yöntem, Bölüm 61'de PCA'yı öğrendikten sonra doğal bir uzantı olarak okunmalıdır.

Gauss süreçleri (GP), regresyonda Bayesçi bir yaklaşım sunar. Bir GP'nin ortalama tahmini, kernel ridge'in tahminiyle aynıdır; fark, GP'nin bir belirsizlik (varyans) de üretmesidir (genel bilgi). Bayesçi bakış Bölüm 62'de tam olarak ele alınacaktır.

## 60.11 Ölçeklenebilirlik: Gram matrisi, süre ve yaklaşımlar

Çekirdek yöntemlerinin ana zorluğu `n × n` Gram matrisidir. Her eleman 64 bit (8 bayt) ise bellek ihtiyacı `8n²` bayttır. `n = 8000` için bu 512 MB'dır. `n = 100 000` için ise 80 GB'a çıkar; bu, bir dizüstü bilgisayar belleğine sığmaz. Eğitim süresi de benzer biçimde büyür: çözücü tipik olarak `n²` ile `n³` arasında bir maliyetle çalışır (genel bilgi).

Aşağıdaki deney, sklearn'in `SVC(kernel="rbf")` ile eğitim süresini `n` değerine göre ölçer. Veri sentetiktir: 20 öznitelik, 10 bilgilendirici, tohum 0. Süreler medyan olarak alınır; `n ≤ 2000` için üç tekrar, büyük `n` için tek koşu yapılır. Log-log eğimi, süre ile `n` arasındaki üstel ilişkiyi tahmin eder: eğim 2 ise süre `n²` ile orantılıdır.

```python
# ---- 11. Egitim suresi ve n ----
print("[11] SVC(rbf) egitim suresi")
rows = []
for n in [500, 1000, 2000, 4000, 8000]:
    X, y = make_classification(n_samples=n, n_features=20,
                               n_informative=10, random_state=0)
    ts = []
    for _ in range(3 if n <= 2000 else 1):
        t0 = time.time()
        m = SVC(kernel="rbf", C=1.0, gamma="scale").fit(X, y)
        ts.append(time.time() - t0)
    rows.append([n, round(float(np.median(ts)), 4),
                 int(m.n_support_.sum()), round(8 * n * n / 1e6, 1)])
    print("  n=%d sure=%.4fs SV=%d Gram=%.1fMB" % tuple(rows[-1]))
ln_n = np.log([r[0] for r in rows])
ln_t = np.log([r[1] for r in rows])
print("  egim(tum)=%.3f egim(n<=4000)=%.3f"
      % (np.polyfit(ln_n, ln_t, 1)[0],
         np.polyfit(ln_n[:4], ln_t[:4], 1)[0]))
csv_yaz("b60_olcek_sure.csv", ["n", "sure_s", "sv", "gram_mb"], rows)
```

Çıktı şöyledir.

```term
[11] SVC(rbf) egitim suresi
  n=500 sure=0.0043s SV=299 Gram=2.0MB
  n=1000 sure=0.0165s SV=528 Gram=8.0MB
  n=2000 sure=0.0484s SV=760 Gram=32.0MB
  n=4000 sure=0.1500s SV=1177 Gram=128.0MB
  n=8000 sure=0.5621s SV=2208 Gram=512.0MB
  egim(tum)=1.725 egim(n<=4000)=1.693
```

Ölçülen eğim, tüm `n` aralığında 1,725 ve `n ≤ 4000` aralığında 1,693'tür. Yani süre, `n²` ile `n` arasında kalan bir hızda, pratikte kabaca `n^1,7` gibi artıyor. Bu, veri büyüdükçe eğitimin giderek pahalılaştığını gösterir. Süre değerleri makineye ve koşuya göre değişir; eğimi bu yüzden iki kez çalıştırıp aralığını bildirmek, tek bir sayıyı mutlak saymaktan daha dürüsttür.

Şekil 60.8 aynı ölçümü log-log ölçeğinde gösterir. Kesik çizgi eğim 2'yi, düz çizgi ölçülen eğimi gösterir.

![Şekil 60.8: RBF SVM eğitim süresi n arttıkça yaklaşık n^1,7 hızında artar; referans n² ile kıyaslanmıştır](gorseller/b60_olcek_sure.png)

Büyük veride üç yol vardır. İlki doğrusal SVM'dir: dual yerine doğrudan birincil problem (Pegasos, Bölüm 60.5) ya da doğrusal çözücüler (liblinear) kullanılır; maliyet örnek sayısında doğrusaldır (genel bilgi). İkincisi, çekirdeği açıkça yaklaşıklamaktır: rastgele Fourier öznitelikleri (RFF) ve Nyström yöntemi. Üçüncüsü, sinir ağlarıdır (Bölüm 63 ve sonrası).

RFF, Rahimi ve Recht'in (2007) fikridir (genel bilgi). Teorem şudur: kaydırmaya bağlı bir çekirdeğin (örneğin Gauss) spektral yoğunluğu `p(ω)` ise, `ω ~ p` ile örneklenen `cos(ωᵀ(x − z))` ifadesinin beklenen değeri çekirdektir. Gauss çekirdeği için `ω ~ N(0, 2γI)`'dir. Pratikte `D` tane rastgele `ω` ve rastgele faz `b ~ U[0, 2π]` seçilir ve öznitelik

`z(x) = √(2/D) · cos(Wᵀx + b)`

olarak tanımlanır. Bu `z` ile `z(x)ᵀz(y)` iç çarpımı, RBF çekirdeğinin tarafsız bir tahmini olur. Artık RBF yerine bu `D` boyutlu öznitelikle doğrusal bir model eğitebiliriz.

Aşağıdaki iki kod parçası, bu fikri uygular ve ölçer. İlki çekirdek yaklaşım hatasını `D`'ye göre ölçer; ikincisi aynı öznitelikle sınıflandırma yapar.

```python
# ---- 12. Rastgele Fourier oznitelikleri ----
A, _, _, _ = train_test_split(Xb, yb, test_size=0.3,
                              stratify=yb, random_state=0)
sc = StandardScaler().fit(A)
Z = sc.transform(A)[:200]
gam = 1.0 / Z.shape[1]
Kex = rbf_kernel(Z, gamma=gam)
rows = []
print("[12] RFF yaklasim hatasi (en buyuk mutlak fark)")
for D in [5, 10, 25, 50, 100, 250, 500, 1000, 2000]:
    eb, es = [], []
    for sd in range(5):
        W, bb = rff_olustur(Z.shape[1], D, gam, seed=sd)
        Phi = rff_donustur(Z, W, bb)
        eb.append(np.abs(Phi @ Phi.T - Kex).max())
        rs = RBFSampler(gamma=gam, n_components=D, random_state=sd)
        P = rs.fit(Z).transform(Z)
        es.append(np.abs(P @ P.T - Kex).max())
    rows.append([D, round(np.mean(eb), 5), round(np.std(eb), 5),
                 round(np.mean(es), 5), round(np.std(es), 5)])
    print("  D=%d bizim=%.5f+-%.5f sk=%.5f+-%.5f" % tuple(rows[-1]))
csv_yaz("b60_rff.csv",
        ["D", "bizim_ort", "bizim_sd", "sklearn_ort", "sklearn_sd"],
```

Çıktı, `D` arttıkça yaklaşımın nasıl iyileştiğini gösterir.

```term
[12] RFF yaklasim hatasi (en buyuk mutlak fark)
  D=5 bizim=1.57119+-0.10559 sk=1.51674+-0.12634
  D=10 bizim=1.15617+-0.09566 sk=1.11617+-0.12519
  D=25 bizim=0.71087+-0.05451 sk=0.74316+-0.08997
  D=50 bizim=0.53532+-0.04238 sk=0.49938+-0.03707
  D=100 bizim=0.36005+-0.02637 sk=0.36381+-0.03047
  D=250 bizim=0.24141+-0.03248 sk=0.24291+-0.02561
  D=500 bizim=0.16438+-0.01716 sk=0.17200+-0.01556
  D=1000 bizim=0.10617+-0.00626 sk=0.12189+-0.01107
  D=2000 bizim=0.08803+-0.00981 sk=0.07902+-0.00809
```

Tablodaki "bizim" sütunu kendi NumPy gerçeklememizdir, "sk" sütunu sklearn'in `RBFSampler` sınıfıdır. İki sütun birbirine çok yakındır; bu, bizim gerçeklememizin doğru olduğunu gösterir. En büyük mutlak hata `D = 100`'de 0,36, `D = 1000`'de 0,106'dır. Bu, kabaca `1/√D` hızıyla düşmek demektir: 10 kat öznitelik, hatayı yaklaşık `√10 ≈ 3,2` kat azaltır (ölçüm 3,4). Bu bir gözlemdir; kesin bir yakınsama oranı değildir.

Şekil 60.9 bu hatayı log-log ölçeğinde gösterir. Kesik çizgi `c/√D` referansıdır.

![Şekil 60.9: RFF çekirdek hatası D ile yaklaşık 1/√D hızında düşer; kendi gerçeklememiz sklearn ile örtüşür](gorseller/b60_rff_hata.png)

Yaklaşımın sınıflandırmadaki etkisi aşağıdaki kodda ölçülür. Öznitelikler standartlaştırılmış meme kanseri verisi (eğitimde öğrenilen ölçekleme) üzerinde üretilir ve üzerine doğrusal bir SVM kurulur.

```python
        rows)
print("[12b] RFF ile siniflandirma (gamma=1/30)")
for D in [10, 50, 200, 1000]:
    acc = []
    for sd in range(5):
        A, B, cA, cB = train_test_split(Xb, yb, test_size=0.3,
                                        stratify=yb, random_state=sd)
        sc = StandardScaler().fit(A)
        A2, B2 = sc.transform(A), sc.transform(B)
        W, bb = rff_olustur(A2.shape[1], D, gam, seed=sd)
        m = LinearSVC(C=1.0, max_iter=20000).fit(
            rff_donustur(A2, W, bb), cA)
        acc.append(np.mean(m.predict(rff_donustur(B2, W, bb)) == cB))
    print("  D=%d test=%.4f+-%.4f" % (D, np.mean(acc), np.std(acc)))
ex = []
for sd in range(5):
    A, B, cA, cB = train_test_split(Xb, yb, test_size=0.3,
                                    stratify=yb, random_state=sd)
    sc = StandardScaler().fit(A)
    ex.append(np.mean(SVC(kernel="rbf", gamma=gam, C=1.0)
                      .fit(sc.transform(A), cA)
                      .predict(sc.transform(B)) == cB))
print("  tam RBF SVC test=%.4f+-%.4f" % (np.mean(ex), np.std(ex)))
```

Çıktı şöyledir.

```term
[12b] RFF ile siniflandirma (gamma=1/30)
  D=10 test=0.8667+-0.0226
  D=50 test=0.9392+-0.0218
  D=200 test=0.9567+-0.0176
  D=1000 test=0.9696+-0.0086
  tam RBF SVC test=0.9661+-0.0094
```

`D = 10` ile doğruluk 0,867'de kalır; `D = 50` ile 0,939 ve `D = 200` ile 0,957'ye çıkar. `D = 1000` ile RFF tabanlı model 0,970 ± 0,009 doğruluk verir; tam RBF SVM ise 0,966 ± 0,009. Aradaki fark tohum sapmasının içinde kalır. Yani bu veride `D = 1000` yeterli görünüyor.

Nyström yöntemi, RFF'ye alternatif bir yaklaşımdır: eğitim noktalarının bir alt kümesi (landmark) seçilir ve Gram matrisi bu alt küme üzerinden yaklaşıklanır (genel bilgi). sklearn'de `Nystroem` sınıfı bunu yapar. Bu bölümde Nyström'ü uygulamadık; kavramını ve maliyet farkını bilmen yeterlidir.

::: mulakat
Bu bölümde iki yaklaşım eşdeğer amaçlar taşıyor: RFF ile çekirdeği taklit etmek ve dual ile tam çözmek. Hangisi ne zaman tercih edilir? Yanıtında hem bellek hem de tahmin maliyetini hesaba kat.
:::

## 60.12 Pratik: ölçekleme, çok sınıf, olasılık ve dengesiz sınıflar

Bir SVM'i gerçek veriyle kullanmadan önce dört konu netleşmelidir: ölçekleme, çok sınıflı sınıflandırma, olasılık çıktısı ve dengesiz sınıflar.

Ölçekleme en kritik olanıdır. RBF çekirdeği `‖x − z‖²`ye dayanır; büyük varyanslı bir öznitelik bu uzaklığı tek başına belirler. Bölüm 56'da öğrendiğimiz ölçeklemeyi burada zorunlu olarak uygularız: öğrenme yalnızca eğitim kümesinden yapılmalı, sonra test kümesine uygulanmalıdır (Bölüm 54'teki veri sızıntısı ilkesi).

Aşağıdaki deney, meme kanseri verisinde RBF SVM'i ölçeklenmemiş ve ölçeklenmiş öznitelikle 10 tohumda karşılaştırır. Ölçekleyici her tohumda yalnızca eğitim kümesinden öğrenilir.

```python
# ---- 13. Olcekleme etkisi (RBF SVC, 10 tohum) ----
ham, olc = [], []
for sd in range(10):
    Xtr, Xte, ytr, yte = train_test_split(
        Xb, yb, test_size=0.3, stratify=yb, random_state=sd)
    ham.append(np.mean(SVC(C=1).fit(Xtr, ytr).predict(Xte) == yte))
    sc = StandardScaler().fit(Xtr)
    olc.append(np.mean(SVC(C=1).fit(sc.transform(Xtr), ytr)
                       .predict(sc.transform(Xte)) == yte))
print("[13] olceksiz=%.4f+-%.4f olcekli=%.4f+-%.4f"
      % (np.mean(ham), np.std(ham), np.mean(olc), np.std(olc)))
csv_yaz("b60_olcekleme.csv", ["tohum", "olceksiz", "olcekli"],
        [[s, round(ham[s], 4), round(olc[s], 4)] for s in range(10)])

# ---- 14. Rakamlar: OvO (SVC) vs OvR (LinearSVC) ----
dg = load_digits()
A, B, cA, cB = train_test_split(dg.data, dg.target, test_size=0.3,
                                stratify=dg.target, random_state=0)
sc = StandardScaler().fit(A)
A, B = sc.transform(A), sc.transform(B)
svc = SVC(kernel="rbf", C=1.0, gamma="scale").fit(A, cA)
lsv = LinearSVC(C=1.0, max_iter=20000).fit(A, cA)
print("[14] SVC(rbf) test=%.4f  LinearSVC(OvR) test=%.4f"
      % (np.mean(svc.predict(B) == cB),
         np.mean(lsv.predict(B) == cB)))
print("  ikili siniflandirici: OvO=45, OvR=10")
```

Bu bloğun ilk kısmı ölçeklemeyi, ikinci kısmı çok sınıflı rakamlar verisini (`load_digits`, 10 sınıf) ele alır. Çıktı şöyledir.

```term
[13] olceksiz=0.9158+-0.0136 olcekli=0.9690+-0.0120
[14] SVC(rbf) test=0.9815  LinearSVC(OvR) test=0.9481
  ikili siniflandirici: OvO=45, OvR=10
```

Ölçeklenmemiş RBF SVM'in test doğruluğu 0,916 ± 0,014 iken ölçeklenmiş olan 0,969 ± 0,012'dir. 10 tohumda her tohum için bu fark pozitif yönde kalır. Şekil 60.10, tohumlar arasındaki eşleşmiş farkları gösterir.

![Şekil 60.10: Aynı tohumlarda ölçekleme test doğruluğunu tutarlı biçimde yükseltir](gorseller/b60_olcekleme_etki.png)

Çok sınıflı sınıflandırmada iki yaklaşım vardır. `SVC` (libsvm) bir "bire bir" (OvO, one-vs-one) stratejisi kullanır: her sınıf çifti için bir ikili SVM eğitir. 10 sınıf için bu `10·9/2 = 45` ikili sınıflandırıcıdır. `LinearSVC` (liblinear) ise "bire karşı kalan" (OvR, one-vs-rest) stratejisi kullanır: her sınıf için bir tane, toplam 10. Rakamlar veri kümesinde, tek bir bölmede, RBF SVC 0,982 doğruluk, OvR LinearSVC ise 0,948 verdi. Bu, yalnızca tek bölmeye dayanan bir karşılaştırmadır; OvO ile OvR arasındaki kesin farkı söylemek için tohumlu çapraz doğrulama gerekir (Bölüm 57). Yine de OvO'nun çok sınıfta daha az veriyle ikili problemler çözdüğünü, ama daha çok ikili model tuttuğunu bilmek önemlidir.

SVM'in doğrudan bir olasılık çıktısı yoktur. `f(x)`, bir işaret ve bir büyüklüktür; büyüklüğü olasılığa çevirmek için bir kalibrasyon gerekir. sklearn'de `SVC(probability=True)` bunu Platt ölçeklemesiyle yapar: bir sigmoid, karar değerlerine dahili 5 katlı çapraz doğrulamayla uydurulur (genel bilgi). Bu olasılıklar, `predict` tarafından verilen etiketle her zaman örtüşmeyebilir; bu sklearn belgelerinde de belirtilir. Kalibrasyonun nasıl ölçüleceği Bölüm 57'de anlatılmıştır.

Son olarak dengesiz sınıflar. `class_weight="balanced"` seçeneği, her sınıfın `C` değerini sınıf sıklığıyla ters orantılı olarak ölçekler. Aşağıdaki deney, %95 ve %5 oranında iki sınıflı bir veride lineer SVM'i bu seçenekle ve bu seçenek olmadan 5 tohumda karşılaştırır. Ölçüt, dengeli doğruluktur: her sınıfın geri çağırmasının (recall) ortalamasıdır. Bu ölçüt, çoğunluk sınıfını tahmin ederek elde edilen yüksek doğruluğu cezalandırır (Bölüm 57).

```python
# ---- 15. Dengesiz veri: class_weight ----
print("[15] dengesiz veri (95/5), lineer SVC, 5 tohum")
ba0, ba1, r0, r1 = [], [], [], []
for sd in range(5):
    X, y = make_classification(n_samples=3000, n_features=10,
                               weights=[0.95, 0.05], flip_y=0.01,
                               class_sep=0.8, random_state=sd)
    A, B, cA, cB = train_test_split(X, y, test_size=0.3,
                                    stratify=y, random_state=sd)
    sc = StandardScaler().fit(A)
    A, B = sc.transform(A), sc.transform(B)
    m0 = SVC(kernel="linear", C=1.0).fit(A, cA)
    m1 = SVC(kernel="linear", C=1.0,
             class_weight="balanced").fit(A, cA)
    ba0.append(balanced_accuracy_score(cB, m0.predict(B)))
    ba1.append(balanced_accuracy_score(cB, m1.predict(B)))
    r0.append(np.mean(m0.predict(B)[cB == 1] == 1))
    r1.append(np.mean(m1.predict(B)[cB == 1] == 1))
print("  agirliksiz dengeli=%.4f+-%.4f geri-cagirma=%.4f"
      % (np.mean(ba0), np.std(ba0), np.mean(r0)))
print("  balanced   dengeli=%.4f+-%.4f geri-cagirma=%.4f"
      % (np.mean(ba1), np.std(ba1), np.mean(r1)))
```

Çıktı şöyledir.

```term
[15] dengesiz veri (95/5), lineer SVC, 5 tohum
  agirliksiz dengeli=0.5786+-0.1337 geri-cagirma=0.1588
  balanced   dengeli=0.8670+-0.0439 geri-cagirma=0.8837
```

Seçenek olmadan dengeli doğruluk 0,579 ± 0,134'tür ve azınlık sınıfının geri çağırması yalnızca 0,159'dur: model azınlığı çoğunlukla kaçırıyor. `class_weight="balanced"` ile dengeli doğruluk 0,867 ± 0,044'e, geri çağırma 0,884'e çıkıyor. Bunun bedeli, çoğunluk sınıfında yanlış alarmların artmasıdır; hangi hatanın daha pahalı olduğunu bir maliyet analizi belirler (Bölüm 57 ve Bölüm 54'teki sınıf dengesizliği tartışması).

Son olarak, ne zaman SVM seçilir? Bu, genel bilgi ve deneyimle verilen bir yargıdır, kesin bir kural değildir. Orta büyüklükte (birkaç yüz ile birkaç on bin örnek), yüksek boyutlu, sınır net olduğu düşünülen veride SVM güçlü bir seçenektir ve geçmişte metin sınıflandırmada yaygın biçimde kullanılmıştır. Çok büyük veride (on binlerce örnekten sonra) çekirdekli SVM'in maliyeti, doğrusal modeller ya da sinir ağları karşısında dezavantaj olur. Tablo verisinde Bölüm 59'daki ağaç topluluklarının ve gradient boosting'in çoğu zaman daha iyi çalıştığı bilinir. Ham görüntü, ses ve dizi verisinde ise derin öğrenme (Bölüm 63 ve sonrası) baskındır. Bu karşılaştırmalar genel bilgidir; kendi verinde mutlaka aynı ölçütlerle dene.

## 60.13 Gömülü ve edge: çıkarımın bellek ve hesap bütçesi

Bir SVM'i eğitmek ile onu bir mikrodenetleyicide çalıştırmak farklı problemlerdir. Eğitim bilgisayarda yapılır; cihazda yalnızca tahmin yapılır. Bölüm 46'da TinyML için kurduğumuz bütçe mantığı burada da geçerlidir: her tahminin kaç çarpma, kaç bellek okuması ve kaç bayt gerektirdiğini hesaplarız.

Doğrusal SVM'in tahmini `f(x) = wᵀx + b` dir. `d` öznitelik için `d` çarpma ve `d` toplama yeterlidir. Model, `d + 1` sayıdan ibarettir. Bu, Bölüm 58'de gördüğümüz doğrusal modelin C'ye aktarımıyla aynıdır: yalnızca bir nokta çarpım ve bir eşikleme.

RBF SVM'in tahmini `f(x) = Σᵢ∈SV αᵢ yᵢ exp(−γ‖x − xᵢ‖²) + b` biçimindedir. Her destek vektörü için bir fark, bir kare toplamı ve bir üstel hesabı gerekir. Model, `n_SV · d` öznitelik değeri ve `n_SV` katsayı saklar.

Aşağıdaki bütçe hesabı, yukarıdaki deneyde ölçtüğümüz 8000 örnekli eğitimin sonucunu kullanır: 20 öznitelik, 2208 destek vektörü. Bellek float32 (4 bayt) varsayımıyla hesaplanmıştır.

| Model | Bellek (öğe sayısı) | Tahmin başına ana işlem |
|---|---|---|
| Doğrusal SVM (d = 20) | 21 | 20 çarpma, 20 toplama |
| RBF SVM (n_SV = 2208, d = 20) | 2208 · 20 + 2208 = 46 368 | 2208 · (yaklaşık 60 işlem + 1 üstel) |
| RFF + doğrusal (D = 1000, d = 20) | 20 · 1000 + 1000 + 1000 = 22 000 | 20 · 1000 çarpma, 1000 kosinüs |

RBF SVM için bellek yaklaşık `46 368 · 4 = 185 KB`tır; RFF modeli için `22 000 · 4 = 88 KB`tır. RBF tahmininin maliyeti destek vektörü sayısıyla orantılıdır: 2208 üstel hesabı, bir mikrodenetleyicide ciddi bir yük olabilir. Bu sayılar, kendi donanımında hesaplanmak üzere bir bütçe iskeletidir; ölçülmüş bir zamanlama değildir.

Cortex-M4F gibi bir işlemcide tek hassasiyetli kayan nokta birimi vardır, ama üstel fonksiyon donanımda yoktur; yazılım ya da tablo ile hesaplanır (genel bilgi). Bu yüzden destek vektörü sayısını azaltmak ya da çekirdeği RFF ile doğrusallaştırmak, gömülü uygulamada sık başvurulan çözümlerdir. RFF'nin maliyeti destek vektörü sayısından bağımsızdır; yalnızca `D` ile orantılıdır. Bu, Bölüm 46'daki TinyML ilkesinin, yani modeli cihazın bütçesine göre küçültmenin, çekirdek yöntemlerdeki karşılığıdır.

::: ipucu
Bir SVM'in destek vektörü sayısı, eğitimden sonra `model.n_support_` ile görülebilir. Gömülü hedef için bu sayı, RBF çekirdeğinde ilk bakılacak büyüklüktür.
:::


## Çözümlü Örnekler

Bu bölümdeki dört örnek, zorluk sırasıyla ★, ★★, ★★ ve ★★★ olarak dizilmiştir. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntüyü bul, iyileştir ve doğrula. Doğrulama adımında elle iz sürme tablosu bulunur. Her örneğin sonunda, hiçbir yapay zekâ aracı kullanmadan çözebilmen için bir varyasyon sorusu vardır. Örneklerdeki sayılar, yukarıdaki deney betikleriyle ve küçük ek kontrollerle doğrulanmıştır.

### Örnek 1 (★): Dört noktada en geniş marjlı doğru

Dört nokta veriliyor: pozitif sınıf `A = (2, 1)` ve `B = (2, 3)`, negatif sınıf `C = (0, 1)` ve `D = (−1, 0)`. Doğrusal ayrılabilir bu veride, marjı en geniş yapan doğruyu bul; destek vektörlerini, `w`'yi, `b`'yi ve marjı hesapla.

**Adım 1 — Anla.** İstenenler: karar sınırı `wᵀx + b = 0`, marjın değeri `2/‖w‖`, ve destek vektörleri. Normalizasyon olarak en yakın noktalarda `yᵢ(wᵀxᵢ + b) = 1` seçilmiştir.

**Adım 2 — Örnekle.** Noktalar kabaca iki kümeye ayrılmıştır: `x₁ = 2` çizgisinin sağında `A` ve `B`, solunda `C` ve `D`. `A` ile `B` aynı sınıftadır; `x₁` ekseninde aynı yerdedirler, ama `A` daha aşağıdadır. Sınıflar arasında en yakın çift, `A` (pozitif) ile `C` (negatif)'dir; yatay olarak 2 birim uzaktadırlar.

**Adım 3 — Kaba çöz.** Dikey bir doğru `x₁ = c` ile sınıfları ayırabilir. `c = 1`, iki yandan da eşit uzaklıkta olan adaydır. Bu doğru için `w = (1, 0)`, `b = −1` alırsak `y(wᵀx + b)` değerleri `A`, `B` ve `C` için tam olarak 1 olur. Marj `2/‖w‖ = 2` dir.

**Adım 4 — Örüntü.** Marjı belirleyen noktalar yalnızca `A` ve `C`'dir; `B` ve `D` marjın dışındadır. Bu nedenle, dual formda `α_A` ve `α_C` sıfırdan farklı, `α_B` ve `α_D` sıfırdır. KKT koşulu ile `w = Σ αᵢ yᵢ xᵢ = α(2, 1) − α(0, 1) = (2α, 0)` olur. `w = (1, 0)` için `α = 1/2` gerekir.

**Adım 5 — İyileştir.** Dual kontrolü yap: `Σ αᵢ yᵢ = 1/2 − 1/2 = 0` sağlanır. `‖w‖² = Σ αᵢ` eşitliği de sağlanmalıdır (`‖w‖² = 1` ve `Σ αᵢ = 1`). Bu iki koşul, `w`'nin doğru hesaplandığını hızlıca doğrular.

**Adım 6 — Doğrula.** Üç aday doğruyu karşılaştıralım. Her biri için `w` ve `b` normalize edilmiştir, yani `min yᵢ(wᵀxᵢ + b) = 1`.

| Aday | `w` | `b` | `yᵢ(wᵀxᵢ + b)` (A, B, C, D) | Marj `2/‖w‖` |
|---|---|---|---|---|
| `c = 0,5` | (2, 0) | −1 | 3, 3, 1, 3 | 1,0 |
| `c = 1,0` | (1, 0) | −1 | 1, 1, 1, 2 | 2,0 |
| `c = 1,5` | (2, 0) | −3 | 1, 1, 3, 5 | 1,0 |

Tabloda üç adayın da kısıtları sağladığı görülüyor; yalnızca `c = 1,0` marjı 2 yapıyor. Sonuç, deney betiğinin çıktısıyla birebir eşleşir: `w = [1, 0]`, `b = −1`, `marj = 2,0`, destek vektörleri `[2 0]` (yani `C` ve `A`).

**Bunu AI'sız yazabilir misin?** Dört nokta `A' = (3, 0)` (+1), `B' = (4, 2)` (+1), `C' = (1, 0)` (−1) ve `D' = (0, −1)` (−1) olsun. En geniş marjlı doğruyu, `w`'yi, `b`'yi ve destek vektörlerini bul. Ardından `w = Σ αᵢ yᵢ xᵢ` denklemiyle `α` değerlerini ve `Σ αᵢ` ile `‖w‖²` eşitliğini kontrol et.

### Örnek 2 (★★): Menteşe kaybında tek bir alt-gradyan adımı

Aynı dört nokta için birincil amaç `J(w, b) = ½‖w‖² + C Σᵢ max(0, 1 − yᵢ(wᵀxᵢ + b))` olsun, `C = 0,1`. Başlangıç `w₀ = (0,4, 0)`, `b₀ = 0`. Bir alt-gradyan adımı at ve `η = 0,1` ile `η = 0,5` için amacın nasıl değiştiğini karşılaştır.

**Adım 1 — Anla.** Hedef: `J`'nin bir adım sonra azalıp azalmadığını görmek. Her nokta için menteşe kaybı `max(0, 1 − yᵢ f(xᵢ))`dir; bir nokta "aktif"tir, yani kaybına katkı verir, eğer `yᵢ f(xᵢ) < 1` ise.

**Adım 2 — Örnekle.** `w₀ = (0,4, 0)` ile tüm dört nokta marjın içinde kalıyor: `yᵢ f(xᵢ)` değerleri 0,8, 0,8, 0 ve 0,4 gibi 1'in altında. Yani hepsi aktiftir ve gradyana katkı verir.

**Adım 3 — Kaba çöz.** Gradyan: `∇_w = w − C Σ yᵢ xᵢ` ve `∇_b = −C Σ yᵢ`. Aktif tüm noktalar için `Σ yᵢ xᵢ = (2, 1) + (2, 3) − (0, 1) − (−1, 0) = (5, 3)` ve `Σ yᵢ = 0`. Bu yüzden `∇_w = (0,4, 0) − 0,1·(5, 3) = (−0,1, −0,3)` ve `∇_b = 0`.

**Adım 4 — Örüntü.** Adım `w(η) = w₀ − η∇_w = (0,4 + 0,1η, 0,3η)` biçimindedir. Küçük `η` ile `J` azalmalıdır; büyük `η` ile bir nokta marjın dışına çıkıp aktif küme değiştiğinde `J` artabilir. Bu, alt-gradyan yönteminin temel uyarısıdır.

**Adım 5 — İyileştir.** Adımı `η = 0,1` ile dene: `w₁ = w₀ − η∇_w = (0,41, 0,03)`, `b₁ = 0`. Bu iki değeri hesapla ve sonucu `J` ile karşılaştır. Sonra aynı yönü `η = 0,5` ile dene.

**Adım 6 — Doğrula.** İz tablosu:

| Nokta | `y` | `f₀` (`w₀`) | `yf₀` | kayıp₀ | `f₁` (`η = 0,1`) | `yf₁` | kayıp₁ |
|---|---|---|---|---|---|---|---|
| A (2, 1) | +1 | 0,80 | 0,80 | 0,20 | 0,85 | 0,85 | 0,15 |
| B (2, 3) | +1 | 0,80 | 0,80 | 0,20 | 0,91 | 0,91 | 0,09 |
| C (0, 1) | −1 | 0,00 | 0,00 | 1,00 | 0,03 | −0,03 | 1,03 |
| D (−1, 0) | −1 | −0,40 | 0,40 | 0,60 | −0,41 | 0,41 | 0,59 |
| Toplam | | | | 2,00 | | | 1,86 |

`J₀ = ½·(0,4)² + 0,1·2,00 = 0,08 + 0,20 = 0,28`. `J₁ = ½·(0,41² + 0,03²) + 0,1·1,86 = 0,0845 + 0,186 = 0,2705`. `J` azaldı.

`η = 0,5` için `w = (0,45, 0,15)`; A ve B marjın dışına çıkıyor (`yf = 1,05` ve `1,35`), C ve D için kayıp toplamı 1,70. `J = ½·(0,45² + 0,15²) + 0,1·1,70 = 0,1125 + 0,17 = 0,2825`. Yani `J`, `0,28`den `0,2825`e çıktı: adım çok büyük.

Ders: alt-gradyan adımında öğrenme oranı küçük seçilmeli ve her adım sonrası amaç değeri kontrol edilmelidir.

**Bunu AI'sız yazabilir misin?** Aynı veri ve `w₀ = (0,4, 0)` ile `C = 0,1`, `η = 0,2` için `w₁` ve `J₁`'i hesapla. `J₁ < J₀` mı? Bu sonucu, yukarıdaki iz tablosu biçiminde yaz.

### Örnek 3 (★★): Polinom çekirdek açılımı ve elle eşleme

Polinom çekirdek `k(x, z) = (xᵀz + 1)²` ve iki boyutlu `x = (1, 2)`, `z = (3, −1)` veriliyor. Önce `k(x, z)` değerini doğrudan hesapla, sonra açılımdan çıkarılan `φ(x)` ve `φ(z)` ile `φ(x)ᵀφ(z)` değerini bul ve karşılaştır.

**Adım 1 — Anla.** Hedef: çekirdek değerini hem doğrudan hem de öznitelik eşlemesi üzerinden hesaplamak; iki yolun aynı sayıyı verdiğini göstermek.

**Adım 2 — Örnekle.** `x` ve `z` iki boyutludur. Çekirdek, iki vektörün iç çarpımına bir ekleyip karesini alır. Bu durumda derece 2 olduğu için eşleme, altı bileşenli bir vektör olacaktır (`C(2 + 2, 2) = 6`).

**Adım 3 — Kaba çöz.** `xᵀz = 1·3 + 2·(−1) = 1`. Yani `k(x, z) = (1 + 1)² = 4`.

**Adım 4 — Örüntü.** Açılım `(x₁z₁ + x₂z₂ + 1)²` ifadesinin her terimi bir çarpımdır. Bu nedenle `φ(x) = (1, √2·x₁, √2·x₂, x₁², x₂², √2·x₁x₂)` seçilmelidir. `√2` katsayıları çapraz terimi doğru saymak içindir.

**Adım 5 — İyileştir.** Hesabı tek satırda yapmak yerine, her bileşeni ayrı ayrı çarp ve toplayarak `k` ile karşılaştır. Bu, hata ayıklamanın da en kolay yoludur: yanlış bir terim tek bir satırda görünür.

**Adım 6 — Doğrula.** İz tablosu:

| Bileşen | `φ(x)` | `φ(z)` | Çarpım |
|---|---|---|---|
| 1 | 1 | 1 | 1 |
| 2 (`√2 x₁`, `√2 z₁`) | 1,414 | 4,243 | 6 |
| 3 (`√2 x₂`, `√2 z₂`) | 2,828 | −1,414 | −4 |
| 4 (`x₁²`, `z₁²`) | 1 | 9 | 9 |
| 5 (`x₂²`, `z₂²`) | 4 | 1 | 4 |
| 6 (`√2 x₁x₂`, `√2 z₁z₂`) | 2,828 | −4,243 | −12 |
| Toplam | | | 4 |

Toplam 4'tür ve `k(x, z) = 4`'e eşittir. Betiğin çıktısı da `k(x,z) = 4,0` ve `φ(x)ᵀφ(z) = 4,0` gösterir. Kendi kendine bir sınama olarak, aynı çekirdeği `z`'yi değiştirerek iki kez daha dene.

**Bunu AI'sız yazabilir misin?** `x = (2, 0)` ve `z = (1, 3)` için `k(x, z)`'yi doğrudan hesapla ve sonra aynı `φ` ile `φ(x)ᵀφ(z)`yi bul. İki sonucun aynı olduğunu iz tablosuyla göster.

### Örnek 4 (★★★): Basitleştirilmiş SMO'nun tek bir adımı

Aynı dört nokta, bu kez `C = 1` ve doğrusal çekirdek ile. Başlangıç `α = (0, 0, 0, 0)`, `b = 0`. SMO'nun ilk adımını elle yap: hangi çifti seçeceğini, `α`'ların nasıl güncelleneceğini ve `b`'nin değerini bul. Sonra KKT koşullarının sağlanıp sağlanmadığını kontrol et.

**Adım 1 — Anla.** Amaç: dual problemi iki değişkenli adımlarla çözmek, her adımda eşitlik kısıtı `Σ αᵢ yᵢ = 0`ı korumak ve kutu sınırı `0 ≤ α ≤ C`'yi uygulamak. Hedef, KKT koşullarının sağlandığı bir noktaya ulaşmaktır.

**Adım 2 — Örnekle.** Başlangıçta `f(x) = 0` olduğu için hata `E = f − y` değerleri `(−1, −1, +1, +1)` (A, B, C, D sırasıyla). KKT koşulunu ihlal eden nokta arasında `A`: `yᵢEᵢ = (+1)(−1) = −1 < −tol` ve `αᵢ = 0 < C`. Bu nedenle `i = A`. İkinci nokta `j` olarak `C` seçilir (SMO'da rastgele seçilir).

**Adım 3 — Kaba çöz.** Gerekli büyüklükler: `K_AA = 5`, `K_CC = 1`, `K_AC = 1`. Kodda kullanılan `η = 2K_AC − K_AA − K_CC = 2 − 5 − 1 = −4`. Kutu sınırları: `y_A ≠ y_C` olduğu için `L = max(0, α_C − α_A) = 0` ve `H = min(C, C + α_C − α_A) = 1`.

**Adım 4 — Örüntü.** `α_C^yeni = α_C − y_C (E_A − E_C) / η = 0 − (−1)(−2)/(−4) = 0,5`. Kutu içinde olduğu için kırpma gerekmez. `α_A^yeni = α_A + y_A y_C (α_C^eski − α_C^yeni) = 0 + (1)(−1)(0 − 0,5) = 0,5`. Eşitlik kısıtı: `0,5 − 0,5 = 0`.

**Adım 5 — İyileştir.** `b`'yi iki adayından hesapla: `b₁ = b − E_A − y_A Δα_A K_AA − y_C Δα_C K_AC = 0 + 1 − 2,5 + 0,5 = −1` ve `b₂ = b − E_C − y_A Δα_A K_AC − y_C Δα_C K_CC = 0 − 1 − 0,5 + 0,5 = −1`. İki aday aynı olduğu için `b = −1`.

**Adım 6 — Doğrula.** İz tablosu:

| Adım | İşlem | Değer |
|---|---|---|
| 1 | Başlangıç | `α = (0, 0, 0, 0)`, `b = 0`, `E = (−1, −1, 1, 1)` |
| 2 | İhlal ve çift | `i = A`, `j = C` |
| 3 | `η`, `L`, `H` | `η = −4`, `L = 0`, `H = 1` |
| 4 | Güncelleme | `α_C = 0,5`, `α_A = 0,5` |
| 5 | `b` | `b₁ = b₂ = −1` |
| 6 | Kontrol | `f = (1, 1, −1, −2)`, `yf = (1, 1, 1, 2)` |

Son satır KKT denetimidir: `A` ve `C`'nin `α`'sı sıfırdan büyük ve `yf = 1` (marj üzerinde), `B`'nin `α`'sı sıfır ve `yf = 1` (sınırda, kabul edilebilir), `D`'nin `α`'sı sıfır ve `yf = 2 ≥ 1` olduğu için bütün KKT koşulları sağlanır. Dual amaç `½(α∘y)ᵀK(α∘y) − Σα = −0,5`tir ve `α` değerleri, Bölüm 60.2'deki sklearn çözümünün `alpha*y` değerleriyle (`−0,5` ve `+0,5`) aynıdır. Yani tek bir SMO adımı, bu küçük problemi optimuma götürmüştür.

**Bunu AI'sız yazabilir misin?** Aynı dört noktada bu kez `i = B` ve `j = D` ile ilk adımı yap. `α_B`, `α_D` ve `b`'yi bul. (Yanıt: `α_B = α_D = 1/9`, `b = −2/3`.) Hangi kutu sınırının etkin olduğunu, hangi koşulun kırpmayı gerektirdiğini de söyle.


## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı kullanma. Kodu, testleri ve ölçümleri kendin yaz. Amaç, bu bölümdeki kavramları bir mülakatta ya da boş bir IDE'de yeniden kurabilmektir. Bir hata bulursan, önce hatayı kendin çöz; bu, bu bölümün en değerli kısmıdır.
:::

### Proje 1 (★★): Sıfırdan SVM kütüphanesi

**Amaç.** Bu bölümdeki dört yöntemi tek bir küçük kütüphanede topla: birincil problem için alt-gradyan (Pegasos), dual problem için basitleştirilmiş SMO, RBF için rastgele Fourier öznitelikleri ve kernel ridge. Her birini sklearn'in karşılığıyla karşılaştıran bir rapor üret.

**Yapılacak / Beklenen davranış.** Kütüphane, her model için `fit` ve `predict` işlevlerini sunsun. Doğrusal SVM için hem Pegasos hem de sklearn `SVC(kernel="linear")` çözümleri aynı veride karşılaştırılsın; amaç değeri farkı ve karar işaretlerinin uyumu raporlansın. Çekirdekli SVM için SMO çözümü sklearn `SVC(kernel="rbf")` ile aynı dual amaca ve aynı karar işaretlerine ulaşsın. Ayrıca, RFF öznitelikleriyle yaklaşılan Gram matrisinin hatası `D`'ye göre ölçülsün. Son olarak üç veri kümesinde (meme kanseri, rakamlar ve ay) test kümesinde karşılaştırmalı bir tablo üretilsin.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Önce bu bölümdeki `b60_sifirdan.py` dosyasının işlevlerini okumadan kendi sürümünü yazmayı dene, sonra karşılaştır. Pegasos'ta adım büyüklüğünü `1/(λt)` seçmenin neden ilk adımları çok büyüttüğünü ve izdüşümün bunu nasıl sınırladığını düşün. SMO'da ikinci değişkeni rastgele seçmek yerine hangi seçimin daha hızlı yakınsatacağını ölç. RFF için `D` ve tohum sayısını değiştirerek hatanın dağılımını raporla.

**Başarı kriterleri.** (1) Doğrusal SVM için Pegasos ile sklearn arasında amaç değeri farkı, en fazla yüzde bir olarak en az bir epoch sayısında raporlanmış olsun. (2) Çekirdekli SMO'nun dual amacı sklearn ile `10⁻²` tolerans içinde ve karar işaretleri tüm test noktalarında aynı olsun. (3) RFF hatası `D`'ye göre beş tohumla verilmiş ve ortalama ile sapması gösterilmiş olsun. (4) Karşılaştırma tablosunda her değer bir tohum ve bir bölme ile etiketlenmiş olsun. (5) Kütüphane aynı tohumla iki kez çalıştırıldığında aynı sayıları üretsin.

### Proje 2 (★★★): Sentetik İHA sensör imzası sınıflandırması

**Amaç.** Bir İHA'nın sensör telemetrisinden çıkarılan öznitelik vektörlerini "normal uçuş" ve "anomali" sınıflarına ayıran bir sınıflandırıcı kur. Veri tamamen sentetiktir; gerçek bir İHA verisi değildir ve bu, raporda açıkça yazılmalıdır. RBF SVM'i, rastgele ormanı (Bölüm 59) ve lojistik regresyonu (Bölüm 58) karşılaştır. SVM'in destek vektörü sayısından yola çıkarak gömülü bir çıkarım bütçesi çıkar.

**Yapılacak / Beklenen davranış.** Sabit tohumlu bir üreteçle 1500 uçuş penceresi üret. Her pencere için 12 öznitelik olsun: ortalama hız, hız varyansı, ivme genliği, batarya gerilimi eğilimi, iki sensör arasındaki tutarsızlık ölçüsü ve benzerleri. Anomaliler, bu özniteliklerin birkaçında bilinen bir kaymayla üretilsin ve azınlık sınıfı (%5 ile %10 arası) olsun. Veriyi bir test kümesine ayır. Eğitim kümesinde `γ` ve `C` için iç içe çapraz doğrulama (Bölüm 57) çalıştır; dış döngüden elde edilen tahminleri raporla. Seçilen RBF SVM'in destek vektörü sayısını bulup, Bölüm 60.13'teki tabloya benzer bir bellek ve tahmin bütçesi hesapla.

**Önerilen yaklaşım (ipucu).** Azınlık sınıfı için `class_weight` seçeneğini ve dengeli doğruluğu kullan; yalnızca doğruluk raporlama. Ölçeklemeyi her iç katta yalnızca eğitim kısmından öğren. Lojistik regresyon için olasılık çıktısını, SVM için karar fonksiyonunun değerini kullandığını unutma: iki modeli eşik değerinde karşılaştırmak adil olmayabilir; bunu nasıl düzelteceğini düşün. Gömülü bütçede, RBF'nin her tahminde kaç üstel hesabı gerektirdiğini ve bunun RFF ile nasıl değiştiğini hesapla.

**Başarı kriterleri.** (1) Veri üretimi sabit tohumla tekrarlanabilir ve sentetik olduğu raporda yazılı. (2) Dış çapraz doğrulama sonuçları üç modelin her biri için ortalama ve standart sapmayla verilmiş. (3) Dengeli doğruluk ve azınlık sınıfının geri çağırması, yalnızca doğruluk değil, raporlanmış. (4) Her bir modelin bir baseline (çoğunluk sınıfı tahmini) karşısında daha iyi olduğu ölçülmüş; olmuyorsa bunu açıkça yazmış. (5) SVM'in destek vektörü sayısı, bellek (bayt) ve tahmin başına işlem sayısı cinsinden bütçe tablosunda verilmiş. (6) Rapor, hangi modelin hangi koşulda seçileceğini gerekçelendirmiş.

### Ek Alıştırmalar

Aşağıdaki problemler kademelidir. ★ olanlar kavramı yoklar, ★★ olanlar bir türetme ya da küçük bir hesap ister, ★★★ olanlar birden çok konuyu birleştirir. Mülakat etiketli olanlar klasik sorulardır.

1. ★ Sert marjlı SVM'de bir destek vektörünün doğruya uzaklığını yazarak marj formülünün `2/‖w‖` olduğunu türet. (Mülakat)
2. ★ Tek boyutlu `(0, −1)`, `(2, +1)` ve `(5, +1)` noktaları için en büyük marjlı eşiği bul. Hangi noktalar marjı belirler ve neden?
3. ★ Menteşe kaybının `z = 1` noktasındaki alt-gradyan kümesini yaz. Bu küme, tek bir değer mi yoksa bir aralık mı?
4. ★★ Lojistik kayıp ile menteşe kaybının `z → ∞` davranışını karşılaştır. Hangisi çözümü seyrek yapar ve neden? (Mülakat)
5. ★★ `K = 1·1ᵀ` (her elemanı 1 olan `n × n` matris) bir çekirdek Gram matrisi olabilir mi? Özdeğerlerini bul ve Mercer koşulunu kontrol et.
6. ★★ Doğrusal çekirdek `k(x, z) = xᵀz` için dual karar fonksiyonunun `wᵀx + b` olarak yeniden yazılabildiğini, `w = Σ αᵢ yᵢ xᵢ` ile göster.
7. ★★ Gauss çekirdeğinde `γ → 0` ve `γ → ∞` limitlerinde Gram matrisinin nasıl davrandığını yaz. Bu iki uçta SVM neden başarısız olur? (Mülakat)
8. ★★ Kernel ridge'de `λ → 0` ve `λ → ∞` limitlerinde `α` ve eğitim noktalarındaki tahmin ne olur? Bunu `α = (K + λI)⁻¹y` ifadesinden göster. (Mülakat)
9. ★★★ SMO'da iki değişkenli adımın `η ≥ 0` çıkması ne anlama gelir? Bu durumun hangi çekirdek özelliğiyle bağlantılı olduğunu açıkla ve bu durumda adımın nasıl atlanacağını yaz.
10. ★★★ Rastgele Fourier öznitelikleri için `ω`'yı `N(0, 2γI)` yerine `N(0, γI)` ile seçersen hangi çekirdeği tahmin edersin? Beklenen değeri hesaplayarak göster.
11. ★ `n = 100 000` örnek için RBF Gram matrisinin float64 ile belleğini hesapla. Bu bellek, Bölüm 60.11'deki yaklaşımların neden gerekli olduğunu gösterir mi?
12. ★★★ Dengesiz bir ikili problemde pozitif örnekleri kopyalamak (oversampling) ile `class_weight="balanced"` arasındaki fark nedir? İkisi de tek bir `C` kullandığında hedef fonksiyonu nasıl etkiler? (Mülakat)

### Kod Okuma Egzersizi

Bu bölümde gerçek bir açık kaynak kesitini okuyacağız. Kaynak, scikit-learn 1.8.0 kurulumundaki `sklearn/kernel_approximation.py` dosyasıdır; `RBFSampler` sınıfının `fit` ve `transform` yöntemlerinden alınmıştır (fit satır 376–380, transform satır 408–412). Dosyanın yolu `Python312\Lib\site-packages\sklearn\` altındadır. Satırlar kitap genişliğine sığsın diye parantez içinde bölünmüştür; token dizisi ve anlam değişmemiştir. Kesit dışında kalan `gamma="scale"` hesabını (satır 370–375) bilerek atladık.

Fit yöntemi rastgele ağırlıkları ve fazı üretir:

```python
        self.random_weights_ = (
            (2.0 * self._gamma) ** 0.5
            * random_state.normal(
                size=(n_features, self.n_components)
            )
        )

        self.random_offset_ = random_state.uniform(
            0, 2 * np.pi, size=self.n_components
        )
```

Transform yöntemi, öznitelikleri hesaplar:

```python
        projection = safe_sparse_dot(X, self.random_weights_)
        projection += self.random_offset_
        np.cos(projection, projection)
        projection *= (2.0 / self.n_components) ** 0.5
        return projection
```

**Sorular — cevaplamadan geçme:**

1. `random_weights_` neden `N(0, 2γI)` dağılımından çekiliyor ve standart sapma neden `√(2γ)`? Bu seçimi, `E[cos(ωᵀΔ)] = exp(−γ‖Δ‖²)` ilişkisinden türet.
2. `random_offset_` neden `[0, 2π)` üzerinde düzgün dağılmıştır? Faz kaydırmanın beklenen değeri nasıl etkilemediğini düşün.
3. `np.cos(projection, projection)` ifadesinde çıktı, girdiyle aynı dizidir. Bu, bellek açısından ne kazandırır ve hangi durumda yanlış sonuç verebilir?
4. Ölçek faktörü `√(2/D)` neden gereklidir? `z(x)ᵀz(y)`nin beklenen değerinin `k(x, y)` olması için `D` ile nasıl ilişkilidir?
5. `transform` içindeki `X @ W` çarpımı `n × d` ile `d × D` matrisi arasındadır. Bu maliyeti Bölüm 60.13'teki bütçe tablosuyla karşılaştır: hangi koşulda RFF, RBF SVM'den daha ucuzdur?
6. sklearn'in `random_state` parametresi ile bu bölümdeki `seed` argümanı arasında sonuç farkı var mı? Aynı tohumla iki kez çalıştırmak aynı `W` ve `b` değerlerini verir mi, neden?

## Bölüm Özeti

- SVM, iki sınıf arasındaki marjı en geniş yapan doğruyu arar. Marj `2/‖w‖`dir; çözümü yalnızca destek vektörleri belirler.
- Yumuşak marj, gevşek değişkenler `ξ` ve `C` ile düzenlenir. Küçük `C` geniş marj ve çok hata, büyük `C` dar marj ve az hata üretir; doğru `C` çapraz doğrulamayla seçilir.
- Menteşe kaybı `max(0, 1 − yf)`, SVM'in amacını bir L2 düzenlileştirmeli kayıp olarak okumayı sağlar. Lojistik kayıptan farkı, `z ≥ 1` için sıfır olmasıdır; bu seyrekliğin kaynağıdır.
- Birincil problem alt-gradyan ile çözülebilir (Pegasos); amaç değeri yakınsasa da test doğruluğu her zaman buna paralel değişmez.
- Dual problem, verinin yalnızca iç çarpımlarla görünmesini sağlar. KKT tamamlayıcı gevşekliği, destek vektörlerini tanımlar. SMO, iki değişkenli adımlarla bu problemi çözer.
- Çekirdek hilesi, `k(x, z) = φ(x)ᵀφ(z)` ile açık eşlemeyi atlar. Geçerli bir çekirdek için Gram matrisi PSD olmalıdır; bu, Mercer koşuludur.
- RBF çekirdeği `γ` ve `C` ile birlikte ayarlanır; büyük `γ` ve büyük `C` aşırı uydurmaya yol açar. Bu hiperparametreler Bölüm 57'deki iç içe çapraz doğrulamayla seçilir.
- Çekirdek yöntemlerinin bellek maliyeti `n²` ile orantılıdır; eğitim süresi bu veride yaklaşık `n^1,7` hızında arttı. Rastgele Fourier öznitelikleri, RBF'yi `D` boyutlu doğrusal bir modele çevirir ve maliyeti destek vektörü sayısından ayırır.
- Pratikte ölçekleme zorunludur, çok sınıflı SVM OvO ile çalışır, olasılık için kalibrasyon gerekir ve dengesiz sınıflarda `class_weight` etkilidir.

**Sonraki bölümde:** Bölüm 61, Denetimsiz Öğrenme ile devam ediyor. Etiketsiz veride kümeleme (k-means, GMM ve EM), boyut azaltma (PCA ve kernel PCA'nın temeli) ve anomali tespiti göreceksin. Bu bölümde kısaca değindiğimiz kernel PCA, orada PCA'nın doğrusal temeli üzerine kurulacak.

::: mulakat
1. Marjı büyütmek neden `‖w‖`yi küçültmekle aynıdır? Bu ilişki, sert marjlı SVM'in amaç fonksiyonunda neden `½‖w‖²` biçiminde yazılır?
2. Menteşe kaybı ile lojistik kayıp arasında hangi davranış farkı, SVM'in çözümünü destek vektörleriyle sınırlar?
3. Dual problemde verinin yalnızca iç çarpımlar olarak görünmesi, kernel trick'i nasıl mümkün kılar? Hangi koşulda bir fonksiyonun gerçekten bir çekirdek olduğunu nasıl kontrol edersin?
4. RBF çekirdeğinde `γ`'yı büyütmek karar sınırını neden daha kıvrımlı yapar? Eğitim ve test hatası bu değişimle nasıl davranır?
5. SVM'in eğitim süresi neden veri sayısıyla hızlı büyür? Büyük veride doğrusal SVM ve rastgele Fourier öznitelikleri bu sorunu nasıl ele alır?
6. SVM'in çıktısı olasılık değildir. Bir SVM'e olasılık çıktısı eklemek için ne yaparsın ve bu adımın neden ayrı bir doğrulama gerektirdiğini açıkla.
7. Gömülü bir mikrodenetleyicide RBF SVM'i çalıştırmak neden zordur? Destek vektörü sayısı hangi bütçe kalemlerini belirler?
8. Dengesiz bir veride doğruluk neden yanıltıcıdır? `class_weight="balanced"` ile dengeli doğruluk arasındaki ilişkiyi açıkla.
:::

