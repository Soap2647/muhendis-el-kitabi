## 16.9 Aralık DP: matris zinciri çarpımı

Şimdiye kadarki tablolarda alt problemler önekler (`a`'nın ilk `i` karakteri) ya da kapasiteler gibi tek boyutlu bir parametreyle tanımlanıyordu. Matris zinciri çarpımında alt problem bir **aralıktır**: `A_i, A_{i+1}, ..., A_j` matrislerinin çarpımı. Bu tür DP'ye aralık DP denir.

Problem şudur. Matrislerin çarpımı birleşmelidir ama değişmeli değildir: `(AB)C` ile `A(BC)` aynı sonucu verir, ama işlem maliyeti farklı olabilir. Bir `p × q` matrisi ile `q × r` matrisini çarpmak `p·q·r` skaler çarpım yapar. Dolayısıyla çarpma sırası, toplam maliyeti değiştirir. Örneğin `10 × 100` boyutlu `A`, `100 × 5` boyutlu `B` ve `5 × 50` boyutlu `C` için `(AB)C` önce `AB` (10·100·5 = 5000) sonra `(AB)C` (10·5·50 = 2500) yapar; toplam 7500 çarpma. `A(BC)` ise önce `BC` (100·5·50 = 25000), sonra `A(BC)` (10·100·50 = 50000) yapar; toplam 75000 çarpma. Aynı sonuç, on kat farklı maliyet.

Protokolü uygulayalım. `m[i][j]`, `A_i ... A_j` aralığını çarpmanın en az skaler çarpım sayısı olsun. Durum: bir aralık. Geçiş: aralığı `k` noktasından bölmek; sol parça `A_i..A_k`, sağ parça `A_{k+1}..A_j`, ve iki parçayı çarpmanın maliyeti `p[i] · p[k+1] · p[j+1]`. Yani `m[i][j] = min_k (m[i][k] + m[k+1][j] + p[i] · p[k+1] · p[j+1])`. Taban durum: tek matris (`i = j`) için maliyet 0'dır. Sıra: aralığın uzunluğu 2'den `n`'ye artan; çünkü `m[i][j]`'yi hesaplamak için daha kısa aralıklar gerekir.

Bu sıralama, aralık DP'nin özüdür: alt problemler uzunluklarına göre hesaplanır. Bir aralığın içindeki her bölünme, iki daha kısa aralığa bağlıdır, dolayısıyla uzunluk sırası doğru sıradır.

Aşağıdaki program, CLRS'nin klasik örneğini çözer: `p = [30, 35, 15, 5, 10, 20, 25]`, yani altı matris. Aynı zamanda bölme noktasını `s[i][j]` tablosunda saklar, böylece parantezlemeyi geri kurabilir.

{{KOD:matris.py:1:30}}

{{KOD:matris.py:31:44}}

Ana fonksiyon, yazdırılan en az maliyetin doğruluğunu, rastgele örneklerde tüm parantezlemeleri numaralandırarak kontrol eder. Altı matrisli bir zincirde parantezleme sayısı Catalan sayısıdır (`C_5 = 42`); bu yüzden kaba kuvvet küçük `n` için yeterince hızlıdır.

{{KOD:matris.py:45:63}}

Programı çalıştırdık:

{{TERM}}
python matris.py ||| python matris.py
{{/TERM}}

Çıktıdaki en az maliyet `15125` ve parantezleme `((A1 x (A2 x A3)) x ((A4 x A5) x A6))`'dır. En dıştaki bölünme `A1..A3` ile `A4..A6` arasındadır; bu, `s[0][5]` hücresinde saklı `k = 2` değeridir (0 tabanlı indeks). Tablonun tamamı aşağıda.

![Şekil 16.8: Matris zinciri tablosu m[i][j], p = [30, 35, 15, 5, 10, 20, 25]. Satırlar ve sütunlar A1..A6; sağ üst köşe tüm zincirin maliyetidir (kırmızı çerçeve, 15125). Renkler aralık uzunluğuna göre: açık gri üçgenin altı kullanılmaz.](gorseller/b16_matris_aralik.png)

Tabloyu köşegen boyunca okumak en kolayıdır. Köşegenler uzunluğa göre dizilir: ilk köşegen tek matrislerdir (`0`), ikinci köşegen iki matrisli çarpımlardır (`15750`, `2625`, ...). Sağ üst köşe, en uzun aralıktır ve cevabı verir. Bir hücreyi hesaplamak için soldaki ve aşağıdaki hücrelere, yani daha kısa aralıklara bakarsın; bu, sıralamanın doğruluğunu görsel olarak gösterir.

Karmaşıklık, üç iç içe döngüden gelir: uzunluk (`n`), başlangıç (`n`) ve bölme noktası (`n`). Zaman `O(n^3)`, bellek `O(n^2)`'dir. `n = 6` için bu küçüktür, ama bin matrisli bir zincir için bu hesap pahalıdır. Derin öğrenmede benzer problemler tensör çarpım sıralamasında ortaya çıkar; `einsum` gibi araçlar bu sıralamayı otomatik seçmeye çalışır.

Matris zinciri, aralık DP'nin tipik şablonudur: bir dizinin bir parçasını (aralığı) durum olarak alırsın, bölme noktasını geçiş olarak seçersin ve hesabı uzunluk sırasıyla yaparsın. Bölüm 19'da (Divide & Conquer) aynı "böl ve birleştir" düşüncesini bir kez daha göreceksin; fark, orada alt problemlerin tekrar etmemesidir.
