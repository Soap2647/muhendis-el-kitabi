## 80.9 Doğrulama raporu: kabul ölçütleri ve model kartı

Gereksinimleri 80.1'de yazdık. Şimdi her birini ölçtüğümüz değerle karşılaştırıyoruz. Tabloda üç sütun var: ölçülen değer, eşik ve sonuç. Sonuç sütunu iki kelimeden biridir: GEÇTİ ya da KALDI. Bir ölçüm yapılamadıysa "ÖLÇÜLMEDİ" yazarız; bu, geçmek anlamına gelmez.

Burada hangi kalemin neden kaldığını açıkça yazmak önemlidir. Bir mühendislik raporunda kalanları gizlemek, geçenleri vurgulamaktan daha zararlıdır: okuyan, sistemin hangi koşullarda güvenilmez olduğunu bilmeden kullanır.

| Kod | Gereksinim | Ölçülen | Eşik | Sonuç |
|---|---|---|---|---|
| R1 | Nominal mAP@0,5 | 0,937 ± 0,004 | >= 0,90 | GEÇTİ |
| R2 | Kayma mAP@0,5 | 0,875 ± 0,006 | >= 0,80 | GEÇTİ |
| R3 | Test MOTA | 0,814 | >= 0,90 | KALDI |
| R4 | IDSW / GT (test) | 24 / 1 735 = %1,4 | <= %1 | KALDI (nokta tahmini; %95 aralık eşiği kapsıyor) |
| R5 | int8 mAP@0,5 kaybı (test) | 1,1 puan | <= 2 puan | GEÇTİ |
| R6 | int8 mAP@[0,5:0,95] kaybı (test) | 9,5 puan | <= 5 puan | KALDI |
| R7 | Uçtan uca p95, 96 px, 4 iş p. | 1,09 ms | <= 33 ms | GEÇTİ (yalnız 96 px) |
| R8 | 640 px ağın çıkarım p95, 4 iş p. | 3,08 ms | <= 33 ms | GEÇTİ (yalnız ağ) |
| R8b | 640 px uçtan uca p95 | ÖLÇÜLMEDİ | <= 33 ms | ÖLÇÜLMEDİ |
| R9 | int8 model dosyası | 71 173 bayt | <= 1 MB | GEÇTİ |
| R10 | En büyük ara tampon, 96 px | 36 864 bayt | <= 256 KB | GEÇTİ |
| R10b | En büyük ara tampon, 640 px | 1 638 400 bayt | <= 256 KB | KALDI |
| R11 | OOD yanlış alarm azalması | Tek skor %79, tohum uyumu %96 | >= %50 | GEÇTİ |
| R12 | Test kapsama kaybı | Tek skor 3,2 puan, tohum uyumu 7,7 puan | <= 5 puan | GEÇTİ (tek skor) / KALDI (tohum uyumu) |
| R13 | Kayma alarmı gecikmesi ve nominal alarm | 3 pencere, 0 alarm | <= 5, 0 | GEÇTİ |
| R14 | ONNX ile PyTorch kutu farkı | 8,0e-6 | <= 1e-4 | GEÇTİ |

Sayım dürüst olmak gerekirse şöyle: on bir ölçüm geçti (R12'de yalnızca tek skor kuralı için). Beş kalem kaldı: test MOTA (R3), kimlik değişimi (R4), int8 lokalizasyon kaybı (R6), 640 px ara tamponu (R10b) ve tohum uyumu kuralının kapsama kaybı (R12). Bir kalem ölçülmedi: 640 px uçtan uca gecikme (R8b).

R3 ve R4'ün kaldığı nedenleri 80.5'te gösterdik: kaçırmalar (kenar ve küçük hedefler), kuş benzeri OOD nesnelerinden gelen yanlış izler ve kesişmede kimlik değişimi. R6'nın kaldığı nedenin bir hipotezi var (kafa katmanında üstel kodlama ve kuantizasyon hatası), ama bunu doğrulamadık. R10b ise bir mimari seçimin sonucudur: 640 pikselde ara tampon, mikrodenetleyici sınıfı belleğin dışındadır.

Kalan sorunlar bir "tamamlandı" işaretini hak etmez. Bu, sistemin hangi koşullarda kullanılabileceğini belirleyen bir çıktıdır. Operatöre verilecek bir sistemin sınırları bu tabloda yazılı olmalıdır.

### Model kartı

Model kartı, bir modelin ne için yapıldığını, neyle eğitildiğini, nerede güvenilmez olduğunu ve kimin sorumlu olduğunu tek bir sayfada anlatan belgedir. Bölüm 77'deki izlenebilirlik düşüncesinin son adımıdır. Aşağıdaki kart, bu sistemin dedektörü için yazılmıştır.

| Alan | Değer |
|---|---|
| Amaç | Sentetik gözetleme videosunda hava hedeflerini algılamak ve izlemek; operatöre iz listesi ve güvence işareti sunmak |
| Kapsam dışı | Hedef seçimi, silahlandırma, angajman ve sınıflandırmanın yerine geçen karar; insan operatörün yerine karar verme |
| Mimari | MiniYolo: 4 konvolüsyon bloğu (BatchNorm ve ReLU), 1 x 1 kafa; 61 440 parametre; 12 x 12 ızgara, 2 anchor, 3 sınıf |
| Girdi | 96 x 96 piksel, gri tonlu, değerler 0..1 |
| Eğitim verisi | Sentetik, 3 000 sahne, tohum 0, EGITIM ayarı (aydınlatma, gürültü, bulanıklık, ölçek) |
| Eğitim | AdamW, en yüksek öğrenme oranı 2e-3, OneCycle, 60 epoch, yığın 64; tohumlar 1, 2, 3; GPU RTX 3060 (6 GB) |
| Ölçüm | Nominal test (500 sahne), kayma (500), sert kayma (500), OOD (500, kuş eklenmiş), videolar (5 x 120 kare) |
| Bilinen sınırlar | Sentetik veri; 96 px çözünürlük; üç sınıf; kuş benzeri OOD yalnızca bir şekil ailesi; kayma üreticinin tanımıyla simüle edildi |
| Bilinen hatalar | int8'de kutu hassasiyeti düşer (R6); kenar ve küçük hedefler kaçırılır; kuşlar FP üretir; kesişmede IDSW |
| Güvence | Tohum uyumu ya da skor eşiği ile "doğrulat" işareti; eşikler yalnızca doğrulama kümesinde seçildi |
| Sürüm izi | yolo_t1.pt ve yolo_int8.onnx; int8 model SHA-256 özeti (ilk 16 karakter) 34f1c9ef6dac1a5b |
| Ortam | Windows 11; Python 3.12.10; PyTorch 2.6.0+cu124; ONNX Runtime 1.25.1; ONNX 1.23.2; NumPy 2.3.5 |
| Sorumlu | Proje sahibi; yeniden eğitim yalnızca insan onayıyla yayınlanır |

Model kartındaki "bilinen hatalar" satırı, bir modelin kendi raporudur. Kullanıcının beklentisini modelin gerçek kapasitesine uydurmak için vardır. Bu satır olmadan okuyan, modelin her sahnede çalıştığını varsayar.

### Deney kaydı

Son olarak Bölüm 77.5'teki deney takipçisine kayıt. Her tohum için bir deney satırı, parametreler, metrikler ve model dosyasının özeti yazılır. Bu kayıt, bir sonraki koşuda sonuçların neden değiştiğini sorgulamamızı sağlar.

{{KOD kayit 1}}

Kayıt betiği, `Takip` sınıfını Bölüm 77'den kullanır. Kodun ikinci parçası üç tohum için deneyi ve metriklerini yazar.

{{KOD kayit 2}}

Son parça betiğin giriş noktasıdır; sıralanmış sonuçları yazdırır.

{{KOD kayit 3}}

{{CIKTI kayit.txt python b80_kayit.py}}

Çıktıda deneyler test mAP@0,5 değerine göre azalan sırada listelenir. Üç tohum arasındaki sıralama, ortalamayı değiştirmez; yalnızca sonuçların ne kadar dağıldığını gösterir. Bu sıralamaya bakarak "en iyi tohumu" seçmek, bir test kümesine göre seçim yapmak olur. Edge hattına yalnızca tohum 1 aktarıldı. Tohum uyumu kuralını edge'de kullanmak için tohum 2 ve 3'ün de ONNX'e aktarılması ve birlikte ölçülmesi gerekir. Bu bölümde tohum uyumu yalnızca PyTorch ile ölçüldü; edge karşılığı açık bir iştir.
