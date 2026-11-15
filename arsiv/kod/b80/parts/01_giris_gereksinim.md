## Giriş: Kitabın son bölümü, tek bir sistem

Bu kitapta 79 bölüm boyunca parça parça şeyler öğrendik. Veri yapıları, algoritmalar, işletim sistemi, ağ, gömülü yazılım, matematik ve makine öğrenmesi ayrı ayrı anlatıldı. Bu bölümde hepsini tek bir sistemde bir araya getireceğiz. Sistem, bir İHA'nın gözetleme videosundan hava hedeflerini bulacak, onları kareler boyunca izleyecek, sonucu bir operatöre iz listesi olarak sunacak ve kendi performansını izleyecek.

Savunma sanayiinde bu tür bir sistemin karşılığı durumsal farkındalık (situational awareness) adıyla bilinir. Gözetleme kamerası bir şey görür, bilgisayar görüşü bunu tespit eder, takip bunun aynı nesne olduğunu korur, operatör de kararını verir. Mülakatlarda bu zincirin her halkası ayrı bir soru olarak çıkar; projede ise bu halkaların birbirine nasıl bağlandığı asıl iştir.

Sistemin hiçbir parçası gerçek bir İHA verisiyle ölçülmedi. Veri sentetik, donanım bir dizüstü bilgisayarın işlemcisi ve bir GPU, edge cihazı ise yalnızca bir vekil (proxy). Bu sınırları bölüm boyunca açıkça yazacağız. Sayılara güvenmenin yolu, hangi koşulda ölçüldüklerini bilmekten geçer.

::: not
Bu bölümde gösterilen tüm sayılar, bölümün betikleriyle yeniden üretilebilir. Betikler sabit tohum kullanır, ama GPU eğitiminde bit düzeyinde tekrarlanabilirlik yoktur; aynı kodu iki kez çalıştırınca test mAP@0,5 değerleri yaklaşık ±0,003 oynar. Sayılar ilk bakışta kesin görünse de, her sayının yanında belirsizliği de okumak gerekir.
:::

## 80.1 Gereksinimler: önce ne yapacağımızı yazmak

Bir mühendislik projesi kod yazmadan önce ne yapması gerektiğini yazar. Bu adım sıkıcı görünür, ama sonradan "başarılı oldu mu?" sorusunun cevabı buna bağlıdır. "Hedefi iyi tespit etsin" gibi bir cümle ölçülemez; ölçülemeyen bir gereksinim de kabul edilemez. Bu yüzden gereksinimleri en baştan sayısal kabul ölçütlerine çevireceğiz.

Görev tanımı şöyle: sentetik bir İHA gözetleme videosunda hava hedeflerini (daire, kare, üçgen) algılamak, kareler boyunca her birine sabit bir kimlik vermek ve bunu operatöre iz listesi olarak sunmak. Sistem, kendi güvenilmez olduğu durumları da işaretlemeli. Son olarak, veri dağılımı değiştiğinde bunu fark edip yeniden eğitim gerektiğini bildirmeli.

Bu görevin kapsamı sınırlıdır ve bilinçli olarak sınırlanmıştır. Bu bölümün 67.20 bölümündeki savunma bağlamı notunu tekrar edelim: sistem **algılama, takip, operatöre bilgi ve güvence** için vardır. Hedef seçimi, silahlandırma ya da angajman kararı bu sistemin işi değildir ve bu bölümde bu tür kararları destekleyen hiçbir yöntem anlatılmaz. Operatör her zaman karar vericidir.

Çalışma varsayımlarımızı açıkça yazalım, çünkü sonraki her sayının anlamı bunlara bağlıdır:

- **Veri:** Gerçek İHA görüntüsü yok. Veri, 96 x 96 piksel gri tonlu sentetik sahnelerden oluşur. Bölüm 67'deki sahne üreticisi genişletilir.
- **Donanım:** Eğitim RTX 3060 (6 GB) üzerinde yapılır. Edge ölçümü, bir dizüstü bilgisayarın CPU'sunda ONNX Runtime ile yapılır ve bu bir vekildir. Cortex-M ve Jetson sınıfı donanım ölçülmedi.
- **Kare hızı:** Operatör akıcı bir görüntü istiyorsa saniyede 30 kare hedeflenir. Bu, kare başına en fazla 33 ms demektir.
- **Kapsam:** Tek bir kamera, tek bir İHA, gerçek zamanlı çevrim içi öğrenme yok.

Gereksinimleri iki gruba ayıralım. İşlevsel gereksinimler sistemin **ne** yaptığını, işlevsel olmayanlar **ne kadar iyi** yaptığını söyler.

| No | Tür | Gereksinim |
|---|---|---|
| F1 | İşlevsel | Her karede hedefleri üç sınıfta (daire, kare, üçgen) algıla |
| F2 | İşlevsel | Kareler boyunca her hedefe kararlı bir kimlik ver |
| F3 | İşlevsel | Operatöre iz listesi ver; güvenilmez tespitleri "doğrulat" diye işaretle |
| F4 | İşlevsel | Girdi ve performans kaymasını izle; alarm ver |
| F5 | İşlevsel | Yeniden eğitimi otomatik değil, insan onayıyla tetikle |
| N1 | Doğruluk | Nominal veride mAP@0,5 yüksek olsun |
| N2 | Doğruluk | Operasyonel kaymada da kullanılabilir kalsın |
| N3 | Takip | Test videolarında MOTA yüksek, kimlik değişimi düşük olsun |
| N4 | Gecikme | Kare başına süre bütçede kalsın |
| N5 | Bellek | Model ve ara tamponlar makul sınırda olsun |
| N6 | Güvenilirlik | Güvence katmanı kapsamayı çok bozmadan yanlış alarmı düşürsün |
| N7 | Tekrarlanabilirlik | Model dışa aktarımı PyTorch ile aynı kutuları üretsin |

Bu gereksinimlerin her birini ölçülebilir bir kabul ölçütüne çevirmek gerekir. Tablo, her birine bir eşik ve bir ölçüm yöntemi verir. Eşikleri bu bölümün ölçümlerine bakmadan önce koyduk; bölümün sonunda hangilerinin tutulduğunu ayrıca göstereceğiz.

| Kod | Ölçü | Eşik | Nerede ölçülür |
|---|---|---|---|
| R1 | mAP@0,5, nominal test (3 tohum ort.) | >= 0,90 | 80.4 |
| R2 | mAP@0,5, operasyonel kayma (3 tohum ort.) | >= 0,80 | 80.4 |
| R3 | MOTA, nominal test videoları | >= 0,90 | 80.5 |
| R4 | Kimlik değişimi (IDSW) / GT sayısı | <= %1 | 80.5 |
| R5 | int8 kuantizasyonunda mAP@0,5 kaybı | <= 2 puan | 80.6 |
| R6 | int8 kuantizasyonunda mAP@[0,5:0,95] kaybı | <= 5 puan | 80.6 |
| R7 | Uçtan uca kare süresi p95, 96 px, 4 iş parçacığı | <= 33 ms | 80.6 |
| R8 | 640 px girdide ağın çıkarım süresi p95 (4 iş parçacığı) | <= 33 ms | 80.6 |
| R9 | Model dosyası (int8) | <= 1 MB | 80.6 |
| R10 | En büyük ara tampon (int8, 96 px) | <= 256 KB | 80.6 |
| R11 | OOD'de görüntü başına yanlış alarm, korumasıza göre azalma | >= %50 | 80.7 |
| R12 | Test kapsaması, korumasıza göre kayıp | <= 5 puan | 80.7 |
| R13 | Kayma alarmı gecikmesi ve nominal pencerelerde alarm sayısı | <= 5 pencere, 0 alarm | 80.8 |
| R14 | PyTorch ile ONNX kutu farkı (maks) | <= 1e-4 | 80.6 |

R7 ve R8 aynı eşiği taşıyor ama farklı bir şeyi ölçüyor. R7 96 piksellik girdi için uçtan uca hattın süresidir; R8 ise 640 piksellik girdi için yalnızca ağın çıkarım süresidir. İkincisini ekledik çünkü 96 piksel bir oyuncak boyutudur. Gerçek bir İHA görüntüsünde 8 ile 24 piksellik hedefler, 96 pikselde bir karede birkaç pikselden ibaret olur. Çözünürlük ile gecikme arasındaki bu gerilim sistemin en önemli tasarım kararıdır ve 80.6'da geri döneceğiz.
