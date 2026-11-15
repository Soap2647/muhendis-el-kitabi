%% kisim_no: XV
%% kisim_ad: Derin Öğrenme
%% bolum_no: 64
%% baslik: Eğitimin Sanatı

## Giriş: Model kurmak kadar eğitmek de bir sanattır

Bölüm 63'te bir sinir ağının nasıl ileri hesaplandığını, kaybın nasıl geri yayıldığını ve yalın gradyan inişinin neden işe yaradığını gördün. Orada ağı eğitmek, öğrenme oranını bir sayı olarak seçip döngüyü çalıştırmaktan ibaretti. Gerçek projede bu yeterli değil. Aynı ağ bir koşuda %97 doğruluğa çıkarken başka bir koşuda hiç öğrenmez; aynı kodu iki kez çalıştırdığında sonuç değişir; daha büyük bir batch kullandığında kayıp düşmek yerine salınır. Eğitim, bu nedenle bir kod yazma işinden çok bir deney yapma işidir.

Savunma sanayiinde bu fark somut bir maliyete dönüşür. Bir İHA'nın hedef tanıma modeli haftalarca eğitilir, sonra bir yazılım sürümünde yeniden eğitilir. Eğitim koşusu pahalıdır, GPU saati ve mühendis zamanı harcanır. Kötü giden bir koşuyu hızlıca teşhis edebilmek ve doğru değişikliği yapabilmek, bu sürecin en değerli becerisidir. Mert'in EV Dashboard projesinde bir sinir ağı batarya hücrelerinin sıcaklık örüntüsünü öğreniyorsa, aynı disiplin tek bir hücrenin neden yanlış tahmin edildiğini bulmak için de gerekir.

Bu bölümün iddiası şudur: iyi bir eğitim, birkaç iyi seçilmiş tekniğin bilinçli bir kombinasyonudur ve her tekniğin ne işe yaradığını ölçerek görebilirsin. Önce optimizasyon algoritmalarını (momentum, Adam, AdamW) ve öğrenme oranı takvimlerini ele alacağız. Sonra başlatmanın (initialization) derin ağlardaki önemini, normalizasyonu (BatchNorm, LayerNorm) ve düzenlileştirmeyi (dropout, ağırlık azaltma, etiket yumuşatma, erken durdurma) göreceğiz. Bölümün kalbi ise eğitim hatası ayıklamadır: loss eğrisine bakarak teşhis koymak, tek bir batch'e aşırı uydurarak kodu sınamak ve kasıtlı hatalarla kendi kendini kontrol etmek.

Bu bölümdeki sayısal iddialar ölçümle desteklenir; ölçmediğimiz yerleri metinde açıkça belirtiyoruz. Veri olarak scikit-learn'ün `load_digits` kümesini kullandık (1797 örnek, 64 özellik, 10 sınıf). Veri her deneyde aynı şekilde %60 eğitim, %20 doğrulama ve %20 test olarak bölündü. Test kümesi, hiçbir karar için kullanılmadı; her karşılaştırma beş tohumla (seed) yapıldı ve sonuçlar ortalama ± sapma olarak verildi. Sayılar tek bir koşuya değil, bu tekrarlara dayanır.

::: not
Bu bölümde PyTorch'u bir ölçüm aracı olarak kullandık, öğretici bir çerçeve olarak değil. Tensörler, autograd ve `nn.Module` ayrıntıları Bölüm 65'in konusu. Burada `torch.optim` ve `torch.nn` yapılarını, yazdığımız NumPy kodunun doğru olduğunu sınamak için kullandık. Eğitim deneylerinin hepsi CPU üzerinde ve sabit tohumla yapıldı; böylece sonuçlar yeniden üretilebilir. GPU ölçümleri Bölüm 65 ve 76'da ele alınacak.
:::

## 64.1 Eğitim bir deney disiplinidir

Bir sinir ağını eğitirken her değişiklik birden fazla şeyi aynı anda etkiler. Öğrenme oranını değiştirdiğinde, aynı zamanda adım büyüklüğünü, gürültü düzeyini ve nihai kararlılığı değiştirirsin. Bu yüzden eğitim, bilimsel bir deney gibi yürütülmelidir: bir kerede tek bir şey değiştir, ölç, tekrar et.

Üç kural bu disiplinin omurgasıdır. Birincisi **tek değişken**: karşılaştırdığın iki koşu yalnızca incelediğin faktörde farklı olmalı. İkincisi **tohum**: sinir ağının başlangıç ağırlıkları ve mini-batch sırası rastgeledir. Tek bir koşudan elde edilen "bu daha iyi" yargısı, tohumun şansı olabilir. Üçüncüsü **ayrı test kümesi**: karar verirken kullandığın ölçü, son raporlanan ölçüden farklı bir veriden gelmeli. Bölüm 57'de gördüğümüz gibi, hiperparametreyi test kümesinde seçersen test skoru artık tarafsız bir tahmin olmaz.

Bu bölümdeki deneylerin hepsinde bu kurallara uyduk. Veri üç parçaya ayrıldı; tohumlar 0'dan 4'e kadar beşer koşu yapıldı; öğrenme oranı seçimleri yalnızca doğrulama kümesinde, ayrı tohumlarla yapıldı. Test kümesi en sonda, seçilen modele bir kez uygulandı.

Eğitimin ilk kontrolü de bir disiplin meselesidir. Her sınıflandırma ağı eğitime başlamadan önce bir beklenen başlangıç kaybına sahiptir. Eğer ağ her sınıfa eşit olasılık veriyorsa, çapraz entropi kaybı ln C olur (Bölüm 51). `C = 10` için bu 2,302585'tir. Başlangıç kaybın bu değerden çok uzaksa, ağın çıkış katmanında ya da veri etiketlerinde bir sorun vardır. Bu kontrolü bölümün sonunda, eğitim hatası ayıklamada tekrar kullanacağız.

## 64.2 Mini-batch, gradyan gürültüsü ve batch boyutu

Bölümdeki tüm deneyler, veri ve eğitim döngüsü için aynı küçük altyapıyı kullanır. Bu dosya ilk deneyden önce verilir: veri bölmesi, MLP kurucu, eğitim döngüsü ve kayıt yardımcıları. Dosyanın başındaki `VERI` yolu, deney çıktılarının yazıldığı klasördür; okur kendi bilgisayarında bu yolu değiştirebilir.

{{KOD|ortak64.py|^|torch.set_num_threads(1)}}
{{KOD|ortak64.py|def veri|return (t(Xtr), t(ytr), t(Xva), t(yva), t(Xte), t(yte))}}
{{KOD|ortak64.py|def mlp|return nn.Sequential(*kat)}}
{{KOD|ortak64.py|@torch.no_grad()|<def egit(}}
{{KOD|ortak64.py|def egit|<    for ep in range(epochs):}}
{{KOD|ortak64.py|    for ep in range(epochs):|<    _, h[}}
{{KOD|ortak64.py|    _, h[|return h}}
{{KOD|ortak64.py|def csv_yaz|return yol}}
{{KOD|ortak64.py|def ortalama_sapma|return a.mean()}}


Bölüm 50'de gradyan inişinin tam veriyle hesaplanan gradyanla ve stokastik (SGD) biçimiyle nasıl farklılaştığını gördük. Tam gradyan, tüm eğitim kümesinin ortalamasıdır. Her adımda bu ortalamayı hesaplamak pahalıdır. Mini-batch SGD, veriden rastgele bir alt küme seçer ve gradyanı yalnızca o alt küme üzerinden hesaplar. Bu tahmin gürültülüdür, ama her adım çok daha ucuzdur.

Gürültünün büyüklüğü batch boyutuna bağlıdır. Tam gradyanı g, batch gradyanını g_b ile gösterelim. Rastgele bir batch'in beklenen kareli hatası kabaca şöyle davranır:

E‖g_b − g‖² ≈ (σ²/b) · (1 − b/N)

Burada σ² tek bir örneğin gradyanının varyansı, b batch boyutu, N ise veri kümesi büyüklüğüdür. Çarpan (1 − b/N), örnekleme sırasında veri kümesi tükendikçe gürültünün azalmasını anlatan sonlu popülasyon düzeltmesidir. Gürültü, batch büyüdükçe ters orantılı olarak düşer. Batch'i 4 kat büyütmek gürültüyü kabaca 4 kat azaltır; ama aynı epoch için yapılan adım sayısı da 4 kat düşer.

Aşağıdaki betik iki ölçümü birlikte yapar. Birinci bölümde başlangıç ağırlıklarında tek bir ağın gradyanını hesaplar ve 300 rastgele batch için tam gradyandan sapmayı ölçer. İkinci bölümde 30 epoch boyunca sabit ve doğrusal ölçekli öğrenme oranlarıyla beş tohumlu eğitimleri tekrarlar. Sonuçlar aşağıdaki tablolarda ve Şekil 64.1'de özetlenir.

{{KOD|t01_batch.py|^|<def grad_vec}}
{{KOD|t01_batch.py|@|<# (b)}}
{{KOD|t01_batch.py|@|$}}
{{CIKTI|t01_batch.py|out_t01_batch.txt}}

Bunu ölçmek için ağı başlangıç ağırlıklarında tuttuk ve 300 rastgele batch üzerinde tam gradyandan sapmayı hesapladık. Sonuçlar teoriyle uyumludur:

| Batch boyutu | E‖g_b − g‖² (ölçüm) | Oran (8'e göre) | Teorik oran |
|---|---|---|---|
| 8 | 0,386054 | 1,000 | 1,000 |
| 32 | 0,091766 | 0,238 | 0,246 |
| 128 | 0,020654 | 0,054 | 0,055 |
| 512 | 0,003085 | 0,008 | 0,013 |

Teorik oran, (1/b − 1/N) farkının 8'e göre oranından hesaplanmıştır; N = 1078 eğitim örneği. Ölçüm ile teori arasındaki küçük fark, 300 tekrarın istatistiksel dalgalanmasından gelir.

Bu gürültü neden önemlidir? Küçük batch'te gürültü, optimizasyonu bir düzenlileştirme gibi de etkiler: gradyan rastgele salındığı için ağ dar ve keskin bir minimumdan çıkıp daha geniş bir çukura geçebilir. Bu sezgi, büyük batch'in test performansını neden düşürebildiğini kısmen açıklar. Ama asıl pratik sonuç daha basittir: batch boyutu ve öğrenme oranı birlikte seçilmelidir. Aşağıdaki deneyde sabit bir öğrenme oranıyla (0,1) ve doğrusal ölçekli bir öğrenme oranıyla (0,1 · b/32) batch boyutunu değiştirdik. Her koşu 30 epoch sürdü ve beş tohumla yapıldı.

| Mod | Batch | Adım sayısı | Test doğruluğu (ortalama ± sapma) |
|---|---|---|---|
| Sabit lr = 0,1 | 8 | 4050 | 0,9767 ± 0,0032 |
| Sabit lr = 0,1 | 32 | 1020 | 0,9633 ± 0,0036 |
| Sabit lr = 0,1 | 128 | 270 | 0,9356 ± 0,0036 |
| Sabit lr = 0,1 | 512 | 90 | 0,7744 ± 0,0865 |
| Doğrusal ölçek | 8 | 4050 | 0,9656 ± 0,0058 |
| Doğrusal ölçek | 32 | 1020 | 0,9633 ± 0,0036 |
| Doğrusal ölçek | 128 | 270 | 0,9672 ± 0,0063 |
| Doğrusal ölçek | 512 | 90 | 0,1639 ± 0,0844 |

Tablo üç şeyi gösteriyor. Sabit öğrenme oranıyla batch büyüdükçe adım sayısı düşer ve 512'lik batch'te model 90 adımda yetersiz kalır. Doğrusal ölçekleme, 128'e kadar işe yarar ve 270 adımda 0,967'ye ulaşır. Ama 512 batch ile öğrenme oranı 1,6'ya çıktığında model çöker: 0,16 doğruluk şans düzeyine yakındır. Yani "batch'i büyüt, öğrenme oranını orantılı artır" kuralı sonsuza kadar geçerli değildir; öğrenme oranının da bir kararlılık sınırı vardır. Bu sınır, gradyan inişinin kararlılık koşulunu hatırlatır (Bölüm 50). Büyük batch'lerde öğrenme oranını artırmak için ısınma (warmup) kullanılır; bunu 64.5'te ele alacağız.

Şekil 64.1, gürültünün batch boyutuyla düşüşünü ve iki öğrenme oranı stratejisinin davranışını birlikte gösteriyor.

![Şekil 64.1: Sol: gradyan gürültüsü batch boyutuyla ters orantılı azalır. Sağ: batch büyüdükçe sabit ve doğrusal ölçekli öğrenme oranlarının farkı.](gorseller/b64_gurultu_batch.png)

## 64.3 Momentum, Nesterov, AdaGrad, RMSProp ve Adam

Gradyan inişinin sorunu, kötü koşullu yüzeylerde zikzak çizmesidir. Bölüm 50'de gördüğümüz gibi, eğrilik bir yönde büyük, başka bir yönde küçük olduğunda tek bir öğrenme oranı ya dik yönde salındırır ya da düz yönde çok yavaş ilerletir. Bu sorunu çözmek için iki temel fikir geliştirildi: geçmiş adımların bir kısmını hatırlamak (momentum) ve her parametre için öğrenme oranını ayrı ayarlamak (uyarlamalı yöntemler).

**Momentum**, hızın (v) bir sönümlü birikim olmasını önerir. Her adımda hız, gradyanın kendisine ve bir önceki hızın μ katına göre güncellenir; parametre bu hızla hareket eder:

v ← μv + g
θ ← θ − η · v

Dik yönde gradyan işaret değiştirdiği için hız bu salınımları birbirini sönümleyerek azaltır; düz yönde ise gradyan hep aynı işaretteyse hız birikir ve ilerleme hızlanır. μ genelde 0,9 alınır. **Nesterov**, gradyanı mevcut konumda değil, hızın gösterdiği yeni konumda hesaplamayı önerir. Pratikte PyTorch'un kullandığı biçim, güncellemede gradyanı biraz öne çekerek uygular:

v ← μv + g
θ ← θ − η · (g + μv)

Sıfırdan yazdığımız optimizasyon güncellemeleri `egitim_np.py` dosyasındadır. Dosyanın başı ile momentum ve Nesterov güncellemeleri aşağıdadır:

{{KOD|egitim_np.py|^|return theta - lr * (g + mu * v), v}}

**AdaGrad** her parametrenin geçmiş gradyan karelerini toplar ve öğrenme oranını bu toplamın karekökü ile böler. Sık değişen parametreler yavaşlar, nadir değişenler hızlanır. Toplam sürekli büyüdüğü için öğrenme oranı zamanla sıfıra yaklaşır; bu bir avantaj gibi görünse de derin ağlarda erken durmaya neden olabilir. **RMSProp**, toplamı üstel bir ortalamayla değiştirerek bu sorunu giderir: geçmiş kareler hızla unutulur.

**Adam** (Kingma ve Ba, 2014), momentumu ve RMSProp'un uyarlamasını birleştirir. İki hareketli ortalama tutar: birinci moment m (gradyanın ortalaması, yani momentum) ve ikinci moment v (gradyan karesinin ortalaması). Güncelleme şöyledir:

m ← β₁m + (1 − β₁)g
v ← β₂v + (1 − β₂)g²
m̂ = m / (1 − β₁ᵗ),   v̂ = v / (1 − β₂ᵗ)
θ ← θ − η · m̂ / (√v̂ + ε)

Burada β₁ = 0,9, β₂ = 0,999 ve ε = 10⁻⁸ tipik değerlerdir. Dikkat edilmesi gereken bölüm, m̂ ve v̂ ile yapılan **sapma düzeltmesidir** (bias correction). m ve v sıfır ile başlatılır. İlk adımlarda hareketli ortalama, gerçek gradyan ortalamasına değil, sıfıra doğru çekilmiş bir değere yaklaşır. Düzeltme olmadan, ilk birkaç yüz adımda v küçük kalır ve adım boyu gereğinden büyük olur. Düzeltme, 1 − β₂ᵗ paydasıyla bu sıfıra çekilmeyi telafi eder. t büyüdükçe 1 − β₂ᵗ → 1 olduğu için düzeltme kendiliğinden kaybolur.

Bunu elle görmek için tek parametreli bir örneği ele alalım: θ₀ = 1,0, η = 0,1 ve gradyan dizisi 0,5, −0,2, 0,1. Aşağıdaki program Adam'ın ilk üç adımını NumPy ile hesaplar. Program `egitim_np.py` dosyasındaki `adam_adim` fonksiyonunu kullanır ve bu fonksiyonun tam kodu bölümün sonunda Kod Okuma kısmında PyTorch'un kendi kaynağıyla karşılaştırılır.

Aşağıdaki kod Adam'ın tek adımını tanımlar. Sapma düzeltmesi, güncellemeden önce m ve v'nin ayrı ayrı bölünmesiyle yapılır:

{{KOD|egitim_np.py|def adam_adim|return theta, m, v, t}}

Aşağıdaki program aynı fonksiyonu üç adım boyunca çağırır ve ara değerleri yazdırır. Böylece her satırı elle kontrol edebilirsin:

{{KOD|adam_iz.py|^|$}}

Program şu çıktıyı verir:

{{CIKTI|adam_iz.py|out_adam_iz.txt}}

İlk adımda sapma düzeltmesi tam olarak gradyanı verir: m̂ = 0,5 ve v̂ = 0,25 (yani √v̂ = 0,5). Güncelleme 0,1 · 0,5/0,5 = 0,1 kadar yapılır ve θ 0,9 olur. Bu, Adam'ın her parametreyi kabaca η büyüklüğünde hareket ettirdiğini gösterir; adım gradyanın mutlak büyüklüğünden bağımsızdır. Bu özellik, ölçeği farklı parametreler arasında Adam'ı güçlü kılar; ama aynı zamanda Adam'ın, kaybın ölçeğine karşı SGD kadar duyarlı olmadığı anlamına gelir. Üçüncü satırda gradyan işaret değiştirdiğinde m küçülür ve adım yönü dengelenir.

**AdamW** (Loshchilov ve Hutter, 2019; genel bilgi) bir ince ama önemli ayrıntıyı düzeltir. Adam'da ağırlık azaltma (weight decay) genellikle L2 düzenlileştirme olarak uygulanır: gradyana λθ eklenir. Adam'ın uyarlamalı ölçeği bu eklenen terimi de normalize ettiği için, büyük gradyanlı parametrelerde azaltma etkisi zayıflar. AdamW ise azaltmayı gradyandan ayırır ve doğrudan ağırlığa uygular: θ ← θ(1 − ηλ), ardından normal Adam adımı atılır. Farkı PyTorch kaynağında görebilirsin (Kod Okuma bölümünde). Aşağıdaki kod her iki biçimi yan yana tanımlar:

{{KOD|egitim_np.py|def adamw_adim|return adam_adim(theta, g, m, v, t, lr, b1, b2, eps)#2}}

Bu iki fonksiyonun ayrımını test etmek için PyTorch'un `torch.optim.AdamW` ve `torch.optim.Adam(weight_decay=...)` sınıflarıyla karşılaştırdık. Sayısal fark makine hassasiyeti düzeyinde kaldı (en fazla 2,2 × 10⁻¹⁶), yani NumPy gerçeklemesi PyTorch ile aynı güncellemeyi yapıyor. Momentum ve Nesterov için de aynı test yapıldı ve fark sıfır çıktı.

Bu bölümde kullandığımız NumPy kodunun tamamı (`egitim_np.py`) ve PyTorch ile eşleşme testi (`test_np64.py`, 19 kontrol) 64.12'de verilmiştir. Tüm kontroller geçti: Adam, AdamW, momentum, BatchNorm ileri ve geri geçişi, dropout, zamanlayıcılar ve gradyan kırpma PyTorch ile eşleşti; BatchNorm'un gradyanı sayısal fark ile de doğrulandı (en büyük fark 1,4 × 10⁻⁹).

## 64.4 Optimizer karşılaştırması: aynı ağ, aynı veri, adil bir seçim

Hangi optimizer'ın daha iyi olduğu sorusu, öğrenme oranı seçimi yapılmadan cevaplanamaz. Her optimizer'ın kendi kararlılık aralığı vardır. Adil bir karşılaştırma, her optimizer'a kendi öğrenme oranı ızgarasını (1e-4'ten 1e-1'e) tanır ve en iyi lr'yi yalnızca doğrulama kümesinde seçer. Seçim için ayrı üç tohum (10, 11, 12) kullanıldı. Sonra seçilen lr ile beş tohumla test ölçüldü. Test kümesi seçim sürecinde hiç kullanılmadı.

Ağ iki gizli katmanlı (128 birim, ReLU) bir MLP'dir; eğitim 30 epoch ve batch 32 ile yapıldı. Sonuçlar aşağıda:

Optimizer karşılaştırmasını yapan betik aşağıdadır. Önce her optimizer için yedi öğrenme oranı yalnızca doğrulama kümesinde (tohum 10–12) denenir; sonra seçilen lr ile test kümesi beş tohumda (0–4) ölçülür.

{{KOD|t02_optim.py|^|<for ad in OPT:}}
{{KOD|t02_optim.py|@|<print("\nAdim 2}}
{{KOD|t02_optim.py|print("\nAdim 2|$}}
{{CIKTI|t02_optim.py|out_t02_optim.txt}}

| Optimizer | Seçilen lr | Doğrulama (seçim) | Test (5 tohum) |
|---|---|---|---|
| SGD | 0,1 | 0,9712 | 0,9633 ± 0,0036 |
| Momentum (0,9) | 0,1 | 0,9814 | 0,9767 ± 0,0042 |
| Nesterov (0,9) | 0,1 | 0,9814 | 0,9767 ± 0,0025 |
| AdaGrad | 0,03 | 0,9777 | 0,9789 ± 0,0015 |
| RMSProp | 0,001 | 0,9814 | 0,9611 ± 0,0252 |
| Adam | 0,003 | 0,9842 | 0,9739 ± 0,0025 |
| AdamW (wd 0,01) | 0,003 | 0,9851 | 0,9744 ± 0,0030 |

Tablodan üç sonuç çıkıyor. Birincisi, bu küçük MLP ve veri kümesinde optimizer farkları küçüktür: en iyi (AdaGrad, 0,9789) ile en kötü ortalama (RMSProp, 0,9611) arasındaki fark yaklaşık %2'dir. Ama RMSProp'un sapması (± 0,0252) çok büyük: beş tohumdan birinin belirgin biçimde düşük olduğunu gösteriyor (bu tohumun neden düşük kaldığını incelemedik). Yani tek bir tohumla "RMSProp kötüdür" ya da "AdaGrad en iyidir" demek yanıltıcı olurdu. İkincisi, doğrulamada en yüksek skoru veren AdamW, testte de Adam'dan biraz yüksek çıktı; ama bu fark sapmalar içinde kalıyor. Üçüncüsü ve en önemlisi, seçim sırasında kullanılan doğrulama skoru ile test skoru arasında sıralama her zaman aynı değil; bu da küçük kümelerde karşılaştırmanın kendisinin ne kadar gürültülü olduğunu gösterir.

Yörüngeleri üreten betik aşağıdadır. Aynı başlangıç noktasından üç optimizer 60 adım yürütülür; her adımın konumu ve kaybı CSV dosyasına yazılır. Şekil 64.2 bu dosyadan çizilmiştir.

{{KOD|t03a_yorunge.py|^|<satir = []}}
{{KOD|t03a_yorunge.py|satir = []|$}}
{{CIKTI|t03a_yorunge.py|out_t03a_yorunge.txt}}

Şekil 64.2, aynı deneyin yörüngelerini ayrı bir kayıp yüzeyinde gösteriyor. Kayıp f(x, y) = ½(x² + 10y²) gibi kötü koşullu bir ikinci dereceden fonksiyondur. Üç optimizer aynı başlangıç noktasından (−4, 1) başlar. SGD ve momentum için öğrenme oranı 0,09, Adam için 0,3 seçildi.

![Şekil 64.2: Sol: üç optimizerin kötü koşullu bir kayıp yüzeyindeki yörüngeleri. Sağ: adım adım kayıp (log ölçek).](gorseller/b64_yorunge.png)

Şekil 64.2'de SGD, dik yönde salınmadan ama yavaş ilerliyor ve 60 adımda f ≈ 10⁻⁴ düzeyine iniyor. Momentum aynı öğrenme oranında daha hızlı yön değiştiriyor ama dik yönde salınıyor; 60 adımda kayıp daha yüksek kalıyor. Bu, momentumun her zaman hız kazandırmadığını, öğrenme oranıyla birlikte ayarlanması gerektiğini gösteriyor. Adam'ın yörüngesi adım büyüklüğünü gradyan ölçeğinden bağımsız tuttuğu için düz eksende de dik eksende de benzer hızla ilerliyor.

Şekil 64.3, beş tohumun doğrulama eğrilerini ve son değerleri gösteriyor. Eğrilerin gölgeli bantları ortalamanın ± bir standart sapmasını gösterir.

![Şekil 64.3: Sol: optimizer başına doğrulama doğruluğu eğrileri (5 tohum, ortalama ± sapma). Sağ: son epoch doğrulama doğruluğu.](gorseller/b64_optim_egri.png)

Eğriler, SGD'nin yaklaşık 15. epoch'a kadar geride kaldığını gösteriyor. Adam ve AdamW'nin erken yakınsaması, uyarlamalı ölçeğin ilk adımlarda öğrenme oranını etkin biçimde yükseltmesinden gelir. Ama eğriler 25. epoch'tan sonra neredeyse düzleşiyor: bu veri kümesinde optimizer seçimi, doğru öğrenme oranıyla karşılaştırıldığında, nihai doğruluğu fazla değiştirmiyor. Büyük ve zor görev ve modellerde bu tablo farklı olabilir; bu yüzden bir optimizer'ı varsayılan olarak seçmek yerine her projede kendi ızgarasıyla karşılaştırmak gerekir.

## 64.5 Öğrenme oranı: en önemli hiperparametre ve zamanlayıcılar

Öğrenme oranı (η), eğitimin en hassas hiperparametresidir. Bu bölümdeki deneylerde de en büyük etkiyi o gösterdi: SGD ile 0,0001 kullanıldığında kayıp neredeyse hiç düşmedi (B vakası, 64.10'da), 2,0 kullanıldığında ise ağ tamamen çöktü. Bölüm 63'te gördüğümüz gibi, öğrenme oranı 2,0 iken 64 gizli birimden 63'ü ölüyordu; ReLU birimi bir kez negatif tarafa itilirse gradyanı sıfır olur ve bir daha öğrenmez.

Bu nedenle öğrenme oranını rastgele seçmek yerine ölçmek gerekir. Bunun bir yolu **LR aralık testi**dir (Smith, genel bilgi). Öğrenme oranını çok küçük bir değerden (10⁻⁷) çok büyük bir değere (10) doğru her adımda üstel olarak artırırsın ve kaybı izlersin. Kayıp başlangıçta yavaş düşer, sonra bir noktadan sonra hızla artar. Kaybın en hızlı düştüğü veya en düşük olduğu bölge, kullanılabilir öğrenme oranlarının üst sınırını verir; pratik öneri bu değerin 10 kat altıdır.

LR aralık testini yapan betik aşağıdadır. Öğrenme oranı her adımda çarpanla artırılır ve kayıp izlenir.

{{KOD|t03b_lr_aralik.py|^|<# ---- (b)}}
{{KOD|t03b_lr_aralik.py|# ---- (b)|$}}
{{CIKTI|t03b_lr_aralik.py|out_t03b_lr_aralik.txt}}

Aşağıdaki deney, 0,9 momentumlu SGD ile batch 64 kullanarak 264 adımlık bir aralık taraması yaptı. Öğrenme oranı 10⁻⁷'den 10'a kadar her adımda çarpanla artırıldı. Taramanın özeti: en düşük düzeltilmiş EMA kaybı lr = 0,665 (kayıp 1,5565) noktasında görüldü; önerilen değer 0,0665'tir. Son adımlarda lr ≈ 1,09 iken kayıp 42,7'ye çıktı. Bu tek koşuda en düşük kayıp 0,66 civarında görüldü ve öneri 0,066 oldu. Bu değer, 0,9 momentumlu SGD için makul bir aralıktadır; ama tek bir koşu gürültülüdür, çünkü her öğrenme oranı yalnızca bir mini-batch ile denenir. Bu yüzden öneriyi bir başlangıç noktası olarak kullan ve kısa bir ızgara ile doğrula. Şekil 64.4, taramadaki EMA kaybını ve önerilen değeri gösteriyor.

![Şekil 64.4: LR aralık testi: öğrenme oranına karşı düzeltilmiş EMA kaybı. En düşük nokta ile önerilen değer (÷10) işaretlendi.](gorseller/b64_lr_aralik.png)

**Zamanlayıcılar (schedules).** Sabit bir öğrenme oranı eğitimin başında büyük adım atıp sonda gürültü yapmak zorunda kalır. Bu yüzden eğitim boyunca öğrenme oranını değiştiririz. En yaygın üç takvim şunlardır. **Basamaklı (step)** takvim, belirli aralıklarla öğrenme oranını bir katsayıyla çarpar. **Üstel (exponential)** takvim, her adımda sabit bir oranla küçültür. **Kosinüs (cosine)** takvim, öğrenme oranını bir kosinüs eğrisiyle maksimumdan minimuma indirir:

η(t) = η_min + ½(η_max − η_min)(1 + cos(πt/T))

Kosinüs takvimi, başta ve sonda yavaş, ortada hızlı değişir. Bu, eğitimin başında geniş bir alanı tarayıp sonda dar bir çukurun dibine inmeye karşılık gelir. Aşağıdaki kod üç takvimi ve ısınma (warmup) ile kosinüsü tanımlar:

{{KOD|egitim_np.py|def lr_adim_kurali|return lr_kosinus(t - W, T - W, lr_max, lr_min)}}

Bu fonksiyonlar PyTorch'un `StepLR`, `ExponentialLR` ve `CosineAnnealingLR` zamanlayıcılarıyla birebir eşleşti (en büyük fark 5 × 10⁻¹⁸). Isınma ve kosinüsü birleştiren `lr_isinma_kosinus` ise bizim tanımımızdır; ilk W adımda öğrenme oranı 0'dan η_max'a doğrusal çıkar, sonra kosinüs başlar.

Takvim şekillerini, takvim karşılaştırmasını ve derin ağ deneyini üreten betik aşağıdadır. İlk bölüm 300 adımlık takvim dizilerini yazar ve kosinüs takvimini PyTorch ile karşılaştırır; ikinci bölüm MLP üzerinde üç takvimi beş tohumla eğitir; üçüncü bölüm 12 katmanlı ağda ısınmanın etkisini ölçer.

{{KOD|t04_takvim.py|^|<# Torch karsilastirmasi}}
{{KOD|t04_takvim.py|# Torch karsilastirmasi|<# (b) Sig}}
{{KOD|t04_takvim.py|# (b) Sig|<# (c) Derin}}
{{KOD|t04_takvim.py|@|<satir = []}}
{{KOD|t04_takvim.py|@|$}}
{{CIKTI|t04_takvim.py|out_t04_takvim.txt}}

Şekil 64.5 sol üstte dört takvimi, sağ üstte üç takvimle eğitilmiş MLP'nin test doğruluğunu gösteriyor. Sağ altta ise bir derin ağın ısınma ile ve ısınmadan eğitim kaybını görüyorsun.

![Şekil 64.5: Sol üst: takvim şekilleri (η_max = 0,01, 300 adım). Sağ üst: MLP, Adam, test doğruluğu (5 tohum). Sol alt: 12 katmanlı ağda ısınmanın ilk üç epoch tepe kaybı ve son kayba etkisi. Sağ alt: okuma notu.](gorseller/b64_takvimler.png)

MLP deneyinde sabit öğrenme oranı (10⁻³) 0,9728 ± 0,0046, kosinüs (η_max = 0,003) 0,9761 ± 0,0015 ve ısınma + kosinüs 0,9767 ± 0,0015 test doğruluğu verdi. Fark küçük ama sapmalara göre tutarlı: takvim, sabit öğrenme oranından yaklaşık 0,3 ile 0,4 puan iyi, ama bu veri kümesinde kazanç kendi başına büyük değil.

**Neden ısınma (warmup)?** Derin ve büyük ağlarda, eğitimin ilk adımlarında Adam'ın ikinci moment tahmini v̂ henüz güvenilir değildir; sadece birkaç gradyan karesinin ortalamasıdır. Bu durumda büyük bir öğrenme oranı, tahmin dengelenmeden büyük adımlar atar ve ağı kararsız bir bölgeye iter. Isınma, ilk adımlarda öğrenme oranını küçük tutarak tahminin oturmasına izin verir. Bölüm 50'de gördüğümüz gibi, büyük modellerde kararlılık sınırı daha dardır; bu yüzden ısınma neredeyse standart bir bileşen hâline gelmiştir.

Derin ağ deneyinde bu etki açıkça görülüyor. 12 gizli katmanlı, BatchNorm'suz bir ReLU ağını Adam ile η = 0,01 kullanarak 10 epoch (yaklaşık 340 adım) eğittik. Isınma kullanılmadığında ilk üç epoch'un en yüksek kaybı 2,309 oldu (ağ öğrenmeye hiç başlayamadı), son eğitim kaybı 1,669 ve test doğruluğu 0,346 kaldı. 200 adımlık ısınma ile son eğitim kaybı 1,207 ve test 0,452 oldu. Her iki koşu da zayıf: bu ağ için η = 0,01 zaten büyük. Ama karşılaştırma yönü açık: ısınma, aynı öğrenme oranında daha kararlı bir başlangıç sağlar.

## 64.6 Başlatma (initialization): sinyal derin ağda nerede kayboluyor?

Bölüm 63'te ağırlıkların rastgele ama uygun ölçekte başlatılması gerektiğini ve bunun için Xavier ve He başlatma sezgisini gördük. Burada aynı fikri derin bir ağda ölçüyoruz. Ağ 20 gizli katmandan oluşuyor (her biri 256 birim, ReLU). Girdi olarak 512 eğitim örneği kullandık ve her katmanın aktivasyonlarının standart sapmasını (ileri geçiş) ve ağırlık gradyanlarının normunu (geri geçiş) ölçtük.

Başlatma deneyini yapan betik aşağıdadır. İlk bölüm, her katmanın aktivasyon standart sapmasını ve ağırlık gradyan normunu ölçer; ikinci bölüm dört başlatma yöntemini 20 epoch eğitir.

{{KOD|t05_baslatma.py|^|<def ag(}}
{{KOD|t05_baslatma.py|@|<def olc(}}
{{KOD|t05_baslatma.py|@|<satir = []}}
{{KOD|t05_baslatma.py|@|<print("\nEgitim}}
{{KOD|t05_baslatma.py|print("\nEgitim|$}}
{{CIKTI|t05_baslatma.py|out_t05_baslatma.txt}}

Dört başlatma biçimi karşılaştırıldı: küçük sabit std (0,01), Xavier (Glorot) normal, He normal ve He + BatchNorm. Aşağıdaki tablo üç katmandaki değerleri veriyor:

| Başlatma | Aktivasyon std (1. / 10. / 20. katman) | Gradyan normu (W1 / W20) |
|---|---|---|
| Küçük (0,01) | 2,4 × 10⁻² / 1,0 × 10⁻¹⁰ / 5,1 × 10⁻²⁰ | 5,0 × 10⁻²⁰ / 4,9 × 10⁻²⁰ |
| Xavier | 1,9 × 10⁻¹ / 1,2 × 10⁻² / 5,4 × 10⁻⁴ | 5,8 × 10⁻⁴ / 7,2 × 10⁻⁴ |
| He | 4,2 × 10⁻¹ / 5,8 × 10⁻¹ / 8,7 × 10⁻¹ | 1,9 / 8,4 |
| He + BN | 5,8 × 10⁻¹ / 5,9 × 10⁻¹ / 6,0 × 10⁻¹ | 9,3 / 0,61 |

Tablo açık bir hikâye anlatıyor. Küçük sabit başlatmada sinyal katmanlar boyunca ortalama her katmanda yaklaşık 8 kat küçülüyor ve 20. katmanda 10⁻²⁰ düzeyine düşüyor. Gradyan da aynı şekilde sönüyor: ilk katmanın gradyanı 10⁻²⁰, yani hiçbir öğrenme olmaz. Bu, Bölüm 55'te gördüğümüz kaybolan gradyanın en saf biçimi: çarpanların her biri 1'den küçük olduğu için zincirin uzunluğu sinyali yok eder. Xavier, ReLU için tasarlanmadığından sinyali daha yavaş sönümlendiriyor; 20 katmanda 5 × 10⁻⁴'e düşüyor. He başlatma ise ReLU'nun yarısını sıfırlamasını hesaba katar (Bölüm 63'teki sezgi) ve aktivasyon düzeyini katmanlar boyunca korur. Tabloda He'nin std değerleri yaklaşık 0,4'ten 0,9'a çıkıyor; bu, girdinin ölçeğiyle ve ilk katmandaki sapma etkisiyle birlikte olan kabaca dengeli bir artıştır.

Eğitim sonuçları aynı hikâyeyi destekliyor. Aynı 20 katmanlı ağ, SGD (η = 0,05), 20 epoch ve üç tohumla eğitildiğinde test doğrulukları şöyle oldu:

| Başlatma | Test doğruluğu |
|---|---|
| Küçük (0,01) | 0,1028 ± 0,0000 |
| Xavier | 0,3306 ± 0,1302 |
| He | 0,7426 ± 0,1998 |
| He + BN | 0,9648 ± 0,0042 |

Küçük başlatma ağı hiç öğrenemedi (şans düzeyi 0,10). He tek başına tutarsızdı (üç tohum arasındaki sapma 0,20 idi). BatchNorm ile birleşince tutarlı biçimde 0,96'ya çıktı. Bu, başlatmanın gerekli ama tek başına yeterli olmadığını gösterir: derin ağda normalizasyon, sinyal ölçeğini her katmanda yeniden ayarlayarak başlatmanın etkisini sürdürür. Bunu bir sonraki bölümde BatchNorm ile ayrıntılı göreceğiz.

Şekil 64.6, aynı başlatma deneyinin katman katman değerlerini gösteriyor. Sol panelde aktivasyon standart sapması, sağ panelde ağırlık gradyanı normu logaritmik ölçekte çizildi.

![Şekil 64.6: 20 katmanlı ağda başlatma ve BatchNorm'un etkisi. Sol: ileri geçişte aktivasyon std. Sağ: geri geçişte ağırlık gradyanı normu.](gorseller/b64_baslatma.png)

Şekil 64.6'da bir ayrıntı dikkat çekicidir: He başlatmada gradyan normu, ilk katmandan son katmana doğru artıyor (1,9'dan 8,4'e). Bu tam bir "dengeli" durum değildir; ama patlama da değildir. BatchNorm ile birlikte gradyan normları ilk katmanda daha büyük ve son katmanda daha küçük hâle gelir. Yani normalizasyon, katmanlar arası gradyan ölçeğini de değiştirir. Öğrenme oranını seçerken bu farkı akılda tutmak gerekir: ilk katmanın öğrenme hızı ile son katmanınki aynı olmak zorunda değildir.

## 64.7 Normalizasyon: BatchNorm, LayerNorm ve GroupNorm

Normalizasyon, bir katmanın çıktısını (ya da girdisini) yeniden ölçekleyerek dağılımını sabit tutma fikridir. Derin ağlarda her katmanın girdisinin dağılımı, önceki katmanların ağırlıkları değiştikçe kayar. Bu olguya **iç kovaryans kayması** denir ve eski tanımıyla BatchNorm'un ilk gerekçesiydi. Güncel açıklama daha çok kayıp yüzeyinin pürüzlülüğünü azaltmasıdır: normalizasyon, optimizasyonun daha geniş ve daha düzgün bir yüzeyde ilerlemesini sağlar. Hangi açıklama doğru olursa olsun, pratik etki ölçülebilir ve büyüktür.

**Batch normalizasyon (BatchNorm)**, bir mini-batch içinde her özellik (her sütun) için ortalama ve varyansı hesaplar. Eğitim modunda girdi, bu batch istatistikleriyle normalize edilir ve öğrenilebilir iki parametreyle ölçeklenir ve kaydırılır:

μ = (1/N) Σᵢ xᵢ,    σ² = (1/N) Σᵢ (xᵢ − μ)²
x̂ᵢ = (xᵢ − μ) / √(σ² + ε)
yᵢ = γ x̂ᵢ + β

γ ve β, ağın öğrendiği parametrelerdir. Normalizasyon sonrası dağılımın her zaman sıfır ortalama ve birim varyanslı olmasını zorunlu kılmazlar; eğer ağ gerekli görürse bu dağılımı geri kaydırabilir. Şekil 64.7'nin sol paneli bu veri akışını gösteriyor.

Eğitimde BatchNorm'un en önemli yönü geri geçişidir. Çıktıya bağlı kayıp gradyanı dy verildiğinde, girdi gradyanı dx batch'teki tüm örneklere bağlıdır. Türetmenin sonucu şudur:

dγ = Σᵢ dyᵢ x̂ᵢ,    dβ = Σᵢ dyᵢ
dx = (γ / (N σ)) · (N dyᵢ − Σⱼ dyⱼ − x̂ᵢ Σⱼ dyⱼ x̂ⱼ)

Bu formülün önemli bir sonucu, dx'in batch içinde toplamının sıfır olmasıdır: BatchNorm, batch ortalamasının kaymasına karşı gradyanı da düzeltir. Aşağıdaki kod ileri ve geri geçişi tanımlar:

{{KOD|egitim_np.py|def bn_ileri|return dx, dgamma, dbeta}}

Çıkarım modu için BatchNorm fonksiyonu, eğitimde biriken hareketli ortalamaları kullanır:

{{KOD|egitim_np.py|def bn_cikarim|return gamma}}

Bu iki fonksiyonun doğruluğunu iki bağımsız yolla sınadık. İlk olarak PyTorch'un `nn.BatchNorm1d` katmanının ileri ve geri geçişiyle karşılaştırdık; fark 10⁻¹⁵ düzeyinde kaldı. İkinci olarak sayısal gradyanla (merkezi fark, h = 10⁻⁶) karşılaştırdık; en büyük fark 1,4 × 10⁻⁹. Bu iki kontrol, türetmenin ve kodun doğru olduğunu gösterir.

Aşağıdaki küçük örnek, dört sayılık bir batch üzerinde ileri ve geri geçişi gösterir. Girdi x = [1, 3, 5, 7], γ = 2, β = 1 seçildi.

{{KOD|bn_ornek.py|^|$}}

Program şu çıktıyı verir:

{{CIKTI|bn_ornek.py|out_bn_ornek.txt}}

Çıktı, elle yapılan hesabı doğrular. Ortalama 4, yanlı varyans 5'tir (değerler 1, 3, 5, 7 için (9 + 1 + 1 + 9)/4). x̂ değerleri ±1,3416 ve ±0,4472'dir. γ = 2, β = 1 ile y = 2x̂ + 1 olur. Geri geçişte yalnızca ilk örneğe 1 gradyanı verildiğinde dβ = 1 ve dγ = x̂₁ = −1,3416 çıkar. dx'in toplamı sıfırdır; bu, BatchNorm'un sabit bir kaymaya karşı duyarsız olmasının bir sonucudur.

**Eğitim ve çıkarım modu.** Çıkarımda (tek bir örnek için tahmin yaparken) batch istatistiklerine güvenemeyiz: batch yoktur ya da bir örneklik batch ile istatistik anlamsızdır. Bu yüzden eğitim sırasında μ ve σ²'nin hareketli ortalamaları (μ_run, σ²_run) tutulur ve çıkarımda bunlar kullanılır. PyTorch'ta varsayılan momentum 0,1'dir: her eğitim adımında μ_run ← 0,9 μ_run + 0,1 μ. Bir ayrıntı dikkat gerektirir: PyTorch, `running_var`'ı Bessel düzeltmeli (N/(N−1)) varyansla günceller, ama normalizasyonun kendisinde yanlı varyans kullanır. Bu fark, batch büyüdükçe önemsizleşir; ama NumPy kodunda bunu kendi testinle sınamalısın (testimiz bu farkı doğruladı).

Bu ayrım, sık yapılan bir hatanın kaynağıdır. Eğer çıkarım yapmadan önce `model.eval()` çağrılmazsa, BatchNorm hâlâ batch istatistiklerini kullanır. Tek bir örnek için bu istatistikler anlamsızdır; büyük bir doğrulama batch'i için ise sonuç yalnızca az değişir. Bunu bölümün sonundaki tek-batch testinde ölçeceğiz.

BatchNorm'un el örneğini, batch deneyini ve eğitim–çıkarım farkını ölçen betik aşağıdadır.

{{KOD|t06_bn.py|^|<# (b) Kucuk}}
{{KOD|t06_bn.py|# (b) Kucuk|$}}
{{CIKTI|t06_bn.py|out_t06_bn.txt}}

**Küçük batch sorunu.** BatchNorm, batch istatistiklerinin güvenilir olmasını gerektirir. Küçük batch'te μ ve σ² gürültülüdür ve eğitim ile çıkarım arasında tutarsızlık büyür. Aşağıdaki deneyde, iki gizli katmanlı BatchNorm'lu bir MLP'yi farklı batch boyutlarıyla 20 epoch eğittik (beş tohum):

| Batch | Test doğruluğu (ortalama ± sapma) |
|---|---|
| 2 | 0,8683 ± 0,0315 |
| 8 | 0,9811 ± 0,0093 |
| 32 | 0,9856 ± 0,0030 |
| 128 | 0,9833 ± 0,0056 |

Batch 2'de model belirgin biçimde kötü ve daha kararsız. 8 ve üstünde ise BatchNorm sorunsuz çalışıyor. Bu nedenle, bellek sınırı yüzünden batch'i çok küçük tutmak zorunda kalırsan BatchNorm yerine GroupNorm ya da LayerNorm düşünmelisin. Aynı deneyde eğitim ve çıkarım modu arasındaki fark, 64 doğrulama örneğinde 2 tahminle ölçüldü; batch 32 ile eğitilmiş ağda bu fark 360 örnekte 0 çıktı, çünkü hareketli ortalamalar batch istatistiklerine yakındı. Fark, batch küçüldükçe ve veri dağılımı kaydıkça büyür.

**LayerNorm.** Transformer'larda (Bölüm 69) BatchNorm yerine LayerNorm kullanılır. LayerNorm, normalizasyonu batch yerine tek bir örneğin özellikleri üzerinden yapar: μ ve σ², bir örneğin D özelliği üzerinden hesaplanır. Bu, batch boyutundan bağımsızdır, eğitim ve çıkarım arasında fark yoktur ve dizi uzunluğu değişken olan modellerde uygundur. Dizi modellerinde her zaman aynı tüm batch'in istatistikleri anlamlı değildir; bu yüzden LayerNorm oradaki standarttır. Sadece bu noktada bir ayrım: LayerNorm'un formülü aynıdır, sadece ortalama ve varyans farklı eksende alınır.

**GroupNorm.** Özellikleri birkaç gruba bölüp her grup için normalizasyon yapar. Batch'ten bağımsızdır, küçük batch'te veya tek örnekle çalışır. Görüntü modellerinde (Bölüm 66) bellek sınırlı olduğunda tercih edilir. Bu bölümde yalnızca adını ve yerini bilmen yeterli; ayrıntıları ilgili bölümde göreceğiz.

Şekil 64.7, BatchNorm ve dropout'un veri akışını yan yana gösteriyor. Dropout'u aşağıda, düzenlileştirme bölümünde ele alıyoruz.

![Şekil 64.7: Sol: BatchNorm'un eğitim sırasındaki veri akışı ve hareketli ortalamaların rolü. Sağ: dropout'ta eğitim (maske ve ölçekleme) ile çıkarım (kimlik) farkı.](gorseller/b64_bn_dropout_sema.png)

## 64.8 Düzenlileştirme: dropout, ağırlık azaltma, etiket yumuşatma, erken durdurma

Bir ağ, eğitim verisini ezberleyebilecek kadar büyükse aşırı uydurur (Bölüm 57). Düzenlileştirme, ağın ezberlemesini zorlaştıran yöntemlerin genel adıdır. Bu bölümde dört temel yöntemi ölçtük.

**Dropout** (Srivastava ve diğerleri, 2014), eğitimde her ileri geçişte her aktivasyonu 1 − p olasılıkla tutar ve p olasılıkla sıfırlar. Kalan değerleri 1/(1 − p) ile ölçekleriz. Bu **ters ölçekleme** (inverted dropout) yöntemidir: eğitimde beklenen değer aynı kalır, böylece çıkarımda hiçbir değişiklik gerekmez. Çıkarımda dropout kapalıdır ve girdi olduğu gibi geçer. Dropout'un bir ensemble yorumu da vardır: her ileri geçiş, paylaşılan ağırlıklarla farklı bir alt ağı eğitir; çıkarım ise bu alt ağların kabaca ortalamasıdır (genel bilgi).

Aşağıdaki kod, dropout'un ileri geçişini tanımlar:

{{KOD|egitim_np.py|def dropout_ileri|return x * maske, maske}}

Bu fonksiyon, PyTorch'un `F.dropout(..., training=True)` çıktısıyla aynı maske verildiğinde birebir eşleşti. Ters ölçeklemenin doğruluğunu ayrıca, 200 000 örnek üzerinde ortalamanın korunmasıyla kontrol ettik: E[y] ≈ E[x] (0,0047 ve 0,0039, ikisi de sıfıra yakın, çünkü girdi standart normal).

**Ağırlık azaltma (weight decay)** ağırlıkların büyüklüğünü kısıtlar. Adam'da bunu AdamW ile ayrık uyguladığımızı gördük (64.3). Düzenlileştirme etkisini ölçmek için AdamW'yi 0,1 ağırlık azaltmayla da test ettik.

**Etiket yumuşatma (label smoothing)**, hedef etiketi tek sıcak (one-hot) vektör yerine biraz yumuşatılmış bir dağılım olarak verir: ε = 0,1 için doğru sınıfın hedefi 0,9 + 0,01, diğer sınıfların her biri 0,01 olur. Bu, ağı aşırı kendinden emin olmaktan alıkoyar. Bölüm 57'de gördüğümüz **kalibrasyon** bu yüzden ilgi konusudur: model 0,99 güvenle tahmin ettiğinde, gerçekte bu tahminin doğru olma oranı 0,99 olmalıdır. Kalibrasyonu ölçmek için **beklenen kalibrasyon hatası (ECE)** kullanılır: tahminler güvenlik düzeyine göre 15 kutuya ayrılır ve her kutuda ortalama güven ile doğruluk arasındaki fark ağırlıklı olarak toplanır.

**Erken durdurma (early stopping)**, doğrulama kaybı artmaya başladığında eğitimi durdurur ya da en iyi noktayı geri yükler. Bu, eğitim sürecine uygulanmış bir düzenlileştirmedir (Bölüm 57'deki doğrulama uyarısını hatırla).

Düzenlileştirme deneyini yapan betik aşağıdadır. Her varyant için MLP, Adam ile 60 epoch eğitilir; eğitim doğruluğu eğitim kümesinde çıkarım modunda, test doğruluğu ve ECE test kümesinde ölçülür.

{{KOD|t07_duzenlilestirme.py|^|<D = veri()}}
{{KOD|t07_duzenlilestirme.py|D = veri()|<satir = []}}
{{KOD|t07_duzenlilestirme.py|satir = []|<for ad, c in VARYANT}}
{{KOD|t07_duzenlilestirme.py|@|$}}
{{CIKTI|t07_duzenlilestirme.py|out_t07_duzenlilestirme.txt}}

Aşağıdaki deney, 256 gizli birimli iki katmanlı MLP'yi Adam (η = 0,001) ile 60 epoch, beş tohumla eğitti. "Eğitim doğruluğu" eğitim kümesi üzerinde çıkarım modunda ölçüldü; test kümesi ise yalnızca raporlama için kullanıldı.

| Varyant | Eğitim doğruluğu | Test doğruluğu | ECE (test) |
|---|---|---|---|
| Temel | 1,0000 | 0,9733 ± 0,0025 | 0,0195 ± 0,0030 |
| Dropout 0,2 | 0,9998 | 0,9756 ± 0,0023 | 0,0164 ± 0,0011 |
| Dropout 0,5 | 1,0000 | 0,9783 ± 0,0023 | 0,0152 ± 0,0021 |
| AdamW wd = 0,1 | 1,0000 | 0,9722 ± 0,0020 | 0,0167 ± 0,0027 |
| Etiket yumuşatma 0,1 | 1,0000 | 0,9878 ± 0,0032 | 0,1136 ± 0,0053 |

Sonuçlar üç açıdan öğretici. Birincisi, temel model eğitim kümesini tamamen ezberledi (eğitim doğruluğu 1,0000) ama test 0,973'te kaldı: bu, aşırı uydurmanın tipik bir görünümüdür. İkincisi, dropout 0,5 test doğruluğunu 0,978'e çıkardı ve ECE'yi düşürdü; ağırlık azaltma ise bu veri kümesinde anlamlı bir etki yapmadı. Üçüncüsü ve en şaşırtıcı olanı: etiket yumuşatma test doğruluğunu en yüksek seviyeye (0,9878) çıkardı ama ECE'yi 0,11'e yükseltti. Yani model daha doğru tahmin etti, ama güvenini gerçek doğruluğun altına çekti: olası bir açıklama, yumuşatılmış hedeflerin en kolay örnekler için bile güveni yaklaşık 0,9'da tutmasıdır (bu açıklamayı ayrıca sınamadık). Bu, etiket yumuşatmanın kalibrasyonu her zaman iyileştirmediğini gösterir. Kalibrasyon hedefin için önemliyse, yumuşatma seçimini ECE ile birlikte değerlendirmelisin; yalnızca doğruluğa bakmak yetmez.

Erken durdurma bu tabloda ayrı bir sütun değil, ama koşuların en iyi doğrulama epoch'ları bilgi veriyor: temel ve dropout 0,5 varyantlarında en iyi epoch'lar 43 ile 59 arasında. Birçok koşuda en iyi nokta son epoch'lara denk geliyor; yani 60 epoch bu koşularda eğitimi sınırlıyor olabilir. Her projede erken durdurma için doğrulama kaybını bir sabırla (patience) izlemek standart bir uygulamadır.

**Veri artırma (data augmentation)**, eğitim örneklerini döndürerek, kaydırarak veya gürültü ekleyerek çoğaltır. Görüntü modellerinde en güçlü düzenlileştirmelerden biridir. Bu bölümde denemedik; Bölüm 66'da CNN ile birlikte ele alacağız.

**Çift iniş (double descent)** (genel bilgi): modelin kapasitesi arttıkça test hatası önce artıp sonra yeniden düşebilir. Bu, klasik bias-variance eğrisinin tek bir U şekli olmadığını gösterir. Bunu bu bölümde ölçmedik; yalnızca bilmen gereken bir olgu olarak not ediyoruz. Büyük modellerde ezberleme ve genelleme arasındaki ilişki, klasik sezgiden farklı olabilir.

## 64.9 Gradyan sorunları: kırpma ve artık bağlantılar

Kaybolan gradyanı (Bölüm 55) ve başlatmayı (64.6) gördük. Diğer uç, **patlayan gradyan**dır: gradyan normu zincirin çarpanları büyük olduğu için kontrolsüz büyür ve tek bir adımda ağırlıkları yok edecek kadar büyük bir güncelleme yapar. Yaygın çözüm **gradyan kırpmadır** (gradient clipping): tüm parametrelerin gradyanlarının birleşik L2 normu bir eşiği (max_norm) aşarsa, bütün gradyanlar aynı oranda küçültülür. Yön korunur, yalnızca boy kısılır.

{{KOD|egitim_np.py|def norm_kirp|return gradlar, toplam}}

Gradyan deneylerini yapan betik aşağıdadır: (a) patlayan gradyan ve kırpma, (b) ilk katmanın gradyanı, artık bloğu ve sıfır başlatma.

{{KOD|t08_gradyan.py|^|<def derin}}
{{KOD|t08_gradyan.py|def derin|<# (a) patlayan}}
{{KOD|t08_gradyan.py|# (a) patlayan|<# (b) kaybolan}}
{{KOD|t08_gradyan.py|# (b) kaybolan|<class Artik}}
{{KOD|t08_gradyan.py|class Artik|$}}
{{CIKTI|t08_gradyan.py|out_t08_gradyan.txt}}

Bu fonksiyon PyTorch'un `clip_grad_norm_` fonksiyonuyla birebir eşleşti. Bir deneyde 20 katmanlı ağı SGD ile 0,5 öğrenme oranında, batch 32 kullanarak 200 adım eğittik. Kırpmasız koşuda gradyan normu 23,5'e kadar çıktı; kırpmalı koşuda (max_norm = 1) ise kırpmadan önceki normlar 51'e kadar ulaştı ama her adımda kırpıldığı için ağ bu sıçramalara rağmen öğrenmeye devam etti. Kırpmasız koşunun 200 adımdan sonraki tek batch kaybı 2,26 (ağ hâlâ şans düzeyine yakın); kırpmalı koşuda 1,33 idi. Bu tek bir batch değeri olduğu için gürültülüdür; Şekil 64.8'in sağ panelindeki eğri, kaybın genel seyrini daha iyi gösteriyor.

![Şekil 64.8: Sol: gradyan normu (kırpmadan önce) kırpmasız ve kırpmalı koşularda. Sağ: mini-batch kaybı; kırpma eğitimin raydan çıkmasını engeller.](gorseller/b64_klip.png)

Şekil 64.8'in sol panelinde kırpmasız koşunun birkaç adımda 10⁰'ın üzerine çıkan normları ile kırpmalı koşunun sürekli yüksek normlarını görebilirsin. Her iki eğride de norm kırpmadan önce ölçüldüğü için kırpmalı koşunun norm eğrisi de yüksek kalabiliyor; fark, kırpmalı koşuda bu normların her adımda max_norm ile sınırlanmasıdır. Sağ paneldeki kayıp ise kırpmalı koşuda daha kararlı bir düşüş gösteriyor.

**Artık bağlantılar (residual connections)** ise kaybolan gradyana karşı yapısal bir çözümdür. Her bloğun çıktısını girdisine ekleriz: h ← h + F(h). Bu toplamın türevi (1 + F'(h)) olduğu için gradyan, çarpımsal zincir yerine doğrudan bir yoldan geri akar. Bölüm 66'da ResNet ile ayrıntılı göreceğiz; burada etkisini ölçüyoruz.

Aşağıdaki tabloda ilk katmanın gradyan normu, başlatma biçimine göre 30 katmanlı ağlarda ölçüldü (tek batch, 256 örnek, başlangıç ağırlıkları):

| Model | İlk katman gradyanı | Son katman gradyanı |
|---|---|---|
| Varsayılan PyTorch başlatma, 30 katman | 1,4 × 10⁻¹² | 2,1 × 10⁻² |
| He başlatma, 30 katman | 0,32 | 1,2 |
| Artık, He başlatma (dal son katmanı He) | 3,9 × 10³ | 8,2 × 10³ |
| Artık, dal son katmanı sıfır | 0,29 | 0,41 |

Tablo iki şey gösteriyor. Birincisi, varsayılan başlatmada 30 katmanlı ağın ilk katmanı neredeyse hiç gradyan almıyor (10⁻¹²). Bu, kaybolan gradyanın derin bir ağda ne kadar şiddetli olabileceğinin sayısal bir örneğidir. İkincisi, artık bağlantıyı He ile kurduğumuzda gradyan patladı (3,9 × 10³). Çünkü her artık blok eklediği dalın çıktısını girdiye ekler ve 15 blok bu eklemeleri üst üste biriktirir; bu büyümenin kaba bir sezgisi vardır, ölçüm yalnızca sonucu gösteriyor. Çözüm, her artık dalın son katmanını sıfırla başlatmaktır: dal başta sıfır çıktı verir, ağ bir kimlik fonksiyonu olarak başlar ve gradyan olduğu gibi akar. Bu sonuç 0,29 ile sağlıklı bir ölçektedir. Yani artık bağlantı, başlatma ile birlikte düşünüldüğünde işe yarar; tek başına bir sihir değildir.

## 64.10 Eğitim hatası ayıklama: loss eğrisini okumak

Bu bölümün kalbi budur. Bir eğitim koşusu başarısız olduğunda, hatanın kaynağı genellikle üç yerdedir: öğrenme oranı ve optimizer, model ve veri, ya da kodun kendisi. Hangi yerde olduğunu anlamak için iki temel araç kullanılır: loss eğrisi ve tek batch'e aşırı uydurma testi.

Kayıp kataloğunu üreten betik aşağıdadır. Önce başlangıç kaybı kontrolü yapılır; ardından yedi vakanın her biri 40 epoch boyunca eğitilir ve kayıp eğrileri CSV dosyasına yazılır.

{{KOD|t09_teshis.py|^|<satir = []}}
{{KOD|t09_teshis.py|satir = []|<EP = 40}}
{{KOD|t09_teshis.py|EP = 40|<# D. Yetersiz}}
{{KOD|t09_teshis.py|# D. Yetersiz|<# E. Veri}}
{{KOD|t09_teshis.py|# E. Veri|<# F. Etiket}}
{{KOD|t09_teshis.py|# F. Etiket|<# G. Sayisal}}
{{KOD|t09_teshis.py|# G. Sayisal|$}}
{{CIKTI|t09_teshis.py|out_t09_teshis.txt}}

**Loss eğrisi kataloğu.** Eğitim ve doğrulama kaybını her epoch kaydederek, koşunun belirtilerini okuyabilirsin. Aşağıdaki yedi vakanın hepsi gerçek koşulardan alındı (MLP, Adam ya da SGD, digits verisi, 40 epoch, tohum 0). Şekil 64.9, altı vakayı kayıp eğrileriyle gösteriyor; yedinci vaka (NaN) metin ve tabloda ayrıca ele alındı.

![Şekil 64.9: Eğitim hatası kataloğu: altı gerçek koşunun eğitim (kırmızı) ve doğrulama (lacivert kesikli) kaybı. E panelinde log ölçek kullanıldı.](gorseller/b64_teshis_katalog.png)

| Vaka | Yapılan | Son eğitim kaybı | Son doğrulama kaybı | Doğruluk | Belirti ve teşhis |
|---|---|---|---|---|---|
| A: yüksek lr | SGD, η = 2,0 | 2,321 | 2,316 | 0,0975 | Kayıp ln 10 civarında düz; ağ öğrenmiyor. Bölüm 63'te aynı öğrenme oranında ölü ReLU birimleri görülmüştü; bu koşuda birim sayısını ölçmedik. |
| B: düşük lr | SGD, η = 10⁻⁴ | 2,3045 | 2,3039 | 0,0780 | Kayıp neredeyse hiç düşmüyor; ağ öğreniyor ama yavaş. Çözüm lr'yi artırmak ya da daha çok adım. |
| C: aşırı uydurma | 100 örnek, 512 birim | 0,0113 | 0,3032 | 0,8914 | Eğitim kaybı sıfıra yakın, doğrulama kaybı yüksek ve sonra düz. Klasik ezberleme. |
| D: yetersiz uydurma | 2 birimlik darboğaz | 1,694 | 1,706 | 0,2423 | İki kaybın da yüksek ve birbirine yakın olması: model yetersiz. Kapasiteyi artır. |
| E: veri sızıntısı | Etiket bilgisi özelliğe sızdı, test için sıfırlandı | 1,6 × 10⁻⁴ | 3,9 × 10⁻⁴ | 1,0000 (doğrulama) | Doğrulama mükemmel ama test 0,9611. Doğrulama skoru gerçek olamayacak kadar iyi: sızıntı şüphesi. |
| F: etiket karışıklığı | Eğitim etiketlerinin yaklaşık %31'i rastgele | 0,9745 | 0,5544 | 0,9192 | Eğitim kaybı yüksek kalıyor, doğrulama makul; etiket gürültüsünün tipik imzası. |
| G: NaN | Adam, η = 10³ | 485,8 | 508,2 | 0,1003 | Beş epoch'ta NaN çıkmadı ama kayıp devasa; kararsızlık. (Aşağıda NaN'ın nasıl oluştuğunu ayrıca gösteriyoruz.) |

Tablo, belirtileri teşhise nasıl çevireceğimizi gösteriyor. **Aşırı uydurma (C)**da eğitim ve doğrulama kayıpları ilk epoch'larda birlikte düşer, sonra ayrılır: doğrulama kaybı düz kalır ya da yükselir. **Yetersiz uydurma (D)**da iki kayıp birbirine yakın ve yüksektir. **Veri sızıntısı (E)**nda doğrulama, eğitimden bile iyi görünür ve gerçek bir kümede (test) düşer; bu, doğrulama kümesinin eğitimle aynı bilgiyi taşıdığının işaretidir. Bu vakada etiket bilgisi özelliğe doğrudan sızdığı için doğrulama 1,0 oldu.

Vaka F'de eğitim kaybının yüksek kalması, etiket gürültüsünün bir imzasıdır: ağ yanlış etiketleri ezberleyemez, bu yüzden eğitim kaybı yüksek kalır, ama doğru etiketlerin çoğunluğunu öğrendiği için doğrulama düşük kalır. Vaka A ve B'nin ayrımı da öğreticidir: ikisinde de ağ öğrenmiyor, ama A'da kayıp ln 10'un çevresinde salınır, B'de ise yavaşça iner. Bu iki belirti aynı şikâyet gibi görünse de düzeltmesi zıt yönlüdür.

**Başlangıç kaybı kontrolü.** Her eğitim koşusunun ilk adımında kayıp, teorik başlangıç değerine yakın olmalıdır. C sınıf için bu değer ln C'dir. Sıfır başlatılmış son katmanlı bir ağda kayıp tam olarak ln 10 = 2,302585 çıkar; bizim ölçümümüz de 2,302585 verdi. Varsayılan başlatmada ise 2,3073 bulundu, yani aynı düzeyde. Eğer ilk kaybın 2,3'ten çok farklıysa (örneğin 10 ya da 0,01 gibi), çıkış katmanında ya da veri etiketlerinde bir hata vardır. Bu kontrol 10 saniye sürer ve birçok hatayı en başta yakalar.

**NaN'ın iki yolu.** Eğitimde NaN, genellikle sayısal taşmanın sonucudur (Bölüm 63.14). Tipik hata, çapraz entropiyi softmax'in ardından ayrı ayrı hesaplamaktır: softmax çıktısı tam sıfır olursa log(0) = −∞ olur. Aşağıdaki program, aynı veri ve aynı ağ üzerinde iki yolu karşılaştırır: ayrık `log(softmax)` ile `F.cross_entropy` (ki bu log-sumexp ile kararlı hesaplanır). Öğrenme oranını bilerek 10³ aldık.

{{KOD|t09b_nan.py|^|$}}

Program, ayrık yöntemde ilk adımdan sonra kaybın sonsuza gittiğini ve iki adım sonra NaN'a dönüştüğünü gösterir. Kararlı yöntemde ise kayıp büyük ama sonlu kalır:

{{CIKTI|t09b_nan.py|out_t09b_nan.txt}}

Dikkat edilmesi gereken nokta, ayrık yöntemde logit büyüklüğünün 4,6 × 10⁵'e çıkmasıdır; softmax bu değerlerde 1 ile 0 arasında tam sıfırlar üretir ve log(0) sonsuza gider. `F.cross_entropy` de aynı büyük logitlerle sonlu bir kayıp verir çünkü log-sumexp'i maksimumu çıkararak hesaplar. Bu iki yol, sayısal kararlılığın algoritma seçimine bağlı olduğunu gösterir. Pratik kural: çapraz entropiyi her zaman ham logitlerden hesapla, softmax'i önce uygulama.

**Bir tarif olarak eğitim.** Karpathy'nin "A Recipe for Training Neural Networks" (2019, blog yazısı; genel bilgi) yazısı, eğitim hatalarını ayıklamak için bir sıra önerir: önce veriyi gözle incele, sonra basit bir baseline kur, ilk kaybın beklenen değerde olduğunu doğrula, ağı tek bir batch'e aşırı uydurmayı dene, ardından kapasiteyi artırıp düzenlileştir ve en son hiperparametreleri ayarla. Bu bölümdeki sıra da büyük ölçüde bu tarife uyar.

Tek batch testini ve eval modu kontrollerini yapan betik aşağıdadır. Dört varyant aynı 32 örnek üzerinde 500 adım çalışır; ardından dropout ve BatchNorm için eval modu farkı ölçülür.

{{KOD|t10_tek_batch.py|^|<def kos(}}
{{KOD|t10_tek_batch.py|def kos(|<print("Tek batch}}
{{KOD|t10_tek_batch.py|print("Tek batch|<# Eval modu}}
{{KOD|t10_tek_batch.py|# Eval modu|<Xv = veri()[2]}}
{{KOD|t10_tek_batch.py|@|$}}
{{CIKTI|t10_tek_batch.py|out_t10_tek_batch.txt}}

**Tek batch'e aşırı uydurma testi.** Bu, bütün eğitim kodunu sınamanın en hızlı yoludur. Tek bir küçük batch (burada 32 örnek) seçer, ağı ona aşırı uydurmaya çalışırsın. Doğru kurulmuş bir ağ ve kod, birkaç yüz adımda kaybı sıfıra yakın düşürmelidir ve doğruluk 1,0 olmalıdır. Eğer kayıp düşmüyorsa, hata modelde, kayıp fonksiyonunda, optimizasyonda ya da verinin etiketlenmesinde demektir. Aşağıdaki deneyde aynı 32 örnek ve aynı Adam (η = 10⁻³) ile 500 adım koştuk; her seferinde tek bir hata enjekte ettik.

| Vaka | Kayıp (adım 0 → 499) | Doğruluk | Yorum |
|---|---|---|---|
| Doğru kod | 2,311 → 0,0004 | 1,000 | Test geçti. |
| Çift softmax (softmax, sonra CE) | 2,303 → 1,491 | 0,969 | Kayıp 1,49'da takıldı; belirti: kayıp yüksek düzlükte kalıyor. |
| Batch içinde etiket karıştırma | 2,305 → 0,0010 | 1,000 | Test GEÇTİ. Aşağıda neden. |
| `zero_grad` yok | 2,311 → 0,0519 | 0,969 | Kayıp salınımlı (adım 200'de 0,575, 300'de 0,291, 400'de 0,383); gradyanlar birikiyor. |

Çift softmax hatası, kaybı bir düzlüğe kilitler: softmax çıktısını bir daha softmax'lemek olasılıkları düzleştirir ve bu da gradyanları küçültür (bu bir sezgidir; gradyan normunu bu deneyde ölçmedik). Yüksek kalan kayıp ve düşük doğruluk, bu hatanın imzasıdır. `zero_grad` eksikliği ise gradyanların her adımda birikmesine yol açar; kayıp düşer ama salınır ve yakınsamaz. Bu iki hatayı tek batch testi kolayca yakaladı.

Ama tabloda dikkat çeken bir sonuç var: batch içinde etiketleri karıştırdığımız vaka da testi geçti. Etiketler yanlış eşlenmiş olmasına rağmen 128 birimli ağ, 32 örneği ezberleyebildi. Bu, tek batch testinin **gerekli ama yeterli olmadığını** gösterir. Ağ yeterince büyükse, rastgele etiketleri bile ezberleyebilir. Etiket hatalarını yakalamak için başka bir araç gerekir: doğrulama kümesinde beklenen doğruluğu ölçmek, etiket dağılımını kontrol etmek ve (en önemlisi) verinin hangi kaynaktan geldiğini ve nasıl hizalandığını denetlemek. Bu nedenle tek batch testini, eğitim kodunun mekanik olarak çalıştığını sınamak için kullan; veri doğruluğu için ayrı bir kontrol yap.

**Eval modu ve dropout.** Dropout ve BatchNorm, eğitim ile çıkarım arasında davranış farkı yaratır. Eğer eğitimden sonra `model.eval()` çağrılmazsa, tahmin yaparken dropout hâlâ maske uygular ve BatchNorm batch istatistiklerini kullanır. Bunun belirtisi, aynı girdinin iki kez tahmininin farklı çıkmasıdır. 360 doğrulama örneği üzerinde yapılan ölçümde, dropout 0,5'li bir ağda eval unutulduğunda iki tahmin arasında 23 fark çıktı; `model.eval()` ile fark 0 oldu. BatchNorm ağında, 32 batch ile eğitilmiş modelde train ve eval modu arasında tahmin farkı 0/360 çıktı (doğruluk 0,9833 her iki modda da). Yani BatchNorm'un tehlikesi, batch çok küçük olduğunda ve veri dağılımı kaydığında ortaya çıkar; büyük batch'te fark gizli kalabilir. Bu yüzden değerlendirme kodunu her zaman `model.eval()` ile ve `torch.no_grad()` içinde yaz.

**Kasıtlı hata enjeksiyonu: Çözümlü Örnek 4.** Bu teknikleri bir araya getiren bir alıştırma, 3 hatalı bir eğitim betiğinin ayıklanmasıdır. Aşağıdaki betik bir MLP'yi digits verisi üzerinde eğitir ve her epoch'ta eğitim kaybını ve "doğrulama" doğruluğunu yazdırır. Betiğin sonunda test doğruluğu da yazılır. Önce kodu ve çıktıyı oku, sonra hataları bul; çözüm bölümde yer alıyor.

{{KOD|bozuk_egitim.py|^|$}}

Çıktı:

{{CIKTI|bozuk_egitim.py|out_bozuk_egitim.txt}}

Betiğin doğru hâlinde üç hata düzelir: `opt.zero_grad()` her adımdan önce çağrılır, doğruluk hesabında `model.eval()` kullanılır ve doğrulama `Xva, yva` üzerinden yapılır. Düzeltilmiş dosyada ayrıca her epoch başında `model.train()` çağrılır; bu, her epoch'un eğitim modunda başlamasını garanti eder. Düzeltilmiş betik 15 epoch sonunda doğrulamada 0,9526, test kümesinde 0,9472 doğruluk verdi; eğitim kaybı 1,52'den 0,29'a düştü.

Çözüm: Bu hatalar, çıktıda üç farklı belirti bırakır. (1) Kayıp düşmüyor, aksine 2,1'den 2,5'e çıkıp salınıyor. Bu belirti, gradyanların birikmesine (zero_grad eksik) işaret eder; kaybın 15 epoch boyunca düşmemesi birikmiş gradyanların Adam adımlarını bozmasıyla tutarlıdır (bu bir yorumdur; zero_grad'ın tek başına etkisini bu betikte ayrıca ölçmedik). (2) "Doğrulama" doğruluğu, eğitim kümesi üzerinden hesaplanıyor (Xtr, ytr): bu, rakamın neden kendi kaybıyla tutarlı olmadığını ve doğrulama kümesinin hiç kullanılmadığını açıklar. (3) Dropout ile hesaplanan doğruluk, eval modu kapalıyken yapılıyor: aynı girdi her çağrıda farklı tahmin üretebilir ve ölçüm gürültülüdür. Bu üçüncü hata, ikinci hatanın üzerine biner; ama yalnızca ikisi düzeltildiğinde bile bu betik eğitim verisini ölçtüğü için yanıltıcı olurdu. Düzeltilmiş betikte eğitim kaybı 0,75'ten 0,29'a düşüyor, doğrulama 0,95'e çıkıyor ve test kümesi de benzer bir değere ulaşıyor; bu tutarlılık sağlıklı bir eğitimin göstergesidir.

Bu örneğin asıl dersi şudur: bir eğitim betiğinde hata varsa, belirtilerin farklı yerlerde görünür. Kayıp eğrisi bazı hataları, doğrulama ölçümü bazılarını, test ile doğrulamanın tutarlılığı bazılarını gösterir. Üç soruyu aklında tut: Kayıp beklenen yönde mi düşüyor? Doğrulama kaybı ile eğitim kaybı makul bir ilişki içinde mi? Ölçtüğün şey gerçekten doğrulama kümesi mi?

## 64.11 Hiperparametre arama ve deney kaydı

Bir ağda birçok hiperparametre vardır: öğrenme oranı, batch boyutu, dropout, ağırlık azaltma, katman sayısı, birim sayısı. Bunları sistematik biçimde aramanın iki temel yolu vardır: **ızgara arama** (grid search), her boyutta eşit aralıklı değerleri deneyerek tüm kombinasyonları tarar; **rastgele arama** (random search), aynı bütçede değerleri rastgele seçer (Bergstra ve Bengio, 2012; genel bilgi).

Rastgele aramanın üstünlüğü, yalnızca birkaç boyutun gerçekten önemli olduğu durumlarda ortaya çıkar. Izgarada her boyut için az sayıda değer denersen, önemli boyutta kaç farklı değer test ettiğin de azalır. Rastgele aramada ise her deneme önemli boyutta yeni bir değer getirir. Bu deneyde bunu sınadık. Öğrenme oranı (log ölçekte 7 değer, 10⁻⁴ ile 10⁻¹ arası) ve dropout (6 değer, 0 ile 0,5 arası) boyutlarını 42 yapılandırmada tarayıp doğrulama doğruluğunu iki tohumla ölçtük (15 epoch). Sonra gerçek arama bütçesi olarak 9 yapılandırmayı iki yöntemle seçtik ve her seçimde dogrulamada en iyi olanı aldık. Arama süreci 300 kez tekrarlandı ve seçilen yapılandırmanın test skoru raporlandı.

Arama deneyini yapan betik aşağıdadır. Önce 42 yapılandırma iki tohumla eğitilip bir tablo oluşturulur; sonra ızgara ve rastgele arama bu tablo üzerinde 300 kez simüle edilir.

{{KOD|t11_arama.py|^|<tablo = {}}}
{{KOD|t11_arama.py|@|<rng = np.random.default_rng(64)}}
{{KOD|t11_arama.py|@|$}}
{{CIKTI|t11_arama.py|out_t11_arama.txt}}

Şekil 64.10, 42 yapılandırmanın doğrulama doğruluğunu ısı haritasında gösteriyor. Kırmızı kareler, ızgara aramasının seçtiği 9 noktayı işaretliyor.

![Şekil 64.10: Öğrenme oranı ve dropout'un doğrulama doğruluğu üzerindeki etkisi (2 tohum, 15 epoch). Kırmızı kareler ızgara aramasının 9 noktası.](gorseller/b64_arama_isi.png)

Sonuçlar şunları gösteriyor. Doğrulama skoru, öğrenme oranı boyunca 0,17 aralığında değişiyor, dropout boyunca ise yalnızca 0,014. Yani bu problemde öğrenme oranı baskın boyuttur; dropout'un etkisi gürültü düzeyinde. Izgara arama öğrenme oranını yalnızca 3 değerde (10⁻⁴, 3,2 × 10⁻³, 10⁻¹) tararken, rastgele arama 9 denemenin her birinde 7 düzeyli öğrenme oranı ızgarasının tamamından seçim yapabildi. Sonuçta ızgara, test kümesinde 0,9722 doğruluklu bir yapılandırma seçti; rastgele aramanın 300 tekrarında ortalama seçim 0,9710 ± 0,0059 (en kötü 0,9486) çıktı. Tablodaki en iyi yapılandırma 0,9764 idi. Bu fark küçük ve bu deneyde belirleyici değil. Rastgele aramanın sonuçları ise daha geniş bir dağılıma sahip (en kötü 0,9486). Bunun asıl pratik sonucu şudur: önce hangi boyutun önemli olduğunu bilmiyorsan, rastgele arama genellikle daha güvenli bir başlangıçtır; önemli boyut bilinirse ızgara daha hızlı bir kesinlik sağlar.

**Doğrulama disiplini.** Aramayı yalnızca doğrulama kümesinde yap. Test kümesi, arama sürecinin hiçbir aşamasında kullanılmamalıdır; aksi hâlde seçilen yapılandırmanın skoru iyimser olur (Bölüm 57'de gösterildi). Aramanın bütçesini (kaç yapılandırma denendi) raporla: 9 yapılandırmadan seçilen en iyi skor ile 300 yapılandırmadan seçilen en iyi skor aynı şey değildir.

**Tohum sapması.** Tek bir koşunun sonucunu raporlama. Bu bölümdeki her karşılaştırma beş tohumla yapıldı ve ortalama ± sapma verildi. Hiçbir tek koşu "daha iyi" yargısının kanıtı sayılmamalı; sapma, karşılaştırmanın güvenilirliğini gösterir.

**Karışık hassasiyet (mixed precision)** (kısa not): Ağırlıkların ve aktivasyonların bir kısmını 16 bit kayan noktayla hesaplamak, GPU bellek kullanımını ve hızını iyileştirir. Gradyan ölçeklemesi gibi ayrıntılar gerektirir ve sayısal taşma riskini artırır. Bölüm 65'te PyTorch ile uygulamasını göreceğiz; burada yalnızca bu bölümde bildiğimiz NaN ve taşma sorunlarının 16 bitte daha da kolay ortaya çıktığını not ediyoruz (genel bilgi).

**Deney kaydı.** Her koşunun hiperparametrelerini, tohumunu, veri bölme bilgisini ve her epoch'un metriklerini bir dosyaya (JSON satırları ya da CSV) yazmak, bu bölümün bütün ölçümlerini yeniden üretebilmenin şartıdır. Bu bölümdeki her tablo ve şekil, ilgili deney betiği ve veri dosyasından üretildi; kitabın kendisi ölçüm verisini `engine/veri` klasöründen okur. Bir ekip olarak, ölçüm verisini ve kodu birlikte saklamayı alışkanlık hâline getir.




## 64.12 PyTorch ile eşleşme: NumPy kodunun doğrulanması

Sıfırdan yazdığımız her parçanın doğru olduğunu PyTorch ile sınadık. Aşağıdaki betik 19 kontrol yapar: Adam, AdamW, L2 ile azaltma, momentum ve Nesterov güncellemeleri; BatchNorm'un ileri ve geri geçişi (PyTorch ve sayısal gradyan ile), running istatistikleri ve çıkarım modu; dropout'un ters ölçeklemesi; kosinüs, basamaklı ve üstel takvimler; gradyan kırpma. Her kontrol mutlak farkı yazar ve eşiği aşarsa HATA der. Genel eşik 10⁻⁶'dır; takvimler için 10⁻⁹ ve 10⁻¹² kullanılmıştır.

{{KOD|test_np64.py|^|<def kontrol}}
{{KOD|test_np64.py|def kontrol|<# ---- A.}}
{{KOD|test_np64.py|# ---- A.|<kontrol(ad, en_kotu)}}
{{KOD|test_np64.py|@|<# ---- B.}}
{{KOD|test_np64.py|# ---- B.|<# ---- C.}}
{{KOD|test_np64.py|# ---- C.|<# sayisal gradyan}}
{{KOD|test_np64.py|@|<# running istatistikler}}
{{KOD|test_np64.py|@|<# ---- D.}}
{{KOD|test_np64.py|# ---- D.|<# ---- E.}}
{{KOD|test_np64.py|# ---- E.|<# ---- F.}}
{{KOD|test_np64.py|# ---- F.|$}}
{{CIKTI|test_np64.py|out_test_np64.txt}}

## Çözümlü Örnekler

Bu bölümdeki dört örnek, Bölüm 5'te tarif edilen altı adımlı yöntemi izler. Her örnekte önce problemi anlarsın, küçük bir girdiyle denersin, kaba bir çözüm bulur, bu çözümdeki örüntüyü görür, iyileştirir ve sonunda elle yaptığın izle doğrularsın.

### Örnek 1 (★): Adam'ın ilk üç adımını elle izlemek

**Adım 1 — Anla.** Tek bir parametre θ, başlangıçta 1,0'dır. Öğrenme oranı η = 0,1, β₁ = 0,9, β₂ = 0,999 ve ε = 10⁻⁸ alınır. İlk üç adımda gradyanlar sırasıyla 0,5, −0,2 ve 0,1'dir. Soru: her adımda θ ne olur ve sapma düzeltmesi neyi değiştirir?

**Adım 2 — Örnekle.** İlk adımın değerlerini elle yap: m = 0,1 · 0,5 = 0,05; v = 0,001 · 0,25 = 0,00025. Sapma düzeltmesinden sonra m̂ = 0,05 / (1 − 0,9) = 0,5 ve v̂ = 0,00025 / (1 − 0,999) = 0,25. Güncelleme η · m̂/√v̂ = 0,1 · 0,5/0,5 = 0,1, yani θ = 0,9.

**Adım 3 — Kaba çöz.** Her adımda m, v ve ardından m̂ ve v̂ hesaplanır; θ, η m̂/(√v̂ + ε) kadar değişir. Bu, her adımı aynı yolla sürdürmek demektir.

**Adım 4 — Örüntü.** İkinci adımda gradyan işaret değiştirdi, m azaldı (0,05'ten 0,025'e). Üçüncü adımda gradyan tekrar pozitif ama küçük. Sapma düzeltmesi, ilk adımlarda 1 − β₁ᵗ ve 1 − β₂ᵗ paydalarının küçük olmasından dolayı m̂ ve v̂'yi büyütür; t büyüdükçe bu büyütme azalır.

**Adım 5 — İyileştir.** Kaba çözüm zaten doğrudur; ama adım büyüklüğünü ölçeğe bağımlı olmayacak biçimde görmek için v̂'nin kökünü ve m̂'yi birlikte takip etmek yeterlidir. İyileştirme yerine ölçü birimi kontrolü yap: bu güncelleme birimsizdir (η'nın birimi dışında), yani gradyan 100 kat büyüse de adım aynı kalır.

**Adım 6 — Doğrula.** Aşağıdaki tabloyu programın çıktısıyla karşılaştır.

| Adım t | g | m | v | m̂ | v̂ | θ |
|---|---|---|---|---|---|---|
| 1 | +0,50 | 0,05000 | 0,000250 | 0,50000 | 0,25000 | 0,900000 |
| 2 | −0,20 | 0,02500 | 0,000290 | 0,13158 | 0,14495 | 0,865439 |
| 3 | +0,10 | 0,03250 | 0,000299 | 0,11993 | 0,09992 | 0,827500 |

İkinci adımda elle hesap: m = 0,9 · 0,05 + 0,1 · (−0,2) = 0,025 ✓; v = 0,999 · 0,00025 + 0,001 · 0,04 = 0,00028975 ✓; m̂ = 0,025/0,19 = 0,13158 ✓; v̂ = 0,00028975/0,001999 = 0,14495 ✓; θ = 0,9 − 0,1 · 0,13158/√0,14495 = 0,9 − 0,03456 = 0,86544 ✓.

**Bunu AI'sız yazabilir misin?** Gradyan dizisini 0,5, −0,2, 0,1 yerine −1, −1, −1 yap ve θ'nın her adımda neden aynı büyüklükte değiştiğini açıkla. Sapma düzeltmesi olmadan aynı adım ne olurdu?

### Örnek 2 (★★): Dört örneklik batch'te BatchNorm'un ileri ve geri geçişi

**Adım 1 — Anla.** Dört skaler girdi x = [1, 3, 5, 7] var. BatchNorm çıktısı y = γx̂ + β, γ = 2, β = 1. Hem ileri geçişi hem de geri geçişte dβ, dγ ve dx'i hesaplamak gerekir; geri geçişte yalnızca ilk örneğe 1 gradyanı verildiğini varsay.

**Adım 2 — Örnekle.** Ortalama μ = (1 + 3 + 5 + 7)/4 = 4. Sapmalar −3, −1, 1, 3; kareleri 9, 1, 1, 9; yanlı varyans σ² = 20/4 = 5. √5 ≈ 2,2361.

**Adım 3 — Kaba çöz.** x̂ᵢ = (xᵢ − 4)/2,2361 → [−1,3416, −0,4472, 0,4472, 1,3416]. y = 2x̂ + 1 → [−1,6833, 0,1056, 1,8944, 3,6833]. Geri geçiş için dγ = Σ dy x̂ = x̂₁ = −1,3416, dβ = 1, dx'i türev formülüyle hesapla.

**Adım 4 — Örüntü.** Girdinin ölçeği ne olursa olsun x̂ aynı ölçekte kalır ve dx'in toplamı sıfırdır; bu, BatchNorm'un batch ortalamasına bağlı bir kaymaya karşı duyarsız olduğunun cebirsel nedenidir. Bu örnekte dx₁ en büyük pozitif, dx₂ ise en büyük negatif değerdir; gradyan batch içinde birbirini dengeleyen bir dağılım olarak paylaşılır.

**Adım 5 — İyileştir.** Geri geçiş formülünü her seferinde tüm batch'ten topluca hesaplamak yerine, dxᵢ = (γ/(Nσ))(N dyᵢ − Σdy − x̂ᵢ Σ dy x̂) biçiminde yazmak, hem hesabı hem de sıfır toplam özelliğini açıkça gösterir.

**Adım 6 — Doğrula.** Programın çıktısı şu:

| i | xᵢ | x̂ᵢ | yᵢ | dxᵢ (dy = [1,0,0,0]) |
|---|---|---|---|---|
| 1 | 1 | −1,3416 | −1,6833 | 0,2683 |
| 2 | 3 | −0,4472 | 0,1056 | −0,3578 |
| 3 | 5 | 0,4472 | 1,8944 | −0,0894 |
| 4 | 7 | 1,3416 | 3,6833 | 0,1789 |

Elle dx₁ hesabı: dxh₁ = γ · 1 = 2; Σdxh = 2; Σ(dxh x̂) = 2 · (−1,3416) = −2,6833. dx₁ = (1/(4 · 2,2361)) · (4 · 2 − 2 − (−1,3416)(−2,6833)) = (1/8,944) · (8 − 2 − 3,6) = 2,4/8,944 = 0,2683 ✓. Toplam: 0,2683 − 0,3578 − 0,0894 + 0,1789 = 0 ✓.

**Bunu AI'sız yazabilir misin?** Aynı girdiyle γ = 2 yerine γ = 0 yap; dx ne olur ve neden? Bu sonuç, γ'nın gradyan akışında oynadığı rolü gösterir.

### Örnek 3 (★★): Isınma + kosinüs takviminin belirli adımlardaki değerleri

**Adım 1 — Anla.** W = 30 adım ısınma, toplam T = 300 adım, η_max = 0,01 ve η_min = 0 alınır. Ön ısınmada öğrenme oranı doğrusal artar, sonra kosinüs ile azalır. Soru: t = 0, 29, 30, 165 ve 299 adımlarında öğrenme oranı nedir?

**Adım 2 — Örnekle.** t = 0'da ısınma formülü η_max · (t + 1)/W = 0,01 · 1/30 = 0,000333. t = 29'da 0,01 · 30/30 = 0,01 (ısınmanın son adımı). t = 30'da kosinüs başlar: ilerleme (t − W)/(T − W) = 0, yani η = η_max = 0,01.

**Adım 3 — Kaba çöz.** Kosinüs kısmı η(t) = η_min + ½(η_max − η_min)(1 + cos(π · ilerleme)) formülüdür. t = 165 için ilerleme = (165 − 30)/270 = 0,5 ve cos(π/2) = 0; η = ½ · 0,01 · (1 + 0) = 0,005.

**Adım 4 — Örüntü.** Isınma ile kosinüs arasında bir süreklilik vardır: ısınmanın sonunda η_max'a ulaşılır ve kosinüs tam bu değerden başlar. Kosinüsün bitişinde ise η sıfıra yaklaşır; t = 299'da ilerleme 269/270'tir ve cos(π · 0,9963) ≈ −0,99993, dolayısıyla η ≈ 3 × 10⁻⁷.

**Adım 5 — İyileştir.** Formülü her adım için yeniden hesaplamak yerine yalnızca bu iki bölgeyi (ısınma ve kosinüs) ayrı tutmak yeterlidir; kod da zaten böyle.

**Adım 6 — Doğrula.** Aşağıdaki program aynı değerleri üretir (`takvim_ornek.py`). Çıktı da kontrol için yazdırıldı.

{{KOD|takvim_ornek.py|^|$}}

{{CIKTI|takvim_ornek.py|out_takvim_ornek.txt}}

Elle hesap ile tablo eşleşiyor: t = 0 ve t = 165 değerleri, Adım 2 ve Adım 3'teki hesaplarla aynı. t = 299 için sıfıra çok yakın bir değer çıkar (yuvarlamada 0,000000 görünür).

**Bunu AI'sız yazabilir misin?** Isınmayı 0'dan değil de 0,001'den başlatmak için formülü nasıl değiştirirsin? Kosinüsün son değerinin η_min'e ulaşması için T'yi nasıl seçmelisin?

### Örnek 4 (★★★): Bozuk bir eğitim betiğini ayıklamak

**Adım 1 — Anla.** Yukarıdaki betik, iki katmanlı bir dropout'lu MLP'yi 15 epoch eğitiyor. Çıktıda eğitim kaybı yükselmiş, doğruluk şans düzeyine (0,10) düşmüş. Görev: en az üç hatayı bul ve her birinin hangi belirtiye yol açtığını açıkla.

**Adım 2 — Örnekle.** İlk iki epoch'a bak: kayıp 2,149'dan 2,487'ye çıkıyor. Doğrulama doğruluğu 0,345'ten 0,200'e düşüyor. Bu kadar erken bir düşüş, öğrenme oranının ya da birikmiş gradyanların sonucu olabilir.

**Adım 3 — Kaba çöz.** Kodu satır satır oku. Üç olası hata: (a) `opt.zero_grad()` çağrısı yok; (b) doğruluk fonksiyonunda `model.eval()` yok; (c) "dogrulama" ölçümü `Xtr, ytr` ile yapılıyor.

**Adım 4 — Örüntü.** (a) Gradyanlar her adımda birikiyor. Adam'ın ikinci momenti bu biriken büyük gradyanları yakalayınca adım boyları patlıyor ve kayıp salınıyor. (b) Doğruluk hesabı dropout maskesi altında yapılıyor; bu yüzden aynı betik her çalıştırmada biraz farklı doğruluk verir. (c) Ölçüm eğitim verisi üzerinde yapıldığı için rakam bir doğrulama değil, eğitim doğruluğudur; test kümesi ile bir tutarsızlık ancak bu hatalar düzeltildiğinde görünür olur.

**Adım 5 — İyileştir.** Düzeltme üç değişiklik gerektirir: `opt.zero_grad()` her adımdan önce; doğruluk hesabında `model.eval()`; doğrulama için `Xva, yva`. Düzeltilmiş betik (`bozuk_egitim_duzeltilmis.py`) ayrıca her epoch başında `model.train()` içerir.

Düzeltilmiş betik aşağıdadır; üç hatanın düzeltilmiş hâlini içerir. Çıktı, bozuk betikle aynı ölçümleri verir:

{{KOD|bozuk_egitim_duzeltilmis.py|^|$}}
{{CIKTI|bozuk_egitim_duzeltilmis.py|out_bozuk_egitim_duzeltilmis.txt}}

**Adım 6 — Doğrula.** Düzeltilmiş betiğin sonucu: 15 epoch sonunda eğitim kaybı 0,29, doğrulama doğruluğu 0,9526, test doğruluğu 0,9472. Eğitim kaybı 1. epoch'ta 1,516 iken 15. epoch'ta 0,29'a düşüyor. Bozuk betiğin sonunda test 0,0972 idi. İki betiğin farkı birkaç satırdır; çıktıdaki her değişikliği bu satırlara bağlayabiliyorsun.

**Bunu AI'sız yazabilir misin?** Betiğe, doğrulama kaybı üç epoch boyunca düşmezse eğitimi durduran bir erken durdurma ekle. Hangi değişkenleri her epoch kaydetmek gerektiğini ve bunların neden olduğunu açıkla.

## Kendin Yap Projeleri

::: dikkat
Aşağıdaki projelerde yapay zekâ aracı kullanmadan çalış. Amaç, eğitim döngüsünü, optimizer güncellemelerini ve teşhis mantığını kendi elinle kurmaktır. Bir hata çıktığında hatayı önce kendin bulmaya çalış, sonra kayıp eğrisine ve kod satırlarına dön. Yardım istemeden önce kendi ölçümlerini ve notlarını topla.
:::

### Proje 1 (★★): NumPy çatısına Adam, AdamW, BatchNorm, dropout ve zamanlayıcı eklemek

**Amaç.** Bölüm 63'teki NumPy MLP'sini (sinir ağı çatısı) bu bölümde gördüğün teknikleriyle genişlet. Ağ, her gizli katmandan sonra isteğe bağlı BatchNorm ve dropout içermeli; optimizer olarak SGD, momentum, Adam ve AdamW seçilebilmeli; öğrenme oranı bir zamanlayıcıdan gelmeli.

**Yapılacak / Beklenen davranış.** (1) Her optimizer için bir güncelleme fonksiyonu yaz ve ayrı bir test dosyasında PyTorch'un `torch.optim` karşılığıyla 50 adım boyunca karşılaştır; fark 10⁻⁹'dan küçük olmalı. (2) BatchNorm'un ileri ve geri geçişini yaz; sayısal gradyan denetimi (merkezi fark) ve PyTorch `nn.BatchNorm1d` ile eşleşmesini göster. (3) Dropout'u ters ölçekli yaz; eğitim ve çıkarım modunu bir `egitim` bayrağıyla ayır. (4) Kosinüs ve ısınma takvimini uygula; PyTorch zamanlayıcısıyla karşılaştır. (5) Bu parçaları `load_digits` üzerinde bir MLP ile birleştir ve 3 tohumla test doğruluğu raporla.

**Önerilen yaklaşım.** Her güncelleme fonksiyonunu saf bir fonksiyon olarak yaz: girdi olarak parametreyi, gradyanı ve durumu al; yeni parametre ve durumu döndür. Sapma düzeltmesi için adım sayacını durumun içinde tut. BatchNorm'un geri geçişinde önbelleğe aldığın değerlerin (x̂, σ², γ) hangi adımda kullanıldığını bir çizimle düşün. Test dosyasında her karşılaştırmayı tek bir fonksiyonla yap ki hangi kontrolün başarısız olduğu hemen görünsün.

**Başarı kriterleri.** (a) Dört optimizer için PyTorch ile fark 10⁻⁹'dan küçük. (b) BatchNorm dx sayısal gradyanla 10⁻⁶'dan küçük fark. (c) Dropout'un çıkarım modunda kimlik olduğu test edilmiş. (d) Test doğruluğu üç tohum ortalama ± sapma olarak raporlanmış ve test kümesi hiçbir karar için kullanılmamış. (e) Her deney için tohum, lr ve batch bilgisini içeren bir kayıt dosyası üretilmiş.

### Proje 2 (★★★): Eğitim doktoru — kural tabanlı teşhis aracı

**Amaç.** Bir eğitim koşusunun kayıt dosyasını (her epoch için eğitim kaybı, doğrulama kaybı, doğrulama doğruluğu, öğrenme oranı ve gradyan normu) okuyan ve olası sorunları teşhis eden bir araç yaz. Araç, bu bölümde gördüğün belirtileri kurallara dökmeli: yüksek lr, düşük lr, aşırı uydurma, yetersiz uydurma, veri sızıntısı şüphesi, etiket gürültüsü ve NaN.

**Yapılacak / Beklenen davranış.** Araç bir CSV dosyası alır ve bir teşhis raporu üretir. Her teşhis için hangi kuralın tetiklendiğini, hangi epoch'ta ve hangi değerle tetiklendiğini yazar. Kurallar birbiriyle çelişmemeli ve en az bir tanesi "sağlıklı" çıktısı vermeli. Aracı, bu bölümdeki yedi vakanın gerçek kayıtlarıyla (engine/veri içindeki `b64_teshis.csv`) ve ayrıca kasıtlı olarak bozulmuş beş yeni kayıtla test et. Her bozulmuş kayıt için aracın doğru teşhisi bulup bulmadığını raporla.

**Önerilen yaklaşım.** Kuralları küçük ve bağımsız fonksiyonlar olarak yaz: her biri bir kayıt dizisi alıp bir teşhis ya da `None` döndürsün. Eşikleri (ör. "doğrulama kaybı son 10 epoch'ta yükseliyor") sabit değerler olarak değil parametre olarak tanımla ve farklı eşiklerle hangi teşhislerin kararlı kaldığını gözle. NaN'ı kontrol etmeyi en başa koy. Her kural için yanlış pozitif riskini düşün: sızıntı kuralı, doğrulama ile test arasındaki farkı ölçmeden çalışamaz; bu yüzden aracın test kaydını da girdi olarak alabilmesi gerekebilir.

**Başarı kriterleri.** (a) Yedi gerçek vakanın en az altısında doğru ana teşhis. (b) Beş kasıtlı bozulmuş kayıtta en az dördünde doğru teşhis. (c) Sağlıklı bir koşu için hiçbir kural tetiklenmiyor. (d) Her teşhis, dayandığı epoch ve değeri raporluyor. (e) Eşiklerin değişimine karşı hangi teşhisin kararlı olduğunu gösteren kısa bir analiz.

### Ek Alıştırmalar

1. ★ Adam'da β₁ = 0,9 iken ilk gradyan g = 2 ise ilk adımdan sonra m ve sapma düzeltmeli m̂ değerlerini hesapla.
2. ★ Momentum μ = 0,9 ve sabit gradyan g iken hızın kararlı değeri nedir? (İpucu: v = μv + g denklemini sabit noktada çöz.)
3. ★★ Mülakat: Adam neden sapma düzeltmesi yapar? β₂ = 0,999 için 1000. adımda 1 − β₂ᵗ ne kadardır ve v̂ hangi oranda büyür?
4. ★★ Mülakat: BatchNorm'un eğitim ve çıkarım davranışı neden farklıdır? `model.eval()` unutulursa tahminler neden değişir?
5. ★★ Mülakat: Loss NaN oldu. İlk olarak hangi üç şeyi kontrol edersin ve neden bu sırayla?
6. ★★ Bir batch'te N = 4 ve D = 1 için BatchNorm'un dx toplamının sıfır olduğunu cebirle göster.
7. ★★ Dropout p = 0,5 ile ters ölçekleme yapılırken bir aktivasyonun eğitimdeki beklenen değeri neden değişmez? Varyansı nasıl değişir?
8. ★★ Mülakat: Eğitim kaybı düşerken doğrulama kaybı yükseliyor. İki olası neden ve bunlara karşı üç müdahale nedir?
9. ★★★ Kosinüs takviminde ısınma adımı W = 0 olursa (t + 1)/W ifadesi ne olur? Isınma olmadan kosinüs takvimi kullanmanın kararlılık riskini açıkla.
10. ★★★ Mülakat: Derin bir ağda ilk katmanın gradyanı 10⁻¹² mertebesinde. Olası nedenleri ve düzeltme yollarını sırala.
11. ★★★ Bir koşuda doğrulama doğruluğu tek bir epoch'ta 0,95'ten 0,10'a düştü. Üç olası neden ve her biri için yapılacak bir ölçüm öner.
12. ★★★ Mülakat: Izgara ve rastgele arama arasında hangi koşulda ızgara daha iyidir? Bu bölümdeki deneyden bir örnek ver.

## Kod Okuma Egzersizi

Bu bölümde Adam ve AdamW'nin güncelleme kuralını teoride ve NumPy'de gördük. Şimdi aynı kuralın PyTorch'taki uygulamasına bakalım. Kaynak: PyTorch 2.6.0, `torch/optim/adam.py` dosyası, `_single_tensor_adam` fonksiyonu (yerel kurulum: `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\torch\optim\adam.py`, satır 423 – 478). Aşağıdaki alıntı, fonksiyonun tek tensörlü yolundan alındı. Kaynak satırları birebir kopyalandı; yalnızca iki şey yapıldı: capturable/differentiable dalı ile amsgrad dalı bu bölümün kapsamı dışında olduğu için yorumla atlandı, ve 70 karakterlik kitap genişliği için iki satır kırıldı (ifade değişmedi).

```python
        # Decay the first and second moment running average
        # coefficient
        exp_avg.lerp_(grad, 1 - device_beta1)

        exp_avg_sq.mul_(beta2).addcmul_(
            grad, grad.conj(), value=1 - beta2
        )

        # ... capturable/differentiable dali atlandi (satir 427-459)

        else:
            step = _get_value(step_t)

            bias_correction1 = 1 - beta1**step
            bias_correction2 = 1 - beta2**step

            step_size = lr / bias_correction1

            bias_correction2_sqrt = bias_correction2**0.5

            # ... amsgrad dali atlandi (satir 469-474)

            denom = (
                exp_avg_sq.sqrt() / bias_correction2_sqrt
            ).add_(eps)

            param.addcdiv_(exp_avg, denom, value=-step_size)
```

İlk satır birinci momenti `lerp_` ile günceller: exp_avg ← exp_avg + (1 − β₁)(grad − exp_avg). Bu, β₁m + (1 − β₁)g ile aynıdır. İkinci satır ikinci momenti aynı biçimde günceller. Sapma düzeltmesi `bias_correction1` ve `bias_correction2` ile yapılır; bunlar 1 − β₁ᵗ ve 1 − β₂ᵗ değerleridir. Adım boyu `step_size = lr / bias_correction1` olarak alınır ve paydadaki `denom`, √v / √(1 − β₂ᵗ) + ε'dir. Son satır `addcdiv_(exp_avg, denom, value=-step_size)` ile güncellemeyi uygular: sonuç −η · (m/(1 − β₁ᵗ)) / (√v/√(1 − β₂ᵗ) + ε), yani −η · m̂ / (√v̂ + ε). ε, düzeltilmiş kökün dışında eklenir; bu, NumPy kodumuzdaki `np.sqrt(vh) + eps` ifadesiyle aynıdır.

**Weight decay'in yeri.** Adam'da ağırlık azaltma, bu alıntıdan önce, `adam.py` içinde `if weight_decay != 0: grad = grad.add(param, alpha=weight_decay)` satırıyla gradyana eklenir (yaklaşık 397–398. satırlar). AdamW'de ise gradyanlara dokunulmadan önce ağırlık doğrudan küçültülür: `param.mul_(1 - lr * weight_decay)` (`adamw.py` içinde, yaklaşık 405. satır). Bu tek satır, Adam ile AdamW arasındaki farkın özüdür.

**Sorular — cevaplamadan geçme:**

1. `exp_avg.lerp_(grad, 1 - device_beta1)` ifadesi, `β₁ m + (1 − β₁) g` ile matematiksel olarak eşdeğer mi? Hangi tür yuvarlama farkı oluşabilir?
2. Sapma düzeltmesi paydası `1 - beta2**step` ile `step` büyüdüğünde ne olur? Bu, erken adımlar ile geç adımlar arasındaki farkı nasıl değiştirir?
3. Adam'da L2 azaltması gradyanı değiştirir: grad.add(param, alpha=wd). Bu eklemenin v (ikinci moment) üzerindeki etkisini açıkla. Büyük gradyanlı bir parametrede azaltma neden zayıflar?
4. AdamW'de `param.mul_(1 - lr * weight_decay)` adımı, gradyanın ikinci momentine hiç girmez. Bu, azaltmanın hangi parametrelerde daha güçlü olacağı konusunda ne anlama gelir?
5. Kaynakta `step` değişkeni `_get_value(step_t)` ile alınır. Bu adım sayacı neden bir tensör olarak tutulur, düz bir Python tamsayısı olarak değil? (İpucu: `capturable` modu ve GPU üzerinde CUDA grafiği.)
6. Eğer `eps` değerini 10⁻⁸ yerine 10⁻¹⁵ alırsan, hangi koşulda sonuç gözle görülür biçimde değişir? Bu bir sayısal kararlılık sorunu mudur?

## Bölüm Özeti

- Eğitim bir deney disiplinidir: tek değişken, tohum tekrarı ve ayrı test kümesi. Başlangıç kaybını (C sınıf için ln C) kontrol etmek ilk teşhis adımıdır.
- Mini-batch gradyan gürültüsü batch ile ters orantılı azalır; batch ve öğrenme oranı birlikte seçilir. Büyük batch'te doğrusal ölçek bile kararsızlaşabilir.
- Momentum ve Nesterov hız biriktirir; Adam gradyan ölçeğinden bağımsız adım boyu verir ve sapma düzeltmesi ilk adımları telafi eder. AdamW, ağırlık azaltmayı gradyandan ayırır ve bunun farkı PyTorch kaynağında tek satırdır.
- Öğrenme oranı en önemli hiperparametredir. LR aralık testi üst sınırı ölçer; kosinüs ve ısınma + kosinüs, derin ve büyük ağlarda kararlılığı artırır.
- Başlatma sinyali derin ağda korumak zorundadır: küçük sabit başlatma 20 katmanda sinyali sıfıra çökertir; He ve BatchNorm sinyali korur. Artık bağlantılarda son katmanı sıfır başlatmak gradyanı sağlıklı tutar.
- BatchNorm'un ileri ve geri geçişi türetilip sayısal ve PyTorch ile doğrulandı; eval modu ve küçük batch tuzakları ölçüldü. Dropout ters ölçeklemeyle eğitimde uygulanır; etiket yumuşatma doğruluğu artırabilir ama kalibrasyonu bozabilir.
- Gradyan kırpma patlayan gradyanı yönünü koruyarak sınırlar; artık bağlantı kaybolan gradyanı yapısal olarak giderir.
- Eğitim hatası ayıklamada loss eğrisi kataloğu (yüksek ve düşük lr, aşırı ve yetersiz uydurma, sızıntı, etiket gürültüsü, NaN) ve tek batch'e aşırı uydurma testi temel araçlardır. Tek batch testi gerekli ama yeterli değildir: etiket kaymasını yakalamaz.
- Hiperparametre aramasında öğrenme oranı baskın boyuttur; doğrulama disiplinini koru ve bütçeyi raporla.

**Sonraki bölümde:** Bölüm 65, PyTorch Derinlemesine, bu bölümde yalnızca ölçüm aracı olarak kullandığımız çerçeveyi ele alıyor. Tensörleri, autograd'u, `nn.Module` yapısını, Dataset ve DataLoader'ı, mixed precision'ı, checkpoint'leri ve tekrarlanabilirliği göreceksin. Bu bölümde yazdığımız NumPy MLP'sinin neden PyTorch'ta tek satırla yazılabildiğini de orada anlayacaksın.

::: mulakat
1. Adam'da sapma düzeltmesi neden gereklidir? İlk adımda m̂ ve v̂ hangi değerleri alır ve bu güncelleme büyüklüğünü neden etkiler?
2. Eğitim sırasında BatchNorm ile çıkarım sırasında BatchNorm arasındaki fark nedir? Modeli çıkarıma almadan önce `model.eval()` çağrılmazsa ne olur?
3. Loss NaN oldu. İlk olarak hangi üç şeyi kontrol edersin ve neden?
4. L2 düzenlileştirme ile ağırlık azaltma (weight decay) Adam'da neden farklı sonuç verir? AdamW bu farkı nasıl düzeltir?
5. Eğitim kaybı düşüyor ama doğrulama kaybı 10 epoch'tır yükseliyor. Bu nasıl bir durum, neden olabilir ve hangi üç müdahaleyi denersin?
6. Derin bir ağda ilk katmanın gradyanı 10⁻¹² mertebesinde. Sorunun kaynağını nasıl ayırt edersin: başlatma mı, aktivasyon mu, yoksa öğrenme oranı mı?
7. Bir ekip, tek bir batch'e aşırı uydurma testinin geçtiğini söylüyor ama test doğruluğu şans düzeyinde. Hangi hatanın tek batch testini geçebileceğini ve bunu nasıl ayırt edeceğini açıkla.
8. Hiperparametre aramasında rastgele aramanın ızgara aramaya göre avantajı nedir? Hangi koşulda ızgara yine daha iyi olur?
:::
