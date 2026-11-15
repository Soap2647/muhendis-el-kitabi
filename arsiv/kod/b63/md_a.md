%% kisim_no: XV
%% kisim_ad: Derin Öğrenme
%% kisim_ayrac: evet
%% bolum_no: 63
%% baslik: Sinir Ağı Sıfırdan

## Giriş: Beyinden esinlenen bir fikir, türev hesabıyla çalışır

Bugün görüntüden nesne tanıyan, sesi metne çeviren ve bir soruya cevap üreten sistemlerin merkezinde aynı yapı var: doğrusal dönüşümler, aralarına konmuş doğrusal olmayan fonksiyonlar ve bu katmanları eğiten bir türev hesabı. Bu yapıya çok katmanlı algılayıcı (MLP, multilayer perceptron) denir. Bölüm 55'te bu türev hesabının motorunu yazdık, Bölüm 58'de tek katmanlı hâlini, yani lojistik ve softmax regresyonunu gördük. Bu bölümde ikisini birleştiriyoruz: birden çok katmanlı bir ağı, türevlerini elle türeterek, NumPy ile sıfırdan yazacağız.

Neden önemli? Savunma sanayiinde bir sensör akışından hedef sınıflandıran ya da bir arızayı önceden kestiren model çoğu zaman bir MLP'dir. Kütüphanenin içine kapanmış bir ağda eğitim bir gün yanlış bir sonuç verdiğinde, hatanın veride, mimaride, türevde ya da optimizasyonda olup olmadığını ayırt edemezsin. Gradyanın her parçasının nereden geldiğini bilmek, bu ayrımın tek yoludur. Mert'in EV Dashboard projesindeki STM32 sensör verisi için bir arıza sınıflandırıcısı yazmak istediğinde, bu bölümdeki ağ o işin iskeletidir; Bölüm 46'daki tamsayı çıkarım hattı da onun son durağı olacaktır.

Bölümün kurgusu şöyle. Önce algılayıcıdan başlayıp tek bir doğrusal birimin neyi öğrenebildiğini ve neyi öğrenemediğini (XOR) göreceğiz. Sonra katman, aktivasyon fonksiyonu, ileri geçiş ve geri yayılımın tam türetmesine geçeceğiz. Her türetmeyi gradient check ile sayısal olarak sınayacağız. En sonunda yazdığımız çatıyla `load_digits` veri kümesindeki 8×8 el yazısı rakamları üzerinde 64-128-64-10 boyutlu bir ağı eğitip, lojistik regresyon taban çizgisiyle karşılaştıracağız.

Bu bölümde yazılan her programın çıktısı, metinde gösterilen çıktının ta kendisidir; tohumlar sabittir. Başarı iddiaları ayrı bir test kümesinde ölçülmüştür. Eğitim doğruluğu her yerde "eğitim" diye etiketlenmiştir, yanında test sonucu da verilmiştir (Bölüm 54 ve 57'deki değerlendirme disiplini).

::: not
Bu bölümdeki bütün programlar yalnızca NumPy ile yazılmıştır. Veri için scikit-learn'ün `load_digits` fonksiyonu ve veri bölme yardımcısı kullanıldı; ağın kendisinde scikit-learn yoktur. PyTorch yalnızca bölümün sonunda, aynı ağın doğru türevini verdiğini gösteren kısa bir köprü olarak geçiyor. Ölçümler CPU üzerinde yapıldı. GPU ölçümleri, PyTorch'un kendi bağlamında Bölüm 65'te yapılacak.
:::

## 63.1 Biyolojik esin ve abartısı

Bir sinir hücresi dendritleri aracılığıyla girdi alır, bu girdileri gövdesinde toplar ve toplam bir eşiği aşarsa aksonu boyunca bir darbe gönderir. 1943'te McCulloch ve Pitts bu davranışı ikili girdili ve ikili çıktılı bir mantık birimi olarak modelledi (genel bilgi). Bu model mantık kapılarını gerçekleyebiliyordu, ama öğrenemiyordu. Öğrenme sorusu bir sonraki adımda gelir.

Yapay bir nöron ile biyolojik bir nöron arasındaki benzerlik "girdileri ağırlıklı topla, bir fonksiyondan geçir" düzeyinde kalır. Gerçek beyinde bağlantı yapısı, zamanlama, enerji tüketimi ve öğrenme kuralı çok farklıdır. Özellikle geri yayılım beynin bildiğimiz bir mekanizması değildir: bir sinapsın değişimi, o sinapsın kendi yerel bilgisine değil, ağın çıktısındaki hatanın türevine bağlıdır. Bu yerel olmayan bilgi akışının biyolojide nasıl ya da karşılığı olup olmadığı açık bir araştırma sorusudur.

Bu yüzden bu bölümde "beyin gibi" ifadesini bir kolaylık olarak kullanacağım, bir kanıt olarak değil. Doğru zihinsel model şudur: bir yapay nöron, girdilerin ağırlıklı toplamı, bir sapma (bias) ve doğrusal olmayan bir fonksiyondur. Bütün gerisi bu üç parçanın bir araya getirilmesidir.

## 63.2 Algılayıcı ve öğrenme kuralı

Frank Rosenblatt 1958'de algılayıcıyı (perceptron) tanıttı (genel bilgi). Girdi vektörü `x`, ağırlık vektörü `w` ve sapma `b` ile karar kuralı şöyledir:

ŷ = [wᵀx + b ≥ 0]

Burada köşeli parantez, koşul doğruysa 1, değilse 0 veren bir gösterimdir. Öğrenme kuralı da çok sadedir: bir örnek yanlış sınıflanırsa, ağırlıkları hatanın yönünde küçük bir adımla kaydır. Hata `y − ŷ` ile ölçülür ve yalnızca üç değer alabilir: `−1`, `0` ya da `+1`.

w ← w + η (y − ŷ) x
b ← b + η (y − ŷ)

Doğru tahmin edilen bir örnekte `y − ŷ = 0` olduğu için hiçbir şey değişmez. Yanlış tahmin edilen bir örnekte ağırlık, örneğin işaretine doğru çekilir ya da itilir. Bu, Bölüm 50'deki gradyan iniş fikrinin en ilkel hâlidir: adım küçük, yön hatadan gelir. Kural, veri doğrusal olarak ayrılabilirse sonlu sayıda adımda duracağı bilinir (Novikoff'un sınırı, genel bilgi). Doğrusal ayrılamayan veride ise hiçbir zaman durmaz.

Aşağıdaki program algılayıcıyı iki mantık kapısına uygular: AND doğrusal olarak ayrılabilir, XOR ayrılamaz. Program ayrıca XOR için ızgara araması yaparak, bu sınıfta en iyi çizginin bile neden yetmediğini gösterir.

Programın ilk kısmı veriyi, öğrenme kuralını ve ilk epoch'un izini üretir.

@@KOD t01_algilayici.py 1 33@@

Programın ikinci kısmı, XOR için ızgara araması ve sonuçların CSV'ye yazılmasıdır. Bu kısım, şekil 63.1'in verisini de üretir.

@@KOD t01_algilayici.py 34 53@@

Üçüncü kısım ana programdır. AND için iz yazdırır, XOR için 1000 epoch'u çalıştırır ve sonuçları raporlar.

@@KOD t01_algilayici.py 54 79@@

Programı çalıştırdığında şu çıktıyı alırsın:

@@CIKTI t01_algilayici.py out_t01_algilayici.txt@@

AND'nin ilk epoch izini elle de izleyebilirsin. Başlangıçta `w = (0, 0)` ve `b = 0`. İlk örnek `(0, 0)`, etiket `0`; tahmin `1` çıkıyor, hata `−1`. Sapma `−1`'e iniyor. Dördüncü örnek `(1, 1)` etiket `1` ama tahmin `0`; bu kez hata `+1` ve ağırlık `(1, 1)` oluyor. İlk epoch'un sonunda iki güncelleme yapılmış ve sayılar `w = (1, 1)`, `b = 0` olmuş. Sonraki epoch'larda kural, `w = (2, 1)` ve `b = −3`'e yakınsıyor; bu değerler `2·x₁ + x₂ − 3 ≥ 0` demek, yani yalnızca `x₁ = 1` ve `x₂ = 1` için pozitif. AND kapısı budur.

XOR'da ise durum farklıdır. 1000 epoch boyunca hiçbir epoch hatasız geçmiyor; en iyi epoch dahi üç hata yapıyor. Izgara araması daha dürüst bir sonuç verir: `(w₁, w₂, b) = (−2, −2, 2)` çizgisi bile dört örnekten birini yanlış sınıflar. XOR'un iki sınıfı köşegenlerde duruyor ve tek bir doğru bu iki çifti ayıramaz. Bu, 1969'da Minsky ve Papert'in algılayıcı kitabında ayrıntılı olarak incelediği sınırlılığın en küçük örneğidir (genel bilgi). Çözüm, bir ara katman eklemektir; bu bölümün geri kalanı o ara katmanın nasıl kurulacağını ve nasıl eğitileceğini anlatır.

@@SEKIL b63_algilayici.png 63.1 AND doğrusal ayrılabilir; XOR için hiçbir doğru dört noktayı doğru ayıramaz. Sağdaki çizgi, ızgara aramasının bulduğu en iyi çizgidir ve yine bir nokta yanlıştır.@@

## 63.3 Katman ve doğrusal olmayanlık

Bir katman, Bölüm 48'de gördüğümüz matris çarpımı ile başlar: girdi vektörü bir ağırlık matrisiyle çarpılır, bir sapma eklenir ve sonuç doğrusal olmayan bir fonksiyondan geçirilir. Yani `h = φ(xW + b)`. Burada `φ` aktivasyon fonksiyonudur. `φ` yoksa katman bir afin dönüşümdür ve afin dönüşümlerin bileşimi yine afin bir dönüşümdür. Bunu bir sayı ile gösterelim: rastgele seçilmiş üç doğrusal katmanı (64 → 32 → 16 → 10) art arda uygulamak ile bunları tek bir matrise çarpıp uygulamak aynı sonucu verir. Matris çarpımı birleşmelidir, `(AB)C = A(BC)`.

Bu, derin bir ağın neden derin olmadığı anlamına gelir: aktivasyonsuz üç katman, tek bir doğrusal katmandan daha fazla bir şey yapmaz. Parametre sayısı da artmaz; yalnızca gereksiz bir çarpanlaştırma olur. Doğrusal olmayanlık, katmanların birbirinden bağımsız dönüşümler olarak kalmasını engeller. Aşağıdaki programda bu iddiayı sayısal olarak sınıyoruz. Aynı programda aktivasyon fonksiyonlarını ve ölü ReLU deneyini de yapıyoruz; bunları bir sonraki bölümde açıklayacağız.

Programın ilk kısmı aktivasyon fonksiyonlarını ve türevlerini tanımlar. `gelu` fonksiyonu, tanh yaklaşımıyla yazılmıştır ve türevi de bu yaklaşımın analitik türevidir.

@@KOD t02_aktivasyon.py 1 39@@

İkinci kısım, doğrusal çöküşü sayısal olarak gösteren fonksiyondur. Üç rastgele matris alıyor, bunları ayrı ayrı ve birleştirilmiş olarak uyguluyor, farkı ölçüyor.

@@KOD t02_aktivasyon.py 40 52@@

Üçüncü kısım, ölü ReLU deneyidir: bir gizli katmanlı ağı farklı öğrenme oranlarında beş epoch eğitir, eğitim kümesinde hiç aktif olmayan (her örnekte sıfır üreten) birim sayısını sayar.

@@KOD t02_aktivasyon.py 53 66@@

Dördüncü kısım, şekil 63.2 için verinin CSV'ye yazılmasıdır ve ana programdır.

@@KOD t02_aktivasyon.py 67 96@@

Programın çıktısı şöyle:

@@CIKTI t02_aktivasyon.py out_t02_aktivasyon.txt@@

Çıktının ilk satırı, sigmoid türevinin en büyük değerinin `0,25` olduğunu gösteriyor; bu sayı Bölüm 63.4'te önemli olacak. Doğrusal çöküş satırı ise, üç katmanın farkının `1,6 × 10⁻¹³` olduğunu gösteriyor. Bu sayı sıfır değil, çünkü kayan nokta aritmetiğinin yuvarlama hatası var; ama makine hassasiyeti mertebesinde. Parametre sayılarına bakarsan fark daha da çarpıcı: üç katmanlı yapı 2720 parametre taşıyor, tek katmanlı eşdeğeri ise 640. Eşdeğer tek matris, aynı işi yaparken dörtte bir parametreyle yetiniyor. Aktivasyon olmadan derinliğin hiçbir değeri yok.

## 63.4 Aktivasyon fonksiyonları ve türevleri

Aktivasyon fonksiyonu, katmandaki doğrusal olmayanlığı sağlayan fonksiyondur. Her biri için hem değerini hem türevini bilmemiz gerekir, çünkü geri yayılım türevi kullanır (Bölüm 55'teki zincir kuralı).

Sigmoid, `σ(z) = 1 / (1 + e^(−z))` ile tanımlanır. Değeri `(0, 1)` aralığındadır ve türevi `σ′(z) = σ(z)(1 − σ(z))` biçimindedir. Türevinin en büyük değeri `z = 0` noktasında `0,25`tir. Bölüm 55.13'te gördüğümüz kaybolan gradyan sorununun kaynağı tam budur: her katmanda türev en fazla `0,25` ile çarpılır, `n` katman sonra gradyan `0,25ⁿ` mertebesine düşer.

Tanh, `tanh(z)` ile tanımlanır, değeri `(−1, 1)` aralığındadır ve türevi `1 − tanh²(z)` biçimindedir. Türevi en fazla `1`dir, ama yine de büyük `|z|` için sıfıra yaklaşır. Sigmoid'in sıfır merkezli hâlidir.

ReLU, `max(0, z)` fonksiyonudur. Türevi `z > 0` için `1`, `z < 0` için `0`dır. Pozitif tarafta gradyan olduğu gibi geçer, bu yüzden derin ağlarda kaybolma sorunu daha hafiftir. Bunun bedeli, negatif tarafta bir birimin tamamen susabilmesidir. Bir birim, hiçbir girdi için pozitif bir değer üretmezse, hem ileri geçişte hem geri geçişte katkısı sıfır olur ve bir daha güncellenmez. Buna ölü ReLU (dead ReLU) denir.

Leaky ReLU, negatif tarafa küçük bir eğim `α` (burada `0,1`) ekler ve ölü birim sorununu hafifletir. GELU ise `z · Φ(z)` biçiminde yazılır; `Φ`, standart normal dağılımın birikimli fonksiyonudur. Burada kullandığımız tanh yaklaşımı (genel bilgi, Hendrycks ve Gimpel 2016) yaygın bir gerçekleştirmedir. GELU, negatif bölgede küçük ve pürüzsüz bir eğri üretir; dönüşüm modern dil modellerinde sık kullanılır (Bölüm 69 ve 70).

Şekil 63.2, bu fonksiyonların değerlerini ve türevlerini yan yana gösteriyor.

@@SEKIL b63_aktivasyon.png 63.2 Üst satır: değerler. Alt satır: türevler. ReLU ailesinin türevi negatif tarafta sıfır ya da küçük bir sabittir; sigmoid'in türevi her iki uçta sönümlenir.@@

Ölü ReLU deneyinin sonucu, bu sorunun sayısal bir ölçüsünü veriyor. Öğrenme oranı `0,05` iken birkaç birim zaten hiç aktif olmuyor (64'te 3). `0,5`te bu sayı 5'e çıkıyor ve doğruluk hâlâ yüksek kalıyor. Oranı `2,0`'e çıkardığımızda ise 64 birimden 63'ü ölüyor ve doğruluk şans düzeyine (`0,100`) düşüyor. Büyük bir adım, birimleri bir kez negatif tarafa itiyor; oradan dönüş yok. Bu yüzden ReLU ağlarında öğrenme oranı yalnızca doğruluğa değil, ölü birim sayısına da bakılarak seçilir. Bölüm 64'te bu sorunu azaltan başlatma ve normalizasyon tekniklerini göreceksin.

Not: ölü birimleri yalnızca eğitim kümesinde saydık. `H.max(axis=0) == 0` koşulu, birimin eğitim kümesinin hiçbir örneğinde pozitif değer üretmediğini söyler; aynı birimin test kümesinde de ölü olup olmadığını bu sayı söylemez.

## 63.5 Evrensel yaklaşım: ne vaat eder, ne vaat etmez

Evrensel yaklaşım teoremi (Cybenko 1989; Hornik 1991, genel bilgi) şunu söyler: yeterli genişlikte tek bir gizli katmanı olan ve uygun bir aktivasyon kullanan bir ağ, kompakt bir kümede tanımlı herhangi bir sürekli fonksiyonu istenen doğrulukta yaklaştırabilir. Bu bir varlık teoremidir. Üç şeyi söylemez: ağın kaç birime ihtiyacı olduğunu, bu ağırlıkların eğitimle bulunup bulunamayacağını ve verinin genellemeyi sağlayıp sağlamadığını.

Sezgi için ReLU'yu düşün. Tek bir ReLU birimi `max(0, w x + b)`dir; bu, bir kıvrım noktası (knot) olan bir kırık doğrudur. Gizli katmandaki `h` birim, `h` tane kırık doğru üretir ve çıkış katmanı bunları doğrusal olarak toplar. Sonuç, en fazla `h` kıvrımı olan bir parçalı doğrusal fonksiyondur. Kıvrım sayısı arttıkça parçalı doğrusal eğri sürekli fonksiyona daha iyi yaklaşır. Bu, teoremin pratik yüzü: birim sayısı kapasiteyi belirler.

Aşağıdaki deneyde hedef fonksiyon `sin(3x) + 0,3x²` ve girdi aralığı `[-2, 2]`. Gizli birim sayısını `2, 8, 32` yapıyoruz ve sonucu test ızgarasında ölçüyoruz. Bu deney gürültüsüz bir hedefle yapılıyor, çünkü amacımız genellemeyi değil yaklaşım kapasitesini ölçmek. Eğitim verisi de bu fonksiyonun 400 rastgele noktası.

Deneyin en önemli bulgusu bir başlatma ayrıntısıdır. Gizli katmanın sapmalarını sıfır başlatırsak, her ReLU biriminin kıvrım noktası `x = 0`da kalır, çünkü birim yalnızca bu noktada kırılır ve rastgele `w` kıvrımı konumlandırmaz. Bu durumda birim sayısını artırmak yardım etmez. İkinci bir başlatma, kıvrım noktalarını `[-2, 2]` aralığına yayar: her birimin sapması `b = −w·c` ile seçilir, `c` bu aralıkta düzgün dağılımlıdır. Aşağıdaki program iki başlatmayı da, beş tohumla ve üç birim sayısında karşılaştırır.

Programın ilk kısmı hedefi, eğitim fonksiyonunu ve kıvrım yerleştirmesini tanımlar.

@@KOD t04_yaklasim.py 1 29@@

Programın ikinci kısmı deneyi çalıştırır, sonuçları yazdırır ve şekil 63.3'ün verisini kaydeder.

@@KOD t04_yaklasim.py 30 66@@

Çıktı şöyle:

@@CIKTI t04_yaklasim.py out_t04_yaklasim.txt@@

Sonuçları iki ayrı soruyla okumak gerekir. Birincisi, sıfır sapmayla başlatılan ağ `h = 8` ve `h = 32`de yaklaşık `0,31`–`0,32` RMSE'de takılıyor: `h = 32`, `h = 8`den iyi değil. Bu, kapasitenin değil başlatmanın darboğaz olduğunu gösteriyor. İkincisi, kıvrımları yaydığımızda hata birim sayısıyla düzgün biçimde düşüyor: ortalama `0,55`ten `0,22`ye, sonra `0,07`ye iniyor. Ama sapmalar büyük, özellikle `h = 32` için. Tohum bazında değerler, bu sapmanın bir tohumdan kaynaklandığını gösteriyor: beş tohumun dördünde ağ `0,03` ile `0,05` arası bir hataya ulaşırken, birinde yerel bir minimumda `0,19` hatada kalıyor. Gradyan inişi ile bulunan çözüm, hedef fonksiyon için en iyi çözüm değildir; sadece yakınındaki bir minimumdur. Bu, bölümün sonraki kısımlarında yeniden karşımıza çıkacak bir gerçektir.

@@SEKIL b63_yaklasim.png 63.3 Solda tohum 0 için üç ağın tahmini (hedef siyah). Sağda beş tohumun ortalama ± sapması. Kapasite birim sayısıyla artıyor, ama yalnızca kıvrımları yayarak başlatıldığında.@@

## 63.6 İleri geçiş ve modüler gerçekleme

Bir katmanı kodlamadan önce boyutları belirlemek gerekir. Mini-batch ile çalışacağımız için girdi bir matristir: `X` şekli `(B, d_in)`, yani `B` örnek ve her örnekte `d_in` özellik. Dogrusal katmanın ağırlığı `W` şekli `(d_in, d_out)`, sapması `b` şekli `(d_out,)`. Çıktı `Z = X W + b` şekli `(B, d_out)`dur. NumPy'ın yayılım (broadcasting) kuralı sapmayı her satıra ekler (Bölüm 56'da ayrıntılı göreceğiz).

Şekil 63.4 bizim ağımızın şekillerini gösteriyor: girdi `(B, 64)`, ilk katman `64 → 128`, ardından ReLU, `128 → 64`, ReLU ve çıkış `64 → 10`. Toplam parametre sayısı `17.226`dır (ağırlıklar 17.024, sapmalar 202). Bu sayıyı Bölüm 63.13'te doğrulayacağız.

@@SEKIL b63_mlp_mimari.png 63.4 Ağın şekilleri. Her Doğrusal katmanın altında çıktı şekli `(B, d)` yazılı; B mini-batch boyutudur.@@

Kodun ilk parçası katmanları tanımlar. Her katman iki yöntem sunar: `ileri` girdiyi alıp çıktıyı döndürür ve geri geçiş için gerekli ara değerleri saklar; `geri` çıkış gradyanını alıp girdi gradyanını döndürür ve kendi parametre gradyanlarını hesaplar. Bu arayüz, PyTorch'un `nn.Module` sınıfındaki `forward` ve autograd'un geri geçişine karşılık gelir (Bölüm 65).

Aşağıdaki ilk parça `Dogrusal` katmanını ve iki aktivasyon katmanını içerir.

@@KOD sinir.py 1 30@@

Bu kodda dikkat edilmesi gereken üç nokta var. Birincisi, `ileri` içinde girdiyi `self.X` olarak sakladık; geri geçişte `dW = Xᵀ d` için buna ihtiyacımız var. İkincisi, `geri` fonksiyonu `d`yi `dL/dZ` olarak alır ve `dL/dX = d Wᵀ` olarak döndürür; bu da bir önceki katmanın gradyanıdır. Üçüncüsü, `ReLU.geri` maskeyi `self.Z > 0` ile uygular: türev `0` ya da `1` olduğu için çarpma yerine maske kullanmak yeterlidir.

İkinci parça, ReLU ve Tanh sınıflarını ile log-sum-exp tabanlı `log_softmax` fonksiyonunu içerir. Katmanları bir listede tutan `Ag` sınıfı ise 63.7'de gelir; ileri geçişi sıralı, geri geçişi ters sırada çağırır. Bu, Bölüm 55'teki hesap grafiğinin ters mod taramasının elle yazılmış bir karşılığıdır.

@@KOD sinir.py 31 53@@

Kayıp katmanını ve `Ag` sınıfını 63.7'de, türetmeleriyle birlikte veriyoruz. Burada bilmen gereken şu: `Ag.ileri` katmanları sırayla çağırır, `Ag.geri` onları tersten çağırır ve `mlp` fonksiyonu katman listesini boyutlardan kurar.

## 63.7 Geri yayılımın tam türetmesi

Geri yayılım, zincir kuralının bir hesap grafiği üzerinde verimli uygulanmasıdır. Bölüm 55'te bunu skaler değerler için yaptık. Şimdi aynı fikri matrisler için, MLP'nin tam şekilleriyle yapacağız.

**Adım 1: Çıkış kaybı.** Bir örnek için sınıf sayısı `K`, gerçek etiket one-hot vektör `y`, ağın logit çıktısı `z ∈ ℝᴷ` olsun. Softmax olasılıkları `p_k = e^(z_k) / Σ_j e^(z_j)` ve çapraz entropi kaybı `L = −Σ_k y_k log p_k`dır (Bölüm 51.10).

**Adım 2: Softmax'ın türevi.** Bölüm 55'teki zincir kuralını kullanalım: `∂p_k / ∂z_j = p_k (δ_kj − p_j)`, burada `δ_kj` Kronecker deltasıdır. Zincir kuralı ile `∂L/∂z_j = Σ_k (−y_k / p_k) · p_k (δ_kj − p_j)`. Parantezi açarsak `∂L/∂z_j = −y_j + p_j Σ_k y_k`. One-hot `y`de `Σ_k y_k = 1` olduğundan sonuç `∂L/∂z_j = p_j − y_j`dir.

Yani çıkış katmanındaki gradyan yalnızca "tahmin eksi gerçek" farkıdır. Bu, softmax ile çapraz entropinin birlikte kullanılmasının en büyük armağanıdır: softmax'ın türevinin karmaşıklığı kaybın türevinde kendiliğinden sadeleşir (Bölüm 51.10 ve 55.6).

**Adım 3: Batch ortalaması.** Mini-batch'te `B` örnek varsa kayıp, örneklerin ortalamasıdır: `L = (1/B) Σ_i L_i`. Bu yüzden çıkış gradyanı `dL/dZ = (P − Y) / B`dir. Ortalamadaki `1/B` çarpanı burada bir kez yazılır ve geri kalan her gradyana otomatik yayılır.

**Adım 4: Bir Doğrusal katman.** `Z = H W + 1 bᵀ` olsun, burada `H` önceki katmanın çıktısı (`(B, d_in)`), `1` tüm birler vektörü ve `1 bᵀ` sapmanın her satıra eklenmesi. Gradyanları Z'nin `δ = ∂L/∂Z` (şekil `(B, d_out)`) cinsinden yazalım. Z'nin `(i, j)` elemanı `Z_ij = Σ_k H_ik W_kj + b_j` olduğu için:

- `∂L/∂W_kj = Σ_i H_ik δ_ij`, yani matris biçiminde `dW = Hᵀ δ` (şekil `(d_in, d_out)`).
- `∂L/∂b_j = Σ_i δ_ij`, yani `db = Σ_i δ_i` (şekil `(d_out,)`).
- `∂L/∂H_ik = Σ_j δ_ij W_kj`, yani `dH = δ Wᵀ` (şekil `(B, d_in)`).

Bu üç satırın hepsi, Bölüm 48'deki matris çarpımının şekil kuralına uyar. `dW`nin şekli her zaman `W`nin şeklidir; bu kontrol, bir çarpım sırası hatasını anında yakalar.

**Adım 5: Aktivasyon katmanı.** `H = φ(Z)` ise `∂L/∂Z = (∂L/∂H) ⊙ φ′(Z)` olur; `⊙` eleman bazlı çarpımdır. ReLU için `φ′(Z)` maskesi `Z > 0` ile verilir.

**Adım 6: Özyineleme.** Ağ `Z₁ → H₁ → Z₂ → H₂ → Z₃` biçiminde olsun. Çıkıştan başlayarak `δ₃ = (P − Y)/B` ile başlarız. Sonra her katmanda, `dW_l = H_{l−1}ᵀ δ_l`, `db_l = Σ δ_l`, ve bir önceki katmanın gradyanı `δ_{l−1} = (δ_l W_lᵀ) ⊙ φ′(Z_{l−1})`. Bu özyineleme, geri yayılımın özüdür.

Aşağıdaki tablo, 64-128-64-10 ağında her ara değerin şeklini özetliyor:

| Değer | Tanım | Şekil |
|---|---|---|
| X | girdi | (B, 64) |
| Z₁ | X W₁ + b₁ | (B, 128) |
| H₁ | ReLU(Z₁) | (B, 128) |
| Z₂ | H₁ W₂ + b₂ | (B, 64) |
| H₂ | ReLU(Z₂) | (B, 64) |
| Z₃ | H₂ W₃ + b₃ (logit) | (B, 10) |
| δ₃ | (P − Y)/B | (B, 10) |
| dW₃ | H₂ᵀ δ₃ | (64, 10) |
| δ₂ | (δ₃ W₃ᵀ) ⊙ ReLU′(Z₂) | (B, 64) |
| dW₂ | H₁ᵀ δ₂ | (128, 64) |
| δ₁ | (δ₂ W₂ᵀ) ⊙ ReLU′(Z₁) | (B, 128) |
| dW₁ | Xᵀ δ₁ | (64, 128) |

Şekil 63.5 aynı akışı kutularla gösteriyor: üstte ileri geçiş, altta geri geçiş.

@@SEKIL b63_geri_yayilim.png 63.5 Üstte ileri geçiş, altta geri geçiş. Geri geçişteki her ok, bir önceki katmanın gradyanını üretir; her dW kutusunun şekli ilgili W ile aynıdır.@@

Şimdi bu türetmeyi koda çeviriyoruz. Kayıp katmanı, bir softmax ve ortalama çapraz entropiyi birlikte hesaplar. Sayısal kararlılık için log-softmax'ı log-sum-exp hilesiyle yazıyoruz (Bölüm 63.14).

@@KOD sinir.py 54 77@@

Son olarak `Ag` sınıfı ve `mlp` fonksiyonu gelir. `mlp` fonksiyonu, boyut listesinden katmanları üretir: iki boyut arasında bir `Dogrusal`, son hariç her birinin ardından bir aktivasyon.

@@KOD sinir.py 78 107@@

Kodu okurken her `Dogrusal.geri`nin iki iş yaptığını gör: parametre gradyanlarını kendi üzerinde saklar, girdi gradyanını ise döndürür. Parametre güncellemesi bu gradyanları kullanır (Bölüm 63.9). Bu tasarım, bir katmanın yalnızca kendi gradyanlarını bildiği, kalan her şeyi geri yolla öğrendiği bir yapıdır.

## 63.8 Gradient check: türetmeyi sayıyla sınamak

Bir türetmenin doğru olup olmadığını bilmenin en güvenilir yolu, onu sayısal bir türevle karşılaştırmaktır. Merkezi fark formülü, bir parametrenin türevini `ε` küçük bir adımla şöyle tahmin eder:

∂L/∂θ ≈ (L(θ + ε) − L(θ − ε)) / (2ε)

Bu formülün hatası `O(ε²)` mertebesindedir (Bölüm 50.3). `ε` çok küçülürse ise kayan nokta yuvarlama hatası büyür: `L` değerinin kesinliği `10⁻¹⁶` civarında olduğu için fark bölünmesi hatayı `10⁻¹⁶ / ε` kadar büyütür. Bu iki hatanın dengelendiği nokta `ε ≈ 10⁻⁵`tir ve çift duyarlıklı (float64) sayılarla bu noktada göreli hata genellikle `10⁻⁷`nin çok altına iner.

Karşılaştırmayı mutlak farkla değil göreli farkla yapıyoruz: `|g − ĝ| / max(|g| + |ĝ|, 10⁻¹²)`. Mutlak fark, gradyan büyüklüğüne bağlıdır; göreli fark değildir. Eşik olarak `10⁻⁷` alıyoruz. Bölüm 51'de bir softmax çapraz entropi türevi için aynı kontrolü `7,3 × 10⁻¹¹` mertebesinde bir hatayla yapmıştık.

Aşağıdaki program dört katmanlı bir ağın tüm parametrelerini sınıyor. İkinci bir ağda ReLU'nun türev maskesini bilerek kaldırıyoruz. Amaç, kontrolün gerçekten bir hatayı yakalayıp yakalayamadığını görmek.

@@KOD t03_gradcheck.py 1 32@@

Kontrol fonksiyonu, her parametreyi tek tek değiştirir, ileri geçişi iki kez çalıştırır ve sayısal türevi analitik olanla karşılaştırır. Parametre sayısı kadar ileri geçiş gerektiği için bu yöntem yalnızca küçük ağlarda ve test amaçlı kullanılır. Büyük bir ağda her eğitimden önce yapılmaz.

@@KOD t03_gradcheck.py 33 54@@

Çıktı şöyle:

@@CIKTI t03_gradcheck.py out_t03_gradcheck.txt@@

Doğru türetmede en büyük göreli hata `1,03 × 10⁻⁹`dur; eşiğin (`10⁻⁷`) yüz kat altında. Bozuk ağda ise maskenin altındaki iki katmanın her ağırlığı ve sapması `1,00` hata veriyor. Son katmanın gradyanı bozuk maskeden önce hesaplandığı için temiz kalıyor; bu, hatanın nerede başladığını gösterir.

::: ipucu
Gradient check'i bir test olarak yaz ve her değişiklikten sonra çalıştır. İlk yazdığın geri yayılım neredeyse her zaman bir yerde yanlıştır. Hangi parametre grubunun hatalı olduğu, sonuç tablosunda satır satır görünür.
:::

## 63.9 Eğitim döngüsü ve ağırlık başlatma

Eğitim, mini-batch stokastik gradyan inişidir (Bölüm 50.6). Her adımda rastgele bir örnek grubu seçilir, kayıp ve gradyan hesaplanır, parametreler `θ ← θ − η ∇L` ile güncellenir. Bir epoch, eğitim kümesinin tamamının bir kez kullanılmasıdır. Her epoch başında veri karıştırılır; aksi hâlde ağ örneklerin sırasını öğrenir.

Öğrenme oranı `η` en önemli hiperparametredir. Çok küçükse eğitim yavaş ilerler; çok büyükse kayıp salınır ya da ıraksar (Bölüm 63.14). Adam ve benzeri uyarlamalı yöntemler ile öğrenme oranı takvimleri Bölüm 64'te ele alınacak; bu bölümde yalın SGD kullanıyoruz.

Aşağıdaki kod eğitim adımının dört parçasını tanımlar: bir adımda ileri geçiş ve geri geçiş (`ileri_geri`), parametre güncellemesi (`sgd_adim`), tahmin ve doğruluk.

@@KOD sinir.py 108 129@@

Burada `sgd_adim`, L2 cezasını (`lam`) gradyana ekler: `dW + λW`. Bu, `L + (λ/2)‖W‖²` kaybının türevidir. Sapmaya ceza uygulanmaz; bu, Bölüm 58'deki düzenlileştirme kuralıyla aynıdır.

### Ağırlık başlatma neden önemli?

Başlatma, eğitimin ilk adımından önce ağırlıkların değerlerini seçmektir. Üç sorunu var.

Birincisi simetri sorunudur. Tüm ağırlıklar aynı sabit değerle başlarsa, aynı katmandaki bütün birimler her zaman aynı işi yapar ve aynı gradyanı alır. Birimler ayrışmaz; ağın kapasitesi birim sayısından çok daha küçük kalır. Bunu sınamak için ağırlıkları sabit `0,1` yapıp 200 adım eğitiyoruz. Sıfır başlatma ise daha da kötü: tanh katmanında hem ağırlıklar hem sapmalar sıfırsa, çıkış sabit kalır ve kayıp `ln 10 ≈ 2,3026`ya yakın bir değerde (deneyde `2,3025`) donar.

İkincisi aktivasyonların patlaması ya da sönmesidir. Bir katmanda `z = Σᵢ wᵢ xᵢ` ise ve `wᵢ`, `xᵢ` bağımsız ve sıfır ortalamalıysa, `Var(z) = n · Var(w) · Var(x)`dir. Girdi `n` tane olduğundan, ağırlık varyansı `1/n` mertebesinde olmazsa katmanlar boyunca varyans çarpılır ya da küçülür. ReLU için bir ek faktör daha vardır: negatif yarı ölçülü olduğu için çıktının ikinci momenti yarıya düşer. Bu yüzden ReLU ağları için He başlatma `Var(w) = 2/n_in` kullanır. Tanh/sigmoid gibi simetrik aktivasyonlarda ve ileri ile geri yönün varyansını birlikte korumak için Xavier (Glorot) başlatma `Var(w) = 2/(n_in + n_out)` kullanılır (genel bilgi, Glorot ve Bengio 2010; He ve diğerleri 2015). Bu türetme sezgisidir; ayrıntılı ispatlar ve tanh/ReLU'ya göre seçim Bölüm 64'te.

Aşağıdaki program beş başlatma yöntemini aynı ReLU ağında karşılaştırır: sıfır, küçük (`sd = 0,01`), büyük (`sd = 1`), Xavier ve He. Her gizli katmanın aktivasyon standart sapmasını ve sıfır oranını ölçüyor. Ayrıca simetri deneylerini de koşuyor.

@@KOD t05_baslatma.py 1 36@@

Simetri ve kıvrım deneyleri bu programın ikinci kısmındadır.

@@KOD t05_baslatma.py 37 68@@

Çıktı:

@@CIKTI t05_baslatma.py out_t05_baslatma.txt@@

Tablonun ilk üç satırı açık: sıfır başlatmada hiçbir sinyal ilerlemez; küçük başlatmada aktivasyon her katmanda yaklaşık on kat sönümlenir (`2,3 × 10⁻²`den `1,7 × 10⁻⁴`e); büyük başlatmada ise her katmanda sekiz–on kat büyür (`2,3`ten `167`ye). He başlatmada standart sapma üç katman boyunca neredeyse sabittir (`0,41`den `0,46`ya). Xavier başlatma, ReLU için beklenenden biraz fazla küçültür (`0,235`ten `0,133`e) çünkü ReLU ikinci momenti yarıya indirir. Sıfır oranı, ReLU'nun simetrik girdilerde yaklaşık yarısının sıfır olmasından gelir (`0,49`).

Simetri satırları da net: sabit `0,1` başlatmada birimler arası fark tam `0`dır; ağ doğruluk `0,103`te, yani şans düzeyinde kalıyor. Rastgele küçük başlatma ise `0,883`e ulaşıyor. `W₁ = 0` ama `W₂` rastgele olan durumda bile ağ öğreniyor (`0,889`), çünkü `W₂`nin farklı satırları gizli birimlere farklı gradyanlar gönderiyor. Her iki katman da sıfırsa ağ hiçbir şey öğrenmez.

@@SEKIL b63_baslatma.png 63.6 Sol: her gizli katmanda aktivasyonun standart sapması (log ölçek). Sağ: sıfır aktivasyon oranı. He başlatma sinyali korur; küçük ve büyük başlatmalar sırasıyla sönümlenir ve patlar.@@

## 63.10 İlk gerçek eğitim: `load_digits` üzerinde

Artık her şeyi bir araya getirebiliriz. Veri kümesi, scikit-learn'ün `load_digits` fonksiyonu: 1797 örnek, her biri 8×8 piksel, değerler `0`dan `16`ya tam sayılar. Her rakam bir sınıf (0-9). Piksel değerlerini `16`ya bölerek `[0, 1]` aralığına getiriyoruz. Verinin bölünmesi Bölüm 54.7'deki disiplinle yapılıyor: yüzde 60 eğitim, yüzde 20 doğrulama, yüzde 20 test; bölme sınıf oranlarını koruyor (stratified) ve bölme tohumu sabit. Tohum bölmeyi değiştirmiyor; ağın başlatma ve karıştırma tohumları ise ayrı.

Dikkat: test kümesi bu bölümde yalnızca bir kez, son raporda kullanılıyor. Öğrenme oranı ve düzenlileştirme seçimi yalnızca doğrulama kaybına bakarak yapılıyor. Bu, Bölüm 54'te "test kümesini seçim için kullanma" dediğimiz hatanın önlenmesidir.

Taban çizgisi (baseline) olarak aynı eğitim kodunu bir katmanlı softmax regresyonuna uyguluyoruz: `64 → 10`. Bölüm 58'de bu modelin neden güçlü bir referans olduğunu görmüştük. Ağımız bu taban çizgisini ancak anlamlı bir fark yaratırsa "kazanmış" sayılır.

Aşağıdaki kod, veriyi yükler ve eğitim döngüsünü verir.

@@KOD sinir.py 130 148@@

Ana deney programı üç ana adımdan oluşuyor: öğrenme oranı seçimi, L2 seçimi ve beş tohumla son değerlendirme. Önce eğitim fonksiyonu gelir: her epoch sonunda eğitim ve doğrulama kayıp/doğruluklarını kaydeder ve isteğe bağlı olarak erken durdurma uygular.

@@KOD t06_digits.py 1 17@@

@@KOD t06_digits.py 18 43@@

Sonra iki model kurucusu gelir: baseline ve 64-128-64-10 MLP. Öğrenme oranı seçimi bu fonksiyonları kullanır.

@@KOD t06_digits.py 44 62@@

Öğrenme oranı ve L2 katsayısını doğrulama kaybına göre seçen kısım ise şudur.

@@KOD t06_digits.py 63 72@@

Son değerlendirme: dört yapılandırmayı beş tohumla eğitip test kümesinde ölçüyor, eğri ve tohum sonuçlarını yazdırıyoruz.

@@KOD t06_digits.py 73 104@@

@@KOD t06_digits.py 105 117@@

Son olarak karışıklık matrisi, ilk katman ağırlıkları, PCA ve modelin kaydı.

@@KOD t06_digits.py 118 134@@

@@KOD t06_digits.py 135 155@@

@@KOD t06_digits.py 156 161@@

Programın çıktısı:

@@CIKTI t06_digits.py out_t06_digits.txt@@

Önce öğrenme oranı seçimine bak. Dört değer için doğrulama kaybı `0,01`de `0,092`den, `0,3`te `0,035`e iniyor. En büyük değerin (`0,3`) seçilmiş olması bir uyarı işareti: ızgaranın üst sınırı kazanıyor, yani daha büyük değerler de denenmeliydi. Yine de daha büyük değerlerle eğitim doğrulama kaybını artırabilir; bu bölümde ızgarayı genişletmiyoruz ama bu sınırı açıkça belirtmek gerekir. L2 seçiminde ise λ = 0 en düşük doğrulama kaybını veriyor (`0,0352`). Bu nedenle L2 yapılandırmasında sıfır dışındaki en iyi değer (`λ = 10⁻⁴`) kullanılıyor ve metinde bunun bir tercih olduğu söyleniyor: seçim sıfır olsaydı yapılandırma erken durdurmayla aynı olurdu.

Son tablo, beş tohumun ortalamasını ve sapmasını veriyor. Baseline `0,972 ± 0,001`. MLP düzenlileştirmesiz 200 epoch sonunda `0,975 ± 0,003`. Erken durdurmalı MLP `0,973 ± 0,003`, L2 ile birlikte `0,972 ± 0,002`. Dürüst okuma şu: MLP baseline'dan belirgin biçimde daha iyi değil. Fark (`0,003`) tohumlar arası sapmanın (`0,001`-`0,003`) içinde kalıyor ve test kümesi yalnızca 360 örnek içeriyor. Bu kümede bir örnek `0,28` puan demek. Yani bu veri kümesinde derin bir ağ, iyi bir lojistik regresyonu ancak çok az geçiyor. Bu sonuç bir başarısızlık değil; `load_digits` küçük ve görece kolay bir veri kümesi, ve bir taban çizgisinin gücünü gösteriyor.

Eğitim doğruluğu sütunu ise farklı bir hikâye anlatıyor: MLP'nin eğitim doğruluğu `1,000`e ulaşıyor. Eğitim kümesini tamamen ezberliyor. Bu, bir sonraki bölümün konusu olan aşırı uydurmanın tipik bir işaretidir.

@@SEKIL b63_egri.png 63.7 Sol: eğitim ve doğrulama kaybı (log ölçek). Sağ: doğruluklar. Eğitim kaybı sürekli düşerken doğrulama kaybı bir noktadan sonra yatay gidiyor.@@

Şekil 63.7, düzenlileştirmesiz MLP'nin tohum 0 eğrisini gösteriyor. Eğitim kaybı, epoch sayısı arttıkça yaklaşık bir büyüklük mertebesi daha düşüyor; doğrulama kaybı ise bir noktada yatay kalıyor ve hafifçe dalgalanıyor. Aradaki açıklık, modelin eğitim verisine özgü ayrıntıları öğrendiğini gösteriyor.

@@SEKIL b63_karisiklik.png 63.8 Test kümesinde karışıklık matrisi (L2 yapılandırması, tohum 0). Köşegen dışındaki sayılar hatalardır; toplam dokuz hata vardır.@@

Karışıklık matrisi (Bölüm 57.2'nin ikili ölçülerinin çok sınıflı hâli) hataların dağılımını gösteriyor: 360 örnekte yalnızca dokuz hata var. En sık karışan çift, gerçek `1`in `8` olarak tahmin edilmesi (üç kez). Bu da görsel olarak mantıklı: 8×8 çözünürlükte `1` ile `8`in ince çizgileri birbirine yakın. Bölüm 57'de gösterdiğimiz gibi, bir ortalama doğruluğun arkasında hangi sınıfların zorlandığını görmek, model seçimi için doğruluğun kendisi kadar önemlidir.

## 63.11 Aşırı uydurma ve düzenlileştirme

Aşırı uydurma (overfitting), modelin eğitim kümesindeki gürültüye ve tesadüfi ayrıntılara uyum sağlaması, bunun sonucunda yeni veride kötüleşmesidir. Bölüm 54.6'da sapma-varyans dengesi olarak görmüştük. Bir sinir ağında belirtisi, eğitim kaybı düşmeye devam ederken doğrulama kaybının düşmeyi bırakıp artmaya başlamasıdır.

Bizim ağımızda bu olay şekil 63.7'de görülüyor. Eğitim doğruluğu epoch 20 civarında `1,000`e ulaşıyor ve kalıyor; doğrulama doğruluğu ise `0,99` civarında sabit. Eğitim kaybı hâlâ düşüyor ama bu yalnızca ezberleme derinleşiyor demektir. Çıktıdaki sayılar bunu doğrular: tohum 0 için düzenlileştirmesiz MLP'nin doğrulama kaybı en düşük değerine (`0,0352`) epoch 28'de ulaşıyor; 200. epoch'ta doğrulama kaybı `0,0376`ya çıkarken eğitim kaybı `0,00027`ye iniyor. Erken durdurmanın beş tohumda seçtiği en iyi epoch'lar 23 ile 30 arasında. Erken durdurma (early stopping), doğrulama kaybının en düşük olduğu epoch'un ağırlıklarını geri yükleyerek bu durumu önler. Bu basit bir kural: `k` epoch boyunca doğrulama kaybı iyileşmediyse dur ve en iyi noktayı al.

L2 düzenlileştirme (ağırlık azaltma), kayba `(λ/2)‖W‖²` terimini ekler ve gradyanı `λW` kadar değiştirir. Büyük ağırlıklar ceza yer; ağ daha düz, daha az keskin bir fonksiyon öğrenir. Bu, Bölüm 58.7'deki Ridge regresyonunun sinir ağlarındaki karşılığıdır. Bizim deneyimizde bu ceza doğrulama kaybını sıfır dışındaki değerlerde kötüleştirdi (`λ = 10⁻³` ve `10⁻²` için `0,042` ve `0,152`). Yani bu veri kümesinde ve bu eğitim süresinde L2 faydalı değil. Bu bir öğrenme: bir düzenlileştirme tekniğinin işe yaraması veriye ve eğitim sürecine bağlıdır, bir kural değildir.

Dropout ve batch normalizasyon gibi daha güçlü teknikler Bölüm 64'te; küçük veri kümelerinde veri artırma ve transfer öğrenme ise Bölüm 66'da gelecek.

## 63.12 Ağın içinde: ağırlıklar ve gizli temsil

Eğitimli bir ağın iç yapısına bakmak, ne öğrendiğine dair bir fikir verir. Şekil 63.9'un solu ilk gizli katmanın ilk 16 biriminin ağırlıklarını 8×8 görüntü olarak gösteriyor. Görüntüler kırmızı ve mavi renk skalasında: kırmızı pozitif ağırlık, mavi negatif ağırlık. Dürüst bir okuma: çoğu birim gürültülü ve yorumlanması zor bir desen taşıyor. Birkaç birimde kenar ya da çizgi benzeri yapılar var; ama bu, ağın insan tarafından okunabilir tek bir kural öğrendiğini göstermez. Derin ağların iç temsilleri dağınıktır; bunu yorumlamak için Bölüm 78'de anlatılacak açıklanabilirlik yöntemlerine ihtiyaç var.

Şekil 63.9'un sağı, ilk gizli katmanın aktivasyonlarını test kümesinde PCA ile iki boyuta indiriyor. PCA, merkezlenmiş veri matrisinin tekil değer ayrışımıyla (SVD, Bölüm 48.13) en büyük varyanslı iki yönü seçer. İlk iki bileşen toplam varyansın yaklaşık `%22`sini ve `%17`sini açıklıyor; yani iki boyutta bütün yapının yalnızca üçte biri görünüyor. Yine de şekilde `0`, `4`, `6` ve `9` rakamları ayrı bölgelerde toplanıyor; `1` ve `7` alt kısımda kümeleniyor; `2`, `3`, `5` ve `8` ise merkezde birbirine karışıyor.

@@SEKIL b63_agirlik_pca.png 63.9 Solda ilk gizli katmanın 16 biriminin ağırlıkları, 8×8 görüntü olarak (kırmızı pozitif, mavi negatif). Sağda aynı katmanın aktivasyonlarının test kümesindeki PCA izdüşümü, sınıfa göre renkli.@@

Bu izdüşüm, Bölüm 61'deki t-SNE ve UMAP ile karşılaştırıldığında daha kaba bir görüntü verir: PCA doğrusaldır, bu yüzden kümeleri ayırmakta sınırlıdır. Yine de doğrusal bir izdüşümde sınıfların bir kısmının ayrılması, ağın gizli katmanının işe yarar bir temsil öğrendiğine işaret eder; kesin doğruluk ise yukarıdaki `%97`lik sonuçtan gelir. Son katmanın doğrusal sınıflandırıcısı, bu temsilin üzerinde çalışır.

## 63.13 Hesap maliyeti: parametre, FLOP ve batch boyutu

Bir ağın maliyeti üç şeyle ölçülür: bellekteki parametre sayısı, işlem sayısı (FLOP) ve gerçek süre. Bizim ağımızın parametre sayısını elle sayalım: `64·128 + 128 + 128·64 + 64 + 64·10 + 10 = 8192 + 128 + 8192 + 64 + 640 + 10 = 17.226`. Bunların 17.024'ü ağırlık, 202'si sapmadır.

Bir ileri geçişte bir `Dogrusal` katmanı `d_in · d_out` çarpma ve benzer sayıda toplama yapar; kabaca `2 · d_in · d_out` FLOP. Bizim ağda örnek başına ileri geçiş `2 · (64·128 + 128·64 + 64·10) = 34.048` FLOP. Geri geçiş ise her katman için iki matris çarpımı içerir (`dW = Hᵀδ` ve `dH = δWᵀ`), dolayısıyla kabaca ileri geçişin iki katı. Toplam eğitim adımı örnek başına yaklaşık `3` kat ileri geçiş, yani `102.144` FLOP. Bu bir yaklaşıklıktır; aktivasyon ve kayıp hesapları da eklenir ama bunlar matris çarpımının yanında küçük kalır.

Gerçek süre, FLOP sayısından fazlasına bağlıdır. Küçük batch'lerde Python döngüsünün ve NumPy'ın çağrı ek yükünün (overhead) hakim olduğunu, büyük batch'lerde ise matris çarpımının BLAS kütüphanesinde verimli çalıştığını görmek istiyoruz (Bölüm 48.14). Aşağıdaki program, aynı ağı batch boyutlarının farklı değerleriyle bir epoch eğitip süreyi ve saniyedeki örnek sayısını ölçer.

@@KOD t07_batch.py 1 16@@

@@KOD t07_batch.py 17 30@@

@@KOD t07_batch.py 31 43@@

Çıktı:

@@CIKTI t07_batch.py out_t07_batch.txt@@

Tablonun eğimi açık: batch `1`den `256`ya çıktıkça saniyedeki örnek sayısı `4.148`den `137.859`a çıkıyor. Yani ağ aynı, FLOP aynı; yalnızca iş paketlerinin büyüklüğü değişiyor. `256`dan sonra verim artışı durgunlaşıyor: `256` batch'te bir epoch `7,8` ms, `1078` tam batch'te (bir epoch tek adım) `6,4` ms sürüyor. Bu bir ölçüm ve makineye bağlı: aynı program başka bir çalıştırmada birkaç kat farklı mutlak süre verebilir. Bu nedenle sadece sıralamaya ve eğilime bak, mutlak sayılara değil. Ölçümler tek bir çalıştırmadan geliyor; ciddi bir karşılaştırma için tekrar ve ortalama gerekir.

Bu sonuç mühendislik açısından önemlidir: GPU'da da benzer bir eğilim görülür, ama orada ek yükün etkisi daha büyüktür ve yeterince büyük batch'ler gerekir (Bölüm 65 ve 76). Bellek sınırı da batch boyutunu belirler; 6 GB'lık bir GPU'da ağın kendisi küçük olsa da batch'in aktivasyonları bellekte yer kaplar.

@@SEKIL b63_batch.png 63.10 Batch boyutuna göre bir epoch süresi (sol, log-log) ve saniyedeki örnek sayısı (sağ). Ölçüm tek çalıştırma, CPU, NumPy.@@

## 63.14 Sayısal sağlamlık: taşma, log(0) ve ıraksama

Kâğıtta doğru olan bir formül, bilgisayarda yanlış çalışabilir. Üç klasik tuzak var.

Birincisi, softmax taşmasıdır. `e^z` `z` büyükse taşar. Bu durumda payda sonsuz olur ve olasılıklar `NaN` (sayı değil) çıkar. Çözüm log-sum-exp hilesidir: en büyük logit'i çıkarırsın, `softmax(z) = softmax(z − max z)`; sonuç değişmez ama üst sınır `0` olur. Bizim `log_softmax` fonksiyonumuz bunu yapar (Bölüm 55.13'teki aynı tuzak).

İkincisi, `log(0)` tanımsızdır. Çapraz entropi `−y log p` olduğu için tahmin `p = 0` olursa kayıp sonsuz olur. Naif yazımda bir `1e-12` gibi küçük bir sayı eklemek bunu geçici olarak çözer ama doğru değildir; kararlı yol `log p`yi doğrudan log-softmax'tan hesaplamaktır.

Üçüncüsü, öğrenme oranı çok büyükse eğitim ıraksar. Bu tuzağı yukarıdaki ölü ReLU deneyinde zaten gördük; bu kez ağırlıkların büyüklüğüne bakıyoruz.

Aşağıdaki program üç tuzağı gösteriyor ve öğrenme oranı taramasını yapıyor. Tarama, eğitim sırasında kaybın sonlu olup olmadığını denetler ve ağırlıkların en büyük mutlak değerini izler.

@@KOD t08_kayma.py 1 19@@

@@KOD t08_kayma.py 20 52@@

Çıktı:

@@CIKTI t08_kayma.py out_t08_kayma.txt@@

Naif softmax, `z = [1000, 1001, 999]` için `nan` veriyor. Kararlı sürüm ise aynı girdiyi en büyük elemanı çıkararak `[0, 1, −1]`e indirir ve doğru olasılıkları verir: `0,245`, `0,665`, `0,090`. `p = 0` için naif çapraz entropi `inf`; kararlı sürüm `z = [-800, 800]` için `1600`ü, yani doğru değeri veriyor.

Öğrenme oranı taraması daha öğreticidir. `0,1` ve `1,0` arasında ağırlıklar makul kalıyor; `1,0`da bile doğruluk düşüyor (`0,292`). `5,0`da maksimum ağırlık `1,27 × 10⁴`e çıkıyor ve doğruluk şans düzeyine (`0,097`) iniyor. `20,0`da ağırlıklar `10⁷` mertebesine ulaşıyor. Dikkat et: softmax çapraz entropisinde gradyan `P − Y` ile sınırlıdır, bu yüzden kayıp çoğu zaman `NaN` olmaz; ıraksama büyük ağırlıklar ve çökmüş bir doğruluk olarak görünür. Regresyonda, kare hata kaybıyla çalışan bir ağda gradyan sınırsız olduğu için ıraksama `NaN` ile çok daha sık kendini gösterir. Bu yüzden her eğitimde kayıp ve ağırlık normlarını izlemek ve `NaN` denetimi koymak bir alışkanlık olmalı.

::: dikkat
Üretim kodunda `NaN` denetimini eğitim döngüsüne koyan ve kayıp sonlu değilse eğitimi durduran bir kontrol olmadan eğitim başlatma. Sessiz bir ıraksama, bir gece boyunca çalışıp bir anlam ifade etmeyen bir model üretebilir.
:::

## 63.15 Gömülü köprü: int8 çıkarım ve PyTorch

Bu ağı bir mikrodenetleyicide çalıştırmak istiyorsak, Bölüm 46'daki tamsayı hattını kullanırız. Simetrik, tensör başına (per-tensor) kuantizasyonda bir ağırlık matrisi `W` için ölçek `s = max|W| / 127` ve tamsayı değeri `q = round(W / s)`dir; `q` `[-127, 127]` aralığında int8 olur. Girdi ve gizli aktivasyonlar da benzer biçimde kuantize edilir; gizli katmanların ölçeği eğitim kümesinden kalibre edilir. İki tamsayı matrisinin çarpımı int32 biriktiricide yapılır, ardından çıktı yeniden ölçeklenip bir sonraki katmanın tamsayısına dönüştürülür.

Aşağıdaki program eğitilmiş ağı bu şekilde tamsayı aritmetiğiyle çalıştırıyor ve doğruluğu float32 sonucuyla karşılaştırıyor. Bu bir ana bilgisayar simülasyonudur: kod Python'da yazılmıştır ve ARM'a derlenmiş bir C çekirdeği değildir; ARM derlemesi ve Cortex-M4 üzerindeki ölçüm Bölüm 46'da yapılır.

@@KOD t09_int8.py 1 36@@

@@KOD t09_int8.py 37 71@@

Çıktı:

@@CIKTI t09_int8.py out_t09_int8.txt@@

Test doğruluğu int8 ile float32 arasında değişmiyor (`0,975`), ve iki modelin tahminleri 360 örneğin tamamında aynı (uyum `1,000`). Bellek açısından fark büyük: float32 ağırlık ve sapmalar `68.904` bayt tutuyor; int8 ağırlıklar ve int32 sapmalar ise `17.832` bayt, yani yaklaşık dörtte bir. Bir STM32 ailesinde, bu büyüklükteki bir model flash'a sığar; ama asıl ölçüt, bu bellek ve işlem bütçesinin gerçek donanımda ne kadar sürdüğüdür (Bölüm 46.9 ve 46.11).

Şimdi aynı ağın PyTorch'ta nasıl göründüğüne bakalım. Bu bölümün çerçevesi NumPy olduğu için PyTorch kodunu yalnızca bir doğrulama olarak veriyoruz: aynı ağırlıklarla aynı kaybı ve aynı gradyanı hesaplıyor mu? Bölüm 65'te PyTorch'un tensörlerini, autograd'u ve eğitim döngüsünü ayrıntılı göreceğiz.

Aşağıdaki programın ilk kısmı NumPy tarafında kaybı ve gradyanı hesaplar, PyTorch ağını aynı ağırlıklarla kurar.

@@KOD t10_torch.py 1 21@@

İkinci kısım PyTorch geri geçişini çalıştırır ve gradyanları karşılaştırır.

@@KOD t10_torch.py 22 43@@

Çıktı:

@@CIKTI t10_torch.py out_t10_torch.txt@@

PyTorch'un `nn.Sequential` ile kurduğu ağ, bizim elle yazdığımız geri yayılımla aynı kaybı (`0,008927349120`) ve aynı gradyanları veriyor; göreli fark `10⁻¹⁵` mertebesinde, yani float64 yuvarlama hatası düzeyinde. Bu, geri yayılım türetmemizin ve kodumuzun doğru olduğunun ikinci bağımsız kanıtıdır. Gradient check bir sayısal kanıttı; PyTorch karşılaştırması ise ayrı bir kütüphanenin autograd'uyla yapılan bağımsız bir doğrulamadır.

Bu köprü bir amaca hizmet eder: PyTorch'ta yazdığın her ağı, elle yazılmış bir referansla karşılaştırabilmen. Bölüm 65'te göreceğin gibi, `loss.backward()` tek satırının arkasında aynı türev zinciri vardır.

## Kod Okuma Egzersizi: scikit-learn'ün MLP geri yayılımı

Scikit-learn kütüphanesi, `MLPClassifier` ve `MLPRegressor` sınıflarında bizimkine benzer bir NumPy geri yayılımı kullanır. Bu kodu, kendi türetmenle satır satır karşılaştırarak okuyacağız. Kesitlerde 70 sütunu aşan satırlar okunabilirlik için boşluktan bölünmüştür; hiçbir ifade değişmemiştir. Kaynak, kurulu scikit-learn 1.8.0 sürümünün `sklearn/neural_network/_multilayer_perceptron.py` dosyasıdır ve aşağıdaki kesitler bu dosyadan birebir alınmıştır.

İlk kesit, bir katmanın parametre gradyanlarını hesaplayan `_compute_loss_grad` yöntemidir (satır 226–238). Bu, bizim `Dogrusal.geri` içindeki `dW = Xᵀd` ve `db = Σd` işlemlerinin karşılığıdır; ayrıca L2 cezasını da ekler.

@@SKL _multilayer_perceptron.py 226 238@@

İkinci kesit, geri geçişin kendisidir (satır 370–393). Çıkıştan başlayarak her katmanın `delta`sını hesaplar ve bir önceki katmana geçer. Satır 374, bizim Adım 2'deki `p − y` sonucudur.

@@SKL _multilayer_perceptron.py 370 393@@

Üçüncü kesit, ReLU'nun türev maskesidir: `scikit-learn/neural_network/_base.py` içindeki `inplace_relu_derivative` (satır 142–150). Sayıları kendi maskemizle karşılaştır: orada gradyan, ileri geçişte saklanan aktivasyonun sıfır olup olmadığına göre sıfırlanır.

@@SKL _base.py 142 150@@

**Sorular — cevaplamadan geçme:**

1. Satır 374'te `deltas[last] = activations[-1] - y` yazılmış. Bu ifade hangi kayıp–aktivasyon çiftinde geçerlidir? Yorumdaki üç kombinasyonu tek tek adlandır ve neden bunların hepsinde aynı sadeleşmenin olduğunu Adım 2'deki türetmeyle açıkla.
2. `_compute_loss_grad` içinde gradyan `safe_sparse_dot(activations[layer].T, deltas[layer])` ile hesaplanıyor. Bizim `dW = Hᵀδ` ifademizle eşleşen şekil tutarlılığını göster: `activations[layer]` ve `deltas[layer]` şekilleri nelerdir?
3. `coef_grads[layer] += self.alpha * self.coefs_[layer]` satırı, `_backprop`'un başında eklenen L2 cezasının türevidir. Sapmaya (`intercept_grads`) bu ceza neden eklenmiyor? Bu, bizim `sgd_adim` fonksiyonumuzdaki kuralla aynı mı?
4. Satır `coef_grads[layer] /= sw_sum` ile ortalama alınıyor. Bizim kodumuzda bu ortalama nerede yapılır? Ortalama, kaybın mı yoksa gradyanın mı ölçeklemesine bağlıdır ve bu fark neden önemlidir?
5. `inplace_relu_derivative` çağrısı `activations[i]` ile yapılıyor ve türev aktivasyonun kendisine bakarak uygulanıyor. Bizim `ReLU.geri` `self.Z > 0` kullanıyor. İkisi hangi durumlarda farklı sonuç verir? (İpucu: `z = 0` noktasına bak.)
6. Sklearn kodu `deltas` listesini her çağrıda yeniden kullanıyor, yani bellek ayırmaz. Bizim `Ag.geri` her seferinde yeni bir dizi döndürüyor. Bu tasarım farkının bellek ve hız üzerindeki etkisini tartış.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, zorluk sırasıyla ★, ★★, ★★ ve ★★★ olarak dizilmiştir. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntüyü bul, iyileştir ve doğrula. Doğrulama adımında elle iz sürme tablosu bulunur. Her örneğin sonunda, hiçbir yapay zekâ aracı kullanmadan çözebilmen için bir varyasyon sorusu vardır.

### Örnek 1 (★): AND kapısını algılayıcıyla öğrenmek

Bir algılayıcının iki girdili AND kapısını öğrenmesini izle. Başlangıç ağırlıkları `w = (0, 0)` ve `b = 0`, öğrenme oranı `η = 1`, karar kuralı `ŷ = [wᵀx + b ≥ 0]`. Örnekler sırayla `(0,0)`, `(0,1)`, `(1,0)`, `(1,1)` gelsin. Bu bir epoch'ta ağırlıkların nasıl değiştiğini bul.

**Adım 1 — Anla.** İstenen, bir epoch içinde her örnek için tahmini, hatayı ve güncellemeyi izlemek. Güncelleme kuralı `w ← w + η(y − ŷ)x`, `b ← b + η(y − ŷ)`.

**Adım 2 — Örnekle.** AND kapısının gerçek çıktısı `(0,0) → 0`, `(0,1) → 0`, `(1,0) → 0`, `(1,1) → 1`. Başlangıçta ağ her şeyi aynı sınıfa atamaya yatkın; ilk örnekte bir hata bekliyoruz.

**Adım 3 — Kaba çöz.** İlk örnekte `s = 0`, `ŷ = 1`, `y = 0`, yani `y − ŷ = −1`. Güncelleme: `w = (0,0) + (−1)(0,0) = (0,0)` ve `b = 0 − 1 = −1`. Diğer örnekleri aynı şekilde yürüt.

**Adım 4 — Örüntü.** Yanlış tahmin yapılan örneklerde sapma aşağı iniyor; yalnızca pozitif örnekte (`(1,1)`) ağırlık yukarı çekiliyor. Yani kural, pozitif örneğin girdilerini ağırlığa ekliyor ve negatif örneklerde sapmayı düşürüyor.

**Adım 5 — İyileştir.** İz tablosunu kendimiz çizerken her satırda önceki `w` ve `b`yi yazmak zorunda değiliz; yalnızca yeni değerleri takip etmek yeterli. Ayrıca iki kısmi kontrol yapabiliriz: bir epoch'ta hata sayısı azalıyor mu, ve son ağırlıklar tüm dört örneği doğru ayırıyor mu.

**Adım 6 — Doğrula.** İz tablosu:

| Örnek (x) | y | s = wᵀx + b | ŷ | y − ŷ | w sonrası | b sonrası |
|---|---|---|---|---|---|---|
| (0,0) | 0 | 0 | 1 | −1 | (0,0) | −1 |
| (0,1) | 0 | −1 | 0 | 0 | (0,0) | −1 |
| (1,0) | 0 | −1 | 0 | 0 | (0,0) | −1 |
| (1,1) | 1 | −1 | 0 | +1 | (1,1) | 0 |

Bu tablo ilk epoch'un sonunda `w = (1,1)`, `b = 0` veriyor. Programın çıktısındaki ilk epoch'un iki hatası (satır `hatalar=[2, …]`) bu tabloyla uyuşuyor. Tam öğrenme ise `w = (2,1)`, `b = −3` ile altı epoch'ta gerçekleşiyor.

**Bunu AI'sız yazabilir misin?** OR kapısı `(0,0) → 0`, `(0,1) → 1`, `(1,0) → 1`, `(1,1) → 1` için aynı tabloyu çiz ve ilk epoch'un sonunda ağırlıkları bul. Sonra iki kontrolle doğrula: ilk epoch'taki hata sayısı, tabloda işaretlediğin güncellemelerin sayısıyla aynı mı; son ağırlıklar dört örneği de doğru ayırıyor mu?

### Örnek 2 (★★): XOR için elle kurulmuş 2-2-1 ağı

Bölüm 63.2'de gördüğümüz gibi tek algılayıcı XOR'u çözemez. Bir gizli katman eklersek çözülebildiğini göster. Gizli birimler adım fonksiyonu `[· ≥ 0]` kullansın ve ağırlıkları elle seç: `h₁ = [x₁ + x₂ − 0,5 ≥ 0]` (VEYA), `h₂ = [x₁ + x₂ − 1,5 ≥ 0]` (VE), çıkış `y = [h₁ − h₂ − 0,5 ≥ 0]`.

**Adım 1 — Anla.** İstenen: üç ağırlık kümesinin (`h₁`, `h₂`, `y`) XOR'u doğru hesapladığını dört girdi için göstermek ve bu ağın neden bir katmanla yapılamadığını açıklamak.

**Adım 2 — Örnekle.** XOR'un dört girdisi: `(0,0)→0`, `(0,1)→1`, `(1,0)→1`, `(1,1)→0`. Girdi `(1,1)` burada tuzaktır; tek katmanlı algılayıcı için `(0,1)` ve `(1,0)`ı birbirinden ayırmak bile sorun değildir, ama `(0,0)` ve `(1,1)`i pozitif tarafın iki farklı tarafına koymak gerekir.

**Adım 3 — Kaba çöz.** `h₁` VEYA'dır: `x₁ + x₂ ≥ 1` iken `1`. `h₂` VE'dir: `x₁ + x₂ ≥ 2` iken `1`. Çıkış `h₁ − h₂` farkını kullanır: VEYA ama VE değilse `1` (yani tam olarak bir tane) olur.

**Adım 4 — Örüntü.** XOR, VEYA ile VE'nin farkıdır: `XOR = VEYA ∧ ¬VE`. Gizli katmanın işi, doğrusal olarak ayrılamayan bu bileşimi, her biri doğrusal olan iki çizgiye bölmektir.

**Adım 5 — İyileştir.** Sapmaları `h₁` ve `h₂` için `−0,5` ve `−1,5`, çıkış için `−0,5` seçtik. Bu değerler bir adım fonksiyonunun eşiklerini belirler; `0,5` gibi bir ayırıcı seçmek, tam sayılar üzerinde güvenli bir boşluk bırakır.

**Adım 6 — Doğrula.** İz tablosu:

| x₁ | x₂ | h₁ = [x₁+x₂−0,5 ≥ 0] | h₂ = [x₁+x₂−1,5 ≥ 0] | h₁ − h₂ − 0,5 | y | XOR |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | −0,5 | 0 | 0 |
| 0 | 1 | 1 | 0 | 0,5 | 1 | 1 |
| 1 | 0 | 1 | 0 | 0,5 | 1 | 1 |
| 1 | 1 | 1 | 1 | −0,5 | 0 | 0 |

Dört satırın hepsi doğru. Bu ağda toplam `9` sayı var: gizli katmanda 4 ağırlık ve 2 sapma, çıkışta 2 ağırlık ve 1 sapma. Bölüm 63.2'deki tek algılayıcının 3 sayısından farklı olarak, bu ağırlıklar bir gizli katmanla doğrusal olmayan bir bileşim kuruyor.

**Bunu AI'sız yazabilir misin?** `XNOR` (aynı olma) için bir 2-2-1 ağı kur. Gizli birimleri VEYA ve VE olarak seç, çıkış eşiğini sen belirle. Dört satırlık iz tablosunu yaz ve her satırda hangi eşiğin hangi yönde geçtiğini işaretle.

### Örnek 3 (★★): Tek örnekte tam geri yayılım

Bir ağ düşün: girdi `x = (2, 1)`, gizli katman 2 ReLU birim, çıkış 2 sınıflı softmax. Ağırlıklar `W₁ = [[1, −1], [0,5, 2]]`, `b₁ = (0, 0,1)`, `W₂ = [[0,5, −0,3], [0,2, 0,8]]`, `b₂ = (0, 0)`. Gerçek etiket `y = (1, 0)`. Kaybın ve tüm gradyanların değerini hesapla, sonra bunları sayısal olarak doğrula.

**Adım 1 — Anla.** İstenen: `L`, `dW₂`, `dW₁`, `db₁`. Şekiller: `dW₁` `(2, 2)`, `dW₂` `(2, 2)`.

**Adım 2 — Örnekle.** Bu örnekte ilk sınıf doğru sınıf. Ağın bunu yüksek olasılıkla tahmin etmesini bekliyoruz; kaybın küçük çıkması, ağın iyi bir yönde olduğunu gösterir.

**Adım 3 — Kaba çöz.** İleri geçiş. `z₁ = x W₁ + b₁ = (2·1 + 1·0,5, 2·(−1) + 1·2) + (0, 0,1) = (2,5, 0,1)`. ReLU sonrası `h = (2,5, 0,1)`, ikisi de pozitif. `z₂ = h W₂ = (2,5·0,5 + 0,1·0,2, 2,5·(−0,3) + 0,1·0,8) = (1,27, −0,67)`. Softmax: `p ≈ (0,874, 0,126)`, `L = −ln 0,874 ≈ 0,134`.

**Adım 4 — Örüntü.** Çıkış gradyanı `δ₂ = (p − y)/1 = (−0,126, 0,126)`. Geri geçiş: `dW₂ = hᵀ δ₂`, `db₂ = δ₂`, `δh = δ₂ W₂ᵀ` ve ReLU maskesi (her iki `z₁` pozitif olduğu için maske `(1,1)`), böylece `δz₁ = δh`. Son olarak `dW₁ = xᵀ δz₁` ve `db₁ = δz₁`.

**Adım 5 — İyileştir.** Ana bilgisayar hesabında ara değerleri tek tek saklamak yerine yalnızca her katmanın `dW`si ve `db`si için `Hᵀδ` ve `Σδ` formüllerini kullanmak yeterli. Ayrıca gradyanın yönünü sayısal olarak doğrulamak için sadece iki parametreye bakmak (bir `W₁` ve bir `W₂` girişi) yeterli.

**Adım 6 — Doğrula.** İz tablosu (değerler programın çıktısından):

| Değer | Hesap | Sonuç |
|---|---|---|
| z₁ | (2,5; 0,1) | ReLU maskesi (1; 1) |
| z₂ | (1,27; −0,67) | p = (0,874; 0,126) |
| L | −ln 0,874 | 0,134 |
| δ₂ | p − y | (−0,126; 0,126) |
| dW₂ | hᵀ δ₂ | [[−0,314; 0,314]; [−0,013; 0,013]] |
| dW₁ | xᵀ δz₁ | [[−0,201; 0,151]; [−0,101; 0,075]] |
| db₁ | Σδz₁ | (−0,101; 0,075) |

Programın çıktısı ile ondalık düzeyinde uyuşuyor, ve sayısal kontrol `dW₁[0,0]` ve `dW₂[1,1]` için analitik ile sayısal değerin aynı olduğunu gösteriyor (`−0,201037` ve `0,012565`). Bu iki değer, elle türetilmiş formüllerle hesaplanan sayıların doğruluğunu bağımsız olarak doğrular.

**Bunu AI'sız yazabilir misin?** Aynı ağda `y = (0, 1)` olsun. `δ₂`yi, `dW₂`yi ve `db₁`i hesapla. ReLU maskesinin değişip değişmediğini kontrol et; `z₁`in ikinci değerini negatif yapacak bir `b₁` seçersen ne olur?

Programın kendisi:

@@KOD t11_ornek3.py 1 16@@

@@KOD t11_ornek3.py 17 42@@

Çıktı:

@@CIKTI t11_ornek3.py out_t11_ornek3.txt@@

### Örnek 4 (★★★): Gizli birim sayısı, kapasite ve sapma

Bölüm 63.5'teki deneyin sonuçlarını kullanarak bir soru soruyoruz: bir ReLU ağının birim sayısı iki katına çıktığında hata ne kadar düşer, ve bu kazanç her zaman aynı mıdır? Tablo `(baslatma, gizli birim, egitim RMSE, test RMSE, sapma)` biçimindedir; yayılmış kıvrım satırlarını kullan.

**Adım 1 — Anla.** İstenen: `yayılmış` başlatmada `h = 2 → 8 → 32` geçişlerinin her birinde test RMSE'nin oranını ve farkını bulmak, ve bu oranların birim sayısıyla nasıl değiştiğini yorumlamak.

**Adım 2 — Örnekle.** Hedef `sin(3x) + 0,3x²`, aralık `[-2, 2]`. Bu fonksiyon yaklaşık iki tam salınım içerir. Kabaca, birkaç kıvrımla birinci salınımı, daha fazla kıvrımla ikinci salınımın detaylarını yakalamayı bekleriz.

**Adım 3 — Kaba çöz.** `h = 2`de test RMSE `0,547`, `h = 8`de `0,224`, `h = 32`de `0,070`. Oranlar: `0,224 / 0,547 ≈ 0,41`, `0,070 / 0,224 ≈ 0,31`. Yani `2`den `8`e (dört kat) geçişte hata `0,41` kat, `8`den `32`ye (dört kat) geçişte `0,31` kat oluyor.

**Adım 4 — Örüntü.** Hata birim sayısıyla azalıyor, ama bu oranlar yalnızca iki çiftten geliyor ve sapmalar büyük; bunu bir kuvvet yasası olarak yorumlamak için daha fazla birim sayısı ve tohum gerekir. `h = 32`de `0,070 ± 0,060` gerçek bir ölçümü, yerel minimumdaki tohum yüzünden şişirilmiş olabilir.

**Adım 5 — İyileştir.** Sapmanın nedenini ayıklamak için tohum bazında değerlere bak. Beş tohumun dördü `0,03`–`0,05` mertebesinde; biri `0,19` (yerel minimum). Dört tohumla yapılan ortalama `0,04` civarında olurdu. Dolayısıyla "birim sayısı arttıkça hata düşer" sonucu sağlam, ama `h = 32`nin gerçek kapasitesini ölçmek için daha fazla tohum ve eğitim bütçesi gerekir.

**Adım 6 — Doğrula.** İz tablosu:

| gizli birim | test RMSE (ortalama) | sapma | sıfır sapmayla RMSE |
|---|---|---|---|
| 2 | 0,547 | 0,133 | 0,639 |
| 8 | 0,224 | 0,085 | 0,310 |
| 32 | 0,070 | 0,060 | 0,323 |

Sıfır sapmayla başlatılan sütun, kapasitenin kullanılamadığını gösteriyor: `8` ve `32` birim neredeyse aynı hatayı veriyor. Kıvrım yerleştirmesi, aynı birim sayılarında hatayı belirgin biçimde düşürüyor. Yani bu deneyde darboğaz kapasite değil, başlatmadır; bu sonucu Bölüm 63.5'in iki başlatmasının karşılaştırması doğruluyor.

**Bunu AI'sız yazabilir misin?** Aynı hedefte birim sayısını `8`den `16`ya çıkardığını varsay ve hatanın yaklaşık ne olacağını tahmin et. Tahminini bir gerekçeyle yaz: kıvrım sayısı iki katına çıkınca parçalı doğrusal eğrinin hatasının kabaca hangi oranda düşmesini beklersin? Sonra bu tahmini ölçmek için hangi deneyi yazardın?

## Kendin Yap Projeleri

::: dikkat
Bu iki projede önce kendi çözümünü yaz. Yapay zekâ aracını yalnızca bitirdikten sonra kodu okumak ya da bir hatayı bulmak için kullan. Bu bölümü geçmek için değil, bu bölümü öğrenmek için yapıyorsun.
:::

### Proje 1 (★★): Mini bir derin öğrenme çatısı

**Amaç.** Bu bölümdeki `sinir.py` dosyasını, daha genel bir çatıya dönüştür. Katman (`Katman`), model (`Model`), optimizer (`SGD`, `Momentum`) ve kayıp (`Kayip`) arayüzlerini ayır. Kendi çatınla `load_digits` üzerinde test kümesinde ortalama `%97` ve üzeri doğruluğa ulaş.

**Yapılacak ve beklenen davranış.** Çatının şu özellikleri olmalı: (a) her katman kendi ileri ve geri yöntemlerine sahip olmalı, (b) bir model katmanları sırayla çağırabilmeli, (c) optimizer parametre listesini ve gradyanları alıp güncelleme yapabilmeli, (d) model kaydedilip yeniden yüklenebilmeli (ağırlıklar `.npz` olarak), (e) gradient check testleri her katman için geçmeli. Eğitim, yalnızca doğrulama kaybına göre seçilmiş hiperparametrelerle yapılmalı; test kümesi bir kez kullanılmalı.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Bölüm 63.6'daki arayüzü temel al. Momentum için her parametre başına bir hız (`v`) vektörü tut: `v ← μv − η g`, `θ ← θ + v`. Test ve doğrulama ayrımını `veri_yukle` içinde zaten yaptığın için bunu kolayca koruyabilirsin. Gradient check testlerini `t03_gradcheck.py`nin yapısıyla birleştir.

**Başarı kriterleri.** (1) Her katman için gradient check en büyük göreli hata `10⁻⁷`nin altında. (2) Momentumlu SGD ile eğitilmiş 64-128-64-10 ağı, beş tohumun ortalamasıyla test doğruluğu `%97` ya da üzeri. (3) Kaydet ve yükle işleminden sonra tahminler birebir aynı. (4) Her sonucun yanında hangi tohum ve hangi hiperparametre ile üretildiği yazılı.

### Proje 2 (★★★): Batarya arıza sınıflandırıcısı, tamsayı çıkarımı ve C çekirdeği

**Amaç.** Bir elektrikli araç batarya hücresinin sensör verisinden (gerilim, akım, sıcaklık) üç durumu sınıflandır: normal, aşırı ısınma eğilimi, iç direnç artışı. Veri sentetik olacak. Ağı NumPy ile eğit, int8'e kuantize et ve ARM Cortex-M4 üzerinde çalışacak bir C çıkarım çekirdeği yaz.

**Beklenen davranış.** Sentetik bir veri üreticisi, her sınıf için belirli bir dağılım ve ayrım sınırı tanımlamalı. Ağ, test kümesinde makul bir doğruluk vermeli ve baseline (lojistik regresyon) ile karşılaştırılmalı. Kuantizasyon sonrası doğruluk kaybı ölçülmeli. C çekirdeği ana bilgisayarda Python çıktısıyla bit düzeyinde eşleşmeli ve ARM'da derlenip boyutu ölçülmeli.

**Önerilen yaklaşım (ipucu).** Veri üretimi için her sınıfın özellikleri arasındaki korelasyonu bilinçli olarak ayarla; sadece gürültü eklemek yetmez. Eğitim ve kuantizasyon adımlarını Bölüm 63.15'teki hatla aynı tut. C tarafında, Bölüm 46.9'daki tamsayı çekirdek yapısını ve kalibrasyon ölçeklerinin nasıl aktarılacağını kullan. Taşma için her toplama noktasında aralığı kontrol et.

**Başarı kriterleri.** (1) Sentetik veride eğitim, doğrulama ve test bölmeleri ayrı; test kümesi bir kez kullanılıyor. (2) Ağ ile baseline arasındaki fark, beş tohumla ortalama ± sapma olarak raporlanıyor. (3) int8 çıkarımın tahmin uyumu ve doğruluk kaybı ölçülmüş. (4) C çekirdeğinin ana bilgisayar çıktısıyla en fazla bir yuvarlama birimi farkı var. (5) Cortex-M4 derlemesinin kod ve bellek boyutu raporlanmış.

## Ek Alıştırmalar

Aşağıdaki problemler kademelidir. ★ olanlar kavramı yoklar, ★★ olanlar bir türetme ya da küçük bir hesap ister, ★★★ olanlar birden çok konuyu birleştirir. Mülakat etiketli olanlar klasik sorulardır.

1. ★ Algılayıcı öğrenme kuralında `η` öğrenme oranının değeri, sonlu adımda yakınsamayı değiştirir mi? İki farklı `η` ile aynı veriyi çözüp hata sayısının her epoch'ta nasıl değiştiğine bak. (Mülakat)
2. ★ `ReLU(z) = max(0, z)` için `∂ReLU/∂z` türevini yaz. `z = 0` noktasında türev tanımlı mı? Pratikte neden bu noktayı önemsemeyiz?
3. ★ Üç doğrusal katmanın bileşiminin tek bir doğrusal katmanla aynı olduğunu matris çarpımının birleşmeli özelliğinden gösteren kısa bir argüman yaz.
4. ★★ `σ(z) = 1/(1 + e^(−z))` için `σ′(z) = σ(z)(1 − σ(z))` eşitliğini türet. `σ′`nin maksimumunun `0,25` olduğunu göster. (Mülakat)
5. ★★ Çok katmanlı bir ağda `L` kaybının `W₁`e göre gradyanının `Σ_{j}` terimlerinin bir toplamı olduğunu, her yolun bir çıkış nöronundan bir gizli nörona giden ağırlıkların çarpımı olduğunu açıkla. Bu, geri yayılımın neden tek bir geri geçişle hesaplanabildiğini nasıl gösterir?
6. ★★ Sabit başlatma `W = c` (her eleman aynı) için, tek gizli katmanlı bir ağın birimleri arasındaki simetriyi bir gradyan adımından sonra da koruduğunu göster. (Mülakat)
7. ★★ Gizli katmanda `n_in` girdi olan bir Dogrusal katmanda `Var(z) = n_in · Var(w) · Var(x)` olduğunu varsay. He başlatmanın `Var(w) = 2/n_in` ile ReLU'da varyansı koruduğunu, ReLU'nun ikinci momentinin yarıya indiğini de kullanarak göster.
8. ★★ Bir softmax-çapraz entropi çıkışında, eğer tüm logitlere aynı sabit `c` eklersen kayıp ve gradyanın değişmediğini göster. Bu, log-softmax'ın kararlılık hilesini nasıl açıklar? (Mülakat)
9. ★★ Gradient check'te merkezi fark `O(ε²)` hata ve `O(u/ε)` yuvarlama hatası verir (`u` makine epsilonu). Bu iki hatayı dengeleyen `ε`yi bul ve float32 için bu değerin neden çok daha büyük olacağını açıkla.
10. ★★★ Bir MLP'de ağırlıkları `dW = Hᵀδ` yerine `dW = δᵀH` yazarsan ne olur? Şekil tutarlılığı bu hatayı nasıl yakalar, ve bu hata yakalanamazsa ne tür bir sessiz yanlışlık oluşur? (Mülakat)
11. ★★★ Mini-batch boyutu `B` arttıkça, aynı sayıda epoch için gradyan gürültüsü ve adım sayısı nasıl değişir? Bu iki değişikliğin öğrenme oranı seçimine etkisini tartış. (Mülakat)
12. ★★★ Sigmoid aktivasyonlu `n` katmanlı bir ağda gradyan `0,25ⁿ` ile sönümlenir. Aynı ağı ReLU ile yaparsan gradyan hangi koşullarda yine sönümlenir? Ölü ReLU birimlerinin buna katkısını açıkla. (Mülakat)

## Bölüm Özeti

- Algılayıcı, `wᵀx + b`'yi bir eşikle karşılaştıran doğrusal bir sınıflandırıcıdır. Öğrenme kuralı hata yönünde küçük adımlar atar; veri doğrusal ayrılabilirse sonlu adımda yakınsar. XOR gibi doğrusal ayrılamaz veri onu çözemez.
- Katman, bir afin dönüşüm ve doğrusal olmayan bir aktivasyondur. Aktivasyon olmadan çok katmanlı ağ, tek bir doğrusal katmana indirgenir; sayısal olarak doğrulanabilir.
- Sigmoid, tanh, ReLU, Leaky ReLU ve GELU'nun değerleri ve türevleri farklıdır. Sigmoid'in türevi en fazla `0,25`tir ve derin ağlarda gradyan sönümlenir. ReLU'da ölü birim sorunu vardır ve yüksek öğrenme oranında bütün birimler ölebilir.
- Evrensel yaklaşım teoremi, yeterli genişlikte bir gizli katmanın yaklaşım kapasitesini garanti eder; ama öğrenilebilirliği garanti etmez. Başlatma, bu yaklaşımın gerçekleşip gerçekleşmediğini belirler.
- Çıkış softmax ve çapraz entropiyle birleştiğinde gradyan `(P − Y)/B`dir. Geri yayılım, `dW = Hᵀδ`, `db = Σδ` ve `δ_{l−1} = (δ_l Wₗᵀ) ⊙ φ′` özyinelemesidir. Her şeklin ilgili W ile uyumlu olması zorunludur.
- Gradient check, türetmeyi merkezi farkla sınar; göreli hata `10⁻⁷`nin altında olmalıdır. Bilinçli bir hata bu testte açıkça yakalanır.
- Başlatma simetriyi kırmalı ve aktivasyon varyansını korumalıdır. He başlatma ReLU için, Xavier ise simetrik aktivasyonlar için uygundur; sıfır ve sabit başlatmalar öğrenmeyi engeller.
- `load_digits` üzerinde 64-128-64-10 MLP, lojistik regresyon taban çizgisine çok yakın bir doğruluk (`0,975` ve `0,972`) verdi; fark tohum sapmasının içinde. Eğitim doğruluğu `1,000` ile aşırı uydurma belirgin. Erken durdurma ve L2 bu veri kümesinde belirgin fayda sağlamadı.
- Hesap maliyeti, parametre sayısı (`17.226`) ve FLOP sayısıyla ölçülür. Küçük batch'ler ek yükten etkilenir, büyük batch'ler BLAS'ın verimini kullanır. Sayısal sağlamlık için log-sum-exp, `NaN` denetimi ve öğrenme oranı taraması gerekir.
- int8 tamsayı çıkarımı, aynı doğruluğu (`0,975`) ve dört kat daha küçük bellek ile verir; bu bir ana bilgisayar simülasyonudur. PyTorch'un gradyanı, elle yazılmış geri yayılımla `10⁻¹⁵` mertebesinde uyuşur.

**Sonraki bölümde:** Bölüm 64, Eğitimin Sanatı, bu bölümde yalın SGD ile bıraktığımız yerden devam ediyor. Momentum, Adam ve AdamW gibi uyarlamalı optimizer'ları; öğrenme oranı takvimlerini; BatchNorm, LayerNorm ve dropout'u; eğitim hatalarını ayıklamanın yollarını göreceksin. Bu bölümde gördüğümüz aşırı uydurma ve ölü birim sorunları, orada çözümlerini bulacak.

::: mulakat
1. Algılayıcı neden XOR'u çözemez? Doğrusal ayrılabilirlik kavramını kendi cümlelerinle açıkla ve bunu bir gizli katmanın nasıl aştığını anlat.
2. Aktivasyon fonksiyonu olmadan bir derin ağ neden tek bir doğrusal katmanla aynıdır? Bu iddiayı bir matris çarpımı üzerinden gösterir misin?
3. Softmax ve çapraz entropi birlikte kullanıldığında çıkış gradyanı neden `p − y` olur? Bu sadeleşme eğitim verimliliği için neden önemlidir?
4. ReLU'nun ölü birim sorununu nasıl tanımlarsın? Öğrenme oranı bu sorunu nasıl etkiler ve nasıl teşhis edersin?
5. Sıfır başlatma ile sabit başlatmanın öğrenmeyi neden engellediğini, simetri kavramıyla açıkla. Rastgele küçük başlatma bu sorunu nasıl kırar?
6. Gradient check'in merkezi fark formülünde `ε`yi neden çok küçük ama çok küçük olmayan bir değer seçmelisin? Hatanın iki bileşenini yaz.
7. Bir MLP'nin eğitim doğruluğu `%100`, test doğruluğu `%97` ise bu ne anlama gelir? Aşırı uydurmayı azaltmak için hangi üç yöntemi denersin ve hangi sırayla?
8. Derin bir ağın eğitiminde kayıp `NaN` oldu. Bu durumda hangi üç olası nedeni kontrol edersin ve her birini nasıl ayırt edersin?
:::
