%% kisim_no: X
%% kisim_ad: Yazılım Mühendisliği Pratiği
%% bolum_no: 41
%% baslik: System Design

## Giriş: Kutuları çizmek ile sistemi kurmak arasındaki fark

Şimdiye kadar yazdığın programların çoğu tek bir makinede, tek bir kullanıcı için çalıştı. Bir dizi sıraladın, bir ağaç kurdun, bir sunucu yazdın. Gerçek bir hizmette ise aynı programın yüzlerce kopyası aynı anda çalışır, veri birkaç makineye yayılır, bir makine her an kapanabilir ve kullanıcılar "neden yavaş?" diye sorar. Bu noktada soru "bu kod doğru mu?" olmaktan çıkar; "bu parçalar bir arada, yük altında ve arıza varken ne yapar?" sorusuna döner. Sistem tasarımı, bu soruya önceden cevap verme sanatı ve bilimidir.

Bölüm 40'ta bir API'nin sözleşmesini, Bölüm 42'de ise programın bir konteynere konup nasıl dağıtılacağını göreceksin. Bu bölüm bu iki parçanın altındaki soruyu sorar: hangi parçalar olmalı, kaç tane olmalı, hangisi çökerse ne olur, ve bunların hepsinin bedeli nedir? Sistem tasarımında doğru cevap çoğu zaman tek değildir. Bir tasarımı "doğru" ya da "yanlış" yapan şey, gereksinimlerle ne kadar uyumlu olduğudur.

Mülakatlarda bu konu "URL kısaltıcı tasarla" ya da "bir mesajlaşma uygulamasının arka ucunu çiz" gibi sorularla gelir. Kağıda kutu çizmek kolaydır. Zor olan, her kutunun neden orada olduğunu, o kutu çöktüğünde ne olacağını ve trafik on katına çıktığında hangisinin önce kırılacağını söylemektir. Bu bölümde bu üç soruyu sayılarla cevaplamayı öğreneceksin.

Savunma sanayiinde bu soru somut bir biçim alır. Bir İHA'nın telemetrisi saniyede yüzlerce ölçüm üretir; bu veri uçakta kısa süreli tutulur, yer istasyonuna gelir, merkezde uzun süre saklanır ve bir komut kanalı da ters yönde çalışır. Ağ bağlantısının kesilmesi, bir yer istasyonunun yavaşlaması ya da bir komutun iki kez işlenmesi bir oyun hatası değildir; görev sonucunu değiştirebilir. Mert'in EV Dashboard projesindeki STM32 sensör akışı küçük bir ölçekte aynı soruyu sorar: veri üretilir, taşınır, saklanır ve gösterilir. Aradaki her adımda bir gecikme ve bir arıza ihtimali vardır.

::: not
Bu bölümdeki tüm sayılar, kitapla birlikte verilen betiklerle üretildi. Ortam: Windows 11 Pro, Python 3.12.10, numpy 2.3.5. Rastgele deneylerin tohumu 41'dir ve her kod bloğunun altındaki çıktı, o bloğun gerçek çıktısıdır. Sayıları kendi makinende yeniden üretebilirsin. numpy'ın rastgele sayı üreteci sürümler arasında akışını değiştirebilir (numpy belgesi bunu garanti etmez); bu yüzden bu bölümdeki M/M/1 sayıları numpy 2.3.5 ile alındı. Sapma görürsen önce sürümü kontrol et.
:::

## 41.1 Sistem tasarımı nedir?

Sistem tasarımı, bir problemi çözecek bileşenleri, bileşenler arasındaki veri akışını ve her kararın bedelini tasarlamaktır. Bir köprü tasarlayan mühendis için yük, rüzgâr, malzeme maliyeti ve bakım birlikte düşünülür. Bir yazılım sistemi için de benzer dört eksen vardır: **ne kadar iş** (ölçek), **ne kadar hızlı** (gecikme), **ne kadar sık bozulur ve bozulunca ne olur** (dayanıklılık ve kullanılabilirlik) ve **ne kadara mal olur** (maliyet). Bu dört eksen birbiriyle yarışır. Daha hızlı yanıt için bellek harcarsın; daha dayanıklı olmak için ikinci bir kopya tutarsın, bu da maliyeti ve tutarlılık sorununu artırır.

Acemi tasarımların ortak hatası, sorunu çözmeden çözümü seçmektir: "Kafka kullanalım", "Kubernetes'e koyalım", "her şeyi Redis'e alalım". Bu kararların her biri belirli bir gereksinimi karşılar ama bir bedeli de vardır. Gereksinimi bilmeden çözüm seçmek, nedeni bilinmeyen bir ilacı içmeye benzer.

Bu yüzden tasarım bir süreç olarak ele alınır. Şekil 41.1 süreci altı adımda gösteriyor. Her adım bir öncekinin çıktısına dayanır ve her adım somut bir sayı ister. Son adım, yani darboğaz ve takas, süreci bir döngüye dönüştürür: bir takas ilk tasarımı değiştiriyorsa geri dönersin.

![Şekil 41.1: Sistem tasarım süreci: gereksinimden takasa kadar altı adım ve geri besleme.](gorseller/b41_tasarim_sureci.png)

Adımları kısaca açıklayalım. **Gereksinim** adımında iki listeyi yazarsın: işlevsel gereksinimler (sistem ne yapar) ve işlevsel olmayan gereksinimler (ne kadar hızlı, ne kadar sık bozulabilir, ne kadar tutarlı). **Kısıt ve ölçek** adımında kaç kullanıcı, kaç istek, kaç bayt olduğunu sayarsın; bütçe, ekip ve donanım kısıtlarını da buraya yazarsın. **Tahmin** adımında bu sayılardan bant genişliği, depolama ve işlemci yükü hesaplanır. Bu, kaba bir hesaptır ama sistemin hangi boyutta olduğunu söyler. **Üst düzey tasarım** adımında kutuları ve oklara çizersin: istemci, yük dengeleyici, sunucular, önbellek, veritabanı. **Derin dalış** adımında iki üç kritik bileşeni içeriden incelersin. **Darboğaz ve takas** adımında hangi parçanın önce kırılacağını bulur, bunun için neyi feda ettiğini açıkça yazarsın.

Süreç, kötü haberleri erken getirmeye yarar. Tahmin adımı, tek bir veritabanının yazma kapasitesinin sistemin ihtiyacının on katı olduğunu gösterebilir; bunu kod yazıp ancak ölçtüğünde görmek çok daha pahalıdır. Bölüm boyunca bu süreci kullanacağız.

## 41.2 Gereksinimler, SLO'lar ve hata bütçesi

Gereksinimler iki gruba ayrılır. İşlevsel gereksinim, sistemin ne yaptığıdır: "kullanıcı bir URL verir, kısa bir bağlantı alır". İşlevsel olmayan gereksinim, nasıl yaptığıdır ve tasarımı asıl belirleyen odur. Aşağıdaki tablonun her satırı bir karar doğurur.

| Gereksinim | Sorusu | Tipik ölçü | Tasarıma etkisi |
|---|---|---|---|
| Gecikme | Bir istek ne kadar sürede yanıtlanır? | p99, milisaniye | Önbellek, coğrafi dağıtım, eşzamansız iş |
| Verim | Saniyede kaç istek? | istek/s, paket/s | Yatay ölçekleme, toplu işlem |
| Kullanılabilirlik | Sistem ne sıklıkla yanıt veremez? | yüzde (dokuzlar) | Yedeklilik, otomatik geçiş |
| Dayanıklılık | Veri kaybı kabul edilebilir mi? | kayıp sayısı, RPO | Kalıcı günlük, çoğaltma |
| Tutarlılık | Bayat veri görmek kabul edilebilir mi? | okuma-yazma sözleşmesi | Lider-takipçi, quorum (Bölüm 35.8) |
| Maliyet | Ne kadar harcanabilir? | aylık bütçe, kaynak başına | Her şeyin yedeklenmesinin olmadığı kararlar |

### SLI, SLO ve SLA

Bu gereksinimleri ölçülebilir hâle getirmek için üç kavram kullanılır. **SLI** (hizmet seviyesi göstergesi), bir şeyi ölçen niceliktir: "isteklerin yüzde kaçı 300 ms altında yanıtlanıyor?". **SLO** (hizmet seviyesi hedefi), o göstergenin hedef değeridir: "bu oran son 30 günde yüzde 99,9'un üstünde olsun". **SLA** (hizmet seviyesi anlaşması) ise müşteriye verilen sözdür ve ihlal edildiğinde bir ceza ya da tazminat içerir. Mühendis olarak SLO'yla çalışırsın; SLA genellikle iş birimlerinin işidir, ama SLA'yı karşılayabilmek için SLO'nun SLA'dan sıkı tutulması gerekir.

Kullanılabilirlik hedefleri "dokuz" sayısıyla konuşulur: yüzde 99 ya da "iki dokuz", yüzde 99,9 ya da "üç dokuz" gibi. Bu sayının ne anlama geldiğini hesapla görmek gerekir. Yıl 8 760 saattir. Hedef `h` ise izin verilen yıllık kesinti `(1 - h) x 8 760` saattir. Aşağıdaki betik bu hesabı yapar ve 30 günlük pencere için de aynısını yazar.

```python
# -*- coding: utf-8 -*-
"""Bölüm 41.2 - SLO aritmetiği ve bileşen kullanılabilirliği.
Tohum: 41. Çalıştırma: python b41_erisilebilirlik.py
"""

import random

YIL_SAAT = 365 * 24


def kesinti_saat(hedef):
    """Yıllık izin verilen kesinti süresi (saat)."""
    return (1 - hedef) * YIL_SAAT


def metin(dakika):
    """Dakikayı okunur birime çevirir."""
    if dakika >= 60:
        return "%.2f saat" % (dakika / 60)
    if dakika >= 1:
        return "%.2f dakika" % dakika
    return "%.1f saniye" % (dakika * 60)


print("SLO       yıllık kesinti      30 günlük kesinti")
for h in (0.99, 0.999, 0.9995, 0.9999, 0.99999):
    yil = (1 - h) * YIL_SAAT * 60  # dakika
    ay = (1 - h) * 30 * 24 * 60  # dakika
    print("%-9.5f %-19s %s" % (h, metin(yil), metin(ay)))
print("%%99.9 hata bütçesi (30 gün): %.1f dakika"
      % ((1 - 0.999) * 30 * 24 * 60))


# Seri ve paralel bileşenler
```

Betiğin ilk kısmı SLO tablosunu basar; çıktısı şöyle:

```term
$ python b41_erisilebilirlik.py
SLO       yıllık kesinti      30 günlük kesinti
0.99000   87.60 saat          7.20 saat
0.99900   8.76 saat           43.20 dakika
0.99950   4.38 saat           21.60 dakika
0.99990   52.56 dakika        4.32 dakika
0.99999   5.26 dakika         25.9 saniye
%99.9 hata bütçesi (30 gün): 43.2 dakika
```

Sayılar tablosu, dokuzların sertliğini gösteriyor. Yüzde 99,9 kulağa çok yüksek gelmez, ama yılda 8,76 saatlik bir kesinti demektir; bu süre tek bir gece bakım penceresinde bile harcanabilir. Yüzde 99,99 için yıllık pencere 52,56 dakikadır, yani bir kesinti bütün yılın bütçesini bir kez tüketebilir. Bu noktada kavram netleşir: **hata bütçesi**, SLO'nun izin verdiği kötü dakikalardır. Yüzde 99,9'un 30 günlük hata bütçesi 43,2 dakikadır. Bu bütçe bitince yeni özellik yayınlama gibi riskli işler durdurulur ve güvenilirlik işine dönülür. Hata bütçesi fikri, geliştirme hızı ile güvenilirlik arasındaki çatışmayı bir sayıya bağlar; Google'ın SRE uygulamalarında popülerleşmiştir (genel bilgi).

### Seri ve paralel bileşenler

Bir sistem birçok bileşenin birleşimidir ve bileşenlerin nasıl bağlandığı kullanılabilirliği doğrudan belirler. İki temel bağlantı türü vardır.

**Seri** bağlantıda bir istek her bileşenden geçmek zorundadır; biri çalışmazsa sistem çalışmaz. `n` bileşenin kullanılabilirlikleri `A_1, ..., A_n` ise toplam `A = A_1 x A_2 x ... x A_n` olur. Üç bileşen, her biri yüzde 99,9 ise toplam `0,999^3 = 0,997003`, yani yüzde 99,70. Seri bağlantı kullanılabilirliği her zaman en zayıf halkadan daha düşük yapar.

**Paralel** bağlantıda bir kopya çalışması yeterlidir. Her kopyanın çalışmamasının olasılığı `1 - A_i`'dir; bağımsız olduklarını varsayarsak hepsinin birden çalışmaması `Π(1 - A_i)` olur ve toplam `A = 1 - Π(1 - A_i)`. İki kopya, her biri yüzde 99 ise `1 - 0,01^2 = 0,9999`, yani yüzde 99,99. Tek kopyadan iki kat daha az kesinti.

![Şekil 41.2: Seri bağlantıda kullanılabilirlik çarpılır; paralel kopyalarda çarpılan kendi tamamlayıcılarıdır.](gorseller/b41_kullanilabilirlik.png)

Bu formüllerin ardındaki varsayım önemlidir: bileşenler **bağımsız** arıza verir. Gerçekte iki kopya aynı güç hattını, aynı veri merkezi ağını ya da aynı yazılım hatasını paylaşabilir. Bu **ortak neden arızası** (common-mode failure) paralel kazancı hızla eritir. Paralel formülü her zaman iyimser bir üst sınır verir; ortak nedenleri ayrıca düşünmek gerekir.

Formülü bir simülasyonla da doğrulayalım. Aşağıdaki betik iki seri bileşen (`0,999` ve `0,999`) ile iki kopyalı bir bloğu (`0,99` ve `0,99`) birleştirir ve bir milyon deneme yapar. Her denemede bileşenlerin açık olup olmadığını zar atar gibi belirler.

```python
def seri(*a):
    p = 1.0
    for x in a:
        p *= x
    return p


def paralel(*a):
    q = 1.0
    for x in a:
        q *= 1 - x
    return 1 - q


print()
print("seri (0,999 x 3)         = %.6f" % seri(0.999, 0.999, 0.999))
print("paralel (0,99 x 2)       = %.6f" % paralel(0.99, 0.99))
print("paralel (0,99 x 3)       = %.6f" % paralel(0.99, 0.99, 0.99))

# Monte Carlo: anlık görüntü modeli (her bileşen bağımsız açık/kapalı)
rnd = random.Random(41)
```

Bu bloğun çıktısı, seri ve paralel formüllerin sayısal sonucudur:

```term
seri (0,999 x 3)         = 0.997003
paralel (0,99 x 2)       = 0.999900
paralel (0,99 x 3)       = 0.999999
```

```python
N = 1000000


def mc_sistem(olasiliklar_seri, yedek_p, yedek_sayi):
    """Seri zincir: her yazma/okuma adımı bir 'seri' bileşen.
    Yedekli blok: yedek_sayi tane bağımsız kopya, biri açıksa yeter.
    """
    ok = 0
    for _ in range(N):
        tamam = True
        for p in olasiliklar_seri:
            if rnd.random() >= p:
                tamam = False
                break
        if tamam:
            kopya_ok = False
            for _ in range(yedek_sayi):
                if rnd.random() < yedek_p:
                    kopya_ok = True
                    break
            if not kopya_ok:
                tamam = False
        if tamam:
            ok += 1
    return ok / N

if __name__ == "__main__":
    # Örnek: 0,999'luk iki seri bileşen + 0,99'luk 2 kopyalı blok
    teo = seri(0.999, 0.999) * paralel(0.99, 0.99)
    olc = mc_sistem([0.999, 0.999], 0.99, 2)
    print()
    print("iki seri + 2 kopyalı blok")
    print("teorik = %.6f" % teo)
    print("olçülen (1e6 deneme) = %.6f" % olc)
```

Betiğin son kısmı kendi sayısını basar:

```term
iki seri + 2 kopyalı blok
teorik = 0.997901
olçülen (1e6 deneme) = 0.997836
```

Teorik değer `0,997901`, simülasyon `0,997836`. Fark `0,000065`. Bir Bernoulli denemesinde standart hata `sqrt(p(1-p)/N)` ile tahmin edilir: `sqrt(0,997901 x 0,002099 / 1 000 000)` yaklaşık `0,0000458`. Fark, standart hatanın yaklaşık 1,4 katıdır; yani formül ile simülasyon tutarlıdır. Bu, paralel ve seri formüllerin doğru kurulduğunu gösterir. Simülasyonun bir değeri daha var: aynı yapıya ortak neden arızası eklemek istersen, bağımsızlık varsayımını bırakıp bir "tüm sistemi bozan" olayı zarla eklersin ve kullanılabilirliğin ne kadar düştüğünü görürsün.

## 41.3 Kapasite tahmini: kâğıt arkası hesabı

Bir tasarımın büyüklüğünü anlamak için ölçüm yapmadan önce kaba bir hesap yaparsın. Buna **back-of-the-envelope** (zarf arkası) hesabı denir; adı, mühendislerin hesabı bir zarfın arkasına yazmasından gelir. Amaç kesin bir cevap değil, büyüklük mertebesini bulmaktır. "On bin istek mi, on milyon mu?" sorusu, sistemin bir sunucuya mı, bir veri merkezine mi ihtiyacı olduğunu belirler; bu soruya yüzde on hata payıyla cevap vermek yeterlidir.

Hesabın adımları sabittir. Önce kullanıcı sayısını ve kullanıcı başına isteği çarparak günlük toplam isteği bulursun. Bunu saniyeye bölersin; ortalama istek hızı çıkar. Gerçek trafik ortalamanın etrafında dalgalanır, bu yüzden tepe hızı için bir katsayı (çoğu zaman 2 ile 3 arası, varsayım) seçersin. Sonra her isteğin boyutunu ve her isteğin sistemde harcadığı süreyi bilirsen bant genişliğini, depolama ihtiyacını ve gerekli eşzamanlılığı (aynı anda kaç istek işlenmeli) hesaplarsın.

Genel bir şablon örnek alalım: günde 10 milyon etkin kullanıcı, kullanıcı başına günde 20 istek. Günlük toplam 200 milyon istek eder. Gün 86 400 saniye olduğuna göre ortalama hız `200 000 000 / 86 400 = 2 315` istek/saniyedir. Üç kat tepe varsayımıyla tepe hız yaklaşık 6 944 istek/saniyedir. Bu sayının bir sunucuya sığıp sığmadığı, sunucunun bir isteği ne kadar sürede bitirdiğine bağlıdır; bu, 41.6'da Little yasasıyla bağlanacak.

Hesabın doğruluğunu çoğaltan şey, gecikme sayılarını bilmektir. Bölüm 25'te ölçtüğümüz değerler bu bölümün zemini: bu makinede bağımlı yüklerle ölçülen DRAM erişimi 110 ile 130 nanosaniye arasındaydı. Bir NVMe diske yazma için genel bilgi olarak yaklaşık 100 mikrosaniye, aynı veri merkezi içinde bir ağ turu için yaklaşık 0,5 milisaniye kullanılır. Bu sayıları ezberlemen gerekmez; önemli olan büyüklük mertebesidir: bellek yüz nanosaniye, disk yüz mikrosaniye, ağ yarım milisaniye. Aradaki fark üç ile dört kat katsayı farkıdır ve bu fark mimariyi değiştirir.

Şimdi bir İHA filosunun telemetrisini hesaplayalım. Varsayımlarımız şöyle: 40 İHA, her biri saniyede 100 paket, her paket 256 bayt (başlık, ölçümler ve sağlama toplamı) ve sıkıştırma oranı 5:1. Bu varsayımlar bir sistem tasarımcısının yaptığı ilk tahmindir; gerçek değerler sensör sayısı ve donanıma göre değişir. Betik adım adım hesabı yapar ve her satırda birimi yazar.

```python
# -*- coding: utf-8 -*-
"""Bölüm 41.3 - Kapasite tahmini (back-of-the-envelope).
Varsayımlar metinde açıkça yazılmıştır. Ölçüm değil, hesaptır.
"""

# --- 1) Genel şablon: kullanıcı tabanlı istek tahmini ---------------
kullanici_gun = 10_000_000  # günlük aktif kullanıcı (varsayım)
istek_kullanici_gun = 20  # kullanıcı başına günlük istek
gun_saniye = 86400
ortalama = kullanici_gun * istek_kullanici_gun / gun_saniye
tepe_katsayi = 3  # ortalamanın kaç katı tepe (varsayım)
print("Ortalama istek/s : %.0f" % ortalama)
print("Tepe istek/s     : %.0f" % (ortalama * tepe_katsayi))
```

```python
# --- 2) İHA filosu telemetrisi -------------------------------------
ARAC = 40  # filodaki İHA sayısı (varsayım)
HZ = 100  # her araçtan saniyede paket
PAKET = 256  # bayt: başlık + ölçümler + CRC (varsayım)
SIKISMA = 5  # ham/sıkıştırılmış oran (varsayım: 5:1)

paket_s = ARAC * HZ
bayt_s = paket_s * PAKET
print()
print("İHA filosu telemetrisi")
print("Paket/s (filo)        : %d" % paket_s)
print(
    "Ham bayt/s            : %d (%.3f MB/s)" % (bayt_s, bayt_s / 1e6)
)
print("Ham bit/s             : %.2f Mbit/s" % (bayt_s * 8 / 1e6))
print("Tepe (2x) bit/s       : %.2f Mbit/s" % (2 * bayt_s * 8 / 1e6))
gun_ham = bayt_s * gun_saniye
print("Ham depolama / gün    : %.1f GB" % (gun_ham / 1e9))
print("Sıkıştırılmış / gün   : %.1f GB" % (gun_ham / SIKISMA / 1e9))
print(
    "Sıkıştırılmış / yıl   : %.1f TB"
    % (gun_ham / SIKISMA * 365 / 1e12)
)
print(
    "Tek bir paket başına  : %.1f us (4000 paket/s için pay)"
    % (1e6 / paket_s)
)
```

```python
# --- 3) Gecikme bütçesi (Bölüm 25 ve 35 sayıları) -------------------
DRAM_NS = 120  # Bölüm 25.4 ölçümü, 110-130 ns
NVME_US = 100  # genel bilgi
AG_MS = 0.5  # genel bilgi, aynı veri merkezi
print()
print("Bir paketin yol üzerindeki kabaca maliyeti:")
print("  bellek (DRAM)       : %d ns" % DRAM_NS)
print("  NVMe diske yazma    : %d us" % NVME_US)
print("  ağ turu (aynı DC)   : %.1f ms" % AG_MS)
print(
    "Tek bağlantıda sıralı (her paket bir tur) en fazla: %d paket/s"
    % (1000 / AG_MS)
)
print(
    "Filo gereksinimi                        : %d paket/s" % paket_s
)
print(
    "Bağlantı sayısı (en az, tur başına)     : %d"
    % (paket_s / (1000 / AG_MS))
)
```

Betiğin çıktısı şöyle:

```term
$ python b41_kapasite.py
Ortalama istek/s : 2315
Tepe istek/s     : 6944

İHA filosu telemetrisi
Paket/s (filo)        : 4000
Ham bayt/s            : 1024000 (1.024 MB/s)
Ham bit/s             : 8.19 Mbit/s
Tepe (2x) bit/s       : 16.38 Mbit/s
Ham depolama / gün    : 88.5 GB
Sıkıştırılmış / gün   : 17.7 GB
Sıkıştırılmış / yıl   : 6.5 TB
Tek bir paket başına  : 250.0 us (4000 paket/s için pay)

Bir paketin yol üzerindeki kabaca maliyeti:
  bellek (DRAM)       : 120 ns
  NVMe diske yazma    : 100 us
  ağ turu (aynı DC)   : 0.5 ms
Tek bağlantıda sıralı (her paket bir tur) en fazla: 2000 paket/s
Filo gereksinimi                        : 4000 paket/s
Bağlantı sayısı (en az, tur başına)     : 2
```

Sonuçları okumak için bir ayrıntıya dikkat et. Filo saniyede 4 000 paket üretiyor. Her paket 256 bayt olduğundan ham veri 1,024 MB/s eder; bu 8,19 Mbit/s demektir. Tepe için iki katını alırsan 16,38 Mbit/s. Bant genişliği tek başına büyük bir sorun değildir; asıl sorun, paketlerin ayrı ağ turlarıyla gönderilmesidir. Tek bir bağlantıda her paket bir tur sürerse, 0,5 milisaniyelik turla saniyede en fazla 2 000 paket gönderebilirsin. Filonun ihtiyacı 4 000 olduğu için en az iki paralel bağlantı, ya da paketleri toplu gönderme gerekir. Kaba hesabın bize verdiği kararı budur: ya bağlantı sayısını artır ya da paketleri gruplayarak tur sayısını düşür.

Depolama tarafı da aynı disiplinle hesaplanır. Ham veri günde yaklaşık 88,5 GB eder; beş kat sıkıştırmayla 17,7 GB, bir yılda yaklaşık 6,5 TB. Bu, bir yer istasyonu için yönetilebilir bir boyuttur, ama bir yıllık ham kaydı sınırsız tutmak yerine saklama süresi koymak gerekir. Saklama politikası 41.10'da zaman serisi deposuyla birlikte ele alınacak.

Tablo, hesabın tamamını tek bakışta gösterir.

![Şekil 41.3: İHA filosu telemetrisi için kapasite tahmin tablosu. Her satır bir öncekinden hesaplanır.](gorseller/b41_kapasite_tablo.png)

Son satır, bir sonraki bölümün başlangıcıdır: paket başına düşen süre bütçesi 250 mikrosaniyedir. Tek bir işlemcinin her paketi bu süre içinde ayrıştırıp kaydetmesi gerekir. Python ile bunu yapabilir miyiz? Bu, ölçmeden cevaplanamaz; Bölüm 31'de ölçtüğün gibi bir yük testiyle sınanmalıdır.

## 41.4 Ölçekleme: dikey, yatay ve durumsuz servisler

Sistem büyüdüğünde kapasiteyi artırmanın iki yolu vardır. **Dikey ölçekleme** (scale up), aynı makineyi daha güçlüsüyle değiştirmektir: daha fazla çekirdek, daha fazla bellek. Basittir; kod değişmez, ağ topolojisi değişmez. Ama bir tavanı vardır: en büyük makine bile sınırlıdır, fiyatı doğrusal değil üssel artar ve makine çökerse tüm sistem çöker. **Yatay ölçekleme** (scale out), aynı görevi yapan birçok makine çalıştırmaktır. Tavanı çok daha yüksektir ve bir makinenin çökmesi sistemin yalnızca bir parçasını etkiler. Bedeli, bu makinelerin birbirinden haberdar olmasını ve trafiği aralarında bölmeyi gerektirmesidir.

Yatay ölçeklemenin ön koşulu **durumsuz** (stateless) servislerdir. Bir sunucu, bir isteği işlerken kendi belleğinde kullanıcıya ait bir durum tutmuyorsa, istek hangi kopyaya giderse gitsin aynı yanıt verilir. Oturum bilgisi istemcinin üzerinde (imzalı bir belirteç gibi) ya da ortak bir depoda (Bölüm 35'teki Redis tipi bir sistem) tutulursa servis durumsuz kalır. Durum sunucunun belleğindeyse, aynı kullanıcının sonraki isteği başka bir kopyaya giderse oturum kaybolur. Bu yüzden yatay ölçeklemeye geçmeden önce durumun nerede yaşadığını bilmek gerekir.

Yük, bir **yük dengeleyici** (load balancer) tarafından kopyalara dağıtılır. Dengeleyiciler iki katmanda çalışabilir (genel bilgi). **L4** dengeleyici TCP bağlantılarını yönlendirir; paketin içeriğine bakmaz, bu yüzden hızlı ve ucuzdur. **L7** dengeleyici HTTP isteğini okur; yola, başlığa ya da çerezlere göre karar verebilir, TLS'i sonlandırabilir, ama her isteği daha fazla işler. Hangi katmanın seçileceği, kuralların ne kadar zengin olması gerektiğine bağlıdır.

Dengeleyici, bir sunucunun sağlıklı olup olmadığını **sağlık kontrolü** ile anlar. Aktif kontroller, dengeleyicinin belirli aralıklarla bir uç noktayı yoklamasıdır. Pasif kontroller, gerçek trafikteki hataları sayar. İki kavramı ayırmak önemlidir: "canlı" (process çalışıyor) ile "hazır" (yeni isteği alabilir, veritabanına bağlantısı var). Canlı ama hazır olmayan bir sunucuya trafik göndermek, kullanıcıyı hata sayfasıyla karşılar. Bir de sinsi bir durum vardır: sağlık kontrolü "200 OK" döner ama her isteği on saniyede yanıtlar. Bu nedenle gecikmeyi de ölçen ve yavaş kopyaları dışarıda bırakan kontroller gerekir.

Yatay ölçekleme bir darboğazı çözer, ama onu ortadan kaldırmaz; başka yere taşır. Kopya sayısını artırdığında darboğaz çoğu zaman paylaşılan veritabanına geçer. Bu yüzden ölçekleme kararı her zaman "hangi bileşen şimdi kırılacak?" sorusuyla birlikte verilir.

## 41.5 Yük dengeleme algoritmaları ve iki seçimin gücü

Dengeleyicinin her gelen isteği bir sunucuya yönlendirmek için bir **politikası** vardır. En yaygın olanları şunlardır.

**Round robin (sırayla)** istekleri sırayla dağıtır: 1., 2., 3. sunucu, sonra başa döner. Uygulaması en basittir ve kopyalar aynıysa iyi çalışır. Ama sunucular farklı hızdaysa yavaş olan bir sunucuya da eşit pay gider.

**Ağırlıklı round robin** her sunucuya bir ağırlık verir ve payı ağırlıkla orantılı dağıtır. Hızları bilinen bir kümede round robin'in eksiğini kapatır.

**En az bağlantı (least connections)** en az sayıda açık isteği olan sunucuya gönderir. Hızı bilmeden de adil davranır: yavaş bir sunucuda istekler birikir ve sayısı artar, dengeleyici de ona daha az gönderir.

**Tutarlı hash** (consistent hashing), isteğin bir anahtarına (örneğin kullanıcı kimliği) göre sunucu seçer. Bölüm 35.7'de gördüğümüz halka yapısı, bir sunucu eklendiğinde yalnızca az sayıda anahtarın yer değiştirmesini sağlar. Yük dengeleme açısından bu politika, aynı anahtarın hep aynı sunucuya gitmesini sağlayarak sunucu tarafı önbelleğin isabet oranını artırır. Ama anahtarlar düzgün dağılmışsa, yük dağılımı rastgele seçime benzer; hız ya da anlık yük bilgisi kullanmaz.

**İki seçimin gücü** (power of two choices), en az bağlantı politikasının ucuz bir versiyonudur. Her istekte tüm sunucuları taramak yerine **rastgele iki** sunucu seçilir ve kuyruğu kısa olan alınır. Bu basit fikir, rastgele seçimin kuyruklarındaki dengesizliği dramatik biçimde azaltır. Mitzenmacher'ın 2001 tarihli analizi bunu gösterdi (genel bilgi): `n` sunucuya rastgele dağıtımda en uzun kuyruk yaklaşık `log n / log log n` büyürken, iki seçimle `log log n / log 2` mertebesinde kalır.

Bu sonuçları kendi gözümüzle görmek için bir ayrık olay simülatörü yazalım. Model şöyledir. İstekler Poisson sürecine göre gelir (saniyede `lambda` tane, aralar üssel dağılımlı). Her istek ortalama bir birim iş taşır; `mu_i` hızlı bir sunucu bu işi `iş / mu_i` sürede bitirir. Her sunucu FIFO kuyruğa sahiptir. Yönlendirme, istek geldiği anda yapılır. Betik altı politikayı karşılaştırır: sırayla (`rr`), ağırlıklı (`wrr`), rastgele, en az bağlantı (`enaz`), iki seçim (`pot`) ve bir de referans olarak en erken bitiş (`erken`). Son politika, her sunucunun ne zaman boşalacağını bildiği ideal bir durumdur; gerçek bir dengeleyici bunu genellikle bilmez ama karşılaştırma için faydalıdır.

Simülatörün veri yapısı şöyledir: her sunucunun bir `deque`'si, içinde o sunucudaki işlerin tamamlanma zamanları vardır. Bir sunucunun kuyruk uzunluğu, `now`'dan büyük tamamlanma zamanlarının sayısıdır. Kuyruğu saymak için baştan eski zamanları atmak yeterlidir; bu, her sunucu için amortize sabit zamanlıdır.

```python
# -*- coding: utf-8 -*-
"""Bölüm 41.4 - Yük dengeleme stratejileri: ayrık olay simülasyonu.

Model: istekler Poisson süreciyle gelir (oran lambda). Her istek
ortalama 1 birimlik iş taşır; i. sunucu hızı mu_i ile işler, yani
hizmet süresi iş/mu_i. Her sunucu FIFO kuyruğa sahiptir. Yönlendirme,
istek geldiği anda yapılır (dağıtım sonradan değişmez).
Tohum: 41. Çıktılar: engine/veri/b41_yuk_dengeleme.csv,
engine/veri/b41_pot.csv
"""

import csv
import random
from collections import deque

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ISTEK = 100000
```

```python
def simule(mus, lam, politika, rnd, istek=ISTEK):
    n = len(mus)
    deq = [
        deque() for _ in range(n)
    ]  # sunucudaki tamamlanma zamanları
    serbest = [0.0] * n  # FIFO'da son işin bitişi
    agirlik = [int(m * 2) for m in mus]  # WRR için tamsayı ağırlık
    cur = [0] * n
    toplam_w = sum(agirlik)
    rr = 0
    t = 0.0
    gecikmeler = []
    enb_kuyruk = 0

    def kuyruk(i, now):
        dq = deq[i]
        while dq and dq[0] <= now:
            dq.popleft()
        return len(dq)
```

Bir sonraki blok, politikaların her biri için yönlendirme kararını verir. Dikkat et: `rr` ve `rastgele` hızı hiç görmez; `wrr` hızı ağırlık olarak kullanır; `enaz` yalnızca kuyruk uzunluğuna bakar; `pot` bu bilginin rastgele iki örneğine bakar; `erken` ise sunucunun ne zaman boşalacağını bilir.

```python
    for _ in range(istek):
        t += rnd.expovariate(lam)
        if politika == "rr":
            i = rr
            rr = (rr + 1) % n
        elif politika == "wrr":
            for j in range(n):
                cur[j] += agirlik[j]
            i = max(range(n), key=lambda j: cur[j])
            cur[i] -= toplam_w
        elif politika == "rastgele":
            i = rnd.randrange(n)
        elif politika == "enaz":
            i = min(range(n), key=lambda j: (kuyruk(j, t), j))
        elif politika == "pot":
            a, b = rnd.sample(range(n), 2)
            i = a if kuyruk(a, t) <= kuyruk(b, t) else b
        elif politika == "erken":
            i = min(range(n), key=lambda j: (max(t, serbest[j]), j))
        else:
            raise ValueError(politika)

        for j in range(n):
            kj = kuyruk(j, t)
            if kj > enb_kuyruk:
                enb_kuyruk = kj

        boyut = rnd.expovariate(1.0)
        baslangic = max(t, serbest[i])
        bitis = baslangic + boyut / mus[i]
        serbest[i] = bitis
        deq[i].append(bitis)
        gecikmeler.append(bitis - t)
```

Bu blokta istek, seçilen sunucunun FIFO kuyruğunun sonuna eklenir. Gecikme, tamamlanma zamanı ile varış zamanı arasındaki farktır ve yüzdelikler (p50, p99) sıralanmış gecikme listesinden alınır.

```python
    gecikmeler.sort()
    p = lambda q: gecikmeler[int(q * (len(gecikmeler) - 1))]
    ort = sum(gecikmeler) / len(gecikmeler)
    return ort, p(0.5), p(0.99), enb_kuyruk

POLITIKALAR = ["rr", "wrr", "rastgele", "enaz", "pot", "erken"]
```

Ana blok, heterojen bir küme kurar: dört sunucu hızı 1, iki sunucu hızı 2 ve iki sunucu hızı 0,5. Toplam hız 9'dur. Yük oranı `rho`, `lambda / toplam hız` olarak tanımlanır; `rho = 0,8` demek sistemin toplam kapasitesinin yüzde 80'inin kullanıldığı anlamına gelir. Sonra aynı yük ile iki sonuç üretilir: heterojen kümenin tablosu ve 100 sunucuda rastgele ile iki seçimin karşılaştırması.

```python
if __name__ == "__main__":
    # 1) Heterojen küme: 4 x hız 1, 2 x hız 2, 2 x hız 0,5
    mus = [1.0] * 4 + [2.0] * 2 + [0.5] * 2
    toplam_mu = sum(mus)
    satirlar = []
    print(
        "Heterojen küme, toplam hız = %.1f, istek = %d"
        % (toplam_mu, ISTEK)
    )
    print("rho  politika   ort     p50     p99     maks_kuyruk")
    for rho in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        for pol in POLITIKALAR:
            rnd = random.Random(41)
            lam = rho * toplam_mu
            ort, p50, p99, mk = simule(mus, lam, pol, rnd)
            print(
                "%.2f %-10s %7.3f %7.3f %8.3f %6d"
                % (rho, pol, ort, p50, p99, mk)
            )
            satirlar.append(
                [
                    rho,
                    pol,
                    "%.5f" % ort,
                    "%.5f" % p50,
                    "%.5f" % p99,
                    mk,
                ]
            )
    with open(
        VERI + "/b41_yuk_dengeleme.csv",
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        w = csv.writer(f)
        w.writerow(["rho", "politika", "ort", "p50", "p99", "maks_k"])
        w.writerows(satirlar)
```

```python
    # 2) Homojen 100 sunucu: iki seçimin gücü
    print()
    print("Homojen 100 sunucu, rho = 0,9, istek = %d" % 30000)
    print("politika   maks_kuyruk  p99")
    satirlar = []
    for pol in ("rastgele", "pot"):
        rnd = random.Random(41)
        ort, p50, p99, mk = simule(
            [1.0] * 100, 90.0, pol, rnd, istek=30000
        )
        print("%-10s %11d  %.3f" % (pol, mk, p99))
        satirlar.append([pol, mk, "%.5f" % p99])
    with open(
        VERI + "/b41_pot.csv", "w", encoding="utf-8", newline=""
    ) as f:
        w = csv.writer(f)
        w.writerow(["politika", "maks_k", "p99"])
        w.writerows(satirlar)
```

Betik 100 000 istekle her çalıştırmayı yapar, tohum 41 sabittir. Tam çıktı şöyle:

```term
$ python b41_yuk_dengeleme.py
Heterojen küme, toplam hız = 9.0, istek = 100000
rho  politika   ort     p50     p99     maks_kuyruk
0.20 rr           1.271   0.705    8.247      9
0.20 wrr          0.919   0.555    5.422      4
0.20 rastgele     1.679   0.878   11.498     13
0.20 enaz         0.966   0.656    4.585      2
0.20 pot          1.151   0.678    6.806      3
0.20 erken        0.966   0.656    4.581      2
0.30 rr           1.655   0.789   12.605     15
0.30 wrr          0.973   0.591    5.740      6
0.30 rastgele     2.392   1.063   19.050     21
0.30 enaz         0.942   0.624    4.674      2
0.30 pot          1.219   0.715    7.235      4
0.30 erken        0.940   0.623    4.668      3
0.40 rr           3.515   0.964   33.536     33
0.40 wrr          1.065   0.650    6.307      9
0.40 rastgele     5.687   1.358   62.434     56
0.40 enaz         0.941   0.608    4.869      3
0.40 pot          1.335   0.776    8.010      5
0.40 erken        0.930   0.604    4.807      4
0.50 rr         353.617   1.199 2667.785   1422
0.50 wrr          1.211   0.739    7.062     12
0.50 rastgele   326.288   1.794 2440.775   1298
0.50 enaz         0.972   0.613    5.160      3
0.50 pot          1.501   0.877    9.137      6
0.50 erken        0.939   0.599    4.996      5
```

Çıktının devamı, aynı çalıştırmanın ikinci yarısıdır: yük oranlarının geri kalanı ve 100 sunucu karşılaştırması.

```term
0.60 rr         815.785   1.466 6153.574   3236
0.60 wrr          1.444   0.885    8.351     16
0.60 rastgele   785.722   2.352 5998.410   3188
0.60 enaz         1.035   0.646    5.645      4
0.60 pot          1.732   1.020   10.105      7
0.60 erken        0.963   0.622    5.189      7
0.70 rr         1146.275   2.049 8677.465   4596
0.70 wrr          1.849   1.137   10.610     20
0.70 rastgele   1114.819   3.464 8544.363   4568
0.70 enaz         1.161   0.717    6.280      5
0.70 pot          2.143   1.273   12.365     10
0.70 erken        1.023   0.685    5.390     10
0.80 rr         1395.350   4.006 10590.392   5604
0.80 wrr          2.658   1.644   15.263     26
0.80 rastgele   1363.721   7.142 10459.973   5567
0.80 enaz         1.403   0.880    7.613      7
0.80 pot          2.903   1.785   15.699     13
0.80 erken        1.178   0.837    5.707     13
0.90 rr         1648.856 137.822 12070.875   6377
0.90 wrr          5.059   3.139   28.168     34
0.90 rastgele   1617.452 101.999 11936.254   6330
0.90 enaz         2.053   1.336   10.859      9
0.90 pot          5.008   3.235   25.558     21
0.90 erken        1.713   1.298    6.961     20

Homojen 100 sunucu, rho = 0,9, istek = 30000
politika   maks_kuyruk  p99
rastgele            50  41.925
pot                  7  8.718
```

Çıktıyı okumanın yolu, önce bir kararsızlık ölçütünü anlamaktır. Heterojen kümede sırayla ve rastgele politikalar hızı hiç görmediği için hız 0,5 olan iki sunucuya toplam yükün sekizde birini gönderir. Bu sunucuların kapasitesi 0,5 olduğundan, yük oranı bu sunucular için `(9 x rho / 8) / 0,5 = 2,25 rho` olur. Bu 1'den büyükse kuyruk sonsuza kadar büyür. Yani `rho` 0,444'ün üstünde olduğunda bu iki politika kararsızdır. Tabloda `rho = 0,5`'ten itibaren p99 değerinin birkaç bin birim iş olması, ve maksimum kuyruğun birkaç bin olması bunun sonucudur. Kararsız bir sistemde "ortalama gecikme" bir anlam taşımaz; simülasyon uzadıkça büyür. Bu yüzden bu iki politikanın ortalamasını değil, kararsızlık sınırını okumalısın.

Kararlı bölgede (`rho = 0,8`) fark belirgindir. Sırayla politikanın p99'u 10 590, rastgelenin 10 460 birim iş. En az bağlantı 7,6, en erken bitiş 5,7, ağırlıklı 15,3, iki seçim 15,7 birim iş. Ağırlıklı politika hız bilgisini kullanır ve kararlıdır, ama en az bağlantı ondan iyidir: kuyruk uzunluğu zaten yavaş sunucuda birikir, dolayısıyla kuyruk sayısı hızın dolaylı bir ölçüsüdür. İki seçim, en az bağlantının tam bilgisine sahip olmadığı için biraz geride kalır; ama her istekte tüm sunucuları taramadığı için çok daha ucuzdur.

![Şekil 41.4: Sol: heterojen kümede yük oranına göre p99 gecikmesi (log ölçek). Sağ: 100 sunucuda rastgele ile iki seçimin en uzun kuyruğu.](gorseller/b41_yuk_dengeleme.png)

Şekil 41.4 sağ paneli iki seçimin gücünü gösterir. Aynı 100 sunucuya, `rho = 0,9` yükle, 30 000 istek gönderildiğinde rastgele dağıtımda en uzun kuyruk 50, iki seçimde 7 oldu. p99 gecikmesi 41,9'dan 8,7'ye düştü. İki rastgele örnekten kısa olanı seçmek, tüm kuyrukların dengesizliğini çok büyük ölçüde kırıyor. Bu, Bölüm 41'in en ucuz ve en değerli derslerinden biridir: tam bilgi yerine küçük bir örnekleme, çoğu zaman yeterli ve çok ucuzdur.

Bu simülasyonun bilinçli sınırları var. Ağ gecikmesi, bağlantı kurulumu ve istemci davranışı modelde yok. Sunucu yükü gelen isteklerden etkilenmez; oysa gerçekte yavaşlayan bir sunucu dengeleyiciye geri bildirim verir. Ayrıca her politikanın mutlak gecikme değerleri birim iş cinsindendir ve gerçek milisaniyelere çevrilemez. Ölçtüğümüz şey politikalar arasındaki yön ve sıralamadır. Gerçek bir dengeleyici için bu sıralamayı bir yük testiyle doğrulamak gerekir.

## 41.6 Kuyruk teorisi: Little yasası ve M/M/1

Yük dengeleme simülasyonunda gördün: `rho` yaklaşık 0,9'a geldiğinde gecikme patlamaya başlıyordu. Bu olguyu genel bir dile koymak için kuyruk teorisine ihtiyacın var. Kuyruk teorisi, bir hizmetin (sunucu, kasa, ağ kapısı) gelen işleri ne kadar sürede bitirdiğini matematiksel olarak anlatır. Sistem tasarımcısı için bu, kapasite planının kalbidir.

En önemli tek formül **Little yasası**dır: kararlı bir sistemde sistemdeki ortalama iş sayısı `L`, varış hızı `lambda` ile ortalama sistem süresi `W` arasında `L = lambda x W` ilişkisi vardır. Yasanın güzel yanı, varışların nasıl dağıldığına ve hizmetin nasıl çalıştığına bağlı olmamasıdır; her kararlı sistemde geçerlidir (genel bilgi). Örneğin saniyede 100 istek gelen ve her biri ortalama 0,2 saniye süren bir hizmette, herhangi bir anda ortalama `100 x 0,2 = 20` istek işleniyor olur. Bu sayı, bir sunucunun kaç iş parçacığına ya da bağlantıya ihtiyacı olduğunu doğrudan verir. Kapasite tahmininde (41.3) eksik kalan halka buydu.

Little yasası, tek bir kuyruk için bir kuralı açıklamaz: kuyruk hangi hızda boşalır? Bunun için en basit model **M/M/1** kuyruğudur. Bu isim üç şeyi söyler: varışlar Poisson sürecidir (ilk M, Markov özelliği: geçmişten bağımsız, Poisson süreciyle rastgele varışlar), hizmet süreleri üssel dağılımlıdır (ikinci M), ve tek bir sunucu vardır (1). Model, FIFO sırasına göre çalışır. Gerçek sistemlerin çoğu bu modele tam uymaz, ama modelin formülleri hızlı bir kapasite sezgisi verir.

M/M/1 için üç formül yeterlidir. `mu` hizmet hızı, `rho = lambda / mu` kullanım oranı olmak üzere:

- Sistemdeki ortalama süre (bekleme artı hizmet): `W = 1 / (mu - lambda)`.
- Sistemdeki ortalama iş sayısı: `L = rho / (1 - rho)`.
- Kararlılık koşulu: `rho < 1`. Bu koşul sağlanmazsa kuyruk sonsuz büyür.

Bu formüllerde `W`'nin payda `1 - rho` ile orantılı olduğuna dikkat et. `rho` 0,5 iken `W` hizmet süresinin 2 katıdır; `rho` 0,8'de 5 katı; 0,9'da 10 katı; 0,99'da 100 katı. Son satır, neden "yüzde yüz kullanımda çalışmayız" sözünün bir mühendislik gerçeği olduğunu gösteriyor: sunucunun son yüzde birlik kapasitesi, gecikmeyi iki kat artırmak yerine yüz kat artırır. Kapasite planlamasında hedef kullanım oranı için sık görülen bir aralık yüzde 60-75'tir (genel bir kural; kesin değer sisteme bağlıdır).

Formülü bir simülasyonla da doğrulayalım. Simülasyonda her işin varış aralığını ve hizmet süresini üssel dağılımla üretiriz. İşin bekleme süresini **Lindley yinelemesi** ile hesaplarız: bir işin beklemesi, önceki işin beklemesi artı önceki işin hizmet süresi eksi bu işin varış aralığıdır; sonuç negatif olursa sıfıra kırpılır:

`bekleme_k = max(0, bekleme_(k-1) + hizmet_(k-1) - aralik_k)`

Bu yineleme, kuyruğu tek tek işlemeden hızla hesaplar. Ortalama sistemdeki iş sayısını ise iki yoldan ölçeriz: işlerin sistemdeki sürelerinin ortalamasıyla (`W`) ve zaman boyunca sistemdeki iş sayısının integraliyle (`L`). Little yasasının bu iki ölçümü birbirine bağladığını görmek, simülasyonun tutarlılık testidir.

```python
# -*- coding: utf-8 -*-
"""Bölüm 41.5 - M/M/1 kuyruğu: gecikme-kullanım eğrisi.

Model: varış süreci Poisson (oran lambda), hizmet süresi üssel
(oran mu = 1). rho = lambda / mu. Teorik ortalama sistemdeki süre
W = 1 / (mu - lambda), ortalama sistemdeki iş sayısı L = rho/(1-rho).
Ölçüm: Lindley yinelemesi  bekleme_{k+1} = max(0, bekleme_k + hizmet_k
- aralik_{k+1}). L doğrudan zaman integraliyle ölçülür (Little'ın
L = lambda W eşitliğini ayrıca kontrol etmek için).
Tohum: 41 (numpy default_rng). Çıktı: engine/veri/b41_mm1.csv
"""

import csv
import sys

import numpy as np

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ISINMA = 20000  # ilk örnekler atılır (kararlı duruma yaklaşmak için)


def mm1(rho, n, rng):
    lam = rho
    aralik = rng.exponential(1.0 / lam, n)
    hizmet = rng.exponential(1.0, n)
    bekleme = np.empty(n)
    bekleme[0] = 0.0
    b = 0.0
    for k in range(1, n):  # Lindley: sıralı, vektörleşmez
        b = max(0.0, b + hizmet[k - 1] - aralik[k])
        bekleme[k] = b
    varis = np.cumsum(aralik)
    ayrilma = varis + bekleme + hizmet
    sistemde = ayrilma - varis
    return bekleme, varis, ayrilma, sistemde
```

```python
def L_olc(varis, ayrilma):
    """Zaman integrali: sistemdeki iş sayısının ortalaması."""
    olaylar = np.concatenate([varis, ayrilma])
    deger = np.concatenate(
        [np.ones_like(varis), -np.ones_like(varis)]
    )
    sira = np.argsort(olaylar, kind="stable")
    olaylar = olaylar[sira]
    deger = deger[sira]
    sayi = np.cumsum(deger)[:-1]
    dt = np.diff(olaylar)
    toplam = olaylar[-1] - olaylar[0]
    return float(np.sum(sayi * dt) / toplam)
```

Bu fonksiyon, sistemdeki iş sayısının zaman ortalamasını ölçer. Olayları (varış `+1`, ayrılış `-1`) zamana göre sıralar ve her aralıkta sayıyı o aralığın süresiyle çarpıp toplar. Toplamı toplam süreye böler.

```python
if __name__ == "__main__":
    print(
        "rho   W_teorik   W_olculen   L_teorik  L_olculen  lambda_W"
    )
    satirlar = []
    for rho, n in (
        (0.5, 2000000),
        (0.8, 2000000),
        (0.9, 2000000),
        (0.99, 6000000),
    ):
        rng = np.random.default_rng(41)
        bekleme, varis, ayrilma, sistemde = mm1(rho, n, rng)
        s = sistemde[ISINMA:]
        w_teo = 1.0 / (1.0 - rho)
        l_teo = rho / (1.0 - rho)
        w_olc = float(np.mean(s))
        l_olc = L_olc(varis[ISINMA:], ayrilma[ISINMA:])
        print(
            "%.2f %10.3f %11.3f %10.3f %10.3f %9.3f"
            % (rho, w_teo, w_olc, l_teo, l_olc, rho * w_olc)
        )
        satirlar.append(
            [
                rho,
                n,
                "%.6f" % w_teo,
                "%.6f" % w_olc,
                "%.6f" % l_teo,
                "%.6f" % l_olc,
            ]
        )
```

Ana blok dört kullanım oranı için çalışır: 0,5, 0,8, 0,9 ve 0,99. Son değer daha uzun bir simülasyon gerektirir, çünkü kararlı duruma yakınsaması yavaştır. Her çalıştırmadan önce ilk 20 000 iş atılır (ısınma). Çıktı:

```term
$ python b41_mm1.py
rho   W_teorik   W_olculen   L_teorik  L_olculen  lambda_W
0.50      2.000       1.998      1.000      0.999     0.999
0.80      5.000       5.006      4.000      4.005     4.005
0.90     10.000      10.108      9.000      9.097     9.097
0.99    100.000      99.251     99.000     98.230    98.259
```

Tablo, formülle simülasyonun ne kadar uyumlu olduğunu gösteriyor. `rho = 0,5`'te teorik `W = 2,000`, ölçülen `1,998`; `0,8`'de `5,000` ve `5,006`; `0,9`'da `10,000` ve `10,108`. Little yasasının sütunları da tutarlı: `lambda x W` değerleri ölçülen `L` ile neredeyse aynı (`0,999`, `4,005`, `9,097`). `rho = 0,99`'da ölçülen `W` 99,25 ve teorik 100. Sapma yüzde 0,75 kadar. Bunu bir hata olarak değil, belirsizlik olarak okumalısın: `rho` yaklaştıkça kararlı duruma yakınsama yavaşlar ve bir ölçümün güvenilirliği için farklı tohumlarla tekrar yapmak gerekir. Bu bölümde yalnızca tek bir tohum (41) kullandık ve bunu dürüstçe belirtiyoruz.

Betik sonuçları ayrıca bir CSV dosyasına yazar; Şekil 41.5 bu dosyadan çizilir. Son iki blok, dosyayı yazan kısım ve iz modunu (`iz` argümanıyla) çalıştıran kısımdır:

```python
    with open(
        VERI + "/b41_mm1.csv", "w", encoding="utf-8", newline=""
    ) as f:
        wr = csv.writer(f)
        wr.writerow(
            [
                "rho",
                "n",
                "w_teorik",
                "w_olculen",
                "l_teorik",
                "l_olculen",
            ]
        )
        wr.writerows(satirlar)
```

```python
    if len(sys.argv) > 1 and sys.argv[1] == "iz":
        rng = np.random.default_rng(41)
        b, v, a, sis = mm1(0.8, 10, rng)
        print()
        print("rho = 0,8 ilk 6 iş (iz)")
        print("is  varis    bekleme  ayrilma     sistemde")
        for k in range(6):
            print(
                "%-3d %7.3f  %7.3f  %10.3f  %8.3f"
                % (k + 1, v[k], b[k], a[k], sis[k])
            )
```

Bir de bir işin tam izini görelim. Aşağıdaki çıktı `rho = 0,8` için ilk altı işi gösteriyor; `ayrilma` sütunu işin sistemden çıktığı zamandır.

```term
$ python b41_mm1.py iz
rho = 0,8 ilk 6 iş (iz)
is  varis    bekleme  ayrilma     sistemde
1     6.028    0.000       6.132     0.104
2     6.467    0.000       6.772     0.305
3     7.062    0.000       8.335     1.273
4     7.866    0.469      11.707     3.841
5     8.002    3.706      13.570     5.568
6    11.266    2.303      13.617     2.351
```

Dördüncü işin satırını elle kontrol edelim: işi, önceki işin (3. iş) ayrılışı olan `8,335` zamanında bitene kadar bekler; varışı `7,866` olduğundan beklemesi `8,335 - 7,866 = 0,469`'dur. Çıktıdaki değer tam olarak budur. Bu, Lindley yinelemesinin doğru kurulduğunun el ile kanıtıdır.

![Şekil 41.5: M/M/1 kuyruğunda kullanım oranına göre ortalama süre. Çizgi teorik değer, noktalar simülasyon.](gorseller/b41_mm1_egri.png)

Şekil 41.5 aynı bilgiyi eğri olarak verir ve gecikme patlamasını görünür kılar. Eksen logaritmik: `rho` 0,5'ten 0,9'a çıkarken gecikme 2'den 10'a çıkar, ama 0,9'dan 0,99'a çıkarken 10'dan 100'e sıçrar. Sistem tasarımında bu eğriyi aklında tutmak, "sunucu yüzde 95 dolu ama sorun yok" gibi cümlelerin neden tehlikeli olduğunu açıklar.

## 41.7 Önbellekleme: katmanlar, stratejiler ve stampede

Önbellek (cache), yavaş ama doğru bir kaynağın sonucunu daha hızlı bir yerde tutmaktır. Bölüm 9'daki LRU önbelleğinde sınırlı bellekte hangi kaydın atılacağını gördün; burada asıl soru, önbelleği kaynakla nasıl senkron tuttuğundur. Büyük bir sistemde önbellek tek bir yerde değildir; istek yolu boyunca birden çok katman vardır. Şekil 41.6 bu katmanları ve tipik gecikme sıralarını gösterir.

![Şekil 41.6: İstek yolundaki önbellek katmanları. Gecikme değerleri tipik büyüklük mertebesidir.](gorseller/b41_onbellek_katman.png)

Her katmanın görevi farklıdır. **İstemci önbelleği** tarayıcının ya da uygulamanın yerel kopyasıdır; sıfır ağ gecikmesi verir ama yalnızca o kullanıcıya yarar. **CDN** (içerik dağıtım ağı), statik içeriği kullanıcıya coğrafi olarak yakın kenar sunucularında tutar. **Ters vekil önbellek** (reverse proxy), sunucunun önündeki bir katmandır; aynı yanıtı birçok kullanıcıya sunar. **Uygulama önbelleği** (örneğin Redis), sunucular arasında paylaşılan bir bellek deposudur (Bölüm 35.11). **Veritabanı önbelleği** ise motorun kendi tampon havuzudur (genel bilgi). Bir isteğin en erken katmanda yanıtlanması, arkadaki bütün katmanları korur.

Önbelleğin kendisi bir sorun da yaratır: kaynakla senkron kalması. Bölüm 35.11'de dört kalıp gördün; burada tasarım dilinde özetleyelim. **Cache-aside** (yan önbellek): uygulama önce önbelleğe bakar, yoksa kaynağı okur ve önbelleğe yazar; yazmada kaynağı günceller ve önbellek kaydını siler. **Read-through**: önbelleğin kendisi kaynağı okur. **Write-through**: yazma hem önbelleğe hem kaynağa yapılır. **Write-back**: yazma önce önbelleğe yapılır, kaynağa sonradan gider; hızlıdır ama önbellek çökerse yazmalar kaybolabilir. **TTL** (yaşam süresi), bir kaydın bayatlık süresini sınırlar.

Önbelleğin etkisini ortalama gecikmeyle düşünelim. İsabet oranı `h` ise, ortalama gecikme `E = h x t_onb + (1 - h) x t_kaynak` olur. Önbellek `0,5` ms'de, kaynak `20` ms'de yanıt verirse (bu değerler betikte varsayım olarak alındı) tablo şöyle okunur: `h = 0,5` için ortalama `10,25` ms; `h = 0,9` için `2,45` ms; `h = 0,99` için `0,695` ms. İsabet oranını yüzde 90'dan yüzde 99'a çıkarmak gecikmeyi yaklaşık 3,5 kat düşürür; buna karşılık kaynağa giden istek sayısı on kat azalır. Dikkat: formül yalnızca ortalamayı verir; kuyruğun uzun ucu (p99) için hangi isteklerin kaynağa gittiğini bilmek gerekir.

İsabet oranı, erişim örüntüsüne bağlıdır. Gerçek dünyada istekler eşit dağılmaz; birkaç popüler anahtar çok sayıda istek alır. Bu dağılımı **Zipf** yasasıyla modelleyebiliriz: `k`'inci en popüler anahtarın erişim olasılığı `1/k` ile orantılıdır. Aşağıdaki betik 100 000 anahtarlık bir Zipf dağılımından bir milyon istek üretir ve farklı boyutlu LRU önbelleklerinin isabet oranını ölçer. LRU, Bölüm 9'daki gibi, en uzun süredir kullanılmayan kaydı atar; burada bunu Python'un `OrderedDict` ile gerçekliyoruz.

```python
# -*- coding: utf-8 -*-
"""Bölüm 41.7 - Önbellek isabet oranı ve ortalama gecikme.

1) Formül: ort = h * t_onb + (1 - h) * t_kaynak.
2) Zipf erişim örüntüsü ile LRU önbelleği simülasyonu (Bölüm 9'daki
   LRU fikrinin OrderedDict ile gerçeklemesi). Tohum: 41.
"""

import bisect
import random
from collections import OrderedDict

ANAHTAR = 100000  # farklı anahtar sayısı
ERISIM = 1000000  # toplam istek
S = 1.0  # Zipf üssü (s=1: klasik Zipf)
T_ONB_MS = 0.5  # ağ önbelleği gecikmesi (genel bilgi)
T_KAYNAK_MS = 20.0  # veritabanı gecikmesi (varsayım)
```

```python
class LRU:
    def __init__(self, kapasite):
        self.k = kapasite
        self.v = OrderedDict()

    def al(self, anahtar):
        if anahtar in self.v:
            self.v.move_to_end(anahtar)
            return True
        return False

    def koy(self, anahtar):
        self.v[anahtar] = True
        self.v.move_to_end(anahtar)
        if len(self.v) > self.k:
            self.v.popitem(last=False)
```

```python
def zipf_kumulatif(n, s):
    agirlik = [1.0 / (i**s) for i in range(1, n + 1)]
    toplam = sum(agirlik)
    kum, acc = [], 0.0
    for a in agirlik:
        acc += a / toplam
        kum.append(acc)
    return kum


def isabet_orani(oran, rnd, kum):
    kapasite = int(ANAHTAR * oran)
    onb = LRU(kapasite)
    isabet = 0
    for _ in range(ERISIM):
        a = bisect.bisect_left(kum, rnd.random())
        if onb.al(a):
            isabet += 1
        else:
            onb.koy(a)
    return isabet / ERISIM
```

```python
if __name__ == "__main__":
    print(
        "1) Formül: t_onb = %.2f ms, t_kaynak = %.1f ms"
        % (T_ONB_MS, T_KAYNAK_MS)
    )
    print("h      ort_ms")
    for h in (0.0, 0.5, 0.9, 0.99, 0.999):
        ort = h * T_ONB_MS + (1 - h) * T_KAYNAK_MS
        print("%-6.3f %7.3f" % (h, ort))
    print()
    print(
        "2) Zipf(s=%.1f), %d anahtar, %d istek, LRU"
        % (S, ANAHTAR, ERISIM)
    )
    kum = zipf_kumulatif(ANAHTAR, S)
    print("onbellek(%)  isabet    ort_ms (formül)")
    for oran in (0.01, 0.05, 0.10, 0.20):
        rnd = random.Random(41)
        h = isabet_orani(oran, rnd, kum)
        ort = h * T_ONB_MS + (1 - h) * T_KAYNAK_MS
        print("%-12.0f %7.4f  %8.3f" % (oran * 100, h, ort))
```

Betiğin çıktısı şöyle:

```term
$ python b41_onbellek.py
1) Formül: t_onb = 0.50 ms, t_kaynak = 20.0 ms
h      ort_ms
0.000   20.000
0.500   10.250
0.900    2.450
0.990    0.695
0.999    0.520

2) Zipf(s=1.0), 100000 anahtar, 1000000 istek, LRU
onbellek(%)  isabet    ort_ms (formül)
1             0.5059    10.135
5             0.6638     7.055
10            0.7346     5.675
20            0.8059     4.284
```

Sonuçlar güçlü bir sezgiyi doğruluyor. Önbellek anahtarların yalnızca yüzde 1'ini tutsa bile isabet yüzde 50,6 oluyor; çünkü popüler anahtarlar bu küçük kümede toplanıyor. Yüzde 20'ye çıkınca isabet yüzde 80,6. Ortalama gecikme 10,1 ms'den 4,3 ms'ye iner. Her katına çıkan bellek, isabet oranına eşit bir katkı vermez; getiri azalır. Bu, kapasite kararını bir "kaç gigabayt?" sorusundan çok bir "hangi isabet oranına ihtiyacım var?" sorusuna çevirir.

### Önbellek damgası (stampede)

Önbelleğin en tehlikeli arıza biçimi **önbellek damgası** (cache stampede) ya da sürü baskını adını taşır. Popüler bir anahtarın TTL'i dolduğunda ve yüzlerce istek aynı anda gelirse, hepsi önbellekte bulamaz ve hepsi kaynağa gider. Örneğin önbellek isteklerin yüzde 99'una yanıt veriyorsa veritabanı yalnızca yüzde 1'ini görür; damgada tüm istekleri görür ve yükü yüz kat artar. Bu durum, önbelleğin koruması gereken sistemi öldürür.

Çözümlerden biri **tekil uçuş** (single-flight) ya da istek birleştirmedir: bir anahtar için aynı anda yalnızca bir istek kaynağa gider; diğerleri o isteğin sonucunu bekler. Aşağıdaki betik bunu iş parçacıklarıyla gerçekler. Senaryo: önbellek boş, 1000 iş parçacığı aynı anda aynı anahtarı istiyor, kaynak 0,2 saniyede yanıt veriyor. Bir `threading.Barrier` herkesin aynı anda başlamasını sağlar; böylece yarış koşulu gerçekten oluşur.

```python
# -*- coding: utf-8 -*-
"""Bölüm 41.7 - Önbellek damgası (stampede) ve tekil uçuş.

Senaryo: önbellekte anahtar yok (ya da TTL doldu). 1000 iş parçacığı
aynı anda aynı anahtarı ister. Kaynak (veritabanı) 0,2 s sürer.
Naif: her iş parçacığı kaynağa gider. Tekil uçuş: bir anahtar için
yalnızca bir istek kaynağa gider, diğerleri onu bekler (istek
birleştirme).
"""

import threading
import time


class Onbellek:
    def __init__(self):
        self.veri = {}
        self.kilit = threading.Lock()
        self.kaynak_cagrisi = 0
        self.sayac_kilit = threading.Lock()

    def kaynaktan_oku(self, anahtar):
        with self.sayac_kilit:
            self.kaynak_cagrisi += 1
        time.sleep(0.2)  # yavaş veritabanı (simülasyon)
        return "deger-" + anahtar

    def naif(self, anahtar):
        if anahtar in self.veri:
            return self.veri[anahtar]
        d = self.kaynaktan_oku(anahtar)
        self.veri[anahtar] = d
        return d
```

```python
class TekilUcus(Onbellek):
    def __init__(self):
        super().__init__()
        self.uclar = {}  # anahtar -> Event (uçuştaki istek)

    def al(self, anahtar):
        if anahtar in self.veri:
            return self.veri[anahtar]
        with self.kilit:
            if anahtar in self.veri:
                return self.veri[anahtar]
            olay = self.uclar.get(anahtar)
            benim = olay is None
            if benim:
                olay = threading.Event()
                self.uclar[anahtar] = olay
        if not benim:
            olay.wait()  # başkası getiriyor, bekle
            return self.veri[anahtar]
        try:
            d = self.kaynaktan_oku(anahtar)
            self.veri[anahtar] = d
        finally:
            with self.kilit:
                del self.uclar[anahtar]
            olay.set()
        return d
```

```python
def kos(sinif, metot, n=1000):
    o = sinif()
    bariyer = threading.Barrier(n)
    sonuc = [None] * n

    def is_parcacigi(k):
        bariyer.wait()  # hepsi aynı anda başlasın
        f = getattr(o, metot)
        sonuc[k] = f("urun-42")

    thr = [
        threading.Thread(target=is_parcacigi, args=(k,))
        for k in range(n)
    ]
    for t in thr:
        t.start()
    for t in thr:
        t.join()
    return o.kaynak_cagrisi, len(set(sonuc))
```

```python
if __name__ == "__main__":
    c1, d1 = kos(Onbellek, "naif")
    print(
        "naif          : kaynak çağrısı = %d, farklı yanıt = %d"
        % (c1, d1)
    )
    c2, d2 = kos(TekilUcus, "al")
    print(
        "tekil uçuş    : kaynak çağrısı = %d, farklı yanıt = %d"
        % (c2, d2)
    )
```

Çıktı:

```term
$ python b41_stampede.py
naif          : kaynak çağrısı = 1000, farklı yanıt = 1
tekil uçuş    : kaynak çağrısı = 1, farklı yanıt = 1
```

Naif yöntemde 1000 iş parçacığının hepsi önbelleği boş görüp kaynağa gitti: 1000 kaynak çağrısı. Tekil uçuşta yalnızca bir çağrı yapıldı; diğer 999 iş parçacığı, uçuştaki isteğin bitmesini `Event` ile bekledi ve aynı değeri aldı. Yanıt sayısı iki yöntemde de 1'dir: herkes tutarlı bir değer aldı. Betiği üç kez çalıştırdığımızda sonuç değişmedi; çünkü bariyer çakışmayı zorunlu kılıyor.

Bu kodun gerçek bir sistemdeki sınırları var. Tek bir süreç içindeki kilit, birden çok sunucu arasında işe yaramaz; orada dağıtık bir kilit ya da önbellek sunucusunun kendi atomik işlemleri gerekir (genel bilgi). Ayrıca bir kaynak isteği başarısız olursa bekleyenlerin hepsi aynı hatayı alır; bu, hata yayılımını da kontrol etmen gerektiğini gösterir. Son olarak, TTL'i rastgele bir sapmayla dağıtmak (jitter), birçok anahtarın aynı anda dolmasını önler ve stampede'in bir başka önleyicisidir.

Önbellek geçersiz kılma (invalidation) ise bu bölümün en zor kısmıdır. Kaynak değiştiğinde önbelleği ne zaman ve nasıl silersin? Silmeyi unutursan kullanıcı bayat veri görür; önce silip sonra eski değeri yeniden yazan bir yarış koşulu oluşursa, bayat değer süresiz kalabilir. Bu yüzden önbellek tasarımında "bayatlık ne kadar kabul edilebilir?" sorusu, teknik kararı belirler: bazı veriler birkaç saniyelik bayatlığa tahammül eder, bazıları (örneğin bir hedefin koordinatı) etmez.

## 41.8 Kuyruklar ve asenkron işleme

Her işin isteğin yanıtını beklemesi gerekmez. Bir kullanıcı sipariş verdiğinde faturanın kesilmesi, e-postanın gönderilmesi ya da raporun hazırlanması isteğin yanıtına girmek zorunda değildir; bunları bir **kuyruğa** koyup hemen yanıt dönebilirsin. Asenkron işleme, hem yanıt süresini düşürür hem de yük tepelerini düzleştirir: gelen istekler kuyrukta birikir, işçiler kendi hızlarında çeker.

Kuyruk kalıbını Bölüm 27.10'daki **üretici-tüketici** problemi üzerinden tanıdın: üretici bir tampona yazar, tüketici okur, tampon dolduğunda üretici bekler. Dağıtık sistemlerde aynı kalıp bir **mesaj kuyruğu** olarak uygulanır. İki yaygın model vardır (genel bilgi). **RabbitMQ** tarzı bir sistemde mesaj kuyruğa girer, bir tüketici alır ve onay (acknowledgment) gönderince silinir; hedef, işi dağıtmak ve güvenilir biçimde tamamlamaktır. **Kafka** tarzı bir sistemde ise mesajlar bölümlere (partition) ayrılmış bir günlüğe eklenir ve her tüketici kendi konumunu (offset) tutar; mesajlar tüketilse de saklama süresi dolana kadar silinmez (genel bilgi), bu da yeniden oynatmayı mümkün kılar.

Asıl zor soru, bir mesajın **kaç kez** teslim edileceğidir. Üç garanti vardır. **En fazla bir kez** (at-most-once): mesaj kaybolabilir ama asla iki kez işlenmez. **En az bir kez** (at-least-once): mesaj kaybolmaz ama tekrar teslim edilebilir; bir ağ kesintisinde tüketici işi yaptı ama onayı gönderemedi, mesaj yeniden gelir. **Tam bir kez** (exactly-once): her mesaj tam bir kez etkisini gösterir. Dağıtık bir ağda gerçek anlamda tam bir kez teslim, bir ağ kesintisinde mesajın işlenip işlenmediğini hem gönderen hem alan için bilmeyi gerektirir ve bu genel olarak mümkün değildir (genel bilgi). Pratikte mühendisler **at-least-once** teslim alır ve tüketiciyi **idempotent** yapar; böylece sonuç, tam bir kez teslim edilmiş gibi görünür. Kafka gibi sistemler belirli bir kapsamda üretici idempotentliği ve işlem desteği sunar (genel bilgi), ama uygulama düzeyindeki idempotentlik sorumluluğu yine sende kalır.

**İdempotent tüketici**, aynı mesajı iki kez işlediğinde sonucun değişmediği tüketicidir. Bunun iki yaygın yolu vardır. Birincisi, her mesaja benzersiz bir kimlik verip işlenmiş kimlikleri bir tabloda tutmak; ikinci mesaj geldiğinde kimlik zaten varsa atlanır. İkincisi, işlemi kendisi idempotent yapmak: "konumu 40 yapıldı" tekrarlanabilir, ama "konumu 5 birim ilerlet" tekrarlanınca iki kez ilerler. Bölüm 40'ta API tasarımında gördüğün idempotentlik anahtarı, aynı fikrin istek tarafındaki karşılığıdır. Savunma uygulamalarında bu fark kritiktir: bir İHA'ya gönderilen "hedefe git" komutu tekrarlanırsa ne olduğunu bilmeden, komut kanalına güvenemezsin. Komutu sıra numarasıyla ve durum tabanlı yazmak (ör. "hedef koordinatı şu olsun"), ağ tekrarlarına karşı güvenlidir.

Kuyruğun bir sınırsız büyüme riski vardır. Üretici tüketiciden hızlıysa kuyruk büyür, bellek dolar ve sistem çöker. Bu yüzden kuyruklar **sınırlı** tasarlanır ve sınır dolduğunda üreticinin ne yapacağı bilinçli bir karardır: beklemek (geri basınç, backpressure), yeni isteği reddetmek (yük atma, load shedding) ya da en eski kaydı düşürmek. Geri basınç, en güzel kararlardan biridir çünkü tıkanıklığı üreticiye geri bildirir: sistem kendini yavaşlatarak ayakta kalır. Bu kavramın bir Python uygulamasını Kod Okuma bölümünde, `asyncio.Queue(maxsize)` üzerinden okuyacaksın.

## 41.9 Dayanıklılık kalıpları: zaman aşımı, yeniden deneme, devre kesici

Dağıtık bir sistemde bir bileşenin yavaşlaması, arızadan daha tehlikelidir. Arıza net bir hata verir; yavaşlama ise istekleri bekletir, bekleyen istekler bellek ve bağlantı tutar, ve sonunda çağıran bileşen de yavaşlar. Yavaşlık zincir boyunca yayılır. Dayanıklılık kalıpları, bu yayılmayı durdurmak için tasarlanmış küçük ama güçlü araçlardır. Dört temel kalıp vardır: zaman aşımı, yeniden deneme, devre kesici ve bölme.

**Zaman aşımı** (timeout), her dış çağrıya bir süre sınırı koyar. Zaman aşımı olmadan bir çağrı sonsuza kadar bekleyebilir. Zincirli çağrılarda bu daha da önemlidir: A, B'yi çağırır; B, C'yi çağırır. A'nın bütçesi 1 saniyeyse, B'ye 800 milisaniye, B'nin C'ye ayırdığı süre daha azı olmalıdır. Bu, **süre bütçesinin** zincir boyunca azalmasıdır; her katman kendi süresini bir öncekinden küçük tutar.

**Yeniden deneme** (retry) geçici hatalarda işe yarar: bir ağ paketi kaybolmuştur, bir kopya bir an meşgul. Ama yeniden denemenin bedeli vardır ve en kötü anda en çok zarar verir. Bir sunucu yavaşladığında herkes yeniden dener; yük iki katına çıkar; sunucu daha da yavaşlar. Bu kısır döngüye **sürü etkisi** (thundering herd) denir. Yeniden denemenin doğru kullanımı üç kural içerir: yalnızca geçici hatalarda dene (ağ hatası, 503 gibi), yalnızca idempotent işleri dene (Bölüm 41.8), ve bekleme süresini **üstel geri çekilme** (exponential backoff) ile artır.

Üstel geri çekilmede `k`'inci başarısızlıktan sonraki bekleme üst sınırı `min(tavan, taban x 2^(k-1))` olur. Ama bu tek başına yetmez: bütün istemciler aynı anda başarısız olduysa, hepsi aynı anda tekrar dener. Bu yüzden bekleme süresine **jitter** (rastgelelik) eklenir. Üç strateji karşılaştıracağız (ayrışık jitter, AWS'in 2015 yazısıyla yaygınlaşmış bir yöntemdir, genel bilgi):

- **Sabit**: bekleme tam olarak `min(tavan, taban x 2^(k-1))`. Jitter yok.
- **Tam jitter**: bekleme `uniform(0, min(tavan, taban x 2^(k-1)))`.
- **Ayrışık jitter**: bekleme `min(tavan, uniform(taban, 3 x önceki_bekleme))`.

Bir simülasyonla bu farkı görelim. Senaryo: 1000 istemci, aynı anda (t = 0) başarısız oluyor. Sunucu ilk iki saniye kapalı, sonra saniyede 200 isteği kabul ediyor. Kapasiteyi aşan istekler reddediliyor. Her istemci en fazla 12 deneme yapıyor; taban 1 saniye, tavan 30 saniye. Betik her strateji için toplam istek sayısını, başarıyı, süreyi ve tepe yükünü ölçer.

```python
# -*- coding: utf-8 -*-
"""Bölüm 41.6 - Yeniden deneme: sürü etkisi (thundering herd).

Senaryo: 1000 istemci t=0'da aynı anda başarısız olur (sunucu 2 s
kapalı). Sunucu t >= 2 s'de açılır, kapasitesi 200 istek/s'dir
(10 ms'de 2 istek). Kapasiteyi aşan istekler reddedilir ve istemci
geri çekilme (backoff) ile yeniden dener. En fazla 12 deneme.
Üç strateji: sabit (jitter yok), tam jitter, ayrışık jitter.
Tohum: 41. Çıktı: engine/veri/b41_jitter.csv
"""

import csv
import heapq
import random

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
TICK = 0.01  # simülasyon adımı (s)
SUNUCU_ACILIS = 2.0  # sunucu bu andan sonra hizmet verir (s)
KAPASITE = 2  # tick başına kabul edilen istek (200/s)
ISTEMCI = 1000
TABAN = 1.0  # ilk geri çekilme (s)
TAVAN = 30.0  # geri çekilme üst sınırı (s)
MAKS = 12  # en fazla deneme sayısı
KOVA = 0.1  # sayım kovası (s)
SURE = 120.0
```

```python
def bekleme(strateji, k, onceki, rnd):
    """k: şimdiye kadarki başarısızlık sayısı (>= 1)."""
    if strateji == "sabit":
        return min(TAVAN, TABAN * 2 ** (k - 1)), None
    if strateji == "tam":
        ust = min(TAVAN, TABAN * 2 ** (k - 1))
        return rnd.uniform(0, ust), None
    if strateji == "ayrisik":
        # ayrışık jitter: önceki beklemeye göre yeni aralık
        s = min(TAVAN, rnd.uniform(TABAN, onceki * 3))
        return s, s
    raise ValueError(strateji)
```

```python
def kos(strateji, rnd):
    olay = [(0.0, i) for i in range(ISTEMCI)]
    heapq.heapify(olay)
    deneme = [0] * ISTEMCI
    onceki = [TABAN] * ISTEMCI
    kovalar = {}
    toplam = basarili = vazgecen = 0
    son = 0.0

    adim = int(round(SURE / TICK))
```

```python
    for s in range(adim):
        t = s * TICK
        istekler = []
        while olay and olay[0][0] <= t + 1e-9:
            istekler.append(heapq.heappop(olay)[1])
        if not istekler:
            continue
        kova = int(t / KOVA + 1e-9)
        kovalar[kova] = kovalar.get(kova, 0) + len(istekler)
        toplam += len(istekler)
        kabul = (
            set(istekler[:KAPASITE]) if t >= SUNUCU_ACILIS else set()
        )
        for i in istekler:
            if i in kabul:
                basarili += 1
                son = t
                continue
            deneme[i] += 1
            if deneme[i] >= MAKS:
                vazgecen += 1
                continue
            d, yeni = bekleme(strateji, deneme[i], onceki[i], rnd)
            if yeni is not None:
                onceki[i] = yeni
            heapq.heappush(olay, (t + d, i))
```

Ana döngü, reddedilen her istek için yeni bir bekleme süresi hesaplar ve olayı zaman çizelgesine ekler. Ayrışık jitter bir önceki bekleme değerini ister; bu yüzden her istemci için `onceki` listesi ayrıca tutulur.

```python
    tepe = max(kovalar.values())
    ilk_sn = int(1.0 / KOVA)  # t=0 ilk başarısızlık patlamasını dışla
    tepe_sonra = max(v for k, v in kovalar.items() if k >= ilk_sn)
    bekleyen = len(olay)
    return (
        toplam,
        basarili,
        vazgecen,
        bekleyen,
        son,
        tepe,
        tepe_sonra,
        kovalar,
    )
```

```python
if __name__ == "__main__":
    satirlar = []
    print(
        "strateji  toplam  basarili  vazgecen  bekleyen  son_s"
        "  tepe  tepe_1s_sonra"
    )
    for strateji in ("sabit", "tam", "ayrisik"):
        rnd = random.Random(41)
        top, bas, vaz, bek, son, tepe, tepe_s, kov = kos(
            strateji, rnd
        )
        print(
            "%-9s %7d %9d %9d %9d %6.2f %5d %8d"
            % (strateji, top, bas, vaz, bek, son, tepe, tepe_s)
        )
        for k in range(int(SURE / KOVA)):
            satirlar.append(
                [strateji, "%.1f" % (k * KOVA), kov.get(k, 0)]
            )
    with open(
        VERI + "/b41_jitter.csv", "w", encoding="utf-8", newline=""
    ) as f:
        w = csv.writer(f)
        w.writerow(["strateji", "zaman_s", "istek_100ms"])
        w.writerows(satirlar)
```

Çıktı:

```term
$ python b41_jitter.py
strateji  toplam  basarili  vazgecen  bekleyen  son_s  tepe  tepe_1s_sonra
sabit        7970        12         0       988  91.00  1000     1000
tam          4432      1000         0         0  37.00  1083       72
ayrisik      3039      1000         0         0  26.42  1000       69
```

Sütunları açıklayalım. `toplam` sunucuya giden toplam istek sayısı, `basarili` kabul edilen istek, `vazgecen` on iki denemeyi tüketen istemci, `bekleyen` simülasyon bittiğinde hâlâ bekleyen istemci, `son_s` son başarılı isteğin zamanı, `tepe` en yoğun 100 milisaniyelik kovadaki istek sayısı, ve `tepe_1s_sonra` ilk saniyeden sonraki en yoğun kova. Tepe sütunu ilk saniyedeki ortak başarısızlığı da içerdiği için, asıl sürü etkisini `tepe_1s_sonra` gösterir.

Sabit geri çekilmede sürü etkisi açıkça görülüyor. 1000 istemci aynı anda yeniden deniyor; bu, 1 saniye, 3 saniye, 7 saniye, 15 saniye ve 31 saniye sonrasında tekrar eden tepeler olarak Şekil 41.7'de görünüyor. Her tepede sunucu yalnızca 2 isteği kabul edebiliyor (10 milisaniyede 2 istek, yani 200 istek/s), gerisi reddediliyor; bu yüzden 120 saniye sonunda yalnızca 12 istemci başarılı, 988 istemci hâlâ bekliyor. Tam jitter 1000 isteği 37 saniyede bitirdi ve sunucuya 4 432 istek gönderdi; ayrışık jitter 26,4 saniyede bitirdi ve yalnızca 3 039 istek gönderdi. Ayrışık jitter daha az istekle daha hızlı sonuç verdi. Bunun nedeni bekleme sürelerinin istemciler arasında daha iyi ayrışması olabilir; simülasyon bu nedeni ayrıca sınamadı, yalnızca sonucu ölçtü.

![Şekil 41.7: Yeniden denemede istek sayısı (100 ms kova). Sabit geri çekilmede tepeler 1, 3, 7, 15 ve 31 saniyede aynı anda gelir; jitter bu tepeleri dağıtır.](gorseller/b41_jitter_surusu.png)

Bu simülasyonun sınırları da var: sunucu tek bir sabit kapasiteye sahip, istemciler tek bir zaman çizelgesi izliyor ve ağ gecikmesi yok. Ama yönü görmek için yeterli. Yeniden denemeyi tasarlarken akla gelen ilk soru "kaç kez deneyeyim?" değil, "bu deneme kopyaları nasıl dağıtır?" olmalıdır.

**Devre kesici** (circuit breaker) bir bağımlılığın kötü olduğunu bildiğinde çağrıları tamamen durdurur. Elektrik devresindeki sigortadan ilham alır: aşırı yük olduğunda devreyi keser, hasarı önler ve bir süre sonra yeniden dener. Devre kesicinin üç durumu vardır. **KAPALI** (closed) durumunda istekler geçer ve hatalar sayılır. Ardışık hata sayısı bir eşiğe ulaşırsa devre **AÇIK** (open) durumuna geçer: istekler yapılmadan, hemen hata döndürülerek reddedilir. Bekleme süresi dolunca devre **YARI AÇIK** (half-open) durumuna geçer: yalnızca tek bir deneme isteğine izin verir. Deneme başarılıysa devre kapanır; başarısızsa yeniden açılır.

![Şekil 41.8: Devre kesici durum makinesi. Eşik ve bekleme süresi, geçişleri belirler.](gorseller/b41_devre_kesici.png)

Devre kesici, Bölüm 22.12'deki **State** kalıbının somut bir örneğidir: davranış (istekleri geçirmek ya da reddetmek) durumun (KAPALI, AÇIK, YARI AÇIK) bir fonksiyonudur ve geçişler açıkça tanımlanır. Aşağıdaki gerçeklemede her durum, bir `cagir` metodunun dallarıdır. Zaman, sayılmaz; bir tam sayı `tick` ile temsil edilir, böylece deneme deterministik olur.

```python
# -*- coding: utf-8 -*-
"""Bölüm 41.8 - Devre kesici (circuit breaker) ve durum izi.

Durumlar: KAPALI (istek geçer), AÇIK (istek reddedilir),
YARI AÇIK (tek deneme isteğine izin verilir).
Saat: tam sayı tick. Hata ardışık `esik` kez olursa AÇIK olur;
AÇIK'ta `bekleme` tick geçince YARI AÇIK'a geçilir.
"""

KAPALI = "KAPALI"
ACIK = "AÇIK"
YARI = "YARI AÇIK"
```

```python
class DevreKesici:
    def __init__(self, esik=3, bekleme=5):
        self.esik = esik
        self.bekleme = bekleme
        self.durum = KAPALI
        self.ardisik = 0
        self.acilis = None

    def _ac(self, t):
        self.durum = ACIK
        self.acilis = t
        self.ardisik = 0

    def cagir(self, t, islem):
        """islem() bir istisna fırlatırsa hata sayılır."""
        if self.durum == ACIK:
            if t - self.acilis < self.bekleme:
                return "REDDEDİLDİ"
            self.durum = YARI  # bekleme doldu: tek deneme
        deneme = self.durum == YARI
        try:
            islem()
        except Exception:
            if deneme:
                self._ac(t)  # deneme başarısız: yeniden aç
                return "DENEME HATA"
            self.ardisik += 1
            if self.ardisik >= self.esik:
                self._ac(t)
            return "HATA"
        self.durum = KAPALI  # başarı: kapat ve sayacı sıfırla
        self.ardisik = 0
        return "DENEME BAŞARI" if deneme else "BAŞARI"
```

```python
def hata():
    raise IOError("bağlantı yok")


def basari():
    return "tamam"

if __name__ == "__main__":
    # Her tick'te bir çağrı yapılır. "H" hata, "B" başarı.
    # Reddedilen tick'lerde arka uç çağrılmaz.
    dizi = "BHHHHBHHHBBBBBBHHBBB"
    cb = DevreKesici(esik=3, bekleme=5)
    print("tick  önce        çağrı  sonuç         sonra")
    for t, c in enumerate(dizi):
        onceki = cb.durum
        islem = hata if c == "H" else basari
        sonuc = cb.cagir(t, islem)
        print(
            "%-5d %-12s  %s      %-14s %s"
            % (t, onceki, c, sonuc, cb.durum)
        )
```

Bir hata dizisi boyunca durum izi, kalıbı anlamanın en iyi yoludur. Dizideki her harf, o tick'te arka ucun ne yaptığını gösterir: `B` başarılı, `H` hata. Devre AÇIK iken arka uca hiç gidilmediğini unutma; yine de dizide `H` ya da `B` yazılı olabilir, ama bu bir çağrı değildir.

```term
$ python b41_devre_kesici.py
tick  önce        çağrı  sonuç         sonra
0     KAPALI        B      BAŞARI         KAPALI
1     KAPALI        H      HATA           KAPALI
2     KAPALI        H      HATA           KAPALI
3     KAPALI        H      HATA           AÇIK
4     AÇIK          H      REDDEDİLDİ     AÇIK
5     AÇIK          B      REDDEDİLDİ     AÇIK
6     AÇIK          H      REDDEDİLDİ     AÇIK
7     AÇIK          H      REDDEDİLDİ     AÇIK
8     AÇIK          H      DENEME HATA    AÇIK
9     AÇIK          B      REDDEDİLDİ     AÇIK
10    AÇIK          B      REDDEDİLDİ     AÇIK
11    AÇIK          B      REDDEDİLDİ     AÇIK
12    AÇIK          B      REDDEDİLDİ     AÇIK
13    AÇIK          B      DENEME BAŞARI  KAPALI
14    KAPALI        B      BAŞARI         KAPALI
15    KAPALI        H      HATA           KAPALI
16    KAPALI        H      HATA           KAPALI
17    KAPALI        B      BAŞARI         KAPALI
18    KAPALI        B      BAŞARI         KAPALI
19    KAPALI        B      BAŞARI         KAPALI
```

Tick 1-3'te üç ardışık hata eşiğe (3) ulaştı ve devre AÇIK oldu. Tick 4-7 arasında istekler reddedildi; bekleme süresi 5 tick olduğundan tick 8'de devre YARI AÇIK'a geçti ve tek deneme yapıldı. Bu deneme (`H`) başarısız oldu: `DENEME HATA` satırı devreyi yeniden AÇIK yaptı ve yeni bekleme süresi tick 8'de başladı. Tick 13'te yeni bekleme doldu, deneme (`B`) başarılı oldu ve devre KAPALI'ya döndü. Tick 14-19 arasında iki ardışık hata oldu (tick 15 ve 16), ama eşik 3'e ulaşılmadan tick 17'deki başarı sayacı sıfırladı; devre KAPALI kaldı.

Bu kalıbın iki parametresi var ve ikisi de bir takastır. **Eşik** çok düşükse devre, geçici tek bir hatada bile açılır ve sistem sürekli gidip gelir (flapping). Çok yüksekse arızalı bağımlılık çok sayıda isteği boşuna bekletir. **Bekleme süresi** kısaysa, bağımlılık toparlanmadan tekrar denenir; uzunsa, toparlandığında bile geç haber alınır. Gerçek sistemlerde bu değerler gözlemlenen hata oranına göre ayarlanır.

**Bölme** (bulkhead), bir bileşenin kaynaklarını bağımlılıklara göre ayırmaktır. Gemiler su geçirmez bölmelerle yapılır; bir bölme su alırsa gemi batmaz. Yazılımda, her bağımlılık için ayrı bir bağlantı havuzu ya da iş parçacığı havuzu ayrılır. Raporlama servisi yavaşladığında, ortak bir havuz tükenirse kullanıcı oturumları da durur; ayrı havuzlarla yalnızca raporlama etkilenir. **Kademeli bozulma** (graceful degradation) ise bir bağımlılık çöktüğünde tam işlevi bozmak yerine sınırlı bir yanıt vermektir: öneri servisi çökerse "popüler ürünler" sabit bir listesi döner. Kullanıcı eksik bir deneyim görür ama sistem ayakta kalır.

Son bir kalıp, **hız sınırı** (rate limiting), sistemi kötü niyetli ya da hatalı istemcilerden korur. En yaygın yöntem **jeton kovası** (token bucket)dır: bir kova en fazla `B` jeton tutar; jetonlar `r` jeton/saniye hızında dolar; her istek bir jeton harcar; kova boşsa istek reddedilir (HTTP'de 429, genel bilgi). Kovanın `B` kapasitesi kısa patlamalara izin verir, `r` ise uzun vadeli ortalama hızı belirler. Bölüm 40'ta API'lerin hız sınırlarını göreceksin; burada aynı mekanizmanın dayanıklılık tarafındaki rolünü not ediyoruz.

## 41.10 Veri katmanı: çoğaltma, bölümleme, dağıtık işlem

Uygulama katmanı yatay ölçeklenmesi kolay olan kısımdır; zor olan veridir. Bölüm 35'te veriyi birden çok makineye nasıl koyacağını ve tutarlılığın ne demek olduğunu gördün. Burada bu kararların sistem tasarımındaki sonuçlarına bakıyoruz.

**Okuma replikaları**, ana veritabanının asenkron kopyalarıdır. Okuma yükü replikalara dağıtılır, ana sunucu yazmaya odaklanır. Bedeli, replikanın gerisinde kalmasıdır: bir yazmadan hemen sonra replikadan okuyan kullanıcı, eski değeri görebilir. Bunu çözmenin yaygın yolu **oku-yazdığını-oku** (read-your-writes) tutarlılığıdır: bir kullanıcı yazdıktan sonraki kısa pencerede okumalarını ana sunucuya yönlendirirsin. Bu, Bölüm 35.8'deki tutarlılık modelinin uygulamadaki karşılığıdır.

**Bölümleme** (sharding), veriyi bir **bölüm anahtarına** göre makinelere dağıtır. Anahtar seçimi kritiktir: kullanıcı kimliği çoğu zaman iyi bir seçimdir, çünkü istekler kullanıcıya dağılır. Ama bir anahtar çok sıcak olursa (ör. ünlü bir hesap ya da tek bir popüler ürün) o bölüm tek makineyi boğar. Bölüm 35.7'deki tutarlı hash, bölümler arasında yeniden dengeleme yaparken taşınan veriyi azaltır; sıcak anahtar sorununu ise çözmez. Bölümleme ayrıca çapraz bölüm sorgularını pahalı yapar. Bölüm 34'te JOIN'in maliyetini gördün; dağıtık bir JOIN birden çok ağ turu demektir. Bu yüzden ilişkileri bölüm anahtarına göre tasarlarsın. Bölüm 34.9'daki N+1 sorunu da burada ağ çağrıları olarak ortaya çıkar: her öğe için ayrı bir uzak çağrı yapmak yerine toplu (batch) çağrı kullanmak gerekir.

Bir işlemin birden çok bölümü ya da servisi etkilediği durumda **dağıtık işlem** gerekir. Bölüm 35'te iki aşamalı işlemi (two-phase commit) gördün: tüm katılımcılar "hazırım" dedikten sonra koordinatör "yap" der. Bu protokolün sorunu, koordinatör çökerse katılımcıların kilitli kalmasıdır; sistem bekler. Bu yüzden büyük ölçekli sistemler çoğu zaman **saga** kalıbını tercih eder (Garcia-Molina ve Salem, 1987; genel bilgi). Saga, bir dizi yerel işlemdir; her adımın bir **telafi** (compensation) işlemi vardır. Sipariş örneğinde: stok ayır, ödemeyi al, kargoya ver. Ödeme başarısız olursa, stok ayırma telafi edilir (ayırma iptal edilir). Saga tam atomik değildir; ara durumlar görünür olabilir, ama her adımın geri alınabilir olması sistemi tutarlı bir sona götürür.

**Raft** ile devam edelim; Bölüm 35.8'de adını ve kavramını görmüştün, şimdi nasıl çalıştığını ve sistem tasarımında nerede kullanıldığını öğreniyoruz. Raft, birden çok düğümün **aynı sırada aynı kararı** vermesini sağlayan bir konsensüs algoritmasıdır. Üç parçası vardır (Ongaro ve Ousterhout, 2014; genel bilgi). **Lider seçimi**: düğümler bir zaman aşımına sahiptir; sinyal (kalp atışı) almayan bir düğüm kendini aday ilan eder ve oy ister. Zaman aşımları rastgeledir, böylece iki aday aynı anda yarışmaz. Çoğunluk oyu alan aday lider olur. **Günlük çoğaltma**: lider, istemciden gelen komutu kendi günlüğüne ekler ve takipçilere gönderir; komut, çoğunluk onayladığında **commit** edilir. **Güvenlik**: yalnızca günlüğü en az o kadar güncel olan bir düğüm lider seçilebilir; böylece commit edilmiş bir kayıt kaybolmaz.

Çoğunluk kuralı, Raft'ın dayanıklılığını belirler. `N` düğümlü bir kümede çoğunluk `floor(N/2) + 1` düğümdür ve en fazla `floor((N-1)/2)` düğüm arızasına dayanılabilir. Tablo bunu gösterir:

| Düğüm sayısı (N) | Çoğunluk | Dayanılan arıza |
|---|---|---|
| 3 | 2 | 1 |
| 5 | 3 | 2 |
| 7 | 4 | 3 |

Çift sayıda düğüm (4 ya da 6) genellikle tercih edilmez: `N = 4`'ün çoğunluğu 3'tür ve yine yalnızca 1 arızaya dayanır; bir düğüm daha fazla maliyet, ek dayanıklılık getirmez. Raft tek bir yazma için bile çoğunluğun ağ turunu bekler; bu nedenle aynı veri merkezinde bile her yazma en az bir ağ turu gecikmesi taşır (0,5 ms genel bilgi). Raft'ı gerçek bir sistemde, etcd ve Consul gibi sistemler, küçük ama kritik bir yapılandırma ve üst veri deposunu tutarlı tutmak için kullanır (genel bilgi). Büyük hacimli veriyi Raft üzerinden yazmak genellikle pahalıdır; bu yüzden Raft çoğunlukla "kim lider, hangi yapılandırma geçerli" gibi küçük ama tutarlılık gerektiren bilgiyi taşır.

**CQRS** (komut ve sorgu sorumluluklarının ayrılması), yazma modelini ve okuma modelini ayrı tasarlamaktır. Yazma tarafı, iş kurallarını uygulayan ve olayları kaydeden bir modeldir. Okuma tarafı, bu olaylardan türetilmiş ve sorgu için optimize edilmiş bir görünümdür. İki model arasındaki gecikme, okuma tarafının bayat olabileceği anlamına gelir; bu, sonsuz tutarlılık (eventual consistency) demektir. CQRS, okuma ve yazma yükleri çok farklı olduğunda ve okumanın ayrı biçimlere ihtiyaç duyduğunda işe yarar; her sistemde gereksiz bir karmaşıklıktır. Bunu bir takas olarak değerlendir.

## 41.11 Gözlemlenebilirlik: ölçmeden tasarlanamaz

Bir sistemi tasarlamak, onu çalışırken anlayabilmekle eşdeğerdir. Bu yüzden gözlemlenebilirlik (observability) tasarımın parçasıdır, sonradan eklenen bir özellik değildir. Üç sinyal türü vardır (genel bilgi). **Metrikler**, zaman içinde toplanan sayısal özetlerdir: istek sayısı, hata oranı, gecikme dağılımı. **Loglar**, olayların kayıtlarıdır; yapılandırılmış (anahtar-değer) biçimde tutulmaları, arama yapabilmek için önemlidir. **İzler** (trace), bir isteğin birden çok servis içinden geçen yolunu gösterir; her adım bir **span**, bütün zincir bir **trace** olarak kaydedilir. Google'ın Dapper makalesi (2010) bu kavramı yaygınlaştırdı (genel bilgi).

Metrikleri düzenlemenin iki yaygın yöntemi vardır (genel bilgi). **RED** yöntemi servisler için kullanılır: istek hızı (**R**ate), hata sayısı (**E**rrors) ve süre (**D**uration). **USE** yöntemi kaynaklar (CPU, disk, bağlantı havuzu) için kullanılır: kullanım (**U**tilization), doygunluk (**S**aturation, bekleyen iş) ve hata (**E**rrors). İkisi birlikte, bir sorunun servisten mi yoksa kaynaktan mı geldiğini ayırt etmeye yarar.

Gecikmeyi ölçerken en sık yapılan hata ortalamaya bakmaktır. Ortalama, uzun kuyruğu gizler. Bir örnekle görelim. 100 istekten 95'i 20 milisaniye, 4'ü 100 milisaniye, 1'i 2 saniye sürsün. **Yüzdelik** (percentile), sıralı değerlerin belirli bir oranın altında kalan değeridir. Betik en yakın sıra (nearest-rank) yöntemiyle `q` yüzdeliğini `sirali[ceil(q x n) - 1]` olarak hesaplar.

```python
# -*- coding: utf-8 -*-
"""Bölüm 41.10 - Yüzdelikler ve kuyruk gecikmesi (tail latency).

1) En yakın sıra (nearest-rank) yüzdeliği: sıralı n değerden q
   yüzdeliği = sirali[ceil(q*n) - 1].
2) Yayılım (fan-out): bir sayfa 10 servise paralel istek atar; her
   servisin p99'u 100 ms. Sayfa, en yavaş servisi bekler.
Tohum: 41.
"""

import math
import random

def yuzdelik(degerler, q):
    s = sorted(degerler)
    n = len(s)
    return s[math.ceil(q * n) - 1]
```

```python
if __name__ == "__main__":
    # 100 istek: 95 tanesi 20 ms, 4 tanesi 100 ms, 1 tanesi 2000 ms
    ornek = [20] * 95 + [100] * 4 + [2000]
    print("ortalama = %.1f ms" % (sum(ornek) / len(ornek)))
    print("p50      = %d ms" % yuzdelik(ornek, 0.50))
    print("p90      = %d ms" % yuzdelik(ornek, 0.90))
    print("p99      = %d ms" % yuzdelik(ornek, 0.99))
    print("maks     = %d ms" % max(ornek))

    # Yayılım: 10 paralel servis, her birinin p99 = 100 ms
    n = 10
    p_yavas = 0.01
    print()
    print(
        "Analitik: P(en az biri > 100 ms) = 1 - 0,99^%d = %.4f"
        % (n, 1 - (1 - p_yavas) ** n)
    )
    rnd = random.Random(41)
    deneme = 200000
    yavas = 0
    for _ in range(deneme):
        if any(rnd.random() < p_yavas for _ in range(n)):
            yavas += 1
    print(
        "Simülasyon (%d deneme)                : %.4f"
        % (deneme, yavas / deneme)
    )
```

Çıktı:

```term
$ python b41_gozlem.py
ortalama = 43.0 ms
p50      = 20 ms
p90      = 20 ms
p99      = 100 ms
maks     = 2000 ms

Analitik: P(en az biri > 100 ms) = 1 - 0,99^10 = 0.0956
Simülasyon (200000 deneme)                : 0.0960
```

Ortalama 43 milisaniye, medyan (p50) 20 milisaniye, p99 100 milisaniye. Ortalama ve p50 kullanıcının "normal" deneyimini anlatır, p99 ise her yüz istekten birinin ne kadar beklediğini. Maksimum 2 saniyedir ve tek bir isteğin sistemde ne kadar uzun kalabildiğini gösterir. Bölüm 31.9'da, sunucu modellerini ölçerken maksimum sütununun p99'un gizlediği kuyruğu gösterdiğini görmüştün; burada aynı dersi bir dağıtık sistemin içinden tekrarlıyoruz.

Asıl sürpriz **yayılım** (fan-out) ile gelir. Bir sayfa 10 servise paralel istek atıyor ve her servisin p99'u 100 milisaniye olsun. Sayfa, en yavaş yanıtı beklediği için kendi gecikmesi, tek bir servisinkinden çok daha kötü olur. Bir servisin yavaş olma olasılığı yüzde 1 ise, en az birinin yavaş olma olasılığı `1 - 0,99^10 = 0,0956`, yani yüzde 9,6'dır. Simülasyon bunu 200 000 denemeyle `0,0960` olarak doğruladı. Yani sayfaların yaklaşık onda biri, tek bir servisin p99'unu aşar. Büyük ölçekli sistemlerde "nadir" olan olay, yüksek yayılımda nadir değildir (Dean ve Barroso'nun "The Tail at Scale" tartışması, genel bilgi). Bu yüzden hedef gecikme, ortalamaya değil, yayılım altındaki yüzdeliğe göre konulmalıdır.

Gözlemlenebilirlik, SLO'nun da ölçüsüdür. SLI'ı ölçen metrik olmadan hata bütçesini izleyemezsin; hata bütçesi olmadan da hangi değişikliğin yayınlanabileceğine karar veremezsin. Bu bağ, bölümün başında kurduğumuz SLO fikrinin günlük işleyişe bağlanmasıdır.

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

```python
# -*- coding: utf-8 -*-
"""Bölüm 41.9 - URL kısaltıcı: ID üretimi ve base62 kodlama.

1) base62 kodlama/çözme (0-9, a-z, A-Z; 62 karakter).
2) Sayaç: uzunluk büyümesi.
3) Kırpılmış hash: doğum günü çakışmaları (tohum 41).
4) Snowflake tarzı üretici: 41 bit zaman | 10 bit makine |
   12 bit sıra.
"""

import hashlib
import random
import threading

ALFABE = (
    "0123456789abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
)
```

```python
def kodla(n):
    if n == 0:
        return ALFABE[0]
    s = []
    while n > 0:
        n, r = divmod(n, 62)
        s.append(ALFABE[r])
    return "".join(reversed(s))


def coz(s):
    n = 0
    for ch in s:
        n = n * 62 + ALFABE.index(ch)
    return n
```

```python
def sayac_uzunlugu():
    print("Sayaç -> kod uzunluğu (base62)")
    for n in (1, 61, 62, 3843, 3844, 10**6, 10**9):
        print(
            "%12d -> %-8s (%d karakter)"
            % (n, kodla(n), len(kodla(n)))
        )
    print(
        "Kontrol: coz(kodla(n)) == n:",
        all(coz(kodla(n)) == n for n in range(100000)),
    )
```

```python
def hash_cakisma(n=10**6, bit=32):
    rnd = random.Random(41)
    N = 2**bit
    degerler = set()
    for i in range(n):
        url = "https://ornek.com/s/%d-%d" % (i, rnd.randrange(10**9))
        h = hashlib.sha256(url.encode()).digest()
        degerler.add(int.from_bytes(h[: bit // 8], "big"))
    cakisan = n - len(degerler)
    beklenen = n - N * (1 - (1 - 1 / N) ** n)
    print()
    print("Kırpılmış hash, %d bit, %d URL" % (bit, n))
    print("ölçülen çakışan kayıt : %d" % cakisan)
    print("beklenen (doğum günü) : %.1f" % beklenen)
```

```python
class SnowflakeTarzi:
    """Tek makinede sıra + zaman; makineler koordinasyonsuz."""

    ZAMAN_BIT, MAKINE_BIT, SIRA_BIT = 41, 10, 12
    SIRA_MAKS = (1 << 12) - 1

    def __init__(self, makine, saat_ms):
        self.makine = makine & ((1 << 10) - 1)
        self.saat = saat_ms
        self.son = -1
        self.sira = 0
        self.kilit = threading.Lock()

    def al(self):
        with self.kilit:
            ms = self.saat()
            if ms == self.son:
                self.sira = (self.sira + 1) & self.SIRA_MAKS
                if self.sira == 0:
                    raise RuntimeError("bu ms'de sıra taştı")
            else:
                self.sira = 0
            self.son = ms
            return (ms << 22) | (self.makine << 12) | self.sira
```

```python
def snowflake_demo():
    print()
    print("Snowflake tarzı üretici (sabit saat, 4 makine)")
    saat = {"ms": 1000}
    makineler = [
        SnowflakeTarzi(m, lambda: saat["ms"]) for m in range(4)
    ]
    idler = set()
    toplam = 0
    for ms in range(1000, 1100):
        saat["ms"] = ms
        for u in makineler:
            for _ in range(250):
                idler.add(u.al())
                toplam += 1
    print("üretilen = %d, tekil = %d" % (toplam, len(idler)))
    ornek = makineler[2]
    saat["ms"] = 5000
    x = ornek.al()
    print("örnek ID : %d" % x)
    print("base62   : %s (%d karakter)" % (kodla(x), len(kodla(x))))
    print("zaman    : %d ms" % (x >> 22))
    print("makine   : %d" % ((x >> 12) & 1023))
    print("sıra     : %d" % (x & 4095))
```

```python
if __name__ == "__main__":
    sayac_uzunlugu()
    hash_cakisma()
    snowflake_demo()
```

Çıktı:

```term
$ python b41_kisaltici.py
Sayaç -> kod uzunluğu (base62)
           1 -> 1        (1 karakter)
          61 -> Z        (1 karakter)
          62 -> 10       (2 karakter)
        3843 -> ZZ       (2 karakter)
        3844 -> 100      (3 karakter)
     1000000 -> 4c92     (4 karakter)
  1000000000 -> 15FTGg   (6 karakter)
Kontrol: coz(kodla(n)) == n: True

Kırpılmış hash, 32 bit, 1000000 URL
ölçülen çakışan kayıt : 118
beklenen (doğum günü) : 116.4

Snowflake tarzı üretici (sabit saat, 4 makine)
üretilen = 100000, tekil = 100000
örnek ID : 20971528192
base62   : mTgouI (6 karakter)
zaman    : 5000 ms
makine   : 2
sıra     : 0
```

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

## Çözümlü Örnekler

Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntü, iyileştir, doğrula. Doğrulama adımında bir elle iz tablosu vardır. Her örneğin sonundaki soruyu kâğıtta çöz; yapay zekâ kullanmadan cevaplayabildiğin an, konu sende yerleşmiş demektir.

### Örnek 1 (★): Yer istasyonunda kullanılabilirlik hedefi

**Adım 1 — Anla.** Bir İHA'nın veri hattı üç parçadan oluşuyor: sensör okuması (kullanılabilirlik `0,999`), filtre (`0,998`) ve yer istasyonuna aktarım. Yer istasyonu tek bir sunucu olarak kurulursa kullanılabilirliği `0,99` olur. Gereksinim, uçtan uca kullanılabilirliğin en az `0,996` olmasıdır. Soru: hangi yapı bu hedefi sağlar ve ne kadar yıllık kesinti bırakır?

**Adım 2 — Örnekle.** Önce en basit yapı: üç bileşen de seri bağlı, yer istasyonu tek kopya. Sonra yer istasyonunu iki kopya yapalım; kopyalar bağımsız varsayılsın. Son olarak filtreyi de iki kopyalı yapalım.

**Adım 3 — Kaba çöz.** Seri zincirde kullanılabilirlikler çarpılır. Tek yer istasyonu: `0,999 x 0,998 x 0,99 = 0,987032`. Bu hedefin altında. İki yer istasyonu kopyası paralel bloktur: `1 - (1 - 0,99)^2 = 0,9999`. Zincir: `0,999 x 0,998 x 0,9999 = 0,996902`. Hedefi geçti.

**Adım 4 — Örüntü.** Paralel blok, seri zincirin en zayıf halkasını iyileştirir. Ama zincirin geri kalanı bir tavan koyar: yer istasyonu paralel olsa bile toplam, seri bileşenlerin çarpımı olan `0,997002`'yi aşamaz. Darboğaz artık yer istasyonu değil, filtredir. Bu, tasarımda "en zayıf halka"nın yer değiştirmesi demektir.

**Adım 5 — İyileştir.** Filtreyi de iki kopyalı yapalım: paralel blok `1 - (1 - 0,998)^2 = 1 - 0,002^2 = 0,999996`. Sensör tek kalsın. Zincir: `0,999 x 0,999996 x 0,9999 = 0,998896`. Artık darboğaz sensördür; bunu daha fazla yedekle (yedek sensör) iyileştirmek mümkündür, ama her yedek bir maliyet ve bir tutarlılık sorunu getirir.

**Adım 6 — Doğrula.** Her yapının yıllık kesintisini `(1 - A) x 8 760` ile hesapla:

| Yapı | Hesap | Toplam `A` | Yıllık kesinti (saat) | Hedef (`>= 0,996`) |
|---|---|---|---|---|
| Tek yer istasyonu | `0,999 x 0,998 x 0,99` | 0,987032 | 113,6 | Hayır |
| İki yer istasyonu | `0,999 x 0,998 x 0,9999` | 0,996902 | 27,14 | Evet |
| Filtre ve yer istasyonu yedekli | `0,999 x 0,999996 x 0,9999` | 0,998896 | 9,67 | Evet |

Tablo, iki yedeklemenin de hedefi geçtiğini ve ikincisinin kesintiyi yaklaşık yüzde 64 azalttığını gösteriyor (27,14 saatten 9,67 saate). Bu sayıların hepsi bağımsızlık varsayımıyla alındı; ortak neden arızası ekleyen bir gerçek hesap, bu kazançları azaltır.

**Bunu AI'sız yazabilir misin?** Sensör `0,995`, filtre `0,999` ve yer istasyonu iki kopyalı (her biri `0,99`) olsun. Uçtan uca kullanılabilirliği hesapla, zayıf halkanın hangisi olduğunu söyle ve yıllık kesintiyi bul.

### Örnek 2 (★★): Daha büyük bir İHA filosu için kapasite ve bağlantı sayısı

**Adım 1 — Anla.** Filo 60 İHA'dan oluşuyor; her biri 50 Hz ile saniyede 50 paket üretiyor. Her paket 300 bayt, sıkıştırma oranı 4:1. Soru: ham ve sıkıştırılmış veri hızı nedir, günlük ve yıllık depolama ne kadar, ve bir bağlantı ile bu paketleri göndermek yeter mi?

**Adım 2 — Örnekle.** Tek bir İHA saniyede 50 paket gönderiyor. Yani her paket 20 milisaniyede bir üretiliyor. Filonun toplam paket hızı: 60 araç çarpı 50 paket/s.

**Adım 3 — Kaba çöz.** Paket hızı `60 x 50 = 3 000` paket/s. Ham bayt hızı `3 000 x 300 = 900 000` bayt/s, yani `0,9` MB/s. Bit cinsinden `0,9 x 8 = 7,2` Mbit/s; tepe (2 kat) `14,4` Mbit/s. Günlük ham veri `900 000 x 86 400 = 77,76` GB; 4:1 sıkıştırmayla `19,44` GB/gün. Yıllık `19,44 x 365 = 7 096` GB, yani yaklaşık `7,1` TB. Her paket için sunucu süre bütçesi `1 / 3 000` s, yani `333` mikrosaniye.

**Adım 4 — Örüntü.** Bağlantı kararını Bölüm 41.3'teki gibi verelim. Tek bağlantıda her paket bir tur gerektiriyorsa ve tur `0,5` ms ise, bir bağlantı saniyede en fazla `2 000` paket gönderir. Filo `3 000` paket/s ürettiği için iki bağlantı gerekir. Bant genişliği bu ölçekte sorun değil; darboğaz tur sayısıdır.

**Adım 5 — İyileştir.** Paketleri beşerli gruplar hâlinde göndersek, tur sayısı `3 000 / 5 = 600` tur/s'ye düşer ve tek bağlantı yeter. Bedeli gecikmedir: beşinci paketin üretilmesini beklemek gerekir. 50 Hz'de paketler 20 milisaniye aralıklıdır; ilk paket, grubun dolmasını `4 x 20 = 80` milisaniye bekler. Bu, bir kontrol döngüsü için kabul edilebilir mi? Cevap görevin gereksinimine bağlıdır; burada bu bir takastır ve kararı gereksinim verir.

**Adım 6 — Doğrula.** Sonuçları tek tabloda topla ve birim tutarlılığını kontrol et:

| Ölçü | Hesap | Sonuç | Birim kontrolü |
|---|---|---|---|
| Paket/s | `60 x 50` | 3 000 | paket/s |
| Ham bayt/s | `3 000 x 300` | 900 000 | bayt/s |
| Ham bit/s | `900 000 x 8` | 7,2 Mbit/s | bit/s |
| Günlük ham | `900 000 x 86 400` | 77,76 GB | bayt/gün |
| Günlük sıkıştırılmış | `77,76 / 4` | 19,44 GB | bayt/gün |
| Yıllık sıkıştırılmış | `19,44 x 365` | 7 096 GB (7,1 TB) | bayt/yıl |
| Paket başı bütçe | `1 / 3 000` | 333 µs | s/paket |
| Bağlantı sayısı | `3 000 / 2 000` | 1,5 → en az 2 | bağlantı |

Son satırda 1,5'i iki olarak yukarı yuvarlamak zorundasın; bağlantı sayısı kesirli olamaz. Bu, kapasite hesabının sonunda hep tekrarlanacak bir ilkedir: tahmin bir sayı verir, ama yerleşim onu tam sayıya çevirir.

**Bunu AI'sız yazabilir misin?** Filo 80 İHA, 25 Hz, 200 bayt, sıkıştırma 5:1 olsun. Paket hızını, ham bit hızını, yıllık sıkıştırılmış depolamayı ve tek bağlantıda gereken en az bağlantı sayısını (tur süresi 0,5 ms) hesapla.

### Örnek 3 (★★): M/M/1 kuyruğunda bekleme süresinin kullanım oranıyla değişimi

**Adım 1 — Anla.** Tek bir sunucuya saniyede `lambda` istek geliyor; sunucunun hizmet hızı `mu = 1` (birim iş/s) olsun. Kullanım oranı `rho = lambda`. Soru: `rho` 0,5, 0,8, 0,9 ve 0,99 olduğunda ortalama sistem süresi `W` ne olur ve simülasyon bunu doğruluyor mu?

**Adım 2 — Örnekle.** `rho = 0,8` için `lambda = 0,8` istek/s. Her işin ortalama hizmet süresi 1 saniye. Önce bu durumda ilk üç işi kendimiz izleyelim; sonra formülü uygulayalım.

**Adım 3 — Kaba çöz.** Formül: `W = 1 / (mu - lambda)`. `rho = 0,5` için `W = 1 / 0,5 = 2`. `0,8` için `1 / 0,2 = 5`. `0,9` için `1 / 0,1 = 10`. `0,99` için `1 / 0,01 = 100`. Bu, hizmet süresinin 2, 5, 10 ve 100 katıdır.

**Adım 4 — Örüntü.** Payda `1 - rho`'dur. `rho` 1'e yaklaştıkça payda sıfıra gider ve `W` hızla büyür. Doğrusal bir artış değil, hiperbolik bir patlama: `rho` 0,5'ten 0,9'a iki katına yakın çıkarken `W` 5 kat artar; 0,9'dan 0,99'a yalnızca 0,09 artarken `W` 10 kat artar.

**Adım 5 — İyileştir.** Formülü bir simülasyonla doğrulamak için Lindley yinelemesini kullanırız: `bekleme_k = max(0, bekleme_(k-1) + hizmet_(k-1) - aralik_k)`. Bu, gerçek simülasyonun çekirdeğidir. Bölüm 41.6'daki betik bu yinelemeyi `rho = 0,8` için çalıştırır ve ilk altı işin izini verir.

**Adım 6 — Doğrula.** Simülasyonun ilk dört işini elle izle (çıktı `b41_mm1.py iz` komutundan):

| İş | Varış | Bekleme (Lindley) | Ayrılış | Sistemde | Elle kontrol |
|---|---|---|---|---|---|
| 1 | 6,028 | 0,000 | 6,132 | 0,104 | `6,132 - 6,028 = 0,104` |
| 2 | 6,467 | 0,000 | 6,772 | 0,305 | `6,772 - 6,467 = 0,305` |
| 3 | 7,062 | 0,000 | 8,335 | 1,273 | `8,335 - 7,062 = 1,273` |
| 4 | 7,866 | 0,469 | 11,707 | 3,841 | bekleme `8,335 - 7,866 = 0,469` |

Dördüncü iş, üçüncünün ayrılış zamanında (8,335) sisteme girmeye hazır olur; varışı 7,866 olduğundan bekler: `0,469`. Sonra hizmet süresi (`11,707 - 8,335 = 3,372`) ile sistemde kalma süresi `3,841` eder (`0,469 + 3,372`). Tablo, yinelemenin doğru kurulduğunu gösteriyor. Uzun simülasyonun sonucu da tabloda: `rho = 0,5` için ölçülen `1,998`, `0,8` için `5,006`, `0,9` için `10,108`, `0,99` için `99,251`; teorik değerler `2`, `5`, `10`, `100`.

**Bunu AI'sız yazabilir misin?** `mu = 2` (birim iş/s) ve `lambda = 1,6` için `rho`'yu, `W`'yi ve `L`'yi (Little yasasıyla) kâğıtta hesapla. Sonra `lambda = 1,8` için `W`'nin neden yaklaşık iki katına çıktığını açıkla.

### Örnek 4 (★★★): Devre kesicinin bir hata dizisi boyunca durum izi

**Adım 1 — Anla.** Devre kesici üç durumlu: KAPALI, AÇIK, YARI AÇIK. Eşik `3` (ardışık hata sayısı), bekleme süresi `5` tick. Her tick'te bir çağrı yapılır ve arka ucun sonucu dizide `B` (başarı) ya da `H` (hata) olarak verilir. Reddedilen çağrılarda arka uca gidilmez, bu yüzden dizideki harf yalnızca bir çağrı yapılırsa geçerlidir. Soru: 20 tick boyunca devrenin durum izi nedir?

**Adım 2 — Örnekle.** Dizi: `BHHHHBHHHBBBBBBHHBBB`. İlk üç tick'e bakalım: `B` (tick 0) başarılı, KAPALI kalır. `H` (tick 1), `H` (tick 2), `H` (tick 3): üçüncü ardışık hata eşiğe ulaşır ve devre AÇIK olur. Açılış anı `t = 3`'tür.

**Adım 3 — Kaba çöz.** AÇIK durumunda `t - acilis < bekleme` ise istek reddedilir. Tick 4 için `4 - 3 = 1 < 5`, reddet. Tick 5, 6, 7 için de `2`, `3`, `4` ile reddet. Tick 8'de `8 - 3 = 5`, bekleme doldu: devre YARI AÇIK'a geçer ve bu tick'in çağrısı tek deneme olur. Dizideki `H` başarısız olur ve devre yeniden AÇIK olur; yeni açılış anı `t = 8`.

**Adım 4 — Örüntü.** Her AÇIK dönemi, son açılıştan `bekleme` tick sonra YARI AÇIK'ı tetikler. YARI AÇIK'ta yalnızca bir deneme yapılır: başarılıysa KAPALI'ya, başarısızsa AÇIK'a döner. KAPALI'da ise başarı sayacı ardışık hatayı sıfırlar; bu yüzden tek tek serpiştirilmiş hatalar devreyi açmaz.

**Adım 5 — İyileştir.** Bekleme süresi çok kısa seçilirse (ör. `bekleme = 1`), devre her tick'te AÇIK ile YARI AÇIK arasında gidip gelir ve arka uca sürekli deneme gider; bu tam olarak yapmak istemediğimiz şeydir. Çok uzun seçilirse arka uç toparlanmış olsa bile devre kapalı kalır. Bu ikisi arasında bir değer, gözlemlenen toparlanma süresine göre seçilir.

**Adım 6 — Doğrula.** Dizinin tamamı için elle iz tablosu (betik çıktısıyla birebir aynı):

| Tick | Önce | Dizi harfi | Sonuç | Sonra |
|---|---|---|---|---|
| 0 | KAPALI | B | BAŞARI | KAPALI |
| 1, 2 | KAPALI | H | HATA | KAPALI |
| 3 | KAPALI | H | HATA (3. ardışık) | AÇIK |
| 4-7 | AÇIK | H, B, H, H | REDDEDİLDİ | AÇIK |
| 8 | AÇIK (bekleme doldu) | H | DENEME HATA | AÇIK (`acilis = 8`) |
| 9-12 | AÇIK | B, B, B, B | REDDEDİLDİ | AÇIK |
| 13 | AÇIK (bekleme doldu) | B | DENEME BAŞARI | KAPALI |
| 14 | KAPALI | B | BAŞARI | KAPALI |
| 15, 16 | KAPALI | H, H | HATA (2 ardışık, eşik değil) | KAPALI |
| 17-19 | KAPALI | B, B, B | BAŞARI | KAPALI |

Tabloda iki kritik nokta var: tick 8'deki deneme hatası, açılış anını 8'e taşıdı ve bekleme yeniden başladı; tick 15-16'daki iki hata, eşiğe (3) ulaşmadan tick 17'deki başarıyla sıfırlandı. Eşik ve bekleme süresi, bu tablodaki her geçişi belirleyen iki sayıdır.

**Bunu AI'sız yazabilir misin?** Aynı dizi için `bekleme = 2` seçilseydi tabloda neyin değişeceğini söyle. Tick 4'ten itibaren hangi tick'lerde YARI AÇIK görülür ve ilk deneme hangi tick'te yapılır?

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçları **yasak**. Amaç, bir yük dengeleyiciyi ya da URL kısaltıcıyı senin kafanla tasarlayıp ölçebilmen. Takıl, kâğıda çiz, küçük testler yaz; çözümü dışarıdan alma. Ölçtüğün sayılar, bu bölümdeki sayılarla karşılaştırıldığında farklıysa, nedenini bul; bu da projenin bir parçasıdır.
:::

### Proje 1 (★★): Kendi yük dengeleyici simülatörün

**Amaç:** Bölüm 41.5'teki ayrık olay simülatörünü kendi kodunla yeniden yaz ve farklı bir küme için karşılaştır: üç sunucu, hızları 1, 2 ve 4. Politikaları (sırayla, ağırlıklı, en az bağlantı, iki seçim) ve bir de `rho` taramasını uygula.

**Beklenen davranış:** Program, verilen bir `rho` ve politika için p50, p99 ve en uzun kuyruğu yazdırır. Aynı tohumla iki kez çalıştırıldığında sonuç birebir aynıdır. Bir politika kararsız olduğunda (ortalama gecikme istek sayısıyla büyüyorsa) programın bunu ayırt edebilmesi gerekir; bunun için aynı deneyi iki farklı uzunlukta (ör. 50 000 ve 100 000 istek) çalıştırıp p99'un artıp artmadığına bakabilirsin.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Sunucuların her birini bir `deque` ile temsil et; her girişin tamamlanma zamanını tut. Kuyruk uzunluğunu sayarken baştan eski zamanları at. Politikaları tek bir fonksiyonda `if/elif` zinciriyle seç; her politika yalnızca hangi sunucunun seçileceğini döndürsün. Rastgelelik için tek bir `random.Random(41)` örneği kullan. Kararsızlık sınırını hesaplamayı unutma: tüm sunucuların toplam kapasitesi ile yük oranını karşılaştırarak zayıf sunucunun `rho_i`'sini bul.

**Başarı kriterleri:**
- Üç sunucu hızlarında (1, 2, 4), `rho = 0,8` için ağırlıklı politikanın p99'u sırayla politikanın p99'undan belirgin biçimde küçük; oranı raporuna yaz.
- 100 sunucuda iki seçimin en uzun kuyruğu, rastgele seçiminkinden belirgin biçimde küçük (aynı tohum, aynı yük); iki değeri raporla.
- Sırayla politikanın p99'u `rho` 0,5'i geçtiğinde iki katından fazla artıyor ve bu artış, istek sayısını artırınca da sürüyor (kararsızlık).

### Proje 2 (★★★): Bir URL kısaltıcının tasarımı, prototipi ve yük testi

**Amaç:** Bir URL kısaltıcının tam tasarım dokümanını yaz ve küçük bir çalışan prototip geliştir. Prototip, base62 kodlamayı, bir ID üreticisini, bir LRU önbelleğini ve bir jeton kovası hız sınırını içersin. Son olarak prototipe yük uygulayıp darboğazı bul.

**Beklenen davranış:** Kullanıcı uzun bir URL verir, kısa bir kod alır. Kısa kod ile GET isteği 301 (kalıcı) ya da 302 (geçici) yanıtıyla uzun URL'ye yönlendirir. Kısa kodun uzunluğu, üretilebilecek kayıt sayısına göre seçilmiş olmalı. Okuma ağırlıklı yük altında önbellek isabeti ölçülmeli. Bir istemcinin saniyede çok sayıda istek göndermesi, jeton kovası ile sınırlanmalı.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Tasarım dokümanında Şekil 41.9'daki bileşenleri ve her birinin gereksinim karşılığını yaz; kısa kod için base62'nin kaç karakterle kaç kayıt desteklediğini hesapla (`62^7`'nin büyüklüğünü ve bir sayaçtan kaç yıl süreceğini düşün). ID üreticisi için sayaç, kırpılmış hash ve Snowflake tarzı üretici arasında karşılaştırma yap; hangisinin çakışma ve koordinasyon açısından ne getirdiğini tablo hâline getir. Yük testi için bir istemci havuzu ile önceden belirlenmiş bir hızda istek gönder; p50, p99 ve hata oranını Bölüm 31.9'daki gibi ölç. Darboğazı bulmak için hangi bileşenin önce doygunluğa ulaştığını (USE yöntemi) izle.

**Başarı kriterleri:**
- Tasarım dokümanı, en az üç gereksinim (gecikme, verim, kullanılabilirlik) için bir sayı ve bu sayıyı karşılayan bir karar içeriyor; her karar için bir takas yazılı.
- Base62 kodlama ve çözme, 100 000 rastgele sayıda birebir tutarlı (`coz(kodla(n)) == n`).
- Yük testinde, okuma ağırlıklı trafikte önbellek isabeti ölçülmüş ve kaynak çağrılarının oranı bu isabetle tutarlı.
- Hız sınırı, belirlenen kovayı aşan istemcilerin isteklerini reddediyor; sınır altındaki istemcilerin isteklerini reddetmiyor.
- Darboğaz raporu, hangi bileşenin ilk doygunluğa ulaştığını ve bunun hangi ölçümle kanıtlandığını söylüyor.

## Ek Alıştırmalar

Aşağıdaki problemlerin çözümü bu kitapta yok. Önce kâğıda, sonra editöre geç; yapay zekâ yasak. Zorluk etiketine göre sırala. Çoğu klasik sistem tasarımı mülakat sorusudur; bu soruları sesli düşünerek ve süreyi sınırlayarak çöz.

1. **★ — Seri bileşenler.** Üç bileşen seri bağlı, her birinin kullanılabilirliği `0,998`. Toplam kullanılabilirlik nedir ve yıllık kesinti kaç saattir? Dördüncü bir `0,998` bileşeni eklersen kesinti ne kadar artar?
2. **★ — Hata bütçesi.** Bir hizmet 30 günlük pencerede `0,9995` SLO'suna sahip. Bu pencerede izin verilen kesinti kaç dakikadır? Bir olayda 25 dakika kesinti olduysa, bütçenin yüzde kaçı kullanılmıştır?
3. **★ — Little yasası.** Bir sunucu saniyede 400 istek alıyor ve ortalama yanıt süresi 80 milisaniye. Ortalamada kaç istek aynı anda işleniyor? Bu sayı, sunucunun en az kaç eşzamanlı işçiye ihtiyacı olduğunu nasıl gösterir?
4. **★ — Yeniden deneme sayısı.** Bir istemci ilk istekten sonra en fazla 4 kez yeniden deniyor. Taban bekleme 0,5 saniye, her seferinde iki katına çıkıyor, jitter yok. Toplam bekleme kaç saniyedir? Aynı 1000 istemci aynı anda başarısız olursa, her yeniden denemede sunucuya kaç istek gelir?
5. **★★ — Mülakat: kısa kod uzunluğu.** Bir URL kısaltıcı 10 milyar URL'yi desteklemek zorunda. Base62 ile en az kaç karakter gerekir? Cevabını `62^k >= 10^10` eşitsizliğini çözerek ver.
6. **★★ — Mülakat: yayılım.** Bir sayfa 20 servise paralel istek atıyor. Her servisin p99'u 50 milisaniye. Sayfanın en az bir servisten yavaş yanıt alma olasılığı nedir (`1 - 0,99^20`)? Bu sonuç, p99 hedefini nasıl değiştirmeni gerektirir?
7. **★★ — Mülakat: sürü etkisi.** Bir mikroservis 2 saniye kapalı kaldı ve 2000 istemci hemen yeniden deniyor. Sabit geri çekilmeyle ve tam jitter ile ne olacağını birkaç cümleyle anlat. Hangisi neden daha iyi?
8. **★★ — M/M/1 hesabı.** Tek sunucunun hizmet hızı 1 istek/s, gelen hız 0,95 istek/s. Ortalama sistem süresi `W` kaçtır? Bu sistemi yüzde 60 kullanıma indirmek için hizmet hızı ne olmalıdır?
9. **★★★ — Mülakat: tam bir kez teslim.** Bir sistem "her mesaj tam bir kez işlenir" diyor. Bu iddiayı nasıl sorgularsın? Hangi hata senaryosunda iki kez işleme ya da hiç işlememe olabilir? Çözümün neden idempotent tüketici olduğunu açıkla.
10. **★★★ — Mülakat: beğeni sayacı.** Bir gönderinin beğeni sayısını milyonlarca eşzamanlı kullanıcı artırıyor. Tek bir satırı kilitleyen basit bir `UPDATE` neden yetmez? Yazma yükünü dağıtan iki tasarım öner ve her birinin okuma doğruluğuna etkisini yaz.
11. **★★★ — Mülakat: Raft kümesi.** Beş düğümlü bir Raft kümesinde iki düğüm çöktü. Yazma yapılabilir mi? Üç düğüm çökerse ne olur? Her durum için çoğunluk hesabını yaz.
12. **★★★ — Mülakat: önbellek ve değişim.** Bir ürün fiyatı değiştiğinde kullanıcıların birkaç saniye içinde yeni fiyatı görmesi gerekiyor. Önbellek TTL'i 60 saniye. Hangi kalıbı seçersin (cache-aside, write-through, olay tabanlı geçersiz kılma) ve yarış koşulu nasıl oluşabilir?

## Kod Okuma Egzersizi

Bu bölümde bir kuyruğun **gerçek** gerçeklemesini okuyacaksın. Kaynak: CPython **3.12.10**, `Lib/asyncio/queues.py`. Dosya, yerel Python 3.12.10 kurulumundan alındı ve birebir kopyalandı; yalnızca satır sonları Windows'taki CRLF'ten LF'ye çevrildi. **Sadeleştirme:** sınıf ve metotların docstring'leri çıkarıldı (her parçada nerede olduğunu belirttik); 70 karakteri aşan iki yorum satırı bölündü, ve bir yorum kodun üstüne taşındı. Hiçbir kod satırı silinmedi ya da değiştirilmedi.

Önce kuyruğun kurulumu ve `full()` kontrolü. `maxsize` değeri sıfır ya da negatifse kuyruk sınırsızdır.

```python
    def __init__(self, maxsize=0):
        self._maxsize = maxsize

        # Futures.
        self._getters = collections.deque()
        # Futures.
        self._putters = collections.deque()
        self._unfinished_tasks = 0
        self._finished = locks.Event()
        self._finished.set()
        self._init(maxsize)

    def full(self):
        if self._maxsize <= 0:
            return False
        else:
            return self.qsize() >= self._maxsize
```

Şimdi `put()`. Kuyruk dolu olduğunda üretici bir `Future` oluşturur, bu `Future`'ı bekleyenler listesine koyar ve uyanana kadar bekler. Döngünün `while` olması, uyandıktan sonra kuyruğun yeniden dolu olabileceği için gereklidir.

```python
    async def put(self, item):
        while self.full():
            putter = self._get_loop().create_future()
            self._putters.append(putter)
            try:
                await putter
            except:
                # Just in case putter is not done yet.
                putter.cancel()
                try:
                    # Clean self._putters from canceled putters.
                    self._putters.remove(putter)
                except ValueError:
                    # The putter could be removed from
                    # self._putters by a previous get_nowait call.
                    pass
                if not self.full() and not putter.cancelled():
                    # We were woken up by get_nowait(), but can't take
                    # the call.  Wake up the next in line.
                    self._wakeup_next(self._putters)
                raise
        return self.put_nowait(item)
```

Son olarak `put_nowait()`: kuyruk doluysa hemen `QueueFull` fırlatır, değilse öğeyi ekler, tamamlanmamış iş sayacını artırır ve bekleyen bir tüketiciyi uyandırır.

```python
    def put_nowait(self, item):
        if self.full():
            raise QueueFull
        self._put(item)
        self._unfinished_tasks += 1
        self._finished.clear()
        self._wakeup_next(self._getters)
```

**Sorular — cevaplamadan geçme:**

1. `full()` neden `maxsize <= 0` için `False` döndürüyor? Bu varsayılan değerin sonucu, bir üretici için ne anlama gelir ve bu, Bölüm 41.8'deki bellek riskiyle nasıl ilişkilidir?
2. `put()` içinde neden `if` yerine `while self.full():` kullanılıyor? Uyanan bir üreticinin kuyruğu hâlâ dolu bulabilmesi hangi durumda mümkündür?
3. `put()`nin `except` bloğunda neden `self._wakeup_next(self._putters)` çağrılıyor? Bu çağrı yapılmazsa hangi "kaybolan uyandırma" oluşur ve Bölüm 27.9'daki koşul değişkeni fikri bu durumda neyi çözer?
4. `put_nowait()` içinde `_unfinished_tasks` artırılıyor ve `_finished` temizleniyor. Bu iki alan, `join()` çağrısını nasıl destekler? Üreticinin "tüm işler bitti" sinyalini almasını sağlayan mekanizmayı tek cümleyle anlat.
5. Geri basınç (backpressure) bu kodda nasıl gerçekleşiyor? `maxsize` dolduğunda, üretici mi yavaşlar yoksa tüketici mi? Bu tasarım, Bölüm 41.8'de anlatılan "yük atma" (load shedding) seçeneğinden neden farklıdır?
6. Varsayılan `maxsize=0` ile çalışan bir üretici, tüketicisi yavaşladığında ne olur? Bu senaryoda hangi sistem kaynağı ilk tükenir ve sistem kullanıcıya hangi belirtiyle kendini gösterir?

## Bölüm Özeti

- Sistem tasarımı, gereksinimden takasa uzanan bir süreçtir; her adım somut bir sayı ister ve tasarım kararları bir bedel taşır.
- Kullanılabilirlik dokuzları, yıllık ve 30 günlük kesinti sürelerine dönüşür; hata bütçesi, güvenilirlik ile değişim hızı arasındaki çatışmayı bir sayıya bağlar. Seri bileşenler kullanılabilirliği çarpar, paralel kopyalar ise bağımsızlık varsayımı altında kesintiyi çarpar.
- Kapasite tahmini, kullanıcıdan istek hızına, oradan bant genişliğine ve depolamaya uzanan kaba bir hesaptır; gecikme sayıları büyüklük mertebesini verir ve bağlantı sayısı gibi tam sayı kararlarını belirler.
- Yük dengeleme politikaları arasındaki fark, kararlılık sınırıyla başlar: hızı bilmeyen politikalar zayıf sunucularda kararsızlaşır. İki rastgele seçimin gücü, tam bilgi olmadan kuyruk dengesizliğini büyük ölçüde kırar.
- Kuyruk teorisinde Little yasası (`L = lambda W`) her kararlı sistemde geçerlidir; M/M/1'de `W = 1/(mu - lambda)` olduğundan kullanım yüzde 100'e yaklaştıkça gecikme patlar.
- Önbellek katmanları, isabet oranı ve yayılım altındaki yüzdelikler birlikte düşünülmelidir; stampede'i tekil uçuş ya da jitter ile önlersin.
- Dayanıklılık kalıpları (zaman aşımı, jitter'lı yeniden deneme, devre kesici, bölme, hız sınırı) yavaşlığın zincirleme yayılmasını durdurur; devre kesici, Bölüm 22'deki State kalıbının bir uygulamasıdır.
- Veri katmanında çoğaltma, bölümleme ve dağıtık işlemler tutarlılık ile gecikme arasında takas yapar; Raft gibi konsensüs algoritmaları yalnızca küçük ama kritik durumu tutarlı tutmak için kullanılır.
- Gözlemlenebilirlik, tasarımın parçasıdır: ortalama yerine yüzdelik ölçmek ve yayılım etkisini hesaba katmak gerekir.

**Sonraki bölümde:** Bölüm 42 — Docker & Deployment. Bu bölümde tasarladığın bileşenler bir konteyner içinde nasıl paketlenir, bir CI/CD hattıyla nasıl dağıtılır ve mavi-yeşil ya da kademeli dağıtım stratejileriyle nasıl değiştirilir, bunları göreceğiz. Tasarımın her parçasının "nerede çalışacağı" sorusu, bu bölümün konusudur.

::: mulakat
Aşağıdaki sorular cevapsızdır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. Bir İHA yer istasyonu, uçaktan gelen telemetriyi kaybetmeden ve sırasız gelebilecek paketlerle birlikte nasıl tasarlanır? Hangi bileşen sırayı, hangisi tekrarı ele alır?
2. Bir sistemde gecikme hedefi p99 ile tanımlanıyor ama bir ekip "ortalama 20 ms, yeterli" diyor. Bu iki cümlenin çelişmediği bir dağılım düşünebilir misin? Gerçek sistemde bunu nasıl görürsün?
3. Bir yük dengeleyici, sağlık kontrolüne 200 OK dönen ama her isteği 10 saniyede yanıtlayan bir sunucuyu sağlıklı sayıyor. Bunu nasıl tespit edersin ve hangi politikayı eklersin?
4. Üç servisli bir zincirde (A, B, C) her servisin zaman aşımı 1 saniye. A, C'nin cevabını ne kadar bekleyebilir ve bu değer zincirde nasıl tasarlanmalı?
5. Bir devre kesici hiç açılmıyor ama arka uç sürekli hata veriyor. Hangi üç ölçüm eksik olabilir ve eşiğin neden yanlış ayarlandığını nasıl anlarsın?
6. Bir sistemin çoğu isteği önbellekten yanıt alıyor (isabet yüzde 98), ama yeni deploy sonrası veritabanı çöküyor. Hangi olayın olduğunu ve bunu önlemek için hangi tasarım değişikliğinin gerektiğini düşün.
7. Monolit ile mikroservis arasında bir karar verirken, hangi üç ölçü (ekip, ölçek, dağıtım sıklığı) yeterli ve hangisi tek başına yanıltıcı? Savunma sanayiinde sertifikasyon bu kararı nasıl etkiler?
:::
