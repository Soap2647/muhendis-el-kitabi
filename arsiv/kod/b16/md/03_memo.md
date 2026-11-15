## 16.3 Memoization ve tabulation: üstten alta mı, alttan üste mi?

Tekrar eden alt problemleri bir kez hesaplamanın iki yolu vardır. **Memoization** (not alma, ezberleme) üstten alta çalışır: özyinelemeli fonksiyon bir alt problemi ilk kez çözdüğünde sonucu bir önbelleğe yazar, sonraki çağrılarda hesap yapmadan döndürür. **Tabulation** (tablo doldurma) alttan üste çalışır: taban durumlardan başlayıp tabloyu bir döngüyle sırayla doldurur, özyineleme kullanmaz.

İki yöntem aynı sonucu verir; farkı dört boyutta görmek önemlidir. Önce kavramı tek bir noktada gösterelim. Aşağıdaki şekil, memo ile `fib(5)`'in alt problem bağımlılıklarını gösteriyor. Her düğüm tek bir kez hesaplanır; ok, bir düğümün hangi düğüme ihtiyaç duyduğunu gösterir.

![Şekil 16.2: Memo'nun alt problem DAG'ı. fib(n), fib(n-1) ve fib(n-2) değerlerine ihtiyaç duyar; her düğüm bir kez hesaplanır. Ağaçtaki 15 çağrı yerine 6 hesap yapılır.](gorseller/b16_fib_dag.png)

DAG, yönlü çevrimsiz graf (directed acyclic graph) demektir. Burada "çevrimsiz" önemlidir: bir alt problem kendisine bağlı olamaz, yoksa tanımsız bir hesap olurdu. DP'nin her çözümünde bağımlılıklar bu şekilde bir DAG oluşturur; hesaplama sırası, DAG'ın topolojik sıralamasıdır. Bölüm 17'de topolojik sıralamayı grafların içinde ayrıntılı göreceğiz.

Aşağıdaki program üç yöntemi yan yana koyar: naif özyineleme, memo ve tablo. Program her üç yöntemin de aynı değeri verdiğini `assert` ile doğrular; ardından çağrı sayılarını yazdırır.

Kodun ilk yarısı üç fonksiyonu tanımlar. `fib_memo`'nun üstündeki `@functools.cache` süsleyicisi (decorator), Python'un standart kütüphanesindeki bir önbellektir; Python 3.9'dan beri bulunur ve `lru_cache(maxsize=None)` ile aynı davranışa sahiptir. Önbelleğe yazılan her sonuç bir daha hesaplanmaz; bu yüzden fonksiyonun gövdesi her `n` için bir kez çalışır.

{{KOD:fib_olcum.py:1:28}}

Programın ikinci yarısı ölçümleri yapar. `sayac` sözlüğü, naif fonksiyonun her çağrısında, memo fonksiyonunun ise yalnızca gerçek hesapta arttırılır. Tablo sürümünde bir sayaç yoktur; döngü zaten `n` adımdır.

{{KOD:fib_olcum.py:29:55}}

Programı çalıştırdık. Çıktıdaki `naif_cagri` ile `memo_hesap` sütunlarını karşılaştır:

{{TERM}}
python fib_olcum.py ||| python fib_olcum.py
{{/TERM}}

Sonuçlar iki şeyi açıkça gösteriyor. Naif yöntemde çağrı sayısı büyüklük olarak Fibonacci sayısının kendisine yakındır: `n = 30` için 2692537 çağrı, yani `fib(30)` değerinin (832040) üç katından fazla. Bu, `2 * fib(n+1) - 1` formülüyle uyumludur; üstel büyüme buradan gelir. Memo sürümünde gerçek hesap sayısı yalnızca `n + 1`'dir, çünkü `fib(0)`'dan `fib(n)`'e kadar her değer bir kez hesaplanır.

Ölçüm grafiği bu farkı tüm `n` aralığında gösterir. Dikey eksen logaritmiktir; naif eğri bir doğru gibi görünüyorsa, bu üstel büyümenin işaretidir.

![Şekil 16.3: Fibonacci için naif çağrı sayısı (kırmızı) ve memo hesap sayısı (mavi), n = 1..25. Dikey eksen logaritmik; naif büyüme bir doğru gibi, memo ise neredeyse düz kalır.](gorseller/b16_olcum.png)

Memo'nun bir bedeli var: özyineleme yığını. `fib_memo(n)` ilk çağrıda `fib_memo(n-1)`'i çağırır, o da `fib_memo(n-2)`'yi; derinlik `n`'e ulaşır. Python'da varsayılan özyineleme sınırı 1000'dir ve programın çıktısındaki iki satır bunu gösteriyor: `n = 900` başarılı oldu, `n = 1200` `RecursionError` verdi. Tabulation'da böyle bir derinlik sorunu yoktur; `fib_tablo(1200)` 251 basamaklı bir sayı üretir ve sorunsuz biter. Python'un büyük tamsayıları otomatik desteklemesi (Bölüm 3) bu programda taşmayı önler, ama C'de bu bedava değildir.

C'de aynı hesap farklı davranır. Aşağıdaki program `fib(92)`'den `fib(94)`'e kadar değerleri 64-bit işaretsiz (`unsigned long long`) tamsayıda hesaplar. İşaretsiz tamsayılarda taşma tanımlı davranıştır: değer 2^64 modülüne göre sarar. İşaretli tamsayıda aynı taşma **tanımsız davranıştır (UB)**: derleyici bunu optimizasyonda kendi lehine kullanabilir, dolayısıyla sonucu garanti edemezsin. Tanımsız davranış her zaman çökme anlamına gelmez; tipik olarak yanlış değer üretir, ama garanti değildir.

{{KOD_C:fib_tasma.c}}

Programı WSL içinde derledik ve çalıştırdık. Windows dosyasına WSL'den `/mnt/c/...` yolu üzerinden erişilir:

{{TERM}}
gcc -O2 -Wall -Wextra -std=c11 fib_tasma.c -o fib_tasma ||| wsl gcc -O2 -Wall -Wextra -std=c11 /mnt/c/Users/merty/AppData/Local/Temp/b16/kod/fib_tasma.c -o /tmp/fibt
./fib_tasma ||| wsl /tmp/fibt
{{/TERM}}

`F(94)` değeri 2^64'ü aştığı için sarmıştır; çıktıdaki `1293530146158671551` gerçek `F(94)` değerinin 2^64 ile bölümünden kalan sayıdır. Bu değer yanlış görünüyor, çünkü yanlıştır, ama bu yanlışlık tanımlı bir sarmadır. İşaretli `long long` ile aynı kodu yazsaydık, `F(93)`'ten sonra UB başlardı ve sonuç hiçbir şekilde güvenilir olmazdı.

Şimdi tablo ile memo arasındaki dört farkı tek bir tabloda toplayalım:

| Özellik | Memoization | Tabulation |
|---|---|---|
| Yön | Üstten alta (özyineleme) | Alttan üste (döngü) |
| Yığın derinliği | En kötü `O(n)` çağrı yığını | Yığın kullanmaz |
| Gereksiz durumlar | Yalnızca ihtiyaç duyulanlar hesaplanır | Tüm tablo hesaplanır |
| Bellek | Önbellek ve yığın birlikte | Tablo; genelde daha az yük |
| Kod | Bağıntıyı doğrudan yazarsın | Sıra ve taban durumlarını sen kurarsın |

"Gereksiz durumlar" satırı önemli bir ayrımdır. Bazı problemlerde yalnızca küçük bir alt küme gerçekten gerekir; örneğin tek bir hedef hücreye giden yolların sayısı. Bu durumda memo yalnızca ulaşılabilir durumları hesaplar, tablo ise hepsini hesaplar. Diğer yandan tablo, hesaplama sırasını açıkça kontrol ettiği için bellek ve önbellek davranışını tahmin etmeyi kolaylaştırır. Pratikte iki yaklaşımı da bilmek gerekir: önce memo ile doğruluğu kontrol et, sonra yığın sorunu veya hız gerekirse tabloya geç.
