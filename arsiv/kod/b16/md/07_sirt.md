## 16.7 Sırt çantası ailesi: 0/1, sınırsız ve çubuk kesimi

Sırt çantası problemi, DP'nin en çok karşılaşacağın kalıptır. Ortak yapı şudur: bir kapasite (ağırlık, uzunluk, bütçe) var ve her öğenin bir maliyeti ve bir getirisi var. Amaç, kapasiteyi aşmadan en büyük toplam getiriyi bulmaktır. Bu ailenin üyeleri, öğelerin kaç kez kullanılabildiğine göre ayrılır.

Bölüm 16.4'te 0/1 ve sınırsız iki sürümü programda gördük. Burada farkı tabloyla özetleyelim:

| Problem | Her öğe için kısıt | Kapasite döngüsü | Kaba kuvvet |
|---|---|---|---|
| 0/1 sırt çantası | En fazla bir kez | Büyükten küçüğe | `2^n` altküme |
| Sınırsız sırt çantası | Sınırsız kopya | Küçükten büyüğe | Sayı kombinasyonları |
| Çubuk kesimi | Uzunluk parçaları sınırsız | Küçükten büyüğe | Parça bölümleri |

Son satır, sınırsız sırt çantasının farklı bir kılığıdır. Bir çubuğu `n` birim uzunlukta düşün; `k` birimlik parçanın satış fiyatı `fiyat[k]` olsun. Çubuğu parçalara kesmek ve en yüksek geliri elde etmek istiyorsun. Her parça bir "öğe" (ağırlık `k`, değer `fiyat[k]`), toplam uzunluk ise "kapasite"dir. Parçalar sınırsız kez kullanılabilir, çünkü aynı uzunlukta birden fazla parça satabilirsin. Yani çubuk kesimi, sınırsız sırt çantasının tam karşılığıdır.

Protokolü uygulayalım. `dp[u]`, uzunluğu `u` olan çubuğun en yüksek gelirini tutsun. Son parçayı `k` seçersen, kalan `u - k` için en iyi gelir `dp[u - k]`'dır. Bu yüzden `dp[u] = max(fiyat[k] + dp[u - k])` olur, `k` 1'den `u`'ya kadar. Taban durum `dp[0] = 0`'dır: sıfır uzunluk sıfır gelir.

Aşağıdaki program bu bağıntıyı uygular, kaba kuvvetle karşılaştırır ve örnek fiyat tablosu için sonuçları yazdırır. Bu fiyat tablosu, bu alanda sık kullanılan bir örnekle aynıdır (Cormen ve arkadaşlarının algoritma kitabında yer alır).

{{KOD:cubuk.py}}

Programı çalıştırdık:

{{TERM}}
python cubuk.py ||| python cubuk.py
{{/TERM}}

Uzunluk 4 için en iyi gelir 10'dur: çubuğu iki parçaya (`2 + 2`) bölmek `5 + 5 = 10` verir; tek parça ise `9` verir. Uzunluk 8 için cevap 22'dir ve bunu `2 + 6` parçalarıyla elde edersin: `5 + 17 = 22`. Kaba kuvvet, rastgele fiyat tablolarında yaptığı 200 karşılaştırmanın hiçbirinde farklı sonuç vermedi.

Programda bir ayrıntıya dikkat et. Fiyat dizisi `fiyat[k]`, ancak `k` uzunluğu için fiyat tanımlı değilse o parça hiç kesilemez. Bu yüzden döngü üst sınırı `min(u, len(fiyat) - 1)` olarak alındı. İlk sürümde bu sınır yoktu ve rastgele testte `IndexError` aldık; düzeltme, gerçek problemin sınırını kodda açıkça yazmaktı. Bu, DP'de sık yapılan bir hatadır: tablonun ve girdinin boyutlarını birbirinden bağımsız varsaymak.

Son olarak, sınırsız sırt çantasının çalışma zamanına bak. Kapasite döngüsü `W` adım, her adımda `n` eşya; toplam `O(nW)`. Çubuk kesiminde `n` uzunluk, her uzunlukta en fazla `n` parça denenir; toplam `O(n^2)`. Bu, bağıntıdaki iç içe iki döngüden gelir: dış döngü uzunlukta, iç döngü kesim boyunda ilerler.
