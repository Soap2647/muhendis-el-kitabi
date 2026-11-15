%% kisim_no: XII
%% kisim_ad: Matematik
%% bolum_no: 48
%% baslik: Lineer Cebir

## Giriş: Sayıları ok gibi düşünmek

Bir İHA'nın uçuş bilgisayarı her döngüde ivmeölçer ve jiroskoptan gelen değerleri okur. Bu değerler gövdenin kendi çerçevesindedir: "önüme doğru" ve "sağıma doğru" demek gövdeye göre anlam taşır. Kontrol algoritması ise dünya çerçevesinde konuşur: kuzey, doğu, yukarı. Aradaki çeviriyi her döngüde yapmak gerekir ve bu çeviri bir matris çarpımıdır. Aynı İHA'da bir Kalman filtresi (Bölüm 62) konum tahmini yaparken yine matris işlemleri kullanır. Uçuş yazılımının saniyede yüzlerce kez yaptığı iş, büyük ölçüde lineer cebirdir.

Makine öğrenmesinde durum daha da açık. Bir sinir ağının bir katmanı, girdi vektörünü bir ağırlık matrisiyle çarpar, bir sabit ekler ve sonra doğrusal olmayan bir fonksiyon uygular. Bölüm 63'te göreceğin MLP tam olarak budur. Bölüm 69'daki dikkat mekanizması `QKᵀ` gibi bir matris çarpımıyla başlar. Bölüm 70'te bir kelimeyi temsil eden vektör, bir kosinüs benzerliğiyle karşılaştırılır. Yani bu kitabın ML kısmını okumak, lineer cebirin dilini okumaktır.

Lineer cebirin üç ana fikri var ve bu bölümün tamamı bunların etrafında döner. Birincisi **vektör**: bir nesneyi sayılar listesi olarak tutmak ve bu listeler üzerinde toplama, ölçekleme, uzaklık ve açı hesaplamak. İkincisi **doğrusal dönüşüm**: bir matrisin uzayı nasıl büküp döndürdüğü. Üçüncüsü **ayrışım**: bir matrisi, anlaşılması kolay parçalara bölmek. Özdeğer ve tekil değer ayrışımı (SVD) bu üçüncü fikrin en önemli örnekleridir.

Bu bölümde her kavramı dört adımla vereceğiz. Önce **geometrik bir resim** çizeceğiz; çünkü matrisi bir tablo olarak değil, bir hareket olarak görmek gerekir. Sonra **elle küçük bir örnek** hesaplayacağız. Üçüncü adımda bu sonucu **NumPy ile doğrulayacağız**. Son olarak her kavramın bir **mühendislik ya da ML uygulamasına** nasıl bağlandığını göstereceğiz. Tek başına ezber formül işe yaramaz; sezgi ile hesabın birlikte gelmesi gerekir.

Bölüm 3'te, Python listesinin her elemanı ayrı bir nesne olduğu için bir milyon sayılık aritmetiğin yavaş olduğunu görmüştük. NumPy'nin var olma sebebi, sayıları bitişik bir bellek bloğunda tutup bu bloğu C ve Fortran'da yazılmış kütüphanelere vermektir. Bu bölümün sonunda bu farkı ölçecek ve bu kütüphanelerin altında neyin çalıştığına bakacağız.

::: not
Bu bölümdeki bütün programlar Python 3.12.10 ve NumPy 2.3.5 ile çalıştırıldı. Rastgele sayılar `default_rng(42)` tohumuyla üretildi, bu yüzden sonuçlar sizde birebir aynı çıkar. Hız ölçümleri makineye bağlıdır: metindeki süreler bizim bilgisayarımızdan geldi; sen farklı süreler göreceksin. Ama yapısal sonuçlar, yani hangi yöntemin hızlı, hangisinin kararsız olduğu, her makinede aynıdır. NumPy yoksa `python -m pip install numpy` ile kur.
:::

## 48.1 Vektör: hem ok hem de liste

Bir vektör, sıralı bir sayı listesidir. Ama aynı listeye iki farklı gözle bakabiliriz. **Geometrik** bakışta vektör, başlangıç noktası orijin olan bir oktur: `(3, 4)` koordinat düzleminde orijinden `(3, 4)` noktasına giden oktur. **Sayısal** bakışta ise vektör bir kayıttır: bir uçağın anlık durumu `(hız, irtifa, yönelim, batarya)` dört sayıdan oluşan bir vektördür ve bu dört boyutlu bir uzayda bir noktadır.

ML'de ikinci bakış baskındır. Bir fotoğrafın 28×28 piksel değeri 784 boyutlu bir vektördür. Bir kelimenin 300 boyutlu gömmesi (Bölüm 70) 300 boyutlu bir vektördür. Bu vektörler çoğu zaman görünmezdir ama her zaman oradadır. Geometrik düşünmek, bu 784 ya da 300 boyutlu uzayda "iki örnek birbirine yakın mı?" sorusunu sormanın yoludur.

İki temel işlem vardır. **Toplama** bileşen bileşen yapılır: `(1, 2) + (3, 4) = (4, 6)`. Bu, okların uç uca eklenmesidir. **Ölçekleme** her bileşeni aynı sayıyla çarpar: `2 · (3, 4) = (6, 8)`; ok aynı yönde, iki kat uzunlukta kalır. Bu iki işlem birlikte **doğrusal kombinasyon** adını alır: `a·u + b·v`. Bölüm 48.9'da bu kombinasyonların hangi vektörleri üretebildiğini inceleyeceğiz.

Python'da küçük bir tuzak var. Liste üzerinde `+` işleci birleştirme yapar: `[1, 2] + [3, 4]` sonucu `[1, 2, 3, 4]` olur, yani bir dört elemanlı listedir. Vektör toplamı ise `np.array([1, 2]) + np.array([3, 4])` ile `[4, 6]` verir. Bu farkı akılda tut: liste bir kap, vektör bir matematiksel nesnedir. Bu bölümdeki tüm vektörler NumPy dizisidir.

## 48.2 Nokta çarpım, izdüşüm ve kosinüs benzerliği

İki vektörün **nokta çarpımı** (dot product), bileşen çarpımlarının toplamıdır:

u · v = u₁v₁ + u₂v₂ + ... + uₙvₙ = Σ uᵢvᵢ

Bu tanımın geometrik anlamı çok daha önemlidir. Nokta çarpım, iki vektörün uzunluklarının ve aralarındaki açının kosinüsünün çarpımına eşittir:

u · v = ‖u‖ ‖v‖ cos θ

Burada ‖u‖, u'nun uzunluğunu (normunu) gösterir ve bir sonraki bölümde ayrıntısıyla ele alınacaktır. θ, iki ok arasındaki açıdır. Bu eşitlikten üç sonuç çıkar. Nokta çarpım pozitifse açı dar, yani vektörler aynı yöne bakıyordur. Sıfırsa vektörler diktir. Negatifse açı geniştir ve vektörler birbirine ters bakıyordur.

Nokta çarpımın bir diğer yorumu **izdüşümdür**. `a` vektörünün `b` doğrultusundaki izdüşümü, `a`'nın `b`'ye dik indirilen gölgesidir:

proj_b(a) = (a · b / b · b) b

Bu formülde `a · b / b · b` kısmı, gölgenin `b`'nin kaç katı olduğunu söyler. Şekil 48.1 (a) bu gölgeyi gösterir. Vektör `a` bir ışık kaynağından `b` doğrultusuna düşürülen bir cisim gibi düşünülebilir; gölgesinin uzunluğu, `a`'nın `b` yönündeki bileşenidir.

![Şekil 48.1: (a) a vektörünün b üzerindeki izdüşümü ve a · b. (b)-(d) Üç normun birim kümesi: L1 elmas, L2 çember, L∞ kare (Bölüm 48.3).](gorseller/b48_nokta_norm.png)

Elle küçük bir örnek yapalım. `u = (3, 4)` ve `v = (4, -3)` vektörlerinin nokta çarpımı `3·4 + 4·(-3) = 12 - 12 = 0` çıkar. Bu iki vektör diktir. `u`'nun `e₁ = (1, 0)` doğrultusundaki izdüşümü `(u·e₁ / e₁·e₁) e₁ = (3/1)(1, 0) = (3, 0)` olur; yani gölge, `u`'nun yatay bileşenidir. Aşağıdaki programda bu hesapları ve bir kosinüs benzerliği örneğini NumPy ile doğruluyoruz.

Kosinüs benzerliği, nokta çarpımı uzunluklara bölerek elde edilen ölçüdür:

cos(u, v) = (u · v) / (‖u‖ ‖v‖)

Bu ölçü vektörlerin uzunluğundan bağımsızdır. Bir belgenin kelime sayım vektörü iki katına çıksa, yani aynı içerik iki kez yazılmış olsa, kosinüs benzerliği değişmez. Bu özellik, Bölüm 70'te göreceğin gömme (embedding) tabanlı arama sistemlerinin temelidir: iki metnin anlamca yakınlığını uzunluktan bağımsız ölçmek istersin. Dikkat: kosinüs benzerliği yalnızca yönü ölçer. Kelime sayımı gibi ham vektörlerde iki belge yalnızca ortak kelimeleri paylaştığı için yüksek skor alabilir; anlam her zaman yakalanmaz (genel bilgi).

Aşağıdaki program nokta çarpımı, izdüşümü ve kosinüs benzerliğini hem elle yapılan değerlerle hem NumPy ile hesaplar.

```python
# vek.py: vektor, nokta carpim, norm, kosinus benzerligi, izdusum
import numpy as np

u = np.array([3.0, 4.0])
v = np.array([4.0, -3.0])

print("u + v   =", u + v)
print("2 * u   =", 2 * u)
print("u . v   =", u @ v)
print("|u|_2   =", np.linalg.norm(u))
print("|u|_1   =", np.linalg.norm(u, 1))
print("|u|_inf =", np.linalg.norm(u, np.inf))


def kosinus(a, b):
    return (a @ b) / (np.linalg.norm(a) * np.linalg.norm(b))


def izdusum(a, b):
    # a vektorunun b dogrultusundaki izdusumu
    return (a @ b) / (b @ b) * b


e1 = np.array([1.0, 0.0])
print("izdusum(u, e1)  =", izdusum(u, e1))
print("kosinus(u, v)   =", round(kosinus(u, v), 6))

# belge benzerligi: kelime sayim vektorleri
a = np.array([2.0, 1.0, 0.0, 3.0])
b = 2 * a                       # ayni icerik, iki kat uzunluk
c = np.array([1.0, 0.0, 0.0, 0.0])
print("kosinus(a, 2a)  =", round(kosinus(a, b), 6))
print("kosinus(a, c)   =", round(kosinus(a, c), 6))
```

```term
$ python vek.py
u + v   = [7. 1.]
2 * u   = [6. 8.]
u . v   = 0.0
|u|_2   = 5.0
|u|_1   = 7.0
|u|_inf = 4.0
izdusum(u, e1)  = [3. 0.]
kosinus(u, v)   = 0.0
kosinus(a, 2a)  = 1.0
kosinus(a, c)   = 0.534522
```

Çıktıdaki `kosinus(a, 2a) = 1.0` satırı önemlidir: `b = 2a` aynı yönde, iki kat uzunlukta olduğu için açı sıfırdır ve kosinüs 1'dir. `kosinus(a, c) = 0.534522` değeri ise `a · c = 2`, `‖a‖ = √14`, `‖c‖ = 1` olduğu için `2/√14` olarak elle de doğrulanabilir.

## 48.3 Normlar: uzaklığın farklı tanımları

Bir vektörün **normu**, o vektörün "boyutunu" ölçen bir sayıdır. Normun tanımı tek değildir; üç tanesi ML'de sürekli karşına çıkar.

**L2 normu** (Öklid normu), bildiğin uzunluktur: ‖x‖₂ = √(Σ xᵢ²). `(3, 4)` için `√(9 + 16) = 5` olur. Bu, Pisagor teoreminin doğrudan uygulamasıdır.

**L1 normu** (Manhattan normu), mutlak değerlerin toplamıdır: ‖x‖₁ = Σ |xᵢ|. `(3, 4)` için `3 + 4 = 7` olur. Bu norm, şehir bloklarında yürümenin uzunluğuna benzer: çapraz gidemezsin, yalnızca sokak boyunca yürürsün.

**L∞ normu** (maksimum normu), en büyük mutlak bileşendir: ‖x‖∞ = max |xᵢ|. `(3, 4)` için `4` olur. Bu norm, en kötü durumda sapmayı ölçer: vektörün en çok bozulmuş bileşeni ne kadar?

Her normun **birim kümesi** (‖x‖ = 1 koşulunu sağlayan noktalar) farklı bir şekil verir. Şekil 48.1 (b), (c) ve (d) bunları gösterir: L1 birim kümesi bir elmas, L2 bir çember, L∞ bir karedir. Bu şekiller, bir normu seçmenin ne anlama geldiğini gösterir. L1 birim kümesinin köşeleri eksenlerin üzerindedir. Bu yüzden L1 ile bir şeyi cezalandırmak, çözümü sıfır bileşenlere itme eğilimindedir. Bu özellik Bölüm 58'de L1 düzenlileştirmesinin (lasso) seyrek çözümler üretmesinin sebebidir.

Normlar ML'de doğrudan hata ölçüsü olarak kullanılır. Ortalama mutlak hata (MAE) bir L1 ortalamasıdır, kök ortalama kare hata (RMSE) bir L2 ortalamasıdır. L∞ ise bir tahminde en büyük tek sapmayı verir ve güvenlik açısından önemli olabilir: bir sensörün hiçbir zaman belirli bir sınırı aşmaması gerekiyorsa L∞ doğru ölçüdür. Bu ölçüler arasında şu eşitsizlikler vardır (genel bilgi, kolayca kanıtlanır): ‖x‖∞ ≤ ‖x‖₂ ≤ ‖x‖₁.

Matrisler için de benzer bir norm tanımlanır. **Frobenius normu** matrisin tüm elemanlarının karelerinin toplamının karekökü, yani matrisi uzun bir vektör gibi görmektir: ‖A‖_F = √(Σ aᵢⱼ²). Bu normu SVD bölümünde (Bölüm 48.13) sıkıştırma hatasını ölçmek için kullanacağız. Yukarıdaki `vek.py` programı vektör normlarını hesapladı; `u = (3, 4)` için ‖u‖₁ = 7, ‖u‖₂ = 5, ‖u‖∞ = 4 değerlerini verdi.

## 48.4 Matris bir dönüşümdür

Bir matrisi tablo olarak görmek yaygın bir alışkanlıktır, ama lineer cebirde asıl anlamı başkadır: **matris, uzaya uygulanan bir dönüşümdür**. `m × n` boyutlu bir `A` matrisi, `n` boyutlu bir `x` vektörünü `m` boyutlu bir `Ax` vektörüne taşır.

Bu dönüşümü anlamanın en kolay yolu sütunlara bakmaktır. `A`'nın birinci sütunu, birim vektör `e₁ = (1, 0, ..., 0)`'ın `A` ile dönüşmüş hâlidir. İkinci sütun `e₂`'nin, üçüncüsü `e₃`'ün görüntüsüdür. Bir `x` vektörü `x₁ e₁ + x₂ e₂ + ...` olarak yazılabildiği için, `Ax` bu görüntülerin `x`'in bileşenleriyle ağırlıklı toplamıdır: `Ax = x₁ a₁ + x₂ a₂ + ...`. Yani tüm dönüşümü, birim vektörlerin nereye gittiğini bilerek kurarsın.

Bu iki özellik matrisin "doğrusal" olduğunu garanti eder: `A(u + v) = Au + Av` ve `A(cu) = c(Au)`. Doğrusal dönüşüm, düz çizgileri düz çizgilere, paralel çizgileri paralel çizgilere götürür ve orijini sabit tutar. Bu yüzden bir karenin görüntüsü her zaman bir paralelkenardır.

Şekil 48.2, birim karenin dört temel dönüşümle nasıl değiştiğini gösterir. Kesikli kare birim karedir; dolu şekil `M` ile görüntüsüdür. İlk panelde 90 derece döndürme vardır: `R = [[0, -1], [1, 0]]`. `e₁ = (1, 0)` `(0, 1)`'e, `e₂ = (0, 1)` `(-1, 0)`'a gider. Bu, `R`'nin sütunlarıdır. İkinci panelde `S = [[2, 0], [0, 1]]` x yönünde iki kat uzatır. Üçüncü panelde `K = [[1, 1], [0, 1]]` bir kayma yapar: karenin üst kenarı sağa kayar, şekil eğilir. Dördüncü panelde `P = [[1, 0], [0, 0]]` her noktayı x eksenine indirir: kare bir çizgiye çöker.

![Şekil 48.2: Birim karenin dört dönüşümle görüntüsü. Her panelde det(M) yazılı: dönme ve kayma alanı korur, S alanı iki katına çıkarır, izdüşüm alanı sıfıra indirir.](gorseller/b48_donusum_det.png)

Şekil 48.2'nin her panelinde bir sayı var: determinant, `det(M)`. Determinant, dönüşümün alan ölçeğidir. Birim karenin alanı 1'dir; dönüşüm sonrası alan `|det(M)|` olur. `R` ve `K`'nin determinantı 1 olduğu için alanı korurlar; `S`'nin determinantı 2 olduğu için alan iki katına çıkar; `P`'nin determinantı 0 olduğu için kare bir çizgiye çöker ve alanı sıfır olur. Determinantın işareti yönelimi söyler: negatif determinant, dönüşümün bir ayna görüntüsü (yansıma) olduğunu gösterir. Bu bölümün 48.10'daki kısmında 2×2 ve 3×3 matrislerde determinantı elle hesaplayacağız.

Aşağıdaki program dört matrisin determinantını ve birim karenin köşelerinin görüntüsünü hesaplar. `donusum.py` aynı zamanda bir sonraki bölümün (48.5) bileşim örneğini de içerir.

```python
# donusum.py: 2B donusumler, determinant ve bilesim sirasi
import numpy as np

kare = np.array([[0, 1, 1, 0, 0],       # birim karenin kose noktalari
                 [0, 0, 1, 1, 0]], dtype=float)   # 1. satir x, 2. y

R = np.array([[0.0, -1.0], [1.0, 0.0]])  # 90 derece dondurme
S = np.array([[2.0, 0.0], [0.0, 1.0]])   # x ekseninde 2 kat olcekleme
K = np.array([[1.0, 1.0], [0.0, 1.0]])   # kayma
P = np.array([[1.0, 0.0], [0.0, 0.0]])   # x eksenine izdusum

for ad, M in [("R", R), ("S", S), ("K", K), ("P", P)]:
    print(ad, "det =", round(np.linalg.det(M), 6))

print("R kareyi dondurur (sutunlar kose):")
print(np.round(R @ kare, 3))

e1 = np.array([1.0, 0.0])
e2 = np.array([0.0, 1.0])
print("R(S e1) =", R @ (S @ e1), "  S(R e1) =", S @ (R @ e1))
print("R @ S =")
print(R @ S)
print("S @ R =")
print(S @ R)
print("AB == BA ?", np.allclose(R @ S, S @ R))
print("R e2 =", R @ e2)
```

```term
$ python donusum.py
R det = 1.0
S det = 2.0
K det = 1.0
P det = 0.0
R kareyi dondurur (sutunlar kose):
[[ 0.  0. -1. -1.  0.]
 [ 0.  1.  1.  0.  0.]]
R(S e1) = [0. 2.]   S(R e1) = [0. 1.]
R @ S =
[[ 0. -1.]
 [ 2.  0.]]
S @ R =
[[ 0. -2.]
 [ 1.  0.]]
AB == BA ? False
R e2 = [-1.  0.]
```

Çıktıdaki `R kareyi dondurur` tablosu, karenin köşe noktalarını sütun sütun verir: `(0,0), (0,1), (-1,1), (-1,0)` dördüncü noktaya kadar. Bu, karenin sola doğru 90 derece döndüğünü gösterir; burada köşe noktaları sütunlardır, çünkü her sütun bir noktanın `(x, y)` koordinatıdır.


## 48.5 Matris çarpımı: dönüşümlerin bileşimi ve sıra

İki matrisin çarpımı, iki dönüşümün art arda uygulanmasıdır. `(AB)x = A(Bx)` eşitliği bunu söyler: önce `B` uygulanır, sonra `A`. Bu yüzden matris çarpımının sırası önemlidir. Sayılarda `2 · 3 = 3 · 2`, ama dönüşümlerde genellikle `AB ≠ BA`. Önce döndürüp sonra uzatmak ile önce uzatıp sonra döndürmek farklı şekiller verir.

Şekil 48.3 bunu iki sıra için gösterir. Sol panelde önce `S` (x yönünde iki kat uzatma), sonra `R` (90 derece döndürme) uygulanır; bu, `R · S` matrisidir. Sağ panelde sıra tersinedir: önce `R`, sonra `S`; bu da `S · R` matrisidir. İki panelin şekilleri farklı, çünkü uzatma ile döndürme birbirini yer değiştirmez.

![Şekil 48.3: Aynı iki dönüşümün iki sırası. Sol: önce S, sonra R (R · S). Sağ: önce R, sonra S (S · R). Şekiller farklıdır: matris çarpımı değişmeli değildir.](gorseller/b48_bilesim.png)

Matris çarpımının kuralı açıktır: `A` `m × n`, `B` `n × p` boyutundaysa `AB` `m × p` boyutundadır ve ortadaki `n` boyutu eşleşmelidir. Çarpımın her elemanı, `A`'nın bir satırı ile `B`'nin bir sütununun nokta çarpımıdır: `(AB)ᵢⱼ = Σₖ aᵢₖ bₖⱼ`. Bu tanım, bir matris çarpımının `m · n · p` çarpma gerektirdiğini de gösterir; kare matrislerde bu `n³` demektir. Bölüm 12'deki karmaşıklık dilini burada kullanıyoruz ve 48.14'te bu maliyeti ölçeceğiz.

Çarpım **birleşmelidir** (`(AB)C = A(BC)`) ama değişmeli değildir. Parantez sırası iş miktarını da değiştirir: Bölüm 16.9'da matris zinciri çarpımını dinamik programlamayla optimize etmiştik, orada aynı sonucun farklı parantezlemelerinin maliyetini saymıştık. Sinir ağlarında bu önemli bir sonuç doğurur: birbirini izleyen iki doğrusal katman, tek bir matris çarpımına indirgenebilir (doğrusal olmayan fonksiyon araya girmezse). Bu yüzden katmanların arasına bir doğrusal olmayan fonksiyon koyulur; yoksa on katmanlı bir ağ bir katmanlı bir ağdan farksız olurdu. Bu fikri Bölüm 63'te MLP ile tekrar göreceksin.

Sıra önemlidir, bir örnek daha: `R = [[0, -1], [1, 0]]` ve `S = [[2, 0], [0, 1]]` için `R · S = [[0, -1], [2, 0]]`, `S · R = [[0, -2], [1, 0]]`. Birim vektör `e₁` üzerinde deneyelim. `R(S e₁)`: önce `S e₁ = (2, 0)`, sonra `R(2, 0) = (0, 2)`. `S(R e₁)`: önce `R e₁ = (0, 1)`, sonra `S(0, 1) = (0, 1)`. Sonuçlar farklı, `(0, 2)` ile `(0, 1)`. Bu hesabı `donusum.py` programı 48.4'te zaten yaptı. Çıktısının bileşim kısmını burada yeniden okuyalım:

- `R(S e1) = [0. 2.]` ve `S(R e1) = [0. 1.]` satırları elle yaptığımız hesabı doğrular.
- `AB == BA ? False` satırı, değişmeliliğin genel olarak sağlanmadığını gösterir.

Bu bölümün bir sonraki adımında aynı fikri üç boyuta taşıyacağız: bir uçağın gövde çerçevesinden dünya çerçevesine dönüşümü, art arda uygulanan dönmelerin bir matris çarpımıdır ve sıra, uçağın hangi eksen etrafında önce döndüğüne göre değişir.

## 48.6 Üç boyutta dönme ve homojen koordinatlar

İki boyutta bir dönme tek bir açıyla tanımlanır. Üç boyutta ise bir dönme üç açıyla tanımlanır: her biri bir eksen etrafında. Bir uçağın durumunu anlatan klasik üç açı şunlardır: **yaw** (ψ, z ekseni etrafında, burun sağa-sola), **pitch** (θ, y ekseni etrafında, burun yukarı-aşağı) ve **roll** (φ, x ekseni etrafında, kanat sallanması). Bu üç açının tek bir dönme matrisine nasıl birleştiği, uygulama sırasına bağlıdır. Bu bölümde yaygın bir sözleşmeyi kullanıyoruz: önce roll, sonra pitch, sonra yaw; yani `R = Rz(ψ) · Ry(θ) · Rx(φ)`. Uçuş yazılımınızda hangi sıra kullanılıyorsa onu izleyin; sıra yanlış olursa sonuç yanlış olur.

Bir dönme matrisinin önemli bir özelliği **ortogonalliktir**: `Rᵀ R = I` (birim matris). Bunun anlamı, dönmenin uzunlukları ve açıları bozmadığıdır. Sonucun pratik değeri büyüktür: `R`'nin tersi, `R`'nin devriğidir (transpozu). Tersini hesaplamak gerekmez, yalnızca satırları sütun yapmak yeter. Bu, gövde ile dünya arasındaki çeviriyi geri yönde yapmanın en ucuz yoludur.

Dönme tek başına yetmez: bir uçağın konumu da vardır ve konum eklenmesi gereken bir ötelemedir. Öteleme doğrusal değildir: `A(0) = 0` olmak zorunda olan bir matris dönüşümü orijini sabit tutar, oysa öteleme orijini hareket ettirir. Bunu çözmek için **homojen koordinatlar** kullanılır: 3 boyutlu bir noktaya dördüncü bir `1` bileşeni eklenir, `(x, y, z) → (x, y, z, 1)`. Bu sayede dönme ve öteleme tek bir 4×4 matrise yazılabilir:

T = [[R, t], [0, 1]]

Burada `t` öteleme vektörüdür. Bu matris, robotikte ve 3B grafikte standarttır. Bir İHA'nın gövde çerçevesinde `(2, 0, 0)` noktası, yani burnunun 2 metre önü, dünyada `T · (2, 0, 0, 1)` ile bulunur. Bu matrisin tersi de kapalı biçimde yazılır: `T⁻¹ = [[Rᵀ, -Rᵀ t], [0, 1]]`. Aşağıdaki program bu yapının üç özelliğini kontrol eder: ortogonallik, determinant ve geri dönüşüm.

```python
# rot3.py: 3B donme matrisleri, ortogonallik, homojen donusum
import numpy as np


def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


yaw, pitch, roll = np.deg2rad([90.0, 30.0, 10.0])
R = rot_z(yaw) @ rot_y(pitch) @ rot_x(roll)
print("R^T R == I ?", np.allclose(R.T @ R, np.eye(3)))
print("det(R)     =", round(np.linalg.det(R), 9))

# 4x4 homojen donusum: govde -> dunya
t = np.array([100.0, 50.0, 30.0])          # konum (metre)
T = np.eye(4)
T[:3, :3] = R
T[:3, 3] = t
p_govde = np.array([2.0, 0.0, 0.0, 1.0])  # govde x ekseninde 2 m
p_dunya = T @ p_govde
print("dunya koordinati =", np.round(p_dunya[:3], 4))

# ters donusum: dunya -> govde (R^T yeter, tersi gerekmez)
Tt = np.eye(4)
Tt[:3, :3] = R.T
Tt[:3, 3] = -R.T @ t
print("geri donus    =", np.round((Tt @ p_dunya)[:3], 4))
print("ters dogru ?  ", np.allclose(Tt @ p_dunya, p_govde))
```

```term
$ python rot3.py
R^T R == I ? True
det(R)     = 1.0
dunya koordinati = [100.      51.7321  29.    ]
geri donus    = [2. 0. 0.]
ters dogru ?   True
```

Çıktıdaki `det(R) = 1.0` önemlidir: ortogonal matrisin determinantı `+1` (dönme) ya da `-1` (yansıma) olabilir; bir dönme matrisi için `+1` olmak zorundadır. `dunya koordinati` satırında 2 metrelik gövde vektörü, dünyada `(100, 51.73, 29)` konumuna düşer. Bu konum, öteleme `t = (100, 50, 30)` ile dönmüş vektörün toplamıdır: `(100, 50, 30) + R(2, 0, 0)` ve `R(2, 0, 0) = (0, 1.7321, -1)`. Ters dönüşüm bu noktayı geri `(2, 0, 0)`'a getirir; `ters dogru ? True` satırı bunu doğrular.

Savunma ve uçuş yazılımında bu dönüşümlerin bir zayıf noktası vardır. Euler açıları (yaw, pitch, roll) belirli konumlarda belirsizleşir: pitch `±90°` olduğunda yaw ve roll aynı dönmeyi ürettiği için iki açının ayrımı kaybolur. Bu duruma **kilitlenme** (gimbal lock) denir (genel bilgi). Bu nedenle birçok uçuş sistemi dönmeyi dörtlü sayılarla (quaternion) temsil eder. Bu bölümde quaternion'a girmiyoruz; yalnızca bilmen gereken, Euler açılarının bir sözleşme olduğu ve bu sözleşmenin sınırları olduğudur.

## 48.7 Doğrusal sistemler: Gauss eliminasyonu ve kısmi pivotlama

Lineer cebirin en sık kullanılan işi `A x = b` denklemini çözmektir. `A` bilinen bir katsayı matrisi, `b` bilinen bir vektör ve `x` bulunması gereken bilinmeyendir. Bu denklem, bir sensör ağında ölçümlerden konumu çözmekten, bir sinir ağında en küçük kareler ile bir katmanın ağırlığını bulmaya kadar her yerde çıkar.

Bu denklemi çözmenin en eski yolu **Gauss eliminasyonudur**. Fikir basit: ilk denklemi kullanarak ikinci ve üçüncü denklemlerden birinci bilinmeyeni yok et; sonra ikinci denklemi kullanarak üçüncüden ikinciyi yok et; en sonda üçgen bir sistem kalır ve bunu alttan yukarı çözersin. İlk adıma **ileri eleme**, ikinci adıma **geri yerine koyma** denir.

Eleme adımında bir tehlike vardır: bölen olarak kullanacağımız eleman, **pivot**, sıfır olabilir ya da çok küçük olabilir. Küçük bir pivot, büyük bir çarpanın (`m = aᵢₖ / pivot`) doğmasına yol açar ve bu çarpan, yuvarlama hatasını bütün satıra yayar. Bu yüzden **kısmi pivotlama** kullanılır: her adımda, ilgili sütundaki en büyük mutlak değerli elemanı içeren satır, pivot satırı olarak seçilir ve yerine takas edilir. Kısmi pivotlama çarpanları 1'in altında tutar ve hata büyümesini sınırlar. Sütunun tamamı sıfırsa hiçbir takas yardım etmez; o durumda matris tekildir (48.8).

Bunu bir örnekle görelim. Aşağıdaki sistemin gerçek çözümü `x = 1` ve `y = 1`'dir (tam değer `x = 1/(1 - ε)`):

ε · x + y = 1
x + y = 2

`ε` çok küçük bir sayı olsun. Pivotlamadan, birinci satırdaki `ε`'u pivot kabul edersek, ikinci satırdan `1/ε` katını çıkarmamız gerekir. Bu çarpan devasa olur ve ikinci satırın `y` katsayısı `1 - 1/ε` gibi bir değere iner. `1/ε` büyük olduğunda `1`, yuvarlama sırasında kaybolur ve geriye yalnızca büyük sayılar kalır. Sonuçta `y` doğru (`1`) çıkar, ama `x = (1 - y)/ε` hesabında `1 - y` sıfıra iner ve `x = 0` olur. Gerçek değerde `1 - y` yalnızca `ε·x ≈ 10⁻²⁰` kadardır; bu fark, büyük sayılarla yapılan çıkarmanın yuvarlama hatasında kaybolur. Aşağıdaki program `ε`'u `10⁻⁴`'ten `10⁻²⁰`'ye düşürerek hem pivotsuz hem pivotlu sürümü çalıştırır.

```python
# gauss.py: Gauss eliminasyonu, kismi pivotlama ve pivotsuz felaket
import numpy as np


def gauss_coz(A, b, pivot=True):
    M = np.array(A, dtype=float)
    y = np.array(b, dtype=float)
    n = len(y)
    for k in range(n - 1):
        if pivot:                       # en buyuk |.| satiri
            p = k + np.argmax(np.abs(M[k:, k]))
            M[[k, p]] = M[[p, k]]
            y[[k, p]] = y[[p, k]]
        for i in range(k + 1, n):      # k. sutunun altini sifirla
            m = M[i, k] / M[k, k]
            M[i, k:] -= m * M[k, k:]
            y[i] -= m * y[k]
    x = np.zeros(n)                     # geri yerine koyma
    for i in range(n - 1, -1, -1):
        x[i] = (y[i] - M[i, i+1:] @ x[i+1:]) / M[i, i]
    return x


for eps in [1e-4, 1e-8, 1e-12, 1e-16, 1e-20]:
    A = [[eps, 1.0], [1.0, 1.0]]
    b = [1.0, 2.0]                      # gercek cozum: x = 1, y = 1
    x0 = gauss_coz(A, b, pivot=False)
    x1 = gauss_coz(A, b, pivot=True)
    print("eps=%-6g pivotsuz: x=%-10.6g pivotlu: x=%.6g"
          % (eps, x0[0], x1[0]))

rng = np.random.default_rng(42)
enb = 0.0
for _ in range(200):
    n = int(rng.integers(2, 8))
    A = rng.standard_normal((n, n))
    b = rng.standard_normal(n)
    fark = np.max(np.abs(gauss_coz(A, b) - np.linalg.solve(A, b)))
    enb = max(enb, fark)
print("200 rastgele sistem, en buyuk fark:", "%.2e" % enb)
```

```term
$ python gauss.py
eps=0.0001 pivotsuz: x=1.0001     pivotlu: x=1.0001
eps=1e-08  pivotsuz: x=1          pivotlu: x=1
eps=1e-12  pivotsuz: x=0.999978   pivotlu: x=1
eps=1e-16  pivotsuz: x=2.22045    pivotlu: x=1
eps=1e-20  pivotsuz: x=0          pivotlu: x=1
200 rastgele sistem, en buyuk fark: 6.20e-10
```

Çıktı üç şeyi gösteriyor. Birincisi, pivotlu çözüm her `ε` için `x = 1` (yuvarlama içinde) verir. İkincisi, pivotsuz çözüm `ε = 10⁻¹²`'de `0.999978` verir ve hata başlar; `ε = 10⁻¹⁶`'da `2.22045` verir ve tamamen yanlış olur; `ε = 10⁻²⁰`'de `0` verir. Bu, **kayan nokta felaketinin** (floating-point catastrophe) bir örneğidir: sonuç bir sayıyı kaybetmekten değil, büyük bir sayının küçük bir sayıyı yutmasından gelir. Üçüncüsü, 200 rastgele sistemde pivotlu yöntemin LAPACK'in (NumPy'nin `solve`'u) sonucuyla en büyük farkı `6.20e-10`'dur. Bu fark sıfır değil, çünkü iki yöntem yuvarlamayı farklı sırayla yapar. Rastgele sistemlerde fark küçük kalır, çünkü bu sistemlerin kondisyon sayısı genellikle küçüktür; bunu 48.10'da ölçeceğiz. Pivotsuz yöntemin hatası ise ε'a bağlı olarak kontrolden çıkabilir.

Şekil 48.4, üç bilinmeyenli bir sistemde kısmi pivotlamanın her adımını gösterir. Sistem `Çözümlü Örnek 2`'de de elle çözülecek; burada sadece adımların görünümüne bakıyoruz.

![Şekil 48.4: Kısmi pivotlu Gauss eliminasyonu. (a) başlangıç, sütun 1'de en büyük |.| = |-3| satır 1 ile 2'yi takas eder. (b) birinci eleme sonrası. (c) ikinci eleme sonrası üst üçgen (köşegen: -3, 1.667, 0.2). (d) geri yerine koyma ile x = 2, y = 3, z = -1.](gorseller/b48_gauss_adimlar.png)

## 48.8 LU ayrışımı, rank ve çözüm uzayı

Gauss eliminasyonunun yaptığı işi bir matris çarpımı olarak da yazabiliriz. Eleme sırasında kullandığımız çarpanları alt üçgen bir `L` matrisinde, sonucu üst üçgen bir `U` matrisinde tutarsak `P A = L U` yazabiliriz. Burada `P` satır takaslarını kaydeden bir permütasyon matrisidir. Bu ayrışım, **LU ayrışımı** olarak bilinir ve bir sistemi birden çok kez çözeceksen çok değerlidir: `A`'yı bir kez ayrıştırırsın, her yeni `b` için yalnızca iki üçgen sistem çözersin. Bu, `A`'nın tersini almaktan hem daha ucuz hem genellikle daha kararlıdır (48.10'da ölçeceğiz).

Aşağıdaki program kısmi pivotlu LU ayrışımını kendi kodumuzla yazar ve `P A = L U` eşitliğini kontrol eder. Tekil bir matrisin `U`'sunu ve rank'ını da gösterir.

```python
# lu.py: kismi pivotlu LU ayrisimi PA = LU ve rank
import numpy as np


def lu_pivot(A):
    U = np.array(A, dtype=float)
    n = U.shape[0]
    L = np.eye(n)
    P = np.eye(n)
    for k in range(n - 1):
        p = k + np.argmax(np.abs(U[k:, k]))
        if p != k:
            U[[k, p], :] = U[[p, k], :]
            P[[k, p], :] = P[[p, k], :]
            L[[k, p], :k] = L[[p, k], :k]
        for i in range(k + 1, n):
            L[i, k] = U[i, k] / U[k, k]
            U[i, k:] -= L[i, k] * U[k, k:]
    return P, L, U


rng = np.random.default_rng(42)
A = rng.integers(-5, 6, size=(4, 4)).astype(float)
P, L, U = lu_pivot(A)
print("PA == LU ?", np.allclose(P @ A, L @ U))
print("L (alt ucgen, birler koseguede):")
print(L)
print("rank(A) =", np.linalg.matrix_rank(A))

# ikinci satir = 2 * birinci satir
tekil = np.array([[1.0, 2.0], [2.0, 4.0]])
_, _, U2 = lu_pivot(tekil)
print("tekil matris U:")
print(U2)
print("rank =", np.linalg.matrix_rank(tekil))
```

```term
$ python lu.py
PA == LU ? True
L (alt ucgen, birler koseguede):
[[ 1.          0.          0.          0.        ]
 [ 0.6         1.          0.          0.        ]
 [ 0.2        -0.5862069   1.          0.        ]
 [-0.6        -0.82758621 -0.36158192  1.        ]]
rank(A) = 4
tekil matris U:
[[2. 4.]
 [0. 0.]]
rank = 1
```

`PA == LU ? True` satırı ayrışımın doğru olduğunu gösterir. `L` matrisinin köşegeni birlerden oluşur ve alt üçgende eleme çarpanları vardır; çarpanlar 1'in altındadır, çünkü pivot en büyük elemandır. Bu, kısmi pivotlamanın kararlılığa etkisini görmenin bir yoludur.

**Rank** (rank, sıra), bir matrisin bağımsız satır ya da sütunlarının sayısıdır. Bir matrisin rank'ı, LU ayrışımında sıfır olmayan pivot sayısıdır (sayısal bir tolerans içinde). `4 × 4` rastgele tam sayılı matrisin rank'ı 4'tür. İkinci matris `[[1, 2], [2, 4]]`'tür: ikinci satır birincinin iki katıdır. Eleme sonunda ikinci satır sıfıra iner ve `U` yalnızca bir sıfır olmayan satır içerir; rank 1'dir. Bu durumda matris **tekildir** (singular): tersi yoktur.

Rank, bir `A x = b` sisteminin kaç çözümü olduğunu söyler. Üç durum vardır. Eğer `A` karesi ve tam rank'lıysa (rank = n), sistemin tek bir çözümü vardır. Eğer rank eksikse, iki durum olur: `b` sütun uzayında değilse (sistem bir "tutarsızlık" içeriyorsa) çözüm yoktur; `b` sütun uzayındaysa çözüm sonsuz çoktur, çünkü bir boş uzay vektörü eklenerek çözüm değiştirilebilir. Örneğin `[[1, 2], [2, 4]] x = (1, 2)` sonsuz çözümlüdür (`x = (1, 0)` ve `x = (0, 0.5)` ikisi de çalışır), `[[1, 2], [2, 4]] x = (1, 3)` ise hiç çözümü yoktur. Bu üç durumun ayrımını bir sonraki bölümde vektör uzayları ve dört temel alt uzay ile tamamen açıklayacağız.

Bir uygulama: EV Dashboard'daki sensör kalibrasyonunda birkaç ölçüm noktasından bir doğrusal model kurarsan, ölçümlerin hepsi aynı bilgiyi tekrarlıyorsa (rank eksikse) model parametrelerini tek bir değerle belirleyemezsin. Rank kontrolü, bu tür bir kalibrasyonun neden kararsız olduğunu önceden söyler; bu, sayısal bir uyarı mekanizması kurmanın ilk adımıdır.


## 48.9 Vektör uzayları: bağımsızlık, taban ve dört temel alt uzay

Bir vektör uzayı, toplama ve ölçekleme işlemlerinin kapalı olduğu vektörler kümesidir: iki vektörü topladığında ya da bir sayıyla çarptığında yine o kümede kalırsın. `ℝ³` bunun en tanıdık örneğidir. Bu uzayın içinde bir alt küme de bir **alt uzay** olabilir: iki düzlemden biri, `z = 0` düzlemi gibi, kendi içinde toplamayı ve ölçeklemeyi kapatır.

Bir uzayı tanımlamanın en verimli yolu **taban** (basis) kavramıyla olur. Bir vektör kümesi iki koşulu sağlarsa taban oluşturur. Birincisi, **lineer bağımsızlık**: hiçbir vektör diğerlerinin doğrusal bir kombinasyonu değildir; yani `c₁v₁ + c₂v₂ + ... = 0` denklemi yalnızca tüm `cᵢ = 0` ile sağlanır. İkincisi, **üretme** (span): uzayın her vektörü bu vektörlerin bir kombinasyonu olarak yazılabilir. Bir tabandaki vektör sayısı uzayın **boyutudur**. `ℝ³`'ün boyutu 3'tür; `z = 0` düzleminin boyutu 2'dir.

Bir matrisle ilişkili dört temel alt uzay, bu kavramların en önemli uygulamasıdır. `A` bir `m × n` matris olsun ve rank'ı `r` olsun. Dört alt uzay şunlardır:

- **Sütun uzayı** C(A): `A`'nın sütunlarının ürettiği alt uzay, `ℝ^m`'nin içinde, boyutu `r`. `A x = b` sisteminin çözülebilmesi için `b`'nin bu uzayda olması gerekir.
- **Satır uzayı** C(Aᵀ): satırların ürettiği alt uzay, `ℝ^n`'nin içinde, boyutu da `r`.
- **Boş uzay** N(A): `A x = 0` denkleminin çözümleri, `ℝ^n`'nin içinde, boyutu `n − r`.
- **Sol boş uzay** N(Aᵀ): `Aᵀ y = 0` denkleminin çözümleri, `ℝ^m`'nin içinde, boyutu `m − r`.

Bu dört uzayın en güzel özelliği şudur: satır uzayı ile boş uzay birbirine diktir; sütun uzayı ile sol boş uzay da birbirine diktir. Yani her `ℝ^n` vektörü, satır uzayındaki bir parçayla boş uzaydaki bir parçanın toplamıdır. Bu, bir sistemin çözüm kümesinin neden bir "öteleme" ve bir "boş uzay" olarak yazıldığını açıklar.

Elle bir örnek yapalım. Aşağıdaki `3 × 3` matrisin üçüncü sütunu birinci ile ikincisinin toplamıdır: `c₁ = (1, 2, 1)`, `c₂ = (2, 4, 0)`, `c₃ = (3, 6, 1) = c₁ + c₂`. Bu yüzden rank 2'dir ve boş uzay boyutu `3 − 2 = 1`'dir. Boş uzayda bir vektör `(1, 1, −1)`'dir: `c₁ + c₂ − c₃ = 0`. Aşağıdaki program rank'ı, boş uzayı ve sol boş uzayı SVD ile hesaplar ve dört alt uzayın dikliğini ve `b`'nin çözülebilirliğini kontrol eder.

```python
# altuzay.py: dort temel alt uzay (sutun, satir, bos, sol bos)
import numpy as np

A = np.array([[1.0, 2.0, 3.0],
              [2.0, 4.0, 6.0],
              [1.0, 0.0, 1.0]])
m, n = A.shape
r = np.linalg.matrix_rank(A)
print("rank(A) =", r, " m =", m, " n =", n)

# bos uzay N(A): A x = 0 cozumleri, SVD'nin sag tekil vektorleri
U, s, Vt = np.linalg.svd(A)
N = Vt[r:].T                       # n x (n - r)
print("N(A) boyutu =", N.shape[1])
print("N(A) tabani (sutun):", np.round(N[:, 0], 4))
print("A N = 0 ?", np.allclose(A @ N, 0))

# sol bos uzay N(A^T): A^T y = 0
Nl = U[:, r:]                      # m x (m - r)
print("N(A^T) boyutu =", Nl.shape[1], " A^T y = 0 ?",
      np.allclose(A.T @ Nl, 0))

# sutun uzayi C(A) ile bos uzayin dik olmasi
C = U[:, :r]
print("C(A) ile N(A^T) dik ?", np.allclose(C.T @ Nl, 0))

# A x = b cozulebilir mi? b in C(A) ise evet
b_iyi = A @ np.array([1.0, 0.0, 1.0])
b_kotu = np.array([1.0, 0.0, 0.0])
for ad, b in [("b_iyi", b_iyi), ("b_kotu", b_kotu)]:
    yon = Nl.T @ b                 # sol bos uzaydaki bilesen
    print(ad, "cozulebilir mi ?", np.allclose(yon, 0))
```

```term
$ python altuzay.py
rank(A) = 2  m = 3  n = 3
N(A) boyutu = 1
N(A) tabani (sutun): [-0.5774 -0.5774  0.5774]
A N = 0 ? True
N(A^T) boyutu = 1  A^T y = 0 ? True
C(A) ile N(A^T) dik ? True
b_iyi cozulebilir mi ? True
b_kotu cozulebilir mi ? False
```

Çıktıdaki `N(A) tabani` vektörü `(-0.5774, -0.5774, 0.5774)`'tür; bu, `(1, 1, -1)`'in birim uzunluğa ölçeklenmiş hâlidir (`1/√3 ≈ 0.5774`). Program bu vektörü SVD'nin sağ tekil vektörlerinden alır. Bu bölümün 48.13'te göreceğin SVD'nin dört alt uzayı tam olarak bu şekilde açığa çıkarması, onu lineer cebirin en güçlü aracı yapar.

`b_kotu` için çözümlenebilirlik kontrolü `False` döner. Bunun sebebi `b = (1, 0, 0)`'ın sütun uzayında olmamasıdır; sol boş uzaydaki bir vektörle nokta çarpımı sıfır olmadığı için sistem tutarsızdır. Mühendislikte bu, bir sensör ağında fazla denklemle uğraşırken veri uyuşmazlığını yakalamanın matematiksel yoludur.

## 48.10 Ters, determinant ve koşul sayısı: solve neden inv'den iyi

`n × n` bir `A` matrisinin tersi `A⁻¹`, `A A⁻¹ = I` koşulunu sağlayan matristir. Ters yalnızca `A` tam rank'lıysa (tekil değilse) vardır. 2×2 matrisler için formül açıktır: `[[a, b], [c, d]]⁻¹ = (1/(ad − bc)) [[d, −b], [−c, a]]`. Paydaki `ad − bc` sayısı **determinanttır**. Determinant sıfırsa ters yoktur.

Üç boyutta determinantı genişleme ile hesaplayabilirsin. Bir örnek: `A = [[2, 1, −1], [−3, −1, 2], [−2, 1, 2]]` için

det(A) = 2 · ((−1)(2) − 2·1) − 1 · ((−3)(2) − 2·(−2)) + (−1) · ((−3)(1) − (−1)(−2)) = −8 + 2 + 5 = −1

Aynı sonucu LU ayrışımıyla da bulabilirsin: `det(A) = (−1)^takas · Π pivotlar`. Bu örnekte iki takas yapıldı (sayı çift, işaret `+1`) ve pivotlar `−3, 1.667, 0.2`; çarpım `−1`'dir. Determinantın bu hesabı, 48.7'deki Gauss adımlarıyla birebir uyuşur.

Determinant bir **alan** ölçeğidir (48.4'te gördük). Ama asıl önemi, ters matrisin varlığını ve tekilliği belirlemesidir. Bu yüzden ters matris, çözüm kararlılığı için hem doğrudan hem dolaylı olarak önemlidir.

Burada asıl tuzak şudur: bir `A x = b` sistemini çözmek için `A⁻¹` hesaplayıp `A⁻¹ b` yazmak yaygın bir alışkanlıktır, ama genellikle yanlıştır. Ters hesaplamak `n³` iş gerektirir ve daha büyük sabitlerle çalışır; üstelik ters matrisin hesaplanması sırasında yuvarlama hataları birikir. `np.linalg.solve(A, b)` ise LU ayrışımını ve iki üçgen çözümü kullanır; çoğu zaman daha hızlı ve daha doğrudur. Aşağıdaki programda rastgele `n × n` sistemler için iki yolu zamanlayıp hatalarını karşılaştırıyoruz.

```python
# solve_inv.py: inv(A) @ b ile solve(A, b): hiz ve dogruluk
import time
import numpy as np

rng = np.random.default_rng(42)
for n in [200, 800, 2000]:
    A = rng.standard_normal((n, n))
    x_gercek = rng.standard_normal(n)
    b = A @ x_gercek
    t0 = time.perf_counter()
    x1 = np.linalg.solve(A, b)
    t1 = time.perf_counter()
    x2 = np.linalg.inv(A) @ b
    t2 = time.perf_counter()
    e1 = np.max(np.abs(x1 - x_gercek))
    e2 = np.max(np.abs(x2 - x_gercek))
    print("n=%4d  solve: %7.4f s, hata %.1e | "
          "inv@b: %7.4f s, hata %.1e"
          % (n, t1 - t0, e1, t2 - t1, e2))
```

```term
$ python solve_inv.py
n= 200  solve:  0.0007 s, hata 5.0e-14 | inv@b:  0.1388 s, hata 1.3e-13
n= 800  solve:  0.0129 s, hata 1.4e-12 | inv@b:  0.4139 s, hata 4.9e-12
n=2000  solve:  0.1303 s, hata 1.0e-12 | inv@b:  0.4130 s, hata 7.8e-12
```

Çıktı, `solve`'un `inv(A) @ b` yolundan hızlı olduğunu (özellikle küçük `n`'lerde) ve hatalarının aynı düzeyde ama `inv` yolunda birkaç kat daha büyük olduğunu gösterir. Zamanlar makineye ve çalıştırmaya göre değişir; birkaç kez çalıştırırsan sırayı genellikle korursun, rakamları değil. Bu ayrım, Bölüm 12'de anlattığımız sabit çarpanların ve yuvarlama hatalarının pratik sonucudur.

**Koşul sayısı** (condition number), bir matrisin girdideki küçük değişikliklere ne kadar duyarlı olduğunu ölçer. 2-normla tanımlanır: `κ(A) = ‖A‖₂ · ‖A⁻¹‖₂ = σ_max / σ_min` (σ'lar tekil değerlerdir, 48.13'te tanımlanacak). `κ` büyükse, `b`'deki küçük bir hata `x`'te büyük bir hataya dönüşebilir. Pratik bir kural: `κ ≈ 10^k` ise sonucun yaklaşık `k` ondalık basamağını kaybedersin (genel bilgi; çift duyarlıklı sayılarda ~16 basamak vardır).

Bu kuralı görmek için **Hilbert matrisine** bakalım. `H` matrisinin elemanları `1/(i + j + 1)` olur. Bu matris bilinen en kötü koşullu matrislerden biridir. Aşağıdaki program `n` büyüdükçe `κ`'nın nasıl patladığını ve çözümün ne kadar bozulduğunu gösterir. Gerçek çözüm her zaman `x = (1, 1, ..., 1)`'dir; `b = H x` olarak kurulur, böylece hata doğrudan görülebilir.

```python
# kosul.py: kosul sayisi, Hilbert matrisi ve kayip basamaklar
import numpy as np


def hilbert(n):
    i = np.arange(n)
    return 1.0 / (i[:, None] + i[None, :] + 1)


print(" n     kappa(H)   kayip_bas.  hata(solve)   hata(inv)")
for n in range(2, 13, 2):
    H = hilbert(n)
    x_gercek = np.ones(n)
    b = H @ x_gercek
    x1 = np.linalg.solve(H, b)
    x2 = np.linalg.inv(H) @ b
    kappa = np.linalg.cond(H)
    e1 = np.max(np.abs(x1 - x_gercek))
    e2 = np.max(np.abs(x2 - x_gercek))
    kayip = np.log10(kappa)
    print("%2d  %10.2e  %8.2f  %11.2e  %11.2e"
          % (n, kappa, kayip, e1, e2))
```

```term
$ python kosul.py
 n     kappa(H)   kayip_bas.  hata(solve)   hata(inv)
 2    1.93e+01      1.29     6.66e-16     8.88e-16
 4    1.55e+04      4.19     6.55e-14     9.09e-13
 6    1.50e+07      7.17     2.39e-10     1.05e-09
 8    1.53e+10     10.18     1.19e-07     1.91e-06
10    1.60e+13     13.20     1.69e-04     5.55e-03
12    1.76e+16     16.25     6.96e-01     2.10e+01
```

Tablo açıktır. `n = 2`'de `κ ≈ 19`, yani yaklaşık bir basamak kaybedersin ve hata `10⁻¹⁶` mertebesindedir. `n = 12`'de `κ ≈ 1.8 · 10¹⁶`, yani çift duyarlıklı sayıların tüm basamaklarını kaybedersin; hata `0.70` olur ve ters matrisle çözüm `21` gibi tamamen anlamsız bir değer verir. `kayip_bas.` sütunu `log₁₀ κ`'dır ve bu sayı, kaybolan basamak sayısının yaklaşık ölçüsüdür: `n = 12` için `16.25`. Bu, çift duyarlıklı sayıların yaklaşık 16 anlamlı basamağının tamamına karşılık gelir.

Bu deneyin ders şudur: koşul sayısını bilmeden bir sistemin çözümüne güvenme. Gerçek bir projede `np.linalg.cond(A)` ile kontrol et; `κ` çok büyükse ya veriyi yeniden ölçeklemelisin ya da en küçük kareler gibi daha kararlı bir formülasyon kullanmalısın (48.11).

## 48.11 Ortogonallik: Gram–Schmidt, QR ve en küçük kareler

İki vektör **ortogonal** (dik) ise nokta çarpımları sıfırdır. Bir vektör kümesinin tüm vektörleri birbirine dik ve birim uzunluktaysa **ortonormal** derleriz. Ortonormal bir sütun kümesi `Q` matrisinde toplanırsa `Qᵀ Q = I` olur. Bu basit eşitlik, sayısal lineer cebirde en değerli araçlardan birinin temelidir: ortonormal bir matrisin tersi devriğidir, yani tersini almak için yalnızca devrik almak yeter.

Ortonormal bir taban nasıl elde edilir? **Gram–Schmidt** süreci bunu yapar: her yeni vektörden önceki vektörlerin izdüşümlerini çıkarır, kalan kısmı normalize eder. Klasik sürüm, izdüşümleri **orijinal** vektörden hesaplar. Değiştirilmiş sürüm ise her çıkarmadan sonra **güncel** vektörü kullanır. Matematiksel olarak ikisi aynıdır, sayısal olarak değildir. Aşağıdaki program iki sürümü Hilbert matrisleri üzerinde karşılaştırır ve NumPy'nin QR ayrışımını da ekler. Ölçüt `‖QᵀQ − I‖_F`'dir: sıfır mükemmel dikliktir, büyük değer ortogonalliğin kaybını gösterir.

```python
# gram.py: Gram-Schmidt (klasik ve degistirilmis) ve QR kararliligi
import numpy as np


def cgs(A):
    Q = np.zeros(A.shape)
    for j in range(A.shape[1]):
        a = A[:, j]
        r = Q[:, :j].T @ a                 # hepsi ORIJINAL a ile
        v = a - Q[:, :j] @ r
        Q[:, j] = v / np.linalg.norm(v)
    return Q


def mgs(A):
    Q = np.array(A, dtype=float)
    for j in range(Q.shape[1]):
        Q[:, j] /= np.linalg.norm(Q[:, j])
        for k in range(j + 1, Q.shape[1]):
            Q[:, k] -= (Q[:, j] @ Q[:, k]) * Q[:, j]   # guncel v ile
    return Q


def hilbert(n):
    i = np.arange(n)
    return 1.0 / (i[:, None] + i[None, :] + 1)


def dikgenlik_kaybi(Q):
    return np.linalg.norm(Q.T @ Q - np.eye(Q.shape[1]))


print(" n  klasik_GS   degistirilmis  numpy_QR")
for n in [4, 6, 8, 10, 12]:
    A = hilbert(n)
    k1 = dikgenlik_kaybi(cgs(A))
    k2 = dikgenlik_kaybi(mgs(A))
    k3 = dikgenlik_kaybi(np.linalg.qr(A)[0])
    print("%2d  %9.2e  %12.2e  %9.2e" % (n, k1, k2, k3))
```

```term
$ python gram.py
 n  klasik_GS   degistirilmis  numpy_QR
 4   3.69e-11      4.22e-13   1.09e-15
 6   3.75e-04      3.55e-10   9.61e-16
 8   1.44e+00      3.62e-07   1.20e-15
10   3.47e+00      5.19e-05   1.50e-15
12   5.48e+00      3.27e-01   1.43e-15
```

Tablo, iki sürümün farkını ve hatanın nasıl büyüdüğünü gösterir. `n = 4`'te klasik sürümün dikliği `3.7e-11`, değiştirilmiş olanın `4.2e-13` bozulur. `n = 8`'de klasik sürümün dikliği tamamen kaybolur (`1.44`), değiştirilmiş sürüm ise `3.6e-7` ile hâlâ kullanılabilirdir. NumPy'nin QR'ı (Householder yansımalarıyla yapılır, genel bilgi) her `n` için `10⁻¹⁵` düzeyinde kalır; yani ortogonalliği en iyi koruyan yöntem budur. Genel kural: klasik Gram–Schmidt'te dikliğin bozulması `κ²` ile, değiştirilmiş sürümde `κ` ile orantılıdır (genel bilgi). Tablodaki büyüme bu eğilimle uyumludur; kesin sabitleri ölçmedik.

Ortogonalliğin en önemli uygulaması **en küçük kareler** problemidir. Bir `A x ≈ b` sisteminde `b` çoğu zaman gürültülü bir ölçümdür ve `A x = b` tam olarak çözülemez. Bu durumda `‖A x − b‖₂` hatasını en küçük yapan `x`'i ararız. Bu, Bölüm 58'deki doğrusal regresyonun matematiğidir.

Bu problemi çözmenin klasik yolu **normal denklemler**dir: `AᵀA x = Aᵀ b`. Bu denklem tek satırda yazılır ama sayısal olarak tehlikelidir: `AᵀA`'nın koşul sayısı `κ(A)²`'dir. Yani `A`'nın koşulu `10⁶` ise `AᵀA`'nın koşulu `10¹²` olur. Daha kararlı yol **QR** yöntemidir: `A = QR` yazarak `R x = Qᵀ b` üçgen sistemini çözersin. Aşağıdaki program bir telemetri verisine polinom uydurur (yükseklik zamanın fonksiyonu olarak) ve üç yolu karşılaştırır: normal denklemler, QR ve NumPy'nin `lstsq`'i.

```python
# lsq.py: en kucuk kareler: normal denklem, QR, lstsq
import numpy as np

rng = np.random.default_rng(42)
t = np.linspace(0.0, 1.0, 60)
irtifa = 120 + 80 * t - 40 * t**2 + rng.normal(0, 0.5, t.size)

for d in [3, 6, 10]:
    A = np.vander(t, d + 1, increasing=True)   # 1, t, t^2, ...
    x_norm = np.linalg.solve(A.T @ A, A.T @ irtifa)
    Q, R = np.linalg.qr(A)
    x_qr = np.linalg.solve(R, Q.T @ irtifa)
    x_ls = np.linalg.lstsq(A, irtifa, rcond=None)[0]
    print("derece %2d  cond(A)=%8.2e  cond(A^T A)=%8.2e"
          % (d, np.linalg.cond(A), np.linalg.cond(A.T @ A)))
    fark_n = np.max(np.abs(x_norm - x_ls))
    fark_q = np.max(np.abs(x_qr - x_ls))
    print("   fark(normal, lstsq)=%8.2e  fark(QR, lstsq)=%8.2e"
          % (fark_n, fark_q))
```

```term
$ python lsq.py
derece  3  cond(A)=1.19e+02  cond(A^T A)=1.41e+04
   fark(normal, lstsq)=1.05e-10  fark(QR, lstsq)=1.14e-12
derece  6  cond(A)=2.00e+04  cond(A^T A)=4.01e+08
   fark(normal, lstsq)=3.20e-07  fark(QR, lstsq)=8.57e-11
derece 10  cond(A)=2.05e+07  cond(A^T A)=4.21e+14
   fark(normal, lstsq)=6.36e+02  fark(QR, lstsq)=6.93e-08
```

Çıktı tam olarak beklenen davranışı gösterir. Derece 3'te normal denklemlerin çözümü `lstsq`'ten `10⁻¹⁰` kadar uzaktadır; QR ise `10⁻¹²`. Derece 6'da normal denklemlerin hatası `3.2e-7`'ye çıkar; `cond(AᵀA)` `4 · 10⁸`'dir. Derece 10'da `cond(A) = 2 · 10⁷`, `cond(AᵀA) = 4 · 10¹⁴` olur ve normal denklemlerin sonucu `636` fark verir: sonuç tamamen anlamsızdır. QR ise `10⁻⁸` düzeyinde kalır. Bu, `κ²` etkisinin somut bir ölçümüdür.

Bu deney, bir uygulama kuralı verir: polinom uydururken ya da bir regresyon çözerken `np.linalg.lstsq` ya da QR kullan; normal denklemleri elle kurmak yalnızca küçük ve iyi koşullu problemlerde kabul edilebilir. Telemetri verisinde yüksek dereceli polinom uydurmak zaten kötü bir fikirdir (aşırı uyum, Bölüm 57); ama yanlış yöntem seçmek, kötü fikri daha da kötüleştirir.

## 48.12 Özdeğer ve özvektör: yönü değişmeyen vektörler

Bir `A` matrisi çoğu vektörün yönünü değiştirir. Ama bazı özel vektörler yalnızca uzunluklarını değiştirir: `A v = λ v`. Bu eşitliği sağlayan `v`'ye **özvektör** (eigenvector), `λ`'ya **özdeğer** (eigenvalue) denir. Özvektör, dönüşümün "doğal eksenleridir": o yönlerde dönüşüm yalnızca ölçekleme yapar.

Şekil 48.5 bunu gösterir. `A = [[3, 1], [1, 3]]` matrisi `v₁ = (1, 1)` yönünü dört kat, `v₂ = (1, −1)` yönünü iki kat uzatır. Yani `λ₁ = 4` ve `λ₂ = 2`'dir. Öte yandan `w = (1, 0)` vektörü `A w = (3, 1)` olur; yönü değişir. Bu dönüşümü en iyi anlatan vektörler `v₁` ve `v₂`'dir.

![Şekil 48.5: Solda üç başlangıç vektörü (v1, v2, w). Sağda A uygulandıktan sonra: v1 yönü korunup dört kat, v2 yönü korunup iki kat uzar; w'nun yönü değişir. Özvektörler dönüşümün doğal eksenleridir.](gorseller/b48_ozvektor.png)

Özdeğerleri elle bulmanın yolu karakteristik denklemdir: `A v = λ v` yazılır, `(A − λ I) v = 0` elde edilir ve sıfırdan farklı bir `v` için `det(A − λ I) = 0` olmalıdır. Bu iki boyutlu örnekte `det([[3 − λ, 1], [1, 3 − λ]]) = (3 − λ)² − 1 = λ² − 6λ + 8`. Kökler `λ = 4` ve `λ = 2`'dir. Her `λ` için `(A − λ I) v = 0` denklemini çözersen özvektörleri bulursun; `λ = 4` için `v₁ = (1, 1)` ve `λ = 2` için `v₂ = (1, −1)` çıkar.

Bu özvektörler birbirine diktir, çünkü `A` simetriktir (`Aᵀ = A`). Simetrik matrislerin gerçek özdeğerleri ve ortogonal özvektörleri vardır (spektral teorem, genel bilgi). Bu, sayısal hesapta çok önemli bir kolaylıktır ve `np.linalg.eigh` fonksiyonunun neden `eig`'ten daha hızlı ve kararlı olduğunun sebebidir.

Özdeğerler sayısal olarak nasıl bulunur? Gerçek uygulamada karakteristik polinomun köklerini almak pratik değildir; bunun yerine **güç yinelemesi** (power iteration) gibi yinelemeli yöntemler kullanılır. Fikir şudur: rastgele bir `v` al, `A` ile çarp, normalize et, tekrarla. Bu süreç en büyük mutlak özdeğere karşılık gelen özvektöre yakınsar. Bu yönteme **Rayleigh bölümü** (`vᵀ A v / vᵀ v`) ile özdeğer de tahmin edilir. Aşağıdaki program güç yinelemesini kendi kodumuzla yazar, `eigh` ile karşılaştırır ve bir de PageRank'i bu yöntemle hesaplar.

PageRank, Bölüm 11'deki graf modelinin bir uygulamasıdır: sayfalar düğüm, bağlantılar kenar, ve bir sayfanın önemi, ona bağlanan sayfaların önemlerinin toplamı. Bu tanım, bir **sabit nokta** denklemine dönüşür ve sonuç, uygun bir matrisin özvektörüdür (`λ = 1`). Graf 4 düğümlü ve küçüktür; komşuluk matrisinin nasıl kurulacağı Bölüm 11.3'te gösterilmişti.

```python
# ozdeger.py: ozdeger, guc yinelemesi, PageRank, simetrik matris
import numpy as np


def guc_yineleme(A, iters=200, seed=42):
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(A.shape[0])
    v /= np.linalg.norm(v)
    for _ in range(iters):
        w = A @ v
        lam = v @ w                       # Rayleigh bolumu
        v = w / np.linalg.norm(w)
    return lam, v


A = np.array([[2.0, 1.0], [1.0, 2.0]])
lam, v = guc_yineleme(A)
print("guc yineleme: lambda =", round(lam, 10),
      " v =", np.round(v, 6))
vals, vecs = np.linalg.eigh(A)
print("eigh        : lambda =", vals, " vektorler (sutun):")
print(np.round(vecs, 6))
print("V^T V == I ?", np.allclose(vecs.T @ vecs, np.eye(2)))

# PageRank: 4 sayfa, A -> B, A -> C, B -> C, C -> A, D -> C
# G[i, j] = 1: j'den i'ye link
G = np.array([[0, 0, 1, 0],
              [1, 0, 0, 0],
              [1, 1, 0, 1],
              [0, 0, 0, 0]], dtype=float)
# sutun-stokastik M: M[i, j] = 1/outdeg(j) (i'ye giden link)
M = np.zeros((4, 4))
for j in range(4):
    if G[:, j].sum() > 0:
        M[:, j] = G[:, j] / G[:, j].sum()
d, n = 0.85, 4
Gg = d * M + (1 - d) / n * np.ones((4, 4))
x = np.full(n, 1 / n)
for _ in range(100):
    x = Gg @ x
print("PageRank (guc yineleme):", np.round(x, 4))
vals2, vecs2 = np.linalg.eig(Gg)
i = np.argmax(vals2.real)
pi = np.real(vecs2[:, i] / vecs2[:, i].sum())
print("PageRank (eig, lambda=1):", np.round(pi, 4))
```

```term
$ python ozdeger.py
guc yineleme: lambda = 3.0  v = [-0.707107 -0.707107]
eigh        : lambda = [1. 3.]  vektorler (sutun):
[[-0.707107  0.707107]
 [ 0.707107  0.707107]]
V^T V == I ? True
PageRank (guc yineleme): [0.3725 0.1958 0.3941 0.0375]
PageRank (eig, lambda=1): [0.3725 0.1958 0.3941 0.0375]
```

Çıktı üç sonuç gösterir. Güç yinelemesi `λ = 3.0` ve `v = (−0.707, −0.707)` verir; `eigh` aynı özdeğeri (dikkat, `eigh` özdeğerleri küçükten büyüğe sıralar, bu yüzden `[1, 3]` görünür) ve aynı yönü verir. Burada kullanılan `A = [[2, 1], [1, 2]]` matrisinin özdeğerleri `1` ve `3`tür; `λ = 3` için özvektör `(1, 1)/√2`'dir. Programın bulduğu `(−0.707, −0.707)` işaret olarak ters ama aynı yönü temsil eder. PageRank iki yöntemle aynı vektörü verir: `[0.3725, 0.1958, 0.3941, 0.0375]`. Bu toplam `1`'dir ve düğüm C'nin en yüksek önemi aldığını gösterir: A, B ve D'nin ona bağlanması bunu sağlar.

Özdeğerlerin bir diğer güçlü uygulaması **matris üssüdür**. `Aᵏ` hesaplamak, `A`'yı `k` kez çarpmak demektir; ama `A`'yı kendi özdeğerleriyle yazabilirsen `Aᵏ = V Λᵏ V⁻¹` olur ve `Λᵏ` yalnızca köşegen elemanların `k`'nci kuvvetini alır. Bunu Fibonacci sayıları ile gösterelim. `F = [[1, 1], [1, 0]]` matrisinin `Fⁿ`'nin `(0, 1)` elemanı `Fₙ`'dir. Bölüm 19.4'te bu sayıları `O(log n)` matris çarpımıyla hesaplamıştık. Burada ise özdeğerler `φ = (1 + √5)/2` ve `ψ = (1 − √5)/2` olur, ve `Fₙ = (φⁿ − ψⁿ)/√5` (Binet formülü) çıkar. Aşağıdaki program ikisini de doğrular ve aynı programda, bir **Markov zincirinin durağan dağılımını** özdeğer problemi olarak hesaplar; bu Bölüm 49'da olasılık tarafını göreceğin zincirin lineer cebir yüzüdür.

```python
# fib_mat.py: Fibonacci matrisi, kopegenleme, Markov dagilimi
import numpy as np

F = np.array([[1, 1], [1, 0]], dtype=np.int64)
print("F^10 =")
print(np.linalg.matrix_power(F, 10))        # [[F11 F10], [F10 F9]]

vals, V = np.linalg.eig(F.astype(float))
print("ozdegerler:", np.round(vals, 6))
print("(1+sqrt5)/2 =", round((1 + 5 ** 0.5) / 2, 6))


def fib_kop(n):
    # F^n = V diag(lambda^n) V^-1 ; F_n = (F^n)[0, 1]
    P = V @ np.diag(vals ** n) @ np.linalg.inv(V)
    return round(P[0, 1].real)


print("kosegenlestirme F_10 =", fib_kop(10), " F_30 =", fib_kop(30))
print("matris uslu F_30   =",
      np.linalg.matrix_power(F, 30)[0, 1])

# Markov zinciri: hava durumu (1: gunes, 2: yagmur)
# P[i, j]: i'den j'ye gecis olasiligi
P = np.array([[0.9, 0.1],
              [0.5, 0.5]])
# pi P = pi  <=>  P^T pi^T = pi^T
vals_p, vecs_p = np.linalg.eig(P.T)
k = np.argmin(np.abs(vals_p - 1))
pi = np.real(vecs_p[:, k] / vecs_p[:, k].sum())
print("durağan dagilim pi =", np.round(pi, 6))
dist = np.array([1.0, 0.0])
for _ in range(50):
    dist = dist @ P
print("50 adim sonra     =", np.round(dist, 6))
```

```term
$ python fib_mat.py
F^10 =
[[89 55]
 [55 34]]
ozdegerler: [ 1.618034 -0.618034]
(1+sqrt5)/2 = 1.618034
kosegenlestirme F_10 = 55  F_30 = 832040
matris uslu F_30   = 832040
durağan dagilim pi = [0.833333 0.166667]
50 adim sonra     = [0.833333 0.166667]
```

Çıktı, `F¹⁰`'un `[[89, 55], [55, 34]]` olduğunu gösterir (`F₁₀ = 55`). Köşegenleştirme yöntemi `F₃₀ = 832040` verir ve bu matris üssünün sonucuyla aynıdır. Markov tarafında, hava durumu zincirinin durağan dağılımı `(5/6, 1/6)`dır (yani zamanın yaklaşık `%83`'ünde güneşli). Elle kontrol: `π = (5/6, 1/6)` için `π P = (5/6 · 0.9 + 1/6 · 0.5, 5/6 · 0.1 + 1/6 · 0.5) = (5/6, 1/6)`. Bu, Bölüm 49'da olasılık zincirinin özelliklerini inceleyeceğimiz durumun doğrudan bir örneğidir.


## 48.13 SVD: her matrisin döndür–ölçekle–döndür yapısı

Özdeğer ayrışımı yalnızca kare ve simetrik (ya da en azından köşegenleştirilebilir) matrisler için temiz çalışır. Gerçek veriler ise çoğu zaman dikdörtgendir: bir ölçüm tablosu `m` örnek ve `n` özellik içerir, `m ≠ n`. **Tekil değer ayrışımı** (singular value decomposition, SVD) her gerçek `m × n` matrisi için çalışır:

A = U Σ Vᵀ

Burada `U` (`m × m`) ve `V` (`n × n`) ortogonal matrislerdir (sütunları ortonormal), `Σ` ise köşegeninde negatif olmayan `σ₁ ≥ σ₂ ≥ ... ≥ 0` sayıları bulunan bir `m × n` köşegen matristir. Bu sayılara **tekil değer** denir. Geometrik yorum bir cümleyle söylenebilir: her lineer dönüşüm, bir **dönme**, bir **eksen boyunca ölçekleme** ve bir **dönmenin** bileşimidir. Şekil 48.6 bu üç adımı birim çember üzerinde gösterir.

Şekil 48.6'da kullanılan matris `A = [[2, 1], [0, 1.5]]`'tir. (a) panelinde birim çember vardır. (b) panelinde `Vᵀ` uygulanır; çember yalnızca döner, şekli değişmez. (c) panelinde `Σ` uygulanır; çember, eksenleri `σ₁ = 2.379` ve `σ₂ = 1.261` olan bir elipse dönüşür. (d) panelinde `U` uygulanır ve sonuç `A` ile birim çemberin görüntüsü olan elipstir. Elipsin ana eksenleri `σᵢ uᵢ` vektörleridir.

![Şekil 48.6: Birim çemberin SVD ile dönüşümü. (a) birim çember. (b) Vᵀ dönmesi. (c) Σ ölçeklemesi: eksenlerde σ1 = 2.379, σ2 = 1.261. (d) U dönmesi: sonuç A'nın elipsidir, eksenler σᵢuᵢ vektörleridir.](gorseller/b48_svd_elips.png)

SVD'nin en güçlü uygulaması **düşük rank yaklaşımıdır**. Eğer tekil değerlerin çoğu küçükse, matrisi ilk `k` tekil değerle yazmak büyük ölçüde bilgiyi korur. `A_k = Σᵢ≤ₖ σᵢ uᵢ vᵢᵀ` tanımlarsak, **Eckart–Young teoremi** (genel bilgi, kanıtı bu bölümde yok) `A_k`'nın, rank'ı en fazla `k` olan tüm matrisler arasında `A`'ya en yakın olduğunu söyler. Bu yakınlık, spektral normda `‖A − A_k‖₂ = σ_{k+1}` ve Frobenius normda `‖A − A_k‖_F = √(Σ_{i>k} σᵢ²)` ile ölçülür.

Bu yaklaşımın depolama maliyeti de açıktır. `A_k` yerine `U_k` (`m × k`), `σ` (`k` sayı) ve `V_kᵀ` (`k × n`) saklarsan `k(m + n + 1)` sayı tutarsın. Orijinal `mn` sayıya göre oranı `k(m + n + 1) / (mn)`'dir. Bu oran `k` küçük olduğunda çok küçük, `k` büyüdüğünde ise 1'i geçebilir: `k(m + n + 1) > mn` ise sıkıştırma kazanç değil kayıptır.

Bunu bir görüntü üzerinde deneyelim. Gerçek bir fotoğraf yerine kontrollü bir sentetik gri görüntü kullanıyoruz: 128 × 128 piksel, bir yumuşak eğim, bir daire, bir sinüs şeritleri ve küçük bir gürültü. Gerçek fotoğrafların tekil değerlerinin daha yavaş düştüğü ve bu yüzden aynı `k` ile daha büyük hata verdiği beklenir (genel bilgi; bu bölümde gerçek fotoğrafla ölçmedik). Program, `k = 1, 2, 4, ..., 64` için bağıl hatayı (`‖A − A_k‖_F / ‖A‖_F`), Eckart–Young'ın `σ_{k+1}` değerini ve oranı hesaplar. Ayrıca bir sözde ters (pseudo-inverse) doğrulaması yapar.

```python
# svd_gorsel.py: SVD ile rank-k goruntu yaklasimi ve sikistirma orani
import csv
import sys
import numpy as np


def sentetik_gorsel(n=128, seed=42):
    # yumusak degisim + daire + cizgiler + hafif gurultu (0..1)
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:n, 0:n] / n
    g = 0.5 * x + 0.3 * y
    g += 0.4 * (((x - 0.6) ** 2 + (y - 0.4) ** 2) < 0.06)
    g += 0.2 * np.sin(18 * np.pi * x) * (y > 0.7)
    g += 0.02 * rng.standard_normal((n, n))
    return np.clip(g, 0.0, 1.0)


def rank_k(A, k):
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    return (U[:, :k] * s[:k]) @ Vt[:k]


def sikistirma_orani(m, n, k):
    # U: m x k, s: k, V^T: k x n  ->  k (m + n + 1) sayi
    return k * (m + n + 1) / (m * n)


```

Yukarıdaki kodun ilk yarısı görüntüyü üretir ve tekil değer ayrışımına hazırlanır. Şimdi programın geri kalan yarısını okuyalım: `rank_k` fonksiyonu SVD'yi bir kez hesaplar ve ilk `k` terimle yeniden kurar.

```python
A = sentetik_gorsel()
m, n = A.shape
s = np.linalg.svd(A, compute_uv=False)
print("tekil degerler: s1=%.3f s2=%.3f s128=%.2e"
      % (s[0], s[1], s[-1]))
print(" k   bagil_hata   s_(k+1)   oran(%)")
satirlar = []
for k in [1, 2, 4, 8, 16, 32, 64]:
    Ak = rank_k(A, k)
    hata = np.linalg.norm(A - Ak) / np.linalg.norm(A)
    oran = 100 * sikistirma_orani(m, n, k)
    sigma = s[k]                     # Eckart-Young: s_{k+1}
    print("%3d   %10.4f   %12.4e   %7.2f"
          % (k, hata, sigma, oran))
    satirlar.append((k, hata, oran))
if len(sys.argv) > 1:                # csv'yi kitap sekilleri icin yaz
    with open(sys.argv[1], "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["k", "bagil_hata", "oran_yuzde"])
        for k, h, o in satirlar:
            w.writerow([k, "%.6f" % h, "%.4f" % o])
print("pinv testi (lstsq ile):",
      np.allclose(np.linalg.pinv(A),
                  np.linalg.lstsq(A, np.eye(m), rcond=None)[0]))
```

```term
$ python svd_gorsel.py
tekil degerler: s1=66.624 s2=11.924 s128=1.75e-03
 k   bagil_hata   s_(k+1)   oran(%)
  1       0.2187     1.1924e+01      1.57
  2       0.1316     5.2300e+00      3.14
  4       0.0862     2.8149e+00      6.27
  8       0.0572     1.3506e+00     12.55
 16       0.0414     6.4254e-01     25.10
 32       0.0288     3.9302e-01     50.20
 64       0.0143     2.1869e-01    100.39
pinv testi (lstsq ile): True
```

Çıktıda `s_(k+1)` sütunu Eckart–Young'ın `‖A − A_k‖₂` değerini verir; bağıl hata sütununda ise Frobenius normu kullanılır. Tablo iki önemli gerçek gösterir. Birincisi, `k = 16` değerinde görüntünün yalnızca `%25`'i depolanır ve bağıl hata `0.041` olur; hata görsel olarak fark edilmeyecek kadar küçük değildir ama nesneler tanınabilir kalır (Şekil 48.7). İkincisi, `k = 64` değerinde oran `%100.39` olur: yaklaşım orijinalden biraz daha fazla yer kaplar. Bu, `k(m + n + 1) > mn` koşulunun tam olarak sınırda olduğu noktadır.

Şekil 48.7 bu yaklaşımları görsel olarak gösterir. `k = 2` ile yalnızca genel yapı kalır; şeritler bulanıklaşır ve daire yumuşar. `k = 8`'de daire belirginleşir ama kenarlarda halkalar oluşur. `k = 16`'da görüntü neredeyse orijinaldir.

![Şekil 48.7: Sentetik görüntü ve k = 2, 8, 16 ile rank-k yaklaşımları. Bağıl hata her panelin başlığında yazılı. Düşük rank yapıyı korur, ince ayrıntıyı ilk kaybeden kısımdır.](gorseller/b48_rankk_gorsel.png)

Şekil 48.8 bu ölçümleri `k`'ya karşı çizer: sol panelde hata düşer, sağ panelde oran yükselir. İki eğri birbirinin tersidir ve gerçek mühendislik kararı bu iki eğrinin kesiştiği yerdedir. Bu takas, veri sıkıştırma, telemetri iletimi ve model ağırlıklarını küçültme (Bölüm 46'daki kuantizasyonun bir benzeri) için aynıdır.

![Şekil 48.8: Bağıl hata (sol) ve depolama oranı (sağ) k'ya göre. Veri engine/veri/b48_svd.csv dosyasından okunur. Sağ panelde %100 çizgisinin üstü orijinalden daha büyük depolamayı gösterir.](gorseller/b48_rankk_hata.png)

Sözde ters (pseudo-inverse) `A⁺` her dikdörtgen matris için tanımlıdır ve SVD ile yazılır: `A⁺ = V Σ⁺ Uᵀ`. Burada `Σ⁺`, `Σ`'nın sıfır olmayan elemanlarının tersidir. `A` tam rank'lıysa `A⁺ b` en küçük kareler çözümünü verir; tekilse en küçük normlu çözümü verir. Programın son satırı bunu NumPy'nin `lstsq` ile hesaplanan değerine karşı doğrular (`pinv testi (lstsq ile): True`).

SVD'nin iki modern ML uygulaması, bu bölümün son büyük fikridir. **PCA** (temel bileşen analizi) merkezlenmiş veri matrisi `X`'in SVD'sidir: `X = U Σ Vᵀ`. `V`'nin sütunları veri yayılımının ana yönleridir, `σᵢ²/(n−1)` ise o yöndeki varyansıdır. Bu bağlantının olasılık ve istatistik yüzü, kovaryans matrisinin özdeğerleridir ve Bölüm 49 ile Bölüm 61'de ayrıntılandırılacak; burada lineer cebir tarafını gördük. **LoRA** (Bölüm 70) ise büyük bir dil modelinin ağırlık matrisi `W`'yi `W + B A` olarak değiştirir; `B` (`d × r`) ve `A` (`r × d`) ile `r` küçüktür. Burada `d = 4096` ve `r = 8` için eğitilecek parametre sayısı `2dr = 65.536`dır; tam matrisin `d² = 16.777.216` parametresine kıyasla yaklaşık `1/256`'dır. Bu, düşük rank varsayımının ML'de neden bu kadar işe yaradığının sayısal özetidir.

## 48.14 Hesaplama: BLAS, LAPACK, bellek düzeni ve yayınlama

Şimdiye kadar yazdığımız `A @ B` ya da `np.linalg.solve` gibi ifadelerin arkasında kendi kodumuzdan çok daha olgun kütüphaneler çalışır. Bunların katmanları iyi tanımlanmıştır. **BLAS** (Basic Linear Algebra Subprograms) temel vektör ve matris işlemlerinin bir arayüzüdür: düzey 1 vektör-vektör (`axpy`), düzey 2 matris-vektör (`gemv`), düzey 3 matris-matris (`gemm`) işlemleri. **LAPACK** ise bunun üzerine kurulan, `solve`, `eig`, `svd`, `qr` gibi üst düzey algoritmalardır. NumPy bu kütüphanelerin üzerinde ince bir Python katmanıdır.

Bu katmanlar bizim kurulumumuzda şu şekildedir. Aşağıdaki program NumPy'nin derleme yapılandırmasından BLAS ve LAPACK adlarını okur.

```python
# blas_bilgi.py: NumPy'nin altindaki BLAS/LAPACK kutuphanesini oku
import numpy as np

yapi = np.show_config(mode="dicts")
bagli = yapi["Build Dependencies"]
for ad in ["blas", "lapack"]:
    print(ad, "->", bagli[ad]["name"], bagli[ad]["version"])
print("numpy", np.__version__)
```

```term
$ python blas_bilgi.py
blas -> scipy-openblas 0.3.30
lapack -> scipy-openblas 0.3.30
numpy 2.3.5
```

Çıktı, bu NumPy kurulumunun BLAS ve LAPACK'i olarak SciPy'nin paketlediği OpenBLAS 0.3.30 kullandığını gösterir. Yapılandırma çıktısında OpenBLAS'ın `MAX_THREADS=24` ayarıyla çok iş parçacıklı çalışabildiği de görülür. Başka bir dağıtımda (Intel MKL gibi) ad farklı olur, ama mimari aynıdır.

Matris çarpımının hızını anlamak için, saf Python'da üç döngülü bir çarpım ile NumPy'nin `@` işlecini karşılaştıralım. Python döngüsü her çarpma ve toplamayı ayrı bir nesne işlemi olarak yapar; Bölüm 3'te gördüğümüz kutu ve dolaylılık maliyeti her adımda ödenir. NumPy ise tüm çarpımı derlenmiş BLAS çekirdeğine verir; bu çekirdek önbellek dostu blok sırasını, SIMD komutlarını (Bölüm 24.8) ve iş parçacığı paralelliğini kullanır. Önbellek etkisini Bölüm 25.7'de ölçtük (blok çarpım, sıralı çarpımdan 18–19 kat hızlıydı); burada o ölçümü tekrarlamıyoruz, yalnızca farkın büyüklüğünü görüyoruz.

```python
# matmul_hiz.py: saf Python ucgen dongu ile NumPy matmul hiz olcumu
import csv
import sys
import time
import numpy as np


def saf_carpim(A, B):
    n = len(A)
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            s = 0.0
            for k in range(n):
                s += A[i][k] * B[k][j]
            C[i][j] = s
    return C


def en_iyi(f, tekrar):
    zamanlar = []
    for _ in range(tekrar):
        t0 = time.perf_counter()
        f()
        zamanlar.append(time.perf_counter() - t0)
    return min(zamanlar)


rng = np.random.default_rng(42)
satirlar = []
print("   n   python_ms   numpy_us     oran")
for n in [16, 32, 64, 128, 256]:
    A = rng.standard_normal((n, n))
    B = rng.standard_normal((n, n))
    Al, Bl = A.tolist(), B.tolist()
    tp = en_iyi(lambda: saf_carpim(Al, Bl), 1 if n >= 128 else 3)
    tn = en_iyi(lambda: A @ B, 20)
    assert np.allclose(np.array(saf_carpim(Al, Bl)), A @ B)
    print("%4d  %9.3f  %10.2f  %8.0f"
          % (n, tp * 1e3, tn * 1e6, tp / tn))
    satirlar.append((n, tp, tn))
if len(sys.argv) > 1:
    with open(sys.argv[1], "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "python_s", "numpy_s"])
        for n, tp, tn in satirlar:
            w.writerow([n, "%.8f" % tp, "%.8f" % tn])
```

```term
$ python matmul_hiz.py
   n   python_ms   numpy_us     oran
  16      0.222        1.40       159
  32      1.519        2.90       524
  64     11.999       11.30      1062
 128     98.984       67.40      1469
 256    752.218      179.10      4200
```

Çıktı, iki yaklaşım arasında binlerce kat fark olduğunu gösterir. Saf Python süresi `n` 16'dan 256'ya çıkarken yaklaşık `3.4 · 10³` kat (`0.222 ms`'den `752.2 ms`'ye) artar; bu, `n³` (`16³ → 256³`, yani `4096` kat) büyümesine yakındır. Şekil 48.9 aynı veriyi log-log eksende çizer; Bölüm 12.10'da öğrendiğin eğim okuması burada doğrudan geçerlidir: Python eğrisinin eğimi yaklaşık `3`, yani kübik büyüme. NumPy eğrisi de kübik büyür ama katsayısı çok daha küçüktür.

Şekil 48.9 bu ölçümü log-log eksende gösterir. Eğrilerin paralelliğine dikkat et: iki çizgi de benzer bir eğime sahiptir, ama aralarındaki açıklık `159×` ile `4200×` arasında değişir. Bu, sabit çarpanın (katsayının) farkını gösterir, büyüme derecesinin değil.

![Şekil 48.9: Matris çarpımı süresi (n × n, log-log). Saf Python ile NumPy arasındaki oran her noktada yazılı. Eğrilerin eğimi benzer, yani her ikisi de n³ ile büyür; fark sabit çarpandadır. Veri engine/veri/b48_matmul.csv dosyasından okunur.](gorseller/b48_matmul_hiz.png)

Algoritma düzeyinde de iki fikir var. Strassen (Bölüm 19.6) 2×2 blok bölmesiyle çarpım sayısını `8`'den `7`'ye indirir ve `n^2.807` karmaşıklığa ulaşır; ama sabitleri büyük olduğu için pratikte yalnızca büyük matrislerde ve bir eşikle kullanılır, BLAS çoğu zaman kullanmaz (genel bilgi). Bölüm 19.11'deki FFT ise konvolüsyonu `n log n` ile yapar. Bölüm 46'daki tamsayı çekirdeğinde (int8 GEMM) çarpımın yapısı aynıdır; yalnızca sayı türü ve birikim kaydı değişir.

**Bellek düzeni** (memory layout) ikinci büyük etkendir. NumPy dizileri varsayılan olarak **satır öncelikli** (C düzeni) tutulur: bir satırın elemanları bellekte yan yana durur. Fortran düzeni ise sütun önceliklidir. Aynı sayılar, hangi yönde tarandığına göre farklı hızda okunur. Aşağıdaki program aynı `2000 × 2000` matrisi iki düzende de satır ve sütun boyunca tarar.

```python
# duzen.py: bellek duzeni, yayinlama (broadcasting) ve einsum
import time
import numpy as np

n = 2000
A = np.random.default_rng(42).standard_normal((n, n))   # C duzeni
# Fortran duzeni (sutun oncelikli)
F = np.asfortranarray(A)


def satir_tara(M):
    s = 0.0
    for i in range(n):
        s += M[i, :].sum()          # bitisik bellek
    return s


def sutun_tara(M):
    s = 0.0
    for j in range(n):
        s += M[:, j].sum()          # adim = n * 8 bayt
    return s


def olc(f, M):
    en_kisa = float("inf")
    for _ in range(5):
        t0 = time.perf_counter()
        f(M)
        en_kisa = min(en_kisa, time.perf_counter() - t0)
    return en_kisa


print("C duzeni    satir: %.4f s  sutun: %.4f s"
      % (olc(satir_tara, A), olc(sutun_tara, A)))
print("F duzeni    satir: %.4f s  sutun: %.4f s"
      % (olc(satir_tara, F), olc(sutun_tara, F)))

a = np.arange(3)
b = np.arange(3).reshape(3, 1)
print("a + b (3,)+(3,1) ->", (a + b).shape)
print(a + b)

X = np.array([[1.0, 2.0, 3.0],
              [4.0, 5.0, 9.0],
              [7.0, 8.0, 1.0]])
dogru = X - X.mean(axis=0)          # sutun ortalamasi
yanlis = X - X.mean(axis=1)         # satir ortalamasi, yanlis eksen
print("dogru: sutun ort. sifir ?", np.allclose(dogru.mean(axis=0), 0))
print("yanlis: sutun ort. sifir ?",
      np.allclose(yanlis.mean(axis=0), 0))

B = np.arange(6.0).reshape(2, 3)
C = np.arange(12.0).reshape(3, 4)
print("einsum == @ ?",
      np.allclose(np.einsum("ik,kj->ij", B, C), B @ C))
u = np.array([1.0, 2.0, 3.0])
v = np.array([10.0, 20.0])
print("dis carpim (einsum):")
print(np.einsum("i,j->ij", u, v))
# (batch, kanal, yukseklik, genislik)
batch = np.zeros((8, 3, 32, 32))
print("tensor sekli:", batch.shape, " eleman:", batch.size)
print("ortalama kanal basina:", batch.mean(axis=(0, 2, 3)).shape)
```

```term
$ python duzen.py
C duzeni    satir: 0.0069 s  sutun: 0.0098 s
F duzeni    satir: 0.0098 s  sutun: 0.0069 s
a + b (3,)+(3,1) -> (3, 3)
[[0 1 2]
 [1 2 3]
 [2 3 4]]
dogru: sutun ort. sifir ? True
yanlis: sutun ort. sifir ? False
einsum == @ ? True
dis carpim (einsum):
[[10. 20.]
 [20. 40.]
 [30. 60.]]
tensor sekli: (8, 3, 32, 32)  eleman: 24576
ortalama kanal basina: (3,)
```

Çıktı düzenin etkisini gösterir: C düzeninde satır taraması `0.0069 s`, sütun taraması `0.0098 s` sürer; Fortran düzeninde durum tersine döner (`0.0098 s` ve `0.0069 s`). Yani hangi taramanın hızlı olduğu, verinin bellekte hangi düzende durduğuna bağlıdır. Bu fark bu basit toplamalarda orta ölçüde kalır; yoğun döngülerde ve matris çarpımında çok daha büyük olabilir. Bu bölümün bağlantısı, Bölüm 25'teki önbellek satırlarının neden bitişik bellekte yan yana okumayı ödüllendirdiğini hatırlamaktır.

Aynı programın ikinci yarısı **yayınlama** (broadcasting) kurallarını gösterir. İki dizinin şekilleri sağdan sola karşılaştırılır; her boyut için ya eşit olmalı ya da biri 1 olmalıdır. `(3,)` boyutlu `a` ile `(3, 1)` boyutlu `b` toplanınca `(3, 3)` sonucu çıkar: `a` her satıra kopyalanır, `b` her sütuna kopyalanır. Bu kolaylık büyük bir tuzağı da gizler: `X` `3 × 3` ise `X − X.mean(axis=1)` bir hata vermez; yalnızca yanlış eksende ortalama çıkarır. Çıktıdaki `yanlis: sutun ort. sifir ? False` satırı bunun sessiz bir hata olduğunu gösterir. Kural: broadcasting yapmadan önce ortalamanın hangi eksende alındığını şekille doğrula.

Son olarak `einsum` (Einstein toplama gösterimi) ile çok boyutlu tensörler. `np.einsum("ik,kj->ij", B, C)` tekrarlanan indeks `k` üzerinden toplar ve matris çarpımına eşittir. `einsum("i,j->ij", u, v)` ise dış çarpımdır; hiçbir indeks toplanmaz. Bir batch görüntü tensörü `(batch, kanal, yükseklik, genişlik)` dört boyutludur; `batch.mean(axis=(0, 2, 3))` her kanal için ayrı bir ortalama verir. ML kodunda bu şekil sözleşmesi (shape contract) her katmanda değişir, bu yüzden tensör şeklini düşünmek bir alışkanlık hâline gelmelidir. Bölüm 65'te PyTorch'ta aynı düşünceyi kullanacaksın.

## 48.15 ML'de lineer cebir haritası

Bu bölümde öğrendiğimiz araçların ML'de nerede durduğunu tek bir haritada toplayalım. Şekil 48.10 ana kavramları ve kitabın hangi bölümünde derinleştiklerini gösterir. Harita bir sinir ağının ileri geçişinden başlar ve oradan dikkat, gömme, PCA ve düşük rank gibi kavramlara dallanır.

![Şekil 48.10: ML'de lineer cebir haritası. Üst satır: bir katmanın veri akışı (afin dönüşüm, doğrusal olmayan fonksiyon). Orta ve alt satır: dikkat, gömme, PCA, LoRA, gradyan ve en küçük kareler. Parantez içindeki bölüm numaraları ilgili derinleştirmeyi gösterir.](gorseller/b48_ml_harita.png)

Haritanın okunması şöyledir. Bir sinir ağı katmanı `σ(XW + b)` biçimindedir: girdi matrisi `X` (örnek × özellik) bir ağırlık matrisi `W` ile çarpılır, bir sapma `b` eklenir ve doğrusal olmayan bir `σ` uygulanır (Bölüm 63). Bu yapının bütün ağırlık öğrenimi, kayıp fonksiyonunun türevlerini zincir kuralıyla bir matris çarpımlarına dönüştürmekle yapılır; bunun bütün ayrıntısını Bölüm 55'te Jacobian ile göreceksin. **Dikkat** mekanizması `softmax(QKᵀ / √d) V` formülüyle iki matris çarpımını birleştirir ve Bölüm 69'da satır satır kurulacak. **Gömme** tablosu, bir kelimenin indeksini bir one-hot vektörle çarpmanın hızlı bir yoludur; yani aslında bir satır seçimidir (Bölüm 70). Kosinüs benzerliği, bu gömmelerin yakınlığını ölçer (48.2). **PCA** (Bölüm 61), SVD ile hesaplanır (48.13). **LoRA** düşük rank güncellemesidir (Bölüm 70). En küçük kareler, regresyonun QR ya da SVD ile çözümüdür (Bölüm 58 ve 48.11).

Bu haritanın bir sonucu şudur: ML'de yazdığın kodun büyük kısmı tensör ve matris işlemleridir. Bir şeyin neden yavaş ya da neden hatalı olduğunu anlamak için şekilleri (shape), bellek düzenini ve yapılan işlemin lineer cebirdeki karşılığını bilmek gerekir. Bu bölüm bu üç soruyu cevaplamak için gereken temeli verdi.


## Çözümlü Örnekler

Bu bölümdeki dört örnek ★ zorluğundan ★★★'e doğru ilerler. Her örnekte Bölüm 5'teki altı adımı izleyeceğiz. Adım 6'da elle iz sürme tablosu olacak; tablodaki değerler örnekte verilen programın çıktısıyla aynıdır. Programı çalıştırmadan önce her örneğin ilk üç adımını kâğıtta dene.

### Örnek 1 (★): Birim karenin bileşik dönüşümü

**Problem:** Birim kare (köşeleri `(0,0)`, `(1,0)`, `(1,1)`, `(0,1)`) önce 90 derece döndürülüyor, sonra `K = [[1, 1], [0, 1]]` kayma matrisiyle dönüştürülüyor. Dönüşümün tek matrisini bul ve köşelerin son konumunu hesapla.

**Adım 1 — Anla.** Girdi bir kare ve iki dönüşümdür; çıktı bir matris ile dört köşe noktasıdır. Sıra önemlidir: önce `R`, sonra `K`. Bu, bileşik matrisin `M = K · R` olacağı anlamına gelir (48.5).

**Adım 2 — Örnekle.** Köşe `(1, 0)`'ı izleyelim. `R` bu noktayı `(0, 1)`'e götürür (`R`'nin birinci sütunu). Sonra `K` `(0, 1)`'i `(1, 1)`'e götürür (`K(x, y) = (x + y, y)`).

**Adım 3 — Kaba çöz.** Her köşeyi sırayla iki dönüşümden geçir. Bu, dört noktada iki matris-vektör çarpımıdır; tek bir `M` matrisini bir kez kurup dört noktaya uygulamak daha az iştir.

**Adım 4 — Örüntü.** Bileşik matrisi `K · R` olarak kur. `K · R`'nin birinci sütunu `K (R e₁) = K e₂` ve ikinci sütunu `K (R e₂) = K (−e₁) = −K e₁`'dir. Yani `M`'nin sütunları `K`'nin sütunlarından gelir; hesabı sütunlar üzerinden yapabilirsin.

**Adım 5 — İyileştir.** Matrisi bir kez kur, sonra köşe matrisini tek bir çarpımla dönüştür. Determinant `det(M) = det(K) det(R) = 1 · 1 = 1` olur; alan korunur ve yönelim değişmez. Bu kontrolü programda yapıyoruz.

Bu matrisi elle yazmak için `K · R`'nin sütunlarını hesaplayalım: `M = [[1, −1], [1, 0]]`.

**Adım 6 — Doğrula.** Aşağıdaki iz tablosu her köşeyi adım adım izler. Sütunlar: başlangıç, `R` sonrası, `K` sonrası (`= M` ile tek çarpım).

| Köşe | Başlangıç | R sonrası | K sonrası (= M·köşe) |
|---|---|---|---|
| A | (0, 0) | (0, 0) | (0, 0) |
| B | (1, 0) | (0, 1) | (1, 1) |
| C | (1, 1) | (−1, 1) | (0, 1) |
| D | (0, 1) | (−1, 0) | (−1, 0) |

Son sütun, `M = [[1, −1], [1, 0]]` matrisinin her köşeye uygulanmasıyla da aynıdır: `M (1, 1) = (1 − 1, 1 + 0) = (0, 1)`. Aşağıdaki programı çalıştır; `M @ kose == K @ (R @ kose)` ve rastgele 100 nokta için de eşitlik `True` çıkmalıdır.

```python
# ornek1.py: birim karenin bilesik donusumu (once R, sonra K)
import numpy as np

R = np.array([[0, -1], [1, 0]])     # 90 derece dondurme
K = np.array([[1, 1], [0, 1]])      # kayma
M = K @ R                           # once R, sonra K

kose = np.array([[0, 1, 1, 0],      # (0,0) (1,0) (1,1) (0,1)
                 [0, 0, 1, 1]])
print("M = K @ R =")
print(M)
print("det(M) =", round(np.linalg.det(M), 6))
adim1 = R @ kose
adim2 = K @ adim1
print("adim 1 (R)   x:", adim1[0], " y:", adim1[1])
print("adim 2 (K)   x:", adim2[0], " y:", adim2[1])
print("M @ kose == K @ (R @ kose):", np.array_equal(M @ kose, adim2))
rng = np.random.default_rng(42)
P = rng.integers(-5, 6, size=(2, 100))
print("100 rastgele nokta:", np.array_equal(M @ P, K @ (R @ P)))
```

```term
$ python ornek1.py
M = K @ R =
[[ 1 -1]
 [ 1  0]]
det(M) = 1.0
adim 1 (R)   x: [ 0  0 -1 -1]  y: [0 1 1 0]
adim 2 (K)   x: [ 0  1  0 -1]  y: [0 1 1 0]
M @ kose == K @ (R @ kose): True
100 rastgele nokta: True
```

**Bunu AI'sız yazabilir misin?** Ölçekleme `S = [[2, 0], [0, 1]]`, 90 derece döndürme `R` ve x eksenine göre yansıma `Y = [[1, 0], [0, −1]]` için üç dönüşümün bileşik matrisini (önce `S`, sonra `R`, sonra `Y`) kâğıtta kur. Determinantını hesapla ve birim karenin dört köşesinin son konumunu tabloyla göster.

### Örnek 2 (★★): Kısmi pivotlu Gauss ile 3×3 sistem, adım adım

**Problem:** `2x + y − z = 8`, `−3x − y + 2z = −11`, `−2x + y + 2z = −3` sistemini kısmi pivotlu Gauss eliminasyonuyla çöz. Ayrıca determinantı pivotlardan hesapla.

**Adım 1 — Anla.** Üç bilinmeyenli, üç denklemli bir sistem. Çıktı `x, y, z` değerleri ve determinanttır. Matris `A` tam rank'lı olmalı; yoksa tek çözüm yoktur.

**Adım 2 — Örnekle.** Sistemi artırılmış matris `[A | b]` olarak yaz. İlk sütunda mutlak değeri en büyük eleman `−3`'tür (ikinci satır); pivot olarak bunu kullanacağız.

**Adım 3 — Kaba çöz.** Pivotsuz eleme bu örnekte de sonuç verir (ilk pivot `2`, çarpanlar `−1.5` ve `−1`). Asıl sorun ilk pivotun küçük olduğu sistemlerde ortaya çıkar (48.7'deki `ε` örneği). Büyük pivotu seçmek, bu kötü durumu baştan engelleyen bir alışkanlıktır.

**Adım 4 — Örüntü.** Her `k` için: en büyük pivotu seç, satırı takas et, altındaki satırlardan `aᵢₖ / pivot` katını çıkar. Bu, ileri eleme döngüsüdür. Sonunda üst üçgen bir sistem kalır; geri yerine koyma ile çözülür.

**Adım 5 — İyileştir.** Takasları ve çarpanları kaydet; determinant için `(−1)^takas · Π pivotlar` kullanılır. Eleme sonunda köşegen `−3`, `1.667`, `0.2` olur; takas sayısı 2 olduğu için `det(A) = (+1) · (−3)(1.667)(0.2) = −1`'dir.

**Adım 6 — Doğrula.** Her adımdaki matrisi tabloda tut ve çözümü `A x = b` ile kontrol et.

| Adım | İşlem | Matris [A; b] |
|---|---|---|
| 0 | başlangıç | [2, 1, −1; 8], [−3, −1, 2; −11], [−2, 1, 2; −3] |
| 1 | satır 1 ↔ 2 (pivot −3), k=1 eleme | [−3, −1, 2; −11], [0, 0.333, 0.333; 0.667], [0, 1.667, 0.667; 4.333] |
| 2 | satır 2 ↔ 3 (pivot 1.667), k=2 eleme | [−3, −1, 2; −11], [0, 1.667, 0.667; 4.333], [0, 0, 0.2; −0.2] |
| 3 | geri yerine koyma | z = −1, y = 3, x = 2 |

Kontrol: `2·2 + 3 − (−1) = 8` ✓, `−3·2 − 3 + 2·(−1) = −11` ✓, `−2·2 + 3 + 2·(−1) = −3` ✓. Aşağıdaki program aynı adımları yazdırır ve numpy ile karşılaştırır.

```python
# ornek2.py: 3x3 sistem, kismi pivotlu Gauss, adim adim
import numpy as np

A = np.array([[2.0, 1.0, -1.0],
              [-3.0, -1.0, 2.0],
              [-2.0, 1.0, 2.0]])
b = np.array([8.0, -11.0, -3.0])
n = 3
M = np.hstack([A, b[:, None]])          # artirilmis matris [A | b]


def goster(baslik):
    print(baslik)
    for satir in M:
        print("  ", "  ".join("%7.3f" % x for x in satir))


goster("baslangic [A | b]:")
for k in range(n - 1):
    p = k + int(np.argmax(np.abs(M[k:, k])))
    if p != k:
        M[[k, p]] = M[[p, k]]
        print("satir %d <-> %d (pivot %.3f)"
              % (k + 1, p + 1, M[k, k]))
    for i in range(k + 1, n):
        m = M[i, k] / M[k, k]
        M[i, k:] -= m * M[k, k:]
    goster("k=%d sonrasi:" % (k + 1))
x = np.zeros(n)
for i in range(n - 1, -1, -1):
    x[i] = (M[i, -1] - M[i, i + 1:n] @ x[i + 1:]) / M[i, i]
print("x =", np.round(x, 6))
print("numpy =", np.round(np.linalg.solve(A, b), 6))
```

```term
$ python ornek2.py
baslangic [A | b]:
     2.000    1.000   -1.000    8.000
    -3.000   -1.000    2.000  -11.000
    -2.000    1.000    2.000   -3.000
satir 1 <-> 2 (pivot -3.000)
k=1 sonrasi:
    -3.000   -1.000    2.000  -11.000
     0.000    0.333    0.333    0.667
     0.000    1.667    0.667    4.333
satir 2 <-> 3 (pivot 1.667)
k=2 sonrasi:
    -3.000   -1.000    2.000  -11.000
     0.000    1.667    0.667    4.333
     0.000    0.000    0.200   -0.200
x = [ 2.  3. -1.]
numpy = [ 2.  3. -1.]
```

**Bunu AI'sız yazabilir misin?** Aynı yöntemle `x + 2y = 5`, `3x + 6y = 15` (tekil) sistemini dene. Hangi adımda bir pivot sıfır çıkar, bu durum neyi gösterir ve çözüm kümesi tek nokta mı, boş mu, sonsuz mu?

### Örnek 3 (★★): Simetrik 2×2 matris: özdeğer, özvektör, köşegenleştirme

**Problem:** `A = [[3, 1], [1, 3]]` matrisinin özdeğerlerini ve özvektörlerini elle bul; `A = V Λ Vᵀ` yazıp `A⁵`'i köşegenleştirme ile hesapla.

**Adım 1 — Anla.** Girdi simetrik bir 2×2 matristir. Çıktı iki özdeğer, iki dik özvektör ve `A⁵`'tir.

**Adım 2 — Örnekle.** `A v = λ v` için `v = (1, 1)` dener, `A v = (4, 4) = 4 v` olduğunu görürüz. Demek `λ = 4` ve `(1, 1)` özdeğer ve özvektör çiftidir. `(1, −1)` için `A v = (2, −2) = 2 v`, yani `λ = 2`.

**Adım 3 — Kaba çöz.** Karakteristik denklemi elle kur: `det(A − λ I) = (3 − λ)² − 1 = λ² − 6λ + 8 = 0`. Kökler `4` ve `2`'dir; bu, adım 2'deki sonucu doğrular.

**Adım 4 — Örüntü.** Özvektörleri birim uzunluğa getir: `v₁ = (1, 1)/√2`, `v₂ = (1, −1)/√2`. Bunlar diktir (`v₁ · v₂ = 0`). `V = [v₁ v₂]` ve `Λ = diag(4, 2)` ile `A = V Λ Vᵀ`. Bu, `Aᵏ = V Λᵏ Vᵀ` ile `Aᵏ`'yi hızlı hesaplamanın yoludur.

**Adım 5 — İyileştir.** `A⁵ = V diag(4⁵, 2⁵) Vᵀ`. `4⁵ = 1024`, `2⁵ = 32`; `A⁵ = [(1024 + 32)/2, (1024 − 32)/2; (1024 − 32)/2, (1024 + 32)/2]`. Yani matris çarpımı yerine iki sayıyla iş bitti. Simetrik matriste `A^k`'nin köşegeni `(4ᵏ + 2ᵏ)/2`, köşegen dışı `(4ᵏ − 2ᵏ)/2`'dir.

**Adım 6 — Doğrula.** Aşağıdaki tablo `Aᵏ`'yi `k = 1..5` için iki yoldan da verir: çarpma ile ve formülle.

| k | Aᵏ (çarpma) | köşegen (4ᵏ+2ᵏ)/2 | köşegen dışı (4ᵏ−2ᵏ)/2 |
|---|---|---|---|
| 1 | [[3, 1], [1, 3]] | 3 | 1 |
| 2 | [[10, 6], [6, 10]] | 10 | 6 |
| 3 | [[36, 28], [28, 36]] | 36 | 28 |
| 4 | [[136, 120], [120, 136]] | 136 | 120 |
| 5 | [[528, 496], [496, 528]] | 528 | 496 |

Program, `eigh` ile `V`'yi ve `Λ`'yı hesaplar; `V Λ Vᵀ = A` ve iki `A⁵` yöntemini karşılaştırır.

```python
# ornek3.py: simetrik 2x2 matris: ozdeger, ozvektor, kosegenlestirme
import numpy as np

A = np.array([[3.0, 1.0], [1.0, 3.0]])
print("karakteristik: det(A - lam I) = lam^2 - 6 lam + 8")
print("kokler: lam1 = 4, lam2 = 2")
v1 = np.array([1.0, 1.0]) / np.sqrt(2)
v2 = np.array([1.0, -1.0]) / np.sqrt(2)
print("A v1 =", np.round(A @ v1, 6), " 4 v1 =", np.round(4 * v1, 6))
print("A v2 =", np.round(A @ v2, 6), " 2 v2 =", np.round(2 * v2, 6))

vals, V = np.linalg.eigh(A)
print("numpy lambda =", vals)
Lam = np.diag(vals)
print("V Lam V^T == A ?", np.allclose(V @ Lam @ V.T, A))
A5 = V @ np.diag(vals ** 5) @ V.T
print("A^5 (kopegel.) =")
print(np.round(A5, 3))
print("A^5 (matris_power) =")
print(np.round(np.linalg.matrix_power(A, 5), 3))
```

```term
$ python ornek3.py
karakteristik: det(A - lam I) = lam^2 - 6 lam + 8
kokler: lam1 = 4, lam2 = 2
A v1 = [2.828427 2.828427]  4 v1 = [2.828427 2.828427]
A v2 = [ 1.414214 -1.414214]  2 v2 = [ 1.414214 -1.414214]
numpy lambda = [2. 4.]
V Lam V^T == A ? True
A^5 (kopegel.) =
[[528. 496.]
 [496. 528.]]
A^5 (matris_power) =
[[528. 496.]
 [496. 528.]]
```

**Bunu AI'sız yazabilir misin?** `A = [[2, 1], [1, 2]]` için özdeğerleri ve özvektörleri elle bul; sonra `A⁴`'ü köşegenleştirme ile hesapla ve çarpma ile karşılaştır. Özdeğer sıralamasını (`eigh` küçükten büyüğe verir) kendi tablonda belirt.

### Örnek 4 (★★★): SVD ile rank-k yaklaşım: hata ve sıkıştırma oranı

**Problem:** `8 × 6` matrisi `A = 5 u₁ v₁ᵀ + 1 u₂ v₂ᵀ` biçiminde kurulmuştur, `u₁ = (1, 2, 3, 4, 3, 2, 1, 0)`, `u₂ = (0, 1, 0, −1, 0, 1, 0, −1)`, `v₁ = (1, 1, 1, 1, 1, 1)`, `v₂ = (1, −1, 1, −1, 1, −1)`. Tekil değerleri hesapla. `k = 1` ve `k = 2` için `‖A − A_k‖_F` hatasını ve depolama oranını bul.

**Adım 1 — Anla.** Girdi `8 × 6` bir matris, çıktı tekil değerler, hatalar ve oranlardır. Matris 48 sayıdır; `k` terimle 15 sayı ile yazılabilir (`k(m + n + 1)`).

**Adım 2 — Örnekle.** Bu matris iki terimli bir toplamdır. `‖u₁‖ = √44`, `‖v₁‖ = √6`, `‖u₂‖ = 2`, `‖v₂‖ = √6`. Ayrıca `u₁ · u₂ = 0` ve `v₁ · v₂ = 0`: iki terim birbirine diktir.

**Adım 3 — Kaba çöz.** Dikeyliği görünce tekil değerleri doğrudan yazabiliriz: `σ₁ = 5 ‖u₁‖ ‖v₁‖ = 5 √44 √6 = 5 · 6.633 · 2.449 ≈ 81.24` ve `σ₂ = 1 · ‖u₂‖ ‖v₂‖ = 2 · 2.449 ≈ 4.899`. Kalan tekil değerler sıfırdır; rank 2'dir.

**Adım 4 — Örüntü.** Tekil değer ayrışımında `A_k` ilk `k` terimin toplamıdır. Eckart–Young'a göre `k = 1` için hata `σ₂ = 4.899`'dur; `k = 2` için hata sıfırdır. Depolama oranı `k(m + n + 1)/(mn) = k · 15/48`'dir.

**Adım 5 — İyileştir.** Hesabı SVD'yi çalıştırmadan yap: `σ`'ları ve oranları formülle hesapla. Bu, büyük matrislerde de aynı mantıkla çalışır; sadece `σ`'ları SVD'den okursun.

**Adım 6 — Doğrula.** Aşağıdaki tablo elle hesabı programın çıktısıyla karşılaştırır.

| k | elle hata (√Σ_{i>k} σᵢ²) | programın hatası | oran (k · 15/48) |
|---|---|---|---|
| 1 | 4.899 | 4.8990 | 0.3125 |
| 2 | 0 | 0.0000 | 0.6250 |

Program tekil değerleri ve iki `k` için hatayı ile oranı yazdırır. `rank(A) = 2` satırı, sıfır olmayan tekil değer sayısının iki olduğunu doğrular.

```python
# ornek4.py: SVD ile rank-k hata ve sikistirma orani hesabi
import numpy as np

m, n = 8, 6
u1 = np.array([1.0, 2, 3, 4, 3, 2, 1, 0])
u2 = np.array([0.0, 1, 0, -1, 0, 1, 0, -1])
v1 = np.array([1.0, 1, 1, 1, 1, 1])
v2 = np.array([1.0, -1, 1, -1, 1, -1])
A = 5.0 * np.outer(u1, v1) + 1.0 * np.outer(u2, v2)

U, s, Vt = np.linalg.svd(A, full_matrices=False)
print("tekil degerler:", np.round(s, 4))
print("rank(A) =", np.linalg.matrix_rank(A))
for k in [1, 2]:
    Ak = (U[:, :k] * s[:k]) @ Vt[:k]
    hata = np.linalg.norm(A - Ak, "fro")
    tahmin = np.sqrt(np.sum(s[k:] ** 2))
    oran = k * (m + n + 1) / (m * n)
    print("k=%d  ||A-Ak||_F = %.4f  (sqrt toplam s^2 = %.4f)"
          % (k, hata, tahmin))
    print("     sikistirma orani = %d*(8+6+1)/(8*6) = %.4f"
          % (k, oran))
```

```term
$ python ornek4.py
tekil degerler: [81.2404  4.899   0.      0.      0.      0.    ]
rank(A) = 2
k=1  ||A-Ak||_F = 4.8990  (sqrt toplam s^2 = 4.8990)
     sikistirma orani = 1*(8+6+1)/(8*6) = 0.3125
k=2  ||A-Ak||_F = 0.0000  (sqrt toplam s^2 = 0.0000)
     sikistirma orani = 2*(8+6+1)/(8*6) = 0.6250
```

**Bunu AI'sız yazabilir misin?** Aynı `A`'nın rank-1 yaklaşımını yalnızca `σ₁ u₁ v₁ᵀ` ile kur ve `‖A − A₁‖_F`'yi hesapla. Sonucun `σ₂`'ye eşit olduğunu neden beklemen gerektiğini iki cümleyle açıkla.


## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Lineer cebirin asıl öğrenimi, bir matrisin satırlarını elinle takas edip çarpanları kendi kodunla hesaplamaktan geçer. Bir aracın yazdığı LU ya da SVD kodu doğru sonuç verse bile sınır durumlarını (tekil matris, boş girdi, `1 × 1` matris, çok küçük pivot) sen test etmedikçe bilmiyorsun. NumPy'yi yalnızca referans olarak kullan; çözüm kodunda `np.linalg` çağırma.
:::

### Proje 1 (★★): Sıfırdan mini lineer cebir kütüphanesi

**Amaç:** NumPy kullanmadan (yalnızca Python listeleri ve `math`) bir `Matris` sınıfı yaz; bu sınıf kısmi pivotlu LU, determinant, ters, `solve`, modifiye Gram–Schmidt ile QR ve güç yinelemesi işlemlerini yapsın. Her işlemi NumPy'nin karşılık gelen sonucuyla karşılaştır.

**Yapılacak / Beklenen davranış:**

1. `Matris` sınıfı `m × n` boyutunu, toplama, çarpma (`@` işleci `__matmul__` ile), devrik ve `__repr__` işlemlerini destekler.
2. `lu(A)`: `P A = L U` döndürür; takas sayısını da verir. `det(A)`, LU'nun pivotlarından `(−1)^takas · Π pivotlar` ile hesaplanır.
3. `coz(A, b)`: LU ile çözer. Tekil matriste (bir pivot `1e-12`'nin altındaysa) açık bir hata fırlatır.
4. `ters(A)`: birim vektörleri `coz` ile çözerek `A⁻¹`'in sütunlarını bulur.
5. `qr(A)`: değiştirilmiş Gram–Schmidt ile `Q` ve `R` üretir; `Qᵀ Q ≈ I` ve `QR ≈ A` testlerini geçer.
6. `guc_yineleme(A)`: simetrik bir matris için en büyük mutlak özdeğeri ve özvektörünü verir.

**Önerilen yaklaşım (ipucu, tam çözüm değildir):** Önce `lu` fonksiyonunu yaz ve küçük `3 × 3` bir matris ile elle hesapladığın değerleri karşılaştır. `coz`'u LU'nun iki üçgen çözümü olarak kur; ileri ve geri yerine koymayı ayrı fonksiyonlar yap. Gram–Schmidt'te izdüşümleri her çıkarmadan sonra güncel vektörle hesapla (48.11'deki değiştirilmiş sürüm). Güç yinelemesinde Rayleigh bölümünü kullan. Hız karşılaştırmasında yalnızca `n ≤ 200` için ölç; saf Python'da daha büyük matrislerde süre çok uzar (48.14).

**Başarı kriterleri:**

- 300 rastgele `n × n` sistemde (`n ∈ [2, 8]`, tohum `42`), senin `coz` sonucun NumPy `solve` sonucuyla en fazla `10⁻⁸` mutlak farkla eşleşir.
- Bir sıfır pivotlu ama tekil olmayan matris (örneğin `[[0, 1], [1, 0]]`) doğru çözülür; yani takas çalışır.
- Tekil matrisler (`[[1, 2], [2, 4]]`) için `coz` açık bir hata verir, sessizce yanlış sonuç vermez.
- `qr` için `‖QᵀQ − I‖_F < 10⁻¹²` ve `‖QR − A‖_F < 10⁻¹²` (`5 × 5` rastgele matris).
- Hız tablosu `n = 50, 100, 200` için hem senin sürümünü hem `np.linalg.solve`'u içerir ve log-log grafiği ile yorumlanmıştır.

### Proje 2 (★★★): SVD ile görüntü sıkıştırma ve gürültü giderme

**Amaç:** Gerçek bir gri tonlamalı görüntü üzerinde SVD tabanlı bir sıkıştırıcı ve bir gürültü giderici yaz. Sıkıştırma ile hata ve depolama oranı arasındaki takası ölç, gürültü gidermenin düşük rank varsayımıyla neden işe yaradığını göster.

**Yapılacak / Beklenen davranış:**

1. Bir gri tonlamalı görüntüyü (kendi fotoğrafın ya da 256 × 256 bir test görüntüsü) bir `float` matrise çevir. Görüntüyü `[0, 1]` aralığına normalize et.
2. Girdi olarak bir `k` ya da bir enerji eşiği (tekil değerlerin karelerinin toplamının `%90` ya da `%99`'u) al. `k`'yi enerji eşiğinden otomatik seç.
3. Sıkıştırılmış görüntüyü, orijinal ile birlikte aynı pencerede göster. Bağıl hatayı ve depolama oranını yazdır.
4. Görüntüye tohumlu (`42`) Gauss gürültüsü ekle (`σ = 0.05` ve `σ = 0.1`). Gürültülü görüntünün düşük rank yaklaşımını alarak gürültü gidermeyi dene ve PSNR (`10 log₁₀(1 / MSE)`) ile ölç.
5. `k`'ya karşı hata, oran ve PSNR grafiklerini çiz.

**Önerilen yaklaşım (ipucu, tam çözüm değildir):** `np.linalg.svd(A, full_matrices=False)` ile başla; yukarıdaki `svd_gorsel.py` programı sana rank-k yaklaşımın iskeletini verir. Enerji eşiği için `np.cumsum(s**2) / np.sum(s**2)` kullan. Gürültü gidermede gerçek görüntünün tekil değerlerinin hızla düştüğünü, gürültünün ise geniş bir tekil değer yelpazesine yayıldığını düşün: bu iki yapıyı ayırmak için hangi `k`'nin uygun olduğunu sen ölçmelisin. Yalnızca bir tekil değer eşiğiyle başlayabilirsin.

**Başarı kriterleri:**

- Tohum `42` ile, aynı görüntüde iki çalıştırma birebir aynı sayıları verir.
- Enerji eşiği `%99` için seçilen `k` ile yapılan yaklaşımın bağıl hatası, Eckart–Young'a göre hesaplanan `√(Σ_{i>k} σᵢ²) / ‖A‖_F` değeriyle eşleşir (`10⁻¹²` toleransla).
- Gürültü gidermede en az bir `k` değeri için gürültülü görüntünün PSNR'ı, gürültüsüz girdiye karşı ölçülen PSNR'dan yüksektir. Bu sonucu `σ = 0.05` ve `σ = 0.1` için ayrı raporla.
- Rapor, düşük rank varsayımının hangi görüntüde işe yaramadığını da içerir (ör. ince dokulu bir görüntü), çünkü her yöntemin bir sınırı vardır.

### Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kâğıtta düşün; son çare olarak kodla doğrula. Mülakat sorularının bir kısmı ayrıca işaretlidir.

1. ★ `(2, −1, 3)` ve `(1, 4, −2)` vektörlerinin nokta çarpımını, L1, L2 ve L∞ normlarını ve aralarındaki kosinüsü hesapla. Kosinüs negatifse vektörler hakkında ne söylenebilir?
2. ★ Birim karenin `(1, 1)` doğrultusundaki yansımasını veren 2×2 matrisi bul. Determinantı nedir ve bu sayı yansımanın hangi özelliğini söyler? (Mülakat)
3. ★ `R(θ) = [[cos θ, −sin θ], [sin θ, cos θ]]` için `Rᵀ R = I` ve `det(R) = 1` olduğunu elle göster. `R(a) R(b) = R(a + b)` eşitliğinin neden doğru olduğunu açıkla. (Mülakat)
4. ★ `[[2, 0, 1], [1, 3, 0], [0, 1, 4]]` matrisinin tersini kofaktörlerle elle hesapla; sonucu `np.linalg.inv` ile karşılaştır.
5. ★★ `[[a, b], [c, d]]` matrisinin özdeğerlerinin gerçek olmadığı bir koşul bul. Bu koşulu karakteristik polinomun diskriminantıyla ifade et. (Mülakat)
6. ★★ Gauss eliminasyonunda ilk pivotun sıfır olduğu, ama matrisin tekil olmadığı bir `3 × 3` örnek ver. Takas gerekir mi, hangi takas?
7. ★★ Klasik ve değiştirilmiş Gram–Schmidt'i `n = 5` Hilbert matrisinde karşılaştır. Dikliğin bozulmasını `‖QᵀQ − I‖_F` ile ölç ve hangi yöntemin neden daha kararlı olduğunu iki cümleyle yaz.
8. ★★ Rank-nullity teoremini (`rank(A) + dim N(A) = n`) bir `4 × 6` matris üzerinde açıkla ve bir örnekle doğrula. Boş uzayın boyutu sıfır olmadan `A x = 0`'ın yalnızca sıfır çözümü olduğunu neden söyleyebilirsin? (Mülakat)
9. ★★ Sütunları doğrusal bağımlı bir `X` tasarım matrisinde `XᵀX` tekildir. `np.linalg.pinv` bu durumda neyi döndürür? En küçük normlu çözümü elle nasıl bulursun? (Mülakat)
10. ★★★ Güç yinelemesinin yakınsama hızının ikinci en büyük ve en büyük mutlak özdeğerlerin oranına (`|λ₂| / |λ₁|`) bağlı olduğunu iki simetrik matris üzerinde deneyle göster. Oranı değiştirerek hata-iterasyon eğrisinin eğimini gözlemle.
11. ★★★ `512 × 512` bir gri görüntüde SVD ile `k = 20` ve `k = 50` sıkıştırması yap. Depolama oranını ve PSNR'ı (`10 log₁₀(MAX² / MSE)`) hesapla. Hangi `k` için görsel olarak fark edilmez kalitesi başlar?
12. ★★★ Bir MLP katmanında `1024 × 1024` ağırlık matrisi `W` vardır. Rank-32 yaklaşımı ile parametre sayısının ne kadar azalacağını ve bağıl hatanın ne olacağını, `W`'nin tekil değerlerini bir normal dağılım örneğinde ölçerek tahmin et. Bu tahmin neden gerçek bir sinir ağı ağırlığı için kesin olmayabilir? (Mülakat)

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak kodu okuyacaksın: NumPy 2.3.5'in lineer cebir modülündeki `solve` fonksiyonu. Kaynak, NumPy deposunun `v2.3.5` etiketinden alındı (`https://raw.githubusercontent.com/numpy/numpy/v2.3.5/numpy/linalg/_linalg.py`). Bu dosya, bilgisayarımızda kurulu NumPy 2.3.5'in `numpy/linalg/_linalg.py` dosyasıyla satır sonları normalize edildiğinde birebir aynıdır; yani kurulu sürüm ile etiket aynıdır.

Aşağıdaki kesit `solve` fonksiyonunun imzasını ve gövdesini içerir; docstring (384–455. satırlar, yaklaşık 72 satır) atlandı, kodun geri kalanı kelimesi kelimesine kopyalandı. Atlanan yer kesitte "docstring atlandı" diye işaretli. Gövdedeki bir yorum satırı ("We use the b = ...") sayfa genişliği için iki satıra bölündü; kelimeler değişmedi.

```python
def solve(a, b):
    # [384-455. satirlar: docstring atlandi]
    a, _ = _makearray(a)
    _assert_stacked_square(a)
    b, wrap = _makearray(b)
    t, result_t = _commonType(a, b)

    # We use the b = (..., M,) logic, only if the number of
    # extra dimensions
    # match exactly
    if b.ndim == 1:
        gufunc = _umath_linalg.solve1
    else:
        gufunc = _umath_linalg.solve

    signature = 'DD->D' if isComplexType(t) else 'dd->d'
    with errstate(call=_raise_linalgerror_singular, invalid='call',
                  over='ignore', divide='ignore', under='ignore'):
        r = gufunc(a, b, signature=signature)

    return wrap(r.astype(result_t, copy=False))
```

Bu kesit birkaç şeyi açıkça gösterir. `_makearray` girdiyi bir NumPy dizisine çevirir, `_assert_stacked_square` ise kare olup olmadığını denetler. `b.ndim == 1` kontrolü, `b`'nin tek bir vektör mü yoksa bir matris yığını mı olduğuna göre iki farklı gufunc'a (`solve1` ve `solve`) yönlendirme yapar: docstring'in `versionchanged 2.0` notu bu ayrımın tarihçesini anlatır. Asıl hesap C tarafındaki `_umath_linalg` modülünde yapılır; bu modül Python'a açık değildir ve bu kesitte yer almaz.

**Sorular — cevaplamadan geçme:**

1. `errstate(call=_raise_linalgerror_singular, invalid='call', ...)` bloğu ne yapar? Bir matris tekil olduğunda kullanıcıya hangi hata sınıfı ulaşır ve bu hata nerede tanımlanmıştır? Kaynak dosyada bul.
2. `b.ndim == 1` ile `b.ndim > 1` ayrımı neden gerekli? Docstring'deki `versionchanged 2.0` notunu okuyup eski davranışın neden kafa karıştırıcı olduğunu iki cümleyle açıkla.
3. Docstring'de çözümün LAPACK rutini `_gesv` ile hesaplandığı yazar. Bu rutinin hangi matematiksel ayrışımı yaptığını (48.8) ve `P A = L U` ile ilişkisini kendi cümlelerinle anlat.
4. `r.astype(result_t, copy=False)` neden var? `_commonType` fonksiyonunun döndürdüğü `result_t`'nin girdi türüne nasıl bağlı olduğunu `_commonType` kaynağında (`182–260` satırları arası) bularak yaz.
5. Kodda `gufunc(a, b, signature=signature)` çağrısı var. İmza `dd->d` ne anlama gelir? Bu imzanın `DD->D` karmaşık sürümünden farkı nedir?
6. Kodda hiçbir `np.linalg.inv` çağrısı yok. Bu, `solve`'un içinde tersin hesaplanmadığını mı gösterir, yoksa tersi başka bir yerde mi hesaplar? Cevabını, `_umath_linalg` modülünün hangi LAPACK rutinlerini kullandığını öğrenerek (kaynak: NumPy deposundaki `numpy/linalg/umath_linalg.cpp`, bu bölümde indirmedik) doğrula ya da "emin değilim" olarak işaretle.

## Bölüm Özeti

Bu bölümde lineer cebiri bir hesap listesi olarak değil, bir hareket ve bir ölçü olarak öğrendik:

- **Vektör** hem ok hem kayıttır. Nokta çarpım açıyı ve izdüşümü verir; kosinüs benzerliği uzunluktan bağımsız bir benzerlik ölçüsüdür. Bu, gömme tabanlı aramanın temelidir.
- **Norm** bir uzaklık tanımıdır: L1, L2 ve L∞ farklı birim kümeler ve farklı hata karakterleri verir. Frobenius normu matrisi uzun bir vektör gibi ölçer.
- **Matris bir doğrusal dönüşümdür**: sütunları birim vektörlerin görüntüsüdür. Determinant alan ölçeğidir, işareti yönelimi söyler.
- **Matris çarpımı dönüşümlerin bileşimidir** ve değişmeli değildir. 3B dönmeler ortogonal matrislerdir (`Rᵀ R = I`); homojen koordinatlar öteleme ile dönmeyi tek matriste birleştirir.
- **Gauss eliminasyonu** ve kısmi pivotlama `A x = b`'yi çözer. Küçük bir pivot yuvarlama hatasını büyütür (`ε` deneyi). LU ayrışımı aynı işi bir kez yapıp çok kez kullanılmasını sağlar.
- **Rank** bir sistemin çözüm sayısını belirler. Vektör uzayları ve dört temel alt uzay, sütun ve boş uzayların birbirine dik olduğunu gösterir.
- **Koşul sayısı** hata büyütmesini ölçer; `log₁₀ κ` kaybolan basamak sayısının kabaca değeridir. `solve`, `inv` ile çarpmaktan genellikle hem hızlı hem doğrudur.
- **Ortogonallik** ve QR, en küçük kareler problemini kararlı çözer; normal denklemler `κ²` ile bozulur.
- **Özdeğer ve özvektör** dönüşümün yönü değişmeyen eksenleridir. Güç yinelemesi bunları yinelemeyle bulur; PageRank ve Markov durağan dağılımı bu fikrin uygulamalarıdır.
- **SVD** her matrisi döndür–ölçekle–döndür olarak yazar. Düşük rank yaklaşımı Eckart–Young ile optimaldir ve görüntü sıkıştırma, pseudo-inverse, PCA ve LoRA'nın ortak temelidir.
- **Hesaplama**: BLAS ve LAPACK, NumPy'nin altındaki optimize çekirdeklerdir; saf Python'a karşı fark binlerce kattır. Bellek düzeni, yayınlama ve `einsum`, ML kodunda şekil hatalarını anlamanın araçlarıdır.

**Sonraki bölümde:** Bölüm 49'da, Olasılık ve İstatistik'e geçiyoruz. Bu bölümde gördüğümüz kovaryans matrisi, Markov zincirlerinin durağan dağılımı ve PCA'nın istatistiksel yorumu, bu bölümün lineer cebir tarafının olasılıksal karşılıkları olacak. Bayes kuralı, beklenen değer ve varyans, MLE ve MAP, hipotez testi ile güven aralığı da orada ele alınacak. Bu bölümde yazdığımız matris araçları olasılık hesaplarını vektörleştirmek için ihtiyacın olacak.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. Bir matrisin determinantının sıfır olması ne anlama gelir? Bu durumun üç eşdeğer yorumunu (ters yok, rank eksik, boş uzay var) bir örnekle açıkla.
2. `A x = b` sistemini çözmek için neden `inv(A) @ b` yerine `solve(A, b)` kullanılmalı? Hangi durumda ikisi de aynı sonucu verir ama hata farkı belirgin olur?
3. Koşul sayısı `10⁹` olan bir sistemde çift duyarlıklı bir sonucun kaç anlamlı basamağına güvenebilirsin? Bu tahmini hangi varsayımlarla yaptın?
4. Klasik ve değiştirilmiş Gram–Schmidt matematiksel olarak aynıdır, ama sayısal olarak farklıdır. Bu farkın sebebi nedir ve hangi durumda hangisini seçersin?
5. Normal denklemler yerine QR ile en küçük kareler çözmek neden daha kararlıdır? `κ(AᵀA) = κ(A)²` ilişkisinin bu kararlılık farkıyla bağlantısını anlat.
6. Bir matrisin özvektörleri her zaman birbirine dik midir? Simetrik olmayan bir matris için karşı örnek ver ve simetrik matrisler için bu özelliğin hangi teoremden geldiğini söyle.
7. SVD'nin düşük rank yaklaşımı neden optimaldir? Frobenius normunda hatayı en küçük yapan `k`'nın tekil değerlerden nasıl seçildiğini açıkla.
8. Bir sinir ağında iki ardışık doğrusal katmanın araya doğrusal olmayan bir fonksiyon konmadan birleştirilemeyeceğini matris çarpımının özelliklerinden yola çıkarak göster. Bu sonuç, derin ağların neden "derin" olması gerektiği sorusuyla nasıl ilişkilidir?
:::
