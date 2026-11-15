%% kisim_no: III
%% kisim_ad: Veri Yapıları
%% bolum_no: 9
%% baslik: Hash Table

## Giriş: Aramak yerine hesaplamak

Bölüm 5'ten beri bir sihir kullanıyoruz. "Bu değeri daha önce gördüm mü?" sorusunu soruyoruz ve cevap anında geliyor. İki Toplam'ı O(n)'e indiren, kelime frekansını tek geçişte sayan, anagramları gruplayan hep aynı şeydi: **sözlük**. Şimdiye kadar onu bir kara kutu olarak kullandık. Bu bölümde kutuyu açıyoruz.

Şimdiye kadar öğrendiğimiz tüm arama yöntemleri iki gruba giriyordu: ya elemanları **tek tek gezdik** (dizide, bağlı listede — O(n)), ya da sıralılıktan yararlanıp **aralığı böldük** (ikili arama — O(log n)). Hash tablosu üçüncü ve tamamen farklı bir fikir sunar: **elemanı hiç aramayalım; nerede olduğunu hesaplayalım.**

Bu fikrin sonucu sarsıcıdır: bir milyon kayıtlı bir sözlükte arama, on kayıtlı bir sözlükteki aramayla **aynı süreyi** alır. Ortalama O(1). Bu yüzden hash tablosu, muhtemelen bilgisayar biliminin en çok kullanılan veri yapısıdır — Python `dict`, JavaScript nesneleri, veritabanı indeksleri, derleyicilerin sembol tabloları, ağ yönlendirme tabloları, önbellekler, `MertOS`'un süreç tablosu... liste uzayıp gider.

Ama bedava değil. Bu bölümde üç şeyi öğreneceksin: fikrin *nasıl* çalıştığı, kaçınılmaz olarak *nerede tıkandığı* (çakışmalar), ve mühendislerin bu tıkanmayı *nasıl* çözdüğü. Sonunda "O(1) ortalama" ifadesindeki hem "O(1)"i hem de "ortalama"yı hak ederek anlamış olacaksın.

::: not
Bu bölüm Bölüm 7'nin bir devamı gibi okunmalı. Orada öğrendiğin üç şey burada doğrudan iş görecek: dizinin O(1) indeks erişimi (hash tablosunun temeli), bağlı liste (zincirleme çözümü), ve amortize analiz (yeniden hash'leme). Aynı fikirlerin yeni bir sentezini kuracağız.
:::

## 9.1 Temel fikir: adresi veriden üretmek

Bir düşünce deneyiyle başlayalım. Anahtarların 0-99 arası tam sayı olduğunu varsay. En hızlı yapı nedir? Basit: 100 elemanlı bir dizi. `dizi[42]` ile 42 numaralı kaydı O(1)'de bulursun. Buna **doğrudan adresleme tablosu** denir ve mükemmeldir.

Peki anahtarlar string ise? Ya da anahtarlar 0-99 değil de 0 ile 2 milyar arasında dağılmış birkaç yüz sayıysa? İki milyar elemanlık dizi ayıramazsın. İşte hash fonksiyonu tam bu boşluğu doldurur:

![Şekil 9.1: Hash tablosunun temel fikri. Hash fonksiyonu, anahtarı (ne olursa olsun) bir sayıya çevirir; modülo işlemi bu sayıyı tablo boyutuna sıkıştırır. Sonuç, doğrudan kullanılabilir bir dizi indeksidir — arama yok, hesaplama var.](gorseller/b09_temel.png)

Formül tek satırdır:

`indeks = h(anahtar) % M`

Burada `h` **hash fonksiyonu** (anahtarı bir tam sayıya çevirir), `M` tablo boyutu (kova sayısı). Tablodaki her hücreye **kova (bucket)** denir.

Kritik nokta şu: hash fonksiyonu, **çok büyük bir evreni** (tüm olası stringler, tüm olası sayılar) **çok küçük bir kümeye** (0 ile M-1 arası) sıkıştırır. Bu sıkıştırma kayıplıdır ve tam da bu yüzden çakışmalar kaçınılmazdır — 9.3'te matematiğini göreceğiz.

Temel işlemler bu formül üzerine kurulur:

| İşlem | Nasıl çalışır | Ortalama | En kötü |
|---|---|---|---|
| Ekle | indeksi hesapla, kovaya koy | O(1) | O(n) |
| Ara | indeksi hesapla, kovaya bak | O(1) | O(n) |
| Sil | indeksi hesapla, kovadan çıkar | O(1) | O(n) |

"En kötü O(n)" sütununu unutma; 9.8'de bunun gerçek bir saldırı yüzeyi olduğunu göreceğiz.

## 9.2 Hash fonksiyonu tasarımı

Hash tablosunun tüm performansı, hash fonksiyonunun kalitesine bağlıdır. İyi bir hash fonksiyonunun dört özelliği vardır:

**1. Deterministik.** Aynı anahtar her zaman aynı değeri vermeli. Aksi hâlde koyduğun yeri bulamazsın.

**2. Hızlı.** Hash hesabı O(1) olmalı, yoksa kazandığın hızı hesaplamaya harcarsın.

**3. Düzgün dağıtan (uniform).** Anahtarlar kovalara mümkün olduğunca eşit dağılmalı. Yığılma varsa bazı kovalar uzar, arama yavaşlar.

**4. Çığ etkisi (avalanche).** Anahtarda tek bir bitin değişmesi, hash değerinde büyük bir değişikliğe yol açmalı. Benzer anahtarlar (`"kullanici1"`, `"kullanici2"`) uzak kovalara düşmeli.

### Kötü hash örneği ve neden kötü olduğu

En sık yapılan naif tasarım, karakterlerin ASCII değerlerini toplamaktır:

```c
unsigned kotu_hash(const char *s) {
    unsigned h = 0;
    while (*s) h += (unsigned char)*s++;   /* sadece topla */
    return h;
}
```

Bu fonksiyon üç ağır kusur taşır. **Birincisi:** toplama sırayı umursamaz, dolayısıyla tüm anagramlar aynı kovaya düşer — `"kar"`, `"rak"`, `"ark"` hep çakışır (Bölüm 5'teki anagram örneğini hatırla, orada bu bir *özellikti*; burada bir *kusurdur*). **İkincisi:** dağılım berbattır; küçük harfli 10 karakterli kelimelerde toplam yaklaşık 970-1220 arasına sıkışır, dolayısıyla büyük bir tablonun çoğu kovası hiç kullanılmaz. **Üçüncüsü:** çığ etkisi yoktur; bir harfi bir değiştirmek hash'i yalnız bir değiştirir.

### İyi hash örneği: polinom yuvarlama

Yaygın ve iyi çalışan bir kalıp, karakterleri bir çarpanla ilerleterek karıştırmaktır. Meşhur **djb2** fonksiyonu:

```c
unsigned long djb2(const char *s) {
    unsigned long h = 5381;
    int c;
    while ((c = (unsigned char)*s++))
        h = ((h << 5) + h) + c;     /* h * 33 + c */
    return h;
}
```

`h << 5` + `h` ifadesi `h * 33`'tür (Bölüm 1'in kaydırma numarası). Neden 33? Deneysel olarak iyi dağıtıyor — kriptografik bir gerekçesi yok, ama pratikte kanıtlanmış. Kritik olan, her karakterin *konumuna göre* farklı ağırlık alması: sıra artık önemli, anagram sorunu yok. Bu bilinçli bir tercihtir: C sürümü `unsigned long` kullandığı için değeri platforma göre 32 ya da 64 bit taşar; Örnek 3'teki Python sürümü ise 32 bite maskelenmiştir, bu yüzden iki sürümün değerleri farklı çıkabilir.

Benzer ailedeki diğer klasikler: **FNV-1a**, **MurmurHash**, **xxHash**. Bunlara **kriptografik olmayan** hash denir: hızlıdırlar ama bir saldırganın çakışma üretmesini engellemezler. SHA-256 gibi **kriptografik** hash'ler bunu engeller ama kat kat yavaştır — Bölüm 32'de neden ikisinin farklı işler için olduğunu göreceğiz.

::: dikkat
Modülo alırken tablo boyutu `M`'nin seçimi önemlidir. `M` 2'nin kuvvetiyse `h % M` işlemi yalnız hash'in **alt bitlerini** kullanır (`h & (M-1)`); hash fonksiyonun alt bitleri zayıfsa dağılım bozulur. Klasik çözüm `M`'yi **asal sayı** seçmektir. Alternatif — ki modern kütüphanelerin tercihi budur — `M`'yi 2'nin kuvveti tutup hash'i ekstra bir karıştırma adımından geçirmektir (Java'nın `HashMap`'i `h ^ (h >>> 16)` yapar). Kod Okuma egzersizinde CPython'un bu sorunu nasıl çözdüğünü göreceksin.
:::

Python'da bu makine hazır gelir: `hash(nesne)` yerleşik fonksiyonu. Kendi sınıfın için `__hash__` yazabilirsin — ama bir kuralla: **eşit nesnelerin hash'i eşit olmalıdır** (`a == b` ise `hash(a) == hash(b)`). Tersi gerekmez (farklı nesnelerin hash'i çakışabilir). Bu sözleşmeyi bozarsan sözlüğün sessizce yanlış çalışır: koyduğun anahtarı bulamazsın.

## 9.3 Çakışma kaçınılmazdır

Şimdi kötü haberi matematikle verelim. Anahtar evreni tablo boyutundan büyükse — ki her zaman öyledir — iki farklı anahtarın aynı kovaya düşmesi kaçınılmazdır. Bunun adı **çakışmadır (collision)** ve nedeni **güvercin yuvası ilkesidir**: 10 güvercini 9 yuvaya koyarsan, en az bir yuvada iki güvercin olur.

Ama asıl şaşırtıcı olan, çakışmanın *ne kadar erken* geldiğidir:

![Şekil 9.2: Doğum günü paradoksu. 365 kovalı bir tabloya rastgele anahtarlar eklendiğinde, yalnız 23 anahtardan sonra çakışma olasılığı %50'yi geçer. Sezgi "365'e yakın olunca çakışır" der; gerçek, karekökü mertebesindedir (√365 ≈ 19).](gorseller/b09_dogumgunu.png)

Bu, **doğum günü paradoksu** olarak bilinir: bir odada 23 kişi varsa, ikisinin doğum gününün aynı olma olasılığı %50'den fazladır. Sezgiye aykırıdır çünkü kişi sayısını değil, *kişi çiftlerinin* sayısını (23×22/2 = 253 çift) düşünmek gerekir.

Hash tablosu için sonuç nettir: **çakışmayı önlemeye çalışma; onunla yaşamayı öğren.** M kovalı bir tabloda yaklaşık √M anahtardan sonra çakışma beklenir. Dolayısıyla her hash tablosu gerçeklemesi bir **çakışma stratejisi** içermek zorundadır. İki ana aile var ve ikisini de göreceğiz.

## 9.4 Zincirleme: çakışanları listeye diz

En doğrudan çözüm: her kovaya tek bir eleman değil, bir **liste** koy. Aynı kovaya düşenler o listede birikir.

![Şekil 9.3: Zincirleme. Her kova bir bağlı listenin başıdır. Çakışanlar aynı listede toplanır; arama, kovayı bulup listede gezmektir. Kova 3'te üç eleman varsa o kovadaki arama üç adım sürer.](gorseller/b09_zincir.png)

Gerçeklemesi, Bölüm 7'nin bağlı listesinin doğrudan kullanımıdır:

```c
typedef struct Dugum {
    char *anahtar;
    int deger;
    struct Dugum *sonraki;
} Dugum;

typedef struct {
    Dugum **kovalar;        /* Dugum* dizisi */
    size_t M, n;            /* kova sayısı, eleman sayısı */
} Tablo;

int tablo_ara(Tablo *t, const char *anahtar, int *cikan) {
    size_t i = djb2(anahtar) % t->M;      /* indeksi hesapla */
    for (Dugum *p = t->kovalar[i]; p; p = p->sonraki)
        if (strcmp(p->anahtar, anahtar) == 0) {   /* tam eşleşme */
            *cikan = p->deger;
            return 1;
        }
    return 0;
}
```

Dikkat edilecek kritik ayrıntı: hash eşleşmesi **yetmez**, anahtarın kendisi de karşılaştırılmalıdır (`strcmp`). Çünkü aynı kovada farklı anahtarlar olabilir. Bu kontrolü atlamak, sessizce yanlış veri döndüren bir hataya yol açar.

**Maliyet analizi.** n eleman, M kova varsa ortalama zincir uzunluğu `α = n / M`'dir. Buna **yük faktörü (load factor)** denir. Arama maliyeti: kovayı bulmak O(1) + zincirde gezmek O(α), yani **O(1 + α)**. α'yı sabit tutabilirsek (örneğin 1 civarında), arama O(1) olur — hash tablosunun vaadi budur.

**Artıları:** Silme kolaydır (listeden çıkar, başka hiçbir şey bozulmaz). α > 1 olsa bile çalışır, tablo "dolmaz". Uygulaması basit ve hataya az açıktır.

**Eksileri:** Her düğüm ayrı bir `malloc` demek — hem yavaş hem bellek israfı (düğüm başına bir işaretçi fazladan). Ve Bölüm 7.2'nin dersi: düğümler bellekte dağınık olduğu için **cache dostu değildir**. İşte bir sonraki yaklaşım tam bu sorunu çözer.

## 9.5 Açık adresleme: boş kova ara

İkinci aile bambaşka bir yol izler: **hiç liste yok**, her şey tek bir dizide. Kova doluysa, belirli bir kurala göre *başka bir kova* denenir. Buna **sondalama (probing)** denir.

![Şekil 9.4: Açık adresleme. Üstte doğrusal sondalama: dolu kova bulununca bir sağa bakılır. Bitişik dolu bloklar (kümeler) büyüdükçe aramalar uzar. Altta silme tuzağı: kovayı boşaltmak arama zincirini kopardığı için "mezar taşı" bırakmak gerekir.](gorseller/b09_acik.png)

Üç klasik sondalama stratejisi vardır:

**Doğrusal sondalama (linear probing).** Sıradaki kovaya bak: `i, i+1, i+2, ...`. Basit ve **çok cache dostudur** (komşu bellek okur). Kusuru **birincil kümelenme (primary clustering)**: dolu hücreler bitişik bloklar oluşturur ve bu bloklar büyüdükçe kendilerini besler — bloğa düşen her yeni anahtar bloğu daha da uzatır.

**Karesel sondalama (quadratic probing).** Adımları büyüterek atla: `i, i+1², i+2², i+3², ...`. Kümelenmeyi dağıtır ama **ikincil kümelenme** kalır: aynı ilk indekse düşen anahtarlar hep aynı sondalama dizisini izler. Ayrıca tüm kovaları ziyaret etmesi garanti değildir (M asal ve α < 0.5 ise garanti edilir).

**Çift hash'leme (double hashing).** Adım büyüklüğünü ikinci bir hash fonksiyonundan al: `i + k·h₂(anahtar)`. Her anahtar kendi sondalama dizisini izler, ikincil kümelenme de biter. En iyi dağılımı verir; bedeli ikinci bir hash hesabı ve daha kötü cache davranışıdır.

### Silme tuzağı: mezar taşları

Açık adreslemenin en sinsi ayrıntısı silmedir. Diyelim `Mert` kova 2'ye düştü, `Efe` de 2'ye düşüp 3'e kaydı. Şimdi `Mert`'i silip kova 2'yi boşaltırsan ne olur? `Efe`'yi ararken kova 2'ye bakarsın, boş görürsün ve **"yok" diye sonuç dönersin** — oysa 3'te duruyor. Arama zinciri koptu.

Çözüm, silinen hücreye özel bir işaret bırakmaktır: **mezar taşı (tombstone)**. Anlamı: *"burası şu an boş ama bir zamanlar doluydu, aramaya devam et."* Ekleme yaparken mezar taşı kullanılabilir, arama yaparken üzerinden geçilir. Bedeli: mezar taşları biriktikçe aramalar uzar, dolayısıyla ara sıra tablonun tamamen yeniden inşa edilmesi gerekir.

**Artıları:** Tek dizi → mükemmel cache davranışı, işaretçi yok, `malloc` yok. Bellek verimli. Modern yüksek performanslı hash tabloları (Python `dict`, Google'ın `absl::flat_hash_map`) bu aileden.

**Eksileri:** Silme karmaşık (mezar taşı). Tablo dolmaya yaklaşınca performans çöker — bu yüzden yük faktörünü sıkı tutmak *zorunludur*.

## 9.6 Yük faktörü ve yeniden hash'leme

Yük faktörü `α = n / M`, hash tablosunun sağlık göstergesidir. Ve etkisi doğrusal değil, **patlayıcıdır**:

![Şekil 9.5: Yük faktörünün maliyeti. Zincirlemede maliyet α ile doğrusal artar (başarısız arama: 1 + α). Doğrusal sondalamada ise α → 1 iken maliyet dikey olarak patlar: ½(1 + 1/(1−α)) (başarılı arama, yaklaşık). Bu yüzden gerçek kütüphaneler α'yı 0.66–0.75 civarında sınırlar.](gorseller/b09_yuk.png)

Grafiğin anlattığı şu: α = 0.5'te doğrusal sondalama, başarılı bir arama için ortalama 1.5 sonda yapar — gayet iyi. α = 0.9'da 5.5 sondaya çıkar. α = 0.99'da ise yaklaşık 50.5'e fırlar. Yani tablo dolmaya yaklaştıkça O(1) vaadi çöker.

Yukarıdaki sayılar **başarılı arama** içindir. Başarısız arama (ve ekleme, boş bir kova bulunana kadar) daha pahalıdır ve formülü ½(1 + 1/(1−α)²)'dir: α = 0.9'da bu yaklaşık 50.5 sonda eder, yani başarılı aramanın yaklaşık 9 katı. Zincirlemede ise durum çok daha yumuşaktır: başarılı arama ≈ 1 + α/2, başarısız arama ≈ 1 + α sonda.

Çözüm, α'yı bir eşiğin altında **tutmaktır**. Bu kitapta zincirleme tablomuz için eşik **α > 0.75**, büyüme ise **M → 2M** (kapasiteyi ikiye katlamak) olarak alınır; Örnek 2'deki kod tam olarak bunu yapar. Açık adreslemede sondalama uzadıkça maliyet daha hızlı arttığı için eşik daha sıkıdır: **α > 0.66** (Kendin Yap 1). Eşik aşılınca daha büyük bir tablo ayrılır ve **tüm gerçek elemanlar yeni tabloya yeniden yerleştirilir**: her anahtar yeni M'ye göre `h(anahtar) % yeniM` ile yeniden hesaplanır. Rehash sırasında mezar taşları da atılır; yalnız gerçek elemanlar taşınır:

![Şekil 9.6: Yeniden hash'leme. Tablo boyutu M değişince `h(anahtar) % M` sonucu da değişir — bu yüzden eski yerler geçersizdir ve her anahtar yeniden hesaplanıp taşınmalıdır. Tek bir ekleme O(n) sürebilir; ama Bölüm 7'deki geometrik büyüme sayesinde amortize maliyet O(1) kalır.](gorseller/b09_rehash.png)

Kritik nokta: **eski hash değerleri yeniden kullanılamaz**, çünkü modülo tabanı değişti. `h % 4 = 3` olan bir anahtar, `h % 8` ile bambaşka bir yere düşebilir. Bu yüzden rehashing gerçekten O(n) iş yapar.

Ama Bölüm 7'nin amortize analizi burada da geçerlidir: tabloyu her seferinde **ikiye katlarsak**, n ekleme boyunca toplam yeniden yerleştirme işi `1 + 2 + 4 + ... + n < 2n` olur. Ekleme başına ortalama sabit → **amortize O(1)**. Aynı geometrik seri, aynı sonuç.

Pratikte kullanılan eşikler:

| Kütüphane | Strateji | Eşik α | Büyüme |
|---|---|---|---|
| Python `dict` | açık adresleme | 2/3 | ×2 (veya ×4) |
| Java `HashMap` | zincirleme (+ağaç) | 0.75 | ×2 |
| C++ `unordered_map` | zincirleme | 1.0 | ×2 (asal) |
| Go `map` | zincirleme (kova=8) | 6.5 (kova başına) | ×2 |

::: dikkat
Yeniden hash'leme, hash tablosunun **en kötü durum gecikmesinin** kaynağıdır. Milyon elemanlı bir sözlüğe eleman eklerken bir anda milyonlarca yeniden yerleştirme tetiklenebilir. Ortalama hızlı ama *öngörülemez* olan bu davranış, gerçek zamanlı sistemlerde (uçuş kontrol, ses işleme) kabul edilemez olabilir — Bölüm 7'de bağlı liste için söylediğimizin aynısı. Böyle yerlerde ya baştan yeterince büyük tablo ayrılır ya da başka yapılar seçilir.
:::

## 9.7 Gerçek dünya: Python dict ve akrabaları

Teoriyi gerçek gerçeklemelerle karşılaştırmak, tasarım kararlarını görmenin en iyi yoludur.

**Python `dict`** açık adresleme kullanır ve sondalama dizisi alışılmadıktır: `i = (i*5 + perturb + 1) & mask`, burada `perturb` her adımda hash'in üst bitlerinden beslenir. Bu, doğrusal sondalamanın cache avantajını korurken kümelenmeyi kırar — Kod Okuma egzersizinde bu satırı inceleyeceğiz.

Python 3.7'den beri `dict` **ekleme sırasını korur** ve bu bir yan üründür, bilinçli bir "sıralı yapı" tasarımı değildir. Sır şu: tablo ikiye ayrılmıştır — küçük bir *indeks dizisi* ve elemanların ekleme sırasıyla dizildiği yoğun bir *giriş dizisi*. Bu **compact dict** tasarımı hem dikkate değer bir bellek tasarrufu sağladı hem de sırayı bedavaya korudu. Güzel bir mühendislik hikâyesi: performans için yapılan bir değişiklik, kullanıcıya ek bir garanti hediye etti.

**Java `HashMap`** zincirleme kullanır ama bir hilesi vardır: bir kovadaki zincir en az 8 elemana ulaşırsa ve tablo kapasitesi en az 64 ise, o zincir bir **kırmızı-siyah ağaca** dönüştürülür (buna *treeify* denir). Tablo 64'ten küçükse treeify yerine önce tablo büyütülür; çünkü zincirin uzamasının asıl sebebi çoğu zaman yetersiz kapasitedir. Böylece en kötü durum O(n)'den O(log n)'e iner — 9.8'deki saldırıya karşı bir savunma. (Ağaçlar Bölüm 10'da.)

**C++ `unordered_map`** standart gereği zincirleme kullanır ve bu bir *zorunluluktur*: standart, elemanlara verilen işaretçilerin ve referansların rehashing sonrası geçerli kalmasını şart koşar. Bu garanti açık adreslemeyle sağlanamaz. Sonuç: `unordered_map` genelde modern açık adreslemeli alternatiflerden (`absl::flat_hash_map`, `robin_hood`) yavaştır — standart bir garantiyi korumak için ödenen performans bedeli.

## 9.8 Sınırlar ve saldırı yüzeyi

Hash tablosu her derde deva değildir. Sınırlarını bilmek, ne zaman *kullanmayacağını* bilmektir.

**Sıra yoktur.** Hash tablosu elemanları rastgele dağıtır. "En küçük anahtar", "5 ile 9 arasındaki anahtarlar", "sıralı gez" gibi isteklerin hiçbirini O(1)'de yapamaz — hepsi tüm tabloyu taramayı gerektirir. Bu ihtiyaçların yapısı **dengeli arama ağacıdır** (Bölüm 10). Bölüm 5'in karar ağacındaki ayrım tam olarak buydu.

**En kötü durum O(n)'dir.** Tüm anahtarlar aynı kovaya düşerse hash tablosu bir bağlı listeye dönüşür. Rastgele veride bu olmaz — ama **veri rastgele olmayabilir**.

**Hash flooding saldırısı.** Bir saldırgan, hash fonksiyonunu bilirse *kasıtlı olarak* hepsi aynı kovaya düşen anahtarlar üretebilir. Bir web sunucusuna böyle hazırlanmış birkaç bin form alanı gönderirsen, sunucunun sözlüğü O(n²) davranmaya başlar ve CPU'yu tüketir — hizmet dışı bırakma (DoS) saldırısı. 2011'de PHP, Java, Python, Ruby dahil neredeyse tüm popüler diller bu açıkla sarsıldı.

Çözüm iki katmanlı oldu: **rastgele tohum (randomized seeding)** — her programın hash fonksiyonu farklı bir gizli tohumla başlar, böylece saldırgan hangi anahtarların çakışacağını bilemez; ve **SipHash** gibi hızlı ama saldırıya dayanıklı fonksiyonlar. Python'da `PYTHONHASHSEED` ortam değişkeni bu davranışı kontrol eder; bu yüzden Python'da `hash("abc")` her çalıştırmada farklı çıkar.

**Anahtar değişmez olmalıdır.** Bölüm 3'ün mutable/immutable ayrımı burada kritik bir sonuca varır: bir nesneyi anahtar yaptıktan sonra *değiştirirsen*, hash'i değişir ve nesne artık bulunduğu kovada aranmaz — sözlüğe koyduğun şey kaybolur. Bu yüzden Python `list`'i anahtar olarak kabul etmez ama `tuple`'ı eder:

```python
d = {}
d[(1, 2)] = "nokta"      # tuple: değişmez, anahtar olabilir
d[[1, 2]] = "hata"       # TypeError: unhashable type: 'list'
```

Bölüm 3'te "tuple neden dict anahtarı olabilir?" diye sormuştuk; cevabı buydu.

### Universal hashing

Saldırı sorununa teorik bir cevap da var. Fikir şu: hash fonksiyonunu tek bir sabit olarak değil, bir **aile** olarak düşün ve program başladığında aileden rastgele bir üye seç. Klasik aile (Carter ve Wegman, 1979) şudur:

`h(x) = ((a·x + b) mod p) mod M`

Burada `p` anahtar evreninden büyük bir asaldır, `a` 1 ile p−1 arasından, `b` ise 0 ile p−1 arasından rastgele seçilir. Anahtarların tam sayı olduğu varsayılır; string'ler önce bir tam sayıya çevrilir.

Ailenin özelliği şudur: herhangi iki **farklı** anahtar x ≠ y için, `a` ve `b` rastgele seçildiğinde çakışma olasılığı en fazla 1/M'dir. Buna **evrensel (universal)** hash denir. Sonuç olarak bir anahtarın kovasındaki beklenen diğer eleman sayısı en fazla (n−1)/M ≈ α olur; yani beklenen zincir uzunluğu yine O(1 + α)'dır.

Peki bu neden saldırıyı durdurur? Saldırgan hangi `a` ve `b`'nin seçildiğini bilmez. "Şu anahtarlar hepsi aynı kovaya düşer" diyebilmek için seçilen tohumu bilmesi gerekir; tohum rastgeleyse saldırganın önceden hazırlayabileceği bir çakışma kümesi yoktur. Bu, yukarıdaki rastgele tohum fikrinin matematiksel karşılığıdır.

Dikkat: bu bir **beklenen değer** garantisidir; her çalıştırmada değil, rastgele seçim üzerinden ortalamada geçerlidir. Uygulamada bu aileyi doğrudan kullanmak yerine SipHash gibi anahtarlı (gizli tohumlu) fonksiyonlar aynı ihtiyacı karşılar. Yine de teoriyi bilmek, "saldırıya dayanıklı hash" konuşmasında neyin neyi garanti ettiğini ayırt etmeni sağlar.

```python
import random

P = 2**61 - 1        # asal; anahtar evreninden büyük olmalı

def yeni_hash(M):
    a = random.randrange(1, P)   # program başında bir kez seç
    b = random.randrange(0, P)
    return lambda x: ((a * x + b) % P) % M
```

Kullanım: `h = yeni_hash(16)`; her çalıştırmada farklı bir `h` gelir ve `h(12345)` değeri de değişir.

## 9.9 Küme ve hash'in diğer işleri

**Küme (set)**, değeri olmayan bir hash tablosudur: yalnız anahtarları tutar. "Bu eleman var mı?" sorusunu O(1)'de cevaplar. Bölüm 5'teki kayan pencere çözümünde kullandığımız `set` tam olarak budur. Kesişim, birleşim, fark işlemleri de doğal olarak gelir.

Hash fikri veri yapısının ötesinde de çalışır:

- **Sağlama toplamı (checksum) ve parmak izi.** Büyük bir dosyanın hash'i, içeriğinin kısa bir özetidir. İki dosyanın aynı olup olmadığını, dosyaları baştan sona karşılaştırmadan kontrol edebilirsin — Kendin Yap 2'de bunu yapacaksın.
- **Yinelenen veri temizliği (deduplication).** Yedekleme sistemleri ve `git` (Bölüm 38: her nesne içeriğinin SHA-1'iyle adlandırılır) bu fikri kullanır.
- **Önbellek anahtarı.** Bir hesabın sonucunu saklarken, girdilerin hash'i anahtar olur (memoization — Bölüm 16).
- **Tutarlı hash'leme (consistent hashing).** Dağıtık sistemlerde verinin hangi sunucuya gideceğini belirler; sunucu eklenip çıkarıldığında verinin çoğunun yerinde kalmasını sağlar (Bölüm 41).
- **Bloom filtresi.** Birden çok hash fonksiyonu kullanan, olasılıksal bir üyelik yapısı: "kesinlikle yok" ya da "muhtemelen var" der. Çok az bellekle devasa kümeleri sorgulamak için kullanılır.

## Çözümlü Örnekler

### Örnek 1 (★): İlk tekrarsız karakter

**Problem:** Bir dizgideki ilk tekrarsız karakteri bul. `"aabbcdd"` → `'c'`. Yoksa `None`.

**Adım 1-2 (anla, örnekle).** Girdi `str`, çıktı karakter ya da `None`. Kenar durumlar: boş dizgi (`None`), hepsi tekrarlı (`"aabb"` → `None`), tek karakter (`"a"` → `'a'`). Elle nasıl çözerim? Her karakter için "başka yerde geçiyor mu?" diye bakarım — yani **sayarım**.

**Adım 3-4 (kaba çöz, örüntü).** Kaba kuvvet: her karakter için tüm dizgiyi tara — O(n²). Örüntü tablosu: "sayma" → **hash tablosu**.

**Adım 5 (iyileştir).** İki geçiş: önce say, sonra ilk sayısı 1 olanı bul.

```python
def ilk_tekrarsiz(s):
    sayac = {}
    for ch in s:                          # 1. geçiş: say
        sayac[ch] = sayac.get(ch, 0) + 1
    for ch in s:                          # 2. geçiş: sırayla ara
        if sayac[ch] == 1:
            return ch
    return None
```

**Adım 6 (doğrula).** `"aabbcdd"`: sayaç `{a:2, b:2, c:1, d:2}`. İkinci geçişte `a`(2), `a`(2), `b`(2), `b`(2), `c`(1) → **`'c'`**. Doğru.

Neden **iki** geçiş? Çünkü tek geçişte "bu karakter ileride tekrar edecek mi?" sorusunu cevaplayamayız — geleceği bilmiyoruz. Önce tüm bilgiyi topluyoruz, sonra karar veriyoruz. Bu, sık karşılaşacağın bir kalıptır.

Karmaşıklık: **O(n) zaman**, alfabe boyutuyla sınırlı **O(k) bellek**. Bir de incelik: ikinci geçiş `s` üzerinde yapılıyor, `sayac` üzerinde değil — çünkü *ilk* tekrarsızı istiyoruz ve sıra bilgisi dizgide. (Python 3.7+ `dict` sırayı korusa da, bu garantiye yaslanmak yerine niyeti açık yazmak daha sağlamdır.)

**Bunu AI'sız yazabilir misin?** Değiştir: ilk tekrar *eden* karakteri bul. Kaç geçiş yeter, neden?

### Örnek 2 (★★): Kendi hash tablonu yaz

**Problem:** C'de zincirleme kullanan, string anahtarlı, tam sayı değerli bir hash tablosu yaz.

**Adım 1 — Anla.** Üç işlem gerekiyor: `koy` (ekle ya da güncelle), `ara` ve ileride `sil`. Kenar durumlar: aynı anahtar iki kez konursa değer güncellenir (n artmaz); boş tabloda arama "bulunamadı" döner.

**Adım 2 — Örnekle.** `Mert`, `Efe` ve `Ali` anahtarlarını sırayla koyalım. Her biri hangi kovaya düşer? Bunu elle hesaplayacağız (Adım 6'daki tabloda).

**Adım 3 — Kaba çöz.** Tek bir büyük dizi tutup her eklemede tüm anahtarları tarayarak "var mı?" diye bakmak her işlemi O(n) yapar. Bu, sözlüğün vaadi olan O(1)'i vermez.

**Adım 4 — Örüntü.** Bölüm 9.1'deki `indeks = h(anahtar) % M` formülünü al ve çakışmaları her kovada bir liste içinde tut (9.4'teki zincirleme). Düşünce süreci: üç parça gerek — hash fonksiyonu (9.2'deki djb2), kova dizisi ve her kovada bağlı liste. Bölüm 7'nin bağlı listesi ile Bölüm 9'un hash'ini birleştiriyoruz.

**Adım 5 — İyileştir.** Kodu üç parçada veriyoruz: önce kurulum (başlıklar, yapılar, `tablo_olustur`), sonra yeniden hash'leme, en sonda ekleme. Her parçadan sonra kısa bir açıklama var.

```c
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#define BASLANGIC_M 16

typedef struct Dugum {
    char *anahtar;
    int deger;
    struct Dugum *sonraki;
} Dugum;

typedef struct {
    Dugum **kovalar;
    size_t M, n;
} Tablo;

Tablo *tablo_olustur(void) {
    Tablo *t = malloc(sizeof(Tablo));
    if (!t) return NULL;
    t->M = BASLANGIC_M;
    t->n = 0;
    t->kovalar = calloc(t->M, sizeof(Dugum *));  /* hepsi NULL */
    if (!t->kovalar) { free(t); return NULL; }
    return t;
}
```

Yeniden hash'leme, Örnek 2'nin en dikkat isteyen parçası. Tablo büyüdüğünde (M → 2M) her anahtarın kovası değişir (9.6'daki uyarı), bu yüzden her düğümü yeniden hesaplayıp taşımak gerekir. Püf nokta: düğümleri **kopyalamıyoruz**, yalnızca yeniden bağlıyoruz; `strdup` ile ayrılmış anahtar belleği yerinde kalır. Fonksiyon 9.2'deki `djb2`'yi kullanır.

```c
static int rehash(Tablo *t) {
    size_t yeniM = t->M * 2;
    Dugum **yeni = calloc(yeniM, sizeof(Dugum *));
    if (!yeni) return 0;             /* eski tablo hâlâ geçerli */
    for (size_t i = 0; i < t->M; i++) {
        Dugum *p = t->kovalar[i];
        while (p) {
            Dugum *sonraki = p->sonraki;      /* önce sakla */
            size_t j = djb2(p->anahtar) % yeniM;
            p->sonraki = yeni[j];             /* kovanın başına */
            yeni[j] = p;
            p = sonraki;
        }
    }
    free(t->kovalar);                /* yalnız kova dizisi */
    t->kovalar = yeni;
    t->M = yeniM;
    return 1;
}
```

Dikkat: `p->sonraki`'yi yeniden bağlamadan önce saklamazsan zincirin kalanını kaybedersin; bu, Bölüm 7.4'teki bağlı liste hatasının aynısıdır. `free(t->kovalar)` yalnızca kova dizisini serbest bırakır, düğümleri değil.

`tablo_koy` artık her eklemeden sonra yük faktörünü kontrol eder:

```c
int tablo_koy(Tablo *t, const char *anahtar, int deger) {
    size_t i = djb2(anahtar) % t->M;
    for (Dugum *p = t->kovalar[i]; p; p = p->sonraki)
        if (strcmp(p->anahtar, anahtar) == 0) {
            p->deger = deger;                    /* varsa güncelle */
            return 1;
        }
    Dugum *yeni = malloc(sizeof(Dugum));         /* yoksa ekle */
    if (!yeni) return 0;
    yeni->anahtar = strdup(anahtar);             /* KOPYASINI sakla */
    if (!yeni->anahtar) { free(yeni); return 0; }
    yeni->deger = deger;
    yeni->sonraki = t->kovalar[i];               /* başa ekle: O(1) */
    t->kovalar[i] = yeni;
    t->n++;
    if ((double)t->n / t->M > 0.75)  /* yük faktörü aşıldı */
        rehash(t);                   /* hata olursa tablo geçerli */
    return 1;
}
```

**Açıklama — üç kritik karar.** **(1)** `calloc` kullandık: kovaların tamamı `NULL` başlamalı, yoksa çöp işaretçileri izleriz (Bölüm 2'nin başlatılmamış bellek dersi). **(2)** `strdup` ile anahtarın **kopyasını** sakladık. Çağıran taraf kendi tamponunu değiştirirse ya da serbest bırakırsa tablomuz bozulmasın diye — sahiplik (ownership) meselesi, C'nin en sık hata kaynaklarından. **(3)** Yeni düğümü zincirin **başına** ekledik: O(1), sona eklemek O(zincir) olurdu.

Bir not: `strdup` bir **POSIX** fonksiyonudur; C23 ile standarda girdi. Visual Studio (MSVC) gibi derleyicilerde `strdup` yerine `_strdup` yazılır; aksi hâlde C4996 uyarısı alırsın.

Yeniden hash'leme artık tablonun parçası: yük faktörü 0.75'i aştığında `M` ikiye katlanır ve her düğüm yeni kovasına taşınır. Bu örnekte (M = 16) ilk yeniden hash'leme 13. eleman eklendiğinde tetiklenir. Kendin Yap 1'de silme ve tüm belleği serbest bırakan `bitir` fonksiyonlarını tamamlayacaksın; yeniden hash'lemeyi de kendin yazıp buradakiyle karşılaştır.

**Adım 6 — Doğrula.** Üç ekleme, bir güncelleme ve bir arama ile elle izleyelim. Kova numarası `djb2(anahtar) % 16`. Hesabı kolaylaştıran bir gözlem var: 33 ≡ 1 (mod 16) olduğundan djb2 sonucunun mod 16 değeri `(5381 + karakter kodlarının toplamı) mod 16`'ya eşittir. Bu, taşma olsa da geçerlidir, çünkü 2^32 ve 2^64 sayıları 16'ya tam bölünür. Arama satırı için 9.4'teki `tablo_ara` kullanılıyor.

| adım | işlem | karakter toplamı | kova: (5381 + toplam) mod 16 | dolu kovalar | n |
|---|---|---|---|---|---|
| 1 | `koy("Mert", 1)` | 408 | 413 mod 16 = **13** | 13: Mert | 1 |
| 2 | `koy("Efe", 2)` | 272 | 277 mod 16 = **5** | 5: Efe, 13: Mert | 2 |
| 3 | `koy("Ali", 3)` | 278 | 283 mod 16 = **11** | 5: Efe, 11: Ali, 13: Mert | 3 |
| 4 | `koy("Mert", 9)` | 408 | 13 (bulundu, güncellendi) | değişmez; Mert = 9 | 3 |
| 5 | `tablo_ara(t, "Efe", &v)` | 272 | 5 (zincirde bulundu) | değişmez; v = 2 | 3 |

Üç ekleme üç ayrı kovaya düştü (toplamlar farklı, çakışma yok). Güncelleme `n`'i artırmadı; arama doğru değeri buldu. Çakışmayı kendin görmek için `Efe` ile aynı kovaya (5) düşen bir anahtar bul (ipucu: karakter toplamı 16'nın katı olmalı) ve iki anahtarın da bulunabildiğini doğrula.

**Bunu AI'sız yazabilir misin?** `tablo_sil(t, anahtar)` fonksiyonunu yaz. İpucu: zincirden düğüm silmek için *önceki* düğüm gerekir (Bölüm 7.4) — ve `anahtar` için ayırdığın belleği de `free` etmeyi unutma.

### Örnek 3 (★★): Kötü hash'in bedelini ölçmek

**Problem:** İki hash fonksiyonunu (naif toplama vs djb2) aynı veri üzerinde karşılaştır ve farkı sayılarla göster.

**Adım 1 — Anla.** Girdi bir kelime listesi, çıktı iki hash fonksiyonunun kova dağılımına dair iki özet. Bölüm 5'in dersi: "daha iyi" iddiası ölçümle desteklenmeli; önce ölçütü seçmeliyiz.

**Adım 2 — Örnekle.** Dört kelime ve beş kovalı küçük bir tablo: `ab`, `ba`, `ac`, `zz`. Naif toplamanın hangi iki kelimeyi çakıştıracağını tahmin edebilir misin? (Cevap Adım 6'da.)

**Adım 3 — Kaba çöz.** Her kelimeyi her hash ile kovaya koyup kovaları elle saymak en doğrudan yol, ama 10 000 kelimede elle olmaz. Bu yüzden ölçümü koda döküyoruz; ama önce neyi saydığımızı netleştiriyoruz: kovadaki eleman sayısını.

**Adım 4 — Örüntü.** İdeal durumda her kovada yaklaşık α eleman olur. Kötü hash'te birkaç kova şişer, çoğu boş kalır. Dağılımın iki ucunu yakalayan iki sayı yeterli: **boş kova oranı** (kaynak israfı) ve **en uzun zincir** (en kötü arama).

**Adım 5 — İyileştir.** İki hash fonksiyonu ve dağılım ölçen fonksiyon:

```python
def kotu_hash(s):
    return sum(ord(c) for c in s)          # sadece topla

def djb2(s):
    h = 5381
    for c in s:
        h = ((h << 5) + h + ord(c)) & 0xFFFFFFFF
    return h

def dagilim_olc(kelimeler, hash_fn, M=1024):
    kovalar = [0] * M
    for k in kelimeler:
        kovalar[hash_fn(k) % M] += 1
    bos = sum(1 for c in kovalar if c == 0)
    return {
        "bos_kova_orani": bos / M,
        "en_uzun_zincir": max(kovalar),
        "ortalama": len(kelimeler) / M,
    }
```

**Adım 6 — Doğrula.** Önce elle izleyelim: `M = 5` ile dört kelime. İki hash'in değerleri ve mod 5 karşılıkları:

| kelime | naif: toplam | naif mod 5 | djb2: değer | djb2 mod 5 |
|---|---|---|---|---|
| `ab` | 195 | **0** | 5863208 | **3** |
| `ba` | 195 | **0** | 5863240 | **0** |
| `ac` | 196 | **1** | 5863209 | **4** |
| `zz` | 244 | **4** | 5864057 | **2** |

Kova dolulukları: naif hash'te kova 0'da `ab` ve `ba` (anagram, çakıştı), kova 1'de `ac`, kova 4'te `zz`; boş kova 2 tane (oran 0.4), en uzun zincir 2. djb2'de her kelime ayrı kovada, yalnız kova 1 boş (oran 0.2), en uzun zincir 1. Adım 2'deki tahmin doğrulandı: naif toplama anagramları çakıştırır.

Büyük ölçekte ise (10 000 İngilizce kelime, M = 1024, α ≈ 9.8):

```term
$ python3 hash_olc.py
kotu_hash : bos kova %71.4 | en uzun zincir 412 | ortalama 9.8
djb2      : bos kova % 0.1 | en uzun zincir  23 | ortalama 9.8
```

Bu sayılar kullanılan kelime listesine bağlıdır; liste değişirse rakamlar da değişir, bu yüzden bunları ezberleme. Kendi kelime listenle (ör. bir sözlük dosyasından alınmış 10 000 kelime) aynı ölçümü yapıp kendi sayılarını üretmelisin. (Terminal satırları, `dagilim_olc`'u iki hash için çağırıp sonuçları yazdıran küçük bir sürücüden gelir.)

Sonuç çarpıcı: naif hash'te kovaların %71'i boş, en uzun zincir 412 — yani bazı aramalar 412 karşılaştırma yapıyor. djb2'de neredeyse hiç boş kova yok ve en uzun zincir 23. **Aynı veri yapısı, aynı yük faktörü, 18 kat fark.** Sebep: naif hash kelimeleri dar bir sayı aralığına sıkıştırıyor (harf toplamı ~300-1500), dolayısıyla 1024 kovanın büyük kısmı hiç kullanılmıyor.

**Bunu AI'sız yazabilir misin?** Üçüncü bir fonksiyon ekle: yalnız kelimenin *ilk harfini* kullanan hash. Ölçümü tahmin et (kaç kova dolu olur?), sonra çalıştırıp doğrula.

### Örnek 4 (★★★): LRU önbelleği

**Problem:** Sabit kapasiteli bir önbellek tasarla: `al(anahtar)` ve `koy(anahtar, deger)` işlemleri **O(1)** olsun; kapasite dolduğunda **en uzun süredir kullanılmayan** (Least Recently Used) eleman atılsın.

Bu, Bölüm 7'de söz verdiğim örnektir ve gerçek sistemlerin kalbinde çalışır: CPU önbellekleri, veritabanı tampon havuzları, web önbellekleri, `MertOS`'un sayfa değiştirme politikası (Bölüm 25).

**Adım 1-3 (anla, örnekle, kaba çöz).** İki ihtiyaç var: (a) anahtarla O(1) erişim, (b) "en az kullanılan"ı O(1)'de bulup atmak. Kaba çözüm: her elemana bir zaman damgası koy, atarken en eskisini ara — arama O(n). Yetmez.

**Adım 4 (örüntü).** Bölüm 5'in karar ağacı: "anahtarla erişim" → hash tablosu. "En eskisini/en yenisini O(1)'de yönet" → sıralı bir yapı gerek; ve elimizdeki düğümü listeden O(1)'de koparabilmeliyiz → **çift yönlü bağlı liste** (Bölüm 7.6). Karar ağacının altındaki not iş başında: **yapıları birleştir.**

**Adım 5 (iyileştir).** Tasarım şöyle: çift yönlü listede elemanlar *kullanım sırasına* göre durur — baş taraf en yeni, kuyruk taraf en eski. Hash tablosu ise anahtardan **doğrudan liste düğümüne** eşler.

- `al(k)`: sözlükten düğümü bul (O(1)), düğümü listeden kopar ve başa taşı (O(1), çünkü düğüm elimizde ve liste çift yönlü).
- `koy(k, v)`: varsa güncelle ve başa taşı; yoksa başa ekle. Kapasite aşıldıysa kuyruktaki düğümü at ve sözlükten sil (O(1)).

Python'da `OrderedDict` bu yapıyı zaten sağlar (aynı fikirle gerçeklenmiştir):

```python
from collections import OrderedDict

class LRUOnbellek:
    def __init__(self, kapasite):
        self.kap = kapasite
        self.d = OrderedDict()

    def al(self, anahtar):
        if anahtar not in self.d:
            return -1
        self.d.move_to_end(anahtar)       # en yeni konuma taşı
        return self.d[anahtar]

    def koy(self, anahtar, deger):
        if anahtar in self.d:
            self.d.move_to_end(anahtar)
        self.d[anahtar] = deger
        if len(self.d) > self.kap:
            self.d.popitem(last=False)    # en eskiyi at
```

**Adım 6 (doğrula).** Kapasite 2 ile senaryo:

| işlem | önbellek (eskiden yeniye) | sonuç |
|---|---|---|
| `koy(1,'a')` | 1 | — |
| `koy(2,'b')` | 1, 2 | — |
| `al(1)` | 2, 1 | `'a'` (1 en yeni oldu) |
| `koy(3,'c')` | 1, 3 | 2 atıldı (en eskiydi) |
| `al(2)` | 1, 3 | `-1` (yok) |

Doğru: `al(1)` çağrısı 1'i tazelediği için, kapasite dolunca 2 atıldı. Tüm işlemler **O(1)**, bellek **O(kapasite)**.

**Bunu AI'sız yazabilir misin?** Asıl sınav: `OrderedDict` kullanmadan, kendi çift yönlü listenle yaz. Nöbetçi düğümler (Bölüm 7.5) baş ve kuyruk için özel durumları nasıl ortadan kaldırır? Sonra düşün: LRU yerine **LFU** (en az *sıklıkta* kullanılan) isteseydi, hangi ek yapı gerekirdi?

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Hash tablosunu kendi ellerinle yazmadan "anladım" deme — bu yapının inceliği ayrıntılarda (silme, rehashing, sahiplik) saklıdır.
:::

### Proje 1 (★★): Tam hash tablosu ve strateji karşılaştırması

**Amaç:** Örnek 2'yi tamamla, sonra ikinci bir gerçekleme yazıp ikisini ölçerek karşılaştır.

**Yapılacak:**

1. **Zincirleme sürümünü tamamla:** `koy`, `al`, `sil`, `bitir` (tüm belleği serbest bırak) ve **yeniden hash'leme** (α > 0.75 olunca M'yi ikiye katla; tüm düğümleri yeni M'ye göre yeniden yerleştir — 9.6 ve Örnek 2).
2. **Açık adreslemeli sürüm yaz:** doğrusal sondalama + **mezar taşı** ile silme + yeniden hash'leme (α > 0.66 olunca M'yi ikiye katla; tüm gerçek elemanları yeni tabloya yeniden yerleştir, mezar taşlarını taşıma).
3. **Ölç:** 100 000 rastgele string anahtarla her iki tablo için (a) ekleme süresi, (b) arama süresi, (c) bellek kullanımı, (d) en uzun sondalama/zincir. Sonuçları tabloya dök.

**Önerilen yaklaşım:** İki gerçeklemeyi aynı başlık dosyasındaki *aynı arayüzle* yaz (Bölüm 2.11) — böylece test kodun değişmeden ikisini de kullanabilir. Bu, Kısım V'te göreceğin "arayüz/gerçekleme ayrımı"nın erken bir uygulaması.

**Başarı kriterleri:** İkisi de aynı testlerden geçiyor; `valgrind` temiz (sızıntı yok — `strdup` ettiklerini `free` ettin mi?); rehashing sonrası tüm eski anahtarlar hâlâ bulunabiliyor; mezar taşı silme testinde "silinen anahtarın arkasındaki anahtar hâlâ bulunuyor" durumu doğrulanmış; ölçüm tablosunda açık adreslemenin arama hızındaki cache avantajı görünüyor.

### Proje 2 (★★★): Yinelenen dosya bulucu

**Amaç:** Hash'i bir "parmak izi" olarak kullanmayı öğren ve gerçek bir araç yaz: bir dizin ağacındaki birebir aynı dosyaları bul.

**Yapılacak:** `python dedup.py /bir/dizin` komutu, ağaçtaki tüm dosyaları tarayıp içerikçe aynı olanları gruplar hâlinde listelesin ve toplam israf edilen alanı raporlasın.

**Önerilen yaklaşım — üç aşamalı eleme (performansın kalbi burada):**

1. **Boyuta göre grupla.** Farklı boyuttaki dosyalar kesinlikle farklıdır; bu, hiç okuma yapmadan adayların çoğunu eler.
2. **Aynı boyuttakilerin ilk 4 KB'ının hash'ini al.** Hâlâ eşleşenler kalır.
3. **Kalanların tam hash'ini al** (`hashlib.sha256`, parça parça okuyarak — dosyanın tamamını belleğe alma, Bölüm 3'ün generator dersi).

**Kritik tasarım sorusu:** Hash'leri eşit olan iki dosyayı "aynı" ilan etmek doğru mu? SHA-256 için çakışma olasılığı pratikte sıfırdır, ama Bölüm 9.3'ün dersi "çakışma kaçınılmazdır" diyordu. Kararını **gerekçelendirerek** ver ve gerekçeni koda yorum olarak yaz. (İpucu: dosya silecek bir araç yazıyorsan, kanıt standardın ne olmalı?)

**Başarı kriterleri:** 10 000 dosyalık bir ağaçta makul sürede bitiyor; üç aşamalı eleme sayesinde okunan toplam bayt, tüm dosyaları okumaya göre çok daha az (bunu raporla); aynı içerikli ama farklı isimli dosyalar bulunuyor; boş dosyalar ve simgesel bağlar (symlink) düzgün ele alınıyor; program hiçbir dosyayı **silmiyor**, yalnız raporluyor (yıkıcı işlemler ayrı bir onay gerektirmeli — Bölüm 4'ün `rm` uyarısı).

### Ek Alıştırmalar

Aşağıdaki problemler cevapsızdır. Her birini önce kâğıtta çöz, sonra kodla ve zaman ile bellek karmaşıklığını yaz. Hepsi bu bölümdeki hash ve küme kalıplarıyla çözülür.

1. **Two Sum (★).** Tam sayı dizisi ve bir `hedef` verildiğinde toplamı `hedef` olan iki elemanın **dizin**lerini döndür. O(n) zamanda nasıl yaparsın?
2. **Contains Duplicate II (★).** Aynı değer, dizindeki konumları arasındaki fark en fazla `k` olacak şekilde iki kez geçiyor mu? Kayan bir küme ile çöz.
3. **Valid Anagram (★).** İki dizgi anagram mı? Önce sıralayarak, sonra sayaçla çöz; iki yaklaşımın bedelini karşılaştır.
4. **Group Anagrams (★★).** Dizgi listesindeki anagramları aynı grupta topla. Gruplamak için anahtar olarak ne seçersin? (Liste anahtar olamaz; 9.8'i hatırla.)
5. **Isomorphic Strings (★★).** Her `s` karakteri `t`'deki tek bir karaktere birebir eşlenmeli. İki yönlü eşlemeyi nasıl kontrol edersin?
6. **Subarray Sum = k (★★).** Negatif sayılar içerebilen bir dizide toplamı `k` olan bitişik alt dizilerin sayısını bul. İpucu: ön toplam ve bir sayaç. Kaydırmalı pencere burada neden çalışmaz?
7. **Longest Consecutive Sequence (★★).** Sıralamadan kaçınarak en uzun ardışık tam sayı dizisinin uzunluğunu bul. Hangi kümeyi kurarsan bir elemanın dizinin başı olup olmadığını O(1)'de anlarsın?
8. **En sık k kelime (★★).** Bir kelime listesinde en sık geçen `k` kelimeyi döndür. Sayıp sıralamak ile yığın (heap, Bölüm 10) arasındaki bedel farkı nedir?
9. **Ransom Note (★).** `mektup` dizgisindeki harflerden `ransom` kurulabilir mi? Sayaç mı dizi mi kullanırsın, neden?
10. **Happy Number (★★).** Bir sayının rakamlarının kareleri toplamı tekrar tekrar alındığında 1'e ulaşıyorsa sayı "mutlu"dur. Sonsuz döngüyü hangi veri yapısıyla tespit edersin?
11. **Four Sum II (★★★).** Dört dizinin her birinden birer eleman seçip toplamı 0 olan dörtlü sayısını bul. Naif yaklaşım O(n⁴)'tür. İlk iki dizinin tüm toplamlarını bir hash tablosunda say; O(n²)'ye nasıl inersin?
12. **RandomizedSet (★★★).** `ekle(x)`, `sil(x)` ve `rastgele()` işlemleri ortalama O(1) olsun; `rastgele()` her elemanı eşit olasılıkla döndürsün. Hash tablosu tek başına ve dizi tek başına neden yetmez? İkisini nasıl birleştirirsin? (Silmede "son elemanla yer değiştir" fikrini düşün.)

## Kod Okuma Egzersizi

Bugünkü kesit CPython 3.12, `Objects/dictobject.c` dosyasından (sadeleştirilmiş): sık çalışan sondalama döngüsü.

```c
#define PERTURB_SHIFT 5

/* Sondalama döngüsünün çekirdeği (sadeleştirilmiş) */
perturb = hash;
i = (size_t)hash & mask;
for (;;) {
    if (dk_get_index(dk, i) == ix)      /* bulundu mu? */
        break;
    perturb >>= PERTURB_SHIFT;
    i = ((i << 2) + i + perturb + 1) & mask;   /* i*5 + perturb + 1 */
}
```

Kaynaktaki yorumların özeti: sondalama dizisi tablodaki her indeksi ziyaret eder ve yalnızca hash'in alt bitlerine bağlı kalmaz.

**Sorular — cevaplamadan geçme:**

- `& mask` ifadesi ne yapıyor? `mask = M - 1` ve `M` 2'nin kuvveti olduğuna göre, bu işlem hangi aritmetik işleme eşdeğerdir? (Bölüm 1'in bit numaraları.)
- 9.2'de "2'nin kuvveti M kullanırsan yalnız alt bitler işe yarar" demiştik. `perturb` değişkeni bu sorunu nasıl çözüyor? `perturb >>= 5` satırı her adımda hash'in hangi kısmını devreye sokuyor?
- `i*5 + perturb + 1` formülünde `+1` neden var? (İpucu: `perturb` sıfıra düştüğünde ne olur, ve döngü sonsuza girer mi?)
- Bu, saf doğrusal sondalamadan (`i+1`) nasıl farklı? Hangi problemi (9.5'teki hangi kümelenme türünü) çözüyor ve karşılığında hangi avantajdan kısmen feragat ediyor?
- `perturb` sıfırlandıktan sonra dizi `i = i*5 + 1` hâline gelir. Bu formülün, M = 2^k için tablodaki **tüm** indeksleri ziyaret ettiği kanıtlanabilir. Neden bu garanti kritik? Olmasaydı hangi hata oluşurdu?
- Son olarak tasarım sorusu: Python neden zincirleme yerine açık adreslemeyi seçti? 9.4 ve 9.5'teki ödünleşimleri kullanarak gerekçelendir.

## Bölüm Özeti

Bu bölümde "aramak yerine hesaplamak" fikrini kurduk:

- **Hash tablosu**, anahtarı bir indekse çevirir: `indeks = h(anahtar) % M`. Böylece arama O(n)'den ortalama **O(1)**'e iner.
- **İyi hash fonksiyonu** deterministik, hızlı, düzgün dağıtan ve çığ etkili olmalıdır. Karakter toplama gibi naif tasarımlar anagramları çakıştırır ve dağılımı bozar; djb2/FNV gibi çarpımsal karıştırmalar iş görür.
- **Çakışma kaçınılmazdır** (güvercin yuvası) ve sezgiden çok erken gelir (**doğum günü paradoksu**: M kovada ~√M anahtarda beklenir). Çözüm önlemek değil, yönetmektir.
- **Zincirleme:** her kova bir liste. Maliyet O(1 + α), silme kolay, ama `malloc` yükü ve kötü cache davranışı var.
- **Açık adresleme:** tek dizi, dolu kovada başkasını dene (doğrusal / karesel / çift hash). Cache dostu ve bellek verimli; ama silme **mezar taşı** gerektirir ve tablo dolarken performans çöker.
- **Yük faktörü α = n/M** sağlık göstergesidir; α → 1 iken maliyet patlar. Eşik aşılınca **yeniden hash'leme** yapılır: M ikiye katlanır, herkes yeniden yerleşir — Bölüm 7'nin geometrik büyümesi sayesinde **amortize O(1)**.
- **Sınırlar:** sıra yoktur (min/max/aralık için ağaç gerekir — Bölüm 10); en kötü durum O(n)'dir ve bu bir **saldırı yüzeyidir** (hash flooding → rastgele tohum, SipHash); **anahtarlar değişmez olmalıdır**.
- **Küme**, değersiz hash tablosudur. Hash fikri ayrıca parmak izi, dedup, önbellek anahtarı, tutarlı hash'leme ve Bloom filtresi olarak da karşına çıkar.

**Sonraki bölümde:** Hash tablosunun tek büyük eksiği sıraydı. **Bölüm 10 — Tree**'de sırayı koruyan yapılara geçiyoruz: ikili ağaç gezinmeleri, ikili arama ağacı (BST), dengelemenin neden şart olduğu ve AVL rotasyonları, öncelik kuyruğunun motoru olan yığın (heap), ve önek aramanın yapısı trie. Bölüm 5'in karar ağacındaki "sıralı tut + aralık sorgusu" dalını nihayet dolduracağız.

::: mulakat
Klasik sorular — hemen cevaplamaya çalışma, her birini birkaç dakika düşün:

1. Hash tablosunun aramada O(1) olması nasıl mümkün? "Ortalama" kelimesi burada tam olarak neyi saklıyor?
2. İyi bir hash fonksiyonunun özellikleri nelerdir? Karakter toplamı neden kötüdür?
3. Zincirleme ile açık adreslemeyi karşılaştır: hangi durumda hangisini seçersin?
4. Açık adreslemede bir elemanı silip kovayı boşaltmak neden hatalıdır? Doğru çözüm nedir?
5. Yük faktörü nedir, neden bir eşikte tutulur? Eşik aşılınca ne olur ve maliyeti nedir?
6. Neden Python'da `list` sözlük anahtarı olamaz da `tuple` olabilir?
7. Hash flooding saldırısı nasıl çalışır ve diller buna karşı ne yapmıştır?
8. Sıralı gezinme, en küçük eleman ve aralık sorgusu gerekiyorsa neden hash tablosu yanlış seçimdir?
:::
