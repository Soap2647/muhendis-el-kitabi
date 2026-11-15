## 80.2 Mimari: parçalar, sözleşmeler ve hatalar

Sistemi bir zincir olarak düşünmek kolaydır, ama gerçek sistemler zincir değil, birbirine veri gönderen kutulardan oluşur. Her kutunun girdisi ve çıktısı belli olmalıdır; bu belirleme **veri sözleşmesi** olarak adlandırılır. Sözleşme yazılmazsa, bir kutunun değişikliği diğerini sessizce bozar. Bölüm 46.7'deki uçta ön işleme ile Bölüm 77.8'deki eğitim ve servis çarpıklığı aynı sorunu anlatır: eğitimdeki ön işleme ile çıkarımdaki ön işleme farklıysa model hata vermeden kötüleşir.

Şekil 80.1, uçtan uca yaşam döngüsünü gösterir. Veri üretiminden başlayıp eğitime, değerlendirmeye, dışa aktarmaya ve edge hattına uzanır. Edge hattından gelen bilgi operatöre gider, izleme ise kayma olup olmadığına bakar ve gerekiyorsa yeniden eğitimi tetikler.

![Şekil 80.1: Uçtan uca yaşam döngüsü: veriden operatöre ve geri bildirime](gorseller/b80_mimari.png)

Edge hattının içi Şekil 80.2'de görünür. Her ok bir veri sözleşmesidir ve her sözleşmenin biçimi kutunun içine yazılmıştır. Bu şekil, sistemin en kritik yerini gösterir: kare, ön işlemeye girdiğinde uint8 ile gelir ve float32'ye dönüşürken aralığı [0, 1] olarak sabitlenir. Eğitimde de aynı dönüşüm kullanılır; bu tutarlılık sistem düzeyinde bir gereksinimdir.

![Şekil 80.2: Edge çıkarım hattı ve her aşamanın veri sözleşmesi](gorseller/b80_hat.png)

Sözleşmeleri tablo hâline de getirelim. Bu tablo, bir arayüz değiştiğinde hangi kutuların etkileneceğini gösterir.

| Arayüz | Veri | Biçim ve aralık | Sıklık |
|---|---|---|---|
| Sensör -> ön işleme | Kare | 96 x 96, uint8, 0..255 | 30 kare/s |
| Ön işleme -> dedektör | Tensör | (1, 1, 96, 96), float32, 0..1 | Kare başına |
| Dedektör -> son işleme | Ham çıktı | (1, 12, 12, 16), float32, sınırsız | Kare başına |
| Son işleme -> takipçi | Kutular | (N, 4) xyxy piksel, skor, sınıf | Kare başına |
| Takipçi -> güvence | İz listesi | (id, kutu) ve geçmiş isabet sayısı | Kare başına |
| Güvence -> operatör | Alarm | Kimlik, kutu, skor, "otomatik" veya "doğrulat" | Olay bazlı |
| Edge -> izleme | Özet | Pencere başına girdi istatistiği ve skor dağılımı | Pencere başına |
| İzleme -> eğitim | Tetik | Tarih, pencere aralığı, alarm türü, insan onayı | Olay bazlı |

Son satır bir insan onayı gerektirir. Bu tasarım kararı bilinçlidir: bir izleme alarmı bir modelin otomatik olarak yeniden eğitilip yayınlanması anlamına gelmez. Bölüm 77.11'de yeniden eğitim politikalarını tartıştık; burada politikayı basit tuttuk: iki ardışık alarm, bir insan onayı.

### Hata modları ve etkileri (FMEA)

Mühendislikte bir sistemin nasıl bozulacağını önceden yazmak, bozulduğunda şaşırmamanın yoludur. FMEA (Failure Mode and Effects Analysis), her hata modu için etkiyi, tespit yolunu ve önlemi bir tabloda toplar. Aşağıdaki tablo kısadır; amaç yöntemi göstermektir.

| Hata modu | Etki | Tespit | Önlem |
|---|---|---|---|
| Kamera kontrastı düşer (sis, yansıma) | Tespit kaçırır, mAP düşer | PSI ve KS alarmı (80.8) | Yeniden eğitim tetiği, insan onayı |
| Küçük hedefler kaçar | FN artar, MOTA düşer | MOTA ve FN takibi (80.5) | Çözünürlük seçimi (80.6) |
| Kuş veya gölge tespit edilir | Yanlış alarm (FP) | OOD testi, tohum uyumu (80.7) | Güvence: "doğrulat" işareti |
| İki hedef kesişir | Kimlik değişimi (IDSW) | Kimlik takibi (80.5) | Macar eşleştirme, kayıt |
| int8 modelde bozulma | Lokalizasyon hatası | PyTorch ile eşleşme testi (80.6) | Kabul kapısı (R5, R6) |
| Model dosyası bozulur veya yanlış sürüm yüklenir | Tahmin tamamen yanlış | SHA-256 kontrolü (77.4) | Kayıt defteri ve özet doğrulaması |
| Kare süresi bütçeyi aşar | Kare atlanır, takip kopar | Kare süresi p95 izleme (80.6) | Kare atlama politikası, model küçültme |
| Yanlış veriyle yeniden eğitim | Model kötüleşir | Kalite kapısı (77.7) | Eğitim öncesi veri doğrulama |

Tabloda bir eksik var: model dosyası ve veri kaynağının güvenliği. Bölüm 32'deki savunma odaklı güvenlik ilkeleri bu noktada devreye girer. Eğitilmiş bir modeli pickle ile yüklemek, güvenilmeyen bir kaynaktan gelen kodu çalıştırmak demektir. Bu yüzden model dosyalarını ONNX ya da state_dict olarak taşıyor ve yüklemeden önce özetini kontrol ediyoruz.
