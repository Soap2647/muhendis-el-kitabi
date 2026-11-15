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

@@KOD ortak.py:def merkezi_fark

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

@@KOD matris_turev.py:def sayisal_grad_vek

Bir Jacobian'ı bu şekilde doğrulamak, analitik türetmenin doğru olup olmadığını anlamanın en güvenilir yoludur. Bu bölümün her türev formülünü aynı yöntemle sınayacağız.

## 55.4 Çok değişkenli zincir kuralı: Jacobian çarpımı

Zincir kuralını vektörlere genişletmek için `f = g ∘ h` olduğunu düşünelim, ama şimdi `h : ℝⁿ → ℝᵐ` ve `g : ℝᵐ → ℝᵏ`. Bu durumda Jacobian'lar çarpılır:

J_f(x) = J_g(h(x)) · J_h(x)

Burada `J_g` bir `k × m` matristir, `J_h` bir `m × n` matristir ve çarpım bir `k × n` matris verir. Şekillerin uyuşması, zincir kuralının doğru olduğunu gösteren ilk kontroldür. Bu kontrolü her zaman yapmanı öneririm: Türevin şekli, fonksiyonun girdi ve çıktı şekillerinden başka bir şey olamaz.

Somut bir örnek için `h(x₁, x₂) = (x₁x₂, x₁ + x₂²)` ve `g(u₁, u₂) = u₁² + sin u₂` alalım. `J_h = [[x₂, x₁], [1, 2x₂]]` ve `J_g = [2u₁, cos u₂]` olur. Çarpım, `(1, 0,5)` noktasında `(0,815322, 1,315322)` verir. Aşağıdaki fonksiyon bu iki Jacobian'ı kurar, çarpar ve sonucu merkezi farkla karşılaştırır.

@@KOD zincir.py:27-58

Aşağıdaki çıktının ilk bölümü Örnek 1'in tek değişkenli türevini de gösterir. İkinci bölümdeki `J_g J_h` satırı ile `sayisal` satırı aynıdır. Tek değişkenli kısımda elle hesaplanan `f′(x)` ile merkezi fark arasındaki fark `10⁻¹¹` mertebesindedir. Bu fark, merkezi farkın kesme ve yuvarlama hatalarının toplamıdır.

@@CIKTI python zincir.py out_zincir.txt

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

@@KOD matris_turev.py:def sayisal_grad

Denetimi çalıştırdığında her kuralın hatası `10⁻¹⁰` ile `10⁻⁹` arasında kalır. Bu, türetilen formüllerin doğru olduğunun sayısal kanıtıdır.

@@CIKTI python matris_turev.py out_matris_turev.txt

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
