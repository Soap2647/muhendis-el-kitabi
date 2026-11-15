%% kisim_no: XIV
%% kisim_ad: Makine Öğrenmesi
%% bolum_no: 62
%% baslik: Olasılıksal Modeller & Bayesçi ML

## Giriş: Belirsizliği bir sayıya değil, bir dağılıma çevirmek

Şimdiye kadarki makine öğrenmesi bölümlerinde modelin çıktısı genellikle tek bir sayıydı: bir doğrusal regresyonun tahmini, bir karar ağacının sınıfı, bir SVM'in karar değeri. Bölüm 57'de olasılık çıktısını ve kalibrasyonu gördün, ama bu bölümde soruyu tersine çeviriyoruz: model neyi bilmediğini nasıl söyleyebilir?

Bu soru savunma sanayiinde kuru bir akademik merak değildir. Bir İHA'nın radarından gelen menzil ölçümü her zaman gürültülüdür. Hedefin bir sonraki konumunu tek bir noktayla söylemek yerine "yaklaşık şu bölgede, şu yarıçapta" demek, takip sisteminin neden çalıştığını ve neden bazen yanıldığını anlatır. Bayesçi bakış bu belirsizliği açıkça modeller: önceden bildiğini (önsel, prior) veriyle birleştirip sonsal (posterior) dağılımı elde edersin. Bölüm 49'da bu kalıbı tek bir olasılık değeri üzerinde gördün; burada aynı kalıbı bir sınıflandırıcıya, bir ağa, bir zincire ve bir hareket modeline taşıyacağız.

Bölüm 62 kısım XIV'ün son bölümüdür. Naive Bayes ile başlayıp Bayes ağlarına, gizli Markov modellerine ve sonunda Kalman ve parçacık filtrelerine uzanır. Bu yöntemlerin ortak dili olasılıktır, ortak aracı ise Bayes kuralıdır. Hedef takibi ve sensör füzyonu, bu bölümün savunma sanayiindeki en somut uygulamasıdır: bir İHA'nın konumunu IMU ile GPS'i birleştirerek kestirmek, bir radarın gürültülü ölçümlerinden hedefin hızını ve yönünü çıkarmak.

Bu bölümde hiçbir kütüphanenin "tek satırlık" yöntemini körü körüne kullanmayacağız. Her yöntemi NumPy ile sıfırdan yazacak, sonra scikit-learn ya da FilterPy ile karşılaştıracaksın. Veriler iki türlüdür: yerleşik veri kümeleri (meme kanseri, Iris) ve sabit tohumla ürettiğimiz sentetik veriler. Sentetik olanlar metinde açıkça "sentetik" diye etiketlenmiştir; bir İHA'nın gerçek uçuş kaydı değildir.

::: not
Bu bölümdeki her deney, metinde verilen sabit tohumla yeniden üretilebilir. Kodlar kitapta tam olarak yer alıyor; çıktılar da o kodun gerçek çıktısıdır. Bir sayıyı görüp inanmak yerine, kodu kendi bilgisayarında çalıştırıp aynı sayıyı görmen bu bölümün beklediği alışkanlıktır.
:::

## 62.1 Belirsizliği modellemek: üretici ve ayırt edici yaklaşım

Bir sınıflandırma problemini iki farklı şekilde düşünebilirsin. Birincisi, verinin nasıl üretildiğini modellemektir: önce sınıfı seçersin, sonra o sınıfa bağlı özellikleri üretirsin. Bu, ortak dağılımı öğrenmek demektir: p(x, y). İkincisi, yalnızca sınıf verildiğinde ne olduğunu sorarsın: p(y | x). Birincisine **üretici (generative)** model, ikincisine **ayırt edici (discriminative)** model denir.

Bu ayrım bir benzetmeyle daha kolay oturur. Bir uzman bir kuşun türünü tanımak istiyor. Üretici yaklaşımda uzman her türün nasıl göründüğünü, nasıl uçtuğunu, hangi bölgede yaşadığını öğrenir ve yeni bir kuşu gördüğünde "bu tür bu özellikleri üretme olasılığı en yüksek olan tür" diye karar verir. Ayırt edici yaklaşımda uzman yalnızca iki tür arasındaki sınırı öğrenir ve kuşun hangi tarafta kaldığına bakar. İlk yaklaşım daha fazla şey bilir; ikincisi ise çoğu zaman sınır üzerinde daha iyi çalışır, çünkü tüm dünyayı modellemek zorunda değildir.

Bayes kuralı bu iki yaklaşımı birbirine bağlar. Üretici modelden başlayarak ayırt edici olasılığı şöyle yazarsın:

p(y | x) = p(x | y) p(y) / Σ_y' p(x | y') p(y')

Paydadaki toplam, sonucun 1'e normalize olmasını sağlar. Bölüm 49'da gördüğün taban oranı ve kanıt paylaşımı burada da aynıdır. Naive Bayes, bu formülde p(x | y) dağılımına bağımsızlık varsayımı ekleyerek üretici modelin en basit biçimidir. Lojistik regresyon (Bölüm 58) ise p(y | x) dağılımını doğrudan modeller ve p(x) hakkında hiçbir şey söylemez.

Şekil 62.1'de iki yaklaşımın veri akışı yan yana verilmiştir. Üretici yolda önce ortak dağılım öğrenilir ve Bayes kuralıyla koşullu olasılığa dönüşür; ayırt edici yolda koşullu olasılık doğrudan öğrenilir.

![Şekil 62.1: Üretici model (Bayes kuralıyla) ve ayırt edici model (doğrudan) karşılaştırması](gorseller/b62_uretici_ayirici.png)

Bu iki yaklaşımın pratik farkı az veride ve gerçek dünyada ortaya çıkar. Az veri olduğunda üretici model, dağılım hakkında yaptığı varsayımlar sayesinde daha hızlı öğrenebilir. Çok veri olduğunda ayırt edici model, yanlış bir dağılım varsayımına bağlı kalmadığı için genellikle daha iyi sonuç verir. Bölüm 62.2'de bu farkı deneyle göreceksin.

::: baglanti
Bölüm 49'daki Bayes teoremi bu bölümün her yerinde kullanılır. Naive Bayes'in olasılık hesabı, Bölüm 49'daki taban oranı probleminin çok özellikli hâlidir. Ayırt edici modellerin sınır mantığı için Bölüm 58'deki lojistik regresyona bak.
:::

## 62.2 Naive Bayes: koşullu bağımsızlık varsayımı

Bir e-postanın spam olup olmadığını düşün. Metinde yüzlerce kelime var. Bir e-postadaki her kelimenin spam olma olasılığını ayrı ayrı bilsek, bütün metnin olasılığını hesaplamak için ne kadar veriye ihtiyacımız olurdu? Kelimeler birbirine bağımlıdır: "bedava" kelimesinden sonra "kazan" gelmesi, "toplantı" kelimesinden sonra "saat" gelmesi gibi. Tüm kelime kombinasyonlarının olasılığını tahmin etmek, binlerce kelimeyle imkânsızdır.

Naive Bayes bu sorunu tek bir varsayımla çözer. Özellikler, sınıf verildiğinde **koşullu olarak bağımsızdır**:

p(x_1, ..., x_d | y) = Π_j p(x_j | y)

Bu varsayım gerçekçi değildir; "naive" (saf, safdil) sıfatı tam da bunu söyler. Ama etkisi büyüktür: d boyutlu bir ortak dağılım yerine d tane tek boyutlu dağılım tahmin edersin. Bu sayede az veriyle çalışabilir, sınıf başına her özellik için basit bir istatistik tutarsın.

Sınıflandırma kuralı, sınıf başına bir log-olasılık hesaplayıp en büyüğünü seçmektir:

ŷ = argmax_y [ log p(y) + Σ_j log p(x_j | y) ]

Çarpım yerine toplam kullanmamızın iki nedeni var. Birincisi, sayısal kararlılıktır: çok sayıda küçük olasılığı çarpmak, Bölüm 51'de gördüğün alt taşmaya (underflow) yol açar. İkincisi, toplam üzerinde çalışmak doğrusal cebirle (matris çarpımı) kolay hesaplanır. Kodda bunu hem Gauss hem multinomial sürümde göreceksin.

### Gauss naive Bayes: sürekli özellikler

Özellik sürekliyse (örneğin bir sensörden gelen sıcaklık), p(x_j | y) için bir Gauss dağılımı varsayarız: her sınıf ve her özellik için bir ortalama ve bir varyans. Eğitim, sınıf başına örnek ortalamasını ve varyansını hesaplamaktan ibarettir. Tahmin ise yukarıdaki formülde log-Gauss yoğunluğunu toplamaktır.

Aşağıdaki programın ilk parçası bu sınıfı kurar. Varyansa küçük bir sayı eklemek (`eps`) sıfıra yakın varyansla bölmeyi önler; bu, scikit-learn'ün `var_smoothing` parametresinin yaptığı işle aynıdır.

```python
# -*- coding: utf-8 -*-
# b62_01_nb.py: Naive Bayes sifirdan: Gauss ve multinomial,
# Laplace duzeltmesi, log-uzay, sklearn ile eslestirme, varsayim
# bozulmasi (kalibrasyon) ve NB / lojistik ogrenme egrisi.
import re
import numpy as np
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


# ---------- 1) Gauss naive Bayes (sifirdan) ----------
```

Sınıfın kalbi `fit` ve `joint_log` yöntemleridir. `fit` her sınıf için önseli ve Gauss parametrelerini hesaplar. `joint_log` ise log p(y) + log p(x | y) değerini her örnek ve sınıf için döndürür.

```python
class GaussNB:
    """Her sinif ve her ozellik icin Gauss; sklearn ile ayni varyans
    duzeltmesi (var_smoothing * max varyans)."""

    def fit(self, X, y):
        self.sinif = np.unique(y)
        eps = 1e-9 * X.var(axis=0).max()  # sklearn'deki epsilon_
        self.log_prior = np.log([np.mean(y == c) for c in self.sinif])
        self.mu = np.array(
            [X[y == c].mean(axis=0) for c in self.sinif]
        )
        self.var = (
            np.array([X[y == c].var(axis=0) for c in self.sinif])
            + eps
        )
        return self

    def joint_log(self, X):
        """log p(y) + sum_j log N(x_j; mu_yj, var_yj), boyut n x C."""
        out = []
        for k in range(len(self.sinif)):
            ll = (
                -0.5 * np.log(2 * np.pi * self.var[k])
                - 0.5 * (X - self.mu[k]) ** 2 / self.var[k]
            )
            out.append(self.log_prior[k] + ll.sum(axis=1))
        return np.column_stack(out)

    def predict(self, X):
        return self.sinif[np.argmax(self.joint_log(X), axis=1)]


```

Gauss sınıfını test etmek için meme kanseri veri kümesini (569 örnek, 30 özellik; scikit-learn ile birlikte gelir) kullanıyoruz. Sıfırdan yazdığımız sınıfın log-olasılıklarını scikit-learn'ün `predict_joint_log_proba` çıktısıyla karşılaştırıyoruz.

```python
def gauss_deney():
    X, y = load_breast_cancer(return_X_y=True)
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.3, random_state=62, stratify=y
    )
    mine = GaussNB().fit(Xtr, ytr)
    sk = GaussianNB().fit(Xtr, ytr)
    J1 = mine.joint_log(Xte)
    J2 = sk.predict_joint_log_proba(Xte)
    print("[Gauss] en buyuk log-fark:", float(np.abs(J1 - J2).max()))
    print(
        "[Gauss] dogruluk sifirdan:",
        round(float(np.mean(mine.predict(Xte) == yte)), 4),
    )
    print(
        "[Gauss] dogruluk sklearn :",
        round(float(np.mean(sk.predict(Xte) == yte)), 4),
    )


# ---------- 2) Multinomial NB ve Turkce metin ----------
```

### Multinomial naive Bayes ve metin sınıflandırma

Metin için özellik, kelime sayılarıdır. Bir belgeyi bir "kelime torbası" (bag of words) olarak temsil edersin: kelimenin sırası önemli değildir, yalnızca her kelimeden kaç tane olduğu sayılır. Multinomial NB, bu sayılar için bir kategorik dağılım varsayar: her sınıfın kelime olasılıkları θ_yw vardır ve bir belgenin log-olasılığı Σ_w x_w log θ_yw'dir. Bu, bir matris çarpımıyla hesaplanır.

Bu parametreleri eğitim verisinden tahmin etmek, sayım yapmaktır. Ama bir sorun vardır: eğitimde hiç görmediğin bir kelime, log(0) = −∞ üretir ve tek bir kelime bütün belgeyi "imkânsız" yapar. Çözüm **Laplace düzeltmesidir** (ya da genel adıyla ekleyici düzeltme, additive smoothing): her sayıma α eklersin.

θ_yw = (sayım(y, w) + α) / (Σ_w' sayım(y, w') + α V)

Burada V sözlük boyutudur. Bu formül, Bölüm 49'daki eşlenik önsel fikrinin çok terimli karşılığıdır: Beta–Bernoulli çiftinde önsel bir Beta dağılımıdır, çok terimli durumda ise Dirichlet önseli. α = 1 seçimi, her kelimeye bir "sahte gözlem" eklemek gibidir. Genel bilgi olarak: α'nın MAP yorumu bir Dirichlet önseline karşılık gelir.

Aşağıdaki kod, Türkçe bir mini külliyatla (kurgusal ve küçük, bir spam filtresi sadece mekanizmayı göstermek için) multinomial NB'yi sıfırdan yazar. Türkçe metinde bir ayrıntı önemlidir: büyük harf "İ" Python'da `lower()` ile birleşik bir noktalı i'ye dönüşür ve sözcüğü bozar. Bu yüzden önce "İ" ve "I" harflerini kendimiz düzeltiyoruz.

```python
SPAM_TRAIN = [
    "Tebrikler! Bedava hediye kazandınız, hemen tıklayın",
    "Ücretsiz kredi fırsatı yalnızca bugün geçerli",
    "Bedava bonus için hemen kaydol ve kazan",
    "Acil indirim! Bedava kargo için tıkla",
    "Ödülünüzü almak için hemen kaydolun",
    "Para kazanmanın en kolay yolu burada",
    "Sadece bugün özel fırsat, indirim tıkla",
    "Tebrikler, çekilişi kazandınız, ödül için kaydol",
    "Bedava kredi ve hediye için tıklayın",
    "İNDİRİM: bedava kargo, hemen kaydol",
]
NORMAL_TRAIN = [
    "Toplantı yarın saat onda başlıyor",
    "Proje raporunu cuma gününe kadar gönderir misin",
    "Yarın derse gelecek misin, notlar paylaşıldı",
    "Sunum dosyasını güncelledim, lütfen kontrol et",
    "Akşam yemeğe çıkalım mı",
    "Laboratuvar raporu için veri setini ekledim",
    "Hocanın ofis saati yarın öğleden sonra",
    "Kodu gözden geçirdim, birkaç yorum yazdım",
    "Vize sonuçları sisteme yüklendi",
    "Bu hafta sonu projeyi birlikte çalışalım",
]
SPAM_TEST = [
    "Bedava kredi için hemen tıkla",
    "Tebrikler, ödül kazandınız! Kaydol",
    "İNDİRİM fırsatı kaçmadan tıkla",
    "Hemen kaydol, bedava hediye",
]
NORMAL_TEST = [
    "Yarın toplantı için rapor gönderir misin",
    "Vize notları sisteme yüklendi mi",
    "Sunum için veri setini kontrol ettim",
    "Akşam projeyi birlikte gözden geçirelim",
]


```

Aşağıdaki parça tokenizer'ı, sıfırdan multinomial sınıfı ve sözlük-sayım fonksiyonunu içerir.

```python
def tokenize(s):
    """Turkce kucuk harf: once I->i ve İ->i, sonra lower()."""
    s = s.replace("İ", "i").replace("I", "ı").lower()
    return re.findall(r"[a-zçğıöşü]+", s)


def tokenize_naive(s):
    """Yanlis yol: dogrudan lower(). 'İ' birlesik nokta uretir."""
    return re.findall(r"[a-zçğıöşü]+", s.lower())


class MultiNB:
    """Multinomial NB, Laplace (alpha) duzeltmeli, sifirdan."""

    def __init__(self, alpha=1.0):
        self.alpha = alpha

    def fit(self, X, y):
        self.sinif = np.unique(y)
        self.log_prior = np.log([np.mean(y == c) for c in self.sinif])
        sayim = np.array([X[y == c].sum(axis=0) for c in self.sinif])
        duz = sayim + self.alpha
        self.log_theta = np.log(duz) - np.log(
            duz.sum(axis=1, keepdims=True)
        )
        return self

    def joint_log(self, X):
        """log p(y) + sum_w x_w log theta_yw  (matris carpimi)."""
        return X @ self.log_theta.T + self.log_prior

    def predict(self, X):
        return self.sinif[np.argmax(self.joint_log(X), axis=1)]


```

Aşağıdaki parça metin deneyidir. Sözlüğü yalnızca eğitim kümesinden kurar, sonra sıfırdan ve scikit-learn'ün `MultinomialNB` sınıfını aynı sayımlar üzerinde karşılaştırır, Laplace'ın etkisini ve log-uzayın neden gerekli olduğunu gösterir.

```python
def sozluk_ve_sayim(docs, sozluk):
    X = np.zeros((len(docs), len(sozluk)))
    for i, d in enumerate(docs):
        for w in tokenize(d):
            if w in sozluk:
                X[i, sozluk[w]] += 1
    return X


def metin_deney():
    docs = SPAM_TRAIN + NORMAL_TRAIN
    y = np.array([1] * len(SPAM_TRAIN) + [0] * len(NORMAL_TRAIN))
    test_docs = SPAM_TEST + NORMAL_TEST
    yt = np.array([1] * len(SPAM_TEST) + [0] * len(NORMAL_TEST))
    sozluk = {
        w: i
        for i, w in enumerate(
            sorted({w for d in docs for w in tokenize(d)})
        )
    }
    print("[Metin] sozluk boyutu:", len(sozluk))
    print("[Metin] 'indirim' var mi:", "indirim" in sozluk)
    print(
        "[Metin] naive lower:",
        tokenize_naive("İNDİRİM"),
        " dogru:",
        tokenize("İNDİRİM"),
```

Metin deneyinin devamında, α = 0 ile α = 1 arasındaki farkı ve 500 kelimelik bir mesajın olasılığının alt taşmasını ölçüyoruz.

```python
    )
    X = sozluk_ve_sayim(docs, sozluk)
    Xt = sozluk_ve_sayim(test_docs, sozluk)
    mine = MultiNB(alpha=1.0).fit(X, y)
    sk = MultinomialNB(alpha=1.0).fit(X, y)
    print(
        "[Metin] log theta farki (sifirdan - sklearn):",
        float(np.abs(mine.log_theta - sk.feature_log_prob_).max()),
    )
    print(
        "[Metin] log-olasilik farki:",
        float(
            np.abs(
                mine.joint_log(Xt) - sk.predict_joint_log_proba(Xt)
            ).max()
        ),
    )
    print("[Metin] tahminler (sifirdan):", mine.predict(Xt).tolist())
    print("[Metin] dogru etiketler     :", yt.tolist())
    print(
        "[Metin] test dogrulugu:",
        float(np.mean(mine.predict(Xt) == yt)),
    )
    # Laplace etkisi: 'kredi' yalnizca spam'de geciyor
    w = sozluk["kredi"]
    for a in [0.0, 1.0]:
        with np.errstate(divide="ignore"):
            m = MultiNB(alpha=a).fit(X, y)
        print(
            "[Laplace] alpha=%.0f  log theta(kredi|normal)=%s"
            % (a, m.log_theta[0, w])
        )
    # Alt tasma: 500 kelimelik mesaj, her biri p=0,1
    p = np.full(500, 0.1)
    print("[Log] carpim 0,1^500 =", float(np.prod(p)))
    print(
        "[Log] log toplam     =", round(float(np.sum(np.log(p))), 3)
    )


```

### Varsayım bozulduğunda ne olur: kalibrasyon

Naive Bayes'in bağımsızlık varsayımı bozulduğunda sınıflandırma doğruluğu çoğu zaman makul kalır; ama olasılık çıktısı, yani güven değeri, ciddi biçimde yanlış olabilir. Bunun nedeni basittir: model aynı kanıtı iki kez sayar. Birbirine bağlı iki özelliği bağımsızmış gibi çarpınca, kanıt olduğundan güçlü görünür ve posterior kendinden emin bir hale gelir.

Bunu Bölüm 57'deki kalibrasyon kavramıyla ölçeriz. Bir modelin "%80 eminim" dediği tahminlerin gerçekte yaklaşık %80'i doğru çıkıyorsa iyi kalibredir. Beklenen kalibrasyon hatası (ECE), güven aralıklarına göre doğruluk ile güven farkının ağırlıklı ortalamasıdır. Brier skoru ise olasılık tahmininin karesel hatasıdır; küçük olması iyidir.

Aşağıdaki kod iki deney yapar. İlkinde iki özellik sınıf içinde korelasyonludur (ρ = 0,9); NB ile lojistik regresyonu karşılaştırırız. İkincisinde bağımsız verideki bir özelliği k kez kopyalarız; NB'ye aynı kanıtı k kez saydırmış oluruz.

```python
def proba(J):
    """Log-olasilik matrisinden olasilik (log-toplam-exp kararli)."""
    J = J - J.max(axis=1, keepdims=True)
    P = np.exp(J)
    return P / P.sum(axis=1, keepdims=True)


def ece(p1, y, bins=10):
    """Beklenen kalibrasyon hatasi (guven araliklarina gore)."""
    guven = np.maximum(p1, 1 - p1)
    dogru = ((p1 >= 0.5).astype(int) == y).astype(float)
    kenar = np.linspace(0.5, 1.0, bins + 1)
    toplam = 0.0
    for a, b in zip(kenar[:-1], kenar[1:]):
        m = (
            (guven >= a) & (guven <= b)
            if a == 0.5
            else ((guven > a) & (guven <= b))
        )
        if m.any():
            toplam += m.mean() * abs(
                dogru[m].mean() - guven[m].mean()
            )
    return toplam


def iki_sinif(n, rho, rng):
    """Iki sinif, ortak kovaryans (rho). Sinif ortalamalari +-0,6."""
    y = rng.integers(0, 2, n)
    isaret = np.where(y == 1, 1.0, -1.0)[:, None]
    kov = np.array([[1.0, rho], [rho, 1.0]])
    X = 0.6 * isaret + rng.multivariate_normal([0, 0], kov, size=n)
    return X, y


```

Deney parçası ilk olarak korelasyonlu veriyi, sonra kopyalanmış özellik senaryosunu çalıştırır. Her iki senaryoda 20 tohum üzerinden ortalama alınır.

```python
def varsayim_deney():
    print("\n[Varsayim] 20 tohum, n_egitim=2000, n_test=4000")
    for rho in [0.0, 0.9]:
        sonuc = {"NB": [], "LR": []}
        for s in range(20):
            rng = np.random.default_rng(s)
            Xa, ya = iki_sinif(2000, rho, rng)
            Xb, yb = iki_sinif(4000, rho, rng)
            nb = GaussNB().fit(Xa, ya)
            lr = LogisticRegression(max_iter=1000).fit(Xa, ya)
            for ad, p1 in [
                ("NB", proba(nb.joint_log(Xb))[:, 1]),
                ("LR", lr.predict_proba(Xb)[:, 1]),
            ]:
                sonuc[ad].append(
                    [
                        np.mean((p1 >= 0.5) == yb),
                        np.mean((p1 - yb) ** 2),
                        ece(p1, yb),
                        np.mean(np.maximum(p1, 1 - p1)),
                    ]
                )
        for ad in ["NB", "LR"]:
            a = np.array(sonuc[ad])
            print(
                "rho=%.1f %s  dogruluk=%.4f  Brier=%.4f  ECE=%.4f"
                "  ort.guven=%.4f" % (rho, ad, *a.mean(axis=0))
            )


```

```python
def varsayim_kopya():
    print("\n[Kopya] bagimsiz veri (rho=0), x1 kac kez kopyalaniyor")
    for k in [1, 2, 4, 8]:
        sonuc = []
        for s in range(20):
            rng = np.random.default_rng(100 + s)
            Xa, ya = iki_sinif(2000, 0.0, rng)
            Xb, yb = iki_sinif(4000, 0.0, rng)
            Xa2 = np.column_stack(
                [Xa[:, [0]].repeat(k, axis=1), Xa[:, 1]]
            )
            Xb2 = np.column_stack(
                [Xb[:, [0]].repeat(k, axis=1), Xb[:, 1]]
            )
            p1 = proba(GaussNB().fit(Xa2, ya).joint_log(Xb2))[:, 1]
            sonuc.append(
                [
                    np.mean((p1 >= 0.5) == yb),
                    np.mean((p1 - yb) ** 2),
                    ece(p1, yb),
                    np.mean(np.maximum(p1, 1 - p1)),
                ]
            )
        a = np.array(sonuc).mean(axis=0)
        print(
            "k=%d  dogruluk=%.4f  Brier=%.4f  ECE=%.4f  guven=%.4f"
            % (k, *a)
        )


```

### Naive Bayes ile lojistik regresyon: öğrenme eğrisi

Ng ve Jordan'ın 2001 tarihli çalışması (genel bilgi), üretici ve ayırt edici modelin örnek sayısına göre davranışını teorik olarak karşılaştırır: naive Bayes az veride daha hızlı öğrenir ve kendi asimptotik hatasına daha erken ulaşır; lojistik regresyon ise daha yavaş öğrenir ama daha düşük bir asimptotik hataya gider. Bunu kendi verimizde test edelim. Meme kanseri verisinin %25'i sabit test kümesine ayrılır; eğitim kümesinden 10'dan 320'ye kadar örnekler rastgele seçilir ve her boyut için 30 farklı alt küme denenir.

```python
def ogrenme_egrisi():
    X, y = load_breast_cancer(return_X_y=True)
    Xh, Xte, yh, yte = train_test_split(
        X, y, test_size=0.25, random_state=62, stratify=y
    )
    boyutlar = [10, 20, 40, 80, 160, 320]
    satirlar = ["n,nb_ort,nb_ss,lr_ort,lr_ss"]
    print("\n[Egri] n, NB ort (ss), LR ort (ss); 30 alt kume")
    for n in boyutlar:
        nb_a, lr_a = [], []
        for s in range(30):
            rng = np.random.default_rng(1000 * n + s)
            while True:
                idx = rng.choice(len(Xh), n, replace=False)
                if len(np.unique(yh[idx])) == 2:
                    break
            nb_a.append(
                np.mean(
                    GaussianNB().fit(Xh[idx], yh[idx]).predict(Xte)
                    == yte
                )
            )
```

```python
            lr = make_pipeline(
                StandardScaler(), LogisticRegression(max_iter=1000)
            )
            lr_a.append(
                np.mean(lr.fit(Xh[idx], yh[idx]).predict(Xte) == yte)
            )
        nb_a, lr_a = np.array(nb_a), np.array(lr_a)
        print(
            "n=%3d  NB %.4f (%.4f)   LR %.4f (%.4f)"
            % (n, nb_a.mean(), nb_a.std(), lr_a.mean(), lr_a.std())
        )
        satirlar.append(
            "%d,%.5f,%.5f,%.5f,%.5f"
            % (n, nb_a.mean(), nb_a.std(), lr_a.mean(), lr_a.std())
        )
    with open(
        VERI + "/b62_nb_lr_ogrenme.csv", "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")


```

```python
if __name__ == "__main__":
    print("== 1) Gauss NB ==")
    gauss_deney()
    print("\n== 2) Multinomial NB (Turkce metin) ==")
    metin_deney()
    print("\n== 3) Varsayim bozulmasi ==")
    varsayim_deney()
    varsayim_kopya()
    print("\n== 4) Ogrenme egrisi ==")
    ogrenme_egrisi()
```

Programın tam çıktısı aşağıdadır. Bu çıktıyı yeniden üretmek için `b62_01_nb.py` dosyasını çalıştırman yeterlidir (tohumlar kodun içinde sabittir).

```term
$ python b62_01_nb.py
== 1) Gauss NB ==
[Gauss] en buyuk log-fark: 1.1368683772161603e-13
[Gauss] dogruluk sifirdan: 0.9474
[Gauss] dogruluk sklearn : 0.9474

== 2) Multinomial NB (Turkce metin) ==
[Metin] sozluk boyutu: 87
[Metin] 'indirim' var mi: True
[Metin] naive lower: ['i', 'ndi', 'ri', 'm']  dogru: ['indirim']
[Metin] log theta farki (sifirdan - sklearn): 0.0
[Metin] log-olasilik farki: 0.0
[Metin] tahminler (sifirdan): [1, 1, 1, 1, 0, 0, 0, 0]
[Metin] dogru etiketler     : [1, 1, 1, 1, 0, 0, 0, 0]
[Metin] test dogrulugu: 1.0
[Laplace] alpha=0  log theta(kredi|normal)=-inf
[Laplace] alpha=1  log theta(kredi|normal)=-4.962844630259907
[Log] carpim 0,1^500 = 0.0
[Log] log toplam     = -1151.293

== 3) Varsayim bozulmasi ==

[Varsayim] 20 tohum, n_egitim=2000, n_test=4000
rho=0.0 NB  dogruluk=0.8024  Brier=0.1379  ECE=0.0145  ort.guven=0.8021
rho=0.0 LR  dogruluk=0.8028  Brier=0.1379  ECE=0.0156  ort.guven=0.8019
rho=0.9 NB  dogruluk=0.7306  Brier=0.1895  ECE=0.0955  ort.guven=0.8254
rho=0.9 LR  dogruluk=0.7303  Brier=0.1791  ECE=0.0174  ort.guven=0.7289

[Kopya] bagimsiz veri (rho=0), x1 kac kez kopyalaniyor
k=1  dogruluk=0.8033  Brier=0.1373  ECE=0.0153  guven=0.8041
k=2  dogruluk=0.7920  Brier=0.1500  ECE=0.0713  guven=0.8611
k=4  dogruluk=0.7683  Brier=0.1851  ECE=0.1483  guven=0.9163
k=8  dogruluk=0.7502  Brier=0.2208  ECE=0.2052  guven=0.9547

== 4) Ogrenme egrisi ==

[Egri] n, NB ort (ss), LR ort (ss); 30 alt kume
n= 10  NB 0.8828 (0.0897)   LR 0.9131 (0.0488)
n= 20  NB 0.9448 (0.0151)   LR 0.9455 (0.0236)
n= 40  NB 0.9480 (0.0095)   LR 0.9599 (0.0144)
n= 80  NB 0.9464 (0.0068)   LR 0.9748 (0.0080)
n=160  NB 0.9469 (0.0067)   LR 0.9762 (0.0071)
n=320  NB 0.9499 (0.0065)   LR 0.9865 (0.0051)
```

Çıktıda birkaç şeyi okumak gerekir. Gauss NB'nin log-olasılıkları scikit-learn ile 10^-13 mertebesinde aynıdır; kayan noktalı aritmetikteki küçük farklar dışında iki uygulama birebir çalışır. Metin sınıflandırmada sözlük boyutu 87'dir ve sıfırdan yazdığımız multinomial sınıf, scikit-learn'ün θ ve log-olasılık değerlerini birebir tutturur. Test kümesi de (8 mesaj) tamamen doğru sınıflanır. Ama bu bir kanıt değildir: 8 kurgusal mesaj küçük bir sayıdır ve doğruluk tek başına bir şey kanıtlamaz; önemli olan mekanizmanın doğru çalışmasıdır.

Laplace çıktısı açıktır: α = 0 iken "kredi" kelimesinin normal sınıftaki log-olasılığı −∞'dir, α = 1 iken −4,96'dır. Log-uzay çıktısı ise alt taşmayı gösterir: 0,1'in 500 kez çarpımı float64'te 0'a iner, ama log-toplam −1151,29 olarak hesaplanabilir.

Varsayım deneyi açıktır. Bağımsız veride (ρ = 0) NB ve lojistik regresyon neredeyse aynı Brier ve ECE değerlerini verir. Korelasyon ρ = 0,9 olduğunda NB'nin ECE değeri 0,0955'e çıkar; lojistik regresyonda bu 0,0174'tür. Kopya deneyi de aynı hikâyeyi anlatır: özellik kopyalandıkça ECE 0,015'ten 0,205'e çıkar ve ortalama güven 0,80'den 0,95'e yükselir. Doğruluk da 0,80'den 0,75'e düşer; bu, kopyalanan özelliğin modeli fazla etkilemesinin bir sonucudur.

Öğrenme eğrisi ise beklenenden farklı bir sonuç verdi ve bunu olduğu gibi raporlamak gerekir. Bu veride naive Bayes'in erken üstünlüğü görülmedi: n = 10'da NB ortalaması 0,883 iken lojistik regresyon 0,913'tür, standart sapma da NB'de daha büyüktür. NB'nin asimptotik tavanı yaklaşık 0,95'te kalırken lojistik regresyon 320 örnekte 0,987'ye çıkar. Yani bu veride asimptotik fark netken erken üstünlük gözlenmedi. Bu, Ng-Jordan'ın genel eğiliminin her veride kendiliğinden görüleceği anlamına gelmez; teoriyi kendi verinde sınaman gerekir.

Şekil 62.2, bu öğrenme eğrisini hata çubuklarıyla gösterir.

![Şekil 62.2: Meme kanseri verisinde NB ve lojistik regresyon öğrenme eğrisi](gorseller/b62_nb_lr_ogrenme.png)

::: dikkat
Naive Bayes'in doğruluğuna bakıp "varsayım yanlış ama işe yarıyor" demek kolaydır. Ama olasılık çıktısını bir karar eşiği olarak kullanıyorsan (örneğin %90'ın üstünde alarm) kalibrasyonu ayrıca ölçmek zorundasın. Bu bölümün ECE deneyi tam olarak bunu gösterir.
:::

## 62.3 Bayes ağları: yapı, çarpanlara ayırma ve çıkarım

Naive Bayes'te özellikler birbirinden tamamen bağımsızdı; gerçek dünyada bu nadiren doğrudur. Bayes ağı, bağımlılıkları açıkça çizmenin bir yoludur. Her değişken bir düğüm, her doğrudan nedensel ya da olasılıksal ilişki bir yönlü ok olarak gösterilir. Ağ **yönlü döngüsüz bir graf** (DAG) olmalıdır; Bölüm 11 ve 17'de gördüğün yönlü graf ve topolojik sıra kavramları burada doğrudan kullanılır.

Her düğüm için bir **koşullu olasılık tablosu** (CPT) verilir: düğümün ebeveynleri verildiğinde kendi değerinin dağılımı. Ortak dağılım, bütün düğümler için bu tabloların çarpımına ayrışır:

P(X_1, ..., X_n) = Π_i P(X_i | ebeveynler(X_i))

Bu çarpanlara ayırma, bağımsızlık varsayımlarını grafın yapısından okumamızı sağlar. Naive Bayes da bir Bayes ağıdır: tek ebeveyni olan bir sınıf düğümü ve onun çocuklarıdır. Ağın yapısı, hangi bilgilerin hangi bilgilere bağlı olduğunu açıkça söyler.

### Koşullu bağımsızlık ve d-ayrılma sezgisi

Üç düğümlü üç temel yapı vardır. **Zincir** A → B → C'de B biliniyorsa A ve C bağımsızdır. **Ortak neden** A ← B → C'de B biliniyorsa A ve C bağımsızdır. **Ortak sonuç** (collider) A → B ← C'de ise durum tersinedir: B gözleniyorsa A ve C birbirine bağımlı hale gelir, B bilinmiyorsa bağımsızdır. Bu son durum bu bölümün en önemli sezgilerinden biridir ve aşağıda açıklama gücü (explaining away) olarak sayısal göreceksin.

Genel kural d-ayrılma (d-separation) olarak bilinir ve bir grafın bağımsızlık yapısını tümüyle belirler. Bu bölümde tam algoritmasına girmeyeceğiz; üç temel yapının sezgisi yeterlidir.

### Küçük bir ağ: sensör arızası ve gerçek hedef

Bir İHA'da bir sensör arızası ile gerçek bir hedefin varlığı, bir alarm üretebilir. Üç ikili değişkenli bir ağ kuralım: F (sensör arızası, P(F=1) = 0,02), H (gerçek hedef var, P(H=1) = 0,05) ve A (alarm verildi). Alarm iki nedene bağlıdır: F → A ← H. Koşullu olasılık tablosu şöyledir (kurgusal, öğretim amaçlı sayılar):

| F | H | P(A = 1 \| F, H) |
|---|---|---|
| 0 | 0 | 0,01 |
| 1 | 0 | 0,60 |
| 0 | 1 | 0,90 |
| 1 | 1 | 0,92 |

Şekil 62.3, bu ağın yapısını gösterir. Alarm ortak sonuçtur; F ve H ayrı nedenlerdir.

![Şekil 62.3: Üç düğümlü ağ: sensör arızası ve gerçek hedef, ortak sonuç olarak alarm](gorseller/b62_bayes_agi.png)

### Sayımla tam çıkarım

Çıkarım (inference), bir gözlem verildiğinde bilinmeyen bir değişkenin dağılımını hesaplamaktır. Bu küçük ağda en basit yöntem **sayımla tam çıkarım**dır: ortak dağılımın bütün 8 olasılığını yaz, gözleme uymayanları at, kalanları topla ve normalize et. Ortak dağılım P(F, H, A) = P(F) P(H) P(A | F, H) biçimindedir. Aşağıdaki kod bu hesabı sıfırdan yapar. Ayrıca reddetme örneklemesiyle (Bölüm 49'daki reddetme yönteminin aynısı) aynı sonucu yaklaşık olarak bulur.

```python
# -*- coding: utf-8 -*-
# b62_02_bn.py: 3 dugumlu Bayes agi (F -> A <- H), sayimla cikarim,
# aciklama gucu (explaining away) ve reddetme ornekleme ile yaklasik
# cikarim.
import numpy as np

# F: sensor arizasi, H: gercek hedef var, A: alarm (1 = alarm)
P_F = {0: 0.98, 1: 0.02}
P_H = {0: 0.95, 1: 0.05}
# P(A = 1 | F, H): kosullu olasilik tablosu (CPT)
P_A1 = {(0, 0): 0.01, (1, 0): 0.60, (0, 1): 0.90, (1, 1): 0.92}


def ortak(f, h, a):
    """Ortak olasilik: P(F,H,A) = P(F) P(H) P(A|F,H)."""
    pa = P_A1[(f, h)]
    return P_F[f] * P_H[h] * (pa if a == 1 else 1 - pa)


def olasilik(sart, hedef):
    """Sayimla cikarim: P(hedef|sart) = T(hedef,sart)/T(sart).
    sart ve hedef: {'F':1} gibi sozlukler."""

    def topla(kisit):
        s = 0.0
        for f in (0, 1):
            for h in (0, 1):
                for a in (0, 1):
                    v = {"F": f, "H": h, "A": a}
                    if all(v[k] == x for k, x in kisit.items()):
                        s += ortak(f, h, a)
        return s

    pay = topla(sart)
    return topla({**sart, **hedef}) / pay


```

```python
def reddetme(n, seed=62):
    """Reddetme ornekleme: ornekle, A=1 olmayanlari at."""
    rng = np.random.default_rng(seed)
    f = (rng.random(n) < P_F[1]).astype(int)
    h = (rng.random(n) < P_H[1]).astype(int)
    p = np.array([P_A1[(a, b)] for a, b in zip(f, h)])
    a = (rng.random(n) < p).astype(int)
    kabul = a == 1
    return f[kabul], h[kabul], kabul.mean()


```

Programın ana bölümü, her sorgu için sayımla çıkarımı, reddetme örneklemesini ve kabul oranını ayrı ayrı yazdırır.

```python
if __name__ == "__main__":
    toplam = sum(
        ortak(f, h, a) for f in (0, 1) for h in (0, 1) for a in (0, 1)
    )
    print("Toplam olasilik (1 olmali):", round(toplam, 10))
    print(
        "P(A=1)                   =", round(olasilik({}, {"A": 1}), 5)
    )
    print(
        "P(F=1 | A=1)             =",
        round(olasilik({"A": 1}, {"F": 1}), 4),
    )
    print(
        "P(F=1 | A=1, H=0)        =",
        round(olasilik({"A": 1, "H": 0}, {"F": 1}), 4),
    )
    print(
        "P(F=1 | A=1, H=1)        =",
        round(olasilik({"A": 1, "H": 1}, {"F": 1}), 4),
    )
```

```python
    print(
        "P(H=1 | A=1)             =",
        round(olasilik({"A": 1}, {"H": 1}), 4),
    )
    print(
        "P(H=1 | A=1, F=1)        =",
        round(olasilik({"A": 1, "F": 1}, {"H": 1}), 4),
    )
    print()
    print("Reddetme ornekleme (N = 200000, tohum 62):")
    for n in [200000]:
        f, h, kabul = reddetme(n)
        print("  kabul orani            =", round(kabul, 4))
        print("  P(F=1 | A=1)  tahmin   =", round(f.mean(), 4))
        print(
            "  P(F=1 | A=1, H=1) tah. =",
            round(f[h == 1].mean(), 4),
            " (kabul sayisi:",
            int((h == 1).sum()),
            ")",
        )
```

```term
$ python b62_02_bn.py
Toplam olasilik (1 olmali): 1.0
P(A=1)                   = 0.06573
P(F=1 | A=1)             = 0.1874
P(F=1 | A=1, H=0)        = 0.5505
P(F=1 | A=1, H=1)        = 0.0204
P(H=1 | A=1)             = 0.6849
P(H=1 | A=1, F=1)        = 0.0747

Reddetme ornekleme (N = 200000, tohum 62):
  kabul orani            = 0.0665
  P(F=1 | A=1)  tahmin   = 0.184
  P(F=1 | A=1, H=1) tah. = 0.0205  (kabul sayisi: 9284 )
```

Ortak olasılıkların toplamı 1'dir ve sayımla çıkarım dört durumda da hesaplanabilir. Ama bu ağda asıl ilgi çekici sonuç açıklama gücüdür.

### Açıklama gücü (explaining away)

Bir alarm verildiğinde (A = 1) sensörün arızalı olma olasılığı P(F = 1 | A = 1) = 0,1874'tür. Yani alarm, arızaya şüphe düşürür ama onu da yükseltir; başlangıçtaki önsel %2'ye göre belirgin bir artış. Şimdi bir de gerçek hedefin var olduğunu öğrendiğimizi düşünelim (H = 1). O zaman P(F = 1 | A = 1, H = 1) = 0,0204 olur. Gerçek hedef alarmı açıklayabildiği için arızanın payı neredeyse sıfıra iner. Bu, **açıklama gücü**dür: iki bağımsız neden aynı sonucu paylaştığında, birini doğrulamak diğerinin olasılığını düşürür.

Bu etki ortak sonuç yapısının doğrudan sonucudur. F ve H, önsel olarak birbirinden bağımsızdır; ama A gözlendiğinde ikisi birbirine bağımlı hale gelir. Bölüm 49'da bu tür koşullu bağımlılığı görmemiştin; bu nedenle bu bölümde açık bir sayısal örnekle ayrıca çalışacağız (Örnek 2).

### Yaklaşık çıkarım: reddetme örneklemesi

Ağ büyüdüğünde sayımla tam çıkarım üstel olarak pahalılaşır: n ikili değişken için 2^n terim toplanır. Bu yüzden yaklaşık yöntemler kullanılır. Reddetme örneklemesinde ortak dağılımdan örnekler üretir (önce ebeveynler, sonra çocuklar), gözleme uymayan örnekleri atarsın ve kalan örneklerden oranı tahmin edersin. Kabul oranı, gözlemin olasılığı kadardır (P(A = 1) = 0,0657). Bu yüzden gözlem nadirse yöntem yavaşlar; bu da Bölüm 49'da gördüğün reddetme yönteminin boyut ve nadirlik sorunudur.

Programın çıktısında N = 200.000 örnekle kabul oranı 0,0665 ve P(F = 1 | A = 1) tahmini 0,184 çıkmıştır; kesin değer 0,1874'tür. Standart hata yaklaşık √(0,18·0,82/13.150) ≈ 0,0034 olduğundan fark bir standart hatanın içindedir. Koşullu sorguda (H = 1 ekleyince) yalnızca 9.284 kabul olur ve tahmin 0,0205'tir. Gözlemi genişletmek, geçerli örnek sayısını da azaltır.

## 62.4 Markov zincirleri: durum geçişleri ve durağan dağılım

Bir Bayes ağı zamana bağlı değildir. Oysa bir İHA'nın uçuş modu zamanla değişir: önce kalkış, sonra seyir, sonra iniş. Bu tür zamansal bağımlılığı modellemenin en basit yolu **Markov zinciri**dir: bir sonraki durumun dağılımı yalnızca şu anki duruma bağlıdır (Markov özelliği). Durumlar K tane ise geçişler bir K×K stokastik matrisle (P) tanımlanır; P_ij, i durumundan j durumuna geçiş olasılığıdır.

Uzun süre sonra zincir bir **durağan dağılım** π'ye yaklaşabilir. Bu dağılım π = πP denklemini sağlar; yani π, P'nin sol özvektörüdür ve özdeğeri 1'dir (Bölüm 48'deki özdeğer ve özvektör kavramı). Bunu iki yolla bulabilirsin: özdeğer ayrışımıyla ya da P'nin kuvvetlerini alıp satırların yakınsamasını izleyerek. Güç yöntemi her satırın aynı dağılıma yaklaştığını gösterir.

Durağan dağılım, bir sistemin "uzun vadede hangi oranda hangi modda olacağını" söyler. Bu, daha sonra HMM'de durum sürelerini ve bekleme oranlarını yorumlarken işimize yarayacak.

## 62.5 Gizli Markov modelleri (HMM)

Çoğu gerçek problemde durumu doğrudan göremezsin. Bir İHA'nın uçuş modunu (kalkış, seyir, iniş) doğrudan ölçen bir sensör yoktur; ama irtifasındaki değişimi ölçersin. Bu, gizli durumlu bir modeldir: durumlar gizlidir, yalnızca gözlemler görülür. **Gizli Markov modeli (HMM)**, bir Markov zinciri (gizli durumlar) ile her durumdan gözlem üreten bir emisyon dağılımının birleşimidir.

Bir HMM üç bileşenle tanımlanır. π, ilk durumun dağılımıdır. A, durum geçiş matrisidir (A_ij = P(z_t = j | z_{t−1} = i)). B, emisyon matrisidir (B_kv = P(x_t = v | z_t = k)). Ortak olasılık şöyledir:

P(z, x) = π(z_1) B(x_1 | z_1) Π_{t≥2} A(z_t | z_{t−1}) B(x_t | z_t)

Bir HMM, üç temel problemi çözmek için kullanılır. **Değerlendirme**: bir gözlem dizisinin olasılığı nedir? (İleri algoritma.) **Kod çözme**: gözlemlere en uygun gizli durum dizisi hangisidir? (Viterbi.) **Öğrenme**: parametreler (π, A, B) gözlemlerden nasıl tahmin edilir? (Baum–Welch.)

Şekil 62.4 solda üç durumlu bir HMM'i ve geçiş olasılıklarını, sağda ise Viterbi kafesini (trellis) gösterir. Kafes, her zaman adımında her durumun bir düğümle temsil edildiği ve geçişlerin kenarlarla gösterildiği bir ağdır. Viterbi algoritması bu kafes üzerinde bir yol arar; kırmızı yol, örnek bir durum dizisidir.

![Şekil 62.4: HMM durum diyagramı (solda) ve Viterbi kafesi (sağda; kırmızı, örnek bir durum yolu)](gorseller/b62_hmm_viterbi.png)

### İleri algoritma: olasılığı hesaplamak

Bir gözlem dizisinin olasılığını (P(x_1..T)) doğrudan hesaplamak, K^T yolu toplamaktır; T = 10 ve K = 3 için bile 59.049 terim eder. İleri algoritma bunu dinamik programlamayla O(T·K²) işlemde yapar (Bölüm 16'daki DP fikri). α_t(k), t anına kadarki gözlemleri görmüş ve z_t = k olan olasılıktır. Başlangıçta α_1(k) = π(k) B(x_1 | k), sonra α_t(k) = [Σ_j α_{t−1}(j) A_jk] B(x_t | k).

Sayısal sorun şudur: α değerleri T arttıkça çok küçülür ve alt taşar. Bu yüzden her adımda α'yı normalize ederiz ve toplamı c_t ile saklarız. O zaman log P(x) = Σ_t log c_t olur. Bu, Bölüm 51'de gördüğün log-uzay fikrinin ölçekli biçimidir.

### Viterbi: en olası yolu bulmak

Viterbi algoritması, ileri algoritmadaki toplamın yerine maksimum koyar. δ_t(k), z_t = k ile biten en olası yolun log-olasılığıdır; ψ_t(k), bu en iyi yolun bir önceki durumunu saklar. Sonunda en iyi son durumdan geriye doğru izlenerek tüm yol bulunur. Bu, Bölüm 16'daki LCS ve sırt çantası tablolarının tam aynı yapısıdır: bir tablo doldurulur, sonra geri izleme yapılır. Bölüm 16'da bunu bir DP olarak gördün; burada tablonun neden yalnızca bir önceki sütuna bağlı olduğunu anlayacaksın.

Viterbi'nin uygulamada log-uzayda çalıştırılması gerekir: δ değerleri toplam olarak tutulur, çarpım olarak değil. Yukarıdaki kod da bunu yapar. Sıfır olasılıklı geçişler (örneğin iniş durumundan kalkışa geçiş) log(0) = −∞ üretir; `argmax` bu değerleri asla seçmez, dolayısıyla yapısal kısıtlar kendiliğinden korunur.

### Baum–Welch: parametreleri öğrenmek

Parametreler bilinmiyorsa, gözlem dizisinden EM algoritmasıyla (Bölüm 61'deki GMM+EM'in dizisel versiyonu) öğrenilir. Baum–Welch iki adımdan oluşur. E adımında ileri ve geri (β) algoritmalarıyla her t anında her durumun sonsal olasılığını (γ) ve her geçişin sonsal olasılığını (ξ) hesaplarsın. M adımında π, A ve B bu beklenen sayımlardan yeniden tahmin edilir. Yakınsama garantisi genel EM teorisinden gelir: gözlemin log-olabilirliği her iterasyonda azalmaz (genel bilgi). Pratikte bu, yerel bir maksimuma yakınsama demektir; başlangıç değeri önemlidir.

Baum–Welch'in yapısal bir özelliği: A'da sıfır olan bir geçiş EM iterasyonlarında sıfır kalır, çünkü sayımı da sıfır olur. Böylece "iniş durumundan kalkışa asla geçilmez" gibi bilgiyi modele koyabilirsin.

### İHA uçuş modu: sentetik bir HMM

Gizli durumlar kalkış (0), seyir (1) ve iniş (2) olsun. Gözlem, irtifa değişiminin üç sınıfa ayrılmış hâlidir: düşüyor (0), sabit (1), yükseliyor (2). Model şöyle tanımlanmıştır (sentetik, bir İHA'nın gerçek kaydı değildir; sadece HMM mekanizmasını göstermek için seçildi): iniş bittikten sonra yeni bir uçuşa geçilebilir, bu yüzden iniş durumunun geçişleri kalkışa dönüşe izin verir.

Aşağıdaki kod, bu modelden sabit tohumla örnek üretir, ileri algoritmayı ve Viterbi'yi kaba kuvvetle karşılaştırır ve Baum–Welch ile parametreleri eğitim verisinden öğrenir.

```python
# -*- coding: utf-8 -*-
# b62_03_hmm.py: Gizli Markov modeli sifirdan: ileri (olcekli),
# Viterbi (log-uzay), geri algoritma, Baum-Welch (EM); IHA ucus modu
# (kalkis / seyir / inis) sentetik verisi. Kaba kuvvet dogrulamasi.
import itertools
import numpy as np

# Gizli durumlar: 0 = kalkis, 1 = seyir, 2 = inis
# Gozlemler (irtifa degisimi): 0 = dusuyor, 1 = sabit, 2 = yukseliyor
PI = np.array([1.0, 0.0, 0.0])
A = np.array(
    [[0.70, 0.30, 0.00], [0.00, 0.97, 0.03], [0.30, 0.00, 0.70]]
)
B = np.array(
    [[0.20, 0.30, 0.50], [0.15, 0.70, 0.15], [0.60, 0.30, 0.10]]
)


```

```python
def ornekle(T, pi, A, B, rng):
    """Once gizli durum dizisi, sonra gozlemler (sentetik veri)."""
    K, V = B.shape
    z = np.zeros(T, dtype=int)
    x = np.zeros(T, dtype=int)
    z[0] = rng.choice(K, p=pi)
    for t in range(1, T):
        z[t] = rng.choice(K, p=A[z[t - 1]])
    for t in range(T):
        x[t] = rng.choice(V, p=B[z[t]])
    return z, x


def ileri(obs, pi, A, B):
    """Olcekli ileri algoritma. alpha_hat[t] toplam 1'e normalize,
    c[t] olcek katsayisi; log P(x) = sum log c[t]."""
    T, K = len(obs), len(pi)
    alpha = np.zeros((T, K))
    c = np.zeros(T)
    alpha[0] = pi * B[:, obs[0]]
    c[0] = alpha[0].sum()
    alpha[0] /= c[0]
    for t in range(1, T):
        alpha[t] = (alpha[t - 1] @ A) * B[:, obs[t]]
        c[t] = alpha[t].sum()
        alpha[t] /= c[t]
    return alpha, c


```

```python
def geri(obs, A, B, c):
    """Olcekli geri algoritma; ileri ile ayni olcekleri kullanir."""
    T, K = len(obs), A.shape[0]
    beta = np.zeros((T, K))
    beta[-1] = 1.0
    for t in range(T - 2, -1, -1):
        beta[t] = A @ (B[:, obs[t + 1]] * beta[t + 1]) / c[t + 1]
    return beta


def viterbi(obs, pi, A, B):
    """En olasi gizli yol. Log-uzay: toplam, carpim degil."""
    T, K = len(obs), len(pi)
    with np.errstate(divide="ignore"):
        lpi, lA, lB = np.log(pi), np.log(A), np.log(B)
    delta = np.zeros((T, K))
    psi = np.zeros((T, K), dtype=int)
    delta[0] = lpi + lB[:, obs[0]]
    for t in range(1, T):
        skor = delta[t - 1][:, None] + lA  # (onceki, sonraki)
        psi[t] = np.argmax(skor, axis=0)
        delta[t] = np.max(skor, axis=0) + lB[:, obs[t]]
    yol = np.zeros(T, dtype=int)
    yol[-1] = np.argmax(delta[-1])
    for t in range(T - 1, 0, -1):
        yol[t - 1] = psi[t, yol[t]]
    return yol, delta, psi


```

```python
def kaba_kuvvet(obs, pi, A, B):
    """Tum K^T yolu tek tek dene: toplam olabilirlik ve en iyi yol."""
    T, K = len(obs), len(pi)
    toplam, en_iyi, en_yol = 0.0, -1.0, None
    for yol in itertools.product(range(K), repeat=T):
        p = pi[yol[0]] * B[yol[0], obs[0]]
        for t in range(1, T):
            p *= A[yol[t - 1], yol[t]] * B[yol[t], obs[t]]
        toplam += p
        if p > en_iyi:
            en_iyi, en_yol = p, yol
    return toplam, np.array(en_yol)


```

```python
def baum_welch(obs, pi, A, B, iter_sayisi=80):
    """EM: E adimi (gamma, xi) ve M adimi (pi, A, B yeniden tahmini).
    Sifir olan gecisler sifir kalir (yapi korunur)."""
    obs = np.asarray(obs)
    K, V = B.shape
    log_olab = []
    for _ in range(iter_sayisi):
        alpha, c = ileri(obs, pi, A, B)
        beta = geri(obs, A, B, c)
        log_olab.append(np.sum(np.log(c)))
        gamma = alpha * beta
        gamma /= gamma.sum(axis=1, keepdims=True)
        T = len(obs)
        xi = np.zeros((T - 1, K, K))
        for t in range(T - 1):
            m = (
                alpha[t][:, None]
                * A
                * (B[:, obs[t + 1]] * beta[t + 1])[None, :]
            )
            xi[t] = m / m.sum()
        pi = gamma[0]
        A = xi.sum(axis=0) / gamma[:-1].sum(axis=0)[:, None]
        B_yeni = np.zeros((K, V))
        for v in range(V):
            B_yeni[:, v] = gamma[obs == v].sum(axis=0)
        B = B_yeni / gamma.sum(axis=0)[:, None]
    return pi, A, B, np.array(log_olab)


```

Aşağıdaki parça Örnek 3'teki iki durumlu küçük HMM'i ve deney ortamını kurar.

```python
ISIM = ["kalkis", "seyir", "inis"]


def ornek3():
    """Kucuk iki durumlu ornek: tablo (delta, psi) ve geri izleme."""
    pi2 = np.array([0.6, 0.4])
    A2 = np.array([[0.7, 0.3], [0.4, 0.6]])
    B2 = np.array([[0.9, 0.1], [0.2, 0.8]])
    obs2 = [1, 0, 0]
    yol, delta, psi = viterbi(obs2, pi2, A2, B2)
    print("delta (log):\n", np.round(delta, 4))
    print("psi:\n", psi)
    print("en iyi yol:", yol.tolist())
    print("olasilik (dogru):", np.exp(delta[-1]).max().round(6))
    top, en = kaba_kuvvet(obs2, pi2, A2, B2)
    print(
        "kaba kuvvet en iyi yol:",
        en.tolist(),
        " P(x) toplam:",
        round(top, 6),
    )


```

```python
def uav_deney():
    print("\n[IHA] egitim: T=3000 tohum 62, test: T=600 tohum 63")
    z8, x8 = ornekle(8, PI, A, B, np.random.default_rng(5))
    alpha, c = ileri(x8, PI, A, B)
    top, en = kaba_kuvvet(x8, PI, A, B)
    lp_ileri = round(np.sum(np.log(c)), 10)
    lp_kaba = round(np.log(top), 10)
    print("[dogrulama T=8] log P ileri:", lp_ileri)
    print("[dogrulama T=8] log P kaba:", lp_kaba)
    yol_v = viterbi(x8, PI, A, B)[0].tolist()
    print("[dogrulama T=8] viterbi:", yol_v)
    print("[dogrulama T=8] kaba kuvvet:", en.tolist())
    print("[dogrulama T=8] gercek:", z8.tolist())
    z_tr, x_tr = ornekle(3000, PI, A, B, np.random.default_rng(62))
    z_te, x_te = ornekle(600, PI, A, B, np.random.default_rng(63))
    vit = viterbi(x_te, PI, A, B)[0]
    naif = np.argmax(B[:, x_te], axis=0)
    print(
        "[Dogruluk] Viterbi:",
        round(np.mean(vit == z_te), 4),
        " gozlem basina en iyi durum (naif):",
        round(np.mean(naif == z_te), 4),
    )
    # Baum-Welch: yapisal sifirlar korunur, bozuk baslangic
    A0 = np.array(
```

```python
        [[0.60, 0.40, 0.00], [0.00, 0.90, 0.10], [0.40, 0.00, 0.60]]
    )
    B0 = np.array(
        [[0.30, 0.40, 0.30], [0.25, 0.50, 0.25], [0.40, 0.35, 0.25]]
    )
    pi_h, A_h, B_h, ll = baum_welch(x_tr, PI, A0, B0, iter_sayisi=150)
    print("[BW] egitim: T=3000, 150 iterasyon, baslangic: A0, B0")
    print("[BW] log P(x) iterasyon boyunca (ilk 6 ve son):")
    print(
        "   ", np.round(ll[:4], 3).tolist(), "...", round(ll[-1], 3)
    )
    print("[BW] monoton artis:", bool(np.all(np.diff(ll) >= -1e-9)))
    print("[BW] ogrenilen A:\n", np.round(A_h, 3))
    print("[BW] ogrenilen B:\n", np.round(B_h, 3))
    vit2 = viterbi(x_te, pi_h, A_h, B_h)[0]
    print(
        "[BW] gercek dogruluk (gercek parametreler):",
        round(np.mean(viterbi(x_te, PI, A, B)[0] == z_te), 4),
    )
    print(
        "[BW] test dogrulugu (ogrenilen parametreler):",
        round(np.mean(vit2 == z_te), 4),
    )


if __name__ == "__main__":
    print("== Ornek 3 (iki durum, T=3) ==")
    ornek3()
    print("\n== IHA ucus modu HMM ==")
    uav_deney()
```

Programın tam çıktısı aşağıdadır.

```term
$ python b62_03_hmm.py
== Ornek 3 (iki durum, T=3) ==
delta (log):
 [[-2.8134 -1.1394]
 [-2.1611 -3.2597]
 [-2.6231 -4.9745]]
psi:
 [[0 0]
 [1 1]
 [0 0]]
en iyi yol: [1, 0, 0]
olasilik (dogru): 0.072576
kaba kuvvet en iyi yol: [1, 0, 0]  P(x) toplam: 0.12573

== IHA ucus modu HMM ==

[IHA] egitim: T=3000 tohum 62, test: T=600 tohum 63
[dogrulama T=8] log P ileri: -8.3535052841
[dogrulama T=8] log P kaba: -8.3535052841
[dogrulama T=8] viterbi: [0, 0, 1, 1, 1, 1, 1, 1]
[dogrulama T=8] kaba kuvvet: [0, 0, 1, 1, 1, 1, 1, 1]
[dogrulama T=8] gercek: [0, 1, 1, 1, 1, 1, 1, 1]
[Dogruluk] Viterbi: 0.7833  gozlem basina en iyi durum (naif): 0.6483
[BW] egitim: T=3000, 150 iterasyon, baslangic: A0, B0
[BW] log P(x) iterasyon boyunca (ilk 6 ve son):
    [-2902.248, -2718.253, -2716.359, -2714.188] ... -2700.904
[BW] monoton artis: True
[BW] ogrenilen A:
 [[0.337 0.663 0.   ]
 [0.    0.927 0.073]
 [0.286 0.    0.714]]
[BW] ogrenilen B:
 [[0.017 0.427 0.556]
 [0.146 0.731 0.123]
 [0.464 0.351 0.185]]
[BW] gercek dogruluk (gercek parametreler): 0.7833
[BW] test dogrulugu (ogrenilen parametreler): 0.81
```

Çıktı üç şeyi gösterir. Birincisi, ileri algoritma ile kaba kuvvet toplamı T = 8 için log-olasılıkta −8,3535052841 değerinde birebir aynıdır; Viterbi'nin en iyi yolu da kaba kuvvetle aynıdır. İkincisi, Viterbi ile gerçek yol arasındaki doğruluk 0,7833'tür; gözlem başına en iyi durum seçmek (geçişleri hesaba katmadan) yalnızca 0,6483 verir. Yani geçiş yapısı gerçekten bilgi taşır. Üçüncüsü, Baum–Welch log-olabilirliği her iterasyonda artar (monoton artış) ve 150 iterasyon sonunda −2700,9'a yakınsar.

Öğrenilen parametrelerin gerçeğe yakınlığı ise karışıktır ve bunu dürüstçe söylemek gerekir. Seyir durumunun emisyonu gerçek değere (0,15; 0,70; 0,15) yakındır (öğrenilen: 0,146; 0,731; 0,123). Ama kalkış durumu (gerçek: 0,20; 0,30; 0,50) iyi öğrenilmemiştir: öğrenilen 0,017; 0,427; 0,556'dır. Kalkış durumu eğitim verisinde yalnızca birkaç adım sürer (her uçuşta kısa); bu yüzden EM bu durumu zayıf tanımlar. Öğrenilen parametrelerle yapılan Viterbi doğruluğu (0,81), gerçek parametrelerle yapılandan (0,7833) biraz yüksek çıktı. Bu, öğrenilen modelin gerçek modelden daha iyi olduğu anlamına gelmez; tek bir test dizisinin örnekleme değişkenliğidir. Parametreler yerel bir optimuma yakınsadığı için kalkış durumu zayıf kalmıştır.

::: ipucu
Baum–Welch'in en sık tuzağı kimlik sorunudur: iki farklı yerel optimum aynı gözlemleri farklı durum etiketleriyle açıklayabilir. Durum isimlerini (kalkış, seyir, iniş) veriye bakarak sonradan atamak zorundasın; EM sana hangi sayının hangi fiziksel moda ait olduğunu söylemez.
:::

## 62.6 Durum uzayı modelleri ve Kalman filtresi

HMM'de durumlar ayrık bir kümeden gelir. Oysa bir İHA'nın konumu ve hızı süreklidir. Bu durumda model, durum uzayı modeli olarak yazılır:

x_k = F x_{k−1} + w_k,  w_k ~ N(0, Q)
z_k = H x_k + v_k,      v_k ~ N(0, R)

Burada x durum vektörü (konum, hız), F durum geçiş matrisi, Q süreç gürültüsü kovaryansı, z ölçüm, H ölçüm matrisi ve R ölçüm gürültüsü kovaryansıdır. Bu doğrusal Gauss modelinde posterior her zaman Gauss'tur; bu yüzden tüm dağılımı iki parametre, ortalama x̂ ve kovaryans P, temsil eder. **Kalman filtresi**, bu iki parametreyi her yeni ölçümle özyinelemeli olarak günceller.

Kalman filtresinin iki adımı vardır.

**Tahmin** (dinamik modele göre): x̂⁻ = F x̂ ve P⁻ = F P Fᵀ + Q. Ölçüm yokken de yapılabilir; belirsizlik Q kadar büyür.

**Güncelleme** (ölçüme göre): inovasyon ν = z − H x̂⁻, inovasyon kovaryansı S = H P⁻ Hᵀ + R, Kalman kazancı K = P⁻ Hᵀ S⁻¹, sonra x̂ = x̂⁻ + K ν ve P = (I − K H) P⁻.

Şekil 62.5, bu döngüyü gösterir: tahmin, ölçümle güncelleme, sonra bir sonraki adıma taşınma.

![Şekil 62.5: Kalman filtresinin tahmin ve güncelleme döngüsü](gorseller/b62_kalman_dongu.png)

### Tek boyutta sezgi: iki Gauss'un çarpımı

Kalman güncellemesinin sezgisi, Bölüm 49'daki 1B Gauss ölçüm birleştirmesidir. Önsel N(x̂⁻, P⁻) ile ölçüm N(z, R) çarpılır; sonuç yine bir Gauss'tur ve kesinlikler (1/varyans) toplanır: 1/P = 1/P⁻ + 1/R. Kazanç K = P⁻/(P⁻ + R) olur: ölçümün varyansı küçükse (R küçük) K büyür ve filtre ölçüme daha çok güvenir; önselin varyansı küçükse K küçülür ve filtre modele güvenir. Bu, "ölçüme mi modele mi güvenelim?" sorusunun tam matematiksel cevabıdır.

Bölüm 52'deki tümleyen filtre de aynı şeyi sezgisel olarak yapar: iki kaynağı sabit bir ağırlıkla karıştırır. Kalman filtresi bu ağırlığı belirsizliklerden hesaplar. Bölüm 62.9'da bu ilişkiyi tam olarak göstereceğiz.

Örnek 4'te tek boyutlu bir rastgele yürüyüş (x_k = x_{k−1} + w, z_k = x_k + v) için üç adımlık tahmin ve güncelleme izini elle izleyeceksin. Önce kendi sayılarını hesapla, sonra programla karşılaştır. Aşağıdaki kod hem bu izi üretir hem de 1B kesinlik toplama kuralını (1/P = 1/P⁻ + 1/R) bir doğrulama olarak kontrol eder.

```python
# -*- coding: utf-8 -*-
# b62_04_kalman.py: Kalman filtresi sifirdan. (1) 1B ornek izi,
# (2) 2B sabit hiz (DWNA) hedef takibi, (3) NEES/NIS tutarlilik,
# (4) eksik olcum, (5) Q/R ayari, (6) filterpy karsilastirmasi.
import numpy as np

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def tahmin(x, P, F, Q):
    """Tahmin adimi: x- = F x, P- = F P F^T + Q."""
    return F @ x, F @ P @ F.T + Q


def guncelle(x, P, z, H, R):
    """Guncelleme adimi. Joseph bicimi P'yi kararli tutar."""
    nu = z - H @ x  # inovasyon (yenilik)
    S = H @ P @ H.T + R  # inovasyon kovaryansi
    K = P @ H.T @ np.linalg.inv(S)  # Kalman kazanci
    x = x + K @ nu
    IKH = np.eye(len(x)) - K @ H
    P = IKH @ P @ IKH.T + K @ R @ K.T
    return x, P, K, nu, S


```

```python
def ornek4_iz():
    """1B rastgele yuruyus: x_k = x_{k-1} + w, z_k = x_k + v."""
    x, P = np.array([0.0]), np.array([[10.0]])
    Q, R = 0.1, 1.0
    zs = [2.0, 1.5, 3.0]
    print("adim    x-      P-      K       nu      x^      P")
    for k, z in enumerate(zs, 1):
        xm, Pm = tahmin(x, P, np.array([[1.0]]), np.array([[Q]]))
        x, P, K, nu, S = guncelle(
            xm, Pm, np.array([z]), np.array([[1.0]]), np.array([[R]])
        )
        print(
            "%d  %7.4f %7.4f %7.4f %7.4f %7.4f %7.4f"
            % (k, xm[0], Pm[0, 0], K[0, 0], nu[0], x[0], P[0, 0])
        )
        # Iki Gauss'un carpimi: 1/P = 1/P- + 1/R
        assert abs(1 / P[0, 0] - (1 / Pm[0, 0] + 1 / R)) < 1e-9


```

### İki boyutta hedef takibi: sabit hız modeli

Bir İHA'nın konumunu ölçmek için kullanılan sensörler (GPS, radar) gürültülüdür; hızını ise doğrudan görmezsin. Durum vektörünü x = [px, py, vx, vy] alırsak, sabit hız modeli şöyle yazılır: konum, hız kadar her adımda kayar. Kesikli zamanda F = [[1, 0, Δt, 0], [0, 1, 0, Δt], [0, 0, 1, 0], [0, 0, 0, 1]].

Süreç gürültüsü için **ayrık beyaz ivme** (DWNA) modelini kullanırız: ivme her adımda bağımsız bir Gauss gürültüsü olarak değişir, bunun etkisi Q = σ_a² G Gᵀ ile verilir, G = [Δt²/2, Δt²/2, Δt, Δt]ᵀ (her eksen için). Bu Q, gerçek ivme gürültüsüyle tutarlı olduğu için simülasyonun kendisi bu modelle üretilir.

Aşağıdaki kod, bu modeli kurar, gerçek bir yörünge ve gürültülü ölçümler simüle eder, sonra Kalman filtresini uygular. Ayrıca iki kontrol yapar: NEES ve NIS (aşağıda açıklanacak) ve filterpy ile karşılaştırma.

```python
def model_b(dt=1.0, q=0.5, sigma=5.0):
    """2B sabit hiz, durum = [px, py, vx, vy]; ivme gurultusu DWNA."""
    F = np.array(
        [[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]],
        float,
    )
    G = np.array(
        [[dt**2 / 2, 0], [0, dt**2 / 2], [dt, 0], [0, dt]], float
    )
    Q = q * G @ G.T  # sigma_a^2 = q
    H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], float)
    R = sigma**2 * np.eye(2)
    return F, G, Q, H, R


def simule(n, F, G, q, sigma, rng, x0=(0, 0, 20, 5)):
    """Gercek yorunge (ivme gurultulu) ve gurultulu olcumler."""
    x = np.array(x0, float)
    xs, zs = [], []
    for _ in range(n):
        a = rng.normal(0, np.sqrt(q), 2)
        x = F @ x + G @ a
        xs.append(x.copy())
        zs.append(x[:2] + rng.normal(0, sigma, 2))
    return np.array(xs), np.array(zs)


```

```python
def filtrele(zs, F, Q, H, R, sigma, eksik=None):
    """Kalman takibi. eksik: olcumsuz adimlarin bool dizisi."""
    x = np.array([zs[0][0], zs[0][1], 0.0, 0.0])
    P = np.diag([sigma**2, sigma**2, 100.0, 100.0])
    xs, Ps, nees, nis = [], [], [], []
    for k in range(len(zs)):
        if k > 0:
            x, P = tahmin(x, P, F, Q)
        if eksik is not None and eksik[k]:
            xs.append(x.copy())
            Ps.append(P.copy())
            continue
        x, P, K, nu, S = guncelle(x, P, zs[k], H, R)
        xs.append(x.copy())
        Ps.append(P.copy())
        nis.append(float(nu @ np.linalg.solve(S, nu)))
    return np.array(xs), np.array(Ps), np.array(nis)


def rms(a, b):
    return float(np.sqrt(np.mean(np.sum((a - b) ** 2, axis=-1))))


```

```python
def tutarlilik(n_kosu=50, n=100):
    """NEES (4 boyut) ve NIS (2 boyut) ortalamalari; dogru modelde
    NEES ~ 4 ve NIS ~ 2 beklenir."""
    F, G, Q, H, R = model_b()
    sonuc = {"dogru": [], "kucuk_q": []}
    for kosu in range(n_kosu):
        rng = np.random.default_rng(1000 + kosu)
        xt, zs = simule(n, F, G, 0.5, 5.0, rng)
        for ad, qm in [("dogru", 0.5), ("kucuk_q", 0.005)]:
            Qm = model_b(q=qm)[2]
            xs, Ps, nis = filtrele(zs, F, Qm, H, R, 5.0)
            e = xt - xs
            nees = [
                float(e[k] @ np.linalg.solve(Ps[k], e[k]))
                for k in range(n)
            ]
            sonuc[ad].append([np.mean(nees), np.mean(nis)])
    for ad in sonuc:
        a = np.array(sonuc[ad]).mean(axis=0)
        print(
            "[Tutarlilik] %-8s NEES=%.3f (4)  NIS=%.3f (2)"
            % (ad, a[0], a[1])
        )


```

```python
def ayar_deneyi(n_kosu=50, n=100):
    """Gercek q=0.5, sigma=5. Model q ve R olcegi degisince RMS."""
    F, G, Q, H, R = model_b()
    qs = [0.005, 0.05, 0.5, 5.0, 50.0]
    olcekler = [0.25, 1.0, 4.0]
    tablo = np.zeros((len(qs), len(olcekler)))
    for kosu in range(n_kosu):
        rng = np.random.default_rng(2000 + kosu)
        xt, zs = simule(n, F, G, 0.5, 5.0, rng)
        for i, qm in enumerate(qs):
            for j, sc in enumerate(olcekler):
                _, _, Qm, Hm, Rm = model_b(
                    q=qm, sigma=5.0 * np.sqrt(sc)
                )
                xs, _, _ = filtrele(
                    zs, F, Qm, Hm, Rm, 5.0 * np.sqrt(sc)
                )
                tablo[i, j] += rms(xs[:, :2], xt[:, :2]) / n_kosu
    print(
        "\n[Ayar] ort. RMS (m); satir q, sutun R olcegi 0.25 / 1 / 4"
    )
    for i, qm in enumerate(qs):
        print("q=%7.3f  %.3f  %.3f  %.3f" % (qm, *tablo[i]))
    satirlar = ["q,r025,r1,r4"]
    for i, qm in enumerate(qs):
        satirlar.append("%g,%.5f,%.5f,%.5f" % (qm, *tablo[i]))
    with open(VERI + "/b62_qr_ayar.csv", "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")


```

```python
def takip_ve_eksik(n=100):
    F, G, Q, H, R = model_b()
    rng = np.random.default_rng(62)
    xt, zs = simule(n, F, G, 0.5, 5.0, rng)
    xs, Ps, nis = filtrele(zs, F, Q, H, R, 5.0)
    print("\n[Takip] ham olcum RMS = %.3f m" % rms(zs, xt[:, :2]))
    print(
        "[Takip] filtre RMS    = %.3f m" % rms(xs[:, :2], xt[:, :2])
    )
    satirlar = ["k,tx,ty,zx,zy,fx,fy"]
    for k in range(n):
        satirlar.append(
            "%d,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f"
            % (
                k,
                xt[k, 0],
                xt[k, 1],
                zs[k, 0],
                zs[k, 1],
                xs[k, 0],
                xs[k, 1],
```

```python
            )
        )
    with open(
        VERI + "/b62_takip_yorunge.csv", "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    # Eksik olcum: 40-59 arasi yalnizca tahmin
    eksik = np.zeros(n, bool)
    eksik[40:60] = True
    xe, Pe, _ = filtrele(zs, F, Q, H, R, 5.0, eksik=eksik)
    print("[Eksik] 20 adim olcum yok: pozisyon belirsizligi (iz P)")
    for k in [39, 45, 55, 59, 65]:
        print(
            "   k=%d  sqrt(trP_konum)=%.2f  hata=%.2f"
            % (
                k,
                np.sqrt(np.trace(Pe[k][:2, :2])),
                np.linalg.norm(xe[k, :2] - xt[k, :2]),
            )
        )


```

```python
def filterpy_karsilastir(n=100):
    import filterpy
    from filterpy.kalman import KalmanFilter

    F, G, Q, H, R = model_b()
    rng = np.random.default_rng(62)
    xt, zs = simule(n, F, G, 0.5, 5.0, rng)
    xs, _, _ = filtrele(zs, F, Q, H, R, 5.0)
    kf = KalmanFilter(dim_x=4, dim_z=2)
    kf.x = np.array([[zs[0][0]], [zs[0][1]], [0.0], [0.0]])
    kf.F, kf.H, kf.Q, kf.R = F, H, Q, R
    kf.P = np.diag([25.0, 25.0, 100.0, 100.0])
    fp = []
    for k in range(n):
        if k > 0:
            kf.predict()
        kf.update(zs[k])
        fp.append(kf.x.ravel().copy())
    fp = np.array(fp)
    print(
        "\n[filterpy %s] en buyuk fark (kendi - filterpy): %.2e"
        % (filterpy.__version__, np.abs(xs - fp).max())
    )


if __name__ == "__main__":
    print("== 1B ornek izi ==")
    ornek4_iz()
    print("\n== 2B takip ve tutarlilik ==")
    takip_ve_eksik()
    tutarlilik()
    ayar_deneyi()
    filterpy_karsilastir()
```

```term
$ python b62_04_kalman.py
== 1B ornek izi ==
adim    x-      P-      K       nu      x^      P
1   0.0000 10.1000  0.9099  2.0000  1.8198  0.9099
2   1.8198  1.0099  0.5025 -0.3198  1.6591  0.5025
3   1.6591  0.6025  0.3760  1.3409  2.1632  0.3760

== 2B takip ve tutarlilik ==

[Takip] ham olcum RMS = 6.777 m
[Takip] filtre RMS    = 4.623 m
[Eksik] 20 adim olcum yok: pozisyon belirsizligi (iz P)
   k=39  sqrt(trP_konum)=4.54  hata=1.55
   k=45  sqrt(trP_konum)=16.61  hata=3.81
   k=55  sqrt(trP_konum)=49.00  hata=13.45
   k=59  sqrt(trP_konum)=64.96  hata=20.16
   k=65  sqrt(trP_konum)=4.76  hata=8.21
[Tutarlilik] dogru    NEES=4.289 (4)  NIS=2.031 (2)
[Tutarlilik] kucuk_q  NEES=177.371 (4)  NIS=8.798 (2)

[Ayar] ort. RMS (m); satir q, sutun R olcegi 0.25 / 1 / 4
q=  0.005  7.519  11.607  18.268
q=  0.050  4.793  5.924  8.710
q=  0.500  4.879  4.627  5.116
q=  5.000  5.735  5.186  4.820
q= 50.000  6.515  6.073  5.579

[filterpy 1.4.5] en buyuk fark (kendi - filterpy): 0.00e+00
```

Çıktıda ilk olarak Örnek 4'ün 1B izi görülür. İkinci olarak, 2B takipte ham ölçümün RMS hatası 6,777 m iken filtre 4,623 m'ye iner: filtre, ölçümleri hem konum hem hız modeliyle birleştirdiği için gürültüyü azaltır. Şekil 62.6 gerçek yörüngeyi, gürültülü ölçümleri ve filtre tahminini çizer.

![Şekil 62.6: 2B sabit hız modeliyle takip: gerçek yörünge, ölçümler ve Kalman tahmini](gorseller/b62_takip_2b.png)

### Tutarlılık kontrolü: NEES ve NIS

Bir filtrenin yalnızca hatası küçük değil, aynı zamanda belirsizliği de doğru olmalıdır. Bunu kontrol etmenin iki standart yolu vardır. **NEES** (normalize hata kareleri toplamı), e = x_gerçek − x̂ olmak üzere eᵀ P⁻¹ e'dir; doğru modelde ortalaması durum boyutu n_x'e (burada 4) eşit olmalıdır. **NIS** (normalize inovasyon kareleri), νᵀ S⁻¹ ν'dür; ortalaması ölçüm boyutu n_z'ye (burada 2) eşit olmalıdır. Bu iki değer, filtrenin "kendine ne kadar güvendiğini" ölçer.

Kodda 50 koşu ve her koşuda 100 adımla iki model karşılaştırıldı. Doğru Q ile NEES ortalaması 4,289 ve NIS ortalaması 2,031 çıktı; beklenen değerlere çok yakın. Gerçek Q'nun yüzde biri kadar (0,005) bir model Q ile NEES 177,4'e çıkar: filtre kendine fazla güveniyor, belirsizliği küçük tutuyor ve hatalarını bu yüzden düzeltemiyor. Bu, tutarlılık kontrolünün gücünü gösterir: hata küçük olmasa da belirsizlik yanlışsa NEES bunu yakalar.

### Q ve R'nin etkisi: ayar deneyi

Q ve R, modelin iki temel ayarıdır. Q büyükse filtre hızlı değişen hedeflere uyum sağlar ama ölçüm gürültüsünü de takip eder. R büyükse filtre ölçüme az güvenir ve yumuşak ama gecikmeli bir yörünge çizer. Gerçek q = 0,5 ve σ = 5 m için beş model q değeri ve üç R ölçeği (0,25, 1, 4) denendi, her biri 50 koşuda ortalandı.

Tablo, sonucu gösterir: en düşük RMS (4,63 m) q = 0,5 ve R ölçeği 1 ile elde edilmiştir; bu doğru modeldir. Ama R ölçeği 0,25 ve q = 0,05 gibi bir kombinasyon (4,79 m) doğru modele çok yakın sonuç verir. Yani Q ve R birbirini telafi eder: ölçüme daha az güvenirsen, süreç gürültüsünü de düşürerek aynı dengeye ulaşabilirsin. Gerçek ayar tek bir parametrenin değil, oranın ayarıdır. Şekil 62.7 bu sonucu gösterir.

![Şekil 62.7: Model süreç gürültüsü q ve R ölçeğinin ortalama konum RMS hatasına etkisi](gorseller/b62_qr_ayar.png)

### Eksik ölçümler: yalnızca tahmin adımı

Bir GPS sinyali kaybolduğunda ya da radar bir süre hedefi görmediğinde ölçüm yoktur. Kalman filtresinde bu adımda yalnızca tahmin yapılır: x̂ dinamik modelle ilerler, P ise Q kadar büyür. Belirsizlik zamanla büyür ve ölçüm geldiğinde filtre hemen güncellenir. Kodda 40-59 arası 20 adım ölçüm yok ve belirsizlik konum için 4,54 m'den 64,96 m'ye çıktı; ölçüm yeniden geldiğinde (k = 65) belirsizlik 4,76 m'ye indi. Bu, belirsizliğin bir sigorta değil bir ölçü olduğunu gösterir.

### filterpy ile karşılaştırma

FilterPy kütüphanesi (sürüm 1.4.5) aynı modeli kendi KalmanFilter sınıfıyla çalıştırdı ve bizim filtremizle yörüngeler arasındaki en büyük fark 0,00 çıktı. Bu, sıfırdan yazdığımız filtrenin kütüphaneyle birebir aynı matematiği uyguladığını gösterir. Kod Okuma bölümünde FilterPy'nin `update` fonksiyonunu satır satır okuyacaksın.

## 62.7 Genişletilmiş Kalman filtresi (EKF): doğrusal olmayan ölçüm

Kalman filtresinin varsayımı doğrusal bir ölçüm modelidir: z = H x + v. Radar ise doğrusal değildir. Hedef konumu (px, py) olan bir radar, menzil r = √(px² + py²) ve yön açısı θ = atan2(py, px) ölçer. Bu fonksiyon doğrusal değildir ve ölçüm gürültüsü artık Gauss kalmaz.

**Genişletilmiş Kalman filtresi (EKF)**, ölçüm fonksiyonunu tahmin edilen durum etrafında doğrusallaştırır. Bunu Bölüm 55'teki Jacobian matrisiyle yaparsın: h(x) fonksiyonunun kısmi türevlerinden oluşan matris. Radar için iki satırlı Jacobian şöyledir:

∂r/∂px = px/r,     ∂r/∂py = py/r
∂θ/∂px = −py/r²,   ∂θ/∂py = px/r²

Geri kalan adımlar Kalman filtresiyle aynıdır, yalnızca H yerine her adımda yeniden hesaplanan Jacobian kullanılır ve inovasyon h(x⁻) ile ölçümün farkıdır. Bu, doğrusal olmayan bir fonksiyonu yerel bir doğrusal yaklaşımla değiştirmektir. Yaklaşım, durum belirsizliği küçükken iyi çalışır; belirsizlik büyükse (örneğin ilk tahmin çok kötüyse) yanlış bir doğrusallaştırma filtreyi ıraksatabilir.

Açı ile çalışırken bir tuzak vardır. İnovasyonda θ_ölçüm − θ_tahmin farkı 2π'ye yakın olabilir (örneğin −179° ile +179°, aslında 2° fark). Bu farkı [−π, π) aralığına sarmalamak zorunludur; yoksa filtre gerçekte küçük olan bir hatayı büyük sanar.

Şekil 62.8, aynı radar senaryosunda gerçek yörüngeyi, EKF tahminini ve parçacık filtresinin tahminini gösterir. Parçacık filtresi bir sonraki bölümde anlatılacaktır; iki yöntem birlikte karşılaştırılacağı için figür burada da verilir.

![Şekil 62.8: Radar senaryosunda gerçek yörünge, EKF ve parçacık filtresi tahminleri](gorseller/b62_radar_ekf_pf.png)

## 62.8 Parçacık filtresi: Monte Carlo ile doğrusal olmayan durum kestirimi

Kalman ve EKF, posterior'u Gauss ile temsil eder. Gerçek dünyada posterior çok modlu olabilir (örneğin radar bir hedefin iki farklı geçerli konumu olduğunu söylüyorsa) ya da çarpık olabilir. **Parçacık filtresi** posterior'u N tane ağırlıklı örnekle (parçacık) temsil eder. Dağılımın biçimi hakkında hiçbir varsayım yapmaz.

Bir adımda üç iş yapılır. **Tahmin**: her parçacık dinamik modele göre ilerletilir (gürültü eklenerek). **Ağırlıklandırma**: her parçacığın ağırlığı ölçümün olasılığıyla güncellenir, w_i ∝ w_i · p(z | x^(i)). Ağırlıklar normalize edilir. **Yeniden örnekleme**: ağırlıklar tek bir parçacığa yığılmasın diye parçacıklar ağırlıklarına göre yeniden seçilir.

Ağırlıkların ne kadar eşit dağıldığını ölçmek için **etkin örnek sayısı** (ESS = 1 / Σ w_i²) kullanılır. Tüm ağırlıklar eşitse ESS = N; tek bir parçacık her şeyi taşıyorsa ESS ≈ 1. ESS düşükse filtre **dejenere** olmuş demektir: birkaç parçacık dışındakiler işe yaramaz.

Yeniden örnekleme yöntemi önemlidir. Sistematik yeniden örnekleme, tek bir rastgele u_0 ∈ [0, 1/N) seçer ve u_i = u_0 + i/N noktalarını ağırlıkların kümülatif toplamında arar. Bu yöntem tek bir rastgele sayı kullandığı için örnekleme gürültüsünü multinomial yeniden örneklemeye göre azaltır; ağırlıkların kümülatif toplamı üzerinde tek bir sıralı tarama ile yapılabilir. Kod bunu sıfırdan yazar.

Parçacık yoksullaşması (particle impoverishment), yeniden örneklemeden sonra çok az farklı parçacık kalmasıdır: aynı parçacık çoğaltılır ve filtre belirsizliği temsil edemez hâle gelir. Yaygın çare, yeniden örneklemeden sonra küçük bir süreç gürültüsü eklemektir. Burada böyle bir çare kullanmadık; N küçükken bunun etkisini deneyle gözlemleyeceksin.

Aşağıdaki kod, radar senaryosunu kurar: hedef sabit hızla radarın yakınından geçer, ölçümler menzil ve açı olarak gürültülüdür. Sonra EKF ile parçacık filtresini 30 koşu boyunca karşılaştırır, parçacık sayısının etkisini ölçer ve tek bir koşunun yörüngesini kaydeder.

```python
# -*- coding: utf-8 -*-
# b62_05_ekf_pf.py: Radar olcumlu hedef takibi. EKF (Jacobian ile
# dogrusallastirma) ve parcacik filtresi (sistematik yeniden
# ayni senaryoda karsilastirma. Kalman modeli b62_04'ten.
import time
import numpy as np
from b62_04_kalman import model_b, simule, tahmin, guncelle

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
RADAR = np.array([0.0, 0.0])  # radar konumu (orijin)


def radar_olc(x):
    """Menzil r = sqrt(px^2+py^2), yon acisi theta = atan2(py, px)."""
    dx, dy = x[0] - RADAR[0], x[1] - RADAR[1]
    return np.array([np.hypot(dx, dy), np.arctan2(dy, dx)])


def radar_jakobiyen(x):
    """h(x) icin 2x4 Jacobian (durum [px,py,vx,vy])."""
    dx, dy = x[0] - RADAR[0], x[1] - RADAR[1]
    r2 = dx * dx + dy * dy
    r = np.sqrt(r2)
    return np.array(
        [[dx / r, dy / r, 0, 0], [-dy / r2, dx / r2, 0, 0]]
    )


def aci_sar(a):
    """Aciyi [-pi, pi) araligina getirir (inovasyonda sart)."""
    return (a + np.pi) % (2 * np.pi) - np.pi


```

```python
def ekf(zs, F, Q, R, x0, P0):
    x, P = x0.copy(), P0.copy()
    xs = []
    for k in range(len(zs)):
        if k > 0:
            x, P = tahmin(x, P, F, Q)
        H = radar_jakobiyen(x)
        nu = zs[k] - radar_olc(x)
        nu[1] = aci_sar(nu[1])
        S = H @ P @ H.T + R
        K = P @ H.T @ np.linalg.inv(S)
        x = x + K @ nu
        IKH = np.eye(4) - K @ H
        P = IKH @ P @ IKH.T + K @ R @ K.T
        xs.append(x.copy())
    return np.array(xs)


```

```python
def sistematik_yeniden_ornekle(agirlik, rng):
    """Sistematik yeniden ornekleme: tek u0, N esit aralik."""
    n = len(agirlik)
    konum = (rng.random() + np.arange(n)) / n
    kum = np.cumsum(agirlik)
    kum[-1] = 1.0
    return np.searchsorted(kum, konum)


```

```python
def parcacik(zs, F, Q, R, x0, P0, N, rng):
    parc = rng.multivariate_normal(x0, P0, size=N)
    w = np.full(N, 1.0 / N)
    Lq = np.linalg.cholesky(Q + 1e-12 * np.eye(4))
    Ri = np.linalg.inv(R)
    xs, ess_log = [], []
    for k in range(len(zs)):
        if k > 0:
            parc = parc @ F.T + rng.standard_normal((N, 4)) @ Lq.T
        # olabilirlik: log w += log N(z; h(x), R), aci farki sarmali
        dx = parc[:, 0] - RADAR[0]
        dy = parc[:, 1] - RADAR[1]
        nu = np.column_stack(
            [
                zs[k][0] - np.hypot(dx, dy),
                aci_sar(zs[k][1] - np.arctan2(dy, dx)),
            ]
        )
        logw = -0.5 * np.einsum("ni,ij,nj->n", nu, Ri, nu)
        logw += np.log(w + 1e-300)
        logw -= logw.max()
        w = np.exp(logw)
        w /= w.sum()
        ess_log.append(1.0 / np.sum(w**2))
        xs.append(w @ parc)
        idx = sistematik_yeniden_ornekle(w, rng)
        parc = parc[idx]
        w = np.full(N, 1.0 / N)
    return np.array(xs), np.array(ess_log)


```

```python
def senaryo(
    seed, n=60, x_bas=(-60.0, 8.0, 3.0, -1.0), rad_sig=(3.0, 1.5)
):
    """Hedef radara yakin gecer; radar acisi dogrusal olmayan.
    Gercek model: sabit hiz + kucuk ivme gurultusu (b62_04 ile ayni).
    """
    F, G, Q, H, R_k = model_b(q=0.5, sigma=5.0)
    rng = np.random.default_rng(seed)
    xt = np.zeros((n, 4))
    x = np.array(x_bas, float)
    for k in range(n):
        x = F @ x + G @ rng.normal(0, np.sqrt(0.5), 2)
        xt[k] = x
    rad_sigma = np.array([rad_sig[0], np.radians(rad_sig[1])])
    zs = np.array(
        [
            radar_olc(xt[k]) + rng.normal(0, rad_sigma)
            for k in range(n)
        ]
    )
    for k in range(n):
        zs[k][1] = aci_sar(zs[k][1])
    R = np.diag(rad_sigma**2)
    return xt, zs, F, Q, R


```

```python
def konum_rms(xs, xt):
    return float(
        np.sqrt(np.mean(np.sum((xs[:, :2] - xt[:, :2]) ** 2, 1)))
    )


def ilk_durum(zs, R):
    """Ilk tahmin: ilk olcumden konum, hiz belirsiz."""
    r, th = zs[0]
    x0 = np.array([r * np.cos(th), r * np.sin(th), 0.0, 0.0])
    P0 = np.diag([25.0, 25.0, 25.0, 25.0])
    return x0, P0


```

```python
def karsilastir(kosu=30, **sk):
    n = 60
    ekf_h, pf_h, pf_t = [], [], []
    for s in range(kosu):
        xt, zs, F, Q, R = senaryo(3000 + s, n, **sk)
        x0, P0 = ilk_durum(zs, R)
        ekf_h.append(konum_rms(ekf(zs, F, Q, R, x0, P0), xt))
        t0 = time.time()
        xp, _ = parcacik(
            zs, F, Q, R, x0, P0, 1000, np.random.default_rng(s)
        )
        pf_t.append(time.time() - t0)
        pf_h.append(konum_rms(xp, xt))
    ekf_h, pf_h = np.array(ekf_h), np.array(pf_h)
    print("\n[EKF vs PF] %d kosu, N=1000, n=%d adim" % (kosu, n))
    print(
        "EKF konum RMS: ort %.3f  medyan %.3f  en kotu %.3f"
        % (ekf_h.mean(), np.median(ekf_h), ekf_h.max())
    )
    print(
        "PF  konum RMS: ort %.3f  medyan %.3f  en kotu %.3f"
        % (pf_h.mean(), np.median(pf_h), pf_h.max())
    )
    print("PF kosu suresi ort: %.2f s" % np.mean(pf_t))


```

```python
def parcacik_sayisi(kosu=30):
    n = 60
    print("\n[N etkisi] PF konum RMS, ESS ort.")
    satirlar = ["N,rms_ort,rms_ss,ess_ort"]
    for N in [10, 50, 200, 1000, 5000]:
        rm, ess = [], []
        for s in range(kosu):
            xt, zs, F, Q, R = senaryo(3000 + s, n)
            x0, P0 = ilk_durum(zs, R)
            xp, e = parcacik(
                zs, F, Q, R, x0, P0, N, np.random.default_rng(100 + s)
            )
            rm.append(konum_rms(xp, xt))
            ess.append(e.mean())
        rm = np.array(rm)
        print(
            "N=%5d  RMS %.3f (ss %.3f)  ESS ort %.1f"
            % (N, rm.mean(), rm.std(), np.mean(ess))
        )
        satirlar.append(
            "%d,%.5f,%.5f,%.3f"
            % (N, rm.mean(), rm.std(), np.mean(ess))
        )
    with open(VERI + "/b62_pf_N.csv", "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")


```

```python
def radar_iz(seed=3000):
    """Tek kosu: gercek, EKF ve PF yorungeleri (sekil icin CSV)."""
    n = 60
    xt, zs, F, Q, R = senaryo(seed, n)
    x0, P0 = ilk_durum(zs, R)
    xe = ekf(zs, F, Q, R, x0, P0)
    xp, _ = parcacik(
        zs, F, Q, R, x0, P0, 1000, np.random.default_rng(seed)
    )
    satirlar = ["k,tx,ty,ex,ey,px,py"]
    for k in range(n):
        satirlar.append(
            "%d,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f"
            % (
                k,
                xt[k, 0],
                xt[k, 1],
                xe[k, 0],
                xe[k, 1],
                xp[k, 0],
                xp[k, 1],
            )
        )
    with open(VERI + "/b62_radar_iz.csv", "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
    print(
        "\n[Tek kosu] EKF RMS %.3f, PF RMS %.3f"
        % (konum_rms(xe, xt), konum_rms(xp, xt))
    )


if __name__ == "__main__":
    print("== EKF vs PF ==")
    karsilastir(30)
    karsilastir(30, x_bas=(-12.0, 4.0, 2.0, 0.0), rad_sig=(3.0, 5.0))
    print("\n== Parcacik sayisi ==")
    parcacik_sayisi(30)
    radar_iz(3000)
```

```term
$ python b62_05_ekf_pf.py
== EKF vs PF ==

[EKF vs PF] 30 kosu, N=1000, n=60 adim
EKF konum RMS: ort 3.033  medyan 3.081  en kotu 3.866
PF  konum RMS: ort 3.057  medyan 3.100  en kotu 3.942
PF kosu suresi ort: 0.02 s

[EKF vs PF] 30 kosu, N=1000, n=60 adim
EKF konum RMS: ort 5.711  medyan 5.440  en kotu 8.954
PF  konum RMS: ort 5.708  medyan 5.307  en kotu 9.469
PF kosu suresi ort: 0.02 s

== Parcacik sayisi ==

[N etkisi] PF konum RMS, ESS ort.
N=   10  RMS 39.190 (ss 39.482)  ESS ort 3.7
N=   50  RMS 7.236 (ss 6.829)  ESS ort 20.4
N=  200  RMS 3.381 (ss 0.610)  ESS ort 81.1
N= 1000  RMS 3.061 (ss 0.474)  ESS ort 400.9
N= 5000  RMS 3.000 (ss 0.454)  ESS ort 1990.6

[Tek kosu] EKF RMS 2.901, PF RMS 3.095
```

Çıktı, beklediğimizden farklı bir tablo verdi ve bunu olduğu gibi okumak gerekir. Standart senaryoda (hedef radardan uzak geçer, menzil σ = 3 m, açı σ = 1,5°) EKF ortalama konum RMS'i 3,033 m, parçacık filtresi (N = 1000) 3,057 m verdi. İkisi neredeyse aynıdır. Radara yakın geçen ve açı gürültüsü 5° olan zor senaryoda (ikinci blok) EKF 5,711 m, parçacık filtresi 5,708 m verdi; medyanda EKF 5,440 m, parçacık filtresi 5,307 m. Yani bu iki senaryoda parçacık filtresinin belirgin bir üstünlüğü görülmedi. Bu sonuç, parçacık filtresinin her zaman daha iyi olduğu beklentisini çürütür: EKF'nin yaklaşımı, bu ölçüm gürültüsü seviyesinde yeterince iyidir. Parçacık filtresinin asıl avantajı, posterior'un Gauss'tan gerçekten saptığı durumlarda (çok modlu belirsizlik, güçlü doğrusal olmayanlık) ortaya çıkar; bu deney onu göstermiyor. Dürüst sonuç budur.

Parçacık sayısı deneyi ise net bir trend gösterir. N = 10 ile ortalama RMS 39,19 m'ye çıkar ve ESS ortalaması yalnızca 3,7'dir: filtre dejenere olmuştur. N = 50'de RMS 7,24 m (ESS 20,4), N = 200'de 3,38 m (ESS 81,1), N = 1000'de 3,06 m (ESS 400,9) ve N = 5000'de 3,00 m. Hata, N arttıkça kararlı bir tavana yaklaşır; küçük N'de ise hem ortalama hem de koşular arası sapma çok büyüktür. Şekil 62.9 bu eğriyi gösterir.

Yörünge çizimi (Şekil 62.8) iki filtrenin de gerçek yörüngeyi yakından izlediğini gösterir; sapmalar hem EKF'de hem parçacık filtresinde benzerdir.

![Şekil 62.9: Parçacık sayısına göre konum hatası (30 koşu; log–log ölçek)](gorseller/b62_pf_n.png)

::: dikkat
Parçacık filtresi "daha genel" olduğu için her zaman tercih edilmez. Hesap maliyeti N ile orantılıdır, ayrıca N'i ve yeniden örnekleme stratejisini sen seçersin. Bir sistemde EKF yeterliyse, parçacık filtresinin karmaşıklığı bir kazanç değil bir yüktür.
:::

## 62.9 Sensör füzyonu: tümleyen filtre, Kalman ve çok sensörlü güncelleme

Bir İHA'nın konumu tek bir sensörle yeterince iyi ölçülmez. IMU (ivmeölçer ve jiroskop) hızlı ve pürüzsüz bir hız sinyali verir ama zamanla sürüklenir (yanlılık). GPS doğru ama yavaş ve gürültülüdür. Füzyon, iki kaynağı birleştirerek her birinin zayıf yanını gidermektir.

Bölüm 52'deki **tümleyen filtre** bu fikrin en basit biçimidir: x̂_k = α (x̂_{k−1} + v_IMU Δt) + (1 − α) z_GPS. IMU ile integre edilen konum kısa vadede güvenilirdir, GPS ise uzun vadede düzeltir. Sabit α ile iki kaynağı tartmak, sezgisel ama etkilidir.

Bu filtrenin Kalman ile ilişkisini görmek için Kalman'ın tahmin ve güncellemesini yazalım. Tahmin: x⁻ = x̂ + v Δt. Güncelleme: x̂ = x⁻ + K (z − x⁻) = (1 − K) x⁻ + K z. Bu iki ifade, α = 1 − K seçildiğinde tümleyen filtreyle **birebir aynıdır**. Yani tümleyen filtre, kazancı sabit tutulmuş bir Kalman filtresidir. Kalman'ın avantajı, K'yi her adımda belirsizliklerden hesaplamasıdır; sabit kazanç ise sürekli durum için bir yaklaşımdır.

Sabit kazancın değeri Riccati denkleminin durağan hâlinden gelir: P⁻ = P + Q, K = P⁻ / (P⁻ + R), P = (1 − K) P⁻ iterasyonu yakınsayınca K_ss elde edilir. Kodda Q = 0,0025 ve R = 4 (GPS σ = 2 m) için K_ss = 0,02469 ve α = 0,97531 bulundu. Kalman'ın son adımdaki kazancı da 0,02469'dur: yakınsamış durumdadır.

```python
# -*- coding: utf-8 -*-
# b62_06_fuzyon_bayes.py: (1) tumleyen filtre = sabit kazancli Kalman,
# (2) cok sensorlu birlestirme (sirali = yigin), (3) Bayesci
# dogrusal regresyon (kapali form, Ridge = MAP), (4) MH dogrulama.
import numpy as np

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


# ---------- (1) IMU + GPS: tumleyen filtre ve Kalman ----------
```

```python
def senaryo_imu_gps(n=600, dt=0.1, seed=62):
    rng = np.random.default_rng(seed)
    v = 5.0
    x = np.zeros(n)
    for k in range(1, n):
        x[k] = x[k - 1] + v * dt + rng.normal(0, 0.05)
    v_imu = v + 0.2 + rng.normal(0, 0.5, n)  # sabit yanlilik 0,2
    z_gps = x + rng.normal(0, 2.0, n)  # sigma = 2 m
    return x, v_imu, z_gps, dt


def tumleyen(v_imu, z, dt, alpha, x0=0.0):
    x = np.zeros(len(z))
    x[0] = x0
    for k in range(1, len(z)):
        x[k] = alpha * (x[k - 1] + v_imu[k] * dt) + (1 - alpha) * z[k]
    return x


def kalman_1b(v_imu, z, dt, Q, R, x0=0.0, P0=100.0):
    x, P = x0, P0
    out, K_ler = np.zeros(len(z)), np.zeros(len(z))
    out[0] = x
    for k in range(1, len(z)):
        x = x + v_imu[k] * dt  # tahmin (IMU ile)
        P = P + Q
        K = P / (P + R)  # kazanc
        x = x + K * (z[k] - x)  # guncelleme (GPS ile)
        P = (1 - K) * P
        out[k], K_ler[k] = x, K
    return out, K_ler


```

```python
def tumleyen_ve_kalman():
    x, v_imu, z, dt = senaryo_imu_gps()
    Q, R = 0.0025, 4.0
    kal, K = kalman_1b(v_imu, z, dt, Q, R)
    # sabit kazanc: Riccati'nin durgun hali (P- ve P iterasyonu)
    P = 100.0
    for _ in range(2000):
        Pm = P + Q
        Kss = Pm / (Pm + R)
        P = (1 - Kss) * Pm
    alpha = 1 - Kss
    tum = tumleyen(v_imu, z, dt, alpha, x0=kal[0])
    print(
        "[Fuzyon] Kalman K (son adim) = %.5f, K_ss = %.5f"
        % (K[-1], Kss)
    )
    print("[Fuzyon] tumleyen alpha = 1 - K_ss = %.5f" % alpha)
    print(
        "[Fuzyon] RMS  ham GPS  = %.3f m"
        % np.sqrt(np.mean((z - x) ** 2))
    )
    print(
        "[Fuzyon] RMS  Kalman   = %.3f m"
        % np.sqrt(np.mean((kal - x) ** 2))
    )
    print(
        "[Fuzyon] RMS  tumleyen = %.3f m"
        % np.sqrt(np.mean((tum - x) ** 2))
    )
    print(
        "[Fuzyon] tumleyen-Kalman, 400. adimdan sonra fark: %.2e"
        % np.abs(tum[400:] - kal[400:]).max()
    )


# ---------- (2) Cok sensorlu olcum birlestirme ----------
```

Tümleyen filtre ile Kalman'ın yörüngeleri ilk adımlarda farklıdır, çünkü Kalman P_0 = 100 gibi büyük bir başlangıç belirsizliğiyle başlar ve ilk adımlarda kazancı yüksektir. Bu geçici fark (1 − K)^k ile söner. Kodda 400. adımdan sonra iki yörünge arasındaki en büyük fark 4,98·10^-5'tir; 0,975^400 ≈ 4·10^-5 olduğu için bu tam olarak beklenen sönümdür. RMS değerleri de bunu yansıtır: ham GPS 2,071 m, Kalman 0,887 m, tümleyen filtre 0,906 m. Toplam pencerede tümleyen filtrenin biraz daha yüksek hata vermesinin büyük olasılıkla nedeni, Kalman'ın ilk adımlardaki büyük kazancıdır; bu, ilk birkaç yüz adımda hata toplamına katkı yapar.

### Çok sensörlü ölçüm birleştirme

Bir adımda birden fazla ölçüm varsa (IMU'dan bir hız, GPS'ten bir konum, bir radardan bir menzil) bunları iki şekilde işleyebilirsin: sırayla ya da tek bir yığılmış vektör olarak. Gauss modelinde iki yol aynı posterior'u verir: sıralı güncellemeler yığılmış güncellemeye eşdeğerdir (ölçümler bağımsızsa). Kodda bu, rastgele bir 3 boyutlu durumla ve üç ölçümle doğrulandı; x ve P farkı 10^-16 mertebesindedir. Bu özellik, ölçüm sensörleri farklı hızlarda geldiğinde her ölçümü geldiği anda işlemene izin verir.

```python
def guncelle_kalman(x, P, z, H, R):
    S = H @ P @ H.T + R
    K = P @ H.T @ np.linalg.inv(S)
    x = x + K @ (z - H @ x)
    P = (np.eye(len(x)) - K @ H) @ P
    return x, P


def cok_sensor():
    rng = np.random.default_rng(7)
    x0 = rng.normal(size=3)
    P0 = np.diag([2.0, 1.0, 0.5])
    H1 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    H2 = np.array([[0.0, 1.0, 1.0]])
    R1 = np.diag([0.5, 0.8])
    R2 = np.array([[0.3]])
    z1 = rng.normal(size=2)
    z2 = rng.normal(size=1)
    # sirali: once 1, sonra 2
    x_s, P_s = guncelle_kalman(x0, P0, z1, H1, R1)
    x_s, P_s = guncelle_kalman(x_s, P_s, z2, H2, R2)
    # yigin: tek adimda iki olcum birlikte
    H = np.vstack([H1, H2])
    R = np.block([[R1, np.zeros((2, 1))], [np.zeros((1, 2)), R2]])
    x_y, P_y = guncelle_kalman(x0, P0, np.concatenate([z1, z2]), H, R)
    print(
        "\n[Cok sensor] sirali ve yigin farki (x): %.2e, (P): %.2e"
        % (np.abs(x_s - x_y).max(), np.abs(P_s - P_y).max())
    )


# ---------- (3) Bayesci dogrusal regresyon ----------
```

## 62.10 Bayesçi doğrusal regresyon: parametre belirsizliği

Şimdiye kadar parametreleri tek bir değer olarak tahmin ettin. Bayesçi bakışta parametre de bir rastgele değişkendir ve veriden sonra bir dağılım (sonsal) olarak tanımlanır. Doğrusal regresyonda bu çok açıktır. Olabilirlik y | w ~ N(Φw, β⁻¹ I) (β = 1/σ² kesinlik) ve önsel w ~ N(0, α⁻¹ I) olsun. Gauss-Gauss çarpımı kapalı formda bir sonsal verir (Bishop'un kitabında da bu biçimde yazılır; genel bilgi):

S_N = (α I + β Φᵀ Φ)⁻¹,     m_N = β S_N Φᵀ y

Tahminin belirsizliği yeni bir x için şöyle hesaplanır: Var(y(x)) = 1/β + φ(x)ᵀ S_N φ(x). İlk terim gürültüdür ve veriyle azalmaz; ikinci terim parametre belirsizliğidir ve veri arttıkça küçülür. Bu ayrım önemlidir: sonsuz veriyle bile ölçüm gürültüsü kalır.

Şekil 62.10, N = 2, 10 ve 50 veriyle öğrenilen doğruyu ve ±2σ tahmin bandını gösterir. N = 2 iken bant çok geniştir ve özellikle veri aralığının dışında hızla açılır. N = 50'de bant gerçek doğrunun etrafında dardır.

```python
def bayes_lin(Phi, y, alpha, beta):
    """Onsel N(0, alpha^-1 I), olabilirlik N(Phi w, beta^-1 I)."""
    S_N = np.linalg.inv(
        alpha * np.eye(Phi.shape[1]) + beta * Phi.T @ Phi
    )
    m_N = beta * S_N @ Phi.T @ y
    return m_N, S_N


def ozellik(x):
    return np.column_stack([np.ones_like(x), x])


```

```python
def bayes_bant():
    alpha, beta = 2.0, 1.0 / 0.3**2
    rng = np.random.default_rng(62)
    grid = np.linspace(-1, 1, 101)
    satirlar = ["N,x,ort,ss"]
    nokta = ["N,x,y"]
    for N in [2, 10, 50]:
        x = rng.uniform(-1, 1, N)
        y = 0.5 + 1.2 * x + rng.normal(0, 0.3, N)
        Phi = ozellik(x)
        m_N, S_N = bayes_lin(Phi, y, alpha, beta)
        G = ozellik(grid)
        ort = G @ m_N
        ss = np.sqrt(1 / beta + np.sum((G @ S_N) * G, axis=1))
        print(
            "N=%2d  m_N=(%.3f, %.3f)  tahmin belirsizligi x=0,9: %.3f"
            % (N, m_N[0], m_N[1], ss[95])
        )
        for g, o, s in zip(grid, ort, ss):
            satirlar.append("%d,%.4f,%.5f,%.5f" % (N, g, o, s))
        for a, b in zip(x, y):
            nokta.append("%d,%.4f,%.4f" % (N, a, b))
    with open(
        VERI + "/b62_bayes_bant.csv", "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    with open(
        VERI + "/b62_bayes_nokta.csv", "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(nokta) + "\n")


```

![Şekil 62.10: Bayesçi doğrusal regresyonda tahmin belirsizliği bandı: N = 2, 10, 50](gorseller/b62_bayes_bant.png)

Bayesçi regresyonun Ridge ile bağlantısı Bölüm 58'de vaat edilmişti. Sonsal ortalama m_N, MAP tahminidir ve bu, λ = α/β olmak üzere (ΦᵀΦ + λ I)⁻¹ Φᵀ y Ridge çözümüne eşittir. Kodda bu eşitlik 50 örnekle sınandı: m_N = (0,490076; 1,205965), kapalı form Ridge ve scikit-learn Ridge de aynı iki değeri verdi (λ = 0,18). Yani L2 cezası, Gauss önseline karşılık gelir; bu, Bölüm 49'daki MAP ile Bölüm 58'deki regülarizasyonun aynı şey olduğunu sayısal olarak gösterir.

```python
def ridge_esdegeri():
    from sklearn.linear_model import Ridge

    alpha, beta = 2.0, 1.0 / 0.3**2
    rng = np.random.default_rng(62)
    x = rng.uniform(-1, 1, 50)
    y = 0.5 + 1.2 * x + rng.normal(0, 0.3, 50)
    Phi = ozellik(x)
    m_N, _ = bayes_lin(Phi, y, alpha, beta)
    lam = alpha / beta
    w_r = np.linalg.solve(Phi.T @ Phi + lam * np.eye(2), Phi.T @ y)
    sk = Ridge(alpha=lam, fit_intercept=False).fit(Phi, y).coef_
    print("\n[MAP=Ridge] lambda = alpha/beta = %.5f" % lam)
    print("  sonsal ortalama m_N     :", np.round(m_N, 6))
    print("  Ridge kapali form       :", np.round(w_r, 6))
    print("  sklearn Ridge           :", np.round(sk, 6))


# ---------- (4) Metropolis-Hastings ile dogrulama ----------
```

### Metropolis–Hastings ile sonsal örnekleme

Bu problemde sonsal kapalı formda olduğu için bir MCMC yöntemine ihtiyacın yoktur. Ama sonsal kapalı form olmadığında (doğrusal olmayan model, karmaşık önsel) sonsal dağılımdan örnek almanın standart yolu Markov Zinciri Monte Carlo (MCMC) yöntemleridir. En basiti Metropolis–Hastings'tir: mevcut durumdan rastgele bir aday çek, sonsal oranına göre kabul et veya reddet. Kabul kuralı, log-sonsal farkına dayanır: log u < log p(aday) − log p(mevcut) ise kabul edilir (u ~ U(0,1)). Bu kural, simetrik bir öneri dağılımı için sonsal dağılıma yakınsayan bir zincir üretir.

Aşağıdaki kod, aynı doğrusal regresyon sonsalını rasgele yürüyüş MH ile örnekler ve kapalı formla karşılaştırır. Bu, yöntemin doğru çalıştığını kanıtlamanın en güvenli yoludur: bilinen cevabı geri bulmak.

```python
def mh(Phi, y, alpha, beta, n=20000, adim=0.12, seed=1):
    rng = np.random.default_rng(seed)

    def log_post(w):
        r = y - Phi @ w
        return -0.5 * beta * r @ r - 0.5 * alpha * w @ w

    w = np.zeros(2)
    lp = log_post(w)
    zincir, kabul = np.zeros((n, 2)), 0
    for t in range(n):
        aday = w + rng.normal(0, adim, 2)
        lp_a = log_post(aday)
        if np.log(rng.random()) < lp_a - lp:
            w, lp = aday, lp_a
            kabul += 1
        zincir[t] = w
    return zincir[2000:], kabul / n


```

```python
def mh_dogrulama():
    alpha, beta = 2.0, 1.0 / 0.3**2
    rng = np.random.default_rng(62)
    x = rng.uniform(-1, 1, 50)
    y = 0.5 + 1.2 * x + rng.normal(0, 0.3, 50)
    Phi = ozellik(x)
    m_N, S_N = bayes_lin(Phi, y, alpha, beta)
    zincir, kabul = mh(Phi, y, alpha, beta)
    print(
        "\n[MH] kabul orani = %.3f, ornek sayisi = %d"
        % (kabul, len(zincir))
    )
    print(
        "  MH ort       :",
        np.round(zincir.mean(axis=0), 4),
        " kapali form:",
        np.round(m_N, 4),
    )
    print("  MH kovaryans :", np.round(np.cov(zincir.T), 5).tolist())
    print("  kapali S_N   :", np.round(S_N, 5).tolist())


```

```python
if __name__ == "__main__":
    print("== (1) Tumleyen filtre ve Kalman ==")
    tumleyen_ve_kalman()
    cok_sensor()
    print("\n== (3) Bayesci dogrusal regresyon ==")
    bayes_bant()
    ridge_esdegeri()
    print("\n== (4) MCMC dogrulama ==")
    mh_dogrulama()
```

```term
$ python b62_06_fuzyon_bayes.py
== (1) Tumleyen filtre ve Kalman ==
[Fuzyon] Kalman K (son adim) = 0.02469, K_ss = 0.02469
[Fuzyon] tumleyen alpha = 1 - K_ss = 0.97531
[Fuzyon] RMS  ham GPS  = 2.071 m
[Fuzyon] RMS  Kalman   = 0.887 m
[Fuzyon] RMS  tumleyen = 0.906 m
[Fuzyon] tumleyen-Kalman, 400. adimdan sonra fark: 4.98e-05

[Cok sensor] sirali ve yigin farki (x): 1.11e-16, (P): 5.55e-17

== (3) Bayesci dogrusal regresyon ==
N= 2  m_N=(0.599, 0.395)  tahmin belirsizligi x=0,9: 0.504
N=10  m_N=(0.600, 1.054)  tahmin belirsizligi x=0,9: 0.337
N=50  m_N=(0.497, 1.169)  tahmin belirsizligi x=0,9: 0.310

[MAP=Ridge] lambda = alpha/beta = 0.18000
  sonsal ortalama m_N     : [0.490076 1.205965]
  Ridge kapali form       : [0.490076 1.205965]
  sklearn Ridge           : [0.490076 1.205965]

== (4) MCMC dogrulama ==

[MH] kabul orani = 0.264, ornek sayisi = 18000
  MH ort       : [0.4901 1.2034]  kapali form: [0.4901 1.206 ]
  MH kovaryans : [[0.00176, -0.0003], [-0.0003, 0.00533]]
  kapali S_N   : [[0.00181, -0.00032], [-0.00032, 0.00561]]
```

MH zinciri 20.000 adımda çalıştı, ilk 2.000 adım yanma (burn-in) olarak atıldı; kabul oranı 0,264'tür. Örnek ortalaması (0,4901; 1,2034) kapalı formdaki (0,4901; 1,2060) değerine yakındır. Kovaryans matrisi de yaklaşık olarak S_N'ye uyar; fark birkaç yüzde mertebesindedir ve bunun nedeni MCMC örneklerinin birbirine bağımlı olmasıdır (otokorelasyon). Daha büyük bir örnek ya da bir hedef etkin örnek sayısı, bu farkı küçültür.

Gauss süreçleri (Bölüm 60'daki çekirdek fikrinin Bayesçi karşılığı) bu fikri bir adım öteye taşır: fonksiyonun kendisi üzerine bir önsel tanımlanır ve tahmin, her noktada bir belirsizlik bandı verir. Bu bölümde ayrıntısına girmiyoruz; ama Şekil 62.10'daki bandın bir Gauss süreci için de aynı mantıkla hesaplandığını bilmek yeterlidir.

## 62.11 Belirsizlik tahmini ve güvenlik: neden bantlara bakarsın?

Bu bölümdeki her yöntem, bir cevabın yanında bir belirsizlik de üretir: Naive Bayes'in olasılığı, HMM'in sonsal durum dağılımı, Kalman'ın P'si, parçacık filtresinin ağırlıkları, Bayesçi regresyonun bandı. Bu belirsizlikler yalnızca akademik bir süs değildir; bir kararın ne kadar güvenilir olduğunu söyler. Bir İHA'nın hedef takibinde "konum şudur" demekle "konum şu bölgededir (%95 güvenle)" demek arasında fark, bir angajman kararında hayati olabilir.

Ama belirsizlik yalnızca doğruysa işe yarar. Bölüm 62.2'de gördüğün gibi, bağımsızlık varsayımı kırıldığında NB'nin güveni şişebilir; Bölüm 62.6'da gördüğün gibi Q yanlış seçilirse Kalman kendine fazla güvenir. Belirsizliğin kalibre edilmiş olup olmadığını (NEES, NIS, ECE gibi ölçümlerle) sürekli denetlemek, güvenlik-kritik sistemlerde bir zorunluluktur. Bölüm 78'de bu fikri adversarial dayanıklılık, açıklanabilirlik ve doğrulama bağlamında derinleştireceğiz; savunma sanayiinde bir sistemin "bildiğini" ve "bilmediğini" ayırt edebilmesi, sertifikasyonun temel gereklerinden biridir.

## Çözümlü Örnekler

Bu bölümde dört çözümlü örnek var ve zorluk sırası ★, ★★, ★★ ve ★★★'tür. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntüyü bul, iyileştir, doğrula. Doğrulama adımında her örnek için elle iz sürme tablosu vardır. Her örneğin sonunda, hiçbir yapay zekâ aracı kullanmadan çözebilmen için bir varyasyon sorusu bulunur. Sayılar, bu bölümdeki programların çıktılarıyla ve kendi elle hesaplarınla birebir denetlenmiştir.

### Örnek 1 (★): Küçük bir sözlükle naive Bayes ve Laplace düzeltmesi

Dört kısa mesaj eğitim verisi olsun: spam (1) "bedava kredi" ve "bedava tıkla"; normal (0) "toplantı yarın" ve "rapor yarın". Sözlük altı kelimedir: bedava, kredi, rapor, toplantı, tıkla, yarın. Yeni mesaj "kredi yarın" için multinomial NB ile sınıfı bul. Laplace düzeltmesi α = 1 kullan ve α = 0 ile farkı göster.

**Adım 1 — Anla.** İstenen, her sınıf için log p(y) + Σ_w x_w log θ_yw değerini hesaplayıp büyük olanı seçmek. Test mesajındaki kelimeler "kredi" ve "yarın"dır; her biri bir kez geçer.

**Adım 2 — Örnekle.** "kredi" yalnızca spam mesajlarda geçer, "yarın" ise yalnızca normal mesajlarda. Yani iki kelime farklı sınıfları işaret ediyor; hangisinin baskın olduğu sayımlara bağlı.

**Adım 3 — Kaba çöz.** Önseller: P(spam) = P(normal) = 2/4 = 0,5. Spam belgelerindeki toplam kelime sayısı 4, normal belgelerdeki de 4'tür. Sözlük boyutu V = 6. Laplace ile θ_yw = (sayım + 1) / (4 + 6) = (sayım + 1) / 10.

**Adım 4 — Örüntü.** Spam sınıfında "kredi" bir kez geçer, θ = (1 + 1)/10 = 0,2; "yarın" hiç geçmez, θ = 1/10 = 0,1. Normal sınıfta "kredi" hiç geçmez, θ = 1/10 = 0,1; "yarın" iki kez geçer, θ = 3/10 = 0,3. Dolayısıyla spam skoru 0,5 · 0,2 · 0,1 = 0,010 ve normal skoru 0,5 · 0,1 · 0,3 = 0,015.

**Adım 5 — İyileştir.** Laplace olmadan (α = 0) normal sınıfta "kredi" için θ = 0 olur ve normal skor sıfıra düşer. Bu durumda mesaj, yalnızca tek bir kelimenin sıfır olasılığı yüzünden kesin olarak spam'e atanır ya da log-uzayda −∞ olur. α = 1 ile bu sorun kalmaz ve "yarın"ın normal sınıfa olan güçlü kanıtı sonucu belirler. Ayrıca çarpım yerine log toplamı kullanılmalıdır; bu örnekte iki çarpan olduğu için sorun yok, ama mesaj uzadıkça alt taşma riski artar.

**Adım 6 — Doğrula.** İz tablosu:

| Sınıf | P(y) | θ(kredi) | θ(yarın) | Çarpım | Log-skor |
|---|---|---|---|---|---|
| spam | 0,5 | 0,2 | 0,1 | 0,010 | −4,605 |
| normal | 0,5 | 0,1 | 0,3 | 0,015 | −4,200 |

Normal sınıf daha büyük skora sahip, dolayısıyla tahmin "normal". Bu, Python'daki `MultiNB` sınıfının çıktısıyla da uyuşur (ortak olasılıklar 0,015 ve 0,010). Önemli bir not: "kredi" spam'de geçtiği halde mesaj normal çıkıyor, çünkü "yarın" kelimesinin normal sınıftaki kanıtı daha güçlü. Naive Bayes kelimeleri birbirinden bağımsız saydığı için bu iki kanıtı topluca tartar.

**Bunu AI'sız yazabilir misin?** Aynı eğitim verisi üzerinde α = 2 ile θ değerlerini yeniden hesapla. "kredi yarın" mesajının sınıfı değişir mi? Sonra yeni mesajı "bedava yarın" yap ve iki α değeri için de sınıfı hesapla. Hangi durumda Laplace'ın seçimi sonucu değiştirir?

### Örnek 2 (★★): Üç düğümlü ağda açıklama gücünün sayısal hesabı

Bir Bayes ağında F (sensör arızası) ve H (gerçek hedef) bağımsız nedenler, A (alarm) ise ikisinin ortak sonucu olsun. P(F = 1) = 0,1, P(H = 1) = 0,2. Koşullu tablo: P(A = 1 | F, H): (0,0) → 0,05; (1,0) → 0,70; (0,1) → 0,80; (1,1) → 0,90. Alarm verildiğinde (A = 1) P(F = 1 | A = 1) ve P(F = 1 | A = 1, H = 1) değerlerini hesapla. Sonuçtaki düşüşü açıkla.

**Adım 1 — Anla.** İki sorgu var: P(F = 1 | A = 1) ve P(F = 1 | A = 1, H = 1). Her ikisi de A = 1 koşulu altında ortak olasılıkların oranıdır.

**Adım 2 — Örnekle.** Alarm, arıza ya da hedef tarafından üretilebilir. Hedef varsa (H = 1) alarm büyük olasılıkla hedefe bağlanır; arıza payı küçülmelidir. Bu sezgiyi sayılarla doğrulayacağız.

**Adım 3 — Kaba çöz.** A = 1 için dört terimin her birini yaz: P(F, H) · P(A = 1 | F, H). P(F = 1) = 0,1 ve P(F = 0) = 0,9; P(H = 1) = 0,2 ve P(H = 0) = 0,8.

**Adım 4 — Örüntü.** Dört terim: (F=0, H=0): 0,9 · 0,8 · 0,05; (F=1, H=0): 0,1 · 0,8 · 0,70; (F=0, H=1): 0,9 · 0,2 · 0,80; (F=1, H=1): 0,1 · 0,2 · 0,90. Bu, aşağıdaki iz tablosunda gösterilmiştir. Toplam P(A = 1) = 0,254. Dolayısıyla P(F = 1 | A = 1) = (0,056 + 0,018) / 0,254 = 0,2913. Koşullu sorgu için yalnızca H = 1 satırlarına bakarız: P(F = 1 | A = 1, H = 1) = 0,018 / (0,144 + 0,018) = 0,1111.

**Adım 5 — İyileştir.** Bu hesabı tekrar tekrar yapmak yerine, iki koşullu sorguyu ortak tablonun satırlarından okumak yeterlidir. Açıklama gücü de burada görünür: H = 1 bilgisi, P(F = 1 | A = 1) = 0,2913'ten 0,1111'e düşürür. Ek olarak H = 0 koşulunda P(F = 1 | A = 1, H = 0) = 0,056 / 0,092 = 0,6087 çıkar; arıza, alarmın tek açıklaması olduğunda çok daha şüphelidir.

**Adım 6 — Doğrula.** İz tablosu:

| F | H | P(F)P(H) | P(A=1 \| F,H) | Ortak (A=1) |
|---|---|---|---|---|
| 0 | 0 | 0,9 · 0,8 = 0,72 | 0,05 | 0,036 |
| 1 | 0 | 0,1 · 0,8 = 0,08 | 0,70 | 0,056 |
| 0 | 1 | 0,9 · 0,2 = 0,18 | 0,80 | 0,144 |
| 1 | 1 | 0,1 · 0,2 = 0,02 | 0,90 | 0,018 |
| Toplam | | | | 0,254 |

Toplam 0,254'tür ve P(F = 1 | A = 1) = 0,074 / 0,254 = 0,2913; P(F = 1 | A = 1, H = 1) = 0,018 / 0,162 = 0,1111. Bu değerler, sayımla çıkarım ile aynıdır; Bölüm 62.3'teki koddaki yöntemi bu sayılarla da çalıştırabilirsin.

**Bunu AI'sız yazabilir misin?** P(H = 1) = 0,2 değerini 0,5 yap ve P(F = 1 | A = 1) ile P(F = 1 | A = 1, H = 1) değerlerini yeniden hesapla. H'nin önseli arttığında açıklama gücünün etkisi büyür mü, küçülür mü? Nedenini ortak tablo üzerinden açıkla.

### Örnek 3 (★★): Viterbi tablosunun doldurulması ve geri izleme

İki durumlu bir HMM'de (durumlar A ve B) π = (0,6; 0,4), geçiş A = [[0,7; 0,3]; [0,4; 0,6]] ve emisyon B = [[0,9; 0,1]; [0,2; 0,8]] olsun. Gözlem dizisi (1, 0, 0) olsun (0 = "düşüyor/sabit", 1 = "yükseliyor" gibi iki sembol). En olası durum dizisini Viterbi ile bul; δ ve ψ tablolarını doldur ve geri izleme yap.

**Adım 1 — Anla.** İstenen, bir gözlem dizisi için maksimum olasılıklı gizli durum dizisidir. Tablo üç zaman adımı ve iki durum içerir; her hücrede log-olasılık tutacağız.

**Adım 2 — Örnekle.** İlk gözlem 1'dir. B durumu 1 üretme olasılığı 0,8, A durumu ise 0,1'dir. Ama B'nin başlangıç olasılığı 0,4'tür; yani B'nin başlaması pahalıdır. Sonraki iki gözlem 0'dır: A bu sembolü üretme olasılığı 0,9'dur. Bu nedenle en iyi yolun ilk adımda B, sonra A'ya geçmesi beklenir.

**Adım 3 — Kaba çöz.** Her hücre için iki aday vardır: önceki durumdan gelen en iyi toplam artı geçiş, artı emisyon. Log'u kullanarak toplam hesaplarız.

**Adım 4 — Örüntü.** Birinci adım: δ_1(A) = log(0,6 · 0,1) = log 0,06 = −2,8134; δ_1(B) = log(0,4 · 0,8) = log 0,32 = −1,1394. İkinci adım, gözlem 0: δ_2(A) = max(δ_1(A) + log 0,7, δ_1(B) + log 0,4) + log 0,9 = max(−3,1701; −2,0557) − 0,1054 = −2,1611 (ψ_2(A) = B). δ_2(B) = max(δ_1(A) + log 0,3, δ_1(B) + log 0,6) + log 0,2 = max(−4,0174; −1,6502) − 1,6094 = −3,2597 (ψ_2(B) = B). Üçüncü adım, gözlem 0: δ_3(A) = max(−2,1611 − 0,3567; −3,2597 − 0,9163) − 0,1054 = −2,6231 (ψ_3(A) = A). δ_3(B) = max(−2,1611 − 1,2040; −3,2597 − 0,5108) − 1,6094 = −4,9745 (ψ_3(B) = A).

**Adım 5 — İyileştir.** Geri izleme, son adımdan başlar: en büyük δ_3 A'dadır, yani z_3 = A. ψ_3(A) = A olduğu için z_2 = A. ψ_2(A) = B olduğu için z_1 = B. Yani en iyi yol B, A, A'dır. İyileştirme, tabloyu yalnızca bir sütun tutarak yapmaktır: δ'ler bir sonraki adımı hesaplamak için yeterlidir; ψ tüm sütunları saklar.

**Adım 6 — Doğrula.** İz tablosu:

| t | gözlem | δ_t(A) | δ_t(B) | ψ_t(A) | ψ_t(B) |
|---|---|---|---|---|---|
| 1 | 1 | −2,8134 | −1,1394 | — | — |
| 2 | 0 | −2,1611 | −3,2597 | B | B |
| 3 | 0 | −2,6231 | −4,9745 | A | A |

Geri izleme: z_3 = A, z_2 = ψ_3(A) = A, z_1 = ψ_2(A) = B. Yol (B, A, A). Log-olasılık −2,6231'dir; olasılık e^(−2,6231) = 0,0726. Programdaki `viterbi` fonksiyonu aynı yolu ve aynı tabloyu üretir; kaba kuvvetle yani üç adımda sekiz yolun hepsini deneyerek de (B, A, A) yolunun en büyük olduğunu doğrulayabilirsin.

**Bunu AI'sız yazabilir misin?** Aynı π ve A ile gözlem dizisini (0, 1, 1) yap. δ tablosunu doldur ve geri izle. ψ tablosunda bir önceki durumun değiştiği bir hücre var mı? Bu, Viterbi'nin "geçiş pahalı" durumunu nasıl çözdüğünü gösterir.

### Örnek 4 (★★★): 1B Kalman filtresinin üç adımlık izi

Rastgele yürüyüş modeli x_k = x_{k−1} + w (F = 1, Q = 0,1) ve ölçüm z_k = x_k + v (H = 1, R = 1) olsun. Başlangıç x̂_0 = 0 ve P_0 = 10. Ölçümler sırasıyla z_1 = 2,0, z_2 = 1,5 ve z_3 = 3,0. Her adımda tahmin (x⁻, P⁻), kazanç K, inovasyon ν, güncelleme (x̂, P) değerlerini hesapla ve izi tablola.

**Adım 1 — Anla.** Her adımda iki iş var: tahmin (dinamik model) ve güncelleme (ölçüm). Kalman kazancı K = P⁻ / (P⁻ + R) gibi basit bir ilişkidir çünkü H = 1.

**Adım 2 — Örnekle.** Ölçümler 2,0, 1,5 ve 3,0 arasında dalgalanıyor. Modelimiz sabit bir değer tahmin ettiği için filtre bu dalgalanmaları yumuşatacak, ama her yeni ölçümde biraz kayacak.

**Adım 3 — Kaba çöz.** Adım 1 için: x⁻ = 0, P⁻ = 10 + 0,1 = 10,1. K = 10,1 / 11,1. ν = 2,0 − 0 = 2,0.

**Adım 4 — Örüntü.** K_1 = 10,1 / 11,1 = 0,9099. x̂_1 = 0 + 0,9099 · 2,0 = 1,8198. P_1 = (1 − 0,9099) · 10,1 = 0,9099. Adım 2 için: x⁻ = 1,8198, P⁻ = 0,9099 + 0,1 = 1,0099, K_2 = 1,0099 / 2,0099 = 0,5025, ν = 1,5 − 1,8198 = −0,3198, x̂_2 = 1,8198 − 0,5025 · 0,3198 = 1,6591, P_2 = 0,4975 · 1,0099 = 0,5025. Adım 3 için: x⁻ = 1,6591, P⁻ = 0,6025, K_3 = 0,6025 / 1,6025 = 0,3760, ν = 3,0 − 1,6591 = 1,3409, x̂_3 = 1,6591 + 0,3760 · 1,3409 = 2,1632, P_3 = 0,6240 · 0,6025 = 0,3760.

**Adım 5 — İyileştir.** Kazancın azaldığını görüyorsun: K = 0,91 → 0,50 → 0,38. Bu, filtrenin ölçümlere giderek daha az güvendiği anlamına gelir; belirsizlik (P) azaldıkça model daha çok güven kazanır. Ayrıca P_k değerleri 1/P = 1/P⁻ + 1/R eşitliğini sağlar (bu, iki Gauss'un çarpımındaki kesinlik toplamıdır). Kodda bu eşitlik her adımda `assert` ile denetlenir.

**Adım 6 — Doğrula.** İz tablosu:

| k | x⁻ | P⁻ | K | ν | x̂ | P |
|---|---|---|---|---|---|---|
| 1 | 0,0000 | 10,1000 | 0,9099 | 2,0000 | 1,8198 | 0,9099 |
| 2 | 1,8198 | 1,0099 | 0,5025 | −0,3198 | 1,6591 | 0,5025 |
| 3 | 1,6591 | 0,6025 | 0,3760 | 1,3409 | 2,1632 | 0,3760 |

Kod çıktısı tabloyla birebir aynıdır. Kontrol: adım 1 için 1/0,9099 = 1,0990 ve 1/10,1 + 1/1 = 0,0990 + 1 = 1,0990 eşittir.

**Bunu AI'sız yazabilir misin?** R = 0,25 ile aynı üç adımı tekrarla. K_1 neden daha büyük çıkar? Sonra Q = 0 yap (süreç gürültüsü yok): bu durumda P_k neye yakınsar ve filtre bir ortalama gibi mi davranır?

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı kullanma. Kodu, testleri ve ölçümleri kendin yaz. Amaç, bu bölümdeki yöntemleri boş bir IDE'de yeniden kurabilmektir. Bir hata bulursan önce kendin çöz; hatayı bulma süreci bu bölümün en değerli kısmıdır.
:::

### Proje 1 (★★): Uçuş modu HMM'i: öğrenme, çözme ve doğrulama

**Amaç.** Bu bölümdeki İHA uçuş modu HMM'ini sıfırdan kendin kur: ileri algoritma, Viterbi, Baum–Welch. Gerçek bir uçuş kaydı yerine kendi sentetik verini üret ve modelin parametrelerini geri kazanıp kazanmadığını ölç.

**Yapılacak / Beklenen davranış.** Üç durumlu (kalkış, seyir, iniş) bir HMM için geçiş ve emisyon matrislerini sabit tohumla bir veri üreticiyle kullan; 3000 adımlık bir eğitim ve 600 adımlık bir test dizisi üret. Baum–Welch ile parametreleri eğitim verisinden öğren. Öğrenilen modelle test dizisinde Viterbi çözümü yap ve gerçek durumlarla karşılaştır. Ayrıca her iterasyonda log-olabilirliğin arttığını göster.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** İleri ve geri algoritmalarında taşmayı normalizasyonla önle; her adımın ölçek katsayısını sakla. Baum–Welch'te γ ve ξ'yi önce T × K ve T × K × K boyutlu dizilerde tut. Başlangıç değerlerini gerçek parametrelere yakın seçip bir kez de uzak seçerek yerel optimumu karşılaştır. Kalkış durumunun neden zor öğrenildiğini düşün: bu durum kısa sürüyor mu?

**Başarı kriterleri.** (1) İleri algoritmanın log-olasılığı, T = 8 için kaba kuvvet toplamıyla 10^-9 hassasiyetinde eşleşiyor. (2) Viterbi yolu, T = 8 için kaba kuvvet en iyi yolla aynı. (3) Baum–Welch log-olabilirliği her iterasyonda monoton artıyor. (4) Öğrenilen parametrelerle test doğruluğunu ve gerçek parametrelerle doğruluğunu raporladın; farkı açıkladın. (5) Sabit tohumla iki kez çalıştırıldığında aynı sayılar çıkıyor.

### Proje 2 (★★★): Hedef takibi: sabit hız, EKF ve parçacık filtresi

**Amaç.** Bir İHA'nın radar ölçümlerinden konum ve hız kestirimi yapan bir takip sistemi kur. Sabit hız modeliyle Kalman filtresi, radar ölçümü için genişletilmiş Kalman (EKF) ve bir parçacık filtresini aynı senaryoda karşılaştır. Ölçüm kayıpları ve Q/R ayarının etkisini ölç. Savunma bağlamında, bu tür bir takip sisteminin hangi koşullarda güvenilir olduğunu raporla.

**Yapılacak / Beklenen davranış.** Hedef sabit hızla bir noktadan geçsin; süreç gürültüsü DWNA modeliyle üretilsin. Radar menzil ve yön açısı ölçsün, her ikisi de gürültülü olsun (açı farkını [−π, π) aralığına sarmalamayı unutma). Sabit hız modeli üzerinde EKF ve parçacık filtresi aynı radar verisiyle çalışsın; doğrusal Kalman filtresi radar ölçümü için uygun olmadığından karşılaştırmaya dahil edilmez. 20 adımlık bir ölçüm kaybını (yalnızca tahmin) ekle ve belirsizlik ile hatanın değişimini izle. Q ve R ölçeklerini bir ızgarada tara ve ortalama RMS'i tablola. Son olarak NEES ve NIS ile tutarlılığı denetle.

**Önerilen yaklaşım (ipucu).** EKF'de Jacobian'ı hata yapmadan yazmak için önce numerik bir türevle karşılaştır. Parçacık filtresinde ağırlıkları log-uzayda hesapla ve sistematik yeniden örneklemeyi kendin yaz. Parçacık sayısı arttıkça hatanın nasıl davrandığını ölç ve ESS'yi her adımda kaydet. Bir koşuda EKF ile PF'nin neden farklı sonuç verdiğini bulmak için hedefi radara daha yakın geçir.

**Başarı kriterleri.** (1) Her üç filtrenin RMS'i 30 koşu üzerinden ortalanmış, standart sapmasıyla raporlanmış. (2) Kayıp ölçüm aralığında belirsizliğin büyümesi ve ölçüm dönünce düşmesi gösterilmiş. (3) NEES ortalaması 4'e (durum boyutu) ve NIS ortalaması 2'ye (ölçüm boyutu) yakın, yanlış Q ile bu değerlerin bozulduğu gösterilmiş. (4) Parçacık sayısına göre hata ve ESS grafiği var. (5) Hangi filtrenin hangi senaryoda neden daha iyi olduğu, verilerle desteklenmiş bir paragrafla yazılmış; sentetik verinin gerçek bir uçuşu temsil etmediği açıkça belirtilmiş.

### Ek Alıştırmalar

Aşağıdaki problemler kademelidir. ★ olanlar kavramı yoklar, ★★ olanlar bir türetme ya da küçük bir hesap ister, ★★★ olanlar birden çok konuyu birleştirir. Mülakat etiketli olanlar klasik sorulardır.

1. (★) İki sınıf ve tek özellikli bir veri setinde Gauss naive Bayes için sınıf ortalamalarını ve varyanslarını elle hesapla. Sonra bir test noktasında log-olasılık farkının işaretini belirle.
2. (★) Multinomial NB'de α = 0 olduğunda bir kelimenin tek sınıfta geçmesi neden tüm belgeyi tek sınıfa bağlar? Bu sorunu bir cümleyle açıkla. (Mülakat)
3. (★) Üç ikili değişkenli bir zincir A → B → C düşün. B gözlemlenmişse A ile C'nin bağımsız olduğunu bir cümleyle gerekçelendir.
4. (★★) Ortak neden yapısında (A ← B → C) A ve C'nin önsel olarak bağımlı olduğunu, ama B gözlendiğinde bağımsız olduğunu göster. Hangi koşullu olasılıkları eşitlemen gerektiğini yaz.
5. (★★) Bir Markov zincirinin geçiş matrisi P = [[0,9; 0,1]; [0,2; 0,8]] için durağan dağılımı π = πP denkleminden bul. Sonucu özdeğer ayrışımıyla da doğrula.
6. (★★) Viterbi algoritması T adımlı ve K durumlu bir HMM için neden O(T·K²) işlem yapar? Ayrıca ileri algoritmanın neden aynı karmaşıklığa sahip olduğunu açıkla. (Mülakat)
7. (★★) Kalman kazancı K = P⁻ / (P⁻ + R) için P⁻ → ∞ ve P⁻ → 0 limitlerini incele. Filtre hangi durumda tamamen ölçüme, hangi durumda tamamen modele güvenir?
8. (★★) Bir 1B Kalman filtresinde ölçüm yokken P'nin her adımda Q kadar arttığını göster. Üç adımdan sonra P'nin değerini P_0 ve Q cinsinden yaz. (Mülakat)
9. (★★) Radar menzil ölçümünün Jacobian'ını (∂r/∂px ve ∂r/∂py) türetmeden önce r = √(px² + py²) ifadesinin türevinin zincir kuralıyla nasıl elde edildiğini açıkla. Bölüm 55'teki Jacobian kavramını kullan.
10. (★★★) Parçacık filtresinde N parçacık ve her adımda ESS'nin 1 ile N arasında olduğunu düşün. ESS'nin N/2 eşiğinin altına düşmesi durumunda yeniden örnekleme yapan bir politika yaz. Bu politikanın hangi durumda gereksiz yeniden örnekleme yapacağını açıkla. (Mülakat)
11. (★★★) Tümleyen filtrenin α = 1 − K_ss olarak yorumlanmasının, ölçüm gürültüsü R ile süreç gürültüsü Q'nun oranına nasıl bağlı olduğunu türet. Q/R oranı büyürse α ne olur? (Mülakat)
12. (★★★) Bayesçi doğrusal regresyonda sonsal kovaryansın S_N = (αI + βΦᵀΦ)⁻¹ olduğunu, veri arttıkça belirsizliğin neden azaldığını bir Φ matrisinin özdeğerleri üzerinden açıkla. Sonuçta tahmin belirsizliği neden tamamen sıfıra inmez? (Mülakat)

## Kod Okuma Egzersizi

Bu bölümde iki gerçek kaynak kesiti okuyacağız. İlki scikit-learn 1.8.0 kurulumundaki `sklearn/naive_bayes.py` dosyasından, multinomial NB'nin Laplace düzeltmesini ve log-olasılık hesabını yapan iki yöntemdir. Kaynak dosyanın yolu: `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\sklearn\naive_bayes.py`. Kesit satır 925–937 arasıdır. İki yerde biçim değişikliği yaptık ve bunu belirtiyoruz: docstring satırı 75 karakter olduğu için iki satıra bölündü; `return` satırı 83 karakterdi, parantez içine alınarak bölündü. İfadeler değişmemiştir.

```python
    def _update_feature_log_prob(self, alpha):
        """Apply smoothing to raw counts and recompute log
        probabilities"""
        smoothed_fc = self.feature_count_ + alpha
        smoothed_cc = smoothed_fc.sum(axis=1)

        self.feature_log_prob_ = np.log(smoothed_fc) - np.log(
            smoothed_cc.reshape(-1, 1)
        )

    def _joint_log_likelihood(self, X):
        """Calculate the posterior log probability of the samples X"""
        return (
            safe_sparse_dot(X, self.feature_log_prob_.T)
            + self.class_log_prior_
        )
```

Bu kesitte `smoothed_fc = count + alpha` satırı, Laplace düzeltmesinin kodda birebir karşılığıdır; bizim `MultiNB.fit` içindeki `duz = sayim + self.alpha` satırı aynı işi yapar. İkinci satır `log(smoothed_fc) − log(toplam)` ise θ_yw = (sayım + α) / (toplam + αV) formülünün log-uzay biçimidir; sklearn `reshape(-1, 1)` ile toplamı her sınıf satırına yayar. `_joint_log_likelihood` ise X · log θᵀ + log P(y) hesabını yapar; bizim `joint_log` yöntemi tam olarak aynı matris çarpımıdır. Yani iki uygulama aynı matematiği izler; farkları yalnızca sparse matris desteği ve doğrulama katmanlarıdır.

İkinci kesit, FilterPy 1.4.5 kurulumundaki `filterpy/kalman/kalman_filter.py` dosyasından, `KalmanFilter.update` yönteminin kod kısmıdır. Yol: `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\filterpy\kalman\kalman_filter.py`. Docstring ve `z is None` dalı atlanmıştır. Tek değişiklik, 79 karakterlik `self.P = ...` satırının parantezle iki satıra bölünmesidir; ifade aynıdır.

```python
        # set to None to force recompute
        self._log_likelihood = None
        self._likelihood = None
        self._mahalanobis = None

        if z is None:
            self.z = np.array([[None]*self.dim_z]).T
            self.x_post = self.x.copy()
            self.P_post = self.P.copy()
            self.y = zeros((self.dim_z, 1))
            return

        z = reshape_z(z, self.dim_z, self.x.ndim)

        if R is None:
            R = self.R
        elif isscalar(R):
            R = eye(self.dim_z) * R

        if H is None:
            H = self.H

        # y = z - Hx
        # error (residual) between measurement and prediction
        self.y = z - dot(H, self.x)

        # common subexpression for speed
        PHT = dot(self.P, H.T)
```

```python

        # S = HPH' + R
        # project system uncertainty into measurement space
        self.S = dot(H, PHT) + R
        self.SI = self.inv(self.S)
        # K = PH'inv(S)
        # map system uncertainty into kalman gain
        self.K = dot(PHT, self.SI)

        # x = x + Ky
        # predict new x with residual scaled by the kalman gain
        self.x = self.x + dot(self.K, self.y)

        # P = (I-KH)P(I-KH)' + KRK'
        # This is more numerically stable
        # and works for non-optimal K vs the equation
        # P = (I-KH)P usually seen in the literature.

        I_KH = self._I - dot(self.K, H)
        self.P = dot(dot(I_KH, self.P), I_KH.T) + dot(
            dot(self.K, R), self.K.T
        )

        # save measurement and posterior state
        self.z = deepcopy(z)
        self.x_post = self.x.copy()
        self.P_post = self.P.copy()
```

Bu kodu bizim `guncelle` fonksiyonumuzla karşılaştır: `nu = z − Hx` inovasyon, `S = HPHᵀ + R`, `K = PHᵀS⁻¹` kazanç ve `x = x + Kν` güncellemesi bizimkiyle aynıdır. FilterPy, P'yi Joseph biçiminde, yani (I − KH) P (I − KH)ᵀ + K R Kᵀ olarak günceller; biz de aynı formülü kullandık. Yorum satırı bunun "sayısal olarak daha kararlı" olduğunu söyler; bu, P'nin simetrik ve pozitif yarı tanımlı kalmasını sağlamaya yönelik genel bir sayısal tercihtir. Kodda FilterPy ile karşılaştırmada elde edilen 0,00 farkı, iki uygulamanın bu satırlarda birebir aynı işlemleri yaptığını gösterir.

**Sorular — cevaplamadan geçme:**

1. sklearn'ün `_update_feature_log_prob` yönteminde `np.log(smoothed_fc) − np.log(smoothed_cc)` yerine doğrudan `np.log(smoothed_fc / smoothed_cc)` yazılsaydı ne olurdu? Sayısal bir fark doğurabilir mi, hangi koşullarda?
2. `alpha` parametresi sıfır olduğunda sklearn'ün davranışı nedir? Bir sınıfta sıfır sayımlı bir özellik olursa `log(0)` ne üretir ve bunu kod nasıl ele alır?
3. FilterPy'nin `update` yönteminde `self.SI = self.inv(self.S)` kullanılıyor. Bunun yerine `np.linalg.solve` ile K'yi hesaplamak neden tercih edilebilir? Hangi durumda `inv` kötü koşulludur?
4. Joseph biçimi P'yi simetrik tutar. Basit (I − KH)P biçiminde simetri nasıl bozulabilir ve bu uzun bir süreçte neye yol açabilir?
5. FilterPy'nin `update` yöntemi `R` argümanını her çağrıda geçersiz kılabilir. Bu özellik, ölçüm kalitesi (örneğin GPS sinyal gücü) değiştiğinde filtreyi nasıl etkiler?
6. Yorum satırı "works for non-optimal K" diyor. Kazanç Kalman kazancının optimal değerinden farklı olduğunda Joseph biçimi neden hâlâ geçerli bir kovaryans üretir, basit biçim neden üretmeyebilir?

## Bölüm Özeti

- Üretici modeller ortak dağılımı (p(x, y)) öğrenir, ayırt edici modeller yalnızca p(y | x)'i öğrenir. Bayes kuralı ikisini birbirine bağlar.
- Naive Bayes, özellikleri sınıf verildiğinde bağımsız varsayar; Laplace düzeltmesi sıfır olasılık sorununu önler ve log-uzay alt taşmayı engeller.
- Varsayım kırıldığında doğruluk çoğu zaman korunsa bile olasılık kalibrasyonu bozulabilir; bu, ECE ve Brier ile ölçülür.
- Bayes ağları, koşullu olasılık tablolarıyla ortak dağılımı çarpanlara ayırır. Ortak sonuçta açıklama gücü, bir nedeni doğrulamanın diğerinin olasılığını düşürmesidir.
- HMM'de ileri algoritma olasılığı, Viterbi en olası yolu, Baum–Welch (EM) parametreleri öğrenir. Viterbi bir DP'dir; log-uzayda ve geri izlemeyle çalışır.
- Kalman filtresi doğrusal Gauss modelinde posterior'u (x̂, P) özyinelemeli olarak günceller; kazanç ölçüme ve modele güveni dengeler. Q ve R'nin oranı önemlidir.
- EKF, doğrusal olmayan ölçümü Jacobian ile doğrusallaştırır; parçacık filtresi posterior'u ağırlıklı örneklerle temsil eder ve dejenerasyonu ESS ile izlenir.
- Tümleyen filtre sabit kazançlı bir Kalman filtresidir; Bayesçi doğrusal regresyonun sonsal ortalaması Ridge ile aynıdır ve tahmin belirsizliği veriyle azalır, ama gürültü terimi kalır.

**Kısım XIV'ün kapanışı.** Kısım XIV, ham veriden öğrenmenin dört ana fikrini kurdu: ML'e giriş ve değerlendirme (54, 57), matematiksel temel (55, 48–49, 51), veriyle çalışma (56) ve sınıflandırıcı ile topluluk modelleri (58, 59, 60, 61). Bu bölümde bu fikirler olasılıksal bir çerçeveye taşındı: bir modelin yalnızca tahmin değil, belirsizlik de üretmesi gerektiğini gördük. Naive Bayes'ten Kalman'a uzanan yol, aynı Bayes kuralının farklı yapılarda nasıl uygulandığını gösterdi. Kısım XIV'ün son cümlesi şudur: bir model ne kadar iyi tahmin ederse etsin, ne kadar emin olduğunu da kalibre edilmiş biçimde söyleyemiyorsa, güvenlik-kritik bir sistemde tek başına yeterli değildir.

**Sonraki bölümde:** Bölüm 63, Sinir Ağı Sıfırdan başlıyor. Bu bölümde doğrusal ve olasılıksal modellerin sınırlarını gördük; orada doğrusal olmayan katmanlar ve geri yayılım (backpropagation) ile bu sınırları aşan bir MLP'yi NumPy ile sıfırdan kuracağız. Kısım XV — Derin Öğrenme böylece başlıyor.

::: mulakat
1. Naive Bayes'in bağımsızlık varsayımı yanlış olduğu hâlde neden sık sık iyi sınıflandırma yapar? Olasılık çıktısı ile sınıf kararı arasındaki farkı açıklayarak cevapla.
2. Laplace düzeltmesi neden bir Dirichlet önselinin MAP tahminine karşılık gelir? α'nın değerinin küçük ve büyük olması sonucu nasıl etkiler?
3. Açıklama gücü (explaining away) nedir? Bir Bayes ağında ortak sonuç yapısının bu etkiyi nasıl ürettiğini bir örnekle anlat.
4. Viterbi algoritması ile ileri algoritmanın arasındaki fark nedir? Biri neyi toplar, diğeri neyi maksimize eder?
5. Kalman kazancı neden ölçümün kovaryansı R ile önselin kovaryansı P⁻'nin oranına bağlıdır? R → 0 ve P⁻ → 0 durumlarında filtre ne yapar?
6. Parçacık filtresinde ESS'nin düşmesi neden bir sorun? Yeniden örnekleme bu sorunu çözer mi, yoksa yalnızca belirtiyi mi gizler?
7. Bayesçi doğrusal regresyonda tahmin belirsizliğinin gürültü terimi (1/β) ile parametre belirsizliği (φᵀS_Nφ) terimlerini ayırt et. Hangisi veri arttıkça sıfıra gider?
8. Bir Kalman filtresinin NEES ortalaması durum boyutundan belirgin biçimde büyük çıkıyorsa bu neyin belirtisidir ve nasıl düzeltilir?
