## 16.5 Çözümü geri kurmak: değer yetmez, seçimi de bil

DP çoğu zaman yalnızca bir sayı üretir: en yüksek değer, en az maliyet, en uzun uzunluk. Pratikte ise çoğu zaman *hangi* eşyaların alındığını, *hangi* hizalamanın yapıldığını ya da *hangi* düzenlemelerin gerektiğini de istersin. Bu soruyu cevaplamak için tablonun yalnızca son hücresini değil, hesabın izini de tutmak gerekir.

Yaygın yöntem geri izlemedir (backtracking, Bölüm 15'te gördüğümüz terim buradaki anlamla karıştırılmamalı). Tablo tamamen doldurulduktan sonra, cevabın son hücreden başlayarak her adımda "bu değere nasıl gelindi?" sorusunu sorarız. Her adımda tablodaki iki komşuya bakarak hangi bağıntının geçerli olduğunu buluruz ve oradan geriye gideriz.

Sırt çantasında bu basittir. `dp[i][c]` ile `dp[i-1][c]` aynıysa, `i`. eşya alınmamıştır: değer, eşya olmadan da aynı şekilde elde edilmiştir. Farklıysa eşya alınmıştır ve kalan kapasite `c - w_i`'dir. Aşağıdaki şekil, `W = 7` ve dört eşyalık örnekte tabloyu ve geri izleme yolunu gösteriyor.

![Şekil 16.4: 0/1 sırt çantası tablosu (eşyalar ağırlık-değer: (1,1), (3,4), (4,5), (5,7); W = 7). Bordo hücreler, eşyanın alındığı adımlardır; açık yeşil hücreler geri izleme yolunu oluşturur. Seçilen eşyalar 2. ve 3. (ağırlık 3 ve 4) ve toplam değer 9'dur.](gorseller/b16_knap_tablo.png)

Şekildeki yolu programın fonksiyonuyla izleyelim. `secilenler` fonksiyonu `dp[i][c] != dp[i-1][c]` koşulunu kullanır ve alınan eşyanın indeksini döndürür. Bu yüzden onu sırt çantası programının ikinci parçasında gördük:

{{KOD:sirt_canta.py:39:46}}

Bu fonksiyon tam tabloyu okuduğu için, tablonun tamamının saklı olması şarttır. Yuvarlanan dizi (Bölüm 16.4) bunu sağlamaz: tek satır kullanıldığında eski satırlar yok olur ve geri izleme yapılamaz. Bu bir ödünleşmedir. Ya `O(nW)` bellek ödersin ve geri izlersin, ya da `O(W)` bellekle yalnızca değeri hesaplarsın. Bellek kritikse üçüncü bir yol vardır: Hirschberg tipi bölme-fethetme, geri izlemeyi tablo saklamadan yapar. Bu yöntem LCS için de geçerlidir; ama uygulaması bu kitabın kapsamı için karmaşıktır, konuyu kendi projen için ileri okumaya bırak.

Geri izlemede bir ayrıntı daha önemlidir: eşitlik durumu. Birden fazla en iyi çözüm varsa, `secilenler` hangisini seçtiğini kendi koşuluyla belirler. Bu, "tek doğru cevap" beklentisini bozar. Mülakatta "bu çözüm tek mi?" diye sorulduğunda, eşitlik durumlarını tek tek saymak gerekir.

Tablo ile yolu birlikte düşünmek, hatayı bulmanın da en hızlı yoludur. Eğer geri izlemenin sonucu `dp[n][W]` değerine eşit bir toplam vermiyorsa, ya tablo ya da geri izleme yanlıştır. Programın ana fonksiyonunda bu kontrolü yapmadık, çünkü kaba kuvvet karşılaştırması yeterlidir. Ama kendi kodunda değer ile seçilen eşyaların toplamını ayrıca karşılaştırmayı alışkanlık hâline getir.
