## Kendin Yap Projeleri

::: dikkat
Bu iki projeyi yapay zekâ aracı olmadan yap. Önce kağıt üzerinde tasarımı çiz, veri akışını elle izle, sonra kodla. MLflow ya da DVC gibi hazır araçları kullanma; amacın bu bölümün küçük araçlarını genişletmek ve bunun neden zor olduğunu görmek.
:::

### Proje 1 (★★): Veri kökeni (lineage) izleyicisi

**Amaç.** Türev verilerin hangi ham verilerden üretildiğini kaydeden, ham veri değiştiğinde eskiyen türevleri ve onlara bağlı deneyleri bulan bir araç yazmak.

**Yapılacaklar / beklenen davranış.** Her türev dosya için üst dosyaların özetlerini ve üretim betiğinin commit kimliğini tutan bir `kaynak` tablosu oluştur. Bu bağlardan bir yönlü çevrimsiz graf (DAG) kur. Zincirin herhangi bir düğümü değiştiğinde, o düğümden erişilebilen bütün alt düğümleri "eskidi" olarak işaretle. Deney takipçisindeki `veri` alanının zincirdeki hangi düğüme karşılık geldiğini de gösterebilmelisin. Üç katmanlı bir zincir (ham, temiz, özellik) ile sına.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Düğümleri özetleriyle adresle, kenarları `(ust_ozet, alt_ozet, betik_commit)` üçlüsü olarak tut. Eskime taraması için Bölüm 17'deki DFS ya da topolojik sıralama doğrudan kullanılabilir. Döngü olmadığını varsay ama bir kez kontrol et; kontrol edilmeyen döngü sonsuz taramaya yol açar.

**Başarı kriterleri.** (a) Üç katmanlı zincirde ham dosyanın tek bir baytı değiştiğinde alt iki katman eskidi olarak işaretlenir ve ilgisiz bir dosya işaretlenmez. (b) Türev yeniden üretildiğinde sonucun özeti beklenen özetle eşleşir. (c) En az 20 rastgele zincirde, her biri için beklenen eskime kümesi elle hesaplanmış kümeyle birebir aynıdır. (d) Kod 70 sütunu aşmaz ve testleri vardır.

### Proje 2 (★★★): İHA telemetri modeli için uçtan uca izleme ve yeniden eğitim hattı

**Amaç.** Bu bölümdeki parçaları (77.4'ten 77.11'e kadar) tek bir çalıştırılabilir hatta birleştirmek. Her gün yeni bir telemetri partisi gelir; hat veriyi doğrular, eğitir, kapıdan geçirir, kayıt defterine koyar, kaymayı izler ve tetiklemeli politikaya göre yeniden eğitir. Her karar bir denetim kaydına yazılır.

**Yapılacaklar / beklenen davranış.** Önce 100 günlük bir parti simülatörü yaz: her gün 300 satır, ortam ve katsayı kayması 40. günden itibaren kademeli artsın. Her gün sırasıyla şunları yap: veri denetimi, kayma metrikleri, gecikmeli performans, kalite kapısı, kayıt ve denetim günlüğü. Yeniden eğitim tetiklenirse önceki model korunmalı ve yalnızca kapıdan geçen aday production'a alınmalıdır. Hat tek komutla (`python hat.py`) çalışsın ve aynı tohumla iki kez çalıştığında bayt bayt aynı denetim günlüğünü üretsin. Dört politikayı (hiç, 10, 30 ve tetikli) aynı hatla üç tohumda karşılaştır ve hangi politikanın neden kazandığını yazılı açıkla.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Her adımı girdi ve çıktısı açık bir fonksiyon yap, sonra hepsini bir `gunluk_dongu(gun, durum)` içinde çağır. Denetim günlüğünü JSON satırları olarak ekle ve yalnızca ekleme yap (append-only); eski satırlar asla değişmez. "Kapı reddederse önceki model korunur" kuralını ayrı bir testle kanıtla. Maliyet birimlerini bir yapılandırma dosyasına taşı, böylece değiştirildiğinde sonucun nasıl değiştiğini görebilirsin.

**Başarı kriterleri.** (a) Üç tohumda da hat hatasız tamamlanır ve her gün için denetim kaydı vardır. (b) Aynı tohumla iki çalıştırma aynı denetim günlüğünü üretir. (c) Kapı reddettiğinde üretim modeli değişmez; bunu bir test kanıtlar. (d) Maliyet ve yeniden eğitim sayısı üç tohumun ortalaması ve standart sapmasıyla raporlanır. (e) Maliyet birimleri değiştirildiğinde kararların değişip değişmediği raporlanır.

### Ek Alıştırmalar

1. ★ PSI'de bir kutunun oranı sıfır olduğunda formül ne olur? Koddaki 0,0001 alt sınırı sonucu nasıl etkiler, bunu iki farklı değerle dene.
2. ★ Deney takipçisinde aynı parametrelerle iki koşu yapılırsa tablo ne gösterir? Bu, tekrarlanabilirlik hakkında ne söyler?
3. ★ Veri özetinde SHA-256 yerine MD5 kullanmanın hangi riski vardır? Bölüm 9'daki çarpışma fikrini kullanarak açıkla.
4. ★★ Kalite kapısında önyükleme sayısı B = 1000 yerine B = 100 kullanılırsa %2,5 alt sınır kararlı kalır mı? Üç tohumla gözlemle.
5. ★ Bir modelin etiketi yalnızca 30 gün sonra geliyorsa, performans alarmı hangi gecikmeyle çalışır? Gecikmenin tespit süresine etkisini yaz.
6. ★★ Kanarya payı yüzde 2'den yüzde 10'a çıkarsa Örnek 3'teki gün sayısı nasıl değişir? Bu artışın bedeli nedir?
7. ★★ (Mülakat) Bir sistemde her gün 200 özellik için PSI hesaplanıyor. Yanlış alarm oranını nasıl yönetirsin? Çoklu karşılaştırma düzeltmesini düşün.
8. ★★ (Mülakat) Eğitim ve servis aynı dönüşüm fonksiyonunu çağırıyor, ama servise gelen veri yeni bir yazılım sürümünde farklı bir birimle kaydediliyor. Bu tür bir çarpıklık nasıl fark edilir?
9. ★★★ (Mülakat) Bir savunma sisteminde bir modelin sürüm izlenebilirliği nasıl kanıtlanır? Bu bölümdeki hangi bileşenler çekirdektir, hangi eksikleri kapatman gerekir?
10. ★ Kayıt defterinde production sürümü arşive taşınırken hata olursa hangi durum oluşur? Bu işlemi atomik yapmak için ne gerekir?
11. ★★ (Mülakat) Gölge dağıtımda adayın gecikmesi taban modelden yüzde 40 yüksek çıkıyor. Gecikme ölçümünde p50 mi p99 mu daha önemlidir ve neden?
12. ★★ Kalite kapısı, veri doğrulama ile birlikte hangi hataları kaçırabilir? Her biri için bir örnek ver.

## Kod Okuma Egzersizi

Aşağıdaki kesit, scipy 1.17.1 kütüphanesinin yerel kurulumundaki `ks_2samp` fonksiyonudur. Dosya `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\scipy\stats\_stats_py.py` konumundadır ve 7948. satırdan 7969. satıra kadar birebir alınmıştır. Kısaltma ya da sadeleştirme yapılmadı. Bu kesit, KS istatistiğinin nasıl hesaplandığını gösterir; Bölüm 77.10'da kullandığımız p değeri ise bu fonksiyonun devamında hesaplanır.

{{KAYNAK C:/Users/merty/AppData/Local/Programs/Python/Python312/Lib/site-packages/scipy/stats/_stats_py.py 7948 7969}}

**Sorular — cevaplamadan geçme:**

1. `data1` ve `data2` neden önce sıralanıyor? Sıralama olmadan `searchsorted` neden yanlış bir ampirik dağılım verir?
2. `searchsorted(..., side='right')` kullanılmasının eşit değerlerdeki etkisi nedir? Kaynaktaki yorumun neden söz ettiği konuyu açıkla.
3. `cddiffs = cdf1 - cdf2` ifadesi KS istatistiğinin hangi tanımına karşılık gelir? İki yönlü test için neden hem `minS` hem `maxS` hesaplanıyor?
4. `np.clip(-cddiffs[argminS], 0, 1)` satırında neden `clip` var? Hangi durumda negatif bir değer üretilebilir?
5. Büyük örneklerde (on milyonlarca eleman) en pahalı adım hangisidir? `np.sort` ile iki `searchsorted` çağrısının maliyetini karşılaştır.
6. Bölüm 77.10'daki KS hesabımız `ks_min_p` için bu fonksiyonun p değerini kullanır. Pencere büyüklüklerimizde (600 ve 2000) `method='auto'` hangi yöntemi seçer, kaynakta bu kuralı bul ve açıkla.

## Bölüm Özeti

- ML sistemi kod, veri ve modelden oluşur. Modelin kodu sistemin küçük bir parçasıdır; geri kalanı teknik borç olarak birikir (Sculley ve ark. 2015, genel bilgi).
- Tekrarlanabilirlik dört bilgiye dayanır: kod sürümü, veri özeti, ortam kilidi ve tohum. Biri eksikse sonuç yeniden üretilemez.
- İçerik-adresli depolama, veriyi SHA-256 özetiyle adresler. Git'e yalnızca küçük işaretçi girer ve bozulma özet kontrolüyle yakalanır.
- Deney takipçisi her koşuyu kod, veri ve ortamla bağlar. Küçük AUC farkları tohum belirsizliğinin içinde kalabilir; tek koşuya bakıp karar verme.
- Kayıt defteri sürümleri ve aşamaları tutar. Yüklemede özet doğrulanır, geri alma eski sürümü production'a döndürür.
- Kalite kapısı ve veri doğrulama bozuk modelin ve partinin yayınlanmasını engeller. Kapı küçük bozulmaları her zaman yakalamaz; bu bir sınırdır ve bilinmelidir.
- Eğitim/servis çarpıklığı hata vermeden doğruluğu düşürür. Tek kaynak dönüşüm ve tahmin dağılımı izlemesi bunu önler.
- Kayma türleri farklı yöntemlerle yakalanır: PSI, KS ve alan sınıflandırıcısı etiketsiz kovaryat kaymasını, performans alarmı kavram kaymasını yakalar. Yeniden eğitim politikası bir maliyet kararıdır.

**Sonraki bölümde:** Bölüm 78'de (Güvenilir ve Güvenli AI) bu bölümde kurduğumuz izlenebilirlik zincirinin neden tek başına yetmediğini göreceğiz. Model, saldırılara karşı dayanıksız olabilir, belirsizliğini bildirmeyebilir ve kararlarını açıklayamayabilir. Savunma sanayiinde bu eksikler, sertifikasyon sürecinin asıl konusudur. Bu bölümdeki sürüm izlenebilirliği, o tartışmanın ön koşuludur.

::: mulakat
1. Üretimdeki bir model %10 daha kötü çalışıyor, ama kayıtlarda hiçbir hata yok. Hangi üç veriye, hangi sırayla bakarsın?
2. Eğitim ve servis aynı dönüşüm fonksiyonunu çağırıyor. Bu yeterli mi? Hangi durumda yine de çarpıklık oluşur?
3. Bir veri dosyasının adı aynı, içeriğinde tek bir bayt değişti. Git bunu nasıl görür ve büyük bir ikili dosya için bu neden yetersizdir?
4. Kalite kapısı yeni modeli reddetti, ama ekip modelin iyi olduğuna inanıyor. Tartışmada kapının hangi parametresine bakarsın ve neden?
5. Kanarya dağıtımı yüzde 1 trafikle başladı ve iki gün sonra hata oranında belirgin bir fark yok. Bu, adayın güvenli olduğu anlamına gelir mi?
6. Yeniden eğitimin maliyeti 60, yanlış negatifin maliyeti 5 birim. Kaç yanlış negatif bir yeniden eğitimi haklı çıkarır? Bu hesabın dayandığı varsayımları say.
7. Bir model dosyasını bir arkadaşından `pickle` ile aldın. Yüklemeden önce hangi üç şeyi kontrol edersin?
:::
