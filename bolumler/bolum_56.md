%% kisim_no: XIV
%% kisim_ad: Makine Öğrenmesi
%% bolum_no: 56
%% baslik: Veriyle Çalışmak

## Giriş: Modelin büyük kısmı veridir

Bir makine öğrenmesi projesinde en çok zaman alan iş çoğu zaman model seçimi değildir. Sahada sık söylenen bir söz vardır: modelin büyük kısmı veriden oluşur. Bu sözü kesin bir oran olarak almak yanlış olur; genel bir deneyim gözlemidir. Ama arkasındaki fikir sağlamdır. Aynı algoritma, kirli bir veriyle temiz bir veri arasında çok farklı sonuç verir.

Savunma sanayiinde bu durum daha da belirgindir. Bir İHA uçuş günlüğünde irtifa bir kayıtta metre, bir başkasında fit olarak yazılabilir. Bir sensör bağlantısı koptuğunda `-999` gibi bir sentinel değer dönebilir. Farklı kaynaklardan gelen zaman damgaları farklı saat dilimlerinde olabilir. Model bunların hiçbirini "görmez"; yalnızca sayı görür. Yanlış birimdeki bir irtifa, eğitimde bir hata olarak değil, bir gerçek olarak öğrenilir. Mert'in EV Dashboard projesindeki STM32 sensör akışı da aynı sorunu taşır: sensör kopar, saat kayar, değer birimi değişir.

Bu bölümde verinin ham hâlinden modele giden yolu adım adım kuruyoruz. Önce NumPy'ın iç yapısını öğreneceğiz: dizinin belleği, görünüm ile kopya farkı, vektörleştirme ve yayınlama. Veri işlemenin hızı ve doğruluğu bu iç yapıya bağlıdır. Sonra pandas ile tablo işlemeyi, keşifsel veri analizini, temizlemeyi, eksik veriyi, öznitelik mühendisliğini ve dengesiz veriyi ele alacağız. Son olarak veri doğrulamayı ve büyük veri dosyalarını göreceğiz.

Ana uygulamada Bölüm 54'teki disiplini kullanıyoruz. Kural basittir: her ön işleme adımı veri bölündükten sonra yapılır, yalnızca eğitim kümesinden öğrenir ve bir Pipeline içinde çalışır. Bu kuralı çiğnemek, Bölüm 54'te gördüğümüz veri sızıntısını doğurur. Bölümün sonunda aynı kirli veriyle iki hat kuracak ve arıza tahmin başarısının nasıl değiştiğini ölçeceğiz.

Bu bölümde gerçek bir kayıt kullanmıyoruz. İHA uçuş günlüğü, bu bölüm için ürettiğimiz sentetik bir veri kümesidir. Kirlilikler bilerek eklenmiştir ve her birinin gerçek yeri bilinmektedir. Böylece temizlik adımlarımızı tahmin etmek yerine ölçebiliyoruz. Bölümdeki sayısal bilgiler Python 3.12.10, numpy 2.3.5, pandas 2.3.3, scikit-learn 1.8.0, scipy 1.17.1, matplotlib 3.10.9 ve pyarrow 23.0.1 ile üretildi.

::: not
Bu bölümdeki her sayı, yazdığımız bir programın çıktısıdır. Tohumlar sabittir, bu yüzden aynı sürümlerde aynı sayıları görmelisin. Zamanlama ölçümleri ise makineye bağlıdır; onları kendi bilgisayarında yeniden ölç ve oranlara bak, mutlak sürelere değil.
:::

## 56.1 NumPy dizisinin içi: bellek, görünüm ve kopya

Bölüm 48'de vektörleri ve matrisleri matematiksel olarak gördük. Burada aynı nesnenin bilgisayarda nasıl saklandığına bakıyoruz, çünkü veri işlemedeki en pahalı hatalar çoğu zaman buradan çıkar. NumPy'da bir `ndarray` iki parçadan oluşur: bir başlık ve bir bellek bloğu. Başlık veri türünü (`dtype`), şekli (`shape`) ve **adımları** (`strides`) tutar. Bellek bloğu ise öğelerin ham baytlarını düz bir şerit hâlinde saklar.

Adımlar, bir öğeye ulaşmak için kaç bayt atlanacağını söyler. Satır adımı (`strides[0]`) bir sonraki satıra geçmek için, sütun adımı (`strides[1]`) bir sonraki sütuna geçmek için atlanacak baytı verir. `(i, j)` öğesinin bellek ofseti `i · s0 + j · s1` ile hesaplanır. Örneğin `int32` öğeli 3×4 bir matriste adımlar `(16, 4)`tür ve `a[1, 2]` öğesi `16·1 + 4·2 = 24` bayt ilerdedir. Bu, düz diziye bakarsak altıncı öğedir.

Burada önemli bir ayrım var. Bazı işlemler yeni bir bellek bloğu ayırmaz; yalnızca aynı belleği farklı adımlarla okuyan bir **görünüm** (view) döndürür. Bazı işlemler ise bellekte yeni bir **kopya** üretir. Görünüm üzerinde yapılan bir değişiklik orijinal diziyi de değiştirir. Kopya üzerinde yapılan değişiklik orijinali etkilemez. Bu ayrımı bilmeden yazılan kod, sessizce yanlış sonuç verebilir.

Aşağıdaki tabloda hangi işlemin ne ürettiğini özetledik. Bu tablonun her satırını aşağıdaki program doğrular.

| İşlem | Sonuç | Neden |
|---|---|---|
| `a[:, 1:3]` (dilim) | görünüm | Aynı bellek, farklı adımlar |
| `a.T` | görünüm | Yalnızca adımlar değişir (genel bilgi) |
| `a.reshape(4, 3)` | görünüm | Veri bitişik olduğu için mümkün |
| `a.T.reshape(-1)` | kopya | Bellek bitişik değil, düzleştirme kopya ister |
| `a[[0, 2]]` (tamsayı dizisiyle indeks) | kopya | Seçilen satırlar yeni bir yere toplanır |
| `a[a > 5]` (boolean maske) | kopya | Seçilen öğeler yeni bir dizi olur |

Aşağıdaki program bu tabloyu sayılarla denetliyor. Paylaşımı `np.shares_memory` ile sorguluyoruz; bu fonksiyon iki dizinin bellek alanlarının kesişip kesişmediğini söyler.

```python
import numpy as np

a = np.arange(12, dtype=np.int32).reshape(3, 4)
print("dtype:", a.dtype, " shape:", a.shape)
print("strides (bayt):", a.strides, " itemsize:", a.itemsize)
print("a[1,2] bellek ofseti:", 1 * 16 + 2 * 4, "bayt")
print("ravel()[6] == a[1,2]:", a.ravel()[6] == a[1, 2])
print("T strides:", a.T.strides)
dilim = a[:, 1:3]
print("dilim strides:", dilim.strides)
print("dilim paylasim:", np.shares_memory(a, dilim))
f = a[[0, 2]]
print("gelismis indeks paylasim:", np.shares_memory(a, f))
m = a[a > 5]
print("maske paylasim:", np.shares_memory(a, m))
print("reshape paylasim:", np.shares_memory(a, a.reshape(4, 3)))
print("T.reshape paylasim:", np.shares_memory(a, a.T.reshape(-1)))
```

Aşağıdaki çıktı, her satırın tabloyla uyuştuğunu gösteriyor. Adımlar `(16, 4)` ve `a.T` için `(4, 16)` olarak çıktı; `a[1,2]` öğesinin ofseti de 24 bayt.

```term
$ python b56_01_ndarray.py
dtype: int32  shape: (3, 4)
strides (bayt): (16, 4)  itemsize: 4
a[1,2] bellek ofseti: 24 bayt
ravel()[6] == a[1,2]: True
T strides: (4, 16)
dilim strides: (16, 4)
dilim paylasim: True
gelismis indeks paylasim: False
maske paylasim: False
reshape paylasim: True
T.reshape paylasim: False
```

Şekil 56.1, aynı belleğin üzerinde dilimin ve gelişmiş indeksin nasıl farklı davrandığını gösteriyor. Üstteki satırda 12 öğe düz bir şerit olarak durur; ortadaki görünüm bu şeridin içinden seçilmiş öğeleri, alttaki kopya ise yeni bir bellek bloğunu gösterir.

![Şekil 56.1: Düz bellek üzerinde görünüm ve kopya. Dilim aynı şeridi okur; gelişmiş indeks yeni bir blok ayırır.](gorseller/b56_bellek.png)

Görünüm, bir tuzak olarak ciddi zarar verebilir. Aşağıdaki örnekte bir fonksiyon, gelen diziyi yerinde ortalamadan çıkarıyor. Fonksiyona bir dilim verildiğinde orijinal dizi de değişir; bir kopya verildiğinde değişmez. Üçüncü versiyon yerinde değiştirmeyen, güvenli yoldur.

```python
import numpy as np

def normalize_et(v):
    v -= v.mean()          # yerinde degistirir
    return v

x = np.array([1.0, 2.0, 3.0, 4.0, 10.0])
dilim = x[1:4]             # gorunum
normalize_et(dilim)
print("dilim sonrasi x:", x)

y = np.array([1.0, 2.0, 3.0, 4.0, 10.0])
kopya = y[[1, 2, 3]]       # gelismis indeks: kopya
normalize_et(kopya)
print("kopya sonrasi y:", y)

def normalize_guvenli(v):
    return v - v.mean()    # yeni dizi uretir

z = np.array([1.0, 2.0, 3.0, 4.0, 10.0])
sonuc = normalize_guvenli(z[1:4])
print("guvenli: z =", z, " sonuc =", np.round(sonuc, 3))
```

Çıktı, tuzağın nasıl işlediğini açıkça gösteriyor. `x` dizisi, yalnızca bir dilim fonksiyona verildiği için değişti. Kopya ile çağrılan `y` değişmedi. Güvenli sürüm ise `z` dizisini koruyarak yeni bir sonuç üretti.

```term
$ python b56_01b_tuzak.py
dilim sonrasi x: [ 1. -1.  0.  1. 10.]
kopya sonrasi y: [ 1.  2.  3.  4. 10.]
guvenli: z = [ 1.  2.  3.  4. 10.]  sonuc = [-1.  0.  1.]
```

Bu davranışın bir kuralı var: NumPy'da `-=`, `+=` gibi yerinde (in-place) işleçler görünüm üzerinde çalıştığında kaynağı değiştirir. Bir işlevin girdisini değiştirmesi gerekmiyorsa `v = v - v.mean()` gibi yeni dizi üreten bir yazım tercih edilir. Bu, bellek maliyeti getirir ama hataları önler. Bellek düzeni ayrıca hız ile ilgilidir. Bölüm 25'te gördüğümüz önbellek satırları, ardışık erişimi hızlandırır; bu yüzden bir dizinin hangi eksende bitişik olduğunu bilmek performansı doğrudan etkiler.

## 56.2 Vektörleştirme: döngüden diziye

Bir sensör verisinin her örneği için aynı hesabı yapmak, veri işlemenin en yaygın işidir. Bu hesabı Python `for` döngüsüyle yazmak, en kolay yoldur ama en yavaşıdır. Nedeni şudur: Python döngüsünde her öğe için yorumlayıcı bir nesne oluşturur, tipini kontrol eder ve işlemi ayrı ayrı çağırır. NumPy ise aynı işi tek bir C döngüsünde, bitişik bellek üzerinde, çoğu zaman SIMD komutlarıyla yapar (Bölüm 24). Bu yaklaşıma **vektörleştirme** denir.

Aşağıdaki program aynı hesabın iki yoldan nasıl çalıştığını ölçüyor. Her ölçümde dokuz tekrar alıyor ve medyanı alıyoruz; tek bir ölçüm, işletim sisteminin gürültüsüne kolayca yenik düşer. Program ayrıca iki sonucun birbirine eşit olduğunu doğruluyor, çünkü hızlı bir yanlış sonuç hiçbir işe yaramaz.

```python
import csv, os, time
import numpy as np

def dongu(x, a, b):
    s = 0.0
    for v in x:                    # her eleman icin Python dongusu
        t = a * v + b
        s += t * t
    return s

def vektor(x, a, b):
    t = a * x + b                  # tum dizi tek seferde
    return np.dot(t, t)

def en_iyi(f, *args, tekrar=9):
    zaman = []
    for _ in range(tekrar):
        t0 = time.perf_counter()
        f(*args)
        zaman.append(time.perf_counter() - t0)
    return float(np.median(zaman))  # gurultuye dayanikli

rng = np.random.default_rng(56)
satirlar = []
print("%10s %12s %12s %8s" % ("n", "dongu (s)", "vektor (s)", "oran"))
for n in [10**3, 10**4, 10**5, 10**6]:
    x = rng.standard_normal(n)
    d_s = en_iyi(dongu, x, 2.0, 0.5)
    v_s = en_iyi(vektor, x, 2.0, 0.5)
    assert abs(dongu(x, 2.0, 0.5) - vektor(x, 2.0, 0.5)) < 1e-6 * n
    print("%10d %12.6f %12.6f %8.1f" % (n, d_s, v_s, d_s / v_s))
    satirlar.append((n, "%.6f" % d_s, "%.6f" % v_s))

```

Programın ikinci yarısı, ölçüm tablosunu yazar ve sonucu bir CSV dosyasına kaydeder. Bu dosya Şekil 56.2'yi üretir.

```python
yol = os.path.join("D:/Mevcut Projeler/Kitap/engine/veri",
                   "b56_dongu_olcum.csv")
with open(yol, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["n", "dongu_s", "vektor_s"])
    w.writerows(satirlar)
print("csv yazildi")
```

Aşağıdaki çıktı, her dizi uzunluğu için iki süreyi ve oranı gösteriyor.

```term
$ python b56_02_dongu_olcum.py
         n    dongu (s)   vektor (s)     oran
      1000     0.000183     0.000003     55.4
     10000     0.001736     0.000007    259.1
    100000     0.018098     0.000445     40.7
   1000000     0.198602     0.003519     56.4
csv yazildi
```

Tablo açıkça bir fark gösteriyor: vektörleşmiş sürüm, her boyutta onlarca kat daha hızlı. Ancak oran tek bir sayı değildir. Oranın `n = 10⁴`te diğerlerinden yüksek çıkmasının nedeni, dizinin önbelleğe sığıp sığmamasıyla ilgilidir. `10⁴` öğelik bir `float64` dizisi yaklaşık 80 KB'tır; `10⁵`te ise 800 KB olur ve bu boyut çoğu işlemcinin L2 önbelleğini aşabilir (önbellek ayrıntısı için Bölüm 25; hangi boyutun hangi düzeye sığdığı işlemciye bağlıdır). Ölçümleri tekrarladığımızda oranların değiştiğini de göreceksin; bu yüzden tek bir koşudaki sayıya değil, sıralamaya ve nedene dikkat et.

Şekil 56.2, aynı ölçümü log-log ölçekte çiziyor. İki eğrinin eğimi, iki yöntemin dizi uzunluğuyla nasıl büyüdüğünü gösterir. Dönüm noktası, önbellek sınırının eğriye yansıdığı yerdir.

![Şekil 56.2: Python döngüsü ile NumPy vektörleştirmesinin süresi (medyan, log-log).](gorseller/b56_olcum.png)

Vektörleştirmenin bir maliyeti de vardır. Çok büyük ara diziler bellek tüketir: `a * x + b` ifadesi her adımda yeni bir dizi üretir. Bu yüzden büyük verilerde ifadeleri parçalara bölmek ya da yerinde işleçler kullanmak gerekebilir. Bunun bedelini bu bölümün büyük veri kısmında ölçeceğiz.

## 56.3 Yayınlama (broadcasting): farklı şekilli diziler

Bir sensör matrisinden her sütunun ortalamasını çıkarmak istediğinizde iki dizinin şekli farklıdır: bir matris `(örnek, özellik)`, ortalama ise `(özellik,)`. NumPy bu işlemi kendi kurallarıyla hizalayıp uygular. Bu kurallara **yayınlama** (broadcasting) denir. Kuralların kendisi kısa, ama yanlış anlaşıldığında en sinsi hatalardan birine yol açarlar.

Kurallar şöyledir. Önce iki şekli **sağdan** hizalarız. Eksik kalan boyutları 1 kabul ederiz. Sonra her eksende iki boyut ya eşittir ya da biri 1'dir. Eşitse sonuç o boyuttur; biri 1 ise diğerine yayılır. Bu koşul sağlanmazsa NumPy hata verir. Yayılan eksenler için bellek kopyalanmaz; NumPy bu eksende adımı 0 yapar ve aynı değeri tekrar okur. Bu, yayınlamanın bellek maliyetinin neden sıfıra yakın olduğunu açıklar.

Aşağıdaki program bu kuralları bir fonksiyon olarak yeniden yazıyor, sonra NumPy'ın kendi `broadcast_shapes` fonksiyonuyla rastgele 2000 şekil çifti üzerinde karşılaştırıyor. Bu, kuralı kendi cümlelerinizle doğru yazdığınızın kanıtıdır.

```python
import numpy as np

def yayin_sekli(s1, s2):
    # sag hizala; her eksende boyutlar esit ya da biri 1 olmali
    n = max(len(s1), len(s2))
    p1 = (1,) * (n - len(s1)) + tuple(s1)
    p2 = (1,) * (n - len(s2)) + tuple(s2)
    out = []
    for a, b in zip(p1, p2):
        if a == b or b == 1:
            out.append(a)
        elif a == 1:
            out.append(b)
        else:
            raise ValueError("uyumsuz: %d ve %d" % (a, b))
    return tuple(out)

print("(3,4)+(4,)  ->", yayin_sekli((3, 4), (4,)))
print("(3,1)+(1,4) ->", yayin_sekli((3, 1), (1, 4)))
print("(5,)+(5,1)  ->", yayin_sekli((5,), (5, 1)))
print("(8,1,6)+(7,1)->", end=" ")
try:
    print(yayin_sekli((8, 1, 6), (7, 1)))
except ValueError as e:
    print("hata:", e)

rng = np.random.default_rng(56)
def rastgele_sekil():
    boy = rng.integers(1, 4)
    return tuple(int(rng.integers(1, 4)) for _ in range(boy))

```

Programın ikinci yarısı, `(n,)` ile `(n, 1)` farkını ve `broadcast_to` ile adımın nasıl sıfır olduğunu gösteriyor.

```python
uyusan = 0
for _ in range(2000):
    s1, s2 = rastgele_sekil(), rastgele_sekil()
    try:
        bizim = yayin_sekli(s1, s2)
    except ValueError:
        bizim = None
    try:
        numpy_s = tuple(np.broadcast_shapes(s1, s2))
    except ValueError:
        numpy_s = None
    uyusan += (bizim == numpy_s)
print("2000 rastgele sekil cifti, uyusan:", uyusan)

x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
sutun = x.reshape(5, 1)
print("x - x.mean(), x (5,):", (x - x.mean()).shape)
print("x - sutun ->", (x - sutun).shape)
print("dogru (keepdims):", (sutun - sutun.mean(axis=0)).shape)

b = np.broadcast_to(np.arange(3), (1000, 3))
print("broadcast_to sekil:", b.shape, " strides:", b.strides)
print("kopya mi:", not np.shares_memory(b, np.arange(3)))
```

Çıktı, kuralın tüm örneklerde doğru işlediğini gösteriyor. Dikkat edilmesi gereken satır, `x - sutun` çıktısıdır: `x` bir `(5,)` dizisi, `sutun` ise `(5, 1)` boyutludur. Sonuç `(5, 5)` olur. Bu bir hata mesajı vermez; sadece her çift için bir fark hesaplar ve ortalamayı yanlış merkezler.

```term
$ python b56_03_yayin.py
(3,4)+(4,)  -> (3, 4)
(3,1)+(1,4) -> (3, 4)
(5,)+(5,1)  -> (5, 5)
(8,1,6)+(7,1)-> (8, 7, 6)
2000 rastgele sekil cifti, uyusan: 2000
x - x.mean(), x (5,): (5,)
x - sutun -> (5, 5)
dogru (keepdims): (5, 1)
broadcast_to sekil: (1000, 3)  strides: (0, 8)
kopya mi: True
```

Şekil 56.3, üç örnek çiftin hizalanmasını ve sonucu gösteriyor. Son satırdaki `(5,)` ile `(5,1)` çifti, yaygın tuzağın görsel hâlidir: sonuç beklenen `(5,)` değil, `(5, 5)` matrisidir.

![Şekil 56.3: Yayınlama kuralları. Sağdan hizalama, 1 boyutunun yayılması ve (5,) ile (5,1) tuzağı.](gorseller/b56_yayin.png)

Bu tuzaktan kaçınmanın yolu `keepdims=True` ile ortalamayı `(5, 1)` olarak tutmak ya da sütun ortalamasını `axis` ile açıkça almaktır. Bölüm 55'teki gradyan hesabında da aynı kural vardı: bir yayınlanan toplamanın geri adımında gradyan, yayınlanan eksende toplanmalıdır. Bu, yayınlamayı yalnızca kolaylık değil, türev kuralının da parçası yapar.

## 56.4 Eksenler, maskeler ve sayısal tuzaklar

Bir matrisi toplarken `axis` parametresi hangi eksenin "çökeceğini" belirler. `axis=0` satırları üst üste toplar ve sütun başına bir değer verir; sonuç `(4,)` şeklindedir. `axis=1` sütunları toplar ve satır başına bir değer verir. Akılda tutulacak sezgi şudur: verilen eksen sonuçta **kaybolur**.

Veri temizlemede en sık kullandığımız araçlar, koşula göre seçim yapan maskeler ve `np.where` ile sayısal hatalardır. Boolean maske, bir koşulu sağlayan öğeleri seçer ve yeni bir dizi döndürür (Bölüm 56.1'deki tabloya göre bir kopyadır). `np.where(koşul, a, b)` ise bir koşula göre iki dizi arasından seçim yapar ve bellekte yeni bir dizi üretir.

Sayısal tuzaklar, gerçek verinin dışarıdan gelen ölçümlerinde ortaya çıkar. Eksik ölçüm `NaN` olarak temsil edilir ve `NaN` her işleme bulaşır: bir `NaN` içeren ortalama `NaN` döner. Ayrıca `NaN == NaN` ifadesi `False`tur; eksik değeri yalnızca `np.isnan` ile yakalayabilirsiniz. Bir başka tuzak, düşük hassasiyetli toplamadır. `float32` ile on milyon kez `0.1` toplamak, sıralı birikim yaparsa büyük bir hata biriktirir. NumPy'ın `np.sum` fonksiyonu ise ikili (pairwise) toplam yaparak bu hatayı belirgin biçimde azaltır.

Aşağıdaki program eksen davranışını, maskeyi, `NaN` yayılımını ve `float32` birikim hatasını sayılarla gösteriyor. Son kısımda dört veri türünün bellek maliyetini de yazdırıyor.

```python
import math
import numpy as np

M = np.array([[1, 2, 3, 4],
              [5, 6, 7, 8],
              [9, 10, 11, 12]])
print("M.sum(axis=0):", M.sum(axis=0), " sekil:", M.sum(axis=0).shape)
print("M.sum(axis=1):", M.sum(axis=1), " sekil:", M.sum(axis=1).shape)

x = np.array([-2.0, 0.5, 3.0, -1.0, 4.0])
print("np.where:", np.where(x > 0, x, 0.0))
print("maske sayisi:", int((x > 0).sum()),
      " pozitif ort:", x[x > 0].mean())

v = np.array([1.0, np.nan, 3.0])
print("mean (NaN):", v.mean(), " nanmean:", np.nanmean(v))
print("nan == nan:", np.nan == np.nan, " isnan:", np.isnan(v))
print("nan yayilimi (max):", np.array([1, np.nan]).max())

n = 10**7
x32 = np.full(n, 0.1, dtype=np.float32)
ardisik = np.add.accumulate(x32)[-1]     # soldan saga birikim
ciftli = np.sum(x32, dtype=np.float64)   # genisletilmis toplam
pairwise = np.sum(x32)                   # ikili (pairwise) toplam
print("float32 ardisik birikim :", float(ardisik))
print("float32 np.sum          :", float(pairwise))
print("float64 birikim         :", float(ciftli))
print("gercek (fsum, 10^7*0.1f):", math.fsum(x32.astype(np.float64)))

for dt in (np.int8, np.int64, np.float32, np.float64):
    a = np.zeros(10**6, dtype=dt)
    print("%-8s %9.2f MB" % (np.dtype(dt).name, a.nbytes / 1e6))
```

Çıktı üç şeyi gösteriyor. Birincisi, `axis=0` ve `axis=1` sonuçları farklı şekillerdedir. İkincisi, `NaN` yayılır ve `nanmean` onu atlar. Üçüncüsü, `float32` ardışık birikimi on milyon `0.1` toplamında yaklaşık %8,8 hata verirken `np.sum` ve `float64` çok daha iyi sonuç verir.

```term
$ python b56_04_eksen_sayisal.py
M.sum(axis=0): [15 18 21 24]  sekil: (4,)
M.sum(axis=1): [10 26 42]  sekil: (3,)
np.where: [0.  0.5 3.  0.  4. ]
maske sayisi: 3  pozitif ort: 2.5
mean (NaN): nan  nanmean: 2.0
nan == nan: False  isnan: [False  True False]
nan yayilimi (max): nan
float32 ardisik birikim : 1087937.0
float32 np.sum          : 1000000.125
float64 birikim         : 1000000.0149011612
gercek (fsum, 10^7*0.1f): 1000000.0149011612
int8          1.00 MB
int64         8.00 MB
float32       4.00 MB
float64       8.00 MB
```

Bellek seçimi de bir tasarım kararıdır. Bir milyon öğelik bir dizi `int8` ile 1 MB, `float64` ile 8 MB tutar. Telemetri gibi milyonlarca satırlık verilerde doğru veri türünü seçmek hem bellek hem de önbellek davranışını değiştirir. Bu bölümde `category` ve `int8` gibi tiplerin bellek kazancını pandas tarafında ölçeceğiz.

## 56.5 pandas: Series, DataFrame ve indeks

NumPy dizisi bir sayı bloğudur. pandas ise bu bloğa **etiketler** ekler: satırlar bir indeks, sütunlar adlar taşır. `Series` tek bir sütundur; `DataFrame` ise bu sütunların bir tablosudur. Etiketler, pandas'ın en güçlü ve en tehlikeli özelliğidir. İki `Series` toplandığında pandas önce **indekslerini hizalar**. Hizalanmayan etiketler `NaN` olur.

Aşağıdaki program, indeks hizalamasını, `loc` ile `iloc` farkını ve zincirli atamanın neden tehlikeli olduğunu gösteriyor.

```python
import warnings
import pandas as pd

s1 = pd.Series([1, 2, 3], index=["a", "b", "c"])
s2 = pd.Series([10, 20, 30], index=["b", "c", "d"])
print("indeks hizalama (s1 + s2):")
print((s1 + s2).to_dict())

df = pd.DataFrame({"x": [5, 6, 7]}, index=[10, 20, 30])
print("loc[20]:", df.loc[20, "x"], " iloc[1]:", df.iloc[1]["x"])
df2 = pd.DataFrame({"x": [5, 6, 7]}, index=[1, 2, 3])
print("df2.loc[1] (etiket):", df2.loc[1, "x"],
      " df2.iloc[1] (konum):", df2.iloc[1]["x"])

d = pd.DataFrame({"a": [1, -1, 2], "b": [0, 0, 0]})
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    d[d.a > 0]["b"] = 9
    print("zincir atama -> b:", d.b.tolist())
    print("uyari:", [x.category.__name__ for x in w])
d.loc[d.a > 0, "b"] = 9
print("loc ile atama -> b:", d.b.tolist())

e = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
bir_kopya = e[["x"]].copy()
bir_kopya.loc[0, "x"] = -1.0
print("kopya uzerinde degisiklik, e:", e.x.tolist())
```

Aşağıdaki çıktı, indeks hizalamasını, `loc` ile `iloc` farkını ve zincirli atamanın sonucunu gösteriyor.

```term
$ python b56_05_pandas_temel.py
indeks hizalama (s1 + s2):
{'a': nan, 'b': 12.0, 'c': 23.0, 'd': nan}
loc[20]: 6  iloc[1]: 6
df2.loc[1] (etiket): 5  df2.iloc[1] (konum): 6
zincir atama -> b: [0, 0, 0]
uyari: ['SettingWithCopyWarning']
loc ile atama -> b: [9, 0, 9]
kopya uzerinde degisiklik, e: [1.0, 2.0, 3.0]
```

`loc` etiketle, `iloc` konumla çalışır. İndeks tam sayı olduğunda bu fark gizlenir: `df.loc[20]` ile `df.iloc[1]` aynı satırı verebilir, ama `df2.loc[1]` ile `df2.iloc[1]` farklı satırlar verir. Bu yüzden bir tablo ile çalışırken hangi yöntemin kullanıldığını her seferinde kontrol etmek gerekir.

Çıktı, pandas'ın en çok kafa karıştıran tuzağını gösteriyor: zincirli atama (`d[d.a > 0]["b"] = 9`) hiçbir şey yapmaz ve bir `SettingWithCopyWarning` uyarısı üretir. Bunun nedeni, ilk dilimin bir görünüm mü yoksa kopya mı olduğunun belirsiz olmasıdır. Doğru yazım tek adımda yapılır: `d.loc[d.a > 0, "b"] = 9`. Burada koşul ve sütun birlikte belirtildiği için yazma tek bir nesnede gerçekleşir. Son satır, bir kopya üzerinde yapılan değişikliğin orijinali etkilemediğini gösterir.

pandas'ın sürümüne göre bu davranış değişebilir. Bu bölümde kullandığımız sürüm olan 2.3.3'te copy-on-write varsayılan olarak kapalıdır. Yeni sürümlerde bu davranışın varsayılan hâle gelmesi beklenmektedir (genel bilgi); bu yüzden kodunuzun kullandığı sürümü her zaman not edin.

## 56.6 Gruplama, birleştirme ve şekil değiştirme

Veri analizinin büyük kısmı üç işlemden oluşur: bölmek, bir işlem uygulamak, sonuçları birleştirmek. Bu üçlü **split-apply-combine** olarak bilinir ve SQL'deki `GROUP BY` ile birebir örtüşür (Bölüm 34'teki toplama ve pencere fonksiyonlarını hatırla). Şekil 56.4, bu akışı bir İHA araç kümesi üzerinde gösteriyor.

![Şekil 56.4: Split-apply-combine. Tablo anahtara göre bölünür, her grupta bir işlem yapılır, sonuçlar birleştirilir.](gorseller/b56_split_apply.png)

Aşağıdaki program araç başına bir özet çıkarıyor. Aynı özeti SQL ile yazmak istersen şöyle bir sorgu gerekir:

```sql
SELECT arac_id,
       COUNT(*) AS satir,
       COUNT(DISTINCT ucus_no) AS ucus,
       AVG(batarya_v) AS batarya_ort,
       MAX(sicaklik_c) AS sicak_maks,
       AVG(ariza) AS ariza_oran
FROM ucus
GROUP BY arac_id;
```

Yukarıdaki SQL ile aşağıdaki pandas kodu aynı işi yapar. `named aggregation` yazımı, her çıktı sütununa açık bir ad verir. `transform` ise grup sonucunu aynı satır sayısıyla geri yayar; bu yüzden tabloya yeni bir sütun olarak eklenebilir.

```python
import warnings
import pandas as pd
from ihadata import uret, kayit_tablosu

df, tr = uret(56)
df["arac_id"] = df["arac_id"].str.strip().str.upper()
df = df.drop_duplicates(subset=["arac_id", "zaman"])
ozet = (df.groupby("arac_id", as_index=False)
          .agg(satir=("hiz", "size"),
               ucus=("ucus_no", "nunique"),
               batarya_ort=("batarya_v", "mean"),
               sicak_maks=("sicaklik_c", "max"),
               ariza_oran=("ariza", "mean")))
print(ozet.round(3).to_string(index=False))

son = df.groupby("ucus_no")["ariza"].transform("max")
print("ucus ariza isareti sayisi (transform):", int(son.sum()))

sol = pd.DataFrame({"ucus_no": [1, 2, 3, 4],
                    "arac": ["A", "A", "B", "C"]})
sag = pd.DataFrame({"arac": ["A", "A", "A", "B"],
                    "firmware": ["v1", "v2", "v3", "v1"]})
for tip in ["inner", "left", "outer"]:
    print(tip, len(sol.merge(sag, on="arac", how=tip)))
try:
    sol.merge(sag, on="arac", validate="many_to_one")
except pd.errors.MergeError as e:
    print("validate hatasi:", str(e)[:50])
kayit = kayit_tablosu()
birlesik = df.merge(kayit, on="arac_id", how="left",
                    validate="many_to_one")
print("satir once/sonra:", len(df), len(birlesik))
```

Çıktı, her araç için satır sayısı, uçuş sayısı, ortalama batarya, en yüksek sıcaklık ve arıza oranını gösteriyor. Ayrıca `transform` ile üretilen sütunun toplamı, arızalı uçuşlardaki tüm satırları sayıyor.

```term
$ python b56_06_groupby_merge.py
arac_id  satir  ucus  batarya_ort  sicak_maks  ariza_oran
 IHA-01   5046    20       24.364      47.117       0.006
 IHA-02   5067    20       24.356      46.205       0.037
 IHA-03   5197    20       24.353      46.272       0.024
 IHA-04   5047    20       24.355      49.811       0.049
 IHA-05   4974    20       24.356      48.593       0.050
 IHA-06   4882    20       24.359      46.950       0.044
 IHA-07   5132    20       24.355      45.370       0.018
 IHA-08   5143    20       24.355      47.615       0.036
 IHA-09   4957    20       24.364      45.279       0.019
 IHA-10   4950    20       24.357      47.643       0.050
ucus ariza isareti sayisi (transform): 13325
inner 7
left 8
outer 8
validate hatasi: Merge keys are not unique in right dataset; not a 
satir once/sonra: 50395 50395
```

Birleştirme (merge), SQL'deki `JOIN` işlemine karşılık gelir ve **anahtar çoğalması** en sık düşülen tuzaktır. İki tablodaki bir anahtar değeri sol tabloda `a` kez, sağ tabloda `b` kez geçiyorsa sonuçta `a × b` satır olur. Bu, satır sayısını beklenmedik biçimde patlatır. Şekil 56.5 bu durumu gösteriyor: sol tabloda `A` iki kez, sağ tabloda üç kez geçtiği için birleşim altı satır üretir.

![Şekil 56.5: Birleştirme türleri ve anahtar çoğalması. A anahtarı 2 × 3 = 6 satır üretir.](gorseller/b56_merge.png)

Aşağıdaki tablo, üç birleştirme türünün aynı girdide verdiği satır sayılarını özetliyor. Bu sayılar yukarıdaki programın çıktısıdır.

| Tür | Satır | Ne içerir |
|---|---|---|
| `inner` | 7 | Yalnız iki tabloda da olan anahtarlar (A: 6, B: 1) |
| `left` | 8 | Sol tablonun tümü; C için sağ sütunlar `NaN` |
| `outer` | 8 | İki tablonun birleşimi; C ve sağdaki eşleşmeyenler dahil |

Bu tuzaktan korunmanın en iyi yolu `validate` parametresidir. `validate="many_to_one"` yazarsan, sağ tabloda anahtar tekil değilse pandas hata verir. Bizim araç kayıt tablosunda her araç bir kez geçtiği için aşağıdaki birleştirme satır sayısını korur; bu, ilk temizlik adımımızın güvenlik kontrolüdür.

Pivot ve melt, tabloyu biçim değiştirmek için kullanılır. `pivot` (veya `unstack`) uzun bir tabloyu geniş bir matrise çevirir; `melt` tersini yapar ve geniş sütunları satırlara açar. Makine öğrenmesi boru hatlarında iki yönü de sık kullanırsın. Aşağıdaki programda arıza oranını araç ve göreve göre matrise çeviriyor, ardından iki sensör sütununu uzun biçime açıyoruz.

```python
import pandas as pd
from ihadata import uret, kayit_tablosu
from temizle import temizle

df, _ = uret(56)
t = temizle(df, kayit_tablosu())[0]
ozet = t.groupby(["arac_id", "gorev"])["ariza"].mean().unstack()
print("pivot (arac x gorev, arizali oran):")
print(ozet.round(3).head(3).to_string())

ornek = t[["zaman", "irtifa", "batarya_v"]].head(2)
uzun = pd.melt(ornek, id_vars="zaman", var_name="olcum",
               value_name="deger")
print("melt (genis -> uzun):")
print("genis:", ornek.shape, " uzun:", uzun.shape)
print(uzun.round(2).to_string(index=False))
```

Aşağıdaki çıktı, arıza oranının pivot tablosunu ve `melt` sonucunu gösteriyor.

```term
$ python b56_19_pivot.py
pivot (arac x gorev, arizali oran):
gorev    gozetleme  kesif
arac_id                  
IHA-01       0.015  0.000
IHA-02       0.034  0.038
IHA-03       0.046  0.016
melt (genis -> uzun):
genis: (2, 3)  uzun: (4, 3)
                    zaman     olcum  deger
2026-03-01 06:45:00+00:00    irtifa 121.29
2026-03-01 06:45:02+00:00    irtifa 121.38
2026-03-01 06:45:00+00:00 batarya_v  24.63
2026-03-01 06:45:02+00:00 batarya_v  24.65
```

Çıktı, `melt` sonrasında iki satırlık geniş tablonun dört satırlık uzun tabloya dönüştüğünü gösteriyor: her zaman adımı iki ölçüm türü için ayrı bir satır alır.

Son olarak `apply` konusu. Bir DataFrame sütununa Python fonksiyonu uygulamak için `apply` kullanılabilir. Ancak `apply` içte bir Python döngüsüdür; bu yüzden vektörleştirme kazancını yok eder. Aşağıdaki ölçüm bunu sayılarla gösteriyor.

```python
import time
import numpy as np
import pandas as pd
from ihadata import uret, kayit_tablosu
from temizle import temizle

df, _ = uret(56)
t = temizle(df, kayit_tablosu())[0]
ser = pd.Series(t["sicaklik_c"].fillna(0).values[:50000])


def olc(fn, tekrar=7):
    zaman = []
    for _ in range(tekrar):
        t0 = time.perf_counter()
        fn()
        zaman.append(time.perf_counter() - t0)
    return float(np.median(zaman))


print("apply ile vektorlestirme (5 * 10^4 satir):")
a = olc(lambda: ser.apply(lambda v: 2 * v + 1))
b = olc(lambda: 2 * ser + 1)
print("apply: %.4f s  vektor: %.6f s  oran: %.0f"
      % (a, b, a / b))
```

Aşağıdaki çıktı, iki yöntemin medyan süresini ve oranını gösteriyor.

```term
$ python b56_18b_apply.py
apply ile vektorlestirme (5 * 10^4 satir):
apply: 0.0087 s  vektor: 0.000088 s  oran: 99
```

Çıktıdaki oran, aynı işlemin `apply` ile yapılmasının vektörleştirilmiş ifadeye göre belirgin biçimde yavaş olduğunu gösteriyor. Kural açıktır: önce vektörleştirilmiş bir ifade ara; `apply` yalnızca bunun ifade edilemediği durumlarda kullanılmalıdır.

## 56.7 Zaman serisi ve kategorik tür

Telemetri bir zaman serisidir: her satırın bir zaman damgası vardır ve sıra önemlidir. pandas bu veriyi `DatetimeIndex` ile tutar. Zaman damgası ayrıştırmak, sanıldığından daha zordur, çünkü farklı kaynaklar farklı biçimler ve saat dilimleri kullanabilir. Aşağıdaki program, iki biçimin karıştığı bir sütunu nasıl doğru ayrıştıracağımızı gösteriyor.

```python
import pandas as pd
from ihadata import uret

df, tr = uret(56)
ist = df.loc[df.arac_id == "IHA-05", "zaman"].iloc[0]
print("yerel saat (IHA-05, ilk satir):", ist)
try:
    pd.to_datetime(pd.Series(["2026-03-01T06:00:00Z",
                              "2026-03-01 09:00:00+03:00"]))
except ValueError as e:
    print("hata:", str(e)[:60])
zaman = pd.to_datetime(df["zaman"], format="ISO8601", utc=True)
print("ISO8601 + utc dtype:", zaman.dtype, " ilk:", zaman.iloc[0])
print("ayni an (UTC):",
      zaman[df.arac_id == "IHA-05"].iloc[0])

uc = df[df.ucus_no == 1].copy()
uc.index = zaman[uc.index]
uc = uc.sort_index()
ort = uc[["irtifa", "batarya_v"]].resample("20s").mean()
print("20 sn yeniden ornekleme satir sayisi:", len(ort))
print("ilk iki satir:")
print(ort.head(2).round(2).to_string())

kayan = uc["sicaklik_c"].rolling("60s", closed="left").mean()
print("gecmis 60 sn ortalamasi ilk degerleri:",
      kayan.iloc[:3].round(2).tolist())

bellek_obj = df["arac_id"].memory_usage(deep=True)
bellek_cat = df["arac_id"].astype("category").memory_usage(deep=True)
print("arac_id object bellek (byte):", bellek_obj)
print("arac_id category bellek (byte):", bellek_cat)
print("oran:", round(bellek_obj / bellek_cat, 1))
```

Bu programın ikinci bölümünde, zaman serisi işlemleri (yeniden örnekleme ve kayan pencere) ile kategorik türün bellek kazancını ölçüyoruz.

```python

```

Çıktı, ayrıştırma ve yeniden örnekleme sonuçlarını birlikte gösteriyor.

```term
$ python b56_07_zaman_kategori.py
yerel saat (IHA-05, ilk satir): 2026-03-03 21:45:00+03:00
hata: time data "2026-03-01 09:00:00+03:00" doesn't match format "
ISO8601 + utc dtype: datetime64[ns, UTC]  ilk: 2026-03-01 06:45:00+00:00
ayni an (UTC): 2026-03-03 18:45:00+00:00
20 sn yeniden ornekleme satir sayisi: 25
ilk iki satir:
                           irtifa  batarya_v
zaman                                       
2026-03-01 06:45:00+00:00  121.59      24.60
2026-03-01 06:45:20+00:00  124.10      24.55
gecmis 60 sn ortalamasi ilk degerleri: [nan, 40.88, 40.25]
arac_id object bellek (byte): 2827438
arac_id category bellek (byte): 53199
oran: 53.1
```

Üç ayrıntıya dikkat et. Birincisi, `format` belirtmeden yapılan ayrıştırma karışık biçimde bir hata verdi: pandas biçimi ilk değerden çıkarır ve sonraki farklı biçimle uyuşmaz. `format="ISO8601", utc=True` yazımı her iki biçimi de tek bir UTC zamanına çevirir. İkincisi, `resample("20s")` iki saniyelik adımları yirmi saniyelik kutulara toplar. Üçüncüsü, `rolling("60s", closed="left")` yalnızca geçmiş değerleri kullanır: mevcut satır pencereye girmez. Bu, Bölüm 56.10'da göreceğimiz sızıntı konusunun zaman serisindeki karşılığıdır.

Kategorik tür, tekrar eden metin değerleri için büyük bellek kazancı sağlar. Araç kimliği gibi sütunlar yüz binlerce kez tekrar eder; `category` türü her değeri bir kez saklar ve satırlara kısa kodlar koyar. Çıktıdaki oran, bu sütunda yaklaşık elli kat bellek tasarrufu sağladığını gösteriyor. Bu, büyük veri bölümünde yapacağımız okuma stratejisinin de temelidir.

## 56.8 Veri kümesi, keşifsel analiz ve temizleme

Bölümün geri kalanında kullanacağımız veri, bir İHA filosunun uçuş günlüğüdür. On araç, her biri yirmi uçuş yapmış; her uçuş yaklaşık on dakikalık bir kayıttır ve iki saniyede bir ölçüm alınır. Veri gerçek değildir. Aşağıdaki modül, gerçekçi ama bilerek kirletilmiş bir günlük üretir; tohum sabittir (56). Kirlilikler şunlardır: iki araç yerel saatle (+03:00) kayıt yazıyor, dört araç irtifayı fit cinsinden kaydediyor, sensörler bazen `-999` ve `NaN` döndürüyor, bazı satırlar kopya, bazı araç kimlikleri küçük harf ya da fazla boşlukla yazılmış, görev adları ve hata kodları farklı yazımlarla gelmiş. Bir de gerçek bir arıza olayı var: arızalı uçuşlarda son yarım dakikada sıcaklık ve titreşim yükselir, irtifa hızla düşer. Her kirliliğin ve her arıza etiketinin yeri `tr` tablosunda tutuluyor; böylece temizliğimizi tahmin etmek yerine ölçebiliyoruz.

Üretici modülü, hangi değerin hangi kirlilikle üretildiğini açıkça saklar. Bu, gerçek hayatta elimizde olmayan bir lükstür. Bu yüzden bu bölümdeki her temizlik adımından sonra, cevabı bildiğimiz kontrollerle sonucu doğruluyoruz.

```python
# -*- coding: utf-8 -*-
"""Sentetik IHA ucus gunlugu uretici (Bolum 56). Tohum: 56.

Gercek veri degildir. Ogrenme icin bilerek kirletilmis bir veri
kumesidir; kirlilikler truth tablosunda isaretlenir."""
import numpy as np
import pandas as pd

ARACLAR = ["IHA-%02d" % i for i in range(1, 11)]
FT_ARACLAR = {"IHA-07", "IHA-08", "IHA-09", "IHA-10"}  # v2: ft
IST_ARACLAR = {"IHA-05", "IHA-06"}                     # +03:00
BASLANGIC = pd.Timestamp("2026-03-01 06:00:00")        # UTC
UCUS_PER = 20


def _ucus(rng, arac, ariza, tf, n):
    """Tek bir ucusun ham sinyalleri ve kirli etiketleri."""
    i = np.arange(n)
    if ariza:
        r = np.clip((i - (tf - 120)) / 120, 0, 1)   # oncul rampa
    else:
        r = np.zeros(n)
    sic = (36 + rng.normal(0, 1.5) + 2.5 * rng.standard_normal(n)
           + 3 * r)
    volt = 24.6 - 0.002 * i - 0.15 * r + 0.05 * rng.standard_normal(n)
    akim = (11 + 2 * np.sin(i / 25) + 1.0 * r
            + 0.5 * rng.standard_normal(n))
    tit = 0.15 + 0.03 * np.abs(rng.standard_normal(n)) + 0.03 * r
    irt = 120 + 12 * np.sin(i / 40) + 1.5 * rng.standard_normal(n)
    if ariza:                                       # gercek olay
        irt = irt - 45 * np.clip((i - (tf - 8)) / 8, 0, 1)
    hiz = 14 + 0.6 * rng.standard_normal(n)
    return r, sic, volt, akim, tit, irt, hiz


```

Aşağıdaki kod, uçuş tek tek ölçümlere dönüşür. Her uçuş için rastgele bir arıza kararı verilir; arızalı uçuşta son altmış saniyelik pencere etiketlenir ve sıcaklık, titreşim ve irtifa değerleri bu pencereye doğru değişir.

```python
def uret(seed=56):
    rng = np.random.default_rng(seed)
    satirlar, truth = [], []
    ucus_no = 0
    for arac in ARACLAR:
        for _ in range(UCUS_PER):
            ucus_no += 1
            ariza = rng.random() < 0.25
            tf = int(rng.integers(200, 290)) if ariza else -1
            n = tf + 1 if ariza else int(rng.integers(206, 297))
            i = np.arange(n)
            r, sic, volt, akim, tit, irt, hiz = _ucus(
                rng, arac, ariza, tf, n)
            gorev = rng.choice(["Keşif", "kesif", "gözetleme",
                                "Gözetleme", "KEŞİF"],
                               p=[.3, .2, .2, .15, .15])
            hk = np.where(rng.random(n) < 0.6, "", "OK")
            hk = hk.astype(object)
            hata = rng.random(n) < 0.002
            hk[hata] = rng.choice(["HATA", "hata", "Hata "],
                                  hata.sum())
            if ariza:                               # olaya bagli kod
                kod = rng.choice(["E17", "e17", "E17 ", "E21"])
                hk[(i >= tf - 3) & (i <= tf + 5)] = kod
            y = ((i >= tf - 30) & (i <= tf)).astype(int)
            # ---- kirlilikler ----
            if arac in FT_ARACLAR:
                irt = irt * 3.28084
            gps = rng.random(n) < 0.003
            irt[gps] += 900
            sen = rng.random(n) < 0.005
            sic[sen] = -999
            sic[rng.random(n) < 0.05] = np.nan
            volt_nan = (volt < 24.2) & (rng.random(n) < 0.35)
            volt[volt_nan] = np.nan
            tit_nan = (gorev == "gözetleme") & (rng.random(n) < 0.25)
            tit = np.where(tit_nan, np.nan, tit)
            t0 = BASLANGIC + pd.Timedelta(minutes=45 * ucus_no)
```

Üretici, kirlilikleri bu döngünün içinde ekler. Ayrıca iki kayıt kümesi, yinelenen satırları ve küçük harfli ya da boşluklu kimlikleri üretir.

```python
            for j in range(n):
                tu = t0 + pd.Timedelta(seconds=2 * j)
                if arac in IST_ARACLAR:
                    z = (tu + pd.Timedelta(hours=3)).strftime(
                        "%Y-%m-%d %H:%M:%S") + "+03:00"
                else:
                    z = tu.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                satirlar.append((z, arac, ucus_no, str(gorev), irt[j],
                                 hiz[j], volt[j], akim[j], sic[j],
                                 tit[j], str(hk[j]), y[j]))
                truth.append((arac in FT_ARACLAR, bool(gps[j]),
                              bool(sen[j]), False))
    cols = ["zaman", "arac_id", "ucus_no", "gorev", "irtifa", "hiz",
            "batarya_v", "akim_a", "sicaklik_c", "titresim_g",
            "hata_kodu", "ariza"]
    df = pd.DataFrame(satirlar, columns=cols)
    tr = pd.DataFrame(truth, columns=["birim_ft", "gps", "sentinel",
                                      "kopya"])
    # ---- yinelenen kayitlar: kopya ve kucuk harfli/bosluklu kimlik
    rng2 = np.random.default_rng(seed + 1)
    kop = rng2.choice(len(df), size=int(0.015 * len(df)),
                      replace=False)
    yak = rng2.choice(len(df), size=int(0.005 * len(df)),
                      replace=False)
    d1 = df.iloc[kop].copy()
    d2 = df.iloc[yak].copy()
    d2["arac_id"] = d2["arac_id"].str.lower() + " "
    t1 = tr.iloc[kop].copy()
    t1["kopya"] = True
    t2 = tr.iloc[yak].copy()
    t2["kopya"] = True
    df = pd.concat([df, d1, d2], ignore_index=True)
    tr = pd.concat([tr, t1, t2], ignore_index=True)
    return df, tr


```

Son parça, araç kayıt tablosunu üretir. Bu tablo her araç için yazılım sürümünü (fit mi metre mi) ve istasyonu tutar. Temizlik sırasında birim kararını bu tabloya bakarak vereceğiz; birimi sadece değerin büyüklüğüne bakarak tahmin etmeyeceğiz.

```python
def kayit_tablosu():
    """Arac kayit tablosu: firmware ve istasyon (merge icin)."""
    return pd.DataFrame({
        "arac_id": ARACLAR,
        "firmware": ["v2_ft" if a in FT_ARACLAR else "v1_m"
                     for a in ARACLAR],
        "istasyon": ["IST" if a in IST_ARACLAR else "ANK"
                     for a in ARACLAR]})
```

Keşifsel veri analizi (EDA), modele dokunmadan önce veriyi tanımanın adımıdır: şekli, eksik değerleri, sütunların gerçek değerlerini, dağılımları ve hedefle ilişkileri incelersin. Aşağıdaki program bu soruları sırayla soruyor.

```python
import csv, os
import numpy as np
import pandas as pd
from ihadata import uret

df, tr = uret(56)
print("satir, sutun:", df.shape)
print("eksik sayisi:")
print(df.isna().sum()[lambda s: s > 0].to_dict())
print("sicaklik = -999 :", int((df.sicaklik_c == -999).sum()))
print("arac_id ham degerler:", df.arac_id.nunique())
print("gorev ham degerler:")
print("  " + ", ".join(sorted(df.gorev.unique())))
print("hata_kodu ham degerler:")
degerler = sorted(df.hata_kodu.unique())
print("  " + ", ".join("'%s'" % v for v in degerler))
print("zaman bicimi (Z):", int(df.zaman.str.endswith("Z").sum()),
      " (+03:00):", int(df.zaman.str.endswith("+03:00").sum()))
print("tam kopya satir:", int(df.duplicated().sum()))
print("ariza orani: %.4f" % df.ariza.mean())

ft = df.irtifa.values
print("irtifa <200 (m benzeri):", int((ft < 200).sum()),
      " >200:", int((ft >= 200).sum()))
bins = np.arange(0, 1400, 50)
sayi, _ = np.histogram(ft, bins=bins)
print("histogram tepe baslari (50 m kutu):",
      [int(bins[k]) for k in range(1, len(sayi) - 1)
       if sayi[k] > sayi[k - 1] and sayi[k] >= sayi[k + 1]
       and sayi[k] > 500])

tr_ft = tr.birim_ft.values
print("ft satirlari (truth):", int(tr_ft.sum()))
```

Programın ikinci kısmı, eksik değerlerin hedefle ilişkisini ve iki birim karışımını ölçüyor. Son satırda çıktı dosyası, Şekil 56.6'yı üretmek için yazılıyor.

```python
print("arac medyan irtifa:")
med = (df.assign(a=df.arac_id.str.strip().str.upper())
         .groupby("a")["irtifa"].median().round(1))
for k in range(0, 10, 2):
    print("  %-7s %6.1f   %-7s %6.1f" % (
        med.index[k], med.iloc[k], med.index[k + 1], med.iloc[k + 1]))

yol = os.path.join("D:/Mevcut Projeler/Kitap/engine/veri",
                   "b56_irtifa_dagilim.csv")
with open(yol, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["irtifa", "birim_ft"])
    for a, b in zip(ft, tr_ft):
        w.writerow(["%.3f" % a, int(b)])
print("csv: b56_irtifa_dagilim.csv")

kirlilik = df.loc[df.ucus_no == 3]
```

Çıktı, EDA'nın ilk tablosudur. Her bulguyu buradan okuyabilirsin.

```term
$ python b56_08_eda.py
satir, sutun: (51401, 12)
eksik sayisi:
{'batarya_v': 4327, 'sicaklik_c': 2494, 'titresim_g': 2509}
sicaklik = -999 : 259
arac_id ham degerler: 20
gorev ham degerler:
  Gözetleme, KEŞİF, Keşif, gözetleme, kesif
hata_kodu ham degerler:
  '', 'E17', 'E17 ', 'E21', 'HATA', 'Hata ', 'OK', 'e17', 'hata'
zaman bicimi (Z): 41352  (+03:00): 10049
tam kopya satir: 755
ariza orani: 0.0331
irtifa <200 (m benzeri): 30704  >200: 20697
histogram tepe baslari (50 m kutu): [100, 350]
ft satirlari (truth): 20602
arac medyan irtifa:
  IHA-01   121.0   IHA-02   121.0
  IHA-03   121.5   IHA-04   121.0
  IHA-05   121.6   IHA-06   121.2
  IHA-07   398.7   IHA-08   396.9
  IHA-09   398.6   IHA-10   398.5
csv: b56_irtifa_dagilim.csv
batarya_v    eksikken ariza 0.1412  dolu iken 0.0232
titresim_g   eksikken ariza 0.0395  dolu iken 0.0328
sicaklik_c   eksikken ariza 0.0365  dolu iken 0.0329
ucus 3 satir: 296  ariza: 0
```

Çıktıdan birkaç sonuç çıkar. Birincisi, satır sayısı 51401'dir; bu sayı kopyaları da içerir. İkincisi, `gorev` sütununda beş farklı yazım var (`Keşif`, `KEŞİF`, `kesif`, `Gözetleme`, `gözetleme`); `hata_kodu` sütununda ise dokuz farklı değer var. Üçüncüsü, zaman damgası iki biçimde: `Z` ile biten UTC ve `+03:00` ile biten yerel saat. Dördüncüsü, eksiklik ile hedef arasında güçlü bir ilişki var: batarya ölçümü eksikken arıza oranı yaklaşık %14, doluyken yaklaşık %2,3. Bu, eksikliğin kendisinin bilgi taşıdığını gösterir; bu noktayı Bölüm 56.9'da ayrıntılı göreceğiz.

Beşincisi ve en önemlisi, irtifa histogramı iki tepe veriyor. Şekil 56.6 bunu gösteriyor: metre cinsinden kaydedilen araçlar 120 civarında, fit cinsinden kaydedilen araçlar ise 400 civarında toplanıyor. Fit ile metre arasında yaklaşık 3,28 kat fark vardır, yani 400 ft yaklaşık 122 m'dir. İki tepe, bir veri hatasının imzasıdır; ham ortalamayı kullanırsan irtifa özniteliği anlamsız olur.

![Şekil 56.6: Ham irtifa histogramı. Metre (v1) ve fit (v2) kayıtları iki ayrı tepe oluşturur.](gorseller/b56_mft.png)

Keşifsel analizden sonra temizlik. Temizliği her adımda sayarak, hangi kuralın kaç satırı etkilediğini kayıt altına alıyoruz. Temizlik kuralları ayrı bir modülde duruyor; hem bu bölümdeki programlar hem de Pipeline aynı kodu kullanıyor. Böylece ölçtüğümüz temizlik ile modele giren temizlik aynı oluyor.

Modül üç tür kural içerir. Metin kuralları (`gorev_normalize`, `hata_normalize`), büyük/küçük harf ve boşluk farklarını kanonik değerlere çevirir. Ana `temizle` fonksiyonu ise zaman damgasını UTC'ye çevirir, kopyaları kaldırır, kayıt tablosunu birleştirir ve birim, sentinel ve sıçrama kurallarını uygular.

```python
# -*- coding: utf-8 -*-
"""Bolum 56 temizleme adimlari. Her kural tek yerde durur."""
import numpy as np
import pandas as pd

GOREV = {"keşif": "kesif", "kesif": "kesif",
         "gözetleme": "gozetleme", "gozetleme": "gozetleme"}
HATA_ESLESME = {"": "YOK", "OK": "YOK", "HATA": "HATA",
                "E17": "E17", "E21": "E21"}


def gorev_normalize(s, naif=False):
    if naif:                                  # yanlis: sadece lower
        t = s.str.strip().str.lower()
    else:                                      # Turkce-duyarli yol
        t = s.str.strip().str.casefold().str.replace("\u0307", "",
                                                    regex=False)
    return t.map(GOREV)


def hata_normalize(s):
    t = s.fillna("").str.strip().str.upper()
    return t.map(HATA_ESLESME).fillna("DIGER")


```

Modülün ikinci kısmı, `temizle` fonksiyonunun kendisidir. Her adımın sayısını `rap` sözlüğünde tutar; bu sözlük, hangi kuralın kaç satır değiştirdiğini gösterir.

```python
def temizle(df, kayit, tr=None, aykiri_sil=True):
    """Ham tabloyu temizler. tr verilirse (sadece test icin) dogrulama
    bayraklarini doner. Kaynak satir numarasi her zaman korunur."""
    rap = {}
    df = df.copy()
    df["kaynak"] = np.arange(len(df))
    df["arac_id"] = df["arac_id"].str.strip().str.upper()
    df["gorev"] = gorev_normalize(df["gorev"])
    df["hata_kodu"] = hata_normalize(df["hata_kodu"])
    df["zaman"] = pd.to_datetime(df["zaman"], format="ISO8601",
                                 utc=True)
    rap["gorev_taninmayan"] = int(df["gorev"].isna().sum())
    dup = df.duplicated(subset=["arac_id", "zaman"], keep="first")
    rap["kopya_silindi"] = int(dup.sum())
    df = df.loc[~dup]
    df = df.merge(kayit, on="arac_id", how="left",
                  validate="many_to_one")
    ft = df["firmware"].eq("v2_ft")
    df.loc[ft, "irtifa"] = df.loc[ft, "irtifa"] / 3.28084
    rap["birim_donusum"] = int(ft.sum())
    df.loc[df["sicaklik_c"].eq(-999), "sicaklik_c"] = np.nan
    df.loc[~df["sicaklik_c"].between(-40, 120), "sicaklik_c"] = np.nan
    df = df.sort_values(["ucus_no", "zaman"]).reset_index(drop=True)
    ref = (df.groupby("ucus_no")["irtifa"]
             .transform(lambda s: s.shift(1).rolling(5, min_periods=3)
                        .median()))
    sapma = (df["irtifa"] - ref).abs() > 100
    rap["nedensel_aykiri"] = int(sapma.sum())
    df["nedensel_bayrak"] = sapma
    if aykiri_sil:
        df.loc[sapma, "irtifa"] = np.nan
    return df, rap
```

Aşağıdaki program temizlik fonksiyonlarını çalıştırıyor ve her adımın sonucunu gerçek kirlilik kayıtlarıyla karşılaştırıyor. Bu karşılaştırma, temizlik kurallarımızın doğru olup olmadığını sayılarla kanıtlamamızı sağlar.

```python
import numpy as np
import pandas as pd
from ihadata import uret, kayit_tablosu
from temizle import gorev_normalize, hata_normalize, temizle

df, tr = uret(56)
kayit = kayit_tablosu()
print("gorev naif (lower) taninmayan:",
      int(gorev_normalize(df["gorev"], naif=True).isna().sum()))
print("gorev dogru taninmayan:",
      int(gorev_normalize(df["gorev"]).isna().sum()))
print("hata_kodu sonrasi:",
      hata_normalize(df["hata_kodu"]).value_counts().to_dict())

temiz, rap = temizle(df, kayit)
print("rapor:")
for k, v in rap.items():
    print("  %-18s %8d" % (k, v))
kept = temiz["kaynak"].values
print("kalan kopya (olmali 0):", int(tr.kopya.values[kept].sum()))
print("ft donusum dogrulama:",
      bool((tr.birim_ft.values[kept] ==
            temiz.firmware.eq("v2_ft").values).all()))
print("sicaklik -999 kalan:", int((temiz.sicaklik_c == -999).sum()))
print("temiz satir:", len(temiz), " kalan NaN irtifa:",
      int(temiz.irtifa.isna().sum()))
gps_say = int(tr.gps.values[kept].sum())
gps_yakalanan = int((tr.gps.values[kept] &
                     temiz.irtifa.isna().values).sum())
print("gps gercek:", gps_say, " yakalanan:", gps_yakalanan)

sayisal = ["irtifa", "hiz", "batarya_v", "akim_a", "sicaklik_c",
           "titresim_g", "ariza"]
print("temiz ozet (ortalama, std, min, maks):")
print(temiz[sayisal].agg(["mean", "std", "min", "max"]).round(2)
      .to_string())
print("ariza ile korelasyon:")
print(temiz[sayisal].corr()["ariza"].round(3).to_string())
```

Aşağıdaki çıktı, her kuralın sayısını ve doğrulamanın sonucunu gösteriyor.

```term
$ python b56_09_temizle.py
gorev naif (lower) taninmayan: 7672
gorev dogru taninmayan: 0
hata_kodu sonrasi: {'YOK': 51085, 'E17': 161, 'HATA': 97, 'E21': 58}
rapor:
  gorev_taninmayan          0
  kopya_silindi          1006
  birim_donusum         20182
  nedensel_aykiri         156
kalan kopya (olmali 0): 0
ft donusum dogrulama: True
sicaklik -999 kalan: 0
temiz satir: 50395  kalan NaN irtifa: 156
gps gercek: 158  yakalanan: 156
temiz ozet (ortalama, std, min, maks):
       irtifa    hiz  batarya_v  akim_a  sicaklik_c  titresim_g  ariza
mean   120.23  14.00      24.36   11.34       36.32        0.18   0.03
std     10.67   0.60       0.16    1.50        2.98        0.02   0.18
min     61.11  11.61      23.75    7.02       23.92        0.15   0.00
max   1022.26  16.30      24.78   16.00       49.81        0.28   1.00
ariza ile korelasyon:
irtifa       -0.195
hiz          -0.003
batarya_v    -0.339
akim_a        0.081
sicaklik_c    0.178
titresim_g    0.233
ariza         1.000
```

Önemli noktalar şöyle. Büyük/küçük harf tuzağı, Türkçe için klasik bir hatadır: `"KEŞİF".lower()` sonucu `keşi̇f` olur ve sonunda birleşik bir nokta karakteri (U+0307) taşır. Bu yüzden naif `lower()` ile eşleme yapan kod `7672` satırı tanımadan geçer. `casefold` ve birleşik noktanın kaldırılması ile bu sayı sıfıra iner. İkinci nokta, kopya silme sayısının (1006) gerçek kopya sayısıyla birebir tutmasıdır; kalan kopya sıfırdır. Üçüncü nokta, birim dönüşümüdür: fit kayıtları metreye çevrildikten sonra, 10 metrelik kutularla ölçüldüğünde tek bir tepe (120 m civarı) kalır. Son olarak, temiz tablonun özeti ve korelasyonu okunabilir hâle gelir: arızayla en güçlü ilişki batarya geriliminde (−0,339) ve titreşimde (0,233) görülür.

Sentinel `-999` değerleri `NaN`'a çevrildi ve fiziksel aralığın (-40 ile 120 °C) dışına çıkan sıcaklıklar da temizlendi. Bu bir "fiziksel kural" örneğidir: sensörün ölçebileceği aralığı bilirsin ve bu bilgiyi kodla zorlarsın.

Aykırı değer konusu en zor olanıdır. Bir değer aykırı görünüyor diye silinmez. Önce sorulması gereken soru, bunun bir hata mı yoksa gerçek bir olay mı olduğudur. İHA'da arıza anındaki hızlı alçalma, istatistiksel olarak aykırıdır, ama tam da aradığımız olaydır. Aşağıdaki program dört yöntemi aynı veride karşılaştırıyor ve her birinin kaç gerçek GPS sıçramasını ve kaç gerçek arıza öncesi satırı bayrakladığını sayıyor.

```python
import csv
import os
import numpy as np
import pandas as pd
from ihadata import uret, kayit_tablosu
from temizle import temizle

df, tr = uret(56)
temiz, _ = temizle(df, kayit_tablosu(), tr, aykiri_sil=False)
kept = temiz["kaynak"].values
gps_t = pd.Series(tr.gps.values[kept], index=temiz.index)
ariza = temiz["ariza"]
x = temiz["irtifa"].dropna()

# 1) Tum veri uzerinde IQR
q1, q3 = x.quantile([0.25, 0.75])
iqr = q3 - q1
alt, ust = q1 - 1.5 * iqr, q3 + 1.5 * iqr
f_iqr = (temiz.irtifa < alt) | (temiz.irtifa > ust)

# 2) Tum veri uzerinde robust z (medyan ve MAD)
med = x.median()
mad = (x - med).abs().median()
f_z = (temiz.irtifa - x.mean()).abs() / x.std() > 3
f_rz = (0.6745 * (temiz.irtifa - med) / mad).abs() > 3.5

# 3) Ucus ici robust z (bu uçusun kendi medyani)
ref_med = temiz.groupby("ucus_no")["irtifa"].transform("median")
sapma = (temiz.irtifa - ref_med).abs()
ref_mad = sapma.groupby(temiz["ucus_no"]).transform("median")
f_frz = (0.6745 * (temiz.irtifa - ref_med) / ref_mad).abs() > 3.5

```

Programın ikinci kısmı, bayrakları yazdırır ve Şekil 56.7 için tek bir arızalı uçuşu CSV'ye kaydeder. Aşağıdaki çıktı, dört yöntemi yan yana gösteriyor.

```python
print("Q1=%.1f Q3=%.1f IQR=%.1f" % (q1, q3, iqr))
print("alt=%.1f ust=%.1f" % (alt, ust))
print("medyan=%.1f MAD=%.2f" % (med, mad))
print("ort=%.1f ss=%.2f" % (x.mean(), x.std()))
print("%-18s %6s %6s %6s %6s" % ("yontem", "bayrak", "gps",
                                 "ariza", "digeri"))
for ad, f in [("global z (3 ss)", f_z), ("global IQR", f_iqr),
              ("global robust z", f_rz),
              ("ucus-ici robust z", f_frz)]:
    print("%-18s %6d %6d %6d %6d" % (
        ad, int(f.sum()), int((f & gps_t).sum()),
        int((f & (ariza == 1)).sum()),
        int((f & (gps_t == 0) & (ariza == 0)).sum())))

print("nedensel bayrak = gps:",
      int((temiz.nedensel_bayrak & gps_t).sum()), "/",
      int(temiz.nedensel_bayrak.sum()))

# Grafik icin bir arizali ucus seç ve CSV'ye yaz
hedef = None
for u in sorted(temiz.ucus_no.unique()):
    g = temiz[temiz.ucus_no == u]
    if g.ariza.sum() > 0 and g.arac_id.iloc[0] == "IHA-01":
        hedef = u
        break
g = temiz[temiz.ucus_no == hedef]
yol = os.path.join("D:/Mevcut Projeler/Kitap/engine/veri",
                   "b56_aykiri_ucus.csv")
with open(yol, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["adim", "irtifa", "gps", "ariza", "iqr", "alt",
                "ust"])
    for k, (i, r) in enumerate(g.iterrows()):
        w.writerow([k, "%.3f" % r.irtifa, int(gps_t.loc[i]),
                    int(r.ariza), int(f_iqr.loc[i]),
                    "%.3f" % alt, "%.3f" % ust])
print("ornek ucus:", hedef, "satir:", len(g))
```

Aşağıdaki çıktı, dört yöntemin bayrak sayılarını ve bunların GPS, arıza ve diğer satırlarla kesişimini gösteriyor. Sütunlar bazı satırları iki kez sayabilir, çünkü bir GPS sıçraması arıza penceresinin içinde de olabilir.

```term
$ python b56_10_aykiri.py
Q1=111.8 Q3=128.5 IQR=16.7
alt=86.8 ust=153.5
medyan=121.3 MAD=8.15
ort=122.2 ss=40.98
yontem             bayrak    gps  ariza digeri
global z (3 ss)       158    158      4      0
global IQR            311    158    157      0
global robust z       236    158     82      0
ucus-ici robust z     232    158     78      0
nedensel bayrak = gps: 156 / 156
ornek ucus: 5 satir: 256
```

Tablo, aykırı değer tespitinin neden dikkatli yapılması gerektiğini açıkça gösteriyor. Standart z-skoru (ortalama ve standart sapma ile, 3'ün üstü) yalnızca GPS sıçramalarını yakalıyor ama arızalı satırların neredeyse hiçbirini yakalamıyor. Sebebi şu: GPS sıçramaları standart sapmayı 10'dan 41'e şişiriyor, bu yüzden eşik çok genişliyor ve sıçramaların etkisi tespit yönteminin kendisini bozuyor. Bu, **maskeleme** denen olgudur: aykırı değerler, onları bulmak için kullanılan istatistikleri bozar.

IQR ve robust z (medyan ile MAD) ise sıçramaların etkisini sınırlar, ama bu kez gerçek arıza satırlarını da bayraklar: IQR yüz elli yedi arıza satırını aykırı sayıyor. Bunun nedeni basittir. Arıza öncesi irtifa düşüşü, bütün veri kümesinin dağılımına göre gerçekten uç bir değerdir. "Etiketsiz ama bayraklanan" sütunundaki sıfır da bir şey anlatır: bu veride bayraklanan her satır ya bir GPS sıçraması ya da bir arıza öncesi satırıdır.

En iyi sonuç, kuralı nedensel olarak yazdığımızda çıkar. `nedensel_bayrak` kuralında her satır yalnızca kendisinden önceki beş satırın medyanıyla kıyaslanır. Bu yöntem 156 GPS sıçramasını, sıfır yanlış pozitifle yakalar. Gerçek arıza satırlarına dokunmaz. Kuralın sınırı ise uçuşun ilk üç satırıdır, çünkü bu satırların geçmişi yoktur; o nedenle iki sıçrama kaçar ve bunları ancak aralık kontrolü yakalar (Bölüm 56.12).

Şekil 56.7, bir arızalı uçuşun irtifa serisini, IQR sınırlarını ve GPS sıçramalarını gösteriyor. Gri bölge arıza penceresidir; sıçramalar pencerenin dışında da ortaya çıkabilir.

![Şekil 56.7: Bir arızalı uçuşun irtifası. Global IQR bandı, arıza penceresi ve gerçek GPS sıçramaları.](gorseller/b56_aykiri.png)

## 56.9 Eksik veri: mekanizmalar, doldurma ve sızıntı

Eksik veri, her gerçek veri kümesinde vardır ve nasıl ele alındığı sonucu doğrudan değiştirir. Önce mekanizmayı anlamak gerekir, çünkü doldurma yöntemi mekanizmaya bağlıdır. Literatürde üç tür vardır. **MCAR** (tamamen rastgele eksik): eksiklik ne gözlenen ne de gözlenmeyen hiçbir değere bağlıdır. Bir sensör paketinin rastgele kaybolması buna örnektir. **MAR** (gözlenen değere bağlı eksik): eksiklik başka gözlenen bir değere bağlıdır; örneğin gözetleme görevlerinde titreşim sensörünün hiç kaydedilmemesi gibi. **MNAR** (gözlenmeyen değere bağlı eksik): eksiklik değerin kendisine bağlıdır; düşük batarya gerilimlerinin ölçülememesi gibi. MNAR en tehlikelisidir, çünkü onu gözlenen verilerden tespit etmek zordur.

Eksik veriyi üç şekilde ele alabilirsin. Silmek (satırları atmak) en basit yoldur, ama MAR ve MNAR'da sonucu yanlılaştırır. Doldurmak, bir değer atamak demektir: ortalama, medyan ya da en sık değer. Eksiklik göstergesi (indicator) ise eksikliğin kendisini ayrı bir özniteliğe dönüştürür; bu, MNAR'da bilgi kaybını önler. Ayrıca zaman serisinde ileri doldurma (`ffill`) kullanılabilir; bunun riski, eski değerin gerçek durumu yansıtmamasıdır (genel bilgi; bu bölümde ölçmedik).

Aşağıdaki program bu üç mekanizmayı ve dört yöntemi, bilinen bir veri kümesi üzerinde deniyor. Kullanılan veri, scikit-learn'ün yerleşik `diabetes` veri kümesidir; eksiklik, bir özniteliğin 20%'sine yapay olarak eklenir ve 200 bağımsız tekrarda ortalama alınır. Gerçek değer bilindiği için yöntemlerin yanlılığını ve varyans bozulmasını ölçebiliyoruz.

```python
import csv, os
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.impute import KNNImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

X, y = load_diabetes(return_X_y=True)
n = len(y)
age, bmi = X[:, 0], X[:, 2]
rank_age = age.argsort().argsort() / (n - 1)
rank_bmi = bmi.argsort().argsort() / (n - 1)

def maske(mek, rng, p=0.2):
    if mek == "MCAR":                    # tamamen rastgele
        pr = np.full(n, p)
    elif mek == "MAR":                   # yasa bagli (gozlenen)
        pr = 2 * p * rank_age
    else:                                # MNAR: bmi'ye bagli
        pr = 2 * p * rank_bmi
    return rng.random(n) < pr

def yontemler(Xm):
    out = {}
    obs = ~np.isnan(Xm[:, 2])
    out["silme"] = Xm[obs, 2]
    for ad, sta in [("ortalama", "mean"), ("medyan", "median")]:
        v = Xm[:, 2].copy()
        v[~obs] = np.nanmean(v) if sta == "mean" else np.nanmedian(v)
        out[ad] = v
    out["knn"] = KNNImputer(n_neighbors=5).fit_transform(Xm)[:, 2]
    return out, obs

```

Programın ikinci kısmı, eksiklik göstergesinin test R² değerine etkisini ölçüyor. Bu deney, MNAR durumunda göstergenin ne kadar önemli olduğunu gösterir.

```python
print("%-6s %-10s %8s %8s %8s" % ("mek.", "yontem", "sd oran",
                                  "sapma", "kor(y)"))
sonuc = {}
for mek in ["MCAR", "MAR", "MNAR"]:
    acc = {}
    for s in range(200):
        rng = np.random.default_rng(s)
        m = maske(mek, rng)
        Xm = X.copy()
        Xm[m, 2] = np.nan
        out, obs = yontemler(Xm)
        for k, v in out.items():
            yy = y[obs] if k == "silme" else y
            sd_r = v.std() / bmi.std()
            sap = (v.mean() - bmi.mean()) / bmi.std()
            kor = np.corrcoef(v, yy)[0, 1]
            acc.setdefault(k, []).append((sd_r, sap, kor))
    for k, vals in acc.items():
        a = np.array(vals).mean(axis=0)
        print("%-6s %-10s %8.3f %8.2f %8.3f"
              % (mek, k, a[0], a[1], a[2]))
        sonuc[(mek, k)] = a

```

Programın son kısmı, sonuçları CSV'ye yazar ve ekrana basar. Şekil 56.8, aynı tabloyu grafik olarak sunuyor.

```python
kayip_ind = []
for s in range(30):
    rng = np.random.default_rng(s)
    m = maske("MNAR", rng)
    Xm = X.copy()
    Xm[m, 2] = np.nan
    tr_i = np.arange(n) < int(0.7 * n)
    med = np.nanmedian(Xm[tr_i, 2])
    b = np.where(np.isnan(Xm[:, 2]), med, Xm[:, 2])
    ind = np.isnan(Xm[:, 2]).astype(float)
    r1 = LinearRegression().fit(b[tr_i, None], y[tr_i])
    r2 = LinearRegression().fit(np.c_[b, ind][tr_i], y[tr_i])
    kayip_ind.append((
        r2_score(y[~tr_i], r1.predict(b[~tr_i, None])),
        r2_score(y[~tr_i], r2.predict(np.c_[b, ind][~tr_i]))))
kayip_ind = np.array(kayip_ind).mean(axis=0)
print("MNAR test R2 (sadece bmi): %.3f" % kayip_ind[0])
print("MNAR test R2 (bmi+indikator): %.3f" % kayip_ind[1])

yol = os.path.join("D:/Mevcut Projeler/Kitap/engine/veri",
                   "b56_eksik_olcum.csv")
with open(yol, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["mekanizma", "yontem", "sd_orani", "sapma",
                "korelasyon"])
    for (mek, k), a in sonuc.items():
        w.writerow([mek, k, "%.4f" % a[0], "%.4f" % a[1],
                    "%.4f" % a[2]])
print("csv yazildi")
```

Aşağıdaki çıktı, üç mekanizma için dört doldurma yönteminin standart sapma oranını, yanlılığını ve korelasyonunu, ayrıca MNAR eksiklik göstergesinin R² kazancını gösteriyor.

```term
$ python b56_11_eksik.py
mek.   yontem      sd oran    sapma   kor(y)
MCAR   silme         1.002    -0.00    0.587
MCAR   ortalama      0.897    -0.00    0.525
MCAR   medyan        0.899    -0.03    0.524
MCAR   knn           0.939     0.00    0.572
MAR    silme         1.016    -0.03    0.588
MAR    ortalama      0.910    -0.03    0.524
MAR    medyan        0.912    -0.06    0.519
MAR    knn           0.948     0.00    0.570
MNAR   silme         0.967    -0.14    0.579
MNAR   ortalama      0.865    -0.14    0.506
MNAR   medyan        0.866    -0.17    0.494
MNAR   knn           0.907    -0.09    0.561
MNAR test R2 (sadece bmi): 0.239
MNAR test R2 (bmi+indikator): 0.289
csv yazildi
```

Çıktıdaki en önemli sayı, `ortalama` satırındaki MCAR sd oranıdır: 0,897. Bu, teorik beklentiyle örtüşür. Ortalama doldurmada eksik olmayan değerlerin payı `1 − p = 0,8` olur ve standart sapma `√0,8 ≈ 0,894` oranında küçülür. Yani doldurma dağılımı daraltır ve yapay olarak "daha tutarlı" bir veri üretir. Bu, modelin varyansını hafife almasına yol açar. Medyan benzer bir daraltma yapar. k-NN doldurma daha az daraltır, çünkü eksik değeri diğer özniteliklerin komşularından tahmin eder.

MNAR satırları, en büyük yanlılığı üretir. Eksik değerler yüksek `bmi` olanlarda yoğunlaştığı için, gözlenen değerlerin ortalaması aşağı kayar; sapma sütununda −0,14 standart sapma görüyorsun. Eksiklik göstergesi, bu bilgiyi modele geri verir: test R² değeri 0,239'dan 0,289'a çıkar. Yani eksik olmanın kendisi bir sinyal taşır ve bunu saklamak modeli iyileştirir.

Şekil 56.8, bu tabloyu üç mekanizma için yan yana gösteriyor. Kesikli çizgi, ortalama doldurmanın teorik daraltma oranıdır; ortalama ve medyan çubukları bu çizginin hemen altında kalır.

![Şekil 56.8: Eksik veri mekanizmaları ve doldurma yöntemlerinin standart sapma oranı. Kesikli çizgi, ortalama doldurmanın teorik değeridir.](gorseller/b56_eksik.png)

Eksik veri konusunda en önemli kural, doldurmanın **veri bölündükten sonra ve yalnızca eğitim kümesinden öğrenerek** yapılmasıdır. Tüm veri üzerinde hesaplanan bir medyan, test kümesinin bilgisini eğitime sızdırır (Bölüm 54'teki sızıntı). Bu yüzden doldurma adımını Pipeline'a koyacağız; onu Bölüm 56.14'te, modelle birlikte göreceğiz.

## 56.10 Öznitelik mühendisliği

Öznitelik mühendisliği, ham ölçümleri modelin kullanabileceği sayılara dönüştürme sanatıdır. Ham bir sensör akışı nadiren doğrudan iyi bir girdidir. Bir arızayı önceden gösteren şey genellikle bir değişimdir (sıcaklığın son bir dakikadaki artışı), bir oran (güç ile hız), bir döngüsel desen (günün saati) ya da bir pencere istatistiğidir (geçmiş ortalamadan sapma).

Önce bu bölümün öznitelik modülünü görelim. Modül iki fonksiyon içerir. `ozellik_tablosu`, her satır için yalnızca geçmiş değerleri kullanan pencere öznitelikleri üretir. `gecmis_olmayan_pencere` ise bilerek yanlış yazılmıştır: merkezi bir pencere kullanır ve gelecek değerleri görür. Sızıntı testimizin karşılaştırma tabanı budur.

```python
# -*- coding: utf-8 -*-
"""Bolum 56 oznitelik uretimi. Kural: t aninda yalnizca t ve oncesi
kullanilir (gecmis pencere). Gelecek degerler asla girmez."""
import numpy as np
import pandas as pd

SAYISAL = ["irtifa", "hiz", "batarya_v", "akim_a", "sicaklik_c",
           "titresim_g", "guc_w", "sic_ort30", "sic_fark",
           "tit_max30",
           "volt_fark", "irt_fark", "saat_sin", "saat_cos"]
KATEGORIK = ["gorev"]


def ozellik_tablosu(t):
    t = t.sort_values(["ucus_no", "zaman"]).copy()
    g = t.groupby("ucus_no", sort=False)
    gec = lambda c, w, f: g[c].transform(
        lambda s: getattr(s.shift(1).rolling(w, min_periods=5), f)())
    t["guc_w"] = t["batarya_v"] * t["akim_a"]
    t["sic_ort30"] = gec("sicaklik_c", 30, "mean")
    t["sic_fark"] = t["sicaklik_c"] - t["sic_ort30"]
    t["tit_max30"] = gec("titresim_g", 30, "max")
    t["volt_fark"] = t["batarya_v"] - gec("batarya_v", 30, "mean")
    t["irt_fark"] = t["irtifa"] - gec("irtifa", 10, "median")
    saat = t["zaman"].dt.hour + t["zaman"].dt.minute / 60
    t["saat_sin"] = np.sin(2 * np.pi * saat / 24)
    t["saat_cos"] = np.cos(2 * np.pi * saat / 24)
    return t


def gecmis_olmayan_pencere(t):
    """Yanlis (sizdiran) surum: merkezi pencere, gelecegi de gorur."""
    t = t.sort_values(["ucus_no", "zaman"]).copy()
    g = t.groupby("ucus_no", sort=False)
    t["sic_ort30"] = g["sicaklik_c"].transform(
        lambda s: s.rolling(31, center=True, min_periods=5).mean())
    return t
```

Modüldeki `SAYISAL` listesi, Pipeline'ın kullanacağı öznitelikleri tanımlar. `guc_w`, batarya gerilimi ile akımın çarpımıdır (güç = V·I); bu, alan bilgisinden öznitelik üretmenin basit bir örneğidir. Gerilim ile akımı ayrı ayrı vermek yerine çarpımı vermek, modelin işini kolaylaştırır.

Döngüsel özniteliklerle başlayalım. Saat gibi bir değer, 23 ile 0 arasında çok yakın olmasına rağmen sayısal olarak 23 birim uzaktır. Çözüm, değeri bir çember üzerinde bir noktaya çevirmektir: `sin` ve `cos`. Aşağıdaki program ve Şekil 56.9 bu fikri ölçüyor.

Ölçekleme, özniteliklerin büyüklüğünü eşitlemek için kullanılır. Uzaklığa dayalı modeller (k-NN, k-means, SVM) büyük ölçekli öznitelikleri öne çıkarır. Ağaçlar ise tek tek eşikleri değerlendirdiği için ölçekten etkilenmez. Aşağıdaki program aynı veride k-NN'nin ölçeklemeden ve üç farklı ölçeklemeyle doğruluğunu ölçüyor; ayrıca ağacın ölçekten bağımsız olduğunu gösteriyor. Ayrıca çarpık bir dağılım için log ve Box-Cox dönüşümünü, etkileşim teriminin doğrusal olmayan bir ilişkiyi nasıl yakaladığını da gösteriyor.

```python
import csv, os
import numpy as np
from scipy.stats import skew
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import (StandardScaler, MinMaxScaler,
                                   RobustScaler, PowerTransformer)

X, y = load_breast_cancer(return_X_y=True)
cv = StratifiedKFold(5, shuffle=True, random_state=56)
print("kNN (k=5) olcekleme karsilastirmasi, 5 katli CV:")
satir = []
adaylar = [("olceksiz", None), ("standart", StandardScaler()),
           ("min-max", MinMaxScaler()), ("robust", RobustScaler())]
for ad, sc in adaylar:
    adim = [] if sc is None else [sc]
    p = make_pipeline(*adim, KNeighborsClassifier(n_neighbors=5))
    s = cross_val_score(p, X, y, cv=cv)
    print("  %-10s %.4f +- %.4f" % (ad, s.mean(), s.std()))
    satir.append((ad, "%.4f" % s.mean(), "%.4f" % s.std()))
for ad, sc in [("olceksiz", None), ("standart", StandardScaler())]:
    adim = [] if sc is None else [sc]
    p = make_pipeline(*adim, DecisionTreeClassifier(max_depth=4,
                                                    random_state=56))
    s = cross_val_score(p, X, y, cv=cv)
    print("agac (%s) %.4f" % (ad, s.mean()))

yol = os.path.join("D:/Mevcut Projeler/Kitap/engine/veri",
                   "b56_olcek_knn.csv")
with open(yol, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["olcekleme", "dogruluk", "std"])
    w.writerows(satir)

```

Programın ikinci kısmı, ölçeklemeden sonra dönüşümlerin ve döngüsel mesafenin sonuçlarını hesaplıyor.

```python
print("--- donusum ---")
rng = np.random.default_rng(56)
gelir = rng.lognormal(mean=3.0, sigma=0.8, size=5000)
print("carpiklik ham: %.3f  log1p: %.3f" % (
    skew(gelir), skew(np.log1p(gelir))))
pt = PowerTransformer(method="box-cox")
bc = pt.fit_transform(gelir.reshape(-1, 1)).ravel()
print("box-cox lambda: %.3f  carpiklik: %.3f" % (
    pt.lambdas_[0], skew(bc)))

saat = np.array([0, 23])
ang = 2 * np.pi * saat / 24
nokta = np.c_[np.cos(ang), np.sin(ang)]     # saat -> cember
print("dongusel (sin,cos) 23 ile 0 mesafesi:",
      round(float(np.linalg.norm(nokta[0] - nokta[1])), 4))

x1 = rng.standard_normal(2000)
x2 = rng.standard_normal(2000)
t = x1 * x2 + 0.1 * rng.standard_normal(2000)
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score as cvs
r_dogrusal = cvs(LinearRegression(), np.c_[x1, x2], t, cv=5).mean()
X_etk = np.c_[x1, x2, x1 * x2]
r_etk = cvs(LinearRegression(), X_etk, t, cv=5).mean()
print("R2 dogrusal: %.3f  etkilesimli: %.3f" % (r_dogrusal, r_etk))
```

Aşağıdaki çıktı, ölçekleme, dönüşüm, döngüsel mesafe ve etkileşim deneylerinin sonuçlarını gösteriyor.

```term
$ python b56_12_ozellik.py
kNN (k=5) olcekleme karsilastirmasi, 5 katli CV:
  olceksiz   0.9385 +- 0.0147
  standart   0.9649 +- 0.0146
  min-max    0.9684 +- 0.0197
  robust     0.9631 +- 0.0128
agac (olceksiz) 0.9333
agac (standart) 0.9333
--- donusum ---
carpiklik ham: 2.904  log1p: 0.137
box-cox lambda: -0.002  carpiklik: 0.000
dongusel (sin,cos) 23 ile 0 mesafesi: 0.2611
R2 dogrusal: -0.008  etkilesimli: 0.990
```

Çıktının ilk satırları ölçeklemenin etkisini gösteriyor. Ölçeksiz k-NN doğruluğu 0,9385 iken standartlaştırılmış olanı 0,9649'dur. Ağacın doğruluğu ise iki durumda da 0,9333'te kalıyor: ağaç her özniteliği tek başına eşiklediği için ölçek değişikliği sonucu değiştirmez. Çarpık dağılımda (ham çarpıklık 2,904), log dönüşümü çarpıklığı 0,137'ye düşürüyor. Box-Cox'un bulduğu λ değeri −0,002'dir, yani neredeyse 0; bu, Box-Cox'un log dönüşümüne denk düştüğü anlamına gelir. Etkileşim ise doğrusal modelin kaçırdığı ilişkiyi yakalar: `x₁·x₂` terimi eklenince R², −0,008'den 0,990'a çıkar.

Döngüsel kodlama, 23 ile 0 arasındaki ham fark 23 iken çember üzerindeki uzaklığın 0,261 olduğunu gösteriyor. Şekil 56.9, saatlerin çemberini ve bu iki noktanın yan yana olduğunu çiziyor.

![Şekil 56.9: Saatin döngüsel kodlaması. 23 ve 0 ham değerde uzak, çember üzerinde yan yanadır.](gorseller/b56_dongusel.png)

Ölçeklemenin sonucu ise Şekil 56.10'da. Standartlaştırma ve min-max, ölçeksiz k-NN'ye göre belirgin bir kazanç sağlıyor; robust ölçekleme de benzer bir sonuç veriyor. Hata çubukları 5 katlı çapraz doğrulamadaki oynamayı gösterir; farklar bu oynamanın yakınında olduğu için ölçeklemenin seçimi ayrıca düşünülmelidir.

![Şekil 56.10: Ölçekleme yöntemlerine göre k-NN doğruluğu (5 katlı çapraz doğrulama, hata çubukları standart sapma).](gorseller/b56_olcek.png)

Kategorik değişkenler için **tek sıcak kodlama** (one-hot) yaygındır. Görev türü gibi küçük bir kümede bu güvenlidir. Ama `ucus_no` gibi yüzlerce değerli bir kategoride sütun sayısı patlar. Bu durumda **hedef kodlama** kullanılır: her kategori yerine o kategorideki arıza oranı yazılır. Bu yöntemin tehlikesi büyüktür. Eğer oran tüm veriden hesaplanırsa, her satır kendi etiketini de kullanmış olur ve bu bir sızıntıdır. Doğru yöntem, **çapraz doğrulama katlarında dışarıda bırakma** (out-of-fold) yapmaktır: her satırın değeri, o satırın katı dışındaki veriden hesaplanır.

Pencere öznitelikleri zaman serisinin en güçlü araçlarıdır, ama en kolay sızdırılanlardır. `ozellik_tablosu`, her satır için yalnızca geçmiş değerleri kullanır: `shift(1)` mevcut satırı dışarıda bırakır, `rolling` ise geçmiş pencereyi toplar. Bu kuralın doğru uygulandığını bir deneyle ölçmek gerekir. Aşağıdaki program, rastgele seçilmiş 40 satırda, o satırdan sonraki tüm değerleri bozuyor ve özniteliğin değişip değişmediğine bakıyor. Gelecek bilgisi kullanılmıyorsa özniteliğin değişmemesi gerekir. Program aynı testi merkezi (sızdıran) pencere üzerinde de çalıştırıyor. Ayrıca naif ve out-of-fold hedef kodlamayı yan yana karşılaştırıyor.

```python
import numpy as np
import pandas as pd
from ihadata import uret, kayit_tablosu
from temizle import temizle
from ozellik import ozellik_tablosu, gecmis_olmayan_pencere
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score

df, tr = uret(56)
temiz, _ = temizle(df, kayit_tablosu())
ozel = ozellik_tablosu(temiz)

rng = np.random.default_rng(56)
def gelecek_testi(fn, adet=40):
    ok, bozuk = 0, 0
    sayilan = 0
    secimler = rng.choice(len(ozel), adet, replace=False)
    for k in secimler:
        t_satir = ozel.loc[k]
        bas = ozel.index[ozel.ucus_no == t_satir.ucus_no]
        if k not in bas or k == bas[-1]:
            continue
        ust = bas[bas > k]
        pert = temiz.copy()
        pert.loc[ust, "sicaklik_c"] = (pert.loc[ust, "sicaklik_c"]
                                       + 500)
        pert.loc[ust, "titresim_g"] = 9.0
        sayilan += 1
        a = fn(temiz).loc[k, "sic_ort30"]
        b = fn(pert).loc[k, "sic_ort30"]
        if np.isnan(a) and np.isnan(b):
            ok += 1
        elif abs(a - b) < 1e-9:
            ok += 1
        else:
            bozuk += 1
    return ok, bozuk, sayilan

```

Programın ikinci kısmı hedef kodlamayı ölçüyor.

```python
print("gecmis pencere  (ok, bozuk):",
      gelecek_testi(lambda t: ozellik_tablosu(t)))
print("merkezi pencere (ok, bozuk):",
      gelecek_testi(gecmis_olmayan_pencere))

# hedef kodlama: ucus_no uzerinden naif ve out-of-fold karsilastirma
ucus = temiz["ucus_no"].values
y = temiz["ariza"].values
global_ort = y.mean()
naif = pd.Series(y).groupby(ucus).transform("mean").values
print("naif hedef kodlama AUC (kendi etiketi dahil): %.3f"
      % roc_auc_score(y, naif))
oof = np.full(len(y), global_ort)
for tr_i, te_i in GroupKFold(5).split(y, y, ucus):
    harita = pd.Series(y[tr_i]).groupby(ucus[tr_i]).mean()
    oof[te_i] = pd.Series(ucus[te_i]).map(harita).fillna(
        global_ort).values
print("out-of-fold hedef kodlama AUC:     %.3f"
      % roc_auc_score(y, oof))
```

Aşağıdaki çıktı, sızıntı testinin ve hedef kodlama karşılaştırmasının sonuçlarını gösteriyor.

```term
$ python b56_13_sizinti.py
gecmis pencere  (ok, bozuk): (40, 0, 40)
merkezi pencere (ok, bozuk): (0, 40, 40)
naif hedef kodlama AUC (kendi etiketi dahil): 0.889
out-of-fold hedef kodlama AUC:     0.500
```

Test sonucu net: geçmişe bakan pencere 40 denemenin 40'ında gelecek değişikliklerine karşı duyarsız kaldı; merkezi pencere ise 40'ının 40'ında sızdırdı. Hedef kodlama tarafında, naif yöntemle AUC 0,889 çıkıyor. Bu değer bir başarı değil, bir sızıntı belirtisidir: her satır kendi etiketini kodlamada kullandığı için model ezbere yakın bir sonuç görür. Out-of-fold sürümde AUC 0,500 yani rastgele tahmin düzeyine iner. Bu, hedef kodlamanın gerçek değerinin, yalnızca dışarıda bırakma ile ölçülebileceğini gösterir.

Son olarak öznitelik seçimi. Üç yaklaşım vardır. **Filtre** yöntemleri her özniteliği tek başına hedefle ilişkisine göre sıralar (karşılıklı bilgi gibi). Hızlıdır, ama özniteliklerin birlikte oluşturduğu etkileşimi kaçırabilir. **Sarmalayıcı** yöntemler (RFE gibi) modeli tekrar tekrar eğitip en az katkılı özniteliği eler; pahalıdır ama model-bağımlıdır. **Gömülü** yöntemler, eğitim sırasında seçimi yapar: L1 düzenlileştirmesi katsayıları sıfıra iterek seyrek bir küme bırakır (Bölüm 58'de ayrıntısı var). Aşağıdaki program üç yaklaşımı, Pipeline içinde, aynı grup çapraz doğrulamasıyla karşılaştırıyor. Eksiklik göstergeleri de öznitelik kümesinin parçasıdır.

```python
import time
import warnings
import numpy as np
import pandas as pd
from sklearn.feature_selection import (SelectKBest, RFE,
                                       SelectFromModel,
                                       mutual_info_classif)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (StratifiedGroupKFold,
                                     cross_val_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from ihadata import uret, kayit_tablosu
from temizle import temizle
from ozellik import ozellik_tablosu, SAYISAL

warnings.filterwarnings("ignore")
df, _ = uret(56)
t = ozellik_tablosu(temizle(df, kayit_tablosu())[0])
X = t[SAYISAL]
y = t["ariza"].values
g = t["ucus_no"].values
cv = StratifiedGroupKFold(5, shuffle=True, random_state=56)


def bilgi(a, b):
    return mutual_info_classif(a, b, random_state=56)


```

```python
def hat(ad, sec):
    p = make_pipeline(SimpleImputer(strategy="median",
                                    add_indicator=True),
                      StandardScaler(), sec,
                      LogisticRegression(max_iter=3000))
    s = cross_val_score(p, X, y, groups=g, cv=cv,
                        scoring="average_precision")
    print("%-26s AP %.3f+-%.3f" % (ad, s.mean(), s.std()))
    return p


hat("hepsi (secim yok)", SelectKBest(bilgi, k="all"))
filtre = hat("filtre (karsilikli bilgi)",
             SelectKBest(bilgi, k=5))
hat("sarmalayici (RFE)", RFE(LogisticRegression(max_iter=3000),
                             n_features_to_select=5))
hat("gomulu (L1)", SelectFromModel(LogisticRegression(
    penalty="l1", solver="liblinear", C=0.1)))

# Secilen oznitelikleri isimleriyle yaz
adimlar = make_pipeline(SimpleImputer(strategy="median",
                                      add_indicator=True),
                        StandardScaler(),
                        SelectKBest(bilgi, k=5)).fit(X, y)
isimler = adimlar[0].get_feature_names_out(SAYISAL)
secilen = adimlar[2].get_support()
print("filtre secilen:")
for ad in isimler[secilen]:
    print("  ", ad)
Z = StandardScaler().fit_transform(
    SimpleImputer(strategy="median", add_indicator=True)
    .fit_transform(X))
l1 = LogisticRegression(penalty="l1", solver="liblinear", C=0.1)
l1.fit(Z, y)
print("L1 sifir olmayan katsayi:", int((l1.coef_ != 0).sum()),
      "/", Z.shape[1])
rfe = RFE(LogisticRegression(max_iter=3000),
```

Aşağıdaki çıktı, dört senaryonun AP değerlerini, filtre ve sarmalayıcı yöntemlerin seçtiği öznitelikleri ve L1'in sıfırladığı katsayı sayısını gösteriyor.

```term
$ python b56_18_secim_apply.py
hepsi (secim yok)          AP 0.891+-0.031
filtre (karsilikli bilgi)  AP 0.672+-0.075
sarmalayici (RFE)          AP 0.670+-0.020
gomulu (L1)                AP 0.891+-0.031
filtre secilen:
   batarya_v
   sic_ort30
   tit_max30
   saat_sin
   saat_cos
L1 sifir olmayan katsayi: 17 / 24
RFE secilen:
   batarya_v
   guc_w
   volt_fark
   missingindicator_guc_w
   missingindicator_volt_fark
```

Çıktı, yöntemlerin sonucunu gösteriyor. Seçim yapılmadığında (tüm özniteliklerle) AP 0,891 olur. Filtre yöntemi, karşılıklı bilgiye göre ilk beşi seçip AP'yi 0,672'ye düşürüyor: seçilen öznitelikler içinde eksiklik göstergeleri yok, ve güç (`guc_w`) ile gerilim değişimi (`volt_fark`) gibi birlikte çalışan öznitelikler kaçıyor. RFE de benzer biçimde 0,670 veriyor ve seçtiği öznitelikler arasında eksiklik göstergeleri var. L1 düzenlileştirmesi ise 24 öznitelikten 17'sini tutuyor ve AP'yi korur. Bu, bir seçim yönteminin değerinin sadece hızı ya da basitliğiyle değil, modelin kullandığı etkileşimleri koruyup korumamasıyla ölçüldüğünü gösterir.

## 56.11 Dengesiz veri: ağırlık, yeniden örnekleme ve sızıntı

Arıza tahmininde pozitif sınıf nadirdir: veri kümemizde etiketlerin yalnızca yaklaşık %3'ü pozitiftir. Model, çoğunluk sınıfını her zaman tahmin ederek yüksek bir doğruluk elde edebilir. Bu yüzden dengesizlik, veri düzeyinde ve değerlendirme düzeyinde ele alınmalıdır. Bu bölümde veri düzeyindeki iki tekniği, **sınıf ağırlığı** ve **yeniden örneklemeyi** ele alıyoruz; metriklerin seçimi ve eşik ayarı Bölüm 57'nin konusudur.

Sınıf ağırlığı, yanlış bir pozitif tahminin cezasını azınlık sınıfı için büyütür. `class_weight="balanced"` her sınıfın ağırlığını ters orantılı biçimde ayarlar. Yeniden örnekleme ise veriyi değiştirir: çoğunluk sınıfından seyrekleştirme (undersampling) ya da azınlık sınıfını çoğaltma (oversampling) yapar. Çoğaltma, en basit hâliyle aynı satırları kopyalamaktır. Daha akıllı bir yöntem olan **SMOTE**, azınlık örneklerinin iki komşusu arasında yeni noktalar üretir: `x_yeni = x_i + λ (x_j − x_i)`, burada `λ` 0 ile 1 arasında rastgeledir. İmbalanced-learn kütüphanesi bu bölümde kurulu değil; bu yüzden yöntemi kendimiz yazıyoruz. Aşağıdaki modül, azınlık noktalarının k en yakın komşusunu bularak bu formülü uygular.

```python
# -*- coding: utf-8 -*-
"""Bolum 56: el yapimi SMOTE (imbalanced-learn kurulu degil)."""
import numpy as np


def smote(X, y, rng, oran=0.5, k=5):
    """Azinlik orneklerinin k en yakin komsusu arasina yeni ornek koy.
    oran: hedef (azinlik / cogunluk) orani."""
    poz = X[y == 1]
    n_neg = int((y == 0).sum())
    n_yeni = int(oran * n_neg) - len(poz)
    if n_yeni <= 0:
        return X, y
    d = ((poz[:, None, :] - poz[None, :, :]) ** 2).sum(axis=2)
    komsu = np.argsort(d, axis=1)[:, 1:k + 1]    # 0. kendisi
    i = rng.integers(0, len(poz), n_yeni)
    j = komsu[i, rng.integers(0, k, n_yeni)]
    lam = rng.random((n_yeni, 1))
    yeni = poz[i] + lam * (poz[j] - poz[i])
    return (np.vstack([X, yeni]),
            np.concatenate([y, np.ones(n_yeni, dtype=int)]))
```

Modülün test programı, üretilen yeni noktaların gerçekten iki azınlık noktasının doğrusal karışımı olup olmadığını ve azınlık kutusunun dışına çıkmadığını denetliyor. Bu, algoritmanın doğru uygulandığını gösteren basit ama önemli bir kontroldür.

```python
import numpy as np
from dengesiz import smote

rng = np.random.default_rng(56)
X = np.vstack([rng.normal(0, 1, (300, 2)),
               rng.normal(2, 0.5, (30, 2))])
y = np.r_[np.zeros(300, int), np.ones(30, int)]
Xs, ys = smote(X, y, np.random.default_rng(1), oran=0.5, k=5)
print("once: poz=%d neg=%d" % ((y == 1).sum(), (y == 0).sum()))
print("sonra: poz=%d neg=%d" % ((ys == 1).sum(), (ys == 0).sum()))

yeni = Xs[len(X):]
poz = X[y == 1]
lo, hi = poz.min(axis=0), poz.max(axis=0)
kutu = ((yeni >= lo - 1e-12) & (yeni <= hi + 1e-12)).all()
print("yeni ornekler azinlik kutusunda mi:", bool(kutu))


def dogrusal_mi(p, poz):
    """p, iki azinlik noktasinin [0,1] karisiminda mi?"""
    for a in poz:
        for b in poz:
            d = b - a
            if np.dot(d, d) == 0:
                continue
            t = np.dot(p - a, d) / np.dot(d, d)
            if 0 <= t <= 1 and np.allclose(a + t * d, p, atol=1e-9):
                return True
    return False


sayi = sum(dogrusal_mi(p, poz) for p in yeni)
print("yeni orneklerden karisim olan:", sayi, "/", len(yeni))
```

Çıktı, yeni noktaların hepsinin azınlık kutusunun içinde ve doğrusal karışım olduğunu gösteriyor.

```term
$ python b56_17_smote_test.py
once: poz=30 neg=300
sonra: poz=150 neg=300
yeni ornekler azinlik kutusunda mi: True
yeni orneklerden karisim olan: 120 / 120
```

Dengesizlikte en kritik kural, yeniden örneklemenin **yalnızca eğitim katında** yapılmasıdır. Test katına kopya ya da sentetik nokta girerse ölçüm şişer: model, test noktasına çok yakın bir eğitim kopyasını ezberlemiş olur. Bu sızıntının boyutunu Bölüm 56.14'teki tabloda göreceksin: tüm veride SMOTE uygulandığında AP 0,990'a fırlıyor; oysa yalnızca eğitim katında uygulandığında 0,890 kalıyor. Sınıf ağırlığı bu veride kazanç sağlamadı (0,885); bu, yöntemin her veride işe yaramadığının bir örneğidir.

## 56.12 Veri doğrulama ve veri sözleşmesi

Bir model eğitildikten sonra bozulduğunda, sorunun genellikle veride olduğu görülür: bir sensör yeni bir birim göndermeye başlamıştır, bir sütunun eksiklik oranı artmıştır, bir zaman damgası biçimi değişmiştir. Bu hataların ilk tespiti, modelden önce yapılmalıdır. **Veri doğrulama**, verinin beklenen yapıda olduğunu her çalıştırmada denetleyen kurallar setidir. Kurallar beş türdedir: **şema** (sütun ve tür), **aralık** (fiziksel sınırlar), **tekillik** (anahtar kopyası), **eksiklik** (en fazla oran) ve **dağılım kayması** (eğitim ile yeni verinin dağılımının karşılaştırılması).

Dağılım kayması için iki örneklemli Kolmogorov-Smirnov testini kullanıyoruz. Bu test, iki örneğin dağılımının aynı olup olmadığını sınar; p değeri düşükse dağılım değişmiş demektir. Aşağıdaki modül beş tür kuralı tek bir fonksiyonda toplar ve her kuralın sonucunu bir liste olarak döndürür.

```python
# -*- coding: utf-8 -*-
"""Bolum 56: kucuk bir veri dogrulayici (sema, aralik, benzersizlik,
eksiklik, dagilim kaymasi). Her kural bir (ad, sonuc) doner."""
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def kontrol(df, sema, aralik, benzersiz, en_fazla_eksik,
            referans=None,
            kayma_p=0.01):
    bulgular = []
    for kolon, tur in sema.items():                       # 1. sema
        ok = (kolon in df.columns
              and str(df[kolon].dtype).startswith(tur))
        bulgular.append(("sema:" + kolon, ok))
    for kolon, (lo, hi) in aralik.items():                # 2. aralik
        v = pd.to_numeric(df[kolon], errors="coerce").dropna()
        disi = int(((v < lo) | (v > hi)).sum())
        bulgular.append(("aralik:%s disi=%d" % (kolon, disi),
                         disi == 0))
    for anahtar in benzersiz:                              # 3. tekil
        d = int(df.duplicated(subset=anahtar).sum())
        bulgular.append(("tekil:%s kopya=%d" % ("+".join(anahtar), d),
                         d == 0))
    for kolon, oran in en_fazla_eksik.items():             # 4. eksik
        e = float(df[kolon].isna().mean())
        bulgular.append(("eksik:%s %.3f" % (kolon, e), e <= oran))
    if referans is not None:                               # 5. kayma
        for kolon in referans.columns:
            if kolon in df.columns and np.issubdtype(
                    df[kolon].dtype, np.number):
                a = referans[kolon].dropna()
                b = df[kolon].dropna()
                p = ks_2samp(a, b).pvalue
                bulgular.append(("kayma:%s p=%.4f" % (kolon, p),
                                 p >= kayma_p))
    return bulgular
```

Aşağıdaki program, aynı doğrulayıcıyı ham ve temizlenmiş veriye uyguluyor. Ham veride doğrulayıcı beklediğimiz sorunların hepsini yakalar. Temiz veride ise şema ve kopya kuralları geçerken eksiklik kuralı hâlâ uyarır: bu, eksikliğin temizlikle kaybolmadığını, ama doldurma ile yönetileceğini gösterir.

```python
import numpy as np
import pandas as pd
from ihadata import uret, kayit_tablosu
from temizle import temizle
from dogrula import kontrol

df, tr = uret(56)
sema = {"zaman": "object", "arac_id": "object",
        "irtifa": "float", "batarya_v": "float"}
aralik = {"irtifa": (0, 500), "batarya_v": (18, 27),
          "sicaklik_c": (-40, 120)}
benz = [["arac_id", "zaman"]]
eksik = {"batarya_v": 0.05, "sicaklik_c": 0.03}
ref = df.iloc[:20000][["irtifa", "batarya_v"]]

print("HAM veri:")
for ad, ok in kontrol(df, sema, aralik, benz, eksik, ref):
    print("  [%s] %s" % ("OK" if ok else "!!", ad))
temiz, _ = temizle(df, kayit_tablosu())
print("TEMIZ veri:")
ref_t = temiz.iloc[:20000][["irtifa", "batarya_v"]]
sema_t = dict(sema, zaman="datetime64")
for ad, ok in kontrol(temiz, sema_t, aralik, benz, eksik, ref_t):
    print("  [%s] %s" % ("OK" if ok else "!!", ad))
```

Aşağıdaki çıktı, ham ve temiz veride her kuralın sonucunu gösteriyor.

```term
$ python b56_15_dogrula.py
HAM veri:
  [OK] sema:zaman
  [OK] sema:arac_id
  [OK] sema:irtifa
  [OK] sema:batarya_v
  [!!] aralik:irtifa disi=161
  [OK] aralik:batarya_v disi=0
  [!!] aralik:sicaklik_c disi=259
  [!!] tekil:arac_id+zaman kopya=755
  [!!] eksik:batarya_v 0.084
  [!!] eksik:sicaklik_c 0.049
  [!!] kayma:irtifa p=0.0000
  [OK] kayma:batarya_v p=0.9917
TEMIZ veri:
  [OK] sema:zaman
  [OK] sema:arac_id
  [OK] sema:irtifa
  [OK] sema:batarya_v
  [!!] aralik:irtifa disi=2
  [OK] aralik:batarya_v disi=0
  [OK] aralik:sicaklik_c disi=0
  [OK] tekil:arac_id+zaman kopya=0
  [!!] eksik:batarya_v 0.084
  [!!] eksik:sicaklik_c 0.054
  [OK] kayma:irtifa p=0.5317
  [OK] kayma:batarya_v p=0.9901
```

Ham veride doğrulayıcı, 161 aralık dışı irtifa, 755 kopya satır, 259 aralık dışı sıcaklık (sentinel) ve ölçek kayması yakalar. Temiz veride birkaç sorun kalır. İki aralık dışı irtifa, uçuşun ilk üç satırında kalan GPS sıçramalarıdır; nedensel kural bu satırlarda devreye giremez (Bölüm 56.8). Bu, katmanlı doğrulamanın değerini gösterir: bir kural eksik kalırsa başka bir kural yakalar. Batarya eksikliği oranı (%8,4) ise doldurma kararıyla ele alınmalıdır.

Dağılım kaymasında da temizlik işe yarar. Ham irtifada p değeri neredeyse sıfır, yani dağılım referanstan farklı; birim karışımı tam da bu kaymayı üretir. Temiz veride p değeri 0,53'tür. Bu, sadece veri hatalarını değil, dağılım değişimini de izlemenin gerekli olduğunu gösterir; ayrıca MLOps'ta bu izlemenin nasıl yapılacağını Bölüm 77'de göreceğiz.

Veri sözleşmesi, bu kuralların bir belge gibi yazılmış hâlidir: bir veri üreticisi ile tüketicisi, hangi sütunların hangi türde, hangi aralıkta ve hangi sıklıkta olacağını önceden anlaşır. Sözleşme ihlal edildiğinde, model eğitimi başlamadan durdurulur. Veri sürümleme de aynı mantıktadır: hangi veri üzerinde hangi modelin eğitildiğini izlemek, bir sonuç tekrar üretilmek istendiğinde zorunludur (Bölüm 77).

## 56.13 Büyük veri: CSV, Parquet ve parçalı okuma

Telemetri birikince dosyalar gigabaytlara ulaşır. Bu durumda iki soru ortaya çıkar: dosyayı belleğe sığdırabilir miyiz ve okumak ne kadar sürer? Biçim seçimi bu cevabı belirler. CSV metindir; her sayı bir karakter dizisi olarak saklanır ve her okumada ayrıştırılır. Parquet ise sütun tabanlı ve ikilidir: türler dosyada tutulur, sıkıştırma sütun içinde yapılır ve yalnızca gerekli sütunlar okunabilir.

Aşağıdaki program yaklaşık bir milyon satırlık bir veri kümesini hem CSV hem Parquet olarak yazıyor, boyutlarını ve sürelerini ölçüyor. Son satırda, dosyayı `chunksize` ile parça parça okuyoruz; bu, belleğe sığmayan verinin işlenme yoludur.

```python
import os, time, tempfile
import numpy as np
import pandas as pd
import pyarrow
from ihadata import uret

df, _ = uret(56)
df = pd.concat([df] * 20, ignore_index=True)     # ~1,15 M satir
print("satir:", len(df), " pyarrow:", pyarrow.__version__)
klasor = tempfile.mkdtemp(prefix="b56_")
csv_y = os.path.join(klasor, "u.csv")
pq_y = os.path.join(klasor, "u.parquet")
t0 = time.perf_counter(); df.to_csv(csv_y, index=False)
print("CSV yazma  %.2f s  %6.1f MB" % (time.perf_counter() - t0,
      os.path.getsize(csv_y) / 1e6))
t0 = time.perf_counter(); df.to_parquet(pq_y, index=False)
print("Parquet yaz %.2f s  %6.1f MB" % (time.perf_counter() - t0,
      os.path.getsize(pq_y) / 1e6))
t0 = time.perf_counter(); pd.read_csv(csv_y)
print("CSV oku    %.2f s" % (time.perf_counter() - t0))
t0 = time.perf_counter(); pd.read_parquet(pq_y)
print("Parquet oku %.2f s" % (time.perf_counter() - t0))
toplam = 0; parca = 0
for c in pd.read_csv(csv_y, chunksize=200_000):
    toplam += len(c); parca += 1
print("chunk ile okunan satir:", toplam, " parca sayisi:", parca)
```

Aşağıdaki çıktı, CSV ve Parquet boyutlarını, yazma ve okuma sürelerini ve parça sayısını gösteriyor.

```term
$ python b56_16_buyuk.py
satir: 1028020  pyarrow: 23.0.1
CSV yazma  5.87 s   159.1 MB
Parquet yaz 0.65 s    19.4 MB
CSV oku    1.58 s
Parquet oku 0.25 s
chunk ile okunan satir: 1028020  parca sayisi: 6
```

Çıktı, dosya boyutunda belirgin bir fark gösteriyor: CSV yaklaşık 159 MB, Parquet ise yaklaşık 19 MB. Yazma ve okuma süreleri de Parquet için belirgin biçimde daha kısa. Bu sayılar makineye ve disk önbelleğine bağlıdır; bu yüzden oranı, mutlak süreden daha önemli sayın. Chunk ile okuma, bütün veriyi aynı anda tutmadan toplam satır sayısını doğru verir; istatistikleri parçalar üzerinden biriktirerek hesaplayabilirsin.

Büyük veri için pandas dışında iki yaygın araç vardır. Polars, sütun tabanlı ve çok iş parçacıklı bir DataFrame kütüphanesidir; büyük tablolarda pandas'tan genellikle hızlı çalışır (genel bilgi; bu bölümde ölçmedik). Dask ise pandas API'sini dağıtık ya da bellek dışı işlemeye taşır. Hangisinin ne zaman uygun olduğu, veri boyutuna ve altyapıya bağlıdır; ilk adım her zaman biçim ve sütun seçimidir.

## 56.14 Uçtan uca hat: aynı kirli veri, iki pipeline

Bölümün son adımında, şimdiye kadar kurduğumuz parçaları bir araya getiriyoruz. Ana soru şudur: temizlik ve öznitelik mühendisliği arıza tahmin başarısını gerçekten değiştiriyor mu, ve bunu nasıl güvenilir biçimde ölçeriz?

Model, Bölüm 54'teki değerlendirme disiplinini izler: lojistik regresyon, ölçümler AP ve ROC-AUC, dengesiz sınıf için ortalama ve standart sapma, ve çapraz doğrulama **uçuş bazlı** yapılır. Uçuş bazlı çapraz doğrulama, bir uçuşun satırlarının hem eğitimde hem testte bulunmamasını sağlar. Aksi hâlde bir uçuşun komşu satırları birlikte eğitime ve teste düşer ve model uçuşun kendisini ezberler. Bu, `StratifiedGroupKFold` ile yapılır.

Aşağıdaki program on iki senaryoyu aynı ölçütle karşılaştırıyor. Kirli veri, temizlenmemiş ham sütunlarla kurulan hattır: birimler karışık, sentinel değerler yerinde, kopyalar duruyor, hata kodu sütunu dahil. Temiz veri ise temizlik ve pencere öznitelikleriyle kurulmuş hattır. Senaryo adları, hangi değişkenin değiştirildiğini açıkça söyler.

```python
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.model_selection import (StratifiedKFold,
                                     StratifiedGroupKFold)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from ihadata import uret, kayit_tablosu
from temizle import temizle
from ozellik import ozellik_tablosu, SAYISAL
from dengesiz import smote

df, tr = uret(56)
kayit = kayit_tablosu()
temiz = ozellik_tablosu(temizle(df, kayit)[0])
ham = df.copy()
ham["irt_fark"] = 0.0

RAW_NUM = ["irtifa", "hiz", "batarya_v", "akim_a", "sicaklik_c",
           "titresim_g"]
RAW_CAT = ["gorev", "hata_kodu"]
CLEAN_CAT = ["gorev"]

def pre(num, cat, ind=True):
    return ColumnTransformer([
        ("num", make_pipeline(SimpleImputer(strategy="median",
                                            add_indicator=ind),
                              StandardScaler()), num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat)])

def boru(num, cat, cw=None, ind=True):
    return make_pipeline(pre(num, cat, ind),
                         LogisticRegression(max_iter=3000,
                                            class_weight=cw))

```

Pipeline'ı kuran ana fonksiyonlar `pre` ve `boru` içindedir. Ön işleme (medyan doldurma, eksiklik göstergesi, standartlaştırma ve tek sıcak kodlama) bir `ColumnTransformer` içinde, modelin önünde durur. Böylece çapraz doğrulamanın her katında, doldurma ve ölçekleme yalnızca o katın eğitim kısmından öğrenir. Bu, Bölüm 54'teki kuralın doğrudan uygulamasıdır: ön işleme bölmeden sonra ve Pipeline içinde yapılır.

```python
def kos(ad, X, y, g, cv, fn, mod="normal"):
    auc, ap = [], []
    for tr_i, te_i in cv.split(X, y, g):
        if mod == "normal":
            m = fn().fit(X.iloc[tr_i], y[tr_i])
            pr = m.predict_proba(X.iloc[te_i])[:, 1]
            yt = y[te_i]
        elif mod == "smote_egitim":
            p = fn()[0].fit(X.iloc[tr_i])
            Xs, ys = smote(p.transform(X.iloc[tr_i]), y[tr_i],
                           np.random.default_rng(56))
            m = LogisticRegression(max_iter=3000).fit(Xs, ys)
            pr = m.predict_proba(p.transform(X.iloc[te_i]))[:, 1]
            yt = y[te_i]
        auc.append(roc_auc_score(yt, pr))
        ap.append(average_precision_score(yt, pr))
    print("%-40s AUC %.3f+-%.3f  AP %.3f+-%.3f" % (
        ad, np.mean(auc), np.std(auc), np.mean(ap), np.std(ap)))

def tum_veride_smote(ad, X, y, cv):
    p = pre(SAYISAL, CLEAN_CAT).fit(X)
    Z = p.transform(X)
    Zs, ys = smote(Z, y, np.random.default_rng(56))
    auc, ap = [], []
    for tr_i, te_i in cv.split(Zs, ys):
        m = LogisticRegression(max_iter=3000).fit(Zs[tr_i], ys[tr_i])
        pr = m.predict_proba(Zs[te_i])[:, 1]
        auc.append(roc_auc_score(ys[te_i], pr))
        ap.append(average_precision_score(ys[te_i], pr))
    print("%-40s AUC %.3f+-%.3f  AP %.3f+-%.3f" % (
        ad, np.mean(auc), np.std(auc), np.mean(ap), np.std(ap)))

```

Programın son kısmı, senaryoları çalıştırıyor. Tüm veride SMOTE uygulayıp sonra satır bazlı bölen senaryo, sızıntıyı kasıtlı olarak gösterir.

```python
yt_ = temiz["ariza"].values
gt_ = temiz["ucus_no"].values
yh_ = ham["ariza"].values
gh_ = ham["ucus_no"].values
import warnings
warnings.filterwarnings('ignore', message='The groups')
satir = StratifiedKFold(5, shuffle=True, random_state=56)
grup = StratifiedGroupKFold(5, shuffle=True, random_state=56)

kos("R1 kirli, satir CV, hata dahil", ham, yh_, gh_, satir,
    lambda: boru(RAW_NUM, RAW_CAT))
kos("R2 kirli, grup CV, hata dahil", ham, yh_, gh_, grup,
    lambda: boru(RAW_NUM, RAW_CAT))
kos("R3 kirli, grup CV, hata haric", ham, yh_, gh_, grup,
    lambda: boru(RAW_NUM, ["gorev"]))
kos("R4 temiz, grup CV, hata dahil", temiz, yt_, gt_, grup,
    lambda: boru(SAYISAL, CLEAN_CAT + ["hata_kodu"]))
kos("R5a temiz, ham ozellik (temizlik etkisi)", temiz, yt_, gt_,
    grup, lambda: boru(RAW_NUM, ["gorev"]))
kos("R5 temiz, grup CV, hata haric", temiz, yt_, gt_, grup,
    lambda: boru(SAYISAL, CLEAN_CAT))
kos("R5b temiz, eksiklik gostergesi yok", temiz, yt_, gt_, grup,
    lambda: boru(SAYISAL, CLEAN_CAT, ind=False))
kos("R6 R5 + class_weight=balanced", temiz, yt_, gt_, grup,
    lambda: boru(SAYISAL, CLEAN_CAT, cw="balanced"))
kos("R7 R5 + SMOTE (sadece egitim)", temiz, yt_, gt_, grup,
    lambda: (pre(SAYISAL, CLEAN_CAT),), mod="smote_egitim")
kos("R9 satir CV, SMOTE sadece egitim", temiz, yt_, gt_, satir,
    lambda: (pre(SAYISAL, CLEAN_CAT),), mod="smote_egitim")
kos("R10 satir CV, orneklemesiz", temiz, yt_, gt_, satir,
    lambda: boru(SAYISAL, CLEAN_CAT))
tum_veride_smote("R8 satir CV, SMOTE TUM veride (SIZINTI)",
                 temiz[SAYISAL + CLEAN_CAT], yt_, satir)
```

Aşağıdaki çıktı, on iki senaryonun AUC ve AP değerlerini ortalama ve standart sapmalarıyla birlikte gösteriyor.

```term
$ python b56_14_pipeline.py
R1 kirli, satir CV, hata dahil           AUC 0.980+-0.001  AP 0.684+-0.024
R2 kirli, grup CV, hata dahil            AUC 0.979+-0.001  AP 0.674+-0.013
R3 kirli, grup CV, hata haric            AUC 0.977+-0.001  AP 0.629+-0.016
R4 temiz, grup CV, hata dahil            AUC 0.995+-0.002  AP 0.891+-0.031
R5a temiz, ham ozellik (temizlik etkisi) AUC 0.982+-0.003  AP 0.712+-0.026
R5 temiz, grup CV, hata haric            AUC 0.995+-0.002  AP 0.891+-0.032
R5b temiz, eksiklik gostergesi yok       AUC 0.978+-0.009  AP 0.763+-0.057
R6 R5 + class_weight=balanced            AUC 0.995+-0.002  AP 0.885+-0.029
R7 R5 + SMOTE (sadece egitim)            AUC 0.995+-0.002  AP 0.888+-0.032
R9 satir CV, SMOTE sadece egitim         AUC 0.995+-0.000  AP 0.890+-0.007
R10 satir CV, orneklemesiz               AUC 0.995+-0.000  AP 0.893+-0.006
R8 satir CV, SMOTE TUM veride (SIZINTI)  AUC 0.996+-0.000  AP 0.990+-0.001
```

Çıktı, bütün karşılaştırmayı tek bir tabloda veriyor. Tabloyu beş yönden okumanı öneririm. Birinci yön, **temizliğin etkisi**dir: aynı ham öznitelik kümesiyle (R3'ten R5a'ya) temizlik AP'yi 0,629'dan 0,712'ye çıkarıyor. İkinci yön, **öznitelik mühendisliğinin etkisi**dir: aynı temiz veriyle pencere öznitelikleri (R5a'dan R5'e) AP'yi 0,712'den 0,891'e çıkarıyor. Üçüncü yön, **eksiklik göstergesinin etkisi**dir: göstergeyi kaldırınca (R5b) AP 0,763'e düşüyor. Bu, batarya gerilimi düştüğünde sensörün boşluk vermesinin, yani MNAR yapısının, modelin en güçlü sinyallerinden biri olduğunu gösterir. Bu sinyal gerçek bir fiziksel ilişkiden de gelebilir, bir kayıt artefaktından da. Ayrımı gerçek veride ancak sensör kayıt mantığını bilerek yapabilirsin.

Dördüncü yön, **sızıntının boyutu**dur. Hata kodu bir olayın sonucudur, tahmin anında hazır değildir. Grup çapraz doğrulamasında kirli veride hata kodunu eklemek (R2 ile R3'ü karşılaştır) AP'yi 0,629'dan 0,674'e çıkarır. Kodlar yalnızca arızanın son birkaç saniyesinde göründüğü için temiz pipeline'da ek kazanç yoktur (R4 ile R5 aynı); ama bu, sızıntının zararsız olduğu anlamına gelmez, çünkü üretimde bu sütun o anda bilinmez. Satır bazlı bölmenin etkisi (R1 ile R2) küçük çıkar; bu veride uçuşlar birbirinden çok farklı olmadığı için şişme az olur. Asıl büyük sızıntı R8'de: tüm veride SMOTE uygulanıp sonra satır bazlı bölünürse AP 0,990'a fırlar, oysa yalnızca eğitim katında uygulanan R9 ve R10 yaklaşık 0,890'da kalır. Bu fark, dengesiz veride yeniden örneklemenin nerede yapıldığının önemini gösterir.

Beşinci yön, **dengeleme yöntemlerinin etkisizliği**dir. Sınıf ağırlığı (R6, AP 0,885) ve yalnızca eğitim katında SMOTE (R7, AP 0,888) temel modelin AP'sinde (0,891) belirgin bir değişiklik yaratmadı. Bu, dengesizliğin her zaman bir sorun olmadığını gösterir: model zaten pozitif sınıfı yeterince ayırabiliyorsa, yeniden örnekleme kazanç sağlamayabilir. Hangi metriğin ve hangi eşiğin uygun olduğu, Bölüm 57'de ayrıntılı olarak ele alınacak.

Bu sonuçların hepsi tek bir sentetik veri kümesine ve tek bir tohuma dayanıyor. Gerçek bir değerlendirmede, sonuçları farklı tohumlarda ve farklı kümelerde yeniden doğrulamak gerekir; standart sapma değerleri bu tekrarın bir ölçüsüdür. Burada gösterilen sayılar, metodolojik hataların ne kadar büyük fark yaratabileceğini gösteren bir ölçektir; kesin bir başarı oranı olarak okunmamalıdır.

## Çözümlü Örnekler

Her örneği Bölüm 5'teki altı adımla çözeceğiz: anla, örnekle, kaba çöz, örüntü, iyileştir, doğrula. Doğrulama adımında elle iz sürme tablosu var. Her örneğin sonunda, bu bölümün kavramlarını yeniden kurman için bir varyasyon soruyor.

### Örnek 1 (★): İki dizinin yayınlama sonucu

**Adım 1 — Anla.** `A` şekli `(2, 3, 1)` ve `B` şekli `(3, 4)` olan iki dizi var. İstenen, `A + B` işleminin sonucunun şeklidir. Sonucun değerlerine değil, şekline bakıyoruz.

**Adım 2 — Örnekle.** Eğer `B` tek bir sayı olsaydı, sonuç `A`'nın şeklinde olurdu. Burada `B`'nin şekli üç boyutlu `A`'ya sağdan hizalanınca farklılaşıyor, bu yüzden `(2, 3, 4)` gibi bir şey bekliyoruz.

**Adım 3 — Kaba çöz.** `B`'yi üç boyutlu yap: `(1, 3, 4)`. Şimdi her eksene bakıyoruz: birinci eksende `2` ile `1` var, `2` alınır. İkinci eksende `3` ile `3` var, `3` alınır. Üçüncü eksende `1` ile `4` var, `4` alınır.

**Adım 4 — Örüntü.** Kural her eksende aynıdır: eşitse o değer, biri 1 ise diğeri. Üçüncü eksendeki `1`, `B`'nin `4` değerine yayılır. Bu, `A` her satırda tek bir sayıyı `4` kez tekrar ediyormuş gibi kullanır demektir.

**Adım 5 — İyileştir.** Hesabı kafada tutmak yerine bir kontrol kuralı yazabilirsin: her eksen için iki değerin eşit ya da biri 1 olduğunu sınarsın. Böyle bir sınama, hatalı şekilleri hemen yakalar.

**Adım 6 — Doğrula.** İz tablosu:

| Eksen | A | B (sağdan hizalı) | Sonuç |
|---|---|---|---|
| 0 | 2 | 1 (eksik boyut) | 2 |
| 1 | 3 | 3 | 3 |
| 2 | 1 | 4 | 4 |

Tablo `(2, 3, 4)` veriyor. `np.broadcast_shapes((2, 3, 1), (3, 4))` çağrısı da aynı şekli döndürür; bu, elle yaptığımız hesabın doğru olduğunu gösterir.

**Bunu AI'sız yazabilir misin?** `(4, 1, 5)` ve `(3, 1)` şekillerinin yayınlama sonucunu bul. Önce hangi boyutun eksik olduğunu yaz, sonra her ekseni tek tek karşılaştır.

### Örnek 2 (★★): Araç başına özet ve SQL eşdeğeri

**Adım 1 — Anla.** Altı satırlık bir tablo var: her satır bir ölçüm, `arac` ile gruplanacak. İstenen, her araç için satır sayısı, ortalama hız, en yüksek batarya ve ortalama batarya. Üstelik bir tuzak var: `batarya` sütununda bir eksik değer var.

**Adım 2 — Örnekle.** `B` aracının üç satırı var, ama bunlardan biri batarya değeri eksik. Satır sayısı üç olmalı, batarya ortalaması ise yalnızca iki dolu değerle hesaplanmalı. Bu, `size` ile `count` arasındaki farktır.

**Adım 3 — Kaba çöz.** Her grup için sırayla sayıları toplarız. `A` için: iki satır, hız `(10 + 14) / 2 = 12`, batarya en büyüğü `24,5`, batarya ortalaması `(24,5 + 24,1) / 2 = 24,3`. `B` için iki dolu batarya değeri var, bu yüzden ortalama `(24,8 + 24,6) / 2 = 24,7`.

**Adım 4 — Örüntü.** Her grubu üç adımda işliyoruz: bölmek, işlem uygulamak, birleştirmek. SQL'deki `GROUP BY` bu üç adımın tek bir ifadeye sıkıştırılmış hâlidir. Eksik değerler `COUNT(sütun)` ve `AVG` tarafından atlanır, `COUNT(*)` ise hepsini sayar.

**Adım 5 — İyileştir.** Aynı sorguyu pandas'ta yazabilirsin. Bunu adlandırılmış toplamalarla yaparsan, her sütun için açık bir isim ve açık bir işlem olur.

```python
ozet = t.groupby("arac").agg(
    satir=("hiz", "size"),
    batarya_say=("batarya", "count"),
    hiz_ort=("hiz", "mean"),
    bat_maks=("batarya", "max"))
```

**Adım 6 — Doğrula.** İz tablosu:

| Araç | satir (size) | batarya_say (count) | hiz_ort | bat_maks |
|---|---|---|---|---|
| A | 2 | 2 | 12,0 | 24,5 |
| B | 3 | 2 | 10,0 | 24,8 |
| C | 1 | 1 | 9,0 | 24,0 |

Tablo, pandas'ın `size` ve `count` sonuçlarıyla birebir tutar. `B` için satır sayısı 3, batarya sayısı ise 2'dir; bu fark, eksik değerin etkisidir.

**Bunu AI'sız yazabilir misin?** Aynı tabloda her araç için hız değerinin en büyüğünü ve batarya değerlerinin ortalamasını hesapla. Sonra `COUNT(*)` ile `COUNT(batarya)` farkının hangi satırda ortaya çıktığını göster.

### Örnek 3 (★★): Birleştirmede anahtar çoğalması

**Adım 1 — Anla.** İki tablo var. Sol tablo her uçuş için araç kimliği taşıyor: `(1, A)`, `(2, A)`, `(3, B)`, `(4, C)`. Sağ tablo her araç için yazılım sürümlerini taşıyor: `(A, v1)`, `(A, v2)`, `(A, v3)`, `(B, v1)`. Birleşimin satır sayısını üç türde bulmak istiyoruz.

**Adım 2 — Örnekle.** Sol tabloda `A` iki kez, sağ tabloda üç kez geçiyor. Eğer her sol `A` satırı, her sağ `A` satırıyla eşleşirse, sonuçta `A` için kaç satır olmalı? Bir sezgi: iki ile üçün çarpımı, yani altı.

**Adım 3 — Kaba çöz.** Her anahtar için eşleşen satır sayısını çarpıyoruz. `A`: sol 2 × sağ 3 = 6 satır. `B`: 1 × 1 = 1 satır. `C`: sol 1, sağda yok, bu yüzden `inner` için 0 satır, `left` için ise 1 satır (sağ sütunlar `NaN`).

**Adım 4 — Örüntü.** Çarpım, anahtar çoğalmasının kaynağıdır. Bir anahtar iki tabloda da tekrarlanıyorsa satırlar çarpılır. Bu yüzden birleşim satır sayısını sol tablodan daha fazla büyütebilir.

**Adım 5 — İyileştir.** Birleşimden önce anahtarın tekil olup olmadığını denetlemek daha iyidir. Sağ tablo kayıt tablosu gibi bir "bir-çok" ilişki bekliyorsa `validate="many_to_one"` yazarsın; bu bizim araç kayıt tablosunda kullandığımız kuraldır.

**Adım 6 — Doğrula.** İz tablosu:

| Anahtar | Sol satır | Sağ satır | inner | left | outer |
|---|---|---|---|---|---|
| A | 2 | 3 | 6 | 6 | 6 |
| B | 1 | 1 | 1 | 1 | 1 |
| C | 1 | 0 | 0 | 1 | 1 |
| Toplam | | | 7 | 8 | 8 |

Toplamlar, `b56_06_groupby_merge` programının çıktısıyla aynıdır: `inner` 7, `left` 8, `outer` 8.

**Bunu AI'sız yazabilir misin?** Sol tabloda `K` anahtarı üç kez, sağ tabloda iki kez geçiyor; ayrıca `M` anahtarı sol tabloda bir, sağda dört kez geçiyor. `inner` birleşim kaç satır üretir? Sonra sağ tabloya bir `K` satırı daha eklersen `inner` sonucu nasıl değişir?

### Örnek 4 (★★★): Zaman serisinde sızıntısız geçmiş pencere

**Adım 1 — Anla.** Altı ölçümlük bir sıcaklık serisi var: `s = [10, 12, 11, 15, 30, 14]`. Her `t` için, yalnızca geçmiş üç ölçümün ortalamasını veren bir özniteliği tanımlamak istiyoruz. Ayrıca bu özniteliğin gelecek değerlerden etkilenmediğini kanıtlamamız gerekiyor.

**Adım 2 — Örnekle.** `t = 4` için (`s₄ = 30`) geçmiş pencere `s₁, s₂, s₃` olmalı. Bu değerlerin ortalaması `(12 + 11 + 15) / 3 = 12,667`. Buna karşılık `s₅` (sonraki değer, `14`) bu özniteliğe hiç girmemeli.

**Adım 3 — Kaba çöz.** `shift(1)` her değeri bir satır aşağı kaydırır: böylece `t` satırına `s_{t−1}` gelir. Sonra `rolling(3)` son üç değeri ortalar. Kaydırma, mevcut değeri pencereden dışarı atar; bu yüzden gelecek değer hiçbir zaman görülmez.

**Adım 4 — Örüntü.** Sızıntının yolu, pencerenin "merkezlenmesi"dir. Merkezi pencere `t` anını ortalar ve `t + 1` değerini de kullanır. Bunu `c_t = (s_{t−1} + s_t + s_{t+1}) / 3` ile görebilirsin. Bu özniteliği bir model eğitiminde kullanan biri, bir sonraki ölçümü zaten bilir.

**Adım 5 — İyileştir.** Doğruluğu test etmek için bir pertürbasyon deneyi kur. `s₅`'i `100` yap ve her özniteliğin değişip değişmediğine bak. Geçmiş pencere değişmemeli; merkezi pencere değişmeli. Bu, sızıntının testidir.

**Adım 6 — Doğrula.** İz tablosu (`s₅` iki kez: orijinal `14`, sonra `100`):

| t | s_t | geçmiş f_t | merkez c_t | c_t (s₅=100) | f_t (s₅=100) |
|---|---|---|---|---|---|
| 0 | 10 | — | 11,000 | 11,000 | — |
| 1 | 12 | 10,000 | 11,000 | 11,000 | 10,000 |
| 2 | 11 | 11,000 | 12,667 | 12,667 | 11,000 |
| 3 | 15 | 11,000 | 18,667 | 18,667 | 11,000 |
| 4 | 30 | 12,667 | 19,667 | 48,333 | 12,667 |
| 5 | 14 | 18,667 | 22,000 | 65,000 | 18,667 |

Tablo, geçmiş pencere özniteliğinin `s₅` değişiminden etkilenmediğini (`t = 4`'te 12,667 kalıyor) ve merkezi pencerenin `t = 4` için 19,667'den 48,333'e sıçradığını gösteriyor. Aynı ilkeyi gerçek sentetik veride `b56_13_sizinti` programındaki 40 denemeyle doğruladık; orada da geçmiş pencere hiçbir denemede değişmedi, merkezi pencere ise her denemede değişti.

**Bunu AI'sız yazabilir misin?** Geçmiş iki değeri kullanan bir özniteliği (`shift(1)` ve `rolling(2)`) yaz, aynı serinin `s₅`'ini `100` yap ve hangi `t` değerlerinde özniteliğin değiştiğini gösteren bir tablo çıkar.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı kullanma. Kodu, testleri ve ölçümleri kendin yaz. Amaç, bu bölümdeki kavramları bir mülakatta ya da boş bir IDE'de yeniden kurabilmektir. Bir hata bulursan, önce hatayı kendin çöz; bu, bu bölümün en değerli kısmıdır.
:::

### Proje 1 (★★): Mini veri doğrulayıcı kütüphanesi

**Amaç.** Bu bölümdeki `dogrula.py` modülünü bir kütüphane düzeyine getirmek: kurallar tanımlanabilir, her kural ayrı test edilebilir ve sonuç bir rapor olarak dışa aktarılabilir olsun.

**Yapılacak / Beklenen davranış.** Beş tür kuralı (şema, aralık, tekillik, eksiklik, dağılım kayması) destekleyen bir sınıf yaz. Her kural bir ad, bir sonuç ve bir ayrıntı döndürsün. Bir CSV dosyasını girdi alıp tüm kuralları çalıştıran bir komut satırı arabirimi ekle. Her kuralın kendi birim testi olsun: sahte bir tabloda kuralın hem geçtiği hem kaldığı durumu gösteren testler.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Kuralları bir liste içinde nesne olarak tut; her nesne `uygula(df)` yöntemi taşısın. Dağılım kaymasında `scipy.stats.ks_2samp` kullanabilirsin. Test için ilk önce tek satırlık bir tablo ile her kuralın uç durumunu (boş tablo, tüm değerler `NaN`) dene.

**Başarı kriterleri.** (1) En az beş kural türü, her biri en az iki birim testiyle kapsanmış. (2) Bu bölümdeki ham veriye uygulandığında, `ihadata` ile üretilen 755 kopyayı ve 161 aralık dışı irtifayı yakalıyor. (3) Temiz veriye uygulandığında kopya ve aralık kuralları geçiyor. (4) Hatalı bir sütun adı verildiğinde kütüphane çökmek yerine açık bir hata raporu döndürüyor.

### Proje 2 (★★★): Batarya telemetrisi için uçtan uca veri hattı

**Amaç.** Bir elektrikli araç batarya telemetrisi (EV Dashboard tarzı, sentetik) için içe alma, doğrulama, temizleme, öznitelik üretimi, modelleme ve raporlamayı tek bir hat olarak kurmak. Amaç, hattın her adımının Bölüm 56'daki kurallara uyduğunu ölçmektir.

**Yapılacak / Beklenen davranış.** Zaman damgalı, gerilim, akım, sıcaklık ve hücre dengesizliği içeren bir sentetik veri üret (sabit tohumla). Verinin bir kısmını bilerek kirlet: birim karışımı, eksik değerler, kopyalar ve bir sensör kayması. Ardından: (a) doğrulama, (b) temizleme, (c) yalnızca geçmişe bakan pencere öznitelikleri, (d) bir Pipeline içinde ön işleme ve model, (e) grup çapraz doğrulaması ile AP ve AUC, (f) kısa bir rapor dosyası üret.

**Önerilen yaklaşım (ipucu).** Bölüm 56.14'teki `pre` ve `boru` fonksiyonlarının yapısını taklit et. Her veri dönüşümünü Pipeline'a koy; doldurma ve ölçeklemeyi yalnızca eğitim katında öğrenmesini sağla. Bir "sızıntı kontrolü" yaz: aynı hattı tüm veride uygulayan ve grup yerine satır bazlı bölen bir sürüm kur; iki sürümün AP farkını raporla.

**Başarı kriterleri.** (1) Sentetik kirliliklerin her biri, temizleme adımında sayısal olarak yakalanmış ve doğrulanmış. (2) Pencere öznitelikleri, gelecek değer değişikliğine karşı duyarsızlık testinden geçiyor. (3) Tüm veride ön işleme yapan sürüm ile Pipeline sürümü arasındaki AP farkı raporda ve nedeniyle birlikte yazılmış. (4) Sonuçlar üç farklı tohumda tekrarlanmış ve standart sapmaları raporlanmış.

### Ek Alıştırmalar

Aşağıdaki problemler cevapsızdır. Her birini önce kendin çöz, sonra kontrol etmek için bu bölümdeki kodları kullan.

1. (★) Bir `(5, 3)` matrisinin her satırının ortalamasını yayınlama ile çıkar. Ortalamanın şeklini ve neden `keepdims=True` gerektiğini yaz.
2. (★) `a = np.arange(10)` ve `b = a[2:5]` için `b[0] = -1` yaptığında `a`'nın durumu nedir? Nedenini bellek adımlarıyla açıkla.
3. (★) `np.broadcast_shapes((3, 1), (2,))` ne döner? Önce elle hesapla, sonra doğrula.
4. (★) `float32` ile on milyon kez `0.1` toplamanın sonucunu `np.sum` ve sıralı döngüyle tahmin et; sonra ölç.
5. (★★) Mülakat: Bir sütun ortalamasını (n,) ve (n,1) karışıklığıyla çıkarmak neden sessiz bir hatadır? Hangi kontrolle yakalarsın?
6. (★★) Bir sensör akışında eksik değerleri ortalama yerine medyanla doldurmak varyansı nasıl etkiler? Bunu ölçmek için bir deney tasarla.
7. (★★) Mülakat: MNAR durumunda "eksik satırları sil" yaklaşımı neden yanıltıcıdır? Somut bir sensör örneği ver.
8. (★★) Hedef kodlamada out-of-fold yapmadığında AUC'nin neden şiştiğini, kendi küçük bir veri kümende göster.
9. (★★) Mülakat: `shift(-1)` ile üretilmiş bir zaman serisi özniteliği neden sızıntılıdır? Tek bir cümleyle açıkla.
10. (★★★) Mülakat: Filtre ve sarmalayıcı öznitelik seçimi arasındaki farkı, iki özniteliğin birlikte anlam kazandığı bir örnekle açıkla.
11. (★★★) SMOTE'un yüksek boyutlu verilerde neden zorlandığını, k komşuluk ve uzaklık ölçüsü açısından tartış.
12. (★★★) Mülakat: Bir modelin AP değeri alışılmadık derecede yüksek çıktığında, önce hangi üç veri hatasını kontrol edersin?

## Kod Okuma Egzersizi

Bu bölümde NumPy'ın yayınlama kurallarını uygulayan gerçek kodu okuyacağız. Kaynak, yerel olarak kurulu NumPy 2.3.5 sürümünün `numpy/lib/_stride_tricks_impl.py` dosyasının `_broadcast_shape` fonksiyonudur (satır 413 ile 430 arası; `_broadcast_shape` fonksiyonu ve yardımcı `_size0_dtype` tanımı). Kod, site-packages dizininden birebir kopyalandı. Bir docstring satırı ile iki yorum satırı, 70 karakter sınırına sığsın diye iki satıra bölündü; hiçbir kod satırı değiştirilmedi. Fonksiyonun, `np.broadcast` nesnesini kullanarak bir dizi şekil listesinin ortak şeklini nasıl hesapladığına dikkat et.

```python
def _broadcast_shape(*args):
    """Returns the shape of the arrays that would result from
    broadcasting the supplied arrays against each other.
    """
    # use the old-iterator because np.nditer does not handle
    # size 0 arrays consistently
    b = np.broadcast(*args[:32])
    # unfortunately, it cannot handle 32 or more arguments directly
    for pos in range(32, len(args), 31):
        # ironically, np.broadcast does not properly handle
        # np.broadcast objects (it treats them as scalars)
        # use broadcasting to avoid allocating the full array
        b = broadcast_to(0, b.shape)
        b = np.broadcast(b, *args[pos:(pos + 31)])
    return b.shape


_size0_dtype = np.dtype([])

```

Bu fonksiyon, yayınlamanın kurallarını bizim `yayin_sekli` fonksiyonumuzla aynı biçimde değil, NumPy'ın kendi `np.broadcast` nesnesiyle yapar. Çoğu zaman bu iki yol aynı sonucu verir; ama kaynak kodun yorumları, bu yolun bazı sınırlarını da açıkça belirtir.

**Sorular — cevaplamadan geçme:**

1. `np.broadcast(*args[:32])` ile başlamanın nedeni nedir? Yorumdaki sınırlamayı kendi cümlelerinle açıkla.
2. `broadcast_to(0, b.shape)` çağrısı, ara sonucu bellekte gerçekten ayırmadan nasıl çalışır? Bölüm 56.3'teki adım sıfır fikriyle ilişkisini kur.
3. Döngüdeki adım neden 31 ve başlangıç neden 32? Bu sayılar hangi sınırdan gelir?
4. `broadcast_shapes` neden yalnızca şekilleri alıp boş diziler (`np.empty`) oluşturuyor? Büyük bir şekil için bu yaklaşımın bellek maliyeti nedir?
5. `_size0_dtype = np.dtype([])` satırı neden gerekli? Boyutu sıfır olan dizilerle ilgili yorumdaki uyarıyı kendi sözlerinle açıkla.
6. Yorumdaki "ironically" ifadesi neyi kastediyor? Bu kodun, bir kütüphane sınırlamasının etrafından nasıl dolandığını açıkla.

## Bölüm Özeti

- **NumPy dizisi**, bir başlık (dtype, shape, strides) ve bir bellek bloğudur. Dilim ve yeniden şekillendirme çoğu zaman görünüm üretir; gelişmiş indeks ve boolean maske kopya üretir. Görünüm üzerinde yerinde değişiklik orijinali bozar.
- **Vektörleştirme**, Python döngüsünü NumPy'ın C döngüsüyle değiştirir. Kazanç, önbellek ve SIMD sınırlarına bağlı olarak dizi boyutuna göre değişir; ölçmeden hız iddia etme.
- **Yayınlama**, şekilleri sağdan hizalar ve 1 boyutlarını yayar. `(5,)` ile `(5, 1)` çıkarması sessizce `(5, 5)` üretir; `keepdims=True` bu tuzağı önler.
- **pandas**, indeksleri hizalar. `loc` ile `iloc` farklıdır; zincirli atama bir uyarı verir ve hiçbir şey yapmayabilir. `groupby` SQL'deki `GROUP BY`, `merge` ise `JOIN`dir; anahtar çoğalması satır sayısını çarpar, `validate` bunu yakalar.
- **Keşifsel analiz ve temizlik**, birim karışımı, kopya, sentinel değer ve Türkçe büyük/küçük harf tuzağı gibi sorunları sayısal olarak ortaya çıkarır. Aykırı değer, hata mı yoksa gerçek olay mı olduğu sorulmadan silinmez; maskeleme etkisi z-skorlarında görülür.
- **Eksik veri**, MCAR, MAR ve MNAR mekanizmalarına göre ele alınır. Ortalama doldurma varyansı `√(1 − p)` oranında daraltır; eksiklik göstergesi MNAR'da bilgi taşır.
- **Öznitelik mühendisliği**, ölçeklemeyi (uzaklık tabanlı modeller için), döngüsel kodlamayı, hedef kodlamanın out-of-fold yapılmasını ve yalnızca geçmişe bakan pencereleri gerektirir. Sızıntı testi bunu doğrulamanın yoludur.
- **Dengesiz veri**da sınıf ağırlığı ve SMOTE'un yalnızca eğitim katında uygulanması zorunludur. Tüm veride yapılan SMOTE, bu veride AP'yi 0,890'dan 0,990'a şişirdi.
- **Doğrulama ve büyük veri**, şema, aralık, tekillik, eksiklik ve dağılım kaymasını her çalıştırmada denetler. Parquet, CSV'ye göre hem boyut hem okuma süresinde belirgin avantaj sağlar.

**Sonraki bölümde:** Bölüm 57, Değerlendirme ve Deney Tasarımı, bu bölümde kullandığımız AP ve AUC ölçütlerini derinlemesine ele alacak. Dengesiz veride metriğin ve eşiğin nasıl seçileceği, ROC ve PR eğrileri, kalibrasyon, çapraz doğrulamanın ayrıntıları ve istatistiksel anlamlılık orada işlenecek. Bu bölümde gördüğümüz 0,890 ile 0,990 arasındaki fark, deney tasarımının neden ayrı bir konu olduğunu gösteriyor.

::: mulakat
1. Bir NumPy dizisinin bir dilimi neden çoğu zaman yeni bir bellek bloğu ayırmaz? Görünüm ile kopya arasındaki farkı adım (stride) kavramıyla açıkla.
2. `(n,)` ve `(n, 1)` şekilli iki dizi çıkarıldığında sonuç neden sessizce `(n, n)` olur? Bu hatayı üretimde nasıl yakalarsın?
3. Birleştirme (merge) sonucunda satır sayısı neden giriş tablolarından büyük olabilir? Hangi parametre bu durumu önceden yakalar?
4. Bir sensör verisinde eksik değerler yalnızca düşük batarya gerilimlerinde oluşuyorsa, bu eksikliği nasıl ele alırsın? MCAR, MAR ve MNAR ayrımı burada neden önemlidir?
5. Hedef kodlamayı tüm veriden hesaplayıp sonra çapraz doğrulama yaparsan hangi sızıntı oluşur? Out-of-fold yöntem bunu nasıl önler?
6. Zaman serisinde bir özniteliğin yalnızca geçmişe baktığını nasıl kanıtlarsın? Bu kanıtın testi neden bir pertürbasyon deneyi olmalıdır?
7. Dengesiz veride SMOTE'u tüm veriye uygulayıp sonra bölmek neden tehlikelidir? Test kümesindeki sentetik noktaların modeli nasıl şişirdiğini açıkla.
8. Dağılım kaymasını izlemek için iki örneklemli Kolmogorov-Smirnov testi ne ölçer, ne ölçmez? Testin p değeri küçük çıktığında hangi adımları atarsın?
