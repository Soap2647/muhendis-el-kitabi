## 80.7 Güvence: ne zaman "emin değilim" demeli

Bir dedektörün en tehlikeli davranışı, yanlış olduğu bir tespiti yüksek güvenle göstermesidir. Skor 0,9 olan bir kuş, operatörün gözünde bir İHA olabilir. Güvence katmanının işi, sistemin ne bildiğini ve ne bilmediğini ayırmaktır. Bu bölümde iki basit kural kuruyoruz ve hangisinin hangi koşulda işe yaradığını ölçüyoruz.

Birinci kural tek skora bakar: skor eşiğin (tau) üstündeyse tespit "otomatik alarm" olur, altındaysa "operatöre doğrulat" olarak işaretlenir. Bu, en ucuz güvence biçimidir ve sıfır ek işlem gerektirir.

İkinci kural tohum uyumuna bakar. Aynı mimari, farklı başlangıç ağırlıklarıyla üç kez eğitildi. Eğitim verisi aynı olduğu hâlde, üç modelin bir tespit üzerinde hemfikir olması, o tespitin veriden kaynaklanan bir örüntü olduğunu gösterir. Biri tespit ederken diğerleri etmiyorsa, tespit başlangıç rastgeleliğine bağlıdır ve güvenilmez. Bu, belirsizliğin bir parçasıdır: ağın kendi bilgisindeki eksikliği (epistemik belirsizlik). Bölüm 78'de belirsizlik tahminini ve dağılım dışı (OOD) tespitini derinlemesine işleyeceğiz; burada sadece bu sinyalin sisteme nasıl bağlandığını gösteriyoruz.

Uyum kuralı şöyle tanımlanır: bir tespitin, diğer iki tohumdan birinde aynı sınıfta, IoU en az 0,5 ile örtüşen ve skoru en az 0,3 olan bir karşılığı varsa, o tespit "uyumlu" sayılır. Otomatik alarm için hem skor eşiğini geçmesi hem de iki tohumla da uyumlu olması gerekir.

Kodun ilk parçası uyum ölçümünü ve doğru eşleştirme için kullanılan gerçek eşleştirme fonksiyonunu tanımlar. Eşleştirme Bölüm 67.7'deki AP hesabıyla aynı mantığı izler: skora göre azalan sırada, en yüksek IoU'lu ve henüz kullanılmamış gerçek kutuyu seçer.

{{KOD guvence 1}}

Kodun ikinci parçası, eşleştirme fonksiyonunun devamıdır. Burada bir karar, gerçek kutulara bir kez eşlenen tespitlerin doğruluğunu sağlar; aynı gerçek kutuya birden fazla tespit eşlenemez.

{{KOD guvence 2}}

Üçüncü parça, bir kurala ve eşiğe göre hangi tespitlerin otomatik alarm olduğunu belirleyen maskeyi üretir.

{{KOD guvence 3}}

Dördüncü parça, bir maske ile birlikte kesinlik, kapsama ve görüntü başına yanlış alarmı hesaplar. Üç ölçü birlikte okunmalıdır; biri tek başına yanıltır.

{{KOD guvence 4}}

Beşinci parça ana akıştır. Eşik seçimi yalnızca doğrulama kümesinde yapılır: iki kural için eşikler taranır ve kesinlik en az 0,90 olan eşikler arasından kapsaması en yüksek olan seçilir. Bu, Bölüm 57'deki maliyet temelli eşik seçiminin basit bir biçimidir: yanlış alarm pahalıysa kesinlik hedefi yükselir, kaçırılan hedef pahalıysa kapsama hedefi yükselir. 0,90 bir maliyet varsayımıdır, bir ölçüm değildir; bunu açıkça kabul ediyoruz.

{{KOD guvence 5}}

Son parça, korumasız (her tespit otomatik) referansı ölçer ve sonuçları CSV'ye yazar. Korumasız referans, güvencenin ne kazandırdığını ve ne kaybettirdiğini gösteren tabandır.

{{KOD guvence 6}}

{{CIKTI guvence.txt python b80_guvence.py}}

### Sonuçlar: iki kuralın ödünleşimi

Doğrulama kümesinde tek skor kuralı için seçilen eşik 0,30 (kesinlik 0,913, kapsama 0,904). Tohum uyumu kuralı için seçilen eşik 0,05 (kesinlik 0,963, kapsama 0,879). Tohum uyumu, eşik düşük olsa bile kesinliği artırır, çünkü yalnızca iki tohumun da hemfikir olduğu tespitleri geçirir.

Tablo, seçilen eşiklerde test, kayma ve OOD kümelerini gösterir. "Yanlış/görüntü" sütunu, bir görüntüde operatöre giden yanlış otomatik alarm sayısıdır.

| Kural | Küme | Kesinlik | Kapsama | Yanlış / görüntü |
|---|---|---|---|---|
| Korumasız | Test | 0,593 | 0,955 | 1,588 |
| Tek skor (tau 0,30) | Test | 0,917 | 0,923 | 0,202 |
| Tohum uyumu (tau 0,05) | Test | 0,961 | 0,878 | 0,086 |
| Korumasız | OOD | 0,377 | 0,948 | 3,886 |
| Tek skor (tau 0,30) | OOD | 0,730 | 0,899 | 0,824 |
| Tohum uyumu (tau 0,05) | OOD | 0,939 | 0,870 | 0,140 |
| Tek skor (tau 0,30) | Kayma | 0,814 | 0,849 | 0,472 |
| Tohum uyumu (tau 0,05) | Kayma | 0,939 | 0,775 | 0,122 |

OOD satırları, güvencenin asıl işini gösterir. Korumasız sistemde her görüntüde ortalama 3,9 yanlış otomatik alarm vardır; bunların çoğu kuş benzeri şekillerdir. Tek skor kuralı bunu 0,82'ye indirir (yüzde 79 azalma). Tohum uyumu ise 0,14'e indirir (yüzde 96 azalma). İki kuralın da R11'i (en az yüzde 50 azalma) geçtiğini görüyoruz.

Asıl ödünleşim kapsamadadır. Korumasız sistemin test kapsaması 0,955'tir; tek skor kuralı bunu 0,923'e, tohum uyumu ise 0,878'e indirir. R12 (kapsama kaybı en fazla 5 puan) tek skor kuralı için geçildi (3,2 puan kayıp), tohum uyumu için geçilemedi (7,7 puan kayıp). Yani tohum uyumu daha temiz bir alarm akışı sağlar, ama bunun bedelini kaçırılan hedeflerle öder. Hangisinin doğru olduğu bir mühendislik kararıdır ve bu karar, operatörün ne kadar kaçırmayı göze alabileceğine bağlıdır. Bu nedenle eşik değil, kuralın seçimi operasyonel bir karardır.

Tohum uyumunun bir maliyeti de vardır. Her kare için üç model çalıştırmak gerekir. Bu bölümün ölçümlerine göre bir modelin çıkarım süresi yaklaşık 0,115 ms ve son işleme süresi yaklaşık 0,29 ms'dir (80.6). Üç modelle ek yük kabaca iki model daha demektir; bu, yaklaşık 0,8 ms'lik bir ek süredir. Bu bir tahmindir, ölçülmedi; ama sonucu değiştirmeyecek kadar küçüktür. 640 piksel ölçeğinde ise bu ek yük ağın kendisi kadar büyür ve ayrıca değerlendirilmelidir.

Şekil 80.8, eşiğe bağlı davranışı gösterir. Sol panelde kapsama, eşik arttıkça düşer; iki kural da yüksek eşiklerde hızla kapsama kaybeder. Sağ panelde OOD'deki yanlış alarm, simetrik log eksende gösterilmiştir. Kesikli çizgi korumasız taban değerdir. Tohum uyumu eğrisi her eşikte tek skor eğrisinin altında kalır: aynı eşikte daha az yanlış alarm verir, ama kapsaması da daha düşüktür. İki eğri arasındaki asıl soru, hangi kapsama kaybının kabul edilebilir olduğudur.

![Şekil 80.8: Skor eşiğine göre kapsama (test) ve OOD'de görüntü başına yanlış alarm](gorseller/b80_guvence.png)
