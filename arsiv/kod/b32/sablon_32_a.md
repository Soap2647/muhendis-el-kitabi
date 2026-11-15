%% kisim_no: VII
%% kisim_ad: Ağ
%% bolum_no: 32
%% baslik: Güvenlik

## Giriş: Güvenlik sonradan eklenen bir özellik değildir

Bölüm 29'da paketlerin ağda nasıl yolculuk ettiğini, Bölüm 30'da HTTP ve DNS'in konuşma kurallarını, Bölüm 31'de ise bir soketten baytların nasıl okunup yazıldığını gördün. Üç bölümde de bir soru bilerek bekletildi: karşıdaki taraf her zaman dürüst miydi? Bölüm 31'in sonunda "ağdan gelen her baytın düşman olabileceğini" söyledik. Bu bölümün işi, o cümleyi bir mühendislik disiplinine dönüştürmektir.

Güvenlik, kod bittikten sonra eklenen bir katman değildir; tasarımın ilk gününden başlayan bir sorumluluktur. Bir protokole bütünlük alanı sonradan eklenirse, eski istemciler ve kaydedilmiş trafik yüzünden tüm kurguyu baştan yazmak gerekebilir. Bu yüzden önce "neyi koruyoruz, kimden, neden?" sorusunu soruyor, sonra araçlara geçiyoruz: kriptografi, güvenli bellek kullanımı, girdi doğrulama ve test yöntemleri.

Savunma sanayiinde bu sorunun ağırlığı daha da büyüktür. Bir İHA'nın komut kanalına sahte bir komut girebilmesi, yer istasyonundaki telemetrinin değiştirilebilmesi ya da uçuş yazılımındaki bir tamponun taşması yalnızca bir yazılım hatası değildir; görevi ve insan güvenliğini etkiler. Bu yüzden güvenlik standartları (örneğin DO-178C ve DO-326A) ve bağımsız değerlendirme süreçleri, yazılım mühendisliğinin ayrılmaz parçasıdır.

Bu bölümde iki şeyi kendimiz yapacağız: küçük programlar yazıp onların hatalarını kendimiz bulacağız. Bir kuralı baştan koyuyoruz: bu bölümde hiçbir saldırı aracı yazılmadı, çalıştırılmadı ve üçüncü taraf bir sisteme karşı işlem yapılmadı. Tüm deneyler kendi programlarımız üzerinde, yerelde çalıştı. Tek istisna, 32.4'te yapılan, example.com'un sertifikasını yalnızca okuyan tek bir TLS el sıkışmasıdır; uygulama verisi gönderilmez.

::: not
C deneylerinin tamamı WSL2 içindeki Ubuntu 24.04 üzerinde gcc 13.3.0 ile derlendi ve çalıştırıldı; ASan ve UBSan raporları bu Linux araç zincirinden gelir. Python deneyleri Windows üzerinde Python 3.12.10 ile çalıştı. Zamanlama ölçümleri ve adres değerleri makineye göre değişir; yönü ve nedenini anlamak önemlidir, mutlak sayıyı değil.
:::

## 32.1 Güvenlik düşüncesi ve tehdit modelleme

Güvenliğe başlamadan önce üç soru sorarız: neyi koruyoruz, kime karşı koruyoruz ve bunun bedeli ne? Bu soruların cevabı yoksa her önlem rastgele kalır ve bir sonraki sistemde sıfırdan başlamak gerekir.

**CIA üçlüsü** (gizlilik, bütünlük, erişilebilirlik; İngilizce confidentiality, integrity, availability) bilgi güvenliğinin ilk çerçevesidir. **Gizlilik**, verinin yetkisiz kişilere sızmamasıdır: telemetri paketini dinleyen birinin İHA'nın konumunu okuyamaması gibi. **Bütünlük**, verinin yetkisiz biçimde değiştirilmemesidir: bir komutun hedefinin yolda değiştirilememesi gibi. **Erişilebilirlik**, sistemin yetkili kullanıcılara zamanında hizmet vermeye devam etmesidir: yer istasyonunun bir taşkın saldırısıyla susturulamaması gibi.

Üçlüye üç özellik daha eklenir. **Kimlik doğrulama** (authentication), karşıdakinin iddia ettiği kişi olduğunu kanıtlar. **Yetkilendirme** (authorization), kimliği doğrulanmış birinin neye erişebileceğini belirler. **İnkâr edilemezlik** (non-repudiation), bir işlemi yapan tarafın sonradan bunu reddedememesidir. Bu özellikler birbirine bağlıdır: inkâr edilemezlik, kimlik doğrulama ve bütünlük olmadan kurulamaz.

![Şekil 32.1: CIA üçlüsü ve üç tamamlayıcı özellik. Altı özellik birlikte bir güvenlik hedefini tanımlar.](gorseller/b32_cia.png)

Bir sistemin saldırıya ne kadar açık olduğu **saldırı yüzeyi** (attack surface) ile ölçülür. Dinlenen her port, okunan her dosya, ayrıştırılan her alan, çalıştırılan her harici komut ve kullanılan her bağımlılık bu yüzeyin parçasıdır. Yüzeyi küçültmek, yüzeyi korumaktan çoğu zaman daha ucuzdur: kullanılmayan bir portu kapatmak, o porttaki ayrıştırıcıyı test etmekten çok daha az iştir.

Üç ilke her tasarımda yol gösterir. **En az ayrıcalık** (least privilege): bir bileşen görevini yapmak için gereken en küçük yetkiye sahip olmalıdır. Bölüm 34'te veritabanı kullanıcısını salt okunur tanımlamak bunun bir örneğidir. **Derinlemesine savunma** (defense in depth): tek bir önlemin başarısız olabileceğini kabul edip birbirini tamamlayan katmanlar koymak. Şekil 32.2 bu fikri gösterir. **Güvenli varsayılan** (secure by default): ayarlanmamış bir sistem güvenli olmalı, güvensiz davranış açıkça seçilmelidir. 32.4'te göreceğin `verify=False` örneği, güvensiz seçeneği varsayılan yapmanın en sık düşülen hatalardan biri olduğunu gösterecek.

![Şekil 32.2: Derinlemesine savunma. Bir katman aşılsa bile sonraki katmanlar saldırının etkisini sınırlar.](gorseller/b32_katmanlar.png)

**Güven sınırı** (trust boundary), verinin güvenilmeyen bir bölgeden güvenilen bir bölgeye geçtiği yerdir. Yer istasyonunun ağ arayüzü bir güven sınırıdır: oradan gelen her bayt düşman olabilir. Güvenlik analizinin ilk adımı bu sınırları çizmektir; bunun için veri akış diyagramları kullanılır.

### Tehdit modelleme ve STRIDE

**Tehdit modelleme** (threat modeling), bir sistemin hangi yollarla ihlal edilebileceğini sistematik biçimde aramaktır. Sık kullanılan yöntem **STRIDE**'dır; altı harfin her biri bir tehdit sınıfını adlandırır ve her tehdit, korunması gereken bir özelliğe karşılık gelir. **S**poofing (kimlik taklidi) kimlik doğrulamayı; **T**ampering (değiştirme) bütünlüğü; **R**epudiation (inkâr) inkâr edilemezliği; **I**nformation disclosure (bilgi sızıntısı) gizliliği; **D**enial of service (hizmet reddi) erişilebilirliği; **E**levation of privilege (yetki yükseltme) yetkilendirmeyi hedef alır.

STRIDE'ı Bölüm 31'deki İHA yer istasyonuna uygulayalım. Bu sistemde iki akış var: İHA'dan yere telemetri ve yerden İHA'ya komut. Aşağıdaki tablo her bileşen için en önemli tehdidi ve önlemi listeler. Önlemlerin çoğu bu bölümde ele alınacak; bazıları Bölüm 30 ve 31'de zaten görüldü.

| Bileşen / akış | STRIDE | Tehdit | Önlem (bölüm) |
|---|---|---|---|
| Telemetri (İHA → yer) | T | Paketin alanı değiştirilir | HMAC etiketi (32.3) |
| Telemetri | S, T | Kaydedilmiş paket tekrar oynatılır | Sıra numarası, tekrar reddi (32.3) |
| Telemetri | I | Konum ve durum dinlenir | AEAD ile şifreleme (32.3) |
| Komut kanalı (yer → İHA) | S | Sahte komut gönderilir | İmza veya HMAC (32.3) |
| Komut kanalı | E | Düşük yetkili bir komut kritik işlemi yapar | Komut başına yetki denetimi (32.10) |
| Komut kanalı | D | Çok sayıda paket kanalı tıkar | Boyut ve hız sınırı (31.4, 32.8) |
| Yer istasyonu web paneli | T, E | Panele betik enjekte edilir; istenmeden işlem yapılır | Çıktı kaçışı, CSRF jetonu (32.7, 32.9) |
| Görev günlükleri | R | Bir kayıt sonradan silinir | Değiştirilemez günlük (32.10) |
| Gizli anahtar | I | Anahtar kaynak kodda ya da günlükte görünür | Sır yönetimi (32.10) |
| Ayrıştırıcı (C kodu) | T, D, E | Bellek bozulur; uygulama çöker ya da kontrolü kaybeder | ASan, sınır denetimi, derleyici korumaları (32.5, 32.6) |
| Bağımlılıklar | T | Kötü amaçlı bir sürüm kurulur | Sürüm sabitleme, hash doğrulama (32.10) |

Bu tablo bir kontrol listesi değil, bir başlangıç noktasıdır. Gerçek bir sistemde tehdit listesi, sistem güvenliği (system safety) analizi ve sertifikasyon gereksinimleriyle birlikte üretilir. Yazılım mühendisinin görevi, her satırın koda ve teste karşılık geldiğinden emin olmaktır.

## 32.2 Kriptografinin temelleri: hash, parola ve rastgelelik

Bu bölümde en önemli kural şudur: **kendi kriptografik algoritmanı yazma**. AES, SHA-256 ve Ed25519'un tasarımı yıllarca açık analiz edilmiş matematiktir. Sen onları sınanmış bir kütüphane üzerinden kullanırsın; yanlış olan, kütüphaneyi yanlış kullanmaktır. Burada hangi aracın ne işe yaradığını ve hangi yanlış kullanımın felakete yol açtığını öğreneceksin.

::: dikkat
Mülakatta "kendi şifreleme algoritmamı yazarım" demek kırmızı bayraktır. Doğru cevap şudur: "Sınanmış bir kütüphane kullanırdım; benim işim doğru algoritmayı seçmek, anahtarı güvenle üretmek ve yapılandırmayı doğru yapmaktır." Bu bölümdeki kodların hiçbiri kriptografik algoritma içermez; her biri var olan bir kütüphaneyi çağırır.
:::

### Hash fonksiyonu ve çığ etkisi

**Hash fonksiyonu** (hash function), keyfi uzunlukta bir girdiyi sabit uzunlukta bir özete çevirir. SHA-256 256 bit (32 bayt) özet üretir. Kriptografik bir hash fonksiyonundan üç şey beklenir: girdiden özeti hesaplamak kolay olmalı; özetten girdiyi bulmak pratikte mümkün olmamalı (ön görüntü direnci); iki farklı girdinin aynı özeti vermesi pratikte mümkün olmamalıdır (çakışma direnci).

Bu özellikler matematiksel olarak kanıtlanmış değildir; yıllarca analiz edilmiş ve bugüne kadar kırılmamış oldukları için güvenilirler. Bu yüzden hash seçimi bir karardır ve zamanla değişebilir: MD5 ve SHA-1 bugün çakışma saldırılarına karşı güvenlik amacıyla kullanılmaz.

Bir hash'in dağılımını ilk bakışta değerlendirebilirsin: **çığ etkisi** (avalanche effect). Girdinin tek bir bitini değiştirdiğinde çıktının yaklaşık yarısının değişmesini beklersin. 256 bitlik bir özette bu yaklaşık 128 bit demektir. Aşağıdaki fonksiyon, iki girdinin özetlerini alıp farklı bitleri sayar. Bitler XOR ile karşılaştırılır: sonucunda 1 olan her bit "farklı" demektir.

@@KOD b32_1_parola.py 21 26@@

Aşağıdaki çıktı, `cig` kipinin gerçek çıktısıdır. İlk satır referansı kendisiyle karşılaştırır ve 0 verir. İkinci ve üçüncü satırlar tek karakter farkıyla değişen girdileri gösterir; son satır ise 1000 ardışık girdi çiftinin ortalamasıdır.

@@TERMW§python b32_1_parola.py cig§python b32_1_parola.py cig@@

Ortalama fark 128'e yakın çıktı. Bu bir tesadüf değildir: iyi bir hash fonksiyonunun çıktı bitleri, girdinin herhangi bir bitinden bağımsız görünmelidir. Çığ etkisi zayıfsa, saldırgan girdi üzerinde küçük değişikliklerle özetlerin nasıl değiştiğini öğrenerek bir yapı tespit edebilir. Bu, hash'in kriptografik güvenlik için "yeterince karışık" olup olmadığını gösteren ilk ölçüttür; tek başına yeterli değildir.

::: baglanti
Bölüm 9'daki hash tablolarında FNV ve MurmurHash gibi kriptografik olmayan hash'ler görmüştün. Onlar hızlı ve dağılımı iyidir; ama bir saldırganın çakışma üretmesini engellemezler. Kriptografik hash ise bu saldırıyı pratikte imkânsız kılar, bedeli ise hızdır.
:::

### Parola saklama: neden düz hash yetmez

Bir kullanıcı sisteme parolasını yazdığında, sunucunun parolayı olduğu gibi saklamaması gerekir. Parolanın hash'ini saklamak daha iyidir, ama yalnızca hash yetmez; üç ayrı sorun vardır.

**Birinci sorun: hız.** SHA-256 çok hızlı bir fonksiyondur. Bu hız, veritabanı sızdığında saldırganın milyonlarca aday parolayı saniyeler içinde deneyebilmesi demektir. Parola saklamada hız bir avantaj değil, bir risktir. Aşağıdaki ölçümde bu farkı görebilirsin: tek bir SHA-256 hesabı ile tek bir scrypt hesabı arasında on binlerce kat fark vardır. Kurguda hashing'i yavaşlatmak, saldırganın maliyetini artırır, senin kullanıcının maliyetini ise yalnızca bir kez, giriş anında artırır.

**İkinci sorun: aynı parolalar aynı özeti verir.** İki kullanıcı "parola123" yazarsa, saklanan özetler aynı olur. Saldırgan bir kez hesaplanmış bir tabloyla (önceden hesaplanmış özetler tablosu, rainbow table) bu özetleri anında çözebilir. **Tuz** (salt), her kayıt için rastgele üretilen ve özetle birlikte saklanan bir değerdir. Tuz sayesinde aynı parola farklı özet üretir ve önceden hesaplanmış tablo işe yaramaz hâle gelir. Tuz gizli değildir; amacı tekilliği sağlamaktır.

**Üçüncü sorun: maliyet parametreleri.** Güçlü bir parola saklama fonksiyonu (KDF, key derivation function) yavaş olmak zorundadır ve bu yavaşlığı parametrelerle ayarlanabilir kılar. Python'un standart kütüphanesi iki seçenek sunar: `hashlib.pbkdf2_hmac` ve `hashlib.scrypt`. **scrypt** bellek yoğun (memory-hard) tasarlanmıştır: her hesap belirli bir bellek miktarı gerektirir, bu da özel donanımla (GPU, ASIC) yapılan toplu denemeleri pahalılaştırır. Argon2 de benzer bir tasarımdır, ama Python'un standart kütüphanesinde yoktur.

![Şekil 32.3: Tuzlu KDF ile parola saklama. Kayıtta tuz üretilir ve özetle birlikte saklanır; doğrulamada aynı tuz ve parametrelerle yeniden hesaplanıp sabit zamanlı karşılaştırma yapılır.](gorseller/b32_parola.png)

Aşağıdaki iki fonksiyon kaydı üretir ve doğrular. Kayıt biçimi, algoritmayı ve parametreleri kendi içinde taşır; böylece ileride maliyet artırıldığında eski kayıtlar çalışmaya devam eder ve yeniden hash'lenebilir.

@@KOD b32_1_parola.py 41 66@@

Doğrulamada iki noktaya dikkat et. Birincisi, kayıttan okunan `n` değeri üst sınırla denetlenir (`N_MAKS`). Kayıt bir veritabanı sızıntısıyla değişmiş olabilir ve saldırgan bu değeri çok büyük yazarsa, doğrulama sırasında sunucunun belleğini tüketebilir. Kayıt verisi de güvenilmeyen girdi gibi işlenmelidir. İkincisi, karşılaştırma `hmac.compare_digest` ile yapılır. Bunun nedenini 32.3'te göreceksin.

Şimdi fonksiyonların gerçekten çalıştığını görelim. `test` kipi, doğru parolayı kabul eden, yanlış parolayı reddeden, aynı parolanın farklı tuzla farklı kayıt ürettiğini gösteren ve bozuk kayıtları reddeden dokuz kontrol yapar.

@@TERMW§python b32_1_parola.py test§python b32_1_parola.py test@@

Şimdi maliyet farkını ölç. `sure` kipi, aynı makinede her yöntemin ortalama hash süresini ölçer ve CSV dosyasına yazar. Sayılar makineye göre değişir; ama oranlar her zaman aynı yönü gösterir.

@@TERMW§python b32_1_parola.py sure§python b32_1_parola.py sure@@

Ölçüm sonucu, düz SHA-256 ile scrypt arasında yaklaşık dört büyüklük mertebesi (on binlerce kat) fark olduğunu gösterir. Parola sızıntısı senaryosunda saldırganın her denemesi bu kadar pahalıdır. Parametreleri seçerken iki şeyi dengele: sunucunun giriş anındaki gecikmesi ve saldırganın maliyeti. Güncel parametreleri her zaman güncel bir rehberden (örneğin OWASP Password Storage Cheat Sheet) al; değerler donanım geliştikçe artar.

::: ipucu
Parola politikası konusunda kuralı dengele: uzun parola karmaşık kurallardan daha değerlidir. NIST SP 800-63B, zorunlu karakter karmaşıklığı yerine uzunluğu ve yasaklı parolaların taranmasını önerir (genel bilgi). Parolayı asla düz metin olarak günlüğe yazma ve hata mesajına koyma.
:::

## 32.3 Bütünlük, kimlik ve şifreleme: HMAC, AEAD, imza

Bölüm 31'deki telemetri paketi 28 bayt uzunluğundaydı ve son dört baytı CRC-32 idi. CRC, iletim hatalarını yakalar: bir kablodaki gürültü ya da bir bitin yanlış okunması. Ama CRC bir **anahtar** kullanmaz. Bu yüzden CRC bir **bütünlük** kanıtı değil, bir **hata algılama** kodudur. Aşağıdaki kod bunu gösterir: bir paketin alanını değiştirip CRC'yi yeniden hesaplayan biri, paketi kabul ettirebilir. Bu işlemin bir anahtara ihtiyacı yoktur, dolayısıyla herkes yapabilir.

@@KOD b32_2_hmac_telemetri.py 71 88@@

Bu fonksiyonlar iki şeyi gösterir: CRC'li bir paketin gövdesi değiştirilip CRC yeniden hesaplanabilir ve alıcı bunu fark etmez. Değişimin nerede yapıldığına, sahte bir enlem değerinin neden kabul edildiğine dikkat et. Bu, CRC'nin bu iş için neden yetersiz olduğunun en açık gösterimidir.

### HMAC: anahtarlı bütünlük

**HMAC** (Hash-based Message Authentication Code), bir hash fonksiyonu ile gizli bir anahtarı birleştirip mesajın etiketini üretir. RFC 2104'te tanımlanan yapı şöyledir: `HMAC(K, m) = H((K ⊕ opad) ∥ H((K ⊕ ipad) ∥ m))`. Burada `opad` ve `ipad` sabit bayt desenleridir. Yapının iç içe iki hash çağrısı içermesi, uzunluk uzatma saldırısı (length extension) gibi hash'in kendi yapısından gelen zayıflıkları engeller. Bunu ezberlemen gerekmez; önemli olan HMAC'in bir hash değil, bir **anahtarlı** doğrulama kodu olduğudur.

![Şekil 32.4: HMAC ile bütünlük. Gönderen gövdeyi anahtarla etiketler; alıcı aynı anahtarla yeniden hesaplar ve etiketleri karşılaştırır.](gorseller/b32_hmac.png)

Bölüm 31'deki paket düzenini koruyup CRC yerine 16 baytlık bir HMAC-SHA256 etiketi koyalım. Etiket, tam 32 baytlık özetin ilk 16 baytıdır. Kesme (truncation) etiketi kısaltır; 128 bit, sahte etiket bulmanın pratikte mümkün olmadığı bir düzeyde kalır. Kısaltmanın pratik nedeni paket boyutudur. Kısaltma yapılırken, etiket uzunluğunun bir güvenlik kararı olduğunu da unutma.

Yeni paket düzeninde govde 24 bayt (Bölüm 31'deki `!BBIIiiiH`), etiket 16 bayttır. Sıra numarası govdenin içindedir, yani etiketin kapsamındadır: onu değiştirmek etiketi geçersiz kılar. Bu, tekrar oynatma (replay) saldırısını engelleyen iki mekanizmadan birincisidir; ikincisi alıcının son gördüğü sıra numarasını tutmasıdır.

@@KOD b32_2_hmac_telemetri.py 30 69@@

Alıcı önce etiketi doğrular, sonra sıra numarasına bakar. Bu sıra önemlidir: sıra numarasına önce bakmak, sahte bir paketin alıcının durumunu değiştirmesine izin verir. Etiketi doğrulamadan hiçbir alanı kabul etme.

Aşağıdaki çıktı paketin boyutunu ve hex dökümünü, ardından aynı paketin ikinci kez gelmesinin ve bozulmuş bir paketin reddinin sonuçlarını gösterir. Son satır, CRC ile sahte paketin hâlâ kabul edilebildiğini de doğrular.

@@TERMW§python b32_2_hmac_telemetri.py goster§python b32_2_hmac_telemetri.py goster@@

Testler daha sıkı bir kanıt verir. Paketin 320 bitinin her birini tek tek değiştiriyoruz (40 bayt × 8 bit) ve her değişimin reddedildiğini doğruluyoruz. Ardından yanlış anahtar, tekrar oynatma, geri giden sıra ve kısa paket senaryolarını deniyoruz.

@@TERMW§python b32_2_hmac_telemetri.py test§python b32_2_hmac_telemetri.py test@@

Burada dikkat edilmesi gereken iki sınır var. Birincisi, sıra numarası 32 bitliktir; 2^32 paketten sonra sayaç taşar ve alıcının yeniden anahtar değiştirmesi gerekir. İkincisi, alıcı yeniden başlatıldığında `son_sira` değeri sıfırlanır ve eski paketler tekrar kabul edilebilir. Gerçek sistemde son sıra numarası kalıcı olarak saklanmalı ya da oturum anahtarı her başlatmada değiştirilmelidir.

### Sabit zamanlı karşılaştırma

Etiketi karşılaştırırken `==` kullanmak yanlıştır. Python'un bayt karşılaştırması, ilk farklı baytta durur. Bu, karşılaştırmanın süresinin, eşleşen önek uzunluğuna bağlı olması demektir. Ölçülebilir bir zamanlama farkı olduğunda, saldırgan bu farkı kullanarak etiketi bayt bayt tahmin edebilir. Buna **yan kanal** (side channel) saldırısı denir: sonuç değil, işlemin süresi ya da enerji tüketimi bilgi taşır.

`hmac.compare_digest` karşılaştırmayı, uzunluk aynıysa, sonucun içeriğinden bağımsız bir süre içinde yapar. Bu kütüphane fonksiyonunun Python kaynağında da bunu görebilirsin (Kod Okuma bölümünde). Bir ölçüm notu: bu makinede `==` ile `compare_digest` arasındaki zamanlama farkını güvenilir biçimde ölçemedik; Python'un yorumlayıcı yükü, bu farkı gürültüde kaybettirir. Yine de kuralı uygula: gizli bir değeri, tahmin edilebilir bir süreyle karşılaştırma.

::: baglanti
Bölüm 24'te gördüğün Spectre ve Meltdown saldırıları da yan kanal fikrine dayanır: işlemci önbelleğinin zamanlaması, spekülatif yürütmenin izini sızdırabilir. Yazılım tarafında sabit zamanlı kod ve bellek erişim desenlerinin kontrolü aynı ailedendir.
:::

### Rastgelelik: random ile secrets

Anahtarların, jetonların ve nonce'ların kriptografik olarak rastgele olması gerekir. Python'da iki modül var: `random` ve `secrets`. `random` modülü Mersenne Twister algoritmasını kullanır; bu algoritma simülasyonlar için hızlı ve dağılımı iyi bir üreteçtir, ama tahmin edilebilir. Tohumu bilinen bir `random` üreteci her zaman aynı diziyi üretir. `secrets` modülü ise işletim sisteminin kriptografik üreteçlerini (Windows'ta bu, işletim sistemi kaynağıdır) kullanır.

Aşağıdaki deney, bu farkı kendi programımızda ölçer. 128 bitlik bir jeton, tohumu 16 bit olan bir `random` üreteciyle üretilirse, etkin güç yalnızca 16 bittir: tohum uzayı taranarak jeton yeniden bulunabilir. Bu bir saldırı aracı değil, tohum uzayının gücünü ölçen bir deneydir.

@@KOD b32_4_rastgele.py 22 39@@

@@TERMW§python b32_4_rastgele.py goster§python b32_4_rastgele.py goster@@

Çıktı üç şeyi gösterir: `random` aynı tohumla aynı diziyi üretir, `secrets` her çağrıda farklı değer verir ve 16 bitlik tohum uzayında jeton saniyeler içinde bulunur. Dersin özü: bir değerin gücü, nominal uzunluğuyla değil, gerçek belirsizliğiyle ölçülür. Jetonun 128 bit olması, tohumun 16 bit olmasını telafi etmez.

Kural basit: güvenlik için `secrets` (veya `os.urandom`), oyun ve simülasyon için `random` kullan. C tarafında da aynı ilke geçerlidir: `rand()` güvenlik için kullanılmaz; işletim sisteminin kriptografik kaynağı (Linux'ta `getrandom`) tercih edilir.

### AEAD: şifreleme ve doğrulamayı birlikte yapmak

Şifreleme ile bütünlük ayrı kavramlardır. Yalnızca şifrelenmiş bir paket, değiştirilebilir olabilir: saldırgan şifreli baytları bilmeden değiştirir ve alıcı bozuk düz metin okur. **AEAD** (Authenticated Encryption with Associated Data), şifrelemeyi ve doğrulamayı tek bir işlemde yapar. Çıktı, şifreli metin ile birlikte bir **etiket** (tag) içerir; etiket tutmazsa alıcı hiçbir düz metin üretmez.

AEAD'in dört girdisi vardır. **Anahtar** gizlidir ve iki taraf arasında paylaşılır. **Nonce** (number used once) her mesaj için benzersiz olmalı, genellikle rastgele üretilir ve açıkça iletilir. **Düz metin** şifrelenecek veridir. **Ek veri** (associated data) şifrelenmeyen ama etiketin kapsamına giren bilgidir; Bölüm 31'deki başlık alanları, yani sıra numarası ve tür, buraya konabilir. Çıktılar **şifreli metin** ve **etiket**tir.

![Şekil 32.5: AEAD girdileri ve çıktıları. Ek veri şifrelenmez ama etiketle korunur; etiket tutmazsa düz metin üretilmez.](gorseller/b32_aead.png)

Python'da AEAD için `cryptography` paketinin `AESGCM` ve `ChaCha20Poly1305` sınıflarını kullanırsın. Aşağıdaki kod, sıra numarasını ek veri olarak bağlayıp şifreler; bir baytın değişmesinin, ek verinin değişmesinin ve yanlış anahtarın reddedildiğini gösterir. Kodda kriptografik algoritma yoktur; yalnızca doğru çağrılar vardır.

@@KOD b32_3_aead_imza.py 22 33@@

Nonce kuralı bu tasarımın en çok hata yapılan kısmıdır. Aynı anahtarla aynı nonce'u iki kez kullanmak felakettir. Genel bilgi olarak: GCM gibi bir mod, nonce tekrarında düz metinlerin XOR'unu sızdırır ve doğrulama anahtarının ele geçmesine de yol açabilir; bu durumda saldırgan sahte mesajlar üretebilir. Rastgele 96 bit nonce ile anahtar başına mesaj sayısı sınırlıdır; NIST SP 800-38D bu sınırı belirtir (genel bilgi). Sayaç tabanlı nonce ise tekrar riskini ortadan kaldırır, ama sayaç bir daha geri dönmemelidir. Bu tasarım kararını protokolünde açıkça yaz.

@@TERMW§python b32_3_aead_imza.py goster§python b32_3_aead_imza.py goster@@

Çıktıda paket boyutunun 12 bayt nonce, sifreli metin ve 16 bayt etiketten oluştuğunu görüyorsun. Tek bir bitin değişmesi `InvalidTag` ile reddedilir; ek verinin değişmesi (örneğin sıra numarasının "8" yapılması) de reddedilir. Bu, Bölüm 31'deki telemetri paketinde sıra numarasını şifrelemeden de koruyabileceğimizin kanıtıdır.

### Açık anahtarlı imza ve anahtar yönetimi

HMAC ve AEAD, anahtarı iki tarafın da bildiği **simetrik** kriptografidir. Komut kanalında ise başka bir gereksinim vardır: yer istasyonu bir komut gönderdiğinde, İHA bu komutun gerçekten yer istasyonundan geldiğini kanıtlayabilmeli, ama İHA'nın yalnızca doğrulama anahtarı olsun istiyoruz. Bu, **açık anahtarlı** (asymmetric) kriptografinin ve **dijital imzanın** görevidir.

Dijital imzada üreticinin **özel anahtarı** ile imza atılır ve herkesin bilebileceği **açık anahtar** ile doğrulanır. Özel anahtar yalnızca imzalayanda kalır. Ed25519, bu iş için yaygın ve hızlı bir eğri tabanlı şemadır. Aşağıdaki kod imza üretir ve doğrular; değişen mesajın reddini gösterir.

@@KOD b32_3_aead_imza.py 62 73@@

Anahtar yönetimi, algoritma seçiminden daha zordur ve çoğu gerçek olay buradan çıkar. Birkaç ilke: özel anahtar üretildiği yerden dışarı çıkmamalı (mümkünse donanım güvenlik modülü, TPM ya da güvenli eleman); her ortam için ayrı anahtar kullanılmalı; anahtarlar belirli aralıklarla değiştirilebilmeli (rotasyon); bir anahtarın sızdığından şüphelenildiğinde iptal ve yenileme için bir süreç olmalı. Bir oturum anahtarı ise tek bir el sıkışma için üretilir ve sonra atılır; buna ileriye dönük gizlilik (forward secrecy) denir ve TLS 1.3 bunu varsayılan yapar.

::: dikkat
Anahtarı koda, yapılandırma dosyasına ya da depoya gömmek, güvenliği kendi elinle bitirmektir. Git geçmişinde bir kez görünen anahtar, silinse bile sızmış sayılır; anahtarı iptal edip yenilemek gerekir. Bu konu 32.10'da ayrıntılı işlenir.
:::

## 32.4 TLS: HTTPS'in arkasındaki güvenlik

Bölüm 29'da katmanlı modeli, Bölüm 30'da HTTP'yi gördün ve HTTPS'in "HTTP + TLS" olduğunu söyledik. **TLS** (Transport Layer Security), TCP'nin üzerinde çalışan bir katmandır ve üç şeyi sağlar: sunucunun kimliğini kanıtlar, verinin gizliliğini ve bütünlüğünü korur. Bölüm 30'daki HTTP istekleri, TLS katmanına geçirildiğinde aynı mesajlar şifrelenmiş ve doğrulanmış olarak taşınır. HTTP'nin mesaj biçimi değişmez; değişen, baytların kanalda nasıl taşındığıdır.

TLS'nin yapısı iki aşamadan oluşur. Önce **el sıkışma** (handshake) gelir: taraflar sürümü ve şifre takımını anlaşır, anahtar paylaşımı yapar ve sunucunun kimliğini doğrular. Sonra **kayıt katmanı** (record layer) gelir: uygulama verisi, el sıkışmada türetilen anahtarlarla şifrelenip doğrulanarak taşınır. TLS 1.0 ve 1.1 bugün kullanılmaz (RFC 8996); güncel sürüm TLS 1.3'tür.

### TLS 1.3 el sıkışması (kavramsal)

Aşağıdaki şekil, TLS 1.3'ün tam el sıkışmasını kavramsal olarak gösterir. Bu bir protokol şeması; her mesajın bayt düzeni ayrıntısı değildir.

![Şekil 32.6: TLS 1.3 el sıkışması (kavramsal). Anahtar paylaşımı istemci ilk mesajda yapılır; sunucunun kimliği şifreli kısımda kanıtlanır ve iki yönde Finished mesajlarıyla el sıkışma doğrulanır.](gorseller/b32_tls_el.png)

Adımları sırayla izle. İstemci **ClientHello** mesajında desteklediği sürümleri, şifre takımlarını ve kendi geçici (ephemeral) açık anahtarını gönderir. Sunucu **ServerHello** ile kendi geçici açık anahtarını ve seçtiği şifre takımını yanıtlar. Bu noktadan sonra iki taraf ortak bir gizli değer hesaplayabilir (elliptik eğri Diffie-Hellman, ECDHE) ve bu değerden trafik anahtarlarını türetir. Bu sayede bir gizli anahtar sızsa bile geçmiş oturumların şifresi çözülemez: buna ileriye dönük gizlilik denir.

Sunucu, sertifikasını ve **CertificateVerify** mesajını şifreli olarak gönderir. CertificateVerify, sunucunun sertifikadaki özel anahtara sahip olduğunu, o ana kadarki el sıkışma özetini imzalayarak kanıtlar. Son olarak her iki taraf **Finished** mesajıyla el sıkışmanın bozulmadığını doğrular; ardından uygulama verisi akmaya başlar. Tam el sıkışma TLS 1.3'te tek bir gidiş-dönüş (1-RTT) gerektirir; bu, eski sürümlere göre bir gecikme kazancıdır.

::: not
Bu şema tek bir sertifika zinciriyle ve tam el sıkışmayla anlatıldı. Oturum yeniden kullanımı (session resumption) ve 0-RTT gibi ayrıntılar bu bölümün kapsamı dışındadır; istemci tarafında 0-RTT verisinin tekrar oynatılabileceği bilinen bir risktir (genel bilgi).
:::

### Sertifika zinciri ve doğrulama

Sunucunun "ben example.com'um" demesi yetmez; bunu bir güven zinciri ile kanıtlaması gerekir. Sertifika, bir **sertifika otoritesinin** (CA) bir alan adını ve açık anahtarı birbirine bağlayan dijital imzasıdır. Sunucu sertifikası (yaprak) bir ara CA tarafından imzalanır, o da kök CA tarafından imzalanır. Kök CA'nın sertifikası işletim sistemi ya da tarayıcının güvenilen kök deposunda bulunur. Bu yüzden zinciri yukarı doğru doğrularsın: her imza, bir üst sertifikanın açık anahtarıyla kontrol edilir ve en sonunda güvenilen bir köke varılır.

![Şekil 32.7: Sertifika zinciri. Yaprak sertifika ara CA tarafından, ara CA kök CA tarafından imzalanır; doğrulama güvenilen köke kadar yürür.](gorseller/b32_zincir.png)

Doğrulama tek bir kontrol değildir; birkaç adım vardır. Zincir kurulur ve her imza doğrulanır. Her sertifikanın geçerlilik tarihleri şimdiki zamanı kapsamalıdır. Sertifikanın konu alanı (SAN, Subject Alternative Name), bağlandığın alan adıyla eşleşmelidir. Son olarak iptal durumu kontrol edilir (CRL veya OCSP; genel bilgi). Python'un `ssl` modülü bu adımların hepsini varsayılan bağlamda yapar.

Kendi test sertifikamızı bir CA olarak işaretleyip iki bağlamı deneyelim. Aşağıdaki kod, yerel bir TLS sunucusu açar ve üç farklı istemci yapılandırmasını dener. Hepsi `127.0.0.1` üzerinde, yerelde çalışır.

@@KOD b32_5_tls.py 91 124@@

Burada iki önemli şey olur. Varsayılan bağlam, kendinden imzalı sertifikayı güvenilen bir kök olmadığı için reddeder. Bunu "tehlikeli" bağlam kabul eder; çünkü doğrulamayı kapatmıştır. Üçüncü bağlam ise sertifikayı açıkça güvenilen kök olarak verir; bu, özel bir CA kullanan kurumsal ve savunma sistemlerinin doğru yoludur.

@@TERMW§python b32_5_tls.py yerel§python b32_5_tls.py yerel@@

::: ipucu
Bir İHA sisteminde yer istasyonu ile uçak arasındaki TLS sertifikası çoğunlukla özel bir CA'dan gelir. Doğru yöntem, o CA'nın kök sertifikasını yalnızca bu uygulamanın güven deposuna eklemektir; sistem genelindeki deponu değiştirmek ya da doğrulamayı kapatmak değil. Böylece yalnızca bu CA'nın imzaladığı sertifikalar kabul edilir.
:::

### verify=False neden tehlikelidir?

Üçüncü satırdaki "dogrulama kapali" bağlamı, sertifika zincirini, geçerlilik tarihini ve isim eşleşmesini tamamen atlar. Sonuç, TLS'in kimlik kısmının yok olmasıdır. İstemci, kendisine kim sunulursa sunulsun bağlanır. Bir ağ yolunda duran biri, kendi sertifikasını sunarak trafiği okuyabilir ve değiştirebilir; bu saldırıya **ortada adam** (man in the middle) denir. Yani `verify=False` ile HTTPS'in yalnızca şifreleme kısmı kalır ve güvenin tek dayanağı olan kimlik doğrulama kaybolur.

Bu hatayı yapanlar genellikle "sadece geliştirme sırasında" niyetiyle yazar ve bu kod bir sonraki sürüme sızar. Kural: doğrulamayı kapatan bir satır gördüğünde, bunun neden orada olduğunu ve neden kaldırılamadığını yazılı olarak açıklamadan kabul etme. Yerel test sertifikası sorununu çözmenin doğru yolu, o sertifikayı açıkça güvenilir kök olarak eklemektir.

Şimdi aynı yapılandırmayı gerçek bir sunucuda, yalnızca okuma amacıyla deneyelim. `example.com` sunucusuna tek bir TLS el sıkışması yapılır, sertifikanın alanları okunur ve bağlantı kapatılır. Uygulama verisi gönderilmez.

@@TERMW§python b32_5_tls.py ornek§python b32_5_tls.py ornek@@

Çıktıda TLS sürümünü (TLSv1.3), şifre paketini ve sertifika zincirinin yaprağını (konu) ile veren kuruluşu görürsün. Veren, bir ara CA'dır; bu, zincirin en az iki halkalı olduğunu gösterir. Sertifika tarihleri zamanla değişir, bu yüzden çıktın bu bölümdekinden farklı olabilir; önemli olan alanların anlamıdır.

