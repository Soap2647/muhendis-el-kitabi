## 80.6 Edge dağıtım: katla, dışa aktar, küçült, ölç

Eğitilmiş bir model laboratuvarda işe yarar; edge'de ise üç şey daha ister. Birincisi, eğitim çatısından bağımsız bir biçim (ONNX), ikincisi daha küçük sayılar (int8), üçüncüsü ise kanıtlanmış bir süre bütçesi. Bölüm 75'te bu üç adımı teoriyle gördük; burada bunları tek bir hatta birleştiriyoruz ve her adımın bedelini ölçüyoruz.

İlk adım BatchNorm'u katlamaktır. Eğitimde BatchNorm, her kanalın ortalamasını ve varyansını kullanarak normalizasyon yapar; çıkarımda bu istatistikler sabittir. Bu yüzden Conv ile BN ardışık ise, BN'nin doğrusal dönüşümü Conv'un ağırlıklarına ve sapmasına gömülebilir. Bölüm 75'teki formül şöyledir: s = gamma / sqrt(var + eps); W' = W * s; b' = beta - mu * s. Katlama sonrası ağ BN içermez ve bir katman daha az çalıştırılır. Kodun ilk parçası sınıfları ve katlama fonksiyonunu tanımlar.

{{KOD onnx 1}}

Kodun ikinci parçası, katlanmış ağırlıkları yeni bir `Dagitim` modülüne yükler. Bu modül yalnızca Conv, ReLU ve son 1 x 1 kafa katmanından oluşur. Orijinal `MiniYolo` ile yeni modül arasındaki sayısal fark, katlamanın doğruluğunu ölçer.

{{KOD onnx 2}}

Üçüncü parçada modülün ileri geçişi ve ham çıktıyı Bölüm 67'deki kod çözme biçimine çeviren `ham_to_cikti` fonksiyonu yer alır. Bir ağ çıktısının düzeni, son işlemenin doğru çalışması için bir sözleşmedir; burada sözleşme "kanal sırası = anchor x (5 + sınıf)" biçimindedir. `Veri` sınıfı ise statik kuantizasyon için kalibrasyon verisini sağlar.

{{KOD onnx 3}}

Dördüncü parça, ONNX Runtime oturumunu iş parçacığı sayısıyla yapılandırır ve ONNX çıktısını aynı `decode` fonksiyonundan geçirerek PyTorch ile karşılaştırılabilir kutulara dönüştürür. Bu ortak son işleme, iki yolun farkını yalnızca ağa bağlar.

{{KOD onnx 4}}

Beşinci parça, katlamanın sayısal doğruluğunu ölçer ve modeli ONNX'e aktarır. Dışa aktarmada yükseklik ve genişlik eksenlerini dinamik bırakıyoruz; aksi hâlde 96 px'te donmuş bir graf, 640 px senaryosunu ölçmemize izin vermezdi. Bu küçük bir karardır ama sonradan 80.6'nın ikinci yarısında önem kazanır.

{{KOD onnx 5}}

Altıncı parça statik int8 kuantizasyonu yapar. QDQ biçimi, her tensörün etrafına QuantizeLinear ve DequantizeLinear düğümleri koyar. Ağırlıklar kanal başına simetrik int8, aktivasyonlar tensör başına asimetrik uint8 olarak kuantize edilir. Kalibrasyon için kullanılan 200 sahne, eğitimden ve test kümelerinden farklı bir tohumdan (4242) gelir; böylece kuantizasyon aralıkları test verisini görmez.

{{KOD onnx 6}}

Son parça ölçüm çıktısını ve kutu farkını yazar. Bu dosyadaki `quantize_static` çağrısı, ONNX Runtime 1.25.1'in kendi kuantizasyon modülünü kullanır; kaynağını Kod Okuma bölümünde inceleyeceğiz.

{{KOD onnx 7}}

{{CIKTI onnx.txt python b80_onnx.py}}

### Doğruluk: katlama bedava, int8 bedeli var

Tablo, PyTorch, ONNX fp32 ve ONNX int8 modellerinin üç kümedeki mAP değerlerini verir. Tek bir tohum (1) kullanılmıştır; bu bölüm amacı, dışa aktarma ve kuantizasyonun etkisini izole etmektir.

| Küme | Yöntem | mAP@0,5 | mAP@[0,5:0,95] | Kayıp (mAP@0,5) | Kayıp (mAP@[0,5:0,95]) |
|---|---|---|---|---|---|
| Test | PyTorch | 0,939 | 0,639 | - | - |
| Test | ONNX fp32 | 0,939 | 0,639 | 0 | 0 |
| Test | ONNX int8 | 0,928 | 0,543 | 1,1 puan | 9,5 puan |
| Kayma | PyTorch | 0,873 | 0,547 | - | - |
| Kayma | ONNX int8 | 0,836 | 0,472 | 3,7 puan | 7,6 puan |
| OOD | PyTorch | 0,895 | 0,605 | - | - |
| OOD | ONNX int8 | 0,887 | 0,516 | 0,8 puan | 8,9 puan |

İlk iki satır sağlam bir sonuçtur. BN katlama farkı maksimum 1,10e-5, ONNX ile PyTorch kutuları arasındaki en büyük fark ise 7,99e-6'dır. Yani dışa aktarma ve katlama, R14 eşiğinin (1e-4) çok altında kaldı. Bu, Bölüm 75'te savunduğumuz "önce eşleşme testi" ilkesinin pratikteki karşılığıdır.

int8 tablosu daha ilginçtir. mAP@0,5 kaybı nominal test için 1,1 puan, yani R5 (<= 2 puan) geçildi. Ama mAP@[0,5:0,95] kaybı 9,5 puan, yani R6 (<= 5 puan) geçilemedi. Fark, metriğin ne ölçtüğündedir. mAP@0,5 kutunun kabaca doğru yerde olduğunu ister; mAP@[0,5:0,95] ise on farklı IoU eşiğinde kutunun ne kadar hassas olduğunu ister. Kuantizasyon, kutu koordinatlarını hafifçe kaydırıyor; kutu kabaca doğru ama kesin değil. Hipotezimiz, kafa katmanındaki ofset ve log-ölçek kodlamasının (Bölüm 67.8) kuantizasyon hatasına karşı hassas olduğudur: w = anchor * exp(t_w) gibi bir üstel, küçük bir t_w hatasını ölçekle büyütür. Bu hipotezi bu bölümde doğrulamadık. Doğrulamak için kafa katmanını fp32 tutan bir karma hassasiyet deneyi yapılabilir; Ek alıştırmalarda bunu bir soru olarak bıraktık.

Boyut açısından int8 bir kazanımdır. PyTorch durum dosyası 255 304 bayt, ONNX fp32 246 582 bayt ve ONNX int8 71 173 bayt. Modelin kendi sabitleri (ağırlık ve sapmalar) 64 366 bayttır. Bu, Cortex-M sınıfı bir mikrodenetleyicinin flaşına sığacak bir boyuttur ve R9'u (<= 1 MB) bol bol geçer.

### Gecikme: ölçüm disiplini ve bütçe

Gecikme ölçümü, Bölüm 75.2'deki disiplinle yapılır: bir ısınma dönemi (30 kare), sonra 300 kare üzerinden p50 ve p95 değerleri; ölçüm CPU'da yapılır çünkü edge hedefimiz CPU'dur. Her kare, bir sensör çıktısı simülasyonuyla başlar (float'tan uint8'e ve geri), sonra sırasıyla ön işleme, çıkarım, son işleme, takip ve güvence kuralı çalışır. Her aşama ayrı zamanlanır.

Kodun ilk parçası sabitleri ve import'ları tanımlar; ölçüm döngüsü ikinci parçadadır.

{{KOD gecikme 1}}

Kodun ikinci parçası ölçüm döngüsüdür. `time.perf_counter` her aşamanın başında ve sonunda çağrılır; ısınma kareleri atılır. Gecikmeler milisaniye cinsinden kaydedilir.

{{KOD gecikme 2}}

Üçüncü parça, konvolüsyonun çarpma-toplama sayısını (MAC) hesaplar. Bir konvolüsyonun MAC sayısı, çıktı alanı x giriş kanalı x çıkış kanalı x çekirdek alanıdır. Bu hesap, işlem yükünü bellek ve gecikmeden bağımsız olarak verir; Bölüm 75.1'deki maliyet modelinin doğrudan uygulamasıdır.

{{KOD gecikme 3}}

Dördüncü parça ana fonksiyonun ilk yarısıdır: iki iş parçacığı sayısı (4 ve 1) ve iki hassasiyet (int8, fp32) için ölçümleri çalıştırır, sonuçları yazdırır.

{{KOD gecikme 4}}

Beşinci parça 640 piksellik senaryoyu ölçer. Bu boyutta ağ eğitilmedi; yalnızca çıkarım süresi ölçülür. Dolayısıyla bu satır bir doğruluk değil, bir hız tahminidir.

{{KOD gecikme 5}}

Son parça bellek hesabını yapar: model sabitlerinin toplam baytı ve iki girdi boyutu için MAC ile en büyük ara tamponu. Bu sayılar, Cortex-M tartışmasının sayısal temelidir.

{{KOD gecikme 6}}

{{CIKTI gecikme.txt python b80_gecikme.py}}

Tabloda kare başına sürenin aşamalara göre dağılımı vardır. Değerler p50 ve p95 olarak milisaniye cinsindendir.

| Aşama | int8, 4 iş p. (p50 / p95) | fp32, 4 iş p. (p50 / p95) | int8, 1 iş p. (p50 / p95) |
|---|---|---|---|
| Ön işleme | 0,019 / 0,026 | 0,020 / 0,029 | 0,019 / 0,026 |
| Çıkarım | 0,115 / 0,152 | 0,120 / 0,145 | 0,214 / 0,238 |
| Son işleme (kod çözme, NMS) | 0,288 / 0,549 | 0,260 / 0,543 | 0,266 / 0,477 |
| Takip | 0,300 / 0,455 | 0,294 / 0,477 | 0,286 / 0,361 |
| Güvence | 0,002 / 0,003 | 0,002 / 0,003 | 0,002 / 0,003 |
| Toplam | 0,747 / 1,092 | 0,703 / 1,146 | 0,812 / 1,074 |

![Şekil 80.6: Doğruluk ve gecikme: PyTorch, ONNX fp32 ve int8 (gecikme uçtan uca, CPU)](gorseller/b80_karsilastirma.png)

Bu tablo iki açıdan öğreticidir. İlki, çıkarımın toplamın yalnızca yaklaşık yüzde 15'i olmasıdır. Son işleme ve takip birlikte, toplamın yaklaşık yüzde 80'ini oluşturur. Şekil 80.7, bu dağılımı yığılı çubukla gösterir.

![Şekil 80.7: Kare başına gecikmenin aşamalara göre dağılımı (int8, p50)](gorseller/b80_bilesen.png)

Hızlandırmak istediğimiz şeyi yanlış seçersek, çıkarımı iki katına çıkarsak bile toplam yalnızca birkaç yüzde kazanır. Bölüm 53'teki Amdahl yasası tam olarak budur: bir parçanın payı küçükse, o parçayı hızlandırmanın üst sınırı küçüktür.

İkincisi, int8'in bu ölçekte hız kazandırmadığıdır. 4 iş parçacığında int8 çıkarımı 0,115 ms, fp32 ise 0,120 ms; 1 iş parçacığında ise int8 0,214 ms, fp32 0,203 ms. Fark, ölçüm gürültüsünün içinde. Nedeni, ağın çok küçük olması ve kuantizasyon düğümlerinin (QuantizeLinear, DequantizeLinear) sabit bir ek yük getirmesidir. int8'in gerçek hız kazancı, daha büyük katmanlarda ve tam sayı çekirdeklerinin desteklendiği donanımda ortaya çıkar; bu bir genel bilgidir ve bu makinede ölçülmedi. Kazancı belirleyen şey, kuantizasyonun bir modeli küçültüp küçültmediği değil, modelin ölçeğine ve donanımın tam sayı yeteneğine bağlıdır.

R7'yi (96 px, uçtan uca p95 <= 33 ms) geçtik: 1,09 ms. Ama bu rakam 96 piksel için geçerlidir ve 96 piksel gerçek bir İHA için yeterli çözünürlük değildir. Hedefler 8 ile 24 piksel arasındaydı; 1920 x 1080'lik bir kareyi 96 x 96'ya indirmek, bir hedefi birkaç piksele düşürür.

### Çözünürlük ve Cortex-M: neden 640 px sorun?

Bu yüzden 640 x 640 girdiyle aynı ağın çıkarım süresini de ölçtük. Ağ tamamen konvolüsyonel olduğu için girdi boyutunu değiştirmek, ağırlıkları değiştirmez; bu yalnızca bir hız ölçümüdür, doğruluk değildir. Sonuç: int8 çıkarımı 4 iş parçacığında 2,83 ms (p50), 1 iş parçacığında 7,83 ms. Yani ağın kendisi 33 ms bütçesinin içinde kalır, ama bu, uçtan uca bir kanıt değildir: 640 pikselde kod çözme, 80 x 80 ızgara üzerinde çalışır ve bu, 12 x 12'ye göre yaklaşık 44 kat daha fazla hücre demektir. Mevcut son işleme Python döngüleriyle yazılmıştır. Bu aşama ölçülmedi. R8 yalnızca ağ için geçildi; R7'nin 640 px karşılığı ise "ölçülmedi" olarak kalır.

Bellek tarafını da hesaplayalım. Tablo, iki girdi boyutu için MAC sayısını ve en büyük ara tamponu verir.

| Girdi | MAC (kare başına) | En büyük ara tampon (int8) | Model sabitleri |
|---|---|---|---|
| 96 x 96 | 11,1 milyon | 36 864 bayt (36 KB) | 64 366 bayt |
| 640 x 640 | 493,2 milyon | 1 638 400 bayt (1,6 MB) | 64 366 bayt |

96 piksel için sayılar bir mikrodenetleyiciye yakındır: 64 KB sabit, 36 KB ara tampon. Bölüm 75.8'de bir Cortex-M4'te int8 MLP'nin nasıl kurulacağını gördük; bu ağ da aynı türden işlemlerden oluşur. Ama 640 piksel için tampon tek başına 1,6 MB'dır; birçok Cortex-M4 ve M7 çipinin toplam SRAM'inden büyüktür (genel bilgi, bu makinede ölçülmedi). Ayrıca 640 pikselde kare başına 493 milyon MAC, 30 kare/s için saniyede yaklaşık 15 milyar MAC demektir. Bir Cortex-M4 bunu, SIMD dahil bile, yapamaz (genel bilgi). Bu yüzden bu sistemin hedef donanımı, Cortex-M sınıfı değil, Jetson sınıfı bir GPU veya bir NPU olmalıdır. Jetson'da ölçüm yapmadık; bu yalnızca bir tahmin ve bir tasarım gerekçesidir.

Kısacası karar şudur: 96 piksellik bir sistem bir mikrodenetleyiciye sığabilir ama işe yaramaz; 640 piksellik bir sistem işe yarayabilir ama bir mikrodenetleyiciye sığmaz. Gereksinimler, donanımın seçimini zorlar. Bu, gömülü sistemlerde sık karşılaşılan bir ikilemdir ve Bölüm 75.9'da edge tasarımı için verilen kararlarla aynı yönü gösterir.
