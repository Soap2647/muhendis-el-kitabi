%% kisim_no: V
%% kisim_ad: OOP & Yazılım Tasarımı
%% bolum_no: 22
%% baslik: Design Patterns

## Giriş: Aynı çözümü ikinci kez icat etmemek

Bölüm 20'de sınıfları, Bölüm 21'de SOLID ilkelerini gördün. İlkeler sana "ne istediğini" söyler: değişikliğe kapalı, genişlemeye açık olsun; bağımlılık soyutlamaya bağlansın. Ama ilke bir yol göstermez. "Açık olsun" dediğinde bunu hangi yapıyla kuracağını ilke sana söylemez. Kalıplar tam bu boşluğu doldurur: aynı tasarım sorununun, onlarca yıldır tekrar tekrar kurulan çözümlerini adlandırılmış olarak verirler.

Design patterns kavramı 1994'te Gamma, Helm, Johnson ve Vlissides'in kitabıyla yaygınlaştı; bu dört yazar genellikle "Gang of Four" (GoF) diye anılır (genel bilgi). Kitapta 23 kalıp vardır. Bu bölümde onlardan on tanesini ele alıyoruz: Factory, Singleton, Builder, Adapter, Decorator, Facade, Observer, Strategy, Command ve State.

Bu kalıpların mülakatta ve gerçek projede nerede çıktığını söylemek kolay: "Bu sınıfı nasıl bir kez oluştururum ama sonradan yeni türler ekleyebileyim?" sorusu Factory'nin, "Bir eylemi geri almam gerekiyor" sorusu Command'ın, "Bir sensör değiştiğinde ekranın kendiliğinden güncellenmesi" sorusu Observer'ın kapısıdır. Savunma sanayiinde de benzer kalıplar yaygındır: bir İHA'nın uçuş modları bir durum makinesidir, sensör sürücüleri çoğu zaman bir adaptör arkasına saklanır, telemetri zincirleri dekoratörlerle sarılır.

Mert'in projelerinde doğal karşılıklar var. MertOS'un kabuğu (shell) komutlarını bir tabloda, her birinin işleyici fonksiyonuna bir gösterici ile tutar; bu, Command kalıbının çekirdeğidir. EV Dashboard'daki sensör okumaları için yeni bir donanım eklediğinde, eski sürücüyü değiştirmek yerine bir uyarlayıcı yazarsın. Bu bölümde bu iki örneği gerçek kodla geri çağıracağız.

::: not
Bu bölümdeki Python programları Python 3.12.10 ile, C++ programları WSL içinde Ubuntu 24.04 üzerindeki g++ 13.3.0 ile derlendi ve `-std=c++17 -O2 -Wall -Wextra` uyarılarıyla birlikte `-fsanitize=address,undefined` ile de çalıştırıldı. Sanitizer araçları Linux'ta çalışır; bu yüzden C++ kodlarını Windows'ta değil WSL2 içinde derledik. Çıktılar birebir bu kodların çıktılarıdır. Kendi makinende aynı çıktıyı elde etmek için kodu bu bölümdeki haliyle yazman yeterlidir; rastgele sayı yoktur, bu yüzden tohum da gerekmez.
:::

## 22.1 Kalıp nedir, ne değildir

Bir kalıp (pattern) hazır bir kod parçası değildir. Bir tasarım problemi için tekrar eden bir **çözüm biçimidir**; bu biçimin adı, ne zaman kullanılacağı ve bedeli yazılıdır. Bunu bir takas (trade-off) olarak düşün: kalıp sana bir esneklik verir, karşılığında bir dolaylama (indirection) katmanı, daha fazla sınıf ve daha karmaşık bir okuma yükü öder. Bu takas her zaman kârlı değildir.

Kalıbı kod parçası sayan yanlış bir alışkanlık vardır. Bu alışkanlık, kalıp avcılığı (pattern hunting) denen hataya yol açar: her yere bir kalıp sokmak. Örneğin iki sayıyı toplayan bir fonksiyonu Strategy ile sarmak, her şeyi Singleton yapmak ya da her nesneye bir Factory yazmak kodu anlaşılmaz hâle getirir. Bu kalıpların hiçbiri gereksiz yere kullanılmamalıdır. Bir kalıbı ancak sorun gerçekten ortaya çıktığında uygula.

Kalıpları öğrenmenin doğru sırası şudur: önce problemi kalıpsız kötü kodla gör, sonra kalıbın bu kodu nasıl düzelttiğini gör, en son bedelini hesapla. Bu bölümdeki her kalıp bu üç adımı izler. Bir kalıbın adını ezberlemek yetmez; onu hangi kötü koddan çıkardığını hatırlayabilmen gerekir.

Kalıpların birbirleriyle ilişkisini de bil. Bölüm 21'deki ilkeler kalıpların gerekçesidir: OCP, Strategy ve Decorator'ın; DIP, Factory ve Observer'ın arkasındaki düşüncedir. Bu bölümde her kalıbın hangi ilkeyi gerçekleştirdiğini bir cümleyle bağlayacağız; ilkelerin kendisini yeniden anlatmayacağız.

## 22.2 Üç aile ve bir harita

GoF kalıplarını üç aileye ayırdı. Yaratımsal (creational) kalıplar nesnelerin nasıl oluşturulduğuyla ilgilenir. Yapısal (structural) kalıplar sınıf ve nesnelerin nasıl bir araya getirildiğiyle ilgilenir. Davranışsal (behavioral) kalıplar nesnelerin birbirine nasıl mesaj gönderip sorumluluk paylaştığıyla ilgilenir. Aşağıdaki tablo bu bölümdeki on kalıbı bu ailelere ve çözdükleri ağrıya göre yerleştirir.

| Kalıp | Aile | Çözdüğü ağrı |
|---|---|---|
| Factory | Yaratımsal | Hangi sınıfın oluşturulacağı çalışma zamanında belirlenir |
| Builder | Yaratımsal | Çok sayıda isteğe bağlı parametreli nesne kurmak |
| Singleton | Yaratımsal | Tek bir örnek gerektiğini garanti etmek (çoğu zaman şüpheli) |
| Adapter | Yapısal | Uyumsuz iki arayüzü birbirine bağlamak |
| Decorator | Yapısal | Bir nesneye, sınıfı değiştirmeden yeni davranış eklemek |
| Facade | Yapısal | Karmaşık bir alt sisteme sade bir kapı açmak |
| Strategy | Davranışsal | Bir algoritmayı çalışma zamanında değiştirebilmek |
| Observer | Davranışsal | Bir değişimi, onu ilgilendiren birçok nesneye bildirmek |
| Command | Davranışsal | Bir eylemi nesne olarak saklamak; geri al/yinele yapmak |
| State | Davranışsal | Bir nesnenin davranışını iç durumuna göre değiştirmek |

Bu tabloyu bir harita gibi kullan. Yeni bir problemle karşılaştığında önce soruyu ailesine göre sor: "Nesne nasıl kurulacak?", "Parçalar nasıl bağlanacak?", "Davranış nasıl değişecek?" Cevap, aday kalıpları daraltır. Bölüm 22.14'te bu daraltmayı bir karar ağacına dönüştüreceğiz.

## 22.3 Factory: nesne türünü çalışma zamanında seçmek

**Problem.** Bir sensör okuma programı, adı metin olarak gelen sensörleri oluşturmak zorunda olsun. İlk akla gelen kod, bir `if` zinciridir:

```python
def sensor_olustur(tip):
    if tip == "termistor":
        return Termistor()
    elif tip == "nem":
        return Nem()
    # yeni bir tip her geldiğinde buraya yeni bir elif
    raise ValueError(tip)
```

Bu kod ilk bakışta makul görünür, ama bir sorunu vardır. Yeni bir sensör eklemek için bu fonksiyonu değiştirmek zorundasın. Bu, Bölüm 21'deki açık-kapalı ilkesinin (OCP) ihlalidir: davranışı genişletmek için mevcut kodu düzenliyorsun. Üstelik fonksiyon büyüdükçe, her yeni tip hem sınıf kurma mantığını hem de tip adlarının eşleşmesini bilmek zorunda kalır.

**Çözüm.** Factory kalıbı, nesne oluşturma işini bir yere toplar. İstemci hangi somut sınıfın kullanıldığını bilmez; yalnızca bir ad verir ve arayüz (`Sensor`) üzerinden bir nesne alır. Yeni tür eklemek için, kendi sınıfını yazıp fabrikanın tablosuna kaydetmen yeter. Fabrikanın kodu değişmez.

![Şekil 22.1: Fabrika yapısı. İstemci yalnızca fabrikanın adını bilir; fabrika kayıt tablosundan somut sınıfı bulup bir Sensor döndürür.](gorseller/b22_factory_yapi.png)

Şekil 22.1'de üç parça görüyorsun: arayüz (`Sensor`), somut sınıflar (`Termistor`, `Nem`) ve bu ikisini ad üzerinden bağlayan kayıt tablosu. Kayıt tablosu, Python'da bir sözlük, C++'ta bir `std::map` olarak tutulur.

Aşağıdaki Python programı kayıt tablosunu bir dekoratörle doldurur. Dekoratör `@kayit("termistor")` satırıyla sınıfı tabloya ekler. Burada `@` sözdizimi bir Decorator kalıbı değildir; bunun farkını Bölüm 22.7'de açıklayacağız. Aşağıdaki kod ilk yarısıdır:

```python
# fabrika.py: kayit tablosuyla sensor fabrikasi (Bolum 22.3)
_KAYIT = {}


class Sensor:
    def oku(self):
        raise NotImplementedError


def kayit(ad):
    """Sinifi fabrika tablosuna ad ile ekleyen dekorator."""
    def ekle(sinif):
        _KAYIT[ad] = sinif
        return sinif
    return ekle


@kayit("termistor")
class Termistor(Sensor):
    def oku(self):
        return 23.5


@kayit("nem")
class Nem(Sensor):
    def oku(self):
        return 61.0
```

Kodun ikinci yarısı fabrikanın kendisini ve test bölümünü içerir:

```python
def sensor_olustur(ad):
    try:
        sinif = _KAYIT[ad]
    except KeyError:
        raise ValueError("bilinmeyen sensor: " + ad) from None
    return sinif()


if __name__ == "__main__":
    for ad in ["termistor", "nem"]:
        s = sensor_olustur(ad)
        print(ad, type(s).__name__, s.oku())
    try:
        sensor_olustur("basinc")
    except ValueError as e:
        print("hata:", e)
    from pathlib import Path
    print("pathlib:", type(Path("a.txt")).__name__)
```

Bu programı çalıştırdığında şu çıktıyı alırsın:

```term
$ python fabrika.py
termistor Termistor 23.5
nem Nem 61.0
hata: bilinmeyen sensor: basinc
pathlib: WindowsPath
```

Son satır, aynı fikrin standart kütüphanede zaten kullanıldığını gösterir: `Path("a.txt")` çağrısı bir `Path` nesnesi değil, işletim sistemine göre `WindowsPath` ya da `PosixPath` döndürür. Yani `Path` bir fabrika gibi davranır; sınıf seçimini sen değil, kütüphane yapar. Çıktıdaki `WindowsPath` Windows'a özgüdür; Linux'ta `PosixPath` görürsün.

C++'ta aynı fikir, `std::function` ile kurulan bir tablo ve bir şablon yardımcısıyla yazılır. Tablo, değer olarak "bu türden bir nesne üreten fonksiyonu" tutar. Aşağıdaki kodun ilk yarısı arayüzü, somut sınıfları ve tabloyu içerir:

```cpp
// factory.cpp: kayit tablosu ile sensor fabrikasi (C++17, Bolum 22.3)
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>

struct Sensor {
    virtual ~Sensor() = default;
    virtual double oku() const = 0;
};

struct Termistor : Sensor {
    double oku() const override { return 23.5; }
};

struct Nem : Sensor {
    double oku() const override { return 61.0; }
};

using Uretici = std::function<std::unique_ptr<Sensor>()>;

// Tablo bir fonksiyonun yerel statik degiskeninde (Bolum 22.5'te
// bu tercihi sorgulayacagiz).
std::map<std::string, Uretici>& kayit() {
    static std::map<std::string, Uretici> tablo;
    return tablo;
}
```

Şablon tabanlı kaydedici ve fabrika fonksiyonu ikinci yarıda:

```cpp
template <typename T>
struct Kaydedici {
    explicit Kaydedici(const std::string& ad) {
        kayit()[ad] = [] { return std::make_unique<T>(); };
    }
};

std::unique_ptr<Sensor> sensor_olustur(const std::string& ad) {
    auto it = kayit().find(ad);
    if (it == kayit().end())
        throw std::runtime_error("bilinmeyen sensor: " + ad);
    return it->second();
}

static Kaydedici<Termistor> k1("termistor");
static Kaydedici<Nem> k2("nem");

int main() {
    for (const char* ad : {"termistor", "nem"}) {
        auto s = sensor_olustur(ad);
        std::cout << ad << " " << s->oku() << "\n";
    }
    try {
        sensor_olustur("basinc");
    } catch (const std::runtime_error& e) {
        std::cout << "hata: " << e.what() << "\n";
    }
}
```

WSL içinde derleyip çalıştırdığında:

```term
$ g++ -std=c++17 -O2 -Wall -Wextra -fsanitize=address,undefined \
    -o factory factory.cpp
$ ./factory
termistor 23.5
nem 61
hata: bilinmeyen sensor: basinc
```

C++ çıktısında `61` yazar, Python'da `61.0`: iki dilin sayı biçimlendirmesi farklıdır, mantık aynıdır.

**Bedel ve yanlış kullanım.** Factory'nin bedeli dolaylamadır. Hangi sınıfın kullanıldığını artık kodun bir yerinde görmezsin; kayıt tablosunu doldurmak için modül yüklenmiş olmalıdır. Yukarıdaki C++ kodunda `Kaydedici` nesneleri bir çeviri birimi içinde statik olarak tanımlandığı için bu çalışır; ama başka bir çeviri biriminde tanımlanmış bir kaydedici, başlatma sırası (static initialization order) yüzünden henüz kayıt olmamış olabilir. Bu tuzaktan kaçınmak için tabloya bir fonksiyonun içinden erişmek (`kayit()` gibi) gerekir; aynen bu kodda yaptığımız gibi.

Python'da da benzer bir tuzak vardır: kayıt dekoratörü çalıştığı için, sınıfın tanımlandığı modülün içe aktarılmış olması gerekir. Modül hiç içe aktarılmadıysa tablo boş kalır ve `sensor_olustur` hata verir. Bu hatayı gerçek bir projede ilk gördüğünde kayıt tablosunun dolmadığını düşün.

Yanlış kullanımın tipik örneği, tek bir tür için fabrika yazmaktır. Yalnızca bir sensör tipin varsa `Sensor()` çağrısını doğrudan yapman yeterlidir. Fabrika, tür sayısı arttığında ya da tür seçimi çalışma zamanında yapıldığında değer kazanır.

Gerçek dünyada bu kalıbı, `pathlib` dışında da görürsün. Genel bilgi olarak: Java'daki `Calendar.getInstance()` ve birçok ORM'nin sorgu nesnesi üreten yardımcıları aynı fikri kullanır; bu örnekleri bu bölümde doğrulamadık.

## 22.4 Builder: karmaşık nesneyi adım adım kurmak

**Problem.** Bir İHA uçuş ayarı düşün. Hız, irtifa, batarya eşiği, GPS açık mı, kayıt açık mı gibi alanlar vardır; çoğu varsayılan değere sahiptir. Kurucu (constructor) ile yazarsan şöyle bir şey çıkar:

```python
ayar = UcusAyar(12.0, 120.0, 80.0, True, True, False, 5, "tr")
```

Bu satırı okuyan biri, `True` değerlerinin hangi alan olduğunu bilemez. Parametrelerin sırasını hatırlamak zorundasın; bir tanesini yanlış yere koyduğunda derleyici (ya da Python) hata vermez, sadece yanlış değer kurar. Buna **teleskopik kurucu** (telescoping constructor) denir: her yeni isteğe bağlı alan, kurucuya yeni bir parametre ekler ve her kombinasyon için ayrı bir kurucu gerekir.

**Çözüm.** Builder, nesneyi bir **inşaatçı** (builder) nesnesi üzerinden adım adım kurar. Her adım bir alanı adıyla atar; en sonunda `build()` çağrısı nesneyi üretir ve geçerliliğini denetler. Aşağıdaki şekil bu akışı gösteriyor.

![Şekil 22.2: Builder akışı. Her adım inşaatçıyı döndürür; build() son doğrulamayı yapıp nesneyi üretir.](gorseller/b22_builder_akis.png)

Python'da Builder'ın en çok ihtiyaç duyulan kısmı, anahtar kelime argümanlarıyla (keyword arguments) zaten karşılanır. Bu yüzden önce Python'da kalıbın gereksiz olduğu durumu görmek, onun gerçek değerini anlamanı sağlar. Aşağıdaki dosyanın ilk yarısı, dataclass tabanlı çözümü ve doğrulamayı içerir:

```python
# ayar.py: parametre sayisi arttiginda iki yaklasim (Bolum 22.4)
from dataclasses import dataclass


@dataclass(frozen=True)
class UcusAyar:
    hiz: float = 10.0          # m/s
    irtifa: float = 50.0       # m
    batarya: float = 80.0      # yuzde
    gps: bool = True
    kayit: bool = False

    def __post_init__(self):   # dogrulama tek yerde
        if not 0 < self.hiz <= 30:
            raise ValueError("hiz 0..30 m/s olmali")
        if not 0 <= self.batarya <= 100:
            raise ValueError("batarya 0..100 olmali")
```

İkinci yarı inşaatçı sınıfını ve testi içerir:

```python
class AyarInsaatcisi:
    def __init__(self):
        self._deger = {}

    def hiz(self, v):
        self._deger["hiz"] = v
        return self                  # zincir icin kendini dondur

    def irtifa(self, v):
        self._deger["irtifa"] = v
        return self

    def kayit(self, v=True):
        self._deger["kayit"] = v
        return self

    def build(self):
        return UcusAyar(**self._deger)


if __name__ == "__main__":
    a = UcusAyar(hiz=12.0, irtifa=120.0)
    b = AyarInsaatcisi().hiz(12.0).irtifa(120.0).build()
    print("esit:", a == b)
    print(b)
    for hiz in (0, 40):
        try:
            AyarInsaatcisi().hiz(hiz).build()
        except ValueError as e:
            print("reddedildi:", e)
```

Çıktı:

```term
$ python ayar.py
esit: True
UcusAyar(hiz=12.0, irtifa=120.0, batarya=80.0, gps=True, kayit=False)
reddedildi: hiz 0..30 m/s olmali
reddedildi: hiz 0..30 m/s olmali
```

Bu karşılaştırma önemli bir ders veriyor: anahtar kelime argümanları, `UcusAyar(hiz=12.0, irtifa=120.0)` biçiminde, Builder'ın öğretmek istediği okunabilirliği zaten sağlar. Python'da Builder genellikle yalnızca iki durumda anlam kazanır: nesne kurulumu birkaç adımlı ve sıralı bir süreç gerektiriyorsa (ör. önce bağlan, sonra kimlik doğrula, sonra yapılandır) ya da kurulum sırasında ara durumlar tutman gerekiyorsa. Aksi hâlde kalıp, gereksiz bir sınıf katmanıdır.

C++'ta anahtar kelime argümanı yoktur (C++20 ile gelen tasarlanmış başlatıcılar, designated initializers, bu boşluğu kısmen doldurur; genel bilgi). Bu yüzden Builder orada daha değerlidir. Aşağıdaki C++ kodunun ilk yarısı akıcı (fluent) inşaatçıyı yazar:

```cpp
// ayar.cpp: Builder deseni (C++17, Bolum 22.4)
#include <iostream>
#include <stdexcept>

struct UcusAyar {
    double hiz = 10.0, irtifa = 50.0, batarya = 80.0;
    bool gps = true, kayit = false;
};

class AyarInsaatcisi {
public:
    AyarInsaatcisi& hiz(double v) { a_.hiz = v; return *this; }
    AyarInsaatcisi& irtifa(double v) { a_.irtifa = v; return *this; }
    AyarInsaatcisi& kayit(bool v) { a_.kayit = v; return *this; }
```

İkinci yarı doğrulamayı ve testi içerir:

```cpp
    UcusAyar build() const {
        if (!(a_.hiz > 0 && a_.hiz <= 30))
            throw std::invalid_argument("hiz 0..30 m/s olmali");
        if (!(a_.batarya >= 0 && a_.batarya <= 100))
            throw std::invalid_argument("batarya 0..100 olmali");
        return a_;
    }

private:
    UcusAyar a_;
};

int main() {
    UcusAyar a = AyarInsaatcisi().hiz(12).irtifa(120)
                                 .kayit(true).build();
    std::cout << "hiz=" << a.hiz << " irtifa=" << a.irtifa
              << " kayit=" << a.kayit << "\n";
    try {
        AyarInsaatcisi().hiz(40).build();
    } catch (const std::invalid_argument& e) {
        std::cout << "reddedildi: " << e.what() << "\n";
    }
}
```

Çıktı:

```term
$ ./ayar
hiz=12 irtifa=120 kayit=1
reddedildi: hiz 0..30 m/s olmali
```

**Bedel ve yanlış kullanım.** Builder, kopya bir sınıf ağacı ve ekstra kod demektir. Ayrıca `build()` çağrılmadan kısmi nesnenin dışarı sızmasına izin verirsen (örneğin inşaatçıdan `UcusAyar` alanlarını doğrudan okutursan) kalıbın koruması boşa çıkar. Yukarıdaki C++ örneğinde inşaatçı içindeki `a_` alanı özeldir ve geçerli nesne yalnızca `build()` ile çıkar; bunu korumak Builder'ın asıl kazancıdır.

Dikkat etmen gereken bir ayrıntı: doğrulamayı nerede yaptığın. Yukarıdaki iki örnekte doğrulama, nesnenin kendi kurucusunda (Python'da `__post_init__`, C++'ta `build`) yapılıyor. Doğrulama inşaatçıda değil de her setter'da yapılırsa, sıralama değişince davranış değişir: önce hızı sonra irtifayı ayarlamak ile tersini yapmak farklı sonuç doğurabilir. Doğrulamayı tek bir noktada, nesne tamamlandığında yap.

Gerçek dünyada: `dataclasses` modülü ile birlikte gelen alan varsayılanları ve `argparse.ArgumentParser` nesnesinin `add_argument` çağrılarıyla kademeli kurulumu, Builder'ın Python'daki hafif biçimleridir (genel bilgi; bu iki kütüphane için iç yapıyı bu bölümde doğrulamadık).

## 22.5 Singleton: tek örnek ve gizli global durum

**Problem.** Bir uygulamada tek bir yapılandırma nesnesi olsun: hangi modda çalıştığını, hangi portu dinlediğini tutan bir nesne. Her modül bunu doğrudan çağırabilsin istersin. En kolay yol, sınıfa bir "tek örnek ver" metodu eklemektir. Bu, **Singleton** kalıbıdır: bir sınıfın en fazla bir örneği olmasını ve bu örneğe bilinen bir noktadan erişilmesini sağlar.

Singleton'ın çekiciliği kısa vadede büyüktür, ama uzun vadede bir bedeli vardır. Kalıbın sağladığı şey aslında **global değişkendir**: her yerden erişilebilen ve her yeri etkileyebilen bir durum. Global durum iki sorun doğurur. Birincisi, bağımlılık görünmez olur: bir fonksiyonun imzasına bakarak hangi durumu okuyup değiştirdiğini bilemezsin. İkincisi, testler birbirini etkiler: bir test yapılandırmayı değiştirirse sonraki test o değişikliği devralır. Aşağıdaki Python programı bu ikinci sorunu doğrudan gösteriyor.

Python'da bir önemli ayrıntı var. Modüller zaten tek örnektir: bir modül ilk kez içe aktarıldığında Python onu `sys.modules` içinde saklar ve sonraki içe aktarmalar aynı nesneyi döndürür. Dosyanın ilk iki satırı bunu ölçer. Ardından klasik sınıf tabanlı singleton'ı yazıp testlerin neden bozulduğunu gösteriyoruz.

```python
# tekil.py: Python'da tekil nesne ve test sorunu (Bolum 22.5)
import json as a
import json as b

print("modul onbellegi:", a is b)


class Yapilandirma:
    _ornek = None

    @classmethod
    def al(cls):
        if cls._ornek is None:
            cls._ornek = cls()
            cls._ornek.ayarlar = {"mod": "normal"}
        return cls._ornek
```

Testler aşağıda. `test_a` yapılandırmayı değiştirir, `test_b` ise varsayılan değeri bekler. Bu iki test birbirinden bağımsız olmalı, ama değildir:

```python
def test_a():
    Yapilandirma.al().ayarlar["mod"] = "test"


def test_b():
    # bagimsiz olmasi gereken test; test_a ayni nesneyi degistirdi
    assert Yapilandirma.al().ayarlar["mod"] == "normal"


class Kaydedici:
    def __init__(self, depo):          # bagimlilik disaridan gelir
        self.depo = depo

    def kaydet(self, veri):
        self.depo.append(veri)


def test_c():
    sahte = []                         # test icin sahte depo
    Kaydedici(sahte).kaydet(1)
    assert sahte == [1]


if __name__ == "__main__":
    test_a()
    try:
        test_b()
        print("test_b gecti")
    except AssertionError:
        print("test_b basarisiz: gizli durum sizdi")
    test_c()
    print("test_c gecti")
```

Çıktı:

```term
$ python tekil.py
modul onbellegi: True
test_b basarisiz: gizli durum sizdi
test_c gecti
```

`test_b` başarısız oldu, çünkü `test_a` aynı global nesneyi değiştirdi. Hatanın kendisi değil, testler arasındaki gizli bağımlılık sorunu. `test_c` ise bağımlılığı dışarıdan verdiği için her zaman bağımsız çalışır. Bu, bir sonraki bölümde göreceğimiz **bağımlılık enjeksiyonu** (dependency injection) fikridir ve Bölüm 21'deki bağımlılığı soyutlama (DIP) ilkesinin uygulamasıdır.

Şekil 22.3 aynı farkı iki yönlü gösteriyor: solda her modül global nesneye doğrudan bağlı, sağda bağımlılık bir yapıcı parametresi olarak dışarıdan geliyor.

![Şekil 22.3: Gizli global bağımlılık (solda) ve enjeksiyon (sağda). Enjeksiyonda depo testte sahte bir nesneyle değiştirilebilir.](gorseller/b22_singleton_di.png)

C++'ta Singleton'ın standart biçimi, Scott Meyers'ın önerdiği yerel statik değişkenli yöntemdir. Fonksiyonun içindeki `static` nesne ilk çağrıda bir kez kurulur. C++11'den beri, yerel statik nesnenin başlatılmasının iş parçacığı güvenli olması standartta garanti edilir (genel bilgi, dil standardı). Aşağıdaki program bunu sekiz iş parçacığıyla ölçer: her biri bin kez `al()` çağırır ve kurucunun kaç kez çalıştığını sayar.

```cpp
// tekil.cpp: Meyers singleton ve es zamanli erisim (C++11 ve sonrasi)
#include <atomic>
#include <iostream>
#include <thread>
#include <vector>

std::atomic<int> kurulum{0};

class Yapilandirma {
public:
    static Yapilandirma& al() {
        static Yapilandirma tek;       // ilk cagrida bir kez kurulur
        return tek;
    }
    int mod = 0;

private:
    Yapilandirma() { ++kurulum; }
};
```

Programın ikinci yarısı iş parçacıklarını başlatır ve sonuçları yazdırır:

```cpp
int main() {
    std::atomic<const void*> ilk{nullptr};
    std::atomic<bool> tutarli{true};
    std::vector<std::thread> is;
    for (int t = 0; t < 8; ++t) {
        is.emplace_back([&] {
            for (int k = 0; k < 1000; ++k) {
                const void* p = &Yapilandirma::al();
                const void* beklenen = nullptr;
                if (!ilk.compare_exchange_strong(beklenen, p) &&
                    beklenen != p)
                    tutarli = false;
            }
        });
    }
    for (auto& th : is) th.join();
    std::cout << "kurulum sayisi: " << kurulum.load() << "\n";
    std::cout << "ayni ornek: " << (tutarli.load() ? "true" : "false")
              << "\n";
}
```

WSL içinde `-pthread` ile derleyip çalıştırdığında:

```term
$ g++ -std=c++17 -O2 -Wall -Wextra -pthread \
    -fsanitize=address,undefined -o tekil tekil.cpp
$ ./tekil
kurulum sayisi: 1
ayni ornek: true
```

Çıktı, kurucunun tek kez çalıştığını ve sekiz iş parçacığının aynı adresi gördüğünü doğrular. Bu tek bir çalıştırmanın kanıtıdır, bir ispat değildir; ama Meyers singleton'ın bu ölçekte doğru davrandığını gösterir.

**Bedel ve yanlış kullanım.** Singleton'ın asıl sorunu kalıbın kendisinden çok, ne için kullanıldığıdır. Üç yaygın hata vardır. Birincisi, "tek olmalı" ile "global olmalı" aynı şey değildir: bir sensör sürücüsünün tek örneğine ihtiyaç duyman, onu her yerden doğrudan çağırabileceğin anlamına gelmez. İkincisi, singleton'ı test edilebilir yapmak için sıfırlama fonksiyonları yazarsın; bu hem kötü tasarımdır hem de yarış koşulu üretir. Üçüncüsü, singleton'ı yaşam döngüsü belirsiz bir kaynak (ör. bir bağlantı havuzu) için kullanırsın; uygulama kapanırken sırası belirsiz yıkılan global nesneler sorun çıkarır.

Pratik kural şudur: singleton yerine önce bağımlılık enjeksiyonunu dene. Nesneyi `main` içinde bir kez yarat ve bağımlı nesnelere yapıcı parametresi olarak ver. Bu, testte sahte nesne vermeyi kolaylaştırır ve bağımlılığı imzada görünür kılar. Tek örnek gerçekten zorunluysa ve enjeksiyon mümkün değilse, singleton'ı kullan ama durumunu olabildiğince küçük tut.

Gerçek dünyada: Python'daki `sys.modules` mekanizması, modül düzeyinde tekil nesnenin en yaygın biçimidir. C++'ta Meyers singleton'ı birçok kütüphanenin günlükleyicisinde görürsün; bu kütüphanelerin kullanımını bu bölümde doğrulamadık (genel bilgi).

## 22.6 Adapter: uyumsuz arayüzü uyarlamak

**Problem.** EV Dashboard'a yeni bir sıcaklık sensörü bağladığını düşün. Eski sürücü, ham ADC değerini (0 ile 4095 arası bir tamsayı) döndürüyor ve metodu `adc_oku(kanal)` diye adlandırılmış. Uygulamanın geri kalanı ise `celsius()` metodu olan bir `Sicaklik` arayüzü bekliyor. Eski sürücünün kodunu değiştiremezsin (başka bir ekip yazmış ya da bir kütüphaneden geliyor). Her çağrı yerine dönüşüm kodu yazarsan, dönüşüm mantığı her yere dağılır.

**Çözüm.** Adapter, uyumsuz bir nesneyi beklenen arayüze **sarar** ve çevirisini tek bir yerde yapar. İstemci yalnızca hedef arayüzü bilir; adaptör hem hedef arayüzü uygular hem de eski nesneyi içinde tutar. Aşağıdaki Python dosyasında adaptör sınıfı `Uyarlayici`, hedef arayüz `Sicaklik` (bir `Protocol`), uyarlanan sınıf ise `EskiSurucu`'dur.

![Şekil 22.4: Adapter yapısı. Uyarlayıcı, hedef arayüzü uygular ve eski sürücüyü içinde tutar; istemci yalnızca hedefi görür.](gorseller/b22_adapter_yapi.png)

```python
# adaptor.py: eski surucuyu yeni arayuze uyarlamak (Bolum 22.6)
from typing import Protocol


class Sicaklik(Protocol):          # yeni arayuz (hedef)
    def celsius(self) -> float: ...


class EskiSurucu:                  # uyarlanan: ham ADC sayisi
    """Eski API: 12 bit ham deger (0..4095) dondurur."""
    def __init__(self, ham_degerler):
        self._degerler = ham_degerler

    def adc_oku(self, kanal):
        return self._degerler[kanal]


class Uyarlayici:                  # adapter
    """10 mV/derece, 3.3 V referans varsayimi (ornek amacli)."""
    def __init__(self, eski, kanal):
        self._eski = eski
        self._kanal = kanal

    def celsius(self):
        ham = self._eski.adc_oku(self._kanal)
        gerilim = ham / 4095 * 3.3
        return gerilim / 0.010


def olc(sensor: Sicaklik) -> str:
    return "%.1f C" % sensor.celsius()
```

Test bölümü, üç kanalı uyarlayıcıdan geçirir ve Python'un standart kütüphanesindeki bir adaptörü de gösterir:

```python
if __name__ == "__main__":
    eski = EskiSurucu([1024, 2048, 3000])
    for k in range(3):
        print("kanal", k, "->", olc(Uyarlayici(eski, k)))
    import io
    m = io.TextIOWrapper(io.BytesIO("merhaba\n".encode()),
                         encoding="utf-8")
    print("TextIOWrapper:", m.readline().rstrip())
```

Çıktı:

```term
$ python adaptor.py
kanal 0 -> 82.5 C
kanal 1 -> 165.0 C
kanal 2 -> 241.8 C
TextIOWrapper: merhaba
```

Dönüşüm formülü, `10 mV/derece` varsayımına dayanır; bu, LM35 benzeri bir sensörün kabaca tanımıdır ve bir veri sayfasından alınmış değildir. Formülün kendisi değil, mekanizma önemlidir: dönüşüm bir yerde yazılıdır ve sensör değişince yalnızca `Uyarlayici` değişir.

Son satırdaki `io.TextIOWrapper`, aynı fikrin standart kütüphanedeki örneğidir. Bu sınıf ham bayt akışını (`BytesIO`) alır ve metin arayüzü (`readline`) sunar; yani bayt akışını metin akışına uyarlar. Yazı tipi ve satır sonu çevirisini sen değil, bu adaptör yapar.

C++'ta aynı yapı, sanal bir arayüz ve onu uygulayan bir sınıfla kurulur. Uyarlayıcı eski sürücüyü bir referansla tutar, böylece sürücünün ömrünü sahiplenmez:

```cpp
// adaptor.cpp: eski surucuyu yeni arayuze uyarlamak (C++17, 22.6)
#include <iostream>
#include <vector>

struct Sicaklik {                       // hedef arayuz
    virtual ~Sicaklik() = default;
    virtual double celsius() const = 0;
};

struct EskiSurucu {                // uyarlanan: ADC (0..4095)
    std::vector<int> degerler;
    int adc_oku(int kanal) const { return degerler[kanal]; }
};

class Uyarlayici : public Sicaklik {    // adapter
public:
    Uyarlayici(const EskiSurucu& e, int kanal) : e_(e), k_(kanal) {}

    double celsius() const override {
        double gerilim = e_.adc_oku(k_) / 4095.0 * 3.3;
        return gerilim / 0.010;         // 10 mV/derece varsayimi
    }

private:
    const EskiSurucu& e_;
    int k_;
};

void yazdir(const Sicaklik& s) {
    std::cout << s.celsius() << " C\n";
}

int main() {
    EskiSurucu e{{1024, 2048, 3000}};
    for (int k = 0; k < 3; ++k)
        yazdir(Uyarlayici(e, k));
}
```

Çıktı:

```term
$ ./adaptor
82.5201 C
165.04 C
241.758 C
```

C++ çıktısı altı anlamlı basamakla yazılır (`cout`'un varsayılan biçimi), Python ise bir ondalık basamakla. Sayılar aynıdır.

**Bedel ve yanlış kullanım.** Adaptör bir dolaylama katmanıdır ve her çağrı bir fazladan metot çağrısı demektir. Gerçek zamanlı bir döngüde bu önemli olabilir; ama çoğu uygulamada ihmal edilebilir. Asıl risk, adaptörün iş mantığı taşımasıdır. Adaptör yalnızca çeviri yapmalıdır: birim dönüşümü, arayüz uyumu. Filtreleme, eşik kontrolü ya da hata yönetimi gibi davranışlar adaptöre girdiğinde, sınıf hem çeviren hem karar veren bir nesneye dönüşür ve yeniden kullanılabilirliği kaybolur.

Bir başka tuzak, adaptörün gerçek bir uyumsuzluk olmadan kullanılmasıdır. İki arayüz zaten aynıysa ya da tek bir yerde çağrılıyorsa, adaptör yalnızca gürültü ekler. Adaptörü, dış bir bileşenin arayüzünü kendi kodunda sabit tutmak istediğinde kullan.

Python'da `typing.Protocol` ile yapısal tipleme (structural typing) kullanmak mümkündür: `Uyarlayici`, `Sicaklik`'ten miras almadan da `celsius` metoduna sahipse kabul edilir. C++'ta ise uyumluluk kalıtımla açıkça ilan edilir; bu, derleyicinin kontrol etmesini sağlar.

## 22.7 Decorator: davranışı sarmalayarak eklemek

**Problem.** Bir sensör okumasını düşün. Bu okumaya üç şey eklemek isteyebilirsin: sonucu önbelleğe almak (donanımı sık yormamak için), okuma süresini ölçmek ve geçici hatalarda yeniden denemek. Bu üç özelliği sensör sınıfının içine yazarsan sınıf büyür ve her özellik birbirine karışır. Kalıtımla çözmeye çalışırsan, her özellik kombinasyonu için ayrı bir alt sınıf gerekir: önbellekli, önbellekli-yeniden-denemeli, önbellekli-ölçümlü-yeniden-denemeli ve benzeri. Bu kombinasyon patlaması, Bölüm 20'de gördüğün kalıtımın sınırıdır.

**Çözüm.** Decorator, bir nesneyi **aynı arayüzü uygulayan** başka bir nesneyle sarar. Sarıcı, kendi işini yapar ve işi iç nesneye devreder. Sarıcılar zincirlenebilir: her katman tek bir sorumluluk taşır ve sıra değiştirilebilir. Bu, Bölüm 21'deki açık-kapalı ilkesinin (OCP) doğrudan uygulamasıdır: yeni bir özellik için mevcut sınıfları değiştirmek yerine yeni bir sarıcı yazarsın.

Aşağıdaki dosyada `Ham` gerçek donanımı taklit eder: ikinci çağrısı bilerek bir `IOError` fırlatır. `Onbellek`, `Yeniden` ve `Olcum` aynı `Okuyucu` arayüzünü uygular ve bir iç okuyucuyu sarar.

```python
# sarici.py: nesne dekoratorleri ve fonksiyon dekoratorleri (22.7)
import functools


class Okuyucu:
    def oku(self):
        raise NotImplementedError


class Ham(Okuyucu):
    """Donanim taklidi: 2. cagri gecici hata verir."""
    def __init__(self):
        self.cagri = 0

    def oku(self):
        self.cagri += 1
        if self.cagri == 2:
            raise IOError("gecici hata")
        return 20.0 + self.cagri


class Onbellek(Okuyucu):
    def __init__(self, ic):
        self._ic = ic
        self._son = None

    def oku(self):
        if self._son is None:
            self._son = self._ic.oku()
        return self._son


class Yeniden(Okuyucu):
    def __init__(self, ic, deneme=3):
        self._ic = ic
        self._deneme = deneme

    def oku(self):
        for i in range(self._deneme):
            try:
                return self._ic.oku()
            except IOError:
                if i == self._deneme - 1:
                    raise
```

Dosyanın son kısmı, Python'un fonksiyon dekoratörünü ve test bölümünü içerir:

```python
def olcum(f):
    @functools.wraps(f)
    def sarici(*args, **kwargs):
        sarici.cagri += 1
        return f(*args, **kwargs)
    sarici.cagri = 0
    return sarici


@olcum
def topla(a, b):
    """Iki sayiyi toplar."""
    return a + b


if __name__ == "__main__":
    ham = Ham()
    ham.cagri = 1                      # sonraki cagri 2. cagri olur
    print("yeniden:", Yeniden(ham).oku(), "ham cagri:", ham.cagri)
    print("topla:", topla(2, 3), "sayac:", topla.cagri)
    print("ad:", topla.__name__, "| __wrapped__:",
          topla.__wrapped__.__name__)
    f = open(__file__, "rb")
    print("nesne katmani:", type(f).__name__, "->",
          type(f.raw).__name__)
    f.close()
```

Çıktı:

```term
$ python sarici.py
yeniden: 23.0 ham cagri: 3
topla: 5 sayac: 1
ad: topla | __wrapped__: topla
nesne katmani: BufferedReader -> FileIO
```

İlk satır, yeniden deneme sarıcısını sınar. `ham.cagri = 1` ile sayaç bir yerde başlatılır; bu yüzden `Yeniden`'in ilk çağrısı ikinci donanım çağrısına denk gelir ve `IOError` alır. Sarıcı bir kez daha dener, üçüncü çağrı başarılı olur ve sonuç `23.0`, toplam donanım çağrısı `3` olur.

Çıktının ikinci kısmı Python'da iki dekoratörün ayrımını gösterir. `@olcum` bir **fonksiyonu** alıp yeni bir fonksiyon döndürür; bu, GoF anlamında bir Decorator değil, fonksiyon-düzeyinde bir sarmalayıcıdır. `functools.wraps` olmadan `topla.__name__` değeri `"sarici"` olurdu; onu olması gereken `"topla"` yapan ve orijinali `__wrapped__` ile saklayan satırdır. Bu kontrolü bu bölüm için ayrıca çalıştırdık: `wraps` varsa `a`, yoksa `sarici` çıktı.

Son satır ise GoF anlamındaki nesne dekoratörünün standart kütüphanedeki bir örneğidir: `open(..., "rb")` çağrısı bir `BufferedReader` döndürür ve bu nesne bir `FileIO`'yu içinde tutar. Tamponlama, dosyayı okuyan nesnenin aynı arayüzünü koruyarak eklenmiş bir davranıştır.

Şekil 22.5 zincirin yapısını gösteriyor: istemci en dış katmanı çağırır, her katman bir alt katmana devreder ve değer geri döner.

![Şekil 22.5: Dekoratör zinciri. Her katman oku() arayüzünü uygular ve bir alt katmana sarar; değer dıştan içe çağrılıp içten dışa döner.](gorseller/b22_decorator_zincir.png)

C++'ta aynı zincir, sahiplik için `unique_ptr` kullanılarak kurulur. Her sarıcı kendi iç nesnesini sahiplenir, bu yüzden zincir yıkıldığında bütün katmanlar da düzgünce yıkılır. Aşağıdaki kodun ilk yarısı arayüzü, donanımı ve önbellek sarıcısını içerir:

```cpp
// sarici.cpp: nesne dekoratorleri zinciri (C++17, Bolum 22.7)
#include <iostream>
#include <memory>
#include <stdexcept>

struct Okuyucu {
    virtual ~Okuyucu() = default;
    virtual double oku() = 0;
};

struct Ham : Okuyucu {
    int cagri = 0;
    double oku() override {
        ++cagri;
        if (cagri == 2) throw std::runtime_error("gecici hata");
        return 20.0 + cagri;
    }
};

struct Onbellek : Okuyucu {
    std::unique_ptr<Okuyucu> ic;
    bool var = false;
    double son = 0.0;
    explicit Onbellek(std::unique_ptr<Okuyucu> i)
        : ic(std::move(i)) {}
    double oku() override {
        if (!var) { son = ic->oku(); var = true; }
        return son;
    }
};
```

İkinci yarı yeniden deneme sarıcısını ve testi içerir:

```cpp
struct Yeniden : Okuyucu {
    std::unique_ptr<Okuyucu> ic;
    int deneme;
    Yeniden(std::unique_ptr<Okuyucu> i, int d)
        : ic(std::move(i)), deneme(d) {}
    double oku() override {
        for (int i = 0;; ++i) {
            try {
                return ic->oku();
            } catch (const std::runtime_error&) {
                if (i == deneme - 1) throw;
            }
        }
    }
};

int main() {
    auto ham = std::make_unique<Ham>();
    Ham* h = ham.get();                 // sayaci okumak icin
    Yeniden y(std::move(ham), 3);
    std::cout << "1. yeniden: " << y.oku()
              << " ham cagri: " << h->cagri << "\n";
    std::cout << "2. yeniden: " << y.oku()
              << " ham cagri: " << h->cagri << "\n";

    Onbellek z(std::make_unique<Yeniden>(std::make_unique<Ham>(), 3));
    std::cout << "onbellek: " << z.oku() << " " << z.oku() << "\n";
}
```

Çıktı:

```term
$ ./sarici
1. yeniden: 21 ham cagri: 1
2. yeniden: 23 ham cagri: 3
onbellek: 21 21
```

İlk satırda ham donanım yalnızca bir kez çağrılır ve değer `21` çıkar. İkinci çağrıda donanım hata verir, yeniden deneme sarıcısı ikinci bir deneme yapar ve `23` döner. Son satır önbelleği gösterir: iki çağrı da `21` döndürür, çünkü ikincisi iç zinciri hiç çağırmaz. C++ sürümünde sayaç yerine değeri yazdırdık; önbelleğin iç çağrıyı atladığını görmek için Python sürümündeki `ham.cagri` kontrolüne bak.

**Bedel ve yanlış kullanım.** Decorator'ın bedeli, zincirin ayrıntısını izlemeyi zorlaştırmasıdır. Bir hata ayıklama oturumunda çağrının hangi katmanlardan geçtiğini görmek için her katmanı tek tek incelemen gerekir. Ayrıca sıralama önemlidir: önbelleği yeniden denemenin içine koyarsan, hatalı bir okuma önbelleğe girmez; dışına koyarsan, hatalı bir sonuç da önbelleğe girebilir. Yukarıdaki şekilde önbellek en dışta olduğu için tekrarlanan çağrılar ne ölçülür ne yeniden denenir.

Yanlış kullanım, sarıcı yerine kalıtım kullanmaktır. Bir sınıfa tek bir ek özellik eklemek için alt sınıf yazarsan, özellikler arttıkça kombinasyon patlaması geri döner. Decorator, özelliklerin bağımsız ve bileşebilir olduğu durumda değer üretir.

Gerçek dünyada: `io` katmanları, `functools.lru_cache` ile sarılmış fonksiyonlar ve `gzip` gibi modüller bu fikri kullanır. `wraps`'in `__wrapped__` özniteliğini ayarladığı yer CPython 3.12.10 kaynağında `Lib/functools.py` dosyasının 61. satırıdır (`wrapper.__wrapped__ = wrapped`); bunu kaynaktan doğruladık. Yalnızca `io` ve `wraps` davranışlarını bu bölümde çalıştırarak gösterdik; `gzip` içindeki ayrıntıyı doğrulamadık.

## 22.8 Facade: karmaşık alt sisteme tek kapı

**Problem.** Bir telemetri paketini göndermek için birkaç adım gerekir: metni ayrıştırmak, değerini doğrulamak, sıkıştırmak ve ağa yollamak. Bu adımları bilen her istemci, her adımın sırasını ve ayrıntısını kendi kodunda tekrar eder. Bir gün sıkıştırma kütüphanesini değiştirdiğinde, kodu kullanan her yeri düzeltmen gerekir.

**Çözüm.** Facade, karmaşık bir alt sistemin önüne **sade bir arayüz** koyar. İstemci yalnızca fasadın metodunu çağırır; alt sistemlerin sırasını ve ayrıntılarını fasad bilir. Facade alt sistemi gizlemez, yalnızca kolaylaştırır: istersen alt sistemlere doğrudan da inebilirsin. Bu, Bölüm 21'deki arayüz ayrıştırma ilkesiyle (ISP) yakından ilgilidir: istemciye yalnızca ihtiyacı olan yüzeyi göstermek.

![Şekil 22.6: Facade yapısı. İstemci tek bir kapıyı çağırır; fasad dört alt sistemi sırayla kullanır.](gorseller/b22_facade_yapi.png)

Aşağıdaki Python dosyasında dört alt sistem var: ayrıştırıcı, doğrulayıcı, sıkıştırıcı ve (burada gösterilmeyen) bir gönderici. Sıkıştırma için Python'un standart `zlib` modülünü kullanıyoruz; gerçek bir ağ bağlantısı yerine fasad sıkıştırılmış baytları döndürür.

```python
# fasad.py: karmasik alt sistemin sade on yuzu (Bolum 22.8)
import zlib


class Ayristirici:
    def coz(self, metin):
        alanlar = metin.split(";")
        return {"id": alanlar[0], "deger": float(alanlar[1])}


class Dogrulayici:
    def gecerli_mi(self, paket):
        return 0 <= paket["deger"] <= 150


class Sikistirici:
    def paketle(self, metin):
        return zlib.compress(metin.encode("utf-8"))


class TelemetriFasad:
    """Istemci yalnizca gonder() cagirir; alt sistemleri bilmez."""
    def __init__(self):
        self._ayristir = Ayristirici()
        self._dogrula = Dogrulayici()
        self._sikistir = Sikistirici()

    def gonder(self, metin):
        paket = self._ayristir.coz(metin)
        if not self._dogrula.gecerli_mi(paket):
            return None
        return self._sikistir.paketle(metin)


if __name__ == "__main__":
    f = TelemetriFasad()
    g = f.gonder("ARAC7;23.5")
    print("sikistirilmis bayt:", len(g))
    print("geri acildi:", zlib.decompress(g).decode())
    print("gecersiz:", f.gonder("ARAC7;999"))
```

Çıktı:

```term
$ python fasad.py
sikistirilmis bayt: 18
geri acildi: ARAC7;23.5
gecersiz: None
```

İstemci tek satırda sıkıştırılmış paketi alır, geçersiz bir değer için `None` görür. Fasadın gövdesinde sıra açıkça yazılıdır: önce ayrıştır, sonra doğrula, en son sıkıştır. Bu sıra, istemcinin kodunda değil, tek bir yerde durur.

C++ sürümü aynı yapıyı, alt sınıfların değer türü olarak tutulduğu bir fasadla kurar. Aşağıdaki kod ayrıştırıcı, doğrulayıcı ve göndericiyi içerir:

```cpp
// fasad.cpp: karmasik altsistemin sade on yuzu (C++17, Bolum 22.8)
#include <iostream>
#include <string>

struct Ayristirici {
    double coz(const std::string& m) const {
        return std::stod(m.substr(m.find(';') + 1));
    }
};

struct Dogrulayici {
    bool gecerli(double d) const { return d >= 0 && d <= 150; }
};

struct Gonderici {
    void yolla(const std::string& p) const {
        std::cout << "yollandi: " << p << "\n";
    }
};
```

Fasadın kendisi ve testi aşağıda. Fasad, üç alt sistemi üye olarak tutar ve sıralamayı yalnızca `gonder` içinde yapar:

```cpp
class TelemetriFasad {
public:
    void gonder(const std::string& metin) const {
        double d = ayr_.coz(metin);
        if (!dog_.gecerli(d)) {
            std::cout << "reddedildi\n";
            return;
        }
        gon_.yolla(metin);
    }

private:
    Ayristirici ayr_;
    Dogrulayici dog_;
    Gonderici gon_;
};

int main() {
    TelemetriFasad f;
    f.gonder("ARAC7;23.5");
    f.gonder("ARAC7;999");
}
```

Çıktı:

```term
$ ./fasad
yollandi: ARAC7;23.5
reddedildi
```

**Bedel ve yanlış kullanım.** Facade'ın tipik hatası, her şeyi tek bir sınıfa doldurmaktır. Fasad zamanla alt sistemlerin bütün özelliklerini yeniden sunmaya başlar ve kendisi bir tanrı nesnesine (god object) dönüşür. Fasadı küçük tut: yalnızca istemcilerin sık yaptığı işlemleri sun. Nadir ihtiyaçlar için alt sisteme doğrudan erişim açık kalsın.

Bir başka tuzak, fasadın hata yönetimini gizlemesidir. Yukarıdaki C++ kodunda geçersiz değer `reddedildi` yazısıyla sessizce geçilir; gerçek bir sistemde bu bir istisna (exception) ya da durum kodu olmalıdır, çünkü çağıran taraf neyin ters gittiğini bilmek ister.

Gerçek dünyada: Python'daki `subprocess.run`, işlem başlatma ve iletişimi yöneten daha düşük seviyeli `Popen` sınıfının üzerine kurulmuş bir fasaddır. CPython 3.12.10 kaynağında `Lib/subprocess.py` dosyasının 548. satırı `with Popen(*popenargs, **kwargs) as process:` ifadesini çağırır; bunu kaynaktan doğruladık.

## 22.9 Strategy: algoritmayı değiştirilebilir yapmak

**Problem.** Sensör verisini düzeltmek için bir kayan pencere filtresi uyguladığını düşün. Bazen pencerenin ortalamasını, bazen medyanını, bazen de üstel ağırlıklı bir ortalamayı kullanmak isteyebilirsin. Her biri için ayrı bir fonksiyon yazarsan, filtreleme döngüsünü de üç kez yazmak zorunda kalırsın. Bir `if algoritma == "medyan"` zinciri koyarsan, yeni bir algoritma eklediğinde döngüyü tekrar açarsın.

**Çözüm.** Strategy, bir algoritmayı **ayrı bir nesne ya da fonksiyon** olarak tanımlar ve onu bağlama (context) nesnesine dışarıdan verir. Bağlam, hangi algoritmanın kullanıldığını bilmez; yalnızca arayüzü çağırır. Bu, Bölüm 21'deki açık-kapalı ilkesinin bir başka uygulamasıdır: yeni algoritma eklemek için bağlam sınıfını değiştirmezsin.

![Şekil 22.7: Strategy yapısı. Filtreleyici bir strateji arayüzü kullanır; somut algoritmalar bu arayüzü uygular ve çalışma zamanında seçilir.](gorseller/b22_strategy_yapi.png)

Python'da bir strateji çoğu zaman bir fonksiyondur. Aşağıdaki dosyada üç strateji bir fonksiyon olarak yazılmıştır ve `Filtreleyici` bağlamı bunları değiştirilebilir biçimde kullanır. Veri, üçüncü ölçümün bozuk (90) olduğu küçük bir dizidir.

```python
# strateji.py: degistirilebilir filtre algoritmalari (Bolum 22.9)
import statistics


def ortalama(pencere):
    return sum(pencere) / len(pencere)


def medyan(pencere):
    return statistics.median(pencere)


def ustel(pencere, alfa=0.5):
    s = pencere[0]
    for x in pencere[1:]:
        s = alfa * x + (1 - alfa) * s
    return s


class Filtreleyici:                    # baglam (context)
    def __init__(self, strateji):
        self.strateji = strateji       # calisma zamaninda secilir

    def uygula(self, veri, n):
        return [self.strateji(veri[i:i + n])
                for i in range(len(veri) - n + 1)]
```

Test bölümü aynı veriyi üç stratejiyle çalıştırır ve bir de `sorted` fonksiyonunun `key` parametresini gösterir:

```python
if __name__ == "__main__":
    veri = [20, 21, 90, 22, 21, 23, 22]   # 90: bozuk olcum
    for ad, s in [("ortalama", ortalama), ("medyan", medyan),
                  ("ustel", ustel)]:
        sonuc = Filtreleyici(s).uygula(veri, 3)
        print("%-9s" % ad, [round(x, 2) for x in sonuc])
    print("key ile sirala:", sorted(["bb", "a", "ccc"], key=len))
```

Çıktı:

```term
$ python strateji.py
ortalama  [43.67, 44.33, 44.33, 22.0, 22.0]
medyan    [21, 22, 22, 22, 22]
ustel     [55.25, 38.75, 38.5, 22.25, 22.0]
key ile sirala: ['a', 'bb', 'ccc']
```

Sonuçlara bak: ortalama, bozuk ölçümü ilk üç pencerede dağıtıyor ve sonuç `43.67` gibi bir değere çıkıyor. Medyan ise bozuk değeri tamamen eliyor ve pencere sonuçlarını `22` civarında tutuyor. Üstel ağırlıklı ortalama, yeni değere daha çok ağırlık verdiği için ara kalır. Hangi stratejinin doğru olduğu sensörün gürültüsüne bağlıdır; bu yüzden strateji seçimini çalışma zamanında yapabilmek değerlidir.

Son satırdaki `sorted(..., key=len)` aynı fikrin dilin kendi içindeki örneğidir: sıralama algoritması sabit kalır, karşılaştırma ölçütü dışarıdan verilir. Bölüm 13'te gördüğün sıralama karşılaştırıcısı tam olarak bir stratejidir.

C++'ta strateji iki biçimde verilebilir. Derleme zamanında (şablon parametresiyle) ya da çalışma zamanında (`std::function` ile). Aşağıdaki kod ikinci yolu kullanır ve `std::sort`'un karşılaştırıcısını da strateji olarak gösterir:

```cpp
// strateji.cpp: derleme zamani ve calisma zamani stratejisi (22.9)
#include <algorithm>
#include <cstddef>
#include <functional>
#include <iostream>
#include <numeric>
#include <vector>

using Pencere = std::vector<double>;
using Strateji = std::function<double(const Pencere&)>;

double ortalama(const Pencere& w) {
    return std::accumulate(w.begin(), w.end(), 0.0) / w.size();
}

double medyan(Pencere w) {               // kopya: siralanacak
    std::sort(w.begin(), w.end());
    return w[w.size() / 2];              // tek uzunlukta pencere
}

Pencere uygula(const Strateji& s, const Pencere& v, std::size_t n) {
    Pencere out;
    for (std::size_t i = 0; i + n <= v.size(); ++i)
        out.push_back(s(Pencere(v.begin() + i, v.begin() + i + n)));
    return out;
}

void yazdir(const char* ad, const Pencere& p) {
    std::cout << ad << " ";
    for (double x : p) std::cout << x << " ";
    std::cout << "\n";
}

int main() {
    Pencere veri{20, 21, 90, 22, 21, 23, 22};   // 90: bozuk olcum
    yazdir("ortalama", uygula(ortalama, veri, 3));
    yazdir("medyan  ", uygula(medyan, veri, 3));

    std::vector<int> sayilar{3, 1, 4, 1, 5};
    std::sort(sayilar.begin(), sayilar.end(), std::greater<int>());
    for (int x : sayilar) std::cout << x << " ";
    std::cout << "\n";
}
```

Çıktı:

```term
$ ./strateji
ortalama 43.6667 44.3333 44.3333 22 22 
medyan   21 22 22 22 22 
5 4 3 1 1 
```

Çıktının sonundaki boşluklar `yazdir` fonksiyonunun her değerden sonra boşluk yazmasından gelir. Son satır, `std::greater<int>()` karşılaştırıcısıyla azalan sıralamayı gösterir.

**Bedel ve yanlış kullanım.** Strateji, her algoritma için bir nesne ya da fonksiyon gerektirir ve bu, küçük algoritmalar için gereksiz dolaylama olabilir. Yalnızca bir algoritman varsa ve değişmeyeceğini biliyorsan, bağlama doğrudan yaz. Ayrıca stratejiler arasındaki ortak ayrıntılar (ör. pencere boyutu kontrolü) her stratejiye kopyalanmamalı; bağlamda kalmalıdır.

Yaygın bir hata, stratejinin bağlamın iç durumunu değiştirmesidir. Strateji yalnızca girdisine bakıp sonucunu döndürmelidir; yan etkisi olan bir strateji, sonucu sırayla çağrılmaya bağlı kılar ve test edilmesini zorlaştırır.

Gerçek dünyada: Python'da `sorted`, `list.sort` ve `heapq` gibi araçlar `key` parametresi alır; bu, her birinin bir Strategy olarak tasarlandığı anlamına gelir. C++'ta `std::sort` karşılaştırıcısı ve STL'deki ayırıcılar (allocator) aynı fikrin derleme zamanı biçimidir (genel bilgi).

## 22.10 Observer: değişimi abonelere bildirmek

**Problem.** Bir sıcaklık ölçümü geldiğinde birkaç şeyin olması gerekebilir: ekranın güncellenmesi, bir alarmın çalması, verinin kaydedilmesi. Ölçümü alan kod her birini tek tek çağırırsa, yeni bir ilgilenen eklemek için ölçüm kodunu değiştirmen gerekir. Ölçüm bileşeni, kimin dinlediğini bilmek zorunda kalır; bu, bağımlılığı tersine çevirmenin (DIP) tam tersidir.

**Çözüm.** Observer'da bir **konu** (subject), kendi durumu değiştiğinde ya da bir olay gerçekleştiğinde, kayıtlı **gözlemcilere** (observers) haber verir. Konu gözlemcilerin somut türünü bilmez; yalnızca bir arayüz çağırır. Gözlemciler kendilerini aboneliğe ekler ve çıkarlar.

Bu kalıbın iki gerçek tuzağı vardır ve kodda bunları ayrıca göreceğiz. Birincisi **bellek sızıntısı**: konu gözlemciye güçlü bir referansla bağlıysa, gözlemci artık gerekmese bile bellekte kalır. İkincisi **yeniden giriş** (reentrancy): bir gözlemci bildirim sürerken aboneliği değiştirirse, gezilen liste bozulabilir. Aşağıdaki dosya ikisini de gösteriyor.

![Şekil 22.8: Observer akışı. Konu, kopya üzerinden gözlemcilere bildirim yapar; gözlemcilere zayıf referansla bağlıdır, öldüklerinde listeden temizlenirler.](gorseller/b22_observer_akis.png)

Aşağıdaki dosyada `Konu` gözlemcileri `weakref.WeakMethod` ile tutar. Bu sayede konu gözlemcinin yaşamını uzatmaz. Bildirim sırasında liste üzerinde değil, bir kopya üzerinde gezilir.

```python
# gozlemci.py: yayinci/abone, zayif referans, yeniden giris (22.10)
import weakref


class Alarm:
    def __init__(self, ad, esik):
        self.ad = ad
        self.esik = esik
        self.kayitlar = []

    def olay(self, deger):
        self.kayitlar.append(deger)
        if deger > self.esik:
            print("  ALARM", self.ad, deger)


class Konu:
    def __init__(self):
        self._gozlemciler = []                # zayif referanslar

    def abone_ol(self, fonk):
        self._gozlemciler.append(weakref.WeakMethod(fonk))

    def cik(self, fonk):
        hedef = weakref.WeakMethod(fonk)
        self._gozlemciler[:] = [r for r in self._gozlemciler
                                if r != hedef]   # yerinde degisir

    def bildir(self, deger):
        for ref in list(self._gozlemciler):   # kopya uzerinde gez
            fonk = ref()
            if fonk is None:
                self._gozlemciler.remove(ref)  # olu referansi temizle
            else:
                fonk(deger)
```

`cik` metodunun listeyi yerinde değiştirdiğine dikkat et: `self._gozlemciler[:] = ...`. Bu ayrıntı, aşağıdaki hatayı gerçekten ortaya çıkarmak için gereklidir. Liste `self._gozlemciler = ...` ile yeniden atanmış olsaydı, döngü eski listeyi gezmeye devam eder ve hata görünmezdi.

Hatalı sürüm, bildirimi bir kopya yerine doğrudan liste üzerinde gezer. Bunun dışında her şey aynıdır:

```python
class NaifKonu(Konu):
    """HATALI surum: liste gezilirken degisebilir."""
    def bildir(self, deger):
        for ref in self._gozlemciler:
            fonk = ref()
            if fonk is not None:
                fonk(deger)


class Tek:
    """Ilk olayda kendini abonelikten cikaran gozlemci."""
    def __init__(self, konu, ad):
        self.konu = konu
        self.ad = ad

    def olay(self, deger):
        print("  %s aldi: %s" % (self.ad, deger))
        self.konu.cik(self.olay)
```

`Tek` sınıfı, ilk olayda kendini abonelikten çıkaran bir gözlemcidir. Bu, yeniden girişi tetiklemek için bilerek yazılmış bir durumdur: gözlemci, bildirim sürerken listeyi değiştirir.

```python
def tekrar(sinif):
    k = sinif()
    t = Tek(k, "A")
    b = Alarm("B", 0)
    k.abone_ol(t.olay)
    k.abone_ol(b.olay)
    k.bildir(1)
    print(sinif.__name__, "-> B kayitlari:", b.kayitlar)


if __name__ == "__main__":
    tekrar(NaifKonu)
    tekrar(Konu)
    k = Konu()
    kritik = Alarm("kritik", 80)
    k.abone_ol(kritik.olay)
    gecici = Alarm("gecici", 0)
    k.abone_ol(gecici.olay)
    k.bildir(10)
    del gecici                      # Konu onu tutmaz
    k.bildir(85)
    print("abone sayisi:", len(k._gozlemciler))
```

Çıktı:

```term
$ python gozlemci.py
  A aldi: 1
NaifKonu -> B kayitlari: []
  A aldi: 1
  ALARM B 1
Konu -> B kayitlari: [1]
  ALARM gecici 10
  ALARM kritik 85
abone sayisi: 1
```

İlk iki satır hatayı gösteriyor. `NaifKonu` bildirim sırasında `A`'yı çağırır; `A` kendini çıkarınca liste küçülür, döngü bir sonraki indekse geçer ve `B`'yi atlar. Sonuçta `B` hiç bildirim almaz: `kayitlar` boş kalır. `Konu` ise kopya üzerinde gezdiği için `B` bildirimi alır ve `[1]` görünür.

Üçüncü ve dördüncü satırlar zayıf referansın etkisini gösterir. `gecici` gözlemcisi `del` ile silindikten sonra da kısa süre `Konu` içinde yer alabilir, ama bir sonraki bildirimde ölü referans olarak fark edilir ve listeden çıkarılır. Son satırdaki `abone sayisi: 1` bunu doğrular: yalnızca `kritik` kalmıştır. `del gecici` olmasaydı, `gecici` nesnesi bellekte kalırdı ve bildirimleri almaya devam ederdi.

Bu tuzak Python'a özgü değildir. Benzer bir koruma, C++'ta `std::weak_ptr` ile sağlanır. Aşağıdaki C++ kodu bildirim sırasında kopya üzerinde gezer; her gözlemci bir `weak_ptr` olarak tutulur ve sadece hayattaysa çağrılır.

```cpp
// gozlemci.cpp: zayif referansli abonelik, weak_ptr (C++17, 22.10)
#include <algorithm>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

struct Gozlemci {
    virtual ~Gozlemci() = default;
    virtual void olay(double deger) = 0;
};

class Konu {
public:
    void abone_ol(const std::shared_ptr<Gozlemci>& g) {
        liste_.push_back(g);                 // weak_ptr'a donusur
    }

    void bildir(double deger) {
        auto kopya = liste_;   // bildirim sirasinda degisebilir
        for (auto& w : kopya)
            if (auto g = w.lock()) g->olay(deger);
        liste_.erase(std::remove_if(liste_.begin(), liste_.end(),
            [](const std::weak_ptr<Gozlemci>& w) {
                return w.expired();
            }), liste_.end());
    }

    std::size_t sayi() const { return liste_.size(); }

private:
    std::vector<std::weak_ptr<Gozlemci>> liste_;
};
```

C++ sürümünde `w.lock()` ile gözlemci hayattaysa bir `shared_ptr` alınır ve çağrılır; değilse `lock` boş döner ve atlanır. Ölü girişler, bildirimden sonra `remove_if` ile listeden silinir.

Gözlemci sınıfı ve ana program aşağıda. Gözlemcilerden biri, nesnenin ömrünü kapsayan bir blokta yaratılır ve blok bittiğinde yok olur:

```cpp
class Alarm : public Gozlemci {
public:
    Alarm(std::string ad, double esik) : ad_(ad), esik_(esik) {}
    void olay(double d) override {
        if (d > esik_)
            std::cout << "  ALARM " << ad_ << " " << d << "\n";
    }

private:
    std::string ad_;
    double esik_;
};

int main() {
    Konu k;
    auto kritik = std::make_shared<Alarm>("kritik", 80);
    k.abone_ol(kritik);
    {
        auto gecici = std::make_shared<Alarm>("gecici", 0);
        k.abone_ol(gecici);
        k.bildir(10);                        // gecici alarm verir
    }                                        // gecici burada yok olur
    std::cout << "abone sayisi: " << k.sayi() << "\n";
    k.bildir(85);                            // olu abone temizlenir
    std::cout << "abone sayisi: " << k.sayi() << "\n";
}
```

Çıktı:

```term
$ ./gozlemci
  ALARM gecici 10
abone sayisi: 2
  ALARM kritik 85
abone sayisi: 1
```

Blok bitmeden önce `abone sayisi` değeri 2'dir, çünkü temizlik henüz yapılmadı. Blok bittikten sonra `gecici` yok olur, ama listede hâlâ ölü bir `weak_ptr` vardır. Bir sonraki bildirimde bu giriş silinir ve sayı 1 olur. Bu, Python'daki davranışın birebir aynısıdır: temizlik tembeldir, bildirim sırasında yapılır.

**Bedel ve yanlış kullanım.** Observer'ın bedeli, olay akışının izlenmesinin zorlaşmasıdır. Bir olay birden çok gözlemciyi tetikler ve bu gözlemciler birbirinden habersizdir; bir değişikliğin sonucunu tahmin etmek için hepsini okuman gerekir. Ayrıca sıra belirsizdir: bu örneklerde gözlemciler eklenme sırasıyla çağrıldı, ama bu bir garanti değildir ve sıraya bağlı bir mantık kurmak kırılgandır.

Yaygın hatalar üçtür. Birincisi, bildirim sırasında bir gözlemcinin başka bir olayı tetiklemesi ve sonsuz bir döngü oluşması; ikincisi, gözlemci içinde ağır bir işlem yapıp konuyu bloke etmesi; üçüncüsü, gözlemcilerin çıkarılmayı unutması ve bellek sızıntısı. Kopya üzerinde gezmek ilkini, zayıf referans ikincisini ve üçüncüsünü azaltır; ama bildirimleri hafif tutmak senin sorumluluğundur.

Gerçek dünyada: Qt kütüphanesindeki sinyal ve yuva (signal/slot) mekanizması Observer'ın çok bilinen bir uygulamasıdır (genel bilgi; bu bölümde Qt kodunu doğrulamadık). CPython'un `logging` modülünde bir kayıt, bir günlükleyiciden çıkıp işleyicilere (handler) iletilir; bu, Observer ve Zincir (Chain of Responsibility) fikirlerinin birlikte kullanımıdır. Ayrıntılı kaynak incelemesini Bölüm 22'nin Kod Okuma egzersizinde yapacağız.

## 22.11 Command: eylemi nesneye çevirmek

**Problem.** Bir metin düzenleyicide `Ctrl+Z` ile son işlemi geri almak istediğini düşün. Düzenleyici, "metne şunu ekle", "şu aralığı sil", "şu biçimi uygula" gibi bir dizi işlem yapar. Geri almak için her işlemin tersini bilmen gerekir. İlk akla gelen çözüm, her tür işlemi tanıyan bir `if` zinciridir; ama yeni bir işlem türü eklediğinde hem işlemi çalıştıran kodu hem de geri alma kodunu değiştirmen gerekir. Bu, işlem bilgisini dağıtır.

**Çözüm.** Command, bir eylemi bir **nesne** olarak paketler. Nesne üç şey bilir: eylemi nasıl çalıştıracağını, eylemi nasıl geri alacağını ve (gerekirse) hangi veriye ihtiyaç duyduğunu. Düzenleyici artık yalnızca komut nesnelerini bir yığına koyar ve tepedekini çeker. Bu yığın, Bölüm 8'deki yığın (stack) veri yapısının doğrudan bir uygulamasıdır: geri alma son giren ilk çıkar mantığıyla çalışır.

![Şekil 22.9: Geri al ve yinele yığınları. Geri al, komutu geri alma yığınından çekip ileri yığınına iter; yinele tersini yapar.](gorseller/b22_command_yigin.png)

### MertOS'taki komut tablosu

Mert'in MertOS işletim sistemindeki kabuk (shell), komutlarını bir Command yapısıyla tutar. Bu, Command kalıbının çekirdek fikridir, ama tam GoF biçimi değildir: MertOS'taki yapıda geri alma yoktur, komutlar nesne olarak saklanmaz, yalnızca bir tabloda ve bir işleyici göstericisiyle temsil edilir. Kaynak dosyada yapı şöyle tanımlanmıştır (`kernel/shell/shell.hpp`, 39-44. satırlar; hizalama boşlukları ve yorumlar okunabilirlik için kısaltıldı, alan adları ve türler aynen korunmuştur):

```cpp
    struct Command {
        const char* name;         // "help", "clear" vb.
        const char* usage;        // "echo [metin]"
        const char* description;  // Kısa açıklama
        void (Shell::*handler)(int argc, char** argv);
    };
```

Komut çalıştırma fonksiyonu, satırı ayrıştırdıktan sonra tabloda adı arar ve bulduğu işleyiciyi çağırır (`kernel/shell/shell.cpp`, 294-297. satırlar; sondaki yorum kaldırıldı):

```cpp
    for (int i = 0; i < s_command_count; i++) {
        if (kstrcmp(s_commands[i].name, m_argv[0]) == 0) {
            (this->*s_commands[i].handler)(m_argc, m_argv);
            return;
```

Bu tasarımın gücü, yeni komut eklemenin yalnızca tabloya bir satır eklemek olmasıdır; ayrıştırma ve çağırma kodu değişmez. Bu, Bölüm 22.3'teki fabrika tablosu ile aynı fikirdir. Eksik olan tek şey geri almadır. Aşağıda GoF Command'ını, geri al ve yinele yığınlarıyla tamamlayan bir sürümü yazıyoruz.

### GoF Command: geri alma ile

Python'da bir komut, iki kapanış (closure) fonksiyonunun birlikte taşındığı bir nesne olarak düşünülebilir. Kapanış, dış fonksiyonun yerel değişkenlerini yakalayabildiği için komutun geri alma bilgisini (eski metin ya da silinen parça) içinde saklar. Aşağıdaki dosyanın ilk yarısı `Komut` ve `Editor` sınıflarını içerir:

```python
# komut.py: komutlari kapanislarla (closure) nesneleştirmek (22.11)
class Komut:
    """Calistir ve geri al islevlerini bir arada tutar."""
    def __init__(self, ad, calistir, geri_al):
        self.ad = ad
        self.calistir = calistir
        self.geri_al = geri_al


class Editor:
    def __init__(self):
        self.metin = ""
        self._geri = []     # geri al yigini
        self._ileri = []    # yinele yigini

    def yap(self, k):
        k.calistir()
        self._geri.append(k)
        self._ileri.clear()

    def geri(self):
        if not self._geri:
            return False
        k = self._geri.pop()
        k.geri_al()
        self._ileri.append(k)
        return True

    def yinele(self):
        if not self._ileri:
            return False
        k = self._ileri.pop()
        k.calistir()
        self._geri.append(k)
        return True
```

`yap` metodu yeni bir komut çalıştırdığında ileri yığınını temizler. Bu kuralın nedeni açıktır: geçmişi değiştirdikten sonra, eskiden "ileri" olan işlemler artık geçerli değildir. Metin düzenleyicilerdeki davranış da böyledir.

Dosyanın ikinci yarısı, iki komut fabrikasını (`ekle`, `sil`) ve test programını içerir:

```python
def ekle(ed, yazi):
    onceki = None                      # kapanisin yakaladigi durum

    def calistir():
        nonlocal onceki
        onceki = ed.metin
        ed.metin = ed.metin + yazi

    def geri_al():
        ed.metin = onceki
    return Komut("ekle(%s)" % yazi, calistir, geri_al)


def sil(ed, k):
    silinen = ""

    def calistir():
        nonlocal silinen
        silinen = ed.metin[len(ed.metin) - k:]
        ed.metin = ed.metin[:len(ed.metin) - k]

    def geri_al():
        ed.metin = ed.metin + silinen
    return Komut("sil(%d)" % k, calistir, geri_al)


if __name__ == "__main__":
    ed = Editor()
    ed.yap(ekle(ed, "Merhaba"))
    ed.yap(ekle(ed, " dunya"))
    ed.yap(sil(ed, 5))
    print(repr(ed.metin))
    ed.geri()
    ed.geri()
    print(repr(ed.metin))
    ed.yinele()
    print(repr(ed.metin))
```

`ekle` ve `sil` fonksiyonları, komut nesnesi üreten birer fabrikadır. Onlarda `nonlocal` anahtar kelimesi önemlidir: `onceki` ve `silinen` değişkenleri kapanışın içinde güncellenir ve geri alma için saklanır. `nonlocal` olmadan, `calistir` içindeki atama yeni bir yerel değişken yaratırdı ve durum kaybolurdu.

Çıktı:

```term
$ python komut.py
'Merhaba '
'Merhaba'
'Merhaba dunya'
```

Programın yaptığı üç iş var: önce `Merhaba`'yı ekler, sonra ` dunya`'yı ekler ve son beş karakteri siler. Bu noktada metin `Merhaba ` olur. İki geri alma, önce silmeyi, sonra eklemeyi tersine çevirir ve metin `Merhaba` olur. Son yinelemeyle `Merhaba dunya` geri gelir.

C++'ta komutlar sanal bir arayüzle tanımlanır. Her somut komut bir `Metin` alıcısını (receiver) tutar ve iki işlemi uygular. Aşağıdaki kodun ilk yarısı arayüzü ve iki somut komutu içerir:

```cpp
// komut.cpp: GoF Command, geri al / yinele yigini (C++17, 22.11)
#include <cstddef>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

struct Metin {                           // alici (receiver)
    std::string s;
};

struct Komut {                           // Command arayuzu
    virtual ~Komut() = default;
    virtual void calistir() = 0;
    virtual void geri_al() = 0;
};

class Ekle : public Komut {
public:
    Ekle(Metin& m, std::string y) : m_(m), y_(std::move(y)) {}
    void calistir() override { m_.s += y_; }
    void geri_al() override { m_.s.resize(m_.s.size() - y_.size()); }

private:
    Metin& m_;
    std::string y_;
};
```

İkinci yarıda `Sil` komutu ve `Editor` sınıfı var. `Editor`, iki yığını `unique_ptr` vektörleri olarak tutar; bu, komut nesnelerinin sahipliğini yığınların üstlendiği anlamına gelir:

```cpp
class Sil : public Komut {
public:
    Sil(Metin& m, std::size_t k) : m_(m), k_(k) {}
    void calistir() override {
        silinen_ = m_.s.substr(m_.s.size() - k_);
        m_.s.resize(m_.s.size() - k_);
    }
    void geri_al() override { m_.s += silinen_; }

private:
    Metin& m_;
    std::size_t k_;
    std::string silinen_;
};

class Editor {
public:
    void yap(std::unique_ptr<Komut> k) {
        k->calistir();
        geri_.push_back(std::move(k));
        ileri_.clear();   // yeni komut ileri yigini siler
    }

    bool geri() {
        if (geri_.empty()) return false;
        auto k = std::move(geri_.back());
        geri_.pop_back();
        k->geri_al();
        ileri_.push_back(std::move(k));
        return true;
    }

    bool yinele() {
        if (ileri_.empty()) return false;
        auto k = std::move(ileri_.back());
        ileri_.pop_back();
        k->calistir();
        geri_.push_back(std::move(k));
        return true;
    }

    Metin& metin() { return m_; }
    std::size_t geri_sayi() const { return geri_.size(); }
    std::size_t ileri_sayi() const { return ileri_.size(); }

private:
    Metin m_;
    std::vector<std::unique_ptr<Komut>> geri_, ileri_;
};
```

Test programı, her adımdan sonra iki yığının boyutunu yazdırır:

```cpp
void goster(const char* ad, Editor& e) {
    std::cout << ad << " metin=\"" << e.metin().s << "\" geri="
              << e.geri_sayi() << " ileri=" << e.ileri_sayi() << "\n";
}

int main() {
    Editor e;
    e.yap(std::make_unique<Ekle>(e.metin(), "Merhaba"));
    goster("ekle", e);
    e.yap(std::make_unique<Ekle>(e.metin(), " dunya"));
    e.yap(std::make_unique<Sil>(e.metin(), 5));
    goster("sil5", e);
    e.geri();
    goster("geri", e);
    e.geri();
    goster("geri", e);
    e.yinele();
    goster("yinele", e);
    e.yap(std::make_unique<Ekle>(e.metin(), "!"));
    goster("ekle!", e);
    bool y = e.yinele();
    std::cout << "yinele: " << (y ? "evet" : "hayir") << "\n";
}
```

Çıktı:

```term
$ ./komut
ekle metin="Merhaba" geri=1 ileri=0
sil5 metin="Merhaba " geri=3 ileri=0
geri metin="Merhaba dunya" geri=2 ileri=1
geri metin="Merhaba" geri=1 ileri=2
yinele metin="Merhaba dunya" geri=2 ileri=1
ekle! metin="Merhaba dunya!" geri=3 ileri=0
yinele: hayir
```

Son satır, `ekle!` komutunun ileri yığınını temizlediğini gösterir: yinelenecek bir şey kalmamıştır. Bu çıktıyı Çözümlü Örnek 1'de adım adım izleyeceğiz.

**Bedel ve yanlış kullanım.** Command her eylem için bir nesne ister; basit bir çağrı için bu gereksiz bir ağırlıktır. Geri alma da her zaman kolay değildir: bir dosya sisteminde silinen dosyayı geri getirmek, ağ üzerinden gönderilmiş bir paketi geri çekmek gibi işlemler için geri alma bilgisini tam tutamazsın. Bu durumlarda komutu "geri alınabilir" değil, "telafi edilebilir" (compensating action) olarak düşün: geri almak yerine ters yönde yeni bir işlem yap.

Yığın yapısındaki bir tuzak, geri alınan komutların bağımlılığıdır. `sil(5)` komutunun geri alması, önceki `ekle` komutunun sonucuna dayanır. Yığın sırası ile geri alma sırası aynı olmalıdır; aksi hâlde sonuç bozulur. Bu yüzden komutların durumu, kendi kapanışında ya da alanında saklanmalıdır; dışarıdaki bir değişkene bakmamalıdır.

Gerçek dünyada: metin düzenleyicilerin geri al yığınları ve veritabanı işlemlerinin geri alma günlükleri (undo log) bu kalıbın birer uygulamasıdır (genel bilgi).

## 22.12 State: davranışı duruma bağlamak

**Problem.** Bir İHA'nın uçuş modlarını düşün: YERDE, KALKIŞ, SEYİR, İNİŞ. Her olay (ör. "kalkış emri", "irtifa ulaştı") bir moddan diğerine geçiş yapar, ama her modda hangi olayların geçerli olduğu farklıdır. Yerdeyken "iniş emri" anlamsızdır; seyirdeyken "kalkış emri" hatalıdır. Bunu tek bir fonksiyonda `if` ve `elif` ile yazarsan şöyle bir şey çıkar:

```python
def olay(durum, e):
    if durum == "YERDE" and e == "kalkis_emri":
        return "KALKIS"
    elif durum == "KALKIS" and e == "irtifa_ulasti":
        return "SEYIR"
    # ... her durum-olay çifti için bir dal daha
    raise ValueError("gecersiz")
```

Durum sayısı ve olay sayısı arttıkça bu zincir büyür, her dal bir durum-olay çiftini temsil eder ve yeni bir durum eklemek bütün zinciri gözden geçirmeni gerektirir. Üstelik geçersiz çiftlerin hangileri olduğu açıkça görünmez.

**Çözüm.** State kalıbında her durum bir **nesnedir** ve olaylara nasıl tepki vereceğini kendisi bilir. Geçerli bir olay bir sonraki durum nesnesini döndürür; geçersiz olay ise hata verir. Böylece geçiş kuralları durum sınıflarına dağılır, ama her durum yalnızca kendi kurallarını taşır. Bu, Bölüm 21'deki açık-kapalı ilkesine (OCP) yakındır: her durumun kuralları kendi sınıfında yazılıdır. Ancak bu örnekte bir geçişin kuralı kaynak durumun sınıfında durur; yani yeni bir geçiş eklediğinde, o geçişi başlatan durumun kodunu da değiştirirsin. Bu bedeli "Bedel ve yanlış kullanım" bölümünde tartışıyoruz.

![Şekil 22.10: İHA uçuş modları durum makinesi. Geçerli geçişler ok ile gösterilmiştir; YERDE'de iniş emri gibi geçersiz bir olay reddedilir ve durum değişmez.](gorseller/b22_state_ucus.png)

Aşağıdaki Python dosyasında her durum bir sınıftır. Bir durum, kendisine tanımadığı bir olay gelirse üst sınıfın `olay` metoduna devreder ve orada `GecersizGecis` fırlatılır:

```python
# durum.py: IHA ucus modlari, durum nesneleri (Bolum 22.12)
class GecersizGecis(Exception):
    pass


class Durum:
    ad = "?"

    def olay(self, ucak, e):
        mesaj = "%s durumunda %s olayi yok" % (self.ad, e)
        raise GecersizGecis(mesaj)


class Yerde(Durum):
    ad = "YERDE"

    def olay(self, ucak, e):
        if e == "kalkis_emri":
            return KALKIS
        return super().olay(ucak, e)


class Kalkis(Durum):
    ad = "KALKIS"

    def olay(self, ucak, e):
        if e == "irtifa_ulasti":
            return SEYIR
        return super().olay(ucak, e)
```

Dosyanın ikinci yarısında kalan iki durum, durum nesnelerinin tanımı ve `Ucak` sınıfı var:

```python
class Seyir(Durum):
    ad = "SEYIR"

    def olay(self, ucak, e):
        if e == "inis_emri":
            return INIS
        return super().olay(ucak, e)


class Inis(Durum):
    ad = "INIS"

    def olay(self, ucak, e):
        if e == "pist_temas":
            return YERDE
        return super().olay(ucak, e)


YERDE, KALKIS, SEYIR, INIS = Yerde(), Kalkis(), Seyir(), Inis()


class Ucak:
    def __init__(self):
        self.durum = YERDE

    def olay(self, e):
        self.durum = self.durum.olay(self, e)   # hata varsa atama yok
        return self.durum.ad
```

`Ucak.olay`'daki satıra dikkat et: `self.durum = self.durum.olay(self, e)`. Eğer geçersiz bir olay gelirse `olay` metodu istisna fırlatır ve atama hiç gerçekleşmez. Durum değişmez. Bu, geçersiz geçişin durumu bozmamasını sağlayan küçük ama kritik bir ayrıntıdır.

Dosyanın son kısmı, tüm durum-olay çiftlerini tarayan bir test içerir. Dört durum ve dört olay için 16 kombinasyon vardır; geçerli olanlar bir tabloda beklenen sonuçla karşılaştırılır:

```python
OLAYLAR = ["kalkis_emri", "irtifa_ulasti", "inis_emri", "pist_temas"]
BEKLENEN = {("YERDE", "kalkis_emri"): "KALKIS",
            ("KALKIS", "irtifa_ulasti"): "SEYIR",
            ("SEYIR", "inis_emri"): "INIS",
            ("INIS", "pist_temas"): "YERDE"}


if __name__ == "__main__":
    gecerli = reddedilen = 0
    for d in [YERDE, KALKIS, SEYIR, INIS]:
        for e in OLAYLAR:
            u = Ucak()
            u.durum = d
            try:
                sonuc = u.olay(e)
                assert BEKLENEN[(d.ad, e)] == sonuc
                gecerli += 1
            except GecersizGecis:
                assert (d.ad, e) not in BEKLENEN
                assert u.durum is d
                reddedilen += 1
    print("gecerli:", gecerli, "reddedilen:", reddedilen)
    u = Ucak()
    for e in OLAYLAR:
        print(e, "->", u.olay(e))
```

Çıktı:

```term
$ python durum.py
gecerli: 4 reddedilen: 12
kalkis_emri -> KALKIS
irtifa_ulasti -> SEYIR
inis_emri -> INIS
pist_temas -> YERDE
```

Test, 16 kombinasyonun dördünün geçerli, on ikisinin reddedildiğini doğrular ve reddedilen her durumda durumun değişmediğini `assert u.durum is d` ile kontrol eder. İkinci kısım, dört geçişin bir tur attığını (YERDE → KALKIŞ → SEYİR → İNİŞ → YERDE) gösterir.

Aynı davranışın C++ sürümünde durumlar, `gec` sanal metodu döndürdüğü bir işaretçiyle (geçerli değilse `nullptr`) temsil edilir. Durum nesneleri tekildir (her biri bir kez oluşturulur) ve bir `static` yerel değişkende tutulur. Aşağıdaki kodun ilk yarısı durum arayüzünü ve dört durumu içerir:

```cpp
// durum.cpp: IHA ucus modlari, durum nesneleri (C++17, Bolum 22.12)
#include <iostream>
#include <stdexcept>
#include <string>

enum class Olay { KalkisEmri, IrtifaUlasti, InisEmri, PistTemas };

struct Durum;
const Durum& yerde();
const Durum& kalkis();
const Durum& seyir();
const Durum& inis();

struct Durum {                           // soyut durum
    virtual ~Durum() = default;
    virtual const char* ad() const = 0;
    // Gecerli gecis: yeni durum. Gecersiz: nullptr.
    virtual const Durum* gec(Olay) const { return nullptr; }
};

struct Yerde : Durum {
    const char* ad() const override { return "YERDE"; }
    const Durum* gec(Olay e) const override {
        return e == Olay::KalkisEmri ? &kalkis() : nullptr;
    }
};

struct Kalkis : Durum {
    const char* ad() const override { return "KALKIS"; }
    const Durum* gec(Olay e) const override {
        return e == Olay::IrtifaUlasti ? &seyir() : nullptr;
    }
};
```

İkinci yarıda kalan iki durum, tekil erişim fonksiyonları ve `Ucak` sınıfı bulunur:

```cpp
struct Seyir : Durum {
    const char* ad() const override { return "SEYIR"; }
    const Durum* gec(Olay e) const override {
        return e == Olay::InisEmri ? &inis() : nullptr;
    }
};

struct Inis : Durum {
    const char* ad() const override { return "INIS"; }
    const Durum* gec(Olay e) const override {
        return e == Olay::PistTemas ? &yerde() : nullptr;
    }
};

const Durum& yerde() { static Yerde s; return s; }
const Durum& kalkis() { static Kalkis s; return s; }
const Durum& seyir() { static Seyir s; return s; }
const Durum& inis() { static Inis s; return s; }

class Ucak {
public:
    void olay(Olay e) {
        const Durum* y = durum_->gec(e);
        if (!y)
            throw std::runtime_error(std::string(durum_->ad()) +
                                     " durumunda olay yok");
        durum_ = y;                      // hata yoksa durum degisir
    }
    const char* ad() const { return durum_->ad(); }
    void durum_ata(const Durum& d) { durum_ = &d; }

private:
    const Durum* durum_ = &yerde();
};
```

Son yarı testi içerir. Test, dört durum ve dört olay için bütün kombinasyonları dener ve bir hata yakalanınca durumun değişmediğini gösterir:

```cpp
int main() {
    const Durum* durumlar[] = {&yerde(), &kalkis(),
                               &seyir(), &inis()};
    const Olay olaylar[] = {Olay::KalkisEmri, Olay::IrtifaUlasti,
                            Olay::InisEmri, Olay::PistTemas};
    int gecerli = 0, reddedilen = 0;
    for (const Durum* d : durumlar)
        for (Olay e : olaylar) {
            Ucak u;
            u.durum_ata(*d);
            try {
                u.olay(e);
                ++gecerli;
            } catch (const std::runtime_error&) {
                ++reddedilen;
            }
        }
    std::cout << "gecerli: " << gecerli << " reddedilen: "
              << reddedilen << "\n";
    Ucak u;
    u.olay(Olay::KalkisEmri);
    std::cout << "kalkis sonrasi: " << u.ad() << "\n";
    try {
        u.olay(Olay::InisEmri);
    } catch (const std::runtime_error& e) {
        std::cout << "hata: " << e.what() << "\n";
    }
    std::cout << "hata sonrasi durum: " << u.ad() << "\n";
}
```

Çıktı:

```term
$ ./durum
gecerli: 4 reddedilen: 12
kalkis sonrasi: KALKIS
hata: KALKIS durumunda olay yok
hata sonrasi durum: KALKIS
```

Son iki satır, geçersiz geçişin durumu değiştirmediğini gösterir: `KALKIS` durumundayken `inis_emri` hata verir ve durum hâlâ `KALKIS` olarak kalır.

**Bedel ve yanlış kullanım.** State'in en büyük bedeli sınıf sayısıdır: her durum bir sınıf (ya da en azından bir nesne) demektir. Dört durum için bu önemsiz, ama elli durum için ağır bir yapıdır. Ayrıca geçiş kuralları durumlara dağıldığı için, "bu geçiş nasıl oluyor?" sorusunun cevabını görmek için birden fazla sınıfı okuman gerekir. Bu yüzden bir geçiş tablosunu (durum × olay → yeni durum) ayrıca belgelemek iyi bir pratiktir; yukarıdaki `BEKLENEN` sözlüğü tam bunu yapar.

Yanlış kullanım, durumların kendi içinde karmaşık işlemler yapması ve durumlar arası bağımlılığın dağılmasıdır. Her durum yalnızca bir sonraki durumu bilmeli; mesela "YERDE'den KALKIŞ'a geç ve motoru çalıştır" işlemini durumun içine koymak yerine, geçiş sırasında çağrılan bir eylem olarak ayrı tut.

Bir başka bedel, geçiş kurallarının dağılmasının yarattığı değişiklik maliyetidir. Yukarıdaki sistemde `Seyir`'e yeni bir `sakla` olayı eklemek, yalnızca `Seyir.olay`'e yeni bir dal eklemekle kalmaz; bu geçişi bilen herkesin zihninde o kuralı yeniden kurmasını gerektirir. Geçişleri tek bir tabloda tutmak (ör. yukarıdaki `BEKLENEN` sözlüğü gibi) kuralları tek yerde görmeni sağlar; kalıbın tam biçimi ise durumlar yerine tabloyla çalışır. İkisi arasındaki seçimi, geçiş sayısı ve değişim sıklığına göre yap.

Bir başka ayrıntı, durumun yalnızca geçişi değil, kendi kurallarını da kapsadığıdır. Durum sınıfları, `Ucak` gibi bir bağlamın alanlarına erişiyorsa, sınıflar arası sıkı bağlılık oluşur. Durumun ihtiyaç duyduğu veriyi parametre olarak almasını tercih et.

Gerçek dünyada: TCP bağlantısının durumları (SYN_SENT, ESTABLISHED, FIN_WAIT gibi) ve birçok protokol kütüphanesinin bağlantı yaşam döngüsü bu kalıpla modellenir (genel bilgi; bu bölümde bir TCP yığınını doğrulamadık).

## 22.13 Kalıpların birlikte kullanımı: mini bir sistem

Gerçek sistemlerde kalıplar tek başına değil, birlikte çalışır. Yukarıdaki üç kalıbı tek bir mini sistemde birleştirelim: uçağın durumu State ile yönetilsin, her geçiş bir Command nesnesi olarak kaydedilsin ve geçişleri izleyen bir gözlemci günlük tutsun.

Bu birleşimde her kalıp kendi sorumluluğunu taşır. State geçiş kurallarını, Command eylemleri ve geri almayı, Observer da değişikliklerin izlenmesini üstlenir. Bu ayrım, Bölüm 21'deki tek sorumluluk ilkesinin (SRP) kalıplara uygulanmasıdır: her parça tek bir şeyi değiştirir.

```python
# birlikte.py: komut + gozlemci + durum, tek mini sistemde (22.13)
from durum import Ucak, GecersizGecis


class Kayit:
    """Gozlemci: her gecisi bir satir olarak saklar."""
    def __init__(self):
        self.satirlar = []

    def guncelle(self, eski, yeni, olay):
        self.satirlar.append("%s -%s-> %s" % (eski, olay, yeni))


class OlayKomutu:
    """Command: bir olayi nesne olarak tutar, geri alabilir."""
    def __init__(self, ucak, olay):
        self.ucak = ucak
        self.olay = olay
        self.eski = None

    def calistir(self):
        self.eski = self.ucak.durum       # geri almak icin sakla
        self.ucak.olay(self.olay)

    def geri_al(self):
        self.ucak.durum = self.eski
```

`OlayKomutu`, geri almayı kolaylaştıran bir noktadadır: geçişten önceki durum nesnesini saklar. Durumlar tekil nesneler olduğu için, bu saklamak yalnızca bir referans kopyalamaktır.

Yönetici sınıfı, komutları çalıştırır, geçmişi tutar ve gözlemcileri bilgilendirir:

```python
class Yonetici:
    def __init__(self, ucak):
        self.ucak = ucak
        self.gecmis = []
        self.gozlemciler = []

    def yap(self, olay):
        eski = self.ucak.durum.ad
        k = OlayKomutu(self.ucak, olay)
        k.calistir()                      # GecersizGecis yukari cikar
        self.gecmis.append(k)
        self._bildir(eski, self.ucak.durum.ad, olay)

    def geri(self):
        if not self.gecmis:
            return
        eski = self.ucak.durum.ad
        k = self.gecmis.pop()
        k.geri_al()
        self._bildir(eski, self.ucak.durum.ad, "geri")

    def _bildir(self, eski, yeni, olay):
        for g in self.gozlemciler:
            g(eski, yeni, olay)
```

`yap` metodunda önemli bir sıra vardır: komut çalıştırılırsa, yalnızca o zaman geçmişe eklenir. Geçersiz bir olay `calistir` içinde `GecersizGecis` fırlattığında geçmişe bir şey eklenmez ve gözlemciler bildirilmez. Böylece geçmiş yalnızca gerçekten gerçekleşen işlemleri tutar.

Test, bir dizi olay gönderir ve geçersiz bir olayı ayrıca yakalar:

```python
if __name__ == "__main__":
    u = Ucak()
    y = Yonetici(u)
    kayit = Kayit()
    y.gozlemciler.append(kayit.guncelle)
    for e in ["kalkis_emri", "inis_emri", "irtifa_ulasti",
              "inis_emri", "geri"]:
        try:
            if e == "geri":
                y.geri()
            else:
                y.yap(e)
        except GecersizGecis:
            print("reddedildi:", e)
    for s in kayit.satirlar:
        print(s)
    print("son durum:", u.durum.ad)
```

Çıktı:

```term
$ python birlikte.py
reddedildi: inis_emri
YERDE -kalkis_emri-> KALKIS
KALKIS -irtifa_ulasti-> SEYIR
SEYIR -inis_emri-> INIS
INIS -geri-> SEYIR
son durum: SEYIR
```

İlk olay (`kalkis_emri`) YERDE'den KALKIŞ'a geçer. İkincisi (`inis_emri`) KALKIŞ'ta geçersizdir ve reddedilir; bu yüzden kayda girmez. Üçüncü ve dördüncü olaylar geçerlidir. Son `geri` komutu, son geçişi (SEYİR'den İNİŞ'e) tersine çevirir ve durum SEYİR olur. Gözlemci her gerçekleşen değişimi satır olarak kaydeder; geri alma da ayrı bir satır olarak görünür.

**Bu birleşimin bedeli.** Üç kalıbın birlikte kullanılması kodu esnek yapar ama dolaylamayı artırır. Yukarıdaki sistemde bir olayın yolu üç dosyadan geçer: `Yonetici.yap`, `OlayKomutu.calistir` ve `Ucak.olay` ile durum sınıfı. Bu üçlüyü izleyebilmek için her birinin sorumluluğunu bilmen gerekir. Küçük bir sistem için bu fazla olabilir; ama bir İHA'nın kontrol yazılımında her geçişin kaydının tutulması ve geri alınabilmesi çoğu zaman gerçekten gereklidir.

## 22.14 Kalıp seçimi: bir karar tablosu

Kalıpları bilmek yetmez; doğru zamanda seçmen gerekir. Aşağıdaki karar ağacı, bir sorunu üç ana soruya ayırır ve her dalda uygun kalıbı önerir. Ağaç bir reçete değildir: "şu ağrıyı hissediyorsan şu kalıp" bir başlangıç noktasıdır, son karar tasarımın bağlamına bağlıdır.

![Şekil 22.11: Kalıp seçim karar ağacı. Önce sorunun türü (nesne kurulumu, yapı, davranış), sonra ağrının ayrıntısı belirlenir.](gorseller/b22_karar_agaci.png)

| Ağrı (belirti) | Aday kalıp | Kanıt olarak bu bölümdeki örnek |
|---|---|---|
| Parametre çok, bazıları isteğe bağlı | Builder | `UcusAyar`, 22.4 |
| Tür, çalışma zamanında seçilecek | Factory | Sensör kayıt tablosu, 22.3 |
| Tek örnek "gerekli" gibi görünüyor | Önce DI, sonra singleton | `Kaydedici(depo)`, 22.5 |
| Dış bileşenin arayüzü uyumsuz | Adapter | `Uyarlayici`, 22.6 |
| Özellikler kombinasyonla çoğalıyor | Decorator | Önbellek, yeniden deneme, 22.7 |
| İstemci çok fazla alt sistem biliyor | Facade | `TelemetriFasad`, 22.8 |
| Aynı işin birden çok yöntemi var | Strategy | Filtre stratejileri, 22.9 |
| Bir değişimi birçok taraf izliyor | Observer | Alarm aboneleri, 22.10 |
| Eylem geri alınacak ya da kaydedilecek | Command | Metin düzenleyici, 22.11 |
| Davranış duruma göre değişiyor | State | İHA uçuş modları, 22.12 |

Tablodaki son sütun, her kalıbın bu bölümde gerçek bir kodla gösterildiğini hatırlatır. Bir kalıbı seçtiğinde, bu örneğe geri dön ve benzerliği kendi probleminle karşılaştır. Benzerlik yoksa kalıbı kullanma.

Bir karar kuralı daha: en basit çözümle başla. Bir `if` zinciri, bir fonksiyon ya da bir sözlük çoğu zaman yeterlidir. Kalıba ancak aynı sorun üç kez ortaya çıktığında, ya da değişikliğin maliyeti görünür hâle geldiğinde geç.

## Çözümlü Örnekler

Bu bölümdeki dört örnek ★ zorluğundan ★★★'e doğru ilerler. Her örnekte Bölüm 5'teki altı adımı izleyeceğiz. Adım 6'da elle iz sürme tablosu olacak; tablodaki değerler örneğin programının çıktısıyla aynıdır. Kodu okumadan önce her örneğin ilk üç adımını kendi kâğıdında dene.

### Örnek 1 (★): Metin düzenleyicide geri al ve yinele

**Problem:** Bir metin düzenleyicinin ekle ve sil komutlarını, geri al ve yinele desteğiyle çalıştır. Komut dizisi: `Merhaba` ekle, ` dunya` ekle, son 5 karakteri sil, iki kez geri al, bir kez yinele, `!` ekle, sonra yinele.

**Adım 1 — Anla.** Girdi bir komut dizisidir; her komut ekle, sil, geri veya yinele olabilir. Çıktı, her adımdan sonraki metin ile iki yığının boyutudur. Kenar durumlar: boş geri alma yığınında `geri` hiçbir şey yapmaz ve `False` döner; yeni bir komut ileri yığınını temizler, yani geri alınmış işlemler artık yinelenemez.

**Adım 2 — Örnekle.** `Merhaba` ekledikten sonra metin `Merhaba`'dır ve geri alma yığını tek bir komut içerir. ` dunya` eklersen metin `Merhaba dunya` olur. Son 5 karakteri sildiğinde metin `Merhaba ` olur; bu noktada silinen `dunya` kelimesini geri getirebilmen gerekir. Bunu kendi kâğıdında iki kez geri alıp yinelediğinde ne olacağını izle.

**Adım 3 — Kaba çöz.** En basit çözüm, her değişimden önce metnin tam bir kopyasını (anlık görüntü, snapshot) bir listeye koymaktır. Geri almak, son kopyayı geri yüklemektir. Bu çalışır, ama bellek kullanımı her adımda metnin tamamı kadar büyür ve yinele için ayrı bir mantık gerekir.

**Adım 4 — Örüntü.** Her değişimin bir tersi vardır: ekleyen komutun tersi, eklenen parçayı silmektir; silen komutun tersi, silinen parçayı geri eklemektir. Bu tersleri komut nesnelerinde saklarsan, geri alma yalnızca "yığının tepesini çek ve tersini uygula" olur. Yinelemek için iki yığın yeterlidir: geri alınan komut ileri yığınına, yinelenen komut geri yığınına geçer.

**Adım 5 — İyileştir.** Anlık görüntü yerine komut nesnesini kullanıyoruz. Silme komutu yalnızca silinen parçayı saklar, ekleme komutu yalnızca eski metni saklar. Bu sürümde ekleme komutu hâlâ eski metnin tamamını tutar; fark (diff) saklamak daha az bellek kullanır ve bu, bir sonraki iyileştirme olarak Ek Alıştırmalar'da yer alıyor. Programda düzenleyici, `komut.py`'deki `Editor` sınıfını kullanır:

```python
# ornek1.py: komut yiginleriyle geri al / yinele izi (Ornek 1)
from komut import Editor, ekle, sil


def yaz(ad, ed):
    print("%-9s metin=%-15r geri=%d ileri=%d"
          % (ad, ed.metin, len(ed._geri), len(ed._ileri)))


if __name__ == "__main__":
    ed = Editor()
    ed.yap(ekle(ed, "Merhaba"))
    yaz("ekle", ed)
    ed.yap(ekle(ed, " dunya"))
    yaz("ekle", ed)
    ed.yap(sil(ed, 5))
    yaz("sil 5", ed)
    ed.geri()
    yaz("geri", ed)
    ed.geri()
    yaz("geri", ed)
    ed.yinele()
    yaz("yinele", ed)
    ed.yap(ekle(ed, "!"))
    yaz("ekle", ed)
    print("yinele ->", ed.yinele())
    yaz("son", ed)
    assert ed.metin == "Merhaba dunya!"
```

**Adım 6 — Doğrula.** Program her adımdan sonra iki yığının boyutunu yazdırır ve son metni `assert` ile kontrol eder. Aşağıdaki tablo, her adımda yığınların içeriğini elle izlediğimiz sonuçtur (geri yığını için en üstteki komut sağda, ileri yığını için en üstteki komut en sağdadır):

| Adım | İşlem | Metin | Geri yığını | İleri yığını |
|---|---|---|---|---|
| 1 | ekle(Merhaba) | `Merhaba` | ekle(Merhaba) | — |
| 2 | ekle( dunya) | `Merhaba dunya` | ekle(Merhaba), ekle( dunya) | — |
| 3 | sil(5) | `Merhaba ` | ..., sil(5) | — |
| 4 | geri | `Merhaba dunya` | ekle(Merhaba), ekle( dunya) | sil(5) |
| 5 | geri | `Merhaba` | ekle(Merhaba) | sil(5), ekle( dunya) |
| 6 | yinele | `Merhaba dunya` | ekle(Merhaba), ekle( dunya) | sil(5) |
| 7 | ekle(!) | `Merhaba dunya!` | ..., ekle(!) | — (temizlendi) |
| 8 | yinele | `Merhaba dunya!` | değişmez | değişmez, `False` döner |

```term
$ python ornek1.py
ekle      metin='Merhaba'       geri=1 ileri=0
ekle      metin='Merhaba dunya' geri=2 ileri=0
sil 5     metin='Merhaba '      geri=3 ileri=0
geri      metin='Merhaba dunya' geri=2 ileri=1
geri      metin='Merhaba'       geri=1 ileri=2
yinele    metin='Merhaba dunya' geri=2 ileri=1
ekle      metin='Merhaba dunya!' geri=3 ileri=0
yinele -> False
son       metin='Merhaba dunya!' geri=3 ileri=0
```

Tablodaki satırlar çıktıyla birebir eşleşir. Adım 5'teki iki geri alma sonrasında ileri yığınının tepesinin `ekle( dunya)` olduğuna dikkat et: ilk `geri` `sil(5)`'i, ikincisi `ekle( dunya)`'yı yığına koydu. Bu yüzden `yinele` önce `ekle( dunya)`'yı geri getirir. Son satır, yeni bir `ekle` komutunun ileri yığınını temizlediğini gösterir; `yinele` artık `False` döner.

**Bunu AI'sız yazabilir misin?** Aynı düzenleyiciyi `ekle`, `sil` ve `yinele` ile, yalnızca iki yığın ve bir `Komut` sınıfı kullanarak sıfırdan yaz. Her adımdan sonra iki yığının boyutunu yazdır ve yukarıdaki tabloyla karşılaştır. Tablo tutmuyorsa hatayı bulmak senin işindir.

### Örnek 2 (★★): İHA uçuş modu ve geçersiz geçiş testi

**Problem:** Bir İHA'nın dört uçuş modunu (YERDE, KALKIŞ, SEYİR, İNİŞ) ve dört olayı (kalkış emri, irtifa ulaştı, iniş emri, pist teması) düşün. Her durum-olay çiftinin 16 kombinasyonu vardır. Geçerli geçişleri ve reddedilenleri tek bir tabloda göster ve reddedilen her geçişte durumun değişmediğini doğrula.

**Adım 1 — Anla.** Girdi bir durum ve bir olaydır; çıktı yeni durum ya da reddetmedir. Kenar durumlar: aynı olay bir durumda iki kez gelirse (ör. SEYİR'de iki kez `irtifa_ulasti`), ikinci gelişte reddedilir çünkü SEYİR'den çıkacak bir `irtifa_ulasti` geçişi yoktur.

**Adım 2 — Örnekle.** YERDE'de `kalkis_emri` geçerlidir ve KALKIŞ'a götürür. YERDE'de `inis_emri` ise reddedilmelidir; İHA yerde iken inmeye çalışmak anlamsızdır. KALKIŞ'ta `inis_emri`'nin de reddedileceğini kendi kâğıdında doğrula.

**Adım 3 — Kaba çöz.** Her durum-olay çifti için bir `if` yaz: `if durum == "YERDE" and olay == "kalkis_emri": ...` gibi. 16 çift için 16 dal gerekir ve her dalın sonunda yeni durumu atarsın. Hatalı bir dal (ör. yanlış yeni durum) ancak test edildiğinde fark edilir.

**Adım 4 — Örüntü.** Her durumun geçerli olayları azdır (her durumda en fazla bir geçerli olay var). Bu, her durum için ayrı bir sınıf açmanın ve her sınıfa yalnızca kendi geçişini yazmanın ne kadar doğal olduğunu gösterir. Reddetme, her durumun varsayılan davranışı olarak tek bir yerde (`Durum.olay`) toplanabilir.

**Adım 5 — İyileştir.** `durum.py`'deki State kalıbını kullanıyoruz: her durum sınıfı kendi geçişini bilir, bilmediği olayı üst sınıfa devreder ve üst sınıf `GecersizGecis` fırlatır. `Ucak.olay`, yeni durumu yalnızca geçiş başarılıysa atar. Bu, geçersiz bir geçişin durumu bozmadığını yapısal olarak garanti eder.

```python
# ornek2.py: IHA durum tablosunun tam taranmasi (Ornek 2)
from durum import YERDE, KALKIS, SEYIR, INIS, Ucak, GecersizGecis

OLAYLAR = ["kalkis_emri", "irtifa_ulasti", "inis_emri", "pist_temas"]
DURUMLAR = [YERDE, KALKIS, SEYIR, INIS]

print("%-8s" % "durum" + "".join("%-14s" % e for e in OLAYLAR))
gecerli = 0
for d in DURUMLAR:
    satir = []
    for e in OLAYLAR:
        u = Ucak()
        u.durum = d
        try:
            satir.append(u.olay(e))
            gecerli += 1
        except GecersizGecis:
            assert u.durum is d            # red: durum degismedi
            satir.append("X")
    print("%-8s" % d.ad + "".join("%-14s" % s for s in satir))
print("gecerli gecis:", gecerli, "/ 16")
```

**Adım 6 — Doğrula.** Program 16 çiftin hepsini dener. Her reddetmede `assert u.durum is d` durumun değişmediğini kontrol eder. Aşağıdaki tablo, satırları durum, sütunları olay olan elle izlediğimiz sonuçtur; `X` reddedilen geçişi gösterir.

| Durum \ Olay | kalkis_emri | irtifa_ulasti | inis_emri | pist_temas |
|---|---|---|---|---|
| YERDE | KALKIS | X | X | X |
| KALKIS | X | SEYIR | X | X |
| SEYIR | X | X | INIS | X |
| INIS | X | X | X | YERDE |

```term
$ python ornek2.py
durum   kalkis_emri   irtifa_ulasti inis_emri     pist_temas    
YERDE   KALKIS        X             X             X             
KALKIS  X             SEYIR         X             X             
SEYIR   X             X             INIS          X             
INIS    X             X             X             YERDE         
gecerli gecis: 4 / 16
```

Tablo, dört geçerli geçişi (köşegen boyunca bir tur) ve on iki reddi gösterir. Çıktıdaki `4 / 16`, elle sayımla aynıdır.

**Bunu AI'sız yazabilir misin?** Dört yeni durum ekle: `BEKLEME` (YERDE'de bekleme, `komut_bekle` olayıyla), `ACIL_INIS` (SEYİR'den, `acil` olayıyla) ve ona uygun geçişler. Geçerli geçiş sayısını ve reddedilen sayısını önceden hesapla, sonra programı çalıştırıp tutup tutmadığına bak. Tutmuyorsa hangi geçişi yanlış yazdığını bul.

### Örnek 3 (★★): Sensör eşik alarmı, abonelikten çıkma ve zayıf referans

**Problem:** Bir sıcaklık konusu (subject) ölçümleri alır ve iki gözlemciye bildirir: eşiği 80 olan bir kritik alarm ve eşiği 50 olan bir geçici alarm. Ölçümler 40, 60, 85 sırasında gelir; sonra geçici alarm abonelikten çıkar ve 90 gelir; son olarak geçici bir gözlemci silinir ve bir ölçüm daha gelir. Her adımda hangi alarmların çaldığını ve kaç abonenin kaldığını göster.

**Adım 1 — Anla.** Girdi bir ölçüm dizisi ve abonelik işlemleridir (ekle, çıkar, sil). Çıktı, her ölçümde çalan alarmlar ve sonunda kalan abone sayısıdır. Kenar durumlar: ölçüm eşiğe tam eşitse (ör. 80) alarm çalmaz, çünkü karşılaştırma `>` ile yapılır; bir gözlemci çıkmış ama henüz bildirim görmemişse listede kalmaz; silinmiş bir gözlemci bir sonraki bildirimde temizlenir.

**Adım 2 — Örnekle.** Ölçüm 60 geldiğinde geçici alarm (eşik 50) çalar, kritik alarm (eşik 80) çalmaz. Ölçüm 85 geldiğinde ikisi de çalar. Ölçüm 90'da geçici alarm artık abone değildir; yalnızca kritik alarm çalar.

**Adım 3 — Kaba çöz.** Her ölçümde her gözlemciyi bir `if` ile elle çağırabilirsin. Bu, gözlemci sayısı artınca her yeri değiştirmeyi gerektirir; ayrıca çıkarma ve silme için özel bir kontrol gerekir.

**Adım 4 — Örüntü.** Konu ve gözlemci ayrılır: konu yalnızca bir arayüz çağırır, gözlemciler kendilerini ekler ve çıkarır. Zayıf referans, silinmiş gözlemcinin konu tarafından tutulmasını engeller. Bildirim kopya üzerinde gezilir, böylece bir gözlemcinin kendini çıkarması döngüyü bozmaz.

**Adım 5 — İyileştir.** `gozlemci.py`'deki `Konu` sınıfını kullanıyoruz. `cik` ile geçici alarm abonelikten çıkarılır; `del` ile silinen gözlemci, bir sonraki bildirimde ölü referans olarak temizlenir.

```python
# ornek3.py: esik alarmi, abonelikten cikma, zayif referans (Ornek 3)
from gozlemci import Konu, Alarm

k = Konu()
kritik = Alarm("kritik", 80)
gecici = Alarm("gecici", 50)
k.abone_ol(kritik.olay)
k.abone_ol(gecici.olay)
for d in [40, 60, 85]:
    print("olcum", d)
    k.bildir(d)
k.cik(gecici.olay)                  # gecici abonelikten cikar
print("cikis sonrasi olcum 90")
k.bildir(90)
print("gecici:", gecici.kayitlar, "| kritik:", kritik.kayitlar)
ge = Alarm("ge", 0)
k.abone_ol(ge.olay)
del ge                              # Konu nesneyi tutmaz
k.bildir(5)
print("abone sayisi:", len(k._gozlemciler))
```

**Adım 6 — Doğrula.** Aşağıdaki iz tablosu, her olaydan sonra abonelerin durumunu gösterir. Program ayrıca `kayitlar` listelerini yazdırır; bu listeler tabloyla eşleşir.

| Olay | Çalan alarmlar | Abone sayısı (olay sonrası) |
|---|---|---|
| ölçüm 40 | yok | 2 |
| ölçüm 60 | geçici | 2 |
| ölçüm 85 | kritik, geçici | 2 |
| geçici çıkar | — | 1 |
| ölçüm 90 | kritik | 1 |
| `ge` abone ol, sil, ölçüm 5 | yok (ölü referans temizlenir) | 1 |

```term
$ python ornek3.py
olcum 40
olcum 60
  ALARM gecici 60
olcum 85
  ALARM kritik 85
  ALARM gecici 85
cikis sonrasi olcum 90
  ALARM kritik 90
gecici: [40, 60, 85] | kritik: [40, 60, 85, 90]
abone sayisi: 1
```

Tabloyla çıktı birebir uyuşur. Çıktıdaki `gecici: [40, 60, 85]` satırı, geçici alarmın yalnızca çıkmadan önceki üç ölçümü gördüğünü gösterir. Tablodaki son satırın "abone sayısı 1" olması, `ge` gözlemcisinin silindikten sonra konudan temizlendiğini doğrular (kritik alarm hâlâ kayıtlı olduğu için 1 kalır).

**Bunu AI'sız yazabilir misin?** Ölçüm dizisi `[70, 90, 40]` olsun. Eşikleri kritik 80, geçici 65 seç. Önce her ölçümde hangi alarmın çalacağını tabloya yaz; sonra geçici alarmı ölçüm 70'ten sonra çıkar ve kodu çalıştırıp tabloyla karşılaştır.

### Örnek 4 (★★★): Önbellek, süre ölçümü ve yeniden deneme zinciri

**Problem:** Bir sensör okuyucusu şu üç özelliği birlikte taşımalıdır: değeri önbelleğe almak, okumanın harcadığı toplam süreyi ölçmek ve geçici hatalarda yeniden denemek. Donanım taklidi, ikinci denemesinde hata versin; her denemenin 5 milisaniye sürdüğünü varsay. İki zincir kur: birincisinde önbellek yok, ikincisinde önbellek en dışta. Her çağrıdaki değeri, donanım deneme sayısını ve toplam süreyi göster.

**Adım 1 — Anla.** Girdi bir okuma çağrı dizisidir (her biri aynı arayüzden geçer). Çıktı: değer, donanımın toplam deneme sayısı ve ölçülen süre. Kenar durumlar: önbellekten gelen çağrı donanıma hiç ulaşmaz ve süre eklemez; yeniden denemenin sınırı aşılırsa hata dışarı çıkar (bu davranışı Ek Alıştırmalar'da test edeceksin).

**Adım 2 — Örnekle.** Birinci okuma: donanımın birinci denemesi başarılıdır, değer 21, süre 5 ms. İkinci okuma: birinci deneme hata verir (süre 10 ms), ikinci deneme başarılıdır (süre 15 ms toplam), değer 23. Önbellekli zincirde ikinci okuma, önbellekten `21` döner ve donanıma gitmez.

**Adım 3 — Kaba çöz.** Üç özelliği tek bir sınıfta yazabilirsin: önbellek, süre ve deneme döngüsü aynı `oku` metodunda. Bu çalışır, ama bir özelliği kaldırmak ya da iki zincirin sırasını değiştirmek için sınıfı yeniden yazman gerekir.

**Adım 4 — Örüntü.** Her özellik ayrı bir sarıcıdır ve hepsi `Okuyucu` arayüzünü uygular. Sıra önemlidir: önbellek dıştaysa, önbellek isabeti süreyi ve denemeleri hiç etkilemez; ölçüm dıştaysa, ölçüm önbellek isabetlerini de sayar. Bunu tabloda görmek için iki zincir kurarız.

**Adım 5 — İyileştir.** `sarici.py`'deki `Onbellek` ve `Yeniden` sınıflarını kullanıyoruz. Yeni olarak, sahte bir saat ve donanım taklidi yazıyoruz; böylece süre ölçümü deterministik olur ve gerçek zamana bağlı çıktı oluşmaz.

```python
# ornek4.py: onbellek + olcum + yeniden deneme zinciri (Ornek 4)
from sarici import Okuyucu, Onbellek, Yeniden


class Saat:
    def __init__(self):
        self.t = 0.0


class SaatliHam(Okuyucu):
    """Her deneme 5 ms surer; basarisiz denemeler de sure harcar."""
    def __init__(self, saat, hatali):
        self.saat = saat
        self.hatali = hatali
        self.deneme = 0

    def oku(self):
        self.deneme += 1
        self.saat.t += 0.005
        if self.deneme in self.hatali:
            raise IOError("deneme %d basarisiz" % self.deneme)
        return 20.0 + self.deneme
```

Dosyanın ikinci yarısı ölçüm sarıcısını, iki zinciri ve ana programı içerir:

```python
class Olcum(Okuyucu):
    """Ic cagrinin harcadigi toplam sureyi biriktirir."""
    def __init__(self, ic, saat):
        self._ic = ic
        self._saat = saat
        self.sure = 0.0

    def oku(self):
        t0 = self._saat.t
        try:
            return self._ic.oku()
        finally:
            self.sure += self._saat.t - t0


def zincir_a():
    saat = Saat()
    ham = SaatliHam(saat, hatali={2})
    olc = Olcum(Yeniden(ham), saat)          # onbellek yok
    return olc, ham


def zincir_b():
    saat = Saat()
    ham = SaatliHam(saat, hatali={2})
    olc = Olcum(Yeniden(ham), saat)
    return Onbellek(olc), olc, ham           # onbellek en dis katman


if __name__ == "__main__":
    olc, ham = zincir_a()
    for i in (1, 2):
        v = olc.oku()
        print("A %d: deger=%.1f deneme=%d sure=%.3f s"
              % (i, v, ham.deneme, olc.sure))
    z, olc, ham = zincir_b()
    for i in (1, 2):
        v = z.oku()
        print("B %d: deger=%.1f deneme=%d sure=%.3f s"
              % (i, v, ham.deneme, olc.sure))
```

**Adım 6 — Doğrula.** Aşağıdaki tablo her çağrıyı, zincirdeki katmanları ve sayaçların değerlerini gösterir.

| Zincir | Çağrı | Ne oldu | Değer | Donanım denemesi | Toplam süre |
|---|---|---|---|---|---|
| A | 1 | deneme 1 başarılı | 21.0 | 1 | 0.005 s |
| A | 2 | deneme 2 hata, deneme 3 başarılı | 23.0 | 3 | 0.015 s |
| B | 1 | deneme 1 başarılı, önbelleğe girer | 21.0 | 1 | 0.005 s |
| B | 2 | önbellek isabeti, donanıma gitmez | 21.0 | 1 | 0.005 s |

```term
$ python ornek4.py
A 1: deger=21.0 deneme=1 sure=0.005 s
A 2: deger=23.0 deneme=3 sure=0.015 s
B 1: deger=21.0 deneme=1 sure=0.005 s
B 2: deger=21.0 deneme=1 sure=0.005 s
```

Zincir A'da ikinci çağrının süresi 0.015 saniyedir çünkü `Olcum` yeniden denemenin harcadığı tüm süreyi (10 ms hatalı deneme dahil) sayar. Zincir B'de önbellek dışta olduğu için ikinci çağrı `Olcum`'a bile ulaşmaz; süre değişmez ve donanım denemesi `1` kalır. Bu sonuç, sarıcıların sırasının neyi ölçtüğünü doğrudan belirler.

**Bunu AI'sız yazabilir misin?** Zincire bir `Yeniden(ham, deneme=2)` ekle ve `hatali={1, 2}` ile donanımın ilk iki denemesini başarısız yap. Üçüncü çağrıda ne olacağını tahmin et: hata dışarı çıkar mı, yoksa sarıcı yine başarılı mı olur? Sonra kodu çalıştırıp tahmininle karşılaştır; tahmin tutmazsa `Yeniden.oku` içindeki `raise` satırının hangi koşulda çalıştığını yeniden oku.

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Kalıpların asıl eğitimi, hangi sorunda hangi kalıbın doğduğunu kendi kodunda fark etmektir. Bir aracın yazdığı kod çalışıyor görünse bile, kalıbın neden orada olduğunu ve hangi değişikliğe dayanıklı olduğunu sen test etmedikçe bilmezsin.
:::

### Proje 1 (★★): MertOS mini kabuğu: komut tablosu, geçmiş ve geri al

**Amaç:** Bölüm 22.11'deki MertOS komut tablosunu GoF Command biçimine taşımak: komutlar nesne olsun, komut kaydı bir Factory gibi çalışsın ve kabuk geçmişi geri alma ile birlikte tutsun. Sonuç, C++17 ile yazılmış, WSL'de sanitizer'larla temiz geçen bir programdır.

**Yapılacak / Beklenen davranış:**

1. Bir `Komut` arayüzü tanımla: `calistir`, `geri_al` ve komutun adı (`ad`). Kabukta en az üç komut olsun: `echo <metin>` (çıktıya yazar, geri alınamaz; bunun için geri alma yerine "geri alınamaz" hatası ver), `ekle <satir>` ve `sil <sayi>` (son satırlardan siler).
2. Bir `KomutKaydi` yaz: ad → üretici fonksiyon tablosu. Yeni komut eklemek için yalnızca kayda bir satır eklenmeli; kabuğun ayrıştırma kodu değişmemeli. (Bölüm 22.3'teki kayıt tablosunu hatırla.)
3. Kabuk bir satır okur, adını kayıttan bulur, komutu çalıştırır ve geçmişe ekler. `geri` ve `yinele` komutları geçmiş yığınlarını kullanır.
4. Hatalı girişte (bilinmeyen komut, eksik argüman) kabuk çökmeden hata mesajı yazar ve geçmişi değiştirmez.
5. Girdi olarak bir dosya ya da standart girdi alabilir; bunu bir tohum veri dosyasıyla (en az 30 satır) tekrarlanabilir biçimde test et.

**Önerilen yaklaşım (ipucu, tam çözüm değildir):** Önce yalnızca `Komut` arayüzünü ve `ekle`/`sil` komutlarını yazıp geri alma testini tamamla. Ardından kaydı ekle ve ayrıştırmayı kayıt üzerinden yap. `sil` komutunun geri alması için silinen satırı komut nesnesinde sakla; bu, Bölüm 22.11'deki `Sil` sınıfının aynısıdır. Hata durumunda geçmiş yığınına dokunmadan önce ön koşulu kontrol et. Derlemeyi WSL'de `-fsanitize=address,undefined` ile yap; ASan bellek sızıntısını da bildirir.

**Başarı kriterleri:**

- 30 satırlık tohum girdide `geri` komutlarının sayısı kadar `yinele` yapıldığında son durum, geri alma yapılmadan önceki durumla birebir aynıdır.
- Bilinmeyen komut ve eksik argüman, geçmiş yığınının boyutunu değiştirmez.
- `-Wall -Wextra` uyarısız derlenir ve ASan ile UBSan temiz çalışır.
- Yeni bir komut eklemek için `ayrıştırma` fonksiyonunda tek satır değişmez (kanıt olarak diff'i raporla).

### Proje 2 (★★★): Telemetri işleyici eklenti mimarisi (Python)

**Amaç:** EV Dashboard'a gelen telemetri satırlarını işleyen bir boru hattı kur. Hat; ayrıştırma (Factory ile türe göre işleyici), doğrulama (Strategy ile değiştirilebilir kurallar), önbellek ve süre ölçümü (Decorator), alarm aboneleri (Observer) ve dış dünya için tek bir giriş noktası (Facade) içersin.

**Yapılacak / Beklenen davranış:**

1. Satır biçimi: `TIP;ID;DEGER;ZAMAN`. Örnek: `SICAKLIK;ARAC7;23.5;1700000001`. Türler en az üç olsun: `SICAKLIK`, `NEM`, `HIZ`.
2. Ayrıştırıcılar bir fabrika tablosunda tutulsun; yeni bir tür eklemek için yalnızca yeni bir sınıf ve tek bir kayıt satırı gerekli olsun.
3. Doğrulama kuralları bir strateji olarak verilsin: aralık kuralı (ör. sıcaklık -40 ile 150 arası), tekrarlı paket kuralı (aynı ID ve ZAMAN) gibi. Kurallar çalışma zamanında seçilebilsin.
4. Ayrıştırıcı çağrısı önbelleğe alınsın ve her işlemin süresi biriktirilsin; bu iki özellik birbirinin içinde değil, sarıcılar olarak eklensin.
5. Sınır aşan bir değer (ör. sıcaklık 200) geldiğinde, kayıtlı alarm aboneleri bilgilendirilsin; abonelikten çıkma çalışsın.
6. Dış giriş noktası tek bir `isle(satir)` metodu olsun; sonuç, kabul edilen paket ya da red nedeni olsun.
7. Test verisi `random.Random(42)` ile üretilsin; en az 500 satırlık bir akış, geçersiz satırlar ve tekrarlı paketler içersin.

**Önerilen yaklaşım (ipucu, tam çözüm değildir):** Önce bir türün uçtan uca akışını (satır → ayrıştırma → doğrulama → sonuç) hiç kalıp kullanmadan yaz. Sonra her parçayı kalıba dönüştür: ayrıştırıcıları kayıt tablosuna taşı, doğrulamayı bir fonksiyon olarak ayır, önbellek ve süre sarıcılarını ekle. Her dönüşümden sonra aynı test akışını çalıştırıp çıktının değişmediğini kontrol et; bu, refactoring'in doğruluğunu kanıtlar. Aboneleri zayıf referansla tut ve bildirim sırasında kopya üzerinde gez (Bölüm 22.10).

**Başarı kriterleri:**

- Yeni bir telemetri türü eklemek, mevcut dosyalardan yalnızca kayıt tablosuna bir satır ve yeni bir sınıf gerektirir.
- Aynı tohumla üretilen akış iki kez çalıştırıldığında çıktılar birebir aynıdır.
- 500 satırlık akıştaki geçersiz satır sayısı, elle doğrulanmış bir sayıyla eşleşir; sayıyı rapora yaz.
- Önbellek isabetleri, ayrıştırıcının çağrı sayısını gerçekten azaltır; bunu bir sayaçla ölç ve raporla.
- Abonelikten çıkan bir gözlemci, çıktıktan sonra hiç bildirim almaz.

### Ek Alıştırmalar

Aşağıdaki problemler cevapsızdır. Önce kâğıt üstünde çöz, sonra kod yaz. (Mülakat) etiketli olanlar klasik mülakat sorularıdır.

1. ★ Bir sensör fabrikası, tanınmayan bir tür adı geldiğinde hata vermek yerine varsayılan bir `BilinmeyenSensor` nesnesi döndürsün. Bu tasarımın artılarını ve eksilerini yaz. Hangi kalıba yakın? (Mülakat)
2. ★ Bir HTTP isteği nesnesi için Builder yazıyorsun: başlıklar, gövde ve zaman aşımı. Doğrulamayı (ör. gövde varken `Content-Type` zorunluluğu) `build()` içinde mi yoksa her setter'da mı yapmalısın? Gerekçeni iki cümleyle yaz.
3. ★ Bölüm 22.5'teki `Yapilandirma` singleton'ını bağımlılık enjeksiyonu ile yeniden yaz. Testlerde kaç sahte nesne gerektiğini ve testlerin birbirinden bağımsız çalıştığını göster.
4. ★★ İki eski sürücü düşün: biri Fahrenheit, biri Kelvin döndürüyor. Her ikisini tek bir `Sicaklik` (celsius) arayüzüne uyarlayan adaptörler yaz. Hangisi için bir `Protocol` yeterli, hangisi için kalıtım gerekir? (Mülakat)
5. ★★ Yeniden deneme sarıcısını sabit aralık yerine üstel bekleme (backoff) ile genişlet. Bekleme süresini gerçek zaman yerine sahte bir saatle ölç. Bekleme süreleri hangi sırayla oluşur?
6. ★★ Bir fasadın doğrulama sınırını 150'den 100'e indirdiğini düşün. Fasadı kullanan istemci kodunda değişiklik gerekir mi? Hangi ilkenin bu soruya cevap verdiğini ve neden (Bölüm 21'e atıf yaparak) açıkla. (Mülakat)
7. ★★ Strateji olarak yazılmış `medyan`, çift uzunluklu pencerelerde ne döndürür? `statistics.median` ile kendi uygulamanı karşılaştır ve farkı tabloya yaz.
8. ★★ Observer'da bir gözlemci, bildirim sırasında yeni bir gözlemci ekliyor. Kopya üzerinde gezildiğinde yeni gözlemci bu bildirimi alır mı? Önce tahmin et, sonra kodla doğrula. (Mülakat)
9. ★★ Command'ın `sil` komutu, geri alma için silinen parçayı değil tüm metni saklasın. Bu iki sürümün bellek kullanımını, sekiz komutluk bir dizi için karşılaştır.
10. ★★★ State'e `ACIL_INIS` durumunu ekle. Geçişleri bir tablo olarak yaz ve durum sınıflarını değiştirmeden yeni geçişlerin eklenebildiğini göster. Bu mümkün değilse nedenini açıkla.
11. ★★★ Command ile Observer'ı birlikte kullan: geri alma sırasında gözlemcilere `geri` olayı bildiriliyor. Bir gözlemci bu sırada hata verirse durum tutarlı kalır mı? Bunu bir test ile göster ve düzeltmeyi tasarla.
12. ★★★ Bir veritabanı bağlantı havuzu için Factory, Builder ve Singleton'dan hangisini seçerdin? Her biri için bir cümlelik gerekçe yaz ve hangisinin test edilebilirliği için en çok yardımcı olduğunu açıkla. (Mülakat)

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak kodu okuyacaksın: CPython 3.12.10 kaynağındaki `Lib/logging/__init__.py` dosyası, `Logger` sınıfının `callHandlers` metodu. Kaynak `https://raw.githubusercontent.com/python/cpython/v3.12.10/Lib/logging/__init__.py` adresinden indirildi; aşağıdaki metin dosyanın 1746-1774. satırlarıdır ve fonksiyonun tamamıdır (kısaltma yoktur; docstring dahil). Tek fark biçimseldir: sınıf gövdesinin 4 boşluk girintisi kaldırıldı ve 70 karakter sınırına uymak için tek satırlık `elif` koşulu iki satıra bölündü. Anlamı değiştirmez.

```python
def callHandlers(self, record):
    """
    Pass a record to all relevant handlers.

    Loop through all handlers for this logger and its parents in the
    logger hierarchy. If no handler was found, output a one-off error
    message to sys.stderr. Stop searching up the hierarchy whenever a
    logger with the "propagate" attribute set to zero is found - that
    will be the last logger whose handlers are called.
    """
    c = self
    found = 0
    while c:
        for hdlr in c.handlers:
            found = found + 1
            if record.levelno >= hdlr.level:
                hdlr.handle(record)
        if not c.propagate:
            c = None    #break out
        else:
            c = c.parent
    if (found == 0):
        if lastResort:
            if record.levelno >= lastResort.level:
                lastResort.handle(record)
        elif raiseExceptions and \
                not self.manager.emittedNoHandlerWarning:
            sys.stderr.write("No handlers could be found for logger"
                             " \"%s\"\n" % self.name)
            self.manager.emittedNoHandlerWarning = True
```

**Sorular — cevaplamadan geçme:**

1. `c = self` ile başlayan `while c:` döngüsü, kayıt hangi nesneler arasında yukarı taşınır? `c = c.parent` satırı bu hiyerarşiyi nasıl kurar? Bir günlükleyicinin `parent` alanını bu koddan başka nerede belirleyeceğini düşün.
2. `if not c.propagate:` dalı ne zaman çalışır ve `c = None` yazmak neden döngüyü bitirir? `propagate` `False` olan bir günlükleyicinin üstündeki işleyicileri neden atladığını kendi kelimelerinle açıkla.
3. `found` sayacı neden her işleyicide artırılır, ama işleyicinin `level` kontrolünden önce artırılır? Bu, "bu kayıt hiçbir işleyiciye ulaşmadı" ile "ulaştı ama seviyesi yetmedi" durumlarını nasıl ayırır?
4. `found == 0` dalındaki `lastResort` ne zaman kullanılır? Bu dal, bir günlükleyicinin hiç işleyicisi yoksa neyin yerine geçer?
5. Bu kodu Observer açısından oku: `Logger` konu gibi, işleyiciler gözlemci gibi görünüyor. Bu benzetmenin nerede bozulduğunu yaz: abonelik kavramı var mı? Hangi noktada bir işleyici bir sonrakini çağırmaz, hiyerarşi ise yukarı çıkar? Bu, Observer'dan çok hangi kalıba yakındır?
6. (Mülakat) `hdlr.handle(record)` çağrısı, Bölüm 22.10'daki `Konu.bildir` ile karşılaştırıldığında hangi farkı gösterir? Bildirim sırasında bir işleyici yeni bir işleyici eklerse ne olur ve bu koddaki liste üzerinde gezme ile Bölüm 22.10'daki kopya üzerinde gezme nasıl farklı sonuç verir? Kaynakta `c.handlers` listesinin eşzamanlılık kilidiyle (lock) korunup korunmadığını da kontrol et.

## Bölüm Özeti

Bu bölümde kalıpları bir ezber listesi değil, tekrar eden tasarım sorunlarına verilmiş adlandırılmış cevaplar olarak gördük:

- Kalıp bir kod parçası değil, bir takas (trade-off) biçimidir; kalıp avcılığı, kalıbı sorun yokken uygulamanın zararlı alışkanlığıdır.
- Factory, nesne türünü çalışma zamanında seçer ve kayıt tablosuyla yeni türleri mevcut kodu değiştirmeden ekler.
- Builder, çok parametreli nesneleri adım adım kurar; Python'da anahtar kelime argümanları çoğu durumda bu ihtiyacı karşılar.
- Singleton, tek örnek ihtiyacını gizli global duruma çevirir; testleri bozar. Önce bağımlılık enjeksiyonunu dene.
- Adapter, uyumsuz arayüzü hedef arayüze sararak dönüşümü tek bir yerde toplar; Decorator aynı arayüzü koruyarak davranışı zincirleyerek ekler.
- Facade, karmaşık bir alt sisteme sade bir kapı açar; Strategy, bir algoritmayı değiştirilebilir biçimde dışarıdan verir.
- Observer, değişimi abonelere bildirir; zayıf referans bellek sızıntısını, kopya üzerinde gezme ise yeniden giriş hatasını önler.
- Command, eylemi nesne yapar ve geri al/yinele yığınlarını mümkün kılar; MertOS'un komut tablosu bu fikrin bir başlangıcıdır.
- State, durum-bağımlı davranışı durum nesnelerine dağıtır; geçersiz geçişler reddedilir ve durum değişmez.
- Kalıplar birlikte çalışır; ama her birleşim bir dolaylama katmanı ekler. Seçimi bir sorunun belirtisine göre yap ve önce en basit çözümle başla.

**Sonraki bölümde:** Bölüm 23 (Clean Code) ile bu kısmın son bölümüne geçiyoruz. Bu bölümde kalıpları adlandırırken ve sınıf sorumluluklarını ayırırken kullandığın kararların, kodun okunabilirliğiyle nasıl ilişkili olduğunu göreceksin. Kalıpların gerçek değerinin, kodu anlaşılır kılmakta yattığını da orada tartışacağız.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. Factory ile Builder arasındaki fark nedir? Hangi durumda birini diğerine tercih edersin ve neden?
2. Python'da Singleton yazmanın neden çoğu zaman gereksiz olduğunu açıkla. Bir modül tekil nesnesi ile sınıf tabanlı tekil nesne arasındaki fark nedir?
3. Adapter ile Decorator'ın ikisi de bir nesneyi sarar. Bu iki kalıp arasındaki temel farkı, arayüzün korunup korunmadığı ve amaç açısından açıkla.
4. Observer'da bildirim sırasında bir gözlemcinin kendini abonelikten çıkarması neden tehlikelidir? Bu sorunu iki yoldan çöz ve aralarındaki farkı söyle.
5. Command'ın geri alma yığınında bir komutun geri alınması, sonraki komutların geri alınmasını nasıl etkiler? Bu bağımlılığı yönetmek için hangi kurala uyman gerekir?
6. State kalıbı ile `if` zinciri arasında bir geçişin doğruluğunu test etmek açısından hangisi daha kolaydır? Bunu tüm durum-olay çiftlerini kapsayan bir test tasarlayarak göster.
7. Bir kalıbın "fazla mühendislik" olduğunu nasıl anlarsın? Bu bölümdeki örneklerden birini seçip kalıpsız hâlinin ne zaman yeterli olacağını tartış.
8. Strategy ile State ikisi de davranışı değiştirir. Hangi durumda birini, hangi durumda diğerini seçersin? Karar kriterini iki cümleyle yaz.
:::
