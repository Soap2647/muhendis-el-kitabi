## 16.6 Sayma ve en iyileme: Fibonacci, merdiven ve para bozma

DP'nin iki büyük ailesi vardır. Birincisi **sayma** problemleridir: kaç farklı yol, kaç farklı kombinasyon var? İkincisi **en iyileme** problemleridir: en az ya da en çok ne? İkisi aynı protokolü kullanır (Bölüm 16.2); geçişteki işlem değişir. Sayma geçişi toplamdır, en iyileme `min` ya da `max`.

Merdiven problemi sayma örneğidir. `n` basamaklı bir merdivene 1 ya da 2 basamak atlayarak kaç farklı yolla çıkılır? Bölüm 16.2'deki protokol ile `dp[i] = dp[i-1] + dp[i-2]`, `dp[0] = 1`, `dp[1] = 1` olur. Bu dizi Fibonacci dizisidir; `n` basamak için cevap `fib(n+1)`'dir. Yani Bölüm 16.3'teki Fibonacci ölçümü aslında bir sayma problemiydi.

Para bozma ise hem sayma hem en iyileme olarak sorulabilir. Elinde `1`, `2`, `5` birimlik madeni paralar olsun ve `tutar` kadar parayı tam olarak toplamak istiyorsun. Üç soru sorulabilir: En az kaç parayla toplanır? Kaç farklı şekilde toplanır? Ve şekil sırası önemli mi? Son soru çoğu zaman gözden kaçar ve asıl tuzak oradadır.

Aşağıdaki program üç fonksiyonla bu soruları cevaplar. İlk fonksiyon en az madeni parayı bulur. Tutarı `inf` (sonsuz yerine `tutar + 1`, çünkü en fazla `tutar` adet para gerekebilir) ile başlatır ve `dp[t]`'yi `dp[t - p] + 1`'den küçükse günceller.

{{KOD:para_bozma.py:1:33}}

Kalan iki fonksiyon, yolların sayısını hesaplar; aralarındaki tek fark döngülerin iç içe geçiş sırasıdır. `yol_kombinasyon` önce madeni paraları, sonra tutarı dolaşır: her madeni para için tabloyu bir kez günceller. Bu, paraların sırasını göz ardı eder; yani `1 + 2` ile `2 + 1` aynı sayılır. `yol_permutasyon` ise önce tutarı, sonra madeni paraları dolaşır: her tutar için tüm paraları dener. Bu da sıralı dizileri sayar; `1 + 2` ile `2 + 1` ayrı sayılır.

{{KOD:para_bozma.py:34:53}}

Bu iki sayma biçimi, DP'nin en sık karıştırılan iki sorusudur. "Kaç farklı kombinasyon" sorusu için madeni para döngüsü dışta, "kaç farklı sıralı dizi" sorusu için tutar döngüsü dışta olmalıdır. Döngü yerini değiştirmek, bir problemi diğerine dönüştürür. Ana fonksiyon bunu sayılarla gösterir ve kaba kuvvet karşılaştırması yapar.

{{KOD:para_bozma.py:54:75}}

Programı çalıştırdık:

{{TERM}}
python para_bozma.py ||| python para_bozma.py
{{/TERM}}

Tutar 5 satırı, kombinasyon ile permütasyonun farkını açıkça gösteriyor. Kombinasyon sayısı 4'tür: `{5}`, `{2,2,1}`, `{2,1,1,1}`, `{1,1,1,1,1}`. Permütasyon sayısı 9'dur, çünkü `{2,2,1}` 3 farklı sıralanır, `{2,1,1,1}` 4 farklı sıralanır ve diğer ikisi 1'er tanedir. Aynı tutarın en az madeni para sayısı ise 1'dir (tek bir 5 birimlik para). Üç soru üç farklı cevap verir; hangi sorunun sorulduğunu önce anlamak gerekir.

`tutar = 3` için `[2]` madeni parası yalnız başına yetmez; program `-1` döndürür. Bu, "çözüm yok" durumunun da tabloda `inf` olarak taşındığını gösterir. Kaba kuvvet kontrolü 200 rastgele örnekte iki sayma fonksiyonunu da doğruladı.

Para bozmada bir gerçek daha var: sıralı dizi sayısı üstel büyür. `tutar = 11` için kombinasyon sayısı 11 iken permütasyon sayısı 218'dir; tutar büyüdükçe bu değerler hızla artar. Bu yüzden sonuçları büyük tutarlarda tam sayı olarak saklamak için Python'un büyük tamsayılarını ya da bir mod (örneğin `10^9 + 7`) kullanmak gerekebilir. Mod kullanıldığında sonuç yalnızca kalanı verir; bu, soruyu değiştirir ve bunu açıkça belirtmek gerekir.

Son olarak bağlantıya bak: merdiven sayısı, yalnızca 1 ve 2 paralarıyla sıralı permütasyon saymaktır. `yol_permutasyon([1, 2], 5)` çağrısı 8 verir; bu `fib(6) = 8` ile aynıdır. Yani merdiven, para bozmanın özel bir durumudur ve Bölüm 16.2'deki protokolün iki kez kullanıldığını görürsün.
