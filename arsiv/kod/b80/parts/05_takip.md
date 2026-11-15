## 80.5 Takip: her karede aynı nesneyi bulmak

Dedektör her karede bağımsız çalışır. Bir karedeki üçgen ile bir sonraki karedeki üçgenin aynı nesne olduğunu bilmez. Takip (tracking) bu bağlantıyı kurar. Bölüm 67.15'te gördüğümüz tespit-ile-takip yaklaşımında üç parça vardır: her iz için bir durum (Kalman filtresi, Bölüm 62.6), bir hareket tahmini, ve tahminlerle yeni tespitlerin eşleştirilmesi (veri ilişkilendirme, Bölüm 67.16).

Bu bölümde iz durumu altı boyutludur: merkez (cx, cy), genişlik ve yükseklik (w, h) ile merkezin hızı (vx, vy). Tahmin adımı merkezi hızla ilerletir; güncelleme adımı tespit kutusuyla durumu düzeltir. Eşleştirmede maliyet, izin tahmini kutusu ile tespit kutusu arasındaki IoU'dur; eşleşme için en düşük IoU 0,3'tür. Bir iz en az üç karede isabet almadan onaylanmaz (min_hits) ve on kareden uzun süre eşleşmeden kalırsa silinir (max_age).

Bu parametreleri ve eşleştirme yöntemini Bölüm 67'deki `Izleyici` sınıfından alıyoruz. Dört mod vardır: `acgozlu_iou` her adımda en yüksek IoU'lu çifti seçer (açgözlü), `macar_iou` tüm maliyet matrisi için Macar algoritmasını çalıştırır (bu, SORT'un eşleştirmesidir), `macar_tum` skor eşiği olmadan tüm tespitleri iz başlatmaya açar, `byte` ise iki aşamalıdır: önce yüksek skorlu tespitler, sonra kalan izler için düşük skorlu tespitler (Bölüm 67.16'daki ByteTrack fikri).

Sistemin takip performansı için MOTA (Multiple Object Tracking Accuracy) kullanıyoruz (Bölüm 67.17):

MOTA = 1 - (FN + FP + IDSW) / GT

Bu formüldeki her terimin bir anlamı var: FN bir kaçırmadır, FP bir yanlış iz, IDSW bir kimlik değişimi, GT ise gerçek nesne-kare sayısıdır. Test videosunda macar_iou ve kare dışı filtresi için sayılar şunlardır: FN = 94, FP = 205, IDSW = 24 ve GT = 1 735. MOTA = 1 - (94 + 205 + 24) / 1 735 = 1 - 0,186 = 0,814. Bu, tablodaki 0,8138 ile uyumludur. Elle hesabı yapmadan bir MOTA değerine güvenmeyin; bu formülü bir kez elle sürmek, neyin neyi düşürdüğünü görmenin en hızlı yoludur.

Takip kodu şu şekilde yazılmıştır. Önce izleyiciyi ve iz çıktısını üreten `takip` fonksiyonunu görürüz; `cerceve` parametresi, kare dışına çıkmış izleri çıktıdan gizler (iz kendisi silinmez, yalnızca çıktı kesilir).

{{KOD takip 1}}

Kodun ikinci parçası, tahmin ve sonuç toplamasını yapar. Her video için MOTA'yı hesaplayıp birleştiriyoruz; böylece tek bir uzun video yerine beş kısa videonun toplamı üzerinden ölçüm yapmış oluyoruz.

{{KOD takip 2}}

{{KOD takip 3}}

Ana fonksiyon önce doğrulama videolarında her mod ve her çerçeve seçeneği için ölçüm yapar. Seçim yalnızca doğrulama MOTA'sına göre yapılır; test ve kayma videoları seçimden sonra okunur. Bu kural bir ayarı test kümesine göre seçmemizi engeller, bu da Bölüm 57'deki kötü uygulamanın en yaygın biçimidir.

{{KOD takip 4}}

{{KOD takip 5}}

Son parça, secilen yapılandırmayla test videosu 0'ın iz çıktısını bir CSV'ye yazar; şekil 80.5 bu dosyadan çizilir.

{{KOD takip 6}}

{{CIKTI takip.txt python b80_takip.py}}

### Ne ölçüldü, ne seçildi

Doğrulama tablosu, dört modun iki çerçeve seçeneğiyle ne yaptığını gösterir. MOTA, FN ve IDSW, doğrulama videolarında (1 722 GT) ölçülmüştür.

| Mod | Çerçeve filtresi kapalı | Çerçeve filtresi açık | FP (açık) | IDSW (açık) |
|---|---|---|---|---|
| acgozlu_iou | 0,755 | 0,791 | 247 | 19 |
| macar_iou (seçilen) | 0,756 | 0,792 | 248 | 20 |
| macar_tum | 0,119 | 0,179 | 1 263 | 79 |
| byte | 0,609 | 0,640 | 524 | 28 |

İki sonuç hemen görülüyor. Birincisi, kare dışı filtresi her modda MOTA'yı yaklaşık 0,035 artırıyor. Bunun sebebi, kaybolan nesnenin izinin max_age süresince kalması ve bu süre boyunca tahmin kutusunun FP üretmesidir. Filtre bu hayalet izleri susturur. İkincisi, macar_tum felaketidir: skor eşiği olmadan her zayıf tespit yeni iz açar ve FP patlar. Bu, "daha fazla tespit daha iyi takip demektir" yanılgısının bedelidir.

Seçilen mod, macar_iou ile açgözlü eşleştirme arasındaki farkın yalnızca 0,001 olduğu bir yarışta kazandı. Bu fark gürültü düzeyindedir. Yine de SORT'u seçmek savunulabilir, çünkü Macar eşleştirmesi bir kez anlaşıldığında açgözlü olandan daha az sürprizlidir: her zaman küresel olarak en iyi toplamı verir. Karar, seçilen ilk kuralın sade olmasına dayanır; sonuçların bu kadar yakın olduğunu da bilerek.

Test ve kayma sonuçları aşağıdadır. Seçilen mod macar_iou ve çerçeve filtresi açıktır.

| Küme | Mod | MOTA | FN | FP | IDSW | GT |
|---|---|---|---|---|---|---|
| Test (nominal) | macar_iou (seçilen) | 0,814 | 94 | 205 | 24 | 1 735 |
| Test (nominal) | acgozlu_iou | 0,813 | 91 | 209 | 25 | 1 735 |
| Operasyonel kayma | macar_iou (seçilen) | 0,726 | 139 | 328 | 24 | 1 789 |
| Operasyonel kayma | byte | 0,349 | 104 | 975 | 86 | 1 789 |

R3 (test MOTA >= 0,90) geçilemedi: 0,814. R4 (IDSW <= %1 GT) da geçilemedi: 24 / 1 735 = %1,4. Bu bir başarısızlıktır ve nedenlerini bilmek gerekir. FN 94 kare-nesne, yani GT'nin yaklaşık yüzde 5,4'ü. Bunların büyük kısmı kenarda kalan ve küçük ya da bulanık nesnelerdir; yani dedektörün kaçırmalarıdır, takipçinin değil. FP 205'in bir kısmı kuş OOD nesnesinden gelir; kalanı, dedektörün nominal sahnelerdeki sahte tespitleri ile kesişme sırasında kısa ömürlü yanlış izlerdir. IDSW 24 ise 0 ve 1 numaralı nesnelerin kesişmesinde (Bölüm 67.18) yoğunlaşır: iki iz kesişme anında birbirinin kimliğini alır ve Macar eşleştirmesi bunu düzeltmek için tek bir kareye yetecek bilgiye sahip değildir.

Şekil 80.5, seçilen yapılandırmanın test videosu 0 üzerindeki çıktısını gösterir. Gri noktalar gerçek yörüngeleri, renkli noktalar ise iz kimliklerini gösterir. Nesneler 0 ve 1 yaklaşık 35. karede aynı bölgeden geçer; kimlik değişimi riski en çok bu aralıkta vardır. Şekil tek bir videonun görsel özetidir. Kimlik değişimlerinin toplam sayısı için yukarıdaki IDSW değerlerine bakın.

![Şekil 80.5: Test videosu 0'da iz yörüngeleri ve gerçek yörüngeler](gorseller/b80_takip.png)
