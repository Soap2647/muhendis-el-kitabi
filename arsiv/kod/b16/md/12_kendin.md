## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. DP'nin asıl eğitimi, tabloyu kendi elinle kurmak ve kendi hatanı bulmaktır. Bir aracın yazdığı tablo doğru görünse bile, sınır durumlarını (boş girdi, tek eleman, tüm eşitler) sen test etmedikçe bilmiyorsun.
:::

### Proje 1 (★★): Kendi `diff` aracın

**Amaç:** İki metin dosyasını satır satır karşılaştıran ve farkı `+` (eklenen) ve `-` (silinen) satırlarla yazdıran bir komut satırı aracı yazmak. Karşılaştırmanın çekirdeği LCS olacak: ortak satırların en uzun altdizisi, değişmeyen satırları verir; geri kalanlar değişikliktir.

**Yapılacak / Beklenen davranış:**

1. Dosyaların satırlarını oku ve her satırı bir "sembol" olarak ele al. Satır sonu karakterlerini (`\r\n` ve `\n`) önce normalize et; Windows'ta bu fark sahte değişiklik üretir.
2. Satırlar arasında LCS tablosunu doldur ve geri izleyerek ortak satırları bul.
3. LCS'e girmeyen eski satırları `-`, yeni satırları `+` ile yazdır. Sıra, dosyadaki sırayı korumalı.
4. Tek bir dosya boş olabilir; iki dosya da aynıysa çıktı boş olmalı; bir dosya tamamen yeniyse tüm satırlar `+` olmalı.
5. Aynı girdiler için GNU `diff --minimal` ile karşılaştır.

**Önerilen yaklaşım (ipucu, tam çözüm değildir):** Bölüm 16.8'deki LCS tablosunu satırlar üzerinde kur; `a` ve `b` artık karakter değil, satır dizileridir. Geri izlemeyi, yazdırma sırasını koruyacak şekilde yap. Bellek ihtiyacı `O(nm)` satır sayısına bağlıdır; büyük dosyalarda bu bir sorundur. Bu sorunu çözmek için Bölüm 16.5'teki Hirschberg fikrini araştırabilirsin, ama önce küçük dosyalarla doğru çalıştığından emin ol. Tablo değerlerini yazdırıp Bölüm 16.8'deki şekille karşılaştır.

**Başarı kriterleri:**

- 300 satırlık rastgele iki dosyada (tohum `42`), çıkan `+` ve `-` satır sayıları toplamı `diff --minimal` ile aynıdır.
- Boş dosya, tek satırlık dosya ve tamamen aynı dosyalar için çıktı elle beklediğinle birebir eşleşir.
- Çalışma süresi 2000 satırlık dosyada bir saniyenin altındadır (ölç, tahmin etme).
- Kodda tüm tablo bağıntısı tek bir fonksiyonda toplanmıştır ve her satırda ne yaptığını açıklayan bir yorum vardır.

### Proje 2 (★★★): Batarya enerji bütçesi: sırt çantası

**Amaç:** EV Dashboard'a benzer bir sistemde, bir batarya şarjı içinde en çok faydayı sağlayan görev kümesini seçen bir planlayıcı yazmak. Her görevin (sensör okuma, veri gönderimi, ısıtma, kalibrasyon) bir enerji maliyeti ve bir fayda değeri vardır; bütçe bir enerji miktarıdır.

**Yapılacak / Beklenen davranış:**

1. Enerjiyi tam sayı birimlerle (ör. `0.1 Wh`) temsil et; kayan nokta bütçesi DP'de sorun çıkarır.
2. 0/1 sırt çantasıyla her görevin en fazla bir kez çalışmasını sağla. En büyük faydayı ve seçilen görevleri döndür.
3. İkinci bir mod ekle: aynı görev birden fazla kez çalışabilsin (sınırsız sırt çantası). Bu iki modu tek bir programda seçilebilir yap.
4. Bütçe 0 ve görev listesi boş olduğunda sonuç 0 olmalı; hiçbir görev bütçeye sığmıyorsa sonuç 0 ve seçilen görev listesi boş olmalı.
5. 20 görevli bir örnekte kaba kuvvetle (`2^20`, yani bir milyondan fazla altküme; süreyi ölç) karşılaştır.

**Önerilen yaklaşım (ipucu):** Bölüm 16.4'te gördüğün tek boyutlu tabloyla başla; sonra geri kurma gerektiğinde tam tabloya (Bölüm 16.5) geç. Kapasiteyi `W` birim olarak düşün: her enerji birimi bir kapasite birimidir. Sınırsız mod için döngü yönünü değiştirmenin neyi değiştirdiğini kendi testinde göster. Bütçe büyüdüğünde bellek ve süre nasıl büyüyor? Bunu tabloyla ölç.

**Başarı kriterleri:**

- 300 rastgele küçük örnekte (tohum `42`), DP sonucu kaba kuvvetle eşleşir; her iki mod için de.
- Seçilen görev listesinin toplam enerjisi bütçeyi aşmaz ve toplam faydası DP sonucuna eşittir. Bu iki kontrol birbirinden bağımsız yazılmalıdır.
- Bütçe `W = 10^4` birim ve `n = 100` görev için çalışma süresi ölçülmüş ve raporlanmıştır; sonuç "sözde-polinom" tartışmasıyla (Bölüm 16.10) yorumlanmıştır.

### Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kâğıtta düşün; son çare olarak kodla doğrula. Mülakat sorularının bir kısmı ayrıca işaretlidir.

1. ★ `fib(n)`'i yalnızca iki değişkenle, `O(n)` zamanda hesapla. Bu sürüm Bölüm 16.3'teki tablodan hangi açıdan farklıdır? (Mülakat)
2. ★ Merdiven problemini 1, 2 ve 3 basamak atlama için genelleştir. Taban durumlarını yazmadan önce `dp[0]`'ın anlamını bir cümleyle tanımla.
3. ★ Para bozmada en az madeni para sayısını ve bu sayıyı veren madeni paraların listesini geri kur. Tutarın kendisi için birden fazla çözüm varsa hangisini döndüreceğine karar ver ve bunu açıkla. (Mülakat)
4. ★★ 0/1 sırt çantasında yalnızca tek bir satır tutarak en iyi değeri hesaplayabilirsin; ama seçilen eşyaları bu tek satırla geri kuramazsın. Nedenini bir örnekle göster.
5. ★★ Sınırlı sırt çantasında her eşyanın en fazla `k_i` kez alınabildiğini düşün. Eşyayı `k_i` ayrı kopya olarak yazmak yerine, ikilik bölmeyle (1, 2, 4, ... kopya) kaç yeni eşya gerekir? (Mülakat)
6. ★★ Bir `s` dizgisinin en uzun palindrom altdizisinin uzunluğunu, `s` ile `reverse(s)` arasındaki LCS olarak hesapla. Bu eşitliği küçük örneklerde kaba kuvvetle doğrula. (Mülakat)
7. ★★ Edit distance'da yalnızca ekleme ve silme izinli olsun (değiştirme yok). Bu mesafenin LCS ile ilişkisini kur ve `m + n - 2 * LCS` formülünü küçük örneklerde doğrula.
8. ★★ "Ev soygunu" problemini ağaç üzerinde çöz: her ev bir düğüm, komşuluk kenarları ağacın kenarlarıdır. Her düğüm için "alındı" ve "alınmadı" durumlarını tanımla ve bağıntıyı yaz. (Mülakat)
9. ★★ Bir `n × m` ikili matriste yalnızca 1'lerden oluşan en büyük kareyi `O(nm)` ile bul. Bu, Bölüm 16.2'deki altı adımla nasıl eşleşir? (Mülakat)
10. ★★ Bir dizide en uzun bitonik altdizi (önce artan, sonra azalan) uzunluğunu bul. Hangi iki LIS hesabını birleştirmen gerektiğini açıkla.
11. ★★★ Matris zinciri için `n = 40` matrisli rastgele boyutlarda, tüm parantezlemeleri sayan bir fonksiyon yaz. Tahminin neden tutmayacağını Catalan sayısıyla açıkla. (Mülakat)
12. ★★★ Bir `s` dizgisinin en az kaç karakter eklenerek palindrom yapılabileceğini bul. Cevabın `n - LPS(s)` olduğunu kanıtlamaya çalış ve küçük örneklerde doğrula.

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak kodu okuyacaksın: CPython 3.12.10'un standart kütüphanesindeki `Lib/difflib.py` dosyası. Kaynak, `v3.12.10` etiketinden alındı (`https://raw.githubusercontent.com/python/cpython/v3.12.10/Lib/difflib.py`). Aşağıdaki kesit, `SequenceMatcher.find_longest_match` yönteminin içinden, dosyanın 368–388. satırlarıdır. Yorumlar dahil birebir kopyalandı; yalnızca iki uzun yorum satırı, sayfa genişliği için ikiye bölündü; bölünen parçaların başına yalnızca `#` eklendi, başka hiçbir karakter değiştirilmedi.

Bu kesit, iki satır arasındaki en uzun ortak **ardışık** eşleşmeyi bulur; yani LCS (altdizi) değil, ortak altdizge (substring) arar. Dinamik programlamanın bir biçimidir: `j2len`, bir önceki `i` satırının değerlerini tutar ve her `i` için yalnızca eşleşen `j`'ler üzerinde güncellenir.

{{SNIP:difflib:368:388}}

**Sorular — cevaplamadan geçme:**

1. `j2len` bir dizi değil bir sözlüktür. Bu seçim, `b2j` ile birlikte hangi girdilerde bellek ve zaman kazandırır? Hangi girdide bu bir kazanç olmaz?
2. Döngüde `newj2len` her `i` için yeniden oluşturulur, sonra `j2len = newj2len` ile değiştirilir. Bu, Bölüm 16.4'teki yuvarlanan dizi fikriyle hangi açıdan aynıdır, hangi açıdan farklıdır?
3. `k = newj2len[j] = j2lenget(j-1, 0) + 1` satırında `j-1` neden kullanılır? LCS tablosundaki `dp[i-1][j-1] + 1` ile bu satırı karşılaştır: eşleşmeyen durumda LCS neden `max` alır, burada ise hücre neden sıfırlanır (yani sözlükte hiç yazılmaz)?
4. Belgelendirme metni, aynı uzunlukta birden fazla eşleşme varsa `a`'da en erken başlayanın döndürüldüğünü söyler. Bu tie-break kuralı için kodda hangi satır sorumludur ve `k > bestsize` (`>=` değil) neden önemlidir?
5. `autojunk` ve popüler öğe mantığı (`__chain_b`) `len(b) >= 200` için devreye girer. Bu eşiğin üzerinde en uzun eşleşme neden tam olarak doğru olmayabilir? Bunu kısa bir örnekle göster; sonucu `SequenceMatcher(None, a, b, autojunk=False)` ile karşılaştır.
6. (Mülakat) Bu kesitin en kötü durum karmaşıklığı nedir? İki dizgi de tek bir karakterden oluşuyorsa ne olur? Bunu, `b2j` listelerinin uzunluğu cinsinden yaz.

## Bölüm Özeti

Bu bölümde dinamik programlamayı bir teknik olarak değil, bir düşünme protokolü olarak öğrendik:

- DP, **örtüşen alt problemler** ve **optimal alt yapı** koşullarının ikisi birden sağlandığında uygulanır. En uzun basit yol, ikinci koşulu sağlamadığı için tabloya dökülemez.
- Protokol altı sorudan oluşur: durum (bir cümleyle), geçiş, taban, sıra, cevabın yeri ve maliyet. Durumu cümleyle tanımlayamıyorsan kod yazma.
- **Memoization** üstten alta ve yığın kullanır; **tabulation** alttan üste ve döngüyle çalışır. Python'da memo derinlik sınırına (varsayılan 1000) takılır; tablo takılmaz.
- Bellek yalnızca bir önceki satıra bağlıysa tek boyuta indirilir; 0/1 sırt çantasında kapasiteler **büyükten küçüğe** taranmalıdır, aksi halde eşya tekrar alınır.
- Geri izleme, değerin yanında seçimleri de verir; bunun için tam tablo gerekir ya da bölme-fethetme ile bellek ödünleşilir.
- Sayma (toplam) ve en iyileme (min/max) aynı protokolü kullanır; döngü sırası, kombinasyon ve permütasyon sayımını belirler.
- Sırt çantası ailesi (0/1, sınırsız, çubuk kesimi) bir kapasite ve öğeler üzerinde çalışır. `O(nW)` sözde-polinomdur; girdi uzunluğu cinsinden üstel olabilir.
- Dizi DP'leri (LCS, edit distance, LIS) iki diziyi ya da bir diziyi tabloyla hizalar; LIS'in `O(n log n)` sürümü sabır sıralamasıdır ve ikili aramaya dayanır.
- Aralık DP (matris zinciri) alt problemleri aralıklar olarak tanımlar ve hesabı uzunluk sırasıyla yapar.

**Sonraki bölümde:** Bu bölümde tabloları sıralı alt problemler üzerinde kurduk. Bölüm 17'de (Graph Algoritmaları) problem bir grafa dönüşür: BFS ve DFS ile dolaşmayı, Dijkstra ve Bellman-Ford ile en kısa yolu, Kruskal ve Prim ile minimum örten ağacı öğreneceğiz. Topolojik sıralama, bu bölümde gördüğümüz DAG'ın hesaplama sırası olduğunu ortaya çıkaracak.

::: mulakat
Klasik sorular, hemen cevaplamaya çalışma; her birini birkaç dakika düşün:

1. Bir problemin DP ile çözülebilmesi için hangi iki koşul gerekir? Her birinin sağlanmadığını gösteren bir örnek ver.
2. Memoization ile tabulation arasında ne zaman birini diğerine tercih edersin? Yığın derinliği ve gereksiz durumlar bu kararı nasıl etkiler?
3. 0/1 sırt çantasında kapasiteleri neden büyükten küçüğe taramalısın? Yanlış yönde taranırsa hangi problem çözülmüş olur?
4. Sözde-polinom ne demektir? `O(nW)` ifadesinin neden girdi uzunluğu cinsinden üstel olduğunu bir sayıyla açıkla.
5. LCS ile en uzun ardışık ortak altdizgi arasındaki fark nedir? Hangisi `diff` için doğru tanımdır ve neden?
6. LIS'in `O(n log n)` sabır sıralaması kuyruk dizisini geri kurmadan neden yalnızca uzunluğu verir? Gerçek LIS'i geri kurmak için ne eklenmelidir?
7. Matris zinciri çarpımında iki parantezleme aynı sonucu verir ama maliyetleri farklıdır. Bu bir DP probleminin ne tür bir alt yapısını gösterir?
8. Açgözlü algoritma bir problemde doğru çalışıyor gibi görünüyorsa, DP'ye geçmeden önce hangi karşı örneği aramalısın?
:::
