
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

Kalan iki kalıp da aynı biçimdedir: logaritmik döngü `i *= 2` ile, harmonik döngü iç döngüde `j += i` ile yazılır. Bu beş fonksiyonu ve üç farklı `n` için çağıran `main`'i derleyip çalıştırdığımızda çıktı şöyle oldu. Derleme WSL içinde yapıldı; Windows'ta MinGW ile de derleyebilirsin, ama sanitizer araçları için WSL gerekir:

```term
$ gcc -O2 -Wall -Wextra -std=c11 sayac.c -o sayac
$ ./sayac
n=   10 tek=   10 ic=     100 bagimli=     45 log=  4 harm=    33
n=  100 tek=  100 ic=   10000 bagimli=   4950 log=  7 harm=   573
n= 1000 tek= 1000 ic= 1000000 bagimli= 499500 log= 10 harm=  8053
```

Çıktıyı formüllerle karşılaştıralım. İç içe döngü `n²` verir: `1000² = 1 000 000`. Bağımlı döngü `n(n−1)/2 = 499 500` verir ve çıktı birebir budur. Logaritmik döngü `⌈log₂ 1000⌉ = 10` verir. Harmonik döngü için `n · Hₙ ≈ 7485`tir; gerçek sayı 8053'tür ve bu, `[n·Hₙ, n·Hₙ + n) = [7485, 8485)` aralığında olduğundan beklenen bir sonuçtur. Asimptotik analizde bu sabit fark önemsizdir.

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

Dinamik dizi için `Φ = 2·boy − kapasite` seçilebilir. Kapasite doluyken değilken ekleme: gerçek maliyet 1, `ΔΦ = +2`, amortize 3. Dolu iken (`boy = kapasite = k`) ekleme: `k` kopyalama artı 1 yazma, gerçek maliyet `k + 1`. Önce `Φ = 2k − k = k`; sonra kapasite `2k`, boy `k + 1` olur ve `Φ = 2(k+1) − 2k = 2`. Yani `ΔΦ = 2 − k` ve amortize maliyet `(k + 1) + (2 − k) = 3`. İki durumda da amortize maliyet 3'tür.

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
