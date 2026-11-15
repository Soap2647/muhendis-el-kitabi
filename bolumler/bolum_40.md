%% kisim_no: X
%% kisim_ad: Yazılım Mühendisliği Pratiği
%% bolum_no: 40
%% baslik: API Tasarımı

## Giriş: Bir arayüz, bir sözleşmedir

Her yazılım bir yerde bir başkasıyla konuşur. Bir fonksiyon çağıran kodla, bir sunucu istemciyle, bir sürücü çekirdekle, bir sensör ana kartla konuşur. Bu konuşmanın kuralları (hangi girdinin kabul edildiği, hangi çıktının döndüğü, hata durumunda ne olduğu ve hangi yan etkinin beklendiği) bir **API**'yi (Application Programming Interface, uygulama programlama arayüzü) oluşturur. API'yi kullanan taraf onun içini görmez; yalnızca sözleşmeye bakar.

Bu bölümün başlığı "API tasarımı" olsa da asıl konu tasarlamanın sonuçlarıdır. Yayımlanmış bir API'yi değiştirmek yalnızca kodu değiştirmek değildir: onu kullanan her program, her ekip ve her cihaz kırılabilir. Bu yüzden iyi API tasarımı, kodu yazmadan önce sözleşmeyi düşünmekle başlar. Bölüm 21'de arayüze bağımlılığın değişim maliyetini gördün; bu bölümde aynı düşünceyi bir kütüphanenin, bir web servisinin ve bir uçuş filosu yönetim sisteminin sözleşmesine uygulayacağız.

Savunma sanayiinde bu konu ayrıca ağırlık taşır. Bir yer istasyonu yazılımı, bir İHA'nın telemetri ve komut arayüzünü yıllarca kullanabilir; bu süre içinde yazılımın parçaları farklı ekipler tarafından değiştirilir. Eski bir istemcinin yeni bir sunucuyla konuşabilmesi, bir sürücünün eski bir kütüphaneyle yeniden derlenmeden çalışabilmesi tesadüf değildir; bir tasarım kararının sonucudur.

Bölümü üç katmanda ilerleteceğiz. Önce kütüphane API'sini ele alacağız: C ve Python'da adlandırma, sahiplik, hata bildirimi, opak işaretçiler ve ABI. Sonra ağ API'sini, yani REST'i: kaynaklar, yöntemler, durum kodları, sayfalama, güvenli yeniden deneme ve hız sınırı. Son olarak sürümleme, şema ve sözleşme testi ile RPC ve GraphQL gibi alternatifleri göreceğiz. Bölümün sonunda gerçek bir İHA filo API'sini sıfırdan yazıp `urllib` ile gerçek isteklerle sınayacağız.

Bölüm 30'daki HTTP bilgisini tekrar etmeyeceğiz; yöntemleri, durum kodu sınıflarını ve başlıkların işlevini orada gördün. Burada o bilgiyi tasarım kararlarına çeviriyoruz.

::: not
Bu bölümdeki her çıktı, bölüm yazılırken kitabın kendi kodu çalıştırılarak alındı. Kodlar `Temp\b40` altında yazıldı ve arşivde `arsiv\kod\b40` altında da bulunur. Ağ örnekleri yalnızca 127.0.0.1 üzerinde çalışır; hiçbir dış sisteme istek gönderilmez. C örnekleri WSL2 içinde Ubuntu 24.04 ve gcc 13.3 ile derlendi.
:::

## 40.1 API nedir ve iyi bir API nasıl görünür?

API'yi üç büyük sınıfa ayırabiliriz. **Kütüphane API'si**, aynı süreç içinde yapılan bir fonksiyon çağrısıdır: `fopen`, `json.dumps`, bir matematik kütüphanesinin `sin` fonksiyonu. **Ağ API'si**, iki süreç arasında istek ve yanıt alışverişidir: bir HTTP servisi, bir gRPC uç noktası. **Donanım ya da sürücü API'si**, yazılımla aygıt arasındaki sözleşmedir: Linux'ta `write` ve `ioctl` çağrıları, bir mikrodenetleyicide HAL fonksiyonları. Üçü de aynı soruyu sorar: karşı taraf ne bekliyor ve ne döndürecek?

![Şekil 40.1: Üç API türü. Her biri farklı bir ortamda çalışır, ama üçü de girdi, çıktı, hata ve yan etki sözleşmesi taşır.](gorseller/b40_api_turleri.png)

İyi bir API'nin özelliklerini altı başlıkta toplayabiliriz. Bu özellikler birbiriyle çelişebilir; tasarımın işi bu gerilimleri yönetmektir.

- **Öğrenmesi kolay:** İlk denemede doğru çalışan en küçük kullanım, dokümantasyona bakmadan anlaşılmalı.
- **Yanlış kullanımı zor:** Hatayı yapmak kolay olmamalı; yapıldığında da fark edilir olmalı. `sensor_olustur` başarısızlıkta `NULL` döner, `sensor_yok_et(NULL)` güvenlidir ve yanlış kullanımın bedeli derleme ya da çalışma anında görünür.
- **Tutarlı:** Aynı kavram her yerde aynı adla ve benzer parametre sırasıyla gelmeli.
- **En az şaşırtma:** Adı "oku" olan bir fonksiyon yazma yapmamalı; bir hata kodu, bir başarı gibi görünmemeli.
- **Minimal:** Bir fonksiyon eklemek kolaydır, kaldırmak neredeyse imkânsızdır. Her yeni öğe, sözleşmenin sonsuza kadar sürecek bir parçasıdır.
- **Belgeli ve sınanabilir:** Örnekleri çalışan kod olan bir API, dokümantasyonu güncel kalan API'dir. Bunu Bölüm 40.9'da ele alacağız.

API tasarımında kullanılan güzel bir kavram **sözleşme tabanlı tasarımdır** (design by contract; genel bilgi). Bir fonksiyon için üç şey yazılır: **ön koşul** (çağıran neyi sağlamak zorunda), **son koşul** (fonksiyon bittiğinde neyin doğru olacağı) ve **değişmezler** (işlemler boyunca değişmeyen şeyler). Sözleşme bu üçünü kayıt altına alır. Kayıt altına alınmayan kısım, kullanıcıların tahmin ettiği kısımdır ve tahminler farklı olunca hatalar başlar.

Bir gözlem daha vardır ve bunu "Hyrum yasası" diye anarız (genel bilgi): Yeterince çok kullanılan bir API'nin **her gözlemlenebilir davranışı**, birileri tarafından bir bağımlılığa dönüşür. Fonksiyonun hata mesajının metni, sıralama düzeni, hatta yanıtın alan sırası bile bir gün birinin kodunda bir koşula dönüşebilir. Bu yüzden bir API'de "gözlemlenebilir" ne kadar çoksa, değiştirilmesi o kadar pahalıdır.

## 40.2 Kütüphane API'si: C ve Python'da tasarım

Bir kütüphane API'si tasarlarken ilk karar adlandırmadır. Adlar, kullanıcının aklındaki modelle kodun modeli arasında köprü kurar. Bu bölümdeki C kütüphanesinde her ad aynı önekle başlar (`sensor_`), oluşturma ve yok etme çiftleri `olustur` ve `yok_et` ile, değer okuma ve yazma `oku` ve `kaydet` ile adlandırılır. Bu düzen tahmin edilebilirdir: `sensor_` yazıp sekmeye bastığında derleyici ve sen aynı listeyi görürsün.

Parametre sırasında da bir kural vardır: sahibi olan nesne önce, dışarıya yazılan değer sona gelir. Standart kütüphanedeki `memcpy(hedef, kaynak, n)` bu kuralın bilinen bir istisnasıdır; yine de yeni bir API'de tutarlılık için bu düzeni seçmek iyidir. Girdi yalnızca okunuyorsa `const` ile işaretlenir; bu bir yorum değildir, derleyicinin denetlediği bir sözleşmedir. Bölüm 2'de işaretçilerin neyi gösterdiğini gördün; bir fonksiyonun bir işaretçiyi değiştirmeyeceğini `const` ile ilan etmek, o işaretçinin arkasındaki veriye dokunmayacağını söyler.

### Opak işaretçi: yapıyı gizlemek

Bir kütüphanenin kullanıcıya en çok değer kaybettirdiği yer, iç yapısını açmasıdır. Bir `struct` başlık dosyasında açıksa, kullanıcı alanlarına erişir, `sizeof` ile boyutunu hesaplar ve bir gün yapı değiştiğinde kodu kırılır. Bu yüzden C'de sık kullanılan çözüm **opak işaretçi**dir: başlık yalnızca yapının adını bilir, yapının içeriği ise kaynak dosyada gizlidir.

`sensor.h` dosyası bu sözleşmenin tamamını taşır:

```c
/* sensor.h: Sensor kutuphanesinin genel arayuzu. */
#ifndef SENSOR_H
#define SENSOR_H

/* opak: yapisini yalnizca sensor.c bilir */
typedef struct sensor sensor_t;

typedef enum {
    SENSOR_OK     = 0,   /* basarili */
    SENSOR_EARG   = -1,  /* gecersiz argum (NULL, bos ad) */
    SENSOR_ERANGE = -2   /* deger aralik disi */
} sensor_durum;

/* Sahiplik: donen isaretci cagirana aittir; sensor_yok_et
   ile serbest birakilir. Basarisizlikta NULL doner. */
sensor_t *sensor_olustur(const char *ad);
void sensor_yok_et(sensor_t *s);  /* NULL: hicbir sey yapmaz */

sensor_durum sensor_kaydet(sensor_t *s, double deger);
sensor_durum sensor_oku(const sensor_t *s, double *cikis);

const char *sensor_durum_metni(sensor_durum d);

#endif
```

`typedef struct sensor sensor_t;` satırı, `sensor_t` adını tanıtır ama yapının alanlarını vermez. Yapının kendisi yalnızca `sensor.c` içindedir:

```c
/* sensor.c: sensor.h arayuzunun gerceklemesi. */
#include <stdlib.h>
#include <string.h>
#include "sensor.h"

/* Yapi disariya kapali: kullanici bunu goremez. */
struct sensor {
    char   ad[32];
    double son;
    int    kayit_sayisi;
};

sensor_t *sensor_olustur(const char *ad)
{
    sensor_t *s;

    if (ad == NULL || ad[0] == '\0')
        return NULL;
    s = malloc(sizeof *s);
    if (s == NULL)
        return NULL;
    strncpy(s->ad, ad, sizeof s->ad - 1);
    s->ad[sizeof s->ad - 1] = '\0';
    s->son = 0.0;
    s->kayit_sayisi = 0;
    return s;
}

```

Burada `struct sensor` gövdesi, `sensor_olustur` ve `sensor_yok_et` yalnızca bu dosyada görünür. Kullanıcı `sensor_t *` işaretçisini tutabilir, geçirebilir ve yalnızca API fonksiyonlarıyla kullanabilir. Yapının yerleşimi ileride değişse bile kullanıcı kodu aynı kalır, çünkü kullanıcı yerleşimi bilmez.

```c
void sensor_yok_et(sensor_t *s)
{
    free(s);                /* free(NULL) tanimli, guvenli */
}

sensor_durum sensor_kaydet(sensor_t *s, double deger)
{
    if (s == NULL)
        return SENSOR_EARG;
    if (deger < -100.0 || deger > 100.0)
        return SENSOR_ERANGE;
    s->son = deger;
    s->kayit_sayisi++;
    return SENSOR_OK;
}

sensor_durum sensor_oku(const sensor_t *s, double *cikis)
{
    if (s == NULL || cikis == NULL)
        return SENSOR_EARG;
    *cikis = s->son;
    return SENSOR_OK;
}

```

Son parça, durum kodunu metne çeviren yardımcıdır. Yapının her alanı yalnızca bu dosyada değiştirilebildiği için, kayıt sayısı gibi iç ayrıntılar da burada güvenle tutulabilir.

```c
const char *sensor_durum_metni(sensor_durum d)
{
    switch (d) {
    case SENSOR_OK:     return "tamam";
    case SENSOR_EARG:   return "gecersiz argum";
    case SENSOR_ERANGE: return "aralik disi";
    }
    return "bilinmeyen";
}
```

Opak bir tipin gücünü görmek için kullanıcı tarafına geçelim. `sensor_main.c` yalnızca başlığı içerir ve API üzerinden konuşur:

```c
/* sensor_main.c: API'yi kullanan istemci. Yapiyi goremez. */
#include <stdio.h>
#include "sensor.h"

int main(void)
{
    sensor_t *s = sensor_olustur("EV-batarya");
    double v = -1.0;
    sensor_durum d;

    if (s == NULL) {
        puts("olusturulamadi");
        return 1;
    }
    d = sensor_kaydet(s, 23.5);
    printf("kaydet 23.5 -> %s\n", sensor_durum_metni(d));
    d = sensor_kaydet(s, 500.0);
    printf("kaydet 500  -> %s\n", sensor_durum_metni(d));
    d = sensor_oku(s, &v);
    printf("oku         -> %s, v=%.1f\n", sensor_durum_metni(d), v);
    d = sensor_oku(NULL, &v);
    printf("NULL oku    -> %s\n", sensor_durum_metni(d));

    sensor_yok_et(s);
    sensor_yok_et(NULL);
    s = NULL;               /* serbest birakilan isaretciyi sifirla */
    return 0;
}
```

Programı WSL2 içinde derleyip çalıştırdığımızda çıktı şöyledir:

```term
$ gcc -std=c11 -O2 -Wall -Wextra -o sensor_main sensor.c sensor_main.c
$ ./sensor_main
kaydet 23.5 -> tamam
kaydet 500  -> aralik disi
oku         -> tamam, v=23.5
NULL oku    -> gecersiz argum
```

Çıktıdaki `NULL oku -> gecersiz argum` satırı, API'nin kendi hata kodunu nasıl döndürdüğünü gösterir: çağıran tarafı çökmeden durumu öğrenir. `aralik disi` satırı ise hatanın nerede tespit edildiğini söyler; kayıt kabul edilmedi ve yapının durumu değişmedi. Bu iki davranışı da sözleşmenin parçası olarak kabul etmeliyiz.

Opak yapının gerçek bir sınır olduğunu görmek için kullanıcı tarafında yapıya doğrudan erişmeyi deneyelim. `hata_opak.c` dosyası bunu yapar:

```c
/* hata_opak.c: Opak tipin yapisina erismek derleme hatasidir. */
#include "sensor.h"

double yapiya_bak(sensor_t *s)
{
    return s->son;      /* yapi tanimsiz: derlenmez */
}
```

gcc 13.3 bu dosyayı derlemeyi reddeder. Tanı mesajının ilk satırı şöyledir: `hata_opak.c:6:13: error: invalid use of incomplete typedef ‘sensor_t’ {aka ‘struct sensor’}`. "Tamamlanmamış tip" (incomplete type) ifadesi kilit kelimedir: derleyici yapının alanlarını bilmediği için `s->son` ifadesini anlamlandıramaz. Bu derleme hatası, sözleşmenin zorlandığı yerdir.

Bir uyarı gerekli. Standart C, `FILE` tipinin içeriğini tanımlamaz; `FILE` da bir opak tiptir. glibc ise `struct _IO_FILE` yapısını `bits/types/struct_FILE.h` başlık dosyasında açık tutar. Bu bir uygulama ayrıntısıdır; standart bunu taahhüt etmez. Kodun `f->_flags` gibi alanlara bağlanması taşınabilirliği bozar ve bir glibc sürümünde çalışan kod başka bir C kütüphanesinde derlenmeyebilir. Doğru yol, `FILE` yapısına hiç dokunmadan yalnızca `fopen`, `fclose` gibi fonksiyonları kullanmaktır. Bölüm 2'deki dosya G/Ç akışında bunu zaten yaptın.

### Sahiplik ve ömür: kim serbest bırakır?

C'de bellek yönetimi sahiplik sorusuna bağlıdır: bir işaretçiyi kim ayırdı ve kim serbest bırakacak? Bölüm 2'de `fopen` ile açılan dosyanın `fclose` ile kapatılması gerektiğini gördün. Aynı kural her kütüphane fonksiyonu için yazılmalıdır ve başlık dosyasında açıkça belirtilmelidir. Bizim `sensor.h` dosyasında bu bir yorum satırıyla yapılır: "Sahiplik: donen isaretci cagirana aittir".

| Fonksiyon | Bellek kimin? | Ne zaman geçerli? | Hata |
|---|---|---|---|
| `sensor_olustur` | Kütüphane ayırır, çağıran `sensor_yok_et` ile bırakır | Bırakılana kadar | `NULL` döner |
| `sensor_yok_et` | Çağıran verir, kütüphane serbest bırakır | Çağrıdan sonra geçersiz | `NULL` ise hiçbir şey yapmaz |
| `sensor_kaydet` | Ödünç (borrow); yalnızca `s` okunur | Çağrı süresince | Kod döner |
| `sensor_oku` | `cikis` çağıranın, kütüphane yalnızca yazar | Çağrı süresince | Kod döner |

Sahiplik tablosunun en çok hata üreten satırı `sensor_yok_et`'tir. Serbest bırakılmış bir işaretçiyi tekrar kullanmak (use-after-free) ve aynı işaretçiyi iki kez serbest bırakmak (double free) C'de **tanımsız davranış**tır (UB). Tipik olarak program çöker ya da bellek bozulur; ama bunun garanti olduğu söylenemez. Bu yüzden `sensor_main.c` içinde serbest bırakıldıktan sonra işaretçiyi `NULL` yapıyoruz. Bu alışkanlık, aynı işaretçinin yanlışlıkla ikinci kez kullanılmasının çoğu zaman bir çökme yerine erken bir kontrol hatası üretmesini sağlar.

### Hata bildirimi: dört yol

C'de hatayı bildirmenin dört yaygın yolu vardır ve her birinin bir bedeli vardır.

| Yol | Örnek | Güçlü yan | Zayıf yan |
|---|---|---|---|
| Dönüş kodu | `sensor_durum` | Açık, her çağrıda denetlenebilir | Çağıran unutursa hata sessizce kaybolur |
| `errno` | `open` ve `read` | POSIX'te standart | Genel durum; çağrı sonrası hemen okunmazsa değişir |
| İstisna | C++, Python | Hata akışı ayrılır | C'de yoktur |
| Sonuç türü | Rust `Result` | Derleyici kontrolü zorlar | C'de elle taklit edilir |

Biz üçüncü adımda, yani dönüş kodunu bir `enum` ile birlikte veriyi bir çıkış parametresi olarak döndürmeyi seçtik. Böylece `sensor_oku` hem durumu hem değeri döndürür ve değer yalnızca başarıda anlamlıdır. Eski tasarımlarda bir fonksiyonun hem değer hem hata taşıması, mesela `-1`'in ya da `NAN`'ın hem geçerli bir sonuç hem de hata olarak kullanılması yaygın bir hata kaynağıdır. Dönüş değerini hatalara ayırmak bu karışıklığı önler.

### Python'da hata modeli ve anahtar kelime argümanları

Python'da hata bildirimi istisnalarla yapılır. Bu, bir kütüphane tasarlarken iki karar gerektirir: tüm hataların ortak bir kökü olsun mu, ve parametrelerin hangileri konumsal, hangileri yalnızca anahtar kelime olsun mu? Aşağıdaki kod sensör kütüphanesinin Python sürümünün hata sınıflarını ve bir fonksiyonun imzasını gösterir.

```python
# -*- coding: utf-8 -*-
"""b40_2_py_api.py: Hata modeli ve anahtar kelime argumanlari."""


class SensorHatasi(Exception):
    """Bu kutuphanenin tum hatalarinin koku."""


class ArgumanHatasi(SensorHatasi):
    """Cagiran yanlis deger verdi; ayni cagri yeniden denenmez."""


class AralikHatasi(SensorHatasi):
    """Deger kabul edilebilir aralikta degil."""


def kaydet(ad, deger, *, birim="C", tavan=100.0):
    """Degeri kaydeder. birim ve tavan yalnizca anahtar kelimedir."""
    if not ad:
        raise ArgumanHatasi("ad bos olamaz")
    if birim not in ("C", "F"):
        raise ArgumanHatasi("birim C ya da F olmali: %r" % birim)
    if not -tavan <= deger <= tavan:
        raise AralikHatasi(
            "%s: %.1f, aralik [-%g, %g]" % (ad, deger, tavan, tavan)
        )
    return {"ad": ad, "deger": deger, "birim": birim}

```

Burada `SensorHatasi` tüm hataların köküdür. Çağıran `except SensorHatasi` yazarak kütüphanenin herhangi bir hatasını yakalayabilir; daha ince ayrım isteyen `ArgumanHatasi` ile `AralikHatasi` alt sınıflarını yakalar. Yakalanan istisnanın türü de bir sözleşmedir: alt sınıf adı değiştirilirse, o adı kullanan kod kırılır.

```python

if __name__ == "__main__":
    print(kaydet("EV-batarya", 23.5))
    print(kaydet("EV-batarya", 23.5, birim="F"))
    cagrilar = [
        lambda: kaydet("", 1.0),
        lambda: kaydet("x", 500.0),
        lambda: kaydet("x", 1.0, "C"),
    ]
    for cagri in cagrilar:
        try:
            cagri()
        except SensorHatasi as e:  # alt siniflarin hepsini yakalar
            print(type(e).__name__, "-", e)
        except TypeError as e:
            print("TypeError -", e)
```

İmzadaki `*` işareti, ondan sonra gelen parametrelerin yalnızca anahtar kelimeyle verilebileceğini söyler. `birim` ve `tavan` böyle tanımlandı. Yarın `kaydet`'e yeni bir `zaman_damgasi` parametresi eklersek, mevcut çağrılar bozulmaz; çünkü onlar bu parametreleri adıyla vermiyor. Konumsal parametre eklemek ise tüm çağrıları kırar. Bu tasarım fikri, Python standart kütüphanesinde de sık görülür.

Programın çıktısı, hata sınıflarının hiyerarşisini ve konumsal argüman hatasını gösterir:

```term
$ python b40_2_py_api.py
{'ad': 'EV-batarya', 'deger': 23.5, 'birim': 'C'}
{'ad': 'EV-batarya', 'deger': 23.5, 'birim': 'F'}
ArgumanHatasi - ad bos olamaz
AralikHatasi - x: 500.0, aralik [-100, 100]
TypeError - kaydet() takes 2 positional arguments but 3 were given
```

Son satır bir `TypeError`'dır. Python 3.12'de bu mesaj `kaydet() takes 2 positional arguments but 3 were given` biçimindedir. Yani anahtar kelime olarak tanımlanmış parametreyi konumsal vermek, istisna yakalama bloğuna düşmez; çağrı hiç başlamadan reddedilir. Bu, API'nin "yanlış kullanımı zor" olması ilkesinin Python'daki karşılığıdır.

## 40.3 ABI: API'yi kırmadan değiştirmek

Kaynak düzeyinde bir API, derleyicinin gördüğü şeydir: fonksiyon adları, parametre türleri, sabitler. **ABI** (Application Binary Interface, uygulama ikili arayüzü) ise derlenmiş ikili dosyanın gördüğü şeydir: fonksiyon sembol adları, çağrı kuralları, veri türlerinin bellekteki boyutu ve hizalaması, yapı alanlarının ofsetleri. Bir kaynak kodu yeniden derlemek API'yi değil ABI'yi de yeniler; ama paylaşımlı bir kütüphaneyi yeniden derlemek, onu kullanan ikili dosyaları yeniden derlemeyi gerektirmez. İşte bu fark, ABI kırılmasının tehlikesini doğurur.

En sık ABI kırılması, bir yapıya yeni alan eklemekten gelir. Gösterelim. Bir sensör ölçümünü tutan `struct olcum` ilk sürümde iki alanlıdır: bir `id` ve bir `deger`. İkinci sürümde ise bir `durum` alanı eklenir. Başlık dosyasında tek bir `#ifdef` ile iki sürümü aynı dosyada tutuyoruz:

```c
/* olcum.h: Paylasimli kutuphanenin baslik dosyasi. */
#ifndef OLCUM_H
#define OLCUM_H

struct olcum {
    int    id;
    double deger;
#ifdef OLCUM_V2
    int    durum;           /* v2'de eklendi: yapinin sonuna */
#endif
};

int  olcum_yapi_boyutu(void);  /* kutuphanenin gordugu sizeof */
void olcum_guncelle(struct olcum *o, double d);

#endif
```

Kütüphanenin gerçekleştirmesi, `olcum_yapi_boyutu` fonksiyonunu içerir. Bu fonksiyon kritik bir tasarım kararıdır: yapının boyutunu kütüphane kendi derlendiği haliyle döndürür.

```c
/* olcum_lib.c: Kutuphane gerceklemesi. -DOLCUM_V2 ile v2 derlenir. */
#include "olcum.h"

int olcum_yapi_boyutu(void)
{
    return (int)sizeof(struct olcum);
}

void olcum_guncelle(struct olcum *o, double d)
{
    o->deger = d;
#ifdef OLCUM_V2
    o->durum = d > 50.0;        /* v2 davranisi: esik uzerinde 1 */
#endif
}
```

Eski istemci ise v1 başlığıyla derlenmiştir ve boyutunu kendi `sizeof` ile hesaplar. Çalıştırmadan önce iki boyutu karşılaştırır. Bu karşılaştırma, ABI uyumsuzluğunu sessiz bir bellek bozulması yerine açık bir hataya çevirir:

```c
/* istemci.c: v1 basligiyla derlenmis eski istemci. */
#include <stdio.h>
#include "olcum.h"

int main(void)
{
    struct olcum o = {7, 0.0};
    int kutuphane = olcum_yapi_boyutu();
    int yerel = (int)sizeof o;
    printf("istemci sizeof=%d kutuphane=%d\n", yerel, kutuphane);
    if (kutuphane != yerel) {
        puts("uyumsuz: calistirma durduruldu");
        return 2;
    }
    olcum_guncelle(&o, 42.0);
    printf("id=%d deger=%.1f\n", o.id, o.deger);
    return 0;
}
```

Deneyi üç adımda yapıyoruz. Önce v1 kütüphanesini derleyip eski istemciyle çalıştırırız. Sonra **aynı istemci ikili dosyasını yeniden derlemeden**, v2 kütüphanesini aynı dosya adıyla (`libolcum.so`) yeniden üretip çalıştırırız. Son olarak istemcinin boyut kontrolü olmadan yazılmış bir sürümünü ASan ile sınarız.

Önce bir ara bilgi. **AddressSanitizer** (ASan), derleme sırasında bellek erişimlerinin yanına denetim kodu ekleyen bir araçtır; yığındaki değişkenlerin etrafına "kırmızı bölgeler" koyar ve bu bölgelere yazılırsa hatayı bildirir. Bölüm 32.8'de fuzzing ile birlikte bu aracı görmüştün. Burada aracı, bir ABI kırılmasının çalışma zamanında nasıl göründüğünü yakalamak için kullanıyoruz. `-fsanitize=address` bayrağı hem derlemede hem bağlamada verilmelidir.

Şimdi kurulum. Paylaşımlı kütüphane `-fPIC -shared` ile derlenir; istemci ise `-L. -lolcum` ile ona bağlanır ve `LD_LIBRARY_PATH=.` ile çalışma anında bulunur. Birinci senaryo v1 kütüphanesiyle:

```term
$ gcc -std=c11 -Wall -Wextra -shared -fPIC -o libolcum.so olcum_lib.c
$ gcc -std=c11 -Wall -Wextra -o istemci istemci.c -L. -lolcum
$ LD_LIBRARY_PATH=. ./istemci
istemci sizeof=16 kutuphane=16
id=7 deger=42.0
```

Her şey tutarlı: istemci de kütüphane de 16 bayt bekliyor. İkinci senaryoda aynı `istemci` dosyası çalıştırılır, ama bu kez `libolcum.so` v2 olarak yeniden üretilmiştir (`-DOLCUM_V2`):

```term
$ gcc -std=c11 -Wall -Wextra -DOLCUM_V2 \
    -shared -fPIC -o libolcum.so olcum_lib.c
$ LD_LIBRARY_PATH=. ./istemci; echo EXIT=$?
istemci sizeof=16 kutuphane=24
uyumsuz: calistirma durduruldu
EXIT=2
```

Bu kez istemci hatayı kendi kontrolüyle yakalayıp çıkıyor (çıkış kodu 2). Kontrol olmasaydı ne olurdu? Üçüncü senaryo bunu gösterir. `istemci_saf.c` boyut kontrolü yapmadan doğrudan `olcum_guncelle` çağırır:

```c
/* istemci_saf.c: Boyut kontrolu YOK. Yalnizca ASan ile sinanir. */
#include <stdio.h>
#include "olcum.h"

int main(void)
{
    struct olcum o = {7, 0.0};
    olcum_guncelle(&o, 42.0);
    printf("id=%d deger=%.1f\n", o.id, o.deger);
    return 0;
}
```

Bu dosya v2 kütüphanesine ASan ile bağlanır (kütüphane de ASan ile derlenmiştir, yoksa kütüphanedeki yazma denetlenmez):

```term
$ gcc -std=c11 -g -O0 -fsanitize=address -DOLCUM_V2 \
    -shared -fPIC -o libolcum_asan.so olcum_lib.c
$ gcc -std=c11 -g -O0 -fsanitize=address \
    -o saf istemci_saf.c -L. -lolcum_asan
$ LD_LIBRARY_PATH=. ./saf 2>&1 \
    | grep -E 'ERROR: |WRITE of|    #[01] ' | head -4
==PID==ERROR: AddressSanitizer: stack-buffer-overflow
WRITE of size 4 at 0xADR thread T0
    #0 0xADR in olcum_guncelle olcum_lib.c:13
    #1 0xADR in main istemci_saf.c:8
```

Rapor, kütüphanenin 13. satırında (`o->durum = d > 50.0;`) 4 baytlık bir yazmanın, yığındaki 16 baytlık `o` nesnesinin dışına taştığını söyler. Yazma, v1 başlığıyla derlenmiş istemcinin ayırdığı alanın dışındadır. Adresler (0xADR) ve süreç numarası (PID) sabit yer tutucularla değiştirildi; gerisi aynıdır.

Bu durumda tanımsız davranışı doğru adlandırmalıyız. Yığın taşması C'de tanımsız davranıştır: tipik olarak komşu değişkenin üzerine yazılır, bazen hiçbir şey görülmez, bazen program çöker. Hangisinin olacağı garanti değildir; "çalıştığını gördüm" bu yüzden kanıt değildir. ASan'ın bulduğu şey, aynı kodun başka bir derleyicide ya da başka bir yığın düzeninde sessizce "çalışabileceğidir".

Yapıların düzenini doğrudan görmek için son bir program yazıyoruz. Aynı başlık dosyasını iki kez derleyip `offsetof` ile alan ofsetlerini ve `sizeof` ile boyutu yazdırıyoruz:

```c
#include <stdio.h>
#include <stddef.h>
#include "olcum.h"
int main(void) {
    printf("sizeof=%zu id@%zu deger@%zu\n", sizeof(struct olcum),
           offsetof(struct olcum, id), offsetof(struct olcum, deger));
#ifdef OLCUM_V2
    printf("durum@%zu\n", offsetof(struct olcum, durum));
#endif
    return 0;
}
```

```term
$ gcc -std=c11 -o boyut_v1 boyut.c
$ ./boyut_v1
$ gcc -std=c11 -DOLCUM_V2 -o boyut_v2 boyut.c
$ ./boyut_v2
sizeof=16 id@0 deger@8
sizeof=24 id@0 deger@8
durum@16
```

Sonuç, ABI kırılmasının somut şeklidir. v1'de `deger` 8. bayttan başlar ve yapı 16 bayttır. v2'de `durum` 16. bayta yerleşir ve yapı 24 bayta çıkar. Eski istemci 16 baytlık bir nesne ayırır; v2 kütüphanesi ise 16. bayta yazmaya çalışır. Şekil 40.2 aynı düzeni iki sürüm yan yana gösterir.

![Şekil 40.2: struct olcum düzeninin v1 ve v2 sürümleri. Eski istemcinin ayırdığı son sınır (16 bayt) kesikli çizgiyle gösterilmiştir.](gorseller/b40_abi_duzen.png)

Bu deneyden çıkan pratik kurallar şunlardır.

- **Yapıyı kullanıcıya açma.** Opak işaretçi (40.2), yapının değişmesini kullanıcıdan saklar. Açık yapı zorunluysa, alan eklemek yerine yeni bir yapı ve yeni bir fonksiyon (`olcum_v2_olustur`) yaz.
- **Boyutu kütüphaneden sorgulat.** `olcum_yapi_boyutu` gibi bir fonksiyon, istemcinin kendi derlediği yapıyla kütüphanenin gördüğü yapı arasındaki uyumsuzluğu çalışma anında ortaya çıkarır.
- **Ayırmayı kütüphaneye bırak.** `sensor_olustur` gibi bir fonksiyon, bellek ayırma işini kütüphaneye devreder. Böylece yapının boyutunu çağıranın bilmesine gerek kalmaz.
- **Sembol sürümlemesi.** Linux'ta GNU sembol sürümleme ile aynı sembol adının farklı sürümleri bir arada tutulabilir (genel bilgi). Bu, eski ikili dosyaların eski sembole bağlı kalmasını sağlar.

Platform notu: Bu deneylerde x86-64 ve WSL2 kullandık. Windows'ta aynı yapı MSVC ile derlendiğinde `int` 4 bayt, `double` 8 bayttır ve bu yapının boyutu 16 olarak kalır; ama paylaşımlı kütüphane DLL olarak yapılır ve dışa aktarılan semboller `__declspec(dllexport)` ile açıkça belirtilmelidir. ARM tabanlı bir mikrodenetleyicide (ör. bir STM32) hizalama ve dolgu kuralları derleyiciye ve hedef ABI'ye bağlıdır; bu yüzden boyutu elle hesaplamak yerine derleyiciden okumak (`sizeof`, `offsetof`) zorunludur. Bu ilke, bu bölümde gördüğümüz her ABI kararında geçerlidir.

## 40.4 REST: kaynaklar, yöntemler ve durum kodları

Bölüm 30'da REST'i bir mimari stil olarak tanıttık: kaynaklar adlarla anılır, durum istemcide tutulmaz, yanıtlar önbelleğe alınabilir. Şimdi bu stilin bir API'ye nasıl döküldeceğine bakıyoruz. Dikkat et: REST bir kütüphane ya da çerçeve değildir; bir kısıtlar kümesidir. Aynı HTTP yöntemlerini ve durum kodlarını kullanan her servis REST değildir. Biz burada pratik bir REST API'nin kararlarını tartışacağız.

### Kaynakları modellemek

REST API'nin ilk kararı, neyin kaynak olduğudur. Bir İHA filosunda kaynaklar uçaklardır, uçakların görevleridir, görevlerin noktalarıdır. Her kaynağın bir adresi (URI) olur ve adres bir isim taşır; eylemi yöntem anlatır. Bu ayrım önemlidir: `GET /ucak-getir?id=3` ile `GET /ucaklar/3` aynı şeyi yapabilir, ama ikincisi kaynağı adlandırır ve önbelleğe alınabilir, birincisi bir fonksiyon çağrısına benzer.

Dört kural pratikte işe yarar.

- **İsimler çoğul ve isimdir:** `/ihalar`, `/ihalar/7`. Fiil koyma: `/ihalar/getir` yanlıştır, çünkü eylemi yöntem zaten söyler.
- **İç içe kaynak en fazla iki seviye:** `/ihalar/7/gorevler` tamamdır; `/filolar/2/ihalar/7/gorevler/4/noktalar` okunması ve değiştirilmesi zor bir yoldur. Derin iç içelik, kaynağın bağımsız varlığını gizler.
- **Eylemler için alt kaynak:** İHA'yı "bakıma al" gibi bir durum değişikliği gerekiyorsa, `PATCH` ile `durum` alanını değiştirmek çoğu zaman yeterlidir. Bir eylem gerçekten kaynak değilse, `POST /ihalar/7/bakim-talepleri` gibi bir kaynağın oluşturulması daha temizdir.
- **Filtre ve sıralama sorgu parametresidir:** `/ihalar?durum=ucuyor&siralama=ad`. Yol kaynağı, sorgu görünümü tanımlar.

Şekil 40.3, bu API'nin kaynak hiyerarşisini gösterir. Her seviyenin yanındaki yöntem listesi, o adreste hangi işlemlerin anlamlı olduğunu söyler.

![Şekil 40.3: Kaynak hiyerarşisi. Koleksiyon, öğe ve alt koleksiyon; her adres kendi yöntem kümesini taşır.](gorseller/b40_kaynak_hiyerarsi.png)

### Yöntemler ve idempotentlik

Bölüm 30.6'da yöntemlerin güvenli ve idempotent olma özelliklerini gördün. Burada bu özellikleri tasarım kararına çeviriyoruz. Şekil 40.4, bu API'de kullandığımız yöntemleri ve beklenen davranışlarını özetler.

![Şekil 40.4: Yöntemler, güvenlik ve idempotentlik. PATCH'in idempotent olmadığına dikkat et; genel durumda RFC 5789 bunu garanti etmez.](gorseller/b40_yontem_tablosu.png)

En sık yapılan hata `PUT` ile `PATCH` arasındaki farktır. **PUT** kaynağın tamamını gönderir ve kaynağı bu gövdeyle değiştirir; gönderilmeyen alan varsayılana döner ya da silinir. Bu yüzden PUT idempotenttir: aynı tam gövde iki kez gelirse sonuç aynıdır. **PATCH** yalnızca gönderilen alanları değiştirir (RFC 5789). PATCH'in idempotent olması zorunlu değildir; `PATCH` ile "sayaç 1 artır" gibi bir işlem iki kez gelirse sonuç değişir. Bu yüzden PATCH gövdesinde değer olarak yeni durumu gönderir, artış değil; biz de API'de böyle yapıyoruz.

`POST` ise kaynak oluşturmanın ve "işlem başlatmanın" yöntemidir. İdempotent değildir ve bu yüzden ağ kesildiğinde istemcinin aynı POST'u körlemesine tekrar göndermesi tehlikelidir. Bu sorunu Bölüm 40.6'daki `Idempotency-Key` ile çözeceğiz.

### Durum kodlarını doğru seçmek

Durum kodu, istemciye ne yapması gerektiğini söyler. Yanlış kod, yanlış yeniden deneme davranışına yol açar. Bu API'nin kullandığı kodları ve seçim gerekçelerini tabloda topladık.

| Kod | Ne zaman | Notlar |
|---|---|---|
| 200 OK | Okuma ya da başarılı güncelleme, gövde var | `PUT` ve `PATCH` için yeni durumu döndür |
| 201 Created | Kaynak oluşturuldu | `Location` başlığı yeni kaynağın adresini taşır |
| 204 No Content | Silme gibi, gövdesiz başarı | RFC 9110: 204'te `Content-Length` gönderilmez |
| 400 Bad Request | JSON bozuk, sözdizimi hatalı | İstek anlaşılamadı |
| 401 Unauthorized | Kimlik yok ya da geçersiz | `WWW-Authenticate` başlığı zorunludur |
| 404 Not Found | Kaynak yok, ya da başkasına ait | Aşağıda tartışıyoruz |
| 405 Method Not Allowed | Yöntem bu adreste desteklenmiyor | `Allow` başlığı zorunludur |
| 409 Conflict | Kaynak durumuyla çakışıyor (ör. aynı ad) | İstemci durumu düzelterek yeniden deneyebilir |
| 412 Precondition Failed | `If-Match` eşleşmedi | Kaynak başkası tarafından değişmiş |
| 413 Content Too Large | Gövde sınırı aşıldı | RFC 9110 adı; Python'da `REQUEST_ENTITY_TOO_LARGE` |
| 422 Unprocessable Content | Sözdizimi doğru, anlam yanlış | RFC 9110 adı; Python'da `UNPROCESSABLE_ENTITY` |
| 428 Precondition Required | `If-Match` zorunlu ama gelmedi | RFC 6585 |
| 429 Too Many Requests | Hız sınırı aşıldı | `Retry-After` başlığı (40.8) |

400 ile 422 arasındaki ayrım sık karıştırılır. JSON hiç ayrıştırılamıyorsa (`{ad:` gibi) 400 uygundur. JSON geçerliyse ama alanlar tanımla uyuşmuyorsa (ad çok kısa, tip bilinmeyen) 422 uygundur. Bu ayrım istemciye yardımcı olur: 400 "isteğin biçimini düzelt" demektir, 422 "değerleri düzelt" demektir.

404 seçimi bir **güvenlik kararıdır**. Bir kaynağın var olduğunu, ama sana ait olmadığını söylemek (403) saldırgana kaynağın varlığını doğrular. Bu yüzden API, başkasına ait kaynağı da yok gibi gösterir: 404. Bu tercihin bedeli, meşru bir kullanıcının "neden bulamıyorum" diye şaşırmasıdır. Bölüm 40.12'de bu konuya tekrar dönüyoruz.

### Hata gövdesi: RFC 9457 problem details

Hata durumunda istemciye yalnızca durum kodu yetmez; bir açıklama gerekir. Ama açıklamanın biçimi her API'de farklıysa, her istemci her API için ayrı bir ayrıştırıcı yazmak zorunda kalır. **RFC 9457 (Problem Details for HTTP APIs)**, bu sorunu çözmek için standart bir gövde biçimi tanımlar; RFC 7807'nin yerine geçmiştir. Biçim `application/problem+json` medya türünü kullanır ve şu alanları taşır (genel bilgi, alanların tamamı RFC'de):

- `type`: hata türünü tanımlayan bir URI. Yoksa `about:blank`.
- `title`: türün kısa, insan okunur adı.
- `status`: HTTP durum kodunun tekrarı.
- `detail`: bu olaya özgü açıklama.
- `instance`: hatanın oluştuğu kaynağın adresi.

RFC, ek alanlara (extension members) izin verir. Biz bu API'de doğrulama hatalarını `hatalar` dizisiyle taşıyoruz; her eleman hangi alanın neden reddedildiğini söyler. Aşağıdaki program, geçersiz bir İHA isteğini gönderir ve yanıt gövdesinin tamamını yazdırır.

```python
# -*- coding: utf-8 -*-
"""b40_9_ornek_yanit.py: Bir hata yanitinin tam govdesini gosterir."""

import json
import threading
from http.server import HTTPServer

import b40_6_ihafilo_api as api
import b40_7_istemci as ist

srv = HTTPServer(("127.0.0.1", 0), api.Istek)
threading.Thread(target=srv.serve_forever, daemon=True).start()
ist.TABAN = "http://127.0.0.1:%d" % srv.server_address[1]

durum, basl, govde = ist.istek(
    "POST", "/ihalar", govde={"ad": "X", "tip": "ucak"}
)
print("HTTP", durum, basl["content-type"])
print(json.dumps(json.loads(govde), indent=2, ensure_ascii=False))
srv.shutdown()
```

Programın çıktısı şöyledir. Üst satır durum kodunu ve medya türünü, altındaki JSON ise gövdeyi gösterir.

```term
$ python b40_9_ornek_yanit.py
HTTP 422 application/problem+json; charset=utf-8
{
  "type": "/hatalar/dogrulama",
  "title": "Dogrulama hatasi",
  "status": 422,
  "detail": "2 alan",
  "hatalar": [
    {
      "alan": "ad",
      "mesaj": "'X' is too short"
    },
    {
      "alan": "tip",
      "mesaj": "'ucak' is not one of ['sabit_kanat', 'dortrotor']"
    }
  ]
}
```

Yanıtta `type` alanının değeri `/hatalar/dogrulama`'dır; bu göreli bir URI'dir ve RFC 9457 buna izin verir. İstemci `type` değerine bakarak hata sınıfını anlayabilir, `title` değerine bakarak da insanlara gösterebilir. `hatalar` dizisindeki mesajlar, şema kütüphanesinin İngilizce ürettiği metinlerdir. Gerçek bir sistemde bu mesajlar yerelleştirilmeli; ama `alan` değerleri değişmemeli, çünkü istemci kodu onlara bakar.

## 40.5 Sayfalama, filtreleme ve sıralama

Bir koleksiyonda yüz bin İHA görev kaydı olduğunda, hepsini tek yanıtta döndürmek hem bellek hem ağ açısından kabul edilemez. **Sayfalama**, koleksiyonu parçalara böler. Bu konuda iki temel yöntem vardır ve farkları, tasarım kararlarının en sinsi olanlarından biridir.

**Offset sayfalama**, sayfa numarasıyla çalışır: `?sayfa=3&boyut=20`. Veritabanı sorgusu `LIMIT` ve `OFFSET` ile yazılır. Bölüm 34'te gördüğün gibi, `OFFSET n` ifadesi çoğu veritabanında ilk `n` satırın okunup atılmasına yol açar; sayfa numarası büyüdükçe iş artar. Daha önemlisi, veri sayfalar arasında değişirse sonuç kayar. Bir kayıt başa eklenirse sonraki sayfada bir kayıt iki kez görünür; bir kayıt silinirse bir kayıt atlanır.

**İmleç (keyset) sayfalama**, "son gördüğüm kaydın anahtarından sonrasını ver" der: `WHERE id < son ORDER BY id DESC LIMIT 20`. Veritabanı `id` üzerindeki indeksten doğrudan oraya gider (Bölüm 34.8); sayfa numarasının bir anlamı yoktur, bu yüzden veri değişse de sonuç kaymaz. İstemciye verilen imleç, genellikle kaydın anahtarını taşıyan, opak (içeriği yorumlanmayan) bir dizedir. Biz bunu JSON'u base64url ile kodlayarak yapıyoruz; istemci içeriğe bakmamalı ve kendi imlecini üretmemelidir. Bu sayede sunucu imlecin biçimini sonradan değiştirebilir.

Bu farkı bir deneyle görelim. On kayıtlık bir tablo, sayfa boyutu üç. Birinci sayfayı alıyoruz, sonra ikinci sayfadan önce bir silme ya da bir ekleme yapıyoruz. Kodun ilk yarısı tabloyu kurar ve iki sayfalama yöntemini tanımlar:

```python
# -*- coding: utf-8 -*-
"""b40_3_sayfalama.py: Offset ve imlec (keyset) sayfalama."""

import base64
import json
import sqlite3


def veritabani():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE ucus (id INTEGER PRIMARY KEY, ad TEXT)")
    db.executemany(
        "INSERT INTO ucus (id, ad) VALUES (?, ?)",
        [(i, "U%02d" % i) for i in range(1, 11)],
    )
    return db


def offset_sayfa(db, sayfa, boyut):
    """OFFSET = (sayfa - 1) * boyut. Sayfa istemcide tutulur."""
    sorgu = "SELECT id FROM ucus ORDER BY id DESC LIMIT ? OFFSET ?"
    return [
        r[0] for r in db.execute(sorgu, (boyut, (sayfa - 1) * boyut))
    ]


def imlec_kodla(son_id):
    ham = json.dumps({"son": son_id}).encode("utf-8")
    return base64.urlsafe_b64encode(ham).decode("ascii")


def imlec_coz(imlec):
    return json.loads(base64.urlsafe_b64decode(imlec))["son"]

```

Kodun ikinci yarısı, sayfalar arası değişikliği uygular ve sonuçları yazdırır. Silme bir kaydı, ekleme ise başa yeni bir kaydı koyar.

```python

def keyset_sayfa(db, imlec, boyut):
    """Son gorulen kaydin id'sinden devam eder: WHERE id < son."""
    if imlec is None:
        sorgu, arg = (
            "SELECT id FROM ucus ORDER BY id DESC LIMIT ?",
            (boyut,),
        )
    else:
        sorgu = (
            "SELECT id FROM ucus WHERE id < ? "
            "ORDER BY id DESC LIMIT ?"
        )
        arg = (imlec_coz(imlec), boyut)
    ids = [r[0] for r in db.execute(sorgu, arg)]
    yeni = imlec_kodla(ids[-1]) if len(ids) == boyut else None
    return ids, yeni


def sil10(db):
    db.execute("DELETE FROM ucus WHERE id = 10")


def ekle11(db):
    db.execute("INSERT INTO ucus (id, ad) VALUES (11, 'U11')")


def offset_iki(degis):
    db = veritabani()
    s1 = offset_sayfa(db, 1, 3)
    degis(db)  # 1. ve 2. sayfa arasinda degisiklik
    return s1, offset_sayfa(db, 2, 3)

```

Son parça, iki senaryoyu çalıştırıp sonuçları yazdırır.

```python

def keyset_iki(degis):
    db = veritabani()
    s1, imlec = keyset_sayfa(db, None, 3)
    degis(db)
    s2, _ = keyset_sayfa(db, imlec, 3)
    return s1, s2


if __name__ == "__main__":
    for ad, fn in (
        ("offset, sil", offset_iki),
        ("keyset, sil", keyset_iki),
    ):
        print(ad, "->", fn(sil10))
    for ad, fn in (
        ("offset, ekle", offset_iki),
        ("keyset, ekle", keyset_iki),
    ):
        print(ad, "->", fn(ekle11))
```

Programın çıktısı, aynı değişikliğin iki yöntemde nasıl farklı sonuç verdiğini gösterir:

```term
$ python b40_3_sayfalama.py
offset, sil -> ([10, 9, 8], [6, 5, 4])
keyset, sil -> ([10, 9, 8], [7, 6, 5])
offset, ekle -> ([10, 9, 8], [8, 7, 6])
keyset, ekle -> ([10, 9, 8], [7, 6, 5])
```

İlk satır, offset sayfalamada 10 silindikten sonra 7 numaralı kaydın hiç görünmediğini (atlandı) söyler. Üçüncü satır, offset sayfalamada başa 11 eklendikten sonra 8 numaralı kaydın iki kez görüldüğünü (çift) gösterir. Keyset satırlarında ise her iki değişiklik de sonucu etkilemez, çünkü imleç "8'den küçükler" der. Şekil 40.5, aynı dört senaryoyu görsel olarak gösterir; sorunlu kayıtlar kırmızıyla işaretlenir.

![Şekil 40.5: Offset ve keyset sayfalama. Offset'te silme bir kaydı atlatır, ekleme bir kaydı çiftler; keyset iki durumda da sonucu korur.](gorseller/b40_sayfalama.png)

Filtreleme ve sıralama için iki uyarı. Birincisi, sıralama alanını istemciden doğrudan SQL'e koyma: `ORDER BY` içine yazılan bir değer bir enjeksiyon yüzeyidir (Bölüm 32.7). Sıralanabilir alanları bir beyaz liste ile sınırla; istemcinin söylediği "ad" yerine bir eşleme tablosundan `ad` sütunu seç. İkincisi, filtre parametreleri de bir sözleşmedir: `?durum=ucuyor` ile `?durum=UÇUYOR` aynı şey mi? Bu kararı belgele ve tutarlı uygula.

Sayfalama ile ilgili bir son not: toplam kayıt sayısı (`toplam`) döndürmek, büyük tablolarda pahalı bir `COUNT` gerektirebilir. Bu yüzden birçok API sayfalama yanıtında toplamı vermez, yalnızca bir sonraki sayfanın var olup olmadığını söyler. Biz de bu API'de `sonraki_imlec` alanını bu amaçla kullanıyoruz; sonraki sayfanın var olup olmadığını, bir fazla kayıt çekerek anlıyoruz.

## 40.6 Güvenli yeniden deneme: Idempotency-Key ve ETag

Ağ güvenilir değildir. Bir istemci `POST /ihalar` isteğini gönderir, sunucu kaydı oluşturur, ama yanıt ağda kaybolur. İstemci zaman aşımına uğrar ve ne olduğunu bilmez: kayıt oluştu mu? Yeniden göndermek güvenli mi? Bu belirsizlik, idempotent olmayan yöntemlerin en büyük sorunudur.

Çözüm **Idempotency-Key** başlığıdır. İstemci her mantıksal işlem için rastgele, benzersiz bir anahtar üretir (ör. bir UUID) ve isteğe ekler. Sunucu anahtarı, isteğin parmak izi ile birlikte saklar ve yanıtı da kaydeder. Aynı anahtarla gelen ikinci istek yeni bir kayıt oluşturmaz; kayıtlı yanıtı döndürür. Şekil 40.6 bu akışı gösterir.

![Şekil 40.6: Idempotency-Key akışı. Aynı anahtar ve aynı gövde kayıtlı yanıtı döndürür; aynı anahtar farklı gövdeyle gelirse istek reddedilir.](gorseller/b40_idempotent_akis.png)

Bu kararın dört kuralı vardır.

- **Kapsam:** Anahtar kullanıcıya göre ayrılır. İki farklı kullanıcının aynı anahtarı kullanması çakışma sayılmaz. Bu API'de tablo `(sahip, anahtar)` bileşik anahtarını kullanır.
- **Parmak izi:** Aynı anahtarla gelen gövdenin özeti (hash) saklanır. Aynı anahtar farklı bir gövdeyle gelirse bu bir hatadır ve 422 döner. Bu kural, bir istemcinin anahtarı yanlışlıkla iki farklı işlem için kullanmasını yakalar.
- **Süre:** Anahtarlar sonsuza kadar saklanmaz; birkaç saat ya da gün sonra silinir. Süre dolduktan sonra aynı anahtarın yeniden kullanılması yeni bir işlem sayılır. Bu süre, istemcinin yeniden deneme penceresiyle uyumlu olmalıdır.
- **Eşzamanlılık:** İki aynı isteğin tam aynı anda gelmesi mümkündür. Bizim sunucumuz tek iş parçacıklıdır ve bu sorunu yaşamaz. Gerçek sistemde ise anahtar tablosuna benzersizlik kısıtı (UNIQUE) koymak ve ilk yazımı kazanan olarak kabul etmek gerekir. Bu, Bölüm 34.10'daki kilit ve izolasyon düşüncesidir.

Idempotency-Key başlığı henüz bir RFC değildir; IETF'de taslak olarak çalışılmaktadır ve birçok ödeme API'si bunu zaten uygular (genel bilgi). Bu nedenle başlığın adı ve davranışı bir API'den diğerine değişebilir; kendi API'nde belgele.

Yeniden denemenin ikinci tehlikesi **kayıp güncellemedir**. İki istemci aynı İHA kaydını okur, birisi durumu `ucuyor` yapar, diğeri `bakimda` yapar; sonuncu yazan öncekinin değişikliğini sessizce ezer. Bu, Bölüm 34.10'da gördüğümüz kayıp güncelleme sorunudur ve HTTP'de **ETag** ile çözülür.

ETag, bir kaynağın belirli bir sürümünün parmak izidir. Sunucu `GET` yanıtında bu değeri `ETag` başlığında verir. İstemci güncelleme isteğinde `If-Match` ile bu değeri geri gönderir. Sunucu, kaynağın hâlâ aynı sürümde olup olmadığını kontrol eder: eşleşirse güncellemeyi yapar, eşleşmezse `412 Precondition Failed` döner. İstemci o zaman kaynağı yeniden okur ve kararını yeniden verir. Bu, **iyimser kilitleme**dir: kilidi önceden almıyoruz, çakışma olursa tespit edip yeniden deniyoruz.

Şekil 40.7 bu akışı gösterir. `If-Match` hiç gönderilmezse sunucu `428 Precondition Required` döner; bu, kayıp güncellemeyi yapısal olarak önleyen bir politikadır.

![Şekil 40.7: ETag ve If-Match ile iyimser kilitleme. Güncelleme yalnızca istemcinin gördüğü sürüm hâlâ geçerliyse yapılır.](gorseller/b40_etag_akis.png)

ETag değerinin nasıl üretileceği bir tasarım seçimidir. Bu API'de ETag, kaynağın kanonik JSON gösteriminin SHA-256 özetinin ilk 16 hanesidir; Bölüm 30.9'daki yaklaşımın aynısıdır. RFC 9110, ETag değerinin tırnak içinde olmasını ister: `"a02112d960b174f0"`. Bu tırnaklar değerin parçasıdır ve `If-Match` ile tam olarak aynı biçimde geri gönderilmelidir. Güçlü ETag (strong validator) bayt düzeyinde eşleşme anlamına gelir; biz de güçlü olanı kullanıyoruz, çünkü kayıp güncelleme önlemek için bayt eşleşmesi gerekir.

## 40.7 Hız sınırlama: token bucket

Bir API'yi herkes sınırsız çağırabilirse, tek bir hatalı istemci ya da kötü niyetli bir saldırgan sunucuyu boğabilir. **Hız sınırlama** (rate limiting), bir istemcinin birim zamanda yapabileceği istek sayısını sınırlar. En yaygın algoritma **token bucket** (jeton kovası)tır.

Kavram basittir. Her istemcinin bir kovası vardır; kova en fazla **kapasite** kadar jeton tutar. Kova saniyede **hız** kadar jeton kazanır (ama kapasiteyi aşamaz). Her istek bir jeton harcar. Jeton yoksa istek reddedilir. Bu modelin güzel yanı, kısa süreli patlamalara izin vermesidir: kova doluysa, istemci kapasite kadar isteği arka arkaya gönderebilir; ama uzun vadede ortalama hız, hız parametresiyle sınırlıdır.

Kovanın durumu iki değişkenle tanımlanır: `jeton` (şu an kaç jeton var) ve `son` (son güncelleme zamanı). Her istekte önce geçen süreye göre jeton eklenir, sonra isteğin maliyeti düşülür:

```text
jeton = min(kapasite, jeton + (simdi - son) * hiz)
```

Bu formül kovayı tembel (lazy) biçimde günceller: süre dolduğunda değil, bir istek geldiğinde hesaplanır. Böylece kova için ayrı bir zamanlayıcı gerekmez.

Kodun tamamı, bir kova sınıfı ile bir olay dizisinde kovanın durumunu yazdırır. Saat, gerçek zaman yerine elle verilen değerlerdir; böylece sonuç her çalıştırmada aynıdır. Gerçek sunucuda `time.monotonic()` kullanılır. (`monotonic` saatin geriye gitmediği bir sayaçtır; hız sınırlama için `time.time()` yerine bunu kullanmak doğru tercihtir.)

```python
# -*- coding: utf-8 -*-
"""b40_4_kova.py: Token bucket (jeton kovasi) hiz sinirlayicisi."""

import csv
import sys


class KovaSinirlayici:
    def __init__(self, kapasite, hiz):
        if kapasite <= 0 or hiz <= 0:
            raise ValueError("kapasite ve hiz pozitif olmali")
        self.kapasite = float(kapasite)  # biriken en fazla jeton
        self.hiz = float(hiz)  # saniyede eklenen jeton
        self.jeton = float(kapasite)  # baslangicta kova dolu
        self.son = None  # son guncelleme zamani

    def _yenile(self, simdi):
        if self.son is None:
            self.son = simdi
        gecen = simdi - self.son
        self.jeton = min(self.kapasite, self.jeton + gecen * self.hiz)
        self.son = simdi

    def izin_ver(self, simdi, maliyet=1.0):
        """(izin, bekleme_s). izin True ise jeton dusulur."""
        self._yenile(simdi)
        if self.jeton >= maliyet:
            self.jeton -= maliyet
            return True, 0.0
        return False, (maliyet - self.jeton) / self.hiz


OLAYLAR = [0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.2, 3.0, 3.0, 3.0, 3.0]
```

Sınıfın kullanımını gösteren ana bölüm, bir dizi zaman damgası için kararları yazdırır ve CSV dosyası üretir:

```python

if __name__ == "__main__":
    kova = KovaSinirlayici(kapasite=3, hiz=1.0)
    print("%6s %6s %7s %9s" % ("zaman", "izin", "jeton", "bekleme"))
    satirlar = []
    for t in OLAYLAR:
        izin, bekle = kova.izin_ver(t)
        print("%6.2f %6s %7.2f %9.2f" % (t, izin, kova.jeton, bekle))
        satirlar.append(
            (t, int(izin), round(kova.jeton, 4), round(bekle, 4))
        )
    if len(sys.argv) > 1:  # CSV'yi istenen yola yaz
        with open(
            sys.argv[1], "w", newline="", encoding="utf-8"
        ) as f:
            w = csv.writer(f)
            w.writerow(["zaman_s", "izin", "jeton", "bekleme_s"])
            w.writerows(satirlar)
```

Program, kapasitesi üç ve hızı saniyede bir olan bir kovaya on bir istek gönderir. Çıktı şöyledir:

```term
$ python b40_4_kova.py kova.csv
 zaman   izin   jeton   bekleme
  0.00   True    2.00      0.00
  0.00   True    1.00      0.00
  0.00   True    0.00      0.00
  0.00  False    0.00      1.00
  0.50  False    0.50      0.50
  1.00   True    0.00      0.00
  1.20  False    0.20      0.80
  3.00   True    1.00      0.00
  3.00   True    0.00      0.00
  3.00  False    0.00      1.00
  3.00  False    0.00      1.00
```

Her satırda istek anındaki jeton sayısı (istekten sonra) ve reddedilirse ne kadar beklenmesi gerektiği yazılıdır. İlk üç istek (t = 0) kovadaki üç jetonu harcar. Dördüncü istek aynı anda geldiği için jeton yoktur ve bekleme süresi `(1 - 0) / 1 = 1.00` saniyedir. Bu bekleme değeri, API'nin `Retry-After` başlığına yazdığı değerin kaynağıdır: sunucu saniyenin tam sayısına yukarı yuvarlar. Şekil 40.8, aynı olayları CSV dosyasından okuyarak çizer; yeşil noktalar izin verilen, kırmızı noktalar reddedilen istekleri gösterir.

![Şekil 40.8: Token bucket durumu. Adım fonksiyonu jeton sayısını gösterir; kesikli çizgi kapasiteyi (3) belirtir. Veri engine/veri/b40_kova.csv dosyasından okunur.](gorseller/b40_kova_durum.png)

Şekil, bir ayrıntıyı açıkça gösterir: kova t = 3'te boşalmış bir kovadır ve bu andan sonra iki istek reddedilir. Jeton saniyede bir eklenir: kova boşken gelen istekler yalnızca bu hızda geçer, kova dolu iken ise kapasite kadar istek arka arkaya geçebilir. Bu tam olarak "kısa patlamaya izin ver, uzun vadede hızı sınırla" hedefidir.

Bu API'de her kullanıcının kendi kovası vardır (`KOVALAR` sözlüğü). Reddedilen istek 429 döner ve `Retry-After` başlığı, saniye cinsinden bir sonraki isteğin ne zaman kabul edileceğini söyler. RFC 9110 bu başlığın değerini ya saniye ya da bir HTTP tarihi olarak tanımlar; biz saniye kullanıyoruz.

Token bucket'a alternatif olarak birkaç algoritma vardır (genel bilgi). **Sızdıran kova** (leaky bucket), istekleri sabit bir hızda işler ve fazlasını kuyruğa alır; patlamalara izin vermez. **Sabit pencere** (fixed window), "dakikada en fazla 100 istek" gibi bir sayaç tutar; ama pencere sınırında iki katına yakın bir patlamaya izin verir (bir dakikanın sonunda 100, bir sonrakinin başında 100). **Kayan pencere** bu sorunu giderir ama daha fazla bellek ister. Hangisinin seçileceği, patlamaya ne kadar toleransın olduğuna bağlıdır.

Bir son not: bu sınırlayıcı tek bir süreçte, bellekte çalışır. Birden çok sunucu varsa her birinin kendi kovası olur ve kullanıcı sınırı kadar istek her sunucuya gönderebilir. Bu durumda kovanın ortak bir depoda (ör. Redis) tutulması gerekir; bu, Bölüm 41'in ölçekleme ve önbellek konularının doğal devamıdır.

## 40.8 Sürümleme ve geriye dönük uyumluluk

Bir API yayımlandığı anda, onu kullanan istemciler vardır. Bu yüzden yeni bir sürüm çıkarmak, eskisini bir gecede kapatmak anlamına gelmez. Sürümleme, iki sürümün bir süre birlikte çalışmasını sağlayan bir sözleşmedir.

Önce bir soru: hangi değişiklikler **uyumlu** (geriye dönük uyumlu), hangileri **kırıcı** (breaking)? Pratik bir kural:

- **Uyumlu:** Yanıta yeni bir isteğe bağlı alan eklemek; yeni bir uç nokta eklemek; isteğe bağlı yeni bir sorgu parametresi eklemek. Eski istemci bu alanları görmezden gelirse sorun çıkmaz.
- **Kırıcı:** Bir alanı kaldırmak ya da adını değiştirmek; bir alanın türünü değiştirmek; zorunlu bir istek alanı eklemek; bir alanın anlamını değiştirmek (ör. `hiz` alanı km/s'ten m/s'ye geçerse, değerin kendisi aynı kalsa bile kırıcıdır); bir varsayılan değeri değiştirmek.
- **Gri alan:** Numaralandırmaya (enum) yeni bir değer eklemek. Eski istemci o değeri görünce ne yapacağını bilmiyorsa kırılır. Bu yüzden numaralandırma değerlerinin bilinmeyenlere dayanıklı olması istenir.

Kırıcı değişiklik gerekiyorsa sürüm numarasını artırırsın. Üç yaygın yol vardır; Şekil 40.9 bunları karşılaştırır.

![Şekil 40.9: Sürümleme stratejileri. URL, başlık ve içerik anlaşması; her birinin kazancı ve maliyeti farklıdır.](gorseller/b40_surum_stratejileri.png)

- **URL sürümü** (`/v2/ihalar`): En açık yöntemdir; tarayıcıda, önbellekte ve günlüklerde görünür. Bedeli, her sürüm için ayrı bir adres kümesi demektir.
- **Başlık sürümü** (`X-Api-Version: 2`): Adresler temiz kalır. Ama önbellekler ve tarayıcı istekleri bu başlığa bakmayı unutabilir; `Vary` başlığı doğru kullanılmazsa önbellek karışır.
- **İçerik anlaşması** (`Accept: application/vnd.ihafilo.v2+json`): REST'in içerik müzakeresi ilkesine en uygun olanıdır (Bölüm 30). Öğrenmesi daha zordur ve bazı istemci araçları özel medya türlerini zorlanarak kullanır.

Hangisini seçersen seç, şu kural değişmez: **alan eklemek güvenlidir, kaldırmak ya da anlamını değiştirmek yıkıcıdır.** Bu kural, sürümlemenin çoğu ihtiyacını ortadan kaldırır. Bir alanı kaldırmak yerine "kullanımdan kaldırıldı" diye işaretleyip yeni alan eklemek, sürüm atlamadan geçişi mümkün kılar.

Bu noktada **Postel ilkesi** anılır: "Gönderdiğin şeyde muhafazakâr, aldığın şeyde hoşgörülü ol." İlke, TCP spesifikasyonları üzerinden yayılmıştır (genel bilgi). Hoşgörülü ayrıştırma, bir zamanlar birlikte çalışabilirliği artırmak için mantıklıydı. Ancak bugün aynı hoşgörü, belirsiz davranışların kalıcılaşmasına ve güvenlik açıklarına yol açar: bir istemci sana tanımadığın bir alanla gelirse onu sessizce atarsan, o alanın yanlış tür ya da yanlış değerle geldiğini de sessizce kabul etmiş olursun. Modern yaklaşım, sözleşmede tanımlı olanı titizlikle kabul etmek, tanımsız alanları ise açıkça reddetmek ya da belgelenmiş bir biçimde yok saymaktır. Bu API şemamızda `additionalProperties: false` ile bunu yapıyoruz (40.9).

Kullanımdan kaldırma (deprecation) bir süreçtir, bir anahtar değildir. Sıra şöyledir: yeni sürümü yayımla; eski sürümün yanıtlarına kullanımdan kaldırma bilgisini ekle; eski sürümün ne zaman kapanacağını **Sunset** başlığıyla bildir (RFC 8594); bu sürede eski sürümün kullanımını günlüklerden izle; kapanış tarihinden önce kullanan istemcilere ulaş. `Deprecation` başlığı için IETF'de bir çalışma sürmektedir (genel bilgi). Önemli olan, kullanımdan kaldırmayı bir duyuru ile değil, yanıtın kendisiyle yapmaktır: insanlar duyuruyu okumaz, ama log'lar okunur.

## 40.9 Şema, sözleşme ve belgelendirme

Bir API'nin sözleşmesi bir tarafta yazılı, diğer tarafta kodlanmış olmalıdır. Yazılı sözleşme belgedir; kodlanmış sözleşme ise çalışma anında denetlenen kurallardır. İkisi uyuşmazsa, belge yalan söyler ya da kod kendi kurallarını ihlal eder.

**JSON Schema**, bir JSON nesnesinin biçimini tanımlayan bir standarttır (Draft 2020-12 bu bölümde kullandığımız sürümdür). Bir şema, hangi alanların zorunlu olduğunu, türlerini, sınırlarını ve izin verilen değerlerini söyler. Bu API'de iki şema var: İHA için `IHA_SEMA`, görev için `GOREV_SEMA`. Bunları kendi kodumuzda değil, `jsonschema` kütüphanesi ile doğrularız. Kütüphane, Python'da JSON Schema'nın yaygın uygulamasıdır ve sürüm 4.26.0 ile bu bölümde kullanıldı.

Şemanın nasıl çalıştığını görmek için, aşağıdaki program üç örneği doğrular. Birinci örnek geçerli, ikincisinde bilinmeyen bir alan ve eksik zorunlu alan var, üçüncüsünde iki alan kuralı ihlal ediliyor. Ayrıca bu API'nin gerçek kod yolunda, HTTP'ye gerek kalmadan, bir **tüketici odaklı sözleşme testi** yapılıyor: istemcinin beklediği yanıt biçimi, gerçek üretilen yanıtla karşılaştırılıyor.

```python
# -*- coding: utf-8 -*-
"""b40_8_sozlesme.py: JSON Schema ile sozlesme dogrulamasi.

Iki parca: (1) istek govdesi dogrulamasi, (2) tuketici odakli
sozlesme testi: API'nin gercek yanit govdesi istemcinin
beklentisine uyuyor mu?
"""

import jsonschema

import b40_6_ihafilo_api as api

# Istemcinin (tuketicinin) bekledigi yanit bicimi.
YANIT_SEMA = {
    "type": "object",
    "required": ["id", "ad", "tip", "durum"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "ad": {"type": "string"},
        "tip": {"enum": ["sabit_kanat", "dortrotor"]},
        "durum": {"enum": ["hazir", "ucuyor", "bakimda"]},
    },
}


def hatalar(sema, nesne):
    dogrulayici = jsonschema.Draft202012Validator(sema)
    return [
        ("/".join(str(p) for p in e.path) or "(kok)", e.message)
        for e in dogrulayici.iter_errors(nesne)
    ]

```

```python

def istek_testi():
    ornekler = [
        {"ad": "ALFA-1", "tip": "sabit_kanat"},
        {"ad": "ALFA-1", "tipp": "sabit_kanat"},
        {"ad": "A", "tip": "helikopter", "durum": "ucuyor"},
    ]
    for i, o in enumerate(ornekler, 1):
        h = hatalar(api.IHA_SEMA, o)
        if not h:
            print("ornek %d: gecerli" % i)
            continue
        print("ornek %d:" % i)
        for alan, mesaj in h:
            print("  %s: %s" % (alan, mesaj))


def sozlesme_testi():
    # Gercek kod yolunu calistirir: HTTP katmani olmadan.
    durum, nesne, _, _ = api.ihalari_olustur(
        "ali", {"ad": "ZETA-9", "tip": "dortrotor"}, None
    )
    print("provider durum:", durum)
    print("yanit gecerli mi:", hatalar(YANIT_SEMA, nesne) == [])
    kirik = dict(nesne)
    kirik["state"] = kirik.pop("durum")  # alan adini degistirmek
    print("alan adi degisince:", hatalar(YANIT_SEMA, kirik))


if __name__ == "__main__":
    istek_testi()
    sozlesme_testi()
```

Programın çıktısı şöyledir:

```term
$ python b40_8_sozlesme.py
ornek 1: gecerli
ornek 2:
  (kok): 'tip' is a required property
  (kok): Additional properties are not allowed ('tipp' was unexpected)
ornek 3:
  ad: 'A' is too short
  tip: 'helikopter' is not one of ['sabit_kanat', 'dortrotor']
provider durum: 201
yanit gecerli mi: True
alan adi degisince: [('(kok)', "'durum' is a required property")]
```

İkinci örnekteki iki hata birlikte raporlanır: `tip` zorunlu olduğu için eksik, `tipp` ise tanımsız olduğu için reddedilir. Yazım hatası bu yüzden tam olarak yakalanır. Üçüncü örnekte ise her hata ayrı ayrı görünür. Bu, istemcinin tek seferde bütün sorunları düzeltebilmesi için önemlidir.

Sözleşme testinin asıl fikri son satırlardadır. Bir sağlayıcı (provider) değişikliği yaptığında, alanın adını `durum` yerine `state` yaparsa, tüketici (consumer) tarafındaki beklenti kırılır. Bu kırılma, sağlayıcının kendi testlerinde değil, tüketicinin beklentisini doğrulayan testte görünür. **Tüketici odaklı sözleşme testi** (consumer-driven contract testing; Pact çerçevesi bu fikrin bilinen bir uygulamasıdır, genel bilgi) tam olarak bunu sağlar: tüketici beklentisini yazar, sağlayıcı bu beklentilerin hepsini karşılamak zorundadır. Bölüm 39'da birim ve entegrasyon testlerini gördün; sözleşme testi, bu ailenin ağlar arası versiyonudur.

**OpenAPI**, REST API'lerini makine tarafından okunabilir bir belgeyle tanımlamanın yaygın standardıdır (genel bilgi). OpenAPI 3.1 belgesi, JSON Schema 2020-12 ile uyumludur; yani bir OpenAPI belgesindeki şema bölümü, bu bölümde yazdığımız şemanın aynısıdır. Kısaltılmış bir örnek:

```yaml
paths:
  /ihalar:
    post:
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/IhaIstek'
      responses:
        '201':
          description: Kayıt oluşturuldu
        '422':
          description: Doğrulama hatası
```

Bu belge, bir istemci kütüphanesinin, bir test sunucusunun ve bir belge sayfasının tek kaynaktan üretilmesine imkân verir. OpenAPI belgesi bu bölümde çalıştırılmadı; yalnızca yapıyı göstermek için yazıldı. Gerçek bir projede belge ile kod arasındaki uyumu, belgeyi kodla birlikte bir test olarak çalıştırarak denetle.

Belgelendirmenin son kuralı: örnekler çalışmalı. Bu bölümdeki her çıktı, kodun gerçekten ürettiği çıktıdır; bir API belgesindeki örnek de böyle olmalıdır. Python'da `doctest` modülü, docstring'lerdeki örnekleri çalıştırıp çıktılarını karşılaştırır; bu, belgenin kodla senkron kalmasını sağlar (genel bilgi).

## 40.10 Alternatifler: RPC, GraphQL, gerçek zamanlı akış ve mesajlaşma

REST her sorunu çözmez. Bazı durumlarda başka bir API stili daha uygundur. Her birinin ne zaman seçildiğini bilmek, tasarım mülakatlarının ve gerçek projelerin önemli bir parçasıdır.

**RPC** (Remote Procedure Call), ağ üzerinden bir fonksiyon çağırmanın soyutlamasıdır. İstemci `gorevBaslat(ihaId, rota)` gibi bir fonksiyon çağırır; arka planda bir kodlama, bir taşıma ve bir ayrıştırma yapılır. **gRPC**, Google'ın RPC çerçevesidir; taşıma olarak HTTP/2 kullanır ve veri biçimi olarak **Protocol Buffers** (protobuf) kullanır. Protobuf bir şemayla başlar (`.proto` dosyası), bu şemadan çeşitli dillerde kod üretilir ve veri ikili (binary) olarak kodlanır. Düşük bant genişliğindeki bir telemetri hattında bu fark ciddidir; Bölüm 31'de ikili protokollerin neden tercih edildiğini gördün.

Protobuf'un kodlaması, bir bayt sırası sorusudur ve elle çözülebilir. Bir mesaj, alanların sıralı bir dizisidir. Her alanın başında bir **anahtar** vardır: `(alan_no << 3) | tip`. Tip, değerin nasıl kodlandığını söyler: `0` varint, `2` uzunluk öneki. Varint, sayıyı 7 bitlik parçalara bölüp her parçayı bir bayta yazan değişken uzunluklu bir kodlamadır; en yüksek bit (MSB), "devamı var" anlamına gelir. `sint32` türü için negatif sayılar **zigzag** kodlamasıyla pozitife çevrilir: `-3` → `5`, `3` → `6`.

Aşağıdaki program, bu kuralları elle uygular. Üç alanlı bir `Telemetri` mesajını kodlar ve çözer:

```python
# -*- coding: utf-8 -*-
"""b40_5_protobuf.py: Protocol Buffers kodlamasini elle yapar.

Mesaj: message Telemetri { uint32 id = 1; sint32 sicaklik = 2;
                           string ad = 4; }
"""


def varint_kodla(n):
    cikti = bytearray()
    while True:
        bayt = n & 0x7F  # alttaki 7 bit
        n >>= 7
        if n:
            cikti.append(bayt | 0x80)  # devam biti: sonra gelen var
        else:
            cikti.append(bayt)
            return bytes(cikti)


def varint_coz(veri, i):
    """(deger, yeni_konum) dondurur."""
    n, kayma = 0, 0
    while True:
        b = veri[i]
        i += 1
        n |= (b & 0x7F) << kayma
        kayma += 7
        if not b & 0x80:
            return n, i
        if kayma > 63:
            raise ValueError("varint cok uzun")


def zigzag_kodla(n):
    return (n << 1) ^ (n >> 31)  # sint32 icin: -3 -> 5, 3 -> 6

```

```python

def zigzag_coz(z):
    return (z >> 1) ^ -(z & 1)


def alan_kodla(no, tip, deger):
    anahtar = varint_kodla((no << 3) | tip)
    if tip == 0:  # varint
        return anahtar + varint_kodla(deger)
    if tip == 2:  # uzunluk onekli
        return anahtar + varint_kodla(len(deger)) + deger
    raise ValueError("desteklenmeyen tip")


def telemetri_kodla(id_, sicaklik, ad):
    return (
        alan_kodla(1, 0, id_)
        + alan_kodla(2, 0, zigzag_kodla(sicaklik))
        + alan_kodla(4, 2, ad.encode("utf-8"))
    )


def telemetri_coz(veri):
    i, alanlar = 0, {}
    while i < len(veri):
        anahtar, i = varint_coz(veri, i)
        no, tip = anahtar >> 3, anahtar & 0x7
        if tip == 0:
            deger, i = varint_coz(veri, i)
        elif tip == 2:
            uz, i = varint_coz(veri, i)
            deger = veri[i : i + uz]
            i += uz
        else:
            raise ValueError("tip %d desteklenmiyor" % tip)
        alanlar[no] = (tip, deger)
    return alanlar

```

```python

if __name__ == "__main__":
    print("150 varint:", varint_kodla(150).hex(" "))
    print(
        "zigzag(-3) = %d, zigzag(3) = %d"
        % (zigzag_kodla(-3), zigzag_kodla(3))
    )
    m = telemetri_kodla(150, -3, "EV")
    print("mesaj (%d bayt): %s" % (len(m), m.hex(" ")))
    a = telemetri_coz(m)
    print("alan 1 id       =", a[1][1])
    print("alan 2 sicaklik =", zigzag_coz(a[2][1]))
    print("alan 4 ad       =", a[4][1].decode("utf-8"))
```

Programın çıktısı mesajın baytlarını ve çözülmüş alanları gösterir:

```term
$ python b40_5_protobuf.py
150 varint: 96 01
zigzag(-3) = 5, zigzag(3) = 6
mesaj (9 bayt): 08 96 01 10 05 22 02 45 56
alan 1 id       = 150
alan 2 sicaklik = -3
alan 4 ad       = EV
```

Mesajın dokuz baytı şu anlama gelir: `08` alan 1'in anahtarıdır (`1 << 3 | 0`); `96 01` değer olarak 150'dir. `10` alan 2'nin anahtarıdır; `05` zigzag değeridir ve `-3`'e karşılık gelir. `22` alan 4'ün anahtarıdır (`4 << 3 | 2`); `02` uzunluğu, `45 56` ise "EV" metnini taşır. Şekil 40.10 bu düzeni bir bakışta gösterir.

![Şekil 40.10: Protobuf mesajının bayt düzeni. Her alan bir anahtar ve bir değer taşır; anahtar alan numarasını ve kodlama tipini tek bayta sıkıştırır.](gorseller/b40_protobuf_bayt.png)

Elle yazdığımız kodun doğruluğunu sınamanın en iyi yolu, resmi kütüphaneyle karşılaştırmaktır. Bu bilgisayarda `protoc` derleyicisi kurulu değil; ama Python'un `google.protobuf` paketi kurulu. Tanımı `FileDescriptorProto` ile programatik olarak kurup aynı mesajı resmi kütüphaneyle kodlayabiliriz:

```python
# -*- coding: utf-8 -*-
"""b40_5b_capraz.py: Elle kodlamayi resmi kutuphaneyle karsilastirir.

protoc calismiyor olabilir; bunun yerine tanimi FileDescriptorProto
ile programatik olarak kurup google.protobuf'a verir.
"""
from google.protobuf import descriptor_pb2, descriptor_pool
from google.protobuf.message_factory import GetMessageClass

import b40_5_protobuf as el

F = descriptor_pb2.FieldDescriptorProto
fdp = descriptor_pb2.FileDescriptorProto(
    name="telemetri.proto", package="b40", syntax="proto3")
mesaj = fdp.message_type.add(name="Telemetri")
for ad, no, tip in (("id", 1, F.TYPE_UINT32),
                    ("sicaklik", 2, F.TYPE_SINT32),
                    ("ad", 4, F.TYPE_STRING)):
    mesaj.field.add(name=ad, number=no, type=tip,
                    label=F.LABEL_OPTIONAL)

havuz = descriptor_pool.DescriptorPool()
havuz.AddSerializedFile(fdp.SerializeToString())
Telemetri = GetMessageClass(
    havuz.FindMessageTypeByName("b40.Telemetri"))

resmi = Telemetri(id=150, sicaklik=-3, ad="EV").SerializeToString()
ben = el.telemetri_kodla(150, -3, "EV")
print("resmi kutuphane:", resmi.hex(" "))
print("elle kodlama   :", ben.hex(" "))
print("ayni mi        :", resmi == ben)
```

```term
$ python b40_5b_capraz.py
resmi kutuphane: 08 96 01 10 05 22 02 45 56
elle kodlama   : 08 96 01 10 05 22 02 45 56
ayni mi        : True
```

İki çıktı birebir aynıdır. Bu, kendi ayrıştırıcının doğruluğunu kanıtlamanın en ucuz yoludur: bağımsız bir uygulama aynı baytları üretiyorsa, ikisinin de büyük olasılıkla doğru olduğunu düşünebiliriz.

**GraphQL**, istemciye sorgusunda hangi alanları istediğini seçme gücü verir: tek bir uç nokta ve bir sorgu dili. Bu güç iki sorun doğurur. Birincisi **aşırı veri (overfetching)** ve **eksik veri (underfetching)**: istemci ihtiyacından fazlasını ya da eksiğini isteyebilir. İkincisi **N+1 sorunu**dur: her öğe için ayrı bir veritabanı sorgusu yapılır. Bölüm 34.9'da bu sorunu bir ORM bağlamında gördün; GraphQL çözümleyicilerinde (resolver) aynı kalıp kendiliğinden ortaya çıkar ve yükleyici (dataloader) gibi toplu yükleme teknikleriyle çözülür (genel bilgi). GraphQL'in önbellekleme zorluğu da bilinir: tek uç nokta, URL tabanlı HTTP önbelleğini zorlaştırır.

**Gerçek zamanlı akış** için iki yaygın araç vardır. **Sunucu gönderimli olaylar** (SSE), sunucudan istemciye tek yönlü bir olay akışıdır ve düz HTTP üzerinde çalışır. **WebSocket**, iki yönlü, sürekli bir kanaldır ve HTTP'den bir yükseltmeyle (upgrade) başlar. Bir telemetri paneli için SSE çoğu zaman yeterlidir; bir komut kanalı için WebSocket ya da başka bir iki yönlü protokol gerekebilir (genel bilgi).

**Mesaj tabanlı API'ler**, istek-yanıt yerine kuyruk ya da yayın-abone modeli kullanır: üretici bir mesaj yazar, tüketici sonra okur. Bu, üretici ile tüketicinin aynı anda hazır olmasını gerektirmez; yük yükseldiğinde mesajlar birikir. Bu modelin ölçekleme, tutarlılık ve kuyruk kavramları Bölüm 41'in konusudur; burada yalnızca bir API stili olarak anıyoruz.

## 40.11 Güvenlik ve gözlemlenebilirlik

Bir API'ye erişen herkesi tanımadığın sürece, her isteği şüpheli kabul etmelisin. Bu bölümde güvenliğin tamamını anlatmıyoruz; Bölüm 32 bu konunun ayrıntılı yeridir. Burada API tasarımına doğrudan dokunan dört konuyu alıyoruz.

**Kimlik doğrulama** (authentication) "bu kim?" sorusunu, **yetkilendirme** (authorization) ise "bu kişi bunu yapabilir mi?" sorusunu yanıtlar. İkisi karıştırılmamalıdır. Bu API'de kimlik, `X-Api-Key` başlığındaki anahtarla belirlenir; yetki ise anahtarın sahibinin kaynaklara erişimiyle belirlenir. API anahtarı, kullanıcıyı tanımlayan uzun bir dizgedir; OAuth 2.0 ile gelen bearer token'lar ise sınırlı süreli ve kapsamlı jetonlardır (genel bilgi). Anahtarlar ve jetonlar koda gömülmez; bu bölümdeki anahtarlar yalnızca yerel bir demo içindir ve gerçek sistemde yapılandırmadan okunur (Bölüm 32.10: sırları koda gömmemek).

Yetkilendirmenin en sık ihlal edilen biçimi **nesne düzeyinde yetkilendirme** eksikliğidir. OWASP API Güvenlik İlk On listesinin 2023 sürümünde bu, **API1: Kırık Nesne Düzeyi Yetkilendirme (BOLA)** olarak en başta yer alır (genel bilgi). Saldırgan, kendi kaynağının kimliğini başka bir kaynağın kimliğiyle değiştirir: `GET /ihalar/7` yerine `GET /ihalar/8`. Sunucu kimliğin sahibini kontrol etmezse, başkasının verisi gelir. Bu API'de sahiplik kontrolü her sorguda `WHERE ... AND sahip = ?` ile yapılır; başkasına ait kayıt, sorguya hiç girmez ve 404 döner. Bu, Bölüm 40.12'deki test programının sınadığı davranıştır.

**Girdi doğrulama**, her alanın türünü, uzunluğunu, biçimini ve değer aralığını sınırlar. Bu API'de üç katman vardır: gövde boyutu sınırı (4096 bayt, 413), alan şeması (tür, uzunluk, `pattern`, `enum`, `minimum`) ve iş kuralları (aynı ad iki kez kaydedilemez, 409). Şema, `additionalProperties: false` ile bilinmeyen alanları da reddeder; bu, mass assignment (istemcinin, izin verilmeyen alanları, mesela `sahip` alanını göndererek değiştirmesi) saldırısını engeller. Bölüm 32.7'deki enjeksiyon ve doğrulama ilkeleri burada da geçerlidir.

**Hız sınırı** (40.8) hem kötüye kullanımı hem de yanlışlıkla oluşan döngüleri sınırlar. Ayrıca her kullanıcının kendi kovası olduğunu unutma; tek bir kullanıcının yükü diğerlerini etkilememelidir.

**Gözlemlenebilirlik**, bir sistemin dışarıdan ne yaptığını gözlemleyebilme yeteneğidir. Bir API için iki temel araç vardır. Birincisi **istek kimliği** (correlation ID): her isteğe benzersiz bir kimlik verilir, yanıta ve günlüğe yazılır. Kullanıcı bir hata bildirdiğinde, bu kimlikle günlükteki tam kaydı bulabilirsin. Bizim sunucu istemciden gelen `X-Request-ID` değerini kabul eder ya da bir UUID üretir; bu değer yanıt başlığında geri döner. Kullanıcıdan gelen bir değeri günlüğe yazarken dikkat et: yeni satır karakteri içeren bir kimlik, günlük dosyasına sahte satırlar eklenmesine (log injection) yol açabilir. Bu yüzden günlüğü JSON olarak yazıyoruz; JSON, dizgedeki yeni satırı kaçışlar (`\n`).

İkincisi **yapılandırılmış günlük**tür. Her satır, makine tarafından okunabilen bir JSON nesnesidir ve olay, yöntem, yol, durum ve istek kimliği gibi alanlar taşır. Bu API'de günlük satırlarında zaman damgası yok; çünkü zaman damgası genellikle günlük toplayıcısı tarafından eklenir ve bu demoyu her çalıştırmada aynı tutmak istedik. Gerçek bir sistemde zaman damgası, süre ve istemci adresi de eklenir; ama hassas verileri (parola, anahtar, kişisel veri) günlüğe asla yazma.

## 40.12 Uygulama: İHA filo API'si

Bu bölümde öğrendiklerinin hepsini birleştiren bir uygulama yazıyoruz: bir İHA filosu için REST API'si. Kaynaklar, her kullanıcının kendi filosu, alt kaynak olarak görevler, doğrulama, hata gövdesi, imleç sayfalama, `Idempotency-Key`, `ETag`/`If-Match`, hız sınırı ve gövde boyutu sınırı burada bir arada.

Tasarım kararları şunlardır.

- **Kaynaklar:** `/ihalar` (koleksiyon), `/ihalar/{id}` (öğe), `/ihalar/{id}/gorevler` (alt koleksiyon). Yanıtlar JSON'dur; hatalar RFC 9457 biçimindedir.
- **Veri:** Bellekte SQLite (`:memory:`). Tablolar Bölüm 34'teki ilişkisel tasarım düşüncesiyle kuruldu: `iha`, `gorev`, ve yeniden denemeler için `idem`. `UNIQUE (sahip, ad)` kısıtı aynı kullanıcı için aynı adı önler.
- **Kimlik ve sahiplik:** `X-Api-Key` başlığı kullanıcıyı belirler. Her sorgu `sahip` sütununa göre filtrelenir; başkasına ait kayıt 404 döner.
- **Sayfalama:** İmleç tabanlı (keyset), bir fazla kayıt çekerek sonraki sayfanın varlığını anlama.
- **Eşzamanlılık:** GET yanıtında ETag, güncelleme ve silmede `If-Match` zorunlu (428), uyumsuzlukta 412.
- **Yeniden deneme:** `POST /ihalar` için `Idempotency-Key`; aynı anahtar ve aynı gövdede kayıtlı yanıt, farklı gövdede 422.
- **Hız sınırı:** Her kullanıcının kovası; aşılırsa 429 ve `Retry-After`.
- **Gövde sınırı:** 4096 bayttan büyük gövdeler 413 ile reddedilir; gövde okunmadan bağlantı kapatılır.

Uygulama yalnızca standart kütüphane ve `jsonschema` kullanır; sunucu `http.server` üzerinde çalışır. Kod iki dosyaya bölünmüştür. Önce sunucu modülü: yapılandırma ve şemalarla başlar.

```python
# -*- coding: utf-8 -*-
"""b40_6_ihafilo_api.py: Mini Iha filo REST API'si.

Kaynaklar: /ihalar, /ihalar/{id}, /ihalar/{id}/gorevler
Veri: sqlite3 (bellekte), Bolum 34'teki gibi tablolar.
"""

import hashlib
import json
import math
import sqlite3
import sys
import time
import uuid
from base64 import urlsafe_b64decode, urlsafe_b64encode
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import jsonschema

from b40_4_kova import KovaSinirlayici

# Test anahtarlari: yalnizca bu bolumun yerel demosu icin.
# Gercek sistemde anahtarlar yapilandirmadan okunur (Bolum 32).
# anahtar -> (kullanici, kova kapasitesi, jeton/saniye)
ANAHTARLAR = {
    "k-ali": ("ali", 60, 10.0),
    "k-ayse": ("ayse", 60, 10.0),
    "k-hiz": ("hiz", 5, 0.5),  # hiz siniri icin dar kova
}
KOVALAR = {}  # kullanici -> KovaSinirlayici
GUNLUK = []  # her yanit icin bir JSON satiri
```

Şemalar, İHA ve görev için kabul edilen alanları, türleri ve sınırları tanımlar. `ad` alanı yalnızca harf, rakam ve tire kabul eder; böylece adı bir biçim dizgisine ya da yola yerleştirmenin yolu kapanır. `tip` ve `durum` ise numaralandırmadır: bilinmeyen değer 422 ile reddedilir.

```python

IHA_SEMA = {
    "type": "object",
    "required": ["ad", "tip"],
    "additionalProperties": False,
    "properties": {
        "ad": {
            "type": "string",
            "minLength": 2,
            "maxLength": 32,
            "pattern": "^[A-Za-z0-9-]+$",
        },
        "tip": {"enum": ["sabit_kanat", "dortrotor"]},
        "durum": {"enum": ["hazir", "ucuyor", "bakimda"]},
    },
}
GOREV_SEMA = {
    "type": "object",
    "required": ["hedef", "irtifa_m"],
    "additionalProperties": False,
    "properties": {
        "hedef": {"type": "string", "minLength": 1, "maxLength": 64},
        "irtifa_m": {
            "type": "integer",
            "minimum": 0,
            "maximum": 5000,
        },
    },
}

```

Veritabanı şeması üç tablo kurar: `iha` (sahip, ad, tip, durum; sahip ve ad birlikte benzersiz), `gorev` (bir İHA'ya bağlı) ve `idem` (idempotentlik kayıtları). Bu şema Bölüm 34'teki tablo tasarımının küçük bir uygulamasıdır: yabancı anahtar (`iha_id`) ilişkiyi, bileşik benzersizlik kısıtı ise kuralı veritabanına yazar. `DB` modül düzeyinde tek bir bağlantıdır; sunucu tek iş parçacıklı olduğu için bu güvenlidir.

```python

def veritabani_kur():
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.executescript("""
        CREATE TABLE iha (
            id INTEGER PRIMARY KEY,
            sahip TEXT NOT NULL,
            ad TEXT NOT NULL,
            tip TEXT NOT NULL,
            durum TEXT NOT NULL,
            UNIQUE (sahip, ad)
        );
        CREATE TABLE gorev (
            id INTEGER PRIMARY KEY,
            iha_id INTEGER NOT NULL REFERENCES iha(id),
            hedef TEXT NOT NULL,
            irtifa_m INTEGER NOT NULL
        );
        CREATE TABLE idem (
            sahip TEXT NOT NULL,
            anahtar TEXT NOT NULL,
            ozet TEXT NOT NULL,
            konum TEXT NOT NULL,
            govde TEXT NOT NULL,
            PRIMARY KEY (sahip, anahtar)
        );
    """)
    return db


DB = veritabani_kur()


class Red(Exception):
    """Isleyiciyi erken bitirir; tasidigi sonuc yanit olarak gider."""

    def __init__(self, sonuc):
        super().__init__()
        self.sonuc = sonuc
```

`Red` istisnası, bir işleyicinin erken çıkışını taşır: gövde ayrıştırılamadığında ya da bir yol kuralı tutmadığında, yanıt doğrudan bu istisnanın içinden gönderilir. `ok` ve `hata` yardımcıları, yanıtı üç bileşenli bir demete çevirir: durum kodu, gövde (ya da `None`), ek başlıklar ve medya türü. Bu düzen, yanıt biçimini tek bir yerde toplar. Hata gövdesi, 40.4'te anlattığımız RFC 9457 alanlarını taşır.

```python


def ok(durum, nesne=None, ek=None):
    return (durum, nesne, ek or {}, "application/json")


def hata(durum, baslik, ayrinti, ek=None, tip="about:blank", **alan):
    nesne = {
        "type": tip,
        "title": baslik,
        "status": durum,
        "detail": ayrinti,
    }
    nesne.update(alan)
    return (durum, nesne, ek or {}, "application/problem+json")


def izinli_degil(allow):
    return hata(
        405,
        "Yontem izinli degil",
        "desteklenmez",
        ek={"Allow": allow},
    )


def ozet(nesne):
    """Kanonik JSON'un parmak izi: ETag ve idempotentlik icin."""
    kanon = json.dumps(
        nesne,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(kanon.encode("utf-8")).hexdigest()[:16]


def etag(nesne):
    return '"%s"' % ozet(nesne)
```

ETag yardımcıları, kaynağın kanonik JSON gösterimini (anahtarlar sıralı, boşluksuz) SHA-256 ile özetler. Aynı kaynak her zaman aynı ETag'i üretir ve kaynak değiştiğinde ETag de değişir. İmleç fonksiyonları ise son kaydın kimliğini opak bir dizgeye kodlar ve çözer. `govde_al`, bozuk JSON için 400, JSON nesnesi olmayan bir gövde için 422 döndürür; bu, 40.4'teki ayrımın kodudur.

```python


def imlec_kodla(son_id):
    ham = json.dumps({"son": son_id}).encode("utf-8")
    return urlsafe_b64encode(ham).decode("ascii")


def imlec_coz(imlec):
    return json.loads(urlsafe_b64decode(imlec))["son"]


def govde_al(ham):
    try:
        nesne = json.loads(ham.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise Red(hata(400, "Hatali JSON", str(e)))
    if not isinstance(nesne, dict):
        raise Red(
            hata(
                422,
                "Dogrulama hatasi",
                "nesne bekleniyordu",
                tip="/hatalar/dogrulama",
            )
        )
    return nesne


def dogrula(sema, nesne):
    hatalar = []
    for e in jsonschema.Draft202012Validator(sema).iter_errors(nesne):
        yol = "/".join(str(p) for p in e.path) or "(kok)"
        hatalar.append({"alan": yol, "mesaj": e.message})
    return sorted(hatalar, key=lambda h: (h["alan"], h["mesaj"]))

```

Doğrulama, şemanın tüm hatalarını toplar ve alan yoluna göre sıralar. `iter_errors` tüm ihlalleri üretir, yalnızca ilkini değil; bu sayede istemci tek seferde bütün sorunları görebilir. İlk hata yerine tüm listeyi döndürmek, bir sözleşme tasarım tercihidir.

```python

def dogrulama_hatasi(hatalar):
    return hata(
        422,
        "Dogrulama hatasi",
        "%d alan" % len(hatalar),
        tip="/hatalar/dogrulama",
        hatalar=hatalar,
    )


def iha_getir(kul, iha_id):
    """Sahiplik filtresi: baskasinin kaydi 'yok' gibi davranir."""
    satir = DB.execute(
        "SELECT ad, tip, durum FROM iha WHERE id = ? AND sahip = ?",
        (iha_id, kul),
    ).fetchone()
    if satir is None:
        return None
    return {
        "id": iha_id,
        "ad": satir[0],
        "tip": satir[1],
        "durum": satir[2],
    }

```

`iha_getir` sahiplik filtresinin merkezidir: `WHERE id = ? AND sahip = ?`. Başkasına ait kayıt, bu sorguda hiç bulunmaz ve `None` döner. Böylece her çağıran fonksiyon, "yok" durumunu tek bir yerden alır ve sahiplik kuralını ayrıca düşünmek zorunda kalmaz.

```python

def ihalari_listele(kul, sorgu):
    try:
        boyut = min(int(sorgu.get("limit", ["2"])[0]), 50)
        imlec = sorgu.get("imlec", [None])[0]
        son = imlec_coz(imlec) if imlec else 0
    except (ValueError, KeyError, json.JSONDecodeError):
        return hata(400, "Gecersiz sorgu", "imlec ya da limit")
    rows = DB.execute(
        "SELECT id, ad, tip, durum FROM iha "
        "WHERE sahip = ? AND id > ? ORDER BY id ASC LIMIT ?",
        (kul, son, boyut + 1),
    ).fetchall()  # bir fazla: devam var mi?
    veri = [
        {
            "id": r[0],
            "ad": r[1],
            "tip": r[2],
            "durum": r[3],
            "href": "/ihalar/%d" % r[0],
        }
        for r in rows[:boyut]
    ]
    sonraki = None
    if len(rows) > boyut:
        sonraki = imlec_kodla(rows[boyut - 1][0])
    return ok(200, {"veri": veri, "sonraki_imlec": sonraki})

```

Listeleme, imleç sayfalamasının uygulamasıdır. `id > son` koşulu, imleçten sonraki kayıtları verir. Sorgu `boyut + 1` kayıt çeker: bir fazla kayıt varsa sonraki sayfa vardır ve imleç, son döndürülen kaydın kimliğinden üretilir. Bu teknik, boş bir son sayfa döndürme sorununu önler.

```python

def ihalari_olustur(kul, govde, anahtar):
    hatalar = dogrula(IHA_SEMA, govde)
    if hatalar:
        return dogrulama_hatasi(hatalar)
    ozeti = ozet(govde)
    if anahtar:
        eski = DB.execute(
            "SELECT ozet, konum, govde FROM idem "
            "WHERE sahip = ? AND anahtar = ?",
            (kul, anahtar),
        ).fetchone()
        if eski is not None:
            if eski[0] != ozeti:
                return hata(
                    422,
                    "Idempotency-Key yeniden kullanildi",
                    "farkli govde",
                )
            return ok(
                201,
                json.loads(eski[2]),
                ek={
                    "Location": eski[1],
                    "Idempotent-Replayed": "true",
                },
            )
    try:
        cur = DB.execute(
            "INSERT INTO iha (sahip, ad, tip, durum) "
            "VALUES (?, ?, ?, ?)",
            (
                kul,
                govde["ad"],
                govde["tip"],
                govde.get("durum", "hazir"),
            ),
        )
    except sqlite3.IntegrityError:
        return hata(409, "Cakisma", "bu ad zaten kayitli")
```

Oluşturma fonksiyonu üç kararı birleştirir. Önce doğrulama yapılır. Sonra `Idempotency-Key` varsa daha önce kaydedilmiş bir işlem olup olmadığına bakılır: özet aynıysa kayıtlı yanıt döner, farklıysa 422. Yeni kayıt, `UNIQUE` kısıtı ihlal edilirse 409 ile reddedilir. Başarılı oluşturmada `Location` ve `ETag` başlıkları döner, anahtar da kaydedilir.

```python
    nesne = iha_getir(kul, cur.lastrowid)
    konum = "/ihalar/%d" % nesne["id"]
    if anahtar:
        DB.execute(
            "INSERT INTO idem VALUES (?, ?, ?, ?, ?)",
            (kul, anahtar, ozeti, konum, json.dumps(nesne)),
        )
    DB.commit()
    return ok(201, nesne, ek={"Location": konum, "ETag": etag(nesne)})


def iha_goster(kul, iha_id):
    nesne = iha_getir(kul, iha_id)
    if nesne is None:
        return hata(404, "Bulunamadi", "iha yok")
    return ok(200, nesne, ek={"ETag": etag(nesne)})

```

Okuma fonksiyonu, varsa ETag'i yanıta ekler. Bu değer, sonraki bir güncelleme için `If-Match` olarak geri gönderilmelidir.

```python

def iha_guncelle(kul, iha_id, if_match, govde, kismi):
    mevcut = iha_getir(kul, iha_id)
    if mevcut is None:
        return hata(404, "Bulunamadi", "iha yok")
    if if_match is None:
        return hata(428, "Onkosul gerekli", "If-Match basligi yok")
    if if_match != etag(mevcut):
        return hata(
            412,
            "Onkosul basarisiz",
            "kayit degismis; once GET ile yeniden okuyun",
            ek={"ETag": etag(mevcut)},
        )
    if kismi:  # PATCH: yalnizca gonderilen alanlar
        yeni = {
            "ad": mevcut["ad"],
            "tip": mevcut["tip"],
            "durum": mevcut["durum"],
        }
        yeni.update(govde)
    else:  # PUT: tam nesne, eksik durum varsayilan
        yeni = {"durum": "hazir", **govde}
    hatalar = dogrula(IHA_SEMA, yeni)
    if hatalar:
        return dogrulama_hatasi(hatalar)
    try:
        DB.execute(
            "UPDATE iha SET ad = ?, tip = ?, durum = ? "
            "WHERE id = ? AND sahip = ?",
            (yeni["ad"], yeni["tip"], yeni["durum"], iha_id, kul),
        )
    except sqlite3.IntegrityError:
        return hata(409, "Cakisma", "bu ad zaten kayitli")
    DB.commit()
    nesne = iha_getir(kul, iha_id)
    return ok(200, nesne, ek={"ETag": etag(nesne)})

```

Güncelleme fonksiyonu, sıralamasıyla dikkat çeker. Önce kaynağın varlığı ve sahipliği denetlenir (404). Sonra `If-Match` yoksa 428, yanlışsa 412 döner. Ancak bundan sonra gövde işlenir. PUT tam nesne bekler, PATCH ise mevcut değerlerin üzerine yalnızca gönderilen alanları yazar. Sonuç, yine şemayla doğrulanır ve yalnızca tutarlı ise veritabanına yazılır. Yeni ETag, güncellenmiş kaydın özetinden üretilir.

```python

def iha_sil(kul, iha_id, if_match):
    mevcut = iha_getir(kul, iha_id)
    if mevcut is None:
        return hata(404, "Bulunamadi", "iha yok")
    if if_match is None:
        return hata(428, "Onkosul gerekli", "If-Match basligi yok")
    if if_match != etag(mevcut):
        return hata(
            412,
            "Onkosul basarisiz",
            "kayit degismis",
            ek={"ETag": etag(mevcut)},
        )
    DB.execute("DELETE FROM gorev WHERE iha_id = ?", (iha_id,))
    DB.execute(
        "DELETE FROM iha WHERE id = ? AND sahip = ?", (iha_id, kul)
    )
    DB.commit()
    return ok(204)


def gorevleri_listele(kul, iha_id):
    if iha_getir(kul, iha_id) is None:
        return hata(404, "Bulunamadi", "iha yok")
    rows = DB.execute(
        "SELECT id, hedef, irtifa_m FROM gorev "
        "WHERE iha_id = ? ORDER BY id",
        (iha_id,),
    ).fetchall()
    veri = [
        {"id": r[0], "hedef": r[1], "irtifa_m": r[2]} for r in rows
    ]
    return ok(200, {"veri": veri})

```

Silme, aynı ETag kontrolünü kullanır: `If-Match` olmadan silinmez. Bir İHA silindiğinde bağlı görevler de silinir; bu, yabancı anahtar kısıtı olmadan kodla yapılan bir kaskad silmedir. Başarılı silme 204 döner ve gövde göndermez; bu yüzden `_gonder` fonksiyonu 204'te `Content-Length` başlığını yazmaz.

```python

def gorev_olustur(kul, iha_id, govde):
    if iha_getir(kul, iha_id) is None:
        return hata(404, "Bulunamadi", "iha yok")
    hatalar = dogrula(GOREV_SEMA, govde)
    if hatalar:
        return dogrulama_hatasi(hatalar)
    cur = DB.execute(
        "INSERT INTO gorev (iha_id, hedef, irtifa_m) "
        "VALUES (?, ?, ?)",
        (iha_id, govde["hedef"], govde["irtifa_m"]),
    )
    DB.commit()
    konum = "/ihalar/%d/gorevler/%d" % (iha_id, cur.lastrowid)
    return ok(
        201, {"id": cur.lastrowid, **govde}, ek={"Location": konum}
    )


class Istek(BaseHTTPRequestHandler):
    server_version = "IHAFilo/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass  # varsayilan stderr logunu kapat

    def do_GET(self):
        self._isle()

    do_POST = do_PUT = do_PATCH = do_DELETE = do_GET
```

Görev uç noktaları, alt koleksiyonun iki yöntemini uygular. Her ikisi de önce İHA'nın sahipliğini denetler; görev oluşturma gövdeyi `GOREV_SEMA` ile doğrular ve `201` ile `Location` döner.

```python

def gorev_olustur(kul, iha_id, govde):
    if iha_getir(kul, iha_id) is None:
        return hata(404, "Bulunamadi", "iha yok")
    hatalar = dogrula(GOREV_SEMA, govde)
    if hatalar:
        return dogrulama_hatasi(hatalar)
    cur = DB.execute(
        "INSERT INTO gorev (iha_id, hedef, irtifa_m) "
        "VALUES (?, ?, ?)",
        (iha_id, govde["hedef"], govde["irtifa_m"]),
    )
    DB.commit()
    konum = "/ihalar/%d/gorevler/%d" % (iha_id, cur.lastrowid)
    return ok(
        201, {"id": cur.lastrowid, **govde}, ek={"Location": konum}
    )


```

`Istek` sınıfı `BaseHTTPRequestHandler`'dan türer. `protocol_version = "HTTP/1.1"` satırı kalıcı bağlantıyı etkinleştirir (Bölüm 30.8). `do_GET` ve diğer yöntemler aynı `_isle` fonksiyonuna yönlenir; yöntem ayrımı orada yapılır. Günlüğü kapatmak için `log_message` boş bırakıldı; kendi JSON günlüğümüz var.

```python
class Istek(BaseHTTPRequestHandler):
    server_version = "IHAFilo/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass  # varsayilan stderr logunu kapat

    def do_GET(self):
        self._isle()

    do_POST = do_PUT = do_PATCH = do_DELETE = do_GET

    def _isle(self):
        self.istek_id = (
            self.headers.get("X-Request-ID") or uuid.uuid4().hex
        )
        uz = int(self.headers.get("Content-Length") or 0)
        if uz > 4096:
            self.close_connection = True  # govdeyi okumadan kapat
            return self._gonder(
                hata(413, "Govde cok buyuk", "en fazla 4096 bayt")
            )
        ham = self.rfile.read(uz) if uz else b""
        try:
            sonuc = self._yonlendir(ham)
        except Red as r:
            sonuc = r.sonuc
        self._gonder(sonuc)

```

`_isle` önce istek kimliğini belirler ve gövde boyutunu denetler. 4096 bayttan büyük bir gövde okunmadan 413 ile reddedilir ve bağlantı kapatılır; bu, bellek tüketimini sınırlar. Gövde küçükse okunur ve `_yonlendir`'e verilir; `Red` istisnası ile erken çıkılabilir. Kritik nokta: gövde her durumda okunmalıdır, çünkü HTTP/1.1 kalıcı bağlantıda okunmamış bayt bir sonraki isteği bozar.

```python
    def _yonlendir(self, ham):
        kayit = ANAHTARLAR.get(self.headers.get("X-Api-Key") or "")
        if kayit is None:
            return hata(
                401,
                "Kimlik dogrulanamadi",
                "gecerli X-Api-Key gerekli",
                ek={"WWW-Authenticate": 'ApiKey realm="ihafilo"'},
            )
        kul, kapasite, hiz = kayit
        kova = KOVALAR.setdefault(kul, KovaSinirlayici(kapasite, hiz))
        izin, bekle = kova.izin_ver(time.monotonic())
        if not izin:
            return hata(
                429,
                "Cok fazla istek",
                "hiz siniri asildi",
                ek={"Retry-After": str(math.ceil(bekle))},
            )
        yol = urlparse(self.path)
        p = [s for s in yol.path.split("/") if s]
        q = parse_qs(yol.query)
        m = self.command
        if p == ["ihalar"]:
            if m == "GET":
                return ihalari_listele(kul, q)
            if m == "POST":
                return ihalari_olustur(
                    kul,
                    govde_al(ham),
                    self.headers.get("Idempotency-Key"),
                )
```

`_yonlendir` önce anahtarı kullanıcıya çevirir; anahtar yoksa 401 döner. Sonra kullanıcının kovasından bir jeton ister; yoksa 429 ve `Retry-After` döner. Ardından yolu parçalara ayırır ve kalıbı eşleştirir.

```python
            return izinli_degil("GET, POST")
        if len(p) == 2 and p[0] == "ihalar" and p[1].isdigit():
            i = int(p[1])
            if m == "GET":
                return iha_goster(kul, i)
            if m in ("PUT", "PATCH"):
                return iha_guncelle(
                    kul,
                    i,
                    self.headers.get("If-Match"),
                    govde_al(ham),
                    m == "PATCH",
                )
            if m == "DELETE":
                return iha_sil(kul, i, self.headers.get("If-Match"))
            return izinli_degil("GET, PUT, PATCH, DELETE")
        if (
            len(p) == 3
            and p[0] == "ihalar"
            and p[1].isdigit()
            and p[2] == "gorevler"
        ):
            i = int(p[1])
            if m == "GET":
                return gorevleri_listele(kul, i)
            if m == "POST":
                return gorev_olustur(kul, i, govde_al(ham))
            return izinli_degil("GET, POST")
        return hata(
            404, "Bulunamadi", "yol tanimli degil: %s" % yol.path
        )

```

Yol eşleştirmesi bilinçli olarak açıktır: her yol için hangi yöntemlerin desteklendiği yazılıdır ve desteklenmeyenler `Allow` başlığıyla 405 döner. Hiçbir kalıp tutmazsa 404 döner.

```python
    def _gonder(self, sonuc):
        durum, nesne, ek, tur = sonuc
        govde = b""
        if nesne is not None:
            govde = json.dumps(nesne, ensure_ascii=False).encode(
                "utf-8"
            )
        self.send_response(durum)
        if govde:
            self.send_header("Content-Type", tur + "; charset=utf-8")
        if durum != 204:  # RFC 9110: 204'te Content-Length yok
            self.send_header("Content-Length", str(len(govde)))
        self.send_header("X-Request-ID", self.istek_id)
        for ad, deger in ek.items():
            self.send_header(ad, deger)
        self.end_headers()
        if govde:
            self.wfile.write(govde)
        GUNLUK.append(
            json.dumps(
                {
                    "olay": "istek",
                    "yontem": self.command,
                    "yol": self.path,
                    "durum": durum,
                    "istek_id": self.istek_id,
                },
                ensure_ascii=False,
            )
        )


```

`_gonder` yanıtı yazar ve günlüğe bir satır ekler. Başlık sırası önemlidir: önce `send_response` ile durum, sonra içerik başlıkları, sonra ek başlıklar, en sonunda `end_headers`. Gövde yalnızca varsa yazılır; 204'te `Content-Length` yazılmaz.

```python
if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    HTTPServer(("127.0.0.1", port), Istek).serve_forever()
```

Modül doğrudan çalıştırıldığında belirtilen bir portta (varsayılan 8080) yalnızca `127.0.0.1` üzerinde dinler. Bu bilinçli bir seçimdir: demo, dış ağa açılmaz.

Sunucuyu sınamak için bir istemci yazıyoruz. Bu istemci, gerçek HTTP isteklerini `urllib` ile gönderir; sunucuyu aynı süreçte, bir iş parçacığında, geçici bir portta başlatır. Her adım bir isteğin yanıtını ve önemli başlıklarını yazdırır.

```python
# -*- coding: utf-8 -*-
"""b40_7_istemci.py: API'yi gercek HTTP istekleriyle sinar.

Sunucu ayni surecte bir is parcacigi olarak, 127.0.0.1 uzerinde,
gecici bir portta calisir. Her adim bir HTTP istegidir (urllib).
"""

import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer

import b40_6_ihafilo_api as api

TABAN = ""
SAYAC = [0]

```

```python

def istek(
    yontem, yol, anahtar="k-ali", govde=None, ham=None, ek=None
):
    basliklar = {"X-Api-Key": anahtar} if anahtar else {}
    SAYAC[0] += 1
    basliklar["X-Request-ID"] = "t%03d" % SAYAC[0]
    veri = ham
    if govde is not None:
        veri = json.dumps(govde).encode("utf-8")
    if veri is not None:
        basliklar["Content-Type"] = "application/json"
    basliklar.update(ek or {})
    req = urllib.request.Request(
        TABAN + yol, data=veri, method=yontem, headers=basliklar
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return (
                r.status,
                {k.lower(): v for k, v in r.headers.items()},
                r.read(),
            )
    except urllib.error.HTTPError as e:
        return (
            e.code,
            {k.lower(): v for k, v in e.headers.items()},
            e.read(),
        )

```

`istek` fonksiyonu, her isteğe bir `X-Request-ID` ekler (sayaçla üretilir, böylece çıktı her çalıştırmada aynıdır). HTTP hatalarını (4xx, 5xx) istisna olarak değil, normal bir yanıt olarak döndürür; böylece her adımda durum kodunu aynı biçimde yazdırabiliriz. Bu, `urllib`'in davranışının kullanımıdır: `HTTPError` yakalanır ve yanıt olarak paketlenir.

```python

def goster(ad, sonuc):
    durum, basl, govde = sonuc
    print("%-28s %d" % (ad, durum))
    ilgili = []
    for alan, ad_ in (
        ("location", "Location"),
        ("etag", "ETag"),
        ("retry-after", "Retry-After"),
        ("allow", "Allow"),
        ("www-authenticate", "WWW-Authenticate"),
        ("idempotent-replayed", "Idempotent-Replayed"),
    ):
        if alan in basl:
            ilgili.append("%s=%s" % (ad_, basl[alan]))
    if ilgili:
        print("      " + " ".join(ilgili))
    if durum >= 400 and govde:
        p = json.loads(govde)
        print("      %s: %s" % (p["title"], p["detail"]))
        for h in p.get("hatalar", []):
            print("      - %s: %s" % (h["alan"], h["mesaj"]))


def json_al(sonuc):
    return json.loads(sonuc[2]) if sonuc[2] else None


if __name__ == "__main__":
    srv = HTTPServer(("127.0.0.1", 0), api.Istek)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    TABAN = "http://127.0.0.1:%d" % srv.server_address[1]
```

`goster` fonksiyonu bir adımın durum kodunu ve ilgili başlıkları yazdırır. Hata gövdesi varsa, başlığını ve hatalarını da yazar. Bu, istemcinin sunucunun sözleşmesini gerçekten okuduğunu gösterir.

```python

    print("1. Idempotent olusturma")
    s = istek(
        "POST",
        "/ihalar",
        govde={"ad": "ALFA-1", "tip": "sabit_kanat"},
        ek={"Idempotency-Key": "siparis-1"},
    )
    goster("POST /ihalar", s)
    s = istek(
        "POST",
        "/ihalar",
        govde={"ad": "ALFA-1", "tip": "sabit_kanat"},
        ek={"Idempotency-Key": "siparis-1"},
    )
    goster("POST /ihalar (ayni anahtar)", s)
    s = istek(
        "POST",
        "/ihalar",
        govde={"ad": "BETA-2", "tip": "dortrotor"},
        ek={"Idempotency-Key": "siparis-1"},
    )
    goster("POST (anahtar, farkli govde)", s)
    print(
        "   kayit sayisi:",
        len(api.DB.execute("SELECT * FROM iha").fetchall()),
    )
```

Ana bölüm sunucuyu başlatır ve senaryonun ilk adımlarını çalıştırır. Birinci adımda aynı `Idempotency-Key` ile iki POST gönderilir; ikincisi yeni kayıt oluşturmaz. Üçüncü istek aynı anahtarla farklı gövde gönderir ve 422 alır.

```python

    print("2. Girdi hatalari")
    goster(
        "POST gecersiz alanlar",
        istek(
            "POST", "/ihalar", govde={"ad": "X", "tip": "helikopter"}
        ),
    )
    goster(
        "POST bozuk JSON", istek("POST", "/ihalar", ham=b'{"ad": ')
    )
    goster(
        "POST ayni ad (409)",
        istek(
            "POST",
            "/ihalar",
            govde={"ad": "ALFA-1", "tip": "dortrotor"},
        ),
    )
```

İkinci adım girdi hatalarını sınar: geçersiz alanlar (422 ve alan listesi), bozuk JSON (400), ve aynı ad (409).

```python

    print("3. Kosullu guncelleme (ETag)")
    s = istek("GET", "/ihalar/1")
    goster("GET /ihalar/1", s)
    e1 = s[1]["etag"]
    goster(
        "PUT If-Match yok",
        istek(
            "PUT",
            "/ihalar/1",
            govde={"ad": "ALFA-1", "tip": "dortrotor"},
        ),
    )
    goster(
        "PUT yanlis If-Match",
        istek(
            "PUT",
            "/ihalar/1",
            govde={"ad": "ALFA-1", "tip": "dortrotor"},
            ek={"If-Match": '"0000000000000000"'},
        ),
    )
    s = istek(
        "PUT",
        "/ihalar/1",
        govde={"ad": "ALFA-1", "tip": "dortrotor"},
        ek={"If-Match": e1},
    )
    goster("PUT dogru If-Match", s)
    e2 = s[1]["etag"]
    goster(
        "PATCH eski ETag",
        istek(
            "PATCH",
            "/ihalar/1",
            govde={"durum": "ucuyor"},
            ek={"If-Match": e1},
        ),
    )
    goster(
```

Üçüncü adım, ETag akışını sınar. İlk GET ETag'i alır; `If-Match` olmadan PUT 428 döner; yanlış ETag 412 döner; doğru ETag güncellemeyi yapar ve yeni bir ETag verir. Eski ETag ile PATCH 412 döner, güncel ile 200 döner.

```python
        "PATCH guncel ETag",
        istek(
            "PATCH",
            "/ihalar/1",
            govde={"durum": "ucuyor"},
            ek={"If-Match": e2},
        ),
    )
    e3 = istek("GET", "/ihalar/1")[1]["etag"]

    print("4. Sahiplik: ayse, ali'nin kaydina erisemez")
    goster(
        "GET /ihalar/1 (ayse)", istek("GET", "/ihalar/1", "k-ayse")
    )
    goster(
        "DELETE /ihalar/1 (ayse)",
        istek("DELETE", "/ihalar/1", "k-ayse", ek={"If-Match": e3}),
    )

    print("5. Imlecli sayfalama (limit=2)")
    for ad in ("BRAVO-3", "CHARLIE-4", "DELTA-5"):
        istek(
            "POST", "/ihalar", govde={"ad": ad, "tip": "sabit_kanat"}
        )
    s = istek("GET", "/ihalar?limit=2")
    sayfa1 = json_al(s)
    print("   sayfa 1:", [v["ad"] for v in sayfa1["veri"]])
    s = istek(
        "GET", "/ihalar?limit=2&imlec=" + sayfa1["sonraki_imlec"]
    )
    sayfa2 = json_al(s)
    print(
        "   sayfa 2:",
        [v["ad"] for v in sayfa2["veri"]],
        "sonraki:",
        sayfa2["sonraki_imlec"],
    )
```

Dördüncü adım sahipliği sınar: `ayse` kullanıcısı `ali`'nin kaydını göremez ve silemez; ikisi de 404 döner. Beşinci adım, imleç sayfalamasını üç ek kayıtla sınar. Altıncı adım alt kaynağı ve yanlış yöntemi (405 ve `Allow`) ve gövde boyutu sınırını (413) sınar.

```python

    print("6. Alt kaynak ve yontem")
    s = istek(
        "POST",
        "/ihalar/1/gorevler",
        govde={"hedef": "sinir-hatti-A", "irtifa_m": 120},
    )
    goster("POST /ihalar/1/gorevler", s)
    goster(
        "GET  /ihalar/1/gorevler", istek("GET", "/ihalar/1/gorevler")
    )
    goster(
        "PUT  /ihalar (koleksiyon)", istek("PUT", "/ihalar", govde={})
    )
    goster(
        "POST 5000 bayt govde",
        istek("POST", "/ihalar", ham=b"x" * 5000),
    )

    print("7. Hiz siniri (kapasite 5, 0,5 jeton/s)")
    for _ in range(7):
        s = istek("GET", "/ihalar", "k-hiz")
        goster("GET /ihalar (hiz)", s)

    print("8. Kimliksiz istek ve silme")
    goster(
        "GET /ihalar (anahtarsiz)",
        istek("GET", "/ihalar", anahtar=None),
    )
    goster(
        "DELETE /ihalar/1 (ali)",
        istek("DELETE", "/ihalar/1", ek={"If-Match": e3}),
    )
    goster("GET /ihalar/1 (silindi)", istek("GET", "/ihalar/1"))
```

Yedinci adım hız sınırını sınar. `hiz` kullanıcısının kovası beş kapasiteli ve saniyede yarım jetonludur; yedi hızlı istekten beşi geçer, ikisi 429 ile reddedilir ve `Retry-After` değeri bir sonraki jetonun kaç saniye sonra geleceğini söyler. Sekizinci adım kimliksiz isteği ve silmeyi sınar. Dokuzuncu adım, sunucu günlüğünün son iki satırını yazar.

```python

    srv.shutdown()
    print("9. Gunluk son satirlar")
    for satir in api.GUNLUK[-2:]:
        k = json.loads(satir)
        print(
            "  %s %s -> %d (istek_id=%s)"
            % (k["yontem"], k["yol"], k["durum"], k["istek_id"])
        )
```

İstemci ve sunucu şu sırayla çalışır: önce sunucu bir iş parçacığında başlar, sonra istemci adımları sırayla gönderir ve her yanıtı yazdırır. Çıktı, kodun ürettiği gerçek çıktıdır ve iki kez çalıştırıldığında birebir aynıdır:

```term
$ python b40_7_istemci.py
1. Idempotent olusturma
POST /ihalar                 201
      Location=/ihalar/1 ETag="a02112d960b174f0"
POST /ihalar (ayni anahtar)  201
      Location=/ihalar/1 Idempotent-Replayed=true
POST (anahtar, farkli govde) 422
      Idempotency-Key yeniden kullanildi: farkli govde
   kayit sayisi: 1
2. Girdi hatalari
POST gecersiz alanlar        422
      Dogrulama hatasi: 2 alan
      - ad: 'X' is too short
      - tip: 'helikopter' is not one of ['sabit_kanat', 'dortrotor']
POST bozuk JSON              400
      Hatali JSON: Expecting value: line 1 column 8 (char 7)
POST ayni ad (409)           409
      Cakisma: bu ad zaten kayitli
3. Kosullu guncelleme (ETag)
GET /ihalar/1                200
      ETag="a02112d960b174f0"
PUT If-Match yok             428
      Onkosul gerekli: If-Match basligi yok
PUT yanlis If-Match          412
      ETag="a02112d960b174f0"
      Onkosul basarisiz: kayit degismis; once GET ile yeniden okuyun
PUT dogru If-Match           200
      ETag="baf639db873eda8f"
PATCH eski ETag              412
      ETag="baf639db873eda8f"
      Onkosul basarisiz: kayit degismis; once GET ile yeniden okuyun
PATCH guncel ETag            200
      ETag="01c45672efc975dd"
4. Sahiplik: ayse, ali'nin kaydina erisemez
GET /ihalar/1 (ayse)         404
      Bulunamadi: iha yok
DELETE /ihalar/1 (ayse)      404
      Bulunamadi: iha yok
```

Beşinci adımdan sonraki çıktı:

```term
$ | py7b
```

Bu çıktıyı okurken her satırın bir sözleşme maddesini sınadığını düşün. Birinci adımdaki `Idempotent-Replayed=true` başlığı, sunucunun aynı kaydı iki kez yazmadığının kanıtıdır; hemen ardından gelen `kayit sayisi: 1` satırı bunu doğrular. Üçüncü adımdaki 412 yanıtının `ETag` başlığı, istemciye güncel sürümü söyler; istemci bu değerle yeniden deneyebilir. Altıncı adımdaki 413 ise gövdenin hiç ayrıştırılmadığını gösterir: sunucu 5000 baytı okumadan reddetti.

Bu uygulamada kasıtlı olarak bulunmayan şeyler de var: sunucu tek iş parçacıklıdır, veriler bellektedir ve test anahtarları koddadır. Bunlar bir demo sınırıdır, bir tasarım hatası değildir. Gerçek bir sistemde her birinin yerine ne geçeceğini Kendin Yap bölümündeki projelerde düşüneceksin.

## 40.13 Gerçek dünya bağlamı: EV Dashboard ve gömülü sürücü API'leri

İHA filo API'si bir ağ API'siydi. Aynı tasarım kararları, Mert'in projelerindeki iki yere de uygulanır.

**EV Dashboard telemetri API'si.** Bir elektrikli araç panelinin sensör verisini (sıcaklık, akım, gerilim) bir sunucuya taşıyan bir hat düşünelim. Burada üç karar öne çıkar. Birincisi, ölçüm akışı için tek bir `POST` ile tek tek ölçüm göndermek yerine toplu gönderim (batch) yapılır; böylece her ölçüm için bir bağlantı ve başlık maliyeti ödenmez. İkincisi, ölçümler zaman damgasıyla değil sıra numarasıyla tanımlanır; ağ sıra dışı teslim edebilir ve sunucu, yinelenen ölçümleri sıra numarasıyla atabilir (bu bir idempotentlik anahtarının telemetri biçimidir). Üçüncüsü, düşük bant genişliğinde protobuf gibi ikili bir biçim (40.10) ya da sıkıştırılmış JSON tercih edilir. Bu kararların hiçbiri "en iyi" değildir; her biri bir ödünleşimdir ve tasarım belgesinde yazılmalıdır.

**Gömülü sürücü API'si.** Bir STM32 üzerinde çalışan bir sıcaklık sensörü sürücüsü, bir C kütüphanesidir ve bu bölümde yazdığımız ABI kuralları aynen geçerlidir. Sürücü, opak bir tanıtıcı (handle) döndürmeli; yapının alanlarını kullanıcıya açmamalı; boyutu bir fonksiyonla sorgulatmalı; hata kodlarını bir `enum` olarak tanımlamalı. Bölüm 21.9'da gördüğün `struct file_operations` örneği de aynı fikri, bir fonksiyon işaretçisi tablosuyla uygular: sürücü hangi işlemleri desteklediğini tabloda belirtir, desteklemediklerinde `NULL` bırakır. Bu tasarım, çekirdeğin yeni işlemler eklemesini eski sürücüleri kırmadan mümkün kılar.

Bu iki örneğin ortak noktası, API'nin bir sözleşme olduğu ve sözleşmenin üretim ortamında kırılmadan evrilebilmesi gerektiğidir. Bir sistemin yirmi yıl ayakta kalması, bu evrilebilirliğin kodda ve belgede ne kadar iyi kurulduğuna bağlıdır.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, Bölüm 5'teki altı adımlı çözüm yöntemini izler: Anla, Örnekle, Kaba çöz, Örüntü, İyileştir, Doğrula. Doğrulama adımında her örnek elle iz sürme tablosu kullanır; program çıktısı yerine kendi hesabını tabloyla karşılaştırmak, bu bölümün asıl amacıdır.

### Örnek 1 (★): Bir görev listesi için doğru yöntem ve durum kodu

**Problem.** Bir İHA'nın görev listesi için bir API yazıyorsun. Aşağıdaki altı işlemin her biri için uygun yöntemi ve durum kodunu seç: (a) yeni bir görev ekleme, (b) var olmayan bir İHA'ya görev ekleme, (c) bir görevi silme, (d) silinmiş bir görevi tekrar silme, (e) görev gövdesini eksik alanla gönderme, (f) başka kullanıcının İHA'sının görevlerini listeleme.

**Adım 1 — Anla.** Her işlemin iki sorusu var: hangi yöntem bu niyeti taşır, ve sunucu hangi sonucu bildirmeli? Yöntem niyetten, durum kodu sonuçtan gelir.

**Adım 2 — Örnekle.** (a) bir kaynak oluşturur. (d) aynı silme isteğinin ikinci kez gelmesidir; yöntem `DELETE`'tir ve idempotenttir. (e) JSON'un biçimi doğru olabilir ama alanlar tanımla uyuşmuyor olabilir.

**Adım 3 — Kaba çöz.** Her satır için yöntem ve kodu ilk tahminle yaz: (a) POST, 200. (b) POST, 500. (c) DELETE, 200. (d) DELETE, 500. (e) POST, 400. (f) GET, 403.

**Adım 4 — Örüntü.** Dört hata bulduk. Birincisi, yeni kaynak için 201 ve `Location` gerekir; 200 yanlış. İkincisi, kaynak yoksa 500 değil 404 gerekir; 500 sunucu hatasıdır, oysa burada istemci bir şey yanlış istemiştir. Üçüncüsü, (e)'de JSON geçerliyse 400 değil 422 gerekir. (f)'de 403 yerine 404 gerekir, çünkü başkasının kaynağının varlığını ifşa etmemek için. Bir de (d)'de ikinci silme için 204 yerine 404 düşünülebilir; ama DELETE idempotenttir, bu yüzden ikinci silmenin sonucu da "kaynak yok" olarak 404 olabilir; bu, tasarım seçimidir ve belgelenmelidir.

**Adım 5 — İyileştir.** Tablonun son hali şöyle: (a) POST, 201 + `Location`. (b) POST, 404. (c) DELETE, 204. (d) DELETE, 404 (belgelenmiş tasarım). (e) POST, 422 ve `hatalar`. (f) GET, 404. Bu tabloyu bir istemcinin davranışına çevirirsek: 404 "yeniden deneme" değil, "bu kaynak yok" demektir; 422 "değerleri düzelt" demektir; 409 ise "durumu düzeltip yeniden dene" demektir.

**Adım 6 — Doğrula.** Her satırı, sorudaki niyetle ve tablonun kuralıyla karşılaştırdık. Elle iz tablosu:

| Satır | Niyet | Yöntem | Kod | Gerekçe | Sonuç |
|---|---|---|---|---|---|
| (a) | Oluştur | POST | 201 | Yeni kaynak, `Location` | Doğru |
| (b) | Olmayan üst kaynak | POST | 404 | İstemci hatası değil, adres yok | Düzeltildi (500 → 404) |
| (c) | Sil | DELETE | 204 | Gövdesiz başarı | Doğru |
| (d) | Yinelenen sil | DELETE | 404 | İdempotent, ama kaynak zaten yok | Tasarım kararı, belgelendi |
| (e) | Eksik alan | POST | 422 | JSON geçerli, anlam yanlış | Düzeltildi (400 → 422) |
| (f) | Başkasının kaynağı | GET | 404 | Varlığı ifşa etme | Düzeltildi (403 → 404) |

Bu tablonun hiçbir satırı tahmin değildir: her biri RFC 9110'un tanımına ya da bu API'nin sahiplik kuralına dayanır.

**Bunu AI'sız yazabilir misin?** Yukarıdaki altı senaryoyu bir kağıda yaz; her biri için yöntemi ve durum kodunu, gerekçesiyle birlikte, önce kendin belirle. Sonra bu bölümdeki tabloyla karşılaştır; farklı çıkan satırın neden farklı çıktığını bir cümleyle açıkla.

### Örnek 2 (★★): Offset sayfalamanın kayan veride kaydı kaçırması

**Problem.** Tabloda 10 kayıt var (id 1'den 10'a). Sayfa boyutu 3, sıralama id'ye göre azalan. İstemci birinci sayfayı okuyor; sonra ikinci sayfayı istemeden önce id 10 siliniyor. İkinci sayfayı offset sayfalamayla ve keyset sayfalamayla alırsak hangi kayıtları görür? Hangi kayıt atlanır?

**Adım 1 — Anla.** Sıralama azalan, yani sayfalar 10, 9, 8, … şeklinde ilerler. Birinci sayfa `[10, 9, 8]`dir. Silme birinci sayfadan sonra olduğu için istemcinin elinde zaten 10 vardır; soru, ikinci sayfanın ne getireceğidir.

**Adım 2 — Örnekle.** Silmeden sonra tablo `9, 8, 7, 6, 5, 4, 3, 2, 1` sırasındadır. Offset sayfalamada ikinci sayfa, `OFFSET 3` ile başlar: yani ilk üç satırı atlar.

**Adım 3 — Kaba çöz.** Offset için: ilk üç satır `9, 8, 7` atlanır, ikinci sayfa `6, 5, 4`. Keyset için: son gören id 8'dir; `id < 8` olan kayıtlar `7, 6, 5`.

**Adım 4 — Örüntü.** Offset, satırları konumla sayar. Silme, sonraki satırların konumunu bir kaydırdığı için, konum 3'teki kayıt (yani 7) bir önceki konuma kayar ve atlanır. Keyset ise satırları değerle sayar; `id < 8` her zaman aynı sonucu verir, silme bunu etkilemez.

**Adım 5 — İyileştir.** Offset'i düzeltmenin yolu yoktur; yalnızca değişmeyen veride güvenlidir. Keyset'in iyileştirmesi, imleçte kaydın sıralama anahtarını (burada id) taşımaktır. Sıralama anahtarı benzersiz değilse (ör. birden çok kaydın aynı zaman damgası varsa), imleç iki alan taşımalıdır: `(zaman, id)`.

**Adım 6 — Doğrula.** Elle iz tablosu (silme sonrası tablo: 9, 8, 7, 6, 5, 4, 3, 2, 1):

| Yöntem | Son gören | Sorgu | Dönen | Atlanan / çift |
|---|---|---|---|---|
| Offset | — | OFFSET 3, LIMIT 3 | 6, 5, 4 | 7 atlandı |
| Keyset | 8 | id < 8, LIMIT 3 | 7, 6, 5 | yok |

Bu tablo, Şekil 40.5'teki silme satırı ile ve programın çıktısındaki `offset, sil -> ([10, 9, 8], [6, 5, 4])` ve `keyset, sil -> ([10, 9, 8], [7, 6, 5])` satırlarıyla birebir uyuşur.

**Bunu AI'sız yazabilir misin?** Aynı tabloda ekleme senaryosunu, yani başa id 11'in eklendiği durumu, hem offset hem keyset için elle hesapla. Hangi id'nin çift göründüğünü tabloda işaretle ve nedenini bir cümleyle açıkla.

### Örnek 3 (★★): Token bucket'ın zaman içindeki durum izi

**Problem.** Kapasitesi 2 ve hızı saniyede 1 jeton olan bir kova, şu istekleri alıyor: t = 0, 0, 0, 0.5, 2.0. Her isteğin sonucunu (izin/red), isteğden sonraki jeton sayısını ve reddedildiyse beklenmesi gereken süreyi hesapla.

**Adım 1 — Anla.** Kova başlangıçta doludur: jeton = 2. Her istek 1 jeton harcar. Aradaki sürede jeton, saniyede 1 artar ama kapasiteyi (2) aşamaz.

**Adım 2 — Örnekle.** t = 0'da iki istek jetonları harcar; üçüncü istek red alır. t = 0.5'te yarım jeton birikmiştir; ama 1 jeton gerekir. t = 2.0'da kova yeterince dolmuştur.

**Adım 3 — Kaba çöz.** İlk üç istek: izin, izin, red. Red için bekleme `(1 - 0) / 1 = 1` saniye. Dördüncü istek (t=0.5): red; bekleme `(1 - 0.5) / 1 = 0.5`. Beşinci (t=2.0): izin.

**Adım 4 — Örüntü.** Jeton formülü `min(kapasite, jeton + geçen * hız)`dir. Her istekte önce yenilenir, sonra harcanır. Bekleme, eksik jetonun hıza bölümüdür.

**Adım 5 — İyileştir.** Sunucu bekleme süresini `Retry-After` için saniyeye yukarı yuvarlar: 0.5 saniye → 1 saniye. Ayrıca isteğin maliyeti 1'den büyükse (ör. toplu istek), bekleme `(maliyet - jeton) / hız` ile hesaplanır; bu, koddaki `maliyet` parametresinin amacıdır.

**Adım 6 — Doğrula.** Elle iz tablosu (kapasite 2, hız 1, başlangıç jeton = 2):

| t | Geçen | Yenilenen jeton | İstek | Harcanan sonra jeton | İzin | Bekleme |
|---|---|---|---|---|---|---|
| 0.0 | 0 | 2 | 1. | 1 | evet | 0 |
| 0.0 | 0 | 1 | 2. | 0 | evet | 0 |
| 0.0 | 0 | 0 | 3. | 0 | hayır | 1.0 |
| 0.5 | 0.5 | 0.5 | 4. | 0.5 | hayır | 0.5 |
| 2.0 | 1.5 | min(2, 0.5 + 1.5) = 2 | 5. | 1 | evet | 0 |

Son satırda yenilenen jeton 2'dir: kapasite sınırı devrededir (0.5 + 1.5 = 2.0, tam sınırda). Bu, bir jetonun kapasiteyi aşarak birikemeyeceğini gösterir.

**Bunu AI'sız yazabilir misin?** Kapasite 3, hız 0.5 jeton/saniye ve t = 0, 0, 0, 0, 1, 2, 4 için aynı tabloyu elle doldur. Beşinci istekte jetonun yarım mı, tam mı olduğuna dikkat et ve bekleme süresini hesapla.

### Örnek 4 (★★★): Protobuf varint'ini elle çözmek

**Problem.** Bayt dizisi `96 01 10 05` verildi. Bu dizide, `int` olarak kodlanmış bir varint ve bir zigzag `sint32` değeri var. Her baytın hangi değere katkıda bulunduğunu izleyerek iki değeri elle çöz. Sonra aynı yöntemle `150`'nin ve `-3`'ün kodlamasını da üret.

**Adım 1 — Anla.** Varint: her baytın düşük 7 biti veri, en yüksek biti (MSB) devam bayrağıdır. Düşük gruplar önce gelir, yani little-endian sırasıyla. Zigzag: `(n >> 1) ^ -(n & 1)` ile geri çevrilir.

**Adım 2 — Örnekle.** `96 01`: ilk bayt `0x96 = 1001 0110`, MSB = 1 (devam), düşük 7 bit `001 0110` = 22. İkinci bayt `0x01 = 0000 0001`, MSB = 0 (son), düşük 7 bit `000 0001` = 1. Değer, 1 bayt sonra 1 · 2^7 eklenerek bulunur.

**Adım 3 — Kaba çöz.** `22 + 1 · 128 = 150`. Zigzag bölümü için `05`: `05 >> 1 = 2`, `05 & 1 = 1`, `-(1) = -1`; `2 ^ -1` ile `-3` bulunur.

**Adım 4 — Örüntü.** Her yeni bayt, kendinden önce gelen grubu 7 bit sola kaydırır. Yani k. bayt `2^(7·k)` ile çarpılır. Zigzag'de tek sayılar negatif, çift sayılar pozitiftir: `n` pozitifse `2n`, negatifse `-2n - 1`.

**Adım 5 — İyileştir.** Kodlayıcı tarafında `varint_kodla` bu örüntüyü tersine çevirir: en düşük 7 biti alıp MSB'yi ayarlar, sayıyı 7 bit kaydırır. Çözücüde bir güvenlik sınırı gerekir: kayma 63'ü aşarsa girdi bozuktur ve sonsuz bir okumadan kaçınmak için hata verilmelidir (`b40_5_protobuf.py` bunu yapar).

**Adım 6 — Doğrula.** Elle iz tablosu:

| Bayt | İkilik | MSB | Düşük 7 bit | Kayma | Katkı | Toplam |
|---|---|---|---|---|---|---|
| 96 | 1001 0110 | 1 (devam) | 0010110 = 22 | 0 | 22 | 22 |
| 01 | 0000 0001 | 0 (son) | 0000001 = 1 | 7 | 128 | 150 |

| Zigzag bayt | Değer | `n >> 1` | `n & 1` | `(n>>1) ^ -(n&1)` |
|---|---|---|---|---|
| 05 | 5 | 2 | 1 | 2 ^ -1 = -3 |

Elle bulduğumuz 150 ve -3, programın çıktısındaki `alan 1 id = 150` ve `alan 2 sicaklik = -3` satırlarıyla birebir uyuşur. Ayrıca `b40_5b_capraz.py` aynı mesajı resmi kütüphaneyle kodladığında `08 96 01 10 05 22 02 45 56` baytlarını üretir; bu bizim elle kodladığımız baytlarla aynıdır.

**Bunu AI'sız yazabilir misin?** `300` sayısını varint olarak elle kodla: iki baytı da ikilik olarak yaz, MSB'leri ayarla, sonra bu iki baytı tekrar çözerek 300'e geri dön. Sonra `-1` için zigzag değerini hesapla ve geri çevir.

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Bu bölümün projeleri, sözleşme tasarlama ve arayüz düşünme kasını geliştirmek için var. Bir aracın kodunu ya da tasarımını kopyalarsan, sınadığın şey aracın kararıdır, senin değil. Sözleşmeyi kendin yaz, hataları kendin bul.
:::

### Proje 1 (★★): İHA görev API'si

**Amaç.** Bu bölümdeki İHA filo API'sini, görevlerin tam yaşam döngüsünü kapsayacak şekilde genişlet: bir görevin oluşturulması, durumunun değiştirilmesi (`planlandi`, `ucuyor`, `tamamlandi`, `iptal`), listelenmesi, güncellenmesi ve silinmesi.

**Yapılacak / beklenen davranış.** Görevler için tam CRUD olsun. Durum geçişleri kurallıdır: `tamamlandi` olan bir görev yeniden `ucuyor` yapılamaz (409). Görev listesi, durum filtresi ve imleç sayfalamasıyla gelsin. Her değişiklik `If-Match` ile korunsun. Sözleşme testlerini (40.9) ayrı bir dosyada yaz; testler bu API'nin istemcisi gibi davransın.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Durum geçişlerini bir tablo olarak tanımla: her durumun izin verilen sonraki durumlarını bir sözlükte tut ve geçişi denetleyen tek bir fonksiyon yaz. `iha_guncelle`'deki `ETag` kontrol sırasını örnek al; yeni uç noktanın hangi sırayla 404, 428, 412, 422 ve 409 döneceğini önce bir tabloya yaz. Sözleşme testleri için, her bir uç noktanın beklenen yanıt şemasını JSON Schema olarak yaz ve `jsonschema` ile doğrula.

**Başarı kriterleri.** (1) Her geçersiz durum geçişi 409 döner ve veri değişmez. (2) Başkasına ait bir görev hiçbir uç noktada görünmez. (3) Sayfalama, ekleme ve silme sırasında kayıt atlamaz ya da çiftlemez; bunu bir testle kanıtla. (4) Sözleşme testleri, kasıtlı olarak bir alan adı değiştirildiğinde kırmızıya döner. (5) Tüm testler birkaç saniyede biter ve sunucu ayrı bir süreçte değil, testin içinde başlar.

### Proje 2 (★★★): Kararlı ABI'li bir C kütüphanesi ve uyumluluk testi

**Amaç.** Bir C kütüphanesi tasarla, ilk sürümünü yayımla, sonra ikinci sürümünde bir özellik ekle. Eski istemcinin yeni kütüphaneyle, yeniden derlenmeden çalışmasını ya da açık bir hata vermesini sağla.

**Yapılacak / beklenen davranış.** Kütüphane bir opak tanıtıcı (`kuyruk_t`) döndürsün. Yapının boyutu bir sürüm fonksiyonuyla (`kuyruk_surum()`) ve bir yapı-boyutu fonksiyonuyla sorgulanabilsin. İkinci sürümde yeni bir özellik (ör. öncelik) yalnızca yeni bir fonksiyonla eklensin; mevcut fonksiyonların imzası ve yapının bellek düzeni değişmesin. Bir uyumluluk testi, v1 istemcisini v2 kütüphanesine karşı çalıştırıp (a) sonucun doğru olduğunu ya da (b) açık bir hatayla reddedildiğini doğrulasın.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Opak tanıtıcı için yapıyı yalnızca kaynak dosyada tanımla ve kullanıcıya yalnızca `typedef`'i göster. Sürüm fonksiyonunu bir sabit döndürecek şekilde yaz; ikinci sürümde artır. ABI'yi `offsetof` ve `sizeof` ile ölçen küçük bir program yaz; v1 ve v2 çıktılarını yan yana koy. Uyumluluk testi için, v1 istemcisini derledikten sonra kütüphaneyi yeniden derleyip istemciyi yeniden derlemeden çalıştır. Kırılma varsa ASan ile yakala.

**Başarı kriterleri.** (1) İstemci kaynak kodunda yapının bir alanına hiçbir yerde doğrudan erişilmez. (2) v1 istemcisi v2 kütüphanesine karşı, yeniden derlenmeden, ya doğru çalışır ya da sürüm kontrolüyle temiz bir hata verir. (3) ASan ile çalıştırıldığında bellek hatası raporu yoktur. (4) Sürüm numarası, belgelenmiş ve kütüphaneden okunabilir durumdadır. (5) Bir kullanıcıya dönük başlık dosyası, yapıyı tanımlamadan derlenebilir.

### Ek Alıştırmalar

**Zorluk etiketleri:** ★ kolay, ★★ orta, ★★★ zor. (Mülakat) etiketli sorular klasik mülakat problemleridir; önce kağıtta, sonra kodla çöz.

1. **(★) Fonksiyon adı.** `get_user_data()`, `kullanici_al()`, `kullanici()` adlarını tutarlılık ve şaşırtma ölçütüne göre karşılaştır. Hangisi bir REST koleksiyonu ve hangisi bir öğe için uygun? Gerekçeni tek cümleyle yaz.
2. **(★) Yöntem seçimi.** "Bir kullanıcının parolasını değiştir", "bir kullanıcıyı sil", "bir kullanıcının adını güncelle" işlemleri için yöntem seç. Hangisi idempotent, hangisi değildir ve neden?
3. **(★★) Durum kodu tablosu (Mülakat).** Bir ödeme API'sinde yetersiz bakiye, geçersiz kart numarası, aynı işlemin ikinci gönderimi ve sunucunun veritabanına ulaşamaması durumları için durum kodlarını gerekçeleriyle seç. Hangi durumda istemci yeniden deneyebilir?
4. **(★★) Offset'in sınırı.** Sayfa boyutu 10 olan bir offset sayfalamada, son sayfanın `OFFSET 999990` ile istendiğini düşün. Veritabanı kaç satır okumak zorunda kalır? Bu maliyeti keyset ile karşılaştır.
5. **(★★) Sıralama anahtarı (Mülakat).** Keyset sayfalamada sıralama anahtarı benzersiz değilse imleç neden iki alan taşımalıdır? Yinelenen zaman damgası olan iki kayıt sayfa sınırına denk gelirse ne olur?
6. **(★★★) Token bucket ve sabit pencere (Mülakat).** Dakikada en fazla 100 istek kuralı, sabit pencereyle uygulanır. Pencere sınırında bir istemci en fazla ne kadar istek gönderebilir? Aynı kuralı token bucket ile uygularsan bu sınır nasıl değişir? Kapasiteyi ve hızı nasıl seçersin?
7. **(★★) Retry-After yuvarlama.** Sunucu beklemeyi saniyeye yukarı yuvarlıyor. Yuvarlama yerine aşağı yuvarlasaydı hangi istemci davranışı bozulurdu? Bir istemci, 0 saniye `Retry-After` alırsa ne yapmalı?
8. **(★★) Silme ve idempotentlik.** `DELETE /ihalar/7` ikinci kez gönderildiğinde 404 döndürmek, "idempotent" tanımına aykırı mıdır? Tanımı ve 404'ün bir durum değişikliği olmadığını göz önünde bulundurarak yanıtını gerekçelendir.
9. **(★★★) Sürüm geçişi (Mülakat).** Bir alanın tipini `int`'ten `string`'e değiştirmek gerekiyor. Eski istemciler bozulmadan geçişi nasıl planlarsın? Yeni bir alan eklemek, eski alanı yaşatmak ve kullanımdan kaldırma takvimini içeren bir plan yaz.
10. **(★★) Güvenli silme.** `If-Match` olmadan silmeye izin veren bir API'de hangi senaryo veri kaybına yol açar? Bu senaryoyu bir zaman çizelgesiyle göster.
11. **(★★★) Protobuf sınırı.** Varint çözücüde 63 bit kaymadan sonra hâlâ devam biti varsa neden hata vermeliyiz? Bu sınırı koymazsak, kötü niyetli bir bayt dizisi çözücüye ne yaptırabilir?
12. **(★) Hata gövdesinin dili (Mülakat).** Hata mesajlarını İngilizce mi Türkçe mi yazmalısın? Hangi alanlar dile bağlı olmamalı ve neden? Bir istemcinin hangi alana bakarak hatayı ayırt etmesi gerektiğini gerekçelendir.

## Kod Okuma Egzersizi

Bugünkü kesit, CPython 3.12.10'un `Lib/http/__init__.py` dosyasındaki `HTTPStatus` sınıfıdır. Kaynak, yerel kurulumdan birebir alındı: `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\http\__init__.py`. Sınıfın belgelendirme dizesi (docstring) ve tüm durum tanımları kısaltıldı; kısaltılan yerler `# ...` ile işaretlendi. Kalan satırlar kaynaktaki haliyle aynıdır.

```python
from enum import StrEnum, IntEnum, _simple_enum

__all__ = ['HTTPStatus', 'HTTPMethod']


@_simple_enum(IntEnum)
class HTTPStatus:
    # ... (kısaltıldı)
    def __new__(cls, value, phrase, description=''):
        obj = int.__new__(cls, value)
        obj._value_ = value

        obj.phrase = phrase
        obj.description = description
        return obj
    # ... (kısaltıldı)
    @property
    def is_client_error(self):
        return 400 <= self <= 499

    @property
    def is_server_error(self):
        return 500 <= self <= 599

    # informational
    CONTINUE = 100, 'Continue', 'Request received, please continue'
    SWITCHING_PROTOCOLS = (101, 'Switching Protocols',
            'Switching to new protocol; obey Upgrade header')
    PROCESSING = 102, 'Processing'
```

Kesitin ikinci parçasında üye tanımlarına bakıyoruz. Bazı üyeler parantezli, bazıları parantezsiz bir demettir (`CONFLICT = 409, ...` gibi); bu bir biçim farkıdır, anlam farkı değildir. Çok satırlı tanımların devam satırları da aynı demeti sürdürür.

```python
    PROXY_AUTHENTICATION_REQUIRED = (407,
        'Proxy Authentication Required',
        'You must authenticate with this proxy before proceeding')
    REQUEST_TIMEOUT = (408, 'Request Timeout',
        'Request timed out; try again later')
    CONFLICT = 409, 'Conflict', 'Request conflict'
    GONE = (410, 'Gone',
        'URI no longer exists and has been permanently removed')
    LENGTH_REQUIRED = (411, 'Length Required',
        'Client must specify Content-Length')
    PRECONDITION_FAILED = (412, 'Precondition Failed',
        'Precondition in headers is false')
    # ... (kısaltıldı)
    PRECONDITION_REQUIRED = (428, 'Precondition Required',
        'The origin server requires the request to be conditional')
```

**Sorular — cevaplamadan geçme:**

- `HTTPStatus` bir `IntEnum`'dir (dosyanın üst kısmındaki `_simple_enum(IntEnum)` ile). Bir durum kodunun `== 404` ile karşılaştırılabilmesi, bu tasarımın hangi API kararını ortaya koyar? Aynı üyenin hem sayı hem metin olarak kullanılabilmesi, bir kütüphane API'sinde neden değerlidir?
- `PRECONDITION_FAILED = (412, 'Precondition Failed', 'Precondition in headers is false')` satırında değer bir demet (tuple). Enum üyesi oluşturulurken bu demet `__new__` fonksiyonuna nasıl geçer? `__new__` içindeki `obj._value_ = value` satırı olmasaydı ne olurdu?
- `CONFLICT = 409, 'Conflict', 'Request conflict'` ile `PROXY_AUTHENTICATION_REQUIRED = (407, ...)` satırlarındaki biçim farkını açıkla. Parantezler neyi değiştirir, neyi değiştirmez?
- Enum üyeleri `is_client_error` ve `is_server_error` gibi özellikler taşıyor. Bu özellikleri `400 <= self <= 499` biçiminde yazmak, bir durum kodunu sınıflamak için neden yeterlidir? Bu, Bölüm 30.6'daki durum kodu sınıflarıyla nasıl eşleşir?
- Kaynağın ilk satırındaki `from enum import StrEnum, IntEnum, _simple_enum` içinde `_simple_enum` özel (alt çizgili) bir isimdir. Kütüphane geliştiricisi bunu neden kullanmış olabilir ve bu, senin kendi API'nde bir enum yazarken hangi dikkati gerektirir?
- Bu dosyanın belgelendirme dizesi, RFC'lerin bir listesini verir (RFC 7231, 6585, 3229 …). Bir durum kodunun hangi RFC'de tanımlandığını bilmek, API tasarımında ne işe yarar? RFC 9110'un bu listeye göre ne değiştirdiğini kendi kelimelerinle yaz.

## Bölüm Özeti

- **API bir sözleşmedir:** Girdi, çıktı, hata ve yan etkiler kayıt altına alınmalı; Hyrum yasası nedeniyle gözlemlenebilir her davranış bir bağımlılığa dönüşebilir.
- **Kütüphane API'si:** Tutarlı adlandırma, `const` ile girdi işaretleme, opak işaretçi ile yapıyı gizleme ve sahiplik kurallarını açıkça belgeleme.
- **Hata bildirimi:** Dönüş kodu, `errno`, istisna ve sonuç türü arasında bir ödünleşim vardır; C'de sonuç açık bir `enum` ve çıkış parametresiyle yazılır.
- **ABI:** Yapıya alan eklemek boyutu değiştirir ve eski ikili dosyalarda tanımsız davranışa yol açar; boyutu kütüphaneden sorgulatmak, yapıyı gizlemek ve yeni işlevi yeni fonksiyonla eklemek bu sorunu önler.
- **REST:** Kaynakları isimle, yöntemleri niyetle, durum kodlarını sonuçla eşleştir; 400 ile 422, 404 ile 403 arasındaki ayrımlar birer tasarım kararıdır.
- **Sayfalama ve güvenli yeniden deneme:** Offset kayan veride kayıt atlatır ya da çiftletir; keyset bunu önler. `Idempotency-Key` ve ETag/`If-Match`, ağ belirsizliğinde ve eşzamanlı güncellemede veri bütünlüğünü korur.
- **Hız sınırı ve sürümleme:** Token bucket patlamalara izin verir ama ortalama hızı sınırlar; sürümleme, "alan eklemek güvenli, kaldırmak yıkıcıdır" kuralıyla ve kullanımdan kaldırma sürecinin yanıtlarla bildirilmesiyle yürür.
- **Şema ve sözleşme testi:** JSON Schema ile doğrulama, tüketici odaklı sözleşme testleri ve çalışan örnekler, belgeyi kodla senkron tutar. Protobuf gibi alternatifler, kodlamanın bayt düzeyinde anlaşılmasını gerektirir.

**Sonraki bölümde:** Bölüm 41 — System Design. Bu bölümde tek bir sunucunun arayüzünü tasarladık; sonraki bölümde bu sunucuların nasıl çoğaltılacağını, yük dağıtılacağını, önbelleklerin ve kuyrukların nerede duracağını ve tutarlılığın kapasiteyle nasıl ödünleşeceğini göreceğiz. Burada yazdığımız token bucket'ın dağıtık hâli ve `Idempotency-Key` tablosunun çoklu sunucudaki tutarlılığı, orada ele alınacak sorular olacak.

::: mulakat
Klasik sorular — hemen cevaplamaya çalışma, her birini birkaç dakika düşün:

1. Bir kütüphane fonksiyonunun bellek sahipliğini başlık dosyasında nasıl belirtirsin? Sahiplik belirtilmezse hangi hatalar kaçınılmaz olur?
2. Bir yapıya yeni bir alan eklemek kaynak düzeyinde güvenli, ikili düzeyde neden güvenli değildir? Eski ikili dosya neyi yanlış hesaplar?
3. PUT ile PATCH arasındaki farkı, idempotentlik kavramıyla birlikte açıkla. Hangisini bir "sayaç artır" işlemi için kullanmazsın ve neden?
4. Offset sayfalamada veri sayfalar arasında değişirse ne olur? Keyset sayfalama bu sorunu nasıl çözer ve kendi bedeli nedir?
5. İki istemci aynı anda aynı kaydı güncellerse kayıp güncellemeyi ETag ve `If-Match` olmadan nasıl önlersin? Iyimser ve kötümser kilitlemenin farkı nedir?
6. Bir ödeme API'sinde istemci zaman aşımına uğrayıp POST'u yeniden gönderdi. Kayıt iki kez oluşmasın diye hangi mekanizmayı tasarlarsın, anahtar nerede saklanır ve ne kadar süre?
7. Token bucket ile sabit pencere arasındaki fark nedir? Dakikada 100 kuralında sabit pencerenin hangi açığını kapatır, hangi bedeli ödetir?
8. Bir API'de hangi alanın "kaldırılabilir" olduğunu nasıl anlarsın? Hangi değişikliği kırıcı saymazsın ve neden bu kadar dikkatli olursun?
:::
