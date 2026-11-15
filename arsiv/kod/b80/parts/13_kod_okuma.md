## Kod Okuma Egzersizi

Bu bölümde kendi yazdığımız kodun yanında gerçek bir kütüphanenin kodunu da okuyacağız. Kaynak, bu sistemin int8 kuantizasyon adımını çalıştıran ONNX Runtime'ın Python kısmıdır: `onnxruntime` 1.25.1 sürümünün `quantization/quantize.py` dosyasındaki `quantize_static` fonksiyonu. Kendi kurulumumuzdan birebir alındı; yol `C:/Users/merty/AppData/Local/Programs/Python/Python312/Lib/site-packages/onnxruntime/quantization/quantize.py`.

Fonksiyonun imzası 479. satırda başlar ve on beş parametre alır. Aşağıdaki kesit, gövdenin 640. satırından itibaren, başındaki iki işi gösterir: varsayılan değerlerin hazırlanması ve modelin yüklenmesi. Kesit, dosyadan kelimesi kelimesine alınmıştır; hiçbir satır değiştirilmedi. Yalnızca gövdenin devamı (kalibrasyon seçenekleri ve SmoothQuant dalı) dışarıda bırakıldı, çünkü bu bölümde kullanmadık.

{{KAYNAK C:/Users/merty/AppData/Local/Programs/Python/Python312/Lib/site-packages/onnxruntime/quantization/quantize.py 640 657}}

Kesitin 658 ile 662 satırları, ön işleme uyarısını kaydeden `logging.warning` çağrısıdır. Uyarının metni bir bağlantı içerdiği için kesitte yer almıyor; mesajın başı şöyledir: "Please consider to run pre-processing before quantization." Bu uyarıyı çalıştırmamızda gördük ve 80.6'da çıktıdan kapattık. Kapatmanın doğru olup olmadığını aşağıdaki sorularla tartışın.

**Sorular — cevaplamadan geçme:**

1. Satır 640-642 neden `nodes_to_exclude or []` gibi bir ifade kullanıyor? Parametrelere doğrudan `[]` varsayılanı yazılsaydı hangi tuzak ortaya çıkardı? Python'un değiştirilebilir varsayılan argüman tuzağını Bölüm 3'te hatırlayarak yanıtlayın.
2. `op_types_to_quantize` boşsa, hangi operatör türleri kuantize edilir? Bu kümeyi oluşturan iki kayıt defterinin (`QLinearOpsRegistry` ve `QDQRegistry`) ne tuttuğunu, kaynağın başka bir yerinde arayarak bulun.
3. Satır 650-654 neden iki farklı yükleme fonksiyonu arasında seçim yapıyor? Modelin dinamik eksenleri (`h` ve `w`) bu şekil çıkarımını nasıl etkiler? Bunu 80.6'daki dışa aktarma kararıyla ilişkilendirin.
4. Satır 658'deki uyarı, graf düzeyinde bir ön işlemenin (ör. şekil ve sabit katlama) yapılmadığını söyler. Bu bizim modelimizde kaliteyi etkiler mi? Etkilemesi için hangi ölçüm gerekirdi? Bölüm 77.3'teki tekrarlanabilirlik ilkesiyle yazın.
5. Satır 643'teki `mode = QuantizationMode.QLinearOps` değişkeni, bizim QDQ formatımızda kullanılıyor mu? Yanıtınızı, `quant_format` parametresinin gövdedeki hangi dalda okunduğunu göstererek verin.
6. Kalibrasyonda `CalibMovingAverage` ve `CalibPercentile` seçenekleri, MinMax yönteminin aşırı değerlere (outlier) karşı davranışını nasıl değiştirir? Bu değişim, 80.6'da gördüğümüz 9,5 puanlık kutu hassasiyeti kaybını açıklayabilir mi? Bir hipotez yazın ve nasıl sınanacağını tarif edin.

