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

```python
def cig_bit(a, b):
    """Iki girdinin SHA-256 ozetleri arasindaki farkli bit sayisi."""
    x = hashlib.sha256(a).digest()
    y = hashlib.sha256(b).digest()
    return sum(bin(p ^ q).count("1") for p, q in zip(x, y))

```

Aşağıdaki çıktı, `cig` kipinin gerçek çıktısıdır. İlk satır referansı kendisiyle karşılaştırır ve 0 verir. İkinci ve üçüncü satırlar tek karakter farkıyla değişen girdileri gösterir; son satır ise 1000 ardışık girdi çiftinin ortalamasıdır.

```term
$ python b32_1_parola.py cig
girdi                    ozet farki (bit / 256)
b'merhaba'               0
b'merhabb'               123
b'Merhaba'               133
b'merhaba '              128
1000 ardisik girdi, ortalama fark: 127.8 bit
```

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

```python
def parola_hashle(parola):
    """Rastgele tuzlu scrypt ozeti. Kayit bicimi kendi parametrelerini
    tasir; boylece ileride maliyet artirilabilir."""
    tuz = os.urandom(16)                    # kriptografik rastgele
    ozet = hashlib.scrypt(parola.encode("utf-8"), salt=tuz,
                          n=N, r=R, p=P, dklen=32)
    return "scrypt$%d$%d$%d$%s$%s" % (N, R, P, tuz.hex(), ozet.hex())


def parola_dogrula(parola, kayit):
    try:
        ad, n, r, p, tuz_h, ozet_h = kayit.split("$")
        if ad != "scrypt":
            return False
        n, r, p = int(n), int(r), int(p)
        tuz = bytes.fromhex(tuz_h)
        beklenen = bytes.fromhex(ozet_h)
    except ValueError:
        return False                        # bozuk kayit: reddet
    if not (2 <= n <= N_MAKS) or r < 1 or p < 1:
        return False                        # kayit guvenilmez
    aday = hashlib.scrypt(parola.encode("utf-8"), salt=tuz,
                          n=n, r=r, p=p, dklen=len(beklenen))
    # Sabit zamanli karsilastirma: == ilk farkli baytta durur
    return hmac.compare_digest(aday, beklenen)

```

Doğrulamada iki noktaya dikkat et. Birincisi, kayıttan okunan `n` değeri üst sınırla denetlenir (`N_MAKS`). Kayıt bir veritabanı sızıntısıyla değişmiş olabilir ve saldırgan bu değeri çok büyük yazarsa, doğrulama sırasında sunucunun belleğini tüketebilir. Kayıt verisi de güvenilmeyen girdi gibi işlenmelidir. İkincisi, karşılaştırma `hmac.compare_digest` ile yapılır. Bunun nedenini 32.3'te göreceksin.

Şimdi fonksiyonların gerçekten çalıştığını görelim. `test` kipi, doğru parolayı kabul eden, yanlış parolayı reddeden, aynı parolanın farklı tuzla farklı kayıt ürettiğini gösteren ve bozuk kayıtları reddeden dokuz kontrol yapar.

```term
$ python b32_1_parola.py test
GECTI dogru parola kabul
GECTI yanlis parola red
GECTI bos parola red
GECTI ayni parola, farkli tuz
GECTI iki kayit da dogrulanir
GECTI ozet son bayti degisince red
GECTI bozuk bicim red
GECTI hex olmayan tuz red
GECTI asiri n sinirda red
hata sayisi: 0
```

Şimdi maliyet farkını ölç. `sure` kipi, aynı makinede her yöntemin ortalama hash süresini ölçer ve CSV dosyasına yazar. Sayılar makineye göre değişir; ama oranlar her zaman aynı yönü gösterir.

```term
$ python b32_1_parola.py sure
yontem                              ms/hash
sha256 (tuzlu, tek tur)               0.001
pbkdf2-hmac-sha256 (600k)           216.069
scrypt (n=2^14, r=8, p=1)            58.000
```

Ölçüm sonucu, düz SHA-256 ile scrypt arasında yaklaşık dört büyüklük mertebesi (on binlerce kat) fark olduğunu gösterir. Parola sızıntısı senaryosunda saldırganın her denemesi bu kadar pahalıdır. Parametreleri seçerken iki şeyi dengele: sunucunun giriş anındaki gecikmesi ve saldırganın maliyeti. Güncel parametreleri her zaman güncel bir rehberden (örneğin OWASP Password Storage Cheat Sheet) al; değerler donanım geliştikçe artar.

::: ipucu
Parola politikası konusunda kuralı dengele: uzun parola karmaşık kurallardan daha değerlidir. NIST SP 800-63B, zorunlu karakter karmaşıklığı yerine uzunluğu ve yasaklı parolaların taranmasını önerir (genel bilgi). Parolayı asla düz metin olarak günlüğe yazma ve hata mesajına koyma.
:::

## 32.3 Bütünlük, kimlik ve şifreleme: HMAC, AEAD, imza

Bölüm 31'deki telemetri paketi 28 bayt uzunluğundaydı ve son dört baytı CRC-32 idi. CRC, iletim hatalarını yakalar: bir kablodaki gürültü ya da bir bitin yanlış okunması. Ama CRC bir **anahtar** kullanmaz. Bu yüzden CRC bir **bütünlük** kanıtı değil, bir **hata algılama** kodudur. Aşağıdaki kod bunu gösterir: bir paketin alanını değiştirip CRC'yi yeniden hesaplayan biri, paketi kabul ettirebilir. Bu işlemin bir anahtara ihtiyacı yoktur, dolayısıyla herkes yapabilir.

```python
def crc_paketle(govde):
    return govde + struct.pack("!I", zlib.crc32(govde))


def crc_kabul(p):
    """Yalnizca CRC kontrol eden alici: govdeyi kabul eder."""
    govde, crc = p[:-4], struct.unpack("!I", p[-4:])[0]
    return zlib.crc32(govde) == crc


def crc_sahtele(p, ofset, yeni_bayt):
    """Govdeyi degistirip CRC'yi yeniden hesaplar. CRC bir anahtar
    olmadigi icin bunu herkes yapabilir: CRC butunluk degil, hata
    algilamadir."""
    govde = bytearray(p[:-4])
    govde[ofset] = yeni_bayt
    return crc_paketle(bytes(govde))

```

Bu fonksiyonlar iki şeyi gösterir: CRC'li bir paketin gövdesi değiştirilip CRC yeniden hesaplanabilir ve alıcı bunu fark etmez. Değişimin nerede yapıldığına, sahte bir enlem değerinin neden kabul edildiğine dikkat et. Bu, CRC'nin bu iş için neden yetersiz olduğunun en açık gösterimidir.

### HMAC: anahtarlı bütünlük

**HMAC** (Hash-based Message Authentication Code), bir hash fonksiyonu ile gizli bir anahtarı birleştirip mesajın etiketini üretir. RFC 2104'te tanımlanan yapı şöyledir: `HMAC(K, m) = H((K ⊕ opad) ∥ H((K ⊕ ipad) ∥ m))`. Burada `opad` ve `ipad` sabit bayt desenleridir. Yapının iç içe iki hash çağrısı içermesi, uzunluk uzatma saldırısı (length extension) gibi hash'in kendi yapısından gelen zayıflıkları engeller. Bunu ezberlemen gerekmez; önemli olan HMAC'in bir hash değil, bir **anahtarlı** doğrulama kodu olduğudur.

![Şekil 32.4: HMAC ile bütünlük. Gönderen gövdeyi anahtarla etiketler; alıcı aynı anahtarla yeniden hesaplar ve etiketleri karşılaştırır.](gorseller/b32_hmac.png)

Bölüm 31'deki paket düzenini koruyup CRC yerine 16 baytlık bir HMAC-SHA256 etiketi koyalım. Etiket, tam 32 baytlık özetin ilk 16 baytıdır. Kesme (truncation) etiketi kısaltır; 128 bit, sahte etiket bulmanın pratikte mümkün olmadığı bir düzeyde kalır. Kısaltmanın pratik nedeni paket boyutudur. Kısaltma yapılırken, etiket uzunluğunun bir güvenlik kararı olduğunu da unutma.

Yeni paket düzeninde govde 24 bayt (Bölüm 31'deki `!BBIIiiiH`), etiket 16 bayttır. Sıra numarası govdenin içindedir, yani etiketin kapsamındadır: onu değiştirmek etiketi geçersiz kılar. Bu, tekrar oynatma (replay) saldırısını engelleyen iki mekanizmadan birincisidir; ikincisi alıcının son gördüğü sıra numarasını tutmasıdır.

```python
def paketle(anahtar, sira, zaman, enlem, boylam, irtifa, batarya):
    govde = GOVDE.pack(SURUM, TUR_TELE, sira, zaman,
                       enlem, boylam, irtifa, batarya)
    etiket = hmac.new(anahtar, govde, hashlib.sha256).digest()
    return govde + etiket[:ETIKET_BOY]


class Alici:
    """Etiket dogrular, sira numarasi ilerlemiyorsa reddeder."""

    def __init__(self, anahtar):
        self.anahtar = anahtar
        self.son_sira = -1
        self.red = {"bicim": 0, "etiket": 0, "tekrar": 0}

    def al(self, p):
        if len(p) != PAKET_BOY:
            self.red["bicim"] += 1
            return None
        govde, etiket = p[:GOVDE.size], p[GOVDE.size:]
        beklenen = hmac.new(self.anahtar, govde,
                            hashlib.sha256).digest()[:ETIKET_BOY]
        # Sabit zamanli karsilastirma: zamanlama sizintisini onler
        if not hmac.compare_digest(beklenen, etiket):
            self.red["etiket"] += 1
            return None
        surum, tur, sira, zaman, enlem, boylam, irtifa, batarya = \
            GOVDE.unpack(govde)
        if surum != SURUM or tur != TUR_TELE:
            self.red["bicim"] += 1
            return None
        if sira <= self.son_sira:          # tekrar oynatma (replay)
            self.red["tekrar"] += 1
            return None
        self.son_sira = sira
        return {"sira": sira, "zaman": zaman, "enlem": enlem,
                "boylam": boylam, "irtifa": irtifa,
                "batarya": batarya}


```

Alıcı önce etiketi doğrular, sonra sıra numarasına bakar. Bu sıra önemlidir: sıra numarasına önce bakmak, sahte bir paketin alıcının durumunu değiştirmesine izin verir. Etiketi doğrulamadan hiçbir alanı kabul etme.

Aşağıdaki çıktı paketin boyutunu ve hex dökümünü, ardından aynı paketin ikinci kez gelmesinin ve bozulmuş bir paketin reddinin sonuçlarını gösterir. Son satır, CRC ile sahte paketin hâlâ kabul edilebildiğini de doğrular.

```term
$ python b32_2_hmac_telemetri.py goster
paket boyu: 40 bayt (govde 24 + etiket 16)
hex  : 02 01 00 00 00 07 00 01 e2 40 17 3e ed 80 13 9c 24 40 00 00
       3b 60 2e cc 86 76 b5 0b 14 d5 87 c1 49 f1 5a 37 3b 77 17 6b
ilk teslim: True
ayni paket tekrar: True
bit bozulmus: True
red sayaclari: {'bicim': 0, 'etiket': 1, 'tekrar': 1}
etiketsiz sahte govde reddedildi: True
CRC ile sahte paket kabul: True
```

Testler daha sıkı bir kanıt verir. Paketin 320 bitinin her birini tek tek değiştiriyoruz (40 bayt × 8 bit) ve her değişimin reddedildiğini doğruluyoruz. Ardından yanlış anahtar, tekrar oynatma, geri giden sıra ve kısa paket senaryolarını deniyoruz.

```term
$ python b32_2_hmac_telemetri.py test
GECTI boyut 40 bayt
GECTI gecerli paket kabul
GECTI 320 tek-bit bozulmanin hepsi red (kabul=0)
GECTI yanlis anahtar red
GECTI ilk paket kabul
GECTI ayni paket (replay) red
GECTI geri sira (0 < 1) red
GECTI kisa paket red
GECTI sira ilerleyince kabul
GECTI CRC'li sahte paket kabul ediliyor (zafiyet gosterimi)
hata sayisi: 0
```

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

```python
def zayif_jeton(tohum):
    """YANLIS: random, tohumu bilinen kucuk bir kaynaktan alir."""
    return "%032x" % random.Random(tohum).getrandbits(128)


def guclu_jeton():
    """DOGRU: isletim sistemi CSPRNG'sinden 128 bit."""
    return secrets.token_hex(16)


def tohum_say(hedef_jeton, bit):
    """Tohum uzayini sirayla tarar; etkin gucu olcer."""
    denenen = 0
    for tohum in range(1 << bit):
        denenen += 1
        if zayif_jeton(tohum) == hedef_jeton:
            return tohum, denenen
    return None, denenen
```

```term
$ python b32_4_rastgele.py goster
random, ayni tohum -> ayni dizi (tekrarlanabilirlik):
  tohum=42 ilk: bdd640fb06671ad11c80317fa3b1799d
  tohum=42 ikinci: bdd640fb06671ad11c80317fa3b1799d
secrets, her cagrida farkli:
   68c029b914abf91653377a37d065498b
   8b0c9ace5c95d11efc309eaff50f16d7
   4f655d28845619c8b8e5ee282c509022
16-bit tohum uzayinda tarama:
  bulunan tohum=40123, denenen=40124, sure=0.17 s
  jetonun nominal gucu: 128 bit; etkin guc: 16 bit
```

Çıktı üç şeyi gösterir: `random` aynı tohumla aynı diziyi üretir, `secrets` her çağrıda farklı değer verir ve 16 bitlik tohum uzayında jeton saniyeler içinde bulunur. Dersin özü: bir değerin gücü, nominal uzunluğuyla değil, gerçek belirsizliğiyle ölçülür. Jetonun 128 bit olması, tohumun 16 bit olmasını telafi etmez.

Kural basit: güvenlik için `secrets` (veya `os.urandom`), oyun ve simülasyon için `random` kullan. C tarafında da aynı ilke geçerlidir: `rand()` güvenlik için kullanılmaz; işletim sisteminin kriptografik kaynağı (Linux'ta `getrandom`) tercih edilir.

### AEAD: şifreleme ve doğrulamayı birlikte yapmak

Şifreleme ile bütünlük ayrı kavramlardır. Yalnızca şifrelenmiş bir paket, değiştirilebilir olabilir: saldırgan şifreli baytları bilmeden değiştirir ve alıcı bozuk düz metin okur. **AEAD** (Authenticated Encryption with Associated Data), şifrelemeyi ve doğrulamayı tek bir işlemde yapar. Çıktı, şifreli metin ile birlikte bir **etiket** (tag) içerir; etiket tutmazsa alıcı hiçbir düz metin üretmez.

AEAD'in dört girdisi vardır. **Anahtar** gizlidir ve iki taraf arasında paylaşılır. **Nonce** (number used once) her mesaj için benzersiz olmalı, genellikle rastgele üretilir ve açıkça iletilir. **Düz metin** şifrelenecek veridir. **Ek veri** (associated data) şifrelenmeyen ama etiketin kapsamına giren bilgidir; Bölüm 31'deki başlık alanları, yani sıra numarası ve tür, buraya konabilir. Çıktılar **şifreli metin** ve **etiket**tir.

![Şekil 32.5: AEAD girdileri ve çıktıları. Ek veri şifrelenmez ama etiketle korunur; etiket tutmazsa düz metin üretilmez.](gorseller/b32_aead.png)

Python'da AEAD için `cryptography` paketinin `AESGCM` ve `ChaCha20Poly1305` sınıflarını kullanırsın. Aşağıdaki kod, sıra numarasını ek veri olarak bağlayıp şifreler; bir baytın değişmesinin, ek verinin değişmesinin ve yanlış anahtarın reddedildiğini gösterir. Kodda kriptografik algoritma yoktur; yalnızca doğru çağrılar vardır.

```python
def sifrele(anahtar_sinifi, anahtar, yuk, ek_veri):
    """Rastgele 96 bit nonce; cikti = nonce + sifreli + etiket."""
    nonce = os.urandom(12)
    sifreli = anahtar_sinifi(anahtar).encrypt(nonce, yuk, ek_veri)
    return nonce + sifreli


def coz(anahtar_sinifi, anahtar, paket, ek_veri):
    nonce, sifreli = paket[:12], paket[12:]
    # Etiket tutmazsa InvalidTag: hic duz metin uretilmez
    return anahtar_sinifi(anahtar).decrypt(nonce, sifreli, ek_veri)

```

Nonce kuralı bu tasarımın en çok hata yapılan kısmıdır. Aynı anahtarla aynı nonce'u iki kez kullanmak felakettir. Genel bilgi olarak: GCM gibi bir mod, nonce tekrarında düz metinlerin XOR'unu sızdırır ve doğrulama anahtarının ele geçmesine de yol açabilir; bu durumda saldırgan sahte mesajlar üretebilir. Rastgele 96 bit nonce ile anahtar başına mesaj sayısı sınırlıdır; NIST SP 800-38D bu sınırı belirtir (genel bilgi). Sayaç tabanlı nonce ise tekrar riskini ortadan kaldırır, ama sayaç bir daha geri dönmemelidir. Bu tasarım kararını protokolünde açıkça yaz.

```term
$ python b32_3_aead_imza.py goster
duz metin: 36 bayt
paket    : 64 bayt (12 nonce + 52 sifreli+etiket)
etiket   : son 16 bayt, sifreli kisim: 36 bayt
cozuldu  : True
sifreli kisimda 1 bit: InvalidTag (red)
ek veri (sira) degisti: InvalidTag (red)
ChaCha20-Poly1305 paket: 64 bayt
Ed25519 imza: 64 bayt
imza dogrulandi
degisen mesaj: InvalidSignature (red)
```

Çıktıda paket boyutunun 12 bayt nonce, sifreli metin ve 16 bayt etiketten oluştuğunu görüyorsun. Tek bir bitin değişmesi `InvalidTag` ile reddedilir; ek verinin değişmesi (örneğin sıra numarasının "8" yapılması) de reddedilir. Bu, Bölüm 31'deki telemetri paketinde sıra numarasını şifrelemeden de koruyabileceğimizin kanıtıdır.

### Açık anahtarlı imza ve anahtar yönetimi

HMAC ve AEAD, anahtarı iki tarafın da bildiği **simetrik** kriptografidir. Komut kanalında ise başka bir gereksinim vardır: yer istasyonu bir komut gönderdiğinde, İHA bu komutun gerçekten yer istasyonundan geldiğini kanıtlayabilmeli, ama İHA'nın yalnızca doğrulama anahtarı olsun istiyoruz. Bu, **açık anahtarlı** (asymmetric) kriptografinin ve **dijital imzanın** görevidir.

Dijital imzada üreticinin **özel anahtarı** ile imza atılır ve herkesin bilebileceği **açık anahtar** ile doğrulanır. Özel anahtar yalnızca imzalayanda kalır. Ed25519, bu iş için yaygın ve hızlı bir eğri tabanlı şemadır. Aşağıdaki kod imza üretir ve doğrular; değişen mesajın reddini gösterir.

```python
    ozel = Ed25519PrivateKey.generate()
    acik = ozel.public_key()
    mesaj = b"komut: hedef=WP-7"
    imza = ozel.sign(mesaj)
    print("Ed25519 imza: %d bayt" % len(imza))
    acik.verify(imza, mesaj)
    print("imza dogrulandi")
    try:
        acik.verify(imza, b"komut: hedef=WP-8")
        print("degisen mesaj kabul (hata!)")
    except InvalidSignature:
        print("degisen mesaj: InvalidSignature (red)")
```

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

```python
def dene(ad, baglam, port):
    try:
        with socket.create_connection(("127.0.0.1", port),
                                      timeout=5) as ham:
            with baglam.wrap_socket(ham,
                                    server_hostname="localhost") as s:
                print("%-34s KABUL  (surum %s)" % (ad, s.version()))
                return True
    except ssl.SSLCertVerificationError as e:
        print("%-34s RED    (%s)" % (ad, e.verify_message))
        return False
    except (ssl.SSLError, OSError) as e:
        print("%-34s HATA   (%s)" % (ad, e))
        return False


def yerel(dizin=None):
    dizin = dizin or tempfile.mkdtemp(prefix="b32tls_")
    cert_yol, anah_yol = kendinden_sertifika(dizin)
    sonuc = {}
    port = sunucu_baslat(cert_yol, anah_yol)
    sonuc["varsayilan"] = dene("varsayilan baglam",
                               ssl.create_default_context(), port)
    port = sunucu_baslat(cert_yol, anah_yol)
    tehlikeli = ssl.create_default_context()
    tehlikeli.check_hostname = False
    tehlikeli.verify_mode = ssl.CERT_NONE
    sonuc["kapali"] = dene("dogrulama kapali (TEHLIKELI)",
                           tehlikeli, port)
    port = sunucu_baslat(cert_yol, anah_yol)
    dogru = ssl.create_default_context(cafile=cert_yol)
    sonuc["kok"] = dene("sertifika guvenilen kok olarak", dogru, port)
    return sonuc

```

Burada iki önemli şey olur. Varsayılan bağlam, kendinden imzalı sertifikayı güvenilen bir kök olmadığı için reddeder. Bunu "tehlikeli" bağlam kabul eder; çünkü doğrulamayı kapatmıştır. Üçüncü bağlam ise sertifikayı açıkça güvenilen kök olarak verir; bu, özel bir CA kullanan kurumsal ve savunma sistemlerinin doğru yoludur.

```term
$ python b32_5_tls.py yerel
varsayilan baglam                  RED    (self-signed certificate)
dogrulama kapali (TEHLIKELI)       KABUL  (surum TLSv1.3)
sertifika guvenilen kok olarak     KABUL  (surum TLSv1.3)
```

::: ipucu
Bir İHA sisteminde yer istasyonu ile uçak arasındaki TLS sertifikası çoğunlukla özel bir CA'dan gelir. Doğru yöntem, o CA'nın kök sertifikasını yalnızca bu uygulamanın güven deposuna eklemektir; sistem genelindeki deponu değiştirmek ya da doğrulamayı kapatmak değil. Böylece yalnızca bu CA'nın imzaladığı sertifikalar kabul edilir.
:::

### verify=False neden tehlikelidir?

Üçüncü satırdaki "dogrulama kapali" bağlamı, sertifika zincirini, geçerlilik tarihini ve isim eşleşmesini tamamen atlar. Sonuç, TLS'in kimlik kısmının yok olmasıdır. İstemci, kendisine kim sunulursa sunulsun bağlanır. Bir ağ yolunda duran biri, kendi sertifikasını sunarak trafiği okuyabilir ve değiştirebilir; bu saldırıya **ortada adam** (man in the middle) denir. Yani `verify=False` ile HTTPS'in yalnızca şifreleme kısmı kalır ve güvenin tek dayanağı olan kimlik doğrulama kaybolur.

Bu hatayı yapanlar genellikle "sadece geliştirme sırasında" niyetiyle yazar ve bu kod bir sonraki sürüme sızar. Kural: doğrulamayı kapatan bir satır gördüğünde, bunun neden orada olduğunu ve neden kaldırılamadığını yazılı olarak açıklamadan kabul etme. Yerel test sertifikası sorununu çözmenin doğru yolu, o sertifikayı açıkça güvenilir kök olarak eklemektir.

Şimdi aynı yapılandırmayı gerçek bir sunucuda, yalnızca okuma amacıyla deneyelim. `example.com` sunucusuna tek bir TLS el sıkışması yapılır, sertifikanın alanları okunur ve bağlantı kapatılır. Uygulama verisi gönderilmez.

```term
$ python b32_5_tls.py ornek
host         : example.com
TLS surumu   : TLSv1.3
sifre paketi : TLS_AES_256_GCM_SHA384
konu (CN)    : example.com
veren (CN)  : Cloudflare TLS Issuing ECC CA 3
gecerlilik   : Sep 26 22:49:11 2026 GMT -> Dec 25 22:56:35 2026 GMT
SAN (ilk 3)  : example.com, *.example.com (toplam 2)
```

Çıktıda TLS sürümünü (TLSv1.3), şifre paketini ve sertifika zincirinin yaprağını (konu) ile veren kuruluşu görürsün. Veren, bir ara CA'dır; bu, zincirin en az iki halkalı olduğunu gösterir. Sertifika tarihleri zamanla değişir, bu yüzden çıktın bu bölümdekinden farklı olabilir; önemli olan alanların anlamıdır.

## 32.5 Bellek güvenliği: C'de hata sınıfları

C'de bellek güvenliği dilin değil, programcının sorumluluğundadır. Derleyici bir dizinin sınırını, serbest bırakılmış bir belleğin hâlâ kullanılıp kullanılmadığını ya da bir tamsayının taşıp taşmadığını çoğu durumda denetlemez. Bunların bir kısmı **tanımsız davranıştır** (undefined behavior, UB): standart ne olacağını söylemez, sonuç derleyiciye, optimizasyon düzeyine ve mimariye göre değişir. Bölüm 2.6'da tampon sınırını ve Bölüm 8'de yığın çerçevesini gördük; burada bu tekil hataların güvenlik açısından ne anlama geldiğini ve nasıl yakalanacağını öğreniyoruz.

Bu bölümün en önemli ilkesi burada da geçerlidir: bir hatayı düzeltmek için önce onu **görünür kılmak** gerekir. Bu yüzden her hata sınıfı için üç şey yapacağız: hatalı küçük bir program yazacağız, bir sanitizer ile hatanın raporunu alacağız ve düzeltilmiş sürümü aynı sanitizer ile doğrulayacağız. Aşağıdaki tablo sınıfları, nedenlerini ve tespit araçlarını özetler.

| Hata sınıfı | Neden oluşur | Tespit | Önleme |
|---|---|---|---|
| Tampon taşması | Yazma sınırı denetlenmez | ASan, `-Wall`, `-fanalyzer` | Sınırlı API, boyut denetimi |
| Serbest bırakılmış belleği kullanma | Yaşam süresi karışır | ASan, `-fanalyzer` | Sahipliği tek noktada tut, NULL'la |
| Çift serbest bırakma | Sahiplik belirsizdir | ASan, `-fanalyzer` | Sahiplik kuralı, `free` sonrası NULL |
| Tamsayı taşması | Boyut hesabı taşar | UBSan (işaretli), derleyici | `__builtin_mul_overflow` |
| Biçim dizesi | Girdi biçim dizesi olarak kullanılır | `-Wformat-security` | Sabit biçim dizesi |
| Sınır dışı okuma | Uzunluk alanına körü körüne güvenilir | ASan | Uzunluğu üst sınırla denetle |

![Şekil 32.8: Bellek hata sınıfları ve bunları yakalayan araçlar. Her sınıfın yanındaki araç, hatayı çalışma zamanında ya da derleme zamanında gösterebilir.](gorseller/b32_bellek.png)

::: not
Bu bölümdeki sanitizer raporları WSL2 içindeki Ubuntu 24.04 ve gcc 13.3.0 ile alındı. Windows'taki MSVC da bir ASan desteği sunar, ama rapor biçimi ve kapsamı farklıdır. ASan raporlarındaki adresler her çalıştırmada değişir; önemli olan rapordaki işaretçi, boyut ve kaynak satırı bilgileridir.
:::

### Tampon taşması

`strcpy` hedefin boyutunu bilmez; kaynağı sonuna kadar kopyalar. Aşağıdaki fonksiyonda 16 baytlık bir yerel dizi var, ama girdinin uzunluğu sınırsız. 40 karakterlik bir girdi, yığında tamponun komşusundaki belleğe taşar. Yığında bu komşuluk, bir fonksiyonun yerel değişkenleri ile çağrı bilgileri (dönüş adresi dahil) arasında olabilir. Bölüm 8'de gördüğün yığın çerçevesi bunu açıklar. Burada önemli olan şudur: taşan yazma, tamponun dışındaki bir değeri değiştirir ve bu değer programın davranışını belirler.

```c
/* b32_c1_hatali.c: yigin tamponu tasmasi (sinirsiz kopya).
 * Derleme (ASan): gcc -g -O0 -fno-omit-frame-pointer \
 *                 -fsanitize=address -Wall -Wextra -std=c11 \
 *                 b32_c1_hatali.c -o b32_c1_hatali
 */
#include <stdio.h>
#include <string.h>

static void ad_yaz(const char *girdi)
{
    char ad[16];
    strcpy(ad, girdi);            /* sinir denetimi yok */
    printf("merhaba, %s\n", ad);
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "kullanim: %s METIN\n", argv[0]);
        return 2;
    }
    ad_yaz(argv[1]);
    return 0;
}
```

Kodu derleyip ASan ile çalıştırıyoruz. Girdi olarak 40 karakterlik bir dizi veriyoruz; program bir hata raporu basıp durur.

```term
$ ./c1a AAAA...A (40 karakter)
==375==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x735ec1e
00030 at pc 0x735ec42a7923 bp 0x7ffe474a0f70 sp 0x7ffe474a0718
WRITE of size 41 at 0x735ec1e00030 thread T0
    #0 0x735ec42a7922 in strcpy ../../../../src/libsanitizer/asan/asan_int
erceptors.cpp:563
    #1 0x5e07490d530c in ad_yaz b32_c1_hatali.c:12
    #2 0x5e07490d5439 in main b32_c1_hatali.c:22
```

Raporu okumayı öğren. İkinci satır hatanın türünü söyler: `stack-buffer-overflow`, yani yığın tamponunun taşması. Üçüncü satır yazmanın boyutunu (41 bayt, sonlandırıcı NUL dahil) ve adresi verir. Dördüncü ve beşinci satırlar hatayı üreten çağrının `strcpy` olduğunu ve kaynak satırının `b32_c1_hatali.c:12` olduğunu gösterir. Rapordaki "located in stack ... offset 48" bilgisi, tamponun yığında olduğunu ve taşmanın komşu alana değdiğini söyler.

Düzeltme, sınırı kopyalama işleminin içine koymaktır. `snprintf` en fazla `sizeof(ad)` baytı yazar ve sonunu NUL ile kapatır. Dönüş değeri, kesilmiş olsaydı yazılacak uzunluğu verir; bu değeri kullanarak kesilmeyi tespit edip girdiyi reddediyoruz. Kesmek yerine reddetmenin nedeni, kesilmiş bir yolun ya da kimliğin anlamının sessizce değişmesini önlemektir.

```c
/* b32_c1_duzeltilmis.c: tampon tasmasinin sinirli kopya ile
 * onlenmesi.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 b32_c1_duzeltilmis.c \
 *          -o b32_c1_duzeltilmis
 */
#include <stdio.h>

static int ad_yaz(const char *girdi)
{
    char ad[16];
    /* snprintf en fazla sizeof(ad)-1 karakter yazar ve sonunu NUL ile
     * kapatir. Donus degeri, kesilmis olsaydi yazilacak uzunluk. */
    int n = snprintf(ad, sizeof ad, "%s", girdi);
    if (n < 0 || (size_t)n >= sizeof ad) {
        fprintf(stderr, "ad cok uzun (en fazla %zu karakter)\n",
                sizeof ad - 1);
        return -1;                /* kesmek yerine reddet */
    }
    printf("merhaba, %s\n", ad);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "kullanim: %s METIN\n", argv[0]);
        return 2;
    }
    return ad_yaz(argv[1]) == 0 ? 0 : 1;
}
```

Düzeltilmiş sürümü aynı 40 karakterle ve kısa bir girdiyle çalıştıralım. İlki reddedilir, ikincisi normal çalışır.

```term
$ ./c1d AAAA...A; ./c1d ali
cikis=1
merhaba, ali
cikis=0
```

Dikkat edilmesi gereken bir tuzak daha var: `strncpy` hedefi sonlandırmaz ve hedef dolduğunda NUL eklemez. `strncpy` ile kopyalanan bir dizinin `strlen` ile okunması, yine bir taşmaya yol açabilir. Güvenli kopyada sonlandırıcının hesaba katıldığını her zaman kontrol et.

### Serbest bırakılmış belleği kullanma (use-after-free)

Bir işaretçi `free` ile belleği serbest bıraktıktan sonra hâlâ o adresi gösterir. Bu işaretçi üzerinden okuma ya da yazma tanımsız davranıştır. Bellek hemen değişmediği için program çoğu zaman "çalışmış" gibi görünür; bu şans, hatanın testlerde görünmemesinin en yaygın nedenidir.

```c
/* b32_c2_hatali.c: serbest birakilmis bellegi kullanma
 * (use-after-free).
 * Derleme (ASan): gcc -g -O0 -fsanitize=address -Wall -Wextra
 *                 -std=c11 b32_c2_hatali.c -o b32_c2_hatali
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct sensor {
    int id;
    char etiket[16];
};

int main(void)
{
    struct sensor *s = malloc(sizeof *s);
    if (s == NULL)
        return 1;
    s->id = 7;
    strcpy(s->etiket, "GPS");
    free(s);
    printf("id=%d\n", s->id);     /* HATA: bellek artik serbest */
    return 0;
}
```

ASan, serbest bırakılan bellek bölgesini özel olarak işaretler ve erişimi yakalar. Raporda üç bilgi aranır: hatanın türü (`heap-use-after-free`), erişimin türü (`READ`) ve belleğin nerede serbest bırakıldığı.

```term
$ ./c2h
==399==ERROR: AddressSanitizer: heap-use-after-free on address 0x503000000
040 at pc 0x6209ab24e337 bp 0x7ffee9be5020 sp 0x7ffee9be5010
READ of size 4 at 0x503000000040 thread T0
    #0 0x6209ab24e336 in main b32_c2_hatali.c:23
```

Düzeltmede iki kural uygulanır. Birincisi, serbest bırakmadan önce gereken değer okunur. İkincisi, işaretçi serbest bırakıldıktan sonra NULL yapılır; böylece yanlışlıkla kullanılırsa bir sonraki erişim NULL işaretçi hatası olarak hemen ortaya çıkar. Düzeltilmiş sürümde ASan'ın sessiz kaldığını da göreceksin.

```c
/* b32_c2_duzeltilmis.c: deger serbest birakmadan once okunur;
 * isaretci serbest birakildiktan sonra NULL yapilir.
 * Derleme: gcc -g -O0 -fsanitize=address -Wall -Wextra -std=c11 \
 *          b32_c2_duzeltilmis.c -o b32_c2_duzeltilmis
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct sensor {
    int id;
    char etiket[16];
};

int main(void)
{
    struct sensor *s = malloc(sizeof *s);
    if (s == NULL)
        return 1;
    s->id = 7;
    strcpy(s->etiket, "GPS");
    int id = s->id;               /* serbest birakmadan once oku */
    free(s);
    s = NULL;                     /* artik kullanilmayacak */
    printf("id=%d\n", id);
    return 0;
}
```

```term
$ ./c2d
id=7
cikis=0
```

### Çift serbest bırakma (double free)

Aynı bellek bloğunu iki kez `free` etmek, allocator'ın iç veri yapısını bozar. Bu hata bazen çökmeye, bazen sessiz bellek bozulmasına yol açar. Sorun çoğunlukla sahipliğin belirsiz olmasından doğar: iki fonksiyon da belleği serbest bırakmayı kendisinin görevi sanır.

```c
/* b32_c3_hatali.c: ayni bellegi iki kez serbest birakma
 * (double free).
 * Derleme (ASan): gcc -g -O0 -fsanitize=address -Wall -Wextra
 *                 -std=c11 b32_c3_hatali.c -o b32_c3_hatali
 */
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static void tampon_bosalt(char *p)
{
    free(p);
}

int main(void)
{
    char *p = malloc(32);
    if (p == NULL)
        return 1;
    strcpy(p, "veri");
    tampon_bosalt(p);
    tampon_bosalt(p);             /* HATA: ikinci free */
    puts("bitti");
    return 0;
}
```

```term
$ ./c3h
==421==ERROR: AddressSanitizer: attempting double-free on 0x503000000040 i
n thread T0:
    #0 0x7587818fc4d8 in free ../../../../src/libsanitizer/asan/asan_mallo
c_linux.cpp:52
```

Düzeltmenin kuralı şudur: belleği serbest bırakan fonksiyon, işaretçiyi de NULL yapar. `free(NULL)` tanımlıdır ve hiçbir şey yapmaz; yani ikinci çağrı zararsız olur. Bu bir kalıp değil, sahiplik tasarımının sonucudur: belleği kimin serbest bıraktığını tek bir yerde bil.

```c
/* b32_c3_duzeltilmis.c: sahiplik tek noktada; serbest birakan kod
 * isaretciyi NULL yapar. free(NULL) tanimlidir ve hicbir sey yapmaz.
 * Derleme: gcc -g -O0 -fsanitize=address -Wall -Wextra -std=c11 \
 *          b32_c3_duzeltilmis.c -o b32_c3_duzeltilmis
 */
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static void tampon_bosalt(char **p)
{
    free(*p);
    *p = NULL;
}

int main(void)
{
    char *p = malloc(32);
    if (p == NULL)
        return 1;
    strcpy(p, "veri");
    tampon_bosalt(&p);
    tampon_bosalt(&p);            /* ikinci cagri zararsiz */
    puts("bitti");
    return 0;
}
```

```term
$ ./c3d
bitti
cikis=0
```

### Tamsayı taşması ve yanlış boyut

Bir dizi için bellek ayırırken genellikle `eleman_sayisi * sizeof(eleman)` hesaplanır. Bu çarpım, işaretli bir tamsayıda taşabilir. İşaretli tamsayı taşması tanımsız davranıştır; sonuç derleyiciye göre değişir. İşaretsiz tamsayılarda taşma tanımlıdır (modüler aritmetik), ama bu sonucun doğru olduğu anlamına gelmez: taşan çarpım küçük bir boyut verir ve sonraki döngü, ayrılan alanın çok ötesine yazar.

Aşağıdaki programda `n * 4` hesabı `int` ile yapılıyor. `n = 1073741825` (2^30 + 1) için matematiksel çarpım 4294967300'dür ve 32 bitlik `int` bunu taşırır. UBSan bu taşmayı işaretler; ASan ise taşan `malloc` boyutu yüzünden oluşan yazma hatasını gösterir.

```c
/* b32_c4_hatali.c: tamsayi tasmasi, yanlis malloc boyutu.
 * int n*4 hesabi tasar; malloc kucuk bir blok verir; dongu
 * ayrilan bellegin disina yazar.
 * Derleme: gcc -g -O0 -fsanitize=address,undefined -Wall -Wextra \
 *          -std=c11 b32_c4_hatali.c -o b32_c4_hatali
 */
#include <stdio.h>
#include <stdlib.h>

static int *dizi_olustur(int n)
{
    int bayt = n * (int)sizeof(int);     /* int tasmasi (UB) */
    int *d = malloc((size_t)bayt);
    if (d == NULL)
        return NULL;
    for (int i = 0; i < n; i++)
        d[i] = i;                        /* ayrilan alanin disina */
    return d;
}

int main(int argc, char **argv)
{
    if (argc != 2)
        return 2;
    int n = atoi(argv[1]);
    int *d = dizi_olustur(n);
    if (d == NULL)
        return 1;
    printf("d[0]=%d\n", d[0]);
    free(d);
    return 0;
}
```

```term
$ ./c4h 1073741825
b32_c4_hatali.c:12:9: runtime error: signed integer overflow: 1073741825 *
 4 cannot be represented in type 'int'
=================================================================
==443==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x50200000
0014 at pc 0x61fea3d2d432 bp 0x7ffc8fe974c0 sp 0x7ffc8fe974b0
```

Raporun ilk satırı UBSan'dan gelir; taşan işlemi, değerleri ve türü söyler. Sonraki satırlar ASan'dan gelir: `heap-buffer-overflow` ve `WRITE of size 4`, yani ayrılan alanın dışına 4 baytlık bir yazma. Düzeltme boyut hesabını `size_t` üzerinde yapar ve `__builtin_mul_overflow` ile taşmayı hesap anında tespit eder. Taşma varsa ayırma yapılmaz.

```c
/* b32_c4_duzeltilmis.c: boyut hesabi tasma denetimli yapilir.
 * __builtin_mul_overflow tasma olursa 1 dondurur (GCC ve Clang).
 * Derleme: gcc -g -O0 -fsanitize=address,undefined -Wall -Wextra \
 *          -std=c11 b32_c4_duzeltilmis.c -o b32_c4_duzeltilmis
 */
#include <stdio.h>
#include <stdlib.h>

static int *dizi_olustur(size_t n)
{
    size_t bayt;
    if (__builtin_mul_overflow(n, sizeof(int), &bayt))
        return NULL;                     /* hesap tasti: reddet */
    int *d = malloc(bayt);
    if (d == NULL)
        return NULL;
    for (size_t i = 0; i < n; i++)
        d[i] = (int)i;
    return d;
}

int main(int argc, char **argv)
{
    if (argc != 2)
        return 2;
    char *son;
    unsigned long v = strtoul(argv[1], &son, 10);
    if (*son != '\0' || v == 0)
        return 2;
    int *d = dizi_olustur((size_t)v);
    if (d == NULL) {
        fprintf(stderr, "boyut kabul edilemez\n");
        return 1;
    }
    printf("d[0]=%d\n", d[0]);
    free(d);
    return 0;
}
```

Düzeltilmiş sürümü iki girdiyle deneyelim: taşacak kadar büyük bir değer ve normal bir değer.

```term
$ ./c4d 4611686018427387904; ./c4d 16
cikis=1
d[0]=0
cikis=0
```

### Biçim dizesi (format string)

`printf` ailesinin ilk argümanı bir biçim dizesidir. Girdi bir biçim dizesi olarak kullanılırsa, saldırganın belirlediği `%` dizileri, programın beklemediği argümanları okumaya ya da yazmaya yol açabilir. Derleyici bu hatayı bazı durumlarda uyarır; uyarıyı kapatmamak ilk savunmadır.

```c
/* b32_c5_hatali.c: kullanici girdisi bicim dizesi olarak
 * kullaniliyor.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 b32_c5_hatali.c
 *          -o b32_c5_hatali
 */
#include <stdio.h>

int main(int argc, char **argv)
{
    if (argc != 2)
        return 2;
    printf(argv[1]);                     /* girdi = biçim dizesi */
    printf("\n");
    return 0;
}
```

```term
$ gcc -O2 -Wall -Wextra ... b32_c5_hatali.c
b32_c5_hatali.c: In function ‘main’:
b32_c5_hatali.c:12:5: warning: format not a string literal and no format a
rguments [-Wformat-security]
   12 |     printf(argv[1]);                     /* girdi = biçim dizesi
*/
      |     ^~~~~~
```

Uyarı, girdinin bir biçim dizesi olarak kullanıldığını söyler. Düzeltme basittir: girdi her zaman bir argüman olarak verilir ve biçim dizesi sabit bir değerdir. Biçim dizesi hatasının asıl tehlikesi, `%n` gibi yazma yapan dizilerin de kullanılabilmesidir; bu bölümde bu tekniği göstermiyoruz, yalnızca hatayı ve düzeltmeyi gösteriyoruz.

```c
/* b32_c5_duzeltilmis.c: girdi her zaman bir argumana verilir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 b32_c5_duzeltilmis.c \
 *          -o b32_c5_duzeltilmis
 */
#include <stdio.h>

int main(int argc, char **argv)
{
    if (argc != 2)
        return 2;
    printf("%s\n", argv[1]);           /* girdi veri olarak */
    return 0;
}
```

```term
$ ./c5d "yuzde %% isareti"
yuzde %% isareti
yuzde % isareti
```

### Tanımsız davranışı doğru adlandırmak

Bu dört sınıfın ortak noktası, programın hata verdiğini bildirmemesidir. Bu yüzden testlerin geçmesi güvenlik kanıtı değildir. Üç araç yaygın olarak kullanılır. **ASan** (AddressSanitizer), bellek erişimlerini izleyerek sınır dışı ve serbest bırakılmış bellek erişimlerini yakalar. **UBSan** (UndefinedBehaviorSanitizer), taşma gibi tanımsız işlemleri çalışma zamanında işaretler. **`-fanalyzer`**, derleyicinin statik analiz motorudur; hatayı çalıştırmadan, kod yolları üzerinde arar. Bunu 32.8'de kullanacağız.

Sanitizer'lar hızı ve bellek kullanımını artırır; bu yüzden test ortamında kullanılır, üretimde kullanılmaz. Ayrıca bir sanitizer'ın raporu yalnızca çalıştırılan yolu kapsar: bir hata, test etmediğin bir girdide kalabilir. Bu yüzden fuzzing (32.8) ve sanitizer birlikte kullanılır.

::: baglanti
Bölüm 23'te kod kalitesi ve statik analiz araçlarından söz etmiştik. `-fanalyzer` de aynı ailedendir; farkı, yalnızca biçimi değil yol boyunca bellek durumunu izlemesidir.
:::

### Bellek güvenli diller

Rust gibi diller, sahiplik (ownership) ve ödünç alma (borrow) kurallarını derleme zamanında denetler. Güvenli Rust kodunda serbest bırakılmış belleğe erişim ve veri yarışı derlenmez. Bu, bu sınıftaki hataların dilin kendisi tarafından önlenmesi demektir. Bununla birlikte `unsafe` blokları ve C kütüphaneleriyle çağrı (FFI) sınırı, güvenlik sorumluluğunu yeniden programcıya bırakır. Bu kitapta C'de kalmamızın nedeni, gömülü sistemlerde (Kısım XI) ve işletim sistemlerinde (Kısım VI) C'nin hâlâ baskın olmasıdır; kavramlar ortaktır.

## 32.6 Derinlemesine savunma: derleyici ve işletim sistemi korumaları

Hataları önlemek birinci savunmadır; ama hiçbir büyük yazılımda tüm hataların önlenebileceğini varsaymamak gerekir. **Derinlemesine savunma** (Şekil 32.2) burada devreye girer: derleyici ve işletim sistemi, hatanın kötüye kullanılmasını zorlaştıran katmanlar koyar. Bu katmanlar bir hatayı **düzeltmez**; yalnızca bedelini artırır. Bu farkı akılda tut: bir koruma açıldığında hata hâlâ oradadır.

| Koruma | Ne yapar | Nasıl açılır (gcc / Linux) |
|---|---|---|
| Yığın kanaryası | Dönüş adresinden önce bir değer koyar; bozulursa programı durdurur | `-fstack-protector-strong` |
| FORTIFY | Boyutu bilinen tamponlarda kopya işlevlerini denetimli sürümüyle değiştirir | `-D_FORTIFY_SOURCE=2` (`-O` ile) |
| NX (DEP) | Veri bölgelerinin çalıştırılmasını engeller | Yığın için `GNU_STACK` bayrağı `RW` olmalı |
| ASLR | Bellek yerleşimini her çalıştırmada rastgeleleştirir | Çekirdek: `randomize_va_space` |
| PIE | Program kodunu da rastgele bir adrese yükler | `-pie` (Ubuntu varsayılanı) |
| RELRO / BIND_NOW | Dinamik bağlama tablosunu başlangıçtan sonra yazmaya kapatır | `-Wl,-z,relro -Wl,-z,now` |

Her koruma farklı bir aşamayı zorlaştırır. Yığın kanaryası, yığın üzerinden dönüş adresinin bozulmasını yakalar ve programı `stack smashing detected` mesajıyla durdurur. NX, veri bölgesine yerleştirilen bir kodun çalıştırılmasını engeller; bunu sağlayan, Bölüm 25'te gördüğün sayfa tablosu bitidir. ASLR, kod ve yığın adreslerini tahmin edilemez kılar. PIE, ikili kodunu da bu rastgeleleştirmeye dahil eder. RELRO, dinamik bağlama tablolarını başlangıçtan sonra salt okunur yapar.

![Şekil 32.9: Korumalar bir saldırının farklı aşamalarını zorlaştırır. Hiçbiri tek başına yeterli değildir; hatanın kendisi düzeltildiğinde ve birlikte kullanıldıklarında anlam kazanırlar.](gorseller/b32_koruma.png)

Önce bir ikilinin hangi korumalara sahip olduğunu denetleyen küçük bir araç yazıyoruz. Bu araç yalnızca `readelf` çıktısını okur; ikiliyi çalıştırmaz. Bir ikilinin başlık bilgilerini okumak, gerçek bir güvenlik denetiminin ilk adımıdır: sürümünün beklenen korumalara sahip olup olmadığını bilmek istersin.

```python
def readelf(bayrak, yol):
    cikti = subprocess.run(["readelf", bayrak, yol],
                           capture_output=True, text=True)
    return cikti.stdout


def denetle(yol):
    prog = readelf("-lW", yol)
    baslik = readelf("-hW", yol)
    dinamik = readelf("-dW", yol)
    semb = readelf("-sW", yol)
    sonuc = {}
    # GNU_STACK satirinin bayrak alani sondan ikinci sutundadir
    for satir in prog.splitlines():
        if "GNU_STACK" in satir:
            bayrak = satir.split()[-2]
            sonuc["NX (yigin calistirilamaz)"] = "E" not in bayrak
            sonuc["yigin bayragi"] = bayrak
    sonuc["PIE (DYN tipi)"] = "Type:" in baslik and "DYN" in baslik
    sonuc["RELRO (bolum)"] = "GNU_RELRO" in prog
    sonuc["BIND_NOW (tam RELRO)"] = bool(
        re.search(r"\bBIND_NOW\b|Flags: .*\bNOW\b", dinamik))
    sonuc["yigin kanarisi"] = "__stack_chk_fail" in semb
    sonuc["FORTIFY (__*_chk)"] = bool(
        re.search(r"\b__\w+_chk\b", semb))
    return sonuc

```

Denetçiyi iki ikili üzerinde çalıştırıyoruz. Birincisi Ubuntu'nun varsayılan ayarlarıyla, ikincisi bilinçli olarak korumaları kapatarak derlenmiş. Bu karşılaştırma, hangi bayrağın hangi korumayı açtığını gösterir.

```term
$ python3 b32_korumalar.py ./k_varsayilan ./k_zayif
== ./k_varsayilan
  NX (yigin calistirilamaz)  VAR
  yigin bayragi              RW
  PIE (DYN tipi)             VAR
  RELRO (bolum)              VAR
  BIND_NOW (tam RELRO)       VAR
  yigin kanarisi             VAR
  FORTIFY (__*_chk)          VAR
== ./k_zayif
  NX (yigin calistirilamaz)  YOK
  yigin bayragi              RWE
  PIE (DYN tipi)             YOK
  RELRO (bolum)              YOK
  BIND_NOW (tam RELRO)       YOK
  yigin kanarisi             YOK
  FORTIFY (__*_chk)          YOK
```

Zayıf ikilide NX "YOK" olarak görünür ve yığın bayrağı `RWE` (yazılabilir ve çalıştırılabilir) çıkar; bu, yığının çalıştırılmasına izin verir. Bu bayrağı yalnızca bu deneyde bilerek açtık: gerçek bir ürünün bu bayrakla derlenmesi ciddi bir hatadır. Şimdi korumaların davranışını tek tek görelim. Önce yalnızca yığın kanaryasını açık bırakıp FORTIFY'yi kapatalım; böylece kanaryanın mesajı görünür.

```term
$ ./k_kanarili AAAA...A (40 karakter)
cikis=134
```

Mesaj `*** stack smashing detected ***` ve program çıkış kodu 134 (SIGABRT) ile sonlanır. Kanaryanın yaptığı iş budur: taşmayı fark eder ve kontrolü, bozulmuş bir dönüş adresinden önce durdurur. Aynı hatayı FORTIFY açıkken derlediğimizde farklı bir mesaj görürüz; çünkü `strcpy` çağrısı denetimli sürümle değiştirilmiştir ve kanaryaya ulaşılmadan program durur.

```term
$ ./k_varsayilan AAAA...A (40 karakter)
cikis=134
```

Son olarak, bütün korumaları kapatılmış ikiliyi aynı girdiyle çalıştırıyoruz. Program kontrolsüz biçimde çöker (segmentation fault, çıkış kodu 139). Bu, koruma olmadığında hatanın nasıl davrandığının somut bir örneğidir: program çöker. Çöküş bir kayıptır, ama en kötüsü değildir; sessiz kalmış bir bozulma çok daha tehlikelidir.

```term
$ ./k_zayif AAAA...A (40 karakter)
cikis=139
```

ASLR'nin etkisini kendi programımızda görelim. Aşağıdaki program yığın değişkeninin, bir fonksiyonun ve heap bloğunun adreslerini yazdırır. Üç çalıştırmada değerler değişir; ASLR'yi `setarch -R` ile kapattığımızda ise her çalıştırmada aynı kalır.

```c
/* b32_c7_aslr.c: adres uzayi yerlesiminin calistirmalar arasindaki
 * degisimini gosterir. Yalnizca kendi adreslerimizi yazdiriyoruz.
 * Derleme: gcc -O0 -Wall -Wextra -std=c11 b32_c7_aslr.c
 *          -o b32_c7_aslr
 */
#include <stdio.h>
#include <stdlib.h>

static void islev(void) { }

int main(void)
{
    int yerel = 0;
    int *yigin = &yerel;
    int *yigin_tam = malloc(sizeof *yigin_tam);
    printf("yigin=%p yigin-kod=%p heap=%p\n",
           (void *)yigin, (void *)islev, (void *)yigin_tam);
    free(yigin_tam);
    return 0;
}
```

```term
$ ./c7 (3 kez) ve setarch x86_64 -R ./c7 (2 kez)
yigin=0x7ffc792fd874 yigin-kod=0x5fc99c4951a9 heap=0x5fc9aac242a0
yigin=0x7ffec4121954 yigin-kod=0x624790ea21a9 heap=0x6247c9eee2a0
yigin=0x7ffe39996ad4 yigin-kod=0x5f399bf961a9 heap=0x5f39c4dd32a0
-- setarch -R:
yigin=0x7fffffffe0f4 yigin-kod=0x5555555551a9 heap=0x5555555592a0
yigin=0x7fffffffe0f4 yigin-kod=0x5555555551a9 heap=0x5555555592a0
```

Çıktıda sistemin ASLR değeri 2'dir (tam rastgeleleştirme) ve yığın, kod ve heap adresleri her çalıştırmada değişir. `setarch -R` ile yapılan çalıştırmalarda adresler sabittir. Bu fark, ASLR'nin neyi değiştirdiğini ve neyi değiştirmediğini gösterir: adresleri değiştirir, ama bellekteki hatayı ortadan kaldırmaz. Bir sızıntı yoluyla adres öğrenilirse ASLR'nin değeri azalır; bu yüzden yalnızca ASLR'ye güvenmek yetmez.

FORTIFY'nin davranışını bilinen boyutlu bir tampon üzerinde görelim. Burada derleyici `memcpy`'nin hedef boyutunu bilir ve denetimli sürümü seçer.

```c
/* b32_c6_fortify.c: hedef boyutu derleme zamaninda bilinen tampona
 * kopya. _FORTIFY_SOURCE=2 ile -O2 altinda memcpy, __memcpy_chk'a
 * donusur; tasma tespit edilince program durdurulur.
 * Derleme: gcc -O2 -D_FORTIFY_SOURCE=2 -Wall -Wextra -std=c11 \
 *          b32_c6_fortify.c -o b32_c6_fortify
 */
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
    char hedef[8];
    if (argc != 2)
        return 2;
    size_t n = strlen(argv[1]) + 1;
    memcpy(hedef, argv[1], n);           /* n > 8 ise tasma */
    printf("kopyalandi: %s\n", hedef);
    return 0;
}
```

```term
$ ./c6 kisa; ./c6 "bu metin sekiz bayttan uzun"
kopyalandi: kisa
cikis=0
cikis=134
```

Kısa girdi normal kopyalanır. Uzun girdi `*** buffer overflow detected ***` mesajıyla durur. Bu koruma, boyutu derleme zamanında bilinen durumlarda çalışır; boyut çalışma zamanında belirliyse sınır denetimini sen yazmalısın. Korumaya güvenmek yerine sınırı açıkça kontrol etmek her zaman doğru yoldur.

Bir mimari notu: Cortex-M (STM32 gibi) ve ARM64 gibi ARM çekirdeklerinde, bir fonksiyon çağrıldığında dönüş adresi LR yazmacına konur. Yaprak olmayan bir fonksiyon, LR'yi çağrı yapmadan önce yığına kaydeder. Yani bir yığın taşması, bu kaydedilmiş değeri ezebilir. Derleyici korumaları ARM hedefleri için de vardır, ama her hedef ve derleyici sürümü için bunların açık olduğunu derleme çıktısından kontrol etmelisin. x86'da dönüş adresi `call` ile yığına yazılır; ARM'da ise bu yalnızca yaprak olmayan fonksiyonlarda yığına iner. Mimari farkları için Bölüm 1 ve Bölüm 24 iyi bir başlangıçtır.

::: dikkat
Üretim derlemesinde korumaları kapatmak için bir gerekçe yoktur. Yalnızca bir ikilinin korumalarını denetleyen bir adım ekle ve korumaları kaybeden her derlemenin hata sayılmasını sağla; bu adım CI'da başarısız olmalıdır.
:::

::: baglanti
Bölüm 24'te Meltdown ve Spectre'in azaltımlarının (KPTI gibi) çekirdek girişini nasıl pahalılaştırdığını gördün. Bellek korumaları ile spekülatif yürütme azaltımları aynı felsefeyi paylaşır: güvenlik, bir performans bedeli ile satın alınır.
:::

## 32.7 Girdi doğrulama ve enjeksiyon

Bölüm 31'de ağdan gelen her baytın düşman olabileceğini söyledik. Bu cümlenin pratik sonucu şudur: **güvenilmeyen girdi, kodun veri değil komut olarak yorumlanmasına izin vermemelidir**. Enjeksiyon saldırılarının tamamı tek bir hatadan doğar: veri ile komut, aynı metin içinde karışır ve hedef yorumlayıcı (kabuk, SQL motoru, tarayıcı, dosya sistemi) veriyi komut sanır.

Savunma üç adımdan oluşur ve bu sırayla düşünülmelidir. **Doğrula**: girdinin beklenen biçimde olup olmadığını kontrol et; mümkünse izin verilenleri listele (allowlist), yasaklılarını değil. **Ayır**: komutu ve veriyi ayrı kanallardan geçir (parametreli sorgu, argüman listesi). **Kaçır**: veri kaçınılmazsa, çıktı bağlamına uygun biçimde kaçır (HTML için HTML kaçışı, URL için URL kodlaması). Bu üç adımın birinin yerine diğerini koymak, çoğu zaman yetersiz kalır.

### Komut enjeksiyonu

Bir programın harici bir komutu çağırırken girdiyi kabuğa metin olarak verdiğini düşün. Kabuk, bu metni komut satırı gibi ayrıştırır; `&`, `;`, `|` gibi karakterler yeni komutlar başlatır. Python'da bu, `subprocess.run(..., shell=True)` ile olur. Girdi liste olarak verildiğinde ise kabuk devreye girmez ve girdi tek bir argüman olarak kalır.

Aşağıdaki deneyde girdi `merhaba & echo ENJEKTE` olarak verilir. Yazdırma komutu zararsızdır; amaç, ikinci bir komutun çalıştığını görmektir.

```python
def komut_liste(girdi):
    """Dogru: arguman listesi; kabuk yorumu yok."""
    s = subprocess.run([PY, "-c", YAZ, girdi],
                       capture_output=True, text=True)
    return s.stdout.strip()


def komut_kabuk(girdi):
    """YANLIS: girdi kabuk komutunun parcasi olur."""
    s = subprocess.run('"%s" -c "%s" %s' % (PY, YAZ, girdi),
                       shell=True, capture_output=True, text=True)
    return s.stdout.strip().splitlines()
```

```term
$ python b32_girdi.py komut
liste biciminde: merhaba & echo ENJEKTE
shell=True    : ['merhaba', 'ENJEKTE']
```

Çıktı farkı net gösterir. Liste biçiminde `&` ve `echo` karakterleri düz metin olarak yazdırılır. `shell=True` ile çalıştırıldığında ise ikinci komut ayrı bir çıktı olarak çalışır: `ENJEKTE` yazısı, girdinin komut olarak yorumlandığının kanıtıdır. Kural: harici bir program çağırırken her zaman argüman listesi kullan, kabuğu hiçbir koşulda girdi işleme aracı olarak kullanma.

::: ipucu
Kabuk gerçekten gerekirse, POSIX sistemlerde `shlex.quote` ile her argümanı tek tırnağa alabilirsin. Windows'ta kabuk (`cmd`) farklı tırnak kurallarına sahiptir; bu yüzden orada en güvenli yol yine argüman listesidir.
:::

### Yol geçişi (path traversal)

Kullanıcının verdiği bir dosya adını bir kök dizinin altına eklemek, bir saldırganın `../` dizilerini kullanarak kök dizinin dışına çıkmasına izin verebilir. Bu, Bölüm 30'daki HTTP sunucusunda da tam olarak bu riskti. Yol normalleştirme (`normpath`) tek başına yeterli değildir: sembolik bağlar, Windows sürücü harfleri ve NUL baytı gibi durumlar ayrı ele alınmalıdır.

Sağlam yaklaşım üç adımdır. Önce yolu, sembolik bağları çözen `realpath` ile gerçek bir yola çevir. Sonra kök dizinin de gerçek yolunu al. Son olarak `commonpath` ile sonucun kök dizinin altında olduğunu doğrula. `commonpath` farklı sürücüler için bir hata fırlattığından, bunu da yakalamalısın.

```python
def guvenli_yol(kok, istek):
    """Istegi kok dizin altina cozer; kokten cikarsa None doner."""
    if "\x00" in istek:
        return None                       # NUL baytli yol
    kok_gercek = os.path.realpath(kok)    # sembolik baglari da cozer
    aday = os.path.realpath(
        os.path.join(kok_gercek, istek.lstrip("/\\")))
    try:
        ortak = os.path.commonpath([kok_gercek, aday])
    except ValueError:                    # farkli surucu (C: ve D:)
        return None
    if ortak != kok_gercek:
        return None
    return aday


def yol_naif(kok, istek):
    """YANLIS: yalnizca birlestirir; sonuc kokten cikabilir."""
    return os.path.normpath(os.path.join(kok, istek.lstrip("/")))
```

Üç yolu karşılaştıran tablo, naif birleştirmenin nerede kırıldığını gösterir. Deneyde kök dizini geçici bir klasördür.

```term
$ python b32_girdi.py yol
istek                  naif       guvenli (kokte mi?)
'a.txt'                kokte      kabul
'alt/b.txt'            kokte      kabul
'../gizli.txt'         KOKTEN     red
'/../gizli.txt'        KOKTEN     red
'..\\gizli.txt'        KOKTEN     red
'C:\\Windows\\win.ini' KOKTEN     red
'a\x00b.txt'           kokte      red
```

Naif sütunda `KOKTEN` yazan satırlar, dosyanın kök dizinin dışına çıkacağı anlamına gelir. Güvenli sütun bu durumları reddeder. NUL baytı içeren yolun naif sürümde kök içinde kaldığına dikkat et: bu, güvenlik için yeterli değildir; NUL baytını ayrıca reddetmek, dosya sistemi API'lerinin farklı davranışlarından doğan belirsizliği önler.

Sembolik bağ senaryosunu Windows'ta bu deneyde üretemedik (bağ oluşturmak yönetici hakkı ister). Kavramsal olarak şöyledir: kök dizinin içinde görünen bir bağ, dışarıdaki bir dosyaya işaret edebilir. `normpath` bağı çözmez, bu yüzden kök kontrolünü geçer; `realpath` ise bağı çözer ve kontrol bunu yakalar. Bölüm 32.8'de düzelttiğimiz sunucu bu ayrımı kullanır.

### HTML kaçışı ve çapraz site betiği (XSS)

Bir web sayfasına kullanıcı verisi yazılırken, veri HTML olarak yorumlanırsa, veri içindeki `<script>` etiketi çalışır. Buna **çapraz site betiği** (cross-site scripting, XSS) denir. Çözüm, çıktı bağlamına uygun kaçıştır: HTML metni için `<`, `>`, `&`, `"` ve `'` karakterleri karşılık gelen varlıklara çevrilir. `html.escape` bu iş için yeterlidir; `quote=True` ile tırnaklar da kaçırılır, böylece öznitelik değerleri içinde de güvenlidir.

```python
def html_sayfa(ad):
    return "<p>Merhaba, %s</p>" % html.escape(ad, quote=True)
```

```term
$ python b32_girdi.py html
<p>Merhaba, &lt;script&gt;alert(1)&lt;/script&gt;</p>
<p>Merhaba, Ayse &amp; Ali</p>
```

Kaçışın bağlama özgü olduğunu unutma. Bir JavaScript bloğunun içine ya da bir URL'nin içine yazılan veri için HTML kaçışı yetmez; her bağlamın kendi kodlaması vardır. Ek olarak İçerik Güvenlik Politikası (CSP) gibi tarayıcı katmanı savunmaları, XSS'in etkisini sınırlar (genel bilgi).

### SQL enjeksiyonu

SQL enjeksiyonu, sorgunun metin birleştirmeyle kurulmasından doğar ve kendi bölümünde ayrıntılı işlendi (bkz. Bölüm 34, SQL enjeksiyonu anlatımı). Burada tek kural yeter: değer her zaman **parametre** olarak bağlanır; sorgu metni ise sabit olur. Tablo ya da sütun adları parametreyle bağlanamaz; bunlar için izin verilen adların bir listesini kullan. Bölüm 34'te görülen `ORDER BY` örneği, bu sınırın pratik bir sonucudur.

### Deserializasyon ve pickle

Bir nesneyi bayt dizisine çevirmek (serileştirme) ve geri okumak (deserializasyon), ağ protokollerinin ve dosya biçimlerinin olağan parçasıdır. Ama Python'un `pickle` modülü, veriyi okurken nesne oluşturucularını çağırabilir. Yani güvenilmeyen bir kaynaktan gelen `pickle` verisi, deserializasyon sırasında kod çalıştırabilir. Bu yüzden `pickle.loads` güvenilmeyen veri üzerinde kullanılmaz.

Kural basit: dış dünyadan gelen veri için yalnızca veri tiplerini okuyan biçimleri kullan. JSON bunun bir örneğidir: `json.loads` yalnızca sözlük, liste, sayı, metin, bool ve `null` üretir ve nesne oluşturucusu çağırmaz. Başka bir biçim gerekiyorsa, veriyi açmadan önce bir HMAC ile doğrula (32.3). Diğer dillerdeki serileştirme kütüphaneleri de benzer riskler taşır (genel bilgi).

### Uzunluk alanına körü körüne güvenmemek

Bölüm 31'deki uzunluk önekli çerçevede, alıcı 4 baytlık bir uzunluk okur ve o kadar bayt bekler. Uzunluk alanı, saldırganın kontrolündedir. Bu alanın değerini bellek ayırmadan önce bir üst sınırla karşılaştırmak zorunludur (Bölüm 31.4'teki `MAKS`). Aynı ilke, HTTP başlık satırlarının uzunluğu için de geçerlidir: Bölüm 30'daki sunucu `MAKS_BASLIK` ile sınırlar. Sayısal girdilerde de benzer biçimde, değer aralığını ve türünü ayrıştırmadan önce denetle.

## 32.8 Kendi kodunda hata avı: fuzzing, statik analiz ve canlı test

Birim testleri, bildiğimiz davranışları doğrular. Fuzzing ise bilmediğimiz hataları arar. Bir fuzzer, hedef fonksiyona çok sayıda girdi verir; bu girdiler mevcut örneklerin **mutasyonu** ile üretilir: bir bayt değişir, bir parça silinir, bir parça tekrar eder, özel karakterler eklenir. Her girdi için hedefin davranışı izlenir ve bir **sözleşme** ihlali (beklenmeyen istisna, çökme, sanitizer hatası) aranır.

Üç kavram bu işin çekirdeğidir. **Sözleşme**, hedefin hangi girdide hangi istisnayı fırlatabileceğini belirtir: çerçeve okuyucusu bozuk girdide `ValueError` fırlatabilir, ama bir bağlantı işleyicisi hiçbir istemci girdisinde istisna sızdırmamalıdır. **Sabit tohum**, aynı deneyin her çalıştırmada aynı girdileri üretmesini sağlar; bu sayede bulunan bir hata tekrar üretilebilir. **En kısa yeniden üretici**, bulunan hatayı tetikleyen en küçük girdidir ve hatanın nedenini anlamayı kolaylaştırır.

![Şekil 32.10: Fuzzing döngüsü. Mutasyon, hedefi çalıştırma, sözleşme denetimi, en kısa örneğin saklanması ve düzeltme sonrası yeniden çalıştırma adımlarından oluşur.](gorseller/b32_fuzz.png)

### Fuzzer'ımız

Aşağıdaki çatı, dört hedefi aynı mutasyon motoruyla sınar: Bölüm 31'deki çerçeve okuyucusu, Bölüm 31'deki CRC'li telemetri çözücüsü, bu bölümdeki HMAC alıcısı ve Bölüm 30'daki HTTP sunucusunun bağlantı işleyicisi. Her hedefin sözleşmesi ayrıdır; bu ayrım önemlidir, aşağıda neden olduğunu göreceksin.

```python
def mutasyon(r, veri, tohumlar):
    """Rastgele bir mutasyon uygular; bazen baska tohumdan parca."""
    b = bytearray(veri) if veri else bytearray(b"\x00")
    secim = r.randrange(7)
    if secim == 0 and b:                      # bayt degistir
        b[r.randrange(len(b))] = r.randrange(256)
    elif secim == 1:                          # bayt ekle
        b.insert(r.randrange(len(b) + 1), r.randrange(256))
    elif secim == 2 and b:                    # bayt sil
        del b[r.randrange(len(b))]
    elif secim == 3 and b:                    # kes
        del b[r.randrange(len(b)):]
    elif secim == 4:                          # ozel karakterler
        i = r.randrange(len(b) + 1)
        b[i:i] = r.choice(
            [b"\r\n", b" ", b":", b"\xff\xfe", b"\x00", b"/../"])
    elif secim == 5:                          # tekrar eden blok
        i = r.randrange(len(b) + 1)
        b[i:i] = b[i:i + r.randrange(1, 40)]
    else:                                     # baska tohumdan parca
        baska = r.choice(tohumlar)
        i = r.randrange(len(b) + 1)
        b[i:] = baska[r.randrange(len(baska) + 1):]
    return bytes(b)

```

Mutasyon fonksiyonu, seçilen bir tohumu rastgele bir işlemle değiştirir. Yedinci dal, başka bir tohumdan parça alır; böylece geçerli bir çerçevenin başı ile bozuk bir gövde birleşebilir. Bu, gerçek ağ trafiğinde görülen karışımları taklit eder.

```python
def tara(ad, hedef, tohumlar, beklenen, yineleme=YINELEME):
    """Hedefi yineleme kez calistirir; beklenmeyen istisnalari sayar.

    beklenen: hedefin bilerek firlatabilecegi istisna sinifi demeti.
    Bu demet bos ise hedef istemci girdisinde istisna sizdirmamali."""
    r = random.Random(TOHUM)
    beklenmeyen = {}
    ornek = {}
    for _ in range(yineleme):
        girdi = mutasyon(r, r.choice(tohumlar), tohumlar)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                hedef(girdi)
        except beklenen:
            pass                              # sozlesmedeki red
        except Exception as e:                # beklenmeyen -> HATA
            tur = type(e).__name__
            beklenmeyen[tur] = beklenmeyen.get(tur, 0) + 1
            # en kisa yeniden uretici girdiyi sakla
            if tur not in ornek or len(girdi) < len(ornek[tur][0]):
                ornek[tur] = (girdi, str(e)[:60])
    return beklenmeyen, ornek

```

Test döngüsü, her girdiyi hedefe verir. Sözleşmedeki istisnalar sessizce geçilir; diğer her istisna sayılır ve en kısa örnekle birlikte saklanır. Bu tasarımın kritik bir noktası var: `beklenen` demeti, hedef bazında ayrı verilir. HTTP hedefinde bu demet boştur; yani bağlantı işleyicisi hiçbir girdide istisna fırlatmamalıdır.

### Bulgu: Bölüm 30 sunucusu bir baytla düşüyor

Özgün Bölüm 30 sunucusunu, yalnızca kopyalayıp fuzzer'a verdik. Hiçbir kod değiştirmedik. Önce fuzzer'ı çalıştıralım.

```term
$ python b32_fuzz.py ham
surum=ham, yineleme=20000, tohum=32
cerceve    beklenmeyen istisna yok
telemetri  beklenmeyen istisna yok
hmac       beklenmeyen istisna yok
http      ValueError  x1770
  ornek: b'PO\xadT / HTTP/1.1\r\n\r\n'
           mesaj: invalid literal for int() with base 10: 'ascii'
toplam beklenmeyen istisna: 1770
```

Çıktı, 20 000 denemenin 1770'inde HTTP hedefinin beklenmeyen bir `ValueError` fırlattığını söyler. En kısa yeniden üretici, `POST` isteğinin yöntem alanında tek bir `0xAD` baytı olan bir istektir. Çerçeve okuyucusu ve telemetri çözücüsü ise sıfır hata verdi; bunu da kaydetmeliyiz. Bu sonuç bir kanıt değil, bu girdi uzayında bulunamamış bir hatadır.

Hatanın nedenine bak. Bölüm 30 sunucusunun `istek_oku` fonksiyonu, istek satırını `ascii` olarak çözer. 0xAD gibi bir bayt bu çözmeyi `UnicodeDecodeError` ile durdurur. Bu istisna bir `ValueError` alt sınıfıdır. Sunucunun `baglanti_isle` fonksiyonu, `ValueError`'u bir HTTP durum kodu sanarak `int(e.args[0])` çağırır. Bu çağrı, `e.args[0]`'ın değeri `'ascii'` olduğu için kendisi de bir `ValueError` fırlatır ve bu istisna hiçbir yerde yakalanmadan dışarı çıkar.

```python
def baglanti_isle(conn, adres):
    conn.settimeout(5.0)              # bosta bekleyen baglanti
    f = conn.makefile("rb")
    try:
        while True:
            try:
                istek = istek_oku(f)
            except ValueError as e:
                cevap_yaz(conn, int(e.args[0]),
                          [("Connection", "close")], b"")
                return
            except socket.timeout:
                return
            if istek is None:
                return
```

Sunucunun ana döngüsü `baglanti_isle` çağrısını hiçbir `try` bloğu içinde yapmaz. Bu nedenle istisna, süreci sonlandırır. Sunucu tek süreçli olduğu için, tek bir kötü biçimlendirilmiş istek tüm hizmeti durdurur. Bu bir **hizmet reddi** (DoS) hatasıdır ve STRIDE tablosundaki D (denial of service) sınıfına girer.

Bu hatanın canlı bir sunucuda da olduğunu doğrulayalım. `b32_canli.py`, iki sunucuyu yalnızca `127.0.0.1` üzerinde başlatır, aynı kötü isteği gönderir ve sonra iyi bir istek dener.

```term
$ python b32_canli.py
ozgun (b32_http_ham)   kotu istek -> b''
ozgun (b32_http_ham)   SUNUCU OLDU (cikis=1)
                       son satir: ValueError
sagmlastirilmis        kotu istek -> b'HTTP/1.1 400 Bad Request'
sagmlastirilmis        hayatta; sonraki iyi istek -> b'HTTP/1.1 200 OK'
```

Özgün sunucu, kötü isteğe yanıt vermeden çıkar ve çıkış kodu 1 ile hata mesajını yazar. Sağlamlaştırılmış sürüm aynı isteğe `400 Bad Request` döner ve sonraki iyi isteğe `200 OK` ile yanıt verir. Bu fark, hatanın yalnızca bir fuzzer sonucu olmadığını, gerçek bir süreçte de yıkıcı olduğunu gösterir.

Fuzzer'ın bu hatayı ilk seferde neden kaçırdığı da öğreticidir. İlk sürümümüzde `ValueError` tüm hedeflerde "beklenen red" sayılıyordu. Bu nedenle `UnicodeDecodeError`'dan türeyen `ValueError` da sessizce geçiliyordu ve sayaç sıfır gösteriyordu. Sözleşmeyi hedef bazında ayırmak, bu tür maskelemeyi önler. Kural: beklenen istisnayı yalnızca sınıf olarak değil, hedefin kendi tanımladığı bir sözleşme olarak belirt.

### Düzeltme: sağlamlaştırılmış sunucu

Düzeltmenin üç parçası vardır ve her biri ayrı bir savunma katmanıdır. Birincisi, ayrıştırma hataları bir `HttpHata` istisnası ile durum koduna bağlanır; durum kodu bir `int` olarak istisnanın içinde taşınır ve hiçbir yerde metinden sayıya çevrilmez. Her ASCII çözme adımı da `_ascii` yardımcısından geçer ve hata 400'e dönüşür.

```python
class HttpHata(Exception):
    """Istemci hatasi: durum kodu istisnanin kendisinde tasinir."""

    def __init__(self, kod):
        super().__init__(kod)
        self.kod = kod


def _ascii(bayt):
    try:
        return bayt.decode("ascii")
    except UnicodeDecodeError:
        raise HttpHata(400)

```

İkincisi, yol denetimi gerçek yol üzerinde yapılır. Bu, 32.7'de anlattığımız üç adımın bu sunucudaki uygulamasıdır.

```python
def dosya_yolu(yol):
    """URL yolunu KOK altindaki gercek dosya yoluna cevirir.

    realpath sembolik baglari cozer; boylece KOK icindeki bir bag
    disari gosteriyorsa da reddedilir. URL cozme (%2e%2e gibi) bu
    sunucuda yapilmaz; yapilirsa denetim ayni tekrarlanmali."""
    yol = yol.split("?", 1)[0]
    if yol.endswith("/"):
        yol += "index.html"
    aday = os.path.realpath(os.path.join(KOK, yol.lstrip("/")))
    try:
        ortak = os.path.commonpath([KOK, aday])
    except ValueError:                    # farkli surucu
        return None
    if ortak != KOK:
        return None
    return aday if os.path.isfile(aday) else None

```

Üçüncüsü, ana döngü her bağlantıyı ayrı bir `try` bloğuyla korur. Bu, birinci katmanın kaçırdığı bir hata olursa bile, sunucunun çalışmaya devam etmesini sağlar. Bu bir yama değil, bir **savunma derinliği** katmanıdır: asıl düzeltme birinci katmandadır, ama ikinci katman, birincinin unuttuğu durumda hizmeti sürdürür.

```python
    while MAKS == 0 or sayac < MAKS:
        conn, adres = srv.accept()
        try:
            baglanti_isle(conn, adres)
        except Exception as e:      # savunma derinligi: katman 4
            print("baglanti hatasi:", type(e).__name__,
                  file=sys.stderr, flush=True)
        sayac += 1
```

Düzeltilmiş sunucuyu aynı fuzzer ile yeniden çalıştırıyoruz. Sözleşmenin aynı olduğuna dikkat et: yalnızca kod değişti, test değişmedi.

```term
$ python b32_fuzz.py sag
surum=sag, yineleme=20000, tohum=32
cerceve    beklenmeyen istisna yok
telemetri  beklenmeyen istisna yok
hmac       beklenmeyen istisna yok
http       beklenmeyen istisna yok
toplam beklenmeyen istisna: 0
```

Sayım sıfır. Bu, bu deney tasarımı ve bu girdi uzayı için bir sonuçtur; bir ispat değildir. Tablo, iki sürümün ve dört hedefin karşılaştırmasını verir.

| hedef | yineleme | ozgun | sagmlastirilmis |
|---|---|---|---|
| cerceve | 20000 | 0 | 0 |
| telemetri | 20000 | 0 | 0 |
| hmac | 20000 | 0 | 0 |
| http | 20000 | 1770 | 0 |

Tabloda Bölüm 31'in çerçeve ve telemetri hedeflerinin sıfır hata verdiğini görüyorsun. Bu iyi bir haberdir; ama fuzzer'ın bulamadığı bir hatanın yokluğunu kanıtlamaz. Fuzzing, kapsamını bildiğin girdiler için bir kanıt üretir; kapsam dışı girdilerde sessiz kalır.

### Statik analiz: derleyici de hata arayabilir

Bir hata, çalıştırılmadan da görülebilir. `-fanalyzer`, derleyicinin içinde çalışan bir analiz motorudur: fonksiyonlar boyunca bir işaretçinin durumunu izler ve serbest bırakılmış bellek ile çift serbest bırakmayı çoğu zaman yakalar. Bölüm 32.5'teki iki hatalı programı bu motorla tarayalım.

```term
$ gcc -fanalyzer -Wall -std=c11 -c b32_c2_hatali.c
b32_c2_hatali.c:23:5: warning: pointer ‘s’ used after ‘free’ [-Wus
e-after-free]
b32_c2_hatali.c:23:5: warning: use after ‘free’ of ‘s’ [CWE-416] [
-Wanalyzer-use-after-free]
```

```term
$ gcc -fanalyzer -Wall -std=c11 -c b32_c3_hatali.c
b32_c3_hatali.c:12:5: warning: double-‘free’ of ‘p’ [CWE-415] [-Wa
nalyzer-double-free]
```

Uyarılar, ASan'ın çalışma zamanında gösterdiği hataları derleme zamanında işaretler: `use after 'free'` ve `double-'free' of 'p'`. Statik analizin sınırı da burada görünür: aynı analiz, `c1_hatali.c`'deki yığın taşmasını bu sürümde yakalamadı (uyarı çıkmadı). Bu yüzden statik analiz, sanitizer ve fuzzing'in yerini almaz; üçü birlikte kullanılır.

### Fuzzing ve sanitizer birlikte

Python fuzzer'ı, C kodunun bellek hatalarını ASan ile birlikte yakalamaz; çünkü bir Python süreci kendi belleğini yönetir. C kodu için gerçek bir fuzzing'de, hedef fonksiyonu ASan ve UBSan ile derleyip kapsamı yönlendiren fuzzer'lar (AFL++, libFuzzer; genel bilgi) kullanılır. Bu kitapta bu araçları kurmadık; ama ilke aynıdır: girdiyi rastgele üret, hedefi sanitizer altında çalıştır, bulunan en kısa örneği sakla.

Bölüm 31'deki ayrıştırıcıları yeniden düşün: bir uzunluk alanı, bir sınır denetimi ve bir sıra numarası. Bu üç alanın her biri, fuzzing için bir hedef yüzeyidir. Bir sonraki adımda bu yüzeyi sistematik olarak kapatmayı kendin deneyeceksin (Kendin Yap, Proje 2).

::: dikkat
Fuzzing'i yalnızca kendi kodunda ve yalnızca kendi kontrolündeki sistemlerde çalıştır. Üçüncü taraf bir hizmete yönelik istekleri, izinsiz bir tarama olarak yorumlanabilir ve hukuki sonuçları olabilir.
:::

## 32.9 Web, oturum ve kimlik

Bölüm 30'da çerezlerin ve oturumların HTTP'ye nasıl eklendiğini gördün ve bu konunun güvenlik kısmını bu bölüme bıraktık. Oturum tasarımında temel fikir şudur: tarayıcıda yalnızca **tahmin edilemez bir oturum kimliği** tutulur; kullanıcının durumu, yetkileri ve verileri sunucudadır. Çerezi çalmak, o oturumu devralmak demektir; bu yüzden çerezin korunması bir güvenlik gereksinimidir.

### Çerez bayrakları

Bir çerezin davranışı birkaç bayrakla belirlenir. **HttpOnly** çerezi JavaScript'in okuyamamasını sağlar; bir XSS açığının çerezi doğrudan sızdırmasını engeller. **Secure** çerezin yalnızca HTTPS üzerinden gönderilmesini sağlar. **SameSite** (Lax, Strict ya da None) çerezin çapraz site isteklerde ne zaman gönderileceğini belirler. **Max-Age** ve **Path** süreyi ve kapsamı sınırlar. Aşağıdaki kod, bu bayrakları ayarlayan bir `Set-Cookie` satırı üretir.

```python
def oturum_cerezi(deger):
    c = cookies.SimpleCookie()
    c["oturum"] = deger
    c["oturum"]["path"] = "/"
    c["oturum"]["max-age"] = 1800          # 30 dakika
    c["oturum"]["httponly"] = True         # JavaScript okuyamaz
    c["oturum"]["secure"] = True           # yalnizca HTTPS
    c["oturum"]["samesite"] = "Lax"     # capraz site istek yok
    return c["oturum"].OutputString()
```

```term
$ python b32_web.py
Set-Cookie:
    oturum=8CPQEBYsDjxUseszDRoMExvm5lU8B1fJRWv9IDZ4zTY
    HttpOnly
    Max-Age=1800
    Path=/
    SameSite=Lax
    Secure
csrf dogru: True
csrf yanlis: False
csrf eksik: False
```

Çıktıdaki `Set-Cookie` satırı, sekiz bayrağın hepsinin doğru yazıldığını gösterir. Oturum kimliği `secrets.token_urlsafe(32)` ile üretilir: 256 bit rastgelelik, kayıt tahmin edilemezlik sağlar.

### CSRF: sahte istekler

**Çapraz site istek sahteciliği** (Cross-Site Request Forgery, CSRF), kullanıcının tarayıcısının, oturum çerezi ile birlikte, kullanıcının bilmediği bir isteği hedef siteye göndermesidir. Tarayıcı, hedef siteye giden her isteğe ilgili çerezleri otomatik ekler; saldırgan sayfası kullanıcıdan bir işlem yaptırabilir. Savunma, isteğin gerçekten kendi sayfandan geldiğini kanıtlamaktır: formda gönderilen ve sunucuda oturumla eşleştirilmiş bir **CSRF jetonu**. Saldırgan sayfası bu jetonu okuyamaz (aynı köken politikası), bu yüzden jetonu içeren bir istek üretemez.

```python
def csrf_jetonu_uret():
    return secrets.token_urlsafe(32)       # 256 bit, oturuma bagli


def csrf_dogrula(oturum_jetonu, form_jetonu):
    if not oturum_jetonu or not form_jetonu:
        return False
    return hmac.compare_digest(oturum_jetonu, form_jetonu)
```

Jetonun karşılaştırması da sabit zamanlı yapılır (32.3). SameSite çerezi ek bir katmandır, ama tek başına yeterli değildir: eski tarayıcılar ve bazı yönlendirme senaryoları için jeton hâlâ gereklidir. Durum değiştiren her işlem (`POST`, `PUT`, `DELETE`) CSRF jetonu ister; `GET` yalnızca okuma içindir ve durum değiştirmemelidir.

### Parola politikası, çok faktörlü doğrulama ve federasyon

Parola saklamayı 32.2'de gördük; burada politika tarafını ekliyoruz. NIST SP 800-63B, parolalarda uzunluğu, yasaklı parolaların taranmasını ve periyodik zorunlu değişikliği yerine gereksiz yere karmaşık kuralların kaldırılmasını önerir (genel bilgi). **Çok faktörlü doğrulama** (MFA), bilgi (parola), sahiplik (telefon, güvenlik anahtarı) ve biyometri gibi bağımsız faktörlerden en az ikisini ister. Bir faktörün sızması, tek başına hesabı ele geçirmeye yetmez.

**OAuth 2.0** bir yetki devri çerçevesidir: kullanıcı, bir uygulamanın kendi verilerine belirli kapsamlarla erişmesine izin verir. **OpenID Connect** bunun üzerine bir kimlik katmanı ekler ve kullanıcının kimliğini bir kimlik sağlayıcısı üzerinden doğrular. Bu iki standart ayrıntılı bir konudur ve bu kitabın kapsamı dışındadır; ama farkı bilmek önemlidir: OAuth "bu uygulama neye erişebilir" sorusunu, OIDC "bu kullanıcı kimdir" sorusunu yanıtlar.

::: dikkat
JWT gibi imzalı belirteçleri kabul ederken imzanın doğrulandığından ve algoritmanın sunucu tarafında sabitlendiğinden emin ol. İmza doğrulamayan ya da algoritmayı belirteçten okuyan kütüphaneler, saldırganın kendi belirteçlerini kabul ettirmesine izin verir. Bu, kütüphane seçiminin ve yapılandırmanın doğrudan güvenlik kararı olduğunun bir örneğidir.
:::

## 32.10 Güvenli yazılım süreci ve savunma sanayii bağlamı

Bu bölümde gördüğümüz tekniklerin hiçbiri tek başına bir sistemi güvenli yapmaz. Güvenlik, kodun yazıldığı, test edildiği, dağıtıldığı ve izlendiği süreçlerin toplamıdır. Bu alt bölümde, bu sürecin en önemli parçalarını ve savunma sanayiinde bunların nasıl ele alındığını özetliyoruz.

### Bağımlılık güvenliği

Projenin kullandığı her kütüphane, senin saldırı yüzeyinin parçasıdır. Üç ilke bu riski azaltır. **Sürüm sabitleme**: `requirements.txt` içinde her bağımlılığın tam sürümü yazılır; "en son sürüm" beklentisi, bir gün bir kötü amaçlı ya da hatalı sürümü otomatik olarak kurmana yol açabilir. **Hash doğrulama**: `pip install --require-hashes` ile her paketin özeti, kurulumdan önce kontrol edilir (pip özelliği; genel bilgi). **Bağımlılık envanteri**: hangi bileşenin hangi sürümde olduğunu bilmek, bir güvenlik bülteni çıktığında etkilenen sistemleri dakikalar içinde bulmanı sağlar. Bu envantere yazılım malzeme listesi (SBOM) denir (genel bilgi).

### Sırları koda gömmemek

Parolalar, API anahtarları ve özel anahtarlar koda, yapılandırma dosyasına ya da depoya girmemelidir. Yerel geliştirmede ortam değişkeni kullanılır ve bu değişken gösterilen dosyalar (`.env` gibi) `.gitignore` ile depodan dışlanır. Üretimde bir sır kasası (secret manager) veya donanım güvenlik modülü tercih edilir. Bir sır bir kez depoya girdiyse, silinse bile sızmış sayılır: git geçmişi onu tutar. Doğru tepki, sırrı derhal iptal edip yenilemektir; geçmişi yeniden yazmak yalnızca ek bir adımdır.

### Güvenlik günlüğü

Güvenlik günlüğü, bir olay olduğunda neyin olduğunu sonradan anlamanı sağlar. Kaydedilmesi gerekenler: başarısız giriş denemeleri, yetki reddleri, yapılandırma değişiklikleri ve yönetici işlemleri. Kaydedilmemesi gerekenler: parolalar, oturum kimlikleri, tam kişisel veri ve sırlar. Günlüğün değiştirilemez olması bir gereksinimdir: kayıtlar yalnızca eklenebilir (append-only) olmalı ve tercihen her kaydın özeti bir öncekine HMAC ile bağlanmalıdır (32.3). Böylece bir saldırgan iz bırakmadan kayıt silemez; bu, inkâr edilemezliğin uygulamadaki karşılığıdır.

### Sorumlu açıklama

Bir güvenlik açığı bulduğunda, ilk adım onu kamuya açıklamak değil, sorumlu tarafa (yazılımın sahibine ya da üreticisine) gizlilik içinde bildirmektir. Yaygın bir pratik, sorumlu tarafa bir düzeltme için makul bir süre tanımak ve bu süre dolmadan kamuya açıklamamaktır. Bu süreler sektörde ve kuruluşlarda farklıdır (genel bilgi). Yazılım mühendisi olarak, kendi projene gelen bildirimleri bir kanal üzerinden alabilecek ve yanıtlayabilecek şekilde hazır olmalısın.

### Savunma sanayiinde standartlar ve sertifikasyon

Savunma ve havacılık yazılımında güvenlik, bir tercih değil, bir sertifikasyon gereksinimidir. Bu bölümde adını andığımız standartlar, ayrıntılarına girmeden bilinmelidir (hepsi genel bilgi düzeyindedir). **Common Criteria** (ISO/IEC 15408), ürünlerin güvenlik özelliklerinin bağımsız olarak değerlendirilmesi için uluslararası bir çerçevedir. **DO-178C**, havacılık yazılımının geliştirme ve doğrulama süreçlerini tanımlar; güvenlik ve doğrulama kanıtları bu sürecin parçasıdır. **DO-326A**, havacılık sistemlerinde siber güvenlik için süreç gereksinimlerini içerir. **NIST SP 800 serisi**, kriptografi, kimlik ve sistem güvenliği için yaygın referans belgeleridir. Bu standartların ortak mesajı, güvenliğin ispatlanabilir olması gerektiğidir: "güvenliyiz" demek yetmez, kanıt gerekir.

Bu kanıt, bu bölümde yaptığımız deneylerin mantığına benzer: bir iddiayı (sözleşme, koruma, sertifika) ölçülebilir bir sonuçla (test, sanitizer raporu, fuzzing tablosu) desteklemek. Sertifikasyon süreçleri bu kanıtları daha büyük ölçekte ve bağımsız bir gözle ister. Doğrulama ve sertifikasyon ayrıntıları Bölüm 78'de yeniden ele alınacak.

### Yan kanal ve sabit zamanlı kod

Bölüm 32.3'te sabit zamanlı karşılaştırmayı gördük. Aynı mantık daha geniş bir alana uygulanır: bir işlemin süresi, önbellek davranışı ya da güç tüketimi, gizli bir değer hakkında bilgi taşıyabilir. Bölüm 24'teki Spectre ve Meltdown, bu fikrin işlemci düzeyindeki karşılığıdır: spekülatif yürütme, işlemci önbelleğinin zamanlamasını bir yan kanal olarak açığa çıkarır. Yazılım tarafında bu riskle başa çıkmanın yolu, gizli veriye bağlı dallanma ve bellek erişimlerinden kaçınan sabit zamanlı kodlar yazmaktır; ancak bu, donanım azaltımlarını (mikro kod ve işletim sistemi yamaları) ortadan kaldırmaz.

### Kontrol listesi

Aşağıdaki liste, bu bölümde gördüğümüz ilkeleri bir geliştirme sürecinde kontrol edilebilir maddeler hâline getirir. Her maddeyi bir kod incelemesinde sorabilirsin.

1. Her girdi noktasında (ağ, dosya, komut satırı, ortam değişkeni) veri sınırı ve biçimi denetleniyor mu?
2. Harici komutlar argüman listesiyle mi çağrılıyor?
3. Dosya yolları `realpath` ve kök dizin denetimiyle mi çözülüyor?
4. Kriptografik işlemler sınanmış bir kütüphaneyle mi yapılıyor; anahtarlar kodda değil mi?
5. Karşılaştırmalar gizli değerler için sabit zamanlı mı?
6. Derleme korumaları (kanarya, FORTIFY, NX, PIE, RELRO) açık ve bir CI adımıyla denetleniyor mu?
7. C kodu ASan ve UBSan altında test ediliyor mu; ayrıştırıcılar fuzzing'den geçiyor mu?
8. Bağımlılıklar sabit sürümlü ve hash doğrulamalı mı; sırlar depoda değil mi?

## Çözümlü Örnekler

Aşağıdaki dört örnek, Bölüm 5'teki altı adımlı yöntemi izler: Anla, Örnekle, Kaba çöz, Örüntü, İyileştir, Doğrula. Her örneğin sonunda elle iz sürme tablosu vardır. Önce kâğıda çöz, sonra çıktıyla karşılaştır.

### Örnek 1 (★): Telemetri akışının kabul ve red kararlarını izlemek

Bölüm 32.3'teki alıcı, her pakette üç soru sorar: etiket doğru mu, sıra numarası son kabul edilenden büyük mü, paket beklenen uzunlukta mı. Bu örnekte bu üç sorunun sırasının neden önemli olduğunu göreceksin.

**Adım 1 — Anla.** Alıcının durumu tek bir değişkendir: `son_sira`, başlangıçta -1. Bir paket geldiğinde önce uzunluk kontrol edilir (40 bayt). Sonra etiket HMAC ile yeniden hesaplanıp karşılaştırılır. Etiket doğruysa sıra numarası `son_sira` ile karşılaştırılır. Sıra büyükse paket kabul edilir ve `son_sira` güncellenir. Her red durumunda `son_sira` değişmez.

**Adım 2 — Örnekle.** Sekiz paket gelir. Paketlerin bir kısmı kasıtlı olarak bozulmuştur: 2. pakette bir bit değişmiş, 6. paketin uzunluğu 39 bayttır. Sıra numaraları 1, 2, 2, 2, 1, 5, 6, 6'dır.

**Adım 3 — Kaba çöz.** Her paket için kararı yukarıdan aşağı soralım. Önce uzunluk, sonra etiket, sonra sıra. İlk red kararında diğer kontrollere gerek yoktur, ama bu tabloda her paketin hangi kontrolde takıldığını görmek için yine de sırayla gideceğiz.

**Adım 4 — Örüntü.** Bir tekrar eden kural var: sıra numarası hiçbir zaman geri gitmez, ama aynı numara ikinci kez gelirse reddedilir. Bu, `son_sira` karşılaştırmasının iki işi birden yaptığını gösterir: tekrar oynatmayı ve sıra dışı paketleri engeller.

**Adım 5 — İyileştir.** Bu kuralın bir sonucu, sıra numarası boşluklarıdır. 3 ve 4 numaralı paketler hiç gelmedi; alıcı bunları kayıp sayabilir, ama bu bir **tahmindir**: paketler gecikmiş olarak da gelebilir, ama bu tasarımda gecikmiş paketler zaten reddedilir. Gerçek bir sistemde bu tahmin, bir pencere (window) mekanizmasıyla yumuşatılır; bu tasarım bunu yapmaz.

**Adım 6 — Doğrula.** Aşağıdaki tabloyu kâğıtta doldur, sonra karşılaştır.

| No | Sıra | Uzunluk | Etiket | Sıra > son? | Karar | son (sonra) |
|---|---|---|---|---|---|---|
| 1 | 1 | 40 | geçerli | 1 > -1 evet | kabul | 1 |
| 2 | 2 | 40 | bozuk | — | red (etiket) | 1 |
| 3 | 2 | 40 | geçerli | 2 > 1 evet | kabul | 2 |
| 4 | 2 | 40 | geçerli | 2 > 2 hayır | red (tekrar) | 2 |
| 5 | 1 | 40 | geçerli | 1 > 2 hayır | red (tekrar) | 2 |
| 6 | 5 | 39 | — | — | red (biçim) | 2 |
| 7 | 5 | 40 | geçerli | 5 > 2 evet | kabul | 5 |
| 8 | 6 | 40 | geçerli | 6 > 5 evet | kabul | 6 |

Tablo 2 numaralı paketin bozuk olduğunu, ama 3 numaralı paketin aynı sıra numarasıyla kabul edildiğini gösterir. Bu doğrudur: bozuk paket `son_sira`'yı değiştirmedi. 6 numaralı paketin reddi de aynı şekilde `son_sira`'ya dokunmaz. 7 numaralı paket 5'i kabul eder; sıra numarası 5 olduğu için boşluk 3 ve 4 ile ilgili kayıp tahmini burada yapılmış olur.

**Bunu AI'sız yazabilir misin?** Aynı kuralları üreten bir `alici_karar(paket, durum)` fonksiyonu yaz. Fonksiyon, bir `(karar, yeni_durum)` çifti döndürsün. Sekiz paketlik bir diziyle tabloyu yeniden üret ve her satırın sonucunu elle yazdığın tabloyla karşılaştır.

### Örnek 2 (★★): Parola kaydının doğrulamasında sınır denetimi

Bölüm 32.2'deki `parola_dogrula` fonksiyonu bir kayıt satırını alır. Kayıt bir veritabanından gelir ve veritabanı sızmış olabilir; bu yüzden kayıttaki her alan güvenilmez kabul edilir. Bu örnekte dört farklı kaydın doğrulamasını elle izleyeceğiz.

**Adım 1 — Anla.** Kayıt `scrypt$n$r$p$tuz_hex$ozet_hex` biçimindedir. Fonksiyon önce kaydı altı parçaya böler, sonra `n`, `r`, `p` değerlerini tamsayıya ve tuz ile özeti hex'ten bayta çevirir. Ardından `n` değeri `2 ≤ n ≤ N_MAKS` aralığında mı diye bakar. Bu denetim, `scrypt` hesabından önce yapılır.

**Adım 2 — Örnekle.** Dört kayıt deneyeceğiz: (a) doğru parolanın geçerli kaydı, (b) yanlış parola, (c) `n = 1073741824` (2^30) olan bir kayıt, (d) tuz alanında geçersiz hex olan bir kayıt. `N_MAKS = 2^20 = 1048576`.

**Adım 3 — Kaba çöz.** (a) ve (b) için scrypt hesabı çalışır, sonuçlar sabit zamanlı karşılaştırılır. (c) için `n` aralığın dışındadır ve fonksiyon hesap yapmadan `False` döner. (d) için `bytes.fromhex` `ValueError` fırlatır; bu, `try` bloğunda yakalanır ve `False` döner.

**Adım 4 — Örüntü.** Kayıt bir **güvenilmeyen girdidir** ve her alan için iki denetim gerekir: biçim (ayrıştırma hatası) ve değer aralığı. Biçim hatası istisna ile yakalanır; değer aralığı hatası ise hesaplamadan önce reddedilir. İkinci denetim olmasaydı, kayıttaki büyük bir `n` sunucuda aşırı bellek ayırmasına yol açabilirdi.

**Adım 5 — İyileştir.** Fonksiyonun bir eksiği var: `r` ve `p` değerlerine üst sınır konmamış. `r` büyüdükçe bellek kullanımı artar; bu yüzden gerçek bir sistemde `r` ve `p` için de üst sınırlar tanımlanmalıdır. Bu bölümde bu sınırı eklemedik; ödev olarak bırakıyoruz.

**Adım 6 — Doğrula.** Tabloyu doldur ve `test` kipinin çıktısıyla karşılaştır.

| Kayıt | Ayrıştırma | n aralığı | Hesap | Sonuç |
|---|---|---|---|---|
| (a) doğru parola | başarılı | 2^14 uygun | scrypt yapıldı, eşleşti | True |
| (b) yanlış parola | başarılı | 2^14 uygun | scrypt yapıldı, eşleşmedi | False |
| (c) n = 2^30 | başarılı | 2^30 > 2^20, red | yapılmadı | False |
| (d) tuz "zz" | `ValueError` | — | yapılmadı | False |

Testteki "asiri n sinirda red" kontrolü, (c) satırının davranışını doğrular. Bu tablo ile test çıktısının aynı sonucu verdiğini görmelisin.

**Bunu AI'sız yazabilir misin?** Kaydı biçimine göre ayrıştıran ve bir `(n, r, p, tuz, ozet)` demeti döndüren, geçersiz alanlarda `ValueError` fırlatan bir `kayit_coz` fonksiyonu yaz. Üst sınır denetimini bu fonksiyonun içinde değil, çağıranda yapmanın hangi riski doğurduğunu iki cümleyle açıkla.

### Örnek 3 (★★): Yol geçişinde üç kontrolün sırası

Bölüm 32.7'deki `guvenli_yol` fonksiyonu üç kontrol yapar: NUL baytı, gerçek yol ve kök dizin ile ortak yol karşılaştırması. Bu örnekte kök dizinin `/srv/kok` olduğunu varsayarak beş isteği izleyeceğiz.

**Adım 1 — Anla.** Fonksiyon önce NUL baytını arar; varsa `None` döner. Sonra kök dizinin gerçek yolunu alır, isteği birleştirip gerçek yolunu bulur ve `commonpath([kok, aday])` ile ortak öneki hesaplar. Ortak önek kök dizinden farklıysa aday kökün dışındadır.

**Adım 2 — Örnekle.** İstekler: `a.txt`, `../gizli`, `/../gizli`, `alt/../b`, ve `a\x00b`.

**Adım 3 — Kaba çöz.** `a.txt` için birleştirme `/srv/kok/a.txt` verir, ortak önek `/srv/kok`'tur, eşleşir: kabul. `../gizli` için birleştirme `/srv/kok/../gizli`'yi `/srv/gizli`'ye normalleştirir; ortak önek `/srv`'dir: red. `/../gizli` baştaki eğik çizgi silindikten sonra `../gizli` ile aynıdır: red. `alt/../b` `/srv/kok/b`'ye düşer: kabul. `a\x00b` ilk kontrolde reddedilir.

**Adım 4 — Örüntü.** Kökten çıkmanın tüm yolları, birleştirme sonrası gerçek yolun kökün altında kalıp kalmadığına bakılarak yakalanır. Girdinin nasıl yazıldığı (`/`, `..`, `alt/..`) önemli değildir; ölçüt sonuçtur. Bu nedenle kontrolü girdi metninde değil, çözümlenmiş yolda yapmak gerekir.

**Adım 5 — İyileştir.** `realpath` sembolik bağları da çözer. Bu, kök içinde görünen bir bağın dışarıya işaret etmesi durumunu da yakalar; bunu bu örnekte iz sürmedik ama aynı mantıkla çalışır. Sistem gerçek bir sembolik bağa sahip olduğunda, `realpath`'in ne döndüreceğini kendin doğrulamalısın.

**Adım 6 — Doğrula.** Tablo:

| İstek | Birleştirme (normalleştirilmiş) | Ortak önek | Karar |
|---|---|---|---|
| `a.txt` | `/srv/kok/a.txt` | `/srv/kok` | kabul |
| `../gizli` | `/srv/gizli` | `/srv` | red |
| `/../gizli` | `/srv/gizli` | `/srv` | red |
| `alt/../b` | `/srv/kok/b` | `/srv/kok` | kabul |
| `a\x00b` | — | — | red (NUL) |

Tablo, Bölüm 32.7'deki `yol` kipinin mantığını izler: naif sürüm `../gizli` için kökten çıkar, güvenli sürüm reddeder.

**Bunu AI'sız yazabilir misin?** `/srv/kok` yerine kök dizin olarak `/srv/kok/` (sondaki eğik çizgiyle) verilirse ne olur? `commonpath` ve `realpath` bu sondaki eğik çizgiyi nasıl ele alır? Cevabını Python'da bir kez dene ve açıkla.

### Örnek 4 (★★★): Tamsayı taşmasından doğan yanlış `malloc` boyutu

Bölüm 32.5'teki `dizi_olustur` fonksiyonu `n * 4` hesabını `int` ile yapar. Bu örnekte farklı `n` değerleri için hesabın ne olduğunu izleyeceğiz; hem işaretli `int` hem de düzeltilmiş `size_t` sürümü için.

**Adım 1 — Anla.** Fonksiyon `bayt = n * (int)sizeof(int)` hesaplar, sonra `malloc((size_t)bayt)` çağırır ve `n` tamsayı yazar. İşaretli `int` taşması tanımsız davranıştır. Pratikte derleyiciler genellikle modüler (2'nin tümleyeni) sonucu üretir, ama bu standardın garantisi değildir.

**Adım 2 — Örnekle.** Dört `n` değeri: 16, 2^30, 2^30 + 1 ve 2^62. İlk üçü `int` sürümünde, dördüncüsü `size_t` sürümünde denenecek.

**Adım 3 — Kaba çöz.** `n = 16` için `16 * 4 = 64`, taşma yok. `n = 2^30` için matematiksel çarpım `2^32`'dir; 32 bitlik sonuç modüler olarak `0` olur. `malloc(0)` ayırma büyüklüğü sıfır olan bir istektir; döndürülen değer kullanılamaz ve yazma hatası doğurur. `n = 2^30 + 1` için matematiksel çarpım 4294967300'dür; 32 bit sonucu `4`'tür; `malloc(4)` yalnızca 4 bayt verir, döngü ise 2^30 + 1 tamsayı yazmaya çalışır. `n = 2^62` için `size_t` çarpımı `2^64`'tür ve taşar.

**Adım 4 — Örüntü.** Taşan çarpım **küçük** bir sonuç verir ve bu sonuç, döngünün ihtiyacını karşılamaz. Hata, bellek ayırma ile yazma döngüsü arasındaki boyut uyuşmazlığıdır. Düzeltme de bu uyuşmazlığı yok etmektir: ayırmadan önce hesabın taşmadığını kanıtla.

**Adım 5 — İyileştir.** `__builtin_mul_overflow(n, sizeof(int), &bayt)` çarpımı yapar ve taşma varsa `1` döner; yani sonucu kullanmadan önce bir kez kontrol edersin. Tip olarak `size_t` kullanmak da hesabın işaretsiz olmasını sağlar, ama bu tek başına yeterli değildir: `n` büyükse taşma yine olur.

**Adım 6 — Doğrula.** Tablo:

| n | Matematiksel n·4 | 32 bit `int` sonucu | `malloc` boyutu | Düzeltilmiş sürüm |
|---|---|---|---|---|
| 16 | 64 | 64 | 64 | ayırır, yazar |
| 2^30 | 4294967296 | 0 | 0 (hatalı) | taşma, NULL döner |
| 2^30 + 1 | 4294967300 | 4 | 4 (hatalı) | taşma, NULL döner |
| 2^62 (size_t) | 2^64 | — | — | taşma, NULL döner |

Gerçek derleme ASan ile çalıştırıldığında, `n = 2^30 + 1` için UBSan işaretli taşmayı, ASan ise yazma hatasını raporlar. Düzeltilmiş sürüm `2^62` değerinde reddeder ve `16` değerinde normal çalışır. Tablodaki hesapların çıktıyla uyumlu olduğunu doğrula.

**Bunu AI'sız yazabilir misin?** `n` değerinin bir dizi uzunluğu olarak kullanıldığı bir `int` fonksiyonunda taşmayı önleyen sürümü, ayırmanın yanında yazma döngüsünün de `n` ile sınırlı olduğunu gösteren bir yorumla birlikte yaz. Taşmanın yalnızca çarpımda değil, toplamda da (`n + 1`) olabileceğini bir örnekle göster.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçları **yasak**. Amaç çalışan bir sistem üretmekten çok, güvenliğin tasarım kararlarını ve bu kararların bedelini kendi gözlemlerinle anlamak. Bir protokol tasarlarken her alanın neden orada olduğunu yaz; bir hata bulduğunda, onu hangi girdiyle tetiklediğini kanıtla. Çözümü dışarıdan alma.
:::

### Proje 1 (★★): İHA yer istasyonu protokolünü güvenli hâle getirme

**Amaç:** Bölüm 31'deki telemetri ve komut protokolünü, bu bölümde öğrendiğin ilkelerle sertleştirmek: gizlilik, bütünlük, tekrar oynatma koruması ve anahtar türetme. Proje sonunda, bir ağ simülatöründe kayıp ve bozulma altında da doğru çalışan bir protokol olmalı.

**Beklenen davranış:** Simülatör saniyede 10 telemetri paketi üretir. Paketler AEAD ile şifrelenir; ek veri olarak sıra numarası ve paket türü bağlanır. Ana anahtar bir paylaşılan sırdan (ortak gizli değer) HMAC tabanlı bir türetmeyle iki ayrı anahtara ayrılır: biri şifreleme, biri komut kanalının doğrulaması için. Simülatör paketleri %10 oranında düşürür, %5 oranında bir bit bozar ve %5 oranında çoğaltır. Alıcı, kabul ettiği paketlerin sıra numaralarını ve red sebeplerini sayar. Komut kanalı Ed25519 ile imzalanır; komut, sıra numarası ile tekrar oynatılamaz.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Önce hangi alanın gizli, hangi alanın yalnızca doğrulanan olduğunu bir tabloya yaz. Anahtar türetme için sürüm ve bağlam bilgisini (örneğin "telemetri" ve "komut" etiketlerini) girdiye ekle; böylece aynı ana anahtardan türetilen iki anahtarın birbirine karışmadığını doğrula. Sıra numarasını alıcı tarafında kalıcı tut ve yeniden başlatmada ne olacağını tasarla. Simülatörde kayıp ve bozulmayı ayrı tohumlu üreteçlerle yap ki deneyler tekrarlanabilir olsun.

**Başarı kriterleri:**
- Simülatör %10 kayıp, %5 bit bozulması ve %5 çoğaltma ile 600 paket gönderdiğinde, hiçbir bozulmuş paket kabul edilmez (kabul sayısı, bozulan sayısından fazla değildir).
- Aynı paketin ikinci kez gelmesi, hiçbir durumda ikinci bir uygulama etkisi yaratmaz.
- Şifreli paketin ek verisinin (sıra numarası) değiştirilmesi her zaman reddedilir.
- Komut kanalında imzası geçersiz bir komut hiçbir zaman uygulanmaz; geçerli bir komut tam olarak bir kez uygulanır.

### Proje 2 (★★★): Bölüm 30 ve 31 ayrıştırıcıları için fuzzing çatısı

**Amaç:** Bu bölümdeki fuzzer'ı genelleştirip, Bölüm 30 ve 31'deki ayrıştırıcılar için her hedefin sözleşmesini açıkça tanımlayan, tekrarlanabilir ve bulunan hataları en küçük örneğe indiren bir çatı yazmak. Çatının amacı, bir ayrıştırıcıya yeni bir alan eklediğinde sessizce bir açık oluşmasını önlemektir.

**Beklenen davranış:** Her hedef, bir `(kabul_istisnalari, fonksiyon, tohumlar)` üçlüsüyle tanımlanır. Çatı, her hedef için sabit tohumlu N yineleme çalıştırır ve beklenmeyen istisnaları sınıflandırır. Bulunan her hata için en kısa yeniden üretici saklanır; bu üretici bir dosyaya yazılır ve sonradan tek başına çalıştırılabilir. Çatı, ayrıca Bölüm 31'deki çerçeve okuyucusunun parçalı okumada doğru çalıştığını, Bölüm 30'daki sunucunun ise her girdide tek bir yanıt yazdığını (kapanmadan) doğrulayan iki özel test içerir.

**Önerilen yaklaşım (ipucu):** Mutasyon fonksiyonunu küçük, ayrı ve test edilebilir bir modül olarak tut. En kısa örneği bulmak için basit bir küçültme (her seferinde bir parça silip hatanın hâlâ oluşup oluşmadığına bakma) yeterlidir; bu, kapsama yönlendirmeli bir araç değildir ama fikri anlamanı sağlar. Sonuçları CSV olarak yazan bir çıktı üret ve bu çıktıyı önceki çalışmalarla karşılaştır; böylece bir değişikliğin hata sayısını artırıp artırmadığını görürsün.

**Başarı kriterleri:**
- Çatı, bu bölümdeki özgün Bölüm 30 sunucusunda hatayı bulur ve sağlamlaştırılmış sürümde sıfır hata verir.
- Her bulunan hata için en kısa yeniden üretici dosyaya yazılır ve tek başına çalıştırıldığında aynı istisnayı üretir.
- Aynı tohumla iki çalıştırma bit bit aynı sonucu verir.
- Yeni bir hedef eklemek, mevcut hedeflerin kodunda değişiklik gerektirmez.

### Ek Alıştırmalar

Aşağıdaki problemlerin çözümü bu kitapta yok. Önce kâğıda, sonra editöre geç; yapay zekâ yasak. Zorluk etiketine göre sırala.

1. **★ — Çığ etkisi.** 8 bitlik bir girdinin her bitini tek tek değiştirip 8 farklı çıktı üretiyorsun. Çıktılar arasındaki ortalama farkın 4 bit olması, bir hash için neden yeterli değildir? Bu ölçümün sana neyi söyleyip neyi söylemediğini yaz.
2. **★ — Tuz.** İki kullanıcı aynı parolayı kullanıyor, ama tuzları aynı. Saldırgan veritabanı sızıntısından ne öğrenir? Tuzun tekrar kullanılmaması neden önemlidir?
3. **★ — Sabit zamanlı karşılaştırma.** `==` ile iki baytlık bir etiket karşılaştırmasında, ilk baytı yanlış olan bir etiket ile son baytı yanlış olan bir etiket aynı sürede mi döner? Bunun ölçülebilir bir fark yaratması için hangi koşullar gerekir?
4. **★★ — Nonce sayacı.** Bir sensör, AEAD nonce'unu bir sayaçtan üretiyor ve cihaz yeniden başlayınca sayaç sıfırlanıyor. Bu tasarım neden tehlikelidir ve düzeltme için iki yol öner.
5. **★★ — Tekrar oynatma penceresi.** Bir protokolde, sıra numarasının "pencere" içinde olan ama daha önce görülmemiş paketleri kabul etmek istiyorsun (kayıplı bir ağ için). Son gördüğün sıradan geriye doğru 64 paketlik bir pencere tanımla; pencerenin dışındaki bir paketi nasıl reddedersin?
6. **★★ — Kanarya neyi koruyor?** Yığın kanaryası, dönüş adresinden önce bir değer koyar. Bu değerin tahmin edilemez olması neden gereklidir? Kanaryanın koruyamadığı bir hata sınıfı var mı?
7. **★★ — Çerez kapsamı.** `Path=/admin` çerezi, `/admin/sil` yolunda gönderilir mi? `Path` bayrağı bir güvenlik sınırı mıdır? Cevabını yaz ve neden olduğunu açıkla.
8. **★★ — Yol normalleştirme.** Bir dosya sunucusu, istek yolunu `os.path.normpath` ile normalleştirip kök dizinin altında olup olmadığını `startswith` ile kontrol ediyor. Bu kontrolü geçen ama kökten çıkan bir yol tasarlayabilir misin? (Yalnızca kavramsal düzeyde yanıtla.) Düzeltme nedir?
9. **★★★ — Mülakat: boyut hesabı.** Bir fonksiyon `malloc(n * m)` ile iki boyutlu bir matris ayırıyor. `n` ve `m` kullanıcıdan geliyor. Bu hatayı ASan ve UBSan ile nasıl yakalarsın, düzeltmesi ne olur? (Mülakat)
10. **★★★ — Mülakat: parola saklama.** Bir ekip SHA-256'yı tuz ile birlikte kullanıyor ve "yeterince güvenli" diyor. Hangi üç ölçüt bunun yetersiz olduğunu gösterir? Bir kullanıcı yeni parola kurarken sistemin ne yapması gerekir? (Mülakat)
11. **★★★ — Mülakat: CSRF.** Bir API `POST /sil` isteğini yalnızca çerezle kimlik doğrular ve SameSite bayrağı yoktur. Bu API'ye karşı hangi saldırı yapılabilir, hangi üç savunma uygulanabilir ve bunların hangisi tek başına yeterlidir? (Mülakat)
12. **★★★ — Mülakat: ASLR ve sızıntı.** ASLR açık bir sistemde, bir hata yalnızca bellek adresi bilindiğinde kullanılabiliyor. Bu bilgi bir sızıntıyla elde edilirse hangi koruma bu durumu tek başına engeller? Hangi katmanlar hâlâ işe yarar? (Mülakat)

## Kod Okuma Egzersizi

Aşağıdaki kesitler, Python 3.12.10 standart kütüphanesinden alınmıştır. Kaynak yerel kurulumdan alındı ve resmi `v3.12.10` etiketindeki `Lib/secrets.py` ile satır satır aynıdır. `Lib/hmac.py` kesiti de aynı yerel kurulumdan alındı; birebir kopyadır, kısaltma yoktur.

Birinci kesit, `secrets.py` dosyasının içe aktarma satırlarıdır (17–18 ve 20). `compare_digest` fonksiyonu `hmac`'ten alınır; rastgele kaynak olarak `SystemRandom` seçilir.

```python
from hmac import compare_digest
from random import SystemRandom

_sysrand = SystemRandom()
```

İkinci kesit, jeton üreten `token_bytes` fonksiyonudur (33–45).

```python
def token_bytes(nbytes=None):
    """Return a random byte string containing *nbytes* bytes.

    If *nbytes* is ``None`` or not supplied, a reasonable
    default is used.

    >>> token_bytes(16)  #doctest:+SKIP
    b'\\xebr\\x17D*t\\xae\\xd4\\xe3S\\xb6\\xe2\\xebP1\\x8b'

    """
    if nbytes is None:
        nbytes = DEFAULT_ENTROPY
    return _sysrand.randbytes(nbytes)
```

Üçüncü kesit, `hmac.py` dosyasının `compare_digest` sağlayıcısını seçen bloktur (6–15).

```python
import warnings as _warnings
try:
    import _hashlib as _hashopenssl
except ImportError:
    _hashopenssl = None
    _functype = None
    from _operator import _compare_digest as compare_digest
else:
    compare_digest = _hashopenssl.compare_digest
    _functype = type(_hashopenssl.openssl_sha256)  # builtin type
```

**Sorular — cevaplamadan geçme:**

1. `token_bytes` `random.SystemRandom` nesnesinin `randbytes` metodunu çağırıyor. `SystemRandom` sınıfı rastgele baytları hangi kaynaktan alır? Bu kaynağın `random.Random` ile farkı nedir ve bunu `random` modülünün belgesinden doğrula.
2. `hmac.py`, `compare_digest` için iki yol tanımlıyor: `_hashlib` (OpenSSL) ya da `_operator` yedeği. Yedek yol neden vardır ve iki yolun da aynı güvenlik özelliğini taşıdığını nasıl kontrol edersin?
3. `token_urlsafe` sonuna `rstrip(b'=')` ekliyor. Base64 dolgusu (padding) neden jeton için gereksizdir ve bu işlem, çözümlemede hangi varsayımı değiştirir?
4. `token_bytes` varsayılan uzunluk olarak `DEFAULT_ENTROPY` kullanıyor. Bu sabit, bir jetonun gücü için neden tek başına bir ölçü değildir? Bölüm 32.3'teki tohum deneyiyle ilişkilendir.
5. `secrets` modülü `choice` ve `randbits`'i `_sysrand` üzerinden tanımlıyor. Bu tanımların `random.choice` ile aynı kaynağı kullanmadığını göstermek için hangi tek satırlık deneyi yaparsın?
6. `hmac.py`'deki `trans_5C` ve `trans_36` tabloları neden 256 elemanlıdır ve bunlar RFC 2104'teki hangi sabitlere karşılık gelir? Tabloların her girişinin neden tek tek hesaplandığını açıkla.

## Bölüm Özeti

- Güvenlik, tasarımın ilk gününden başlar. CIA üçlüsü, kimlik doğrulama, yetkilendirme ve inkâr edilemezlik birlikte bir hedef tanımlar; STRIDE ise her tehdidi bir özelliğe bağlar.
- Kendi kriptografik algoritmanı yazma. Hash'in çığ etkisi ölçülür; parola saklamada hız bir risktir, tuz ve yavaş bir KDF (scrypt) gerekir.
- CRC bir hata algılama kodudur, bütünlük değildir. HMAC anahtarlı bütünlük sağlar; sıra numarası ile tekrar oynatma engellenir ve karşılaştırma sabit zamanlı yapılır.
- AEAD şifrelemeyi ve doğrulamayı birlikte yapar; nonce tekrarı felakettir. İmza, anahtar yönetimiyle birlikte düşünülmelidir.
- TLS, sertifika zinciriyle kimliği ve geçici anahtar paylaşımıyla gizliliği sağlar. `verify=False` kimlik kısmını yok eder.
- C'de tampon taşması, serbest bırakılmış bellek, çift serbest bırakma, tamsayı taşması ve biçim dizesi hataları ASan, UBSan ve `-fanalyzer` ile görünür kılınır; düzeltmeler sınırı açıkça denetler.
- Derleyici ve işletim sistemi korumaları (kanarya, FORTIFY, NX, ASLR, PIE, RELRO) bir hatayı düzeltmez, kötüye kullanımını zorlaştırır. Hiçbiri tek başına yeterli değildir.
- Fuzzing, sözleşmeleri hedef bazında tanımlanmış bir mutasyon testidir. Bölüm 30 sunucusundaki tek baytlık hata, sözleşmenin ve sınıflandırmanın ne kadar önemli olduğunu gösterdi.

Bu bölümle Kısım VII, Ağ, tamamlandı. Bölüm 29'da katmanları, Bölüm 30'da HTTP ve DNS'i, Bölüm 31'de soketleri ve Bölüm 32'de güvenliği gördün. Bu dört bölüm, bir ağ uygulamasının baytlarından güvenliğine uzanan tek bir zincir kurar.

**Sonraki bölümde:** Bölüm 33 (İlişkisel Model) ile Kısım VIII, Veritabanı, başlıyor. Burada gördüğün güvenlik ilkeleri, veritabanına taşındığında da geçerlidir: en az ayrıcalık, parametreli sorgular ve bütünlük kısıtları. Veritabanı, verinin tutarlılığını ve güvenliğini bir şema düzeyinde sağlar.

::: mulakat
Aşağıdaki sorular cevapsızdır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. HMAC ile `H(anahtar ∥ mesaj)` biçiminde basit bir birleştirme arasındaki fark nedir? Neden HMAC'in iç içe yapısı gerekir?
2. Parola saklamada neden hızlı bir hash yetmez? Tuz neyi çözer ve neyi çözmez?
3. AEAD'de aynı anahtarla nonce'un iki kez kullanılması neden felakettir? Bu hatayı tasarımda nasıl önlersin?
4. TLS 1.3'te sertifika doğrulaması ile anahtar paylaşımı birbirinden nasıl ayrılır? İleriye dönük gizlilik ne demektir ve neden önemlidir?
5. `strncpy` neden güvenli bir kopya fonksiyonu sayılmaz? Hedef bir dizinin sonlandırılması için hangi koşul gerekir?
6. ASLR açıkken bir bellek hatası hâlâ kötüye kullanılabilir mi? Bu soruyu, koruma katmanlarının birbirini nasıl tamamladığını da kullanarak yanıtla.
7. Tek bir kötü biçimlendirilmiş istekle tüm bir sunucu nasıl durabilir? Bu hatayı fuzzing ile nasıl bulursun ve sözleşmeyi nasıl tanımlarsın?
8. Bir koruma açık, ama başka bir koruma kapalı: NX açık, PIE kapalı. Hangi risk kalır ve bunu azaltmak için hangi adımları atarsın?
:::
