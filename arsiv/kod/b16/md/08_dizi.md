## 16.8 Dizi DP'leri: LCS, edit distance ve LIS

Dizi DP'leri, iki diziyi (ya da tek bir diziyi) karşılaştırır. Üç klasik problem bu ailenin temelidir: en uzun ortak altdizi (LCS), iki dizgi arasındaki düzenleme mesafesi (edit distance) ve en uzun artan altdizi (LIS). Üçü de tabloyu satır satır ya da köşegen boyunca doldurur.

Önce bir ayrımı netleştirelim, çünkü mülakatta ve kendi projende karıştırılır. **Altdizi** (subsequence) elemanları sırasını koruyarak, ama aralarını atlayarak seçtiğin dizidir. **Altdizge** (substring) ise ardışık elemanlardan oluşan bir parçadır. LCS altdizi ile ilgilenir, bu bölümde ele alacağımız problem budur. Kod Okuma Egzersizi'nde göreceğimiz difflib kodu ise ardışık eşleşmeyi, yani altdizgiyi arar.

### LCS: en uzun ortak altdizi

`a` ve `b` dizgileri için `dp[i][j]`, `a`'nın ilk `i` karakteri ile `b`'nin ilk `j` karakteri arasındaki LCS uzunluğu olsun. Geçiş iki durumludur. Eğer `a[i-1] == b[j-1]` ise bu karakter LCS'e girebilir ve `dp[i][j] = dp[i-1][j-1] + 1` olur. Değilse, iki karakterden en az birini atlamak gerekir ve `dp[i][j] = max(dp[i-1][j], dp[i][j-1])` olur. Taban durumlar boş bir önek için 0'dır.

Aşağıdaki program tabloyu doldurur, geri izleyerek LCS dizgisini yazdırır ve küçük örneklerde kaba kuvvetle karşılaştırır. Kaba kuvvet, `a`'nın tüm altdizilerini üretip `b` içinde arar.

{{KOD:lcs.py:1:40}}

Ana fonksiyonun çıktısı, tabloyu bir matris olarak gösterir; üst satır ve sol sütun sıfırlardan oluşan taban durumlardır. Geri izleme kuralı şöyledir: eşleşen karakterde köşegenden gel ve karakteri al; eşleşmeyen karakterde, değeri büyük olan komşuya git (eşitse yukarı).

{{KOD:lcs.py:41:66}}

Programı çalıştırdık:

{{TERM}}
python lcs.py ||| python lcs.py
{{/TERM}}

Sonucun `BCBA` olduğunu tablodan elle de doğrulayabilirsin. Son hücre 4 ve geri izleme dört eşleşme yapar. Bu tablonun ve yolun şekli aşağıda.

![Şekil 16.5: LCS tablosu, a = ABCBDAB ve b = BDCABA. Açık yeşil hücreler geri izleme yolunu gösterir; köşegen adımlar, eşleşen harfleri (A, B, C, B) işaretler.](gorseller/b16_lcs_tablo.png)

LCS'in gerçek hayattaki karşılığı, satır bazlı `diff`'tir. İki dosyanın satırlarını birer dizi olarak düşün; ortak satırların en uzun altdizisi LCS'tir. LCS'e dahil olmayan satırlar silinmiş ya da eklenmiş sayılır. Bu yorumla `diff`'in çıktısı, LCS'in tümleyenidir. GNU `diff` bu hesabı tabloyla değil Myers algoritmasıyla yapar; tanım aynıdır, hız farklıdır. Bu bölümün kendi projesi tam olarak bu fikri kullanır.

C'de aynı algoritmanın belleği elle yönetilen sürümü şöyle görünür. Tablo tek bir `calloc` bloğunda, satır-sütun indeksleriyle tutulur. `calloc` bellekteki her değeri sıfırlar, bu da taban durumların elle doldurulmasını gereksiz kılar. Burada `(n+1) * (m+1)` çarpımının taşmaması için girdi boyutlarının makul olduğunu varsayıyoruz; gerçek bir kodda bu kontrol edilmelidir.

{{KOD_C:lcs.c}}

Programı WSL'de iki kez derledik: önce normal, sonra `-fsanitize=address,undefined` ile. Sanitizer, bellek taşmasını ve tanımsız davranışı çalışma zamanında yakalar. Çıktıda sanitizer uyarısı yoksa program bu girdi için temizdir:

{{TERM}}
gcc -O2 -Wall -Wextra -std=c11 lcs.c -o lcs ||| wsl gcc -O2 -Wall -Wextra -std=c11 /mnt/c/Users/merty/AppData/Local/Temp/b16/kod/lcs.c -o /tmp/lcs_b16
./lcs ||| wsl /tmp/lcs_b16
gcc -g -O1 -Wall -Wextra -fsanitize=address,undefined lcs.c -o lcs_asan ||| wsl gcc -g -O1 -Wall -Wextra -fsanitize=address,undefined /mnt/c/Users/merty/AppData/Local/Temp/b16/kod/lcs.c -o /tmp/lcs_asan
./lcs_asan ||| wsl /tmp/lcs_asan
{{/TERM}}

Sanitizer'ın temiz çıkması, bu bir kanıt değildir; yalnızca çalışan yollar için bir sinyaldir. Diziyi sınır dışına taşıran bir girdi için aynı program ASan raporu verirdi. Bu, C'de DP tablolarının indekslerini her zaman iki kez kontrol etmenin nedenidir.

### Edit distance: yazım denetimi ve düzenleme mesafesi

İki dizgi arasındaki düzenleme mesafesi, birinciyi ikinciye dönüştürmek için gereken en az işlem sayısıdır. İşlemler üçtür: bir karakter ekle, sil ya da değiştir. Bu tanıma Levenshtein mesafesi de denir. Yazım denetimi (spell check), en yakın sözcüğü bulmak için bu mesafeyi kullanır; Mert Studio Code'daki Türkçe parser'a benzer bir öneri motoru bu yolla yazılabilir (Çözümlü Örnekler'in dördüncüsünde bunu deneyeceksin).

`dp[i][j]`, `a`'nın ilk `i` karakterini `b`'nin ilk `j` karakterine çevirmenin en az maliyetidir. Taban durumlar: `dp[i][0] = i` (hepsini sil), `dp[0][j] = j` (hepsini ekle). Geçiş: `a[i-1] == b[j-1]` ise maliyet değişmez, `dp[i][j] = dp[i-1][j-1]`. Değilse, üç seçeneğin en küçüğüne 1 eklenir: değiştir (`dp[i-1][j-1]`), sil (`dp[i-1][j]`) ve ekle (`dp[i][j-1]`).

Programın ilk parçası tabloyu ve işlem dizisini geri izleyerek üretir. Geri izleme sırasında her adımda hangi işlemin kullanıldığını kaydederiz; bu yüzden yalnızca mesafeyi değil, dönüşümün kendisini de elde ederiz.

{{KOD:edit.py:1:41}}

Programın ikinci parçası, işlem dizisini `a` üzerinde uygular ve sonucun `b`'ye eşit olduğunu doğrular. Bu, geri izlemenin doğruluğunu kanıtlayan en iyi testtir: işlemleri yürütmek sonucu üretmeliyse, geri izleme doğrudur. Ayrıca `bfs` fonksiyonu, düzenleme işlemlerinin tüm dizgi uzayında en kısa yolunu bulur. Bu, DP'den bağımsız bir kontroldür; DP'nin tablo bağıntısını hiç kullanmaz.

{{KOD:edit.py:42:80}}

Ana fonksiyon `kitten` → `sitting` örneğini çözer ve 150 rastgele örnekte üç kontrolü birlikte yapar: BFS mesafesi, işlemlerin uygulanması ve düzenleme sayısı. Düzenleme sayısını sayarken `ESLE` (eşleşme) işlemlerini dışarıda bırakmak gerekir; çünkü onlar maliyet taşımaz.

{{KOD:edit.py:81:108}}

Programı çalıştırdık:

{{TERM}}
python edit.py ||| python edit.py
{{/TERM}}

Çıktı üç düzenleme gösteriyor: `k` harfi `s` ile değiştirilir, `e` harfi `i` ile değiştirilir ve sona `g` eklenir. Toplam maliyet 3'tür. Aşağıdaki şekil bu yolu tabloda gösterir.

![Şekil 16.6: kitten'den sitting'e edit distance tablosu. Yeşil yol, üç düzenlemeye (k->s, e->i, ekle g) karşılık gelen hücrelerdir; son hücre 3'tür.](gorseller/b16_edit_tablo.png)

Edit distance'ın bir hatası çok sinsidir: maliyet doğru olsa bile geri izleme yanlış işlem dizisi üretebilir. Bu yüzden iki ayrı kontrol gerekir: sayı (BFS ile) ve işlem dizisi (uygulayarak). Programda ikisi de yapılıyor.

### LIS: en uzun artan altdizi

Bir dizinin en uzun artan altdizisi (LIS), sırasını koruyan ve kesin artan olan en uzun altdizidir. `dp[i]` = `a[i]`'de biten en uzun artan altdizinin uzunluğu olsun; `dp[i] = 1 + max(dp[j])`, `j < i` ve `a[j] < a[i]` için. Bu, `O(n^2)` bir DP'dir. Bölüm 16.2'de gördüğümüz gibi cevap tüm `dp` değerlerinin en büyüğüdür.

Daha hızlı bir yol vardır: sabır sıralaması (patience sorting). Her adımda bir kuyruk dizisi tutarız; `kuyruk[k]`, uzunluğu `k + 1` olan artan altdizilerin en küçük son elemanıdır. Yeni bir `x` geldiğinde, `x`'ten küçük olmayan ilk konumu ikili aramayla buluruz (Bölüm 14.2'deki alt sınır). Bu konum kuyruğun sonundaysa dizi uzar; değilse o konumdaki değer `x` ile değiştirilir. Bu değiştirme, aynı uzunluktaki altdizilerin en küçük son elemanını korur, bu yüzden sonraki adımlar için daha iyidir. Her eleman için `O(log n)` iş yapıldığından toplam `O(n log n)` olur.

Aşağıdaki program iki sürümü çalıştırır, sabır izini yazdırır ve kaba kuvvetle karşılaştırır. `bisect.bisect_left` Python'un standart ikili arama fonksiyonudur; Bölüm 14'teki alt sınır tanımıyla aynıdır.

{{KOD:lis.py:1:38}}

Ana fonksiyon, `[3, 1, 4, 1, 5, 9, 2, 6]` dizisi için sabır izini yazdırır ve iki sürümün sonuçlarını karşılaştırır.

{{KOD:lis.py:39:55}}

Programı çalıştırdık:

{{TERM}}
python lis.py ||| python lis.py
{{/TERM}}

İzde kuyruk dizisinin **uzunluğu** LIS uzunluğunu verir: 4'tür. Ama kuyruktaki değerler tek bir artan altdizi değildir. Son adımda kuyruk `[1, 2, 5, 6]` olur; fakat bu dizi bir altdizi değildir, çünkü `2`, `a`'da `5`'ten sonra gelir. Kuyruk, her uzunluk için ayrı ayrı "en küçük son" değerlerini tutar ve bu değerler farklı altdizilerden gelebilir. Gerçek LIS elemanlarını geri kurmak için her elemanın kuyruktaki önceki elemanını da kaydetmen gerekir; bu, geri izleme kalıbının aynısıdır.

Aşağıdaki şekil aynı izi sütunlar hâlinde gösterir; her satır bir eleman geldikten sonraki kuyruk dizisidir.

![Şekil 16.7: LIS sabır sıralaması, a = [3, 1, 4, 1, 5, 9, 2, 6]. Her satır bir eleman eklendikten sonraki kuyruk dizisidir; bordo kutu, o adımda değiştirilen ya da eklenen konumdur.](gorseller/b16_lis_sabir.png)

Sabır sıralamasında kuyruğun sıralı kalması, ikili aramanın doğruluğunun temelidir. Kuyruk her zaman kesin artan olduğu için `bisect_left` her seferinde doğru konumu bulur. Bu sıralılık değişmezi, Bölüm 14'teki döngü değişmezinin bir başka örneğidir.

Bu üç problemi bir arada görmek, DP'de sık görülen bir kalıbı açıklar: bir dizi üzerinde iki indeks ya da tek indeks ve bir yardımcı yapı (kuyruk, tablo, geri izleme dizisi). Sorunun hangi biçimde olduğunu tanımak, hangi tabloyu kuracağına karar vermenin ilk adımıdır.
