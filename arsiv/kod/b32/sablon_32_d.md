## Çözümlü Örnekler

Aşağıdaki dört örnek, Bölüm 5'teki altı adımlı yöntemi izler: Anla, Örnekle, Kaba çöz, Örüntü, İyileştir, Doğrula. Her örneğin sonunda elle iz sürme tablosu vardır. Önce kâğıda çöz, sonra çıktıyla karşılaştır.

### Örnek 1 (★): Telemetri akışının kabul ve red kararlarını izlemek

Bölüm 32.3'teki alıcı, her pakette üç soru sorar: etiket doğru mu, sıra numarası son kabul edilenden büyük mü, paket beklenen uzunlukta mı. Bu örnekte bu üç sorunun sırasının neden önemli olduğunu göreceksin.

**Adım 1 — Anla.** Alıcının durumu tek bir değişkendir: `son_sira`, başlangıçta -1. Bir paket geldiğinde önce uzunluk kontrol edilir (40 bayt). Sonra etiket HMAC ile yeniden hesaplanıp karşılaştırılır. Etiket doğruysa sıra numarası `son_sira` ile karşılaştırılır. Sıra büyükse paket kabul edilir ve `son_sira` güncellenir. Her red durumunda `son_sira` değişmez.

**Adım 2 — Örnekle.** Sekiz paket gelir. Paketlerin bir kısmı kasıtlı olarak bozulmuştur: 2. pakette bir bit değişmiş, 6. paketin uzunluğu 39 bayttır. Sıra numaraları 1, 2, 2, 2, 1, 5, 6, 6'dır.

**Adım 3 — Kaba çöz.** Her paket için kararı yukarıdan aşağı soralım. Önce uzunluk, sonra etiket, sonra sıra. İlk red kararında diğer kontrollere gerek yoktur, ama bu tabloda her paketin hangi kontrolde takıldığını görmek için yine de sırayla gideceğiz.

**Adım 4 — Örüntü.** Bir tekrar eden kural var: sıra numarası hiçbir zaman geri gitmez, ama aynı numara ikinci kez gelirse reddedilir. Bu, `son_sira` karşılaştırmasının iki işi birden yaptığını gösterir: tekrar oynatmayı ve sıra dışı paketleri engeller.

**Adım 5 — İyileştir.** Bu kuralın bir sonucu, sıra numarası boşluklarıdır. 3 ve 4 numaralı paketler hiç gelmedi; alıcı bunları kayıp sayabilir, ama bu bir **tahmindir**: paketler gecikmiş olarak da gelebilir, ama bu tasarımda gecikmiş paketler zaten reddedilir. Gerçek bir sistemde bu tahmin, bir pencere (window) mekanizmasıyla yumuşatılır; bu tasarım bunu yapmaz.

**Adım 6 — Doğrula.** Aşağıdaki tabloyu kâğıtta doldur, sonra karşılaştır.

| No | Sıra | Uzunluk | Etiket | Sıra > son? | Karar | son (sonra) |
|---|---|---|---|---|---|---|
| 1 | 1 | 40 | geçerli | 1 > -1 evet | kabul | 1 |
| 2 | 2 | 40 | bozuk | — | red (etiket) | 1 |
| 3 | 2 | 40 | geçerli | 2 > 1 evet | kabul | 2 |
| 4 | 2 | 40 | geçerli | 2 > 2 hayır | red (tekrar) | 2 |
| 5 | 1 | 40 | geçerli | 1 > 2 hayır | red (tekrar) | 2 |
| 6 | 5 | 39 | — | — | red (biçim) | 2 |
| 7 | 5 | 40 | geçerli | 5 > 2 evet | kabul | 5 |
| 8 | 6 | 40 | geçerli | 6 > 5 evet | kabul | 6 |

Tablo 2 numaralı paketin bozuk olduğunu, ama 3 numaralı paketin aynı sıra numarasıyla kabul edildiğini gösterir. Bu doğrudur: bozuk paket `son_sira`'yı değiştirmedi. 6 numaralı paketin reddi de aynı şekilde `son_sira`'ya dokunmaz. 7 numaralı paket 5'i kabul eder; sıra numarası 5 olduğu için boşluk 3 ve 4 ile ilgili kayıp tahmini burada yapılmış olur.

**Bunu AI'sız yazabilir misin?** Aynı kuralları üreten bir `alici_karar(paket, durum)` fonksiyonu yaz. Fonksiyon, bir `(karar, yeni_durum)` çifti döndürsün. Sekiz paketlik bir diziyle tabloyu yeniden üret ve her satırın sonucunu elle yazdığın tabloyla karşılaştır.

### Örnek 2 (★★): Parola kaydının doğrulamasında sınır denetimi

Bölüm 32.2'deki `parola_dogrula` fonksiyonu bir kayıt satırını alır. Kayıt bir veritabanından gelir ve veritabanı sızmış olabilir; bu yüzden kayıttaki her alan güvenilmez kabul edilir. Bu örnekte dört farklı kaydın doğrulamasını elle izleyeceğiz.

**Adım 1 — Anla.** Kayıt `scrypt$n$r$p$tuz_hex$ozet_hex` biçimindedir. Fonksiyon önce kaydı altı parçaya böler, sonra `n`, `r`, `p` değerlerini tamsayıya ve tuz ile özeti hex'ten bayta çevirir. Ardından `n` değeri `2 ≤ n ≤ N_MAKS` aralığında mı diye bakar. Bu denetim, `scrypt` hesabından önce yapılır.

**Adım 2 — Örnekle.** Dört kayıt deneyeceğiz: (a) doğru parolanın geçerli kaydı, (b) yanlış parola, (c) `n = 1073741824` (2^30) olan bir kayıt, (d) tuz alanında geçersiz hex olan bir kayıt. `N_MAKS = 2^20 = 1048576`.

**Adım 3 — Kaba çöz.** (a) ve (b) için scrypt hesabı çalışır, sonuçlar sabit zamanlı karşılaştırılır. (c) için `n` aralığın dışındadır ve fonksiyon hesap yapmadan `False` döner. (d) için `bytes.fromhex` `ValueError` fırlatır; bu, `try` bloğunda yakalanır ve `False` döner.

**Adım 4 — Örüntü.** Kayıt bir **güvenilmeyen girdidir** ve her alan için iki denetim gerekir: biçim (ayrıştırma hatası) ve değer aralığı. Biçim hatası istisna ile yakalanır; değer aralığı hatası ise hesaplamadan önce reddedilir. İkinci denetim olmasaydı, kayıttaki büyük bir `n` sunucuda aşırı bellek ayırmasına yol açabilirdi.

**Adım 5 — İyileştir.** Fonksiyonun bir eksiği var: `r` ve `p` değerlerine üst sınır konmamış. `r` büyüdükçe bellek kullanımı artar; bu yüzden gerçek bir sistemde `r` ve `p` için de üst sınırlar tanımlanmalıdır. Bu bölümde bu sınırı eklemedik; ödev olarak bırakıyoruz.

**Adım 6 — Doğrula.** Tabloyu doldur ve `test` kipinin çıktısıyla karşılaştır.

| Kayıt | Ayrıştırma | n aralığı | Hesap | Sonuç |
|---|---|---|---|---|
| (a) doğru parola | başarılı | 2^14 uygun | scrypt yapıldı, eşleşti | True |
| (b) yanlış parola | başarılı | 2^14 uygun | scrypt yapıldı, eşleşmedi | False |
| (c) n = 2^30 | başarılı | 2^30 > 2^20, red | yapılmadı | False |
| (d) tuz "zz" | `ValueError` | — | yapılmadı | False |

Testteki "asiri n sinirda red" kontrolü, (c) satırının davranışını doğrular. Bu tablo ile test çıktısının aynı sonucu verdiğini görmelisin.

**Bunu AI'sız yazabilir misin?** Kaydı biçimine göre ayrıştıran ve bir `(n, r, p, tuz, ozet)` demeti döndüren, geçersiz alanlarda `ValueError` fırlatan bir `kayit_coz` fonksiyonu yaz. Üst sınır denetimini bu fonksiyonun içinde değil, çağıranda yapmanın hangi riski doğurduğunu iki cümleyle açıkla.

### Örnek 3 (★★): Yol geçişinde üç kontrolün sırası

Bölüm 32.7'deki `guvenli_yol` fonksiyonu üç kontrol yapar: NUL baytı, gerçek yol ve kök dizin ile ortak yol karşılaştırması. Bu örnekte kök dizinin `/srv/kok` olduğunu varsayarak beş isteği izleyeceğiz.

**Adım 1 — Anla.** Fonksiyon önce NUL baytını arar; varsa `None` döner. Sonra kök dizinin gerçek yolunu alır, isteği birleştirip gerçek yolunu bulur ve `commonpath([kok, aday])` ile ortak öneki hesaplar. Ortak önek kök dizinden farklıysa aday kökün dışındadır.

**Adım 2 — Örnekle.** İstekler: `a.txt`, `../gizli`, `/../gizli`, `alt/../b`, ve `a\x00b`.

**Adım 3 — Kaba çöz.** `a.txt` için birleştirme `/srv/kok/a.txt` verir, ortak önek `/srv/kok`'tur, eşleşir: kabul. `../gizli` için birleştirme `/srv/kok/../gizli`'yi `/srv/gizli`'ye normalleştirir; ortak önek `/srv`'dir: red. `/../gizli` baştaki eğik çizgi silindikten sonra `../gizli` ile aynıdır: red. `alt/../b` `/srv/kok/b`'ye düşer: kabul. `a\x00b` ilk kontrolde reddedilir.

**Adım 4 — Örüntü.** Kökten çıkmanın tüm yolları, birleştirme sonrası gerçek yolun kökün altında kalıp kalmadığına bakılarak yakalanır. Girdinin nasıl yazıldığı (`/`, `..`, `alt/..`) önemli değildir; ölçüt sonuçtur. Bu nedenle kontrolü girdi metninde değil, çözümlenmiş yolda yapmak gerekir.

**Adım 5 — İyileştir.** `realpath` sembolik bağları da çözer. Bu, kök içinde görünen bir bağın dışarıya işaret etmesi durumunu da yakalar; bunu bu örnekte iz sürmedik ama aynı mantıkla çalışır. Sistem gerçek bir sembolik bağa sahip olduğunda, `realpath`'in ne döndüreceğini kendin doğrulamalısın.

**Adım 6 — Doğrula.** Tablo:

| İstek | Birleştirme (normalleştirilmiş) | Ortak önek | Karar |
|---|---|---|---|
| `a.txt` | `/srv/kok/a.txt` | `/srv/kok` | kabul |
| `../gizli` | `/srv/gizli` | `/srv` | red |
| `/../gizli` | `/srv/gizli` | `/srv` | red |
| `alt/../b` | `/srv/kok/b` | `/srv/kok` | kabul |
| `a\x00b` | — | — | red (NUL) |

Tablo, Bölüm 32.7'deki `yol` kipinin mantığını izler: naif sürüm `../gizli` için kökten çıkar, güvenli sürüm reddeder.

**Bunu AI'sız yazabilir misin?** `/srv/kok` yerine kök dizin olarak `/srv/kok/` (sondaki eğik çizgiyle) verilirse ne olur? `commonpath` ve `realpath` bu sondaki eğik çizgiyi nasıl ele alır? Cevabını Python'da bir kez dene ve açıkla.

### Örnek 4 (★★★): Tamsayı taşmasından doğan yanlış `malloc` boyutu

Bölüm 32.5'teki `dizi_olustur` fonksiyonu `n * 4` hesabını `int` ile yapar. Bu örnekte farklı `n` değerleri için hesabın ne olduğunu izleyeceğiz; hem işaretli `int` hem de düzeltilmiş `size_t` sürümü için.

**Adım 1 — Anla.** Fonksiyon `bayt = n * (int)sizeof(int)` hesaplar, sonra `malloc((size_t)bayt)` çağırır ve `n` tamsayı yazar. İşaretli `int` taşması tanımsız davranıştır. Pratikte derleyiciler genellikle modüler (2'nin tümleyeni) sonucu üretir, ama bu standardın garantisi değildir.

**Adım 2 — Örnekle.** Dört `n` değeri: 16, 2^30, 2^30 + 1 ve 2^62. İlk üçü `int` sürümünde, dördüncüsü `size_t` sürümünde denenecek.

**Adım 3 — Kaba çöz.** `n = 16` için `16 * 4 = 64`, taşma yok. `n = 2^30` için matematiksel çarpım `2^32`'dir; 32 bitlik sonuç modüler olarak `0` olur. `malloc(0)` ayırma büyüklüğü sıfır olan bir istektir; döndürülen değer kullanılamaz ve yazma hatası doğurur. `n = 2^30 + 1` için matematiksel çarpım 4294967300'dür; 32 bit sonucu `4`'tür; `malloc(4)` yalnızca 4 bayt verir, döngü ise 2^30 + 1 tamsayı yazmaya çalışır. `n = 2^62` için `size_t` çarpımı `2^64`'tür ve taşar.

**Adım 4 — Örüntü.** Taşan çarpım **küçük** bir sonuç verir ve bu sonuç, döngünün ihtiyacını karşılamaz. Hata, bellek ayırma ile yazma döngüsü arasındaki boyut uyuşmazlığıdır. Düzeltme de bu uyuşmazlığı yok etmektir: ayırmadan önce hesabın taşmadığını kanıtla.

**Adım 5 — İyileştir.** `__builtin_mul_overflow(n, sizeof(int), &bayt)` çarpımı yapar ve taşma varsa `1` döner; yani sonucu kullanmadan önce bir kez kontrol edersin. Tip olarak `size_t` kullanmak da hesabın işaretsiz olmasını sağlar, ama bu tek başına yeterli değildir: `n` büyükse taşma yine olur.

**Adım 6 — Doğrula.** Tablo:

| n | Matematiksel n·4 | 32 bit `int` sonucu | `malloc` boyutu | Düzeltilmiş sürüm |
|---|---|---|---|---|
| 16 | 64 | 64 | 64 | ayırır, yazar |
| 2^30 | 4294967296 | 0 | 0 (hatalı) | taşma, NULL döner |
| 2^30 + 1 | 4294967300 | 4 | 4 (hatalı) | taşma, NULL döner |
| 2^62 (size_t) | 2^64 | — | — | taşma, NULL döner |

Gerçek derleme ASan ile çalıştırıldığında, `n = 2^30 + 1` için UBSan işaretli taşmayı, ASan ise yazma hatasını raporlar. Düzeltilmiş sürüm `2^62` değerinde reddeder ve `16` değerinde normal çalışır. Tablodaki hesapların çıktıyla uyumlu olduğunu doğrula.

**Bunu AI'sız yazabilir misin?** `n` değerinin bir dizi uzunluğu olarak kullanıldığı bir `int` fonksiyonunda taşmayı önleyen sürümü, ayırmanın yanında yazma döngüsünün de `n` ile sınırlı olduğunu gösteren bir yorumla birlikte yaz. Taşmanın yalnızca çarpımda değil, toplamda da (`n + 1`) olabileceğini bir örnekle göster.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçları **yasak**. Amaç çalışan bir sistem üretmekten çok, güvenliğin tasarım kararlarını ve bu kararların bedelini kendi gözlemlerinle anlamak. Bir protokol tasarlarken her alanın neden orada olduğunu yaz; bir hata bulduğunda, onu hangi girdiyle tetiklediğini kanıtla. Çözümü dışarıdan alma.
:::

### Proje 1 (★★): İHA yer istasyonu protokolünü güvenli hâle getirme

**Amaç:** Bölüm 31'deki telemetri ve komut protokolünü, bu bölümde öğrendiğin ilkelerle sertleştirmek: gizlilik, bütünlük, tekrar oynatma koruması ve anahtar türetme. Proje sonunda, bir ağ simülatöründe kayıp ve bozulma altında da doğru çalışan bir protokol olmalı.

**Beklenen davranış:** Simülatör saniyede 10 telemetri paketi üretir. Paketler AEAD ile şifrelenir; ek veri olarak sıra numarası ve paket türü bağlanır. Ana anahtar bir paylaşılan sırdan (ortak gizli değer) HMAC tabanlı bir türetmeyle iki ayrı anahtara ayrılır: biri şifreleme, biri komut kanalının doğrulaması için. Simülatör paketleri %10 oranında düşürür, %5 oranında bir bit bozar ve %5 oranında çoğaltır. Alıcı, kabul ettiği paketlerin sıra numaralarını ve red sebeplerini sayar. Komut kanalı Ed25519 ile imzalanır; komut, sıra numarası ile tekrar oynatılamaz.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Önce hangi alanın gizli, hangi alanın yalnızca doğrulanan olduğunu bir tabloya yaz. Anahtar türetme için sürüm ve bağlam bilgisini (örneğin "telemetri" ve "komut" etiketlerini) girdiye ekle; böylece aynı ana anahtardan türetilen iki anahtarın birbirine karışmadığını doğrula. Sıra numarasını alıcı tarafında kalıcı tut ve yeniden başlatmada ne olacağını tasarla. Simülatörde kayıp ve bozulmayı ayrı tohumlu üreteçlerle yap ki deneyler tekrarlanabilir olsun.

**Başarı kriterleri:**
- Simülatör %10 kayıp, %5 bit bozulması ve %5 çoğaltma ile 600 paket gönderdiğinde, hiçbir bozulmuş paket kabul edilmez (kabul sayısı, bozulan sayısından fazla değildir).
- Aynı paketin ikinci kez gelmesi, hiçbir durumda ikinci bir uygulama etkisi yaratmaz.
- Şifreli paketin ek verisinin (sıra numarası) değiştirilmesi her zaman reddedilir.
- Komut kanalında imzası geçersiz bir komut hiçbir zaman uygulanmaz; geçerli bir komut tam olarak bir kez uygulanır.

### Proje 2 (★★★): Bölüm 30 ve 31 ayrıştırıcıları için fuzzing çatısı

**Amaç:** Bu bölümdeki fuzzer'ı genelleştirip, Bölüm 30 ve 31'deki ayrıştırıcılar için her hedefin sözleşmesini açıkça tanımlayan, tekrarlanabilir ve bulunan hataları en küçük örneğe indiren bir çatı yazmak. Çatının amacı, bir ayrıştırıcıya yeni bir alan eklediğinde sessizce bir açık oluşmasını önlemektir.

**Beklenen davranış:** Her hedef, bir `(kabul_istisnalari, fonksiyon, tohumlar)` üçlüsüyle tanımlanır. Çatı, her hedef için sabit tohumlu N yineleme çalıştırır ve beklenmeyen istisnaları sınıflandırır. Bulunan her hata için en kısa yeniden üretici saklanır; bu üretici bir dosyaya yazılır ve sonradan tek başına çalıştırılabilir. Çatı, ayrıca Bölüm 31'deki çerçeve okuyucusunun parçalı okumada doğru çalıştığını, Bölüm 30'daki sunucunun ise her girdide tek bir yanıt yazdığını (kapanmadan) doğrulayan iki özel test içerir.

**Önerilen yaklaşım (ipucu):** Mutasyon fonksiyonunu küçük, ayrı ve test edilebilir bir modül olarak tut. En kısa örneği bulmak için basit bir küçültme (her seferinde bir parça silip hatanın hâlâ oluşup oluşmadığına bakma) yeterlidir; bu, kapsama yönlendirmeli bir araç değildir ama fikri anlamanı sağlar. Sonuçları CSV olarak yazan bir çıktı üret ve bu çıktıyı önceki çalışmalarla karşılaştır; böylece bir değişikliğin hata sayısını artırıp artırmadığını görürsün.

**Başarı kriterleri:**
- Çatı, bu bölümdeki özgün Bölüm 30 sunucusunda hatayı bulur ve sağlamlaştırılmış sürümde sıfır hata verir.
- Her bulunan hata için en kısa yeniden üretici dosyaya yazılır ve tek başına çalıştırıldığında aynı istisnayı üretir.
- Aynı tohumla iki çalıştırma bit bit aynı sonucu verir.
- Yeni bir hedef eklemek, mevcut hedeflerin kodunda değişiklik gerektirmez.

### Ek Alıştırmalar

Aşağıdaki problemlerin çözümü bu kitapta yok. Önce kâğıda, sonra editöre geç; yapay zekâ yasak. Zorluk etiketine göre sırala.

1. **★ — Çığ etkisi.** 8 bitlik bir girdinin her bitini tek tek değiştirip 8 farklı çıktı üretiyorsun. Çıktılar arasındaki ortalama farkın 4 bit olması, bir hash için neden yeterli değildir? Bu ölçümün sana neyi söyleyip neyi söylemediğini yaz.
2. **★ — Tuz.** İki kullanıcı aynı parolayı kullanıyor, ama tuzları aynı. Saldırgan veritabanı sızıntısından ne öğrenir? Tuzun tekrar kullanılmaması neden önemlidir?
3. **★ — Sabit zamanlı karşılaştırma.** `==` ile iki baytlık bir etiket karşılaştırmasında, ilk baytı yanlış olan bir etiket ile son baytı yanlış olan bir etiket aynı sürede mi döner? Bunun ölçülebilir bir fark yaratması için hangi koşullar gerekir?
4. **★★ — Nonce sayacı.** Bir sensör, AEAD nonce'unu bir sayaçtan üretiyor ve cihaz yeniden başlayınca sayaç sıfırlanıyor. Bu tasarım neden tehlikelidir ve düzeltme için iki yol öner.
5. **★★ — Tekrar oynatma penceresi.** Bir protokolde, sıra numarasının "pencere" içinde olan ama daha önce görülmemiş paketleri kabul etmek istiyorsun (kayıplı bir ağ için). Son gördüğün sıradan geriye doğru 64 paketlik bir pencere tanımla; pencerenin dışındaki bir paketi nasıl reddedersin?
6. **★★ — Kanarya neyi koruyor?** Yığın kanaryası, dönüş adresinden önce bir değer koyar. Bu değerin tahmin edilemez olması neden gereklidir? Kanaryanın koruyamadığı bir hata sınıfı var mı?
7. **★★ — Çerez kapsamı.** `Path=/admin` çerezi, `/admin/sil` yolunda gönderilir mi? `Path` bayrağı bir güvenlik sınırı mıdır? Cevabını yaz ve neden olduğunu açıkla.
8. **★★ — Yol normalleştirme.** Bir dosya sunucusu, istek yolunu `os.path.normpath` ile normalleştirip kök dizinin altında olup olmadığını `startswith` ile kontrol ediyor. Bu kontrolü geçen ama kökten çıkan bir yol tasarlayabilir misin? (Yalnızca kavramsal düzeyde yanıtla.) Düzeltme nedir?
9. **★★★ — Mülakat: boyut hesabı.** Bir fonksiyon `malloc(n * m)` ile iki boyutlu bir matris ayırıyor. `n` ve `m` kullanıcıdan geliyor. Bu hatayı ASan ve UBSan ile nasıl yakalarsın, düzeltmesi ne olur? (Mülakat)
10. **★★★ — Mülakat: parola saklama.** Bir ekip SHA-256'yı tuz ile birlikte kullanıyor ve "yeterince güvenli" diyor. Hangi üç ölçüt bunun yetersiz olduğunu gösterir? Bir kullanıcı yeni parola kurarken sistemin ne yapması gerekir? (Mülakat)
11. **★★★ — Mülakat: CSRF.** Bir API `POST /sil` isteğini yalnızca çerezle kimlik doğrular ve SameSite bayrağı yoktur. Bu API'ye karşı hangi saldırı yapılabilir, hangi üç savunma uygulanabilir ve bunların hangisi tek başına yeterlidir? (Mülakat)
12. **★★★ — Mülakat: ASLR ve sızıntı.** ASLR açık bir sistemde, bir hata yalnızca bellek adresi bilindiğinde kullanılabiliyor. Bu bilgi bir sızıntıyla elde edilirse hangi koruma bu durumu tek başına engeller? Hangi katmanlar hâlâ işe yarar? (Mülakat)

## Kod Okuma Egzersizi

Aşağıdaki kesitler, Python 3.12.10 standart kütüphanesinden alınmıştır. Kaynak yerel kurulumdan alındı ve resmi `v3.12.10` etiketindeki `Lib/secrets.py` ile satır satır aynıdır. `Lib/hmac.py` kesiti de aynı yerel kurulumdan alındı; birebir kopyadır, kısaltma yoktur.

Birinci kesit, `secrets.py` dosyasının içe aktarma satırlarıdır (17–18 ve 20). `compare_digest` fonksiyonu `hmac`'ten alınır; rastgele kaynak olarak `SystemRandom` seçilir.

@@SRC C:/Users/merty/AppData/Local/Programs/Python/Python312/Lib/secrets.py 17 20@@

İkinci kesit, jeton üreten `token_bytes` fonksiyonudur (33–45).

@@SRC C:/Users/merty/AppData/Local/Programs/Python/Python312/Lib/secrets.py 33 45@@

Üçüncü kesit, `hmac.py` dosyasının `compare_digest` sağlayıcısını seçen bloktur (6–15).

@@SRC C:/Users/merty/AppData/Local/Programs/Python/Python312/Lib/hmac.py 6 15@@

**Sorular — cevaplamadan geçme:**

1. `token_bytes` `random.SystemRandom` nesnesinin `randbytes` metodunu çağırıyor. `SystemRandom` sınıfı rastgele baytları hangi kaynaktan alır? Bu kaynağın `random.Random` ile farkı nedir ve bunu `random` modülünün belgesinden doğrula.
2. `hmac.py`, `compare_digest` için iki yol tanımlıyor: `_hashlib` (OpenSSL) ya da `_operator` yedeği. Yedek yol neden vardır ve iki yolun da aynı güvenlik özelliğini taşıdığını nasıl kontrol edersin?
3. `token_urlsafe` sonuna `rstrip(b'=')` ekliyor. Base64 dolgusu (padding) neden jeton için gereksizdir ve bu işlem, çözümlemede hangi varsayımı değiştirir?
4. `token_bytes` varsayılan uzunluk olarak `DEFAULT_ENTROPY` kullanıyor. Bu sabit, bir jetonun gücü için neden tek başına bir ölçü değildir? Bölüm 32.3'teki tohum deneyiyle ilişkilendir.
5. `secrets` modülü `choice` ve `randbits`'i `_sysrand` üzerinden tanımlıyor. Bu tanımların `random.choice` ile aynı kaynağı kullanmadığını göstermek için hangi tek satırlık deneyi yaparsın?
6. `hmac.py`'deki `trans_5C` ve `trans_36` tabloları neden 256 elemanlıdır ve bunlar RFC 2104'teki hangi sabitlere karşılık gelir? Tabloların her girişinin neden tek tek hesaplandığını açıkla.

## Bölüm Özeti

- Güvenlik, tasarımın ilk gününden başlar. CIA üçlüsü, kimlik doğrulama, yetkilendirme ve inkâr edilemezlik birlikte bir hedef tanımlar; STRIDE ise her tehdidi bir özelliğe bağlar.
- Kendi kriptografik algoritmanı yazma. Hash'in çığ etkisi ölçülür; parola saklamada hız bir risktir, tuz ve yavaş bir KDF (scrypt) gerekir.
- CRC bir hata algılama kodudur, bütünlük değildir. HMAC anahtarlı bütünlük sağlar; sıra numarası ile tekrar oynatma engellenir ve karşılaştırma sabit zamanlı yapılır.
- AEAD şifrelemeyi ve doğrulamayı birlikte yapar; nonce tekrarı felakettir. İmza, anahtar yönetimiyle birlikte düşünülmelidir.
- TLS, sertifika zinciriyle kimliği ve geçici anahtar paylaşımıyla gizliliği sağlar. `verify=False` kimlik kısmını yok eder.
- C'de tampon taşması, serbest bırakılmış bellek, çift serbest bırakma, tamsayı taşması ve biçim dizesi hataları ASan, UBSan ve `-fanalyzer` ile görünür kılınır; düzeltmeler sınırı açıkça denetler.
- Derleyici ve işletim sistemi korumaları (kanarya, FORTIFY, NX, ASLR, PIE, RELRO) bir hatayı düzeltmez, kötüye kullanımını zorlaştırır. Hiçbiri tek başına yeterli değildir.
- Fuzzing, sözleşmeleri hedef bazında tanımlanmış bir mutasyon testidir. Bölüm 30 sunucusundaki tek baytlık hata, sözleşmenin ve sınıflandırmanın ne kadar önemli olduğunu gösterdi.

Bu bölümle Kısım VII, Ağ, tamamlandı. Bölüm 29'da katmanları, Bölüm 30'da HTTP ve DNS'i, Bölüm 31'de soketleri ve Bölüm 32'de güvenliği gördün. Bu dört bölüm, bir ağ uygulamasının baytlarından güvenliğine uzanan tek bir zincir kurar.

**Sonraki bölümde:** Bölüm 33 (İlişkisel Model) ile Kısım VIII, Veritabanı, başlıyor. Burada gördüğün güvenlik ilkeleri, veritabanına taşındığında da geçerlidir: en az ayrıcalık, parametreli sorgular ve bütünlük kısıtları. Veritabanı, verinin tutarlılığını ve güvenliğini bir şema düzeyinde sağlar.

::: mulakat
Aşağıdaki sorular cevapsızdır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. HMAC ile `H(anahtar ∥ mesaj)` biçiminde basit bir birleştirme arasındaki fark nedir? Neden HMAC'in iç içe yapısı gerekir?
2. Parola saklamada neden hızlı bir hash yetmez? Tuz neyi çözer ve neyi çözmez?
3. AEAD'de aynı anahtarla nonce'un iki kez kullanılması neden felakettir? Bu hatayı tasarımda nasıl önlersin?
4. TLS 1.3'te sertifika doğrulaması ile anahtar paylaşımı birbirinden nasıl ayrılır? İleriye dönük gizlilik ne demektir ve neden önemlidir?
5. `strncpy` neden güvenli bir kopya fonksiyonu sayılmaz? Hedef bir dizinin sonlandırılması için hangi koşul gerekir?
6. ASLR açıkken bir bellek hatası hâlâ kötüye kullanılabilir mi? Bu soruyu, koruma katmanlarının birbirini nasıl tamamladığını da kullanarak yanıtla.
7. Tek bir kötü biçimlendirilmiş istekle tüm bir sunucu nasıl durabilir? Bu hatayı fuzzing ile nasıl bulursun ve sözleşmeyi nasıl tanımlarsın?
8. Bir koruma açık, ama başka bir koruma kapalı: NX açık, PIE kapalı. Hangi risk kalır ve bunu azaltmak için hangi adımları atarsın?
:::
