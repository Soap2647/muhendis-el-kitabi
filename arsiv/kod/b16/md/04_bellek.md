## 16.4 Bellek optimizasyonu ve döngü yönü

Tabulation tablosu çoğu problemde gereğinden büyüktür. Sırt çantası için `n` eşya ve `W` kapasite varsa tablo `(n+1) × (W+1)` hücre tutar. Ama `dp[i]` satırı yalnızca `dp[i-1]` satırına bakar. Yani geçmiş satırları saklamak zorunda değilsin; tek bir satırı yerinde güncellemek yeter. Buna **yuvarlanan dizi** (rolling array) denir. Tablo boyutu `O(nW)`'den `O(W)`'ye iner.

Yerinde güncelleme tuzaklıdır. Tek bir diziyle çalışırken `dp[c]`'yi güncellediğinde, o değeri bir sonraki hesapta kullanmak isteyebilirsin ya da istemeyebilirsin. 0/1 sırt çantasında her eşya en fazla bir kez alınabilir; bunun için `dp[c - w]` değeri, eşyayı eklemeden önceki hâliyle kullanılmalıdır. Bunu sağlamanın yolu kapasiteleri **büyükten küçüğe** taramaktır: `dp[c]`'yi yazmadan önce `dp[c - w]` henüz bu eşyayla güncellenmemiştir, çünkü `c - w < c`.

Eşyanın sınırsız kez alınabildiği (unbounded) problemde ise tam tersini istersin. Kapasiteleri küçükten büyüğe tararsan, `dp[c - w]` bu eşyayla zaten güncellenmiş olur ve eşya tekrar alınabilir. Yani döngü yönü, problemin türünü belirler. Bu farkı, programın içinde ayrı bir fonksiyon olarak deneyeceğiz.

Aşağıdaki program dört şeyi yapar: 0/1 çözümünü iki yönle hesaplar, sınırsız çözümü ayrı bir fonksiyonla kurar, geri izleme için tam tablo üretir ve her şeyi kaba kuvvetle karşılaştırır. Kaba kuvvet, tüm alt kümeleri (0/1 için) ya da tüm sayı kombinasyonlarını (sınırsız için) dener; küçük girdilerde doğru cevabı garanti eder. Programın ilk parçası tek boyutlu tabloyu içerir.

{{KOD:sirt_canta.py:1:25}}

`sirtcanta_01` fonksiyonunun iç döngüsü `for c in aralik` ile yalnızca bir kez kapasite üzerinde gider; `yon` parametresi döngü sırasını seçer. `sinirsiz` ise ayrı bir fonksiyondur ve kapasiteleri artan sırayla tarar, her kapasitede tüm eşyaları dener. İki fonksiyonun da bir `dp` dizisi vardır; `dp[c]`, "kapasite en fazla `c`" için ulaşılabilen en iyi değerdir. Bu yüzden `dp[W]` doğrudan cevaptır: kapasite tam dolmasa bile en iyisi zaten orada tutulur.

Bir sonraki parça tam tabloyu ve geri izleme fonksiyonunu içerir; onları Bölüm 16.5'te açıklayacağız.

{{KOD:sirt_canta.py:26:47}}

Kaba kuvvet fonksiyonları, DP'nin doğruluğunu bağımsız olarak kontrol etmek için yazıldı. `kaba_01` `2^n` altkümeyi tek tek dener; bu yüzden yalnızca küçük `n` için uygundur. Bu bir hata değil, bir ölçüm araçtır: her zaman küçük örneklerle DP'yi kaba kuvvete karşı test et.

{{KOD:sirt_canta.py:48:70}}

Ana fonksiyon, önce ters ve ileri yönün aynı örnekte nasıl farklı sonuç verdiğini gösterir. Ardından 300 rastgele örnekte iki DP'nin de kaba kuvvetle eşleştiğini doğrular. Sonunda kenar durumları (kapasite 0, boş eşya listesi) ve geri izleme örneğini yazdırır.

{{KOD:sirt_canta.py:71:99}}

Programı çalıştırdık:

{{TERM}}
python sirt_canta.py ||| python sirt_canta.py
{{/TERM}}

Çıktının ilk üç satırı, döngü yönünün önemini tek bir örnekte gösteriyor. Eşyalar `(ağırlık, değer)` olarak `(2, 3)` ve `(3, 4)`, kapasite 4. 0/1 kuralında, iki eşyadan en fazla biri alınabilir: en iyi değer `4`'tür (yalnız ikinci eşya). Ters döngü bunu doğru bulur. İleri döngü `6` verir, yani birinci eşyayı iki kez alır (`2 + 2 = 4`, değer `3 + 3 = 6`). Yani ileri döngü, sessizce 0/1 problemini sınırsız probleme çevirmiş oldu. Bu bir hata mesajı vermez, sadece yanlış cevap verir; bu yüzden döngü yönünü anlamadan 0/1 çözümü yazmamalısın.

Rastgele testte hata sayısının sıfır çıkması, DP'nin iki sürümünün de kaba kuvvetle uyumlu olduğunu gösterir. Bu test sonucu bir kanıt değildir; yalnızca `random.Random(42)` ile üretilen 300 örnekte doğrulamadır. Doğruluk kanıtı için ayrı bir argüman gerekir: 0/1 için döngü değişmezi, her eşyada `dp[c]`'nin "ilk `i` eşya ile kapasite en fazla `c`" anlamını koruduğunu söyler.

Kenar durumlarına da bakalım. `W = 0` için kapasite sıfırdır ve hiçbir eşya sığmaz; cevap 0 olmalıdır. Boş eşya listesinde de cevap 0'dır. Programın çıktısı ikisini de doğru yazıyor. Bu iki durumu her DP'de ayrıca kontrol etmek, Bölüm 16.2'deki taban durumların doğruluğunu sınamanın en ucuz yoludur.
