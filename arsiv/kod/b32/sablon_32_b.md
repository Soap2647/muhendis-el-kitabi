## 32.5 Bellek güvenliği: C'de hata sınıfları

C'de bellek güvenliği dilin değil, programcının sorumluluğundadır. Derleyici bir dizinin sınırını, serbest bırakılmış bir belleğin hâlâ kullanılıp kullanılmadığını ya da bir tamsayının taşıp taşmadığını çoğu durumda denetlemez. Bunların bir kısmı **tanımsız davranıştır** (undefined behavior, UB): standart ne olacağını söylemez, sonuç derleyiciye, optimizasyon düzeyine ve mimariye göre değişir. Bölüm 2.6'da tampon sınırını ve Bölüm 8'de yığın çerçevesini gördük; burada bu tekil hataların güvenlik açısından ne anlama geldiğini ve nasıl yakalanacağını öğreniyoruz.

Bu bölümün en önemli ilkesi burada da geçerlidir: bir hatayı düzeltmek için önce onu **görünür kılmak** gerekir. Bu yüzden her hata sınıfı için üç şey yapacağız: hatalı küçük bir program yazacağız, bir sanitizer ile hatanın raporunu alacağız ve düzeltilmiş sürümü aynı sanitizer ile doğrulayacağız. Aşağıdaki tablo sınıfları, nedenlerini ve tespit araçlarını özetler.

| Hata sınıfı | Neden oluşur | Tespit | Önleme |
|---|---|---|---|
| Tampon taşması | Yazma sınırı denetlenmez | ASan, `-Wall`, `-fanalyzer` | Sınırlı API, boyut denetimi |
| Serbest bırakılmış belleği kullanma | Yaşam süresi karışır | ASan, `-fanalyzer` | Sahipliği tek noktada tut, NULL'la |
| Çift serbest bırakma | Sahiplik belirsizdir | ASan, `-fanalyzer` | Sahiplik kuralı, `free` sonrası NULL |
| Tamsayı taşması | Boyut hesabı taşar | UBSan (işaretli), derleyici | `__builtin_mul_overflow` |
| Biçim dizesi | Girdi biçim dizesi olarak kullanılır | `-Wformat-security` | Sabit biçim dizesi |
| Sınır dışı okuma | Uzunluk alanına körü körüne güvenilir | ASan | Uzunluğu üst sınırla denetle |

![Şekil 32.8: Bellek hata sınıfları ve bunları yakalayan araçlar. Her sınıfın yanındaki araç, hatayı çalışma zamanında ya da derleme zamanında gösterebilir.](gorseller/b32_bellek.png)

::: not
Bu bölümdeki sanitizer raporları WSL2 içindeki Ubuntu 24.04 ve gcc 13.3.0 ile alındı. Windows'taki MSVC da bir ASan desteği sunar, ama rapor biçimi ve kapsamı farklıdır. ASan raporlarındaki adresler her çalıştırmada değişir; önemli olan rapordaki işaretçi, boyut ve kaynak satırı bilgileridir.
:::

### Tampon taşması

`strcpy` hedefin boyutunu bilmez; kaynağı sonuna kadar kopyalar. Aşağıdaki fonksiyonda 16 baytlık bir yerel dizi var, ama girdinin uzunluğu sınırsız. 40 karakterlik bir girdi, yığında tamponun komşusundaki belleğe taşar. Yığında bu komşuluk, bir fonksiyonun yerel değişkenleri ile çağrı bilgileri (dönüş adresi dahil) arasında olabilir. Bölüm 8'de gördüğün yığın çerçevesi bunu açıklar. Burada önemli olan şudur: taşan yazma, tamponun dışındaki bir değeri değiştirir ve bu değer programın davranışını belirler.

@@KOD b32_c1_hatali.c@@

Kodu derleyip ASan ile çalıştırıyoruz. Girdi olarak 40 karakterlik bir dizi veriyoruz; program bir hata raporu basıp durur.

@@TERM§./c1a AAAA...A (40 karakter)§ulimit -c 0; gcc -g -O0 -fno-omit-frame-pointer -fsanitize=address -std=c11 b32_c1_hatali.c -o c1a && ./c1a $(printf 'A%.0s' {1..40}) 2>&1 | sed -e 's#/mnt/c/Users/merty/AppData/Local/Temp/b32/##g' | sed -n '2,6p' | fold -w 74@@

Raporu okumayı öğren. İkinci satır hatanın türünü söyler: `stack-buffer-overflow`, yani yığın tamponunun taşması. Üçüncü satır yazmanın boyutunu (41 bayt, sonlandırıcı NUL dahil) ve adresi verir. Dördüncü ve beşinci satırlar hatayı üreten çağrının `strcpy` olduğunu ve kaynak satırının `b32_c1_hatali.c:12` olduğunu gösterir. Rapordaki "located in stack ... offset 48" bilgisi, tamponun yığında olduğunu ve taşmanın komşu alana değdiğini söyler.

Düzeltme, sınırı kopyalama işleminin içine koymaktır. `snprintf` en fazla `sizeof(ad)` baytı yazar ve sonunu NUL ile kapatır. Dönüş değeri, kesilmiş olsaydı yazılacak uzunluğu verir; bu değeri kullanarak kesilmeyi tespit edip girdiyi reddediyoruz. Kesmek yerine reddetmenin nedeni, kesilmiş bir yolun ya da kimliğin anlamının sessizce değişmesini önlemektir.

@@KOD b32_c1_duzeltilmis.c@@

Düzeltilmiş sürümü aynı 40 karakterle ve kısa bir girdiyle çalıştıralım. İlki reddedilir, ikincisi normal çalışır.

@@TERM§./c1d AAAA...A; ./c1d ali§gcc -O2 -Wall -Wextra -std=c11 b32_c1_duzeltilmis.c -o c1d && ./c1d $(printf 'A%.0s' {1..40}); echo "cikis=$?"; ./c1d ali; echo "cikis=$?"@@

Dikkat edilmesi gereken bir tuzak daha var: `strncpy` hedefi sonlandırmaz ve hedef dolduğunda NUL eklemez. `strncpy` ile kopyalanan bir dizinin `strlen` ile okunması, yine bir taşmaya yol açabilir. Güvenli kopyada sonlandırıcının hesaba katıldığını her zaman kontrol et.

### Serbest bırakılmış belleği kullanma (use-after-free)

Bir işaretçi `free` ile belleği serbest bıraktıktan sonra hâlâ o adresi gösterir. Bu işaretçi üzerinden okuma ya da yazma tanımsız davranıştır. Bellek hemen değişmediği için program çoğu zaman "çalışmış" gibi görünür; bu şans, hatanın testlerde görünmemesinin en yaygın nedenidir.

@@KOD b32_c2_hatali.c@@

ASan, serbest bırakılan bellek bölgesini özel olarak işaretler ve erişimi yakalar. Raporda üç bilgi aranır: hatanın türü (`heap-use-after-free`), erişimin türü (`READ`) ve belleğin nerede serbest bırakıldığı.

@@TERM§./c2h§gcc -g -O0 -fsanitize=address -std=c11 b32_c2_hatali.c -o c2h && ./c2h 2>&1 | sed -e 's#/mnt/c/Users/merty/AppData/Local/Temp/b32/##g' | sed -n '2,4p' | fold -w 74@@

Düzeltmede iki kural uygulanır. Birincisi, serbest bırakmadan önce gereken değer okunur. İkincisi, işaretçi serbest bırakıldıktan sonra NULL yapılır; böylece yanlışlıkla kullanılırsa bir sonraki erişim NULL işaretçi hatası olarak hemen ortaya çıkar. Düzeltilmiş sürümde ASan'ın sessiz kaldığını da göreceksin.

@@KOD b32_c2_duzeltilmis.c@@

@@TERM§./c2d§gcc -g -O0 -fsanitize=address -std=c11 b32_c2_duzeltilmis.c -o c2d && ./c2d; echo "cikis=$?"@@

### Çift serbest bırakma (double free)

Aynı bellek bloğunu iki kez `free` etmek, allocator'ın iç veri yapısını bozar. Bu hata bazen çökmeye, bazen sessiz bellek bozulmasına yol açar. Sorun çoğunlukla sahipliğin belirsiz olmasından doğar: iki fonksiyon da belleği serbest bırakmayı kendisinin görevi sanır.

@@KOD b32_c3_hatali.c@@

@@TERM§./c3h§gcc -g -O0 -fsanitize=address -std=c11 b32_c3_hatali.c -o c3h && ./c3h 2>&1 | sed -e 's#/mnt/c/Users/merty/AppData/Local/Temp/b32/##g' | sed -n '2,3p' | fold -w 74@@

Düzeltmenin kuralı şudur: belleği serbest bırakan fonksiyon, işaretçiyi de NULL yapar. `free(NULL)` tanımlıdır ve hiçbir şey yapmaz; yani ikinci çağrı zararsız olur. Bu bir kalıp değil, sahiplik tasarımının sonucudur: belleği kimin serbest bıraktığını tek bir yerde bil.

@@KOD b32_c3_duzeltilmis.c@@

@@TERM§./c3d§gcc -g -O0 -fsanitize=address -std=c11 b32_c3_duzeltilmis.c -o c3d && ./c3d; echo "cikis=$?"@@

### Tamsayı taşması ve yanlış boyut

Bir dizi için bellek ayırırken genellikle `eleman_sayisi * sizeof(eleman)` hesaplanır. Bu çarpım, işaretli bir tamsayıda taşabilir. İşaretli tamsayı taşması tanımsız davranıştır; sonuç derleyiciye göre değişir. İşaretsiz tamsayılarda taşma tanımlıdır (modüler aritmetik), ama bu sonucun doğru olduğu anlamına gelmez: taşan çarpım küçük bir boyut verir ve sonraki döngü, ayrılan alanın çok ötesine yazar.

Aşağıdaki programda `n * 4` hesabı `int` ile yapılıyor. `n = 1073741825` (2^30 + 1) için matematiksel çarpım 4294967300'dür ve 32 bitlik `int` bunu taşırır. UBSan bu taşmayı işaretler; ASan ise taşan `malloc` boyutu yüzünden oluşan yazma hatasını gösterir.

@@KOD b32_c4_hatali.c@@

@@TERM§./c4h 1073741825§gcc -g -O0 -fsanitize=address,undefined -std=c11 b32_c4_hatali.c -o c4h && ./c4h 1073741825 2>&1 | sed -e 's#/mnt/c/Users/merty/AppData/Local/Temp/b32/##g' | sed -n '1,3p' | fold -w 74@@

Raporun ilk satırı UBSan'dan gelir; taşan işlemi, değerleri ve türü söyler. Sonraki satırlar ASan'dan gelir: `heap-buffer-overflow` ve `WRITE of size 4`, yani ayrılan alanın dışına 4 baytlık bir yazma. Düzeltme boyut hesabını `size_t` üzerinde yapar ve `__builtin_mul_overflow` ile taşmayı hesap anında tespit eder. Taşma varsa ayırma yapılmaz.

@@KOD b32_c4_duzeltilmis.c@@

Düzeltilmiş sürümü iki girdiyle deneyelim: taşacak kadar büyük bir değer ve normal bir değer.

@@TERM§./c4d 4611686018427387904; ./c4d 16§gcc -g -O0 -fsanitize=address,undefined -std=c11 b32_c4_duzeltilmis.c -o c4d && ./c4d 4611686018427387904; echo "cikis=$?"; ./c4d 16; echo "cikis=$?"@@

### Biçim dizesi (format string)

`printf` ailesinin ilk argümanı bir biçim dizesidir. Girdi bir biçim dizesi olarak kullanılırsa, saldırganın belirlediği `%` dizileri, programın beklemediği argümanları okumaya ya da yazmaya yol açabilir. Derleyici bu hatayı bazı durumlarda uyarır; uyarıyı kapatmamak ilk savunmadır.

@@KOD b32_c5_hatali.c@@

@@TERM§gcc -O2 -Wall -Wextra ... b32_c5_hatali.c§gcc -O2 -Wall -Wextra -std=c11 b32_c5_hatali.c -o c5h 2>&1 | head -4 | fold -w 74@@

Uyarı, girdinin bir biçim dizesi olarak kullanıldığını söyler. Düzeltme basittir: girdi her zaman bir argüman olarak verilir ve biçim dizesi sabit bir değerdir. Biçim dizesi hatasının asıl tehlikesi, `%n` gibi yazma yapan dizilerin de kullanılabilmesidir; bu bölümde bu tekniği göstermiyoruz, yalnızca hatayı ve düzeltmeyi gösteriyoruz.

@@KOD b32_c5_duzeltilmis.c@@

@@TERM§./c5d "yuzde %% isareti"§gcc -O2 -Wall -Wextra -std=c11 b32_c5_duzeltilmis.c -o c5d 2>/dev/null; gcc -O2 -std=c11 b32_c5_hatali.c -o c5h 2>/dev/null; ./c5d "yuzde %% isareti"; ./c5h "yuzde %% isareti"@@

### Tanımsız davranışı doğru adlandırmak

Bu dört sınıfın ortak noktası, programın hata verdiğini bildirmemesidir. Bu yüzden testlerin geçmesi güvenlik kanıtı değildir. Üç araç yaygın olarak kullanılır. **ASan** (AddressSanitizer), bellek erişimlerini izleyerek sınır dışı ve serbest bırakılmış bellek erişimlerini yakalar. **UBSan** (UndefinedBehaviorSanitizer), taşma gibi tanımsız işlemleri çalışma zamanında işaretler. **`-fanalyzer`**, derleyicinin statik analiz motorudur; hatayı çalıştırmadan, kod yolları üzerinde arar. Bunu 32.8'de kullanacağız.

Sanitizer'lar hızı ve bellek kullanımını artırır; bu yüzden test ortamında kullanılır, üretimde kullanılmaz. Ayrıca bir sanitizer'ın raporu yalnızca çalıştırılan yolu kapsar: bir hata, test etmediğin bir girdide kalabilir. Bu yüzden fuzzing (32.8) ve sanitizer birlikte kullanılır.

::: baglanti
Bölüm 23'te kod kalitesi ve statik analiz araçlarından söz etmiştik. `-fanalyzer` de aynı ailedendir; farkı, yalnızca biçimi değil yol boyunca bellek durumunu izlemesidir.
:::

### Bellek güvenli diller

Rust gibi diller, sahiplik (ownership) ve ödünç alma (borrow) kurallarını derleme zamanında denetler. Güvenli Rust kodunda serbest bırakılmış belleğe erişim ve veri yarışı derlenmez. Bu, bu sınıftaki hataların dilin kendisi tarafından önlenmesi demektir. Bununla birlikte `unsafe` blokları ve C kütüphaneleriyle çağrı (FFI) sınırı, güvenlik sorumluluğunu yeniden programcıya bırakır. Bu kitapta C'de kalmamızın nedeni, gömülü sistemlerde (Kısım XI) ve işletim sistemlerinde (Kısım VI) C'nin hâlâ baskın olmasıdır; kavramlar ortaktır.

## 32.6 Derinlemesine savunma: derleyici ve işletim sistemi korumaları

Hataları önlemek birinci savunmadır; ama hiçbir büyük yazılımda tüm hataların önlenebileceğini varsaymamak gerekir. **Derinlemesine savunma** (Şekil 32.2) burada devreye girer: derleyici ve işletim sistemi, hatanın kötüye kullanılmasını zorlaştıran katmanlar koyar. Bu katmanlar bir hatayı **düzeltmez**; yalnızca bedelini artırır. Bu farkı akılda tut: bir koruma açıldığında hata hâlâ oradadır.

| Koruma | Ne yapar | Nasıl açılır (gcc / Linux) |
|---|---|---|
| Yığın kanaryası | Dönüş adresinden önce bir değer koyar; bozulursa programı durdurur | `-fstack-protector-strong` |
| FORTIFY | Boyutu bilinen tamponlarda kopya işlevlerini denetimli sürümüyle değiştirir | `-D_FORTIFY_SOURCE=2` (`-O` ile) |
| NX (DEP) | Veri bölgelerinin çalıştırılmasını engeller | Yığın için `GNU_STACK` bayrağı `RW` olmalı |
| ASLR | Bellek yerleşimini her çalıştırmada rastgeleleştirir | Çekirdek: `randomize_va_space` |
| PIE | Program kodunu da rastgele bir adrese yükler | `-pie` (Ubuntu varsayılanı) |
| RELRO / BIND_NOW | Dinamik bağlama tablosunu başlangıçtan sonra yazmaya kapatır | `-Wl,-z,relro -Wl,-z,now` |

Her koruma farklı bir aşamayı zorlaştırır. Yığın kanaryası, yığın üzerinden dönüş adresinin bozulmasını yakalar ve programı `stack smashing detected` mesajıyla durdurur. NX, veri bölgesine yerleştirilen bir kodun çalıştırılmasını engeller; bunu sağlayan, Bölüm 25'te gördüğün sayfa tablosu bitidir. ASLR, kod ve yığın adreslerini tahmin edilemez kılar. PIE, ikili kodunu da bu rastgeleleştirmeye dahil eder. RELRO, dinamik bağlama tablolarını başlangıçtan sonra salt okunur yapar.

![Şekil 32.9: Korumalar bir saldırının farklı aşamalarını zorlaştırır. Hiçbiri tek başına yeterli değildir; hatanın kendisi düzeltildiğinde ve birlikte kullanıldıklarında anlam kazanırlar.](gorseller/b32_koruma.png)

Önce bir ikilinin hangi korumalara sahip olduğunu denetleyen küçük bir araç yazıyoruz. Bu araç yalnızca `readelf` çıktısını okur; ikiliyi çalıştırmaz. Bir ikilinin başlık bilgilerini okumak, gerçek bir güvenlik denetiminin ilk adımıdır: sürümünün beklenen korumalara sahip olup olmadığını bilmek istersin.

@@KOD b32_korumalar.py 14 40@@

Denetçiyi iki ikili üzerinde çalıştırıyoruz. Birincisi Ubuntu'nun varsayılan ayarlarıyla, ikincisi bilinçli olarak korumaları kapatarak derlenmiş. Bu karşılaştırma, hangi bayrağın hangi korumayı açtığını gösterir.

@@TERM§python3 b32_korumalar.py ./k_varsayilan ./k_zayif§gcc -O2 -Wall -Wextra -std=c11 b32_c1_hatali.c -o k_varsayilan 2>/dev/null; gcc -O2 -fno-stack-protector -U_FORTIFY_SOURCE -no-pie -z execstack -Wl,-z,norelro -std=c11 b32_c1_hatali.c -o k_zayif 2>/dev/null; python3 b32_korumalar.py ./k_varsayilan ./k_zayif@@

Zayıf ikilide NX "YOK" olarak görünür ve yığın bayrağı `RWE` (yazılabilir ve çalıştırılabilir) çıkar; bu, yığının çalıştırılmasına izin verir. Bu bayrağı yalnızca bu deneyde bilerek açtık: gerçek bir ürünün bu bayrakla derlenmesi ciddi bir hatadır. Şimdi korumaların davranışını tek tek görelim. Önce yalnızca yığın kanaryasını açık bırakıp FORTIFY'yi kapatalım; böylece kanaryanın mesajı görünür.

@@TERM§./k_kanarili AAAA...A (40 karakter)§gcc -O2 -fstack-protector-strong -U_FORTIFY_SOURCE -std=c11 b32_c1_hatali.c -o k_kanarili 2>/dev/null; ulimit -c 0; ./k_kanarili $(printf 'A%.0s' {1..40}); echo "cikis=$?"@@

Mesaj `*** stack smashing detected ***` ve program çıkış kodu 134 (SIGABRT) ile sonlanır. Kanaryanın yaptığı iş budur: taşmayı fark eder ve kontrolü, bozulmuş bir dönüş adresinden önce durdurur. Aynı hatayı FORTIFY açıkken derlediğimizde farklı bir mesaj görürüz; çünkü `strcpy` çağrısı denetimli sürümle değiştirilmiştir ve kanaryaya ulaşılmadan program durur.

@@TERM§./k_varsayilan AAAA...A (40 karakter)§gcc -O2 -Wall -Wextra -std=c11 b32_c1_hatali.c -o k_varsayilan 2>/dev/null; ulimit -c 0; ./k_varsayilan $(printf 'A%.0s' {1..40}); echo "cikis=$?"@@

Son olarak, bütün korumaları kapatılmış ikiliyi aynı girdiyle çalıştırıyoruz. Program kontrolsüz biçimde çöker (segmentation fault, çıkış kodu 139). Bu, koruma olmadığında hatanın nasıl davrandığının somut bir örneğidir: program çöker. Çöküş bir kayıptır, ama en kötüsü değildir; sessiz kalmış bir bozulma çok daha tehlikelidir.

@@TERM§./k_zayif AAAA...A (40 karakter)§ulimit -c 0; ./k_zayif $(printf 'A%.0s' {1..40}); echo "cikis=$?"@@

ASLR'nin etkisini kendi programımızda görelim. Aşağıdaki program yığın değişkeninin, bir fonksiyonun ve heap bloğunun adreslerini yazdırır. Üç çalıştırmada değerler değişir; ASLR'yi `setarch -R` ile kapattığımızda ise her çalıştırmada aynı kalır.

@@KOD b32_c7_aslr.c@@

@@TERM§./c7 (3 kez) ve setarch x86_64 -R ./c7 (2 kez)§gcc -O0 -Wall -Wextra -std=c11 b32_c7_aslr.c -o c7 && for i in 1 2 3; do ./c7; done; echo "-- setarch -R:"; for i in 1 2; do setarch x86_64 -R ./c7; done@@

Çıktıda sistemin ASLR değeri 2'dir (tam rastgeleleştirme) ve yığın, kod ve heap adresleri her çalıştırmada değişir. `setarch -R` ile yapılan çalıştırmalarda adresler sabittir. Bu fark, ASLR'nin neyi değiştirdiğini ve neyi değiştirmediğini gösterir: adresleri değiştirir, ama bellekteki hatayı ortadan kaldırmaz. Bir sızıntı yoluyla adres öğrenilirse ASLR'nin değeri azalır; bu yüzden yalnızca ASLR'ye güvenmek yetmez.

FORTIFY'nin davranışını bilinen boyutlu bir tampon üzerinde görelim. Burada derleyici `memcpy`'nin hedef boyutunu bilir ve denetimli sürümü seçer.

@@KOD b32_c6_fortify.c@@

@@TERM§./c6 kisa; ./c6 "bu metin sekiz bayttan uzun"§gcc -O2 -D_FORTIFY_SOURCE=2 -Wall -Wextra -std=c11 b32_c6_fortify.c -o c6 && ./c6 kisa; echo "cikis=$?"; ulimit -c 0; ./c6 "bu metin sekiz bayttan uzun"; echo "cikis=$?"@@

Kısa girdi normal kopyalanır. Uzun girdi `*** buffer overflow detected ***` mesajıyla durur. Bu koruma, boyutu derleme zamanında bilinen durumlarda çalışır; boyut çalışma zamanında belirliyse sınır denetimini sen yazmalısın. Korumaya güvenmek yerine sınırı açıkça kontrol etmek her zaman doğru yoldur.

Bir mimari notu: Cortex-M (STM32 gibi) ve ARM64 gibi ARM çekirdeklerinde, bir fonksiyon çağrıldığında dönüş adresi LR yazmacına konur. Yaprak olmayan bir fonksiyon, LR'yi çağrı yapmadan önce yığına kaydeder. Yani bir yığın taşması, bu kaydedilmiş değeri ezebilir. Derleyici korumaları ARM hedefleri için de vardır, ama her hedef ve derleyici sürümü için bunların açık olduğunu derleme çıktısından kontrol etmelisin. x86'da dönüş adresi `call` ile yığına yazılır; ARM'da ise bu yalnızca yaprak olmayan fonksiyonlarda yığına iner. Mimari farkları için Bölüm 1 ve Bölüm 24 iyi bir başlangıçtır.

::: dikkat
Üretim derlemesinde korumaları kapatmak için bir gerekçe yoktur. Yalnızca bir ikilinin korumalarını denetleyen bir adım ekle ve korumaları kaybeden her derlemenin hata sayılmasını sağla; bu adım CI'da başarısız olmalıdır.
:::

::: baglanti
Bölüm 24'te Meltdown ve Spectre'in azaltımlarının (KPTI gibi) çekirdek girişini nasıl pahalılaştırdığını gördün. Bellek korumaları ile spekülatif yürütme azaltımları aynı felsefeyi paylaşır: güvenlik, bir performans bedeli ile satın alınır.
:::
