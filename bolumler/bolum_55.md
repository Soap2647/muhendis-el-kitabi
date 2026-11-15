%% kisim_no: XIV
%% kisim_ad: Makine Öğrenmesi
%% bolum_no: 55
%% baslik: ML için Kalkülüs & Otomatik Türev

## Giriş: Öğrenmek, bir kaybın türevini almaktır

Bir sinir ağını eğitmek, kulağa büyülü gelen bir işlem gibi duyulur. Oysa eğitimin özü tek bir soruya iner: "Her parametreyi biraz oynatırsam kayıp ne kadar değişir?" Parametreler milyonlarca olabilir, kayıp ise tek bir sayıdır. Bu soruya cevap veren araç türevdir. Gradyan inişi (Bölüm 50) her adımda parametreleri kaybın azaldığı yöne kaydırır; bu yönü hesaplamak için de her parametre için kısmi türev gerekir.

Bu bölümün iddiası somut: geri yayılım (backpropagation) sihir değildir. Zincir kuralının, bir hesap grafiği üzerinde doğru sırayla uygulanmasıdır. Bunu kendi gözünle görmek için, bu bölümün sonunda kendi otomatik türev motorunu yazacaksın ve o motorla küçük bir sinir ağını eğiteceksin. Motor yaklaşık yüz satırdır; her satırını anlayacaksın.

Savunma sanayiinde bu konu gündelik iştir. Bir İHA'nın hedef takip filtresini ayarlarken, bir sensör füzyonu modelinin kalibrasyon parametrelerini bulurken ya da bir görüntü sınıflandırıcısını eğitirken, türev bir yerde mutlaka çıkar. Bölüm 46'da EV telemetrisi için bir anomali modelini eğittik; orada geri yayılımı elle yazdık ve ayrıntısını bu bölüme bıraktık. Burada o borcu ödüyoruz.

Mülakatlarda da bu konu sık sorulur: "Backpropagation'ı açıkla", "neden ters mod?", "sigmoid ağlarında neden gradyan kaybolur?" Bu soruların cevabı ezberlenmiş bir formül değil, zincir kuralını bir grafik üzerinde taşıyabilme becerisidir. Bu bölüm o beceriyi kurmak için yazıldı.

Bölüm boyunca üç düzeyde çalışacağız. İlkinde tek değişkenli türevi ve zincir kuralını yerleştiririz. İkincisinde vektör ve matris düzeyine çıkarız: gradyan, Jacobian ve matris kalkülüsü. Üçüncüsünde ise türevin bilgisayarda nasıl hesaplandığına bakarız: sayısal fark, sembolik türev ve otomatik türev.

::: not
Bu bölümdeki her kod, sabit tohumla çalışır ve çıktısı kitapta birebir gösterilir. Okurken kodu yanına aç ve kendi makinende çalıştır. Çıktıların birebir tutması, anladığını kanıtlamanın en kısa yoludur. Hız ölçümleri hariç hiçbir sayı makineye bağlı değildir.
:::

## 55.1 Türev: yerel doğrusal yaklaşım

Bir fonksiyonun bir noktadaki türevi, o noktanın çok küçük bir komşuluğunda fonksiyonu bir doğru ile yaklaşık olarak temsil eden eğimdir. `f(x)` fonksiyonunun `x = a` noktasındaki türevi `f′(a)` ile gösterilir ve şu limitle tanımlanır:

f′(a) = lim (h → 0) [f(a + h) − f(a)] / h

Geometrik anlamı şudur: `(a, f(a))` noktasından geçen ve eğimi `f′(a)` olan doğru, eğrinin o noktadaki en iyi doğrusal yaklaşımıdır. Buna teğet (tangent) denir. Bu yaklaşım, `h` küçükken şöyle yazılır:

f(a + h) ≈ f(a) + f′(a) · h

Bu cümleyi bütün bölüm boyunca kullanacağız. Bir fonksiyonu bir noktada doğrusal bir modelle değiştirmek, türevin tek anlamıdır. Tek değişkende bu bir doğrudur, çok değişkende bir düzlem, daha yüksek boyutlarda ise bir doğrusal dönüşümdür. Gradyan da Jacobian da bu fikrin farklı kıyafetleridir.

Şekil 55.1 bunu `f(x) = x³ − 2x` fonksiyonu için gösteriyor. `x = 1` noktasında `f(1) = −1` ve türev `f′(x) = 3x² − 2` olduğundan `f′(1) = 1`dir. Teğet doğrusu `y = x − 2` olur. `x = 1,4`e giden küçük bir adımda doğru ile eğrinin farkı küçük kalır; adım büyüdükçe fark büyür.

![Şekil 55.1: f(x) = x³ − 2x ve x = 1 noktasındaki teğet doğrusu](gorseller/b55_teget.png)

Türevi bilgisayarda hesaplamanın en basit yolu, türev tanımındaki limiti küçük bir `h` ile yaklaşık almaktır. Bunu merkezi fark ile yaparız: `h` değerini hem sağa hem sola uygular ve farkı alırız. Bölüm 50.3'te bu yöntemi ve hatasını ayrıntılı olarak gördün; burada yalnızca kod olarak kullanacağız. Aşağıdaki fonksiyon, bir vektörün her bileşeni için merkezi farkı hesaplar.

```python
def merkezi_fark(f, x, h=1e-6):
    # Her x_i için (f(x + h e_i) - f(x - h e_i)) / 2h.
    g = []
    for i in range(len(x)):
        xp, xm = list(x), list(x)
        xp[i] += h
        xm[i] -= h
        g.append((f(xp) - f(xm)) / (2 * h))
    return g
```

Bu fonksiyonun döngüsü her girdi bileşeni için iki kez değerlendirme yapar. Yani `n` parametreli bir fonksiyonun tam gradyanı için `2n` fonksiyon çağrısı gerekir. Bir sinir ağında `n` milyonlarsa bu yöntem imkânsızlaşır. Bölüm 55.7'de bu maliyeti sayısal olarak göreceğiz.

## 55.2 Zincir kuralı: bileşik fonksiyon

Gerçek fonksiyonlar tek bir adımda yazılmaz. `sin(x²)` ifadesinde önce `x²` hesaplanır, sonra sinüsü alınır. Bu tür bir fonksiyona bileşik fonksiyon denir. Eğer `f = g ∘ h`, yani `f(x) = g(h(x))` ise türev şöyle hesaplanır:

f′(x) = g′(h(x)) · h′(x)

Buna zincir kuralı denir. Kural, dış fonksiyonun türevini iç fonksiyonun değerinde alıp iç fonksiyonun türeviyle çarpmayı söyler. Leibniz gösterimiyle yazarsak, `u = h(x)` ve `f = g(u)` için `df/dx = (df/du)(du/dx)` olur. Gösterimi bir çarpım gibi okumak, zincir kuralının akılda kalan biçimidir.

Neden bu kadar önemli? Çünkü bir sinir ağı, her katmanı bir önceki katmanın bileşimi olan çok uzun bir zincirdir. Kayıp, son katmanın çıktısının bir fonksiyonudur ve bu çıktı, ilk katmanın parametrelerinin bir bileşimidir. Zincir kuralını uzun bir zincire uyguladığında geri yayılım elde edilir. Zincir ne kadar uzunsa, her halkanın türevinin ne kadar büyük olduğu da çarpım olarak belirleyicidir. Bu, 55.13'te kaybolan gradyanın kaynağıdır.

Şekil 55.2, `f(x) = sin(x²)` için zincir kuralını bir akış olarak gösteriyor. Değerler soldan sağa, türevler sağdan sola çarpılarak akar. İç türev `h′(x) = 2x`, dış türev `g′(u) = cos u` olduğundan sonuç `cos(x²) · 2x`tir.

![Şekil 55.2: Zincir kuralı akışı: iç ve dış türevlerin çarpımı](gorseller/b55_zincir_akis.png)

Kuralı sayısal olarak da denetleyebilmek için Çözümlü Örnek 1'de `x = 1,2` noktasında elle hesaplanan türevi merkezi farkla karşılaştıracağız. Şimdilik yalnızca bir kural olarak kalsın: her iç halka bir çarpan katar. Bu çarpanlardan biri 1'den küçükse ve zincir uzunsa, çarpım hızla sıfıra gider. Bu gözlem, bu bölümün ilerisinde önemli olacak.

## 55.3 Gradyan, yönlü türev ve Jacobian

Birden çok girdisi olan bir fonksiyon `f(x₁, ..., xₙ)` için her değişkene göre kısmi türev alabiliriz. `∂f/∂xᵢ` ifadesi, diğer bütün değişkenleri sabit tutup yalnızca `xᵢ`ye göre türevi gösterir. Bu kısmi türevlerin oluşturduğu vektöre gradyan denir ve `∇f` ile yazılır:

∇f(x) = (∂f/∂x₁, ∂f/∂x₂, ..., ∂f/∂xₙ)

Bölüm 50.2'de gradyanın en dik artış yönünü gösterdiğini görmüştük. Gradyan inişi bu yüzden kaybı azaltmak için gradyanın tersine gider: `θ ← θ − η ∇L(θ)`. Burada `∇L` kaybın gradyanıdır ve `θ` parametre vektörüdür. Bu bölümde gradyanın nasıl hesaplandığını görüyoruz; neden o yöne gidildiğini Bölüm 50 anlatmıştı.

Bir kısmi türev örneği olarak `f(x, y) = x²y` alalım. `∂f/∂x = 2xy` ve `∂f/∂y = x²` olur. Yani `∇f = (2xy, x²)` gradyanıdır. Noktası `(1, 2)` ise gradyan `(4, 1)` olur. Bu noktadan `u = (3/5, 4/5)` yönünde yürürsek fonksiyonun değişim hızı yönlü türev ile ölçülür:

D_u f = ∇f · u = 4 · 3/5 + 1 · 4/5 = 3,2

Yönlü türev, gradyanın bir yöne izdüşümüdür. `u` birim vektör olduğunda en büyük değeri, `u` gradyanla aynı yönde olduğunda alır. Bu, gradyanın neden en dik artış yönü olduğunun kısa cebirsel kanıtıdır.

Fonksiyon bir skalar değil de bir vektör döndürüyorsa, yani `f : ℝⁿ → ℝᵐ` ise, türevin karşılığı bir matristir. Bu matrise Jacobian denir ve `J` ile yazılır. Satır `i` çıktıyı, sütun `j` girdiyi gösterir:

J_ij = ∂fᵢ / ∂xⱼ

Jacobian, bir doğrusal yaklaşımın matrisidir. Bir ağın her katmanı bir vektörü başka bir vektöre gönderir, bu yüzden her katmanın bir Jacobian'ı vardır. Doğrusal bir katman en basit örnektir: `y = Wx + b` için `∂y/∂x = W` olur, çünkü `y`nin `x`e göre doğrusal bağımlılığı tam olarak `W` matrisidir. `b` sabittir ve türevi sıfırdır. Bu, Bölüm 48'de gördüğün matris çarpımının türev dilindeki karşılığıdır.

Jacobian'ı sayısal olarak hesaplamak, her girdi sütunu için merkezi fark almaktır. Bu fonksiyon `matris_turev.py` dosyasında yer alır ve 55.5'te de kullanılacak.

```python
def sayisal_grad_vek(f, x, h=1e-6):
    # Vektör -> vektör fonksiyonun Jacobian'ı: satır i, dy_i/dx_j.
    x = np.asarray(x, dtype=float)
    cols = []
    for j in range(x.size):
        xp, xm = x.copy(), x.copy()
        xp[j] += h
        xm[j] -= h
        fp, fm = np.atleast_1d(f(xp)), np.atleast_1d(f(xm))
        cols.append((fp - fm) / (2 * h))
    return np.stack(cols, axis=1)
```

Bir Jacobian'ı bu şekilde doğrulamak, analitik türetmenin doğru olup olmadığını anlamanın en güvenilir yoludur. Bu bölümün her türev formülünü aynı yöntemle sınayacağız.

## 55.4 Çok değişkenli zincir kuralı: Jacobian çarpımı

Zincir kuralını vektörlere genişletmek için `f = g ∘ h` olduğunu düşünelim, ama şimdi `h : ℝⁿ → ℝᵐ` ve `g : ℝᵐ → ℝᵏ`. Bu durumda Jacobian'lar çarpılır:

J_f(x) = J_g(h(x)) · J_h(x)

Burada `J_g` bir `k × m` matristir, `J_h` bir `m × n` matristir ve çarpım bir `k × n` matris verir. Şekillerin uyuşması, zincir kuralının doğru olduğunu gösteren ilk kontroldür. Bu kontrolü her zaman yapmanı öneririm: Türevin şekli, fonksiyonun girdi ve çıktı şekillerinden başka bir şey olamaz.

Somut bir örnek için `h(x₁, x₂) = (x₁x₂, x₁ + x₂²)` ve `g(u₁, u₂) = u₁² + sin u₂` alalım. `J_h = [[x₂, x₁], [1, 2x₂]]` ve `J_g = [2u₁, cos u₂]` olur. Çarpım, `(1, 0,5)` noktasında `(0,815322, 1,315322)` verir. Aşağıdaki fonksiyon bu iki Jacobian'ı kurar, çarpar ve sonucu merkezi farkla karşılaştırır.

```python
# Çok değişkenli: h: R^2 -> R^2, g: R^2 -> R, f = g o h
def h(x):
    return [x[0] * x[1], x[0] + x[1] ** 2]


def g(u):
    return u[0] ** 2 + math.sin(u[1])


def F(x):
    return g(h(x))


def jakobiyen_h(x):
    return [[x[1], x[0]], [1.0, 2 * x[1]]]


def gradyan_g(u):
    return [2 * u[0], math.cos(u[1])]


def coklu_degisken(x):
    Jh = jakobiyen_h(x)
    Jg = gradyan_g(h(x))
    # Satır vektörü (1x2) ile matris (2x2) çarpımı
    carpim = [sum(Jg[k] * Jh[k][j] for k in range(2))
              for j in range(2)]
    sayisal = merkezi_fark(F, x)
    print("u = h(x)  =", ["%.4f" % v for v in h(x)])
    print("J_h       =", Jh)
    print("J_g       =", ["%.4f" % v for v in Jg])
    print("J_g J_h   =", ["%.6f" % v for v in carpim])
```

Aşağıdaki çıktının ilk bölümü Örnek 1'in tek değişkenli türevini de gösterir. İkinci bölümdeki `J_g J_h` satırı ile `sayisal` satırı aynıdır. Tek değişkenli kısımda elle hesaplanan `f′(x)` ile merkezi fark arasındaki fark `10⁻¹¹` mertebesindedir. Bu fark, merkezi farkın kesme ve yuvarlama hatalarının toplamıdır.

```term
$ python zincir.py
     x         f(x)      elle f'      sayisal       fark
  0.50     0.247404     0.968912     0.968912    1.3e-11
  1.20     0.991458     0.313017     0.313017    1.7e-11
 -0.80     0.597195    -1.283353    -1.283353    3.0e-11
  2.00    -0.756802    -2.614574    -2.614574    7.4e-11

u = h(x)  = ['0.5000', '1.2500']
J_h       = [[0.5, 1.0], [1.0, 1.0]]
J_g       = ['1.0000', '0.3153']
J_g J_h   = ['0.815322', '1.315322']
sayisal   = ['0.815322', '1.315322']
```

## 55.5 Matris kalkülüsü: şekil düşüncesi ile türetme

Sinir ağlarında türev alınan şeyler çoğunlukla vektörler ve matrislerdir. Her seferinde kısmi türevleri tek tek yazmak yerine birkaç pratik kural kullanmak daha verimlidir. Bu kuralların ortak noktası, gradyanın şeklinin parametrenin şekli olmasıdır: bir matris `W` ise `∂L/∂W` de `W` ile aynı boyutta bir matristir. Bu, türetme sırasında yanlış bir çarpım sırasını hemen yakalamanı sağlar.

Aşağıdaki altı kural bu bölümde en çok karşılaşacağın kurallardır. `a` ve `x` vektör, `A` ve `W` matristir ve `y` hedef vektördür.

| Kural | Sonuç | Şekil kontrolü |
|---|---|---|
| ∂(aᵀx)/∂x | a | x ile aynı şekil |
| ∂(xᵀAx)/∂x | (A + Aᵀ)x | x ile aynı şekil |
| ∂‖Wx − y‖²/∂W | 2(Wx − y)xᵀ | W ile aynı şekil (2×3) |
| ∂(Wx + b)/∂x | W | Jacobian, çıktı × girdi |
| ∂(softmax(z))/∂z | diag(p) − ppᵀ | Jacobian, K × K |
| ∂L/∂z, softmax + çapraz entropi | p − y | z ile aynı şekil |

İlk kuralı türetelim. `aᵀx = ∑ aᵢxᵢ` olduğundan `∂(aᵀx)/∂xⱼ = aⱼ` olur; yani gradyan `a`dır. İkinci kuralda `xᵀAx = ∑ᵢ ∑ⱼ xᵢ Aᵢⱼ xⱼ` yazılır. `xₖ`ye göre türev iki yerde ortaya çıkar: `i = k` terimlerinde ve `j = k` terimlerinde. Sonuç `∑ⱼ (Aₖⱼ + Aⱼₖ) xⱼ` olur ve bu `(A + Aᵀ)x` ifadesidir. `A` simetrikse `2Ax` olur; bunu birçok kitapta görürsün.

Üçüncü kural, doğrusal bir katmanın kayıp gradyanıdır ve geri yayılımın özüdür. `r = Wx − y` olsun, kayıp `L = ‖r‖²` olsun. Zincir kuralıyla `∂L/∂r = 2r` ve `∂r/∂W` ise `W`nin her elemanının `r`ye etkisidir. Sonuçta `∂L/∂Wᵢⱼ = 2 rᵢ xⱼ` çıkar. Yani tüm matris `2 r xᵀ` dış çarpımıdır. Şekil kontrolü: `r` 2 boyutlu, `x` 3 boyutlu, dolayısıyla `r xᵀ` bir `2 × 3` matristir. Bu, `W` ile aynı şekildedir. Bu şekil düşüncesi, kuralı hatırlamak yerine yeniden türetmeni sağlar.

Dördüncü kural, Jacobian'ın doğrusal katmanda `W` olmasıdır. Beşinci ve altıncı kurallar softmax ile ilgilidir ve 55.6'da türetilecek.

Bu kuralların hepsini sayısal gradyanla doğruladık. Aşağıdaki kod, rastgele matrisler üzerinde her kuralın sayısal hatasını yazdırır. Sayısal gradyan fonksiyonu matrisin her elemanını ayrı ayrı oynatır ve sonucu matrisin şekliyle döndürür.

```python
def sayisal_grad(f, A, h=1e-6):
    # Matris girdi için merkezi fark; sonuç A ile aynı şekilde.
    G = np.zeros_like(A, dtype=float)
    for idx in np.ndindex(A.shape):
        Ap, Am = A.copy(), A.copy()
        Ap[idx] += h
        Am[idx] -= h
        G[idx] = (f(Ap) - f(Am)) / (2 * h)
    return G
```

Denetimi çalıştırdığında her kuralın hatası `10⁻¹⁰` ile `10⁻⁹` arasında kalır. Bu, türetilen formüllerin doğru olduğunun sayısal kanıtıdır.

```term
$ python matris_turev.py
Kural, sayisal hata:
  d(a^T x)/dx = a      2.3e-10
  d(x^T A x)/dx        6.9e-10
  d||Wx-y||^2/dW       2.9e-10  (sekil: (2, 3))
  dy/dx (Jacobian) = W 1.7e-10
  softmax J = diag(p)-pp^T 3.4e-11
  dL/dz = p - y        7.9e-11

Wx = [ 1. -2.]  r = Wx - y = [ 1. -3.]
L = ||r||^2 = 10.0
dL/dW =
[[  2.   0.   4.]
 [ -6.   0. -12.]]
sayisal fark = 8.4e-10
```

Çıktının ilk bölümü altı kuralı denetler. İkinci bölümde ise Çözümlü Örnek 3'teki sayısal değerlerle ikinci bir kontrol yapılır. Örnek 3'ü el ile çözeceksin; bu çıktı yalnızca sonucu teyit eder.

## 55.6 Eleman bazlı fonksiyonlar, softmax ve çapraz entropi

Bir sinir ağının içindeki çoğu fonksiyon eleman bazlıdır: bir vektörün her bileşenine aynı skaler fonksiyon uygulanır. Bunların türevleri birebir ve kolaydır. Aşağıdaki tabloda bu bölümde kullanacağımız üç aktivasyonun türevleri var.

| Fonksiyon | Tanım | Türev | Not |
|---|---|---|---|
| Sigmoid | σ(x) = 1 / (1 + e⁻ˣ) | σ′(x) = σ(x)(1 − σ(x)) | En büyük değeri 0,25 |
| tanh | tanh(x) | 1 − tanh²(x) | Değeri (−1, 1) arasında |
| ReLU | max(0, x) | 1, x > 0; 0, x < 0 | x = 0 noktasında türev yoktur |

Sigmoid türevinin formülü küçük bir cebirle elde edilir. `σ(x) = (1 + e⁻ˣ)⁻¹` yazılır, zincir kuralıyla `σ′ = e⁻ˣ (1 + e⁻ˣ)⁻²` bulunur. Bu ifade `σ(x) · (1 − σ(x))` biçiminde de yazılabilir, çünkü `1 − σ = e⁻ˣ/(1 + e⁻ˣ)`dir. Asıl önemli gözlem, `σ(x)(1 − σ(x))` çarpımının en büyük değerini `σ = 1/2` olduğunda, yani `x = 0`da, `1/4` olarak almasıdır. Bu 0,25 sınırı 55.13'te kaybolan gradyanın çekirdeğidir.

ReLU'nun `x = 0` noktasındaki türevi tanımsızdır. Yazılımda bu noktada 0 ya da 1 seçilir; uygulamada bu seçimin etkisi genellikle ihmal edilebilir, çünkü tam olarak sıfır olan bir girdi nadirdir. Kendi motorumuzda `relu` türevi `x > 0` ise 1 seçer, aksi halde 0.

Çok sınıflı bir sınıflandırıcıda son katman softmax kullanır: `pᵢ = eᶻⁱ / ∑ⱼ eᶻʲ`. Softmax'ın Jacobian'ı `∂pᵢ/∂zⱼ = pᵢ(δᵢⱼ − pⱼ)` ile verilir; matris biçiminde `diag(p) − ppᵀ` olur. Bu matris simetriktir ve her satırının toplamı sıfırdır; bu da softmax'ın olasılıkları toplam bire tuttuğunun bir yansımasıdır.

Bu Jacobian'ı doğrudan kullanmak gerekmez. Çok sınıflı çapraz entropi kaybıyla birleşince gradyan çok sadeleşir. Doğru sınıf `k` için kayıp `L = −ln pₖ` olsun. Bölüm 51.10'da türettiğimiz sonuç şudur:

∂L / ∂zᵢ = pᵢ − yᵢ

Burada `y` tek sıcak (one-hot) etiket vektörüdür. Bu sadelik, sinir ağlarında çıkış katmanındaki hatanın neden "tahmin eksi gerçek" olduğunu açıklar ve Bölüm 63'te geri yayılımın ilk adımı olur. Matris kalkülüsü tablosundaki altıncı kural budur.

Bu gradyanı sayısal olarak da denetleyebilirsin. Çıktı bölümünde `dL/dz = p − y` satırı `10⁻¹⁰` mertebesinde hata verir. Softmax'ın kendisi taşmaya açıktır; bunu 55.13'te, log-sum-exp hilesiyle birlikte göreceğiz.


## 55.7 Türev alma yolları: sembolik, sayısal ve otomatik

Bir fonksiyonun türevini bilgisayara yaptırmanın üç yolu vardır ve hepsini bilmek gerekir. Sembolik türev, türevi bir cebir sistemi gibi kapalı bir ifade olarak üretir. Sayısal türev, bir değeri küçük adımlarla yaklaşık olarak hesaplar. Otomatik türev ise programın çalıştırılması sırasında her aritmetik işlemin yerel türevini zincir kuralıyla birleştirir.

Sembolik türev en "temiz" sonucu verir: `d/dx sin(x²) = 2x cos(x²)` gibi bir ifade elde edersin ve bunu istediğin nokta için değerlendirirsin. Ama büyük ifadelerde ifade şişer. Bir sinir ağının kaybını sembolik olarak yazıp türevini almak, parametre sayısı arttıkça hem yavaş hem de okunmaz bir sonuç verir. Sembolik türev bu yüzden küçük ve kapalı problemlerde değerlidir.

Sayısal türev, kaybı her parametre için ayrı ayrı değerlendirir. Bölüm 55.1'deki merkezi fark bunun en basit biçimidir. Uygulaması kolaydır ve herhangi bir kodla çalışır; ama bir hata kaynağı vardır: `h` çok büyükse kesme hatası, çok küçükse yuvarlama hatası baskın olur. Parametre sayısı `n` olduğunda merkezi fark `2n` kaybı değerlendirmesi gerektirir. Bir ağın milyonlarca parametresi için bu kabul edilemez.

Otomatik türev, bu iki uçun ortasında yer alır. Ne sembolik bir ifade üretir ne de `h` seçmeye ihtiyaç duyar. Programı çalıştırırken her işlemin girdilerini ve yerel türevini bir hesap grafiğinde kaydeder, sonra bu kaydı geriye doğru tarar. Sonuç makine kesinliğinde bir sayıdır ve maliyet, programın bir kez çalıştırılmasıyla orantılıdır. Bu bölümde yazacağımız motor bu yöntemin ters mod biçimidir.

Şekil 55.3 üç yöntemi özetliyor. Tablodaki maliyet sütunu, `n` girdi için yaklaşık sayım verir: ileri fark `n + 1` geçiş, merkezi fark `2n` değerlendirme gerektirir. Ters modda ise skaler bir çıktı için bir ileri ve bir geri geçiş yeterlidir. Son satırdaki "kontrol akışı ile uyumlu" ifadesi önemlidir: bir `if` ya da döngü içeren bir program için otomatik türev, çalıştırılan dalın türevini verir. Bunu 55.14'te ayrıca ele alacağız.

![Şekil 55.3: Sembolik, sayısal ve otomatik türevin karşılaştırması](gorseller/b55_turev_yontemleri.png)

Bu üç yöntemin farkını somut görmek için Çözümlü Örnek 2'de bir hesap grafiğinin geri geçişini elle izleyip sayısal türevle karşılaştıracağız. Şimdilik tablonun mantığını kavra: otomatik türev, sayısal türevin esnekliğini ve sembolik türevin doğruluğunu birlikte taşımaya çalışır.

## 55.8 Hesap grafiği: ifadeyi düğümler ve kenarlar olarak görmek

Bir ifadeyi, her işlemi bir düğüm ve her girdi-çıktı ilişkisini bir kenar olarak gösteren bir graf biçiminde düşünebiliriz. Bu graf yönlüdür ve döngü içermez; buna hesap grafiği (computation graph) denir. Bölüm 37'de derleyicinin ifadeleri ağaç biçimindeki AST ile temsil ettiğini gördün. Hesap grafiği de bir ağaca benzer, ama aynı alt ifade birden fazla yerde kullanılabildiği için genellikle bir DAG (yönlü çevrimsiz graf) olur.

Bu ayrım önemlidir. Bir değer birden fazla yerde kullanıldığında grafın bir düğümü birden fazla çocuğa sahip olur. Gradyanı doğru hesaplamak için bu paylaşımı hesaba katmak gerekir; Bölüm 55.10'da bunun hatalı biçimini göstereceğiz.

Bir hesap grafiğinde iki geçiş vardır. İleri geçiş, girdilerden başlayıp her düğümün değerini hesaplar ve sonunda kayıp değerini verir. Geri geçiş, çıkıştan başlayıp her düğüm için gradyanı hesaplar. Geri geçişin sırası topolojik sıralamadır: bir düğümün gradyanı, kendisini kullanan bütün düğümlerden gelen katkılar toplandıktan sonra tamamlanır. Topolojik sıralamayı Bölüm 17.3'te DFS ile kurmuştuk; motorda da aynı yöntemi kullanacağız.

Şekil 55.4, `f(a, b) = (a + b) · tanh(a · b)` ifadesinin hesap grafiğini gösteriyor. Girdiler `a = 1,0` ve `b = 0,5` alınmış, her düğümde ileri geçişten gelen değer (veri) ve geri geçişten gelen gradyan (grad) yazılmıştır. Gradyanlar, bu noktada `∂f/∂a = 1,051953` ve `∂f/∂b = 1,641789` olarak bulunmuştur. Bu değerleri Çözümlü Örnek 2'de elle izleyeceksin.

![Şekil 55.4: f = (a + b) tanh(ab) hesap grafiği; değer ve gradyan etiketleriyle](gorseller/b55_hesap_grafi.png)

Bir hesap grafiğinde her düğüm üç şey bilir: kendi değerini, girdilerini ve kendi yerel türevini kullanarak çocuklarına gradyan dağıtma kuralını. Motorumuzda bu üç şey tek bir sınıfın içinde yaşayacak. Hesap grafiğinin mantığını daha somut görmek için, aşağıdaki fonksiyon grafı kurar ve geri geçişi çalıştırır. Düğümleri sınıf olarak tanımlayacağımız için bu fonksiyon şimdilik yalnızca bir kullanım örneğidir; sınıfın kendisi 55.10'da gelecek.

```python
def ileri_geri(a0, b0):
    a = Deger(a0)            # girdi düğümleri
    b = Deger(b0)
    c = a * b                # c = a b
    t = c.tanh()             # t = tanh(c)
    s = a + b                # s = a + b
    f = s * t                # f = s t
    f.geri()
    return [("a", "girdi", a), ("b", "girdi", b), ("c", "a*b", c),
            ("t", "tanh", t), ("s", "a+b", s), ("f", "s*t", f)]
```

## 55.9 İleri mod ve ters mod: hangisi ne zaman daha ucuz?

Otomatik türevin iki yönü vardır. İleri mod, girdilerden başlayarak tek bir girdinin "teğet" değerini ilerletir. Ters mod, çıkıştan başlayarak tek bir çıktının gradyanını geriye taşır. İkisi de zincir kuralının aynısıdır; farkları, hangi yönde bir geçişin kaç çıktı ya da girdi için yeterli olduğudur.

İleri modu, ikili sayılar (dual numbers) ile kurmak en kolay yoldur. Bir `Dual(a, b)` sayısı, `a` değerini ve `b` türevini taşır. Her işlem, değerle birlikte türevi de günceller. Toplama `(a, b) + (c, d) = (a + c, b + d)` ile yapılır. Çarpma çarpım kuralıyla `(a, b) · (c, d) = (ac, ad + bc)` olur. Bu, tek bir girdi için türevi bir geçişte verir.

```python
class Dual:
    def __init__(self, a, b=0.0):
        self.a = float(a)
        self.b = float(b)

    def __repr__(self):
        return f"Dual({self.a:.4f}, {self.b:.4f})"

    @staticmethod
    def _sar(x):
        return x if isinstance(x, Dual) else Dual(x)

    def __add__(self, diger):
        d = self._sar(diger)
        return Dual(self.a + d.a, self.b + d.b)

    def __mul__(self, diger):
        d = self._sar(diger)
        # Çarpım kuralı: (uv)' = u'v + uv'
        return Dual(self.a * d.a, self.a * d.b + self.b * d.a)
```

Üstel ve tanh gibi fonksiyonlar da aynı kalıpla yazılır. Aşağıdaki `exp` tanımı, değeri ve `eᵃ · b` türevini birlikte döndürür.

```python
def exp(x):
    e = math.exp(x.a)
    return Dual(e, e * x.b)
```

İleri modun Jacobian'ı, her girdi sütunu için bir geçişle hesaplanır. Yani `n` girdi için `n` ileri geçiş yapılır. Ters mod ise her çıktı satırı için bir geri geçiş yapar; `m` çıktı için `m` geri geçiş. Bir sinir ağında kayıp skaler (`m = 1`) olduğundan ters mod tek bir geri geçişle gradyanı verir. Parametre sayısı `n` milyonlarsa ileri mod bu yüzden pratik değildir. Şekil 55.5 bu maliyet farkını gösteriyor: ileri modun geçiş sayısı `n` ile büyürken ters modun geçiş sayısı yalnızca `m` ile büyür.

![Şekil 55.5: İleri mod ve ters modun geçiş sayısı; girdi sayısına göre](gorseller/b55_ileri_ters_maliyet.png)

Bu iki yöntemi aynı fonksiyon üzerinde karşılaştıralım. `f : ℝ³ → ℝ²` olan `f(x) = (x₁x₂ + eˣ³, x₂² x₃)` için Jacobian'ı üç yolla hesaplayan `jakobiyen.py` dosyasının ilgili parçası, ters mod için şöyledir. Çıktı başına bir geri geçiş yapılır ve her geri geçişten önce önceki geçişin gradyanları silinir.

```python
def jakobiyen_ters(f, x):
    # Bir ileri geçiş, sonra çıktı başına bir geri geçiş.
    xs = [Deger(v) for v in x]
    ys = f(xs)
    J = []
    for y in ys:
        # Önceki geri geçişin gradyanlarını sil. Yapraklar (xs) her
        # çıktıda okunduğu için, bağlı olmasalar bile silinir.
        for v in topo(y) + xs:
            v.grad = 0.0
        y.geri()
        J.append([v.grad for v in xs])
    return J
```

Dikkat et: bir geri geçişten önce yalnızca o çıktının alt grafının düğümleri değil, yaprakların da gradyanı silinir. Çünkü `x₁` yaprağı ilk çıktıya bağlıdır, ikinciye bağlı değildir; silinmezse ilk geçişten kalan gradyanı ikinci satırda da okuruz. Bu küçük ayrıntı, Jacobian'ın ikinci satırında ilk denemede ortaya çıkan yanlış değerin kaynağıydı.

```term
$ python jakobiyen.py
ileri mod (n = 3 geçiş):
   ['2.000000', '1.000000', '1.648721']
   ['0.000000', '2.000000', '4.000000']
ters mod  (1 ileri + m = 2 geri geçiş):
   ['2.000000', '1.000000', '1.648721']
   ['0.000000', '2.000000', '4.000000']
sayısal fark:
   ['2.000000', '1.000000', '1.648721']
   ['0.000000', '2.000000', '4.000000']
en büyük fark (ileri, ters, sayısal): 1.40e-10
```

Çıktıda üç yöntem de aynı Jacobian'ı verir ve farkları `10⁻¹⁰` mertebesindedir. İleri mod üç geçiş (n = 3), ters mod bir ileri ve iki geri geçiş (m = 2) yaptı. Bu sayılar küçük bir örnekte farkı göstermeye yeter; asıl fark, girdi sayısı milyonlara çıktığında belirir.

## 55.10 Kendi autodiff motorun: Deger

Şimdi motoru yazıyoruz. Tasarım, Andrej Karpathy'nin micrograd projesinden ilham alır ve kitaptaki sürüm kendi kodumuzdur. Temel birim `Deger` sınıfıdır. Her `Deger` dört şey tutar: sayısal değeri (`veri`), gradyanı (`grad`), kendisini üreten işlemin geri yayılım adımını (`_geri`) ve girdilerini (`_ebeveynler`). İşlemlerin her biri yeni bir `Deger` döndürür ve bu yeni düğüm, girdilerine bağlanmış olur. Böylece bir ifadeyi kullandıkça hesap grafiği kendiliğinden kurulur.

Gradyan birikiminin neden gerektiğini Şekil 55.6 gösteriyor. Bir düğümün gradyanı, onu kullanan her yoldan gelen katkıların toplamıdır. Şekildeki `a` düğümü iki yoldan katkı alır: `m = a · b` üzerinden 3 ve doğrudan `f = m + a` üzerinden 1. Toplam 4'tür.

![Şekil 55.6: Gradyan birikimi: paylaşılan a düğümü iki yoldan katkı alır](gorseller/b55_gradyan_birikimi.png)

Önce modülün başlangıcı: gradyan birikimini yöneten `_ekle` yardımcı fonksiyonu ve topolojik sıralama. `BIRIKIR` bayrağı deneyler için vardır; bu bayrak `True` iken gradyanlar toplanır, `False` iken üzerine yazılır. Doğru davranış `True`dur. `False` yapmak, Çözümlü Örnek 4'te göstereceğimiz hatanın bilerek yeniden üretilmesini sağlar.

```python
# deger.py: skaler ters mod otomatik türev motoru (micrograd tarzı).
# Her Deger bir sayı (veri), onun gradyanı (grad), kendisini üreten
# işlemin geri yayılım adımı (_geri) ve girdileri (_ebeveynler) tutar.
import math

# Deney anahtarı. True: gradyan birikir (+=), doğru davranış.
# False: gradyan üzerine yazılır (=), bilerek yapılan hatalı sürüm.
BIRIKIR = True


def _ekle(dugum, g):
    # Gradyan katkısını düğüme ekler. Aynı düğüm birden fazla yoldan
    # kullanılıyorsa katkılar toplanır (çok değişkenli zincir kuralı).
    if BIRIKIR:
        dugum.grad += g
    else:
        dugum.grad = g


def topo(kok):
    # Bölüm 17.3'teki DFS tabanlı topolojik sıralama: bir düğüm,
    # girdilerinin hepsinden sonra gelir.
    sira, ziyaret = [], set()

    def dfs(v):
        if v in ziyaret:
            return
        ziyaret.add(v)
        for e in v._ebeveynler:
            dfs(e)
        sira.append(v)

    dfs(kok)
    return sira
```

Sınıfın kurucusu ve iki temel işlem, toplama ve çarpma, aşağıdadır. Dikkat et: her işlemin geri adımı, yerel türevi çıkışın gradyanıyla çarpıp girdilere `_ekle` ile ekler. Toplamanın yerel türevi 1, çarpmanın yerel türevi karşı girdidir.

```python
class Deger:
    def __init__(self, veri, ebeveynler=(), islem=""):
        self.veri = float(veri)
        self.grad = 0.0
        self._geri = lambda: None
        self._ebeveynler = tuple(ebeveynler)
        self._islem = islem

    def __repr__(self):
        return f"Deger({self.veri:.4f}, grad={self.grad:.4f})"

    @staticmethod
    def _sar(x):
        return x if isinstance(x, Deger) else Deger(x)

    def __add__(self, diger):
        diger = self._sar(diger)
        cikis = Deger(self.veri + diger.veri, (self, diger), "+")

        def _geri():
            _ekle(self, cikis.grad)
            _ekle(diger, cikis.grad)
        cikis._geri = _geri
        return cikis

    def __mul__(self, diger):
        diger = self._sar(diger)
        cikis = Deger(self.veri * diger.veri, (self, diger), "*")

        def _geri():
            _ekle(self, diger.veri * cikis.grad)
            _ekle(diger, self.veri * cikis.grad)
        cikis._geri = _geri
        return cikis
```

Üs, üstel, logaritma ve tanh işlemleri de aynı kalıbı izler. Her biri değerini hesaplar, yerel türevini bilir ve geri adımını tanımlar. Üs alma için kural `n · xⁿ⁻¹`dir; üstel için türev kendisidir; logaritma için `1/x`tir.

```python
    def __pow__(self, n):
        # Yalnızca sabit (int/float) üs desteklenir.
        assert isinstance(n, (int, float))
        cikis = Deger(self.veri ** n, (self,), f"**{n}")

        def _geri():
            _ekle(self, n * self.veri ** (n - 1) * cikis.grad)
        cikis._geri = _geri
        return cikis

    def exp(self):
        e = math.exp(self.veri)
        cikis = Deger(e, (self,), "exp")

        def _geri():
            _ekle(self, e * cikis.grad)
        cikis._geri = _geri
        return cikis

    def log(self):
        cikis = Deger(math.log(self.veri), (self,), "log")

        def _geri():
            _ekle(self, cikis.grad / self.veri)
        cikis._geri = _geri
        return cikis
```

ReLU ve tanh için geri adımlar aşağıdadır. Ardından `geri` metodu gelir: topolojik sırayı kurar, çıkış gradyanını 1 yapar ve düğümleri ters sırada çalıştırır. Son olarak eksi, çıkarma ve bölme gibi işlemler, bunları üç temel işleme indirgeyerek tanımlanır. Bu indirgeme önemlidir: yeni bir yerel türev yazmak yerine yalnızca toplama, çarpma, üs, üstel, logaritma ve tanh bilmek yeter.

```python
    def tanh(self):
        t = math.tanh(self.veri)
        cikis = Deger(t, (self,), "tanh")

        def _geri():
            _ekle(self, (1 - t * t) * cikis.grad)
        cikis._geri = _geri
        return cikis

    def relu(self):
        cikis = Deger(max(0.0, self.veri), (self,), "relu")

        def _geri():
            _ekle(self, float(cikis.veri > 0) * cikis.grad)
        cikis._geri = _geri
        return cikis

    def geri(self):
        # Çıkıştan girdilere doğru her düğümün _geri adımını çalıştır.
        sira = topo(self)
        self.grad = 1.0          # d(self)/d(self) = 1
        for v in reversed(sira):
            v._geri()
```

```python
    def __neg__(self):
        return self * -1

    def __radd__(self, diger):
        return self + diger

    def __sub__(self, diger):
        return self + (-self._sar(diger))

    def __rsub__(self, diger):
        return self._sar(diger) + (-self)

    def __rmul__(self, diger):
        return self * diger

    def __truediv__(self, diger):
        return self * self._sar(diger) ** -1

    def __rtruediv__(self, diger):
        return self._sar(diger) * self ** -1
```

`geri` metodunda dikkat etmen gereken iki satır vardır. Birincisi `self.grad = 1.0`: çıkışın kendisine göre türevi 1'dir. İkincisi döngünün ters sırada çalışmasıdır: bir düğümün gradyanı tam olarak hesaplanmadan kendi geri adımı çalışmamalıdır. Topolojik sırada ters gidince bu garanti edilir.

Motoru denetlemek için her işlemin türevini, Bölüm 50.3'teki merkezi farkla karşılaştıran `grad_kontrol.py` dosyası yazdık. Önce her işlemi tek tek, sonra 300 rastgele ifadeyi sınarız. Rastgele ifadeler, sabit tohumlu bir program üreticisiyle oluşturulur: her adım iki önceki değeri bir işlemle birleştirir.

```python
def calistir(prog, girdi):
    deger = list(girdi)
    for op, i, j in prog:
        a, b = deger[i], deger[j]
        if op == "+":
            c = a + b
        elif op == "-":
            c = a - b
        elif op == "*":
            c = a * b
        elif op == "tanh":
            c = tanh_(a)
        elif op == "relu":
            c = relu_(a)
        else:
            c = a ** 2
        deger.append(c)
    return deger[-1]
```

```term
$ python grad_kontrol.py
ifade            otomatik      sayisal       hata
x0 + x1          1.000000     1.000000    1.4e-10
x0 * x1          1.300000     1.300000    9.1e-11
x0 / x1          0.769231     0.769231    2.5e-11
x0 ** 3          1.470000     1.470000    2.1e-11
tanh(x0)         0.634740     0.634740    7.3e-11
exp(x0)          2.013753     2.013753    2.2e-12
log(x0)          1.428571     1.428571    1.8e-11
relu(x0-1)       0.000000     0.000000    0.0e+00
sigmoid(x0)      0.221713     0.221713    1.0e-11

rastgele ifade sayisi: 300
en buyuk goreli hata: 2.22e-10
1e-6 esigini asan    : 0
```

Çıktının ilk bölümünde her işlemin `x₀` girdisine göre türevi, otomatik ve sayısal olarak yazılmıştır. Hata sütunu göreli farkı verir ve hepsi `10⁻¹⁰` mertebesindedir. İkinci bölümde 300 rastgele ifadenin en büyük göreli hatası `2,22·10⁻¹⁰`dur ve `10⁻⁶` eşiğini aşan yoktur. Bu sonuç motorun ve türev kurallarının tutarlı olduğunu gösterir; hatanın küçük olması, sayısal türevin de yuvarlama hatası taşıdığını unutmamamız gerektiğini hatırlatır.

Bu motor, yorumlarla birlikte yaklaşık 140 satırdır ve gerçek bir sinir ağını eğitmeye yeter. Ama bir kısıtı var: her skaler işlem bir Python nesnesi üretir. Bu, yavaştır ve büyük veride kullanılamaz. Bu konuyu 55.12'de ölçeceğiz.

## 55.11 Motoru MLP ile eğitmek

Şimdi motorla gerçek bir öğrenme problemi çözeceğiz. Veri, iç içe iki yarım aydan oluşan sentetik bir sınıflandırma kümesidir. Bu küme doğrusal olarak ayrılamaz; yani tek bir doğrusal sınır yetmez. Bu nedenle en az bir gizli katman gerekir. Veri, sabit tohumlu bir üreteçle oluşturulur ve 80 nokta içerir.

Ağ mimarisi `[2, 8, 8, 1]`dir: iki girdi, iki gizli katman (her biri 8 birim, tanh etkinleştirmeli) ve tek çıkış (doğrusal). Toplam 105 parametre vardır. Kayıp ortalama kare hatadır ve etiketler `+1` ya da `−1`dir. Önce bir nöron, sonra katman ve ağ sınıflarını yazıyoruz; her biri `Deger` üzerinde çalışır.

```python
class Noron:
    def __init__(self, w, b, tanh_mi):
        self.w = [Deger(v) for v in w]
        self.b = Deger(b)
        self.tanh_mi = tanh_mi

    def __call__(self, x):
        z = sum((wi * xi for wi, xi in zip(self.w, x)), self.b)
        return z.tanh() if self.tanh_mi else z
```

```python
class Katman:
    def __init__(self, W, b, tanh_mi):
        giris = len(W)
        self.noronlar = [Noron([W[i][j] for i in range(giris)],
                               b[j], tanh_mi)
                         for j in range(len(b))]

    def __call__(self, x):
        return [n(x) for n in self.noronlar]
```

```python
class MLP:
    # katmanlar: [(W, b), ...]. Gizli katmanlar tanh, çıkış doğrusal.
    def __init__(self, katmanlar):
        son = len(katmanlar) - 1
        self.katmanlar = [Katman(W, b, k < son)
                          for k, (W, b) in enumerate(katmanlar)]

    def __call__(self, x):
        for k in self.katmanlar:
            x = k(x)
        return x

    def parametreler(self):
        p = []
        for k in self.katmanlar:
            for n in k.noronlar:
                p.extend(n.w)
                p.append(n.b)
        return p
```

Ağın kaybı ortalama kare hatadır. Her örnek için çıkışla etiket arasındaki farkın karesi alınır, ardından ortalaması hesaplanır. Bu kayıp da bir `Deger` olduğu için geri geçiş onu da kapsar.

```python
def kayip(model, X, Y):
    # Ortalama kare hata: (1/N) sum (out - y)^2
    toplam = Deger(0.0)
    for x, y in zip(X, Y):
        out = model(x)[0]
        toplam = toplam + (out - y) ** 2
    return toplam * (1.0 / len(X))
```

Eğitim döngüsü dört adımdan oluşur. Önce kaybı hesaplarız. Sonra her parametrenin gradyanını sıfırlarız; bu adım kritiktir, çünkü gradyanlar her geri geçişte birikir ve bir önceki dönemin değerleri kalırsa yanlış bir yön izlenir. Üçüncü olarak geri geçişi çalıştırırız. Son olarak her parametreyi gradyanın tersine `η` kadar kaydırırız.

```python
def egit(katmanlar, X, Y, donem, ogrenme_orani):
    model = MLP(katmanlar)
    params = model.parametreler()
    gecmis = []
    for _ in range(donem):
        L = kayip(model, X, Y)
        # gradyanlar birikir; her dönem sıfırlanır
        for p in params:
            p.grad = 0.0
        L.geri()
        # gradyan inişi: w <- w - eta * dL/dw
        for p in params:
            p.veri -= ogrenme_orani * p.grad
        gecmis.append(L.veri)
    return model, gecmis
```

Eğitimi 600 dönem, öğrenme oranı `0,1` ile çalıştırdık. Aşağıdaki çıktı kaybın dönemlere göre nasıl düştüğünü ve sonunda **eğitim** doğruluğunun `%98,8` olduğunu gösteriyor. Kayıp ilk dönemde `0,9965`ten başlayıp `0,0691`e iner.

```term
$ python mlp_skaler.py
parametre sayisi: 105
donem   0  kayip 0.996547
donem 100  kayip 0.206237
donem 200  kayip 0.189168
donem 300  kayip 0.165988
donem 400  kayip 0.133932
donem 500  kayip 0.093674
donem 599  kayip 0.069071
son kayip 0.069071, dogruluk 0.988
```

Bu sayı eğitim verisi üzerindedir ve Bölüm 54'ün kuralına göre tek başına bir başarı iddiası değildir: model bu 80 noktayı görerek öğrendi. Ağın ezberleyip ezberlemediğini görmek için aynı dağılımdan, farklı tohumla 1000 yeni nokta üretip yalnızca ölçüm için kullanıyoruz. Aşağıdaki program, bölümdeki vektörel eğitim fonksiyonunu aynı ayarlarla çağırır:

```python
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
```

Çıktı, eğitim ile test doğruluğunun birbirine yakın olduğunu gösteriyor; yani bu küçük ağ yarım ay sınırını ezberlemek yerine genellemiş:

```term
$ python test_dogruluk.py
egitim dogrulugu (80 nokta):  0.988
test dogrulugu   (1000 nokta): 0.967
```

İki sayı arasındaki 2 puanlık fark beklenen bir şeydir: eğitim noktaları modele tanıdıktır. Bu bölümün amacı otomatik türev motorunun çalıştığını göstermekti; modeli gerçekten değerlendirmenin tüm disiplini (çapraz doğrulama, güven aralığı) Bölüm 57'dedir.

Şekil 55.7 kayıp eğrisini gösteriyor. Kayıp ilk yüz dönemde hızla yaklaşık `0,2`ye iner, sonra bir süre plato çizer ve 400. dönemden sonra yeniden belirgin biçimde düşer. Bu plato, tam bir kesinlik kanıtı değildir; ağın önce kaba bir ayrımı bulup sonra ince yapıyı öğrendiğini düşündüren bir gözlemdir. Ölçüm olarak kesin olan, eğrinin tek bir çalıştırmada monoton azaldığı ve son değerin `0,069071` olduğudur. Daha uzun eğitimle kaybın daha da düşmesi beklenir, ama bu bölümde bunu ölçmedik.

![Şekil 55.7: Kendi motorla eğitilen MLP'nin kayıp eğrisi](gorseller/b55_kayip_egrisi.png)

Şekil 55.8 eğitilmiş ağın karar sınırını gösteriyor. Ağın çıkışı sıfırı geçen eğri, iki yarım ayı birbirinden ayıran sınırdır. Bu sınır doğrusal değildir; ağın gizli katmanları bu eğriliği sağlar. İki yarım ay, tek bir doğru ile tam olarak ayrılamayacak biçimde iç içe geçmiştir. Bu yüzden doğrusal bir model bu veride bir tavan doğruluğa takılır; bu bölümde o modeli ayrıca eğitmedik, ama şekle bakınca neden yetersiz kalacağı açıktır.

![Şekil 55.8: Kendi motorla eğitilen MLP'nin karar sınırı ve eğitim verisi](gorseller/b55_karar_siniri.png)

Burada önemli bir gözlem var. Bu ağın tüm parametre gradyanları, bir kez çalıştırılan geri geçişle hesaplanır. Motor, kendi kurduğu hesap grafiği üzerinde bir zincir kuralı taraması yapar; başka bir sihir yoktur. Bu, Bölüm 63'te NumPy ile yazacağımız tam MLP'nin kavramsal olarak aynısıdır.

## 55.12 Vektörleştirilmiş geri yayılım

Skaler motor doğru ama yavaştır. Her skaler işlem bir Python nesnesi yaratır ve her geri adım bir fonksiyon çağrısıdır. Aynı hesabı bir matris çarpımıyla yaparsak, işi NumPy'ın C kodu yapar ve her katman tek bir büyük işlemle çalışır. Bu bölüm, aynı ağı bu kez elle türetilmiş matris gradyanlarıyla yazar ve iki sürümü karşılaştırır.

Matris biçiminde ağın ileri geçişi, her katmanda girdi matrisini ağırlıkla çarpıp sapmayı ekler ve etkinleştirme uygular. Geri geçişin formülleri, 55.5'te türettiğimiz kurallardan gelir. Her katmanda `d = dL/dz` (önceki katmanın doğrusal çıktısının kayıp gradyanı) tutulur. Ağırlık gradyanı `dW = girdiᵀ d`, sapma gradyanı `db = ∑ d` olur. Bir önceki katmana aktarılan gradyan `d Wᵀ`dır ve tanh'ın türevi `1 − a²` ile çarpılır.

```python
def kayip_ve_gradyan(katmanlar, X, Y):
    # Geri yayılım: d = dL/dz; dW = girdi^T d, db = sum d.
    N = X.shape[0]
    A = ileri(katmanlar, X)
    out = A[-1]
    L = np.mean((out - Y) ** 2)
    d = 2.0 * (out - Y) / N                  # dL/dout, şekil (N, 1)
    grad = [None] * len(katmanlar)
    for k in reversed(range(len(katmanlar))):
        W, _ = katmanlar[k]
        grad[k] = (A[k].T @ d, d.sum(axis=0))
        if k > 0:
            # dL/d(girdi) = d W^T; tanh'nin türevi 1 - a^2
            d = (d @ W.T) * (1.0 - A[k] ** 2)
    return L, grad
```

Kod, Bölüm 55.5'teki şekil düşüncesini doğrudan kullanır: `dW` her zaman `W` ile aynı şekildedir, çünkü `girdiᵀ` (girdi × örnek) ile `d` (örnek × çıktı) çarpımı girdi × çıktı verir. Bu kontrol, bir matris çarpım sırasının yanlış olduğunu hemen gösterir.

Vektörel sürümün doğruluğunu, skaler motorla aynı başlangıç ağırlıklarında karşılaştırarak sınadık. İlk kayıp ve ilk gradyanlar, `10⁻¹⁶` mertebesinde bir farkla aynıdır. Sonra iki sürümü 600 dönem boyunca eğittik; sonunda ağırlıklar yine `10⁻¹⁵` mertebesinde aynıdır. Bu, iki yöntemin aynı matematiği yaptığının sayısal kanıtıdır.

```term
$ python vektor.py
ilk kayip: vektor 0.9965468155, skaler 0.9965468155
gradyan en buyuk fark: 1.39e-16
son kayip: vektor 0.069071, skaler 0.069071
600 donem sonunda en buyuk agirlik farki: 1.22e-15
skaler donem suresi  : 0.1390 s
vektor donem suresi  : 0.000062 s
hiz orani            : 2238 kat
vektor modelin dogrulugu: 0.988
```

Çıktıdaki hız satırları en önemli ölçümdür. Skaler motorun bir dönemi yaklaşık `0,14` saniye sürdü; vektörel sürümün bir dönemi `0,00006` saniye. Oran bu çalıştırmada yaklaşık 2200 kattır. Bu sayı makineye, Python sürümüne ve o anki sistem yüküne bağlıdır; senin makinende farklı çıkacaktır. Önemli olan, fark büyüklüğünün basamak düzeyinde ve yönünün aynı olmasıdır.

Şekil 55.9 aynı sonucu grafikte gösteriyor. Log ölçekte iki çubuk arasındaki mesafe, skaler motorun neden büyük ağlarda kullanılamadığını açıkça gösterir.

![Şekil 55.9: Aynı MLP'nin skaler ve vektörel dönem süreleri (log ölçek)](gorseller/b55_hiz.png)

Bu köprü, Bölüm 63'te sıfırdan yazacağın tam MLP'nin iskeletidir. Bölüm 56'da NumPy'ın vektörleştirme ve yayınlama (broadcasting) kurallarını derinlemesine göreceksin; bu bölümdeki `W.T`, `sum(axis=0)` ve eleman bazlı çarpımların her biri o kuralların uygulamasıdır.

## 55.13 Sayısal tuzaklar: kaybolan gradyan, taşma ve log(0)

Türevi doğru formüllerle hesaplamak yetmez; sayılar bilgisayarda sınırlı kesinlikle temsil edilir. Bu bölümde üç tuzak görüyoruz. Birincisi, uzun bir zincirde çarpımın sıfıra gitmesi. İkincisi, üstel fonksiyonun taşması. Üçüncüsü, logaritmanın sıfırda tanımsız olması.

Kaybolan gradyan, zincir kuralının doğal sonucudur. Her katman, gradyanı bir çarpanla çarpar. Sigmoid için bu çarpan `σ′ ≤ 0,25` olduğundan, `n` katmandan sonra gradyan en fazla `0,25ⁿ` ile sınırlıdır. Aşağıdaki fonksiyon `h₀ = x` ve `hₖ = σ(hₖ₋₁)` zincirini kurar ve ters modla `dhₙ/dx`i hesaplar.

```python
def sigmoid(z):
    return 1 / (1 + (-z).exp())


def zincir(x0, derinlik):
    x = Deger(x0)
    h = x
    carpim = 1.0
    for _ in range(derinlik):
        h = sigmoid(h)
        carpim *= h.veri * (1 - h.veri)   # sigma'(z) = s (1 - s)
    h.geri()
    return x.grad, carpim
```

Aşağıdaki çıktı, `x = 0,5` için bazı derinlikleri gösteriyor. Tam çıktı 30 derinliğin hepsini CSV'ye yazar; Şekil 55.10 o veriyi çizer. Gradyan, on katmanda `10⁻⁷`, otuz katmanda `10⁻²⁰` mertebesine iner. Otomatik ve elle çarpılmış değerler aynıdır; yani motor doğru çalışıyor, sorun formülün kendisindedir.

```term
$ python kaybolan.py
derinlik       otomatik         carpim
       1     2.3500e-01     2.3500e-01
       2     5.3408e-02     5.3408e-02
       3     1.2033e-02     1.2033e-02
       5     6.0799e-04     6.0799e-04
      10     3.4831e-07     3.4831e-07
      15     1.9954e-10     1.9954e-10
      20     1.1431e-13     1.1431e-13
      30     3.7514e-20     3.7514e-20
```

![Şekil 55.10: Sigmoid zincirinde kaybolan gradyan; üst sınır 0,25ⁿ ile birlikte](gorseller/b55_kaybolan_gradyan.png)

Bu sonuç, derin sigmoid ağlarının neden eğitilemediğinin en sade açıklamasıdır. Pratikte bu sorunu hafifletmek için ReLU gibi türevi çarpan olarak büyük kalan etkinleştirmeler, dikkatli başlatma ve normalizasyon kullanılır; bunları Bölüm 64'te eğitim sanatı kapsamında göreceksin. Kalıntı (residual) bağlantılar ise Bölüm 66'da ResNet ile anlatılacak. Burada önemli olan, sorunun türevin kendisinde değil, zincirin uzunluğunda ve çarpanların boyutunda olduğunu görmektir.

Taşma ve log(0) tuzakları ise softmax ve çapraz entropide ortaya çıkar. Aşağıdaki fonksiyonlar naif softmax ve log-sum-exp hilesini içerir. Log-sum-exp, en büyük logiti çıkarır: `softmax(z) = softmax(z − m)` eşitliği her zaman doğrudur, çünkü `m` her bileşenden aynı miktarda çıkarılır ve pay ile paydada sadeleşir. Bölüm 51.10'da bunu bilgi teorisi bağlamında görmüştük.

```python
def softmax_naif(z):
    e = np.exp(z)                       # büyük z'de taşar
    return e / e.sum()


def lse(z):
    m = max(z)                          # en büyük değeri çıkar
    return m + math.log(sum(math.exp(v - m) for v in z))
```

```term
$ python sayisal_tuzak.py
math.log(0.0): ValueError: math domain error
np.log(0.0)  : -inf
math.exp(1000): OverflowError: math range error
naif softmax : [nan nan nan]
kararli      : [0.665241 0.244728 0.090031]
p (naif)     : [1. 0.]  -log p_y = inf
lse tabanli  : L = 800.0
```

Çıktı üç tuzağı gösteriyor. `math.log(0.0)` bir `ValueError` fırlatır, `np.log(0.0)` ise sessizce `-inf` döndürür; ikisi de sorunludur. Naif softmax `[1000, 999, 998]` için `nan` üretir, çünkü `e¹⁰⁰⁰` taşar. Kararlı biçim ise doğru olasılıkları `[0,665241; 0,244728; 0,090031]` verir. Son satırda naif çapraz entropi `inf` üretir, oysa log-sum-exp ile hesaplanan kayıp `800` olur. Bu fark, bir eğitim döngüsünde kaybın bir anda `inf`'e çıkmasının nedenidir.

Bu tuzaklardan kaçmanın ilk kuralı şudur: softmax ve logaritmayı asla birbirinden ayrı yazma. Kayıp fonksiyonunu log-sum-exp biçiminde yaz ve gradyanı `p − y` olarak türet. Bu iki kural, `nan` ve `inf` hatalarının büyük kısmını önler.

## 55.14 Gerçek autodiff sistemleri, kontrol akışı ve ikinci dereceden türev

Bu bölümde yazdığımız motor, gerçek sistemlerin özünü taşır ama onlar çok daha büyük ve hızlıdır. Bu alt bölümde o sistemlerin farklarını kavramsal olarak özetliyoruz. Bu kısımdaki bilgilerin çoğu genel bilgidir ve kitabın kendi ölçümü değildir; resmi belgeleri okuyarak doğrulamanı öneririm.

PyTorch'un autograd sistemi, dinamik bir hesap grafiği kurar: program her çalıştığında grafı yeniden inşa eder. Bu yaklaşıma tanımla-çalıştır (define-by-run) denir ve bizim motorumuzun da yaptığı budur. Bölüm 65'te PyTorch'un tensör düzeyinde nasıl çalıştığını ayrıntılı göreceksin. JAX ise farklı bir yol izler: bir fonksiyonu iz (trace) olarak kaydedip o iz üzerinde dönüşümler (türev, derleme) uygular. İki yaklaşım da zincir kuralını aynı şekilde uygular; fark, grafın ne zaman ve nasıl kurulduğudur.

Kontrol akışı, yani `if` ve döngüler, dinamik grafiklerin doğal avantajıdır. Motorumuz da bir `if` içinden geçen yolu kaydeder ve yalnızca çalıştırılan dalın türevini verir. Bu, sembolik türevin zor yapabildiği bir şeydir. Ancak bir uyarı gerekir: türev, çalıştırılan belirli bir yol için geçerlidir ve `if` koşulu bir süreklilik noktasındaysa türev tanımsız olabilir. ReLU'nun `x = 0`daki durumu bunun küçük bir örneğidir.

Son olarak ikinci dereceden türev. Gradyanın bir daha türevi, Hessian matrisini verir; Bölüm 50.11'de Newton yönteminde bu matrisin rolünü görmüştük. Büyük ağlarda Hessian'ın tamamını kurmak imkânsızdır, ama bir Hessian-vektör çarpımı `Hv` çoğu zaman yeterlidir. Bu çarpım, ileri modun bir geri geçişin üzerine kurulmasıyla (genel bilgi olarak: ileri-üzerine-ters) tek bir geçişe yakın maliyetle hesaplanabilir. Hessian ve ikinci dereceden bilgi, Bölüm 50'deki Newton yöntemi ve eğrilik analizinin devamı olarak ileride yeniden karşına çıkacak.

Bu bölümün sonunda elindeki motor, bu büyük sistemlerin mantığını taşıyor: bir hesap grafiği, bir topolojik sıralama, her düğüm için yerel bir türev ve gradyanların doğru birikmesi. Gerisi mühendislik ölçeğidir.


## Çözümlü Örnekler

Bu bölümdeki dört örnek, zorluk sırasıyla ★, ★★, ★★ ve ★★★ olarak dizilmiştir. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntüyü bul, iyileştir ve doğrula. Doğrulama adımında elle iz sürme tablosu bulunur. Her örnek bir varyasyon sorusuyla biter; bu soruyu yapay zekâ aracı kullanmadan çözmeni bekliyorum.

### Örnek 1 (★): f(x) = sin(x²) türevi: zincir kuralı, elle ve sayısal

`f(x) = sin(x²)` fonksiyonunun türevini zincir kuralıyla elle bul, sonra `x = 1,2` noktasında sayısal olarak doğrula.

**Adım 1 — Anla.** İstenen şey `f′(x)` ifadesidir ve bunun belirli bir noktadaki sayısal değeridir. Elle türev ile merkezi farkın aynı sonucu verdiğini göstermek de gerekir.

**Adım 2 — Örnekle.** `x = 0` noktasında `f′(0)` sıfır olmalı, çünkü `sin(x²)` çift bir fonksiyondur ve bu nedenle `x = 0`da düzdür. `x = 1` için `f′(1) = 2 cos(1) ≈ 1,08060` beklenir. Bu iki kontrol, formülün işaretini ve çarpanını denemek için yeterlidir.

**Adım 3 — Kaba çöz.** İç fonksiyon `u = x²` ve dış fonksiyon `sin u`dur. `h′(x) = 2x` ve `g′(u) = cos u` olduğundan `f′(x) = cos(x²) · 2x` olur. `x = 1,2` için `u = 1,44`, `cos(1,44) ≈ 0,130424` ve `2x = 2,4` olduğundan `f′(1,2) ≈ 0,313017` bulunur.

**Adım 4 — Örüntü.** İki çarpan vardır: dış türev `cos u` iç değere bağlıdır, iç türev `2x` ise doğrusaldır. Zincir kuralının yaptığı şey, bu iki çarpanı doğru noktalarda değerlendirip çarpmaktır. Bu örüntü, 55.13'teki kaybolan gradyanın da çekirdeğidir: her halka bir çarpan katar.

**Adım 5 — İyileştir.** Elle türevin yanlış olma ihtimalini azaltmak için bağımsız bir yol kullanırız: merkezi fark. Bölüm 50.3'teki gibi `h = 10⁻⁶` seçilir, çünkü çift duyarlıkta bu değer kesme ve yuvarlama hatalarını dengeler. Böylece iki sonuç bağımsız iki yoldan gelir.

**Adım 6 — Doğrula.** İz tablosu:

| Adım | Değer |
|---|---|
| u = x² | 1,44 |
| cos(u) | 0,130424 |
| 2x | 2,4 |
| Elle f′ = cos(u) · 2x | 0,313017 |
| Merkezi fark (h = 10⁻⁶) | 0,313017 |
| Fark | 1,7 · 10⁻¹¹ |

Bu değerler Bölüm 55.4'teki `zincir.py` çıktısının ilk bölümüyle birebir tutar. Tablonun son satırı, iki yöntemin uyuştuğunu gösterir.

**Bunu AI'sız yazabilir misin?** `f(x) = cos(x³)` fonksiyonunun `x = 0,8` noktasındaki türevini zincir kuralıyla elle hesapla. Önce `f′(x)` ifadesini yaz, sonra değeri bul ve bir merkezi fark ile doğrula. İşaretin neden negatif çıktığını açıklayabiliyor musun?

### Örnek 2 (★★): f(a, b) = (a + b) tanh(ab) hesap grafiği, ileri ve geri geçiş

`f(a, b) = (a + b) · tanh(a · b)` ifadesi için `a = 1,0` ve `b = 0,5` noktasında hesap grafiğinin ileri değerlerini ve geri gradyanlarını bul. Sonucu sayısal türevle karşılaştır.

**Adım 1 — Anla.** Dört ara düğüm vardır: `c = a·b`, `t = tanh(c)`, `s = a + b`, `f = s·t`. İstenen, `∂f/∂a` ve `∂f/∂b` gradyanlarıdır. Ayrıca her düğümde ileri değerin de yazılması gerekir.

**Adım 2 — Örnekle.** `a = 1, b = 0,5` için `c = 0,5`, `t = tanh(0,5) ≈ 0,462117`, `s = 1,5` ve `f = 1,5 · 0,462117 ≈ 0,693176` olur. İleri geçiş bu kadar basittir; asıl iş geri geçişte.

**Adım 3 — Kaba çöz.** Geri geçiş çıkıştan başlar. `∂f/∂f = 1`. `f = s·t` olduğundan `∂f/∂s = t` ve `∂f/∂t = s`. `t = tanh(c)` için `∂t/∂c = 1 − t²`. `c = a·b` için `∂c/∂a = b` ve `∂c/∂b = a`. `s = a + b` için iki yerel türev de 1'dir.

**Adım 4 — Örüntü.** `a` ve `b` iki yoldan etkiler: bir yol `c` üzerinden `t`ye, diğeri `s` üzerinden doğrudan `f`ye. Gradyan, iki yolun katkılarının toplamıdır. Bu, bu bölümün en önemli ilkesidir ve 55.10'da birikim hatasında yeniden göreceksin.

**Adım 5 — İyileştir.** Her düğümde yalnızca yerel türev ile üstten gelen gradyanı çarpmak yeter. `c`nin gradyanı `1,5 · (1 − t²) = 1,5 · 0,786448 = 1,179672` olur; `a` için katkı `1,179672 · b = 0,589836` ve `b` için katkı `1,179672 · a = 1,179672`dir. Böylece geri geçiş bir kez, sıralı biçimde yürür.

**Adım 6 — Doğrula.** Geri geçiş iz tablosu:

| Düğüm | Yerel türev | Üstten grad | Girdiye katkı |
|---|---|---|---|
| f = s · t | ∂f/∂s = t = 0,462117; ∂f/∂t = s = 1,5 | 1 | s: 0,462117; t: 1,5 |
| t = tanh(c) | 1 − t² = 0,786448 | 1,5 | c: 1,179672 |
| c = a · b | ∂c/∂a = b = 0,5; ∂c/∂b = a = 1 | 1,179672 | a: 0,589836; b: 1,179672 |
| s = a + b | 1 | 0,462117 | a: 0,462117; b: 0,462117 |
| Toplam | | | ∂f/∂a = 1,051953; ∂f/∂b = 1,641789 |

Programın çıktısı ve sayısal türev aynı değerleri verir.

```term
$ python hesap_grafi.py
ad   islem        veri       grad
a    girdi    1.000000   1.051953
b    girdi    0.500000   1.641789
c    a*b      0.500000   1.179672
t    tanh     0.462117   1.500000
s    a+b      1.500000   0.462117
f    s*t      0.693176   1.000000
sayisal: df/da = 1.051953, df/db = 1.641789
```

**Bunu AI'sız yazabilir misin?** `f(a, b) = a · b + tanh(a)` ifadesini `a = 0,5`, `b = 2` noktasında bir hesap grafiği olarak çiz, ileri değeri ve `∂f/∂a`, `∂f/∂b` gradyanlarını bul. Hangi düğüm iki kez katkı alıyor?

### Örnek 3 (★★): Doğrusal katman ve ortalama kare hata: ∂L/∂W şekil düşüncesiyle

`W` 2×3 boyutunda bir matris, `x` 3 boyutlu bir girdi ve `y` 2 boyutlu bir hedef olsun. `W = [[1, 2, 0], [0, 1, −1]]`, `x = (1, 0, 2)` ve `y = (0, 1)` için `L = ‖Wx − y‖²` kaybının `∂L/∂W` gradyanını bul ve şeklini doğrula.

**Adım 1 — Anla.** İstenen `∂L/∂W`dir ve bu matrisin şekli `W` ile aynı, yani 2×3 olmalıdır. Ayrıca kaybın değeri de istenebilir.

**Adım 2 — Örnekle.** Örnek bir `W` elemanı, `W₁₁`, yalnızca çıkışın ilk bileşeni üzerinden kayba etki eder. Bu, gradyanın ilk satırının yalnızca ilk çıktıya bağlı olduğunu söyler.

**Adım 3 — Kaba çöz.** İleri geçiş: `Wx = (1·1 + 2·0 + 0·2, 0·1 + 1·0 − 1·2) = (1, −2)`. Artık `r = Wx − y = (1 − 0, −2 − 1) = (1, −3)` ve `L = 1² + (−3)² = 10`.

**Adım 4 — Örüntü.** `∂L/∂r = 2r` ve `∂r/∂Wᵢⱼ` yalnızca `i`. çıktıya bağlı ve `xⱼ`ye eşittir. Böylece `∂L/∂Wᵢⱼ = 2 rᵢ xⱼ`, yani gradyan `2 r xᵀ` dış çarpımıdır. Şekil kontrolü: `r` 2 boyutlu, `xᵀ` 3 boyutlu, dış çarpım 2×3.

**Adım 5 — İyileştir.** Dış çarpımı her elemanı ayrı hesaplamak yerine tek satırda yazarız. Bu, Bölüm 55.5'teki üçüncü kuralın doğrudan uygulamasıdır. Kontrol için sıfır olan elemanları da işaretleyelim: `x₂ = 0` olduğu için ikinci sütun sıfır olmalı.

**Adım 6 — Doğrula.** İz tablosu:

| Eleman | r | xⱼ | 2 · rᵢ · xⱼ |
|---|---|---|---|
| ∂L/∂W₁₁ | 1 | 1 | 2 |
| ∂L/∂W₁₂ | 1 | 0 | 0 |
| ∂L/∂W₁₃ | 1 | 2 | 4 |
| ∂L/∂W₂₁ | −3 | 1 | −6 |
| ∂L/∂W₂₂ | −3 | 0 | 0 |
| ∂L/∂W₂₃ | −3 | 2 | −12 |

Bu tablo `matris_turev.py` çıktısındaki matrisle birebir aynıdır ve sayısal fark `8,4 · 10⁻¹⁰`dur.

```python
def ornek3():
    # Çözümlü Örnek 3 ile aynı sayılar: W 2x3, x 3, y 2, b = 0.
    W = np.array([[1.0, 2.0, 0.0], [0.0, 1.0, -1.0]])
    x = np.array([1.0, 0.0, 2.0])
    y = np.array([0.0, 1.0])
    r = W @ x - y
    L = np.sum(r ** 2)
    grad = 2 * np.outer(r, x) + 0.0   # -0.0 yerine 0.0 yazdirmak icin
    print("Wx =", W @ x, " r = Wx - y =", r)
    print("L = ||r||^2 =", L)
    print("dL/dW =")
    print(grad)
    g = sayisal_grad(lambda M: np.sum((M @ x - y) ** 2), W)
    print("sayisal fark = %.1e" % np.abs(g - grad).max())
```

**Bunu AI'sız yazabilir misin?** `W = [[1, 1]]` (1×2), `x = (3, −1)`, `y = 2` için `L = (Wx − y)²` kaybının `∂L/∂W` gradyanını bul. Önce şeklini söyle, sonra değeri hesapla.

### Örnek 4 (★★★): Gradyan birikimi hatası: = yerine += ile yanlış sonuç

`f = a · b + a` ifadesini `a = 2`, `b = 3` noktasında düşün. `a` iki yolla kullanılıyor. Doğru gradyanı bul, sonra gradyanları `+=` yerine `=` ile biriktiren hatalı bir geri geçişin neden yanlış sonuç verdiğini göster.

**Adım 1 — Anla.** Beklenen doğru değerler `∂f/∂a = b + 1 = 4` ve `∂f/∂b = a = 2`dir. Hatalı sürümün ne verdiğini de bulmak gerekir. Asıl soru, `a`nın iki katkısının nasıl birleştiğidir.

**Adım 2 — Örnekle.** Küçük bir sayısal kontrol: `a` 2'den 2,000001'e giderse `f` değeri `8`den `8,000004`e çıkar, yani `∂f/∂a ≈ 4`. Doğru gradyanın 4 olduğunu biliyoruz; bunu hatalı sürüm için de karşılaştıracağız.

**Adım 3 — Kaba çöz.** Hesap grafiği dört düğümdür: `a`, `b`, `m = a·b` ve `f = m + a`. Topolojik sıra `a, b, m, f`dir. Geri geçiş `f`den başlar: `f.grad = 1`.

**Adım 4 — Örüntü.** `a` iki kez kullanılıyor: bir kez `m = a·b` içinde, bir kez `f = m + a` içinde. Her kullanım `a`ya bir katkı yazar. Katkılar toplanmazsa son yazılan katkı, öncekinin yerini alır. Hata, bu üst üste yazmanın kendisidir.

**Adım 5 — İyileştir.** Düzeltme tek satırdır: katkıyı `=` ile değil `+=` ile eklemek. Motorumuzda bu iş `_ekle` fonksiyonundadır; `BIRIKIR` bayrağı kapatıldığında bu fonksiyon `=` yapar. Böylece aynı kod iki davranışı da üretebilir ve farkı doğrudan görebiliriz.

**Adım 6 — Doğrula.** İz tablosu (geri geçiş sırasıyla):

| Adım | İşlem | Katkı | `a.grad` (+=) | `a.grad` (=) |
|---|---|---|---|---|
| 1 | f: m'ye katkı 1 | — | 0 | 0 |
| 2 | f: a'ya doğrudan katkı 1 | 1 | 1 | 1 |
| 3 | m: a'ya katkı b · 1 = 3 | 3 | 4 | 3 |
| Sonuç | | | 4 (doğru) | 3 (hatalı) |

Program çıktısı (`dogru: a.grad = 4,0` ve `hatali: a.grad = 3,0`) bu tabloyla birebir tutar. Hatalı sürüm yalnızca son katkıyı tutar ve doğru gradyanın `1` eksik kalır. Bu hata, derin ağlarda paylaşılan bir ağırlığın gradyanını sessizce yanlış yapar ve eğitim yine de çalışıyormuş gibi görünebilir. Bu yüzden gradyan denetimi bu kadar önemlidir.

```python
def calistir(birik):
    deger.BIRIKIR = birik
    a = Deger(2.0)
    b = Deger(3.0)
    m = a * b          # yol 1: a'dan m'ye
    f = m + a          # yol 2: a'dan doğrudan f'ye
    f.geri()
    print("BIRIKIR = %s" % birik)
    print("%-6s %8s %8s" % ("dugum", "veri", "grad"))
    for v in topo(f)[::-1]:
        ad = v._islem if v._islem else "girdi"
        print("%-6s %8.2f %8.2f" % (ad, v.veri, v.grad))
    print("")
    return a.grad, b.grad
```

```term
$ python birikim.py
beklenen: df/da = b + 1 = 4, df/db = a = 2

BIRIKIR = True
dugum      veri     grad
+          8.00     1.00
*          6.00     1.00
girdi      3.00     2.00
girdi      2.00     4.00

dogru   : a.grad = 4.0, b.grad = 2.0
BIRIKIR = False
dugum      veri     grad
+          8.00     1.00
*          6.00     1.00
girdi      3.00     2.00
girdi      2.00     3.00

hatali  : a.grad = 3.0, b.grad = 2.0
```

**Bunu AI'sız yazabilir misin?** `f = a · a + a` ifadesini `a = 3` noktasında düşün. Doğru gradyanı `2a + 1` olarak elle hesapla. Sonra `a` iki kez katkı verdiği için `=` ile birikmenin hangi değeri vereceğini tahmin et ve bunu bir iz tablosuyla doğrula.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı kullanma. Kodu, testleri ve ölçümleri kendin yaz. Amaç, bu bölümdeki kavramları bir mülakatta ya da boş bir IDE'de yeniden kurabilmektir. Bir hata bulursan, önce hatayı kendin çöz; bu, bu bölümün en değerli kısmıdır.
:::

### Proje 1 (★★): Motoru genişlet: sigmoid, log-softmax ve çapraz entropi

**Amaç.** Bölüm 55.10'daki `Deger` motorunu sınıflandırma için gerekli işlemlerle genişletmek ve her yeni işlemi sayısal gradyanla denetlemek.

**Yapılacak / Beklenen davranış.** Motora `sigmoid` ve `log_softmax` ekle. İkili sınıflandırma için `sigmoid` ve ikili çapraz entropiyi, çok sınıflı için `log_softmax` ve çapraz entropiyi kullan. Yeni her işlemi `grad_kontrol.py` gibi bir denetimle sına. Sonra motorla, sabit tohumlu bir veriyle, tek katmanlı bir lojistik sınıflandırıcı eğit ve kayıp eğrisini çiz.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Sigmoid'i mevcut `exp`, `+`, `**` ve bölme ile kurabilirsin; yeni bir geri adım yazmak zorunda değilsin. Log-softmax için log-sum-exp kullan: en büyük değeri çıkar. Çapraz entropiyi yazarken gradyanın `p − y` olduğunu önceden hesapla ve motorun ürettiğiyle karşılaştır.

**Başarı kriterleri.** (1) Yeni işlemlerin her birinde göreli hata `10⁻⁶`nın altındadır. (2) Log-softmax, `z` içine büyük bir sabit eklendiğinde aynı olasılıkları verir. (3) Lojistik sınıflandırıcının kaybı eğitim boyunca azalır ve sonuç sabit tohumla birebir tekrarlanır. (4) Kayıp eğrisi ve doğruluk raporda ölçülmüş olarak verilmiştir.

### Proje 2 (★★★): Vektör düzeyi autodiff ve küçük bir MLP

**Amaç.** Skaler motoru, matris çarpımı ve yayınlamayı (broadcasting) destekleyen bir vektör düzeyine taşımak; SGD ve Adam ile gerçek bir veri kümesinde küçük bir MLP eğitmek.

**Yapılacak / Beklenen davranış.** Bir `Tensor` sınıfı yaz: değer dizisi ve gradyan dizisi tutsun. `matmul`, eleman bazlı toplama ve çarpma, `tanh` ve `relu` desteklensin. Toplamada yayınlama yapıldığında geri geçişte gradyanın doğru eksende toplanması gerekir. Ardından `sklearn.datasets.load_digits` verisiyle bir MLP eğit; eğitim ve test doğruluğunu ayrı ayrı raporla. Optimizasyon için hem SGD hem Adam (Bölüm 50.8) dene.

**Önerilen yaklaşım (ipucu).** Her matris işleminin geri adımını Bölüm 55.12'deki `dW = girdiᵀ d` ve `db = ∑ d` kurallarından türet. Yayınlamanın geri geçişi için, toplamanın yayınlandığı eksenlerde gradyanı topla ve şekli eski haline getir. Gradyan denetimini her yeni işlem için tekrarla. Adam için Bölüm 50.8'deki güncelleme kuralını kullan; kendi kodunda iki moment tahminini ayrı tut.

**Başarı kriterleri.** (1) Her tensör işleminin gradyanı sayısal denetimden `10⁻⁶` göreli hatayla geçer. (2) Yayınlamalı toplama için gradyanın şekli girdi şekliyle eşleşir. (3) SGD ve Adam ile eğitilmiş iki model için eğitim ve test doğruluğu, sabit tohumla birlikte tabloda verilmiştir. (4) Hangi işlemin en çok zaman aldığı bir profil ölçümüyle gösterilmiştir.

### Ek Alıştırmalar

Aşağıdaki problemler cevapsızdır. Her birini önce kendin çöz, sonra kontrol etmek için bu bölümdeki kodları kullan.

1. (★) `f(x, y) = x² y` fonksiyonunun `(2, 1)` noktasındaki gradyanını ve `u = (0, 1)` yönündeki yönlü türevini bul.
2. (★) Sigmoid'in `σ′(x) = σ(x)(1 − σ(x))` olduğunu cebirle göster. `σ′`nin en büyük değerinin `1/4` olduğunu `x = 0`da doğrula.
3. (★) `f(x) = x²` için `x = 3` noktasında ileri farkla (`h = 10⁻³`) ve merkezi farkla (`h = 10⁻³`) türevi hesapla. Hangisi gerçek `6` değerine daha yakın?
4. (★) `f(x) = e^{2x}` için ileri mod ile (`Dual` sınıfıyla) `x = 0` noktasındaki türevi bul. Sonucun `2` olduğunu iz tablosuyla göster.
5. (★★) Mülakat: Backpropagation'ı bir hesap grafiği, zincir kuralı ve topolojik sıra kavramlarını kullanarak yaklaşık bir sayfada açıkla. Sihirli bir şey olmadığını nasıl gösterirsin?
6. (★★) Mülakat: Neden ters mod, bir sinir ağında ileri moddan çok daha yaygın kullanılır? `n = 10⁶` parametre ve `m = 1` kayıp için iki yöntemin geçiş sayısını karşılaştır.
7. (★★) Softmax Jacobian'ı `diag(p) − ppᵀ` simetrik midir? Her satırının toplamının sıfır olduğunu göster ve bunun neden olasılık kısıtından geldiğini açıkla.
8. (★★) Mülakat: ReLU'nun `x = 0` noktasındaki türevi tanımlı değildir. Yazılımda bu durumda ne seçilir ve bu seçim eğitimi neden pratikte bozmaz?
9. (★★) `y = Wx + b` ve `L = ‖y − t‖²` için `∂L/∂b` gradyanını türet. Şeklini kontrol et ve bu gradyanın neden `2(y − t)` ile aynı olduğunu açıkla.
10. (★★) Gradyan birikimini bilerek bozan bir hesap grafiğinde `f = a·b + b·c` ifadesi için hangi gradyanların yanlış olacağını (`b` iki kez kullanılır) bir iz tablosuyla göster.
11. (★★★) Mülakat: İleri mod ile ters modun Jacobian-vektör ve vektör-Jacobian çarpımlarında ne hesapladığını ayır. Hangisini ne zaman seçersin?
12. (★★★) Hessian-vektör çarpımı `Hv` için tüm Hessian'ı kurmadan bir yol düşün. Bunun neden büyük ağlarda önemli olduğunu ve hangi iki geçişin birleşiminden oluştuğunu açıkla.

## Kod Okuma Egzersizi

Bu bölümde kendi motorumuzu micrograd projesiyle karşılaştıracağız. micrograd, Andrej Karpathy'nin MIT lisanslı küçük bir otomatik türev kütüphanesidir. Kullanılan kaynak, `https://raw.githubusercontent.com/karpathy/micrograd/master/micrograd/engine.py` adresinden alınan `micrograd/engine.py` dosyasıdır ve commit `7bc720e951fe422b8f8814aa5aa1b64121d26b4c` (master, 2026-08-03) sürümüdür. Aşağıdaki kesitler birebir kopyadır; yalnızca 11. satırdaki sondaki yorum ve 67. satırdaki uzun yorum okuma kolaylığı için atlanmıştır. Atlanan satır aralıkları, kod parçaları arasındaki açıklamalarda belirtilmiştir.

Sınıfın kurucusu, veri ve gradyanı, ardından çocukları ve işlemi tutar. Bu, bizim `Deger` sınıfımızla aynı fikirdir; 11. satırdaki `self._op` alanını atladık, bu alan yalnızca hata ayıklama içindir.

```python
class Value:
    """ stores a single scalar value and its gradient """

    def __init__(self, data, _children=(), _op=''):
        self.data = data
        self.grad = 0
        # internal variables used for autograd graph construction
        self._backward = lambda: None
        self._prev = set(_children)
```

Toplama işlemi, bizim `__add__` metodumuzla birebir eşdeğerdir. Geri adım her iki girdiye de çıkışın gradyanını ekler.

```python
    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), '+')

        def _backward():
            self.grad += out.grad
            other.grad += out.grad
        out._backward = _backward

        return out
```

Çarpma da aynı kalıbı izler. Her girdinin yerel türevi, diğer girdinin değeridir.

```python
    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), '*')

        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward

        return out
```

Geri geçişin asıl kısmı aşağıdadır. 34-53. satırlar (üs ve relu) atlanmıştır; 54. satırdan itibaren `backward` metodunun topolojik sıralama bölümü alınmıştır.

```python
    def backward(self):

        # topological order all of the children in the graph
        topo = []
        visited = set()
        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)
        build_topo(self)
```

Son üç satır çıkışın gradyanını 1 yapar ve düğümleri ters sırada çalıştırır. 67. satırdaki yorum atlanmıştır; kalan kod birebirdir.

```python
        self.grad = 1
        for v in reversed(topo):
            v._backward()
```

**Sorular — cevaplamadan geçme:**

1. `_prev` neden bir `set` olarak tutulur, oysa kurucu `_children` bir tuple olarak alır? Bu seçim topolojik sıralamanın çocuk sırasını nasıl etkiler ve bizim motorumuzda neden `tuple` kullandık?
2. `build_topo` bir düğümü, çocukları ziyaret edildikten sonra listeye ekler. Bu sıralama, geri geçişin çıkıştan girdilere doğru gitmesini neden garanti eder? Bölüm 17.3'teki DFS tabanlı sıralamayla karşılaştır.
3. `self.grad += out.grad` satırında neden `+=` kullanılır? Aynı `Value` nesnesi `a + a` gibi bir ifadede iki kez girdi olursa ne olur? Bu, Çözümlü Örnek 4'teki hatanın tersidir; açıkla.
4. micrograd, `__sub__` için `self + (-other)` yazar. Bizim motorumuz da aynısını yapar. Bu indirgeme, yeni bir yerel türev yazmadan çıkarmayı neden mümkün kılar?
5. `backward` içinde `self.grad = 1` yazılıyor, oysa bizim sürümümüzde `1.0` yazdık. Python'da `int` ve `float` karışımı gradyan biriktirirken hangi tip sorunlarını doğurabilir ve veriyi `float(veri)` ile zorlamamız neden bunu önler?
6. `relu` geri adımı `(out.data > 0) * out.grad` çarpımını kullanır. Python'da `bool` ile `float` çarpıldığında sonuç nedir? Bu ifadeyi kendi motorumuzdaki `float(cikis.veri > 0) * cikis.grad` ile karşılaştır ve farkın olup olmadığını açıkla.

## Bölüm Özeti

- **Türev**, bir fonksiyonun bir noktadaki doğrusal yaklaşımının eğimidir. `f(a + h) ≈ f(a) + f′(a) h` bütün bölümün çekirdeğidir. Sayısal olarak merkezi farkla yaklaşılır (Bölüm 50.3).
- **Zincir kuralı** `(g∘h)′ = g′(h) · h′` bileşik fonksiyonların türevidir. Bir sinir ağı, uzun bir bileşimdir; geri yayılım bu kuralın bir hesap grafiği üzerinde uygulanmasıdır.
- **Gradyan** `∇f`, kısmi türevlerin vektörüdür ve en dik artış yönünü gösterir. **Jacobian** vektör değerli fonksiyonların türev matrisidir; çok değişkenli zincir kuralı Jacobian çarpımıdır.
- **Matris kalkülüsünde** gradyanın şekli parametrenin şeklidir. `∂‖Wx − y‖²/∂W = 2(Wx − y)xᵀ` gibi kurallar sayısal olarak doğrulanabilir. Softmax ve çapraz entropi birlikte `p − y` gradyanını verir (Bölüm 51.10).
- **Otomatik türev** üç yoldan biridir: sembolik, sayısal ve otomatik. Ters mod, skaler kayıplarda bir ileri ve bir geri geçişle tüm gradyanları verir; ileri mod ise girdi sayısı kadar geçiş ister.
- **Gradyan birikimi** paylaşılan her düğümün katkılarını toplamasını gerektirir. `=` yerine `+=` kullanmak, bu bölümün en sık yapılan hatasıdır.
- **Kendi motorumuz** yaklaşık 140 satırdır ve micrograd tarzında bir `Deger` sınıfı, topolojik sıralama ve geri adımlardan oluşur. Sabit tohumlu 300 rastgele ifadede göreli hata `10⁻¹⁰` mertebesindedir.
- **Vektörleştirilmiş** geri yayılım aynı matematiği matris çarpımlarıyla yapar; aynı ağda skaler sürümden birkaç bin kat hızlıdır (makineye bağlı). Bu köprü, Bölüm 63'teki tam MLP'nin temelidir.
- **Sayısal tuzaklar**: sigmoid zincirinde gradyan `0,25ⁿ` ile sınırlıdır ve derinlikle kaybolur; softmax taşar, `log(0)` tanımsızdır. Log-sum-exp ve kararlı kayıp formülleri bu tuzakları önler.

**Sonraki bölümde:** Bölüm 56, Veriyle Çalışmak, kısımda NumPy'ı derinlemesine ele alacak. Bu bölümde gördüğümüz `sum(axis=0)`, `@` ve eleman bazlı işlemler, vektörleştirmenin ve yayınlamanın (broadcasting) en basit örnekleriydi. Bölüm 56'da bu kuralları sistematik olarak öğrenecek, pandas ile veri temizleme ve özellik mühendisliğine geçeceğiz.

::: mulakat
1. Geri yayılım bir "öğrenme" algoritması mı yoksa bir türev hesaplama yöntemi midir? Zincir kuralıyla neden ayırt edilir?
2. Gradyan birikimi neden gereklidir? Bir değişken birden fazla yolla kullanıldığında gradyanı `=` ile yazan bir motor hangi tür hatalı eğitimlere yol açar?
3. İleri mod ve ters modu, bir sinir ağında hangi yöntemi seçerdin ve neden? Girdi ve çıktı sayısını hesaba katarak açıkla.
4. Softmax ile çapraz entropi birlikte kullanıldığında gradyan neden `p − y` olur? Bu sadelik, eğitim verimliliği için neden önemlidir?
5. Sigmoid aktivasyonlu derin bir ağda gradyan neden kaybolur? Bu sorunu azaltmak için hangi üç pratik yaklaşımı sayarsın?
6. Sayısal türev, otomatik türev ve sembolik türev arasındaki doğruluk ve maliyet farkı nedir? Bir sinir ağının eğitiminde hangisini tek başına kullanmazsın?
7. Log-sum-exp hilesi neden softmax'ı kararlı kılar ve gradyanı değiştirmez? Matematiksel olarak nedenini göster.
8. Bir sinir ağının Hessian'ının tamamını hesaplamak neden çoğu zaman mümkün değildir? Hessian-vektör çarpımı bu sorunu nasıl hafifletir?
