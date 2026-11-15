## 32.7 Girdi doğrulama ve enjeksiyon

Bölüm 31'de ağdan gelen her baytın düşman olabileceğini söyledik. Bu cümlenin pratik sonucu şudur: **güvenilmeyen girdi, kodun veri değil komut olarak yorumlanmasına izin vermemelidir**. Enjeksiyon saldırılarının tamamı tek bir hatadan doğar: veri ile komut, aynı metin içinde karışır ve hedef yorumlayıcı (kabuk, SQL motoru, tarayıcı, dosya sistemi) veriyi komut sanır.

Savunma üç adımdan oluşur ve bu sırayla düşünülmelidir. **Doğrula**: girdinin beklenen biçimde olup olmadığını kontrol et; mümkünse izin verilenleri listele (allowlist), yasaklılarını değil. **Ayır**: komutu ve veriyi ayrı kanallardan geçir (parametreli sorgu, argüman listesi). **Kaçır**: veri kaçınılmazsa, çıktı bağlamına uygun biçimde kaçır (HTML için HTML kaçışı, URL için URL kodlaması). Bu üç adımın birinin yerine diğerini koymak, çoğu zaman yetersiz kalır.

### Komut enjeksiyonu

Bir programın harici bir komutu çağırırken girdiyi kabuğa metin olarak verdiğini düşün. Kabuk, bu metni komut satırı gibi ayrıştırır; `&`, `;`, `|` gibi karakterler yeni komutlar başlatır. Python'da bu, `subprocess.run(..., shell=True)` ile olur. Girdi liste olarak verildiğinde ise kabuk devreye girmez ve girdi tek bir argüman olarak kalır.

Aşağıdaki deneyde girdi `merhaba & echo ENJEKTE` olarak verilir. Yazdırma komutu zararsızdır; amaç, ikinci bir komutun çalıştığını görmektir.

@@KOD b32_girdi.py 24 35@@

@@TERMW§python b32_girdi.py komut§python b32_girdi.py komut@@

Çıktı farkı net gösterir. Liste biçiminde `&` ve `echo` karakterleri düz metin olarak yazdırılır. `shell=True` ile çalıştırıldığında ise ikinci komut ayrı bir çıktı olarak çalışır: `ENJEKTE` yazısı, girdinin komut olarak yorumlandığının kanıtıdır. Kural: harici bir program çağırırken her zaman argüman listesi kullan, kabuğu hiçbir koşulda girdi işleme aracı olarak kullanma.

::: ipucu
Kabuk gerçekten gerekirse, POSIX sistemlerde `shlex.quote` ile her argümanı tek tırnağa alabilirsin. Windows'ta kabuk (`cmd`) farklı tırnak kurallarına sahiptir; bu yüzden orada en güvenli yol yine argüman listesidir.
:::

### Yol geçişi (path traversal)

Kullanıcının verdiği bir dosya adını bir kök dizinin altına eklemek, bir saldırganın `../` dizilerini kullanarak kök dizinin dışına çıkmasına izin verebilir. Bu, Bölüm 30'daki HTTP sunucusunda da tam olarak bu riskti. Yol normalleştirme (`normpath`) tek başına yeterli değildir: sembolik bağlar, Windows sürücü harfleri ve NUL baytı gibi durumlar ayrı ele alınmalıdır.

Sağlam yaklaşım üç adımdır. Önce yolu, sembolik bağları çözen `realpath` ile gerçek bir yola çevir. Sonra kök dizinin de gerçek yolunu al. Son olarak `commonpath` ile sonucun kök dizinin altında olduğunu doğrula. `commonpath` farklı sürücüler için bir hata fırlattığından, bunu da yakalamalısın.

@@KOD b32_girdi.py 38 56@@

Üç yolu karşılaştıran tablo, naif birleştirmenin nerede kırıldığını gösterir. Deneyde kök dizini geçici bir klasördür.

@@TERMW§python b32_girdi.py yol§python b32_girdi.py yol@@

Naif sütunda `KOKTEN` yazan satırlar, dosyanın kök dizinin dışına çıkacağı anlamına gelir. Güvenli sütun bu durumları reddeder. NUL baytı içeren yolun naif sürümde kök içinde kaldığına dikkat et: bu, güvenlik için yeterli değildir; NUL baytını ayrıca reddetmek, dosya sistemi API'lerinin farklı davranışlarından doğan belirsizliği önler.

Sembolik bağ senaryosunu Windows'ta bu deneyde üretemedik (bağ oluşturmak yönetici hakkı ister). Kavramsal olarak şöyledir: kök dizinin içinde görünen bir bağ, dışarıdaki bir dosyaya işaret edebilir. `normpath` bağı çözmez, bu yüzden kök kontrolünü geçer; `realpath` ise bağı çözer ve kontrol bunu yakalar. Bölüm 32.8'de düzelttiğimiz sunucu bu ayrımı kullanır.

### HTML kaçışı ve çapraz site betiği (XSS)

Bir web sayfasına kullanıcı verisi yazılırken, veri HTML olarak yorumlanırsa, veri içindeki `<script>` etiketi çalışır. Buna **çapraz site betiği** (cross-site scripting, XSS) denir. Çözüm, çıktı bağlamına uygun kaçıştır: HTML metni için `<`, `>`, `&`, `"` ve `'` karakterleri karşılık gelen varlıklara çevrilir. `html.escape` bu iş için yeterlidir; `quote=True` ile tırnaklar da kaçırılır, böylece öznitelik değerleri içinde de güvenlidir.

@@KOD b32_girdi.py 59 60@@

@@TERMW§python b32_girdi.py html§python b32_girdi.py html@@

Kaçışın bağlama özgü olduğunu unutma. Bir JavaScript bloğunun içine ya da bir URL'nin içine yazılan veri için HTML kaçışı yetmez; her bağlamın kendi kodlaması vardır. Ek olarak İçerik Güvenlik Politikası (CSP) gibi tarayıcı katmanı savunmaları, XSS'in etkisini sınırlar (genel bilgi).

### SQL enjeksiyonu

SQL enjeksiyonu, sorgunun metin birleştirmeyle kurulmasından doğar ve kendi bölümünde ayrıntılı işlendi (bkz. Bölüm 34, SQL enjeksiyonu anlatımı). Burada tek kural yeter: değer her zaman **parametre** olarak bağlanır; sorgu metni ise sabit olur. Tablo ya da sütun adları parametreyle bağlanamaz; bunlar için izin verilen adların bir listesini kullan. Bölüm 34'te görülen `ORDER BY` örneği, bu sınırın pratik bir sonucudur.

### Deserializasyon ve pickle

Bir nesneyi bayt dizisine çevirmek (serileştirme) ve geri okumak (deserializasyon), ağ protokollerinin ve dosya biçimlerinin olağan parçasıdır. Ama Python'un `pickle` modülü, veriyi okurken nesne oluşturucularını çağırabilir. Yani güvenilmeyen bir kaynaktan gelen `pickle` verisi, deserializasyon sırasında kod çalıştırabilir. Bu yüzden `pickle.loads` güvenilmeyen veri üzerinde kullanılmaz.

Kural basit: dış dünyadan gelen veri için yalnızca veri tiplerini okuyan biçimleri kullan. JSON bunun bir örneğidir: `json.loads` yalnızca sözlük, liste, sayı, metin, bool ve `null` üretir ve nesne oluşturucusu çağırmaz. Başka bir biçim gerekiyorsa, veriyi açmadan önce bir HMAC ile doğrula (32.3). Diğer dillerdeki serileştirme kütüphaneleri de benzer riskler taşır (genel bilgi).

### Uzunluk alanına körü körüne güvenmemek

Bölüm 31'deki uzunluk önekli çerçevede, alıcı 4 baytlık bir uzunluk okur ve o kadar bayt bekler. Uzunluk alanı, saldırganın kontrolündedir. Bu alanın değerini bellek ayırmadan önce bir üst sınırla karşılaştırmak zorunludur (Bölüm 31.4'teki `MAKS`). Aynı ilke, HTTP başlık satırlarının uzunluğu için de geçerlidir: Bölüm 30'daki sunucu `MAKS_BASLIK` ile sınırlar. Sayısal girdilerde de benzer biçimde, değer aralığını ve türünü ayrıştırmadan önce denetle.

## 32.8 Kendi kodunda hata avı: fuzzing, statik analiz ve canlı test

Birim testleri, bildiğimiz davranışları doğrular. Fuzzing ise bilmediğimiz hataları arar. Bir fuzzer, hedef fonksiyona çok sayıda girdi verir; bu girdiler mevcut örneklerin **mutasyonu** ile üretilir: bir bayt değişir, bir parça silinir, bir parça tekrar eder, özel karakterler eklenir. Her girdi için hedefin davranışı izlenir ve bir **sözleşme** ihlali (beklenmeyen istisna, çökme, sanitizer hatası) aranır.

Üç kavram bu işin çekirdeğidir. **Sözleşme**, hedefin hangi girdide hangi istisnayı fırlatabileceğini belirtir: çerçeve okuyucusu bozuk girdide `ValueError` fırlatabilir, ama bir bağlantı işleyicisi hiçbir istemci girdisinde istisna sızdırmamalıdır. **Sabit tohum**, aynı deneyin her çalıştırmada aynı girdileri üretmesini sağlar; bu sayede bulunan bir hata tekrar üretilebilir. **En kısa yeniden üretici**, bulunan hatayı tetikleyen en küçük girdidir ve hatanın nedenini anlamayı kolaylaştırır.

![Şekil 32.10: Fuzzing döngüsü. Mutasyon, hedefi çalıştırma, sözleşme denetimi, en kısa örneğin saklanması ve düzeltme sonrası yeniden çalıştırma adımlarından oluşur.](gorseller/b32_fuzz.png)

### Fuzzer'ımız

Aşağıdaki çatı, dört hedefi aynı mutasyon motoruyla sınar: Bölüm 31'deki çerçeve okuyucusu, Bölüm 31'deki CRC'li telemetri çözücüsü, bu bölümdeki HMAC alıcısı ve Bölüm 30'daki HTTP sunucusunun bağlantı işleyicisi. Her hedefin sözleşmesi ayrıdır; bu ayrım önemlidir, aşağıda neden olduğunu göreceksin.

@@KOD b32_fuzz.py 72 96@@

Mutasyon fonksiyonu, seçilen bir tohumu rastgele bir işlemle değiştirir. Yedinci dal, başka bir tohumdan parça alır; böylece geçerli bir çerçevenin başı ile bozuk bir gövde birleşebilir. Bu, gerçek ağ trafiğinde görülen karışımları taklit eder.

@@KOD b32_fuzz.py 98 120@@

Test döngüsü, her girdiyi hedefe verir. Sözleşmedeki istisnalar sessizce geçilir; diğer her istisna sayılır ve en kısa örnekle birlikte saklanır. Bu tasarımın kritik bir noktası var: `beklenen` demeti, hedef bazında ayrı verilir. HTTP hedefinde bu demet boştur; yani bağlantı işleyicisi hiçbir girdide istisna fırlatmamalıdır.

### Bulgu: Bölüm 30 sunucusu bir baytla düşüyor

Özgün Bölüm 30 sunucusunu, yalnızca kopyalayıp fuzzer'a verdik. Hiçbir kod değiştirmedik. Önce fuzzer'ı çalıştıralım.

@@TERMW§python b32_fuzz.py ham§python b32_fuzz.py ham@@

Çıktı, 20 000 denemenin 1770'inde HTTP hedefinin beklenmeyen bir `ValueError` fırlattığını söyler. En kısa yeniden üretici, `POST` isteğinin yöntem alanında tek bir `0xAD` baytı olan bir istektir. Çerçeve okuyucusu ve telemetri çözücüsü ise sıfır hata verdi; bunu da kaydetmeliyiz. Bu sonuç bir kanıt değil, bu girdi uzayında bulunamamış bir hatadır.

Hatanın nedenine bak. Bölüm 30 sunucusunun `istek_oku` fonksiyonu, istek satırını `ascii` olarak çözer. 0xAD gibi bir bayt bu çözmeyi `UnicodeDecodeError` ile durdurur. Bu istisna bir `ValueError` alt sınıfıdır. Sunucunun `baglanti_isle` fonksiyonu, `ValueError`'u bir HTTP durum kodu sanarak `int(e.args[0])` çağırır. Bu çağrı, `e.args[0]`'ın değeri `'ascii'` olduğu için kendisi de bir `ValueError` fırlatır ve bu istisna hiçbir yerde yakalanmadan dışarı çıkar.

@@KOD b32_http_ham.py 99 113@@

Sunucunun ana döngüsü `baglanti_isle` çağrısını hiçbir `try` bloğu içinde yapmaz. Bu nedenle istisna, süreci sonlandırır. Sunucu tek süreçli olduğu için, tek bir kötü biçimlendirilmiş istek tüm hizmeti durdurur. Bu bir **hizmet reddi** (DoS) hatasıdır ve STRIDE tablosundaki D (denial of service) sınıfına girer.

Bu hatanın canlı bir sunucuda da olduğunu doğrulayalım. `b32_canli.py`, iki sunucuyu yalnızca `127.0.0.1` üzerinde başlatır, aynı kötü isteği gönderir ve sonra iyi bir istek dener.

@@TERMW§python b32_canli.py§python b32_canli.py@@

Özgün sunucu, kötü isteğe yanıt vermeden çıkar ve çıkış kodu 1 ile hata mesajını yazar. Sağlamlaştırılmış sürüm aynı isteğe `400 Bad Request` döner ve sonraki iyi isteğe `200 OK` ile yanıt verir. Bu fark, hatanın yalnızca bir fuzzer sonucu olmadığını, gerçek bir süreçte de yıkıcı olduğunu gösterir.

Fuzzer'ın bu hatayı ilk seferde neden kaçırdığı da öğreticidir. İlk sürümümüzde `ValueError` tüm hedeflerde "beklenen red" sayılıyordu. Bu nedenle `UnicodeDecodeError`'dan türeyen `ValueError` da sessizce geçiliyordu ve sayaç sıfır gösteriyordu. Sözleşmeyi hedef bazında ayırmak, bu tür maskelemeyi önler. Kural: beklenen istisnayı yalnızca sınıf olarak değil, hedefin kendi tanımladığı bir sözleşme olarak belirt.

### Düzeltme: sağlamlaştırılmış sunucu

Düzeltmenin üç parçası vardır ve her biri ayrı bir savunma katmanıdır. Birincisi, ayrıştırma hataları bir `HttpHata` istisnası ile durum koduna bağlanır; durum kodu bir `int` olarak istisnanın içinde taşınır ve hiçbir yerde metinden sayıya çevrilmez. Her ASCII çözme adımı da `_ascii` yardımcısından geçer ve hata 400'e dönüşür.

@@KOD b32_http_sag.py 30 43@@

İkincisi, yol denetimi gerçek yol üzerinde yapılır. Bu, 32.7'de anlattığımız üç adımın bu sunucudaki uygulamasıdır.

@@KOD b32_http_sag.py 74 91@@

Üçüncüsü, ana döngü her bağlantıyı ayrı bir `try` bloğuyla korur. Bu, birinci katmanın kaçırdığı bir hata olursa bile, sunucunun çalışmaya devam etmesini sağlar. Bu bir yama değil, bir **savunma derinliği** katmanıdır: asıl düzeltme birinci katmandadır, ama ikinci katman, birincinin unuttuğu durumda hizmeti sürdürür.

@@KOD b32_http_sag.py 161 168@@

Düzeltilmiş sunucuyu aynı fuzzer ile yeniden çalıştırıyoruz. Sözleşmenin aynı olduğuna dikkat et: yalnızca kod değişti, test değişmedi.

@@TERMW§python b32_fuzz.py sag§python b32_fuzz.py sag@@

Sayım sıfır. Bu, bu deney tasarımı ve bu girdi uzayı için bir sonuçtur; bir ispat değildir. Tablo, iki sürümün ve dört hedefin karşılaştırmasını verir.

@@CSV b32_fuzz_olcum@@

Tabloda Bölüm 31'in çerçeve ve telemetri hedeflerinin sıfır hata verdiğini görüyorsun. Bu iyi bir haberdir; ama fuzzer'ın bulamadığı bir hatanın yokluğunu kanıtlamaz. Fuzzing, kapsamını bildiğin girdiler için bir kanıt üretir; kapsam dışı girdilerde sessiz kalır.

### Statik analiz: derleyici de hata arayabilir

Bir hata, çalıştırılmadan da görülebilir. `-fanalyzer`, derleyicinin içinde çalışan bir analiz motorudur: fonksiyonlar boyunca bir işaretçinin durumunu izler ve serbest bırakılmış bellek ile çift serbest bırakmayı çoğu zaman yakalar. Bölüm 32.5'teki iki hatalı programı bu motorla tarayalım.

@@TERM§gcc -fanalyzer -Wall -std=c11 -c b32_c2_hatali.c§gcc -fanalyzer -Wall -std=c11 -c b32_c2_hatali.c -o /dev/null 2>&1 | grep 'warning' | fold -w 74@@

@@TERM§gcc -fanalyzer -Wall -std=c11 -c b32_c3_hatali.c§gcc -fanalyzer -Wall -std=c11 -c b32_c3_hatali.c -o /dev/null 2>&1 | grep 'warning' | fold -w 74@@

Uyarılar, ASan'ın çalışma zamanında gösterdiği hataları derleme zamanında işaretler: `use after 'free'` ve `double-'free' of 'p'`. Statik analizin sınırı da burada görünür: aynı analiz, `c1_hatali.c`'deki yığın taşmasını bu sürümde yakalamadı (uyarı çıkmadı). Bu yüzden statik analiz, sanitizer ve fuzzing'in yerini almaz; üçü birlikte kullanılır.

### Fuzzing ve sanitizer birlikte

Python fuzzer'ı, C kodunun bellek hatalarını ASan ile birlikte yakalamaz; çünkü bir Python süreci kendi belleğini yönetir. C kodu için gerçek bir fuzzing'de, hedef fonksiyonu ASan ve UBSan ile derleyip kapsamı yönlendiren fuzzer'lar (AFL++, libFuzzer; genel bilgi) kullanılır. Bu kitapta bu araçları kurmadık; ama ilke aynıdır: girdiyi rastgele üret, hedefi sanitizer altında çalıştır, bulunan en kısa örneği sakla.

Bölüm 31'deki ayrıştırıcıları yeniden düşün: bir uzunluk alanı, bir sınır denetimi ve bir sıra numarası. Bu üç alanın her biri, fuzzing için bir hedef yüzeyidir. Bir sonraki adımda bu yüzeyi sistematik olarak kapatmayı kendin deneyeceksin (Kendin Yap, Proje 2).

::: dikkat
Fuzzing'i yalnızca kendi kodunda ve yalnızca kendi kontrolündeki sistemlerde çalıştır. Üçüncü taraf bir hizmete yönelik istekleri, izinsiz bir tarama olarak yorumlanabilir ve hukuki sonuçları olabilir.
:::

## 32.9 Web, oturum ve kimlik

Bölüm 30'da çerezlerin ve oturumların HTTP'ye nasıl eklendiğini gördün ve bu konunun güvenlik kısmını bu bölüme bıraktık. Oturum tasarımında temel fikir şudur: tarayıcıda yalnızca **tahmin edilemez bir oturum kimliği** tutulur; kullanıcının durumu, yetkileri ve verileri sunucudadır. Çerezi çalmak, o oturumu devralmak demektir; bu yüzden çerezin korunması bir güvenlik gereksinimidir.

### Çerez bayrakları

Bir çerezin davranışı birkaç bayrakla belirlenir. **HttpOnly** çerezi JavaScript'in okuyamamasını sağlar; bir XSS açığının çerezi doğrudan sızdırmasını engeller. **Secure** çerezin yalnızca HTTPS üzerinden gönderilmesini sağlar. **SameSite** (Lax, Strict ya da None) çerezin çapraz site isteklerde ne zaman gönderileceğini belirler. **Max-Age** ve **Path** süreyi ve kapsamı sınırlar. Aşağıdaki kod, bu bayrakları ayarlayan bir `Set-Cookie` satırı üretir.

@@KOD b32_web.py 11 19@@

@@TERMW§python b32_web.py§python b32_web.py@@

Çıktıdaki `Set-Cookie` satırı, sekiz bayrağın hepsinin doğru yazıldığını gösterir. Oturum kimliği `secrets.token_urlsafe(32)` ile üretilir: 256 bit rastgelelik, kayıt tahmin edilemezlik sağlar.

### CSRF: sahte istekler

**Çapraz site istek sahteciliği** (Cross-Site Request Forgery, CSRF), kullanıcının tarayıcısının, oturum çerezi ile birlikte, kullanıcının bilmediği bir isteği hedef siteye göndermesidir. Tarayıcı, hedef siteye giden her isteğe ilgili çerezleri otomatik ekler; saldırgan sayfası kullanıcıdan bir işlem yaptırabilir. Savunma, isteğin gerçekten kendi sayfandan geldiğini kanıtlamaktır: formda gönderilen ve sunucuda oturumla eşleştirilmiş bir **CSRF jetonu**. Saldırgan sayfası bu jetonu okuyamaz (aynı köken politikası), bu yüzden jetonu içeren bir istek üretemez.

@@KOD b32_web.py 22 29@@

Jetonun karşılaştırması da sabit zamanlı yapılır (32.3). SameSite çerezi ek bir katmandır, ama tek başına yeterli değildir: eski tarayıcılar ve bazı yönlendirme senaryoları için jeton hâlâ gereklidir. Durum değiştiren her işlem (`POST`, `PUT`, `DELETE`) CSRF jetonu ister; `GET` yalnızca okuma içindir ve durum değiştirmemelidir.

### Parola politikası, çok faktörlü doğrulama ve federasyon

Parola saklamayı 32.2'de gördük; burada politika tarafını ekliyoruz. NIST SP 800-63B, parolalarda uzunluğu, yasaklı parolaların taranmasını ve periyodik zorunlu değişikliği yerine gereksiz yere karmaşık kuralların kaldırılmasını önerir (genel bilgi). **Çok faktörlü doğrulama** (MFA), bilgi (parola), sahiplik (telefon, güvenlik anahtarı) ve biyometri gibi bağımsız faktörlerden en az ikisini ister. Bir faktörün sızması, tek başına hesabı ele geçirmeye yetmez.

**OAuth 2.0** bir yetki devri çerçevesidir: kullanıcı, bir uygulamanın kendi verilerine belirli kapsamlarla erişmesine izin verir. **OpenID Connect** bunun üzerine bir kimlik katmanı ekler ve kullanıcının kimliğini bir kimlik sağlayıcısı üzerinden doğrular. Bu iki standart ayrıntılı bir konudur ve bu kitabın kapsamı dışındadır; ama farkı bilmek önemlidir: OAuth "bu uygulama neye erişebilir" sorusunu, OIDC "bu kullanıcı kimdir" sorusunu yanıtlar.

::: dikkat
JWT gibi imzalı belirteçleri kabul ederken imzanın doğrulandığından ve algoritmanın sunucu tarafında sabitlendiğinden emin ol. İmza doğrulamayan ya da algoritmayı belirteçten okuyan kütüphaneler, saldırganın kendi belirteçlerini kabul ettirmesine izin verir. Bu, kütüphane seçiminin ve yapılandırmanın doğrudan güvenlik kararı olduğunun bir örneğidir.
:::

## 32.10 Güvenli yazılım süreci ve savunma sanayii bağlamı

Bu bölümde gördüğümüz tekniklerin hiçbiri tek başına bir sistemi güvenli yapmaz. Güvenlik, kodun yazıldığı, test edildiği, dağıtıldığı ve izlendiği süreçlerin toplamıdır. Bu alt bölümde, bu sürecin en önemli parçalarını ve savunma sanayiinde bunların nasıl ele alındığını özetliyoruz.

### Bağımlılık güvenliği

Projenin kullandığı her kütüphane, senin saldırı yüzeyinin parçasıdır. Üç ilke bu riski azaltır. **Sürüm sabitleme**: `requirements.txt` içinde her bağımlılığın tam sürümü yazılır; "en son sürüm" beklentisi, bir gün bir kötü amaçlı ya da hatalı sürümü otomatik olarak kurmana yol açabilir. **Hash doğrulama**: `pip install --require-hashes` ile her paketin özeti, kurulumdan önce kontrol edilir (pip özelliği; genel bilgi). **Bağımlılık envanteri**: hangi bileşenin hangi sürümde olduğunu bilmek, bir güvenlik bülteni çıktığında etkilenen sistemleri dakikalar içinde bulmanı sağlar. Bu envantere yazılım malzeme listesi (SBOM) denir (genel bilgi).

### Sırları koda gömmemek

Parolalar, API anahtarları ve özel anahtarlar koda, yapılandırma dosyasına ya da depoya girmemelidir. Yerel geliştirmede ortam değişkeni kullanılır ve bu değişken gösterilen dosyalar (`.env` gibi) `.gitignore` ile depodan dışlanır. Üretimde bir sır kasası (secret manager) veya donanım güvenlik modülü tercih edilir. Bir sır bir kez depoya girdiyse, silinse bile sızmış sayılır: git geçmişi onu tutar. Doğru tepki, sırrı derhal iptal edip yenilemektir; geçmişi yeniden yazmak yalnızca ek bir adımdır.

### Güvenlik günlüğü

Güvenlik günlüğü, bir olay olduğunda neyin olduğunu sonradan anlamanı sağlar. Kaydedilmesi gerekenler: başarısız giriş denemeleri, yetki reddleri, yapılandırma değişiklikleri ve yönetici işlemleri. Kaydedilmemesi gerekenler: parolalar, oturum kimlikleri, tam kişisel veri ve sırlar. Günlüğün değiştirilemez olması bir gereksinimdir: kayıtlar yalnızca eklenebilir (append-only) olmalı ve tercihen her kaydın özeti bir öncekine HMAC ile bağlanmalıdır (32.3). Böylece bir saldırgan iz bırakmadan kayıt silemez; bu, inkâr edilemezliğin uygulamadaki karşılığıdır.

### Sorumlu açıklama

Bir güvenlik açığı bulduğunda, ilk adım onu kamuya açıklamak değil, sorumlu tarafa (yazılımın sahibine ya da üreticisine) gizlilik içinde bildirmektir. Yaygın bir pratik, sorumlu tarafa bir düzeltme için makul bir süre tanımak ve bu süre dolmadan kamuya açıklamamaktır. Bu süreler sektörde ve kuruluşlarda farklıdır (genel bilgi). Yazılım mühendisi olarak, kendi projene gelen bildirimleri bir kanal üzerinden alabilecek ve yanıtlayabilecek şekilde hazır olmalısın.

### Savunma sanayiinde standartlar ve sertifikasyon

Savunma ve havacılık yazılımında güvenlik, bir tercih değil, bir sertifikasyon gereksinimidir. Bu bölümde adını andığımız standartlar, ayrıntılarına girmeden bilinmelidir (hepsi genel bilgi düzeyindedir). **Common Criteria** (ISO/IEC 15408), ürünlerin güvenlik özelliklerinin bağımsız olarak değerlendirilmesi için uluslararası bir çerçevedir. **DO-178C**, havacılık yazılımının geliştirme ve doğrulama süreçlerini tanımlar; güvenlik ve doğrulama kanıtları bu sürecin parçasıdır. **DO-326A**, havacılık sistemlerinde siber güvenlik için süreç gereksinimlerini içerir. **NIST SP 800 serisi**, kriptografi, kimlik ve sistem güvenliği için yaygın referans belgeleridir. Bu standartların ortak mesajı, güvenliğin ispatlanabilir olması gerektiğidir: "güvenliyiz" demek yetmez, kanıt gerekir.

Bu kanıt, bu bölümde yaptığımız deneylerin mantığına benzer: bir iddiayı (sözleşme, koruma, sertifika) ölçülebilir bir sonuçla (test, sanitizer raporu, fuzzing tablosu) desteklemek. Sertifikasyon süreçleri bu kanıtları daha büyük ölçekte ve bağımsız bir gözle ister. Doğrulama ve sertifikasyon ayrıntıları Bölüm 78'de yeniden ele alınacak.

### Yan kanal ve sabit zamanlı kod

Bölüm 32.3'te sabit zamanlı karşılaştırmayı gördük. Aynı mantık daha geniş bir alana uygulanır: bir işlemin süresi, önbellek davranışı ya da güç tüketimi, gizli bir değer hakkında bilgi taşıyabilir. Bölüm 24'teki Spectre ve Meltdown, bu fikrin işlemci düzeyindeki karşılığıdır: spekülatif yürütme, işlemci önbelleğinin zamanlamasını bir yan kanal olarak açığa çıkarır. Yazılım tarafında bu riskle başa çıkmanın yolu, gizli veriye bağlı dallanma ve bellek erişimlerinden kaçınan sabit zamanlı kodlar yazmaktır; ancak bu, donanım azaltımlarını (mikro kod ve işletim sistemi yamaları) ortadan kaldırmaz.

### Kontrol listesi

Aşağıdaki liste, bu bölümde gördüğümüz ilkeleri bir geliştirme sürecinde kontrol edilebilir maddeler hâline getirir. Her maddeyi bir kod incelemesinde sorabilirsin.

1. Her girdi noktasında (ağ, dosya, komut satırı, ortam değişkeni) veri sınırı ve biçimi denetleniyor mu?
2. Harici komutlar argüman listesiyle mi çağrılıyor?
3. Dosya yolları `realpath` ve kök dizin denetimiyle mi çözülüyor?
4. Kriptografik işlemler sınanmış bir kütüphaneyle mi yapılıyor; anahtarlar kodda değil mi?
5. Karşılaştırmalar gizli değerler için sabit zamanlı mı?
6. Derleme korumaları (kanarya, FORTIFY, NX, PIE, RELRO) açık ve bir CI adımıyla denetleniyor mu?
7. C kodu ASan ve UBSan altında test ediliyor mu; ayrıştırıcılar fuzzing'den geçiyor mu?
8. Bağımlılıklar sabit sürümlü ve hash doğrulamalı mı; sırlar depoda değil mi?

