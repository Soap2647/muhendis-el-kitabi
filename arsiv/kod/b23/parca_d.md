## Çözümlü Örnekler

Dört örnek, Bölüm 5'in altı adımını izler. Her birinde elle izlenebilir bir girdi var; sonuçları kendi kafanda ya da bir kâğıtta önce tahmin et, sonra çalıştır. Tahmin ile sonuç arasındaki fark, asıl öğrenme anıdır.

### Örnek 1 (★): Kötü adları ve tek fonksiyonu düzeltmek

Aşağıdaki fonksiyon, bir batarya kayıt listesinden kritik skorlu kayıtları seçer ve özetler. Adları kötü, ama davranışı açık.

```python
def f(k, e, m):
    r = []
    t = 0.0
    for i in k:
        if i[0] is None or i[1] is None or i[2] is None:
            continue
        if i[3] != 1:
            continue
        if i[1] < e:
            continue
        v = i[1] * 0.92 + i[2] * 0.08
        if v <= 85.0:
            continue
        r.append((i[0], v))
        t = t + v
    if len(r) == 0:
        return None
    if m == "ortalama":
        return t / len(r)
    if m == "liste":
        return r
    raise ValueError(m)
```

**Adım 1 — Anla.** Fonksiyon üç işi birden yapıyor: (1) aktif olan ve gerilimi eşiğin üstünde olan kayıtları seçmek, (2) her kayıt için ağırlıklı bir skor hesaplamak (gerilim ağırlığı 0.92, sıcaklık ağırlığı 0.08), (3) skoru 85'i aşanları ya liste olarak ya da ortalama olarak döndürmek. Girdi `k`, dört elemanlı tuple'lardan oluşuyor: (zaman, gerilim, sıcaklık, aktif). `m` ise çıktı modu.

**Adım 2 — Örnekle.** Beş kayıt, eşik 80, mod "liste" ve "ortalama":

```text
(0.0, 90.0, 80.0, 1)   aktif, gerilim >= 80, skor 89.2   -> kritik
(1.0, 95.0, 30.0, 0)   aktif degil                       -> atla
(2.0, 70.0, 60.0, 1)   gerilim 70 < 80                   -> atla
(3.0, 88.0, 50.0, 1)   skor 84.96 <= 85                  -> atla
(4.0, 100.0, 20.0, 1)  aktif, gerilim >= 80, skor 93.6   -> kritik
```

Elle hesap: 90 × 0.92 + 80 × 0.08 = 82.8 + 6.4 = 89.2. Beklenen liste `[(0.0, 89.2), (4.0, 93.6)]`, ortalama `(89.2 + 93.6) / 2 = 91.4`.

**Adım 3 — Kaba çöz.** Fonksiyonu çalıştırıp elle bulduğumuz sonuçla karşılaştırmak en kısa yol. Eski kod bu örnekte beklenen sonucu verir; ama sorun, sonucun doğru olup olmadığını değil, kodu okumanın ne kadar zor olduğudur. 22 satırı okurken üç harfli adı, dört sayıyı ve dört indeksi aynı anda akılda tutmak zorundasın.

**Adım 4 — Örüntü.** Fonksiyonun gövdesi üç bölümden oluşuyor: filtre (`continue` ile elenen dört durum), skor hesabı ve özet. Sabitler (0.92, 0.08, 85.0) adsız, tuple elemanları (`i[1]`, `i[3]`) ise "ilkel takıntısı" kokusu taşıyor. Her bölüm ayrı bir fonksiyon adı hak ediyor.

**Adım 5 — İyileştir.** Önce adları düzelt (davranışa dokunmadan), sonra sabitleri ve bir `NamedTuple`'ı tanıt, sonra filtreyi, skor hesabını ve özeti ayrı fonksiyonlara çıkar. Yeni sürümün tamamı:

```python
from typing import NamedTuple, Optional

GERILIM_AGIRLIGI = 0.92
SICAKLIK_AGIRLIGI = 0.08
KRITIK_SKOR = 85.0


class Kayit(NamedTuple):
    zaman: float
    gerilim: float
    sicaklik: float
    aktif: int


def kayit_oku(ham) -> Optional[Kayit]:
    zaman, gerilim, sicaklik, aktif = ham
    if zaman is None or gerilim is None or sicaklik is None:
        return None
    return Kayit(zaman, gerilim, sicaklik, aktif)
```

```python
def kayit_uygun_mu(kayit: Kayit, esik: float) -> bool:
    return kayit.aktif == 1 and kayit.gerilim >= esik


def skor_hesapla(kayit: Kayit) -> float:
    return (kayit.gerilim * GERILIM_AGIRLIGI
            + kayit.sicaklik * SICAKLIK_AGIRLIGI)


def kritik_skorlar(ham_kayitlar, esik):
    sonuc = []
    for ham in ham_kayitlar:
        kayit = kayit_oku(ham)
        if kayit is None or not kayit_uygun_mu(kayit, esik):
            continue
        skor = skor_hesapla(kayit)
        if skor > KRITIK_SKOR:
            sonuc.append((kayit.zaman, skor))
    return sonuc


def kritik_ozet(ham_kayitlar, esik, mod):
    kritikler = kritik_skorlar(ham_kayitlar, esik)
    if not kritikler:
        return None
    if mod == "ortalama":
        toplam = 0.0
        for _, skor in kritikler:
            toplam = toplam + skor
        return toplam / len(kritikler)
    if mod == "liste":
        return kritikler
    raise ValueError(mod)
```

Yeni yapıda en karmaşık fonksiyonun CC'si 5; eskisinde 11'di. Ama bu sayıya bakıp "bitti" demek yanlış olur: asıl kazanım, her parçanın tek bir soruya cevap vermesi.

**Adım 6 — Doğrula.** Eşdeğerliği kanıtlamanın en güvenilir yolu, rastgele girdilerle karşılaştırmaktır. Test, 5000 rastgele kayıt kümesi üretir (tohum 42, bazı gerilim ve sıcaklık değerleri `None`), her küme için üç mod dener (ortalama, liste ve tanınmayan bir mod):

```python
import random
from ex1_eski import f
from ex1_yeni import kritik_ozet


def uret(rng):
    kayitlar = []
    for z in range(rng.randint(0, 30)):
        g = None if rng.random() < 0.08 else rng.uniform(60, 100)
        s = None if rng.random() < 0.08 else rng.uniform(20, 90)
        kayitlar.append((float(z), g, s, rng.choice([0, 1, 1])))
    return kayitlar


def calistir(fn, *a):
    try:
        return ("ok", fn(*a))
    except ValueError as e:
        return ("hata", str(e))


if __name__ == "__main__":
    rng = random.Random(42)
    sayac = {"toplam": 0, "dolu": 0, "uyusmayan": 0}
    for _ in range(5000):
        kay = uret(rng)
        esik = rng.uniform(55, 95)
        for mod in ("ortalama", "liste", "bilinmeyen"):
            sayac["toplam"] += 1
            eski = calistir(f, kay, esik, mod)
            yeni = calistir(kritik_ozet, kay, esik, mod)
            if eski[1] is not None and eski[0] == "ok":
                sayac["dolu"] += 1
            if eski != yeni:
                sayac["uyusmayan"] += 1
    print("toplam:", sayac["toplam"], "dolu:", sayac["dolu"],
          "uyusmayan:", sayac["uyusmayan"])
```

İlk denemede özeti `sum(s for _, s in kritikler) / len(kritikler)` ile yazdık ve test 524 uyuşmazlık buldu. Nedeni, sayıların toplama sırasıyla ilgili değildi; `sum()` ile döngüsel toplam, sonuçların son basamaklarında farklı çıkıyordu. Python 3.12 sürüm notlarında da belirtildiği gibi `sum()`, float toplamında telafili (compensated) bir toplama kullanır ve bu sonuç `math.fsum` ile birebir aynıdır; bizim `t = t + v` döngümüz ise farklı bir sonuç üretir. Refactoring'in kuralı gereği davranışı bit düzeyinde korumak istedik, bu yüzden toplamayı açık döngüye çevirdik. Testin son hali:

| Durum | Eski `f` | Yeni `kritik_ozet` | Not |
|---|---|---|---|
| Elle örnek, liste | `[(0.0, 89.2), (4.0, 93.6)]` | aynı | beklenen |
| Elle örnek, ortalama | `91.4` | `91.4` | beklenen |
| 15000 durum, `sum()` ile | — | 524 uyuşmazlık | telafili toplama farkı |
| 15000 durum, döngü ile | — | 0 uyuşmazlık | davranış korundu |
| `gerilim = nan`, liste | `[(0.0, nan)]` | `None` | NaN ve koşul olumsuzlama |

Son satır, en öğretici olanıdır. Eski kod `if i[1] < e: continue` ile filtreler; NaN için `nan < e` yanlıştır, dolayısıyla kayıt geçer. Yeni kod `kayit.gerilim >= esik` ile geçirir; NaN için bu da yanlıştır, dolayısıyla kayıt elenir. `not (a < b)` ile `a >= b` NaN'da aynı değildir. Test rastgele girdilerde NaN üretmediği için bu farkı yakalayamadı; sen de bir koşulu tersine çevirdiğinde NaN kenar durumunu ayrıca düşünmelisin.

**Bunu AI'sız yazabilir misin?** Aynı kayıtlar için, yalnızca kritik kayıtların en yüksek skorunu döndüren bir `en_yuksek_skor(ham_kayitlar, esik)` fonksiyonu yaz. Önce adını ve parametrelerini düşün, sonra eski kodla eşdeğerlik testini yaz.

### Örnek 2 (★★): İç içe if cehenneminden koruma cümlelerine

Bir sensör ölçümünden alarm kararı çıkaran aşağıdaki fonksiyon, altı farklı sonuç döndürüyor. Girdiler: ölçüm (gerilim, sıcaklık) ya da `None`, son alarm zamanı ve şimdiki zaman.

```python
def alarm_karari(olcum, son_alarm_s, simdi_s):
    if olcum is not None:
        gerilim, sicaklik = olcum
        if gerilim is not None:
            if 300.0 <= gerilim <= 420.0:
                if sicaklik is not None:
                    if sicaklik > 60.0:
                        if simdi_s - son_alarm_s >= 60.0:
                            return "KRITIK"
                        return "SESSIZ"
                    if sicaklik > 45.0:
                        return "UYARI"
                    return "NORMAL"
                return "VERI_EKSIK"
            return "GERILIM_HATASI"
        return "VERI_EKSIK"
    return "VERI_YOK"
```

**Adım 1 — Anla.** Fonksiyon önce veri varlığını kontrol eder (ölçüm, gerilim, sıcaklık), sonra gerilim aralığını, sonra sıcaklık eşiklerini ve son olarak sessizlik süresini değerlendirir. Altı çıkış vardır: `VERI_YOK`, `VERI_EKSIK`, `GERILIM_HATASI`, `KRITIK`, `SESSIZ`, `UYARI`, `NORMAL` (yedi ayrı değer).

**Adım 2 — Örnekle.** Sekiz elle girdi, beklenen sonuçla birlikte:

```text
olcum          son   simdi  beklenen
None            0     0     VERI_YOK
(None, 50.0)    0    10     VERI_EKSIK
(250.0, 50.0)   0    10     GERILIM_HATASI
(350.0, None)   0    10     VERI_EKSIK
(350.0, 70.0)   0    10     SESSIZ    (60 sn dolmadi)
(350.0, 70.0)   0   100     KRITIK
(350.0, 50.0)   0    10     UYARI
(350.0, 30.0)   0    10     NORMAL
```

**Adım 3 — Kaba çöz.** Eski kodu bu sekiz girdide çalıştırıp beklenenlerle karşılaştırdık; hepsi tuttu. Ama kodu okumak için her seviyede bir öncekinin "açık" olduğunu hatırlamak zorundasın: altıncı katmanda beş koşulun da doğru olduğunu bilmen gerekiyor.

**Adım 4 — Örüntü.** Her `if`'in bir `else`'i yok; her iç koşul bir dış koşulun içinde. Bu, koruma cümlesi kalıbına çok uygun bir durum. Dikkat edilmesi gereken tek şey, geçersizlik kontrollerinin **sırası**: gerilim `None` kontrolü, aralık kontrolünden önce gelmeli; ama sıcaklık `None` kontrolü aralık kontrolünden sonra. Sebep, eski kodda gerilim aralık dışıysa sıcaklığın hiç denetlenmemesidir.

**Adım 5 — İyileştir.** Sabitleri adlandır, koruma cümlelerini sırayla yaz:

```python
GERILIM_ALT, GERILIM_UST = 300.0, 420.0
SICAKLIK_KRITIK, SICAKLIK_UYARI = 60.0, 45.0
SESSIZLIK_SURESI_S = 60.0


def alarm_karari(olcum, son_alarm_s, simdi_s):
    if olcum is None:
        return "VERI_YOK"
    gerilim, sicaklik = olcum
    if gerilim is None:
        return "VERI_EKSIK"
    if not GERILIM_ALT <= gerilim <= GERILIM_UST:
        return "GERILIM_HATASI"
    if sicaklik is None:
        return "VERI_EKSIK"
    if sicaklik > SICAKLIK_KRITIK:
        if simdi_s - son_alarm_s >= SESSIZLIK_SURESI_S:
            return "KRITIK"
        return "SESSIZ"
    if sicaklik > SICAKLIK_UYARI:
        return "UYARI"
    return "NORMAL"
```

İlk denememizde sıcaklık `None` kontrolünü gerilim aralık kontrolünün üstüne aldık; yani iki koşulu yer değiştirdik. Bu, "daha düz" görünüyordu ama davranışı bozdu: gerilim aralık dışıyken sıcaklık da boşsa, eski kod `GERILIM_HATASI` dönerken yeni kod `VERI_EKSIK` dönüyordu. Test 20000 girdide 125 uyuşmazlık buldu. Sıra, hangi geçersizliğin önce bildirildiğini belirler; bu bir davranıştır.

**Adım 6 — Doğrula.** 20000 rastgele girdi (tohum 42) üzerinde eski ve yeni sürümü karşılaştıran test:

```python
import random, sys
from ex2_eski import alarm_karari as eski
from ex2_yeni import alarm_karari as yeni


def deger(rng, lo, hi):
    r = rng.random()
    if r < 0.1:
        return None
    if r < 0.2:
        return rng.uniform(lo - 100, hi + 100)  # sinir disi
    return rng.uniform(lo, hi)


if __name__ == "__main__":
    rng = random.Random(42)
    uyusmayan = 0
    toplam = 0
    for _ in range(20000):
        olcum = None if rng.random() < 0.05 else (
            deger(rng, 300.0, 420.0), deger(rng, 20.0, 80.0))
        son = rng.uniform(0.0, 200.0)
        simdi = rng.uniform(0.0, 300.0)
        toplam += 1
        a = eski(olcum, son, simdi)
        b = yeni(olcum, son, simdi)
        if a != b:
            uyusmayan += 1
            if uyusmayan <= 2:
                print("OLCUM", olcum, "eski", a, "yeni", b)
    print("toplam", toplam, "uyusmayan", uyusmayan)
    sys.exit(0)
```

```term
$ python ex2_test.py
toplam 20000 uyusmayan 0
```

Ölçümler, aynı iki fonksiyon için şu şekilde:

| Sürüm | Döngüsel karmaşıklık | Bilişsel puan | Derinlik | Satır |
|---|---|---|---|---|
| Eski | 8 | 26 | 6 | 17 |
| Yeni | 8 | 8 | 2 | 17 |

Döngüsel karmaşıklık değişmedi, çünkü karar noktası sayısı aynı; yalnızca iç içelik kalktı. Bu yüzden CC tek başına "daha iyi" demek için yetersizdir; bilişsel puan ve derinlik bu farkı gösterir.

**Bunu AI'sız yazabilir misin?** Sıcaklık için "80 derecenin üstünde hemen KRITIK, sessizlik süresine bakma" kuralını ekle. Yeni koşulu nereye koyarsın ve hangi girdi ailesi bu değişikliğin doğru olduğunu gösterir?

### Örnek 3 (★★): C'de hata yolunda sızıntı ve goto ile temizlik

Bir sensör kayıt dosyası okuyan `kayit_oku` fonksiyonu C'de yazıldı. Dosya formatı: 4 bayt sihir değeri (`SIHIR`), 4 bayt kayıt sayısı `n` ve ardından `n` adet `double`. Önce başlık kısa bir ortak dosyaya konur:

```c
#ifndef KAYIT_H
#define KAYIT_H
#include <stddef.h>

#define SIHIR 0x4B41u /* "KA" dosya basligi */

/* 0: basarili; negatif: hata kodu. Cikista *kayitlar free() edilmeli. */
int kayit_oku(const char *yol, double **kayitlar, size_t *adet);

#endif
```

**Adım 1 — Anla.** `kayit_oku` bir dosyayı açar, başlığı doğrular, kayıt sayısını okur, kayıtlar için bellek ayırır, kayıtları okur ve sonucu çağırana verir. Her adım başarısız olabilir ve her başarısızlık farklı bir kaynağı açık bırakabilir.

**Adım 2 — Örnekle.** Dört girdi dosyası ve beklenen dönüş değerleri: `iyi.bin` (n = 3, üç kayıt) → 0; `sihir.bin` (sihir yanlış) → -2; `kesik.bin` (n = 1000 ama yalnızca üç kayıt var) → -5; `yok.bin` (dosya yok) → -1.

**Adım 3 — Kaba çöz.** Eski kodu, sızıntıları görebilmek için ASan ve LeakSanitizer ile çalıştırdık:

```c
#include <stdio.h>
#include <stdlib.h>
#include "kayit.h"

int kayit_oku(const char *yol, double **kayitlar, size_t *adet)
{
    FILE *f = fopen(yol, "rb");
    unsigned int sihir = 0, n = 0;
    double *tampon;

    if (f == NULL)
        return -1;
    if (fread(&sihir, sizeof sihir, 1, f) != 1 || sihir != SIHIR)
        return -2;                 /* SIZINTI: f kapanmadi */
    if (fread(&n, sizeof n, 1, f) != 1)
        return -3;                 /* SIZINTI: f kapanmadi */
    tampon = malloc(n * sizeof *tampon);
    if (tampon == NULL)
        return -4;                 /* SIZINTI: f kapanmadi */
    if (fread(tampon, sizeof *tampon, n, f) != n)
        return -5;                 /* SIZINTI: f ve tampon */
    fclose(f);
    *kayitlar = tampon;
    *adet = n;
    return 0;
}
```

Bu dosyayı dört girdiyle çalıştıran sürücü:

```c
#include <stdio.h>
#include <stdlib.h>
#include "kayit.h"

static void dosya_yaz(const char *ad, unsigned int sihir,
                      unsigned int n, int adet_gercek)
{
    FILE *f = fopen(ad, "wb");
    double v = 1.5;
    fwrite(&sihir, sizeof sihir, 1, f);
    fwrite(&n, sizeof n, 1, f);
    for (int i = 0; i < adet_gercek; i++)
        fwrite(&v, sizeof v, 1, f);
    fclose(f);
}

int main(void)
{
    double *k = NULL;
    size_t adet = 0;
    int r;

    setvbuf(stdout, NULL, _IONBF, 0);
    dosya_yaz("iyi.bin", SIHIR, 3, 3);
    dosya_yaz("sihir.bin", 0x1234u, 3, 3);
    dosya_yaz("kesik.bin", SIHIR, 1000, 3);

    r = kayit_oku("iyi.bin", &k, &adet);
    printf("iyi.bin    -> %d, adet=%zu\n", r, adet);
    free(k);
    r = kayit_oku("sihir.bin", &k, &adet);
    printf("sihir.bin  -> %d\n", r);
    r = kayit_oku("kesik.bin", &k, &adet);
    printf("kesik.bin  -> %d\n", r);
    r = kayit_oku("yok.bin", &k, &adet);
    printf("yok.bin    -> %d\n", r);
    return 0;
}
```

Derleyip ASan ile çalıştırdığımızda, eski sürüm için şu çıktıyı aldık (LeakSanitizer raporu, yol ve sürüm kırpılmıştır):

```term
$ gcc -std=c11 -Wall -Wextra -g -fsanitize=address,undefined \
    -o eski_asan ex3_main.c ex3_eski.c && ./eski_asan
iyi.bin    -> 0, adet=3
sihir.bin  -> -2
kesik.bin  -> -5
yok.bin    -> -1
=================================================================
==730==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 8000 byte(s) in 1 object(s) allocated from:
    #1 ... in kayit_oku ex3_eski.c:17
SUMMARY: AddressSanitizer: 8000 byte(s) leaked in 1 allocation(s).
```

Sızıntının kaynağı 17. satırdaki `malloc`'tur ve sızan blok, 1000 `double`'lık (8000 bayt) tampondur: `kesik.bin` durumunda `-5` yolu tamponu serbest bırakmadan döner. Ama bu rapor eksiktir, çünkü `-2`, `-3`, `-4` ve `-1` yollarında açık kalan dosya tutucusu (`FILE *f`) bir bellek bloğu değildir; LeakSanitizer onu görmez. Bunu `gcc -fanalyzer` gösterir.

**Adım 4 — Örüntü.** Her hata yolunda hangi kaynakların açık kaldığını yazarsak bir tablo çıkar:

| Dönüş | Açık kalan kaynak (eski kod) |
|---|---|
| -1 | yok (dosya açılamadı) |
| -2 | `f` |
| -3 | `f` |
| -4 | `f` |
| -5 | `f` ve `tampon` |

Her erken dönüş, bir öncekinin kaynaklarını da açık bırakıyor; bu bir "tek temizleme noktası" eksikliğidir. Çözüm, tüm çıkışları tek bir temizleme bloğuna bağlamak ve bu bloğu kaynak sırasının tersine göre yazmaktır.

**Adım 5 — İyileştir.** `goto` ile tek çıkış, ters sıralı temizlik:

```c
#include <stdio.h>
#include <stdlib.h>
#include "kayit.h"

int kayit_oku(const char *yol, double **kayitlar, size_t *adet)
{
    int durum;
    FILE *f;
    unsigned int sihir = 0, n = 0;
    double *tampon = NULL;

    f = fopen(yol, "rb");
    if (f == NULL)
        return -1;

    durum = -2;
    if (fread(&sihir, sizeof sihir, 1, f) != 1 || sihir != SIHIR)
        goto cik_dosya;

    durum = -3;
    if (fread(&n, sizeof n, 1, f) != 1)
        goto cik_dosya;

    durum = -4;
    tampon = malloc(n * sizeof *tampon);
    if (tampon == NULL)
        goto cik_dosya;

    durum = -5;
    if (fread(tampon, sizeof *tampon, n, f) != n)
        goto cik_tampon;

    fclose(f);
    *kayitlar = tampon;
    *adet = n;
    return 0;

cik_tampon:
    free(tampon);
cik_dosya:
    fclose(f);
    return durum;
}
```

Etiketler yaptığı işi söyler: `cik_tampon` önce tamponu serbest bırakır ve `cik_dosya`'ya düşer; `cik_dosya` dosyayı kapatır. Bir `goto` dalı, ayrılmamış kaynağa dokunmaz: `tampon` henüz ayrılmadan `-4` yoluna giden dal yalnızca `cik_dosya`'ya atlar. `durum` değişkeni, her adımın hangi hata kodunu döndüreceğini başta belirler; bu, hata kodlarının iki kez yazılmasını önler ama adımlar arasında unutmaya da açıktır. Daha temiz bir alternatif, her adım için ayrı bir etiket kullanmaktır; bunu okurun denemesi için bırakıyoruz.

**Adım 6 — Doğrula.** Üç kanıt: dönüş değerleri aynı kaldı, ASan temiz, `-fanalyzer` uyarısı yok.

```term
$ gcc -std=c11 -Wall -Wextra -g -fsanitize=address,undefined \
    -o yeni_asan ex3_main.c ex3_yeni.c && ./yeni_asan
iyi.bin    -> 0, adet=3
sihir.bin  -> -2
kesik.bin  -> -5
yok.bin    -> -1
$ gcc -std=c11 -Wall -Wextra -fanalyzer -c ex3_yeni.c
(uyari yok)
```

Eski sürümün `-fanalyzer` çıktısı ise şuydu:

```term
ex3_eski.c:14:16: warning: leak of FILE 'f' [-Wanalyzer-file-leak]
ex3_eski.c:14:16: warning: leak of 'f' [-Wanalyzer-malloc-leak]
ex3_eski.c:21:16: warning: leak of FILE 'f' [-Wanalyzer-file-leak]
ex3_eski.c:21:16: warning: leak of 'tampon' [-Wanalyzer-malloc-leak]
```

| Girdi | Dönüş (eski) | Dönüş (yeni) | ASan (eski) | ASan (yeni) | -fanalyzer (eski) |
|---|---|---|---|---|---|
| iyi.bin | 0 | 0 | temiz | temiz | uyarı yok |
| sihir.bin | -2 | -2 | temiz | temiz | `f` sızıntısı |
| kesik.bin | -5 | -5 | 8000 bayt | temiz | `f` ve `tampon` |
| yok.bin | -1 | -1 | temiz | temiz | uyarı yok |

Tablo, iki aracın birbirini tamamladığını gösteriyor: ASan bellek sızıntısını, `-fanalyzer` dosya tutucusu sızıntısını yakalar. Hangisine güvenirsen, kendi başına eksik kalır. Ayrıca `-fanalyzer` çıktısındaki iki uyarının aynı satırı göstermesi, tek bir hata yolunun birden çok kaynağı sızdırdığını anlatır.

**Bunu AI'sız yazabilir misin?** `fread` ile `n` değeri 0 okunduğunda ne olur? `malloc(0)`'ın standart tarafından nasıl tanımlandığını (genel bilgi: `NULL` dönebilir ya da benzersiz bir işaretçi) düşün ve bu durumda kodun doğru davranıp davranmadığını test ile göster.

### Örnek 4 (★★★): Tanrı fonksiyonunu karakterizasyonla parçalamak

Aşağıdaki `rapor_uret` fonksiyonu, cihaz ölçümlerinden bir metin raporu üretiyor. Girdi satırları `cihaz;zaman;deger;birim` biçiminde; birim `V` ya da `mV`. Yorum satırları (`#`) ve boş satırlar atlanır; bozuk satırlar sayılır. Bu fonksiyon büyük ve değişmesi riskli: sınırda, bir sorumluluğu değiştirmek diğerlerini de bozabilir.

**Adım 1 — Anla.** Fonksiyon beş işi birden yapıyor: satırları ayrıştırmak ve doğrulamak, birimi volta çevirmek, cihaz bazında min, max ve ortalama toplamak, eşiği aşan cihazları `UYARI` olarak işaretlemek ve sonucu hizalı bir metin tablosu olarak biçimlendirmek.

**Adım 2 — Örnekle.** Beş satırlık bir girdi, elle tahmin ettiğimiz sonuç: `ALFA` iki ölçüm (3.9 ve 2.5 V), `BETA` bir ölçüm (3500 mV = 3.5 V), bir bozuk satır (`x;;1;V`, zaman boş) ve bir yorum (`# not`). Beklenen: `ALFA` maksimumu 3.9 olduğu için eşik 3.6'yı aşar ve `UYARI`; `BETA` `TAMAM`; bir hatalı satır. Program bu beklentiyi aynen üretti.

**Adım 3 — Kaba çöz.** Fonksiyonun çıktısını test etmek kolaydır; zor olan, 42 satırlık gövdeyi okuyup her değişkenin hangi aşamada ne olduğunu takip etmektir:

```python
ESIK = 3.6


def rapor_uret(satirlar):
    cihazlar = {}
    hatalar = 0
    for satir in satirlar:
        satir = satir.strip()
        if not satir or satir.startswith("#"):
            continue
        parca = satir.split(";")
        if len(parca) != 4:
            hatalar += 1
            continue
        cihaz, zaman, deger, birim = parca
        if not zaman.isdigit():
            hatalar += 1
            continue
        try:
            deger = float(deger)
        except ValueError:
            hatalar += 1
            continue
        if birim == "mV":
            deger = deger / 1000.0
        elif birim != "V":
            hatalar += 1
            continue
        if cihaz not in cihazlar:
            cihazlar[cihaz] = {"min": deger, "max": deger,
                               "toplam": 0.0, "adet": 0}
        c = cihazlar[cihaz]
        c["min"] = min(c["min"], deger)
        c["max"] = max(c["max"], deger)
        c["toplam"] += deger
        c["adet"] += 1
    cikti = ["CIHAZ       ADET      MIN      MAX    ORT  DURUM"]
    for ad in sorted(cihazlar):
        c = cihazlar[ad]
        ort = c["toplam"] / c["adet"]
        durum = "UYARI" if c["max"] > ESIK else "TAMAM"
        cikti.append("%-10s %5d %8.3f %8.3f %6.3f  %s"
                     % (ad, c["adet"], c["min"], c["max"], ort, durum))
    cikti.append("hatali satir: %d" % hatalar)
    return "\n".join(cikti) + "\n"
```

**Adım 4 — Örüntü.** Beş iş beş bloğa karşılık geliyor. Bloklar bir değişken kümesini paylaşıyor (`cihazlar`, `hatalar`) ve bu paylaşım, her bloğun ne yaptığını sınırlıyor. Sözlük (`{"min": ..., "max": ...}`) bir ilkel takıntısıdır: anahtar adları yazım hatasına açıktır ve veri yapısının ne olduğu sözlükte yazılı değildir.

**Adım 5 — İyileştir.** Dört adımda, her adımdan sonra testi çalıştırarak ilerledik:

- **a) Ayrıştırmayı çıkar.** `satir_ayristir` tek bir satırı ayrıştırır ve bozuk satır için `ValueError` fırlatır. Döngü, `try/except` ile hatalı satırları sayar.
- **b) Sözlüğü sınıfa çevir.** `CihazOzeti`, `min`, `max`, `toplam`, `adet` alanlarını ve `ekle`, `ortalama`, `durum` davranışlarını tutar. İlk değer için `CihazOzeti(deger, deger)` çağrısı, eski `min` ve `max` başlangıcıyla aynı sonucu verir.
- **c) Toplamayı ayır.** `ozetle` yalnızca veriyi toplar ve `(cihazlar, hatalar)` döndürür.
- **d) Biçimlendirmeyi ayır.** `satir_bicimle` tek bir cihaz satırını üretir; `rapor_uret` artık yalnızca bu parçaları birleştirir.

Son sürüm, dört parçanın birleşimidir:

```python
from dataclasses import dataclass

ESIK = 3.6
BASLIK = "CIHAZ       ADET      MIN      MAX    ORT  DURUM"


@dataclass
class CihazOzeti:
    minimum: float
    maksimum: float
    toplam: float = 0.0
    adet: int = 0

    def ekle(self, volt):
        self.minimum = min(self.minimum, volt)
        self.maksimum = max(self.maksimum, volt)
        self.toplam += volt
        self.adet += 1

    def ortalama(self):
        return self.toplam / self.adet

    def durum(self):
        return "UYARI" if self.maksimum > ESIK else "TAMAM"


def satir_ayristir(satir):
    cihaz, zaman, deger, birim = satir.split(";")
    if not zaman.isdigit():
        raise ValueError("zaman")
    deger = float(deger)
    if birim == "mV":
        deger = deger / 1000.0
    elif birim != "V":
        raise ValueError("birim")
    return cihaz, deger
```

```python
def ozetle(satirlar):
    cihazlar = {}
    hatalar = 0
    for satir in satirlar:
        satir = satir.strip()
        if not satir or satir.startswith("#"):
            continue
        try:
            cihaz, deger = satir_ayristir(satir)
        except ValueError:
            hatalar += 1
            continue
        if cihaz not in cihazlar:
            cihazlar[cihaz] = CihazOzeti(deger, deger)
        cihazlar[cihaz].ekle(deger)
    return cihazlar, hatalar


def satir_bicimle(ad, c):
    return "%-10s %5d %8.3f %8.3f %6.3f  %s" % (
        ad, c.adet, c.minimum, c.maksimum, c.ortalama(), c.durum())


def rapor_uret(satirlar):
    cihazlar, hatalar = ozetle(satirlar)
    cikti = [BASLIK]
    for ad in sorted(cihazlar):
        cikti.append(satir_bicimle(ad, cihazlar[ad]))
    cikti.append("hatali satir: %d" % hatalar)
    return "\n".join(cikti) + "\n"
```

**Adım 6 — Doğrula.** Karakterizasyon testi, Bölüm 23.9'da gösterdiğimiz betikle çalışır: 300 tohumlu girdinin çıktı özetleri, eski sürümden alınan altın kayıtla karşılaştırılır. Her adımda ölçüm de aldık:

| Adım | `rapor_uret` satır | `rapor_uret` CC | En yüksek CC | Bozuk (300 içinden) |
|---|---|---|---|---|
| 0 (eski) | 42 | 12 | 12 (`rapor_uret`) | altın kayıt |
| a) `satir_ayristir` | 29 | 8 | 8 (`rapor_uret`) | 0 |
| b) `CihazOzeti` | 23 | 7 | 7 (`rapor_uret`) | 0 |
| c-d) `ozetle`, `satir_bicimle` | 7 | 2 | 6 (`ozetle`) | 0 |

Her adımda bozuk sayısı sıfır kaldı. Testin gerçekten duyarlı olduğunu kontrol etmek için iki bilinçli hata enjekte ettik: eşiği 3.6'dan 3.5'e çekmek 22 bozuk çıktı, sütun sırasını değiştirmek 244 bozuk çıktı üretti (Bölüm 23.9). Yani test, hem birim dönüşümü hem sıralama gibi ince değişiklikleri yakalar.

Bu örnekte dikkat edilecek bir nokta daha var: toplam CC'ye bakarsan, fonksiyon sayısı arttığı için bir miktar yükselmiş olabilir. Ama hiçbir fonksiyon artık beş ayrı işi birden yapmıyor. Okurun her parçayı ayrı ayrı anlayabilmesi, toplam karmaşıklığın bir miktar artmasından daha değerlidir.

**Bunu AI'sız yazabilir misin?** Birimlere `kV` desteği eklemek gerekiyor. Hangi tek fonksiyon değişir? Karakterizasyon testini bu yeni birimi kapsayacak şekilde nasıl güncellersin, ve eski altın kayıt bu güncellemeyle neden geçersiz olur?

## Kendin Yap Projeleri

::: dikkat
Bu iki projede yapay zekâ aracına kod yazdırma. Bölüm 6'daki kuralın aynısı geçerli: önce kendin dene, takıldığında kavramı sor, cevabı değil. Projeyi bitirdikten sonra kendi kodunu bu bölümün örnekleriyle karşılaştır; farkın nedenini yazmak, öğrenmenin asıl kısmıdır.
:::

### Proje 1 (★★): Kendi mini linter'ın

**Amaç.** Python kaynak dosyalarını `ast` ile tarayan ve dört kod kokusunu satır numarasıyla raporlayan küçük bir araç yaz. Araç, Bölüm 23.9'daki `karmasiklik.py`'nin üzerine kurulabilir, ama sıfırdan yazman daha çok şey öğretir.

**Beklenen davranış.** Komut `python linter.py dosya1.py dosya2.py` biçiminde çalışmalı ve her bulgu şu biçimde yazılmalı: `dosya:satir: KOKU ad (deger)`. Dört kural:

- Uzun fonksiyon: 30 satırdan uzun.
- Uzun parametre listesi: 4 ve üzeri parametre.
- Yüksek döngüsel karmaşıklık: CC 10'dan büyük.
- Sihirli sayı: 0, 1, -1 ve 2 dışında kalan sayısal sabitler; yalnızca atama ya da çağrı argümanı olarak kullanıldıklarında. Büyük harfli sabit atamaları (`ESIK = 3.6`) ve varsayılan argümanlar hariç.

**Önerilen yaklaşım.** İpucu olarak: `ast.walk` ile düğümleri gez; sihirli sayı için `ast.Constant` düğümlerini bul ve üst düğümün türünü (atama mı, çağrı mı) kontrol et. Kuralları bir sözlükte tut, eşikleri komut satırı argümanı olarak al. Tam çözüm değil, yalnızca yön göstermek için: önce dört kuralı ayrı fonksiyonlara böl, sonra tek bir dolaşımda hepsini topla.

**Başarı kriterleri.**

- `ex1_eski.py` için en az iki kural uyarısı üretiyor; `ex1_yeni.py` için sihirli sayı uyarısı yalnızca sabit tanımlamayan satırlarda çıkıyor.
- Kendi kitap motorunun (`engine/` altındaki bir dosya) üzerinde çalışıyor ve kaç fonksiyonun işaretlendiğini raporluyor.
- Eşikler komut satırı argümanıyla değiştirilebiliyor.
- Yanlış pozitif (aracın yanlış alarm verdiği) en az iki durumu listeleyip nedenini yazıyorsun.

### Proje 2 (★★★): Eski bir C modülünü güvenceye al ve temizle

**Amaç.** Kendi yazdığın ya da MertOS ve EV Dashboard'dan seçtiğin 150-300 satırlık bir C modülünü, davranışını bozmadan temizlemek.

**Yapılacak.**

1. Modülün açık API'sini belirle. Her herkese açık fonksiyon için bir karakterizasyon testi yaz: tohumlu girdiler üret, çıktıları kaydet (Bölüm 23.9'daki betik bir başlangıç noktası).
2. `-std=c11 -Wall -Wextra -Wshadow -Wconversion` ile uyarısız derle. ASan ve UBSan ile temiz çalıştır.
3. Hata yollarını `goto` ile tek temizleme noktasına bağla. Her kaynağın serbest bırakıldığını `-fanalyzer` ile doğrula.
4. En uzun üç fonksiyonu Extract Function ile böl; her adımda karakterizasyon testini çalıştır.
5. Önce ve sonra için karmaşıklık tablosu üret (kendi aracınla ya da elle; hangi yöntemi kullandığını yaz).

**Önerilen yaklaşım.** Önce davranışı kaydet, sonra temizle. Her dönüşümü ayrı bir kayıt (commit) olarak tut; Bölüm 38'de git ile bunu nasıl yapacağını göreceksin. Sıra değiştiren her dönüşümü (koruma cümleleri gibi) bilerek test et; sıranın davranış olduğunu kendi testinle kanıtla.

**Başarı kriterleri.**

- Karakterizasyon testi her adımda geçiyor ve en az bir bilinçli mutantı (bozuk kopya) yakalıyor.
- Dört bayrakla (`-Wall -Wextra -Wshadow -Wconversion`) uyarısız derleniyor; ASan ve UBSan temiz; `-fanalyzer` uyarısı yok.
- En uzun fonksiyon 30 satırın altında, en yüksek döngüsel karmaşıklık 10'un altında.
- Yapılan her dönüşümün listesi ve nedeni yazılı; hangi dönüşümün hangi testi değiştirdiği belli.

## Ek Alıştırmalar

Aşağıdaki alıştırmalar cevapsız. Her birini önce kâğıda ya da boş bir dosyaya düşünerek çöz; kodu yazdıktan sonra kontrol et.

1. ★ Şu adları gözden geçir: `d`, `flag`, `tmp2`, `aktif_mi`, `bekle`, `data`. Hangileri niyeti söylüyor, hangileri söylemiyor? Her biri için iyi bir ad öner ve nedenini yaz.
2. ★ `kontrol(x)` adlı bir fonksiyon hem girdiyi doğrulayıp hem de bir sayacı artırıyor. Adını ve yapısını nasıl ayırırsın? Komut–sorgu ayrımını kullan.
3. ★ Dört parametreli bir fonksiyonu iki parametreye indirmek istiyorsun. Hangi bilgiyi bir yapıda toplarsın? Yapının adını ve alanlarını yaz; bu yapının neden tek başına bir anlam taşıdığını açıkla.
4. ★★ Derinliği beş olan bir iç içe `if` bloğunu koruma cümleleriyle düzleştir. Koşulların sırasını değiştirmenin davranışı nasıl etkileyebileceğini iki somut örnekle göster.
5. ★★ İki fonksiyon aynı üç satırı içeriyor, ama biri fiyat hesabında, diğeri raporlamada kullanılıyor. Bu satırları tek bir fonksiyonda birleştirmeli misin? Nedenini değişme sebepleri üzerinden açıkla ve hangi testi yazarsın?
6. ★★ Bir C fonksiyonu dört farklı hata yolunda üç kaynak ayırıyor. `goto` etiketlerini nasıl sıralarsın? Etiketleri ters sırada tasarlamanın neden doğru olduğunu bir tabloyla göster.
7. ★★ `sum()` ile döngüsel toplamın float sonuçlarının farklı çıkabileceğini gösteren üç satırlık bir program yaz. Hangisini seçersin ve neden? (Mülakat)
8. ★★ Bir yorum "bu fonksiyon iş parçacığı güvenlidir" diyor, ama içinde paylaşılan bir global sayaç var. Bunu nasıl kanıtlar ya da düzeltirsin? Yorumu ne zaman yazmalısın?
9. ★★★ Bir enum'a yeni bir değer eklemenin `switch` içindeki `default:` dalı varken ve yokken derleyici uyarılarını nasıl etkilediğini `-Wswitch` ile göster. Kod incelemesinde bu bilgiyi nasıl kullanırsın? (Mülakat)
10. ★★★ Bir Python fonksiyonunun döngüsel karmaşıklığını elle hesapla, sonra bu bölümdeki `karmasiklik.py` ile karşılaştır. Farklı çıkan bir durum bul ve nedenini açıkla. (Mülakat)
11. ★★★ `int i` ile `size_t n` karşılaştırmasındaki `-Wsign-compare` uyarısının gerçek bir hataya dönüştüğü bir girdiyi tarif et. `n` gerçekten `INT_MAX`'ı aşacak kadar büyük bir bellek olmadan bunu nasıl test edersin? (Mülakat)
12. ★★★ Savunma sanayiinde kodlama standardında "dinamik bellek ayırma yasak" kuralı olsaydı, Örnek 3'teki `kayit_oku` fonksiyonunu bu kısıtla nasıl yeniden yazardın? Hangi bilgiyi çağıran tarafa bırakırsın? (Mülakat)

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak belgesini okuyacaksın: Linux çekirdeği v6.6 sürümündeki `Documentation/process/coding-style.rst` dosyası. Dosya, `https://raw.githubusercontent.com/torvalds/linux/v6.6/Documentation/process/coding-style.rst` adresinden indirildi ve 1271 satırdır. Bu bölümde yalnızca üç bölüm kullanıyoruz: 6 (Functions), 7 (Centralized exiting of functions) ve 16 (Function return values and names). Belge GPL-2.0 lisanslıdır; aşağıdaki kesit yalnızca kısa bir alıntıdır.

Bölüm 7, `goto` ile merkezi çıkışı anlatırken şu kesiti verir (kaynakta sekmeler kullanılmış; burada 4 boşlukla gösterildi, başka hiçbir değişiklik yok):

```c
int fun(int a)
{
    int result = 0;
    char *buffer;

    buffer = kmalloc(SIZE, GFP_KERNEL);
    if (!buffer)
        return -ENOMEM;

    if (condition1) {
        while (loop1) {
            ...
        }
        result = 1;
        goto out_free_buffer;
    }
    ...
out_free_buffer:
    kfree(buffer);
    return result;
}
```

Belge, etiket adları için şunu söyler: etiket, `goto`'nun ne yaptığını ya da neden orada olduğunu anlatmalıdır. Bölüm 6 ise fonksiyon boyutu için şunu söyler: fonksiyonlar kısa olmalı ve tek bir şey yapmalıdır. Bölüm 16 ise dönüş değeri kuralını verir: eylem adlı fonksiyon hata kodu, yüklem adlı fonksiyon başarı boolean'ı döndürmelidir.

**Sorular — cevaplamadan geçme:**

1. `fun` içindeki `out_free_buffer` etiketi olmadan, fonksiyonun üç ayrı çıkışı olsaydı, her çıkışta `kfree(buffer)` yazmak zorunda kalırdın. Bu durum hata oranını neden artırır? Bölüm 23.6'daki `kayit_oku` örneğiyle karşılaştır.
2. Belge etiket adlarında `err1:` ve `err2:` gibi numaralı adlardan kaçınmayı öneriyor. Bu adların sakıncasını kendi cümlelerinle yaz; yeni bir çıkış yolu eklendiğinde ne olur?
3. Bölüm 16'daki kurala göre `add_work()` ve `pci_dev_present()` ne döndürmelidir? Bu kuralın hangi tür bir hatayı önlediğini, Bölüm 23.2'deki adlandırma kuralıyla birlikte açıkla.
4. Belgenin bir başka bölümünde tek bir `err:` etiketi, bazı yollarda henüz ayrılmamış bir işaretçiyi serbest bırakabilir. Bu hatayı bir örnekle göster ve çözümünü iki etiketle yaz. Örnek 3'teki etiketlerle karşılaştır.
5. Bölüm 6, bir fonksiyonun 5-10'dan fazla yerel değişken içermemesini öneriyor. Bu sayı neden kesin bir kural değil de bir işaret? Bölüm 23.9'daki karmaşıklık ölçümüyle ilişkisini düşün.
6. (Mülakat) `fun` içinde `result` değişkeni neden 0 ile başlatılmış? `goto` kullanılmayan bir sürümde `result` yerine ne yazardın, ve bu sürümde hangi çıkış yolunda bir temizlik hatası olasılığı artar?

## Bölüm Özeti

Bu bölümde kodun okunabilirliğini ölçülebilir parçalara ayırıp her birini bir araçla ve bir testle destekledik:

- Adlar niyet söyler: kapsamla orantılı uzunlukta, boolean adları bir soru gibi okunur, kısaltmalar yalnızca ekipçe yerleşmişse kullanılır. Türkçe ve İngilizce adlar aynı kod tabanında karıştırılmaz.
- Fonksiyonlar kısa, tek iş yapar ve yan etkisi adından anlaşılır. Komut ve sorgu ayrılır; koruma cümleleri iç içe yapıyı düzleştirir, ama koşulların sırası davranışın parçasıdır.
- Yorumlar NEDEN'i anlatır. Eskimiş yorum, kodla çelişen yorumdan daha tehlikelidir; mümkünse yorumun yerine ad ya da sabit kullanılır.
- Biçim araçları (clang-format, black) tartışmayı bitirir; derleyici uyarıları (`-Wshadow`, `-Wconversion`), clang-tidy ve mypy gibi araçlar hataları çalıştırmadan yakalar. Bu bölümde bunların hepsinin gerçek hataları bulduğunu gördük.
- Hata yolları tek bir yerde temizlenir: C'de `goto` ile ters sıralı temizlik, C++'ta RAII, Python'da istisnayı yutmadan bağlamla zincirlemek.
- Sihirli sayılar adlandırılır, tekrar yalnızca aynı değişme nedenine sahip kopyalar için birleştirilir; tip koşulları ihtiyaç duyulduğunda polimorfizme çevrilir.
- Refactoring davranışı koruyan küçük adımlarla yapılır; her adım karakterizasyon testiyle doğrulanır ve test, bilinçli mutantlarla sınanır.
- Döngüsel karmaşıklık koşul sayısını ölçer; iç içe yapının zihinsel yükünü ise derinlik ve bilişsel bir puan daha iyi yansıtır. Tek bir metriğe güvenmek yanıltıcıdır.
- Savunma sanayiinde MISRA C, CERT C ve JSF AV C++ gibi standartlar kısıtları belirler; araçlarla denetlenebilen kısmı otomatikleşir, kalanı kod incelemesiyle kontrol edilir.

### Kısım V'in kapanışı

Kısım V'te dört ayrı bölümde aynı soruya farklı açılardan baktık: kod, bir sistemi nasıl taşır? Bölüm 20'de sınıflar ve kalıtımla veri ile davranışı birlikte paketledik. Bölüm 21'de SOLID ile her parçanın hangi sorumluluğu taşıdığını ve bağımlılıkların nereye yöneleceğini gördük. Bölüm 22'de tekrar eden tasarım sorunlarına adlandırılmış çözümler, yani kalıplar, ele aldık. Bölüm 23'te ise bu tasarımın kod düzeyinde nasıl okunur ve değiştirilebilir kaldığını inceledik: bir adın, bir fonksiyonun, bir yorumun ve bir hata yolunun ne kadarının okurun kafasında yük olduğunu.

Kısım V'in ortak fikri şudur: iyi tasarım, değişikliğin maliyetini düşürmektir. Kod bugün çalışıyorsa yeterli değildir; yarın bir hata düzeltmesi ya da yeni bir özellik için güvenle değiştirilebiliyorsa iyidir. Bu bölümdeki her araç ve her test, bu güveni bir adım daha sağlamlaştırmak için var.

**Sonraki bölümde:** Bölüm 24 (CPU Mimarisi) ile Kısım VI — İşletim Sistemi & Mimari başlıyor. Şimdiye kadar kodu bir insanın okuyacağı bir metin olarak ele aldık; Kısım VI'da bu kodun donanımda nasıl çalıştığına bakacağız: komutlar, yazmaçlar, önbellekler ve bunların C kodundaki bir atamaya nasıl karşılık geldiği. Bölüm 23'teki hata yolları ve kaynak yönetimi, orada işletim sisteminin bellek ve süreç yönetimiyle birlikte yeniden karşımıza çıkacak.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. İyi bir değişken adı ile kötü bir değişken adı arasındaki farkı, okurun bilişsel yükü üzerinden açıklar mısın? Kısa ad ne zaman doğrudur?
2. Döngüsel karmaşıklık ile bilişsel karmaşıklık neden farklı sonuçlar verebilir? Koruma cümlelerine geçmek CC'yi değiştirmezken okunabilirliği neden değiştirir?
3. C'de hata yönetimi için `goto` kullanmak neden yaygındır, ama bunun tehlikeleri nelerdir? RAII bu tehlikelerin hangilerini ortadan kaldırır?
4. Bir fonksiyonu test etmeden refactor etmek neden tehlikelidir? Karakterizasyon testi ile birim testi arasındaki fark nedir?
5. Bir enum'a yeni bir değer eklendiğinde `default:` dalı olan ve olmayan `switch` bloklarında ne olur? Bu bir tasarım kararı mıdır?
6. Kod kokusu ile hata arasındaki fark nedir? Hata olmayan bir kodu neden yine de değiştirmek isteyebilirsin?
7. Bir ekipte Türkçe ve İngilizce adların karışması hangi somut sorunlara yol açar? Bu kararı kim ve nasıl vermelidir?
8. MISRA C gibi bir standart, tanımsız davranışın bazı türlerini neden yasaklar? Derleyici uyarıları ile standart kuralları arasındaki ilişki nedir?
:::
