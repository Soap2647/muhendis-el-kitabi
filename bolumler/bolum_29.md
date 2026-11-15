%% kisim_no: VII
%% kisim_ad: Ağ
%% kisim_ayrac: evet
%% bolum_no: 29
%% baslik: OSI & TCP/IP

## Giriş: Ağ, katmanlar halinde konuşan bir zincir

Tarayıcına bir adres yazıp Enter'a bastığında ekranda birkaç yüz milisaniye içinde bir sayfa belirir. Bu sürede kablosuz kartın radyo dalgalarıyla bir çerçeve gönderir, yönlendiriciler paketi onlarca ağdan geçirir, sunucu bağlantıyı kurar, veriyi parçalara böler, kayıp olanları yeniden ister ve sonunda sayfayı parça parça geri gönderir. Bunların hiçbiri tek bir büyük programın işi değildir. Her biri ayrı bir protokolün, ayrı bir katmanın sorumluluğudur.

Mülakatlarda bu konu iki şekilde karşına çıkar. Birincisi klasiktir: "OSI modelinin katmanlarını say ve her birine bir örnek ver." İkincisi daha zordur: "Bir HTTP isteği tarayıcıdan sunucuya kadar hangi başlıkları taşır?" İkisinin cevabı da bu bölümde var. Ama asıl kazanç ezber değil, bir paketin baytlarını okuyabilmektir. Bölüm 1'de ağ bayt sırasını (büyük uç) gördün; Bölüm 28'de `read` ve `write` ile dosya tanımlayıcısını öğrendin. Bu bölüm o bayt ve tanımlayıcıların ağa çıktığında ne olduğunu anlatır.

Savunma sanayiinde ağ katmanı her yerde karşına çıkar. Bir İHA'nın telemetri verisi yer istasyonuna nasıl ulaşır, komut kanalında bir paketin kaybolması ne anlama gelir, neden bazı verilerin gecikmeden ama kayıpla, bazılarının ise kayıpsız ama gecikmeyle taşınması gerekir? Bu soruların cevabı taşıma katmanındaki tasarım seçimlerindedir.

Bölüm boyunca bu ağ ortamına dayanan ölçümler yapacağız: ARP tablosunu okuyacağız, TTL ile yolda hangi düğümlerin olduğunu göreceğiz, TCP bağlantısının durum geçişlerini `ss` ile izleyeceğiz, Nagle algoritmasının gecikmesini ölçeceğiz. Her ölçümün kodu kitapta, çıktısı da metinde.

::: not
Bu bölümdeki her çıktı, kitabın kodunun gerçekten çalıştırılmasıyla alındı. Ağ sayıları ortama bağlıdır; kendi bilgisayarında ağ adresleri, MAC'ler ve gecikme değerleri farklı çıkacaktır. Öğrenmen gereken şey sayının kendisi değil, neden o değeri aldığıdır.
:::

**Ölçüm ortamı.** Bütün ağ ölçümleri Windows 11 Pro üzerinde WSL2 içindeki Ubuntu 24.04'te alındı. Çekirdek sürümü 6.6.87.2-microsoft-standard-WSL2, Python 3.12 ve gcc 13.3.0. WSL2 ağı Windows ana bilgisayarının arkasında NAT ile çalışır; bu yüzden TTL ve ARP çıktıları gerçek bir ev ağından farklı görünür. Kullanıcı `merty` root değildir, `sudo` şifre ister; bu yüzden ham soket (raw socket) ve yakalama (`tcpdump`) yapamadık. Bu sınırı bölüm içinde açıkça belirteceğiz ve yerine geçen yöntemi göstereceğiz.

## 29.1 Katmanlar neden var?

Bir mektubu düşün. Sen yalnızca ne söyleyeceğini bilirsin. Zarfa adresi yazan, pulu yapıştıran, postanenin ayırıp taşıdığı, sonunda kapıya bırakan kişiler ise farklı işler yapar. Her biri yalnızca kendi işini bilir; alıcının postacısı mektubun içeriğini okumaz, yalnızca adrese bakar.

Ağda da aynı fikir geçerlidir ve buna **katmanlı mimari** denir. Her katman tek bir sorunu çözer ve bunu alt katmanın sunduğu hizmetle yapar. Üst katman, alt katmanın nasıl çalıştığını bilmek zorunda değildir. Bu, Bölüm 21'de gördüğün soyutlama ve arayüz fikrinin ağa uygulanmış hâlidir: bir sınıf ne yaptığını bir arayüzle söyler, nasıl yaptığını gizler. Bölüm 21'deki DIP'te yüksek seviye modül bir soyutlamaya bağlanır; burada üst katman, alt katmanın sunduğu "şu hedefe şu veriyi gönder" hizmetine bağlanır.

Katmanlamanın üç büyük kazancı vardır:

- **Değişim maliyeti düşer.** Evde Wi-Fi'den Ethernet'e geçtiğinde HTTP protokolü değişmez, çünkü HTTP yalnızca alt katmanın "bu baytı şu adrese gönder" hizmetine bakar. Bölüm 21'deki SRP ve OCP'nin ağ ölçeğindeki karşılığıdır.
- **Her katman bağımsız gelişir.** IPv6 eklendiğinde TCP'nin kodu büyük ölçüde aynı kaldı; Ethernet'in fiziksel katmanı yıllar içinde bakır kablodan fiber ve radyoya değişti, üstteki katmanlar bunu fark etmedi.
- **Hata ayıklaması kolaylaşır.** "Sayfa açılmıyor" sorununun hangi katmanda olduğunu soru sorarak ayırabilirsin: kablo bağlı mı, IP adresi var mı, port açık mı, uygulama yanıt veriyor mu?

Bir katmanın üst katmana sunduğu şeye **hizmet** (service), karşı taraftaki aynı katmanla konuşma kurallarına **protokol** denir. Bu ayrımı akılda tut; mülakatlarda sık sorulur.

Katmanlar arasında veri nasıl aktarılır? Her katman, kendi başlığını (header) veriye ekler. Alıcıda aynı katman bu başlığı okuyup çıkarır ve geri kalanı yukarı iletir. Bu, bir sonraki bölümde bayt bayt göreceğimiz **kapsülleme** (encapsulation) işlemidir.

## 29.2 OSI ve TCP/IP: iki model, bir gerçek

Ağ katmanlarını anlatan iki model vardır ve ikisi de mülakatta sorulur.

**OSI (Open Systems Interconnection) referans modeli** 7 katman tanımlar: uygulama, sunum, oturum, taşıma, ağ, veri bağı ve fiziksel. ISO tarafından 1980'lerde standartlaştırıldı (genel bilgi: ISO/IEC 7498). OSI bir protokol değildir; bir **düşünme çerçevesidir**. Her katmanın hangi soruyu çözdüğünü tarif eder ama hangi protokolün kullanılacağını söylemez.

**TCP/IP modeli** ise internetin gerçekte çalıştığı yığındır ve 4 katmandan oluşur: ağ erişimi (link), internet, taşıma ve uygulama (genel bilgi: RFC 1122). İnternet protokolleri TCP/IP'nin etrafında gelişti; OSI'nin oturum ve sunum katmanları ise ayrı bir protokol yığını olarak hiçbir zaman yaygınlaşmadı. Bugün bir mühendisin "OSI katmanı" dediğinde çoğunlukla kastettiği, şu temel ayrımdır: 2. katman (anahtar ve MAC adresi), 3. katman (IP ve yönlendirme), 4. katman (port ve TCP/UDP), 7. katman (HTTP gibi uygulama).

| OSI katmanı | TCP/IP karşılığı | Bu bölümdeki örnek |
|---|---|---|
| 7. Uygulama | Uygulama | HTTP, DNS, SMTP (Bölüm 30) |
| 6. Sunum | Uygulama | Biçim ve şifreleme (Bölüm 32'de TLS) |
| 5. Oturum | Uygulama | Oturum yönetimi (çoğunlukla uygulamada) |
| 4. Taşıma | Taşıma | TCP ve UDP |
| 3. Ağ | İnternet | IPv4, IPv6, ICMP |
| 2. Veri bağı | Ağ erişimi | Ethernet, Wi-Fi, ARP |
| 1. Fiziksel | Ağ erişimi | Kablo, sinyal, bit |

Şekil 29.1, iki modeli yan yana koyar. Sağdaki dört kutunun soldaki yedi katmanın birleşik karşılığı olduğuna dikkat et.

![Şekil 29.1: OSI yedi katmanı ile TCP/IP dört katmanının karşılaştırması. Sağdaki kutular, soldaki katmanların birleşik karşılığıdır.](gorseller/b29_osi_tcpip.png)

::: dikkat
Mülakatta "OSI'yi say" sorusuna yalnızca isim sıralamak yetmez. Her katmanın hangi sorunu çözdüğünü ve hangi protokolü örnek verdiğini söyle. "Taşıma katmanı nedir?" sorusuna "port numarasıyla uygulamalar arası iletişimi sağlar ve (TCP'de) güvenilirlik sunar" demek, sadece "4. katman" demekten çok daha değerlidir.
:::

## 29.3 Kapsülleme: bir isteğin bayt bayt yolculuğu

Soyut anlatım yeterli değil. Şimdi tek bir HTTP isteğinin bir Ethernet çerçevesine kadar nasıl sarıldığını bayt bayt görelim.

Diyelim ki tarayıcı şu isteği gönderiyor:

```
GET / HTTP/1.1
Host: example.com

```

Bu metin, satır sonları dahil 37 bayttır. Uygulama katmanı bu baytları üretir ve TCP'ye verir.

**TCP katmanı** 20 baytlık bir başlık ekler. Başlık, kaynak ve hedef portu, sıra numarasını, onay numarasını ve bayrakları taşır. Ortaya bir **TCP segmenti** çıkar: 20 bayt başlık + 37 bayt veri = 57 bayt.

**IPv4 katmanı** 20 baytlık bir başlık ekler. Başlık, kaynak ve hedef IP adresini, yaşam süresini (TTL) ve üst protokolü (TCP için 6) taşır. Ortaya bir **IP paketi** çıkar: 20 + 57 = 77 bayt.

**Ethernet katmanı** 14 baytlık bir başlık ekler (hedef MAC, kaynak MAC, EtherType) ve sonuna 4 baytlık bir denetim kodu (FCS) koyar. Ortaya bir **Ethernet çerçevesi** çıkar: 14 + 77 + 4 = 95 bayt.

Şekil 29.2 bu iç içe geçmiş yapıyı gösterir. Dikkat et: her katman yalnızca kendi başlığını ekler ve kendi sınırlarını bilir. Bir ara düğüm (örneğin yönlendirici) çerçevenin içindeki HTTP metnini okumak zorunda değildir.

![Şekil 29.2: Kapsülleme. Her katman kendi başlığını önüne ekler; alıcı bu başlıkları ters sırayla çıkarır.](gorseller/b29_kapsulleme.png)

Kapsüllemede bir kritik nokta daha var: katmanlar birbirine **nasıl** işaret eder? Alıcı çerçeveyi aldığında hangi katmana vereceğini başlığın içindeki bir alandan öğrenir:

- Ethernet başlığındaki **EtherType** alanı içeride ne olduğunu söyler: `0x0800` IPv4, `0x86DD` IPv6, `0x0806` ARP.
- IPv4 başlığındaki **protokol** alanı üst katmanı söyler: `6` TCP, `17` UDP, `1` ICMP.
- TCP ve UDP başlığındaki **port** alanı, paketin hangi uygulamaya gideceğini söyler.

Buna **çoklama ayrımı** (demultiplexing) denir. Bu üç alan olmadan alıcı gelen baytın ne olduğunu bilemez. Bu zincirin son halkası bölümün ileride göreceği soket API'sidir (Bölüm 31): soket, bir portu bir uygulamaya bağlar.

Aşağıdaki çıktı, bu bölümün ilerisinde ayrıntılı çözeceğimiz bir SYN çerçevesinin ham baytlarıdır. Bu, kapsüllenmiş bir TCP bağlantı isteğidir. Üç katmanın başlıkları art arda dizilmiştir: önce 14 bayt Ethernet, sonra 20 bayt IPv4, sonra 24 bayt TCP (MSS seçeneğiyle).


```term
0000  02 00 00 00 00 09 02 00 00 00 00 05 08 00 45 00
0010  00 2c 1c 46 40 00 40 06 0a 79 0a 00 00 05 0a 00
0020  00 09 c9 3a 00 50 00 00 03 e8 00 00 00 00 60 02
0030  fa f0 bb b5 00 00 02 04 05 b4
```


Bu çerçevenin toplam uzunluğu 58 bayttır (14 + 20 + 24). Bu çerçevenin hiçbir uygulama verisi taşımadığına, yalnızca bağlantı kurma bayraklarını (SYN) taşıdığına dikkat et.

## 29.4 Bağlantı katmanı: Ethernet, MAC, ARP ve anahtar

Bağlantı katmanı (2. katman), **aynı fiziksel ağda** bulunan düğümler arasında çerçeve taşır. Bu ağa yerel ağ (LAN) denir ve yalnızca doğrudan erişebildiğin cihazları kapsar. Bu katmanın adresi **MAC adresidir**: 48 bit, altı onaltılık çift olarak yazılır, örneğin `00:15:5d:91:08:bd`. İlk üç bayt üreticiyi gösterir (OUI), kalan üç bayt cihazı. MAC adresinin ilk baytındaki iki düşük bit özeldir: en düşük bit 1 ise adres bir grup (çok yayın) adresidir; bir sonraki bit 1 ise adres üretici yerine yerel yönetici tarafından atanmıştır. Bu yüzden `02:00:00:00:00:09` gibi adresler yereldir ve çoğu zaman sanal makinelerde ya da test ortamlarında görülür.

Ethernet çerçevesinin düzeni şöyledir:

| Alan | Boyut | Açıklama |
|---|---|---|
| Hedef MAC | 6 bayt | Çerçevenin gideceği arayüz |
| Kaynak MAC | 6 bayt | Çerçeveyi gönderen arayüz |
| EtherType | 2 bayt | İçerideki protokol (`0x0800` IPv4) |
| Yük | 46–1500 bayt | IP paketi (en küçük çerçeveyi tamamlamak için doldurulur) |
| FCS | 4 bayt | CRC-32 denetim kodu; bozuk çerçeve atılır |

Yükün en az 46 bayt olması, toplam çerçevenin en az 64 bayt olmasını sağlar (14 + 46 + 4). Yükün en fazla 1500 bayt olması ise **MTU (Maximum Transmission Unit)** değeridir: bir çerçevenin taşıyabileceği en büyük IP paketi. Sahadaki kartlarda ön yükleme (preamble) ve aralık gibi fiziksel alanlar da vardır; bunlar donanım tarafından eklenir ve yazılımın görmediği bayt dizisinin parçası değildir.

**ARP (Address Resolution Protocol)** IP adresinden MAC adresini bulur. Bir cihaz 192.168.10.20 adresine göndermek ister ama MAC'ini bilmez. Yerel ağa "bu IP kimde?" diye bir ARP isteği yayınlar; hedef MAC'i `ff:ff:ff:ff:ff:ff` olan bir çerçeve herkese gider. Sahibi "bu IP bende, MAC'im şu" diye doğrudan yanıt verir. Öğrenilen eşleşme **komşu tablosunda** (ARP önbelleği) saklanır ve bir süre sonra yeniden doğrulanır.

Aşağıdaki çıktı, bu WSL makinesindeki üç bilgiyi gösterir: IPv4 adresleri, yönlendirme tablosu ve komşu tablosu. Komşu tablosundaki satır, ağ geçidinin (172.21.192.1) MAC adresini bilindiğini ve `REACHABLE` durumunda olduğunu gösterir. Diğer durumlar (`STALE`, `DELAY`) eşleşmenin eskidiğini ya da yeniden sorgulanmakta olduğunu anlatır (genel bilgi).


```term
$ ip -4 -br addr
lo               UNKNOWN        127.0.0.1/8 10.255.255.254/32
eth0             UP             172.21.205.116/20
$ ip route
default via 172.21.192.1 dev eth0 proto kernel
172.21.192.0/20 dev eth0 proto kernel scope link src 172.21.205.116
$ ip neigh
```


Bu kısa çıktı, ağ katmanının neden var olduğunu da anlatır. Ağ geçidi aynı yerel ağdaki bir cihaz olduğu için ona ARP ile ulaşılır. Ama `8.8.8.8` gibi yerel ağ dışındaki bir adrese ARP ile ulaşılamaz; bu adrese giden çerçevenin hedef MAC'i ağ geçidinin MAC'idir. Bunu 29.7'de yönlendirme tablosuyla birlikte göreceğiz.

**Anahtar ile hub arasındaki fark.** Eski **hub** bir porttan gelen çerçeveyi diğer bütün portlara kopyalar. Bütün cihazlar birbirinin trafiğini görür ve aynı anda gönderen iki cihaz çarpışır. **Anahtar (switch)** ise her porta bağlı MAC adreslerini öğrenir: kaynak MAC'i hangi porttan geldiyse o MAC'in o portta olduğunu bir tabloda tutar. Sonraki çerçeveler yalnızca hedef MAC'in bulunduğu porta gider; bilinmeyen ya da yayın (broadcast) çerçeveler ise bütün portlara yayılır (genel bilgi). Modern ağların neredeyse tamamı anahtar kullanır; hub bugün pratikte yoktur.

**VLAN (Sanal yerel ağ).** Tek bir fiziksel anahtarın üzerinde birden çok mantıksal ağ kurmak mümkündür. IEEE 802.1Q standardına göre çerçeveye, kaynak MAC'ten sonra 4 baytlık bir **VLAN etiketi** eklenir: ilk iki bayt `0x8100` (TPID) ve sonraki 12 bit VLAN kimliğidir (VID). Kullanılabilir kimlik aralığı 1–4094'tür (genel bilgi). Savunma ağlarında ve kurumsal ağlarda farklı güvenlik seviyesindeki cihazları aynı fiziksel altyapıda ama birbirinden yalıtılmış tutmak için VLAN kullanılır. Bu bölümde yalnızca fikri anlatıyoruz; anahtar yapılandırması ağ mühendisliğinin konusudur.

**MTU'yu gör.** Bu makinedeki `eth0` arayüzünün MTU değeri 1500'dür. `ip link` çıktısının tamamı çok uzundur; burada yalnızca MTU'nun bulunduğu kısmı alıyoruz.


```term
$ ip link show eth0
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    link/ether 00:15:5d:xx:xx:xx brd ff:ff:ff:ff:ff:ff
```


MTU'dan büyük bir IP paketi göndermek istediğinde iki yol vardır. IPv4'te yönlendirici paketi parçalara (fragment) bölebilir. Paket "parçalanamaz" (DF bayrağı) işaretliyse yönlendirici paketi atar ve gönderene bir ICMP hata mesajı döndürür. Bu mekanizmaya yol MTU keşfi (Path MTU Discovery) denir ve sonraki bölümde TCP'nin segment boyutunu belirlerken yeniden karşımıza çıkacak.

## 29.5 Ağ katmanı I: IPv4 başlığı ve sağlama toplamı

Ağ katmanının görevi, paketi kaynaktan hedefe **adres** kullanarak götürmektir. Bunu IPv4 başlığındaki alanlar yapar. Şekil 29.3'ün sol üst köşesindeki IPv4 bit cetveli, 20 baytlık minimum başlığın her alanını gösterir. Cetvelde bitlerin soldan sağa, üstten alta bayt bayt sıralandığına dikkat et: her satır 32 bittir ve ilk bayt en soldadır.

![Şekil 29.3: IPv4, TCP ve UDP başlıklarının bit cetvelleri. Kutu genişliği bit sayısıyla orantılıdır; Ethernet başlığı alt sırada yer alır.](gorseller/b29_basliklar.png)

Alanları anlamak için birkaç tanesine bakalım:

- **Sürüm ve IHL** ilk baytta birlikte durur. Sürüm 4 bittir (IPv4 için 4); IHL başlık uzunluğunu **32 bitlik sözcük** sayısı olarak verir. IHL = 5 ise başlık 5 × 4 = 20 bayttır. Seçenekler yoksa IHL her zaman 5'tir; seçenekler (en fazla 40 bayt) varsa 15'e kadar çıkabilir.
- **Toplam uzunluk** başlık dahil paketin bayt cinsinden uzunluğudur (en fazla 65535).
- **Kimlik, bayrak ve parça ofseti** parçalanmış paketlerin yeniden birleştirilmesi için vardır. DF (Don't Fragment) bayrağı parçalanmayı yasaklar.
- **TTL (Time To Live)** her yönlendiricide bir azalır; 0'a ulaşınca paket atılır. Bu, ağda sonsuza kadar dönen paketleri önler. 29.8'de traceroute bu alanı kullanır.
- **Protokol** üst katmanı söyler: 1 ICMP, 6 TCP, 17 UDP.
- **Sağlama toplamı** yalnızca başlığı kapsar.

Aşağıdaki hex dizisi, bölümün başında gösterdiğimiz SYN çerçevesinin IPv4 başlığıdır (14. bayttan itibaren 20 bayt): `45 00 00 2c 1c 46 40 00 40 06 0a 79 0a 00 00 05 0a 00 00 09`. İlk bayt `45`: üst dört bit 4 (IPv4), alt dört bit 5 (IHL). Toplam uzunluk `00 2c` = 44; bunun 20'si IP başlığı, 24'ü TCP başlığıdır. `40 00` bayrakları gösterir: DF = 1. TTL 64 (`40`), protokol 6 (`06`), yani TCP.

**Sağlama toplamı (checksum).** IPv4 başlığındaki 16 bitlik sağlama toplamı şöyle hesaplanır (RFC 1071): başlığı 16 bitlik sözcüklere ayır, hepsini topla; taşan bitler en düşük tarafa geri eklenir (bir'in tümleyeni toplaması); sonucun bir'in tümleyenini al. Alıcı başlığın tamamını (sağlama alanı dahil) toplar; sonuç `0xFFFF` ise, yani tümleyeni `0` ise başlık bozulmamıştır. Bu hesabı kullanan kod şudur:


```python
def saglama(bayt):
    if len(bayt) % 2:
        bayt += b"\x00"
    toplam = 0
    for i in range(0, len(bayt), 2):
        toplam += (bayt[i] << 8) | bayt[i + 1]
    while toplam >> 16:
        toplam = (toplam & 0xFFFF) + (toplam >> 16)
    return (~toplam) & 0xFFFF
```


Doğrulamak için bilinen bir örnek kullanalım: Wikipedia'da IPv4 sağlama toplamı örneği olarak sık verilen başlık `45 00 00 73 00 00 40 00 40 11 00 00 c0 a8 00 01 c0 a8 00 c7` (sağlama alanı sıfır) ve beklenen değer `0xb861`dir. Kodu bu örnekle çalıştırdığımızda aynı değeri ve doğrulama toplamı olarak `0x0000` aldık.


```term
== 4. IPv4 sağlama toplamı ==
hesaplanan saglama   : 0xb861
doğrulama (0 olmalı) : 0x0000
```


Burada bir ayrıntıyı vurgulamak gerekir: IPv4 sağlaması yalnızca başlığı korur, veriyi değil. Veriyi koruyan denetim TCP ve UDP başlıklarındadır ve onları 29.10'da göreceğiz. Ayrıca TTL her yönlendiricide değiştiği için sağlama toplamı da her atlamada yeniden hesaplanır (genel bilgi).

## 29.6 Ağ katmanı II: adresleme, alt ağlar ve NAT

IPv4 adresi 32 bittir ve noktalı onluk gösterimle yazılır: `192.168.10.77`. Her adres iki parçaya ayrılır: **ağ kısmı** ve **host kısmı**. Hangi bitlerin ağ kısmı olduğunu **maske** söyler. Maske bitlerin sol tarafında ardışık birlerden oluşur; `/26` yazımı ilk 26 bitin maske olduğunu anlatır (CIDR gösterimi).

Bir ağ adresi için dört değer önemlidir:

- **Ağ adresi** = IP AND maske. Bu adres kendi ağını temsil eder ve host'a verilmez.
- **Yayın (broadcast) adresi** = ağ OR (NOT maske). Bu adrese gönderilen paket ağdaki bütün hostlara gider.
- **Kullanılabilir host sayısı** = 2^(32 − p) − 2. İki adres (ağ ve yayın) düşülür.
- **İlk ve son host** ağ adresinden bir sonraki ve yayın adresinden bir önceki adrestir.

Elle bir örnek: `192.168.10.77/26`. Maske 26 bit: `255.255.255.192`, yani son oktette `11000000`. Son oktet 77 = `01001101`. İkisinin AND'i `01000000` = 64. Ağ adresi `192.168.10.64`tür. Son oktette host kısmı 6 bittir, yani 2^6 = 64 adres; yayın adresi 64 + 63 = 127, ilk host 65, son host 126 ve kullanılabilir host sayısı 62'dir. Şekil 29.4 bu dört bloğu gösterir ve 77'nin hangi bloğa düştüğünü vurgular.

![Şekil 29.4: 192.168.10.0/24 ağının dört /26 bloğa bölünmesi. Vurgulanan blok 192.168.10.77 adresini içerir.](gorseller/b29_alt_ag.png)

Elle yaptığımız işlemi kodda yazalım. İlk parça IPv4 adresini bir tamsayıya çevirir; bütün hesaplar bu tamsayı üzerinde AND ve OR ile yapılır:


```python
# -*- coding: utf-8 -*-
# ag_hesap.py - alt ağ, LPM ve IPv4 sağlama toplamı
# toplamı. Her sonuç Python'un ipaddress modülüyle karşılaştırılır.
import ipaddress
import random


# ---------- 1. IPv4 adresini 32 bitlik tamsayıya çevirme ----------
def ip_sayi(metin):
    parca = [int(x) for x in metin.split(".")]
    sayi = 0
    for p in parca:
        sayi = (sayi << 8) | p
    return sayi


def sayi_ip(s):
    return ".".join(str((s >> sh) & 0xFF) for sh in (24, 16, 8, 0))
```


Alt ağ hesabı şöyle yazılır. `/31` ve `/32` özel durumdur: `/31` iki uçlu bağlantılar için RFC 3021 ile iki adres kullanmaya izin verir; `/32` tek bir adres tanımlar.


```python
def alt_ag(cidr):
    ag, uz = cidr.split("/")
    p = int(uz)
    maske = (0xFFFFFFFF << (32 - p)) & 0xFFFFFFFF
    ip = ip_sayi(ag)
    ag_adresi = ip & maske
    yayin = ag_adresi | (~maske & 0xFFFFFFFF)
    toplam = 1 << (32 - p)
    if p == 32:
        host = 1
        ilk = son = ag_adresi
    elif p == 31:
        host = 2   # RFC 3021: /31 nokta-nokta bağlantı
        ilk, son = ag_adresi, yayin
    else:
        host = toplam - 2
        ilk, son = ag_adresi + 1, yayin - 1
    return {"ag": sayi_ip(ag_adresi), "maske": sayi_ip(maske),
            "ilk": sayi_ip(ilk), "son": sayi_ip(son),
            "yayin": sayi_ip(yayin), "host": host}
```


Aynı sonucu Python'un `ipaddress` modülüyle de hesaplayıp karşılaştırıyoruz. Bağımsız bir uygulama ile aynı sonucu alırsak hem hesabımız hem de doğrulamamız büyük olasılıkla doğrudur.


```python
def alt_ag_dogrula(cidr):
    n = ipaddress.ip_network(cidr, strict=False)
    if n.prefixlen >= 31:
        ilk, son = n.network_address, n.broadcast_address
        if n.prefixlen == 32:
            ilk = son = n.network_address
        host = n.num_addresses if n.prefixlen == 31 else 1
    else:
        ilk = n[1]
        son = n[-2]
        host = n.num_addresses - 2
    return {"ag": str(n.network_address), "maske": str(n.netmask),
            "ilk": str(ilk), "son": str(son),
            "yayin": str(n.broadcast_address), "host": host}


# ---------- 3. En uzun önek eşleşmesi: ikili trie ----------
```


Program beş örneği iki yöntemle hesaplar ve sonuçları karşılaştırır.


```term
$ python3 ag_hesap.py
== 1. Alt ağ hesabı ==
192.168.10.77/26  [UYUMLU]
  ağ=192.168.10.64  yayın=192.168.10.127  maske=255.255.255.192
  ilk=192.168.10.65  son=192.168.10.126  host=62
10.1.2.200/25  [UYUMLU]
  ağ=10.1.2.128  yayın=10.1.2.255  maske=255.255.255.128
  ilk=10.1.2.129  son=10.1.2.254  host=126
172.21.200.9/20  [UYUMLU]
  ağ=172.21.192.0  yayın=172.21.207.255  maske=255.255.240.0
  ilk=172.21.192.1  son=172.21.207.254  host=4094
192.168.1.1/31  [UYUMLU]
  ağ=192.168.1.0  yayın=192.168.1.1  maske=255.255.255.254
  ilk=192.168.1.0  son=192.168.1.1  host=2
10.0.0.5/32  [UYUMLU]
  ağ=10.0.0.5  yayın=10.0.0.5  maske=255.255.255.255
  ilk=10.0.0.5  son=10.0.0.5  host=1
```


**Özel adresler.** IPv4'te adresler kamuya açık (internette tekil) ve özel olarak ayrılmış (RFC 1918) bloklara ayrılır: `10.0.0.0/8`, `172.16.0.0/12` ve `192.168.0.0/16`. Özel adresler internette yönlendirilmez; yalnızca yerel ağda anlamlıdır. Bu makinenin `172.21.205.116/20` adresi de `172.16.0.0/12` bloğunun içindedir.

**NAT (Network Address Translation).** Bir ev ağındaki bilgisayarlar özel adres kullanır, ama internete çıkmak için bir kamusal adrese ihtiyaçları vardır. NAT yönlendiricisi giden paketin kaynak adresini kendi kamusal adresiyle değiştirir ve bir **çeviri tablosu** tutar: (özel adres, özel port) ↔ (kamusal adres, kamusal port). Dönüş paketi geldiğinde tabloya bakıp doğru bilgisayara iletir. Port de çevrildiği için buna çoğu zaman NAPT denir (genel bilgi). NAT, IPv4 adreslerinin tükenmesinin bugüne kadar ertelenmesinin en büyük nedenidir; bedeli ise uçtan uca bağlantıyı zorlaştırmasıdır: dışarıdan içeriye doğrudan bağlantı kurmak ek yapılandırma ister.

## 29.7 Yönlendirme ve en uzun önek eşleşmesi

Bir cihaz bir pakete karar verirken iki soru sorar. Hedef benimle aynı alt ağda mı? Evetse paketi doğrudan hedefe gönderir; ARP ile hedefin MAC'ini bulur. Hayırsa paketi bir **ağ geçidine** (gateway) verir; ağ geçidi paketi kendi bilgisine göre ilerletir. Bu karar, **yönlendirme tablosunda** yazılıdır.


```term
$ ip route
default via 172.21.192.1 dev eth0 proto kernel
172.21.192.0/20 dev eth0 proto kernel scope link src 172.21.205.116
```


Bu makinenin tablosunda iki satır vardır. `172.21.192.0/20 dev eth0 proto kernel scope link` satırı doğrudan bağlı ağı gösterir: bu ağdaki hedeflere ARP ile ulaşılır. `default via 172.21.192.1` satırı ise **varsayılan yoldur** (`0.0.0.0/0`); yukarıdaki satırlara uymayan her hedef ağ geçidine gider.

Peki bir hedef birden çok satıra uyarsa hangisi seçilir? Kural **en uzun önek eşleşmesidir (longest prefix match, LPM)**: hedefi kapsayan bütün önekler arasından en çok bit ile eşleşen kazanır. Örneğin `10.1.2.130` hedefi `0.0.0.0/0`, `10.0.0.0/8`, `10.1.0.0/16`, `10.1.2.0/24` ve `10.1.2.128/25` önüne uyar; kazanan en uzun olan `/25`tir. Şekil 29.5 bu seçimi bit düzeyinde gösterir: her çubuk önekin kapsadığı bit sayısıdır ve hedefi kapsayan çubuklar arasından en uzun olanı seçilir.

![Şekil 29.5: Hedef 10.1.2.130 için yönlendirme önekleri. Hedefi kapsayan beş önek var; en uzun önek olan /25 kazanır.](gorseller/b29_lpm.png)

Bu aramayı hızlı yapmanın doğal yolu bir **ikili trie** (ikili ağaç) kurmaktır. Bölüm 10.9'daki trie'da kelimeleri karakter karakter saklamıştın. Burada aynı fikir ikili düzeyde çalışır: her düğüm bir bit, kökten yaprağa giden her yol bir önek. Adresin bitlerini soldan sağa takip eder, bir önek düğümüne her uğradığında "şu ana kadarki en iyi eşleşme" adayını güncellersin. Arama yalnızca 32 adımdır; tablonun kaç satır olduğuna bağlı değildir. Donanım yönlendiricileri aynı işi çoğu zaman TCAM adı verilen içerik adreslenebilir bellekle yapar (genel bilgi).

Trie'yı yazalım. Düğümde iki çocuk (0 ve 1 bitleri için) ve bir hedef alanı vardır:


```python
class Dugum:
    __slots__ = ("cocuk", "hedef")

    def __init__(self):
        self.cocuk = [None, None]
        self.hedef = None


class YonlendirmeTrie:
    def __init__(self):
        self.kok = Dugum()

    def ekle(self, cidr, hedef):
        ag, uz = cidr.split("/")
        p = int(uz)
        ip = ip_sayi(ag)
        dugum = self.kok
        for i in range(p):
            bit = (ip >> (31 - i)) & 1
            if dugum.cocuk[bit] is None:
                dugum.cocuk[bit] = Dugum()
            dugum = dugum.cocuk[bit]
        dugum.hedef = hedef

    def bul(self, adres):
        ip = ip_sayi(adres)
        dugum = self.kok
        son_eslesme = dugum.hedef   # /0: varsayılan yol
        for i in range(32):
            bit = (ip >> (31 - i)) & 1
            dugum = dugum.cocuk[bit]
            if dugum is None:
                break
            if dugum.hedef is not None:
                son_eslesme = dugum.hedef   # daha uzun eşleşme
        return son_eslesme
```


Tablomuz ve kaba kuvvet karşılaştırması şöyle:


```python
TABLO = [
    ("0.0.0.0/0", "eth0 üzerinden 172.21.192.1 (varsayılan)"),
    ("172.21.192.0/20", "eth0 (doğrudan bağlı)"),
    ("10.0.0.0/8", "vpn0"),
    ("10.1.0.0/16", "vpn1"),
    ("10.1.2.0/24", "ofis-lan"),
    ("10.1.2.128/25", "sensor-ag"),
]


def lpm_brute(adres, tablo):
    ip = ipaddress.ip_address(adres)
    en_iyi, en_uz = None, -1
    for cidr, hedef in tablo:
        n = ipaddress.ip_network(cidr)
        if ip in n and n.prefixlen > en_uz:
            en_iyi, en_uz = hedef, n.prefixlen
    return en_iyi


# ---------- 4. IPv4 başlık saglama toplamı (RFC 1071) ----------
```


Trie'nin doğruluğunu test etmek için 20000 rastgele adreste trie'nin sonucunu, tabloyu her satır için tek tek tarayıp en uzun önek bulan kaba kuvvet sonucuyla karşılaştırdık. Kaba kuvvet yöntemi de her satırı `ipaddress` modülüyle kontrol eder. Tohum `random.seed(29)` ile sabitlenmiştir, yani sonuç her çalıştırmada aynıdır.


```term
== 2. Yönlendirme tablosu ve LPM ==
10.1.2.130       -> sensor-ag
10.1.2.5         -> ofis-lan
10.1.9.9         -> vpn1
10.9.9.9         -> vpn0
172.21.205.116   -> eth0 (doğrudan bağlı)
8.8.8.8          -> eth0 üzerinden 172.21.192.1 (varsayılan)

== 3. Rastgele 20000 adresle trie ve kaba kuvvet karşılaştırması ==
uyuşmayan sonuç sayısı: 0
```


Sonuç: 20000 adreste uyuşmazlık sıfır. Bu, yalnızca birkaç örnek adres test etmekten çok daha güçlü bir kanıttır; yine de bir sınır koşulu kalmış olabilir. Trie'nin sınır koşullarını Kendin Yap bölümünde zorlayacaksın: `/0`, `/32` ve aynı önekin iki kez eklenmesi.

Yönlendirme tablosunun kendisi nereden gelir? Statik yönlendirmede yönetici satırları elle yazar. Büyük ağlarda ise **yönlendirme protokolleri** tabloyu otomatik doldurur. OSPF, ağın bağlantı grafiğinde Dijkstra'yı çalıştırarak en kısa yolları bulur (Bölüm 17.6). RIP ise mesafe vektörü yöntemiyle Bellman-Ford'un bir uyarlamasını kullanır (Bölüm 17.7). Bu algoritmaların ayrıntıları Bölüm 17'de; burada yalnızca sonuçları, yani tabloyu kullanıyoruz.

## 29.8 ICMP, ping ve traceroute

IP paketi teslimde başarısız olduğunda, örneğin TTL sıfıra düştüğünde ya da hedef ulaşılamaz olduğunda, kaynağı bilgilendirmek gerekir. Bu iş **ICMP (Internet Control Message Protocol)** ile yapılır. ICMP IP'nin üstünde değil, aynı katmanda çalışan bir protokoldür: IP paketinin yükü olarak taşınır ve protokol numarası 1'dir. Önemli ICMP türleri şunlardır:

| ICMP türü | Anlamı | Kullanım |
|---|---|---|
| 8 (echo isteği) ve 0 (echo yanıtı) | Hedefin canlı olup olmadığını sor | `ping` |
| 3 (hedef ulaşılamaz) | Paket teslim edilemedi | Hata bildirimi |
| 11 (zaman aşımı) | TTL sıfıra düştü | `traceroute` |

**ping** bir echo isteği gönderir ve yanıtın süresini ölçer. Bu süre, yolun gidiş dönüş gecikmesidir (RTT). Bu bölümde ping'i yalnızca bağlantının varlığını doğrulamak için değil, TTL alanını göstermek için kullanacağız.

**traceroute** TTL alanını kasıtlı olarak küçültür. TTL = 1 ile gönderilen paket ilk yönlendiricide düşer ve o yönlendirici kendi adresiyle bir ICMP zaman aşımı mesajı döndürür. TTL = 2 ile gönderilen paket ikinci yönlendiricide düşer ve onun adresi görülür. Bu şekilde her atlama, sırayla kendini bildirir. Hedefe ulaşıldığında echo yanıtı gelir. Aşağıdaki iki komut bu yöntemi elle yapar:


```term
$ ping -c 1 -t 1 -W 2 8.8.8.8
From 172.21.192.1 icmp_seq=1 Time to live exceeded
$ ping -c 1 -t 2 -W 2 8.8.8.8
From 192.168.1.1 icmp_seq=1 Time to live exceeded
```


İlk satır, paketin ilk düğümde (`172.21.192.1`, Windows tarafındaki sanal ağ geçidi) düştüğünü; ikinci satır, TTL = 2 ile ikinci düğümde (`192.168.1.1`, ev yönlendiricisi, WSL'nin dış ağında) düştüğünü gösterir. Bu iki satır, arada üç ayrı ağın (WSL'nin sanal ağı, Windows'un NAT'ı ve ev ağı) iç içe geçtiğini de gösterir. Gerçek bir internet yolunda atlama sayısı çoğu zaman bundan çok daha fazladır.

Bu makinede `traceroute` kurulu değildi ve ham soketi açmak root gerektiriyordu: `AF_PACKET` ile bir soket açmaya çalıştığımızda `PermissionError: Operation not permitted` hatası alındı. Yani yolu ancak `ping`in TTL seçeneğiyle izleyebildik. Ayrıca bu oturumda ağ geçidine gönderilen echo isteklerine yanıt gelmedi; Windows tarafı ICMP yanıtlarını engelliyor olabilir (tahmin; doğrulanmadı). Bu, ağ katmanında pingin her zaman başarılı olmadığını da hatırlatır.

## 29.9 IPv6 kısaca

IPv4 adresleri 2^32 tanedir, yani yaklaşık 4,3 milyar, ve bugünkü cihaz sayısına yetmez. **IPv6** adresleri 128 bittir ve yazılımı şöyle gösterilir: sekiz grup, her grup dört onaltılık basamak, gruplar iki nokta üst üste ile ayrılır. Ardışık sıfır grupları bir kez `::` ile kısaltılabilir ve baştaki sıfırlar atılabilir. Örneğin `fe80:0000:0000:0000:0211:22ff:fe33:4455` yazımı `fe80::211:22ff:fe33:4455` olur. `::` bir adreste en fazla bir kez kullanılabilir; yoksa kısaltmanın nereye ait olduğu belirsizleşirdi.

IPv6'nın bazı tasarım farkları önemlidir (genel bilgi):

- **Sabit 40 baytlık başlık.** IPv4'te değişken uzunluklu IHL alanı yoktur; yönlendiricilerin işi basitleşir.
- **Başlıkta sağlama toplamı yoktur.** Bütünlük üst katmanlarda (TCP, UDP) ve bağlantı katmanında denetlenir.
- **Parçalama yalnızca gönderende yapılır.** Yönlendiriciler paketi parçalamaz; bu nedenle yol MTU keşfi IPv6'da daha da önemlidir.
- **ARP yerine NDP.** Komşu keşfi ICMPv6 mesajlarıyla yapılır ve yayın yerine çoklu yayın (multicast) adresleri kullanır.

Adresler arasında bağlantı yerel (link-local) adresler `fe80::/10` bloğundadır ve her arayüzde otomatik oluşur. Bunların arayüz kimliği çoğu zaman MAC adresinden türetilir (EUI-64): MAC'in ilk baytındaki yerel bit çevrilir (`00` → `02`) ve ortasına `ff:fe` eklenir. Örneğin MAC `00:11:22:33:44:55` için bağlantı yerel adres `fe80::211:22ff:fe33:4455` olur. Bu bir örnek MAC'tir; kendi arayüzünde de aynı kuralla üretilmiş bir `fe80::` adresi görebilirsin (`ip -6 -br addr`). Bu kural, IPv6 adreslerinin MAC'ten sızdırabileceği bir gizlilik konusu olarak da bilinir; modern işletim sistemleri bu nedenle geçici adresler de üretir (genel bilgi).

::: ipucu
IPv6 adreslerinin yazımını elle kontrol etmek kolay değildir. Python'un `ipaddress` modülü hem IPv4 hem IPv6 adreslerini ayrıştırır ve kısaltılmış yazımı otomatik normalleştirir. Bölüm sonundaki alıştırmalarda bunu kullanacaksın.
:::

## 29.10 Taşıma katmanı: portlar, UDP ve TCP'nin ilk bakışı

Ağ katmanı paketi doğru **makineye** getirir. Ama bir makinede onlarca uygulama aynı anda çalışır; paketin hangisine gideceğini söyleyen şey **port**tur. Port 16 bitlik bir sayıdır (0–65535). Bir bağlantı beş değerle tanımlanır: kaynak IP, kaynak port, hedef IP, hedef port ve protokol. Bu beşliye **5'li (5-tuple)** denir ve bir bağlantının kimliğidir. Sunucu tarafında bir uygulama belirli bir portu dinlediğini (`listen`) bildirir; istemci de geçici bir port seçer. Geçici port aralığı genellikle 32768–60999'dur (genel bilgi).

Taşıma katmanında iki protokol vardır. **UDP** en basit taşıma hizmetidir: port ekler ve uzunluk ile sağlama toplamı koyar, başka bir şey yapmaz. UDP başlığı 8 bayttır ve Şekil 29.3'te görülür. Bağlantı kurmaz, sıra numarası kullanmaz, kayıp olursa bildirmez ve yeniden göndermez. Bu "eksik" gibi görünür ama bir avantajdır: kontrol yükü yoktur ve gecikme düşüktür. **TCP** ise güvenilir, sıralı, bayt akışı sunar. Bunun bedeli 20 baytlık başlık, bağlantı kurma gecikmesi ve kendi tıkanıklık denetimidir.

Hangisini seçeceğin uygulamanın ihtiyacına bağlıdır:

| Özellik | TCP | UDP |
|---|---|---|
| Bağlantı | Üçlü el sıkışma ile kurulur | Yok |
| Güvenilirlik | Kayıp yeniden iletilir | Uygulama sorumluluğu |
| Sıralama | Sıra numarasıyla korunur | Yok; paketler sırasız gelebilir |
| Akış ve tıkanıklık denetimi | Var | Yok |
| Başlık boyutu | 20 bayt ve üstü | 8 bayt |
| Yayın (broadcast/multicast) | Yok | Var |
| Gecikme | Kayıp varsa artar | Düşük ve öngörülebilir |
| Tipik kullanım | Web, e-posta, dosya aktarımı | DNS sorguları, akış, telemetri, oyun |

Bir ayrıntı: UDP'de sağlama toplamı isteğe bağlıdır. IPv4'te 0 değeri "sağlama yok" anlamına gelir; ancak çoğu sistem sağlamayı hesaplar.

**Gerçek zamanlı telemetri ve İHA videosu neden UDP'ye yaslanır?** Bir İHA'nın konum ve tutum verisi saniyede onlarca kez gelir. Bir paket kaybolursa yeniden iletilmiş eski bir konum verisinin bir anlamı yoktur; yeni olan veri daha değerlidir. TCP ise kayıp olan paketi yeniden isteyip diğer paketleri bu paket gelene kadar bekletir (**başlık sırası engeli**, head-of-line blocking). Bu bekleme, gerçek zamanlı veride gecikmeyi kabul edilemez seviyeye çıkarabilir. Bu yüzden telemetri ve video akışları çoğu zaman UDP üzerinden taşınır ve uygulama kendi sıra numarasını, kayıp tespitini ve gerekirse yeniden istemeyi kendisi yapar. MAVLink gibi İHA iletişim protokollerinin UDP üzerinde çalışabilmesi de bu fikre dayanır (genel bilgi). Google'ın QUIC protokolü de UDP üzerinde güvenilirlik kurar; onu Bölüm 30'da HTTP ile birlikte göreceksin.

Bu karşılaştırmanın bir sonucu: **güvenilirlik ile gecikme arasında bir takas vardır.** TCP'de her şey yolunda gider ama kayıp anında bekleme olur; UDP'de bekleme yoktur ama veriyi koruma sorumluluğu uygulamanın omuzlarındadır.

## 29.11 TCP bağlantısının yaşamı: el sıkışma, kapanış ve durumlar

TCP bağlantısı bir **durum makinesidir** (Bölüm 22'de State kalıbıyla tanıdığın yapı). Her bağlantı, belirli bir an için tek bir durumdadır ve olaylar (bir segment gelmesi, uygulamanın bir işlem istemesi, bir zamanlayıcının dolması) durumu değiştirir.

TCP başlığının alanları şunlardır: kaynak ve hedef port, **sıra numarası** (gönderilen ilk baytın konumu), **onay numarası** (karşıdan beklenen sonraki bayt), **ofset** (başlık uzunluğu, 32 bitlik sözcük cinsinden), **bayraklar** (SYN, ACK, FIN, RST, PSH, URG ve ECE/CWR), **pencere** (alıcının kabul edebileceği bayt sayısı), **sağlama toplamı** ve **acil işaretçi**. Şekil 29.3'teki TCP bit cetveli bu düzeni gösterir.

TCP sağlama toplamı IPv4'ünkinden farklıdır: sahte bir başlık (pseudo header) ile birlikte hesaplanır. Sahte başlık kaynak IP, hedef IP, sıfır baytı, protokol numarası (6) ve TCP uzunluğunu içerir; böylece bir segment yanlış adrese yönlendirilirse de hata yakalanır. Sağlama, başlık ve veriyi birlikte kapsar.

**Üçlü el sıkışma (three-way handshake).** Bağlantı kurmak için üç segment gerekir:

1. İstemci `SYN` gönderir ve kendi başlangıç sıra numarasını (ISN) bildirir. Bu segment veri taşımasa da sıra numarasında 1 yer kaplar.
2. Sunucu `SYN+ACK` ile yanıt verir: kendi ISN'ini bildirir ve istemcinin ISN'i + 1'i onaylar.
3. İstemci `ACK` ile sunucunun ISN'i + 1'i onaylar. Bağlantı artık kuruldu; veri gönderilebilir.

Bu üç adım en az bir gidiş-dönüş süresi (RTT) alır. Yani uzak bir sunucuya ilk veri, bağlantı kurulduktan sonra gider. Şekil 29.7 bu el sıkışmayı ve dörtlü kapanışı zaman çizelgesi olarak gösterir.

**Dörtlü kapanış.** Bağlantı iki yönde ayrı ayrı kapanır. Taraf kendi tarafındaki veri akışını bitirdiğinde `FIN` gönderir; karşı taraf bunu `ACK` ile onaylar ve kendi verisini göndermeye devam edebilir. Karşı taraf da işini bitirince kendi `FIN`'ini gönderir ve o da onaylanır. Bu yüzden kapanışta genellikle dört segment vardır. İlk kapatan taraf (**aktif kapatan**) sonunda **TIME_WAIT** durumuna girer ve yaklaşık iki maksimum segment ömrü (2MSL) bekler; Linux'ta bu süre tipik olarak 60 saniyedir (genel bilgi). Bu bekleme iki sebeple vardır: son `ACK` kaybolursa karşı taraf `FIN`'ini yeniden gönderir ve bu `ACK`'i tekrar verebilmek gerekir; ayrıca ağda kalmış eski bir segmentin yeni bir bağlantıya karışmasını önlemek için.

Şekil 29.6 tüm durumları ve geçişleri gösterir. Geçişlerin numaraları, altındaki listeyle eşleşir.

![Şekil 29.6: TCP durum makinesi. Üst satır açılış ve aktif kapanışı, alttaki sağ dal pasif kapanışı gösterir. Numaralı geçişler alttaki listededir.](gorseller/b29_tcp_durum.png)

![Şekil 29.7: Üçlü el sıkışma ve dörtlü kapanışın zaman çizelgesi. Sıra ve onay numaraları her segmentte görünür.](gorseller/b29_el_sikisma.png)

Durumları gözlemek için `ss` komutunu kullanacağız. Aşağıdaki program, bir sunucu ve bir istemci arasında bağlantı kurup kapatır ve her adımda `ss -tan` çıktısını alır. Sunucu için boş bir port (0) seçiyoruz; böylece önceki deneylerden kalan soketler çıktıya karışmaz. Bu programda soket API'sinin ayrıntılarını anlatmıyoruz; Bölüm 31'de bunu baştan yapacağız. Burada yalnızca durum geçişlerini görmek için en küçük kodu kullandık.


```python
# -*- coding: utf-8 -*-
# tcp_durum.py - TCP durumlarını ss ile izler (root gerekmez).
# Sunucu port 0 ile açılır; eski soketler çıktıya karışmaz.
import socket
import subprocess
import time


def ss_goster(port, baslik):
    filtre = "( sport = :%d or dport = :%d )" % (port, port)
    cikti = subprocess.run(["ss", "-tan", filtre],
                           capture_output=True, text=True).stdout
    print("--- " + baslik)
    print(cikti.rstrip())


def main():
```



```python
    sunucu = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sunucu.bind(("127.0.0.1", 0))
    sunucu.listen(5)
    port = sunucu.getsockname()[1]
    ss_goster(port, "1. listen() sonrası")

    istemci = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    istemci.connect(("127.0.0.1", port))
    baglanti, _ = sunucu.accept()
    time.sleep(0.05)
    ss_goster(port, "2. connect() + accept() sonrası")

    istemci.close()          # istemci önce kapatır: aktif kapanış
    time.sleep(0.05)
    print("--- 3. Sunucu EOF'u okuyana kadar (recv b'') ...")
    veri = baglanti.recv(16)
    print("    recv döndü:", veri)
    ss_goster(port, "3. istemci close() sonrası")

    baglanti.close()         # sunucu da kapatır
    time.sleep(0.05)
    ss_goster(port, "4. sunucu close() sonrası")

    sunucu.close()


if __name__ == "__main__":
    main()
```


Çıktı şöyle:


```term
$ python3 tcp_durum.py
--- 1. listen() sonrası
State  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess
LISTEN 0      5          127.0.0.1:45431      0.0.0.0:*
--- 2. connect() + accept() sonrası
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      5          127.0.0.1:45431      0.0.0.0:*
ESTAB  0      0          127.0.0.1:40966    127.0.0.1:45431
ESTAB  0      0          127.0.0.1:45431    127.0.0.1:40966
--- 3. Sunucu EOF'u okuyana kadar (recv b'') ...
    recv döndü: b''
--- 3. istemci close() sonrası
State      Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN     0      5          127.0.0.1:45431      0.0.0.0:*
FIN-WAIT-2 0      0          127.0.0.1:40966    127.0.0.1:45431
CLOSE-WAIT 0      0          127.0.0.1:45431    127.0.0.1:40966
--- 4. sunucu close() sonrası
State     Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN    0      5          127.0.0.1:45431      0.0.0.0:*
TIME-WAIT 0      0          127.0.0.1:40966    127.0.0.1:45431
```


Çıktıdaki adımları Şekil 29.6 ile eşleştir:

- **1. adım:** Sunucu `listen` çağırdı; port `LISTEN` durumunda.
- **2. adım:** Bağlantı kuruldu. İki soket de `ESTAB` durumunda. `ss` bu durumu `ESTAB` diye kısaltır; çekirdek ise `ESTABLISHED` der. İki satırın yerel ve uzak adresleri birbirinin tersidir: bu, iki uçtan aynı bağlantıyı gördüğünü gösterir.
- **3. adım:** İstemci `close` çağırdı ve `FIN` gönderdi. İstemci tarafı `FIN-WAIT-2` durumunda (sunucunun `ACK`'ini aldı, sunucunun `FIN`'ini bekliyor). Sunucu tarafı `CLOSE-WAIT` durumunda: uygulama `recv` çağrısında sıfır bayt (EOF) aldı ama henüz kendi `close`'unu çağırmadı. Bu durum, uygulamada bir `close` eksikliğinin işaretidir; çok sayıda `CLOSE-WAIT` görüyorsan uygulama soketlerini kapatmıyor demektir.
- **4. adım:** Sunucu da kapattı. Aktif kapatan istemci `TIME-WAIT` durumunda kalıyor. Sunucunun kabul ettiği bağlantı soketi kapandığı için listede yok; yalnızca dinleyen (`LISTEN`) soket hâlâ açık.

::: dikkat
`TIME-WAIT` durumundaki soketler kendilerine ait bir 2MSL süresi bekler ve bu süre dolana kadar aynı 5'li ile yeni bir bağlantı açılamaz. Gerçek sunucularda binlerce `TIME-WAIT` soketi görmek normaldir; sorun olan, `CLOSE-WAIT` soketlerinin birikmesidir, çünkü onlar uygulamanın kapatmasını bekler ve sonsuza kadar bekleyebilir.
:::

## 29.12 Sıra numaraları, onaylar, kayan pencere ve yeniden iletim

TCP bir **bayt akışı** sunar; paket sınırları yoktur. Bu yüzden sıra numarası segmentteki ilk baytın konumunu gösterir ve her bayt bir sıra numarası taşır. Bir segment `seq = 1000` ve 100 bayt veri taşıyorsa, sonraki segment `seq = 1100` ile başlamalıdır. Onay numarası ise alıcının **bir sonraki beklediği bayttır**. `ack = 1100` demek, "1099'a kadar olan bütün baytları aldım, şimdi 1100'ü bekliyorum" demektir. Bu kümülatif bir onaydır: tek bir onay, öncesindeki bütün baytları kapsar.

SYN ve FIN segmentleri veri taşımasa da sıra numarasında birer yer kaplar. Bu yüzden el sıkışmada `ack = ISN + 1` olur.

**Kayan pencere (sliding window).** Gönderici, onaylanmamış veriyi sınırsız gönderemez. İki sınır vardır. Alıcının pencere alanı (`rwnd`) alıcının boş tampon alanını bildirir; bu **akış kontrolüdür** (alıcı taşmasın diye). Tıkanıklık penceresi (`cwnd`) ise ağın kaldırabileceği miktarı tahmin eder; bunu 29.13'te göreceğiz. Göndericinin uçuştaki (onaylanmamış) veri miktarı ikisinin en küçüğüdür: `min(cwnd, rwnd)`.

Şekil 29.8'de bir gönderici penceresi görünüyor. Sol taraftaki kutular onaylanmış segmentlerdir. Ortadakiler gönderilmiş ama henüz onaylanmamıştır; **SND.UNA** en eski onaylanmamış baytı, **SND.NXT** bir sonraki gönderilecek baytı gösterir. Sağdaki kutular ise pencerenin dışındadır: alıcı kabul etmez. Pencere kayarken sol kenar ilerler (yeni onaylar gelir) ve sağ kenar da alıcının yeni pencere bildirimine göre hareket eder.

![Şekil 29.8: Kayan pencere. Gönderici, onaylanmamış veri ile pencere sınırı arasındaki baytları uçuşta tutabilir.](gorseller/b29_kayan_pencere.png)

**Yeniden iletim.** Bir segment ya da onayı kaybolursa gönderici sonsuza kadar beklemez. Her uçuştaki veri için bir **yeniden iletim zamanlayıcısı** (RTO) çalışır. Zamanlayıcı dolmadan onay gelmezse segment yeniden gönderilir. RTO değeri ölçülen gidiş-dönüş sürelerine göre uyarlanır (RFC 6298); Linux'ta alt sınır tipik olarak 200 milisaniyedir (genel bilgi). Zamanlayıcıyı beklemeden önce daha hızlı bir yol da vardır: alıcı bir boşluk gördüğünde aynı onay numarasını tekrar tekrar gönderir (**tekrarlanan ACK**). Üç tekrarlanan ACK görülünce gönderici kayıp olduğunu varsayar ve segmenti hemen yeniden gönderir (**hızlı yeniden iletim**, RFC 5681; genel bilgi). Bu mekanizmayı Çözümlü Örnek 4'te adım adım izleyeceğiz.

## 29.13 Tıkanıklık kontrolü: AIMD

Akış kontrolü alıcıyı korur; **tıkanıklık kontrolü** ağı korur. İnternetteki bir yönlendirici kuyruğu dolduğunda paketleri atar. Eğer her gönderici pencerelerini sonsuza kadar büyütürse ağ çöker: buna tıkanıklık çöküşü denir. TCP'nin çözümü, göndericiye ağ hakkında bilgiyi kayıplardan öğrenmesini sağlamaktır.

Gönderici bir **tıkanıklık penceresi** (cwnd) tutar ve kayıp belirtisi olmadığı sürece onu büyütür. Algoritma iki evrelidir:

- **Yavaş başlangıç (slow start):** cwnd her RTT'de yaklaşık iki katına çıkar (her onaylanan segment için cwnd bir artar). Bu, ağın kapasitesini hızla keşfetmek içindir.
- **Tıkanıklık kaçınma (congestion avoidance):** cwnd bir eşik değerine (`ssthresh`) ulaşınca artış yavaşlar: her RTT'de yalnızca 1 segment eklenir. Buna **toplamsal artış** (additive increase) denir.
- **Kayıpta çarpımsal azalma:** Kayıp algılandığında cwnd yarıya iner (multiplicative decrease) ve `ssthresh` de bu değere çekilir.

Bu üç kural birlikte **AIMD** (Additive Increase, Multiplicative Decrease) adını alır. AIMD'nin ünlü özelliği şudur: birden çok gönderici aynı yolu paylaştığında, yalnızca bu kurallarla hepsinin payları zamanla eşitlenir (Chiu ve Jain'in 1989 çalışması; genel bilgi). Yavaş büyüme ve sert küçülme, ağın kapasitesi ile paylaşım adaleti arasında denge kurar.

Bu algoritmanın kaydedilmiş bir şekli testere dişi (sawtooth) grafiğidir. Aşağıdaki simülasyon, bu davranışın en sade hâlini kod olarak gösterir. Model idealize edilmiştir: yol kapasitesi sabit 40 paket, kayıp yalnızca kapasiteyi aştığında oluşur ve rastgelelik yoktur. Gerçek bir TCP yığını bunlardan daha karmaşıktır: başlangıç pencere boyutu modern Linux'ta 10 segmenttir (RFC 6928; genel bilgi), kayıp ayrıntısı daha inceliklidir ve Linux varsayılanı CUBIC'tir.


```python
# -*- coding: utf-8 -*-
# aimd_sim.py - cwnd'nin RTT adımlarındaki evrimi (AIMD).
# Model (Reno benzeri, sadeleştirilmiş):
#   - yavaş başlangıç: cwnd < ssthresh ise her RTT'de iki katına çıkar
#   - kaçınma: cwnd >= ssthresh ise her RTT'de +1
#   - kayıp: cwnd KAPASITE'yi aşınca (deterministik)
#     kayıpta ssthresh = cwnd/2 ve cwnd = ssthresh
# Rastgele kayıp kullanılmadığı için sonuç her çalıştırmada aynıdır.
# Kullanım: python aimd_sim.py <çıktı.csv>
import csv
import sys

RTT_SAYISI = 120
KAPASITE = 40        # yol kapasitesi (paket cinsinden), örnek değer
SSTHRESH_BASLANGIC = 32
```



```python
def simule_et():
    cwnd = 1
    ssthresh = SSTHRESH_BASLANGIC
    satirlar = []
    for rtt in range(RTT_SAYISI):
        if cwnd > KAPASITE:
            # kayıp: o andaki cwnd kaydedilir, sonra azalır
            satirlar.append((rtt, cwnd, ssthresh, 1))
            ssthresh = max(cwnd // 2, 2)
            cwnd = ssthresh
            continue
        satirlar.append((rtt, cwnd, ssthresh, 0))
        if cwnd < ssthresh:
            cwnd = cwnd * 2
        else:
            cwnd = cwnd + 1
    return satirlar
```



```python
if __name__ == "__main__":
    cikti = sys.argv[1] if len(sys.argv) > 1 else "b29_aimd.csv"
    veri = simule_et()
    with open(cikti, "w", newline="", encoding="utf-8") as f:
        yaz = csv.writer(f)
        yaz.writerow(["rtt", "cwnd", "ssthresh", "kayip"])
        yaz.writerows(veri)
    kayip_anlari = [r for r, _, _, k in veri if k]
    print("satır:", len(veri), "kayıp RTT'leri:", kayip_anlari)
    print("ilk 12 satır (rtt, cwnd, ssthresh, kayip):")
    for s in veri[:12]:
        print("  ", s)
```


Çıktı:


```term
$ python3 aimd_sim.py b29_aimd.csv
satır: 120 kayıp RTT'leri: [14, 36, 58, 80, 102]
ilk 12 satır (rtt, cwnd, ssthresh, kayip):
   (0, 1, 32, 0)
   (1, 2, 32, 0)
   (2, 4, 32, 0)
   (3, 8, 32, 0)
   (4, 16, 32, 0)
   (5, 32, 32, 0)
   (6, 33, 32, 0)
   (7, 34, 32, 0)
   (8, 35, 32, 0)
   (9, 36, 32, 0)
   (10, 37, 32, 0)
   (11, 38, 32, 0)
```


Kayıp RTT'leri 14, 36, 58, 80 ve 102'dir: her biri bir öncekinden tam 22 adım sonra gelir, yani model her 22 RTT'de bir testere dişi tekrar eder. Şekil 29.9 bu dişleri çizer.

![Şekil 29.9: AIMD simülasyonu. Kayıp anında cwnd yarıya iner; ardından toplamsal artışla yeniden tırmanır. Kesikli çizgi ssthresh değeridir.](gorseller/b29_aimd.png)

Bu makinedeki gerçek varsayılan algoritmayı da sorgulayabiliriz. Çıktıda `cubic` seçilidir ve kullanılabilen seçenekler `reno` ve `cubic`'tir. Reno, yukarıdaki AIMD'nin klasik biçimidir; CUBIC ise pencereyi bir kübik fonksiyonla büyütür ve kayıptan sonra daha yüksek bir çarpan (yaklaşık 0,7) uygular (genel bilgi).


```term
$ sysctl net.ipv4.tcp_congestion_control
net.ipv4.tcp_congestion_control = cubic
$ sysctl net.ipv4.tcp_available_congestion_control
net.ipv4.tcp_available_congestion_control = reno cubic
```


## 29.14 Nagle algoritması ve gecikmeli onay

TCP küçük segmentleri hemen göndermek yerine bekleyebilir. Bu, bağlantının verimliliğini artırmak için yapılır. Ama aynı bekleme, bazı uygulamalarda ciddi gecikmeye yol açar. Bu bölümde iki mekanizmayı birlikte ölçeceğiz.

**Nagle algoritması** (RFC 896): Gönderilmiş ama henüz onaylanmamış veri varken, tam boyutlu (MSS) olmayan yeni bir segment gönderilmez; yeni veri birikir ve onay geldiğinde tek bir segmentte gönderilir. Amaç, küçük yazılardan oluşan çok sayıda küçük segment yerine daha az ve daha büyük segment göndermektir. Bu, uzaktan terminal oturumları gibi tek tek karakter gönderen uygulamalar için yararlıdır.

**Gecikmeli onay (delayed ACK):** Alıcı her segmente hemen onay göndermek yerine kısa bir süre (Linux'ta yaklaşık 40 milisaniye; genel bilgi) bekler; bu sürede bir yanıt verisi çıkarsa onay onunla birlikte gider.

İki mekanizma birleşince bir tuzak doğar. Uygulama iki küçük parçayı ardı ardına yazarsa: ilk parça hemen gider. İkinci parça, ilk parçanın onayı gelene kadar Nagle tarafından tutulur. Ama alıcı ilk parçanın onayını gecikmeli olarak gönderir; çünkü alıcı, uygulamasının yanıt vermesi için ikinci bir parça bekler. Sonuç: iki taraf da birbirini bekler ve bu bekleme gecikmeli onay süresi kadardır.

Bu durumu ölçelim. Program, istemcinin 4 baytlık bir başlık ve 60 baytlık bir gövde gönderdiğini; sunucunun 64 baytın tamamını okuyunca 1 baytlık bir yanıt verdiğini simüle eder. Üç senaryo vardır: tek yazı (A), iki yazı ve Nagle açık (B), iki yazı ve `TCP_NODELAY` (C). `TCP_NODELAY` seçeneği Nagle'ı kapatır.


```python
# -*- coding: utf-8 -*-
# nagle_olcum.py - Nagle ve gecikmeli onay etkisini loopback'te ölçer.
# Tur: istemci 4 bayt ve sonra 60 bayt yazar (küçük iki yazı), sunucu
# 64 baytın tamamını okuyunca 1 bayt yanıt verir. Süre = bir tur.
import socket
import statistics
import threading
import time

TUR = 40
MESAJ = 64
BASLIK = 4


def tam_oku(s, n):
    parca = bytearray()
    while len(parca) < n:
        b = s.recv(n - len(parca))
        if not b:
            raise EOFError("bağlantı kapandı")
        parca += b
    return bytes(parca)


def sunucu(port, hazir):
    dinleyici = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dinleyici.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    dinleyici.bind(("127.0.0.1", port))
    dinleyici.listen(1)
    hazir.set()
    baglanti, _ = dinleyici.accept()
    with baglanti:
        for _ in range(TUR):
            tam_oku(baglanti, MESAJ)
            baglanti.sendall(b"K")
    dinleyici.close()
```



```python
SONUCLAR = []


def olc(ad, port, nodelay, iki_yazi):
    hazir = threading.Event()
    t = threading.Thread(target=sunucu, args=(port, hazir))
    t.start()
    hazir.wait()
    istemci = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if nodelay:
        istemci.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    istemci.connect(("127.0.0.1", port))
    sureler = []
    govde = b"x" * (MESAJ - BASLIK)
    for _ in range(TUR):
        t0 = time.perf_counter()
        if iki_yazi:
            istemci.sendall(b"h" * BASLIK)
            istemci.sendall(govde)
        else:
            istemci.sendall(b"h" * BASLIK + govde)
        tam_oku(istemci, 1)
        sureler.append((time.perf_counter() - t0) * 1000.0)
    istemci.close()
    t.join()
    kalan = sureler[5:]  # ilk turlar bağlantı gürültüsü
    med = statistics.median(kalan)
    SONUCLAR.append((ad, med, statistics.mean(kalan)))
    print("%-30s medyan=%8.3f ms ort=%8.3f ms" % (
        ad, statistics.median(kalan), statistics.mean(kalan)))
```



```python

if __name__ == "__main__":
    import csv
    import sys
    olc("A: tek yazı (Nagle fark etmez)", 9041, False, False)
    olc("B: iki yazı, Nagle AÇIK", 9042, False, True)
    olc("C: iki yazı, TCP_NODELAY", 9043, True, True)
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", newline="",
                  encoding="utf-8") as f:
            yaz = csv.writer(f)
            yaz.writerow(["senaryo", "medyan_ms", "ortalama_ms"])
            for ad, med, ort in SONUCLAR:
                yaz.writerow([ad, "%.3f" % med, "%.3f" % ort])
```


Çıktı:


```term
$ python3 nagle_olcum.py
A: tek yazı (Nagle fark etmez) medyan=   0.067 ms ort=   0.067 ms
B: iki yazı, Nagle AÇIK        medyan=  43.999 ms ort=  44.009 ms
C: iki yazı, TCP_NODELAY       medyan=   0.054 ms ort=   0.075 ms
```


Sonuç nettir. A senaryosunda tek yazı olduğu için Nagle'ın tutacağı bir şey yoktur; bir tur yaklaşık 0,05–0,08 milisaniyedir. B senaryosunda iki küçük yazı yaklaşık 44 milisaniye sürer; bu değer gecikmeli onay süresine çok yakındır ve bekleme tam olarak buradan gelir. C senaryosunda `TCP_NODELAY` ile yine 0,06–0,08 milisaniyedir. Şekil 29.10, B senaryosunun neden bu kadar büyük göründüğünü log ölçekte gösterir.

![Şekil 29.10: Nagle ve TCP_NODELAY ölçümü. Log ölçekte, iki küçük yazı Nagle açıkken yaklaşık 44 milisaniye sürerken diğer iki senaryo onda bir milisaniyenin altındadır.](gorseller/b29_nagle.png)

Bu sonucun pratik dersi şudur: **etkileşimli, istek-yanıt biçimli uygulamalarda** (oyun, komut-kontrol, çok küçük mesajlı protokoller) birden çok küçük yazıyı tek bir yazıda birleştirmek ya da `TCP_NODELAY` açmak gerekir. Toplu veri akışında ise Nagle'ı açık bırakmak genellikle daha verimlidir. Asıl ders, bu iki mekanizmanın etkileşimini bilmektir; ikisinden birini körü körüne kapatmak ya da açık bırakmak yerine, uygulamanın gönderme deseninin ne olduğuna bakmak gerekir. Loopback'te ölçtüğümüz 44 milisaniye, gerçek bir ağda RTT ile birlikte büyür.

## 29.15 Paket yakalama ve elle ayrıştırma

Gerçek bir ağ hatasını ayıklarken çoğu zaman paketin üzerinde ne olduğunu görmek istersin. Bunu yapan araçlar **paket yakalayıcılardır**: `tcpdump` (komut satırı) ve Wireshark (grafiksel). Bu araçlar ağ arayüzünden kopyalanan çerçeveleri okur ve alanlarını ayrıştırıp gösterir. Linux'ta bu iş `AF_PACKET` soketi ve libpcap kütüphanesi üzerinden yapılır; Windows'ta Npcap sürücüsü kullanılır (genel bilgi). Her iki durumda da yakalama **root yetkisi** gerektirir; çünkü başka bir sürecin trafiğini görmek bir güvenlik konusudur.

Bu WSL ortamında root yoktu ve `tcpdump` kurulu değildi. Bu yüzden gerçek bir yakalama yapamadık; bunun yerine iki şeyi yaptık. Birincisi, bilinen bir çerçeveyi (bölüm başındaki SYN) elle üreten ve baytlarını `struct` ile ayrıştıran bir program yazdık. İkincisi, bu ayrıştırıcının IPv4 sağlama toplamını bağımsız bir kaynakla (Wikipedia örneği, 29.5) doğruladık. TCP sağlama toplamı için bağımsız bir kütüphane (scapy gibi) bu ortamda yoktu; onu yalnızca iç tutarlılıkla denetledik: alıcı tarafındaki kuralla, sahte başlık ve segmentin toplamı `0` (tümleyeni) vermeli. Bu tür bir kontrol, yanlış hesaplanmış bir sağlamayı yakalar ama iki tarafta da aynı yanlış varsayım varsa bunu yakalayamaz; dürüstçe söylemek gerekirse bu, eksik bir doğrulamadır.

Ayrıştırıcı, bir çerçeveyi üç katman boyunca çözer. Çerçeve üreten kısım da aynı dosyadadır, çünkü ayrıştırmayı test edecek bir girdiye ihtiyacımız vardı:


```python
# -*- coding: utf-8 -*-
# paket_coz.py - Ethernet + IPv4 + TCP/UDP çerçevesini elle üretir ve
# baytlarını struct ile çözer. Sağlama toplamlarını doğrular.
import struct

# ---------- yardımcılar ----------
def saglama(bayt):
    if len(bayt) % 2:
        bayt += b"\x00"
    toplam = sum((bayt[i] << 8) | bayt[i + 1]
                 for i in range(0, len(bayt), 2))
    while toplam >> 16:
        toplam = (toplam & 0xFFFF) + (toplam >> 16)
    return (~toplam) & 0xFFFF


def ip_bayt(metin):
    return bytes(int(x) for x in metin.split("."))


def mac_bayt(metin):
    return bytes(int(x, 16) for x in metin.split(":"))


def mac_metin(b):
    return ":".join("%02x" % x for x in b)


def ip_metin(b):
    return ".".join(str(x) for x in b)


BAYRAKLAR = [(0x01, "FIN"), (0x02, "SYN"), (0x04, "RST"),
             (0x08, "PSH"), (0x10, "ACK"), (0x20, "URG")]


def bayrak_metni(f):
    return "|".join(ad for bit, ad in BAYRAKLAR if f & bit) or "-"
```



```python
# ---------- çerçeve üretimi ----------
def tcp_bolumu(kaynak_ip, hedef_ip, sport, dport, seq, ack, bayrak,
               pencere, secenekler=b"", veri=b""):
    ofset = (20 + len(secenekler)) // 4
    ust = struct.pack("!HHIIBBHHH", sport, dport, seq, ack,
                      ofset << 4, bayrak, pencere, 0, 0)
    ust += secenekler + veri
    sahte = (ip_bayt(kaynak_ip) + ip_bayt(hedef_ip) +
             struct.pack("!BBH", 0, 6, len(ust)))
    cs = saglama(sahte + ust)
    return ust[:16] + struct.pack("!H", cs) + ust[18:]


def udp_bolumu(kaynak_ip, hedef_ip, sport, dport, veri):
    uzunluk = 8 + len(veri)
    ust = struct.pack("!HHHH", sport, dport, uzunluk, 0) + veri
    sahte = (ip_bayt(kaynak_ip) + ip_bayt(hedef_ip) +
             struct.pack("!BBH", 0, 17, uzunluk))
    cs = saglama(sahte + ust) or 0xFFFF   # 0 "sağlama yok" demektir
    return ust[:6] + struct.pack("!H", cs) + ust[8:]


def ipv4_paketi(kaynak_ip, hedef_ip, protokol, yuk,
                ttl=64, kimlik=0x1C46):
    toplam = 20 + len(yuk)
    baslik = struct.pack("!BBHHHBBH4s4s", 0x45, 0, toplam, kimlik,
                         0x4000, ttl, protokol, 0,
                         ip_bayt(kaynak_ip), ip_bayt(hedef_ip))
    cs = saglama(baslik)
    baslik = baslik[:10] + struct.pack("!H", cs) + baslik[12:]
    return baslik + yuk
```



```python


def ethernet_cercevesi(hedef_mac, kaynak_mac, ethertype, yuk):
    return mac_bayt(hedef_mac) + mac_bayt(kaynak_mac) + \
        struct.pack("!H", ethertype) + yuk


# ---------- çözümleme ----------
def coz_ethernet(c):
    hedef, kaynak, tip = struct.unpack("!6s6sH", c[:14])
    return {"hedef": mac_metin(hedef), "kaynak": mac_metin(kaynak),
            "tip": tip}, c[14:]


def coz_ipv4(p):
    surum_ihl = p[0]
    surum, ihl = surum_ihl >> 4, surum_ihl & 0x0F
    baslik_bayt = ihl * 4
    (_, dscp, toplam, kimlik, bayrak_ofset, ttl, proto, cs,
     kaynak, hedef) = struct.unpack("!BBHHHBBH4s4s", p[:20])
    dogrulama = saglama(p[:baslik_bayt])     # alan doğru ise 0 döner
    return {"surum": surum, "ihl": ihl, "baslik_bayt": baslik_bayt,
            "toplam": toplam, "kimlik": kimlik,
            "df": (bayrak_ofset >> 14) & 1, "ttl": ttl,
            "proto": proto,
            "sag_cs": cs, "sag_ok": dogrulama == 0,
            "kaynak": ip_metin(kaynak), "hedef": ip_metin(hedef)}, \
```



```python
        p[baslik_bayt:toplam]


def coz_tcp(seg, kaynak_ip, hedef_ip):
    (sport, dport, seq, ack, ofset_rez, bayrak, pencere, cs, acil) = \
        struct.unpack("!HHIIBBHHH", seg[:20])
    ofset = (ofset_rez >> 4) * 4
    sahte = (ip_bayt(kaynak_ip) + ip_bayt(hedef_ip) +
             struct.pack("!BBH", 0, 6, len(seg)))
    return {"sport": sport, "dport": dport, "seq": seq, "ack": ack,
            "ofset": ofset, "bayrak": bayrak_metni(bayrak),
            "pencere": pencere, "sag_cs": cs,
            "sag_ok": saglama(sahte + seg) == 0,
            "secenek": seg[20:ofset]}, seg[ofset:]


def coz_udp(seg, kaynak_ip, hedef_ip):
    sport, dport, uzunluk, cs = struct.unpack("!HHHH", seg[:8])
    sahte = (ip_bayt(kaynak_ip) + ip_bayt(hedef_ip) +
             struct.pack("!BBH", 0, 17, uzunluk))
    ok = (cs == 0) or (saglama(sahte + seg[:uzunluk]) == 0)
    return {"sport": sport, "dport": dport, "uzunluk": uzunluk,
```


Çözücü, her katmanı sırayla açar. Önce Ethernet'i, sonra EtherType'a bakarak IPv4'ü, sonra protokol alanına bakarak TCP ya da UDP'yi çözer:


```python
            "sag_cs": cs, "sag_ok": ok}, seg[8:uzunluk]


def coz(cerceve):
    eth, yuk = coz_ethernet(cerceve)
    print("Ethernet  hedef=%s kaynak=%s tip=0x%04x" % (
        eth["hedef"], eth["kaynak"], eth["tip"]))
    if eth["tip"] != 0x0800:
        print("  IPv4 değil; çözme durdu.")
        return
    ip, yuk = coz_ipv4(yuk)
    print("IPv4      %s -> %s  ver=%d IHL=%d "
          "(%d bayt) toplam=%d TTL=%d"
          % (ip["kaynak"], ip["hedef"], ip["surum"], ip["ihl"],
             ip["baslik_bayt"], ip["toplam"], ip["ttl"]))
    print("          proto=%d (%s) kimlik=0x%04x DF=%d "
          "sağlama=0x%04x %s"
          % (ip["proto"], {6: "TCP", 17: "UDP"}.get(ip["proto"], "?"),
             ip["kimlik"], ip["df"], ip["sag_cs"],
             "GEÇERLİ" if ip["sag_ok"] else "BOZUK"))
    if ip["proto"] == 6:
        t, veri = coz_tcp(yuk, ip["kaynak"], ip["hedef"])
        print("TCP       %d -> %d seq=%d ack=%d "
              "ofset=%d bayt bayrak=%s"
              % (t["sport"], t["dport"], t["seq"], t["ack"],
                 t["ofset"], t["bayrak"]))
        print("          pencere=%d sağlama=0x%04x %s seçenek=%s"
              % (t["pencere"], t["sag_cs"],
                 "GEÇERLİ" if t["sag_ok"] else "BOZUK",
                 t["secenek"].hex(" ") or "yok"))
        print("          veri=%d bayt" % len(veri))
    elif ip["proto"] == 17:
        u, veri = coz_udp(yuk, ip["kaynak"], ip["hedef"])
```


Son bölüm, üç örneği çalıştırır: bir SYN çerçevesi, bir UDP telemetri çerçevesi ve bir bit bozulmuş SYN.


```python
        print("UDP       %d -> %d uzunluk=%d sağlama=0x%04x %s"
              % (u["sport"], u["dport"], u["uzunluk"], u["sag_cs"],
                 "GEÇERLİ" if u["sag_ok"] else "BOZUK"))
        print("          veri=%d bayt: %s"
              % (len(veri), veri.hex(" ")))


if __name__ == "__main__":
    # 1. SYN: 10.0.0.5:51514 -> 10.0.0.9:80, MSS=1460 seçenekli
    secenek_mss = bytes([2, 4, 0x05, 0xB4])
    tcp = tcp_bolumu("10.0.0.5", "10.0.0.9", 51514, 80, 1000, 0, 0x02,
                     64240, secenekler=secenek_mss)
    ip = ipv4_paketi("10.0.0.5", "10.0.0.9", 6, tcp)
    syn = ethernet_cercevesi("02:00:00:00:00:09", "02:00:00:00:00:05",
                             0x0800, ip)
    print("== SYN çerçevesi (%d bayt) ==" % len(syn))
    for i in range(0, len(syn), 16):
        print("%04x  %s" % (i, syn[i:i + 16].hex(" ")))
    coz(syn)

    print()
    # 2. Telemetri: UDP 14550, 8 baytlık yük (genel bilgi: MAVLink'in
    # varsayılan GCS UDP portu 14550'dir; bu sadece örnek yüktür).
    udp = udp_bolumu("10.0.0.20", "10.0.0.1", 14550, 14550,
                     bytes(range(8)))
    ip2 = ipv4_paketi("10.0.0.20", "10.0.0.1", 17, udp, ttl=32)
    cerc2 = ethernet_cercevesi("02:00:00:00:00:01",
                               "02:00:00:00:00:20",
                               0x0800, ip2)
    print("== UDP çerçevesi (%d bayt) ==" % len(cerc2))
    coz(cerc2)

    print()
    # 3. Bit bozulması: hedef port 80 -> 81 (1 bit: 0x50 -> 0x51)
    bozuk = bytearray(syn)
    bozuk[14 + 20 + 3] ^= 0x01
    print("== Bozuk çerçeve (hedef port 1 bit değişti) ==")
    coz(bytes(bozuk))
```


Çıktı:


```term
$ python3 paket_coz.py
== SYN çerçevesi (58 bayt) ==
0000  02 00 00 00 00 09 02 00 00 00 00 05 08 00 45 00
0010  00 2c 1c 46 40 00 40 06 0a 79 0a 00 00 05 0a 00
0020  00 09 c9 3a 00 50 00 00 03 e8 00 00 00 00 60 02
0030  fa f0 bb b5 00 00 02 04 05 b4
Ethernet  hedef=02:00:00:00:00:09 kaynak=02:00:00:00:00:05 tip=0x0800
IPv4      10.0.0.5 -> 10.0.0.9  ver=4 IHL=5 (20 bayt) toplam=44 TTL=64
          proto=6 (TCP) kimlik=0x1c46 DF=1 sağlama=0x0a79 GEÇERLİ
TCP       51514 -> 80 seq=1000 ack=0 ofset=24 bayt bayrak=SYN
          pencere=64240 sağlama=0xbbb5 GEÇERLİ seçenek=02 04 05 b4
          veri=0 bayt

== UDP çerçevesi (50 bayt) ==
Ethernet  hedef=02:00:00:00:00:01 kaynak=02:00:00:00:00:20 tip=0x0800
IPv4      10.0.0.20 -> 10.0.0.1  ver=4 IHL=5 (20 bayt) toplam=36 TTL=32
          proto=17 (UDP) kimlik=0x1c46 DF=1 sağlama=0x2a6f GEÇERLİ
UDP       14550 -> 14550 uzunluk=16 sağlama=0x6dfd GEÇERLİ
          veri=8 bayt: 00 01 02 03 04 05 06 07

== Bozuk çerçeve (hedef port 1 bit değişti) ==
Ethernet  hedef=02:00:00:00:00:09 kaynak=02:00:00:00:00:05 tip=0x0800
IPv4      10.0.0.5 -> 10.0.0.9  ver=4 IHL=5 (20 bayt) toplam=44 TTL=64
          proto=6 (TCP) kimlik=0x1c46 DF=1 sağlama=0x0a79 GEÇERLİ
TCP       51514 -> 81 seq=1000 ack=0 ofset=24 bayt bayrak=SYN
          pencere=64240 sağlama=0xbbb5 BOZUK seçenek=02 04 05 b4
          veri=0 bayt
```


Bu çıktıda üç şeyi kontrol et. Birincisi, IPv4 sağlaması her iki çerçevede de `GEÇERLİ`dir; yani başlık alanlarını doğru yerleştirdik. İkincisi, bozulmuş çerçevede yalnızca hedef port değişti (80 → 81) ve TCP sağlaması hemen `BOZUK` olarak işaretlendi: bir bitlik değişiklik bile yakalanır. Üçüncüsü, IPv4 sağlaması değişmedi, çünkü o bit IP başlığında değil TCP başlığındaydı; bu, sağlama alanlarının neyi koruduğunu gösterir. UDP örneğinde 14550 numaralı port kullanılmıştır: bu, MAVLink'in varsayılan yer istasyonu UDP portudur (genel bilgi); yük olarak yalnızca 0–7 baytları konulmuştur, gerçek bir MAVLink mesajı değildir.

## 29.16 Gerçek dünya: savunma ağları, otomotiv ve sensör ağları

Bu bölümde anlatılan katmanların hepsi, savunma sanayiinde ve gömülü sistemlerde farklı kısıtlarla karşımıza çıkar. Bu kısıtlar, genel internet tasarımından nasıl ayrıldıklarını gösterir.

**Taktik veri bağları.** Sahadaki birlikler ve araçlar arasında kurulan veri bağları, kablosuz ve çoğu zaman düşük bant genişliklidir. Bağlantı kesilmeleri, uzun gecikmeler ve yayın yapma ihtiyacı yaygındır. Bu ortamlarda standart TCP'nin tıkanıklık varsayımları ve uzun el sıkışmaları verimsiz olabilir; bu yüzden sistemler çoğu zaman kendi güvenilirlik katmanlarını UDP üzerine kurar ya da özel taşıma protokolleri kullanır (genel bilgi; belirli sistemlerin tasarımına girmiyoruz). Güvenlik boyutu (şifreleme ve kimlik doğrulama) Bölüm 32'nin konusudur.

**İHA telemetrisi.** Bir İHA'dan yer istasyonuna giden telemetri, bu bölümün UDP tartışmasının tipik örneğidir: sık, küçük, gecikmeye duyarlı ve eski veri değersiz. Komut kanalı ise tersine, her komutun ulaşması gereken bir kanaldır; burada kayıp kabul edilemez ve onay mekanizması gerekir. Bu iki kanalı aynı protokolle taşımak mümkündür ama iki farklı güvenilirlik politikası seçmek çoğu zaman daha doğrudur.

**Otomotiv ve gömülü ağlar.** Araçların içindeki ağlar, IP tabanlı değil, çoğunlukla CAN gibi veri yollarıdır. CAN'de düğümler bir ağ adresi ile değil, mesaj kimliği (ID) ile konuşur ve tüm düğümler aynı kablonun trafiğini dinler; yani IP'deki gibi bir yönlendirme katmanı yoktur (genel bilgi). Bu fark, Bölüm 45'te UART, SPI ve I2C ile birlikte seri veri yollarını anlatırken yeniden karşına çıkacak. Bölüm 1.5'te gördüğün ağ bayt sırası sözleşmesi de burada geçerlidir: STM32 kartından gelen bir veri paketini yorumlarken alanların sırası ve hizası bir sözleşmedir.

**Sensör ağları.** Pil ile çalışan ve yüzlerce düğümlü sensör ağlarında her düğüm IPv4 yığınını tam olarak çalıştırmayabilir. Düşük güç ve küçük paketler için sıkıştırılmış IPv6 kullanımları (örneğin 6LoWPAN, genel bilgi) ve çoklu atlamalı yönlendirme kullanılır. Yönlendirme tablosu yerine düğümler kendi komşularını ve en iyi yolu keşfeder. Bu ağlarda bu bölümde gördüğün her kavram (kapsülleme, MTU, LPM ve güvenilirlik) yine geçerlidir, yalnızca uygulanma biçimi değişir.

Son olarak EV Dashboard projene bağlanalım: STM32'den gelen sensör verisi genellikle UART üzerinden tek tek bayt olarak gelir. Bu, TCP veya UDP katmanına hiç girmeyen bir veri akışıdır; ama bayt sırası, çerçeve sınırı ve sağlama fikirleri burada da aynıdır. Yani bu bölümde öğrendiğin şey, sadece internete özgü bir konu değildir: veriyi güvenilir biçimde bir uçtan diğerine taşımanın genel ilkeleridir.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, Bölüm 5'teki altı adımı izler. Her birinde elle iz sürme tablosu vardır; kendi cevabını bu tabloyla karşılaştır. Zorluk sırası ★, ★★, ★★, ★★★ şeklindedir.

### Örnek 1 (★): 172.21.200.9/20 ağının sınırları

**Problem.** `172.21.200.9/20` adresi için ağ adresini, yayın adresini, ilk ve son kullanılabilir hostu ve host sayısını bul.

**Adım 1 — Anla.** Verilen bir IPv4 adresi ve bir CIDR öneki var. Önek 20 olduğu için ilk 20 bit ağ, kalan 12 bit host kısmıdır. İstenen dört değer, bu iki parçanın sınırlarıdır.

**Adım 2 — Örnekle.** Daha küçük bir benzer durumu düşünelim: `10.0.0.5/30`. Önek 30 olduğu için 2 host biti vardır, yani 4 adres: ağ `10.0.0.4`, yayın `10.0.0.7`, kullanılabilir `10.0.0.5` ve `10.0.0.6`. Bu küçük örnekte tek bir bloğun ağ adresinin, adresi host bitleri sıfırlanarak bulunduğunu görürüz.

**Adım 3 — Kaba çöz.** Her adresi 32 bit olarak yazıp maskeyle AND'lemek olur. Ama 12 host bitinin hepsini tek tek düşünmeye gerek yok: maske 20 bitse, 3. oktetin ilk 4 biti ağ, son 4 biti host, 4. oktetin tamamı host'tur.

**Adım 4 — Örüntü.** 3. oktet 200'dür. Ağ kısmı ilk 4 bit (`1100`), host kısmı son 4 bit (`1000`). Blok büyüklüğü 2^4 = 16'dır; 200'ü içeren 16'lık blok 192'den başlar (`200 − (200 mod 16) = 192`). Ağ adresi `172.21.192.0`, yayın adresi bu bloğun son adresi olur: 3. oktet `192 + 15 = 207`, 4. oktet `255`.

**Adım 5 — İyileştir.** Formüller artık kesindir: ağ = IP AND maske; yayın = ağ + (2^12 − 1); ilk host = ağ + 1; son host = yayın − 1; host sayısı = 2^12 − 2 = 4094. Hesabı tek satırlık bir bit işlemine indirdik.

**Adım 6 — Doğrula.** Elle iz tablosu:

| Adım | İşlem | 3. oktet (ikilik) | 4. oktet (ikilik) |
|---|---|---|---|
| 1 | IP | 200 = 11001000 | 9 = 00001001 |
| 2 | Maske /20 | 240 = 11110000 | 0 = 00000000 |
| 3 | IP AND maske = ağ | 11000000 = 192 | 00000000 = 0 |
| 4 | Ağ OR (NOT maske) = yayın | 192 OR 00001111 = 207 | 0 OR 11111111 = 255 |
| 5 | İlk host | 192 | 1 |
| 6 | Son host | 207 | 254 |

Python'un `ipaddress` ile yaptığı hesap aynı sonucu verir. Program çıktısındaki ilgili satırlar:


```term
172.21.200.9/20  [UYUMLU]
  ağ=172.21.192.0  yayın=172.21.207.255  maske=255.255.240.0
  ilk=172.21.192.1  son=172.21.207.254  host=4094
```


**Bunu AI'sız yazabilir misin?** `172.21.200.9/21` için aynı altı adımı izle. Bu kez maske 21 bit olduğunda blok büyüklüğü kaç olur ve 3. oktetin ağ kısmı nasıl değişir? Tabloyu kendi kağıdında kur, sonra ayrıca kodla karşılaştır.

### Örnek 2 (★★): Yönlendirme kararı, üç hedef

**Problem.** 29.7'deki `TABLO` içinde `0.0.0.0/0`, `10.0.0.0/8`, `10.1.0.0/16`, `10.1.2.0/24` ve `10.1.2.128/25` önekleri vardır (`172.21.192.0/20` satırı bu hedefler için ilgisizdir). `10.1.2.5`, `10.9.9.9` ve `8.8.8.8` hedeflerinin hangi satıra gideceğini belirle.

**Adım 1 — Anla.** Her hedef için, hangi önekin o hedefi kapsadığını bulmamız gerekiyor. Birden çok önek kapsıyorsa en uzunu kazanır (LPM). Her önek ile hedef arasında yalnızca önek uzunluğu kadar bitin eşleşmesi gerekir.

**Adım 2 — Örnekle.** `10.1.2.5` hedefini ele alalım. `10.1.2.128/25` önekinin kapsadığı aralık `10.1.2.128`–`10.1.2.255`tir; `10.1.2.5` bu aralığın dışındadır. Ama `10.1.2.0/24` aralığı `10.1.2.0`–`10.1.2.255` olduğundan `10.1.2.5` içindedir. Yani en uzun eşleşme `/24`tür.

**Adım 3 — Kaba çöz.** Her hedef için her önekin kapsama testini yap. Kapsama testi, `hedef AND maske = ağ` eşitliğidir.

**Adım 4 — Örüntü.** Hedefi kapsayan önekler her zaman bir zincir oluşturur: `/0` hepsini kapsar, `/8` daha dar, ... Zincirde en uzun olan karar verir. Hedef bu zincirin dışında kalırsa yalnızca `/0` kalır; yani varsayılan yol.

**Adım 5 — İyileştir.** Tablo büyüdüğünde her satırı taramak yerine trie'da 32 adımda aynı kararı verebilirsin (29.7'de yazdığımız YonlendirmeTrie). Kararın iyileştirmesi, tablo boyutundan bağımsız arama süresidir.

**Adım 6 — Doğrula.** Elle iz tablosu:

| Hedef | Kapsayan önekler | En uzun | Karar |
|---|---|---|---|
| 10.1.2.5 | /0, /8, /16, /24 (/25 değil) | /24 | ofis-lan |
| 10.9.9.9 | /0, /8 (/16 değil: 10.9 ≠ 10.1) | /8 | vpn0 |
| 8.8.8.8 | /0 | /0 | eth0 üzerinden 172.21.192.1 |

Program çıktısındaki karşılık gelen satırlar (aynı tablonun bu üç hedefi ve iki ek hedefi):


```term
10.1.2.130       -> sensor-ag
10.1.2.5         -> ofis-lan
10.1.9.9         -> vpn1
10.9.9.9         -> vpn0
172.21.205.116   -> eth0 (doğrudan bağlı)
8.8.8.8          -> eth0 üzerinden 172.21.192.1 (varsayılan)
```


**Bunu AI'sız yazabilir misin?** Tabloya `10.1.2.200/29` satırını eklersen `10.1.2.130` hangi satıra gider? Bir de `10.1.2.130`'a `10.1.2.128/26` satırı eklersen ne değişir? Cevabını elle yaz; sonra trie'ya ekleyip doğrula.

### Örnek 3 (★★): Hex dökümünden bir SYN çerçevesini çözmek

**Problem.** Bölüm başındaki SYN çerçevesinin 58 baytlık hex dökümünü elle ayrıştır: kaynak ve hedef MAC, IP adresleri, port numaraları, sıra numarası, bayraklar ve MSS seçeneği.

**Adım 1 — Anla.** Çerçeve üç katmandan oluşur: 14 bayt Ethernet, 20 bayt IPv4 ve TCP başlığı. Her alanın hangi bayt aralığında olduğunu bilmeden çözemeyiz. Bu yüzden önce "hangi katman nerede başlar" sorusunu cevaplamalıyız.

**Adım 2 — Örnekle.** Yalnızca ilk iki baytı ele alalım: `02 00`. Hedef MAC'in ilk baytı `02`dir; bu, bu adresin yerel yönetimli olduğunu gösterir (ikinci en düşük bit 1). Bu tek başına çerçevenin ne olduğunu söylemez; ama ileride EtherType ve IHL alanlarını okumaya hazırlar.

**Adım 3 — Kaba çöz.** Baytları sırayla oku ve her birini bir alana eşle. Alan uzunluklarını başlıklardan biliyoruz: Ethernet 6+6+2, IPv4 başlığı IHL × 4 bayt, TCP başlığı ofset × 4 bayt.

**Adım 4 — Örüntü.** Üç kritik işaret vardır. EtherType `08 00` ise sonraki katman IPv4'tür. IHL `5` ise IP başlığı 20 bayttır. TCP ofset `6` ise TCP başlığı 24 bayttır ve fazladan 4 baytlık bir seçenek vardır. Bu seçeneğin tipi (2) MSS'dir ve değeri `05 b4` = 1460.

**Adım 5 — İyileştir.** Doğrulamayı bir kontrole indirgeyelim: toplam çerçeve uzunluğu 14 + 20 + 24 = 58 olmalı; IPv4 toplam uzunluğu `00 2c` = 44 olmalı, yani 20 (IP) + 24 (TCP) = 44. İki eşitlik de sağlanıyorsa uzunluk alanları tutarlıdır.

**Adım 6 — Doğrula.** Elle iz tablosu (ofset, bayt, alan, değer):

| Ofset | Bayt | Alan | Değer |
|---|---|---|---|
| 0–5 | 02 00 00 00 00 09 | Hedef MAC | 02:00:00:00:00:09 |
| 6–11 | 02 00 00 00 00 05 | Kaynak MAC | 02:00:00:00:00:05 |
| 12–13 | 08 00 | EtherType | 0x0800 (IPv4) |
| 14 | 45 | Sürüm, IHL | 4, 5 (20 bayt) |
| 16–17 | 00 2c | Toplam uzunluk | 44 |
| 20–21 | 40 00 | Bayraklar | DF = 1 |
| 22 | 40 | TTL | 64 |
| 23 | 06 | Protokol | 6 (TCP) |
| 24–25 | 0a 79 | IPv4 sağlama | 0x0a79 |
| 26–29 | 0a 00 00 05 | Kaynak IP | 10.0.0.5 |
| 30–33 | 0a 00 00 09 | Hedef IP | 10.0.0.9 |
| 34–35 | c9 3a | Kaynak port | 51514 |
| 36–37 | 00 50 | Hedef port | 80 |
| 38–41 | 00 00 03 e8 | Sıra numarası | 1000 |
| 46 | 60 | Ofset | 6 (24 bayt) |
| 47 | 02 | Bayraklar | SYN |
| 48–49 | fa f0 | Pencere | 64240 |
| 54–57 | 02 04 05 b4 | MSS seçeneği | 1460 |

Python çözücüsünün çıktısıyla karşılaştır: aynı değerleri (toplam = 44, ofset = 24, pencere = 64240, seçenek = `02 04 05 b4`) üretmesi gerekir.


```term
Ethernet  hedef=02:00:00:00:00:09 kaynak=02:00:00:00:00:05 tip=0x0800
IPv4      10.0.0.5 -> 10.0.0.9  ver=4 IHL=5 (20 bayt) toplam=44 TTL=64
          proto=6 (TCP) kimlik=0x1c46 DF=1 sağlama=0x0a79 GEÇERLİ
TCP       51514 -> 80 seq=1000 ack=0 ofset=24 bayt bayrak=SYN
          pencere=64240 sağlama=0xbbb5 GEÇERLİ seçenek=02 04 05 b4
          veri=0 bayt
```


**Bunu AI'sız yazabilir misin?** Aynı çerçevede bayrak baytı `02` yerine `12` olsaydı (SYN+ACK), hangi alan değişirdi ve bu çerçeve hangi bağlantı adımına ait olurdu? Ayrıca 38–41 baytlarındaki sıra numarasını `00 00 03 e8` yerine `00 00 27 10` yapsaydın değeri kaç olurdu?

### Örnek 4 (★★★): Bir kaybın sıra ve onay numaralarında izi

**Problem.** Bir istemci sunucuya üç segment gönderir ve ortadaki segment kaybolur. Her segmentin sıra numarasını, her onayın değerini ve sunucunun beklediği bayt numarasını izle. İstemcinin ISN'i 1000, sunucunun ISN'i 5000. İstemci beş segment gönderiyor: A (1001–1100), B (1101–1200), C (1201–1300), D (1301–1400), E (1401–1500). B kayboluyor.

**Adım 1 — Anla.** Bu soruda üç sayıyı izliyoruz: segmentin **sıra numarası** (ilk baytı), onay numarası (**sonraki beklenen bayt**) ve sunucunun iç durumu `rcv_nxt` (sonraki beklenen bayt). Kayıp B'de olduğu için sunucu C, D ve E'yi alır ama onları sıraya koyamaz; onay hep 1101'de kalır.

**Adım 2 — Örnekle.** Önce bir kolay durum: A tek başına gitseydi, sunucu A'yı alır, `rcv_nxt` 1001'den 1101'e çıkar ve `ACK 1101` döner. Bu durum, onay numarasının "alınan son bayt + 1" olduğunu gösterir.

**Adım 3 — Kaba çöz.** Her segment için iki soru sor: sunucunun beklediği bayt bu mu? Değilse onay hangi değerde kalır?

**Adım 4 — Örüntü.** Sunucu bir boşluk görünce, beklediği baytı (1101) tekrar tekrar onaylar. Bu tekrarlanan ACK'lardır. Üç tekrarlanan ACK görülünce gönderici B'yi yeniden iletir (hızlı yeniden iletim). B geldiğinde sunucunun tampondaki C, D ve E ile birleşip tek bir büyük onay üretir.

**Adım 5 — İyileştir.** Onay numarasına bakarak "kaç bayt tamam" hesabını tek satırda yapabilirsin: `ack − ilk_bayt = 1501 − 1001 = 500`. Bu, beş segmentin toplam verisidir (5 × 100). Hesap, kaybı ve yeniden iletimi de hesaba katar: onay 1501 olduğunda kayıp zaten kapanmıştır.

**Adım 6 — Doğrula.** Elle iz tablosu:

| Adım | Yön | Olay | seq | uzunluk | ack | Sunucunun rcv_nxt |
|---|---|---|---|---|---|---|
| 1 | İ → S | SYN | 1000 | 0 (1 sıra) | — | — |
| 2 | S → İ | SYN+ACK | 5000 | 0 (1 sıra) | 1001 | 1001 |
| 3 | İ → S | ACK | 1001 | 0 | 5001 | 1001 |
| 4 | İ → S | A | 1001 | 100 | 5001 | 1101 (ACK 1101) |
| 5 | İ → S | B: KAYBOLDU | 1101 | 100 | — | 1101 |
| 6 | İ → S | C: tampona alındı | 1201 | 100 | — | 1101 (dup ACK 1) |
| 7 | İ → S | D: tampona alındı | 1301 | 100 | — | 1101 (dup ACK 2) |
| 8 | İ → S | E: tampona alındı | 1401 | 100 | — | 1101 (dup ACK 3) |
| 9 | İ | 3 tekrarlanan ACK, B yeniden iletilir | 1101 | 100 | — | 1101 |
| 10 | İ → S | B (yeniden) | 1101 | 100 | — | 1501 (ACK 1501) |

Adım 6'daki doğrulama, her segmentin sıra numarasının bir öncekinin sonuna eşit olduğunu gösterir: 1001 + 100 = 1101, 1101 + 100 = 1201, 1201 + 100 = 1301, 1301 + 100 = 1401. Son onay 1501, `1501 − 1001 = 500` verir. Üç tekrarlanan ACK ve yeniden iletim, tablonun 6–9. adımlarındadır.

**Bunu AI'sız yazabilir misin?** Bu kez B yerine C kaybolsaydı, sunucu hangi onayları üretirdi, kaç tekrarlanan ACK gelirdi ve yeniden iletim hangi sıra numarasıyla yapılırdı? Tabloyu yeniden çiz ve sonucu kendi cevabınla karşılaştır. Son olarak, B'nin yeniden iletimi de kaybolsaydı zamanlayıcı (RTO) hangi rolü üstlenirdi?

## Kendin Yap Projeleri

::: dikkat
Bu iki projeyi yazarken AI aracı kullanma. Önce kâğıda ne yapacağını çiz: hangi bayt nerede başlıyor, hangi fonksiyon ne döndürüyor. Kod yazarken takıldığında sorunu önce kendi çizimine göre düşün; çıktı yanlış görünüyorsa önce hangi alanı yanlış yerden okuduğunu kontrol et. Bu, ağ ayrıştırıcısı yazmanın en değerli kısmıdır.
:::

### Proje 1 (★★): Mini pcap okuyucu

**Amaç.** pcap dosyasını okuyup her çerçeve için Ethernet, IPv4 ve TCP ya da UDP özetini satır satır yazan bir araç yazmak. Bu, Wireshark'ın ilk özet satırının kendi sürümüdür.

**Beklenen davranış.** Program bir pcap dosyasının yolunu alır. Her paket için sıra numarası, zaman damgası, kaynak ve hedef IP, protokol, port ve (TCP ise) bayrakları yazar. Sağlaması bozuk paketi `BOZUK` diye işaretler. Ethernet dışında bir bağlantı türü görürse ya da IPv4 olmayan bir EtherType gelirse o paketi atlar ve devam eder.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** pcap biçimi libpcap'in dosya biçimidir (genel bilgi). Dosya 24 baytlık bir genel başlıkla açılır: sihirli sayı (`0xa1b2c3d4`), sürüm (2 ve 4), zaman dilimi, zaman hassasiyeti, snaplen ve bağlantı türü (1, Ethernet). Ardından her paket 16 baytlık bir başlıkla gelir: saniye, mikrosaniye, kaydedilen uzunluk (`incl_len`) ve gerçek uzunluk. Sihirli sayı ters okunuyorsa dosya ters bayt sırasıyla yazılmıştır; bu durumda `<` yerine `>` kullanman gerekir. Bu fikri Bölüm 1.5'teki endianness bilgisiyle düşün.

Test dosyasını kendin üret: `paket_coz.py`deki çerçeve üreticilerini kullanarak birkaç çerçeveyi bir pcap dosyasına yaz. Gerçek bir yakalama olmadan test etmenin en güvenilir yolu budur.

**Başarı kriterleri.**

1. Üç çerçeveli bir pcap (SYN, UDP ve bozuk bir SYN) doğru özetlenir; her satırda kaynak ve hedef IP, protokol ve port bulunur.
2. Tek bitlik bir değişiklik `BOZUK` olarak işaretlenir.
3. IPv6 (`0x86DD`) gibi bilinmeyen bir EtherType program çökmeden atlanır.
4. Dosya sonunda yarım kalmış bir paket (`incl_len` kalan baytlardan büyükse) hata vermeden okumayı durdurur.

### Proje 2 (★★★): VLSM planlayıcı

**Amaç.** Tek bir ana ağı, farklı büyüklükte alt ağlara israfsız ve çakışmadan bölen bir araç yazmak. Bu, değişken uzunluklu alt ağ maskesi (VLSM) yöntemidir.

**Beklenen davranış.** Girdi bir ana ağ (örneğin `192.168.20.0/24`) ve istenen host sayılarının listesidir (örneğin 100, 50, 20, 10, 2, 2). Çıktı, her ihtiyaç için ağ adresini, maskeyi, ilk ve son hostu, yayın adresini gösterir; ayrıca kalan boş adres sayısını verir. Ayırma en büyük ihtiyaçtan başlar.

**Önerilen yaklaşım (ipucu).** Her ihtiyaç için host sayısına iki ek adres (ağ ve yayın) eklenir; bu toplamı karşılayan en küçük 2'nin kuvvetini bul. Bu kuvvet host bitlerinin sayısını verir; maske 32 eksi bu sayıdır. İhtiyaçları büyükten küçüğe sırala ve bir imleçle yerleştir. Her blok kendi büyüklüğünün katına hizalanmalıdır; imleç bu kurala uymuyorsa önce ilerlet. Sonucu Python'un `ipaddress` modülündeki `overlaps` ile çakışma için sına.

**Başarı kriterleri.**

1. Örnek girdide hiçbir iki alt ağ çakışmaz ve hepsi ana ağın içindedir.
2. Her blok ihtiyacı karşılar, ama gereğinden büyük bir blok ayrılmaz.
3. Kullanılan ve kalan adres sayıları toplamı 256 (ya da ana ağın boyutu) eder.
4. Ana ağ yetersizse program açıklayıcı bir hata verir.

## Ek Alıştırmalar

Aşağıdaki sorular kademelidir. Mülakat işaretli olanlar, mülakatta gerçekten sorulabilecek türdendir. Cevaplarını önce kendin yaz.

1. (★) `10.20.30.40/13` için ağ adresi, yayın adresi ve host sayısı nedir? Önce elle, sonra `ipaddress` ile doğrula.
2. (★) `192.168.1.1/31` ile `192.168.1.1/32` arasındaki fark nedir? Hangi durumda `/31` tercih edilir?
3. (★★) Bir `/24` ağı 8 eşit alt ağa bölünürse her birinin maskesi, ağ adresleri ve host sayısı nedir?
4. (★★) (Mülakat) Bir ana bilgisayar, hedef IP'nin aynı alt ağda olup olmadığını nasıl anlar? Bu karar hangi bilgiye dayanır?
5. (★★) Yönlendirme tablosuna `10.0.0.0/8 → A`, `10.0.0.0/16 → B` ve `0.0.0.0/0 → C` satırları eklendi. `10.0.200.1` ve `10.1.0.1` hangi satıra gider? Nedenini açıkla.
6. (★★) (Mülakat) Yönlendirmede neden en kısa önek değil, en uzun önek eşleşmesi seçilir? Bunun bir sonucu olarak, varsayılan yol (`/0`) neden her zaman en son başvurulan yoldur?
7. (★★) (Mülakat) Bir TCP sıra numarası `4294967290` ve segment 10 bayt veri taşıyor. Sonraki segmentin sıra numarası kaçtır? Sıra numaralarının 32 bitte sarması (wrap) neden dikkat gerektirir?
8. (★★★) UDP üzerinde bir telemetri akışı kuruyorsun ve paketler sırasız gelebiliyor. Uygulama katmanına hangi alanları eklersin ve alıcı eski veriyi nasıl ayırt eder?
9. (★★) (Mülakat) Bir sunucuda çok sayıda `CLOSE-WAIT` soketi görüyorsun. Önce hangi tarafın hatalı olduğunu nasıl belirlersin ve hangi kodu incelersin?
10. (★★★) (Mülakat) İki taraf bir TCP bağlantısını aynı anda kapatmaya çalışırsa ne olur? Bu durum Şekil 29.6'daki hangi durumla ilişkilidir ve dörtlü kapanış modeli bu durumda neyi değiştirir?
11. (★★★) RTT'si 200 ms olan bir yolda yavaş başlangıç her RTT'de pencereyi iki katına çıkarıyor. Pencere 1460 baytlık 1 MB'a ulaşmak için yaklaşık kaç RTT gerekir? Bu süre sizin için neden önemlidir?
12. (★★★) Nagle algoritmasının ve gecikmeli onayın birleşiminin zarar verdiği bir uygulama tasarımı düşün. Bu tasarımı nasıl değiştirirsin: uygulama katmanında mı, soket seçeneğinde mi?

## Kod Okuma Egzersizi

Bu egzersizde iki gerçek Linux çekirdek başlık dosyasını okuyacaksın. Kaynak: Linux çekirdeği, sürüm **v6.6**, `include/uapi/linux/ip.h` (`struct iphdr`, satır 87–109) ve `include/uapi/linux/tcp.h` (`struct tcphdr`, satır 25–58). Dosyalar `torvalds/linux` deposunun v6.6 etiketinden alındı; `ip.h` için `raw.githubusercontent.com` 429 yanıtı verdiği için `cdn.jsdelivr.net` aynası kullanıldı. Metin birebir kopyalandı; yalnızca sekme karakterleri 4 boşlukla değiştirildi.

Önce `ip.h` içindeki IPv4 başlık yapısı:


```c
struct iphdr {
#if defined(__LITTLE_ENDIAN_BITFIELD)
    __u8    ihl:4,
        version:4;
#elif defined (__BIG_ENDIAN_BITFIELD)
    __u8    version:4,
        ihl:4;
#else
#error  "Please fix <asm/byteorder.h>"
#endif
    __u8    tos;
    __be16  tot_len;
    __be16  id;
    __be16  frag_off;
    __u8    ttl;
    __u8    protocol;
    __sum16 check;
    __struct_group(/* no tag */, addrs, /* no attrs */,
        __be32  saddr;
        __be32  daddr;
    );
    /*The options start here. */
};
```


Sonra `tcp.h` içindeki TCP başlık yapısı:


```c
struct tcphdr {
    __be16  source;
    __be16  dest;
    __be32  seq;
    __be32  ack_seq;
#if defined(__LITTLE_ENDIAN_BITFIELD)
    __u16   res1:4,
        doff:4,
        fin:1,
        syn:1,
        rst:1,
        psh:1,
        ack:1,
        urg:1,
        ece:1,
        cwr:1;
#elif defined(__BIG_ENDIAN_BITFIELD)
    __u16   doff:4,
        res1:4,
        cwr:1,
        ece:1,
        urg:1,
        ack:1,
        psh:1,
        rst:1,
        syn:1,
        fin:1;
#else
#error  "Adjust your <asm/byteorder.h> defines"
#endif
    __be16  window;
    __sum16 check;
    __be16  urg_ptr;
};
```


**Sorular — cevaplamadan geçme:**

1. `struct iphdr` içinde little-endian makineler için `ihl` alanı `version`dan önce yazılmıştır. Ağ baytı `0x45` bu yapıya konduğunda `ihl` ve `version` hangi dört bitten okunur? Big-endian tanımında sıra neden tersine dönmüştür?
2. C standardı bit alanlarının bellekteki sırasını belirtmez. Bu yüzden çekirdek `#if defined(__LITTLE_ENDIAN_BITFIELD)` gibi bir ayrım yapar. Bu ayrım olmasaydı aynı kaynak kodu iki farklı makinede neden yanlış okurdu?
3. `tcp.h`'de `syn` alanı little-endian tanımında hangi bit konumunda? TCP başlığının 13. baytı (bayrakların bulunduğu bayt) için `0x02` değeri, hem little-endian hem big-endian tanımda `syn` bitine denk gelir mi? Hesabını yaz.
4. `tot_len` ve `saddr` alanlarının türü `__be16` ve `__be32`dir. Bu tür adlandırması derleyiciye ne söyler ve bu alanları bir hesapta kullanmadan önce hangi dönüşüm gerekir?
5. `saddr` ve `daddr` alanları `__struct_group(..., addrs, ...)` içinde gruplanmıştır. Bu gruplama olmasaydı, iki adresi tek bir karşılaştırmayla kıyaslamak için kod nasıl yazılmak zorunda kalırdı?
6. `struct iphdr` içindeki `/*The options start here. */` yorumu neyi işaret eder? Seçenek alanlarının boyutunu bu yapıdan nasıl hesaplarsın (IHL ve 4 bayt kuralı)?

## Bölüm Özeti

- Katmanlı mimari, her katmanı tek bir sorunla sınırlar ve alt katmanın hizmetini kullanır; bu, Bölüm 21'deki soyutlama fikridir.
- OSI yedi katmanlı bir referans modeldir; internet ise dört katmanlı TCP/IP ile çalışır. Mülakatta ikisinin farkını ve birbirine karşılığını söyle.
- Kapsülleme her katmanın başlığını önüne eklemesidir; alıcıdaki çoklama, EtherType, protokol ve port alanlarına dayanır.
- Ethernet çerçevesi MAC adresleriyle aynı yerel ağda iletir; ARP IP'den MAC'e köprü kurar; anahtar MAC tablosuyla yalnızca gerekli porta gönderir.
- IPv4 başlığında TTL, protokol ve sağlama alanları vardır; alt ağ hesabı maske, AND ve OR ile yapılır. Yönlendirme tablosunda en uzun önek kazanır; bunun için ikili trie kullanılır.
- ICMP, ağ katmanının hata ve kontrol mesajlarını taşır; TTL alanı, traceroute'un yol izleme yöntemidir.
- TCP bağlantısı üçlü el sıkışma ile kurulur, dörtlü kapanışla kapanır; durum makinesi ve TIME_WAIT, bağlantının ömrünü belirler.
- TCP'de sıra ve onay numaraları kayan pencere ile akış kontrolü sağlar; AIMD tıkanıklığı kontrol eder; Nagle ve gecikmeli onay birlikte gecikme yaratabilir.
- UDP düşük gecikme ve düşük yük sunar, güvenilirliği uygulamaya bırakır; gerçek zamanlı telemetri bu yüzden UDP'ye yaslanır.

**Sonraki bölümde:** Bölüm 30 (HTTP, DNS, DHCP) ile uygulama katmanına çıkıyoruz. Bu bölümde gördüğün TCP bağlantısı HTTP'nin taşıyıcısı olacak; DNS ise adları IP adreslerine çevirirken UDP üzerinde çalışacak. DHCP ile bir cihaz bu bölümde görülen IP adresini, maskesini ve ağ geçidini nasıl alır, onu da göreceksin. Ayrıca QUIC'in UDP üzerinde kendi güvenilirliğini nasıl kurduğunu da orada ele alacağız.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. OSI modelinin katmanlarını say ve her birine bir örnek protokol ver. TCP/IP modeliyle eşleştir. Bu eşleşme neden tam birebir değildir?
2. Bir web sayfası açıldığında bir HTTP isteği, hangi başlıkların sırasıyla eklenerek bir Ethernet çerçevesine dönüştüğünü anlat.
3. Bir ev ağındaki bilgisayarlar neden internete tek bir kamusal IP ile çıkabilir? NAT tablosu hangi bilgileri tutar ve dönüş paketi nasıl doğru bilgisayara ulaşır?
4. `192.168.5.130/25` ağında kaç kullanılabilir host vardır ve bu adres hangi blokta yer alır? Cevabını elle yaz.
5. TCP bağlantısı neden üç adımda kurulur ve neden iki adımda kurulmaz? İki adımlı bir el sıkışmanın hangi durumda sorun çıkarabileceğini düşün.
6. Bir sunucuda binlerce `TIME_WAIT` soketi görmek normal midir, yoksa sorun işareti midir? `CLOSE_WAIT` soketlerinin birikmesiyle farkı nedir?
7. Gerçek zamanlı bir sensör akışı için TCP mi UDP mi seçersin? Kararını gecikme, güvenilirlik ve yük üzerinden gerekçelendir.
8. Yönlendirme tablosunda hedef bir önekle eşleşmiyorsa paket ne olur? Varsayılan yol olmasaydı bir yönlendirici hangi tepkiyi verirdi?
:::

