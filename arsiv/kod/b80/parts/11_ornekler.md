## Çözümlü Örnekler

Dört örnek, zorluk sırasına göre (★, ★★, ★★, ★★★) sıralanmıştır. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntü, iyileştir, doğrula. Doğrulama adımında bir tablo ile kendi sonucunuzu elle kontrol edersiniz. Örneklerdeki sayılar bu bölümün ölçümlerinden alınmıştır; her yerde kaynağını yazdık.

### Örnek 1 (★): Kare bütçesini bileşenlere dağıtmak

Bir gözetleme sistemi saniyede 30 kare işlemek zorundadır. Bu, her kare için en fazla 33 ms demektir. Sistemin 96 piksel ölçümünde int8, 4 iş parçacığı ile p50 toplamı 0,747 ms'dir. Bütçenin ne kadarının kullanıldığını ve 640 pikselde ne olabileceğini bilmek istiyoruz.

**Adım 1 — Anla.** Soru iki parçalıdır. Birincisi bugünkü durumda bütçenin ne kadarı kullanılıyor. İkincisi 640 piksele geçersek bütçe nasıl değişir. İkinci soru bir tahmindir; ölçüm yapılmadan cevaplanamaz, ama bir tahminin dürüst yazılması gerekir.

**Adım 2 — Örnekle.** 96 pikselde ölçülen bileşenler şunlardır (p50, ms): ön işleme 0,019, çıkarım 0,115, son işleme 0,288, takip 0,300, güvence 0,002. Bunların toplamı 0,724 ms eder. Ölçülen toplam p50 ise 0,747 ms'dir. Fark, medyanların toplamının toplamın medyanına eşit olmamasından gelir; bu bir hata değil, bir istatistiksel gerçektir.

**Adım 3 — Kaba çöz.** 96 pikselde bütçenin yüzde 2,3'ü kullanılıyor (0,747 / 33). Bu kadar büyük bir boşluk, 640 pikselde gelişmenin mümkün olduğunu gösterir. Ama 640'ta son işlemenin ne yapacağını bilmiyoruz: ızgara 12 x 12'den 80 x 80'e çıkar, yani hücre sayısı yaklaşık 44 kat artar. İki varsayım seçelim. Varsayım A: son işleme ve takip değişmez. Varsayım B: son işleme hücre sayısıyla doğru orantılı büyür.

**Adım 4 — Örüntü.** Ağın çıkarım süresi 640'ta ölçüldü: p50 2,83 ms. Bu bir ölçümdür, varsayım değildir. Örüntü şudur: ağ ile son işleme aynı oranda büyümez. Ağın büyümesi evrişimin doğasında vardır (yaklaşık 44 kat MAC, ama donanım bunu paralel yapar); son işleme ise Python döngüsüyle yazılmıştır ve doğrusal büyür.

**Adım 5 — İyileştir.** Varsayım B'nin sonucu, bütçeyi zorlar. Bunu azaltmanın yolu son işlemeyi vektörleştirmektir (Bölüm 56'daki NumPy vektörleştirme). Ama önce ölçmek gerekir: son işlemeyi 80 x 80 ızgara ile bir kez çalıştırıp süreyi görmeden kod yazmayın. Bölüm 75.2'deki disiplin, önce ölçümü ister.

**Adım 6 — Doğrula.** Aşağıdaki tablo iki varsayımı yan yana koyar. Ağın 2,83 ms'lik değeri ölçümdür; son işleme için A'da 0,288, B'de 0,288 x 44,4 = 12,8 ms alınır; takip sabit kalır.

| Senaryo | Ağ | Son işleme | Takip | Diğer | Toplam | Bütçe kullanımı |
|---|---|---|---|---|---|---|
| 96 px (ölçüm) | 0,115 | 0,288 | 0,300 | 0,021 | 0,747 | %2,3 |
| 640 px, A | 2,83 | 0,288 | 0,300 | 0,021 | 3,44 | %10,4 |
| 640 px, B | 2,83 | 12,8 | 0,300 | 0,021 | 15,95 | %48,3 |

Sonuç: Varsayım B bile bütçede kalıyor. Ancak p95 değeri ölçülmediği için kesin bir karar veremeyiz. Bu tablo, "bütçe tutuyor mu" sorusunun cevabının, hangi varsayımla yanıtlandığına bağlı olduğunu gösterir. Bir mühendis bu cevabı yazarken iki varsayımı da yazar ve hangisinin ölçülmesi gerektiğini belirtir.

**Bunu AI'sız yazabilir misin?** Ön işleme 96 pikselde 0,019 ms, son işleme 0,288 ms olsun. Ağ 640 pikselde 4 ms, son işleme hücre sayısıyla doğrusal büyüsün ve takip sabit kalsın. Toplamı ve 33 ms bütçesindeki payını hesapla.

### Örnek 2 (★★): Bir gereksinimi ölçülebilir kabul ölçütüne çevirmek

Gereksinim şudur: "Takip sırasında kimlikler kararlı olmalı." Bu cümle ölçülemez. Kararlı ne demek? Kaç kimlik değişimi kabul edilebilir? Bu örnekte bu cümleyi bir test tasarımına çevireceğiz.

**Adım 1 — Anla.** "Kararlı" kelimesi bir ölçü değildir. Ölçü, kimlik değişimi sayısının gerçek nesne-kare sayısına oranı olabilir (IDSW / GT). Bu, Bölüm 67.17'deki tanımdır. Eşiği de seçmemiz gerekir: bu bölümde yüzde 1.

**Adım 2 — Örnekle.** Test kümesinde 1 735 gerçek nesne-kare ve 24 kimlik değişimi ölçtük. Oran 24 / 1 735 = 0,0138, yani yüzde 1,38. Eşiğin üstünde görünüyor.

**Adım 3 — Kaba çöz.** Bu bir nokta tahmini. Bir nokta tahmini yalnızca bir sayıdır; belirsizliğini bilmeden karar vermek, bir zarın tek bir atışına bakıp zarın hilekâr olduğuna karar vermek gibidir. Kaba bir güven aralığı için binom yaklaşımına (Wald) bakalım: standart hata = karekök(p (1 - p) / n).

**Adım 4 — Örüntü.** Kimlik değişimleri, kesişme anlarında yoğunlaşır (Şekil 80.5). Yani değişimler bağımsız rastgele olaylar değildir; kümelenmişlerdir. Wald aralığı bağımsızlık varsayar, dolayısıyla gerçek belirsizlik daha geniş olabilir. Bu, aralığı bir alt sınır olarak okumamız gerektiği anlamına gelir.

**Adım 5 — İyileştir.** Kararı netleştirmek için iki şey yapılabilir: GT sayısını artırmak (daha fazla video) ve kesişme sahnelerini ayrı bir alt küme olarak ölçmek. Ayrıca kriteri "IDSW / GT <= %1" yerine "her kesişme olayında en fazla bir değişim" gibi daha yapısal bir ölçüye çevirmek de düşünülebilir.

**Adım 6 — Doğrula.** Tabloda hem test hem doğrulama kümesinin Wald %95 aralıkları vardır.

| Küme | GT | IDSW | Oran | Standart hata | %95 aralık |
|---|---|---|---|---|---|
| Test (macar_iou, çerçeve açık) | 1 735 | 24 | %1,38 | %0,28 | [%0,83; %1,93] |
| Doğrulama (macar_iou, çerçeve açık) | 1 722 | 20 | %1,16 | %0,26 | [%0,66; %1,67] |

Sonuç: Test oranı eşiğin üstünde, ama %95 aralığı eşiği (%1) kapsıyor. Bu, "kesin olarak kaldı" demenin yanlış olacağını gösterir. Doğru ifade şudur: "Nokta tahmini eşiği aşıyor; belirsizlik aralığı eşiği kapsıyor; karar için daha fazla GT gerekir." Bu bölümde R4'ü bu yüzden "KALDI (nokta tahmini)" olarak işaretledik.

**Bunu AI'sız yazabilir misin?** 12 000 nesne-karede 9 kimlik değişimi ölçtün. Oran nedir? Wald %95 aralığını hesapla ve eşiğin (%0,1) aralığın içinde olup olmadığına karar ver.

### Örnek 3 (★★): Kayıtlardan kök neden analizi

İzleme sisteminde mAP'nin bir pencerede düştüğünü görüyorsunuz. Operatör "model bozuldu, yeniden eğitelim" diyor. Ama tetiğe basmadan önce kök nedeni bulmanız gerekir. Kayıtlar elinizde: her pencerenin PSI, KS p değeri, mAP ve üç alarm bayrağı.

**Adım 1 — Anla.** Soru "ne oldu?" değil "neden oldu?" sorusudur. İki olası neden var: kovaryat kayması (girdi dağılımı değişti, ilişki aynı) ya da kavram kayması (girdi ile etiket arasındaki ilişki değişti). İkisi farklı müdahale gerektirir. Kavram kayması etiket gerektirir (performans sinyali), kovaryat kayması etiketsiz de görülebilir (PSI).

**Adım 2 — Örnekle.** Aşağıdaki kayıtlar pencere 22 ile 26 arasını gösterir.

**Adım 3 — Kaba çöz.** İlk değişen sinyal PSI'dır: pencere 22'de 0,059 iken 23'te 0,220'ye çıkıyor. mAP de aynı pencerede düşüyor (0,932'den 0,875'e). Yani kayma girdiden başlıyor gibi görünüyor. Ama bu, tek bir pencereye dayanarak vardığımız bir sonuç.

**Adım 4 — Örüntü.** mAP bir sonraki pencerede (24) 0,910'a geri yükseliyor. PSI ise 24'te daha da arttı (0,296). Yani mAP tek başına güvenilir bir sinyal değil; 200 sahnelik pencerelerde gürültülü. Bu durumda mAP'ye bakarak kavram kaymasına karar vermek yanlış olur. Örüntü, girdi kaymasının monoton arttığı, mAP'nin ise gürültüyle birlikte aşağı yönlü bir eğilim gösterdiğidir.

**Adım 5 — İyileştir.** Karar için daha sağlam bir yol: performans sinyalini tek pencereye değil, üç pencerenin hareketli ortalamasına bağlamak, ve kavram kaymasını ayrı bir testle (Bölüm 77.10'daki alan sınıflandırıcısı) kontrol etmek. Bu, yanlış alarm riskini de düşürür.

**Adım 6 — Doğrula.** Tablo, kayıtlardan okuduğumuz değerleri ve sonucu gösterir.

| Pencere | PSI | KS p | mAP | Girdi | Skor | Performans | Yorum |
|---|---|---|---|---|---|---|---|
| 22 | 0,059 | 0,188 | 0,932 | 0 | 0 | 0 | Sakin |
| 23 | 0,220 | 0,055 | 0,875 | 1 | 0 | 0 | Girdi kayması başladı |
| 24 | 0,296 | 0,004 | 0,910 | 1 | 1 | 0 | mAP toparlandı, kayma sürüyor |
| 26 | 0,561 | 0,0001 | 0,906 | 1 | 1 | 1 | Performans alarmı, etiket gecikmeli |

Sonuç: Kök neden, kovaryat (girdi) kaymasıdır; kavram kayması kanıtı yoktur. Ama bu sonuç, tek bir mAP değerine dayanamaz. Müdahale: yeniden eğitimi tetiklemek (iki ardışık girdi ve skor alarmı var) ve insan onayıyla yeni işaretli veriyle eğitmek. Bu noktada yapılacak en önemli iş, kararı yazmak ve kanıtını kaydetmektir.

**Bunu AI'sız yazabilir misin?** Pencere 30'da PSI 3,65 ve mAP 0,910 olsun; pencere 31'de PSI 3,75 ve mAP 0,871 olsun. Hangi sinyal daha güvenilir ve neden?

### Örnek 4 (★★★): Bir değişikliğin bütün kabul ölçütlerine etkisi: int8'e geçiş

Ekipten biri "int8'e geçelim, model 3 kat küçülür, hız artar" diyor. Bu bir değişiklik önerisidir ve kararı kabul ölçütlerine bakarak vermeliyiz. Karar, bir mühendisin en sık verdiği karar türüdür: bir kazancın hangi kayıplarla geldiğini tartmak.

**Adım 1 — Anla.** Değişiklik, fp32 ağırlıklar ve aktivasyonlardan int8'e geçiştir. Beklenen kazanım: boyut, bellek ve (belki) hız. Beklenen kayıp: doğruluk, özellikle kutu hassasiyeti. Kabul ölçütleri 80.1'deki R tablosudur. Değişiklik yalnızca bu tabloya göre değerlendirilir.

**Adım 2 — Örnekle.** Ölçümler elimizde: int8 mAP@0,5 kaybı 1,1 puan, mAP@[0,5:0,95] kaybı 9,5 puan. Model dosyası 255 KB'den 71 KB'ye düştü. 96 px uçtan uca p95: fp32 1,146 ms, int8 1,092 ms. 640 px'te yalnızca int8 ağ süresi ölçüldü (2,83 ms p50).

**Adım 3 — Kaba çöz.** Her R için fp32 ve int8'in durumunu sıralayalım. fp32'de kayıp sıfırdır; bellek değerleri ise dört katıdır, çünkü fp32 bir eleman için 4 bayt, int8 için 1 bayt harcar.

**Adım 4 — Örüntü.** Kazançlar boyut ve ara tamponda, kayıplar kutu hassasiyetinde. Kutu hassasiyeti mAP@[0,5:0,95] ile ölçülür ve tam olarak R6'da zorlanır. Örüntü: int8, sınıflandırma kadar lokalizasyon için uygun değildir (bu, bu ağda; genel bir yasa değildir).

**Adım 5 — İyileştir.** Üç seçenek var. (a) Karma hassasiyet: ağın kafa katmanını (yalnızca 1 024 ağırlık) fp32 tutmak; boyut artışı ihmal edilebilir, lokalizasyon kaybı büyük olasılıkla düşer; ama bu ölçülmedi. (b) int8'i olduğu gibi kabul edip R6 kaybını belgelemek. (c) int8'i reddedip fp32 ile devam etmek, boyut ve bellek kazancını vazgeçmek. Öneri: (a), ölçüm sonrası karar.

**Adım 6 — Doğrula.** Tablo, değişikliğin her kabul ölçütüne etkisini gösterir.

| Kod | Ölçüt | fp32 | int8 | Etki |
|---|---|---|---|---|
| R5 | mAP@0,5 kaybı <= 2 puan | 0 | 1,1 | GEÇTİ |
| R6 | mAP@[0,5:0,95] kaybı <= 5 puan | 0 | 9,5 | KALDI |
| R7 | 96 px uçtan uca p95 <= 33 ms | 1,146 | 1,092 | GEÇTİ (her ikisi) |
| R8 | 640 px ağ p95 <= 33 ms | ÖLÇÜLMEDİ | 3,08 | GEÇTİ (int8) |
| R9 | Model <= 1 MB | 246 KB | 71 KB | GEÇTİ (her ikisi) |
| R10 | 96 px ara tampon <= 256 KB | ~144 KB | 36 KB | GEÇTİ (her ikisi) |
| R10b | 640 px ara tampon <= 256 KB | ~6,5 MB | 1,6 MB | KALDI (her ikisi) |
| R14 | ONNX ile PyTorch kutu farkı <= 1e-4 | 8e-6 | (fp32 yolu) | GEÇTİ |

Sonuç: int8, boyut ve bellekte kazandırır, ama R6'da kaldığı için lokalizasyon hassasiyeti gerektiren bir kullanımda kabul edilemez. Karma hassasiyet (a) seçeneği, bu eksiği kapatma olasılığı taşıyor ve bir sonraki deney olarak öneriliyor. Ekibe söylenecek cümle şöyle olabilir: "int8 kazancı gerçek, ama R6 kaybı ölçüldü ve kabul edilmedi; kafa katmanı fp32 ile yeniden ölçülene kadar int8 yayına alınmamalı."

**Bunu AI'sız yazabilir misin?** Bir modelin fp32 boyutu 4 MB, int8 boyutu 1 MB olsun; ara tampon fp32'de 300 KB ise int8'de kaç KB olur ve 256 KB sınırına göre hangisi geçer?
