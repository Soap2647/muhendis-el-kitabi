
## 45.11 Vaka çalışması: EV Dashboard veri hattı

Bu bölümün en somut kısmı Mert'in kendi projesidir: Teknofest 2026 elektrikli araç takımının EV Dashboard'u. Sistemin protokol omurgası şöyledir. Daly BMS, batarya gerilimini, akımını, SOC'unu, sıcaklığını ve hücre gerilimlerini 13 baytlık UART çerçeveleriyle verir. Kelly motor sürücüsü hız verisini UART ile verir. Vites, sinyal ve far durumları STM32'nin GPIO pinlerinden okunur. STM32 bütün bunları bir JSON satırında toplayıp 200 ms'de bir UART3 üzerinden Raspberry Pi 5'e yollar. Pi'de iki servis çalışır: `telemetri.py` veriyi RFD900X telsiz modülü üzerinden yer istasyonuna iletir, `kadran.py` ise WebSocket ile tarayıcıdaki dashboard'a yayınlar.

Şekil 45.10 bu akışı gösterir. Bu bölümde kodu okurken dikkat edeceğin nokta şudur: her iki uçta, yani BMS ile STM32 arasında ve STM32 ile Pi arasında, **alınan baytın doğruluğunu hiçbir yerde denetlemiyoruz**. Bu, sistemin çalıştığı günlerde iyi görünür; ama gürültü, kablo gevşekliği ya da bir kesintiden sonra sessiz yanlış değerler üretir.

![Şekil 45.10: EV Dashboard veri akışı. BMS ve motor sürücüsü UART ile STM32'ye bağlanır; STM32 JSON satırını UART3 üzerinden Pi 5'e yollar; Pi iki servisle telsize ve tarayıcıya dağıtır.](gorseller/b45_ev_akis.png)

### Bulgular

Aşağıdaki tablo, kodu satır satır okuyup her bulguyu bir kanıtla eşleştirir. Kanıt türü üç sınıftan biridir: **kod incelemesi** (satır mantığından çıkan), **kaynak karşılaştırması** (ESPHome daly_bms.cpp'nin resmi olmayan ama açık kaynaklı Daly sürücüsü ile), ya da **simülasyon** (arşivdeki programlar). Kaynak dosyalar salt okunurdur ve değiştirilmemiştir; satır numaraları `stm32/main.c` ve `rpi/*.py` dosyalarına aittir.

| No | Konum | Bulgu | Kanıt |
|---|---|---|---|
| B1 | main.c, 47–57 ve 66–69 | Daly yanıtında başlık (0xA5), adres (0x01), komut eşleşmesi ve sağlama denetimi yok. Yanıt doğrudan alan olarak okunuyor. | Kod incelemesi; 45.4 örneği |
| B2 | main.c, 75–77 | 0x95 (hücre) yanıtında kare numarası (bayt 4) ve ilk hücrenin üst baytı gerilim sanılıyor. Sonuç 0,268 V; doğru değer 3,300 V. Ayrıca "en düşük hücre" hesaplanmıyor; tek karede yalnızca 3 hücre var. | ESPHome kaynağı (hücre 1: bayt 5–6); simülasyon |
| B3 | main.c, 62–78 ve 155–166 | Zaman aşımında eski değer korunur; yaşı belli olmaz. Hiçbir bayrak yok. | Kod incelemesi |
| B4 | main.c, 90 | Yorum "RPM -> km/h" diyor, ama dönüşüm yok; ham RPM değeri hız olarak yollanıyor. Dönüşüm, tekerlek çevresi ve dişli oranı gerektirir. | Kod incelemesi |
| B5 | main.c, 98–109 | Hiçbir vites pini aktif değilse vites `'D'` oluyor. Kablo kopması sürüş modu olarak görünür. | Kod incelemesi |
| B6 | main.c, 123–131 | `snprintf` ile `%f` kullanılıyor. Gömülü libc'de float biçimlendirmesi bağlayıcı bayrağına bağlıdır; bayrak yoksa `volt` ve `cell` alanları bozulur. | Sembol kontrolü (45.10); proje bağlayıcı ayarı dosyada yok |
| B7 | main.c, 137–141; telemetri.py, 60–65 | JSON satırında sıra no, sağlama ya da uzunluk alanı yok. Bozulan bir rakam geçerli JSON kalır. | Simülasyon (aşağıdaki tablo) |
| B8 | telemetri.py, 77–79 | JSON geçerli ama bir nesne değilse (örneğin `5`), `veri.get(...)` bir `AttributeError` fırlatır; yalnızca `SerialException` yakalandığı için servis durur. | Simülasyon: `'int' object has no attribute 'get'` |
| B9 | telemetri.py, 67–71 | 5 Hz sınırı gelen paketleri atarak uygulanır. 190 ms aralıkla gelen 10 pakette 5 tanesi iletildi. Tam 200 ms aralıkta kayan nokta ve jitter yüzünden bazı paketler atıldı. STM32 periyodu 200 ms'den uzun olduğu için filtre çoğunlukla etkisizdir, ama bir garanti değildir. | Simülasyon |
| B10 | kadran.py, 43–57 | Yayın sırasında bir istemci bağlanır ya da ayrılırsa `RuntimeError: Set changed size during iteration` oluşur. Hata `seri_oku` üzerinden tüm servisi düşürür. `kadran.service` (Restart=always, RestartSec=3) hizmeti üç saniye sonra yeniden başlatır; tüm tarayıcılar bu sürede kopar. | Simülasyon (gerçek `yayinla` kodu) |
| B11 | telemetri.py, 18; kadran.py, 8 | İki servis de `/dev/ttyAMA2` hattını açar. Aynı anda çalışırlarsa her bayt yalnızca birine gider; veri bölünür. `baslat.sh` yalnızca tarayıcıyı başlatır, hangi servisin çalışacağı kurulumda belirlenmeli. | Kod incelemesi; Linux seri port semantiği (genel bilgi) |
| B12 | main.c, 47–57 | Daly UART hızı dosyada yok (`MX_USART1_UART_Init` ayrı dosyada). Sürücünün 9600 mı başka bir hızda mı çalıştığı doğrulanmalı. | Kod incelemesi |

Üç bulgu özellikle üzerinde durmaya değer. Birincisi **B2**: bu bir yorumlama hatasıdır; doğru uzunluk ve ofset bilgisine sahipsen düzeltmek kolaydır, ama hatanın fark edilmemiş olması, B1'in bir sonucudur. Doğrulanmamış bir yanıtın alanları yanlış anlamlandırıldığında hata sessizce kalır. İkincisi **B7 ve B10**: sessiz bozulma ile servis çökmesi, sağlamlık ve hata izolasyonu konusunun iki yüzüdür. Üçüncüsü **B3**: zaman aşımı ve yaş bilgisi yokken bir sensör durduğunda sistem eski veriyi taze gibi gösterir. Bir EV'de bu, sürücünün yanlış bir batarya yüzdesine güvenmesi demektir.

Aşağıdaki simülasyon, B7'yi sayısal olarak gösterir. Her kare 15 baytlık sabit bir yük (hız, batarya, gerilim, menzil, sıcaklık, hücre, vites ve sinyaller) taşır. Bir JSON satırı ile 21 baytlık ikili çerçeve aynı veriyi taşır. İkisine de bit başına eşit olasılıkla ters çevirme uygulanır; 20000 kare üzerinden kabul edilen yanlış değerler sayılır. Sabit tohum 45 kullanıldı; simülasyon programı arşivdedir.

| Bit hata olasılığı (BER) | CRC-çerçeve: yanlış kabul | CRC-çerçeve: red | JSON: yanlış kabul | JSON: red |
|---|---|---|---|---|
| 1 × 10⁻⁴ | 0 | 357 | 707 | 1178 |
| 1 × 10⁻³ | 0 | 3074 | 3647 | 8687 |
| 3 × 10⁻³ | 0 | 7947 | 2536 | 16358 |

Tablonun önemli yanı, JSON'un "yanlış kabul" sütunudur: 1 × 10⁻³ gibi orta bir hata oranında 20000 karenin 3647'si geçerli JSON olarak kabul edilip yanlış değer taşır. CRC hattında bu sayı sıfırdır; bozuk kareler reddedilir. Bedeli, kırmızı sütundaki reddetmelerdir: CRC hattı daha çok kareyi atar. Bu takas, bir telemetride genellikle doğrudur: eksik bir kare, yanlış bir kareden daha az zararlıdır, çünkü yer istasyonu bir sonrakini bekleyebilir.

### Sağlamlaştırılmış çerçeve önerisi

Önerilen çerçeve, bu bölümdeki parçaları birleştirir: sürüm alanı (Bölüm 31.5), sıra numarası (boşluk ve yinelenen tespiti), sabit uzunlukta ikili yük (JSON'daki ondalık biçimlendirme ve ayrıştırma sorunları yok, boyut küçük), CRC-16 (bütünlük) ve COBS (çerçeve sınırı).

| Alan | Boyut | Açıklama |
|---|---|---|
| SÜRÜM | 1 bayt | Protokol sürümü (şu an 1) |
| SIRA | 1 bayt | 0–255 arası döngüsel sıra numarası |
| YÜK | 15 bayt | spd (u16), bat (u8), volt×10 (u16), range (u16), btemp (i8), tmp (i8), cell mV (u16), gear (ASCII), sigL, sigR, beam (u8) |
| CRC16 | 2 bayt | CRC-16/CCITT-FALSE, SÜRÜM + SIRA + YÜK üzerinde, büyük uç |
| Ayraç | 1 bayt | 0x00 (COBS kodlamasından sonra) |

Çerçeve 21 bayttır. Aynı veri JSON satırı olarak ortalama 118,9 bayt tutar (ölçüm: 2000 rastgele yük). 5 Hz yayında JSON yaklaşık 595 bayt/s, ikili çerçeve yaklaşık 105 bayt/s üretir. Telsiz modülünün hava hızı ayrı bir ayardır ve burada bu oranın doğrudan bir sonucu değildir; ama daha az bayt, daha az çarpışma ve daha kısa gecikme demektir.

Aşağıdaki C kodu STM32 tarafındaki kodlayıcıdır. Yük, struct dolgusuna güvenmeden baytlara tek tek yazılır; bu, derleyiciden ve hedef mimariden bağımsız bir düzen sağlar (Bölüm 2.7 ve 1.5).

{{KOD|telemetri_cerceve.h|1|32|c}}

{{KOD|telemetri_cerceve.c|1|24|c}}

{{KOD|telemetri_cerceve.c|25|47|c}}

Aşağıdaki demo, Python'daki başvuru çerçevesiyle aynı yükü kodlar. Çıktıdaki 21 bayt, 45.3'teki COBS ve 45.4'teki CRC ile hesaplanmıştır; Python ölçümünde kullanılan çerçeve ile birebir aynıdır.

{{KOD|ornek_tel.c|1|15|c}}

{{CIKTI|gcc -std=c11 ornek_tel.c telemetri_cerceve.c cobs.c crc16.c; ./a.out|out/ornek_tel.txt}}

Pi tarafındaki çözücü, bu çerçeveyi ters sırayla uygular: sonlandırıcıya kadar oku, COBS çöz, uzunluk 19 mu kontrol et, CRC'yi doğrula, sürümü denetle, sırayı önceki sıra ile karşılaştır (boşluk ya da yineleme varsa say) ve yükü aç. Zaman aşımı kuralı da eklenmelidir: son geçerli çerçeveden 500 ms geçtiyse dashboard veriyi "bayat" işaretlemelidir. Bu, B3'ün ve B10'un da çözümüdür. Pi tarafındaki çözücüyü yazmak, Kendin Yap bölümündeki ilk projedir.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, Bölüm 5'teki altı adımı izler. Her birinde adımlar ayrı başlıklarla işaretlenmiştir ve son adımda elle iz sürme tablosu bulunur. Zorluk sırası ★, ★★, ★★, ★★★ şeklindedir.

### Örnek 1 (★): 0x4B baytını bir UART hattında çiz ve örnekle

**Adım 1 — Anla.** Hat 8N1 (8 veri biti, parite yok, 1 durdurma biti) çalışıyor. Verici 0x4B baytını gönderiyor. Alıcının saati, vericinin saatinden %6 yavaş (d = +0,06). Soru: alıcı baytı doğru okur mu? Okursa her bit nerede örneklenir? Okumazsa hangi bit yanlış olur?

**Adım 2 — Örnekle.** `0x4B = 0100 1011`. UART LSB önce gönderir: bit 0 = 1, bit 1 = 1, bit 2 = 0, bit 3 = 1, bit 4 = 0, bit 5 = 0, bit 6 = 1, bit 7 = 0. Çerçeve: `0 | 1 1 0 1 0 0 1 0 | 1` (başlangıç, veri, durdurma). Toplam 10 bit penceresi, indeksleri 0–9.

**Adım 3 — Kaba çöz.** Verici k. biti `[k, k+1)` aralığında tutar (birim: bir bit süresi). Alıcı k. biti `t_k = (k + 0.5) · (1 + d)` anında örnekler. Sapma yoksa her örnek kendi penceresinin ortasındadır. Sapma varsa örnek kayar; kayma k ile birlikte artar. Hangi k'da örnek pencereden çıkar?

**Adım 4 — Örüntü.** Kayma `(k + 0.5) · d` kadardır. Örnek, pencerenin sonunu geçer ve bir sonraki pencereye düşerse hata oluşur: `(k + 0.5)(1 + d) ≥ k + 1`. d = 0,06 için bu `(k + 0,5) · 0,06 ≥ 0,5`, yani `k ≥ 0,5/0,06 − 0,5 ≈ 7,83`. Bu, k = 8 ve k = 9 için hata demektir. Ama dikkat: k = 9 durdurma biti olduğundan ve bir sonraki pencere boşta (1) olduğundan, durdurma bitindeki hata görünmez. Bayt bozulması k = 8 ile olur, çünkü o bit 0 iken bir sonraki pencerede 1 okunur.

**Adım 5 — İyileştir.** Yapılabilecek iki şey var. Birincisi, saat sapmasını azaltmak: iki tarafın saatini harici bir kristalle sabitlemek ya da baud hızını bölen değerle tam tutturmak (genel bilgi: bazı UART çevre birimleri 16 kat aşırı örnekleme yapar, böylece örnek anı bit süresinin 1/16'sı kadar hassas olur). İkincisi, çerçeveyi bu hatadan bağımsız kılmak: Bölüm 45.3'teki COBS + CRC ile bozuk bayt reddedilir ve yanlış değer taşınmaz.

**Adım 6 — Doğrula.** Her k için örnek anını, pencereyi ve okunan biti tabloya yazalım. `d = 0` ve `d = +0,06` karşılaştırılıyor.

| k | t_k (d = 0) | t_k (d = +0,06) | Pencere | Hat biti | Okunan (d = +0,06) |
|---|---|---|---|---|---|
| 0 (başlangıç) | 0,50 | 0,53 | [0, 1) | 0 | 0 |
| 1 | 1,50 | 1,59 | [1, 2) | 1 | 1 |
| 2 | 2,50 | 2,65 | [2, 3) | 1 | 1 |
| 3 | 3,50 | 3,71 | [3, 4) | 0 | 0 |
| 4 | 4,50 | 4,77 | [4, 5) | 1 | 1 |
| 5 | 5,50 | 5,83 | [5, 6) | 0 | 0 |
| 6 | 6,50 | 6,89 | [6, 7) | 0 | 0 |
| 7 | 7,50 | 7,95 | [7, 8) | 1 | 1 |
| 8 | 8,50 | **9,01** | [8, 9) | 0 | **1** (pencere dışı) |
| 9 (dur) | 9,50 | **10,07** | [9, 10) | 1 | 1 |

Okunan bayt `1 1 0 1 0 0 1 1` olur ve değeri `0xCB`'dir. Yani d = +0,06'da 0x4B, 0xCB olarak okunur. Simülasyonda bunu sınadığımızda da aynı sonuç çıktı; tolerans taraması d = +5,88 üst sınırını bulmuştu, dolayısıyla +6 bu sınırın dışındadır.

::: ipucu
Bu örnek, tolerans sınırının neden **bir yüzde değil, bir bayt bazında** olduğunu gösterir. Sınırın altında her bayt doğru okunur; üstünde yalnızca belirli bit desenleri (son veri biti 0 olan baytlar) bozulur. Bu yüzden sınır testini yalnızca tek bir baytla yapmak yanıltıcı olur.
:::

**Bunu AI'sız yazabilir misin?** Son veri biti 1, diğer bitleri 0 olan bir bayt (`0x80`) düşün. Sapma negatif olduğunda hangi `k` değerinde hata oluşur? Bu, `0x4B` örneğindeki hesabın tersi yönüdür; formülü türetip bir tabloyla doğrula.

### Örnek 2 (★★): Bir I2C okuma işleminin bit izi

**Adım 1 — Anla.** Ana, 7 bitlik adresi `0x50` olan uyduya yazar: önce yazmaç adresi `0x10`, sonra tekrarlanan START ile okuma yapar ve iki bayt (`0x5A`, `0x6B`) alır. İzi, her bitin ne olduğunu ve her ACK/NACK'in nerede verildiğini gösterecek şekilde yazmamız istenir.

**Adım 2 — Örnekle.** Adres baytları: yazma için `0x50 << 1 | 0 = 0xA0`, okuma için `0x50 << 1 | 1 = 0xA1`. Bunların ikili gösterimi `1010 0000` ve `1010 0001`dir. Yazmaç adresi `0x10 = 0001 0000`. Veriler: `0x5A = 0101 1010`, `0x6B = 0110 1011`.

**Adım 3 — Kaba çöz.** İşlem sırası: START, adres yazma (8 bit, ACK), yazmaç (8 bit, ACK), tekrarlanan START, adres okuma (8 bit, ACK), veri 1 (8 bit, ACK ana tarafından), veri 2 (8 bit, NACK ana tarafından), STOP. Burada ACK'i kimin verdiğine dikkat et: adresten sonraki ACK uydudan, okunan verilerden sonraki ACK anadan gelir.

**Adım 4 — Örüntü.** Her baytta sekiz veri biti MSB önce gider, dokuzuncu bit ACK slotudur. Okumada veri biti uydu tarafından SDA'ya konur; ana yalnızca SCL yüksekken okur. Son okunan bayttan sonra ana NACK gönderir ve STOP çıkarır. Yazmadan okumaya geçişte STOP beklenmez; tekrarlanan START kullanılır.

**Adım 5 — İyileştir.** Okuma izinin her baytını, uydu tarafında hangi yazmaç adresinden geldiğiyle birlikte yaz. Bu örnekte okunan iki bayt `0x10` ve `0x11` yazmaçlarındadır; uydunun yazmaç işaretçisi her veri baytında bir artar. Böylece 'hangi bayt hangi konumdan geldi' sorusu izden doğrudan cevaplanır.

**Adım 6 — Doğrula.** Aşağıdaki tablo, her adımın SDA'da ne göründüğünü ve kimin sürdüğünü gösterir (ACK = SDA 0; NACK = SDA 1).

| Sıra | Gönderen | İçerik | Bitler (MSB önce) | SDA'da ne görünür | Yanıt |
|---|---|---|---|---|---|
| 1 | Ana | START | — | SCL yüksekken SDA düşer | — |
| 2 | Ana | Adres yazma `0xA0` | 1010 0000 | Ana sürer | Uydu ACK (SDA = 0) |
| 3 | Ana | Yazmaç `0x10` | 0001 0000 | Ana sürer | Uydu ACK |
| 4 | Ana | Tekrarlanan START | — | SCL yüksekken SDA düşer | — |
| 5 | Ana | Adres okuma `0xA1` | 1010 0001 | Ana sürer | Uydu ACK |
| 6 | Uydu | Veri 1 `0x5A` | 0101 1010 | Uydu sürer (ana okur) | Ana ACK (SDA = 0) |
| 7 | Uydu | Veri 2 `0x6B` | 0110 1011 | Uydu sürer | Ana NACK (SDA = 1) |
| 8 | Ana | STOP | — | SCL yüksekken SDA yükselir | — |

Tablo, simülasyon modelinin olay sırasıyla aynıdır (START, ACK, ACK, tekrarlanan START, ACK, OKU, OKU, STOP). Bu örnekte uydunun `0x10` ve `0x11` konumlarında önceden `0x5A` ve `0x6B` bulunduğunu varsayıyoruz; ana bu iki baytı okur.

**Bunu AI'sız yazabilir misin?** Aynı işlemi, ana yalnızca **bir** bayt okuyacak şekilde değiştir. Son okunan bayttan sonra SDA ne olmalı? Hangi sıra numarasında STOP gelir? Ve bu bir bayt okumada yazmaç adresi neden yine de gönderilmelidir?

### Örnek 3 (★★): Üç CAN düğümünün tahkimi

**Adım 1 — Anla.** Üç düğüm aynı anda 11 bitlik kimliklerle başlıyor: A `0x123`, B `0x0A5`, C `0x3F0`. Hangi düğüm kazanır? Hangi bitte hangisi kaybeder? Kaybettikten sonra hangisi hatta yazmayı sürdürür?

**Adım 2 — Örnekle.** İkili gösterimler (11 bit, MSB önce): `0x123 = 001 0010 0011`, `0x0A5 = 000 1010 0101`, `0x3F0 = 011 1111 0000`. Her mesajın başında bir SOF biti (0) vardır, ardından kimlik gelir.

**Adım 3 — Kaba çöz.** Her bitte hattın değeri, gönderen tüm düğümlerin AND'idir (baskın 0). Bir düğüm 1 gönderir ve hat 0 okursa kaybeder. İlk bit SOF'tur ve üç düğümün de 0'ı var, bu yüzden tahkim orada başlar.

**Adım 4 — Örüntü.** Bitleri karşılaştır: SOF (indeks 0): üçü de 0. ID10 (indeks 1): üçü de 0. ID9 (indeks 2): A 0, B 0, C 1. C 1 gönderir, hat 0 olur; C kaybeder. ID8 (indeks 3): A 1, B 0. A 1 gönderir, hat 0; A kaybeder. Geriye B kalır.

**Adım 5 — İyileştir.** Kazananın kendini tanıması için ayrı bir mekanizmaya gerek yoktur; tahkim kendi içinde kazananı seçer. Tasarım açısından önemli olan, düğümlerin öncelik tablosunu kimlik seçimiyle kurmaktır: kritik mesajlara en küçük kimlikleri ver.

**Adım 6 — Doğrula.** Aşağıdaki tablo, programın çıktısıyla aynı sonucu verir: `ornek_can.py` çıktısında `bit 2` satırında `0x3F0`, `bit 3` satırında `0x123` kaybeder ve kazanan `0x0A5`'tir.

| İndeks | Bit (A) | Bit (B) | Bit (C) | Hat | Kaybeden |
|---|---|---|---|---|---|
| 0 (SOF) | 0 | 0 | 0 | 0 | — |
| 1 (ID10) | 0 | 0 | 0 | 0 | — |
| 2 (ID9) | 0 | 0 | **1** | 0 | C |
| 3 (ID8) | **1** | 0 | (kaybetti) | 0 | A |

**Bunu AI'sız yazabilir misin?** `0x3F0` yerine `0x3F1` kullansaydın tahkim sonucu değişir mi? Hangi bitte? Dolgu biti kimlik bitlerinin arasına girdiğinde tahkim karşılaştırması hangi bitleri karşılaştırır?

### Örnek 4 (★★★): Daly BMS paketini elle kur, bozulmuş paketi yakala

**Adım 1 — Anla.** Daly BMS'ten gelen 0x90 yanıtı 13 bayttır. Bu örnekte iki şeyi yapacağız: yanıtın sağlamasını elle hesaplayacağız, sonra iki gerilim baytının yer değiştiği bir paketi hem toplama sağlamasıyla hem CRC-16 ile denetleyeceğiz. Ayrıca `main.c`'nin 0x95 çözümlemesindeki hatayı göreceğiz.

**Adım 2 — Örnekle.** Daly yanıtında baytlar şöyle: 0–3 başlık (`A5 01 90 08`), 4–5 gerilim (×0,1 V), 6–7 kullanılmıyor, 8–9 akım (ofsetli), 10–11 SOC (×0,1 %), 12 sağlama. Gerilim 52,3 V ise ham değer `523 = 0x020B`. Yani bayt 4 = `02`, bayt 5 = `0B`.

**Adım 3 — Kaba çöz.** Sağlama, bayt 0'dan 11'e kadar olan baytların toplamının alt 8 biti. Yanıtı kurmak için toplamı hesaplayacağız: `A5 + 01 + 90 + 08 + 02 + 0B + 00 + 00 + 74 + B3 + 03 + 6A`. Ardından gerilim baytlarını yer değiştirip yeniden hesaplayacağız.

**Adım 4 — Örüntü.** Toplama, bayt sırasına duyarsızdır: iki baytı yer değiştirmek toplamı değiştirmez. Bu yüzden sağlama, gerilim baytlarının yer değişimini yakalayamaz. CRC-16 ise sıraya duyarlıdır; bu yüzden aynı hatayı yakalar. Yani sorun bir "toplama" sorunudur, bir "veri" sorunu değildir.

**Adım 5 — İyileştir.** Doğrulanmamış bir yanıtı kabul etmemek için üç adım eklenir: (a) başlık (0xA5), adres (0x01) ve komut eşleşmesi denetlenir, (b) sağlama hesaplanır, (c) aralık denetimi yapılır (gerilim makul bir aralıkta mı?). CRC, Daly'nin kendi sağlamasının yerine geçmez; ancak BMS yanıtını STM32 ile Pi arasında taşırken kendi çerçevemizde kullanılabilir.

**Adım 6 — Doğrula.** Aşağıdaki tablo, programın çıktısıyla birebir uyuşur (`ornek_daly.py`).

| Alan | Orijinal (hex) | Yer değiştirmiş (hex) | Açıklama |
|---|---|---|---|
| Bayt 4–5 | 02 0B | 0B 02 | Gerilim ham değeri |
| Gerilim | 52,3 V | 281,8 V | 0x0B02 = 2818; ÷10 |
| Toplam (alt 8 bit) | DF | DF | Aynı; toplama yakalamaz |
| CRC-16 (12 bayt) | BC50 | CE95 | Farklı; CRC yakalar |
| Sağlama baytı (12) | DF | DF | Değişmedi |

Aynı paketin 0x95 hücre yanıtı için: `A5 01 95 08 01 0C E4 0C D7 0C F0 00 13`. Bayt 4 kare numarası (1). Hücre 1 bayt 5–6: `0C E4` = 3300 mV = 3,300 V. `main.c` ise `((bayt4 << 8) | bayt5) / 1000` hesaplar: `(0x01 << 8 | 0x0C) = 268`, yani 0,268 V. Program çıktısında `main.c hucre = 0.268 V` ve `dogru hucre1 = 3.300 V` satırları bu farkı gösterir.

**Bunu AI'sız yazabilir misin?** İstek çerçevesinin (`A5 40 90 08 00...`) sağlaması `0x7D`'dir; bunu elle doğrula. Sonra bayt 8–9 akım değerini `−12,5 A` için (ofsetli) yeniden hesapla ve sağlamayı güncelle. Son olarak, yanıtın adres baytını `0x02` yapıp sağlamayı yeniden hesaplarsan, `daly_sorgu`'nun hangi dönüş kodunu vereceğini söyle.

## Kendin Yap Projeleri

::: dikkat
Bu projeleri **yapay zekâ aracı olmadan** yapacaksın. Bölüm metnini, şekilleri ve arşivdeki kodu okuyabilirsin; ama kodu yazarken bir aracın öneri vermesine izin verme. Bir sorunda takıldığında önce kendi notlarına ve dokümana dön; hâlâ çözülmüyorsa ipucunu oku, sonra tekrar dene.
:::

### Proje 1 (★★): EV telemetri hattını sağlamlaştır

**Amaç.** EV Dashboard'un STM32'den Pi'ye giden JSON hattını, 45.11'deki sağlamlaştırılmış çerçeveye geçirmek. STM32 tarafındaki kodlayıcı, bu bölümde verilen `telemetri_cerceve.c` dosyasıdır. Senin işin Pi tarafındaki çözücüyü, sıra takibini ve bayatlık denetimini yazmak.

**Beklenen davranış.** Pi, her seri sonlandırıcıya kadar bir kare okur, COBS çözer ve CRC'yi doğrular. Yalnızca geçerli kareler işlenir. Sıra numarası bir önceki kareye göre atlamışsa kayıp sayısı artar; aynı sıra iki kez gelirse yinelenen sayısı artar. Son geçerli kareden 500 ms geçtiyse veri "bayat" işaretlenir. Bozuk bir kare, servisi düşürmeden atlanır.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Çözücüyü üç parçaya böl: kareyi ayırma (sonlandırıcıya kadar tampon), COBS çözme ve doğrulama, yükü açma. Yük açma için `struct` modülünün `<HBHHbbHBBBB` biçimini kullanabilirsin; bu biçim C'deki düzenle birebir eşleşir. Kayıp sayacını ve bayatlık zamanlayıcısını ayrı bir sınıfta tut. Test için Bölüm 39'daki sahte (fake) yaklaşımı kullan: gerçek seri port yerine baytları bir listeden veren bir nesne.

**Başarı kriterleri.**
1. Gürültü testinde (BER = 1 × 10⁻³, 20000 kare, sabit tohum 45) yanlış kabul edilen kare sayısı 0 olmalı.
2. 100 kare bilerek atıldığında kayıp sayacı tam 100 göstermeli; sıra numarası 255'ten 0'a sardığında da doğru çalışmalı.
3. Son geçerli kareden 500 ms sonra "bayat" işareti verilmeli; yeni bir kare gelince işaret kalkmalı.
4. Servis, JSON olmayan, uzunluğu yanlış ve geçersiz COBS içeren kareler karşısında çökmemeli.

### Proje 2 (★★★): I2C protokol çözücü

**Amaç.** Bir bit düzeyi I2C izini (her satır: zaman, SCL, SDA) alıp bunu START, STOP, adres, R/W, veri baytları ve ACK/NACK olarak çözen bir program yazmak. Bu, bir mantık analizörünün protokol çözücüsünün en küçük hâlidir (45.9).

**Beklenen davranış.** Çözücü, SCL yükselirken SDA değişirse START ya da STOP tanır (SCL yüksekken SDA'nın düşmesi START, yükselmesi STOP). SCL yükseldiğinde SDA'yı okuyup sekiz bit toplar, dokuzuncu bitin ACK olup olmadığını bildirir. Tekrarlanan START'ı yeni bir işlem başlatmadan ayırt eder.

**Önerilen yaklaşım (ipucu).** Her adımın durumunu (beklemede, bit toplama, ACK bekleme) bir değişkenle izle. Girdi olarak bir liste ya da CSV kullanabilirsin; girdiyi kendin üret: bu bölümdeki şekil 45.6'nın bit düzeyi karşılığını bir kenar kenar yazmak iyi bir alıştırmadır. Bir hata (ACK yokluğu, yarım bayt) gelirse çözücü hata durumuna geçmeli ve yeniden senkron olmalıdır.

**Başarı kriterleri.**
1. Yalnızca yazma yapan bir işlem (adres + iki bayt) doğru adres, doğru bayt ve doğru ACK bilgisiyle çözülmeli.
2. Tekrarlanan START içeren bir yazma-oku işlemi, iki ayrı çerçeve olarak değil tek bir işlem olarak görünmeli (aynı işlemin parçaları).
3. Hiçbir aygıtın ACK vermediği bir adres NACK olarak raporlanmalı.
4. Rastgele bozulmuş bir izde çözücü takılı kalmamalı; bir STOP'ta yeniden başlamalı.

## Ek Alıştırmalar

1. **★** 0x55 baytını 8N1 UART'ta gönder: `0101 0101` LSB önce hangi çerçeveyi üretir? Bit 0'dan başlayarak 10 bitlik diziyi yaz.
2. **★** Bir UART hattı 115200 bps'de çalışıyor. Tek bir bit süresi kaç µs'dir? 8N1 ile bir bayt kaç µs sürer?
3. **Mülakat ★★** İki tarafın saatleri birbirinden zıt yönde %2 sapıyor: toplam sapma %4. 8N1 çerçevesi güvende mi? Hangi sınıra göre karar verdin?
4. **★★** SPI'de CPOL = 1 ve CPHA = 1 kipi hangi kenarda veri hazırlar, hangi kenarda okur? Bir tablo çiz.
5. **★★** Dört uydu tek bir SPI hattına bağlanacak. CS hattı sayısı ile zincirleme (daisy chain) yapısını karşılaştır. Hangisi daha az pin kullanır, hangisi daha yavaş olur?
6. **★★** I2C'de bir ana 0x50 adresine yazarken 0x51'e de yazmaya çalışırsa tahkimde hangi bit belirleyici olur? Neden?
7. **★★** I2C hattında iki çekme direncini paralel bağlarsan etkin direnç ne olur? Bu, hızlı moda geçişte ne anlama gelir?
8. **★★★** CAN'de iki düğüm aynı kimlikle mesaj gönderirse ne olur? Tahkim bu durumu çözebilir mi? (İpucu: veri alanı ve CRC'ye bak.)
9. **Mülakat ★★★** Toplama sağlaması ile CRC-8 (poli 0x07) arasında bir karşılaştırma yap. Hangi hata türlerinde CRC-8 toplamadan üstün, hangilerinde eşit?
10. **Mülakat ★★** "Bir I2C hattında SDA 0'da kilitlendi. Hangi adımları izlersin ve neden?" sorusunu, 9 saat darbesi kuralını da kullanarak cevapla.
11. **Mülakat ★★★** "Kesme tabanlı bir UART alıcısında halka tampon kullanırken hangi yarış koşulu oluşabilir? Tek üretici tek tüketici olduğunda nasıl önlenir?" sorusunu yaz.
12. **Mülakat ★★** "CRC bütünlük sağlar mı, kimlik doğrulaması sağlar mı?" sorusunu iki cümlede yanıtla ve bir örnek ver.

