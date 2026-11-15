%% kisim_no: III
%% kisim_ad: Veri Yapıları
%% bolum_no: 8
%% baslik: Stack & Queue

## Giriş: Kısıtlamanın gücü

Bölüm 7'de iki temel yapıyı kurduk ve ikisi de "her yere erişebilirsin" diyordu. Şimdi tuhaf görünen bir hamle yapacağız: **erişimi kasıtlı olarak kısıtlayacağız.** Yığın ve kuyruk, dizinin ya da bağlı listenin *daha az yetenekli* hâlleridir — sadece bir ya da iki uçtan giriş-çıkış yaparlar. Peki daha az yapabilen bir şey neden daha değerli olsun?

Cevap mühendisliğin derin ilkelerinden birinde: **kısıtlama, garanti üretir.** Bir yapıya "yalnız tepeden ekleyip tepeden çıkarabilirsin" dediğinde üç şey birden kazanırsın. Birincisi *performans*: tek uçta çalışan işlemler her zaman O(1)'dir, kaydırma ya da arama yoktur. İkincisi *doğruluk*: yanlış yerden eleman almak diye bir hata sınıfı ortadan kalkar — Bölüm 7'de nöbetçi düğümle yaptığımız şeyin genel hâli. Üçüncüsü ve en önemlisi *anlam*: kodda `Yigin` gördüğün an, o verinin nasıl kullanılacağını okumadan bilirsin. Yapı, niyeti belgeler.

Bu iki yapı bilgisayar biliminin her katmanında karşına çıkacak. Yığın, fonksiyon çağrılarının nasıl çalıştığının cevabıdır — Bölüm 1'de "stack segmenti" diye geçtiğimiz şeyin gerçek mekaniğini bu bölümde açacağız. Kuyruk, işletim sisteminin süreçleri sıraya dizmesinden ağ paketlerinin tamponlanmasına, BFS'in en kısa yolu bulmasından `MertOS`'un klavye tamponuna kadar her yerdedir. İkisi de "veri yapısı" olmaktan çok, **düşünme kalıbıdır**.

::: not
Bu bölümde bir de "aynı fikrin farklı gerçeklemeleri" temasını işleyeceğiz. Yığın hem diziyle hem bağlı listeyle yapılabilir; ikisi de aynı *sözleşmeyi* sunar ama farklı ödünleşimler taşır. Arayüz (ne yapar) ile gerçekleme (nasıl yapar) arasındaki bu ayrım, Kısım V'te soyutlama ve OOP'nin temeli olacak.
:::

## 8.1 Yığın: son giren ilk çıkar

**Yığın (stack)**, elemanların yalnız *tek bir uçtan* eklenip çıkarıldığı yapıdır. Bu uca **tepe (top)** denir. Kural, İngilizce kısaltmasıyla **LIFO**'dur: *Last In, First Out* — son giren ilk çıkar.

Somut benzetme: bulaşıktaki tabak yığını. Yeni tabağı üste koyarsın, alırken de üstten alırsın. Alttaki tabağı almak için üsttekileri kaldırman gerekir — yapı buna izin vermez zaten.

![Şekil 8.1: Yığının çalışması. Her `push` tepeye ekler, her `pop` tepeden alır. Yapı hiçbir zaman ortadaki bir elemana erişim vermez; bu kısıtlama sayesinde tüm işlemler O(1)'dir.](gorseller/b08_stack.png)

Yığının sözleşmesi (arayüzü) dört işlemden ibarettir:

| İşlem | Anlamı | Maliyet |
|---|---|---|
| `it(x)` / push | tepeye ekle | O(1) |
| `cek()` / pop | tepeden al ve döndür | O(1) |
| `bak()` / peek | tepeye bak, alma | O(1) |
| `bos_mu()` | boş mu? | O(1) |

### Dizi tabanlı gerçekleme

En yaygın gerçekleme, dinamik dizinin sonunu tepe olarak kullanmaktır. Bölüm 7'yi hatırla: dizinin *sonuna* ekleme amortize O(1), sondan silme O(1). Yığının ihtiyacı tam olarak bu:

```c
#include <stddef.h>                  /* size_t */
#include <stdlib.h>                  /* realloc */

typedef struct {
    int *veri;
    size_t boyut, kapasite;
} Yigin;

int yigin_it(Yigin *y, int deger) {
    if (y->boyut == y->kapasite) {            /* Bölüm 7: büyüt */
        size_t yeni_kap = y->kapasite ? y->kapasite * 2 : 8;
        int *yeni = realloc(y->veri, yeni_kap * sizeof(int));
        if (!yeni) return 0;
        y->veri = yeni;
        y->kapasite = yeni_kap;
    }
    y->veri[y->boyut++] = deger;              /* tepeye koy */
    return 1;
}

int yigin_cek(Yigin *y, int *cikan) {
    if (y->boyut == 0) return 0;              /* boş: hata bildir */
    *cikan = y->veri[--y->boyut];             /* tepeden al */
    return 1;
}
```

Dikkat edilecek iki ayrıntı var. **Birincisi:** `boyut` hem eleman sayısı hem de "bir sonraki yazılacak yer" olarak çalışıyor; `veri[boyut-1]` tepedir. Bu ikili kullanım, `pop` ve `push`'u tek satıra indiriyor. **İkincisi:** boş yığından çekmek bir hatadır ve *sessizce* geçiştirilmemelidir. Burada dönüş değeriyle bildirdik; Bölüm 6'nın diliyle bu bir sözleşme ihlalidir, `assert` de makul bir seçimdir.

Dizi tabanlı yığının büyük avantajı Bölüm 7.2'den geliyor: elemanlar bitişik olduğu için **cache dostudur**. Bu yüzden pratikte tercih edilen gerçekleme budur.

### Bağlı liste tabanlı gerçekleme

Alternatif: her `push` yeni bir düğümü listenin *başına* ekler. Bölüm 7'den biliyoruz ki başa ekleme O(1). Tepe işaretçisi `push` ve `cek` ile değiştiği için fonksiyonlar tepenin *adresini* (`Dugum **`) alır. Bellek ayırma başarısız olabilir; bu durumu sessizce yutmak yerine dönüş değeriyle bildiriyoruz. Çağıran taraf bu değeri kontrol etmek zorundadır:

```c
#include <stdlib.h>                  /* malloc, free */

typedef struct Dugum {
    int veri;
    struct Dugum *sonraki;
} Dugum;

/* tepe = listenin başı; 1: başarılı, 0: bellek yok */
int yigin_it_liste(Dugum **tepe, int deger) {
    Dugum *yeni = malloc(sizeof(Dugum));
    if (!yeni) return 0;             /* bildir, sessizce geçme */
    yeni->veri = deger;
    yeni->sonraki = *tepe;           /* eski tepe artık altımda */
    *tepe = yeni;                    /* yeni tepe benim */
    return 1;
}

int yigin_cek_liste(Dugum **tepe, int *cikan) {
    Dugum *eski = *tepe;
    if (!eski) return 0;             /* boş */
    *cikan = eski->veri;
    *tepe = eski->sonraki;
    free(eski);                      /* düğümü bırak */
    return 1;
}
```

Bu sürümün avantajı **kapasite sınırının olmaması** ve büyüme sırasında kopyalama yapılmamasıdır. Dezavantajı, her eleman için ayrı `malloc` (yavaş) ve dağınık bellek (cache düşmanı). Karar tablosu:

| Ölçüt | Dizi tabanlı | Bağlı liste tabanlı |
|---|---|---|
| Tüm işlemler | O(1) amortize | O(1) her zaman |
| Bellek ek yükü | Kapasite fazlası | Düğüm başına işaretçi |
| Cache davranışı | **İyi** | Kötü |
| En kötü durum gecikmesi | Büyümede sıçrar (O(n) kopya) | Öngörülemez (her push bir `malloc`) |
| Tipik tercih | **Genel amaçlı** | Yalnız düğüm havuzuyla |

Son satır önemli: gerçek zamanlı bir sistemde (uçuş kontrol, motor kontrolü) "ortalama hızlı" yetmez, *en kötü durum* öngörülebilir olmalıdır. Dizi büyürken oluşan ani O(n) sıçrama orada kabul edilemez olabilir. Bağlı listede ise her `push` bir `malloc` çağırdığı için, `malloc`'un süresi ve başarısı da öngörülemez. Bu yüzden gerçek zamanlı ve gömülü sistemlerde çalışma sırasında `malloc` çağrılmaz: kapasite önceden bilinir ve sabit dizi ya da dairesel tampon kullanılır.

## 8.2 Çağrı yığını: Bölüm 1'in içini açmak

Şimdi kitabın en önemli bağlantılarından birine geldik. Bölüm 1'de bir programın belleğinde "stack segmenti" olduğunu, Bölüm 2'de fonksiyon çağrılarının orada "çerçeve" açtığını söylemiştim. O çerçeveleri yöneten şey, tam olarak bu bölümün konusu olan yığındır — hem de donanım desteğiyle.

![Şekil 8.2: Çağrı yığını. Her fonksiyon çağrısı bir çerçeve iter: parametreler, yerel değişkenler ve kritik olarak dönüş adresi. `return` çerçeveyi çeker, yığın işaretçisini (SP) geri indirir ve dönüş adresine atlar. LIFO düzeni, iç içe çağrıların doğru sırayla geri dönmesini garanti eder.](gorseller/b08_callstack.png)

Neden yığın? Çünkü fonksiyon çağrıları **doğal olarak LIFO'dur**: `main` `a`'yı çağırır, `a` `b`'yi çağırır; `b` bittiğinde `a`'ya, `a` bittiğinde `main`'e dönülür. En son çağrılan en önce biter — yığının tanımı.

Donanım bu işi iki yazmaçla yapar (Bölüm 1'i hatırla): **SP (stack pointer)** yığının tepesini gösterir, **PC (program counter)** sıradaki komutu. Bir fonksiyon çağrıldığında kabaca şu olur:

1. Argümanlar yazmaçlara ya da yığına konur.
2. Çağrı komutu hedef fonksiyona atlar ve dönüş adresini saklar. **x86'da** `call` dönüş adresini **yığına iter**. **ARM'da** (STM32 dahil) `BL` komutu dönüş adresini **LR (link register)** yazmacına koyar; fonksiyon kendi içinde başka bir çağrı yapacaksa LR'yi yığına kendisi kaydeder (örneğin `push {lr}`).
3. Fonksiyon kendi yerel değişkenleri için SP'yi kaydırarak yer açar.
4. `return` çalışınca yerel alan bırakılır ve dönüş adresi geri yüklenip oraya atlanır: x86'da yığından çekilerek, ARM'da LR'den (ya da yığına kaydedilmiş LR'den) alınarak.

Bu mekanizma üç sonucu doğrudan açıklar:

**Yerel değişkenler neden fonksiyon bitince kaybolur?** Çünkü SP geri indiğinde o bölge "boş" sayılır; bir sonraki çağrı üzerine yazar. Bölüm 2'deki "yerel dizinin adresini döndürme" hatasının gerçek mekaniği budur.

**Özyineleme neden bellek yer?** Her özyineli çağrı yeni bir çerçeve iter. `faktoriyel(10000)` on bin çerçeve demektir. Taban durumu olmayan bir özyineleme yığını sınırına dayar ve program çöker — **stack overflow**. (Programcıların bilinen soru-cevap sitesi Stack Overflow'un adı da buradan gelir.) Özyinelemenin tamamı Bölüm 15'te, ama artık *neden* yığın yediğini biliyorsun.

**Tampon taşması neden bu kadar tehlikeli?** Bölüm 2.6'da yerel bir diziye sınır kontrolsüz yazmanın komşu belleği ezdiğini söylemiştik. Şimdi o komşunun ne olduğunu görüyorsun. Yığın, x86 ve ARM dahil çoğu mimaride **yüksek adresten düşük adrese doğru** büyür. Yerel tampon, dönüş adresinden daha düşük bir adreste durur; yazma yukarı doğru ilerledikçe önce aradaki yerel değişkenlerin, sonra **dönüş adresinin** üzerine gelinir. (x86'da dönüş adresi doğrudan yığındadır; ARM'da LR'de tutulur, ama fonksiyon LR'yi yığına kaydettiyse aynı risk geçerlidir.) Saldırgan dönüş adresini kendi kodunun adresiyle değiştirebilirse, fonksiyon `return` ettiğinde işlemci saldırganın istediği yere atlar. Bu, bilgisayar güvenliği tarihinin en verimli saldırı sınıfıdır ve modern sistemlerdeki karşı önlemleri (stack canary, ASLR, NX bit) Bölüm 32'de göreceğiz.

::: baglanti
Bu bölümde yazdığın `Yigin` yapısı ile işlemcinin çağrı yığını *aynı fikirdir*, farklı katmanlarda. Bu, kitap boyunca göreceğin bir tema: aynı desen donanımda, işletim sisteminde ve uygulama kodunda tekrar tekrar belirir. Bölüm 15'te özyinelemeli bir algoritmayı elle yığına çevirerek bu bağlantıyı bizzat kuracaksın.
:::

## 8.3 Yığının klasik işleri

Yığın, "en son açılanı en önce kapat" yapısındaki her problemin doğal aracıdır. Karşına çıkacak başlıca kullanımlar:

**Eşleşme ve dengeleme.** Parantezler, süslü parantezler, HTML/XML etiketleri, `MertOS`'taki komut ayrıştırıcısı... Açılanı yığına it, kapanan gelince tepeyi kontrol et. Örnek 1'de bunu baştan sona yazacağız.

**İfade değerlendirme.** `3 + 4 * 2` gibi bir ifadeyi hesaplamak için önce **postfix** (Lehçe sonek, RPN) biçimine çevirilir — `3 4 2 * +` — ve bu biçim yığınla tek geçişte hesaplanır: sayı görünce it, operatör görünce iki sayı çek, sonucu it. Hesap makineleri ve derleyicilerin ifade üreteçleri bu deseni kullanır (Bölüm 37'de derleyici bağlamında yeniden göreceğiz). Kendin Yap 1'de bunu yazacaksın.

**Geri alma (undo).** Her işlemi bir yığına it; `Ctrl+Z` tepeden çeker. İleri alma (redo) için ikinci bir yığın tutulur. Bir metin düzenleyicinin, çizim programının ya da IDE'nin geri alma yığını tam olarak budur — ve Bölüm 22'deki Command Pattern'in tipik uygulamasıdır.

**Geri izleme (backtracking) ve DFS.** Bir labirentte yol ararken "buraya kadar geldiğim yol"u yığında tutarsın; çıkmaza girince geri çekip başka yol denersin. Derinlik öncelikli arama (DFS) ya açıkça bir yığın kullanır ya da özyinelemeyle *çağrı yığınını* kullanır — ikisi aynı şeydir. Bölüm 15 ve 17'nin temeli.

**Tarayıcı geçmişi, geri düğmesi, iç içe geçmiş bağlamlar.** Hepsi aynı desen: en son girilenden çıkılır.

## 8.4 Kuyruk: ilk giren ilk çıkar

**Kuyruk (queue)** tam ters kuralı uygular: elemanlar bir uçtan girer (**arka / rear**), diğer uçtan çıkar (**ön / front**). Kural **FIFO**'dur: *First In, First Out*. Benzetmesi adında zaten: markette sıraya girmek.

![Şekil 8.3: Kuyruk ve gerçekleme tuzağı. Naif dizi gerçeklemesinde önden çıkarma tüm elemanları kaydırmayı gerektirir — O(n). Dairesel dizi (Bölüm 7.7) iki indeksi sararak bu maliyeti O(1)'e indirir.](gorseller/b08_queue.png)

Yığında dizi gerçeklemesi kolaydı çünkü hep *sondan* çalışıyorduk. Kuyrukta bir uçtan girip diğerinden çıkıyoruz ve dizinin *başından* silmek O(n) kaydırma demek. Naif çözüm burada tuzağa düşer.

Çözümü Bölüm 7.7'de zaten kurduk: **dairesel tampon**. İki indeks (`bas`, `kuyruk`) diziyi halka gibi gezer; kaydırma yoktur:

```c
#define BOYUT 64

typedef struct {
    int veri[BOYUT];
    unsigned bas, kuyruk, adet;
} Kuyruk;

int kuyruga_ekle(Kuyruk *k, int deger) {
    if (k->adet == BOYUT) return 0;              /* dolu */
    k->veri[k->kuyruk] = deger;
    k->kuyruk = (k->kuyruk + 1) % BOYUT;
    k->adet++;
    return 1;
}

int kuyruktan_al(Kuyruk *k, int *cikan) {
    if (k->adet == 0) return 0;                  /* boş */
    *cikan = k->veri[k->bas];
    k->bas = (k->bas + 1) % BOYUT;
    k->adet--;
    return 1;
}

/* on() ve bos_mu(): boşken on() çağrılmamalı */
int on(const Kuyruk *k) { return k->veri[k->bas]; }
int bos_mu(const Kuyruk *k) { return k->adet == 0; }
```

Kuyruğu sıfır ile başlatmak için `{0}` kullanılır: `bas`, `kuyruk` ve `adet` sıfır olur, `veri` dizisi de sıfırlanır; böylece başlangıçta çöp değer kalmaz:

```c
void ornek(void) {
    Kuyruk k = {0};        /* bas = kuyruk = adet = 0 */
    kuyruga_ekle(&k, 7);
    int ilk = bos_mu(&k) ? -1 : on(&k);   /* ilk = 7 */
    (void)ilk;
}
```

Sabit boyut istemiyorsan bağlı liste gerçeklemesi de doğaldır: **baş** ve **kuyruk** olmak üzere iki işaretçi tutulur; sona ekleme kuyruk işaretçisi sayesinde O(1), baştan çıkarma zaten O(1). Bu sürümde nöbetçi düğüm (Bölüm 7.5) özellikle işe yarar, çünkü "kuyruk boşken ekleme" özel durumunu ortadan kaldırır.

Kuyruğun sözleşmesi de dört işlemdir: `ekle` (enqueue), `al` (dequeue), `on()` (baştakine bak), `bos_mu()` — hepsi O(1).

## 8.5 Kuyruk nerede karşına çıkar

Kuyruk, "adil sıra" gereken her yerde belirir:

**BFS — genişlik öncelikli arama.** Bu, kuyruğun en güzel kullanımıdır ve neden işe yaradığını görmek önemli:

![Şekil 8.4: BFS ve kuyruk. Bir düğümü işlerken komşularını kuyruğa eklersin; kuyruk FIFO olduğu için önce aynı katmandaki tüm düğümler, sonra bir sonraki katman işlenir. Bu katman katman ilerleme, bulunan ilk yolun en kısa yol olmasını garanti eder.](gorseller/b08_bfs.png)

Sezgi şu: kuyruk "sırayla" çalıştığı için, başlangıçtan 1 adım uzaktaki tüm düğümler, 2 adım uzaktakilerden *önce* işlenir. Dolayısıyla hedefe ilk ulaştığın an, en az adımla ulaşmışsındır. Aynı algoritmada kuyruk yerine **yığın** kullanırsan derine dalarsın (DFS) ve bulduğun yol en kısa olmayabilir. Yalnız bir veri yapısını değiştirerek algoritmanın anlamını değiştirmiş olursun — Bölüm 17'de bu ikiliyi tam olarak işleyeceğiz, Kendin Yap 2'de ise bizzat karşılaştıracaksın.

İki uyarı var. **Birincisi:** BFS'in sonsuz döngüye girmemesi için her düğümün ziyaret edilip edilmediğini tutan bir **ziyaret edilmiş (visited) kümesi** şarttır. Grafta döngü varsa, ziyaret kümesi olmadan aynı düğüm kuyruğa defalarca girer ve algoritma bitmez. **İkincisi:** "en kısa yol" garantisi yalnızca **ağırlıksız** grafta geçerlidir: kenarların ağırlığı (mesafe, maliyet) varsa katman sayısı gerçek mesafe değildir. Ağırlıklı graflarda en kısa yol için Dijkstra kullanılır (Bölüm 17).

**Üretici-tüketici.** Bir taraf veri üretir, diğer taraf tüketir; arada kuyruk tampon görevi görür. `MertOS`'ta kesme işleyicisi tuşları kuyruğa yazar, ana döngü okur. Ağ kartı paketleri kuyruğa koyar, çekirdek işler. Bu desenin eşzamanlılık boyutu Bölüm 27'nin konusu.

**İş kuyrukları ve zamanlayıcı.** İşletim sisteminin hazır süreçleri (Bölüm 26), yazıcı kuyruğu, web sunucusundaki istek kuyruğu, mesaj kuyrukları (Bölüm 41'de RabbitMQ/Kafka).

**Akış tamponlama.** Ses/video oynatıcıda gelen veri kuyrukta bekler, oynatıcı sabit hızda tüketir; ağdaki dalgalanma böyle emilir.

## 8.6 Deque: iki uçlu kuyruk

Yığın tek uçtan, kuyruk iki farklı uçtan çalışıyordu. **Deque** (*double-ended queue*, "dek" okunur) ikisini birleştirir: **her iki uçtan da** ekleme ve çıkarma yapabilirsin, hepsi O(1).

![Şekil 8.5: Deque. Dört işlem de O(1): sola ekle, soldan çıkar, sağa ekle, sağdan çıkar. Yığın ve kuyruk, deque'in yeteneklerinin kısıtlanmış hâlleridir.](gorseller/b08_deque.png)

Deque bir genelleme olduğu için hem yığın hem kuyruk yerine kullanılabilir. Ama asıl değeri, *ikisinin birden* gerektiği problemlerdedir:

- **Kayan pencerede maksimum.** Bölüm 5'teki kayan pencere deseniyle birleşince, penceredeki en büyük elemanı O(n) toplam maliyetle takip edebilirsin — monotonik bir deque tutarak. Klasik ve zor bir mülakat sorusudur.
- **Geri/ileri gezinme.** Tarayıcı geçmişi, adım adım geri alma.
- **İş çalma (work stealing).** Paralel programlamada bir iş parçacığı kendi kuyruğundan bir uçtan alır, boşta kalan başka bir iş parçacığı diğer uçtan "çalar" (Bölüm 53).

Python'da `collections.deque` hazır gelir ve `list`'e göre baştan ekleme/çıkarmada dramatik biçimde hızlıdır:

```python
from collections import deque

d = deque([1, 2, 3])
d.append(4)        # sağa ekle
d.appendleft(0)    # sola ekle       -> deque([0,1,2,3,4])
d.pop()            # sağdan çıkar     -> 4
d.popleft()        # soldan çıkar     -> 0
```

Neden `list.insert(0, x)` yerine bunu kullanmalısın? Çünkü Python listesi bir dizidir; başa ekleme tüm elemanları kaydırır — O(n). Milyon elemanlı bir listeye milyon kez başa ekleme yaparsan O(n²) ile karşılaşırsın. `deque` aynı işi O(1)'de yapar. Nasıl becerdiğini Kod Okuma egzersizinde göreceksin — cevap, Bölüm 7'nin iki yapısını *birleştirmesinde*.

## 8.7 Monotonik yığın: sıradışı bir desen

Şimdi mülakatlarda sık çıkan ama okulda nadiren öğretilen güçlü bir desene geleceğiz: **monotonik yığın**.

Problem şu: bir dizideki her eleman için, **kendisinden sonra gelen ilk büyük elemanı** bul. `[2,1,2,4,3]` için cevap `[4,2,4,-1,-1]`. Kaba kuvvet basit: her eleman için sağa doğru tara — O(n²).

Daha iyisi mümkün mü? Anahtar gözlem şu: bir eleman büyük bir sayı görene kadar "cevap bekliyor" durumundadır. Bekleyenleri bir yığında tutalım — ve yığını hep **azalan** sırada koruyalım:

![Şekil 8.6: Monotonik yığın adım adım. Yığında "henüz cevabı bulunmamış" elemanlar bekler. Yeni gelen eleman, yığının tepesindekinden büyükse o elemanın cevabı bulunmuş demektir: çekilir ve cevabı yazılır. Her eleman yığına en fazla bir kez girer ve bir kez çıkar — toplam maliyet O(n).](gorseller/b08_monotonic.png)

```python
def sonraki_buyuk(dizi):
    n = len(dizi)
    cevap = [-1] * n
    yigin = []                       # indeksleri tutar
    for i, v in enumerate(dizi):
        while yigin and dizi[yigin[-1]] < v:
            cevap[yigin.pop()] = v   # bekleyenin cevabı bulundu
        yigin.append(i)
    return cevap
```

Bu kodun karmaşıklığı ilk bakışta O(n²) gibi görünür — döngü içinde `while` var. Ama Bölüm 7'deki amortize akıl yürütmeyi uygula: **her indeks yığına tam bir kez girer ve en fazla bir kez çıkar.** Toplam `while` yinelemesi n'i aşamaz. Dolayısıyla toplam maliyet **O(n)**.

Bu desenin çıktığı problem ailesi geniştir: "sonraki/önceki büyük/küçük eleman", "günlük sıcaklıklar" (kaç gün sonra daha sıcak olacak), "histogramdaki en büyük dikdörtgen", "yağmur suyu biriktirme". Hepsinde ortak sezgi aynıdır: *bir eleman, kendisinden büyük biri gelene kadar bekler; geldiği an işi biter.* Örnek 4'te bunu baştan sona uygulayacağız.

### Kayan pencere maksimumu: monotonik deque

Bölüm 5'teki kayan pencerede, boyutu `k` olan her pencerenin maksimumunu bulmak istediğimizi düşün. Her pencere için baştan taramak O(n·k) eder. Monotonik yığının iki uçlu hâli bunu O(n)'ye indirir: deque'de **değerleri azalan** sırada tutulan *indeksler* durur. Baştaki indeks her zaman pencerenin maksimumunun konumudur.

Yeni bir eleman geldiğinde, arkadaki ondan küçük ya da eşit indeksler artık hiçbir zaman maksimum olamaz (hem daha eski, hem daha küçük); atılırlar. Baştaki indeks pencerenin dışına çıktıysa o da baştan atılır.

```python
from collections import deque

def kayan_maks(dizi, k):
    dq = deque()                    # indeksler; değerler azalan
    sonuc = []
    for i, v in enumerate(dizi):
        while dq and dizi[dq[-1]] <= v:
            dq.pop()                # arkadaki küçükler gereksiz
        dq.append(i)
        if dq[0] <= i - k:          # pencere dışına çıktı
            dq.popleft()
        if i >= k - 1:              # ilk pencere doldu
            sonuc.append(dizi[dq[0]])
    return sonuc
```

**Neden O(n)?** `for` döngüsü n kez döner. Her indeks deque'ye tam bir kez girer (`append`) ve en fazla bir kez çıkar (`pop` ya da `popleft`). İçteki `while` ve `popleft`'in toplam çalışma sayısı bu giriş-çıkışlarla sınırlıdır; toplam işlem sayısı en fazla 2n'dir. Bu, Bölüm 7'deki amortize argümanın aynısıdır. Örneğin `kayan_maks([1,3,-1,-3,5,3,6,7], 3)` çağrısı `[3, 3, 5, 5, 6, 7]` döndürür.

## 8.8 Özet karar tablosu

| İhtiyacın | Yapı | Neden |
|---|---|---|
| En son ekleneni geri al | **Yığın** | LIFO doğal |
| İç içe eşleşme/dengeleme | **Yığın** | Açılan-kapanan sırası |
| Derine dal, çıkmazda geri gel | **Yığın** (ya da özyineleme) | Geri izleme |
| Adil sıra, geliş sırasıyla işle | **Kuyruk** | FIFO doğal |
| En kısa yol / katman katman keşif | **Kuyruk** (BFS) | Katman garantisi |
| Üretici-tüketici tamponu | **Kuyruk** (dairesel) | O(1), sabit bellek |
| İki uçtan da erişim | **Deque** | Genelleme |
| "Sonraki büyük eleman" ailesi | **Monotonik yığın** | Amortize O(n) |

Ve gerçekleme kararı için tek kural: **gerçek zamanlı ya da gömülü bir sistemde çalışma sırasında `malloc` çağrılmaz; kapasite önceden bilinir ve sabit dizi ya da dairesel tampon kullanılır.** Genel amaçlı işte dizi tabanlı (dinamik büyüyen) gerçekleme cache dostudur ve varsayılandır. Bağlı liste ancak düğümler başta ayrılmış bir havuzdan geliyorsa bu kurala uyar.

## Çözümlü Örnekler

### Örnek 1 (★): Parantez dengeleme

**Problem:** Bir metindeki `()`, `[]`, `{}` çiftlerinin doğru şekilde açılıp kapandığını kontrol et. `"{[()]}"` → doğru; `"([)]"` → yanlış (iç içelik bozuk).

**Adım 1 — Anla.** Girdi `str`, çıktı `bool`. Kenar durumlar: boş metin (doğru sayılmalı), yalnız kapanış `")"` (yanlış), fazladan açılış `"(("` (yanlış — sonda yığın boş kalmamalı).

**Adım 2 — Örnekle.** Elle çözerken ne yapıyorum? Açılan her parantezi aklımda tutuyorum; kapanan geldiğinde *en son açılanla* eşleşmesini bekliyorum.

**Adım 3 — Kaba çöz.** Kaba yöntem: her kapanış için sola doğru tarayıp en yakın açılmamış eşi bulmak. Her kapanışta tarama O(n) sürer, toplam O(n²). Doğru ama yavaş; "en yakın açılmamış" bilgisini tutan bir yapı işi hızlandırır.

**Adım 4 — Örüntü.** "En son açılan, ilk kapanır" — LIFO. Yığın.

**Adım 5 — İyileştir.** Açılışları it; kapanış gelince tepeyi çek ve eşleşiyor mu bak:

```python
def dengeli_mi(metin):
    eslesme = {")": "(", "]": "[", "}": "{"}
    yigin = []
    for ch in metin:
        if ch in "([{":
            yigin.append(ch)
        elif ch in eslesme:
            if not yigin or yigin.pop() != eslesme[ch]:
                return False        # boş ya da yanlış eşleşme
    return not yigin                # sonda boş kalmalı
```

**Adım 6 — Doğrula.** `"([)]"` üzerinde iz sürelim:

| ch | işlem | yığın | sonuç |
|---|---|---|---|
| `(` | it | `[ ( ]` | — |
| `[` | it | `[ (, [ ]` | — |
| `)` | çek → `[` , beklenen `(` | — | **False** |

Doğru şekilde reddetti. `"{[()]}"` ise sırayla iter, sırayla eşleşir, sonda yığın boş → `True`. Boş metin: döngüye girmez, `not []` → `True`. Sadece `")"`: yığın boş, ilk koşul yakalar → `False`. Karmaşıklık: **O(n) zaman, O(n) bellek** (en kötü durumda hepsi açılış).

**Bunu AI'sız yazabilir misin?** Son satırdaki `return not yigin` neden gerekli? Onu `return True` yapsan hangi girdi yanlış cevap verir?

### Örnek 2 (★★): O(1) minimumlu yığın

**Problem:** Normal yığın işlemlerine ek olarak, yığındaki **en küçük elemanı O(1)'de** döndüren `min()` işlemini destekleyen bir yığın tasarla.

**Adım 1 — Anla.** Normal yığın işlemlerine (`it`, `cek`) ek olarak `min()` var; üçü de O(1) olmalı.

**Adım 2 — Örnekle.** `5, 3, 7, 2` itip bir `cek` yaptığımızda minimum ne olmalı? Önce 2, çekilince 3: minimum *geri gelmek* zorunda.

**Adım 3 — Kaba çöz.** Kaba kuvvet: `min()` çağrıldığında tüm yığını tara — O(n). Kabul edilemez. Peki minimumu bir değişkende tutsak? Sorun: minimum eleman `pop` ile çıkarsa, **bir önceki minimumu** bilmemiz gerekir — ve o bilgi kayboldu.

**Adım 4 — Örüntü.** İşte anahtar: "geçmişteki durumları geri alabilme" ihtiyacı da LIFO'dur. Yani minimum bilgisini de bir **yığında** tutmalıyız. Bölüm 5'in "yapıları birleştir" ilkesi: iki yığın.

**Adım 5 — İyileştir.** Ana yığının yanında bir **yardımcı minimum yığını** tutarız. Ana yığına her ekleme yapıldığında, o ana kadarki minimum da min-yığınına itilir:

```python
class MinYigin:
    def __init__(self):
        self.ana = []
        self.minler = []              # paralel: o andaki min

    def it(self, x):
        self.ana.append(x)
        yeni_min = x if not self.minler else min(x, self.minler[-1])
        self.minler.append(yeni_min)

    def cek(self):
        self.minler.pop()             # ikisi hep aynı boyda
        return self.ana.pop()

    def min(self):
        return self.minler[-1]        # O(1)
```

**Adım 6 — Doğrula.** `it(5), it(3), it(7), it(2)` sonrası:

| ana | 5 | 3 | 7 | 2 |
|---|---|---|---|---|
| minler | 5 | 3 | 3 | 2 |

`min()` → 2. `cek()` → 2 çıkar; minler'in tepesi 3 olur, `min()` → 3. Doğru: 2 gittiğine göre minimum yeniden 3. Karmaşıklık: tüm işlemler **O(1)**, bellek **O(n)** (iki kat).

Bir iyileştirme de mümkün: min-yığınına *yalnız* yeni minimum geldiğinde itmek (eşitlik durumuna dikkat ederek). Bellek kazanırsın, kod biraz karmaşıklaşır — klasik bir ödünleşim.

**Bunu AI'sız yazabilir misin?** Aynı fikri "O(1) maksimum" için uyarla. Sonra düşün: hem min hem max isteniyorsa kaç yardımcı yapı gerekir, ve `cek` sırasında tutarlılığı nasıl korursun?

### Örnek 3 (★★): İki yığınla kuyruk

**Problem:** Elinde yalnız yığın var (yalnız `it`/`cek`/`bak`). Bunlarla bir kuyruk (FIFO) gerçekle.

Bu, hem klasik bir mülakat sorusu hem de amortize analizin güzel bir örneğidir.

**Adım 1 — Anla.** Yalnız yığın işlemleriyle (`it`, `cek`) bir kuyruk (`ekle`, `al`) gerçekleyeceğiz. `al`, sıraya en eski giren elemanı döndürmeli.

**Adım 2 — Örnekle.** Bir yığına `1,2,3` itersem çekerken `3,2,1` alırım — ters sıra. Ama *ters sıranın tersi* doğru sıradır! Bir yığından çekip başka bir yığına itersem sıra düzelir.

**Adım 3 — Kaba çöz.** Her `al`'de girişteki bütün elemanları ikinci bir yığına aktarıp en alttakini almak, sonra geri kalanı geri itmek. Doğru çalışır, ama her `al` O(n). Bu kaba çözümün yavaşlığı, iyileştirmeyi tetikler.

**Adım 4 — Örüntü.** Aktarım pahalı; ama bir kez yapılan aktarım sırayı kalıcı olarak düzeltir. Aktarımı yalnızca çıkış yığını boşken yaparsak aynı iş tekrar tekrar yapılmaz.

**Adım 5 — İyileştir.** İki yığın: **giriş** (yeni gelenler) ve **çıkış** (sıraya girmiş olanlar). Çıkış boşaldığında girişteki her şeyi ona aktarırız:

```python
class YiginKuyruk:
    def __init__(self):
        self.giris = []
        self.cikis = []

    def ekle(self, x):
        self.giris.append(x)          # her zaman O(1)

    def al(self):
        if not self.cikis:            # çıkış boşsa aktar
            while self.giris:
                self.cikis.append(self.giris.pop())
        return self.cikis.pop()       # doğru sırada
```

**Adım 6 — Doğrula.** Senaryoyu izleyelim: `ekle(1), ekle(2), al(), ekle(3), al(), al()`.

| işlem | giriş | çıkış (sonra) | döndürülen |
|---|---|---|---|
| `ekle(1)` | `[1]` | `[]` | — |
| `ekle(2)` | `[1, 2]` | `[]` | — |
| `al()` | `[]` | `[2]` | **1** |
| `ekle(3)` | `[3]` | `[2]` | — |
| `al()` | `[3]` | `[]` | **2** |
| `al()` | `[]` | `[]` | **3** |

İlk `al()`'de çıkış boştu; giriş `[1, 2]` çıkışa `[2, 1]` olarak aktarıldı ve `pop()` ile **1** çekildi. Sıra 1, 2, 3: FIFO çalışıyor. Sonra `ekle(3)` girişe gitti; `al()` çıkıştaki **2**'yi verdi. Çıkış boşalınca son `al()` girişteki **3**'ü aktarıp verdi.

Karmaşıklık burada ilginçleşiyor. Tek bir `al()` çağrısı O(n) sürebilir (aktarım). Ama Bölüm 7'nin amortize mantığını uygula: **her eleman hayatı boyunca en fazla dört işlem görür** — girişe it, girişten çek, çıkışa it, çıkıştan çek. n eleman için toplam iş 4n, yani işlem başına sabit: **amortize O(1)**.

Bu, "en kötü durum O(n) ama amortize O(1)" ayrımının en temiz örneklerinden biridir. Mülakatta bu analizi yapabilmek, kodu yazabilmekten daha değerlidir.

**Bunu AI'sız yazabilir misin?** Tersini dene: iki *kuyrukla* bir yığın gerçekle. Bu yönde amortize O(1) elde edilebiliyor mu, yoksa bir işlem kaçınılmaz olarak O(n) mi kalıyor?

### Örnek 4 (★★★): Günlük sıcaklıklar — monotonik yığın

**Problem:** Günlük sıcaklık dizisi verildiğinde, her gün için "kaç gün sonra daha sıcak bir gün gelecek?" sorusunu cevapla. Böyle bir gün yoksa 0. `[73,74,75,71,69,72,76,73]` → `[1,1,4,2,1,1,0,0]`.

**Adım 1 — Anla.** Girdi `list[int]`, çıktı aynı uzunlukta `list[int]`. n = 10⁵ olabilir → Bölüm 5'in kısıt haritası O(n²)'yi eler; O(n) ya da O(n log n) gerek.

**Adım 2 — Örnekle.** Elle bakalım: 3. gün (75 derece) için sonraki daha sıcak gün 7. gün (76) — fark 4. Dikkat: 75'ten sonra gelen 71, 69, 72 hep daha soğuk; 75 "bekliyor". Bu bekleme fikri kritik.

**Adım 3 — Kaba çöz.** Her gün için ileriye tara: O(n²). n=10⁵'te 10¹⁰ işlem — elenmiş, ama referansımız olarak duruyor.

**Adım 4 — Örüntü.** "Bir eleman, kendisinden büyüğü gelene kadar bekler" → **monotonik yığın** (8.7). Yığında *indeksleri* tutacağız, çünkü cevap gün *farkı*.

**Adım 5 — İyileştir.** Bekleyen indeksleri yığında tutan çözüm:

```python
def gunluk_sicakliklar(sicakliklar):
    n = len(sicakliklar)
    cevap = [0] * n
    yigin = []                            # bekleyen İNDEKSLER
    for i, s in enumerate(sicakliklar):
        while yigin and sicakliklar[yigin[-1]] < s:
            j = yigin.pop()               # j'nin beklediği gün geldi
            cevap[j] = i - j              # kaç gün sonra
        yigin.append(i)
    return cevap                          # kalanlar 0 kalır
```

**Adım 6 — Doğrula.** `[73,74,75,71,69,72,76,73]` üzerinde kritik anları izleyelim:

| i | sıcaklık | yığından çıkanlar | cevap güncellemesi | yığın (sonrası) |
|---|---|---|---|---|
| 0 | 73 | — | — | [0] |
| 1 | 74 | 0 (73<74) | cevap[0]=1 | [1] |
| 2 | 75 | 1 (74<75) | cevap[1]=1 | [2] |
| 3 | 71 | — | — | [2,3] |
| 4 | 69 | — | — | [2,3,4] |
| 5 | 72 | 4, 3 | cevap[4]=1, cevap[3]=2 | [2,5] |
| 6 | 76 | 5, 2 | cevap[5]=1, cevap[2]=4 | [6] |
| 7 | 73 | — | — | [6,7] |

Sonuç `[1,1,4,2,1,1,0,0]` — beklenen çıktı. Yığında kalan 6 ve 7 için cevap 0 kalıyor, doğru (onlardan sıcak gün gelmedi).

**Neden yığın hep azalan?** Çünkü bir elemanı ancak kendisinden *büyük* biri gelince çıkarıyoruz; yani yığında kalanlar hep azalan sıradadır. Bu değişmez (invariant), algoritmanın doğruluğunun kalbidir — Bölüm 6'da öğrendiğin gibi, değişmezi ifade edebilmek kodu anlamaktır.

Karmaşıklık: her indeks bir kez girer, en fazla bir kez çıkar → **O(n) zaman**, yığın için **O(n) bellek**.

**Bunu AI'sız yazabilir misin?** Aynı deseni "önceki daha küçük eleman" için yaz. Hangi iki şey değişir? Sonra zorlu olanı dene: "histogramdaki en büyük dikdörtgen" — aynı desenin en ünlü uygulaması.

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. İkisi de bu bölümün yapılarını gerçek bir işte kullanmanı gerektiriyor — ezber değil, tasarım kararı isteyen projeler.
:::

### Proje 1 (★★): İfade değerlendirici

**Amaç:** `3 + 4 * (2 - 1)` gibi bir matematik ifadesini okuyup hesaplayan bir program yaz. Bu, yığının en klasik ve en öğretici uygulamasıdır; Bölüm 37'de derleyici yazarken aynı fikri yeniden kullanacaksın.

**Yapılacak — iki aşama:**

1. **Ayrıştırma (shunting-yard).** İnfix ifadeyi (`3 + 4 * 2`) postfix'e (`3 4 2 * +`) çevir. İki yapı kullanılır: çıktı için bir liste, operatörler için bir **yığın**. Kural: sayı gelirse doğrudan çıktıya; operatör gelirse, yığının tepesindeki operatörün önceliği daha yüksek ya da eşitse onu çıktıya al, sonra kendini it; `(` doğrudan itilir, `)` gelince `(` görene kadar boşalt.

2. **Değerlendirme.** Postfix ifadeyi bir **yığınla** hesapla: sayı görünce it, operatör görünce iki sayı çek, işlemi yap, sonucu it. Sonda yığında tek eleman kalır — sonuç.

**Önerilen yaklaşım:** Önce postfix değerlendiriciyi yaz ve elle yazdığın postfix ifadelerle test et (daha kolay olan bu). Sonra shunting-yard'ı ekle. Operatör önceliklerini bir sözlükte tut: `{"+": 1, "-": 1, "*": 2, "/": 2}`.

**Başarı kriterleri:** `3+4*2` → 11 (öncelik doğru); `(3+4)*2` → 14 (parantez doğru); `10/(5-5)` → sıfıra bölme hatası düzgün raporlanıyor (çökme yok); dengesiz parantez yakalanıyor; en az bir birim testi dosyası var. Bonus: tek terimli eksi (`-5 + 3`) desteği ekle — bu, gerçek ayrıştırıcıların klasik zorluğudur.

### Proje 2 (★★★): Labirent çözücü — BFS ve DFS yan yana

**Amaç:** Aynı problemi bir kez kuyrukla, bir kez yığınla çözüp farkı *gözünle görmek*. Bölüm 17'ye en iyi hazırlık budur.

**Yapılacak:** Bir metin dosyasından labirent oku (`#` duvar, `.` boş, `S` başlangıç, `E` çıkış). İki çözücü yaz:

- **BFS (kuyruk):** Katman katman ilerler, bulduğu yol **en kısadır**.
- **DFS (yığın):** Derine dalar, bulduğu yol geçerlidir ama en kısa olmayabilir.

İkisi de bulunan yolu labirent üzerinde işaretleyerek yazdırsın; ayrıca ziyaret edilen hücre sayısını ve yol uzunluğunu raporlasın.

**Önerilen yaklaşım:** Ortak iskeleti tek bir fonksiyonda topla; tek fark, bekleyen hücreleri tuttuğun yapının kuyruk mu yığın mı olduğu olsun (`collections.deque` ikisini de yapabilir: `popleft` → BFS, `pop` → DFS). Bu tasarım, "veri yapısını değiştirince algoritma değişir" dersini kodun kendisinde görünür kılar. Yolu geri kurmak için her hücrenin "nereden gelindiği" bilgisini bir sözlükte tut.

**Başarı kriterleri:** BFS her zaman en kısa yolu buluyor (birkaç labirentte elle doğrula); DFS'in bulduğu yol bazı labirentlerde daha uzun; ziyaret sayıları raporlanıyor ve ikisi karşılaştırılıyor; çıkışı olmayan labirentte ikisi de düzgün "yol yok" diyor; 100×100 labirentte ikisi de saniyeler içinde bitiyor. Bonus: `MertOS`'un dairesel tamponunu C'de bir BFS kuyruğu olarak kullan ve sabit bellekle çalıştır.

### Ek Alıştırmalar

Aşağıdaki problemlerin cevabı verilmiyor. Her birinde önce kaba çözümü kâğıda yaz, sonra bu bölümdeki yapılarla iyileştir.

1. **★★ Histogramdaki en büyük dikdörtgen.** Yan yana çubukların yükseklikleri bir dizide verilsin; bu çubuklarla çizilebilecek en büyük alanlı dikdörtgeni bul. Monotonik yığınla O(n) mümkün.
2. **★★★ Yağmur suyu.** Yükseklik dizisi çukurlara yağmur bıraktığında toplam kaç birim su birikir? İki taraftaki sınırları birlikte düşün; yığın ya da iki işaretçiyle çöz.
3. **★ Dosya yolu sadeleştirme.** `/a/./b/../../c/` gibi bir Unix yolunu kanonik biçime (`/c`) çevir. `.` ve `..` parçalarını yığın mantığıyla işle.
4. **★★ Postfix doğrulama.** `3 4 + *` gibi bir postfix ifadede operand eksikse ya da sonda birden fazla değer kalıyorsa hata ver. Proje 1'deki değerlendiriciyi bu kontrollerle güçlendir.
5. **★★ İki kuyrukla yığın.** Örnek 3'ün tersi: yalnız kuyruk işlemleriyle (`ekle`, `al`) LIFO bir yığın gerçekle. Hangi işlem O(n) olur, neden?
6. **★★★ Sabit boyutlu kuyruk, dolu-boş ayrımı.** Dairesel kuyrukta `bas == kuyruk` hem boş hem dolu anlamına gelebilir. Bunu adet sayacı, bir slot boş bırakma ve bayrak ile üç farklı çöz; her birinin bedelini yaz.
7. **★★ Asteroid çarpışması.** Bir dizide her eleman bir asteroidin büyüklüğü ve yönüdür (işaret). Yan yana ters yönlü asteroidler çarpışır; büyük olan kalır. Yığınla simüle et, kalanları döndür.
8. **★★ Önceki daha küçük eleman.** Her eleman için solundaki ilk daha küçük elemanı bul (yoksa -1). Örnek 4'ün aynasıdır; hangi iki şey değişir?
9. **★★ En kısa yol sayısı.** Ağırlıksız bir grafta başlangıçtan her düğüme giden en kısa yolların kaç tane olduğunu BFS ile say. Mesafe dizisi ve ziyaret kümesiyle çalış.
10. **★★★ Min-max kuyruk.** Kuyruğa `ekle`, `al`, `min()` ve `max()` işlemlerini ekle; dördü de amortize O(1) olsun. İki monotonik deque tutabilirsin.
11. **★★★ Yalnız iki yığınla sıralama.** Bir dizi yalnızca iki yığın ve sabit sayıda değişken kullanılarak artan sıraya dizilebilir mi? Mümkünse yaz, değilse neden olmadığını açıkla.
12. **★★ Hatalı ayraç konumu.** `(a + [b * {c])` gibi bir ifadede ilk hatalı kapanış karakterinin indeksini bul. Örnek 1'in küçük bir genişletmesi.

## Kod Okuma Egzersizi

Bugünkü kesit CPython 3.12, `Modules/_collectionsmodule.c` dosyasındaki `collections.deque` gerçeklemesinden alındı (sadeleştirilmiş; gerçek yapıda `PyObject_VAR_HEAD`, `maxlen` ve durum alanları da vardır). Deque'in O(1) baş-son işlemlerini *nasıl* başardığı, Bölüm 7'nin ödünleşimine verilmiş çok zarif bir cevaptır:

```c
#define BLOCKLEN 64

typedef struct BLOCK {
    struct BLOCK *leftlink;
    PyObject *data[BLOCKLEN];
    struct BLOCK *rightlink;
} block;

typedef struct {
    block *leftblock;
    block *rightblock;
    Py_ssize_t leftindex;    /* 0 <= leftindex < BLOCKLEN */
    Py_ssize_t rightindex;   /* 0 <= rightindex < BLOCKLEN */
    Py_ssize_t len;
    ...
} dequeobject;
```

Kaynaktaki yorumların özetine göre tasarım, sabit uzunlukta blokların çift yönlü bağlı listesidir.

**Sorular — cevaplamadan geçme:**

- Bu yapı, Bölüm 7'nin iki yapısını nasıl **birleştiriyor**? Dizinin hangi avantajını, bağlı listenin hangi avantajını alıyor?
- `BLOCKLEN = 64` neden seçilmiş olabilir? (İpucu: Bölüm 7.2'deki cache satırı ve bir `PyObject*`'in boyutu — 64 işaretçi kaç bayt eder, bu neden makul bir blok boyutu?)
- Saf çift yönlü listeye (her eleman ayrı düğüm) göre bu tasarımın bellek ve cache avantajı ne? 1000 elemanlı bir deque'te kaç düğüm ayrılır?
- `leftindex` ve `rightindex` ne işe yarar? Sol uca ekleme yapılırken `leftindex` sıfıra ulaşırsa ne olması gerekir?
- Bu yapıda `d[500]` gibi ortadaki bir elemana erişim kaç adımda olur — O(1) mi, O(n) mi? Neden `deque` belgelerinde "ortadan erişim yavaştır" uyarısı var?
- Tasarım sorusu: Python `list` neden bu yapıyı kullanmıyor? `list`'in vazgeçemeyeceği hangi özellik bunu engelliyor? (İpucu: `lst[i]` sözleşmesi.)

## Bölüm Özeti

Bu bölümde erişimi kısıtlayarak güç kazanmayı öğrendik:

- **Kısıtlama garanti üretir:** tek/iki uçla sınırlı erişim, O(1) işlemler + bir sınıf hatanın imkânsızlığı + kodda okunabilir niyet demektir.
- **Yığın LIFO'dur** (`it`/`çek`/`bak`). Dizi tabanlı gerçekleme cache dostudur ve genel amaçlı varsayılandır; gerçek zamanlı sistemde ise sabit kapasiteli dizi ya da dairesel tampon kullanılır, çünkü bağlı liste her push'ta `malloc` çağırır ve gecikmesi öngörülemez.
- **Çağrı yığını**, Bölüm 1'in stack segmentinin gerçek mekaniğidir: her çağrı parametreleri, yerelleri ve **dönüş adresini** iter. Yerel değişkenlerin ölümü, özyinelemenin bellek tüketimi, stack overflow ve tampon taşması saldırılarının tamamı bu resimle açıklanır.
- **Yığının klasik işleri:** eşleşme/dengeleme, ifade değerlendirme (postfix), geri alma, geri izleme ve DFS.
- **Kuyruk FIFO'dur.** Naif dizi gerçeklemesi O(n) kaydırma yüzünden yanlıştır; doğrusu **dairesel tampon** (Bölüm 7.7) ya da baş+kuyruk işaretçili bağlı listedir.
- **BFS kuyruk kullanır** ve bu yüzden katman katman ilerler; bulduğu ilk yol en kısadır. Aynı algoritmada kuyruk yerine yığın koymak onu DFS'e çevirir.
- **Deque** iki uçtan da O(1)'dir; yığın ve kuyruk onun kısıtlanmış hâlleridir. Kayan pencere maksimumu, iş çalma ve geri/ileri gezinmenin aracıdır.
- **Monotonik yığın**, "sonraki büyük eleman" ailesini O(n)'de çözer: her eleman yığına bir kez girer, bir kez çıkar — amortize akıl yürütmenin bir başka zaferi.

**Sonraki bölümde:** Şimdiye kadar bir elemanı bulmak için ya sırayla taradık (O(n)) ya da sıralılıktan yararlandık. **Bölüm 9 — Hash Table**'da bambaşka bir fikir geliyor: elemanın *nerede olduğunu hesaplamak*. Hash fonksiyonu tasarımı, çakışma stratejileri (zincirleme, açık adresleme), yük faktörü ve yeniden hash'leme ile Python `dict`'inin ve Bölüm 5'te sürekli kullandığımız "gördüm mü?" desenin altındaki makineyi kuracağız.

::: mulakat
Klasik sorular — hemen cevaplamaya çalışma, her birini birkaç dakika düşün:

1. Yığın ve kuyruğu tek cümleyle ayır. Hangi gerçek hayat örneği hangisine karşılık gelir?
2. Çağrı yığınında dönüş adresi neden saklanır? Saklanmasaydı ne olurdu?
3. `StackOverflowError` / stack overflow tam olarak ne zaman oluşur ve nasıl önlenir?
4. Kuyruğu dizi ile gerçeklerken neden dairesel yapmak zorundasın?
5. BFS neden en kısa yolu bulur, DFS neden bulmayabilir? Farkı yaratan tek şey nedir?
6. Monotonik yığın çözümünde iç içe döngü var ama karmaşıklık O(n). Bunu nasıl kanıtlarsın?
7. İki yığınla yapılan kuyrukta `al()` işleminin en kötü durumu O(n)'dir. Buna rağmen neden "amortize O(1)" diyoruz?
:::
