%% kisim_no: II
%% kisim_ad: Problemi Çözmeyi Öğrenmek
%% bolum_no: 6
%% baslik: Debugging Sanatı

## Giriş: Asıl iş burada başlıyor

Bölüm 5'te problemi çözdün, kodu yazdın. Çalıştırdın. Çalışmadı.

Hoş geldin — mesleğin gerçek yüzü burası. Yaygın bir tahmine göre bir yazılım mühendisi mesai saatlerinin önemli bir kısmını (bazı tahminlere göre yarıya yakınını) *yeni kod yazarak* değil, **var olan kodun neden beklendiği gibi davranmadığını anlayarak** geçirir. Yani üniversitede en az öğretilen beceri, sahada en çok kullandığın beceridir.

Kötü haber şu: çoğu insan hata ayıklamayı hiç öğrenmez. Kodun içine rastgele `printf` serpiştirir, satırları karıştırır, "acaba burayı yorum satırı yapsam mı" der, Stack Overflow'da benzer hata mesajı arar. Bazen tutar. Tuttuğunda da *neden* tuttuğunu bilmez — ki bu, hiç çözememekten daha tehlikelidir, çünkü hata muhtemelen hâlâ oradadır, sadece saklanmıştır.

İyi haber şu: hata ayıklama **öğrenilebilir bir yöntemdir**. Sezgi değil, sistematiktir. Deneyimli mühendisin hatayı hızlı bulmasının sebebi daha zeki olması değil, **arama alanını disiplinli biçimde daraltmasıdır**. Bir dedektif gibi çalışır: kanıt toplar, hipotez kurar, sınar, eler. Bu bölümde o yöntemi kuracağız.

Yaklaşımımız Bölüm 5'in ikizi olacak — çünkü hata ayıklama da bir problem çözmedir; tek farkı, çözülecek problemin *senin kendi kodun* olması. Beş adımlı bir döngü öğreneceksin, sonra o döngünün her adımında kullanacağın araçları: `print`'ten `gdb`'ye, log'dan sanitizer'lara, `git bisect`'ten `assert`'e.

::: not
Bu bölüm `MertOS` için özellikle kritik. Bir işletim sistemi çekirdeğinde hata ayıklamak, normal bir programa göre kat kat zordur: hata ayıklayıcı takamazsın (çekirdek zaten en altta), `printf` bile her zaman çalışmaz, çökme genelde ekranı komple kilitler. O yüzden çekirdek geliştiricileri *savunmacı* çalışır: erken doğrulama, `assert`, panik mesajları, seri porttan log. 6.10'da bu zihniyeti kuracağız.
:::

## 6.1 Hata nedir: zihinsel model uyuşmazlığı

Önce tanımı düzeltelim, çünkü yanlış tanım yanlış arama demektir.

**Bir hata (bug), kodun yaptığı iş ile senin yaptığını sandığın iş arasındaki farktır.** Bilgisayar hata yapmaz; yazdığın şeyi harfiyen yapar. Uyuşmazlık koddadır değil, **kafandaki modeldedir**. Bu yüzden hata ayıklamanın özü şudur: *"kodun gerçekte ne yaptığını öğrenmek."* Kodu okurken gördüğün şey çoğu zaman yazdığın değil, yazmayı *niyet ettiğindir* — gözün eksiği tamamlar. Araçlar tam olarak bu yüzden vardır: sana gerçeği gösterirler.

Hataları tanımak için bir taksonomi işine yarayacak, çünkü **hata türü hangi aracı kullanacağını belirler**:

| Tür | Ne zaman ortaya çıkar | Tipik örnek |
|---|---|---|
| Sözdizimi / derleme | Derlemede | Eksik `;`, tanımsız isim |
| Bağlama (link) | Derlemenin sonunda | `undefined reference` (Bölüm 4) |
| Çalışma zamanı çökmesi | Program koşarken | Segfault, sıfıra bölme |
| Mantık hatası | Hiç — sessizce yanlış sonuç | Yanlış formül, birim hatası |
| Kaynak hatası | Zamanla birikerek | Bellek sızıntısı, açık kalan dosya |
| Eşzamanlılık | Rastgele, tekrarlanamaz | Yarış koşulu, kilitlenme |
| Tanımsız davranış (UB) | Bazen; derleyiciye göre değişir | Taşma, sarkan işaretçi |

Bu listede tehlike sırası aşağı indikçe artar. Derleme hatası en iyi hatadır: derleyici sana yerini ve türünü söyler, bedava. Çökme ikinci en iyisidir: en azından *bir şey olduğunu* bilirsin. **Asıl korkulması gereken, sessizce yanlış sonuç üreten mantık hatasıdır** — çünkü sistem "çalışıyor" görünür. Bir sensör okuma kodundaki birim hatası (metre yerine feet) programı çökertmez; sadece yanlış irtifa hesaplar. 1999'da NASA'nın Mars Climate Orbiter'ı tam olarak bu yüzden kaybedildi: bir modül pound-kuvvet·saniye (lbf·s), diğeri newton-saniye kullanıyordu. Kod çalıştı, uzay aracı yandı.

En alttaki iki satır ise mühendisliğin en zor bölgesidir; 6.8'de ayrıca ele alacağız.

## 6.2 Beş adımlı döngü

İşte hata ayıklamanın çerçevesi:

![Şekil 6.1: Hata ayıklama döngüsü. Beş adım sırayla ilerler; hipotez çürüdüğünde ya da düzeltme tutmadığında başa dönülür — ama artık daha çok kanıtla. Adım 1 atlanamaz: tekrar üretemediğin hatayı düzelttiğini kanıtlayamazsın.](gorseller/b06_cycle.png)

1. **Üret (reproduce)** — Hatayı istediğin anda, güvenilir biçimde tekrarlayabil.
2. **İzole et (isolate)** — Arama alanını sistematik olarak daralt.
3. **Teşhis et (diagnose)** — Hipotez kur, deneyle sına, kök nedeni bul.
4. **Düzelt (fix)** — Semptomu değil, kök nedeni onar.
5. **Doğrula (verify)** — Düzeldiğini kanıtla ve bir daha dönmemesini garantiye al.

Acemi ile ustanın farkı, adım 1 ve 2'de ortaya çıkar. Acemi doğrudan adım 3'e atlar: koda bakar, "şurada olabilir" diye tahmin eder, değiştirir, dener. Bu bir arama değil, kumardır. Usta ise önce hatayı kafese kapatır (üret), sonra kafesi küçültür (izole et) — teşhis çoğu zaman kafes yeterince küçüldüğünde kendiliğinden gelir.

## 6.3 Adım 1: Yeniden üret

Kural net: **tekrar üretemediğin hatayı düzelttiğini asla kanıtlayamazsın.** "Sanırım düzeldi" cümlesi mühendislik değildir. Bu yüzden ilk iş, hatayı emrine amade hâle getirmektir.

Hedefin şu üç özelliğe sahip bir tetikleyici bulmak: **deterministik** (her seferinde olur), **hızlı** (saniyeler içinde) ve **küçük** (mümkün olan en az girdiyle). Buna **asgari yeniden üretim örneği** (minimal reproducible example) denir.

Küçültme işlemi mekaniktir ve hatayı bulmanın yarısını halleder. 10 000 satırlık bir girdi dosyası programı çökertiyorsa, dosyayı ikiye böl — hangi yarı çökertiyor? O yarıyı tekrar ikiye böl. Bu tam olarak bir sonraki adımın (izolasyon) konusu, ama küçültme sırasında sıklıkla hata *kendiliğinden* görünür hâle gelir: "Ha, çökertenler hep boş satır içeren kayıtlarmış."

Aynı disiplini koda da uygularsın: hatayı, projeden bağımsız çalışan 20 satırlık bir dosyaya taşımaya çalış. Çoğu zaman bu taşıma sırasında "aa, burada olmuyor" dediğin an, farkın kendisi cevabı verir.

### "Bende çalışıyor" sendromu

Klasik durum: sende çalışıyor, arkadaşında çökıyor. Bu, hatanın *ortam farkından* beslendiğinin işaretidir. Şüpheli listesi kısadır:

- **Derleyici/yorumlayıcı sürümü ve bayrakları** — `-O2` ile çalışıp `-O0` ile çökmek (ya da tersi) tanımsız davranışın klasik parmak izidir.
- **İşletim sistemi ve mimari** — endianness (Bölüm 1), `int` boyutu, yol ayracı (`/` vs `\`).
- **Kütüphane sürümleri** — Python'da `requirements.txt`, C'de paylaşılan kütüphaneler.
- **Ortam değişkenleri ve dosya yolları** (Bölüm 4).
- **Zamanlama ve donanım** — çekirdek sayısı; tek çekirdekli makinede uyuyan yarış koşulu, sekiz çekirdekte uyanır.
- **Başlatılmamış bellek** — senin makinende sıfır çıkan çöp, onunkinde başka değer.

Bu yüzden modern mühendislik, ortamı da koda gömer: sanal ortamlar, kilitlenmiş bağımlılık sürümleri, container'lar (Bölüm 42). "Bende çalışıyor" cümlesini duyulmaz kılmanın yolu budur.

::: ipucu
Yeniden üretimi bulduğun an onu **kaydet**: tek satırlık bir komut, küçük bir betik ya da başarısız bir test olarak. Bu, adım 5'te (doğrula) elindeki tek kanıt olacak. Hatayı bulup düzelttikten sonra o testi projeye ekle — böylece hata geri dönmeye kalkarsa seni ilk o uyarır.
:::

## 6.4 Adım 2: İzole et — ikili aramanın gücü

Şimdi hata ayıklamanın en güçlü tek fikrine geldik ve bu fikri zaten tanıyorsun: **ikili arama**. Bölüm 5'te sıralı dizide eleman ararken kullandık; burada *hatayı* arıyoruz ama mantık aynı: her denemede arama alanını yarıya böl.

![Şekil 6.2: İkili aramayla izolasyon, üç ayrı eksende. Girdi verisini yarıya bölerek hangi kaydın çökerttiğini; kod tarihinde bölerek hangi commit'in bozduğunu bulursun. 10 000 adaylık bir alan, tek tek denemeyle 10 000 deneme; ikiye bölerek yalnız 14 deneme ister.](gorseller/b06_bisect.png)

Bu fikri üç ayrı eksende uygularsın:

**Veri üzerinde.** Girdiyi ikiye böl, hangi yarı hatayı tetikliyor? Tetikleyen yarıda devam et. 10 000 satırlık dosyada suçlu satırı 14 denemede bulursun.

**Kod üzerinde.** Program 500 satırlık bir işlemden geçiyorsa, ortasına bir kontrol noktası koy: "buraya geldiğinde veri hâlâ doğru mu?" Doğruysa hata ikinci yarıdadır, değilse birincide. Bu, `print` ile yapılan en akıllı iştir — rastgele serpiştirme değil, **ikiye bölen ölçüm**.

**Tarih üzerinde.** "Geçen hafta çalışıyordu" cümlesi altın değerindedir, çünkü arama alanını commit'lere indirger. Ve git bu aramayı senin için otomatikleştirir:

```term
$ git bisect start
$ git bisect bad                 # şu anki hâli bozuk
$ git bisect good v1.2           # bu sürüm çalışıyordu
Bisecting: 97 revisions left to test after this (roughly 7 steps)
$ ...test et...
$ git bisect good                # bu commit temizmiş
$ ...test et...
$ git bisect bad                 # bu bozukmuş
...
a3f9c21 is the first bad commit
$ git bisect reset               # normal duruma dön
```

200 commit arasından suçluyu 8 adımda bulur. Testi otomatikleştirebiliyorsan `git bisect run ./test.sh` ile tamamen otomatik de çalışır — sen kahve içerken git suçluyu bulur. Bu, `MertOS` gibi hızlı gelişen bir projede paha biçilmezdir; yeter ki commit'lerin küçük ve anlamlı olsun (Bölüm 4'te bu yüzden ısrar etmiştik).

::: dikkat
İzolasyon sırasında **aynı anda birden fazla şeyi değiştirme**. İki değişikliği birlikte yapıp sonuç düzelirse, hangisinin işe yaradığını bilemezsin — ve büyük ihtimalle biri gereksiz, hatta zararlıdır. Bu, hata ayıklamanın en sık ihlal edilen kuralıdır; acele ettiğin an ihlal edersin.
:::

## 6.5 Adım 3: Teşhis — bilimsel yöntem

Arama alanı daraldı; şimdi *neden* sorusunun sırası. Burada yapılacak iş, tahmin etmek değil **sınamaktır**:

![Şekil 6.3: Teşhis döngüsü, bilimsel yöntemin ta kendisidir. Gözlemden hipoteze, hipotezden sınanabilir bir tahmine, oradan deneye. Hipotez çürürse arama alanın daralmıştır — bu bir kayıp değil, kazançtır.](gorseller/b06_hypothesis.png)

Süreç şöyle işler:

**Gözlem.** Tam olarak ne oluyor? "Çalışmıyor" bir gözlem değildir. "3 elemanlı girdide doğru, 4 elemanlıda son eleman eksik geliyor" gözlemdir.

**Hipotez.** Gözlemi açıklayan bir mekanizma öner: "Döngü sınırı `< n-1` olmalı ama `< n` yazmışım gibi görünüyor — son eleman işlenmiyor."

**Tahmin.** Hipotez doğruysa başka ne doğru olmalı? Bu adım kritiktir, çünkü hipotezi *sınanabilir* hâle getirir: "Öyleyse döngü sayacı en fazla n−2 olmalı."

**Deney.** Tahmini ölç. Tek bir değişkeni yazdır, kesme noktası koy, kontrollü bir girdi ver.

Sonuç doğrularsa bir katman aşağı in (neden yanlış sınır yazılmış?). Çürütürse **sevin**: bir olasılığı elediğin için arama alanın daraldı. Acemiyi yoran şey, çürüyen hipotezleri başarısızlık sanmasıdır; oysa bilimde de mühendislikte de eleme, ilerlemenin kendisidir.

### En sık şüpheliler

Deneyim, hangi yerlere önce bakacağını öğretir. İşte istatistiksel olarak en verimli şüpheli listesi:

- **Sınırlar:** ilk eleman, son eleman, boş girdi, tek eleman. Birim hataları (`<` vs `<=`) burada yaşar.
- **En son değiştirdiğin şey.** Dün çalışıyorsa, dünden beri ne değişti?
- **Varsayımların.** "Bu liste hep sıralı gelir" — gerçekten mi? Bunu doğrulayan bir şey var mı?
- **Tür ve dönüşümler:** tam sayı bölmesi, taşma, `float` karşılaştırması (Bölüm 1).
- **Başlatma:** değişken gerçekten ilk değerini aldı mı? (Bölüm 2'nin çöp değerleri.)
- **Kopya mı, referans mı?** (Bölüm 3'ün aliasing tuzağı.)
- **Kaynak yaşam süresi:** serbest bırakılmış bellek, kapanmış dosya, geçersiz iterator.

### Lastik ördek yöntemi

Kulağa şaka gibi gelen ama işe yaradığı defalarca kanıtlanmış bir teknik: **kodunu yüksek sesle, satır satır, birine anlat.** O birinin insan olması bile şart değil — masandaki bir lastik ördeğe anlatabilirsin (yöntemin adı buradan gelir).

Neden işe yarıyor? Çünkü anlatmak, kodu *okumaktan* farklı bir zihinsel işlemdir. Okurken beynin niyetini görür; anlatırken her adımı gerekçelendirmek zorunda kalırsın. "Sonra bu döngü diziyi baştan sona geziyor ve her elemanı... dur, buradaki `i` neden hiç artmıyor?" Cümlenin ortasında gelen bu "dur" anı, tekniğin tamamıdır.

Pratik uygulaması: kodu anlatırken **ne yaptığını değil, neden yaptığını** söyle. "Burada `n-1`'e kadar gidiyorum çünkü son elemanla bir sonrakini karşılaştırıyorum" — bu cümleyi kuramıyorsan, hata muhtemelen orada.

## 6.6 Araç kutusu: print'ten sanitizer'a

Doğru araç, hatayı saatler yerine dakikalar içinde bulmanı sağlar. Seçimi belirti yapar:

![Şekil 6.4: Belirti-araç eşlemesi. Her hata türünün doğal bir aracı vardır. Genel strateji: en ucuz araçla başla (kodu okumak, log), tıkandığında ağır topu çıkar (hata ayıklayıcı, sanitizer).](gorseller/b06_tools.png)

### print ile hata ayıklama — ne zaman doğru?

`print`/`printf` küçümsenir ama profesyoneller de kullanır. Doğru kullanıldığında hızlı ve etkilidir. Yanlış kullanım şudur: rastgele yerlere "buraya geldi" yazdırmak. Doğru kullanım üç kurala uyar:

**1. Ölçüm yap, iz bırakma.** Her `print` bir *hipotezi sınamalı*: "burada `n`'in 4 olmasını bekliyorum" → `print("n =", n)`. Amaçsız `print("BURADA")` satırları, gürültüden başka bir şey değildir.

**2. İkiye bölerek yerleştir** (6.4). Beş `print` peş peşe değil, ortaya bir tane.

**3. Bağlam ver.** `print(x)` değil, `print(f"donguden once i={i} toplam={toplam}")`. Yarım saat sonra çıktıya baktığında hangisinin ne olduğunu bilmek zorundasın.

Ne zaman yetmez? Çok tekrarlı döngülerde (binlerce satır çıktı boğar), zamanlamaya duyarlı hatalarda (çıktı almanın kendisi zamanlamayı değiştirir — 6.8'deki heisenbug), ve programın çöktüğü durumlarda (tampondaki son satırlar diske hiç inmeyebilir — Bölüm 2'nin `fflush` dersi).

### Log: print'in yetişkin hâli

Kalıcı kodda `print` yerine **log** kullanılır. Farkı: seviyeleri vardır (kapatılabilir), zaman damgası taşır, dosyaya yazılabilir, üretimde bırakılabilir.

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("kodek")

log.debug("pencere basladi: sol=%d sag=%d", sol, sag)
log.info("dosya islendi: %s (%d satir)", ad, n)
log.warning("bozuk satir atlandi: %d", satir_no)
log.error("cikti yazilamadi: %s", hata)
```

Seviye hiyerarşisi bir sözleşmedir: `DEBUG` geliştirici ayrıntısı, `INFO` normal akış, `WARNING` beklenmedik ama idare edilebilir, `ERROR` işlem başarısız, `CRITICAL` program devam edemez. Geliştirirken `DEBUG`, üretimde `INFO` seviyesi açılır — kodu değiştirmeden ayrıntı miktarını ayarlarsın. Bu, `printf` ile mümkün olmayan şeydir.

Bir incelik: `log.debug("x=%d", x)` yazımını `log.debug(f"x={x}")` yerine tercih et. Birincisinde biçimleme yalnız o seviye açıksa yapılır; ikincisinde string her hâlükârda üretilir. Sıcak döngüde bu fark ölçülebilir.

### gdb: derinlemesine

Bölüm 4'te `gdb`'nin temel komutlarını gördün. Hata avında asıl işi gören ileri özellikler şunlar:

```term
$ gcc -g -O0 program.c -o program      # -O0: optimizasyon kapalı
$ gdb ./program
(gdb) break dosya.c:42 if i == 100     # KOŞULLU durak
(gdb) watch toplam                     # değişken DEĞİŞİNCE dur
(gdb) run
(gdb) backtrace                        # buraya nasıl geldik?
(gdb) frame 2                          # çağıran çerçeveye geç
(gdb) print *dizi@10                   # dizinin 10 elemanını bas
(gdb) info locals                       # tüm yerel değişkenler
(gdb) finish                           # bu fonksiyondan çık
```

İki komut ayrıca öne çıkar. **`watch`** (izleme noktası), "bu değişken ne zaman değişirse beni uyandır" der — bir değerin *nerede* bozulduğunu bulmanın en doğrudan yoludur. **Koşullu durak** (`break ... if`), döngünün 100 000. turunda oluşan hata için biçilmiş kaftandır; elle 100 000 kez `continue` demenin alternatifidir.

Bir de çöken programın otopsisi var: **core dump**. Program çöktüğünde belleğinin fotoğrafı diske yazılabilir; sonra `gdb ./program core` ile çökme anını, tüm değişkenleriyle inceleyebilirsin. Üretimde çöken ve tekrar üretemediğin bir hata için tek kanıtın çoğu zaman budur.

::: dikkat
`-O2` ile derlenmiş kodda hata ayıklamak yanıltıcıdır: derleyici satırları birleştirir, değişkenleri yazmaçlara taşır, döngüleri açar. `gdb` "value optimized out" der ya da satır sırası zıplar. Kural: hata ayıklarken `-O0 -g` kullan. Ama dikkat — hata *yalnızca* `-O2`'de oluşuyorsa, bu neredeyse kesinlikle **tanımsız davranış** işaretidir; o zaman sanitizer'lara geçersin.
:::

### Sanitizer'lar ve valgrind: C'nin sigortası

C'nin en zor hataları bellek hatalarıdır: taşma, sarkan işaretçi, sızıntı (Bölüm 2). Bunlar çoğu zaman *anında* çökmez; belleği sessizce bozar, program üç fonksiyon sonra alakasız bir yerde patlar. Neyse ki bunları yakalayan araçlar var ve kullanmamak için hiçbir mazeret yok:

```term
$ gcc -g -fsanitize=address,undefined program.c -o program
$ ./program
==12345==ERROR: AddressSanitizer: heap-buffer-overflow
WRITE of size 4 at 0x602000000018 thread T0
    #0 0x4008f4 in doldur program.c:12
    #1 0x400a1e in main program.c:24
0x602000000018 is located 0 bytes to the right of
    8-byte region [0x602000000010,0x602000000018)
allocated by thread T0 here:
    #0 0x7f2a in malloc
    #1 0x4008c0 in main program.c:22
```

Bu çıktı bir hediyedir: hatanın **türünü** (heap taşması), **yerini** (satır 12), **çağrı zincirini** ve hatta **bozulan bloğun nerede ayrıldığını** (satır 22) söyler. AddressSanitizer (`-fsanitize=address`) bellek hatalarını, UndefinedBehaviorSanitizer (`-fsanitize=undefined`) taşma gibi tanımsız davranışları yakalar. Programı ~2 kat yavaşlatırlar; geliştirme ve test sırasında bu bedeli seve seve ödersin.

Alternatif olarak `valgrind ./program` yeniden derlemeye gerek duymadan çalışır (daha yavaştır, ~20 kat), ve `--leak-check=full` ile sızıntıları satır satır raporlar. Bölüm 2'nin projelerinde koyduğumuz "valgrind temiz" kriteri işte bu araca aitti.

### Python: pdb ve traceback

Python tarafında hata ayıklayıcı bir satır uzağında:

```python
def ortalama(dizi):
    breakpoint()          # Python 3.7+: burada durur
    return sum(dizi) / len(dizi)
```

`breakpoint()` çağrısı seni `pdb` konsoluna düşürür; komutları `gdb`'ye benzer: `n` (next), `s` (step), `c` (continue), `p ifade` (print), `l` (list), `w` (where/backtrace), `q` (quit). Çökme sonrası inceleme için `python -m pdb -c continue program.py` ile çalıştırırsan, istisna anında konsola düşersin — çökme anının fotoğrafını canlı incelersin.

### print mi, log mu, gdb mi? Karar tablosu

Elindeki belirtiye göre ilk aracı seç; yetmezse bir sonraki ağır araca geç.

| Belirti | İlk deneyeceğin | Ağır top |
|---|---|---|
| Sonuç yanlış, nerede saptığını bilmiyorsun | `print` ya da log (ara değerler) | gdb `watch` ile değişkeni izle |
| Program çöküyor, nerede olduğunu bilmiyorsun | Traceback'i sondan oku | gdb `backtrace` ve `frame`, core dump |
| Değerler rastgele bozuluyor, bellek şüpheli | Sınırları ve başlatmayı kontrol et | ASan ya da valgrind |
| Yalnız `-O2`'de ya da "bazen" oluyor | Derlemeyi `-O0 -g` ile tekrar dene | Sanitizer'lar; yarış için ThreadSanitizer |
| Kaynak sızıntısı, bellek zamanla şişiyor | Oluşturma ve yok etme çiftlerini say | valgrind `--leak-check=full` |

::: not
Windows'ta çalışıyorsan gdb, valgrind ve ASan gibi Linux araçlarını WSL2 içinde bir Ubuntu kurup orada kullan; kodun Windows'ta kalabilir. Visual Studio'nun MSVC derleyicisinde ise bellek sanitizer'ı `/fsanitize=address` bayrağıyla açılır.
:::

## 6.7 Traceback ve log okuma

Bir hata mesajını doğru okumak, aracı kullanmaktan önce gelir. Python'un traceback'i, acemilerin panikle atladığı ama aslında adres tarifi veren bir belgedir:

![Şekil 6.5: Traceback anatomisi. Okuma sırası: (1) en alttaki hata türü ve mesajı, (2) çağrı zincirinde en alttaki SENİN dosyan, (3) o satırdaki değişkenler. Yukarıdan aşağıya çağrı sırası, aşağıdan yukarıya ise suçluya giden yol.](gorseller/b06_traceback.png)

Kurallar üç tanedir:

**1. Sondan başla.** Son satır hatanın *türünü* ve mesajını verir: `ZeroDivisionError: division by zero`. Tür sana hata sınıfını, mesaj ayrıntıyı söyler.

**2. En alttaki kendi dosyanı bul.** Traceback genelde kütüphane içlerine kadar iner. `pandas/core/frame.py` satırındaki hata büyük olasılıkla *senin* hatandır — kütüphanenin değil; sen ona yanlış bir şey vermiş olabilirsin. Kütüphane hatası da mümkündür, ama önce kendi girdini şüpheli say. En alttaki kendi dosyan, sorunun girdiği kapıdır.

**3. Kök nedeni yukarıda ara.** Çöken satır çoğu zaman *tanıktır*, suçlu değil (Bölüm 4'ün gdb örneğindeki gibi). `len(dizi)` sıfır olduğu için bölme patladıysa asıl soru şudur: dizi neden boş geldi? Cevap, çağrı zincirinin yukarısındadır.

Python'da bir de zincirleme istisnalar vardır: `During handling of the above exception, another exception occurred` ya da `The above exception was the direct cause of...`. Bu durumda **iki** traceback vardır ve genelde ilki (üstteki) asıl sebeptir; ikincisi, hatayı işlerken çıkan ikincil sorundur.

Log okumada da benzer bir disiplin işler: hatanın *ilk* göründüğü ana bak, son satıra değil. Bir sistem çökerken onlarca ardışık hata basar; bunların çoğu ilkinin sonucudur. Zaman damgalarını izleyerek en erken anormalliği bul — asıl olay orasıdır.

## 6.8 Zor hatalar: heisenbug, yarış koşulu, bellek bozulması

Bazı hatalar yukarıdaki düzenli sürece direnir. Onları ayrıca tanımak gerekir.

**Heisenbug**, gözlemlediğinde kaybolan hatadır (adı Heisenberg'in belirsizlik ilkesine göndermedir). `printf` eklersin, hata kaybolur; hata ayıklayıcı takarsın, olmaz; `-O0` ile derlersin, düzelir. Bu davranış rastgele değildir; neredeyse her zaman şunlardan birine işaret eder: zamanlamaya bağlı yarış koşulu, başlatılmamış bellek (yerleşim değişince değer değişir) ya da tanımsız davranış (derleyici optimizasyona göre farklı kod üretir). Yani heisenbug bir *bilgidir*: sana hangi aileye baktığını söyler. Cevabın sanitizer'lar ve kod incelemesidir, `printf` değil.

**Yarış koşulu (race condition)**, iki iş parçacığının aynı veriye kontrolsüz eriştiğinde ortaya çıkar:

![Şekil 6.6: Yarış koşulu. `sayac++` tek bir işlem değildir; oku-artır-yaz üçlüsüdür. İki iş parçacığı araya girerse iki artış tek artışa dönüşür. Doğruluk, işletim sisteminin zamanlama kararına kalmıştır — bu yüzden hata "bazen" ortaya çıkar.](gorseller/b06_race.png)

Bu hataların en sinsi yanı, testlerde neredeyse hiç görünmemeleridir: pencere mikrosaniyeler kadardır ve yük altında açılır. Araçların: `-fsanitize=thread` (ThreadSanitizer), kod incelemesi ve — asıl çözüm — paylaşılan durumu en baştan kilitlerle korumak. Senkronizasyonun tamamı Bölüm 27'nin konusu; şimdilik bilmen gereken, "bazen bozuluyor" belirtisinin bu aileyi işaret ettiğidir.

**Bellek bozulması** ise C'nin imzasıdır: bir yere fazladan yazarsın, çok sonra alakasız bir yer patlar. Sebep ile sonuç arasındaki bu mesafe, `printf` ile avlanmayı imkânsız kılar. Tek makul yol sanitizer/valgrind'dir — kabaca "her bellek erişimini denetleyen bir gözcü" koyarlar ve ihlali *olduğu anda* yakalarlar.

## 6.9 Adım 4-5: Düzelt ve doğrula

Kök nedeni buldun. İki tuzak kaldı.

**Semptomu değil kök nedeni düzelt.** Program `None` üzerinde patlıyorsa `if x is None: return` eklemek hatayı susturur ama çözmez: `x` neden `None` geldi? Bu soruya cevabın yoksa, hatayı bir katman derine gömmüş olursun; ileride başka bir yerde, daha anlaşılmaz bir biçimde çıkacaktır.

Kök nedene inmenin pratik aracı **beş neden** tekniğidir: cevaba ulaşana kadar "neden?" diye sormaya devam et.

> *Program çöktü.* → Neden? *Dizi boştu.* → Neden? *Dosyadan hiç kayıt okunmadı.* → Neden? *Dosya adı yanlıştı.* → Neden? *Yol, ortam değişkeninden geliyor ve tanımlı değildi.* → Neden? *Ayar okuyucu, eksik değişken için sessizce boş string dönüyor.*

Gerçek düzeltme sonuncudadır: ayar okuyucu eksik değişkende *gürültü çıkarmalıdır*. İlk maddeye yamayan bir çözüm, aynı hatayı yarın başka bir yolda karşına çıkarır.

**Doğrula ve kilitle.** Düzeltmenin işe yaradığını, adım 1'de kaydettiğin yeniden üretim örneğiyle kanıtla. Sonra da onu **regresyon testine** çevir: hatayı tetikleyen girdiyi bir teste gömersin, artık o hata geri dönmeye kalkarsa testler kırmızı yanar. Böylece her düzeltilen hata, projeyi kalıcı olarak biraz daha sağlamlaştırır. (Test yazımının tamamı Bölüm 39'da.)

Son bir şey: **düzeltmenin yan etkisini kontrol et.** Değiştirdiğin fonksiyonu başka kim çağırıyor? Bir hatayı düzeltirken iki yenisini doğurmak, acele edilen düzeltmelerin klasik sonucudur.

## 6.10 Hata ayıklamayı gereksiz kılmak

En iyi hata ayıklama, yapmak zorunda kalmadığındır. Kodu, hataların *erken* ve *gürültülü* biçimde ortaya çıkacağı şekilde yazmaya **savunmacı programlama** denir.

**Erken patla (fail fast).** Bir fonksiyon geçersiz girdiyle çağrıldığında sessizce garip bir sonuç dönmek yerine hemen bağırmalıdır. Sessiz hata, kilometrelerce ötede patlayan bir mayındır; erken hata, olay yerinde yakalanan bir hırsız.

**`assert` ile varsayımlarını yaz.** Kafandaki "burada dizi hep sıralıdır" varsayımı yorum satırı olarak yazılırsa belge, `assert` olarak yazılırsa **denetlenen sözleşme** olur:

```c
#include <assert.h>
#include <stddef.h>     /* size_t, NULL */

double ortalama(const int *dizi, size_t n) {
    assert(dizi != NULL);        // sözleşme: geçerli işaretçi
    assert(n > 0);               // sözleşme: boş dizi yasak
    long toplam = 0;
    for (size_t i = 0; i < n; i++) toplam += dizi[i];
    return (double)toplam / n;
}
```

`assert` ihlal edilirse program dosya adı ve satır numarasıyla anında durur — hatanın *oluştuğu* yerde, sonucunun görüldüğü yerde değil. C'de `NDEBUG` tanımlıysa assert'ler derlemeden silinir, yani üretimde maliyeti sıfırdır. Bu yüzden bir kural vardır: **assert içine yan etkili ifade yazma** (`assert(sil(x))` gibi) — üretim derlemesinde o satır komple yok olur.

Assert ile hata yönetimini karıştırma: `assert` *programcı hatası* içindir ("bu asla olmamalı"); kullanıcı hatası ya da dış dünya sorunu (dosya yok, ağ koptu) normal hata yolu ile ele alınır (Bölüm 3'ün istisnaları, C'de dönüş kodları).

**Değişmezleri (invariant) koru.** Bir veri yapısının her zaman doğru olması gereken özelliklerini yaz: "yığının boyu hiçbir zaman negatif olamaz", "sol < sağ". Karmaşık yapılarda bir `dogrula()` fonksiyonu yazıp kritik noktalarda çağırmak, `MertOS`'un bellek yöneticisi gibi yerlerde saatler kazandırır.

**Derleyiciyi ortak yap.** `-Wall -Wextra` ile uyarıları aç, hatta `-Werror` ile uyarıları hataya çevir. Derleyicinin bedavaya söylediği şeyi hata ayıklayıcıyla aramak, israfın daniskasıdır. Python tarafında da tip ipuçları (`def f(x: int) -> str`) ve statik denetleyiciler aynı işi görür.

::: ipucu
Kodunu "gelecekteki, yorgun, konuyu unutmuş sen" için yaz. Anlaşılır isimler, kısa fonksiyonlar, açık varsayımlar — bunların hepsi aslında hata ayıklama yatırımıdır. Bir fonksiyonu okuyup ne yaptığını 30 saniyede anlayamıyorsan, o fonksiyonda hata aramak saatler sürecek demektir. (Temiz kodun tamamı Bölüm 23'te.)
:::

## Çözümlü Örnekler

### Örnek 1 (★): Traceback'ten kök nedene

**Problem:** Bir veri analiz betiği çöküyor. Elimizde yalnız şu traceback var; hatayı ve gerçek kök nedeni bul.

```term
Traceback (most recent call last):
  File "analiz.py", line 42, in <module>
    print(ortalama(oku("veri.csv")))
  File "analiz.py", line 18, in ortalama
    return toplam / len(dizi)
ZeroDivisionError: division by zero
```

**Adım 1 — Anla.** Belirti: betik `ZeroDivisionError` ile çöküyor. Traceback'in kendisi bir kanıttır: hata `ortalama` içinde, 18. satırda.

**Adım 2 — Örnekle.** Traceback tek başına bir yeniden üretim sayılır: aynı betik, aynı girdi, aynı çökme. Girdiyi daraltarak tetikleyiciyi netleştirirsin: boş bir `veri.csv` ile betiği çalıştır. Çökme tekrar ediyorsa tetikleyici bulunmuştur.

**Adım 3 — Kaba çöz.** İlk naif hipotez: "bölme sıfıra yapılıyor, o hâlde `ortalama` içine bir kontrol koyayım." Bu yama doğru görünür ama sorunu gizler. Önce Şekil 6.5'in kurallarını uygula. *Sondan başla:* `ZeroDivisionError` — bölme sıfıra yapılmış. *Hangi satır:* 18, `toplam / len(dizi)`. Demek ki `len(dizi) == 0`; dizi boş.

**Adım 4 — Örüntü.** Ama burada durmak acemiliktir — bu **semptom**. Asıl soru: dizi neden boş? Traceback'in bir üst satırı cevabı işaret ediyor: `ortalama(oku("veri.csv"))`. Yani `oku` boş liste döndürmüş.

Beş neden turunu koşturalım: *Bölme patladı* → çünkü dizi boş → çünkü `oku` boş liste döndü → çünkü dosyada geçerli satır yok → çünkü dosya adı yanlış ya da dosya boş → ve **`oku` bu durumda hiç ses çıkarmıyor.** Hata sınıfı: **sessiz başarısızlık**. Boş sonucu hata olarak bildirmeyen bir fonksiyon, hatayı çok daha uzakta patlatır.

**Adım 5 — İyileştir.** İki katmanlı düzeltme yapılır. Kök neden: `oku` sessiz kalmamalı. Savunma: `ortalama` sözleşmesini korumalı.

```python
def oku(yol):
    with open(yol, encoding="utf-8") as f:
        kayitlar = [ayristir(s) for s in f if s.strip()]
    if not kayitlar:                       # SESSİZ KALMA
        raise ValueError(f"{yol}: geçerli kayıt yok")
    return kayitlar

def ortalama(dizi):
    if not dizi:                           # sözleşmeyi koru
        raise ValueError("ortalama: boş dizi")
    return sum(dizi) / len(dizi)
```

Koddaki `ayristir(s)` bu bölümde tanımlanmadı; bilerek bıraktık, bu fonksiyonu **sen yazacaksın**. İmzası `def ayristir(satir: str) -> float` olmalı: satırdaki sayısal alanı okuyup `float` döndürmeli, sayıya çevrilemeyen bir satırda `ValueError` fırlatmalı (bu, sessiz kalmama ilkesinin tek satırlık uygulamasıdır).

**Adım 6 — Doğrula.** Boş bir dosyayla çalıştır: artık `ZeroDivisionError` yerine `ValueError: veri.csv: geçerli kayıt yok` alırsın — hata, oluştuğu yerde ve anlaşılır biçimde. Bunu bir teste çevir: boş dosya verildiğinde `ValueError` bekleniyor. Düzeltmeyi üç girdiyle izleyen gözlem tablosu:

| Girdi | `oku` sonucu | `ortalama` sonucu |
|---|---|---|
| 3 satırlık geçerli dosya | 3 kayıt | bir sayı (ortalama) |
| Boş dosya, düzeltme öncesi | `[]` | `ZeroDivisionError` |
| Boş dosya, düzeltme sonrası | `ValueError` fırlatır | ulaşılmaz |

**Bunu AI'sız yapabilir misin?** Şu soruyu cevapla: `ortalama` içindeki kontrol ile `oku` içindeki kontrolden **biri** yeterli miydi? Hangisi olmadan sistem daha kırılgan kalırdı ve neden ikisi birden yazıldı?

### Örnek 2 (★★): Sanitizer ile tampon taşması avı

**Problem:** Aşağıdaki program çoğu zaman çalışıyor ama bazen `free()` sırasında çöküyor (heap yönetim verisi bozuluyor). Hatayı bul.

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n = 5;
    int *dizi = malloc(n * sizeof(int));
    for (int i = 0; i <= n; i++)      /* dikkat: <= */
        dizi[i] = i * i;
    printf("%d\n", dizi[0]);
    free(dizi);
    return 0;
}
```

**Adım 1 — Anla.** Belirti: çoğu zaman çalışıyor, ama bazen `free()` sırasında çöküyor; bu, heap yönetim verisinin bozulduğunu düşündürür. "Bazen" kelimesi alarm zilidir — bellek bozulması ya da tanımsız davranış ailesi. Program deterministik çökmüyor çünkü taşan yazma, heap'te bazen zararsız bir yere, bazen kritik bir yönetim verisine denk geliyor.

**Adım 2 — Örnekle.** Bu tür hatayı çıplak gözle yakalamak zordur; belirtiyi kararlı bir rapora çevirmek için AddressSanitizer ile çalıştırırsın:

```term
$ gcc -g -fsanitize=address tasma.c -o tasma
$ ./tasma
==4711==ERROR: AddressSanitizer: heap-buffer-overflow
WRITE of size 4 at 0x602000000034 thread T0
    #0 0x401186 in main tasma.c:8
0x602000000034 is located 0 bytes to the right of
    20-byte region [0x602000000020,0x602000000034)
allocated by thread T0 here:
    #0 0x7f9c in malloc
    #1 0x401156 in main tasma.c:6
```

**Adım 3 — Kaba çöz.** İlk naif hipotez: "`i <= n` şüpheli görünüyor." Ama tahminle değil kanıtla ilerleyelim.

**Adım 4 — Örüntü.** Rapor her şeyi söylüyor: 8. satırda, 20 baytlık bloğun **hemen sağına** 4 baytlık bir yazma. Yani beşinci elemandan sonrasına — `dizi[5]`. Hipotez kanıtlandı: döngü sınırı `<=` olmalıydı `<`. Hata sınıfı **heap taşması** (off-by-one). Taşan yazma tanımsız davranıştır (UB): bazen zararsız bir bayta, bazen `free()`nin kullandığı yönetim verisine denk gelir. Bu yüzden belirti "bazen"dir.

**Adım 5 — İyileştir.** Döngü sınırı `i < n` yapılır.

**Adım 6 — Doğrula.** Program yeniden ASan altında koşturulur ve rapor temiz çıkar. Taşmanın mekaniğini gösteren gözlem tablosu:

| `i` | yazılan bayt ofseti (4·i) | 20 baytlık blokta mı? |
|---|---|---|
| 4 | 16 | evet (16–19) |
| 5 | 20 | **hayır**: taşma (`<=` ile) |

Düzeltilmiş `i < n` ile `i` en fazla 4 olur; yani `i = 5` satırı artık hiç çalışmaz. Regresyon önlemi olarak, projede bundan sonra tüm testler `-fsanitize=address` ile de koşulacak şekilde ayarlanır (Bölüm 4'te yazdığın Makefile'a bir `make test-asan` hedefi eklemek tam bu iştir).

**Bunu AI'sız yapabilir misin?** ASan olmadan aynı hatayı nasıl bulurdun? İki yol düşün: `assert` ile ve `gdb`'nin `watch` komutuyla. Hangisi daha hızlı sonuç verirdi?

### Örnek 3 (★★): git bisect ile regresyon avı

**Problem:** `ÖZCE` kodunun sıkıştırma oranı testi dün geçiyordu, bugün kırık. Aradan 60 commit geçmiş. Suçluyu bul.

**Adım 1 — Anla.** Belirti: test dün geçiyordu, bugün kırık. Hangi değişikliğin bozduğunu bilmiyorsun; elinde yalnız 60 commit var.

**Adım 2 — Örnekle.** Önce testi tek komuta indir: `python -m pytest tests/test_oran.py -q`. Bu komut hem yeniden üretim hem de bisect'in ölçütü olacak.

**Adım 3 — Kaba çöz.** İlk akla gelen: en son commit'i suçlamak ya da 60 diff'i tek tek okumak. İkisi de ya zaman alır ya da yanlış commit'e takılır.

**Adım 4 — Örüntü.** Bu bir **regresyon**: çalışan bir sürüm ile bozuk bir sürüm arasındaki bir değişiklik. Bu sınıfta doğal araç ikili aramadır; elle bisect:

```term
$ git bisect start
$ git bisect bad HEAD
$ git bisect good HEAD~60
Bisecting: 29 revisions left to test (roughly 5 steps)
$ python -m pytest tests/test_oran.py -q && git bisect good
$ ...
7c1e9ab is the first bad commit
    "kuantalama esigi ayarlandi"
$ git bisect reset
```

Beş-altı adımda 60 commit elendi. Otomatikleştirmek istersen tek satır yeter:

```term
$ git bisect start HEAD HEAD~60
$ git bisect run python -m pytest tests/test_oran.py -q
```

**Adım 5 — İyileştir.** Suçlu commit belli olduğunda `git show 7c1e9ab` ile diff'i okursun — genelde küçük ve odaklı olduğu için hata gözle görünür hâle gelir. Düzeltme bu diff'teki yanlış değişikliğe yapılır.

**Adım 6 — Doğrula.** Testi yeniden koş; geçiyorsa düzeltme tamam. Kalan aday sayısının her testte yaklaşık yarıya indiğini gösteren gözlem tablosu:

| Adım | Kalan aday (yaklaşık) |
|---|---|
| Başlangıç | 60 |
| 1 | 30 |
| 2 | 15 |
| 3 | 7 |
| 4 | 3 |
| 5 | 1: suçlu commit |

Burada asıl ders şu: **bisect teşhis yapmaz, arama alanını daraltır.** Onu bu kadar güçlü kılan da, Bölüm 4'te ısrar ettiğimiz alışkanlıktır — küçük, tek işe odaklı commit'ler. 300 dosyayı değiştiren bir "haftalık güncelleme" commit'i bulunsa bile pek işe yaramaz.

**Bunu AI'sız yapabilir misin?** Bisect sırasında bir commit'te proje hiç derlenmiyorsa ne yaparsın? (İpucu: `git bisect skip` diye bir komut var — neden gerekli olduğunu düşün.)

### Örnek 4 (★★★): Sessiz mantık hatası

**Problem:** Bölüm 5'te yazdığımız kayan pencere fonksiyonunun bir varyantı, "en uzun tekrarsız alt dizgi" için bazı girdilerde **yanlış ama makul** sonuçlar veriyor. Çökme yok, hata mesajı yok. Bu, en zor hata sınıfı.

```python
def en_uzun_hatali(s):
    gorulen = {}          # karakter -> son görüldüğü indeks
    sol = 0
    en_iyi = 0
    for sag, ch in enumerate(s):
        if ch in gorulen:
            sol = gorulen[ch] + 1     # tekrarın bir sağına atla
        gorulen[ch] = sag
        en_iyi = max(en_iyi, sag - sol + 1)
    return en_iyi
```

**Adım 1 — Anla.** Belirti: çökme ve hata mesajı yok; yalnız sonuç yanlış ama makul görünüyor. Bu en zor hata sınıfıdır; sistem "çalışıyor" gibi durur.

**Adım 2 — Örnekle.** Önce hatayı deterministik hâle getir. Elimizde çökme olmadığı için "doğru cevabı bilen" bir referansa ihtiyacımız var — ve Bölüm 5'ten hatırla: kaba kuvvet çözümü tam olarak bu işe yarar. Aşağıdaki `en_uzun_kaba`, Bölüm 5'teki kaba kuvvet çözümüdür: her alt dizgiyi denetler ve tekrarsız olanların en uzununu tutar. Yavaştır ama doğrudur.

```python
def en_uzun_kaba(s):
    en = 0
    for i in range(len(s)):
        for j in range(i + 1, len(s) + 1):
            p = s[i:j]
            if len(set(p)) == len(p):     # tekrarsız mı?
                en = max(en, len(p))
    return en
```

Rastgele girdilerle iki çözümü karşılaştıran bir **fark avcısı** yazarız. `random.seed(42)` sayesinde her çalıştırmada aynı girdi dizisi üretilir:

```python
import random, string

def fark_bul():
    random.seed(42)
    for _ in range(10000):
        n = random.randint(1, 12)
        s = "".join(random.choice("abc") for _ in range(n))
        if en_uzun_hatali(s) != en_uzun_kaba(s):
            return s                    # ilk uyuşmazlık
    return None
```

Bu teknik (rastgele test + referans karşılaştırma) profesyonel dünyada **fuzzing**'in basit bir hâlidir ve mantık hatalarını bulmakta olağanüstü etkilidir. Çıktı (seed 42): `"aacbaaacacc"`. Bu 11 karakterlik girdiyi elle izlemek zordur. `'abc'` alfabesiyle 1-3 karakterli bütün girdiler denendi, hiçbiri uyuşmazlık vermedi; ilk 4 karakterli karşı örnek `"abba"` ve elle inceleyebileceğimiz büyüklük tam bu. Adım 2 tamam.

**Adım 3 — Kaba çöz.** `"abba"` üzerinde elle iz sürelim; önce gözlem, sonra ilk tahmin:

| sağ | ch | `ch in gorulen`? | sol (sonrası) | uzunluk | en iyi |
|---|---|---|---|---|---|
| 0 | a | hayır | 0 | 1 | 1 |
| 1 | b | hayır | 0 | 2 | **2** |
| 2 | b | evet (1) | 2 | 1 | 2 |
| 3 | a | evet (0) | **1** | 3 | **3** |

Son satır yanlış: `"abba"` içinde 3 uzunluğunda tekrarsız bir parça yok (doğru cevap 2). Gözlem net.

*Hipotez:* `sol` geriye gitti. Üçüncü adımda 2 olmuştu, dördüncüde 1'e düştü. Oysa pencerenin sol kenarı **asla geri gitmemeliydi** (Bölüm 5, Şekil 5.5'teki "iki kenar da yalnız sağa gider" kuralı).

**Adım 4 — Örüntü.** Hata sınıfı: **pencere değişmezinin ihlali**. Sol kenar yalnızca ileri gitmelidir; bir kenarın geri kayması, ardından gelen bütün uzunluk hesaplarını sessizce bozar.

*Tahmin:* Hipotez doğruysa, `sol` değerini her adımda yazdırdığımızda azalan bir adım görmeliyiz.

*Deney:* Döngüye tek bir ölçüm satırı ekle — `print(sag, ch, sol)` — ve `"abba"` ile koştur. Gerçekten de `sol` 2'den 1'e düşüyor. Hipotez doğrulandı.

**Adım 5 — İyileştir.** Kök neden: `gorulen[ch]`, karakterin *pencere dışında kalmış* bir eski konumunu tutabiliyor; ona göre atlayınca sol kenar geri kayıyor. Düzeltme, değişmezi (invariant) açıkça korumaktır:

```python
def en_uzun(s):
    gorulen = {}
    sol = 0
    en_iyi = 0
    for sag, ch in enumerate(s):
        if ch in gorulen and gorulen[ch] >= sol:
            sol = gorulen[ch] + 1      # yalnız pencere İÇİNDEYSE atla
        gorulen[ch] = sag
        en_iyi = max(en_iyi, sag - sol + 1)
    return en_iyi
```

Alternatif ve daha savunmacı bir yazım, değişmezi doğrudan ifade etmektir: `sol = max(sol, gorulen[ch] + 1)` — "sol asla azalmaz" kuralını kodun kendisine gömer. İkinci yazım tercih edilir, çünkü *niyeti* belgeler.

**Adım 6 — Doğrula.** Fark avcısını tekrar koştur (aynı `seed 42` ile): 10 000 girdide uyuşmazlık yok. Sonra `"abba"` örneğini kalıcı bir regresyon testine çevir. Düzeltilmiş kodun aynı girdideki izi:

| sağ | ch | `gorulen[ch]` | sol (sonrası) | uzunluk | en iyi |
|---|---|---|---|---|---|
| 0 | a | yok | 0 | 1 | 1 |
| 1 | b | yok | 0 | 2 | 2 |
| 2 | b | 1 (≥ sol=0) | 2 | 1 | 2 |
| 3 | a | 0 (< sol=2, atla) | 2 | 2 | 2 |

Sol hiç geri gitmez ve son satırda uzunluk 2 olur; doğru cevap budur. Bir de savunma ekleyebilirsin: döngü içinde `assert sol <= sag` ve `assert yeni_sol >= eski_sol`.

**Bunu AI'sız yapabilir misin?** Asıl ders şu: kaba kuvvet çözümünü *saklamak*. Bölüm 5'te "kaba çözüm bir zemindir" demiştik; işte tam da bunun için. Kendine sor: son yazdığın algoritmanın doğruluğunu neyle kanıtlayabilirdin?

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Özellikle bu bölümde: AI'a "şu hatayı düzelt" demek, tam olarak bu bölümün geliştirmeye çalıştığı kasın yerine geçer. Hatayı kendin avla.
:::

### Proje 1 (★★): Hata günlüğü

**Amaç:** Kendi hata örüntülerini tanımak. Çünkü mühendislerin çoğu aynı üç-dört hatayı tekrar tekrar yapar; bunları bilmek, gelecekteki saatlerini geri kazandırır.

**Yapılacak:** İki hafta boyunca karşılaştığın her hata için (kendi kodunda, ödevlerinde, `MertOS`'ta) kısa bir kayıt tut:

```text
BELİRTİ:     ne gördüm (mesaj / yanlış çıktı)
İLK TAHMİN:  ilk aklıma gelen sebep
GERÇEK SEBEP: kök neden (5 neden ile in)
NASIL BULDUM: hangi adım/araç işe yaradı
SÜRE:        ne kadar sürdü
ÖNLEM:       bu sınıfı bir daha nasıl engellerim
```

İki hafta sonra kayıtları oku ve sınıflandır: kaç tanesi birim hatası, kaç tanesi başlatma, kaç tanesi yanlış varsayım? En sık üç sınıfını yaz.

**Başarı kriterleri:** En az 15 kayıt; "İLK TAHMİN" ile "GERÇEK SEBEP"in kaç kez uyuşmadığını sayabiliyorsun (bu sayı, tahminle hata ayıklamanın neden kötü bir strateji olduğunun kişisel kanıtın olacak); en sık üç hata sınıfın için birer önlem yazmışsın (assert, test, kod düzeni...).

### Proje 2 (★★★): MertOS'a hata ayıklama altyapısı

**Amaç:** Çekirdek gibi hata ayıklayıcı takılamayan bir ortamda hatayı görünür kılan altyapıyı kendin kur. Bu proje doğrudan `MertOS`'a yazılacak gerçek kod.

**Yapılacak — üç bileşen:**

1. **Log sistemi:** `KLOG(seviye, format, ...)` makrosu. Seviyeler: `KLOG_DEBUG`, `KLOG_INFO`, `KLOG_WARN`, `KLOG_ERR`. Çalışma anında ayarlanabilen bir eşik seviyesi olsun (eşiğin altındakiler basılmasın). Her satır seviye etiketi ve kaynak konumu (`__FILE__`, `__LINE__`) taşısın.

2. **Assert:** `KASSERT(kosul)` makrosu. İhlal edildiğinde dosya, satır, fonksiyon adı ve koşul metnini basıp sistemi kontrollü biçimde durdursun (panik). `NDEBUG` tanımlıysa hiçbir kod üretmesin.

3. **Panik işleyicisi:** `kpanic(mesaj)` — ekrana/seri porta belirgin bir blok bassın: mesaj, mümkünse yazmaç değerleri ve durdurma. Rastgele çöken bir çekirdek yerine, ne olduğunu söyleyen bir çekirdek elde etmiş olacaksın.

**Önerilen yaklaşım:** Makro yazımında Bölüm 2.11'deki kuralları uygula: parametreleri paranteze al, çok satırlı makroyu `do { ... } while (0)` içine sar (nedenini Kod Okuma egzersizinde göreceksin). Koşulun metnini basmak için ön işlemcinin `#` (stringize) operatörünü araştır: `#kosul` ifadesi, koşulu string'e çevirir.

**Başarı kriterleri:** `KLOG` eşiği değiştirilince çıktı miktarı değişiyor; `KASSERT(1 == 2)` dosya/satır/koşul metnini doğru basıyor; `NDEBUG` ile derlendiğinde assert'ler ikili dosyada hiç yer kaplamıyor (boyutu karşılaştır); makrolar `if (x) KASSERT(y); else ...` gibi bağlamlarda derleme hatası vermiyor (do-while sınavı).

### Ek Alıştırmalar

**Hata avı.** Aşağıdaki üç kısa programın her birinde gizli bir hata var. Belirtisini verdik, çözümünü vermedik. Hatayı bul, nedenini bir cümleyle açıkla ve düzelt.

**Hata avı 1 (★) — Birim hatası.** Aşağıdaki program, hızı km/sa ile mesafeyi metre ile verince süreyi dakika olarak döndürmeli. Belirti: `5000` metre ve `36.0` km/sa için çıktı `2.31`; oysa 5 km'yi 36 km/sa hızla giden birinin süresi 8.33 dakika olmalı.

```c
#include <stdio.h>

/* Mesafe (metre) ve hız (km/sa) ile dakika cinsinden süre */
double sure_dk(double mesafe_m, double hiz_kmh) {
    return mesafe_m / hiz_kmh / 60.0;
}

int main(void) {
    printf("%.2f\n", sure_dk(5000, 36.0));
    return 0;
}
```

**Hata avı 2 (★★) — Başlatılmamış değişken.** Aşağıdaki `ara`, dizide hedef yoksa `-1` döndürmeli. Belirti: `ara(d, 3, 99)` çağrısı beklenen `-1` yerine rastgele görünen bir sayı döndürebiliyor; üstelik bu sayı çalıştırmadan çalıştırmaya değişebiliyor.

```c
#include <stdio.h>

int ara(int *d, int n, int hedef) {
    int konum;
    for (int i = 0; i < n; i++)
        if (d[i] == hedef) konum = i;
    return konum;
}

int main(void) {
    int d[] = {4, 8, 15};
    printf("%d\n", ara(d, 3, 99));
}
```

**Hata avı 3 (★★) — Yanlış karşılaştırma.** Aşağıdaki program yalnızca `gizli` parolasını kabul etmeli. Belirti: `gizxyz` ya da `giz` girildiğinde de "Giris tamam" çıkıyor.

```c
#include <stdio.h>
#include <string.h>
int main(void) {
    char girdi[32];
    fgets(girdi, sizeof girdi, stdin);
    girdi[strcspn(girdi, "\n")] = 0;
    if (strncmp(girdi, "gizli", 3) == 0)
        printf("Giris tamam\n");
    else
        printf("Hata\n");
}
```

Bu üç hatayı bulduktan sonra cevapsız alıştırmalara geç. Her birinde klasik bir mülakat sorusu var; çözümü kâğıtta, sonra kodda dene.

**Alıştırma 1 (★) — Parantez dengesi.** `(`, `)`, `[`, `]`, `{`, `}` içeren bir metnin dengeli olup olmadığını döndüren fonksiyonu yaz. Hangi veri yapısını seçtiğini ve neden seçtiğini açıkla.

**Alıştırma 2 (★★) — İki toplam.** Bir dizide toplamı verilen `hedef` eden iki elemanın indekslerini bul. Önce O(n²) bir çözüm yaz, sonra daha hızlı bir yol düşün (ipucu: Bölüm 9'da işine yarayacak bir veri yapısı var).

**Alıştırma 3 (★★) — Bağlı listede döngü.** Tek bağlı listede bir döngü (cycle) olup olmadığını ek bellek kullanmadan bul. Yavaş ve hızlı iki işaretçi fikrini kendi cümlelerinle anlat.

**Alıştırma 4 (★★) — Diziyi döndürme.** Bir diziyi `k` konum sola döndür; yardımcı bir dizi kullanmadan, yalnız O(1) ek bellekle yap.

**Alıştırma 5 (★★★) — Min-stack.** Eleman ekleme, çıkarma ve en küçük elemanı bulma işlemlerinin hepsi O(1) olan bir yığın tasarla. Yardımcı bir yığın tutmak işine yarayabilir mi, düşün.

**Alıştırma 6 (★★★) — En uzun ardışık aralık.** Sıralı olmayan bir tamsayı dizisinde, ardışık sayılardan oluşan en uzun aralığın uzunluğunu bul. Örneğin `[100, 4, 200, 1, 3, 2]` için cevap 4'tür (1, 2, 3, 4). Sıralamadan kaçınarak O(n) hedefle.

**Alıştırma 7 (★★) — Güvenli kopyalama.** `void kopyala(char *hedef, size_t boyut, const char *kaynak)` fonksiyonunu yaz: `hedef` taşmasın ve sonuç her zaman `\0` ile bitsin. Kaynak ile hedefin üst üste binmesi durumunu da düşün.

**Alıştırma 8 (★★★) — İki yığınla kuyruk.** Yalnızca iki yığın kullanarak bir kuyruk (queue) yaz; `ekle` ve `cikar` işlemlerinin ortalama O(1) olduğunu gerekçelendir.

## Kod Okuma Egzersizi

Bugünkü kesit, C standart kütüphanesinin `assert` makrosunun tipik uygulaması ve Linux çekirdeğinin akrabası:

```c
/* glibc 2.39, assert/assert.h -- SADELEŞTİRİLMİŞ kesit.           */
/* Gerçek dosya __ASSERT_FUNCTION, __extension__ ve GCC'ye özgü  */
/* ({ ... }) dallarını da içerir; burada yalnız ANSI C dalı var.  */
#ifdef NDEBUG
#  define assert(expr) ((void)0)
#else
#  define assert(expr)                                        \
     ((expr)                                                  \
      ? (void)0                                               \
      : __assert_fail(#expr, __FILE__, __LINE__, __func__))
#endif
```

Ve öğretici amaçlı bir **kurgu** çekirdek log makrosu. Bu, gerçek bir projeden alınmış değil; `KLOG` adı ve yapısı Proje 2'ye zemin olsun diye uyduruldu. İçinde geçen `kprintf` (çekirdek içi printf benzeri bir çıktı fonksiyonu) ve `klog_seviye` (çalışma anındaki eşik, bir `int` değişkeni) bu bölümde tanımlanmamış semboller; burada var sayılıyorlar:

```c
#define KLOG(sev, fmt, ...)                                   \
    do {                                                      \
        if (klog_seviye >= (sev))                             \
            kprintf("[%s:%d] " fmt, __FILE__, __LINE__,       \
                    ##__VA_ARGS__);                           \
    } while (0)
```

**Sorular — cevaplamadan geçme:**

- `#expr` ifadesi ne üretir? `assert(n > 0)` yazdığında hata mesajında `"n > 0"` metninin çıkmasını sağlayan mekanizma nedir?
- `__FILE__`, `__LINE__`, `__func__` ne zaman ve kim tarafından doldurulur? (İpucu: Bölüm 4'ün dört aşaması — hangisinde?)
- `NDEBUG` tanımlıyken `assert(x)` neden `((void)0)`'a çevriliyor da boş bırakılmıyor? (İpucu: `assert(x);` satırındaki noktalı virgül ve `if (a) assert(x); else ...` yapısını düşün.)
- Bu tanım, `assert` içine yan etkili ifade yazmanın neden tehlikeli olduğunu doğrudan gösteriyor: `assert(kaydet(x))` üretim derlemesinde ne olur?
- `KLOG` makrosu neden `do { ... } while (0)` içinde? Sadece `{ ... }` kullansaydık `if (a) KLOG(KLOG_INFO, "x"); else b();` satırında ne olurdu? Deneyerek gör.
- `##__VA_ARGS__` içindeki `##` ne işe yarar? `KLOG(KLOG_INFO, "basladi")` gibi ek argümansız çağrıda olmasa ne olurdu?
- Son olarak tasarım sorusu: `KLOG` seviye kontrolünü *çalışma anında* (`if`) yapıyor. Derleme anında kapatmak isteseydin nasıl yazardın ve hangi durumda hangisi tercih edilir?

## Bölüm Özeti

Bu bölümde hata ayıklamayı sezgiden yönteme çevirdik:

- **Hata, kodun yaptığı ile senin sandığın arasındaki farktır.** Bilgisayar hata yapmaz; düzeltilecek şey çoğu zaman kafandaki modeldir.
- **Hata türü aracı belirler:** derleme < çökme < mantık hatası (en tehlikelisi sessiz olandır) < eşzamanlılık/UB.
- **Beş adımlı döngü:** Üret → İzole et → Teşhis → Düzelt → Doğrula. Acemi 3'ten başlar (tahmin); usta 1 ve 2'ye yatırım yapar.
- **Üret:** deterministik, hızlı, küçük bir yeniden üretim örneği. "Bende çalışıyor" bir ortam farkı ipucudur.
- **İzole et:** ikili arama — veri üzerinde, kod üzerinde, tarih üzerinde (`git bisect`). Her denemede alan yarıya iner. Aynı anda tek bir şey değiştir.
- **Teşhis:** gözlem → hipotez → tahmin → deney. Çürüyen hipotez ilerlemedir. Lastik ördek: kodu *neden* öyle yazdığını sesli anlat.
- **Araçlar:** ölçüm yapan `print`, seviyeli log, `gdb` (koşullu durak, `watch`, core dump), sanitizer'lar ve valgrind (bellek), `pdb`, profiler. En ucuzdan başla.
- **Traceback'i sondan başa oku:** hata türü → en alttaki kendi dosyan → kök neden yukarıda.
- **Zor sınıflar:** heisenbug (gözleyince kaybolur → zamanlama/UB/başlatılmamış bellek), yarış koşulu (`sayac++` atomik değildir), bellek bozulması (sebep ile sonuç arasında mesafe var).
- **Düzelt:** semptomu değil kök nedeni (beş neden). **Doğrula:** yeniden üretim örneğini regresyon testine çevir.
- **Savunmacı programlama** hata ayıklamayı gereksiz kılar: erken patla, `assert` ile varsayımlarını yaz, değişmezleri koru, derleyici uyarılarını aç.

**Sonraki bölümde:** Kısım II bitti — artık bir problemi çözecek süreci ve kodunu ayağa kaldıracak yöntemi biliyorsun. Şimdi cephaneliği dolduruyoruz. **Kısım III — Veri Yapıları** ile başlıyoruz: **Bölüm 7 — Array & Linked List**'te bitişik bellek ile bağlı düğümlerin ödünleşimini, Bölüm 5'te söz verdiğimiz dinamik dizi büyütmesinin amortize analizini ve `MertOS`'un `kstring.hpp`'sinin altındaki mekaniği kuracağız.

::: mulakat
Klasik sorular — hemen cevaplamaya çalışma, her birini birkaç dakika düşün:

1. Bir hatayı yeniden üretemiyorsan ilk yapman gerekenler nelerdir?
2. `git bisect` hangi problemi çözer ve neden küçük commit'ler onu daha güçlü kılar?
3. Programın `-O0` ile çalışıp `-O2` ile çöküyorsa ilk şüphen ne olur?
4. `assert` ile normal hata yönetimi (istisna / dönüş kodu) arasındaki sınır nerededir?
5. `sayac++` iki iş parçacığında neden güvenli değildir? Sorun tam olarak hangi anda oluşur?
6. Bir hatayı düzelttikten sonra "bitti" demeden önce yapılması gereken iki şey nedir?
:::
