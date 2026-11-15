%% kisim_no: XVI
%% kisim_ad: ML Mühendisliği & Araştırma
%% bolum_no: 79
%% baslik: Makale Okuma & Araştırma Yöntemi

## Giriş: Okumak, yeniden kurmak, doğru kanıtlamak

Bu kitapta şimdiye kadar yüzlerce sonuç gördün. Bölüm 57'de bir sınıflandırıcının doğruluğunun nasıl ölçüleceğini, Bölüm 64'te bir eğitimin neden tutmadığını, Bölüm 77'de bir modelin üretimde neden bozulduğunu konuştuk. Her bölümün sonunda bir iddia vardı ve o iddia bir yerden geliyordu: ya bir makaleden, ya bir kütüphane belgesinden, ya da bizim kendi ölçümümüzden. Bu bölümün konusu, o iddiaları kendi başına okuyup sınayabilmektir.

Araştırma makalesi okumak, mühendislik işinin ayrılmaz parçasıdır. Savunma sanayiinde bir hedef takip algoritmasının, bir sensör füzyonu yönteminin ya da bir tespit modelinin yeni bir yöntemini ilk duyduğunda, o yöntem yayımlanmış bir makalede anlatılır. Bu makaleyi okuyup üç soruyu cevaplayabilmen gerekir: iddia ne, kanıt yeterli mi, ben bunu kendi verimde denediğimde aynı şey oluyor mu? Bu üçüncü soru bu bölümün asıl konusudur.

Bu bölümde dört şey yapacağız. Önce makaleyi verimli okumanın bir yöntemini (üç geçiş) öğreneceğiz. Sonra makalelerde sık görülen kırmızı bayrakları, yani güvenilmez sonuçların işaretlerini tanıyacağız. Üçüncüsü, bu bölümde yazdığımız istatistik araçlarıyla "iki yöntem gerçekten farklı mı?" sorusuna ölçülü cevap vermeyi kuracağız. Son olarak, kitabın önceki bölümlerinden birindeki bir iddiayı bağımsız olarak yeniden üreteceğiz. Yeniden üretme, bir araştırmacının en değerli alışkanlığıdır.

::: not
Bu bölümün tüm kodu Windows 11 üzerinde Python 3.12.10 ile çalıştırıldı. Kullanılan sürümler: torch 2.6.0 (yalnızca CPU), scikit-learn 1.8.0, scipy 1.17.1, numpy 2.3.5. GPU kullanılmadı; tüm eğitimler 4 iş parçacığıyla CPU'da koştu ve her koşu yaklaşık 1,5 saniye sürdü. Her sonucun tohumu koda yazılıdır, ham sonuçlar `engine/veri/b79_*.csv` dosyalarındadır. Sayılar bu koşuya aittir; başka bir donanımda son ondalık basamaklar değişebilir.
:::

## 79.1 Araştırma neden mühendislik için önemli

Mühendislikte bir yöntemi "biliyorum" demek, onu bir kez çalıştırıp işe yaradığını görmek demek değildir. Bir yöntemi bilmek, onun hangi koşullarda işe yaradığını, hangi koşullarda yaramadığını ve sonucun ne kadar güvenilir olduğunu bilmektir. Araştırma, bu bilginin üretildiği ve sınandığı süreçtir. Mühendis ise bu süreci tersine kullanır: hazır bir sonucu alır, kendi probleminde ne kadar geçerli olduğunu sınar, işe yarıyorsa uygular.

Mert'in hedefi bu iki becerinin birleşimidir: savunma sanayiinde gerçek sistemlere ML koymak, bu yüzden makale okuyup uygulayabilen bir mühendis olmak. Makalelerin sunduğu sonuçlar genellikle temiz koşullarda, seçilmiş veri kümelerinde ve en iyi tohumla ölçülür. Gerçek bir İHA görüntüsü, bozuk bir sensör ya da farklı bir hava koşulu o temizliği bozar. Bu boşluğu görmek, okumanın asıl değeridir.

Bölüm 57'de modelleri karşılaştırmanın anlamlılık sorusunu gördük, Bölüm 65'te eğitimi tekrarlanabilir hâle getirmeyi öğrendik. Bu bölüm bu iki bilgiyi bir araya getirir: bir makalenin sonucunu tekrarlanabilir biçimde yeniden üretmek ve bu sonucun şans olup olmadığını istatistikle sınamak.

## 79.2 Makale okuma protokolü: üç geçiş

Makaleyi baştan sona tek seferde okumak çoğu zaman verimsizdir. Keshav'ın 2007'de yayımlanan "How to read a paper" yazısı (genel bilgi) bunun yerine üç geçişli bir yöntem önerir. Her geçiş, bir öncekinin üstüne kurulur ve her geçişin sonunda kısa bir karar verilir: bu makale bana değerli mi, bir sonraki geçişe ihtiyacım var mı?

Birinci geçişte makaleyi haritalarsın. Başlığı, özeti, giriş bölümünün son paragrafını (katkı listesini genelde orada bulursun), şekillerini ve sonuç tablolarını okursun. Yirmi dakikayı geçmez. Bu geçişin sonunda makalenin hangi problemi çözdüğünü, hangi iddiayı öne sürdüğünü ve bu iddianın nasıl ölçüldüğünü bilmelisin.

İkinci geçişte yöntemi okursun. Veri, baseline (karşılaştırılan temel yöntem), ayarlar, deney düzeni ve hangi metriklerin raporlandığı burada yer alır. Bu geçiş bir ya da iki saat sürebilir ve makalenin kendisiyle birlikte kenara notlar almayı gerektirir.

Üçüncü geçişte ayrıntıya girersin: denklemleri türetirsin, ek bölümleri okursun, kod ve veri varsa onları incelersin ve en önemlisi, kendi ortamında yeniden üretip üretemeyeceğini düşünürsün. Bu geçiş günler sürebilir ama her makale için gerekmez. Sadece değerli bulduğun ve kullanmayı düşündüğün makaleye uygulanır.

| Geçiş | Ne okursun | Süre (kabaca) | Çıktı |
|---|---|---|---|
| 1. Haritalama | Başlık, özet, giriş sonu, şekiller, sonuç tabloları | 15–20 dk | İddia ve kanıtın tipi |
| 2. Yöntem | Veri, baseline, ayarlar, deney düzeni, metrikler | 1–2 saat | Sorular ve kırmızı bayraklar |
| 3. Ayrıntı | Denklemler, ek bölümler, kod, yeniden üretim | Günler | Yeniden üretim planı |

Şekil 79.1, bu üç geçişin birbirine nasıl bağlandığını ve her geçişin sonunda verilen kararı gösteriyor.

![Şekil 79.1: Makale okumanın üç geçişi ve her geçişin kararı](gorseller/b79_uc_gecis.png)

Bu yöntemin ana faydası, zamanı önemli olana harcamaktır. Birinci geçişte bir makalenin iddiası ve kanıtı yanlışsa, ikinci ve üçüncü geçişlere hiç girmeden bırakabilirsin. Bu, ilk okumada bir yazıyı baştan sona okuyup sonunda hiçbir şey hatırlamamanın en kolay çaresidir.

## 79.3 Bir makalenin anatomisi ve okuma notu

Bir araştırma makalesi, birbirine bağlı altı parçadan oluşur. Makaleyi okurken bu parçaları ayrı ayrı bulup not almak, dağınık bir metni yapılandırılmış bilgiye çevirir.

Birincisi **iddiadır (katkı)**: makalenin "şunu yaptık ve şu daha iyi" dediği cümledir. İkincisi **yöntemdir**: ne yapıldığı, nasıl yapıldığı. Üçüncüsü **deney düzenidir**: hangi veri, hangi bölme, kaç tohum, hangi metrik. Dördüncüsü **baseline**dır: karşılaştırılan basit yöntem. Beşincisi **ablation**dır: önerilen yöntemin hangi parçası sonucu taşıyor? Altıncısı **sınırlamalardır**: yazarların kendilerinin kabul ettiği ve kabul etmediği zayıflıklar.

Şekil 79.2 bu parçaların iddiaya nasıl bağlandığını gösteriyor. Her parça iddiayı destekleyen bir kanıt olmalı. Bir parça iddiayla bağlantılı değilse, o parça süs olabilir.

![Şekil 79.2: Bir makalenin parçaları ve iddiaya bağlantıları](gorseller/b79_makale_anatomi.png)

Okurken her parça için kendine beş soru sor. Bu sorular bir okuma notu şablonunu oluşturur:

1. Problem ne? (Hangi soruyu cevaplıyor, kime lazım?)
2. Katkı ne? (Önceki yöntemlerden farkı tek cümlede ne?)
3. Kanıt yeterli mi? (Hangi veri, kaç tohum, hangi baseline, hangi metrik?)
4. Neyi kontrol etmedi? (Hangi değişken sabit tutulmadı, hangi karşılaştırma yapılmadı?)
5. Ben nasıl test ederim? (Bu iddiayı kendi küçük veri kümemde sınamak için en az ne yapmalıyım?)

Beşinci soru bu bölümün en önemli sorusudur. Bir makalenin iddiasını kendi ortamında sınayacak planı yazamıyorsan, o makaleyi anlamamışsındır demektir. Okuma notunun sonunda bu beş sorunun cevapları bir sayfada toplanmış olmalı.

Bu bölümün devamında gösterdiğimiz uygulamada, makale okuma ile deney yapmayı birleştiriyoruz. Her iddiayı önce okuyup not alıyor, sonra sınıyoruz. Okumadan sınamak ya da sınamadan kabul etmek, iki yönde de hatalıdır.

## 79.4 Denklemi koda çevirmek

Makalelerdeki denklemler kısa ve yoğundur. Bir güncelleme kuralı üç satırda yazılabilir ama o üç satırın her bir terimi bir fikri taşır. Denklemi koda çevirmek, o fikri anlamanın en sağlam yoludur. Bu kitapta bunu defalarca yaptık: Bölüm 55'te zincir kuralını koda döktük, Bölüm 64'te Adam ve AdamW'nin güncelleme kurallarını NumPy'de gerçekledik.

Bunu iyi yapmak için üç alışkanlık yeterlidir. Birincisi, her sembolü koddaki bir değişkene bağla. Denklemde `η` varsa kodda `lr` olmalı, `λ` varsa `wd`. İkincisi, koda girmeden önce boyutları yaz: bir matris çarpımının iki tarafı uyuşuyor mu? Üçüncüsü, küçük bir girdiyle elle hesap yapıp kodun sonucunu karşılaştır. Bu üçüncü adım, Bölüm 64.12'de gördüğümüz PyTorch eşleşme testinin fikridir: iki gerçekleme aynı girdide aynı sonucu vermeli.

AdamW örneğinde, Bölüm 64.3'teki ayrım şuydu: L2 düzenlileştirmede ağırlık azaltma gradyana eklenir ve Adam'ın ölçeklemesinden geçer; AdamW'de ise ağırlık doğrudan `θ ← θ(1 − ηλ)` ile küçülür ve gradyan buna karışmaz. Bu iki satırın farkını anlamadan iki yöntemi karşılaştıran bir makaleyi okumak, sonucun nedenini yanlış yere bağlamak demektir.

## 79.5 Eleştirel okuma ve kırmızı bayraklar

Bir makalede sonuç ne kadar iyi görünürse görünsün, eleştirel okuyucu bazı işaretleri arar. Bu işaretlere kırmızı bayrak diyoruz; bayrak, sonucun yanlış olduğu anlamına gelmez, ama o sonucu daha dikkatle sınamayı gerektirir. Aşağıdaki tablo her bayrağı, kitabın kendi ölçümlerinden bir örnekle eşleştiriyor.

| Kırmızı bayrak | Belirti | Kitaptan örnek | Okurken sorulacak soru |
|---|---|---|---|
| Tek tohum | Tek koşu, "daha iyi" sonucu | Bölüm 64.4: RMSProp tek tohumla yanıltıcı olabilirdi; beş tohumda ortalama 0,9611, sapma ±0,0252 | Kaç tohum, sapma kaç? |
| Zayıf baseline | Karşılaştırılan yöntem ayarlanmamış | Bölüm 64.4: her optimizer kendi öğrenme oranı ızgarasıyla karşılaştırıldı | Baseline da iyi ayarlandı mı? |
| Test kümesinde ayar | Seçim ile raporlama aynı veride | Bölüm 57.10 ve bu bölümün Çözümlü Örnek 3'ü | Seçim hangi veride yapıldı? |
| Seçici raporlama | Tek metrik, kötü metrik gizli | Bölüm 64.8: etiket yumuşatma doğruluğu 0,9878'e çıkardı ama ECE'yi 0,11'e yükseltti | Diğer metrikler raporlandı mı? |
| Anlamlılık eksikliği | Fark var deniyor, belirsizlik yok | Bölüm 64.4: AdamW ile Adam arasındaki fark sapmalar içinde kaldı | Fark güven aralığının dışında mı? |
| Aşırı genelleme | Küçük deneyden büyük iddia | Bölüm 64.4: sonuç "küçük MLP ve veri kümesinde" geçerli | Kapsam neresi? |
| Sızıntı | Test bilgisi eğitime karışmış | Bölüm 54'te veri sızıntısı ve bölme disiplini | Ön işleme bölmeden önce mi yapıldı? |

Bu bayraklardan biri tek başına bir makaleyi çürütmez. Ama üç bayrak birden varsa, makalenin sonucunu ancak kendi yeniden üretimin ile kabul etmelisin. Bu bölümün en önemli öğretisi budur: sonuç, sınama olmadan bilgi değildir.

Bir ayrıntıyı daha vurgulayalım. Bölüm 64.4'teki tablo, ilk bakışta "en iyi optimizer AdaGrad" gibi bir sonuç veriyor. Ama tablonun yanındaki sapma değerlerine baktığında, AdaGrad'ın 0,9789 ile AdamW'nin 0,9744 arasındaki farkın bu sapmaların içinde kaldığını görürsün. Sıralamayı okumadan önce sapmayı oku.

## 79.6 İstatistik pratiği: çok tohum, eşleştirilmiş fark, bootstrap, düzeltme

Bu bölümde dört istatistik aracı kullanıyoruz. Hepsi Bölüm 49'da gördüğün hipotez testi, güven aralığı ve bootstrap fikirlerinin uygulamasıdır; burada onları derin bir kurama girmeden, bir araç olarak kuruyoruz.

Birincisi **çok tohum**tur. Bir yöntemin tek bir koşudaki skoru, tohumun şansını da taşır. Bu yüzden her yöntemi birden fazla tohumla çalıştırır ve ortalama ile sapmasını raporlarız. Kitapta genelde beş tohum kullandık; Deney 1'de bunun neden yeterli ya da yetersiz olduğunu göreceğiz.

İkincisi **eşleştirilmiş fark**tır. İki yöntemi aynı tohumla çalıştırırsan, ikisi de aynı başlangıç ağırlıklarını ve aynı mini-batch sırasını görür. Bu durumda iki skorun farkı, yöntemin etkisine daha yakın bir büyüklük olur ve bunu tek örneklem t testi ile sınarsın. Bağımsız iki kümenin Welch testi, tohumlar eşleşmediğinde kullanılır.

Eşleştirilmiş farkın t istatistiği şöyledir:

`t = ortalama(fark) / (sd(fark) / sqrt(n))`, serbestlik derecesi `n − 1`.

Üçüncüsü **bootstrap güven aralığı**dır (Bölüm 49'un yöntemi). Beş farkın ortalamasının güven aralığını bir dağılım varsayımı yapmadan, değerleri yeniden örnekleyerek tahmin ederiz: bir yeniden örnekte beş değeri yerine koyarak seçeriz, ortalamasını alırız, bunu on binlerce kez yaparız. Ortalamaların %2,5 ve %97,5 yüzdelikleri aralığın uçlarıdır.

Dördüncüsü **çoklu karşılaştırma düzeltmesidir**. Yirmi model karşılaştırırsan, gerçekte hiçbir fark olmasa bile en az birinin "anlamlı" çıkma olasılığı yüksektir. Bunu düzeltmek için iki yaygın yöntem var (genel bilgi). Bonferroni, her p değerini karşılaştırma sayısı `m` ile çarpar: `p × m < α`. Holm ise p değerlerini küçükten büyüğe sıralar; i-inci en küçük p için eşik `α / (m − i + 1)` olur ve bir değer reddedilemezse, daha büyükleri de reddedilmez. Holm, Bonferroni'den her zaman en az o kadar güçlüdür ve aynı hata garantisini verir.

Bu araçların hepsini tek bir ortak modülde topluyoruz. Modül, eğitim koşusunu, veri bölmesini, t testini, bootstrap'i ve Holm düzeltmesini içerir. Tüm deneyler bu modülü kullanır.

Aşağıdaki modül, veri hazırlığını, MLP'yi ve eğitim döngüsünü içerir. Veri, Bölüm 64'teki kurulumla aynıdır: `load_digits` kümesi (1797 örnek, 64 özellik, 10 sınıf), tabakalı bölmeyle %60 eğitim, %20 doğrulama, %20 test. Piksel değerleri 16'ya bölünerek 0–1 aralığına getirilir.

```python
# -*- coding: utf-8 -*-
"""Bolum 79 ortak yardimcilari: veri, MLP, egitim, istatistik.

Veri: load_digits, %60 egitim / %20 dogrulama / %20 test (katmanli).
Her koşu bir tohumla belirlenir: agirlik baslangici ve mini-batch
sirasi ayni tohumdan gelir. Test skoru yalnizca raporlama icin okunur.
"""
import os

os.environ["OMP_NUM_THREADS"] = "4"
os.environ["MKL_NUM_THREADS"] = "4"

import numpy as np
import torch
from torch import nn
from scipy import stats
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

torch.set_num_threads(4)
VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"


```

Aşağıdaki kısım MLP'yi ve eğitim döngüsünü içerir. `egit` fonksiyonu tek bir koşuyu yapar; tohum hem ağırlık başlangıcını hem de mini-batch sırasını belirler. Son epoch'taki model değerlendirilir, erken durdurma yoktur; bu, sonucu seçimden bağımsız tutar.

```python
def veri():
    X, y = load_digits(return_X_y=True)
    X = (X / 16.0).astype(np.float32)
    Xtr, Xg, ytr, yg = train_test_split(
        X, y, test_size=0.4, stratify=y, random_state=0
    )
    Xva, Xte, yva, yte = train_test_split(
        Xg, yg, test_size=0.5, stratify=yg, random_state=0
    )
    t = torch.tensor
    return (t(Xtr), t(ytr), t(Xva), t(yva), t(Xte), t(yte))


def mlp(bn=False, dropout=0.0):
    """Iki gizli katman, 128 birim, ReLU. BN/dropout istege bagli."""
    kat, d = [], 64
    for _ in range(2):
        kat.append(nn.Linear(d, 128))
        if bn:
            kat.append(nn.BatchNorm1d(128))
        kat.append(nn.ReLU())
        if dropout > 0:
            kat.append(nn.Dropout(dropout))
        d = 128
    kat.append(nn.Linear(d, 10))
    return nn.Sequential(*kat)


```

```python
def dogruluk(model, X, y):
    model.eval()
    with torch.no_grad():
        return (model(X).argmax(1) == y).float().mean().item()


def egit(seed, opt="adam", lr=3e-3, wd=0.0, bn=False, dropout=0.0,
         cosine=False, epochs=30, batch=32, D=None):
    """Bir koşu. Son epoch modeli değerlendirilir; erken durdurma yok.

    opt: "adam" (torch.optim.Adam, wd=0) ya da "adamw" (AdamW, wd=wd).
    Dönüş: (dogrulama_dogrulugu, test_dogrulugu).
    """
    if D is None:
        D = veri()
    Xtr, ytr, Xva, yva, Xte, yte = D
    torch.manual_seed(seed)
    model = mlp(bn=bn, dropout=dropout)
    if opt == "adam":
        o = torch.optim.Adam(model.parameters(), lr=lr)
    else:
        o = torch.optim.AdamW(model.parameters(), lr=lr,
                              weight_decay=wd)
    sched = None
    if cosine:
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(o, epochs)
    g = torch.Generator().manual_seed(seed)
    loss_fn = nn.CrossEntropyLoss()
```

Şimdi istatistik araçları. `t_testi` eşleştirilmiş farklar için t istatistiğini ve iki yönlü p değerini hesaplar. `bootstrap_gven` yüzdelik bootstrap güven aralığını verir. `holm` ise Holm düzeltmesini uygular: sıralı p değerlerini en büyük eşiğe kadar taşıyan kısa bir döngüdür.

```python
    n = len(Xtr)
    for _ in range(epochs):
        model.train()
        perm = torch.randperm(n, generator=g)
        for i in range(0, n, batch):
            idx = perm[i:i + batch]
            o.zero_grad()
            loss_fn(model(Xtr[idx]), ytr[idx]).backward()
            o.step()
        if sched is not None:
            sched.step()
    return dogruluk(model, Xva, yva), dogruluk(model, Xte, yte)


def t_testi(fark):
    """Tek ornek t testi: ortalama, t, iki yonlu p (scipy ile)."""
    fark = np.asarray(fark, dtype=float)
    n = len(fark)
    ort, sd = fark.mean(), fark.std(ddof=1)
    t = ort / (sd / np.sqrt(n))
    p = 2 * stats.t.sf(abs(t), df=n - 1)
    return ort, t, p


```

```python
def bootstrap_gven(x, B=10000, seed=0, a=0.05):
    """Ortalama icin yuzdelik bootstrap guven araligi (Bolum 49)."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    idx = rng.integers(0, len(x), size=(B, len(x)))
    ort = x[idx].mean(axis=1)
    return np.quantile(ort, [a / 2, 1 - a / 2])


def holm(p):
    """Holm duzeltmesi: en kucuk p'den basla, esik alpha/(m-k)."""
    p = np.asarray(p, dtype=float)
    m = len(p)
    sira = np.argsort(p)
    duz = np.empty(m)
    enb = 0.0
    for k, i in enumerate(sira):
        enb = max(enb, (m - k) * p[i])
        duz[i] = min(1.0, enb)
    return duz


def csv_yaz(ad, satirlar, basliklar):
    yol = os.path.join(VERI, ad)
    with open(yol, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(basliklar) + "\n")
        for s in satirlar:
            f.write(",".join(str(x) for x in s) + "\n")
    return yol
```

Bu modülün üç noktasına dikkat et. Birincisi, `egit` her çağrıda veriyi yeniden yüklemez; `D` parametresiyle aynı bölmeyi tekrar kullanır. Bu hem hızlıdır hem de deneylerin aynı veriyle koştuğunu garanti eder. İkincisi, `torch.manual_seed(seed)` ve ayrı bir `torch.Generator` aynı tohumla çağrıldığında aynı sonucu verir; bu, Bölüm 65'teki tekrarlanabilirlik kuralının uygulamasıdır. Üçüncüsü, `holm` fonksiyonu sıralamayı kendi içinde yapar ve sonuçları özgün sıraya geri yazar; böylece çağıran kod p değerlerinin sırasını değiştirmek zorunda kalmaz.

## 79.7 Tohum gürültüsü: aynı yöntemi iki kez koşmak

Bu bölümün en öğretici deneyi, hiçbir şeyi değiştirmeden yapılandır. Aynı MLP, aynı veri, aynı öğrenme oranı (Adam, 0,003), aynı 30 epoch ve batch 32. Tek fark tohum. Bu deneyin sorusu basit: tohum değiştiğinde test doğruluğu ne kadar oynuyor? Ve iki farklı tohumun "farkı" ne kadar büyük olabilir?

Bu soru önemlidir, çünkü makalelerdeki "yöntem A, yöntem B'den yüzde bir daha iyi" cümlesinin anlamı, bu tohum gürültüsüne göre ölçülmelidir. Tohum gürültüsü sıfır olmadığı sürece, tek bir koşudan gelen küçük bir fark bir şey söylemez.

Deney, 200 tohumla (0'dan 199'a) aynı koşuyu yapar ve her tohumun doğrulama ve test doğruluğunu kaydeder. Sonra bu tohumları çiftlere ayırır: (0,1), (2,3), ... ve her çiftin test farkını alır. Bir çiftin farkı, "aynı yöntemin iki koşusu" arasındaki farktır ve gerçek fark sıfırdır.

```python
# -*- coding: utf-8 -*-
"""Deney 1: tohum gurultusu. Ayni yontem, 200 tohum (0..199).

Hic degisiklik yok: her kosu ayni ayarlarla (Adam, lr=0,003,
30 epoch, batch 32). Tek fark tohum. Iki tohumlu kosularin farki
"sifir" olmali; degil. Bu fark, bir yontemin "daha iyi" sayilmasi
icin gereken esigi belirler.
"""
import numpy as np
from ortak79 import veri, egit, csv_yaz

D = veri()
satir = []
for s in range(200):
    va, te = egit(s, D=D)
    satir.append((s, "%.4f" % va, "%.4f" % te))
csv_yaz("b79_tohum_havuz.csv", satir, ["tohum", "dogrulama", "test"])

te = np.array([float(r[2]) for r in satir])
va = np.array([float(r[1]) for r in satir])
print("havuz n=200  test ort=%.4f  sd=%.4f"
      % (te.mean(), te.std(ddof=1)))
print("havuz n=200  dogr ort=%.4f  sd=%.4f"
      % (va.mean(), va.std(ddof=1)))
print("min=%.4f  max=%.4f  aralik=%.4f"
      % (te.min(), te.max(), te.max() - te.min()))

# Ayni yontemin iki kosusu: (0,1), (2,3), ... 100 cift
fark = te[0::2][:100] - te[1::2][:100]
print("100 cift farki: ort=%+.4f  sd=%.4f"
      % (fark.mean(), fark.std(ddof=1)))
print("|fark| >= 0.01 : %d / 100" % np.sum(np.abs(fark) >= 0.01))
print("|fark| >= 0.02 : %d / 100" % np.sum(np.abs(fark) >= 0.02))
print("en buyuk |fark| = %.4f" % np.abs(fark).max())
csv_yaz("b79_tohum_fark.csv",
        [(i, "%.4f" % f) for i, f in enumerate(fark)],
        ["cift", "fark"])
```

Aşağıdaki çıktı betiğin gerçek çıktısıdır.

```term
$ python t01_tohum.py
havuz n=200  test ort=0.9736  sd=0.0030
havuz n=200  dogr ort=0.9819  sd=0.0050
min=0.9639  max=0.9806  aralik=0.0167
100 cift farki: ort=+0.0001  sd=0.0044
|fark| >= 0.01 : 3 / 100
|fark| >= 0.02 : 0 / 100
en buyuk |fark| = 0.0112
```

Sonuçlar üç şey söylüyor. Birincisi, tek bir koşunun test doğruluğunun sapması yaklaşık 0,0030'dur, yani yüzde 0,3 puan. İkincisi, iki koşunun farkının sapması yaklaşık 0,0044'tür; bu, iki bağımsız gürültünün birleşimi için beklenen `√2 × 0,0030 ≈ 0,0042` değerine çok yakındır. Üçüncüsü ve en önemlisi, yüz çiftin üçünde fark bir yüzde puanı aşıyor, ama hiçbirinde iki puanı aşmıyor. Yani bu yöntem için, "bir puandan küçük fark gürültüdür" demek makul bir ilk tahmindir.

Şekil 79.3, yüz çiftin farkının dağılımını gösteriyor. Dağılım sıfır etrafında simetrik ve dar. Bir makalede "yüzde bir iyileşme" gördüğünde bunun bu gürültünün neresinde olduğunu sorman gerekir.

![Şekil 79.3: Aynı yöntemin iki koşusu arasındaki fark dağılımı (100 çift)](gorseller/b79_tohum_fark.png)

Bu deneyin bir uyarısı var. Gürültü ölçüsü bu veri kümesine, bu modele ve bu eğitim süresine aittir. Daha büyük bir modelde, farklı bir veri kümesinde ya da daha kısa bir eğitimde gürültü başka olabilir. Bu yüzden gürültüyü her projede yeniden ölçmek gerekir; bir kez ölçülmüş sayı başka bir projeye taşınmaz.

## 79.8 Güç analizi: kaç tohum yeterli?

Tohum gürültüsünü bildiğimizde bir sonraki soru doğal olarak gelir: gerçek bir farkı bulmak için kaç tohum gerekir? Bu soruya **güç analizi** (power analysis) cevap verir. Güç, gerçekte bir fark varken testin bunu "fark var" diye yakalama olasılığıdır. Pratikte sık hedeflenen değer yüzde seksen güçtür; yani gerçek bir fark olduğunda on kez denersen sekizinde yakalamak.

Bu deneyde sapma `σ = 0,0030` olarak Deney 1'den alınır. Her yöntemi bağımsız tohumlarla `n` kez koşuyoruz ve iki kümeyi Welch t testiyle karşılaştırıyoruz. Gerçek fark `δ` olarak üç değer deniyoruz: 0,5 puan, 1 puan ve 2 puan. Her `(n, δ)` çifti için dört bin simülasyon yapıyoruz; testin kaç kez "fark var" dediğini sayıyoruz. Bu sayı gücün Monte Carlo tahminidir.

Analitik bir yaklaşım da var. İki örneklemli, eşit varyanslı, iki yönlü bir test için grup başına gereken örnek sayısı yaklaşık şöyledir (genel bilgi):

`n ≈ 2 (z_(α/2) + z_β)² σ² / δ²`

Burada `z_(α/2) = 1,96` (α = 0,05), `z_β = 0,84` (güç = 0,80). Bu formül, Monte Carlo sonucunu doğrulamak için bir kontrol olarak kullanılacak.

```python
# -*- coding: utf-8 -*-
"""Deney 4: guc analizi (sentetik Monte Carlo, sigma olculmus).

Sigma, Deney 1'in 200 tohumlu havuzundan alinir (test dogrulugu sd).
Iki yontem, bagimsiz tohum kumeleriyle (n tohum her biri), Welch
t testi, alfa=0,05. Her (n, delta) icin 4000 simulasyon: gercek
fark delta iken testin kac kez "fark var" dedigi = guc.
Analitik n icin: n = 2 (z_a/2 + z_b)^2 sigma^2 / delta^2
(z_b icin 0,84 alinir).
"""
import numpy as np
from scipy import stats
from ortak79 import csv_yaz, VERI
import os

pool = np.genfromtxt(os.path.join(VERI, "b79_tohum_havuz.csv"),
                     delimiter=",", skip_header=1, usecols=2)
sigma = pool.std(ddof=1)
print("sigma (test sd, n=200) = %.4f" % sigma)

NS = [2, 3, 5, 10, 20]
DELTAS = [0.005, 0.010, 0.020]
SIM = 4000
rng = np.random.default_rng(79)
satir = []
for d in DELTAS:
    z = stats.norm.ppf(0.975) + stats.norm.ppf(0.80)
    nana = 2 * z ** 2 * sigma ** 2 / d ** 2
    print("delta=%.3f  analitik n/grup = %.1f" % (d, nana))
    for n in NS:
        a = rng.normal(0.0, sigma, size=(SIM, n))
        b = rng.normal(d, sigma, size=(SIM, n))
        p = stats.ttest_ind(b, a, axis=1, equal_var=False).pvalue
        guc = np.mean(p < 0.05)
        print("  n=%2d  guc=%.3f" % (n, guc))
        satir.append((d, n, "%.3f" % guc, "%.1f" % nana))
csv_yaz("b79_guc.csv", satir, ["delta", "n", "guc", "n_analitik"])
```

```term
$ python t04_guc.py
sigma (test sd, n=200) = 0.0030
delta=0.005  analitik n/grup = 5.5
  n= 2  guc=0.084
  n= 3  guc=0.268
  n= 5  guc=0.625
  n=10  guc=0.940
  n=20  guc=0.999
delta=0.010  analitik n/grup = 1.4
  n= 2  guc=0.229
  n= 3  guc=0.764
  n= 5  guc=0.996
  n=10  guc=1.000
  n=20  guc=1.000
delta=0.020  analitik n/grup = 0.3
  n= 2  guc=0.579
  n= 3  guc=0.999
  n= 5  guc=1.000
  n=10  guc=1.000
  n=20  guc=1.000
```

Sonuçları iki şekilde okuyabilirsin. Birincisi, `δ = 0,005` (yarım puan) için analitik gereksinim grup başına yaklaşık 5,5 tohumdur; Monte Carlo sonucu n = 5'te güç 0,625, n = 10'da 0,940 çıkıyor. Yani beş tohum, yarım puanlık bir farkı bulmak için yetmez; on tohum gerekir. İkincisi, `δ = 0,01` (bir puan) için beş tohum güçlü sayılır (0,996). Bu, tohum sayısının tasarım kararı olduğunu gösterir: ne kadar küçük bir farkı arıyorsan o kadar çok tohum gerekir.

Şekil 79.4, güç eğrilerini gösteriyor. Eğrilerin her biri `n` arttıkça yukarı kayar ve bir eşik olan yüzde seksene değer. Bu eşiği geçmek için gereken tohum sayısı, aradığın farkın büyüklüğüne bağlıdır.

![Şekil 79.4: Tohum sayısına göre güç (σ = 0,0030, üç gerçek fark)](gorseller/b79_guc_egrisi.png)

Bu analizin iki sınırlaması var. Birincisi, simülasyon normal dağılım varsayar. Gerçek tohum dağılımı küçük örneklerde çarpık olabilir; Deney 1'in 200 değeri normale yakın görünüyor, ama bu bir kanıt değil. İkincisi, burada bağımsız tohum kümeleri varsayıldı. Eşleştirilmiş tasarımda (aynı tohumlar iki yöntemde) gerekli tohum sayısı daha az olabilir, çünkü tohum gürültüsünün bir kısmı iki koşuda ortak kalır. Bu avantajdan yararlanmak istiyorsan, eşleştirilmiş farkın sapmasını ayrıca ölçmelisin.

## 79.9 Çoklu karşılaştırma: yirmi testte kaç yanlış alarm?

Diyelim ki yirmi yeni bir eğitim ayarı denedin ve her birini baz ayarla karşılaştırdın. Her karşılaştırma için p değerine bakıp "p < 0,05 ise fark var" diyorsun. Gerçekte hiçbir ayar işe yaramıyor olsa bile, en az birinin "anlamlı" çıkma olasılığı yüksektir. Bu, bir karşılaştırma için beşte birin altında olan hata oranının, yirmi karşılaştırmada birikmesidir.

Bu deneyde, tüm yirmi karşılaştırmanın gerçekte fark olmadığını (H0 doğru) varsayıyoruz. Her karşılaştırma beş tohumla yapılıyor ve tohum sapması `σ = 0,0030`. Üç yöntem karşılaştırıyoruz: hiçbir düzeltme yok (ham), Bonferroni ve Holm. Her deneyde en az bir "anlamlı" sonuç çıkma olasılığına bakıyoruz; bunu ailenin hata oranı (FWER, family-wise error rate) olarak adlandırıyoruz. Üç bin deney yapıyoruz.

```python
# -*- coding: utf-8 -*-
"""Deney 5: coklu karsilastirma. Gercek fark YOK (H0 dogru).

20 model, her biri baz modelle (n=5 tohum) karsilastiriliyor: 20 test.
Sigma Deney 1'den. 3000 deney; her deneyde 20 p degeri uretilir.
Ucu olculen sey: en az bir "anlamli" sonuc cikma olasiligi (FWER).
Holm ve Bonferroni duzeltmesi ile karsilastirma.
"""
import os
import numpy as np
from scipy import stats
from ortak79 import csv_yaz, VERI, holm

pool = np.genfromtxt(os.path.join(VERI, "b79_tohum_havuz.csv"),
                     delimiter=",", skip_header=1, usecols=2)
sigma = pool.std(ddof=1)
M, N, R = 20, 5, 3000
rng = np.random.default_rng(790)

```

```python
ham = bon = hol = 0
toplam = {"ham": 0, "bon": 0, "holm": 0}
for _ in range(R):
    base = rng.normal(0.0, sigma, N)
    p = np.array([
        stats.ttest_ind(rng.normal(0.0, sigma, N), base,
                        equal_var=False).pvalue for _ in range(M)])
    ham += np.any(p < 0.05)
    bon += np.any(p * M < 0.05)
    hol += np.any(holm(p) < 0.05)
    toplam["ham"] += np.sum(p < 0.05)
    toplam["bon"] += np.sum(p * M < 0.05)
    toplam["holm"] += np.sum(holm(p) < 0.05)

print("sigma=%.4f  M=%d  n=%d  R=%d" % (sigma, M, N, R))
print("FWER ham     = %.3f" % (ham / R))
print("FWER Bonf.   = %.3f" % (bon / R))
print("FWER Holm    = %.3f" % (hol / R))
print("ort. yanlis alarm (ham) = %.2f" % (toplam["ham"] / R))
csv_yaz("b79_coklu.csv",
        [("ham", "%.4f" % (ham / R), "%.3f" % (toplam["ham"] / R)),
         ("bonferroni", "%.4f" % (bon / R),
          "%.3f" % (toplam["bon"] / R)),
         ("holm", "%.4f" % (hol / R), "%.3f" % (toplam["holm"] / R))],
        ["duzeltme", "fwer", "ort_yanlis_alarm"])
```

```term
$ python t05_coklu.py
sigma=0.0030  M=20  n=5  R=3000
FWER ham     = 0.378
FWER Bonf.   = 0.028
FWER Holm    = 0.028
ort. yanlis alarm (ham) = 0.91
```

Ham düzeltmesiz sonuçta her üç deneyden birinde en az bir yanlış "anlamlı" sonuç çıkıyor (FWER 0,378) ve deney başına ortalama 0,91 yanlış alarm var. Bağımsız yirmi test için teorik değer `1 − 0,95²⁰ ≈ 0,64` olurdu; burada daha düşük çıkmasının sebebi, yirmi karşılaştırmanın hepsinin aynı baz modeli paylaşması ve sonuçların birbiriyle bağımlı olmasıdır. Bu bağımlılık, hata oranını bağımsız durumdan daha düşük tutar ama yine de kabul edilemeyecek kadar yüksek bırakır.

Bonferroni ve Holm her ikisi de FWER'ı 0,028'e indiriyor, yani nominal 0,05'in altında. Bonferroni tutucudur: her p değerini yirmiyle çarpar. Holm bunu sıralı bir eşikle yapar, bu yüzden Bonferroni'den daha güçlüdür; bu deneyde iki yöntemin sonucu aynı çıktı, çünkü gerçek fark yoktu ve p değerlerinin çoğu zaten çok büyüktü. Fark, gerçek bir etki olduğunda ortaya çıkar: Holm, büyük etkileri Bonferroni'den daha fazla yakalar.

Şekil 79.5 aynı üç sayıyı iki farklı biçimde gösteriyor. Soldaki panelin ekseni 0,0275 ile 0,0285 arasında kesilmiş. Bu eksenle ham yöntemin 0,378'lik çubuğu çerçevenin dışında kalıyor, Bonferroni ve Holm ise 0,028'de eşit olmalarına rağmen ayrı ve farklı yükseklikte görünüyor gibi okunabiliyor. Sağdaki panel sıfırdan başlıyor, üç değeri sayılarıyla gösteriyor ve alfa çizgisini ekliyor. Bu karşılaştırma, grafik seçiminin bir sonucu nasıl abarttığını gösterir; bölüm 79.13'te bu ilkeye geri döneceğiz.

![Şekil 79.5: Üç düzeltme yönteminde FWER: kesik eksenli (kötü) ve sıfırdan (iyi) gösterim](gorseller/b79_coklu_karsilastirma.png)

## 79.10 Yeniden üretim vaka çalışması: Bölüm 64.4 iddiası

Yeniden üretim, bir sonucu başkasının kodu ya da verisi olmadan, yalnızca yazılı tarifinden tekrar elde etmektir. Makalelerde bu kolay değildir; birçok makale tarifi eksik bırakır. Bu bölümde kitabın kendi iddialarından birini seçtik: Bölüm 64.4'teki Adam ve AdamW karşılaştırması.

Bölüm 64.4'ün iddiası şuydu: "Doğrulamada en yüksek skoru veren AdamW, testte de Adam'dan biraz yüksek çıktı; ama bu fark sapmalar içinde kalıyor." Bu cümlenin iki parçası var. Birincisi, AdamW'nin testte Adam'dan yüksek olması (yön). İkincisi, farkın sapmalar içinde kalması (belirsizlik). Yeniden üretimin amacı her iki parçayı da sınamaktır.

Kurulumu Bölüm 64.4'ün anlatımından aldık; o bölümün kodunu kopyalamadık. Piksel ölçeği (16'ya bölme) 64.4'ün anlatımında yazılı değildi; bunu Bölüm 64'ün veri tanımından aldık ve burada belirttik. Veri `load_digits`, %60/%20/%20 tabakalı bölme; ağ iki gizli katmanlı, 128 birimli ReLU MLP; 30 epoch, batch 32. Öğrenme oranı, `1e-4`'ten `1e-1`'e yedi değerlik ızgaradan, yalnızca doğrulamada tohum 10, 11, 12 ile seçiliyor. Seçilen lr ile test kümesi tohum 0, 1, 2, 3, 4'te ölçülüyor. Eşleştirilmiş fark, aynı tohumdaki AdamW eksi Adam.

Metin, AdamW için ağırlık azaltma katsayısını 0,01 olarak veriyor; Adam için ağırlık azaltma yok. Bu yorum bizim kurulumumuza yansıtıldı.

```python
# -*- coding: utf-8 -*-
"""Deney 2: Bolum 64.4 iddiasinin yeniden uretimi.

Iddia (Bolum 64.4, metinden): "Dogrulamada en yuksek skoru veren
AdamW, testte de Adam'dan biraz yuksek cikti; ama bu fark sapmalar
icinde kaliyor."

Kurulum Bolum 64.4 anlatimindan alindi (piksel olcegi 1/16 icin
Bolum 64 veri tanimi): load_digits, %60/%20/%20 katmanli bolme,
2 gizli katman x 128 ReLU, 30 epoch, batch 32. Ogrenme orani
1e-4 ... 1e-1 izgarasindan, yalnizca dogrulamada (tohum 10,11,12)
secilir. Secilen lr ile test kumesi tohum 0..4'te olculur.
Eslestirilmis fark: ayni tohumda AdamW - Adam.
"""
import numpy as np
from ortak79 import veri, egit, csv_yaz, t_testi, bootstrap_gven

D = veri()
LRS = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1]
SECIM = [10, 11, 12]
TEST = [0, 1, 2, 3, 4]

AYAR = {
    "Adam": dict(opt="adam", wd=0.0),
    "AdamW": dict(opt="adamw", wd=0.01),
}

```

```python
secilen = {}
print("Adim 1: lr secimi (yalnizca dogrulama, tohum 10-12)")
for ad, a in AYAR.items():
    skor = {}
    for lr in LRS:
        v = [egit(s, lr=lr, D=D, **a)[0] for s in SECIM]
        skor[lr] = np.mean(v)
        print("  %-6s lr=%-7g dogr=%.4f" % (ad, lr, skor[lr]))
    secilen[ad] = max(skor, key=skor.get)
    print("  secim %-6s lr=%g" % (ad, secilen[ad]))

print("Adim 2: test (tohum 0-4, secilen lr)")
test = {ad: [] for ad in AYAR}
for ad, a in AYAR.items():
    for s in TEST:
        test[ad].append(egit(s, lr=secilen[ad], D=D, **a)[1])
    x = np.array(test[ad])
    print("  %-6s test ort=%.4f sd=%.4f"
          % (ad, x.mean(), x.std(ddof=1)))

fark = np.array(test["AdamW"]) - np.array(test["Adam"])
ort, t, p = t_testi(fark)
gl, gh = bootstrap_gven(fark)
print("fark (AdamW-Adam) ort=%+.4f  t=%.3f  p=%.3f" % (ort, t, p))
print("bootstrap %%95 GA: [%+.4f, %+.4f]" % (gl, gh))

satir = []
for i, s in enumerate(TEST):
    satir.append((s, "%.4f" % test["Adam"][i],
                  "%.4f" % test["AdamW"][i], "%.4f" % fark[i]))
csv_yaz("b79_yeniden.csv", satir,
        ["tohum", "adam_test", "adamw_test", "fark"])
```

```term
$ python t02_yeniden.py
Adim 1: lr secimi (yalnizca dogrulama, tohum 10-12)
  Adam   lr=0.0001  dogr=0.9174
  Adam   lr=0.0003  dogr=0.9647
  Adam   lr=0.001   dogr=0.9684
  Adam   lr=0.003   dogr=0.9842
  Adam   lr=0.01    dogr=0.9833
  Adam   lr=0.03    dogr=0.9582
  Adam   lr=0.1     dogr=0.8180
  secim Adam   lr=0.003
  AdamW  lr=0.0001  dogr=0.9174
  AdamW  lr=0.0003  dogr=0.9638
  AdamW  lr=0.001   dogr=0.9684
  AdamW  lr=0.003   dogr=0.9851
  AdamW  lr=0.01    dogr=0.9842
  AdamW  lr=0.03    dogr=0.9369
  AdamW  lr=0.1     dogr=0.8357
  secim AdamW  lr=0.003
Adim 2: test (tohum 0-4, secilen lr)
  Adam   test ort=0.9739 sd=0.0025
  AdamW  test ort=0.9744 sd=0.0030
fark (AdamW-Adam) ort=+0.0006  t=0.408  p=0.704
bootstrap %95 GA: [-0.0017, +0.0033]
```

Önce karşılaştırma tablosu. Kitabın 64.4 tablosundaki değerler ile bizim koşumuzun değerleri şöyle:

| Yöntem | Seçilen lr | Kitap (test, 5 tohum) | Bu yeniden üretim (test, 5 tohum) |
|---|---|---|---|
| Adam | 0,003 | 0,9739 ± 0,0025 | 0,9739 ± 0,0025 |
| AdamW (wd 0,01) | 0,003 | 0,9744 ± 0,0030 | 0,9744 ± 0,0030 |

Sayılar ondalık dördüncü basamağa kadar aynı çıktı. Bu güçlü bir işarettir ama kanıt değildir. Metindeki protokol, sonucu büyük ölçüde belirliyor olabilir: aynı veri bölmesi, aynı ağ, aynı tohumlar ve aynı lr seçimi, aynı sayıları üretir. Kitabın kodunun bizimkiyle birebir aynı olduğunu bilmiyoruz (mini-batch sırasını nasıl ürettiği gibi ayrıntılar metinde yok). Bu yüzden bu eşleşmeyi "tarif yeterince tam" olarak okumalıyız, "kod doğru" olarak değil.

Şimdi iddianın iki parçasına bakalım. Yön: AdamW ortalama olarak 0,0006, yani altı binde bir puan kadar yüksek. Belirsizlik: eşleştirilmiş farkın t değeri 0,408, serbestlik derecesi 4, iki yönlü p değeri 0,704. Bootstrap %95 güven aralığı `[−0,0017, +0,0033]`, yani yaklaşık `[−0,17; +0,33]` yüzde puan. Aralık sıfırı içeriyor.

Şekil 79.6, beş tohumun her biri için AdamW eksi Adam farkını ve güven aralığını gösteriyor. Tohum 0'da fark negatif (−0,28 puan), tohum 4'te pozitif (+0,56 puan), diğerleri sıfır. Bu dağılım, iddianın "sapmalar içinde" ifadesiyle uyumlu.

![Şekil 79.6: Bölüm 64.4 iddiasının yeniden üretimi: tohum başına AdamW eksi Adam](gorseller/b79_yeniden_uretim.png)

Sonuç: iddianın "fark sapmalar içinde kalıyor" kısmı bu yeniden üretimde destekleniyor. "Biraz yüksek" kısmı da yön olarak tutuyor, ama bu yönü istatistiksel olarak sağlam bir biçimde ayırt edemiyoruz. Bu iki sonuç farklı şeylerdir: "fark yok" demiyoruz, "bu deneyle fark ayırt edilemiyor" diyoruz.

Bu deneyin dürüst sınırları da var. Beş tohum küçük bir örneklemdir; Deney 1 ve 4 bize göstermişti ki yarım puanlık farkı bulmak için on tohum gerekir. Dolayısıyla "AdamW ile Adam arasında fark yoktur" diyebilmek için çok daha fazla tohum gerekir. Ayrıca Bölüm 64.4'teki RMSProp sonucunu bu koşuda yeniden üretmedik; onun sapması (±0,0252) tek bir kötü tohumdan geliyor olabilir ve bunu sınamak yeni bir deney gerektirir. Bu, Kendin Yap Projesi 1'in konusu.

## 79.11 Ablation tasarımı: hangi bileşen sonucu taşıyor?

Ablation, bir sistemden bir bileşeni çıkarıp sonucun ne kadar değiştiğine bakmaktır. Makalelerde önerilen yöntemin birkaç bileşeni olur ve yazar her birinin katkısını göstermek ister. Ablation olmadan bir makalenin "tüm bileşenler birlikte iyi çalışıyor" demesi ile "şu bileşen sonucu taşıyor" demesi arasında fark vardır; ikincisi çok daha güçlü bir iddiadır.

En basit ablation, tek bileşen çıkarmaktır: tam modelden bir bileşeni çıkar, sonucu ölç. Bu yaklaşımın bir eksiği var: bileşenler birbiriyle etkileşebilir. İki bileşenin birlikte yaptığı etki, tek tek yaptıklarının toplamından farklı olabilir. Bu yüzden **faktöriyel tasarım** daha güçlüdür: her bileşenin açık ve kapalı olduğu tüm kombinasyonları koşarsın. Üç bileşen için bu `2³ = 8` koşuldur.

Bu deneyde üç bileşen seçtik: BatchNorm (BN), dropout (oranı 0,2, DO) ve kosinüs öğrenme oranı takvimi (COS). Her kombinasyon beş tohumla koşuldu. Raporlanan sayı test doğruluğu; ama dikkat: bu deneyde seçim yapılmadı, sekiz koşulun hepsi raporlandı. Gerçek bir çalışmada bileşen seçimi doğrulama ile yapılmalı, test yalnızca son raporda kullanılmalıdır.

Ana etki, bir bileşenin açık olduğu koşulların ortalamasından, kapalı olduğu koşulların ortalamasını çıkarmaktır. Bunu tohum başına hesaplarız, böylece beş değer elde ederiz ve aynı t mantığıyla güven aralığını kurarız.

```python
# -*- coding: utf-8 -*-
"""Deney 3: 2x2x2 faktoriyel ablation.

Uc bilesen: BN (BatchNorm), DO (dropout 0,2), COS (kosinus takvimi).
Sekiz kosul x bes tohum (0..4). Tohum basina ana etki:
  etki_A(s) = ortalama(A acik kosullar) - ortalama(A kapali kosullar)
Ana etkinin %95 guven araligi, bes tohumluk t dagilimi ile.
Ablation burada secim icin degil, bilesenin katkisini gormek icin.
"""
import itertools
import numpy as np
from scipy import stats
from ortak79 import veri, egit, csv_yaz

D = veri()
TOHUM = [0, 1, 2, 3, 4]
KOSUL = list(itertools.product([0, 1], repeat=3))  # (BN, DO, COS)
AD = ["BN", "DO", "COS"]

# sonuc[k][s] = test dogrulugu
sonuc = {}
for k in KOSUL:
    sonuc[k] = []
    for s in TOHUM:
        _, te = egit(s, lr=3e-3, bn=bool(k[0]), dropout=0.2 * k[1],
                     cosine=bool(k[2]), D=D)
        sonuc[k].append(te)
    x = np.array(sonuc[k])
    h = stats.t.ppf(0.975, df=len(x) - 1)
    h = h * x.std(ddof=1) / np.sqrt(len(x))
    tag = "+".join(a for a, v in zip(AD, k) if v) or "temel"
    print("%-12s test=%.4f  +-GA %.4f  (sd %.4f)" % (
        tag, x.mean(), h, x.std(ddof=1)))

```

```python
print("Ana etkiler (tohum basina, 5 tohum):")
satir = []
for k in KOSUL:
    satir.append(("+".join(a for a, v in zip(AD, k) if v) or "temel",
                  k[0], k[1], k[2],
                  "%.4f" % np.mean(sonuc[k])))
csv_yaz("b79_ablation.csv", satir,
        ["kosul", "BN", "DO", "COS", "test_ort"])

for j, a in enumerate(AD):
    ac = [k for k in KOSUL if k[j] == 1]
    kap = [k for k in KOSUL if k[j] == 0]
    etki = np.array([
        np.mean([sonuc[k][s] for k in ac]) -
        np.mean([sonuc[k][s] for k in kap])
        for s in range(len(TOHUM))])
    ort = etki.mean()
    h = stats.t.ppf(0.975, df=4) * etki.std(ddof=1) / np.sqrt(5)
    print("%-4s etki=%+.4f  %%95 GA [%+.4f, %+.4f]" % (
        a, ort, ort - h, ort + h))
```

```term
$ python t03_ablation.py
temel        test=0.9739  +-GA 0.0031  (sd 0.0025)
COS          test=0.9761  +-GA 0.0019  (sd 0.0015)
DO           test=0.9756  +-GA 0.0057  (sd 0.0046)
DO+COS       test=0.9783  +-GA 0.0015  (sd 0.0012)
BN           test=0.9839  +-GA 0.0079  (sd 0.0063)
BN+COS       test=0.9872  +-GA 0.0052  (sd 0.0042)
BN+DO        test=0.9828  +-GA 0.0045  (sd 0.0036)
BN+DO+COS    test=0.9878  +-GA 0.0031  (sd 0.0025)
Ana etkiler (tohum basina, 5 tohum):
BN   etki=+0.0094  %95 GA [+0.0052, +0.0137]
DO   etki=+0.0008  %95 GA [-0.0016, +0.0033]
COS  etki=+0.0033  %95 GA [+0.0029, +0.0037]
```

Sonuçlar. BatchNorm'un ana etkisi yaklaşık +0,94 puan ve güven aralığı `[+0,52; +1,37]` puan; yani bu etki beş tohumda da yeterince tutarlı. Kosinüs takvimi +0,33 puan, aralık `[+0,29; +0,37]`. Dropout'un ana etkisi +0,08 puan ve aralık sıfırı içeriyor; bu veri kümesinde ve bu eğitim süresinde dropout bir etki yapmıyor. Bunu "dropout işe yaramaz" diye genellemek yanlış olur; sadece bu kurulumda ayırt edilemedi.

Şekil 79.7, sekiz koşulun ortalamasını sıralı bir çubuk grafikte gösteriyor. En yüksek iki koşul BN içerenlerdir. Eksen 0,96'dan başlıyor; bu, sıfırdan başlamanın bu tür bir ölçüde gereksiz olduğu durumdur, ama farkları görünür kılmak için yeterli. Bu grafikte sayılar çubukların ucunda yazılıdır, böylece okur farkı tahmin etmek zorunda kalmaz.

![Şekil 79.7: 2x2x2 ablation: sekiz koşulun ortalama test doğruluğu (5 tohum)](gorseller/b79_ablation.png)

Bu tasarımın sınırları da açık olmalı. Beş tohum ve üç bileşen küçük bir deneydir; etkileşimleri (örneğin BN ile COS'un birlikte yaptığı şeyi) ayrıca raporlamadık, sadece ana etkileri verdik. Ayrıca bu ablation'ın bir "genel bilgi" değeri yok: sonuçlar bu küçük ağa ve bu veri kümesine aittir. Büyük bir ağda BatchNorm'un etkisi çok farklı olabilir.

## 79.12 Seçici raporlama: test kümesinde seçimin bedeli

Bu bölümde en çok karşılaşacağın hata, yirmi aday arasından en iyisini seçip onun test skorunu raporlamaktır. Seçim test kümesinde yapıldığında, raporlanan skor iyimser bir tahmindir: en iyi aday, gerçekten iyi olduğu kadar, şans olarak da yüksek skor almış olabilir.

Bu deney bunu gösteriyor. Havuzdan (Deney 1'in 200 tohumu) iki kümeyi ayırdık. İlk yüz tohum, yirmi "konfigürasyona" beşer tohum olarak dağıtıldı; bu kümeye seçim kümesi diyoruz. Son yüz tohum ise taze tohumlar olarak aynı yirmi konfigürasyona beşer beşer karşılık geliyor. Tüm yirmi konfigürasyon aynı yöntemdir, yani gerçek fark sıfırdır.

Üç şey karşılaştırıyoruz: (a) seçim kümesinde test ortalamasına göre en iyi konfigürasyonun skoru, (b) aynı konfigürasyonun taze tohumlardaki skoru, (c) doğrulama ortalamasına göre seçilen konfigürasyonun taze test skoru.

```python
# -*- coding: utf-8 -*-
"""Deney 6: test kumesinde secim (secici raporlama).

Havuzdan (Deney 1, tohum 0..199) iki kume alinir:
  - Secim kumesi: tohum 0..99, 20 "konfigurasyon" x 5 tohum.
  - Taze kume:    tohum 100..199, ayni 20 gruba karsilik gelen 5'erli.
Hepsi AYNI yontem: 20 konfigurasyon arasinda gercek fark yok.

(a) Test ortalamasina gore en iyisi secilip "raporlanirsa" ne olur?
(b) Ayni grubun taze tohumlardaki testi ne veriyor?
(c) Dogrulamaya gore secilen grubun testi ne veriyor?
"""
import os
import numpy as np
from ortak79 import csv_yaz, VERI

pool = np.genfromtxt(os.path.join(VERI, "b79_tohum_havuz.csv"),
                     delimiter=",", skip_header=1)
tohum, dog, te = pool[:, 0], pool[:, 1], pool[:, 2]

```

```python
K = 20
grup = lambda lo, x: np.array([x[lo + 5 * k: lo + 5 * k + 5].mean()
                               for k in range(K)])
te_sec = grup(0, te)          # secim kumesi test ortalamalari
dog_sec = grup(0, dog)        # secim kumesi dogrulama ortalamalari
te_taze = grup(100, te)       # taze tohumlardaki test ortalamalari

k_te = int(np.argmax(te_sec))
k_dog = int(np.argmax(dog_sec))
print("20 konfigurasyon, gercek fark yok")
print("(a) test'e gore secilen: secim-test = %.4f" % te_sec[k_te])
print("    ayni grubun taze tohum testi    = %.4f" % te_taze[k_te])
print("(c) dogrulamaya gore secilen: taze test = %.4f"
      % te_taze[k_dog])
print("tum 20 grup, taze test ort = %.4f  (dogru tahmin)"
      % te_taze.mean())
print("secim kumesinde max-ort fark = %+.4f"
      % (te_sec[k_te] - te_sec.mean()))
csv_yaz("b79_secim.csv",
        [("test_secimi", "%.4f" % te_sec[k_te],
          "%.4f" % te_taze[k_te]),
         ("dogrulama_secimi", "%.4f" % te_sec[k_dog],
          "%.4f" % te_taze[k_dog]),
         ("tum_gruplar_ort", "%.4f" % te_sec.mean(),
          "%.4f" % te_taze.mean())],
        ["secim_olcutu", "secim_kumesi_test", "taze_test"])
```

```term
$ python t06_secim.py
20 konfigurasyon, gercek fark yok
(a) test'e gore secilen: secim-test = 0.9761
    ayni grubun taze tohum testi    = 0.9717
(c) dogrulamaya gore secilen: taze test = 0.9739
tum 20 grup, taze test ort = 0.9734  (dogru tahmin)
secim kumesinde max-ort fark = +0.0022
```

Sonuç açık. Test ortalamasına göre seçilen konfigürasyon seçim kümesinde 0,9761 ile raporlanırdı; aynı konfigürasyonun taze tohumlardaki skoru 0,9717. Yani raporlanan iyimserlik yaklaşık 0,4 puan. Doğrulamaya göre seçilen konfigürasyonun taze testi 0,9739, yani yirmi grubun gerçek ortalamasına (0,9734) çok yakın. Burada tek bir tohum kümesi kullandık; bu nedenle bu sayılar bir örnektir, bir istatistik değildir. Ama mekanizma her tekrarda aynıdır: test üzerinde seçim, raporlanan skoru yukarı çeker.

Bunun pratik sonucu şudur: bir makalede "en iyi konfigürasyon test kümesinde %X" diyorsa, o konfigürasyon seçim kümesinde tanımlanmış mı, yoksa test kümesinde mi seçilmiş, bunu sormalısın. Eğer test kümesinde seçildiyse, o sayı üst sınırdır, tarafsız tahmin değildir.

## 79.13 Deney günlüğü, araştırma döngüsü ve şekil ilkeleri

Araştırma bir döngüdür: bir hipotez kurarsın, bir deney tasarlarsın, sonucu ölçersin, sonuca göre karar verirsin ve bu karar genelde yeni bir hipotez doğurur. Şekil 79.8 bu döngüyü gösteriyor. Döngünün her adımı kayda geçmelidir; kaydı tutmadığında aynı deneyi ikinci kez yaparsın, ya da daha kötüsü, negatif bir sonucu hiç görmezsin.

![Şekil 79.8: Araştırma döngüsü: hipotez, deney, sonuç ve karar](gorseller/b79_arastirma_dongu.png)

Deney günlüğü, her koşu için bir satırdır. Bir satırda en azından şunlar bulunmalı: tarih, hipotez, tohum listesi, veri sürümü ve bölme, kod sürümü (commit özeti), hiperparametreler, metrikler, sonuç ve karar. Bölüm 77.5'te bu günlüğü SQLite ile sıfırdan kurduk; bu bölümde ise günlüğü bir CSV ile tuttuk ve her deneyin çıktısını `engine/veri` altına yazdık. Yöntem ne olursa olsun kural aynıdır: her sayı, onu üreten betiğe ve tohuma bağlanabilmeli.

Negatif sonuçların değeri büyüktür. Bu bölümde bulduğumuz "dropout bu kurulumda bir etki yapmadı" sonucu, bir başkasının aynı deneyi tekrar yapmasını engeller. Yayımlanmayan negatif sonuçlar, bilimsel kayda girmediği için aynı hatalar tekrarlanır. Bu, tekrarlanabilirlik krizinin başlıca nedenlerinden biridir (genel bilgi).

Döngünün son adımı olan rapor, bir şekil ya da tabloya dayanır. Şekil tasarımı ayrı bir beceridir ve yanlış tasarlanmış bir şekil, doğru bir sonucu yanıltıcı yapabilir. İyi bir şekil için birkaç ilke:

- Sayısal bir çubuk grafiğin ekseni sıfırdan başlamalı. Sıfırdan başlamayan bir eksen farkları abartır; bu gerekliyse bunu açıkça belirt.
- Ölçümün belirsizliği gösterilmeli: hata çubuğu, güven aralığı ya da tohum bandı.
- Renk bir anlam taşımalı; süs için renk kullanılmamalı.
- Her eksenin birimi ve her şeklin açıklaması olmalı.
- Okur, şeklin tek bir mesajını on saniyede anlayabilmeli.

Şekil 79.5 bu ilkelerin tersini gösteriyor: soldaki kesik eksenli panel, eşit iki değeri bir fark gibi gösteriyor ve üçüncü değeri çerçevenin dışına itiyor. Sağdaki panel sıfırdan başlıyor, sayıları ve alfa çizgisini içeriyor. Aynı veri, iki farklı mesaj.

Bu bölümün kodu, bu şekilleri ve kitabın diğer şekillerinin tarzını üreten ortak bir diyagram betiğiyle yazıldı. Betik, ölçüm grafiklerini `engine/veri` altındaki CSV dosyalarından okur; böylece şekiller sayılardan ayrılmaz.

```python
# -*- coding: utf-8 -*-
"""Bölüm 79 - Makale okuma ve araştırma yöntemi diyagramları.

Ölçüm grafikleri engine/veri/b79_*.csv dosyalarından okunur;
bu CSV'leri deney betikleri üretir (t01 ... t06).
Kavramsal şekiller veri okumaz.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import os

import matplotlib.pyplot as plt
import numpy as np

from diagrams import (ACCENT, ACCENT_L, EDGE, FILL, INK, MUTED, RULE,
                      _arrow, _box, _save)

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VERI = os.path.join(KOK, "engine", "veri")
GORSEL = os.path.join(KOK, "gorseller")


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))

```

```python

def uc_gecis(path):
    """Makale okumanın üç geçişi.
    Her geçiş bir öncekinin üstüne kurulur."""
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis("off")
    adimlar = [
        ("1. Geçiş: haritalama",
          "başlık, özet, şekiller,\nsonuç tabloları", 0),
        ("2. Geçiş: yöntem",
          "veri, baseline, ayarlar,\ndeney düzeni", 1),
        ("3. Geçiş: ayrıntı",
          "denklemler, kod, ek,\nyeniden üretim", 2),
    ]
    for ad, alt, i in adimlar:
        x = 0.4 + i * 4.6
        _box(ax, x, 3.1, 4.0, 1.5, ad, fill=FILL[i], edge=EDGE[i],
             fs=11.5, bold=True)
        ax.text(x + 2.0, 2.2, alt, ha="center", va="center",
                fontsize=9.4, color=MUTED)
        if i < 2:
            _arrow(ax, x + 4.0, 3.85, x + 4.6, 3.85,
                   col=ACCENT, lw=1.8)
    _box(ax, 3.0, 0.2, 8.0, 1.0,
         "Karar: oku, not al, bir sonraki geçişe gerek var mı?",
         fill=FILL[4], edge=EDGE[4], fs=10.5)
    return _save(fig, path)

```

```python

def makale_anatomi(path):
    """Makalenin parçaları ve her parçanın okurken sorduğu soru."""
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")
    _box(ax, 4.2, 6.6, 5.6, 1.1, "İddia (katkı)", fill=FILL[0],
         edge=ACCENT, fs=12, bold=True)
    parcalar = [
        ("Yöntem", "ne yapıldı,\nnasıl", 0.3, 4.1),
        ("Deney düzeni", "veri, bölme,\ntohum sayısı", 4.9, 4.1),
        ("Baseline", "karşılaştırılan\nbasit yöntem", 9.5, 4.1),
        ("Ablation", "hangi bileşen\nsonucu taşıyor", 0.3, 1.6),
        ("Sınırlamalar", "neyi kontrol\netmedi", 4.9, 1.6),
        ("Kod ve veri", "yeniden üretilebilir\nmi", 9.5, 1.6),
    ]
    for ad, alt, x, y in parcalar:
        _box(ax, x, y, 4.1, 1.5, ad, fill=FILL[2], edge=EDGE[2],
             fs=11, bold=True)
        ax.text(x + 2.05, y - 0.45, alt, ha="center", va="center",
                fontsize=8.8, color=MUTED)
        _arrow(ax, x + 2.05, y + 1.5, 7.0, 6.6, col=RULE, lw=1.0)
    ax.text(7.0, 0.35, "Her parça iddiayla bağlantılı olmalı; "
            "bağlantı yoksa iddia desteği zayıftır.",
            ha="center", fontsize=9.2, color=INK)
    return _save(fig, path)

```

```python

def tohum_fark(path):
    """Aynı yöntemin iki koşusu arasındaki fark dağılımı (Deney 1)."""
    satir = oku("b79_tohum_fark.csv")
    f = np.array([float(r["fark"]) for r in satir])
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.hist(f * 100, bins=np.arange(-1.6, 1.6, 0.2), color=FILL[0],
            edgecolor=EDGE[0], lw=1.0)
    ax.axvline(0, color=ACCENT, lw=1.6)
    ax.axvline(1.0, color=MUTED, lw=1.0, ls="--")
    ax.axvline(-1.0, color=MUTED, lw=1.0, ls="--")
    ax.text(1.05, ax.get_ylim()[1] * 0.92, "+1 puan", color=MUTED,
            fontsize=9)
    ax.text(-1.05, ax.get_ylim()[1] * 0.92, "-1 puan", color=MUTED,
            fontsize=9, ha="right")
    ax.set_xlabel("Test doğruluğu farkı (yüzde puan), aynı yöntem",
                  color=INK)
    ax.set_ylabel("Çift sayısı (100 çift)", color=INK)
    ax.set_title("Tohum gürültüsü: aynı yöntemin iki koşusu",
                 color=INK, fontsize=12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return _save(fig, path)

```

```python

def guc_egrisi(path):
    """Tohum sayısına göre saptanabilir fark (Deney 4)."""
    satir = oku("b79_guc.csv")
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    renk = {"0.005": ACCENT_L, "0.010": EDGE[1], "0.020": ACCENT}
    for d in ["0.005", "0.010", "0.020"]:
        s = [r for r in satir if r["delta"] == d]
        n = [int(r["n"]) for r in s]
        g = [float(r["guc"]) for r in s]
        ax.plot(n, g, "o-", color=renk[d], lw=1.8,
                label="gerçek fark %.3f" % float(d))
    ax.axhline(0.8, color=MUTED, lw=1.0, ls="--")
    ax.text(20.3, 0.82, "güç = 0,80", color=MUTED,
            fontsize=9, ha="right")
    ax.set_xlabel("Her yöntemde tohum sayısı (n)", color=INK)
    ax.set_ylabel("Güç (doğru fark saptama olasılığı)", color=INK)
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=False, fontsize=9.5)
    ax.set_title("Güç analizi: σ = 0,0030 ölçülmüş",
                 color=INK, fontsize=12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return _save(fig, path)

```

```python

def yeniden_uretim(path):
    """İddia ile ölçüm: tohum başına AdamW - Adam farkı (Deney 2)."""
    satir = oku("b79_yeniden.csv")
    f = np.array([float(r["fark"]) for r in satir]) * 100
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    x = np.arange(len(f))
    ax.axhspan(-0.17, 0.33, color=FILL[1], alpha=0.8)
    ax.text(4.4, 0.42, "%95 GA (bootstrap): [-0,17; +0,33] puan",
            ha="right", fontsize=9, color=EDGE[1])
    ax.axhline(0, color=ACCENT, lw=1.5)
    ax.scatter(x, f, s=60, color=ACCENT_L, zorder=3)
    ax.axhline(f.mean(), color=INK, lw=1.2, ls="--")
    ax.text(4.4, f.mean() - 0.12, "ortalama +0,06 puan",
            ha="right", fontsize=9, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(["tohum %d" % i for i in range(len(f))])
    ax.set_ylabel("AdamW - Adam (yüzde puan)", color=INK)
    ax.set_title("Bölüm 64.4 iddiası: fark sapmalar içinde mi?",
                 color=INK, fontsize=12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return _save(fig, path)

```

```python

def ablation(path):
    """2x2x2 ablation: sekiz koşulun ortalama testi (Deney 3)."""
    satir = oku("b79_ablation.csv")
    sirali = sorted(satir, key=lambda r: float(r["test_ort"]))
    ad = [r["kosul"] for r in sirali]
    v = np.array([float(r["test_ort"]) for r in sirali])
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.barh(ad, v, color=FILL[0], edgecolor=EDGE[0], lw=1.4)
    ax.set_xlim(0.96, 0.99)
    for i, val in enumerate(v):
        ax.text(val + 0.0003, i, "%.4f" % val,
                va="center", fontsize=9)
    ax.set_xlabel("Test doğruluğu (5 tohum ortalaması)", color=INK)
    ax.set_title("Ablation: BN etkisi görünür, dropout etkisi küçük",
                 color=INK, fontsize=12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return _save(fig, path)

```

```python

def coklu_karsilastirma(path):
    """Kötü ve iyi şekil: aynı veri, iki farklı eksen (Deney 5)."""
    satir = oku("b79_coklu.csv")
    ad = ["ham", "bonferroni", "holm"]
    f = {r["duzeltme"]: float(r["fwer"]) for r in satir}
    v = [f[a] for a in ad]
    fig, (sol, sag) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    sol.bar(ad, v, color=FILL[3], edgecolor=EDGE[3])
    sol.set_ylim(0.0275, 0.0285)
    sol.set_title("Kötü: kesik eksen, fark abartılı", color=INK,
                  fontsize=10.5)
    sol.set_ylabel("FWER", color=INK)
    sag.bar(ad, v, color=FILL[1], edgecolor=EDGE[1])
    sag.axhline(0.05, color=ACCENT, lw=1.4, ls="--")
    sag.text(2.45, 0.058, "alfa = 0,05", color=ACCENT, fontsize=9,
             ha="right")
    sag.set_ylim(0, 0.7)
    for i, val in enumerate(v):
        sag.text(i, val + 0.015, "%.3f" % val,
                 ha="center", fontsize=9)
    sag.set_title("İyi: sıfırdan, eşik görünür",
                  color=INK, fontsize=10.5)
    sag.set_ylabel("FWER", color=INK)
    for a in (sol, sag):
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
    fig.tight_layout()
    return _save(fig, path)

```

```python

def arastirma_dongu(path):
    """Hipotez -> deney -> sonuç -> karar döngüsü."""
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis("off")
    dugumler = [
        ("Hipotez", "iddia, ölçülebilir\nbeklenti", 0.6, 4.3, 0),
        ("Deney", "tek değişken,\n3+ tohum", 4.9, 4.3, 1),
        ("Sonuç", "güven aralığı,\nnegatif sonuç dahil", 9.2, 4.3, 2),
        ("Karar", "kabul, red ya da\nyeni hipotez", 4.9, 0.6, 3),
    ]
    for ad, alt, x, y, i in dugumler:
        _box(ax, x, y, 3.9, 1.6, ad, fill=FILL[i], edge=EDGE[i],
```

```python
             fs=12, bold=True)
        ax.text(x + 1.95, y - 0.45, alt, ha="center", va="center",
                fontsize=8.8, color=MUTED)
    _arrow(ax, 4.5, 5.1, 4.9, 5.1, col=ACCENT, lw=1.8)
    _arrow(ax, 8.8, 5.1, 9.2, 5.1, col=ACCENT, lw=1.8)
    _arrow(ax, 11.15, 3.9, 8.8, 1.6, col=ACCENT, lw=1.8)
    _arrow(ax, 4.9, 1.4, 2.5, 3.9, col=ACCENT, lw=1.8)
    ax.text(7.0, 3.1,
            "Karar yeni hipotez doğuruyorsa döngü tekrar eder",
            ha="center", fontsize=9, color=MUTED)
    return _save(fig, path)


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    uc_gecis(os.path.join(GORSEL, "b79_uc_gecis.png"))
    makale_anatomi(os.path.join(GORSEL, "b79_makale_anatomi.png"))
    tohum_fark(os.path.join(GORSEL, "b79_tohum_fark.png"))
    guc_egrisi(os.path.join(GORSEL, "b79_guc_egrisi.png"))
    yeniden_uretim(os.path.join(GORSEL, "b79_yeniden_uretim.png"))
    ablation(os.path.join(GORSEL, "b79_ablation.png"))
    coklu_karsilastirma(
        os.path.join(GORSEL, "b79_coklu_karsilastirma.png"))
    arastirma_dongu(os.path.join(GORSEL, "b79_arastirma_dongu.png"))
    print("tamam")
```

## 79.14 Yazma ve yayın: makale nasıl yapılandırılır?

Bir araştırma sonucunu yazmanın en yaygın yapısı IMRaD'dır: Giriş (Introduction), Yöntem (Methods), Sonuçlar (Results) ve Tartışma (Discussion). Bu yapı, okurun aradığı bilgiyi aradığı sırayla vermek için vardır: önce neden, sonra nasıl, sonra ne bulundu, en sonda ne anlama geliyor (genel bilgi).

Yöntem bölümü, bir başkasının yeniden üretebileceği kadar ayrıntılı olmalıdır: veri sürümü, bölme, tohum listesi, hiperparametreler, metrik tanımı ve donanım. Bu bölümde yaptığımız her deneyin kaynak satırlarını ve tohumlarını yazmak, bu kuralın uygulamasıdır. Sonuçlar bölümü ise yalnızca ölçümleri verir: yorum tartışma bölümüne aittir.

Özet, makalenin en çok okunan kısmıdır ve yazması en zor olanıdır. İyi bir özet dört cümlede verilir: problem, yöntem, temel sonuç ve sınırlama. Özette ölçü ve belirsizlik bulunmalı; "önemli bir iyileşme sağladık" gibi bir ifade, bir sayı içermediği sürece değersizdir.

Atıf ve intihal etiği, bilimsel dürüstlüğün ayrılmaz parçasıdır. Bir fikri, bir sonucu ya da bir kod parçasını kullandığında kaynağını göstermelisin. Bu kitapta bunu "genel bilgi" işaretiyle yapıyoruz; bir iddianın kaynağını doğrulayamadığımızda bunu açıkça yazıyoruz.

Yayın süreci iki yolla ilerler. Ön baskı (örneğin arXiv) makaleyi hakem süreci beklemeden herkese açar; hızlıdır ama hakemli değildir. Hakemli yayın, konferans ya da dergi üzerinden ilerler; konferans daha hızlı ve sıkı zamanlıdır, dergi daha uzun ve ayrıntılı bir incelemeye sahiptir (genel bilgi). Hangisinin uygun olduğu, araştırma alanına ve çalışmanın büyüklüğüne bağlıdır.

Açık kaynak kod ve veri yayınlamak, bugün bir yöntemin güvenilirliğini gösteren en güçlü araçtır. Kodunu ve tohumlarını paylaşan bir çalışma, okurun sonucu kendisi tekrar üretmesini sağlar. Bu, bu kitabın her bölümünde uyguladığımız kuraldır.

Savunma sanayiinde yayın, ek bir kısıtla gelir: gizlilik. Bir sistemin performans sayıları, sensör özellikleri ya da görev senaryoları kamuya açık olmayabilir. Bu durumda genel ilkeleri yayımlamak, ayrıntıları ise kurumun izinli kanallarında paylaşmak gerekir. Hangi bilginin paylaşılabileceği, kurumun ve ilgili mevzuatın kurallarına göre değişir; bu konuda kesin bir politika iddia etmiyoruz. Kurum adı verirken dikkatli ol ve gizlilik kararını ilgili yetkiliye bırak.

## 79.15 Araştırma problemi bulmak: ilgiden açık soruya

Çoğu öğrenci araştırma sorusunu "yeni bir şey yapmak" olarak düşünür. Daha verimli bir yol, bir mühendislik projesinde karşılaşılan somut bir belirsizliği açık bir soruya çevirmektir. Örneğin bir sensör verisiyle çalışan bir modelin performansı, gürültü arttığında ne kadar düşüyor? Bu, ölçülebilir bir sorudur ve bu bölümde kurduğumuz araçlarla sınanabilir.

Bu dönüşüm üç adımda olur. Birincisi, projedeki bir ölçümü ya da gözlemi yazarsın: "modelim gece verisinde kötü çalışıyor." İkincisi, bunu bir hipoteze çevirirsin: "gece verisinde doğruluk, gündüz verisine göre en az yüzde beş düşüktür." Üçüncüsü, hipotezi sınayacak en küçük deneyi tasarlarsın: hangi veri, kaç tohum, hangi metrik, hangi fark anlamlı sayılacak?

Mert'in projeleri bu dönüşüm için doğal bir kaynaktır. EV Dashboard'daki STM32 sensör verisi, zaman serisi ve gürültü sorularına; ÖZCE'deki semantik iletişim fikri, bir kodlayıcının bilgiyi ne kadar koruduğu sorusuna dönüşebilir. Bu bölümde bu projelerin dosyalarına erişmedik; yalnızca konsept düzeyinde bir örnek veriyoruz. Gerçek bir soruya dönüştürmek için projenin kendi verisini ve kendi kısıtlarını kullanman gerekir.

Küçük ama iyi tasarlanmış bir deney, büyük ama kötü tasarlanmış bir deneyden daha değerlidir. Bu bölümde yaptığımız deneyler birkaç dakika sürdü; ama her biri tek bir soruyu, tohum gürültüsünü ölçerek, kontrol ederek ve sonucu güven aralığıyla raporlayarak cevapladı. Bu, bir araştırmacının en güçlü alışkanlığıdır.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, Bölüm 5'teki altı adımı izler: Anla, Örnekle, Kaba çöz, Örüntü, İyileştir, Doğrula. Her örneğin sonunda elle iz sürme tablosu ve bir "AI'sız yazabilir misin?" sorusu vardır.

### Örnek 1 (★): Kurgu bir makale özetini üç geçişle okumak

Bu örnekte bir makale kurgusaldır; gerçek bir yayın değildir. Özeti şöyle olsun: "KAPSAM-7 adlı yeni bir hafif dikkat katmanı önerdiğimiz. Üç kamu veri kümesinde standart taban modelden yüzde 1,8 daha yüksek doğruluk elde ettik. Yöntem, mevcut dikkat katmanına yalnızca iki parametre ekler." Bu metni üç geçişle okuyup bir okuma notu çıkaracağız.

**Adım 1 — Anla.** Soru: Bu makale hangi problemi çözüyor, hangi iddiayı öne sürüyor? Cevap: Dikkat katmanına çok az parametre ekleyerek doğruluğu artırmak. İddia tek cümle: "yüzde 1,8 daha iyi, iki parametre ekleniyor."

**Adım 2 — Örnekle.** İddiayı somutlaştırırsak: bir veri kümesinde taban doğruluk 0,900 ise yeni yöntem yaklaşık 0,918 vermeli. Hangi kamu veri kümeleri, hangi tohum, hangi baseline? Özet bunları söylemiyor.

**Adım 3 — Kaba çöz.** İlk geçişte (haritalama) başlığı, özeti ve (varsayılan olarak) şekilleri okuruz. Özet, iddiayı ve kanıtın tipini ("üç veri kümesi") verir. Eksik olan: tohum sayısı, sapma, baseline'ın ayarı.

**Adım 4 — Örüntü.** Kırmızı bayrak tablosuna bakarız: özette tohum sayısı yok (tek tohum olabilir), "standart taban modelin" ayarı belirsiz (zayıf baseline olabilir), "yüzde 1,8" bir sapmayla verilmemiş. Bu üç eksik, iddianın kanıtını sınamadan kabul etmememiz gerektiğini gösterir.

**Adım 5 — İyileştir.** İkinci geçişte yöntem bölümünü ararız. Sorular: Taban model hangi ayarla eğitildi? Kaç tohum, sapma kaç? Hangi metrik? Bir ablation var mı? Bu soruların cevabı ikinci geçişte bulunmazsa, sonuç ertelenir.

**Adım 6 — Doğrula.** Okuma notunu beş soruyla yazarız. Kendi testimiz: iki parametrelik ekleme için 5 tohumla, taban ve yeni modeli eşleştirilmiş farkla karşılaştırırız; fark güven aralığının dışında mı? Okuma notu tablosu:

| Soru | Cevap (kurgu makale için) |
|---|---|
| Problem ne? | Dikkat katmanına az parametreyle doğruluk artırmak |
| Katkı ne? | İki parametrelik bir ekleme |
| Kanıt yeterli mi? | Sayısal kanıt var, tohum ve sapma yok: yetersiz |
| Neyi kontrol etmedi? | Taban ayarı, tohum sayısı, ablation |
| Ben nasıl test ederim? | 5 tohum, eşleştirilmiş fark, %95 GA |

**Bunu AI'sız yazabilir misin?** Yukarıdaki beş soruyu, uydurduğun ama gerçekçi bir özet için kendi cevaplarınla doldur. Ardından özette olmayan ama iddiayı sınamak için gereken üç bilgiyi listele.

### Örnek 2 (★★): Beş tohumluk farkın elle testi

Bölüm 79.10'daki AdamW ile Adam farkları, beş tohumda şöyle: −0,0028, 0,0000, 0,0000, 0,0000, +0,0056. Bu farkın ortalamasının sıfırdan farklı olup olmadığını, eşleştirilmiş t testiyle elle sınayacağız.

**Adım 1 — Anla.** Soru: beş eşleştirilmiş farkın ortalaması sıfırdan anlamlı şekilde farklı mı? Hipotez: H0, gerçek fark sıfır. Serbestlik derecesi `5 − 1 = 4`.

**Adım 2 — Örnekle.** Farklar `d = (−0,0028; 0; 0; 0; 0,0056)`. Ortalama `(−0,0028 + 0,0056) / 5 = 0,0028 / 5 = 0,00056`.

**Adım 3 — Kaba çöz.** Sapma için her farkın ortalamadan sapmasını ve karesini alırız, sonra `n − 1` ile böleriz. Sapmalar: −0,00336; −0,00056 (üç kez); +0,00496. Karelerin toplamı yaklaşık `3,65 × 10⁻⁵`. Bölü 4: `9,13 × 10⁻⁶`. Karekök: sapma `≈ 0,00302`.

**Adım 4 — Örüntü.** Standart hata `0,00302 / √5 ≈ 0,00135`. t değeri `0,00056 / 0,00135 ≈ 0,41`. Bu, betiğin verdiği 0,408 ile uyumlu.

**Adım 5 — İyileştir.** t = 0,41 için df = 4 ile iki yönlü p değeri yaklaşık 0,70. Bu, sıfır hipotezini reddetmek için hiçbir neden olmadığı anlamına gelir. Bootstrap güven aralığı ise, beş değerden yeniden örnekleme ile kodla hesaplanır: elle yapmak için 5⁵ = 3125 olası örnek vardır; betik bunları on binlerce rastgele örnekle tahmin eder. Sonuç `[−0,0017, +0,0033]`.

**Adım 6 — Doğrula.** Elle iz tablosu:

| Adım | Değer | Betik çıktısı |
|---|---|---|
| Ortalama | 0,00056 | +0,0006 |
| Sapma | 0,00302 | (hesaplanmadı) |
| Standart hata | 0,00135 | (hesaplanmadı) |
| t (df 4) | 0,41 | 0,408 |
| p (iki yönlü) | ≈ 0,70 | 0,704 |

Elle ve betikle sonuç uyuşuyor. Dikkat: iki değerin de yüksek sapması, dört tanesinin sıfır olması beş tohumun çok küçük olduğunu gösteriyor; bu yüzden p değeri güvenilir olmasa da düşük gücü yansıtıyor.

**Bunu AI'sız yazabilir misin?** Yalnızca `(1; 3; 2)` farklarını alıp eşleştirilmiş t değerini ve p değerini elle hesapla. Sonra aynı üç değer için bootstrap'in neden kendi başına yeterli olmadığını bir cümleyle açıkla.

### Örnek 3 (★★): Kurgu bir sonuç tablosunda metodolojik hatalar

Bu tablo kurgudur: "Model A (önerilen) test doğruluğu 0,953; Model B (taban) 0,949. A, tek tohumla eğitildi. Hiper parametreler test kümesinde seçildi. Sonuç: A, B'den yüzde 0,4 daha iyi."

**Adım 1 — Anla.** İddia: A, B'den yüzde 0,4 iyi. Verilen kanıt: iki tek sayı, tek tohum, test kümesinde ayar.

**Adım 2 — Örnekle.** Tek tohumda sapma yaklaşık 0,3 puan (Bölüm 79.7). Dolayısıyla 0,4 puanlık fark, bir tohumun şansı olabilir.

**Adım 3 — Kaba çöz.** Üç hata var: tohum sayısı bir, seçim test kümesinde, güven aralığı yok.

**Adım 4 — Örüntü.** Bu üç hata da Bölüm 79.5'teki kırmızı bayrakların ikisidir: tek tohum ve test kümesinde ayar. Üçüncüsü, belirsizlik eksikliği.

**Adım 5 — İyileştir.** Doğru deney tasarımı: hiper parametreleri ayrı bir doğrulama kümesinde seç. Her model için 5 tohum koş, eşleştirilmiş farkı ve %95 güven aralığını raporla. Test kümesini yalnızca son raporlamada kullan.

**Adım 6 — Doğrula.** Düzeltilmiş tasarımda sonucu şu biçimde rapor ederdik: "Eşleştirilmiş fark A − B = +0,4 puan, %95 GA [−0,2; +1,0] puan, n = 5." Bu aralık sıfırı içerdiği için, iddia "daha iyi" değil, "ayırt edilemez" olarak yazılmalı.

| Hata | Sayı | Düzeltme |
|---|---|---|
| Tek tohum | 1 | En az 5 tohum |
| Test kümesinde ayar | Evet | Doğrulama kümesinde seçim |
| Belirsizlik yok | Evet | Eşleştirilmiş fark + GA |

**Bunu AI'sız yazabilir misin?** Bu tablonun sahte bir kurgu olduğunu, ama gerçek bir makalede olabilecek üç hatayı kendi cümlelerinle, her biri için düzeltmeyle birlikte yaz.

### Örnek 4 (★★★): Bir ablation çalışmasını tasarlamak ve koşmak

Bu örnekte iddia şudur: "Bu küçük MLP'de BatchNorm, sonucu en çok etkileyen bileşendir." Bunu sınamak için 2³ faktöriyel tasarım kuracağız ve Bölüm 79.11'deki betiği kullanacağız.

**Adım 1 — Anla.** Soru: sekiz koşulluk tasarımda BN'nin ana etkisi sıfırdan güvenli biçimde farklı mı? Bileşen sayısı üç; her koşul beş tohum.

**Adım 2 — Örnekle.** BN açık ve kapalı iki grup; her grupta dört koşul. Tohum 0'da BN açık dört koşulun ortalaması ile BN kapalı dört koşulun ortalaması arasındaki fark, tohum 0'ın BN etkisidir. Beş tohum için beş etki elde edilir.

**Adım 3 — Kaba çöz.** Sekiz koşulu koş, her birinin ortalamasını al, ana etkiyi hesapla, beş etki üzerinden t güven aralığı kur.

**Adım 4 — Örüntü.** Çalıştırılan sonuçta BN'li koşullar 0,9828–0,9878 arasında, BN'siz koşullar 0,9739–0,9783 arasında. Bu, BN'nin tutarlı bir etkisi olduğunu gösteriyor. Kosinüs takvimi de küçük ama tutarlı bir artış veriyor; dropout ise etkisiz görünüyor.

**Adım 5 — İyileştir.** Bu ablation'ı daha sağlam yapmak için: (a) bileşen seçimi doğrulamada yapılmalı, (b) etkileşimler ayrıca raporlanmalı, (c) en az on tohum kullanılmalı (Bölüm 79.8). Biz beş tohum kullandık; dropout'un etkisini ayırt etmek için bu yetmez.

**Adım 6 — Doğrula.** Elle iz tablosu, ana etkiler:

| Bileşen | Ana etki (puan) | %95 GA (puan) | Yorum |
|---|---|---|---|
| BN | +0,94 | [+0,52; +1,37] | Tutarlı etki |
| COS | +0,33 | [+0,29; +0,37] | Küçük ama tutarlı |
| DO | +0,08 | [−0,16; +0,33] | Ayırt edilemedi |

Sonuç: "BN bu kurulumda sonucu en çok etkileyen bileşendir" iddiası destekleniyor, ama "dropout işe yaramaz" diyemeyiz; yalnızca ayırt edemedik.

**Bunu AI'sız yazabilir misin?** Ablation'ı iki bileşenle (BN ve COS) tasarla: dört koşul, üç tohum. Hangi sonuçta "etkileşim var" diyebilirsin, hangisinde diyemezsin, bir cümleyle açıkla.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı kullanma. Kendi okumanı, kendi deneyini ve kendi raporunu yaz. Araç yalnızca bir sözlük ya da bir kaynak olarak kullanılabilir; sonuçları ve kodu sen yazmalısın. Bu yasak, okuduğun makalenin yeniden üretimi için de geçerlidir.
:::

### Proje 1 (★★): Bölüm 64.8'deki etiket yumuşatma iddiasını yeniden üretmek

**Amaç.** Bölüm 64.8, etiket yumuşatmanın test doğruluğunu en yüksek seviyeye çıkardığını ama kalibrasyon hatasını (ECE) 0,11'e yükselttiğini raporluyor. Bu iddiayı bağımsız olarak yeniden üret ve iki metriği birlikte raporla.

**Yapılacak / Beklenen davranış.** (1) Kitabın metninden MLP ve kurulumu oku; etiket yumuşatma olmadan ve 0,1 ile iki koşulu tanımla. (2) Beş tohumla her iki koşulu çalıştır; test doğruluğu ve ECE'yi kaydet. (3) Farkı eşleştirilmiş olarak ve %95 güven aralığı ile raporla. (4) ECE için bir hesap fonksiyonu yaz ve bunu on tohumdan bir alt kümede doğrula.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** ECE, tahmin olasılıklarını on eşit aralığa bölüp her aralıktaki ortalama güven ile doğruluk farkının ağırlıklı ortalaması olarak tanımlanır (genel bilgi). Bölüm 79.6'daki `t_testi` ve `bootstrap_gven` fonksiyonlarını kullanabilirsin; etiket yumuşatma için `nn.CrossEntropyLoss(label_smoothing=0.1)` gibi bir parametre kullanılabilir (PyTorch belgesini kontrol et).

**Başarı kriterleri.** (a) Her iki koşul beş tohumla koşulmuş ve tablo tohum bazında verilmiş. (b) Test farkının %95 GA'sı raporlanmış. (c) ECE farkı için de aynı istatistik yapılmış. (d) Kitabın sayılarıyla karşılaştırma yapılmış ve uyuşmazlık varsa nedeni tartışılmış.

### Proje 2 (★★★): Küçük bir araştırma sorusu için uçtan uca çalışma

**Amaç.** Tek bir açık soruyu uçtan uca cevapla: "Bu MLP'de öğrenme oranı takvimi, aynı eğitim süresinde sabit öğrenme oranından daha iyi mi?" Hipotez, deney günlüğü, güç analizi, istatistik ve IMRaD biçiminde iki sayfalık bir rapor üret.

**Yapılacak / Beklenen davranış.** (1) Hipotezini yaz ve H0/H1'i tanımla. (2) Güç analizi yap: beklediğin fark için kaç tohum gerektiğini Bölüm 79.8'deki yöntemle hesapla. (3) Deney günlüğünü (CSV) tut: her koşu için tohum, koşul, sonuç. (4) Eşleştirilmiş farkı ve güven aralığını hesapla; bir ablation tablosu ekle. (5) Raporu IMRaD yapısında yaz; yöntem bölümü yeniden üretilebilir olmalı.

**Önerilen yaklaşım (ipucu).** Önce Deney 1'in gürültüsünü yeniden ölç. Güç analizi için sigma'yı kendi takvimine göre düzelt. Sonucu güven aralığıyla raporla; "fark yok" yerine "bu deneyle fark ayırt edilemedi" demeyi unutma.

**Başarı kriterleri.** (a) Hipotez ve güç analizi deneyden önce yazılmış (tarihli günlük). (b) En az on tohum. (c) Eşleştirilmiş fark ve güven aralığı raporlanmış. (d) Rapor, bir başkasının tekrarlayabileceği kadar ayrıntılı. (e) Negatif bir sonuç çıkarsa bile rapor dürüstçe yazılmış.

### Ek Alıştırmalar

1. ★ Bir makalede "yöntemimiz baseline'dan yüzde 2 iyi" diyor, ama tohum sayısı yok. Bu cümleyi sınamak için hangi üç soruyu sorarsın?
2. ★ Üç tohumlu iki koşunun farkı yüzde 1 puan. Bu, gerçek bir fark olduğunu gösterir mi? Neden?
3. ★ Sapması 0,003 olan bir yöntemde yüzde 0,5 puanlık bir farkı yüzde 80 güçle bulmak için kaç tohum gerekir (kabaca)?
4. ★★ 20 karşılaştırma yaparsan ve hepsinin gerçek farkı sıfırsa, en az bir "anlamlı" sonuç çıkma olasılığı kabaca nedir? Bağımsız varsayımla hesapla.
5. ★★ Holm yöntemi neden Bonferroni'den daha güçlüdür? Sıralı eşiği bir örnekle açıkla.
6. ★★ Bir ablation tablosunda BN açıkken ve kapalıyken iki ayrı sonuç var, ama etkileşim raporlanmamış. Ne sorarsın?
7. ★ "Yönteminiz neden çalışıyor?" sorusunu, kanıt sormadan nasıl cevaplarsın?
8. ★★ Test kümesinde ayar yapılmış bir makalenin tablosunu nasıl düzeltirsin? Yeniden hangi veriyi kullanırsın?
9. ★★ Bir makalede kodu paylaşılmamış, ama tohumlar ve hiperparametreler verilmiş. Yine de yeniden üretim için neye ihtiyacın var?
10. ★★ Negatif bir sonucu neden yayımlamak istersin? Yayımlanmazsa hangi hatalar tekrarlanır?
11. ★★★ Bir şekilde eksen kesilmiş ve ortalama çubuklarına hata çubuğu konmamış. Bu şekli okuyan birine hangi üç şeyi açıkça söylersin?
12. ★★★ Savunma sanayiinde bir ekip, bir makalenin sonucunu gizlilik nedeniyle yayımlayamıyor. Yine de bu çalışmayı nasıl belgeler ve tekrarlanabilir kılarsın?

## Kod Okuma Egzersizi

Bu bölümde iki tek örneklem t testini kullandık. Kullandığımız `t_testi` fonksiyonu kendi basit hesabımızdı. Gerçek bir kütüphane aynı işi nasıl yapıyor? Yerel scipy 1.17.1 kurulumunda (`C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\scipy\stats\_stats_py.py`) `ttest_rel` fonksiyonu, eşleştirilmiş farkları alıp `ttest_1samp` çağırır. Aşağıdaki alıntı `ttest_1samp` fonksiyonunun hesaplama kısmıdır; yorumlar ve docstring çıkarılmıştır, satırlar birebir kopyalanmıştır.

```python
    df = n - 1

    if a.shape[axis] == 0:
        # This is really only needed for *testing*
        # _axis_nan_policy decorator
        # It won't happen when the decorator is used.
        NaN = _get_nan(a)
        return TtestResult(NaN, NaN, df=NaN, alternative=NaN,
                           standard_error=NaN, estimate=NaN)

    mean = xp.mean(a, axis=axis)
    try:
        popmean = xp.asarray(popmean)
        popmean = (xp.squeeze(popmean, axis=axis)
                   if popmean.ndim > 0 else popmean)
    except ValueError as e:
        raise ValueError("`popmean.shape[axis]` must equal 1.") from e
    d = mean - popmean
    v = _var(a, axis=axis, ddof=1)
    denom = xp.sqrt(v / n)

    with np.errstate(divide='ignore', invalid='ignore'):
        t = xp.divide(d, denom)
        t = t[()] if t.ndim == 0 else t
```

Not: `popmean = xp.squeeze(...)` satırı 70 karakter sınırı için iki satıra bölündü; ifade değişmedi; uzun bir yorum satırı da iki satıra bölündü. Docstring ve dağıtım nesnesi (`_SimpleStudentT`) alıntıdan çıkarıldı, kaynaktaki yorum satırları ise olduğu gibi bırakıldı. Alıntı, `d`, `v`, `denom` ve `t` hesabının tamamını kapsıyor; p değeri bu alıntının dışında kalıyor.

**Sorular — cevaplamadan geçme:**

1. `ttest_rel(a, b)` çağrısının `ttest_1samp(a - b, popmean=0)` olarak yazılmış olması, eşleştirilmiş testin neden tek örneklem testine indirgenebildiğini açıklıyor mu? Bu indirgemenin hangi varsayımı taşıdığını yaz.
2. `denom = xp.sqrt(v / n)` satırında `v` neden `ddof=1` ile hesaplanıyor? `ddof=0` kullanılsaydı p değeri nasıl etkilenirdi?
3. `d = mean - popmean` ile `t = d / denom` arasındaki ilişkiyi, Bölüm 79.6'daki formülle karşılaştır. Aynı mı?
4. `with np.errstate(divide='ignore', invalid='ignore'):` bloğu neden var? `denom` sıfır olduğunda ne olur?
5. Bu alıntıda p değeri hesabı görünmüyor. p değerini bulmak için hangi dağılım kullanılıyor ve neden serbestlik derecesi `df = n - 1`?
6. Kendi `t_testi` fonksiyonumuz ile bu kodun sonucu, beş değerli bir örnekte aynı olmalı. Bunu kendin doğrulamak için hangi küçük girdiyi kullanırsın?

## Bölüm Özeti

- Bir makaleyi üç geçişle oku: haritalama, yöntem, ayrıntı. Her geçişin sonunda karar ver.
- Her makalenin altı parçası var: iddia, yöntem, deney düzeni, baseline, ablation, sınırlamalar. Bunları iddiaya bağla.
- Kırmızı bayraklar (tek tohum, zayıf baseline, test kümesinde ayar, seçici raporlama, anlamlılık eksikliği, aşırı genelleme, sızıntı) sonucu sınamadan kabul etmemeni söyler.
- Tohum gürültüsünü ölç. Bu kurulumda iki koşunun farkı genelde yüzde bir puanın altında kalır, ama bu bir genelleme değildir.
- Güç analizi, aradığın farkı bulmak için kaç tohum gerektiğini söyler. Yarım puanlık fark için beş tohum yetmez.
- Çoklu karşılaştırmada düzeltme şart: ham hata oranı yirmi testte yüzde 38'e çıkabildi, Holm ve Bonferroni bunu yüzde 3'e indirdi.
- Yeniden üretim, kitabın Bölüm 64.4 iddiasında olduğu gibi, sonucun metinden tekrar elde edilebildiğini gösterir; ama protokol aynı olsa bile kodun birebir aynı olduğunu kanıtlamaz.
- Ablation, bileşenlerin katkısını faktöriyel tasarımla ölçer; BatchNorm bu kurulumda tutarlı bir etki verdi, dropout ayırt edilemedi.
- Negatif sonuçları kaydet; şekil tasarımında ekseni sıfırdan başlat ve belirsizliği göster.

**Sonraki bölümde:** Bölüm 80'de (Bitirme: Uçtan Uca Sistem), bu kitabın bütün araçlarını bir araya getiren tek bir sistemi kuracağız: bir İHA görüntüsünden nesne tespiti, takip, edge cihazına dağıtım ve izleme. Bu bölümde kurduğumuz deney ve ölçüm disiplini, o sistemin hangi bileşeninin ne kadar güvenilir olduğunu sınamak için doğrudan kullanılacak.

::: mulakat
1. Bir makalede "yöntemimiz daha iyi" diyor. Bunu sınamak için hangi üç soruyu sorarsın?
2. Tek bir tohumla yapılmış bir karşılaştırmaya neden güvenilmez?
3. Aynı yöntemin iki koşusu arasındaki fark sıfır olmalı mı? Neden değil?
4. Yirmi karşılaştırma yaptın ve birinde p değeri 0,03 çıktı. Bu sonuca ne dersin?
5. Eşleştirilmiş fark ile bağımsız iki örneklem arasındaki farkı ne zaman kullanırsın?
6. Bir ablation çalışmasında hangi bileşenin "sonucu taşıdığını" nasıl gösterirsin?
7. Bir modelin raporlanan test skorunun iyimser olduğunu nasıl anlarsın?
8. Yeniden üretim neden tek başına "doğrulama" sayılmaz?
:::
