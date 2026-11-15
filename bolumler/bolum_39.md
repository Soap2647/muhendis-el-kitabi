%% kisim_no: X
%% kisim_ad: Yazılım Mühendisliği Pratiği
%% bolum_no: 39
%% baslik: Test Yazma

## Giriş: Kodun çalıştığını nereden bilirsin?

Bölüm 6'da bir hatayı nasıl avlayacağını gördün: yeniden üret, izole et, teşhis et, düzelt, doğrula. Son adımda bir cümle geçti: düzelttiğin hatanın girdisini bir **regresyon testine** çevir, hata geri dönerse testler kırmızı yansın. Bu bölüm o cümlenin açtığı kapıdır. Test yazmak, bir kez elle deneyip "tamam" demekten farklı bir iştir: aynı denemeyi her değişiklikten sonra, saniyeler içinde, insan dikkatine bağlı kalmadan tekrar edebilmektir.

Mülakatta bu konu iki biçimde gelir. Ya "bu fonksiyonu nasıl test edersin?" diye sorulur, ya da "bu testi neden yazdın, ne kanıtlıyor?" diye. İkinci soru ayrım ister: test, davranışın belirli bir kümesini sınar; tüm davranışı kanıtlamaz. Dijkstra'nın yıllar önce söylediği gibi, testler hataların varlığını gösterebilir, yokluğunu kanıtlayamaz. Bu yüzden iyi bir test yazmak, neyi sınadığını ve neyi sınamadığını bilmek demektir.

Mert'in projelerinde test ihtiyacı somuttur. EV Dashboard'a STM32'den gelen telemetri paketlerini ayrıştıran bir kod yazarsan (Bölüm 31'deki çerçeve ve CRC düzeni), bir bayt kayması tüm grafikleri sessizce bozar. MertOS'ta bir çekirdek fonksiyonu yanlış bir bayrak döndürürse, sistem bunu sonradan ve çok uzakta bir çökmeyle gösterir. Test, bu hataları hatanın yaşandığı yerde yakalar.

Bu bölümde test yazmanın üç işlevini göreceksin: **geri bildirim** (kodu değiştirdiğinde saniyeler içinde sonuç), **regresyon koruması** (bir kez düzelttiğin hatanın geri gelmesini engeller) ve **tasarım baskısı** (test edilemeyen kod genelde kötü tasarlanmış koddur). Ardından test piramidini, iyi birim testinin yapısını, pytest'in temellerini, test ikizlerini, kapsama ve mutasyon testini, özellik tabanlı testi, TDD'yi, kararsız testleri ve savunma sanayiinde test gereksinimlerini (MC/DC dahil) işleyeceğiz.

::: not
Bu bölümdeki her sayı ve her çıktı, bu bölümün kendi kodundan **çalıştırılarak** alındı: Python 3.12.10, pytest 9.0.3, Hypothesis 6.170.2, pytest-cov 7.1.0 ve WSL2 (Ubuntu 24.04) içinde gcc 13.3.0. Kod ve çıktılar birebir kitapta; komut satırlarında sayfa genişliği için `--no-header` ve `-p no:cacheprovider` gibi çıktıyı değiştirmeyen bayraklar gösterilmedi. Olduğu gibi çalıştırmak için kodu yazman yeterli.
:::

## 39.1 Neden test yazarız?

Bir testin üç işi vardır ve üçü de ayrı ayrı değerlidir.

**Geri bildirim hızı.** Bir fonksiyonu değiştirdiğinde, doğru olup olmadığını öğrenmenin en ucuz yolu testtir. Elle denemek her seferinde dakikalar alır ve tam olarak neyi denediğini unutmana yol açar. Testler ise aynı kontrolü her çalıştırmada aynı biçimde yapar.

**Regresyon koruması.** Bir hatayı bir kez düzeltmek, o hatanın bir daha gelmeyeceği anlamına gelmez. Yeni bir özellik eklerken eski bir davranışı bozmak çok kolaydır. Düzeltilen her hatanın girdisi bir testte kalırsa, gelecekteki değişiklikler o hatayı yeniden üretirse testler kırmızı yanar. Bölüm 6.9'da bunu zaten gördün.

**Tasarım baskısı.** Bir fonksiyonu test etmek istediğinde onu dosya okuyan, ağa bağlanan, global durumu değiştiren bir yapıdan ayırman gerekir. Bu zorluk bir sorun işaretidir: kodun bağımlılıkları yanlış yerde. Bölüm 21'deki bağımlılığın tersine çevrilmesi (DIP) ile test edilebilirlik aynı yere çıkar. Test yazmak, iyi tasarımın erken bir denetçisidir.

Testin sınırını da bilmek gerekir. Bir test seti geçtiğinde, sınanan durumlarda kodun doğru davrandığını söylersin; sınanmayan durumlar hakkında hiçbir şey söylemez. Bu yüzden "testler geçiyor" cümlesi tek başına bir kanıt değildir; hangi davranışın sınandığını bilmen gerekir. Bölüm 39.6'da bunu ölçmenin araçlarını göreceğiz, 39.7'de ise test setinin kendisini sınamayı.

## 39.2 Test piramidi ve test türleri

Testleri üç katmanda düşünmek yaygındır. En altta **birim testleri** (unit tests) bir fonksiyonu ya da sınıfı tek başına sınar; dış sistemler sahte nesnelerle (39.5) yerine konur. Ortada **entegrasyon testleri** birden çok bileşenin birlikte çalışmasını sınar: gerçek bir SQLite dosyası, gerçek bir soket. En üstte **uçtan uca testler** (end-to-end) tam bir kullanıcı senaryosunu baştan sona çalıştırır: bir web sayfası, bir tarayıcı, bir üretim ortamına yakın kurulum.

Şekil 39.1, bu katmanların önerilen oranını (piramit) ve sıkça görülen ters durumu (test kupası) karşılaştırır. Piramitte birim testleri çoktur; hızlıdırlar, ucuzdurlar ve bir hata olduğunda tam olarak nerede olduğunu gösterirler. Kupada ise her şey elle ya da tarayıcıyla yapılır: yavaş, kırılgan ve hatanın nerede olduğunu söylemeyen testler çıkar. Kupa, ekiplerin "çok test yazıyoruz" sanıp ağır uçtan uca testlere yaslandığı durumda ortaya çıkar.

![Şekil 39.1: Test piramidi (önerilen) ile test kupası (kaçınılacak)](gorseller/b39_piramit.png)

Test türleri de ayrı ayrı adlandırılır, çünkü her biri farklı bir soruya cevap verir:

| Tür | Sorusu | Örnek |
|---|---|---|
| Fonksiyonel | Özellik doğru çalışıyor mu? | `gecerli_tarih(2024, 2, 29)` doğru mu? |
| Sınır | Eşiklerde ve eşiğin dışında ne oluyor? | Şubat 28, 29 ve 30 |
| Regresyon | Düzelttiğimiz hata geri geldi mi? | Bölüm 6'daki hatanın girdisi |
| Performans | Yeterince hızlı mı? | 10⁶ elemanlı sıralama süresi |
| Duman (smoke) | Temel yol hiç çalışmıyor mu? | Uygulama açılıyor mu? |

Performans testini dikkatli kur: makine yükü ve ısınma, süreyi oynatır. Bölüm 12.10'daki ölçüm protokolü (sabit girdi, tekrarlı koşu, en iyi süre) burada da geçerlidir. Duman testi ise genelde ilk ve en kısa testtir: büyük bir değişiklikten sonra her şeyin kökten bozulmadığını hızla söyler.

## 39.3 İyi birim testi: AAA, tek davranış, adlandırma

Bir birim testinin yapısı üç adımlıdır ve bu yapının adı **AAA**'dır: Düzenle (Arrange), Eylem (Act), Doğrula (Assert). Önce girdiyi ve gerekli nesneleri kurarsın, sonra tek bir işlemi çağırırsın, en sonunda beklenen sonucu kontrol edersin (Şekil 39.2).

![Şekil 39.2: AAA yapısı: düzenle, eylem, doğrula](gorseller/b39_aaa.png)

İyi bir birim testinin birkaç özelliği vardır. **Tek davranış:** bir test bir şeyi sınar. "Siparişi oluştur, stoğu düş, e-posta gönder ve hata durumunu kontrol et" diyen bir test kırıldığında hangi davranışın bozulduğunu söylemez. **Deterministik:** aynı kodla her çalıştırmada aynı sonuç çıkar; rastgelelik, saat ve ağ bağımlılığı ya tohumla ya da sahte nesnelerle sabitlenir (39.11). **Hızlı:** birim testi milisaniyeler sürmeli; yüzlerce testi saniyeler içinde koşturabilmelisin. **Bağımsız:** bir testin sonucu başka bir testin çalışmasına bağlı olmamalı; sırası değişince kırılan test kötü yazılmıştır. **Açık adlandırma:** test adı, hangi durumda ne beklendiğini söyler.

Ad için yaygın bir kalıp `ne_olur_nerede_ne_beklenir` biçimidir, örneğin `test_stok_yetersizse_hata_verir`. Adı okuyan biri, testi açmadan bir davranış listesi çıkarabilmelidir. Bu, test raporunu bir belgeye çevirir.

Küçük bir örnekle farkı görelim. Aşağıdaki iki test aynı şeyi söyler gibi görünür, ama ikincisi ne sınadığını açıkça söyler:

```python
def test_1():
    assert gecerli_tarih(2024, 2, 29) is True
    assert gecerli_tarih(2023, 2, 29) is False
    assert gecerli_tarih(2024, 4, 31) is False

def test_artik_yil_subati_etkiler():
    assert gecerli_tarih(2024, 2, 29) is True
    assert gecerli_tarih(2023, 2, 29) is False
```

Birinci testin adı bir şey söylemez ve üç farklı davranışı tek seferde sınar; ikincisi tek bir davranışa (artık yıl etkisi) odaklanır. Bir sonraki bölümde gördüğün `pytest.mark.parametrize`, benzer testleri tek bir tabloda tutmanı ve her satırı ayrı bir test olarak raporlatmanı sağlar.

## 39.4 pytest ile test yazmak

Python'da en yaygın test çatısı **pytest**'tir. Python'un kendi `unittest` modülü de kullanılabilir (bunu Bölüm 21'de `TestCase` ile gördün), ama pytest daha az törenle yazılır ve daha okunaklı hata raporu verir. pytest, `test_*.py` ya da `*_test.py` biçimindeki dosyaları ve `test_` ile başlayan fonksiyonları kendiliğinden bulur. Bu, **test keşfi** (test discovery) adını alır.

### Assert yeniden yazımı

Python'da `assert` bir ifadeyi doğrular ve yanlışsa `AssertionError` fırlatır. Varsayılan Python, bu hatanın içinde ne olduğunu çok az söyler. pytest ise test modülünü içe aktarırken `assert` ifadelerini yeniden yazar; böylece hatanın içindeki ara değerleri de raporlayabilir. Bunu bir kasıtlı kırık test ile görelim:

```python
def test_siralama_beklenen():
    assert sorted([3, 1, 2]) == [1, 2, 4]
```

```python
def test_siralama_beklenen():
    assert sorted([3, 1, 2]) == [1, 2, 4]
```

Çıktı, iki listeyi karşılaştırır ve farkın nerede olduğunu gösterir:

```term
$ python -m pytest -q gosterim/test_kirik.py --tb=short
F                                                                [100%]
============================== FAILURES ===============================
_______________________ test_siralama_beklenen ________________________
gosterim\test_kirik.py:2: in test_siralama_beklenen
    assert sorted([3, 1, 2]) == [1, 2, 4]
E   assert [1, 2, 3] == [1, 2, 4]
E     
E     At index 2 diff: 3 != 4
E     Use -v to get more diff
======================= short test summary info =======================
FAILED gosterim/test_kirik.py::test_siralama_beklenen - assert [1, 2,...
1 failed in 0.83s
```

Bu rapor, `assert` ifadesinin sol ve sağ tarafını ayrı ayrı değerlendirir ve farkın 2. indekste olduğunu söyler. Bu yüzden testlerde `assertEqual(a, b)` yazmak yerine düz `assert a == b` yazmak pytest'te daha iyi sonuç verir.

### Fixture'lar: bağımlılıkları hazırlamak

**Fixture**, bir testin ihtiyaç duyduğu hazırlığı bir kez tanımlayıp testlere parametre olarak vermenin yoludur. Bir fixture'ın yaşam süresi **kapsam** (scope) ile belirlenir: `function` (her test için yeniden), `module` (dosya başına bir kez), `session` (tüm koşu için bir kez). Yerleşik `tmp_path` fixture'ı her test için benzersiz geçici bir dizin verir; böylece testler birbirinin dosyasını bozmaz.

Bölüm 39.10'da kullanacağımız oturum kapsamlı bir sunucu fixture'ı şöyle görünür (bu dosya `conftest.py` adıyla, pytest'in otomatik yüklediği özel bir dosyadır):

```python
import socket
import threading

import pytest

from cerceve import cerceve_al, cerceve_gonder


@pytest.fixture(scope="session")
def yanki_sunucu():
    """Oturum boyunca yaşayan, çerçeveyi geri yollayan sunucu."""
    dinleyici = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dinleyici.bind(("127.0.0.1", 0))    # port 0: çekirdek seçer
    dinleyici.listen(1)
    port = dinleyici.getsockname()[1]

    def calis():
        conn, _ = dinleyici.accept()
        with conn:
            while True:
                try:
                    yuk = cerceve_al(conn)
                except ConnectionError:
                    break
                cerceve_gonder(conn, yuk)
        dinleyici.close()

    threading.Thread(target=calis, daemon=True).start()
    return port
```

### parametrize: aynı testi çok girdiyle

`parametrize`, bir testi bir girdi tablosuyla çalıştırır. Her satır ayrı bir test olur; biri kırılırsa raporda adıyla görünür. Örnek 1'de bunu tarih doğrulayıcısında kullanacağız; şimdilik yapısını bilmek yeter.

### İşaretler (mark): atla, beklenen hatayı kaydet

`pytest.mark.skipif` bir testi koşulla atlar: test Linux dışında çalıştırılmaz. `pytest.mark.xfail` ise "bu testin başarısız olması beklenir" der; test kırılırsa rapor bunu hata olarak saymaz, geçerse uyarı verir. `xfail`, bilinen bir hatayı silmeden kayda almanın dürüst yoludur. Aşağıdaki dosya üç durumu da gösteriyor; ayrıca `pytest.approx` ve `unittest.TestCase` uyumu var:

```python
import sys
import unittest

import pytest


def test_kayan_nokta_yaklasik():
    assert 0.1 + 0.2 == pytest.approx(0.3)
    assert 0.1 + 0.2 != 0.3      # IEEE-754 (Bölüm 1)


@pytest.mark.skipif(sys.platform != "linux",
                    reason="yalnız Linux'ta")
def test_linux_ozel():
    assert sys.platform == "linux"


@pytest.mark.xfail(reason="bilinen hata: kayan nokta yuvarlama")
def test_bilinen_hata():
    assert 0.1 + 0.2 == 0.3


class BolumUnittest(unittest.TestCase):
    # pytest, unittest.TestCase sınıflarını da çalıştırır (Bölüm 21).
    def test_alan(self):
        self.assertEqual(2 * 3, 6)
```

```term
$ python -m pytest -v test_pytest_ozellikleri.py
========================= test session starts =========================
collecting ... collected 4 items

test_pytest_ozellikleri.py::test_kayan_nokta_yaklasik PASSED     [ 25%]
test_pytest_ozellikleri.py::test_linux_ozel SKIPPED (yalnız ...) [ 50%]
test_pytest_ozellikleri.py::test_bilinen_hata XFAIL (bilinen...) [ 75%]
test_pytest_ozellikleri.py::BolumUnittest::test_alan PASSED      [100%]

=============== 2 passed, 1 skipped, 1 xfailed in 0.83s ===============
```

Çıktıda `PASSED`, `SKIPPED`, `XFAIL` ve sonuç satırındaki sayılar bu üç mekanizmayı gösterir. `BolumUnittest` sınıfı, pytest'in eski `unittest` testlerini de çalıştırdığını gösterir: Bölüm 21'de yazdığın `TestCase` sınıfları pytest ile birlikte kullanılabilir.

### approx: kayan noktada eşitlik

Bölüm 1'deki kayan nokta bölümünde gördün: `0.1 + 0.2` tam olarak `0.3` değildir. Kayan noktalı sayıları `==` ile karşılaştırmak bu yüzden tuzaktır. `pytest.approx` bir tolerans ile karşılaştırır. Aşağıdaki küçük betik dört karşılaştırmayı yapar:

```python
import pytest

print(0.1 + 0.2 == pytest.approx(0.3))
print(1e-13 == pytest.approx(0))
print(1000000.5 == pytest.approx(1000000.0))
print(0.1 + 0.2 == 0.3)
```

```term
$ python approx_demo.py
True
True
True
False
```

`approx` nasıl karar veriyor? Kaynağa bakalım. Bu bölümün kullandığı pytest 9.0.3 sürümünde, `_pytest/python_api.py` dosyasındaki `ApproxScalar` sınıfı varsayılan toleransları ve eşitlik kararını tanımlar. Bu kesit, dosyadan birebir alındı; yalnızca yorum satırları çıkarıldı, satırlar bölünmedi:

```python
class ApproxScalar(ApproxBase):
    DEFAULT_ABSOLUTE_TOLERANCE: float | Decimal = 1e-12
    DEFAULT_RELATIVE_TOLERANCE: float | Decimal = 1e-6

    def __eq__(self, actual) -> bool:
        if is_bool(self.expected) or not (
            isinstance(self.expected, Complex | Decimal)
            and isinstance(actual, Complex | Decimal)
        ):
            return False
        if math.isnan(abs(self.expected)):
            return self.nan_ok and math.isnan(abs(actual))
        if math.isinf(abs(self.expected)):
            return False
        result: bool = abs(self.expected - actual) <= self.tolerance
        return result
```

Kaynak, toleransın göreli ve mutlak tolerans arasından büyük olanı seçtiğini de söyler (`tolerance` özelliğinin açıklamasında). Bu yüzden `approx(0)` gibi sıfıra yakın değerlerde mutlak tolerans, büyük sayılarda göreli tolerans devreye girer. Dolayısıyla `approx`'un doğru tolerans seçimi bir mühendislik kararıdır: sıfır civarındaki bir ölçüm için `rel` tek başına yetmez.

## 39.5 Test ikizleri: fake, mock, stub, spy

Gerçek bir sistemde bir fonksiyon genelde başka bileşenleri çağırır: bir veritabanı, bir e-posta gönderici, bir sensör. Birim testinde bu bağımlılıkları gerçekten çalıştırmak hem yavaştır hem de testi kırılgan yapar. Çözüm, bağımlılığın yerine bir **test ikizi** koymaktır. Test ikizlerinin beş yaygın türü vardır (Şekil 39.3):

![Şekil 39.3: Test ikizlerinin türleri ve görevleri](gorseller/b39_ikizler.png)

- **Dummy (sahte doldurma):** yalnızca argüman listesini doldurmak için verilir; hiç kullanılmaz.
- **Stub (taslak yanıt):** çağrıldığında önceden hazırlanmış bir değer döner. Testin girdisini kontrol etmek içindir.
- **Spy (gözlemci):** gerçek ya da sahte bir nesnedir, ama çağrılarını kaydeder; sonra "bu çağrı oldu mu, hangi argümanlarla" diye sorulabilir.
- **Mock (taklit):** beklentiyi önceden kurar ("şu çağrı, şu argümanlarla, bir kez gelmeli") ve doğrulamayı nesne yapar.
- **Fake (sahte gerçeklik):** gerçek davranışı olan ama hafif bir uygulamadır; örneğin bellekte çalışan bir depo.

Bu ayrımın pratik sonucu şudur: Fake ve Stub genelde **durumu** doğrulamayı sağlar (depo ne kadar kaldı?), Mock ise **etkileşimi** doğrulamayı (çağrı sırası ve argümanları doğru mu?). Etkileşimi çok sık doğrulamak, testi uygulamanın iç yapısına bağlar. Aşağıdaki küçük sipariş servisi bu farkı gösterir. Servis bağımlılıklarını dışarıdan alır (Bölüm 21'deki DIP), bu yüzden testte gerçek depo yerine kendi fake'ini verebilirsin:

```python
"""Test ikizlerini göstermek için küçük bir sipariş servisi."""


class StokYetersiz(Exception):
    pass


class SiparisServisi:
    def __init__(self, depo, eposta):
        self.depo = depo          # bağımlılık: stok deposu
        self.eposta = eposta      # bağımlılık: bildirim gönderici

    def olustur(self, urun, adet):
        if adet <= 0:
            raise ValueError("adet pozitif olmalı")
        if self.depo.stok_al(urun) < adet:
            raise StokYetersiz(urun)
        self.depo.stok_dus(urun, adet)
        self.eposta.gonder("siparis", urun, adet)
        return "onay"


class SiparisServisiV2(SiparisServisi):
    """Dış davranış aynı; stok kontrolü ve düşüm tek çağrıda."""

    def olustur(self, urun, adet):
        if adet <= 0:
            raise ValueError("adet pozitif olmalı")
        if not self.depo.stok_dus_dene(urun, adet):
            raise StokYetersiz(urun)
        self.eposta.gonder("siparis", urun, adet)
        return "onay"


class BellekDeposu:
    """Fake: gerçek davranışı olan, bellekte çalışan hafif depo."""

    def __init__(self, stoklar):
        self.stoklar = dict(stoklar)

    def stok_al(self, urun):
        return self.stoklar.get(urun, 0)

    def stok_dus(self, urun, adet):
        self.stoklar[urun] -= adet

    def stok_dus_dene(self, urun, adet):
        if self.stoklar.get(urun, 0) < adet:
            return False
        self.stoklar[urun] -= adet
        return True


class KayitliEposta:
    """Spy: gönderilen mesajları kaydeder, gerçekte göndermez."""

    def __init__(self):
        self.mesajlar = []

    def gonder(self, tur, urun, adet):
        self.mesajlar.append((tur, urun, adet))
```

`BellekDeposu` bir **fake**'tir: gerçekten stok tutar, gerçekten düşer. `KayitliEposta` bir **spy**'dır: gerçekten göndermez, sadece kaydeder. Testler şimdi bu iki gerçekliği kullanır:

```python
import pytest

from siparis import (BellekDeposu, KayitliEposta, SiparisServisi,
                     SiparisServisiV2, StokYetersiz)


@pytest.fixture(params=[SiparisServisi, SiparisServisiV2],
                ids=lambda c: c.__name__)
def servis_sinifi(request):
    return request.param


def test_yeterli_stokta_siparis_onaylanir(servis_sinifi):
    depo = BellekDeposu({"kalem": 5})
    servis = servis_sinifi(depo, KayitliEposta())
    assert servis.olustur("kalem", 2) == "onay"
    assert depo.stoklar["kalem"] == 3


def test_stok_yetersizse_hata_ve_stok_degismez(servis_sinifi):
    depo = BellekDeposu({"kalem": 1})
    servis = servis_sinifi(depo, KayitliEposta())
    with pytest.raises(StokYetersiz):
        servis.olustur("kalem", 2)
    assert depo.stoklar["kalem"] == 1


def test_basarili_siparis_bildirim_gonderir(servis_sinifi):
    eposta = KayitliEposta()
    servis = servis_sinifi(BellekDeposu({"kalem": 5}), eposta)
    servis.olustur("kalem", 2)
    assert eposta.mesajlar == [("siparis", "kalem", 2)]


def test_sifir_adet_reddedilir(servis_sinifi):
    servis = servis_sinifi(BellekDeposu({"kalem": 5}),
                           KayitliEposta())
    with pytest.raises(ValueError):
        servis.olustur("kalem", 0)
```

```term
$ python -m pytest -q test_siparis.py
........                                                         [100%]
8 passed in 0.75s
```

Her test iki servis sınıfıyla da çalışır (`fixture` parametreleri), çünkü ikisi de dış davranış olarak aynıdır. Şimdi aynı davranışı **mock** ile kontrol eden kırılgan bir test yazalım. Bu test, depo çağrılarının tam sırasını ve argümanlarını bekler:

```python
from unittest.mock import Mock

import pytest

from siparis import SiparisServisi, SiparisServisiV2


@pytest.fixture(params=[SiparisServisi, SiparisServisiV2],
                ids=lambda c: c.__name__)
def servis_sinifi(request):
    return request.param


def test_cagri_sirasi_kirilgan(servis_sinifi):
    # AŞIRI MOCK: test, davranış yerine iç çağrı dizisini sınar.
    depo = Mock()
    depo.stok_al.return_value = 5
    eposta = Mock()
    servis_sinifi(depo, eposta).olustur("kalem", 2)
    ad = [c[0] for c in depo.mock_calls]
    assert ad == ["stok_al", "stok_dus"]
    eposta.gonder.assert_called_once_with("siparis", "kalem", 2)
```

```term
$ python -m pytest -q test_siparis_kirilgan.py --tb=short -rN
.F                                                               [100%]
============================== FAILURES ===============================
____________ test_cagri_sirasi_kirilgan[SiparisServisiV2] _____________
test_siparis_kirilgan.py:21: in test_cagri_sirasi_kirilgan
    assert ad == ["stok_al", "stok_dus"]
E   AssertionError: assert ['stok_dus_dene'] == ['stok_al', 'stok_dus']
E     
E     At index 0 diff: 'stok_dus_dene' != 'stok_al'
E     Right contains one more item: 'stok_dus'
E     Use -v to get more diff
1 failed, 1 passed in 0.88s
```

Sonuç öğreticidir. `SiparisServisi` (V1) testi geçer, çünkü onun çağrı dizisi testin beklediğiyle aynıdır. `SiparisServisiV2` ise dış davranışı tamamen aynı olmasına rağmen testte kırılır: iç olarak stok kontrolünü ve düşümü tek bir `stok_dus_dene` çağrısında birleştirmiştir. Bu bir **aşırı mock** (over-mocking) tuzağıdır: test davranışı değil uygulamayı sınar. Yeniden düzenlemek (Bölüm 23.9) bu testi kırmamalıydı, ama kırdı. Kural şudur: mock'u **dış sınırda** kullan (e-posta, ağ, saat, dosya sistemi), kendi kodunun iç çağrılarını mock'lama. İç kısım için fake kullan.

`unittest.mock.patch` ile bir modülün içindeki bir fonksiyonu geçici olarak değiştirmek de aynı tuzaktadır. Yaygın bir hata, testin içinde `patch("modul.fonksiyon")` ile bir şeyi yerinden söküp döndürmektir. Patch hedefi yanlış yazıldığında test sessizce gerçek kodu çalıştırır ya da hiç uygulanmaz. Yeniden adlandırma ve taşıma yapıldığında da kırılır. Bu nedenle `patch` kullanıyorsan, hedefin **nerede kullanıldığını** (ör. `siparis.Depo`, tanımlandığı yerde değil) yazmaya dikkat et.

## 39.6 Kapsama: satır, dal ve sınırları

**Kapsama** (coverage), test çalışırken kodun hangi kısmının çalıştığını ölçer. En yaygın ölçüler şunlardır. **Satır kapsamı** (statement/line): her satır en az bir kez çalıştı mı? **Dal kapsamı** (branch): bir karar noktasının her yönü (`if` doğru ve yanlış) en az bir kez alındı mı?

Python'da bunun için `coverage.py` ve onun pytest eklentisi `pytest-cov` kullanılır. Aşağıdaki iki fonksiyonda satır ve dal kapsamasının farklı şeyler ölçtüğünü göreceğiz:

```python
def etiket(x):
    s = "sifir"
    if x is not None and x > 0:
        s = "pozitif"
    return s


def ortalama(xs):
    if not xs:
        return 0.0
    return sum(xs) // len(xs)   # HATA: tam bölme, ondalık kaybolur
```

`etiket` fonksiyonunda tek bir `if` var; `ortalama` fonksiyonunda da bir `if` var ve sonuç döndüren bir hata (`//`) içeriyor. Önce yalnızca iki test yazalım: biri boş liste, biri pozitif sayı için. Testler şunlar:

```python
from kapsama_ornek import etiket, ortalama


def test_ortalama_bos():
    assert ortalama([]) == 0.0


def test_ortalama_esit_degerler():
    assert ortalama([2, 2]) == 2


def test_etiket_pozitif():
    assert etiket(5) == "pozitif"
```

Önce satır kapsamasını ölçelim, sonra dal kapsamasını:

```term
$ python -m pytest -q --cov=kapsama_ornek \
      --cov-report=term-missing test_kapsama_zayif.py
...                                                              [100%]
=========================== tests coverage ============================
__________ coverage: platform win32, python 3.12.10-final-0 ___________

Name               Stmts   Miss  Cover   Missing
------------------------------------------------
kapsama_ornek.py       9      0   100%
------------------------------------------------
TOTAL                  9      0   100%
3 passed in 0.73s
```

```term
$ python -m pytest -q --cov=kapsama_ornek --cov-branch \
      --cov-report=term-missing test_kapsama_zayif.py
...                                                              [100%]
=========================== tests coverage ============================
__________ coverage: platform win32, python 3.12.10-final-0 ___________

Name               Stmts   Miss Branch BrPart  Cover   Missing
--------------------------------------------------------------
kapsama_ornek.py       9      0      4      1    92%   3->5
--------------------------------------------------------------
TOTAL                  9      0      4      1    92%
3 passed in 0.70s
```

Satır ölçüsü %100 çıktı, çünkü her satır en az bir kez çalıştı; `etiket` içindeki `s = "pozitif"` satırı `etiket(5)` ile çalıştı. Dal ölçüsü ise `etiket` içindeki `if`'in **yanlış** yönünü hiç denemediğini gösterdi: rapordaki `3->5` ifadesi, 3. satırdan 5. satıra (yani `if` yanlış ise doğrudan `return`e) geçişin çalışmadığını söyler. Şekil 39.4 bu farkı CFG (kontrol akış grafiği) üzerinde gösterir.

![Şekil 39.4: Satır ve dal kapsamasının aynı koddaki farkı](gorseller/b39_kapsama.png)

Bu grafikte kapsamanın birleşik yüzdesi %92'dir. Raporun hesabı, satırlar ile dalların toplamını kullanır: 9 satır ve 4 dal yönünden 12'si kapsanmıştır (9 + 3 = 12, 9 + 4 = 13). Bu yüzden yüzde yalnızca bir sayıdır; neyin eksik olduğunu gösteren tablo "Missing" sütunudur.

**Kapsama %100 olsa da hata olabilir.** Aşağıda, `ortalama` için dal kapsamasını tamamlayan ama hatayı kaçıran bir test paketi var:

```python
from kapsama_ornek import etiket, ortalama


def test_ortalama_bos():
    assert ortalama([]) == 0.0


def test_ortalama_esit_degerler():
    assert ortalama([2, 2]) == 2


def test_etiket_pozitif():
    assert etiket(5) == "pozitif"


def test_etiket_pozitif_degil():
    assert etiket(-1) == "sifir"
```

```term
$ python -m pytest -q --cov=kapsama_ornek --cov-branch \
      --cov-report=term-missing test_kapsama_tam.py
....                                                             [100%]
=========================== tests coverage ============================
__________ coverage: platform win32, python 3.12.10-final-0 ___________

Name               Stmts   Miss Branch BrPart  Cover   Missing
--------------------------------------------------------------
kapsama_ornek.py       9      0      4      0   100%
--------------------------------------------------------------
TOTAL                  9      0      4      0   100%
4 passed in 0.73s
```

Dal kapsamı da %100, ama `ortalama([1, 2])` sonucu `1` olur, oysa doğrusu `1.5`'tir. Hatanın yakalanması için bir **özellik** gerekir: "herhangi bir boş olmayan tam sayı listesi için sonuç, `statistics.fmean` ile aynı olmalı" (39.8'de özellik tabanlı testi ayrıntılı göreceğiz). Ders şu: kapsama bir **eksik test bulma aracıdır**, bir doğruluk kanıtı değildir. Kapsama yüzdesini hedef yaparsan, kodu çalıştırıp hiçbir şeyi doğrulamayan testler yazmaya başlarsın.

## 39.7 Mutasyon testi: testi test etmek

Kapsama, testlerin kodu **çalıştırdığını** ölçer; ama çalıştırıp **doğrulamadıklarını** ölçmez. Mutasyon testi bu boşluğu kapatır. Fikir şudur: kaynak koda küçük, bilinçli bir hata enjekte edersin (bir `<` yerine `<=`, bir `+` yerine `-`, bir sabiti bir artırmak). Bu değiştirilmiş koda **mutant** denir. Test paketi bu mutantı yakalarsa (en az bir test kırılırsa) mutant **öldürülmüş** sayılır; hiçbir test kırılmazsa mutant **hayatta kalmıştır**, bu da test setinde bir boşluk olduğunu gösterir (Şekil 39.5).

![Şekil 39.5: Mutasyon testi döngüsü](gorseller/b39_mutasyon_dongu.png)

Mutasyon skoru, öldürülen mutantların toplam mutanta oranıdır. Bu oran, testlerin kaynak koddaki küçük değişikliklere ne kadar duyarlı olduğunu ölçer. Bir uyarı gerekir: bazı mutantlar **eşdeğerdir**; yani kodun davranışını hiç değiştirmezler (örneğin sıfır olmayan bir değere yapılan bir sabit toplaması, o değerin hiç kullanılmadığı bir yerde). Eşdeğer mutantları hiçbir test öldüremez; bu yüzden skor, teorik bir üst sınır değil, bir alt ölçüdür ve hayatta kalan her mutantın elle incelenmesi gerekir.

Mutasyon testini kendimiz yazabileceğimiz kadar küçük bir araç, `ast` (Python'un sözdizimi ağacı modülü) ile kurabiliriz. Araç üç şey yapar: kaynağı ağaca çevirir, mutasyon yapılabilecek düğümleri bulur (karşılaştırmalar, ikili işlemler, mantıksal `and`/`or`, tam sayı sabitleri), her biri için tek bir değişiklik uygulanmış bir kopya üretir ve test paketini bu kopyayla çalıştırır. Test paketi başarısız olursa mutant öldü sayılır.

```python
"""Küçük bir mutasyon test aracı (Bölüm 39, Örnek 4).

Kullanım:  python mutasyon.py HEDEF.py TESTDOSYASI.py
Her mutant (kaynağa tek bir küçük değişiklik) ayrı bir geçici
dizinde çalıştırılır. Test paketi başarısız olursa mutant
'öldürüldü' sayılır; hepsi geçerse 'hayatta kaldı'.
"""
import ast
import os
import shutil
import subprocess
import sys
import tempfile

ZITLAR = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE,
          ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
          ast.Add: ast.Sub, ast.Sub: ast.Add}
BOOL_ZITLAR = {ast.And: ast.Or, ast.Or: ast.And}


def sahalar(agac):
    """Mutasyon yapılabilecek düğümleri sırayla listeler."""
    liste = []
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Compare):
            for i, op in enumerate(dugum.ops):
                if type(op) in ZITLAR:
                    liste.append(("cmp", dugum, i))
        elif isinstance(dugum, ast.BinOp):
            if type(dugum.op) in ZITLAR:
                liste.append(("bin", dugum, None))
        elif isinstance(dugum, ast.BoolOp):
            if type(dugum.op) in BOOL_ZITLAR:
                liste.append(("bool", dugum, None))
        elif (isinstance(dugum, ast.Constant)
              and type(dugum.value) is int):
            liste.append(("sabit", dugum, None))
    liste.sort(key=lambda s: (s[1].lineno, s[1].col_offset, s[0]))
    return liste


def mutantlar(kaynak):
    """(açıklama, mutant_kaynağı) çiftlerini üretir."""
    ilk = ast.parse(kaynak)
    sayi = len(sahalar(ilk))
    for k in range(sayi):
        agac = ast.parse(kaynak)
        tur, dugum, i = sahalar(agac)[k]
        if tur == "cmp":
            eski = type(dugum.ops[i]).__name__
            dugum.ops[i] = ZITLAR[type(dugum.ops[i])]()
            yeni = type(dugum.ops[i]).__name__
        elif tur == "bin":
            eski = type(dugum.op).__name__
            dugum.op = ZITLAR[type(dugum.op)]()
            yeni = type(dugum.op).__name__
        elif tur == "bool":
            eski = type(dugum.op).__name__
            dugum.op = BOOL_ZITLAR[type(dugum.op)]()
            yeni = type(dugum.op).__name__
        else:
            eski = str(dugum.value)
            dugum.value = dugum.value + 1
            yeni = str(dugum.value)
        ast.fix_missing_locations(agac)
        aciklama = "satır %d: %s -> %s" % (dugum.lineno, eski, yeni)
        yield aciklama, ast.unparse(agac) + "\n"


def calistir(hedef, testdosyasi, zaman_siniri=60):
    """Her mutant için (açıklama, öldü_mü) listesi döndürür."""
    with open(hedef, encoding="utf-8") as f:
        kaynak = f.read()
    sonuc = []
    for aciklama, mutant in mutantlar(kaynak):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, os.path.basename(hedef)), "w",
                      encoding="utf-8") as f:
                f.write(mutant)
            hedef_test = os.path.join(tmp, "test_suite.py")
            shutil.copy(testdosyasi, hedef_test)
            try:
                r = subprocess.run(
                    [sys.executable, "-m", "pytest", "-q", "-x",
                     "--no-header", "-p", "no:cacheprovider"],
                    cwd=tmp, capture_output=True,
                    timeout=zaman_siniri)
                oldu = r.returncode != 0
            except subprocess.TimeoutExpired:
                oldu = True
        sonuc.append((aciklama, oldu))
    return sonuc


if __name__ == "__main__":
    hedef, test = sys.argv[1], sys.argv[2]
    satirlar = calistir(hedef, test)
    for aciklama, oldu in satirlar:
        print("%-28s %s" % (aciklama,
                            "ÖLDÜ" if oldu else "HAYATTA"))
    olen = sum(1 for _, o in satirlar if o)
    print("Toplam: %d, öldürülen: %d, skor: %.1f%%" % (
        len(satirlar), olen, 100.0 * olen / len(satirlar)))
```

Aracı, Bölüm 39.4'te gördüğün tarih doğrulayıcısına karşı çalıştıralım. Hedef dosya `tarih.py`'dir; bu bölümün sonunda bu fonksiyonu tamamen ele alacağız. Aşağıda önce yalnızca üç testlik zayıf bir paket var:

```python
from tarih import artik_yil_mi, gecerli_tarih


def test_temel():
    assert gecerli_tarih(2024, 1, 1)
    assert not gecerli_tarih(2023, 2, 29)
    assert artik_yil_mi(2024)
```

Aracın ilk on iki mutantı, zayıf paket ile:

```term
$ python mutasyon.py tarih.py mutasyon/test_zayif.py | head -12
satır 3: 31 -> 32            HAYATTA
satır 3: 28 -> 29            ÖLDÜ
satır 3: 31 -> 32            HAYATTA
satır 3: 30 -> 31            HAYATTA
satır 3: 31 -> 32            HAYATTA
satır 3: 30 -> 31            HAYATTA
satır 4: 31 -> 32            HAYATTA
satır 4: 31 -> 32            HAYATTA
satır 4: 30 -> 31            HAYATTA
satır 4: 31 -> 32            HAYATTA
satır 4: 30 -> 31            HAYATTA
satır 4: 31 -> 32            HAYATTA
```

Yalnızca bir mutant (Şubat 28 → 29) öldü. Gerisinde test paketi, değişikliği fark etmiyor. Bu, kapsamanın gösteremediği bir boşluktur: `gecerli_tarih(2024, 1, 1)` gibi çağrılar kodun büyük kısmını çalıştırır, ama ayların gün sayılarının doğruluğunu sınamaz. Mutasyon testi, bu boşluğu sayısal olarak gösterir. Örnek 4'te bu paketi sistematik olarak güçlendireceğiz.

## 39.8 Özellik tabanlı test, küçültme ve diferansiyel test

Birim testinde girdiyi sen seçersin: "2024-02-29 geçerli, 2023-02-29 değil". Bu yaklaşım, aklına gelen durumları sınar. **Özellik tabanlı test** (property-based testing) tersini yapar: bir özelliği (her girdi için doğru olması gereken bir kuralı) tanımlarsın, çatı binlerce rastgele girdi üretir ve kuralı bozan bir girdi bulursa onu **küçültür** (shrinking): karşı örneği, hatayı hâlâ gösteren en küçük haline indirir.

Python'da bunun standart aracı **Hypothesis**'tir. Bir özellik şu üç parçadan oluşur: `@given` ile girdi stratejisi, bir test fonksiyonu ve (isteğe bağlı) `@settings` ile çalışma ayarları. Bu bölümde `derandomize=True` ayarını kullanıyoruz: Hypothesis her çalıştırmada aynı girdi dizisini üretir, böylece testler tekrarlanabilir kalır (39.11'deki kararsızlık konusuyla doğrudan bağlantılı).

Önce ikili arama (Bölüm 14) üzerinde bir özellik. Aşağıdaki modülde iki sürüm var: biri doğru, biri bir hatayla (döngü koşulu `<` olarak yazılmış; doğrusu `<=`):

```python
"""İkili arama (Bölüm 14). Biri hatalı, biri doğru iki sürüm."""


def ikili_arama_hatali(xs, hedef):
    """HATA: döngü koşulu '<' (olmalı '<='). Tek elemanlı dizide
    ya da aranan değer son adayken döngü hiç ona bakmaz."""
    lo, hi = 0, len(xs) - 1
    while lo < hi:
        orta = (lo + hi) // 2
        if xs[orta] == hedef:
            return orta
        if xs[orta] < hedef:
            lo = orta + 1
        else:
            hi = orta - 1
    return -1


def ikili_arama(xs, hedef):
    lo, hi = 0, len(xs) - 1
    while lo <= hi:
        orta = (lo + hi) // 2
        if xs[orta] == hedef:
            return orta
        if xs[orta] < hedef:
            lo = orta + 1
        else:
            hi = orta - 1
    return -1
```

Hatalı sürümün neden yanlış olduğunu Bölüm 14.5'teki off-by-one kataloğundan tanıyabilirsin: arama aralığının sağ ucu hiç karşılaştırılmaz. Özellik testi iki parçalıdır: bulunan indeks doğruysa değer oradadır; `-1` dönerse değer listede yoktur.

```python
import random
from collections import deque

import pytest
from hypothesis import given, settings, strategies as st

from halka import HalkaTampon
from ikili import ikili_arama, ikili_arama_hatali
from rle import coz, kodla


@settings(derandomize=True, max_examples=300)
@given(st.lists(st.integers(), unique=True).map(sorted),
       st.integers())
def test_ikili_arama_ozelligi(xs, hedef):
    i = ikili_arama(xs, hedef)
    if i == -1:
        assert hedef not in xs
    else:
        assert xs[i] == hedef


@settings(derandomize=True, max_examples=300)
@given(st.lists(st.integers(), unique=True).map(sorted),
       st.integers())
def test_hatali_ikili_arama_ozelligi(xs, hedef):
    i = ikili_arama_hatali(xs, hedef)
    if i == -1:
        assert hedef not in xs
    else:
        assert xs[i] == hedef


@settings(derandomize=True, max_examples=300)
@given(st.text())
def test_rle_gidis_donus(s):
    parcalar = kodla(s)
    assert coz(parcalar) == s
    assert all(k >= 1 for _, k in parcalar)
    assert all(a[0] != b[0] for a, b in zip(parcalar, parcalar[1:]))


def test_halka_referans_deque_ile():
    # Diferansiyel test: iki gerçekleme aynı işlemlerde aynı mı?
    rng = random.Random(42)
    t = HalkaTampon(4)
    ref = deque()
    for _ in range(5000):
        if rng.random() < 0.5:
            x = rng.randint(-9, 9)
            if len(ref) < 4:
                ref.append(x)
                t.ekle(x)
            else:
                with pytest.raises(BufferError):
                    t.ekle(x)
        elif ref:
            assert t.al() == ref.popleft()
        else:
            with pytest.raises(IndexError):
                t.al()
        assert len(t) == len(ref)
```

Test dosyası, ikili aramanın iki sürümünü ve bir **gidiş-dönüş** (round-trip) özelliğini içerir. Gidiş-dönüş, bir kodlama ile çözme işleminin birlikte orijinal veriyi geri vermesi gerektiğini söyler. `rle.py` çalıştırma uzunluğu kodlamasını (`aaab` → `a×3, b×1`) gerçekler:

```python
"""Çalıştırma uzunluğu kodlaması (run-length encoding)."""


def kodla(s):
    cikti = []
    for ch in s:
        if cikti and cikti[-1][0] == ch:
            cikti[-1] = (ch, cikti[-1][1] + 1)
        else:
            cikti.append((ch, 1))
    return cikti


def coz(parcalar):
    return "".join(ch * k for ch, k in parcalar)
```

Hatalı arama sürümünü özellik testi ile çalıştıralım:

```term
$ python -m pytest -q test_ozellik.py -k hatali --tb=short
F                                                                [100%]
============================== FAILURES ===============================
__________________ test_hatali_ikili_arama_ozelligi ___________________
test_ozellik.py:24: in test_hatali_ikili_arama_ozelligi
    @given(st.lists(st.integers(), unique=True).map(sorted),
                   ^^^
test_ozellik.py:29: in test_hatali_ikili_arama_ozelligi
    assert hedef not in xs
E   assert 0 not in [0]
E   Failing test case: test_hatali_ikili_arama_ozelligi(
E       xs=[0],
E       hedef=0,
E   )
======================= short test summary info =======================
FAILED test_ozellik.py::test_hatali_ikili_arama_ozelligi - assert 0 n...
1 failed, 3 deselected in 1.20s
```

Hypothesis, ilk karşılaşmada `xs=[0]`, `hedef=0` karşı örneğini buldu ve raporladı. Bu, tek elemanlı bir dizide arama yapan kişinin ilk akla gelmeyen durumudur; yani küçültme sonucu gerçekten öğretici bir girdi verdi. Küçültmenin ne kadar değerli olduğunu daha büyük bir örnekle görelim: Bölüm 39.6'daki `ortalama` hatası için aynı özelliği yazdık (`test_kapsama_ozellik.py`), bu kez Hypothesis büyük ve gürültülü bir karşı örnekle başladı:

```python
import statistics

import pytest
from hypothesis import given, settings, strategies as st

from kapsama_ornek import ortalama


@settings(derandomize=True, max_examples=300)
@given(st.lists(st.integers(-1000, 1000), min_size=1))
def test_ortalama_ozelligi(xs):
    assert ortalama(xs) == pytest.approx(statistics.fmean(xs))
```

```term
$ python -m pytest -q test_kapsama_ozellik.py --tb=short
F                                                                [100%]
============================== FAILURES ===============================
_______________________ test_ortalama_ozelligi ________________________
test_kapsama_ozellik.py:10: in test_ortalama_ozelligi
    @given(st.lists(st.integers(-1000, 1000), min_size=1))
                   ^^^
test_kapsama_ozellik.py:12: in test_ortalama_ozelligi
    assert ortalama(xs) == pytest.approx(statistics.fmean(xs))
E   assert 0 == 0.5 ± 5.0e-07
E     
E     comparison failed
E     Obtained: 0
E     Expected: 0.5 ± 5.0e-07
E   Failing test case: test_ortalama_ozelligi(
E       xs=[0, 1],
E   )
======================= short test summary info =======================
FAILED test_kapsama_ozellik.py::test_ortalama_ozelligi - assert 0 == ...
1 failed in 1.21s
```

Detaylı izleme (`--hypothesis-verbosity=verbose` ile aldığımız çıktı, `kapsama_ozellik_verbose`), küçültme sürecinde şu adayların hepsinin hâlâ başarısız olduğunu gösterdi: ilk bulunan `[194, -85]`, sonra `[0, -85]`, `[0, 85]` ve en sonunda `[0, 1]`. Şekil 39.6 bu zinciri gösterir. Son örnek, bir insanın hata ayıklarken kolayca görebileceği kadar küçüktür: iki sayı, bir ortalama, bir tam bölme.

![Şekil 39.6: Hypothesis küçültme zinciri: büyük karşı örnekten en küçüğe](gorseller/b39_kucultme.png)

Hypothesis'in küçültme sırası ayrıntılı bir iç algoritmadır; biz yalnızca bu koşuda gözlemlediğimiz adayları gösteriyoruz. Önemli olan, sonuçta elde edilen küçük örneğin tekrarlanabilir olmasıdır: `derandomize=True` ile aynı kod her seferinde aynı zinciri üretir.

**Diferansiyel test.** Bu bölümün önceki bölümlerinde zaten yaptığımız bir şeyi adlandıralım: iki gerçekleme aynı girdiye karşı aynı çıktıyı üretmeli. Bölüm 13'te sabit tohumlu rastgele girdilerle sıralamayı ölçtük; Bölüm 16'da ise 300 rastgele örnekte DP çözümünü kaba kuvvet çözümüyle karşılaştırdık. Bu **çapraz test**tir (diferansiyel test). Referans gerçekleme ne kadar basit ve güvenilirse, test o kadar güçlüdür. Bu bölümde iki örneğimiz var: halka tamponunu Python'un `collections.deque` ile (`test_ozellik.py` içinde, aşağıda gösterilecek), tarih doğrulayıcısını ise `datetime.date` ile karşılaştırıyoruz; `datetime`, geçersiz tarihte `ValueError` fırlatarak bağımsız bir referans sağlar.

**Metamorfik test.** Bazı durumlarda doğru çıktıyı bilmesek de iki girdi arasındaki ilişkiyi bilebiliriz. Bu **metamorfik ilişki** (metamorphic relation) testidir. Örneğin bir listenin elemanlarının sırası değişince ortalama değişmemelidir: `ortalama(xs) == ortalama(xs[::-1])`. Bu tür ilişkiler, referans gerçekleme bulunmadığında özellikle işe yarar (ör. makine öğrenmesi modelleri, Bölüm 54 ve sonrası).

## 39.9 TDD: kırmızı, yeşil, yeniden düzenle

**Test güdümlü geliştirme** (TDD, test-driven development) bir çalışma döngüsüdür: önce başarısız olan bir test yazarsın (kırmızı), sonra o testi geçirecek en basit kodu yazarsın (yeşil), en sonunda kodu temizlersin (yeniden düzenle) ve testler yeşil kalır (Şekil 39.7).

![Şekil 39.7: TDD döngüsü](gorseller/b39_tdd.png)

TDD'nin asıl değeri, kodun ne yapması gerektiğini önce bir testle netleştirmen zorunda kalmasıdır. Kırmızıyı görmek de önemlidir: bir testin hiç kırmızı olmadan geçtiğini gördüğünde, testin gerçekten bir şey sınayıp sınamadığını bilmezsin. Bu bölümde, bir **halka tamponu** (ring buffer) adım adım TDD ile yazılacak. Halka tamponu, sabit kapasiteli bir FIFO yapısıdır: en eski elemanı ilk çıkarır, dolunca yeni eleman eklenemez. Aşağıdaki Örnek 2 bu süreci bütün ayrıntısıyla gösterir; burada yalnızca döngünün ilk turunu özetleyelim.

**TDD'nin sınırları.** TDD her şeyin çözümü değildir. Bir algoritmanın nasıl çalışacağı henüz bilinmiyorsa, önce deneme yapmak ve sonra test yazmak daha verimlidir. Kullanıcı arayüzü, dış sistem entegrasyonu ve performans gibi alanlarda test ilk adımda yazılamayacak kadar belirsiz olabilir. TDD'nin güçlü olduğu yer, **bilinen bir davranışı** kodlarken ve **bir hatayı düzeltirken** gelir: önce hatayı yeniden üreten bir kırmızı test, sonra düzeltme.

## 39.10 Entegrasyon testleri ve C'de test

Birim testleri tek bileşeni sınar; entegrasyon testleri bileşenlerin **birlikte** çalıştığını sınar. Bu testler yavaştır, ama gerçek dünyanın kenar durumlarını (dosya kilitleri, parçalı okumalar, bağlantı kopması) gösterir. Bu bölümde iki gerçek bileşen kullanıyoruz: SQLite (Bölüm 34) ve loopback üzerinde bir TCP soketi (Bölüm 31).

SQLite ile sensör ölçümleri tutan küçük bir depo:

```python
import sqlite3


class OlcumDeposu:
    """Sensör ölçümlerini SQLite dosyasında tutar (Bölüm 34)."""

    def __init__(self, yol):
        self.con = sqlite3.connect(yol)
        self.con.execute(
            "CREATE TABLE IF NOT EXISTS olcum ("
            " id INTEGER PRIMARY KEY,"
            " sensor INTEGER NOT NULL,"
            " deger REAL NOT NULL)")

    def ekle(self, sensor, deger):
        with self.con:
            self.con.execute(
                "INSERT INTO olcum(sensor, deger) VALUES (?, ?)",
                (sensor, deger))

    def son(self, sensor, n):
        cur = self.con.execute(
            "SELECT deger FROM olcum WHERE sensor = ? "
            "ORDER BY id DESC LIMIT ?", (sensor, n))
        return [satir[0] for satir in cur]

    def kapat(self):
        self.con.close()
```

Uzunluk önekli çerçeve okuyucu, Bölüm 31.4'teki düzenin aynısıdır: önce 4 baytlık ağ sırasında (`!I`) uzunluk gelir, sonra o kadar bayt. `tam_oku`, TCP'nin bir bayt akışı olduğunu (Bölüm 31.3) hatırlatır: `recv` istenenden az bayt döndürebilir.

```python
"""Uzunluk önekli çerçeveler (Bölüm 31.4'teki düzen)."""
import struct

MAKS = 1 << 16


def tam_oku(sock, n):
    """Tam n bayt oku: recv kısmi dönebilir (Bölüm 31)."""
    parca = bytearray()
    while len(parca) < n:
        b = sock.recv(n - len(parca))
        if not b:
            raise ConnectionError("karşı taraf kapattı")
        parca += b
    return bytes(parca)


def cerceve_gonder(sock, yuk):
    sock.sendall(struct.pack("!I", len(yuk)) + yuk)


def cerceve_al(sock):
    (n,) = struct.unpack("!I", tam_oku(sock, 4))
    if n > MAKS:
        raise ValueError("çerçeve çok büyük: %d" % n)
    return tam_oku(sock, n)
```

Oturum boyunca yaşayan bir yankı sunucusu (`conftest.py`'de gösterilen fixture) ve bu iki bileşenin birlikte sınandığı testler:

```python
import socket
import struct

import pytest

from cerceve import cerceve_al, cerceve_gonder
from depo import OlcumDeposu


def test_sqlite_veri_yeniden_acilinca_kalir(tmp_path):
    yol = tmp_path / "olcum.db"
    d = OlcumDeposu(yol)
    d.ekle(1, 20.5)
    d.ekle(1, 21.0)
    d.kapat()
    d2 = OlcumDeposu(yol)               # yeni bağlantı, aynı dosya
    assert d2.son(1, 2) == [21.0, 20.5]
    d2.kapat()


def test_soket_yanki(yanki_sunucu):
    with socket.create_connection(("127.0.0.1", yanki_sunucu)) as s:
        cerceve_gonder(s, b"merhaba")
        assert cerceve_al(s) == b"merhaba"


def test_bolunmus_akis_dogru_okunur():
    # Gönderici veriyi 7 baytlık parçalara böler: recv tek seferde
    # tamamını vermez, tam_oku bunu toplamalıdır.
    a, b = socket.socketpair()
    with a, b:
        yuk = b"x" * 1000
        cerceve = struct.pack("!I", len(yuk)) + yuk
        for i in range(0, len(cerceve), 7):
            a.sendall(cerceve[i:i + 7])
        assert cerceve_al(b) == yuk


def test_buyuk_cercevede_bellek_ayrilmadan_reddedilir():
    a, b = socket.socketpair()
    with a, b:
        a.sendall(struct.pack("!I", 1 << 20))
        with pytest.raises(ValueError):
            cerceve_al(b)
```

```term
$ python -m pytest -q test_entegrasyon.py
....                                                             [100%]
4 passed in 0.73s
```

Testler birbirinden bağımsız çalışır: SQLite testi `tmp_path` ile kendi dosyasını kullanır; soket testleri `socketpair` ile çekirdek içinde bir çift uç açar ve `yanki_sunucu` oturum boyunca bir kez başlar. `test_bolunmus_akis_dogru_okunur` testi, 7 baytlık parçalarla gönderilen bir çerçevenin tek bir `recv` çağrısıyla okunamayacağını (ve `tam_oku`'nun bunu toplayabildiğini) sınar.

**C'de test.** C'de yerleşik bir test çatısı yoktur. Bu yüzden küçük bir makro çatısı (`minitest.h`) yazmak, öğretici ve yeterlidir. Makrolar iki şey yapar: bir koşulu kontrol eder ve başarısızlıkta hangi dosya ve satırda olduğunu yazdırır; ayrıca sayaç tutar ve sonunda çıkış kodunu belirler (sıfır = başarılı).

```c
/* minitest.h: birkaç satırlık birim test çatısı (Bölüm 39). */
#ifndef MINITEST_H
#define MINITEST_H
#include <stdio.h>

static int mt_gecen = 0;
static int mt_kalan = 0;

#define CHECK(kosul) do { \
    if (kosul) { mt_gecen++; } \
    else { mt_kalan++; \
        printf("  BAŞARISIZ %s:%d: %s\n", \
               __FILE__, __LINE__, #kosul); } \
} while (0)

#define CHECK_EQ(a, b) do { \
    long long mt_a = (long long)(a); \
    long long mt_b = (long long)(b); \
    if (mt_a == mt_b) { mt_gecen++; } \
    else { mt_kalan++; \
        printf("  BAŞARISIZ %s:%d: %s == %s (%lld != %lld)\n", \
               __FILE__, __LINE__, #a, #b, mt_a, mt_b); } \
} while (0)

#define MT_SONUC() do { \
    printf("%d geçti, %d başarısız\n", mt_gecen, mt_kalan); \
    return mt_kalan == 0 ? 0 : 1; \
} while (0)

#endif
```

Test edilecek C kodu, Python'daki tarih doğrulayıcının C karşılığıdır. İki fonksiyon ekledik: `gun_sayisi_ham`, aralık denetimi olmayan, yani bilerek tehlikeli bir sürümdür; `gun_sayisi` ise denetimlidir.

```c
#ifndef TARIH_H
#define TARIH_H
int artik_yil_mi(int yil);
int gun_sayisi(int yil, int ay);
int gun_sayisi_ham(int yil, int ay);   /* sinir kontrolu yok */
int gecerli_tarih(int yil, int ay, int gun);
#endif
```

```c
#include "tarih.h"

static const int AY_GUN[12] = {31, 28, 31, 30, 31, 30,
                               31, 31, 30, 31, 30, 31};

int artik_yil_mi(int yil) {
    return yil % 4 == 0 && (yil % 100 != 0 || yil % 400 == 0);
}

/* Sinir kontrolu YOK: ay 1..12 disinda okuma tanimsiz davranis. */
int gun_sayisi_ham(int yil, int ay) {
    if (ay == 2 && artik_yil_mi(yil)) return 29;
    return AY_GUN[ay - 1];
}

int gun_sayisi(int yil, int ay) {
    if (ay < 1 || ay > 12) return -1;
    return gun_sayisi_ham(yil, ay);
}

int gecerli_tarih(int yil, int ay, int gun) {
    int n = gun_sayisi(yil, ay);
    return n > 0 && gun >= 1 && gun <= n;
}
```

Test dosyası, denetimli sürümü sınar:

```c
#include "minitest.h"
#include "tarih.h"

int main(void) {
    CHECK(artik_yil_mi(2024));
    CHECK(!artik_yil_mi(1900));
    CHECK(artik_yil_mi(2000));
    CHECK(gecerli_tarih(2024, 2, 29));
    CHECK(!gecerli_tarih(2023, 2, 29));
    CHECK(!gecerli_tarih(2024, 13, 1));
    CHECK(!gecerli_tarih(2024, 4, 31));
    CHECK_EQ(gun_sayisi(2023, 2), 28);
    CHECK_EQ(gun_sayisi(2024, 4), 30);
    CHECK_EQ(gun_sayisi(2024, 13), -1);
    MT_SONUC();
}
```

Derleyip çalıştıralım. Derleme `-Wall -Wextra -std=c11` ile yapılır; sonra sanitizer'lı sürümle de koşacağız. Bu komutlar WSL2 içindeki gcc ile çalıştı; çünkü ASan ve UBSan gibi araçlar Linux'ta olgundur ve Windows'ta MSVC ile farklı davranırlar (Bölüm 6'daki Linux araçları notu).

```term
$ gcc -O2 -Wall -Wextra -std=c11 -o tarih_test \
      tarih_test.c tarih.c
$ ./tarih_test
10 geçti, 0 başarısız
```

Sanitizer'lar, C'nin tanımsız davranışını (UB) çalışma anında yakalar. Sınırlı bir girdi (ay = 13) ile `gun_sayisi_ham`'ı çağıran kasıtlı bir gösterim yapalım:

```c
#include <stdio.h>
#include "tarih.h"

/* Tanimsiz davranis gosterimi: sinirsiz fonksiyona ay = 13. */
int main(void) {
    volatile int s = gun_sayisi_ham(2024, 13);
    printf("sonuc (tanimsiz): %d\n", s);
    return 0;
}
```

Önce sanitizer olmadan derleyip çalıştıralım:

```term
$ gcc -O1 -g -std=c11 -o ub_demo ub_demo.c tarih.c
$ ./ub_demo
sonuc (tanimsiz): 990059265
```

Çıktı bir sayıdır, program hata vermeden çıkar. Bu, tanımsız davranışın en tehlikeli biçimidir: sessizdir ve sonuç rastgeledir. Aynı kodu sanitizer ile derleyelim:

```term
$ gcc -O1 -g -std=c11 -fsanitize=address,undefined \
      -o ub_demo_san ub_demo.c tarih.c
$ ./ub_demo_san
tarih.c:13:18: runtime error: index 12 out of bounds
==431==ERROR: AddressSanitizer: global-buffer-overflow
READ of size 4 at ... thread T0
    #0 ... in gun_sayisi_ham tarih.c:13
[... ASan'in geri kalan satırları kısaltıldı]
```

ASan, sınırı aşan okumayı `tarih.c:13` satırında yakaladı ve dizinin (`AY_GUN`) genel bellek alanının dışında olduğunu söyledi. Kasıtlı kırık testi de burada gösterelim: `kirik_test.c`, `tarih_test.c`'nin bir değer değiştirilmiş kopyasıdır (`gun_sayisi(2024, 4)` için 30 yerine 31 beklenir).

```term
$ ./kirik_test
  BAŞARISIZ kirik_test.c:13: gun_sayisi(2024, 4) == 31 (30 != 31)
9 geçti, 1 başarısız
```

**Sürekli entegrasyonda çalıştırma (köprü).** Bu testlerin her değişiklikte otomatik koşması gerekir. CI/CD boru hattının ayrıntıları Bölüm 42'de; burada yalnızca testlerin nasıl çağrılacağını gösteren bir örnek iş akışı var. Bu dosya bu bölümde çalıştırılmadı; yalnızca yapıyı göstermek için yazıldı:

```text
# .github/workflows/test.yml  (örnek; ayrıntı Bölüm 42'de)
name: test
on: [push, pull_request]
jobs:
  pytest:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pytest pytest-cov hypothesis
      - run: python -m pytest -q --cov --cov-branch
```

C++ için GoogleTest (genel bilgi) benzer bir yapı sunar: test makroları, bir çalıştırıcı ve XML raporu. Bu bölümde kurup çalıştırmadık; yapısı burada tanıtılan `CHECK` makrosuna çok benzer.

## 39.11 Kararsız (flaky) testler

Kararsız test, kod değişmeden bazen geçen, bazen kalan testtir. Bu, test setinin en çok zaman yiyen hastalığıdır: ekip kırmızıya alışır, gerçek hataları gözden kaçırır. Kararsızlığın dört yaygın nedeni vardır (Şekil 39.8).

![Şekil 39.8: Kararsız testlerin dört yaygın nedeni ve çözümleri](gorseller/b39_kararsiz.png)

**Zamanlama.** `sleep` ile iki iş parçacığının sırasını tahmin etmek, yük altında kayar. Bölüm 27'deki senkronizasyon ilkeleri burada da geçerlidir: olay (event) ya da kilit ile bekle, zaman aşımı yalnızca bir üst sınırdır.

**Sıra bağımlılığı.** Test A'nın bıraktığı bir durumu Test B kullanıyorsa, B yalnızca A'dan sonra çalışırsa geçer. Aşağıdaki iki test bunu gösterir:

```python
import random

KAYITLAR = []           # paylaşılan (global) durum


def test_yaz():
    KAYITLAR.append("a")
    assert len(KAYITLAR) == 1


def test_oku():
    # Sıra bağımlılığı: yalnızca test_yaz önce çalıştıysa geçer.
    assert KAYITLAR == ["a"]


def test_rastgele_zar():
    # Tohumsuz rastgelelik: her çalıştırmada farklı bir sonuç.
    assert random.random() > 0.1
```

Bu testte `test_oku`, `test_yaz`'ın bıraktığı listeye bağlıdır. Önce tek başına, sonra ters sırada çalıştıralım:

```term
$ python -m pytest -q test_kararsiz.py::test_oku --tb=no -rf
F                                                                [100%]
======================= short test summary info =======================
FAILED test_kararsiz.py::test_oku - AssertionError: assert [] == ['a']
1 failed in 0.68s
```

```term
$ python -m pytest -q test_kararsiz.py::test_oku \
      test_kararsiz.py::test_yaz --tb=no -rf
F.                                                               [100%]
======================= short test summary info =======================
FAILED test_kararsiz.py::test_oku - AssertionError: assert [] == ['a']
1 failed, 1 passed in 0.66s
```

Dosyadaki sıra (`test_yaz` önce) ile geçer; ters sırada ya da tek başına çalıştırıldığında kırılır. Bu, paylaşılan durumun tipik sonucudur. Çözüm, her testin kendi durumunu kurmasıdır (fixture ile, `autouse` ile temizleyerek):

```python
import random

import pytest

KAYITLAR = []


@pytest.fixture(autouse=True)
def temiz_durum():
    # Her test kendi durumuyla başlar; sıraya bağlı değildir.
    KAYITLAR.clear()
    yield


def test_yaz():
    KAYITLAR.append("a")
    assert KAYITLAR == ["a"]


def test_oku_kendi_kurulumunu_yapar():
    KAYITLAR.extend(["a"])
    assert KAYITLAR == ["a"]


def test_rastgele_zar_tohumlu():
    rng = random.Random(42)           # her çalıştırmada aynı dizi
    assert rng.random() > 0.1
```

```term
$ python -m pytest -q test_kararsiz_duzeltilmis.py
...                                                              [100%]
3 passed in 0.68s
```

**Rastgelelik.** Tohumsuz bir rastgele sayı üreteci, her koşuda farklı bir sonuç verir. Test, bazen kalan bir yapıya dönüşür. Çözüm tohumu sabitlemektir (`random.Random(42)`), böylece her koşuda aynı dizi üretilir. Ancak tohumu sabitlemek bir testi tekrarlanabilir yapar, doğru yapmaz: test hâlâ belirli bir dizi için yazılmıştır. Bu nedenle olasılıksal davranışı ölçmek için tohumsuz çalıştırıp oranı gözlemlemek daha dürüsttür. Aşağıdaki betik, `test_rastgele_zar` testini ayrı süreçlerde 40 kez koşturup kaç kez kaldığını sayar:

```python
"""test_rastgele_zar'ı n kez ayrı süreçte çalıştırıp sayar."""
import subprocess
import sys

n = int(sys.argv[1])
basarisiz = 0
for _ in range(n):
    r = subprocess.run([sys.executable, "-m", "pytest", "-q",
                        "--no-header", "-p", "no:cacheprovider",
                        "test_kararsiz.py::test_rastgele_zar"],
                       capture_output=True)
    if r.returncode != 0:
        basarisiz += 1
print("%d koşu: %d başarısız, %d başarılı" % (
    n, basarisiz, n - basarisiz))
```

```term
$ python kararsiz_say.py 40
40 koşu: 3 başarısız, 37 başarılı
```

Sonuç, koşudan koşuya değişir; bu koşuda 4 kalma gözlemlendi. Test `random.random() > 0.1` koşulunu sınar; beklenen kalma oranı yaklaşık %10'dur. Kaç koşu gerektiği, istediğin güven düzeyine bağlıdır; bu, Bölüm 57'deki istatistiksel anlamlılık ve güven aralığı konusudur.

**Paylaşılan durum.** Global bir liste, bir dosya ya da bir veritabanı testler arasında kalırsa, her test başka testlerin izini taşır. Çözüm, her test için temiz bir kopya kullanmak: `tmp_path`, yeni bir SQLite dosyası, ya da fixture ile sıfırlama.

Kararsız bir testi **bulmanın** yolu tekrarlı çalıştırmaktır (yukarıdaki betik gibi). Bunu otomatikleştiren eklentiler vardır (ör. pytest-repeat); pytest-xdist ile testleri paralel çalıştırmak da kararsızlığı açığa çıkarabilir, çünkü paylaşılan durum paralellikte görünür hale gelir (genel bilgi; bu bölümde kurup denemedik).

## 39.12 Savunma sanayiinde test: gereksinim, MC/DC ve HIL

Savunma ve havacılık yazılımında test, kod kalitesi kadar **kanıt** meselesidir: bir gereksinimin karşılandığını, bu karşılamanın bir testle gösterildiğini ve bu testin kapsama ölçüsünü sağladığını belgelemek gerekir. Bu zincire **iz sürülebilirlik** (traceability) denir: gereksinimden koda, koddan teste ve testten sonuca giden bir zincir. Örnek bir iz sürülebilirlik satırı (hayali bir gereksinim kimliğiyle, yalnızca biçimi göstermek için):

| Gereksinim | Kod | Test | Sonuç |
|---|---|---|---|
| GR-12: tarih geçerliliği | `tarih.py: gecerli_tarih` | `test_tarih.py: test_sinir_degerler` | geçti |

**MC/DC** (Modified Condition/Decision Coverage), karmaşık bir karar ifadesinin her koşulunun sonucu bağımsız olarak etkilediğini gösteren bir kapsama ölçüsüdür. Dal kapsamasından daha güçlüdür: `if (A and B) or C` ifadesinde dal kapsaması yalnızca karar doğru ve yanlış olsun diye ister; MC/DC ise her koşulun (A, B, C) tek başına karara etkisini bir test çiftiyle kanıtlamayı ister. Havacılık yazılım standardı DO-178C'nin en yüksek kritiklik seviyesinde (DAL A) MC/DC kapsamasını istediği bilinen bir gerçektir (genel bilgi). Bir koşul için bağımsız etkiyi göstermek, o koşulu değiştirirken yalnız onun değiştiği ve kararın değiştiği iki testi bulmak demektir. Bu kavramı Örnek 3'te elle türetip bir araçla doğrulayacağız.

Bir uyarı: Python'da `and` ve `or` kısa devre yapar; yani sağdaki koşul, soldaki yeterliyse hiç değerlendirilmeyebilir. Bu, MC/DC'nin koşul bağımsızlığı tanımını bazı durumlarda zorlaştırır (maskeleme MC/DC). Gerçek sertifikasyonda bu ayrıntılar araç ve standart kurallarıyla ele alınır (genel bilgi). GCC 14 ile gelen `-fcondition-coverage` bayrağı MC/DC ölçümü için bir başlangıç noktasıdır; bu makinede yalnızca GCC 13.3 bulunduğu için bu bayrağı deneyemedik.

**Donanım-döngüde test** (HIL, hardware-in-the-loop) bir gömülü sistemi gerçek donanıma bağlayarak, ama fiziksel ortamı simüle ederek test etmektir. Bir sensörün yerine simülatör verisi koyup kontrol yazılımını gerçek mikrodenetleyicide çalıştırmak tipik bir örnektir. Kısım XI'de (Bölüm 43–45) STM32 üzerinde kesme ve iletişim protokollerini yazarken bu kavrama geri döneceğiz; Bölüm 80'in bitirme sisteminde de simülatör ile gerçek donanım arasındaki farkı ölçeceksin.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, Bölüm 5'in altı adımını izler: Anla, Örnekle, Kaba çöz, Örüntü, İyileştir, Doğrula. Her örneğin sonunda elle izleme tablosu ve bir varyasyon sorusu var.

### Örnek 1 (★): Tarih doğrulayıcı için sınır değer testleri

**Adım 1 — Anla.** `gecerli_tarih(yil, ay, gun)` üç sayının gerçek bir Gregoryen tarihi olup olmadığını söyleyecek. Kurallar: ay 1 ile 12 arasında; gün 1 ile ayın gün sayısı arasında. Ayın gün sayısı ayın adına bağlı; yalnızca Şubat artık yılda değişir. Artık yıl kuralı: 4'e bölünen yıllar artıktır, ama 100'e bölünenler artık değildir, 400'e bölünenler yine artıktır.

**Adım 2 — Örnekle.** Birkaç elle doğrulanabilir girdi: `(2024, 2, 29)` geçerli (2024 artık yıl); `(2023, 2, 29)` geçersiz; `(1900, 2, 29)` geçersiz (100'e bölünüyor, 400'e bölünmüyor); `(2000, 2, 29)` geçerli (400'e bölünüyor); `(2024, 4, 31)` geçersiz (Nisan 30 çeker).

**Adım 3 — Kaba çöz.** İlk akla gelen çözüm, ay için bir `if` zinciri ve Şubat için bir dal yazmaktır. Bu çözüm işe yarar, ama testi nasıl yazacağını söylemez: "her kuralı bir kez dene" demek, eşikleri (1, 12, 28, 29, 30, 31) ve sınır dışını (0, 13, 32) gözden kaçırmaya yol açar.

**Adım 4 — Örüntü.** Her değişkenin bir alt sınırı, bir üst sınırı ve sınırın dışı vardır. Bu, **sınır değer analizi**dir. Ayrıca artık yıl kuralı üç eşiğe sahiptir: 4, 100 ve 400. Test listesini bu eşiklerden türetmek, tahmin etmekten daha güvenilirdir.

**Adım 5 — İyileştir.** Gün sayılarını bir tabloya koyup artık yılı ayrı bir fonksiyon yaparsak kod sadeleşir. Testleri `parametrize` ile tablo hâline getirirsek her eşik ayrı bir test olur. Ayrıca `datetime.date` bağımsız bir referans olduğundan, 1900–2100 aralığındaki her yıl-ay-gün üçlüsünü (32 güne kadar) karşılaştırabiliriz.

```python
"""Gregoryen takvimde tarih doğrulayıcı (Bölüm 39, Örnek 1)."""

AY_GUN_SAYISI = [31, 28, 31, 30, 31, 30,
                 31, 31, 30, 31, 30, 31]


def artik_yil_mi(yil):
    """400'e bölünen yıllar ve 4'e bölünüp 100'e bölünmeyenler."""
    return yil % 4 == 0 and (yil % 100 != 0 or yil % 400 == 0)


def gun_sayisi(yil, ay):
    """Ayın gün sayısı. Ay 1..12 aralığında olmalıdır."""
    if ay == 2 and artik_yil_mi(yil):
        return 29
    return AY_GUN_SAYISI[ay - 1]


def gecerli_tarih(yil, ay, gun):
    """Üçlünün gerçek bir Gregoryen tarihi olup olmadığını söyler."""
    if not 1 <= ay <= 12:
        return False
    return 1 <= gun <= gun_sayisi(yil, ay)
```

```python
import datetime

import pytest

from tarih import artik_yil_mi, gecerli_tarih


# Sınır değer analizi: her aralığın iki ucu ve bir dışı.
@pytest.mark.parametrize("yil, ay, gun, beklenen", [
    (2024, 1, 1, True),      # ilk gün
    (2024, 12, 31, True),    # son gün
    (2024, 1, 0, False),     # bir altı
    (2024, 1, 32, False),    # bir üstü
    (2024, 0, 15, False),    # ay alt sınırın dışı
    (2024, 13, 15, False),   # ay üst sınırın dışı
    (2023, 2, 28, True),     # normal yıl, Şubat'ın son günü
    (2023, 2, 29, False),    # normal yıl, 29 Şubat yok
    (2024, 2, 29, True),     # artık yıl
    (2000, 2, 29, True),     # 400'e bölünen artık yıl
    (1900, 2, 29, False),    # 100'e bölünen, 400'e bölünmeyen
    (2024, 4, 30, True),     # 30 çeken ay
    (2024, 4, 31, False),    # 30 çeken ayın 31'i
])
def test_sinir_degerler(yil, ay, gun, beklenen):
    assert gecerli_tarih(yil, ay, gun) is beklenen


@pytest.mark.parametrize("yil, beklenen", [
    (1900, False), (2000, True), (2024, True), (2023, False),
])
def test_artik_yil(yil, beklenen):
    assert artik_yil_mi(yil) is beklenen


def test_1900_2100_tum_gunler_datetime_ile_ayni():
    # datetime.date geçersiz tarihte ValueError verir: bağımsız
    # bir referans. Her yıl, ay ve gün için karşılaştır.
    for yil in range(1900, 2101):
        for ay in range(1, 13):
            for gun in range(1, 33):
                try:
                    datetime.date(yil, ay, gun)
                    ref = True
                except ValueError:
                    ref = False
                sonuc = gecerli_tarih(yil, ay, gun)
                assert sonuc == ref, (yil, ay, gun)
```

**Adım 6 — Doğrula.** Testleri çalıştırıp sınır değerlerin sonuçlarını elle hesaplanmış değerlerle karşılaştıralım:

```term
$ python -m pytest -q test_tarih.py
..................                                               [100%]
18 passed in 0.74s
```

Aşağıdaki iz tablosu üç kaynağın (elle kural, `gecerli_tarih`, `datetime`) aynı sonucu verdiğini gösterir:

| Girdi (yıl, ay, gün) | Kural (elle) | `gecerli_tarih` | `datetime` |
|---|---|---|---|
| (2024, 2, 29) | artık yıl, Şubat 29 var | True | geçerli |
| (2023, 2, 29) | normal yıl | False | ValueError |
| (1900, 2, 29) | 100'e bölünür, 400'e değil | False | ValueError |
| (2000, 2, 29) | 400'e bölünür | True | geçerli |
| (2024, 4, 31) | Nisan 30 çeker | False | ValueError |
| (2024, 13, 1) | ay 12'yi aşıyor | False | ValueError |

**Bunu AI'sız yazabilir misin?** Ocak–Aralık gün sayılarını bir tablo olarak yazmadan, yalnızca artık yıl kuralı ve bir `if` zinciriyle `gun_sayisi(yil, ay)` fonksiyonunu yaz. Sonra sınır değerler için en az yedi test çıkar: hangi girdileri ve neden seçtiğini tek cümlede açıkla.

### Örnek 2 (★★): Halka tamponu, TDD ile adım adım

**Adım 1 — Anla.** Halka tamponu (FIFO) sabit kapasiteli bir kuyruktur. `ekle` yeni bir eleman koyar; kapasite dolduysa hata verir. `al` en eski elemanı çıkarır; boşsa hata verir. Bağlantılı liste ya da dinamik dizi ile de yazılabilir; burada sabit kapasiteli dizi (ve sonunda dairesel indeks) hedeftir.

**Adım 2 — Örnekle.** Kapasite 3 olan bir tampona 1, 2, 3 ekleyelim. `al` 1 döndürmeli, sonra 2, sonra 3. Dördüncü `ekle` (dolu iken) reddedilmeli. Bu, ilk test listesidir.

**Adım 3 — Kaba çöz (kırmızı, sonra yeşil).** Önce yalnızca ilk üç testi yazarız. Modül yokken çalıştırmak **kırmızı** verir: test, henüz var olmayan bir şeyi sınayamaz.

```python
import pytest

from halka import HalkaTampon


def test_yeni_tampon_bostur():
    t = HalkaTampon(3)
    assert t.bos()
    assert len(t) == 0


def test_fifo_sirasi():
    t = HalkaTampon(3)
    t.ekle(1)
    t.ekle(2)
    assert t.al() == 1
    assert t.al() == 2


def test_bosken_al_hata_verir():
    with pytest.raises(IndexError):
        HalkaTampon(3).al()
```

```term
$ python -m pytest -q test_halka.py | tail -9
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
test_halka.py:3: in <module>
    from halka import HalkaTampon
E   ModuleNotFoundError: No module named 'halka'
======================= short test summary info =======================
ERROR test_halka.py
!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!
1 error in 0.90s
```

En basit çözüm bir liste kullanmaktır: `ekle` sona ekler, `al` baştan çıkarır. Bu çözüm üç testi geçirir (**yeşil**):

```python
class HalkaTampon:
    """Adım 2: en basit çözüm, düz liste."""

    def __init__(self, kapasite):
        self.kapasite = kapasite
        self.veri = []

    def __len__(self):
        return len(self.veri)

    def bos(self):
        return not self.veri

    def ekle(self, x):
        self.veri.append(x)

    def al(self):
        if not self.veri:
            raise IndexError("tampon boş")
        return self.veri.pop(0)
```

```term
$ python -m pytest -q test_halka.py
.....                                                            [100%]
5 passed in 0.66s
```

**Adım 4 — Örüntü.** Testi tamamlayalım: dolu iken eklemenin hata vermesi ve sarmanın (wrap-around) çalışması. Dolu testi eklenince naif liste **kırmızı** verir, çünkü liste kapasiteyi bilmez. Sarma testi ise naif listede de geçer: liste büyüdüğü için sarma gerekmez. Bu gözlem önemlidir: test, davranışı sınar, yapıyı sınamaz. Kapasite kontrolünü ekleyince dolu testi yeşile döner.

```term
$ python -m pytest -q test_halka.py
.....                                                            [100%]
5 passed in 0.67s
```

```python
class HalkaTampon:
    """Adım 2: en basit çözüm, düz liste."""

    def __init__(self, kapasite):
        self.kapasite = kapasite
        self.veri = []

    def __len__(self):
        return len(self.veri)

    def bos(self):
        return not self.veri

    def ekle(self, x):
        if len(self.veri) >= self.kapasite:
            raise BufferError("tampon dolu")
        self.veri.append(x)

    def al(self):
        if not self.veri:
            raise IndexError("tampon boş")
        return self.veri.pop(0)
```

```term
$ python -m pytest -q test_halka.py
.....                                                            [100%]
5 passed in 0.71s
```

**Adım 5 — İyileştir (yeniden düzenle).** Liste yerine sabit bir dizi ve iki indeks (`_bas`, `_boyut`) kullanalım; indeksler `% kapasite` ile sarar. Bu, `pop(0)`'ın O(n) maliyetini de ortadan kaldırır. Yeniden düzenleme sırasında tüm testlerin yeşil kalması, testlerin bu işin güvenlik ağı olduğunu gösterir. Final kod ve testler:

```python
class HalkaTampon:
    """Sabit kapasiteli FIFO halka tamponu (dizi tabanlı)."""

    def __init__(self, kapasite):
        if kapasite <= 0:
            raise ValueError("kapasite pozitif olmalı")
        self._veri = [None] * kapasite
        self._bas = 0       # en eski elemanın indeksi
        self._boyut = 0     # tampondaki eleman sayısı

    def __len__(self):
        return self._boyut

    def bos(self):
        return self._boyut == 0

    def ekle(self, x):
        if self._boyut == len(self._veri):
            raise BufferError("tampon dolu")
        son = (self._bas + self._boyut) % len(self._veri)
        self._veri[son] = x
        self._boyut += 1

    def al(self):
        if self._boyut == 0:
            raise IndexError("tampon boş")
        x = self._veri[self._bas]
        self._veri[self._bas] = None
        self._bas = (self._bas + 1) % len(self._veri)
        self._boyut -= 1
        return x
```

```python
import pytest

from halka import HalkaTampon


def test_yeni_tampon_bostur():
    t = HalkaTampon(3)
    assert t.bos()
    assert len(t) == 0


def test_fifo_sirasi():
    t = HalkaTampon(3)
    t.ekle(1)
    t.ekle(2)
    assert t.al() == 1
    assert t.al() == 2


def test_bosken_al_hata_verir():
    with pytest.raises(IndexError):
        HalkaTampon(3).al()


def test_dolu_iken_ekle_hata_verir():
    t = HalkaTampon(2)
    t.ekle(1)
    t.ekle(2)
    with pytest.raises(BufferError):
        t.ekle(3)


def test_sarma_kapasite_asilmadan_yeniden_kullanilir():
    t = HalkaTampon(3)
    for x in (1, 2, 3):
        t.ekle(x)
    assert t.al() == 1       # bas ilerler, yer açılır
    t.ekle(4)                # 4, 1'in eski yerine yazılır
    assert [t.al(), t.al(), t.al()] == [2, 3, 4]
```

```term
$ python -m pytest -q test_halka.py
.....                                                            [100%]
5 passed in 0.70s
```

**Adım 6 — Doğrula.** Birim testlerine ek olarak bir diferansiyel test yazalım: 5000 rastgele işlemde (sabit tohum 42) halka tamponunu `collections.deque` ile karşılaştıralım. Bu test `test_ozellik.py` içinde (39.8) çalışır ve geçmiştir (`ozellik_ok`). Aşağıdaki iz tablosu, TDD turlarının özetidir:

| Tur | Eklenen test | Sonuç | Kod durumu |
|---|---|---|---|
| 1 | boş, FIFO, boşken al | kırmızı (modül yok) | yok |
| 2 | (aynı 3 test) | yeşil | liste |
| 3 | dolu iken ekle | kırmızı (DID NOT RAISE) | liste |
| 3 | sarma | yeşil (liste ile de geçer) | liste |
| 4 | (dolu kontrolü) | yeşil | liste + kapasite |
| 5 | (yeni test yok) | yeşil | dairesel dizi |

**Bunu AI'sız yazabilir misin?** Kapasite 0 ya da negatif olduğunda kurucunun `ValueError` fırlatması gerekir. Bu davranış `halka.py`'de var ama testlerde sınanmıyor. Önce kırmızı bir test yaz, sonra kodun zaten yeşil olduğunu gözle doğrula ve son olarak testi bir mutant (`<=` yerine `<`) ile çalıştırıp öldüğünü göster. Bu üç adımı, bu bölümdeki TDD döngüsüyle aynı sırayla yaz.

### Örnek 3 (★★): `(A ve B) veya C` için MC/DC test kümesi

**Adım 1 — Anla.** Karar `(A and B) or C` biçimindedir; üç koşul (A, B, C) vardır. MC/DC, her koşul için şu iki şeyi ister: iki test vardır, biri yalnızca o koşulu değiştirir, ve kararın sonucu bu iki testte farklıdır. Bu, koşulun "bağımsız etkisini" gösterir.

**Adım 2 — Örnekle.** Koşul A için bir çift bulalım: B doğru, C yanlış tutalım. Bu durumda karar, A'ya göre doğrudan değişir: `TTF` (sonuç T) ile `FTF` (sonuç F). Koşul B için: A doğru, C yanlış; `TTF` ile `TFF` (sonuç T'den F'ye). Koşul C için: A ve B'nin ikisi de yanlış olmalı ki `(A and B)` yanlış olsun; `TFF` (sonuç F) ile `TFT` (sonuç T).

**Adım 3 — Kaba çöz.** Her koşul kombinasyonunu denemek, üç koşul için 2³ = 8 test verir. Bu, MC/DC'nin istediğinden fazladır ve hangi testlerin gerekli olduğunu söylemez.

**Adım 4 — Örüntü.** Her koşul için bir çift gerekiyor ve çiftler birbirini paylaşabilir. Üç koşul için dört testin yeterli olabileceğini görüyoruz: çiftler arasında ortak test kullanılır. Genel olarak n bağımsız koşul için en az n + 1 test gerekir (en iyi durum, genel bilgi).

**Adım 5 — İyileştir.** Seçimi `TTF`, `FTF`, `TFF`, `TFT` olarak yapalım. Koşul A çifti: `TTF`–`FTF`; koşul B çifti: `TTF`–`TFF`; koşul C çifti: `TFF`–`TFT`. Dört test, üç koşulu da kapsıyor. Bunu bir araçla doğrulayalım:

```python
"""MC/DC denetçisi: karar (A and B) or C için test kümesini sınar.

Bir koşulun MC/DC kapsamı: o koşulu yalnız değiştiren ve kararın
sonucunu da değiştiren bir test çifti kümede bulunmalıdır.
"""
from itertools import combinations, product

KOSUL_ADLARI = ["A", "B", "C"]


def karar(a, b, c):
    return (a and b) or c


def ac(metin):
    """'TTF' -> (True, True, False)"""
    return tuple(ch == "T" for ch in metin)


def etiket(v):
    return "".join("T" if x else "F" for x in v)


def bagimsiz_cift(kume, i):
    """Koşul i için bağımsız etkisi gösteren bir (x, y) çifti."""
    for x, y in combinations(kume, 2):
        fark = [k for k in range(3) if x[k] != y[k]]
        if fark == [i] and karar(*x) != karar(*y):
            return x, y
    return None


def rapor(kume):
    print("test kümesi:", " ".join(etiket(v) for v in kume))
    tamam = True
    for i, ad in enumerate(KOSUL_ADLARI):
        cift = bagimsiz_cift(kume, i)
        if cift is None:
            tamam = False
            print("  %s: KAPSANMADI" % ad)
        else:
            x, y = cift
            print("  %s: %s -> %s  (sonuç %s -> %s)" % (
                ad, etiket(x), etiket(y),
                "T" if karar(*x) else "F",
                "T" if karar(*y) else "F"))
    print("  MC/DC:", "TAM" if tamam else "EKSİK")
    return tamam


def en_kucuk_kumeler(boyut_ust=8):
    """Tüm 8 girdi üzerinde MC/DC sağlayan en küçük kümeleri bul."""
    evren = list(product([True, False], repeat=3))
    for n in range(1, boyut_ust + 1):
        bulunan = []
        for kume in combinations(evren, n):
            if all(bagimsiz_cift(kume, i) for i in range(3)):
                bulunan.append(kume)
        if bulunan:
            return n, bulunan
    return None, []


if __name__ == "__main__":
    print("El ile türetilen küme:")
    el = [ac("TTF"), ac("FTF"), ac("TFF"), ac("TFT")]
    rapor(el)
    print()
    print("Eksik küme (TFT çıkarıldı):")
    rapor(el[:3])
    print()
    n, kumeler = en_kucuk_kumeler()
    print("En küçük MC/DC kümesi boyutu:", n)
    print("Bu boyutta bulunan küme sayısı:", len(kumeler))
    for k in kumeler[:3]:
        print("  ", " ".join(etiket(v) for v in k))
```

**Adım 6 — Doğrula.** Araç, elle seçilen dört testin tam MC/DC sağladığını; birini çıkarınca C koşulunun kapsanmadığını gösteriyor. Tüm 8 girdi üzerinde yapılan aramada da en küçük boyutun 4 olduğu ve bu boyutta iki farklı küme bulunduğu görülüyor:

```term
$ python mcdc.py
El ile türetilen küme:
test kümesi: TTF FTF TFF TFT
  A: TTF -> FTF  (sonuç T -> F)
  B: TTF -> TFF  (sonuç T -> F)
  C: TFF -> TFT  (sonuç F -> T)
  MC/DC: TAM

Eksik küme (TFT çıkarıldı):
test kümesi: TTF FTF TFF
  A: TTF -> FTF  (sonuç T -> F)
  B: TTF -> TFF  (sonuç T -> F)
  C: KAPSANMADI
  MC/DC: EKSİK

En küçük MC/DC kümesi boyutu: 4
Bu boyutta bulunan küme sayısı: 2
   TTF TFT TFF FTF
   TTF TFF FTT FTF
```

Aşağıdaki iz tablosu, her koşulun bağımsız etkisini gösteriyor:

| Koşul | Çift (girdi) | Çiftte değişen | Karar sonucu |
|---|---|---|---|
| A | TTF → FTF | yalnız A | T → F |
| B | TTF → TFF | yalnız B | T → F |
| C | TFF → TFT | yalnız C | F → T |

![Şekil 39.9: (A ve B) veya C için doğruluk tablosu ve seçilen dört test](gorseller/b39_mcdc.png)

**Bunu AI'sız yazabilir misin?** Karar `(A or B) and C` olsun. Dört testlik bir MC/DC kümesini kâğıtta türet, sonra `mcdc.py`'deki `karar` fonksiyonunu değiştirerek aracın bu kümeyi doğrulayıp doğrulamadığını kontrol et.

### Örnek 4 (★★★): Mutasyon testiyle zayıf bir paketi güçlendirmek

**Adım 1 — Anla.** Elimizde `tarih.py` ve üç paket var: zayıf (3 test), orta (sınır değerler, 13 + 4 test), güçlü (sınır + tüm 1900–2100 aralığı, `datetime` ile karşılaştırma). Hedef, mutasyon skorunu yükseltmek ve her hayatta kalan mutantın nedenini bulmaktır.

**Adım 2 — Örnekle.** Zayıf pakette Şubat'ı 28'den 29'a çevirmek mutantını (`satır 3: 28 -> 29`) test şunu yakalar: `gecerli_tarih(2023, 2, 29)` artık geçerli sayılır ve test kırılır. Ama Mart'ı 31'den 32'ye çevirmek (`satır 3: 31 -> 32`) yakalanmaz: hiçbir test Mart 32'yi denemez.

**Adım 3 — Kaba çöz.** Üç paketin hepsini aynı 36 mutant üzerinde çalıştıralım. Zayıf paketin skoru %38,9 (14/36) çıktı:

```python
"""Dört test paketinin mutasyon skorunu CSV'ye yazar (Bölüm 39)."""
import csv
import os
import sys

from mutasyon import calistir

KOK = os.path.dirname(os.path.abspath(__file__))
CIKTI = sys.argv[1]
PAKETLER = [("zayif", "mutasyon/test_zayif.py"),
            ("orta", "mutasyon/test_orta.py"),
            ("guclu_v1", "mutasyon/test_guclu_v1.py"),
            ("guclu_v2", "mutasyon/test_guclu_v2.py")]

satirlar = []
for ad, yol in PAKETLER:
    sonuc = calistir(os.path.join(KOK, "tarih.py"),
                     os.path.join(KOK, yol))
    toplam = len(sonuc)
    olen = sum(1 for _, o in sonuc if o)
    skor = 100.0 * olen / toplam
    satirlar.append([ad, toplam, olen, "%.1f" % skor])
    print(ad, toplam, olen, "%.1f" % skor, flush=True)

with open(CIKTI, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["paket", "mutant", "oldurulen", "skor_yuzde"])
    w.writerows(satirlar)
print("yazıldı:", CIKTI)
```

Bu betik her paket için aracı çalıştırıp skoru CSV dosyasına yazar. Sonuçlar:

```term
$ cat veri/b39_mutasyon.csv
paket,mutant,oldurulen,skor_yuzde
zayif,36,14,38.9
orta,36,26,72.2
guclu_v1,36,30,83.3
guclu_v2,36,36,100.0
```

**Adım 4 — Örüntü.** Orta paket %72,2'ye çıkar: sınır değerler Şubat, Nisan ve Haziran gibi kritik ayların eşiklerini yakalar, ama her ayın gün sayısını ayrı ayrı denemez. Güçlü v1 (`range(1, 32)`) %83,3'tür ve hayatta kalan altı mutant bir örüntü oluşturur: hepsi 31 günlü aylarda (Mart, Mayıs, Temmuz, Ağustos, Ekim, Aralık) gün 32 denemesi. Yani test döngüsü `range(1, 32)` ile yazıldığı için gün 32 hiç denenmemiştir. Bu bir hata ayıklama ipucudur: kod doğru, test eksik. Hayatta kalan mutantların hiçbiri eşdeğer değildir; üçü de gerçek bir boşluktur.

```term
$ python mutasyon.py tarih.py mutasyon/test_guclu_v1.py | grep HAYATTA
satır 3: 31 -> 32            HAYATTA
satır 3: 31 -> 32            HAYATTA
satır 4: 31 -> 32            HAYATTA
satır 4: 31 -> 32            HAYATTA
satır 4: 31 -> 32            HAYATTA
satır 4: 31 -> 32            HAYATTA
```

**Adım 5 — İyileştir.** Tek satır değişiklik: `range(1, 32)` yerine `range(1, 33)`. Bu değişikliği, her gün için yapılan kontrolde 32. günü de içerecek şekilde yaptık. Güncel test dosyası (`test_tarih.py`) bu düzeltmeyi içerir; kopya olan v1 paketi yalnızca bu sayıda farklıdır.

**Adım 6 — Doğrula.** Düzeltilmiş paket (v2) 36 mutantın 36'sını öldürdü:

```term
$ python mutasyon.py tarih.py mutasyon/test_guclu_v2.py | tail -1
Toplam: 36, öldürülen: 36, skor: 100.0%
```

Aşağıdaki iz tablosu, altı mutantın dört pakette nasıl davrandığını gösterir:

| Mutant | Zayıf | Güçlü v1 | Güçlü v2 |
|---|---|---|---|
| satır 3: Ocak 31 → 32 | hayatta | öldü | öldü |
| satır 3: Şubat 28 → 29 | öldü | öldü | öldü |
| satır 3: Mart 31 → 32 | hayatta | hayatta | öldü |
| satır 3: Nisan 30 → 31 | hayatta | öldü | öldü |
| satır 4: Temmuz 31 → 32 | hayatta | hayatta | öldü |
| satır 4: Eylül 30 → 31 | hayatta | öldü | öldü |

Skorun seyri, paketin ne kadar güçlendiğini gösterir (Şekil 39.10). Ölçüm, tek bir modül (`tarih.py`) ve tek bir mutant kümesi üzerinde; bu yüzden genelleme yapmak için farklı modüllerde de denemek gerekir.

![Şekil 39.10: Dört test paketinin mutasyon skorları (engine/veri/b39_mutasyon.csv)](gorseller/b39_mutasyon_skor.png)

**Bunu AI'sız yazabilir misin?** `halka.py` için mutasyon aracını çalıştır (hedef: `halka.py`, test: `test_halka.py`). Hayatta kalan mutantları listele. Her biri için ya yeni bir test yaz ya da mutantın eşdeğer olduğunu açıkla. Sonunda skorunun neden %100'e ulaşamayabileceğini tartış.

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Bu bölümün projeleri test yazma kasını geliştirmek için var; testi bir araca ürettirirsen sınadığın şey aracın kararıdır, senin değil. Testleri kendin yaz, kırmızıyı kendin gör.
:::

### Proje 1 (★★): Mini test çatısı

**Amaç:** pytest'in arkasındaki üç mekanizmayı (keşif, fixture ve parametrize) kendi elinle kurmak. Amaç pytest'in tamamını yazmak değil; keşif, parametrize ve hata raporunun nasıl çalıştığını görmek.

**Yapılacak:** Yalnızca standart kütüphane (`importlib`, `inspect`, `traceback`) ile küçük bir çatı yaz. Çatı şunları yapsın:

- Verilen bir `.py` dosyasında `test_` ile başlayan fonksiyonları bulup çalıştırsın (keşif).
- `@parametrize(parametre_adi, [degerler])` süsleyicisi ile bir testi çok girdiyle koştursun; her satır ayrı raporlansın.
- Parametre adı bir `@fixture` fonksiyonunun adıyla eşleşirse fixture'ı çağırıp değerini versin.
- Sonunda geçen ve kalan sayısını, her başarısız testin adını ve hata metnini yazdırsın; başarısızlık varsa çıkış kodu 1 olsun.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Keşif için modül nesnesinde `dir()` ve `callable` kullan. Parametrize'ı bir fonksiyon özniteliği olarak sakla (`f.parametreler = ...`), koşturucu o özniteliği okusun. Fixture çözümlemesinde `inspect.signature(f).parameters` ile parametre adlarını al. Hata metni için `traceback.format_exc()` yeterlidir.

**Başarı kriterleri:**

- Bölüm 39.4'teki `test_tarih.py` dosyasının parametrik kısmını (`test_sinir_degerler`) kendi çatında koşturabiliyorsun ve 13 satırın her biri ayrı raporlanıyor.
- Kasıtlı olarak bir girdiyi bozduğunda çatın hangi satırın kırıldığını ve beklenen/gerçek değeri söylüyor.
- Bir fixture'ı iki farklı test paylaşıyor ama her test kendi kopyasını alıyor (çatında fixture her testte yeniden çağrılıyor).

### Proje 2 (★★★): Çerçeve okuyucuyu test paketiyle sarmak ve mutasyon skoru hedeflemek

**Amaç:** Bölüm 31.4'teki uzunluk önekli çerçeve okuyucuyu bir test paketiyle sarıp bu paketin kalitesini mutasyon skoruyla ölçmek. Bu proje, Bölüm 39'un tüm araçlarını (birim, sınır, özellik, entegrasyon, mutasyon) bir arada kullanır.

**Yapılacak:** Bölüm 39.10'daki `cerceve.py` dosyasını temel al. Şu davranışları sınayan bir paket yaz:

- **Birim:** uzunluk 0 olan çerçeve; uzunluk tam olarak `MAKS` olan çerçeve (kabul edilmeli); `MAKS + 1` (`ValueError` fırlatmalı).
- **Özellik:** rastgele bir yük (`hypothesis` ile) bir çerçeveye konduktan sonra, gönderici onu rastgele parçalara bölerek yazsın; alıcı yükü aynen geri okusun.
- **Entegrasyon:** `socketpair` üzerinden iki yönlü, art arda birkaç çerçeve.
- **Mutasyon:** 39.7'deki `mutasyon.py` aracını bu dosyaya uygula ve skoru ölç.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** `tam_oku` içindeki döngünün kapanış koşulunu ve `recv` boş dönüş durumunu ayrı birer test olarak düşün. Mutasyon skorunda hayatta kalan mutantları tek tek incele: birçoğu `MAKS` sınırıyla ilgili olacaktır (`>` ile `>=` farkı gibi). Eşdeğer bir mutant çıkarsa bunu bir cümleyle gerekçelendir.

**Başarı kriterleri:**

- Paket, `cerceve.py` üzerindeki mutasyon skorunun en az %90 olduğunu gösteriyor. Skoru ve hayatta kalan mutantların listesini raporla.
- Hayatta kalan her mutant için ya bir test eklenmiş ya da eşdeğer olduğu gerekçelendirilmiş.
- Paket, her çalıştırmada aynı sonucu veriyor (tohum sabit, sıra bağımsız).

### Ek Alıştırmalar

**Zorluk etiketleri:** ★ kolay, ★★ orta, ★★★ zor. Mülakat etiketli sorular klasik mülakat problemleridir; önce yalnızca test listesini yaz, sonra kodu yaz.

1. **(★) Palindrom.** `palindrom_mu(s)` için test listesi yaz: boş metin, tek karakter, büyük-küçük harf, boşluk ve noktalama, Türkçe karakterler (`"Kayak"`, `"İstanbul"`). Hangi girdi için testin hangi durumu sınadığını tek cümlede açıkla.
2. **(★★) İki toplam (Mülakat).** Bir dizide iki elemanın toplamı hedefe eşit olan bir çift bulan fonksiyon için test listesi yaz. Negatif sayılar, aynı elemanın iki kez kullanılması, hedefin hiç bulunmaması ve boş dizi durumlarını ekle. Sonra karma tabloyla `O(n)` çözümünü yaz ve testlerle doğrula.
3. **(★★) Min'li yığın (Mülakat).** `push`, `pop` ve `min` işlemleri olan ve `min` işlemini `O(1)` tutan bir yığın için TDD ile çalış: kırmızı testleri sırayla yaz, her turda yeşil kodu ve yeniden düzenlemeyi göster.
4. **(★) Fizz–Buzz parametrize tablosu.** 1 ile 30 arasındaki sayılar için beklenen çıktıyı bir `parametrize` tablosuna yaz. 3'ün, 5'in ve 15'in katlarını ayrı satırlarda kapsa.
5. **(★★★) LRU önbellek (Mülakat).** Kapasiteli bir LRU önbelleği için test senaryolarını yaz: kapasite dolunca en az kullanılanın atılması, `get` işleminin bir girdiyi "yeni" yapması, aynı anahtara yeniden `put` yapmanın değeri güncellemesi. Testler kodundan önce yazılmalı.
6. **(★★) İkili aramayı sına.** Bölüm 39.8'deki `ikili_arama_hatali` için bir özellik testi yetiyor mu? Hatayı yakalamayan ama yakalayan üç farklı girdi kümesi tasarla ve neden yakalamadığını açıkla. (Bölüm 14.5'teki off-by-one kataloğu bu konuda yardımcı olur.)
7. **(★) Fake mi, mock mu?** `test_siparis.py` içindeki `BellekDeposu` yerine bir `Mock()` kullanan bir test yazsaydın neyi kaybederdin? Bir cümleyle yaz ve kırılganlığın kaynağını göster.
8. **(★★) Üç mutant.** `ortalama` fonksiyonu için (Bölüm 39.6'daki `kapsama_ornek.py`) üç mutant tasarla: biri `//` yerine `/` koyar, biri boş liste kontrolünü kaldırır, biri `len(xs)` yerine `len(xs) + 1` yazar. Bu mutantlardan hangisinin mevcut testlerle hayatta kalacağını tahmin et, sonra çalıştır.
9. **(★★★) Kararsız test istatistiği (Mülakat).** Bir testin yaklaşık %2 olasılıkla kaldığını gözlemledin. Bunu güvenilir biçimde ayırt etmek için kaç koşu gerekir? Bir kalma oranı için güven aralığını nasıl hesaplarsın ve testi "kararlı" ilan etmek için hangi kriteri koyarsın?
10. **(★★) Başka bir MC/DC kümesi.** `(A or B) and C` kararı için dört testlik bir MC/DC kümesi türet. Sonra Örnek 3'teki `mcdc.py` aracının `karar` fonksiyonunu bu yeni karara göre değiştir ve kümeni araçla doğrula.
11. **(★★★) Disk dolu simülasyonu (Mülakat).** Bir dosyaya satır yazan `kaydet(yol, satirlar)` fonksiyonu için test yaz. `tmp_path` kullan. Disk dolu durumunu (yazma sırasında `OSError`) nasıl simüle edersin? Gerçek bir dolu disk olmadan bunu yapabilmek neden önemlidir?
12. **(★★) Halka tamponunun boş kenarı.** Bölüm 39.9'daki `HalkaTampon(0)` çağrısı `ValueError` fırlatmalı. Bu davranışı sınayan testi yaz; önce kırmızı olduğunu göster ya da neden zaten yeşil olduğunu açıkla.

## Kod Okuma Egzersizi

Bugünkü kesit, CPython 3.12.10'un `unittest.mock` modülünden: bir `patch` bağlamının bir özniteliği nasıl kaydedip geri koyduğunu gösteren `_patch` sınıfının parçaları. Kaynak, yerel kurulumdaki `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py` dosyasından birebir alındı; satır numaraları bu dosyaya aittir: `get_original` 1419–1440, `__exit__` 1597–1619. Atlanan bölgeler `# ...` ile işaretlendi; kalan satırlar değiştirilmedi.

```python
    def get_original(self):
        target = self.getter()
        name = self.attribute

        original = DEFAULT
        local = False

        try:
            original = target.__dict__[name]
        except (AttributeError, KeyError):
            original = getattr(target, name, DEFAULT)
        else:
            local = True

        if name in _builtins and isinstance(target, ModuleType):
            self.create = True

        if not self.create and original is DEFAULT:
            raise AttributeError(
                "%s does not have the attribute %r" % (target, name)
            )
        return original, local

    # ... (1441-1596 atlandı)

    def __exit__(self, *exc_info):
        """Undo the patch."""
        if not self.is_started:
            return

        if self.is_local and self.temp_original is not DEFAULT:
            setattr(self.target, self.attribute, self.temp_original)
        else:
            delattr(self.target, self.attribute)
            # ... (1606-1612 atlandı)
        del self.temp_original
        del self.is_local
        del self.target
        exit_stack = self._exit_stack
        del self._exit_stack
        self.is_started = False
        return exit_stack.__exit__(*exc_info)
```

Bu kesit, Bölüm 39.5'te "patch hedefi" uyarısını verdiğimiz mekanizmanın içini gösterir. `_patch` nesnesinin `getter` ve `attribute` alanları, `patch("modul.ad")` yazdığında çözümlenen hedef nesneyi ve değiştirilecek adı tutar.

**Sorular — cevaplamadan geçme:**

- `get_original` önce `target.__dict__[name]` dener, olmazsa `getattr(target, name, DEFAULT)` çağırır. Bir sınıfın metodu bir alt sınıf üzerinden patch edildiğinde `local` neden `False` olur? Bu bilgi `__exit__` içinde hangi işlemi seçtirir?
- `if name in _builtins and isinstance(target, ModuleType): self.create = True` satırı ne zaman devreye girer? Bir modülde tanımlı olmayan `open` gibi bir yerleşik adı neden patch edilebilir, oysa tanımlı olmayan `ad_yok` adı `AttributeError` verir?
- `if not self.create and original is DEFAULT:` koşulu, Bölüm 39.5'teki hatalı hedef adının sonucunu gösterir. Hedefi `siparis.Depo` yerine tanımlandığı yerde (`depo.Depo`) yazarsan bu satır ne zaman tetiklenir, ne zaman sessizce hiçbir şey yapmaz?
- `__exit__` içinde `if self.is_local and self.temp_original is not DEFAULT:` dalı `setattr` ile geri koyar, `else` dalı `delattr` ile siler. Miras alınan (yerel olmayan) bir özniteliği `setattr` ile geri koymak neden yanlış olurdu? Yerel olmayan bir öznitelik için `delattr` neyi geri getirmiş olur?
- `__enter__` içindeki `is_started` kontrolü, aynı patch nesnesi ikinci kez başlatılırsa `RuntimeError` fırlatır. Bu, iç içe iki `with patch(...)` kullanımını nasıl etkiler? Aynı hedefi iki farklı `patch` ile değiştirmek neden durumu bozabilir?
- Bu mekanizma test sırasında kaynak kodu geçici olarak değiştirir. Bölüm 21'deki DIP ile sahte nesne enjeksiyonu aynı problemi çözer ama bağımlılığı değiştirmek için hedef adına değil, bir parametreye bağlanır. Bölüm 39.5'teki `BellekDeposu` (fake) örneğini kullanarak, hangi durumda `patch` yerine enjeksiyonu tercih edersin ve neden?

## Bölüm Özeti

Bu bölümde testin neden yazıldığından başlayıp kanıtın sınırlarına kadar gittik:

- **Test üç işe yarar:** hızlı geri bildirim, regresyon koruması ve tasarım baskısı. Ama hiçbir test hataların yokluğunu kanıtlamaz; yalnızca sınadığı durumları doğrular.
- **Test piramidi:** çok birim testi, daha az entegrasyon, en az uçtan uca. Test kupası bu oranın tersidir ve kırılgandır.
- **İyi birim testi:** AAA yapısı, tek davranış, deterministik, hızlı, bağımsız ve açık adlandırılmış.
- **pytest:** keşif, `assert` yeniden yazımı, fixture kapsamları, `parametrize`, `skip` ve `xfail`, `approx` ile kayan nokta toleransı.
- **Test ikizleri:** fake ve spy ile davranışı, mock ile etkileşimi sına. Dış sınırda mock kullan; iç çağrıları mock'lamak uygulamaya bağlı kırılgan testler üretir.
- **Kapsama:** satır ve dal kapsaması farklı şeyler ölçer; %100 kapsama hatasızlık demek değildir (Örnek 1'deki `ortalama` hatası buna örnektir).
- **Mutasyon testi:** küçük hatalar enjekte edip test setinin onları yakalayıp yakalamadığını ölçer; hayatta kalan her mutant ya bir test boşluğu ya da eşdeğer bir mutanttır.
- **Özellik tabanlı test ve küçültme:** Hypothesis özelliği rastgele girdilerle sınar ve karşı örneği en küçük haline indirir. Diferansiyel test (referans gerçeklemeye karşı) Bölüm 13 ve 16'daki çapraz test disiplininin genelleşmiş hâlidir.
- **TDD:** kırmızı, yeşil, yeniden düzenle; kırmızıyı görmeden yazılan test bir şey kanıtlamaz.
- **Kararsız testler:** zamanlama, sıra bağımlılığı, rastgelelik ve paylaşılan durum. Tekrarlı çalıştırma ile bulunur, tohum, fixture ve izolasyon ile düzeltilir.
- **Savunma sanayiinde test:** iz sürülebilirlik, MC/DC (DO-178C DAL A için) ve donanım-döngüde test (HIL).

**Sonraki bölümde:** Bölüm 40 — API Tasarımı. Testlerin sınadığı şey bir arayüzdür; bu bölümde gördüğümüz bağımlılık enjeksiyonu ve sözleşme düşüncesi, bir arayüzü tasarlarken nasıl kararlar aldığımızı belirleyecek. Bölüm 40'ta bu sözleşmeleri, sürümlemeyi ve hata modellerini ayrıntılı göreceğiz.

::: mulakat
Klasik sorular — hemen cevaplamaya çalışma, her birini birkaç dakika düşün:

1. Bir birim testi ile bir entegrasyon testi arasındaki fark nedir? Hangisini ne zaman yazarsın ve neden?
2. Fake ile mock arasındaki farkı bir örnekle açıklar mısın? Hangi durumda mock kullanmak zararlıdır?
3. %100 dal kapsaması olan bir test paketinin hâlâ hata kaçırabileceğini nasıl gösterirsin?
4. Mutasyon testi, kapsamadan neyi fazladan ölçer? Eşdeğer mutant neden skoru bir üst sınır olmaktan çıkarır?
5. Kararsız bir testi nasıl bulur, nasıl düzeltirsin? Tohumu sabitlemek her zaman doğru çözüm müdür?
6. TDD'de kırmızı adımı atlamak neden tehlikelidir? Bir testin hiç kırmızı olmadan geçtiğini görmek ne anlama gelir?
7. MC/DC ile dal kapsaması arasındaki fark nedir? `(A and B) or C` kararında neden en az n + 1 test gerekir?
8. Bir hatayı düzelttikten sonra regresyon testi yazmak neden tek başına yeterli değildir; testi nasıl doğrularsın?
:::
