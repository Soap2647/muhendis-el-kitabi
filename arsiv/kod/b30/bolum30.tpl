%% kisim_no: VII
%% kisim_ad: Ağ
%% bolum_no: 30
%% baslik: HTTP, DNS, DHCP

## Giriş: Bir tarayıcı adresi nasıl bulur?

Tarayıcıya `https://example.com` yazıp Enter'a bastığında iki şey peş peşe olur. Önce `example.com` adı bir IP adresine çevrilir. Sonra o adrese bir HTTP isteği gider ve sayfa geri döner. Bu iki adımın arkasında, sen bir sayfa açmadan çok önce yapılmış bir iş vardır: cihaz ağa katıldığında bir IP adresi, bir ağ geçidi ve bir DNS sunucusu almıştır. Bu üç parçanın her biri ayrı bir protokolün işidir. DHCP adresi dağıtır, DNS adı adrese çevirir, HTTP ise o adrese giden konuşmanın dilidir.

Mülakatlarda "tarayıcıya bir adres yazınca neler olur?" sorusu neredeyse klasiktir. Cevabı bilmek yetmez; her adımın hangi mesajla yapıldığını, o mesajın baytlarının nasıl dizildiğini ve hangi hatada ne göreceğini de söyleyebilmek gerekir. Bu bölüm o ayrıntıya iner. DNS sorgusunu bayt bayt kuracak, DHCP'nin dört adımlık konuşmasını inceleyecek, HTTP isteğini satır satır okuyacaksın.

Savunma sanayiinde bu bilgi doğrudan karşına çıkar. Bir yer istasyonu panelinin İHA telemetrisini tarayıcıda göstermesi, bir sensör düğümünün ölçümünü bir API'ye göndermesi, bir sistemin kendi ağ adreslerini ve adlarını yönetmesi bu protokollere dayanır. Bölüm 29'da IP ve TCP'yi gördün; burada o katmanların üstündeki uygulama protokollerine çıkıyoruz. Bölüm 31'de aynı konuşmayı soket API'siyle kendi kodunla kuracaksın.

Bu bölümde bir kuralı baştan koyuyoruz: HTTP ve DNS metin gibi görünür, ama ağ kartının gördüğü şey bayt dizisidir. Bu yüzden her protokol için en az bir kez ham baytları elle okuyacaksın. Ağ erişimi gereken yerlerde yalnızca herkese açık DNS çözümleyicileri (1.1.1.1 ve 8.8.8.8) ile example.com'a, okuma amaçlı ve az sayıda istekle gittik. Hiçbir siteye form gönderilmedi ve hiçbir kimlik bilgisi girilmedi.

::: not
Bu bölümdeki her çıktı, kitabın kendi kodundan bu bölüm yazılırken çalıştırılarak alındı. Ağa bağlı ölçümler (DNS ve HTTP gecikmeleri) makineye ve ağa göre değişir. Okurun öğreneceği şey sayıların kendisi değil, gecikmenin nereden geldiği ve nasıl ölçüleceğidir. Ölçüm ortamı 30.14'te anlatılır.
:::

## 30.1 Ad çözümleme: neden DNS var?

Ağ katmanı IP adresleriyle çalışır. Bölüm 29'da gördüğün gibi bir IP paketi, bir hedef adres taşır ve yönlendiriciler bu adrese bakarak paketi ileterek ilerler. İnsanlar ise `example.com` gibi adları hatırlar. Adres ile adı ayırmanın iki somut faydası var. Birincisi, bir sunucu başka bir veri merkezine taşındığında adı değiştirmeden adresi güncelleyebilirsin. İkincisi, tek bir ada birden çok adres bağlayabilirsin; yük dağıtımı ve yedeklilik bu sayede mümkün olur.

Bu ayrımı yapan sistemin adı DNS'tir (Domain Name System). Başlangıçta ARPANET'te her makinenin kopyaladığı tek bir `HOSTS.TXT` dosyası vardı. Ağ büyüdükçe bu dosyanın yönetimi imkânsız hâle geldi; bugünkü hiyerarşik ve dağıtık sistem bu yüzden tasarlandı. Bir telefon rehberi gibi düşünebilirsin: adını bilirsin, numarayı rehberden alırsın, numara değişirse rehberi güncelleyen yetkili bir yer vardır.

Buradaki en önemli sonuç şudur: ad çözümlemesi de bir ağ isteğidir. Tarayıcı, HTTP isteğini göndermeden önce bir DNS isteği yapar ve bu istek bir gidiş-dönüş süresi (RTT) harcar. Sayfa yükleme süresinin ilk parçası çoğu zaman budur. Bunu 30.14'te ölçeceğiz.

## 30.2 Hiyerarşi: kök, TLD ve yetkili sunucular

Bir alan adı sağdan sola okunur. `www.example.com.` adının sonundaki nokta, adın en üstteki, yani kök (root) düğümünü gösterir. DNS ağacı üç seviyede düşünülebilir:

- **Kök (.)**: Dünyada 13 mantıksal kök sunucu adı vardır (a.root-servers.net'ten m.root-servers.net'e). Kök sunucular, bir alan adının hangi üst düzey bölgeye ait olduğunu bilir; "com alanını kim yönetiyor?" sorusunu cevaplar, adın kendisini bilmez.
- **Üst düzey alan (TLD)**: `com`, `net`, `org`, `tr` gibi. Her TLD'nin kendi yetkili sunucuları vardır ve kendi altındaki adları bilir.
- **Yetkili (authoritative) sunucu**: `example.com` bölgesinin gerçek kayıtlarını tutan sunucu. Yanıtı bu sunucu verir.

Şekil 30.1 bu ağacı ve bir sorgunun hangi düğümlere dokunabileceğini gösterir.

![Şekil 30.1: DNS hiyerarşisi. Kök, com TLD'si ve example.com yetkili sunucusu; çözümleyici önce kökü sorar, sonra alt düzeylere iner.](gorseller/b30_dns_hiyerarsi.png)

Telefonun tek bir DNS isteği yaptığını düşünebilirsin, ama arkada bir çözümleyici (resolver) çalışır. Burada iki çalışma biçimi ayırt edilir. **Özyinelemeli (recursive)** çözümleyici, istemci adına tüm zinciri kendisi yürütür ve sonunda hazır cevabı döner. İstemci tek bir soru sorar ve RD (Recursion Desired) bayrağını açar. **Yinelemeli (iterative)** sorguda ise sunucu cevabın kendisini değil, bir sonraki sorulacak sunucunun adresini döner. Bu tür bir cevaba **yönlendirme (referral)** denir. Çözümleyici, kök sunucudan gelen yönlendirmeyle com sunucularına, onların yönlendirmesiyle yetkili sunucuya gider.

![Şekil 30.2: Özyinelemeli çözümleme zaman çizelgesi. Çözümleyici adına kök, TLD ve yetkili sunucular sırayla sorulur; cevap istemciye geri döner.](gorseller/b30_dns_cozumleme.png)

Şekil 30.2'de bir sorgunun zincirini görüyorsun. Bu zincirin uzunluğu sabit değildir, çünkü çözümleyici her adımın cevabını önbelleğe alır. Bir sonraki sorguda kök ya da com sunucularına gitmesine gerek kalmayabilir. Bu yüzden 30.3'teki önbellekleme ve TTL kavramları, zincirin pratikte nasıl kısaldığını anlatır.

Bir güvenlik notu şimdiden: çözümleyici, sorduğu sorunun cevabını güvenmeden önce kabul ederse sahte bir cevap önbelleğe girebilir. Bu tehdit ve DNSSEC'in ona karşı koyma biçimi 30.4'te kısaca anlatılır; ayrıntısı Bölüm 32'dedir.

## 30.3 Kayıt türleri, TTL ve önbellekleme

Bir DNS yanıtı **kayıt (resource record)** listesinden oluşur. Her kayıt bir ad, bir tür, bir sınıf (neredeyse her zaman `IN`, yani internet), bir TTL ve bir veri alanı taşır. Tabloda sık kullanılan türleri görüyorsun. Değerler, bölümü yazarken yapılan canlı sorgulardan alındı; bugün farklı olabilir.

| Tür | Ne taşır | Örnek (ölçüm anında) |
|---|---|---|
| A | IPv4 adresi | example.com → 104.20.23.154 |
| AAAA | IPv6 adresi | example.com → 2606:4700:10::6814:179a |
| CNAME | Bir adın başka bir ada takma adı | www.github.com → github.com |
| MX | Posta sunucusu (öncelik + ad) | example.com → "0 ." (posta kabul etmez) |
| NS | Bölgenin yetkili sunucuları | example.com → hera.ns.cloudflare.com |
| TXT | Serbest metin (SPF, doğrulama anahtarı) | example.com → TXT kayıtları var |
| PTR | IP adresinden ada (ters arama) | 1.1.1.1 → one.one.one.one |

CNAME'in davranışını bilmek önemlidir. `www.github.com` sorgulandığında yanıtta önce bir CNAME kaydı, sonra o adın A kaydı gelir. Çözümleyici zinciri kendisi izler; istemci iki kaydı da görür. MX'in "0 ." değeri ise tuhaf görünür: bu, RFC 7505'in tanımladığı "posta kabul etmiyorum" (null MX) biçimidir ve kök adına işaret eder.

Her kaydın **TTL** (Time To Live) alanı saniye cinsinden, o kaydın önbellekte ne kadar yaşayabileceğini söyler. Ölçümlerimizde aynı kaydı kısa aralıklarla sorguladığımızda TTL değerinin azaldığını gördük: örneğin 1.1.1.1 için aynı A kaydı bir sorguda 63, daha sonraki bir sorguda 50 saniye döndü. Bu, çözümleyicinin önbelleğindeki kalan süredir, kaydın "orijinal" TTL'si değildir. Yani önbellek bir geri sayım sayacı gibi çalışır. TTL dolunca çözümleyici kaydı yeniden sorar ve yeni bir TTL alır.

TTL seçimi bir ödünleşimdir. Uzun TTL, sorgu yükünü azaltır ama bir değişikliğin yayılmasını geciktirir. Kısa TTL, değişikliği hızlı yayar ama her seferinde ağ isteği doğurur. Bir sunucuyu taşıyacaksan, eski TTL'yi taşımadan önce düşürmek bu yüzden bilinen bir pratiktir.

Önbellek tek bir yerde durmaz. Tarayıcının kendi önbelleği, işletim sisteminin DNS istemcisi ve ISS'nin ya da 1.1.1.1 gibi bir genel çözümleyicinin önbelleği vardır. Bir alan adı hiç yoksa (NXDOMAIN), çözümleyici bu olumsuz cevabı da bir süre önbelleğe alabilir; ayrıntısı, SOA kaydındaki değerlerle belirlenir (genel bilgi).

### Yerel adlandırma: /etc/hosts ve /etc/resolv.conf

Ağa sorulmadan önce cihazın kendi yerel kuralları vardır. Linux'ta iki dosya bunu belirler. `/etc/hosts` elle yazılmış ad-adres eşlemelerini tutar. `/etc/resolv.conf` ise hangi DNS sunucusuna sorulacağını ve hangi arama alanlarının (search) deneneceğini söyler. Hangi kaynağın önce bakılacağı `/etc/nsswitch.conf` içindeki `hosts:` satırında belirlenir.

WSL2 üzerinde bu dosyaların gerçek içeriği şöyleydi :


@@CIKTI cikti/wsl_dns.txt "grep -v -e ^# /etc/resolv.conf /etc/hosts"@@

Bu çıktıda üç şey dikkat çekiyor. `nameserver 10.255.255.254` adresi WSL'nin Windows tarafındaki DNS aracısıdır; WSL, sorguları Windows'a devreder. Dosyanın başındaki açıklama, bu dosyanın WSL tarafından otomatik üretildiğini söyler. `/etc/hosts` dosyasında ise yalnızca yerel adlar vardır; example.com yoktur, yani o ad DNS'ten çözülecektir. Ayrıca `/etc/nsswitch.conf` içindeki `hosts: files dns` satırı, önce `/etc/hosts` dosyasına bakılacağını, bulunmazsa DNS'e gidileceğini gösterir.

Bu sıralama bir uyarı da içerir: `/etc/hosts` içine yazdığın bir satır, yerel ad çözümünde genel DNS'in önüne geçer. Tuhaf bir "adres yanlış" hatasıyla karşılaşırsan ilk bakacağın yerlerden biri budur.

Aynı sorgunun iki ayrı sonucu da dikkat çekicidir. Aşağıdaki çıktı, WSL'nin çözümleyicisi üzerinden example.com'un adres listesini gösteriyor. Sıralama, çözümleyici ve istemci kütüphanesinin seçimine göre değişebilir; bu yüzden bir adresin "ilk" olması bir kural değildir.


@@CIKTI cikti/wsl_getent.txt "getent ahosts example.com | head -3"@@

## 30.4 DNS mesaj biçimi: baytlardan okumak

DNS sorguları ve yanıtları aynı biçimdedir ve çoğunlukla UDP 53 numaralı porttan gider. Mesaj üç bölümden oluşur: 12 baytlık sabit bir başlık, soru bölümü ve yanıt bölümleri (yanıt, yetki ve ek kayıtlar). Başlık, kaç soru ve kaç kayıt geldiğini sayılarla söyler. Bu sayede ayrıştırıcı, her bölümün nerede bittiğini bilir.

Başlıktaki alanlar şunlardır. **ID** (2 bayt), istek ve yanıtı eşleştirmek için kullanılan 16 bitlik bir kimliktir. **Bayraklar** (2 bayt), QR (sorgu mu, yanıt mı), RD (özyinelemeli iste), RA (özyinelemeli destekleniyor), AA (yetkili yanıt) ve RCODE (hata kodu, 0 = hata yok, 3 = NXDOMAIN) gibi tek bitlik alanları taşır. Son dört 16 bitlik sayaç ise QDCOUNT, ANCOUNT, NSCOUNT ve ARCOUNT alanlarıdır.

Şekil 30.3, bu alanların baytlardaki yerini gösterir. Buradaki bayt sayıları, sorgu sırasında gerçekten gönderdiğimiz paketin uzunluğuyla birebir tutar.

![Şekil 30.3: DNS mesajının bayt düzeni. Başlık 12 bayt; soru bölümünde ad, tür ve sınıf; yanıt bölümünde kayıt alanları. Çok baytlı sayılar ağ bayt sırasıyla (big-endian) yazılır.](gorseller/b30_dns_mesaj.png)

Ad alanı, DNS'in en ilginç yanıdır. Bir adı etiketlerine ayırır ve her etiketi uzunluğuyla birlikte yazar: `example.com` için 7 `example` 3 `com` 0 dizisi (son 0 ad sonunu işaretler). Bu sayede bir ayrıştırıcı, etiket uzunluğu kadar okuyup durabilir. Bir etiket en fazla 63 bayt olabilir.

Aynı ad bir yanıtta birden çok kez geçer: önce soruda, sonra her kaydın kendi adında. DNS bunu **ad sıkıştırma (name compression)** ile azaltır. Bir ad yerine, mesajın başından itibaren bir ofsete işaret eden iki baytlık bir **işaretçi** yazılır. İşaretçinin ilk iki biti `11` olur ve kalan 14 bit ofseti taşır. Yani ilk bayt `0xC0` ile başlarsa, ikinci baytla birlikte ofset `((ilk & 0x3F) << 8) | ikinci` formülüyle bulunur. Şekil 30.4 bunu gerçek bir yanıtta gösterir.

Aşağıdaki kod, bu mesaj biçimini sıfırdan uygular: sorgu kuran, ad alanını ve işaretçileri çözen, yanıtı ayrıştıran bir programdır. Yalnızca standart kütüphaneyi kullanır; `socket` modülü sadece UDP datagramı göndermek ve almak için vardır. Soket API'sinin ayrıntısı Bölüm 31'dedir; burada yalnızca iki çağrının ne yaptığına bakman yeterli.

Önce programın ilk yarısı: sorgu kurma ve ad alanı çözme.

@@KOD b30_1_dns_ham.py 1 28 python@@

Aşağıda ad çözme fonksiyonu. İşaretçi gelirse ana akış bir kez kaydedilir, ardından hedef ofsetten okuma devam eder. Sonsuz döngüye karşı sayaç koyduk: kötü niyetli bir yanıt iki işaretçinin birbirine dönmesiyle çözümleyiciyi kilitleyebilir.

@@KOD b30_1_dns_ham.py 29 50 python@@

Kayıt verisi (RDATA) tipe göre yorumlanır. A kaydı dört bayt bir IPv4 adresidir; `inet_ntop` onu okunabilir hâle getirir. CNAME, NS ve MX içindeki adlar da işaretçi içerebilir, bu yüzden onları da `ad_coz` ile, tüm mesajın başından okuyarak çözeriz. TXT gibi diğer türleri şimdilik ham onaltılık metin olarak bırakıyoruz; TXT'nin uzunluk önekli dizilerini çözmek bölümün alıştırmalarındadır.

@@KOD b30_1_dns_ham.py 51 82 python@@

Son kısım sorguyu gönderir, yanıtı alır ve sonucu yazdırır. Yanıtın ham baytlarını da onaltılık olarak gösteriyoruz; böylece her alanı bayt bayt karşılaştırabilirsin. Kimlik değeri sabit (`0x1A2B`) tutuldu; sonuçlar yalnızca TTL ve gecikme açısından değişir.

@@KOD b30_1_dns_ham.py 83 114 python@@

Programı 1.1.1.1 çözümleyicisine example.com A sorgusuyla çalıştırdığımızda çıktı şuydu. Sorgu 29 bayt, yanıt 61 bayt; yanıt başlığındaki bayrak `0x8180` (QR=1, RD=1, RA=1, RCODE=0) ve ANCOUNT=2 ile iki A kaydı geldi:


@@CIKTI cikti/b30_1.txt "python b30_1_dns_ham.py example.com 1.1.1.1"@@

Son satır, işletim sisteminin kendi çözümleyicisinin (`socket.getaddrinfo`) verdiği adres listesiyle birebir aynıdır. Bu karşılaştırma, ayrıştırıcının doğruluğunu kanıtlamanın en ucuz yoludur: kendi yazdığın çözümleyici, sistemin çözümleyicisiyle aynı cevabı veriyorsa, ikisi de büyük olasılıkla doğrudur.

![Şekil 30.4: Ad sıkıştırma işaretçisi. Yanıt kaydının adı c0 0c baytlarıdır; ofset 12'deki soru adına geri döner. Ofset 0x0C = 12.](gorseller/b30_dns_isaretci.png)

### DNS güvenliği (kısa)

DNS tasarlandığında kimlik doğrulama yoktu. Bu, iki temel tehdide kapı açar. Birincisi **önbellek zehirleme**: bir saldırgan, çözümleyicinin beklediği bir sorguya sahte bir yanıt yetiştirirse, yanlış adres önbelleğe girebilir. Bu saldırıyı zorlaştıran şey, yanıtın ID alanının (16 bit) ve sorgunun kaynak portunun tahmin edilmesi gerekliliğidir. 2008'de yayımlanan bir zafiyet, bu alanların yetersiz rastgeleliğinin ne kadar tehlikeli olabileceğini gösterdi ve kaynak portu rastgeleleştirmesi yaygınlaştı. İkincisi **gizlilik**: klasik DNS sorguları açık metindir, yani ağdaki herkes hangi sitelere gittiğini görebilir.

Savunmalar iki yönde gelişti. DNSSEC, kayıtları dijital imzalarla korur (RRSIG kayıtları ve DNSKEY, DS gibi anahtar kayıtları); bu, yanıtın bütünlüğünü ve kaynağını doğrulamaya yarar, ama sorguyu gizlemez. Gizlilik için DoT (TLS üzerinden DNS, TCP 853) ve DoH (HTTPS üzerinden DNS, RFC 8484) kullanılır. Bu konuların kriptografik ayrıntıları Bölüm 32'de işlenir.

## 30.5 DHCP: IP adresi nasıl dağıtılır?

Bir cihaz ağa ilk bağlandığında elinde bir IP adresi yoktur. Kaynak adresini 0.0.0.0 olarak kullanabilir, ama hedef adresi bilmez. DHCP (Dynamic Host Configuration Protocol, RFC 2131) bu boşluğu bir yayın (broadcast) konuşmasıyla doldurur. İstemci UDP 68 numaralı porttan, sunucu UDP 67 numaralı porttan konuşur.

Konuşma dört mesajdan oluşur ve adına DORA denir: **D**iscover, **O**ffer, **R**equest, **A**ck. Şekil 30.5'te akış ve zamanlayıcılar görünüyor.

![Şekil 30.5: DHCP DORA akışı. İstemci yayınla keşif yapar, sunucu teklif eder, istemci seçimini yayınlar, sunucu kira onayını gönderir. T1 ve T2 yenileme zamanlarını gösterir.](gorseller/b30_dhcp_dora.png)

Adım adım: istemci, ağda bir DHCP sunucusu olup olmadığını **DISCOVER** ile sorar. Bu mesaj tüm ağa yayınlanır. Bir veya birden çok sunucu **OFFER** ile bir adres önerir. Teklifte önerilen IP (yiaddr alanı), kira süresi ve ağ parametreleri bulunur. İstemci bir teklifi seçer ve **REQUEST** ile bunu yayınlar; bu mesajda seçilen sunucunun kimliği yer alır, böylece diğer sunucular teklifini geri çeker. Son olarak seçilen sunucu **ACK** ile kiralamayı onaylar.

Bir DHCP sunucusunun verdiği tipik parametreler şunlardır:

| Parametre | Ne işe yarar | DHCP seçeneği |
|---|---|---|
| IP adresi | Cihazın kendi adresi (yiaddr) | alan, seçenek değil |
| Alt ağ maskesi | Hangi adreslerin yerel olduğunu söyler | 1 |
| Varsayılan ağ geçidi | Yerel dışı trafiğin çıkacağı yönlendirici | 3 |
| DNS sunucusu | Ad çözümlemesinin soracağı sunucu | 6 |
| Kira süresi | Adresin kaç saniye geçerli olduğu | 51 |
| Sunucu kimliği | Hangi sunucunun kiraladığı | 54 |
| Mesaj türü | DISCOVER, OFFER, REQUEST, ACK… | 53 |

Kira süresi, adresin ne kadar kullanılabileceğini belirler. Kiranın yarısında (T1 = kira/2) istemci aynı sunucuya tek başına bir REQUEST göndererek kiralamayı yeniler. Yanıt gelmezse, kiranın yüzde 87,5'inde (T2) başka sunuculara yayın yapar. Kira tamamen biterse istemci adresi bırakmak zorundadır.

Pratikte sunucu ile istemci arasında her zaman dört mesaj olmayabilir: sunucu bir NAK göndererek isteği reddedebilir ya da istemci bir DECLINE ile adresin çakıştığını bildirebilir. Bu ayrıntılar RFC 2131'de tanımlıdır.

### DHCP paketinin alanları

DHCP mesajı, BOOTP'den miras kalan sabit uzunlukta bir başlıkla başlar. Bu başlık 236 bayttır ve sırasıyla şu alanları taşır: op (1 bayt, istek ya da yanıt), htype ve hlen (donanım türü ve adres uzunluğu), hops, xid (işlem kimliği, 4 bayt), secs, flags (en yüksek bit yayın yanıtı istendiğini söyler), ciaddr (istemcinin mevcut adresi), yiaddr (sunucunun önerdiği adres), siaddr, giaddr (rölenin adresi), chaddr (istemcinin donanım adresi, 16 bayt), sname ve file (eski, genelde boş alanlar). Başlıktan sonra dört baytlık bir **sihirli çerez** (99.130.83.99, yani 0x63825363) gelir ve bunun ardından değişken uzunluklu seçenekler (TLV: tür, uzunluk, değer) sıralanır. Seçenek listesi 255 (END) ile biter.

Bu bölümde gerçek bir DHCP paketi göndermedik. Bir DHCP sunucusunun yanıtlarını taklit etmek, ağdaki gerçek cihazların adreslerini bozabilir. Onun yerine çevrimdışı bir OFFER paketi kuran ve ayrıştıran bir program yazdık; bu sayede alanların yerlerini ölçebilirsin.

@@KOD b30_7_dhcp_sema.py 1 20 python@@

Paketi kurma fonksiyonunda sabit başlık tek bir `struct.pack` çağrısıyla yazılır. Biçim dizesindeki her karakter bir alanın türünü söyler: `B` bir bayt, `I` dört bayt, `H` iki bayt, `4s` dört baytlık bir dizi. Adres alanlarını bu yüzden `4s` ile yazıyoruz; bunları tamsayı olarak yazmak yanlış olurdu.

@@KOD b30_7_dhcp_sema.py 21 41 python@@

Ayrıştırıcı, sabit başlığın ilk 12 baytını okur, sihirli çerezi kontrol eder ve seçenekleri TLV olarak dolaşır. Her seçenek bir `kod` ve `uzunluk` taşır; PAD (0) baytları atlanır, END (255) görünce durulur.

@@KOD b30_7_dhcp_sema.py 42 68 python@@

Son kısım, örnek paketi kurup ayrıştırır ve alanları yazdırır:

@@KOD b30_7_dhcp_sema.py 69 78 python@@

Programın çıktısı, offer'ın alanlarını ve paketin ilk 32 baytını gösterir:


@@CIKTI cikti/b30_7.txt "python b30_7_dhcp_sema.py"@@

Çıktıdaki `op = 2` BOOTREPLY anlamına gelir; sunucudan istemciye giden bir mesajdır. Paket 274 bayt: 236 bayt sabit başlık, 4 bayt sihirli çerez ve 34 bayt seçenek. `xid` alanı, istemcinin isteğiyle eşleşmek için kullanılır. Bu kodun son satırları, `ayristir` fonksiyonunun DHCP seçeneklerini gerçekten okuduğunu gösterir.

### Gömülü cihaz: statik IP mi, DHCP mi?

Bir STM32 kartı ile Ethernet üzerinden veri gönderen bir cihazda iki seçenek vardır. DHCP, cihazı herhangi bir ağa takmayı kolaylaştırır; ağ yöneticisi adresi kendisi dağıtır. Ancak adres değişebilir; bu, telemetri sunucusunda cihazı izlemeyi zorlaştırır. Statik IP ise adresi sabitler ve kolay izlenmesini sağlar, ama her ağda adresin elle ayarlanmasını, çakışmaların önlenmesini gerektirir. Pratikte sık kullanılan bir yaklaşım, sunucu ve ağ geçidi için statik adres, saha cihazları için DHCP kullanmaktır. Hangisinin seçileceği ağın büyüklüğüne ve izleme gereksinimine bağlıdır; EV Dashboard gibi bir projede bu karar, verinin hangi adrese gideceğini doğrudan etkiler.

## 30.6 HTTP/1.1: istek ve yanıtın anatomisi

HTTP (HyperText Transfer Protocol), istemci-sunucu modelinde çalışan bir uygulama protokolüdür. İstemci bir **istek** gönderir, sunucu bir **yanıt** döner. Protokol metin tabanlıdır: başlık satırları ASCII karakterlerdir ve her satır CRLF (`\r\n`) ile biter. HTTP **durumsuz (stateless)** tasarlanmıştır: her istek kendi başına anlaşılmalıdır ve sunucu iki istek arasında bir durumu hatırlamak zorunda değildir. Oturum bilgisi gerektiğinde bunu çerezlerle taşırız (30.10). Bugünkü tanımlar RFC 9110 (anlam) ve RFC 9112 (HTTP/1.1 mesaj sözdizimi) belgelerinde yer alır.

Şekil 30.6, bir isteğin ve yanıtın hangi parçalardan oluştuğunu gösterir.

![Şekil 30.6: HTTP istek ve yanıt anatomisi. Başlangıç satırı, başlıklar, boş satır ve gövde; istekte gövde genelde yoktur, yanıtta ise içerik buradadır.](gorseller/b30_http_anatomi.png)

İstek satırı üç parçadan oluşur: yöntem, istek hedefi (genelde yol) ve sürüm. Örneğin `GET /ornek/not.txt HTTP/1.1`. Yanıt satırı ise sürüm, durum kodu ve kısa bir açıklamadır: `HTTP/1.1 200 OK`. Başlıklar `ad: değer` biçimindedir ve adları büyük-küçük harfe duyarsızdır. Başlıkların bittiği yer, tek bir boş satırla (`\r\n\r\n`) işaretlenir. Bu boş satırdan sonra gelen her şey gövdedir.

HTTP/1.1'de her istekte bir **Host** başlığı zorunludur. Bunun nedeni, tek bir IP adresinin birden çok siteyi barındırabilmesidir (sanal sunucu). Sunucu, hangi siteyi istediğini bu başlıktan öğrenir.

### Yöntemler ve idempotentlik

Yöntem, isteğin ne yapmak istediğini söyler. Yaygın olanlar aşağıda:

| Yöntem | Anlamı | Güvenli mi? | İdempotent mi? |
|---|---|---|---|
| GET | Kaynağı oku | Evet | Evet |
| HEAD | GET gibi, ama yalnızca başlıklar | Evet | Evet |
| POST | Kaynağa yeni bir şey gönder (oluştur, işle) | Hayır | Hayır |
| PUT | Kaynağı verilen içerikle değiştir (yerine koy) | Hayır | Evet |
| PATCH | Kaynağı kısmen değiştir | Hayır | Hayır |
| DELETE | Kaynağı sil | Hayır | Evet |

**Güvenli (safe)** yöntemler sunucunun durumunu değiştirmemesi beklenen yöntemlerdir. **İdempotent** bir yöntem, aynı isteği bir kez ya da on kez gönderdiğinde sonuç durumun aynı olmasını sağlar. `DELETE /kayit/42` iki kez gönderilirse, ikinci seferde kayıt zaten silinmiştir; son durum aynıdır. `POST /kayit` ise iki kez gönderildiğinde iki kayıt oluşabilir. Bu fark, bir bağlantı kesilip istemcinin isteği yeniden göndermesi gerektiğinde önemlidir: idempotent olmayan bir isteği güvenle tekrar gönderemezsin.

### Durum kodları

Durum kodunun ilk rakamı sınıfı belirler. 1xx bilgilendirme (geçici), 2xx başarı, 3xx yönlendirme ya da önbellek doğrulaması, 4xx istemci hatası, 5xx sunucu hatası demektir.

| Kod | Anlamı | Ne zaman görürsün |
|---|---|---|
| 200 | OK | İstek başarılı, gövde var |
| 201 | Created | Yeni kaynak oluşturuldu |
| 204 | No Content | Başarılı, ama gövde yok |
| 301, 308 | Kalıcı yönlendirme | Adres kalıcı olarak taşındı |
| 302, 307 | Geçici yönlendirme | Geçici başka adres |
| 304 | Not Modified | Önbellekteki kopya hâlâ geçerli (30.9) |
| 400 | Bad Request | İstek sözdizimi hatalı |
| 401, 403 | Yetkisiz, yasak | Kimlik doğrulama ya da yetki eksik |
| 404 | Not Found | Kaynak yok |
| 405 | Method Not Allowed | Yöntem bu kaynakta desteklenmiyor |
| 429 | Too Many Requests | İstek sınırı aşıldı |
| 500, 502, 503, 504 | Sunucu hataları | Sunucu tarafında sorun; geçit ve zaman aşımı hataları dâhil |

Durum kodu tek başına ayrıntı vermez. Bir 500 hatası çoğu zaman sunucunun günlüğünde bir istisna demektir; bir 404 bazen yol yazım hatası, bazen yanlış bir yönlendirme kuralıdır. Bu yüzden durum kodunu, başlıklar ve gövdeyle birlikte okumak gerekir.

## 30.7 Başlıklar, gövde ve chunked aktarım

Gövdenin ne kadar olduğunu bilmek gerekir; aksi halde istemci bağlantının ne zaman bittiğini bilemez. HTTP iki yol sunar. Gövdenin boyutu baştan belliyse **Content-Length** başlığı, bayt cinsinden uzunluğu söyler. Boyut önceden bilinmiyorsa, örneğin sunucu sayfayı üretirken bir yandan gönderiyorsa, **Transfer-Encoding: chunked** kullanılır.

Chunked gövde, parçalardan oluşur. Her parça önce boyutunu onaltılık sayı olarak, sonra CRLF ile yazılır; ardından veri ve bir CRLF gelir. Gövdenin sonu boyutu `0` olan bir parçayla işaretlenir ve bundan sonra gelen boş satır mesajı kapatır. Biçim şöyledir:

```term
4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n
```

Bu gövde üç parçadan oluşur; ilk ikisi Wikipedia kelimesini böler. Boyut satırlarındaki `;` sonrası **chunk-extension** alanıdır ve nadiren kullanılır. Aşağıdaki kod bu biçimi çözer. Programdaki örnek, HTTP belgelerinde sık anılan Wikipedia in chunks. örneğidir.

@@KOD b30_3_chunked.py 1 30 python@@

İkinci yarı, başlıkları ayrıştırır (ad ve değer, küçük harfe çevrilerek) ve chunked çözücüyü bir ana akışa bağlar.

@@KOD b30_3_chunked.py 31 52 python@@

Programı çalıştırdığımızda, ilk çıktı normal chunked gövdenin nasıl açıldığını, ikinci çıktı ise bozuk bir gövdeyi nasıl reddettiğini gösterir:


@@CIKTI cikti/b30_3.txt "python b30_3_chunked.py"@@

Hata satırı önemlidir. Parça boyutu "5" dedi ama veri "abc" ile bitti ve parçanın sonunda CRLF bulunamadı. Gerçek bir ağda bu, bağlantının ortada kesilmesi ya da yanlış bir sunucu uygulamasının işareti olabilir. Ayrıştırıcının bunu sessizce geçmemesi, hataları gizlememenin bir örneğidir.

Gövdesiz mesajlarda (304 gibi) ya da yalnızca başlık isteyen HEAD yanıtlarında gövde hiç yoktur. Bu yüzden ayrıştırıcılar önce durum koduna, sonra başlıklara bakar.

## 30.8 Kalıcı bağlantılar (keep-alive) ve bağlantı maliyeti

Her HTTP isteği, eskiden bir TCP bağlantısı açıp kapatmak demekti. TCP bağlantısı kurmak bir üçlü el sıkışma gerektirir ve bu, bir gidiş-dönüş süresi (RTT) harcar. Sonra şifreli bağlantı için TLS el sıkışması gelir; TLS 1.3'te bu da genelde bir RTT'dir (TLS 1.2'de iki). Yani her isteğe iki ya da üç RTT ekleniyordu.

**Kalıcı bağlantı (keep-alive)** bunu tekrarlamamak içindir. HTTP/1.1'de bir bağlantı, aksi söylenmedikçe kalıcıdır; `Connection: close` başlığı bağlantının istek sonunda kapanacağını söyler. HTTP/1.0'da ise varsayılan kapanmaktı, kalıcılık açıkça istenmeliydi.

Şekil 30.7, iki yaklaşımın zaman çizelgesini karşılaştırır.

![Şekil 30.7: Her istekte yeni bağlantı ile kalıcı bağlantının karşılaştırması. Üç istek üç el sıkışma gerektirirken kalıcı bağlantıda tek el sıkışma yeter.](gorseller/b30_keepalive.png)

Kalıcı bağlantının bir bedeli de vardır: sunucu açık bağlantıları bellekte tutar. Bu yüzden sunucular boşta bekleyen bağlantıları belli bir süre sonra kapatır. Bizim minimal sunucumuzda bu süre 5 saniyedir (30.11'deki kodda `settimeout(5.0)`). Bir de **HTTP pipelining** vardır: istemci, yanıt beklemeden birden çok istek gönderir. Ama yanıtların sırayla dönmesi gerektiği için, ilk yanıt yavaşsa arkadakiler de bekler; bu, başlı başına bir engelleme türüdür. Tarayıcılar pipelining'i pratikte kullanmaz; HTTP/2 bu sorunu farklı bir yolla çözer (30.13).

## 30.9 Önbellek: Cache-Control, ETag ve 304

Bir sayfayı her seferinde baştan indirmek gereksizdir. HTTP, önbelleğe alınmış bir kopyanın hâlâ geçerli olup olmadığını kontrol etmek için iki mekanizma sunar.

Birincisi **Cache-Control** başlığıdır. `max-age=60` yanıtın 60 saniye boyunca taze kabul edilebileceğini söyler; bu süre içinde istemci ağa hiç çıkmadan kopyayı kullanabilir. `no-cache` ise her kullanımda doğrulama ister. `no-store` hiçbir yerde saklamamayı söyler; hassas veriler için kullanılır. `public` ve `private` ise paylaşılan önbelleklerin (CDN gibi) yanıtı saklayıp saklayamayacağını belirler.

İkincisi **doğrulama**dır. Yanıt, içeriğin bir parmak izini taşıyan **ETag** başlığıyla gelir. Süre dolduğunda istemci aynı kaynağı, son bildiği ETag'i `If-None-Match` başlığıyla sorar. İçerik değişmediyse sunucu gövdesiz bir **304 Not Modified** döner ve istemci kendi kopyasını kullanır. Değiştiyse normal bir 200 ile yeni içeriği gönderir.

Şekil 30.8, bu akışı gösterir.

![Şekil 30.8: ETag ve 304 akışı. Taze süre içinde ağ isteği yoktur; süre dolunca koşullu istek gider ve içerik değişmediyse yalnızca başlık döner.](gorseller/b30_etag_akisi.png)

Minimal sunucumuz (30.11) her dosya için ETag'i içeriğin SHA-256 özetinin ilk 16 hanesinden üretir. İçerik değişmezse ETag aynı kalır; bu yüzden `If-None-Match` ile gelen istek 304 ile karşılanır. Önemli bir ayrıntı: 304 yanıtı da `Cache-Control` taşımalıdır. Aksi halde istemci, yenilenen kopyanın ne kadar taze olduğunu bilemez. Bu, RFC 9111'in istediği bir davranıştır ve önbellek kodunu yazarken bunu bir hata olarak yaşayabilirsin. Solved Örnek 4'te bunu bizzat göreceksin.

Gerçek sitelerde durum daha karmaşıktır. Aşağıdaki ham yanıtta (30.11'deki betikle alındı) example.com'un bir CDN üzerinden geldiğini görüyorsun: `Age` başlığı, yanıtın önbellekte ne kadar kaldığını saniye olarak söyler, `cf-cache-status: HIT` ise yanıtın kenar sunucudan verildiğini gösterir. Tarayıcın, bu yanıtı yalnızca kendi önbelleğinde değil, aracı önbelleklerde de tutabilir.

## 30.10 Çerezler, oturum ve CORS

HTTP durumsuz olduğu için bir kullanıcının giriş yaptığını sunucu kendiliğinden bilemez. Bunu **çerezler** ile çözeriz. Sunucu yanıtta `Set-Cookie: oturum=...` başlığını gönderir; tarayıcı çerezi saklar ve aynı siteye giden sonraki her istekte `Cookie` başlığıyla geri yollar. Çerezin özellikleri, nasıl kullanılacağını belirler: `HttpOnly` çerezi JavaScript'ten okunamaz hâle getirir, `Secure` çerezi yalnızca HTTPS üzerinden gönderir, `SameSite` ise çerezin siteler arası isteklerde gönderilip gönderilmeyeceğini kısıtlar. `Max-Age` ve `Expires` çerezin ömrünü belirler.

Sunucu tarafında oturum genelde bir oturum kimliğine (rastgele, tahmin edilemez bir dizi) karşılık gelen bir kayıttır. Çerez yalnızca bu kimliği taşır, asıl veriyi değil. Bu tasarım, çerezin çalınmasının ne anlama geldiğini de belirler: kimliği ele geçiren, oturumu devralabilir. Bu yüzden çerez yönetimi, oturum süresi ve yenileme Bölüm 32'nin konusudur.

**CORS** (Cross-Origin Resource Sharing) sık yanlış anlaşılan bir mekanizmadır. Tarayıcı, bir sayfanın başka bir kökenden (origin: şema, alan adı ve port) kaynak istemesini varsayılan olarak engeller. CORS, sunucunun bu kısıtı hangi kökenler için gevşeteceğini `Access-Control-Allow-Origin` başlığıyla söylemesidir. Basit olmayan istekler (örneğin JSON gövdeli bir POST ya da özel bir başlık içeren istek) önce bir `OPTIONS` ön uçuş (preflight) isteğiyle sorulur. Burada önemli bir noktayı tekrarlayalım: CORS bir sunucu güvenlik özelliği değildir; tarayıcının kendi politikasıdır. Sunucuya gelen isteği durdurmaz, yalnızca tarayıcının yanıtı okumasına izin verip vermeyeceğini belirler. Bu ayrım, XSS ve CSRF gibi saldırıları anlamak için Bölüm 32'de yeniden ele alınacak.

## 30.11 Ham HTTP: bayt bayt bir istek

Şimdi bir tarayıcının yaptığını elle yapıyoruz. Aşağıdaki program example.com'un 80 numaralı portuna düz bir TCP bağlantısı açar, tam bir HTTP/1.1 isteği gönderir ve yanıtı okur. Bu kez TLS yok; HTTPS'in arkasındaki şifreleme Bölüm 32'nin konusu. Program, yanıtı ayrıştırmak için 30.7'deki `yanit_ayir` ve `chunked_coz` fonksiyonlarını kullanır.

@@KOD b30_2_http_ham.py 1 22 python@@

İstek metni, satırları `\r\n` ile biten bir dizgedir ve boş satırla biter. `Connection: close` başlığı, sunucuya yanıttan sonra bağlantıyı kapatmasını söyler; böylece istemci gövdenin bittiğini bağlantının kapanmasıyla anlar. Bu, kalıcı bağlantının tersi bir kolaylıktır ama yanıtın ne zaman bittiğini belirlemek için her zaman yeterli değildir.

@@KOD b30_2_http_ham.py 23 53 python@@

Çıktının başında gönderilen isteğin tam baytları görünür; sonrasında yanıt özeti gelir:


@@CIKTI cikti/b30_2.txt "python b30_2_http_ham.py example.com 80 /"@@

Bu çıktıdan üç şeyi okumalısın. Birincisi, durum satırı `HTTP/1.1 200 OK`: sunucu sayfayı doğrudan verdi, yönlendirme yapmadı. İkincisi, `transfer-encoding: chunked` başlığı var; gövde parçalı gönderildi ve istemci onu açtı. Üçüncüsü, `age` ve `cf-cache-status` başlıkları, yanıtın bir CDN önbelleğinden geldiğini gösteriyor (30.9).

### Kendi HTTP sunucun

Bir protokolü gerçekten anlamanın en iyi yolu, onu karşı tarafta uygulamaktır. Aşağıdaki sunucu, tek bir iş parçacığıyla çalışan minimal bir HTTP/1.1 sunucusudur. Statik dosyaları sunar, 404 ve 405 döner, `Content-Length` ile gövde uzunluğunu bildirir, kalıcı bağlantıyı destekler, ETag ve `Cache-Control` üretir, `../` ile kök dizinden çıkmayı engeller. Bağlantıları tek tek kabul eder; eşzamanlılık Bölüm 31 ve 53'te gelir.

@@KOD b30_4_http_sunucu.py 1 21 python@@

Ayrıştırıcı, istek satırını üç parçaya böler ve sürümün `HTTP/1.` ile başladığını doğrular. Başlık satırları `:` ile ayrılır; ilk `:` karakterinden sonrası değerdir. Bir ayrıntıya dikkat et: `rstrip(b"\r\n")` yalnızca CRLF'yi değil tek bir LF'yi de kabul eder. RFC 9112, alıcının tek LF'yi satır sonu olarak tanıyabileceğini söyler. Başlık boyutu, üst sınırı aşarsa 431 döner; bu, kötü niyetli ya da bozuk bir istemcinin belleği şişirmesini önler.

@@KOD b30_4_http_sunucu.py 22 50 python@@

Ayrıştırıcının devamı, yol çözümlemesidir:

@@KOD b30_4_http_sunucu.py 51 61 python@@

Yol çözümleme, sunucunun güvenlik açısından en kritik kısmıdır. İstenen yol `KOK` dizinine eklenir ve `normpath` ile normalleştirilir; ardından sonucun hâlâ kök dizinin altında olup olmadığı kontrol edilir. `/../b30_4_http_sunucu.py` gibi bir istek normalleştirildikten sonra kökün dışına düşer ve reddedilir. Bu kontrol olmasaydı, sunucu yalnızca `site` klasörünü değil, bilgisayarındaki her dosyayı sunabilirdi. Yol geçişi saldırılarının ayrıntısı ve kodlanmış varyantları Bölüm 32'de işlenir.

@@KOD b30_4_http_sunucu.py 62 98 python@@

Yanıt yazma fonksiyonu, Content-Length'i gövdenin gerçek uzunluğundan hesaplar. 304 ve HEAD yanıtlarında gövde gönderilmez; HEAD için başlıklar gönderilir ama gövde atlanır. Koşullu istek mantığı da burada: `If-None-Match` içindeki ETag, sunucunun ürettiğiyle eşleşirse 304 döner.

@@KOD b30_4_http_sunucu.py 99 135 python@@

Sunucuyu curl ile test ettik: önce düz istekler ve hata durumları. Sunucu altı bağlantıdan sonra kendiliğinden çıkacak şekilde başlatıldı: `python -I b30_4_http_sunucu.py site 8100 6`. Her curl komutu bir bağlantı açar.


@@CIKTI cikti/b30_4_curl_raw.txt ""@@

Çıktıda 200 yanıtında ETag ve `Cache-Control: max-age=60` başlıklarını görüyorsun. Aynı ETag ile yapılan ikinci istek 304 aldı ve gövde gelmedi. Bilinmeyen yol 404 aldı; POST ise 405 ve `Allow: GET, HEAD` başlığıyla reddedildi. `../` isteği 404 ile reddedildi ve sunucu günlüğünde bu isteğin ham yolu görünse de dosya dışarı çıkmadı. Son istekte iki yol aynı bağlantı üzerinden gitti: `Connection #0` ikisinde de aynıydı, yani kalıcı bağlantı çalıştı.

Sunucunun günlüğü, hangi bağlantıdan hangi isteğin geldiğini de gösterir:


@@CIKTI cikti/b30_4_log.txt ""@@

## 30.12 REST: kaynak ve yöntem eşlemesi

REST (Representational State Transfer), Roy Fielding'in 2000 tarihli doktora tezinde tanımladığı bir mimari stildir; bir protokol değildir. Temel fikir, sunucudaki her şeyi bir **kaynak** olarak düşünmek ve her kaynağa bir URI ile erişmektir. Kaynağın istemciye gönderilen hâli bir **temsildir** (JSON, HTML, XML). İstemci, kaynağın durumunu HTTP yöntemleriyle değiştirir.

Bir kayıt koleksiyonu için tipik eşleme şöyledir:

| İstek | Anlamı | Başarılı yanıt |
|---|---|---|
| GET /kayitlar | Kayıt listesini oku | 200 |
| POST /kayitlar | Yeni kayıt oluştur | 201 ve Location başlığı |
| GET /kayitlar/42 | 42 numaralı kaydı oku | 200 |
| PUT /kayitlar/42 | 42 numaralı kaydı tamamen değiştir | 200 ya da 204 |
| DELETE /kayitlar/42 | 42 numaralı kaydı sil | 204 |

REST'in "durumsuz" olması, her isteğin tek başına anlaşılabilir olması demektir. Bu sayede istekler farklı sunucular arasında dağıtılabilir ve önbelleğe alınabilir. Ama REST'i HTTP ile karıştırmak yaygın bir hatadır: aynı yöntemleri ve durum kodlarını kullanan her API REST değildir. Ayrıntılı API tasarımı, sürümleme ve hata modelleri Bölüm 40'ta ele alınacak.

## 30.13 HTTP/2 ve HTTP/3

HTTP/1.1'in tek bir bağlantıda bir seferde bir yanıt sunması, sayfa başına çok sayıda küçük dosya (betik, stil, görsel) olduğunda ciddi bir darboğaza dönüşür. Tarayıcılar bunu host başına birkaç paralel bağlantı açarak hafifletti; bu ise her bağlantının kendi el sıkışma maliyetini getirir.

**HTTP/2** (RFC 9113) aynı anlamı, farklı bir taşıma biçimiyle korur. Metin mesajlar yerine **ikili çerçeveler (frame)** kullanır. Her istek ve yanıt, bir **akış (stream)** numarası taşıyan çerçevelere bölünür. Bu sayede tek bir TCP bağlantısı üzerinde birden çok akış aynı anda ilerler; buna **çoklama (multiplexing)** denir. Başlıklar **HPACK** ile sıkıştırılır (RFC 7541): tekrar eden başlıklar bir dinamik tablodan referansla gönderilir. Sunucu itme (server push) özelliği de vardır; ancak tarayıcı desteği azaldığı için pratikte yaygın değildir (genel bilgi).

HTTP/2'nin tek bir TCP bağlantısına bağımlılığı yeni bir sorun doğurur. TCP, paketleri sırayla teslim eder; bir paket kaybolursa, sonraki paketler ardından gelse bile uygulamaya verilmez. Yani bir akıştaki kayıp, aynı bağlantıdaki diğer akışları da bekletir. Bu, **TCP seviyesinde baş-satır engellemesi (head-of-line blocking)** olarak bilinir.

**HTTP/3** bu sorunu taşıma katmanında çözer. Taşıma olarak TCP yerine **QUIC** kullanır (RFC 9000). QUIC, UDP üzerinde çalışır ve akışları kendi içinde ayırır: bir akıştaki kayıp yalnızca o akışı bekletir. QUIC, TLS 1.3'ü kendi el sıkışmasına gömer (RFC 9001), böylece taşıma ve şifreleme tek bir el sıkışmada kurulur. Başlık sıkıştırması HPACK'in yerine **QPACK** ile yapılır (RFC 9204); çünkü akışlar bağımsız olduğu için HPACK'in sıralı yapısı doğrudan kullanılamaz.

![Şekil 30.9: HTTP/1.1, HTTP/2 ve HTTP/3 yığınları. HTTP anlamı aynı kalır; değişen, altındaki taşıma ve akışların birbirinden ne kadar bağımsız olduğudur.](gorseller/b30_surum_yigin.png)

Şekil 30.9'daki katmanlar, bu üç sürümün aynı HTTP anlamını farklı bir taşımayla taşıdığını gösterir. Bu bölümde HTTP/2 ve HTTP/3 için kendi kodumuzu yazmadık; çünkü bu protokoller TLS ve sıkıştırma ayrıntılarını gerektirir. Bunların nasıl çalıştığını görmek için `curl --http2` ya da `curl --http3` ile tarayabilirsin; ama HTTP/3 desteği yerel curl derlemesine bağlıdır.

## 30.14 Performans: bir sayfanın gecikme bileşenleri

Bir sayfanın ilk baytı gelene kadar geçen süre, birkaç bileşenin toplamıdır. Bu bileşenleri ayrı ayrı görmek, hangisinin optimize edileceğini seçmenin ilk adımıdır. Kabaca şu sıra izlenir: DNS sorgusu, TCP el sıkışması (1 RTT), TLS el sıkışması (TLS 1.3'te 1 RTT), HTTP isteğinin gönderilip ilk yanıt baytının dönmesi (1 RTT artı sunucunun işlem süresi), sonra gövde aktarımı.

Bu zincirde en pahalı şey çoğu zaman RTT'dir. Ağ hızı ne olursa olsun ışık hızı ve yönlendirme gecikmesi bir alt sınır koyar. Bu yüzden iki yaklaşım önemlidir: bağlantı sayısını azaltmak (kalıcı bağlantı, HTTP/2 ve HTTP/3) ve sunucuyu kullanıcıya yakın tutmak (CDN). Gövdenin boyutu ise bu zincirde küçük bir yer tutar; bu bölümdeki örnek sayfa yalnızca 577 bayt gövdeye sahipti.

### Ölçüm: curl -w ile zamanlama

`curl`, `-w` seçeneğiyle her aşamanın kümülatif zamanını verir: `time_namelookup` (DNS), `time_connect` (TCP), `time_appconnect` (TLS), `time_starttransfer` (ilk bayt) ve `time_total` (toplam). Aşağıdaki program, example.com'a 10 kez bu zamanlamalarla istek atar, her aşamanın ayrık süresini hesaplar ve CSV'ye yazar. Ham DNS ölçümü için ise aynı sorgu kodunu 20 kez tekrarlar. DNS ölçümleri Windows üzerinde doğrudan Python ile, HTTP ölçümleri WSL2 (Ubuntu) içindeki curl 8.5.0 ile yapıldı.

@@KOD b30_5_olcum.py 1 20 python@@

Yardımcı fonksiyonlar, DNS sorgusunu tekrar eder ve her ölçümün süresini milisaniye olarak toplar. `assert` satırı, yanıtın başarılı (RCODE 0) olduğunu doğrular; yanlış bir cevapla süre ölçmek anlamsız olurdu.

@@KOD b30_5_olcum.py 21 50 python@@

Ana bölüm, sonuçları CSV'ye yazar ve ekrana medyanları basar. Medyan, aykırı bir ölçümün sonucu bozmasını engeller; ortalamadan daha dayanıklıdır.

@@KOD b30_5_olcum.py 51 73 python@@

Programın çıktısı şöyleydi:


@@CIKTI cikti/b30_5.txt "python b30_5_olcum.py"@@

Bu sonuçları nasıl okumalısın? DNS'in medyanı 4,5 milisaniye: bu bir önbellek isabetidir, çünkü WSL'nin çözümleyicisi kaydı zaten tutuyordu. Bir **soğuk** önbellekte (kayıt hiç yokken) bu süre çok daha uzun olurdu; bunu ölçmedik, çünkü önbelleği güvenilir biçimde temizlemek bu ortamda kolay değil ve tahmin yürütmek istemedik. TCP ve TLS aşamaları ise kabaca 60-75 milisaniye sürdü; bu değerler, ağdaki bir gidiş-dönüşün yaklaşık 60-70 milisaniye olduğunu düşündürüyor. İlk bayta kadar geçen süre de (istek, sunucu işlemi ve yanıtın ilk baytı) yaklaşık 70 milisaniye. Toplam, medyan olarak yaklaşık 221 milisaniye.

Bu sayılar, ağa ve güne göre değişir. Ama oranlar gerçek bir şeyi anlatır: sayfanın ilk baytından önce üç gidiş-dönüş yapıldı (TCP, TLS, istek-yanıt) ve bunların her biri ağ gecikmesi kadar sürdü. Gövdenin aktarılması ise neredeyse bedavaydı. Bu yüzden küçük bir sayfa için bile bağlantı sayısını ve RTT'yi azaltmak, gövdeyi küçültmekten çok daha fazla kazandırır.

DNS ölçümündeki iki çözümleyici arasındaki fark (1.1.1.1 için medyan yaklaşık 20 milisaniye, 8.8.8.8 için yaklaşık 44 milisaniye) bu makinenin ağ yolundan kaynaklanıyordu; genel bir "hangisi daha hızlı" yargısı değildir. Ölçümü farklı bir ağdan tekrarladığında sıralama değişebilir.

![Şekil 30.10: Ölçülen bir sayfa isteğinin gecikme bileşenleri. Çubuk, toplama en yakın tek bir ölçümün DNS, TCP, TLS, ilk bayta kadar ve gövde aktarımı süresini gösterir.](gorseller/b30_gecikme_bilesen.png)

Şekil 30.10, medyan toplama en yakın ölçümün bileşenlerini gösterir. Çubuğun bileşenleri toplamla birebir tutar; böylece okur kendi ölçümünü aynı şekilde yorumlayabilir.

## 30.15 Gerçek dünya: yer istasyonu, sensör API'si, mikroservisler

Savunma sanayiinde HTTP'nin rolünü üç yerde görebilirsin. Birincisi bir **yer istasyonu** web paneli: operatörün durum ekranı, görev planı ve komutları için bir HTTP/REST arayüzü kullanılır; canlı telemetri akışı ise genelde WebSocket ya da benzeri sürekli bir kanalda taşınır. Bunun nedeni, komutların her biri bağımsız bir isteğe benzerken telemetrinin sürekli bir akış olmasıdır. Ayrıntılar ürüne ve tasarıma göre değişir; burada genel mantığı söylüyoruz.

İkincisi bir **sensör düğümü** ile **EV Dashboard** gibi bir panel arasındaki iletişimdir. Düğüm bir ağ geçidine bağlanır, ağ geçidi verileri bir HTTP uç noktasına yollar. Burada 30.5'teki soru yeniden ortaya çıkar: düğüm DHCP ile mi adres alıyor, yoksa sunucu adresi sabit mi? Ayrıca her ölçüm için yeni bağlantı açmak yerine kalıcı bağlantı kullanmak, pil ve gecikme açısından önemlidir. Projenin ayrıntısı bu çözümü şekillendirir.

Üçüncüsü **mikroservis** mimarisidir. Servisler birbirleriyle HTTP üzerinden konuşur, adlarını DNS ile çözer (kümelerde servis adları çoğu zaman bir küme içi DNS tarafından sağlanır; genel bilgi), ve tekrarlanan istekler için bağlantı havuzu ve önbellek başlıkları kullanır. Bu bölümde gördüğün her şey, bu sistemlerdeki hataların teşhisinde doğrudan işe yarar: bir zaman aşımı DNS'te mi, TCP'de mi, TLS'te mi, yoksa sunucunun kendisinde mi, bu bileşen zamanlamasıyla anlaşılır.

## Çözümlü Örnekler

Dört örnek, zorluk sırasıyla ★'dan ★★★'e gider. Her birinde altı adım izlenir: anla, örnekle, kaba çöz, örüntü, iyileştir, doğrula. Doğrulama adımında elle iz sürme tablosu bulunur.

### Örnek 1 ★: Bir HTTP yanıtını elle ayrıştırmak

Elinde şu ham yanıt olduğunu düşün (satır sonları CRLF; gövde chunked):

```term
HTTP/1.1 200 OK
Content-Type: text/plain
Transfer-Encoding: chunked

4
Wiki
5
pedia
E
 in

chunks.
0

```

**Adım 1 — Anla.** Yanıtın durum satırını, başlıklarını ve gövdesini ayırmak istiyoruz. Gövde chunked olduğu için iki kat ayrıştırma gerekiyor: önce başlıklar, sonra parçalar.

**Adım 2 — Örnekle.** Yanıtın ilk satırı `HTTP/1.1 200 OK`; başlıklar `Content-Type` ve `Transfer-Encoding`; gövdede `4`, `Wiki`, `5`, `pedia`, `E`, ` in`, boş satır, `chunks.`, `0` ve sonra boş satır var.

**Adım 3 — Kaba çöz.** Başlıkları bulmak için ilk `\r\n\r\n` dizisini ara. Öncesi başlıklar, sonrası gövde. Gövdeyi okumak için boyut satırını oku, o kadar bayt al, CRLF'yi atla; boyut `0` olunca dur.

**Adım 4 — Örüntü.** Bu, her parça için "boyut, veri, CRLF" döngüsüdür. Sonunda boyutu `0` olan parça ve ardından bir boş satır gelir. Döngü invariantı: her turda `i` bir sonraki boyut satırının başını gösterir.

**Adım 5 — İyileştir.** Kaba çözümde boyut satırını bulmak için her seferinde baştan aramak gerekmez; zaten ilerlediğimiz yerden bulmak yeter. Ayrıca boyut satırını onaltılık olarak yorumlarken `;` sonrasını atmalıyız (chunk-extension). Hata durumunda (parça eksik, CRLF yok) fırlatmalıyız, sessizce kırpmamalıyız. Bu, 30.7'deki `chunked_coz` tasarımının ta kendisidir.

**Adım 6 — Doğrula.** Aşağıdaki iz tablosunda girdinin her parçasının `i` ofsetinde hangi değeri aldığını elle takip et. Gövde `Wikipedia in\r\n\r\nchunks.` olmalı, artan bayt boş olmalı.

| Tur | `i` (başlangıç) | Boyut satırı | Boyut (onluk) | Alınan veri | Yeni `i` |
|---|---|---|---|---|---|
| 1 | 0 | `4` | 4 | `Wiki` | 9 |
| 2 | 9 | `5` | 5 | `pedia` | 19 |
| 3 | 19 | `E` | 14 | ` in\r\n\r\nchunks.` (14 bayt) | 38 |
| 4 | 37 | `0` | 0 (son parça) | — | sonra boş satır, bitti |

Tabloda 14 bayt, ` in`, iki CRLF ve `chunks.` (3 + 4 + 7 = 14 bayt) demektir. Gövde, `Wiki` + `pedia` + ` in\r\n\r\nchunks.` birleşimi, yani `Wikipedia in\r\n\r\nchunks.` olur; programın çıktısıyla aynıdır.

**Bunu AI'sız yazabilir misin?** Gövdedeki boyut satırı `1A` olsaydı ne değişirdi? Kodu kâğıda yaz, `1A` onaltılıkla 26 bayt demek olduğunu hesaba kat ve veri eksik kaldığında hangi hatanın fırlatılacağını söyle.

### Örnek 2 ★★: DNS sorgusunu bayt bayt kurmak

Sorgumuz example.com için A kaydı istiyor. Önce ne göndermek istediğimizi cümleyle söyleyelim: "example.com'un IPv4 adresini ver, özyinelemeli olarak." Bu cümleyi 29 baytlık bir pakete çevirmemiz gerekiyor.

**Adım 1 — Anla.** Bir DNS sorgusu üç parçadır: 12 baytlık başlık, soru adı ve soru (tür ve sınıf). Yanıt bölümü yok; sorgularda yalnızca soru vardır.

**Adım 2 — Örnekle.** Bölüm 30.4'te gerçekten gönderdiğimiz sorgu (kimlik `0x1A2B`) şu baytlardır: `1a 2b 01 00 00 01 00 00 00 00 00 00 07 65 78 61 6d 70 6c 65 03 63 6f 6d 00 00 01 00 01`.

**Adım 3 — Kaba çöz.** Başlığı ilk 12 bayt olarak yaz: kimlik, bayraklar, dört sayaç. Soru adını etiketlere böl ve her etiketin önüne uzunluğunu koy. Sonuna sıfır koy. Ardından tür ve sınıfı yaz.

**Adım 4 — Örüntü.** Ad alanı her zaman `uzunluk, etiket, uzunluk, etiket, ..., 0` örüntüsündedir. Başlığın sayaçları yalnızca QDCOUNT=1 ile anlamlıdır; geri kalanı sıfırdır.

**Adım 5 — İyileştir.** AAAA (IPv6) sorgusu istemek için yalnızca QTYPE değişir: A için `00 01`, AAAA için `00 1c` (28). Kimliği rastgele seçmek, sahte yanıt riskini azaltır (30.4'teki güvenlik notu). Tek bir fonksiyon, tip parametresiyle her iki sorguyu da kurabilir.

**Adım 6 — Doğrula.** Aşağıdaki tabloyu programın çıktısıyla karşılaştır. Her bayt, bir alana aittir ve toplam 29 bayt tutar (12 + 13 + 4).

| Alan | Bayt (onaltılık) | Değer | Ofset | Açıklama |
|---|---|---|---|---|
| Kimlik | 1a 2b | 0x1A2B | 0-1 | İstek-yanıt eşleştirme |
| Bayraklar | 01 00 | RD=1 | 2-3 | Özyinelemeli iste |
| QDCOUNT | 00 01 | 1 | 4-5 | Bir soru var |
| ANCOUNT | 00 00 | 0 | 6-7 | Sorguda yanıt yok |
| NSCOUNT | 00 00 | 0 | 8-9 | Yetki kaydı yok |
| ARCOUNT | 00 00 | 0 | 10-11 | Ek kayıt yok |
| QNAME etiket 1 | 07 65 78 61 6d 70 6c 65 | 7, "example" | 12-19 | Uzunluk + 7 bayt |
| QNAME etiket 2 | 03 63 6f 6d | 3, "com" | 20-23 | Uzunluk + 3 bayt |
| QNAME sonu | 00 | kök | 24 | Ad sonu |
| QTYPE | 00 01 | A (1) | 25-26 | IPv4 adresi |
| QCLASS | 00 01 | IN (1) | 27-28 | İnternet sınıfı |

**Bunu AI'sız yazabilir misin?** `www.example.com` için MX (tür 15) sorgusunun baytlarını kâğıda yaz. Toplam uzunluğun kaç bayt olduğunu, etiket sayısını ve kimliğin nerede olacağını söyle.

### Örnek 3 ★★: Ad sıkıştırmalı bir yanıtı ayrıştırmak

Ağa bağlı olmadan, kayıtlı bir yanıtın baytlarında işaretçi izini takip edelim. Yanıt, example.com A sorgusunun gerçek bir cevabıdır (61 bayt, iki A kaydı). Program, ad çözme sürecini adım adım yazdırır.

**Adım 1 — Anla.** İlk yanıt kaydı ofset 29'da başlıyor. Adı yazılı değil: `c0 0c` diye bir işaretçi var. Bu işaretçiyi takip ederek adın asıl yerini bulmamız gerekiyor.

**Adım 2 — Örnekle.** Ofset 29-30 çifti `c0 0c`. İlk baytın üst iki biti `11`, yani bu bir işaretçi. Ofset `((0xC0 & 0x3F) << 8) | 0x0C = 12`.

**Adım 3 — Kaba çöz.** Ad çözme fonksiyonunu yaz: bayt işaretçiyse hedefe git, uzunlukla etiket oku, sıfırda dur. Ana akışın `c0 0c`'den sonra devam etmesi gerektiğini unutma.

**Adım 4 — Örüntü.** Her işaretçi, mesajın başına doğru geriye (ya da ileriye) bir atlamadır. Döngü olabilir; bu yüzden bir sayaçla sınırlamak gerekir. İşaretçi ardından gelen ad, işaretçinin hedefinden okunur, ama ana akış işaretçinin iki baytından sonra devam eder.

**Adım 5 — İyileştir.** Sayaç sınırı (ör. 20) kötü yanıtlara karşı koruma sağlar. İşaretçinin hedefinin mesaj sınırları içinde olduğunu doğrulamak da iyi bir ekleme olurdu; bunu alıştırmalarda bırakıyoruz.

Önce izleyici ve ana programın tamamı aşağıda. `ad_izle`, `ad_coz`'un adım adım yazdırılan sürümüdür; ana program ise `yanit_ayristir` ile tüm yanıtı çözer.

@@KOD b30_8_isaretci.py 1 34 python@@

@@KOD b30_8_isaretci.py 35 43 python@@

**Adım 6 — Doğrula.** Programı çalıştır ve izi tabloyla karşılaştır.


@@CIKTI cikti/b30_8.txt "python b30_8_isaretci.py"@@

Program, işaretçiyi takip edip "example" ve "com" etiketlerini okuyarak adı 12-24 aralığından alır. Yanıt kaydının ana akışı 29 + 2 = 31'de devam eder; orada `TYPE`, `CLASS`, `TTL` ve `RDATA` okunur.

| Ofset | Bayt | Yorum |
|---|---|---|
| 29-30 | c0 0c | İşaretçi, hedef 12 |
| 12 | 07 | Etiket uzunluğu 7 |
| 13-19 | "example" | Etiket |
| 20 | 03 | Etiket uzunluğu 3 |
| 21-23 | "com" | Etiket |
| 24 | 00 | Ad sonu; işaretçiden döndü |
| 31-32 | 00 01 | TYPE = A |
| 33-34 | 00 01 | CLASS = IN |
| 35-38 | 00 00 00 57 | TTL = 87 saniye |
| 39-40 | 00 04 | RDLENGTH = 4 |
| 41-44 | 68 14 17 9a | RDATA = 104.20.23.154 |

İkinci kayıt (ofset 45) aynı işaretçiyi kullanır ve farklı bir RDATA taşır; bu yüzden iki A kaydı görürsün.

**Bunu AI'sız yazabilir misin?** Bu yanıtta ikinci kaydın adı yerine işaretçi değil de tam ad yazılı olsaydı, ayrıştırıcının yapması gereken değişiklik nedir? Ve `c0 00` işaretçisi (hedef ofset 0, başlığın ilk baytı) ne döndürür? Cevabını iz tablosuyla gerekçelendir.

### Örnek 4 ★★★: Koşullu istek ve LRU'lu istemci önbelleği

Bir istemci, sık istediği kaynakları yerelde tutmak ister. Ama kapasite sınırlı: en eski kullanılanı atmalı. Burada Bölüm 16'daki **LRU (en az kullanılan atılır)** önbelleği fikrini HTTP'ye uyguluyoruz. Önbellek, `max-age` süresi dolmadan ağa çıkmaz; süre dolduğunda `If-None-Match` ile koşullu istek yapar ve 304 gelirse kendi kopyasını yeniler.

**Adım 1 — Anla.** Üç durumu ayırt etmemiz lazım: taze (ağa çıkılmaz), bayat ama değişmemiş (304), bayat ve değişmiş (200). Ayrıca kapasite aşılınca en eski kayıt atılmalı ve atılmış bir kaynak sonraki istekte yeniden ağdan gelmeli.

**Adım 2 — Örnekle.** Sunucu `index.html` için `Cache-Control: max-age=60` ve ETag döner. İstemci bu kopyayı tutar. Süreyi geriye çekersek (bayatlatırsak), bir sonraki istek 304 ile karşılanmalı.

**Adım 3 — Kaba çöz.** Bir sözlük (yol → (ETag, bitiş zamanı, gövde)) ve bir sayaç yeterli. Her istekte önce sözlüğe bak; taze ise dön, değilse koşullu istek gönder.

**Adım 4 — Örüntü.** Bu, "önbellek + süreli geçerlilik + koşullu doğrulama" kalıbıdır. Kapasite sınırı ise LRU kalıbıdır: bir kaydı her kullanımda sona taşımak ve sınır aşılınca baştakini atmak. Python'da `OrderedDict` bunu `move_to_end` ve `popitem(last=False)` ile verir.

**Adım 5 — İyileştir.** 404 gibi başarısız yanıtlar önbelleğe alınmamalı; aksi halde bir kaynak sunucuda oluşunca bile istemci eski hatayı görmeye devam eder. Bu yüzden yalnızca 200 ve 304 yanıtları saklanır. Bir hata ayıklama notu: 304 yanıtında `Cache-Control` yoksa, tazelik süresi sıfır sanılır ve her istek yeniden doğrulanır. Sunucumuzun 304'ünde bu başlığı bilinçli olarak gönderdik.

Önbellek istemcisinin tamamı aşağıda. Sunucu tarafı 30.11'de verildi; bu istemci onunla birlikte çalışır.

@@KOD b30_6_onbellek.py 1 19 python@@

Sınıfın durumu üç alandan oluşur: kapasite, yol → (ETag, bitiş, gövde) sözlüğü ve bir sayaç sözlüğü. `OrderedDict` sıra da tuttuğu için ilk eleman en eski, son eleman en yeni kullanılandır.

@@KOD b30_6_onbellek.py 20 55 python@@

`al` fonksiyonu, taze kopya varsa ağa çıkmadan döner. Değilse koşullu istek gönderir: 304 gelirse önbellekteki gövdeyi kullanır, 200 gelirse yeni gövdeyi saklar. Kapasite aşılınca en eski kayıt atılır.

@@KOD b30_6_onbellek.py 56 72 python@@

Ana bölüm aynı istemciyi dört adımlık bir senaryoyla sınar.

**Adım 6 — Doğrula.** Önce sunucuyu başlat (`python -I b30_4_http_sunucu.py site 8080`), sonra istemciyi çalıştır (`python b30_6_onbellek.py 127.0.0.1:8080`). Sunucu sınırsız çalışsın diye üçüncü argüman verilmedi.



@@CIKTI cikti/b30_6.txt "python b30_6_onbellek.py 127.0.0.1:8080"@@

Çıktıdaki sayaç değerleri iz tablosu gibi okunmalı. `ag` gerçekten yapılan ağ isteklerinin sayısıdır, `taze` ağa çıkmadan karşılanan isteklerdir.

| Adım | Ne oldu | ag | 200 | 304 | taze |
|---|---|---|---|---|---|
| 1 | Önbellek boş, 200 geldi | 1 | 1 | 0 | 0 |
| 2 | Hemen tekrar, taze | 1 | 1 | 0 | 1 |
| 3 | Süre geriye çekildi, koşullu istek, 304 | 2 | 1 | 1 | 1 |
| 4 | not.txt ve uc.txt ağdan geldi; index taze kaldı | 4 | 3 | 1 | 2 |
| 5 | not.txt yeniden istendi, ağa çıktı | 5 | 4 | 1 | 2 |

Beşinci adımda `200` sayısının dört olduğuna dikkat et: not.txt iki kez 200 aldı, çünkü LRU onu atmıştı; `uc.txt` de 200 ile geldi. Bu, LRU'nun doğru çalıştığını ve atılan kaydın gerçekten yeniden indiğini gösterir.

**Bunu AI'sız yazabilir misin?** Kapasite 2 yerine 3 olsaydı, adım 4'ten sonra önbellekte hangi yollar olurdu ve adım 5'te `ag` kaç olurdu? Cevabını önce tabloya yazarak, sonra programı çalıştırarak doğrula.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı, kod asistanı ya da hazır bir DNS ya da HTTP kütüphanesi kullanma. Standart kütüphanedeki `socket` ve `struct` modülleri serbesttir; ama `dnspython`, `requests`, `http.server` gibi hazır çözümleri kullanmak, bu bölümün öğretmek istediği şeyi atlamak demektir. Bölümdeki kodları kapatıp boş bir dosyada başla.
:::

### Proje 1 ★★: Kendi `dig` aracın

**Amaç.** Komut satırından çalışan, A, AAAA, MX, NS, CNAME ve TXT sorgularını yapabilen, yanıtı ayrıştıran bir DNS sorgu aracı yaz. Adını `mydig.py` koyabilirsin.

**Beklenen davranış.** `python mydig.py example.com A` gibi bir komut, soru bölümünü, yanıt kayıtlarını (ad, tür, TTL, değer) ve RCODE adını yazdırmalı. Geçersiz bir tür adı verildiğinde kullanıcıya açık bir hata vermeli. Sunucu yanıt vermezse zaman aşımı ile yeniden denemeli.

**Önerilen yaklaşım.** Tür adlarını sayısal kodlara eşleyen bir sözlük kur (A=1, NS=2, CNAME=5, MX=15, TXT=16, AAAA=28). Yanıt ayrıştırıcısını bu projede yeniden yaz; 30.4'teki ad çözme fonksiyonundaki sayaç koruması gibi koruma mekanizmalarını da ekle. Zaman aşımı için her denemeden önce süreyi iki katına çıkarmayı (1 s, 2 s, 4 s) dene. Yanıttaki kimlik, gönderdiğin kimlikle eşleşmiyorsa o paketi yok say. TXT ve MX'in RDATA biçimlerini belirlemek için RFC 1035'i oku.

**Başarı kriterleri.** (1) Beş farklı tür için doğru yanıt üretilir ve `socket.getaddrinfo` ile A kayıtları karşılaştırıldığında aynı adresler çıkar. (2) Ağ yokken program üç denemeden sonra anlamlı bir hata mesajı ile çıkar; takılıp kalmaz. (3) Kötü biçimli bir yanıt (kesilmiş paket) program çökmeden bir hata döndürür. (4) Ayrıştırıcının bir testi var: sabit bir yanıt baytı dizisinden beklenen değerleri üretir.

### Proje 2 ★★★: Olay döngülü minimal HTTP sunucusu

**Amaç.** 30.11'deki sunucuyu büyüt: birden çok bağlantıyı aynı anda yöneten, kalıcı bağlantıları destekleyen, dinamik içerik için chunked yanıt üreten, MIME türlerini doğru bildiren ve her isteği günlüğe yazan bir sunucu.

**Beklenen davranış.** Sunucu yüzlerce eşzamanlı bağlantıyı tek bir iş parçacığında (olay döngüsüyle) taşıyabilmeli. `/zaman` gibi bir uç nokta chunked yanıtla saniyede bir satır gönderebilmeli. Her istek için bir erişim günlüğü satırı (istemci, yöntem, yol, durum, gövde boyutu, süre) yazılmalı. Bir yük testi (kendi yazdığın basit istemciyle 100 eşzamanlı bağlantı) hatasız tamamlanmalı.

**Önerilen yaklaşım.** Python'da `selectors` modülü, Linux'ta `epoll`'un üst katmanıdır. Bölüm 28'deki olay döngüsü fikriyle karşılaştır. Her bağlantı için bir durum makinesi tut: okuma tamponu, işlenmemiş istek, yazılacak yanıt. Chunked yanıtta her parçanın boyutunu onaltılık yaz. Yük testini, sunucu sorunsuz çalıştığında bile ölçümünü yazmadan yapma: bağlantı başına gecikme ve toplam süre tablosu hazırla. Güvenlik tarafını (yol geçişi, başlık sınırı) unutma; bu kısım Bölüm 32'de daha ayrıntılı işlenecek.

**Başarı kriterleri.** (1) 100 eşzamanlı bağlantı, hiçbir bağlantı zaman aşımı olmadan tamamlanır. (2) `/zaman` uç noktası chunked yanıt döner; istemci gövdeyi 30.7'deki çözücüyle hatasız açar. (3) Erişim günlüğü her isteği tam bir satırla kaydeder. (4) `../` istekleri ve 8 KB'dan büyük başlıklar sunucuyu çökertmeden reddedilir. (5) Sunucu, boşta kalan bağlantıları kapatır ve bellek kullanımı sabit kalır (ölçümle kanıtla).

## Ek Alıştırmalar

Aşağıdaki problemler cevapsızdır. Zorluk etiketlerine dikkat et; çoğu klasik mülakat sorusudur.

1. ★ DNS yanıtında AA bayrağının (yetkili yanıt) ne anlama geldiğini ve bir çözümleyicinin önbellekten gelen yanıtta bu bayrağı nasıl gördüğünü açıkla.
2. ★ Bir istek 404 döndürüyor ama aynı kaynak bir gün sonra 200 dönüyor. Bu durumda 404 yanıtı önbelleğe alınmalı mıydı? Gerekçeni yaz.
3. ★★ Bir DNS sunucusunun NS kaydının adı ile yetkili sunucunun IP'si aynı bölgenin içindeyse, neden yapıştırıcı (glue) kaydı gerekir? Örnek bir bölge ile açıkla.
4. ★★ HTTP/1.1'de iki istek aynı bağlantıda sırayla gönderildi. İlkinin yanıtı yavaş. İkincisinin neden daha geç geldiğini ve HTTP/2'nin bu sorunu nasıl ele aldığını açıkla.
5. ★★ Chunked gövdede boyut satırı `1F` olarak okundu ama veri 31 bayt yerine 30 bayt geldi. Ayrıştırıcının ne yapması gerektiğini ve neden sessizce devam etmemesi gerektiğini yaz.
6. ★★ Bir DHCP sunucusu aynı IP'yi iki farklı cihaza kiraladı. Kira mekanizması bunu nasıl önlemeye çalışır ve çakışma nerede yakalanır?
7. ★★ Bir istemci `Cache-Control: no-cache` ile birlikte `ETag` aldı ve sonraki istekte 304 geldi. Ardından istemci kopyayı kullandı. Bu, `no-cache`'in anlamıyla çelişir mi? Açıkla.
8. ★★ Bir sitenin ana sayfası ilk ziyarette 200 ile 3 MB gövde döndürdü. İkinci ziyarette `max-age=0` ve ETag ile 304 geldi. İkinci ziyarette hangi aşamaların atlandığını ve hangilerinin hâlâ yapıldığını (DNS, TCP, TLS, istek) sırala.
9. ★★★ Bir DNS yanıtında TC (truncated) bayrağı 1 olarak geldi. Bu durumda istemci ne yapmalı ve neden UDP'den TCP'ye geçiş gerekir? EDNS0'ın bu sınırı nasıl değiştirdiğini genel olarak açıkla.
10. ★★★ Bir mikroservis, `api.internal` adını çözemiyor, ama IP adresiyle erişebiliyor. Sorunu bulmak için hangi dosyalara ve komutlara bakarsın? Sıralı bir teşhis planı yaz.
11. ★★★ Bir HTTP/2 bağlantısında bir TCP paketi kayboldu ve dört akış aynı anda bekliyor. HTTP/3'te aynı kayıp kaç akışı etkiler? Kendi cevabını bu bölümdeki şekille karşılaştır.
12. ★★★ Bir "yeniden deneme" mekanizması, idempotent olmayan bir POST isteğini iki kez gönderdi. Hangi tasarım kararı bu çiftlemeyi önler? İstemci tarafı ve sunucu tarafı ayrı ayrı açıkla.

## Kod Okuma Egzersizi

Kaynak: CPython 3.12.10, `Lib/http/client.py` (git etiketi `v3.12.10`, raw.githubusercontent.com üzerinden indirildi ve birebir kopyalandı). Aşağıdaki kesit, chunked gövdenin boyut satırını okuyan fonksiyondur. Üst satır numarası, dosyadaki gerçek satırdır.

@@KAYNAK 537 551@@

Bu fonksiyon, boyut satırını bir satır olarak okur, uzunluk sınırını kontrol eder, `;` sonrasını atar ve onaltılık sayıya çevirir. Bir ikinci kesit ise parçaları gerçekten okuyan döngüdür:

@@KAYNAK 591 609@@

**Sorular — cevaplamadan geçme:**

1. `_read_next_chunk_size` içinde `readline(_MAXLINE + 1)` neden `_MAXLINE` değil de bir fazlasını ister? Uzunluğu kontrol eden satır bu farkı nasıl kullanıyor?
2. Boyut satırında `;` bulunduğunda CPython neden satırı tamamen atmak yerine `;`'den önceki kısmı alıyor? Bu, RFC 9112'deki chunk-extension tanımıyla nasıl uyuşur?
3. `int(line, 16)` başarısız olursa kod neden `_close_conn()` çağırıyor? Bağlantıyı açık bırakmak neden tehlikeli olurdu?
4. `_read_chunked` içindeki `amt` parametresi, bir `read(n)` çağrısının chunked bir gövdeden yalnızca `n` bayt okuyabilmesini nasıl sağlıyor? `self.chunk_left` değişkeni bu sırada neyi saklar?
5. `_read_chunked` hata durumunda `IncompleteRead` fırlatıyor ve okunan kısmı içinde taşıyor. Bu tasarım, 30.7'deki bozuk gövde örneğindeki hatayla aynı mı? Farkı bir cümleyle yaz.
6. Bölüm 30.7'deki `chunked_coz` ile bu kod arasında en az iki tasarım farkı bul (ör. parçaların nasıl birleştirildiği, sınır denetimi, kapanış). Hangisi daha savunmacı?

## Bölüm Özeti

- DNS, adları IP adreslerine çeviren dağıtık, hiyerarşik bir sistemdir; kök, TLD ve yetkili sunucular zinciri izlenir.
- Özyinelemeli çözümleyici istemci adına zinciri yürütür; yinelemeli sorguda sunucular yönlendirme döner.
- Her kayıt bir TTL taşır; önbellek bu süre boyunca sorguyu kısaltır. Ad sıkıştırma (0xC0 işaretçileri) yanıtı küçültür.
- DHCP, DORA dört mesajıyla IP, maske, ağ geçidi ve DNS parametrelerini dağıtır; kira T1 ve T2 zamanlarıyla yenilenir.
- HTTP/1.1 metin tabanlı, durumsuzdur. Yöntemlerin güvenli ve idempotent olma farkı, istemcinin yeniden deneme kararını belirler.
- Chunked aktarım, boyutu önceden bilinmeyen gövdeyi parçalar; bozuk parça hatayla reddedilmelidir.
- Kalıcı bağlantı, tekrarlanan TCP ve TLS el sıkışmalarını ortadan kaldırır; ETag ve `Cache-Control` ile koşullu istekler gereksiz indirmeyi önler.
- HTTP/2 çoklama ile aynı bağlantıda akışlar ilerler; HTTP/3 QUIC üzerinde akışları bağımsız kılarak TCP düzeyindeki engellemeyi çözer.
- Gecikmenin büyük kısmı RTT'den gelir: DNS, TCP, TLS ve ilk bayt birlikte ölçülmeden hangi adımın optimize edileceği bilinemez.

**Sonraki bölümde:** Bölüm 31'de bu bölümde kullandığımız `socket` çağrılarının içine giriyoruz: soket API'si, sunucu ve istemci iskeleti, mesaj çerçeveleme ve epoll tabanlı bir sunucu. Bu bölümde kendi sunucumuzun tek iş parçacıklı olmasının sınırını gördün; Bölüm 31 bu sınırı kırmanın yollarını gösterecek.

::: mulakat
1. Tarayıcıya `https://www.example.com` yazıldığında, DNS, TCP ve TLS'in hangi sırayla çalıştığını ve her birinin kaç RTT eklediğini açıklar mısın?
2. Özyinelemeli ve yinelemeli DNS sorgusu arasındaki fark nedir? Bir ISS çözümleyicisi hangisini yapar ve neden?
3. 304 Not Modified yanıtı neden gövde taşımaz ve bu yanıtta hangi başlıkların bulunması gerekir?
4. GET, PUT ve POST arasındaki idempotentlik farkını bir ağ hatası senaryosu üzerinden açıklar mısın?
5. HTTP/2'de çoklama varken neden hâlâ bir engelleme sorunu vardır ve HTTP/3 bunu nasıl çözer?
6. DHCP'de bir istemci neden DISCOVER'ı yayınlar (broadcast) ve OFFER'a neden hemen bağlanmaz?
7. Bir DNS önbellek zehirleme saldırısı, sorgu kimliği 16 bit olsa bile neden hâlâ mümkündür? Kaynak portunun rastgeleleştirilmesi neyi değiştirir?
8. Bir API'nin sık yavaşladığını, ama CPU ve bellek kullanımının düşük olduğunu görüyorsun. Gecikmeyi DNS, TCP, TLS ve sunucu işlem süresine nasıl ayırırsın?
