%% kisim_no: XIV
%% kisim_ad: Makine Öğrenmesi
%% kisim_ayrac: evet
%% bolum_no: 54
%% baslik: ML'e Giriş & Pipeline

## Giriş: Önce bunun bir makine öğrenmesi problemi olup olmadığına karar ver

Bir savunma sistemi mühendisine makine öğrenmesi çoğu zaman bir model eğitme görevi olarak gelmez. Daha sık gelen soru şudur: "Bu veriden bir şey öğrenebilir miyiz, öğrenmeli miyiz?" Bir İHA'nın kamera akışında hedef olup olmadığını söylemek, bir motorun arızasını daha yola çıkmadan tahmin etmek, bir radarın izlediği nesnenin sınıfını belirlemek gibi işler ilk bakışta hep "modelle çözülür" gibi görünür. Ama aynı işler bazen tek bir eşik kuralıyla, bazen de ölçülen fiziğin basit bir denklemiyle daha ucuz, daha açıklanabilir ve daha güvenli çözülür.

Mülakatta ve gerçek projede en sık düşülen hata modelin kendisi değildir. Asıl hata, problemi yanlış kurmaktır: yanlış hedef tanımlamak, gelecekten bilgi sızdırmak, bir test kümesine bakarak model seçmek ya da hiç baseline kurmadan "yüzde doksan iki doğruluk" diye sevinmek. Modeller bu hataları çoğu zaman düzeltemez; onları kendi doğruluk sayılarının arkasına gizlerler.

Bu yüzden bölümü bir model sınıfıyla değil, bir iş akışıyla açıyoruz. Önce ML'in ne zaman kullanılmaması gerektiğini, sonra bir iş hedefinin nasıl bir ML hedefine çevrileceğini göreceksin. Ardından verinin nasıl bölüneceğini, veri sızıntısının neden bu alanın en pahalı hatası olduğunu ve bir modelin neye karşı ölçülmesi gerektiğini (baseline) öğreneceksin. Bölümün sonunda uçtan uca küçük bir örnek, sıfırdan ve scikit-learn ile iki kez kurulacak. Ayrıntılı modeller (Bölüm 58 ve sonrası), metrikler (Bölüm 57) ve veri işleme (Bölüm 56) ileride derinleşir; burada onların çerçevesini kuruyoruz.

Bölümün sayısal bilgileri Python 3.12.10, numpy 2.3.5, pandas 2.3.3, scikit-learn 1.8.0 ve matplotlib 3.10.9 ile üretildi. Rastgele kullanılan her deneyde tohum açıkça verilmiştir. Metindeki her sayı, yazdığımız bir programın çıktısıdır.

::: not
Bu bölümde gördüğün her sayıyı kendi makinende yeniden üret. Tohumlar sabit olduğu için aynı sürümlerde aynı sayıları görmelisin. Farklı bir sayı görürsen önce ortam sürümlerini karşılaştır; sonra kodu oku. Bu alışkanlık, bölümün öğrettiği disiplinin ilk adımıdır: inanmadan önce ölç.
:::

## 54.1 Programı veriden öğrenmek

Klasik yazılımda programcı kuralı yazar. Bir motor sıcaklığı 85 derecenin üstüne çıkarsa alarm veren bir program, bu kuralı doğrudan kodun içine gömer:

    eğer sıcaklık > 85 ise alarm = doğru

Bu kural bilindiği sürece program işini yapar. Ama bazı problemlerde kuralı kimse bilmez. Bir İHA kamerasının bir karesinde "hedef var" olduğunu hangi piksel örüntüsünün söylediğini hiçbir mühendis satır satır yazamaz. Elimizde yalnızca iki şey vardır: girdi-çıktı çiftleri (bu kareler, bu etiketler) ve hatanın nasıl ölçüleceği. Makine öğrenmesi, programcının yazmadığı kuralı bu örneklerden çıkarma işidir.

Biçimsel olarak üç parça vardır. Birincisi **hipotez uzayı** `H = {f_θ : θ ∈ Θ}`: modelin seçebileceği bütün fonksiyonların kümesi. İkincisi **kayıp fonksiyonu** `L(ŷ, y)`: bir tahmin ile gerçek etiket arasındaki hatayı tek bir sayıyla ölçer. Üçüncüsü **eğitim**: eğitim kümesi üzerindeki ortalama kaybı en küçük yapan parametreyi bulmak.

    θ̂ = argmin_θ  (1/n) Σ_i L( f_θ(x_i), y_i )

Bu ifadeye ampirik risk minimizasyonu denir. Kuralı yazmak yerine θ'yı arıyoruz; `θ̂`, eğitimin çıktısıdır. Bölüm 50'deki gradyan inişi bu minimizasyonu yapan en yaygın yoldur, ama amaç yöntem değil, bu eşitliğin çözümüdür.

![Şekil 54.1: Kural tabanlı programda kuralı insan yazar. Öğrenilen programda insan veri, kayıp ve optimizasyonu verir; kuralı (parametreleri θ) algoritma bulur.](gorseller/b54_kural_vs_ogrenme.png)

Aşağıdaki küçük program bu farkı sayılarla gösteriyor. Bir sensör sıcaklığını ölçüyor ve alarm gerekip gerekmediğine bir etiket veriyor. Gerçek eşik 85 derecedir, ama etiketlerin %8'i hatalıdır; gerçek hayatta uzman etiketleri de böyle gürültülü olabilir. Bir mühendis eşiği 90 olarak tahmin etmiş olsun. Program hem bu elle yazılmış kuralın doğruluğunu hem de eşiği veriden arayarak bulunan değeri raporlar.

```python
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
```

Çıktı, öğrenmenin neyi kazandırdığını gösteriyor:

```term
$ python b54_00_esik.py
elle kural (90) dogrulugu: 0.815
ogrenilen esik:           85.0
ogrenilen esik dogruluk: 0.920
```

Elle yazılmış 90'lık kural %81,5 doğrulukta kalıyor. Veriden aranan eşik 85,0'a denk geliyor ve doğruluğu %92,0'ye çıkarıyor. Dikkat et: bu doğruluk, eşiği seçerken kullandığımız veri üzerinde ölçüldü. Yani bu sayı modelin gerçek dünyadaki başarısı değil, yalnızca eğitim verisindeki uyumudur. Genelleme sorusunu 54.6 ve 54.7'de ayrıntılı olarak ele alacağız.

Bu, Bölüm 46'daki TinyML modelinin de arkasındaki fikirdi. Orada küçük bir sinir ağı numpy ile eğitilmiş, sonra cihaza yalnızca ileri geçiş kopyalanmıştı. Eğitim dışarıda yapılıyordu; cihaz yalnızca `θ̂`'yi uyguluyordu.

## 54.2 ML'i ne zaman kullanmamalısın

En önemli mühendislik kararlarından biri, ML kullanmamaya karar vermektir. "Kural yeter" cevabı bir başarısızlık değildir; çoğu zaman daha ucuz, daha hızlı ve daha doğrulanabilir bir çözümdür. Kendine dört soru sor:

1. **Kural yazılabiliyor mu?** Girdi ile çıktı arasındaki ilişki bir formülle ya da birkaç eşikle ifade edilebiliyorsa, öğrenmek gereksizdir.
2. **Yeterli ve temsil edici veri var mı?** Üç arıza kaydıyla bir sınıflandırıcı eğitmek, ezber dışında bir şey öğretmez.
3. **Hatanın maliyeti ve açıklanabilirlik şartı nedir?** Bir hatanın sonucu can kaybıysa ve kararın gerekçesi denetlenmek zorundaysa, öğrenilmiş bir fonksiyon her zaman uygun değildir.
4. **Dağılım zaman içinde sabit mi?** Veri dağılımı hızla değişiyorsa ve bunu izleyecek bir altyapın yoksa, bugün öğrenilen model yarın sessizce bozulur (Bölüm 77 ve 78).

Bu soruların sonucunu bir tabloda özetlemek işe yarar:

| Durum | ML neden riskli | Daha uygun yaklaşım |
|---|---|---|
| Kural net ve kısa: "gerilim 2,8 V altına düşerse kes" | Öğrenilen model bu kuralı bozabilir, kanıtlanamaz | Eşik kuralı, birim testiyle doğrulanır |
| Veri yok ya da çok az | Model ezberler, genelleyemez | Fiziksel model, istatistiksel model (Bölüm 49) |
| Hata maliyeti çok yüksek, gerekçe denetlenmeli | Kararın nedeni açık değildir | Deterministik kontrol yasası, sertifikalı yazılım |
| Dağılım hızla değişiyor, izleme yok | Model sessizce bozulur | Önce izleme altyapısı, sonra model (Bölüm 77) |

Savunma bağlamında bir not ekleyelim. Havacılık ve savunma yazılımının sertifikasyonu izlenebilir gereksinimler ve deterministik davranış bekler. Öğrenilmiş bileşenler için sertifikasyon yolu hâlâ tartışmalıdır ve uygulamaya, bölgeye ve otoriteye göre değişir. Bu nedenle bir ML bileşeni tasarlarken önce şu soruyu cevapla: bileşen hata yaptığında sistemin geri kalanı ne yapar? Bu soru Bölüm 78'de tekrar gelecek.

## 54.3 Öğrenme türleri: bir harita

Makine öğrenmesi tek bir yöntem değil, bir problem ailesidir. Hangi ailenin kullanılacağına veri ve hedef belirler. En önemli ayrım, verinin etiketi olup olmadığıdır.

**Denetimli öğrenme** (supervised learning) her örnek için bir etiket varsayar. Etiket kategorikse buna **sınıflandırma** denir: bu kare "hedef" mi, "arka plan" mı? Etiket sürekli bir sayıysa buna **regresyon** denir: bu motorun kalan ömrü kaç saat? Bölüm 58 ile 60 bu ailenin temel modellerini ele alır.

**Denetimsiz öğrenme** (unsupervised learning) etiket olmadan yapıyı arar. Örnekleri benzerliklerine göre gruplamak (kümeleme), veriyi daha az boyutta özetlemek (boyut azaltma) ya da olağandışı örnekleri bulmak (anomali tespiti) bu ailenin işidir. Bölüm 61'de ele alınacak.

**Yarı denetimli öğrenme** (semi-supervised learning) az sayıda etiketli ve çok sayıda etiketsiz veriyi birlikte kullanır. Etiket pahalıysa, örneğin bir uzmanın her görüntüyü tek tek etiketlemesi gerekiyorsa, bu yaklaşım önemlidir.

**Öz-denetimli öğrenme** (self-supervised learning) etiketi verinin kendisinden üretir: bir cümlenin bir kelimesini gizle ve tahmin ettir, bir görüntünün iki bozulmuş kopyasının aynı nesneye ait olduğunu öğret. Büyük dil modellerinin ve görüntü temsillerinin çoğu bu yolla eğitilir (Bölüm 70 ve 73).

**Pekiştirmeli öğrenme** (reinforcement learning) etiket yerine ödül sinyali kullanır. Bir ajan eylemler yapar, ortamdan geri bildirim alır ve uzun vadeli toplam ödülü en büyük yapan politikayı arar (Bölüm 74).

![Şekil 54.2: Öğrenme türlerinin kısa haritası. Ayrım, verideki etiketin türüne göre yapılır; her dal ilgili bölüme bağlanır.](gorseller/b54_ml_turleri.png)

Bu ayrım neden önemli? Çünkü yanlış bir aile seçmek, baştan başarısız bir deney tasarlamak demektir. Etiketi olmayan bir veriye sınıflandırıcı uygulayamazsın; ödül tanımlamadan pekiştirmeli öğrenmeye başlayamazsın.

## 54.4 Problem çerçeveleme: iş hedefinden ML hedefine

Bir iş sorusu ile bir model arasında bir boşluk vardır ve bu boşluğu doldurmak mühendisliğin asıl işidir. "Hedefi bul" gibi bir istek bir model değildir. Modelin çalışabilmesi için istek bir fonksiyona çevrilmelidir. Bunun için sırayla şu soruları cevapla:

- **Karar.** Sistem hangi kararı verecek? (Alarm ver ya da verme; bakım planla ya da planlama.)
- **Girdi `x`.** Karar anında gerçekten elinde olan bilgi nedir? Gelecekte ne olacağını bilmiyorsan, girdi yalnızca o andaki ölçümlerden oluşmalıdır.
- **Çıktı `y`.** Ne tahmin edilecek? Olasılık, sınıf, sayı, zaman?
- **Etiket kaynağı.** Her `y` değerini kim ya da ne belirleyecek? Uzman, sistem kaydı, sonradan gözlem?
- **Hata türleri ve maliyeti.** Yanlış pozitif (gereksiz alarm) ve yanlış negatif (kaçırılan olay) aynı maliyete sahip değildir.
- **Metrik ve kabul kriteri.** Başarı hangi sayıyla ölçülecek ve hangi değerden sonra "yeterli" sayılacak? (Metriklerin derinliği Bölüm 57'dedir.)

Bu şablonu iki gerçekçi örnekte uygulayalım. Birincisi bir İHA'nın kamerasından gelen kareler için hedef tanımadır. İkincisi bir elektrikli araç bataryasının arıza tahminidir. Yapısal olarak farklı olduklarına dikkat et.

| Öğe | İHA hedef tanıma | EV batarya arıza tahmini |
|---|---|---|
| Karar | Kare için "hedef var" uyarısı | Önümüzdeki 7 gün için bakım planlaması |
| Girdi `x` | Karedeki piksel özellikleri | Son 24 saatin sensör özetleri (gerilim, sıcaklık, akım) |
| Çıktı `y` | 0 (hedef yok) veya 1 (hedef var) | 0 (arıza yok) veya 1 (7 gün içinde arıza) |
| Etiket kaynağı | Uzman anotasyonu, kare kare | Arıza kayıtları, geriye dönük hizalama |
| Hatalar | Kaçırılan hedef (FN), yanlış alarm (FP) | Kaçırılan arıza (FN), gereksiz bakım (FP) |
| Tuzak | Aynı hedef birkaç karede görünür; kareler bağımlıdır | Arıza kaydı tamirden sonra açılır; girdi buna bakamaz |

Tablonun son satırı, bölümün ilerisindeki en önemli konuya işaret ediyor. Batarya örneğinde, "arıza" etiketi servis kaydından geliyorsa ve girdi özelliklerinden biri servis kaydı açıldıktan sonra toplanmış bir ölçümse, model gelecekten bilgi görmüş olur. Bu, veri sızıntısının en sinsi biçimidir (54.8).

Etiketlerle ilgili iki tuzak daha var. **Vekil etiket** (proxy label), gerçek hedefin yerine ölçülmesi kolay bir şeyin kullanılmasıdır: "uçuşta yüksek sıcaklık" arızanın vekili olabilir, ama vekil ile gerçek hedef aynı şey değildir ve model vekili öğrenir. **Etiket gürültüsü** ise iki uzmanın aynı kareye farklı etiket vermesidir. Etiketçiler arası uyum ölçülmediyse, modelin ulaşabileceği en iyi doğruluk bilinmez.

Son olarak karar eşiği. Çoğu sınıflandırıcı bir olasılık üretir, ama kararı biz veririz. Eşiği 0,5 seçmek bir varsayımdır ve maliyetler simetrik değilse yanlıştır. Örneğin kaçırılan bir arızanın maliyeti gereksiz bir bakımın elli katıysa, en iyi eşik 0,5'in çok altında olur. Bunu Çözümlü Örnek 1'de sayılarla göreceğiz.

## 54.5 Temel kavramlar

Bu bölümde sık kullanacağımız kavramları tek yerde toplayalım. Bunların her biri ilerideki bölümlerde derinleşir; burada yalnızca dil ortak olsun.

**Örnek ve özellik.** Bir örnek, bir varlığın ölçülmüş özelliklerinden oluşan bir vektördür (öznitelik vektörü). Bir veri kümesi `n` örnek ve her örnek için `d` özellik içeriyorsa, bunu bir `X` matrisi olarak yazarız: `X` boyutu `n × d`'dir, etiketler bir `y` vektöründe `n` elemanlıdır. Bu, Bölüm 48'deki matris dilinin doğrudan uygulamasıdır. Kodda `X.shape` her zaman ilk kontroldür.

**Hipotez uzayı.** Modelin seçebileceği fonksiyonların ailesidir. Doğrusal bir model `f(x) = wᵀx + b` biçimindedir; `θ = (w, b)`. Bir polinom ailesi derecesiyle belirlenir; bir karar ağacı ise bölünme kurallarıyla. Hipotez uzayı ne kadar geniş olursa, eğitim verisini o kadar iyi uydurabilir; bu, bir sonraki konunun, aşırı uydurmanın kaynağıdır.

**Kayıp fonksiyonu.** Tahminin ne kadar yanlış olduğunu bir sayıya çevirir. Regresyonda en yaygın seçenek kare kayıptır, `L = (y − ŷ)²`. İkili sınıflandırmada log kayıp (çapraz entropi) kullanılır:

    L(p, y) = −[ y · log p + (1 − y) · log(1 − p) ]

Bu ifade Bölüm 51'de çapraz entropi olarak tanıtıldı. Bir bağlantı da burada: Bernoulli modelinde log kaybı en küçük yapmak, Bölüm 49.8'deki en büyük olabilirlik tahminiyle aynı şeydir. Yani kayıp fonksiyonu keyfi bir seçim değil, bir olasılık varsayımının sonucudur.

**Eğitim, bir optimizasyondur.** Eğitim kümesinde kaybı en küçük yapan `θ`'yı bulmak, Bölüm 50'deki optimizasyon problemidir. Gradyan inişi, her adımda kaybın gradyanının ters yönünde küçük bir adım atar: `θ ← θ − η ∇L(θ)`. Bu bölümde eğitimi bu kadar kısa tanımlamamız yeterli; gradyanların türetilmesi Bölüm 55'te yapılacak.

**Genelleme.** Asıl hedef, eğitim kümesinde değil, daha önce görülmemiş yeni verilerde iyi çalışmaktır. Gerçek riski `R(f) = E[ L(f(x), y) ]` ile tanımlarız; bu, veri dağılımından yeni bir örnek çekildiğinde beklenen kayıptır. Eğitim kümesinde ölçtüğümüz `R_ampirik(f)` ise bu değerin yanıltıcı bir tahminidir, çünkü model o örnekleri eğitimde gördü. İkisi arasındaki fark, bölümün ana sorusudur: model neyi öğrendi, neyi ezberledi?

## 54.6 Eksik ve aşırı uydurma; sapma–varyans

Bir modelin başarısızlığı iki yönde olabilir. **Eksik uydurma** (underfitting), model yeterince esnek olmadığı için verideki gerçek örüntüyü bile yakalayamamasıdır; eğitim hatası da yüksektir. **Aşırı uydurma** (overfitting), model eğitim verisindeki gürültüyü de ezberlediğinde ortaya çıkar; eğitim hatası düşüktür ama yeni veride hata büyür.

Bunu görmek için bilinen bir fonksiyonu gürültüyle bozalım. Gerçek fonksiyon `sin(2πx)`, gürültü ise standart sapması 0,2 olan normal dağılımdan çekiliyor. Eğitim kümesi 30 örnek, doğrulama kümesi ayrı 200 örnek. Modeller, derecesi 1'den 12'ye kadar değişen polinomlar. Polinomları `Polynomial.fit` ile kuruyoruz; bu fonksiyon veri aralığını otomatik olarak `[−1, 1]`'e eşler. Bunu yapmamız, yüksek dereceli polinomlarda sayısal kararlılık için önemlidir: ham Vandermonde matrisi bu derecelerde kötü koşullanır.

Programın ilk kısmı eğitim ve doğrulama hatasını hesaplar ve bir CSV dosyasına yazar. İkinci kısım, şekiller için uyum eğrilerini kaydeder.

```python
import csv
import os
import numpy as np
from numpy.polynomial import Polynomial

HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(54)

def veri(n):
    x = rng.uniform(0, 1, n)
    y = np.sin(2 * np.pi * x) + rng.normal(0, 0.2, n)
    return x, y

def rmse(p, x, y):
    return np.sqrt(np.mean((p(x) - y) ** 2))

xe, ye = veri(30)          # egitim: 30 ornek
xv, yv = veri(200)         # dogrulama: 200 ornek, ayni dagilim

print("derece  egitim_RMSE  dogrulama_RMSE")
satirlar = []
for d in range(1, 13):
    p = Polynomial.fit(xe, ye, d)
    e, v = rmse(p, xe, ye), rmse(p, xv, yv)
    satirlar.append((d, e, v))
    print("%5d    %10.4f      %12.4f" % (d, e, v))

en_iyi = min(satirlar, key=lambda t: t[2])
print("dogrulamaya gore en iyi derece:", en_iyi[0])

with open(os.path.join(HERE, "veri", "b54_polinom_hata.csv"), "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["derece", "egitim_rmse", "dogrulama_rmse"])
    w.writerows(satirlar)

```

Şekil için gereken veriler programın ikinci kısmında üretilir. Bu kısım yalnızca çizim içindir.

```python
# Cizim icin: egitim noktalari ve secilen derecelerin egrileri
izgara = np.linspace(0, 1, 201)
with open(os.path.join(HERE, "veri", "b54_polinom_uyum.csv"), "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["derece", "x", "y"])
    for d in (1, 3, 9, 12):
        p = Polynomial.fit(xe, ye, d)
        for x, y in zip(izgara, p(izgara)):
            w.writerow([d, "%.5f" % x, "%.5f" % y])
with open(os.path.join(HERE, "veri", "b54_polinom_nokta.csv"), "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["x", "y"])
    w.writerows(zip(np.round(xe, 5), np.round(ye, 5)))
```

Programı çalıştırdığında şu tabloyu görürsün:

```term
$ python b54_01_polinom.py
derece  egitim_RMSE  dogrulama_RMSE
    1        0.4713            0.4785
    2        0.4679            0.4846
    3        0.1851            0.2033
    4        0.1817            0.2079
    5        0.1474            0.2151
    6        0.1460            0.2142
    7        0.1400            0.2214
    8        0.1301            0.2632
    9        0.1223            0.3210
   10        0.1201            0.2775
   11        0.1161            0.2371
   12        0.1126            0.4974
dogrulamaya gore en iyi derece: 3
```

Tablo üç bölgeyi açıkça gösteriyor. Derece 1 ve 2'de iki hata da yaklaşık 0,47'de kalıyor; model fonksiyonun şeklini yakalayamıyor, bu eksik uydurmadır. Derece 3'te doğrulama hatası 0,203'e düşüyor ve bu, doğrulamada seçilen en iyi derecedir. Derece 9'dan sonra eğitim hatası düşmeye devam ederken doğrulama hatası 0,321'e ve derece 12'de 0,497'ye yükseliyor; model gürültüyü ezberlemeye başlamıştır. Bu iki sonucun birleşimi aşırı uydurmadır. Eğitim hatası tek başına hiçbir şey söylemez: derece 12'nin eğitim hatası derece 3'ten düşüktür ama o model çok daha kötüdür.

Şekil 54.3, dört dereceyi aynı veri üzerinde gösteriyor. Derece 9 ve 12'deki uyum eğrilerinin veri aralığının dışına doğru nasıl kontrolsüz sapmaya başladığına dikkat et.

![Şekil 54.3: Eğitim noktaları (30 örnek) ve dört derecenin uyumu. Derece 1 eksik uydurur, derece 3 gerçek eğriyi izler, derece 9 gürültüyü ezberler, derece 12 veri aralığının kenarlarında patlar.](gorseller/b54_polinom_uyum.png)

Şekil 54.4 hata eğrilerini tek bakışta gösterir. Eğitim hatası derece arttıkça monoton olarak azalırken doğrulama hatası U biçiminde davranır; minimumu, modelin kapasitesi ile veriye uyum arasındaki dengeyi gösterir.

![Şekil 54.4: Eğitim ve doğrulama RMSE'si polinom derecesine göre. Doğrulamadaki minimum derece 3'tür; sağ taraftaki yükseliş aşırı uydurmanın işaretidir.](gorseller/b54_polinom_hata.png)

**Sapma–varyans ayrışımı.** Tek bir eğitim kümesine dayanan tek bir tablo gürültülüdür. Daha temiz bir resim için aynı sabit `x` noktasında beklenen hatayı üç parçaya ayırabiliriz. Gerçek fonksiyon `f`, gözlem `y = f(x) + ε` olsun, `ε` sıfır ortalamalı ve `σ²` varyanslı bağımsız gürültü olsun. Eğitim kümesinden öğrenilen tahmin `f̂(x)` ise, kare kayıp için:

    E[ (y − f̂(x))² ]  =  (E[f̂(x)] − f(x))²  +  Var[f̂(x)]  +  σ²
                         sapma² (bias²)       varyans      ölçüm gürültüsü

Birinci terim **sapma**dır: modelin ortalamada gerçek fonksiyondan ne kadar uzak olduğu. İkinci terim **varyans**dır: farklı eğitim kümeleri alındığında tahminin ne kadar oynadığı. Üçüncü terim, hiçbir modelin azaltamadığı ölçüm gürültüsüdür. Derece arttıkça sapma azalır, varyans artar; en iyi model bu ikisinin toplamını en küçük yapandır. Bu türetme kare kayıp için tam geçerlidir; sınıflandırma kayıpları için benzer ama aynı biçimde olmayan bir ayrışım vardır ve ayrıntısı Bölüm 57'dedir.

Ayrışımı ölçmek için 300 bağımsız eğitim kümesi üretip her biriyle bir model kuruyoruz. Sapma ve varyansı, bu 300 tahminin ortalamasından ve yayılımından hesaplıyoruz.

```python
import numpy as np
from numpy.polynomial import Polynomial

rng = np.random.default_rng(54)
f = lambda x: np.sin(2 * np.pi * x)     # gercek fonksiyon
sigma = 0.2                              # gurultu (sigma^2 = 0.04)
xg = np.linspace(0.1, 0.9, 81)           # ic izgara: veri yogun
xk = np.linspace(0, 1, 101)              # kenar dahil izgara
R = 300                                  # 300 bagimsiz egitim seti
print("derece  bias^2   varyans   bias^2+var+sigma^2   kenar_var")
for d in (1, 3, 9):
    tahmin = np.empty((R, xg.size))
    kenar = np.empty((R, xk.size))
    for r in range(R):
        x = rng.uniform(0, 1, 30)
        y = f(x) + rng.normal(0, sigma, 30)
        p = Polynomial.fit(x, y, d)
        tahmin[r] = p(xg)
        kenar[r] = p(xk)
    ortalama = tahmin.mean(axis=0)
    bias2 = np.mean((ortalama - f(xg)) ** 2)
    var = np.mean(tahmin.var(axis=0))
    kv = np.mean(kenar.var(axis=0))
    print("%5d  %7.4f  %8.4f  %18.4f  %10.2f"
          % (d, bias2, var, bias2 + var + sigma ** 2, kv))
```

Ölçüm noktalarını `[0,1]` aralığının iç kısmında (0,1 ile 0,9 arası) seçtik ve kenarı ayrıca raporladık. Bunun nedeni bir ilk denememizde yaşadığımız sonuçtur: `[0,1]` aralığının tamamında ölçtüğümüzde derece 9 için varyans ortalaması 116 çıktı. Sebep, eğitim örneklerinin aralığın dışına taştığı durumlarda polinomun ekstrapolasyon yapmasıydı. Bu bir programlama hatası değil, yüksek dereceli polinomların doğası; yine de tek bir sayı olarak rapor edilmesi yanıltıcı olurdu. Bu yüzden iki sayıyı birlikte gösteriyoruz.

```term
$ python b54_02_sapma_varyans.py
derece  bias^2   varyans   bias^2+var+sigma^2   kenar_var
    1   0.1490    0.0137              0.2028        0.02
    3   0.0031    0.0048              0.0479        0.01
    9   0.0011    0.3798              0.4209       43.55
```

Tablo klasik resmi doğruluyor. Derece 1'de sapma yüksek (0,149) ama varyans düşük (0,014): model çok katı, her eğitim kümesinde aynı yanlış eğriyi buluyor. Derece 3'te iki terimin toplamı en küçüktür (0,0048 + 0,0031). Derece 9'da sapma neredeyse sıfıra iner (0,0011) ama varyans 0,38'e çıkar: model her eğitim kümesinde farklı bir eğri üretiyor. Kenar sütunundaki 43,55 değeri ise, iç bölgede bile görülmeyen büyük kenar salınımlarını gösteriyor. Toplam hatayı (son sütun), `σ² = 0,04` gürültüyü de içerecek biçimde tahmin ediyoruz; derece 3'ün 0,048 ile en düşük olması, Şekil 54.4'teki doğrulama minimumuyla uyumludur.

Bu iki sonuç bir tasarım ilkesi verir: model karmaşıklığını artırmanın bedeli, veriyi çoğaltmadan ödenemez. Aynı derece daha fazla veriyle eğitildiğinde varyans azalır; bu, öğrenme eğrisinin (54.11) bize göstereceği şeydir. Bölüm 57'de bu takas, düzenlileştirme ve model seçimiyle birlikte resmi olarak ele alınacak.


## 54.7 Veri bölme: eğitim, doğrulama, test

Bir modelin dürüst bir değerlendirmesi, verinin üç ayrı kümeye bölünmesini gerektirir. **Eğitim kümesi** parametreleri (θ) öğrenmek için kullanılır. **Doğrulama kümesi** hiperparametre ve model seçimi için kullanılır: polinom derecesi, k-NN'deki `k`, düzenlileştirme gücü. **Test kümesi** en sonda, bir kez, dürüst bir tahmin için kullanılır.

Üçüncü kuralı en çok çiğneyen insanlar olur: test kümesi bir karar vermek için kullanıldığı anda artık doğrulama kümesine dönüşür. Test sonucuna bakıp modeli değiştirirsen, seçtiğin model o test kümesine uyum sağlamış olur ve sayı şişer. Pratik kural basit: test kümesini bölmenin başında kilitle, başka hiçbir karar için açma. Bu bölümde de test sonuçlarını yalnızca 54.11'de, baseline ve lojistik regresyon için bir kez raporlayacağız; k-NN'in test sonucu bilerek raporlanmamıştır.

Dengesiz sınıflarda rastgele bölme, bir sınıfı eğitimde hiç görmeyen bir test kümesi üretebilir. Bu yüzden **katmanlı bölme** (stratified split) kullanılır: her kümede sınıf oranları orijinaliyle aynı kalır. Aşağıdaki program üç bölme biçimini küçük bir örnekte gösteriyor: el ile sıralı bloklar, katmanlı kat dağılımı ve zaman serisi için ileri yönlü bölme.

```python
import numpy as np
from sklearn.model_selection import (KFold, StratifiedKFold,
                                     TimeSeriesSplit)

# 1) El ile k-katlı bölme: sıralı bloklar
n, k = 10, 5
idx = np.arange(n)
bloklar = np.array_split(idx, k)
for i, test in enumerate(bloklar):
    egitim = np.setdiff1d(idx, test)
    print("kat %d  test=%s  egitim=%s" % (i, test, egitim))

# 2) sklearn KFold(shuffle=False) ile aynı mı?
for i, (tr, te) in enumerate(KFold(k).split(idx)):
    assert np.array_equal(te, bloklar[i])
print("KFold ile el yapımı bölme birebir aynı.")

# 3) Dengesiz sınıflar: StratifiedKFold, kat başına sayılar
y = np.array([0] * 8 + [1] * 2)
print("\nStratifiedKFold(2) kat başına (sınıf0, sınıf1):")
for tr, te in StratifiedKFold(2).split(np.zeros(10), y):
    sayi = np.bincount(y[te], minlength=2)
    print("  test sınıf sayıları:", sayi)

# 4) Zaman serisi: gelecek testte, geçmiş eğitimde
t = np.arange(12)
print("\nTimeSeriesSplit(3) — 12 zaman adımı:")
for tr, te in TimeSeriesSplit(3).split(t):
    print("  egitim=%s  test=%s" % (tr, te))
```

```term
$ python b54_03_bolme.py
kat 0  test=[0 1]  egitim=[2 3 4 5 6 7 8 9]
kat 1  test=[2 3]  egitim=[0 1 4 5 6 7 8 9]
kat 2  test=[4 5]  egitim=[0 1 2 3 6 7 8 9]
kat 3  test=[6 7]  egitim=[0 1 2 3 4 5 8 9]
kat 4  test=[8 9]  egitim=[0 1 2 3 4 5 6 7]
KFold ile el yapımı bölme birebir aynı.

StratifiedKFold(2) kat başına (sınıf0, sınıf1):
  test sınıf sayıları: [4 1]
  test sınıf sayıları: [4 1]

TimeSeriesSplit(3) — 12 zaman adımı:
  egitim=[0 1 2]  test=[3 4 5]
  egitim=[0 1 2 3 4 5]  test=[6 7 8]
  egitim=[0 1 2 3 4 5 6 7 8]  test=[ 9 10 11]
```

İlk blokta el ile yazılmış bloklarla `KFold`'un aynı bölmeleri ürettiğini doğruladık; `assert` bunu kontrol eder. İkinci blokta, sekiz sıfır ve iki birden oluşan bir etiket dizisinde her kat tam olarak dört sıfır ve bir bir içeriyor: katmanlı bölmenin bu dengeyi koruduğunu görüyorsun. Üçüncü blokta ise `TimeSeriesSplit` her seferinde eğitimi geçmişe, testi geleceğe koyuyor. Bunun neden önemli olduğu bir sonraki paragrafta.

**k-katlı çapraz doğrulama** (k-fold cross-validation), veriyi `k` eşit parçaya böler; her parça bir kez test, geri kalanı eğitim olur. Skor, `k` katın ortalamasıdır. Bu, tek bir bölmenin şansına bağlı kalmadan her örneğin bir kez test edilmesini sağlar. Şekil 54.5 beş katlı şemayı gösteriyor.

![Şekil 54.5: Beş katlı çapraz doğrulama. Her satır bir kat; test bloğu her satırda farklı. Skor beş katın ortalamasıdır.](gorseller/b54_kfold_semasi.png)

Çapraz doğrulama bir sınıfın yanlış kullanımına karşı da koruyabilir: katlar arasındaki skor yayılımı (standart sapma), tahminin ne kadar kararlı olduğunu gösterir. Bu yayılımın bir güven aralığına dönüşümü Bölüm 49.9'da bootstrap ile yapılır.

Ama çapraz doğrulama her veri için güvenli değildir. İki durum özellikle tehlikelidir ve Şekil 54.6 bunları iki panelde gösteriyor.

**Zaman serisi.** Gelecekteki bir değeri tahmin etmek için geçmişi kullanırsın. Rastgele bölme, gelecekteki örnekleri eğitime, geçmişteki örnekleri teste sokar. Model zamanın ilerleyişini değil, sadece bir karışımı görür ve performans olduğundan iyi çıkar. Doğru bölme ileriye doğrudur: eğitim geçmişte kalır, test ondan sonra gelir.

**Grup yapısı.** Aynı hastanın, aynı uçuşun ya da aynı cihazın birden fazla kaydı varsa, bu kayıtlar birbirine benzer. Rastgele bölünürse model kişiyi değil, kişinin kimliğini tanır. Doğru bölme, bir grubun tamamını ya da hiçbir kısmını test kümesine koyar (`GroupKFold`). Bu sızıntının ölçülmüş etkisini 54.8'de göreceksin.

![Şekil 54.6: Üstte zaman serisinde rastgele bölme (kırmızı testler geçmişte eğitimdir) ile ileriye doğru bölme. Altta grup yapısında rastgele bölme (kişiler iki tarafta) ile grup bölme (K2 tümüyle test).](gorseller/b54_zaman_grup.png)

## 54.8 Veri sızıntısı

Veri sızıntısı (data leakage), test sürecinde elde olmayacak bir bilginin eğitime girmesidir. Sonuç olarak model, gerçek kullanımda sahip olmayacağı bir bilgiyle iyi görünür. Altın kural şudur: **tahmin anında elinde olmayacak hiçbir bilgi eğitime girmemelidir.** Bu kuralı her öznitelik ve her işlem için sor.

Sızıntının beş yaygın biçimi var:

- **Hedef sızıntısı.** Bir öznitelik, tahmin etmeye çalıştığın sonucu doğrudan kodlar. "Servis kaydı açıldı mı?" bir arızanın sonucudur, nedeni değil.
- **Ön işleme sızıntısı.** Ölçekleyici, eksik değer doldurucu ya da öznitelik seçici tüm veriyle eğitilirse, test kümesinin istatistikleri eğitime karışır.
- **Kopya örnekler.** Aynı örnek hem eğitimde hem testte bulunur; model ezberlediği kopyayı "tahmin eder".
- **Grup sızıntısı.** Aynı kişi, uçuş ya da cihaz iki tarafta da yer alır (54.7).
- **Zaman sızıntısı.** Bir özniteliğin hesaplanması gelecek pencereyi kullanır, örneğin tüm yılın ortalaması.

En sinsi biçim ön işleme sızıntısıdır, çünkü kod temiz görünür. Aşağıdaki deney bunun en bilinen versiyonunu, öznitelik seçimini, bir gürültü veri setiyle gösteriyor. Veri tamamen rastgele: 100 örnek, 5000 öznitelik, etiket rastgele. Gerçek bir sinyal yok, dolayısıyla doğru bir değerlendirme yaklaşık %50 doğruluk vermeli. Öznitelik seçimini iki yolla yapıyoruz: önce tüm veriyle (sızıntılı) ve pipeline içinde, her katın eğitim kısmıyla (doğru). Üç sızıntı türünün tamamını 20 tohumda ölçüyoruz.

Program üç parçaya bölünmüş. İlk parça öznitelik seçimi deneyini kurar.

```python
import csv
import os
import numpy as np
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (KFold, StratifiedKFold,
                                     GroupKFold, cross_val_score,
                                     train_test_split)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline

HERE = os.path.dirname(os.path.abspath(__file__))

def secim_sizintisi(seed):
    # Gercek sinyal yok: X ve y bagimsiz. Dogru tahmin oranı 0.5.
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(100, 5000))
    y = np.repeat([0, 1], 50)
    rng.shuffle(y)
    cv = StratifiedKFold(5, shuffle=True, random_state=seed)
    model = LogisticRegression(max_iter=1000)
    # SIZINTILI: 20 oznitelik tum veriyle seçilir, sonra CV
    Xs = SelectKBest(f_classif, k=20).fit_transform(X, y)
    sizinti = cross_val_score(model, Xs, y, cv=cv).mean()
    # DOGRU: secim, her egitim katinin icinde yapilir
    pipe = make_pipeline(SelectKBest(f_classif, k=20), model)
    dogru = cross_val_score(pipe, X, y, cv=cv).mean()
    return sizinti, dogru

```

İkinci parça kopya örnekleri, üçüncü parça grup sızıntısını kurar.

```python
def kopya_sizintisi(seed):
    # Her ornegin birebir bir kopyasi var (ayni satirlar)
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(200, 20))
    y = rng.integers(0, 2, 200)
    XX, yy = np.vstack([X, X]), np.concatenate([y, y])
    gg = np.concatenate([np.arange(200), np.arange(200)])
    Xtr, Xte, ytr, yte = train_test_split(
        XX, yy, test_size=0.25, random_state=seed)
    sizinti = KNeighborsClassifier(1).fit(Xtr, ytr).score(Xte, yte)
    tr, te = next(GroupKFold(4).split(XX, yy, gg))
    dogru = KNeighborsClassifier(1).fit(XX[tr], yy[tr]).score(
        XX[te], yy[te])
    return sizinti, dogru

```

```python
def grup_sizintisi(seed):
    # 40 kisi, kisi basina 25 ornek; etiket kisiye bagli ve rastgele
    rng = np.random.default_rng(seed)
    kimlik = rng.normal(0, 3, (40, 50))
    g = np.repeat(np.arange(40), 25)
    X = kimlik[g] + rng.normal(0, 1, (1000, 50))
    y = rng.integers(0, 2, 40)[g]
    model = KNeighborsClassifier(1)
    rast = KFold(4, shuffle=True, random_state=seed)
    sizinti = cross_val_score(model, X, y, cv=rast).mean()
    dogru = cross_val_score(model, X, y, cv=GroupKFold(4),
                            groups=g).mean()
    return sizinti, dogru

SEEDS = range(20)
sonuc = []
for ad, fn in [("secim", secim_sizintisi), ("kopya", kopya_sizintisi),
               ("grup", grup_sizintisi)]:
    s = np.array([fn(sd) for sd in SEEDS])
    for j, yontem in enumerate(["sizintili", "dogru"]):
        m, sd = s[:, j].mean(), s[:, j].std(ddof=1)
        sonuc.append((ad, yontem, m, sd))
        print("%-6s %-10s ort=%.3f  ss=%.3f" % (ad, yontem, m, sd))

```

Son parça tohumları döngüye alır, sonuçları yazdırır ve CSV'ye kaydeder.

```python
with open(os.path.join(HERE, "veri", "b54_sizinti.csv"), "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["deney", "yontem", "ortalama", "ss"])
    w.writerows([(a, b, "%.4f" % c, "%.4f" % d)
                 for a, b, c, d in sonuc])
```

```term
$ python b54_04_sizinti.py
secim  sizintili  ort=0.880  ss=0.037
secim  dogru      ort=0.503  ss=0.065
kopya  sizintili  ort=0.870  ss=0.045
kopya  dogru      ort=0.544  ss=0.077
grup   sizintili  ort=1.000  ss=0.000
grup   dogru      ort=0.506  ss=0.092
```

Sonuçlar net. Öznitelik seçimi sızıntısında doğruluk 0,880 çıkıyor; oysa veride sinyal yok ve doğru değer 0,503. Kopya örneklerde 0,870 ve doğru değer 0,544. Grup sızıntısında 1,000 gibi kusursuz bir skor ve doğru değer 0,506. Şekil 54.7 bu farkı tek bakışta gösteriyor.

![Şekil 54.7: Üç sızıntı deneyinde sızıntılı ve doğru değerlendirme. Her çubuk 20 tohumun ortalaması; hata çubukları standart sapma. Kesikli çizgi şans düzeyidir.](gorseller/b54_sizinti_sonuc.png)

Öznitelik seçimi neden bu kadar yanıltıcı? Seçici, 5000 öznitelik arasından etiketle en çok ilişkili 20 tanesini seçer. Veri tamamen rastgele olsa bile, 5000 öznitelikten bazıları bu 100 örnekte etiketle tesadüfen ilişkilidir. Sızıntılı kurulumda bu seçim, daha sonra test edilecek katların etiketlerini de görerek yapılır. Yani test bilgisi zaten seçilen özniteliklere girmiştir. Doğru kurulumda, her katta seçim yalnızca o katın eğitim etiketlerine bakar; test katı seçime hiç katılmaz ve sonuç şans düzeyine iner. Bu, bir pipeline'ın ne işe yaradığının özetidir: `make_pipeline(SelectKBest, LogisticRegression)` gibi bir nesne, `fit` çağrısını yalnızca eğitim katına uygular ve test katını `transform` ile yalnızca dönüştürür. Bunu Kod Okuma egzersizinde kaynaktan göreceksin.

Bu deneyden çıkacak pratik ders şudur: sızıntı kendini çoğu zaman "şüpheli derecede iyi" bir sayı olarak gösterir. Ama her iyi sayı sızıntı değildir; sayının doğruluğunu ancak temiz bir protokolle karşılaştırarak anlarsın. Bu yüzden 54.9'daki baseline'lar ve 54.11'deki sıfırdan kurulum bu alışkanlığın bir parçası olarak tasarlandı.

## 54.9 Baseline'lar: model işe yarıyor mu?

Bir modelin başarısı ancak bir referansla anlamlıdır. **Baseline**, bilerek en basit makul tahmindir: her zaman en sık sınıfı söylemek, sınıf oranına göre rastgele tahmin etmek, regresyonda ortalamayı tahmin etmek ya da tek bir eşik kuralı kullanmak. "Baseline'ı geçmeyen model işe yaramaz" cümlesi sert görünür ama doğrudur: baseline'ı geçmeyen bir model, veriden hiçbir şey öğrenmemiş demektir.

En öğretici tuzak, dengesiz sınıflarda doğruluğun yanıltıcı olmasıdır. Yüzde beş oranında nadir bir olayı (bir arıza, bir sahte alarm) ele alalım. Hiçbir şey öğrenmeyen, her zaman "olay yok" diyen bir model, verinin %95'inde haklı çıkar. Doğruluğu %95 görünür, ama model işe yaramaz. Aşağıdaki program bu paradoksu gösteriyor, sonra gerçek bir veri setinde (meme kanseri, scikit-learn ile birlikte gelen) baseline'larla lojistik regresyonu karşılaştırıyor.

```python
import csv
import os
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.model_selection import (StratifiedKFold, learning_curve,
                                     train_test_split)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))

# Dengesizlik paradoksu: %5 pozitif (ör. sahte alarm / nadir ariza)
rng = np.random.default_rng(54)
y_nadir = (rng.random(10000) < 0.05).astype(int)
tahmin = np.zeros_like(y_nadir)          # hep "0" diyen model
print("nadir olay orani:", y_nadir.mean().round(4))
print("hep-0 modelinin dogrulugu:",
      round(accuracy_score(y_nadir, tahmin), 4))
print("dengeli dogruluk (hep-0):",
      round(balanced_accuracy_score(y_nadir, tahmin), 4))

# Gerçek veri: Wisconsin meme kanseri (paketle gelir, indirilmez)
veri = load_breast_cancer()
X, y = veri.data, veri.target
print("\nsekil:", X.shape, " sinif sayilari:", np.bincount(y))
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=54)

```

Programın geri kalanı baseline'ları test kümesinde bir kez değerlendirir ve bir öğrenme eğrisi hesaplar.

```python
modeller = {
    "hep-cogunluk": DummyClassifier(strategy="most_frequent"),
    "rastgele-oran": DummyClassifier(strategy="stratified",
                                     random_state=54),
    "lojistik": make_pipeline(StandardScaler(),
                              LogisticRegression(max_iter=1000)),
}
sonuc = []
print("\nTEST kumesi (bir kez):  model  dogruluk  dengeli_dogruluk")
for ad, m in modeller.items():
    m.fit(X_tr, y_tr)
    t = m.predict(X_te)
    a, b = accuracy_score(y_te, t), balanced_accuracy_score(y_te, t)
    sonuc.append((ad, a, b))
    print("  %-14s %8.4f  %10.4f" % (ad, a, b))

cv = StratifiedKFold(5, shuffle=True, random_state=54)
boyutlar, egitim, dogrulama = learning_curve(
    make_pipeline(StandardScaler(),
                  LogisticRegression(max_iter=1000)),
    X_tr, y_tr, cv=cv, train_sizes=np.linspace(0.1, 1.0, 10),
    scoring="accuracy")
print("\negitim boyutu  egitim_skor  dogrulama_skor(CV)")
for n, e, v in zip(boyutlar, egitim.mean(1), dogrulama.mean(1)):
    print("%8d   %11.4f   %14.4f" % (n, e, v))

with open(os.path.join(HERE, "veri", "b54_baseline.csv"), "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["model", "dogruluk", "dengeli_dogruluk"])
    w.writerows([(a, "%.4f" % b, "%.4f" % c) for a, b, c in sonuc])
with open(os.path.join(HERE, "veri", "b54_ogrenme_egrisi.csv"), "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["egitim_boyutu", "egitim_skor", "cv_skor"])
    w.writerows([(n, "%.4f" % e, "%.4f" % v) for n, e, v in
                 zip(boyutlar, egitim.mean(1), dogrulama.mean(1))])
```

```term
$ python b54_05_baseline.py
nadir olay orani: 0.0524
hep-0 modelinin dogrulugu: 0.9476
dengeli dogruluk (hep-0): 0.5

sekil: (569, 30)  sinif sayilari: [212 357]

TEST kumesi (bir kez):  model  dogruluk  dengeli_dogruluk
  hep-cogunluk     0.6316      0.5000
  rastgele-oran    0.4737      0.4345
  lojistik         0.9737      0.9643

egitim boyutu  egitim_skor  dogrulama_skor(CV)
      36        1.0000           0.9582
      72        0.9972           0.9692
     109        0.9780           0.9648
     145        0.9848           0.9648
     182        0.9868           0.9670
     218        0.9890           0.9736
     254        0.9890           0.9714
     291        0.9883           0.9714
     327        0.9896           0.9758
     364        0.9907           0.9736
```

Çıktının ilk satırları paradoksu gösteriyor: nadir olay oranı 0,0524 (rastgele üretilmiş veride tam %5 değil), her zaman "0" diyen modelin doğruluğu 0,9476, ama dengeli doğruluğu (her sınıfın kendi içindeki doğruluğunun ortalaması) tam 0,5. Dengeli doğruluk şans düzeyini bu yüzden kullanıyoruz: hep en sık sınıfı söyleyen model %50'de kalır. Gerçek veride test kümesinde (114 örnek) hep-çoğunluk baseline'ı doğruluk 0,632 verir, lojistik regresyon ise 0,974 ve dengeli doğruluk 0,964. Şekil 54.8 bu karşılaştırmayı gösterir.

![Şekil 54.8: Test kümesinde üç model. Hep-çoğunluk baseline'ı doğrulukta 0,63 alır ama dengeli doğrulukta 0,50'dir. Lojistik regresyon her iki ölçüte göre belirgin üstündür.](gorseller/b54_baseline.png)

Burada iki ölçüt yan yana durmalı. Doğruluk, sınıf dengesizliğinde yanıltır; dengeli doğruluk bunu düzeltir. Hangi ölçütün ne zaman doğru olduğu Bölüm 57'nin konusu, ama şimdiden kuralı benimse: karşılaştırma, aynı ölçütle ve aynı test protokolüyle yapılır.

## 54.10 ML iş akışı: pipeline

Bir ML projesi tek bir `fit` çağrısından ibaret değildir. Veri toplamadan izlemeye kadar uzanan bir akış vardır. Şekil 54.9 bu akışı gösteriyor. Üç nokta özellikle önemli: bölme, ön işlemeden önce gelir; test, yalnızca bir kez kullanılır; ve izleme bittiğinde değil, başladığında başlar.

![Şekil 54.9: Uçtan uca ML akışı. Bölme (3), ön işlemeden (4) önce gelir; izleme (9) yeni veriyle geri beslemeye bağlanır.](gorseller/b54_pipeline_akis.png)

Akışın adımlarını kısaca açıklayalım:

1. **Veri toplama.** Verinin nereden, hangi koşullarda ve hangi sensörle geldiğini kaydet. Bu bilgi sonradan yanlılığı anlamak için gerekir (54.12).
2. **Keşif (EDA).** Dağılımlara, eksik değerlere, aykırı değerlere ve sınıf oranlarına bak. Bu aşamada model yok; amaç veriyi tanımak.
3. **Bölme.** Test kümesini kilitle. Zaman ve grup yapısını burada belirle (54.7).
4. **Ön işleme.** Ölçekleme, eksik değer doldurma, öznitelik seçimi. Bunların her biri yalnızca eğitim kısmından öğrenmeli; sızıntı burada başlar (54.8).
5. **Model eğitimi.** Bölüm 58'den itibaren modeller; burada doğrulama ile seçim yapılır.
6. **Değerlendirme.** Test kümesi yalnızca bir kez kullanılır.
7. **Hata analizi.** Model nerede yanılıyor? Hangi sınıf, hangi koşul, hangi grup? Ortalama skor bu sorunun cevabı değildir.
8. **Dağıtım.** Eğitim çoğu zaman dışarıda yapılır, cihaza yalnızca ileri geçiş kopyalanır (Bölüm 46'daki yaklaşım). Üretim ortamında veri akışı için Bölüm 3'te gördüğün üreteçler (generator) büyük veriyi bellek tüketmeden işlemeye yarar.
9. **İzleme.** Girdi dağılımı ve hata oranı zamanla değişir. Bu değişime dağılım kayması denir (54.12, Bölüm 77).
10. **Geri besleme.** Yeni etiketli veri toplanır, akış baştan başlar.

**Deney disiplini.** Akışın her adımı tekrarlanabilir olmalıdır. Üç araç bunu sağlar. Birincisi **tohum**: her rastgele işlem sabit bir tohumla çalışmalı. İkincisi **sürüm kaydı**: Python, numpy ve scikit-learn sürümleri raporla; bu bölümün her sayısı bu sürümlerle üretildi. Üçüncüsü **deney günlüğü**: her deneyin yapılandırmasını ve sonucunu, Bölüm 3'te öğrendiğin JSON biçiminde kaydet. Tek bir tohumla yapılan bir karşılaştırma bir zar atışıdır; birden fazla tohumun ortalamasını ve yayılımını rapor etmeden iki model arasında "ilk daha iyi" demek doğru olmaz. Bu ölçüm belirsizliğini nasıl yorumlayacağın Bölüm 49.9'un konusudur.

Bu akışın sonunda bir dağıtım ve izleme sistemi olur. Bu sistemin nasıl işletileceği Bölüm 77'de MLOps olarak ele alınacak.

## 54.11 Uçtan uca ilk örnek: sıfırdan ve scikit-learn ile

Şimdi akışı gerçek bir veride uçtan uca çalıştıralım. Veri scikit-learn'ün paketinde gelen Wisconsin meme kanseri veri seti: 569 örnek, 30 özellik (hücre çekirdeği ölçümleri). Sınıflar 212 kötü huylu (`malignant`, etiket 0) ve 357 iyi huylu (`benign`, etiket 1). Ayrıntılı tıbbi yorum bu bölümün konusu değil; amacımız protokolü görmek.

Protokol sırası şöyle: test kümesi bölmenin başında kilitlenir. Bölme katmanlıdır, test oranı %20'dir. Standardizasyon yalnızca eğitim kümesinden öğrenilir. Model seçimi (k-NN'deki `k`) yalnızca eğitim kümesi içindeki çapraz doğrulamayla yapılır. Test kümesi, baseline ve lojistik regresyon için en sonda bir kez kullanılır.

Bölme sonucu 455 eğitim ve 114 test örneğidir. Eğitimde 170 kötü huylu ve 285 iyi huylu; testte 42 kötü huylu ve 72 iyi huylu örnek vardır.

**Adım A: lojistik regresyonu sıfırdan yazmak.** Model `p = σ(wᵀx + b)` olasılığını verir, burada `σ` sigmoid fonksiyonudur. Scikit-learn'ün varsayılan lojistik regresyonu bir L2 cezasıyla çalışır; amaç, `C · Σ logloss + ½‖w‖²` biçimindedir. Bu amacı `n`'e böldüğümüzde gradyan `Xᵀ(p − y)/n + w/(Cn)` olur. Gradyanın türetilmesi Bölüm 55'te; burada sonlu fark denetimi (Bölüm 50.3) ile doğruluğunu kontrol ediyoruz. Program bu denetimin sonucunu da yazdırır.

```python
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))

def kayip(w, b, X, y, C):
    # sklearn'in amaci: C * sum(logloss) + 0.5 ||w||^2, n'e bolunmus
    p = np.clip(sigmoid(X @ w + b), 1e-12, 1 - 1e-12)
    ll = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    return ll + np.sum(w * w) / (2 * C * len(y))

def lojistik_gd(X, y, C=1.0, eta=0.1, adim=100000):
    n, d = X.shape
    w, b = np.zeros(d), 0.0
    for _ in range(adim):
        p = sigmoid(X @ w + b)
        g_w = X.T @ (p - y) / n + w / (C * n)   # L2 terimi
        g_b = np.mean(p - y)                    # bias'a ceza yok
        w, b = w - eta * g_w, b - eta * g_b
    return w, b

```

```python
veri = load_breast_cancer()
X_tr, _, y_tr, _ = train_test_split(
    veri.data, veri.target, test_size=0.2, stratify=veri.target,
    random_state=54)
mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)   # sadece egitim
Z = (X_tr - mu) / sd

# Gradyan denetimi (Bolum 50.3): analitik ve sonlu fark
rng = np.random.default_rng(0)
w0, b0 = rng.normal(size=30) * 0.1, 0.0
p = sigmoid(Z @ w0 + b0)
g = Z.T @ (p - y_tr) / len(y_tr) + w0 / (len(y_tr))
h = 1e-6
num = np.array([(kayip(w0 + h * e, b0, Z, y_tr, 1.0)
                 - kayip(w0 - h * e, b0, Z, y_tr, 1.0)) / (2 * h)
                for e in np.eye(30)])
print("gradyan denetimi, en buyuk fark:",
      "%.2e" % np.max(np.abs(g - num)))

w, b = lojistik_gd(Z, y_tr)   # 100000 adim: yakinsama
sk = LogisticRegression(C=1.0, max_iter=10000, tol=1e-10).fit(Z, y_tr)
print("max |w_sifirdan - w_sklearn| =",
      "%.2e" % np.max(np.abs(w - sk.coef_[0])))
print("|b_sifirdan - b_sklearn|     =",
      "%.2e" % abs(b - sk.intercept_[0]))
print("egitim dogrulugu (sifirdan):",
      round(np.mean(((Z @ w + b) > 0) == y_tr), 4))
print("egitim dogrulugu (sklearn): ",
      round(sk.score(Z, y_tr), 4))
```

```term
$ python b54_06_lojistik.py
gradyan denetimi, en buyuk fark: 1.04e-10
max |w_sifirdan - w_sklearn| = 7.77e-07
|b_sifirdan - b_sklearn|     = 1.02e-07
egitim dogrulugu (sifirdan): 0.989
egitim dogrulugu (sklearn):  0.989
```

Gradyan denetiminde en büyük fark 1,0·10⁻¹⁰ çıktı: analitik gradyan doğru. Ama ilk denemede gradyan inişini 20 000 adımla çalıştırdığımızda katsayılar sklearn'den 2,2·10⁻³ kadar uzaktı ve gradyan normu hâlâ 1,35·10⁻⁵ idi; yani yöntem yakınsamamıştı. Karşılaştırmayı yakınsama kontrolü yapmadan yapsaydık, katsayı farkını bir uygulama hatası sanabilirdik. Adım sayısını 100 000'e çıkardığımızda gradyan normu 9,4·10⁻¹⁴'e indi ve katsayı farkı 7,8·10⁻⁷ oldu. Sıfırdan yazılan bir optimizasyonu, referansla karşılaştırmadan önce yakınsadığını göstermek gerekir; bu, Bölüm 50'nin ana uyarısıdır.

Sıfırdan model ile scikit-learn'ün modeli aynı eğitim doğruluğunu veriyor: 0,989. Scikit-learn'ün `LogisticRegression` nesnesi, bu adımda kullanılan eşleşmeyi kanıtlamak içindir; üretimde pipeline içinde kullanılacaktır.

**Adım B: k-NN.** En yakın `k` komşunun çoğunluk oyuyla sınıflandıran k-NN, eğitim verisini saklar ve tahmin anında uzaklık hesaplar. Sıfırdan uygulamasında uzaklık matrisi açıkça kurulur. Kritik nokta `k`'nın seçimidir: test kümesine bakmadan, yalnızca eğitim kümesinde 5 katlı çapraz doğrulamayla seçilir. Ölçekleyici her katta yeniden, o katın eğitim kısmından öğrenilir. Bu, 54.8'deki sızıntı dersinin doğrudan uygulamasıdır.

```python
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.neighbors import KNeighborsClassifier

def knn_tahmin(X_tr, y_tr, X_te, k):
    # Tum uzakliklar: (n_test, n_train) matrisi
    D = np.sqrt(((X_te[:, None, :] - X_tr[None, :, :]) ** 2).sum(-1))
    komsu = np.argsort(D, axis=1)[:, :k]    # en yakin k komsu
    oy = y_tr[komsu].mean(axis=1)           # ikili oylama
    return (oy >= 0.5).astype(int)          # k tek ise berabere yok

def olcekle(X_tr, X_te):
    # Olcekleyici yalnizca egitim kismindan ogrenir
    mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
    return (X_tr - mu) / sd, (X_te - mu) / sd

veri = load_breast_cancer()
X_tr, _, y_tr, _ = train_test_split(
    veri.data, veri.target, test_size=0.2, stratify=veri.target,
    random_state=54)

```

```python
# k secimi: sadece egitim verisinde 5 katli CV
cv = StratifiedKFold(5, shuffle=True, random_state=54)
print("k   CV dogruluk (sifirdan)")
skor = {}
for k in range(1, 32, 2):
    dogru = []
    for tr, va in cv.split(X_tr, y_tr):
        A, B = olcekle(X_tr[tr], X_tr[va])   # kat-ici olcekleme
        tahmin = knn_tahmin(A, y_tr[tr], B, k)
        dogru.append(np.mean(tahmin == y_tr[va]))
    skor[k] = np.mean(dogru)
    print("%2d  %.4f" % (k, skor[k]))
k_en_iyi = max(skor, key=skor.get)
print("secilen k:", k_en_iyi)

# Dogrulama: sklearn ile ayni tahminler mi?
A, B = olcekle(X_tr, X_tr)
sk = KNeighborsClassifier(n_neighbors=k_en_iyi).fit(A, y_tr)
ayni = np.mean(knn_tahmin(A, y_tr, B, k_en_iyi) == sk.predict(B))
print("sifirdan ve sklearn tahmin uyumu:", ayni)
```

```term
$ python b54_07_knn.py
k   CV dogruluk (sifirdan)
 1  0.9451
 3  0.9648
 5  0.9604
 7  0.9626
 9  0.9582
11  0.9582
13  0.9560
15  0.9560
17  0.9560
19  0.9516
21  0.9516
23  0.9473
25  0.9473
27  0.9407
29  0.9407
31  0.9363
secilen k: 3
sifirdan ve sklearn tahmin uyumu: 1.0
```

Tablo `k` değerlerinin doğruluğunu veriyor. En iyi değer `k = 3`, çapraz doğrulama doğruluğu 0,965. Tek bir tohumdaki farklar küçük (0,95 ile 0,965 arası), bu yüzden `k` seçimi kesin bir sonuç değil, makul bir tercihtir. Sıfırdan yazılan k-NN'in sklearn'ün `KNeighborsClassifier`'ı ile aynı tahminleri verdiği son satırda doğrulanıyor (1,0).

**Adım C: test kümesi, bir kez.** Şimdi 54.9'da gördüğümüz baseline'lar ve lojistik regresyon test kümesinde değerlendirildi. Sonuçlar:

| Model | Test doğruluğu | Test dengeli doğruluğu |
|---|---|---|
| Hep çoğunluk (baseline) | 0,632 | 0,500 |
| Rastgele oran (baseline) | 0,474 | 0,435 |
| Lojistik regresyon | 0,974 | 0,964 |

Bu bölümde k-NN'in test sonucunu raporlamadık; testi bir kez kullanma kuralını korumak için bu sonucu Proje 1'de sen üreteceksin. Rakamlar doğru olsa bile yalnızca bu kuralı dürüstçe uygularsan güvenilirdir.

**Öğrenme eğrisi.** Eğitim kümesinin büyüklüğü arttıkça model ne kadar iyileşiyor? Scikit-learn'ün `learning_curve` fonksiyonu, eğitim kısmının %10'undan %100'üne kadar alt kümelerle çapraz doğrulama skorunu hesaplar. Programın bu kısmı 54.9'daki çıktıda da yer alıyordu; şimdi sonucu yorumluyoruz.

Eğitim alt kümesi 36 örnekten 364 örneğe çıktıkça çapraz doğrulama doğruluğu 0,958'den 0,974'e yükseliyor; eğitim doğruluğu ise 1,000'den 0,991'e iniyor. Aralık (boşluk) büyük değil ama kalıcı: model biraz ezberlemeye devam ediyor. Veri arttıkça kazanç küçülüyor; yani daha fazla veri biraz yardım ediyor ama tek başına bir sınır koyuyor. Bu sınırı aşmak için ya öznitelikleri değiştirmek ya da farklı bir model ailesine geçmek gerekir (Bölüm 57, 58 ve 59).

![Şekil 54.10: Öğrenme eğrisi. Eğitim doğruluğu ve çapraz doğrulama doğruluğu, eğitim alt kümesinin büyüklüğüne göre. Aradaki aralık, modelin ezber payıdır.](gorseller/b54_ogrenme_egrisi.png)

## 54.12 Model kartı, yanlılık ve dağılım kayması

Bir modelin sayıları tek başına bir şey anlatmaz; hangi veriden, hangi protokolle, hangi koşullarda üretildiklerini de söylemek gerekir. Bunu bir **model kartı** (model card) ile yapıyoruz: modelin kısa bir kimlik belgesi. Aşağıdaki tablo, bu bölümdeki lojistik regresyon için bir kart örneği. Veri kliniğe ait değil; bu kart bir öğretim örneğidir ve klinik kullanım için yeterli değildir.

| Alan | İçerik |
|---|---|
| Amaç | Öğretim: lojistik regresyonun baseline'a göre üstünlüğünü göstermek |
| Kullanım dışı alan | Klinik tanı, hasta kararı; bu veri seti bir klinik protokol değildir |
| Veri | 569 örnek, 30 özellik, scikit-learn paketi; kaynak ve toplama koşulları bu pakette belgelidir |
| Bölme | Katmanlı, %20 test, sabit tohum 54; test bir kez kullanıldı |
| Metrikler | Doğruluk ve dengeli doğruluk; baseline: hep çoğunluk, rastgele oran |
| Bilinen sınırlar | Tek merkezli veri; cihaz ve popülasyon değişimi test edilmedi |
| Sürümler | Python 3.12.10, numpy 2.3.5, scikit-learn 1.8.0 |

Kartın "sınırlar" satırı bu bölümün ana uyarısıdır: model, eğitim verisinin dünyasında iyidir. Yanlılık ve dağılım kayması, o dünyanın dışına çıkıldığında ortaya çıkar.

**Yanlılık (bias).** Veri, gerçek dünyanın tarafsız bir örneği olmayabilir. Belirli bir sensörle, belirli bir hava koşulunda ya da belirli bir popülasyonda toplanmış veri, o koşullar dışında bir şey öğretemez. Etiketler de yanlı olabilir: uzmanların belirli türleri daha sık etiketlemesi, ya da bir sistemin bazı arızaları kaydetmeyi unutması gibi. Bu yanlılıklar modelin hatasına dönüşür ve ortalama skorda görünmez; bu yüzden 54.10'daki hata analizi adımı, skoru gruplara ayırarak bakmayı önerir.

**Dağılım kayması (distribution shift).** Eğitimde görülen dağılım ile dağıtımda görülen dağılım farklıysa model bozulur. Üç tür ayırt edilir. Girdi dağılımı değişirse (kovaryat kayması), `p(x)` değişmiş, ilişki `p(y|x)` aynı kalmış olabilir. Sınıf oranı değişirse (etiket kayması), `p(y)` değişmiştir. İlişkinin kendisi değişirse (kavram kayması), `p(y|x)` değişmiştir ve bu en zoru, çünkü model yanlış bir ilişkiyi öğrenmiş durumda kalır. Bu üçünü ayırt etmek için yalnızca skora bakmak yetmez; girdi dağılımını ve hata oranını zamanla izlemek gerekir. Bu izleme, akışın 9. adımıdır ve Bölüm 77'nin konusudur; sağlam bir modelin bu değişimlere karşı nasıl test edileceği Bölüm 78'de tartışılır.

**İnsan döngüde karar.** Yüksek riskli sistemlerde bir modelin çıktısı çoğu zaman bir karar önerisidir, kararın kendisi değildir. Tasarım ilkesi şudur: ML bileşeni hata yaptığında, sistemin geri kalanı güvenli bir duruma geçebilmelidir ve nihai sorumluluk, kararın etkisini bilen bir insanda kalmalıdır. Bu ilke bir programlama tekniği değil, bir mimari kararıdır; dolayısıyla model seçiminden önce alınır.


## Çözümlü Örnekler

Dört örnek bölümün kavramlarını elle izlemeni hedefler. Her birinde önce kâğıt üstünde iz sürersin, sonra programla doğrularsın. Sayısal sonuçların tamamı yukarıdaki programların çıktısıyla birebir aynıdır.

### Örnek 1 (★): İHA bakım kararında eşik seçimi

**Adım 1 — Anla.** Bir model 6 uçuşun her biri için bir arıza olasılığı `p` veriyor. Bir kaçırılan arızanın maliyeti 50 birim, gereksiz bir bakımın maliyeti 1 birim. Hangi eşikle "bakım yap" demeliyiz? Neden 0,5 büyük ihtimalle yanlış?

**Adım 2 — Örnekle.** Kayıtlar: `p` = 0,01 / 0,03 / 0,30 / 0,60 / 0,04 / 0,02 ve gerçek durum `y` = 0 / 1 / 0 / 1 / 0 / 1. Eşik 0,5 alınırsa yalnızca `p = 0,60` olan kayıt "bakım" olur. `y = 1` olan ikinci ve altıncı uçuş kaçar; her biri 50 birim maliyet demektir.

**Adım 3 — Kaba çöz.** Her eşik `t` için toplam maliyet, eşiğin altında kalan gerçek arızaların sayısı çarpı 50 ile, eşiğin üstünde kalan sağlam uçuşların sayısı çarpı 1 ile hesaplanır. Eşik yalnızca `p` değerlerinde değişir; bu yüzden adayları `p` değerlerinin kendisi ve iki uç olarak almak yeterlidir.

**Adım 4 — Örüntü.** Eşik düştükçe kaçan arıza azalır, gereksiz alarm artar. Beklenen maliyeti eşiğe göre türevlediğinde en iyi eşik `t* = c_FP / (c_FP + c_FN)` çıkar. Burada `t* = 1 / 51 ≈ 0,0196`. Bu türetmenin kalibrasyon koşulunu (model olasılıkları gerçek frekansla uyuşmalı) Bölüm 57'de ele alacağız; burada sayıya güvenmek yerine taramayla doğrulayacağız.

**Adım 5 — İyileştir.** Eşiği elle hesaplamak yerine bütün adayları tarayıp en küçük maliyeti seçen bir döngü yazabiliriz. Program aynı zamanda iki eşikteki kararları yan yana gösterir.

```python
import numpy as np

# Model her ucusa bir ariza olasiligi p veriyor (kalibre varsayiyoruz)
p = np.array([0.01, 0.03, 0.30, 0.60, 0.04, 0.02])
y = np.array([0, 1, 0, 1, 0, 1])       # gercekte ariza (1) oldu mu
c_fn, c_fp = 50, 1          # kacirilan ariza, gereksiz bakim

def maliyet(t):
    karar = (p >= t).astype(int)
    fn = np.sum((karar == 0) & (y == 1))
    fp = np.sum((karar == 1) & (y == 0))
    return fn * c_fn + fp * c_fp, karar

print("ucus    p     y   karar(0.5)  karar(1/51)")
_, k1 = maliyet(0.5)
_, k2 = maliyet(1 / 51)
for i in range(len(p)):
    print("%4d  %5.2f  %3d   %9d   %10d"
          % (i + 1, p[i], y[i], k1[i], k2[i]))
print("toplam maliyet, t=0.5:   ", maliyet(0.5)[0])
print("toplam maliyet, t=1/51:  ", maliyet(1 / 51)[0])

# Tum esikleri tara: en dusuk maliyet nerede?
adaylar = np.unique(np.concatenate([p, [0.0, 1.0]]))
en = min(adaylar, key=lambda t: maliyet(t)[0])
print("en iyi esik (tarama):", round(en, 4),
      " maliyet:", maliyet(en)[0])
```

**Adım 6 — Doğrula.** Program çıktısı:

```term
$ python b54_08_ornek_maliyet.py
ucus    p     y   karar(0.5)  karar(1/51)
   1   0.01    0           0            0
   2   0.03    1           0            1
   3   0.30    0           0            1
   4   0.60    1           1            1
   5   0.04    0           0            1
   6   0.02    1           0            1
toplam maliyet, t=0.5:    100
toplam maliyet, t=1/51:   2
en iyi esik (tarama): 0.02  maliyet: 2
```

Elle izin sonucu da aynı: 0,5 eşiğinde iki kaçan arıza, toplam maliyet 100. Eşik 1/51'de (ve tarama ile 0,02'de; `p = 0,02` kaydı her iki eşikte de "bakım" olur) iki gereksiz alarm, toplam maliyet 2. Eşik kararı, yalnızca maliyet oranına bağlıdır; doğruluk yüzdesi burada yanıltıcı olurdu.

**Bunu AI'sız yazabilir misin?** `c_FN = 5` olsaydı `t*` ne olurdu? Bu durumda `p = 0,03` olan ikinci uçuş için kararın değişip değişmediğini kâğıtta göster.

### Örnek 2 (★★): On noktalı k-NN'nin elle izi

**Adım 1 — Anla.** On noktalık küçük bir veri kümesi var. Sorgu noktası `q = (4, 3)`. `k = 3` komşu ile sınıfı tahmin edeceğiz. Amaç, uzaklıkları kendi elinle hesaplayıp sıralamak ve oyu saymaktır.

**Adım 2 — Örnekle.** Uzaklık yerine kare uzaklığı (`d²`) kullanacağız; kökü almak sıralamayı değiştirmez. Örneğin `(5, 4)` için `d² = (5 − 4)² + (4 − 3)² = 2`.

**Adım 3 — Kaba çöz.** Her noktanın `d²` değerini hesapla, sırala, ilk üç komşunun etiketlerini say.

**Adım 4 — Örüntü.** Sıralamada en yakın noktalar birbirine karışık etiketlidir: `(5, 4)` etiket 1, `(2, 3)` etiket 0, `(4, 5)` etiket 1. Üç komşudan ikisi 1, biri 0. Burada beraberlik yok, çünkü dördüncü ve beşinci konumlar (`d² = 5`) üçüncü konumdan uzakta.

**Adım 5 — İyileştir.** Kendi elinle sıralamayı yaptıktan sonra tekrar kontrol etmek için programı kullan. Programın `d²` sütunu elle hesapladığınla aynı olmalı.

```python
import numpy as np

X = np.array([[1, 1], [2, 1], [1, 2], [2, 3], [3, 1],
              [5, 4], [6, 5], [5, 6], [4, 5], [6, 2]], float)
y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
q = np.array([4.0, 3.0])
k = 3

d2 = ((X - q) ** 2).sum(axis=1)       # kare mesafe (kok gerekmez)
sira = np.argsort(d2, kind="stable")
print(" sira  nokta      d^2  etiket")
for r, i in enumerate(sira, 1):
    print("%5d  (%g,%g)  %5g  %6d"
          % (r, X[i, 0], X[i, 1], d2[i], y[i]))
komsu = sira[:k]
oy = y[komsu].sum()
print("k=%d komsu etiketleri: %s" % (k, y[komsu]))
print("oylama: 1 oy = %d, 0 oy = %d -> tahmin %d"
      % (oy, k - oy, int(oy > k / 2)))
```

**Adım 6 — Doğrula.** Program çıktısı:

```term
$ python b54_08_ornek_knn.py
 sira  nokta      d^2  etiket
    1  (5,4)      2       1
    2  (2,3)      4       0
    3  (4,5)      4       1
    4  (3,1)      5       0
    5  (6,2)      5       1
    6  (2,1)      8       0
    7  (6,5)      8       1
    8  (1,2)     10       0
    9  (5,6)     10       1
   10  (1,1)     13       0
k=3 komsu etiketleri: [1 0 1]
oylama: 1 oy = 2, 0 oy = 1 -> tahmin 1
```

Tablo, elle yaptığın sıralamayla aynıdır: ilk üç komşu `[1 0 1]`, oylama 2'ye 1, tahmin 1. Aynı sorgu için `k = 1` olsaydı yalnızca en yakın `(5, 4)` bakılacak ve tahmin yine 1 olurdu; `k = 5` olsaydı beşinci konuma kadar bakılacak ve oy yine 1'e düşerdi. Bu, `k`'nın değerinin bazen sonucu değiştirmediğini, bazen değiştirdiğini gösterir; hangisinin olduğunu doğrulama kümesi söyler.

**Bunu AI'sız yazabilir misin?** Sorgu noktasını `(3, 2)` yaparak aynı tabloyu kur. Hangi üç komşu seçilir ve tahmin ne olur? Bir beraberlik (`d²` değerleri aynı) ortaya çıkıyorsa, `k` çift olduğunda oylama nasıl bozulur?

### Örnek 3 (★★): Polinom derecesinin seçimi

**Adım 1 — Anla.** Veri `sin(2πx)` gürültüsüyle bozulmuş, eğitim 30 örnek. Amaç, hangi polinom derecesinin doğrulamada en iyi olduğunu bulmak ve bunun neden eğitim hatasına bakarak seçilemeyeceğini göstermek.

**Adım 2 — Örnekle.** Derece 1 için eğitim ve doğrulama RMSE'si 0,4713 ve 0,4785 (54.6'daki polinom programının çıktısı). Derece 9 için 0,1223 ve 0,3210.

**Adım 3 — Kaba çöz.** Dereceleri eğitim hatasına göre sıralarsan en iyi model derece 12 çıkar (0,1126). Doğrulamaya göre sıralarsan derece 3 (0,2033).

**Adım 4 — Örüntü.** Eğitim hatası monoton düşerken doğrulama hatası U biçimindedir. Eğitim hatası, modelin kendi verisini ezberleme kapasitesini ölçer; ona bakarak model seçmek her zaman daha karmaşık modeli seçer.

**Adım 5 — İyileştir.** Doğrulamaya göre seçilen dereceyi bir kenara koy. Seçimi doğrulama kümesi üzerinde yaptığın için o kümedeki 0,2033 sayısı artık hafifçe iyimserdir; dürüst bir rapor için ayrı bir test kümesi gerekir (54.7). Bu yüzden her dereceyi ayrı bir veri üzerinde tekrar değerlendirmek, seçimi doğrulamak için ikinci bir ölçüm sağlar.

**Adım 6 — Doğrula.** Aşağıdaki tablo 54.6'daki polinom programının çıktısından alındı:

| Derece | Eğitim RMSE | Doğrulama RMSE | Yorum |
|---|---|---|---|
| 1 | 0,4713 | 0,4785 | Eksik uydurma |
| 3 | 0,1851 | 0,2033 | En iyi (doğrulamaya göre) |
| 5 | 0,1474 | 0,2151 | Hafif aşırı uydurma başlıyor |
| 9 | 0,1223 | 0,3210 | Aşırı uydurma |
| 12 | 0,1126 | 0,4974 | Kenarlarda patlama |

**Bunu AI'sız yazabilir misin?** Bir modelin eğitim RMSE'si 0,12 ve doğrulama RMSE'si 0,32 ise, bu oran aşırı uydurmanın bir ölçüsü olarak kullanılabilir mi? Hangi eşik değerinin üstünde bunu alarm sayarsın, ve neden bu eşiği tek başına bir sayıyla tanımlayamazsın?

### Örnek 4 (★★★): Sızıntı avı

**Adım 1 — Anla.** Bir ekip, 100 örnekli bir veri kümesinde 5000 özniteliği standartlaştırıp 20 özniteliği seçen ve ardından 5 katlı çapraz doğrulama yapan bir hat kurmuş. Sonuç yüksek görünüyor. Veri, 54.8'deki deneyde olduğu gibi rastgele üretildi; yani doğru değer yaklaşık 0,5. Hangi adım sızdırıyor?

**Adım 2 — Örnekle.** Hattın iki işlemi var: ölçekleme (`StandardScaler`) ve öznitelik seçimi (`SelectKBest`). İkisinin de tüm veriyle yapılması sızıntı olabilir. Ama hangisinin asıl sorun olduğunu bilmiyoruz; tahmin etmek yerine ayırmalıyız.

**Adım 3 — Kaba çöz.** Dört varyant kur: (1) ikisi de tüm veriyle, (2) yalnızca ölçekleme tüm veriyle, (3) yalnızca seçim tüm veriyle, (4) ikisi de pipeline içinde. Her varyantı 20 tohumda çalıştır ve ilk beş tohumun sonuçlarını bir tabloda tut.

**Adım 4 — Örüntü.** Varyant 1 ile 3 neredeyse aynı (0,879 ve 0,880); varyant 2 ile 4 neredeyse aynı (0,504 ve 0,502). Yani sızıntıyı seçim yaratıyor, ölçekleme değil. Bu beklenen bir sonuçtur: F istatistiği (ANOVA) her özniteliğin ölçeğinden bağımsızdır, dolayısıyla ölçekleme seçimin hangi öznitelikleri seçeceğini değiştirmez. Bu genel bir kural değil; ölçeklemenin sızıntısı başka modellerde ve verilerde daha büyük olabilir.

**Adım 5 — İyileştir.** Seçimi pipeline içine al. Ölçekleme de içeri alınabilir ve bu, hattın geri kalanını da temiz tutar. Programın dördüncü varyantı tam olarak budur.

```python
import numpy as np
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

def varyant(X, y, cv, olcek_tum, secim_tum):
    model = LogisticRegression(max_iter=1000)
    if olcek_tum:
        X = StandardScaler().fit_transform(X)
    if secim_tum:
        X = SelectKBest(f_classif, k=20).fit_transform(X, y)
        return cross_val_score(model, X, y, cv=cv).mean()
    adimlar = []
    if not olcek_tum:
        adimlar.append(StandardScaler())
    adimlar += [SelectKBest(f_classif, k=20), model]
    boru = make_pipeline(*adimlar)
    return cross_val_score(boru, X, y, cv=cv).mean()

```

```python
print("tohum  V1:hepsi  V2:olcek  V3:secim  V4:temiz")
ort = np.zeros(4)
for sd in range(20):
    rng = np.random.default_rng(sd)
    X = rng.normal(size=(100, 5000))
    y = np.repeat([0, 1], 50)
    rng.shuffle(y)
    cv = StratifiedKFold(5, shuffle=True, random_state=sd)
    r = [varyant(X, y, cv, True, True),     # ikisi de sizinti
         varyant(X, y, cv, True, False),    # yalnizca secim doğru
         varyant(X, y, cv, False, True),    # yalnizca olcek doğru
         varyant(X, y, cv, False, False)]   # ikisi de doğru
    ort += np.array(r) / 20
    if sd < 5:
        print("%5d   %.3f   %.3f   %.3f   %.3f" % (sd, *r))
print("ortalama (20 tohum):", np.round(ort, 3))
```

**Adım 6 — Doğrula.** Program çıktısı:

```term
$ python b54_08_ornek_sizinti.py
tohum  V1:hepsi  V2:olcek  V3:secim  V4:temiz
    0   0.900   0.510   0.880   0.510
    1   0.880   0.460   0.890   0.470
    2   0.830   0.550   0.830   0.560
    3   0.830   0.490   0.830   0.490
    4   0.930   0.580   0.930   0.560
ortalama (20 tohum): [0.879 0.504 0.88  0.502]
```

Kaynak tablosu: sahte doğruluk yaklaşık 0,88 (ikisi de sızıntılı), gerçek doğruluk yaklaşık 0,50 (ikisi de temiz). Fark, tamamen seçim adımının konumundan kaynaklanıyor. Bu, "sahte %88 → gerçek %50" farkını adım adım izlemenin en açık yoludur.

**Bunu AI'sız yazabilir misin?** Pipeline'a öznitelik seçimini koydun ama skor hâlâ şüpheli yüksek. Bu durumda bir sızıntı kaynağı hâlâ olabilir mi? Hiperparametre `k`'yı tüm veriye bakarak seçmek bunun bir örneği olabilir mi, ve bunu nasıl önlersin?

## Kendin Yap Projeleri

::: dikkat
Bu projelerde önce kendi tasarımını yap; yapay zekâ araçlarına, kendin bir taslak çıkarana kadar başvurma. Aşağıdaki "önerilen yaklaşım" bölümleri yalnızca bir ipucudur, tam çözüm değildir. Başarı kriterlerini tamamlamadan projeyi bitmiş sayma.
:::

### Proje 1 (★★): İlk ML projen, uçtan uca

**Amaç.** Scikit-learn'ün paketinde gelen `load_digits` veri setiyle (1797 örnek, 64 özellik, 10 sınıf, her biri 8×8 piksellik bir rakam görüntüsü) bu bölümün iş akışını baştan sona uygulamak. Hiçbir adımı kopyalamadan, kendi kararlarını gerekçelendirerek yap.

**Beklenen davranış.** Bir betik şu çıktıları üretmeli: veri kümesinin bölünme biçimi ve sınıf dağılımları; en az üç baseline (hep çoğunluk, rastgele oran ve bir basit kural); iki farklı model ailesi (ör. lojistik regresyon ve k-NN); 5 katlı çapraz doğrulama ortalaması ve standart sapması; test kümesinde yalnızca bir kez alınmış sonuçlar; ve bir karışıklık matrisiyle hata analizi.

**Önerilen yaklaşım.** Önce test kümesini kilitle ve tohumu kaydet. Baseline'ları ve iki modeli yalnızca eğitim kümesi üzerindeki çapraz doğrulamayla karşılaştır. Ölçekleyiciyi ve öznitelik seçimini pipeline içinde tut. Model seçtikten sonra test kümesini bir kez aç. Hata analizinde en çok karışan rakam çiftlerine bak. Son olarak bir model kartı yaz (54.12'deki alanlar).

**Başarı kriterleri.** (1) Test kümesi tek bir kez kullanılmış ve bunun kanıtı betikte var. (2) Seçilen model her iki baseline'ı dengeli doğrulukta geçmiş. (3) Çapraz doğrulama sonucu ortalama ± standart sapma olarak raporlanmış. (4) Betik iki kez çalıştırıldığında aynı sayıları üretiyor. (5) Model kartında sınırlamalar en az üç maddeyle yazılmış.

### Proje 2 (★★★): Sızıntı dedektifi

**Amaç.** Bir veri hattını (ölçekleme, eksik değer doldurma, öznitelik seçimi, örnek çoğaltma, zaman türevli bir öznitelik içeren) gözden geçirip her sızıntıyı bulan bir kontrol listesi ve bu kontrolleri otomatikleştiren bir kod yazmak.

**Beklenen davranış.** Verilen bir hat için her adımın hangi kümeye uygulandığını listeleyen bir rapor üretilsin. Rapor, her sızıntı şüphesi için bir kanıt (ör. "bu öznitelik tahmin anından sonra hesaplanıyor") ve düzeltilmiş hattın sonucunu içersin.

**Önerilen yaklaşım.** Hattaki her adım için tek bir soru sor: bu işlemin öğrendiği şey yalnızca eğitim kümesinden mi geliyor? Öznitelikler için ayrıca sor: bu değer tahmin anında biliniyor mu? Kodu okumak yerine `fit` çağrılarının kapsamını listeleyen küçük bir yardımcı yazabilirsin. Düzeltmeden önce ve sonra skorları yan yana koy.

**Başarı kriterleri.** (1) Beş farklı sızıntı türünün her biri için bir örnek ve kanıt bulunmuş. (2) Her sızıntı için sayısal etkisi (düzeltme öncesi ve sonrası skor) ölçülmüş. (3) Düzeltilmiş hattın skoru, gerçek sinyal yokken şans düzeyine yakın. (4) Kontrol listesi başka bir veri hattına da uygulanabilir biçimde yazılmış.

## Ek Alıştırmalar

Aşağıdaki problemler kademelidir. ★ olanlar kavramı yoklar, ★★ olanlar bir türetme ya da küçük bir kod ister, ★★★ olanlar birden çok konuyu birleştirir. Mülakat etiketli olanlar klasik sorulardır.

1. ★ Bir veri kümesinde 1000 örneğin 20'si pozitif. Her zaman negatif diyen modelin doğruluğu nedir, dengeli doğruluğu nedir? (Mülakat)
2. ★ Kare kayıp `Σ (y_i − c)²`'yi en küçük yapan sabit `c`'yi türevle bul. Bu sonuç regresyonda neden "ortalama" baseline'ını doğal kılar?
3. ★ 1000 örnekli bir veride 70/15/15 eğitim/doğrulama/test bölmesi yapıyorsun. Her kümede kaç örnek var? Sınıflar dengesizse katmanlı bölme yapılmazsa hangi sorun doğabilir?
4. ★ Her zaman damgalı örnekler için "son 7 günün ortalamasını" öznitelik olarak kullanıyorsun. Bu öznitelik hangi tarihte hesaplanmalı ki sızıntı olmasın?
5. ★★ 12 örnekli bir veri için `KFold(5)` kullanırsan parça boyutları nasıl dağılır? `np.array_split` davranışını ve sklearn'ün bunu nasıl yaptığını açıkla.
6. ★★ 54.6'daki polinom deneyinde derece 12'nin doğrulama hatasının neden patladığını kenar ekstrapolasyonuyla açıkla. Bu sorunu azaltmak için iki önlem öner.
7. ★★ Öznitelik olarak "servis kaydı açıldı mı" (0/1) kullanıyorsun, etiket "önümüzdeki 7 günde arıza". Bu öznitelik neden sızıntılı olabilir? Zaman hizalaması nasıl olmalı?
8. ★★ Lojistik regresyonda sklearn'ün amacını `n`'e bölünce gradyan terimi `w/(Cn)` oluyor. `C` çok büyüdüğünde (ceza zayıfladığında) bu terim neye yaklaşır? (Mülakat)
9. ★★ 54.8'deki sızıntı deneyinin öznitelik seçimi deneyini `k = 20` yerine `k = 5` ve `k = 100` ile tekrarla. Sızıntılı skorun `k` ile nasıl değişeceğini önce tahmin et, sonra ölç.
10. ★★★ Bir modelin doğruluğu %92, pozitif sınıf oranı %8. Modeli hangi baseline'larla karşılaştırmalısın ve hangi ölçütte geçmesi gerekir?
11. ★★★ Üç tohumda 0,91, 0,88 ve 0,93 veren bir model var; yeni modelin ortalaması 0,90. İyileşme var mı? Tohum sayısını ve belirsizliği nasıl raporlarsın? (Mülakat)
12. ★★★ 54.8'deki grup deneyini 40 kişi yerine 10 kişiyle tekrarla. Grup sızıntısının etkisi ve grup bölmenin tahmin belirsizliği nasıl değişir?

## Kod Okuma Egzersizi

Aşağıdaki kesitler, yerel olarak kurulu scikit-learn 1.8.0 paketinden (`sklearn/pipeline.py`) alındı. Kesitler birebir kopyadır; atlanan satırlar `...` ile işaretlenmiştir. Bazı satırlar yalnızca sayfaya sığması için bölünmüştür; ifadede değişiklik yoktur.

Birinci kesit `Pipeline._fit` yönteminin ana döngüsüdür (satır 527-528 ve 547-559). Döngü, son tahminci hariç her adımı sırayla çalıştırır.

```python
        for step_idx, name, transformer in self._iter(
            with_final=False, filter_passthrough=False
        ):
            ...
            X, fitted_transformer = fit_transform_one_cached(
                cloned_transformer,
                X,
                y,
                weight=None,
                message_clsname="Pipeline",
                message=self._log_message(step_idx),
                params=step_params,
            )
            # Replace the transformer of the step with the fitted
            # transformer. This is necessary when loading the
            # transformer from the cache.
            self.steps[step_idx] = (name, fitted_transformer)
        return X
```

İkinci kesit `Pipeline.fit` yönteminden alındı (satır 613 ve 621). Önce tüm adımlar `_fit` ile eğitilir, sonra son tahminci dönüştürülmüş eğitim verisiyle eğitilir.

```python
        Xt = self._fit(X, y, routed_params, raw_params=params)
        ...
                self._final_estimator.fit(Xt, y,
                    **last_step_params["fit"])
```

**Sorular — cevaplamadan geçme:**

1. `_fit` her dönüştürücüyü `clone` ile kopyalayarak eğitiyor (satır 539, `cloned_transformer`). Bir nesneyi iki kez `fit` etmenin bedeli nedir? Klonlama, çapraz doğrulamadaki katlar arasında hangi bilgi sızıntısını önler?
2. `fit_transform_one_cached` tek çağrıda hem öğrenmeyi hem dönüşümü yapar. `SelectKBest` gibi bir dönüştürücünün eğitim verisinde seçtiği sütunların test verisine nasıl uygulandığını, `transform` çağrısıyla birlikte açıkla.
3. `self.steps[step_idx] = (name, fitted_transformer)` satırı neden gerekli? Eğitilmiş dönüştürücünün yerine geçmezse, sonraki tahmin çağrısı ne kullanır?
4. `Pipeline.fit` son tahmincinin `fit(Xt, y)` ile çağrıldığını gösteriyor. `Xt`'nin hangi veriden üretildiğini ve bunun sızıntı açısından neden önemli olduğunu açıkla.
5. Kaynakta `_fit_transform_one` (satır 1471-1492), dönüştürücüde `fit_transform` yoksa `fit` ardından `transform` çağırır. Bu dal, sızıntı açısından `fit_transform` dalından farklı mı? Neden?
6. `cross_validate` her katta tahminciyi `clone(estimator)` ile yeniden kurar (`sklearn/model_selection/_validation.py`, satır 370-375). Bu ayrıntı, 54.8'deki `secim_sizintisi` deneyinin iki sonucunu nasıl açıklar?

## Bölüm Özeti

- Makine öğrenmesi, kuralı elle yazmak yerine örneklerden bir fonksiyon öğrenmektir; eğitim, kayıp fonksiyonunun en küçüğünü bulan bir optimizasyondur (Bölüm 49, 50, 51).
- ML kullanmamak bir başarısızlık değildir: kural yeterliyse, veri yoksa, hata maliyeti ve açıklanabilirlik gerekçesi ağırsa ya da dağılım izlenemiyorsa, daha basit bir çözüm tercih edilir.
- Problem çerçevelemede karar, girdi, çıktı, etiket kaynağı, hata maliyetleri ve metrik açıkça tanımlanır; vekil etiket ve etiket gürültüsü ayrıca kontrol edilir.
- Eksik uydurma ve aşırı uydurma, sapma–varyans dengesiyle açıklanır; eğitim hatası tek başına model seçmeye yetmez.
- Veri bölmesi, test kümesini kilitleyerek yapılır; katmanlı, zaman ve grup yapıları bölme biçimini belirler.
- Veri sızıntısı, bilgisi tahmin anında olmayan her şeyin eğitime girmesidir. Öznitelik seçimi tüm veriyle yapıldığında sahte %88 doğruluk, doğru kurulumda %50 çıkar.
- Baseline'ı geçmeyen model işe yaramaz; dengesiz sınıflarda doğruluk yanıltır, dengeli doğruluk ve karşılaştırma gerekir.
- Pipeline, ön işlemeyi eğitim kısmına bağlayarak sızıntıyı yapısal olarak önler; tohum, sürüm ve deney günlüğü tekrarlanabilirliği sağlar.
- Model kartı, yanlılık ve dağılım kayması, bir modelin nerede güvenilir olduğunu dürüstçe belgelemek için gereklidir; yüksek riskli sistemlerde insan karar yetkisi korunur.

**Sonraki bölümde:** Bölüm 55, ML için Kalkülüs ve Otomatik Türev ile devam ediyor. Bu bölümde lojistik regresyonun gradyanını kullanmadan yazdık; bir sonraki bölümde o gradyanın nasıl türetildiğini, zincir kuralını ve küçük bir otomatik türev motorunu sıfırdan göreceksin.

::: mulakat
1. Bir modelin eğitim hatası düşük, doğrulama hatası yüksekse bu ne anlama gelir? Hangi adımlarla bunu teşhis edersin?
2. Veri sızıntısı nedir? Ölçekleyiciyi tüm veriyle eğitmek neden sorundur ve bunu pipeline ile nasıl önlersin?
3. K-katlı çapraz doğrulama neyi ölçer? Hangi veri türlerinde yanıltıcı olabilir?
4. Zaman serisinde rastgele bölme neden yanlıştır? Doğru bölme nasıl olmalıdır?
5. Her zaman en sık sınıfı tahmin eden bir model %95 doğrulukla neden başarılı görünür ve sen hangi ölçütü kullanırsın?
6. Bias ve varyans nedir? Polinom derecesini artırdığında hangisi azalır, hangisi artar?
7. Bir savunma uygulamasında makine öğrenmesini kullanmamayı ne zaman seçersin? Bu kararı nasıl gerekçelendirirsin?
8. Test kümesini birçok kez kullanırsan ne olur? Bunu önlemek için hangi pratikleri uygularsın?
:::
