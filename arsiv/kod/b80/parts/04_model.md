## 80.4 Model: eğitim, temel çizgi ve mAP

Dedektör olarak Bölüm 67.10'daki küçük tek aşamalı ağı (`MiniYolo`) yeniden kullanıyoruz. Ağ 96 x 96 girdiyi üç kez ikiye bölerek 12 x 12'lik bir ızgaraya indirir; her hücrede iki anchor ve üç sınıf için tahmin üretir (Bölüm 67.8 ve 67.9). Kayıp fonksiyonu üçe ayrılır: nesnellik (BCE, pozitiflere üç kat ağırlık), kutu (MSE) ve sınıf (çapraz entropi). Kutu ve sınıf kaybı yalnızca pozitif hücrelerde hesaplanır. Bu tasarımın gerekçesi Bölüm 67'de ayrıntılı olarak anlatıldı; burada yeniden türetmeyeceğiz.

Eğitim ayarları Bölüm 64'teki pratiklerle uyumludur: AdamW, en yüksek öğrenme oranı 2e-3, OneCycle takvimi, 60 epoch ve 64'lük yığın. Üç tohum (1, 2, 3) aynı veriyle eğitilir. Üç tohum, tek bir koşunun şansını değil, yöntemin tutarlılığını ölçer; sonuçları ortalama ± standart sapma olarak raporlarız (Bölüm 57).

Kodun ilk parçası, klasik temel çizgiyi tanımlar. Bu temel çizgi bir öğrenme yöntemi değil, bir kural setidir: sabit bir eşikle ikili görüntü üretir, bağlı bileşenleri bulur ve her bileşenin doluluk oranına bakarak sınıfını seçer. Dolu bir daire bbox alanının yaklaşık yüzde 78,5'ini, kare yüzde 100'ünü, üçgen yaklaşık yüzde 50'sini kaplar. Bu basit kural, veri kendi içinde ayırt edilebilir olduğunda ne kadar yol alabileceğimizi gösterir.

{{KOD egit 1}}

Kodun ikinci parçası bu temel çizgiyi tanımlar. Dikkat edilecek nokta, skorun bileşenin ortalama parlaklığı olmasıdır; bu, tespitleri mAP hesabında sıralayabilmek için gereklidir. Bir eşik değeri (0,45) elle seçilmiştir ve bu seçim doğrulama kümesine bakılarak değil, arka plan ve nesne parlaklıklarının ortasına bakılarak yapılmıştır. Kayma kümesinde bu eşik çöker; bunu aşağıda göreceğiz.

{{KOD egit 2}}

Ana fonksiyon beş kümeyi üretir (doğrulama, test, kayma, sert kayma, OOD), klasik temel çizgiyi her birinde değerlendirir, sonra üç tohumla eğitip her birini aynı kümelerde ölçer. Her koşunun süresi ve GPU adı yazılır; süre ölçümleri tek koşudur ve bir sistematik kıyas değildir. Eğitimden önce kartın boşta olduğu `nvidia-smi` ile doğrulandı (kullanım yüzde 0 ile 10 arasında).

{{KOD egit 3}}

Kodun son parçası, tahminleri ve ölçümleri diske yazar. Tahminleri pickle ile saklamamızın nedeni, sonraki betiklerin (güvence, izleme) aynı tahminleri yeniden hesaplamadan kullanabilmesidir.

{{KOD egit 4}}

{{CIKTI egit.txt python b80_egit.py}}

### Sonuçlar

Tablo, iki yöntemin beş kümedeki mAP@0,5 ve mAP@[0,5:0,95] değerlerini verir. CNN satırı üç tohumun ortalamasıdır.

| Küme | Klasik mAP@0,5 | CNN mAP@0,5 | Klasik mAP@[0,5:0,95] | CNN mAP@[0,5:0,95] |
|---|---|---|---|---|
| Doğrulama | 0,597 | 0,936 ± 0,007 | 0,510 | 0,640 |
| Test (nominal) | 0,601 | 0,937 ± 0,004 | 0,523 | 0,638 |
| Operasyonel kayma | 0,202 | 0,875 ± 0,006 | 0,091 | 0,543 |
| Sert kayma (kontrol) | 0,004 | 0,067 ± 0,007 | 0,002 | 0,030 |
| OOD (kuş eklenmiş) | 0,443 | 0,883 ± 0,015 | 0,384 | 0,599 |

Birinci satır şunu söyler: doğrulama ve test değerleri birbirine çok yakın. Eşikleri ve takip modunu doğrulama kümesinde seçtiğimiz için, test kümesindeki bu yakınlık bir aşırı uyum (overfitting) göstergesi değildir. R1 (nominal mAP@0,5 >= 0,90) geçildi: 0,937 ± 0,004.

Operasyonel kaymada klasik temel çizgi 0,20'ye düşer, CNN ise 0,87'de kalır. Kayma, arka plan parlaklığını yükseltir ve kontrastı düşürür; sabit bir eşik bu durumda bir nesneyi arka plandan ayıramaz. CNN'in bunu öğrenmesinin nedeni, eğitimde aynı genişlikte bir aydınlatma çeşitliliği görmesidir. Bu bir avantajdır, ama bir uyarı da içerir: model, eğitimde gördüğü aralığın dışında ne kadar güvenilir kalır? Sert kayma kontrolü bu soruyu cevaplar. Her iki yöntem de 0,07'nin altına düşer. Yani eğitim dağılımının çok dışına çıkıldığında model sessizce bozulur. Bu nedenle R2'yi (operasyonel kayma >= 0,80) geçmek yeterli değildir; izleme ve güvence katmanına ihtiyacımız vardır (80.7 ve 80.8).

OOD satırı, kuş benzeri şekillerin dedektörü ne kadar yanılttığını gösterir. OOD kümesinde mAP 0,883'e düşer, çünkü kuşlar yanlış alarm (FP) olarak sayılır. Bu düşüş, güvence katmanının neden gerektiğinin en açık kanıtıdır.

Ölçümlerin belirsizliğine dair bir not. Aynı kodla yapılan iki eğitim koşusunda test mAP@0,5 ortalaması 0,9357 ve 0,9374 çıktı. Fark, GPU'nun bit düzeyinde tekrarlanabilir olmamasından kaynaklanır (cuDNN çekirdekleri her koşuda farklı sırayla toplama yapabilir). Bu nedenle sonuçlar arasındaki yaklaşık ±0,003 fark bilgi taşımaz; bu bölümdeki karşılaştırmaların hepsi bu gürültünün çok üzerindedir.

Son olarak deneyin kaydı. Bölüm 77.5'teki SQLite deney takipçisi, her tohumun parametrelerini, metriklerini ve model dosyasının özetini tutar. Bu kayıt betiğini 80.9'da çalıştıracağız; şimdi, şekli üreten veri hazırlık betiğine bakalım.

{{KOD ornek 1}}

Bu betik, şekil için üç kümeden üç örnek sahne ve seed-1 modelinin tespitlerini tek bir dosyaya yazar. Dosya, çizim betiğinin Temp klasörüne bağımlı olmadan çalışmasını sağlar.

{{KOD ornek 2}}

{{CIKTI ornek.txt python b80_ornek.py}}

Şekil 80.4, bu örnekleri gösterir. Kırmızı kutular modelin tespitleri (skor en az 0,30), kesikli yeşil kutular gerçek kutulardır. Nominal sahnelerde kutular gerçeğe çok yakındır. Kayma satırında bazı nesneler kaçırılır ve bir tanesinde skor düşüktür. OOD satırında kuş, bir ya da iki kırmızı kutuyla yanlış alarm üretir.

![Şekil 80.4: Tespit sonuçları: nominal, kayma ve OOD (kırmızı: tespit, kesikli yeşil: gerçek)](gorseller/b80_tespit.png)
