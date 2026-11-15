
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

@@KOD hesap_grafi.py:def ileri_geri

## 55.9 İleri mod ve ters mod: hangisi ne zaman daha ucuz?

Otomatik türevin iki yönü vardır. İleri mod, girdilerden başlayarak tek bir girdinin "teğet" değerini ilerletir. Ters mod, çıkıştan başlayarak tek bir çıktının gradyanını geriye taşır. İkisi de zincir kuralının aynısıdır; farkları, hangi yönde bir geçişin kaç çıktı ya da girdi için yeterli olduğudur.

İleri modu, ikili sayılar (dual numbers) ile kurmak en kolay yoldur. Bir `Dual(a, b)` sayısı, `a` değerini ve `b` türevini taşır. Her işlem, değerle birlikte türevi de günceller. Toplama `(a, b) + (c, d) = (a + c, b + d)` ile yapılır. Çarpma çarpım kuralıyla `(a, b) · (c, d) = (ac, ad + bc)` olur. Bu, tek bir girdi için türevi bir geçişte verir.

@@KOD ileri_mod.py:6-25

Üstel ve tanh gibi fonksiyonlar da aynı kalıpla yazılır. Aşağıdaki `exp` tanımı, değeri ve `eᵃ · b` türevini birlikte döndürür.

@@KOD ileri_mod.py:def exp

İleri modun Jacobian'ı, her girdi sütunu için bir geçişle hesaplanır. Yani `n` girdi için `n` ileri geçiş yapılır. Ters mod ise her çıktı satırı için bir geri geçiş yapar; `m` çıktı için `m` geri geçiş. Bir sinir ağında kayıp skaler (`m = 1`) olduğundan ters mod tek bir geri geçişle gradyanı verir. Parametre sayısı `n` milyonlarsa ileri mod bu yüzden pratik değildir. Şekil 55.5 bu maliyet farkını gösteriyor: ileri modun geçiş sayısı `n` ile büyürken ters modun geçiş sayısı yalnızca `m` ile büyür.

![Şekil 55.5: İleri mod ve ters modun geçiş sayısı; girdi sayısına göre](gorseller/b55_ileri_ters_maliyet.png)

Bu iki yöntemi aynı fonksiyon üzerinde karşılaştıralım. `f : ℝ³ → ℝ²` olan `f(x) = (x₁x₂ + eˣ³, x₂² x₃)` için Jacobian'ı üç yolla hesaplayan `jakobiyen.py` dosyasının ilgili parçası, ters mod için şöyledir. Çıktı başına bir geri geçiş yapılır ve her geri geçişten önce önceki geçişin gradyanları silinir.

@@KOD jakobiyen.py:def jakobiyen_ters

Dikkat et: bir geri geçişten önce yalnızca o çıktının alt grafının düğümleri değil, yaprakların da gradyanı silinir. Çünkü `x₁` yaprağı ilk çıktıya bağlıdır, ikinciye bağlı değildir; silinmezse ilk geçişten kalan gradyanı ikinci satırda da okuruz. Bu küçük ayrıntı, Jacobian'ın ikinci satırında ilk denemede ortaya çıkan yanlış değerin kaynağıydı.

@@CIKTI python jakobiyen.py out_jakobiyen.txt

Çıktıda üç yöntem de aynı Jacobian'ı verir ve farkları `10⁻¹⁰` mertebesindedir. İleri mod üç geçiş (n = 3), ters mod bir ileri ve iki geri geçiş (m = 2) yaptı. Bu sayılar küçük bir örnekte farkı göstermeye yeter; asıl fark, girdi sayısı milyonlara çıktığında belirir.

## 55.10 Kendi autodiff motorun: Deger

Şimdi motoru yazıyoruz. Tasarım, Andrej Karpathy'nin micrograd projesinden ilham alır ve kitaptaki sürüm kendi kodumuzdur. Temel birim `Deger` sınıfıdır. Her `Deger` dört şey tutar: sayısal değeri (`veri`), gradyanı (`grad`), kendisini üreten işlemin geri yayılım adımını (`_geri`) ve girdilerini (`_ebeveynler`). İşlemlerin her biri yeni bir `Deger` döndürür ve bu yeni düğüm, girdilerine bağlanmış olur. Böylece bir ifadeyi kullandıkça hesap grafiği kendiliğinden kurulur.

Gradyan birikiminin neden gerektiğini Şekil 55.6 gösteriyor. Bir düğümün gradyanı, onu kullanan her yoldan gelen katkıların toplamıdır. Şekildeki `a` düğümü iki yoldan katkı alır: `m = a · b` üzerinden 3 ve doğrudan `f = m + a` üzerinden 1. Toplam 4'tür.

![Şekil 55.6: Gradyan birikimi: paylaşılan a düğümü iki yoldan katkı alır](gorseller/b55_gradyan_birikimi.png)

Önce modülün başlangıcı: gradyan birikimini yöneten `_ekle` yardımcı fonksiyonu ve topolojik sıralama. `BIRIKIR` bayrağı deneyler için vardır; bu bayrak `True` iken gradyanlar toplanır, `False` iken üzerine yazılır. Doğru davranış `True`dur. `False` yapmak, Çözümlü Örnek 4'te göstereceğimiz hatanın bilerek yeniden üretilmesini sağlar.

@@KOD deger.py:1-34

Sınıfın kurucusu ve iki temel işlem, toplama ve çarpma, aşağıdadır. Dikkat et: her işlemin geri adımı, yerel türevi çıkışın gradyanıyla çarpıp girdilere `_ekle` ile ekler. Toplamanın yerel türevi 1, çarpmanın yerel türevi karşı girdidir.

@@KOD deger.py:37-70

Üs, üstel, logaritma ve tanh işlemleri de aynı kalıbı izler. Her biri değerini hesaplar, yerel türevini bilir ve geri adımını tanımlar. Üs alma için kural `n · xⁿ⁻¹`dir; üstel için türev kendisidir; logaritma için `1/x`tir.

@@KOD deger.py:72-97

ReLU ve tanh için geri adımlar aşağıdadır. Ardından `geri` metodu gelir: topolojik sırayı kurar, çıkış gradyanını 1 yapar ve düğümleri ters sırada çalıştırır. Son olarak eksi, çıkarma ve bölme gibi işlemler, bunları üç temel işleme indirgeyerek tanımlanır. Bu indirgeme önemlidir: yeni bir yerel türev yazmak yerine yalnızca toplama, çarpma, üs, üstel, logaritma ve tanh bilmek yeter.

@@KOD deger.py:99-121

@@KOD deger.py:123-142

`geri` metodunda dikkat etmen gereken iki satır vardır. Birincisi `self.grad = 1.0`: çıkışın kendisine göre türevi 1'dir. İkincisi döngünün ters sırada çalışmasıdır: bir düğümün gradyanı tam olarak hesaplanmadan kendi geri adımı çalışmamalıdır. Topolojik sırada ters gidince bu garanti edilir.

Motoru denetlemek için her işlemin türevini, Bölüm 50.3'teki merkezi farkla karşılaştıran `grad_kontrol.py` dosyası yazdık. Önce her işlemi tek tek, sonra 300 rastgele ifadeyi sınarız. Rastgele ifadeler, sabit tohumlu bir program üreticisiyle oluşturulur: her adım iki önceki değeri bir işlemle birleştirir.

@@KOD grad_kontrol.py:def calistir

@@CIKTI python grad_kontrol.py out_grad_kontrol.txt

Çıktının ilk bölümünde her işlemin `x₀` girdisine göre türevi, otomatik ve sayısal olarak yazılmıştır. Hata sütunu göreli farkı verir ve hepsi `10⁻¹⁰` mertebesindedir. İkinci bölümde 300 rastgele ifadenin en büyük göreli hatası `2,22·10⁻¹⁰`dur ve `10⁻⁶` eşiğini aşan yoktur. Bu sonuç motorun ve türev kurallarının tutarlı olduğunu gösterir; hatanın küçük olması, sayısal türevin de yuvarlama hatası taşıdığını unutmamamız gerektiğini hatırlatır.

Bu motor, yorumlarla birlikte yaklaşık 140 satırdır ve gerçek bir sinir ağını eğitmeye yeter. Ama bir kısıtı var: her skaler işlem bir Python nesnesi üretir. Bu, yavaştır ve büyük veride kullanılamaz. Bu konuyu 55.12'de ölçeceğiz.

## 55.11 Motoru MLP ile eğitmek

Şimdi motorla gerçek bir öğrenme problemi çözeceğiz. Veri, iç içe iki yarım aydan oluşan sentetik bir sınıflandırma kümesidir. Bu küme doğrusal olarak ayrılamaz; yani tek bir doğrusal sınır yetmez. Bu nedenle en az bir gizli katman gerekir. Veri, sabit tohumlu bir üreteçle oluşturulur ve 80 nokta içerir.

Ağ mimarisi `[2, 8, 8, 1]`dir: iki girdi, iki gizli katman (her biri 8 birim, tanh etkinleştirmeli) ve tek çıkış (doğrusal). Toplam 105 parametre vardır. Kayıp ortalama kare hatadır ve etiketler `+1` ya da `−1`dir. Önce bir nöron, sonra katman ve ağ sınıflarını yazıyoruz; her biri `Deger` üzerinde çalışır.

@@KOD mlp_skaler.py:7-15

@@KOD mlp_skaler.py:18-26

@@KOD mlp_skaler.py:29-47

Ağın kaybı ortalama kare hatadır. Her örnek için çıkışla etiket arasındaki farkın karesi alınır, ardından ortalaması hesaplanır. Bu kayıp da bir `Deger` olduğu için geri geçiş onu da kapsar.

@@KOD mlp_skaler.py:def kayip

Eğitim döngüsü dört adımdan oluşur. Önce kaybı hesaplarız. Sonra her parametrenin gradyanını sıfırlarız; bu adım kritiktir, çünkü gradyanlar her geri geçişte birikir ve bir önceki dönemin değerleri kalırsa yanlış bir yön izlenir. Üçüncü olarak geri geçişi çalıştırırız. Son olarak her parametreyi gradyanın tersine `η` kadar kaydırırız.

@@KOD mlp_skaler.py:def egit

Eğitimi 600 dönem, öğrenme oranı `0,1` ile çalıştırdık. Aşağıdaki çıktı kaybın dönemlere göre nasıl düştüğünü ve sonunda doğruluğun `%98,8` olduğunu gösteriyor. Kayıp ilk dönemde `0,9965`ten başlayıp `0,0691`e iner.

@@CIKTI python mlp_skaler.py out_mlp_skaler.txt

Şekil 55.7 kayıp eğrisini gösteriyor. Kayıp ilk yüz dönemde hızla yaklaşık `0,2`ye iner, sonra bir süre plato çizer ve 400. dönemden sonra yeniden belirgin biçimde düşer. Bu plato, tam bir kesinlik kanıtı değildir; ağın önce kaba bir ayrımı bulup sonra ince yapıyı öğrendiğini düşündüren bir gözlemdir. Ölçüm olarak kesin olan, eğrinin tek bir çalıştırmada monoton azaldığı ve son değerin `0,069071` olduğudur. Daha uzun eğitimle kaybın daha da düşmesi beklenir, ama bu bölümde bunu ölçmedik.

![Şekil 55.7: Kendi motorla eğitilen MLP'nin kayıp eğrisi](gorseller/b55_kayip_egrisi.png)

Şekil 55.8 eğitilmiş ağın karar sınırını gösteriyor. Ağın çıkışı sıfırı geçen eğri, iki yarım ayı birbirinden ayıran sınırdır. Bu sınır doğrusal değildir; ağın gizli katmanları bu eğriliği sağlar. İki yarım ay, tek bir doğru ile tam olarak ayrılamayacak biçimde iç içe geçmiştir. Bu yüzden doğrusal bir model bu veride bir tavan doğruluğa takılır; bu bölümde o modeli ayrıca eğitmedik, ama şekle bakınca neden yetersiz kalacağı açıktır.

![Şekil 55.8: Kendi motorla eğitilen MLP'nin karar sınırı ve eğitim verisi](gorseller/b55_karar_siniri.png)

Burada önemli bir gözlem var. Bu ağın tüm parametre gradyanları, bir kez çalıştırılan geri geçişle hesaplanır. Motor, kendi kurduğu hesap grafiği üzerinde bir zincir kuralı taraması yapar; başka bir sihir yoktur. Bu, Bölüm 63'te NumPy ile yazacağımız tam MLP'nin kavramsal olarak aynısıdır.

## 55.12 Vektörleştirilmiş geri yayılım

Skaler motor doğru ama yavaştır. Her skaler işlem bir Python nesnesi yaratır ve her geri adım bir fonksiyon çağrısıdır. Aynı hesabı bir matris çarpımıyla yaparsak, işi NumPy'ın C kodu yapar ve her katman tek bir büyük işlemle çalışır. Bu bölüm, aynı ağı bu kez elle türetilmiş matris gradyanlarıyla yazar ve iki sürümü karşılaştırır.

Matris biçiminde ağın ileri geçişi, her katmanda girdi matrisini ağırlıkla çarpıp sapmayı ekler ve etkinleştirme uygular. Geri geçişin formülleri, 55.5'te türettiğimiz kurallardan gelir. Her katmanda `d = dL/dz` (önceki katmanın doğrusal çıktısının kayıp gradyanı) tutulur. Ağırlık gradyanı `dW = girdiᵀ d`, sapma gradyanı `db = ∑ d` olur. Bir önceki katmana aktarılan gradyan `d Wᵀ`dır ve tanh'ın türevi `1 − a²` ile çarpılır.

@@KOD vektor.py:def kayip_ve_gradyan

Kod, Bölüm 55.5'teki şekil düşüncesini doğrudan kullanır: `dW` her zaman `W` ile aynı şekildedir, çünkü `girdiᵀ` (girdi × örnek) ile `d` (örnek × çıktı) çarpımı girdi × çıktı verir. Bu kontrol, bir matris çarpım sırasının yanlış olduğunu hemen gösterir.

Vektörel sürümün doğruluğunu, skaler motorla aynı başlangıç ağırlıklarında karşılaştırarak sınadık. İlk kayıp ve ilk gradyanlar, `10⁻¹⁶` mertebesinde bir farkla aynıdır. Sonra iki sürümü 600 dönem boyunca eğittik; sonunda ağırlıklar yine `10⁻¹⁵` mertebesinde aynıdır. Bu, iki yöntemin aynı matematiği yaptığının sayısal kanıtıdır.

@@CIKTI python vektor.py out_vektor.txt

Çıktıdaki hız satırları en önemli ölçümdür. Skaler motorun bir dönemi yaklaşık `0,14` saniye sürdü; vektörel sürümün bir dönemi `0,00006` saniye. Oran bu çalıştırmada yaklaşık 2200 kattır. Bu sayı makineye, Python sürümüne ve o anki sistem yüküne bağlıdır; senin makinende farklı çıkacaktır. Önemli olan, fark büyüklüğünün basamak düzeyinde ve yönünün aynı olmasıdır.

Şekil 55.9 aynı sonucu grafikte gösteriyor. Log ölçekte iki çubuk arasındaki mesafe, skaler motorun neden büyük ağlarda kullanılamadığını açıkça gösterir.

![Şekil 55.9: Aynı MLP'nin skaler ve vektörel dönem süreleri (log ölçek)](gorseller/b55_hiz.png)

Bu köprü, Bölüm 63'te sıfırdan yazacağın tam MLP'nin iskeletidir. Bölüm 56'da NumPy'ın vektörleştirme ve yayınlama (broadcasting) kurallarını derinlemesine göreceksin; bu bölümdeki `W.T`, `sum(axis=0)` ve eleman bazlı çarpımların her biri o kuralların uygulamasıdır.

## 55.13 Sayısal tuzaklar: kaybolan gradyan, taşma ve log(0)

Türevi doğru formüllerle hesaplamak yetmez; sayılar bilgisayarda sınırlı kesinlikle temsil edilir. Bu bölümde üç tuzak görüyoruz. Birincisi, uzun bir zincirde çarpımın sıfıra gitmesi. İkincisi, üstel fonksiyonun taşması. Üçüncüsü, logaritmanın sıfırda tanımsız olması.

Kaybolan gradyan, zincir kuralının doğal sonucudur. Her katman, gradyanı bir çarpanla çarpar. Sigmoid için bu çarpan `σ′ ≤ 0,25` olduğundan, `n` katmandan sonra gradyan en fazla `0,25ⁿ` ile sınırlıdır. Aşağıdaki fonksiyon `h₀ = x` ve `hₖ = σ(hₖ₋₁)` zincirini kurar ve ters modla `dhₙ/dx`i hesaplar.

@@KOD kaybolan.py:7-19

Aşağıdaki çıktı, `x = 0,5` için bazı derinlikleri gösteriyor. Tam çıktı 30 derinliğin hepsini CSV'ye yazar; Şekil 55.10 o veriyi çizer. Gradyan, on katmanda `10⁻⁷`, otuz katmanda `10⁻²⁰` mertebesine iner. Otomatik ve elle çarpılmış değerler aynıdır; yani motor doğru çalışıyor, sorun formülün kendisindedir.

@@CIKTI python kaybolan.py out_kaybolan.txt

![Şekil 55.10: Sigmoid zincirinde kaybolan gradyan; üst sınır 0,25ⁿ ile birlikte](gorseller/b55_kaybolan_gradyan.png)

Bu sonuç, derin sigmoid ağlarının neden eğitilemediğinin en sade açıklamasıdır. Pratikte bu sorunu hafifletmek için ReLU gibi türevi çarpan olarak büyük kalan etkinleştirmeler, dikkatli başlatma ve normalizasyon kullanılır; bunları Bölüm 64'te eğitim sanatı kapsamında göreceksin. Kalıntı (residual) bağlantılar ise Bölüm 66'da ResNet ile anlatılacak. Burada önemli olan, sorunun türevin kendisinde değil, zincirin uzunluğunda ve çarpanların boyutunda olduğunu görmektir.

Taşma ve log(0) tuzakları ise softmax ve çapraz entropide ortaya çıkar. Aşağıdaki fonksiyonlar naif softmax ve log-sum-exp hilesini içerir. Log-sum-exp, en büyük logiti çıkarır: `softmax(z) = softmax(z − m)` eşitliği her zaman doğrudur, çünkü `m` her bileşenden aynı miktarda çıkarılır ve pay ile paydada sadeleşir. Bölüm 51.10'da bunu bilgi teorisi bağlamında görmüştük.

@@KOD sayisal_tuzak.py:7-14

@@CIKTI python sayisal_tuzak.py out_sayisal_tuzak.txt

Çıktı üç tuzağı gösteriyor. `math.log(0.0)` bir `ValueError` fırlatır, `np.log(0.0)` ise sessizce `-inf` döndürür; ikisi de sorunludur. Naif softmax `[1000, 999, 998]` için `nan` üretir, çünkü `e¹⁰⁰⁰` taşar. Kararlı biçim ise doğru olasılıkları `[0,665241; 0,244728; 0,090031]` verir. Son satırda naif çapraz entropi `inf` üretir, oysa log-sum-exp ile hesaplanan kayıp `800` olur. Bu fark, bir eğitim döngüsünde kaybın bir anda `inf`'e çıkmasının nedenidir.

Bu tuzaklardan kaçmanın ilk kuralı şudur: softmax ve logaritmayı asla birbirinden ayrı yazma. Kayıp fonksiyonunu log-sum-exp biçiminde yaz ve gradyanı `p − y` olarak türet. Bu iki kural, `nan` ve `inf` hatalarının büyük kısmını önler.

## 55.14 Gerçek autodiff sistemleri, kontrol akışı ve ikinci dereceden türev

Bu bölümde yazdığımız motor, gerçek sistemlerin özünü taşır ama onlar çok daha büyük ve hızlıdır. Bu alt bölümde o sistemlerin farklarını kavramsal olarak özetliyoruz. Bu kısımdaki bilgilerin çoğu genel bilgidir ve kitabın kendi ölçümü değildir; resmi belgeleri okuyarak doğrulamanı öneririm.

PyTorch'un autograd sistemi, dinamik bir hesap grafiği kurar: program her çalıştığında grafı yeniden inşa eder. Bu yaklaşıma tanımla-çalıştır (define-by-run) denir ve bizim motorumuzun da yaptığı budur. Bölüm 65'te PyTorch'un tensör düzeyinde nasıl çalıştığını ayrıntılı göreceksin. JAX ise farklı bir yol izler: bir fonksiyonu iz (trace) olarak kaydedip o iz üzerinde dönüşümler (türev, derleme) uygular. İki yaklaşım da zincir kuralını aynı şekilde uygular; fark, grafın ne zaman ve nasıl kurulduğudur.

Kontrol akışı, yani `if` ve döngüler, dinamik grafiklerin doğal avantajıdır. Motorumuz da bir `if` içinden geçen yolu kaydeder ve yalnızca çalıştırılan dalın türevini verir. Bu, sembolik türevin zor yapabildiği bir şeydir. Ancak bir uyarı gerekir: türev, çalıştırılan belirli bir yol için geçerlidir ve `if` koşulu bir süreklilik noktasındaysa türev tanımsız olabilir. ReLU'nun `x = 0`daki durumu bunun küçük bir örneğidir.

Son olarak ikinci dereceden türev. Gradyanın bir daha türevi, Hessian matrisini verir; Bölüm 50.11'de Newton yönteminde bu matrisin rolünü görmüştük. Büyük ağlarda Hessian'ın tamamını kurmak imkânsızdır, ama bir Hessian-vektör çarpımı `Hv` çoğu zaman yeterlidir. Bu çarpım, ileri modun bir geri geçişin üzerine kurulmasıyla (genel bilgi olarak: ileri-üzerine-ters) tek bir geçişe yakın maliyetle hesaplanabilir. Hessian ve ikinci dereceden bilgi, Bölüm 50'deki Newton yöntemi ve eğrilik analizinin devamı olarak ileride yeniden karşına çıkacak.

Bu bölümün sonunda elindeki motor, bu büyük sistemlerin mantığını taşıyor: bir hesap grafiği, bir topolojik sıralama, her düğüm için yerel bir türev ve gradyanların doğru birikmesi. Gerisi mühendislik ölçeğidir.
