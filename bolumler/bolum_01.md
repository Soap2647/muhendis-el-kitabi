%% kisim_no: I
%% kisim_ad: Programlama Temelleri
%% kisim_ayrac: evet
%% bolum_no: 1
%% baslik: Bilgisayar Nasıl Düşünür

## Giriş: Sihir değil, anahtarlar

Bir bilgisayarın içinde ne olduğunu düşün. Kod yazıyorsun, `Enter`'a basıyorsun, ekranda bir şeyler oluyor. Arada kalan kısım çoğu insan için bir kara kutu — "işte bir şekilde çalışıyor". Bu bölümün amacı o kara kutuyu açmak. Sonunda, en soyut gördüğün kavramların bile aslında **açılıp kapanan minik anahtarlardan** ibaret olduğunu göreceksin.

Peki bu neden senin derdin olsun? Çünkü temeli bilmeyen bir mühendis, hata mesajlarını *tanır* ama *anlamaz*. `segmentation fault` gördüğünde ne olduğunu bilmezsen, çözümü internetten kopyalarsın; işe yararsa şanslısın, yaramazsa tıkanırsın. Ama belleğin nasıl bölümlendiğini bilirsen, o hatayı gördüğün an kafanda bir resim belirir: "demek ki erişmemem gereken bir adrese dokundum." İşte bu kitabın hedefi tam olarak bu: araçlar elinden alınsa bile ayakta kalabilmen.

Bu bölümde dört şeyi baştan kuracağız. Önce **ikilik sistemi** — bilgisayarın tek alfabesi. Sonra bu alfabeyle **sayıların ve karakterlerin nasıl temsil edildiğini**. Ardından bir program çalışırken **belleğin haritasını**. Ve en sonunda, işlemcinin bu bellekten komutları alıp **nasıl tek tek işlediğini**. Bunlar senin `MertOS` işletim sistemini yazarken her gün uğraştığın kavramların ta kendisi; burada onları sıfırdan, sağlam bir zemine oturtacağız.

::: not
Bu bölümde bolca "elle hesap" yapacağız. Hesap makinesi ya da çevrimiçi çevirici kullanma dürtüne diren. Amacımız cevabı bulmak değil; cevabın *nereden geldiğini* parmaklarına kadar hissetmen. Bir kez elle yaptığında, bir daha asla unutmazsın.
:::

## 1.1 Her şey iki durumdan ibaret: İkilik sistem

### Neden ikilik? Çünkü elektrik iki şeyi iyi biliyor

Bir bilgisayarın en küçük yapı taşı **transistör**dür. Transistörü şimdilik minik bir elektronik anahtar gibi düşün: ya akımı geçirir ya geçirmez. Ya açık ya kapalı. Üçüncü bir hâli yok — daha doğrusu, güvenilir bir üçüncü hâli yok.

İşte bilgisayarların neden **ikilik (binary)** çalıştığının bütün sırrı bu. Bir mühendis, "yüksek voltaj = 1, düşük voltaj = 0" diye anlaşırsa, iki durumu ayırt etmek çok kolay ve gürültüye dayanıklı olur. Onluk sistem gibi on ayrı voltaj seviyesini birbirinden ayırmaya çalışsaydık, en ufak parazit her şeyi bozardı. İki seviyeyi ayırmak ise dünyanın en sağlam işi.

Bu tek bir anahtarın tuttuğu bilgiye **bit** denir (İngilizce *binary digit*, ikilik basamak). Bir bit ya `0`'dır ya `1`. Tek başına pek bir şey söylemez — sadece bir "evet/hayır". Ama yan yana dizince güç kazanır.

### Taban kavramı: onluk sistemi yeniden tanımak

İkiliği anlamanın en kolay yolu, hep kullandığın **onluk (decimal)** sistemi bir yabancı gözüyle yeniden görmek. `375` sayısını yazdığında aslında şunu söylüyorsun:

`375 = 3×100 + 7×10 + 5×1 = 3×10² + 7×10¹ + 5×10⁰`

Her basamağın bir **ağırlığı** var ve bu ağırlıklar 10'un kuvvetleri. Sağdan sola: birler, onlar, yüzler... "10" olmasının özel bir sebebi yok; sadece on parmağımız olduğu için bu tabana alıştık. Bilgisayarın parmağı iki tane, o yüzden onun tabanı 2.

İkilik sistemde tam olarak aynı mantık geçerli, sadece ağırlıklar 2'nin kuvvetleri: birler, ikiler, dörtler, sekizler, on altılar... Bir baytın (8 bit) her bitinin ağırlığını görelim:

![Şekil 1.1: Bir baytın basamak değerleri. `0100 0101` ikilik sayısında değeri 1 olan bitlerin ağırlıkları toplanır: 64 + 4 + 1 = 69. Bu değer aynı zamanda 'E' harfinin ASCII kodudur.](gorseller/b01_bit_places.png)

Bu şekil, ikilikten onluğa çevirmenin tüm hikâyesini anlatıyor: **değeri 1 olan bitlerin ağırlıklarını topla, bitti.** `0100 0101` sayısında 1 olan bitler 64, 4 ve 1 ağırlıklarında; toplamı 69.

### Onluktan ikiliğe: kalanlı bölme yöntemi

Ters yöne, onluktan ikiliğe geçmek için pratik bir yol var: sayıyı sürekli 2'ye böl, **kalanları** kaydet, sonra kalanları tersten oku. `69` sayısını çevirelim:

```term
69 ÷ 2 = 34,  kalan 1   (en sağdaki bit)
34 ÷ 2 = 17,  kalan 0
17 ÷ 2 =  8,  kalan 1
 8 ÷ 2 =  4,  kalan 0
 4 ÷ 2 =  2,  kalan 0
 2 ÷ 2 =  1,  kalan 0
 1 ÷ 2 =  0,  kalan 1   (en soldaki bit)
```

Kalanları aşağıdan yukarı okuyunca `1000101` çıkar; başına bir sıfır koyup 8 bite tamamlarsak `0100 0101` — az önceki sayının aynısı. İki yöntem birbirini doğruladı.

### Bit, bayt ve kelime: ölçü birimleri

Bitler tek tek kullanılmaz; gruplanır. En yaygın grup **bayt (byte)**, yani 8 bit. Bir bayt 0 ile 255 arası 256 (`2⁸`) farklı değer tutabilir. İşlemcinin bir seferde rahatça işlediği bit grubuna ise **kelime (word)** denir; bugünkü çoğu bilgisayarda bu 64 bittir.

| Birim | Kaç bit | Kaç değer tutar |
|---|---|---|
| bit | 1 | 2 |
| nibble (yarım bayt) | 4 | 16 |
| bayt (byte) | 8 | 256 |
| kelime (word, tipik) | 64 | çok büyük (2⁶⁴) |

::: dikkat
Depolama birimlerinde bir kafa karışıklığı vardır: 1 kilobayt gerçekte 1000 mi yoksa 1024 mü? Standart olarak `KB = 1000 bayt`, `KiB (kibibayt) = 1024 bayt`. İşletim sistemleri çoğu zaman 1024'ü kullanıp "KB" yazdığı için diskin "500 GB" diye satılıp bilgisayarda daha küçük görünmesinin sebebi budur. `MertOS`'ta bellek yönetimi yazarken bu ayrımı net tutmak, ileride saç baş yolduran hataları önler.
:::

### Onaltılık sistem: insanlar için kısaltma

`0100 0101` gibi bir sayıyı okumak, yazmak, telefonda birine söylemek zahmetli. Bir bayt 8 bit ve gözün kolayca kaybolur. Bu yüzden mühendisler **onaltılık (hexadecimal)** sistemi bir stenografiye çevirdi.

Fikir çok zarif: 4 bit (bir nibble) tam olarak 0–15 arası bir değeri kodlar ve bu aralığı tek bir sembolle gösterebiliriz. 0–9 rakamlarını kullanır, sonra 10–15 için `A–F` harflerini ekleriz. Böylece her bayt **iki hex hanesine** iner:

| İkilik | Hex | Onluk |
|---|---|---|
| 0000 | 0 | 0 |
| 0101 | 5 | 5 |
| 1001 | 9 | 9 |
| 1010 | A | 10 |
| 1100 | C | 12 |
| 1111 | F | 15 |

`0100 0101` sayısını çevirmek artık çocuk oyuncağı: sol nibble `0100 = 4`, sağ nibble `0101 = 5`, sonuç `0x45`. Baştaki `0x` öneki "bu sayı onaltılıktır" demenin evrensel yolu. Bellek adreslerini, renk kodlarını (`#FF8800`), makine kodunu hep hex görmenin sebebi bu: ikiliğin sadakati, onluğa yakın okunabilirlik.

## 1.2 Negatif ve gerçek sayılar: Veri temsili

Şimdiye kadar hep pozitif tam sayılardan konuştuk. Peki `-5` nasıl saklanır? Ya da `3.14`? Bilgisayarın elinde yalnız 0 ve 1 varken, eksi işareti ya da virgül nereden gelecek? Cevap: gelmiyor. Onları da bir *anlaşmayla* bitlerin içine gömüyoruz.

### İşaretsiz ve işaretli sayılar

Bir baytı **işaretsiz (unsigned)** yorumlarsak, tüm 8 biti değere ayırırız: 0–255. Ama negatif sayılara da ihtiyacımız var. İlk akla gelen fikir, en soldaki biti "işaret biti" yapmak: 0 ise pozitif, 1 ise negatif. Bu yönteme *işaret-büyüklük* denir ama iki büyük derdi vardır: hem `+0` hem `-0` diye iki tane sıfır ortaya çıkar, hem de toplama devresi negatiflerde farklı davranmak zorunda kalır. Donanımcılar bunu sevmez.

### İki'ye tümleyen: zarif çözüm

Bütün modern işlemciler negatif sayıları **iki'ye tümleyen (two's complement)** ile temsil eder. Kuralı önce mekanik olarak verelim, sonra neden bu kadar akıllıca olduğunu göreceğiz. Bir sayının negatifini bulmak için: **tüm bitleri ters çevir, sonra 1 ekle.**

Örneğin 8 bitte `+5 = 0000 0101`. Bitleri ters çevir: `1111 1010`. Bir ekle: `1111 1011`. İşte bu `-5`. En soldaki bit hâlâ işareti söylüyor (1 = negatif) ama artık sıfır tek, üstelik toplama devresi hiçbir şeyi değiştirmeden çalışıyor.

Bu sistemi görselleştirmenin en güzel yolu, onu dairesel bir *sayaç* gibi düşünmektir:

![Şekil 1.2: 4-bit iki'ye tümleyen sistemin dairesel modeli. Dışta ikilik değer, içte işaretli karşılığı. Sayaç `0111` (+7) noktasından bir ileri gidince `1000`'e (−8) atlar; bu "taşma sınırı"dır. En soldaki bit 1 olan tüm değerler negatiftir.](gorseller/b01_twos.png)

Bu çemberin güzelliği şu: toplama, saat yönünde ilerlemek demek. `-1` yani `1111`'e bir eklersen çember başa döner ve `0000` yani `0` olursun — tam da matematikte beklediğin gibi. İşte bu yüzden `5 + (-5)` işlemi donanımda özel bir muamele istemeden `0` verir.

::: mulakat
"İki'ye tümleyende −8'in 4-bit karşılığı `1000`'dir ama +8 yoktur, neden?" — Çünkü çemberde 16 nokta var ve biri sıfıra gittiği için pozitif tarafta bir eksik kalır: aralık −8 ile +7 arasıdır. Bu asimetri neredeyse her düşük seviye mülakatta bir yerde karşına çıkar.
:::

### Taşma (overflow): çemberin kopduğu yer

İki'ye tümleyenin bir bedeli var. 4 bitte en büyük pozitif `+7`. Ona bir eklersen çember `−8`'e atlar. `7 + 1` işlemi `−8` verir! Buna **taşma (overflow)** denir ve gerçek bir hata kaynağıdır. C dilinde `signed char` (8 bit) türünde 127'ye 1 eklemek **tanımsız davranıştır (UB)**: C standardı işaretli taşmayı tanımlamaz. Tipik derleyicilerde sonuç −128 çıkar, ama bu garanti değildir; derleyici optimizasyonları bu durumu beklemediğin şekilde kullanabilir. Bu, oyunlardaki "skor bir anda eksiye düştü" efsanelerinin ve daha ciddi güvenlik açıklarının kaynağıdır.

### Karakterler: ASCII ve Unicode

Sayıları hallettik. Peki harfler? Aynı numara: bir *anlaşma tablosu* yapıp her karaktere bir sayı atarız. En eski ve temel anlaşma **ASCII**'dir; 7 bitle 128 karakteri kodlar. Birkaç örnek:

| Karakter | Onluk | Hex | İkilik |
|---|---|---|---|
| (boşluk) | 32 | 0x20 | 0010 0000 |
| '0' | 48 | 0x30 | 0011 0000 |
| 'A' | 65 | 0x41 | 0100 0001 |
| 'E' | 69 | 0x45 | 0100 0101 |
| 'a' | 97 | 0x61 | 0110 0001 |

Dikkat: `'A'` (65) ile `'a'` (97) arasında tam 32 fark var — yani tek bir bit (`0x20`). Küçük harfi büyüğe çevirmenin klasik bit numarası buradan gelir. Ayrıca `'0'` karakterinin değeri 48'dir, sayısal sıfır değil; bu yüzden bir rakam karakterini sayıya çevirirken `c - '0'` yaparız.

ASCII 128 karaktere sığar ama Türkçe'nin `ç, ğ, ı, ş, ö, ü` harfleri, emoji, Çince... hepsi sığmaz. Bu yüzden bugün **Unicode** ve onun en yaygın kodlaması **UTF-8** kullanılır. UTF-8'in dâhice yanı, ASCII ile geriye uyumlu olması: ilk 128 karakter birebir aynı, geri kalanlar için 2–4 bayt kullanır. `Sessiz Köprü` gibi Türkçe metinle çalışan bir uygulamada, bir `ş` harfinin neden tek değil iki bayt tuttuğunu artık biliyorsun.

### Ondalık sayılar: kayan nokta

`3.14` gibi sayılar için **kayan nokta (floating point)** temsili kullanılır. Fikir, bilimsel gösterime benzer: sayıyı `işaret × mantissa × 2^üs` biçiminde üç parçaya ayırırız. Bu sayede hem çok büyük hem çok küçük sayılar aynı 32 ya da 64 bite sığar. Bedeli ise **kesinlik kaybı**dır: bazı ondalıklar ikilikte tam ifade edilemez.

::: dikkat
Python'da `print(0.1 + 0.2)` ya da C'de `printf("%.17g\n", 0.1 + 0.2)` yazdırdığında `0.30000000000000004` görürsün. Bu bir hata değil, kayan noktanın doğası: `0.1` ikilikte tıpkı `1/3`'ün onlukta olduğu gibi sonsuz tekrar eden bir açılıma sahip, bir yerde kesiliyor. Bu yüzden para hesabı gibi yerlerde `float` yerine tam sayı (kuruş cinsinden) ya da özel ondalık türler kullanılır. Bu detay **Bölüm 50**'de (Optimizasyon) sayısal kararlılık bağlamında yeniden karşımıza çıkacak.
:::

## 1.3 Belleğin haritası: Bir program çalışırken RAM

Artık sayıları ve karakterleri bitlere gömmeyi biliyoruz. Ama bu bitler *nerede* durur? Cevap: **ana bellek**, yani RAM. RAM'i, her birinin bir **adresi** olan devasa bir posta kutuları dizisi gibi düşün. Her kutu bir bayt tutar, her kutunun benzersiz bir numarası (adresi) vardır: 0, 1, 2, ... Bir değişkene erişmek, aslında onun adresindeki kutuya bakmak demektir.

Bir program çalışmaya başladığında, işletim sistemi ona bu bellekten bir bölge ayırır ve bu bölgeyi dört ana **segmente** böler. Bu harita, C'de yazdığın her programın görünmez iskeletidir:

![Şekil 1.3: Çalışan bir sürecin bellek düzeni. Yüksek adreslerden düşük adreslere doğru: aşağı büyüyen yığın (stack), yukarı büyüyen öbek (heap), global/statik verilerin durduğu data/BSS ve salt-okunur makine kodunun bulunduğu text segmenti.](gorseller/b01_memory.png)

### Text (kod) segmenti

Programın **makine kodu** burada durur — az önce öğrendiğimiz gibi, komutlar da sonuçta sayıdır. Bu segment genellikle **salt-okunur**dur; program kendi kodunu yanlışlıkla (ya da kötü niyetle) değiştiremesin diye. Bir fonksiyonun adresini aldığında, aslında bu segmentteki bir yeri işaret ediyorsun.

### Data ve BSS: global ve statik değişkenler

Program boyunca yaşayan **global** ve **static** değişkenler burada oturur. İkiye ayrılır: ilk değeri verilmiş olanlar (`data`), ilk değeri sıfır olanlar (`BSS`). Bu değişkenler program başlarken doğar, program bitince ölür; ömürleri tüm çalışma süresidir.

### Stack (yığın): fonksiyonların defteri

İşte en çok iş gören segment. Bir fonksiyon çağırdığında, onun **yerel değişkenleri**, **parametreleri** ve **dönüş adresi** yığının tepesine bir "çerçeve" (stack frame) olarak yığılır. Fonksiyon bitince bu çerçeve tek hamlede atılır. Bu yüzden yerel değişkenler o kadar hızlıdır: yer açmak, sadece bir işaretçiyi (stack pointer) kaydırmaktır. Yığın yüksek adreslerden aşağı doğru büyür.

Recursion'ın (özyineleme) neden bellek yiyip bitirdiğini de artık görebilirsin: her özyineli çağrı yığına yeni bir çerçeve ekler. Taban durumuna hiç ulaşmayan bir recursion, yığını taşırır — meşhur `stack overflow`. Bu mekanizmayı **Bölüm 15**'te satır satır işleyeceğiz.

### Heap (öbek): senin kontrolündeki bellek

Bazen ne kadar belleğe ihtiyacın olacağını ancak program çalışırken bilirsin: kullanıcı 10 satır mı girecek, 10 milyon mu? İşte bu dinamik ihtiyaç için **öbek (heap)** vardır. C'de `malloc()` ile öbekten bir blok istersin, işin bitince `free()` ile geri verirsin. Öbek aşağıdan yukarı büyür ve yönetimi tamamen sana aittir — bu hem güç hem tehlike.

::: baglanti
İşaretçiler, `malloc`/`free` mekaniği, dangling pointer ve bellek sızıntıları **Bölüm 2**'de; işletim sisteminin bu segmentleri sayfalama (paging) ile fiziksel belleğe nasıl eşlediği **Bölüm 25**'te derinlemesine işlenir. `MertOS`'un bellek yöneticisini yazarken bu iki bölüm başucu kaynağın olacak.
:::

## 1.4 İşlemcinin içi: CPU nasıl komut işler

Belleğin haritasını çıkardık. Şimdi asıl oyuncuya, o bellekten komutları alıp hayata geçiren **CPU**'ya (Central Processing Unit, merkezi işlem birimi) geçelim. Çoğu bilgisayar, adını John von Neumann'dan alan zarif bir fikir üzerine kuruludur.

### Von Neumann mimarisi: komut da veri, veri de veri

**Von Neumann mimarisi**nin devrimci fikri şuydu: *komutları ve verileri aynı bellekte tut.* Yani programın kendisi de, üzerinde çalıştığı veriler de aynı RAM'de, aynı biçimde (sayılar olarak) durur. Bu, programların başka programları işlemesini, derleyicilerin var olmasını, hatta bir metin düzenleyicinin kod yazmasını mümkün kılan temeldir.

![Şekil 1.4: Von Neumann mimarisi. CPU'nun içinde kontrol birimi (CU), aritmetik-mantık birimi (ALU) ve yazmaçlar bulunur. CPU, ana bellek (RAM) ve giriş/çıkış birimleriyle ortak bir sistem yolu (bus) üzerinden konuşur.](gorseller/b01_vonneumann.png)

Şekildeki üç ana parçayı tanıyalım. **Kontrol Birimi (CU)** orkestra şefidir: hangi komutun ne zaman işleneceğini yönetir. **ALU** kasların olduğu yerdir: toplama, çıkarma, AND, OR gibi işlemleri yapar. **Yazmaçlar** ise şefin cebindeki not kâğıtlarıdır — birazdan onlara geleceğiz. Bu üçlü, bellek ve dış dünyayla **sistem yolu (bus)** üzerinden veri alışverişi yapar.

### Yazmaçlar: en hızlı bellek

Bir işlem yaparken CPU'nun elini uzatıp değerleri koyacağı bir yere ihtiyacı var. RAM'e gidip gelmek — CPU hızında düşünürsek — kilometrelerce uzaktaki bir depoya gidip gelmek gibidir. Bu yüzden CPU'nun *içinde*, avuç içi kadar ama ışık hızında çalışan bir bellek vardır: **yazmaçlar (registers)**.

![Şekil 1.5: Temel CPU yazmaçları. PC sıradaki komutun adresini, IR işlenmekte olan komutu, SP yığının tepesini tutar; genel amaçlı yazmaçlar ara hesaplar için, FLAGS ise son işlemin sonucu hakkındaki durum bayrakları içindir.](gorseller/b01_registers.png)

Bu yazmaçlardan üçü döngünün kalbinde yer alır: **PC (Program Counter)** sırada hangi komutun olduğunu söyler; **IR (Instruction Register)** o an işlenen komutu tutar; **SP (Stack Pointer)** ise yığının tepesini işaret eder — az önce konuştuğumuz stack segmentinin bağlantısı tam olarak burada. **FLAGS** yazmacı ise her işlemden sonra "sonuç sıfır mıydı, taşma oldu mu, negatif mi?" gibi soruların cevabını bit bit tutar; `if` ve döngü kararları aslında bu bayraklara bakar.

### Fetch-Decode-Execute: bilgisayarın kalp atışı

Şimdi her şeyi birleştiren döngüye geldik. CPU, açıldığı andan kapandığı ana kadar tek bir şeyi tekrar tekrar yapar: bir komut **getir**, ne olduğunu **çöz**, sonra **yürüt**. Sonra bir sonrakine geç. Milyarlarca kez, saniyede.

![Şekil 1.6: Komut döngüsü. PC'nin gösterdiği adresten komut getirilir (fetch) ve PC hemen bir sonraki komutu gösterecek şekilde ilerletilir; ardından komutun ne yapacağı çözülür (decode), ALU/yazmaçlar üzerinde yürütülür (execute) ve sonuç yazılır (writeback). Dallanma komutu, yürütme sırasında PC'nin üzerine yeni adres yazar. Döngü baştan başlar.](gorseller/b01_fde.png)

Adımları tek tek açalım:

1. **Getir (Fetch):** Kontrol birimi, PC'nin gösterdiği bellek adresine gider, oradaki komutu okuyup IR'ye koyar. PC fetch sırasında (komut okununca) ilerletilir; artık bir sonraki komutu gösterir.
2. **Çöz (Decode):** IR'deki sayı çözülür: "bu bir toplama komutu, şu iki yazmacı topla" gibi.
3. **Yürüt (Execute):** Komut ne diyorsa yapılır — ALU bir toplama yapar, bir değer belleğe yazılır, ya da PC bir başka adrese atlar (dallanma).
4. **Yaz (Writeback):** Sonuç ilgili yazmaca ya da belleğe yerleşir, FLAGS güncellenir.

Bu döngünün hızını **saat (clock)** belirler. "3 GHz işlemci" demek, bu ritmin saniyede yaklaşık 3 milyar kez tıkladığı anlamına gelir. Modern işlemciler tek tıkta birden çok komutu üst üste bindirerek (pipeline) daha da hızlanır; bu inceliği **Bölüm 24**'te açacağız.

### Somut örnek: `c = a + b` nasıl çalışır?

Soyut kalmasın. Diyelim `a` ve `b` bellekte duruyor ve `c = a + b` yazdın. Derleyici bunu kabaca şu makine komutlarına çevirir (basitleştirilmiş bir sözde-assembly ile):

```term
LOAD  R1, [a]     ; a'yı bellekten R1 yazmacına getir
LOAD  R2, [b]     ; b'yi bellekten R2 yazmacına getir
ADD   R3, R1, R2  ; R1 + R2 sonucunu R3'e koy (ALU çalışır)
STORE [c], R3     ; R3'ü c'nin bellek adresine yaz
```

Bu dört komutun her biri, tam olarak yukarıdaki getir-çöz-yürüt döngüsünden geçer. `c = a + b` gibi masum bir satırın altında dört ayrı bellek/ALU dansı olduğunu görmek, "yüksek seviye kod" ile "gerçekte olan" arasındaki köprüyü kurar. Bir gün bir kod parçasının neden yavaş olduğunu merak ettiğinde, işte bu seviyede düşünebilmek seni kurtaracak.

## 1.5 Sahadaki bitler: endianness ve IEEE-754

Bölümü kapatmadan, ders kitaplarının çoğunun atladığı ama sahada — özellikle gömülü sistem ve haberleşme dünyasında — ilk hafta karşına çıkacak iki gerçeğe inelim. İkisi de "bitleri biliyorum" ile "bitlerle çalışabiliyorum" arasındaki farkı ölçer.

### Bayt sırası: hangisi önce yazılır?

Bir baytın içindeki bitlerin sırası standarttır; ama `int` gibi **çok baytlı** bir değer belleğe yazılırken baytların hangi *sırayla* dizileceği mimariden mimariye değişir. `0x1A2B3C4D` sayısını dört bayta bölersen (`1A`, `2B`, `3C`, `4D`), iki meşru diziliş vardır:

![Şekil 1.7: Aynı 32-bit sayı, iki bayt sırası. Little-endian küçük anlamlı baytı (4D) küçük adrese koyar; x86 ve çoğu ARM böyle çalışır. Big-endian tersini yapar ve ağ protokollerinin standart sırasıdır.](gorseller/b01_endian.png)

**Little-endian** "küçük ucu önce" der: en az anlamlı bayt (`4D`) en küçük adrese. Masaüstündeki x86 işlemcin ve telefonundaki ARM çekirdeği (varsayılan modunda) böyledir. **Big-endian** ise insan okuyuşuna benzer: büyük uç önce. TCP/IP protokol ailesi tüm başlık alanlarını big-endian ister; bu yüzden ona **ağ baytı sırası (network byte order)** denir.

Peki bu ne zaman canını yakar? Tam olarak iki dünya birbirine veri gönderdiğinde. `EV Dashboard`'un STM32'den gelen sensör paketini okuduğunu düşün: kartın gönderdiği 4 baytlık hız değerini kendi sıranla yorumlarsan `0x1A2B3C4D` yerine `0x4D3C2B1A` okursun — doğru hız 439 milyon iken yanlış okumayla yaklaşık 1,3 milyar çıkar, gösterge çıldırır. Çözüm sözleşmedir: ağda ve dosya formatlarında sıra baştan ilan edilir; C'de `htonl`/`ntohl` (host-to-network-long) ailesi bu çeviriyi yapar (Bölüm 31'de socket yazarken kullanacağız).

Kendi makineni sorgulayan klasik numara, Bölüm 2'de öğreneceğin `union`'ın güzel bir kullanımıdır:

```c
#include <stdio.h>

int main(void) {
    union { unsigned int sayi; unsigned char bayt[4]; } test;
    test.sayi = 0x1A2B3C4D;              // aynı belleğe iki gözlük
    if (test.bayt[0] == 0x4D)            // ilk bayt küçük uç mu?
        printf("little-endian\n");
    else
        printf("big-endian\n");
    return 0;
}
```

`union` iki alanı aynı baytların üstüne serer: `sayi` olarak yazdık, `bayt[0]` ile ilk adresteki baytı okuduk. İlk bayt `4D` ise küçük uç önce yazılmış demektir.

::: not
Adlar Gulliver'in Seyahatleri'nden gelir: yumurtayı sivri ucundan mı, küt ucundan mı kırmalı diye savaşan iki krallık. Mühendislikteki savaş da benzer şekilde sonuçsuzdur — iki sıra da meşrudur; felaket, hangisinin kullanıldığını *sormamaktır*.
:::

### IEEE-754: float'ın bitlerini açmak

1.2'de kayan noktayı "işaret × mantis × 2^üs" diye tanıttım ve `0.1 + 0.2` sürprizini gösterdim. Şimdi kaputu tamamen açalım; çünkü ML kariyerinde her gün trilyonlarca kez çalışacak format bu — ve Bölüm 46'da modelleri küçültürken (FP16, INT8) bu bitlerle pazarlık edeceksin.

32-bit bir `float`, üç alana bölünür: 1 bit işaret, 8 bit üs, 23 bit mantis. `-6.25` sayısının yerleşimini izleyelim:

![Şekil 1.8: -6.25'in IEEE-754 tek duyarlık yerleşimi. Sayı önce ikilik bilimsel gösterime çevrilir (-1.1001₂ × 2²); işaret biti 1, üs alanına 2+127=129 yazılır (bias), mantise ise baştaki zorunlu 1 atılıp kalan (1001…) konur.](gorseller/b01_ieee754.png)

Çeviri üç adımdır ve her adım Bölüm 1'in araçlarıyla yapılır. Önce sayı ikiliğe çevrilir: `6.25 = 110.01₂` (4+2+0.25). Sonra virgül, başta tek bir 1 kalana dek kaydırılır: `1.1001₂ × 2²` — buna normalizasyon denir. Son olarak alanlar doldurulur: işaret 1 (negatif); üs alanına gerçek üs değil `2 + 127 = 129` yazılır (**bias**: negatif üsleri de işaretsiz saklayabilmek için); mantise baştaki `1.` *yazılmaz* (nasılsa hep 1 — bedava bir bit kazanılır, buna gizli bit denir), kalan `1001` yazılır.

Bu yapının üç pratik sonucu var:

- **Kesinlik sınırlıdır:** 23 bit mantis ≈ 7 anlamlı ondalık basamak (`float`), 52 bit ≈ 15-16 basamak (`double`). Yedi basamaktan sonrası yuvarlanır — sensör kalibrasyonunda `float`'a 8 haneli sabit gömmek, sessizce hassasiyet kaybıdır.
- **Dağılım eşit değildir:** temsil edilebilen sayılar 0 civarında sık, büyüdükçe seyrektir. `16777216.0f + 1.0f == 16777216.0f` — büyük float'a küçük eklemek kaybolabilir. Uzun toplamlarda birikim hatasının kaynağı budur (Bölüm 50'de optimizasyonda yeniden karşılaşacağız).
- **Özel değerler vardır:** üs alanı tamamen 1 olunca sonuçlar ayrılır: `±inf` (taşma) ve `NaN` (Not a Number — `0.0/0.0` gibi tanımsızlıklar). `NaN` hiçbir şeye, kendisine bile eşit değildir; ML eğitiminde loss'un `NaN`'a dönmesi, bu bitlerin sana "hesap patladı" demesidir.

::: dikkat
Kayan noktalı iki sayıyı `==` ile karşılaştırma. `0.1 + 0.2 == 0.3` yanlıştı; doğru kalıp tolerans karşılaştırmasıdır: `fabs(a - b) < 1e-9`. Testlerde, sensör eşiklerinde, geometri kodunda bu refleks yoksa, "bazen çalışan" türden hataların en sinsileriyle tanışırsın.
:::

## Çözümlü Örnekler

### Örnek 1 (★): 156 sayısını ikiliğe ve hex'e çevir

**Adım 1 — Anla.** Onluk `156` sayısının 8-bit ikilik ve onaltılık karşılığını elle bul.

**Adım 2 — Örnekle.** Önce sayıyı kuvvetlerin toplamı olarak parçalayalım: `156 = 128 + 16 + 8 + 4`. Her terim bir bitin ağırlığıdır; toplamda yer alan terimler, açık olan bitleri gösterir.

**Adım 3 — Kaba çöz.** İki yol var. Ya kalanlı bölme yaparım ya da basamak değerlerinden düşerim. Basamak değeri yöntemi hex için de işime yarayacağı için onu seçiyorum: 128'den başlayıp "sığar mı?" diye sorarım. Bu soruyu bit bit sorduğumda şu döküm çıkar:

```term
156 ≥ 128 ?  Evet → bit 128 = 1,  kalan 156−128 = 28
 28 ≥  64 ?  Hayır → bit  64 = 0
 28 ≥  32 ?  Hayır → bit  32 = 0
 28 ≥  16 ?  Evet → bit  16 = 1,  kalan 28−16 = 12
 12 ≥   8 ?  Evet → bit   8 = 1,  kalan 12−8  = 4
  4 ≥   4 ?  Evet → bit   4 = 1,  kalan 0
  0 ≥   2 ?  Hayır → bit   2 = 0
  0 ≥   1 ?  Hayır → bit   1 = 0
```

**Adım 4 — Örüntü.** Bitleri sırayla dizince `1001 1100`. Hex için iki nibble'a bakarım: `1001 = 9`, `1100 = C`. Yani `156 = 1001 1100 = 0x9C`. Örüntü şu: 8 bit iki nibble'dan oluşur ve her nibble tam bir hex hanesine denk gelir.

**Adım 5 — İyileştir.** Her sayı için 8 basamağı tek tek sormak yerine, Bölüm 1.1'deki onaltılık tabloyu kullanıp nibble'ları ayrı ayrı okumak daha hızlıdır: iki bakışta iki hane çıkar.

**Adım 6 — Doğrula.** Önce toplamla kontrol edelim: `9×16 + 12×1 = 144 + 12 = 156`. Tuttu. Aynı işi bit bit de yürütelim; her satırda kalan bir sonraki satıra taşınır:

| Adım | Ağırlık | Kalan (önce) | Bit | Kalan (sonra) |
|---|---|---|---|---|
| 1 | 128 | 156 | 1 | 28 |
| 2 | 64 | 28 | 0 | 28 |
| 3 | 32 | 28 | 0 | 28 |
| 4 | 16 | 28 | 1 | 12 |
| 5 | 8 | 12 | 1 | 4 |
| 6 | 4 | 4 | 1 | 0 |
| 7 | 2 | 0 | 0 | 0 |
| 8 | 1 | 0 | 0 | 0 |

Kalan sıfıra indiğinde ve bitler `1001 1100` olarak okunduğunda iz tutarlı.

::: not
Kendini sına: Bunu bir kâğıt ve kalemle, hiçbir araç açmadan yapabildin mi? Yapabildiysen 156 gibi başka üç sayı seç ve tekrarla. Bu çeviri, aşağıdaki bit manipülasyonu örneklerinin ve `MertOS`'taki register ayarlarının ön koşuludur.
:::

**Bunu AI'sız yazabilir misin?** Başka bir onluk sayıyı (ör. 200) hiçbir araç açmadan hem ikiliğe hem hex'e çevirebiliyor musun? Yapabiliyorsan bit ağırlıklarını aklında tutuyorsun demektir.

### Örnek 2 (★★): İki'ye tümleyende toplama

**Adım 1 — Anla.** 8-bit iki'ye tümleyen sistemde `−37` sayısını bul, sonra `5 + (−37)` işlemini ikilik olarak yap ve sonucu doğrula.

**Adım 2 — Örnekle.** Önce daha küçük bir deneme yapalım: `5 + (−1)`. 8 bitte `−1` = `1111 1111`'dir. `0000 0101 + 1111 1111` toplanınca en soldan taşan elde atılır ve `0000 0100` kalır; bu da `5 − 1 = 4` demek. Yöntem tutuyor, şimdi asıl soruya geçebiliriz.

**Adım 3 — Kaba çöz.** Önce `+37`'yi yazarım, sonra "ters çevir + 1" kuralıyla negatifini alırım. Toplamayı normal ikilik toplama gibi yapıp sonucu tekrar onluğa çevirerek kontrol ederim. Dökümü şöyle yapıyorum:

```term
+37 = 0010 0101
bitleri ters çevir → 1101 1010
bir ekle           → 1101 1011   =  −37

Şimdi 5 + (−37):
   0000 0101   (+5)
 + 1101 1011   (−37)
 -----------
   1110 0000
```

**Adım 4 — Örüntü.** Sonuç `1110 0000`. En soldaki bit 1, demek ki negatif. Onluk değerini bulmak için tekrar tümleyenini alırım: ters çevir `0001 1111`, bir ekle `0010 0000` = 32. Yani `1110 0000 = −32`. Örüntü şu: tümleyen alma işlemi iki yönde de aynıdır, pozitiften negatife de negatiften pozitife de (−128 istisnası dışında).

**Adım 5 — İyileştir.** Bu yöntemin kazancı, çıkarma için ayrı bir devre gerekmemesidir. `5 − 37` gibi bir işlemi sadece toplayarak yaptık. İki'ye tümleyenin bütün marifeti bu.

**Adım 6 — Doğrula.** `5 + (−37) = −32` olmalı. Bit bit yürüyelim: `a = 0000 0101` (+5), `b = 1101 1011` (−37). Her sütunda elde bir sol bite taşınır:

| Bit | a | b | Elde girişi | Toplam biti | Elde çıkışı |
|---|---|---|---|---|---|
| 0 | 1 | 1 | 0 | 0 | 1 |
| 1 | 0 | 1 | 1 | 0 | 1 |
| 2 | 1 | 0 | 1 | 0 | 1 |
| 3 | 0 | 1 | 1 | 0 | 1 |
| 4 | 0 | 1 | 1 | 0 | 1 |
| 5 | 0 | 0 | 1 | 1 | 0 |
| 6 | 0 | 1 | 0 | 1 | 0 |
| 7 | 0 | 1 | 0 | 1 | 0 |

Toplam bitleri soldan sağa `1110 0000` eder; bu da −32'dir. Doğrulama tamam.

**Bunu AI'sız yazabilir misin?** Boş bir IDE'de `signed char x = 5, y = -37;` tanımlayıp `x + y` sonucunu ve her birinin bitlerini yazdıran küçük bir C programı düşün. Bitleri elle çıkardığınla program çıktısı birebir uyuşmalı.

### Örnek 3 (★★): Bir baytın bitlerini yazdıran fonksiyon

**Adım 1 — Anla.** `unsigned char` bir sayının 8 bitini soldan sağa (`bit 7 → bit 0`) yazdıran bir C fonksiyonu yaz. Her bit için tek bir karakter (`'0'` ya da `'1'`) basılacak.

**Adım 2 — Örnekle.** Somut bir sayıyla deneyelim: `69 = 0100 0101`. Bit 6 (64), bit 2 (4) ve bit 0 (1) açık; bit 7, 5, 4, 3 ve 1 kapalı. Fonksiyon tam bu deseni basmalı.

**Adım 3 — Kaba çöz.** Her biti tek tek nasıl "görürüm"? Bir maske kullanırım. `1 << i` ifadesi, yalnız i'nci biti 1 olan bir maske üretir. Bu maskeyi sayıyla `&` (AND) yaparsam, o bitin açık olup olmadığını öğrenirim. En soldan başlamak için `i`'yi 7'den 0'a doğru azaltırım. Aşağıdaki fonksiyon bu fikri doğrudan uygular:

```c
#include <stdio.h>

// bir baytın bitlerini bit7'den bit0'a yazdırır
void bitleri_yaz(unsigned char sayi) {
    for (int i = 7; i >= 0; i--) {   // en anlamlı bitten başla
        unsigned char maske = 1 << i;  // sadece i. bit 1 olan maske
        putchar((sayi & maske) ? '1' : '0');  // o bit açık mı?
        if (i == 4) putchar(' ');     // nibble'ları ayır
    }
    putchar('\n');
}

int main(void) {
    bitleri_yaz(69);   // beklenen: 0100 0101
    return 0;
}
```

**Adım 4 — Örüntü.** İşin kalbi `sayi & maske` satırında. `maske`, döngü ilerledikçe `1000 0000`, `0100 0000`, ... `0000 0001` değerlerini alır. AND işlemi, yalnızca ilgili bit hem sayıda hem maskede 1 ise 1 verir; böylece o biti tek başına yalıtmış oluruz.

**Adım 5 — İyileştir.** `if (i == 4) putchar(' ');` satırı bit 4'ten sonra bir boşluk basar; böylece çıktı iki nibble'a bölünmüş okunur. Bu, sadece okunabilirlik için eklenmiş bir dokunuştur; bitlerin değerini değiştirmez.

**Adım 6 — Doğrula.** `putchar` ile ya `'1'` ya `'0'` basarız. Her adımda ne olduğunu tabloda izleyelim:

| i | maske | sayi & maske | Basılan |
|---|---|---|---|
| 7 | 1000 0000 | 0000 0000 | 0 |
| 6 | 0100 0000 | 0100 0000 | 1 |
| 5 | 0010 0000 | 0000 0000 | 0 |
| 4 | 0001 0000 | 0000 0000 | 0 (sonra boşluk) |
| 3 | 0000 1000 | 0000 0000 | 0 |
| 2 | 0000 0100 | 0000 0100 | 1 |
| 1 | 0000 0010 | 0000 0000 | 0 |
| 0 | 0000 0001 | 0000 0001 | 1 |

Basılan karakterler `0100 0101` eder; bu da 69'dur. Çıktı:

```term
$ gcc bit.c -o bit && ./bit
0100 0101
```

**Bunu AI'sız yazabilir misin?** Asıl sınav şu: `1 << i` neden işe yarıyor ve neden `i`'yi 7'den başlattık? Bu iki soruya kendi cümlelerinle cevap verebiliyorsan, kodu ezberlemene gerek yok — her seferinde yeniden türetebilirsin.

### Örnek 4 (★★★): Hangi değişken hangi segmentte?

**Adım 1 — Anla.** Aşağıdaki C kodunda geçen değerlerin her biri hangi bellek segmentinde yaşar? Ayrıca bu kodda gizli bir hata var; bul.

```c
#include <stdlib.h>   // malloc ve free için

int global_sayac = 0;          // (A)
char *mesaj = "Merhaba";       // (B) işaretçi ve gösterdiği metin

char *isim_uret(void) {
    char tampon[32] = "Mert";  // (C)
    return tampon;             // (D) dikkat!
}

int main(void) {
    int *dizi = malloc(100 * sizeof(int));  // (E)
    // ...
}
```

**Adım 2 — Örnekle.** Önce tek bir değere bakalım: `global_sayac` program başlarken vardır, `main` çalışmaya başlamadan önce de yerindedir ve program bitene kadar yaşar. Şimdi aynı soruyu yerel `tampon` için soralım; o, fonksiyon dönünce yok olacak.

**Adım 3 — Kaba çöz.** Her değeri "ne zaman doğar, ne zaman ölür?" diye sorgularım. Program boyunca yaşayanlar data/BSS'te, fonksiyonla gelip giden yerel değişkenler stack'te, `malloc` ile gelen her şey heap'te, sabit metinler ve kod ise salt-okunur bölgede olur. Kaba cevaplar şöyle:

- **(A)** `global_sayac`: global ve ilk değeri 0 → **BSS segmenti**.
- **(B)** `mesaj` işaretçisinin kendisi global → **data**; ama gösterdiği `"Merhaba"` metni salt-okunur bir sabit → **text/rodata**.
- **(C)** `tampon` dizisi `isim_uret` içinde yerel → **stack**. Fonksiyon dönünce çerçevesiyle birlikte yok olur.
- **(D)** İşte hata: fonksiyon, yok olacak bir stack değişkeninin adresini döndürüyor. Çağıran taraf bu adrese eriştiğinde çoktan geçersiz olmuş bir belleğe dokunur — **dangling pointer**. Derleyici çoğu zaman uyarır ama durdurmaz.
- **(E)** `malloc`'tan gelen blok → **heap**. Kullanımı bitince `free` gerekir, yoksa sızıntı olur.

**Adım 4 — Örüntü.** Beş değerin hepsi üç kurala bağlanıyor: ömrü program boyunca olanlar data/BSS ya da text'te, fonksiyon çerçevesiyle yaşayanlar stack'te, açıkça istenen bellek heap'te durur. Bir adresin geçerli olup olmadığını, o adresin hangi kuralla yaşadığına bakarak sorabilirsin.

**Adım 5 — İyileştir.** (D)'yi düzeltmenin iki yolu var: çağıran taraf bir tampon verir (`isim_uret(char *cikis, size_t n)` gibi bir imza), ya da `tampon` `static` yapılır. Birinci yol sahipliği açık tutar. İkincisi her çağrıda aynı belleği paylaştırır; bu yüzden iki çağrının sonucu birbirini ezer. (E) için de yapılacak iş net: `main` sonunda `free(dizi)` şarttır.

**Adım 6 — Doğrula.** Hatanın zaman içinde nasıl ilerlediğini izleyelim:

| Adım | Olay | `tampon`'un durumu | Sonuç |
|---|---|---|---|
| 1 | `isim_uret()` çağrılır | Çerçevede, stack'te yaşıyor | — |
| 2 | `tampon` `"Mert"` ile dolar | Geçerli | — |
| 3 | `return tampon;` çalışır | Çerçeve atılır, `tampon` ölür | Adres dışarı döner |
| 4 | Çağıran taraf adrese erişir | Geçersiz (dangling pointer) | Tanımsız davranış (UB) |

Sonuç öngörülemez: içerik bazen hâlâ `Mert` gibi görünür, bazen bir sonraki fonksiyon çağrısı onu ezer. Windows'ta MSVC bu hatayı C4172, GCC ise `-Wreturn-local-addr` uyarısıyla bildirir; uyarıyı susturmak yerine nedenini anla.

**Bunu AI'sız yazabilir misin?** Bir sonraki C kodunu okurken, gözünle her değişkeni bu dört segmentten birine yerleştirmeyi alışkanlık hâline getir. Bu refleks, ileride en zor bellek hatalarını dakikalar içinde çözmeni sağlayacak.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçlarını kullanmak **yasak**. Amaç doğru cevaba ulaşmak değil; bağımsız düşünme kasını çalıştırmak. Takılırsan ipuçlarına dön, kâğıda çiz, ama çözümü başkasına yazdırma.
:::

### Proje 1 (★★): Elle çalışan taban çevirici

**Amaç:** Onluk bir sayıyı alıp ikilik ve onaltılık karşılığını yazdıran bir C programı yaz. Ama önce şart: aynı 5 sayıyı programı yazmadan **elle** çevir, sonra programının onları doğruladığını gör.

**Beklenen girdi/çıktı:** Girdi `156`, çıktı `1001 1100` ve `0x9C` gibi.

**Önerilen yaklaşım:** İkilik için Örnek 3'teki maske fikrini kullanabilirsin. Hex için sayıyı 4'erli nibble'lara ayırıp her nibble'ı `0–9` ya da `A–F` karakterine eşleyen bir tablo düşün. `printf`'in `%x` biçimini *kullanma* — amacımız çeviriyi kendi elinle yapmak.

**Başarı kriterleri:** 0, 255, 156 ve senin seçtiğin iki sayı için elle bulduğun sonuçla programın çıktısı birebir aynı olmalı. Negatif sayılar için `unsigned` yorumunu da denersen bonus.

### Proje 2 (★★★): Minik bir sanal makine

**Amaç:** Kendi küçük "işlemcini" yaz. Bellek olarak bir dizi, birkaç yazmaç ve bir fetch-decode-execute döngüsü kurarak dört komutluk bir sanal makine yap. Bu proje, `MertOS`'un çekirdeğinde olan biteni anlaman için bulunmaz bir egzersiz.

**Beklenen davranış:** Program olarak verdiğin komut dizisini işleyip bir sonuç yazdırmalı. Örneğin `LOAD 5`, `ADD 3`, `PRINT` komutları `8` üretmeli.

**Önerilen yaklaşım (bu sırayla ilerle):**

1. **Temel — veri yapısı.** Komutları basit sayılarla kodla (örn. `LOAD=1, ADD=2, STORE=3, PRINT=4`) ve komut dizisini bir dizide tut. Bir `pc` (program counter) değişkeni ile bir `akumulator` yazmacı tanımla; başlangıçta ikisinin değeri ne olmalı, önce kâğıtta düşün.
2. **Döngü.** Bir `while` döngüsü kur: `pc`'nin gösterdiği komutu getir, `switch` ile ne olduğunu çöz, ilgili işlemi yürüt, `pc`'yi ilerlet. Bu tam olarak Şekil 1.6'daki döngü.
3. **Kenar durumlar.** Bilinmeyen bir komut kodu geldiğinde ne yapacağını, komut dizisi bittiğinde döngünün nasıl duracağını ve `pc`'nin dizinin dışına çıkmasını nasıl önleyeceğini tasarla.

**Başarı kriterleri:** En az dört farklı komutu doğru işlemeli, program sonuna gelince temiz durmalı ve sen döngünün her adımında hangi yazmacın ne değer aldığını kâğıt üstünde takip edebilmelisin.

### Ek Alıştırmalar

Aşağıdaki problemlerin çözümü yok. Her birini önce kâğıtta dene, sonra kodla doğrula.

1. **★ Taban çevirici.** Onluk bir `unsigned int` değerini yalnız 2'ye bölme ve kalanı alma işlemleriyle ikilik olarak yazan bir fonksiyon yaz. `0` girdisi için de doğru çalışmalı.

2. **★ Yorumlama.** `0x7F`, `0x80` ve `0xFF` değerlerini önce `unsigned char`, sonra `signed char` olarak yorumlarsan karşılıkları ne olur? Bu üç değerden hangileri negatif çıkar ve neden?

3. **★★ İki'ye tümleyen (mülakat).** `-` operatörünü kullanmadan, bit işlemleriyle bir `int` değerin negatifini hesaplayan bir fonksiyon yaz. Hangi girdi için sonuç beklediğinden farklı çıkar ve neden?

4. **★★ İkinin kuvveti (mülakat).** Döngü, `/` ve `%` kullanmadan, bir sayının 2'nin bir kuvveti olup olmadığını bit işlemiyle test et. Sonuç `0` için ne olmalı?

5. **★★ Bit ters çevirme (mülakat).** 8 bitlik bir değerin bit sırasını ters çeviren bir fonksiyon yaz; `0000 0001` girdisi `1000 0000` üretmeli. Sonra aynı fikri 32 bitlik bir `unsigned int` için nasıl genelleyeceğini düşün.

6. **★★ Tek kalan (mülakat).** Her elemanı iki kez geçen, yalnız bir elemanı tek geçen bir tamsayı dizisinde o tek elemanı bul. Ek bellek kullanmadan, diziyi bir kez tarayarak çözmeye çalış.

7. **★★ Bayt sırası.** Bir `unsigned int` değerinin 4 baytını elle yer değiştirip ters bayt sırasına çeviren bir fonksiyon yaz. Sonucu, Bölüm 1.5'teki `union` testiyle bellekte gerçekten beklenen sırada olduğunu kontrol et.

8. **★★★ Float'ın bitleri (mülakat).** `1.0`, `0.5` ve `-6.25` için IEEE-754 tek duyarlık yerleşimini (işaret, üs, mantis) önce kâğıtta hesapla. Sonra bir `union` ile programda yazdırıp karşılaştır.

9. **★★★ Kaybolan küçük sayı (mülakat).** `1.0f + 1e-8f - 1.0f` ifadesi neden `0` çıkar? Bölüm 1.5'teki 7 basamak kuralını ve 1'e yakın float'ların aralığını düşünerek açıkla, sonra programla doğrula.

10. **★★ Segment avcısı.** Global, static, yerel ve `malloc` ile alınmış dört değişkenin adreslerini yazdır; hangi adres aralığının hangi segmente ait olduğunu tahmin et. Adresler sistemden sisteme değişir, tahminini ölçümle doğrula.

11. **★★★ Taşmayı önceden gör (mülakat).** İki pozitif `int` değerin toplamının taşıp taşmayacağını, toplamayı yapmadan ve tanımsız davranışa (UB) düşmeden kontrol eden bir fonksiyon yaz.

12. **★ Maskeleme.** `0x1F`, `0xA0` ve `0x3C` değerlerinin ikilik karşılıklarını yaz. Sonra her birinin düşük nibble'ını (`& 0x0F`) ve yüksek nibble'ını (`& 0xF0`) ayır; sonuçları bir tabloda göster.

## Kod Okuma Egzersizi

Başkasının kodunu okumak, en az kod yazmak kadar önemli bir kas. Aşağıda Linux çekirdeğinde ve sayısız gerçek projede karşına çıkacak, bit temelli iki klasik parça var.

```c
/* Linux çekirdeği tarzı bit makroları */
#define BIT(n)     (1UL << (n))       /* n. biti 1 yapan maske */
#define SET(x, n)     ((x) |=  BIT(n))      /* n. biti kur */
#define CLR(x, n)     ((x) &= ~BIT(n))      /* n. biti temizle */
#define TEST(x, n)    ((x) &   BIT(n))      /* n. bit açık mı? */
```

Bu makrolar, tek bir tamsayının içine onlarca "açık/kapalı" bayrağı sığdırmanın standart yoludur; gömülü sistemlerde bir donanım register'ının bitlerini ayarlarken tam da bunları kullanacaksın (**Bölüm 43**).

İkinci parça, bir sayıdaki 1 bitlerini sayan meşhur **Kernighan** numarası:

```c
int bir_say(unsigned int n) {
    int sayac = 0;
    while (n) {           // n sıfır olana dek
        n &= (n - 1);     // en sağdaki 1 bitini sıfırla
        sayac++;
    }
    return sayac;
}
```

**Sorular — cevaplamadan geçme:**

- `SET`, `CLR`, `TEST` makrolarında sırasıyla neden `|`, `& ~`, `&` kullanıldı? Her birinin neden o işlemle çalıştığını bir cümleyle açıkla.
- `CLR` makrosundaki `~BIT(n)` ifadesi ne üretir ve neden AND ile birleştirince tam olarak istediğimiz biti temizler?
- Asıl bilmece: `n & (n - 1)` işlemi neden **en sağdaki 1 bitini** siler? İpucu: `n = 1011 0000` için `n - 1`'i elle yaz ve ikisini AND'le. Bir örnek bütün sırrı çözer.
- Bu döngü kaç kez döner? Sayının bit sayısıyla mı, yoksa içindeki 1 sayısıyla mı orantılı? Bu neden onu "saf" bir döngüden daha akıllı yapar?

## Bölüm Özeti

Bu bölümde bilgisayarın en alt katmanını, sıfırdan kurduk:

- **İkilik sistem** bir tercih değil, transistörün fiziksel doğasının sonucu: güvenilir iki durum. Bit, bilginin en küçük birimi.
- Sayılar **basamak ağırlıklarıyla** temsil edilir; ikilikten onluğa geçmek "açık bitlerin ağırlıklarını toplamak"tan ibaret. **Hex**, ikiliğin insan-dostu kısaltmasıdır (her nibble bir hane).
- Negatif sayılar **iki'ye tümleyen** ile tutulur: ters çevir, bir ekle. Bu yöntem tek sıfır verir ve toplama devresini basitleştirir. Sınırı aşınca **taşma** olur.
- Karakterler bir **anlaşma tablosuyla** (ASCII, sonra Unicode/UTF-8) sayılara eşlenir; ondalıklar **kayan nokta** ile temsil edilir ve kaçınılmaz bir kesinlik bedeli taşır.
- Çalışan bir program bellekte dört segmente ayrılır: **text** (kod), **data/BSS** (global/statik), **heap** (dinamik, senin kontrolünde), **stack** (fonksiyon çerçeveleri).
- **CPU**, von Neumann mimarisinde komutu ve veriyi aynı bellekte tutar; **yazmaçlar** en hızlı belleğidir ve **fetch-decode-execute** döngüsüyle her komutu tek tek işler.
- Çok baytlı değerlerin bellekteki sırası mimariye bağlıdır: **little-endian** (x86/ARM) küçük ucu önce yazar, ağ protokolleri **big-endian** ister — iki dünya konuşurken sıra sözleşmeyle sabitlenir.
- **IEEE-754**, float'ı işaret + biaslı üs + gizli bitli mantis olarak paketler: ~7 (float) / ~15 (double) anlamlı basamak, eşit olmayan dağılım, `inf`/`NaN` özel değerleri. Kayan noktada `==` yok, tolerans var.

En önemlisi: `c = a + b` gibi bir satırın altında dört ayrı makine komutu ve bir sürü bit dansı olduğunu artık *görebiliyorsun*. Bu görüş, iyi bir mühendisi yüzeysel bir kullanıcıdan ayıran şeydir.

**Sonraki bölümde:** Bu temelin üzerine ilk gerçek aracımızı koyacağız. **Bölüm 2 — C Dili**'nde, belleği doğrudan konuşan bir dille tanışacak; işaretçileri, `malloc`/`free`'yi ve bu bölümde adını andığımız dangling pointer gibi tehlikeleri bizzat ellemeye başlayacaksın.

::: mulakat
Bu bölümü gerçekten sindirdiysen, aşağıdaki klasik mülakat sorularına rahatça yaklaşabilmelisin. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün.

1. Stack ile heap arasındaki fark nedir? Hangi değişken nerede saklanır ve neden stack "daha hızlı"dır?
2. İki'ye tümleyen neden işaret-büyüklük yönteminden üstündür? `+0` ve `−0` sorunu ne demek?
3. `0.1 + 0.2 == 0.3` neden çoğu dilde `false` döner?
4. Bir işaretçi 64-bit sistemde kaç bayttır ve bir diziyi fonksiyona geçirince `sizeof` neden dizinin boyutunu vermez?
5. Fetch-decode-execute döngüsünü tek cümleyle anlat. `if` kararı bu döngünün neresinde, hangi yazmaca bakarak verilir?
6. Little-endian bir makinede `0x12345678` değerinin ilk baytı bellekte nedir? Ağa gönderirken neden `htonl` gerekir?
:::
