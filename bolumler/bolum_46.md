%% kisim_no: XI
%% kisim_ad: Gömülü Sistem
%% bolum_no: 46
%% baslik: Edge AI & TinyML

## Giriş: Model bulutta eğitilir, cihazda yaşar

Bir elektrikli aracın batarya yönetim sistemi (BMS) her hücrenin gerilimini ve sıcaklığını saniyede onlarca kez okur. Bu veriden bir hücrenin ne zaman bozulmaya başladığını anlamak istiyorsun. Bunu yapmanın kolay yolu, ham veriyi bir sunucuya gönderip oradaki büyük bir modelle karar vermek. Ama bir sorun var: ağ gecikir, bağlantı kopabilir ve sürücünün aracındaki sensör verisini bir yerlere göndermesi çoğu zaman istenmez. Asıl soru şu: karar cihazın içinde, kendi işlemcisinde verilebilir mi?

Bu soruya **Edge AI** (uçta yapay zekâ) ve **TinyML** (çok küçük makine öğrenmesi) alanları cevap arar. Fikir basit: model eğitimi güçlü bir bilgisayarda yapılır, ama çıkarım (inference, yani eğitilmiş modelin yeni bir girdi için cevap üretmesi) cihazın kendi işlemcisinde çalışır. Bu bölümün konusu tam olarak bu son adım: bir modeli kısıtlı donanımda, birkaç kilobaytlık belleğe ve birkaç yüz kilobayt flash'a sığdırıp doğru ve hızlı çalıştırmak.

Savunma sanayiinde bu konu doğrudan karşına çıkar. Bir İHA'nın bağlantısı kesildiğinde bile kendi sensöründen karar verebilmesi gerekir. Bir hedefin görüntüsünü yere indirip sunucuda işlemek, hem gecikme hem de bağlantı açısından bir risk taşır. Bölüm 67'de nesne tespitini göreceksin; orada modelin büyük olduğunu göreceksin. Bu bölümde ise aynı soruya gömülü mühendisin gözünden bakıyoruz: model ne kadar yer tutar, bir çıkarım ne kadar sürer, bunu kaç bit ile yapabiliriz ve doğruluktan ne kadar ödün veririz?

Bu bölüm ML'in tamamını anlatmıyor. Okur olarak sen henüz makine öğrenmesi öğrenmedin; bu konu Kısım XIV'te (Bölüm 54 ve sonrası) derinlemesine geliyor. Burada yalnızca ihtiyacımız olan minimum fikri alıyoruz: bir model, **parametreler** (ağırlıklar) ve bu parametreleri girdiye uygulayan bir **hesap grafiği**dir. Eğitim başka bir yerde yapılır, cihazda yalnızca ileri geçiş çalışır. Gerisi, bu ileri geçişi kısıtlı bir işlemcide doğru ve ölçülebilir biçimde çalıştırmanın mühendisliğidir.

::: not
Bu bölümdeki sayıların iki türü var. Birincisi **ölçülen**: host'ta çalıştırdığımız programların ve arm-none-eabi-gcc 13.3.1 ile derlediğimiz Cortex-M4 kodunun çıktıları. İkincisi **tahmin**: Cortex-M4 üzerinde gecikme ve enerji. Bu tahminleri hiçbir kartta çalıştırmadık; metinde her biri açıkça "tahmin" diye işaretli. Bölümdeki ölçüm programlarını kendi bilgisayarında çalıştırabilirsin.
:::

## 46.1 Neden uçta çıkarım?

Bir modeli bulutta çalıştırmak ile cihazda çalıştırmak arasındaki farkı beş eksende düşünebiliriz: gecikme, gizlilik, bağlantı, bant genişliği ve güç. Aşağıdaki tablo bu beş eksenin iki seçenek için kabaca nasıl göründüğünü özetler. Sayılar değil yönler önemlidir; gerçek değerler ağa, donanıma ve yazılıma göre değişir.

| Eksen | Bulutta çıkarım | Uçta (cihazda) çıkarım |
|---|---|---|
| Gecikme | Ağ gidiş-dönüşü eklenir; ağa ve konuma bağlı | Ağ yok; yalnızca işlemci süresi |
| Gizlilik | Ham veri cihazdan çıkar | Ham veri cihazda kalır, yalnızca karar gider |
| Bağlantı | Sürekli bağlantı gerekir | Bağlantı kesilse de karar verilir |
| Bant genişliği | Her örnek ya da pencere gönderilir | Yalnızca sonuç ya da özet gönderilir |
| Güç | Radyo iletimi pil tüketir | İşlemci ve az bellek; iletim azalır |

Gecikme eksenindeki fark bazen tek başına kararı verir. Bir hücrenin aşırı ısınmasına bağlı bir olayda, kararın ağ üzerinden geri dönmesini beklemek, güvenli bir tepkiyi geciktirebilir. Bağlantı ekseni ise savunma sanayiinde ağır basar: menzil dışına çıkan, tünelden geçen ya da elektronik harp altında olan bir sistem bulutla konuşamayabilir. Bant genişliği ve güç eksenleri ise pil ve radyo ile ilgilidir: saniyede yüzlerce örneği kablosuz göndermek hem pahalı hem de gereksizdir.

Bu üçlüden çıkan sonuç şudur: karar yerel olmalı, veri yalnızca gerektiğinde dışarı çıkmalı. Uçta çıkarım bu ilkenin ML tarafıdır.

![Şekil 46.1: Bulut, uç ve MCU çıkarım spektrumu (kaba mertebeler)](gorseller/b46_spektrum.png)

Şekil 46.1'de üç donanım sınıfı görüyorsun. Bulut tarafında GPU'lu sunucular vardır; bunlar en büyük modelleri çalıştırır ama sürekli bağlantı ister. Uç tarafında Cortex-A tabanlı gömülü bilgisayarlar ve NPU (sinir işleme birimi) ya da GPU içeren kartlar bulunur; Jetson sınıfı kartlar buna örnektir. Bunlar birkaç watt ile çalışır ve gigabayt mertebesinde bellek sunar. MCU sınıfında ise Cortex-M gibi mikrodenetleyiciler vardır: milliwatt mertebesinde güç harcar, kilobayt mertebesinde RAM'e sahiptir ve bağlantı gerektirmez. Bu bölümün odağı en sağdaki sınıftır; ama bu sınıftaki kısıtları anlamak için diğer ikisini bilmek gerekir.

Bu sınıflar arasındaki sayılar genel bilgidir; her karta özgü değerleri ilgili veri sayfasından kendin doğrulamalısın. Bu bölümdeki ölçümler yalnızca Cortex-M4 sınıfı bir hedef için yapılmıştır.

## 46.2 Model nedir? Parametre, hesap grafiği, eğitim ve çıkarım

Bir modeli soyut olarak şöyle düşünebilirsin: bir fonksiyon `f(x; θ)`. Burada `x` girdi, `θ` ise parametreler kümesidir. Eğitim, `θ`'yı öyle bulmaktır ki `f` iyi tahmin üretsin. Çıkarım ise `θ` sabitken yalnızca `f(x; θ)`'yı hesaplamaktır. Gömülü tarafın işi çoğunlukla ikinci kısımdır: `θ` bir kez hazırlanır, cihaza yazılır, sonra milyonlarca kez `x` için `f` hesaplanır.

En basit sinir ağı türü olan çok katmanlı algılayıcıda (MLP) hesap, birkaç matris işlemine ayrılır. Bizim bu bölümde kullanacağımız ağ 20 girdi alıyor, 8 gizli birim içeriyor ve 2 çıktı üretiyor:

`z1 = W1 x + b1`, `a1 = max(0, z1)`, `z2 = W2 a1 + b2`

Burada `W_1` 8 satır ve 20 sütunluk bir matristir; `b_1` 8 elemanlı bir vektördür. `max(0, ·)` işlemi ReLU'dur: negatif değerleri sıfıra çeker. Son satırdaki `z_2` iki sınıf için iki sayıdır (logit); hangisi büyükse ağ o sınıfı seçer. Bu üç satır, **hesap grafiğinin** en küçük örneğidir: hangi işlemin hangi sırayla hangi verinin üzerinde yapıldığını söyler.

Eğitim tarafında bir **kayıp** (loss) fonksiyonu vardır. Örneğin iki sınıflı bir sınıflandırmada çapraz entropi, tahminin ne kadar yanlış olduğunu tek bir sayıyla ölçer. **Gradyan inişi**, bu kaybın parametrelere göre türevini (gradyanını) alıp parametreleri her adımda küçük bir miktar ters yönde kaydırır: `θ ← θ − η ∇L(θ)`. Buradaki `η` öğrenme oranıdır. Bu tek paragraf ihtiyacın olan her şeydir; türevin nasıl alındığı Bölüm 55'te, sinir ağlarında geri yayılımın türetilmesi Bölüm 63'te anlatılacak. Bu bölümde eğitim kodu bir kutu gibi davranır: çıktısı olan `θ` cihaza gider.

Aşağıdaki üç satır, MLP'nin ileri geçişini numpy ile yazar. Bu fonksiyon, bu bölümün ilerleyen kısımlarında hem eğitimde hem de kuantizasyon referansında kullanılacak.

```python
def ileri(x, W1, b1, W2, b2):
    """x: (B, 20). Doner: z1, a1, z2."""
    z1 = x @ W1.T + b1
    a1 = np.maximum(z1, 0.0)
    z2 = a1 @ W2.T + b2
    return z1, a1, z2
```

Dikkat et: bu fonksiyonda hiçbir `θ` değişmiyor. Çıkarım yalnızca okur ve hesaplar. Gömülü tarafta bu ayrım çok önemlidir, çünkü `θ` sabit olduğu için flash belleğe (salt okunur) yazılabilir ve RAM'i yalnızca ara değerler için kullanırsın. Bölüm 25'teki bellek hiyerarşisi burada doğrudan işe yarar: büyük ve sabit olan şey flash'ta, küçük ve geçici olan şey RAM'de durur.

## 46.3 Bütçe: bellek, işlem sayısı ve gecikme

Bir modeli bir MCU'ya sığdırmadan önce üç soruyu cevaplamalısın: model flash'a sığar mı, çıkarım sırasındaki geçici değerler RAM'e sığar mı ve çıkarım yeterince hızlı mı? Bu üç soru bir **bütçe** hesabıdır. Bütçeyi yapmadan kod yazmak, sonradan "neden sığmıyor?" diye saatlerce uğraşmanın en kısa yoludur.

**Parametre belleği.** `P` parametre sayısı ve `b` bit genişliği ise model belleği yaklaşık `P · b / 8` bayttır. Float32 için `b = 32`, int8 için `b = 8`. Bu, 1 milyon parametreli bir modelin float32 ile yaklaşık 4 MB, int8 ile yaklaşık 1 MB tuttuğu anlamına gelir. Gerçek modelde buna her katmanın ölçek ve sıfır noktası gibi ek bilgisi de eklenir; bunu kuantizasyon bölümünde göreceksin.

**Aktivasyon belleği.** Bir katmanın girdisi ile çıktısı aynı anda RAM'de olmalıdır. Ağın tepe (peak) aktivasyon belleği, katmanlar boyunca bu çiftlerin en büyüğüdür. Ağ katman katman ilerlediği için her katmanın bellek ihtiyacı ayrı ayrı hesaplanır; sonra en büyüğü alınır. Bu, tüm katmanların çıktılarını aynı anda tutmak zorunda olmadığın anlamına gelir.

**İşlem sayısı (MAC).** Bir tam bağlı katman `m` girdi ve `n` çıktı ile `m · n` çarpma-toplama (MAC, multiply-accumulate) işlemi yapar. Bir MAC, bir çarpma ile bir toplamadır; mikrodenetleyicilerde en sık yapılan iş budur.

**Gecikme.** Kaba bir tahmin için, tek bir MAC'in `c` çevrim sürdüğünü varsayıp toplam çevrimi işlemci saat hızına bölersin: `T ≈ (MAC · c) / f`. Örneğin 168 MHz'de çalışan bir Cortex-M4 (STM32F4 ailesi) için `10^6` MAC'lik bir ağ, her MAC'in tam bir çevrim sürdüğü ideal durumda yaklaşık 6 ms eder (`10^6 / 168·10^6`). Gerçekte bir MAC birden fazla komut ister ve bellek erişimi çevrim ekler; bu yüzden `c` değeri genellikle birden büyüktür. Bunu bu bölümün ilerleyen kısmında ölçülen komut sayılarıyla gerçekçi hale getireceğiz.

Bu bölümdeki model iki katmandan oluşuyor. Bütçe tablosunu bu modelin değerlerinden çıkardık; tablo doğrudan kuantize edilmiş modelin boyutlarından üretildi.

| Katman | Parametre | float32 (bayt) | int8 modeli (bayt) | MAC | Çıktı (bayt) |
|---|---|---|---|---|---|
| Normalizasyon | 40 | 160 | 160 | 0 | 80 |
| Katman 1 (20 → 8) | 168 | 672 | 256 | 160 | 8 |
| Katman 2 (8 → 2) | 18 | 72 | 24 | 16 | 8 |
| Toplam | 226 | 904 | 440 | 176 | 96 |

Tabloyu üreten betik `butce.py`'dir; çıktısı aşağıdadır (aynı değerler CSV olarak `engine/veri/b46_butce.csv` dosyasına da yazılır).

```python
# -*- coding: utf-8 -*-
"""Katman basina parametre, bellek, MAC butcesi (CSV)."""
import os
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
# (katman, parametre, f32 bayt, int8 modeli bayt, MAC, cikti bayt)
SATIR = [
    ("normalizasyon", 40, 160, 160, 0, 80),
    ("katman1_20x8", 168, 672, 256, 160, 8),
    ("katman2_8x2", 18, 72, 24, 16, 8),
]
if __name__ == "__main__":
    yol = os.path.join(VERI, "b46_butce.csv")
    with open(yol, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("katman,parametre,bayt_f32,bayt_int8,mac,"
                 "cikti_bayt\n")
        for r in SATIR:
            fh.write("%s,%d,%d,%d,%d,%d\n" % r)
        t = [sum(r[i] for r in SATIR) for i in range(1, 6)]
        fh.write("toplam,%d,%d,%d,%d,%d\n" % tuple(t))
    print(open(yol, encoding="utf-8").read(), end="")
```

```term
$ python butce.py
katman,parametre,bayt_f32,bayt_int8,mac,cikti_bayt
normalizasyon,40,160,160,0,80
katman1_20x8,168,672,256,160,8
katman2_8x2,18,72,24,16,8
toplam,226,904,440,176,96
```

Tablodaki "int8 modeli" sütunu, katman 1 için 160 bayt ağırlık, 32 bayt onyargı (8 adet 32-bit), 32 bayt `M0` ve 32 bayt `rs` değerini kapsar. Normalizasyon satırı float kalır (160 bayt), çünkü ortalama ve standart sapma değerleri cihazda float olarak tutulur. Şekil 46.2 aynı bilgiyi katman katman gösteriyor.

![Şekil 46.2: Katman başına parametre belleği: float32 ve int8 karşılaştırması](gorseller/b46_butce.png)

Bu tablodan iki sonuç çıkar. Birincisi, modelin kendisi (440 bayt) bu mikrodenetleyicinin flash'ında küçük bir yer kaplar; RAM'de tutulması gereken şey ise pencere tamponudur. Bu bölümde 32 örneklik 4 kanallı bir float pencere 512 bayt tutar; modelin ara değerleri ise birkaç düzine bayttır. Yani bu sistemin RAM bütçesini belirleyen şey model değil, sensör tamponudur. İkincisi, MAC sayısı 176'dır; bu küçük bir iş yüküdür. Ama ön işleme (öznitelik çıkarımı) bu işin yanında çok daha fazla işlem isteyebilir; bunu 46.9'daki ölçümlerde göreceksin.

## 46.4 Sayı temsili: tam sayı, sabit nokta ve kayan nokta maliyeti

Bölüm 1'de iki şeyi gördün: tamsayıların ikilik temsili (iki tümleyen dahil) ve IEEE-754 kayan nokta biçimi. Bölüm 1.5'teki `float` (32 bit: 1 işaret, 8 üs, 23 mantis) bilgisayarlarda genel amaçlı bir sayı biçimidir. Gömülü dünyada bu biçimin bir maliyeti vardır ve model küçültmenin temel nedenlerinden biri de budur.

**Kayan nokta ne kadar pahalı?** Cortex-M4F çekirdeği, tek duyarlıklı (32-bit) kayan nokta birimi (FPU) içerir. Bu birim toplama ve çarpmayı donanımda yapar; ama bölme ve kare kök çok daha uzun sürer (genel bilgi; kesin çevrim sayısı için komut tablosuna bakmalısın). FPU'su olmayan bir Cortex-M3 veya M0'da ise her float işlemi yazılım kütüphanesi çağrısıdır ve birkaç yüz çevrime çıkabilir (genel bilgi). Bu bölümde derlemeyi `-mfpu=fpv4-sp-d16` ile yaptık: bu, tek duyarlıklı FPU olduğu anlamına gelir. Çift duyarlık (`double`) donanımda yoktur ve derleyici onu yazılımla çevirir; bu yüzden C kodunda `1.0` yerine `1.0f` yazmak gereksiz pahalı işlemleri önler.

**Sabit nokta (fixed-point) biçimi.** Sabit noktada bir sayıyı tamsayı olarak saklarsın; ama her değerin ondalık noktasının nerede olduğuna sen karar verirsin. Bu kararı `Qm.n` yazımıyla ifade ederiz: toplam bit genişliği `m + n` (işaret biti dahil), `n` kesir biti. DSP literatüründe en yaygın olan **Q1.15**'te 16 bit vardır: en üst bit işaret, kalan 15 bit kesirdir. Bir `q` tamsayısının gerçek değeri `q / 2^n` olur. Şekil 46.3'te bu düzen görülüyor.

![Şekil 46.3: Q1.15 sabit nokta biçimi: bit düzeni ve değer](gorseller/b46_qformat.png)

Q1.15 sayıları `[-1, 1 - 2^-15]` aralığını temsil eder. Adım aralığı `2^-15 ≈ 0.0000305`'tir. Örneğin `0.5`, `q = 0.5 · 2^15 = 16384` olarak saklanır. Bir kesir sayının Q1.15'e çevrilmesi `round(x · 2^15)` ile yapılır ve sonuç `[-32768, 32767]` aralığına kırpılmalıdır. Bu kırpma **doygunluk** (saturation) denen işlemdir.

Sabit noktada iki sayıyı çarptığında sonuç Q2.30 biçimindedir (her iki operandın kesir bitleri toplanır). Sonucu tekrar Q1.15'e indirmek için 15 bit sağa kaydırırsın. Burada iki sorun ortaya çıkar. Birincisi **yuvarlama**: sağa kaydırma, değerin aşağı yönlü (sonsuza doğru) yuvarlanmasına yol açar; negatif sayılarda bu sistematik bir kayma demektir. En yaygın çözüm kaydırmadan önce `2^(n-1)` eklemektir, böylece en yakın tamsayıya yuvarlanır. İkincisi **taşma** (overflow) ve **doygunluk**. Taşma, sayının bit genişliğini aşıp sarması (wrap-around) demektir. Doygunluk ise sonucu sınırda kesmektir. Bir sinyal işlemcisinde `0.999 + 0.999` gibi bir toplama taşmak yerine `0.99997` sınırında kalmalıdır; aksi halde işaret tersine döner ve bu, ağın davranışını kökten bozar. C dilinde işaretli tamsayı taşması tanımsız davranıştır (UB); yani derleyici bunun sonucunu garanti etmez. Bu yüzden biriktirici değerleri `int32_t` içinde tutar ve doygunluğu açıkça uygularsın.

Pratikte şu üç kural işini görür:

- Çarpım sonucunu bir boyut büyük tut (Q1.15 × Q1.15 için 32 bit).
- Kaydırmadan önce yuvarlama sabitini ekle.
- Her ara sonucu veya nihai çıktıyı doygunlukla sınırla.

Bu kuralların uygulamasını Çözümlü Örnek 2'de elle yapacaksın. Bölüm 24.8'deki SIMD ve Cortex-M4 DSP komutları (SMLAD, SSAT gibi) bu işlemleri tek komutla yapabilir; bu bölümün ilerleyen kısmında bu komutları kullanan bir iç döngü göstereceğiz.

## 46.5 Kuantizasyon: gerçek sayıyı tamsayıya eşlemek

Kuantizasyon, kayan noktalı ağırlıkları ve aktivasyonları daha az bitle temsil etme işidir. Bizim hedefimizde bu, float32 değerleri int8'e (8 bit işaretli tamsayı, aralığı `[-128, 127]`) çevirmek demektir. Bunun için kullanılan dönüşüm **afin** (doğrusal ötelemeli) bir eşlemedir:

`r = S · (q - Z)`

Burada `r` gerçek (float) değer, `q` int8 değer, `S` float bir **ölçek** (scale), `Z` ise tamsayı bir **sıfır noktası** (zero point) değeridir. Sıfır noktası, gerçek `0.0` değerinin hangi tamsayıya denk geldiğini söyler. Bu öteleme neden gereklidir? Çünkü ReLU çıkışları ve dolgu (padding) sıfırları tam olarak `0.0` olmalıdır; kuantizasyon bu sıfırı bozmamalıdır. Şekil 46.4, `[lo, hi] = [-0.4, 2.3]` aralığının int8 eksenine nasıl eşlendiğini gösterir; burada `Z = -90`'dır.

![Şekil 46.4: Afin kuantizasyon: gerçek eksen ve tamsayı ekseni eşlemesi](gorseller/b46_affin.png)

**Asimetrik eşleme.** Bir tensörün en küçük değeri `lo` ve en büyüğü `hi` ise, bu aralığı 256 seviyeye bölmek için `S = (hi - lo) / 255` alırsın. Sıfır noktası `Z = round(-128 - lo / S)` ile hesaplanır; ardından `Z` değerini `[-128, 127]` aralığına kırparsın. Asimetrik eşleme aralığın tamamını kullanır, ama her zaman sıfırı tam temsil etmek için aralığa `0` eklenir: `lo = min(lo, 0)` ve `hi = max(hi, 0)`. ReLU çıkışlarında `lo = 0` olduğundan `Z = -128` çıkar; yani ReLU'nun sıfır kısmı zaten tamsayının en küçük değeridir.

**Simetrik eşleme.** Simetrik eşlemede `Z = 0` alınır ve ölçek `S = max|r| / 127` olur. Böylece `q` değerleri `[-127, 127]` aralığında ve sıfır tam olarak `0`'a eşlenir. Simetrik eşleme ağırlıklar için yaygındır, çünkü ağırlıklar genelde sıfır civarında simetrik dağılır ve tamsayı çarpımı için `Z` terimi hesaba katılmaz. Aktivasyonlarda ise (özellikle ReLU sonrası, tek taraflı aralıkta) asimetrik eşleme yarım aralığı boşa harcamaktan kurtarır; bunun sayısal etkisini Çözümlü Örnek 4'te göreceksin.

**Katman başına mı, kanal başına mı?** Katman başına (per-tensor) kuantizasyonda bir katmanın tüm ağırlıkları tek bir `S` ile ölçeklenir. Kanal başına (per-channel) kuantizasyonda her çıktı kanalının (yani `W` matrisinin her satırının) kendi `S`'si vardır. Kanal başına yöntem, satırlar arasında büyüklük farkı çoksa daha az hata verir; maliyeti ise her kanal için ayrı bir çarpan saklamaktır. Bu bölümde birinci katmanı kanal başına, ikinci katmanı katman başına kuantize ettik. İkinci katmanın tek ölçekli olmasının nedenini 46.5'in sonunda, argmax bahsinde açıklayacağız.

**Kalibrasyon: min/maks mı, yüzdelik mi?** Aralık `lo` ve `hi` değerlerini nereden alacağını kalibrasyon belirler. Eğitim verisinden geçirilen bir ileri geçişte aktivasyonların gözlenen en küçük ve en büyük değerleri (min/maks) en basit yöntemdir. Ama tek bir aykırı değer, tüm aralığı genişletip çözünürlüğü öldürebilir. Yüzdelik (percentile) kalibrasyonda `%0.1` ve `%99.9` gibi uç noktalar kırpılır; böylece aralık gerçek veri yoğunluğuna daha yakın olur. Bu farkın etkisini 46.6'da bit taraması ile ölçeceğiz.

**Eğitim sonrası ve eğitim sırasında kuantizasyon.** Bu bölümde yaptığımız, eğitim bittikten sonra uygulanan **eğitim sonrası kuantizasyon** (PTQ, post-training quantization) yöntemidir: model yeniden eğitilmez, yalnızca dönüştürülür. Doğruluk kaybı büyük olursa **kuantizasyon farkındalıklı eğitim** (QAT, quantization-aware training) kullanılır: eğitim sırasında ileri geçişte sahte kuantizasyon uygulanır ve ağ bu hataya uyum sağlar. QAT'in ayrıntısı genel bilgi olarak Bölüm 75'te gelecek.

**Tamsayı-only yeniden ölçekleme.** Kuantize edilmiş bir katmanın çıktısı, gerçekte şöyle hesaplanır. Girdi `x_q`, ağırlık `W_q` ve ölçekleri `S_in`, `S_w`, çıktı ölçeği `S_out` olsun. Birikim tamsayıdır:

`acc = b_q + Σ W_q · x_q`

Bu `acc` değeri, gerçek çıktının `S_in · S_w` ile çarpılmış hâlidir. Çıkışı int8 yapmak için yeniden ölçekleriz: `y = round(acc · m) + Z_out`, burada `m = S_in · S_w / S_out`. Sorun şu ki `m` bir kayan nokta sayısıdır. Bunu tamsayılarla yapmak için `m`'yi bir tamsayı ve bir kaydırma sayısına ayırırız: `m ≈ M0 / 2^rs`. Burada `M0`, `[2^30, 2^31)` aralığında bir tamsayıdır (Q31 biçiminde, yani `m`'nin mantisi), `rs` ise bir kaydırma sayısıdır. Bu ayrıştırma `math.frexp` ile yapılır: `m = mant · 2^e` ve `mant ∈ [0.5, 1)` ise `M0 = round(mant · 2^31)`, `rs = 31 - e`.

Sonuç olarak yeniden ölçekleme şu üç tamsayı işleminden oluşur: 64-bit çarpım `acc · M0`, yuvarlama sabitini ekleyip `rs` bit sağa kaydırma ve sıfır noktası ekleme ile doygunluk. Şekil 46.5 bu veri akışını gösteriyor.

![Şekil 46.5: int8 katman veri akışı: birikim, yeniden ölçekleme, kırpma](gorseller/b46_gemm.png)

Burada iki önemli hile daha var. Birincisi **sıfır noktasının katlanması**. `Σ (x_q - Z_in) W_q` ifadesini açarsan `Σ x_q W_q - Z_in Σ W_q` elde edersin. Sağdaki `Z_in Σ W_q` terimi girdiden bağımsızdır; bu yüzden derleme zamanında hesaplanıp onyargıya eklenir. Böylece çalışma zamanında çıkarma yapmak gerekmez. İkincisi **argmax'ın ölçek duyarlılığı**. Son katmanın logit'lerini sınıf seçmek için yalnızca karşılaştırıyorsun. Bu karşılaştırma doğru olsun diye tüm logit'lerin aynı ölçekte olması gerekir. Bu yüzden son katmanın ağırlıklarını kanal başına değil katman başına ölçekledik ve yeniden ölçekleme uygulamadık: tamsayı birikim doğrudan logit olarak kullanılır, `argmax` ise ortak pozitif bir ölçeğe duyarsızdır.

Bu bölümde yeniden ölçekleme `m` değerleri 0 ile 1 arasında ve `rs` değerleri 37 ile 38 arasında çıktı. Bu, `M0` değerinin 31 bit ve `rs`'nin 37 civarında olduğu anlamına gelir; 64-bit çarpım bu aralıkta taşmaz (`2^19 · 2^31 = 2^50 < 2^63`).

## 46.6 Kuantizasyonun doğruluğa etkisi: bit genişliği taraması

Kuantizasyonun gerçek maliyeti doğrulukta görünür. Bunu ölçmenin en sağlam yolu, aynı eğitilmiş modeli farklı bit genişlikleriyle **sahte kuantizasyon** (fake quantization) ile değerlendirmektir: sayılar float olarak tutulur, ama her değer önce kuantize edilip sonra geri çevrilir. Böylece bit genişliğinin doğruluk üzerindeki etkisi, tamsayı mühendisliğinden bağımsız olarak görülür. Aşağıdaki program bu taramayı yapar ve üç ölçüm sunar: yalnız ağırlıkların kuantize edildiği durum, ağırlık ile aktivasyonun birlikte min/maks kalibrasyonla kuantize edildiği durum ve aynı durumun yüzdelik kalibrasyonla ölçümü.

Önce programın kendisi:

```python
# -*- coding: utf-8 -*-
"""Bit genisligi taramasi: 8, 7, ... 2 bit (sahte kuantizasyon).

Olcumler (test seti, 2000 pencere):
  yalniz_agirlik : yalniz agirliklar kuantize, aktivasyonlar float
  minmax         : agirlik + girdi + ara aktivasyon, min/maks
                   kalibrasyon
  yuzdelik       : ayni, %0,1 ve %99,9 yuzdelik kalibrasyon
Cikti: engine/veri/b46_bit_dogruluk.csv
"""
import os
import numpy as np
from telemetri import veri_seti
from egit import ozellik_matrisi

HERE = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
f32 = np.float32
```

```python
def qdq_sim(W, bits, eksen=None):
    """Simetrik: Z=0, seviyeler -(2^(b-1)-1) .. 2^(b-1)-1."""
    lv = 2 ** (bits - 1) - 1
    if eksen is None:
        S = np.abs(W).max() / lv
    else:
        S = (np.abs(W).max(axis=eksen) / lv)[:, None]
    q = np.clip(np.round(W / S), -lv, lv)
    return (q * S).astype(f32)

def qdq_asim(x, lo, hi, bits):
    """Asimetrik: [lo, hi] araligi 2^b seviyeye.

    Sifir her zaman temsil edilir."""
    lo = min(lo, 0.0)
    hi = max(hi, 0.0)
    n = 2 ** bits - 1
    S = (hi - lo) / n
    Z = np.round(-lo / S)
    q = np.clip(np.round(x / S) + Z, 0, n)
    return ((q - Z) * S).astype(f32)
```

```python
def ileri_sim(Xn, p, bits_w, bits_a, lo_x, hi_x, lo_a, hi_a):
    W1 = p["W1"] if bits_w is None else qdq_sim(p["W1"], bits_w, 1)
    W2 = p["W2"] if bits_w is None else qdq_sim(p["W2"], bits_w)
    x = Xn if bits_a is None else qdq_asim(Xn, lo_x, hi_x, bits_a)
    z1 = x @ W1.T + p["b1"]
    a1 = np.maximum(z1, 0.0)
    if bits_a is not None:
        a1 = qdq_asim(a1, lo_a, hi_a, bits_a)
    return a1 @ W2.T + p["b2"]
```

```python
def main():
    Xtr, ytr, Xte, yte = veri_seti()
    npz = np.load(os.path.join(HERE, "model_f32.npz"))
    p = {k: npz[k] for k in ["W1", "b1", "W2", "b2", "mu", "sd"]}
    Ftr = ozellik_matrisi(Xtr)
    Fte = ozellik_matrisi(Xte)
    Xn_tr = ((Ftr.astype(f32) - p["mu"]) / p["sd"]).astype(f32)
    Xn_te = ((Fte.astype(f32) - p["mu"]) / p["sd"]).astype(f32)
    a1_tr = np.maximum(Xn_tr @ p["W1"].T + p["b1"], 0.0)

    lo_x, hi_x = Xn_tr.min(), Xn_tr.max()
    lo_a, hi_a = a1_tr.min(), a1_tr.max()
    lo_xp, hi_xp = np.percentile(Xn_tr, [0.1, 99.9])
    lo_ap, hi_ap = np.percentile(a1_tr, [0.1, 99.9])

    rows = []
    print("bit  yalniz_agirlik  minmax  yuzdelik")
    for b in [8, 7, 6, 5, 4, 3, 2]:
        z_w = ileri_sim(Xn_te, p, b, None, lo_x, hi_x, lo_a, hi_a)
        z_m = ileri_sim(Xn_te, p, b, b, lo_x, hi_x, lo_a, hi_a)
        z_p = ileri_sim(Xn_te, p, b, b, lo_xp, hi_xp, lo_ap, hi_ap)
        d_w = (z_w.argmax(axis=1) == yte).mean()
        d_m = (z_m.argmax(axis=1) == yte).mean()
        d_p = (z_p.argmax(axis=1) == yte).mean()
        rows.append((b, d_w, d_m, d_p))
        print("%d    %.4f           %.4f  %.4f" % (b, d_w, d_m, d_p))
    yol = os.path.join(VERI, "b46_bit_dogruluk.csv")
    with open(yol, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("bit,dogruluk_yalniz_agirlik,dogruluk_minmax,"
                 "dogruluk_yuzdelik\n")
        for b, d_w, d_m, d_p in rows:
            fh.write("%d,%.4f,%.4f,%.4f\n" % (b, d_w, d_m, d_p))
    print("CSV yazildi: engine/veri/b46_bit_dogruluk.csv")

if __name__ == "__main__":
    main()
```

Programı çalıştırdığında şu çıktıyı alırsın. Her satır bir bit genişliğini gösterir; ilk sütun yalnız ağırlık, ikinci sütun min/maks, üçüncü sütun yüzdelik kalibrasyondur.

```term
$ python bit_tara.py
bit  yalniz_agirlik  minmax  yuzdelik
8    0.9930           0.9930  0.9930
7    0.9930           0.9925  0.9930
6    0.9930           0.9925  0.9930
5    0.9930           0.6885  0.9925
4    0.9930           0.5250  0.6445
3    0.9930           0.4075  0.4615
2    0.8900           0.3135  0.3135
CSV yazildi: engine/veri/b46_bit_dogruluk.csv
```

Şekil 46.6 aynı tabloyu bir grafikte gösterir. Yalnız ağırlık kuantizasyonu, 4 bit'e kadar doğruluğu neredeyse hiç değiştirmiyor (0.9930) ve 2 bit'te yaklaşık 0.89'a düşüyor. Asıl kırılma aktivasyonlarda ortaya çıkıyor: min/maks kalibrasyonla 5 bit'te doğruluk 0.6885'e iniyor. Aynı bit genişliğinde yüzdelik kalibrasyon doğruluğu 0.9925'te tutuyor. Fark, aktivasyon aralığının aykırı değerlerle genişlemesinden kaynaklanır. Anomali penceresinde bir kanal, normal pencerelerden çok uzak bir değer verdiğinde (örneğin akım sıçraması), min/maks aralığı bu tek değere göre genişler ve geri kalan değerler birkaç seviyeye sıkışır. Yüzdelik kalibrasyon bu uç değerleri kırpar; kırpılan birkaç değer doğruluğu pek etkilemez, çünkü sınıflandırma kararı çoğu zaman bu uçlarda değil, ortalama davranışta verilir.

![Şekil 46.6: Bit genişliğine göre test doğruluğu: ağırlık ve aktivasyon kuantizasyonu](gorseller/b46_bit_dogruluk.png)

Bu grafikten çıkan pratik sonuç şudur: ağırlıkları 4 bite indirmek bu modelde ucuzdur, ama aktivasyonları indirirken kalibrasyon yöntemi belirleyicidir. Ayrıca bu sonuçlar sentetik veriye aittir; gerçek bir EV veri setinde kırılma noktası farklı olabilir. Ölçümü kendi verinle tekrarlamak, bu bölümün en önemli alıştırmalarından biridir.

## 46.7 Uçta veri ön işleme: pencere, öznitelik ve normalizasyon

Ham sensör verisi doğrudan modele verilmez. Önce bir pencere seçilir, sonra pencereden öznitelikler (özellikler) çıkarılır ve bu öznitelikler normalize edilir. Bu adımların her biri cihazda, model kadar dikkatle yazılmalıdır, çünkü eğitimde kullanılan işlemle cihazdaki işlem birebir aynı olmalıdır. Aksi halde model eğitim verisinde iyi, sahada kötü çalışır.

**Pencereleme.** Bir sensör 10 Hz'de örnek verirse, 32 örneklik bir pencere 3.2 saniyelik bir olaya karşılık gelir. Gerçek sistemde pencereler genelde kayan (ardışık pencereler birbirini örtüşür) ve dairesel bir tamponla (ring buffer) tutulur; bu tampon Bölüm 7'deki dizi ve indeks mantığının doğrudan uygulamasıdır. Bu bölümde pencereler sabit ve örtüşmesizdir; böylece hangi örneğin hangi pencereye ait olduğu açıktır.

**Öznitelikler.** Bir pencerede kanal başına beş istatistik hesapladık: ortalama, standart sapma, en küçük, en büyük ve eğim. Eğim, pencere boyunca doğrusal trendi yakalar; formülü en küçük kareler yöntemidir: `eğim = Σ (t - t̄)(x - x̄) / Σ (t - t̄)²`. Bu, bir sıcaklık ya da gerilimin yükselip yükselmediğini tek sayıyla söyler; termal arızada bu değer belirleyicidir. Öznitelikler dört kanalla birlikte 5 × 4 = 20 değer eder.

Öznitelik seçimi bir mühendislik kararıdır. Bir FFT (hızlı Fourier dönüşümü) ile frekans bandı enerjisi de çıkarılabilir; bu, Bölüm 52'deki DSP temellerinin ve Bölüm 19'daki bölme-fethet fikrinin (FFT bir bölme-fethet algoritmasıdır) doğrudan uygulamasıdır. Ancak FFT'nin `N log N` maliyeti, bu tür bir MCU'da pencere başına ek birkaç bin çevrim demektir. Bu bölümde yalnızca istatistik kullandık, çünkü bunlar tek geçişte hesaplanır ve sonuç yeterince ayırt edicidir.

**Normalizasyon.** Öznitelikler farklı ölçekte olabilir: gerilim birkaç volt, akım onlarca amper, devir yüzlerce rpm olabilir. Model için bunları aynı ölçeğe getirmek gerekir: `v = (x - μ) / σ`. Buradaki `μ` ve `σ` yalnızca **eğitim verisinden** hesaplanır ve modelle birlikte cihaza kopyalanır. Test verisinden ya da sahadan kendi ortalamanı hesaplarsan, model eğitimde görmediği bir dağılımla karşılaşır; bu, Bölüm 77'de göreceğin dağılım kayması (drift) sorununun en basit biçimidir.

**Girdinin kuantizasyonu.** Normalize edilmiş öznitelik float olarak gelir ve int8'e çevrilir: `q = floor(v / S_in + 0.5) + Z_in`, sonra `[-128, 127]`'ye kırpılır. Burada yuvarlamanın yönü ile sonucun her yerde aynı olması kritiktir. Bu bölümde Python referansı ile C kodu aynı float32 işlem sırasını kullanır; sonuç olarak tüm test vektörlerinde girdi kuantizasyonu bit-tam eşleşti (test çıktısına bakabilirsin). Bu eşleşmeyi sağlamak, bir sonraki bölümde tekrar karşımıza çıkacak olan "sayısal uyum" sorununun ilk örneğidir.

## 46.8 Derleme hattı ve çalışma zamanı çatıları

Bir modelin cihaza ulaşması için bir dönüşüm hattından geçmesi gerekir. Şekil 46.7 bu hattı altı adımda gösteriyor: eğitim, dışa aktarma, kuantizasyon, C dizisi üretimi, derleme ve doğrulama. Bu bölümde bu hattın her adımını kendimiz yazdık; böylece her dönüşümün ne yaptığını görebiliyorsun.

![Şekil 46.7: Eğit, dışa aktar, kuantize et, derle, doğrula: model dönüşüm hattı](gorseller/b46_hat.png)

Gerçek projelerde bu hattın büyük kısmını bir çatı (framework) yapar. **TensorFlow Lite Micro (TFLM)** bunun en yaygın örneğidir (genel bilgi): modeli bir flatbuffer dosyasında taşır, bir yorumlayıcı (interpreter) modelin operatörlerini sırayla çalıştırır ve tüm ara tamponları önceden ayrılmış tek bir bellek alanından (tensor arena) dağıtır. Operatör çözücü (op resolver), modelde hangi işlemlerin bulunduğunu derleme anında seçmenizi sağlar; böylece kullanılmayan operatörler flash'a girmez. **CMSIS-NN** ise ARM'ın Cortex-M için optimize ettiği çekirdek kütüphanesidir (genel bilgi): evrişim ve tam bağlı katmanlar için SIMD tabanlı, tamsayı-only yeniden ölçekleme içeren fonksiyonlar sunar. Kod Okuma bölümünde bu kütüphanenin yeniden ölçekleme fonksiyonunu okuyacaksın.

Bizim yaklaşımımızın farkı, her parçanın açık olmasıdır. Modelin sabit dizileri `model_int8.h` içinde duruyor, çekirdek (`tinyml.c`) bu dizileri doğrudan okuyor, hiçbir dinamik bellek kullanılmıyor. Bu, Bölüm 25'te gördüğün statik bellek disiplininin uygulamasıdır: her tampon derleme zamanında bilinen bir boyuttadır ve bir `malloc` çağrısı yoktur. Bir çatı kullanmak bu yükü azaltır ama bellek ve davranış üzerindeki kontrolünü de azaltır. Savunma sanayiinde, bir sistemin hangi bellekte ne yaptığını bilmek çoğu zaman doğruluğun kendisi kadar önemlidir.

## 46.9 Uygulama 1: EV telemetri anomali tespiti, uçtan uca

Bu bölümün ana uygulamasını Mert'in EV Dashboard projesinden esinlendik. O projede bir elektrikli aracın BMS ve motor telemetrisinden anomali aramak söz konusu. Burada aynı fikri küçük ve tam kontrol edilebilir bir ölçekte kuruyoruz: dört kanal (hücre gerilimi, hücre sıcaklığı, akım ve motor devri), her biri 32 örneklik pencere ve iki sınıf (normal, anomali).

**Önemli bir not:** Kullandığımız veri gerçek değildir. Bir programla, sabit bir tohum (46) ile üretilmiş sentetik pencerelerdir. Normal pencereler, her kanal için makul bir taban değer ve küçük bir gürültü içerir. Anomali pencerelerinde dört tipten biri uygulanır: gerilimde kademeli çökme, sıcaklıkta yükselme, kısa akım sıçramaları ve devirde düşme. Şiddet her pencerede rastgele seçilir; zor örnekler (düşük şiddet) bilerek veri setinde yer alır. Bu veri, mühendislik akışını göstermek için vardır; sonuçları bir aracın gerçek güvenliği için yorumlayamazsın.

Hattın adımlarını sırayla izleyeceğiz: veri üretimi, eğitim, kuantizasyon, C çekirdeği, host üzerinde bit-tam doğrulama, Cortex-M4 derlemesi ve ölçümler. Her adımda kodun tamamını ve çıktısını göreceksin.

### Adım A: Sentetik telemetri üretimi

İlk program veri üreticisidir. Her pencere bir `(32, 4)` matrisidir; satırlar zamanı, sütunlar kanalları gösterir. Ardından her pencere için 20 öznitelik çıkarılır: dört kanalın her biri için ortalama, standart sapma, en küçük, en büyük ve eğim. Öznitelik sırası `tür · 4 + kanal` biçimindedir; bu sıra C kodunda da aynen kullanılacak.

```python
# -*- coding: utf-8 -*-
"""Sentetik EV telemetri pencereleri. GERCEK VERI DEGILDIR.

Dort kanal, her pencerede L = 32 ornek (10 Hz, 3,2 saniye):
  kanal 0: hucre gerilimi  [V]
  kanal 1: hucre sicakligi [derece C]
  kanal 2: akim            [A]
  kanal 3: motor devri     [rpm / 100]

Ozellik vektoru (20 deger): 5 istatistik x 4 kanal.
Sira: [ort(4), std(4), min(4), maks(4), egim(4)].
Indeks = tur*4 + kanal.
"""
import numpy as np

L = 32
KANAL = 4
NOZ = 20
TOHUM = 46

def normal_pencere(rng):
    t = np.arange(L) / 10.0
    v = rng.uniform(3.55, 3.85) + rng.normal(0.0, 0.004, L)
    T0 = rng.uniform(25.0, 40.0)
    drift = 0.01 * rng.uniform(0, 1) * np.arange(L)
    T = T0 + rng.normal(0.0, 0.08, L) + drift
    I0 = rng.uniform(20.0, 80.0)
    frek = rng.uniform(0.8, 2.0)
    faz = rng.uniform(0, 2 * np.pi)
    I = I0 + 0.1 * I0 * np.sin(2 * np.pi * frek * t + faz)
    I = I + rng.normal(0.0, 1.0, L)
    n = rng.uniform(15.0, 40.0) + rng.normal(0.0, 0.2, L)
    return np.stack([v, T, I, n], axis=1)
```

Veri üreticisinin ikinci yarısı, normal ve anomali pencerelerini üreten fonksiyonları içerir. Anomali tipi `rng.integers(0, 4)` ile seçilir ve şiddet `[0.4, 1.0]` aralığında çekilir.

```python

def anomali_uygula(p, rng):
    p = p.copy()
    tip = rng.integers(0, 4)
    siddet = rng.uniform(0.4, 1.0)  # 0.4 zor, 1.0 belirgin
    if tip == 0:  # gerilim cokmesi (hucre dengesizligi)
        rampa = np.linspace(0, 1, L)
        p[:, 0] -= siddet * rng.uniform(0.10, 0.30) * rampa
    elif tip == 1:  # termal yukselme (sogutma arizasi)
        rampa = np.linspace(0, 1, L) ** 1.5
        p[:, 1] += siddet * rng.uniform(6, 18) * rampa
    elif tip == 2:  # akim sicramasi (kisa sureli)
        for _ in range(rng.integers(1, 4)):
            s = rng.integers(0, L - 2)
            p[s:s + 2, 2] += siddet * rng.uniform(40, 90)
    else:  # devir dusmesi (kismi takilma)
        s = rng.integers(0, L // 2)
        p[s:, 3] -= siddet * rng.uniform(5, 15)
    return p

def ozellik(p):
    """(L, 4) pencereden 20 ozellik. Egim: en kucuk kareler."""
    t = np.arange(L) - (L - 1) / 2.0
    ort = p.mean(axis=0)
    std = p.std(axis=0)
    mn = p.min(axis=0)
    mx = p.max(axis=0)
    egim = (t[:, None] * (p - ort)).sum(axis=0) / (t ** 2).sum()
    return np.concatenate([ort, std, mn, mx, egim])
```

Son kısım eğitim ve test kümelerini oluşturur. Tohum sabit olduğu için her çalıştırmada aynı veri çıkar; bu, sonuçların tekrarlanabilirliğinin ilk şartıdır.

```python
def veri_uret(n, rng, anomali_orani=0.3):
    X = np.zeros((n, L, KANAL))
    y = (rng.uniform(size=n) < anomali_orani).astype(np.int64)
    for i in range(n):
        p = normal_pencere(rng)
        if y[i] == 1:
            p = anomali_uygula(p, rng)
        X[i] = p
    return X, y

def veri_seti():
    """Egitim (4000) ve test (2000) pencereleri; tohum sabit (46)."""
    rng = np.random.default_rng(TOHUM)
    Xtr, ytr = veri_uret(4000, rng)
    Xte, yte = veri_uret(2000, rng)
    return Xtr, ytr, Xte, yte

if __name__ == "__main__":
    Xtr, ytr, Xte, yte = veri_seti()
    F = np.array([ozellik(p) for p in Xte])
    print("egitim:", Xtr.shape, "anomali:", ytr.mean().round(3))
    print("test  :", Xte.shape, "anomali:", yte.mean().round(3))
    print("ilk ozellik vektoru (test[0]):")
    print(np.round(F[0], 3))
```

Programı çalıştırdığında eğitim ve test kümelerinin boyutlarını ve anomali oranlarını, ayrıca bir test penceresinin 20 öznitelik değerini görürsün.

```term
$ python telemetri.py
egitim: (4000, 32, 4) anomali: 0.312
test  : (2000, 32, 4) anomali: 0.314
ilk ozellik vektoru (test[0]):
[ 3.5530e+00  2.7580e+01  1.9739e+01  1.7040e+01  4.0000e-03  6.8000e-02
  1.5100e+00  1.7500e-01  3.5440e+00  2.7429e+01  1.6779e+01  1.6760e+01
  3.5610e+00  2.7708e+01  2.2103e+01  1.7386e+01  0.0000e+00  1.0000e-03
 -2.4000e-02 -0.0000e+00]
```

Çıktıda anomali oranı yaklaşık yüzde 31'dir; bu, üretim sırasında seçilen olasılık (0.3) ile uyumludur. Öznitelik vektörünün ilk dört değeri kanal başına ortalamalardır: gerilim yaklaşık 3.55 V, sıcaklık yaklaşık 27.6 °C, akım yaklaşık 19.7 A (ölçeklenmemiş), devir yaklaşık 1700 rpm (100'e bölünmüş değer 17.0). Eğim değerleri (son dört değer) bu pencerede sıfıra yakındır; yani bu pencere normaldir.

### Adım B: Eğitim (numpy ile sıfırdan)

Model, 20 girdili, 8 ReLU birimli gizli katmanı ve 2 çıktılı bir MLP'dir. Eğitimde softmax çapraz entropi kaybı kullanılır ve geri yayılım (backpropagation) elle yazılmıştır: çıktı katmanındaki hata, zincir kuralıyla gizli katmana ve oradan girdi ağırlıklarına taşınır. Bu türev hesabının ayrıntısı Bölüm 55 ve Bölüm 63'te; burada yalnızca kodun ne yaptığını görmen yeterli. Eğitim, mini-parti (batch 64) gradyan inişi ile 80 dönem (epoch) boyunca çalışır ve öğrenme oranı 0.1'dir.

```python
# -*- coding: utf-8 -*-
"""20 -> 8 (ReLU) -> 2 (logit) MLP, numpy ile sifirdan egitim.

Gradyan inisi: softmax capraz entropi kaybi.
Geri yayilim elle yazildi.
Tohum sabit (46). Cikti: model_f32.npz (float32 parametreler).
"""
import numpy as np
from telemetri import veri_seti, ozellik

TOHUM = 46
NIN, NH, NOUT = 20, 8, 2

def ozellik_matrisi(X):
    return np.array([ozellik(p) for p in X])

def ileri(x, W1, b1, W2, b2):
    """x: (B, 20). Doner: z1, a1, z2."""
    z1 = x @ W1.T + b1
    a1 = np.maximum(z1, 0.0)
    z2 = a1 @ W2.T + b2
    return z1, a1, z2

def softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)
```

Eğitim döngüsü, her dönemde bir mini parti üzerinde ileri geçişi, kayıp türevini ve ağırlık güncellemesini yapar. Her 20 dönemde bir kayıp ve doğruluk yazdırılır.

```python
def egit(xtr, ytr, epoch=80, lr=0.1, bs=64):
    rng = np.random.default_rng(TOHUM)
    W1 = rng.normal(0, np.sqrt(2.0 / NIN), (NH, NIN))
    b1 = np.zeros(NH)
    W2 = rng.normal(0, np.sqrt(1.0 / NH), (NOUT, NH))
    b2 = np.zeros(NOUT)
    n = len(xtr)
    for ep in range(epoch):
        sira = rng.permutation(n)
        for k in range(0, n, bs):
            idx = sira[k:k + bs]
            x, y = xtr[idx], ytr[idx]
            z1, a1, z2 = ileri(x, W1, b1, W2, b2)
            p = softmax(z2)
            p[np.arange(len(y)), y] -= 1.0      # dKayip/dz2
            dz2 = p / len(y)
            dW2 = dz2.T @ a1
            db2 = dz2.sum(axis=0)
            da1 = dz2 @ W2
            dz1 = da1 * (z1 > 0)
            dW1 = dz1.T @ x
            db1 = dz1.sum(axis=0)
            W1 -= lr * dW1
            b1 -= lr * db1
            W2 -= lr * dW2
            b2 -= lr * db2
        if ep % 20 == 19 or ep == 0:
            _, _, z2 = ileri(xtr, W1, b1, W2, b2)
            olas = softmax(z2)[np.arange(n), ytr]
            kayip = -np.log(olas + 1e-12).mean()
            dog = (z2.argmax(axis=1) == ytr).mean()
            print("epoch %3d  kayip %.4f  egitim dogrulugu %.4f"
                  % (ep + 1, kayip, dog))
    return W1, b1, W2, b2
```

Son kısım veriyi yükler, öznitelikleri standartlaştırır ve parametreleri `model_f32.npz` dosyasına kaydeder. Bu dosya, sonraki kuantizasyon adımının tek girdisidir.

```python
if __name__ == "__main__":
    Xtr, ytr, Xte, yte = veri_seti()
    Ftr = ozellik_matrisi(Xtr)
    Fte = ozellik_matrisi(Xte)
    mu = Ftr.mean(axis=0)
    sd = Ftr.std(axis=0) + 1e-8          # sifira bolunmeyi onler
    xtr = (Ftr - mu) / sd
    xte = (Fte - mu) / sd
    W1, b1, W2, b2 = egit(xtr, ytr)
    _, _, z2 = ileri(xte, W1, b1, W2, b2)
    dog = (z2.argmax(axis=1) == yte).mean()
    print("test dogrulugu (float64): %.4f" % dog)
    f32 = lambda a: a.astype(np.float32)
    np.savez("model_f32.npz", W1=f32(W1), b1=f32(b1), W2=f32(W2),
             b2=f32(b2), mu=f32(mu), sd=f32(sd))
    print("model_f32.npz yazildi")
```

```term
$ python egit.py
epoch   1  kayip 0.1115  egitim dogrulugu 0.9765
epoch  20  kayip 0.0338  egitim dogrulugu 0.9932
epoch  40  kayip 0.0317  egitim dogrulugu 0.9932
epoch  60  kayip 0.0305  egitim dogrulugu 0.9940
epoch  80  kayip 0.0300  egitim dogrulugu 0.9940
test dogrulugu (float64): 0.9930
model_f32.npz yazildi
```

Çıktıdan görüldüğü gibi kayıp 0.11'den 0.030'a iner ve test doğruluğu yaklaşık yüzde 99.3'tür. Bu oran, sentetik verinin kolay olmasının da bir sonucudur; anomali şiddeti düşük örnekler az olduğu için model bu kadar yüksek doğruluk verir. Gerçek bir veri setinde bu sayıyı beklememelisin.

### Adım C: Kuantizasyon ve C'ye aktarma

Kuantizasyon programı üç işi yapar. Birincisi, eğitim verisinden aktivasyon ve girdi aralıklarını (kalibrasyon) bulur ve her katman için ölçek ile sıfır noktasını hesaplar. İkincisi, ağırlıkları int8'e çevirir ve onyargıları, sıfır noktası terimini katlayarak tamsayı onyargılarına dönüştürür. Üçüncüsü, her çıktı kanalı için yeniden ölçekleme çarpanı `M0` ile kaydırma sayısı `rs`'yi hesaplar. Ardından bu değerleri C başlık dosyasına yazar.

Program ayrıca, tamsayı çıkarımın referans değerlerini (test pencerelerinin int8 girdileri ve beklenen logit'ler) ve tam aralıklı rastgele int8 vektörleri ikili dosyalara yazar. Bu dosyalar C testinin doğru cevabıdır.

```python
# -*- coding: utf-8 -*-
"""float32 -> int8 kuantizasyon, tamsayi referans, C aktarimi.

Afin esleme:  r = S * (q - Z),  q in [-128, 127]
Girdi: asimetrik, katman basina; kalibrasyon min/maks ya da yuzdelik.
Agirliklar: simetrik (Z = 0). 1. katmanda kanal basina olcek, 2.
katmanda tek olcek (logit'ler ayni olcekte olsun diye).
Yeniden olcekleme: m = S_in * S_w / S_cikis = M0 / 2^rs, M0 Q31.
"""
import math
import os
import numpy as np
from telemetri import veri_seti
from egit import ozellik_matrisi

HERE = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
f32 = np.float32
```

Aşağıdaki kısım, kalibrasyon ve eşlemeyi uygular. `asimetrik` fonksiyonu 0'ın tam temsilini garanti eder; `m_ayristir` ise `m` çarpanını `M0` ve `rs`'ye ayırır.

```python
def asimetrik(lo, hi):
    """int8 icin (S, Z). Sifir her zaman temsil edilir."""
    lo = min(float(lo), 0.0)
    hi = max(float(hi), 0.0)
    if hi - lo < 1e-9:
        hi = lo + 1e-6
    S = f32((hi - lo) / 255.0)
    Z = int(np.clip(np.round(-128 - lo / float(S)), -128, 127))
    return S, Z

def simetrik_olcek(W, eksen=None):
    """Simetrik int8 olcegi: S = max|W| / 127 (Z = 0)."""
    if eksen is None:
        return f32(np.abs(W).max() / 127.0)
    return f32(np.abs(W).max(axis=eksen) / 127.0)

def agirlik_kuantize(W, S):
    Sb = S if np.ndim(S) == 0 else S[:, None]
    q = np.round(W / Sb)
    return np.clip(q, -127, 127).astype(np.int64)

def m_ayristir(m):
    """m (0,1) -> (M0, rs): m ~ M0 / 2^rs, M0 in [2^30, 2^31)."""
    mant, e = math.frexp(m)
    M0 = int(round(mant * 2 ** 31))
    if M0 == 2 ** 31:
        M0 //= 2
        e += 1
    rs = 31 - e
    assert rs >= 1, "rs < 1: m cok buyuk"
    return M0, rs
```

Kalibrasyon fonksiyonu eğitim verisinden aralıkları çıkarır; `modeli_kuantize` ise bu aralıklarla bütün parametreleri hazırlar. Bu fonksiyon bir sözlük döndürür; içinde hem tamsayı ağırlıklar hem de yeniden ölçekleme sabitleri bulunur.

```python
def kalibre_et(W1, b1, Xn, kalib="minmax"):
    """Egitim verisinin float32 ileri gecisiyle araliklar."""
    a1 = np.maximum(Xn @ W1.T + b1, 0.0)
    if kalib == "minmax":
        aralik_x = (Xn.min(), Xn.max())
        aralik_a = (a1.min(), a1.max())
    else:  # yuzdelik: uc noktalar kirpilir
        aralik_x = tuple(np.percentile(Xn, [0.1, 99.9]))
        aralik_a = tuple(np.percentile(a1, [0.1, 99.9]))
    return aralik_x, aralik_a
```

```python
def modeli_kuantize(p, Xn_train, kalib="minmax", kanal_basina=True):
    W1, b1, W2, b2 = p["W1"], p["b1"], p["W2"], p["b2"]
    (lo_x, hi_x), (lo_a, hi_a) = kalibre_et(W1, b1, Xn_train, kalib)
    S_in, Z_in = asimetrik(lo_x, hi_x)
    S_a1, Z_a1 = asimetrik(lo_a, hi_a)
    if kanal_basina:
        S_w1 = simetrik_olcek(W1, eksen=1)
    else:
        S_w1 = np.full(W1.shape[0], simetrik_olcek(W1), dtype=f32)
    S_w2 = simetrik_olcek(W2)
    W1q = agirlik_kuantize(W1, S_w1)
    W2q = agirlik_kuantize(W2, S_w2)
    # Onyargi: b_q = b / (S_in*S_w). Z_in terimi onyargiya katlanir:
    # sum (x - Z) w + b_q = sum x w + (b_q - Z * sum w)
    B1q = np.round(b1.astype(np.float64)
                   / (S_in * S_w1.astype(np.float64)))
    B1f = B1q.astype(np.int64) - Z_in * W1q.sum(axis=1)
    B2q = np.round(b2.astype(np.float64)
                   / (float(S_a1) * float(S_w2)))
    B2f = B2q.astype(np.int64) - Z_a1 * W2q.sum(axis=1)
    M1, RS1 = [], []
    for i in range(W1.shape[0]):
        m = float(S_in) * float(S_w1[i]) / float(S_a1)
        M0, rs = m_ayristir(m)
        M1.append(M0)
        RS1.append(rs)
    return dict(S_in=S_in, Z_in=Z_in, S_a1=S_a1, Z_a1=Z_a1,
                S_w1=S_w1, S_w2=S_w2, W1q=W1q, W2q=W2q, B1f=B1f,
                B2f=B2f, M1=np.array(M1, dtype=np.int64),
                RS1=np.array(RS1, dtype=np.int64),
                mu=p["mu"], sd=p["sd"])
```

Tamsayı çıkarım fonksiyonu, C çekirdeğinin birebir referansıdır. Burada `np.int64` kullanılır; böylece 64-bit çarpım taşmaz ve sonuç C'deki `int64_t` hesabıyla aynı olmalıdır.

```python
def girdi_kuantize(F, Q):
    """Ham ozellik (float32) -> int8 girdi. C ile ayni sira."""
    v = ((F.astype(f32) - Q["mu"]) / Q["sd"]).astype(f32)
    w = (v / Q["S_in"]).astype(f32)
    q = np.floor(w + f32(0.5)).astype(np.int64) + Q["Z_in"]
    return np.clip(q, -128, 127).astype(np.int64)

def int_ileri(xq, Q):
    """Tam tamsayi cikarim.

    Doner: a1 (int8 degerler), logit (int32)."""
    acc1 = Q["W1q"] @ xq + Q["B1f"]
    y1 = acc1 * Q["M1"] + np.left_shift(np.int64(1), Q["RS1"] - 1)
    y1 = np.right_shift(y1, Q["RS1"])
    a1 = np.clip(y1 + Q["Z_a1"], Q["Z_a1"], 127)
    logit = Q["W2q"] @ a1 + Q["B2f"]
    return a1, logit

def float_ileri(xn, p):
    """Ayni yapi, float32 (kuantizasyon oncesi referans)."""
    a1 = np.maximum(xn @ p["W1"].T + p["b1"], 0.0)
    return a1 @ p["W2"].T + p["b2"]

def float_p(npz):
    return {k: npz[k] for k in ["W1", "b1", "W2", "b2", "mu", "sd"]}
```

Aşağıdaki kısım, sınıf ölçütlerini ve C başlık dosyasının yazıcısını içerir. Başlık dosyası, sabit dizileri 70 sütuna sığacak şekilde biçimlendirir.

```python
def sinif_metrik(y, tahmin):
    tp = int(((tahmin == 1) & (y == 1)).sum())
    fp = int(((tahmin == 1) & (y == 0)).sum())
    fn = int(((tahmin == 0) & (y == 1)).sum())
    tn = int(((tahmin == 0) & (y == 0)).sum())
    pre = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    return pre, rec, (tn, fp, fn, tp)

def dizi_satirlari(ad, tip, degerler, kesim=66):
    """Degerleri en fazla 70 sutunluk C dizisi satirlarina boler."""
    parcalar = [str(v) for v in degerler]
    satirlar, cur = [], ""
    for k, s in enumerate(parcalar):
        ek = s + (", " if k < len(parcalar) - 1 else "")
        if len(cur) + len(ek) > kesim:
            satirlar.append(cur.rstrip())
            cur = ""
        cur += ek
    satirlar.append(cur.rstrip())
    govde = "\n    ".join(satirlar)
    return "static const %s %s[%d] = {\n    %s\n};\n\n" % (
        tip, ad, len(parcalar), govde)
```

```python
def disa_aktar(Q, yol):
    """model_int8.h: agirliklar, onyargi, M0, rs, sabitler."""
    W1, W2 = Q["W1q"], Q["W2q"]
    nh, nin = W1.shape
    nout = W2.shape[0]
    out = ["/* Otomatik uretildi: kuantize.py.\n",
           "   Elle degistirmeyin. */\n",
           "#ifndef TM_MODEL_INT8_H\n#define TM_MODEL_INT8_H\n\n",
           "#include <stdint.h>\n\n",
           "#define TM_NIN %d\n#define TM_NH %d\n#define TM_NOUT %d\n"
           % (nin, nh, nout),
           "#define TM_ZIN (%d)\n#define TM_ZA1 (%d)\n\n"
           % (Q["Z_in"], Q["Z_a1"]),
           "static const float TM_SIN = %.9ef;\n\n"
           % float(Q["S_in"])]
    out.append(dizi_satirlari("TM_MU", "float",
                              ["%.9ef" % v for v in Q["mu"]]))
    out.append(dizi_satirlari("TM_SD", "float",
                              ["%.9ef" % v for v in Q["sd"]]))
    out.append(dizi_satirlari("TM_W1", "int8_t", W1.reshape(-1)))
    out.append(dizi_satirlari("TM_B1", "int32_t", Q["B1f"]))
    out.append(dizi_satirlari("TM_M1", "int32_t", Q["M1"]))
    out.append(dizi_satirlari("TM_RS1", "int32_t", Q["RS1"]))
    out.append(dizi_satirlari("TM_W2", "int8_t", W2.reshape(-1)))
    out.append(dizi_satirlari("TM_B2", "int32_t", Q["B2f"]))
    out.append("#endif\n")
    with open(yol, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(out))
```

Ana fonksiyon önce float ve int8 doğruluklarını karşılaştırır, ardından seçilen varyantı C'ye aktarır ve test dosyalarını yazar.

```python
def main():
    Xtr, ytr, Xte, yte = veri_seti()
    Ftr = ozellik_matrisi(Xtr)
    Fte = ozellik_matrisi(Xte)
    p = float_p(np.load(os.path.join(HERE, "model_f32.npz")))
    mu, sd = p["mu"], p["sd"]
    Xn_tr = ((Ftr.astype(f32) - mu) / sd).astype(f32)

    z2_f = float_ileri(((Fte.astype(f32) - mu) / sd).astype(f32), p)
    print("float32 test dogrulugu:      %.4f"
          % (z2_f.argmax(axis=1) == yte).mean())

    variantlar = [("kanal basina, minmax", True, "minmax"),
                  ("katman basina, minmax", False, "minmax"),
                  ("kanal basina, yuzdelik", True, "yuzdelik")]
    for ad, kanal, kal in variantlar:
        Qv = modeli_kuantize(p, Xn_tr, kal, kanal)
        tah = np.array([int_ileri(girdi_kuantize(Fte[i], Qv), Qv)[1]
                        .argmax() for i in range(len(Xte))])
        print("int8 (%-24s) dogruluk: %.4f"
              % (ad, (tah == yte).mean()))
    # Secilen varyant (kanal basina, minmax) C'ye aktarilir
    Q = modeli_kuantize(p, Xn_tr, "minmax", True)
```

```python
    rows = []
    for i in range(len(Xte)):
        xq = girdi_kuantize(Fte[i], Q)
        a1, lg = int_ileri(xq, Q)
        rows.append((xq, a1, lg))
    lg_int = np.array([r[2] for r in rows]) * float(Q["S_a1"]) \
        * float(Q["S_w2"])
    fark = np.abs(lg_int - z2_f)
    print("max |logit_int8 - logit_f32|: %.4f" % fark.max())
    print("ortalama |fark|:              %.4f" % fark.mean())
    tah = np.array([r[2].argmax() for r in rows])
    print("argmax uyumu (int8 vs f32):   %.4f"
          % (tah == z2_f.argmax(axis=1)).mean())
    pre, rec, cm = sinif_metrik(yte, tah)
    print("int8 anomali: kesinlik %.4f, duyarlilik %.4f" % (pre, rec))
    print("karisiklik (tn, fp, fn, tp):", cm)

    skor_i8 = np.array([r[2][1] - r[2][0] for r in rows]) \
        * float(Q["S_a1"]) * float(Q["S_w2"])
    skor_f = z2_f[:, 1] - z2_f[:, 0]
    with open(os.path.join(VERI, "b46_anomali.csv"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("etiket,skor_f32,skor_int8\n")
        for e, a, b in zip(yte, skor_f, skor_i8):
            fh.write("%d,%.6f,%.6f\n" % (e, a, b))
```

```python
    disa_aktar(Q, os.path.join(HERE, "model_int8.h"))
    XQ = np.array([r[0] for r in rows])
    BEK = np.array([[yte[i], r[2][0], r[2][1]]
                    for i, r in enumerate(rows)], dtype=np.int32)
    XQ.astype(np.int8).tofile(os.path.join(HERE, "test_xq.bin"))
    BEK.tofile(os.path.join(HERE, "test_beklenen.bin"))
    yol = os.path.join(HERE, "test_ozellik.bin")
    Fte.astype(np.float32).tofile(yol)
    yol = os.path.join(HERE, "test_pencere.bin")
    Xte.astype(np.float32).tofile(yol)
    # Tam aralikli rastgele int8 girdiler (tasma/doygunluk sinamasi)
    rng = np.random.default_rng(46)
    vecs = [np.full(20, -128), np.full(20, 127),
            np.tile([-128, 127], 10)]
    vecs += [rng.integers(-128, 128, 20) for _ in range(997)]
    RXQ = np.array(vecs, dtype=np.int64)
    RBEK = np.array([int_ileri(x, Q)[1] for x in RXQ], dtype=np.int32)
    RXQ.astype(np.int8).tofile(os.path.join(HERE, "test_r_xq.bin"))
    RBEK.tofile(os.path.join(HERE, "test_r_beklenen.bin"))
    print("rastgele vektor:", len(RXQ), "logit araligi:",
          int(RBEK.min()), int(RBEK.max()))
```

Son kısım, tam aralıklı rastgele girdi testini ve yazdırma kısmını içerir.

```python
    print("C dosyalari yazildi: model_int8.h, test_*.bin")
    print("S_in=%.6g Z_in=%d S_a1=%.6g Z_a1=%d" % (
        Q["S_in"], Q["Z_in"], Q["S_a1"], Q["Z_a1"]))
    for i, (m0, rs) in enumerate(zip(Q["M1"], Q["RS1"])):
        print("kanal %d: M0 = %d, rs = %d" % (i, m0, rs))

if __name__ == "__main__":
    main()
```

```term
$ python kuantize.py
float32 test dogrulugu:      0.9930
int8 (kanal basina, minmax    ) dogruluk: 0.9930
int8 (katman basina, minmax   ) dogruluk: 0.9930
int8 (kanal basina, yuzdelik  ) dogruluk: 0.9930
max |logit_int8 - logit_f32|: 0.5661
ortalama |fark|:              0.1100
argmax uyumu (int8 vs f32):   1.0000
int8 anomali: kesinlik 1.0000, duyarlilik 0.9777
karisiklik (tn, fp, fn, tp): (1373, 0, 14, 613)
rastgele vektor: 1000 logit araligi: -45319 66391
C dosyalari yazildi: model_int8.h, test_*.bin
S_in=0.0819739 Z_in=7 S_a1=0.0522158 Z_a1=-128
kanal 0: M0 = 1362398346, rs = 37
kanal 1: M0 = 1111630342, rs = 37
kanal 2: M0 = 1950243921, rs = 37
kanal 3: M0 = 1974131210, rs = 37
kanal 4: M0 = 1375567070, rs = 37
kanal 5: M0 = 1455104087, rs = 38
kanal 6: M0 = 1921711117, rs = 37
kanal 7: M0 = 1710252355, rs = 37
```

Çıktıda ilk satırlar float32 ve int8 doğruluklarını gösterir; üç varyant da yüzde 99.3'te eşittir. Bu, sentetik veride kanal başına ile katman başına ölçeklemenin ayırt edilemediği anlamına gelir; gerçek veride fark çıkabilir. Logit farkı en fazla 0.57 ve ortalama 0.11'dir, ama argmax uyumu yüzde yüzdür: yani tamsayı ağ, float ağın verdiği sınıf kararını her pencerede aynı verir. Anomali sınıfında kesinlik 1.0, duyarlılık yaklaşık 0.978'dir; yani 627 anomali penceresinden 14'ü kaçırılmıştır.

Model başlık dosyasının başı şöyledir. Dosyanın geri kalanı aynı biçimde sabit dizileri içerir; tam dosyayı programın üretmesi yeterlidir.

```c
/* Otomatik uretildi: kuantize.py.
   Elle degistirmeyin. */
#ifndef TM_MODEL_INT8_H
#define TM_MODEL_INT8_H

#include <stdint.h>

#define TM_NIN 20
#define TM_NH 8
#define TM_NOUT 2
#define TM_ZIN (7)
#define TM_ZA1 (-128)

static const float TM_SIN = 8.197394758e-02f;

static const float TM_MU[20] = {
    3.695642233e+00f, 3.281343460e+01f, 5.032714081e+01f,
    2.699958801e+01f, 6.977423094e-03f, 3.008534610e-01f,
    4.553880692e+00f, 3.785285056e-01f, 3.682279348e+00f,
    3.234998703e+01f, 4.384639359e+01f, 2.646095085e+01f,
    3.708997488e+00f, 3.340738678e+01f, 5.970183182e+01f,
    2.776323509e+01f, -3.657392517e-04f, 2.754088119e-02f,
    -3.566999920e-03f, -1.573983952e-02f
};
```

Dikkat edilmesi gereken iki nokta var. `TM_RS1` dizisinin tamamı 37 ya da 38 değerindedir, yani çarpanlar birbirine çok yakındır. Ve `TM_ZA1` değeri -128'dir: birinci katmanın çıktısı ReLU sonrası olduğu için sıfır noktası tamsayının en küçük değeridir.

### Adım D: Tamsayı çekirdek (C)

Çekirdek, `tinyml` kütüphanesidir: öznitelik hesabı (float), girdi kuantizasyonu ve iki katmanlı tamsayı ağ. Başlık dosyası dört işlevi dışa açar. Kullanıcı kodu yalnızca bu dört fonksiyonu çağırır; iç ayrıntılar `tinyml.c` içinde gizlidir.

```c
/* tinyml.h - sabit noktali (int8) MLP cikarim kutuphanesi.
 * Dinamik bellek yok (malloc yok). Tum tamponlar cagiran tarafta
 * veya yigida (cok kucuk) tutulur.
 */
#ifndef TINYML_H
#define TINYML_H

#include <stdint.h>

#define TM_L 32 /* pencere uzunlugu (ornek) */
#define TM_K 4  /* kanal sayisi */

/* Ham pencere (TM_L x TM_K float) -> 20 ozellik (float).
 * Sira: [ort(4), std(4), min(4), maks(4), egim(4)].         */
void tm_ozellik(const float p[TM_L][TM_K], float oz[20]);

/* Ozellik (float) -> int8 girdi. Normalizasyon ve kuantizasyon. */
void tm_girdi_kuantize(const float oz[20], int8_t xq[20]);

/* int8 girdi -> int32 logit'ler (tam tamsayi cekirdek). */
void tm_ileri(const int8_t xq[20], int32_t logit[2]);

/* Ham pencere -> 0 (normal) veya 1 (anomali). */
int tm_siniflandir(const float p[TM_L][TM_K]);

#endif
```

Uygulama dosyasının ilk kısmı, öznitelik hesabını içerir. Kanal başına döngü, ortalama ve standart sapma için iki geçiş yapar; her geçiş, Python'daki `numpy` fonksiyonlarının tanımını birebir izler. Eğim, zamanın merkezine göre ağırlıklı toplamdır ve paydası 32 örnek için sabit olarak 2728'dir (`L (L² - 1) / 12`).

```c
/* tinyml.c - sabit noktali MLP cikarimi (20 -> 8 -> 2).
 * TM_KULLAN_DSP=1 ve ARM hedefinde iç dongu SMLAD ile yazilir.
 */
#include <stdint.h>
#include <math.h>
#include "tinyml.h"
#include "model_int8.h"

#ifndef TM_KULLAN_DSP
#define TM_KULLAN_DSP 0
#endif

#if TM_KULLAN_DSP && defined(__ARM_FEATURE_DSP)
#define TM_DSP_AKTIF 1
#else
#define TM_DSP_AKTIF 0
#endif
```

```c
/* ---- Ozellikler (float; Cortex-M4F'te tek duyarlik FPU) ---- */
void tm_ozellik(const float p[TM_L][TM_K], float oz[20])
{
    const float n = (float)TM_L;
    const float tden = 2728.0f; /* sum (t - 15.5)^2, L = 32 */
    for (int k = 0; k < TM_K; k++) {
        float s = 0.0f, mn = p[0][k], mx = p[0][k];
        for (int t = 0; t < TM_L; t++) {
            float v = p[t][k];
            s += v;
            if (v < mn) mn = v;
            if (v > mx) mx = v;
        }
        float ort = s / n, var = 0.0f, eg = 0.0f;
        for (int t = 0; t < TM_L; t++) {
            float d = p[t][k] - ort;
            var += d * d;
            eg += ((float)t - 15.5f) * d;
        }
        oz[0 * TM_K + k] = ort;
        oz[1 * TM_K + k] = sqrtf(var / n);
        oz[2 * TM_K + k] = mn;
        oz[3 * TM_K + k] = mx;
        oz[4 * TM_K + k] = eg / tden;
    }
}
```

Girdi kuantizasyonu, Python'daki `girdi_kuantize` ile aynı işlem sırasını kullanır: önce `(x - μ) / σ`, sonra `/ S_in`, sonra `floor(· + 0.5)` ve sıfır noktasının eklenmesi. Float işlemlerin sırası ve yuvarlama, iki tarafta bit-tam aynı sonucu verir.

```c
/* ---- Girdi kuantizasyonu: q = floor((x-mu)/sd / S) + Z ---- */
void tm_girdi_kuantize(const float oz[20], int8_t xq[20])
{
    for (int i = 0; i < TM_NIN; i++) {
        float v = (oz[i] - TM_MU[i]) / TM_SD[i];
        float w = v / TM_SIN;
        float wr = w + 0.5f;
        int32_t q = (int32_t)wr;       /* sifira dogru kirpma */
        if ((float)q > wr) q--;        /* floor (negatif icin) */
        q += TM_ZIN;
        if (q < -128) q = -128;
        if (q > 127) q = 127;
        xq[i] = (int8_t)q;
    }
}
```

Nokta çarpımı iki sürümde yazılmıştır. Düz C sürümü, `int8` değerleri `int32` olarak çarpıp toplar. DSP sürümü ise Cortex-M4'ün SIMD benzeri komutlarını (`SXTB16` ile iki baytı iki yarı kelimeye açmak ve `SMLAD` ile iki çarpımı tek komutta toplamak) kullanır. Bu komutlar yalnızca ARM hedefinde derlenir; host'ta `TM_KULLAN_DSP` tanımsız olduğu için düz C yolu çalışır.

```c
/* ---- Nokta carpimi: sum w[j]*x[j], n, 4'un kati ---- */
#if !TM_DSP_AKTIF
static int32_t dot_c(const int8_t *w, const int8_t *x, int n)
{
    int32_t acc = 0;
    for (int j = 0; j < n; j++) {
        acc += (int32_t)w[j] * (int32_t)x[j];
    }
    return acc;
}
#endif
```

```c
#if TM_DSP_AKTIF
static inline uint32_t sxtb16_0(uint32_t v)   /* bayt 0 ve 2 */
{
    uint32_t r;
    __asm__ ("sxtb16 %0, %1" : "=r"(r) : "r"(v));
    return r;
}

static inline uint32_t sxtb16_1(uint32_t v)   /* bayt 1 ve 3 */
{
    uint32_t r;
    __asm__ ("sxtb16 %0, %1, ror #8" : "=r"(r) : "r"(v));
    return r;
}

static inline int32_t smlad(uint32_t a, uint32_t b, int32_t c)
{
    int32_t r;
    __asm__ ("smlad %0, %1, %2, %3"
             : "=r"(r) : "r"(a), "r"(b), "r"(c));
    return r;
}

static int32_t dot_dsp(const int8_t *w, const int8_t *x, int n)
{
    int32_t acc = 0;
    for (int j = 0; j < n; j += 4) {
        uint32_t wv, xv;
        __builtin_memcpy(&wv, w + j, 4);
        __builtin_memcpy(&xv, x + j, 4);
        acc = smlad(sxtb16_0(wv), sxtb16_0(xv), acc);
        acc = smlad(sxtb16_1(wv), sxtb16_1(xv), acc);
    }
    return acc;
}
#define DOT(w, x, n) dot_dsp((w), (x), (n))
```

Birinci katman, her çıktı kanalı için birikimi yapar, `M0` ile çarpar, `rs` bit kaydırır, yuvarlama sabitini eklemeyi unutmaz, sıfır noktasını ekler ve doygunluk uygular. `TM_RS1` değerleri 37 ya da 38 olduğu için `(int64_t)1 << (rs - 1)` her zaman tanımlıdır. ReLU, sıfır noktası `TM_ZA1` altına inmeyi engelleyen bir alt sınır ile uygulanır.

```c
#else
#define DOT(w, x, n) dot_c((w), (x), (n))
#endif

/* ---- Katman 1: 20 -> 8, yeniden olcekleme + ReLU ---- */
static void katman1(const int8_t x[20], int8_t a1[TM_NH])
{
    for (int i = 0; i < TM_NH; i++) {
        int32_t acc = TM_B1[i] + DOT(&TM_W1[i * TM_NIN], x, TM_NIN);
        int32_t rs = TM_RS1[i];
        int64_t p = (int64_t)acc * TM_M1[i];
        p += (int64_t)1 << (rs - 1);   /* yuvarlama */
        int32_t y = (int32_t)(p >> rs) + TM_ZA1;
        if (y < TM_ZA1) y = TM_ZA1;    /* ReLU: sifir = ZA1 */
        if (y > 127) y = 127;          /* doygunluk */
        a1[i] = (int8_t)y;
    }
}

/* ---- Katman 2: 8 -> 2, yeniden olcekleme yok (argmax yeter) ---- */
static void katman2(const int8_t a1[TM_NH], int32_t logit[TM_NOUT])
{
    for (int o = 0; o < TM_NOUT; o++) {
        logit[o] = TM_B2[o] + DOT(&TM_W2[o * TM_NH], a1, TM_NH);
    }
}
```

İkinci katmanda yeniden ölçekleme yoktur; logit'ler birikim değerleridir. Son işlev, sınıfı `lg[1] > lg[0]` karşılaştırmasıyla seçer. Bu karşılaştırma, Python tarafındaki `argmax` ile eşleşir: eşitlik durumunda ikisi de sıfırı (normal) seçer.

```c

void tm_ileri(const int8_t xq[20], int32_t logit[2])
{
    int8_t a1[TM_NH];
    katman1(xq, a1);
    katman2(a1, logit);
}

int tm_siniflandir(const float p[TM_L][TM_K])
{
    float oz[20];
    int8_t xq[20];
    int32_t lg[2];
    tm_ozellik(p, oz);
    tm_girdi_kuantize(oz, xq);
    tm_ileri(xq, lg);
    return lg[1] > lg[0];
}
```

### Adım E: Host üzerinde bit-tam doğrulama

Bir gömülü kodu hedef kartta hata ayıklamak yavaştır. Bu yüzden önce aynı C kodunu bilgisayarda derleyip Python referansıyla karşılaştırırız. Derlemeyi WSL'deki gcc 13.3 ile yaptık; ASan (bellek hatalarını yakalar) ve UBSan (tanımsız davranışı yakalar) etkindir.

```c
/* test_host.c - host (gcc) dogrulama.
 * Kullanim: test_host <veri_dizini>
 * Python referansiyla bit-tam karsilastirma + uctan uca dogruluk.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "tinyml.h"
#include "model_int8.h"

#define N 2000
#define NR 1000

static void *oku(const char *dizin, const char *ad, size_t boyut)
{
    char yol[512];
    snprintf(yol, sizeof yol, "%s/%s", dizin, ad);
    FILE *f = fopen(yol, "rb");
    if (!f) { perror(yol); exit(1); }
    void *b = malloc(boyut);
    if (!b || fread(b, 1, boyut, f) != boyut) {
        fprintf(stderr, "okuma hatasi: %s\n", ad);
        exit(1);
    }
    fclose(f);
    return b;
}
```

Test programı dört şey ölçer. Birincisi, C öznitelik hesabının Python sonucuna ne kadar yakın olduğu. İkincisi, girdi kuantizasyonunun Python'la bit-tam eşleşip eşleşmediği. Üçüncüsü, tamsayı çekirdeğin logit'lerinin Python'un tamsayı referansıyla bit-tam eşleşmesi. Dördüncüsü, ham pencereden sınıfa uçtan uca doğruluk. Dışarıdan okunan dosyalar, Python tarafında üretilmiştir.

```c
int main(int argc, char **argv)
{
    const char *d = (argc > 1) ? argv[1] : ".";
    float (*pen)[TM_L][TM_K] = oku(d, "test_pencere.bin",
                                   sizeof(float) * N * TM_L * TM_K);
    float (*ozp)[20] = oku(d, "test_ozellik.bin",
                           sizeof(float) * N * 20);
    int8_t (*xqp)[20] = oku(d, "test_xq.bin", N * 20);
    int32_t (*bek)[3] = oku(d, "test_beklenen.bin",
                            sizeof(int32_t) * N * 3);
    int8_t (*rxq)[20] = oku(d, "test_r_xq.bin", NR * 20);
    int32_t (*rbek)[2] = oku(d, "test_r_beklenen.bin",
                             sizeof(int32_t) * NR * 2);

    double ozellik_max = 0.0;
    int girdi_uyus = 0, logit_uyus = 0, dogru = 0, tah_fark = 0;

    for (int i = 0; i < N; i++) {
        /* (a) ozellik: C ile Python arasinda kucuk fark beklenir */
        float oz[20];
        tm_ozellik(pen[i], oz);
        for (int j = 0; j < 20; j++) {
            double dd = (double)oz[j] - (double)ozp[i][j];
            if (dd < 0) dd = -dd;
            if (dd > ozellik_max) ozellik_max = dd;
        }
        /* (b) girdi kuantizasyonu: Python ozellikleriyle bit-tam */
        int8_t xq[20];
        tm_girdi_kuantize(ozp[i], xq);
        for (int j = 0; j < 20; j++) {
            if (xq[j] != xqp[i][j]) { girdi_uyus++; break; }
        }
        /* (c) tam tamsayi cekirdek: Python tamsayi referansi ile */
        int32_t lg[2];
        tm_ileri(xqp[i], lg);
        if (lg[0] != bek[i][1] || lg[1] != bek[i][2]) logit_uyus++;
```

```c
        /* (d) uctan uca: ham pencere -> sinif */
        int tah = tm_siniflandir(pen[i]);
        if (tah == bek[i][0]) dogru++;
        if (tah != (bek[i][2] > bek[i][1])) tah_fark++;
    }

    /* (e) tam aralikli rastgele girdiler: tasma ve doygunluk */
    int r_uyus = 0;
    for (int i = 0; i < NR; i++) {
        int32_t lg[2];
        tm_ileri(rxq[i], lg);
        if (lg[0] != rbek[i][0] || lg[1] != rbek[i][1]) r_uyus++;
    }

    printf("ozellik en buyuk fark (C - Python): %.3g\n", ozellik_max);
    printf("girdi kuantizasyonu uyusmazlik    : %d / %d\n",
           girdi_uyus, N);
    printf("int8 logit uyusmazlik (bit-tam)   : %d / %d\n",
           logit_uyus, N);
    printf("uctan uca dogruluk (C)            : %.4f\n",
           (double)dogru / N);
    printf("uctan uca ile Python argmax farki : %d\n", tah_fark);
    printf("rastgele tam aralik uyusmazlik    : %d / %d\n",
           r_uyus, NR);
    free(pen);
    free(ozp);
    free(xqp);
    free(bek);
    free(rxq);
    free(rbek);
    if (girdi_uyus || logit_uyus || r_uyus) return 2;
    return 0;
}
```

Test şu komutlarla derlenir ve çalıştırılır. Derleme komutu, ASan ve UBSan için gereken bayrakları içerir.

```bash
gcc -O2 -Wall -Wextra -std=c11 -ffp-contract=off \
    -fsanitize=address,undefined -o test_host_asan \
    tinyml.c test_host.c -lm
./test_host_asan .
```

Çıktı, C'nin ve Python'un eşleştiğini gösterir.

```term
$ ./test_host_asan .
ozellik en buyuk fark (C - Python): 2.29e-05
girdi kuantizasyonu uyusmazlik    : 0 / 2000
int8 logit uyusmazlik (bit-tam)   : 0 / 2000
uctan uca dogruluk (C)            : 0.9930
uctan uca ile Python argmax farki : 0
rastgele tam aralik uyusmazlik    : 0 / 1000
```

Sonuçlar tam istediğimiz gibi: öznitelik farkı en fazla 2.29·10⁻⁵'tir (float32 toplamanın sırası farkı), girdi kuantizasyonu ve tamsayı logit'ler 2000 pencerenin tamamında bit-tam eşleşir ve 1000 rastgele tam aralıklı vektörde (doygunluk ve taşma sınırlarını da kapsayan) hiçbir uyuşmazlık yoktur. Uçtan uca doğruluk yüzde 99.3'tür ve Python argmax'ından farkı sıfırdır. `-fsanitize` ile derlenen programda ASan ve UBSan hiçbir uyarı vermedi.

Bu sonuç, "host'ta doğru" demektir. Cortex-M4 üzerinde aynı kodun aynı sonucu vereceğini ancak onu hedefte çalıştırarak doğrulayabilirsin. Bu bölümde hedef kart kullanılmadı; bu nedenle bir sonraki adımda yalnızca derleme, boyut ve komut sayımı yapıyoruz.

### Adım F: Cortex-M4 derlemesi, boyut ve komut sayımı

Hedef derlemesi için bir başlangıç dosyası, bir bağlayıcı betiği ve ölçüm yapan bir ana program gerekir. Ana program, DWT (Data Watchpoint and Trace) birimindeki çevrim sayacını kullanarak her çıkarımın kaç çevrim sürdüğünü ölçer. Kod hazırdır, ama kartta çalıştırılmamıştır; çevrim değerlerini bu yüzden üretmedik. Derlemeyle ilgili ölçümler ise tamamen gerçektir.

```c
/* mcu_main.c - Cortex-M4 olcum programu.
 * DWT cycle sayaci ile cikarim suresini olcer.
 * Bu kod DONANIMDA CALISTIRILMADI; yalniz derlendi. */
#include <stdint.h>
#include "tinyml.h"
#include "ornek.h"

#define DEMCR      (*(volatile uint32_t *)0xE000EDFCu)
#define DWT_CTRL   (*(volatile uint32_t *)0xE0001000u)
#define DWT_CYCCNT (*(volatile uint32_t *)0xE0001004u)

volatile int sonuc[ORNEK_SAYI];
volatile uint32_t dongu[ORNEK_SAYI];
volatile uint32_t cekirdek_dongu;
volatile int32_t lg_son[2];

int main(void)
{
    DEMCR |= (1u << 24);   /* TRCENA: DWT'yi etkinlestir */
    DWT_CYCCNT = 0;
```

```c
    DWT_CTRL |= 1u;        /* CYCCNTENA */

    for (int i = 0; i < ORNEK_SAYI; i++) {
        uint32_t t0 = DWT_CYCCNT;
        sonuc[i] = tm_siniflandir(ORNEK[i]);
        dongu[i] = DWT_CYCCNT - t0;
    }

    /* Yalniz tamsayi cekirdek: ozellik ve kuantizasyon haric */
    float oz[20];
    int8_t xq[20];
    int32_t lg[2];
    tm_ozellik(ORNEK[0], oz);
    tm_girdi_kuantize(oz, xq);
    uint32_t t1 = DWT_CYCCNT;
    tm_ileri(xq, lg);
    cekirdek_dongu = DWT_CYCCNT - t1;
    lg_son[0] = lg[0];
    lg_son[1] = lg[1];
    return 0;
}
```

Bağlayıcı ve başlangıç kodu, programın bellek haritasını tanımlar. Flash 512 KB, RAM 128 KB olarak varsayılmıştır (STM32F4 ailesine yakın bir harita; kendi kartının değerlerini kullanmalısın). Vektör tablosu yalnızca ilk iki girdiyi (yığın işaretçisi ve reset vektörü) içerir.

```c
/* startup.c - minimum Cortex-M baslangic kodu (kitap icin). */
#include <stdint.h>

extern int main(void);
extern uint32_t __stack_top;

void _start(void)
{
    main();
    for (;;) { }
}

__attribute__((section(".isr_vector"), used))
const void *const vektor[2] = {
    (void *)&__stack_top,
    (void *)_start,
};
```

```c
/* Minimum baglayici betigi: STM32F4 benzeri bellek haritasi. */
ENTRY(_start)

MEMORY
{
  FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 512K
  RAM   (rwx): ORIGIN = 0x20000000, LENGTH = 128K
}

SECTIONS
{
  .isr_vector : { KEEP(*(.isr_vector)) } > FLASH
  .text       : { *(.text*) *(.rodata*) } > FLASH
  .data       : { *(.data*) } > RAM AT > FLASH
  .bss        : { *(.bss*) *(COMMON) } > RAM
}
__stack_top = ORIGIN(RAM) + LENGTH(RAM);
```

Ölçüm için 4 örnek pencere (2 normal, 2 anomali) test kümesinden seçilir ve `ornek.h` içine yazılır. Bu betik onu üretir.

```python
# -*- coding: utf-8 -*-
"""MCU ornek penceresi: test setinden 2 normal, 2 anomali."""
import os
import numpy as np
from telemetri import veri_seti

HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    _, _, Xte, yte = veri_seti()
    normal = np.where(yte == 0)[0]
    anomali = np.where(yte == 1)[0]
    secim = [int(normal[0]), int(anomali[0]),
             int(normal[1]), int(anomali[1])]
    etiket = ", ".join(str(int(yte[i])) for i in secim)
    L = ["/* ornek.h - otomatik uretildi (ornek_uret.py). */",
         "#ifndef ORNEK_H", "#define ORNEK_H", "",
         "#define ORNEK_SAYI 4",
         "static const int ORNEK_ETIKET[4] = { %s };" % etiket,
         "static const float ORNEK[4][32][4] = {"]
    for i in secim:
        L.append("  {")
        for t in range(32):
            vals = ", ".join("%.4ff" % v for v in Xte[i, t])
            L.append("    {%s}," % vals)
        L.append("  },")
    L += ["};", "", "#endif"]
    yol = os.path.join(HERE, "ornek.h")
    with open(yol, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("secim:", secim, "etiketler:", [int(yte[i]) for i in secim])
```

Derleme ve komut sayımı tek bir kabuk betiğinde toplanmıştır. Betik her iki sürüm (düz C ve DSP) için derler, boyutu raporlar ve `objdump` çıktısındaki bazı komutları sayar.

```bash
#!/bin/bash
# Cortex-M4 derleme, boyut ve komut sayimi.
PLG="/c/ST/STM32CubeIDE_1.19.0/STM32CubeIDE/plugins"
PKG="com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32"
PKG="$PKG.13.3.rel1.win32_1.0.0.202411081344"
TB="$PLG/$PKG/tools/bin"
CC="$TB/arm-none-eabi-gcc.exe"
SZ="$TB/arm-none-eabi-size.exe"
OD="$TB/arm-none-eabi-objdump.exe"
BAYRAK="-mcpu=cortex-m4 -mthumb -mfloat-abi=hard"
BAYRAK="$BAYRAK -mfpu=fpv4-sp-d16 -Os"
BAYRAK="$BAYRAK -ffp-contract=off -fno-math-errno"
BAYRAK="$BAYRAK -ffunction-sections -fdata-sections"
BAYRAK="$BAYRAK -Wall -Wextra -std=c11"
cd "$(dirname "$0")"
for v in 0 1; do
  echo "=== TM_KULLAN_DSP=$v ==="
  "$CC" $BAYRAK -DTM_KULLAN_DSP=$v -S -o tinyml_dsp$v.s tinyml.c
  "$CC" $BAYRAK -DTM_KULLAN_DSP=$v -c -o tinyml_dsp$v.o tinyml.c
  echo "-- tinyml.o:"
  "$SZ" tinyml_dsp$v.o
  "$CC" $BAYRAK -DTM_KULLAN_DSP=$v -nostartfiles -nostdlib \
     -T ld_m4.ld -Wl,--gc-sections -o fw_dsp$v.elf \
     startup.c mcu_main.c tinyml.c -lm -lgcc
  echo "-- firmware (fw_dsp$v.elf):"
  "$SZ" fw_dsp$v.elf
  "$OD" -d tinyml_dsp$v.o > dis_dsp$v.txt
  echo "-- komut sayimi (tinyml.o, disassembly):"
  for m in smlad smlabb mla ldrsb ldr; do
    n=$(grep -cE "\s$m(\.[wn])?\s" dis_dsp$v.txt)
    printf "  %-8s %s\n" "$m" "$n"
  done
done
```

```term
$ ./derle_m4.sh
=== TM_KULLAN_DSP=0 ===
-- tinyml.o:
   text	   data	    bss	    dec	    hex	filename
   1064	      0	      0	   1064	    428	tinyml_dsp0.o
-- firmware (fw_dsp0.elf):
   text	   data	    bss	    dec	    hex	filename
   3284	      0	     44	   3328	    d00	fw_dsp0.elf
-- komut sayimi (tinyml.o, disassembly):
  smlad    0
  smlabb   2
  mla      1
  ldrsb    6
  ldr      15
=== TM_KULLAN_DSP=1 ===
-- tinyml.o:
   text	   data	    bss	    dec	    hex	filename
   1104	      0	      0	   1104	    450	tinyml_dsp1.o
-- firmware (fw_dsp1.elf):
   text	   data	    bss	    dec	    hex	filename
   3324	      0	     44	   3368	    d28	fw_dsp1.elf
-- komut sayimi (tinyml.o, disassembly):
  smlad    10
  smlabb   0
  mla      0
  ldrsb    0
  ldr      20
```

Çıktıdaki `size` tabloları, bir nesne dosyasının (`tinyml.o`) ve tüm yazılımın (`fw_dsp0.elf`, `fw_dsp1.elf`) bölümlerini gösterir. Metin (text) sütunu flash'a giden kodu ve salt okunur verileri (sabit diziler) içerir; bss sütunu RAM'de sıfırlanan değişkenleri içerir. Her iki derlemede de bss 44 bayttır: sonuç dizisi (16 bayt), süre dizisi (16 bayt), logit değerleri (8 bayt) ve çevrim sayacı (4 bayt) toplamıdır.

Komut sayımı ise en önemli karşılaştırmadır. Düz C sürümünde `smlabb` (16 bit çarpım-toplam) ve `ldrsb` (işaretli bayt yükleme) komutları baskındır; DSP sürümünde ise `smlad` komutları ortaya çıkar. Sayım, tüm `tinyml.o` nesnesi üzerinden yapıldığı için tek tek döngüleri ayırt etmez. Bu yüzden iç döngünün kendisine bakmak daha öğreticidir. Aşağıda birinci katmanın iç döngüsünün `objdump` kesiti var; iki sürüm de aynı katmandan alındı.

Düz C sürümünde döngü, her MAC için bir kez çalışır:

```text
32: ldrsb.w r1, [r6, #1]!
36: ldrsb.w sl, [r8, #1]!
3a: cmp r9, r6
3c: smlabb r5, r1, sl, r5
40: bne.n 32
```

DSP sürümünde döngü her yinelemede dört MAC yapar ve on iki komut tutar:

```text
2a: ldr r4, [sp, #4]
2c: ldr r0, [r2, r6]
2e: ldr r4, [r4, r2]
30: sxtb16 sl, r0
34: adds r2, #4
36: cmp r2, #20
38: sxtb16 r1, r4
3c: sxtb16 r0, r0, ror #8
40: smlad r3, sl, r1, r3
44: sxtb16 r4, r4, ror #8
48: smlad r3, r0, r4, r3
4c: bne.n 2a
```

Düz C'de bir MAC yaklaşık beş komut, DSP'de yaklaşık üç komut tutar (12 komut / 4 MAC). Birinci katmanın iç döngüsünde bu, MAC başına komut sayısının yaklaşık 5'ten 3'e, yani yüzde 40 civarında azalması demektir. Bu bir komut sayısıdır; ölçülen çevrim farkı değildir, çünkü yükleme gecikmeleri ve dal tahmini de süreyi etkiler. Bu yüzden süre tahminini ayrıca 46.11'de yapıyoruz.

Düz C ile DSP arasındaki bir başka fark, derleyicinin ikinci katmanla yaptığı işte görülür. Derleyici, iki çıkışlı ve sekiz girdili ikinci katmanı açmış (unroll) ve onyargı dizisi `TM_B2` iki derlemede de, ağırlık dizisi `TM_W2` yalnızca DSP derlemesinde kod içine sabit olarak gömülmüştür; bu yüzden sembol tablosunda bu diziler görünmez. Flash tablosundaki "model parametreleri" satırı bu yüzden 432 ve 416 bayttır; tam model boyutu 440 bayttır (Bölüm 46.3 tablosu).

Boyut dökümü, `size` ve `nm` çıktısından otomatik üretilir.

```python
# -*- coding: utf-8 -*-
"""Firmware boyut dokumu: arm-none-eabi-size ve nm ciktilari."""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
TB = ("C:/ST/STM32CubeIDE_1.19.0/STM32CubeIDE/plugins/"
      "com.st.stm32cube.ide.mcu.externaltools."
      "gnu-tools-for-stm32.13.3.rel1.win32_1.0.0.202411081344"
      "/tools/bin")
MODEL = ["TM_W1", "TM_W2", "TM_B1", "TM_B2", "TM_M1", "TM_RS1",
         "TM_MU", "TM_SD"]

def sayilar(elf):
    out = subprocess.run([TB + "/arm-none-eabi-size.exe", "-A", elf],
                         capture_output=True, text=True).stdout
    text = int(re.search(r"\.text\s+(\d+)", out).group(1))
    bss = int(re.search(r"\.bss\s+(\d+)", out).group(1))
    nmexe = TB + "/arm-none-eabi-nm.exe"
    nm = subprocess.run([nmexe, "-S", "-t", "d", elf],
                        capture_output=True, text=True).stdout
    sembol = {}
    for sat in nm.splitlines():
        p = sat.split()
        if len(p) == 4:
            sembol[p[3]] = int(p[1])
    model = sum(sembol.get(s, 0) for s in MODEL)
    ornek = sembol.get("ORNEK", 0)
    return dict(model=model, ornek=ornek,
                kod=text - model - ornek, ram=bss)
```

```python
if __name__ == "__main__":
    a = sayilar(os.path.join(HERE, "fw_dsp0.elf"))
    b = sayilar(os.path.join(HERE, "fw_dsp1.elf"))
    yol = os.path.join(VERI, "b46_boyut.csv")
    with open(yol, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("bilesen,hedef,duz_c_bayt,dsp_bayt\n")
        fh.write("model_parametreleri,flash,%d,%d\n"
                 % (a["model"], b["model"]))
        fh.write("kod_ve_sabitler,flash,%d,%d\n"
                 % (a["kod"], b["kod"]))
        fh.write("ornek_pencereler,flash,%d,%d\n"
                 % (a["ornek"], b["ornek"]))
        fh.write("durum_ve_tamponlar,ram,%d,%d\n"
                 % (a["ram"], b["ram"]))
    print(open(yol, encoding="utf-8").read(), end="")
```

```term
$ python boyut_csv.py
bilesen,hedef,duz_c_bayt,dsp_bayt
model_parametreleri,flash,432,416
kod_ve_sabitler,flash,796,852
ornek_pencereler,flash,2048,2048
durum_ve_tamponlar,ram,44,44
```

Şekil 46.8, bu dökümü flash ve RAM bütçesi olarak gösterir. Flash'ın büyük kısmı sabit örnek pencereler (demo amaçlı, 2048 bayt) ile kod tarafından kullanılır; gerçek sistemde bu pencereler yoktur ve kullanılan flash yaklaşık 1,2 KB'a iner. Model parametreleri, demo dışı flash'ın (yaklaşık 1,2 KB) üçte birinden biraz fazlasını oluşturur. RAM ise 44 bayttır; ama bu sayı yalnızca ölçüm değişkenlerini kapsar. Gerçek sistemde RAM'in büyük kısmı sensör pencere tamponu olur: 32·4 float = 512 bayt.

![Şekil 46.8: Firmware'in flash ve RAM dökümü (düz C ve DSP sürümleri)](gorseller/b46_flash_ram.png)

### Adım G: Sonuçlar

Uygulamanın sonuçlarını beş ölçüt üzerinden özetleyebiliriz. Float32 test doğruluğu yüzde 99.30, int8 doğruluğu da yüzde 99.30'tur; argmax uyumu yüzde 100'dür. Kesinlik 1.0 ve duyarlılık 0.978'dir: yani sistem hiç yanlış alarm vermemiş, ama 627 anomali penceresinin 14'ünü kaçırmıştır. Bellek olarak model 440 bayt ve kod+sabitler yaklaşık 0.8 KB flash kullanır (demo pencereler hariç). Gecikme ise bu bölümde ölçülmedi; tahmini değerleri 46.11'de vereceğiz.

Şekil 46.9, float32 ve int8 skorlarının dağılımını gösterir. Sol panelde normal (mavi) ve anomali (kırmızı) pencerelerin skorları sıfır eşiğinin iki yanına ayrılmıştır. Sağ panelde ise int8 skoru ile float32 skoru neredeyse üst üste biner; her nokta köşegene yakındır. Bu, tamsayı çekirdeğin sınıf sınırını doğru yerde tuttuğunu gösterir.

![Şekil 46.9: Anomali skorları: sınıf dağılımı ve float32 ile int8 uyumu (sentetik veri)](gorseller/b46_anomali.png)

Kaçırılan 14 anomaliyi incelemedik; ama genel bir tahmin yapabiliriz: bunlar büyük olasılıkla düşük şiddetli örnekler, yani eşiğe en yakın olanlardır. Bu bir hipotezdir ve kendi verinle test etmelisin. Gerçek bir sistemde yanlış negatifin (kaçan anomali) bedeli yanlış alarmdan çok daha yüksek olabilir; bu nedenle eşiği yalnızca doğruluk değil, maliyet ile birlikte seçmelisin. Bu kararın güvenlik boyutunu 46.11'de tartışacağız.

## 46.10 Uygulama 2 (kavram): IMU ile hareket tanıma

Bu uygulama isteğe bağlıdır ve burada yalnızca kavram olarak anlatılır; kod verilmez. Bir IMU (eylemsizlik ölçü birimi), genelde bir ivmeölçer ve bir jiroskop içerir. Bunlar üç eksende ivme ve açısal hız verir. Bir cihazın elde tutulması, sallanması ya da yerde sabit durması bu sinyallerde farklı biçimler bırakır. Tipik bir hareket tanıma hattı, 50 Hz'de 2 saniyelik pencereler alır, her pencereden birkaç istatistik çıkarır ve küçük bir sınıflandırıcıyla "sabit", "yürüme" ya da "sallanma" gibi bir etiket verir.

Bu hattın mimarisi, EV uygulamasıyla aynıdır: pencereleme, öznitelik, normalizasyon, int8 MLP, sınıf kararı. Değişen şey girdinin kanal sayısı (altı eksen) ve sınıfların anlamıdır. Bu benzerlik kasıtlıdır: TinyML hattının büyük kısmı sensörden bağımsızdır. Sen de Kendin Yap Proje 2'de bu fikri farklı bir sensöre uyarlayarak test edebilirsin.

Burada dikkat edilmesi gereken bir nokta var: IMU verisi gürültülüdür ve kişiden kişiye değişir. Sentetik bir veriyle elde edilen doğruluk, gerçek bir kullanıcı grubunda aynı kalmaz. Bu, Bölüm 57'deki değerlendirme ve deney tasarımının (kişiler arası bölme, veri sızıntısı) tam konusudur.

## 46.11 Değerlendirme: doğruluk, gecikme, bellek, enerji ve güvenilirlik

Bir TinyML sistemini değerlendirirken tek bir sayıya bakmak yanıltıcıdır. En az beş eksen birlikte düşünülmelidir: doğruluk, gecikme, bellek, enerji ve güvenilirlik. Bunlar birbirini etkiler; bir eksende kazanmak çoğu zaman bir diğerinde kaybettirir.

**Doğruluk.** Anomali tespitinde yalnızca genel doğruluk yetmez. Kesinlik (alarmların ne kadarı gerçek) ve duyarlılık (gerçek anomalilerin ne kadarı yakalandı) ayrı ayrı izlenmelidir. Bu bölümde kesinlik 1.0 ve duyarlılık yaklaşık 0.978'dir; yani kaçan 14 anomali bir risktir.

**Gecikme.** Burada iki tür sayımız var. Ölçülen: derlenmiş iç döngülerdeki komut sayıları. Düz C'de MAC başına yaklaşık 5, DSP'de yaklaşık 3 komut. Tahmin: çevrim ve süre. Bu tahmin, komut sayısını bir çevrim-komut oranıyla (CPI) çarpar. Bu oran dal, yükleme ve bellek gecikmelerine bağlıdır ve burada kabaca 1.2 ile 2.0 arasında varsayılmıştır (tahmin, ölçülmedi). Sonuç olarak:

- Birinci katman: yaklaşık 480 komut (DSP) ya da 800 komut (düz C). Bu, 168 MHz'de yaklaşık 3 ile 10 mikrosaniye arasında (tahmin).
- Öznitelik çıkarımı ve normalizasyon: 4 kanal × 32 örnek üzerinde birkaç geçiş ve 20 bölme. Tahmini birkaç bin çevrim; bu da birkaç on mikrosaniye demektir (tahmin). Bölmeler (`VDIV`) yavaş komutlar olduğu için girdi kuantizasyonu da ayrıca pahalıdır (genel bilgi).

Bu tahminlerden çıkan sonuç çarpıcıdır: süreyi asıl belirleyen **ağ değil, öznitelik hesabıdır**. Ağın 176 MAC'i birkaç mikrosaniye sürer; pencere başına float işlemler ise daha fazla. Bu yüzden gerçek bir sistemi hızlandırmak istediğinde önce ön işlemeye bakmalısın, sonra modele.

**Bellek.** Model flash'ta 440 bayt, kod ve sabitler yaklaşık 0.8 KB flash, RAM'de ise pencere tamponu (512 bayt) ve birkaç düzine bayt ara değer. Bu, bir mikrodenetleyicinin kilobaytlık RAM'ine rahat sığar; asıl kısıt RAM'de sensör tamponunun büyüklüğü olabilir. Şekil 46.10'daki takas üçgeninde bellek köşesi bu anlama gelir.

**Enerji.** Enerji, güç ile süre çarpımıdır: `E = P · t`. Güç değeri (P) kullandığın kartın ve çalışma modunun veri sayfasından gelir; bu bölümde kart kullanılmadığı için bunu bir varsayım olarak yazıyoruz. Örneğin aktif gücü 50 mW varsayarsak ve pencere başına süreyi 40 mikrosaniye tahmin edersek, bir çıkarım yaklaşık 2 µJ tutar (tahmin, varsayımlara bağlı). Bir pencere 3.2 saniyelik olduğu için işlemcinin çalışma oranı yüzde 0,001 civarındadır; asıl enerji tüketimi uykuda kalma ve sensör okumadadır. Bu, enerji hesabında ortalama gücün çıkarımdan çok uyku modunun belirlediği anlamına gelir.

**Güvenilirlik.** Bir modelin laboratuvarda doğru olması, sahada güvenli olduğu anlamına gelmez. Üç konu özellikle önemlidir.

Birincisi **dağılım kayması**. Sensörler yaşlanır, sıcaklık değişir, farklı bir araç ya da farklı bir sürücü geldiğinde veri değişir. Model bu değişimi fark etmez ve doğruluk sessizce düşer. Bunu yakalamanın yolu, sahadaki öznitelik dağılımlarını eğitim dağılımıyla karşılaştırmaktır; ayrıntı Bölüm 77'de.

İkincisi **giriş doğrulama**. Bir hücre geriliminin 0 V ya da 10 V okunması fiziksel olarak mümkün değildir; bu bir sensör arızasıdır. Model bu değerle de bir karar verir, ama o karar anlamsızdır. Modelden önce fiziksel aralık kontrolü koymak, sistemi bu tür durumlarda güvenli bir moda sokabilir.

Üçüncüsü **güvenli varsayılan**. Model emin değilse ne olur? Logit farkı sıfıra çok yakınsa, karar bir yazı turası gibidir. Böyle durumlarda sistemin yapması gereken, kararı zorlamak değil, belirsizliği bildirmek ve güvenli bir davranışa geçmektir: uyarı vermek, insan onayı istemek ya da bağımsız ikinci bir kontrol çalıştırmak. Savunma sanayiinde bu ilke daha da önemlidir: kritik bir kararı tek bir öğrenen modele bağlamamalısın. Belirsizlik tahmini ve doğrulama Bölüm 78'in konusudur.

**Takas.** Yukarıdaki beş eksen bir üçgenin köşeleri gibi düşünülebilir. Şekil 46.10 bu düşünceyi özetler: bit genişliği, budama ve model boyutu, üçgenin içinde bir takas yaratır. Düşük bit, bellek ve gecikmeyi iyileştirir ama doğruluğu kötüleştirir; bunu bit taraması ölçümünde gördük.

![Şekil 46.10: Doğruluk, gecikme ve bellek/enerji arasındaki takas üçgeni](gorseller/b46_takas.png)

## 46.12 Gerçek dünya bağlamı

Bu bölümde kurduğumuz hattın gerçek dünyadaki yerini üç örnekle düşünelim. Bu örnekler kavramsaldır; her birinin ayrıntısı ilgili bölümde gelecek.

**İHA'da yerel karar.** Bir İHA'nın kamerası yüksek çözünürlüklü bir görüntü üretir; bu görüntüyü her karede yere göndermek, bant genişliği ve gecikme açısından olanaksızdır. Bu nedenle hedef tespiti ve takibi uçakta, uçağın kendi işlemcisinde yapılır. Burada modelin boyutu MCU'dan çok daha büyüktür ve kullanılan donanım bir Jetson ya da benzeri bir uç bilgisayardır. Bu bölümdeki ilkeler (bütçe, bit genişliği, ölçüm) aynen geçerlidir. Nesne tespiti modellerinin mimarisi Bölüm 67'de; uç üzerinde hızlandırma Bölüm 75'te gelecek.

**Kestirimci bakım.** Bir bataryanın ya da motorun arızası aniden değil, yavaş yavaş gelişir. Titreşim ve sıcaklık verisinden bir anomali skoru üretmek, bakım zamanını planlamak için değerlidir. Burada karar gecikmesi kritik değildir; ama cihazın bağlantısız çalışabilmesi ve verinin dışarı çıkmadan işlenmesi yine avantajdır. Mert'in EV Dashboard projesinde kurduğu telemetri hattı, bu kullanımın doğrudan bir örneğidir.

**Semantik iletişimde uçta kodlama.** Klasik iletişimde gönderilen şey bitlerdir ve amaç bitleri hatasız taşımaktır. Semantik iletişimde ise gönderilen şey anlamdır: verinin amacı için gerekli bilgi çıkarılır ve yalnızca o gönderilir. Bu yaklaşımda kodlayıcı (encoder) bir sinir ağıdır ve uçta çalışmak zorundadır; bant genişliği ve gecikme bu yüzden uçtaki hesapla dengelenir. Mert'in ÖZCE projesi bu fikrin bir örneğidir; üretken modeller ve ÖZCE bağlantısı Bölüm 72'de ayrıntılı olarak ele alınacak. Burada yalnızca şunu not et: uçta çıkarımın tasarımı, yalnızca "model küçük mü?" sorusu değil, "hangi bilgi uçta üretilmeli, hangisi gönderilmeli?" sorusudur.

## Çözümlü Örnekler

Bu bölümdeki örnekler, Bölüm 5'te öğrendiğin altı adımı izler: Anla, Örnekle, Kaba çöz, Örüntü, İyileştir, Doğrula. Her örnekte son adım bir elle iz sürme tablosu içerir. Örnekleri okurken kâğıt ve kalem kullan; tabloyu sen doldurmadan sonuca bakma. Örnekteki sayılar, bu bölümün kendi modelinden ve kendi ölçümlerinden alınmıştır; bunları hesap makinesiyle yeniden üretebilirsin.

### Örnek 1 (★): Bir ağın parametre, bellek ve MAC bütçesi

Bu örnekte iki katmanlı bir ağın (20 girdi, 8 gizli birim, 2 çıktı) bütçesini çıkaracaksın. Tablonun değerleri, 46.3'teki tabloyla aynıdır; amacın tabloyu kendi başına üretebilmek.

**Adım 1 — Anla.** Bir katman için üç şey sorulur: kaç parametresi var, bu parametreler float32 ve int8 olarak kaç bayt tutar ve kaç MAC yapılır. Ayrıca ağın tepe aktivasyon belleği, katman girdisi ile çıktısının toplamının en büyüğüdür. Bu üç sayıyı katman katman topladığında ağın flash ve RAM ihtiyacı çıkar.

**Adım 2 — Örnekle.** Birinci katman 20 girdi ve 8 çıktı içerir. Bu, `W1` matrisinin 8 × 20 olduğu ve `b1` vektörünün 8 elemanlı olduğu anlamına gelir.

**Adım 3 — Kaba çöz.** Parametre sayısı `8·20 + 8 = 168`. Float32 bayt sayısı `168 · 4 = 672`. Int8 modeli için ağırlık 160 bayt (1 bayt her biri), onyargı 8 · 4 = 32 bayt, `M0` ve `rs` için 8'er değer, her biri 4 bayt, yani 32 + 32 bayt. Toplam int8 model boyutu `160 + 32 + 32 + 32 = 256` bayt. MAC sayısı `20 · 8 = 160`.

**Adım 4 — Örüntü.** Her katman aynı üç adımla hesaplanır: parametre sayısı, float ve int8 bayt sayıları, MAC sayısı. Fark yalnızca ağırlık sayısından ve yeniden ölçekleme dizilerinden gelir. Bu örüntüyü ikinci katmanda da kullanabilirsin.

**Adım 5 — İyileştir.** Tepe aktivasyon belleğini azaltmak için her katman yalnızca kendi girdisini ve çıktısını tutar. Birinci katmanda girdi 20 bayt (int8), çıktı 8 bayt (int8) olduğu için tepe `20 + 8 = 28` bayttır. İkinci katmanda girdi 8 bayt, çıktı 8 bayt (int32 logit) olduğu için `8 + 8 = 16` bayttır. Tepe, en büyüğü olan 28 bayttır.

**Adım 6 — Doğrula.** Aşağıdaki tablo, iki katmanın değerlerini ve toplamlarını gösterir. Toplamlar 46.3'teki tablonun toplamıyla uyuşmalıdır.

| Katman | Parametre | float32 (bayt) | int8 model (bayt) | MAC | Tepe aktivasyon (bayt) |
|---|---|---|---|---|---|
| Katman 1 (20 → 8) | 168 | 672 | 256 | 160 | 28 |
| Katman 2 (8 → 2) | 18 | 72 | 24 | 16 | 16 |
| Toplam | 186 | 744 | 280 | 176 | 28 (tepe) |

Bu tablo yalnızca iki katmanı kapsar. Normalizasyon (40 parametre, 160 bayt, float) ekleyince toplam parametre 226, float32 toplam 904 bayt, int8 model toplamı (normalizasyon dahil) 440 bayt olur; bu değerler 46.3'teki tabloyla birebir aynıdır. Tepe aktivasyon belleğine ise ham float pencere (512 bayt) eklenmelidir; sistemin RAM ihtiyacını belirleyen de budur.

**Bunu AI'sız yazabilir misin?** Girdi 16, gizli birim 4, çıktı 3 olan bir ağ için aynı tabloyu doldur. Ardından tepe aktivasyon belleğinin hangi katmanda ortaya çıktığını ve neden öyle olduğunu tek cümleyle yaz.

### Örnek 2 (★★): Bir sayıyı Q1.15'e çevirmek, kırpmak ve geri okumak

Bu örnekte bazı float değerleri Q1.15 biçimine çevirip geri okuyacak, doygunluğun nerede devreye girdiğini göreceksin. Ayrıca iki Q1.15 sayının çarpımını ve bir toplamanın doygunluğunu elle hesaplayacaksın.

**Adım 1 — Anla.** Q1.15 sayılar `[-1, 1 - 2^-15]` aralığını temsil eder ve 16 bitlik bir tamsayı olarak saklanır. Bir `x` değerinin Q1.15 karşılığı `q = round(x · 2^15)` ile hesaplanır ve sonuç `[-32768, 32767]` aralığına kırpılır. Geri okumak için `x' = q / 2^15` yaparsın.

**Adım 2 — Örnekle.** Altı değer alalım: `0.5`, `-0.75`, `0.999`, `1.2`, `-1.0` ve `0.0001`. Bunlardan `1.2` aralık dışındadır; `-1.0` ise tam sınırdadır.

**Adım 3 — Kaba çöz.** Her değeri `2^15 = 32768` ile çarpıp en yakın tamsayıya yuvarlarsın; sonra aralığa kırparsın. `0.5 · 32768 = 16384` ve `-0.75 · 32768 = -24576` tam sayılardır. `0.999 · 32768 = 32735.2`, yuvarlayınca `32735`. `1.2 · 32768 = 39321.6`, yuvarlayınca `39322`, ama bu üst sınır olan `32767`'yi aşar; kırpılınca `32767` olur. `-1.0 · 32768 = -32768` tam sınırdır. `0.0001 · 32768 = 3.2768`, yuvarlayınca `3`.

**Adım 4 — Örüntü.** Pozitif ve negatif değerler simetrik davranır: `-0.75` için yuvarlama ve ölçek aynı kuralı izler. Tek asimetri üst sınırdadır: pozitif sınır `32767`, negatif sınır `-32768`'dir. Bu yüzden `1.0` tam olarak temsil edilemez; en büyük temsil edilebilir değer `0.99997`'dir.

**Adım 5 — İyileştir.** Çarpım için her iki operandın kesir bitleri toplanır: `q_a · q_b` Q2.30 biçimindedir. Sonucu Q1.15'e indirmek için 15 bit sağa kaydırıp yuvarlarsın: `(q_a · q_b + 2^14) >> 15`. Toplamada ise sonucun taşmaması için doygunluk uygulanır: `clamp(q_a + q_b, -32768, 32767)`.

**Adım 6 — Doğrula.** Aşağıdaki tablo her adımı gösterir.

| Girdi x | q (ham) | q (kırpılmış) | Geri okunan x' | Hata |x - x'| |
|---|---|---|---|---|
| 0.5 | 16384 | 16384 | 0.500000 | 0 |
| -0.75 | -24576 | -24576 | -0.750000 | 0 |
| 0.999 | 32735 | 32735 | 0.998993 | 0.000007 |
| 1.2 | 39322 | 32767 | 0.999969 | 0.200031 |
| -1.0 | -32768 | -32768 | -1.000000 | 0 |
| 0.0001 | 3 | 3 | 0.000092 | 0.000008 |

Bu tablo, `1.2` değerinin doygunluk nedeniyle büyük bir hata verdiğini gösterir; diğer değerlerde hata yaklaşık `2^-15 / 2` ile sınırlıdır. Çarpımda `0.5 · (-0.75)`: `16384 · (-24576) = -402653184`. Yuvarlama ile `(-402653184 + 16384) >> 15`... burada dikkat: `2^14 = 16384`, yani `(-402653184 + 16384) / 32768 = -12287.5`, aşağı yuvarlanırsa `-12288`; bu da `-12288 / 32768 = -0.375` değerine denk gelir ve gerçek çarpım `-0.375`'tir. Doğru.

Çarpımın ikinci örneği `0.999 · 0.999`: `32735 · 32735 = 1071580225`; yuvarlamalı kaydırma `(1071580225 + 16384) >> 15 = 32702`, yani `0.997986`. Gerçek değer `0.998001`'dir; fark, iki kuantizasyon hatasının birikmesinden gelir. Son olarak `0.999 + 0.999`: `32735 + 32735 = 65470` aralık dışındadır, doygunlukla `32767` olur ve bu `0.99997`'dir. Doygunluk olmadan işaret tersine dönerdi; bu, ağın davranışını kökten bozardı.

**Bunu AI'sız yazabilir misin?** `0.6` ve `-0.9` değerlerini Q1.15'e çevir, sonra çarpımlarını yuvarlamalı kaydırmayla hesapla. Sonucu float çarpımıyla karşılaştır ve farkın neden `2^-15`'in katlarıyla sınırlı olduğunu açıkla.

### Örnek 3 (★★): Bir int8 nokta çarpımını elle yapmak ve yeniden ölçeklemek

Bu örnekte tek bir çıktı kanalının tamsayı birikimini, yeniden ölçeklemesini ve sıfır noktası hesabını elle izleyeceksin. Ardından iki farklı birikim değerinin yuvarlamasını karşılaştıracaksın; biri kolay, diğeri ilginç bir yuvarlama davranışı gösterir.

**Adım 1 — Anla.** Bir int8 katmanda bir çıktı kanalı `acc = b + Σ (x_j - Z_in) · w_j` ile hesaplanır. Sonra `y = round(acc · m) + Z_out` ile int8 çıktı elde edilir; burada `m = S_in · S_w / S_out`. Tamsayı uygulamada `m` yerine `M0` ve `rs` kullanılır: `y = (acc · M0 + 2^(rs-1)) >> rs`.

**Adım 2 — Örnekle.** Girdi `x = [12, -7, 33, 5]`, girdi sıfır noktası `Z_in = 3`, ağırlık `w = [-3, 8, 2, -1]`, onyargı `b = 10`. Ölçekler `S_in = 0.05`, `S_w = 0.02`, `S_out = 0.1`, çıktı sıfır noktası `Z_out = 5`.

**Adım 3 — Kaba çöz.** Önce her terimi hesapla: `(12 - 3)(-3) = -27`, `(-7 - 3)(8) = -80`, `(33 - 3)(2) = 60`, `(5 - 3)(-1) = -2`. Toplam `-49`, onyargı ile `acc = -39`. Gerçek çıktı `acc · S_in · S_w = -39 · 0.001 = -0.039`. Bunu `S_out`'a bölersen `-0.39` elde edersin; en yakın tamsayı `0`'dır, dolayısıyla `y = 0` ve `q = 0 + 5 = 5`.

**Adım 4 — Örüntü.** Yeniden ölçekleme çarpanı `m = 0.05 · 0.02 / 0.1 = 0.01`'dir. Bunu `M0 / 2^rs` biçiminde yazmak için `frexp` kullanırsın: `0.01 = 0.64 · 2^-6`, yani `M0 = round(0.64 · 2^31) = 1374389535` ve `rs = 31 - (-6) = 37`. Bu iki sayı ile tamsayı yolu, kayan nokta yolunun sonucunu vermelidir.

**Adım 5 — İyileştir.** Tamsayı yol, `acc` değerini bir kez 64-bit'e taşıyıp `M0` ile çarpar, yuvarlama sabiti olan `2^36 = 68719476736`'yı ekler ve `37` bit sağa kaydırır. Burada önemli bir tuzak var: negatif sayılarda `>>` işlemi aşağı yuvarlar (sonsuza doğru). Bu yüzden yuvarlama sabitini eklemek, sonucu doğru en yakın tamsayıya çeker. Sabiti eklemeden kaydırmak, negatif değerlerde sistematik bir kayma yapar.

**Adım 6 — Doğrula.** İki ayrı birikim değeri için tablo:

| acc | acc · M0 | + 2^36 | >> 37 (yuvarlanmış) | Kayan nokta acc · m | q = y + 5 |
|---|---|---|---|---|---|
| -39 | -53601191865 | 15118284871 | 0 | -0.39 | 5 |
| -61 | -83837761635 | -15118284899 | -1 | -0.61 | 4 |

İlk satırda `acc · m = -0.39` en yakın tamsayı `0`'a yuvarlanır ve tamsayı yol bunu doğrular. İkinci satırda `acc · m = -0.61` en yakın tamsayı `-1`'dir. Tamsayı yol `-1` verir, çünkü `-15118284899 / 2^37 ≈ -0.11`, aşağı yuvarlanınca `-1` olur. Eğer `-61 · M0`'ı doğrudan C'de `/ 2^37` ile bölseydin, tamsayı bölme sıfıra doğru yuvarlanır ve sonuç `0` olurdu; bu da yanlıştır. Bu yüzden yeniden ölçeklemede bölme yerine kaydırma ve açık yuvarlama kullanılır.

**Bunu AI'sız yazabilir misin?** `x = [20, 1, -5, 9]`, `Z_in = 0`, `w = [2, -4, 6, 1]`, `b = 3` için `acc`'yi hesapla. `S_in = 0.1`, `S_w = 0.05`, `S_out = 0.2`, `Z_out = -10` ile `m`'yi ve `M0`, `rs` değerlerini bul; sonra tamsayı yolla çıktıyı üret ve kayan nokta yoluyla karşılaştır.

### Örnek 4 (★★★): Kuantizasyon parametrelerini bir tensörün aralığından hesaplamak ve hatayı analiz etmek

Bu örnekte iki kuantizasyon şemasını (asimetrik ve simetrik) aynı veriye uygulayıp hatalarını karşılaştıracaksın. Ayrıca neden ReLU çıkışlarında asimetrik şemanın çözünürlüğü daha yüksek olduğunu göstereceksin.

**Adım 1 — Anla.** Bir tensör `t` için kuantizasyon parametrelerini `lo` ve `hi` değerlerinden çıkarırsın. Asimetrik şemada `S = (hi - lo) / 255` ve `Z = round(-128 - lo / S)`; simetrik şemada `S = max|t| / 127` ve `Z = 0`. Hata, geri okunan değer ile gerçek değer arasındaki farktır. Her iki şemada da yuvarlama hatası en fazla `S / 2`'dir; bu, en yakın seviyeye yuvarlamanın doğal sonucudur.

**Adım 2 — Örnekle.** Tensör 8 değerli olsun, ama tablo için dört değeri inceleyelim: `t = [-0.1, 0.25, 1.1, 2.3]`. Tensörün tamamının `lo = -0.4` (tensörde bulunan en küçük değer) ve `hi = 2.3` olduğunu varsayalım. Ayrıca simetrik şema için `max|t| = 2.3`'tür.

**Adım 3 — Kaba çöz.** Asimetrik ölçek `S = (2.3 + 0.4) / 255 = 0.010588`, sıfır noktası `Z = round(-128 + 0.4 / 0.010588) = round(-90.2) = -90`. Simetrik ölçek `S = 2.3 / 127 = 0.018110`. Her değer için `q = round(t / S) + Z` (asimetrik) ve `q = round(t / S)` (simetrik) hesaplanır.

**Adım 4 — Örüntü.** Asimetrik şema `-0.4` ile `2.3` arasındaki 256 seviyeyi tam kullanır. Simetrik şema ise `-2.3` ile `2.3` arasındaki 255 seviyeyi kullanır; negatif tarafın büyük kısmı bu tensörde hiç görülmez. Bu bir tensörde negatif değerler yarı yarıya olsaydı simetrik şema doğal olurdu. Ama ReLU çıkışında hiç negatif değer yoktur: simetrik şema, yarısını boşa harcar.

**Adım 5 — İyileştir.** ReLU çıkışları için bir örnek alalım: aralık `[0, 6]`. Asimetrik `S = 6 / 255 = 0.023529` ve `Z = -128`; yarım adım `0.011765`. Simetrik `S = 6 / 127 = 0.047244`; yarım adım `0.023622`. Asimetrik şemanın en kötü durum hatası, simetrik şemanın yarısıdır. Bu, tek tek örneklerin hatasının her zaman daha küçük olacağı anlamına gelmez (yuvarlama bazen şanslıdır), ama sınır budur.

**Adım 6 — Doğrula.** Aşağıdaki tablo ilk tensör için iki şemanın hatasını gösterir.

| t | Asimetrik q | Asimetrik hata | Simetrik q | Simetrik hata |
|---|---|---|---|---|
| -0.10 | -99 | 0.00471 | -6 | 0.00866 |
| 0.25 | -66 | 0.00412 | 14 | 0.00354 |
| 1.10 | 14 | 0.00118 | 61 | 0.00472 |
| 2.30 | 127 | 0.00235 | 127 | 0.00000 |

Tabloda her hata, ilgili şemanın yarım adımından (asimetrik için `0.00529`, simetrik için `0.00906`) küçüktür; bu, yuvarlamanın sınırını doğrular. Bu dört örnekte simetrik şema bazı noktalarda daha iyi çıkıyor, bu yuvarlamanın şansıdır. Asıl karşılaştırma yarım adımlardır. ReLU aralığı `[0, 6]` için yarım adım asimetrikte `0.011765`, simetrikte `0.023622`'dir; yani aynı bit genişliğinde simetrik şema çözünürlüğü yarıya düşürür.

**Bunu AI'sız yazabilir misin?** `t = [-0.5, 0.0, 0.8, 1.2]` tensörü için asimetrik `S` ve `Z`'yi hesapla, sonra her değeri kuantize edip geri okuyarak hatayı yaz. Aynı tensörü simetrik şemayla da kuantize et ve iki hatanın en büyüğünü karşılaştır. Son olarak `[0, 3]` aralığı için yarım adımları hesapla.

## Kendin Yap Projeleri

::: dikkat
Bu iki projede yapay zekâ aracına kod yazdırma. Bölüm 6'daki kural geçerli: önce kendin dene, takıldığında kavramı sor, cevabı değil. Bu bölümde yazdığın ve bu bölümde verilen kodlar başlangıç noktası olarak kullanılabilir, ama projelerin çözümü yazmak sana aittir.
:::

### Proje 1 (★★): Sabit noktalı matematik kütüphanesi

**Amaç.** Q1.15 biçiminde küçük bir matematik kütüphanesi yaz: çarpma, bölme, doygunluklu toplama ve çıkarma, ayrıca `tanh` ve sigmoid için tablo aramasıyla doğrusal ara değerleme. Kütüphane, bu bölümün `tinyml.c` dosyasıyla aynı ilkeleri (yuvarlama, doygunluk, `int64_t` birikim) kullanmalıdır.

**Beklenen davranış.** Kütüphane şu işlevleri sunmalı: `q15_mul(a, b)`, `q15_div(a, b)` (`b ≠ 0` ve sonucun aralığa sığdığı durumlar için), `q15_add_sat(a, b)`, `q15_sub_sat(a, b)`, `q15_tanh(x)` ve `q15_sigmoid(x)`. Her işlev, karşılık gelen float fonksiyonun Q1.15 kuantizasyonuna göre sonucuyla karşılaştırılmalıdır.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Çarpma için 32-bit ara sonucu tut ve kaydırmadan önce yuvarlama sabitini ekle. Bölme için pay değerini `2^15` ile ölçekleyip `int32_t` üzerinde böl; işaret ve sıfır bölme durumlarını ayrıca ele al. `tanh` için `[-4, 4]` aralığında eşit aralıklı bir tablo hazırla; girdi bu tablonun iki komşu noktası arasında kalırsa doğrusal ara değerleme yap. Tablo değerlerini derleme zamanında bir dizide tut (Bölüm 25'teki statik bellek ilkesi).

**Başarı kriterleri.**
- Çarpma, 10 000 rastgele Q1.15 çifti üzerinde float sonucundan en fazla bir kuantizasyon adımı (`2^-15`) farklı.
- Doygunluklu toplama, `32767 + 1` ve `-32768 - 1` için sınır değerleri döndürür, taşmaz.
- Tablo ve ara değerleme ile `tanh`, `[-4, 4]` aralığında float `tanh`'tan en fazla `10^-3` farklı.
- Kod `-fsanitize=address,undefined` ile derlendiğinde hata vermez ve `-Wall -Wextra` uyarısı üretmez.

### Proje 2 (★★★): Kendi telemetri hattını kur ve bir anomali tipi ekle

**Amaç.** Bu bölümdeki EV hattını uçtan uca kendin tekrarla, ama bir değişiklik yap: veri setine dördüncü bir anomali tipi ekle. Örneğin sıcaklık sensörünün donması (ardışık aynı değer), ya da hücre geriliminde ani bir sıfır okuması (sensör kopması). Yeni anomali tipi, hem eğitimi hem de kuantizasyonu etkileyecektir.

**Beklenen davranış.** Hat şu sırayla çalışmalı: veri üretimi (yeni tip dahil), eğitim, int8 kuantizasyon, C başlık dosyası üretimi, host üzerinde bit-tam test (0 uyuşmazlık), Cortex-M4 derlemesi (uyarısız) ve boyut dökümü. Raporun sonunda üç sayı olmalı: test doğruluğu, kaçırılan anomali sayısı ve flash ile RAM kullanımı.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Yeni anomali tipini `anomali_uygula` içinde bir `elif` olarak ekle; ama sensör donmasını aynı değerin tekrarı olarak üretmek, öznitelik olarak `std = 0` ve `eğim = 0` yaratır. Bu durumda özniteliklerin normalizasyonunda bölme sıfıra yaklaşabilir; standart sapmaya küçük bir alt sınır ekle. Ardından eğitim ve kuantizasyonu aynı şekilde çalıştır; C tarafında hiçbir değişiklik gerekmemelidir, çünkü hat yalnızca sabit dizileri değiştirir. Yeni tipin kaçırılıp kaçırılmadığını ayrıca say.

**Başarı kriterleri.**
- Host bit-tam testi 2000 pencerede ve 1000 rastgele vektörde sıfır uyuşmazlık veriyor.
- Cortex-M4 derlemesi `-Wall -Wextra` ile uyarısız tamamlanıyor.
- Flash ve RAM dökümü, model ve kod ayrı ayrı raporlanmış.
- Raporda, yeni anomali tipinin kesinlik ve duyarlılığı ayrı ayrı yazılmış; kaçırılan örneklerin hangi şiddette olduğu bir tablo ile gösterilmiş.

### Ek Alıştırmalar

**Zorluk etiketleri:** ★ kolay, ★★ orta, ★★★ zor. Mülakat etiketli sorular klasik mülakat problemleridir; önce cevabını kâğıda yaz, sonra kodla doğrula.

1. **(★) Parametre sayımı.** `m` girdi ve `n` çıktılı bir tam bağlı katmanın parametre sayısı nedir? Bias dahil ve hariç için iki ayrı formül yaz ve 16 → 4 → 3 ağı için değerlerini hesapla.
2. **(★) Q7 aralığı.** Q1.7 biçiminde en küçük ve en büyük temsil edilebilir değerleri yaz. Adım aralığı nedir? `0.3` sayısının Q1.7 karşılığını ve geri okunan değerini bul.
3. **(★★) Taşma sınırı (Mülakat).** Bir int32 birikiminin taşmasına kaç adet `int8 × int8` çarpım yetmez? En kötü durum girdilerini düşünerek sınırı bul ve bu sınırın bu bölümdeki ağ için yeterli olup olmadığını yaz.
4. **(★★) Yuvarlama yönü.** `-0.5` değerini tamsayıya yuvarlarken üç yöntem (sıfıra doğru kesme, `floor(x + 0.5)`, en yakın çift) ne verir? Bu bölümdeki yöntem hangisidir ve neden?
5. **(★★) Sıfır noktası (Mülakat).** Asimetrik kuantizasyonda `Z` neden tamsayı olmak zorundadır? `Z`'nin tamsayı olmaması hangi işlemi bozar?
6. **(★) ReLU ve Z.** ReLU çıkışı için asimetrik kuantizasyon `Z = -128` verirse, bu ReLU'yu bedava yapar. Bu cümleyi bir örnekle açıkla.
7. **(★★) Simetrik mi, asimetrik mi?** Ağırlıkların dağılımı `[-0.8, 0.9]` ise hangi şema daha uygun? Aktivasyonların dağılımı `[0, 4]` ise? Gerekçeni yaz.
8. **(★★) Argmax ölçeği (Mülakat).** İki sınıf için tamsayı logit'ler `(20, 15)` olsun, ama birinci logit'in ölçeği 0.1, ikincinin ölçeği 0.3 olsun. Gerçek karar hangisidir? Bu neden kanal başına ölçeklemenin son katmanda sorun yaratabileceğini gösterir?
9. **(★★★) Kanal başına bellek.** Kanal başına ölçekleme için her kanal ayrı bir `M0` ve `rs` saklar. 128 kanallı bir katmanda bu ek bellek ne kadardır? Bunu ağırlık belleğiyle karşılaştır.
10. **(★★★) Döngü hizalaması (Mülakat).** `SMLAD` komutu iki 16-bit çarpımı toplar, ama ağırlıklar 8-bit tutuluyor. Girdi uzunluğu 4'ün katı değilse ne olur? Bu bölümdeki `dot_dsp` fonksiyonu bu durumu nasıl varsayar ve bunu yanlış kullanırsan ne olur?
11. **(★★) Eğim formülü.** Bir pencerede eğim, `Σ (t - t̄)(x - x̄) / Σ (t - t̄)²` ile hesaplanır. Bu formül, düz bir çizginin eğimini bulmak için neden yeterlidir? Gürültü eğimi nasıl etkiler?
12. **(★★★) Enerji bütçesi.** Bir sensör 10 Hz'de örnek verir, pencere 3.2 saniyedir ve her çıkarım 40 µs sürer. Ortalama işlemci çalışma oranı nedir? Sistem her pencerede uykudan uyanıp sonra tekrar uyuyorsa, bu oranın enerjiye etkisi nedir?

## Kod Okuma Egzersizi

Bu bölümde yazdığımız yeniden ölçekleme ile ARM'ın CMSIS-NN kütüphanesindeki yeniden ölçekleme fonksiyonunu karşılaştıracağız. Kaynak, CMSIS-NN deposunun **v6.0.0** etiketindeki `Include/arm_nnsupportfunctions.h` dosyasıdır. Dosya, raw.githubusercontent.com yerine jsdelivr aynası (cdn.jsdelivr.net/gh/ARM-software/CMSIS-NN@v6.0.0/...) üzerinden indirildi; içerik aynı etikete aittir. Telif başlığı Apache-2.0 lisansını belirtir. Aşağıdaki kesit 1330-1347, 1357-1378 ve 1399-1413 satırlarını içerir. Kodun okunabilirliği için iki fonksiyon imzası ile bir çağrı satırı 70 sütuna sığacak biçimde bölündü; kelimesi kelimesine aynıdır, yalnızca satır sonları değişti. `__STATIC_FORCEINLINE` makrosu ve `arm_nn_long_long` birliği bu kesitte tanımlanmamıştır; bunlar aynı başlık dosyasının başka bölümlerinde yer alır.

Önce birinci kısım, sabit-noktalı çarpımı yapan fonksiyondur. Burada `val` ile `multiplier` çarpımının üst 32 bitini alıyorsun; yani bu, Q31 sayılarının çarpımıdır.

```c
__STATIC_FORCEINLINE int32_t arm_nn_doubling_high_mult_no_sat(
    const int32_t m1, const int32_t m2)
{
    int32_t result = 0;
    union arm_nn_long_long mult;

    // Rounding offset to add for a right shift of 31
    mult.word.low = 1 << 30;
    mult.word.high = 0;

    // Gets resolved as a SMLAL instruction
    mult.long_long = mult.long_long + (int64_t)m1 * m2;

    // Utilize all of the upper 32 bits. This is the doubling step
    // as well.
    result = (int32_t)(mult.long_long >> 31);

    return result;
}
```

İkinci kısım, yuvarlamalı kaydırmadır. Yorumunda "midpoint rounded away from zero" yazıyor: yani tam ortadaki değerler sıfırdan uzağa yuvarlanır.

```c

__STATIC_FORCEINLINE int32_t arm_nn_divide_by_power_of_two(
    const int32_t dividend, const int32_t exponent)
{
    int32_t result = 0;
    const int32_t remainder_mask = (1 << exponent) - 1;
    int32_t remainder = remainder_mask & dividend;

    // Basic division
    result = dividend >> exponent;

    // Adjust 'result' for rounding (mid point away from zero)
    int32_t threshold = remainder_mask >> 1;
    if (result < 0)
    {
        threshold++;
    }
    if (remainder > threshold)
    {
        result++;
    }

    return result;
}
```

Üçüncü kısım, yeniden ölçekleme fonksiyonunun kendisidir. `CMSIS_NN_USE_SINGLE_ROUNDING` tanımlıysa tek yuvarlamalı yol, tanımlı değilse iki aşamalı yol çalışır. Varsayılan yol, önce çarpımı yapar, sonra kaydırır.

```c

__STATIC_FORCEINLINE int32_t arm_nn_requantize(const int32_t val,
                                             const int32_t multiplier,
                                             const int32_t shift)
{
#ifdef CMSIS_NN_USE_SINGLE_ROUNDING
    const int64_t total_shift = 31 - shift;
    const int64_t new_val = val * (int64_t)multiplier;

    int32_t result = new_val >> (total_shift - 1);
    result = (result + 1) >> 1;

    return result;
#else
    return arm_nn_divide_by_power_of_two(
        arm_nn_doubling_high_mult_no_sat(
            val * (1 << LEFT_SHIFT(shift)), multiplier),
        RIGHT_SHIFT(shift));
#endif
}
```

**Sorular — cevaplamadan geçme:**

1. `arm_nn_doubling_high_mult_no_sat` fonksiyonunda `mult.word.low = 1 << 30` ile başlayıp `>> 31` yapmak neden yuvarlama yapar? Bu sabit, bu bölümdeki `2^(rs-1)` ile hangi açıdan benzer, hangi açıdan farklıdır?
2. `arm_nn_divide_by_power_of_two` içindeki `threshold` değeri neden `remainder_mask >> 1` ile başlar ve sonucu negatifse neden bir artar? Bu, "sıfırdan uzağa yuvarlama" kuralını nasıl uygular? Aynı örneği `-5 / 4` ile düşün: `-1.25` hangi değere yuvarlanır?
3. Bu bölümdeki `katman1` fonksiyonu tek bir yuvarlama yapar (`(acc · M0 + 2^(rs-1)) >> rs`). CMSIS-NN varsayılan yolu ise iki yuvarlama yapar (önce `>> 31` ile, sonra `>> rs` ile). İki yolun sonucu hangi durumlarda farklı olabilir? Bu farkın ağın doğruluğu üzerinde pratik etkisi olur mu? Cevabını bir örnekle destekle.
4. `arm_nn_requantize` içindeki `LEFT_SHIFT(shift)` ve `RIGHT_SHIFT(shift)` makroları neden iki ayrı kaydırma yapar? Bu, bizim `rs` değerimizin (her zaman pozitif, 37 civarı) hangi durumla karşılık geldiğini düşünmeni ister.
5. `CMSIS_NN_USE_SINGLE_ROUNDING` yolunda `total_shift - 1` kaydırması ve ardından `(result + 1) >> 1` neden yapılır? Bu iki adım toplamda hangi yuvarlamayı yapar?
6. Bu kesitte 64-bit çarpım açıkça `int64_t` ile yapılmıyor; `arm_nn_doubling_high_mult_no_sat` içinde `(int64_t)m1 * m2` olarak yazılıyor. Bu yazım, taşmayı nasıl önler ve neden `int32_t * int32_t` yazmak tanımsız davranış olurdu?

## Bölüm Özeti

- **Uçta çıkarım**, kararı gecikme, gizlilik, bağlantı, bant genişliği ve güç açısından yerel tutar; bulut ile MCU arasında üç donanım sınıfı vardır ve her biri farklı kısıtlar taşır.
- **Model**, parametreler ve hesap grafiğidir; eğitim (kayıp ve gradyan inişi) başka yerde yapılır, cihazda yalnızca ileri geçiş çalışır.
- **Bütçe**, parametre belleğini (`P · b / 8`), tepe aktivasyon belleğini, MAC sayısını ve gecikmeyi (`MAC · c / f`) birlikte hesaplamaktır. Uygulamada RAM'i çoğu zaman model değil sensör tamponu belirler.
- **Sabit nokta** (Q1.15), kayan noktanın maliyetini ve belleğini azaltır; çarpımda yuvarlama ve doygunluk zorunludur, C'de işaretli taşma tanımsız davranıştır.
- **Kuantizasyon** `r = S (q - Z)` ile yapılır; asimetrik şema aralığın tamamını kullanır, simetrik şema ağırlıklar için uygundur. Tamsayı yeniden ölçekleme `M0` ve `rs` ile tamsayı-only yapılır ve sıfır noktası terimi onyargıya katlanır.
- **Doğruluk**, bit genişliğiyle birlikte ölçülmelidir: ağırlıklar 4 bite kadar ucuzdur, aktivasyonlarda kalibrasyon yöntemi (min/maks ya da yüzdelik) belirleyicidir.
- **Uçtan uca hat** (veri, eğitim, kuantizasyon, C dizisi, host bit-tam testi, Cortex-M4 derlemesi, boyut ve komut sayımı) her adımda ölçülebilir olmalıdır; bu bölümde host testi bit-tam, derleme ise ölçülerek yapıldı, donanım çalıştırması yapılmadı.
- **Güvenilirlik**, dağılım kayması, giriş doğrulama ve güvenli varsayılan kararlar olmadan bir TinyML sistemi sahada güvenli değildir.

**Sonraki bölümde:** Bölüm 47, Ayrık Matematik ile Kısım XII'ye (Matematik) başlıyoruz. Bu bölümde Kısım XI'in son bölümünü bitirdik: bare-metal C (Bölüm 43), kesmeler ve zamanlayıcılar (Bölüm 44), iletişim protokolleri (Bölüm 45) ve şimdi edge AI. Bu zincir, bir sensörden veri okuyup, bu veriyi bir modelle işleyip karar vermeye kadar olan yolu kapatır. Bölüm 47'de ise bu kararların arkasındaki sayma, mantık ve grafların dilini kuracağız; bu dil, bir sonraki kısmın olasılık, lineer cebir ve optimizasyon bölümlerinin de temelidir.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. Bir modelin bir mikrodenetleyiciye sığıp sığmadığını nasıl hesaplarsın? Parametre belleğini ve tepe aktivasyon belleğini ayrı ayrı nasıl bulursun, RAM'i asıl hangisi belirler?
2. int8 çarpımların toplamı neden int32 birikim gerektirir? En kötü durumda kaç terim taşmadan toplanabilir?
3. Asimetrik kuantizasyonda sıfır noktası (zero point) neden var? ReLU çıkışı için `Z = -128` olması neyi ifade eder?
4. Yeniden ölçekleme çarpanı `m = S_in · S_w / S_out` neden `(0, 1)` aralığındadır ve bunu neden kayan nokta olmadan uygularsın?
5. Min/maks kalibrasyonu aykırı değerlerle nasıl bozulur? Bunu azaltmanın iki yolunu söyle.
6. Argmax, logit'ler ortak bir ölçekte değilse neden yanlış sonuç verir? Son katmanın kanal başına ölçeklenmemesinin nedeni bu mudur?
7. Bir sistemin doğruluğu laboratuvarda yüzde 99 ama sahada düşüyor. Hangi nedenleri ve hangi izlemeleri düşünürsün?
:::
