%% kisim_no: XIII
%% kisim_ad: Sinyal & Paralel
%% kisim_ayrac: evet
%% bolum_no: 52
%% baslik: DSP Temelleri

## Giriş: Dünyayı sayılara çevirmek

Bir İHA'nın kanadındaki ivmeölçer, bir radarın anteninden dönen yankı, bir sonar hidrofonunun denizden topladığı basınç dalgası, bir mikrofonun sesi: hepsi zamanla değişen fiziksel bir büyüklüktür. İşlemci ise yalnızca sayı görür. Aradaki köprü sinyal işlemedir (signal processing), ve dijital sinyal işleme (DSP) bu köprünün mühendislik tarafıdır. Bir sensörden gelen ham veri ile bir karar arasında duran her şey, yani gürültüyü temizlemek, bir hedefin hızını ölçmek, bir sesi tanımak, bir açıyı kestirmek, DSP'nin işidir.

Bu bölüm savunma ve gömülü tarafta en sık karşına çıkacak temel fikirleri kurar. Radarda eşleşik filtre ile gecikme kestirimi, sonarda Doppler kayması ile hız ölçümü, IMU'da filtreleme ile eğim kestirimi, bir EV'nin batarya akımını düzleştirme ve bir ses kaydında spektrogram okuma bu bölümün konularıdır. Mülakatlarda "bir sinyali neden örnekleriz?", "neden FFT yaparız?" ve "neden FIR değil IIR kullanıyorsun?" gibi sorular çok gelir; bu soruların cevabı bu bölümde ölçülerek verilecek.

Bölüm 19'da hızlı Fourier dönüşümünü (FFT) polinom çarpımı için görmüştün. Burada aynı algoritmanın sinyal tarafını kuracağız: polinomun katsayıları yerine bir sinyalin örnekleri, çarpım yerine konvolüsyon. Bölüm 46'da TinyML için pencereleme, Q15 sabit nokta ve Cortex-M4 DSP komutlarını gördün; bu bölümde o araçları bir filtrenin içine koyacağız. Bölüm 44'te bir zamanlayıcı ile periyodik örnekleme yapmayı, Bölüm 45'te UART hatlarındaki zamanlamayı öğrendin; burada o örneklerin neden belli bir hızda alındığını matematiksel olarak göreceğiz. Bölüm 51'deki Shannon–Hartley formülündeki `B` ve `S/N` kavramları burada örnekleme hızı ve kuantizasyon gürültüsü olarak geri dönecek.

Yaklaşım her zamanki gibi: her kavram için bir sezgi, Unicode düz metin matematik, numpy ile sıfırdan gerçekleme, varsa scipy ile doğrulama ve bir grafik. Simülasyonlarda `numpy.random.default_rng(52)` ile sabit tohum kullanıyoruz; aynı sayıları sen de üretebilirsin. Bölümdeki sayılar, bölüm yazılırken çalıştırılan betiklerin çıktılarıdır.

::: not
Bu bölümdeki sentetik sinyaller açıkça etiketlidir: IMU, EV akımı ve radar verileri gerçek sensörden alınmadı, kontrollü bir modelden üretildi. Kestirim yöntemlerinin karşılaştırması bu verilerde geçerlidir; gerçek bir donanımda ayrıca ölçüm yapılmalıdır. Gömülü derlemeler yalnızca derlendi ve boyutu ölçüldü; kartta çalıştırılmadı.
:::

## 52.1 Sürekli ve ayrık sinyal: örnekleme ve Nyquist–Shannon

Doğadaki sinyal sürekli bir zaman fonksiyonudur: her an, `x(t)` gibi bir değeri vardır. Bir ivmeölçerin çıkışı bir voltajdır, bu voltaj her an değişir. İşlemci ise belirli aralıklarla okuma yapabilir. Saniyede `fs` kez okursan, `T = 1/fs` aralıklı bir dizi elde edersin:

x[n] = x(nT) = x(n / fs)

Bu dizi ayrık zamanlı bir sinyaldir: indeks `n` tam sayıdır ve her değer bir ölçümdür. Ayrık sinyal, sürekli sinyalin bir "fotoğrafı"dır; sorun şu: fotoğraf her zaman aslı temsil eder mi? Cevap, örnekleme hızına ve sinyalin frekans içeriğine bağlıdır.

Bir sinyalin en yüksek frekansını `f_max` ile gösterelim. Nyquist–Shannon örnekleme teoremi (genel bilgi, 1920'ler–1940'lar Nyquist ve Shannon'a atfedilir) şunu söyler: bant sınırlı bir sinyal, örnekleme hızı `fs > 2 f_max` olacak şekilde alınırsa, örneklerden sürekli sinyal hatasız geri kurulabilir. `fs/2` değerine Nyquist frekansı denir; örnekleme hızının yarısıdır. Frekansı Nyquist'in üzerinde olan bileşen, örneklerde kendini bir alçak frekanslı bileşen gibi gösterir. Buna örtüşme (aliasing) denir ve bir sonraki alt başlığın konusudur.

Neden bu kadar önemli? Bir radar darbesinin frekansı gigahertz mertebesindedir; ama onu doğrudan dijitalleştirmek zor ve pahalıdır. Çoğu sistem önce sinyali bir karıştırıcı ile alçak frekansa indirir (taban bant), sonra örnekler. Bu yüzden `fs` seçimi bir mühendislik kararıdır: hedef hızı, menzili, gürültü tabanını ve işlemci bütçesini birlikte düşünürsün.

Teorem bir "yeterli koşul"dur; `fs = 2 f_max` tam sınırdır ve pratikte yetersizdir. Bir kuralı şöyle kullan: gerçek sistemde Nyquist'in biraz üstünde, `fs ≈ 2,5 f_max` ile `5 f_max` arasında örnekle, ve anti-aliasing filtresiyle `f_max`'ı önceden sınırla (bkz. 52.2). Örnekleme hızını nasıl seçeceğin, hangi frekanslara ihtiyacın olduğuna bağlıdır: ses 20 kHz'e kadar, bir IMU'nun titreşim analizi birkaç yüz Hz'e kadar yeterlidir.

::: ipucu
Örnekleme hızı bir sayıdır ama sinyalin özelliğidir. Aynı 1 kHz'lik tonu `fs = 8 kHz` ve `fs = 1,5 kHz` ile örnekleyen iki sistem aynı diziyi üretmez. Birinci sistem tonu yakalar, ikincisi onu alias'a çevirir.
:::

## 52.2 Örtüşme (aliasing) ve örtüşme önleyici filtre

Örtüşme, Nyquist frekansını aşan bir bileşenin örneklerde daha düşük bir frekans gibi görünmesidir. Bir örnek dizisi yalnızca bir sinyali temsil eder; birden fazla sürekli sinyal aynı örnekleri üretebilir. Tekerlek etkisi (wagon-wheel effect) buna güzel bir gündelik örnektir: film çekiminde bir tekerlek her karede biraz döndüğünde geriye dönüyor gibi görünür. Kamera saniyede 24 kare alır, tekerlek bir kareden diğerine neredeyse tam tur atar; gözlemci yalnızca kareleri görür.

Somut bir örnek: `fs = 10 kHz` ile örnekleme yapalım ve iki sinüse bakalım, 7 kHz ve 3 kHz. Örnek anları `t = n/fs`. Bu iki sinyal arasındaki fark:

sin(2π · 7000 · n / 10000) = sin(2π · n − 2π · 3000 · n / 10000) = −sin(2π · 3000 · n / 10000)

`2πn` terimi her tam sayı `n` için `2π`'nin katı olduğundan sinüsü değiştirmez. Demek ki 7 kHz'lik sinyalin örnekleri, 3 kHz'lik sinyalin örneklerinin negatifidir. 7 kHz, `fs − 3 kHz` olarak katlanmıştır. Genel kural: `f` frekansı, en yakın `fs`'nin katına olan uzaklık olarak görünür, yani `|f − k · fs|` ile `fs/2` arasındaki en küçük değer.

Aşağıdaki program bu eşitliği sayılarla doğrular. `x7` ve `x3` diziler arasındaki fark sıfıra yakındır (`2,78 · 10⁻¹⁵` makine hassasiyeti). Program aynı zamanda 52.3'teki nicemleme deneyini de içerir; ikinci yarıyı oraya geldiğimizde açıklayacağız.

```python
# ornekleme.py - Bolum 52.2-52.3: ortusme ve nicemleme
import numpy as np

# --- 52.2: 7 kHz sinyal, fs = 10 kHz ile ornekleniyor
fs = 10_000.0
n = np.arange(12)
t = n / fs
x7 = np.sin(2 * np.pi * 7000 * t)
x3 = np.sin(2 * np.pi * 3000 * t)
print("n    7 kHz         3 kHz")
for k in range(6):
    print(f"{k:<4} {x7[k]:+.6f}    {x3[k]:+.6f}")
print("max|x7 + x3| =", f"{np.max(np.abs(x7 + x3)):.2e}")

# --- 52.3: N bitlik tekduze nicemleyici, tam olcek [-1, 1)
def nicemle(x, N):
    adim = 2.0 ** (1 - N)
    q = adim * np.round(x / adim)
    return np.clip(q, -1.0, 1.0 - adim)

rng = np.random.default_rng(52)
faz = rng.uniform(0, 2 * np.pi)
t = np.arange(200_000) / 200_000.0
x = np.sin(2 * np.pi * 37 * t + faz)
p_sinyal = np.mean(x ** 2)
print("\nN   SNR olculen   6,02N+1,76")
for N in (4, 6, 8, 12, 16):
    e = nicemle(x, N) - x
    snr = 10 * np.log10(p_sinyal / np.mean(e ** 2))
    print(f"{N:<3} {snr:10.2f} dB   {6.02 * N + 1.76:10.2f} dB")
```

```term
$ python ornekleme.py
n    7 kHz         3 kHz
0    +0.000000    +0.000000
1    -0.951057    +0.951057
2    +0.587785    -0.587785
3    +0.587785    -0.587785
4    -0.951057    +0.951057
5    +0.000000    +0.000000
max|x7 + x3| = 2.78e-15

N   SNR olculen   6,02N+1,76
4        23.24 dB        25.84 dB
6        36.40 dB        37.88 dB
8        49.12 dB        49.92 dB
12       73.79 dB        74.00 dB
16       98.07 dB        98.08 dB
```

Şekil 52.1, bu olayı sürekli eğrilerle gösteriyor. 7 kHz'lik sinüs (düz) ile 3 kHz'lik sinüs (kesikli) aynı örnek noktalarında (`×` ve `●`) kesişiyor. Örnekleyici için bu iki sinyal ayırt edilemez.

![Şekil 52.1: 10 kHz'de örneklenen 7 kHz sinüs, 3 kHz sinüsle aynı örnekleri üretir. Yalnızca noktalara bakan bir sistem iki sinyali karıştırır.](gorseller/b52_ornekleme_ortusme.png)

**Örtüşme önleyici filtre (anti-aliasing filter).** Çözüm, örneklemeden önce Nyquist'in üstündeki bileşenleri analog yolda kesmektir. Bu filtre bir alçak geçiren analog filtredir ve tasarımı, geçirme bandı ile durdurma bandı arasında yeterli bir geçiş bölgesi gerektirir. Gerçek sistemlerde filtre kesim frekansı `fs/2`'nin biraz altındadır, çünkü hiçbir analog filtre kenarında sıfıra iner. Bu yüzden `fs`'i biraz büyük seçmek hem kolaylık hem de güvenlik sağlar. Örtüşme sonrası düzeltilemez: bir kez katlanan bilgi bir daha geri alınamaz. Bu yüzden önleme filtresi, sonradan yazılacak bir yazılım düzeltmesinden daha önemlidir.

::: dikkat
Yazılım filtresi, örneklemeden sonra örtüşmeyi geri alamaz. Dijital bir alçak geçiren filtre yalnızca örneklenmiş dizideki yüksek frekansları bastırır; katlanmış 7 kHz zaten 3 kHz olarak içeridedir ve ondan ayrılamaz. Anti-aliasing işini donanımda yap.
:::

## 52.3 Nicemleme: ADC bit sayısı ve SNR

Örnekleme zamanı ayrıklaştırır; nicemleme (quantization) değeri ayrıklaştırır. Bir ADC (analog–dijital dönüştürücü) bir voltajı `N` bitlik bir tam sayıya çevirir. `N` bit, `2^N` farklı seviye demektir. Tam ölçek aralığı `[−1, 1)` olan tekdüze bir nicemleyicinin adımı `Δ = 2^(1−N)`'dir ve her değeri en yakın seviyeye yuvarlar. Yuvarlama hatası `e = q(x) − x` her örnekte farklıdır; sinyal yeterince karmaşıksa bu hata yaklaşık olarak `[−Δ/2, Δ/2]` aralığında düzgün dağılmış bir gürültü gibi davranır.

Düzgün dağılımlı bir hatanın ortalama karesi `E[e²] = Δ²/12`'dir (bkz. Bölüm 49'da düzgün dağılım ve beklenen değer). Tam ölçekli bir sinüsün gücü `1/2`'dir. Sinyal-gürültü oranı (SNR) desibel cinsinden:

SNR = 10 log₁₀( (1/2) / (Δ²/12) ) = 10 log₁₀(6 · 2^(2N−2))

Logaritmayı açarsak `SNR ≈ 6,02 N + 1,76` dB elde edilir. Bu formül mühendislikte ezberlenir: her ek bit yaklaşık 6 dB kazandırır, yani gürültü tabanını yarıya (genlik olarak) indirir. Formül yalnızca tam ölçekli bir sinüs ve yeterince rastgele bir hata için geçerlidir; düşük bitlerde ya da sabit bir sinyalde hata rastgele olmaz ve sapma büyür.

Aynı programın ikinci yarısı (`nicemle` fonksiyonu ve son döngü) tam ölçekli bir sinüsü `N = 4, 6, 8, 12, 16` bit ile nicemler ve ölçülen SNR'yi formülle karşılaştırır. Çıktının son beş satırı bu ölçümdür.

Ölçüm, formülün yüksek bitlerde (12 ve 16) 0,1 dB içinde olduğunu, düşük bitlerde (4) ise yaklaşık 2,6 dB sapma gösterdiğini söylüyor. Bu sapma, düşük bitte hatanın tekdüze dağılımdan uzaklaşmasından gelir: sinüsün tepe noktalarında seviye doyumu ve yuvarlama, hatayı sinyalle ilişkili hale getirir. Metinde "6,02N + 1,76" yazarken bunun geniş bitler için bir yaklaşım olduğunu bil.

![Şekil 52.2: Solda 3 bitlik nicemleme (basamaklı çizgi) ve gerçek sinüs; sağda bit sayısına göre ölçülen SNR ile 6,02N + 1,76 doğrusu.](gorseller/b52_nicemleme_snr.png)

Mühendislik sonucu şudur. 12 bitlik bir ADC'nin teorik SNR'si yaklaşık 74 dB'dir; 16 bitlik olan 98 dB. Ama ADC'nin kendi gürültüsü, referans gerilimi ve sensörün gürültüsü de vardır; efektif bit sayısı (ENOB) çoğu zaman etiket değerinden birkaç bit düşüktür. Bölüm 46'daki kuantizasyon bölümünde tam sayıya eşlemenin doğruluğa etkisini ölçmüştük; burada aynı hatanın kaynağını görüyorsun: bit genişliği bir gürültü tabanı belirler ve bu taban, filtrelerin ulaşabileceği dinamik aralığı sınırlar.

## 52.4 Ayrık zamanlı sistemler ve konvolüsyon

Bir sinyal işleme bloğunu (filtre, kazanç, gecikme) bir kutu olarak düşün: girişe bir dizi `x[n]` verilir, çıkışta `y[n]` çıkar. Bu kutunun iki özelliği, mühendislikte bir sistemi çözümlemek için yeterlidir.

**Doğrusallık.** Girişleri toplarsan çıkışlar da toplanır, ölçeklersen çıkış da aynı oranda ölçeklenir. Bir sensörün kalibrasyon katsayısı doğrusaldır; bir diyot ise değildir.

**Zamanla değişmezlik.** Girişi `k` örnek geciktirirsen çıkış da aynı `k` kadar gecikir, şeklini değiştirmez. Sabit katsayılı bir filtre zamanla değişmez; katsayısı her örnekte değişen bir uyarlamalı filtre ise değildir.

Doğrusal ve zamanla değişmeyen (LTI) bir sistem tek bir diziyle tamamen tanımlanır: birim dürtü `δ[n]`'e verdiği cevap, dürtü yanıtı `h[n]`. Dürtü, `n = 0`'da 1, diğer her yerde 0 olan dizidir. Herhangi bir girişi dürtülerin toplamı olarak yazabildiğin için (`x[n] = Σ_k x[k] δ[n−k]`), doğrusallık ve zaman değişmezliği çıkışı şöyle verir:

y[n] = Σ_k x[k] · h[n − k]

Bu işleme konvolüsyon (convolution) denir ve `y = x * h` ile gösterilir. Formülü gözünde canlandırmak için şunu düşün: her giriş örneği `x[k]` kendi başına bir dürtü gibi davranır; kendi ölçeğinde ve gecikmesinde `h`'nin bir kopyasını üretir. Bütün bu kopyalar toplanır.

Nedensellik (causality): `n < 0` için `h[n] = 0` ise sistem yalnızca geçmiş girişlere bakar. Gerçek zamanlı bir sistemde gelecek örneği bilemeyeceğin için bu bir zorunluluktur. Kararlılık (stability, BIBO): sınırlı her girişe sınırlı çıkış veriyorsa, `Σ_n |h[n]| < ∞` olmalıdır. Bir sonraki bölümde iki sınırlı `h` örneğini göreceğiz.

Elle küçük bir örnek. `x = [1, 2, 3]` ve `h = [0,5; 0,5]` (iki noktalı ortalama). `y[0] = 1·0,5 = 0,5`; `y[1] = 1·0,5 + 2·0,5 = 1,5`; `y[2] = 2·0,5 + 3·0,5 = 2,5`; `y[3] = 3·0,5 = 1,5`. Çıkış uzunluğu `N + M − 1 = 4`'tür. Aşağıdaki program bu hesabı, kendi dört iç döngülü gerçeklememizle ve `np.convolve` ile karşılaştırır; ayrıca dürtü ile konvolüsyonun sistemin kendisini verdiğini gösterir.

```python
# konvolusyon.py - Bolum 52.4: dogrudan konvolusyon ve dogrulama
import numpy as np

def konv(x, h):
    """y[n] = sum_k x[k] * h[n-k], dogrudan tanim."""
    N, M = len(x), len(h)
    y = np.zeros(N + M - 1)
    for n in range(N + M - 1):
        for k in range(N):
            if 0 <= n - k < M:
                y[n] += x[k] * h[n - k]
    return y

x = np.array([1.0, 2.0, 3.0])
h = np.array([0.5, 0.5])
print("elle ornek y =", konv(x, h))
print("np.convolve  =", np.convolve(x, h))

rng = np.random.default_rng(52)
x = rng.standard_normal(200)
h = rng.standard_normal(31)
fark = np.max(np.abs(konv(x, h) - np.convolve(x, h)))
print("200 x 31 rastgele, max fark =", f"{fark:.2e}")

# birim durtu (delta) ile konvolusyon, sistemin kendisini verir
delta = np.array([1.0, 0.0, 0.0])
print("delta * h =", np.round(konv(delta, h[:4]), 4))
print("h[:4]     =", np.round(h[:4], 4))
```

```term
$ python konvolusyon.py
elle ornek y = [0.5 1.5 2.5 1.5]
np.convolve  = [0.5 1.5 2.5 1.5]
200 x 31 rastgele, max fark = 3.55e-15
delta * h = [-0.4803  1.5183 -0.4031 -0.7905  0.      0.    ]
h[:4]     = [-0.4803  1.5183 -0.4031 -0.7905]
```

Şekil 52.3, bu kaydırma işlemini `n = 2, 3, 4` için gösterir: bordo ters çevrilmiş `h`, mavi `x` üzerinde kayar ve üst üste binen çarpımlar toplanır.

![Şekil 52.3: Konvolüsyon kaydırması. Mavi x[k]; bordo h[n−k] (ters çevrilip n konumuna kaydırılmış). Üst üste binen çiftlerin çarpımları toplanır.](gorseller/b52_konvolusyon_kaydirma.png)

İlk satırda elle hesapladığımız `[0,5 1,5 2,5 1,5]` dizisi çıkıyor; kendi gerçeklememiz ile `np.convolve` aynı sayıları verir (fark `3,6 · 10⁻¹⁵`). Son satır önemlidir: `δ * h` çıktısı `h`'nin kendisidir. Bu yüzden bir filtrenin katsayıları aynı zamanda onun dürtü yanıtıdır.

Gerçek bir filtre için bu hesap `N` girişte `M` katsayı çarpar: `N · M` çarpma ve toplama. Bu, bir sonraki iki bölümde sık sık karşına çıkacak işlem bütçesinin temel birimidir (bkz. 52.9).

Bölüm 19'da polinom çarpımını gördün: iki polinomun katsayı dizisinin çarpımı tam olarak bu konvolüsyondur. `(1 + 2z)(3 + 4z)` çarpımının katsayıları `[1, 2] * [3, 4] = [3, 10, 8]`'dir. Yani konvolüsyon, polinom çarpımının sinyal dilindeki adıdır; Bölüm 19'daki hızlı çarpım, bu bölümde konvolüsyonu hızlandıracak.

## 52.5 DFT ve FFT: frekans alanına geçiş

Zaman alanındaki bir dizi bir sinyalin ne olduğunu söyler; ama frekans içeriğini görmek için bir dönüşüme ihtiyacın var. Ayrık Fourier dönüşümü (DFT), `N` noktalı bir diziyi `N` frekans bileşenine ayırır:

X[k] = Σ_{n=0}^{N−1} x[n] · e^(−j 2π k n / N),   k = 0, …, N−1

Sezgi şudur: `k`'inci kutu, `k · fs / N` Hz'lik bir karmaşık sinüsle (`e^(−j2πkn/N)` bir dönen vektördür) girişin ne kadar korelasyonlu olduğunu ölçer. Eğer giriş o frekansta bir sinüsse, toplam büyük çıkar; değilse çoğu terim birbirini götürür ve toplam küçük kalır. `X[k]`'nin büyüklüğü `|X[k]|`, o frekansın genliğini (`N` ile orantılı olarak) verir, açısı ise fazı.

İki gözlem her şeyin anahtarıdır. Birincisi, `N` örnekten `N` frekans kutusu çıkar ve aralarındaki frekans çözünürlüğü:

Δf = fs / N

Bir ses kaydını `fs = 1000 Hz`'de ve `N = 64` örnekle analiz edersen, kutu aralığı `15,625 Hz`'dir. Daha ince bir çözünürlük istiyorsan daha uzun bir kayıt (daha büyük `N`) ya da daha yüksek bir `fs` gerekir; sıfır doldurmanın bunu yapmadığını 52.6'da göstereceğiz. İkincisi, gerçek bir sinyalde `N` örneğin sonundan sonuna kadar 'kesilir' ve kesme, spektrumda yayılma yaratır; buna sızıntı (leakage) denir ve 52.6'nın konusudur.

Hesap maliyeti: doğrudan tanımla `N` kutunun her biri için `N` çarpma yapılır, toplam `O(N²)`. Bölüm 19'da gördüğün Cooley–Tukey FFT, bölme–fethetme ile aynı sonucu `O(N log N)` maliyetle verir. Burada tekrar kurmayacağız; `np.fft.fft` bu algoritmanın C gerçeklemesidir. Aşağıdaki program önce DFT'yi iki döngüyle yazar, 125 Hz'lik bir tonun tepe kutusunu (`k = 8`) bulur, sonra süreyi `np.fft` ile karşılaştırır.

```python
# dft.py - Bolum 52.5: DFT tanimi, O(N^2) gerceklemesi ve FFT
import time
import numpy as np

def dft_dongu(x):
    """X[k] = sum_n x[n] e^{-j 2 pi k n / N}, iki dongu."""
    N = len(x)
    X = np.zeros(N, dtype=complex)
    for k in range(N):
        toplam = 0j
        for n in range(N):
            toplam += x[n] * np.exp(-2j * np.pi * k * n / N)
        X[k] = toplam
    return X

fs, N = 1000.0, 64
n = np.arange(N)
x = np.cos(2 * np.pi * 125.0 * n / fs)      # 125 Hz, tam bir kutuda
X = dft_dongu(x)
k_tepe = int(np.argmax(np.abs(X[:N // 2])))
print("tepe kutusu k =", k_tepe,
      " frekans =", k_tepe * fs / N, "Hz")
print("|X[k_tepe]| =", round(abs(X[k_tepe]), 4),
      " (beklenen N/2 =", N // 2, ")")
print("np.fft ile esles:", np.allclose(X, np.fft.fft(x)))

print("\nN      dongu (ms)   np.fft (us)   oran")
rng = np.random.default_rng(52)
```

Kodun devamı:

```python
for N in (256, 512, 1024, 2048):
    xr = rng.standard_normal(N)
    t0 = time.perf_counter()
    dft_dongu(xr)
    t1 = time.perf_counter()
    for _ in range(200):
        np.fft.fft(xr)
    t2 = time.perf_counter()
    d_ms = (t1 - t0) * 1e3
    f_us = (t2 - t1) / 200 * 1e6
    ora = d_ms * 1e3 / f_us
    print(f"{N:<6} {d_ms:10.1f} {f_us:12.2f} {ora:10.0f}")
```

```term
$ python dft.py
tepe kutusu k = 8  frekans = 125.0 Hz
|X[k_tepe]| = 32.0  (beklenen N/2 = 32 )
np.fft ile esles: True

N      dongu (ms)   np.fft (us)   oran
256          73.0         7.61       9585
512         293.1         9.07      32319
1024       1166.6        12.82      91031
2048       4645.0        21.00     221190
```

İlk üç satır doğru çalışmanın kanıtıdır. Ton `fs/N · 8 = 125 Hz` tam bir kutuya denk geldiği için tepe `k = 8`'de, genlik `N/2 = 32`'dir (gerçek kosinüs iki karmaşık bileşene bölünür, her biri yarı genlikte olduğundan). Tabloda son sütun, bizim `O(N²)` gerçeklememizin `np.fft`'ye göre kaç kat yavaş olduğunu gösterir. Bu sayılar makineye göre değişir; orantı artışı `N` iki katına çıktığında dört kat değil yaklaşık iki katın üstünde büyür. Yani `N = 2048`'de `dongu` sürümü yaklaşık 4,8 saniye sürerken FFT yaklaşık 21 mikrosaniye sürüyor. Bu fark, gerçek zamanlı bir sistemde iki yöntem arasındaki tercihi belirler.

Şekil 52.4, aynı tonun iki durumunu gösterir. Solda 125 Hz tam bir kutuya oturur ve spektrumda tek bir çubuk görünür. Sağda 130 Hz kutular arasında kalır; enerji birkaç kutuya yayılır. Bu yayılmanın nedeni sızıntıdır.

![Şekil 52.4: Solda 125 Hz tonun 64 noktalı DFT büyüklüğü (tek kutu, k = 8), sağda 130 Hz tonun (kutular arasında) enerjisi birkaç kutuya yayılmıştır.](gorseller/b52_dft_spektrum.png)

Mühendislik için bir kural: spektrumda tepe frekansını okurken, okuduğun değer `fs/N`'in katıdır. Gerçek tepe frekansı kutuların arasındaysa okuma kutu merkezine kayar. Bu hata sınırı `±Δf/2`'dir; daha iyi tepe kestirimi için pencereleme ve parabolik interpolasyon kullanılır, ama bu bile çözünürlüğü artırmaz.

## 52.6 Pencereleme, spektral sızıntı ve sıfır doldurma

DFT, sonlu bir kayıtta sinyalin periyodik olduğunu varsayar. Kayıt sonunda sinyal sıfıra bir sıçrama yapmışsa, bu sıçrama her frekansa enerji katar; buna spektral sızıntı denir. Tam bir kutuda duran ton sızmaz; kutular arasında kalan ton ise sinc biçimli bir yan lob bulutu üretir. Sızıntıyı azaltmak için kayıt ile bir pencere fonksiyonu `w[n]` çarpılır: `x[n] · w[n]`.

Pencerenin iki özelliği takas (trade-off) oluşturur. Ana lob genişliği, iki yakın tonu ayırabilme yeteneğini belirler; yan lob seviyesi, zayıf bir tonun güçlü tonun sızıntısı altında kalıp kalmayacağını belirler. Dar bir ana lob ile düşük bir yan lob aynı anda elde edilemez. Dört yaygın pencere:

| Pencere | Yan lob (dB) | Ana lob (kutu) | Not |
|---|---|---|---|
| Dikdörtgen | −13 | 2 | Pencere yok; en dar ana lob, en yüksek sızıntı |
| Hann | −31,5 | 4 | Genel amaçlı; kosinüs karesi |
| Hamming | −42 | 4 | Yan lob ilk değerinde düşük, kenarı sıfır değil |
| Blackman | −58 | ≈ 6 | En düşük yan lob, en geniş ana lob |

Yan lob değerleri ve ana lob genişlikleri literatürde bilinen değerlerdir (genel bilgi); aşağıdaki program bunları kendi pencerelerimizle ölçer. Program dört parçadan oluşur: (A) tek bir tonun yan lob ve ana lob ölçümü, (B) güçlü bir tonun yanında `−60 dB`'lik zayıf bir tonun görünürlüğü, (C) iki eşit tonun ayrılma eşiği, (D) sıfır doldurmanın tepe okumaya etkisi.

Pencereleri kendi tanımlarımızla yazıyoruz (Hann için `0,5 − 0,5 cos(2πn/(N−1))`); bu tanım `np.hanning` ile birebir aynıdır.

```python
# pencere.py - Bolum 52.6: pencereleme, sizinti, ayrilma, doldurma
import numpy as np

def pencere(ad, N):
    n = np.arange(N)
    a = 2 * np.pi * n / (N - 1)
    if ad == "dikdortgen": return np.ones(N)
    if ad == "hann":       return 0.5 - 0.5 * np.cos(a)
    if ad == "hamming":    return 0.54 - 0.46 * np.cos(a)
    if ad == "blackman":
        return 0.42 - 0.5*np.cos(a) + 0.08*np.cos(2*a)

PEN = ["dikdortgen", "hann", "hamming", "blackman"]

# A: yan lob ve ana lob (N=128, fs=1000, 100,5 Hz tek ton)
fs, N = 1000.0, 128
n = np.arange(N)
x0 = np.cos(2 * np.pi * 100.5 * n / fs)
print("A. pencere      yan lob (dB)   ana lob (kutu)")
for ad in PEN:
    S = np.abs(np.fft.rfft(x0 * pencere(ad, N), n=16 * N))
    d = 20 * np.log10(S / S.max())
    tepe = int(np.argmax(d))
    k = tepe
    while d[k + 1] < d[k]:
        k += 1
    print(f"   {ad:<12} {d[k:].max():10.1f}   {2*(k-tepe)/16:12.2f}")

# B: zayif ton sizinti altinda mi? N=256, fs=1024
fs2, N2 = 1024.0, 256
m = np.arange(N2)
guclu = np.cos(2*np.pi*101*m/fs2)
zayif = 0.001 * np.cos(2*np.pi*152*m/fs2)
print("\nB. pencere      sizinti (dB)   sizinti+zayif (dB)")
```

Kodun devamı:

```python
for ad in PEN:
    w = pencere(ad, N2)
    Sg = np.abs(np.fft.rfft(guclu * w))
    Sb = np.abs(np.fft.rfft((guclu + zayif) * w))
    ref = Sg.max()
    print(f"   {ad:<12} {20*np.log10(Sg[38]/ref):10.1f}"
          f"   {20*np.log10(Sb[38]/ref):14.1f}")

# C: iki esit tonun ayrilma esigi (vadi <= -3 dB)
fs3, N3 = 1000.0, 64
t = np.arange(N3) - (N3 - 1) / 2       # pencere merkezine gore zaman
f1 = 300.0
def vadi(w, kutu):
    f2 = f1 + kutu * fs3 / N3
    x = np.exp(2j*np.pi*f1*t/fs3) + np.exp(2j*np.pi*f2*t/fs3)
    S = lambda f: abs(np.sum(w * x * np.exp(-2j*np.pi*f*t/fs3)))
    return 20*np.log10(S((f1+f2)/2) / min(S(f1), S(f2)))
print("\nC. pencere      ayrilma esigi (kutu, vadi <= -3 dB)")
for ad in PEN:
    w = pencere(ad, N3)
    for kutu in np.arange(0.5, 4.0, 0.05):
        if vadi(w, kutu) <= -3:
            print(f"   {ad:<12} {kutu:8.2f}")
            break

# D: sifir doldurma. Tepe okuma hatasi kuculur.
t_ = np.arange(64)
for f0 in (100.0, 104.0):
    x = np.cos(2*np.pi*f0*t_/1000.0)
    print(f"\nD. {f0:.0f} Hz, N=64:", end=" ")
    for pad in (1, 16):
        S = np.abs(np.fft.rfft(x, n=pad*64))
        print(f"pad {pad:2d} -> {np.argmax(S)*1000/(pad*64):7.2f} Hz",
              end="  ")
    print()
```

Program A bölümünde 100,5 Hz'lik ton iki kutu arasında kalır. Pencere uzunluğu `N = 128`, `fs = 1000 Hz`. Ölçülen yan lob ve ana lob değerleri tabloyla uyuşur; özellikle Blackman'ın ana lobunun 6 kutu olması, bu pencerenin dar bir tepe değil geniş bir tepe ürettiğini gösterir.

Program B, zayıf tonu gerçekçi yapar: 101 Hz'lik güçlü ton ile 152 Hz'lik `−60 dB`'lik (genlik 0,001) zayıf ton birlikte. Güçlü tonun yan lobları, zayıf tonun bulunduğu kutuya ne kadar sızıyor? Çıktının ilk sütunu yalnızca sızıntıdır, ikinci sütun sızıntı artı zayıf tondur. İkinci sütun ile birinci sütun arasındaki fark, zayıf tonun katkısıdır. Dikdörtgen pencerede fark yoktur: `−35,2` ile `−35,4` arasında, zayıf ton sızıntı altında kaybolmuştur. Hann ve Blackman'da sızıntı `−60 dB`'nin çok altına iner ve zayıf ton kendini gösterir (`−59,0` ve `−59,5`). Hamming'de sızıntı (`−52,6`) zayıf tonun genliğine çok yakındır; zayıf ton görünür ama kesin ölçülemez.

Program C, iki eşit tonun ayrılma eşiğini bulur. Tonların karmaşık üstel olarak alındığı ve zaman ekseninin pencere merkezine göre kaydırıldığı bir modelde, iki tepe arasındaki vadinin derinliği `−3 dB`'e ulaştığı en küçük aralık ayrılma eşiğidir. Zaman ekseninin merkeze göre alınması şarttır: aksi hâlde iki tonun başlangıç fazları vadiyi aralığa bağlı olarak rastgele yerinden oynatır ve ölçüm anlamını yitirir. Sonuçlar, ana lob genişliğinin yarısına yakındır: dikdörtgen 1,55 kutu, Hamming 2,25, Hann 2,50, Blackman 2,85 kutu.

Program D'de sıfır doldurma (zero padding) gösteriliyor. `N = 64` örnekle 100 Hz'lik tonun tepesi `93,75 Hz` olarak okunuyor; kutu aralığı 15,6 Hz olduğu için en yakın kutu merkezi budur. Aynı diziyi 16 katına (1024 nokta) sıfırla doldurup FFT alınca tepe `99,61 Hz` olur. Yani sıfır doldurma, tepe okuma hatasını küçültür; ama iki tonun ayrılma eşiğini (program C) değiştirmez. Sıfır doldurma, DTFT'yi daha sık örnekler; çözünürlüğü değil ızgarayı artırır. Bunu bir işlem olarak düşün: ara noktaları interpolasyonla doldurmak, yeni bilgi eklemek değildir.

Şekil 52.5 bu dört deneyin sonuçlarını bir arada gösterir: pencere şekilleri, 100,5 Hz tonun spektrumu, iki ton vadisinin aralıkla değişimi ve zayıf tonun sızıntı karşılaştırması.

![Şekil 52.5: (a) Dört pencerenin zaman şekilleri; (b) 100,5 Hz tonun spektrumu (dB); (c) iki eşit tonun vadisi, −3 dB eşiği kesikli; (d) 152 Hz'deki −60 dB zayıf tonun sızıntı ile toplam seviyesi.](gorseller/b52_pencere_sizinti.png)

::: ipucu
Pencere seçimi bir tasarım sorusudur, ezber değildir. Yakın iki güçlü tonu ayırmak istiyorsan dikdörtgen veya Hann; geniş dinamik aralıkta zayıf bir sinyali arıyorsan Blackman. Radar ve sonar tarafında pencere, alıcının dinamik aralığına ve gereken çözünürlüğe göre seçilir.
:::

## 52.7 Güç spektral yoğunluğu (Welch) ve spektrogram

Tek bir periodogram (bir kaydın `|X[k]|²`'si) tutarlı bir tahmin değildir: beyaz gürültüde her kutunun değeri, ortalaması etrafında çok oynar. Standart sapma ortalamaya yakın çıkar. Bunun giderilmesi için Welch yöntemi kullanılır: kayıt üst üste binen parçalara bölünür, her parça pencerelenir, periodogramları ortalanır. Parça sayısı arttıkça tahminin varyansı düşer; bedeli frekans çözünürlüğünün parça uzunluğuyla sınırlanmasıdır. Bu bir takasdır: daha az gürültü, daha kaba frekans ızgarası.

Aşağıdaki program kendi Welch gerçeklememizi yazar (`L = 256`, %50 örtüşme, Hann pencere), sonucu `scipy.signal.welch` ile karşılaştırır, sonra beyaz gürültüde tek periodogram ile Welch'in değişim katsayısını (CV = standart sapma / ortalama) ölçer. Ardından bir chirp (doğrusal artan frekanslı sinyal) için STFT (kısa süreli Fourier dönüşümü) spektrogramı hesaplar; pencere uzunluğunun zaman ve frekans çözünürlüğü üzerindeki etkisini ölçer.

```python
# welch_spektrogram.py - Bolum 52.8: Welch PSD ve STFT spektrogrami
import numpy as np
from scipy import signal

def welch(x, fs, L=256):
    """Hann pencereli, %50 cakisan parcalarin ortalamasi."""
    w = np.hanning(L)
    adim = L // 2
    kare = [x[i:i + L] * w for i in range(0, len(x) - L + 1, adim)]
    P = np.mean([np.abs(np.fft.rfft(s)) ** 2 for s in kare], axis=0)
    P = P / (fs * np.sum(w ** 2))
    P[1:-1] *= 2                       # tek tarafli spektrum
    return np.fft.rfftfreq(L, 1 / fs), P

rng = np.random.default_rng(52)
fs = 1000.0
x = rng.standard_normal(2 ** 16)       # beyaz gurultu, sigma = 1
f, P = welch(x, fs)
_, Ps = signal.welch(x, fs, window=np.hanning(256), nperseg=256,
                     noverlap=128, detrend=False)
print("kendi welch ile scipy: max goreli fark =",
      f"{np.max(np.abs(P - Ps) / Ps):.2e}")

# periodogram ile Welch'in gurultu yayilimi (CV = std / ortalama)
w = np.hanning(256)
pg = np.abs(np.fft.rfft(x[:256] * w)) ** 2 / (fs * np.sum(w ** 2))
cv = lambda v: np.std(v[5:-5]) / np.mean(v[5:-5])
print("tek periodogram CV =", f"{cv(pg):.3f}")
print("Welch CV           =", f"{cv(P):.3f}")
print("beklenen PSD = 2 sigma^2 / fs =", 2 / fs)

# spektrogram: lineer cikirtma (chirp) 50 Hz -> 400 Hz, 2 s
fs2, T = 2000.0, 2.0
t = np.arange(int(fs2 * T)) / fs2
f0, f1 = 50.0, 400.0
faz = 2 * np.pi * (f0 * t + (f1 - f0) * t ** 2 / (2 * T))
```

Kodun devamı:

```python
chirp = np.cos(faz)

def stft(x, N, hop):
    w = np.hanning(N)
    merkez = np.arange(N // 2, len(x) - N // 2, hop)
    S = np.array([np.abs(np.fft.rfft(x[c - N//2:c + N//2] * w))
                  for c in merkez])
    return merkez / fs2, np.fft.rfftfreq(N, 1 / fs2), S

print("\nN    kutu (Hz)  tepe hatasi (Hz)  -3 dB serit (Hz)")
for N in (128, 256, 512):
    tc, fk, S = stft(chirp, N, 64)
    ftrue = f0 + (f1 - f0) * tc / T
    ftep = fk[np.argmax(S, axis=1)]
    esik = S.max(axis=1, keepdims=True) / np.sqrt(2)
    serit = np.mean(np.sum(S >= esik, axis=1)) * fk[1]
    hata = np.mean(np.abs(ftep - ftrue))
    print(f"{N:<5}{fk[1]:8.2f}    {hata:10.2f}"
          f"        {serit:10.1f}")

# spektrogram verisi (sekil icin): 256 ornek, 64 ornek atlama
tc, fk, S = stft(chirp, 256, 64)
dB = 20 * np.log10(S / S.max() + 1e-6)
csv = "engine/veri/b52_spektrogram.csv"
with open(csv, "w", encoding="utf-8") as fh:
    fh.write("t_s,f_hz,db\n")
    for i, tt in enumerate(tc):
        for j, ff in enumerate(fk):
            if ff <= 500:
                fh.write(f"{tt:.4f},{ff:.3f},{dB[i, j]:.2f}\n")
```

```term
$ python welch_spektrogram.py
kendi welch ile scipy: max goreli fark = 1.58e-15
tek periodogram CV = 1.122
Welch CV           = 0.044
beklenen PSD = 2 sigma^2 / fs = 0.002

N    kutu (Hz)  tepe hatasi (Hz)  -3 dB serit (Hz)
128     15.62          3.88              24.1
256      7.81          1.97              12.7
512      3.91          0.98              16.3
```

İlk satır iki gerçeklemenin makine hassasiyetinde aynı olduğunu gösterir (`1,6 · 10⁻¹⁵`). Beyaz gürültüde tek periodogramın CV'si `1,12`'dir (kutu değerleri neredeyse üstel dağılımlı; standart sapma ortalamanın yaklaşık katıdır). Welch'in CV'si ise `0,044`'tür. Beklenen PSD değeri `2σ²/fs = 0,002`'dir; tek taraflı spektrum için yaptığımız normalizasyonla birebir uyuşur.

Spektrogram için aynı chirp (50 Hz'den 400 Hz'ye, 2 saniyede) üç pencere uzunluğunda analiz edildi. Tablo üç niceliği verir: kutu aralığı (`fs/N`), gerçek anlık frekansla tepe frekansı arasındaki ortalama mutlak hata ve −3 dB seviyesinde yayılma (serit) genişliği. Pencere ne kadar kısa olursa zaman çözünürlüğü (`N/fs`) o kadar iyi olur; ama frekans çözünürlüğü (`fs/N`) kaba kalır. Kısa pencere 128 örnekte (64 ms) kutu 15,6 Hz'dir ve tepe hatası 3,9 Hz; uzun pencere 512 örnekte (256 ms) kutu 3,9 Hz'dir ve tepe hatası 1,0 Hz. Ama uzun pencerede her kare 256 ms'lik bir zaman bloğunu özetler: bir hedef 256 ms içinde frekans değiştirirse bu değişim tek bir karede kaybolur.

Şekil 52.6, 256 örnekli pencerenin spektrogramını gösterir. Renk dB olarak ölçeklenmiştir; beyaz kesikli çizgi gerçek anlık frekansı (`50 + 175 t`) gösterir. Ridge (sırt) gerçek frekansı izliyor; sırtın kalınlığı, pencerenin frekans bulanıklığıdır.

![Şekil 52.6: Doğrusal chirp (50–400 Hz, 2 s) spektrogramı, 256 örnek Hann penceresi. Beyaz kesikli çizgi gerçek anlık frekanstır.](gorseller/b52_spektrogram.png)

Ses için bu, bir kaydın konuşmasının tonunu, bir motorun devir değişimini ya da bir radarın darbe içindeki frekans kaymasını (chirp) görmenin yoludur. Mülakatta "STFT'nin pencere boyutunu nasıl seçersin?" sorusunun cevabı yukarıdaki takastır: hedefin değişim hızı ve gereken çözünürlük.

## 52.8 FIR ve IIR filtreler: fark denklemi, frekans yanıtı, kutuplar

Filtre, belirli frekansları geçirip diğerlerini zayıflatan bir LTI sistemdir. İki ana ailesi vardır. Sonlu dürtü yanıtlı (FIR) filtrede çıkış yalnızca girişlere bağlıdır:

y[n] = Σ_{k=0}^{M−1} b_k · x[n−k]

Sonsuz dürtü yanıtlı (IIR) filtrede çıkış ayrıca önceki çıkışlara da bağlıdır: `y[n] = Σ b_k x[n−k] − Σ_{k≥1} a_k y[n−k]`. Geri beslemesi olduğu için IIR'nin dürtü yanıtı genellikle sonsuza kadar sürer ve kararlılığı ayrı bir koşul ister.

Üç filtre örneğiyle başlıyoruz. (1) Hareketli ortalama, `M = 5` katsayısı `1/5`: en basit FIR. (2) Pencereli sinc alçak geçiren, `N = 31`, kesim 100 Hz: kesim frekansının ideal sinc dürtü yanıtını Hamming penceresiyle kesip katsayıları hesaplamak. (3) Üstel düzleştirme (EMA), tek kutuplu IIR: `y[n] = α x[n] + (1 − α) y[n−1]`, `α = 1 − e^(−2π fc/fs)`. Bir de (4) scipy ile tasarlanmış 2. derece Butterworth IIR'si, kesim 100 Hz.

Program hem her filtrenin dürtü yanıtını, hem katsayıları, hem de frekans yanıtını doğrular. Pencereli sinc için `scipy.signal.firwin` ile fark `2,8 · 10⁻¹⁷`'dir; yani hesap doğru. EMA'nın döngüsel gerçeklemesi `lfilter` ile birebir aynıdır. Ayrıca EMA'nın `−3 dB` kesimi 20,02 Hz çıkıyor (istenen 20 Hz).

```python
# filtreler.py - Bolum 52.8: FIR ve IIR filtreler, frekans yaniti
import numpy as np
from scipy import signal

fs = 1000.0

# FIR 1: hareketli ortalama (M = 5), y[n] = (1/M) sum x[n-k]
M = 5
b_ma = np.ones(M) / M
x = np.zeros(12)
x[3] = 1.0                              # birim durtu
y = signal.lfilter(b_ma, [1.0], x)
print("MA5 durtu yaniti:", np.round(y[:8], 3))

# FIR 2: pencereli sinc alcak geciren, N = 31, fc = 100 Hz
def sinc_fir(N, fc_norm):
    n = np.arange(N) - (N - 1) / 2
    h = 2 * fc_norm * np.sinc(2 * fc_norm * n)
    h = h * np.hamming(N)
    return h / np.sum(h)                # DC kazanci = 1

N, fc = 31, 100.0 / fs
h = sinc_fir(N, fc)
print("\nsinc FIR katsayi toplami =", round(h.sum(), 6))
ref = signal.firwin(N, 2 * fc, window="hamming")
print("firwin ile fark (max) =", f"{np.max(np.abs(h - ref)):.2e}")
print("simetri (dogrusal faz):", np.allclose(h, h[::-1]))
print("grup gecikmesi (ornek) =", (N - 1) / 2)

# IIR 1: ustel duzlestirme (EMA), fc = 20 Hz
fc_e = 20.0
alfa = 1 - np.exp(-2 * np.pi * fc_e / fs)
xr = np.random.default_rng(52).standard_normal(500)
y_dongu = np.zeros_like(xr)
onceki = 0.0
```

Kodun devamı:

```python
for i, v in enumerate(xr):
    onceki = alfa * v + (1 - alfa) * onceki
    y_dongu[i] = onceki
y_lf = signal.lfilter([alfa], [1.0, -(1 - alfa)], xr)
print("\nalfa =", round(alfa, 5), " dongu - lfilter (max) =",
      f"{np.max(np.abs(y_dongu - y_lf)):.1e}")
w, H = signal.freqz([alfa], [1.0, -(1 - alfa)], worN=4096, fs=fs)
i3 = np.argmin(np.abs(20 * np.log10(np.abs(H)) + 3))
print("EMA -3 dB frekansi ~", round(w[i3], 2), "Hz (istenen 20 Hz)")
gd = signal.group_delay(([alfa], [1.0, -(1 - alfa)]),
                        w=[0.0001], fs=fs)
print("EMA DC grup gecikmesi ~", round(gd[1][0], 2), "ornek;",
      "teori (1-a)/a =", round((1 - alfa) / alfa, 2))

# IIR 2: Butterworth 2. derece, Wn = 100 Hz / (fs/2)
b_bw, a_bw = signal.butter(2, 100.0 / (fs / 2))
kutup = np.roots(a_bw)
print("\nButterworth b =", np.round(b_bw, 5))
print("Butterworth a =", np.round(a_bw, 5))
print("kutuplar:", np.round(kutup, 4),
      " |kutup| =", np.round(np.abs(kutup), 4))

# frekans yaniti tablosu (sekil icin)
f = np.arange(0, 501, 2.0)
tablo = [f]
for b, a in ((b_ma, [1.0]), (h, [1.0]), ([alfa], [1.0, -(1 - alfa)]),
             (b_bw, a_bw)):
    _, Hf = signal.freqz(b, a, worN=f, fs=fs)
    tablo.append(20 * np.log10(np.maximum(np.abs(Hf), 1e-6)))
np.savetxt("engine/veri/b52_frekans.csv", np.column_stack(tablo),
           delimiter=",",
           header="f_hz,ma5_db,fir31_db,ema20_db,bw2_db",
           comments="", fmt="%.4f")
```

```term
$ python filtreler.py
MA5 durtu yaniti: [0.  0.  0.  0.2 0.2 0.2 0.2 0.2]

sinc FIR katsayi toplami = 1.0
firwin ile fark (max) = 2.78e-17
simetri (dogrusal faz): True
grup gecikmesi (ornek) = 15.0

alfa = 0.11809  dongu - lfilter (max) = 0.0e+00
EMA -3 dB frekansi ~ 20.02 Hz (istenen 20 Hz)
EMA DC grup gecikmesi ~ 7.47 ornek; teori (1-a)/a = 7.47

Butterworth b = [0.06746 0.13491 0.06746]
Butterworth a = [ 1.      -1.14298  0.4128 ]
kutuplar: [0.5715+0.2936j 0.5715-0.2936j]  |kutup| = [0.6425 0.6425]
```

Yorumlar: Hareketli ortalamanın dürtü yanıtı 5 örnek boyunca `0,2` değerindedir; doğrusal fazlıdır ve grup gecikmesi `(M−1)/2 = 2` örnektir. Pencereli sinc'in simetri testi `True` döner, yani katsayılar simetriktir; bu doğrusal faz garantisidir ve grup gecikmesi `(N−1)/2 = 15` örnektir. EMA'nın grup gecikmesi ise DC'de `(1−α)/α = 7,47` örnektir. Butterworth'ta iki kutup `0,5715 ± 0,2936j` ve `|kutup| = 0,6425`'tir; birim çemberin içindedir, yani kararlıdır.

FIR ile IIR arasındaki karar, aşağıdaki kısa tabloda özetlenmiştir:

| Özellik | FIR | IIR |
|---|---|---|
| Doğrusal faz | Simetrik katsayılarla kolay | Zor; genelde doğrusal faz yoktur |
| Aynı keskinlik için katsayı | Çok (30–100+) | Az (2–6) |
| Kararlılık | Her zaman kararlı (sonlu) | Kutuplara bağlı; dikkat ister |
| Gerçekleme maliyeti | Çok çarpma, geri besleme yok | Az çarpma, ama geri besleme ve sayısal kararlılık |
| Tipik kullanım | Ses, haberleşme, faz duyarlı işler | Hızlı düzleştirme, gömülü sensör filtreleri |

Frekans yanıtı, bir filtrenin her frekanstaki kazancını (`|H(f)|`) ve faz kaymasını gösterir. Şekil 52.7, dört filtrenin genlik yanıtını dB olarak çizer. Hareketli ortalama yavaş düşen bir yanıt verir ve ilk sıfırını `fs/M = 200 Hz`'de yapar; sinc FIR dik bir geçiş bandı üretir; EMA ve Butterworth ise `−3 dB` çizgisini (kesikli) kesim frekansında geçer. EMA'nın yanıtı Butterworth'a göre çok daha yumuşaktır; bu yüzden düzleştirme için iyi, keskin ayırma için kötü bir seçimdir.

![Şekil 52.7: Dört alçak geçiren filtrenin genlik yanıtı (dB). Kesikli çizgi −3 dB'dir.](gorseller/b52_filtre_frekans.png)

Kutup-sıfır grafiği, bir IIR'nin kararlılığını görmenin en doğrudan yoludur. z-dönüşümünde (bu bölümde yalnızca sezgi düzeyinde) bir IIR'nin paydasının kökleri kutuplardır; kutup birim çemberin içindeyse kararlı, dışındaysa kararsızdır. Kutup ne kadar çembere yakınsa, filtre o kadar uzun süre "çınlar" ve dar bir tepe üretir. EMA'nın kutbu `z = 1 − α = 0,882`'dir; Butterworth'un kutupları çemberin içinde ama iki kutupla daha keskin bir yanıt verir. Şekil 52.8 bu iki filtrenin kutup-sıfır konumlarını gösterir.

![Şekil 52.8: Kutup (×) ve sıfır (○) konumları. Solda EMA'nın tek kutbu, sağda Butterworth'un iki karmaşık kutbu ve çift sıfırı (−1).](gorseller/b52_kutup_sifir.png)

Doğrusal faz neden önemli? Bir radar veya ses sisteminde frekanslar farklı gecikmelerle geçerse, bir darbe biçimi bozulur. Simetrik FIR bütün frekanslara aynı gecikmeyi uygular (grup gecikmesi sabit); bu yüzden darbe şekli korunur. IIR filtrelerde gecikme frekansa göre değişir; bu bazen istenmez ama bazen sorun olmaz (ör. bir düzleştirme için).

## 52.9 Gömülü gerçekleme: Q15 FIR, dairesel tampon ve Cortex-M4

Filtreyi C'de gerçeklerken üç soru vardır: sayılar nasıl temsil edilir (kayan nokta mı, sabit nokta mı), geçmiş örnekler nasıl saklanır (dairesel tampon) ve işlem süresi bütçeye sığıyor mu. Bölüm 46'da sabit nokta Q15 formatını, doygunluğu ve yuvarlamayı gördün. Burada aynı formatta bir FIR yazacağız.

Önce katsayılar. 5 katsayılı bir alçak geçiren FIR, `scipy.signal.firwin` ile hamming penceresi ve kesim `0,4 · Nyquist` için tasarlanır. Katsayılar Q15'e `round(b · 2¹⁵)` ile çevrilir.

```python
# katsayi_q15.py - 5 tap alcak geciren FIR katsayilari, Q15'e cevrim
import numpy as np
from scipy import signal

# hamming penceresi, DC kazanci 1
b = signal.firwin(5, 0.4)
q = np.round(b * 2**15).astype(int)
print("float b :", np.round(b, 6))
print("Q15 q   :", q.tolist())
print("sum b   =", round(b.sum(), 6), "  sum q =", q.sum())
print("sum|b|  =", round(np.abs(b).sum(), 6))
print("kuantizasyon hatasi (max) =",
      f"{np.max(np.abs(q / 2**15 - b)):.2e}")
```

```term
$ python katsayi_q15.py
float b : [0.010087 0.220341 0.539144 0.220341 0.010087]
Q15 q   : [331, 7220, 17667, 7220, 331]
sum b   = 1.0   sum q = 32769
sum|b|  = 1.0
kuantizasyon hatasi (max) = 1.41e-05
```

Çıktı önemli bir ayrıntı içeriyor: Q15 katsayıların toplamı `32769`'dur, yani tam bir birim kazanç (`32768`) değil, bir LSB fazlasıdır. Bu, tam ölçekli bir DC girişin çıkışında `32768` gibi bir değer üretebileceği anlamına gelir; sonuç doygunlukla `32767`'ye çekilir. Q15 katsayılarının toplamını ve `Σ|b|` değerini mutlaka kontrol et: `Σ|b| ≥ 2` olduğunda 32-bit birikim taşabilir ve bu durumda 64-bit birikim gerekir.

Kod üç dosyaya bölündü: `q15_fir.h` arayüz, `q15_fir.c` kütüphane (yalnızca `stdint.h` kullanır, dolayısıyla gömülüye taşınabilir), `q15_test.c` host testi (`stdio` ve `math` kullanır, gömülüye girmez). Dairesel tampon, en yeni örneği bir geri indisle yazar; döngü `(bas + k) mod TAP` yerine bir koşullu dal ile sarar. Bu ayrıntı bir sonraki paragrafta açıklanmıştır.

```c
/* q15_fir.h - 5 tap Q15 FIR, dairesel tampon ile */
#ifndef Q15_FIR_H
#define Q15_FIR_H
#include <stdint.h>

#define TAP 5

typedef struct {
    int16_t gecmis[TAP];   /* dairesel tampon: son TAP ornek */
    uint8_t bas;           /* en yeni ornegin indeksi */
} Fir;

void fir_sifirla(Fir *f);
int16_t fir_adim(Fir *f, int16_t x);

#endif
```

```c
/* q15_fir.c - Q15 FIR cekirdegi (libc gerektirmez) */
#include "q15_fir.h"

/* Q15 katsayilari: round(b * 2^15), katsayi_q15.py ile uretildi */
static const int16_t B[TAP] = {331, 7220, 17667, 7220, 331};

void fir_sifirla(Fir *f)
{
    for (int i = 0; i < TAP; i++)
        f->gecmis[i] = 0;
    f->bas = 0;
}

int16_t fir_adim(Fir *f, int16_t x)
{
    /* yeni ornek: baslangic indeksini bir geri al (sarmali), yaz */
    f->bas = (f->bas == 0) ? (uint8_t)(TAP - 1)
                           : (uint8_t)(f->bas - 1);
    f->gecmis[f->bas] = x;

    /* y = sum B[k] * x[n-k]; x[n-k] konumu (bas + k) mod TAP */
    int64_t acc = 0;
    uint8_t i = f->bas;
    for (int k = 0; k < TAP; k++) {
        acc += (int64_t)B[k] * f->gecmis[i];   /* Q30 birikim */
        i = (uint8_t)(i + 1);
        if (i == TAP) i = 0;                   /* mod yerine dal */
    }
    /* Q30 -> Q15: 15 bit saga kaydir, yuvarla, doyur */
    int64_t y = (acc + (1 << 14)) >> 15;
    if (y > 32767) return 32767;
    if (y < -32768) return -32768;
    return (int16_t)y;
}
```

Dairesel tampon fikri Bölüm 7.7'deki tampondur: sabit boyutlu bir dizi, iki indeks ve sarma. Burada tampon yalnızca `TAP` = 5 örneği tutar; yeni örnek geldiğinde `bas` bir geri gider ve yeni örnek o konuma yazılır. Eski örnek kendiliğinden üzerine yazılır. Böylece veri taşıma (`memmove`) yapılmaz; her çıkış için yalnızca `TAP` çarpma-toplama yapılır.

Bir ayrıntı üzerinde durmaya değer. İlk sürümde sarma `(bas + k) % TAP` ile yapılmıştı. Cortex-M4'te `TAP` bir kuvvet değilse derleyici bu modülü bir `udiv` (tamsayı bölme) komutuna çevirir. ARMv7-M'de `udiv`'in süresi girdiye bağlı yaklaşık 2–12 çevrimdir (genel bilgi; kesin değer için işlemci kılavuzuna bak). Döngünün her adımında bir bölme, kaçınılabilir bir maliyettir. Bu yüzden sarma koşullu dalla yapıldı; derlenmiş `fir_adim` içinde artık `udiv` yok.

Birikim `int64_t`'dir. Gerekçe: iki 16-bit sayının çarpımı 32-bit'e sığar (en kötü `(−32768)² = 2³⁰`), ama beş çarpımın toplamı 32-bit'i taşabilir; işaretli taşma C'de tanımsız davranıştır (UB), bu yüzden 64-bit kullanıyoruz. Q30'dan Q15'e geçiş 15 bit sağa kaydırmaktır; C standardı negatif işaretli sayının sağa kaydırmasını uygulama tanımlı bırakır, ama gcc ve ARM derleyicileri aritmetik kaydırma yapar. Yuvarlama için `2¹⁴` eklenir ve son olarak doygunluk uygulanır.

Host testi, aynı kodu bir float referansla karşılaştırır: iki referans vardır, biri Q15 katsayılarıyla (yalnızca birikim hatası), diğeri kesin katsayılarla (katsayı kuantizasyonu dahil). Girdi, sabit tohumlu (`s = 52`) bir LCG ile üretilir; böylece her derlemede aynı sayılar çıkar.

```c
/* q15_test.c - host testi: Q15 cekirdegi ve float referans */
#include <stdio.h>
#include <stdint.h>
#include <math.h>
#include "q15_fir.h"

static const float BF[TAP] = {0.010087f, 0.220341f, 0.539144f,
                              0.220341f, 0.010087f};
static const float BQ[TAP] = {331/32768.f, 7220/32768.f,
                              17667/32768.f,
                              7220/32768.f, 331/32768.f};

int main(void)
{
    enum { N = 2000 };
    static int16_t x[N];
    static int16_t y[N];
    uint32_t s = 52;                    /* sabit tohum (LCG) */
    for (int n = 0; n < N; n++) {
        s = s * 1664525u + 1013904223u;
        x[n] = (int16_t)((int32_t)(s >> 16) - 32768);
    }

    Fir f;
    fir_sifirla(&f);
    for (int n = 0; n < N; n++)
        y[n] = fir_adim(&f, x[n]);
```

Kodun devamı:

```c
    double e_q = 0.0, e_f = 0.0;
    for (int n = TAP - 1; n < N; n++) {
        float r_q = 0.f, r_f = 0.f;
        for (int k = 0; k < TAP; k++) {
            r_q += BQ[k] * x[n - k];    /* Q15 katsayili referans */
            r_f += BF[k] * x[n - k];    /* kesin katsayili referans */
        }
        double dq = fabs(y[n] - r_q), df = fabs(y[n] - r_f);
        if (dq > e_q) e_q = dq;
        if (df > e_f) e_f = df;
    }
    printf("ilk 6 cikti: ");
    for (int n = 0; n < 6; n++) printf("%d ", y[n]);
    printf("\nmax |Q15 - (Q15 katsayi float)| = %.2f LSB\n", e_q);
    printf("max |Q15 - (kesin float)|       = %.2f LSB\n", e_f);

    /* sinir: tam olcekli DC giris */
    fir_sifirla(&f);
    int16_t son = 0;
    for (int n = 0; n < 10; n++)
        son = fir_adim(&f, 32767);
    printf("DC 32767 girisi, cikis = %d\n", son);
    return 0;
}
```

```term
$ gcc -O2 -Wall -Wextra -std=c11 q15_fir.c q15_test.c -lm -o q15_test
$ ./q15_test
ilk 6 cikti: -161 -3193 -1514 12944 5350 -4125
max |Q15 - (Q15 katsayi float)| = 0.50 LSB
max |Q15 - (kesin float)|       = 1.60 LSB
DC 32767 girisi, cikis = 32767
```

Sonuç: Q15 çıkışı, Q15 katsayılı referanstan en çok `0,50 LSB` sapıyor (yalnızca yuvarlama), kesin float referanstan `1,60 LSB` (katsayı kuantizasyonunun etkisi dahil). Tam ölçekli DC girişte çıkış `32767`'ye doyuyor. Aynı kod `gcc -fsanitize=address,undefined` ile (WSL2 içinde Linux gcc'si) derlendiğinde hata ya da uyarı üretmiyor. Not: ASan ve UBSan Windows'ta doğrudan gcc ile değil, WSL2 içinde çalışır.

**Cortex-M4 derlemesi.** Kütüphane kodu Windows'ta kurulu ARM araç zinciriyle derlendi (`arm-none-eabi-gcc` 13.3.1, STM32CubeIDE ile gelen sürüm). Bayraklar: `-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16`, boyut için `-Os`, karşılaştırma için `-O2`. Aşağıdaki komut boyutu verir; `fir_adim` için komut sayımı `arm-none-eabi-objdump -d` çıktısında bu fonksiyonun satır sayısıdır.

::: not
Bu kod hedef karta yüklenip çalıştırılmadı; yalnızca derlendi ve dosyanın metin (kod) boyutu ile iç döngü komutları sayıldı. Kart üzerinde süre ölçümü ayrı bir adımdır.
:::

```term
$ arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=hard \
    -mfpu=fpv4-sp-d16 -Os -c q15_fir.c -o q15_fir.o
$ arm-none-eabi-size -A q15_fir.o
section           size   addr
.text              136      0
.data                0      0
.bss                 0      0
.rodata             10      0
.comment            68      0
.ARM.attributes     52      0
Total              266
```

Ölçüm: `fir_adim` (`-Os`) 44 komut ve `udiv` yok; `smlal` (64-bit birikim çarpım-toplamı) bir kez görünüyor. Derlenmiş `.text` boyutu 136 bayt. Döngünün beş tekrarı 16 kHz'de bir kanal için bütçeye şöyle yerleşir: her örnek 5 MAC gerektirir, saniyede `5 × 16000 = 80 000` MAC. Cortex-M4 168 MHz'de çalışıyorsa her örnek için `168·10⁶ / 16000 = 10 500` çevrim vardır. Yaklaşık 50 komutluk bir fonksiyon bu bütçenin küçük bir bölümünü kullanır; asıl sınır, ADC kesmesinin ve diğer görevlerin payıdır (Bölüm 44'teki kesme gecikmesi ve jitter).

Bu bütçe hesabı bir kural olarak kullanılır: `ops_per_sample × fs` ile işlemci MIPS/MAC kapasitesini karşılaştır, sonra kesmeler ve diğer görevler için pay bırak. Daha büyük FIR'lerde (ör. 64 katsayılı bir ses filtresi) toplam MAC `64 × fs` olur ve SIMD'li çekirdek (ör. CMSIS-DSP) gerekebilir; bunu Kod Okuma'da göreceğiz.

## 52.10 Uygulamalar: IMU tümleyen filtre, EV akımı, eşleşik filtre ve Doppler

**IMU: eğim kestirimi ve tümleyen filtre.** Bir İHA'nın eğim açısını iki sensörle ölçersin. İvmeölçer, yerçekiminin yönünden açı verir; ama titreşimde ve hızlanmada bu açı bozulur. Jiroskop açısal hızı verir; integrali açıyı verir, ama sapma (bias) zamanla birikerek sürüklenir. Tümleyen filtre (complementary filter) iki kaynağı birleştirir: jiroskop kısa vadede, ivmeölçer uzun vadede güvenilirdir.

Program sentetiktir (açıkça etiketli): gerçek eğim `10° · sin(2π · 0,1 t)`, 200 Hz örnekleme, 60 saniye. İvmeölçer, 40 Hz'lik 2° genlikli titreşim ve 1° standart sapmalı gürültü taşır. Jiroskop, 0,05°/s sapma ve 0,5°/s gürültü taşır. Tümleyen filtre `θ̂[n] = α(θ̂[n−1] + ω[n] dt) + (1−α) θ_a[n]`, `α = 0,98`'dir. İvmeölçere ayrıca 5 Hz'lik bir EMA uygulanır (karşılaştırma için).

```python
# imu_tumleyen.py - Bolum 52.10: IMU egim kestirimi (SENTETIK veri)
import numpy as np

fs, T = 200.0, 60.0
dt = 1.0 / fs
t = np.arange(0, T, dt)
rng = np.random.default_rng(52)

# gercek egim: 10 derece genlikli, 0,1 Hz'lik yavas hareket
theta = 10.0 * np.sin(2 * np.pi * 0.1 * t)
# jiroskop: turev + 0,05 deg/s sapma + gurultu
omega = np.gradient(theta, dt) + 0.05 + rng.normal(0, 0.5, t.size)
# ivmeolcer: gercek egim + 40 Hz titresim + beyaz gurultu
titresim = 2.0 * np.sin(2 * np.pi * 40 * t)
theta_a = theta + titresim + rng.normal(0, 1.0, t.size)

# 1) ivmeolcer, alcak geciren (ustel duzlestirme, fc = 5 Hz)
a = 1 - np.exp(-2 * np.pi * 5.0 / fs)
ema = np.zeros_like(theta_a)
y = theta_a[0]
for i, v in enumerate(theta_a):
    y = a * v + (1 - a) * y
    ema[i] = y

# 2) jiroskop integrali: sapma zamanla birikir
gyro = np.zeros_like(t)
g = 0.0
for i, w in enumerate(omega):
    g += w * dt
    gyro[i] = g

# 3) tumleyen filtre: jiroskop kisa vadede, ivmeolcer uzun vadede
alfa = 0.98
comp = np.zeros_like(t)
c = 0.0
```

Kodun devamı:

```python
for i in range(t.size):
    c = alfa * (c + omega[i] * dt) + (1 - alfa) * theta_a[i]
    comp[i] = c

def rmse(tahmin):
    k = int(2 * fs)                     # ilk 2 saniye isinma
    return np.sqrt(np.mean((tahmin[k:] - theta[k:]) ** 2))

print("yontem                    RMS hata (derece)")
print(f"ivmeolcer ham             {rmse(theta_a):8.3f}")
print(f"ivmeolcer EMA (5 Hz)      {rmse(ema):8.3f}")
print(f"jiroskop integrali        {rmse(gyro):8.3f}")
print(f"tumleyen (alfa=0,98)      {rmse(comp):8.3f}")

np.savetxt("engine/veri/b52_imu.csv",
           np.column_stack([t, theta, theta_a, ema, gyro, comp]),
           delimiter=",",
           header="t_s,gercek,ivme_ham,ivme_ema,jiro,tumleyen",
           comments="", fmt="%.5f")
```

```term
$ python imu_tumleyen.py
yontem                    RMS hata (derece)
ivmeolcer ham                1.727
ivmeolcer EMA (5 Hz)         0.359
jiroskop integrali           1.791
tumleyen (alfa=0,98)         0.105
```

Ölçülen RMS hatalar: ham ivmeölçer `1,73°`, EMA ile düzleştirilmiş ivmeölçer `0,36°`, jiroskop integrali `1,79°` (sapma birikimi), tümleyen filtre `0,11°`. Tümleyen filtre her iki kaynağın zayıf yanını sıfırlar: 40 Hz titreşim ve gürültü ivmeölçer tarafında kalır; tümleyen filtrenin ivmeölçer üzerindeki etkili kesimi `τ = α dt/(1−α) = 0,245 s` ile yaklaşık 0,65 Hz'dir. Jiroskop sapması ise ivmeölçer tarafından sürekli düzeltilir.

Şekil 52.9 solda ilk 20 saniyede gerçek eğimi, ham ivmeölçeri ve tümleyen filtreyi; sağda iki yöntemin hatasını gösterir. Jiroskop hatası zamanla kayar, tümleyen filtrenin hatası ise sınırlı kalır.

![Şekil 52.9: Sol: gerçek eğim, ham ivmeölçer ve tümleyen filtre (ilk 20 s). Sağ: jiroskop integralinin ve tümleyen filtrenin hatası; jiroskop sürüklenirken tümleyen filtre sınırlı kalır.](gorseller/b52_imu_tumleyen.png)

Tümleyen filtre, Kalman filtresinin sezgisel öncülüdür. Kalman filtresi aynı iki kaynağı, gürültülerin istatistiğine göre (kovaryans) optimal ağırlıklarla birleştirir. Bölüm 62'de olasılıksal modeller ve Kalman filtresi, bu bölümdeki sezgiyi matematiksel olarak tamamlayacak.

**EV batarya akımı: gürültü düzleştirme.** Bir EV'nin akım ölçümü anahtarlama gürültüsü ve sensör gürültüsü taşır. Sentetik bir program 20 A'den 80 A'e basamak, 4 A standart sapmalı gürültü ve 50 Hz'lik 3 A parazit üretir. 100 ms'lik sonlu hareketli ortalama ile 5 Hz'lik EMA karşılaştırılır. Ölçülen standart sapma `4,53 A`'den `0,40 A` (MA100) ve `0,55 A` (EMA5) değerine düşer; basamağın %90'ına ulaşma gecikmesi MA100 için 89 ms, EMA5 için 67 ms'dir. Bu bir takastır: hareketli ortalama daha iyi düzleştirir ama daha yavaş tepki verir. Tasarımda hangi gecikme kabul edilebilir sorusu, filtreyi seçer.

Program, 52.10'un akım örneğini şöyle üretir ve ölçer:

```python
# ev_akim.py - Bolum 52.10: EV batarya akimi, gurultu duzlestirme
# (SENTETIK veri: 20 A'den 80 A'e basamak, 4 A gurultu, 50 Hz parazit)
import numpy as np

fs, T = 1000.0, 10.0
t = np.arange(0, T, 1 / fs)
rng = np.random.default_rng(52)
akim = np.where(t < 5.0, 20.0, 80.0)
ham = akim + rng.normal(0, 4.0, t.size) + 3.0 * np.sin(2*np.pi*50*t)

# 100 ms hareketli ortalama (sonlu, nedensel)
M = 100
ma = np.full(t.size, np.nan)
for i in range(M - 1, t.size):
    ma[i] = np.mean(ham[i - M + 1:i + 1])

# 5 Hz ustel duzlestirme
a = 1 - np.exp(-2 * np.pi * 5.0 / fs)
ema = np.zeros_like(ham)
y = ham[0]
for i, v in enumerate(ham):
    y = a * v + (1 - a) * y
    ema[i] = y

kararli = (t > 1) & (t < 4.9)
print("std (1-4,9 s, kararli bolge):")
print(f"  ham   = {np.std(ham[kararli]):6.3f} A")
print(f"  MA100 = {np.std(ma[kararli]):6.3f} A")
print(f"  EMA5  = {np.std(ema[kararli]):6.3f} A")
hedef = 20 + 0.9 * 60                   # basamagin %90'i
for ad, s in (("MA100", ma), ("EMA5", ema)):
    k = np.argmax((t >= 5.0) & (s >= hedef))
    print(f"  {ad}: %90 gecikme = {(t[k] - 5.0) * 1000:6.1f} ms")
```

```term
$ python ev_akim.py
std (1-4,9 s, kararli bolge):
  ham   =  4.534 A
  MA100 =  0.400 A
  EMA5  =  0.553 A
  MA100: %90 gecikme =   89.0 ms
  EMA5: %90 gecikme =   67.0 ms
```

**Radar ve sonar: eşleşik filtre (matched filter).** Bilinen bir darbe şekli `s[n]` (burada 2 ms, 2 kHz'den 6 kHz'e doğrusal bir cıvıltı) gürültülü bir alıcıda aranır. En iyi doğrusal dedektör, darbenin zaman-tersi kopyası ile konvolüsyondur: `h[n] = s[L−1−n]`. Bu, çıkışın darbe tamamen göründüğünde tepe yapmasını sağlar; Bölüm 52.4'teki konvolüsyonun tam uygulamasıdır. Gürültüde maksimum SNR'yi verir (sinyal enerjisine bağlı bir kazanç; `Σs² = L/2 = 50`).

Program, 200 deneme (sabit tohum 52) ile farklı SNR değerlerinde gecikmeyi tahmin eder ve eşleşik filtreyi ham genlik araması ile karşılaştırır. Ayrıca radar ve sonar için Doppler kaymasını hesaplar: `f_d = 2 v f₀ / c`. Radarda 10 GHz ve 30 m/s için `2000 Hz`; sonarda 40 kHz, 10 m/s ve suda `c = 1500 m/s` için `533 Hz`.

```python
# eslesik.py - Bolum 52.10: eslesik filtre ile darbe tespiti
# (SENTETIK veri) ve Doppler hesabi
import numpy as np

fs = 50_000.0                           # 50 kHz
Tp = 0.002                              # 2 ms darbe
t = np.arange(int(Tp * fs)) / fs
L = t.size                              # 100 ornek
k = (6000 - 2000) / (2 * Tp)            # 2 kHz -> 6 kHz cikirtma
sablon = np.cos(2*np.pi*(2000*t + k*t**2))
eslesik = sablon[::-1]                  # h[n] = s[L-1-n]

def sigma2_snr(snr_db):
    """SNR = 0,5 / sigma^2 (cos sinyalinin ortalama gucu 0,5)."""
    return 0.5 / 10 ** (snr_db / 10)

def tespit(snr_db, deneme=200, seed=52):
    """Gecikme tahmini: eslesik filtre ve ham genlik."""
    rng = np.random.default_rng(seed)
    basari_m = basari_h = 0
    for _ in range(deneme):
        d = int(rng.integers(300, 1200))
        r = np.zeros(2000)
        r[d:d + L] += sablon
        r += rng.normal(0, np.sqrt(sigma2_snr(snr_db)), r.size)
        c = np.convolve(r, eslesik)
        tahmin_m = int(np.argmax(c)) - (L - 1)
        tahmin_h = int(np.argmax(np.abs(r)))
        basari_m += abs(tahmin_m - d) <= 1
        basari_h += abs(tahmin_h - d) <= 1
    return basari_m / deneme, basari_h / deneme

print(f"sablon enerjisi = {np.sum(sablon**2):.2f}  (L/2 = {L/2})")
print("SNR (dB)   eslesik dogru   ham genlik dogru")
```

Kodun devamı:

```python
for snr in (-15, -10, -5, 0):
    pm, ph = tespit(snr)
    print(f"{snr:8d}   {pm:12.3f}   {ph:16.3f}")

# Doppler: f_d = 2 v f0 / c (yaklasan hedef icin pozitif)
c_isik, c_ses = 3.0e8, 1500.0
print("\nRadar (10 GHz, 30 m/s):  f_d =",
      round(2 * 30 * 10e9 / c_isik, 1), "Hz")
print("Sonar (40 kHz, 10 m/s):  f_d =",
      round(2 * 10 * 40e3 / c_ses, 1), "Hz")

# sekil verisi: SNR = -5 dB, darbe 700. ornekte
rng = np.random.default_rng(52)
r = np.zeros(2000)
r[700:700 + L] += sablon
r += rng.normal(0, np.sqrt(sigma2_snr(-5)), r.size)
c = np.convolve(r, eslesik)
np.savetxt("engine/veri/b52_eslesik.csv",
           np.column_stack([np.arange(r.size) / fs, r,
                            c[:r.size] / np.max(np.abs(c))]),
           delimiter=",", header="t_s,alici,eslesik_cikis",
           comments="", fmt="%.6f")
```

```term
$ python eslesik.py
sablon enerjisi = 50.04  (L/2 = 50.0)
SNR (dB)   eslesik dogru   ham genlik dogru
     -15          0.075              0.005
     -10          0.480              0.005
      -5          0.990              0.015
       0          1.000              0.025

Radar (10 GHz, 30 m/s):  f_d = 2000.0 Hz
Sonar (40 kHz, 10 m/s):  f_d = 533.3 Hz
```

Sonuç açık: `−5 dB`'de eşleşik filtre %99 doğru, ham genlik %1,5 doğru; `−10 dB`'de sırasıyla %48 ve %0,5. Ham genlik araması, gürültünün tepe değerinin darbenin genliğini geçtiği her durumda yanlış çalışır. Eşleşik filtrenin kazancı, 100 örnek boyunca darbe enerjisinin toplanmasından gelir.

Şekil 52.10, `−5 dB` SNR'de bir darbenin alıcıda hiç görünmediğini (üst panel) ama eşleşik çıkışta tek bir keskin tepe ürettiğini (alt panel, kesikli çizgi) gösterir. Tepe, darbenin bittiği ana (`700 + 100 − 1 = 799`. örnek, 16 ms) denk gelir.

![Şekil 52.10: Üst: −5 dB SNR'li alıcı sinyali; darbe görünmez. Alt: eşleşik filtre çıkışı; tepe, darbe bittiğinde (16 ms) oluşur.](gorseller/b52_eslesik_filtre.png)

Ses için tek bir not: bir mikrofon kaydının örnekleme hızı genelde 16 kHz ya da 48 kHz'dir; üst frekans sınırı `fs/2`'dir. Bir konuşmanın frekans içeriği 4 kHz civarında yoğundur, dolayısıyla 8 kHz'lik bir örnekleme telefon kalitesine yeterlidir. Spektrogramda (52.7) bu frekans sınırı, yukarıdaki yatay çizgi olarak görünür.

## Çözümlü Örnekler

Bu bölümde dört örnek var; zorluk sırası ★, ★★, ★★, ★★★. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntüyü bul, iyileştir ve doğrula. Doğrulama adımında elle iz tablosu vardır. Her örneğin sonunda bir varyasyon sorusu var; bunu yapay zekâ olmadan çözmeye çalış.

### Örnek 1 (★): Örtüşen frekansın bulunması

`fs = 8 kHz` ile örneklenen bir sinyalde `5,5 kHz`'lik bir bileşen var. Örneklerde hangi frekans olarak görünür, ve bu iki sinyalin örnekleri arasındaki ilişki nedir?

**Adım 1 — Anla.** İstenen: örtüşen frekans `f_a`. Ayrıca neden bu frekans olduğunu, yani örnek dizilerinin ilişkisini göstermek.

**Adım 2 — Örnekle.** `5,5 kHz` sinyalin bir periyodu `1/5500 s`'dir; `fs = 8 kHz` ile bir periyot yaklaşık `1,45` örneğe denk gelir. Yani örnekler, bir periyodu tam olarak doldurmaz ve faz her seferinde kayar; bu kaymanın yönünü görmek için birkaç örneğe bakmalıyız.

**Adım 3 — Kaba çöz.** `|f − k·fs|` değerlerine bak: `k = 1` için `|5500 − 8000| = 2500 Hz`. `2500 Hz`, Nyquist'in (`4000 Hz`) içinde olduğu için bu katlamanın sonucudur.

**Adım 4 — Örüntü.** Her örnekte `2π · 5500 · n/8000 = 2π · n − 2π · 2500 · n/8000`. Yani `x(5,5k)[n] = −x(2,5k)[n]`: işaret ters çevrilmiş bir 2,5 kHz sinüs.

**Adım 5 — İyileştir.** Doğrulama için bir kontrol gerekir: `x(5,5k) + x(2,5k)` her `n` için sıfır mı? Bu kontrol makine hassasiyetinde yapılabilir ve bu, eşitliği tek tek örneklerle onaylar.

**Adım 6 — Doğrula.** İz tablosu (`n` ile `t = n/fs`):

| n | t (ms) | sin(2π·5500·n/8000) | sin(2π·2500·n/8000) | toplam |
|---|---|---|---|---|
| 0 | 0,000 | 0,0000 | 0,0000 | 0 |
| 1 | 0,125 | −0,9239 | +0,9239 | 0 |
| 2 | 0,250 | +0,7071 | −0,7071 | 0 |
| 3 | 0,375 | +0,3827 | −0,3827 | 0 |
| 4 | 0,500 | −1,0000 | +1,0000 | 0 |

Tablo, 52.2'deki eşitliği sayılarla onaylar. Bu değerler `sin` fonksiyonunun standart değerleridir (`sin(0,6875·2π)` vb.), elle de hesaplanabilir.

**Bunu AI'sız yazabilir misin?** `fs = 6 kHz` ile örneklenen `4,5 kHz`'lik bir sinyalin örtüşen frekansını bul ve `n = 0..3` için örneklerin işaretinin nasıl değiştiğini tablo yap. Bu durumda tek bir katlama mı yeter, yoksa `k = 1` yerine başka bir `k` mı gerekir?

### Örnek 2 (★★): İki dizinin konvolüsyonu

`x = [1, 2, 3, 4]` ve `h = [1, −1, 2]` dizilerinin konvolüsyonunu elle hesapla. Sonucun uzunluğunu ve her terimin hangi çarpımlardan geldiğini göster.

**Adım 1 — Anla.** İstenen `y = x * h`, uzunluk `4 + 3 − 1 = 6`.

**Adım 2 — Örnekle.** `y[2]`'yi ele alalım: `y[2] = x[0]h[2] + x[1]h[1] + x[2]h[0] = 1·2 + 2·(−1) + 3·1`. Bu üç terim, `h`'nin ters çevrilip `n = 2` konumuna kaydırılmasıyla görünür (Şekil 52.3).

**Adım 3 — Kaba çöz.** Her `n` için yalnızca üst üste binen terimleri topla: `y[n] = Σ_k x[k] h[n−k]`, `0 ≤ k ≤ 3`, `0 ≤ n−k ≤ 2`.

**Adım 4 — Örüntü.** `y[0]` tek terimdir; `y[5]` de tek terimdir (`x[3]·h[2]`). Ortadaki değerler üç terim ile hesaplanır. Yani sonuç hem başta hem sonda "yumuşar".

**Adım 5 — İyileştir.** Terim sayısını azaltmak için her `n`'de yalnızca geçerli `k` aralığını hesapla; yazması kolay olan bir kısayol. `y[n] = Σ` ifadesinde `k` aralığını `max(0, n−2) ≤ k ≤ min(3, n)` olarak sınırlamak yeterlidir.

**Adım 6 — Doğrula.** İz tablosu (`n`, terimler, toplam):

| n | Terimler (x[k]·h[n−k]) | Toplam |
|---|---|---|
| 0 | 1·1 | 1 |
| 1 | 1·(−1) + 2·1 | 1 |
| 2 | 1·2 + 2·(−1) + 3·1 | 3 |
| 3 | 2·2 + 3·(−1) + 4·1 | 5 |
| 4 | 3·2 + 4·(−1) | 2 |
| 5 | 4·2 | 8 |

Sonuç `y = [1, 1, 3, 5, 2, 8]`. Bu sonucu doğrulayan betik, Örnek 3'ün sonunda iki örnekle birlikte verilmiştir.

**Bunu AI'sız yazabilir misin?** `x = [2, 0, −1]` ve `h = [3, 1]` için konvolüsyonu elle yap. Sonucun son elemanını ve uzunluğunu önceden tahmin et; sonra tabloyla doğrula.

### Örnek 3 (★★): 8 noktalı DFT, bir tepenin iki kutuya dağılması

`x[n] = cos(2π · 2,5 · n / 8)`, `n = 0..7`, sinyalinin 8 noktalı DFT'sini düşün. Tepe frekansı `2,5` kutu olduğu için tam bir kutuya oturmaz. Hangi kutularda enerji vardır ve büyüklükler ne kadardır?

**Adım 1 — Anla.** İstenen `|X[k]|`, `k = 0..7`. Ayrıca sızıntının hangi kutulara düştüğünü açıklamak.

**Adım 2 — Örnekle.** Kosinüs iki karmaşık üstele bölünür: `cos(θ) = (e^{jθ} + e^{−jθ})/2`. Her biri, DFT'de `k = ±2,5`'te bir tepe verir; fakat `k = 2,5` tam kutu olmadığından enerji iki kutuya (`k = 2` ve `k = 3`) yayılır.

**Adım 3 — Kaba çöz.** Dirichlet çekirdeği `D(δ) = Σ_{n=0}^{7} e^{j2πδn/8}` ile `|D(δ)| = |sin(πδ)| / |sin(πδ/8)|`. `k = 2` için ana terim `δ = 2,5 − 2 = 0,5`, dolayısıyla `|X[2]|` yaklaşık `(1/2)·|D(0,5)| = (1/2)·(1/|sin(π/16)|) = 2,563`. İkinci terim `δ = −(2,5 + 2) = −4,5` ile gelir ve `(1/2)|D(−4,5)| = 0,510`'dur.

**Adım 4 — Örüntü.** Gerçek bir kosinüs olduğu için spektrum `k` ile `8 − k` arasında simetriktir: `|X[k]| = |X[8−k]|`. Bu yüzden `k = 2` ve `k = 6` eşittir, `k = 3` ve `k = 5` eşittir. Tepe bölgesinde `k = 2` ve `k = 3` komşudur; ikisinin büyüklüğü farklıdır çünkü ikinci terim (`±0,51`) faza bağlı olarak toplamaya ya da çıkarmaya katkı verir.

**Adım 5 — İyileştir.** Hesap yalnızca ana terimi alırsa `2,563` ve tam sonuç `2,798` arasında kalır. Bu fark, ikinci terimin fazından gelir ve bunu hesaba katmadan doğru değeri elde edemezsin. Dikkat: sonucu iki terimle hesapladığımızda tam değer çıkar.

**Adım 6 — Doğrula.** İz tablosu:

| k | f_k (Hz, fs = 1000) | \|X[k]\| |
|---|---|---|
| 0 | 0 | 1,0000 |
| 1 | 125 | 1,1921 |
| 2 | 250 | 2,7979 |
| 3 | 375 | 2,3980 |
| 4 | 500 | 1,0000 |
| 5 | 625 | 2,3980 |
| 6 | 750 | 2,7979 |
| 7 | 875 | 1,1921 |

Simetri (`k` ↔ `8 − k`) tabloda açıkça görünür. Ana terim `2,5629`, ikinci terim `0,5098`; bunların toplamı ile farkı `2,05` ve `3,07` arasındaki sınırları verir. Gerçek `2,7979` bu aralıktadır. Sayılar yukarıdaki betik ile üretildi (`ornek_dogrula.py`, Ex 2 ile aynı).

```python
# ornek_dogrula.py - Cozumlu Ornek 2 ve 3 dogrulamasi
import numpy as np

# Ornek 2: konvolusyon
x = np.array([1, 2, 3, 4])
h = np.array([1, -1, 2])
print("y =", np.convolve(x, h))

# Ornek 3: 8 noktali DFT, 2,5 kutu tonu
N = 8
n = np.arange(N)
X = np.fft.fft(np.cos(2 * np.pi * 2.5 * n / N))
for k in range(N):
    print(f"k={k} f={k * 1000 / N:6.1f} Hz |X[k]| = {abs(X[k]):.4f}")
D = lambda d: abs(np.sin(np.pi * d) / np.sin(np.pi * d / 8))
print("ana terim |D(0,5)|/2   =", round(0.5 * D(0.5), 4))
print("ikinci terim |D(-4,5)|/2 =", round(0.5 * D(-4.5), 4))
```

```term
$ python ornek_dogrula.py
y = [1 1 3 5 2 8]
k=0 f=   0.0 Hz |X[k]| = 1.0000
k=1 f= 125.0 Hz |X[k]| = 1.1921
k=2 f= 250.0 Hz |X[k]| = 2.7979
k=3 f= 375.0 Hz |X[k]| = 2.3980
k=4 f= 500.0 Hz |X[k]| = 1.0000
k=5 f= 625.0 Hz |X[k]| = 2.3980
k=6 f= 750.0 Hz |X[k]| = 2.7979
k=7 f= 875.0 Hz |X[k]| = 1.1921
ana terim |D(0,5)|/2   = 2.5629
ikinci terim |D(-4,5)|/2 = 0.5098
```

**Bunu AI'sız yazabilir misin?** `x[n] = cos(2π · 2 · n / 8)` için 8 noktalı DFT'yi düşün. Bu sinyal tam bir kutuya oturur. Hangi kutularda sıfır olmayan değerler vardır ve neden? Tahminini tabloyla karşılaştır.

### Örnek 4 (★★★): Q15 FIR, birikim ve doygunluk

Katsayıları `q = [8192, 16384, 16384, 16384, 8192]` (Q15, toplam `65536`, yani kazanç `2,0`) olan bir FIR'i, girdi dizisi `x = [8192, 16384, 32767, 32767, −32768, −32768]` üzerinde elle çalıştır. Her adımda birikimi (Q30), Q15'e dönüşümü ve doygunluğu göster.

**Adım 1 — Anla.** İstenen her çıkış `y[n]`. Kazanç 2 olduğu için tam ölçekli girişte çıkış `32767`'yi aşabilir; doygunluk (saturation) gerekecek.

**Adım 2 — Örnekle.** `n = 2` için buf (en yeni önce): `[32767, 16384, 8192, 0, 0]`. Çarpımlar `q[k] · buf[k]`.

**Adım 3 — Kaba çöz.** `acc = Σ q[k]·x[n−k]` (Q30 birikim). Q15'e dönüşüm: `(acc + 2¹⁴) >> 15`. Sonra `[−32768, 32767]` aralığına doyur.

**Adım 4 — Örüntü.** Girişin pozitif olduğu adımlarda birikim büyür ve `n = 3`'te dönüşüm sonucu `36863` olur; bu `32767`'yi aşar, doyar. `n = 4`'te giriş negatiftir ama birikim hâlâ pozitiftir (eski pozitif örnekler katkı yapar), bu yüzden çıkış da doyar: doygunluk girişin işaretine bağlı değil, birikime bağlıdır.

**Adım 5 — İyileştir.** Birikimi 64-bit tutmak gerekir mi? Bu örnekte en büyük birikim `1,2·10⁹`'dur ve 32-bit `2,1·10⁹` sınırının altında kalır; ama `Σ|q|` büyüdükçe (ör. 4 kazanç) 32-bit taşar. Kodda 64-bit birikim bu yüzden seçildi.

**Adım 6 — Doğrula.** İz tablosu (`n`, `acc`, dönüşüm, çıkış):

| n | x[n] | acc | (acc+2¹⁴)>>15 | y[n] |
|---|---|---|---|---|
| 0 | 8192 | 67108864 | 2048 | 2048 |
| 1 | 16384 | 268435456 | 8192 | 8192 |
| 2 | 32767 | 671080448 | 20480 | 20480 |
| 3 | 32767 | 1207934976 | 36863 | 32767 (doygun) |
| 4 | −32768 | 1140817920 | 34815 | 32767 (doygun) |
| 5 | −32768 | 402620416 | 12287 | 12287 |

`n = 2` satırını elle doğrula: `8192·32767 + 16384·16384 + 16384·8192 = 268427264 + 268435456 + 134217728 = 671080448`. Aşağıdaki betik aynı tabloyu üretir.

```python
# ornek4.py - Cozumlu Ornek 4: 5 tap Q15 FIR ve doygunluk izi
q = [8192, 16384, 16384, 16384, 8192]         # Q15, kazanc 2,0
xs = [8192, 16384, 32767, 32767, -32768, -32768]
print("q =", q, " sum q =", sum(q))
buf = [0] * 5                                 # buf[0] en yeni ornek
for n, xv in enumerate(xs):
    buf = [xv] + buf[:4]
    acc = sum(q[k] * buf[k] for k in range(5))
    yq = (acc + (1 << 14)) >> 15         # yuvarla, 15 saga kaydir
    y = min(max(yq, -32768), 32767)           # doyur
    print(f"n={n} x={xv:6d} acc={acc:11d}"
          f" yuvarlanmis={yq:6d} y={y:6d}")
```

**Bunu AI'sız yazabilir misin?** Aynı katsayılarla girişi `[32767, 0, 0, 0, 0, 0]` yap. Yalnızca ilk iki çıkışın doygunluğa ulaşıp ulaşmadığını söyle ve nedenini açıkla: doyma, birinci örnekte mi yoksa ikinci örnekte mi başlar?

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı kullanma. Kodu, testleri ve ölçümleri kendin yaz. Amaç, bu bölümdeki kavramları boş bir IDE'de ya da bir mülakatta yeniden kurabilmektir. Bir hata bulursan önce kendin çöz; bu, bu bölümün en değerli kısmıdır.
:::

### Proje 1 (★★): Spektrum analizörü

**Amaç.** Bir WAV dosyasını ya da sentetik bir sinyali okuyup pencereli FFT ile spektrumunu, spektrogramını ve tepe frekanslarını çıkaran bir araç yaz.

**Yapılacak / Beklenen davranış.** Program üç şey üretsin: (a) zaman alanı grafiği ve tepe frekansları listesi (en güçlü 5 bileşen, Hz ve dB), (b) Welch yöntemiyle güç spektral yoğunluğu, (c) STFT spektrogramı. Girdi olarak iki kaynak kabul etsin: `scipy.io.wavfile` ile okunan bir WAV dosyası ve üç bileşenli (ör. 440, 1000, 1010 Hz) sentetik bir sinyal. Sentetik sinyalde iki yakın bileşenin (1000 ve 1010 Hz) pencere seçimine göre ayrılıp ayrılmadığını raporla.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Pencere seçimini 52.6'daki takas tablosundan yap. Tepe frekansını kutu merkezinden daha iyi okumak için tepe çevresinde parabolik interpolasyon dene; doğruluğunu sentetik sinyalle (bilinen frekans) sına. Welch için `scipy.signal.welch` ile karşılaştırma yap. Spektrogramda `N` seçimini 52.7'deki tablo ile gerekçelendir.

**Başarı kriterleri.** (1) Sentetik 440 Hz tonun tepe frekansı, kutu çözünürlüğünün (`fs/N`) yarısından az hatayla bulunur. (2) 1000 ve 1010 Hz'lik iki bileşen, seçtiğin pencere ile ayrılır (iki tepe, aralarında belirgin bir vadi) ve bu sonuç 52.6'daki eşikle uyumludur. (3) Welch sonucu `scipy.signal.welch` ile en fazla `%1` göreli farkla eşleşir. (4) Her grafik başlığı kullanılan `fs`, `N` ve pencereyi yazar.

### Proje 2 (★★★): Gömülü IMU işleme hattı

**Amaç.** Bir İHA IMU'sunun ivmeölçer ve jiroskop verisini işleyip eğim açısı kestiren bir hattı önce Python'da, sonra Q15 C'de gerçekleştir; son olarak Cortex-M4 için boyut ve komut analizi yap.

**Yapılacak / Beklenen davranış.** Sentetik veri üret (bu bölümdeki gibi, gerçek sensör yok; sapma, gürültü ve titreşim ekle). Python referansında: (a) ivmeölçer için alçak geçiren FIR ya da EMA, (b) jiroskop integrali, (c) tümleyen filtre. C tarafında: aynı hattı `int16_t` Q15 aritmetiğiyle çalıştır; açıyı Q15'te (`[−π, π]` için uygun ölçekle) temsil et. Python referansı ile C çıktısını karşılaştır. Son olarak `arm-none-eabi-gcc` ile `-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -Os` derle, `arm-none-eabi-size` ve `objdump` ile boyut ve iç döngü komut sayısını raporla.

**Önerilen yaklaşım (ipucu).** Tümleyen filtreyi Q15'e taşırken `α` ve `(1−α)` katsayılarını Q15 olarak sakla; çarpımı 64-bit birikim ile yap. Açı aralığını (`±π`) ölçekle ki taşma olmasın; ölçek dışına çıkma durumunu sına. Kayan noktalı referans ile fark bütçesini (ör. `±2 LSB`) önceden belirle. Sayısal kararlılık için sapma (bias) değerini sabit bir büyüklükte tut.

**Başarı kriterleri.** (1) Python referansı ile C çıktısı arasındaki en büyük fark `±2 LSB` içinde (veya belirlediğin bütçede). (2) ASan ve UBSan ile host testi uyarısız geçer. (3) Derlenmiş `.text` boyutu ve iç döngünün komut sayısı tabloda verilmiştir; `udiv` ve gereksiz dallanma olmadığı `objdump` ile gösterilmiştir. (4) Her ölçüm için üretildiği betik ve tohum (seed) verilmiştir.

### Ek Alıştırmalar

Aşağıdaki problemler cevapsızdır. Her birini önce kendin çöz, sonra kontrol için bu bölümdeki programları kullan.

1. (★) `fs = 1000 Hz` ve `N = 500` örnekle kutu aralığını hesapla ve 125 Hz'lik tonun hangi iki kutunun arasına düştüğünü bul. Ton tam iki kutunun ortasındaysa dikdörtgen pencerede tepe genliği ne kadar düşer (scalloping kaybı, dB)? Tonun bir kutu merkezine oturması için `N`'yi nasıl seçerdin?
2. (★) `x = [1, 0, −1]` ile `h = [2, 2]` konvolüsyonunu elle yap ve uzunluğu yaz.
3. (★) `fs = 2 kHz` ile örneklenen bir sinyalde `1,5 kHz`'lik bileşenin örtüşen frekansını hesapla.
4. (★★) 6 bitlik bir ADC'nin teorik SNR'sini (6,02N + 1,76) hesapla. 8 bitlik bir ADC bu değeri kaç dB kazandırır?
5. (★★) Dikdörtgen pencere ile 8 noktalı DFT'de `cos(2π · 1 · n / 8)` tek bir kutuda mıdır? Yanıtını tabloyla doğrula.
6. (★★) Sinc FIR'in grup gecikmesi `(N−1)/2` ise `N = 31` için gecikme kaç örnektir? Bu gecikme `fs = 1 kHz`'de kaç milisaniyedir?
7. (★★) `y[n] = 0,9 y[n−1] + x[n]` sisteminin kararlı olup olmadığını kutba bakarak söyle. Kutup nerededir?
8. (★★) Hann pencereli bir Welch tahmininin `K` parçası varsa CV yaklaşık `1/√K` gibi azalır. Neden tam `1/√K` değil?
9. (★★★) Q15'te `Σ|b| = 2` olan bir FIR'de 32-bit birikim hangi koşulda taşar? Bu koşulun en kötü durumu ne zaman oluşur?
10. (★★★) Bir eşleşik filtrenin SNR'si, darbe enerjisi ile gürültü gücü oranına nasıl bağlıdır? Darbeyi iki katına çıkarmak yerine kaç kat daha uzun yapmak aynı kazancı verir?
11. (★★★) Bir gyro sapmasının (bias) `b` olduğu varsayılırsa, saf integrasyonun `T` süre sonunda hatası nedir? Tümleyen filtrede aynı sapma hangi sınırda kalır?
12. (★★★) Aynı iki yakın ton için ayrılma eşiği dikdörtgen pencerede Hann'dan küçüktür (1,55 ve 2,50 kutu). Bu sonuç bir radar için ne demektir; yakın hedefleri ayırmak için hangi pencereyi seçersin ve neyden ödün verirsin?

## Kod Okuma Egzersizi

Bu bölümde Cortex-M4 için sık kullanılan bir FIR kütüphanesinin skaler kodunu okuyacağız: ARM'ın CMSIS-DSP kütüphanesindeki `arm_fir_q15`. Kaynak, ARM-software/CMSIS-DSP deposunun `v1.16.2` etiketindeki `Source/FilteringFunctions/arm_fir_q15.c` dosyasıdır (`https://raw.githubusercontent.com/ARM-software/CMSIS-DSP/v1.16.2/Source/FilteringFunctions/arm_fir_q15.c`). Dosyanın kendi başlığındaki `$Revision` alanı `V1.9.0` ve `2021` tarihini gösterir; bu, dosyanın son değişim tarihidir, etiketin tarihi değildir.

Kesit, dosyadaki bir döngünün tam gövdesidir (satır 649–681). Kod birebir kopyadır; hiçbir satır değiştirilmedi.

```c
  while (blkCnt > 0U)
  {
    /* Copy two samples into state buffer */
    *pStateCurnt++ = *pSrc++;

    /* Set the accumulator to zero */
    acc0 = 0;

    /* Use SIMD to hold states and coefficients */
    px = pState;
    pb = pCoeffs;

    tapCnt = numTaps >> 1U;

    while (tapCnt > 0U)
    {
      acc0 += (q31_t) *px++ * *pb++;
	    acc0 += (q31_t) *px++ * *pb++;

      tapCnt--;
    }
    

    /* The result is in 2.30 format. Convert to 1.15 with saturation.
       Then store the output in the destination buffer. */
    *pDst++ = (q15_t) (__SSAT((acc0 >> 15), 16));

    /* Advance state pointer by 1 for the next sample */
    pState = pState + 1U;

    /* Decrement loop counter */
    blkCnt--;
  }
```

Bu döngü, bir blok içindeki her örnek için bir çıkış üretir. Önce örnek durum tamponuna kopyalanır (`*pStateCurnt++ = *pSrc++`), sonra `numTaps` katsayının çarpım-toplamı yapılır ve sonuç 2.30 biçiminden 1.15'e `__SSAT` ile dönüştürülür. Durum tamponu bu yaklaşımda bir kayan pencere dizisidir: yeni örnekler sona eklenir ve her blok sonunda son `numTaps − 1` örnek başa kopyalanır. Bu, bizim dairesel tampon yaklaşımımızdan farklıdır: ARM sürümü SIMD yüklemeleri için bitişik bir bellek ister, biz ise modulo yerine sarmayı dallarla yaptık.

**Sorular — cevaplamadan geçme:**

1. Döngünün her örnek için `*pStateCurnt++ = *pSrc++` ile durumu güncellemesi, bizim halka tamponumuzdaki "yalnızca bir yazma" yaklaşımına göre hangi maliyeti ekler? Blok sonunda yapılan kopyalama hangi durumda pahalı olur?
2. Kodun yorumunda "Use SIMD to hold states and coefficients" yazıyor, ama bu dalda `acc0 += (q31_t) *px++ * *pb++;` gibi skaler çarpımlar var. Bu iki bilgi nasıl uzlaşır? Yorum neden kodla tam örtüşmüyor olabilir?
3. Birikim `q63_t acc0` ile yapılıyor. Bizim kodumuzda da `int64_t` vardı. Bu seçim hangi taşma durumunu önler ve bu seçimin derlenmiş koddaki maliyeti (ör. `smlal` ile) nedir?
4. Kesit, `acc0 >> 15` sonra `__SSAT(…, 16)` yapıyor. Bizim `(acc + (1 << 14)) >> 15` yuvarlamasından farkı nedir? Hangi durumda CMSIS sonucu bizimkinden bir LSB farklı çıkabilir?
5. `(q31_t) *px++ * *pb++` ifadesinde `q15_t` çarpımı neden önce `q31_t`'ye dönüştürülür? Bu dönüşüm olmasa C'de hangi tür kuralı devreye girerdi ve neden sorun olabilirdi?
6. Kütüphanenin `ARM_MATH_LOOPUNROLL` tanımlandığında dört örneği birlikte hesaplayan dal, bu bölümdeki döngüleme kararıyla (`% TAP` yerine dal) nasıl bir ilişki kurar? Açılmış (unrolled) kodun boyutla hız arasındaki takası hangi uygulamada değer kazanır?

## Bölüm Özeti

- **Örnekleme** sürekli bir sinyali `x[n] = x(n/fs)` dizisine çevirir. Nyquist–Shannon koşulu `fs > 2 f_max` bilgi kaybı olmadan geri kurulabilirliği garanti eder.
- **Örtüşme**, Nyquist'in üstündeki bileşenlerin `|f − k·fs|` olarak katlanmasıdır; örneklemeden sonra düzeltilemez. Çözüm, donanımda anti-aliasing filtresidir.
- **Nicemleme** `N` bit için SNR'yi yaklaşık `6,02N + 1,76` dB yapar; yüksek bitlerde ölçüm formülle uyuşur, düşük bitlerde sapar.
- **LTI sistemler** tek bir dürtü yanıtıyla tanımlanır; çıkış konvolüsyondur, `y[n] = Σ x[k] h[n−k]`. Konvolüsyon, polinom çarpımının sinyal dilindeki adıdır (Bölüm 19).
- **DFT** `N` örneği `N` frekans kutusuna ayırır, çözünürlük `fs/N`'dir. FFT aynı sonucu `O(N log N)` ile verir; `np.fft` ölçümde binlerce kat hızlıdır.
- **Pencereleme** sızıntıyı azaltır; ana lob genişliği ile yan lob seviyesi arasında takas vardır. İki tonun ayrılma eşiği yaklaşık ana lob yarı genişliğidir. **Sıfır doldurma** tepe okumayı iyileştirir ama çözünürlüğü değiştirmez.
- **Welch** PSD'nin varyansını parça sayısıyla düşürür; **STFT** zaman ve frekans çözünürlüğü arasında bir takas yapar.
- **FIR** katsayılar ile garanti kararlı ve doğrusal fazlıdır; **IIR** daha az katsayıyla keskin yanıt verir ama kutupların birim çember içinde kalmasını ister.
- **Q15 gerçekleme** dairesel tampon, 64-bit birikim, yuvarlama ve doygunluk ister; `%` yerine dal kullanmak Cortex-M4'te `udiv` maliyetini kaldırır.
- **Eşleşik filtre** bilinen bir darbeyi gürültüde en iyi doğrusal şekilde bulur; Doppler `f_d = 2 v f₀ / c` ile hız ölçümü sağlar.

**Sonraki bölümde:** Bölüm 53 (Paralel & Eşzamanlı Programlama) bu bölümün bir DSP hattını birden çok iş parçacığına ve işlemciye nasıl dağıtacağımızı anlatacak. Bu bölümde FIR'in bir örnek bütçesi hesaplamıştık (`5 × fs` MAC); bir sonraki bölümde bu iş yükünü birden çok çekirdeğe bölmenin kilit, kuyruk ve gecikme maliyetlerini göreceğiz. Bölüm 27'deki senkronizasyon kavramları ve bölüm 44'teki kesme gecikmesi burada doğrudan kullanılacak.

::: mulakat
1. Nyquist–Shannon teoremi neyi garanti eder, neyi garanti etmez? `fs = 2 f_max` neden pratikte yetersizdir?
2. Örtüşme (aliasing) olduktan sonra kayıp veriyi yazılımla geri alamayız. Bunu bir mühendislik kararıyla nasıl bağdaştırırsın?
3. Hann ve dikdörtgen pencerelerden hangisi iki yakın tonu daha iyi ayırır, hangisi zayıf bir tonu daha iyi görür? Neden aynı anda ikisi olmaz?
4. Sıfır doldurma neden "çözünürlük artırmaz" denir? Tepe okumasını iyileştirmenin ile çözünürlüğü artırmanın farkı nedir?
5. FIR ile IIR seçerken hangi kriterlere bakarsın? Doğrusal faz neden bir radar darbesinin biçimini korur?
6. Q15'te 5 katsayılı bir FIR'de 32-bit birikim neden yetmeyebilir? Doygunluğu (saturation) yazılımda neden hem toplamda hem çıkışta düşünmen gerekir?
7. Eşleşik filtre gürültüde neden ham genlik aramasından üstündür? Darbe uzunluğu arttığında kazanç neden artar?
8. Tümleyen filtrenin `α` değerini değiştirmek, ivmeölçer ve jiroskop güvenilirliği hakkında ne söyler? Kalman filtresi bu sezgiyi nasıl genelleştirir?

