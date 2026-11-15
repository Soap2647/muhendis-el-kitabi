## 41.12 Monolit ile mikroservis: bir takas

Sistem tasarımında en çok tartışılan kararlardan biri, uygulamanın tek bir süreç (monolit) mi yoksa bağımsız servisler (mikroservis) olarak mı kurulacağıdır. Bu soru bir moda sorusu gibi sorulur ama bir takas sorusudur ve iki tarafın bedeli de gerçektir.

**Monolit** tek bir süreç, tek bir dağıtım birimi ve çoğu zaman tek bir veritabanıdır. Modüller arası çağrılar bellek içidir: mikrosaniyeler sürer ve başarısız olmaz (ağ yoktur). Veritabanı işlemleri tek bir ACID sözleşmesi altında kalır. Hata ayıklama ve gözlemleme basittir, çünkü bir süreç ve bir günlük vardır. Bedeli, ölçeğin birlikte olmasıdır: sistemin bir parçası çok yük altındaysa bütün süreç çoğaltılır, ve ekip büyüdükçe herkes aynı kod tabanında değişiklik yaptığı için sürtünme artar.

**Mikroservis** her yetenek için bağımsız bir servis ve bağımsız bir dağıtım hattı anlamına gelir. Her servis kendi ölçeğine ve kendi sürüm takvimine sahiptir; bir ekip diğerini beklemeden yayın yapabilir. Bedeli çok daha ağırdır. Servisler arası her çağrı bir ağ çağrısıdır: gecikmesi milisaniyelerdir, zaman aşımına uğrayabilir, kısmen başarısız olabilir. Bölüm 41.9'daki dayanıklılık kalıpları artık zorunludur. Veri de parçalanır (41.10): bir işlem birden çok servisi etkilediğinde saga gibi yapılar gerekir. Gözlemlenebilirlik (41.11) bir lüks olmaktan çıkar, çünkü bir isteğin hangi servislerden geçtiğini izleyemezsen hatayı bulamazsın. Dağıtık bilişimde "ağ güvenilirdir" ve "gecikme sıfırdır" gibi varsayımların yanlış olduğu uzun zamandır bilinir (genel bilgi).

Karar için bir tablo yeterlidir:

| Ölçü | Monolit lehine | Mikroservis lehine |
|---|---|---|
| Ekip sayısı | Birkaç ekip, ortak kod | Birden fazla bağımsız ekip |
| Ölçek | Tüm sistem birlikte ölçeklenir | Bileşenler farklı ölçeklenir |
| Dağıtım sıklığı | Hepsi birlikte yayınlanır | Bileşenler ayrı, sık yayınlanır |
| Veri bütünlüğü | Tek işlemle korunur | Saga gibi telafi mekanizmaları kabul edilebilir |
| İşletim olgunluğu | Az izleme ve otomasyon yeter | İzleme, otomasyon ve sürüm yönetimi olgun |

Pratikte iyi bir ara yol **modüler monolit**tir (genel bilgi): tek bir süreç ve tek bir dağıtım, ama modüller arasında net sınırlar ve açık arayüzler. Sınırlar oturduğunda, bir modül gerçekten bağımsız ölçek ya da ekip gereksinimi doğurursa, ayırmak göreli olarak ucuz olur. Tersi, yani yanlış sınırlarla başlanmış bir mikroservis mimarisini birleştirmek, çok daha pahalıdır.

Savunma sanayiinde bu karar ek bir boyut taşır: sertifikasyon ve doğrulama. Bağımsız dağıtım, değişikliklerin etkisini daraltır ama her bağımsız servis için doğrulama kanıtı gerekir. Hangi tasarımı seçersen seç, yazılımın hangi sürümünün hangi bileşenle doğrulandığını izlemek zorundasın. Bu, Bölüm 78'de güvenilir yapay zekâ ve doğrulama konusunda tekrar karşımıza çıkacak.

## 41.13 Tasarım mülakatı protokolü

Sistem tasarımı mülakatlarında beklenen şey, mükemmel bir mimari çizmek değil, belirsiz bir problemi düzenli biçimde açabilmektir. Aşağıdaki protokol, bu bölümde gördüğümüz süreci yaklaşık kırk beş dakikalık bir mülakata uyarlar. Zamanlar bir rehberdir; önemli olan her adımı atlamamaktır.

1. **Gereksinimleri netleştir (yaklaşık 5 dakika).** İşlevsel gereksinimleri (ne yapılacak) ve işlevsel olmayanları (gecikme, verim, kullanılabilirlik, tutarlılık) sor. Kapsam dışını açıkça söyle: "kimlik doğrulamayı kapsam dışı sayıyorum" gibi.
2. **Tahmin yap (yaklaşık 5 dakika).** Kullanıcı sayısı, istek hızı, depolama ve bant genişliği için kaba bir hesap yap. Varsayımları yüksek sesle söyle. Sayıların büyüklük mertebesini doğrula; bu hesap tasarım kararlarını yönlendirmelidir.
3. **Üst düzey tasarım çiz (yaklaşık 10 dakika).** Ana bileşenleri, veri akışını ve temel API uçlarını göster (API tasarımı Bölüm 40'ta). Bileşen seçimini gerekçelendir; bir teknoloji adı söylemek gerekçe değildir.
4. **Derin dalış yap (yaklaşık 15 dakika).** Mülakatçının seçebileceği bir veya iki kritik bileşeni içeriden anlat: ID üretimi, önbellek, veri bölümleme ya da kuyruk. Burada bir ölçüm ya da hesap göstermek, en güçlü sinyaldir.
5. **Darboğaz ve takasları tartış (yaklaşık 10 dakika).** Yük on katına çıkarsa hangi bileşen önce kırılır? Arıza durumunda ne olur? Her kararın bedelini açıkça yaz; tek bir "doğru" tasarım olmadığını göster.

Mülakatta sık düşülen üç hata vardır. Birincisi, gereksinim sormadan çözüm çizmektir. İkincisi, her kutuya bir teknoloji adı koyup neden seçtiğini söylememektir. Üçüncüsü, darboğazı sormadan bütün sistemi büyütmek ve bunun maliyetini hiç konuşmamaktır. Bu protokol, bu üç hatayı da önlemek için vardır.

## 41.14 Tam vaka 1: URL kısaltıcı

Bu vaka, bölümdeki kavramların hepsini tek bir sistemde birleştirir. Gereksinimler: kullanıcı uzun bir URL verir ve kısa bir bağlantı alır; kısa bağlantı yönlendirme yapar; sistem günde bir milyon yeni URL üretebilmeli ve okuma yazmanın yüz katı olmalı (varsayım). Kayıtlar on yıl saklanmalı.

**Tahmin.** Günde bir milyon yeni URL, saniyede yaklaşık 11,6 yazma demektir. Okuma yazmanın yüz katıysa ortalama okuma hızı yaklaşık 1 157 istek/s, tepe (üç kat) yaklaşık 3 472 istek/s'dir. Bir kayıt (kısa kod, uzun URL ve meta veri) kabaca 260 bayt varsayılırsa günlük depolama 0,26 GB, on yıllık yaklaşık 949 GB eder. Bu boyut tek bir veritabanı için yönetilebilir; asıl zorluk okuma tepe hızı ve kısa kodların çakışmasıdır.

**Kısa kod uzunluğu.** `62^7` yaklaşık 3,5 x 10^12 farklı kod eder. On yılda üretilecek yaklaşık 3,65 x 10^9 kayıt için bu, yaklaşık 965 kat bolluk demektir. Yani 7 karakter yeterli. Kodlama ve çözme, bir sayıyı taban 62'de yazmaktır; aşağıdaki bloklar bunu ve ID üretimi seçeneklerini gösterir.

**ID üretimi.** Üç yol karşılaştırılabilir. **Sayaç**: her yeni kayıt bir önceki sayıya bir eklenerek alınır. Basittir ve çakışmasızdır, ama tek bir sayaca bağlıdır: onu paylaşmak için koordinasyon gerekir ve sayaç tahmin edilebilir kodlar üretir. **Kırpılmış hash**: URL'nin hash'inin ilk birkaç baytı alınır. Koordinasyon gerektirmez, ama çakışır. Betik bunu ölçer: 32 bitlik kırpılmış hash ile bir milyon URL'de 118 çakışma gözlendi; doğum günü hesabının beklediği değer 116,4'tür. Bu sonuç, kırpılmış hash'in kendi başına güvenli olmadığını gösterir; çakışma çözümü ayrıca gerekir. **Snowflake tarzı üretici**: 41 bit zaman, 10 bit makine kimliği ve 12 bit sıra numarası ile her makine koordinasyonsuz benzersiz ID üretir (Twitter'ın Snowflake düzeni, genel bilgi). Bir makine milisaniyede 4 096 ID üretebilir.

Aşağıdaki betik üç seçeneği de çalıştırır. Önce taban 62 kodlama, sonra sayaç uzunluğu, hash çakışması ve Snowflake tarzı üreticinin benzersizlik sınaması.

[[KOD b41_kisaltici.py 1]]

[[KOD b41_kisaltici.py 2]]

[[KOD b41_kisaltici.py 3]]

[[KOD b41_kisaltici.py 4]]

[[KOD b41_kisaltici.py 5]]

[[KOD b41_kisaltici.py 6]]

[[KOD b41_kisaltici.py 7]]

Çıktı:

[[CIKTI new_b41_kisaltici.txt | python b41_kisaltici.py]]

Çıktıdan üç sonuç çıkıyor. Birincisi, sayaç uzunluğu `1 000 000` sayısında 4, `10^9`'da 6 karakter: uzunluk logaritmik büyür, o yüzden "7 karakter" tasarımı on yıl ölçeğinde yeterlidir. İkincisi, kırpılmış hash'in çakışması beklenenle uyumludur. Üçüncüsü, Snowflake tarzı üreticinin 100 000 kimliği dört makineden ve sabit saatle üretmesine rağmen hepsi tekildir; çünkü her makine kendi makine kimliğini taşır ve sıra numarası milisaniye içinde artar.

Snowflake yaklaşımının iki ayrıntısını bilmek gerekir. Birincisi, ID'ler zamanı ve makine kimliğini açığa çıkarır; kısa kodlar sırayla tahmin edilebilir hâle gelir. Gerçek bir kısaltıcıda bu, başka kullanıcıların bağlantılarını keşfetmesine yol açabilir; çözüm, ID'yi bir karıştırma (permütasyon) ile sarmalamaktır (genel bilgi). İkincisi, saat geri giderse (NTP düzeltmesi gibi) üretici çakışma riski taşır; bu yüzden üretici, saatin geri gittiğini algılayınca bekler ya da hata verir. Kodumuzda bu kontrol yoktur ve bu bilinçli bir sadeleştirmedir.

**Mimari.** Şekil 41.9 bileşenleri gösterir. İstemci, yük dengeleyiciye istek gönderir; uygulama sunucuları durumsuzdur (41.4), bu yüzden herhangi bir kopya herhangi bir isteği karşılayabilir. Yazma yolu, Snowflake tarzı üreticiden ID alır, kısa kodu üretir ve kaydı veritabanına yazar. Okuma yolu önce önbelleğe (LRU ya da Redis) bakar; yoksa veritabanına gider ve sonucu önbelleğe koyar. Okuma yazmanın yüz katı olduğu için önbellek, isabeti yüksek olduğunda veritabanının asıl yükünü taşır (41.7).

![Şekil 41.9: URL kısaltıcı mimarisi. Okuma yolu önbellekten, yazma yolu ID üreticisinden geçer.](gorseller/b41_url_kisaltici.png)

Yönlendirme yanıtının kodu da bir takastır. 301 (kalıcı yönlendirme) tarayıcıların ve ara sistemlerin yönlendirmeyi önbelleğe almasına izin verir; böylece sonraki isteklerin çoğu sunucuya hiç gelmez, ama tıklama sayımını kaybedersin. 302 (geçici yönlendirme) her seferinde sunucuya gelir; analitik doğrudur ama yük daha yüksektir (genel bilgi).

**Hata ve takaslar.** Önbellek çökerse, okuma yükü doğrudan veritabanına biner. Bu yüzden önbellek için 41.9'daki bölme ve devre kesici kalıplarını, ayrıca veritabanına giden yolda bir istek birleştirme (single-flight) mekanizmasını uygularsın. Veritabanı yazması başarısız olursa üretilen kısa kod boşa çıkar; bu, ID'nin yazılmadan önce ayrılmasının bedelidir ve kabul edilebilir bir sızıntıdır. Hız sınırı, kötüye kullanılan bir istemcinin kısa kod üretme kotasını sınırlar.

## 41.15 Tam vaka 2: İHA telemetrisi ve komuta sistemi

Bu vaka, savunma bağlamında bir sistemin üç özelliğini birlikte gösterir: yüksek frekanslı veri alımı, kayıp bağlantıda davranış ve güvenli komut kanalı. Gereksinimleri şöyle yazalım: 60 İHA, her biri 50 Hz telemetri; görev sırasında yer istasyonu kesintisiz çalışmalı; bağlantı kesildiğinde veri kaybı en aza indirilmeli; komutlar kimliği doğrulanmış ve tekrarlara karşı güvenli olmalı; ham veri 30 gün, dakikalık özet ise beş yıl saklanmalı.

**Kapasite.** Örnek 2'deki hesap bu gereksinimin temelidir: filo saniyede 3 000 paket üretir; ham hız 7,2 Mbit/s, tepe 14,4 Mbit/s; sıkıştırılmış günlük veri 19,44 GB. Ham veriyi 30 gün tutmak yaklaşık 583 GB sıkıştırılmış veri demektir (`19,44 x 30`). Dakikalık özetin boyutu, her araç için tek bir özet kanalıyla dakikada bir kayıt ve kayıt başına 24 bayt (ortalama, minimum, maksimum; 8 bayt × 3) varsayılırsa, beş yılda `60 x 1 440 x 24 x 365 x 5` bayt, yani yaklaşık 3,8 GB eder (varsayım). Bu, zaman serisi deposu için küçük bir boyuttur; asıl yük ham veriden gelir ve onu 30 günle sınırlamak sistemi yönetilebilir kılar. Zaman serisi sıkıştırması (Bölüm 35.10'daki delta-of-delta) ham veri boyutunu bir kat daha küçültür; sıkıştırma oranı veriye bağlıdır.

**Mimari.** Şekil 41.10 üç katmanı ve komut kanalını gösterir. Uçakta sensörlerden gelen veri bir tampona ve bir yazma öncesi günlüğe (WAL, Bölüm 35.4) yazılır. Her pakete bir sıra numarası ve zaman damgası eklenir. Bağlantı kesilirse uçak tampondaki veriyi biriktirir; bağlantı geri geldiğinde son onaylanan sıra numarasından devam eder. Yer istasyonu, gelen paketlerdeki sıra numarası boşluklarını tespit eder ve kayıp olarak işaretler; eksik paketi yeniden isteyip istemeyeceği, görevin gereksinimine göre karar verilen bir takastır. Yer istasyonu gerçek zamanlı izleme için son değerleri kısa TTL'li bir önbellekte tutar (41.7). Merkez, birleştirilmiş veriyi zaman serisi deposunda saklar ve downsampling uygular.

![Şekil 41.10: İHA telemetri sistemi: uçta tampon ve WAL, yer istasyonunda birleştirme ve önbellek, merkezde zaman serisi deposu; komut kanalı ayrıdır.](gorseller/b41_iha_telemetri.png)

**Telemetri ve komut taşıması.** Telemetride düşük gecikme önemlidir ve kayıp, sıra numarasıyla tespit edilip, gerekirse yeniden gönderilerek yönetilebilir. Bölüm 31.3'te TCP'nin bir bayt akışı olduğunu ve paket sınırlarını korumadığını gördün; bu, paket tabanlı bir telemetri için bir sorundur. Bölüm 31.10'daki UDP ve durdur-bekle örneği, düşük gecikmeli bir taşımanın kendi güvenilirlik katmanını gerektirdiğini gösterdi. Bu nedenle telemetri için paket tabanlı bir taşıma ve sıra numarası önerilir (tasarım önerisi; kesin protokol görev gereksinimine ve donanıma bağlıdır). Komut kanalı ise farklı bir sözleşme ister: her komut kimliği doğrulanmış olmalı, bir sıra numarası taşımalı ve uçak aynı sıra numaralı komutu yalnızca bir kez uygulamalıdır. Bu, Bölüm 41.8'deki idempotent tüketicinin doğrudan uygulamasıdır.

Komut akışı şöyle işler. Yer istasyonu komutu imzalar ve sıra numarasını ekler. Uçak komutu alır, imzayı doğrular, daha önce uygulanmış bir sıra numarası ise yalnızca onayı yeniden gönderir, yeni ise uygular ve onay döner. Yer istasyonu onay alınmazsa zaman aşımından sonra komutu yeniden gönderir (41.9). Bu döngü, ağın tekrar ürettiği komutların iki kez uygulanmasını önler; ama onay da kaybolursa yer istasyonu bunu bilemez ve komutu yeniden gönderir; uçak bunu tekrar tanır ve yalnızca onayı yeniden döner. Bu, "tam bir kez etkisi" sağlar ama "tam bir kez teslim" değildir.

**Kayıp bağlantıda davranış.** Bağlantı kesildiğinde iki soru ortaya çıkar: uçak ne yapar ve yer istasyonu ne bilir? Uçağın tampon kapasitesi, kesintinin ne kadar süreceğine dair bir sınır koyar: tampon `T` saniye ise, `T`'den uzun kesintide en eski veri kaybolur. Yer istasyonu kesintiyi görünür kılmalıdır; sessiz bir veri boşluğu, operatörün yanlış karar vermesine yol açabilir. Komut kanalı kesildiğinde uçağın ne yapacağı görevin güvenlik tanımına bağlıdır ve bu bölümde karar verilmez; ama bunun tasarımda açıkça tanımlanması gerektiğini söyleyebiliriz.

**Edge'de ön işleme.** Uçtaki işlemci sınırlıdır ve Örnek 2'de her paket için yalnızca 333 mikrosaniye süre bütçen vardı. Bu yüzden ham veriyi olduğu gibi göndermek yerine uçta bir ön işleme yapılabilir: kalibrasyon, eşik kontrolü ve kısa pencerelerin özeti. Bu, ağ yükünü ve merkezdeki depolamayı azaltır, ama uçtaki kod güvenilir ve test edilmiş olmalıdır. Uçtaki çıkarım ve donanım tarafı Bölüm 46'da işlenecek.

**Yüzdelikler ve izleme.** Yer istasyonunda izlenmesi gereken gecikme, ortalama değil p99 ve maksimum olmalıdır; bir sensörün son saniyedeki değeri bir gecikmeyle geldiyse operatör yanlış bir durum görür. Uçtan merkeze bir isteğin yolunu izlemek için trace kimlikleri (41.11) kullanılmalı; her paket bir sıra numarası taşıdığından, yolu izlemek bu kimlikle kolaydır.

Bu vakanın öğrettiği şey, bir sistemin her katmanının farklı bir sözleşme taşıdığıdır: telemetri "kayıp olabilir ama gecikmesi düşük" olmalı; komut "kayıp olmamalı, tekrarlanmamalı ve kimliği doğrulanmalı"; saklama ise "ucuz ve sorgulanabilir" olmalıdır. Tek bir taşıma ve tek bir veritabanı bu üç sözleşmeyi birden karşılayamaz. Bu yüzden mimari, sözleşmelerin ayrılmasıdır.
