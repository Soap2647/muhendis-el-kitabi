## 80.8 İzleme: kayma ne zaman alarm olur?

Model sahaya çıktığında dünya değişir. Kamera yaşlanır, hava kararır, sis gelir, yeni tip bir İHA görünür. Model bu değişiklikleri kendi kendine fark etmez; kötüleşir ve bunu bir hata mesajıyla bildirmez. Bölüm 77.9 ve 77.10'da bu sessiz bozulmayı, drift adıyla anlatmıştık. Burada bu fikri uçtan uca bağlıyoruz: hangi ölçüleri izleyeceğiz, hangi eşiklerde alarm vereceğiz ve alarm geldiğinde ne olacak.

Üç sinyal izliyoruz. Birincisi girdi kayması: her görüntünün ortalama parlaklığı, referans pencerelerdeki dağılıma göre PSI ile karşılaştırılır (Bölüm 77.10'daki PSI tanımı). İkincisi skor kayması: her görüntünün en yüksek tespit skoru, referans dağılımına göre iki örnekli KS testiyle karşılaştırılır. Üçüncüsü performans: mAP@0,5, gerçek etiketlerle hesaplanır, ama etiketler gecikmeli gelir. Bu gecikme gerçekçidir; bir İHA görüntüsünün doğru etiketi genellikle sonradan bir insan tarafından yazılır.

Girdi ve skor sinyalleri etiketsizdir; yani her pencerede hemen hesaplanabilirler. Performans sinyali ise en güvenilir olanıdır ama en geç gelendir. Bu üçlünün birlikte kullanılması, Bölüm 77.10'daki "etiketsiz kayma yakalanır, kavram kayması etiketle yakalanır" ayrımının uygulamasıdır.

Simülasyon altmış pencere (her biri 200 sahne) üretir. Pencere 0 ile 19 referanstır ve yalnızca nominal veri içerir. Pencere 20'den itibaren kayma karışımı kademeli olarak artar: pencere 20'de sıfır, pencere 30'da bir. Bir pencerede her sahne, karışım oranı kadar olasılıkla kayma ayarından üretilir. Böylece kayma ani değil, bir sis ya da bir ışık değişimi gibi kademeli olur.

Kodun ilk parçası sabitleri, PSI fonksiyonunu ve kayma oranını tanımlar.

{{KOD izleme 1}}

Kodun ikinci parçası pencere üretimini ve tohum seçimini tanımlar. Her pencerenin kendi tohumu (1000 + w) vardır; bu, herhangi bir pencerenin bağımsız yeniden üretilebilmesini sağlar.

{{KOD izleme 2}}

Üçüncü parça ana fonksiyonun başıdır: model yüklenir, pencereler üretilir, her pencerede tahmin ve mAP hesaplanır. Referans istatistikleri (girdi parlaklığı ve skor dağılımı) pencere 0 ile 19 arasından çıkarılır.

{{KOD izleme 3}}

Dördüncü parça, her pencerede alarmları ve yeniden eğitim tetiğini belirler. Tetik kuralı basittir: girdi veya skor alarmı iki ardışık pencerede gelirse tetik çalışır ve insan onayına gönderilir. Performans alarmı ise etiket geldikçe devreye girer ve tetiğe dahil edilmez; onun rolü, tetiğin doğru olduğunu teyit etmektir.

{{KOD izleme 4}}

Beşinci parça, tetik çalıştıysa yeni bir modeli (eğitim ve kayma karışımı) eğitir ve tetikten sonraki pencerelerde eski ve yeni modelin mAP'lerini karşılaştırır. Son olarak sonuçları CSV'ye yazar.

{{KOD izleme 5}}

{{CIKTI izleme_ozet.txt python b80_izleme.py}}

Çıktıda `...` ile gösterilen satırlar kısaltmadır; tam çıktı CSV dosyasında bulunur. Çıktı, her pencerenin PSI, KS p değeri, mAP değeri ve üç alarm bayrağını verir. Alarm bayrakları girdi, skor ve performans için 1 ya da 0'dır.

### Ne zaman alarm verdi?

Tablo, kayma başlangıcından (pencere 20) sonra ilk alarmların geldiği pencereleri özetler.

| Pencere | Alfa | PSI | KS p | mAP | Olay |
|---|---|---|---|---|---|
| 20 | 0,00 | 0,025 | 0,554 | 0,919 | Kayma başlıyor (karışım sıfır) |
| 22 | 0,20 | 0,059 | 0,188 | 0,932 | Hâlâ alarm yok |
| 23 | 0,30 | 0,220 | 0,055 | 0,875 | PSI alarmı (girdi) |
| 24 | 0,40 | 0,296 | 0,004 | 0,910 | KS alarmı (skor); iki ardışık alarm, tetik |
| 26 | 0,60 | 0,561 | 0,0001 | 0,906 | Performans alarmı (etiketli pencere 23) |
| 30 | 1,00 | 3,654 | 0,000 | 0,910 | Tam kayma |

Referans mAP (pencere 0 ile 19 ortalaması) 0,937'dir. Performans alarmı, etiketli pencere 23'ün mAP'i (0,875) referansın 0,05 altına düştüğü için devreye girdi; düşüş 0,062'dir. Girdi alarmı pencere 23'te, skor alarmı ise pencere 24'te geldi. Kayma 20'de başladığı için tespit gecikmesi üç pencere oldu. Nominal pencerelerde (0 ile 22 arası) hiçbir alarm yoktur: yanlış alarm sayısı sıfırdır. R13 bu iki koşulu da geçti (gecikme <= 5 pencere, nominal alarm = 0).

Şekil 80.9, üç sinyali ve yeni modelin performansını birlikte gösterir. Gölgeli bölge kayma karışımının olduğu pencereleri (20 ile 30), kesikli çizgi ise tetiği (pencere 24) işaretler. PSI, kayma başladıktan sonra sert biçimde yükselir; KS p değeri pencere 26'dan itibaren neredeyse sıfıra düşer. Alt panelde, eski modelin mAP'i tam kayma altında 0,87 civarındadır; yeni model ise 0,91 civarında kalır.

![Şekil 80.9: Kayma izleme: PSI, KS p değeri ve eski ile yeni modelin mAP'i](gorseller/b80_drift.png)

### Yeniden eğitim: iyimser bir üst sınır

Tetikten sonra yeni bir model eğitildi. Eğitim verisi, yarısı nominal, yarısı kayma kümesinden (üreticinin aynı ayarlarından) oluşur. Pencere 24'ten 59'a kadar yeni modelin ortalama mAP'i 0,909, eski modelin ise 0,874'tür. Bu bir iyileşme, ama dürüst olmak gerekirse, bu sonuç iyimserdir. Simülasyonda kaymanın üretici tanımı biliniyor ve yeniden eğitim verisi aynı üreticiden geliyor. Gerçek bir sahada yeni model, yeni işaretlenmiş operasyonel veriyle eğitilmeli ve ayrı bir kümede ölçülmelidir. Bu sayı, yeniden eğitimin ne kadar kurtardığı değil, yeterli veri varsa neyin mümkün olabileceği hakkında bir üst sınırdır.

Bu noktada yeniden eğitim bir kalite kapısından (Bölüm 77.7) geçmelidir: yeni model, mevcut modelden doğrulama kümesinde iyi olmalı, kayma kümesinde kötüleşmemeli ve dağıtım öncesi insan onayını almalıdır. Bu bölümde kalite kapısını ayrıca kodlamadık; ama tetiğin çıktısı bir kapıya girmeli, doğrudan üretime gitmemelidir.
