## 16.1 İki koşul: örtüşen alt problemler ve optimal alt yapı

Bir problem DP ile çözülebilmek için iki koşulu birlikte sağlamalıdır. Birincisi **örtüşen alt problemler** (overlapping subproblems): aynı alt problem, çözümün farklı dallarında tekrar tekrar ortaya çıkar. İkincisi **optimal alt yapı** (optimal substructure): büyük problemin en iyi çözümü, alt problemlerin en iyi çözümlerinden kurulabilir.

Birinci koşulu görmek için Bölüm 15'teki ağaca tekrar bakalım. Aşağıdaki şekil `fib(5)` çağrısının ağacını gösteriyor. Düğümlerdeki sayı `n`'dir; kırmızı düğümler birden çok kez çağrılır.

![Şekil 16.1: fib(5) özyineleme ağacı. Kırmızı düğümler (fib(3) ve fib(2)) birden çok kez hesaplanır; ağaçta toplam 15 çağrı vardır, ama farklı alt problem sayısı yalnızca 6'dır.](gorseller/b16_fib_agac.png)

Bu ağaç yanlış bir şey yapmıyor; her çağrı doğru cevabı döndürüyor. Sorun verimde. Ağacı büyütmek, aynı düğümü her seferinde yeniden hesaplamak demek. Eğer her alt problemi yalnızca bir kez hesaplar ve sonucunu saklarsak, `n = 5` için 6 hesap yeter. Bunu Bölüm 16.3'te yapacağız.

Şimdi ikinci koşulu ele alalım. Optimal alt yapıya sahip bir problemde şu kural geçerlidir: büyük problemin en iyisini, alt problemlerin en iyilerini birleştirerek bulabilirsin. En kısa yol problemi bu koşulu sağlar. A'dan C'ye giden en kısa yol bir B noktasından geçiyorsa, A'dan B'ye giden parça da mutlaka A-B arasının en kısa yoludur. Aksi halde o parçayı değiştirip daha kısa bir yol bulurduk.

En uzun basit yol problemi ise bu koşulu sağlamaz. "Basit" yol, hiçbir köşeyi iki kez kullanmayan yoldur. Üç köşeli bir üçgen düşünelim: köşeler `s`, `v`, `t` ve her biri diğer ikisine bağlı. `s`'den `t`'ye en uzun basit yol `s - v - t`'dir; uzunluğu 2'dir. Şimdi bu yolu ortadaki `v` köşesinden bölelim. `s`'den `v`'ye en uzun basit yol `s - t - v`'dir (uzunluk 2) ve `v`'den `t`'ye en uzun basit yol `v - s - t`'dir (uzunluk 2). İki parçayı birleştirirsek `s - t - v - s - t` elde ederiz; bu yol `s`, `t` köşelerini iki kez kullanır, yani basit değildir. Alt problemlerin en iyileri birleşmiyor, çünkü parçalar birbirinin köşelerini kullanıyor.

Bu yüzden DP'nin uygulanabilmesi için alt problemlerin en iyi çözümlerinin birleşip geçerli bir çözüm verebilmesi gerekir. En uzun basit yol problemi genel grafta NP-zordur ve bilinen kesin çözümler üstel zaman tutar; yani DP'nin "tablo" fikri burada işe yaramaz. Koşul sağlanmadığında tabloya dökmek yanlış sonuç verir; önce koşulu kanıtla, sonra tabloyu kur.

## 16.2 DP tasarım protokolü: altı soru

Her DP çözümü, sırası değişmeyen altı soruya cevap verir. Bu sorular bir hile değil, bir düşünme sırasıdır. Çoğu hata, bu sıradan birini atlamaktan çıkar.

| Adım | Soru | Merdiven örneği (1 ya da 2 basamak) |
|---|---|---|
| 1. Durum | Hangi sayı, cevabın tamamını özetler? | `dp[i]`: `i`. basamağa çıkmanın yol sayısı |
| 2. Geçiş | `dp[i]`'yi daha küçük durumlardan nasıl kurarsın? | `dp[i] = dp[i-1] + dp[i-2]` |
| 3. Taban | En küçük durumlar nedir, değerleri ne? | `dp[0] = 1`, `dp[1] = 1` |
| 4. Sıra | Durumlar hangi sırayla hesaplanmalı? | `i` = 2'den `n`'ye, artan |
| 5. Cevap | Cevap tablonun neresinde? | `dp[n]` |
| 6. Maliyet | Durum sayısı × geçiş maliyeti nedir? | `n` durum × 2 geçiş = `O(n)` |

İlk adımın en önemli olduğunu vurgulamak gerekir. Durumu bir cümleyle tanımlayamıyorsan, tabloda neyi sakladığını bilmiyorsun demektir. "`dp[i]`, `i`. basamağa çıkmanın yol sayısıdır" cümlesi, sonraki her adımın anlamını belirler. Bu cümleyi yazmadan kod yazmaya başlamak, DP'de en sık yapılan hatadır.

İkinci adım, durumu alt durumlara bağlayan bağıntıdır. Merdivende son adım ya 1 ya da 2 basamaklıktır. Son adım 1 basamaklıksa `i-1`'e kadar olan yollar bir kez daha sayılır; son adım 2 basamaklıksa `i-2`'ye kadar olan yollar. Toplam `dp[i-1] + dp[i-2]`'dir. Bu bağıntı Fibonacci dizisiyle aynıdır; Bölüm 16.6'da bunun sebebini göreceğiz.

Üçüncü ve dördüncü adımlar birlikte düşünülmelidir. Bağıntı `dp[i]` için `dp[i-1]` ve `dp[i-2]`'ye ihtiyaç duyuyorsa, bu değerler `dp[i]`'den önce hesaplanmalıdır. Taban durumlar, bağıntının dayandığı başlangıç değerleridir. Yanlış taban durum, bütün tabloyu yanlış yapar; bu yüzden Bölüm 16.6'daki sayma problemlerinde taban durumların anlamını ayrıca açıklayacağız.

Beşinci adımda cevabın nerede olduğunu bilmek gerekir: son hücrede mi, tablonun en büyük değerinde mi, yoksa bir satırın içinde mi? En uzun artan altdizi (LIS) bunun iyi bir örneğidir. `dp[i]`, `a[i]`'de biten en uzun artan altdizinin uzunluğu olsun. Dizinin sonu her zaman en uzun altdizinin sonu değildir, çünkü son eleman küçük olabilir. Cevap bu yüzden `dp[n-1]` değil, tüm `dp` değerlerinin en büyüğüdür. Altıncı adımda maliyeti ölçmek, algoritmanın gerçekten pratik olup olmadığını söyler. Durum sayısı çoğu zaman tablonun boyutuna eşittir; geçiş maliyeti ise bağıntıdaki `min`, `max` ya da toplamın kaç terimli olduğudur.

Bu protokol sayma ve en iyileme problemlerinde aynıdır. Fark yalnızca geçişte ortaya çıkar: sayma problemlerinde geçiş toplamdır, en iyileme problemlerinde `min` ya da `max`. Bölüm 16.6'da bu farkı para bozma problemiyle gösteriyoruz.
