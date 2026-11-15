%% kisim_no: I
%% kisim_ad: Programlama Temelleri
%% bolum_no: 4
%% baslik: Terminal & Araçlar

## Giriş: Tezgâhını kur

İlk üç bölümde iki dil öğrendin; bu bölümde **atölyeyi** öğreneceksin. Çünkü gerçek mühendislik ortamında kod, renkli bir editör penceresinde değil, bir zincirin içinde yaşar: derlenir, bağlanır, test edilir, sürümlenir, bir sunucuya taşınır. O zincirin her halkası terminalden geçer.

"Neden fareyle tıklamak varken yazı yazayım?" sorusunun cevabı üç katmanlı. **Birincisi erişim:** savunma sanayiinde çalışacağın makinelerin çoğu, kapalı ağdaki sunucular ya da bir karta gömülü Linux'tur — grafik arayüzü yoktur, `ssh` ile bağlanır, terminalle konuşursun. **İkincisi otomasyon:** fareyle yaptığın hiçbir şeyi tekrarlayamazsın; terminale yazdığın her şey bir betiğe (script) dönüşüp senin yerine bin kez çalışabilir. **Üçüncüsü anlayış:** IDE'nin "Run" düğmesi, bu bölümde söküp içine bakacağımız `gcc` zincirinin üstüne çekilmiş bir perdedir. Perdeyi kaldıran, `undefined reference` hatasını okuyup "bu bir bağlama sorunu" diyebilen mühendis, düğmeye basıp dua eden mühendisten ayrılır.

Bu bölümde beş alet kuşanacaksın: **kabuk** (dosya sistemi + boru hattı), **bash betikleri**, **gcc** (dört aşamasıyla), **gdb** (hata ayıklayıcı), **make** ve **git**. `MertOS` zaten bir Makefile ile derleniyor, `ÖZCE` deneylerini betiklerle koşturuyorsun — bu bölüm o el yordamını sistemli bilgiye çevirecek ve Kısım I'i kapatacak.

::: not
Windows'ta mısın? Bu bölümdeki her şey WSL (Windows Subsystem for Linux) içinde birebir çalışır; zaten `MertOS`'u da öyle derliyorsun. Komutları okumakla yetinme — bu bölüm, kitabın en "yaparak öğrenilen" bölümü. Terminali aç, her komutu kendi elinle yaz.
:::

## 4.1 Dosya sistemi ve kabuk: haritayı öğren

Terminal açtığında karşındaki program **kabuktur (shell)** — genelde `bash`. Kabuk bir çevirmendir: yazdığın komutu alır, ilgili programı çalıştırır, çıktısını sana gösterir. Kabukla konuşmanın ilk şartı, neredesin bilmek. Linux'ta her şey tek bir ağacın dallarıdır; sürücü harfleri (C:, D:) yoktur, tek kök vardır: `/`.

![Şekil 4.1: Linux dosya ağacının önemli durakları. Her şey kökten (/) dallanır; senin evin /home/mert'tir ve ~ ile kısaltılır. /dev'e dikkat: Linux'ta aygıtlar bile dosya gibi görünür.](gorseller/b04_fs_tree.png)

Ağaçta gezinmenin üç temel komutu ve yol (path) kavramı şöyle çalışır:

```term
$ pwd                        # neredeyim?
/home/mert
$ ls projeler                # klasörün içinde ne var?
mertos  ozce  kitap
$ cd projeler/mertos         # göreli yol: bulunduğun yerden
$ cd /home/mert/projeler     # mutlak yol: kökten itibaren
$ cd ..                      # bir üst dizine
$ cd ~                       # eve dön (/home/mert)
```

`/` ile başlayan yol **mutlaktır** (kökten tarif), başlamayan **görelidir** (bulunduğun yerden tarif). İki özel isim her dizinde vardır: `.` "burası", `..` "bir üstü". Dosya işlemlerinin çekirdek takımı da küçüktür:

| Komut | İş | Örnek |
|---|---|---|
| `mkdir` | dizin yarat | `mkdir deneyler` |
| `cp` | kopyala | `cp main.c yedek.c` |
| `mv` | taşı / yeniden adlandır | `mv eski.c yeni.c` |
| `rm` | sil | `rm gecici.o` |
| `cat` | dosyayı bas | `cat notlar.txt` |
| `less` | sayfa sayfa oku | `less uzun.log` |
| `man` | kılavuz | `man cp` |

::: dikkat
Terminalde çöp kutusu yoktur. `rm` geri alınamaz; `rm -r klasor` bir dizini içindekilerle birlikte, sormadan yok eder. Yıldızla birleşince (`rm *.o` niyetine yazılmış `rm * .o`) tek boşluk felaket demektir. Alışkanlık edin: `rm` yazdıysan, Enter'a basmadan komutu bir kez daha oku.
:::

## 4.2 Üç akış ve boru: Unix felsefesi

Unix'in elli yıldır eskimeyen fikri şudur: *her biri tek işi iyi yapan küçük programlar yaz; bunları birbirine bağla.* Bu bağlantıyı mümkün kılan şey, her programın üç standart akışla doğmasıdır: **stdin** (girdi, 0), **stdout** (çıktı, 1) ve **stderr** (hata çıktısı, 2). Bölüm 2'de `fprintf(stderr, ...)` yazarken bu üçlünün ikisini zaten kullandın.

![Şekil 4.2: Üç standart akış ve boru. Normalde stdin klavyeden gelir, stdout ve stderr ekrana gider. Boru (|) soldaki programın stdout'unu sağdakinin stdin'ine bağlar — programlar birbirinden habersizce zincir olur.](gorseller/b04_streams.png)

Akışları yönlendirme operatörleri az ama güçlüdür:

```term
$ ./uygulama > cikti.txt        # stdout'u dosyaya yaz (üstüne)
$ ./uygulama >> cikti.txt       # dosyanın sonuna ekle
$ ./uygulama 2> hatalar.txt     # stderr'i ayrı dosyaya
$ ./uygulama < girdi.txt        # stdin'i dosyadan besle
$ ls -l | grep ".c"             # boru: çıktıyı sonraki komuta ver
```

Boru hattının gedikli işçilerini tanı: `grep desen` satır süzer, `wc -l` satır sayar, `sort` sıralar, `uniq -c` ardışık tekrarları sayarak teker bırakır, `head -n 5` / `tail -n 5` baştan/sondan keser, `cut -d"," -f2` satırı ayraçla bölüp alan seçer. Tek başlarına mütevazı, zincirde güçlüler — Örnek 1'de beş tanesini tek hatta dizip gerçek bir log analizi yapacağız.

::: ipucu
Terminalde hız, ezber değil reflekstir: `Tab` yarım yazdığını tamamlar, `↑` önceki komutları gezer, `Ctrl+R` geçmişte arama yapar, `Ctrl+C` çalışan programı keser. Bu dört tuş, klavye başındaki ömrünü yıllar bazında kısaltır.
:::

## 4.3 Bash betikleri: tekrarı makineye devret

Aynı üç komutu günde beş kez yazıyorsan, o üç komut bir dosyayı hak etmiştir. Bash betiği, komutların sırayla yazıldığı bir metin dosyasıdır; ilk satırdaki **shebang** (`#!`) hangi yorumlayıcının çalıştıracağını söyler. Derle-çalıştır döngünü otomatikleyen gerçekçi bir betik şöyle görünür:

```bash
#!/bin/bash
# derle_kostur.sh — derle, başarılıysa çalıştır

hedef="uygulama"                    # değişken: boşluksuz atama!

if [ ! -f "$1" ]; then          # $1: ilk argüman; -f: dosya var mı
    echo "kullanım: $0 kaynak.c" >&2
    exit 1                      # sıfır dışı = hata (bkz. Bölüm 2)
fi

gcc -Wall -g "$1" -o "$hedef"
if [ $? -ne 0 ]; then               # $?: son komutun çıkış kodu
    echo "derleme başarısız" >&2
    exit 1
fi

echo "--- çalıştırılıyor ---"
./"$hedef"
```

```term
$ chmod +x derle_kostur.sh      # çalıştırma izni ver (bir kez)
$ ./derle_kostur.sh topla.c
--- çalıştırılıyor ---
Dizinin toplamı: 42
```

Satır satır hesabı: `$1, $2, ...` betiğe verilen argümanlar, `$0` betiğin adı. `[ ... ]` bir koşul testidir ve **köşeli parantezlerin içindeki boşluklar zorunludur** — `[$1 -eq 5]` yazmak sözdizimi hatasıdır, çünkü `[` aslında bir programdır ve argümanlarının ayrılması gerekir. `"$1"` gibi tırnaklama, boşluklu dosya adlarının tek argüman kalmasını sağlar; tırnaksız değişken kullanımı bash'in klasik tuzağıdır. `$?` ise Bölüm 2'de `return 0`'la ektiğimiz tohumun hasadı: her programın çıkış kodu, bir sonraki kararın girdisidir. `&&` ile zincirlersen bu kontrol tek satıra iner: `gcc a.c && ./a.out` — soldaki *başarılıysa* sağdaki çalışır (C'deki kısa devrenin kabuktaki ikizi).

Döngü de aynı doğallıkta: `ÖZCE` deneylerinde beş farklı parametreyle aynı programı koşturmak istersen `for oran in 0.1 0.3 0.5; do ./kodek --oran $oran; done` yeter. Betikleşen her tekrar, hem zaman hem *hata* tasarrufudur — insan beşinci tekrarında yanlış yazar, betik yazmaz.

### Komut çıktısını değişkene almak: `$(...)`, `date`, `tar`

Bir komutun çıktısını değişkene koymak için `$(komut)` yazarsın; bu yapıya **komut ikamesi** (command substitution) denir. Kabuk önce parantezin içindeki komutu çalıştırır, çıktısını alır ve o metnin yerine koyar. `date` geçerli tarihi ve saati istediğin biçimde yazdırır: `+%F_%H%M` biçimi `2026-07-20_1432` gibi bir metin üretir. `tar` birden çok dosyayı tek bir arşiv dosyasında toplar; `czf` bayrakları sırasıyla *oluştur* (c), *gzip ile sıkıştır* (z) ve *arşiv dosyasının adı* (f) anlamına gelir. Değişkenin tırnaklı kullanımı ise boşluk içeren sonuçların bozulmasını önler.

```term
$ tarih=$(date +%F_%H%M)
$ echo "$tarih"
2026-07-20_1432
$ tar czf ozce.tar.gz projeler/ozce   # oluştur ve sıkıştır
$ tar tzf ozce.tar.gz | head -3       # içeriği listele (t)
```

## 4.4 gcc'nin dört aşaması: perdeyi kaldır

Bölüm 2'den beri `gcc kaynak.c -o uygulama` yazıyorsun. Tek komut gibi görünen şey, aslında dört ayrı programın konveyör bandıdır ve her aşamanın *ne ürettiğini* bilmek, hata mesajlarını okumanın anahtarıdır:

![Şekil 4.3: gcc'nin konveyör bandı. Ön işlemci #'leri açar (saf C), derleyici C'yi assembly'ye çevirir, assembler makine koduna (nesne dosyası) dönüştürür, bağlayıcı nesneleri ve kütüphaneleri tek çalıştırılabilirde birleştirir. -E, -S, -c bayrakları bandı istediğin aşamada durdurur.](gorseller/b04_gcc.png)

**1. Ön işleme (preprocessing).** `#include`, `#define` gibi `#`'li satırlar burada işlenir. Bölüm 2'de "kopyala-yapıştır" dediğim şey tam olarak budur: `#include <stdio.h>` satırının yerine dosyanın kendisi yapıştırılır. Kanıtı gör: `gcc -E merhaba.c | wc -l` — beş satırlık programın önişlem sonrası kaç bin satır olduğuna bak.

**2. Derleme (compilation).** Saf C, assembly'ye çevrilir — Bölüm 1'deki `LOAD/ADD/STORE` dünyasına. `gcc -S merhaba.c` sana `merhaba.s` bırakır; içine bak, `c = a + b`'nin gerçekte kaç komut olduğunu kendi gözünle gör. Optimizasyon (`-O2`) bu aşamada devreye girer.

**3. Çevirme (assembly).** Assembler, `.s` dosyasını gerçek makine koduna çevirir: `merhaba.o` **nesne dosyası** doğar. Bu dosya çalıştırılamaz; içinde makine kodu ve "printf diye bir şeye ihtiyacım var ama adresini bilmiyorum" türünden boş referanslar vardır.

**4. Bağlama (linking).** Bağlayıcı (linker), tüm `.o` dosyalarını ve kütüphaneleri masaya koyar, herkesin boş referansını birinin tanımıyla eşler, tek çalıştırılabilir üretir. `printf`'in gerçek kodu programına burada, C kütüphanesinden gelir.

Bu ayrımın pratikteki değeri hata mesajlarında ortaya çıkar. İki hata türünü karşılaştır:

```term
$ gcc main.c -o uygulama          # GCC 14 ve sonrası: derleme durur
main.c:5:5: error: implicit declaration of function 'topla'
      # DERLEME hatası: prototip yok — imza hiç görülmedi

$ gcc main.c -o uygulama          # GCC 13: uyarı, sonra bağlama hatası
main.c:5:5: warning: implicit declaration of function 'topla'
/usr/bin/ld: /tmp/ccR7kLqB.o: in function `main':
main.c:(.text+0x1a): undefined reference to `topla'
      # BAĞLAMA hatası: TANIM hiçbir .o'da yok
```

İlki derleyiciden gelir: "bu fonksiyonun imzasını görmedim" — prototip (başlık dosyası) eksiktir. GCC 13 ve öncesi bunu yalnız uyarı sayar ve derlemeye devam eder; hata bağlamada geri döner. GCC 14 ve sonrası ise bunu baştan hata sayıp derlemeyi durdurur. Mesajın sonuna `[-Wimplicit-function-declaration]` etiketi de eklenir. Dikkat: `'x' undeclared` kalıbı tanımsız *değişken* içindir; fonksiyon çağrısında `implicit declaration` görürsün. İkincisi bağlayıcıdan (`ld`) gelir: "imzayı gördüm ama gövdesini bulamadım" — `topla`'nın tanımlandığı `.c` dosyası derlemeye dahil edilmemiştir. Bu ayrımı bilen, hatanın *hangi aşamada* olduğunu mesajın kaynağından okur ve doğru yere bakar; Örnek 2'de bu hatayı bilerek üretip çözeceğiz.

Sık kullanacağın bayrakların özeti:

| Bayrak | Anlamı |
|---|---|
| `-Wall -Wextra` | uyarıları aç — pazarlıksız, her zaman |
| `-g` | hata ayıklama bilgisi ekle (gdb için şart) |
| `-O0` / `-O2` | optimizasyon: kapalı / makul hızlı |
| `-c` | yalnız derle, bağlama (`.o` üret) |
| `-o ad` | çıktı dosyasının adı |
| `-E` / `-S` | ön işlemede / assembly'de dur |

## 4.5 gdb: programın içine ışık tut

`printf` serpiştirerek hata aramak, karanlık odada el yordamıyla anahtar aramaktır. **gdb** (GNU Debugger) odanın lambasıdır: programı durdurur, değişkenlere baktırır, çökme anının fotoğrafını çeker. Tek ön koşulu `-g` bayrağıyla derlemektir — bu bayrak, makine koduyla kaynak satırlarını eşleyen tabloyu gömer.

En sık kullanacağın senaryo, çöken bir programın *nerede ve neden* çöktüğünü bulmaktır. Komut çantası küçüktür:

| Komut | Kısa | İş |
|---|---|---|
| `break main` | `b` | durak koy (fonksiyon ya da dosya:satır) |
| `run` | `r` | programı başlat |
| `next` | `n` | bir satır ilerle (fonksiyonun üstünden atla) |
| `step` | `s` | bir satır ilerle (fonksiyonun içine gir) |
| `print x` | `p` | ifadenin değerine bak |
| `backtrace` | `bt` | çağrı zinciri: buraya nasıl gelindi? |
| `continue` | `c` | sonraki durağa kadar koş |

Gerçek bir oturumu Örnek 4'te baştan sona yaşayacağız; şimdilik akışın iskeleti şu: `gcc -g` ile derle → `gdb ./uygulama` → `run` → çökünce `backtrace` ile "olay yeri raporu"nu al → şüpheli çerçevede `print` ile değişkenleri sorgula. gdb sana *nerede* sorusunun cevabını verir; *neden* sorusu hâlâ senin beynine emanet — o beynin sistematiği de Bölüm 6'nın konusu.

## 4.6 make: yalnız değişeni derle

Projen üç dosyaya çıktığı an elle derleme çileye döner: her değişiklikte hepsini yeniden mi derleyeceksin? `MertOS` gibi onlarca dosyalık bir projede bu, dakikalar demektir. **make**, iki bilgiyle bu israfı bitirir: *neyin neye bağımlı olduğu* ve *dosyaların değişme zamanları*. Kuralı basittir: hedef, bağımlılıklarından eskiyse tarifini çalıştır; değilse elleme.

![Şekil 4.4: make'in bağımlılık grafı. uygulama iki nesne dosyasına, her nesne kendi .c'sine ve ortak mat.h'ye bağlıdır. mat.h değişince main.o, mat.o ve uygulama yeniden üretilir — ama yalnız onlar.](gorseller/b04_make.png)

Bu grafı make'e `Makefile` adlı dosyayla anlatırsın. Söz dizimi üç parçadır — `hedef: bağımlılıklar` ve altında TAB ile içerlenmiş tarif:

```makefile
CC      = gcc
CFLAGS  = -Wall -Wextra -g

uygulama: main.o mat.o          # hedef: bağımlılıklar
	$(CC) $(CFLAGS) -o uygulama main.o mat.o

main.o: main.c mat.h
	$(CC) $(CFLAGS) -c main.c

mat.o: mat.c mat.h
	$(CC) $(CFLAGS) -c mat.c

clean:                          # sahte hedef: dosya üretmez, temizler
	rm -f uygulama *.o

.PHONY: clean
```

```term
$ make            # ilk sefer: her şey derlenir
$ make
make: 'uygulama' is up to date.    # hiçbir şey değişmedi → sıfır iş
$ touch mat.h     # mat.h'nin tarihini yenile (değişmiş gibi yap)
$ make            # main.o, mat.o ve uygulama yeniden; başka hiçbir şey
```

Üç ayrıntı önemli. **TAB zorunlu:** tarif satırları boşlukla değil, gerçek TAB karakteriyle içerlenir; "missing separator" hatası gördüğünde suçlu budur. **Değişkenler** (`CC`, `CFLAGS`) bayrakları tek yerden yönetir — bayrak değişikliği için on satır düzeltmezsin. **`.PHONY`**, `clean` gibi dosya üretmeyen hedefleri işaretler; yoksa dizinde `clean` adında bir dosya belirirse make "clean zaten güncel" deyip tarifini hiç çalıştırmaz. Kod Okuma egzersizinde Redis'in gerçek Makefile'ında bu fikirlerin sanayi hâlini, `%.o: %.c` kalıp kurallarını ve `$@`/`$<` otomatik değişkenlerini göreceksin.

Yukarıdaki Makefile'da `main.o` ve `mat.o` kuralları aynı kalıbı tekrarlıyor. **Kalıp kural** bunu tek satıra indirir: `%.o: %.c` der ki "her `X.o` için, aynı adlı `X.c`'den üret"; `%` herhangi bir adı yakalayan joker karakterdir. Tarifin içinde **otomatik değişkenler** kullanılır: `$@` hedefin adı (`main.o`), `$<` ilk bağımlılık (`main.c`), `$^` ise tüm bağımlılıklar. Proje 2'de elle yazacağın üç `.o` kuralını bu kalıbın tek satırına indirmek, tam olarak bu fikre dayanır.

## 4.7 git: zamanda yolculuk ve paralel evrenler

Şu klasörü hepimiz gördük: `proje_son`, `proje_son2`, `proje_gercekten_son`. **git**, bu ilkel sürümlemenin mühendisçesidir: her anlamlı noktada projenin tam fotoğrafını (commit) alır, fotoğraflar arasında gezdirir, paralel çalışma çizgileri (branch) açtırır. Zihinsel model üç alandır:

![Şekil 4.5: git'in üç alanı. Dosyaları çalışma dizininde düzenlersin; git add seçtiklerini sahneye alır; git commit sahnedekilerin kalıcı fotoğrafını depoya (.git) yazar. Sahne, "bu commit'e tam olarak ne girecek?" sorusunun cevap alanıdır.](gorseller/b04_git_areas.png)

Günlük döngü dört komuttur ve `status` her adımın pusulasıdır:

```term
$ git init                          # bir kez: depoyu kur
$ git status                        # her an: durum ne?
$ git add mat.c mat.h               # değişiklikleri sahneye al
$ git commit -m "kare fonksiyonu eklendi"
$ git log --oneline
a3f9c21 kare fonksiyonu eklendi
7b12e05 ilk derlenen sürüm
```

Sahne (staging) ilk bakışta gereksiz bir ara durak gibi gelir; değeri seçicilikte: beş dosya değiştirdin ama ikisi bir işe, üçü başka işe aitse, iki ayrı temiz commit yaparsın. Commit mesajı da geleceğe yazılmış telgraftır — "düzeltme" değil, "ne ve neden" (`git log`, altı ay sonra en çok okuduğun belge olur). Derleme çıktılarının (`*.o`, `uygulama`) tarihe girmemesi için proje köküne bir `.gitignore` koyarsın; ayrıntısı Bölüm 38'de.

### Dallar: paralel evrenler

Asıl güç dallarda. **Branch**, commit zincirinde ilerleyen isimli bir işaretçidir; yeni özelliği `main`'i kirletmeden ayrı çizgide geliştirir, bitince birleştirirsin:

```term
$ git switch -c yeni-kodek     # dal aç ve geç
$ ...değiştir, add, commit...
$ git switch main              # ana çizgiye dön (dosyalar o ana döner!)
$ git merge yeni-kodek         # dalı main'e birleştir
```

Birleştirmenin iki felsefesi vardır ve mülakatların favori sorusudur:

![Şekil 4.6: Aynı dallar, iki tarih. merge, iki çizgiyi iki ebeveynli bir birleşme commit'iyle bağlar — tarih çatallı ama dürüsttür. rebase, dalın commit'lerini main'in ucuna taşıyıp yeniden yazar — tarih düz ama yeniden yazılmıştır; commit'ler yeni kimlik (D', E') alır.](gorseller/b04_git_merge.png)

**merge** olan biteni olduğu gibi saklar: "iki koldan geliştirildi, burada birleşti." **rebase** ise dalını main'in ucuna taşıyıp commit'leri yeniden oynatır: tarih dümdüz okunur ama *yeniden yazılmıştır*. Pratik kural şudur: kendi makinendeki henüz paylaşılmamış dalını düzlemek için rebase serbest; **başkalarıyla paylaşılmış commit'leri asla rebase etme** — herkesin tarihini bozarsın. İki dal aynı satırı farklı değiştirdiyse git durur ve **çakışmayı (conflict)** sana bırakır: dosyada `<<<<<<<`/`>>>>>>>` işaretleri arasından doğru sürümü seçer, `add` + `commit` ile mühürlersin. Panik yok: çakışma hata değil, "iki insan aynı cümleyi düzeltti, hakem sensin" durumudur.

::: baglanti
Burada temeli attık: üç alan, commit, dal, merge/rebase. Perde arkası (git'in içindeki nesne modeli: blob/tree/commit), Git Flow gibi ekip stratejileri, `git bisect` ile hata avı ve CI/CD entegrasyonu **Bölüm 38**'de.
:::

## 4.8 Süreçler, izinler ve ortam

Terminalde çalıştırdığın her program bir **süreçtir (process)** ve Linux sana onların komuta merkezini verir. Uzun süren bir derlemeyi, takılan bir programı, arkada çalışması gereken bir sunucuyu yönetmek gündelik iştir:

```term
$ ./uzun_deney &                 # & : arka planda başlat
[1] 4172                         # iş no ve süreç kimliği (PID)
$ ps aux | grep deney            # çalışan süreçleri listele + süz
mert  4172  98.0  ./uzun_deney
      # sütunlar kısaltıldı; gerçek çıktıda VSZ, RSS, STAT vb. de var
$ kill 4172                      # nazikçe sonlandır (SIGTERM)
$ kill -9 4172                   # son çare: anında öldür (SIGKILL)
```

Klavye kısayollarıyla birleşince tablo tamamlanır: `Ctrl+C` öndeki süreci sonlandırır, `Ctrl+Z` *dondurur*; donmuş işi `bg` arka planda devam ettirir, `fg` öne getirir, `jobs` bekleyenleri listeler. SSH ile bağlandığın bir sunucuda saatlik eğitim koşturuyorsan bu beşli (`&`, `Ctrl+Z`, `bg`, `fg`, `jobs`) hayat sigortandır. `kill -9`'un "son çare" olması boşuna değil: süreç temizlik şansı bulamaz (Bölüm 2'deki `fclose` tamponlarını hatırla — diske inmeyen ne varsa gider).

**İzinler**, Bölüm 1'in bitlerinin dosya sistemindeki karşılığıdır. `ls -l` çıktısındaki `-rwxr-xr--` dizisi üç üçlü gruptur — sahip / grup / diğerleri; her üçlü oku-yaz-çalıştır bitleridir:

![Şekil 4.7: İzin bitleri. rwx üçlüsü bir binary sayıdır: r=4, w=2, x=1. Sahip rwx (7), grup r-x (5), diğerleri r-- (4) → chmod 754. Betiğini çalıştırılabilir yapan `chmod +x` aslında x bitini 1 yapan (OR ile kuran) bir bit işlemidir.](gorseller/b04_permissions.png)

`chmod +x betik.sh` artık senin için sihir değil: x bitini 1 yapıyor. `chmod 644 rapor.txt` (sahip okur-yazar, herkes okur) ya da `chmod 600 gizli.pem` (yalnız sahip; SSH anahtarlarının şartı) gibi sayısal kalıplar, üç binary sayıyı okuyabilen için ezber değil hesaptır.

Üçüncü bacak **ortam değişkenleri**: her sürecin yanında taşıdığı isim=değer çiftleri. En önemlisi `PATH` — kabuk, `gcc` yazdığında hangi dizinlerde arayacağını buradan öğrenir:

```term
$ echo $PATH
/usr/local/bin:/usr/bin:/bin
$ which gcc                      # PATH'te ilk nerede bulundu?
/usr/bin/gcc
$ export OZCE_VERI=/veri/deney1  # bu oturuma değişken tanımla
$ python3 kodek.py               # python içinden os.environ ile okunur
```

Meşhur soruyu da burada gömelim: neden `uygulama` değil `./uygulama`? Çünkü güvenlik gereği bulunduğun dizin `PATH`'te *yoktur* — `.` öneki "şu dizindekini kastediyorum" demenin açık yoludur. `export` edilen değişken alt süreçlere geçer; kalıcı olması istenirse `~/.bashrc`'ye yazılır. API anahtarları ve yollar gibi ayarları koda gömmek yerine ortamdan okumak, Bölüm 42'de container dünyasının da temel kuralı olacak.

## 4.9 Metin cerrahisi: find, sed, awk

4.2'nin boru hattı takımı satırları süzüyordu; bu üçlü ise dosya *ağacında* gezer ve metni *dönüştürür*. Elli dosyalık bir projede "şu fonksiyonun adı nerede geçiyor, hepsini değiştir" işinin araçlarıdır.

**`find`**, dizin ağacında ölçüte göre dosya arar; `xargs`, bulduklarını başka komuta argüman yapar:

```term
$ find . -name "*.c"                     # bu ağaçtaki tüm .c dosyaları
./main.c
./surucu/klavye.c
$ find . -name "*.o" -delete             # derleme artıklarını süpür
$ find . -name "*.c" | xargs grep -l "kstring"   # kstring geçen DOSYALAR
./surucu/klavye.c
```

`grep -r "desen" .` da özyineli arar; `find | xargs` ikilisinin gücü, aramayı ölçütlerle (ad, tür, tarih, boyut) sınırlandırabilmesidir.

**`sed`**, akış düzenleyicisidir (stream editor); ekmek kapısı tek kalıptır — `s/eski/yeni/g` (substitute, global):

```term
$ sed 's/kanal_kodla/kodla_kanal/g' kodek.c | head -3
      # önizleme: dosyaya dokunmaz
$ sed -i.bak 's/kanal_kodla/kodla_kanal/g' kodek.c
      # yerinde değiştir, .bak yedeği bırak
```

`-i.bak` uzantısı sed'in emniyet kemeridir: orijinali `kodek.c.bak` olarak saklar. Önce borulu önizleme, sonra `-i.bak` — bu iki adımlı disiplin, toplu değiştirmeyi korkulu rüya olmaktan çıkarır.

**`awk`**, sütunlu metnin dilidir; yüzlerce özelliği var ama günlük değeri tek kalıpta: `awk '{print $N}'` — N'inci sütunu bas. `ps aux | awk '{print $2}'` PID sütununu verir; `awk '$3 > 100 {print $1}'` üçüncü sütunu 100'ü aşan satırların ilk sütununu basar. `cut` sabit ayraçta yeterliyken, düzensiz boşluklarda awk kazanır.

Hangisi ne zaman? Şu tablo refleks olana kadar duvarında dursun:

| İş | Araç |
|---|---|
| Satır *bulmak* | `grep` |
| Dosya *bulmak* | `find` |
| Metni *değiştirmek* | `sed` |
| Sütun *seçmek / süzmek* | `awk` (basitse `cut`) |
| Bulunanları komuta *beslemek* | `xargs` |

## 4.10 Uzak depo: clone, push, pull

4.7'deki her şey — commit'ler, dallar, merge — senin makinende, `.git` klasöründe yaşıyordu. Ekip çalışması ve yedeklilik için bir kopyanın ortak bir sunucuda durması gerekir: **uzak depo (remote)**. GitHub bunun en bilineni; şirketlerde aynı işi kapalı ağdaki bir GitLab/Gitea sunucusu yapar — savunma sanayiinde kodun internete çıkmadığı için *sadece* bu iç sunucular vardır, ama komutlar birebir aynıdır:

![Şekil 4.8: Yerel ile uzak depo. clone ilk kopyayı indirir; commit'ler yerelde birikir; push onları uzağa gönderir; pull (= fetch + merge) başkalarının gönderdiklerini alır. Commit yereldir — push edene kadar kimse görmez.](gorseller/b04_git_remote.png)

Günlük döngü dört komuttur:

```term
$ git clone https://sunucu/ekip/mertos.git   # depo + tüm tarih iner
$ git pull                    # yenilikleri al (fetch + merge)
$ ...değiştir, add, commit...
$ git push                    # kendi commit'lerini gönder
$ git remote -v               # uzaklar: origin  https://sunucu/...
```

`origin`, clone sırasında uzak depoya verilen varsayılan takma addır — özel bir şey değil, `git remote add` ile kurulan bir isim. `pull`'un iki adım olduğunu bilmek önemlidir: `fetch` uzaktaki yenilikleri indirir (dosyalarına dokunmaz), `merge` senin dalınla birleştirir. Çakışma çıkarsa 4.7'de öğrendiğin süreç aynen işler — uzaklık, çakışmanın doğasını değiştirmez.

İki görgü kuralıyla kapatalım. **Push etmeden önce pull çek:** uzak depo senden ilerideyse push reddedilir; önce başkalarının işini al, birleştir, sonra gönder. **`main`'e doğrudan push, ekip işinde kabalıktır:** değişiklik dalda gelişir, gözden geçirme (code review) sonrası birleşir — GitHub'daki adı *pull request*'tir; bu akışın tamamı Bölüm 38'de.

::: ipucu
Kendine bugün bir GitHub hesabı aç ve `MertOS`'u push et — işe alımcıların ilk baktığı yer orasıdır. Kapalı ağda çalışacağın gün de aynı kaslar iş görecek; değişen tek şey sunucunun adresi.
:::

## 4.11 Kütüphaneler, editör ve uzak çalışma

Gerçek projelerde kod tek dosyada yaşamaz. Ortak kısımlar kütüphaneye konur ve birden çok program onu kullanır. Sunucularda ise grafik arayüz yoktur: kodu `ssh` üzerinden, terminalde açılan bir editörle yazarsın. Bu son konu, iki gerçeğin pratik tarafını kapatır: kütüphane nasıl yapılır, terminalde nasıl yazılır ve uzak makineye nasıl güvenle bağlanılır.

### Statik kütüphane (.a)

Kütüphane, birden çok `.o` dosyasının arşividir. **Statik kütüphane** (`.a`) bağlama anında programın içine kopyalanır: program tek başına çalışır, ama her program kendi kopyasını taşır. Windows'taki `.lib` dosyasının karşılığıdır. Örnek 2'deki `mat.c`'yi bir arşive koyalım:

```term
$ gcc -c mat.c                       # nesne dosyası
$ ar rcs libmat.a mat.o              # arşiv: kütüphane doğdu
$ gcc main.c -L. -lmat -o uygulama   # -L. buraya bak, -lmat = libmat.a
$ ./uygulama
81
```

`ar rcs` üç bayraktır: `r` ekle (varsa değiştir), `c` arşiv yoksa oluştururken uyarı verme, `s` bağlayıcının aramasını hızlandıran dizini yaz. `-L.` bağlayıcıya "kütüphaneyi şu dizinde ara" der; `-lmat` ise `libmat.a` demektir, `lib` öneki ve `.a` uzantısı kendiliğinden eklenir. Sıra önemlidir: `-lmat` kullanan `main.c` komutta kütüphaneden önce gelmelidir. `gcc -lmat main.c` çoğu Linux sisteminde `undefined reference` verir, çünkü bağlayıcı kütüphaneyi soldan sağa tarar ve henüz görmediği bir sembol için arşive geri dönmez.

### Paylaşımlı kütüphane (.so)

**Paylaşımlı kütüphane** (`.so`, Windows'taki DLL'in karşılığı) kodu programa kopyalamaz; program çalışırken yüklenir ve aynı kopya birden çok programca kullanılır. Bunun için kod konumdan bağımsız (`-fPIC`) derlenmelidir, çünkü aynı kod farklı programların belleğinde farklı adreslere yüklenebilir:

```term
$ gcc -fPIC -c mat.c -o mat.o
$ gcc -shared -o libmat.so mat.o
$ gcc main.c -L. -lmat -o uygulama
$ LD_LIBRARY_PATH=. ./uygulama      # çalışma anında bakılacak dizin
81
$ ldd ./uygulama                    # hangi .so'lara bağlı?
    libmat.so => ./libmat.so (0x...)
    libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x...)
```

Çalışma anında yükleyici (loader) `libmat.so`'yu nereden arayacağını bilmelidir. `LD_LIBRARY_PATH=.` bu oturuma geçici bir yol verir; kalıcı çözüm kütüphaneyi standart bir dizine (ör. `/usr/local/lib`) kurmaktır. `ldd` çıktısındaki adresler kısaltıldı.

`nm` bir nesne dosyasının ya da kütüphanenin sembol tablosunu döker. Sembol adının önündeki harf durumunu anlatır: `T` burada tanımlanmış (kodu olan) bir fonksiyon, `U` ise dışarıdan beklenen bir sembol demektir. Bağlama hatasını bu iki harfle okursun: bir yerde `U kare` var, hiçbir nesnede `T kare` yoksa `undefined reference` çıkar.

```term
$ nm -D libmat.so | grep kare
0000000000001149 T kare
$ nm main.o | grep kare
                 U kare
```

Adres değerleri makineye göre değişir; önemli olan `T` ve `U` harfleridir.

### Editör: vim'in hayatta kalma seti

Uzak bir sunucuda hangi editörün kurulu olduğunu bilemezsin; `vi` ya da `vim` neredeyse her Linux'ta bulunur. vim **iki modludur**: komut modunda tuşlar komut olur, ekleme modunda tuşlar yazı olur. Açılınca komut modundasın; `i` ekleme moduna geçirir, `Esc` komut moduna geri döndürür. Günlük hayatta yetecek komutlar şunlar:

| Tuş | Ne yapar |
|---|---|
| `i` | ekleme moduna geç, yazmaya başla |
| `Esc` | komut moduna dön |
| `:w` | kaydet |
| `:q` | çık (değişiklik yoksa) |
| `:q!` | kaydetmeden zorla çık |
| `:wq` | kaydet ve çık |
| `/kelime` | ileri doğru ara; `n` sonrakine atlar |

Sıkıştığında reçete tek satır: `Esc`, sonra `:q!` ve Enter. Bu komut değişikliklerini atar, ama vim'den çıkmanın her zaman işe yarayan yoludur.

### Kılavuz sayfaları: man bölümleri

`man` sayfaları bölüm numarasıyla çalışır ve aynı isim farklı bölümlerde farklı şeyi anlatabilir. `printf` hem kabuk komutu (bölüm 1) hem de C kütüphane fonksiyonu (bölüm 3) olarak var:

```term
$ man printf          # bölüm 1: kabuk komutu printf
$ man 3 printf        # bölüm 3: C'deki printf fonksiyonu
$ man 2 write         # bölüm 2: sistem çağrısı
```

Bölüm 2 sistem çağrılarıdır; programının çekirdeğe (kernel) gittiği kapılar. Bunlar Kısım VI'da (Bölüm 24-28) işlenecek. Mülakatta `printf`'in tanımını sorarlarsa doğru sayfa `man 3 printf`tir.

### SSH: anahtar, yapılandırma ve izin

Uzak makineye parolayla girmek yerine **anahtar çifti** kullanılır: özel anahtar (`id_ed25519`) yalnız sende kalır, açık anahtar (`.pub`) sunucuya konur. Sunucu açık anahtarı tutar ve yalnız karşılığı olan özel anahtarın sahibine kapıyı açar. Parola ağ üzerinden gönderilmez.

```term
$ ssh-keygen -t ed25519 -C "mert@laptop"
$ ls ~/.ssh
id_ed25519  id_ed25519.pub
$ ssh-copy-id kullanici@sunucu      # açık anahtarı sunucuya koy
```

`-t ed25519` günümüzün kısa ve güçlü anahtar türüdür; `-C` anahtara okunur bir not ekler. Özel anahtar dosyasını başkası okuyabiliyorsa SSH bağlantıyı reddeder (`UNPROTECTED PRIVATE KEY FILE` uyarısı). Bu yüzden `chmod 600 ~/.ssh/id_ed25519` ile yalnız sahibi okuyup yazabilmeli: `600` = `rw-------`. Özel anahtar parola kadar değerlidir; sızarsa sunucuya senin yerine girilir.

Her seferinde adres ve kullanıcı adı yazmamak için `~/.ssh/config` dosyası kullanılır:

```term
$ cat ~/.ssh/config
Host lab
    HostName 10.0.0.21
    User mert
    IdentityFile ~/.ssh/id_ed25519
$ ssh lab                           # artık tek kelime yeter
```

### Derleme ortamı: apt ve WSL2

Linux'ta derleyiciyi ve hata ayıklayıcıyı paket yöneticisiyle kurarsın. `sudo` komutu yönetici (root) yetkisiyle çalıştırır; `apt`, Debian ve Ubuntu ailesinin paket yöneticisidir. `build-essential` gcc, make ve temel başlık dosyalarını getiren bir **metapakettir** (başka paketleri çeken paket); `gdb` ayrı kurulur.

```term
$ sudo apt update                    # paket listesini tazele
$ sudo apt install build-essential gdb
$ gcc --version                      # derleyici hazır mı?
```

Windows'taysan bu komutların tamamı WSL2 içindeki Ubuntu'da çalışır. Windows'un kendi derleyicisi farklı bağlayıcı ve farklı C ortamı kullanır; C'de `long` Windows 64-bit'te 4 bayt (LLP64 modeli), Linux 64-bit'te 8 bayttır. gdb, valgrind ve AddressSanitizer gibi araçlar Linux'ta yaşar; bu yüzden bu bölümdeki her komutu WSL2 içinde çalıştır.

## Çözümlü Örnekler

### Örnek 1 (★): Boru hattıyla log analizi

**Adım 1 — Anla.** `sistem.log` dosyasında binlerce satır var; `HATA` içeren satırlardaki hata türlerinin hangi sıklıkta geçtiğini, en sıktan aza sıralı dök. Satır biçimi: `12:04:31 HATA sensor-zamanasimi`.

**Adım 2 — Örnekle.** Önce dört satırlık bir deneme günlüğü kuralım (`mini.log`). Mantık gerçek dosyada da aynıdır; yalnız satır sayısı değişir:

```term
$ cat mini.log
12:04:31 HATA sensor-zamanasimi
12:04:35 BILGI kanal-acildi
12:04:35 HATA baglanti-koptu
12:05:02 HATA sensor-zamanasimi
```

**Adım 3 — Kaba çöz.** Tek dev komut yazmaya çalışmam; hattı halka halka kurar, her halkada çıktıya bakarım. Süz (`grep`) → alanı seç (`cut`) → sırala (`sort`) → say (`uniq -c`) → sayıya göre sırala (`sort -nr`). `uniq`'in yalnız *ardışık* tekrarları saydığını bildiğimden, öncesine `sort` koymak şart.

Hattı adım adım büyütelim:

```term
$ grep "HATA" sistem.log | head -3        # 1) önce süzgü doğrula
12:04:31 HATA sensor-zamanasimi
12:04:35 HATA baglanti-koptu
12:05:02 HATA sensor-zamanasimi

$ grep "HATA" sistem.log | cut -d" " -f3 | head -3   # 2) türü ayıkla
sensor-zamanasimi
baglanti-koptu
sensor-zamanasimi

$ grep "HATA" sistem.log | cut -d" " -f3 | sort | uniq -c | sort -nr
     41 sensor-zamanasimi
     17 baglanti-koptu
      3 disk-dolu
```

**Adım 4 — Örüntü.** Bu hattın kalıbı her log analizinde aynıdır: *süz → ayıkla → sırala → say → sırala*. Her halka tek iş yapar ve bir öncekinin çıktısını alır; ölçütü değiştirmek (ör. yalnız `12:04` dakikası) yalnız bir halkayı değiştirmek demektir.

**Adım 5 — İyileştir.** Beş küçük program, hiçbiri diğerini tanımadan bir analiz aracı oluşturdu — Unix felsefesi budur. `cut -d" " -f3` boşluk ayraçlı üçüncü alanı alır; `sort` aynı türleri yan yana getirir ki `uniq -c` sayabilsin; `sort -nr` sayısal (`-n`) ve tersten (`-r`) sıralar. Aynı işi C ile yazsan: dosya okuma, string bölme, sayaç tablosu... Bölüm 2'nin emeği. Doğru araç seçimi de mühendisliğin parçası: *keşif ve tek seferlik analiz kabukta, kalıcı ve hızlı iş C'de, ikisinin arası Python'da.*

Aynı işi tek süreçte, `awk` ile de yapabilirsin; süzme ve alan seçme tek adımda birleşir:

```term
$ awk '$2 == "HATA" {print $3}' sistem.log | sort | uniq -c | sort -nr
```

**Adım 6 — Doğrula.** Mini günlük üzerinde her aşamanın çıktısını elle izleyelim; önce kendin tahmin et, sonra karşılaştır:

| Aşama | Çıktı |
|---|---|
| `grep "HATA"` | 3 satır (2. satır BILGI olduğu için elenir) |
| `cut -d" " -f3` | sensor-zamanasimi, baglanti-koptu, sensor-zamanasimi |
| `sort` | baglanti-koptu, sensor-zamanasimi, sensor-zamanasimi |
| `uniq -c` | 1 baglanti-koptu, 2 sensor-zamanasimi |
| `sort -nr` | 2 sensor-zamanasimi, 1 baglanti-koptu |

Sayıların toplamı (3), `grep -c HATA mini.log` çıktısına eşit olmalı; bu, sayımın hiçbir satırı kaçırmadığının en ucuz kanıtıdır.

**Bunu AI'sız yazabilir misin?** Aynı hatta bir halka ekle: yalnız `12:04` dakikasındaki hataları saydır. Hangi halkanın *önüne*, hangi komut gelir?

### Örnek 2 (★★): Çok dosyalı derleme ve undefined reference

**Adım 1 — Anla.** Üç dosyalık mini projeyi (`main.c`, `mat.c`, `mat.h`) önce *bilerek yanlış*, sonra doğru derle; iki hata türünü (derleme vs bağlama) kendi terminalinde üret ve oku.

**Adım 2 — Örnekle.** Önce tek bir dosyayla ısınalım: `gcc -c mat.c` sessizce `mat.o` üretir ve bağlama henüz yok. Tanım dosyası kendi başına derlenebiliyor.

**Adım 3 — Kaba çöz.** 4.4'ün haritasını deneye çeviriyorum. `main.c` yalnız başına derlenirse ne olur? Ön işlemci `mat.h`'yi yapıştırır, derleyici imzayı görür, itiraz etmez; ama bağlayıcı `kare`'nin gövdesini arayıp bulamaz — hata `ld`'den gelmeli. Doğrusu: her `.c`'yi ayrı ayrı `.o`'ya derle, sonda bağla.

Dosyalar ve deney sırasıyla:

```c
/* mat.h — sözleşme (prototip) */
int kare(int x);

/* mat.c — tanım */
int kare(int x) { return x * x; }

/* main.c — kullanım */
#include <stdio.h>
#include "mat.h"                 /* "": önce bu dizine bak */

int main(void) {
    printf("%d\n", kare(9));
    return 0;
}
```

```term
$ gcc main.c -o uygulama              # EKSİK: mat.c masada yok
/usr/bin/ld: ...: undefined reference to `kare'
$ gcc -c main.c                       # 1) main.o üret (bağlama yok)
$ gcc -c mat.c                        # 2) mat.o üret
$ gcc main.o mat.o -o uygulama        # 3) bağla: herkes masada
$ ./uygulama
81
```

**Adım 4 — Örüntü.** Çok dosyalı projenin kalıbı: her `.c` kendi `.o`'suna derlenir, sonda tüm `.o`'lar tek seferde bağlanır. Başlık dosyası (`.h`) yalnız sözleşmeyi (imzayı) taşır; gövde her zaman bir `.c` dosyasında yaşar.

**Adım 5 — İyileştir.** İlk komutun hatası derleyiciden değil `ld`'den (bağlayıcı) geliyor — 4.4'teki ayrımın kanıtı. `#include "mat.h"` çift tırnaklıdır: `< >` sistem dizinlerine, `" "` önce projenin kendi dizinine bakar. Ayrı `-c` adımlarının ödülü şu: `mat.c` değişince yalnız `mat.o`'yu yeniden üretip bağlarsın; `main.o` olduğu gibi durur. Bu tasarruf üç dosyada komik, `MertOS`'un elli dosyasında hayat — ve tam olarak make'in otomatikleştirdiği şey.

Not: `kare`'nin prototipini silersen (aşağıdaki soruya bak) GCC 14 ve sonrası bunu derleme aşamasında "implicit declaration" hatasıyla keser; GCC 13 uyarı verip geçer ve hatayı bağlamaya bırakır. `undeclared` ise tanımsız değişken mesajıdır.

**Adım 6 — Doğrula.** Her komutun neyi ürettiğini tabloda izle:

| Komut | Üretilen | Aşama |
|---|---|---|
| `gcc main.c -o uygulama` (`mat.c` komutta yok) | hata, çıktı yok | bağlama (`ld`) |
| `gcc -c main.c` | `main.o` | derleme ve çevirme |
| `gcc -c mat.c` | `mat.o` | derleme ve çevirme |
| `gcc main.o mat.o -o uygulama` | `uygulama` (çalışınca 81) | bağlama |

**Bunu AI'sız yazabilir misin?** `mat.h`'deki prototipi silip ilk komutu tekrar çalıştır: bu kez hata hangi aşamadan gelir, mesaj neden farklıdır?

### Örnek 3 (★★): TODO avı ve güvenli toplu değiştirme

**Adım 1 — Anla.** Çok dosyalı projende (a) içinde `TODO` geçen dosyaları ve toplam TODO sayısını bul; (b) `eski_kodla` fonksiyon adını bütün `.c`/`.h` dosyalarında `kodla` yap — ama önce önizleyerek ve yedek bırakarak.

**Adım 2 — Örnekle.** Önce tek dosyada deneyelim: `grep -c TODO main.c` kaç satırda geçtiğini sayar, `grep -n` ise satır numarasını da verir.

**Adım 3 — Kaba çöz.** (a) "dosya bulmak" `find`, "satır bulmak" `grep`; ikisini `xargs` evlendirir. Sayı için `grep`'in kendi sayacı (`-c` dosya başına, toplam için boruya `wc -l`). (b) Toplu değiştirme üç aşamalı disiplin ister: önce *hangi dosyalar* etkilenecek (`grep -l`), sonra *nasıl görünecek* (borulu `sed` önizleme), en son *yedekli* gerçek değişiklik (`sed -i.bak`).

```term
$ find . -name "*.[ch]" | xargs grep -n TODO   # (a) nerede, hangi satır
./main.c:42:    // TODO: hata yolunu test et
./surucu/klavye.c:7:  // TODO: uzun basma
$ find . -name "*.[ch]" | xargs grep -c "TODO" | grep -v ":0"
./main.c:1
./surucu/klavye.c:1

$ grep -rl "eski_kodla" --include="*.[ch]" .      # (b1) etkilenecekler
./kodek.c
./kodek.h
$ sed 's/eski_kodla/kodla/g' kodek.c | head -3   # (b2) önizle
int kodla(const bayt *veri, size_t n);
$ grep -rl "eski_kodla" --include="*.[ch]" . \
      | xargs sed -i.bak 's/eski_kodla/kodla/g'   # (b3) uygula
$ grep -r "eski_kodla" --include="*.[ch]" .       # doğrula: boş = temiz
$ make && rm -f *.bak                    # derliyorsa yedekleri at
```

**Adım 4 — Örüntü.** Toplu işin kalıbı: *bul → önizle → uygula → doğrula*. Her adım bir öncekinin güvenliğini artırır; önizlemeyi atlayan, yanlış dosyaya yazdığını ancak derleme patlayınca fark eder.

**Adım 5 — İyileştir.** `*.[ch]` deseni tek yakalamada `.c` ve `.h` uzantılarını seçer. (b)'nin üç aşaması bir güvenlik merdivenidir: liste → önizleme → yedekli uygulama; son adımdaki `make` ise en dürüst doğrulamadır — derlenmeyen bir toplu değiştirme, `git`'te tarihe girmeden yakalanır. Zaten en büyük emniyet ağın da git'in kendisi: değişiklik commit'lenmemiş hâldeyken `git diff` ile satır satır incelenir, felaket hâlinde `git restore .` her şeyi geri alır.

**Adım 6 — Doğrula.** Her aşamanın beklenen sonucunu tabloya yaz, sonra gerçek çıktıyla karşılaştır:

| Aşama | Komut | Beklenen sonuç |
|---|---|---|
| (a) satır | `grep -n TODO` | `main.c` ve `klavye.c` satırları |
| (b1) liste | `grep -rl` | `kodek.c` ve `kodek.h` |
| (b2) önizleme | `sed` (dosyaya yazmadan) | dosya değişmez, çıktıda `kodla` |
| (b3) uygulama | `sed -i.bak` | `kodek.c.bak`, `kodek.h.bak` oluşur |
| doğrulama | `grep -r` | boş çıktı |
| derleme | `make` | hata yok; sonra `rm -f *.bak` |

**Bunu AI'sız yazabilir misin?** Aynı avı yalnız *yorum satırlarındaki* TODO'lar için yap (`//` ile başlayanlar). Hangi halkaya hangi deseni eklersin — `grep`'e mi, `awk`'a mı?

### Örnek 4 (★★★): gdb ile çökme avı

**Adım 1 — Anla.** Aşağıdaki program argümansız çalıştırılınca çöküyor. `printf` eklemeden, yalnız gdb ile çökme noktasını ve kök nedeni bul.

```c
#include <stdio.h>

int say(const char *s, char hedef) {
    int n = 0;
    while (*s) {                 /* '\0' görene dek yürü */
        if (*s == hedef) n++;
        s++;
    }
    return n;
}

int main(int argc, char **argv) {
    const char *kelime = argv[1];        /* argüman verilmediyse?.. */
    printf("%d\n", say(kelime, 'a'));
    return 0;
}
```

**Adım 2 — Örnekle.** Önce belirtiyi iki çağrıyla sabitle: `./sayac` argümansız çöker; `./sayac elma` ise `1` basar, çünkü `elma` içinde `a` bir kez geçer.

**Adım 3 — Kaba çöz.** Aynı koşulu gdb altında koşturup çökme anını yakalayacağım. Çökünce `backtrace` bana *nerede* sorusunu, `print` ile değişken sorgusu *neden* sorusunu cevaplatacak. Oturum, satırı satırına:

```term
$ gcc -Wall -g sayac.c -o sayac
$ gdb ./sayac
(gdb) run
Program received signal SIGSEGV, Segmentation fault.
0x0000555555555151 in say (s=0x0, hedef=97) at sayac.c:5
5           while (*s) {
(gdb) backtrace
#0  say (s=0x0, hedef=97) at sayac.c:5
#1  main (argc=1, argv=0x7fffffffe0a8) at sayac.c:14
(gdb) print s
$1 = 0x0
(gdb) frame 1
(gdb) print argv[1]
$2 = 0x0
```

**Adım 4 — Örüntü.** Çöken satır çoğu zaman tanıktır; kusur, o satıra bozuk değer taşıyan çağrı zincirinde aranır. Kalıp üç soru: *nerede çöktü → değer ne → kim verdi?* Bu üçlü her gdb oturumunda aynıdır.

**Adım 5 — İyileştir.** Rapor kendini okuyor: çökme `say` içinde, 5. satırda; `s=0x0` — yani `NULL` izlenmiş (Bölüm 2'nin uyarısı). Ama asıl ders `backtrace`'in ikinci satırında: `argc=1`, yani argüman hiç verilmemiş; `argv[1]` `NULL`. **Çöken satır suçlu değil, tanık** — kusur, `main`'in `argc`'yi kontrol etmeden `argv[1]`'i kullanması. Düzeltme üç satır: `if (argc < 2) { fprintf(stderr, "kullanım: %s kelime\n", argv[0]); return 1; }`. gdb'nin sana verdiği şey kanıt zinciridir; hükmü veren yine sensin.

**Adım 6 — Doğrula.** Çağrıları ve düzeltilmiş hâli elle izle; her satır, gdb'de gördüğün değerlerle örtüşmeli:

| Çağrı | argc | argv[1] | `say`'e giden `s` | Sonuç |
|---|---|---|---|---|
| `./sayac` | 1 | yok (NULL) | NULL | SIGSEGV, çöker |
| `./sayac elma` | 2 | "elma" | "elma" | `1` basar |
| düzeltilmiş `./sayac` | 1 | kontrol edilir | — | kullanım mesajı, çıkış kodu 1 |

**Bunu AI'sız yazabilir misin?** `break say` koyup `run mert` ile başlat; `next` ile döngüyü üç tur izle ve her turda `print *s` ile `print n` çıktılarını önceden tahmin et. Tahminin tutmuyorsa, zihinsel modelin nerede yanlış?

## Kendin Yap Projeleri

::: dikkat
Kural değişmedi: yapay zekâ araçları **yasak**. Bu bölümün projeleri küçük ama günlük hayatına gireceklerin provası — kendi ellerinle kur ki reflekse dönüşsün.
:::

### Proje 1 (★★): Tarih damgalı yedek betiği

**Amaç:** Verilen proje dizinini `yedekler/` altına tarih damgalı arşiv olarak kaydeden bir bash betiği: `./yedekle.sh projeler/ozce` → `yedekler/ozce_2026-07-20_1432.tar.gz`.

**Beklenen davranış:** Argüman yoksa kullanım mesajı basıp `exit 1`; verilen dizin yoksa hata mesajı (stderr'e!) ve `exit 1`; başarıda oluşan dosyanın adını ve boyutunu yazdır.

**Önerilen yaklaşım:** Tarih için `date +%F_%H%M` komutunu bir değişkene al (komut çıktısını değişkene almanın sözdizimini `man date` sayfasının altındaki örneklerde ve bash'in `$(...)` yapısında ara — bulma süreci de ödevin parçası). Arşivleme `tar czf hedef.tar.gz dizin`. Dizin adındaki `/` sonekini ve boşluklu adları düşün: değişkenlerini tırnakla.

**Başarı kriterleri:** Argümansız çağrıda `$?` 1; olmayan dizinde stderr'e mesaj (stdout'a değil — `2>/dev/null` ile ayırt et); iki kez üst üste çalıştırınca iki farklı dosya oluşuyor; boşluklu dizin adıyla da çalışıyor.

### Proje 2 (★★★): MertOS-vari Makefile

**Amaç:** Örnek 2'nin üç dosyalı projesini büyüt (`main.c`, `mat.c`, `metin.c`, ortak `util.h`) ve elle derlemeyi tamamen bırak: değişkenli, kalıp kurallı, temizlikli bir Makefile yaz.

**Beklenen davranış:** `make` her şeyi kurar; ikinci `make` "up to date" der; `touch util.h` sonrası yalnız gerekenler derlenir; `make clean` tüm üretilenleri siler; `make CFLAGS="-O2"` ile bayrak dışarıdan değişebilir.

**Önerilen yaklaşım:** Önce Örnek 2'nin açık kurallarıyla yaz, çalıştığını gör. Sonra üç `.o` kuralının aynı kalıbı tekrarladığını fark et ve Kod Okuma'daki `%.o: %.c` kalıbıyla `$@`/`$<` otomatik değişkenlerini kullanarak teke indir. `clean`'i `.PHONY`'ye eklemeyi unutma; dizine `clean` adında dosya koyup neden gerektiğini bizzat gör.

**Başarı kriterleri:** Sıfırdan kurulum tek komut; değişmeyen dosya asla yeniden derlenmiyor (`make`'in çıktısını okuyarak kanıtla); Makefile 20 satırın altında; TAB/boşluk hatası yok; `git`'e `.o`'lar ve çalıştırılabilir girmiyor (`.gitignore` yazdın).

### Ek Alıştırmalar

Aşağıdaki on bir problemin cevabı bu bölümde yok; bilerek kısa tuttum. Önce kendin düşün, sonra terminalde dene. Mülakat sorusu olanlar **(mülakat)** etiketiyle işaretli.

1. **★** Bir `access.log` dosyasında her satırın ilk alanı IP adresidir. Her IP'nin kaç kez geçtiğini, en çoktan en aza doğru tek bir boru hattıyla listele.
2. **★ (mülakat)** Yalnız `awk` kullanarak bir dosyadaki satır sayısını bul; `wc` kullanma. Dosya boşken de doğru sonucu vermeli.
3. **★★** `$1` ile verilen bir dizindeki `.c` dosyalarının toplam satır sayısını yazan bir bash betiği yaz. Boşluk içeren dosya adlarında da çalışmalı.
4. **★★ (mülakat)** Bir bash betiği `$1` sayısının asal olup olmadığını söylesin: asalsa `exit 0`, değilse `exit 1`. `[` koşulunun boşluk kuralını unutma.
5. **★★ (mülakat)** İki `.c` dosyasının ikisi de `main` tanımlıyor ve `gcc a.c b.c` çalıştırılıyor. Hata hangi aşamada çıkar ve mesajın başında ne yazar? Cevabı derlemeden önce düşün.
6. **★★** Bir `.c` dosyasında `#define N 10` var. `gcc -E` çıktısında `N` nereye gitti? Sonra `gcc -S` ile assembly'de `10` sayısının nerede göründüğünü bul.
7. **★★** Bir programın sonsuz döngüde takıldığını varsay. `gdb` altında çalıştırıp `Ctrl+C` ile durdurduğunda programın nerede olduğunu hangi komutla görürsün ve çıktıyı nasıl okursun?
8. **★★★ (mülakat)** Büyük bir log dosyasında tekrar eden satırları `sort` ve `uniq` kullanmadan, tek geçişte `awk` ile bul. Her satırı ilk gördüğünde bir dizide (associative array) işaretle; bellek kullanımını düşün.
9. **★★** Makefile'a `test` adında bir hedef ekle; `./uygulama` çalıştırsın ve `uygulama`ya bağımlı olsun. Dizinde `test` adında bir dosya yaratıp make'in tepkisini gözle, sonra `.PHONY` ile düzelt.
10. **★★ (mülakat)** Paylaşılmış bir commit'i geri almak istiyorsun. `git reset` mi `git revert` mi? Gerekçeni yaz ve hangisinin tarihi yeniden yazdığını söyle.
11. **★★** Bir betiğin izinleri `-rwxr-x---`. Bu izni sayısal forma çevir; ardından `chmod 640 rapor.txt` komutunun her grup için etkisini bit bit yaz. `bash betik.sh` ile çalıştırırsan x biti şart olur mu?

## Kod Okuma Egzersizi

Bugünkü kesit, milyonlarca sunucuda çalışan **Redis 7.2**'nin `src/Makefile` dosyasından alındı; **sadeleştirilmiş kesit**tir: nesne (`.o`) listesi dokuz dosyaya indirildi, bağlama tarifinde gömülü kütüphane (hiredis, Lua, hdr_histogram, fpconv) ve `$(FINAL_LIBS)` öncesindeki ek bağlantılar çıkarıldı, `clean` tarifi tek satıra kısaltıldı. Sanayi ölçeğinde bir projenin, bu bölümde kurduğun make fikrini nasıl kullandığına bak:

```makefile
REDIS_SERVER_NAME = redis-server
REDIS_SERVER_OBJ  = adlist.o ae.o anet.o dict.o server.o sds.o \
                    quicklist.o zmalloc.o networking.o

%.o: %.c .make-prerequisites
	$(REDIS_CC) -MMD -o $@ -c $<

$(REDIS_SERVER_NAME): $(REDIS_SERVER_OBJ)
	$(REDIS_LD) -o $@ $^ $(FINAL_LIBS)

clean:
	rm -rf $(REDIS_SERVER_NAME) *.o *.d

.PHONY: clean
```

**Sorular — cevaplamadan geçme:**

- `%.o: %.c` kalıp kuralı ne diyor? Bu tek kural, listedeki dokuz `.o` için kaç açık kuralın yerine geçiyor?
- Otomatik değişkenleri çöz: tarifteki `$@`, `$<` ve `$^` sırasıyla neyin yerini tutar? (İpucu: hedef, ilk bağımlılık, tüm bağımlılıklar — hangisi hangisi, kuraldan doğrula.)
- Satır sonundaki `\` ne işe yarıyor ve neden dokuz `.o` tek satıra yazılmamış?
- `-MMD` bayrağı her `.o`'nun yanına bir `.d` dosyası üretir; `clean`'in `*.d` silmesinden ne işe yaradıklarını çıkar. Senin Proje 2'ndeki hangi eksikliği (başlık dosyası bağımlılıklarını elle yazmak) otomatikliyor olabilir?
- Bağlama kuralı neden `$(REDIS_SERVER_OBJ)` bitmeden çalışamaz? make bunu nereden biliyor?

## Bölüm Özeti

Kısım I'in son bölümünde atölyeyi kurduk:

- **Dosya sistemi tek ağaçtır**: mutlak yol kökten (`/`), göreli yol bulunduğun yerden; `~` evin, `..` üst dizin. `rm` geri dönüşsüzdür — iki kez oku, bir kez bas.
- **Üç akış** (stdin/stdout/stderr) yönlendirilebilir (`>`, `>>`, `2>`, `<`); **boru** (`|`) küçük araçları zincirler. `grep`, `sort`, `uniq -c`, `cut`, `head` beşlisiyle log analizi tek satırdır.
- **Bash betiği** = otomatikleşmiş terminal: `$1` argüman, `$?` çıkış kodu, `[ ]` test (boşluklar zorunlu), değişkenler tırnaklı kullanılır. Tekrarlanan her iş betiği hak eder.
- **gcc dört aşamadır**: ön işleme (`#`'ler açılır) → derleme (assembly) → çevirme (`.o`) → bağlama (çalıştırılabilir). prototipsiz fonksiyon çağrısı GCC 14'te derleme hatası (GCC 13'te uyarı), `undefined reference` ise bağlama hatasıdır — mesajın kaynağı, bakacağın yeri söyler.
- **gdb** `-g` ile derlenmiş programı durdurur ve konuşturur: `break/run/next/print/backtrace`. Çöken satır çoğu zaman tanıktır, suçlu çağrı zincirinin yukarısındadır.
- **make**, bağımlılık grafı + zaman damgasıyla yalnız değişeni derler: `hedef: bağımlılıklar` + TAB'lı tarif; değişkenler, `%.o: %.c` kalıbı, `$@`/`$<`, `.PHONY`.
- **git üç alandır**: çalışma dizini → (add) → sahne → (commit) → depo. Dal paralel evren, merge dürüst çatallı tarih, rebase düz ama yeniden yazılmış tarih; paylaşılan commit rebase edilmez.
- **Süreç yönetimi**: `&`, `Ctrl+Z`/`bg`/`fg`/`jobs`, `ps`, `kill` (−9 son çare). **İzinler** üç binary üçlüdür (rwx → 7/5/4); **PATH** komutların arandığı yerdir, `./` bu yüzden gerekir; ayarlar ortam değişkenlerinden okunur.
- **Metin cerrahisi**: dosya bulmak `find`, satır bulmak `grep`, değiştirmek `sed` (önizle → `-i.bak`), sütun işi `awk`, besleme `xargs`.
- **Uzak depo**: `clone` ilk kopya, `push` gönderir, `pull` = `fetch` + `merge`; `origin` bir takma addır. Commit yereldir — push edene kadar kimse görmez; push'tan önce pull.
- **Kütüphane, editör, uzak makine**: statik `.a` (`ar rcs`) bağlama anında kopyalanır, paylaşımlı `.so` (`-fPIC -shared`) çalışma anında yüklenir; vim'de `i`, `Esc`, `:wq` yeter; uzak girişte `ssh-keygen -t ed25519` ve özel anahtara `chmod 600`.

**Sonraki bölümde:** Diller ve aletler tamam — Kısım I kapandı. Şimdi asıl mesele başlıyor: elinde derleyici, hafızanda sözdizimi varken bir problemin karşısında *nereden başlayacağını* bilmek. **Bölüm 5 — Problemi Parçala** ile Kısım II'ye geçiyoruz: girdi-çıktı tanımlama, kısıt analizi, brute force'tan optimizasyona giden yol.

::: mulakat
Klasik sorular — hemen cevaplamaya çalışma, her birini birkaç dakika düşün:

1. `#include <stdio.h>` satırı derleme sürecinin hangi aşamasında, ne yapılarak işlenir?
2. `undefined reference` hatası neden `-c` ile derlerken değil de son adımda çıkar? Hatayı veren program hangisidir?
3. `ls -l | grep ".c" > liste.txt` komutunda veriler hangi sırayla, hangi akışlardan geçer? `grep`'in hata mesajı `liste.txt`'ye yazılır mı?
4. make bir hedefi yeniden üretip üretmeyeceğine neye bakarak karar verir? `clean` neden `.PHONY` olmalıdır?
5. merge ile rebase'in tarihe etkisini anlat: hangi durumda hangisini seçersin ve paylaşılmış dalda rebase neden yasaktır?
6. `chmod 754 betik.sh` tam olarak hangi izinleri verir? Rakamları bit bit açarak göster.
7. `git pull` neden tek komut değildir — hangi iki adımdan oluşur ve push reddedildiğinde ("rejected: non-fast-forward") doğru hamle nedir?
:::
