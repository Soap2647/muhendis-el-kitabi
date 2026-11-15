
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

@@CIKTI python hesap_grafi.py out_hesap_grafi.txt

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

@@KOD matris_turev.py:def ornek3

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

@@KOD birikim.py:def calistir

@@CIKTI python birikim.py out_birikim.txt

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

@@DOSYA micrograd_engine.py:2-10

Toplama işlemi, bizim `__add__` metodumuzla birebir eşdeğerdir. Geri adım her iki girdiye de çıkışın gradyanını ekler.

@@DOSYA micrograd_engine.py:13-22

Çarpma da aynı kalıbı izler. Her girdinin yerel türevi, diğer girdinin değeridir.

@@DOSYA micrograd_engine.py:24-33

Geri geçişin asıl kısmı aşağıdadır. 34-53. satırlar (üs ve relu) atlanmıştır; 54. satırdan itibaren `backward` metodunun topolojik sıralama bölümü alınmıştır.

@@DOSYA micrograd_engine.py:54-65

Son üç satır çıkışın gradyanını 1 yapar ve düğümleri ters sırada çalıştırır. 67. satırdaki yorum atlanmıştır; kalan kod birebirdir.

@@DOSYA micrograd_engine.py:68-70

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
