%% kisim_no: XIV
%% kisim_ad: Makine Öğrenmesi
%% bolum_no: 61
%% baslik: Denetimsiz Öğrenme

## Giriş: Etiketsiz veriden bilgi çıkarmak

Şimdiye kadar gördüğün makine öğrenmesi problemlerinin hepsinde bir cevap anahtarı vardı. Bölüm 54'te gördüğümüz gibi her örneğin yanında bir etiket bulunuyordu: bu kare bir hedef içeriyor, bu uçuş arızalı, bu hücre sağlam. Denetimli öğrenmede model girdi ile etiket arasındaki ilişkiyi bu çiftlerden öğrenir ve başarısını etiketlere karşı ölçer.

Gerçek dünyada etiket çoğu zaman yoktur ya da pahalıdır. Bir İHA'nın uçuş kaydındaki her iki saniyelik pencereyi bir uzmanın etiketlemesi haftalar sürer. Oysa ham veri bolca bulunur. Denetimsiz öğrenme (unsupervised learning) bu boşlukta çalışır: etiket olmadan veriden yapı çıkarmaya çalışır. Bu yapı dört biçimde karşımıza çıkar. Örnekleri benzerliklerine göre gruplamak (kümeleme), veriyi daha az boyuta sıkıştırmak (boyut indirgeme), verinin olasılık yoğunluğunu anlamak ve olağandışı örnekleri bulmak (anomali tespiti) bu dört işin tamamıdır.

Bu bölümde dört aileyi sıfırdan kuracağız: k-means ve karışım modelleri (EM) ile kümeleme, PCA ile doğrusal boyut indirgeme, t-SNE ve UMAP ile doğrusal olmayan gömme, Isolation Forest ile anomali tespiti. Her yöntemi önce numpy ile kendi kodumuzla yazacak, sonra scikit-learn'ün karşılığıyla karşılaştıracağız. Kendi kodun sklearn ile aynı sayıyı veriyorsa, hem kodun hem de anlayışın doğru demektir. Bu karşılaştırma bu bölümün en önemli alışkanlığıdır.

Savunma sanayiinde bu bölüm sık sık karşına çıkar. Bir uçağın sensör akışı kümelenip normal uçuş modları ayrılabilir. Normal uçuş bölgesinin dışına düşen bir pencere bakım ekibine işaretlenebilir. Bir görüntünün renk paleti sıkıştırılarak bant genişliği azaltılabilir. Mert'in EV Dashboard projesindeki batarya hücresi ölçümleri de aynı türden bir iştir: 96 hücrelik bir modülde etiket olmadan tek bir aykırı hücreyi bulmak.

::: not
Denetimsiz öğrenmede "doğru cevap" çoğu zaman yoktur. Bu yüzden her sonuç bir ölçütle birlikte değerlendirilmeli ve ölçütün tam olarak neyi ölçtüğü yazılmalıdır. Bölümün ilerisinde her yöntem için iki soruyu soracağız: Yöntem neyi bulmak için tasarlandı? Bulduğu şeyin gerçek olduğunu nasıl anlarız?
:::

## 61.1 Etiketsiz öğrenmenin sorusu ve değerlendirme zorluğu

Denetimli bir modelin başarısı basit bir soruyla ölçülür: Tahmin ettiğim etiket doğru mu? Denetimsiz modelde bu soru yoktur. Bir müşteri kümelemesi düşünelim. Algoritma üç küme bulsun. Bu üç küme "doğru" mudur? Cevap, kümelerin amacına bağlıdır. Pazarlama için anlamlıysa iyidir, bir veri işleme adımı için yeterince kararlıysa iyidir, hiçbir karar desteklemiyorsa gürültüden ibarettir. Yani değerlendirme, matematiksel bir ölçütle başlar ama iş bilgisiyle biter.

Pratikte üç tür ölçüt kullanılır. Birincisi **iç ölçütlerdir**: yalnızca veriye ve bölümlemeye bakarlar. Küme içi sıkılık ile kümeler arası ayrımı birlikte ölçen siluet skoru (61.4'te göreceğiz) buna örnektir. İkincisi **dış ölçütlerdir**: gerçek bir etiket bilindiğinde bölümlemeyi o etiketle karşılaştırırlar. Düzeltilmiş Rand indeksi (ARI) bu ailedendir. Üçüncüsü **model ölçütleridir**: olasılıksal modellerde log-olabilirlik ve bilgi kriterleri (BIC gibi), PCA'da yeniden yapılandırma hatası gibi değerler.

ARI, iki bölümlemedeki nokta çiftlerinin ne kadarının tutarlı davrandığını ölçer. Rastgele iki bölümleme arasında beklenen değere göre düzeltilmiştir. 1 tam uyumu, 0 rastgele bir bölümlemeyi, negatif değerler ise rastgeleden de kötü bir uyumu gösterir. Bu bölümdeki deneylerde gerçek etiketleri bildiğimiz sentetik verileri kullanacağız, böylece ARI'yi bir hakem olarak kullanabiliriz. Gerçek bir uygulamada bu hakem yoktur. O zaman yalnızca iç ölçütlere ve alan bilgisine güvenirsin. Bu fark, bölümün en çok unutulacak kısmıdır.

Son bir uyarı: Denetimsiz bir yöntemin "iyi" görünmesi, ölçütün yöntemi ödüllendirmesinden de kaynaklanabilir. Örneğin k-means, kümeleri daireselmiş gibi ayırdığı için siluet skorunu yüksek çıkarabilir, ama bu şekil varsayımı verinin gerçek yapısıyla uyuşmuyorsa sonuç yanıltıcıdır. Ölçütü de yöntem kadar sorgulamak gerekir.

## 61.2 k-means: amaç fonksiyonu ve Lloyd algoritması

k-means, en bilinen kümeleme yöntemidir. Girdi olarak n tane nokta x₁, ..., xₙ ∈ ℝᵈ ve küme sayısı k alır. Çıktı olarak her noktaya bir küme etiketi ve her küme için bir merkez μ_c verir. Yöntemin amacı açıktır: her nokta kendi kümesinin merkezine mümkün olduğunca yakın olsun. Bunu şöyle yazarız:

J = Σ_{c=1..k} Σ_{x ∈ C_c} ‖x − μ_c‖²

Burada C_c, c numaralı kümedeki noktaların kümesi ve μ_c = (1/|C_c|) Σ_{x ∈ C_c} x bu kümenin ortalamasıdır. J, **küme içi kareli hatalar toplamıdır** (SSE, sum of squared errors; sklearn'de "inertia" adıyla geçer). J'yi en küçükleyen atamayı bulmak, genel durumda hesaplama açısından zor bir problemdir (genel bilgi). Ama Lloyd algoritması, yerel bir minimuma çok hızlı yaklaşır ve iki basit adımdan oluşur.

Birinci adım **atamadır**. Merkezler sabit tutulur ve her nokta en yakın merkezine atanır. Bu, J'yi merkezler sabitken en küçük yapan atamadır. İkinci adım **güncellemedir**. Atamalar sabit tutulur ve her merkez kendi kümesinin ortalamasına taşınır. Bunun neden doğru olduğunu görmek için türev alabilirsin. Bir kümedeki kareli hata Σ‖x − μ‖² fonksiyonunun μ'ye göre türevi −2 Σ (x − μ)'dür. Bu türev sıfıra eşitlenirse μ = (1/|C|) Σ x çıkar. Bu, Bölüm 50'deki en küçük kareler ve gradyan sıfırlama fikrinin en basit hâlidir.

İki adımın da J'yi artırmadığını görmek için sırayla bakalım. Atama adımı, merkezler sabitken her noktayı en yakın merkeze koyar; bu J'yi küçültür ya da aynı bırakır. Güncelleme adımı, atamalar sabitken her merkezi kendi kümesinin ortalamasına taşır; ortalama kareli hatayı en küçükleyen sabit olduğu için J yine küçülür ya da aynı kalır. Kesin azalma sürdüğü sürece olası atama sayısı sonlu olduğu için algoritma sonlu adımda durur: ne atama ne merkez değişir. O noktada bir yerel minimumdayız. Ama genel minimumda olduğumuzun garantisi yoktur. Bunu 61.3'te başlatma yüzünden göreceğiz.

Aşağıdaki kod, iki adımı ayrı fonksiyonlar olarak yazar. Hiçbir sklearn çağrısı kullanılmaz; her şey numpy broadcasting ile yapılır (Bölüm 56'da gördüğümüz yayınlama bu kodda merkez-nokta uzaklık matrisini tek satırda hesaplar).

@@KOD b61_01_kmeans.py||def sse@@

Bu kodun ilk fonksiyonu `atama`, her nokta ile her merkez arasındaki kareli uzaklığı tek bir üç boyutlu diziyle hesaplar. `X[:, None, :]` ile `C[None, :, :]` çıkarıldığında (n, k, d) şeklinde bir fark dizisi oluşur. `argmin` her noktanın en yakın merkezinin indeksini verir. `sse` ise seçilen atamaya göre J'yi döndürür. `guncelle` yalnızca boş olmayan kümelerin merkezini yeniden hesaplar. Boş kalan bir kümenin merkezi eski değerinde kalır; bu, algoritmanın çökmesini önleyen basit bir kuraldır.

@@KOD b61_01_kmeans.py|def sse|def lloyd@@

`lloyd` döngüsü her turda önce atar, J'yi kaydeder, sonra merkezleri günceller. Kaydedilen J dizisi, algoritmanın gerçekten azalıp azalmadığını kontrol etmemizi sağlar. Döngü, merkezler bir daha değişmeyince durur.

@@KOD b61_01_kmeans.py|def lloyd|def kmeanspp@@

Deneyin ilk kısmı, tek bir tohumla üretilmiş üç kümeli bir veride J'nin iterasyonlar boyunca nasıl değiştiğini gösterir. Veri `make_blobs` ile üretilir ve sabit tohumla (`random_state=61`) üretildiği için her çalıştırmada aynı sayılar çıkar.

@@KOD b61_01_kmeans.py|def bolum_a_amac|def bolum_b_baslangic@@

@@OUT out_01.txt|python b61_01_kmeans.py|A) J|B) rastgele@@

Çıktının ilk satırı J'nin beş iterasyonda 4626,74'ten 609,51'e düştüğünü gösteriyor. Dikkat et: düşüş her adımda monoton. "J hiç artmadı mi: True" satırı bu gözlemi programın kendisine doğrulatır. Bu kontrol önemlidir, çünkü bir kümeleme kodu yanlış yazıldığında çoğu zaman hata vermez, sadece sessizce kötü sonuç üretir. Monotonluk kontrolü, en ucuz hata ayıklama araçlarından biridir.

Şekil 61.1, aynı mekanizmayı iki boyutta gösterir. Veri 60 noktadan oluşur ve üç kümeye aittir. Başlangıç merkezleri kasıtlı olarak kötü seçilmiştir: en soldaki üç nokta. Her panel bir adımda hangi noktanın hangi merkeze atandığını (renk) ve merkezlerin nereye taşındığını (X) gösterir. Bu şekil için veri üreten fonksiyon `kmeans_iz`'dir; veri `engine/veri/b61_kmeans_iz.csv` dosyasına yazılır ve şekil oradan okunur.

@@KOD b61_07_boyut_iz.py||def boyut_laneti@@

@@KOD b61_07_boyut_iz.py|def kmeans_iz|if __name__@@

![Şekil 61.1: Lloyd iterasyonları (2B, 60 nokta, k=3). Adım 1'den 4'e: atamalar (renk) ve o adımdaki merkezler (X). Beşinci adımda merkezler değişmez.](gorseller/b61_kmeans_iter.png)

Şekilde ilk iki adımda merkezlerin büyük sıçramalarla yer değiştirdiğini, sonra ise yalnızca küçük düzeltmeler yaptığını görürsün. Bu, Lloyd'un tipik davranışıdır: ilk adımlar kabaca bir bölünme bulur, sonrakiler sınırı ince ayarlar. Son adımda merkezler yerinde durur. Ama başlangıç farklı olsaydı aynı veride farklı bir yerel minimum bulunabilirdi. Bunu sayılarla görmek için 61.3'e geçelim.

## 61.3 Başlatma: yerel minimum ve k-means++

Lloyd algoritmasının zayıf noktası başlangıçtır. Merkezleri veri noktalarından rastgele seçmek en basit yoldur, ama iki merkez aynı kümeye düşerse algoritma bunu telafi edemez. Yanlış bir bölünme, iterasyonlar boyunca "kilitlenir". Üstelik bu kilit, sonuç her zaman aynı görünebilir: tek bir çalıştırma size yerel minimumun yerel olduğunu söylemez.

k-means++ (Arthur ve Vassilvitskii, 2007) bu sorunu akıllı bir olasılık kuralıyla çözer. İlk merkez tüm noktalar arasından rastgele seçilir. Sonraki her merkez ise, zaten seçilmiş merkezlere olan en yakın uzaklığın karesi D(x)² ile orantılı bir olasılıkla seçilir:

P(x) = D(x)² / Σ_y D(y)²

Sezgi basittir. Zaten bir merkezin yanında olan noktaların seçilme olasılığı düşüktür; henüz hiçbir merkezin yakınında olmayan noktalar yüksek olasılıkla seçilir. Yani başlangıç merkezleri birbirinden uzak ve veriyi yayan bir dağılım oluşturur. Rastgelelik hâlâ vardır, ama dağılım kötü bir başlangıca kaymaz. Arthur ve Vassilvitskii, bu başlangıcın beklenen SSE'sinin en iyi çözümün O(log k) katı içinde olduğunu gösterdi (literatürdeki bilinen sonuç).

Pratikte iki ayrıntı önemlidir. Birincisi, sklearn her yeni merkez için birkaç aday çeker ve toplam kareli uzaklığı en çok azaltan adayı seçer. Bu "yerel deneme" (greedy) yaklaşımıdır ve aday sayısı varsayılan olarak 2 + ln k'dır. Bu ayrıntıyı Kod Okuma bölümünde gerçek kaynaktan göreceğiz. İkincisi, k-means++ yine yerel minimumu garanti etmez; yalnızca kötü başlangıç olasılığını düşürür. Bu yüzden pratikte birkaç başlangıç (`n_init`) denemek ve en düşük SSE'yi seçmek yaygındır.

Aşağıdaki kod iki başlangıcı da sıfırdan yazar. `kmeanspp` her merkezi olasılıkla seçer; sklearn'deki gibi her adımda birkaç yerel aday deneyip en iyisini tutar.

@@KOD b61_01_kmeans.py|def kmeanspp|def rastgele_baslangic@@

@@KOD b61_01_kmeans.py|def rastgele_baslangic|def silhouette_sifirdan@@

Deney, 500 noktalı beş kümeli bir veride her iki başlangıçla 200 farklı tohum çalıştırır. Her çalıştırmanın son SSE'si ve iterasyon sayısı kaydedilir. "En iyi olmayan" yüzde, bulunan en düşük SSE'den (306,57) daha yüksek bir sonuca yakınsayan çalıştırmaların oranıdır. Bu sayı, yerel minimuma takılma oranının bir ölçüsüdür.

@@KOD b61_01_kmeans.py|def bolum_b_baslangic|def bolum_c_dirsek@@

@@OUT out_01.txt|python b61_01_kmeans.py|B) rastgele|C) k=1@@

Sonuçlar net. Rastgele başlangıçta çalıştırmaların %11,5'i en iyi çözümün üstünde kaldı ve en kötü çalıştırmanın SSE'si 718,75'e çıktı. k-means++ ile bu oran %1,0'a düştü ve en kötü SSE 688,74 oldu. İterasyon sayısı da yaklaşık yarıya indi (ortalama 8,8'den 4,0'a). Bu, k-means++'ın iki yönden de işe yaradığını gösterir: daha az yerel minimum ve daha hızlı yakınsama. Dikkat et: her iki yöntemde de medyan çalıştırma en iyi çözüme ulaşıyor. Sorun, nadir ama maliyetli kötü başlangıçlardadır. Bu yüzden tek bir çalıştırmanın sonucuna güvenmek yanıltıcı olabilir.

![Şekil 61.2: 200 tohumda son SSE dağılımı (solda) ve en iyi olmayan yakınsama oranı (sağda). Kesik çizgi bulunan en düşük SSE'dir. Veri engine/veri/b61_kmeans_init.csv dosyasındandır.](gorseller/b61_kpp_dagilim.png)

Şekil 61.2'de sol paneldeki dağılım bu sayıları görselleştirir. Kesik çizgide yoğunlaşan büyük çoğunluk en iyi çözümdür; sağdaki yüksek sütun ise rastgele başlangıcın sahip olduğu kötü kuyruğu gösterir. Bu tür bir dağılım, kümeleme sonuçlarını raporlarken tek bir sayı yerine dağılım vermenin neden önemli olduğunu açıkça gösterir. Bu sonuçlar bu veri ve bu k için geçerlidir; başka bir veride oranın farklı olması normaldir ve tekrar ölçülmelidir.

## 61.4 Kaç küme? Dirsek, siluet ve k-means'in sınırları

Lloyd ve k-means++ verilen bir k için çalışır, ama gerçek veride k bilinmez. Kaç küme olduğuna karar vermek kümelemenin en zor kısmıdır, çünkü J'nin kendisi k arttıkça her zaman azalır (k = n olduğunda her nokta kendi kümesidir ve J = 0). Bu yüzden J'nin mutlak değerine değil, azalmasının nasıl değiştiğine bakarız.

**Dirsek yöntemi** J(k) eğrisini çizer ve kazancın keskin biçimde düştüğü "dirseği" arar. Eğer k'dan k+1'e geçmek J'yi çok az azaltıyorsa, ek küme fazla gelir. Bu yöntem görsel ve bir miktar öznel bir karardır.

**Siluet skoru** küme yapısını doğrudan ölçmeye çalışır. Her nokta i için a(i), aynı kümedeki diğer noktalara ortalama uzaklıktır (küme içi sıkılık). b(i) ise i'nin en yakın başka kümedeki noktalara ortalama uzaklığıdır. Siluet

s(i) = (b(i) − a(i)) / max(a(i), b(i))

ile [−1, 1] aralığında bir değer alır. 1'e yakın değerler noktanın kendi kümesinde sıkı, komşu kümeden uzak olduğunu; 0 civarı değerler sınırda olduğunu; negatif değerler ise yanlış kümede olabileceğini gösterir. Ortalama siluet, bölümlemenin bir özetidir. Aşağıdaki fonksiyon bu tanımı doğrudan uygular: n × n uzaklık matrisi ile her nokta için a ve b hesaplanır.

@@KOD b61_01_kmeans.py|def silhouette_sifirdan|def bolum_a_amac@@

Aşağıdaki deney 600 noktalı, gerçek olarak dört kümeli bir veride k = 1'den 8'e kadar k-means çalıştırır. Her k için sklearn'ün inertia ve siluet değerleri ile sıfırdan yazdığımız siluet karşılaştırılır. Dört kümeli bir veri kullandığımız için dirseğin 4'te kırılmasını bekleriz. Bu beklenti bir ölçüttür, ama sonucu biz bilmeden okumalıyız.

@@KOD b61_01_kmeans.py|def bolum_c_dirsek|def bolum_d_halka@@

@@KOD b61_01_kmeans.py|def bolum_d_halka|@@

@@OUT out_01.txt|python b61_01_kmeans.py|C) k=1|D) halka@@

Çıktı iki şeyi açıkça gösterir. Birincisi, sıfırdan siluet ile sklearn'ün siluet değeri her k için aynıdır; en büyük fark 1,1 · 10⁻¹⁶'dır, yani makine epsilonu düzeyindedir. Bu, kodun doğruluğunun bir kanıtıdır. İkincisi, iki ölçüt aynı cevabı vermez. Siluet k = 2'de en yüksektir (0,6966) ve k arttıkça monoton düşer. Dirsek ise belirgin bir kırılmayı k = 4 civarında gösterir: k = 2'den 3'e düşüş 1566 birim, 3'ten 4'e 645, 4'ten 5'e yalnızca 111 birimdir. Bu, veriyi üretirken kullandığımız gerçek küme sayısına karşılık gelir.

![Şekil 61.3: Dirsek (solda) ve siluet (sağda). Kesik çizgi gerçek küme sayısı olan k=4'ü gösterir. Siluet k=2'yi, dirsek k=4'ü öne çıkarır.](gorseller/b61_dirsek_siluet.png)

Şekil 61.3 bu tabloyu iki grafikte gösterir. Burada öğretici bir ders var: iki ölçüt çelişiyor ve hangisine güveneceğine sen karar vermek zorundasın. Siluet daha "temiz" bir sayı verir, ama yalnızca iki kümeye bölmenin lehinedir. Dirsek ise gerçek yapıyla uyumlu bir kırılma verir ama görsel olarak yorumlanır. Pratikte iki ölçütü birlikte, bir de alan bilgisini kullanarak karar verilir. Tek bir sayının "en iyi k"yi söylediğine inanma.

Şimdi k-means'in en önemli sınırına bakalım. k-means, kümeleri merkezlerine olan öklid uzaklığıyla ayırır. Bu, kümelerin yaklaşık küresel (her yönde aynı yayılımlı), benzer boyutlu ve benzer yoğunlukta olduğunu varsayar. Bu varsayım bozulduğunda k-means yanlış sonuç üretir. Aşağıdaki deney iç içe iki halkadan oluşan bir veri kümesi üretir. Halkalar açıkça ayrıdır, ama merkezler halkaların ortasına düşeceği için k-means onları radyal olarak değil, açısal olarak bölmeye çalışır. Bu deneyde halka verisinde k-means'in ARI'si sıfıra yakın çıkmıştır: yani kümeleme, gerçek yapıyla rastgele bir uyum göstermektedir.

![Şekil 61.4: İç içe iki halkada k-means (solda) ve DBSCAN (sağda). k-means halkaları ayıramaz, iki kümeyi açısal olarak böler; DBSCAN iki halkayı bağımsız olarak bulur (gri: gürültü).](gorseller/b61_halka_kmeans_dbscan.png)

Şekil 61.4'ün sol panelinde k-means'in halkayı ikiye kestiğini görüyorsun. Sağ paneldeki DBSCAN ise iki halkayı birbirinden ayırır. Bu fark, yöntemin şekil varsayımından kaynaklanır: DBSCAN "yoğun bölgeleri" bulur, k-means ise "merkezleri". DBSCAN'i 61.6'da sıfırdan yazacağız. Şu an için şunu not et: k-means'in başarısızlığı kodun hatası değil, modelin varsayımının sonucudur. Bu tür yöntem seçimlerinde verinin şeklini çizmek her zaman ilk adımdır.

## 61.5 Hiyerarşik kümeleme ve bağlantı türleri

k-means düz bir bölümleme üretir: tek bir k seçersin ve bir bölümleme alırsın. Hiyerarşik kümeleme ise tüm ağacı üretir. Aglomeratif (birleştirici) yaklaşımda her nokta kendi kümesi olarak başlar. Her adımda en yakın iki küme birleştirilir ve tek bir küme kalana kadar devam edilir. Sonuç bir **dendrogram**dır: hangi kümelerin hangi uzaklıkta birleştiğini gösteren ağaç. Dendrogramı istediğin yükseklikte kesersin ve o yüksekliğin üstündeki birleşmeler kalmaz. Böylece tek bir çalıştırmadan tüm k değerlerini görürsün.

Asıl karar "en yakın kümeler" ifadesindeki uzaklığın nasıl tanımlandığıdır. Bu tanıma **bağlantı türü** (linkage) denir.

- **Tek bağlantı** (single): iki küme arasındaki uzaklık, en yakın iki noktanın uzaklığıdır. Uzun ve ince yapıları izleyebilir, ama köprü noktalarıyla iki kümeyi zincirleyebilir. Buna zincirleme etkisi denir.
- **Tam bağlantı** (complete): en uzak iki noktanın uzaklığıdır. Kompakt kümeler üretir ama uzun yapıları böler.
- **Ortalama bağlantı** (average): tüm nokta çiftlerinin ortalama uzaklığıdır. İki uç arasında bir dengedir.
- **Ward bağlantısı**: birleşmenin neden olduğu küme içi SSE artışını en küçük tutar. İki küme a ve b için bu artış (n_a n_b / (n_a + n_b)) ‖μ_a − μ_b‖² ile verilir. Ward, k-means'in SSE amacını hiyerarşik olarak uygular; bu yüzden küresel kümelerde k-means'e en yakın davranış budur.

Bu dört bağlantının birleşme sırası farklıdır ve bu yüzden sonuçları farklıdır. Aşağıdaki deney üç veri üzerinde bu dört bağlantıyı, k-means'i ve DBSCAN'i karşılaştırır. Birinci veri üç küme (toplar), ikincisi iki ay biçimli küme, üçüncüsü ise iki kümeyi 30 gürültülü ara noktayla birbirine bağlayan bir köprü verisidir. Köprü verisinde ARI yalnızca gerçek kümelerdeki 200 noktada hesaplanır; köprü noktalarının gerçek etiketi yoktur.

@@KOD b61_08_hiyerarsi.py||def main@@

@@KOD b61_08_hiyerarsi.py|def main|@@

@@OUT out_08.txt|python b61_08_hiyerarsi.py|||@@

Sonuçlar bağlantı türünün önemini açıkça gösterir. Toplar verisinde tek bağlantı 0,5601 ARI ile zayıf kalır. Boyutlar 200, 98 ve 2 olduğu için büyük kümenin muhtemelen iki gerçek kümenin birleşmesi, iki noktalık kümenin ise bir uç nokta grubu olduğu görülüyor. Tam, ortalama ve Ward bağlantıları 0,92 ile 0,94 arasında, k-means ise 0,9703 ile en yüksek değeri verir. Ay verisinde durum tersine döner: tek bağlantı ARI = 1,0 ile iki ayı mükemmel ayırır, k-means ise yalnızca 0,2408 alır. Bu, ay gibi uzayan şekiller için tek bağlantının doğal seçim olduğunu gösterir.

Köprü verisi zincirleme etkisini en açık gösteren örnektir. Tek bağlantı, iki kümeyi ara noktalarla birleştirdi ve 228 + 2 bölünmesi üretti. Gerçek iki küme ayrılmadı; ARI 0,0002. Tam, ortalama ve Ward bağlantıları aynı veriyi 122 + 108 olarak doğru böldü. Bu fark, tek bağlantının yerel yakınlığa ne kadar hassas olduğunu gösterir: bir tane köprü nokta bile iki kümeyi birleştirebilir.

Bu deneyde DBSCAN'in toplar verisindeki başarısızlığı da dikkat çekicidir. ε = 0,2 bu veri için çok küçüktür; 261 nokta gürültü olarak işaretlenmiştir ve ARI 0,0076'dır. Bu bir yöntemin kötü olduğu anlamına gelmez; parametrenin veriye uyumlanması gerektiğini gösterir. DBSCAN'i bir sonraki alt bölümde ayrıntılı göreceğiz.

![Şekil 61.5: Aynı 30 noktalı veride tek bağlantı (solda) ve Ward (sağda) dendrogramları. Dikey eksen birleşme uzaklığıdır. Tek bağlantıda küme birleşmeleri daha geç ve daha düzensizdir.](gorseller/b61_dendrogram.png)

Şekil 61.5 bir dendrogramın nasıl okunacağını gösterir. Dikey eksen birleşmenin gerçekleştiği uzaklıktır. Her yatay çizgi iki kümenin birleştiği yeri gösterir; çizginin yüksekliği, o birleşmenin ne kadar "pahalı" olduğunudur. Bir dendrogramda uzun dikey çizgiler kümeleri ayıran büyük boşluklardır. Dendrogramı kesmek için yatay bir çizgi çekersin; çizginin kestiği dikey çizgi sayısı küme sayısını verir. Burada tek bağlantının dendrogramı, Ward'a göre daha düzensiz bir merdiven gibidir; bu düzensizlik zincirleme eğiliminin görsel izidir.

Hiyerarşik kümelemenin bir maliyeti vardır. Uzaklık matrisi n × n'dir, bu nedenle bellek ve hesap n² ile büyür. Büyük veride (on binlerce nokta) bu yöntem pahalıdır. k-means ise her iterasyonda O(nkd) çalışır. Bu fark seçimini etkileyen pratik bir etkendir.

## 61.6 DBSCAN: yoğunluk tabanlı kümeleme

k-means ve hiyerarşik kümeleme noktaların merkeze ya da komşuya olan uzaklığına bakar. DBSCAN (Density-Based Spatial Clustering of Applications with Noise) farklı bir soru sorar: Bu nokta yoğun bir bölgenin içinde mi? İki parametresi vardır. ε (epsilon) komşuluk yarıçapıdır. minPts, bir bölgeyi yoğun saymak için gereken en az nokta sayısıdır. Noktanın kendisi de bu sayıya dahildir; sklearn'ün `min_samples` parametresi bu tanımı kullanır.

Tanımlar şöyledir. Bir p noktasının ε-komşuluğu N_ε(p), uzaklığı ε'dan küçük ya da eşit olan tüm noktalardır. p, |N_ε(p)| ≥ minPts ise **çekirdek** noktadır. Bir q noktası, bir çekirdek p'nin komşusuysa p'den **doğrudan erişilebilir**dir. Çekirdek zinciri üzerinden erişilebilen noktalar aynı kümeye girer. Çekirdek olmayan ama bir çekirdeğin komşusu olan noktalara **sınır** noktası denir. Hiçbir çekirdeğe bağlı olmayan noktalar **gürültü** (−1 etiketi) olarak kalır.

Algoritma çok basittir. Henüz ziyaret edilmemiş bir çekirdek noktadan yeni bir küme başlatılır. Bu noktanın komşuları bir yığına (stack) konur. Yığından her çekirdek nokta çıkarılır ve komşuları da yığına eklenir. Yığın boşalınca küme tamamdır ve sıradaki ziyaret edilmemiş çekirdek noktaya geçilir. Bu, Bölüm 17'deki bağlantılı bileşen (connected component) aramasının yoğun noktalar üzerinde yapılmış hâlidir. Bu yüzden DBSCAN'in küme sayısını önceden bilmesi gerekmez; kümeler veriden kendiliğinden çıkar.

DBSCAN'in güçlü yanları iki tanedir. Birincisi, küme şekli serbesttir: halka, ay ya da düzensiz bir bulut aynı şekilde bulunur. İkincisi, gürültüyü açıkça ayırır. Zayıf yanları da bilinmelidir. Parametreler veriye bağlıdır ve ε tek bir değerle tüm yoğunlukları yakalayamaz; yoğunluğu çok farklı kümeleri aynı anda bulmak zordur. Yüksek boyutta ise uzaklıklar birbirine yaklaştığı için "yoğun" kavramı zayıflar; bunu 61.8'de göreceğiz. ε seçimi için yaygın bir yol, her noktanın k-inci en yakın komşusuna olan uzaklığını sıralayıp dizinin kırıldığı yeri aramaktır (genel bilgi).

Aşağıdaki kod DBSCAN'i sıfırdan yazar. Komşu listesi, uzaklık matrisinden bir kez hesaplanır; sonra yukarıda tarif ettiğimiz yığın mantığı uygulanır. Sonuçları sklearn'ün `DBSCAN` çıktısıyla karşılaştırmak için aynı parametreler kullanılır.

@@KOD b61_02_dbscan_gmm.py||def dbscan@@

@@KOD b61_02_dbscan_gmm.py|def dbscan|def gauss_pdf@@

Deney, iç içe iki halkadan oluşan veride ε değerini değiştirir. minPts her seferinde 5'tir. Her çalıştırmada küme sayısı, gürültü sayısı ve gerçek etiketlerle ARI yazdırılır. Ayrıca sklearn'ün ARI'siyle karşılaştırılır; iki bölümleme aynıysa bu değer 1 çıkmalıdır.

@@KOD b61_02_dbscan_gmm.py|def bolum_a_dbscan|def uc_kume_veri@@

@@OUT out_02.txt|python b61_02_dbscan_gmm.py|A) DBSCAN|B) EM@@

Sonuçlar ε'nun etkisini net gösterir. ε = 0,08 çok küçüktür; halkalar parçalanır, beş küme oluşur ve 12 nokta gürültü sayılır. Bu durumda gerçek etiketlerle ARI 0,8273'tür. ε = 0,12, 0,15 ve 0,25 değerlerinde ise iki halka tam olarak ayrılır ve ARI 1,0 olur. Sıfırdan yazdığımız kodun sklearn ile her ε değerinde aynı bölümlemeyi vermesi (ARI sklearn ile 1,0000) doğruluğun ikinci kanıtıdır. Dikkat: 0,25 değerine kadar iki halka ayrık kalmıştır; daha büyük ε değerlerinde iki halka birleşebilir. Bu deneyde bunu test etmedik, ama parametre aralığının kenarlarında ne olacağını görmek her zaman gerekir.

Şekil 61.4'teki sağ panel bu sonuçların görsel hâlidir: iki halka DBSCAN ile bağımsız iki küme olarak çıkar, gürültü gri gösterilmiştir.

## 61.7 Karışım modelleri ve EM algoritması

k-means her noktayı tek bir kümeye sert biçimde atar. Oysa birçok veri, bir noktanın birden fazla kümeye ait olma olasılığını taşır: bir uçuş penceresi "seyir" ile "alçalış" arasında kalabilir. Karışım modeli (mixture model) bu fikri olasılıklı olarak yazar. Veri, k tane Gauss bileşeninden birinden üretilmiş kabul edilir:

p(x) = Σ_{k=1..K} π_k N(x | μ_k, Σ_k)

Burada π_k bileşen ağırlığıdır (Σπ_k = 1, π_k ≥ 0), N(x | μ, Σ) çok değişkenli normal yoğunluktur. Bu model Gauss Karışım Modeli (GMM) olarak bilinir. Her x_i için hangi bileşenden geldiği gizli bir değişken z_i'dir. Bu değişken gözlenmediği için doğrudan en çok olabilirlik çözümü kapalı biçimde bulunamaz. Log-olabilirlik

L = Σ_i ln Σ_k π_k N(x_i | μ_k, Σ_k)

içindeki log-toplam (log-sum) yüzünden türevi sıfıra eşitlemek kapalı biçimli bir çözüm vermez. Bu tam olarak EM (Expectation–Maximization, beklenti–en büyükleme) algoritmasının çözdüğü problemdir.

EM iki adım tekrarlar. **E adımında** her noktanın her bileşene ait olma olasılığı, yani sorumluluğu hesaplanır:

γ_ik = π_k N(x_i | μ_k, Σ_k) / Σ_j π_j N(x_i | μ_j, Σ_j)

**M adımında** bu sorumluluklar ağırlık olarak kullanılıp parametreler yeniden hesaplanır. N_k = Σ_i γ_ik ("etkin nokta sayısı") olmak üzere:

π_k = N_k / n,   μ_k = (1/N_k) Σ_i γ_ik x_i,   Σ_k = (1/N_k) Σ_i γ_ik (x_i − μ_k)(x_i − μ_k)ᵀ

M adımındaki formüller, Bölüm 49.8'de gördüğümüz en çok olabilirlik tahmininin sorumluluklarla ağırlıklandırılmış hâlidir. Yani EM, her adımda gizli atamayı tahmin edip sonra o tahmine göre MLE yapar. Bu döngü log-olabilirliği azaltmaz; bu, EM'in temel teoremidir (Dempster, Laird ve Rubin, 1977; genel bilgi). Aşağıdaki kod bunu her iterasyonda kontrol eder.

Şimdi k-means ile bağlantıyı görelim. GMM'de sorumluluklar 0 ile 1 arasındadır ve bu, sert atamanın yumuşak karşılığıdır. Eğer tüm bileşenlerin kovaryansı aynı σ²I biçimindeyse ve σ → 0 giderse, sorumluluklar 0 ya da 1'e yaklaşır ve M adımı k-means'in merkez güncellemesine döner. Yani k-means, GMM'nin "sert atamalı, eşit küresel kovaryanslı" özel durumudur. Bu ilişkiyi bilmek, k-means'in neden küresel kümelerde iyi, elipsoidal kümelerde zayıf olduğunu da açıklar.

Aşağıdaki kod, tam kovaryanslı bir GMM'yi EM ile sıfırdan eğitir. Başlangıç parametreleri k-means sonucundan alınır (bu yaygın bir pratiktir). E ve M adımları `em` fonksiyonunda, log-olabilirlik her E adımında kaydedilir. Yoğunluk fonksiyonu `gauss_pdf` ile hesaplanır; tersi ve determinant alınarak `einsum` ile karesel form hesaplanır.

@@KOD b61_02_dbscan_gmm.py|def gauss_pdf|def bolum_a_dbscan@@

Deney, üç bileşenli bir veriyi üretmek için iki boyutlu bir toplar verisini bir doğrusal dönüşümle yayar ve bileşen 1'i eksenlerde sıkıştırır. Böylece bileşenler farklı şekil ve yönlerde elipsler oluşturur. Başlangıç, k-means çıktısından alınır; sonra sıfırdan EM 60 iterasyon çalışır ve sklearn'ün `GaussianMixture`'ı aynı başlangıçla çalıştırılarak parametreler karşılaştırılır.

@@KOD b61_02_dbscan_gmm.py|def uc_kume_veri|def bolum_b_em@@

@@KOD b61_02_dbscan_gmm.py|def bolum_b_em|yol = os.path.join(VERI, "b61_em_llh.csv")@@

@@KOD b61_02_dbscan_gmm.py|yol = os.path.join(VERI, "b61_em_llh.csv")|def bolum_c_bic@@

@@OUT out_02.txt|python b61_02_dbscan_gmm.py|B) EM|C) BIC@@

Çıktıda üç şey önemli. İlki, log-olabilirlik ilk değer −2314,9358'den son değer −2302,8645'e çıkmıştır ve "llh hiç azalmadı mı: True" satırı her iterasyonda artışın negatif olmadığını doğrular. En büyük artış ilk iterasyonda, 9,3323 olarak gerçekleşir; sonra artışlar hızla sıfıra iner. Deneyde 60 iterasyon sabit sayıda çalıştırıldı; yakınsama kriteri kullanmadık. İkincisi, ortalama log-olabilirlik sıfırdan kodumuzda ve sklearn'de −3,838108 olarak aynı çıkar. Üçüncüsü, bileşen ortalamaları üç ondalıkta birbirine çok yakındır; en büyük fark 6,026 ile 6,025 arasındaki 0,001'dir. Bu fark, sklearn'ün kendi yakınsama toleransından kaynaklanır.

Şekil 61.6 bu sonucu görsel olarak verir. Sol panelde her bileşenin 1σ (kesik) ve 2σ (düz) elipsleri ve ortalaması (+) gösterilir. Sağ panelde iterasyonla log-olabilirlik eğrisi çıkar; eğri yukarı doğru tek yönlüdür ve altı yedi iterasyondan sonra düzleşir.

![Şekil 61.6: GMM bileşenleri (solda; kesik 1σ, düz 2σ elipsler, + bileşen ortalaması) ve EM log-olabilirliği (sağda; her iterasyonda artar). Veri engine/veri/b61_gmm_bilesen.csv ve b61_em_llh.csv dosyalarındandır.](gorseller/b61_gmm_em.png)

Bileşen sayısı K'yı da veriden seçmek gerekir. Log-olabilirlik K arttıkça her zaman artar, çünkü daha fazla parametre daha esnek bir model demektir. Bu yüzden bilgi kriterleri modelin karmaşıklığını cezalandırır. Bayesçi bilgi kriteri (BIC) şöyle tanımlanır:

BIC = −2 ln L + p ln n

Burada p serbest parametre sayısıdır. Tam kovaryanslı d boyutlu K bileşen için p = (K − 1) + K d + K d(d + 1)/2'dir: ağırlıklar, ortalamalar ve simetrik kovaryanslar. BIC küçük olan model tercih edilir. Ceza terimi p ln n, parametre sayısıyla birlikte büyür; bu yüzden fazla bileşen eklemek bir noktadan sonra BIC'i yükseltir.

Aşağıdaki deney K = 1'den 6'ya kadar sklearn ile GMM eğitir, her biri için BIC'i hesaplar ve formülle karşılaştırır.

@@KOD b61_02_dbscan_gmm.py|def bolum_c_bic|if __name__@@

@@KOD b61_02_dbscan_gmm.py|if __name__|@@

Çıktıda her K için iki BIC değeri vardır: sklearn'ün `bic` fonksiyonu ve elle yazdığımız formül. İkisi her satırda aynı çıkar; bu, parametre sayısı formülünün doğru olduğunu gösterir. En küçük BIC K = 3'te (4714,66) bulunur. Veriyi üç bileşenle ürettiğimiz için bu beklenen bir sonuçtur, ama önemli olan modelin bu seçimi kendi başına yapabilmesidir.

## 61.8 Boyutun laneti

Şimdiye kadar kullandığımız uzaklık ölçüleri iki ya da üç boyutta sezgisel olarak anlamlıdır. Boyut arttıkça ise tuhaf bir şey olur: rastgele noktalar arasındaki uzaklıklar birbirine yaklaşır. Bir sorgu noktasına en yakın ve en uzak noktalar arasındaki göreli fark küçülür. Bu olguya boyutun laneti denir ve kümeleme, komşuluk aramaları ve anomali tespitinin hepsini etkiler. Eğer her nokta diğerlerine neredeyse eşit uzaklıktaysa, "yakın komşu" kavramı ayırt edici olmaktan çıkar.

Aşağıdaki deney bunu sayısal olarak gösterir. Birim küpte (her boyutta [0,1] aralığında) 500 rastgele nokta üretilir. Rastgele 20 sorgu noktası için en uzak ve en yakın noktanın uzaklıkları ölçülür; oran (Dmaks − Dmin) / Dmin her boyutta ortalanır. Oran ne kadar küçükse, en uzak ve en yakın nokta birbirinden o kadar ayırt edilemez demektir. Her boyut için farklı bir tohum kullanılır (61 + d).

@@KOD b61_07_boyut_iz.py|def boyut_laneti|def kmeans_iz@@

@@KOD b61_07_boyut_iz.py|if __name__|@@

@@OUT out_07.txt|python b61_07_boyut_iz.py|A) boyutun|@@

Tablo oranın boyutla hızla düştüğünü gösterir. Bir boyutta (d = 1) en uzak nokta ile en yakın nokta arasındaki fark, en yakın noktanın uzaklığına göre çok büyüktür ve oran 7306 gibi devasa bir değerdir. Bu, tek boyutta tesadüfen çok yakın bir noktanın bulunmasının sonucudur ve oran ölçeğini bozar; ama önemli olan eğilimdir. d = 10'da oran 2,47'ye, d = 100'de 0,40'a, d = 1000'de 0,12'ye düşer. Yani 1000 boyutta bile en uzak nokta en yakın noktanın yalnızca yaklaşık %12 kadar uzağındadır. Bu, rastgele veride uzaklık tabanlı yöntemlerin neden zorlandığını açıklar.

![Şekil 61.7: Boyut arttıkça (Dmaks − Dmin)/Dmin oranı düşer (log-log ölçek). Veri engine/veri/b61_boyut_laneti.csv dosyasındandır.](gorseller/b61_boyut_laneti.png)

Şekil 61.7 bu eğilimi log-log ölçekte gösterir. Burada bir ayrıntıyı vurgulamak gerekir: gerçek veri rastgele değildir. Gerçek uygulamalarda veri genellikle düşük bir içsel boyuta (intrinsic dimension) yakın bir yüzeyde yaşar; bu yüzden etki rastgele küpte gösterdiğimiz kadar sert olmayabilir. Yine de yüksek boyutlu öznitelik uzaylarında (ör. 64 pikselli görüntüler, yüzlerce sensör kanalı) uzaklık temelli yöntemleri kullanmadan önce bu etkiyi ölçmek gerekir. Çözümlerden biri boyut indirgemedir; sonraki alt bölümde PCA ile bunu yapacağız.

## 61.9 PCA: kovaryans, özvektör ve SVD

Ana bileşen analizi (PCA, Principal Component Analysis), veriyi en çok yayıldığı yönlere döndürme işidir. Düşünsel olarak basit: bir bulut düşün; bu bulutun en uzun ekseni, ikinci en uzun ekseni ve böyle devam eder. İlk birkaç eksen verinin çoğu değişkenliğini taşıyorsa, kalan eksenleri atarak veriyi az boyutta özetleyebilirsin. PCA'nın bunu nasıl başardığını matematiksel olarak türetelim.

Merkezlenmiş veri matrisi Z (n × d) olsun, yani her sütundan ortalama çıkarılmış. Veri kovaryansı S = ZᵀZ / (n − 1) olur (Bölüm 49.5'te gördüğümüz kovaryans matrisinin örneklem hâli). Bir yön, birim uzunlukta bir u vektörüyle tanımlanır. Bu yöndeki izdüşümlerin varyansı uᵀSu'dur. Birinci ana yön, bu varyansı en büyük yapan birim u'dur:

maksimize uᵀSu,  kısıt uᵀu = 1

Lagrange çarpanı λ ile yazıp türevi sıfıra eşitlersek 2Su − 2λu = 0 çıkar. Yani Su = λu. Bu, Bölüm 48.12'deki özdeğer–özvektör problemidir. Kısıtlı optimizasyonun bu biçimi Bölüm 50.13'te gördüğümüz Lagrange yönteminin basit bir uygulamasıdır. Çözümlerden en büyük λ en büyük varyansı verir: uᵀSu = λuᵀu = λ. İkinci ana yön, birinciye dik kalarak en büyük varyansı veren yöndür; bu da S'nin ikinci özvektörüne karşılık gelir. Böylece ana bileşenler S'nin özvektörleridir ve sıralanmış özdeğerleri o yöndeki varyanslardır.

Bu yolun karşılığı SVD'dir. Z = U Σ Vᵀ ayrışımında ZᵀZ = V Σ² Vᵀ olduğu için S = V (Σ²/(n−1)) Vᵀ yazılır. Yani V'nin sütunları S'nin özvektörleri, σᵢ²/(n−1) değerleri ise özdeğerleridir. Bölüm 48.13'te SVD'yi "döndür, ölçekle, döndür" olarak görmüştük; PCA bu yapının istatistiksel adıdır. Pratikte PCA'yı SVD ile hesaplamak, kovaryans matrisini açıkça kurmaktan daha kararlıdır, çünkü ZᵀZ'nin koşul sayısı Z'ninkinin karesidir. Aşağıdaki kod iki yolu da sıfırdan yazar.

@@KOD b61_03_pca.py||def pca_svd_sifirdan@@

@@KOD b61_03_pca.py|def pca_svd_sifirdan|def bolum_a_esdegerlik@@

Açıklanan varyans oranı, k'inci bileşenin λ_k / Σλ_j değeridir. Kümülatif toplam, ilk k bileşenin toplam varyansın ne kadarını taşıdığını söyler. Bu oran bileşen sayısını seçmek için kullanılır: sık görülen eşikler %90 ya da %95'tir. Yeniden yapılandırma ise k bileşen ile veriyi geri çevirmektir: X̂ = Z V_k V_kᵀ + μ. Yeniden yapılandırma hatası, bu iki işlemin kayıp miktarını ölçer ve PCA'yı sıkıştırma olarak yorumlamamızı sağlar.

Aşağıdaki deney, 1797 örnekli ve 64 özellikli `digits` veri kümesi üzerinde iki yolun aynı sonucu verdiğini doğrular. Veri, 8 × 8 piksellik el yazısı rakamlarından oluşur. Ayrıca sklearn'ün `PCA` sınıfıyla karşılaştırma yapılır ve kümülatif varyans ile yeniden yapılandırma hatası hesaplanır.

@@KOD b61_03_pca.py|def bolum_a_esdegerlik|    for k in [2, 8, 16, 32]:@@

@@KOD b61_03_pca.py|    for k in [2, 8, 16, 32]:|def bolum_b_merkezleme@@

@@OUT out_03.txt|python b61_03_pca.py|A) digits|B) merkezlemenin@@

Kovaryans yolu ile SVD yolu arasındaki en büyük özdeğer farkı 4,26 · 10⁻¹³'tür; açıklanan oranlar arasındaki en büyük fark ise 8,33 · 10⁻¹⁷'dir. sklearn'ün ilk beş bileşeni ile bizimkiler arasındaki |cos| değerleri 1,000000'dır. Yani üç yöntem aynı yönleri bulur. Oranlara bakalım: ilk bileşen toplam varyansın %14,9'unu, ilk iki bileşen %28,5'ini taşır. %90'a ulaşmak için 21 bileşen, %95 için 29 bileşen gerekir. Yani 64 boyutun yaklaşık yarısı bile varyansın %95'ini korur. Yeniden yapılandırma hatası (MSE) k = 2'de 13,42, k = 8'de 6,12, k = 16'da 2,83 ve k = 32'de 0,63'tür. MSE'nin azalması, bileşen sayısı arttıkça kayıbın düştüğünü gösterir.

![Şekil 61.8: Digits verisi için kümülatif açıklanan varyans (solda; kesik çizgi %90, nokta çizgi %95) ve 64 boyuttan ilk iki ana bileşene izdüşüm (sağda; renk rakam etiketi, yalnızca gösterim için).](gorseller/b61_pca_digits.png)

Şekil 61.8 bu sonuçları görsel olarak verir. Sağ paneldeki 2B izdüşümde rakamlar birbirinden kısmen ayrışır, ama tam ayrı kümeler oluşmaz: iki boyut, 64 boyutun bilgisini tamamen taşımaz. Bu, PCA'nın bir sınıflandırıcı olmadığının da bir göstergesidir. Etiket bilgisi kullanılmadan dönüştürülmüş bir uzayda sınıflar ancak kısmen görünür.

### Merkezleme, ölçek ve beyazlatma

PCA'nın üç tuzağı vardır ve üçü de ML projelerinde sık görülür. Birincisi merkezlemedir. Kovaryans formülü merkezlenmiş veri varsayar. Eğer veri merkezlenmezse, SVD'nin ilk tekil vektörü verinin yayılımını değil ortalamasının yönünü yakalar. Bu, SVD'nin bir kovaryans hesabı olmadığını, bir matris çarpanlarına ayırma olduğunu hatırlatır. İkincisi ölçektir. PCA varyansa bakar; bir özelliğin birimi büyükse (ör. metre yerine milimetre) o özellik sadece birim nedeniyle baskın olur. Bölüm 56'da ölçeklemenin neden gerekli olduğunu gördük; PCA bu konuda hassastır. Üçüncüsü beyazlatmadır (whitening). Bileşenlerin varyanslarını 1'e eşitlemek, Y = Λ^(−1/2) Vᵀ(x − μ) dönüşümüyle yapılır. Bu, sonraki modellerde bileşenlerin eşit ağırlıkta görünmesini sağlar, ama gürültüyü de büyütür.

Aşağıdaki deney üç tuzağı ölçülebilir hâle getirir. Birinci kısımda `digits` verisine sabit bir ofset eklenir; veri aynı kalır ama ortalaması değişir. Merkezli PCA'nın ilk bileşeni ile merkezsiz SVD'nin ilk tekil vektörü karşılaştırılır. Sonra sentetik bir veride ortalama dağılımın yönünden uzaklaştırılır ve doğru yön ile karşılaştırılır. İkinci kısımda `wine` veri kümesi ham ve standartlaştırılmış hâlde PCA'dan geçirilir. Üçüncü kısımda beyazlatmanın varyansları gerçekten 1'e çektiği doğrulanır.

@@KOD b61_03_pca.py|def bolum_b_merkezleme|def bolum_c_beyazlatma@@

@@KOD b61_03_pca.py|def bolum_c_beyazlatma|def bolum_d_kernel_pca@@

@@OUT out_03.txt|python b61_03_pca.py|B) merkezlemenin|D) halka@@

Merkezleme etkisi açıktır: merkezli PC1 ile orijinal PC1 arasındaki |cos| 1,0000 çıkar, oysa merkezsiz SVD'nin ilk vektörü orijinal PC1 ile yalnızca 0,0081 uyuşur. Yani ofset, SVD'nin ilk vektörünü tamamen başka bir yöne çekmiştir. Sentetik veride ortalama (20, 0) noktasındadır ve veri eksenden 0,4 radyan döndürülmüştür; merkezli PC1 doğru yönü 1,0000 ile bulur, merkezsiz SVD 0,9236 ile yalnızca yaklaşık bulur. Ölçek etkisi wine verisinde çarpıcıdır: standartlaştırılmadan PC1 varyansın %99,81'ini açıklar ve en büyük yük proline (prolin) özelliğindedir. Yani PCA sadece en büyük birime sahip özelliği bulmuştur. Standartlaştırıldığında PC1 oranı %36,20'ye düşer ve bileşenler gerçek korelasyon yapısını yansıtmaya başlar. Bu nedenle PCA'dan önce standartlaştırma, çoğu durumda varsayılan bir adımdır (Bölüm 54'teki veri sızıntısı kuralı burada da geçerlidir: ölçekleyici yalnızca eğitim verisiyle eğitilmelidir).

Beyazlatma sonucu tam beklendiği gibidir: ilk beş bileşenin varyansları 1,0000 çıkar. Bu, dönüşümün kovaryansı birim matrise çevirdiğinin bir doğrulamasıdır.

Kernel PCA ve doğrusal olmayan yöntemler 61.10'da gelecek. Burada, PCA'nın doğrusal olduğu ve iki iç içe halkayı ayıramayacağı üzerinde duralım. Bunu çözecek olan, bölüm 60'ta göreceğimiz çekirdek (kernel) fikridir.

## 61.10 Doğrusal olmayan gömme: kernel PCA, t-SNE ve UMAP

PCA bir döndürme ve izdüşümdür; veri eğri bir yüzeyde yaşıyorsa bu yüzeyi düzleştiremez. İç içe iki halkayı PCA ile iki boyuta indirgediğimizde halkalar yine iç içe kalır. Bu sorunun cevabı, doğrusal olmayan bir dönüşümü örtük olarak kullanmaktır: kernel PCA. Bu fikir Bölüm 60'ta göreceğimiz çekirdek (kernel) hilesinin PCA'ya uygulanmasıdır. Veri noktalarını yüksek boyutlu bir uzaya taşımadan, noktalar arasındaki benzerlik matrisi K (ör. RBF çekirdeği K_ij = exp(−γ‖x_i − x_j‖²)) üzerinde PCA yaparız. Çekirdeğin özvektörleri, doğrusal olmayan ana bileşenleri verir.

Aşağıdaki deney, iki halkalı veride doğrusal PCA ve RBF kernel PCA'nın ardından bir lojistik regresyon eğitir. Bu deney sadece kernel PCA'yı gösterir; kernel PCA'nın kendisinin ayrıntılı türetmesi Bölüm 60'ta yapılacaktır.

@@KOD b61_03_pca.py|def bolum_d_kernel_pca|if __name__@@

@@KOD b61_03_pca.py|if __name__|@@

@@OUT out_03.txt|python b61_03_pca.py|D) halka|@@

Sonuç kernel parametresinin ne kadar önemli olduğunu gösterir. Doğrusal PCA'nın iki bileşeni üzerinde lojistik regresyon test verisinde %48,33 doğruluk verir; bu, şans düzeyidir. RBF çekirdeği γ = 1'de %49,17 ile yine şans düzeyinde kalır. γ = 4'te doğruluk %100'e çıkar. γ = 10'da ise %82,50'ye düşer. Yani aynı yöntem, bir parametreyle mükemmel, başka bir parametreyle zayıf olabilir. Bu, denetimsiz bir gömmede parametre seçiminin sonucu ne kadar değiştirdiğini gösterir; γ'yı seçmek için bir etiket kullanıldığında bu sonuç artık denetimsiz değildir. Bu noktayı unutma.

### t-SNE: olasılık benzerliği ve KL kaybı

t-SNE (t-distributed Stochastic Neighbor Embedding), görselleştirme için tasarlanmış bir gömme yöntemidir. Fikri şöyle özetlenebilir. Yüksek boyutlu uzayda her x_i için diğer noktaların bir "komşuluk olasılığı" tanımlanır. x_j'nin x_i'nin komşusu olma olasılığı Gauss çekirdeğiyle p_{j|i} ∝ exp(−‖x_i − x_j‖² / 2σ_i²) olarak hesaplanır ve simetrikleştirilir. Düşük boyutlu gömmede aynı şeyi y noktaları için yapan bir dağılım q_ij tanımlanır, ama burada Student-t (ağır kuyruklu) çekirdeği kullanılır: q_ij ∝ (1 + ‖y_i − y_j‖²)⁻¹. Amaç, q'yu p'ye benzetmektir. Bunun ölçüsü Bölüm 51.9'da gördüğümüz KL ıraksamasıdır:

KL(P ‖ Q) = Σ_{i≠j} p_ij ln(p_ij / q_ij)

KL bir kayıptır ve gradyan inişiyle y'ler üzerinde en aza indirilir (Bölüm 50). Bu kaybın asimetrisi önemlidir: p yüksek olan ama q düşük olan çiftler büyük ceza alır. Yani t-SNE, yakın noktaları yakın tutmaya yüksek öncelik verir; uzak noktaların göreli uzaklığını ise iyi korumaz.

σ_i değeri perplexity parametresiyle belirlenir. Perplexity, p_{·|i} dağılımının Shannon entropisinden hesaplanan etkin komşu sayısıdır: Perp = 2^{H(P_i)} (Bölüm 51.2'deki entropi tanımı). Perplexity 5 ise her noktanın yaklaşık 5 etkin komşusu vardır; 50 ise yaklaşık 50. Perplexity, yerel ve küresel yapı arasında bir dengedir ve sonuçları güçlü biçimde etkiler. Aşağıdaki kod digits alt kümesinde üç perplexity dener, KL kaybını ve "guvenilirlik" (trustworthiness) ölçüsünü hesaplar.

Guvenilirlik, bir gömmenin komşuluk ilişkilerini ne kadar koruduğunu ölçer. Gömmede k en yakın komşusu olan ama orijinal uzayda bu komşulukta olmayan noktalar cezalandırılır. Değer 1'e yakınsa gömme yerel komşulukları iyi korur demektir. Bu ölçüyü sklearn'ün `trustworthiness` fonksiyonu sağlar.

@@KOD b61_04_tsne_umap.py||def tsne@@

@@KOD b61_04_tsne_umap.py|def tsne|def main@@

@@KOD b61_04_tsne_umap.py|def main|B) yontem karsilastirmasi@@

@@KOD b61_04_tsne_umap.py|B) yontem karsilastirmasi|C) gurultuda sahte kume@@

@@KOD b61_04_tsne_umap.py|C) gurultuda sahte kume|@@

@@OUT out_04.txt|python b61_04_tsne_umap.py|A) digits|B) yontem@@

Üç perplexity'nin KL değerleri birbirine yakındır (0,5978, 0,5117, 0,5062). Ama guvenilirlik değerleri bir miktar ayrışır: perplexity 5'te 0,9819, 30'da 0,9883 ve 50'de 0,9870. Bu değerler, bu alt kümede perplexity 30 civarının yerel komşulukları en iyi koruduğunu söyler. Ancak KL'nin düşüklüğü her zaman daha iyi bir görselleştirme anlamına gelmez; KL'yi karşılaştırırken aynı perplexity'de karşılaştırma yapmalısın.

Yöntem karşılaştırmasında 500 noktalı alt kümede guvenilirlik ölçümü şöyledir: PCA-2 için 0,8342, t-SNE (perplexity 30) için 0,9883 ve UMAP için 0,9828. Yani bu veride iki doğrusal olmayan yöntem PCA'dan çok daha iyi yerel komşuluk korur.

@@OUT out_04.txt|python b61_04_tsne_umap.py|B) yontem|C) gurultuda@@

@@OUT out_04.txt|python b61_04_tsne_umap.py|C) gurultuda|@@

### Sahte kümeler: t-SNE gürültüde ne gösterir?

t-SNE'nin en büyük tuzağı şudur: çıkan şekil gerçek yapı olmayabilir. Yukarıda digits için görülen kümeler gerçektir, çünkü veride rakam sınıfları gerçekten ayrışıktır. Ama t-SNE, veride hiçbir yapı olmasa bile bir çıktı üretir. Aşağıdaki deney 500 × 50 boyutlu saf Gauss gürültüsü üretir. Ham uzayda k = 8 için k-means ve siluet hesaplanır, sonra gürültünün t-SNE gömmesinde aynı işlem yapılır. Ek olarak perplexity 5, 15, 30 ve 50 değerleri için KL ve siluet değerleri toplanır.

@@KOD b61_09_gurultu_perp.py||for p in@@

@@KOD b61_09_gurultu_perp.py|for p in|# Etiketli@@

@@KOD b61_09_gurultu_perp.py|# Etiketli|@@

@@OUT out_09.txt|python b61_09_gurultu_perp.py||@@

Sonuç bir tuzağı net gösterir. Ham gürültüde siluet 0,0181'dir; yani veride kümeleme yapısı yok. Aynı verinin t-SNE gömmesinde aynı k-means siluet değeri 0,3198'e çıkar. Perplexity değiştiğinde siluet 0,3198 ile 0,3504 arasında kalır; yani değer perplexity'den bağımsız olarak yüksektir. Bu, t-SNE'nin gürültüyü düzgün bir bulut gibi göstermesine rağmen, k-means'in bu bulutu bölmesinin ve siluetin bunu "küme" olarak ödüllendirmesinin sonucudur. Şekil 61.9'un sağ alt panelinde renklerle gösterilen k = 8 bölümlemesi tam da bu sahte kümelerdir.

Burada bir not: KL değerleri digits için 0,5 civarındayken gürültüde 1,7 ile 2,4 arasındadır. Gürültü, düşük boyutlu bir gömmeye sığdırılması zor bir veridir; bu yüzden kayıp yüksek kalır. Yüksek KL, her zaman kötü bir gömme anlamına gelmez, ama sıfır yapı varsayılan bir veride bile görsel olarak küme görmek kolaydır.

![Şekil 61.9: t-SNE gömmeleri. Üst iki panel ve sol alt: digits için perplexity 5, 30 ve 50 (KL değerleri başlıkta). Sağ alt: saf gürültüde k=8 k-means kümeleri; yapı olmamasına rağmen kümeler görünür.](gorseller/b61_tsne.png)

Şekil 61.9 üç tuzağı birlikte gösterir. Birincisi, digits gömmelerinde kümelerin boyutları ve aralarındaki mesafeler (ör. iki kümenin ne kadar uzak olduğu) bir yorum için güvenilir değildir; t-SNE yerel yapıyı korumaya öncelik verdiği için küresel mesafeleri bozar (genel bilgi, t-SNE'nin tasarım sonucu). İkincisi, perplexity değiştikçe gömmenin görünümü belirgin biçimde değişir. Üçüncüsü, saf gürültüde küme görmek kolaydır. Bu yüzden t-SNE çıktısı, bir keşif aracıdır; bulunan kümeler hipotez olarak alınmalı ve ham uzayda, bağımsız bir ölçütle ya da alan bilgisiyle doğrulanmalıdır. t-SNE öğrenilmiş bir fonksiyon değildir: yeni bir nokta eklemek için gömmeyi baştan hesaplamak gerekir. Bu yüzden öznitelik olarak sınıflandırıcıya verilmesi, bu bölümde gördüğümüz PCA'ya göre çok daha dikkatli olmayı gerektirir.

### UMAP

UMAP (Uniform Manifold Approximation and Projection), t-SNE'ye benzer bir amaçla daha hızlı ve çoğu zaman küresel yapıyı daha iyi koruyan bir yöntemdir. Kavramsal olarak yüksek boyutta bir komşuluk çizgesi kurar ve bu çizgenin düşük boyutlu bir benzerini bir çapraz entropi kaybıyla eşleştirir. Bu kaybın çapraz entropi yapısı Bölüm 51.10'daki sınıflandırma kaybıyla aynı ailedendir. UMAP'ın pratik parametreleri `n_neighbors` (yerel-küresel dengesi) ve `min_dist` (noktaların birbirine ne kadar sıkışabileceği) değerleridir.

Bu bölümün ortamında `umap-learn` 0.5.12 kurulu olduğu için UMAP de aynı alt küme üzerinde çalıştırıldı ve guvenilirlik 0,9828 olarak ölçüldü. t-SNE-30 ile arasındaki 0,0055'lik fark bu tek veri için anlamlı bir genel üstünlük değildir; yöntemler arasında karar vermek için birden çok veri ve tohum gerekir. Bölüm 57'de gördüğün istatistiksel anlamlılık kavramı burada da geçerlidir.

## 61.11 Anomali tespiti: istatistiksel yöntemler ve Mahalanobis

Anomali tespiti (outlier / novelty detection), normal davranışı öğrenip ondan sapan örnekleri bulma işidir. Etiketli veriniz varsa bu bir sınıflandırma problemidir; ama gerçek hayatta anomaliler çok nadirdir ve her türlü anomali önceden tanımlanmamış olabilir. Bu yüzden anomali tespiti çoğunlukla denetimsiz ya da yalnızca normal veriyle eğitilen bir yöntemle yapılır. Bu alt bölümde ilk olarak istatistiksel yaklaşımı görüyoruz.

Bölüm 56'da tek bir özelliğin aykırı değerini IQR ile ya da medyan ve MAD ile robust z-skoruyla bulmayı gördük. Bu yaklaşım tek değişkenli çalışır ve değişkenler arasındaki ilişkiyi görmez. Bir İHA'nın hızı ve akımı tek başına normal aralıkta olabilir; ama birlikte alışılmadık bir kombinasyon oluşturabilirler. Bu durumda tek değişkenli kontrol anomaliyi kaçırır. Çok değişkenli yaklaşım bu sorunu, veri kovaryansını hesaba katan uzaklıkla çözer.

Mahalanobis uzaklığı, bir x noktasının dağılımın merkezi μ ve kovaryansı Σ'ya göre uzaklığıdır:

d_M(x) = √((x − μ)ᵀ Σ⁻¹ (x − μ))

Bu uzaklık, veri uzayını kovaryansın gerdiği biçimde "beyazlatır". Özdeğer ayrışımı ile düşünürsek, her yöndeki uzaklık o yöndeki standart sapmaya bölünür. Gauss varsayımı altında d_M²'nin dağılımı ki-kare (χ²) dağılımıdır ve serbestlik derecesi boyut sayısı d'dir. Bu yüzden eşik, bir ki-kare kantilinden belirlenebilir; bunu 61.13'te kullanacağız.

Aşağıdaki deney, iki boyutlu, ρ = 0,9 korelasyonlu bir normal veri üretir. Test kümesine iki tür anomali eklenir: normal ile aynı tek değişkenli dağılımdan gelen ama korelasyonu ters (ρ = −0,9) olan noktalar. Bu anomalilerin her iki özelliği tek başına normal görünür; yani tek değişkenli kontrol bu anomalileri kaçırmalıdır. Karşılaştırma için aynı test kümesinde tek değişkenli max|z|, Öklid uzaklığı, Mahalanobis, PCA artığı, LOF ve tek Gauss GMM log-olabilirliği hesaplanır. Ölçüt olarak ROC eğrisinin altında kalan alan (AUC) kullanılır; 0,5 rastgele, 1 mükemmel ayrım demektir (Bölüm 57.4).

@@KOD b61_05_anomali.py||def c_n@@

@@KOD b61_05_anomali.py|def korelasyonlu_veri|def bolum_a_korelasyon_tuzagi@@

@@KOD b61_05_anomali.py|def bolum_a_korelasyon_tuzagi|    C = pca.components_@@

@@KOD b61_05_anomali.py|    C = pca.components_|def bolum_b_isolation_forest@@

@@OUT out_05.txt|python b61_05_anomali.py|A) 2B|B) Isolation@@

Tablo tutarlı bir hikâye anlatır. Tek değişkenli max|z| AUC'si 0,5067 ve Öklid uzaklığı 0,5018 ile şans düzeyindedir: anomaliler marjinallerde normal olduğu için bu yöntemler hiçbir şey göremez. Mahalanobis 0,8464 ile belirgin biçimde ayrışır. Burada ilginç bir sonuç var: PCA artığı 0,9120 ile Mahalanobis'ten daha iyidir. Bunun nedeni, anomalilerin korelasyon yönünün tam olarak PCA'nın atılan küçük ana ekseni olmasıdır; iki boyutta PCA artığı yalnızca bu ekseni ölçer ve daha temiz bir sinyal verir. Mahalanobis ise iki yönü de toplar; normal noktaların büyük ekseni boyunca uzak kuyruklarını da cezalandırır. Yani "en iyi yöntem" veriye bağlıdır ve bir yöntemi seçmeden önce veri üzerinde yapısal bir hipotez kurmak gerekir.

Mahalanobis ile tek Gauss GMM'nin log-olabilirliği aynı sırayı verir (AUC 0,8464 her ikisinde de). Bunun nedeni, tek bir Gauss bileşeninin log-olabilirliğinin, d_M² ile doğrudan monoton ilişkili olmasıdır. LOF (yerel aykırılık faktörü) 0,8700 alır; LOF komşuluk yoğunluğunu yerel olarak karşılaştırır ve bir sonraki alt bölümde ele alınır.

Mahalanobis skorunun normal ve anomali ortalamaları 1,228 ile 3,353 arasında ayrışır. Bu, dağılımın ayrımının görsel olarak da net olduğunu gösterir.

## 61.12 Yoğunluk tabanlı anomali ve Isolation Forest

Mahalanobis, verinin tek bir Gauss ile tanımlanabildiğini varsayar. Gerçek veri genellikle birden fazla modludur: bir uçuş modu seyir, bir başkası tırmanış olabilir. Böyle bir veride tek Gauss, merkezi yanlış yerleştirir ve kovaryansı şişirir. Yoğunluk tabanlı yöntemler bu varsayımı bırakır: normal veriyi bir yoğunluk modeli ile tanımlar ve yeni bir noktanın bu yoğunluğa göre ne kadar olası olduğunu ölçer.

İki yaygın yaklaşım vardır. **Yerel aykırılık faktörü (LOF)** bir noktanın komşularının yoğunluğuna göre yerel yoğunluğunu karşılaştırır. Eğer bir noktanın yoğunluğu komşularınınkinden belirgin biçimde düşükse, o nokta aykırıdır. Bu yaklaşım bölgesel farklı yoğunlukları yakalar; DBSCAN'in tersi bir düşünce tarzıdır. **Gauss karışım modeli (GMM)** ise normal veriye bir karışım uydurur ve bir noktanın log-olabilirliği düşükse anomali sayar. Bu yöntemin bileşen sayısı, 61.7'de gördüğümüz BIC ile seçilebilir.

Isolation Forest (Liu, Ting ve Zhou, 2008) farklı bir fikre dayanır: anomaliler azdır ve normal noktalardan farklıdır, bu yüzden rastgele bölmelerle onları yalıtmak daha kolaydır. Veri rastgele bir özellik seçilip rastgele bir eşikle bölünerek bir ağaç kurulur. Bir noktanın yolu, yani yapraktaki derinliği ortalama alınır. Anomali kısa yolla yalıtılır, normal nokta uzun yol ister. Ortalama yol uzunluğu E[h(x)] ise skor

s(x, n) = 2^(−E[h(x)] / c(n))

ile tanımlanır. Burada c(n) = 2H(n−1) − 2(n−1)/n, H harmonik sayının yaklaşık değeri ln(n−1) + 0,5772'dir. Yani c(n), n noktalı rastgele bir ikili ağacın ortalama yol uzunluğudur. s 1'e yakınsa anomali, 0,5'in altındaysa normal sayılır.

Aşağıdaki kod Isolation Forest'ı sıfırdan yazar. `agac_kur` özyinelemeli bir bölme ağacı kurar; `yol_uzunlugu` bir noktanın yapraga kadar yolunu ve yaprağın c(n) düzeltmesini hesaplar. `IsolationForestSifirdan` sınıfı alt örnekleme (psi = 256) ile birden çok ağaç kurar ve skoru tanımlandığı gibi üretir.

Önce yol uzunluğunun düzeltmesini yapan `c_n` ve bölme ağacını kuran `agac_kur` gelir.

@@KOD b61_05_anomali.py|def c_n|def agac_kur@@

Ağacın her düğümü ya yaprak ya da bir dal olarak tanımlanır. Yol uzunluğu, bir noktanın yapraga kadar kaç bölme geçtiğini sayar ve yaprağın c(n) düzeltmesini ekler.

@@KOD b61_05_anomali.py|def agac_kur|class IsolationForestSifirdan@@

Sınıf, alt örnekleme ile birden çok ağaç kurar ve skoru tanımlandığı gibi üretir.

@@KOD b61_05_anomali.py|class IsolationForestSifirdan|def korelasyonlu_veri@@

Deney, aynı korelasyonlu veride sklearn ile sıfırdan Isolation Forest'ı karşılaştırır. İki uygulama tohum farkı nedeniyle birebir aynı ağaçları kurmaz; bu yüzden küçük bir fark beklenir. Asıl sorulan, iki uygulamanın aynı ayrımı yapıp yapmadığıdır.

@@KOD b61_05_anomali.py|def bolum_b_isolation_forest|def bolum_c_esik_butcesi@@

@@OUT out_05.txt|python b61_05_anomali.py|B) Isolation|C) esik@@

Sonuçlar, sıfırdan uygulamanın sklearn'e yakın olduğunu gösterir: AUC 0,7627 (sklearn) ve 0,7657 (sıfırdan); ortalama hassasiyet (AP) 0,1700 ve 0,1811. Ortalama skor normal noktalarda 0,4619, anomalilerde 0,5304'tür. Yani IF bu veride Mahalanobis'ten (0,8464) belirgin biçimde zayıftır. Bu şaşırtıcı görünebilir, ama nedeni basittir: Isolation Forest eksen-paralel bölmeler kullanır ve iki boyutlu, döndürülmüş bir korelasyon yapısını bu bölmelerle yakalamakta zorlanır. Yöntem seçerken verinin geometrisini hesaba katmak gerekir; "en güçlü" algoritma diye bir şey yoktur.

## 61.13 Eşik seçimi ve değerlendirme

Bir anomali skoru ürettiniz; şimdi bir karar gerekir: hangi skor "alarm" sayılacak? Bu, skordan çok daha önemli bir karardır, çünkü eşik yanlış alarm ve kaçan anomali arasındaki dengeyi belirler. Denetimsiz bir bağlamda eşik genellikle normal eğitim verisinin belli bir yüzdeliğinden seçilir. Örneğin normal verinin %99'u eşiğin altında kalacak şekilde bir eşik seçilirse, teorik yanlış alarm oranı %1 olur. Ama bu yalnızca eğitim verisi test verisiyle aynı dağılımdan geliyorsa geçerlidir. Gerçek hayatta bu varsayım sık sık bozulur.

Değerlendirmede iki temel ölçüt kullanılır. ROC eğrisi, tüm eşikler için doğru alarm oranını (TPR) yanlış alarm oranına (FPR) karşı çizer. Ama anomaliler çok nadir olduğunda, PR (kesinlik–duyarlılık) eğrisi daha bilgilendiricidir; Bölüm 57.5'te gördüğümüz gibi ROC, dengesiz sınıflarda iyimser görünebilir. Ortalama hassasiyet (AP) PR eğrisinin altındaki alanın özetidir. Bu bölümde AUC ve AP'yi birlikte raporladık.

Aşağıdaki kod eşik kararını somut hâle getirir. Mahalanobis eşiği, eğitim normalinin %99'undan (d_M² ≈ 9,41) seçilir; ki-kare 2 serbestlik derecesi için %99 kantili 9,2103'tür ve bu iki değer yakındır. Test kümesinde normal noktaların %1,10'u alarm verir ve anomalilerin %45,00'i (60 anomaliden 27'si) yakalanır; 33 anomali kaçar.

@@KOD b61_05_anomali.py|def bolum_c_esik_butcesi|if __name__@@

@@KOD b61_05_anomali.py|if __name__|@@

@@OUT out_05.txt|python b61_05_anomali.py|C) esik|@@

Bu sonuç, bir yöntemin AUC'sinin yüksek olmasının tek başına yeterli olmadığını gösterir. AUC 0,8464 iyi görünür, ama %1 yanlış alarm budgetinde anomalilerin yarısından azı yakalanır. Bir İHA'da her yanlış alarm bakım ekibini gereksiz yere harekete geçirir; her kaçan anomali ise gerçek bir arıza demektir. Bu iki maliyeti birlikte değerlendirmek, eşik seçiminin asıl işidir. Bölüm 57.6'da gördüğün maliyet temelli eşik burada da geçerlidir.

Az etiketle eşik seçmek ayrı bir sorundur. Birkaç anomali etiketi varsa, eşiği bu etiketlere göre ayarlamak mümkündür; ama bu durumda etiket sayısı çok küçük olduğu için eşikte büyük belirsizlik olur. Bu nedenle eşik seçiminde bir yanlış alarm bütçesi (ör. saatte en fazla bir alarm) belirlemek ve buna göre normal veriden kalibre etmek daha güvenilirdir. Bu fikri IHA telemetrisi uygulamasında sayısal olarak göreceğiz.

![Şekil 61.10: Sol: korelasyonlu normal veride Mahalanobis (düz eş-uzaklık) ve Öklid (kesik) çemberleri; kırmızı noktalar ters korelasyonlu anomaliler. Sağ: Isolation Forest skor haritası (koyu sarı: yüksek anomali skoru).](gorseller/b61_anomali.png)

Şekil 61.10 iki yöntemi yan yana gösterir. Soldaki panelde Mahalanobis eş-uzaklıkları veri bulutunun uzanma yönünü izler, oysa Öklid çemberleri her yöne eşit davranır. Anomaliler, bulutun tersine uzanan kuyruğunda yer alır; Öklid çemberleri bu noktaları hiçbir yönde ayırt edemez. Sağdaki panelde IF skor haritası veri bulutunun merkezinden uzaklaştıkça değişir, ama sınır, Mahalanobis'in elipsine kıyasla düzensizdir. Bu görsel kanıt, iki yöntemin neden farklı sonuç verdiğini gösterir.

## 61.14 Uygulamalar: sentetik İHA telemetrisi, batarya hücresi ve renk paleti

Bu alt bölümde öğrendiklerimizi üç uygulamada birleştiriyoruz. Üç veri de **sentetiktir**: gerçek bir uçuş kaydı ya da hücre ölçümü kullanılmamıştır. Sentetik veri, bir yöntemin hangi koşulda çalışıp hangi koşulda çalışmadığını bilerek test etmek için iyi bir araçtır; ama sonuçların gerçek veriye taşınabileceği anlamına gelmez. Her uygulamada bu sınırı açıkça göreceğiz.

Birinci uygulama bir İHA'nın uçuş telemetrisidir. Her iki saniyelik pencere altı özellik taşır: hız, dikey hız, yatış, yunuslama, motor akımı ve titreşim. Dört uçuş modu (seyir, tırmanış, dönüş, alçalış) ayrı Gauss dağılımlarından üretilir. Anomaliler üç türdedir: motor arızası (akım artar, hız düşer), kanat hasarı (yatış dalgalanır) ve sensör donması (titreşim değeri sabit kalır). Aşağıdaki kod veriyi üretir; normal pencerelerin etiketi uçuş modu, anomalilerin etiketi tür adıdır.

@@KOD b61_06_uygulama.py||def iha_verisi@@

@@KOD b61_06_uygulama.py|def iha_verisi|    # motor: akim@@

Anomaliler, normal modların etrafına yerleştirilir. Motor anomalisi akımı 4 birim, titreşimi 0,07 birim kaydırır; hızı da 1,5 düşürür. Kanat anomalisi yatışı ±4 birim oynatır. Bu değerler normal dağılımın standart sapmasına göre yaklaşık 2–3,5 σ'dır; yani her biri tek tek bakıldığında zor fark edilir. Donma anomalisinde titreşim normal ortalamaya sabitlenir; böylece değer tek bir pencerede normaldir ve bu, nokta tabanlı yöntemlerin neden başarısız olacağını gösterecek.

@@KOD b61_06_uygulama.py|    # motor: akim|def bolum_a_ucus_modlari@@

Deneyin ilk kısmı, normal verinin dört modunu k-means ve GMM ile kümeler. Kümeleme, özellikler standartlaştırıldıktan sonra yapılır (Bölüm 56'da gördüğümüz ölçekleme). Gerçek mod etiketleri yalnızca ARI ile karşılaştırma için kullanılır; siluet etiket kullanmadan hesaplanır.

@@KOD b61_06_uygulama.py|def bolum_a_ucus_modlari|def egitim_mcd_skor@@

@@OUT out_06.txt|python b61_06_uygulama.py|A) sentetik|B) anomali@@

Dört mod bu sentetik veride çok iyi ayrılmıştır: iki yöntem de ARI = 1,0000 ve siluet 0,7231 verir. Bunu gerçek bir uçuş verisinde beklemeyin; modlar genellikle üst üste biner ve ARI bu kadar yüksek olmaz. Sentetik deney yöntemin çalıştığını gösterir, veri üzerindeki başarının genellenebileceğini göstermez.

Deneyin ikinci kısmı anomali tespitidir. Eğitim yalnızca normal uçuşlarla yapılır; test kümesine 1000 normal pencere ile 60 anomali eklenir. Eşik, eğitim normalinin %99'undan seçilir. Dört yöntem karşılaştırılır: tek Gauss ile Mahalanobis (MCD), GMM (k=4), Isolation Forest ve PCA artığı.

@@KOD b61_06_uygulama.py|def egitim_mcd_skor|esik: egitimin@@

@@KOD b61_06_uygulama.py|esik: egitimin|def bolum_c_yanlis@@

@@OUT out_06.txt|python b61_06_uygulama.py|B) anomali|C) yanlis@@

Sonuçlar tek bir yöntemin her şeyi yakalayamadığını gösterir. Tek Gauss Mahalanobis'in AUC'si 0,5660'tır. Neden? Normal veri dört ayrı moddan oluşur; tek bir Gauss, bu modların ortalamasına ve geniş bir kovaryansa uyar, bu yüzden her yöne yayılır ve anomaliyi ayırt edemez. Burası Mahalanobis'in varsayımının bozulduğu yerdir. Isolation Forest da 0,5098 ile şans düzeyinde kalır: anomaliler dört modun içinde kalacak kadar küçük sapmalardır, bu yüzden eksen-paralel bölmeler onları kısa yolla yalıtamaz. Tek başına PCA artığı 0,7629 alır. GMM ise 0,8095 ile en iyisidir; çünkü normal yapısını dört bileşenle modeller.

Tür bazında tespit oranları daha öğreticidir. GMM motor anomalisinin %100'ünü, kanat anomalisinin %80'ini yakalar. Ama donma anomalisinin hiçbirini yakalayamaz (%0). Bunun nedeni, donmuş bir değerin tek başına bakıldığında normal olmasıdır: değer ortalamaya eşit. Donmanın tespiti için pencereler arasındaki değişkenliğe bakmak gerekir; yani her pencereye, o pencerenin içindeki ya da bir önceki pencerelerle olan değişkenliğini anlatan bir öznitelik eklemek gerekir. Bu, Bölüm 52'deki pencere öznitelikleri fikridir. Nokta tabanlı bir dedektörün kör noktasını bilmek, uygulamada en değerli sonuçlardan biridir.

Yanlış alarm bütçesi, bu uygulamanın asıl sorusudur. GMM skorunun eşiği eğitim normalinin %99'undan seçildiğinde (hedef 0,010), test normalinde alarm oranı %1,30 çıkar ve anomalilerin %60'ı yakalanır. Her pencere 2 saniye sürdüğüne göre bir saatte 1800 pencere vardır ve bu yanlış alarm oranında saatte 23,40 yanlış alarm demektir. Hedef 0,001'de yanlış alarm saatte 9,00'a düşer, ama tespit %56,7'ye iner. Bir bakım ekibi için saatte dokuz yanlış alarm bile kabul edilebilir değildir. Burada gösterilen şey, eşiğin eğitim yüzdeliğinden seçilmesinin test dağılımına taşınmadığıdır (hedeflenen %1 yerine %1,30); gerçek bir sistemde bütçe, sahada toplanan normal uçuşlarla sürekli kalibre edilmelidir.

Bu sonuçlar, 61.11–61.13'teki karşılaştırmalara benzer bir mesaj verir: yöntem seçimi veri yapısına bağlıdır. Burada yapısal farkı belirleyen şey, normal verinin çok modlu olmasıdır.

### Batarya hücresi aykırı değerleri

İkinci uygulama bir elektrikli araç batarya modülüdür. 96 hücrenin her birinde üç ölçüm vardır: gerilim V, iç direnç R ve sıcaklık T. Bu sentetik modülde iki hücre bilerek bozulmuştur: 17 numaralı hücrenin iç direnci yüksektir (gerilimi normaldir) ve 62 numaralı hücrenin gerilimi düşük, sıcaklığı yüksektir. Amaç, etiket kullanmadan bu iki hücreyi bulmaktır.

@@KOD b61_06_uygulama.py|def bolum_d_batarya|def bolum_e_renk@@

@@OUT out_06.txt|python b61_06_uygulama.py|D) sentetik|E) renk@@

Tek tek robust z-skorları (medyan ve MAD, Bölüm 56) en yüksek üç hücreyi 17 (19,47), 62 (13,48) ve 55 (3,35) olarak verir. Çok değişkenli MCD Mahalanobis uzaklığı ise 17 (577,3), 62 (248,4) ve 2 (19,6) çıkarır. İki yöntem de gerçek iki hücreyi ilk sıraya yerleştirir. Üçüncü sıradaki aday, robust z'de 3,35 ve Mahalanobis'te 19,6 gibi düşük değerlerdir; bunlar bozuk hücre değil, normal değişkenliğin uçlarıdır. Bu sonuç, değerlendirmede ilk sıradaki birkaç adayı incelemenin, üçüncü sıradakini otomatik olarak arıza saymaktan daha değerli olduğunu gösterir.

Bu modül küçüktür ve iki hücre belirgin biçimde bozuktur; gerçek bir modülde sapma bu kadar açık olmayabilir. Çok değişkenli yöntemin avantajı, değişkenler birlikte değiştiğinde (ör. hücre 62'de düşük gerilim ve yüksek sıcaklık) ortaya çıkar. Tek değişkenli yöntem bu ikilinin her birini tek başına normal görebilir.

### Renk paleti: vektör nicemleme

Üçüncü uygulama, bir görüntünün renklerini 16 renkli bir palete indirgemektir. Bu, vektör nicemlemenin (vector quantization) en eski uygulamalarından biridir: her piksel RGB üç boyutlu bir vektördür ve k-means merkezleri bir kod kitabı (codebook) oluşturur. Her piksel, en yakın kod vektörünün indeksi ile temsil edilir. Böylece piksel başına 24 bit yerine 4 bit (16 renk için) kullanılır; palet ise 16 × 24 bit'tir. Bölüm 51'de gördüğümüz bilgi-bit ilişkisi burada doğrudan uygulanır: indeks başına bit sayısı log₂(16) = 4'tür.

Aşağıdaki kod sklearn'ün örnek fotoğrafını (china.jpg, 640 × 427 piksel) yükler, piksellerin rastgele 5000'lik bir alt kümesi üzerinde k-means çalıştırır ve paleti tüm piksellere uygular. Kalite PSNR ile ölçülür: PSNR = 10 log₁₀(1 / MSE), piksel değerleri [0, 1] aralığındadır.

@@KOD b61_06_uygulama.py|def bolum_e_renk|if __name__@@

@@KOD b61_06_uygulama.py|if __name__|@@

@@OUT out_06.txt|python b61_06_uygulama.py|E) renk|@@

Sonuç: PSNR 27,48 dB ve sıkıştırma oranı 6,00'dır. Palet yükü (16 × 24 bit) toplam bitlere ihmal edilebilir katkı yapar; bu yüzden oran pratikte 24/4 = 6'ya yakındır. PSNR bir kalite sayısıdır ama algısal kaliteyi tam ölçmez; 27 dB, renk geçişlerinde belirgin kayıp anlamına gelebilir. Üstelik bu oran sadece palet indeksini sayar; entropi kodlama (Bölüm 51.6) bu oranı daha da artırabilir. Gömülü sistemlerde bu tür bir nicemleme, bant genişliği ve bellek kazancı için kullanılır (Bölüm 46).

## Çözümlü Örnekler

Dört örnek bu bölümün kavramlarını elle izlemeni hedefler. Her birinde önce kâğıt üzerinde iz sürersin, sonra programla doğrularsın. Programların çıktıları, bu bölümün ilk kod dosyasındaki (`b61_00_izler.py`) sayılarla birebir aynıdır. Örnekler ★ ile ★★★ arasında artan bir zorluk sırasındadır.

### Örnek 1 (★): 1B k-means, iki iterasyonun elle izi

**Adım 1 — Anla.** Altı nokta X = [1, 2, 4, 8, 9, 11] ve k = 2 veriliyor. Başlangıç merkezleri 1 ve 4. Atamaları, merkezleri ve SSE amacını (J) iterasyon iterasyon izle. Hangi noktalar ilk atamada hangi kümeye girer? Kaç iterasyonda durulur?

**Adım 2 — Örnekle.** Her noktanın iki merkeze uzaklığını yaz. 1 → merkez 1 (uzaklık 0), 2 → merkez 1 (uzaklık 1, merkez 4'e uzaklık 2), 4 → merkez 4 (uzaklık 0), 8, 9 ve 11 → merkez 4 (uzaklıklar 4, 5, 7).

**Adım 3 — Kaba çöz.** Her iterasyonda: (a) her noktayı en yakın merkeze ata; (b) J'yi bu atama ve mevcut merkezle hesapla; (c) her kümenin ortalamasını al ve merkezleri güncelle; (d) yeni merkezle J'yi tekrar hesapla. Atama değişmiyorsa dur.

**Adım 4 — Örüntü.** Her adımda J ya düşer ya da aynı kalır. Birinci iterasyondan sonra ikinci merkez 8'e kayar. İkinci iterasyonda yalnızca 4 noktası ilk kümeye geçer ve merkezler 2,333 ile 9,333'e taşınır. Üçüncü iterasyonda atama değişmez: yakınsama.

**Adım 5 — İyileştir.** Elle izlediğin adımları programa dök. Program her iterasyonu yazdırır, yakınsamayı kontrol eder ve J'yi kaydeder.

@@KOD b61_00_izler.py||def pdf@@

**Adım 6 — Doğrula.** Programın çıktısı elle izlediğin tabloyu doğrular.

| İterasyon | Merkez (öncesi) | Atama | J (öncesi merkezle) | Güncelleme sonrası merkez | J (yeni merkezle) |
|---|---|---|---|---|---|
| 1 | (1, 4) | {1, 2} → 1; {4, 8, 9, 11} → 2 | 91,00 | (1,5; 8,0) | 26,50 |
| 2 | (1,5; 8,0) | {1, 2, 4} → 1; {8, 9, 11} → 2 | 16,75 | (2,333; 9,333) | 9,33 |
| 3 | (2,333; 9,333) | değişmez | 9,33 | değişmez | 9,33 |

@@OUT out_00.txt|python b61_00_izler.py|== 1B k-means|== 1B iki@@

J dizisi 91 → 26,5 → 16,75 → 9,33 → 9,33 biçiminde azalır ve durur; tablo ile programın sonucu birebir uyuşur.

**Bunu AI'sız yazabilir misin?** Yedi noktalı X = [1, 2, 3, 6, 8, 9, 12] veri kümesinde başlangıç merkezleri 2 ve 9 ise, iki iterasyonu elle izle ve J değerlerini hesapla.

### Örnek 2 (★★): 2×2 kovaryans ve PCA

**Adım 1 — Anla.** Beş noktalı iki boyutlu veri (1,2), (2,3), (3,5), (4,4), (5,6). Birinci ana bileşeni, açıklanan varyans oranlarını ve ana eksenin yönünü bul. Merkezleme yapılmadan SVD'nin ana yönü ne olur?

**Adım 2 — Örnekle.** Ortalama (3, 4). Merkezlenmiş noktalar: (−2, −2), (−1, −1), (0, 1), (1, 0), (2, 2).

**Adım 3 — Kaba çöz.** Kovaryans S = ZᵀZ / (n − 1). Z'nin sütunlarının kareleri ve çarpımlarını elle hesapla: Sxx = (4 + 1 + 0 + 1 + 4) / 4 = 2,5; Syy = 2,5; Sxy = (4 + 1 + 0 + 0 + 4) / 4 = 2,25.

**Adım 4 — Örüntü.** S = [[2,5; 2,25], [2,25; 2,5]] simetrik ve 2×2'dir. Özdeğerler λ = 2,5 ± 2,25 ⇒ 4,75 ve 0,25. Birinci özvektör (1, 1)/√2 yönündedir. Açıklanan oran: 4,75 / 5 = %95 ve 0,25 / 5 = %5.

**Adım 5 — İyileştir.** Bu hesabı programa dök; ayrıca merkezlenmemiş SVD'nin yanlış yönü nasıl verdiğini gör.

@@KOD b61_00_izler.py|def ornek_pca|def ornek_mahalanobis@@

**Adım 6 — Doğrula.**

| Büyüklük | Elle | Program |
|---|---|---|
| Ortalama | (3, 4) | [3, 4] |
| S | [[2,5; 2,25], [2,25; 2,5]] | aynı |
| Özdeğerler | 4,75; 0,25 | 4,75; 0,25 |
| Ana yön | (0,7071; 0,7071) | (0,7071; 0,7071) |
| Merkezsiz SVD yönü | — | (−0,6141; −0,7893) |

@@OUT out_00.txt|python b61_00_izler.py|== 2x2|== Mahalanobis@@

Merkezlenmemiş SVD'nin ilk yönü (−0,6141; −0,7893), verinin ortalamasının (3, 4) yönüne yakındır: (0,6; 0,8) ile karşılaştır. Yani merkezleme yapılmazsa SVD yayılımı değil konumu bulur.

**Bunu AI'sız yazabilir misin?** Dört noktalı (0, 0), (2, 1), (1, 3), (3, 4) verisinin kovaryansını, özdeğerlerini ve birinci ana yönünü elle hesapla; sonra programla doğrula.

### Örnek 3 (★★): 1B iki bileşenli GMM ve bir EM iterasyonu

**Adım 1 — Anla.** Altı nokta X = [1, 2, 4, 8, 9, 11]. Başlangıçta μ = (2, 9), σ² = (4, 4) ve π = (0,5; 0,5). Bir E ve bir M adımı uygula. Sorumlulukları, yeni π, μ, σ² değerlerini ve log-olabilirliğin artışını hesapla.

**Adım 2 — Örnekle.** x = 4 için iki bileşenin olasılığı: N(4 | 2, 4) ≈ 0,1210 ve N(4 | 9, 4) ≈ 0,0088 (varyans 4, yani σ = 2; bu değerleri programla kontrol et). Ağırlıklı değerler π · N'dir: 0,5 · 0,1210 = 0,0605 ve 0,5 · 0,0088 = 0,0044.

**Adım 3 — Kaba çöz.** E adımında her noktanın sorumluluğu r_1 = π_1 N_1 / (π_1 N_1 + π_2 N_2). M adımında N_k = Σ r_ik, π_k = N_k / n, μ_k = Σ r_ik x_i / N_k ve σ_k² = Σ r_ik (x_i − μ_k)² / N_k.

**Adım 4 — Örüntü.** Sorumluluklar 1, 2, 4 noktalarını birinci bileşene, 8, 9, 11'i ikinci bileşene verir. M adımı bu gruplara göre μ'yü iki gruba taşır; σ² ise grup yayılımını tutar.

**Adım 5 — İyileştir.** Her ara değeri yazdıran programı çalıştır.

@@KOD b61_00_izler.py|def pdf|def ornek_pca@@

**Adım 6 — Doğrula.**

| x | π₁N₁ | π₂N₂ | r₁ | r₂ |
|---|---|---|---|---|
| 1 | 0,088016 | 0,000033 | 0,9996 | 0,0004 |
| 2 | 0,099736 | 0,000218 | 0,9978 | 0,0022 |
| 4 | 0,060493 | 0,004382 | 0,9325 | 0,0675 |
| 8 | 0,001108 | 0,088016 | 0,0124 | 0,9876 |
| 9 | 0,000218 | 0,099736 | 0,0022 | 0,9978 |
| 11 | 0,000004 | 0,060493 | 0,0001 | 0,9999 |

Nk = (2,9446; 3,0554), π = (0,4908; 0,5092), μ = (2,3246; 9,2148), σ² = (1,6909; 2,1818). Log-olabilirlik −14,9941'den −14,0865'e çıkar: artış pozitiftir, EM'in temel özelliği.

@@OUT out_00.txt|python b61_00_izler.py|== 1B iki|== 2x2@@

**Bunu AI'sız yazabilir misin?** Aynı veriyi başlangıç μ = (1, 10) ve σ² = (1, 1) ile yeniden ele al; bir E adımı ve bir M adımı yap. Sorumluluklar daha mı keskin olur, yoksa daha yumuşak mı?

### Örnek 4 (★★★): Mahalanobis ile iki aday ve Öklid'in yanılgısı

**Adım 1 — Anla.** İki boyutlu bir veri kümesi Σ = [[1; 0,9], [0,9; 1]] kovaryansına sahip (merkez 0). İki aday nokta var: A = (2; 2) ve B = (2; −1,5). Hangisi anomali olma olasılığı daha yüksektir? Öklid uzaklığı ne söyler, Mahalanobis ne söyler?

**Adım 2 — Örnekle.** Öklid uzaklıkları: |A| = √8 ≈ 2,8284 ve |B| = √(4 + 2,25) = 2,5. Öklid'e göre A daha uzaktır.

**Adım 3 — Kaba çöz.** Σ⁻¹ = (1 / (1 − 0,81)) [[1; −0,9], [−0,9; 1]] = (1 / 0,19) [[1; −0,9], [−0,9; 1]]. Mahalanobis karesi d² = xᵀ Σ⁻¹ x.

**Adım 4 — Örüntü.** A = (2, 2) için pay: 4 + 4 − 2 · 0,9 · 4 = 0,8; d² = 0,8 / 0,19 ≈ 4,2105. B = (2, −1,5) için pay: 4 + 2,25 − 2 · 0,9 · (2 · (−1,5)) = 11,65; d² = 11,65 / 0,19 ≈ 61,316. Yani B çok daha uç.

**Adım 5 — İyileştir.** Bu kararı programla doğrula ve sonucu açıklayan bir tablo çıkar.

@@KOD b61_00_izler.py|def ornek_mahalanobis|@@

**Adım 6 — Doğrula.**

| Nokta | Öklid | Mahalanobis d² | Mahalanobis d |
|---|---|---|---|
| A = (2, 2) | 2,8284 | 4,2105 | 2,0520 |
| B = (2, −1,5) | 2,5000 | 61,316 | 7,8304 |

@@OUT out_00.txt|python b61_00_izler.py|== Mahalanobis|@@

Öklid bu veride yanılır: A'yı daha uç sayar. Ama A, korelasyonun yönünde, yani veri bulutunun uzandığı yöndedir; B ise korelasyona ters düşer. Mahalanobis bunu bilir ve B'yi 7,83 ile çok daha uç bulur. Bu, 61.11'deki korelasyon tuzağının tek nokta üzerinde bir örneğidir.

**Bunu AI'sız yazabilir misin?** Σ = [[1; −0,6], [−0,6; 1]] için A = (2, 2) ve B = (2, −2) noktalarını Öklid ve Mahalanobis ile karşılaştır. Hangisi hangi yönde yanılır?

## Kendin Yap Projeleri

::: dikkat
Bu projelerde önce kendi tasarımını yap; yapay zekâ araçlarına, kendin bir taslak çıkarana kadar başvurma. Aşağıdaki "önerilen yaklaşım" bölümleri yalnızca bir ipucudur, tam çözüm değildir. Başarı kriterlerini tamamlamadan projeyi bitmiş sayma.
:::

### Proje 1 (★★): Sıfırdan denetimsiz öğrenme kütüphanesi

**Amaç.** k-means++ (yerel denemeli), DBSCAN, tam kovaryanslı GMM-EM ve PCA'yı numpy ile yazıp her birini sklearn ile karşılaştıran küçük bir kütüphane ve bir karşılaştırma raporu üretmek.

**Beklenen davranış.** Bir betik, üç test verisi (toplar, ay, iç içe halka) üzerinde dört yöntemi çalıştırmalı; k-means'in J dizisinin her iterasyonda azalmadığı durumda hata vermeli; EM'in log-olabilirliğinin azaldığı durumda hata vermeli; sklearn ile ARI ve SSE farklarını tablo hâlinde yazmalı.

**Önerilen yaklaşım.** Önce her yöntemi tek bir test verisinde elle izleyebileceğin kadar küçük bir veriyle doğrula. Sonra sklearn'ün `random_state` ve başlangıç yöntemini eşitle; aynı başlangıçtan aynı sonucu almadan karşılaştırma yapma. DBSCAN'de komşu sayımında noktanın kendisini dahil etmeyi unutma. Log-olabilirlik için reg_covar gibi bir alt sınır kullan.

**Başarı kriterleri.** (1) Dört yöntem de üç veri kümesinde çalışır. (2) k-means ve EM için monotonluk kontrolü geçer. (3) Sıfırdan ve sklearn sonuçları, aynı başlangıçla, en fazla 10⁻⁶ farkla eşleşir. (4) Raporda her yöntem için en az bir başarısızlık örneği (ör. k-means'in halkada başarısızlığı) yer alır.

### Proje 2 (★★★): Sentetik İHA telemetri anomali dedektörü

**Amaç.** Sentetik İHA telemetrisinde (uçuş modu + üç anomali türü) öznitelik çıkarımı, PCA + Mahalanobis + Isolation Forest karşılaştırması, az etiketle eşik seçimi ve yanlış alarm bütçesi içeren bir dedektör kurmak.

**Beklenen davranış.** Bir betik ham telemetri pencerelerinden pencere öznitelikleri (ortalama, standart sapma, en büyük değişim gibi) üretmeli; yalnızca normal uçuşlarla eğitim yapmalı; her yöntemin AUC ve AP değerini, tür bazında tespit oranlarını ve saatte yanlış alarm sayısını raporlamalı.

**Önerilen yaklaşım.** Donma anomalisinin nokta tabanlı yöntemlerle yakalanamayacağını 61.14'te gördün; bu yüzden pencere içi değişkenlik özniteliği ekle (Bölüm 52'deki pencere öznitelikleri). Eşiği eğitim normalinin yüzdeliğinden seç ama bu eşiği ayrı bir doğrulama kümesinde kontrol et. Yanlış alarm bütçesini (saatte en fazla N alarm) önce belirle ve buna göre kalibre et.

**Başarı kriterleri.** (1) Donma anomalisi için pencere öznitelikleriyle tespit oranı, nokta tabanlı yönteme göre belirgin biçimde artar. (2) Eşik, eğitim dışı bir doğrulama kümesinde belirlenen bütçeyle uyumludur (sapma %50'den az). (3) Raporda her yöntemin kör noktası açıkça yazılır. (4) Sonuçlar üç tohumda tekrarlanır; ortalama ± sapma verilir.

### Ek Alıştırmalar

Aşağıdaki problemler kademelidir. ★ olanlar kavramı yoklar, ★★ olanlar bir türetme ya da küçük bir kod ister, ★★★ olanlar birden çok konuyu birleştirir. Mülakat etiketli olanlar klasik sorulardır.

1. ★ Bir k-means çalıştırmasında bir kümenin tüm noktaları çıkarılıp başka bir kümeye atanırsa, J neden azalmak zorundadır? Bu gözlemi tek cümleyle açıkla.
2. ★ Üç noktalı tek boyutlu bir veride k = 2 için her iki merkezin de sabit kaldığı bir başlangıç bul. Bu neden bir yerel minimum değildir? (Mülakat)
3. ★ Ortalamanın değil medyanın merkez olarak kullanıldığı bir kümeleme (k-medyan) hangi amaç fonksiyonunu en küçükler? Bu fonksiyon hangi durumda k-means'ten farklı sonuç verir?
4. ★★ Bir veri kümesinde n = 1000, d = 2 ve k = 5 var. k-means'in her iterasyonunun yaklaşık işlem maliyetini n, k, d cinsinden yaz. Tek bir iterasyonun bellek ihtiyacı nedir?
5. ★★ Ward bağlantısının birleşme maliyeti (n_a n_b / (n_a + n_b)) ‖μ_a − μ_b‖² olduğunu, iki kümenin SSE artışından türetebileceğini göster.
6. ★★ DBSCAN'de minPts = 3 ve üç noktanın tam olarak ε içinde birbirine uzaklık yoluyla bağlı olduğu bir zincir kur. Hangi noktalar çekirdek, sınır, gürültü olur?
7. ★★ EM'in M adımında σ² için yazılan formülde neden N_k'ye bölünür? Bu formülün, Bölüm 49.8'deki ağırlıklı MLE ile ilişkisini kur. (Mülakat)
8. ★★ Bir PCA'da iki özdeğer 9 ve 1 ise, ilk bileşenin açıkladığı oranı ve %90 eşiğinin hangi bileşen sayısında aşılacağını hesapla.
9. ★★ t-SNE'de perplexity 5 ile 50 arasında iki farklı gömme alındığında KL değerleri karşılaştırılabilir mi? Hangi koşulda karşılaştırılabilir?
10. ★★★ Bir veri setinde 1000 örnek ve 3 modu olan bir normal sınıf var. Tek Gauss Mahalanobis ile GMM(3) arasındaki eşik farkını, yanlış alarm oranı %1 hedefiyle birlikte tartış. (Mülakat)
11. ★★★ Isolation Forest'ta c(n) düzeltmesi ortalama yol uzunluğunu neden normalize eder? n = 256 ve n = 1024 için c(n)'yi hesapla ve yorumla.
12. ★★★ 61.14'teki renk paleti deneyini k = 4 ve k = 64 için tekrarla. Bit oranını ve PSNR'ı tahmin et, sonra ölç. Hangi k değerinde palet yükü toplam bitlerin %1'ini aşar? (Mülakat)

## Kod Okuma Egzersizi

Aşağıdaki kesit, yerel olarak kurulu scikit-learn 1.8.0 paketinin `sklearn/cluster/_kmeans.py` dosyasından (satır 224–278) alınmıştır; `_kmeans_plusplus` fonksiyonunun çekirdek döngüsüdür. Kesit birebir kopyadır; sayfaya sığması için uzun satırlar ve yorumlar sayfaya sığması için bölünmüştür; ifadede değişiklik yoktur.

@@KOD sk_kpp.py||# Pick the remaining@@

Kodun ilk bölümü varsayılan yerel deneme sayısını ve ilk merkezin seçimini içerir. İkinci bölüm, her yeni merkez için yerel adayların örneklenmesini ve en iyisinin seçilmesini yapar.

@@KOD sk_kpp.py|# Pick the remaining|# Decide which candidate@@

Son bölüm en iyi adayı kalıcı olarak ekler ve sonucu döndürür.

@@KOD sk_kpp.py|# Decide which candidate|@@

**Sorular — cevaplamadan geçme:**

1. `n_local_trials` varsayılanı `2 + int(np.log(n_clusters))` olarak ayarlanmış. Koddaki yorum bu değerin kaynağını Arthur ve Vassilvitskii'ye bağlıyor, ama onların bu değer için ayrıntılı sonuç raporlamadığını söylüyor. Bu ne anlama gelir? Kendi cümlenle açıkla.
2. İlk merkez, `random_state.choice(..., p=sample_weight / sample_weight.sum())` ile seçilir. Ağırlıklar eşitse bu seçim nasıl bir dağılımdır? Ağırlıklar farklıysa ne değişir?
3. `closest_dist_sq` ve `current_pot` değişkenleri neyi temsil eder? Her yeni merkezde bu iki değişken nasıl güncellenir?
4. `np.searchsorted(np.cumsum(sample_weight * closest_dist_sq), rand_vals)` satırı, D(x)² ile orantılı örneklemeyi nasıl gerçekleştirir? Kendi cümlenle, bir örnek üzerinden anlat.
5. Yerel denemelerde en küçük `candidates_pot` seçilir. Bu açgözlü seçim, Lloyd'un J'yi azaltan atama adımına benzer mi? Benzer olan ve farklı olan yönleri yaz.
6. Kendi `kmeanspp` fonksiyonunda (61.3) yerel deneme sayısını `yerel` ile aldık. Sklearn'de aynı davranışı elde etmek için hangi satırlar sizin kodunuzla birebir eşleşir, hangileri farklıdır?

## Bölüm Özeti

- Denetimsiz öğrenme etiket olmadan yapı arar: kümeleme, boyut indirgeme, yoğunluk ve anomali tespiti. Değerlendirme bir iş sorusudur; ölçütler (siluet, ARI, log-olabilirlik, yeniden yapılandırma hatası) ne ölçtüklerini bilerek yorumlanmalıdır.
- k-means, J = SSE amacını atama ve güncelleme adımlarıyla Lloyd algoritmasıyla yerel olarak en küçükler. Her adım J'yi artırmaz; yerel minimuma yakınsar. Başlangıç belirleyicidir: k-means++ yerel minimuma takılma olasılığını belirgin biçimde düşürür.
- Küme sayısı için dirsek ve siluet birbirinden farklı sonuçlar verebilir; ikisini birlikte ve alan bilgisiyle yorumla. k-means küresel, benzer yoğunluklu kümeleri varsayar; iç içe halkada başarısız olur.
- Hiyerarşik kümeleme bağlantı türüne çok duyarlıdır: tek bağlantı zincirleme yapar, Ward ise k-means'in SSE amacını hiyerarşik uygular. DBSCAN yoğunluk tabanlıdır, küme sayısını kendi bulur ve gürültüyü ayırır; parametreleri veriye uyumlanmalıdır.
- GMM ve EM, gizli bileşen atamasını sorumluluklarla yumuşatır; log-olabilirlik her iterasyonda artar. BIC bileşen sayısını karmaşıklık cezasıyla seçer. k-means, GMM'nin sert atamalı ve eşit küresel kovaryanslı özel durumudur.
- Boyut arttıkça uzaklıkların ayırt ediciliği azalır (boyutun laneti). PCA kovaryans matrisinin özvektörlerini ana bileşen olarak verir ve SVD ile eşdeğerdir; merkezleme, ölçek ve beyazlatma sonucu belirgin biçimde etkiler.
- t-SNE ve UMAP yerel komşulukları korumaya öncelik verir; t-SNE'nin KL kaybı ve perplexity parametresi görselleştirmeyi belirler. Saf gürültüde bile sahte kümeler görünür; bu yüzden sonuçlar ham uzayda doğrulanmalıdır.
- Mahalanobis uzaklığı korelasyonu hesaba katar ve tek değişkenli kontrollerin kaçırdığı anomalileri yakalar; ama veri çok modluysa tek Gauss yetersizdir. Isolation Forest ve GMM bu durumda daha uygundur, ama her yöntemin bir kör noktası vardır (ör. donmuş sensör).
- Anomali eşiği bir yanlış alarm bütçesine göre seçilmelidir; yüksek AUC tek başına operasyonel başarıyı garanti etmez. Eşik eğitim verisinden seçildiğinde test dağılımında sapabilir.

**Sonraki bölümde:** Bölüm 62, Olasılıksal Modeller ve Bayesçi ML ile devam ediyor. Bu bölümde GMM'nin sorumluluklarını sınıflandırma olasılığı olarak yorumladık; bir sonraki bölümde Bayes teoremini bir model olarak kuracağız: naive Bayes, Bayes ağları, gizli Markov modeli ve hedef takibi için Kalman filtresi. Bölüm 49'daki Gauss güncellemesi, sensör füzyonunun temelidir.

::: mulakat
1. k-means'i neden birden fazla başlangıçla çalıştırırsın? k-means++'ın garantisi ile pratik kazancı arasındaki farkı açıkla.
2. Dirsek ve siluet farklı k değerleri önerdiğinde hangisine güvenirsin ve neden?
3. Tek bağlantı ile Ward arasındaki farkı, bir köprü veri kümesi üzerinde açıkla. Hangisi zincirlemeye karşı dayanıklıdır?
4. EM neden her iterasyonda log-olabilirliği artırır? Sorumlulukların rolünü açıklar mısın?
5. PCA'yı neden kovaryans matrisini açıkça kurmadan SVD ile hesaplarsın? Koşul sayısı tartışmanı yap.
6. Yüksek boyutlu veride en yakın komşu aramasının neden zorlaştığını, boyutun laneti ile açıkla.
7. Anomali tespitinde yanlış alarm bütçesi nedir ve eşiği eğitim verisinin yüzdeliğinden seçmek neden tehlikelidir?
8. t-SNE çıktısında görülen bir kümenin gerçek olup olmadığını nasıl anlarsın? Hangi kontrolleri yaparsın?
:::
