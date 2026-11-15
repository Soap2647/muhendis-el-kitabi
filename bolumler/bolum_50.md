%% kisim_no: XII
%% kisim_ad: Matematik
%% bolum_no: 50
%% baslik: Optimizasyon

## Giriş: En iyisini bulmak bir problemdir

Bir İHA'nın görevi bir rota seçmek. Rota uzunsa batarya yetmez, kısaysa hedefe yetişmez. Bir sensör kalibrasyonu yapıyorsun: düzeltme katsayılarını öyle seçmelisin ki ölçüm hatası en az olsun. Bir makine öğrenmesi modelini eğitiyorsun: parametreleri öyle bulmalısın ki eğitim verisinde yapılan hata küçük çıksın. Üçünde de aynı soru var: bir büyüklüğü en iyi yapan değişkenleri nasıl bulacağız? Bu soruya verilen genel cevabın adı **optimizasyon**dur.

Bu bölümün iki amacı var. Birincisi, Bölüm 46'da tek paragrafla tanıttığımız gradyan inişinin arkasındaki matematiği kurmak: türev neden bize "hangi yöne gitmeliyim" sorusunun cevabını verir, öğrenme oranı neden bir uçurumun kenarını belirler, neden bazı yöntemler diğerlerinden on kat hızlıdır. İkincisi, bu araçları mühendislik problemlerinde kullanmak: kısıtlı bir batarya bütçesinde en uygun hız, bir PID denetleyicinin kazanç ayarı, bir sensörün kalibrasyonu.

Optimizasyon, ML'in fiilen her bölümünde karşına çıkar. Bölüm 58'de doğrusal ve lojistik regresyonun kaybını minimize edeceğiz; Bölüm 63 ve 64'te sinir ağlarının geri yayılımı ve Adam gibi eğitim algoritmaları bu bölümdeki yöntemlerin doğrudan uygulamasıdır. Bölüm 57'de hiperparametre aramasını (ızgara, rastgele arama) göreceğiz; o da türevsiz bir optimizasyondur. Bölüm 49'da en büyük olabilirlik tahmini (MLE) de aslında bir optimizasyon problemidir: log-olabilirliği en büyük yapan parametreyi ararsın.

Bölümün yöntemi, Mert'in alışık olduğu şekilde ilerleyecek. Her yöntemi önce bir geometrik sezgiyle anlatıyoruz, sonra türetiyoruz, sonra sıfırdan NumPy ile yazıyoruz, sonra aynı problem üzerinde yörüngesini çiziyoruz ve yakınsamasını sabit tohumlu bir deneyle ölçüyoruz. SciPy'yi yalnızca karşılaştırma için kullanacağız; yöntemin kendisini kütüphaneye bırakmayacağız.

::: not
Bu bölümdeki tüm sayısal sonuçlar, metinde verilen programlarla yeniden üretilebilir. Rastgele sayı kullanan her deneyde tohum (`default_rng(...)`) açıkça verilmiştir. Bir sonucu okuyunca önce onu üreten programı çalıştır; ancak o zaman inan.
:::

## 50.1 Optimizasyon problemi: amaç, değişken, kısıt

Her optimizasyon problemi üç parçadan oluşur. **Değişkenler** (`x`), seçebildiğimiz sayılardır: bir rotanın noktaları, bir modelin ağırlıkları, bir PID'nin üç kazancı. **Amaç fonksiyonu** (`f(x)`), seçimimizin ne kadar iyi olduğunu tek bir sayıyla ölçer: toplam enerji, eğitim hatası, kare hatanın toplamı. **Kısıtlar**, hangi `x` değerlerinin kabul edilebilir olduğunu belirler: batarya en fazla şu kadar enerji verebilir, bir kazanç negatif olamaz, bir ağırlık bir aralıkta kalmalıdır.

Matematiksel olarak şöyle yazarız:

    min f(x)   öyle ki   g_i(x) ≤ 0,   h_j(x) = 0

Bu biçimde yalnızca en küçüğü arıyoruz. En büyüğü aramak istersen, `−f` üzerinde en küçüğü ararsın; iki problem aynıdır. Bu bölümde kısıtsız problemleri `min f(x)` olarak, kısıtlı problemleri ise yukarıdaki biçimde yazacağız.

Bir noktaya dikkat etmek gerekir: optimizasyonda amaç bir **değer** değil, bir **noktadır**. Soru "f'nin en küçük değeri nedir?" değil, "f'yi en küçük yapan `x*` nedir?" sorusudur. Bu ayrım önemlidir, çünkü `x*`'ı bulduğunda değeri `f(x*)` ile hesaplarsın, ama değeri doğrudan bulmak genellikle `x*`'a ulaşmak demektir.

Problemin doğasına göre dört tür çözüm vardır. **Küresel minimum** (global minimum), bütün uzayda `f`'nin en küçük olduğu noktadır. **Yerel minimum** (local minimum), yalnızca yakın bir komşuluğunda en küçük olan noktadır; daha uzakta daha iyi bir nokta olabilir. **Eyer noktası** (saddle point), bazı yönlerde yükselen, bazı yönlerde alçalan noktadır; `f(x, y) = x² − y²` fonksiyonunun orijini bunun tipik örneğidir. Gradyan burada sıfırdır, ama bu bir minimum değildir. Bir optimizasyon algoritması eyer noktasında durursa yanlış bir sonuca varmış olur.

Mühendislikte bu soru her yerde çıkar. Bir İHA'nın uçuş planında amaç enerji tüketimini azaltmak, kısıt ise batarya kapasitesi ve menzildir. Bir hedef takip filtresinde amaç tahmin hatasını azaltmak, kısıt ise ivme sınırıdır. Bu tür problemler için hem kısıtsız hem kısıtlı yöntemleri bilmek gerekir; bu bölümün ikinci yarısı tam olarak bunu kapsar.

## 50.2 Çok değişkenli türevin özü

Tek değişkenli türev `f'(x)`, fonksiyonun bir noktadaki eğimidir. İki ya da daha çok değişkende eğim tek bir sayı değildir: her değişken yönünde ayrı bir eğim vardır. `x_i` dışındaki değişkenleri sabit tutup `x_i`'ye göre türev alırsan buna **kısmi türev** (partial derivative) denir ve `∂f/∂x_i` ile gösterilir.

Bütün kısmi türevleri bir vektörde toplarsan **gradyan** (gradient) elde edersin:

    ∇f(x) = (∂f/∂x_1, ∂f/∂x_2, ..., ∂f/∂x_n)

Gradyanın en önemli özelliği şudur: `x` noktasından küçük bir `d` adımı attığında fonksiyonun değişimi yaklaşık olarak `∇f(x) · d` kadardır. Bu yüzden gradyan, o noktadaki **en dik artış yönünü** gösterir. Tersi yönde, yani `−∇f(x)` yönünde, fonksiyon en hızlı azalır. Gradyan inişinin bütün fikri budur: her adımda `−∇f` yönünde ilerle.

Bir noktada eğimin nasıl değiştiğini de bilmek isteriz. Bunu **Hessian matrisi** verir: `H_ij = ∂²f / ∂x_i ∂x_j`. Hessian, çok değişkenli eğriliğin tamamını kaydeder. Taylor açılımını ikinci dereceye kadar yazarsan şunu görürsün:

    f(x + d) ≈ f(x) + ∇f(x)ᵀ d + ½ dᵀ H(x) d

Buradaki ilk terim sabit, ikinci terim eğimin doğrusal etkisi, üçüncü terim ise eğriliğin etkisidir. Hessian'ın özdeğerleri (eigenvalues) `λ` eğriliğin asal yönlerini ölçer: büyük bir `λ` o yönde dik bir kase, küçük bir `λ` o yönde yatık bir vadi demektir. Bu bilgi, bu bölümün en önemli sezgilerinden biridir: gradyan inişindeki zikzak, Hessian'ın özdeğerleri arasındaki farkın sonucudur.

Kısmi türev, gradyan ve Hessian'ın ayrıntılı hesabı ve zincir kuralı Bölüm 55'te yapılacak. Burada yalnızca iki gerçeğe ihtiyacın var. Birincisi, `∇f(x) = 0` olan noktalar adaylardır (kritik noktalar). İkincisi, bir kritik noktanın türünü Hessian'ın işaretinden anlarsın: bütün özdeğerler pozitifse yerel minimum, bütün özdeğerler negatifse yerel maksimum, karışıksa eyer noktasıdır.

Bu bilgiyi somutlaştırmak için ikinci dereceden bir fonksiyon düşünelim: `f(x) = ½ xᵀ A x`, burada `A` simetrik bir matristir. Gradyan `∇f(x) = A x`, Hessian ise `H = A`'dır. Bu fonksiyon her zaman `x = 0`'da kritik noktaya sahiptir ve `A`'nın bütün özdeğerleri pozitifse bu bir minimumdur. Bölüm 58'deki en küçük kareler probleminde Hessian bu tür bir `A = XᵀX` matrisidir; Bölüm 48'deki lineer cebir bu matrisin neden pozitif yarı-tanımlı olduğunu açıklar.

## 50.3 Sayısal gradyan ve gradyan denetimi

Bazen fonksiyonun türevini elle alamazsın. Bir simülasyonun çıktısı ya da bir derin ağın karmaşık kaybı için analitik gradyan yazmak zordur. Bu durumda türevi **sonlu farklar** (finite differences) ile yaklaşık hesaplarsın. En basit yaklaşım, `i`. değişkene küçük bir `h` ekleyip fark almaktır:

    ∂f/∂x_i ≈ (f(x + h e_i) − f(x)) / h          (ileri fark)
    ∂f/∂x_i ≈ (f(x + h e_i) − f(x − h e_i)) / (2h)  (merkezi fark)

Burada `e_i`, `i`. koordinat yönündeki birim vektördür. Merkezi fark, ileri farktan genellikle daha doğrudur, çünkü hatası `h²` ile, ileri farkın hatası ise `h` ile küçülür.

Burada bir ikilem var ve bu ikilem sayısal optimizasyonun temel derslerinden biridir. `h` büyükse **kesme hatası** (truncation error) baskındır: türev yaklaşımı gerçek eğimden uzaklaşır. Taylor'a göre ileri farkın kesme hatası yaklaşık `(h/2) f''` kadardır. `h` küçükse **yuvarlama hatası** (roundoff error) baskın olur: `f(x + h) − f(x)` gibi iki neredeyse eşit sayının farkını alırken kayan noktada önemli basamakları kaybedersin. Yuvarlama hatası kabaca `ε |f| / h` mertebesindedir; burada `ε` makine epsilonudur.

Bölüm 1'de `0.1 + 0.2` ifadesinin tam olarak `0.3` vermediğini ve `16777216.0f + 1.0f` işleminin sonucu değiştirmediğini görmüştük. Bu bölümdeki sayısal türev, tam olarak o kayan nokta olgusunun optimizasyondaki yansımasıdır: `h` ne kadar küçük olursa, sayılar o kadar yakın olur ve fark o kadar gürültülü hâle gelir. Gerçek dünyada bu bir "iyi `h`" aramasıdır.

Optimal `h`, iki hatanın dengelendiği noktadadır. İleri fark için bu yaklaşık `√ε` mertebesindedir; çift duyarlıkta (float64, `ε ≈ 2,2·10⁻¹⁶`) yaklaşık `10⁻⁸`, tek duyarlıkta (float32, `ε ≈ 1,2·10⁻⁷`) yaklaşık `10⁻⁴`. Merkezi fark için optimal `h` yaklaşık `ε^(1/3)` mertebesindedir ve çift duyarlıkta `10⁻⁶` civarında çıkar. Bunu bir deneyle ölçelim. Test fonksiyonu olarak Rosenbrock'u kullanacağız:

    f(x, y) = (1 − x)² + 100 (y − x²)²

Bu fonksiyonun minimumu `(1, 1)` noktasındadır ve dar, kıvrımlı bir vadisi vardır; optimizasyon yöntemlerinin en sevilen zorluk testidir. Analitik gradyanı `∇f = (−2(1 − x) − 400x(y − x²), 200(y − x²))` olarak biliyoruz; `(−1,2; 1)` noktasında bu `(−215,6; −88)` eder.

Aşağıdaki program, `h`'yi `10⁻¹`'den `10⁻¹⁶`'ya kadar tarar ve her `h` için iki farkın analitik gradyandan maksimum sapmasını ölçer. Hem float64 hem float32 için çalıştırır; böylece kayan nokta duyarlığının optimal `h`'yi nasıl kaydırdığını görürsün. Program ayrıca ölçüm tablosunu `engine/veri/` altına yazar; Şekil 50.1'i o tablodan çizeriz.

Program önce Rosenbrock'un analitik gradyanını alır, sonra ileri ve merkezi farkları tanımlar. Çekirdek iki ayrı fonksiyon yerine tek bir döngüde `e_i` yönlerinde küçük adım atar.

```python
# -*- coding: utf-8 -*-
# Sayisal gradyan: ileri/merkezi fark, h taramasi.
import csv, os
import numpy as np
from b50_core import rosen, rosen_g

x0 = np.array([-1.2, 1.0])
analitik = rosen_g(x0)
print("analitik gradyan:", analitik)

def ileri(f, x, h):
    g = np.zeros_like(x)
    fx = f(x)
    for i in range(x.size):
        e = np.zeros_like(x)
        e[i] = h
        g[i] = (f(x + e) - fx) / h
    return g

def merkezi(f, x, h):
    g = np.zeros_like(x)
    for i in range(x.size):
        e = np.zeros_like(x)
        e[i] = h
        g[i] = (f(x + e) - f(x - e)) / (2 * h)
    return g
```

Ana döngü `h = 10^-k` değerlerini float64 ve float32 için tarar. Her satırda iki farkın maksimum sapması kaydedilir; en iyi `h` değerleri ve seçilmiş satırlar yazdırılır. Son satırlar CSV'ye yazar.

```python
satirlar = []
for dt in (np.float64, np.float32):
    x = x0.astype(dt)
    for k in range(1, 17):
        h = dt(10.0 ** -k)
        gi = ileri(rosen, x, h)
        gm = merkezi(rosen, x, h)
        ei = np.max(np.abs(gi - analitik))
        em = np.max(np.abs(gm - analitik))
        satirlar.append((dt.__name__, float(h), float(ei), float(em)))

for dt_ad in ("float64", "float32"):
    sec = [s for s in satirlar if s[0] == dt_ad]
    en_iyi_i = min(sec, key=lambda s: s[2])
    en_iyi_m = min(sec, key=lambda s: s[3])
    print(dt_ad, "en iyi ileri h = %.0e hata=%.3e"
          % (en_iyi_i[1], en_iyi_i[2]))
    print(dt_ad, "en iyi merk h = %.0e hata=%.3e"
          % (en_iyi_m[1], en_iyi_m[3]))

for k in (2, 4, 6, 8, 10, 12, 14):
    s = [t for t in satirlar
         if t[0] == "float64" and abs(t[1] - 10.0 ** -k) < 1e-30]
    if s:
        print("h=1e-%02d ileri=%.3e merkezi=%.3e"
              % (k, s[0][2], s[0][3]))

CSV = "D:/Mevcut Projeler/Kitap/engine/veri/b50_sonlu_fark.csv"
with open(CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["tip", "h", "hata_ileri", "hata_merkezi"])
    for s in satirlar:
        w.writerow([s[0], "%.1e" % s[1],
                    "%.6e" % s[2], "%.6e" % s[3]])
```

Programın çıktısı şu: float64 için ileri farkın en iyi `h`'si `10⁻⁸`, merkezi farkın ise `10⁻⁶`'dır. float32'de bu değerler sırasıyla `10⁻⁴` ve `10⁻³`'tür. Yukarıdaki iki kolonu aynı `h` değerinde okuyarak kesme ve yuvarlama hatasının nasıl yer değiştirdiğini izleyebilirsin.

```term
$ python b50_deney1.py
analitik gradyan: [-215.6  -88. ]
float64 en iyi ileri h = 1e-08 hata=7.741e-06
float64 en iyi merk h = 1e-06 hata=2.244e-08
float32 en iyi ileri h = 1e-04 hata=1.078e-01
float32 en iyi merk h = 1e-03 hata=1.049e-02
h=1e-02 ileri=6.602e+00 merkezi=4.800e-02
h=1e-04 ileri=6.650e-02 merkezi=4.800e-06
h=1e-06 ileri=6.650e-04 merkezi=2.244e-08
h=1e-08 ileri=7.741e-06 merkezi=9.906e-07
h=1e-10 ileri=1.784e-05 merkezi=1.784e-05
h=1e-12 ileri=2.485e-02 merkezi=1.597e-02
h=1e-14 ileri=3.056e-01 merkezi=3.056e-01
```

Sonuçlar üç şeyi söylüyor. Birincisi, `h = 10⁻²` gibi büyük adımlarda ileri farkın hatası `6,6` kadardır ve bu, `(h/2) f''` tahminine uyar: `f''` bu noktada yaklaşık `1330`'dur, dolayısıyla `665 h` kadar bir kesme hatası beklenir. İkincisi, `h = 10⁻¹⁴` gibi çok küçük değerlerde hata yeniden büyür ve `0,3` seviyesine çıkar: burada yuvarlama hatası baskındır. Üçüncüsü, en iyi merkezi fark, ileri farktan yaklaşık üç yüz kat daha doğrudur (`2,2·10⁻⁸` ile `7,7·10⁻⁶`), ama bu avantaj fonksiyonun üçüncü türevine bağlıdır; her zaman bu kadar büyük değildir.

![Şekil 50.1: Rosenbrock gradyanında sonlu fark hatası. Kesme ve yuvarlama hatası farklı yönlerde eğilir; float32'de optimal h daha büyük, hata daha büyüktür.](gorseller/b50_sonlu_fark.png)

Şekil 50.1'de kesme hatası, log-log ölçekte bir doğru (eğim 1) olarak görünür. Yuvarlama hatası ise `h` küçüldükçe sol yukarı doğru yükselen bir kol oluşturur. Optimal `h`, iki kolun kesiştiği bölgedir. Float32 eğrilerinin neden daha yüksek başladığına dikkat et: yaklaşık 5·10⁸ kat büyüktür, bu yüzden yuvarlama kolu çok daha erken başlar ve optimal `h` çok daha büyük olur.

Pratikte bunun anlamı nettir. Bir gradyan denetimi (gradient check) yazarken analitik gradyanını sayısal gradyanla karşılaştırırsın. Karşılaştırma ölçüsü olarak göreli hata kullanılır:

    göreli hata = ‖g_analitik − g_sayısal‖ / (‖g_analitik‖ + ‖g_sayısal‖)

Çift duyarlıkta merkezi farkla yaklaşık `10⁻⁷` ile `10⁻⁹` arasındaki göreli hatalar iyi sayılır (genel pratik); bu değerden büyük bir hata çoğunlukla analitik gradyanda bir hata olduğunu gösterir. Denetimi hangi `h` ile yaptığını da not et. Bu bölümde tekrar tekrar kullanacağımız bir alışkanlık: yeni bir gradyan yazdığında önce bu denetimi yap.

## 50.4 Konveksite: yerel minimum neden tek olabilir

Optimizasyonun en önemli ayrımı belki de **konveks** ile **konveks olmayan** problemler arasındadır. Konveksite, bir problemin "kolay" mı yoksa "zor" mu olduğunu büyük ölçüde belirler.

Bir küme `C` konvekstir, eğer içindeki herhangi iki nokta arasındaki doğru parçası da `C`'nin içindeyse: her `x, y ∈ C` ve `λ ∈ [0, 1]` için `λx + (1 − λ)y ∈ C`. Disk, kutu, doğrusal eşitsizliklerle tanımlı çokyüzlü konvekstir. Hilal şekli konveks değildir.

Bir fonksiyon `f` konvekstir, eğer grafiği üzerindeki herhangi iki noktayı birleştiren doğru parçası grafiğin üstünde kalıyorsa:

    f(λx + (1 − λ)y) ≤ λ f(x) + (1 − λ) f(y)

Bu eşitsizlik **Jensen eşitsizliğinin** iki noktalı biçimidir. Genel olarak, `f` konveksse ağırlıklı ortalamanın fonksiyonu, fonksiyonların ağırlıklı ortalamasından küçük ya da eşittir. İki kez türevlenebilen bir fonksiyon için eşdeğer koşul, Hessian'ın her yerde pozitif yarı-tanımlı olmasıdır: `H(x) ⪰ 0`, yani bütün özdeğerleri `≥ 0`.

Şekil 50.2'nin (a) paneli bunu gösteriyor. `f(x) = x²` konvekstir: iki nokta arasındaki kiriş (kırmızı çizgi) her zaman eğrinin üstündedir. Bunun neden önemli olduğunu bir cümleyle söyleyebiliriz: konveks bir fonksiyonun yerel minimumu, küresel minimumdur.

Bu ifadeyi kanıtlayalım. Diyelim `x*` yerel bir minimum ama küresel minimum değil; yani `f(y) < f(x*)` olan bir `y` var. `x*`'ın komşuluğunda `f(x*)` en küçük. Şimdi `x*` ile `y` arasındaki doğru parçası üzerindeki noktaları ele al: `z_t = (1 − t) x* + t y`, `t` küçük bir pozitif sayı. Konvekslikten `f(z_t) ≤ (1 − t) f(x*) + t f(y) < f(x*)`. Ama `z_t` küçük `t` için `x*`'a çok yakındır ve `x*` yerel minimum olduğundan `f(z_t) ≥ f(x*)` olmalı. Bu bir çelişkidir. Demek ki konveks bir problemde yerel minimum da küresel minimumdur. Üstelik minimum kümesi konveksdir.

Şekil 50.2'nin (b) paneli konveks olmayan bir fonksiyon gösteriyor: `f(x) = x⁴ − 3x² + x`. İki yerel minimumu var; soldaki daha derin olan küresel minimumdur, sağdaki ise yalnızca yerel. Bir gradyan inişi, nereden başladığına göre bu minimumlardan birine takılabilir. Bu, konveks olmayan problemlerin temel zorluğudur.

![Şekil 50.2: (a) Konveks f(x) = x²; kiriş eğrinin üstünde. (b) Konveks olmayan fonksiyonun iki yerel minimumu. (c) İki boyutta konveks kase: tek minimum. (d) Rastrigin fonksiyonu: çok sayıda yerel minimum.](gorseller/b50_konveks_yuzey.png)

Alt paneller iki boyutta aynı ayrımı gösteriyor. (c)'deki elips biçimli seviye eğrileri konveks bir kasenin işaretidir: her seviye eğrisi içinde kalan küme konvekstir ve yalnızca bir minimum vardır. (d)'deki Rastrigin fonksiyonu ise yüzlerce küçük çukurla doludur. Makine öğrenmesinde kayıp yüzeyleri genellikle (d)'ye benzer. Doğrusal regresyonun kare kaybı ve lojistik regresyonun çapraz entropisi konvekstir; Bölüm 58'de bunu göreceğiz. Ama derin sinir ağlarının kayıp yüzeyi konveks değildir; bu bölümün son alt başlığı bu duruma dönecek.

Konveksite bir sınıflandırma değil, bir kazançtır. Konveks bir problemde bir yerel arama yeterlidir ve algoritmanın hangi noktadan başladığı sonucu değiştirmez. Konveks olmayan bir problemde aynı algoritma iyi bir sonuç verebilir ama bunu garanti edemez. Bu yüzden bir modeli seçerken, kaybın konveks mi olduğunu sormak, bir mühendisin ilk sorularından biri olmalıdır.

## 50.5 Gradyan inişi: adım, öğrenme oranı ve kararlılık

Gradyan inişinin kuralı tek satırdır:

    x_{k+1} = x_k − η ∇f(x_k)

Buradaki `η` **öğrenme oranıdır** (learning rate). Bölüm 46'daki `θ ← θ − η∇L(θ)` formülünün aynısıdır. Sezgisel olarak `η`, her adımda gradyan yönünde ne kadar gideceğini belirler. Büyük `η` cesur ama riskli, küçük `η` güvenli ama yavaş bir adımdır. Bu tek sayı, gradyan inişinin bütün davranışını yönetir ve bu yüzden onu anlamak zorundasın.

Öğrenme oranının etkisini tam anlamak için ikinci dereceden bir fonksiyonda çözümlemeyi yapalım. `f(x) = ½ xᵀ A x` ve `A`, özdeğerleri `λ_min` ile `λ_max` arasında olan simetrik pozitif tanımlı bir matris olsun. Gradyan `A x` olduğundan:

    x_{k+1} = x_k − η A x_k = (I − η A) x_k

`A`'nın özvektörleri üzerinden bakarsak her bileşen bağımsız olarak `(1 − η λ)` ile çarpılır. Bir bileşenin sönmesi için `|1 − ηλ| < 1` olmalıdır; bütün `λ`'lar için bu, `0 < η < 2 / λ_max` demektir. Bu sınıra **kararlılık eşiği** diyoruz. Eşiği aşarsan en büyük özdeğere karşılık gelen bileşen her adımda işaret değiştirip büyür: yöntem ıraksar.

Bir ikinci sonuç da yakınsama hızıdır. En hızlı azalan sabit `η` için `η = 2 / (λ_min + λ_max)` seçilir ve her adımda hata yaklaşık `(κ − 1)/(κ + 1)` oranıyla küçülür. Burada `κ = λ_max / λ_min` **koşul sayısıdır** (condition number). `κ` büyükse fonksiyon kötü koşullu, yani dar ve uzun bir vadidir; yakınsama çok yavaşlar. Koşul sayısının matris olarak anlamı ve SVD ile ilişkisi Bölüm 48'de lineer cebir ile ayrıntılandırılacak.

Bu teoriyi üç öğrenme oranıyla deneyelim. Test fonksiyonu `f(x, y) = x² + 10 y²` olacak. Hessian `diag(2, 20)`, yani `λ_max = 20` ve kararlılık eşiği `2/20 = 0,1`. Üç öğrenme oranı seçelim: `0,005` (eşiğin çok altında), `0,08` (eşiğin altında ama yakın) ve `0,11` (eşiğin üstünde). Her biri `(1, 1)` noktasından başlasın.

Aşağıda kütüphane kodunu tamamen veriyoruz. Bu dosyadaki her yöntemi bu bölümün ilgili alt başlığında açıklayacağız; şimdilik yalnızca `gd` fonksiyonu ile ilgilen. Test fonksiyonları ve gradyanları, sonraki deneylerde de kullanılacak.

Kütüphanenin başı: üç test fonksiyonu ve gradyanları. `kuad` iyi koşullu (κ = 10), `kot` kötü koşullu (κ = 100), `rosen` ise konveks olmayan klasik vadidir. Her gradyanı elle türettik ve yukarıda ayrıca kontrol edilmesi gereken bir değer olarak kullanıyoruz.

```python
# -*- coding: utf-8 -*-
# Bölüm 50 - Optimizasyon: sıfırdan gradyan tabanlı yöntemler.
import numpy as np

def kuad(x):
    """f(x, y) = x^2 + 10 y^2   (kappa = 10)."""
    return x[0] ** 2 + 10 * x[1] ** 2

def kuad_g(x):
    return np.array([2 * x[0], 20 * x[1]])

def kot(x):
    """f(x, y) = x^2 + 100 y^2   (kappa = 100)."""
    return x[0] ** 2 + 100 * x[1] ** 2

def kot_g(x):
    return np.array([2 * x[0], 200 * x[1]])

def rosen(x):
    """Rosenbrock: (1-x)^2 + 100 (y-x^2)^2, minimum (1, 1)."""
    return (1 - x[0]) ** 2 + 100 * (x[1] - x[0] ** 2) ** 2

def rosen_g(x):
    a = x[1] - x[0] ** 2
    return np.array([-2 * (1 - x[0]) - 400 * x[0] * a, 200 * a])
```

Düz gradyan inişi (`gd`) ve momentum yöntemleri. `gd` her adımda `η g` kadar gider ve bütün yörüngeyi bir dizi olarak döndürür; böylece yakınsamayı sonradan ölçebiliriz. Momentum ve Nesterov fonksiyonlarını 50.7'de türetiyoruz.

```python
def gd(g, x0, eta, n):
    x = np.asarray(x0, float).copy()
    yol = [x.copy()]
    for _ in range(n):
        x = x - eta * g(x)
        yol.append(x.copy())
    return np.array(yol)

def momentum(g, x0, eta, n, beta=0.9):
    x = np.asarray(x0, float).copy()
    v = np.zeros_like(x)
    yol = [x.copy()]
    for _ in range(n):
        v = beta * v + g(x)
        x = x - eta * v
        yol.append(x.copy())
    return np.array(yol)

def nesterov(g, x0, eta, n, beta=0.9):
    x = np.asarray(x0, float).copy()
    v = np.zeros_like(x)
    yol = [x.copy()]
    for _ in range(n):
        v = beta * v - eta * g(x + beta * v)
        x = x + v
        yol.append(x.copy())
    return np.array(yol)
```

AdaGrad, RMSProp ve Adam. Bu üç yöntemin her biri her koordinat için ayrı bir ölçek tutar; formülleri 50.8'de türetiyoruz. `wd` parametresi AdamW'nin ağırlık azaltmasıdır; kavramsal farkını da 50.8'de açıklıyoruz.

```python
def adagrad(g, x0, eta, n, eps=1e-8):
    x = np.asarray(x0, float).copy()
    G = np.zeros_like(x)
    yol = [x.copy()]
    for _ in range(n):
        gr = g(x)
        G += gr * gr
        x = x - eta * gr / (np.sqrt(G) + eps)
        yol.append(x.copy())
    return np.array(yol)

def rmsprop(g, x0, eta, n, rho=0.9, eps=1e-8):
    x = np.asarray(x0, float).copy()
    E = np.zeros_like(x)
    yol = [x.copy()]
    for _ in range(n):
        gr = g(x)
        E = rho * E + (1 - rho) * gr * gr
        x = x - eta * gr / (np.sqrt(E) + eps)
        yol.append(x.copy())
    return np.array(yol)

def adam(g, x0, eta, n, b1=0.9, b2=0.999, eps=1e-8, wd=0.0):
    x = np.asarray(x0, float).copy()
    m = np.zeros_like(x)
    v = np.zeros_like(x)
    yol = [x.copy()]
    for t in range(1, n + 1):
        gr = g(x)
        m = b1 * m + (1 - b1) * gr
        v = b2 * v + (1 - b2) * gr * gr
        mh = m / (1 - b1 ** t)
        vh = v / (1 - b2 ** t)
        x = x - eta * (mh / (np.sqrt(vh) + eps) + wd * x)
        yol.append(x.copy())
    return np.array(yol)
```

Yakınsama ölçümü: her adımda `f(x_k) − f*` değerini bir diziye yazar. Sonraki tüm karşılaştırmalar bu diziye dayanır.

```python

def yakinsama(f, yol, f_star=0.0):
    """Her adım için f(x_k) - f*; numpy dizisi döndürür."""
    return np.array([f(x) - f_star for x in yol])
```

Şimdi öğrenme oranı deneyini çalıştıran programı yazıyoruz. Bu program `gd`'yi üç öğrenme oranıyla çalıştırır, her adımda değeri kaydeder ve "kalıcı yakınsama" adımını ölçer: değerin `10⁻⁶`'nın altına bir daha çıkmadığı ilk adım. Bu ölçüt, bir kez geçici olarak eşiği aşağı kesip sonra salınan yöntemleri yanlış saymamızı önler; bu nokta 50.9'da yeniden önem kazanacak.

Program önce kütüphaneden `gd`yi ve test fonksiyonunu alır. `kalici` fonksiyonu, değerin eşiğin altına inip bir daha çıkmadığı ilk adımı döndürür; eşiği hiç geçmeyen yöntemler için `None` verir.

```python
# -*- coding: utf-8 -*-
# Ogrenme orani, zikzak ve optimizer karsilastirmasi (sabit tohum yok:
# deterministik yontemler).
import csv
import numpy as np
from b50_core import (kuad, kuad_g, kot, kot_g, rosen, rosen_g, gd,
                      momentum, nesterov, adagrad, rmsprop, adam)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"
np.seterr(all="ignore")

def kalici(fk, esik=1e-6):
    """Eşiğin altına İNİP bir daha çıkmayan ilk adım (None: yok)."""
    kotu = np.where(np.asarray(fk) >= esik)[0]
    if len(kotu) == 0:
        return 0
    if kotu[-1] == len(fk) - 1:
        return None
    return int(kotu[-1]) + 1

# 1) Ogrenme orani uc durum: kuad, lambda_max = 20, kararli esik 2/20
print("kararli esik 2/lambda_max = 0.1")
yollar = {}
for eta in (0.005, 0.08, 0.11):
    y = gd(kuad_g, [1.0, 1.0], eta, 200)
    yollar[eta] = y
    fk = np.array([kuad(x) for x in y])
    adim = kalici(fk)
    print("eta=%.3f  f(50)=%.3e  f(200)=%.3e  adim(f<1e-6)=%s"
          % (eta, fk[50], fk[200], adim))
```

Ana döngü üç öğrenme oranını çalıştırır ve sonuçları yazdırır. CSV dosyası Şekil 50.3'ü çizmek için kullanılır; yalnızca ilk 60 adımı kaydeder.

```python
with open(VERI + "b50_ogrenme_orani.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["eta", "adim", "x", "y"])
    for eta, y in yollar.items():
        for k, p in enumerate(y[:60]):
            w.writerow(["%.3f" % eta, k,
                        "%.6f" % p[0], "%.6f" % p[1]])
```

Çıktı üç olguyu gösteriyor. `η = 0,08` 40. adımda kalıcı olarak yakınsıyor. `η = 0,005` 200 adımda hâlâ `0,018` değerinde: çok yavaş. `η = 0,11` ise eşiği aştığı için ıraksıyor; değer 200. adımda `10³²` mertebesindedir.

```term
$ python b50_deney2a.py
kararli esik 2/lambda_max = 0.1
eta=0.005  f(50)=3.663e-01  f(200)=1.795e-02  adim(f<1e-6)=None
eta=0.080  f(50)=2.679e-08  f(200)=5.149e-31  adim(f<1e-6)=40
eta=0.110  f(50)=8.282e+08  f(200)=4.704e+32  adim(f<1e-6)=None
```

![Şekil 50.3: Üç öğrenme oranıyla f = x² + 10y² üzerinde gradyan inişi. Küçük η yavaş, uygun η hızlı ama salınımlı, kararlılık eşiğini aşan η ıraksar.](gorseller/b50_ogrenme_orani.png)

Şekil 50.3 bu üç davranışı gösteriyor. Mavi yörünge (`η = 0,005`) x-ekseni boyunca yavaşça ilerliyor: x yönünde her adımda `(1 − 0,01)` ile çarpılıyor, yani çok sayıda adım gerekiyor. Yeşil yörünge (`η = 0,08`) y-yönünde zikzak yapıyor, çünkü y yönünde çarpan `1 − 0,08 · 20 = −0,6`: her adımda işaret değiştiriyor ama genlik azalıyor. Kırmızı yörünge (`η = 0,11`) y-yönünde `1 − 0,11 · 20 = −1,2` çarpanıyla büyüyor; üç-dört adımda çerçevenin dışına çıkıyor. Kararlılık eşiği, tam olarak bu y-yönündeki çarpanın `−1`'i geçmemesi koşuludur.

Bu sonuç mühendislik açısından öğretici bir uyarıdır. Bir kontrol döngüsünde ya da bir eğitim işinde öğrenme oranını "biraz büyütmek" bir anda ıraksamaya yol açabilir. Pratik çözüm, öğrenme oranını eşiğin yarısı kadar seçmek ve bir deneme koşusunda kaybın azaldığını doğrulamaktır. Bu yaklaşımın bir sonraki adımı, öğrenme oranını eğitim boyunca değiştirmektir; bunu 50.10'da takvimlerle yapacağız.

## 50.6 Stokastik gradyan inişi: gürültü ve mini-batch

Makine öğrenmesinde kayıp genellikle bir **toplamdır**: `L(θ) = (1/n) Σ ℓ_i(θ)`, burada `n` veri noktası sayısıdır. Milyonlarca örnekte tam gradyanı hesaplamak her adımda milyonlarca gradyan hesabı demektir. Stokastik gradyan inişi (SGD) bunun yerine rastgele seçilmiş küçük bir alt küme, yani **mini-batch** `B` üzerinden bir gradyan tahmini alır:

    g_B(θ) = (1/|B|) Σ_{i ∈ B} ∇ℓ_i(θ)

Bu tahmin doğru bir sonuç verir: beklenen değeri tam gradyandır, `E[g_B] = ∇L`. Ama tek bir adımda gürültülüdür. Bu gürültünün büyüklüğünü de ölçebiliriz: örneklerin rastgele seçimi nedeniyle `g_B`'nin kovaryansı yaklaşık `Σ / B` kadardır, burada `Σ` tek bir örneğin gradyanının kovaryansıdır. Örnekleme yerine koymadan yapıldığında bu değer, `(n − B) / (n − 1)` sonlu popülasyon düzeltmesiyle çarpılır. Yani `B` arttıkça gürültü azalır, ama her adımın maliyeti de artar. Bu bir **gürültü–hız takasıdır**.

Bu takası ölçelim. Doğrusal regresyon kullanacağız: `n = 2000`, `d = 5`, gerçek ağırlıklar `(1, −2, 0,5, 3, −1)`'e yakın, gürültü standart sapması `0,5`. Tohum `0`. İlk deneyde `w = 0` noktasında parti gradyanının kovaryans izini (trace) farklı `B` değerleri için ölçeceğiz. Beklenti: `tr(Cov) ≈ S / B · (n − B)/(n − 1)`, dolayısıyla `B · tr(Cov)` küçük `B` için yaklaşık sabit, büyük `B`'de ise sonlu popülasyon nedeniyle azalmalı.

Bu deney, programın ilk bölümüdür. İkinci bölümde ise eşit sayıda **epoch** (tüm veriyi bir kez görme) içinde farklı `B` değerlerinin artık kaybını karşılaştırıyoruz. Bu program için ayrıca dikkat et: tohum `default_rng(0)` ile veri, `default_rng(100 + t)` ile sıralama için kullanılıyor.

Veri üretimi ve tam çözüm. `lstsq` ile tam gradyanın sıfır olduğu `w*` bulunur; SGD sonuçları bununla karşılaştırılacak. `grad_parti` yalnızca seçilen indekslerin gradyanını hesaplar.

```python
# -*- coding: utf-8 -*-
# SGD gurultusu, Newton karesel yakinsama, LM, cizgi aramasi, BFGS.
import csv
import numpy as np
from scipy.optimize import minimize, least_squares
from b50_core import rosen, rosen_g

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"

# ---- 1) Stokastik gradyan: dogrusal regresyon, n=2000, d=5 ----
rng = np.random.default_rng(0)
n, d = 2000, 5
X = rng.standard_normal((n, d))
wt = np.array([1.0, -2.0, 0.5, 3.0, -1.0])
y = X @ wt + 0.5 * rng.standard_normal(n)
w_star = np.linalg.lstsq(X, y, rcond=None)[0]

def kayip(w):
    return 0.5 * np.mean((X @ w - y) ** 2)

def grad_parti(w, idx):
    Xb = X[idx]
    return Xb.T @ (Xb @ w - y[idx]) / len(idx)

# gurultu: w=0'da parti gradyaninin kovaryans izi, B ile olcekleniyor
w0 = np.zeros(d)
for B in (1, 8, 64, 512):
    gs = np.array([grad_parti(w0, rng.choice(n, B, replace=False))
                   for _ in range(2000)])
    iz = np.trace(np.cov(gs.T))
    print("B=%4d  tr(Cov)=%.4f  B*tr(Cov)=%.2f" % (B, iz, B * iz))
```

İki ayrı ölçüm: (1) `w = 0`'da farklı `B` için 2000 rastgele parti gradyanının kovaryans izi, (2) 20 epoch boyunca sabit `η = 0,05` ile SGD ve 5 tohumun ortalama artık kaybı. Artık kayıp `L(w) − L(w*)` ile ölçülür.

```python
print("\nB  guncelleme  artik kayip (5 tohum ortalamasi)")
for B in (1, 16, 256, 2000):
    artik = []
    for tohum in range(5):
        r = np.random.default_rng(100 + tohum)
        w = np.zeros(d)
        adim = 0
        for _ in range(20):
            p = r.permutation(n)
            for i in range(0, n, B):
                w = w - 0.05 * grad_parti(w, p[i:i + B])
                adim += 1
        artik.append(kayip(w) - kayip(w_star))
    print("%4d  %8d       %.5f" % (B, adim, np.mean(artik)))
```

Birinci tabloda `B · tr(Cov)` değerleri `B = 1`'den `64`'e kadar yaklaşık 90'da sabit; bu, varyansın `1/B` ile ölçeklendiğini gösterir. `B = 512`'de değer 70'e iner: bu, sonlu popülasyon düzeltmesinin `(2000 − 512)/1999 ≈ 0,74` çarpanıdır. İkinci tabloda `B = 2000` (tam gradyan) yalnızca 20 güncelleme yapar ve bu kadar az adımla hâlâ `0,97` artık kayıp kalır; `B = 1` ise 40000 güncellemeye rağmen gürültüden `0,0196` artık kayıpta takılır.

```term
$ python b50_deney3a.py
B=   1  tr(Cov)=94.8806  B*tr(Cov)=94.88
B=   8  tr(Cov)=11.3602  B*tr(Cov)=90.88
B=  64  tr(Cov)=1.4032  B*tr(Cov)=89.81
B= 512  tr(Cov)=0.1359  B*tr(Cov)=69.58

B  guncelleme  artik kayip (5 tohum ortalamasi)
   1     40000       0.01957
  16      2500       0.00038
 256       160       0.00000
2000        20       0.97422
```

Bu tablo iki yanlış sezgiyi yıkıyor. İlki, "küçük batch her zaman daha iyidir" demek. Küçük batch daha çok güncelleme yapar ama her güncelleme gürültülüdür; sabit öğrenme oranında gürültü, optimumun çevresinde sürekli bir titreşim bırakır. İkincisi, "büyük batch her zaman daha iyidir" demek. Büyük batch daha az gürültülüdür ama aynı epoch sayısında çok daha az adım atar. Bu iki uç arasında, verinin gürültüsüne, modelin boyutuna ve bilgisayarın paralelliğine bağlı bir optimum vardır. Eğitim pratiğinde batch boyutu ve öğrenme oranı birlikte ayarlanır; bu bağlantı Bölüm 64'te ayrıntılı olarak ele alınacak.

Burada bir not: SGD'nin hızını bir **zaman** ölçüsüyle değil, **güncelleme** sayısıyla kıyasladık. Gerçek bir donanımda büyük batch paralel işlendiği için saat süresi farklı olabilir. Ama yakınsama teorisinin temel birimi güncelleme sayısıdır ve kararlı bir karşılaştırma için bu birim gereklidir.

## 50.7 Momentum ve Nesterov: vadide hız kazanmak

Gradyan inişinin en büyük sorunu zikzaktır. Kötü koşullu bir vadide gradyan, vadinin dik kenarına neredeyse dik bir yön gösterir; yöntem bir kenardan diğerine sekerken asıl hedef olan vadi boyunca çok yavaş ilerler. 50.5'teki `κ = 100` örneğinde gradyan inişinin 571 adım gerektirmesinin nedeni budur.

**Momentum**, bu zikzakları bir "hız" (velocity) değişkeniyle yumuşatır. Polyak'ın ağır top (heavy ball) yöntemi:

    v_{k+1} = β v_k + ∇f(x_k)
    x_{k+1} = x_k − η v_{k+1}

Burada `β ∈ [0, 1)` bir sönümleme katsayısıdır ve tipik değeri `0,9`. Bu formülün sezgisi şudur: her adım, önceki adımların ağırlıklı toplamını taşır. Gradyan birbirini tutarlı biçimde işaret ediyorsa (vadinin uzun ekseni boyunca) hız birikir ve etkili adım yaklaşık `η / (1 − β)` kadar büyür. Gradyan işaret değiştiriyorsa (dik kenar), birbirini götürür ve sönümlenir. Bu yüzden momentum vadide hız kazanır, kenarlarda ise sekmeyi azaltır.

Kuadratik fonksiyon için optimal parametreler klasik olarak şöyledir (genel bilgi, Polyak 1964): `η = 4 / (√λ_max + √λ_min)²` ve `β = ((√κ − 1) / (√κ + 1))²`. Ayrıca bu seçimle hata, her adımda yaklaşık `(√κ − 1)/(√κ + 1)` oranıyla küçülür; gradyan inişinin `(κ − 1)/(κ + 1)` oranına göre çok daha hızlıdır. `κ = 100` için bu iki oran sırasıyla `0,818` ve `0,980`'dir.

**Nesterov'in hızlandırılmış gradyanı**, gradyanı mevcut noktada değil, momentumun gösterdiği noktada hesaplar. Sutskever'in yaygın biçimi şöyledir:

    v_{k+1} = β v_k − η ∇f(x_k + β v_k)
    x_{k+1} = x_k + v_{k+1}

Sezgisi bir "önce bak, sonra düzelt" hareketidir. Momentum seni bir yöne itiyorsa, Nesterov önce o yöne bakar ve gradyanı orada ölçer. Eğer orada yokuş aşağı gidiyorsan düzeltme daha erken yapılır; bu, vadinin dibinde aşırı salınımı önler. Konveks fonksiyonlarda Nesterov'in hızlandırılmış yöntemi `O(1/k²)` yakınsama garantisi verir; saf gradyan inişinin `O(1/k)` garantisinden daha iyidir (genel bilgi, Nesterov 1983).

Bu iki yöntemin kodu kütüphanedeki `momentum` ve `nesterov` fonksiyonlarındadır. Aşağıda yalnızca tanımın kod karşılığını tekrar ediyoruz: `v` her zaman sıfırla başlar, gradyan kendi yerinde ölçülür (momentum) ya da ileri konumda (Nesterov) ölçülür. Yakınsama ölçümlerini 50.9'da yapacağız.

## 50.8 Uyarlamalı yöntemler: AdaGrad, RMSProp ve Adam

Momentum tüm koordinatlar için aynı öğrenme oranını kullanır. Oysa farklı parametreler farklı ölçeklerde gradyan alabilir: bir ağırlık çok sık ve büyük gradyan alırken, bir başkası nadiren ve küçük. **Uyarlamalı** yöntemler her koordinat için ayrı bir ölçek tutar: geçmiş gradyanların büyüklüğüne göre her koordinatın adımını ayarlar.

**AdaGrad** (Duchi ve arkadaşları, 2011), her koordinat için geçmiş karelerin toplamını biriktirir:

    G_k = G_{k−1} + g_k ⊙ g_k
    x_{k+1} = x_k − η g_k / (√G_k + ε)

Burada `⊙` bileşen bileşen çarpımdır, `ε` sıfıra bölmeyi önleyen küçük bir sayıdır (`10⁻⁸`). Sezgisi: sık büyük gradyan alan koordinat hızla büyüyen `G` ile yavaşlar; nadir koordinat ise hızlı kalır. Dezavantaj, `G`'nin sürekli büyümesi ve öğrenme oranını zamanla sıfıra götürmesidir; bu yüzden uzun eğitimlerde adımlar durabilir.

**RMSProp** (Hinton'un ders notlarında tanıtılmış, yayımlanmamış bir yöntem; genel bilgi), `G` yerine üstel hareketli ortalama kullanır. Böylece eski gradyanlar sönümlenir ve adımlar durmaz:

    E_k = ρ E_{k−1} + (1 − ρ) g_k ⊙ g_k
    x_{k+1} = x_k − η g_k / (√E_k + ε)

Tipik `ρ = 0,9`. Bu fark küçük görünür, ama AdaGrad'ın ölümcül sorununu çözer.

**Adam** (Kingma ve Ba, 2014) iki fikri birleştirir: gradyanın birinci momentini (momentum benzeri, `m`) ve ikinci momentini (RMSProp benzeri, `v`) hareketli ortalama olarak tutar:

    m_k = β₁ m_{k−1} + (1 − β₁) g_k
    v_k = β₂ v_{k−1} + (1 − β₂) g_k ⊙ g_k

Tipik değerler `β₁ = 0,9`, `β₂ = 0,999` ve `ε = 10⁻⁸`. Ama burada bir sorun var ve Adam'ın kalbi bu sorunun çözümüdür. `m_0 = 0` ve `v_0 = 0` ile başladığımız için ilk birkaç adımda `m` ve `v` gerçek momentlerin **yanlı** (biased) tahminleridir: sıfıra doğru çekilmişlerdir. Bunu görmek için beklenti alalım. Gradyanların sabit ortalamalı olduğunu varsayarsak, `E[m_k] = (1 − β₁^k) E[g]` ve `E[v_k] = (1 − β₂^k) E[g²]` çıkar. Yani `m_k`, gerçek momentin `(1 − β₁^k)` katıdır; `v_k` ise `(1 − β₂^k)` katıdır.

Bu yanlılığı düzeltmek için her ikisini de bu katsayılara bölersin:

    m̂_k = m_k / (1 − β₁^k)
    v̂_k = v_k / (1 − β₂^k)
    x_{k+1} = x_k − η m̂_k / (√v̂_k + ε)

Bu düzeltmenin etkisini görmek için ilk adımı hesaplayalım. `k = 1` için `m_1 = (1 − β₁) g_1` ve `v_1 = (1 − β₂) g_1²`. Düzeltmeli değerler `m̂_1 = g_1` ve `v̂_1 = g_1²` olur. Adım `η g_1 / |g_1| = η` büyüklüğünde olur ve işareti gradyanı izler. Düzeltmesiz hâlde ise adım, `(1 − β₁) / √(1 − β₂) = 0,1 / 0,0316 = 3,16` kat daha büyük olur. Yani biyas düzeltmesi olmazsa Adam ilk adımlarda öğrenme oranını gereksiz yere üç kat büyütür. Bu, uygulamada eğitimin başında kararsızlığa yol açabilir.

Adam'ın bir başka sonucu da adım büyüklüğünün gradyanın **ölçeğinden bağımsız** olmasıdır: `m̂ / √v̂` oranı, gradyanın işaretine bağlı olarak kabaca `±1` mertebesindedir. Bu yüzden Adam'ın adımları yaklaşık `η` kadardır, her koordinat için. Bu iyi bir özellik (ölçek farklılıklarına dayanıklı) ama aynı zamanda `η`'nın tek başına doğru yakınsamayı belirlediği anlamına gelir: öğrenme oranını doğru seçmezsen ne kadar uyarlamalı olursa olsun yöntem ıraksar ya da çok yavaşlar. Bunu 50.9'daki deneyde de göreceğiz.

**AdamW** (Loshchilov ve Hutter, 2019; genel bilgi) ağırlık azaltmayı (weight decay) gradyan hesabından ayırır. Klasik L2 düzenlileştirmesinde kaybın gradyanına `λθ` eklenir; Adam bu terimi de kendi `v` ölçeğiyle bölünce ağırlık azaltma büyük gradyanı olan parametreler için zayıflar. AdamW ise azaltmayı doğrudan parametreye uygular:

    x_{k+1} = x_k − η (m̂_k / (√v̂_k + ε) + λ x_k)

Kütüphanedeki `adam` fonksiyonundaki `wd` parametresi bu ikinci biçimdir. Gradyan kaybın gradyanı olarak kalır, azaltma ayrıca uygulanır. Bu ayrım Bölüm 64'te eğitim pratiğine geçtiğimizde çok önemli olacak; şimdilik kavramı bilmen yeterli.

## 50.9 Karşılaştırma: zikzak, momentum ve uyarlamalı yöntemler

Bütün yöntemleri aynı problemlerde yan yana koyalım. İki test fonksiyonu kullanıyoruz: `kot` (κ = 100, kötü koşullu ama konveks) ve `rosen` (Rosenbrock, konveks değil, dar kıvrımlı vadi). Başlangıç noktaları sabit: `kot` için `(1, 1)`, `rosen` için `(−1,2; 1)`.

Her yöntem için adaylar `η ∈ {10⁻⁴, 3·10⁻⁴, …, 3·10⁻¹}` ızgarasından seçilir. Seçim ölçütü, değerin `10⁻⁶`'nın altına **kalıcı** olarak indiği ilk adımdır. Bu ayarın bir **oracle** ayar olduğunu açıkça belirtmek gerekir: test problemi üzerinde ayar yapıyoruz, dolayısıyla tablo yöntemlerin en iyi performansını karşılaştırır, genelleme performansını değil. Bu, optimizasyon yöntemlerinin davranışını anlamak için uygun bir ölçüttür; üretim eğitimlerinde ayar, doğrulama verisiyle yapılır (Bölüm 57).

Programda ayrıca momentumun zikzak üzerindeki etkisini de görüyoruz: GD ile momentumun `κ = 100` vadisindeki yörüngeleri aynı başlangıçtan çıkıyor. GD için `η = 0,0099` (≈ 2/(λ_min + λ_max)), momentum için kuadratik optimal parametreler kullanıldı.

Programın başı, 50.5'teki gibi kalıcı yakınsama ölçütünü ve kütüphaneyi kullanır. Bu parçada yalnızca `kot` için GD ve momentumun sabit parametreleriyle zikzak karşılaştırması yapılır.

```python
# -*- coding: utf-8 -*-
# Ogrenme orani, zikzak ve optimizer karsilastirmasi (sabit tohum yok:
# deterministik yontemler).
import csv
import numpy as np
from b50_core import (kuad, kuad_g, kot, kot_g, rosen, rosen_g, gd,
                      momentum, nesterov, adagrad, rmsprop, adam)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"
np.seterr(all="ignore")

def kalici(fk, esik=1e-6):
    """Esigin altina inip kalan ilk adim; yoksa None."""
    kotu = np.where(np.asarray(fk) >= esik)[0]
    if len(kotu) == 0:
        return 0
    if kotu[-1] == len(fk) - 1:
        return None
    return int(kotu[-1]) + 1

# 2) Zikzak: kot (kappa=100). GD eta=0.0099 ~ 2/(lmin+lmax); momentum
N = 1200
y_gd = gd(kot_g, [1.0, 1.0], 0.0099, N)
y_mo = momentum(kot_g, [1.0, 1.0], 0.0165, N, beta=0.67)
for ad, y in (("GD", y_gd), ("Momentum", y_mo)):
    fk = np.array([kot(x) for x in y])
    adim = kalici(fk, 1e-8)
    print("%-9s adim(f<1e-8)=%s  f(100)=%.3e" % (ad, adim, fk[100]))
with open(VERI + "b50_zikzak.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["yontem", "adim", "x", "y"])
    for ad, y in (("GD", y_gd), ("Momentum", y_mo)):
        for k, p in enumerate(y[:150]):
            w.writerow([ad, k, "%.6f" % p[0], "%.6f" % p[1]])
```

Üçüncü bölüm, altı yöntemi iki problemde çalıştırır. Her yöntem için ızgaradan en hızlı kalıcı yakınsamayı veren `η` seçilir; ardından sonuç tablosu yazdırılır ve yörüngeler ile kayıp eğrileri CSV'ye kaydedilir.

```python
# 3) Rosenbrock ve kot: her yontem icin eta izgarasi (oracle ayari)
izgara = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 3e-1]
yontemler = {
    "GD": lambda g, x0, e, n: gd(g, x0, e, n),
    "Momentum": lambda g, x0, e, n: momentum(g, x0, e, n, 0.9),
    "Nesterov": lambda g, x0, e, n: nesterov(g, x0, e, n, 0.9),
    "AdaGrad": lambda g, x0, e, n: adagrad(g, x0, e, n),
    "RMSProp": lambda g, x0, e, n: rmsprop(g, x0, e, n),
    "Adam": lambda g, x0, e, n: adam(g, x0, e, n),
}
N = 20000
sonuc = {}
for pad, f, g, x0 in (("Rosenbrock", rosen, rosen_g, [-1.2, 1.0]),
                      ("kot", kot, kot_g, [1.0, 1.0])):
    print("\n==", pad, "(x0 =", x0, ", N =", N, ")")
    print("yontem    eta     f(sonuc)      adim(f<1e-6)")
    for ad, fn in yontemler.items():
        en = None
        for e in izgara:
            y = fn(g, x0, e, N)
            fk = np.array([f(x) for x in y])
            if not np.all(np.isfinite(fk)):
                continue
            a = kalici(fk)
            skor = (a if a is not None else 10 ** 9, fk[-1])
            if en is None or skor < en[0]:
                en = (skor, e, fk[-1], y, fk, a)
        skor, e, son, y, fk, adim = en
        print("%-9s %-6.0e %-13.3e %s" % (ad, e, son, adim))
        sonuc[(pad, ad)] = (e, y, fk)
```

Yörünge ve kayıp verisini kaydeden son kısım. Yörüngelerin ilk 3000 adımı, kayıp eğrisinin her 50 adımda bir noktası alınır; böylece figürler boyutu makul kalır.

```python
# yorunge ve kayip-adim verisi
with open(VERI + "b50_optimizer_yorunge.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["problem", "yontem", "adim", "x", "y"])
    for (pad, ad), (e, y, fk) in sonuc.items():
        lim = 3000 if pad == "Rosenbrock" else 60
        for k, p in enumerate(y[:lim]):
            if k % 3 == 0 or k < 60:
                w.writerow([pad, ad, k, "%.6f" % p[0], "%.6f" % p[1]])
with open(VERI + "b50_kayip_adim.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["problem", "yontem", "adim", "f"])
    for (pad, ad), (e, y, fk) in sonuc.items():
        for k in range(0, len(fk), 50):
            w.writerow([pad, ad, k, "%.6e" % fk[k]])
```

Zikzak tablosu: GD `κ = 100` vadisinde 571 adımda, momentum 65 adımda `10⁻⁸`'in altına iniyor. Karşılaştırma tablosunda Nesterov ve momentum Rosenbrock'ta yaklaşık 450–1426 adımda, GD'nin ise 15068 adımda ulaştığı `10⁻⁶` eşiğine iniyor; AdaGrad yaklaşık 8752 adım. Kot probleminde AdaGrad, `η = 0,3` ile 40 adımda ulaşıyor.

```term
$ python b50_deney2b.py
GD        adim(f<1e-8)=571  f(100)=1.777e+00
Momentum  adim(f<1e-8)=65  f(100)=1.967e-15

== Rosenbrock (x0 = [-1.2, 1.0] , N = 20000 )
yontem    eta     f(sonuc)      adim(f<1e-6)
GD        1e-03  1.938e-08     15068
Momentum  3e-03  1.245e-30     450
Nesterov  1e-03  7.704e-30     1426
AdaGrad   3e-01  8.917e-14     8752
RMSProp   3e-04  2.028e-05     None
Adam      3e-04  4.462e-13     18399

== kot (x0 = [1.0, 1.0] , N = 20000 )
yontem    eta     f(sonuc)      adim(f<1e-6)
GD        3e-03  2.853e-105    1148
Momentum  3e-03  0.000e+00     174
Nesterov  3e-03  0.000e+00     129
AdaGrad   3e-01  0.000e+00     40
RMSProp   1e-04  2.525e-07     10166
Adam      1e-03  0.000e+00     3123
```

![Şekil 50.4: κ = 100 vadisinde zikzak. Solda düz gradyan inişi, dik kenarlar arasında sekerek ilerliyor. Sağda momentum aynı vadide daha az sekiyor ve 65 adımda ulaşıyor.](gorseller/b50_zikzak.png)

Şekil 50.4'te sol panel düz gradyan inişinin zikzağını gösteriyor. Her adım dik kenara neredeyse dik gittiği için yatay ilerleme çok küçük. Sağ panel, aynı vadide momentumun yörüngesidir. Momentum da vadinin içinde salınıyor, ama salınım genliği hızla azalıyor ve vadinin dibine çok daha erken varıyor. Bu şekilde momentumun "zikzağı yok ettiğini" değil, "zikzağı hızlı sönümlediğini" görmek önemlidir.

Şekil 50.5, altı yöntemin Rosenbrock üzerindeki yörüngelerini ayrı panellerde gösteriyor. Panellerin ortak eksenleri var, böylece yörüngeler doğrudan karşılaştırılabilir.

![Şekil 50.5: Altı yöntemin Rosenbrock üzerindeki yörüngeleri (ilk 3000 adım). Gradyan inişi ve AdaGrad dar vadiye geç girer; momentum vadide büyük sıçramalar yapar; Adam ve RMSProp başlangıçta farklı yönlere sapar.](gorseller/b50_optimizer_yorunge.png)

Şekil 50.5'in okunması gereken noktası şudur: uyarlamalı yöntemlerin hız avantajı her zaman göze çarpmaz. Bu şekle bakarak hangi yöntemin "en iyi" olduğunu söyleyemezsin: sonuç öğrenme oranına ve vadinin eğimine bağlıdır. Tek bir problemden genel bir sıralama çıkarmak yanlıştır. Momentum, bu eğimli vadide hız kazanmaktadır ama vadi dışına çıkıp geri dönen büyük sıçramalar yapar; bu, Şekil 50.5'teki sivri yörüngelerdir.

![Şekil 50.6: Adım başına f(x_k) değeri (log ölçek). Soldaki Rosenbrock'ta momentum ve Nesterov en hızlı düşüyor. Sağdaki κ = 100 kasede Adam ve momentum hızlı, RMSProp salınımlı kalıyor.](gorseller/b50_kayip_adim.png)

Şekil 50.6, aynı deneyin kayıp eğrilerini log ölçekte veriyor. Kesikli yatay çizgi `10⁻⁶` eşiğidir. Bu eğriler, tablodaki sayıların "nasıl" oluştuğunu gösterir: GD ve AdaGrad'ın eğrileri düz bir çizgi gibidir, yani sabit bir oranla geometrik olarak küçülüyorlar. Momentum ve Nesterov'in eğrileri ilk adımlarda dik düşer ve vadinin dibine yaklaştıkça taban değerinde düzleşir. RMSProp'un Rosenbrock eğrisi (soldaki panel) belli bir noktada düzleşiyor: `ρ = 0,9` ile hareketli ortalamanın, bu öğrenme oranında vadinin dibinde adımları yeterince küçültememesi. Sağdaki panelde RMSProp'un ani bir sıçramayla düştüğünü görüyorsun; bu, yöntemin dar bir bölgede kararsızlaşıp yeniden toparlanması ile uyumludur. Bu tür davranışlar, bir yöntemin "kötü" olduğunu değil, o öğrenme oranında kararsız olduğunu gösterir.

Sonuçları bir karar tablosu hâline getirelim:

| Yöntem | Rosenbrock adım (f < 10⁻⁶) | kot adım (f < 10⁻⁶) | Yorum |
|---|---|---|---|
| GD | 15068 | 1148 | Zikzak; kötü koşulda yavaş |
| Momentum | 450 | 174 | Vadide hız; sıçramalar |
| Nesterov | 1426 | 129 | İleri bakış; sıçramayı azaltır |
| AdaGrad | 8752 | 40 | Büyük ölçek farkında güçlü |
| RMSProp | ulaşamadı | 10166 | Bu η'da kararsız |
| Adam | 18399 | 3123 | η = 3·10⁻⁴ çok küçük kaldı |

Bu tablo, "en iyi optimizer" diye bir şeyin olmadığını gösterir. Momentum, Rosenbrock gibi zor ama düzgün bir vadide en hızlı çıkan yöntemdir; AdaGrad, ölçek farkı olan problemlerde öne geçer; Adam ise genel amaçlı ama öğrenme oranına duyarlıdır. Bu yüzden tablodaki her satırın "hangi η ile" ve "hangi problemde" olduğunu okumak zorunludur.

## 50.10 Öğrenme oranı takvimleri

Sabit bir öğrenme oranı iki çelişkili isteği aynı anda karşılamak zorundadır. Başlangıçta, uzakta olduğun yerde büyük adımlar atmak istersin. Sonda, optimuma yakınken küçük adımlar atmak istersin; yoksa salınım yaparsın. **Öğrenme oranı takvimi** (learning rate schedule), bu iki ihtiyacı zamana bağlı olarak ayırır.

Üç temel takvim vardır. **Adım azaltma** (step decay), öğrenme oranını belirli aralıklarla sabit bir çarpanla küçültür: örneğin her 30 epoch'ta yarıya indirmek gibi. **Kosinüs azaltma**, öğrenme oranını bir kosinüs eğrisiyle sıfıra doğru yumuşakça düşürür: `η_t = η_min + ½ (η_max − η_min)(1 + cos(π t / T))`. Bu, sonda küçük adımları yumuşak biçimde sağlar. **Isınma** (warm-up), eğitimin başında öğrenme oranını sıfırdan `η_max`'a doğru lineer olarak artırır. Bu, Adam'ın yanlı ilk adımlarının yarattığı belirsizliği, 50.8'de gördüğümüz düzeltmeye ek olarak yumuşatır; büyük modellerde standart bir uygulamadır.

Takvimlerin etkisini 50.9'daki Rosenbrock problemi üzerinde, Adam ile ölçelim. Karşılaştırma için iki sabit öğrenme oranı da ekliyoruz. Takvimler şunlar: adım azaltma her 5000 adımda öğrenme oranını `0,3` ile çarpar; kosinüs `η_max = 3·10⁻³`'ten `η_min = 10⁻⁵`'e yumuşakça iner; ısınma + kosinüs ilk 500 adımda `η`'yı sıfırdan `η_max`'a doğru lineer artırır ve sonra kosinüsle iner. Bütün koşular aynı 20000 adım bütçesini kullanır ve aynı başlangıç noktasından çıkar.

Program önce `adam_takvim`i tanımlar. Bu, kütüphanedeki `adam` ile aynıdır; tek fark, öğrenme oranının her adımda `takvim(t)` fonksiyonundan okunmasıdır. Kalıcı yakınsama ölçütü 50.5'teki ile aynıdır.

```python
# -*- coding: utf-8 -*-
# Ogrenme orani takvimleri: Adam ile sabit, adim, kosinus.
import numpy as np
from b50_core import rosen, rosen_g

np.seterr(all="ignore")

def kalici(fk, esik=1e-6):
    kotu = np.where(np.asarray(fk) >= esik)[0]
    if len(kotu) == 0:
        return 0
    if kotu[-1] == len(fk) - 1:
        return None
    return int(kotu[-1]) + 1

def adam_takvim(g, x0, takvim, n, b1=0.9, b2=0.999, eps=1e-8):
    x = np.asarray(x0, float).copy()
    m = np.zeros_like(x)
    v = np.zeros_like(x)
    yol = [x.copy()]
    for t in range(1, n + 1):
        gr = g(x)
        m = b1 * m + (1 - b1) * gr
        v = b2 * v + (1 - b2) * gr * gr
        mh = m / (1 - b1 ** t)
        vh = v / (1 - b2 ** t)
        x = x - takvim(t) * mh / (np.sqrt(vh) + eps)
        yol.append(x.copy())
    return np.array(yol)
```

Takvim fonksiyonları: kosinüs, ısınma + kosinüs ve adım azaltma. Her biri adım sayacı `t`'yi alır ve o adımın öğrenme oranını döndürür; sabit takvimler için ayrı bir lambda kullanılır.

```python
N = 20000
ETA = 3e-3
ETA_MIN = 1e-5
ISINMA = 500

def kosinus(t):
    ilerleme = np.pi * (t - 1) / N
    return ETA_MIN + 0.5 * (ETA - ETA_MIN) * (1 + np.cos(ilerleme))

def isinma_kosinus(t):
    if t <= ISINMA:
        return ETA * t / ISINMA
    ilerleme = np.pi * (t - ISINMA) / (N - ISINMA)
    return ETA_MIN + 0.5 * (ETA - ETA_MIN) * (1 + np.cos(ilerleme))

def adim(t):
    return ETA * 0.3 ** ((t - 1) // 5000)
```

Takvim sözlüğü ve çalıştırma döngüsü. Her takvim aynı bütçeyle koşulur; sonuç tablosunda kalıcı yakınsama adımı, son değer ve yörünge boyunca görülen en küçük değer yer alır.

```python
takvimler = {
    "sabit 3e-4": lambda t: 3e-4,
    "sabit 3e-3": lambda t: ETA,
    "adim (x0.3 / 5000)": adim,
    "kosinus": kosinus,
    "isinma + kosinus": isinma_kosinus,
}
print("Rosenbrock, Adam, N = %d, x0 = (-1.2, 1.0)" % N)
print("takvim              adim(f<1e-6)   son f         en iyi f")
for ad, tk in takvimler.items():
    y = adam_takvim(rosen_g, [-1.2, 1.0], tk, N)
    fk = np.array([rosen(x) for x in y])
    print("%-19s %-14s %-13.3e %.3e"
          % (ad, kalici(fk), fk[-1], fk.min()))
```

Kosinüs takvimi 7972 adımla eşiğin altına kalıcı olarak giren en hızlı koşu. Adım azaltma 9435, ısınma + kosinüs 10379 adım harcıyor. Sabit `3·10⁻³` en sonunda (19761) kalıcı olarak giriyor, ama bu adıma kadar değer eşiğin üstüne çıkıp inmeye devam ediyor; yörüngedeki en küçük değer `10⁻³²` mertebesinde, yani sayısal olarak çok iyi, yalnızca salınım hâlinde. Sabit `3·10⁻⁴` ise daha küçük adımlarla 18399 adımda yakınsıyor.

```term
$ python b50_deney2c.py
Rosenbrock, Adam, N = 20000, x0 = (-1.2, 1.0)
takvim              adim(f<1e-6)   son f         en iyi f
sabit 3e-4          18399          4.462e-13     4.462e-13
sabit 3e-3          19761          3.742e-15     1.233e-32
adim (x0.3 / 5000)  9435           3.244e-17     1.972e-31
kosinus             7972           7.889e-31     7.889e-31
isinma + kosinus    10379          4.930e-30     4.930e-30
```

Bu tablo iki şey gösteriyor. Birincisi, büyük sabit öğrenme oranı eşiğin çok altına inebilse de son aşamada salınır; takvim bu salınımı sonda öğrenme oranını küçülterek bastırır. Kosinüs takvimi bunu en yumuşak biçimde yapar ve bu yüzden bu problemde en hızlı kalıcı yakınsamayı verir. İkincisi, takvim bir sihirli değnek değildir: ısınma + kosinüs, ilk 500 adımı düşük öğrenme oranıyla harcadığı için kosinüsten yavaş kalır. Bu tek problem ve tek bir deterministik koşu olduğu için bu sıralamayı genelleyemeyiz. Gerçek bir eğitimde takvim parametreleri (`η_max`, `η_min`, ısınma süresi) doğrulama verisi üzerinde, Bölüm 57'deki deney tasarımı ilkelerine göre seçilir.

Takvimlerin asıl etkisi, gradyan inişinin kararlılık eşiğini zamanla değiştirmesidir. Eğitimin başında büyük `η` ile geniş bir alanı tararsın; sonda küçük `η` ile dar bir çukurun dibine inersin. Bu iki evreyi tek bir sabit `η` ile yapmaya çalışmak, ya yavaş ya da salınımlı bir eğitim üretir. Büyük modellerde takvim ve ısınma, bu yüzden neredeyse standart bir bileşendir; sinir ağlarındaki uygulamasını Bölüm 64'te göreceğiz.

## 50.11 İkinci dereceden yöntemler: Newton ve Levenberg–Marquardt

Gradyan inişi yalnızca birinci türevi kullanır. Hessian'ı da kullanırsak yakınsamayı çok hızlandırabiliriz. **Newton yöntemi**, her adımda fonksiyonu ikinci dereceden Taylor açılımıyla yaklaşıklar ve bu yaklaşığın minimumuna gider:

    x_{k+1} = x_k − H(x_k)⁻¹ ∇f(x_k)

Bu adımın anlamı şudur: Hessian'ın tersi, gradyanı eğriliğe göre ölçeklendirir. Dik bir kase için (`H` büyük) adım küçülür; yatık bir düzlük için (`H` küçük) adım büyür. Gradyan inişinin tek bir sabit `η`'sının yapamadığını, Newton her koordinat yönünde otomatik yapar. Bu yüzden kuadratik bir fonksiyonda Newton tek adımda minimuma iner.

Newton'un en önemli özelliği **karesel yakınsamadır** (quadratic convergence). Eğer iterasyon minimuma yeterince yakınsa, hata her adımda yaklaşık olarak kendi karesi kadar küçülür: `e_{k+1} ≈ C e_k²`. Bu, doğru basamak sayısının iterasyon başına yaklaşık iki katına çıktığı anlamına gelir. Bunu görmek için karekökü hesaplayalım. `√2`'yi bulmak için `F(x) = x³/3 − 2x` fonksiyonunu minimize edelim; `F'(x) = x² − 2` ve `F'' (x) = 2x` olduğundan `√2` yerel minimumdur. Newton adımı `x − (x² − 2)/(2x)`'tir; bu, Babil yönteminin tanıdık formülüdür. Örnek 3'te bu iz tablosunu el ile hesaplayacağız. Burada önce programın sonucunu görelim:

Newton'un her adımda Hessian'ı tersine çevirmesi büyük boyutta pahalıdır: `d` boyutlu bir problemde `O(d³)` maliyet vardır, ve Hessian'ı saklamak `O(d²)` bellek ister. Milyonlarca parametreli bir sinir ağında bu imkânsızdır. Bu yüzden ML'de Newton doğrudan kullanılmaz; ama kavramı, BFGS ve benzeri "yarı-Newton" yöntemlerin temelidir (50.12).

Bir uyarı da var: Newton, Hessian pozitif tanımlı değilse yanlış yöne gidebilir. Eyer noktasının yakınında Hessian'ın bir özdeğeri negatifse Newton adımı bir maksimuma doğru gider. Bu yüzden pratik uygulamalarda Hessian düzeltilir ya da bir çizgi araması eklenir.

Programın başı: test fonksiyonları için `lm` ve Newton'un kullandığı küçük araçlar. `F(x) = x³/3 − 2x` fonksiyonunun gradyanı ve Hessian'ı tanımlanır ve `√2` için Newton ile gradyan inişi karşılaştırılır.

```python
# -*- coding: utf-8 -*-
# SGD gurultusu, Newton karesel yakinsama, LM, cizgi aramasi, BFGS.
import csv
import numpy as np
from scipy.optimize import minimize, least_squares
from b50_core import rosen, rosen_g

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"

# ---- 2) Newton (karesel): F(x) = x^3/3 - 2x, F' = x^2-2 ----
F1 = lambda x: x ** 3 / 3 - 2 * x
g1 = lambda x: x ** 2 - 2
h1 = lambda x: 2 * x
r = np.sqrt(2)
x = 1.0
satir = []
for k in range(7):
    satir.append(("newton", k, abs(x - r)))
    x = x - g1(x) / h1(x)
x = 1.0
for k in range(60):
    satir.append(("gd", k, abs(x - r)))
    x = x - 0.1 * g1(x)
print("\nNewton hatasi (sqrt2):")
for m, k, e in satir[:7]:
    print(k, "%.3e" % e)
print("GD(eta=0.1) adim 10,30,59 hata:",
      ["%.3e" % s[2] for s in satir
       if s[0] == "gd" and s[1] in (10, 30, 59)])
with open(VERI + "b50_newton_iz.csv", "w", newline="") as f:
    w_ = csv.writer(f)
    w_.writerow(["yontem", "adim", "hata"])
    for m, k, e in satir:
        w_.writerow([m, k, "%.6e" % e])
```

Rosenbrock için tam Hessian ile Newton. Hessian, gradyanın türevi olarak elle türetildi: `H = [[2 − 400y + 1200x², −400x], [−400x, 200]]`. Yakınsama adım sayısı ve son değer yazdırılır.

```python
# ---- 3) Newton, Rosenbrock (tam Hessian) ----
def ros_h(p):
    x, y_ = p
    return np.array([[2 - 400 * y_ + 1200 * x * x, -400 * x],
                     [-400 * x, 200.0]])

p = np.array([-1.2, 1.0])
for k in range(100):
    gr = rosen_g(p)
    if np.linalg.norm(gr) < 1e-10:
        break
    p = p - np.linalg.solve(ros_h(p), gr)
print("\nNewton Rosenbrock: adim=%d  x=%s  f=%.3e" % (k, p, rosen(p)))

# ---- 4) Gauss-Newton / Levenberg-Marquardt: us(t) = a e^{bt} ----
rng2 = np.random.default_rng(1)
t = np.linspace(0, 4, 30)
yd = 2.0 * np.exp(-0.7 * t) + 0.02 * rng2.standard_normal(30)

def artik(th):
    return th[0] * np.exp(th[1] * t) - yd

def jac(th):
    e = np.exp(th[1] * t)
    return np.column_stack([e, th[0] * t * e])
```

Levenberg–Marquardt (LM) eğri uydurma. Model `a e^{bt}`dir; gürültülü veri 30 noktada üretilir. Her adımda `(JᵀJ + λI)` sistemi çözülür; maliyet azalırsa `λ` küçülür, azalmazsa büyür. SciPy'nin `least_squares` çağrısı karşılaştırma için kullanılır.

```python
def lm(th, adim=50):
    th = np.asarray(th, float).copy()
    lam = 1e-3
    c = 0.5 * np.sum(artik(th) ** 2)
    for k in range(adim):
        R, J = artik(th), jac(th)
        A = J.T @ J
        dlt = -np.linalg.solve(A + lam * np.eye(2), J.T @ R)
        yeni = th + dlt
        cy = 0.5 * np.sum(artik(yeni) ** 2)
        if cy < c:
            th, c, lam = yeni, cy, lam / 3
        else:
            lam *= 2
        if np.linalg.norm(dlt) < 1e-10:
            break
    return th, c, k

th, c, k = lm([1.0, 0.0])
print("\nLM: a=%.4f b=%.4f maliyet=%.6f adim=%d"
      % (th[0], th[1], c, k))
sc = least_squares(artik, [1.0, 0.0], jac=jac, method="lm")
print("scipy lm: a=%.4f b=%.4f maliyet=%.6f nfev=%d"
      % (sc.x[0], sc.x[1], sc.cost, sc.nfev))
```

Newton sqrt2 için hata 0,41'den 2·10⁻¹⁶'ya iner. `k = 3`'ten sonra hata her adımda kabaca karesine iner: 2·10⁻⁶, 1,6·10⁻¹², makine sınırı. Gradyan inişi aynı problemi 59 adımda yalnızca 1,6·10⁻⁹'a indirir. Rosenbrock'ta tam Hessian ile Newton yalnızca 7 adımda `(1, 1)`'e ulaşıyor (gradyan inişi 15068 adım). LM'nin sonucu SciPy ile aynı çıkıyor ve 6 değerlendirmede yakınsıyor.

```term
$ python b50_deney3b.py

Newton hatasi (sqrt2):
0 4.142e-01
1 8.579e-02
2 2.453e-03
3 2.124e-06
4 1.595e-12
5 0.000e+00
6 2.220e-16
GD(eta=0.1) adim 10,30,59 hata: ['1.840e-02', '2.405e-05', '1.563e-09']

Newton Rosenbrock: adim=7  x=[1. 1.]  f=0.000e+00

LM: a=2.0109 b=-0.7057 maliyet=0.003928 adim=6
scipy lm: a=2.0109 b=-0.7057 maliyet=0.003928 nfev=6
```

![Şekil 50.7: F(x) = x³/3 − 2x üzerinde √2'ye yakınsama. Newton'un hatası her adımda karesel küçülür; gradyan inişi ise sabit oranla doğrusal küçülür.](gorseller/b50_newton_karesel.png)

Şekil 50.7 bu farkı açıkça gösteriyor. Log ölçekte Newton'un eğrisi, altıncı adıma kadar neredeyse dik bir düşüş yapıp makine sınırında duruyor. Gradyan inişinin eğrisi ise düz bir çizgi: her adımda sabit bir oranla küçülüyor. Bu iki davranış arasındaki fark, "karesel" ve "doğrusal" yakınsama kavramlarının tam görsel karşılığıdır.

Şimdi **Levenberg–Marquardt** (LM) yöntemine bakalım. Bu yöntem, en küçük kareler problemleri için Newton'un bir uyarlamasıdır. Eğri uydurmada kayıp `½ Σ r_i(θ)²`'dir; burada `r_i`, modelin i. veri noktasındaki artığıdır. Gauss–Newton yaklaşımı, Hessian'ı `JᵀJ` ile yaklaşıklar (`J`, artıkların Jacobian matrisidir) ve adımı `δ = −(JᵀJ)⁻¹ Jᵀ r` ile verir. Bu yaklaşım, `J`'nin sütunları doğrusal bağımlıysa ya da başlangıç çok uzaksa kararsızdır. LM bunu bir **sönümleme** `λ` ile düzeltir: `δ = −(JᵀJ + λI)⁻¹ Jᵀ r`. `λ` büyükse adım küçük ve gradyan inişi gibi davranır; `λ` küçükse Gauss–Newton gibi davranır. Her adımda maliyet azalırsa `λ` küçültülür, azalmazsa büyütülür.

Bu yöntem kalibrasyonda çok kullanılır: bir sensörün ham çıkışını gerçek bir fiziksel büyüklükle ilişkilendiren modelin parametrelerini bulursun. Programda `a e^{bt}` modeli kullanıldı; LM, SciPy ile aynı parametrelere (`a = 2,0109`, `b = −0,7057`) yakınsıyor. Bu, algoritmanın doğru çalıştığını gösteren bağımsız bir kanıttır: iki farklı uygulama aynı yere varıyor.

## 50.12 Tek boyutlu arama ve yarı-Newton yöntemler

Çoğu optimizasyon algoritmasında her adımda iki karar verilir: hangi **yön**, ve o yönde ne kadar **adım**. Adım uzunluğunu bulmak için tek boyutlu bir arama yaparsın: `φ(t) = f(x_k − t ∇f(x_k))` fonksiyonunu `t ≥ 0` üzerinde minimize edersin. Bu tek boyutlu problemin çözümü hem basit hem de önemlidir.

**İkiye bölme** (bisection), `φ'(t)`'nin işaretini kullanır. `φ'(a) < 0` ve `φ'(b) > 0` ise minimum `[a, b]` içindedir; orta noktanın türevinin işaretine göre aralığın yarısını atarsın. Her adım aralığı yarıya indirir; `10⁻⁸` hassasiyet için bizim aralıkta 29 adım gerekti.

**Altın oran araması** (golden section search), tek tepeli (unimodal) bir fonksiyonun minimumunu türevsiz bulur. Bölüm 14'te gördüğümüz **ternary search** aralığı üçe böler ve iki iç nokta kullanır. Her adımda aralık yaklaşık `2/3`'e iner ve her adımda iki yeni değerlendirme yapılır. Altın oran araması, iç noktaları altın oran `φ = (√5 − 1)/2 ≈ 0,618` konumunda seçerek bir değerlendirmeyi yeniden kullanır: aralık `0,618`'e iner ve her adımda yalnızca bir yeni değerlendirme gerekir. Bu, aynı hassasiyet için değerlendirme sayısını yaklaşık yarıya indirir.

**Geri izlemeli çizgi araması** (backtracking line search), tam minimumu aramak yerine yeterince iyi bir adım bulur. **Armijo koşulu** şöyledir:

    f(x − t ∇f) ≤ f(x) − c · t · ‖∇f‖²        (c ∈ (0, 1), tipik 10⁻⁴)

`t = 1`'den başlarsın; koşul sağlanmıyorsa `t`'yi bir `ρ` çarpanıyla (tipik `0,5`) küçültürsün. Bu koşul, adımın fonksiyonu gerçekten azalttığını ve azalmanın gradyan büyüklüğüyle orantılı olduğunu garanti eder. Bölüm 15'teki geri izleme (backtracking) ile aynı fikir ama bu kez bir çözüm ağacında değil, bir adım uzunluğu üzerinde çalışır.

Aşağıdaki program üç tek boyutlu aramayı ve Armijo'lu en dik iniş ile SciPy'nin BFGS ve L-BFGS-B yöntemlerini karşılaştırır. BFGS, Hessian'ı gradyan farklarından adım adım tahmin eden bir yarı-Newton yöntemidir (genel bilgi): tam Hessian hesaplamadan Newton'a benzer hızda yakınsar. L-BFGS ise Hessian'ı saklamadan yalnızca son birkaç gradyan farkını tutar; bu sayede büyük problemlerde de kullanılabilir.

Programın başı: `bisect_turev` ikiye bölme ile `f' = x³ − 1`in kökünü arar; `G` tek tepeli bir test fonksiyonudur. Ternary ve altın oran aramalarının değerlendirme sayısını karşılaştırmak için aynı aralık kullanılır.

```python
# -*- coding: utf-8 -*-
# SGD gurultusu, Newton karesel yakinsama, LM, cizgi aramasi, BFGS.
import csv
import numpy as np
from scipy.optimize import minimize, least_squares
from b50_core import rosen, rosen_g

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"

# ---- 5) Tek boyutlu arama: ikiye bolme, altin oran, Armijo ----
def bisect_turev(dF, a, b, tol=1e-8):
    cnt = 0
    while b - a > tol:
        m = 0.5 * (a + b)
        cnt += 1
        if dF(m) > 0:
            b = m
        else:
            a = m
    return 0.5 * (a + b), cnt

dF = lambda x: x ** 3 - 1.0
xb, cnt = bisect_turev(dF, 0.0, 3.0)
print("\nBisection (f'=x^3-1): x=%.8f  f' cagrisi=%d" % (xb, cnt))

G = lambda x: (x - 1.3) ** 4 + (x - 1.3) ** 2
```

Altın oran (`altin`) ve ternary (`uclu`) arama. Altın oran yalnızca bir yeni değerlendirme ister, çünkü iç noktalardan biri her adımda yeniden kullanılır. Ternary her adımda iki yeni değerlendirme yapar.

```python
def altin(f, a, b, tol=1e-6):
    phi = (np.sqrt(5) - 1) / 2
    c_ = b - phi * (b - a)
    d_ = a + phi * (b - a)
    fc, fd = f(c_), f(d_)
    ev = 2
    while b - a > tol:
        if fc < fd:
            b, d_, fd = d_, c_, fc
            c_ = b - phi * (b - a)
            fc = f(c_)
        else:
            a, c_, fc = c_, d_, fd
            d_ = a + phi * (b - a)
            fd = f(d_)
        ev += 1
    return 0.5 * (a + b), ev

def uclu(f, a, b, tol=1e-6):
    ev = 0
    while b - a > tol:
        m1 = a + (b - a) / 3
        m2 = b - (b - a) / 3
        ev += 2
        if f(m1) < f(m2):
            b = m2
        else:
            a = m1
    return 0.5 * (a + b), ev

xa, ea = altin(G, -2, 4)
xu, eu = uclu(G, -2, 4)
print("Altin oran: x=%.6f degerlendirme=%d" % (xa, ea))
print("Ucluk (ternary): x=%.6f degerlendirme=%d" % (xu, eu))
```

Armijo koşullu en dik iniş (`armijo_gd`) ve SciPy'nin BFGS ile L-BFGS-B çağrıları. `ev` sayacı yalnızca `f`'nin çağrılarını sayar; gradyan çağrıları karşılaştırmaya dahil değildir.

```python
def armijo_gd(f, g, x0, n=5000, c=1e-4, rho=0.5):
    x = np.asarray(x0, float).copy()
    ev = 0
    for k in range(n):
        gr = g(x)
        fx = f(x)
        ev += 1
        if np.linalg.norm(gr) < 1e-8:
            break
        t = 1.0
        while True:
            ev += 1
            if f(x - t * gr) <= fx - c * t * gr @ gr:
                break
            t *= rho
        x = x - t * gr
    return x, k, ev

xa_, ka, eva = armijo_gd(rosen, rosen_g, [-1.2, 1.0])
print("\nArmijo GD (Rosenbrock): adim=%d f=%.3e f-cagrisi=%d"
      % (ka, rosen(xa_), eva))

# ---- 6) BFGS / L-BFGS-B (scipy) ----
for yontem in ("BFGS", "L-BFGS-B"):
    s = minimize(rosen, [-1.2, 1.0], jac=rosen_g, method=yontem)
    print("%-9s x=%s f=%.3e nit=%d nfev=%d"
          % (yontem, np.round(s.x, 6), s.fun, s.nit, s.nfev))
```

Altın oran 35 değerlendirmede `1,3`'e ulaşıyor; ternary aynı doğruluğa 78 değerlendirmeyle ulaşıyor. Armijo'lu en dik iniş Rosenbrock'ta 5000 iterasyon sınırına kadar çalışıyor ve yalnızca `9·10⁻⁷`'ye iniyor, 54587 `f` çağrısıyla. BFGS ise 32 iterasyonda `10⁻¹⁵` düzeyinde doğruluğa ulaşıyor (39 `f` çağrısı).

```term
$ python b50_deney3c.py

Bisection (f'=x^3-1): x=1.00000000  f' cagrisi=29
Altin oran: x=1.300000 degerlendirme=35
Ucluk (ternary): x=1.300000 degerlendirme=78

Armijo GD (Rosenbrock): adim=4999 f=9.105e-07 f-cagrisi=54587
BFGS      x=[1. 1.] f=2.535e-15 nit=32 nfev=39
L-BFGS-B  x=[0.999999 0.999998] f=2.808e-12 nit=36 nfev=44
```

Bu sonuçlar, çizgi aramasının en dik inişi ne kadar iyileştirebildiğini gösterir ama tek başına yetmediğini de öğretir. Armijo'lu en dik iniş, her adımda yeterli azalmayı garanti eder, fakat yönü yine gradyandan alır; Rosenbrock'un kıvrımlı vadisinde bu yön kötüdür. BFGS ise yönü de Hessian tahminiyle düzeltir ve 32 adımda çözer. Bu fark, yarı-Newton yöntemlerin pratik değerini açıkça ortaya koyar: onlar ikinci dereceden bilgiyi, Hessian'ı açıkça hesaplamadan kullanır.

Pratik bir kural: küçük ve orta ölçekli, gürültüsüz problemlerde (ör. bir kalibrasyon ya da küçük bir eğri uydurma) BFGS veya L-BFGS, kolay bir seçimdir. Derin öğrenmede ise gürültülü mini-batch gradyanları nedeniyle Armijo gibi çizgi aramaları çoğunlukla kullanılmaz; yerine Adam gibi sabit ya da takvimli öğrenme oranları tercih edilir. Bu, yöntemin yanlışlığı değil, gürültünün çizgi aramasının varsayımını bozmasının sonucudur.

## 50.13 Kısıtlı optimizasyon: Lagrange, KKT ve ceza yöntemleri

Gerçek mühendislik problemleri nadiren kısıtsızdır. Bir İHA'nın hızı ile bir kaynağın tahsisi bir bütçeye bağlıdır; bir kazanç negatif olamaz; bir açı bir aralıkta kalmalıdır. Kısıtlı optimizasyonun temel aracı **Lagrange çarpanlarıdır** ve geometrik anlamı çok güzeldir.

Eşitlik kısıtlı bir problem `min f(x)` öyle ki `g(x) = 0` olsun. Çözüm noktasında `f`'nin seviye eğrisi ile kısıt eğrisi **teğet** olmak zorundadır. Neden? Eğer teğet değilsek, kısıt boyunca bir yönde hâlâ `f`'yi azaltabiliriz; bu da çözümün optimum olmadığı anlamına gelir. Teğetlik, iki gradyanın paralel olması demektir:

    ∇f(x*) = λ ∇g(x*)

Bu denklem, `λ` adı verilen **Lagrange çarpanı** ile birlikte çözülür. Bunu daha pratik olarak `L(x, λ) = f(x) − λ g(x)` fonksiyonunun kritik noktası olarak yazarız: `∇_x L = 0` ve `∇_λ L = 0` (ikincisi kısıtın kendisidir).

**Örnek 2**'de bu yöntemi ayrıntılı çözeceğiz; burada kısa bir uygulama yapalım. Bir İHA'nın sabit çevresi 20 metre olan dikdörtgen bir kanat paneli var. Alanı en büyük yapmak istiyoruz. `f = xy`, kısıt `2x + 2y = 20`. Lagrange: `∇f = (y, x)`, `∇g = (2, 2)` ve paralellik `y = x` verir; `x = y = 5`, alan `25`. Çarpan `λ = y/2 = 2,5` olur ve bu, kısıtın bir birimlik gevşemesinin alanı yaklaşık `2,5` kadar artıracağı anlamına gelir. Bu yorum tam olarak çarpanın ekonomik anlamıdır: **gölge fiyat**.

Şekil 50.8 bu teğetliği gösteriyor. Mavi eğriler `xy = sabit` alan seviyeleridir. Kırmızı doğru kısıttır. Alan, doğruya değdiği noktada (5, 5) en büyüktür; orada seviye eğrisinin gradyanı ile kısıtın gradyanı aynı yöne bakar.

![Şekil 50.8: Sabit çevrede en büyük alan. Alan seviye eğrileri (mavi) kısıt doğrusuna (kırmızı) (5, 5) noktasında teğet; orada ∇f ve ∇g paraleldir.](gorseller/b50_lagrange.png)

**Eşitsizlik kısıtları** için Lagrange yetmez; bunun yerine **KKT koşulları** (Karush–Kuhn–Tucker) kullanılır. `min f(x)` öyle ki `h(x) ≤ 0` olsun. KKT koşulları üç parçadır: (1) durağanlık `∇f + μ ∇h = 0`; (2) primal uygunluk `h(x) ≤ 0`; (3) dual uygunluk `μ ≥ 0`. Ek olarak **tamamlayıcı gevşeklik** (complementary slackness) `μ h(x) = 0` koşulu vardır. Bu son koşulun sezgisi çok önemlidir: ya kısıt aktiftir (`h = 0`) ve çarpan sıfır olmayabilir, ya kısıt pasiftir (`h < 0`) ve çarpan sıfırdır. Yani pasif bir kısıt çözümü etkilemez.

Bunu iki örnekle görelim. `min (x − 3)² + (y − 2)²` problemini `x + y ≤ 4` kısıtıyla çözersek, en yakın nokta `(3, 2)`'nin doğruya izdüşümüdür: `(2,5; 1,5)`. Orada `μ = 1` çıkar ve kısıt aktiftir. Kısıtı `x + y ≤ 6` yaparsak, `(3, 2)` zaten uygundur (`3 + 2 = 5 ≤ 6`); kısıt pasiftir ve `μ = 0` olur. Programda ikisini de SciPy ile çözüp KKT artıklarını (durağanlık) kontrol ediyoruz.

**Ceza yöntemi** (penalty), kısıtı ihlal ettiğinde büyük bir ceza ekleyerek kısıtsız problemi çözer: `F_ρ(x) = f(x) + ρ max(0, g(x))²`. `ρ` büyüdükçe çözüm kısıta yaklaşır ama hiçbir zaman tam ona ulaşmaz; bu yüzden ihlal `ρ` ile ters orantılı olarak küçülür. Basit bir örnekte `min x²` öyle ki `x ≥ 1` için `F_ρ(x) = x² + ρ max(0, 1 − x)²` ve türevini sıfır yapınca `x = ρ/(1 + ρ)` çıkar. `ρ` büyüdükçe `x` 1'e yaklaşır ama asla eşit olmaz.

**Bariyer yöntemi** (barrier) tersini yapar: kısıta yaklaşırken sonsuz duvar gibi davranan bir terim ekler. `F_μ(x) = f(x) − μ ln(x − 1)` için stasyonerlik `2x² − 2x − μ = 0` verir, yani `x = (1 + √(1 + 2μ))/2`. `μ` sıfıra giderken çözüm kısıta içeriden yaklaşır. Bariyer yöntemi, iç nokta yöntemlerinin (interior point) temelidir; LP ve konik programlamada standart bir yaklaşımdır (genel bilgi).

**Projeksiyonlu gradyan** en basit kısıt türüdür: `x` bir kutu içinde kalmalıdır (`a ≤ x ≤ b`). Her gradyan adımından sonra noktayı kutuya **izdüşürürsün** (clip). Bu, kutu konveks olduğu için geçerlidir ve kutunun dışına düşen noktaları kutunun en yakın noktasına çeker.

Programın başı: SciPy SLSQP ile sabit çevreli dikdörtgen ve bütçe kısıtı çözülür; her birinin analitik karşılığı yanında yazılır. `kkt_kontrol` fonksiyonu, bir eşitsizlik kısıtının aktif ya da pasif olduğunu ve çarpanın değerini raporlar.

```python
# -*- coding: utf-8 -*-
# Kisitli optimizasyon: Lagrange, KKT, projeksiyon, ceza, bariyer.
import numpy as np
from scipy.optimize import minimize, minimize_scalar, linprog

# ---- 1) Sabit cevreli dikdortgen: max xy, 2x+2y=20 ----
r = minimize(lambda p: -p[0] * p[1], [2.0, 8.0], method="SLSQP",
             constraints=[{"type": "eq",
                           "fun": lambda p: 2 * p[0] + 2 * p[1]
                           - 20}])
print("dikdortgen (SLSQP): x=%.5f y=%.5f alan=%.5f"
      % (r.x[0], r.x[1], -r.fun))
print("Lagrange analitik: x=y=5, lambda=x/2=2.5")

# ---- 2) Butce: max 3 ln x + ln y, 2x + y = 12 ----
r = minimize(lambda p: -(3 * np.log(p[0]) + np.log(p[1])), [3.0, 4.0],
             method="SLSQP",
             constraints=[{"type": "eq",
                           "fun": lambda p: 2 * p[0] + p[1] - 12}])
print("\nbutce (SLSQP): x=%.5f y=%.5f f=%.5f"
      % (r.x[0], r.x[1], -r.fun))
print("Lagrange analitik: x=4.5, y=3, lambda=1/3, f=%.5f"
      % (3 * np.log(4.5) + np.log(3)))

# ---- 3) KKT: min (x-3)^2+(y-2)^2, x+y<=4 (aktif), x+y<=6 ----
def kkt_kontrol(c, sinir):
    cons = [{"type": "ineq", "fun": lambda p: sinir - p[0] - p[1]}]
    r = minimize(lambda p: (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2,
                 [0.0, 0.0], method="SLSQP", constraints=cons)
    x, y = r.x
    grad = np.array([2 * (x - c[0]), 2 * (y - c[1])])
    g_val = sinir - x - y
    mu = max(0.0, -(grad @ np.array([1.0, 1.0])) / 2.0)
    kalan = np.round(grad + mu * np.array([1, 1]), 4) + 0.0
    print("x=(%.4f, %.4f) g=%.4f mu=%.4f"
          % (x, y, g_val, mu))
    print("  KKT kalani: %s" % kalan)
```

KKT örnekleri (aktif ve pasif kısıt), projeksiyonlu gradyan (kutu) ve ceza ile bariyer yöntemlerinin yakınsaması. Ceza tablosunda `x(ρ)` sayısal olarak bulunur ve `ρ/(1 + ρ)` ile karşılaştırılır; bariyer tablosunda `μ` küçüldükçe çözümün `1`'e yaklaşması izlenir.

```python
print("\nKKT aktif (sinir 4):", end=" ")
kkt_kontrol((3.0, 2.0), 4.0)
print("KKT pasif (sinir 6):", end=" ")
kkt_kontrol((3.0, 2.0), 6.0)

# ---- 4) Projeksiyonlu gradyan: kutu [0,1]^2 ----
g = lambda p: np.array([2 * (p[0] - 2), 2 * (p[1] + 1)])
p = np.array([0.5, 0.5])
for k in range(200):
    p = np.clip(p - 0.25 * g(p), 0.0, 1.0)
print("\nproj. GD kutu: x=%s  adim=200" % np.round(p, 6))

# ---- 5) Ceza ve bariyer: min x^2, x>=1 ----
print("\nCeza yontemi  rho   x(rho)      x=rho/(1+rho)   ihlal 1-x")
for rho in (1.0, 10.0, 100.0, 1000.0):
    F = lambda x, rho=rho: x * x + rho * max(0.0, 1 - x) ** 2
    s = minimize_scalar(F, bounds=(0.0, 2.0), method="bounded",
                        options={"xatol": 1e-12})
    print("            %6.0f  %.8f  %.8f   %.2e"
          % (rho, s.x, rho / (1 + rho), 1 - s.x))

print("\nBariyer       mu    x(mu)       (1+sqrt(1+2mu))/2")
for mu in (1.0, 0.1, 0.01, 0.0001):
    F = lambda x, mu=mu: x * x - mu * np.log(x - 1.0)
    s = minimize_scalar(F, bounds=(1.0 + 1e-12, 10.0),
                        method="bounded", options={"xatol": 1e-12})
    print("            %7.4f  %.8f  %.8f"
          % (mu, s.x, (1 + np.sqrt(1 + 2 * mu)) / 2))
```

Dikdörtgen `5 × 5`, alan `25`. Bütçe problemi `x = 4,5`, `y = 3`'e yaklaşıyor ve SciPy değeri analitik `5,61084` ile aynı. Aktif KKT örneğinde çözüm `(2,5; 1,5)`, çarpan `μ = 1`; pasif örnekte `(3, 2)`, `μ = 0`. Kutu problemi `(1, 0)`'a yakınsıyor. Ceza ve bariyer tabloları sayısal çözümün kapalı formla eşleştiğini gösteriyor.

```term
$ python b50_deney4a.py
dikdortgen (SLSQP): x=5.00000 y=5.00000 alan=25.00000
Lagrange analitik: x=y=5, lambda=x/2=2.5

butce (SLSQP): x=4.49989 y=3.00021 f=5.61084
Lagrange analitik: x=4.5, y=3, lambda=1/3, f=5.61084

KKT aktif (sinir 4): x=(2.5000, 1.5000) g=-0.0000 mu=1.0000
  KKT kalani: [0. 0.]
KKT pasif (sinir 6): x=(3.0000, 2.0000) g=1.0000 mu=0.0000
  KKT kalani: [0. 0.]

proj. GD kutu: x=[1. 0.]  adim=200

Ceza yontemi  rho   x(rho)      x=rho/(1+rho)   ihlal 1-x
                 1  0.50000000  0.50000000   5.00e-01
                10  0.90909091  0.90909091   9.09e-02
               100  0.99009901  0.99009901   9.90e-03
              1000  0.99900100  0.99900100   9.99e-04

Bariyer       mu    x(mu)       (1+sqrt(1+2mu))/2
             1.0000  1.36602540  1.36602540
             0.1000  1.04772255  1.04772256
             0.0100  1.00497524  1.00497525
             0.0001  1.00005000  1.00005000
```

Dikkat edilmesi gereken şey, ceza ve bariyerin **parametreye duyarlı** olmasıdır. `ρ` çok büyük seçilirse problem kötü koşullu hâle gelir ve gradyan inişi yavaşlar; `μ` çok hızlı küçülürse bariyer yöntemi sayısal olarak kararsızlaşır. Gerçek çözücüler bu nedenle parametreyi kademeli artırır ya da küçültür ve her seferinde bir öncekinin çözümünü başlangıç olarak kullanır.

## 50.14 Doğrusal programlama ve tamsayı programlama

Amaç ve kısıtlar hepsi doğrusal ise problem bir **doğrusal programlamadır** (linear programming, LP). Standart biçimi şöyledir:

    max cᵀx   öyle ki   A x ≤ b,   x ≥ 0

LP'nin en önemli özelliği çözümünün bir **köşe** (vertex) olmasıdır. Uygun bölge, kısıtların kesişimiyle oluşan bir çokyüzlüdür (ya da yüksek boyutta bir politop). Doğrusal bir amaç fonksiyonunun maksimumu, bu çokyüzlünün bir köşesinde alınır: çünkü amaç seviye çizgisi köşeye ulaşana kadar ilerler. Bu gerçek, LP'yi çözmenin temelidir: yalnızca köşeleri aramak yeterlidir.

**Simpleks yöntemi** (Dantzig, 1947; genel bilgi), bu fikri uygular: bir köşeden başlar, amacı artıran komşu bir köşeye geçer, ve amacı artıramayacağı bir köşeye ulaşınca durur. Her adım bir köşeden komşusuna geçer; kötü durumda üstel sayıda köşe olabilir ama pratikte hızlıdır. Modern çözücüler (ör. SciPy'nin HiGHS'ı) simpleks ya da iç nokta yöntemi kullanır.

Küçük bir örnekle görelim: `max 3x + 2y` öyle ki `x + y ≤ 4`, `x + 3y ≤ 6`, `x, y ≥ 0`. Uygun bölgenin köşeleri `(0,0)`, `(4,0)`, `(3,1)` ve `(0,2)`'dir. Amaç bu köşelerde sırasıyla `0`, `12`, `11`, `4` verir; optimum `(4, 0)`'da `12`'dir. Aşağıdaki program köşeleri **köşe sayımıyla** (her iki kısıtın kesişimini çözüp uygunluğu kontrol ederek) bulur ve sonra SciPy'nin HiGHS çözücüsüyle doğrular.

**Dualite** (duality), her LP'ye karşılık bir ikinci LP olduğunu söyler. Yukarıdaki problemin dual'i `min 4u + 6v` öyle ki `u + v ≥ 3`, `u + 3v ≥ 2`, `u, v ≥ 0`'dır. Zayıf dualite, her uygun dual çözümün değerinin herhangi bir primal uygun çözümün değerinden büyük ya da eşit olduğunu söyler; güçlü dualite ise optimum değerlerin eşit olduğunu garanti eder. Dual değişkenler, primal kısıtların gölge fiyatlarıdır: `u = 3`, birinci kaynağın bir birim artışının amacı üç birim artıracağı anlamına gelir. Programda bunu ayrıca doğrularız: dual optimum da `12`'dir.

**Tamsayı programlama** (integer programming), değişkenlerin tamsayı olmasını ister. Bu küçük bir değişiklik gibi görünür ama problemi NP-zor yapar (Bölüm 16'da gördüğümüz 0/1 sırt çantasının karar sürümü de NP-tamdır). Yaygın çözüm **dal-sınır** (branch and bound) yöntemidir: problemi tamsayı olmayan LP gevşemesiyle başlatır, LP çözümü bir tamsayı değilse bir değişkene göre iki alt probleme dallanır ve her dalın değerinin bir üst sınırını hesaplayarak budama yapar. Bu, Bölüm 15'teki geri izleme ağacına bir sınır eklenmesi gibidir: sınır, o dalda daha iyi bir çözüm bulunamayacağını kanıtlarsa dal kesilir.

Sırt çantası için bu sınır, değeri kapasite ile eşitleyen **kesirli sırt çantası** çözümüdür: eşyaları değer/ağırlık oranına göre sıralar ve kapasiteyi kesirli olarak doldurursun. Bu, tamsayı çözümün üst sınırıdır (LP gevşemesi). Aşağıdaki program bu sınırı kullanan bir dal-sınır çözücüsü yazar ve sonucunu Bölüm 16'daki DP ile karşılaştırır. Her iki yöntem de aynı tamsayı optimumunu bulmalı, ama dal-sınır kaç düğüm gezdiğini ölçebiliriz.

Programın başı: LP ve tamsayı problemleri için bir ön hazırlık. `A` ve `b` standart biçimde kısıtları taşır; köşe sayımı, sınırlı kısıt kümesi üzerinde çalışır.

```python
# -*- coding: utf-8 -*-
# Kisitli optimizasyon: LP ve dal-sinir (tamsayi).
import numpy as np
from scipy.optimize import minimize, minimize_scalar, linprog

# ---- 6) Dogrusal programlama: max 3x+2y, kisitlar ----
c = np.array([3.0, 2.0])
A = np.array([[1.0, 1.0], [1.0, 3.0], [-1.0, 0.0], [0.0, -1.0]])
b = np.array([4.0, 6.0, 0.0, 0.0])
kose = []
for i in range(4):
    for j in range(i + 1, 4):
        M = A[[i, j]]
        if abs(np.linalg.det(M)) < 1e-12:
            continue
        v = np.linalg.solve(M, b[[i, j]])
        if np.all(A @ v <= b + 1e-9):
            kose.append((float(round(v[0], 6)) + 0.0,
                         float(round(v[1], 6)) + 0.0, float(c @ v)))
kose = sorted(set(kose), key=lambda t: -t[2])
print("\nkose noktalar (x, y, 3x+2y):")
for t_ in kose:
    print("  ", t_)
lp = linprog(-c, A_ub=A[:2], b_ub=b[:2], bounds=[(0, None)] * 2,
             method="highs")
print("linprog: x=%s  amac=%.4f" % (np.round(lp.x, 6), -lp.fun))
dl = linprog(b[:2], A_ub=-A[:2].T, b_ub=-c, bounds=[(0, None)] * 2,
             method="highs")
print("dual: u,v=%s  dual amac=%.4f"
      % (np.round(dl.x, 6), dl.fun))
```

LP çözümü: iki kısıtın her kesişimi çözülür, uygunluk kontrol edilir ve köşeler amaca göre sıralanır. SciPy'nin `linprog` çağrısı (HiGHS) köşe sayımını doğrular; dual problem de ayrı bir `linprog` çağrısıyla çözülür.

```python
# ---- 7) Tam sayi: 0/1 sirt cantasi, dal-sinir, DP ----
def dal_sinir(w, v, cap):
    n = len(w)
    sira = sorted(range(n), key=lambda i: -v[i] / w[i])
    W = [w[i] for i in sira]
    V = [v[i] for i in sira]
    en = [0]
    dugum = [0]

    def sinir(i, kap, deg):
        s = deg
        for j in range(i, n):
            if W[j] <= kap:
                kap -= W[j]
                s += V[j]
            else:
                s += V[j] * kap / W[j]
                break
        return s

    def dfs(i, kap, deg):
        dugum[0] += 1
        if deg > en[0]:
            en[0] = deg
        if i == n or sinir(i, kap, deg) <= en[0]:
            return
        if W[i] <= kap:
            dfs(i + 1, kap - W[i], deg + V[i])
        dfs(i + 1, kap, deg)

    dfs(0, cap, 0)
    return en[0], dugum[0]
```

Dal-sınır çözücüsünün iskeleti. Sınır (`sinir`), kalan eşyaların kesirli sırt çantası değeridir. Her düğümde sınır, mevcut en iyi çözümden düşükse dal budanır. `dp` fonksiyonu Bölüm 16'daki 0/1 sırt çantası tablosudur ve doğrulama için kullanılır.

```python
def dp(w, v, cap):
    t = [0] * (cap + 1)
    for wi, vi in zip(w, v):
        for k in range(cap, wi - 1, -1):
            t[k] = max(t[k], t[k - wi] + vi)
    return t[cap]

rng = np.random.default_rng(2)
for n in (12, 20, 30):
    w = list(rng.integers(3, 30, n))
    v = list(rng.integers(5, 60, n))
    cap = int(sum(w) // 3)
    deg, nd = dal_sinir(w, v, cap)
    print("n=%2d kapasite=%3d  B&B=%d  DP=%d  dugum=%d"
          % (n, cap, deg, dp(w, v, cap), nd))
```

LP köşeleri `(4, 0)`'da `12` ile en iyi; `(3, 1)` `11`; `(0, 2)` `4`. SciPy `(4, 0)`'ı ve değeri `12` olarak bulur. Dual optimum `u = 3, v = 0` ile yine `12`'dir: güçlü dualitenin doğrulanması. Dal-sınır ile DP her üç örnekte de aynı optimumu veriyor; dal-sınır 12, 20 ve 30 eşya için sırasıyla 18, 35 ve 78 düğüm gezdi.

```term
$ python b50_deney4b.py

kose noktalar (x, y, 3x+2y):
   (4.0, 0.0, 12.0)
   (3.0, 1.0, 11.0)
   (0.0, 2.0, 4.0)
   (0.0, 0.0, 0.0)
linprog: x=[4. 0.]  amac=12.0000
dual: u,v=[3. 0.]  dual amac=12.0000
n=12 kapasite= 62  B&B=209  DP=209  dugum=18
n=20 kapasite=116  B&B=410  DP=410  dugum=35
n=30 kapasite=173  B&B=478  DP=478  dugum=78
```

Şekil 50.9, bu LP'nin uygun bölgesini ve amaç doğrularını gösteriyor. Uygun bölge dört köşeli bir çokyüzlü; amaç doğruları `z = 4`, `z = 11` ve `z = 12` seviyelerinde çizildi ve en yüksek seviye köşeden geçiyor.

![Şekil 50.9: Uygun bölge çokyüzlüsü ve köşe çözüm. Amaç doğrusu z = 12, (4, 0) köşesinden geçerek uygun bölgeye dokunur.](gorseller/b50_lp_bolge.png)

Bu sonuç, dal-sınırın gücünü gösterir ama sınırlarını da. Düğüm sayısı, sınırın ne kadar sıkı olduğuna bağlıdır: LP gevşemesi iyi bir üst sınır verdiğinde budama çok sayıda dalı keser. Kötü bir sınırda ise üstel sayıda düğüm gerekebilir. Bu yüzden gerçek çözücüler kesme düzlemleri (cutting planes) gibi tekniklerle sınırı sıkılaştırır. Burada ise yalnızca temel fikri görüyoruz.

Bu bölümde LP'yi bir **türevsiz** ya da **kombinatorik** yöntemle karşılaştırmak da ilginç: LP'de çözüm köşelerde olduğu için kombinatorik bir arama gibi düşünebiliriz; ama bu yalnızca doğrusal yapıya özgü bir kestirmedir. Doğrusal olmayan ve kombinatorik problemler için genel yöntemlere ihtiyaç var; bunları bir sonraki alt başlıkta ele alıyoruz.

## 50.15 Türevsiz ve kombinatorik yöntemler: tavlama, rastgele arama

Bazı problemlerde gradyan yoktur ya da anlamsızdır. Bir rotanın ziyaret sırası sürekli bir değişken değildir; bir ayarın iyi olup olmadığını yalnızca bir simülasyon ya da deneyle ölçebilirsin. Bu durumda **türevsiz** (derivative-free) yöntemlere başvurursun.

**Benzetimli tavlama** (simulated annealing), metal soğutmadan esinlenir. Mevcut çözümden rastgele bir komşu üretir; komşu daha iyiyse kabul eder; daha kötüyse de bir olasılıkla kabul eder: `P = exp(−Δ/T)`, burada `Δ` maliyet artışı ve `T` sıcaklıktır. Sıcaklık yüksekken kötü çözümler kolayca kabul edilir ve arama yerel minimumlardan kaçabilir; sıcaklık düştükçe yöntem bir iniş algoritmasına dönüşür. Bu, Bölüm 17'deki graf modellerine doğal bir uygulamadır: çözüm uzayı bir graftır ve komşuluk, bir kenardır.

Gezgin satıcı problemi (TSP), tavlamanın en bilinen uygulamasıdır. `n` şehri ziyaret eden en kısa kapalı turu bulmak NP-zordur (genel bilgi) ve `n!` olası turu vardır. Komşuluk olarak **2-opt** kullanacağız: bir turdaki iki kenarı kesip aradaki parçayı ters çeviririz. Bu hamle bir turdan diğerine geçmenin en yaygın yoludur.

Aşağıdaki programın ilk kısmı tavlamayı 9 şehirde (kesin optimumu bilinebilir: `8! = 40320` tur) beş tohumla dener ve kesin optimumu bulma oranını ölçer. İkinci kısım, 30 şehirde bir çalıştırma yapar ve soğutma takvimini `engine/veri/` altına yazar. Üçüncü kısım, türevsiz bir karşılaştırma olarak **rastgele arama** ile **ızgara arama**yı aynı bütçede (100 değerlendirme) Rastrigin üzerinde karşılaştırır.

Programın başı: mesafe matrisi ve tur maliyeti. Tur maliyeti, ardışık şehirler arasındaki mesafelerin toplamıdır; son şehirden ilk şehre dönüş dahildir.

```python
# -*- coding: utf-8 -*-
# Tavlama (TSP) ve rastgele arama.
import csv
import itertools
import numpy as np
from scipy.optimize import minimize, minimize_scalar

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"

# ---- 1) Tavlama: gezgin satici ----
def mesafe_matrisi(P):
    return np.sqrt(((P[:, None, :] - P[None, :, :]) ** 2).sum(-1))

def tur_maliyeti(D, tur):
    n = len(tur)
    return sum(D[tur[i], tur[(i + 1) % n]] for i in range(n))
```

Tavlama. Başlangıç turu rastgele, komşuluk 2-opt'tur (`tur[i:j+1]` ters çevrilir). Kabul kuralı Metropolis'tir: iyileşme her zaman, kötüleşme `exp(−Δ/T)` olasılıkla kabul edilir. Sıcaklık geometrik olarak `α` ile azalır. Kesin çözüm, 9 şehir için tüm permütasyonların denenmesiyle bulunur.

```python
def tavlama(D, T0=50.0, alfa=0.9995, adim=60000, seed=0):
    r = np.random.default_rng(seed)
    n = D.shape[0]
    tur = list(r.permutation(n))
    c = tur_maliyeti(D, tur)
    en_iyi, en_c = list(tur), c
    T = T0
    gecmis = []
    for k in range(adim):
        i, j = sorted(r.choice(n, 2, replace=False))
        yeni = tur[:i] + tur[i:j + 1][::-1] + tur[j + 1:]   # 2-opt
        cy = tur_maliyeti(D, yeni)
        if cy < c or r.random() < np.exp(-(cy - c) / T):
            tur, c = yeni, cy
            if c < en_c:
                en_iyi, en_c = list(tur), c
        T *= alfa
        if k % 500 == 0:
            gecmis.append((k, T, c))
    return en_iyi, en_c, gecmis

def kesin(D):
    n = D.shape[0]
    en = min(tur_maliyeti(D, (0,) + p)
             for p in itertools.permutations(range(1, n)))
    return en

ok = 0
for tohum in range(5):
    P = np.random.default_rng(10 + tohum).uniform(0, 100, (9, 2))
    D = mesafe_matrisi(P)
    _, sa_c, _ = tavlama(D, adim=20000, seed=tohum)
    kes = kesin(D)
    ok += int(abs(sa_c - kes) < 1e-9)
    print("tohum %d: SA=%.4f  kesin=%.4f" % (tohum, sa_c, kes))
print("9 sehir, 5 tohum: kesin optimumu bulan SA sayisi =", ok)
```

30 şehirli çalıştırma, soğutma takvimini CSV'ye yazar. Rastrigin için ızgara ile rastgele arama karşılaştırması: aynı 100 değerlendirme, 20 tohum.

```python
P = np.random.default_rng(3).uniform(0, 100, (30, 2))
D = mesafe_matrisi(P)
tur, c_sa, gec = tavlama(D, T0=50.0, alfa=0.9997, adim=120000, seed=1)
print("30 sehir: SA maliyeti=%.3f" % c_sa)
with open(VERI + "b50_tavlama.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["adim", "T", "maliyet"])
    for k, T, cc in gec:
        w.writerow([k, "%.6f" % T, "%.4f" % cc])

# ---- 2) Rastgele arama vs izgara (Rastrigin, 2B, 100 eval) ----
def rastrigin(x, y):
    return 20 + x * x + y * y - 10 * np.cos(2 * np.pi * x) \
        - 10 * np.cos(2 * np.pi * y)

izgara = np.linspace(-5.12, 5.12, 10)
en_izg = min(rastrigin(a, b) for a in izgara for b in izgara)
rs = []
for tohum in range(20):
    r = np.random.default_rng(tohum)
    p = r.uniform(-5.12, 5.12, (100, 2))
    rs.append(min(rastrigin(a, b) for a, b in p))
print("\nizgara (10x10) en iyi f=%.4f" % en_izg)
print("rastgele (100) en iyi f: ort=%.4f  en kotu=%.4f  en iyi=%.4f"
      % (np.mean(rs), np.max(rs), np.min(rs)))
```

Dokuz şehirde beş tohumun beşinde de tavlama kesin optimumu buluyor (`235,41` ile `315,27` arasındaki değerler). Otuz şehirde en iyi tur `460,77`. Rastrigin'de 10×10 ızgara en iyi `24,998` değerini buluyor: ızgara noktalarından hiçbiri orijine (küresel minimum, `f = 0`) yakın değil. Aynı bütçeyle rastgele arama 20 tohumun ortalamasında `5,58`, en iyi denemede `0,93` buluyor.

```term
$ python b50_deney5a.py
tohum 0: SA=286.1888  kesin=286.1888
tohum 1: SA=311.9198  kesin=311.9198
tohum 2: SA=310.2522  kesin=310.2522
tohum 3: SA=315.2664  kesin=315.2664
tohum 4: SA=235.4114  kesin=235.4114
9 sehir, 5 tohum: kesin optimumu bulan SA sayisi = 5
30 sehir: SA maliyeti=460.768

izgara (10x10) en iyi f=24.9979
rastgele (100) en iyi f: ort=5.5788  en kotu=10.5674  en iyi=0.9295
```

![Şekil 50.10: Benzetimli tavlamada sıcaklık (log ölçek) ve tur maliyeti. Yüksek sıcaklıkta maliyet dalgalanır; sıcaklık düştükçe maliyet yerleşir ve tur sabitlenir.](gorseller/b50_tavlama.png)

Şekil 50.10 tavlamanın iki yüzünü gösteriyor. Sol panelde sıcaklık, geometrik olarak düşüyor. Sağ panelde maliyet, başlangıçta yüksek sıcaklıkta sert dalgalanıyor (kötü turlar bile kabul ediliyor), sonra sıcaklık düştükçe dalgalanma kayboluyor ve maliyet bir değerde yerleşiyor. Bu yerleşme anı, yöntemin "soğumasıdır". Soğutma çok hızlı yapılırsa yöntem yerel bir minimumda kalır; çok yavaş yapılırsa gereksiz yere uzar. Bu dengeyi kuran `alfa` ve `T0` parametreleri, tavlamanın gerçek mühendisliğidir.

Rastgele arama ile ızgara arasındaki fark, hiperparametre aramasına doğrudan bir köprüdür (Bölüm 57). Izgara, her boyutta eşit aralıklı noktalar seçer; böylece her boyutta yalnızca birkaç farklı değer dener. Rastgele arama ise her boyutta bağımsız değerler seçer; önemli bir boyut azsa rastgele aramanın bu boyutta daha fazla farklı değer denediğini görürsün. Bu nedenle, etkisi az olan parametrelerin çoğu varsa rastgele arama genellikle daha verimlidir (Bergstra ve Bengio, 2012; genel bilgi). Burada gördüğümüz `24,998` ile `5,58` arasındaki fark, ızgara noktalarının orijine hizalanamamasının bir sonucudur; rastgele arama bu hizalanma şansızlığından etkilenmez.

**Genetik algoritmalar** (genel bilgi) bir popülasyon üzerinde çalışır: çözümler çaprazlanır, mutasyona uğrar ve uygunluğa göre seçilir. Tavlamanın tek bir çözümü takip etmesine karşılık, genetik algoritma geniş bir alanı aynı anda tarar. Ama bu genişlik maliyetlidir ve sonucu yakınsamanın kanıtlanmasını zorlaştırır. Bu bölümde yalnızca fikri tanıdık; uygulamada tavlama ve rastgele aramayla birlikte düşünmek, türevsiz problemlerde sık bir başlangıç noktasıdır.

## 50.16 Mühendislik uygulamaları: PID, İHA rotası ve sensör kalibrasyonu

Şimdi optimizasyon araçlarını üç mühendislik problemine uygulayalım. Her biri farklı bir ders öğretir: PID ayarı, türevsiz amaç fonksiyonu ile bir simülasyonun optimizasyonunu; İHA rotası, kısıtlı bir enerji problemini; sensör kalibrasyonu, en küçük kareler ve koşul sayısını.

**PID denetleyici**, bir çıkış `y`'yi bir referans `r`'ye getirmek için kontrol girdisi `u = Kp e + Ki ∫e dt + Kd de/dt` üretir; burada `e = r − y` hatadır. Kazançların (`Kp`, `Ki`, `Kd`) seçimi, yanıtın hızını ve salınımını belirler. Amaç fonksiyonu olarak tipik seçim **integral kare hata** (ISE) `∫ e² dt`'dir. Ama ISE tek başına çok büyük kontrol girdilerini teşvik eder: fiziksel bir eyleyici bunları veremez. Bu yüzden amaca bir **kontrol çabası** cezası eklemek gerçekçi bir yaklaşımdır: `J = ISE + ρ ∫ u² dt`.

Test sistemi birinci dereceden bir modeldir: `G(s) = K / (τ s + 1)`, `K = 2`, `τ = 1,5`. Simülasyon Euler yöntemiyle `dt = 0,01` adımında 8 saniye boyunca yapılır. Kazançlar Nelder–Mead (türevsiz bir simpleks yöntemi; genel bilgi) ile ayarlanır. Bu, bir simülasyonun çıktısını optimize ederken gradyana ihtiyaç duymadığımız tipik bir durumdur.

**İHA rotası** için enerji modeli basitleştirilmiş bir güç eğrisine dayanır: taşıma için sabit bir güç `P₀` ve hava direnci için hıza bağlı bir güç `k v³`. Mesafe `d` boyunca uçuş süresi `d/v`'dir; toplam enerji:

    E(v) = (P₀ + k v³)(d / v) = P₀ d / v + k d v²

Bu fonksiyon, `v* = (P₀ / (2k))^(1/3)` noktasında minimumdur (`E'(v) = −P₀ d / v² + 2 k d v = 0`). Ama bir kısıt daha var: görevin süresi `T_max` içinde bitmek zorunda, yani `d/v ≤ T_max`, buradan `v ≥ d / T_max`. Kısıtsız optimum bu kısıtı ihlal ederse, optimum kısıtın sınırındadır: kısıt **aktiftir**. Bu, 50.13'teki KKT mantığının somut bir örneğidir: amaç ile kısıt arasında bir denge yoktur, kısıt çözümü belirler.

**Sensör kalibrasyonu**, ham bir ADC okumasını bir fiziksel büyüklüğe (ör. sıcaklık) eşleyen katsayıları bulmaktır. Gerçek sensörler doğrusal olmayabilir; bu yüzden ikinci dereceden bir model `c₀ + c₁ T + c₂ T²` ile doğrusal modeli karşılaştırmak öğreticidir. Bu bir en küçük kareler problemidir: `A c ≈ y` ve çözüm `c = (AᵀA)⁻¹ Aᵀ y`. Bu normal denklemler Bölüm 48'in konusudur; burada yalnızca koşul sayısının etkisini ölçeceğiz. `T` değerleri 0 ile 100 arasında olduğunda, `T²` sütunu `10⁴` mertebesindedir ve `A`'nın sütunları çok farklı ölçeklerdedir. Bu, `κ(A)`'yı büyütür ve sayısal kararlılığı bozar.

Programın başı: PID simülasyonu. `sim_pid` birinci dereceden sistemi Euler adımıyla çözer; kontrol girdisi `±10` sınırına kırpılır ve ISE ile kontrol çabasının integralini birlikte döndürür. Kazançlar negatif olamaz; bu, amaç fonksiyonunda büyük bir ceza ile zorlanır.

```python
# -*- coding: utf-8 -*-
# PID kazanc ayari, IHA enerji, sensor kalibrasyonu.
import csv
import itertools
import numpy as np
from scipy.optimize import minimize, minimize_scalar

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"

# ---- 3) PID: G(s) = 2/(1.5s+1), ISE ile kazanc ayari ----
def sim_pid(kp, ki, kd, dt=0.01, T=8.0):
    K, tau = 2.0, 1.5
    y, integ, e_onceki = 0.0, 0.0, 0.0
    ise = 0.0
    cab = 0.0
    for _ in range(int(T / dt)):
        e = 1.0 - y
        integ += e * dt
        turev = (e - e_onceki) / dt
        u = np.clip(kp * e + ki * integ + kd * turev, -10.0, 10.0)
        e_onceki = e
        y += dt * (K * u - y) / tau
        ise += e * e * dt
        cab += u * u * dt
    return ise, cab

def maliyet(p):
    if np.any(np.asarray(p) < 0):
        return 1e6
    ise, cab = sim_pid(*p)
    return ise + 0.01 * cab
```

Nelder–Mead ile PID ayarı, İHA rotası için kısıtlı enerji minimizasyonu ve sensör kalibrasyonu. İHA kısmı, kısıt sınırında `v = 13,33` m/s'de yapılır; kalibrasyonda hem doğrusal hem ikinci dereceden model için en küçük kareler çözülür ve koşul sayıları yazdırılır.

```python
r0 = minimize(maliyet, [1.0, 0.5, 0.1], method="Nelder-Mead",
              options={"xatol": 1e-4, "fatol": 1e-6, "maxiter": 400})
kp, ki, kd = r0.x
print("\nPID (Nelder-Mead): Kp=%.4f Ki=%.4f Kd=%.4f J=%.5f"
      % (kp, ki, kd, r0.fun))
ise, cab = sim_pid(kp, ki, kd)
print("  ISE=%.5f  kontrol cabasi=%.3f" % (ise, cab))
ise, cab = sim_pid(1.0, 0.0, 0.0)
print("sadece P (Kp=1.0): ISE=%.5f  kontrol cabasi=%.3f" % (ise, cab))

# ---- 4) IHA rota enerjisi: E(v) = P0 d/v + k d v^2 ----
P0, kk, dd, Tmax = 50.0, 0.02, 2000.0, 150.0
E = lambda v: P0 * dd / v + kk * dd * v * v
v_ac = (P0 / (2 * kk)) ** (1 / 3)
v_min = dd / Tmax
r1 = minimize_scalar(E, bounds=(v_min, 40.0), method="bounded",
                     options={"xatol": 1e-10})
print("\nIHA: v*(kisitsiz)=%.4f m/s  v_min=%.4f m/s" % (v_ac, v_min))
print("IHA kisitli optimum: v=%.4f E=%.2f J (kisit aktif)"
      % (r1.x, r1.fun))
print("E(v*) kisitsiz = %.2f J (ihlal eder: T=%.1f s)"
      % (E(v_ac), dd / v_ac))

# ---- 5) Sensor kalibrasyonu: en kucuk kareler ----
rng4 = np.random.default_rng(4)
T_ = np.linspace(0, 100, 25)
ham = 120.0 + 3.1 * T_ + 0.004 * T_ ** 2 + rng4.normal(0, 0.5, 25)
A1 = np.column_stack([np.ones_like(T_), T_])
A2 = np.column_stack([np.ones_like(T_), T_, T_ ** 2])
c1 = np.linalg.lstsq(A1, ham, rcond=None)[0]
c2 = np.linalg.lstsq(A2, ham, rcond=None)[0]
print("\nkalibrasyon dogrusal: b=%.4f a=%.4f  RMS=%.4f"
      % (c1[0], c1[1], np.sqrt(np.mean((A1 @ c1 - ham) ** 2))))
print("kalibrasyon ikinci der.: c0=%.4f c1=%.4f c2=%.6f RMS=%.4f"
      % (c2[0], c2[1], c2[2], np.sqrt(np.mean((A2 @ c2 - ham) ** 2))))
print("kosul sayisi (A2): %.3e" % np.linalg.cond(A2))
A3 = np.column_stack([np.ones_like(T_), T_ / 100, (T_ / 100) ** 2])
print("olceklenmis (T/100) kosul sayisi: %.3e" % np.linalg.cond(A3))
```

PID ayarı `Kp = 12,41`, `Ki = 5,45`, `Kd = 0,21`; amaç `J = 0,103` (ISE `0,042`, kontrol çabası `6,13`). Yalnızca P (`Kp = 1`) ile ISE `1,22` ve kontrol çabası `1,22`: ayarlı denetleyici yanıtı çok daha hızlı yapıyor, ama bunun bedeli daha büyük kontrol girdisi. İHA için kısıtsız optimum `10,77 m/s`'dir ama bu hızda görev süresi `185,7 s` olur; `150 s` kısıtını ihlal eder. Kısıtlı optimum `13,33 m/s`, enerji `14611 J`. Kalibrasyonda doğrusal model RMS `3,30`, ikinci dereceden model `0,53` hata verir (gürültü `0,5`). Koşul sayısı ham T ile `1,28·10⁴`, `T/100` ile `21,3`.

```term
$ python b50_deney5b.py

PID (Nelder-Mead): Kp=12.4109 Ki=5.4477 Kd=0.2082 J=0.10339
  ISE=0.04213  kontrol cabasi=6.126
sadece P (Kp=1.0): ISE=1.22334  kontrol cabasi=1.223

IHA: v*(kisitsiz)=10.7722 m/s  v_min=13.3333 m/s
IHA kisitli optimum: v=13.3333 E=14611.11 J (kisit aktif)
E(v*) kisitsiz = 13924.77 J (ihlal eder: T=185.7 s)

kalibrasyon dogrusal: b=113.5608 a=3.5009  RMS=3.2950
kalibrasyon ikinci der.: c0=120.0079 c1=3.0973 c2=0.004036 RMS=0.5334
kosul sayisi (A2): 1.280e+04
olceklenmis (T/100) kosul sayisi: 2.126e+01
```

Üç sonuç özellikle önemli. Birincisi, PID kazanç ayarında Kd'nin küçük çıkmasıdır: bu model gürültüsüz bir birinci dereceden sistemdir ve türev terimi burada gerekli değildir; ölçüm gürültüsü olan gerçek bir sistemde Kd genellikle gürültüyü büyüttüğü için dikkatle seçilir. İkincisi, İHA kısıtlı çözümünün kısıtın sınırında olmasıdır: kısıtsız optimum hiçbir zaman uygun değildi. Üçüncüsü, kalibrasyonda ölçeklemenin koşul sayısını `600` kat azaltmasıdır. Bu, bir sayısal analiz dersinin en pratik sonucudur: model doğru olsa bile veri ölçeklenmezse çözüm güvenilmez olabilir.

## 50.17 ML köprüsü: kayıp, düzenlileştirme ve eyer noktaları

Bu bölümün başında söylediğimiz gibi, bir makine öğrenmesi modelinin eğitimi bir optimizasyon problemidir. Kayıp fonksiyonu `L(θ)` minimize edilir. Üstelik ML'de düzenlileştirme (regularization) de aynı çerçevededir: `min L(θ) + λ‖θ‖²` (L2 düzenlileştirme, ridge), yalnızca kayba bir ceza terimi ekler. Doğrusal regresyonda bu problemin kapalı formu `θ = (XᵀX + λI)⁻¹ Xᵀ y`'dir; burada `λI` terimi `XᵀX`'in koşul sayısını düzeltir. Bu, Bölüm 58'de tekrar karşımıza çıkacak ve kalibrasyondaki koşul sayısı sorununun ML'deki karşılığıdır. Aşırı parametreli sinir ağlarında ise kayıp yüzeyi çok sayıda eyer noktası içerir; gradyan inişinin bu noktalardan kaçabilmesi, konveks olmayan optimizasyonun sürpriz bir yüzüdür (genel bilgi). Bunu Bölüm 63 ve 64'te eğitim pratiğiyle birlikte göreceğiz.

## Çözümlü Örnekler

Bu dört örnek bölümün kavramlarını elle izlemeni hedefler. Her birinde önce kâğıt üstünde iz sürer, sonra sonucu bir programla doğrularsın. Aşağıdaki program dört örneğin sayısal izlerini üretir; elle hesapladığın tabloyu bunlarla karşılaştır.

Program, dört örneğin izlerini yazdırır. İlk kısım Örnek 1'in GD izini, ikinci kısım Örnek 2'nin dikdörtgen tablosunu üretir.

```python
# -*- coding: utf-8 -*-
# Cozumlu ornekler icin izler (elle yapilanla karsilastirma).
import numpy as np

print("Ornek 1: GD, f=x^2+10y^2, eta=0.08, x0=(1,1)")
x, y, eta = 1.0, 1.0, 0.08
for k in range(6):
    f = x * x + 10 * y * y
    print("k=%d x=%.4f y=%.4f gx=%.4f gy=%.4f f=%.4f"
          % (k, x, y, 2 * x, 20 * y, f))
    x, y = x - eta * 2 * x, y - eta * 20 * y

print("\nOrnek 2: dikdortgen, 2x+2y=20 (y=10-x)")
for x in range(1, 10):
    print("x=%d y=%d alan=%d" % (x, 10 - x, x * (10 - x)))

print("\nOrnek 3: Newton sqrt2, x0=1")
r = np.sqrt(2)
x = 1.0
for k in range(6):
    e = abs(x - r)
    dig = -np.log10(e) if e > 0 else float("inf")
    print("k=%d x=%.12f hata=%.3e dogru_basamak=%.2f"
          % (k, x, e, dig))
    x = x - (x * x - 2) / (2 * x)
```

Örnek 3'ün Newton izi ile Örnek 4'ün Adam izi. Adam kısmında iki güncelleme yan yana yazılır: biyas düzeltmeli ve düzeltmesiz adım. Bu karşılaştırma Örnek 4'ün ana sorusudur.

```python
print("\nOrnek 4: Adam, f=(t-3)^2, t0=0, eta=0.1")
b1, b2, eta, eps = 0.9, 0.999, 0.1, 1e-8
t, m, v = 0.0, 0.0, 0.0
for k in range(1, 4):
    g = 2 * (t - 3)
    m = b1 * m + (1 - b1) * g
    v = b2 * v + (1 - b2) * g * g
    mh = m / (1 - b1 ** k)
    vh = v / (1 - b2 ** k)
    adim = eta * mh / (np.sqrt(vh) + eps)
    dz = eta * m / (np.sqrt(v) + eps)
    print("t%d g=%.5f m=%.5f v=%.6f mh=%.5f vh=%.5f"
          % (k, g, m, v, mh, vh))
    print("   duzeltmeli adim=%.6f  duzeltmesiz adim=%.6f"
          % (adim, dz))
    t = t - adim
    print("   yeni t=%.6f" % t)
```

Dört örneğin çıktısı. Bu değerleri bölüm içindeki elle hesapladığın tablolarla karşılaştır: aynı olmaları gerekir, yuvarlama farkları dışında.

```term
$ python b50_ornek.py
Ornek 1: GD, f=x^2+10y^2, eta=0.08, x0=(1,1)
k=0 x=1.0000 y=1.0000 gx=2.0000 gy=20.0000 f=11.0000
k=1 x=0.8400 y=-0.6000 gx=1.6800 gy=-12.0000 f=4.3056
k=2 x=0.7056 y=0.3600 gx=1.4112 gy=7.2000 f=1.7939
k=3 x=0.5927 y=-0.2160 gx=1.1854 gy=-4.3200 f=0.8179
k=4 x=0.4979 y=0.1296 gx=0.9957 gy=2.5920 f=0.4158
k=5 x=0.4182 y=-0.0778 gx=0.8364 gy=-1.5552 f=0.2354

Ornek 2: dikdortgen, 2x+2y=20 (y=10-x)
x=1 y=9 alan=9
x=2 y=8 alan=16
x=3 y=7 alan=21
x=4 y=6 alan=24
x=5 y=5 alan=25
x=6 y=4 alan=24
x=7 y=3 alan=21
x=8 y=2 alan=16
x=9 y=1 alan=9

Ornek 3: Newton sqrt2, x0=1
k=0 x=1.000000000000 hata=4.142e-01 dogru_basamak=0.38
k=1 x=1.500000000000 hata=8.579e-02 dogru_basamak=1.07
k=2 x=1.416666666667 hata=2.453e-03 dogru_basamak=2.61
k=3 x=1.414215686275 hata=2.124e-06 dogru_basamak=5.67
k=4 x=1.414213562375 hata=1.595e-12 dogru_basamak=11.80
k=5 x=1.414213562373 hata=0.000e+00 dogru_basamak=inf

Ornek 4: Adam, f=(t-3)^2, t0=0, eta=0.1
t1 g=-6.00000 m=-0.60000 v=0.036000 mh=-6.00000 vh=36.00000
   duzeltmeli adim=-0.100000  duzeltmesiz adim=-0.316228
   yeni t=0.100000
t2 g=-5.80000 m=-1.12000 v=0.069604 mh=-5.89474 vh=34.81941
   duzeltmeli adim=-0.099897  duzeltmesiz adim=-0.424523
   yeni t=0.199897
t3 g=-5.60021 m=-1.56802 v=0.100897 mh=-5.78605 vh=33.66589
   duzeltmeli adim=-0.099721  duzeltmesiz adim=-0.493643
   yeni t=0.299618
```

### Örnek 1 (★): Gradyan inişinin ilk beş adımı

**Adım 1 — Anla.** `f(x, y) = x² + 10y²` fonksiyonunu `η = 0,08` öğrenme oranıyla, `(1, 1)` noktasından başlayarak minimize etmek istiyoruz. Her adımda `x ← x − η · 2x` ve `y ← y − η · 20y` güncellemesini yapacağız. Amaç, ilk beş adımın değerlerini elle hesaplamak ve `η = 0,08`'in bu fonksiyon için kararlı olup olmadığını görmektir.

**Adım 2 — Örnekle.** Bu fonksiyonun gradyanı `(2x, 20y)`'dir. Başlangıçta `f(1, 1) = 1 + 10 = 11`. Bir adımda `x` yeni değeri `1 − 0,08·2 = 0,84`, `y` yeni değeri `1 − 0,08·20 = −0,6` olur. Örnek olarak bunu tek bir adımda gör: `f(0,84, −0,6) = 0,7056 + 3,6 = 4,3056`. Değer 11'den düştü; bu iyi bir işaret.

**Adım 3 — Kaba çöz.** Her koordinat bağımsız olduğu için her adımda `x` ve `y` ayrı ayrı çarpılır. `x` çarpanı `0,84`, `y` çarpanı `−0,6`'dır. `x` monoton azalır, `y` işaret değiştirerek azalır. Beş adım sonra `f` yaklaşık `0,2`'ye inmiş olmalı.

**Adım 4 — Örüntü.** `y`'nin çarpanı `1 − 20η`'dır ve mutlak değeri `1`'den küçük olmalıdır. Bu, `η < 2/20 = 0,1` demektir. `η = 0,08` bu eşiğin altında olduğu için `y` salınarak sönecek. `x` çarpanı `1 − 2η = 0,84` olduğu için `x` yavaş ama monoton küçülecek. Bu örüntü, 50.5'teki kararlılık eşiğinin doğrudan sonucudur.

**Adım 5 — İyileştir.** Adımları tek tek hesaplamak yerine, `k`. adımda `x_k = 0,84^k` ve `y_k = (−0,6)^k` olduğunu kullanabiliriz. Bu ifadeler aynı tabloyu kapalı biçimde verir. Yani `k`. adımdan sonra `f_k = 0,84^{2k} + 10 (−0,6)^{2k}` olur.

**Adım 6 — Doğrula.** Aşağıdaki tablo elle yaptığın hesabı gösteriyor; programın çıktısıyla aynıdır.

| k | x_k | y_k | ∂f/∂x | ∂f/∂y | f(x_k, y_k) |
|---|---|---|---|---|---|
| 0 | 1,0000 | 1,0000 | 2,0000 | 20,0000 | 11,0000 |
| 1 | 0,8400 | −0,6000 | 1,6800 | −12,0000 | 4,3056 |
| 2 | 0,7056 | 0,3600 | 1,4112 | 7,2000 | 1,7939 |
| 3 | 0,5927 | −0,2160 | 1,1854 | −4,3200 | 0,8179 |
| 4 | 0,4979 | 0,1296 | 0,9957 | 2,5920 | 0,4158 |
| 5 | 0,4182 | −0,0778 | 0,8364 | −1,5552 | 0,2354 |

Tabloda `f` her adımda azalıyor ve `y` işaret değiştirerek sönüyor: kararlı bir yakınsama. Kendi kâğıdındaki sayılarla bu tabloyu karşılaştır; bir yuvarlama farkı dışında aynı olmalı.

**Bunu AI'sız yazabilir misin?** `η = 0,11` için ilk beş adımda `y`'nin çarpanının neden `−1`'i geçtiğini ve `f`'nin neden büyüdüğünü kendi tablonla göster.

### Örnek 2 (★★): Sabit çevrede en büyük alan

**Adım 1 — Anla.** Çevresi 20 metre olan bir dikdörtgenin alanını en büyük yap. Değişkenler kenarlar `x` ve `y`; amaç `f = xy`; kısıt `2x + 2y = 20`.

**Adım 2 — Örnekle.** `x` değerlerini deneyelim. Kısıt `y = 10 − x` verir. `x = 1`'den `9`'a kadar alanları hesaplarsak tabloda gördüğümüz simetrik bir dizi çıkar.

**Adım 3 — Kaba çöz.** Tabloda en büyük alan `x = 5` civarında görünüyor: `x = y = 5` için alan `25`. Bunu daha kesin yapmak için Lagrange'a ihtiyacımız var; ama tahmin doğru yönde.

**Adım 4 — Örüntü.** Alan `x(10 − x) = 10x − x²` bir parabol. Parabolün tepesi `x = 5`'tedir. Simetrinin nedeni, `x` ile `y`'nin kısıtta simetrik olmasıdır. Bu, kare olmanın neden en büyük alanı verdiğini de açıklar.

**Adım 5 — İyileştir.** Lagrange: `∇f = (y, x)` ve `∇g = (2, 2)`. Teğetlik `∇f = λ∇g` verir: `y = 2λ` ve `x = 2λ`. Bu nedenle `x = y`. Kısıttan `x = y = 5` ve `λ = y/2 = 2,5` çıkar. Çarpan, kısıtın bir birim gevşemesinin alanı yaklaşık `2,5` artıracağını söyler.

**Adım 6 — Doğrula.** Tablo ve programın çıktısı şöyle:

| x | y = 10 − x | alan xy |
|---|---|---|
| 1 | 9 | 9 |
| 2 | 8 | 16 |
| 3 | 7 | 21 |
| 4 | 6 | 24 |
| 5 | 5 | 25 |
| 6 | 4 | 24 |
| 7 | 3 | 21 |
| 8 | 2 | 16 |
| 9 | 1 | 9 |

Tablo `x = 5`'te maksimumu gösteriyor ve Lagrange'ın `(5, 5)` sonucuyla aynı. Program da SLSQP ile aynı noktayı `25` alanla buluyor. Çarpan `2,5`'in alan değişimiyle uyumunu kontrol etmek için `c = 22` çevre için alanın `(22/4)² = 30,25` olduğunu hesapla: fark `5,25`. Birinci dereceden tahmin `λ · Δc = 2,5 · 2 = 5` verir; kalan `0,25` ikinci dereceden terimdir.

**Bunu AI'sız yazabilir misin?** Aynı problemi üçgen için yap: sabit çevreli bir üçgende hangi şekil alanı en büyük yapar, ve bunu Lagrange ile nasıl gösterirsin?

### Örnek 3 (★★): Newton ile √2

**Adım 1 — Anla.** `√2`'yi hesaplamak istiyoruz. Bunu `F(x) = x³/3 − 2x` fonksiyonunun yerel minimumunu bularak yapacağız; `F'(x) = x² − 2` olduğundan minimum `√2`'dir.

**Adım 2 — Örnekle.** `x_0 = 1` ile başlayalım. `F'(1) = −1` ve `F''(1) = 2`. Newton adımı `x_1 = 1 − (−1)/2 = 1,5` verir. Bu `√2 ≈ 1,41421`'e yaklaşıyor.

**Adım 3 — Kaba çöz.** Newton adımı `x − F'(x)/F''(x) = x − (x² − 2)/(2x)` olur. Bu, Babil yönteminin formülü: `(x + 2/x)/2`'nin aynısı.

**Adım 4 — Örüntü.** Yakınsama hızı: hata, bir önceki hatanın karesi kadar küçülüyor. Doğru basamak sayısı kabaca iki katına çıkıyor. Bunun nedeni `F''`'nin `√2`'de sıfırdan farklı olmasıdır.

**Adım 5 — İyileştir.** Formülü `x_{k+1} = (x_k + 2/x_k)/2` biçiminde yaz; bölme ve toplama dışında işlem yok. Bu, bir karekök hesabının en verimli yollarından biridir.

**Adım 6 — Doğrula.**

| k | x_k | hata | doğru basamak |
|---|---|---|---|
| 0 | 1,000000000000 | 4,142·10⁻¹ | 0,38 |
| 1 | 1,500000000000 | 8,579·10⁻² | 1,07 |
| 2 | 1,416666666667 | 2,453·10⁻³ | 2,61 |
| 3 | 1,414215686275 | 2,124·10⁻⁶ | 5,67 |
| 4 | 1,414213562375 | 1,595·10⁻¹² | 11,80 |

Doğru basamak sayısı `0,38`'den `11,80`'e çıkıyor: her adımda kabaca iki katına çıkan karesel yakınsama. `k = 5`'te sonuç makine duyarlığının sınırında, bu yüzden programın hatası `0` gösteriyor. Aynı yakınsamayı gradyan inişi (`η = 0,1`) yapsaydı 59 adımda ancak `1,6·10⁻⁹` hataya inerdi.

**Bunu AI'sız yazabilir misin?** Aynı Newton adımını `x³ − 5 = 0`'ın kökü için yaz ve iki adımda `∛5`'e olan hatayı tablola.

### Örnek 4 (★★★): Adam'ın ilk üç adımı ve biyas düzeltmesi

**Adım 1 — Anla.** `f(θ) = (θ − 3)²` fonksiyonunu `θ_0 = 0`'dan, `η = 0,1`, `β₁ = 0,9`, `β₂ = 0,999` ile Adam ile minimize etmek istiyoruz. Amaç, ilk üç adımda `m`, `v`, düzeltilmiş `m̂` ve `v̂` değerlerini izlemek ve biyas düzeltmesinin adım büyüklüğünü nasıl etkilediğini görmek.

**Adım 2 — Örnekle.** `g = f' = 2(θ − 3)`. `θ_0 = 0` için `g_1 = −6`. İlk güncelleme `m_1 = 0,9·0 + 0,1·(−6) = −0,6` ve `v_1 = 0,999·0 + 0,001·36 = 0,036`.

**Adım 3 — Kaba çöz.** Düzeltme `m̂_1 = m_1 / (1 − 0,9) = −6` ve `v̂_1 = v_1 / (1 − 0,999) = 36`. Adım `η · m̂ / √v̂ = 0,1 · (−6)/6 = −0,1`. Parametre `θ_1 = 0 − (−0,1) = 0,1`.

**Adım 4 — Örüntü.** İlk adımda `m̂/√v̂ = g/|g| = ±1`: adım tam olarak `η` büyüklüğünde. Düzeltmesiz hâlde `m/√v = −0,6/0,19 = −3,16`, yani adım 3,16 kat büyük. Bu katsayı `(1 − β₁)/√(1 − β₂)`'dir.

**Adım 5 — İyileştir.** Düzeltmenin etkisi zamanla azalır: `β₂^k` küçüldükçe `√(1 − β₂^k) → 1` olur. Yani yanlılık yalnızca ilk birkaç yüz adımda belirgindir. Bu, düzeltmenin tam olarak neyi düzelttiğini bilmemiz için yeterli bir kanıttır.

**Adım 6 — Doğrula.** Tablo, programın çıktısıyla aynıdır:

Önce ham momentler ve gradyan:

| k | g_k | m_k | v_k |
|---|---|---|---|
| 1 | −6,00000 | −0,60000 | 0,036000 |
| 2 | −5,80000 | −1,12000 | 0,069604 |
| 3 | −5,60021 | −1,56802 | 0,100897 |

Sonra biyas düzeltmesi, adımlar ve yeni konum:

| k | m̂_k | v̂_k | adım (düzeltmeli) | adım (düzeltmesiz) | θ_k |
|---|---|---|---|---|---|
| 1 | −6,00000 | 36,00000 | −0,100000 | −0,316228 | 0,100000 |
| 2 | −5,89474 | 34,81941 | −0,099897 | −0,424523 | 0,199897 |
| 3 | −5,78605 | 33,66589 | −0,099721 | −0,493643 | 0,299618 |

Adım sütununda negatif işaret gradyanın işaretini izler; `θ` pozitif yöne gider. Düzeltmeli adım her üç adımda da `η`'ya yakın kalırken, düzeltmesiz adım `0,32`'den `0,49`'a büyüyor. Bu, `v`'nin yanlı küçüklüğünün `√v`'yi küçülttüğü ve adımı büyüttüğü anlamına gelir.

**Bunu AI'sız yazabilir misin?** `β₁ = 0` alırsan düzeltme formülü ne olur ve Adam'ın ilk adımı hangi işarete göre belirlenir? Bunu üç adımlık bir tablo ile göster.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde önce kendi tasarımını yap; yapay zekâ araçlarına, kendin bir taslak çıkarana kadar başvurma. Aşağıdaki "önerilen yaklaşım" bölümleri yalnızca bir ipucudur, tam çözüm değildir. Başarı kriterlerini tamamlamadan projeyi bitmiş sayma.
:::

### Proje 1 (★★): Optimizer laboratuvarı

**Amaç.** SGD, momentum, Nesterov, RMSProp ve Adam'ı NumPy ile sıfırdan yazıp üç farklı problemde karşılaştıran ve yörünge ile kayıp grafiklerini çizen küçük bir araç yazmak.

**Beklenen davranış.** Araç üç problemde çalışmalı: Rosenbrock, Rastrigin (`20 + Σ (x_i² − 10 cos 2πx_i)`, 2 boyutta) ve küçük bir lojistik regresyon (sabit tohumlu sentetik veri). Her yöntem için bir öğrenme oranı ızgarası denenmeli ve tablo, kalıcı yakınsama adımını ve son değeri vermeli.

**Önerilen yaklaşım.** Her yöntemi tek bir fonksiyon olarak yaz ve hepsi aynı imzayı kullansın: `(gradyan, başlangıç, η, adım sayısı)` ve bir yörünge dizisi döndürsün. Yakınsama ölçütü için bu bölümdeki `kalici` mantığını kendin yeniden yaz; onu okumadan önce kendi çözümünü dene. Lojistik regresyon için kaybın gradyanını elle türet ve 50.3'teki gradyan denetimiyle doğrula. Ayrıca Rastrigin'de yerel minimumlara takılma sıklığını tohumlara göre ölç.

**Başarı kriterleri.** (1) Her yöntemin gradyanı sonlu fark denetimini `10⁻⁶`'nın altındaki göreli hatayla geçer. (2) Tablolar sabit tohumla birebir aynı sonucu üretir. (3) Araç, Adam'ın biyas düzeltmesini kapatıp açtığında ilk adım büyüklüğündeki farkı gösterir. (4) Rastrigin için en iyi öğrenme oranı ile en kötü öğrenme oranı arasındaki yakınsama farkı raporlanır.

### Proje 2 (★★★): İHA görev planlama: kısıtlı rota ve enerji

**Amaç.** Bir İHA'nın bir dizi hedef noktayı ziyaret edip bir batarya bütçesi içinde dönmesi gereken görevi planlamak. Enerji ve menzil kısıtlı bir optimizasyon problemi olarak modellenecek; iki yöntemle çözülüp karşılaştırılacak.

**Beklenen davranış.** Araç, `n` hedef (ör. 8 nokta) için bir ziyaret sırası ve her bacak için bir hız seçsin. Toplam enerji, bacak başına `P₀ d/v + k d v²` ile hesaplansın; toplam süre bir `T_max` ile, toplam menzil bir batarya kapasitesiyle sınırlansın. Araç iki yöntemle çözsün: (a) ziyaret sırası için tavlama, hız için her bacakta bu bölümdeki kısıtlı enerji formülü; (b) aynı problemi doğrusal programlama ile, sıra sabitken, hızları değişken alarak.

**Önerilen yaklaşım.** Önce ziyaret sırası için bir maliyet fonksiyonu yaz: bacak uzunlukları toplamı, her bacak için en iyi hızla enerji. Tavlama için komşuluk olarak 2-opt kullan (50.15'teki gibi) ve sıcaklık takvimini doğrulama bütçesiyle seç. Doğrusal programlama için hız değişkenlerinin süre ve enerji ile ilişkisini doğrusallaştırman gerekecek; bunu nasıl yapacağını kendin bul, ama her doğrusallaştırmanın hangi yaklaşıklığı getirdiğini raporla. Kısıt aktifliğini KKT ile kontrol et.

**Başarı kriterleri.** (1) Tavlama, 8 hedefli bir problemde kesin optimumu (`7!/2` tur, tüm turlar denenerek) en az 4 tohumdan 3'ünde bulur. (2) Doğrusal programlama çözümü, aynı sırada tavlamanın bacak enerjisi toplamından büyük değildir. (3) Raporda hangi kısıtın aktif olduğu ve çarpanının ne anlama geldiği açıklanır. (4) Hız-enerji eğrisi bir grafik olarak verilir ve kısıtsız optimum ile kısıtlı optimum arasındaki fark gösterilir.

## Ek Alıştırmalar

Aşağıdaki problemler kademelidir. ★ olanlar kavramı yoklar, ★★ olanlar bir türetme ya da küçük bir kod ister, ★★★ olanlar birden çok bölüm bilgisini birleştirir. Mülakat etiketli olanlar klasik sorulardır; cevaplarını yazmadan kodla denemeden geçme.

1. ★ `f(x, y) = x² + xy + y²` fonksiyonunun konveks olduğunu Hessian ile göster. Hessian'ın özdeğerlerini bul. (Mülakat)
2. ★ Gradyan inişinde öğrenme oranı neden eşiğin altında olmalıdır? Tek boyutlu `f(x) = x²` için `x_{k+1} = (1 − 2η) x_k` ifadesinden çıkar.
3. ★ Sayısal gradyanda `h`'yi çok küçük seçersen ne olur? Float64 için `h = 10⁻¹⁴` neden yanlış bir türev verir? (Mülakat)
4. ★★ `f(x) = x⁴` için sabit bir öğrenme oranının her yerde kararlı olamayacağını göster. Gradyanın Lipschitz sabiti neden sınırsızdır?
5. ★★ Mini-batch SGD'de batch boyutunu 4 kat artırırsan gürültü varyansı ne olur? Eşit epoch sayısında güncelleme sayısı ne olur? İkisini birlikte yorumla.
6. ★★ Adam'da `β₂ = 0` (düzeltmeli) alırsan `v̂` neye eşit olur ve adım hangi işaret fonksiyonuna benzer? Bunun bir avantajı ve bir sakıncası nedir?
7. ★★ Newton yönteminin bir eyer noktasının yakınında neden yanlış yöne gidebileceğini, Hessian'ın bir özdeğerinin işaretini kullanarak göster. (Mülakat)
8. ★★ Kısıtlı bir problemde aktif olmayan bir kısıtın Lagrange çarpanı hakkında ne söylediğini tamamlayıcı gevşeklikle açıkla. (Mülakat)
9. ★★★ Zayıf dualiteyi kanıtla: her uygun primal çözüm için `cᵀx ≤ bᵀy` olduğunu, bir maksimizasyon LP'si için `y ≥ 0` ile göster. Bu kanıt, dual değerin primal için bir üst sınır olduğunu neden söyler?
10. ★★ Benzetimli tavlamada sıcaklığı hiç düşürmezsen ne olur? Hemen sıfıra indirirsen ne olur? Bu iki uçta yöntemin davranışını anlat. (Mülakat)
11. ★★★ Dal-sınır budamasının doğru olması için sınırın bir üst sınır (maksimizasyonda) olması neden gerekir? Alt sınır kullanırsan hangi dalı yanlışlıkla keseriz?
12. ★ Bir PID denetleyicide türev terimi gürültülü bir sensörde neden tehlikelidir? Bir sinyalin türevinin gürültüye duyarlılığını bir örnekle göster. (Mülakat)

## Kod Okuma Egzersizi

Aşağıdaki kesit, PyTorch'un açık kaynak Adam uygulamasından alınmıştır. Kaynak: `torch/optim/adam.py`, PyTorch sürüm etiketi `v2.4.0`, `_single_tensor_adam` fonksiyonu. Dosyayı `raw.githubusercontent.com/pytorch/pytorch/v2.4.0/torch/optim/adam.py` adresinden indirdim. Aşağıdaki satırlar bu dosyanın 367–368, 378–380, 415–422 ve 430–433. satırlarıdır; aralarındaki AMSGrad dalı (424–429) ve yalnızca `capturable`/`differentiable` durumlarını ele alan dal atlandı. Kaydırılan satırlar (ifade iki satır, bir yorum iki satır) yalnızca görüntü için bölündü; ifadelerde hiçbir değişiklik yoktur.

```python
        if weight_decay != 0:
            grad = grad.add(param, alpha=weight_decay)
```

```python
        # Decay the first and second moment running average
        # coefficient
        exp_avg.lerp_(grad, 1 - beta1)
        exp_avg_sq.mul_(beta2).addcmul_(grad, grad.conj(),
                                        value=1 - beta2)
```

```python
            step = _get_value(step_t)

            bias_correction1 = 1 - beta1**step
            bias_correction2 = 1 - beta2**step

            step_size = lr / bias_correction1

            bias_correction2_sqrt = _dispatch_sqrt(bias_correction2)

            ...

            else:
                denom = (exp_avg_sq.sqrt()
                         / bias_correction2_sqrt).add_(eps)

            param.addcdiv_(exp_avg, denom, value=-step_size)
```

**Sorular — cevaplamadan geçme:**

1. `weight_decay` burada doğrudan `grad`'a ekleniyor. Bu, 50.8'de tanıttığımız AdamW ayrımında hangi tarafa düşer? Bu yaklaşım, `v̂` ile bölündüğünde ağırlık azaltmayı parametreden bağımsız olarak nasıl etkiler?
2. `exp_avg.lerp_(grad, 1 − β₁)` ifadesi, `m ← β₁ m + (1 − β₁) g` denklemine nasıl karşılık gelir? `lerp` fonksiyonunun iç tanımını yazarak eşitliği göster.
3. `step_size = lr / bias_correction1` ve `param.addcdiv_(exp_avg, denom, value=-step_size)` birlikte hangi denklemi uygular? 50.8'deki `η m̂ / (√v̂ + ε)` ile satır satır eşleştir.
4. `ε`, `sqrt(...) / bias_correction2_sqrt` işleminden sonra ekleniyor. Bu, `ε`'nun `√v̂`'ye mi yoksa `√v`'ye mi eklendiği anlamına gelir? Matematiksel olarak hangisi ve neden bu sıra önemlidir?
5. `value=-step_size` argümanı `addcdiv_`'nin hangi bağıntısında yer alır? (`self += value · tensor1 / tensor2` tanımını kaynaktan ya da belgelerden doğrulayarak yaz.)
6. Dosyada tek tensörlü yolun yanında `torch._foreach_*` ile toplu (multi-tensor) bir yol da var. Neden referans olarak tek tensörlü yol daha okunaklıdır, ve toplu yolda `bias_correction1` neden bir liste olarak tutulur?

## Bölüm Özeti

- Optimizasyon, bir amaç fonksiyonunu kısıtlar altında en küçük (ya da en büyük) yapan değişkenleri bulma problemidir; yerel ve küresel minimum ile eyer noktası ayrımı temeldir.
- Gradyan, en dik artış yönünü verir; Hessian eğriliği ölçer ve kritik noktanın türünü belirler. Sayısal gradyanda `h` için kesme ve yuvarlama hatası dengelenir; float32'de optimal `h` belirgin biçimde büyüktür.
- Konveks problemlerde yerel minimum küresel minimumdur; konveks olmayan kayıp yüzeylerinde yöntemin başlangıç noktası ve öğrenme oranı sonucu belirler.
- Gradyan inişinde öğrenme oranı `2/λ_max` eşiğinin altında kalmalıdır; yakınsama hızı koşul sayısı `κ` ile yönetilir ve zikzak bu koşulun sonucudur.
- Momentum ve Nesterov, vadide hız kazanarak zikzağı sönümler. Adam, ilk adımlarda biyas düzeltmesiyle yanlılığı giderir; adımı yaklaşık `η` büyüklüğünde tutar.
- Stokastik gradyan inişi, mini-batch gürültüsünü `1/B` ile ölçeklendirir; batch boyutu ile güncelleme sayısı arasında bir takas vardır.
- Newton yöntemi karesel yakınsar ama Hessian'a ihtiyaç duyar; BFGS gibi yarı-Newton yöntemler bu bilgiyi gradyan farklarından tahmin eder.
- Kısıtlı problemlerde KKT koşulları, aktif kısıtları ve çarpanların gölge fiyat anlamını verir; ceza ve bariyer yöntemleri kısıtı yumuşatarak çözer.
- Doğrusal programlamada optimum bir köşededir; dual problem gölge fiyatları verir. Dal-sınır, LP gevşemesini sınır olarak kullanarak tamsayı problemini budar.
- Türevsiz yöntemler (tavlama, rastgele arama) simülasyon ve kombinatorik problemlerde gradyanın yerini alır; hiperparametre aramasına doğrudan köprü kurar.

**Sonraki bölümde:** Bölüm 51, Bilgi Teorisi ile devam ediyor. Bu bölümde gördüğümüz çapraz entropi kaybı, bir olasılık dağılımı ile gerçek etiket arasındaki bilgi farkını ölçer; entropi, çapraz entropi ve Kullback–Leibler ayrışması, sınıflandırma kayıplarının kökenidir. Bu bölümdeki optimizasyon araçları, o kayıpları minimize etmek için kullanılacak.

::: mulakat
1. Bir fonksiyonun konveks olduğunu Hessian üzerinden nasıl gösterirsin? Bu koşul neden yalnızca iki kez türevlenebilen fonksiyonlar için geçerlidir?
2. Gradyan inişinde öğrenme oranını neden `2/λ_max`'tan küçük seçmelisin? Koşul sayısı büyüdükçe bu sınır ve yakınsama hızı nasıl değişir?
3. Sayısal gradyanı float32 ile hesaplarken `h` için neden float64'e göre çok daha büyük bir değer seçilir? Kesme ve yuvarlama hatasını birlikte açıklayın.
4. Mini-batch SGD'de batch boyutunu artırmak gürültüyü azaltır ama ne kaybettirir? Eşit epoch sayısında iki farklı batch boyutunu karşılaştırın.
5. Newton yöntemi neden karesel yakınsar? Bir eyer noktasının yakınında aynı yöntem neden tehlikeli olabilir?
6. Bir kısıtlı problemde KKT koşullarını ve tamamlayıcı gevşekliği bir örnekle açıklayın. Aktif olmayan bir kısıtın çarpanı neden sıfırdır?
7. Doğrusal programlamada optimum neden bir köşededir? Dual değişkenler hangi ekonomik anlamı taşır?
8. Dal-sınır budamasında sınırın bir üst sınır olması neden kritik? Yanlış bir sınırla kaç çözüm yanlışlıkla kaybedilebilir?
:::
