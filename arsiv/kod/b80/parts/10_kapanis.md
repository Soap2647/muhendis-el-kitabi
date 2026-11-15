## 80.10 Kapanış: kitabın tamamı bu sistemde nerede?

Bu sistemi kurarken kitabın on altı kısmının hepsine dokunduk, ama bazılarına diğerlerinden çok daha fazla. Şekil 80.10, her kısmın sistemdeki karşılığını gösterir. Haritayı okurken şunu hatırlayın: bir kısmın karşılığı, o kısmın yalnızca bir sayfasından değil, o kısımdaki zihinsel modelden gelir.

![Şekil 80.10: Kitabın 16 kısmının bitirme sistemindeki karşılığı](gorseller/b80_kitap_haritasi.png)

Veri yapıları ve algoritmalar (Kısım III ve IV) sistemin en yoğun kullanılan kısımlarıdır. Kutu listeleri, izler ve bağlı bileşenler (Bölüm 11'deki graf düşüncesi, Bölüm 67'deki eşleştirme) ile NMS ve Macar eşleştirmesi, takip ve tespit kodunun omurgasıdır. Bölüm 12'deki Big-O düşüncesi, her karede kaç kutuyla karşılaştırma yapıldığını hesaplamamızı sağladı; NMS'in karmaşıklığının kutu sayısıyla nasıl büyüdüğünü bu düşünceyle anladık.

Sayısal kısımlar (Kısım XII ve XIV) sistemin doğruluk dilini oluşturur. IoU, Kalman tahmini, PSI ve KS testi, MOTA'nın formülü ve tohumlar arası belirsizlik, Bölüm 49 ve 57'nin araçlarıdır. Kısım XV'in (derin öğrenme) ağı ve eğitimi, Kısım XVI'nın (ML mühendisliği) kuantizasyonu, güvence ve izlemesi bu iki kısmın üzerine kuruludur.

Sistemin en az görünen ama en çok iş yapan kısmı işletim sistemi ve iş parçacıklarıdır. Kare hattında iş parçacığı sayısını (Kısım VI ve XIII) değiştirmek, gecikmeyi değiştirdi; bu, Bölüm 26 ve 53'teki paralelliğin pratikte nasıl görüneceğini göstermesi açısından öğreticiydi. Ağ katmanı (Kısım VII) ise bu sistemde yalnızca kavramsaldır: sensör ve operatör arayüzü gerçek bir ağ üzerinden çalışmaz. Bu, bir eksiklik değil, bilinçli bir kapsam sınırıdır; ama gerçek bir sistemde ağ, gecikme ve kayıp hesaplarının bu hatta girmesi gerekir.

## Bu sistemi yapay zekâ olmadan kurabilmek için neler bilinmeli?

Bu bölümdeki her adımı bir yapay zekâ aracı olmadan tekrarlayabilmek, kitabın asıl başarı ölçütüdür. Aşağıdaki kontrol listesi bunu bir sınama gibi kullanmanızı sağlar. Her maddeyi kağıtta, ekransız ve kaynaksız yapabiliyor musunuz, sorusunu sorun.

1. Bir tespit kutusunun IoU değerini ve iki kutunun NMS ile nasıl bastırıldığını elle hesaplayabiliyor musunuz?
2. Beş tahminlik bir listeden PR eğrisini ve AP değerini sıfırdan çıkarabiliyor musunuz?
3. Kalman filtresinin tahmin ve güncelleme adımlarını, sabit hız modeliyle bir kutu için yazabiliyor musunuz?
4. Üç izi üç tespitle Macar ya da açgözlü yöntemle eşleştirip MOTA ve IDSW'yi sayabiliyor musunuz?
5. BatchNorm'un Conv'a nasıl katlandığını, formülünü türeterek gösterebiliyor musunuz?
6. Simetrik int8 kuantizasyonunda ölçek ve sıfır noktasını bir tensörden hesaplayabiliyor musunuz?
7. Bir ağın kare başına gecikmesini, ısınma ve p50/p95 ile doğru ölçebiliyor musunuz?
8. PSI ve KS değerlerini bir referans ve bir pencere için el ile hesaplayabiliyor musunuz?
9. Bir değerlendirme sonucunun neden test kümesinde değil doğrulama kümesinde seçilmesi gerektiğini bir mülakatta anlatabiliyor musunuz?
10. Bir mAP farkının gürültüden ayrılması için kaç tohuma ihtiyaç olduğunu tartışabiliyor musunuz?
11. Bir gereksinimi, ölçülebilir bir kabul ölçütüne ve bir test planına çevirebiliyor musunuz?
12. Bir FMEA tablosunu bir sistem için, en az altı hata modu ile yazabiliyor musunuz?

Bu listedeki her madde, kitabın bir bölümüne dayanır. Bir maddede takılırsanız, o bölüme dönün; sistemi kurmak, bu parçaları birleştirmekten ibarettir.

## Açık kalanlar: dürüst bir liste

Bölüm 39'da bir söz verdik: Bölüm 80'de simülatör ile gerçek donanım arasındaki farkı ölçeceksiniz. Bu sözü tam olarak tutamadık. Gerçek bir gömülü kart yoktu; ölçüm dizüstü bilgisayarın CPU'sunda yapıldı. Bu bir vekil ölçümdür ve gerçek donanım farkı hâlâ ölçülmedi. Bunu, Kendin Yap bölümündeki ek alıştırmalardan birinde, bir STM32 kartında aynı ağı çalıştırarak kendiniz yapabilirsiniz.

Diğer açık kalanlar da açıkça yazılmalıdır:

- Gerçek İHA verisi yok. Tüm sayılar sentetik veriye aittir ve gerçek bir kamerada farklı olabilir.
- Cortex-M ve Jetson ölçülmedi. Cortex-M için bellek ve işlem hesabı yapıldı, Jetson için yalnızca genel bilgi var.
- 640 piksel için uçtan uca gecikme ölçülmedi; kod çözme ve takip bu boyutta yeniden ölçülmeli.
- int8 kuantizasyonunda kutu hassasiyeti düşüyor (R6). Hipotezimiz kafa katmanıdır, ama bu doğrulanmadı.
- Tohum uyumu kuralı yalnızca PyTorch ile ölçüldü; edge'de üç modelin birlikte ölçümü yapılmadı.
- Kayma simülasyonu, üreticinin kendi tanımıyla yapıldı; gerçek kaymalar bu kadar düzenli olmaz.
- Yeniden eğitimin kazancı iyimserdir; gerçek bir sahada yeni etiketli veriyle yeniden ölçülmeli.

Son bir not. Bu sistemin bir savunma sanayii ürününe dönüşmesi için sertifikasyon yolu, yalnızca teknik bir süreç değildir. Havacılıkta yazılım ve donanım için DO-178C ve DO-254 gibi standartlar bulunur (genel bilgi, bu bölümde uygulanmadı). Model yeniden eğitimi, güvence kuralları ve izleme, bu standartların gerektirdiği izlenebilirlik ve doğrulama kanıtlarıyla ilişkilidir. Bölüm 78 ve 77.12, bu konuya giriş niteliğindedir.
