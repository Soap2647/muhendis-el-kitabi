%% kisim_no: V
%% kisim_ad: OOP & Yazılım Tasarımı
%% bolum_no: 21
%% baslik: SOLID

## Giriş: Kod yazmak kolay, değiştirmek zor

Kod ilk yazıldığında iyi görünür. Bir hafta sonra yeni bir sensör gelir, bir gün sonra raporun biçimi değişir, bir ay sonra aynı hesap iki yerde yapılmaya başlanır. Bu bölümün konusu, bu değişikliklerin maliyetini nasıl yöneteceğindir. Yazılımda değişim kaçınılmazdır; asıl soru, bir değişikliğin kaç dosyaya, kaç fonksiyona ve kaç teste yayılacağıdır.

Mülakatlarda "bu tasarımı değiştirmek kolay mı?" sorusu sık gelir. İyi bir cevap genellikle bağımlılık ve sorumluluk üzerine kurulur; SOLID tam olarak bu cevabın beş ayrı kuralıdır. Savunma sanayiinde de aynı ihtiyaç vardır: bir sensörün, bir haberleşme katmanının ya da bir karar algoritmasının değişmesi, sistemin geri kalanını yeniden doğrulamayı gerektirmemelidir. Değişim maliyeti, üretim ortamında doğrulama maliyetine dönüşür (genel bilgi).

Mert'in projelerinde de aynı sorun görünür. EV Dashboard sensör verisini okuyup kaydeden ve gösteren bir hat olarak düşünülürse, sensör türü değiştiğinde kaydetme ve gösterme kodunun da değişmesi gerekir mi? Bu bölümde bu soruyu, bir çamur topundan ayrışmış bir tasarıma dönüştürerek yanıtlayacağız. ÖZCE'deki codec seçimleri ve MertOS'taki komut yapısı da aynı türden kararlar içerir; komut kalıbını Bölüm 22'de ayrıntılı göreceksin.

SOLID, Robert C. Martin'in topladığı beş ilkenin baş harflerinden oluşan bir kısaltmadır; kısaltmanın Michael Feathers tarafından yaygınlaştırıldığı bilinir (genel bilgi). Beş ilke bir kural listesi değildir. Her biri aynı soruya farklı bir açıdan cevap verir: bir modül hangi nedenlerle değişir, değişiklikler hangi yönde yayılır ve sistemin hangi parçası kararlı kalmalıdır.

Bu bölümde her ilkeyi önce tanımlayıp sonra ihlal eden gerçekçi bir kod göstereceğiz. Ardından aynı değişiklik senaryosunu düzeltilmiş tasarımda yeniden çalıştırıp dosya, fonksiyon ve test sayılarını karşılaştıracağız. Sınıf, kalıtım, sanal fonksiyon ve soyut sınıfın mekaniği Bölüm 20'de anlatılıyor; burada onları tasarım kararı olarak kullanacağız.

::: not
Bölümdeki Python programları Python 3.12.10 ile çalıştırıldı. C ve C++ programları WSL'de gcc 13.3 ile `-Wall -Wextra` uyarı açık olarak derlendi ve `-fsanitize=address,undefined` ile de çalıştırıldı. Windows'ta `long` 4 bayttır (LLP64); bu yüzden C kodunda boyut için `size_t`, sayılar için `int` ve `double` kullandık. Ölçüm kodlarında rastgele sayı yoktur: sahte donanım değerleri sabit formüllerle ya da `42` tohumlu bir üreteçle üretilir, bu yüzden aynı kodu çalıştırdığında aynı sayıları alırsın.
:::

## 21.1 Değişim maliyeti: SOLID neden var?

Bir yazılım sisteminin değişim maliyeti, bir değişikliğin sistemin ne kadarına dokunduğuyla ölçülür. Dokunulan yer az ve yalıtılmışsa değişiklik ucuzdur. Her yerde iç içe bağımlılık varsa, tek bir satır bile geniş bir test ve doğrulama turu gerektirir. Bu duruma "çamur topu" (big ball of mud) denir. Çamur topunda sınır yoktur: her parça her parçayı bilir, bir yerdeki değişiklik zincirleme olarak başka yerleri bozar.

Martin'in dilinde kötü tasarımın üç belirtisi vardır: kırılganlık, sertlik ve dayanıksızlık (genel bilgi). Kırılganlık, bir değişikliğin beklenmeyen yerlerde hata üretmesidir. Sertlik, basit bir değişikliğin bile büyük çaba istemesidir. Dayanıksızlık, sistemin bir parçasını değiştirdiğinde başka bir parçasının çalışmaz hâle gelmesidir. SOLID bu üç belirtiye karşı beş ayrı kural verir; ortak amaç, bağımlılığın yönünü kontrol etmek ve değişim alanlarını birbirinden ayırmaktır.

Bir değişikliğin kaç yere dokunduğunu ölçmeden "bu tasarım kötü" demek tahmin yürütmektir. Bu yüzden her ilke için bir değişiklik senaryosu tanımlayıp sayacağız. Sayılar, ilkenin sağladığı kazancın ölçülebilir kanıtıdır. Bölüm 21.7'de bu ölçümün tamamını çalıştıracağız.

## 21.2 SRP: Tek değişim nedeni

Martin'in tanımı şöyledir: bir sınıfın değişmesi için yalnızca bir neden olmalıdır (Single Responsibility Principle, genel bilgi). Martin daha sonra bu tanımı, bir modülün yalnızca bir aktöre (değişiklik talep eden bir paydaş grubuna) karşı sorumlu olması biçiminde açıkladı. Bu ikinci ifade, "neden" kelimesinin ne anlama geldiğini netleştirir.

Yanlış anlaşılmanın kaynağı "tek iş yapar" cümlesidir. Her sınıfın tek bir metodu olması gerektiğini düşünürsen, ilkeyi kaba bir biçimde uygulamış olursun ve kod okunmaz hâle gelir. Asıl soru şudur: bu kodun değişmesini kim ya da hangi gereksinim tetikler? Rapor metninin biçimini tasarım ekibi, alarm eşiğini operasyon ekibi, ölçüm kaynağını donanım ekibi belirler. Bu üç ekibin değişiklikleri aynı sınıfa dokunuyorsa, o sınıfta üç ayrı değişim nedeni vardır.

Aşağıdaki sınıf, sensör ölçümlerinden bir rapor dosyası üretir. Ölçümler `olcum.py` modülünden gelir. Bu sınıf ise veriyi okumaktan alarm üretmeye kadar her şeyi kendisi yapar.

Önce, beş sorumluluğun tek bir sınıfta toplandığı hâli:

```python
"""ONCE: istatistik, bicim, dosya yazma ve alarm tek sinifta."""
from olcum import olcumleri_oku


class RaporYoneticisi:
    def __init__(self, sensorler, yol):
        self.sensorler = sensorler
        self.yol = yol

    def calistir(self):
        olcumler = olcumleri_oku(self.sensorler)
        if not olcumler:
            raise ValueError("olcum yok")
        sayilar = [d for _, d, _ in olcumler]
        ort = sum(sayilar) / len(sayilar)
        satirlar = ["%-10s %8.2f %s" % (t, d, b)
                    for t, d, b in olcumler]
        satirlar.append("ORT %.2f" % ort)
        with open(self.yol, "w", encoding="utf-8") as f:
            f.write("\n".join(satirlar) + "\n")
        alarmlar = ["ALARM: %s %.2f" % (t, d) for t, d, _ in olcumler
                    if t == "termistor" and d > 80.0]
        return ort, alarmlar
```

Bu sınıfta beş değişim nedeni vardır: veri (`olcumleri_oku` çağrısı), istatistik (ortalama), biçim (satır metni ve `ORT` satırı), dosya (`open` ve `write`) ve alarm (`80.0` eşiği). Bunların hepsi tek bir metot olan `calistir` içinde yaşar. Alarm eşiğini değiştirmek isteyen biri, biçimi değiştiren birinin kodunu da okumak zorunda kalır. Ayrım, metot sayısıyla değil değişim nedeniyle yapılır.

Düzeltmede her değişim nedenine ayrı bir modül veriyoruz. Orkestratör sınıf yalnızca adımları sırayla çağırır ve kendisi hesap yapmaz:

```python
"""Orkestrasyon: adimlari sirayla cagirir, kendisi hesap yapmaz."""
import alarm
import bicim
import istatistik


class RaporYoneticisi:
    def __init__(self, sensorler, yol):
        self.sensorler = sensorler
        self.yol = yol

    def calistir(self):
        olcumler = [s.olc() for s in self.sensorler]
        ort = istatistik.ortalama(olcumler)
        with open(self.yol, "w", encoding="utf-8") as f:
            f.write(bicim.metin(olcumler, ort))
        return ort, alarm.alarmlar(olcumler)
```

Ortalama hesabı, biçim ve alarm artık ayrı dosyalarda. Her biri tek bir fonksiyondan oluşur ve yalnızca kendi değişim nedenine tepki verir:

```python
"""Tek is: olcumlerin ortalamasi."""


def ortalama(olcumler):
    if not olcumler:
        raise ValueError("olcum yok")
    return sum(o.deger for o in olcumler) / len(olcumler)
```

```python
"""Tek is: olcumleri metin satirlarina cevirmek."""


def metin(olcumler, ort):
    satirlar = ["%-10s %8.2f %s" % (o.tur, o.deger, o.birim)
                for o in olcumler]
    satirlar.append("ORT %.2f" % ort)
    return "\n".join(satirlar) + "\n"
```

```python
"""Tek is: esigi asan olcumler icin alarm satiri uretmek."""


def alarmlar(olcumler):
    return ["ALARM: %s %.2f" % (o.tur, o.deger) for o in olcumler
            if o.esik is not None and o.deger > o.esik]
```

Şekil 21.1, iki tasarımın yapısını karşılaştırıyor. Dikkat et: dosya yazımı orkestratörde kaldı. Yazma yerinin değişmesi ayrı bir değişim nedeni olabilir; bu tasarımda yazmayı ayrı bir modüle taşımadık. Bu kararın bedeli Örnek 1'de tartışılacak.

![Şekil 21.1: SRP öncesi ve sonrası. Solda tek sınıfta beş değişim nedeni; sağda orkestratör ve her biri tek nedene tepki veren modüller.](gorseller/b21_srp_sorumluluk.png)

Düzeltilmiş tasarımda aynı işi yapan kod dört dosyaya dağıldı; bunun bir bedeli var. Import sayısı arttı, bir değişikliğin hangi dosyada olduğunu bulmak için iki dosyaya bakmak gerekebilir ve ufak bir betik için bu fazla mühendislik olabilir. SRP'yi ne zaman uygulamamalısın? Değişim nedeni tek ve kararlıysa, ekipte aktör ayrımı yoksa ve kod tek seferlik bir analiz betiğiyse, bölmek kazandırmaz. Bölme ölçütü satır sayısı değil, gerçek değişim nedenleridir.


## 21.3 OCP: Genişlemeye açık, değişime kapalı

Bertrand Meyer, 1988'de yayımladığı *Object-Oriented Software Construction* kitabında bu ilkeyi ortaya koydu (genel bilgi): yazılım varlıkları genişlemeye açık, değişime kapalı olmalıdır. Cümle ilk bakışta çelişkili görünür. Değişiklik yapmadan nasıl genişletebilirsin? Cevap, yeni davranışı mevcut kodun dışına yazıp onu bir soyutlama üzerinden bağlamaktır. Mekanizma üç parçadan oluşur: ortak bir arayüz, bu arayüzü uygulayan sınıflar (çok biçimlilik) ve hangi sınıfın seçileceğini belirleyen bir kayıt ya da fabrika.

Önce, yeni bir sensör türü için bir koşul dalının eklenmesi gereken hâli görelim. Okuma fonksiyonu tür adına bakıp hangi kalibrasyonun uygulanacağına karar verir:

```python
"""ONCE: ADC okuma ve kalibrasyon. Donus: (tur, deger, birim)."""


def _adc_oku(kanal):
    """Donanim yerine sahte okuma (gercekte SPI/ADC surucusu)."""
    return 1000 + 100 * kanal


def olcumleri_oku(sensorler):
    """[(tur, kanal)] -> [(tur, deger, birim)]"""
    sonuc = []
    for tur, kanal in sensorler:
        ham = _adc_oku(kanal)
        if tur == "termistor":
            deger, birim = ham * 0.1 - 40.0, "C"
        elif tur == "gerilim":
            deger, birim = ham * 3.3 / 4095, "V"
        else:
            raise ValueError("bilinmeyen sensor: %s" % tur)
        sonuc.append((tur, deger, birim))
    return sonuc
```

Bu tasarımda her yeni tür fonksiyona yeni bir `elif` dalı ekler. Basınç sensörü için değişiklik üç yerde yapılır: `olcumleri_oku` içine yeni bir dal, `rapor.py` içindeki alarm koşuluna yeni bir `or` kolu ve `app.py` içindeki sensör listesine bir satır. Ağrı şudur: çalışan kod değiştirilir. Bir ekip üyesi kalibrasyon mantığını düzeltirken bir başkası basınç dalını eklerse birleştirme çatışması ve yanlış kalibrasyon riski birlikte doğar. Bölüm 21.7'de bu senaryonun sayımını yapacağız. Sonuç şaşırtıcı olacak: bu tasarımda üç dosya değişir ama hiçbir mevcut test kırılmaz. Test kırılmaması güvenli olduğu anlamına gelmez; testler yalnızca yazıldıkları davranışı kontrol eder.

Düzeltmede tür ile sınıf arasına bir kayıt tablosu koyuyoruz. Her sensör sınıfı kendi dosyasında bir dekoratörle (Bölüm 3.8) tablonun içine kendini yazar:

```python
"""Eklenti kaydi: yeni sensor sinifi kendini bu tabloya ekler."""
SENSORLER = {}


def kaydet(tur):
    def sar(sinif):
        SENSORLER[tur] = sinif
        return sinif
    return sar
```

Dekoratör, bir sınıfı ya da fonksiyonu alıp döndüren fonksiyondur. `@kaydet("termistor")` satırı, sınıf tanımından hemen sonra `TermistorSensor = kaydet("termistor")(TermistorSensor)` yazmakla aynıdır. Aşağıdaki sensör dosyası, her türün birimini ve alarm eşiğini kendi sınıfında tutar:

```python
"""Somut sensorler. Her sinif kendi birimini ve esigini bilir."""
from kayit import kaydet
from sozlesme import Olcum


@kaydet("termistor")
class TermistorSensor:
    birim = "C"
    esik = 80.0

    def __init__(self, adc, kanal):
        self.adc = adc
        self.kanal = kanal

    def olc(self):
        ham = self.adc.oku(self.kanal)
        return Olcum("termistor", ham * 0.1 - 40.0,
                     self.birim, self.esik)


@kaydet("gerilim")
class GerilimSensor:
    birim = "V"
    esik = None

    def __init__(self, adc, kanal):
        self.adc = adc
        self.kanal = kanal

    def olc(self):
        ham = self.adc.oku(self.kanal)
        return Olcum("gerilim", ham * 3.3 / 4095,
                     self.birim, self.esik)
```

Yeni tür geldiğinde yeni bir dosya yazılır. Bu dosya kayıt tablosunu ve diğer sensör sınıflarını değiştirmez:

```python
"""Basinc sensoru: yeni tur, mevcut dosyalar degismeden eklenir."""
from kayit import kaydet
from sozlesme import Olcum


@kaydet("basinc")
class BasincSensor:
    birim = "kPa"
    esik = 110.0

    def __init__(self, adc, kanal):
        self.adc = adc
        self.kanal = kanal

    def olc(self):
        ham = self.adc.oku(self.kanal)
        return Olcum("basinc", ham * 0.05, self.birim, self.esik)
```

Sayım şöyledir: basınç senaryosunda sonra tarafında bir yeni dosya (`basinc.py`, 18 satır) oluşur ve kompozisyon kökü `app.py` içinde iki satır değişir (bir `import` ve yapılandırma listesi). Mevcut hiçbir fonksiyonun gövdesi değişmez. Şekil 21.2 iki yaklaşımı karşılaştırıyor.

![Şekil 21.2: Genişleme noktası. Solda her yeni tür fonksiyonun içine dal ekler; sağda kayıt tablosu yeni sınıfın kendini eklemesini bekler ve çekirdek kod değişmez.](gorseller/b21_ocp_kayit.png)

Bu tasarımın bedeli de vardır. Birincisi, kayıt bir yan etkidir: `sensorler.py` içe aktarılmadan `SENSORLER` tablosu boş kalır. Bu görünmeyen bir bağımlılıktır; bu yüzden `app.py` içinde `import sensorler` satırını bilerek yazdık ve yanına neden orada olduğunu not ettik. İkincisi, global bir tablo testleri kirletebilir; testler arasında tablonun temizlenmesi gerekebilir. Üçüncüsü, dekoratörü tanımayan biri sınıfın nereden kaydedildiğini bulmakta zorlanır.

OCP'yi ne zaman uygulamamalısın? Sabit iki tür varsa ve yeni tür beklenmiyorsa `if/elif` daha okunaklıdır. Genel bir pratik, aynı dallanmanın üçüncü kez tekrarlandığında soyutlamayı düşünmektir (genel bilgi). Ayrıca veri şekli değiştiğinde OCP tek başına yetmez: tuple kullanan her tüketici birlikte değişir. Bu, bağlılığın asıl kaynağıdır ve Bölüm 21.7'de ölçeceğiz. C++ tarafında aynı kalıbı Örnek 2'de göreceksin.

## 21.4 LSP: Davranışsal alt tip

Barbara Liskov, 1987'de bir konuşmasında (OOPSLA) veri soyutlaması ve hiyerarşi üzerine bu fikri ortaya attı. Jeannette Wing ile birlikte 1994'te yazdıkları makalede davranışsal alt tip tanımını resmileştirdiler (genel bilgi). Tanımın özü şudur: T tipi için kanıtlanabilen her özellik q(x), T'nin alt tipi S için de geçerli olmalıdır. Başka bir deyişle, bir alt sınıfın nesnesi üst sınıfın nesnesinin yerine konduğunda, bunu kullanan kod fark etmemelidir.

Bu tanım "is-a" (bir X bir Y'dir) cümlesinden farklıdır. Matematikte her kare bir dikdörtgendir. Ama değiştirilebilir bir dikdörtgen nesnesi için bu ilişki davranışsal olarak tutmaz. Klasik örnek budur. Aşağıdaki kod, dikdörtgen ve kareyi kalıtımla bağlar. Kare, kenarları eşit tutmak için `en_ayarla` ve `boy_ayarla` yöntemlerini ezer.

```python
class Dikdortgen:
    def __init__(self, en, boy):
        self._en = en
        self._boy = boy

    def en_ayarla(self, en):
        self._en = en

    def boy_ayarla(self, boy):
        self._boy = boy

    def alan(self):
        return self._en * self._boy


class Kare(Dikdortgen):
    def __init__(self, kenar):
        super().__init__(kenar, kenar)

    def en_ayarla(self, en):
        self._en = self._boy = en

    def boy_ayarla(self, boy):
        self._en = self._boy = boy
```

Kare sınıfında `en_ayarla` çağrıldığında boy da değişiyor. Üst sınıfın sözleşmesi ise "en değişir, boy değişmez" der. Bu fark testte görünür. Dikdörtgen için yazılmış testler, alt sınıf için de çalıştırılır. Python'un yerleşik `unittest` modülünde bir test sınıfı `TestCase`'ten türer; `test_` ile başlayan her metot ayrı bir test olarak çalışır ve `assertEqual` gibi yardımcılarla beklenen değer kontrol edilir. Test çatısının ayrıntıları Bölüm 39'da; burada yalnızca bu yapıyı kullanıyoruz.

```python
class DikdortgenTesti(unittest.TestCase):
    """Dikdortgen sozlesmesi: her alt sinif bu testleri gecmeli."""

    def yarat(self):
        return Dikdortgen(2, 3)

    def test_en_degisince_alan_degisir(self):
        s = self.yarat()
        s.en_ayarla(4)
        self.assertEqual(s.alan(), 12)

    def test_boy_degisince_alan_degisir(self):
        s = self.yarat()
        s.boy_ayarla(5)
        self.assertEqual(s.alan(), 10)
```

`KareTesti`, `DikdortgenTesti`'nin tüm testlerini miras alır ve yalnızca `yarat` yöntemini değiştirir. Bu, "aynı sözleşmeyi her alt sınıf geçmeli" fikrinin en basit biçimidir. Dosya, Dikdörtgen ve Kare testlerini (ve aşağıda göreceğin Okuyucu testlerini) birlikte çalıştırdığında çıktı şöyledir. Traceback satırları kısaltılmıştır:

```term
$ python lsp_kare.py
FAIL: test_en_degisince_alan_degisir (KareTesti)
AssertionError: 16 != 12
FAIL: test_boy_degisince_alan_degisir (KareTesti)
AssertionError: 25 != 10
ERROR: test_negatif_katsayi_kabul_edilir (PozitifOkuyucuTesti)
ValueError: katsayi pozitif olmali
Ran 6 tests in 0.002s
FAILED (failures=2, errors=1)
```

Kare(2) için `en_ayarla(4)` çağrıldığında alan 16 olur; Dikdörtgen sözleşmesi 12 bekler. Testin kendisi hatalı değil: sözleşme üst sınıf için yazıldı ve alt sınıf bu sözleşmeyi bozdu. Bu, LSP ihlalinin tipik imzasıdır.

Sözleşmenin dört bileşeni vardır ve ihlal her birinde ayrı bir biçimde ortaya çıkar (Şekil 21.3):

- **Önkoşul:** Alt sınıf, üst sınıfın kabul ettiği girdileri reddedemez. Önkoşulu güçlendirmek, yani daha az girdi kabul etmek ihlaldir.
- **Sonkoşul:** Alt sınıf, üst sınıfın garanti ettiği sonucu zayıflatamaz.
- **Değişmez (invariant):** Üst sınıfın korunan koşulları alt sınıfta da korunmalıdır.
- **Tarihçe kısıtı:** Alt sınıf, üst sınıfın izin vermediği durum değişikliğini yapamaz. Kare ihlali bu kuralın örneğidir: kare, boyun değişmesini yasaklamadı ama boyu da değiştirdi.

Önkoşul ihlalini bir örnekle görelim. `Okuyucu` her katsayıyı kabul eder. `PozitifOkuyucu` ise negatif katsayıyı reddeder. Bu, önkoşulu güçlendirir:

```python
class Okuyucu:
    def kalibre(self, katsayi):
        self.k = katsayi

    def olc(self, ham):
        return ham * self.k


class PozitifOkuyucu(Okuyucu):
    def kalibre(self, katsayi):
        if katsayi <= 0:
            raise ValueError("katsayi pozitif olmali")
        self.k = katsayi
```

Üst sınıfın testi, `PozitifOkuyucuTesti` tarafından miras alındığında negatif katsayı yüzünden alt sınıf hata fırlatır. Çıktıdaki `ERROR` satırı budur. İhlal, "alt sınıf da kabul etmeli" kuralının bozulmasıdır; kod derlenir ve çalışır, ama üst sınıfa bağlı bir kullanıcı şaşırır.

Düzeltmenin en temiz yolu kalıtımı kaldırmaktır. Kare ve Dikdörtgen yalnızca ortak bir `alan()` sözleşmesi paylaşır; birbirlerini miras almazlar. Ortak arayüzü Bölüm 21.5'te tanıtacağımız `Protocol` ile yazıyoruz:

```python
class Sekil(Protocol):
    def alan(self) -> float: ...


class Dikdortgen:
    def __init__(self, en, boy):
        self.en = en
        self.boy = boy

    def alan(self):
        return self.en * self.boy


class Kare:
    def __init__(self, kenar):
        self.kenar = kenar

    def alan(self):
        return self.kenar * self.kenar
```

Yukarıdaki test tek bir sözleşmeyi her şekil için çalıştırır ve çıktısı `OK` olur. Bu tasarımda Kare, Dikdörtgen'in bir türü değildir; yalnızca `alan()` davranışını paylaşır. Kalıtım gerekiyorsa, üst sınıfın sözleşmesini testle yazıp her alt sınıfa aynı testi uygula. Bunu yapamıyorsan, "is-a" ilişkisi büyük ihtimalle yanlıştır.

![Şekil 21.3: LSP sözleşme kuralları ve Kare ihlali. Kare, en_ayarla çağrısında boyu da değiştirir; Dikdörtgen sözleşmesi bu yan etkiyi yasaklar.](gorseller/b21_lsp_sozlesme.png)

LSP'yi ne zaman uygulamamalısın diye sorarsan, cevap şudur: kalıtım yoksa LSP ihlali de yoktur. Kalıtımı zorlamak yerine bileşim (bir nesnenin başka bir nesneyi içermesi) çoğu zaman daha güvenlidir; bileşim ve kalıtım farkını Bölüm 20'de ayrıntılı göreceksin. LSP'nin pratik karşılığı, alt sınıfları üst sınıfın testleriyle kontrol etmektir. Bu kontrol olmadan kalıtım hiyerarşisi, kullanıcılarını sessizce yanıltan bir tuzağa dönüşür.


## 21.5 ISP: Kullanılmayan metoda bağlanma

Martin'in tanımı: istemciler kullanmadıkları arayüzlere bağımlı olmaya zorlanmamalıdır (Interface Segregation Principle, genel bilgi). Arayüz, bir sınıfın dışarıya sunduğu metotların kümesidir. Arayüz şişerse, onu yalnızca bir kısmına ihtiyaç duyan istemci de tüm metotlara bağlı kalır. Bir metot değiştiğinde ya da bir alt sınıf o metodu uygulamak zorunda kaldığında bu bağımlılık sorun çıkarır.

Python'da arayüzü tanımlamanın yolu `typing.Protocol`'dür. Python 3.8'den beri standart kütüphanede bulunan bu yapı yapısal uyum (structural typing) sağlar: bir sınıf bir arayüzden miras almaz, yalnızca aynı metotları sunarsa o arayüzle uyumlu sayılır (genel bilgi). Bu, "bu sınıf şu arayüzü uygular" demenin açık bir zorunluluk olmadığı anlamına gelir. Tip denetleyicileri (mypy gibi) uyumu kontrol eder; çalışma zamanında Python bunu zorlamaz.

Aşağıdaki kod, tek bir sisik `Cihaz` arayüzünü gösterir. Termistör yalnızca okunabilir; ama arayüz üç metot ister:

```python
from typing import Protocol


class Cihaz(Protocol):          # sisik: her sey tek arayuzde
    def oku(self) -> float: ...
    def kalibre(self, k: float) -> None: ...
    def firmware_guncelle(self, dosya: bytes) -> None: ...


class Okunabilir(Protocol):     # kucuk: yalnizca okuma
    def oku(self) -> float: ...


class Kalibre(Protocol):        # kucuk: yalnizca kalibrasyon
    def kalibre(self, k: float) -> None: ...


class SaltOkunurTermistor:
    def oku(self) -> float:
        return 25.0

    def kalibre(self, k: float) -> None:
        raise NotImplementedError("kalibrasyon desteklenmiyor")

    def firmware_guncelle(self, dosya: bytes) -> None:
        raise NotImplementedError("firmware desteklenmiyor")


def olc_ve_kaydet(kaynak: Okunabilir) -> float:
    return kaynak.oku()        # yalnizca oku() kullanilir
```

`SaltOkunurTermistor`, kalibrasyon ve firmware metotlarını yalnızca arayüzü doldurmak için `NotImplementedError` ile yazmak zorunda kalıyor. Çalıştırdığında arayüz üzerinden çağrılabilen bu metot gerçekten hata verir:

```term
$ python isp_protocol.py
25.0
hata: firmware desteklenmiyor
```

Sorun, `olc_ve_kaydet` fonksiyonunun yalnızca `oku()` kullanmasına rağmen `Cihaz` tipini bilmesidir. Fonksiyonun bağımlılığı üç metoda genişledi; termistörün `firmware_guncelle` metodu da bu arayüzün bir parçası olduğu için her değişikliğe açık hâle geldi. Düzeltme, arayüzü ihtiyaca göre parçalamaktır:

```python
class Okunabilir(Protocol):     # kucuk: yalnizca okuma
    def oku(self) -> float: ...


class Kalibre(Protocol):        # kucuk: yalnizca kalibrasyon
    def kalibre(self, k: float) -> None: ...
```

Okunabilir ve Kalibre iki ayrı arayüz. Termistör her ikisini de uygular ama bunu yazmak zorunda değildir: `Okunabilir`'e bağlı fonksiyon yalnızca `oku` olduğu için yapısal uyum yeterlidir. Şekil 21.4 bu ayrımı gösterir.

![Şekil 21.4: ISP. Solda üç metotlu şişkin arayüz ve yalnızca okuma isteyen istemci; sağda küçük Okunabilir ve Kalibre arayüzleri.](gorseller/b21_isp_arayuz.png)

ISP'nin C++ karşılığı saf sanal (pure virtual) metotlu küçük sınıflardır. Saf sanal metot, alt sınıfın mutlaka uygulaması gereken bir sözleşmedir; C++'ta bu, `= 0` ile yazılır. Mekanizmanın ayrıntısı, yani sanal tablo (vtable) ve dinamik bağlama, Bölüm 20'de anlatılıyor. Burada yalnızca küçük ve tek amaçlı arayüz tasarlama fikrini alıyoruz; bunu Bölüm 21.6'daki C++ kodunda göreceksin.

ISP'nin bedeli, arayüz sayısının artmasıdır. Her istemci için küçük bir arayüz yazmak, arayüzleri bulmayı zorlaştırabilir. Tek bir uygulaması ve tek bir istemcisi olan bir sistemde arayüz ayırmak gereksiz soyutlamadır. Kural şöyle özetlenebilir: istemciler farklı metot kümelerine ihtiyaç duyuyorsa, arayüzü o kümelere göre böl.

## 21.6 DIP: Soyutlamaya bağlan, bağımlılığı dışarıdan al

Martin'in iki maddelik tanımı şöyledir (genel bilgi): (A) yüksek seviye modüller düşük seviye modüllere bağlı olmamalıdır; ikisi de soyutlamalara bağlı olmalıdır. (B) Soyutlamalar ayrıntılara bağlı olmamalıdır; ayrıntılar soyutlamalara bağlı olmalıdır.

Yüksek seviye modül, sistemin "ne" yaptığını bilir: ölç, kaydet, alarm ver. Düşük seviye modül "nasıl" yapıldığını bilir: bu sensör hangi kanaldan okunur, hangi protokolle konuşulur. Bağımlılık yönü normalde yukarıdan aşağıya gider: yüksek seviye düşük seviyeyi çağırır. DIP bu yönü ters çevirir: iki taraf da bir soyutlamaya bağlanır ve soyutlamanın sahibi yüksek seviye modüldür. Şekil 21.5 bu ters çevirmeyi gösterir.

Aşağıdaki kod, önceki bölümdeki `olcum.py` modülünün ADC okumasını nasıl kullandığını gösterir. Sensör fonksiyonu sahte okumayı kendi içinde çağırıyor, dışarıdan verilecek bir yol yok:

```python
def _adc_oku(kanal):
    """Donanim yerine sahte okuma (gercekte SPI/ADC surucusu)."""
    return 1000 + 100 * kanal


def olcumleri_oku(sensorler):
    """[(tur, kanal)] -> [(tur, deger, birim)]"""
    sonuc = []
    for tur, kanal in sensorler:
        ham = _adc_oku(kanal)
        if tur == "termistor":
            deger, birim = ham * 0.1 - 40.0, "C"
        elif tur == "gerilim":
            deger, birim = ham * 3.3 / 4095, "V"
        else:
            raise ValueError("bilinmeyen sensor: %s" % tur)
        sonuc.append((tur, deger, birim))
    return sonuc
```

Bu tasarımda test, gerçek ADC yerine geçecek bir nesneyi dışarıdan veremez. Bunun yerine modülün iç adını yamalar. Testlerin tamamı şu desene dayanır:

```python
class OlcumTesti(unittest.TestCase):
    def test_termistor(self):
        with mock.patch("olcum._adc_oku", return_value=1100):
            (tur, deger, birim), = olcum.olcumleri_oku(
                [("termistor", 1)])
        self.assertEqual((tur, birim), ("termistor", "C"))
        self.assertAlmostEqual(deger, 70.0)

    def test_gerilim(self):
        with mock.patch("olcum._adc_oku", return_value=2048):
            (_, deger, birim), = olcum.olcumleri_oku([("gerilim", 2)])
        self.assertEqual(birim, "V")
        self.assertAlmostEqual(deger, 2048 * 3.3 / 4095)
```

`mock.patch`, bir modül özniteliğini geçici olarak başka bir değerle değiştiren Python aracıdır; `with` bloğu bittiğinde özgün değere döner. Çalışır, ama iki sorunu vardır. Birincisi, test modülün iç adına (`"olcum._adc_oku"`) bağlanır; isim değiştiğinde test bir hata verir ve bu hata, testin neden kırıldığını değil, neyin eksik olduğunu gösterir. İkincisi, yama yalnızca tek bir noktada geçerlidir; aynı sahteyi her testte yazman gerekir.

Düzeltmede sensör sınıfı ADC'yi kurucu parametresi olarak alır. Bu, constructor injection (kurucu ile bağımlılık enjeksiyonu) denen kalıptır: bağımlılık nesnenin dışında oluşturulur ve içeri verilir. ADC için soyutlama, Bölüm 21.5'teki gibi tek metotlu bir `Protocol`'dür:

```python
class AdcKaynagi(Protocol):
    """Tek metot: kanal -> ham ADC degeri (ISP: kucuk arayuz)."""

    def oku(self, kanal: int) -> int: ...
```

Sensör sınıfı yalnızca bu soyutlamaya bağlanır. Gerçek donanım sürücüsü (EV Dashboard'da STM32 ADC'si) soyutlamayı uygular; test ortamında ise sahte bir sınıf aynı metodu sağlar. Test sınıfı şöyle görünür:

```python
class SahteAdc:
    """Donanim yerine test sahtesi: AdcKaynagi arayuzunu uygular."""

    def __init__(self, tablo):
        self.tablo = tablo

    def oku(self, kanal):
        return self.tablo[kanal]
```

Bu sahte nesne yamadan çalışır. Modülün iç adına bağlı değildir ve sensörün gerçekten hangi değeri istediğini açıkça gösterir: kanal 1 için 1100 değerini ver, sonuç 70,0 derece olsun. Aynı sahte, rapor testlerinde de kullanılır. Yama satırı sayısı önce tarafında dört, sonra tarafında sıfırdır; sahte sınıf ise bir kez, sekiz satır olarak yazılır.

![Şekil 21.5: Bağımlılık yönü. Solda üst seviye doğrudan somut sürücüye bağlı; sağda üst seviye ve sürücü aynı soyutlamaya bağlanır, test sahtesi de aynı noktaya bağlanır.](gorseller/b21_dip_yon.png)

C++ tarafında aynı fikri bir telemetri hattı ile gösterelim. Hat, sensörü ve kaydediciyi kurucuda referans olarak alır; hiçbir somut sınıfın adını bilmez:

```cpp
// ISP: telemetri hattina yalnizca okuma gerekir; kucuk arayuz
class Okunabilir {
public:
    virtual ~Okunabilir() = default;
    virtual double oku() const = 0;
};

// Depolama soyutlamasi (dusuk seviye ayrintidan bagimsiz)
class Kaydedici {
public:
    virtual ~Kaydedici() = default;
    virtual void yaz(double v) = 0;
};

// Ust seviye politika: somut sensor ve depoyu bilmez
class TelemetriHatti {
public:
    TelemetriHatti(const Okunabilir &kaynak, Kaydedici &hedef)
        : kaynak_(kaynak), hedef_(hedef) {}
    void calistir() { hedef_.yaz(kaynak_.oku() * 2.0); }
private:
    const Okunabilir &kaynak_;   // kurucu enjeksiyonu: referans
    Kaydedici &hedef_;
};
```

C++'ta referans (`const Okunabilir &`) bir nesneye takma addır; kopya oluşturmaz. Sınıf, referansın gösterdiği nesnenin ömrünü kendisi yönetmez; ömrü nesneyi oluşturan kod yönetir. Bu yüzden `main` içinde nesneler yerel değişken olarak oluşturulup referansları verilir. Akıllı işaretçi (`std::unique_ptr`) ile sahiplik ayrıntısı Bölüm 20'de.

```cpp
// Gercek donanim surucusu (sahte olmayan)
class TermistorSurucu : public Okunabilir {
public:
    double oku() const override { return 36.6; }
};

// Test sahtesi: deger disaridan verilir
class SahteSensor : public Okunabilir {
public:
    explicit SahteSensor(double d) : deger_(d) {}
    double oku() const override { return deger_; }
private:
    double deger_;
};

// Test icin bellek kaydedicisi
class BellekKaydedici : public Kaydedici {
public:
    void yaz(double v) override { kayit_.push_back(v); }
    std::vector<double> kayit_;
};
```

Sahte sensör ve bellek kaydedicisi, gerçek donanım olmadan hattın davranışını doğrulamamızı sağlar. Ana fonksiyon, bu iki sensörü aynı hatta bağlar:

```cpp
int main()
{
    SahteSensor sahte(21.5);
    BellekKaydedici bellek;
    TelemetriHatti h1(sahte, bellek);
    h1.calistir();
    std::printf("sahte: %g\n", bellek.kayit_.at(0));

    TermistorSurucu gercek;
    BellekKaydedici b2;
    TelemetriHatti h2(gercek, b2);
    h2.calistir();
    std::printf("termistor: %g\n", b2.kayit_.at(0));
    return 0;
}
```

Çıktı şöyledir:

```term
$ ./dip_asan
sahte: 43
termistor: 73.2
```

Aynı `TelemetriHatti` sınıfı iki farklı sensörle çalıştı; hatta hiçbir değişiklik yapılmadı. Bu, DIP'nin pratik kazancıdır.

DIP'yi dört kavramdan ayırmak gerekir. DIP bir ilkedir: yüksek seviyenin soyutlamaya bağlanması. Bağımlılık enjeksiyonu (dependency injection, DI) bu ilkeye ulaşmanın bir yoludur: bağımlılığı dışarıdan verirsin. Constructor injection, DI'nın en yaygın biçimidir. DI konteyneri ise bağımlılıkların oluşturulup bağlanmasını otomatikleştiren bir kütüphane ya da çatıdır; Java ve .NET dünyasındaki çatılar bu işi yapar, Python'da da benzer kütüphaneler vardır. Konteyner olmadan DIP uygulanabilir; `app.py` içindeki birkaç satır bunun örneğidir. Konteyner olmadan DI uygulanabilir; konteyner ise DIP'nin ya da DI'nın kendisi değildir.

DIP'nin bedeli, kurucunun parametrelerinin artması ve nesne grafiğinin bir yerde (kompozisyon kökü) kurulmasının zorunluluğudur. Tek bir uygulaması olan, değişim beklenmeyen ve test gerektirmeyen küçük bir yardımcı için soyutlama eklemek gerekmez. Ölçüt, test etmek istediğin yerde gerçek bir dış bağımlılık olup olmadığıdır.

## 21.7 Bağlılık ve uyum: ölçmek

Bir modülün bağlılığı (coupling), diğer modüllere ne kadar bağımlı olduğudur. Uyum (cohesion) ise bir modül içindeki parçaların ne kadar tek bir amaca hizmet ettiğidir. İkisi birlikte değişim maliyetini belirler: düşük bağlılık ve yüksek uyum, değişikliğin yalıtılmasını sağlar.

Bağlılığı ölçmek için en basit ölçüt, import grafiğinden çıkarılan iki sayıdır (genel bilgi, Martin'in kararlılık metrikleri). Ca (afferent coupling), bu modüle bağlı olan modül sayısıdır: bu modülü değiştirdiğinde kaç yer etkilenir? Ce (efferent coupling), bu modülün bağlı olduğu modül sayısıdır: bu modül kaç farklı yerden etkilenir? Kararsızlık I = Ce / (Ca + Ce) ile hesaplanır. I = 0 en kararlı modüldür (kimse ona bağlanmıyor ya da o hiçbir yere bağlanmıyor), I = 1 en kararsız olanıdır.

Aşağıdaki araç, bir klasördeki Python dosyalarının import grafiğini `ast` modülüyle çıkarır. `ast`, Python kaynağını söz dizimi ağacına çeviren standart kütüphane modülüdür; kodu çalıştırmadan içindeki `import` düğümlerini okuyabilirsin. Test dosyaları ölçüme dahil edilmez.

```python
import ast
import os
import sys


def modulleri_bul(kok):
    return sorted(f[:-3] for f in os.listdir(kok)
                  if f.endswith(".py") and not f.startswith("test_"))
```

Import kenarlarını bulan fonksiyon, her modül için dosyayı ayrıştırır ve `Import` ile `ImportFrom` düğümlerini gezer. Yalnızca proje içindeki modüllere giden kenarlar sayılır; `math` ya da `json` gibi standart kütüphane modülleri grafikte görünmez.

```python
def import_kenarlari(kok):
    mods = set(modulleri_bul(kok))
    kenarlar = set()
    for m in mods:
        yol = os.path.join(kok, m + ".py")
        with open(yol, encoding="utf-8") as f:
            agac = ast.parse(f.read(), filename=yol)
        for dugum in ast.walk(agac):
            if isinstance(dugum, ast.Import):
                adlar = [a.name for a in dugum.names]
            elif isinstance(dugum, ast.ImportFrom) and dugum.module:
                adlar = [dugum.module]
            else:
                continue
            for ad in adlar:
                hedef = ad.split(".")[0]
                if hedef in mods and hedef != m:
                    kenarlar.add((m, hedef))
    return sorted(kenarlar), sorted(mods)
```

Son parça Ca, Ce ve I değerlerini hesaplar ve tabloyu yazdırır:

```python
def metrikler(kok):
    kenarlar, mods = import_kenarlari(kok)
    # afferent (Ca): bu module bagli olan modul sayisi
    ca = dict.fromkeys(mods, 0)
    # efferent (Ce): bu modulun bagli oldugu modul sayisi
    ce = dict.fromkeys(mods, 0)
    for a, b in kenarlar:
        ce[a] += 1
        ca[b] += 1
    satirlar = []
    for m in mods:
        toplam = ca[m] + ce[m]
        i = ce[m] / toplam if toplam else 0.0    # kararsizlik
        satirlar.append((m, ca[m], ce[m], i))
    return kenarlar, satirlar


if __name__ == "__main__":
    kenarlar, satirlar = metrikler(sys.argv[1])
    if "--kenar" in sys.argv:
        for a, b in kenarlar:
            print("%s,%s" % (a, b))
    else:
        print("modul       Ca  Ce     I")
        for m, ca, ce, i in satirlar:
            print("%-9s %3d %3d  %5.2f" % (m, ca, ce, i))
```

Önce ve sonra kod tabanlarında aracı çalıştırdığımızda şu tablolar çıktı:

```term
$ python baglilik.py once
modul       Ca  Ce     I
app         0   1   1.00
olcum       1   0   0.00
rapor       1   1   0.50
$ python baglilik.py sonra
modul       Ca  Ce     I
alarm       1   0   0.00
app         0   3   1.00
bicim       1   0   0.00
istatistik  1   0   0.00
kayit       2   0   0.00
rapor       1   3   0.75
sensorler   1   2   0.67
sozlesme    1   0   0.00
```

Önce tasarımında üç modül ve iki bağlantı var. `olcum` modülü hiçbir yere bağlı değil (Ce = 0) ama `rapor` ona bağlanıyor. Yani `olcum` kararlı ama somut: değişirse yalnızca `rapor` etkilenir, ama `rapor` ile birlikte tüm veri biçimi kararlaştırılmış olur. Sonra tasarımında sekiz modül ve sekiz bağlantı var. Tip tanımı (`sozlesme`) ve kayıt tablosu (`kayit`) I = 0 olan modüllerdir; somut sensörler (`sensorler`, I = 0,67) ve orkestratör (`rapor`, I = 0,75) bunlara bağlanır. Bu, kararlılık ilkesinin beklediği düzendir: sık değişmeyen şeyler kararlı ve soyut, sık değişen şeyler kararsız ve somut olmalıdır.

Import grafiği, bağlılığın yalnızca bir kısmını görür. Şekil 21.6 bu iki grafiği yan yana gösteriyor.

![Şekil 21.6: Import grafiği. Solda üç modül ve zincir; sağda sekiz modül, kayıt ve sözleşme gibi kararlı merkezlerle. Kutularda Ca, Ce ve I değerleri.](gorseller/b21_import_grafigi.png)

Ama import grafiği anlamsal bağlılığı görmez. Bir tuple'ın şeklinin değişmesi, iki modül arasında import ilişkisi olmadan bile etkiyi yayabilir. Bunu ölçmek için bir değişiklik senaryosu tanımlayıp etkisini sayacağız. Senaryo A: her ölçüme bir güven değeri eklenecek. Senaryo B: yeni bir sensör türü (basınç) eklenecek.

Ölçüm betiği, her senaryonun klasörünü taban klasörle karşılaştırır: kaç dosya değişti, kaç satır değişti ve değiştirilmiş kodla eski test paketini çalıştırdığında kaç test kırıldı. Satır sayısı, `difflib` ile üretilen birleşik farkın artı ve eksi satırlarının sayısıdır. `subprocess` ile çalıştırılan test çıktısındaki `failures` ve `errors` sayıları kırılan testleri verir.

```python
import difflib
import os
import re
import subprocess
import sys


def dosyalar(kok):
    sozluk = {}
    for f in os.listdir(kok):
        if f.endswith(".py"):
            with open(os.path.join(kok, f), encoding="utf-8") as h:
                sozluk[f] = h.read().splitlines()
    return sozluk


def degisim(taban, yeni):
    a, b = dosyalar(taban), dosyalar(yeni)
    dosya, satir = 0, 0
    for f in sorted(set(a) | set(b)):
        x, y = a.get(f, []), b.get(f, [])
        if x == y:
            continue
        dosya += 1
        for l in difflib.unified_diff(x, y, lineterm="", n=0):
            if l[:3] not in ("+++", "---") and l[:1] in ("+", "-"):
                satir += 1
    return dosya, satir
```

```python
def testler(kok):
    p = subprocess.run(
        [sys.executable, "-m", "unittest", "test_telemetri"],
        cwd=kok, capture_output=True, text=True, encoding="utf-8")
    kosan = int(re.search(r"Ran (\d+) test", p.stderr).group(1))
    f = re.search(r"failures=(\d+)", p.stderr)
    e = re.search(r"errors=(\d+)", p.stderr)
    f_say = int(f.group(1)) if f else 0
    e_say = int(e.group(1)) if e else 0
    return kosan, f_say + e_say
```

```python
if __name__ == "__main__":
    taban = sys.argv[1]
    print(",".join(["senaryo", "degisen_dosya", "degisen_satir",
                     "kosan_test", "kirilan_test"]))
    for yeni in sys.argv[2:]:
        d, s = degisim(taban, yeni)
        kosan, kirilan = testler(yeni)
        print("%s,%d,%d,%d,%d" % (os.path.basename(yeni), d, s,
                                  kosan, kirilan))
```

Senaryo A önce tasarımında iki farklı şekilde uygulandı. İlkinde yalnızca üretici (`olcum.py`) değiştirildi: her ölçüm dört elemanlı bir tuple dönüyor. İkincisinde tüketici ve testler de düzeltildi. Senaryo A sonra tasarımında ise yalnızca `sozlesme.py` içindeki `Olcum` veri sınıfına `guven: float = 1.0` satırı eklendi:

```term
$ python olc_etki.py once senaryo/once_A1 senaryo/once_A2 senaryo/once_B
senaryo,degisen_dosya,degisen_satir,kosan_test,kirilan_test
once_A1,1,2,5,4
once_A2,3,12,5,0
once_B,3,6,5,0
$ python olc_etki.py sonra senaryo/sonra_A senaryo/sonra_B
senaryo,degisen_dosya,degisen_satir,kosan_test,kirilan_test
sonra_A,1,1,5,0
sonra_B,2,21,5,0
```

Bu çıktılar aşağıdaki tabloya ve Şekil 21.7'ye dönüşür:

| Senaryo | Sürüm | Değişen dosya | Değişen satır | Kırılan test (5 testten) |
|---|---|---|---|---|
| A: güven alanı, yalnız üretici | önce | 1 | 2 | 4 |
| A: güven alanı, tam değişiklik | önce | 3 | 12 | 0 (testler de düzeltildi) |
| A: güven alanı | sonra | 1 | 1 | 0 |
| B: basınç sensörü | önce | 3 | 6 | 0 |
| B: basınç sensörü | sonra | 2 (1 yeni) | 21 (18 yeni satır) | 0 |

![Şekil 21.7: Değişiklik senaryolarının etkisi. Önce tasarımında üretici değişikliği dört testi kırar; sonra tasarımında veri alanı eklemek hiçbir testi kırmaz.](gorseller/b21_etki_olcum.png)

Tablo üç şey söyler. Birincisi, senaryo A'da önce tasarımı dört testi kırar ama import grafiğinde bu değişikliğin bir işareti yoktur: `olcum` modülü değişiyor, ama Ca ve Ce değerleri aynı kalıyor. Anlamsal bağlılık, yani veri biçimi sözleşmesi, import grafiğinden görünmez. İkincisi, senaryo B'de önce tasarımı üç dosyaya dokunur ve hiçbir testi kırmaz. Yani ölçüt yalnızca kırılan test değildir; değiştirilen mevcut dosya sayısı da bir risk göstergesidir. Üçüncüsü, sonra tasarımında yeni bir sensör türü, mevcut dosyaların içine girmek yerine yeni bir dosya olarak eklenir; bu sayede değişen dosya sayısı önceki tasarımdan az kalır, ama toplam satır sayısı artar. Kazanç yerleştirmede, risk ise mevcut kodun değişmesindedir.

Bu ölçümün sınırları da var. Dört ila beş testlik küçük bir örnek, bir ekibin gerçek kod tabanının yerini tutmaz. Ayrıca sayılar tasarımın kalitesini değil, seçtiğimiz iki senaryonun etkisini gösterir. Değişiklik senaryosunu yanlış seçersen sonuç da yanlış olur; bu yüzden senaryolar gerçekçi değişim taleplerinden alınmalıdır.

Uyum için de benzer bir ölçüm yapılabilir. Bir sınıfın metotlarını, paylaştıkları alanlara göre bir graf üzerinde birleştirip bağlantısız bileşen sayısını bulmak LCOM ailesi metriklerinin fikridir (genel bilgi). Bu bölümde uyumu niteliksel olarak tartıştık: önce `RaporYoneticisi` tek metotlu olduğu için uyum görünmez, ama beş ayrı değişim nedeni taşıyordu. Bu, uyumun neden metot sayısıyla ölçülemediğini gösterir. Kendi LCOM ölçümünü bu aracın üstüne eklemeyi Kendin Yap bölümünde yapacaksın.


## 21.8 SOLID'in bedeli: YAGNI, KISS ve "her şeye arayüz"

Beş ilkeyi her yere uygulamak bir kalite işareti değildir. SOLID, değişim maliyetini yönetmek için bir araçtır; gereksiz yere uygulanırsa kendisi bir maliyete dönüşür. Bu gerilimi açıklayan iki pratik kural vardır. YAGNI (You Aren't Gonna Need It) "ihtiyacın olacağını varsayarak yazma" der. KISS (Keep It Simple, Stupid) ise en basit çözümün tercih edilmesini söyler (genel bilgi).

Bir örnek görelim. Aşağıdaki kod iki sayıyı toplamak için bir strateji arayüzü, bir uygulama sınıfı ve bir fabrika kullanıyor:

```python
from typing import Protocol


class ToplamaStratejisi(Protocol):
    def topla(self, sayilar: list[float]) -> float: ...


class NormalToplama:
    def topla(self, sayilar: list[float]) -> float:
        return sum(sayilar)


class ToplayiciFabrika:
    def olustur(self) -> ToplamaStratejisi:
        return NormalToplama()


if __name__ == "__main__":
    print(ToplayiciFabrika().olustur().topla([1.5, 2.5]))
    print(sum([1.5, 2.5]))
```

Programın çıktısı şöyledir:

```term
$ python asiri_muhendislik.py
4.0
4.0
```

İki satırlık `sum` ifadesi ile yirmi bir satırlık fabrikalı çözüm aynı sonucu veriyor. Fabrikalı çözümün kazanımı, ileride ikinci bir toplama stratejisi eklendiğinde ortaya çıkabilir. Ama o gün gelmediyse, bugünkü kodu okuyan kişi üç soyutlama katmanı çözmek zorunda kalır. Bu, "her şeye arayüz" kalıbının tipik tuzağıdır.

Bir soyutlama eklemeden önce kendine şu dört soruyu sor:

1. Bu soyutlamanın ikinci bir uygulaması bugün var mı, yarın olacağı biliniyor mu?
2. Testte gerçek bir dış bağımlılığı (donanım, ağ, dosya) taklit etmen gerekiyor mu?
3. Değişim beklenen bir yer mi, yoksa yalnızca "belki" mi?
4. Soyutlama okunabilirliği artırıyor mu, azaltıyor mu?

Dört soruda da "hayır" çıkarsa, soyutlama yalnızca kod hacmini artırır. Bu bölümdeki örneklerde soyutlamaları bu sorulara göre seçtik: sensör ADC'si test için gerçekten dış bağımlılıktı. LSP bölümündeki `Okuyucu` ise yalnızca bir ihlal örneğiydi; gerçek bir sistemde ikinci bir uygulaması olmayan bir arayüz eklemezdin. Bu fark, SOLID'i uygulamak ile gereksiz mühendislik yapmak arasındaki farktır.

## 21.9 SOLID'in C ve gömülü dünyadaki karşılığı

Şimdiye kadar yazdığımız OCP ve DIP örnekleri nesne yönelimli dildeydi. Peki sınıf ve kalıtım olmayan bir C programında aynı kazanımlar mümkün mü? Cevap evet, bunun için fonksiyon işaretçisi kullanılır. Bölüm 2'de işaretçilerin bir değişkenin adresini tuttuğunu gördün. Fonksiyonların da bellekte bir adresi vardır; bir fonksiyon işaretçisi bu adresi tutar. Söz dizimi `double (*oku)(int)` gibi görünür: `oku`, `int` alıp `double` döndüren bir fonksiyonun adresini saklar. Parantezler gereklidir; `double *oku(int)` yazarsan bu, `double` döndüren bir fonksiyon bildirimi olur.

Aşağıdaki program, üç sensör sürücüsünü bir fonksiyon işaretçisi tablosunda toplar. Tabloyu işleyen `raporla` fonksiyonu somut sürücüleri bilmez. `typedef`, `struct`'a bir tip adı verir; böylece tabloyu `sensor_ops` tipiyle yazabiliriz:

```c
#include <stddef.h>
#include <stdio.h>

typedef struct {
    const char *ad;
    const char *birim;
    double (*oku)(int ham);        /* zorunlu */
    double (*kalibre)(double v);   /* istege bagli: NULL olabilir */
} sensor_ops;

static double termistor_oku(int ham) { return ham * 0.1 - 40.0; }
static double gerilim_oku(int ham) { return ham * 3.3 / 4095.0; }
static double basinc_oku(int ham) { return ham * 0.05; }
static double basinc_duzelt(double v) { return v + 1.5; }

static const sensor_ops tablo[] = {
    {"termistor", "C", termistor_oku, NULL},
    {"gerilim", "V", gerilim_oku, NULL},
    {"basinc", "kPa", basinc_oku, basinc_duzelt},
};
```

Tablonun her satırı bir sürücüyü tanımlar. `kalibre` alanı `NULL` olabilir; bu, sürücünün bu adımı desteklemediği anlamına gelir. Çekirdek bu alanı çağırmadan önce kontrol eder. Bunu yapmasak, `NULL` bir fonksiyon işaretçisini çağırmak tanımsız davranıştır (UB); tipik olarak programın çökmesine yol açar, ama bu bir garanti değildir.

```c
static void raporla(const sensor_ops *t, size_t n, const int *ham)
{
    for (size_t i = 0; i < n; i++) {
        double v = t[i].oku(ham[i]);
        if (t[i].kalibre != NULL)     /* NULL ise adim atlanir */
            v = t[i].kalibre(v);
        printf("%-10s %8.3f %s\n", t[i].ad, v, t[i].birim);
    }
}
```

Test için sahte bir sürücü, aynı tip üzerinden çekirdeğe verilir. Çekirdek bu sürücünün gerçek olup olmadığını bilmez:

```c
/* Test icin sahte surucu: cekirdek bunu da ayni sekilde isler */
static double sahte_oku(int ham) { return (double)ham; }
static const sensor_ops sahte[] = {{"sahte", "u", sahte_oku, NULL}};

int main(void)
{
    int ham[3] = {1500, 1100, 1200};
    size_t n = sizeof tablo / sizeof tablo[0];
    raporla(tablo, n, ham);
    printf("-- sahte surucu --\n");
    int ham2[1] = {7};
    raporla(sahte, sizeof sahte / sizeof sahte[0], ham2);
    return 0;
}
```

WSL içinde `gcc -O2 -Wall -Wextra -std=c11` ile uyarısız derlendi ve sanitizer sürümüyle de çalıştırıldı. Çıktı şöyle:

```term
$ ./sensor_tablo
termistor   110.000 C
gerilim       0.886 V
basinc       61.500 kPa
-- sahte surucu --
sahte         7.000 u
```

Burada iki ilke birlikte çalışıyor. OCP: yeni bir sürücü eklemek için yeni fonksiyonlar yazılır ve tabloya bir satır eklenir; `raporla` değişmez. DIP: çekirdek somut sürücülere değil, `sensor_ops` tipine bağlıdır. Tip, C'deki soyutlamadır.

Bu kalıbın en bilinen büyük örneği Linux çekirdeğinin dosya işlemleri tablosudur. `struct file_operations`, her dosya sistemi ve aygıt sürücüsünün sağladığı işlemleri fonksiyon işaretçisi olarak tutar. Sistem çağrıları bu tabloya bakar ve doğru fonksiyonu çağırır. Bu, C++'taki sanal fonksiyonların dolaylı bir karşılığıdır (genel bilgi). Gerçek kaynağını Kod Okuma bölümünde inceleyeceksin. Şekil 21.8, bu yapının iki sürücüde nasıl doldurulduğunu yan yana gösteriyor: `null_fops` ve `zero_fops` aynı alanları farklı fonksiyonlarla doldurur, doldurulmayan alanlar ise `NULL` kalır.

![Şekil 21.8: struct file_operations alanlarının null_fops ve zero_fops tarafından doldurulması. NULL hücreler, sürücünün o işlemi desteklemediğini gösterir.](gorseller/b21_fops_tablo.png)

Gömülü sistemlerde bu kalıp donanım soyutlama katmanı (HAL) olarak yaşar: uygulama kodu "ADC'den oku" der, HAL bunun hangi register'a yazılacağını bilir. Test ortamında HAL yerine sahte bir sürücü konur. Bu, Bölüm 43 ve 44'te donanıma yakın kodu nasıl test edeceğinin temelidir. Çamur topu projesinde (Kendin Yap, Proje 1) sen de bu ayrımı yapacaksın.

Bu kalıbın bir sınırı var: dizi boyutu sözleşmesini derleyici denetlemez. `raporla` fonksiyonu `ham` dizisinin en az `n` elemanlı olduğunu varsayar. Daha kısa bir dizi verirsen, sınır dışı okuma tanımsız davranıştır (UB). Bu yüzden gerçek projelerde dizi boyutunu ayrı bir parametre olarak alır ve sınır kontrolünü açıkça yazarsın; Bölüm 2'deki dizi sınır hatası burada da geçerlidir.

## Çözümlü Örnekler

### Örnek 1 (★): Rapor sınıfını değişim nedenlerine göre böl

**Adım 1 — Anla.** Önce tasarımda tek bir `RaporYoneticisi.calistir` metodu var. Üç istek geldi: (a) `ORT` satırındaki iki ondalık kaldırılsın, (b) alarm eşiği 80'den 85'e çıksın, (c) ortalama yerine medyan yazılsın. Her istek için kaç dosyaya ve kaç yere dokunulacağını say. Hangi tasarım bu üç isteği en az yerde karşılar?

**Adım 2 — Örnekle.** Ölçümler `termistor 70.0` ve `gerilim 0.967` olsun. Düzeltilmiş tasarımdaki biçim fonksiyonu, `metin` çağrısıyla şu çıktıyı üretir:

Aşağıdaki metin, `bicim.metin` fonksiyonunun iki ölçüm ve 35,48 ortalama için ürettiği içeriktir:

```term
termistor     70.00 C
gerilim        0.97 V
ORT 35.48
```

Bu metin dosyanın içeriğidir. Test, dosyada `ORT` satırının bulunduğunu kontrol eder. Bu örnekte ortalama 35,48'dir; bunun nasıl hesaplandığını Adım 6'da elle izleyeceğiz.

**Adım 3 — Kaba çöz.** Önce tasarımda üç istek de aynı metoda girer. (a) için satır biçimi, (b) için `80.0` sabiti, (c) için `sum(...) / len(...)` ifadesi değişir. Dosya sayısı bir olsa da üç ayrı değişiklik aynı metot içinde birbirine karışır. Bu tür bir değişiklikte, (b) isteğini uygularken (a) biçiminin yanlışlıkla bozulması mümkündür. Düzeltilmiş tasarımda ise (a) `bicim.py`, (b) `sensorler.py` (eşik bir sensör özelliği olarak tutulur) ve (c) `istatistik.py` içinde yapılır.

**Adım 4 — Örüntü.** Her değişim nedeni tek bir modülde yaşar. Orkestratör yalnızca sırayla çağırır ve hesap yapmaz. Bu örüntü, bir isteğin etkisinin tek bir dosyada kalmasını sağlar.

**Adım 5 — İyileştir.** (b) isteğini düzeltilmiş tasarımda uygulamak için tek yere dokunursun: eşik değeri sensör sınıfının içindedir. Aşağıdaki sınıf başlığı, değişecek satırın yerini gösterir:

```python
@kaydet("termistor")
class TermistorSensor:
    birim = "C"
    esik = 80.0
```

`esik = 80.0` satırı `esik = 85.0` olur. Alarm fonksiyonu (`alarm.py`) değişmez çünkü eşiği sensörden okur. (a) için yalnızca `bicim.py`, (c) için yalnızca `istatistik.py` açılır.

**Adım 6 — Doğrula.** İki tasarımın testlerini çalıştırdığında her ikisi de beş testi geçer. Ortalamanın elle izi aşağıdadır:

| Satır | Toplam | Eleman sayısı | Ortalama |
|---|---|---|---|
| `olcumler` iki ölçüm alındı | 70,0 + 0,967 = 70,967 | 2 | — |
| `istatistik.ortalama` çağrısı | 70,967 | 2 | 70,967 / 2 = 35,4835 |
| `bicim.metin` `%.2f` biçimi | — | — | 35,48 |

İstek tablosu, iki tasarımda dokunulan yerleri karşılaştırır:

| İstek | Önce: dosya ve yer | Sonra: dosya ve yer |
|---|---|---|
| (a) ORT iki ondalık | `rapor.py`, `calistir` içinde satır biçimi | `bicim.py`, `metin` |
| (b) eşik 80 → 85 | `rapor.py`, `calistir` içinde `80.0` | `sensorler.py`, `TermistorSensor.esik` |
| (c) medyan | `rapor.py`, `calistir` içinde ortalama | `istatistik.py`, `ortalama` |

**Bunu AI'sız yazabilir misin?** Alarm kuralını değiştirmek istiyorsun: iki ardışık ölçüm de eşiğin üstündeyse alarm üretilsin. Hangi dosyaya ve hangi fonksiyona dokunursun? Yeni kuralı kendi testinle nasıl kanıtlarsın?

### Örnek 2 (★★): İndirim kuralları ve OCP (C++)

**Adım 1 — Anla.** Bir mağazada üç indirim kuralı var: öğrenci (%20), bayram (%10) ve sadakat (%5). Kurallar birbirinin üstüne uygulanabilir. Bir tutar için son fiyatı hesaplayan fonksiyon, yeni bir kural eklendiğinde kaç yerde değişir?

**Adım 2 — Örnekle.** 100 birimlik bir sepet için: yalnız öğrenci 80; öğrenci ve bayram birlikte 72; üçü birlikte 68,4 (100 × 0,80 × 0,90 × 0,95). Bu üç değer doğru sonuç olmalı ve iki tasarım da bunları üretmeli.

**Adım 3 — Kaba çöz.** Önce tasarımda tüm kurallar tek bir fonksiyonun içinde bir `if` zincirindedir:

```cpp
struct Musteri {
    bool ogrenci;
    bool bayram;
    bool sadakat;   // 'sonradan eklenen' alan
};

// ONCE: her yeni kural bu govdeyi degistirmeyi gerektirir
double indirim_once(double t, const Musteri &m)
{
    if (m.ogrenci) t *= 0.80;
    if (m.bayram) t *= 0.90;
    if (m.sadakat) t *= 0.95;
    return t;
}
```

Bu fonksiyon çalışır, ama her yeni kural `indirim_once`'ın gövdesini değiştirir. Sadakat kuralını sonradan eklediğimizi düşün: fonksiyon açılır, yeni bir `if` yazılır ve bu fonksiyonu kullanan her yerde yeniden doğrulama gerekir.

**Adım 4 — Örüntü.** Her kural bir nesne olsun. Bu nesnelerin ortak bir sözleşmesi (`uygula`) olsun. Toplam, kuralları sırayla dolaşan bir döngü olsun. Yeni kural yeni bir sınıf olur; döngü değişmez. Sanal fonksiyonun ayrıntısı Bölüm 20'de, ama burada kullanacağımız tek şey şudur: `uygula` çağrıldığında gerçek sınıfın sürümü çalışır.

**Adım 5 — İyileştir.** Kural sınıfları ve toplam fonksiyonu:

```cpp
// SONRA: kural = sinif. Yeni kural = yeni sinif + listeye ekleme
class IndirimKurali {
public:
    virtual ~IndirimKurali() = default;
    virtual double uygula(double t, const Musteri &m) const = 0;
};

class OgrenciIndirimi : public IndirimKurali {
public:
    double uygula(double t, const Musteri &m) const override
    { return m.ogrenci ? t * 0.80 : t; }
};

class BayramIndirimi : public IndirimKurali {
public:
    double uygula(double t, const Musteri &m) const override
    { return m.bayram ? t * 0.90 : t; }
};

class SadakatIndirimi : public IndirimKurali {
public:
    double uygula(double t, const Musteri &m) const override
    { return m.sadakat ? t * 0.95 : t; }
};
```

```cpp
double toplam(
    const std::vector<std::unique_ptr<IndirimKurali>> &kurallar,
    double t, const Musteri &m)
{
    for (const auto &k : kurallar)
        t = k->uygula(t, m);
    return t;
}
```

`std::vector<std::unique_ptr<IndirimKurali>>` bir dizi nesne tutar; her eleman bir kural nesnesinin sahipliğini taşır. `unique_ptr`, kapsamdan çıkınca nesneyi siler. Burada bellek sızıntısı riski yoktur; ayrıntısı Bölüm 20'de.

**Adım 6 — Doğrula.** Programın çıktısı:

```term
$ ./ocp_asan
once=100.0000 sonra=100.0000 esit=1
once=80.0000 sonra=80.0000 esit=1
once=68.4000 sonra=68.4000 esit=1
```

İz tablosu, üçüncü satırı adım adım gösterir:

| Adım | Kural | Uygulanan çarpan | Tutar |
|---|---|---|---|
| 0 | başlangıç | — | 100,00 |
| 1 | öğrenci | 0,80 | 80,00 |
| 2 | bayram | 0,90 | 72,00 |
| 3 | sadakat | 0,95 | 68,40 |

Değişim sayımı: önce tasarımda yeni bir kural için `indirim_once` gövdesi değişir (1 fonksiyon) ve tüm yapı (`Musteri`) yeni bir alan kazanır. Sonra tasarımda yeni kural için bir sınıf yazılır ve listeye bir satır eklenir; mevcut hiçbir fonksiyon değişmez.

**Bunu AI'sız yazabilir misin?** Sadakat puanı 500'ü geçen müşterilere %15 indirim veren bir `PuanIndirimi` sınıfını yaz. Sınıfı ve listeye ekleme satırını yazıp `g++ -std=c++17 -Wall -Wextra` ile uyarısız derlediğini göster.

### Örnek 3 (★★): Kare ve Dikdörtgen: testle yakalanan LSP ihlali

**Adım 1 — Anla.** `Kare`, `Dikdörtgen`'in alt sınıfı olarak yazıldı. Bir kullanıcı `Dikdörtgen` gibi davranan bir nesneyle çalışıyorsa, `Kare` geçirildiğinde ne değişir? Hangi testler geçer, hangileri kalır?

**Adım 2 — Örnekle.** `Dikdörtgen(2, 3)` nesnesinde `en_ayarla(4)` çağrısından sonra alan 12 olur. `Kare(2)` nesnesinde aynı çağrı alanı 16 yapar, çünkü kare eni değiştirirken boyu da değiştirir.

**Adım 3 — Kaba çöz.** Kullanıcı kodunda `if isinstance(s, Kare):` diye bir özel durum yazmak mümkündür. Bu, ihlali kodun her yerine yayar: her kullanıcı kare için ayrı kural bilmek zorunda kalır. Sözleşme bozulmuştur, kullanıcı ise bunu bilmek zorundadır.

**Adım 4 — Örüntü.** Ortak bir test sınıfı, üst sınıfın sözleşmesini tanımlar. Her alt sınıf bu testleri çalıştırır. Bir alt sınıf geçmiyorsa, bu sözleşme ihlalinin kanıtıdır. Test kalıtımı, sözleşmeyi kodun kendisi kadar görünür kılar.

**Adım 5 — İyileştir.** Kalıtımı kaldırıp ortak bir `alan()` sözleşmesi tanımladık; kod Bölüm 21.4'te. Her şekil yalnızca `alan()` sağlar ve birbirini miras almaz.

**Adım 6 — Doğrula.** Aynı test paketini üç sınıfa uyguladığında sonuç şöyle:

| Test | `Dikdörtgen(2, 3)` | `Kare(2)` (önce) | `Dikdörtgen` ve `Kare` (sonra) |
|---|---|---|---|
| en değişince alan değişir | geçer (12) | kalır (16 ≠ 12) | — |
| boy değişince alan değişir | geçer (10) | kalır (25 ≠ 10) | — |
| alan sözleşmesi | — | — | geçer (6 ve 4) |

Negatif katsayı örneğinde de benzer bir tablo çıkar: `Okuyucu` negatif kabul eder, `PozitifOkuyucu` ValueError fırlatır ve üst sınıfın testi bir hata (ERROR) olarak raporlanır. İki kanıt da aynı yerden gelir: alt sınıf, üst sınıfın sözleşmesini bozmuştur.

**Bunu AI'sız yazabilir misin?** `Kare(0)` gibi bir kenar değeri için alan sözleşmesi ne söyler? Sıfır kenarlı bir kare, `alan()` sözleşmesinde hangi değeri döndürmelidir ve bunu test ederken hangi durumu ayrıca kontrol etmelisin?

### Örnek 4 (★★★): EV Dashboard telemetri hattını sensörden bağımsızlaştırmak

**Adım 1 — Anla.** EV Dashboard'da sensör değeri gerçek bir ADC'den okunur. Telemetri hattının birim testleri donanım olmadan, her seferinde aynı sonucu vererek çalışmalıdır. Mevcut `olcum.py` sabit bir `_adc_oku` fonksiyonu kullanıyor. Hedef: testlerin donanıma ve iç isimlere bağlanmaması.

**Adım 2 — Örnekle.** Bir termistör kanalı 1100 ham değeri verdiğinde sonucun 70,0 derece olması gerekir. Bu beklentiyi iki tasarımda da test etmelisin.

**Adım 3 — Kaba çöz.** Hızlı bir çözüm, `olcum.py` içinde `TEST_MODU` gibi bir bayrak koymaktır. Bu, üretim kodunun içine test kodu sızdırır; bayrak unutulursa üretimde sahte değerler okunur. Başka bir kaba çözüm, testte `mock.patch` ile iç ismi yamalamaktır; bu da test ile modül ayrıntıları arasında gizli bir bağ kurar.

**Adım 4 — Örüntü.** Yüksek seviye sensör mantığı, ADC'nin ne olduğunu bilmek zorunda değildir; yalnızca `oku(kanal)` metodu olan bir soyutlamaya bağlanır. Gerçek sürücü (STM32 ADC) bu soyutlamayı uygular; test sahtesi de uygular. Bağımlılık kurucu parametresi olarak dışarıdan verilir.

**Adım 5 — İyileştir.** Düzeltilmiş tasarımda sensör sınıfı, ADC'yi kurucudan alır. Sınıfın tamamı aşağıdadır; kurucu `adc` parametresini saklar ve `olc` yalnızca bu nesne üzerinden okur:

```python
class TermistorSensor:
    birim = "C"
    esik = 80.0

    def __init__(self, adc, kanal):
        self.adc = adc
        self.kanal = kanal

    def olc(self):
        ham = self.adc.oku(self.kanal)
        return Olcum("termistor", ham * 0.1 - 40.0,
                     self.birim, self.esik)


@kaydet("gerilim")
```

Gerçek donanım sürücüsünü (STM32 HAL üzerinden) bu kodda yazmadık; donanım gerektirdiği için burada test edilemez. Yapması gereken yalnızca `AdcKaynagi` sözleşmesini uygulamaktır. Bu yazının dışındadır.

**Adım 6 — Doğrula.** İki tasarımın beş testi de geçiyor. Farkı gösteren tablo:

| Test | Önce: yama satırı | Sonra: sahte nesne | Sonuç (önce / sonra) |
|---|---|---|---|
| termistor değeri | 1 (`mock.patch`) | 0 | geçer / geçer |
| gerilim değeri | 1 | 0 | geçer / geçer |
| rapor dosyası | 1 | 0 | geçer / geçer |
| alarm | 1 | 0 | geçer / geçer |
| boş liste hatası | 0 | 0 | geçer / geçer |

Termistör testinin elle izi: ham değer 1100 → `1100 × 0,1 − 40 = 70,0`. Sahte nesne, `oku(1)` çağrısına 1100 döndürür; sensör bu değeri yalnızca dönüştürür, hiçbir iç isme dokunmaz.

**Bunu AI'sız yazabilir misin?** Sahte ADC'nin `oku` metodu her zaman `RuntimeError` fırlatsın. Bu sahte ile `TermistorSensor.olc()` çağrıldığında hangi davranışı kanıtlamış olursun? Sensörün hatayı yutmadığını ve yukarı taşıdığını gösteren bir test yaz.


## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. SOLID'in asıl eğitimi, bir tasarımın hangi değişikliklere dayanamadığını kendi elinle görmek ve düzeltirken hangi kararın neden verildiğini yazabilmektir. Bir aracın yazdığı düzeltilmiş kod doğru çalışsa bile, sana değişim nedenini ve bağımlılık yönünü anlatamaz. Testlerini kendin yaz ve her refaktör adımını kendi kararınla gerekçelendir.
:::

### Proje 1 (★★): Çamur topunu SOLID'e göre yeniden düzenle

**Amaç:** Aşağıdaki gömülü telemetri programı (`camur_topu.c`) tek bir dosyada, global durumla ve doğrudan donanım çağrılarıyla yazılmış bir çamur topudur. Programın davranışını değiştirmeden, kodu SOLID ilkelerine göre adım adım yeniden düzenlemen gerekiyor.

**Başlangıç kodu:** Program bir sahte ADC (doğrusal kongruans üreteci, tohum `42`), bir sahte UART (`printf`) ve bir sahte SD kaydı (bellekte tampon) kullanır. Programın tamamı aşağıda. WSL'de `gcc -O2 -Wall -Wextra -std=c11` ile uyarısız derlendi ve `-fsanitize=address,undefined` ile temiz çalıştı.

```c
/* camur_topu.c: her sey tek dosyada (big ball of mud).
 * Gomulu telemetri simulasyonu. Donanim sahte: ADC yerine LCG,
 * UART yerine printf, SD karti yerine bellekte bir tampon. */
#include <stddef.h>
#include <stdio.h>
#include <string.h>

#define KANAL_SAYI 4   /* 0 termistor, 1 gerilim, 2 basinc, 3 pil */
#define FILTRE_N 4
#define ALARM_ESIK 80.0
#define LOG_BOYUT 512
#define DONGU_SAYI 6

static unsigned tohum = 42u;
static const int taban[KANAL_SAYI] = {1500, 1000, 1200, 1100};
static int adc_son[KANAL_SAYI];
static double filtre[KANAL_SAYI][FILTRE_N];
static double son[KANAL_SAYI];
static double enk[KANAL_SAYI], enb[KANAL_SAYI];
static int dongu_no;
static int alarm_sayisi;
static int pil_uyari_sayisi;
static int watchdog;
static int reset_sayisi;
static char sd_log[LOG_BOYUT];
static size_t sd_uzun;

/* UART'tan gelen komutlar (sahte): dongu numarasina gore */
static const char *gelen[DONGU_SAYI] = {"", "", "", "R", "", "S"};
```

```c
static int hal_adc_oku(int kanal)
{
    tohum = tohum * 1103515245u + 12345u;
    return taban[kanal] + (int)((tohum >> 16) % 50u);
}

static void sensorleri_oku(void)
{
    for (int k = 0; k < KANAL_SAYI; k++)
        adc_son[k] = hal_adc_oku(k);
    watchdog++;
}

static double kalibre(int kanal, int ham)
{
    switch (kanal) {
    case 0: return ham * 0.1 - 40.0;          /* termistor, C */
    case 1: return ham * 3.3 / 4095.0;        /* gerilim, V */
    case 2: return ham * 0.05;                /* basinc, kPa */
    default: return ham * 3.3 * 2.0 / 4095.0; /* pil, V (bolucu 2) */
    }
}
```

```c
static void uart_gonder(const char *metin)
{
    printf("UART> %s\n", metin);
}

static void sd_yaz(const char *satir)
{
    size_t n = strlen(satir);
    if (sd_uzun + n + 2 <= sizeof sd_log) {   /* tasma sigortasi */
        memcpy(sd_log + sd_uzun, satir, n);
        sd_uzun += n;
        sd_log[sd_uzun++] = '\n';
        sd_log[sd_uzun] = '\0';
    }
}

static void filtrele(int kanal)
{
    double v = kalibre(kanal, adc_son[kanal]);
    int n = dongu_no < FILTRE_N ? dongu_no + 1 : FILTRE_N;
    double toplam = 0.0;
    filtre[kanal][dongu_no % FILTRE_N] = v;
    for (int i = 0; i < n; i++)
        toplam += filtre[kanal][i];
    son[kanal] = toplam / n;
    if (dongu_no == 0 || son[kanal] > enb[kanal])
        enb[kanal] = son[kanal];
    if (dongu_no == 0 || son[kanal] < enk[kanal])
        enk[kanal] = son[kanal];
}
```

```c
static void komut_isle(int no)
{
    if (gelen[no][0] == 'R') {
        reset_sayisi++;
        memset(filtre, 0, sizeof filtre);
        dongu_no = 0;
        uart_gonder("RESET OK");
    } else if (gelen[no][0] == 'S') {
        printf("durum: dongu=%d alarm=%d\n", no, alarm_sayisi);
    }
}
```

```c
static void alarm_kontrol(void)
{
    if (son[0] > ALARM_ESIK) {
        alarm_sayisi++;
        printf("ALARM termistor %.2f\n", son[0]);
    }
    if (son[3] < 0.85) {
        pil_uyari_sayisi++;
        printf("UYARI pil %.3f\n", son[3]);
    }
}

static void telemetri_satiri(void)
{
    char satir[96];
    snprintf(satir, sizeof satir, "T=%.2f V=%.3f P=%.2f B=%.3f",
             son[0], son[1], son[2], son[3]);
    uart_gonder(satir);
    sd_yaz(satir);
}

static void dongu(int no)
{
    sensorleri_oku();
    komut_isle(no);
    for (int k = 0; k < KANAL_SAYI; k++)
        filtrele(k);
    alarm_kontrol();
    telemetri_satiri();
    dongu_no++;
}
```

```c
int main(void)
{
    for (int t = 0; t < DONGU_SAYI; t++)
        dongu(t);
    for (int k = 0; k < KANAL_SAYI; k++)
        printf("kanal %d min=%.3f maks=%.3f\n", k, enk[k], enb[k]);
    printf("alarm=%d pil=%d reset=%d watchdog=%d sd=%zu\n",
           alarm_sayisi, pil_uyari_sayisi, reset_sayisi,
           watchdog, sd_uzun);
    fputs(sd_log, stdout);
    return 0;
}
```

Programın ilk birkaç satırı, referans çıktının başlangıcıdır. Tamamını kendin üretmelisin:

```term
$ ./camur
ALARM termistor 114.90
UART> T=114.90 V=0.807 P=61.85 B=1.820
ALARM termistor 113.65
UART> T=113.65 V=0.811 P=62.05 B=1.811
```

**Yapılacak / Beklenen davranış:**

1. Önce kodu derle, çıktıyı `referans.txt` dosyasına kaydet. Bu dosya, tüm refaktör adımlarında kullanacağın tek referanstır.
2. Her global değişkeni listele ve hangi fonksiyonun ona yazdığını tabloya dök. Sonra bu durumu bir `struct` içinde topla ve fonksiyonlara parametre olarak ver.
3. Kalibrasyonu (`kalibre`'deki `switch`) ayrı bir modüle taşı. Yeni bir kanal eklemek için çekirdek fonksiyonunun değişmemesini sağla (OCP).
4. ADC, UART ve SD erişimini bir arayüz `struct`'ında (fonksiyon işaretçileri) topla. Çekirdek yalnızca bu arayüze bağlansın (DIP). Test için sahte bir arayüz yaz.
5. Filtreyi (`filtrele`) kendi modülüne taşı ve kendi testlerini ekle.
6. Alarm kurallarını kanal ve eşik tablosuna çevir; `alarm_kontrol` yalnızca tabloyu gezsin.
7. Her adımda: programın çıktısı `referans.txt` ile birebir aynı olsun, testlerin hepsi geçsin ve ASan/UBSan temiz kalsın.

**Önerilen yaklaşım (ipucu, tam çözüm değildir):** Önce testleri yaz, sonra refaktör et. Testler `assert` ile küçük bir `testler.c` dosyasında olabilir; sahte arayüzle `dongu` fonksiyonunu tek başına çalıştırabilirsin. Global durumu taşırken her seferinde yalnızca bir değişkeni taşı ve çıktıyı karşılaştır. Fonksiyon işaretçisi tablosu için Bölüm 21.9'daki `sensor_tablo.c` örneğine bak; yapı aynı, ama burada `struct` içinde üç işlem olacak (oku, yaz, kaydet).

**Başarı kriterleri:**

- Refaktörden sonra `./camur > cikti.txt` ve `cmp cikti.txt referans.txt` komutu hata vermez; çıktılar baytı baytına aynıdır.
- En az altı birim testi vardır: iki kalibrasyon, iki filtre, bir alarm, bir sahte donanımla döngü testi. Hepsi geçer ve ASan/UBSan ile temizdir.
- Çekirdek modül hiçbir somut donanım fonksiyonunu doğrudan çağırmaz; `grep` ile bu doğrulanabilir.
- Başlangıçtaki global değişken sayısından daha az global değişken kalır; kalanlar yalnızca modül-yerel (`static`) ve tek bir durum yapısında toplanmıştır.
- Kodun her dosyası uyarısız derlenir (`-Wall -Wextra -std=c11`).

### Proje 2 (★★★): Bağlılık ölçüm aracını döngü ve uyum ile genişlet

**Amaç:** Bölüm 21.7'deki `baglilik.py` aracı Ca, Ce ve I değerlerini hesaplıyor. Aracı iki yeni özellikle genişlet: import döngüsü tespiti ve LCOM4 benzeri bir uyum ölçümü. Sonra kendi kod tabanında çalıştır.

**Yapılacak / Beklenen davranış:**

1. Import grafiğinde döngü (A → B → A gibi) varsa bunları bildir. Döngüsüz bir grafikte boş sonuç dön. Hangi algoritmayı kullanacağını seç ve neden olduğunu yaz.
2. Her sınıf için LCOM4 hesapla: sınıfın metotlarını düğüm kabul et. İki metot aynı `self.alan` adını kullanıyorsa ya da biri diğerini `self.metot()` ile çağırıyorsa bağlı say. Bağlantısız bileşen sayısı LCOM4'tür. Metot sayısını değil, bileşen sayısını raporla.
3. Graf çıktısını Graphviz `digraph` biçiminde üret. Bir sınıfın LCOM4 değeri 1'den büyükse uyarı yaz.
4. Aracı kendi küçük bir kod tabanında (en az üç modül ve iki sınıf) çalıştır. Sonuçları yorumla: hangi modül en kararsız, hangi sınıf bölünmeli?

**Önerilen yaklaşım (ipucu, tam çözüm değildir):** Döngü tespiti için derinlik öncelikli aramada (DFS, Bölüm 17) geri kenarları bulmak yeterlidir. LCOM4 için her sınıfın metotlarını bir eşitlik ilişkisi gibi düşün; bağlantısız bileşen sayısı, birleştirme yapılan bir yapı ile bulunur (Bölüm 18'deki birleştirme-bul yapısını hatırla). `ast` modülünde `ast.Attribute` ve `ast.Call` düğümlerini ayırt etmek yeterlidir.

**Başarı kriterleri:**

- Döngü tespiti için en az iki test vardır: biri üç modüllük bir döngü için doğru döngüyü bildirir, biri döngüsüz grafikte boş sonuç döner.
- LCOM4 için bir sınıf kendi testinde bir (tüm metotlar bir alanı paylaşıyor) ve bir başka sınıf iki (iki bağımsız metot grubu) olarak ölçülür. İki değer de testle sabitlenir.
- Graphviz çıktısı, yüklüyse `dot` ile işlenebilir; değilse çıktının sözdizimi kendi testinde doğrulanır.
- Araç kendi kaynak kodu üzerinde çalıştırıldığında hata vermez.
- Tüm sayılar tekrarlanabilir: test verisi sabit ve tohumludur.

### Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kâğıtta düşün, sonra kodla doğrula. Mülakat sorularının bir kısmı ayrıca işaretlidir.

1. ★ Bir fonksiyon hem CSV dosyasını okuyup hem de HTML raporu üretiyor. SRP açısından hangi iki değişim nedeni vardır? Bunları hangi modüllere ayırırsın? (Mülakat)
2. ★ `if tip == "a": ... elif tip == "b": ...` zincirini bir sözlük tablosuna çevir. Bu tablo hangi durumda hâlâ yetersiz kalır?
3. ★ `Yigin` (stack) sınıfının alt sınıfı olarak `Kuyruk` yazarsan LSP açısından ne olur? Hangi testle bunu yakalarsın?
4. ★★ `Kus` sınıfında `ucabilir()` metodu var; `Penguen` alt sınıfı bunu `False` döndürerek uygular. LSP açısından sorunu açıkla ve üç tasarım seçeneği yaz. (Mülakat)
5. ★★ `list` sınıfından türeyen ve `append` çağrısında hata fırlatan salt okunur bir koleksiyon yaz. Bu, LSP'yi ihlal eder mi? Sözleşmeyi hangi testle yakalarsın?
6. ★★ Bir `Yazici` arayüzü `yazdir`, `tara` ve `faksla` metotlarını içeriyor. ISP'ye göre bu arayüzü böl ve her istemciye hangi küçük arayüzü vereceğini yaz.
7. ★★ Bir `BildirimServisi` doğrudan `SmtpIstemcisi`'ne bağlı. DIP'ye göre bağımlılığı nasıl tersine çevirirsin? Test için hangi sahte nesneyi yazarsın? (Mülakat)
8. ★★ Bir sınıfın kurucusu içinde `datetime.now()` çağrısı var. Bu, testleri nasıl etkiler? Saati nasıl enjekte edersin?
9. ★★ Bir modülün Ce değerini düşürmek istiyorsun. Hangi kodu taşıyarak bunu yapabilirsin ve bu işlem Ca değerini nasıl etkiler?
10. ★★★ `Oyuncu` sınıfında `saldir`, `kaydet` ve `ciz` metotları var. `kaydet` yalnızca `saldir` tarafından kullanılıyor. LCOM4 değerini hesapla, sınıfı nasıl bölersin? (Mülakat)
11. ★★★ Liskov'un tanımının yalnızca "alt sınıf üst sınıfın yerine geçebilir" olmadığını, tarihçe kısıtını da içerdiğini bir örnekle göster. Örneğin `Kumbara` sınıfında `cekilebilir` ve `bakiye` ilişkisini kullan.
12. ★★★ Yüz satırlık tek bir fonksiyon, birbirinden bağımsız üç iş yapıyor. SOLID'i sınıf yerine fonksiyon düzeyinde nasıl uygularsın? Hangi ilkeler fonksiyon düzeyinde anlamlı, hangileri değil? (Mülakat)

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak projeden, Linux çekirdeğinin 6.6 sürümünden iki dosya okuyacaksın: `include/linux/fs.h` ve `drivers/char/mem.c`. Kaynak adresleri şöyle: `https://raw.githubusercontent.com/torvalds/linux/v6.6/include/linux/fs.h` ve `https://raw.githubusercontent.com/torvalds/linux/v6.6/drivers/char/mem.c`. İndirilen dosyaların SHA-256 değerleri sırasıyla `62af3875ba09a6cdb03eb3a68b023ee26424fcb8d24dfc76e6597208ec2733c1` ve `d6df5b1c0d615f084fcd7fc159e4e3cb630c506370378db9131ce3781a9e418c` idi.

Aşağıdaki kesitler birebir kopyalanmıştır. İki değişiklik yaptık ve bunları belirtiyoruz: tab karakterleri dört boşlukla değiştirildi ve 70 karakteri aşan imza satırları iki satıra bölündü. İçerikte hiçbir satır silinmedi.

Önce yapının kendisi. `struct file_operations`, fs.h dosyasında 1852 ile 1895 satırları arasındadır:

```c
struct file_operations {
    struct module *owner;
    loff_t (*llseek) (struct file *, loff_t, int);
    ssize_t (*read) (struct file *, char __user *, size_t, loff_t *);
    ssize_t (*write) (struct file *, const char __user *, size_t,
            loff_t *);
    ssize_t (*read_iter) (struct kiocb *, struct iov_iter *);
    ssize_t (*write_iter) (struct kiocb *, struct iov_iter *);
    int (*iopoll)(struct kiocb *kiocb, struct io_comp_batch *,
            unsigned int flags);
    int (*iterate_shared) (struct file *, struct dir_context *);
    __poll_t (*poll) (struct file *, struct poll_table_struct *);
    long (*unlocked_ioctl) (struct file *, unsigned int,
            unsigned long);
    long (*compat_ioctl) (struct file *, unsigned int, unsigned long);
    int (*mmap) (struct file *, struct vm_area_struct *);
    unsigned long mmap_supported_flags;
    int (*open) (struct inode *, struct file *);
    int (*flush) (struct file *, fl_owner_t id);
    int (*release) (struct inode *, struct file *);
    int (*fsync) (struct file *, loff_t, loff_t, int datasync);
    int (*fasync) (int, struct file *, int);
    int (*lock) (struct file *, int, struct file_lock *);
    unsigned long (*get_unmapped_area)(struct file *, unsigned long,
            unsigned long, unsigned long, unsigned long);
    int (*check_flags)(int);
    int (*flock) (struct file *, int, struct file_lock *);
```

```c
    ssize_t (*splice_write)(struct pipe_inode_info *, struct file *,
            loff_t *, size_t, unsigned int);
    ssize_t (*splice_read)(struct file *, loff_t *,
            struct pipe_inode_info *, size_t, unsigned int);
    void (*splice_eof)(struct file *file);
    int (*setlease)(struct file *, int, struct file_lock **, void **);
    long (*fallocate)(struct file *file, int mode, loff_t offset,
              loff_t len);
    void (*show_fdinfo)(struct seq_file *m, struct file *f);
#ifndef CONFIG_MMU
    unsigned (*mmap_capabilities)(struct file *);
#endif
    ssize_t (*copy_file_range)(struct file *, loff_t, struct file *,
            loff_t, size_t, unsigned int);
    loff_t (*remap_file_range)(struct file *file_in, loff_t pos_in,
                   struct file *file_out, loff_t pos_out,
                   loff_t len, unsigned int remap_flags);
    int (*fadvise)(struct file *, loff_t, loff_t, int);
    int (*uring_cmd)(struct io_uring_cmd *ioucmd,
            unsigned int issue_flags);
    int (*uring_cmd_iopoll)(struct io_uring_cmd *,
            struct io_comp_batch *,
                unsigned int poll_flags);
} __randomize_layout;
```

Şimdi aynı yapıyı doldurup kullanan bir sürücü. `mem.c`, `/dev/null` ve `/dev/zero` gibi aygıtları tanımlar. Önce ilgili okuma ve yazma fonksiyonlarının imzaları (440 ile 449 satırları):

```c
static ssize_t read_null(struct file *file, char __user *buf,
             size_t count, loff_t *ppos)
{
    return 0;
}

static ssize_t write_null(struct file *file, const char __user *buf,
              size_t count, loff_t *ppos)
{
    return count;
```

Sonra `null_fops` (657 ile 665 satırları) ve `zero_fops` (674 ile 686 satırları). Bu iki yapı, yukarıdaki `struct file_operations` tipinde tanımlanmıştır:

```c
static const struct file_operations null_fops = {
    .llseek     = null_lseek,
    .read       = read_null,
    .write      = write_null,
    .read_iter  = read_iter_null,
    .write_iter = write_iter_null,
    .splice_write   = splice_write_null,
    .uring_cmd  = uring_cmd_null,
};
```

```c
static const struct file_operations zero_fops = {
    .llseek     = zero_lseek,
    .write      = write_zero,
    .read_iter  = read_iter_zero,
    .read       = read_zero,
    .write_iter = write_iter_zero,
    .mmap       = mmap_zero,
    .get_unmapped_area = get_unmapped_area_zero,
#ifndef CONFIG_MMU
    .mmap_capabilities = zero_mmap_capabilities,
#endif
};
```

Son olarak `zero_fops` içinde kullanılan makro tanımları (639 ile 643 satırları). Bu satırlar, bazı alanların gerçekte hangi fonksiyonlara işaret ettiğini değiştirir:

```c
#define zero_lseek  null_lseek
#define full_lseek      null_lseek
#define write_zero  write_null
#define write_iter_zero write_iter_null
#define open_mem    open_port
```

**Sorular — cevaplamadan geçme:**

1. `null_fops` ve `zero_fops` yapılarında `.open` alanı yoktur. Bu aygıtlar açıldığında çekirdek bu `NULL` işaretçiyle ne yapar olabilir? Bu kesitte çekirdeğin çağıran tarafı bulunmuyor; cevabını genel bilgi olarak yaz ve bunun bu kesitte doğrulanamadığını belirt.
2. `#define write_zero write_null` satırı ile `zero_fops.write = write_zero` ataması birlikte okunduğunda, `zero_fops.write` hangi fonksiyonun adresini tutar? Bu bir OCP kazanımı mıdır, yoksa yalnızca bir kolaylık mı? Gerekçeni yaz.
3. `read_null` ve `write_null` fonksiyonları `file` ve `ppos` parametrelerini kullanmaz. Neden imza bu kadar katı tutulmuştur? İpucu: `struct file_operations` içindeki işaretçilerin tipi tüm sürücülerde aynı olmak zorunda.
4. `struct file_operations` sonundaki `__randomize_layout` niteliği, derleyiciye yapı üyelerini rastgele bir sırada yerleştirmesini söyler (genel bilgi). Bu niteliğin, üyelere sabit ofsetle erişme varsayımıyla ilişkisi nedir?
5. `zero_fops` hem `.read` hem `.read_iter` alanlarını doldurur. Çekirdek bu iki yoldan hangisini seçer ve neden iki yol vardır? Bu kesitte seçimi gösteren kod yok; bunu belirt ve cevabını kaynak olmadan verebileceğin sınırı yaz.
6. Yeni bir işlem eklemek için `struct file_operations`'a yeni bir üye eklendiğinde, bu yapıyı kullanan mevcut sürücüler neden derlenmeye devam eder? Cevabı, C'nin başlatıcı (initializer) kuralına dayandır.

## Bölüm Özeti

- SOLID, değişim maliyetini yönetmek için beş ilkedir; bir kural listesi değil, bağımlılık yönü ve değişim alanları üzerine bir kılavuzdur.
- SRP'de ayrım, metot sayısıyla değil değişim nedeni (aktör) ile yapılır. Tek bir sınıfta birden fazla aktörün değişiklikleri varsa, sınıf bölünmelidir.
- OCP, yeni davranışı mevcut kodu değiştirmeden eklemeyi hedefler. Kayıt tablosu ve çok biçimlilik bunun iki temel aracıdır; sabit ve küçük bir koşul zinciri için fazlasıyla yeterlidir.
- LSP, alt sınıfın üst sınıfın sözleşmesini (önkoşul, sonkoşul, değişmez, tarihçe) koruyup korumadığını test eder. Kalıtım hiyerarşisini bu testlerle doğrulamak gerekir.
- ISP, istemcilerin kullanmadığı metotlara bağlanmasını engeller. Python'da `Protocol`, C++'ta saf sanal küçük arayüzler bu amaca hizmet eder.
- DIP, yüksek seviye modülün düşük seviye ayrıntıya değil soyutlamaya bağlanmasını ister. Bağımlılık dışarıdan verilir (kurucu enjeksiyonu) ve test için sahte nesne kullanılır.
- Bağlılık, Ca ve Ce ile ölçülür; kararlılık I = Ce / (Ca + Ce) ile ifade edilir. İmport grafiği anlamsal bağlılığı (veri şekli sözleşmesini) göstermez; bunun için değişiklik senaryosu sayımı gerekir.
- Her soyutlama bir maliyettir. YAGNI ve KISS, ikinci bir uygulama, test ihtiyacı ve gerçek bir değişim beklentisi olmadan soyutlama eklemeyi engeller.
- C'de fonksiyon işaretçisi tablosu, OCP ve DIP'nin nesne yönelimsiz karşılığıdır. Linux'un `struct file_operations` yapısı bu kalıbın büyük ölçekli örneğidir.

**Sonraki bölümde:** Bölüm 22 (Design Patterns) ile bu bölümde gördüğümüz tasarım sorunlarının yerleşik çözümlerini inceleyeceğiz. Bu bölümde yalnızca ilişkileri işaret ettik: OCP'nin tipik kalıbı Strategy ve Decorator'dır; kayıt tablosu ve sensör seçimi Factory düşüncesine yakındır. Bölüm 22'de her kalıbı kendi uygulamasıyla göreceksin ve MertOS'taki Command Pattern de orada yer alacak.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. Tek sorumluluk ilkesi "tek iş yapan sınıf" anlamına gelmez. Martin'in "değişim nedeni" ifadesini bir örnekle açıkla ve bu ifadenin neden daha doğru olduğunu savun.
2. Açık-kapalı ilkesini uygulamak için bir `if/elif` zincirini kayıt tablosuna çevirdiğinde hangi yeni risk ortaya çıkar? Bu riski nasıl azaltırsın?
3. Kare ve dikdörtgen örneğinde sorun hangi sözleşme kuralında? Yalnızca "is-a" ilişkisinin matematiksel doğruluğu yeterli mi?
4. Bir arayüzü küçültmek, istemci sayısını artırır. ISP'nin bu bedelini ne zaman kabul edersin, ne zaman etmezsin?
5. Bağımlılık enjeksiyonu ile bağımlılık tersine çevirme (DIP) arasındaki fark nedir? Bir DI konteyneri kullanmadan DIP'yi uygulayabilir misin?
6. Bir modülün Ca değeri yüksek ama Ce değeri sıfırsa bu ne anlama gelir? Bu modülü değiştirmenin riskini nasıl ölçersin?
7. Bir alt sınıf üst sınıfın tüm testlerini geçiyor, ama bir istemci hata alıyor. LSP ihlali var mı? Sözleşmeyi neyi kapsayacak şekilde genişletirsin?
8. Fonksiyon işaretçisi tablosu, C'de OCP'yi nasıl sağlar? Tablonun elemanlarından birinin NULL olması, çekirdek kodunda hangi sorumluluğu doğurur?
:::
