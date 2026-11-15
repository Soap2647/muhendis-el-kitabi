%% kisim_no: XIV
%% kisim_ad: Makine Öğrenmesi
%% bolum_no: 58
%% baslik: Doğrusal Modeller

## Giriş: Derin ağların çağında hâlâ en önemli araçlardan biri

Her ML projesinin ilk modeli neredeyse her zaman doğrusaldır. Bunun sebebi modelin ilkel olması değil, doğrusal bir modelin üç şeyi aynı anda vermesidir: bir sonucun nasıl üretildiğini açıklayabilmek, eğitimini ve tahminini milisaniyeler içinde yapabilmek, ve bir karmaşık modelin gerçekten bir şey öğrenip öğrenmediğini ölçmek için sağlam bir referans olmak. Bölüm 54'te baseline kavramını gördük; bu bölümdeki doğrusal modeller o baseline'ların en güçlü ve en dürüst olanıdır.

Savunma sanayiinde bu konu doğrudan karşına çıkar. Bir hedef sınıflandırıcısının bir tespiti neden yaptığını ya da bir arıza kestiriminin neden "bakım yap" önerdiğini bir mühendise, bir denetçiye ya da bir sertifikasyon kuruluşuna açıklaman gerekebilir. Katsayıları okunabilen bir model bu soruya doğrudan cevap verir. Derin bir ağda aynı soruya cevap vermek Bölüm 78'de ele alınacak ayrı bir araştırma konusudur.

Bu bölümde doğrusal regresyondan başlayıp lojistik regresyona, softmax'a ve Poisson gibi genelleştirilmiş doğrusal modellere (GLM) kadar uzanan ailenin tamamını sıfırdan kuracağız. Her modeli önce NumPy ile yazacak, sonra scikit-learn ile karşılaştıracağız. Düzenlileştirmeyi (Ridge, Lasso, Elastic Net) koordinat inişi ile kendi elimizle çözeceğiz. Bölümün sonunda modeli bir mikrodenetleyiciye aktarmanın yolunu da göreceksin.

::: not
Bu bölümdeki başarı iddialarının çoğu ayrı bir test kümesinde ve bir baseline ile karşılaştırılarak ölçülmüştür; eğitim skorları test skorundan ayrı etiketlenmiştir. Tekrarlanabilirlik için tüm tohumlar sabittir; bölüm metnindeki her sayı, yazılan programın gerçek çıktısıdır.
:::

## 58.1 Neden doğrusal modeller hâlâ önemli

Doğrusal model, tahmini girdilerin ağırlıklı toplamı olarak yazar: `ŷ = wᵀx + b`. Bu kadar basit bir yapının neden hâlâ yaygın olduğunu dört soru üzerinden düşünebiliriz.

**Yorumlanabilirlik.** Her `wⱼ` katsayısı, öznitelik `xⱼ` bir birim arttığında (diğer öznitelikler sabitken) tahminin ne kadar değiştiğini söyler. Bu cümleyi bir mühendis ya da bir denetçi doğrudan anlar. Ağaç ve sinir ağı modellerinde aynı cümleyi kurmak için ek araçlar gerekir (Bölüm 59 ve 78).

**Hız ve boyut.** Eğitilmiş bir doğrusal modelin tahmini bir nokta çarpımdır: `d` çarpma ve toplama. Bellekte yalnızca `d + 1` sayı tutulur. Bu özellik, bölüm 58.14'te göreceğin gibi, bir mikrodenetleyicide çalışmayı mümkün kılar.

**Baseline.** Bölüm 54'te gördüğümüz gibi, bir modelin değeri yalnızca bir baseline'a göre anlamlıdır. Doğrusal model, karmaşık bir modelin ne kadar kazandırdığını ölçmek için en ucuz referanstır. Karmaşık model doğrusal modelden anlamlı biçimde iyi değilse, karmaşıklığın bedeli kazancı aşıyor demektir.

**Sınırları.** Doğrusal model, öznitelikler arasındaki doğrusal olmayan ilişkileri kendiliğinden öğrenemez. Bu sınırı iki yolla aşarız: öznitelikleri dönüştürmek (58.6'da temel fonksiyonlar) ya da modelin kendisini esnetmek (Bölüm 59, 60 ve 63). Bölüm 58.15'te, bu sınırın XOR gibi basit bir örnekte nasıl göründüğünü göstereceğiz.

Bir incelik var: "doğrusal" sözcüğü parametreler için geçerlidir, girdiler için değil. `ŷ = w₁x + w₂x²` modeli, `x²` yeni bir öznitelik olarak düşünüldüğünde yine doğrusaldır. Bu fikir bölümün ikinci yarısının temelidir.

## 58.2 Doğrusal regresyon: model, kayıp ve kapalı form

Girdi öznitelikleri `x ∈ ℝᵈ`, hedef `y ∈ ℝ` olsun. Eğitim kümesinde `n` örnek varsa, tasarım matrisini `A` ile gösterelim. İlk sütunu sapma (intercept) için hep 1 olan `A ∈ ℝⁿˣ⁽ᵈ⁺¹⁾` matrisinde i'inci satır `[1, xᵢᵀ]`'dir. Model `ŷ = A w` olur; burada `w = [b, w₁, …, w_d]ᵀ`.

Kayıp fonksiyonu, Bölüm 50'de tanıştığımız kare kayıptır (ortalama kare hata, MSE):

L(w) = (1/n) Σ (yᵢ − ŷᵢ)² = (1/n) ‖y − A w‖²

Kaybı minimize eden `w`'yi bulmak için gradyanı sıfıra eşitleriz. `∇L = (2/n) Aᵀ(A w − y)` olduğundan, koşul `AᵀA w = Aᵀy` olur. Bu denkleme **normal denklem** denir. Eğer `AᵀA` tersinir ise çözüm:

w* = (AᵀA)⁻¹ Aᵀ y

Bu formülü yazmak kolaydır, ama pratikte `(AᵀA)⁻¹`'i hesaplamayız. Bölüm 48.10'da gördüğümüz gibi, bir matrisin tersini almak yerine denklemi çözmek hem daha hızlı hem daha kararlıdır. Bunun için üç kapalı form yolu vardır.

**Normal denklem.** `AᵀA w = Aᵀy` denklemini doğrudan bir doğrusal sistem çözücüsüyle (LU, Cholesky) çözersin. En hızlı yoldur, ama `AᵀA`'nın koşul sayısı `A`'nın koşul sayısının karesidir: `cond(AᵀA) = cond(A)²`. Bu, Bölüm 48.10 ve 48.11'de anlatılan sayısal kayıp demektir.

**QR ayrışımı.** `A = QR` yazarsın; burada `Q`'nun sütunları dikgen, `R` üst üçgendir. `‖y − A w‖ = ‖Qᵀy − R w‖` olduğundan (Q dikgen olduğu için), çözüm `R w = Qᵀy` denklemini geriye yerine koyma ile bulunur. `AᵀA` hiç oluşturulmaz; koşul sayısı `cond(A)` ile orantılıdır.

**Tekil değer ayrışımı (SVD).** `A = U Σ Vᵀ` yazarsın ve `w = V Σ⁺ Uᵀ y` alırsın; burada `Σ⁺` her sıfır olmayan tekil değerin tersini alır. En kararlı yöntemdir ve tekil değerler küçükse kesme (truncation) yapmana izin verir (Bölüm 48.13). Scikit-learn'ün `LinearRegression` nesnesi, SVD tabanlı `scipy.linalg.lstsq` çözücüsünü kullanır.

Bu üç yöntemin uyumunu, kendi yazdığımız bir programla gösterelim. Veri olarak scikit-learn'ün diyabet veri setini kullanacağız: 442 örnek, 10 öznitelik, sürekli bir hedef. Veri setinin özniteliklerini sklearn önceden merkezlemiş ve ölçeklemiştir; bu yüzden ham birim yorumuna bu bölümde girmiyoruz. Eğitim ve test bölmesi için 25 % test, sabit tohum 58 kullanıyoruz. Ölçekleyici yalnızca eğitim kümesinden öğrenilir (Bölüm 54.8'deki sızıntı kuralı).

Önce bu bölümün ortak kütüphanesini (`b58_core.py`) okuyalım. Bu dosyadaki fonksiyonların her birini ilgili alt bölümde açıklayacağız; şimdilik yalnızca ne işe yaradıklarını bilmek yeterli.

@@KODTAM|b58_core.py@@

Aşağıdaki program üç kapalı form yolu ile scikit-learn'ü karşılaştırır. Ayrıca, Bölüm 48'deki polinom uydurma örneğinin matrisini (Vandermonde) kullanarak koşul sayısının karesel büyümesini ve normal denklemin kayıbını gösterir.

@@KODTAM|b58_01_ols.py@@

@@CIKTI|b58_01_ols.py@@

Sonuçlar üç şeyi söylüyor. Birincisi, üç yöntem de on iki basamağa yakın bir hassasiyetle aynı katsayıları verir: diyabet verisinde sorun yoktur, çünkü `cond(A) = 22,2` ve normal denklem bu kadar küçük bir koşul sayısında güvenlidir. İkincisi, `cond(AᵀA) = 492,9` değeri `22,2²` ≈ 492,8 ile uyumludur; bu, karesel ilişkinin ölçülmüş bir doğrulamasıdır. Üçüncüsü, Vandermonde matrisinde (dereceyi 8 seçtik, 50 nokta `[0, 1]` aralığında) koşul sayısı `6,3·10⁵`'ten `3,9·10¹¹`'e çıkar. Bu durumda normal denklem, bilinen tam çözümden `1,9·10⁻⁵` uzaklaşırken QR `6,6·10⁻¹¹` hata verir. Aradaki fark beş basamak civarındadır.

Test kümesinde doğrusal model RMSE 55,29 ve R² 0,411 verir. Baseline (eğitim ortalamasını tahmin etmek) RMSE 72,72 verir. Model baseline'ı belirgin biçimde geçer, ama R² değeri 0,41 olduğu için diyabet ilerlemesinin çoğu hâlâ açıklanamamıştır. Bu, doğrusal modelin sınırıdır ve sonraki alt bölümlerde gerçek bir iyileştirme için ne yapılabileceğine bakacağız.

## 58.3 Gradyan inişi ve SGD: öğrenme oranı ve ölçekleme

Normal denklemin kapalı çözümü küçük ve orta boyutlu problemlerde yeterlidir. Ama `n` ve `d` milyonlara çıktığında `AᵀA` matrisini oluşturmak ve çözmek pahalıdır. Bu durumda gradyan inişi (GD) devreye girer. Bölüm 50.5'te öğrendiğimiz adım kuralını doğrusal regresyona uygularız:

w ← w − η ∇L(w),  ∇L(w) = (2/n) Aᵀ(A w − y)

Her adımda bir tam gradyan hesaplanır. Kare kayıp için bu, kayıp yüzeyinin bir paraboloid olduğu anlamına gelir. Bu durumda yakınsama hızı `AᵀA`'nın özdeğerlerine bağlıdır. Sabit öğrenme oranı için kararlılık koşulu `η < 2/L`'dir; burada `L = λ_maks((2/n) AᵀA)` kayıp fonksiyonunun Lipschitz sabitidir. Bu seçimle, en küçük özdeğere karşılık gelen yön yavaş yakınsar. Oran `λ_maks / λ_min` olan koşul sayısını artırır.

Stokastik gradyan inişi (SGD), her adımda tüm veri yerine bir mini-grup kullanır. Bu, adımı ucuzlatır ama gradyanı gürültülü yapar. Bölüm 50.6'da gördüğümüz gibi, gürültü belli bir tabana kadar kayıp minimizasyonunu bozmaz, ama öğrenme oranı azaltılmadan tam çözüme yakınsamaz.

Aşağıdaki program üç şeyi ölçer: tam GD'nin normal denkleme yakınsaması, mini-grup SGD'nin gürültülü davranışı ve öznitelik ölçeklemesinin yakınsama hızına etkisi. Ölçekleme etkisi için aynı problemi iki parametrelemede (ham ve standardize) çözüyoruz. İki problemin optimum kaybı aynıdır, çünkü standardizasyon yalnızca sütunların doğrusal dönüşümüdür ve sütun uzayını değiştirmez; yalnızca gradyan iniş yolunu değiştirir.

@@KODTAM|b58_02_gd.py@@

@@CIKTI|b58_02_gd.py@@

Tam GD, `η = 1/L = 0,124` ile 20 000 adım sonra normal denklem çözümünden `7,4·10⁻¹³` uzaklaşır; yakınsama tamamdır. SGD'nin (grup 16, `η = 0,01`, 50 epoch) durumu farklıdır: ağırlıklar kapalı çözümden `15,9` birim uzakta, kayıp ise `2847,25`'e karşı `2842,10`. Bu fark, sabit öğrenme oranlı SGD'nin gürültü tabanıdır. Gürültüyü azaltmanın yolu öğrenme oranını zamanla küçültmek ya da iterasyonları ortalamaktır (Bölüm 50.10).

Ölçekleme etkisi en öğretici kısımdır. Standardize edilmiş sistemde koşul sayısı `22,2`, `L = 8,06`; ham sistemde koşul sayısı `230,4`, `L = 2,00`. Ham sistemde `L` daha küçük olduğu için adım daha büyük seçilebilir, ama en küçük özdeğer çok küçüktür; bu yön yavaş yakınsar. Sonuç açıktır: standardize edilmiş sistemde kayıp farkı `10⁻²`'nin altına 1 567 adımda iner, ham sistemde 20 000 adımda inmez. Bu fark, Şekil 58.1'de log ölçekte görülür.

@@SEKIL|b58_olcekleme.png|Ölçeklemenin gradyan inişine etkisi: standardize edilmiş ve ham öznitelikler için kayıp farkı, adıma göre (log ölçek).@@

Pratik sonuç: gradyan inişiyle eğitim yapacaksan öznitelikleri önce ölçekle. Ölçekleyiciyi yalnızca eğitim kümesinden öğren ve test kümesine uygula (Bölüm 56'daki pipeline kuralı). Bu, sadece hızı değil, aynı zamanda sayısal kararlılığı da iyileştirir.

## 58.4 Olasılıksal yorum: Gauss gürültüsü altında MSE, MLE'dir

Kare kaybını neden seçtiğimizi şimdiye kadar sezgisel olarak açıkladık: büyük hatalar karesel olarak cezalandırılır. Ama bu seçimin ardında olasılıksal bir gerekçe vardır ve bu gerekçeyi Bölüm 49.8'deki en büyük olabilirlik (MLE) ilkesiyle birlikte türetebiliriz.

Varsayım: her gözlem için `yᵢ = aᵢᵀ w + εᵢ`, burada gürültüler bağımsız ve aynı dağılımlı `εᵢ ~ N(0, σ²)`. Bu, `yᵢ`'nin `N(aᵢᵀw, σ²)` dağılımından geldiği anlamına gelir. Tüm veri için olabilirlik çarpımdır:

p(y | w, σ²) = Π (2πσ²)^(−1/2) exp(−(yᵢ − aᵢᵀw)² / (2σ²))

Doğal logaritma alınca, log-olabilirlik şöyle olur:

ℓ(w, σ²) = −(n/2) ln(2πσ²) − (1/(2σ²)) Σ (yᵢ − aᵢᵀw)²

Bu ifadenin `w`'ye bağlı tek terimi `Σ (yᵢ − aᵢᵀw)² = SSE(w)`'dir. Log-olabilirliği en büyük yapmak, `SSE`'yi en küçük yapmakla aynıdır. Yani Gauss gürültüsü varsayımı altında, MSE ile kayıp minimizasyonu ile en büyük olabilirlik tahmini birebir aynı sonucu verir. Bu, Bölüm 49.8'deki en büyük olabilirlik ilkesinin doğrusal regresyondaki karşılığıdır.

`σ²` de bilinmiyorsa MLE'ye göre `σ̂² = SSE(ŵ)/n`'dir. Bu tahmin yanlıdır: serbestlik derecesini hesaba katan `SSE/(n − p)` daha yaygındır (burada `p = d + 1`). Aşağıdaki program bu eşitliği üç yoldan doğrular: kapalı form OLS, analitik gradyanlı BFGS ile log-olabilirliğin doğrudan minimizasyonu ve scikit-learn'ün sonucu. Analitik gradyanlar yukarıdaki türetmeden gelir: `∂(−ℓ)/∂w = −Aᵀ(y − Aw)/σ²` ve `∂(−ℓ)/∂(log σ) = n − SSE/σ²`. Gradyanın doğruluğu, OLS noktasında sıfıra yakın çıkmasıyla denetlenir (Gradyanın doğruluğunu burada yalnızca OLS noktasında sıfıra yakınlık ile denetliyoruz).

@@KODTAM|b58_03_mle.py@@

@@CIKTI|b58_03_mle.py@@

Olabilirlik maksimizasyonu OLS katsayılarını `1,6·10⁻⁶` mertebesinde bulur. BFGS, çıkış koşulunun kesinlik sınırına çarptığı için `success=False` bildirdi; bu, kesinlik sınırına yakın bir çözüm olduğunu, bir yöntem hatasını değil, söyler. Gradyanın OLS noktasında `3,6·10⁻¹⁵` çıkması analitik türetmenin doğruluğunu gösterir. `σ̂ = 53,31` ile `√(SSE/n)` tam olarak aynıdır; sapmasız tahmin `54,22`'dir.

Bu bölümde MSE'yi Gauss varsayımından türettik. Laplace gürültüsü (çift üstel dağılım) varsayımı altında ise MLE, mutlak hata (MAE, L1 kaybı) ile aynıdır. Bölüm 58.13'te bu farkın aykırı değerler karşısında ne anlama geldiğini deneyle göreceğiz.

## 58.5 Varsayımlar, artıklar ve katsayıların yorumu

Doğrusal regresyonun olabilirlik yorumu, modelin varsayımlarını açıkça ortaya koyar. Bunları dört madde halinde sıralayabiliriz: doğrusallık (ortalama ilişki doğrusaldır), bağımsızlık (gözlemler birbirinden bağımsızdır), sabit varyans (artıkların yayılımı tahminle değişmez) ve normallik (artıklar normal dağılımlıdır). Bu varsayımları gerçek veride artıklara bakarak sınarız. Artık, `rᵢ = yᵢ − ŷᵢ`'dir.

Artık grafikleri, Bölüm 57'de ayrıntılı olarak göreceğimiz tanılama araçlarının doğrusal regresyondaki karşılığıdır. İki temel grafik vardır: artıkların tahmine karşı çizimi (doğrusallık ve sabit varyans için) ve artıkların normal dağılımla karşılaştırılması (normallik için). Biz burada iki sayısal özet kullanıyoruz: Shapiro–Wilk normallik testinin p değeri ve artığın mutlak değeri ile tahmin arasındaki Spearman korelasyonu (değişen varyans için bir ölçü).

Aşağıdaki programda iki veri var: gerçek diyabet verisinin artıkları ve sabit tohumla üretilmiş, varyansı `x` ile büyüyen bir sentetik veri (`y = 3 + 2x + N(0, (0,3x)²)`). Sentetik veri, değişen varyansın ne göründüğünü bilerek göstermek içindir.

Katsayıların yorumu için iki ayrı kavram ayırt edilmelidir. Standardize edilmiş bir öznitelik için katsayı, öznitelik bir standart sapma arttığında tahminin ne kadar değiştiğini söyler. Ham birimde katsayı, öznitelik bir birim arttığında değişimdir. İkisi arasındaki ilişki basittir: `wⱼ(ham) = wⱼ(std) / σⱼ`. Programda bu eşitliği tahmin farkı olarak da doğruluyoruz.

Bir uyarı: çoklu regresyonda `wⱼ` "diğer öznitelikler sabitken" anlamına gelir. Eğer öznitelikler birbirine bağlıysa (Bölüm 58.7'de göreceğiz), bu cümle sanal bir senaryo tanımlar ve katsayı kararsız olabilir.

@@SEKIL|b58_artik.png|Artıklar: diyabet verisi (sol) ve değişen varyanslı sentetik veri (sağ), tahmine karşı.@@

Şekil 58.2'de sol panelde artıklar yatay bir bant içinde dağılır; bu, doğrusallığın ve sabit varyansın kabaca tutulduğunu gösterir. Sağ panelde ise artık yayılımı tahminle birlikte açılan bir huni biçimindedir. Bu desen, en küçük kareler varsayımının ihlalidir: tahmin standart hatası artık değişen varyans altında yanlış olur, ama katsayı tahmini hâlâ yansızdır. Bu sorun için ağırlıklı en küçük kareler (WLS) ya da sağlam standart hatalar kullanılır.

Programın çıktısı bu gözlemi sayısal olarak doğrular. Diyabet verisinde artıkların ortalaması `10⁻¹⁴` mertebesinde sıfırdır, Shapiro–Wilk p değeri `0,726`'dır; normallik reddedilmez. Ama `|artık|` ile tahmin arasındaki Spearman korelasyonu `0,193`'tür ve p değeri `0,001`'in altındadır. Bu, gerçek veride varyansın tam sabit olmadığını, ama sentetik örnekteki gibi güçlü olmadığını gösterir. Sentetik veride korelasyon `0,434`'tür.

Katsayı yorumu tarafında: standardize katsayılar arasında en büyük mutlak değer `8` numaralı öznitelikte (yani `s5`) görülür. Bu, yalnızca bu model ve bu bölmede geçerlidir; ölçek ve bağlantı değişirse sıralama da değişebilir. Ham birimdeki tahminle standardize tahmin arasındaki fark `5,7·10⁻¹⁴`'tür; yani dönüşüm eşitliği kesindir.

## 58.6 Doğrusal olmayanı doğrusal modelle: temel fonksiyonlar

Doğrusal modelin gücü, parametrelerde doğrusal olmasına rağmen girdilerde doğrusal olmayabilmesindedir. Bunu temel fonksiyonlar (basis functions) ile yaparız: `ŷ = Σ wⱼ φⱼ(x)`. Burada `φⱼ` herhangi bir dönüşüm olabilir. Model hâlâ doğrusal bir problemdir, çünkü `w` için en küçük kareler ya da gradyan inişi aynen geçerlidir.

Bu fikrin en eski iki biçimi polinom ve radyal tabanlı fonksiyon (RBF) ailesidir. Polinomlar `φ_k(x) = xᵏ` ile tanımlanır; ama yüksek dereceli kuvvetler sayısal olarak kötüdür, Vandermonde matrisi gibi koşul sayısı çok büyür (58.2'de gördük). Bu yüzden girdiyi önce `[-1, 1]` aralığına alıp Chebyshev tabanını kullanırız. RBF ise merkezlere olan uzaklığa göre tepe yapan bir çan eğrisidir: `φⱼ(x) = exp(−(x − cⱼ)² / (2s²))`.

Bu bölümde (ve bölümün sonuna doğru) sınır konusunu tekrar ele alacağız. Şimdi konuyu bir regresyon örneğiyle görelim: `y = sin(x) + N(0, 0,2²)` verisini, derecesi ve merkez sayısı farklı temel fonksiyonlarla uyduralım. Model seçimini eğitim kümesinin bir bölümünü doğrulama olarak ayırarak yaparız; test kümesi bu örnekte kullanılmaz. Eğitim MSE'si karmaşıklıkla her zaman düşer, ama doğrulama MSE'si bir noktada yükselir. Bu, aşırı uydurmanın (Bölüm 54.6) doğrudan göstergesidir.

Aşağıdaki program ayrıca XOR ve yarım ay veri kümelerini de içerir. Bu iki örnek, doğrusal modelin temel sınırını gösterir; onları Bölüm 58.15'te ele alacağız. Programın çıktısında bu satırlar yukarıda durur, o yüzden sınır tartışmasında onlara geri döneceğiz.

@@KODTAM|b58_11_taban.py@@

@@CIKTI|b58_11_taban.py@@

Sin uydurma örneğinde eğitim MSE'si polinom derecesi ile düşer: `derece 3`'te `0,0513`, `derece 15`'te `0,0418`. Doğrulama MSE'si ise `poly5`'te en düşük değere (`0,0279`) ulaşır, sonra `poly9` ve `poly15`'te yükselir. Bu tipik bir U biçimidir: karmaşıklık arttıkça önce eksik uydurma, sonra aşırı uydurma azalır. RBF ailesinde en iyi doğrulama değeri `rbf4`'te (`0,0312`) çıktı; `poly3` (`0,0308`) ile birlikte bu tek bölmede iki aile benzer sonuç verir. Seçim ölçütü doğrulama MSE'si olduğu için `poly5` seçilir.

Burada dürüst bir not gerekir: doğrulama kümesi 36 örnek içerdiği için bu sayılar gürültülüdür. Bir yöntemin diğerinden "daha iyi" olduğunu söylemek için birden çok bölme ve güven aralığı gerekir (Bölüm 49.9 ve 57). Burada amacımız, karmaşıklık seçiminin nasıl yapıldığını göstermektir.

## 58.7 Ridge (L2): koşul sayısını düzeltmek ve çoklu doğrusallık

Normal denklem `AᵀA w = Aᵀy` tekil ya da neredeyse tekil olduğunda çözüm kararsızdır. Düzenlileştirme (regularization) bu soruna bir ceza terimi ekleyerek yaklaşır. En yaygın biçim L2 cezasıdır (Ridge regresyonu, Tikhonov düzenlileştirmesi):

min ‖y − A w‖² + α ‖w‖²

Sapma (intercept) cezalandırılmaz; çünkü sapma yalnızca ortalamayı yerleştirir, öznitelikler üzerindeki etkisi değildir. Bu yüzden önce `y` ve her öznitelik kendi ortalamasına göre merkezlenir ve Ridge bu merkezlenmiş veri üzerinde çözülür. Merkezleme sonrası çözüm kapalı biçimdedir:

w = (Zᵀ Z + α I)⁻¹ Zᵀ y

Bu formülün önemli bir sonucu, `ZᵀZ + αI` matrisinin özdeğerlerinin her birinin `α` kadar artmasıdır. Yani en küçük özdeğer sıfıra yakın olsa bile `α > 0` ile kesinlikle pozitif tanımlı olur. Koşul sayısı `(σ_maks² + α)/(σ_min² + α)` olur ve `α` arttıkça düşer. Bu, Bölüm 48.10'daki "koşul sayısı kararlılığı" kavramının doğrudan uygulamasıdır.

SVD ile bakarsak Ridge çözümü açık bir biçim alır. `Z = U Σ Vᵀ` ise:

w = Σ (σᵢ / (σᵢ² + α)) (uᵢᵀ y) vᵢ

Her bileşen, OLS'in bileşeninin `σᵢ²/(σᵢ² + α)` ile çarpılmış halidir. Büyük tekil değerler (`σᵢ² ≫ α`) neredeyse etkilenmez; küçük tekil değerlere karşılık gelen bileşenler güçlü biçimde küçülür. Bu, Ridge'in gürültü yönlerini bastırmasının matematiksel açıklamasıdır. Etkin serbestlik derecesi `df(α) = Σ σᵢ²/(σᵢ² + α)` ile tanımlanır; `α = 0` için `df = p` ve `α → ∞` için `df → 0` olur.

Aşağıdaki program dört şey yapar: kapalı formun ve SVD yolunun sklearn ile uyumunu gösterir, Vandermonde matrisinde koşul sayısının `λ` ile düşüşünü ölçer, düzenlileştirme yolunu (katsayıların `α`'ya göre değişimi) CSV'ye yazar ve `α`'yı yalnızca eğitim kümesinde beş katlı çapraz doğrulama ile seçer. Çapraz doğrulamada ölçekleyici her katta yeniden öğrenilir (Bölüm 54.8'deki sızıntı kuralı). Test kümesi en sonda bir kez kullanılır.

@@KODTAM|b58_04_ridge.py@@

@@CIKTI|b58_04_ridge.py@@

Kapalı form ile sklearn'ün `Ridge` nesnesi `10⁻¹³` mertebesinde uyuşur. SVD yolu da aynı sonucu verir (`1,5·10⁻¹³`). `α = 10` için etkin serbestlik derecesi `8,64`'tür; yani on katsayılık modelde yaklaşık dokuz serbestlik kullanılmaktadır. Vandermonde matrisinde koşul sayısı `λ` ile dikkat çekici biçimde düşer: `λ = 0`'da `3,9·10¹¹`, `λ = 10⁻⁴`'te `8,8·10⁵`, `λ = 10⁻²`'de `8,8·10³`. Yani küçük bir `λ`, normal denklemi çözülebilir hâle getirir.

Çapraz doğrulama `α* = 31,62` seçti. Bu değer sklearn'ün `GridSearchCV` sonucuyla aynıdır. Testte Ridge `RMSE = 55,51`, `R² = 0,4065` verdi; OLS ise `RMSE = 55,29`, `R² = 0,4111`. Yani bu veri setinde ve bu bölmede Ridge, OLS'i geçemedi. Fark (0,22 RMSE) gürültü düzeyindedir ve burada Ridge'in faydası yoktur. Diyabet verisinde bazı öznitelikler birbirine bağlıdır (aşağıdaki VIF tablosu), ama bu bağlılık test tahminini çok bozmadığı için Ridge'in faydası sınırlı kalır. Ridge'in asıl faydası çoklu doğrusallık varken görülür; bunu bir sonraki deneyde göstereceğiz.

Çoklu doğrusallık (multicollinearity), iki ya da daha fazla öznitelik birbirine çok yakın olduğunda ortaya çıkar. Bu durumda katsayılar tek tek belirsizleşir, ama öznitelikler birlikte belirgin bir sinyal taşıyabilir. Aşağıdaki deneyde iki öznitelik `0,99995` korelasyonla neredeyse aynıdır ve gerçek katsayılar `(1, 1)`dir. 300 farklı tohumla tekrarlanmış deneyde OLS katsayılarını ve Ridge katsayılarını karşılaştırıyoruz. Ayrıca diyabet verisi için varyans enflasyon faktörünü (VIF) hesaplıyoruz: `VIF_j = 1/(1 − R_j²)`, burada `R_j²` öznitelik `j`'nin diğer öznitelikler üzerine regresyon R²'sidir.

@@KODTAM|b58_06_coklu.py@@

@@CIKTI|b58_06_coklu.py@@

@@SEKIL|b58_coklu_dogrusallik.png|Çoklu doğrusallık: 300 veri kümesinde OLS katsayıları (sol) ile Ridge katsayıları (sağ).@@

Sonuç Şekil 58.3'te çarpıcıdır. OLS katsayılarının her birinin standart sapması `5,18`'dir; yani `(1, 1)` gerçek değerinden çok uzakta, `−15` ile `17` arasında dağılırlar. Ridge (`α = 1`) katsayıları ise `0,034` standart sapma ile `1`'e çok yakın toplanır. Toplamın belirlenebilirliği de bunu destekler: `β₁ + β₂`'nin OLS standart sapması yalnızca `0,047`'dir. Yani OLS iki katsayının toplamını iyi bilir, ama farkı bilmez; çünkü veri bu farkı neredeyse hiç taşımaz. Ridge ise katsayıları eşit paylaştırarak kararsızlığı bastırır.

VIF değerleri aynı tabloyu gösterir: `s1` için `59,2`, `s2` için `39,2`, `s3` için `15,4`, `s4` için `8,9`, `s5` için `10,1`. Genel bir pratik kurala göre 10'un üzerindeki VIF değerleri sorunlu sayılır (genel bilgi). Diğer öznitelikler (`age`, `sex`, `bmi`, `bp`, `s6`) `1,2`–`1,5` arasında, yani bağımsızdır. Diyabet verisinde `s1` ve `s2` birbirine bağlıdır; ama bu bağlılık test tahminini ciddi biçimde bozmadığı için Ridge'in test kümesinde kazandırmaması şaşırtıcı değildir.

Pratik kural: çoklu doğrusallığı bir sorun olarak görmek için katsayıların değişkenliğine bak, sadece tahmin doğruluğuna değil. Doğruluk iyi olabilir ama katsayılar kararsız olabilir; bu durumda "x1 arttığında y artar" yorumunu yapamazsın.

## 58.8 Lasso (L1) ve Elastic Net: koordinat inişi ve seyreklik

Ridge katsayıları küçültür ama sıfıra eşitlemez. Oysa bazen hangi özniteliklerin gerçekten önemli olduğunu bilmek ve geri kalanını atmak isteriz. Bu, L1 cezasının (Lasso, Least Absolute Shrinkage and Selection Operator) yaptığıdır:

min (1/(2n)) ‖y − Z w‖² + λ ‖w‖₁,   ‖w‖₁ = Σ |wⱼ|

Neden L1 sıfır üretir, L2 üretmez? Geometrik cevap kısıt biçiminde görülür. Kısıtlı problemi `‖w‖ ≤ t` olarak yazarsak, L2 için kısıt bir çember, L1 için bir elmastır. Kare kaybın eş seviye eğrileri (elipsler ya da daireler) bu kısıt bölgesine ilk değdiği noktada çözüm bulunur. Elmasın köşeleri eksenlerin üzerindedir; eş seviye eğrisi bir köşeye değerse bir katsayı tam sıfır olur. Çember'de ise değme noktası genellikle eksenlerin dışındadır.

Analitik olarak aynı şey alt gradyan (subgradient) koşuluyla görülür. Lasso'nun optimalite koşulu, `wⱼ = 0` için `|ρⱼ| ≤ λ` olmasıdır; burada `ρⱼ = (1/n) zⱼᵀ(y − Z₋ⱼ w₋ⱼ)` öznitelik `j`'nin "artık ile ilişkisidir". Yani öznitelik `j`'nin artıkla ilişkisi ceza eşiğinin altında kaldıkça katsayı sıfırda kalır. Bu eşiğin en küçüğü `λ_maks = maks_j |zⱼᵀ(y − ȳ)|/n`'dir: `λ ≥ λ_maks` ise tüm katsayılar sıfırdır.

Lasso için kapalı form yoktur; bu yüzden koordinat inişi (coordinate descent) kullanırız. Her adımda bir `wⱼ`'yi sabit tutup diğerlerine göre optimize ederiz. Tek boyutlu problem bir yumuşak eşikleme (soft-thresholding) operatörüne indirgenir:

wⱼ ← S(ρⱼ, λ) / zⱼ,  S(z, γ) = sign(z) · max(|z| − γ, 0)

Burada `zⱼ = (1/n)‖zⱼ‖²` ve `ρⱼ` yukarıda tanımlanan artık ilişkisidir. Elastic Net bu iki cezayı birleştirir: `λ ρ ‖w‖₁ + (λ(1 − ρ)/2) ‖w‖²`. Koordinat güncellemesi bu durumda `wⱼ ← S(ρⱼ, λρ) / (zⱼ + λ(1 − ρ))` olur. Elastic Net, birbirine çok benzeyen öznitelikleri birlikte seçme eğilimindedir (gruplama etkisi, genel bilgi).

Aşağıdaki program koordinat inişini `enet_cd` (core dosyasında) ile yazar. Burada sadece kullanımı gösteriyoruz: sklearn ile karşılaştırma, `λ_maks` eşiğinin doğrulanması, düzenlileştirme yolu, CV ile λ seçimi ve test. Kendi `enet_cd` fonksiyonumuzun iç çalışmasını, scikit-learn'ün aynı işi yapan Cython kodu ile Kod Okuma bölümünde karşılaştıracağız.

@@KODTAM|b58_05_lasso.py@@

@@CIKTI|b58_05_lasso.py@@

Kendi Lasso koordinat inişimiz sklearn ile `10⁻⁹`'dan küçük farkla uyuşur; Elastic Net için fark `10⁻¹¹` mertebesindedir. `λ_maks = 47,10` olarak hesaplandı; `λ = 1,001·λ_maks`'ta on katsayının tamamı sıfır, `λ = 0,999·λ_maks`'ta yalnızca bir katsayı sıfırdan farklıdır. Bu, eşiğin teorisinin doğrulamasıdır. Düzenlileştirme yolunda (`λ` 47'den `0,01`'e düşerken) sıfır sayısı `10`'dan `0`'a iner. Şekil 58.4 kısıt geometrisini, Şekil 58.5 ise Ridge ve Lasso yollarını gösteriyor.

@@SEKIL|b58_l1_l2_kisit.png|L2 kısıtı (sol) ve L1 kısıtı (sağ) altında kısıtlı çözüm. Gri eğriler eş kayıp çizgileridir; kısıtlı çözüm, kısıt bölgesine ilk değdiği noktadadır.@@

Şekil 58.4 sağ panelde kısıtlı çözümün elmasın köşesinde olduğunu gösterir: `(1, 0)` noktasında `w₂` tam sıfırdır. Sol panelde aynı kayıp merkezi için çözüm çemberin üzerindedir ve `w₂ ≈ 0,13`'tür; sıfır değil. Bu geometri, iki cezanın neden farklı davrandığını hem görsel hem sayısal olarak açıklar.

@@SEKIL|b58_duzenlilestirme_yolu.png|Düzenlileştirme yolu: Ridge (sol; α, log ölçekte) ve Lasso (sağ; λ, log ölçekte) için standart katsayılar.@@

Şekil 58.5'te Ridge katsayıları düzgün biçimde sıfıra yaklaşır, hiçbiri tam sıfıra ulaşmaz. Lasso'da ise katsayılar belirli eşiklerde sıfıra düşer. Lasso'nun seçtiği öznitelik sayısı düzenlileştirme gücüne bağlıdır. CV ile seçilen `λ = 2,395` (sklearn ölçeğinde) on katsayıdan beşini sıfırladı. Test kümesinde Lasso `RMSE = 56,24`, `R² = 0,3906` verdi; Ridge `0,4065`, OLS `0,4111`. Yani bu veride seyreklik kazandırdı, ama doğruluktan ödün verdi. Seyreklik her zaman bedelsiz değildir: beş öznitelik, Ridge'in tüm öznitelikleri birlikte kullanmasından daha az bilgi taşıyorsa, tahmin kaybeder.

Yorum: Lasso'yu seçici bir özellik seçimi aracı olarak kullanabilirsin ama özellik seçiminin kararlılığını test etmeden sonuca güvenme. Farklı tohumlarda seçilen öznitelikler değişiyorsa, seçim gürültüden geliyor demektir.

## 58.9 Bayesçi yorum: L2 Gauss önseli, L1 Laplace önseli; λ seçimi

Bölüm 49.8'de MAP tahminini, en büyük olabilirliğe önsel bilgi ekleyen tahmin olarak tanımladık: `argmax p(y|w) p(w)`. Doğrusal regresyonda bu bağlantı düzenlileştirmeyi doğrudan açıklar.

Gauss gürültüsü `εᵢ ~ N(0, σ²)` ve Gauss önseli `w ~ N(0, τ² I)` alalım. Negatif log-posterior, sabitleri atarak şöyle olur:

(1/(2σ²)) ‖y − Z w‖² + (1/(2τ²)) ‖w‖²

Bu, `‖y − Zw‖² + (σ²/τ²) ‖w‖²` ile aynı minimizasyondur. Yani Ridge'deki `α = σ²/τ²`dir. Gürültü büyüdükçe (ya da önsel dar oldukça) ceza artar. L2 cezası, katsayıların sıfır civarında toplanmasına inanan bir önselin MAP tahminidir.

Laplace önseli `p(w) ∝ exp(−|w|/b)` alalım. Aynı adımda şu minimizasyonu elde ederiz:

(1/(2σ²)) ‖y − Z w‖² + (1/b) ‖w‖₁

Yani Lasso, katsayıların sıfır civarında ve çok sivri bir biçimde toplanmasına inanan Laplace önselinin MAP tahminidir. Laplace'ın kütlesi sıfırda yoğundur; bu, MAP'in neden tam sıfırlar ürettiğini sezgisel olarak açıklar. Ama dikkat: bu, sonsal dağılımın ortalaması (posterior mean) için geçerli değildir; o ortalama tam sıfır vermez (genel bilgi). Lasso'nun seyrekliği bir MAP özelliğidir.

Bu bağlantının pratik sonucu, `λ` (ya da `α`) değerinin bir gürültü-önsel oranı olduğudur. Gürültü ve önsel hakkında elinde bilgi yoksa `λ`yı veriden seçmek gerekir. Bu seçimi çapraz doğrulama ile yaparız (Bölüm 57): `λ` ızgarası logaritmik aralıkta tanımlanır, her `λ` için beş katlı CV ortalama hatası hesaplanır ve en küçük hata veren `λ` seçilir. Bu sırada ölçekleme pipeline içinde yapılmalıdır; çünkü ceza katsayının ölçeğine bağlıdır. Ölçeklenmemiş bir özniteliğin katsayısı daha büyük ölçekte olduğu için daha az cezalanır. Bu yüzden düzenlileştirme öncesi standardizasyon zorunludur.

Son bir not: `λ` seçiminde "en küçük hata" yerine "en büyük λ ile hatası en küçük olanın bir standart hata içinde kalan" kuralı (one-standard-error rule) bazen daha sade modeller verir (genel bilgi). Bu kuralın ayrıntıları Bölüm 57'de ele alınır.

## 58.10 Lojistik regresyon: sigmoid, log-odds, kayıp ve Newton

Doğrusal regresyon sürekli hedefler içindir. İkili sınıflandırmada (örneğin "arıza var" / "arıza yok") hedef 0 ya da 1'dir ve modelin çıktısının bir olasılık olmasını isteriz. Lojistik regresyon, doğrusal skoru sigmoid fonksiyonu ile olasılığa çevirir:

p(x) = σ(wᵀx + b),  σ(z) = 1 / (1 + e^(−z))

Sigmoid, her `z` için `(0, 1)` aralığında bir değer üretir ve `z = 0`'da tam `0,5`'tir. Şekil 58.6 solda bu eğriyi gösterir. Sigmoidin türevi `σ'(z) = σ(z)(1 − σ(z))`dir; bu basit ilişki gradyanı çok sadeleştirir.

Sigmoidi ters yönden okuyalım. Olasılık `p` ise odds `p/(1 − p)`dir ve log-odds `ln(p/(1−p))`dir. Lojistik regresyonda log-odds tam olarak doğrusaldır: `ln(p/(1−p)) = wᵀx + b`. Bu, katsayının yorumunu verir: `wⱼ`, `xⱼ` bir birim arttığında log-odds'un ne kadar değiştiğini söyler. Odds oranı (odds ratio) `e^{wⱼ}`dir: `xⱼ` bir birim arttığında odds'un kaç katına çıktığı. Şekil 58.6 sağda bu doğrusallığı ve bir örnek için olasılıkları gösterir.

::: ipucu
Odds oranı bir olasılık oranı değildir. Olasılık 0,50'den 0,60'a çıktığında odds 1'den 1,5'e çıkar: olasılık 1,2 kat, odds 1,5 kat artmıştır. Olasılık 0,01'den 0,02'ye çıktığında ise odds yaklaşık 2 kat artar. Bu fark sık yapılan bir hatadır.
:::

@@SEKIL|b58_sigmoid_logodds.png|Sigmoid (sol) ve log-odds'un öznitelikle doğrusal ilişkisi (sağ). Noktalar, Çözümlü Örnek 3'teki w = 0,8 ve b = −1,2 modeli için olasılıkları gösterir.@@

Kayıp: ikili çapraz entropi (Bölüm 51.9). Bir örnek için kayıp `−[y ln p + (1 − y) ln(1 − p)]`dir. Tüm veri üzerinde ortalama:

L(w) = −(1/n) Σ [yᵢ ln pᵢ + (1 − yᵢ) ln(1 − pᵢ)]

Gradyanı hesaplamak için `σ'` kullanılır. Her örnek için kayıp gradyanı `(pᵢ − yᵢ) xᵢ`dir; toplamda `∇L = (1/n) Aᵀ(p − y)`. Bu, Bölüm 51.10'daki softmax gradyanının ikili hâlidir: tahmin eksi gerçek etiket. Hessian ise `H = (1/n) Aᵀ S A`dır; burada `S = diag(pᵢ(1 − pᵢ))`. `S` köşegeninin negatif olmayan olduğunu ve `AᵀSA`'nın pozitif yarı-tanımlı olduğunu görmek kolaydır. Bu nedenle `L` konvekstir (Bölüm 50.4): yerel bir minimum varsa o küresel bir minimumdur.

Lojistik regresyonun kapalı formu yoktur; ama Newton yöntemi ikinci dereceden bilgiyi kullanarak birkaç adımda yakınsar (Bölüm 50.11). Newton adımı `w ← w − H⁻¹∇L`dir. Burada bir gözlem yapabiliriz: Newton adımı `(AᵀSA)⁻¹Aᵀ(y − p)` ile düzeltilmiş bir ağırlıklı en küçük kareler çözümüdür. Bu nedenle yöntem IRLS (Iteratively Reweighted Least Squares) adıyla da bilinir. Sonucu doğrulamak için: `w_yeni = (AᵀSA)⁻¹ Aᵀ S (A w + S⁻¹(y − p))`; `S⁻¹(y−p)` terimi çalışan yanıtın (working response) düzeltmesidir.

Aşağıdaki program lojistik regresyonu üç bölümde ele alır: meme kanseri verisinde Newton/IRLS ile L2 cezalı eğitim ve sklearn karşılaştırması (Bölüm 54.11'deki gradyan iniş sonucunun aynı amaç fonksiyonuna sahip ama farklı yöntemle ulaşılan karşılığı), sınıf ağırlığının etkisi (sentetik dengesiz veri, ayrı bölme) ve ayrılabilir veride cezasız kayıp. Bu üç deneyin ortak noktası, her sonucun bir baseline'a göre ölçülmesidir.

Meme kanseri verisinde sklearn'ün amaç fonksiyonu `C · Σ kayıp + ½‖w‖²`dir. Bizim ortalama kayıp biçimimizde bu `(1/n) Σ kayıp + (λ/2) ‖w‖²` ile eşleşir ve `λ = 1/(C·n)` alınır. Sapma cezalandırılmaz. `C = 1` seçtik.

@@KODTAM|b58_07_logistik.py@@

@@CIKTI|b58_07_logistik.py@@

Newton yöntemi on adımda `10⁻¹²`'nin altına indi. Sklearn ile katsayı farkı `1,1·10⁻⁶`dır. Bu fark, sklearn'ün L-BFGS çözücüsünün kendi durma ölçütünden kaynaklanabilir; iki yöntem aynı amaç fonksiyonunu çözer. Test kümesinde doğruluk `0,9649`, dengeli doğruluk `0,9524`'tür; baseline (hep çoğunluk sınıfını tahmin etmek) doğruluğu `0,6316`, dengeli doğruluğu `0,5000`dür. Bu bölmede Bölüm 54'teki sonuçtan farklı bir tohum kullandık, bu yüzden sayılar Bölüm 54'tekiyle birebir aynı değildir.

Katsayı yorumu: sınıf 1 iyi huylu (benign) sınıfıdır. Bu yüzden negatif katsayılar kötü huylu lehinedir. "radius error" standart sapması bir arttığında iyi huylu olma odds'u `0,305` katına düşer; yani kötü huylu olmanın odds'u yaklaşık `3,3` katına çıkar. Bu rakamlar, katsayıların ölçeğe bağlı olduğunu ve doğru yorum için standardizasyonun önemini gösterir.

Sınıf ağırlığı deneyi ayrı bir sentetik veri kümesinde yapıldı: `4 000` örnek, pozitif oranı `%5`. Sınıf ağırlıklı olmayan model dengeli doğrulukta `0,6878` verdi; pozitif sınıfın duyarlılığı (recall) yalnızca `0,381`'dir. Sklearn'ün `balanced` formülü `s = n/(K·n_sınıf)` ile ağırlıklandırılmış model `0,8380` dengeli doğruluk ve `0,8413` duyarlılık verdi. Ağırlığın amaç fonksiyonuna yansıması, örnek başına kaybın `sᵢ` ağırlığı ile çarpılmasıdır; gradyanda `Aᵀ(s ∘ (p − y))/n` olur. Tek bir bölmeyle bu bir kanıt değildir; birden çok tohum için (Bölüm 57'de) tekrarlanmalıdır.

Son deney ayrılabilir veri. İki sınıf, boyutta birbirinden tamamen ayrık. Ceza olmadan kayıp her zaman azalabilir: sınır ne kadar sert olursa `‖w‖` o kadar büyür ve log-olabilirlik `0`a yaklaşır ama hiçbir zaman ulaşmaz. Gradyan inişi `‖w‖`yi sınırsız büyütür. Gerçek sonucu tabloda görüyoruz: 100 adımda `‖w‖ = 2,03`, 20 000 adımda `3,93`. Büyüme yavaş ama durmaz. L2 cezası (`λ = 0,01`) ise `‖w‖`yi `1,70`'te sabitler. Bu, sonlu bir minimumun var olmasının pratik anlamıdır.

@@SEKIL|b58_lojistik_karar.png|İki boyutlu sentetik veride lojistik karar sınırı. Kırmızı çizgi p = 0,5, kesikli çizgiler p = 0,25 ve 0,75'tir.@@

Şekil 58.7 karar sınırının doğrusal olduğunu ve sınırın iki tarafındaki noktaların çoğunun doğru sınıflandığını gösterir. Bu veri kümesinde eğitim doğruluğu `0,925`tir; sınırın üzerinde kalan bir miktar karışıklık, iki Gauss'un üst üste binmesinden kaynaklanır. Karar eşiği `0,5` varsayılan seçimdir, ama maliyet farklıysa değiştirilebilir (Bölüm 57'de eşik seçimi).

@@SEKIL|b58_ayrilabilir_patlama.png|Ayrılabilir veride ‖w‖ değeri, adım sayısına göre (log ölçek): ceza yok (λ = 0) ile sınırsız büyüme, L2 cezası (λ = 0,01) ile sınırlı davranış.@@

Şekil 58.8 bu davranışı gösterir. Pratikte iki sonucu var: ayrılabilir verinin varlığını kendi başına bir uyarı işareti olarak düşünmelisin (öznitelikler sızıntı içerebilir, bkz. Bölüm 54.8), ve çoğu gerçek veride L2 cezası hem kararlılık hem de genelleme için gereklidir.

## 58.11 Çok sınıflı sınıflandırma: OvR ve softmax regresyonu

İki sınıftan fazlası varsa iki yol var. Birincisi, bire karşı hepsi (one-vs-rest, OvR): her sınıf için ayrı bir ikili lojistik regresyon eğitilir ve en yüksek skorlu sınıf seçilir. Her model yalnızca kendi sınıfını diğerlerinden ayırmaya çalışır; ortaya çıkan olasılıklar toplamı `1` etmez, çünkü modeller birbirinden habersizdir.

İkincisi softmax (çok terimli, multinomial) regresyon. `K` sınıf için `K` lineer skor (logit) hesaplanır: `zₖ = wₖᵀx + bₖ`. Olasılıklar ortak bir normalizasyonla bulunur:

pₖ = e^{zₖ} / Σⱼ e^{zⱼ}

Bu, Bölüm 51.10'da ayrıntılı olarak gördüğümüz softmax'tır. Kayıp, doğru sınıf `y` için çapraz entropidir: `L = −ln p_y`. Bunun log-sum-exp biçimi `L = lse(z) − z_y`dir; burada `lse(z) = ln Σ e^{zⱼ}`. Sayısal kararlılık için `lse` en büyük logit çıkarılarak hesaplanır (Bölüm 51.10). Gradyan: `∂L/∂zₖ = pₖ − yₖ`. Bu nedenle ağırlık gradyanı `∂L/∂W = Xᵀ(P − Y)/n`dir; burada `Y` one-hot etiketlerdir.

Softmax'ın parametre sayısı `K(d + 1)`dir. Dijital rakam veri kümesinde (64 piksel, 10 sınıf) bu `650` parametre demektir. Bu sayı, Bölüm 56'daki kategorik kodlama kararlarıyla birlikte düşünülmelidir.

Aşağıdaki program softmax regresyonunu sıfırdan yazar. Kayıp ve gradyan `core` dosyasındadır; L-BFGS (Bölüm 50.12) ile minimize edilir. Gradyanın doğruluğu sonlu farkla (Bölüm 50.3) on koordinatta denetlenir. Düzenlileştirme gücü `λ` yalnızca eğitim kümesinde beş katlı CV ile seçilir. Sonra sklearn ile karşılaştırma ve OvR ile karşılaştırma yapılır. Son olarak beş farklı bölmede tekrarlanmış sonuçlar verilir; bu, tek bir bölmenin gürültüsünü ölçmek içindir.

@@KODTAM|b58_08_softmax.py@@

@@CIKTI|b58_08_softmax.py@@

Gradyan denetimi `3,3·10⁻¹⁰` verdi; yani türetilmiş gradyan doğrudur. CV'de `λ = 10⁻⁴` en yüksek doğruluğu (`0,9596`) verdi; `10⁻¹`'e doğru gidildikçe doğruluk düşer, çünkü ceza çok güçlü olur. L-BFGS `514` adımda yakınsadı; sklearn'ün multinomial çözümüyle en büyük katsayı farkı `5,6·10⁻⁶`, test tahminlerinin uyumu `%100`dür. Test doğruluğu softmax için `0,9806`, OvR için `0,9694`, hep çoğunluk için `0,1028`, rastgele tahmin için beklenen `0,1000`dir. Eğitim doğruluğu (`0,9979`) test doğruluğundan biraz yüksektir; bu normal bir aşırı uydurma boşluğudur, ama büyük değildir.

Birden çok bölmede sonuç şöyle: softmax `0,9700 ± 0,0023`, OvR `0,9656 ± 0,0042` (5 bölme, ortalama ± örneklem standart sapması). Her bölmede softmax'ın farkı `0` ile `0,0083` arasında, hiçbirinde negatif değil. Bu, softmax'ın bu veride tutarlı biçimde biraz daha iyi olduğunu gösterir, ama fark küçüktür; yani bu, "softmax her zaman daha iyidir" demek değildir.

Hata analizi: en sık karıştırılan çiftler gerçek `8` → tahmin `5` (iki kez), gerçek `6` → tahmin `5` ve gerçek `8` → tahmin `1` (birer kez). Bu tür bir çift listesi, öznitelik mühendisliğinin nereye odaklanacağını söyler.

Şekil 58.9 iki boyutlu bir üç sınıflı örnekte softmax karar bölgelerini gösterir. Her bölge doğrusal bir sınırla ayrılır ve üç sınır bir noktada kesişir. Bu, softmax'ın tüm sınırlarının doğrusal olduğunu ve birleşik bir karar yapısı oluşturduğunu gösterir; OvR ise bölgeler arasında ara boşluklar bırakabilir.

@@SEKIL|b58_softmax_bolge.png|Softmax karar bölgeleri: üç sınıf, iki boyutlu sentetik veri, doğrusal sınırlar.@@

## 58.12 GLM çerçevesi ve Poisson regresyonu

Şimdiye kadar iki model gördük: Gauss hedefi için doğrusal regresyon ve Bernoulli hedefi için lojistik regresyon. İkisi de tek bir çatının örnekleridir: genelleştirilmiş doğrusal modeller (GLM). Bir GLM üç bileşenden oluşur: bir üstel aile dağılımı, bir doğrusal öngörü `η = wᵀx` ve bir bağlantı fonksiyonu `g` ki `g(μ) = η`, burada `μ = E[y]`.

Üstel aile, dağılımı `f(y; θ, φ) = exp((yθ − b(θ))/φ + c(y, φ))` biçiminde yazar. Bu biçimde ortalama `μ = b′(θ)` ve varyans `φ b″(θ)` olur. Üç tanıdık örnek:

| Dağılım | Hedef tipi | b(θ) | Doğal bağlantı | Model |
|---|---|---|---|---|
| Gauss | sürekli | θ²/2 | özdeşlik g(μ) = μ | doğrusal regresyon |
| Bernoulli | ikili | ln(1 + e^θ) | logit | lojistik regresyon |
| Poisson | sayım | e^θ | log g(μ) = ln μ | Poisson regresyonu |

Doğal bağlantı, `θ = η` yapan bağlantıdır; bu durumda olabilirlik gradyanı `Aᵀ(y − μ)` biçimini alır. Softmax de bir çok sınıflı GLM'dir (kategorik dağılım, softmax bağlantısı).

Poisson regresyonu sayım verisi içindir: bir zaman aralığında olan olayların sayısı. Bölüm 49'da, saatte gelen paket kaybı sayısını Poisson ile modellemiştik. Şimdi bu sayıyı öznitelikler (sıcaklık, titreşim) ile ilişkilendiriyoruz: `μ = exp(wᵀx + b)`. Log bağlantı, tahmini her zaman pozitif tutar ve çarpımsal bir yapı verir: `e^{wⱼ}`, `xⱼ` bir birim arttığında ortalama sayının kaç katına çıktığıdır (hız oranı, rate ratio).

Olabilirlik (log) `ℓ = Σ (yᵢ ηᵢ − e^{ηᵢ} − ln yᵢ!)`dir. Doğal bağlantı nedeniyle gradyan `Aᵀ(y − μ)` ve Hessian `−Aᵀ diag(μ) A`dır. Yani Newton adımı yine IRLS biçimindedir ve Poisson için de birkaç adımda yakınsar.

Bir uyarı: Poisson regresyonunda dispersiyon `μ`ye eşittir. Gerçek veride bu varsayım sık sık bozulur (aşırı yayılım, overdispersion). Uyumun kalitesini bu yüzden Pearson dispersiyonu ile ölçeriz: `Σ (yᵢ − μᵢ)²/μᵢ / (n − p)`. Gerçek model için bu değer `1` civarında olmalıdır; `1`'den belirgin büyükse aşırı yayılım vardır.

Aşağıdaki program sentetik bir veri kümesinde Poisson regresyonunu sıfırdan (IRLS) yazar ve sklearn ile karşılaştırır. Ayrıca sapma (deviance) ile test ölçümü yapar ve aşırı yayılımlı bir veri üretip dispersiyon değerini karşılaştırır. Sentetik veri: `n = 2 000`, iki standart öznitelik, gerçek katsayılar `(0,3; 0,6; −0,4)`, eğitim `1 500`, test `500`.

@@KODTAM|b58_09_poisson.py@@

@@CIKTI|b58_09_poisson.py@@

IRLS altı adımda yakınsadı ve sklearn ile katsayı farkı `5,7·10⁻¹⁰`dur. sklearn'ün `PoissonRegressor` nesnesinin varsayılan `alpha` değeri 1'dir (ceza); biz `alpha = 0` alarak cezasız MLE'yi karşılaştırdık. Test sapması (deviance) modelde `1,1485`, baseline'da (sabit ortalama) `2,0131`; MAE modelde `0,9609`, baseline'da `1,3889`. Tahmin katsayılarından `e^{0,5897} = 1,80` ve `e^{−0,394} = 0,67` oranları çıkar: sıcaklık bir standart sapma arttığında ortalama sayı yaklaşık `%80` artar, titreşim arttığında `%33` azalır.

Dispersiyon: gerçek model için Pearson dispersiyonu `1,062`, aşırı yayılımlı veri için `1,857`. Teorik olarak Gamma karışımı (ortalama 1, şekil 2) altında dispersiyon `1 + μ/2` olur; ortalama `μ = 1,686` ile bu `1,843`tür ve gözlemle (`1,857`) uyumludur.

Dikkat edilmesi gereken bir nokta: gerçek Poisson veride bile marjinal varyans (`3,555`) ortalamanın (`1,645`) iki katından büyüktür. Bu bir aşırı yayılım işareti değildir; ortalama `x`'e bağlı olduğu için gözlemler arasındaki değişkenlik `Var(μ(x))` terimini de içerir. Bu yüzden dispersiyonu koşullu olarak, yani model uyumu sonrası Pearson istatistiğiyle ölçmelisin.

## 58.13 Pratik: sınıf ağırlığı, aykırı değerler ve Huber kaybı

Pratikte doğrusal modelleri eğitirken karşına çıkan üç sorun var. Ölçekleme (58.3'te gördük) yakınsamayı etkiler. Sınıf dengesizliği (58.10'da gördük) dengeli doğruluğu bozar. Aykırı değerler ise kare kaybı yüzünden modeli çarpıtabilir.

Aykırı değer sorununu şöyle düşünelim: kare kayıp büyük hataları karesel cezalandırır. Bir noktanın hatası 20 birimse, o nokta 400 birimlik bir kayıp katkısı yapar; bu, diğer 199 normal noktanın toplam katkısını bile gölgede bırakabilir. Mutlak hata (MAE, L1 kaybı) bu etkiyi doğrusal büyütür, ama türevi süreksizdir. Huber kaybı ikisinin iyi yanlarını birleştirir:

ρ_δ(r) = ½ r²,  |r| ≤ δ  ;  δ(|r| − δ/2),  |r| > δ

Küçük hatalarda karesel (kare kaybın verimliliği), büyük hatalarda doğrusal (MAE'nin dayanıklılığı). Geçiş noktası `δ`dır; sklearn'ün `HuberRegressor`'ında varsayılan `epsilon = 1,35`tir. Türevi `ψ(r) = clip(r, −δ, δ)`dir: büyük artıklar ağırlığını sınırlandırır. MAE için (medyan regresyonu) kapalı form yoktur, ama doğrusal programa dönüştürülebilir: `min Σ (u + v)` koşulu `Aw + u − v = y`, `u, v ≥ 0`. Bu programı `linprog` ile çözeriz.

Aşağıdaki deney, gerçek eğimi `0,5` olan bir doğrusal veri üretir ve yüzde beşini `+20` ile kaydırır. Önce tek bir veri kümesinde üç yöntemin eğimini karşılaştırır, sonra `200` farklı veri kümesi üzerinde eğim hatalarının ortalama ve yayılımını ölçeriz. Bu ikinci kısım tek bir kümenin şansını ortadan kaldırmak içindir.

@@KODTAM|b58_10_huber.py@@

@@CIKTI|b58_10_huber.py@@

Tek bir veri kümesinde MSE'nin eğimi `0,342` (gerçek `0,5`), LAD `0,463`, Huber `0,439`. Sklearn'ün `HuberRegressor`'ı `0,449` verdi; sklearn ölçek parametresini (`σ`) de öğrendiği için birebir aynı değildir, ama yönü aynıdır. Asıl sonuç 200 tekrar üzerinde: MSE'nin eğim hatasının RMSE'si `0,1056`, LAD'ın `0,0308`, Huber'in `0,0269`. Yani Huber, bu aykırı değer düzeyinde MSE'nin hatasını yaklaşık dörtte birine indirdi.

@@SEKIL|b58_huber_aykiri.png|Aykırı değerli veri üzerinde MSE (OLS), LAD ve Huber uydurma çizgileri; noktalı çizgi gerçek doğrudur.@@

Şekil 58.10'da MSE çizgisi aykırı değerlere doğru eğilmiştir; LAD ve Huber çizgileri gerçek doğruya yakın kalır. Bu, kare kaybın "ortalamaya" gittiğini, mutlak hatanın "medyana" gittiğini gösterir. Hangi tahminin doğru olduğu, aykırı değerlerin ne olduğuna bağlıdır: ölçüm hatasıysa dışlamak ya da dayanıklı yöntemlere geçmek mantıklıdır; gerçek bir olay (örneğin nadir bir arıza) ise onu modelden çıkarmak hatalı olabilir.

Son olarak, sınıf ağırlığının ölçüm kuralı: dengeli doğruluk ve pozitif sınıf duyarlılığı gibi ölçüleri sadece ağırlıklı eğitimle değil, ayrı bir test kümesinde ve bir baseline ile birlikte raporla. Eşik seçimi ve ayrıntılı metrikler Bölüm 57'dedir.

## 58.14 Gömülü ve edge: modeli C'ye aktarmak ve kuantizasyon

Doğrusal modelin en güçlü özelliklerinden biri, eğitildikten sonra çıkarımın (inference) basit olmasıdır. Lojistik modelde tahmin şu kadardır: `d` çarpma-toplama ve bir sigmoid. Bu, bir mikrodenetleyicide (STM32 gibi bir Cortex-M4) çalışmak için idealdir. Bölüm 43'te bare-metal C, Bölüm 46'da ise Edge AI ve TinyML'de gömülü hedefleri gördük; burada bu iki bilgiyi birleştiriyoruz.

Önce bir gözlem: karar için sigmoide gerek yoktur. `p > 0,5` ⇔ `wᵀx + b > 0`. Sigmoid yalnızca olasılık gerektiğinde hesaplanır. Bu, bir mikrodenetleyicide `exp` çağrısını atlamak demektir; `exp` yavaştır ve kütüphane gerektirir.

Ağırlıkları kuantize etmek bellek ve hız kazancı sağlar. Simetrik int8 kuantizasyonunda ölçek `olcek = max|w| / 127`dir ve `wq = round(w / olcek)` ile int8 tamsayılar elde edilir. Çıkarımda `wⱼ ≈ olcek · wqⱼ` kullanılır. Bu, Bölüm 46'da gördüğümüz kuantizasyonun en basit biçimidir: yalnızca ağırlıklar kuantize edilir, girdi ve birikim `float` kalır.

Aşağıdaki program meme kanseri verisinde eğitilmiş modeli Python'dan okunabilir bir C başlık dosyasına yazar (ağırlıklar hem float hem int8 olarak), test kümesini de bir C dizisi olarak gömer ve WSL üzerinde `gcc` ile derleyip çalıştırır. Sonra C çıktılarını Python'un float64 sonuçlarıyla karşılaştırır. C tarafındaki iki fonksiyon (`b58_tahmin.c`) ve test ana programı (`b58_main.c`) ayrı dosyalardır.

@@KODTAM|b58_tahmin.c@@

@@KODTAM|b58_main.c@@

@@KODTAM|b58_12_gomulu.py@@

@@CIKTI|b58_12_gomulu.py@@

Sonuçlar: ağırlıkların kuantizasyon ölçeği `0,009346`, en büyük yuvarlama hatası `4,55·10⁻³`. Float ile int8 modeli arasındaki en büyük olasılık farkı `2,61·10⁻³`, ama test doğruluğu iki modelde de `0,9649` ve kararlar `%100` uyumlu. Ağırlık belleği `120` bayttan (30 float) `30` bayta (30 int8) düştü. C float sonucu ile Python float64 sonucu arasındaki fark `1,1·10⁻⁷`dir; bu float32 hassasiyetinin beklenen büyüklüğüdür. Derleme `-Wall -Wextra` altında uyarısız geçti.

Cortex-M4 hedefi için nesne dosyası boyutunu ölçtük. STM32CubeIDE 1.19.0 ile gelen ARM araç zinciri (`arm-none-eabi-gcc` 13.3.1) ile şu komutlar çalıştırıldı:

```term
$ arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=hard \
    -mfpu=fpv4-sp-d16 -Os -Wall -Wextra -std=c11 -c b58_tahmin.c \
    -o b58_tahmin_m4.o
$ arm-none-eabi-size b58_tahmin_m4.o
   text    data     bss     dec     hex filename
    106       0       0     106      6a b58_tahmin_m4.o
```

Bu rakam bağlanmış bir imajın boyutu değildir; yalnızca `text` bölümünün nesne dosyasındaki boyutudur. Bağlanmış imaj `expf` için libm kodunu ve başlangıç kodunu da içerir. Yani gerçek flash kullanımı bundan büyük olacaktır; bunu bağlayıcı çıktısından ölçmelisin.

Bir mimari notu: x86'da `call` komutu dönüş adresini yığına iter. ARM Cortex-M'de ise `bl` (branch with link) dönüş adresini `LR` yazmacına koyar; yalnızca iç içe çağrılarda yığına kaydedilir. Bu fark, bir fonksiyonun yığın kullanımını ölçerken ve kesme işleyicilerinde önemlidir (Bölüm 44).

## 58.15 Doğrusal modelin sınırları ve köprü

Doğrusal model, öznitelikler dönüştürülmemişse girdilerin doğrusal bir kombinasyonunu öğrenir. Bu, bazı problemleri çözemez. Klasik örnek XOR: `(0,0)` ve `(1,1)` sınıf 0, `(0,1)` ve `(1,0)` sınıf 1. Bu dört noktayı ayıran tek bir doğru yoktur; herhangi bir doğru sınıfları karıştırır.

Bölüm 58.6'daki programda XOR'u gürültülü (`σ = 0,1`) biçimde ürettik. Doğrusal lojistik modelin test doğruluğu `0,420` çıktı. Rastgele tahmin yaklaşık `0,5` verirdi; bu sonuç bir tahmin edilemezlik değil, doğrusal sınırın XOR'u ayıramamasının sonucudur. Girdiye `x₁·x₂` öznitelik olarak eklendiğinde aynı model `1,000` doğrulukla çözer. Yani model değişmedi, öznitelik seti değişti. Bu, öznitelik mühendisliğinin neden bu kadar önemli olduğunu gösteren en sade örnektir.

Yarım aylar veri kümesi daha gerçekçi bir sınır problemidir. Doğrusal model `0,910` verdi. Üçüncü dereceden polinom öznitelikleriyle (9 öznitelik) `0,940`a çıktı; beşinci dereceye (20 öznitelik) çıkmak daha fazla kazandırmadı. Bu veride doğrusal sınırın tavanı yaklaşık `0,91`dir ve polinom öznitelikler bu tavanı biraz aşar. Bölüm 55'te benzer bir iki yarım ay kümesinde gizli katmanlı bir sinir ağının eğri biçimli sınırı nasıl öğrendiğini gördük; doğrusal modelin bu veride neden yetersiz kaldığı orada görsel olarak açıktır.

Bu sınırları aşmanın üç ana yolu, sonraki bölümlerin konusudur:

- **Çekirdek yöntemleri (Bölüm 60).** Çekirdek hilesi (kernel trick), polinom ya da RBF öznitelikleri açıkça oluşturmadan, bunların iç çarpımını hesaplar. Bu bölümde temel fonksiyonları elle seçtik; orada seçim yerine çekirdek kullanılır.
- **Ağaçlar ve ensemble yöntemleri (Bölüm 59).** Karar ağacı eksenlere paralel bölmeler yaparak doğrusal olmayan bölgeleri otomatik oluşturur. Tablo verisinde bu yaklaşım genellikle doğrusal modellerden güçlüdür.
- **Sinir ağları (Bölüm 63).** Gizli katman, temel fonksiyonları veriden öğrenir. Doğrusal modelin "öznitelikleri elle seç" adımı, bir sinir ağında "öznitelikleri öğren" adımına dönüşür.

Bu üç yolda da bir doğrusal model baseline olarak kalır. Karmaşık modelin kazancını ölçmek için önce doğrusal modeli iyi kurmak zorundasın.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, zorluk sırasıyla ★, ★★, ★★ ve ★★★ olarak dizilmiştir. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntüyü bul, iyileştir ve doğrula. Doğrulama adımında elle iz sürme tablosu bulunur. Her örneğin sonunda, hiçbir yapay zekâ aracı kullanmadan çözebilmen için bir varyasyon sorusu vardır. Örneklerdeki sayılar, bölümün sonundaki doğrulama programıyla birebir denetlenmiştir.

### Örnek 1 (★): Beş noktada normal denklemle doğru uydurma

Beş nokta `(1, 2), (2, 3), (3, 5), (4, 4), (5, 6)` veriliyor. Model `ŷ = a + b x` olsun. En küçük kareler katsayılarını normal denklemle elle bul, artıkları hesapla ve SSE'yi bul.

**Adım 1 — Anla.** İstenenler: `a` ve `b`, artıklar `rᵢ = yᵢ − ŷᵢ` ve `SSE = Σ rᵢ²`. Tasarım matrisinin ilk sütunu hep 1'dir: `A = [1 xᵢ]`.

**Adım 2 — Örnekle.** Bu veri ilk bakışta yukarı doğru bir eğilim gösteriyor: `x` arttıkça `y` ortalama olarak artıyor. Ama `(3, 5)` noktası eğrinin biraz üstünde, `(4, 4)` altında. Yani doğru tam oturmayacak; artıkların bir kısmı pozitif, bir kısmı negatif olacak.

**Adım 3 — Kaba çöz.** Gerekli toplamlar: `n = 5`, `Σx = 15`, `Σy = 20`, `Σx² = 55`, `Σxy = 2 + 6 + 15 + 16 + 30 = 69`. Normal denklem `AᵀA = [[5, 15], [15, 55]]` ve `Aᵀy = [20, 69]` verir.

**Adım 4 — Örüntü.** `2×2` sistemi Cramer kuralıyla çözülebilir. Determinant `5·55 − 15·15 = 50`. `a = (55·20 − 15·69)/50 = 65/50 = 1,3` ve `b = (−15·20 + 5·69)/50 = 45/50 = 0,9`. Yani `ŷ = 1,3 + 0,9x`.

**Adım 5 — İyileştir.** Artıkları tek tek hesaplamak yerine kontrol toplamlarını kullan: en küçük kareler çözümünde `Σ rᵢ = 0` ve `Σ xᵢ rᵢ = 0` olmalıdır (normal denklemin iki satırı). Bu iki koşul, hesabın doğruluğunun hızlı kontrolüdür.

**Adım 6 — Doğrula.** İz tablosu:

| x | y | ŷ = 1,3 + 0,9x | r = y − ŷ | r² | x·r |
|---|---|---|---|---|---|
| 1 | 2 | 2,2 | −0,2 | 0,04 | −0,2 |
| 2 | 3 | 3,1 | −0,1 | 0,01 | −0,2 |
| 3 | 5 | 4,0 | 1,0 | 1,00 | 3,0 |
| 4 | 4 | 4,9 | −0,9 | 0,81 | −3,6 |
| 5 | 6 | 5,8 | 0,2 | 0,04 | 1,0 |
| Toplam | | | 0,0 | 1,90 | 0,0 |

`Σ r = 0` ve `Σ x r = 0` sağlanır, `SSE = 1,90`. Programın çıktısı (`a = 1,3000`, `b = 0,9000`, `SSE = 1,9000`) tabloyla birebir tutar.

**Bunu AI'sız yazabilir misin?** Noktalar `(0, 1), (1, 3), (2, 4)` olsun. Normal denklemi kur, `a` ve `b`yi bul, SSE'yi hesapla. Sonra sonucu iki kontrol koşuluyla (`Σ r = 0`, `Σ x r = 0`) doğrula.

### Örnek 2 (★★): Ridge'in iki öznitelikli kosegen tasarımda küçülmesi

Ortalanmış bir veri kümesinde üç örnek ve iki öznitelik var: `X = [[1, 1], [−1, 1], [0, −2]]`, `y = (2, 1, −3)`. Ridge (`α`) çözümünü `α = 0, 2, 6` için hesapla ve hangi katsayının daha çok küçüldüğünü açıkla.

**Adım 1 — Anla.** İstenen: `w(α) = (XᵀX + αI)⁻¹ Xᵀy`. `α = 0` OLS'tir. Ortalanmış olduğu için sapma yok.

**Adım 2 — Örnekle.** Birinci öznitelik `(1, −1, 0)`, ikincisi `(1, 1, −2)`. İkincisinin varyansı daha büyük; yani ikinci öznitelik veride daha çok "yer kaplıyor".

**Adım 3 — Kaba çöz.** `XᵀX`'i hesapla: birinci sütunun normu `1 + 1 + 0 = 2`, ikincinin normu `1 + 1 + 4 = 6`, çapraz terim `1·1 + (−1)·1 + 0·(−2) = 0`. Yani `XᵀX = diag(2, 6)`. `Xᵀy = (2 − 1 + 0, 2 + 1 + 6) = (1, 9)`.

**Adım 4 — Örüntü.** Köşegen olduğu için iki denklem ayrılır: `w₁ = 1/(2 + α)` ve `w₂ = 9/(6 + α)`. Her katsayı kendi `XᵀX` köşegeniyle orantılı küçülür: birinci öznitelik için oran `2/(2+α)`, ikinci için `6/(6+α)`. Büyük varyanslı öznitelik daha az küçülür.

**Adım 5 — İyileştir.** `α = 2` için `w₁ = 1/4 = 0,25` ve `w₂ = 9/8 = 1,125`. `α = 6` için `w₁ = 1/8` ve `w₂ = 9/12 = 0,75`. Ridge, küçük varyanslı yönü daha sert bastırır; bu, Bölüm 58.7'deki SVD yorumunun bir sonucudur.

**Adım 6 — Doğrula.** İz tablosu:

| α | (XᵀX + αI) | Xᵀy | w = (w₁, w₂) |
|---|---|---|---|
| 0 | diag(2, 6) | (1, 9) | (0,5000; 1,5000) |
| 2 | diag(4, 8) | (1, 9) | (0,2500; 1,1250) |
| 6 | diag(8, 12) | (1, 9) | (0,1250; 0,7500) |

Programın çıktısı tabloyla aynıdır.

**Bunu AI'sız yazabilir misin?** Aynı `X` için `α = 4` değerini hesapla ve `w₁`in `α = 2` ile `α = 6` arasında olduğunu doğrula. Sonra `X`in ikinci sütununu `(1, 1, −2)` yerine `(2, 2, −4)` yap ve yeni katsayıları yaz: ikinci öznitelik şimdi daha çok küçülür mü, neden?

### Örnek 3 (★★): Lojistik katsayısının odds oranı

Bir arıza sınıflandırıcısı `p(x) = σ(−1,2 + 0,8x)` modeliyle eğitildi; `x` standardize edilmiş bir sıcaklık özniteliği. `x = 0, 1, 2` için olasılıkları ve odds değerlerini hesapla; `x`'in bir birim artışının odds'u kaç katına çıkardığını bul.

**Adım 1 — Anla.** Üç olasılık, üç odds ve bir oran isteniyor. Odds `p/(1 − p)`dir, odds oranı iki odds'un bölümüdür.

**Adım 2 — Örnekle.** `x = 0` ortalama sıcaklık demek. `x = 2` ortalamanın iki standart sapma üzerinde. Model yüksek sıcaklıkta arıza olasılığını artırıyor; ama bu bir olasılık, kesinlik değil.

**Adım 3 — Kaba çöz.** `z(x) = −1,2 + 0,8x`. `z(0) = −1,2`, `z(1) = −0,4`, `z(2) = 0,4`. Sigmoid değerleri: `σ(−1,2) ≈ 0,2315`, `σ(−0,4) ≈ 0,4013`, `σ(0,4) ≈ 0,5987`.

**Adım 4 — Örüntü.** Log-odds doğrusal olduğu için `x`'in bir birim artışı log-odds'u tam `0,8` artırır. Odds oranı `e^{0,8} ≈ 2,2255`tir. Bu, `x`'in her birim artışında odds'un `2,23` katına çıktığı anlamına gelir; olasılık ise aynı oranda artmaz.

**Adım 5 — İyileştir.** Odds değerleri: `x = 0` için `0,2315/0,7685 ≈ 0,3012`, `x = 1` için `0,6703`, `x = 2` için `1,4918`. Oranlar: `0,6703/0,3012 ≈ 2,2255`, `1,4918/0,6703 ≈ 2,2255`. İki oran da aynı çıkar; bu log-odds'un doğrusallığının sayısal kanıtıdır.

**Adım 6 — Doğrula.** İz tablosu:

| x | z = −1,2 + 0,8x | p = σ(z) | odds = p/(1 − p) |
|---|---|---|---|
| 0 | −1,20 | 0,2315 | 0,3012 |
| 1 | −0,40 | 0,4013 | 0,6703 |
| 2 | 0,40 | 0,5987 | 1,4918 |

Oran: `e^{0,8} = 2,2255`. Programın çıktısı (`odds = 0,3012; 0,6703; 1,4918`, `e^0,8 = 2,2255`) tabloyla birebir tutar.

**Bunu AI'sız yazabilir misin?** Bir model `p(x) = σ(0,5 − 1,5x)` ile `x = 0` ve `x = 1` için olasılıkları hesapla. Odds oranını yaz ve neden negatif katsayının odds'u azalttığını açıkla. Son olarak "olasılık iki katına çıktı" ile "odds iki katına çıktı" ifadelerinin neden aynı olmadığını bir örnekle göster.

### Örnek 4 (★★★): Softmax regresyonunda tek bir gradyan adımı

Üç örnek, iki öznitelik, üç sınıf: `X = [[1, 0], [0, 1], [1, 1]]`, etiketler `y = (0, 1, 2)`. Ağırlıklar sıfırdan başlıyor (`W = 0`, `b = 0`), öğrenme oranı `η = 0,5`. Softmax çıktısını, kaybı ve bir gradyan adımından sonraki yeni `W`yi hesapla.

**Adım 1 — Anla.** İstenen: ilk olasılık matrisi `P`, gradyan `G = Xᵀ(P − Y)/n`, güncellenmiş `W` ve yeni kayıp. Sıfır ağırlıkta tüm logitler sıfırdır.

**Adım 2 — Örnekle.** `x = (1, 0)` ilk sınıfa ait olmalı; ama model henüz hiçbir şey öğrenmedi, bu yüzden her sınıfa eşit olasılık verecek. Adım sonrası `x = (1, 0)` için ilk sınıfın olasılığı artmalı; bu beklentiyi sonunda kontrol edeceğiz.

**Adım 3 — Kaba çöz.** Sıfır logitlerle `P = 1/3` her yerde. `P − Y` satırları: `(−2/3, 1/3, 1/3)`, `(1/3, −2/3, 1/3)`, `(1/3, 1/3, −2/3)`. Gradyanın ilk öznitelik sütunu `(1, 0, 1)` ile çarpılır: birinci ve üçüncü satırların toplamı `(−1/3, 2/3, −1/3)`. İkinci öznitelik `(0, 1, 1)` ile: ikinci ve üçüncü satırların toplamı `(2/3, −1/3, −1/3)`. `n = 3` ile bölünce `G = [[−1/9, 2/9, −1/9], [2/9, −1/9, −1/9]]`.

**Adım 4 — Örüntü.** Bir gradyan adımı `W ← W − η G` ile yapılır. Her sütunun toplamı sıfırdır (`−1/9 + 2/9 − 1/9 = 0`), çünkü softmax'ta logitlere ortak bir sabit eklemek olasılığı değiştirmez. Bu, ağırlık uzayında bir serbestlik olduğu anlamına gelir.

**Adım 5 — İyileştir.** `W_yeni = W − 0,5 G = [[1/18, −1/9, 1/18], [−1/9, 1/18, 1/18]]`. Yeni logitler: `x = (1, 0)` için `(1/18, −1/9, 1/18)`, sonra softmax; bu, `(0,3513; 0,2974; 0,3513)` verir. Ortalama kayıp `ln 3 ≈ 1,0986`dan `1,0276`ya düşer.

**Adım 6 — Doğrula.** Yeni olasılıklar:

| x | p₀ | p₁ | p₂ | doğru sınıf | doğru sınıf olasılığı |
|---|---|---|---|---|---|
| (1, 0) | 0,3513 | 0,2974 | 0,3513 | 0 | 0,3513 |
| (0, 1) | 0,2974 | 0,3513 | 0,3513 | 1 | 0,3513 |
| (1, 1) | 0,3143 | 0,3143 | 0,3713 | 2 | 0,3713 |

Olasılıklar bir satırda toplamı `1` eder. Programın çıktısı (`G`, `W_yeni`, `kayıp önce = 1,098612`, `sonra = 1,027603`) tabloyla birebir tutar. Dikkat: bir adım, doğru sınıfın olasılığını `0,33`ten yalnızca `0,35`e çıkardı; gerçek öğrenme için birçok adım gerekir (Bölüm 50.10).

**Bunu AI'sız yazabilir misin?** Aynı veriyi `η = 1` ile bir kez daha güncelle. Yeni kaybın `η = 0,5` sonucundan daha düşük mü yoksa daha yüksek mi çıktığını, yeni olasılıkları hesaplayarak tahmin et ve sonra doğrula. Sonuç, öğrenme oranının neden hem hızı hem kararlılığı etkilediğini gösterir.

Aşağıdaki programlar, dört örnekteki elle hesaplanan sayıları doğrular.

@@KODTAM|b58_ornek.py@@

@@CIKTI|b58_ornek.py@@

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı kullanma. Kodu, testleri ve ölçümleri kendin yaz. Amaç, aşağıdaki kavramları bir mülakatta ya da boş bir IDE'de yeniden kurabilmektir. Bir hata bulursan, önce hatayı kendin çöz; bu, bu bölümün en değerli kısmıdır.
:::

### Proje 1 (★★): Sıfırdan doğrusal modeller kütüphanesi

**Amaç.** Bu bölümdeki yedi modeli (OLS, Ridge, Lasso, Elastic Net, lojistik regresyon, softmax regresyonu ve Poisson regresyonu) tek bir küçük kütüphanede topla ve her birini scikit-learn ile test et. Kütüphaneyi bir "gerçek veri" üzerinde karşılaştırmalı raporla bitir.

**Yapılacak / Beklenen davranış.** Kütüphane, her model için bir `fit` ve bir `predict` işlevi sunsun. Lasso ve Elastic Net koordinat inişiyle çözülsün; lojistik ve Poisson için Newton (IRLS) kullanılsın; softmax için bir kayıp ve gradyan fonksiyonu ile bir optimize edici kullanılsın. Her model için bir test paketi yaz: sklearn ile katsayı farkı, gradyanın sonlu fark denetimi ve küçük bir sentetik veride bilinen gerçek katsayıların geri kazanılması. Son olarak üç veri kümesinde (diyabet, meme kanseri, rakamlar) test kümesinde karşılaştırmalı bir tablo üret: her model, bir baseline ve sklearn'ün sonucu.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Önce bu bölümdeki `b58_core.py` dosyasını okumadan, kendi fonksiyonlarını yazmayı dene. Sonra kendi sürümünü bu bölümdekiyle karşılaştır. Koordinat inişinde yakınsama koşulunu bir `tol` ile yaz ve adımların ne zaman durduğunu raporla. Lojistik için Hessian'ın tekil olabileceği durumu (ayrılabilir veri) ele al; bir ceza terimi nasıl yardım eder? Poisson için dispersiyonu ayrıca hesapla.

**Başarı kriterleri.** (1) Her model için sklearn ile en büyük katsayı farkı `10⁻⁵`'ten küçük (sklearn'ün kendi toleransı dışında kalan modeller için bunu açıkça raporla). (2) Gradyan testleri geçer. (3) Tahmin, bir baseline'ı test kümesinde geçer; geçmiyorsa bunu raporda açıkça söyle. (4) Karşılaştırma tablosunda her değer bir tohum ve bir bölme ile birlikte verilmiştir. (5) Kütüphane sabit tohumla iki kez çalıştırıldığında aynı sayıları üretir.

### Proje 2 (★★★): Bir batarya sağlık kestirim modeli ve mikrodenetleyici aktarımı

**Amaç.** EV bataryasının kalan kullanım ömrünü (döngü sayısı cinsinden) tahmin eden bir doğrusal model kur, bunu bir Cortex-M4 üzerinde çalışacak C koduna aktar ve bellek ve hız ölçümlerini yap. Veri tamamen sentetik olacak; bunu açıkça belirt ve gerçek bir batarya verisi gibi sunma.

**Yapılacak / Beklenen davranış.** Sabit tohumlu bir üreteçle, her biri ayrı bir batarya olan `600` hücre üret. Her hücre için şu öznitelikleri üret: ortalama şarj sıcaklığı, akım dalgalanması, iç direnç tahmini, döngü başına kapasite kaybı eğilimi ve bir dizi gürültülü ölçüm. Hedef kalan döngü sayısı olsun. Ridge ve Lasso'yu hücre bazında gruplanmış çapraz doğrulama ile karşılaştır (aynı hücrenin verisi hem eğitimde hem doğrulamada olmasın; Bölüm 54.8'deki grup sızıntısı). Seçilen modeli C koduna aktar, Cortex-M4 için derle ve `arm-none-eabi-size` ile boyutunu ölç.

**Önerilen yaklaşım (ipucu).** Öznitelikleri üretirken kalan ömrü etkileyen bir gerçek model tanımla (örneğin lineer bir bozulma ve bir sıcaklık çarpanı) ve gürültüyü ekle. Gruplanmış CV için her hücreyi bir grup olarak ele al. Ölçeklemeyi her katta yalnızca eğitim kısmından öğren. C tarafında sigmoid yerine yalnızca işaret kontrolü yeterli olup olmadığını düşün. Bellek ölçümü için hem `.o` hem bağlanmış imajı (`.elf`) raporla ve farkı açıkla.

**Başarı kriterleri.** (1) Veri üretimi sabit tohumla tekrarlanabilir. (2) Ridge ve Lasso için grup-CV ortalama ve standart sapması raporlanmış. (3) Model baseline'ı (hücre ortalaması) test hatasında geçiyor. (4) C kodu uyarısız derleniyor ve Python çıktısıyla kararlar aynı. (5) Flash ve RAM kullanımı hem nesne hem bağlanmış imaj için ölçülmüş ve farkın nedeni açıklanmış. (6) Raporda sentetik verinin gerçek bir bataryayı temsil etmediği açıkça yazılı.

### Ek Alıştırmalar

Aşağıdaki problemler kademelidir. ★ olanlar kavramı yoklar, ★★ olanlar bir türetme ya da küçük bir hesap ister, ★★★ olanlar birden çok konuyu birleştirir. Mülakat etiketli olanlar klasik sorulardır.

1. ★ Pozitif sınıfı %2 olan bir veride her zaman negatif diyen modelin doğruluğu ve dengeli doğruluğu nedir? (Mülakat)
2. ★ `Σ (yᵢ − c)²`'yi en küçük yapan sabit `c`yi türevle bul. Bu sonuç, yalnızca sapmadan oluşan modelin neden ortalamayı tahmin ettiğini gösterir.
3. ★ Tek öznitelikli (sapmalı) OLS'te `b = Σ(xᵢ − x̄)(yᵢ − ȳ) / Σ(xᵢ − x̄)²` olduğunu normal denklemden türet.
4. ★ Tek öznitelikli regresyonda standart katsayının `β · σₓ / σ_y`, Pearson korelasyonuna eşit olduğunu göster.
5. ★★ Ridge'de `α → ∞` için katsayıların sıfıra, tahminin hedefin ortalamasına yaklaştığını neden beklersin? Bunu kapalı formdan göster. (Mülakat)
6. ★★ Lasso için `λ_maks = maks_j |zⱼᵀ(y − ȳ)| / n` formülünü, `w = 0` çözümünün optimalite koşulundan türet.
7. ★★ İki öznitelik tamamen aynıysa (`x₂ = x₁`) OLS'in normal denklemi neden tekildir? Ridge bu durumda tek bir çözüm verir mi ve katsayıları nasıl dağıtır? (Mülakat)
8. ★★ Sigmoid türevini `σ′ = σ(1 − σ)` kullanarak, lojistik kaybın gradyanının `(1/n) Aᵀ(p − y)` olduğunu göster.
9. ★★ Bir lojistik modelde `p = 0,5` olan bir nokta karar sınırındadır. Bu noktada kayıp gradyanının büyüklüğü neye bağlıdır ve neden?
10. ★★ Poisson regresyonunda log-olabilirlik gradyanının `Aᵀ(y − μ)` olduğunu `μ = exp(η)` ile göster. Bu gradyanın sıfıra eşitlenmesi ne anlama gelir?
11. ★★★ Huber kaybında `δ → 0` ve `δ → ∞` limitlerinde kaybın hangi bilinen kayıplara (MAE ve MSE) benzediğini açıkla. Gerçek bir veri için `δ`yı nasıl seçersin?
12. ★★★ Softmax'ta tüm sınıfların ağırlık vektörlerine aynı vektörü eklemek olasılıkları değiştirmez. L2 cezası bu serbestliği nasıl giderir? Sapmalar için aynı soru neden ayrı bir düşünce gerektirir? (Mülakat)

## Kod Okuma Egzersizi

Bu bölümde üç gerçek kaynak kesiti okuyacağız. İlki, scikit-learn 1.8.0 kurulumundaki `sklearn/linear_model/_ridge.py` dosyasından, Ridge'in çözücüsüdür (`_solve_cholesky`, satır 216–228). Kesit birebir kopyadır.

```python
def _solve_cholesky(X, y, alpha):
    # w = inv(X^t X + alpha*Id) * X.T y
    n_features = X.shape[1]
    n_targets = y.shape[1]

    A = safe_sparse_dot(X.T, X, dense_output=True)
    Xy = safe_sparse_dot(X.T, y, dense_output=True)

    one_alpha = np.array_equal(alpha, len(alpha) * [alpha[0]])

    if one_alpha:
        A.flat[:: n_features + 1] += alpha[0]
        return linalg.solve(A, Xy, assume_a="pos", overwrite_a=True).T
```

İkinci kesit, Lasso ve Elastic Net'in koordinat inişini yapan Cython çekirdeğinden (`sklearn/linear_model/_cd_fast.pyx`, satır 330–343) alındı. Döngünün bir `wⱼ` güncellemesi içeren kısmı budur. Uzun bir satır (satır 333) iki parçaya bölünmüştür; ifade değişmemiştir.

```python
                w_j = w[j]  # Store previous value

                # tmp = X[:,j] @ (R + w_j * X[:,j])
                tmp = (_dot(n_samples, &X[0, j], 1, &R[0], 1)
                       + w_j * norm2_cols_X[j])

                if positive and tmp < 0:
                    w[j] = 0.0
                else:
                    w[j] = (fsign(tmp) * fmax(fabs(tmp) - alpha, 0)
                            / (norm2_cols_X[j] + beta))

                if w[j] != w_j:
                    # R -= (w[j] - w_j) * X[:,j] # Update residual
                    _axpy(n_samples, w_j - w[j], &X[0, j], 1,
                          &R[0], 1)
```

Üçüncü ve son kesit, bu ölçeklemenin Python tarafındaki karşılığıdır (`sklearn/linear_model/_coordinate_descent.py`, satır 2744–2745). Scikit-learn kendi amaç fonksiyonunda `(1/(2n))` ile normalize eder, Cython çekirdeği ise normalize edilmemiş toplamla çalışır; bu iki satır aradaki çarpanı verir.

```python
        l1_reg = self.alpha * self.l1_ratio * n_samples
        l2_reg = self.alpha * (1.0 - self.l1_ratio) * n_samples
```

**Sorular — cevaplamadan geçme:**

1. `_solve_cholesky` `A = XᵀX`i açıkça oluşturuyor. Bölüm 58.2'de gördüğümüz gibi bu, koşul sayısını karesel büyütür. Sklearn neden yine de normal denklemi seçiyor? Bu seçimin yararını ve riskini, bu bölümdeki Ridge deneyine bağlayarak açıkla.
2. `A.flat[:: n_features + 1] += alpha[0]` satırı `αI` matrisini oluşturmadan köşegene ekleme yapar. Bu hilenin neden daha az bellek kullandığını açıkla ve `A`'nın köşegen indekslerinin bu dilimle nasıl seçildiğini bir `3×3` örnekle göster.
3. `linalg.solve(..., assume_a="pos")` ifadesi, matrisin pozitif tanımlı olduğunu varsayar. Ridge'de bu varsayımın neden her zaman geçerli olduğunu, OLS'te ise neden geçerli olmayabileceğini (tam rank değilse) açıkla.
4. Cython kesitinde `tmp = X[:,j]ᵀ(R + wⱼX[:,j])` ifadesi, Bölüm 58.8'deki `ρⱼ`nin normalize edilmemiş hâlidir. `R` artığının bu hesapta neden `wⱼ` katkısı eklenerek başlatıldığını açıkla.
5. `fsign(tmp) * fmax(fabs(tmp) - alpha, 0)` ifadesi yumuşak eşiklemedir. `alpha` yerine `0` konulursa ne olur? Bu bir OLS güncellemesi midir?
6. `if w[j] != w_j` koşulu artığı yalnızca katsayı değiştiğinde güncellemenin nedeni nedir? Bu bir performans kazancı mı, yoksa doğruluk için gerekli mi?
7. `l1_reg` ve `l2_reg` çarpanı `n_samples`tır. `alpha = 0,1` ve `n = 442` için Cython'a giden `l1_reg` değerini hesapla ve bunun `(1/(2n))` normalizasyonunu nasıl telafi ettiğini göster.

## Bölüm Özeti

- Doğrusal model, parametrelerinde doğrusal olan ve tahmini yorumlanabilir bir modeldir; baseline olarak her projede ilk adımdır.
- Kare kayıp minimizasyonu, Gauss gürültüsü varsayımı altında en büyük olabilirlik tahminidir. Normal denklem, QR ve SVD aynı çözümü verir; koşul sayısı normal denklemde karesel büyür.
- Gradyan inişi, öğrenme oranı kararlılığı için `2/L` koşuluna tabidir; ölçekleme koşul sayısını ve dolayısıyla yakınsama hızını doğrudan etkiler.
- Ridge (L2) koşul sayısını düzeltir ve çoklu doğrusallıkta katsayıları kararlı kılar; Lasso (L1) köşe çözümler nedeniyle seyrek katsayılar üretir. İkisi de MAP tahminleridir (Gauss ve Laplace önselleri).
- Düzenlileştirme gücü λ, ölçeklenmiş veride çapraz doğrulamayla seçilir ve test kümesi bir kez kullanılır.
- Lojistik regresyon, log-odds'u doğrusal kılar; kayıp konvekstir ve Newton/IRLS ile birkaç adımda çözülür. Ayrılabilir veride cezasız kayıp sınırsızdır; L2 cezası bunu önler.
- Softmax regresyonu çok sınıflı lojistik regresyondur; gradyanı `P − Y`dir ve OvR'den tutarlı biçimde iyi olabilir. Poisson gibi GLM'ler aynı çatı altında, farklı dağılım ve bağlantılarla çalışır.
- Doğrusal model eğitildikten sonra tek bir nokta çarpım ve bir eşikleme ile çalışır; ağırlıkların int8 kuantizasyonu bellek kullanımını dörtte bire indirir ve karar değişmeden kalabilir.
- Doğrusal modelin sınırı, öznitelik dönüşümü olmadan doğrusal olmayan sınırları çözememesidir (XOR); bunu çekirdekler, ağaçlar ve sinir ağları aşar.

**Sonraki bölümde:** Bölüm 59, Ağaçlar ve Ensemble Yöntemleri ile devam ediyor. Karar ağacını sıfırdan kuracak, bagging ve random forest'ı göreceksin; tablo verisinde doğrusal modellerin neden çoğu zaman geri kaldığını, bu bölümdeki XOR ve yarım ay örneklerinde gördüğümüz sınırın ağaçlarla nasıl aşıldığını ölçeceksin.

::: mulakat
1. Normal denklemi çözmek yerine neden QR veya SVD tercih edilir? Koşul sayısı ilişkisini kendi cümlelerinle açıkla.
2. Kare kayıbı minimize etmek hangi olasılıksal varsayımla eşdeğerdir ve bu varsayım bozulursa ne olur?
3. Ridge ve Lasso'nun kısıt geometrisi arasındaki fark nedir? Lasso neden tam sıfır katsayı üretir, Ridge neden üretmez?
4. Lojistik regresyonda bir katsayı 0,7 ise bu sonuç bir öznitelik artışı için odds'u nasıl değiştirir? Olasılık neden aynı oranda değişmez?
5. Ayrılabilir veride lojistik regresyonun cezasız çözümü neden yoktur? L2 cezası bu sorunu nasıl çözer?
6. Çok sınıflı sınıflandırmada OvR ile softmax arasındaki fark nedir? Hangisi olasılıkları birlikte tutarlı kılar?
7. Poisson regresyonunda dispersiyon ne demektir? Marjinal varyans ile koşullu dispersiyon arasındaki farkı neden ayırt etmelisin?
8. Standardizasyon Ridge'in çözümünü neden değiştirir ve intercept neden cezalandırılmaz?
:::
