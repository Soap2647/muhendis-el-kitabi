%% kisim_no: IV
%% kisim_ad: Algoritmalar
%% kisim_ayrac: evet
%% bolum_no: 12
%% baslik: Algoritma Analizi

## Giriş: Hız bir sayı değil, bir eğridir

Bölüm 10'da bir BST'nin aramasının ağacın yüksekliğine bağlı olduğunu gördük. Bölüm 9'da hash tablosunun O(1) dediğini, ama bunun ortalama bir durum olduğunu öğrendik. Bölüm 7'de dinamik dizinin ekleme maliyetinin "amortize" sabit olduğunu gördük. Her seferinde aynı soru çıktı: bu kod ne kadar hızlı? Bu bölümde o soruya dürüstçe cevap vermeyi öğreneceğiz.

Gündelik cevap şudur: "Benim bilgisayarımda 0,3 saniye sürdü." Bu cümle doğrudur, ama işe yaramaz. Aynı kod yarın başka bir işlemcide, başka bir Python sürümünde ya da 10 kat büyük bir girdiyle çalıştırıldığında ne olacağını söylemez. Algoritma analizi, süreyi bir makineye değil, girdi büyüdükçe işin nasıl büyüdüğüne bağlar. Bu fikir hem mülakatta hem gerçek sistemlerde aynı şekilde işler.

Mülakatta bir çözümü anlatırken "bu O(n log n)" demek, aday için bir sınavdır. Yanıt, neden öyle olduğunu adımlarla açıklayabiliyorsan değer taşır. Savunma ve gömülü sistemlerde ise ölçüm sadece ortalamayı değil, en kötü durumu da sorar. Bir uçuş kontrol döngüsünün her tur belirli bir süreye sığması gerekir; ortalama süre yeterli değildir. Bu yüzden "en kötü durum" kavramı burada yalnızca bir teori merakı değil, güvenlik meselesidir.

Mert'in projelerine dönersek, bir gömülü döngüde her tick'te tüm sensör listesini taramak ilk bakışta makul görünür. Sensör sayısı 10 iken sorun yoktur; 10 000 olduğunda döngü süresi tutturulamaz hâle gelebilir. Bu bölümün araçlarıyla, bu tür bir kodun neden yavaşlayacağını girdi büyümeden önce tahmin edebilirsin.

::: not
Bu bölümde iki ayrı soru soracağız ve bunları birbirine karıştırmamak önemli. Birincisi "bu kod n büyüdükçe nasıl büyür?" sorusudur. İkincisi "girdi hangisi olursa en kötü, en iyi, ortalama durum nedir?" sorusudur. Asimptotik gösterim birinci soruyu, durum analizi ikinci soruyu cevaplar. 12.6'da bu ayrımı ayrıntılı göreceğiz.
:::

## 12.1 Neden ölçmek yetmez? RAM modeli ve adım sayma

Bir programın süresini ölçmek, değerli bir bilgi verir; ama tek başına üç nedenden dolayı yetersizdir. Birincisi **donanım bağımlılığı**: aynı kod, işlemcinin saat hızına, önbellek boyutuna ve işletim sisteminin o anki yüküne göre farklı süre alır. İkincisi **girdi bağımlılığı**: aynı boyuttaki iki girdi, sıralı ya da rastgele olmasına göre çok farklı çalışabilir (bunu 12.6'da göreceğiz). Üçüncüsü **ölçüm gürültüsü**: arka planda çalışan bir uygulama, ölçümün ortasında süreyi değiştirebilir.

Bu üç sorunu aşmak için bilgisayar bilimi, donanımdan soyutlanmış bir model kullanır. En yaygın model **RAM modelidir** (Random Access Machine). Bu modelde şu kurallar geçerlidir:

- Aritmetik işlem (`+`, `-`, `*`, `/`), karşılaştırma, atama ve bir bellek hücresinin okunması/yazılması **sabit maliyetli**, yani 1 adım sayılır.
- Bellek sonsuzdur ve her erişim eşit maliyetlidir. Hangi adrese gidildiği önemli değildir.
- Döngü ve fonksiyon çağrısının kendisi, içindeki işlemlerden ayrı olarak sayılır.

Bu model, süreyi saniyeyle değil **adım sayısıyla** ifade eder. Adım sayısı, makineye bağlı değildir; girdi boyutu `n`'in bir fonksiyonu olarak yazılabilir. Bunu bir örnekle görelim. Aşağıdaki fonksiyon, bir dizinin elemanlarını toplar:

Aşağıdaki kod, `n` elemanlı bir dizinin toplamını alır. Döngü gövdesi her turda bir karşılaştırma, bir toplama ve bir artırma yapar:

```c
#include <stddef.h>

long long toplam(const int *a, size_t n) {
    long long s = 0;
    for (size_t i = 0; i < n; i++)
        s += a[i];
    return s;
}
```

Adımları sayalım. Başlangıçta `s = 0` ve `i = 0` olmak üzere iki atama vardır. Döngüye her girişte `i < n` karşılaştırması yapılır; `n` tur için bu `n` kez, son kontrol için bir kez daha yapılır. Her tur içinde `s += a[i]` (okuma, toplama, atama) ve `i++` yapılır. Toplam kabaca `T(n) = 3n + 3` adımdır. Burada önemli olan sabitler değil, büyümenin doğrusal olduğudur: `n` iki katına çıkarsa adım sayısı da yaklaşık iki katına çıkar.

RAM modelinin sınırı da açıktır. Model, önbelleği görmez. Oysa Bölüm 7'de dizinin ardışık erişiminin önbellek dostu olduğunu, Bölüm 25'te ise bellek hiyerarşisini ayrıntılı göreceğiz. Bu yüzden modelin verdiği adım sayısı, gerçek süreyle ilişkili bir tahmindir; birebir süre değildir. Gerçek süre ile model arasındaki farkı ölçümle kontrol etmek, 12.10'un konusudur.

::: dikkat
Adım saymak, kodu satır satır çalıştırmak değildir. Adım sayarken "bu satır kaç kez çalışır?" sorusunu sorarsın; gövdenin maliyeti sabitse toplam, tur sayısıyla çarpılır. Bu soruyu döngü analizinde (12.5) sistemli olarak kullanacağız.
:::

## 12.2 Asimptotik gösterim: O, Ω, Θ

Adım sayısı `T(n) = 3n + 3` gibi bir ifade verir, ama genellikle bu kadar kesin bir sayıya ihtiyacımız yoktur. Biz büyüme sınıfını merak ederiz: `n` büyüdükçe `T(n)` hangi hızla büyür? **Asimptotik gösterim**, sabitleri ve küçük terimleri atıp büyüme sınıfını yakalayan bir dildir.

**Büyük O (O, üst sınır):** `f(n) = O(g(n))` demek, belirli bir `c > 0` sabiti ve belirli bir `n₀` eşiği için, `n ≥ n₀` olan her `n` için `0 ≤ f(n) ≤ c·g(n)` olmasıdır. Yani `f`, `g`'nin sabit bir katından büyük olamaz. Bu bir üst sınırdır; `f`'nin tam olarak ne olduğunu söylemez.

**Büyük Omega (Ω, alt sınır):** `f(n) = Ω(g(n))` demek, `n ≥ n₀` için `0 ≤ c·g(n) ≤ f(n)` olmasıdır. `f`, `g`'nin bir katından küçük olamaz.

**Büyük Teta (Θ, sıkı sınır):** `f(n) = Θ(g(n))` demek hem O hem Ω olmasıdır. Yani iki sabit `c₁, c₂ > 0` ile `c₁·g(n) ≤ f(n) ≤ c₂·g(n)` (`n ≥ n₀`) olur. `f` ile `g` aynı büyüme sınıfındadır.

Bu tanımları somut bir örnekle sınayalım. `f(n) = 3n² + 5n + 2` için `f(n) = Θ(n²)` olduğunu gösterelim. `n ≥ 1` için:

- Üst sınır: `5n ≤ 5n²` ve `2 ≤ 2n²` olduğundan `f(n) ≤ 3n² + 5n² + 2n² = 10n²`. Yani `c₂ = 10`, `n₀ = 1`.
- Alt sınır: `f(n) ≥ 3n²` açıkça doğrudur. Yani `c₁ = 3`.

Böylece `3n² ≤ f(n) ≤ 10n²` ve `f(n) = Θ(n²)`. Şekil 12.1, bu bandı ve `n₀` eşiğini gösterir.

![Şekil 12.1: Θ(n²) tanımı. f(n) = 3n² + 5n + 2 eğrisi, n ≥ 1 için 3n² ile 10n² arasında kalır. Alt ve üst sabitler c₁ ve c₂, eşik n₀ = 1.](gorseller/b12_asimptotik.png)

Şimdi ters yönü düşünelim: `f(n) = O(n)` olabilir mi? Hayır. Eğer `3n² + 5n + 2 ≤ c·n` olacak şekilde bir `c` ve büyük bir `n` bulabilseydik, `3n² ≤ c·n` yani `3n ≤ c` olurdu. Ama `n` sonsuza giderken `3n` sabit `c`'yi geçer. Çelişki vardır, bu yüzden `f(n) ≠ O(n)`.

Son olarak iki özel sınır: **küçük o** (o) ve **küçük omega** (ω). `f(n) = o(g(n))` demek, *her* `c > 0` için bir eşikten sonra `f(n) < c·g(n)` olmasıdır. O'da sabit bir `c` yeterliyken o'da her `c` gerekir. Pratikte `lim (n→∞) f(n)/g(n) = 0` ise `f = o(g)`. Örneğin `n = o(n²)`, `n log n = o(n²)`. ω, bunun tersidir. Bu bölümde o ve ω'yi yalnızca kavramsal olarak kullanacağız.

::: ipucu
Limit yöntemi pratik bir kestirme sağlar: `lim (n→∞) f(n)/g(n)` sonlu ve sıfırdan büyük bir sayıya gidiyorsa `f = Θ(g)` olur. Sıfıra gidiyorsa `f = o(g)`, sonsuza gidiyorsa `f = ω(g)`. Bu, `3n² + 5n + 2 / n²` oranının `3`'e gittiğini görmenin en kısa yoludur.
:::

Sık yapılan bir hata: "O(n) en kötü durumdur" demek. O, bir **fonksiyonun** üst sınırını tanımlar; durumları (en iyi, en kötü, ortalama) değil. Bir algoritmanın en kötü durum süresi de, en iyi durum süresi de, ortalama süresi de O, Ω ya da Θ ile sınırlanabilir. Bu iki eksen birbirinden bağımsızdır; 12.6'da bunu ayırt edeceğiz.

## 12.3 Yaygın karmaşıklık sınıfları

Analizde sık karşılaşılan büyüme sınıfları, artan hızda şöyledir: `O(1)` (sabit), `O(log n)` (logaritmik), `O(n)` (doğrusal), `O(n log n)`, `O(n²)` (karesel), `O(n³)` (kübik), `O(2ⁿ)` (üstel) ve `O(n!)` (faktöriyel). Aşağıdaki tablo, her sınıfın farklı `n` değerlerinde kabaca kaç işlem gerektirdiğini gösterir. Değerler hesaplanmıştır: `log₂ 10 ≈ 3,32`, `log₂ 100 ≈ 6,64`, `log₂ 10⁶ ≈ 19,93`.

| Sınıf | n = 10 | n = 100 | n = 10⁶ |
|---|---|---|---|
| log₂ n | 3,3 | 6,6 | 19,9 |
| n | 10 | 100 | 10⁶ |
| n log₂ n | 33 | 664 | ≈ 2·10⁷ |
| n² | 100 | 10⁴ | 10¹² |
| n³ | 1 000 | 10⁶ | 10¹⁸ |
| 2ⁿ | 1 024 | ≈ 1,3·10³⁰ | hesaplanamaz |
| n! | 3 628 800 | ≈ 9,3·10¹⁵⁷ | hesaplanamaz |

Tablonun okunması için bir varsayım gerekir: makine saniyede kabaca 10⁹ basit işlem yapsın. Bu, modern bir çekirdek için kaba bir değerdir; kesin değil, ama büyüklük mertebesini görmek için yeterlidir. O hâlde `n = 10⁶` için `n²` yaklaşık 10¹² işlem, yani kabaca 1000 saniye (yaklaşık 17 dakika) eder. `n³` ise 10¹⁸ işlem, yani yaklaşık 31 yıl. `2ⁿ` ve `n!` değerleri için hesap yapmak bile anlamsızlaşır.

Şekil 12.2, aynı eksende bu sınıfların nasıl ayrıştığını gösterir. Y ekseni log ölçeklidir; yoksa `2ⁿ` diğer eğrileri görünmez kılardı.

![Şekil 12.2: Büyüme eğrileri (n = 2..30, log ölçekli y ekseni). log n ve n neredeyse yatay kalır; n log n ve n² orta bölgede ayrışır; 2ⁿ ise hızla yukarı çıkar.](gorseller/b12_buyume.png)

Pratik çıkarım şudur: `n` küçük olduğunda sınıflar arasındaki fark gözle görülmez. Mülakatta "n ≤ 10⁵ olduğunu biliyorum, bu yüzden O(n²) yetmez" demek, bu tabloya dayanan bir akıl yürütmedir. 12.12'de bu muhakemeyi bir protokolün parçası olarak kullanacağız.

## 12.4 Büyüme kuralları: toplam, çarpım, baskın terim, log tabanı

Karmaşıklık ifadelerini sadeleştirmek için dört kural yeterlidir. Bunları ezberlemek yerine nedenlerini anlamak önemlidir.

**Toplam kuralı.** Art arda çalışan iki parça varsa, toplam maliyet en büyük olanla sınırlanır: `O(f) + O(g) = O(max(f, g))`. Önce `n` elemanı tarayan, sonra `n²` ikili karşılaştırma yapan bir kod `O(n + n²) = O(n²)` eder.

**Çarpım kuralı.** Biri diğerinin içinde çalışıyorsa maliyetler çarpılır: `O(f) · O(g) = O(f · g)`. `n` turlu bir döngünün içinde `m` adımlık bir iş varsa toplam `O(n·m)` olur.

**Baskın terim.** Toplamda en hızlı büyüyen terim kalır, küçük terimler ve sabit çarpanlar atılır. `3n² + 5n + 2` ifadesi `O(n²)` olur. Bunun nedeni, `n` büyüdükçe `n²` teriminin toplamı tek başına belirlemesidir: `n = 10⁶` için `3n² = 3·10¹²`, `5n = 5·10⁶`. İkinci terim, birinciye kıyasla ihmal edilebilir.

**Log tabanı önemsizdir.** `log₂ n` ile `log₁₀ n` arasında sabit bir çarpan vardır: `log₂ n = ln n / ln 2`. Bu nedenle `O(log₂ n) = O(log₁₀ n) = O(log n)` yazarız. Taban değişince sadece sabit değişir ve sabitler O'da atılır. (Bu, büyüme sınıfı için geçerlidir; gerçek süre için sabit çarpan önemlidir ve 12.11'de buna döneceğiz.)

Dikkat edilmesi gereken iki nüans var. Birincisi, `2ⁿ⁺¹ = 2 · 2ⁿ` olduğundan `O(2ⁿ⁺¹) = O(2ⁿ)`dir. Ama `4ⁿ = 2²ⁿ` için durum farklıdır: `4ⁿ / 2ⁿ = 2ⁿ` sınırsız büyür, dolayısıyla `4ⁿ ≠ O(2ⁿ)`. Üs içindeki sabit çarpan, büyüme sınıfını değiştirir. İkincisi, `n^2.0001` ile `n²` arasındaki fark teoride var, pratikte büyük önem taşımaz ama sınıf olarak ayrıdır; bu tür ince ayrımlar, Master Teoremi ile 12.9'da ilgilidir.

Çok değişkenli girdilerde değişkenleri ayrı tutmak gerekir. Bir grafın maliyeti `O(V + E)` (düğüm sayısı `V`, kenar sayısı `E`) gibi yazılır; `O(V²)` demek, `E`'yi gizlemek olurdu. Bölüm 11'deki komşuluk listesi ile matrisi arasındaki fark tam olarak buradadır.

## 12.5 Döngü analizi: iç içe, bağımlı, logaritmik, harmonik

Algoritma analizinin en sık işi döngüleri saymaktır. Kural basittir: bir gövdenin kaç kez çalıştığını bul, gövdenin maliyetiyle çarp. Zorluk, iç içe döngülerde ve döngü değişkeninin nasıl değiştiğinde ortaya çıkar. Beş yaygın kalıbı ele alalım.

**Tek döngü:** `for (i = 0; i < n; i++)` gövdesi `n` kez çalışır: `O(n)`.

**İç içe bağımsız döngü:** İki döngünün sınırları birbirinden bağımsızdır (`i < n`, `j < n`). İç gövde `n · n = n²` kez çalışır: `O(n²)`.

**Bağımlı döngü:** İç döngünün sınırı dış döngü değişkenine bağlıdır (`j < i`). Toplam `0 + 1 + 2 + ... + (n−1) = n(n−1)/2` olur. Bu `Θ(n²)`dir; 1/2 sabiti atılır.

**Logaritmik döngü:** Değişken her turda ikiye katlanır (`i *= 2`). `i` değerleri `1, 2, 4, ...` olur ve `i ≥ n` olunca durur. Tur sayısı `⌈log₂ n⌉`dir. Bölüm 5'teki ikili aramanın adım sayısı da aynı mantıkla logaritmiktir.

**Harmonik döngü:** Dış döngü `i = 1..n`, iç döngü `j` her seferinde `i` kadar artar. İç döngü `⌈n/i⌉` kez çalışır. Toplam `Σ ⌈n/i⌉` olur ve `n · Hₙ` ile `n · Hₙ + n` arasındadır; burada `Hₙ = 1 + 1/2 + ... + 1/n ≈ ln n + 0,577`dir. Bu nedenle toplam `Θ(n log n)`dir. Bu kalıp, Bölüm 17'deki bazı grafik algoritmalarının analizinde sık çıkar.

Beş kalıbı tek bir C programında sayalım. Her fonksiyon, gövdesinde yalnızca bir sayaç artırır; böylece gerçek adım sayısını formüllerle karşılaştırabiliriz. `long long` kullanıyoruz, çünkü Windows'ta `long` 32 bittir (LLP64 modeli) ve `n²` değerleri taşabilir.

Aşağıdaki üç fonksiyon, üç döngü kalıbının gövde sayısını döndürür:

```c
typedef long long ll;

ll tek_dongu(ll n) {
    ll say = 0;
    for (ll i = 0; i < n; i++)
        say++;
    return say;
}

ll ic_ice(ll n) {
    ll say = 0;
    for (ll i = 0; i < n; i++)
        for (ll j = 0; j < n; j++)
            say++;
    return say;
}

ll bagimli(ll n) {
    ll say = 0;
    for (ll i = 0; i < n; i++)
        for (ll j = 0; j < i; j++)
            say++;
    return say;
}
```

Kalan iki kalıp da aynı dosyadadır: logaritmik döngü `i *= 2` ile, harmonik döngü iç döngüde `j += i` ile yazılır. Harmonik döngüde iç döngü `j = 1`'den başlayıp `i`'şer atladığı için `i` adımında tam `⌈n/i⌉` kez döner. Dosyanın geri kalanı ve `main` şöyle:

```c
ll log_dongu(ll n) {
    ll say = 0;
    for (ll i = 1; i < n; i *= 2)
        say++;
    return say;
}

ll harmonik(ll n) {
    ll say = 0;
    for (ll i = 1; i <= n; i++)
        for (ll j = 1; j <= n; j += i)
            say++;
    return say;
}

int main(void) {
    ll boyut[] = {10, 100, 1000};
    for (int k = 0; k < 3; k++) {
        ll n = boyut[k];
        printf("n=%5lld tek=%5lld ic=%8lld bagimli=%7lld"
               " log=%3lld harm=%6lld\n",
               n, tek_dongu(n), ic_ice(n), bagimli(n), log_dongu(n),
               harmonik(n));
    }
    return 0;
}
```

Bu beş fonksiyonu derleyip çalıştırdığımızda çıktı şöyle oldu. Derleme WSL içinde yapıldı; Windows'ta MinGW ile de derleyebilirsin, ama sanitizer araçları için WSL gerekir:

```term
$ gcc -O2 -Wall -Wextra -std=c11 sayac.c -o sayac
$ ./sayac
n=   10 tek=   10 ic=     100 bagimli=     45 log=  4 harm=    33
n=  100 tek=  100 ic=   10000 bagimli=   4950 log=  7 harm=   573
n= 1000 tek= 1000 ic= 1000000 bagimli= 499500 log= 10 harm=  8053
```

Çıktıyı formüllerle karşılaştıralım. İç içe döngü `n²` verir: `1000² = 1 000 000`. Bağımlı döngü `n(n−1)/2 = 499 500` verir ve çıktı birebir budur. Logaritmik döngü `⌈log₂ 1000⌉ = 10` verir. Harmonik döngü `Σ ⌈n/i⌉` adım yapar. `n · Hₙ ≈ 7485`tir; gerçek sayı 8053'tür, çünkü her `⌈n/i⌉` terimi `n/i`'den en fazla 1 büyüktür ve bu, `[n·Hₙ, n·Hₙ + n) = [7485, 8485)` aralığında olduğundan beklenen bir sonuçtur. Asimptotik analizde bu sabit fark önemsizdir.

::: dikkat
Döngü sayarken "değişken nasıl değişiyor?" sorusunu açıkça yaz. `for (i = 1; i < n; i *= 2)` içinde `i` değişir, `n` değişmez. Sınırı yanlış yazmak (`<` ile `<=`, `i = 0` ile `i = 1`) `O(n)` ile `O(log n)` gibi çok farklı sonuçlar üretir; bu yüzden değişim kuralını her zaman yaz.
:::

## 12.6 En iyi, en kötü ve ortalama durum

Şimdiye kadar hep "girdi boyutu `n`" üzerinden konuştuk. Ama aynı boyutta iki farklı girdi, bir algoritmayı çok farklı çalıştırabilir. Doğrusal arama bunun en basit örneğidir: aranan eleman ilk sırada olabilir ya da hiç olmayabilir.

Üç durum tanımlarız:

- **En iyi durum (best case):** algoritmanın en az iş yaptığı girdi.
- **En kötü durum (worst case):** algoritmanın en çok iş yaptığı girdi. Gerçek zamanlı sistemler için kritik olan budur.
- **Ortalama durum (average case):** tüm girdilerin olasılığına göre beklenen iş. Bir olasılık dağılımı varsayımı gerektirir.

Doğrusal aramayı ele alalım: `n` elemanlı bir dizide hedefi tara, bulursan dur. En iyi durumda hedef ilk elemandır: 1 karşılaştırma, `Θ(1)`. En kötü durumda hedef yoktur ya da sondadır: `n` karşılaştırma, `Θ(n)`. Ortalama durumda hedefin her konumda eşit olasılıkla bulunduğunu varsayalım. `i`. konumda bulunuyorsa `i` karşılaştırma yapılır. Beklenen değer `(1 + 2 + ... + n)/n = (n + 1)/2`dir, yani `Θ(n)`.

Bu beklentiyi bir deneyle kontrol ettik. Rastgele bir dizide (tohum 42), hedefi her konumdan eşit olasılıkla seçip 20 000 arama yaptık:

| n | Ölçülen ortalama | (n + 1)/2 |
|---|---|---|
| 10 | 5,50 | 5,50 |
| 100 | 50,32 | 50,50 |
| 1000 | 503,94 | 500,50 |

Ölçülen değerler beklenenin etrafında dalgalanır; bu rastgele örneklemenin doğasıdır ve deneme sayısı arttıkça yakınsar.

Hızlı sıralama (quicksort) üç durumun ne kadar farklı olabileceğini gösterir. Ayrıntıyı Bölüm 13'te göreceğiz; burada iskelet yeterlidir. Pivot olarak her seferinde ilk elemanı seçen naif bir sürüm, **sıralı girdide** en kötü duruma düşer: her bölme yalnızca bir eleman ayırır ve toplam `n(n−1)/2` karşılaştırma yapılır (`Θ(n²)`). Pivot rastgele seçildiğinde ortalama süre `Θ(n log n)`dir. Naif sürümü sıralı girdilerle saydığımızda karşılaştırma sayıları `n = 100` için `4950`, `n = 1000` için `499 500` çıktı; formül birebir tuttu.

Naif sürümün aynı girdide başka bir sorunu daha var. Özyineleme derinliği `n`'e çıkar. Python'da varsayılan özyineleme sınırı 1000'dir ve `n = 1000` sıralı girdide naif sürüm `RecursionError` ile çöktü. Bu, en kötü durumun yalnızca süreyi değil **uzay** maliyetini de artırdığını gösterir; 12.8'de buna dönüyoruz.

::: not
En kötü durum ile ortalama durum arasındaki fark, "girdi nasıl üretiliyor?" sorusuna bağlıdır. Gerçek veri çoğu zaman kısmen sıralıdır (bir log dosyasının zaman damgaları gibi). Bu yüzden rastgele pivot seçimi ya da veriyi karıştırmak, ortalama durumu gerçek bir koruma hâline getirir. Girdi üzerinde kontrolün yoksa en kötü durumu hesaba katman gerekir.
:::

## 12.7 Amortize analiz

Bazı işlemler tek başına pahalıdır, ama uzun bir dizi içinde ortalama maliyet düşüktür. Bölüm 7'de dinamik dizinin ekleme işlemini bu şekilde gördük: kapasite dolunca tüm elemanlar kopyalanır (`O(n)`), ama kapasite ikiye katlandığı için `n` ekleme boyunca toplam kopyalama `O(n)`dir ve ekleme başına amortize `O(1)` olur.

**Amortize analiz**, bir işlem dizisinin toplam maliyetini işlem sayısına böler. Tek bir işlem `O(n)` olabilir, ama `k` işlemin toplamı `O(k)` ise amortize maliyet `O(1)`dir. Bu bir **ortalama durum değildir**: girdi üzerinde olasılık varsaymaz, her işlem dizisi için garanti verir. Bu ayrım önemlidir ve 12.6'daki ortalama durumla karıştırılmamalıdır.

Amortize analizin üç yöntemi vardır. Hepsi aynı sonucu verir; hangisinin kullanılacağı problemin yapısına bağlıdır.

**Toplam (aggregate) yöntemi.** `k` işlemin toplam maliyetini hesapla, `k`'ya böl. Dinamik dizide kapasite `1, 2, 4, ..., 2ʲ` değerlerini alır; kopyalama sayısı toplamda `1 + 2 + 4 + ... < 2n`dir. `n` ekleme için toplam iş `n` yazma artı `< 2n` kopyalama, yani `< 3n`. Amortize maliyet `< 3`tür: sabit.

**Muhasebe (accounting) yöntemi.** Her işleme gerçek maliyetinden farklı bir **amortize ücret** ver. Fazla ücret, ileride kullanılmak üzere bir bakiyeye yatırılır; pahalı işlem bu bakiyeyi harcar. Dinamik dizide her ekleme için 3 birim ücret alırız: 1 birim kendi yazma işine, 1 birim kendisinin ileride kopyalanmasına, 1 birim de bir eski elemanın kopyalanmasına harcanır. Kanıt, bakiyenin hiçbir zaman negatif olmadığını göstermektir.

**Potansiyel (potential) yöntemi.** Veri yapısının durumuna bir sayı `Φ` (potansiyel) atarız. Gerçek maliyet `c`, potansiyel değişimi `ΔΦ` ise amortize maliyet `ĉ = c + ΔΦ` olur. `Φ` başlangıçta 0 ve hiçbir zaman negatif değilse, `Σ ĉ = Σ c + Φ_son ≥ Σ c` olur; yani amortize toplam gerçek toplamın üst sınırıdır.

Dinamik dizi için `Φ = 2·boy − kapasite` seçilebilir. Kapasite dolu değilken ekleme: gerçek maliyet 1, `ΔΦ = +2`, amortize 3. Dolu iken (`boy = kapasite = k`) ekleme: `k` kopyalama artı 1 yazma, gerçek maliyet `k + 1`. Önce `Φ = 2k − k = k`; sonra kapasite `2k`, boy `k + 1` olur ve `Φ = 2(k+1) − 2k = 2`. Yani `ΔΦ = 2 − k` ve amortize maliyet `(k + 1) + (2 − k) = 3`. İki durumda da amortize maliyet 3'tür.

Aynı fikri ikili sayaçta da görebiliriz: `n` artış boyunca her artış en sağdaki 1 bitlerini 0'a çevirip ilk 0'ı 1 yapar. Tek bir artış `O(log n)` bit değiştirebilir, ama `n` artışın toplam bit çevirme sayısı `< 2n`dir. Simülasyonumuzda `n = 1000` artış 1994 çevirme yaptı; `n = 100 000` artış 199 994 çevirme yaptı. Toplam/n ≈ 2 olduğundan amortize maliyet sabittir.

Şekil 12.3, dinamik dizide büyüme stratejisinin etkisini gösterir: kapasiteyi her seferinde bir artırmak (kırmızı) ekleme başına ortalama işi `n` ile birlikte büyütür; kapasiteyi ikiye katlamak (yeşil) ortalamayı 2 ile 3 arasında tutar.

![Şekil 12.3: Amortize maliyet. Kapasiteyi her seferinde bir artırmak (kırmızı) ekleme başına ortalama işi n ile birlikte büyütür. Kapasiteyi ikiye katlamak (yeşil) ortalamayı 2 ile 3 arasında tutar.](gorseller/b12_amortize.png)

::: dikkat
Amortize `O(1)`, tek bir işlemin `O(1)` olduğu anlamına gelmez. Gerçek zamanlı bir sistemde tek bir yavaş ekleme zaman sınırını aşabilir. Bu yüzden gerçek zamanlı kodda amortize garanti yerine en kötü durum sınırı aranır ya da yeniden tahsis işlemi zamana yayılır.
:::

## 12.8 Uzay karmaşıklığı

Zaman kadar önemli bir diğer ölçü **uzaydır**: algoritma `n` girdi için ek olarak kaç bellek birimi kullanır. Girdinin kendi belleği genellikle ayrı sayılır; analizde **yardımcı bellek** (auxiliary space) sorulur. Girdiyi yerinde (in-place) değiştiren bir algoritma `O(1)` yardımcı bellek kullanır; girdinin kopyasını tutan bir algoritma ise `O(n)`.

Özyinelemeli algoritmalarda uzay, çağrı yığınından gelir. Bölüm 8'de gördüğümüz gibi, her çağrının bir çerçevesi (dönüş adresi, yerel değişkenler) yığında yer tutar. Derinlik `d` ve çerçeve boyutu sabitse yığın maliyeti `O(d)`dir. Bölüm 10'da dengesiz bir BST'de özyinelemeli gezinmenin derinliğinin `n`'e çıkabildiğini gördük; o gezinmenin uzay maliyeti `O(n)`dir. Dengeli bir ağaçta ise `O(log n)`dir.

Platform notu: x86-64'te `call` komutu dönüş adresini doğrudan yığına iter. ARM tabanlı mikrodenetleyicilerde (ör. STM32, Cortex-M) `BL` komutu dönüş adresini LR yazmacına koyar; fonksiyon başka bir fonksiyon çağıracaksa LR'yi yığına kendisi iter. Bir gömülü sistemde yığın boyutu sınırlıdır ve derin özyineleme yığın taşmasına yol açabilir.

Yığın boyutu derleyiciye ve işletim sistemine göre değişir. MSVC'nin varsayılanı 1 MB'dır; Linux'ta genellikle 8 MB'dır ve `ulimit -s` ile görülür. Bu sayıyı ezberlemek yerine kendi ortamında ölçmek daha sağlıklıdır.

Python'da özyineleme sınırı ayrı bir mekanizmadır. `sys.getrecursionlimit()` değeri 1000'dir ve aşıldığında `RecursionError` fırlatılır. Yaptığımız bir denemede `derin(n) = 1 + derin(n − 1)` fonksiyonu `n = 998`'e kadar çalıştı; yani sınır Python'un kendi koruma mekanizmasıdır, işletim sisteminin yığını değildir.

Son olarak zaman ve uzay arasında bir **ödünleşim** vardır. Bölüm 9'daki hash tablosu, bellek karşılığında ortalama `O(1)` arama verir. Bölüm 5'teki "önce sor, sonra ekle" örneğinde `O(n)` ek bellekle `O(n²)` zamanı `O(n)`e indirdik. Algoritma tasarımında bir kaynağı diğeriyle takas ederiz; bu takasın kararını analiz üretir, sezgi değil.

## 12.9 Özyinelemeli bağıntılar: yerine koyma, ağaç, Master Teoremi

Özyinelemeli bir algoritmanın maliyeti, kendi küçük örneklerinin maliyetine bağlıdır. Bu ilişki bir **özyinelemeli bağıntı (recurrence)** ile yazılır. Merge sort'u düşünelim: `n` elemanı ikiye böl, iki yarıyı ayrı ayrı sırala, sonra `n` adımda birleştir. Maliyet şöyle yazılır:

`T(n) = 2T(n/2) + n`, `T(1) = 1`

Bu bağıntıyı çözmenin üç yolu vardır. Hangisinin uygun olduğu, bağıntının biçimine bağlıdır.

**Yerine koyma (substitution).** Bir büyüme tahmini yap, bunu bağıntıya koyup tümevarımla doğrula. Örneğin `T(n) = T(n−1) + 1` için `T(n) = n` tahmin edilirse, `T(n−1) = n − 1` yerine konunca `T(n) = n` çıkar; taban durum `T(1) = 1` de tutar. Tahmini bulmak için genellikle birkaç adım açarak örüntüyü görürüz.

**Özyineleme ağacı.** Bağıntıyı bir ağaç olarak çizeriz: kök, ilk çağrının maliyetini; çocuklar, alt çağrıların maliyetini taşır. Her seviyenin toplam maliyetini topla, seviyeleri topla. Merge sort için her seviyenin toplamı `n`'dir ve seviye sayısı `log₂ n + 1`'dir. Şekil 12.4'te `n = 8` için bu gösterilmiştir.

![Şekil 12.4: T(n) = 2T(n/2) + n için özyineleme ağacı, n = 8. Her seviye toplam n iş yapar; 4 seviye vardır. Toplam 4·8 = 32 = n·(log₂ n + 1), T(8) değeriyle eşleşir.](gorseller/b12_agac.png)

Ağaçtan çıkan formül `T(n) = n log₂ n + n`dir. Bunu kontrol edelim: `n = 8` için `8·3 + 8 = 32`; `n = 1024` için `1024·10 + 1024 = 11 264`. Deneyde `T(n)` özyinelemeyle hesaplandığında `n = 2, 8, 32, 1024` için sırasıyla `4, 32, 192, 11 264` çıktı; formül tüm değerlerle tutuyor.

**Master Teoremi.** Biçimi `T(n) = a·T(n/b) + f(n)` olan bağıntılar için bir tarif kitabıdır. Burada `a ≥ 1` alt problem sayısı, `b > 1` küçülme oranıdır. `c = log_b a` diyelim. Üç durum vardır:

1. `f(n) = O(n^(c−ε))` (bazı `ε > 0` için): `T(n) = Θ(n^c)`. İşin büyük kısmı yaprakta.
2. `f(n) = Θ(n^c)`: `T(n) = Θ(n^c · log n)`. Her seviye eşit iş yapar, seviye sayısı `log n`.
3. `f(n) = Ω(n^(c+ε))` ve düzenlilik koşulu `a·f(n/b) ≤ δ·f(n)` (bazı `δ < 1` için): `T(n) = Θ(f(n))`. İş köktedir.

Her durumun sezgisi şöyledir: ağacın iki ucu (kök ve yapraklar) ile seviyelerin dengesi. `n^c` yaprak sayısının (`a^(log_b n) = n^c`) ölçüsüdür. Eğer `f`, yapraklardan yavaş büyürse yapraklar baskındır (1); aynı hızda büyürse her seviye eşittir (2); hızlı büyürse kök baskındır (3).

Şekil 12.5, üç durumun `a = 2, b = 2, c = 1` seçimi için `f(n)` ile `n^c`'nin nasıl kıyaslandığını gösterir.

![Şekil 12.5: Master Teoremi üç durumu (a = 2, b = 2, c = 1). Soldan sağa: f(n) = √n (durum 1, sonuç Θ(n)), f(n) = n (durum 2, Θ(n log n)), f(n) = n² (durum 3, Θ(n²)). Gri kesik çizgi n^c'yi gösterir.](gorseller/b12_master.png)

Üç durumu uygulayalım:

- **Merge sort:** `a = 2, b = 2`, `c = 1`, `f(n) = n = Θ(n¹)`. Durum 2: `T(n) = Θ(n log n)`. Şekil 12.4'teki ağacın sonucu budur.
- **İkili arama:** `a = 1, b = 2`, `c = 0`, `f(n) = 1 = Θ(n⁰)`. Durum 2: `T(n) = Θ(log n)`.
- **`T(n) = 4T(n/2) + n`:** `c = 2`, `f(n) = n = O(n^(2−ε))` (`ε = 1`). Durum 1: `T(n) = Θ(n²)`.
- **`T(n) = 2T(n/2) + n²`:** `c = 1`, `f(n) = n² = Ω(n^(1+ε))`. Düzenlilik: `2·(n/2)² = n²/2 = 0,5·f(n)`, yani `δ = 0,5`. Durum 3: `T(n) = Θ(n²)`. Deneyde `T(n)/n²` oranı `n = 2⁴`'te 1,94, `n = 2¹⁶`'da 1,99998'e ulaştı; yani `T(n) → 2n²`dir ve sabit `2` bu durumda sınırın kendisidir.
- **Strassen matris çarpımı:** `T(n) = 7T(n/2) + Θ(n²)`. `c = log₂ 7 ≈ 2,807`, `f(n) = Θ(n²) = O(n^(2,807−ε))`. Durum 1: `T(n) = Θ(n^(log₂ 7))`, yani yaklaşık `Θ(n^2,807)`. Bu algoritma Bölüm 19'da yer alır.

Master Teoremi her bağıntıya uygulanmaz. Üç tipik örnek:

- **`T(n) = 2T(n/2) + n log n`:** `f(n) = n log n` ne `Θ(n^c)` (`c = 1`) ne de polinom farkıyla ayrılır; üç durumun hiçbiri tam olarak uymaz. Bu bağıntı için sadeleştirilmemiş bir teknik gerekir.
- **`T(n) = 2T(n/2) + n / log n`:** `f(n)`, `n^c = n`'den polinom olarak küçük de değil, büyük de değildir (`1/log n` bir polinom farkı değildir). Bu bir "boşluktur" ve temel üç durum bunu kapsamaz.
- **`T(n) = T(n−1) + n`:** küçülme `n/b` biçiminde değil, `n − 1` biçimindedir. Master Teoremi yerine açarak çöz: `T(n) = n + (n−1) + ... + 1 = Θ(n²)`.

::: dikkat
Master Teoremi ezberlerken en sık yapılan hata, `a` ve `b` değerlerini karıştırmaktır. `c = log_b a` olduğunu, yani `a` alt problem sayısı ve `b` küçülme oranı olduğunu her zaman kontrol et. `T(n) = 2T(n/2) + n`de `c = log₂ 2 = 1`dir; `c`'yi `log₂ n` ile karıştırırsan sonuç çöker.
:::

## 12.10 Deneysel doğrulama: log-log grafiği ve eğim

Teori bize bir büyüme sınıfı verir; deney onu sınar. Bir algoritmanın süresini farklı `n` değerlerinde ölçersek, `T(n) ≈ c · n^k` ilişkisinde `k`'yı bulabiliriz. Bunun için iki eksenin de logaritmik olduğu bir grafik kullanılır. `log T = k · log n + log c` olduğundan, veri noktaları bir doğru üzerine düşer ve doğrunun eğimi `k`'dır. Bu eğim, **üssün tahminidir**.

Protokol şöyledir ve her adımı tekrarlanabilir olmalıdır:

1. **Tohum:** Rastgele veri üretirken sabit bir tohum kullan (`random.seed(42)`). Böylece aynı girdi her koşuda aynıdır.
2. **Isınma ve tekrar:** İlk çalıştırmayı (önbellek, JIT, sayfa tahsisi) atla. Her ölçümü birkaç kez tekrarla ve **en iyi süreyi** al; ortalama, arka plan gürültüsünü taşır, en iyi süre ise algoritmanın kendi maliyetine yakındır.
3. **Makine bilgisi:** Ölçümle birlikte işlemciyi, bellek boyutunu, işletim sistemini ve dil sürümünü yaz.
4. **Aralık:** `n`'i birkaç büyüklük mertebesi boyunca değiştir. Çok küçük `n`'lerde sabit yükü görürsün; çok büyük `n`'lerde önbellek etkisi girer.
5. **Eğim:** Log-log doğrusunun en küçük kareler eğimini hesapla.

Aşağıdaki iki yardımcı fonksiyon, ölçüm ve eğim hesabını yapar. `en_iyi_sure`, bir fonksiyonu tekrar tekrar çalıştırıp en küçük süreyi döndürür; `egim` ise `numpy.polyfit` ile log-log doğrusunu uydurur:

```python
import time
import numpy as np

def en_iyi_sure(fonk, tekrar=5):
    en = float("inf")
    for _ in range(tekrar):
        t0 = time.perf_counter()
        fonk()
        en = min(en, time.perf_counter() - t0)
    return en

def egim(xs, ys):
    lx = np.log2(np.array(xs, dtype=float))
    ly = np.log2(np.array(ys, dtype=float))
    return float(np.polyfit(lx, ly, 1)[0])
```

Deneyi bu iki fonksiyonla şu makinede yaptık: AMD Ryzen 7 6800H (8 çekirdek, 16 iş parçacığı, en yüksek saat 3201 MHz), 32 GB bellek, Windows 11, Python 3.12.10 ve numpy 2.3.5. Her ölçüm için en iyi süre alındı. Dört algoritma için sonuçlar şöyle:

| Algoritma | Ölçülen n aralığı | Eğim (koşu 1 / koşu 2) |
|---|---|---|
| O(n) Python döngüsü ile toplam | 4 096 – 1 048 576 | 1,009 / 0,999 |
| O(n log n) `sorted` | 4 096 – 1 048 576 | 1,195 / 1,193 |
| O(n²) iç içe karşılaştırma | 250 – 2 000 | 2,061 / 2,057 |
| O(1) sözlük araması (100 000 arama) | 1 024 – 1 048 576 | 0,341 / 0,341 |

Üç satır beklenen sonucu verir. Doğrusal toplamın eğimi 1,00'dır. Karesel çift karşılaştırma 2,06'dır; sabit payı yüzde birkaç düzeyinde saptırır. `sorted` için eğim 1,19–1,20'dir ve bu beklenenden biraz büyüktür. Nedeni `n log n`'in kendisidir: log-log eğimi `1 + 1/ln n` kadar fazladır ve `n = 10⁶` civarında bu yaklaşık 0,07'dir. Küçük fark, büyük `n`'de artan önbellek maliyetiyle de birleşir. Yani log-log eğimi `n log n` ile `n`'i kesin olarak ayırt etmez; `n log n` için 1,2 eğimi bir ipucudur, kanıt değildir.

Dördüncü satır en öğretici olanıdır. Sözlük araması teoride `O(1)`dir, eğimi ise 0,34'tür. Şekil 12.6 bunu gösterir: sözlük küçük iken tüm verisi önbelleğe sığar ve süre sabittir; sözlük büyüdükçe rastgele erişimler önbellek dışına taşar ve süre artar. Bu, "O(1) eğimi sıfır olmalı" beklentisini yanıltır.

![Şekil 12.6: Dört işlemin log-log ölçümü. Doğrusal (1,01), n log n (1,20) ve karesel (2,06) serilerin eğimleri teoriyle uyumludur. O(1) sözlük serisi (0,34) önbellek taşması nedeniyle sabit değildir.](gorseller/b12_loglog.png)

::: not
Zaman ölçümü tam olarak tekrarlanamaz: iki koşu arasında mutlak süreler değişir. Ama eğim, mutlak süreye değil oranlara dayandığı için iki koşuda da yaklaşık aynı çıkar (en fazla 0,01 fark). Bu yüzden rapor ederken süre yerine eğimi ve ölçüm koşullarını birlikte yaz.
:::

## 12.11 Big-O'nun yalan söylediği yerler

Asimptotik analiz doğrudur, ama tek başına karar vermek için eksiktir. Dört yerde büyük O, pratik gerçeği gizler.

**Sabit çarpanlar.** `100n` ve `n²` farklı büyüme sınıflarındadır, ama `n = 100`'e kadar `100n` daha pahalıdır. Şekil 12.7, iki eğrinin kesiştiği noktayı gösterir: `n > 100`'de `n²` daha pahalıdır. Bu, küçük `n` için sabit çarpanın belirleyici olabileceğinin bir örneğidir. Bu yüzden sıralama algoritmaları, küçük dizilerde kendi karmaşıklıklarından daha basit yöntemlere geçer; Bölüm 13'te bunu göreceğiz. Python'un `sort` fonksiyonu, `minrun` denilen 32–64 aralığındaki küçük parçaları ikili eklemeli sıralama ile sıralar (CPython 3.12 `Objects/listsort.txt` tasarım notu).

![Şekil 12.7: Sabit çarpan. 100n (koyu mavi) ve n² (kırmızı) n = 100'de kesişir. Bu noktadan sonra n² daha pahalıdır; daha küçük n için tersi geçerlidir.](gorseller/b12_sabit_carpan.png)

**Önbellek.** RAM modeli her erişimi eşit sayar. Gerçekte bellek hiyerarşisi vardır (Bölüm 25) ve ardışık erişim, rastgele erişimden çok daha hızlıdır. Aynı `O(n)` toplamı iki farklı sırayla yaptık: bir `int` dizisinin 16 milyon elemanını önce sırayla (`a[i]`), sonra bir rastgele permütasyonla (`a[p[i]]`) topladık. Her iki döngü de aynı sayıda işlem yapar; C'de `-O2` ile WSL'de derlendiğinde sonuç şöyleydi:

```c
for (unsigned int i = 0; i < N; i++)
    s += a[i];                /* sirali erisim */

for (unsigned int i = 0; i < N; i++)
    s += a[p[i]];             /* rastgele erisim */
```

Kodun tamamı, 64 MB'lık `a` ve 64 MB'lık `p` dizilerini ayırıp `rand()` ile Fisher-Yates karıştırması yapan bir programdır; süreler `clock()` ile en iyi üç dört tekrardan alınmıştır. Sonuç, 16 777 216 eleman için:

```term
$ ./onbellek
N = 16777216 (64 MB dizi)
sirali erisim   :     3.17 ms
rastgele erisim :   102.56 ms
oran            :    32.34
```

Oran yaklaşık 32'dir; aynı `O(n)` iki kez çalıştı. Bu, mikro bir ölçümdür ve makineye bağlıdır: 64 MB'lık dizi, tipik bir masaüstü işlemcinin son seviye önbelleğinden kat kat büyüktür. Rastgele döngü `p` dizisini de sırayla okur; yani farkın tamamı `a`'ya rastgele erişimden değil, bu erişimlerin önbellek kaçırmalarından gelir. Derleyici sıralı döngüyü vektörleştirebilir de; bu da farkı büyütür. Yine de mesaj nettir: büyük O, bellek düzenini söylemez.

![Şekil 12.8: Aynı O(n) toplamın iki erişim düzeni. Sıralı erişim 3,17 ms, rastgele erişim 102,56 ms sürdü (Ryzen 7 6800H, Windows 11, WSL gcc -O2).](gorseller/b12_onbellek.png)

**Küçük `n` ve dil.** Python'daki `for` döngüsü, C'deki aynı döngüden onlarca kat yavaştır. Bu fark sabit çarpandır ve büyük O'da görünmez. Mülakatta "Python'da bu yavaş olur" demek, C'de yazsan bile aynı büyüme sınıfının farklı bir süre vereceğini bilmek demektir.

**Girdi dağılımı.** Bölüm 10'da sıralı girdiyle bir BST'nin bağlı listeye dönüştüğünü gördük. Aynı algoritma, rastgele girdide `O(log n)` olur. Girdi dağılımı, hangi büyüme sınıfının gerçekleşeceğini belirler. Bölüm 9'daki hash flooding saldırısı da bu tür bir yanılgıyı sömürür: ortalama durum varsayımı kötü niyetli bir girdiyle bozulur.

::: ipucu
Bir algoritmanın büyük O'sunu öğrendikten sonra iki soru sor: "girdi büyüdüğünde hangi bellek düzeni kullanılıyor?" ve "sabit çarpan bu aralıkta ne kadar?". İlk soru önbelleği, ikincisi dili ve küçük `n`'i kapsar.
:::

## 12.12 Mülakatta karmaşıklık anlatma protokolü

Mülakatta kod yazmak kadar, karmaşıklığı anlatmak da değerlendirilir. Bu bir konuşma protokolüdür; her adımın bir nedeni var.

1. **Önce kaba çözümü söyle ve karmaşıklığını hesapla.** "İki döngüyle her çifti deneyebilirim; bu `O(n²)`." Kaba çözüm, referanstır (Bölüm 5'teki Adım 3).
2. **Darboğazı göster.** "İç döngüde her seferinde tüm diziyi tarıyorum; bu tarama gereksiz." Darboğazı adlandırmadan iyileştirme yapma.
3. **İyileştirmeyi ve nedenini söyle.** "Tarama yerine bir hash tablosu kullanırsam her arama `O(1)` ortalama olur; toplam `O(n)`." Ortalama mı, en kötü mü, amortize mi olduğunu belirt.
4. **Bellek maliyetini ekle.** "Hash tablosu `O(n)` ek bellek kullanır." Zaman-uzay takasını açıkça yaz.
5. **Girdi kısıtıyla karşılaştır.** Kabaca bir kural: basit işlemler saniyede yaklaşık `10⁸`–`10⁹` olabilir. `n ≤ 10⁵` için `O(n log n)` rahatça yetişir; `O(n²)`, `10¹⁰` işlemle yetişmez. Bu bir kestirimdir; kesin değildir.
6. **Sınır durumlarını söyle.** Boş girdi, tek eleman, tekrarlı değerler, taşma ihtimali.

Bu protokolü bir konuşmada görelim:

> Aday: Kaba çözüm her çifti denemek; bu `O(n²)`. `n` en fazla `10⁵` olduğu için bu yetmez. Gereksiz olan, her aday için tüm diziyi taramam. Bir tabloda gördüğüm değerleri tutarsam her arama ortalama `O(1)` olur, toplam `O(n)` ve ek bellek `O(n)`. Boş dizi için döngü hiç çalışmaz.

Bu konuşmanın değeri "O(n) buldum" cümlesinde değil, neden o sonuca ulaştığını gösteren adımlarda yatar.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, ★ zorluğundan ★★★'e doğru ilerler. Her örnekte Bölüm 5'teki altı adımı izleyeceğiz. Burada adımlar bir **analiz** problemine uygulanır: çözüm bir algoritma değil, bir büyüme sınıfı ve kanıtıdır. Doğrulama adımında her zaman bir elle iz tablosu kullanacağız.

### Örnek 1 (★): İç içe döngünün sayımı

**Problem:** Aşağıdaki fonksiyonun döndürdüğü `s` değerinin `n` cinsinden formülünü ve Big-O sınıfını bul. Fonksiyon iki bölümden oluşur: `n(n−1)/2` gövdeli bağımlı bir döngü ve `n` gövdeli basit bir döngü.

```python
def sayac_b(n):
    s = 0
    for i in range(n):
        for j in range(i):
            s += 1
    for k in range(n):
        s += 1
    return s
```

**Adım 1 — Anla.** Girdi tamsayı `n ≥ 1`, çıktı `s`. `s`'nin kaç kez arttığını saymak istiyoruz. Kenar durum: `n = 1` (iç döngü hiç çalışmaz, ikinci döngü bir kez çalışır). Büyüme sınıfını istiyoruz, tam formülü de isteyebiliriz.

**Adım 2 — Örnekle.** `n = 3` için dış döngü `i = 0, 1, 2`'dir. İç döngü `i` kez çalışır: `0 + 1 + 2 = 3`. İkinci döngü `3` kez. Toplam `6`. Elle sayıp görelim; sonuç da bu.

**Adım 3 — Kaba çöz.** Her `i` için iç döngünün kaç kez çalıştığını topla: `Σ_{i=0}^{n−1} i = n(n−1)/2`. Üstüne `n` eklenir. Bu bir "toplamı formülle yazmak" yaklaşımıdır, adım adım sayım değildir.

**Adım 4 — Örüntü.** Bağımlı döngü (`j < i`) klasik `1 + 2 + ... + (n−1)` toplamıdır; kapalı formu `n(n−1)/2`dir. Bu örüntü, Bölüm 12.5'te gördüğümüz bağımlı döngü kalıbıdır.

**Adım 5 — İyileştir.** Büyüme sınıfı için sabitler atılır: `n(n−1)/2 + n = (n² + n)/2`, yani `Θ(n²)`. Burada iyileştirme, daha sıkı bir sınır değil, gereksiz terimleri atmaktır.

**Adım 6 — Doğrula.** Her `n` için formülü fonksiyonun gerçek çıktısıyla karşılaştır:

| n | iç döngü n(n−1)/2 | dış döngü n | toplam | (n² + n)/2 |
|---|---|---|---|---|
| 1 | 0 | 1 | 1 | 1 |
| 2 | 1 | 2 | 3 | 3 |
| 3 | 3 | 3 | 6 | 6 |
| 4 | 6 | 4 | 10 | 10 |
| 5 | 10 | 5 | 15 | 15 |

Her satırda sütunlar tutuyor. Yani `s(n) = (n² + n)/2 = Θ(n²)`.

**Bunu AI'sız yazabilir misin?** Bu fonksiyonun döngü gövdesini `s += i` ile değiştirirsen toplam ne olur? Kâğıtta `Σ i` formülünü kurup, `n = 4` için elle hesapla ve sonucu kodla karşılaştır.

### Örnek 2 (★★): Çoklu pop yığınının amortize analizi

**Problem:** Bir yığında üç işlem olsun: `push(x)`, `pop()` ve `multipop(k)` (en fazla `k` elemanı çıkarır, yığın boşsa durur). Bir işlem dizisinin toplam maliyeti `O(n)` ise, her işlemin amortize maliyeti nedir?

```python
class YiginCokPop:
    def __init__(self):
        self.veri = []
    def push(self, x):
        self.veri.append(x)
        return 1
    def multipop(self, k):
        c = 0
        while self.veri and c < k:
            self.veri.pop()
            c += 1
        return c
```

**Adım 1 — Anla.** Girdi bir işlem dizisi, çıktı toplam maliyet. Tek bir `multipop` `O(n)` olabilir (tüm yığını boşaltır). Soru, bunun uzun vadede ne kadar pahalı olduğunu bilmek.

**Adım 2 — Örnekle.** Dört `push`, sonra `multipop(3)`: `multipop` üç pop yapar, maliyet 3. Sonra `multipop(10)` kalan tek elemanı çıkarır, maliyet 1. Tek tek bakınca pahalı görünen `multipop`, aslında önceki `push`'ların bıraktığı iş birikimini boşaltıyor.

**Adım 3 — Kaba çöz.** Her işlemin en kötü maliyetini topla: `n` işlemin toplamı `O(n²)` gibi görünür (her `multipop` `O(n)`). Bu bir üst sınırdır ama gereğinden kötüdür.

**Adım 4 — Örüntü.** Her eleman en fazla bir kez çıkarılabilir, ve bir kez yığına girer. Bu, potansiyel yönteminin tipik örüntüsüdür: potansiyel = yığındaki eleman sayısı. Her `push` potansiyeli 1 artırır; her `pop` potansiyeli 1 azaltır.

**Adım 5 — İyileştir.** Amortize maliyetleri tanımla. `push` için gerçek 1, `ΔΦ = +1`, amortize `2`. `multipop(k)` için gerçek `c` (çıkarılan eleman sayısı), `ΔΦ = −c`, amortize `c − c = 0`. Yani `push` 2, `multipop` 0; her ikisi de sabit.

**Adım 6 — Doğrula.** Aşağıdaki dizi için gerçek maliyet, potansiyel ve amortize maliyeti kodla hesapladık (`Φ` = yığın boyu):

| işlem | gerçek c | Φ önce | Φ sonra | amortize = c + ΔΦ |
|---|---|---|---|---|
| push(1) | 1 | 0 | 1 | 2 |
| push(2) | 1 | 1 | 2 | 2 |
| push(3) | 1 | 2 | 3 | 2 |
| push(4) | 1 | 3 | 4 | 2 |
| multipop(3) | 3 | 4 | 1 | 0 |
| push(5) | 1 | 1 | 2 | 2 |
| multipop(10) | 2 | 2 | 0 | 0 |

Toplam gerçek maliyet `10`, toplam amortize maliyet `10`. Teorem `Σ ĉ = Σ c + Φ_son − Φ_ilk` der; `Φ_son = Φ_ilk = 0` olduğundan iki toplam eşittir. Tek bir `multipop` `O(n)` olabilir, ama her işlemin amortize maliyeti sabittir.

**Bunu AI'sız yazabilir misin?** `multipop` yerine `pop`'u her seferinde bir eleman için çağıran bir döngü yaz ve toplam maliyeti hesapla. Hangi durumda dizinin uzunluğu ile toplam maliyet arasında bir fark kalır?

### Örnek 3 (★★): Tournament ile maksimum ve yinelenen bağıntı

**Problem:** `n = 2^k` elemanlı bir dizinin maksimumunu, diziyi ikiye bölüp iki yarının maksimumlarını karşılaştırarak bul. Karşılaştırma sayısı `T(n)` için bağıntıyı kur ve çöz.

```python
def maks_bol(a, lo, hi, sayac):
    if hi - lo == 1:
        return a[lo]
    orta = (lo + hi) // 2
    sol = maks_bol(a, lo, orta, sayac)
    sag = maks_bol(a, orta, hi, sayac)
    sayac[0] += 1
    return sol if sol >= sag else sag
```

**Adım 1 — Anla.** Girdi dizi ve sınırlar, çıktı maksimum. Ölçülen şey karşılaştırma sayısı. Taban durum tek eleman: karşılaştırma yok.

**Adım 2 — Örnekle.** `[3, 9, 1, 7, 4, 8, 2, 6]` dizisi için `9` bulunur. Özyinelemenin yaptığı karşılaştırmalar sırayla: `(3,9)`, `(1,7)`, `(9,7)`, `(4,8)`, `(2,6)`, `(8,6)`, son olarak `(9,8)`. Toplam 7 karşılaştırma. `n = 8` için `n − 1 = 7`.

**Adım 3 — Kaba çöz.** Her elemanı mevcut maksimumla karşılaştırmak: `n − 1` karşılaştırma. Bu zaten doğrusal; bağıntı yöntemine ihtiyaç yok gibi görünür. Ama bunun ne kadar iyi olduğunu bağıntı ile kanıtlamak, yöntemi öğretir.

**Adım 4 — Örüntü.** Bağıntı: `T(n) = 2T(n/2) + 1`, `T(1) = 0`. Bu, Master Teoremi'nin biçimine uyar: `a = 2`, `b = 2`, `c = 1`, `f(n) = 1 = O(n^(1−ε))` (`ε = 1` alarak `n⁰`). Durum 1: `T(n) = Θ(n)`.

**Adım 5 — İyileştir.** Master Teoremi'ne gerek kalmadan, özyineleme ağacında her seviye sabit sayıda karşılaştırma yapar ve seviyeler bir artar. Toplam `1 + 2 + 4 + ... + n/2 = n − 1`. Yani tam olarak `n − 1` karşılaştırma; bu, en iyi olası sınırdır (her eleman en az bir kez karşılaştırılmalı).

**Adım 6 — Doğrula.** `n = 8` için seviye seviye karşılaştırma sayısı, kodun sayacıyla birebir eşleşir:

| seviye | düğüm sayısı | düğüm başına karşılaştırma | seviye toplamı |
|---|---|---|---|
| 0 (kök, aralık 0–8) | 1 | 1 | 1 |
| 1 (aralık 0–4, 4–8) | 2 | 1 | 2 |
| 2 (dört aralık) | 4 | 1 | 4 |
| 3 (yapraklar) | 8 | karşılaştırma yok | 0 |
| toplam | | | 7 = n − 1 |

Kodun bu dizi için sayacı `7` döndürdü ve `max` doğruydu. `n = 1000` ve `n = 1024` için de sayaç `n − 1` çıktı. Sonuç, `T(n) = n − 1 = Θ(n)`.

**Bunu AI'sız yazabilir misin?** Aynı bağıntıyı `n` tek bir sayı olmayan bir diziye (ör. `n = 10`) uyarladığında ne olur? `T(n) = T(⌊n/2⌋) + T(⌈n/2⌉) + 1` biçimini yaz ve `n = 10` için elle hesapla; bu, `n − 1` sonucunu veriyor mu?

### Örnek 4 (★★★): Heapify'ın O(n) olduğunun kanıtı

**Problem:** Bölüm 10.7'de `n` elemanlı bir dizinin heapify'ının `O(n)` olduğunu söyledik ama kanıtlamadık. `n` elemanlı bir ikili yığında, her düğüm için sift-down'un yaptığı en fazla takas sayısını toplayarak toplam sınırı bul ve `O(n)` olduğunu kanıtla.

**Adım 1 — Anla.** Girdi `n` elemanlı bir dizi; heapify, yapı `n/2`'den `0`'a kadar her iç düğüm için sift-down çağırır. Ölçülen: toplam takas sayısı. Kenar durumlar: `n = 1` (iş yok), `n` ikinin kuvveti olmayan tam ağaçlar.

**Adım 2 — Örnekle.** `n = 15` (tam bir yığın, yükseklik 3). Kökün sift-down'u en fazla 3 takas yapabilir; yaprakların hiçbiri takas yapmaz. Ara düğümler arada bir yer alır.

**Adım 3 — Kaba çöz.** Her düğüm için sift-down maliyeti `O(log n)`, düğüm sayısı `n/2`. Toplam `O(n log n)`: bu bir üst sınırdır ama gereğinden kötüdür; heapify'ı `n` kez ekleme ile yapmak da aynı sınıra gelir.

**Adım 4 — Örüntü.** Yüksekliği `h` olan düğümlerin sayısı en fazla `⌈n/2^(h+1)⌉`dir (CLRS'deki sayım lemması). Yüksekliği `h` olan bir düğümün sift-down maliyeti en fazla `h`'dir. Yani toplam, her yükseklik için `h · n/2^(h+1)` terimlerinin toplamıdır. Çarpan `1/2^h` hızla küçülür ve `h` yalnızca lineer büyür; bu seriyi sınırlamak mümkündür.

**Adım 5 — İyileştir.** Seriyi açıkça sınırla: `Σ_{h≥0} h/2^h = 2` (standart geometrik-aritmetik seri). Böylece toplam `≤ n · (1/2) · Σ h/2^h = n · (1/2) · 2 = n`. Heapify `O(n)`dir. Naif `O(n log n)` tahminimiz, en kötü her düğümün yükseklik kadar takas yaptığını varsayan gevşek bir sınırdı; yaprakların çoğu yükseklik 0'dadır.

**Adım 6 — Doğrula.** Perfect bir ağaçta (`n = 2^(H+1) − 1`) yüksekliği `h` olan düğüm sayısı tam olarak `2^(H−h)`dir. Seviye tablosu:

| h | düğüm sayısı 2^(H−h) | düğüm başına üst sınır h | katkı h · 2^(H−h) |
|---|---|---|---|
| 0 | 8 | 0 | 0 |
| 1 | 4 | 1 | 4 |
| 2 | 2 | 2 | 4 |
| 3 | 1 | 3 | 3 |
| toplam | | | 11 (n = 15) |

`H = 3` için toplam 11 ≤ 15 = n. Aynı hesap `H = 4` (`n = 31`) için 26, `H = 10` (`n = 2047`) için 2036 verir; oran `toplam/n` 1'e yaklaşır, yani sınır `n`'dir. Gerçek takaslar bu üst sınırın altındadır: rastgele girdilerde `n = 1000`, `10 000` ve `100 000` için takas/n değerleri sırasıyla 0,722, 0,741 ve 0,743 çıktı. Şekil 12.9, perfect ağaçtaki seviye katkılarını gösterir: her seviye kendi içinde küçülür ve toplam `n`'i aşmaz.

![Şekil 12.9: Heapify'ın seviye katkıları (H = 10, n = 2047). Yükseklik 1 ve 2 en büyük katkıyı verir; sonra katkı hızla düşer. Toplam 2036, yani n'den küçük.](gorseller/b12_heapify.png)

**Bunu AI'sız yazabilir misin?** `Σ_{h≥0} h/2^h = 2` eşitliğini kanıtla: `S = Σ h x^h` için `S − xS` hesabı yap, `x = 1/2` koy. Sonra bu kanıtın neden "her düğüm en fazla yükseklik kadar takas yapar" varsayımına dayandığını, ve gerçek takas sayısının neden bundan küçük olduğunu açıkla.

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Ölçüm kodu ve karmaşıklık tahmini, ancak kendi elinle yazdığında gerçekten öğrenilir. Bir ölçüm sonucu beklediğinden farklı çıktığında nedenini bulmak, bu bölümün asıl eğitimidir.
:::

### Proje 1 (★★): Karmaşıklık dedektifi

**Amaç:** Verilen bir fonksiyonun girdi boyutuna göre çalışma süresini ölçen ve log-log eğiminden büyüme sınıfını tahmin eden bir araç yazmak. Araç, 12.10'daki protokolü uygulasın.

**Yapılacak / Beklenen davranış:**

1. Bir `olc(fonk, boyutlar, tekrar)` fonksiyonu yaz. Her `n` için girdi üretici bir fonksiyonla bir test verisi oluştur, `fonk`'u çalıştır ve en iyi süreyi al.
2. Log-log doğrusunun eğimini en küçük kareler ile hesapla ve ekrana yazdır.
3. Eğime göre basit bir sınıflandırma yap: `0,2` altı sabit, `0,8`–`1,2` doğrusal, `1,8`–`2,2` karesel gibi aralıklar kullan. Aralıkları kendi denemelerinle gerekçelendir.
4. Altı bilinen fonksiyonla test et: sabit zamanlı sözlük araması, doğrusal toplam, `sorted`, iç içe karşılaştırma, ikili arama (`bisect`), iki iç içe döngüden oluşan bir üçlü sayaç.

**Önerilen yaklaşım:** Ölçüm için `time.perf_counter()` kullan ve her ölçümü birkaç kez tekrarla. Sabit tohumla (`random.seed(42)`) veri üret, böylece iki koşu arasında veri değişmesin. Doğrusal ve `n log n` farkını görmek için `n`'i en az üç büyüklük mertebesi boyunca değiştir. Sabit yükün küçük `n`'lerde eğimi bozduğunu gözlemlersen, en küçük `n` değerini artır.

**Başarı kriterleri:**

- Altı fonksiyonun en az beşinde tahmin edilen sınıf, beklenen sınıfla eşleşir.
- Her ölçüm için makine bilgisi, Python sürümü ve tohum çıktıda yazılıdır.
- Aynı programın iki koşusunda eğimler `0,05`'ten fazla farklı çıkmaz.
- Sözlük araması için eğimin neden sıfırdan farklı çıktığını önbellek ile açıklayan bir paragraf yazılır.

### Proje 2 (★★★): Büyüme stratejisi simülatörü

**Amaç:** Dinamik dizide kapasite büyüme stratejisinin (`+1`, `×1,5`, `×2`) ekleme başına toplam kopyalama maliyetini simüle etmek ve sonucu amortize analizle karşılaştırmak. Bir de "küçülme" (shrink) stratejisinin neden dikkatli seçilmesi gerektiğini göstermek.

**Yapılacak / Beklenen davranış:**

1. Bir `DinamikDizi` sınıfı yaz. Büyüme çarpanını kurucu parametre olarak al. Ekleme (`ekle`) ve kopyalama sayacı tut.
2. `n = 10³, 10⁴, 10⁵` ekleme için her üç stratejinin toplam kopyalama sayısını ve ekleme başına ortalamasını tablola.
3. `+1` stratejisinin ortalamasının `n` ile doğrusal büyüdüğünü, `×2` stratejisinin ise sabit kaldığını grafikle göster.
4. Küçülme ekle: eleman silindiğinde kapasiteyi yarıya indir. Bir sekanslı ekle-sil-ekle-sil dizisi kur ve her işlemin kopyalama sayısını say. Dolu/boş eşiğini değiştirerek "titreme" (thrashing) davranışını gözlemle.

**Önerilen yaklaşım:** Kopyalama sayacını yalnızca yeniden tahsis sırasında artır; gerçek bellek tahsisi yapmana gerek yok. Küçülme için kapasiteyi yarıya indirmek yerine, boy kapasitenin dörtte birine düştüğünde yarıya indirmek, titreme sorununu nasıl çözdüğünü gözlemle. Sonucu amortize potansiyel `Φ` ile açıklamaya çalış: ekleme ve silme için ayrı ayrı `Φ` tanımlayabilir misin?

**Başarı kriterleri:**

- `+1` stratejisi için `n = 10⁵`'te ekleme başına ortalama kopyalama `n/2`'ye yakın çıkar; `×2` için `2`'nin altındadır.
- Titreme senaryosunda, eşik seçimini yanlış yaptığında toplam kopyalama sayısının `O(n)`'den `O(n²)`'ye çıktığını gösteren bir tablo vardır.
- Her ölçüm için tohum ve test dizisi yazılıdır; kod WSL içinde `-fsanitize=address,undefined` ile de çalıştırılır (C kullanırsan).

### Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kendin düşün, sonra kâğıtta analiz yap, en son gerekirse ölçümle doğrula.

1. ★ `for (i = n; i > 1; i /= 3)` döngüsünün tur sayısını `n` cinsinden bul. Tabanın büyüme sınıfına etkisini açıkla.
2. ★ `for i in 1..n` ve `for j in 1..n` iç içe döngülerinde yalnızca `i·j ≤ n` olduğunda gövde çalışsın. Gövde sayısını `Σ ⌊n/i⌋` olarak yaz ve büyüme sınıfını söyle. (Mülakat)
3. ★★ Bir `f(n) = f(n−1) + f(n−2)` özyinelemesinin (naif Fibonacci) neden üstel büyüdüğünü, çağrı ağacının seviyelerini sayarak açıkla. Bu yapıyı Bölüm 16'daki dinamik programlama ile nasıl hızlandırırsın? (Mülakat)
4. ★★ `T(n) = 3T(n/3) + n` bağıntısını Master Teoremi ile çöz; hangi durumda olduğunu ve `c` değerini belirt.
5. ★★ `T(n) = 4T(n/2) + n` ve `T(n) = 4T(n/2) + n²` bağıntılarını karşılaştır. Hangisinin daha hızlı büyüdüğünü ve neden olduğunu Master Teoremi'nin `c` değeriyle açıkla. (Mülakat)
6. ★★ Sıralı olmayan bir dizide iki elemanın toplamının `k` olduğu bir çift olup olmadığını sor. Naif çözümün ve sıralama + iki işaretçi çözümünün karmaşıklığını karşılaştır. (Mülakat)
7. ★★ Dinamik dizi büyüme çarpanı `1,5` ise, amortize maliyetin sabit kalması için potansiyel `Φ = c·boy − kapasite` biçimindeki bir fonksiyonun `c` katsayısını bul.
8. ★★ Sıralı bir dizide tekrar eden değerleri yerinde silen algoritmanın zaman ve uzay karmaşıklığını yaz. Yardımcı bellek kullanıp kullanmadığını açıkla. (Mülakat)
9. ★★★ `Σ_{i=1}^{n} ⌊n/i⌋ = Θ(n log n)` olduğunu kanıtla. İpucu: harmonik toplamı `n · Hₙ` ile sınırla, `⌊x⌋ ≤ x` ve `x − 1 < ⌊x⌋` kullan. (Mülakat)
10. ★★★ Bağlı listede birleştirmeli sıralamanın (merge sort) yardımcı belleğinin neden `O(1)` yapılabildiğini, dizi sürümünün ise `O(n)` gerektirdiğini açıkla.
11. ★★★ Her `push`, `pop` ve `min` işleminin `O(1)` olduğu bir yığın tasarla. Min'i tutmanın bellek maliyeti nedir, bu maliyet hangi durumda kabul edilemez hâle gelir? (Mülakat)
12. ★★★ Bir min-heap'te bir elemanın değerini azaltmak (decrease-key) neden en kötü durumda `O(log n)`'dir? Değeri artırmakta ise durum nasıldır? Bölüm 10.7'deki sift-up ve sift-down'u kullanarak açıkla.

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir kaynağı okuyacaksın: CPython 3.12.10'un standart kütüphanesindeki `bisect.py` dosyası. Dosya, GitHub'daki `python/cpython` deposunun `v3.12.10` etiketinden indirildi ve yerel Python 3.12.10 kurulumundaki `Lib\bisect.py` ile birebir aynı olduğu doğrulandı. Aşağıdaki kesitlerde docstring'ler, yorumlar ve `key` parametresi için olan dallar çıkarılmıştır; kalan satırlar kaynaktan birebir alınmıştır.

Önce ikili arama yapan `bisect_right`:

```python
def bisect_right(a, x, lo=0, hi=None, *, key=None):
    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    if key is None:
        while lo < hi:
            mid = (lo + hi) // 2
            if x < a[mid]:
                hi = mid
            else:
                lo = mid + 1
    return lo
```

Her turda aralık ikiye bölünür: `lo` ya da `hi` değişir. Aralık uzunluğu `n`'den başlar ve her turda kabaca yarıya iner; tur sayısı `⌈log₂(n + 1)⌉` civarındadır. Bu, Bölüm 5'teki ikili aramanın kendisidir; kaynak bunu bir `while` döngüsüyle yazıyor.

Sonra ekleme yapan `insort_right`:

```python
def insort_right(a, x, lo=0, hi=None, *, key=None):
    if key is None:
        lo = bisect_right(a, x, lo, hi)
    a.insert(lo, x)
```

Bu iki fonksiyonu birlikte okuduğunda önemli bir ayrım görürsün: yer bulmak `O(log n)`, ama elemanı yerleştirmek `a.insert(lo, x)` çağrısıyla yapılır ve bu çağrı, `lo`'dan sonraki elemanları bir kaydırır. Liste üzerinde bu kaydırma `O(n)`dir. Yani `insort_right`'ın toplam maliyeti `O(log n + n) = O(n)`dir. Arama ile ekleme aynı fonksiyonda olsa da karmaşıklıkları aynı değildir.

Son olarak, dosyanın sonunda şu bloğu bulursun:

```python
try:
    from _bisect import *
except ImportError:
    pass
```

Bu blok, Python'daki `bisect_right` ve `insort_right` tanımlarının C ile yazılmış `_bisect` modülüyle üzerine yazıldığını söyler. Yani gerçek programda çoğunlukla bu Python kodu değil, C gerçeklemesi çalışır. Bu bölümde C gerçeklemesinin ayrıntılarını doğrulamadık; yalnızca Python kaynağının algoritmasını ve karmaşıklığını okuduk.

**Sorular — cevaplamadan geçme:**

1. `bisect_right` döngüsünde `hi = mid` ve `lo = mid + 1` neden iki farklı yönde ilerler? `x` eşit olduğunda hangi yöne gidilir ve bu, "sağdan ekleme" anlamına nasıl karşılık gelir?
2. Dizi `n = 1000` elemanlı olsun. Döngü en fazla kaç tur çalışır? Cevabını `⌈log₂(n + 1)⌉` ile karşılaştır ve farkın nedenini açıkla.
3. `insort_right` içinde `a.insert(lo, x)` çağrısının `O(n)` olduğunu nasıl gösterirsin? Bir Python listesinin bellek düzenini (Bölüm 7'deki dinamik dizi) düşünerek açıkla.
4. Bu nedenle `insort` ile `n` elemanı sıralı bir listeye eklemek toplamda `O(n²)` iş yapar. Bunu `n` ekleme için kanıtla. Aynı işi yapmanın daha hızlı bir yolu var mı?
5. `bisect_left` ile `bisect_right` yalnızca eşitlik durumunda hangi konumu verir? Bu fark, Bölüm 14'teki alt sınır ve üst sınır aramasının temelidir; neden?
6. `_bisect` C modülü bu algoritmanın yerine geçerse karmaşıklık değişir mi? Hangi değişir, hangisi değişmez? Sabit çarpan açısından ne beklersin ve bunu nasıl ölçerdin?

## Bölüm Özeti

Bu bölümde algoritmaların ne kadar hızlı olduğunu değil, girdi büyüdükçe nasıl büyüdüğünü ölçmeyi öğrendik:

- **RAM modeli ve adım sayma**, süreyi donanımdan bağımsız bir adım sayısına çevirir. Model önbelleği görmez; bu yüzden tahmindir.
- **O, Ω, Θ** tanımları sabitler ve eşikle biçimselleşir. Θ hem üst hem alt sınırdır. O, durum analizi değildir.
- **Büyüme kuralları:** toplam ve çarpım kuralı, baskın terim, log tabanının önemsizliği. `4ⁿ`'nin `2ⁿ`'den farklı olduğunu unutma.
- **Döngü analizi:** iç içe, bağımlı, logaritmik ve harmonik (`n log n`) kalıpları; sayaçlı C programı formüllerle doğrulandı.
- **En iyi, en kötü, ortalama** durum girdiye bağlıdır. Doğrusal arama `Θ(1)`, `Θ(n)`, `Θ(n)` verir; naif quicksort sıralı girdide `Θ(n²)`dir.
- **Amortize analiz** toplam, muhasebe ve potansiyel yöntemleriyle yapılır. Dinamik dizi ve çoklu pop yığını bunun örnekleridir. Amortize garanti bir ortalama varsayımı değildir.
- **Master Teoremi** `T(n) = aT(n/b) + f(n)` biçimini üç durumla çözer; uygulanamayan bağıntılar da vardır.
- **Deneysel doğrulama:** log-log eğimi üssü tahmin eder. Sözlük aramasında eğim 0,34 çıktı; bu önbellek etkisidir.
- **Big-O'nun yanılttığı yerler:** sabit çarpan, önbellek düzeni, dil ve girdi dağılımı.

**Sonraki bölümde:** Bu bölümde ölçtüğümüz büyüme sınıflarının en önemli uygulamalarından biri sıralamadır. Bölüm 13'te bubble, selection, insertion, merge, quick, heap, counting ve radix sıralamalarını göreceğiz. Her birinin karmaşıklığını bu bölümün araçlarıyla çözeceğiz; quicksort'un ortalama `Θ(n log n)` ve en kötü `Θ(n²)` olmasının nedenini ve kararlılık (stability) kavramını ayrıntılı işleyeceğiz.

::: mulakat
Klasik sorular, hemen cevaplamaya çalışma; her birini birkaç dakika düşün:

1. Bir `for` döngüsü `i` değişkenini `i *= 2` ile artırıyor ve `i < n` iken çalışıyor. Döngü kaç kez çalışır ve neden? Aynı döngü `i += 2` ile yazılırsa sınıf değişir mi?
2. Big-O ile en kötü durum aynı şey midir? Bir algoritmanın en kötü durum süresi `O(n²)`, en iyi durum süresi `Θ(1)` olabilir mi? Bu iki bilgiyi birlikte nasıl ifade edersin?
3. Dinamik diziye eleman eklemek amortize `O(1)`, ama tek bir ekleme `O(n)` olabilir. Bu bir gerçek zamanlı sistemde neden sorun olabilir ve bunu nasıl çözersin?
4. Master Teoremi `T(n) = 2T(n/2) + n log n` için neden doğrudan uygulanamaz? Hangi genişletilmiş biçim gerekir?
5. Bir ağacın gezinmesi `O(n)` sürer. Özyinelemeli gezinmenin uzay maliyeti neden ağacın şekline bağlıdır? Dengeli ve dengesiz ağaçlar için ne olur?
6. Bir hash tablosunda ortalama `O(1)` arama varsa, neden her zaman hash tablosu kullanılmaz? Ortalama ve en kötü durum arasındaki fark burada neden önemlidir?
7. Bir algoritmanın süresini ölçtüğünde log-log eğimi 1,2 çıktı. Bu, algoritmanın `O(n log n)` olduğunu kanıtlar mı? Hangi ek bilgi ve hangi ölçümler gerekir?
8. Mülakatta "bu çözüm O(n²) ama n ≤ 10⁵" diye bir kısıt görürsen ne yaparsın? Bu kısıt, hangi çözüm sınıflarını elemene yardımcı olur?
:::
