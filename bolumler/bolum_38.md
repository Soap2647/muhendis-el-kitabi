%% kisim_no: X
%% kisim_ad: Yazılım Mühendisliği Pratiği
%% kisim_ayrac: evet
%% bolum_no: 38
%% baslik: Git Derinlemesine

## Giriş: Tarihçe bir veritabanıdır

Bölüm 4'te git'i kullanmayı öğrendin: `add`, `commit`, `branch`, `merge`, `push`. Bu komutlar günlük işi görür. Ama bir gün `merge` çakışma bildirdiğinde, bir commit'i yanlışlıkla kaybettiğinde ya da `push` reddedildiğinde "komutu biliyorum" demek yetmez. Gerekçeyi bilmen gerekir: git bu işleri perde arkasında nasıl yapıyor?

Bu bölümde perdeyi kaldırıyoruz. Önce git'in kendi deposuna, yani `.git` klasörünün içine bakacağız. Orada dosya diye bir şey yok; yalnızca içeriğin özetiyle adreslenen nesneler ve bu nesnelere isim veren küçük işaretçi dosyaları var. Bu yapının üstüne üç ağaç modeli, birleştirme ve yeniden yazma (rebase) mantığı, diff algoritmaları, paketleme (packfile) ve uzak depo akışları kurulu. Son olarak bu araçları ekip düzeyinde nasıl kullanacağını göreceksin: iş akışları, commit disiplini, yerel kancalar (hook) ve hata avında git.

Neden önemli? Savunma sanayiinde ve büyük ekiplerde kod yıllarca süren bir tarihçedir. Bir sürümün hangi commit'ten geldiğini, bir regresyonun hangi değişiklikle girdiğini ve bir gereksinimin hangi koda ve hangi teste bağlandığını kanıtlamak zorunda kalabilirsin. Bu kanıt tarihçeden gelir ve tarihçenin nasıl tutulduğunu bilmeyen biri onu sağlayamaz. Mülakatta da "rebase ile merge arasındaki fark nedir?" sorusu neredeyse her zaman gelir. Cevabı ezberden değil, nesne modelinden kurarsan şaşırmazsın.

Kendi projelerinde de aynı şey geçerli. MertOS gibi bir projede bir sürücü değişikliğinin üç ay önce hangi commit'le girdiğini bulmak istersen Bölüm 6'daki `git bisect` ile ikili arama yapabilirsin. Ama bunun işe yaraması için commit'lerin küçük ve anlamlı olması gerekir. Bu bölüm o disiplinin mekanizmasını da anlatıyor.

Bir çalışma notu: bu bölümdeki her komut ve çıktı, Temp klasörü altında kurduğumuz deneme depolarında çalıştırılıp kaydedildi. Hash'ler yazar, bırakan ve zaman damgasına bağlıdır; bu yüzden deneylerdeki tüm commit'lerde `GIT_AUTHOR_DATE` ve `GIT_COMMITTER_DATE` ortam değişkenlerini sabitledik. Kendi denemende tarihleri sabitlemezsen aynı komutlar farklı hash'ler üretir; bu bir hata değil, zaman damgasının hash'e girmesinin sonucudur. Komutlar Git Bash ya da WSL'deki Bash içindir; PowerShell'de ortam değişkeni sözdizimi farklıdır. Çıktılar Git 2.52.0 (Windows) ile alındı; WSL Ubuntu'daki Git 2.43.0 ile de aynı commit ve ağaç hash'lerinin üretildiğini ayrıca kontrol ettik. Komut çıktısının metni (ör. birleştirme mesajları) sürümler arasında değişebilir, ama nesne biçimi kararlıdır.

::: not
Git'i iki cümlede anlatmak gerekirse: içeriğin özetiyle adreslenen bir nesne deposu ve bu nesneleri gösteren isim işaretçilerinden (dallar, HEAD, etiketler) oluşan bir sistemdir. Commit'ler, dallar, birleştirme, yeniden yazma ve paketleme, hepsi bu iki parçanın kombinasyonudur.
:::

## 38.1 Nesne deposu: blob, tree, commit ve tag

Her git deposu `.git` klasöründen ibarettir. Boş bir depoda bu klasörün içinde `objects` dizini vardır ve içinde yalnızca iki alt klasör bulunur: `info` ve `pack`. Henüz hiçbir nesne yoktur. İlk nesneyi yazdığında, nesnenin adının ilk iki hanesiyle bir alt klasör açılır ve dosya o klasörün içine düşer. Bunun nedenini birazdan göreceksin.

Git dört tür nesne saklar:

| Tür | Ne saklar? | Örnek içerik |
|---|---|---|
| **blob** | Bir dosyanın ham baytları. Dosya adı yoktur | `int kare(int x)...` |
| **tree** (ağaç) | Bir dizinin anlık görüntüsü: `izin ad hash` girdileri | `mat.c` ve `mat.h` girdileri |
| **commit** | Bir tree'ye, ebeveyn commit'lere, yazar ve mesaja işaret eden kayıt | `tree d931…`, `parent dda4…` |
| **tag** (etiket) | Bir nesneye ad verir; açıklamalı etikette yazar, tarih ve mesaj da taşınır | `object a959…`, `type commit` |

Bu tabloda bir şeyi fark etmiş olmalısın: blob'un dosya adı yok. Ad, tree'nin içindeki girdide yaşıyor. Bölüm 28.9'da Unix dosya sisteminde dosya adının inode'da değil dizin girdisinde durduğunu görmüştük. Git aynı ayrımı yapar ve bu ayrım, aynı içeriğin farklı adlarla tek bir blob olarak saklanmasını sağlar.

Nesnenin adı, içeriğinin SHA-1 özetidir. Bölüm 9.1'de "adresi veriden üretmek" fikrini gördün; git bunu nesne deposuna uygular. Sonuç iki yönlü bir garanti verir: aynı içerik her zaman aynı adı alır (tekilleştirme), farklı içerik farklı adı alır (bütünlük). Deneyelim. Önce bir klasör açıp dosyayı yazıyoruz:

```term
$ git --version
git version 2.52.0.windows.1
$ git init -q -b main nesne && cd nesne
$ printf 'merhaba\n' > selam.txt
$ git hash-object selam.txt
e995d8e1c89654fd0a6453c2da61fb6e9da262e6
$ git hash-object -w selam.txt
e995d8e1c89654fd0a6453c2da61fb6e9da262e6
$ find .git/objects -type f
.git/objects/e9/95d8e1c89654fd0a6453c2da61fb6e9da262e6
$ git cat-file -t e995d8e1c89654fd0a6453c2da61fb6e9da262e6
blob
$ git cat-file -s e995d8e1c89654fd0a6453c2da61fb6e9da262e6
8
$ git cat-file -p e995d8e1c89654fd0a6453c2da61fb6e9da262e6
merhaba
```

`hash-object` dosyayı yalnızca hesaplar; `-w` ile hesaplanan nesneyi depoya yazar. Yazılan nesnenin yolu `e9/95d8…` biçimindedir: ilk iki hane klasör, kalan otuz sekiz hane dosya adıdır. Bu ayrım, tek bir klasörde on binlerce dosya birikmesini önler. `cat-file -t` nesnenin türünü, `-s` boyutunu, `-p` içeriğini söyler. Dikkat et: boyut 8 bayt, çünkü `merhaba` kelimesi ve sondaki satır sonu karakteri (`\n`) toplam 8 bayt eder.

Peki bu özet nasıl hesaplanıyor? Git, nesneyi hash'lemeden önce bir başlık ekler: tür adı, bir boşluk, gövdenin bayt sayısı ve bir NUL bayt (`\0`). Başlık ile gövde birleştirilip SHA-1'den geçirilir. Bunu git'e sormadan Python ile yapabilirsin. Önce depodaki nesneyi zlib ile açıp içine bakalım. Git nesneleri diske zlib ile sıkıştırarak yazar; okuyucu bu yüzden sıkıştırmayı açmalıdır:

```python
# -*- coding: utf-8 -*-
"""Bir git nesnesini .git/objects'ten okuyup çözer."""
import os
import sys
import zlib


def nesneyi_oku(depo, hash_):
    # İlk iki hane dizin, kalanı dosya adıdır.
    yol = os.path.join(depo, ".git", "objects",
                       hash_[:2], hash_[2:])
    with open(yol, "rb") as f:
        ham = zlib.decompress(f.read())
    bas = ham.index(b"\x00")          # başlık: "tür boyut" + NUL
    tur, boyut = ham[:bas].split(b" ")
    govde = ham[bas + 1:]
    assert int(boyut) == len(govde), "boyut tutmuyor"
    return tur.decode(), govde


def agaci_listele(govde):
    # Ağaç: "<mod> <ad>\0<20 bayt ham hash>" tekrarları
    i = 0
    while i < len(govde):
        bosluk = govde.index(b" ", i)
        nul = govde.index(b"\x00", bosluk)
        mod = govde[i:bosluk].decode()
        ad = govde[bosluk + 1:nul].decode()
        ham = govde[nul + 1:nul + 21]
        print(mod, ad, ham.hex())
        i = nul + 21


if __name__ == "__main__":
    depo, hash_ = sys.argv[1], sys.argv[2]
    tur, govde = nesneyi_oku(depo, hash_)
    print("tür:", tur, "boyut:", len(govde))
    if tur == "tree":
        agaci_listele(govde)
    else:
        print(govde.decode("utf-8"), end="")
```

Bu betiği `nesne` klasöründe `python -I -X utf8 nesne_oku.py . e995d8e1…` diye çalıştırırsan şunu görürsün:

```term
$ python -I -X utf8 nesne_oku.py . \
  e995d8e1c89654fd0a6453c2da61fb6e9da262e6
tür: blob boyut: 8
merhaba
```

Betik yalnızca okur ve yazmaz; `-I` bayrağı Python'un ortamdaki ayarları ve geçerli dizindeki modülleri yok saymasını sağlar. Bu, bir klasörde yanlışlıkla bırakılmış bir `zlib.py` dosyasının araya girmesini önler.

Şimdi işin özü. Yukarıdaki betik, bir nesnenin içinde ne olduğunu gösterdi. Sırada ters yön var: hash'i git'e sormadan kendimiz hesaplayacağız. Aşağıdaki betik `mat.c` (blob), `mat.h` (blob), bunları içeren bir tree ve bu tree'ye bağlı bir commit için hash'i Python'da hesaplar ve sonra git'in sonucuyla karşılaştırır:

```python
# -*- coding: utf-8 -*-
"""Git nesne hash'lerini git'e sormadan Python'da hesaplar."""
import hashlib
import subprocess


def git(*args):
    sonuc = subprocess.run(["git"] + list(args), check=True,
                           capture_output=True)
    return sonuc.stdout.decode().strip()


def nesne_hash(tur, govde):
    # Başlık "<tür> <boyut>\0", ardından gövde; SHA-1 özeti.
    baslik = b"%s %d\x00" % (tur, len(govde))
    return hashlib.sha1(baslik + govde).hexdigest()


# 1) Blob: dosyanın ham baytları
mat_c = open("mat.c", "rb").read()
blob_c = nesne_hash(b"blob", mat_c)
blob_h = git("hash-object", "mat.h")

# 2) Tree: "<mod> <ad>\0<20 baytlık ham hash>" girdileri
#    Girdiler ada göre sıralanır (git bunu bekler).
girdiler = [
    (b"100644", b"mat.c", bytes.fromhex(blob_c)),
    (b"100644", b"mat.h", bytes.fromhex(blob_h)),
]
girdiler.sort(key=lambda g: g[1])
agac = b"".join(m + b" " + ad + b"\x00" + h
                for m, ad, h in girdiler)
tree = nesne_hash(b"tree", agac)

# 3) Commit: düz metin gövde
kimlik = "Kitap Deneme <deneme@example.com>"
zaman = "1768113000 +0300"   # 2026-01-11 09:30:00 +0300
ebeveyn = "dda4f894a869ae52258f8d7f424747d7835ece42"
govde = ("tree %s\nparent %s\nauthor %s %s\n"
         "committer %s %s\n\nkup eklendi\n"
         % (tree, ebeveyn, kimlik, zaman, kimlik, zaman))
commit = nesne_hash(b"commit", govde.encode())

# Karşılaştırma: Python ile git aynı hash'i üretmeli
for ad, benim, gitin in [
        ("blob", blob_c, git("hash-object", "mat.c")),
        ("tree", tree, git("rev-parse", "main^{tree}")),
        ("commit", commit, git("rev-parse", "main"))]:
    print("%-7s python=%s  git=%s  %s"
          % (ad, benim[:12], gitin[:12],
             "EŞLEŞTİ" if benim == gitin else "FARKLI"))
```

Betiği, iki commit'lik deneme deposunda çalıştırdık: ilk commit `mat.c`'de yalnızca `kare` fonksiyonunu içeriyordu, ikinci commit `kup` fonksiyonunu ekledi. Betiğin çıktısı şöyledir:

```term
$ python -I -X utf8 kendin_hash.py
blob    python=792c31b1273e  git=792c31b1273e  EŞLEŞTİ
tree    python=7df8cc960aec  git=7df8cc960aec  EŞLEŞTİ
commit  python=a95940645234  git=a95940645234  EŞLEŞTİ
```

Üç nesne de eşleşti. Bu, git'in hash'lemesinin sihir olmadığını gösteriyor: yalnızca bir başlık, bir gövde ve SHA-1. Tree'nin gövdesinin bir metin değil, ikili bir biçim olduğuna dikkat et. Her girdi `100644 mat.c` gibi bir metin satırı değildir; mod ve ad metin, ardından bir NUL bayt, ardından 20 baytlık ham SHA-1 gelir. Bu yüzden `cat-file -p` tree'yi okunabilir biçimde gösterirken, depoda saklanan şey ikilidir.

Sıkıştırma ve sağlama da aynı kalıba oturuyor. Git nesneyi diske yazmadan önce zlib ile sıkıştırır. Ama adı, sıkıştırılmamış başlık+gövdenin özetidir. Yani dosyanın içeriği bozulursa, ad ile içerik uyuşmaz ve git bunu fark eder. Bu, `git fsck`'in çalışma prensibidir: nesneleri okur, özetini yeniden hesaplar, adıyla karşılaştırır.

::: baglanti
Hash fonksiyonunun tasarımını ve çakışma kavramını Bölüm 9'da gördün (9.2 ve 9.3). Git'in nesne adı, o bölümdeki "veriden adres üret" fikrinin bir sürüm kontrol sistemine uygulanmasıdır. Bölüm 9.8'deki saldırı yüzeyi tartışması da burada geçerli: SHA-1 çarpışmaları pratik olarak gösterildiği için git yeni bir nesne biçimi (SHA-256) desteklemeye başladı.
:::

SHA-256 geçişi, genel bilgi olarak: 2017'de SHA-1 için pratik bir çarpışma gösterildi (SHAttered saldırısı). Git bunun üzerine SHA-256 nesne biçimini ekledi; yeni depolar bu biçimle açılabilir. Biz de Git 2.52.0 ile bir deneme deposunu SHA-256 olarak kurup aynı içeriği hash'ledik:

```term
$ git init -q --object-format=sha256 -b main s256 && cd s256
$ echo "merhaba" > a.txt
$ git hash-object -w a.txt
6084bb9d58dd9d8d821d17b42a6de264bb0502cd22ea5365a1fc4435609c108f
```

Adın uzunluğu 64 karaktere çıktı; SHA-1'de 40 karakterdi. Geçişin pratikte zorluğu, iki biçimin aynı depoda karışmamasıdır: bir SHA-1 deposu ile bir SHA-256 deposu birbirinin nesnelerini doğrudan okuyamaz. Bu yüzden mevcut depoları dönüştürmek bir planlama işidir.

### Ağaç ve commit'i elle kurmak

Bir commit'in ne olduğunu anlamanın en iyi yolu onu elle kurmaktır. `git mktree` bir tree'yi, `git commit-tree` bir commit'i girdilerinden oluşturur. Aşağıda `mat.c` ve `mat.h` blob'larından bir tree kuruluyor, sonra bu tree'ye bir commit bağlanıyor. Tarihleri sabitlemek için iki ortam değişkeni kullanıyoruz; bunu şart kılan neden şudur: git commit hash'ine yazar, bırakan ve zaman damgasını da katar. Tarihi sabitlemezsen her çalıştırmada başka bir hash alırsın.

```term
$ printf 'int kare(int x) { return x * x; }\n' > mat.c
$ printf 'int kare(int x);\n' > mat.h
$ git hash-object -w mat.c
572c1694195ecb4b4c099fafc37f0ba776ebe89e
$ git hash-object -w mat.h
30c115c910920ee12223a685cf9a3a82fab56c2a
$ git mktree < liste.txt
d9311b0dc8f997bb16f63fe9be00ae9c270ceacc
```

`liste.txt` dosyasının içeriği `100644 blob 572c16… mat.c` ve `100644 blob 30c115… mat.h` satırlarıdır; sekmeyle ayrılmış. Şimdi commit:

```term
$ export GIT_AUTHOR_NAME="Kitap Deneme"
$ export GIT_AUTHOR_EMAIL="deneme@example.com"
$ export GIT_COMMITTER_NAME="Kitap Deneme"
$ export GIT_COMMITTER_EMAIL="deneme@example.com"
$ GIT_AUTHOR_DATE="2026-01-10T10:00:00+0300" \
  GIT_COMMITTER_DATE="2026-01-10T10:00:00+0300" \
  git commit-tree d9311b0dc8f997bb16f63fe9be00ae9c270ceacc \
  -m "ilk surum"
dda4f894a869ae52258f8d7f424747d7835ece42
$ git cat-file -p dda4f894a869ae52258f8d7f424747d7835ece42
tree d9311b0dc8f997bb16f63fe9be00ae9c270ceacc
author Kitap Deneme <deneme@example.com> 1768028400 +0300
committer Kitap Deneme <deneme@example.com> 1768028400 +0300

ilk surum
```

Commit'in gövdesi düz metindir: ağaç, ebeveynler (bu ilk commit'te yok), yazar, bırakan, boş satır ve mesaj. `1768028400`, Unix epoch saniyesidir. Bu commit'i `main` dalına bağlayıp sonraki bir commit daha eklediğimizde, nesneler Şekil 38.1'deki gibi birbirine bağlanır. Commit'ten tree'ye, tree'den blob'lara giden oklar "içerir" ilişkisidir; commit'ten ebeveynine giden ok ise geçmişi gösterir. Bu geçmiş yönlü, döngüsüz bir graftır (DAG); Bölüm 11.10'da git commit geçmişini zaten bir DAG örneği olarak anmıştık.

![Şekil 38.1: Nesne modeli. Her commit bir tree'ye ve ebeveynlerine işaret eder; tree'ler blob'lara işaret eder. İki commit aynı mat.h blob'unu paylaşır, bu yüzden o içerik tek kez saklanır.](gorseller/b38_nesne_modeli.png)

Tag nesnesi de aynı biçimdedir. Açıklamalı bir etiket (`git tag -a`), bir commit'e isim verip ayrıca yazar, tarih ve mesaj taşıyan bir nesne oluşturur. Hafif etiket (`git tag` yalnızca isim) ise doğrudan commit'e işaret eden bir dosyadan ibarettir:

```term
$ GIT_AUTHOR_DATE="2026-01-11T10:00:00+0300" \
  GIT_COMMITTER_DATE="2026-01-11T10:00:00+0300" \
  git tag -a v1.0 -m "surum 1" dda4f894a869ae52258f8d7f424747d7835ece42
$ git cat-file -t v1.0
tag
$ git cat-file -p v1.0
object dda4f894a869ae52258f8d7f424747d7835ece42
type commit
tag v1.0
tagger Kitap Deneme <deneme@example.com> 1768114800 +0300

surum 1
```

Sürüm etiketleri (v1.0 gibi) genellikle açıklamalı etiket olarak oluşturulur. Bir sürümü savunmak istediğinde "bu sürüm hangi commit'ten çıktı?" sorusunun cevabı etiketin işaret ettiği nesnedir. Etiketi silmek commit'i silmez; yalnızca ismi kaldırır.

## 38.2 Referanslar, HEAD ve reflog

Nesne deposu bir kütüphane gibidir: kitaplar (nesneler) raflarda durur ama kitapların adları yoktur, yalnızca özetleri vardır. Kütüphaneciye "bana yeni sürümü getir" diyebilmek için bir ada ihtiyaç var. İşte **referanslar** (refs) bu adları taşır. Bir dal, bir etiket ya da HEAD birer referanstır. Referans, bir commit'in 40 karakterlik özetini tutan küçük bir metin dosyasıdır.

```term
$ cat .git/HEAD
ref: refs/heads/main
$ cat .git/refs/heads/main
b85ff7244621469992f650485c5f56fe4aed6693
$ ls .git/refs/heads
main
```

İki şey dikkat çekiyor. Birincisi, `HEAD` bir hash değil, başka bir referansa işaret eden *sembolik* bir referanstır: `ref: refs/heads/main`. Yani "şu an üzerinde durduğum dal `main`'dir" demektir. İkincisi, dal dosyası yalnızca bir hash tutar. `git commit` yaptığında git yeni commit'in hash'ini `refs/heads/main` dosyasına yazar ve HEAD'in gösterdiği dalı ilerletir. Dal diye ayrı bir veri yapısı yoktur; dal, bir dosyadır.

Bu modelin bir sonucu var: HEAD dalı göstermek yerine doğrudan bir commit'i gösterebilir. Buna **ayrık HEAD** (detached HEAD) denir. Eski bir commit'i incelemek için `git switch --detach` ya da `git checkout <hash>` kullandığında olur. Burada yaptığın commit'ler hiçbir dal tarafından tutulmaz; dalı değiştirdiğin anda, o commit'lere ulaşmanın bir yolu kalmaz. Şekil 38.2 iki durumu yan yana gösterir.

![Şekil 38.2: Dal ve HEAD. HEAD bir dala, dal bir commit'e işaret eder. Ayrık HEAD doğrudan bir commit'e işaret eder ve dal adı yoktur.](gorseller/b38_referanslar.png)

Referanslar iki yerde saklanabilir. Normal durumda her dal kendi dosyasındadır (`refs/heads/main`). Çok sayıda referans olduğunda git bunları `packed-refs` adında tek bir dosyada toplayabilir; `git pack-refs --all` bunu yapar. Bu, dosya sistemi işlemlerini azaltmak içindir ve davranışı değiştirmez.

### Reflog: HEAD'in günlüğü

Bir commit'i kaybettiğini düşün: `reset --hard` ile yanlış bir commit'e döndün ve son değişikliklerin dallardan kayboldu. Git bunu kurtarabilir mi? Evet, çünkü **reflog** adında bir günlük tutar. Her HEAD hareketi (commit, reset, checkout, rebase, merge) reflog'a bir satır olarak yazılır. Bu satırlar yerel bir günlüktür; uzak depoya gönderilmez. Deneyelim:

```term
$ echo "v1" > a.txt && git add a.txt && git commit -q -m "a ilk"
$ echo "v2" > a.txt && git add a.txt && git commit -q -m "a ikinci"
$ echo "onemli is" > b.txt && git add b.txt && \
  git commit -q -m "deneysel is"
$ git reset --hard HEAD~1
HEAD is now at 8834243 a ikinci
$ git log --oneline
8834243 a ikinci
f815980 a ilk
$ git reflog
8834243 HEAD@{0}: reset: moving to HEAD~1
b85ff72 HEAD@{1}: commit: deneysel is
8834243 HEAD@{2}: commit: a ikinci
f815980 HEAD@{3}: commit (initial): a ilk
```

`deneysel is` commit'i artık `git log`'da görünmüyor. Ama reflog'da `HEAD@{1}` olarak duruyor. Git'in ona ulaşmak için kullandığı ifade, "HEAD'in bir adım önceki hali"dir. Bu commit hâlâ nesne deposunda duruyor, ama hiçbir referans ona işaret etmiyor. Böyle commit'lere **dangling** (sahipsiz) denir ve `git fsck` bunları listeler:

```term
$ git fsck --no-reflogs
dangling commit b85ff7244621469992f650485c5f56fe4aed6693
```

Reflog'un ömrü sınırlıdır. `gc.reflogExpire` varsayılanı 90 gün; referansa ulaşılamayan (sahipsiz) girdiler için `gc.reflogExpireUnreachable` varsayılanı 30 gün (ikisi de git 2.43 belgesinden). Sahipsiz nesneler için `git gc`, varsayılan olarak `gc.pruneExpire` (2 hafta) öncesindeki nesneleri siler. Yani kaybettiğini fark ettiğin anda hareket et. Kurtarma adımlarının tamamını Örnek 2'de yapacağız.

::: ipucu
Yanlış bir şey yaptığını fark ettiğinde ilk refleks `git reflog` olsun. Commit ya da dal silmekten önce, her zaman önce `git branch yedek <hash>` ile bir dal ismi ver. Bir dal ismi, commit'i reflog'un süresinden bağımsız olarak canlı tutar.
:::

Reflog bir yerel kayıttır: yalnızca senin makinende var. Bu yüzden bir arkadaşının deposunda yaşanan bir kaybı ondan çözemezsin, uzak depodan çözersin. Bunun dersi, tarihçeyi uzakta ve dallarla korumaktır.

## 38.3 Üç ağaç: HEAD, indeks ve çalışma dizini

Bölüm 4.7'de git'in üç alanını (çalışma dizini, sahne, depo) görmüştük. Şimdi bu üç alanın her birini bir **ağaç** olarak düşünelim. Her biri bir anlık görüntüdür ve git her komutu bu üç görüntü arasındaki kopyalama olarak tanımlar:

- **HEAD**: son commit'in tree'si. Depoda kalıcı olan budur.
- **İndeks** (index, sahne alanı): bir sonraki commit'e girecek içeriğin listesi. Git bunu `.git/index` dosyasında tutar.
- **Çalışma dizini** (working tree): dosyaları gerçekten düzenlediğin yer.

Bu üç ağacın her dosya için ayrı bir değeri olabilir. Bunu tek bir dosyada, `a.txt`'de görelim. Dosyanın üç ayrı sürümünü üretip sırasıyla sahneye alıyoruz:

Önceki commit'te `a.txt` içeriği `v1` idi. Şimdi sırasıyla üç sürüm üretiyoruz:

```term
$ echo v2 > a.txt && git add a.txt && git commit -q -m "a ikinci"
$ git ls-files -s
100644 8c1384d825dbbe41309b7dc18ee7991a9085c46e 0	a.txt
$ echo v3 > a.txt && git add a.txt
$ echo v4 > a.txt
$ git show HEAD:a.txt
v2
$ git show :a.txt
v3
$ cat a.txt
v4
$ git status --short
MM a.txt
```

`git ls-files -s` indeksin içeriğini gösterir: mod, blob hash'i, aşama numarası (0 normal durumdur, çakışmada 1-3 olur) ve yol. `:a.txt` yazımı "indeksteki a.txt" anlamına gelir; `HEAD:a.txt` ise commit'teki sürüm. Üç sürümün üç farklı değeri var: HEAD `v2`, indeks `v3`, çalışma dizini `v4`. Durum çıktısındaki `MM` iki kolonu da işaretler: ilki HEAD ile indeks arasındaki farkı (staged), ikincisi indeks ile çalışma dizini arasındaki farkı (unstaged) gösterir.

Bu model, `git status`'un neden iki ayrı kısım gösterdiğini ve `git diff` ile `git diff --cached` arasındaki farkı açıklar. `git diff` indeks ile çalışma dizinini karşılaştırır; `git diff --cached` (ya da `--staged`) HEAD ile indeksi karşılaştırır. Bir commit'e tam olarak neyin gireceğini görmek istediğinde ikincisine bakarsın.

![Şekil 38.3: Üç ağaç ve komutların hareketleri. git add çalışma dizininden indekse, git commit indeksten HEAD'e kopyalar. git restore ters yönde kopyalar.](gorseller/b38_uc_agac.png)

Komutların çoğu bu üç ağacın bir ya da ikisini değiştirir. Git 2.23'ten beri bu işler için iki yeni komut vardır: `git restore` dosyaları geri alır, `git switch` dal değiştirir. Eski `git checkout` her ikisini birden yaptığı için karışıklığa yol açardı; bu iki komut işleri ayırır.

### reset: üç ağacın üçü de değişebilir

`git reset` tam olarak hangi ağaçların değişeceğini seçmene izin verir. Üç biçimi var ve farkları mülakatların favorisidir. Aynı başlangıç durumundan (HEAD `v2`, indeks `v3`, çalışma dizini `v4`) başlayıp her birini `HEAD~1`'e uyguladığımızda şunu gördük:

![Şekil 38.4: reset türleri. Kırmızı kutular o komutla değişen katmanı gösterir; yeşil kutular korunan katmandır. Değerler deneme deposunun gerçek çıktısıdır.](gorseller/b38_reset_tablo.png)

Sonucu okumanın yolu şudur: `--soft` yalnızca dalı taşır, yani commit'i geri alır ama değişiklikleri indekste bırakır. `--mixed` (varsayılan) dalı taşır ve indeksi sıfırlar; değişiklikler çalışma dizininde kalır, dosyalarda hâlâ duran ama sahnede olmayan bir fark olur. `--hard` her şeyi sıfırlar ve geri alınamaz değişiklik yaratabilir. Mixed sonrası durum şöyle görünür:

```term
$ git reset --mixed HEAD~1
$ git status --short
 M a.txt
```

Boşluk-M işareti (` M`) yalnızca çalışma dizini ile indeks arasındaki farkı gösterir: dosya sahnede değil, değiştirilmiş. `--hard` ile bu fark kalmaz, ama `v4` de gider. Bu yüzden `--hard` kullanmadan önce `git status` ve `git stash` ile durumunu kontrol et. Son bir kural: `reset` ile paylaşılmış bir dalın tarihçesini kesmek, başkalarının commit'lerini ulaşılamaz kılar. Yayımlanmış bir commit'in etkisini geri almak için doğru araç `revert`'tür (38.5).

::: dikkat
`git reset --hard`, çalışma dizinindeki izlenmemiş olmayan değişiklikleri geri alır ve bu değişiklikler reflog'da bile yoktur (reflog yalnızca commit'leri tutar). Commit'lenmemiş bir işi kaybettiysen kurtarma yolu yoktur. Önemli bir şeyi sıfırlamadan önce `git stash` ile sakla ya da bir dal aç.
:::

## 38.4 Birleştirme: hızlı ileri, üç yollu birleştirme ve çakışma

İki dal ayrıldığında, birleştirmenin hangi biçimde yapılacağı tarihçenin şeklini belirler. Git iki temel durum tanır.

**Hızlı ileri** (fast-forward): `main` dalı, özellik dalının atası ise, git yapacak bir şey bulamaz. Yalnızca `main` işaretçisini özellik dalının ucuna kaydırır. Yeni bir birleşme commit'i oluşmaz.

**Üç yollu birleştirme** (three-way merge): iki dal da ilerlemişse, git iki ucu ve bunların **ortak atasını** (merge-base) karşılaştırır. Bu üç ağaç (ortak ata = taban, ours = bulunduğun dal, theirs = birleştirilen dal) tek tek farklılıkları bulur. Biri değiştirdiği, öteki değiştirmediği bir satırı alır; ikisi de değiştirdiyse çakışma bildirir.

Önce hızlı ileri örneğini deneyelim. Taban commit'ten `ozellik-a` dalı açıp bir satır ekliyoruz; `main` bu dalda ilerlemedi:

```term
$ git switch -c ozellik-a
$ git commit -qam "ozellik a: 5 eklendi"
$ git switch main
$ git merge --ff-only ozellik-a
Updating 8c9f611..cb2954a
Fast-forward
 m.txt | 1 +
 1 file changed, 1 insertion(+)
$ git log --oneline --graph --all
* cb2954a ozellik a: 5 eklendi
* 8c9f611 taban
```

`--ff-only` bayrağı, hızlı ileri olmazsa birleştirmeyi reddeder. Ekipler bunu sıkça kullanır: tarihçede birleşme commit'i istemiyorsan, işi rebase edip hızlı ileri birleştirmeye zorlarsın (38.5).

Şimdi iki dal da ilerlemiş bir durum. `ozellik-b` 2. satırı, `main` 4. satırı değiştirdi. Değişiklikler farklı satırlarda olduğu için çakışma yok:

```term
$ git merge-base main ozellik-b
8c9f61181388057ddf309daf4eaa4f06cf7392d0
$ git merge --no-edit ozellik-b
Auto-merging m.txt
Merge made by the 'ort' strategy.
 m.txt | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git log --oneline --graph --all
*   4c7b74d Merge branch 'ozellik-b'
|\
| * 6f38aa5 ozellik b: 2. satir
* | 6f9d582 main: 4. satir
|/
* 8c9f611 taban
```

Birleşme commit'i (`4c7b74d`) iki ebeveyne sahiptir: `main`'in ucu ve `ozellik-b`'nin ucu. Bu bir DAG'da iki kolun tekrar birleştiği noktadır.

![Şekil 38.5: Hızlı ileri ve üç yollu birleştirme. Solda main yalnızca ilerler. Sağda taban ortak ata olarak iki kolu birleştirir ve birleşme commit'i iki ebeveyne bağlanır.](gorseller/b38_birlestirme.png)

`Merge made by the 'ort' strategy` mesajındaki `ort`, git'in varsayılan birleştirme stratejisidir; üç yollu birleştirmeyi yapan algoritmanın adıdır.

Şimdi çakışmayı görelim. İki dal aynı satırı (3. satırı) farklı biçimde değiştirirse git birleştirmeyi durdurur ve dosyaya işaret koyar:

```term
$ git merge ozellik-c
Auto-merging m.txt
CONFLICT (content): Merge conflict in m.txt
Automatic merge failed; fix conflicts and then commit the result.
$ cat m.txt
1 giris
2 ortak
<<<<<<< HEAD
3 MAIN-versiyon
=======
3 C-versiyon
>>>>>>> ozellik-c
4 son
$ git ls-files -u
100644 06ff18de1fbe57749a664fcf8070ccf4c6e0bcf8 1	m.txt
100644 4f50bd20cb5a20d6ca2afad29115f14d998234c4 2	m.txt
100644 ba311cd103dd474bf385dac53fcddc5cd5408436 3	m.txt
```

`<<<<<<<` ile `>>>>>>>` arasındaki kısım iki tarafın bakışıdır. `HEAD` yazısı senin tarafını (ours), `ozellik-c` ise birleştirdiğin dalı (theirs) gösterir. Ama asıl önemli bilgi `git ls-files -u` çıktısındadır. Git, çakışan dosya için indekste üç ayrı sürüm tutar: aşama 1 ortak atadır (taban), aşama 2 ours, aşama 3 theirs. Üç sürümü tek tek görebilirsin:

```term
$ git show :1:m.txt | sed -n 3p
3 orta
$ git show :2:m.txt | sed -n 3p
3 MAIN-versiyon
$ git show :3:m.txt | sed -n 3p
3 C-versiyon
```

Taban satırı `3 orta` idi; iki taraf da bunu değiştirdi. Bu yüzden git hangisinin doğru olduğunu bilemez. Taban olmadan çakışmanın ne anlama geldiğini çıkarmak çok daha zordur. Bu yüzden çakışma çözmeyi öğrenmek Örnek 3'ün konusu.

::: ipucu
Birleştirme sırasında `ours` ve `theirs` kelimeleri, rebase sırasında tersine döner. Merge'de `ours` senin bulunduğun daldır, `theirs` birleştirdiğin daldır. Rebase'de ise sen kendi commit'lerini yeniden oynattığın için `ours` hedef dalın (örneğin `main`) tarafı, `theirs` senin commit'in olur. Karıştırmamak için çakışma işaretlerindeki dal adlarına bak, aklında kalmasın.
:::

Birleştirmenin altında yatan mantık Bölüm 16'daki LCS fikridir: iki dizi arasındaki ortak yapıyı bulup, ortak olmayan kısımları değişiklik olarak işaretlemek. Üç yollu birleştirmede bu, taban ile iki taraf arasında iki ayrı karşılaştırma yapmak demektir. Bu karşılaştırmanın nasıl hesaplandığını 38.6'da göreceksin.

## 38.5 Rebase, cherry-pick ve revert

Birleştirme tarihçeyi olduğu gibi tutar; rebase ise tarihçeyi yeniden yazar. Bu iki yaklaşımın farkı, mülakatların en sevilen sorularından biridir. Rebase'in yaptığı iş basit bir fikirdir: dalındaki commit'leri alıp, belirtilen yeni tabanın üzerinde **yeniden oynatır**. Yeniden oynatma, her commit için yeni bir değişiklik uygulamak ve yeni bir commit oluşturmak demektir. Yeni commit'in ebeveyni değiştiği için hash'i de değişir. Örneği deneyelim: `ozellik` dalı `taban`'dan ayrılmış, sonra `main` bir commit (m1) almış.

```term
$ git log --oneline --graph --all
* a8e6331 main: m1
| * 1851908 ozellik: d1
| * 5652564 ozellik: c1
| * 66c602d ozellik: b1
|/
* 2dbfdd9 taban
$ git switch ozellik
$ git rebase main
Successfully rebased and updated refs/heads/ozellik.
$ git log --oneline --graph --all
* 5928776 ozellik: d1
* 4df0447 ozellik: c1
* 48abce4 ozellik: b1
* a8e6331 main: m1
* 2dbfdd9 taban
```

(Git'in ilerleme satırları, `Rebasing (1/3)` gibi, kısaltıldı.) Dikkat et: `main` ve taban commit'leri aynı kaldı (a8e6331, 2dbfdd9). Ama özellik dalının üç commit'inin üçü de yeni hash aldı: `66c602d` → `48abce4`, `5652564` → `4df0447`, `1851908` → `5928776`. İçerikleri aynı; kimlikleri farklı. Şekil 38.6 bu farkı iki panelde gösterir.

![Şekil 38.6: Rebase öncesi ve sonrası. Özellik dalının içeriği korunur, ama her commit'in ebeveyni değiştiği için hash'i yenilenir; eski commit'ler yalnızca reflog'da kalır.](gorseller/b38_rebase.png)

Bu yüzden rebase'in temel kuralı şudur: **paylaşılmış commit'leri rebase etme.** Başka biri o commit'i çekmiş ve kendi çalışmasını ona dayandırmışsa, rebase ile hash'i değiştirdiğinde onun tarihçesiyle senin tarihçen artık ayrışır. Bu konuyu 38.8'de uzak depo örneğiyle göstereceğiz. Kendi yerel dalında, henüz kimseyle paylaşmadığın işleri düzeltmek için rebase güvenlidir ve tarihçeyi düz tutar.

### İnteraktif rebase ve fixup

Rebase'in asıl gücü, commit'leri birleştirmek, düzeltmek ya da sıralamak için kullanılmasıdır. Bunun için `git rebase -i` açılan bir düzenleyicide her commit'in karşısına bir eylem yazmanı ister. Yaygın eylemler: `pick` (olduğu gibi tut), `reword` (mesajı değiştir), `squash` (önceki commit'e birleştir, mesajı düzenle), `fixup` (önceki commit'e birleştir, mesajı at), `drop` (sil). Bu eylemler genel bilgi olarak belgelenmiştir; burada etkileşimsiz bir yol gösteriyoruz.

Sık görülen durum şudur: bir commit'i yaptın, sonra o commit'teki bir hatayı düzelttin. Bu düzeltmeyi ayrı bir commit olarak tutmak yerine asıl commit'in içine katmak istersin. `--fixup` bayrağıyla düzeltme commit'ini doğru hedefe bağlarsın, `--autosquash` ile rebase bu commit'i otomatik olarak hedefin altına taşıyıp birleştirir:

```term
$ git commit -q --fixup=48abce4
$ git log --oneline -1
cc8bcbf fixup! ozellik: b1
$ GIT_SEQUENCE_EDITOR=true git rebase -q -i --autosquash main
$ git log --oneline --graph --all
* 97f6bfd ozellik: d1
* 4a0b8f8 ozellik: c1
* fae1eba ozellik: b1
* a8e6331 main: m1
* 2dbfdd9 taban
```

`GIT_SEQUENCE_EDITOR=true` ile düzenleyiciyi `true` komutuna yönlendirdik; `true` hiçbir şey değiştirmeden çıkar, dolayısıyla git `--autosquash`'in oluşturduğu sıralamayı olduğu gibi kabul eder. Bu, etkileşimli bir komutu betikten ya da bu bölümdeki gibi deneyden çalıştırmanın yoludur. `fixup!` ile başlayan commit'in mesajı, birleştirilince kaybolur ve `fae1eba` commit'i artık düzeltilmiş içeriği taşır (`b1 duzeltildi`).

### cherry-pick ve revert

Bazen bir dalın yalnızca bir commit'ini başka bir dala taşımak istersin. `git cherry-pick`, bir commit'in değişikliğini mevcut dalın üzerine yeniden uygular. Yeni bir commit oluşur ve hash'i farklıdır:

```term
$ git switch main
$ git cherry-pick ozellik~1
[main 2d1721b] ozellik: c1
 1 file changed, 1 insertion(+)
 create mode 100644 c.txt
```

`ozellik~1` (4a0b8f8) ile `2d1721b` aynı değişikliği taşır ama farklı commit'lerdir. Cherry-pick'in bedeli budur: değişiklik çoğaltılmış olur, ve aynı değişiklik iki dalda birden yer alırsa ileride birleştirme sırasında yinelenen çakışmalar görebilirsin.

Bir commit'in etkisini geri almak istediğinde iki yolun var: `reset` (tarihçeyi kes) ya da `revert` (tersini yeni bir commit olarak ekle). Paylaşılmış bir dalda `reset` yapmak, başkalarının tarihçesini bozar. `revert` ise tarihçeyi koruyarak tersi işlemi kaydeder:

```term
$ git revert --no-edit HEAD
[main ee9e7e7] Revert "ozellik: c1"
 1 file changed, 1 deletion(-)
 delete mode 100644 c.txt
$ git log --oneline -3
ee9e7e7 Revert "ozellik: c1"
2d1721b ozellik: c1
a8e6331 main: m1
```

`c.txt` dosyası geri silindi, ama `2d1721b` commit'i tarihçede yerinde duruyor. Bu, "bu değişiklik yapıldı ve sonra geri alındı" kaydını korur; denetim izi (audit trail) için kritik bir özelliktir. Savunma projelerinde bu, bir değişikliğin neden geri alındığının belgelenmesi açısından değerlidir.

| Soru | `reset` | `revert` |
|---|---|---|
| Tarihçede ne olur? | Commit'ler kesilir (ulaşılamaz olur) | Yeni bir ters commit eklenir |
| Paylaşılmış dalda güvenli mi? | Hayır | Evet |
| Denetim izi | Kaybolur | Korunur |
| Tipik kullanım | Yerel işi geri sarmak | Yayımlanmış bir değişikliği geri almak |

## 38.6 Diff: Myers, LCS ve algoritma seçimi

`git diff` iki metin arasındaki farkı bulur. Bu, iki satır dizisi arasında **en kısa düzenleme betiğini** (shortest edit script) bulmaktır: hangi satırların silinmesi, hangi satırların eklenmesi gerektiğini gösteren, en az sayıda eklemeyi ve silmeyi kullanan kısa bir liste. Bu problemin çözümü Bölüm 16.8'deki en uzun ortak altdizi (LCS) problemiyle yakından bağlantılıdır. Eğer N ve M satırlı iki dosyanın ortak altdizisinin uzunluğu L ise, yalnızca ekleme ve silme kullanan en kısa düzenleme betiğinin uzunluğu D = N + M − 2L olur. Yani LCS'i bulmak, diff'i bulmakla aynı iştir.

Git'in varsayılan diff algoritması **Myers** algoritmasıdır (`diff.algorithm` varsayılanı `myers`, git 2.43 belgesinden). Myers, bu en kısa betiği O((N + M) · D) zamanda bulur. Bölüm 16'daki klasik LCS tablosu O(N · M) harcar. Dosyalar birbirine benzediğinde D küçüktür ve Myers belirgin biçimde hızlıdır. Bu, Myers'in 1986 makalesindeki genel sonuçtur ve bu bölümde ölçmedik.

Biz de deneyelim. Aşağıdaki iki dosya küçük bir kod taşımasıdır: `yeni.c`, `eski.c`'deki `u03 = 3;`, `}`, `u05 = 5;`, `}` bloğunu yukarıdan alıp `u08 = 8;` satırının ardına koyuyor. Dosyalar tekrar eden `}` ve boş satırlarla bilerek kuruldu; kod dosyalarında en çok tekrar eden satırlar bunlardır ve diff için tuzak yaratırlar.

```term
$ cat -n eski.c
     1	u00 = 0;
     2	}
     3	u02 = 2;
     4	u03 = 3;
     5	}
     6	u05 = 5;
     7	}
     8	}
     9	u08 = 8;
    10
    11	}
    12	}
    13
    14	u13 = 13;
    15	}
    16
$ cat -n yeni.c
     1	u00 = 0;
     2	}
     3	u02 = 2;
     4	}
     5	u08 = 8;
     6
     7	}
     8	}
     9	u03 = 3;
    10	}
    11	u05 = 5;
    12	}
    13
    14	u13 = 13;
    15	}
    16
```

Varsayılan algoritmayla (Myers) fark şöyle çıkar. Kullandığımız `-c core.autocrlf=false`, Windows'ta sistem düzeyinde açık olan satır sonu dönüşümünü bu deneyde kapatır:

```term
$ git -c core.autocrlf=false diff --no-index --unified=0 eski.c yeni.c
diff --git a/eski.c b/yeni.c
index b689e63..96b2465 100644
--- a/eski.c
+++ b/yeni.c
@@ -4,4 +3,0 @@ u02 = 2;
-u03 = 3;
-}
-u05 = 5;
-}
@@ -12,0 +9,4 @@ u08 = 8;
+u03 = 3;
+}
+u05 = 5;
+}
```

Çıktı, dört satırlık bloğu iki yerde gösteriyor: silinen dört satır eski dosyanın 4-7. satırlarıdır, eklenen dört satır yeni dosyanın 9-12. satırlarıdır. Hunk başlığındaki `@@ -4,4 +3,0 @@` ifadesi, eski dosyanın 4. satırından itibaren dört satır olduğunu, yeni dosyada ise sıfır satır bulunduğunu söyler. Bu, `diff`'in okuma biçimidir; ilk bakışta zorlar, ama birkaç hunk'tan sonra alışırsın.


Git birden fazla algoritma sunar. Aynı iki dosya için üç algoritmanın sonucu şöyle:

| Algoritma | Değişen satır sayısı | Davranış |
|---|---|---|
| `myers` (varsayılan) | 8 (4 silme, 4 ekleme) | En kısa betik; taşınan bloğu bulur |
| `histogram` | 8 | Myers'a benzer; düşük sıklıklı satırları çapa alır |
| `patience` | 10 (5 silme, 5 ekleme) | Yalnızca iki tarafta da tek bulunan satırları çapa alır |

Patience algoritması, yalnızca iki dosyada da tek kez geçen satırları eşleştirme çapası olarak kullanır (bu örnekte `u02`, `u05`, `u08` gibi satırlar bu niteliktedir) ve çapalar arasını ayrı ayrı hizalar. Bu, en kısa betiği garanti etmez: Patience bu örnekte daha uzun bir değişiklik üretti. Yani bir ödünleşim var: minimal değişikliği mi, yoksa "insan gözünde anlamlı" hizalamayı mı istediğine karar vermen gerekir. Patience ve histogram, kod taşıma ve büyük yeniden düzenlemelerde genelde daha okunaklı diff'ler üretir; ama her zaman daha kısa değildir.

Bu farkın ne kadar yaygın olduğunu görmek için bir deney daha yaptık. Her denemede 14-22 satırlık bir dosya kuruldu; satırlar `}`, boş satır ve benzersiz satırların karışımıydı. Sonra dosyadan 4 satırlık bir blok rastgele bir yere taşındı (tohum 38, 150 deneme). 150 denemenin 31'inde üç algoritma farklı sayıda satır değiştirdi. Bu bir örneklem değil, tek bir düzenekteki sayımdır; genel bir yüzde iddiası olarak okunmamalı, ama Myers ile patience'ın sonuçlarının kodun yapısına bağlı olarak ayrıldığını gösteriyor.

::: not
Diff'i sonucuna göre değil, kullanım amacına göre seç. Birleştirme ve gözden geçirme (code review) için okunabilirlik önemliyse `histogram`'ı dene. Minimal değişiklik istiyorsan `myers` (ya da `--minimal`) doğru seçimdir.
:::

Diff ile birleştirmenin ilişkisini burada da görüyoruz. Üç yollu birleştirmede git, taban ile iki taraf arasında iki diff hesaplar; çakışma, iki diff'in aynı bölgede kesiştiği yerde ortaya çıkar. Yani birleştirme, diff'in bir uygulamasından ibarettir.

## 38.7 Paketler: gevşek nesneler, packfile ve delta

Şimdiye kadar her nesne ayrı bir dosyaydı (gevşek nesne, loose object). Bu, küçük depolarda sorun değildir. Ama bin commit'lik bir projede her commit'in her dosyası için ayrı bir dosya tutmak hem disk alanı hem de dosya sistemi yükü demektir. Git bunun için **paket dosyası** (packfile) kullanır: birçok nesneyi tek bir dosyada toplar ve çoğu nesneyi, benzer bir nesneye göre yalnızca **fark** (delta) olarak saklar.

Bunu ölçmek için 200 küçük değişiklikli sürümden oluşan bir depo kurduk. Dosya 1500 satırlık bir ölçüm günlüğü; her commit'te bir satır değişiyor. Önce gevşek nesnelere bakıyoruz, sonra paketliyoruz:

```term
$ git count-objects -v
count: 603
size: 2426
in-pack: 0
packs: 0
size-pack: 0
$ git -c pack.threads=1 gc -q
$ git count-objects -v
count: 0
size: 0
in-pack: 603
packs: 1
size-pack: 86
```

`count` gevşek nesne sayısı ve `size` onların KiB cinsinden toplam boyutudur. İlk commit ile birlikte 201 commit, 201 tree ve 201 blob vardır: toplam 603 nesne. `gc` (garbage collection) bunları tek bir pakete taşıdı: 2426 KiB'den 86 KiB'ye düştü. Bu oran bu deneme deposuna özgüdür; tipik oranı tahmin etmek için kullanma.

`-c pack.threads=1` bayrağını neden kullandığımızı açıklamamız gerekiyor. Git paketlemede delta eşleşmelerini aramak için birden çok iş parçacığı kullanabilir. Bu deneyde çok iş parçacıklı paketleme, aynı betiğin iki çalıştırmasında birkaç baytlık farkla farklı paket dosyaları üretti; paket dosyasının adı (içindeki nesnelerin özetinden türetilir) da değişti. Tek iş parçacığıyla iki çalıştırma birebir aynı sonucu verdi. Bu, ölçümü tekrarlanabilir kılmak için yaptığımız bir ayardır; git'in genel davranışı hakkında bir iddia değildir.

Paketin içine bakmak için `verify-pack` kullanılır. Her satır bir nesnedir:

```term
$ git verify-pack -v .git/objects/pack/*.idx | cut -c1-74
0d41b2fb8133f155d38f51932175471eba6fbe3b blob   52500 10426 30429
4226b7149277676432aa875c29bcadb07de6fb2a blob   23 36 40951 1 0d41b2fb8133
52806c5ba7094e73c29d07e0eb4190fc59957871 blob   22 34 41035 2 4226b7149277
...
chain length = 50: 101 objects
```


Sütunlar sırasıyla: nesne adı, tür, `size`, `size-in-pack`, paketteki `offset` (konum), `depth` (derinlik) ve delta ise temel nesnenin adı. İlk satır tam saklanmış temel blob'dur: 52500 bayt, pakette 10426 bayt (sıkıştırılmış). İkinci satır (`4226b714`) bir delta, derinliği 1: 23 baytlık delta verisi. Üçüncü satır (`52806c5b`) derinliği 2 olan bir delta; `size` sütunu burada 22 gösteriyor, ama bu nesnenin gerçek boyutu değil, delta verisinin boyutudur. Doğrulamak için:

```term
$ git cat-file -s 52806c5ba7094e73c29d07e0eb4190fc59957871
52500
```

Nesnenin gerçek boyutu 52500 bayttır; pakette yalnızca 22 baytlık bir fark tutuluyor. Bu, `olcum.log`'un her sürümünün neden küçük bir ekleme gibi saklandığını açıklar.

`depth` sütunu, bir nesneyi okumak için kaç delta uygulanması gerektiğini söyler. Git varsayılan olarak derinliği 50 ile sınırlar (`pack.depth` varsayılanı 50, git 2.43 belgesinden). Bu deneme deposunda 101 nesne tam sınırda, derinlik 50'de duruyor. Derinlik sınırının bedeli okuma maliyetidir: bir nesneyi okumak için 50 delta uygulanır. Kazancı disk alanıdır. Bu takasın yönünü ayarlamak sana kalmış.

![Şekil 38.7: Paketleme ölçümü. Solda delta derinliklerinin dağılımı: nesnelerin çoğu 44-50 aralığında, en büyük küme sınırdaki 50'de. Sağda gevşek nesnelerin ve paketin toplam boyutu.](gorseller/b38_delta_zinciri.png)

Bir noktayı daha not et: bu depoda tüm commit ve tree nesneleri tam olarak saklandı (201 commit, 201 tree); delta yalnızca blob'larda kullanıldı (1 tam, 200 delta). Commit'ler ve tree'ler küçük olduğu için delta kazancı az, ama kalıp genellikle aynıdır: büyük ve az değişen dosyalar (lock dosyaları, veri setleri, ikili dosyalar) paketlemede en çok kazancı getirir.

::: baglanti
Paketleme, nesne deposunun "sıkıştırılmış" halidir. Bölüm 35'te LSM ağaçlarında birleştirme (compaction) ile okuma-yazma-alan (write amplification) dengesini gördün; git paketlemesinde de benzer bir takas var: birleştirme (gc) disk alanı kazandırır, ama okuma derinliğini artırır.
:::

## 38.8 Uzak depolar ve iş akışları

Bölüm 4.10'da uzak deponun ne olduğunu ve `clone`, `pull`, `push` döngüsünü gördün. Burada iki şeyi derinleştiriyoruz: uzak depo ile yerel depo arasındaki referans eşlemesini ve birden fazla geliştirici aynı dalda çalıştığında ne olduğunu.

Uzak depoyu gerçek bir sunucu gibi kurmak için **çıplak depo** (bare repository) kullanılır: çalışma dizini yoktur, yalnızca nesneler ve referanslar vardır. Yerel makinede bunu bir dizin olarak simüle edebiliriz:

```term
$ git init -q --bare -b main uzak.git
$ git clone -q uzak.git a
$ git clone -q uzak.git b
```

İki geliştirici, `a` ve `b`, aynı uzak depoyu klonladı. Önce `b` bir commit gönderiyor; sonra `a` uzaktan geride kaldığı hâlde kendi commit'ini göndermeye çalışıyor:

```term
$ cd b && git commit -qam "b degisikligi" && git push -q origin main
$ cd ../a && git commit -q -m "a: yeni dosya"
$ git push origin main
 ! [rejected]        main -> main (fetch first)
error: failed to push some refs to '.../uzak.git'
...
hint: the same ref. If you want to integrate the remote changes, use
hint: 'git pull' before pushing again.
```

Git push'u reddetti, çünkü uzak `main` yerel `main`'in atası değil; uzakta senin görmediğin bir commit var. Bu, **hızlı ileri olmayan** (non-fast-forward) durumun koruması: uzak dalın tarihçesi üzerine yazılmasın diye git reddeder. Çözüm, önce uzağı çekmek ve birleştirmektir. Önce `fetch` ile ne olduğuna bakalım:

```term
$ git fetch -q origin && git log --oneline --graph --all
* 706334a a: yeni dosya
| * eb48909 b: sonuna ekle
|/
* 2704823 ilk surum
$ git rev-parse --abbrev-ref --symbolic-full-name @{u}
origin/main
```

`fetch` yalnızca uzak referansları günceller (`refs/remotes/origin/main` gibi) ve dosyalarına dokunmaz. `@{u}` yazımı, mevcut dalın izleme dalını (upstream) verir: `origin/main`. `pull`, `fetch` ile `merge`'ün birleşimidir. Burada dallar ayrılmış olduğu için bir birleşme commit'i oluşur:

```term
$ git pull -q --no-rebase --no-edit && git push -q origin main
$ git log --oneline --graph | head -4
*   d40c569 Merge branch 'main' of .../uzak
|\
| * eb48909 b: sonuna ekle
* | 706334a a: yeni dosya
```

Bu sefer push başarılı oldu. Şimdi aynı satırda çakışma yaratalım: `b` satır 2'yi değiştirip gönderiyor; `a` de aynı satırı farklı değiştiriyor, ardından çekmeye çalışıyor:

```term
$ cd ../b && git pull -q --no-rebase --no-edit
$ sed -i 's/satir2/B-satir2/' not.txt && git commit -qam "b: satir2"
$ git push -q origin main
$ cd ../a && sed -i 's/satir2/A-satir2/' not.txt && \
  git commit -qam "a: satir2"
$ git pull --no-rebase --no-edit
Auto-merging not.txt
CONFLICT (content): Merge conflict in not.txt
$ sed -n 2,6p not.txt
<<<<<<< HEAD
A-satir2
=======
B-satir2
>>>>>>> 4afb48f70a260345dc2a3a64217251fa8988b5b5
```

Çakışma çözmenin yöntemi Örnek 3'te olduğu gibidir: üç sürümü (taban, senin, uzak) göz önünde tutarak doğru metni yazarsın, sonra `add` ve `commit` yaparsın. Burada önemli olan, çakışmanın uzak depoyu değil yerel birleştirmeyi etkilemesidir: çözülmeden push etmek mümkün değildir.

`pull`'un `--no-rebase` ya da `--rebase` ile açıkça çağrılması iyi bir alışkanlıktır: pull'un varsayılan davranışı ve uyarıları git sürümüne ve yapılandırmaya göre değişebilir. Hangi davranışı istediğini kalıcı kılmak için `pull.rebase` yapılandırması vardır, ama ekip içinde tutarlı olması şarttır.

Referansların nasıl eşlendiğini yapılandırma dosyasında görebilirsin:

```term
$ git config --get-all remote.origin.fetch
+refs/heads/*:refs/remotes/origin/*
$ git ls-remote origin
4afb48f70a260345dc2a3a64217251fa8988b5b5	HEAD
4afb48f70a260345dc2a3a64217251fa8988b5b5	refs/heads/main
```

`+refs/heads/*:refs/remotes/origin/*` bir **refspec**'tir: uzaktaki `refs/heads/` altındaki her dalı, yerelde `refs/remotes/origin/` altına eşler. Başındaki `+` işareti, fetch sırasında hızlı ileri olmayan güncellemelere de izin verir. Bu, uzak referansların yerel kopyasıdır ve yerel dalınla karışmaz.

Şimdi, az önce gördüğümüz bir tehlikeyi yeniden ele alalım: paylaşılmış bir commit'i yeniden yazmak. `b` daha önce gönderdiği commit'in mesajını düzeltmek için `--amend` kullanıyor:

```term
$ git commit -q --amend -m "b: satir2 (mesaj duzeltildi)"
$ git push origin main
 ! [rejected]        main -> main (non-fast-forward)
$ git push --force-with-lease origin main
 + 4afb48f...1725e6a main -> main (forced update)
```

Normal push reddedildi, çünkü commit'in hash'i değişti. `--force-with-lease` ile uzağı zorla güncelledi. Bu, "uzak dal beklediğim commit'te ise yaz" anlamına gelir; ama uzakta başka biri yeni bir commit koyduysa reddeder. Yine de sorun bitmedi: `a`'nın yerel dalında eski `4afb48f` commit'i var ve artık uzakla hiçbir ilişkisi yok:

```term
$ cd ../a && git fetch -q && git log --oneline --graph --all -4
* 1725e6a b: satir2 (mesaj duzeltildi)
| * 3f470d8 a: satir2
|/
*   d40c569 Merge branch 'main' of .../uzak
```

Bu, paylaşılmış geçmişi yeniden yazmanın bedelidir: başka bir geliştiricinin tarihçesi ile senin tarihçen ayrışır ve birini diğerine birleştirmek zorunda kalırsın. Kural basit: paylaşılmış dalı rebase etme, yalnızca yerel ve kendi dalında yeniden yaz.

### Pull request ve gözden geçirme

Ekip çalışmasında değişiklik doğrudan `main`'e push edilmez. Bunun yerine değişiklik bir özellik dalında geliştirilir ve bir **pull request** (GitHub'daki adı) ya da **merge request** (GitLab'daki adı) açılır. Bu, dalın hedef dala birleşmeden önce gözden geçirilmesini sağlayan bir kapıdır: bir ya da daha fazla kişi satır satır inceler, testler çalışır, onay verilir ve ancak ondan sonra birleşir. Korumalı dal (protected branch) kuralları, doğrudan push'u engelleyerek bu kapıyı zorunlu kılar.

Savunma sanayiinde kod genellikle internete çıkmaz; bunun yerine kurum içinde çalışan bir GitLab ya da Gitea sunucusu kullanılır. Komutlar aynıdır, değişen yalnızca sunucunun adresidir. Pull request'in amacı kişisel değil, kayıt içindir: kim neyi neden onayladı, hangi testlerden geçti, bu bilgi sonradan denetlenebilir.

### Üç iş akışı

İş akışı, ekibin dalları nasıl açtığını, birleştirdiğini ve sürüm çıkardığını tanımlar. Üç yaygın model var:

| Ölçüt | Trunk-based | GitHub Flow | Git Flow |
|---|---|---|---|
| Ana dal | `main` (tek çizgi) | `main` (her zaman dağıtılabilir) | `main` (sürümler) + `develop` |
| Dal ömrü | Saatler, en fazla bir gün | Birkaç gün | Haftalar |
| Birleştirme sıklığı | Günde birkaç kez | Her özellikte | Sürüm dalına göre |
| Sürüm yönetimi | Sürekli dağıtım, özellik bayrakları | Her birleşmede dağıtım | `release` ve `hotfix` dalları |
| Uygun durum | Sık dağıtım, olgun test | Web uygulamaları, küçük ekipler | Planlı sürümler, birden çok sürüm |

Bu karar tablosu genel bilgi olarak, yaygın uygulamalara dayanır; bunlar kesin kurallar değildir. Ekibin büyüklüğü, dağıtım sıklığı ve test olgunluğu hangi modelin uygun olduğunu belirler. Planlı sürümler ve sertifikasyon gerektiren bazı savunma projelerinde Git Flow benzeri, sürüm dallı bir model tercih edilebilir; ama birleşmelerin küçük ve sık olması yine de geçerlidir.

![Şekil 38.8: İş akışı karşılaştırması. Trunk-based'de kısa dallar tek bir ana çizgiye sık sık birleşir. Git Flow'da sürüm ve özellik dalları ayrı hatlarda yaşar ve birleşmeler daha seyrek olur.](gorseller/b38_is_akislari.png)

Hangi modeli seçersen seç, bir ilke değişmez: dallar kısa ömürlü ve küçük olsun. Uzun ömürlü bir dal, her gün `main` ile ayrışır ve birleştirme anında acı verir. Bu, Bölüm 4'te söylediğimiz "değişiklik dalda gelişir, gözden geçirme sonrası birleşir" kuralının ekip ölçeğindeki halidir.

## 38.9 Commit disiplini: atomik commit, mesaj ve yerel kancalar

Tarihçenin kalitesi, ne commit ettiğine ve onu nasıl adlandırdığına bağlıdır. Üç ilke bu disiplinin çekirdeğidir:

1. **Atomik commit**: bir commit, tek bir mantıksal değişiklik taşır. Bir hata düzeltmesi ile bir biçimlendirme aynı commit'te olursa, sonradan birini geri almak istediğinde ikincisi de gider. Bölüm 23'te biçimlendirmeyi ayrı bir commit'te yapmayı söylemiştik; bunun nedeni budur.
2. **Anlamlı mesaj**: ilk satır kısa bir özet olsun, boş satırdan sonra "neden" anlatılsın. Kod ne yaptığını zaten söyler; mesaj neden değiştiğini söylemelidir.
3. **Derlenebilir commit**: Her commit, en azından derlenebilir olmalıdır. Bu, Bölüm 38.11'deki `bisect`'in çalışması için gereklidir; derlenmeyen bir commit'te ikili arama yanlış yönlere gider.

Mesaj için yaygın bir kalıp, konvansiyonel commit biçimidir: `tür(kapsam): açıklama`, örneğin `fix(io): satır sonu hatasını düzelt`. Bu, Conventional Commits belirtiminden gelen bir düzendir (genel bilgi). Burada bu düzeni bir hook ile zorunlu kılacağız.

Atomik commit'i pratikte yapmanın yolu `git add -p`'dir. Dosyanın her değişikliğini (hunk) tek tek sorar ve yalnızca istediklerini sahneye alırsın. Etkileşimli soruları yanıtlamak için girdiyi bir borudan da verebiliriz. Aşağıda iki farklı yerde değişen bir dosyadan, yalnızca birincisini sahneye alıyoruz:

```term
$ seq 1 30 | sed 's/^/satir /' > mat.c
$ git add mat.c && git commit -q -m "taban"
$ sed -i 's/satir 2$/satir 2 DEGISTI/; \
  s/satir 25$/satir 25 DEGISTI/' mat.c
$ printf 'y\nn\n' | git add -p mat.c
@@ -22,7 +22,7 @@ satir 21
(1/2) Stage this hunk [y,n,q,a,d,k,K,j,J,g,/,e,p,P,?]?
(2/2) Stage this hunk [y,n,q,a,d,K,J,g,/,e,p,P,?]?
$ git diff --cached | grep '^[+-]satir'
-satir 2
+satir 2 DEGISTI
$ git diff | grep '^[+-]satir'
-satir 25
+satir 25 DEGISTI
```

İlk hunk (`y`) sahneye alındı, ikincisi (`n`) çalışma dizininde kaldı. Bu, bir commit'e neyin gireceğini kontrol etmenin en doğrudan yoludur. Git'in hunk'ları birleştirmesi, değişikliklerin arasında yeterince boş satır (bağlam satırı) olmasına bağlıdır; iki değişiklik birbirine yakınsa tek hunk olarak gelir ve onları ayıramazsın. Bu durumda `e` (edit) ile hunk'ı elle bölebilirsin.

Commit mesajı ve biçim denetimi, bir sonraki bölümde kurduğumuz kancanın işidir. Kancalar her commit'te otomatik çalışır; ama ekip kuralı olarak öğrenilmezlerse işe yaramazlar. Bu yüzden önce kancanın nerede durduğunu görelim.

### Git hook'ları ve core.hooksPath

Git, belirli olaylarda çalışacak betikleri (hook) destekler. `pre-commit` commit oluşturulmadan hemen önce, `commit-msg` mesaj dosyası hazır olduğunda, `pre-push` push'tan önce çalışır. Şekil 38.9 bu olayların sırasını gösterir.

![Şekil 38.9: Hook'ların yaşam döngüsündeki yeri. pre-commit ve commit-msg commit'ten önce; pre-push push'tan önce çalışır. Sunucu tarafındaki kontroller en sondadır ve atlanamaz.](gorseller/b38_hook_yasam.png)

Hook'lar varsayılan olarak `.git/hooks` klasöründe durur, ama bu klasör sürüm kontrolüne girmez; yani ekip arkadaşların hook'larını almaz. Çözüm, hook'ları depo içinde bir klasörde tutup git'e oraya bakmasını söylemektir:

```term
$ git config --local core.hooksPath .githooks
```

Bu ayar her klonda ayrı ayrı yapılmalıdır. Ekipte bunu bir kurulum betiğine koymak gerekir; yoksa her geliştirici bunu kendisi unutabilir. Burada yalnızca yerel bir ayarın etkisini gördük.

### Denetleyici: indekse bakan pre-commit

Commit'ten önce neyi kontrol etmeliyiz? Çalışma dizinindeki dosyalara mı, yoksa commit'e gerçekten girecek olan indeks içeriğine mi? Bu fark önemlidir. Bir dosyayı sahneledikten sonra üzerinde değişiklik yapıp sahnelemeden commit edersen, commit'e giren sürüm çalışma dizinindeki değil, sahnelenmiş sürümdür. Denetleyici bu yüzden `git show :yol` ile indeksteki bayt dizisini okur. Aşağıdaki betik, 80 karakterden uzun satırları, bilinen sır desenlerini ve 1 MB'tan büyük dosyaları reddeder:

```python
# -*- coding: utf-8 -*-
"""pre-commit denetimi: sahnelenmiş (indeksteki) içeriğe bakar."""
import re
import subprocess
import sys

SATIR_LIMITI = 80
BUYUK_DOSYA = 1024 * 1024      # 1 MB
METIN = (".py", ".c", ".h", ".md", ".txt", ".cpp")
SIR = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS erişim anahtarı benzeri"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
     "özel anahtar"),
]


def git(*args):
    sonuc = subprocess.run(["git"] + list(args), check=True,
                           capture_output=True)
    return sonuc.stdout


def sahnelenmis_dosyalar():
    cikti = git("diff", "--cached", "--name-only",
                "--diff-filter=ACM")
    return cikti.decode("utf-8").splitlines()
```

Betiğin ikinci yarısı, dosyaları tek tek denetleyen ve sonucu raporlayan kısımdır:

```python
def denetle_dosya(yol):
    hatalar = []
    icerik = git("show", ":" + yol)   # indeksteki bayt dizisi
    if len(icerik) > BUYUK_DOSYA:
        return ["%s: 1 MB'tan büyük (%d bayt)" % (yol, len(icerik))]
    if not yol.endswith(METIN):
        return hatalar
    metin = icerik.decode("utf-8", errors="replace")
    for no, satir in enumerate(metin.splitlines(), 1):
        if len(satir) > SATIR_LIMITI:
            hatalar.append("%s:%d satır %d karakter"
                           % (yol, no, len(satir)))
        for desen, ad in SIR:
            if desen.search(satir):
                hatalar.append("%s:%d olası sır: %s"
                               % (yol, no, ad))
    return hatalar


def main():
    hatalar = []
    for yol in sahnelenmis_dosyalar():
        hatalar += denetle_dosya(yol)
    for h in hatalar:
        print("HATA", h)
    if hatalar:
        print("Commit reddedildi: %d sorun." % len(hatalar))
        return 1
    print("pre-commit: temiz")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Bu betik bir commit'i reddetmek için çıkış kodu 1 döndürür. Git, pre-commit'in sıfırdan farklı çıkış kodunu commit'in iptali olarak yorumlar. Hook betikleri `.githooks/pre-commit` dosyasında yalnızca şu satırdan ibarettir:

```bash
#!/bin/sh
exec python -I -X utf8 tools/denetle.py
```

`-I` bayrağı Python'u izole modda çalıştırır; ortamdaki `PYTHON*` değişkenlerini yok sayar. Bu yüzden Türkçe çıktı için `PYTHONIOENCODING` yetmez, `-X utf8` gerekir. Bu, deneylerimizde karşılaştığımız gerçek bir tuzaktı: Windows konsolunda `satır` kelimesi `sat�r` olarak bozuldu.

### Mesaj denetimi: commit-msg

`commit-msg` hook'u mesaj dosyasının yolunu `$1` ile alır. Burada ilk satırı konvansiyonel biçimle karşılaştırıyoruz:

```python
# -*- coding: utf-8 -*-
"""commit-msg denetimi: konvansiyonel commit biçimi."""
import re
import sys

DESEN = re.compile(
    r"^(feat|fix|docs|refactor|test|chore)(\([a-z0-9-]+\))?: .+")


def main(yol):
    with open(yol, encoding="utf-8") as f:
        ilk = f.readline().rstrip("\n")
    if not DESEN.match(ilk):
        print("commit-msg: biçim hatalı -> '%s'" % ilk)
        print("beklenen: tür(kapsam): kısa açıklama")
        return 1
    if len(ilk) > 72:
        print("commit-msg: ilk satır 72 karakteri aşıyor")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
```

Şimdi hook'ları bir deponun içinde deneyelim. Önce bir depo kur, kancayı bağla ve beş durumu sına. Yukarıdaki iki betik `tools/` altına, iki sarmalayıcı kabuk betiği `.githooks/` altına konmuş olsun: temiz bir dosya, uzun satır, sahte bir anahtar, kötü bir mesaj ve sahnelenmemiş bir sırrın durumu:

```term
$ git init -q -b main hk && cd hk
$ git config --local core.hooksPath .githooks
$ mkdir -p tools .githooks
$ git add . && git commit -q -m "chore(hook): denetim betikleri"
pre-commit: temiz
$ echo 'print("merhaba")' > ok.py && git add ok.py
$ git commit -q -m "feat(io): merhaba yazdır"
pre-commit: temiz
$ python -c "print('x'*90)" > uzun.py && git add uzun.py
$ git commit -q -m "fix(io): uzun satır"
HATA uzun.py:1 satır 90 karakter
Commit reddedildi: 1 sorun.
$ echo 'K = "AKIA0123456789ABCDEF"' > anahtar.py && git add anahtar.py
$ git commit -q -m "feat(auth): anahtar"
HATA anahtar.py:1 olası sır: AWS erişim anahtarı benzeri
Commit reddedildi: 1 sorun.
$ echo "x" > k.txt && git add k.txt
$ git commit -q -m "düzeltme"
pre-commit: temiz
commit-msg: biçim hatalı -> 'düzeltme'
beklenen: tür(kapsam): kısa açıklama
```

Son senaryo önemlidir: `git commit` iki kancayı da çalıştırdı. Pre-commit temiz çıktı (dosya sorunsuz), commit-msg mesajı reddetti. Şimdi indeks ilkesini sınayalım: sahnelenmemiş bir sır commit'i engeller mi?

```term
$ echo 'K = "AKIA0123456789ABCDEF"' >> ok.py
$ echo "temiz satir" > temiz.txt && git add temiz.txt
$ git commit -q -m "docs(not): temiz dosya"
pre-commit: temiz
$ git status --short
 M ok.py
$ git checkout -q -- ok.py
```

Commit başarılı oldu, çünkü `ok.py` içindeki sır sahnelenmemişti ve pre-commit yalnızca indekse baktı. Bu, denetleyicinin doğru çalıştığının kanıtıdır; ama aynı zamanda bir uyarıdır: yerel bir kanca, bilinçli veya kazara sahnelenmemiş bir değişikliği göremez. Bu yüzden kancanın yanına sunucu tarafında bir kontrol gerekir.

Yerel kancaların bir sınırı daha var: `git commit --no-verify` (ya da `-n`) hook'ları atlar; belgeye göre hem pre-commit hem de commit-msg bu bayrakla baypas edilir (git 2.43 belgesinden). Kancalar bir disiplin aracıdır, bir güvenlik sınırı değildir. Gerçek kapı sunucudadır: korumalı dal, zorunlu gözden geçirme ve CI'da aynı denetimlerin yeniden çalıştırılması. CI'nın kendisi ve test çalıştırma Bölüm 39'un konusudur; konteyner ve dağıtım tarafı Bölüm 42'dedir. Burada yalnızca bağlantıyı kuruyoruz: yerelde hızlı geri bildirim, sunucuda zorunlu kapı.

::: dikkat
Bu hook'lar yalnızca yerel hızlı geri bildirim sağlar. Ekip arkadaşın `--no-verify` ile atlayabilir, başka bir makineden de commit edebilirsin. Güvenlik kararı sunucu tarafında verilmelidir; yerel betiğe güvenmek, güvenlik açığını dokümanla kapatmaya benzer.
:::

## 38.10 Gizli bilgiler, büyük dosyalar ve iz sürülebilirlik

### .gitignore: izlenmeyecekler

Derleme çıktıları (`*.o`, `uygulama`), geçici dosyalar ve yerel ayarlar tarihe girmemelidir. Bunun için proje köküne bir `.gitignore` koyulur. Kuralların sırası önemlidir: son eşleşen kural kazanır, `!` ile başlayan kural ise bir önceki hariç tutmayı geri alır. Deneyelim:

```term
$ printf '*.o\nbuild/\n!onemli.o\n' > .gitignore
$ touch a.o onemli.o main.c && mkdir build && touch build/x
$ git check-ignore -v a.o onemli.o build/x main.c
.gitignore:1:*.o	a.o
.gitignore:3:!onemli.o	onemli.o
.gitignore:2:build/	build/x
$ git status --short --ignored
?? .gitignore
?? main.c
?? onemli.o
!! a.o
!! build/
```

`check-ignore -v` hangi kuralın bir yolu eşleştirdiğini gösterir. `main.c` için satır yoktur, çünkü hiçbir kural eşleşmez ve dosya izlenir. `onemli.o` için `!` kuralı en son eşleşen olduğu için dosya görünür kalır. Dikkat: `.gitignore` yalnızca izlenmemiş dosyaları etkiler. Önceden commit edilmiş bir dosyayı yoksaymaya başlamak için önce `git rm --cached` ile izlemeyi bırakman gerekir (genel bilgi).

Büyük ikili dosyalar (veri setleri, model ağırlıkları, derlenmiş kütüphaneler) için normal git tarihçesi uygun değildir; her sürüm tam boyutta saklanır ve depo şişer. Git LFS bu dosyaları ayrı bir depoda tutup yerelde işaretçi (pointer) bırakır (genel bilgi). Alt modüller ve alt ağaçlar (subtree) ise başka bir depoyu bu depoya bağlamanın iki yoludur: alt modül, dış depoya sabit bir commit'i işaret eder; alt ağaç, dış kodu bu depoya kopyalar. Her ikisinin de bedeli vardır; ayrıntısı bu bölümün kapsamı dışındadır (genel bilgi).

### Sırlar tarihçede kalır

Bir API anahtarını yanlışlıkla commit ettiğini düşün. Sonra onu kaldırıp yeni bir commit yaptın. Güvende misin? Hayır. Deneyelim:

```term
$ git log --oneline
d4adc90 anahtar kaldirildi
587a570 api anahtari eklendi
9a23df8 ayarlar
$ git show HEAD~1:ayar.env
uygulama=1
API_ANAHTARI=AKIAIOSFODNN7EXAMPLE
$ git log --oneline -S "AKIAIOSFODNN7EXAMPLE"
d4adc90 anahtar kaldirildi
587a570 api anahtari eklendi
```

(Bu anahtar, AWS'in belgelerindeki örnek değeridir; gerçek bir anahtar değildir.) Anahtar HEAD'de yok, ama `HEAD~1` içinde açıkça duruyor ve `log -S` (pickaxe, 38.11'de ayrıntılı) bu değişikliği getiren commit'leri bulur. Yani klonlayan herkes bu geçmişi görebilir. Bu nedenle doğru sıra şudur:

1. **Anahtarı iptal et ve yenisini üret.** Sızıntının sonucu, anahtarın artık güvende olmadığını kabul etmektir. Bu, tarihçeyi temizlemekten önce gelir.
2. **Tarihçeyi yeniden yaz (isteğe bağlı).** Tarihçeden silmek için `git filter-repo` gibi araçlar kullanılır (genel bilgi; eski `git filter-branch` yerine önerilir). Bu işlem her commit'in hash'ini değiştirir, bu yüzden tüm ekibin klonlarını yeniden kurmasını gerektirir ve paylaşılmış depoda zorla güncelleme ister.
3. **Önleyici tedbir.** `pre-commit` içine sır desenlerini koy (yukarıda yaptığımız gibi), sunucuda tarama (secret scanning) aç.

Sıra önemlidir: önce iptal, sonra temizlik. Tarihçeyi yeniden yazmak yetmez, çünkü önbellekler, forklar ve klonlar eski commit'i tutabilir.

::: ipucu
Yeni bir depo açarken `.gitignore`'u ilk commit'ten önce koy. Sır dosyalarını (`.env`, anahtar dosyaları) baştan ignore et ve örnek bir `.env.example` dosyası bırak. Sonra commit edilen sırrı geri almak her zaman daha pahalıdır.
:::

### İz sürülebilirlik ve imzalı commit'ler

Savunma projelerinde "bu kod neden burada, kim onayladı, hangi testten geçti?" soruları kayıt gerektirir. Git bu kaydın omurgasıdır: her commit kimin, ne zaman, neyi değiştirdiğini tutar. Bunu bir denetim izine dönüştürmek için üç katman eklenir:

- **Gereksinim bağlantısı**: commit mesajına veya bir trailer'a (`Refs: GEREK-12` gibi) gereksinim kimliği konur. Gereksinimden koda, koddan teste izi süren bir matris oluşur.
- **Test bağlantısı**: her gereksinimin testi, aynı commit'te ya da onu izleyen bir commit'te yer alır. Bölüm 39'da testin kendisini göreceksin.
- **İmzalı commit**: `git commit -S` commit'i bir GPG anahtarıyla imzalar; `git log --show-signature` imzayı doğrular (genel bilgi, anahtar kurulumu gerektirir). İmza, commit'in iddia edilen yazardan geldiğini ve sonradan değiştirilmediğini kanıtlamaya yardım eder.

Bu katmanlar gerçek bir süreçte ancak araçla desteklenirse çalışır. Kural olarak: her commit bir gereksinime bağlansın, her gereksinim bir teste bağlansın, ve her birleşme (merge) gözden geçirilmiş olsun.

## 38.11 Hata avında git: blame, pickaxe ve bisect run

Bir hata bulduğunda sorular üç türdür: bu satır kim tarafından ne zaman yazıldı, hangi değişiklik bu davranışı değiştirdi, ve bir regresyon tam olarak nerede girdi? Git her biri için bir araç sunar.

**blame** bir dosyanın her satırının son değişikliğini hangi commit'in yaptığını gösterir:

```term
$ git blame -L 1,1 limit.txt
e1c22f24 (Kitap Deneme 2026-01-10 19:00:00 +0300 1) limit=99
```

Bu, `limit=99` satırını `e1c22f24` commit'inin getirdiğini söyler. Dikkat: blame, o satırı en son kimin değiştirdiğini gösterir; hatanın nedeni çoğu zaman başka bir yerdedir. Kodu taşımış ya da yeniden biçimlendirmiş bir commit, suçlu gibi görünebilir. Bu yüzden blame'den sonra o commit'in diff'ine bakmak ve bağlamı okumak gerekir.

**log -S** (pickaxe) bir metnin sayısının değiştiği commit'leri bulur; yani "bu dizgiyi ilk ekleyen ya da kaldıran commit hangisi?" sorusunu yanıtlar. Düzenli ifade ile aramak için `log -G` vardır (genel bilgi).

```term
$ git log --oneline -S "limit=99"
e1c22f2 is 91
```

Şimdi en güçlü araca gelelim: `bisect run`. Bölüm 6'da (Örnek 3) `git bisect` ile elle ikili arama yapmıştık; burada test betiğiyle otomatikleştiriyoruz. Deneme deposu 128 commit içeriyor; `limit.txt` dosyasındaki değer 91. commit'te `limit=100`'den `limit=99`'a değişiyor ve sonraki tüm commit'lerde bu kalıyor. Test betiği, değerin 100 olup olmadığını kontrol ediyor:

```bash
#!/bin/sh
# iyi (0) = limit 100 ; kotu (1) = degil
grep -q "^limit=100$" limit.txt
```

Bisect'i başlatıp test betiğini çalıştırıyoruz. `bad` ilk kötü, `good` ilk iyi commit'tir:

```term
$ git bisect start
status: waiting for both good and bad commits
$ git bisect bad HEAD
status: waiting for good commit(s), bad commit known
$ git bisect good HEAD~127
Bisecting: 63 revisions left to test after this (roughly 6 steps)
[d473314f81f25200fa39a8a769fb9a88e6bd8008] is 64
$ git bisect run sh test.sh
Bisecting: 31 revisions left to test after this (roughly 5 steps)
Bisecting: 15 revisions left to test after this (roughly 4 steps)
Bisecting: 7 revisions left to test after this (roughly 3 steps)
Bisecting: 3 revisions left to test after this (roughly 2 steps)
Bisecting: 1 revision left to test after this (roughly 1 step)
Bisecting: 0 revisions left to test after this (roughly 0 steps)
e1c22f24dd4cfbbdc2456f88d2d8019c53e94ae9 is the first bad commit
$ git bisect reset
```

Çıktı yalnızca bisect'in ilerleme satırlarıyla sınırlandırıldı; test betiğinin kendi ayrıntıları çıkarıldı. Yedi test, 128 aday commit'i eledi: 2⁷ = 128. Şekil 38.10 kalan aday sayısının her adımda yarıya indiğini gösterir.

![Şekil 38.10: git bisect run ilerlemesi. Her adımda kalan aday sayısı yaklaşık yarıya iner; yedinci adımda tek aday kalmadı, suçlu commit belirlendi.](gorseller/b38_bisect_ikili.png)

İkili arama Bölüm 14'te anlattığımız fikirdir: sıralı bir dizide yarılayarak aramak. Burada dizi, commit geçmişidir ve sıralılık "iyi" ile "kötü" arasındaki tek geçişle sağlanır. Bu varsayım önemlidir: regresyon bir kez girdikten sonra kalıcı olmalıdır (monoton). Test deterministik değilse (ara sıra geçip ara sıra kalan bir test) ya da bir commit derlenmiyorsa, ikili arama yanlış sonuç verebilir.

Git bu durumlar için özel bir çıkış kodu tanımlar: test betiği 125 dönerse commit "atlanır" (skip), 1-127 arası (125 hariç) dönerse commit kötü sayılır (git-bisect belgesinden). Derlenmeyen bir commit için `exit 125` kullanmak bu yüzden doğru çözümdür: `make || exit 125` gibi.

::: baglanti
Bölüm 6'daki hata ayıklama döngüsünün 2. adımı ("izole et") bisect'in elle hâliydi. Burada aynı mantık bir test betiğine bağlandı; ama disiplin aynı: bisect teşhis koymaz, yalnızca aday alanını daraltır. Bölüm 6'nın Örnek 3'ü bu fikri elle çözmüştü.
:::

Bisect'in gücü, commit'lerin küçük olmasından gelir. Yüz dosyayı değiştiren tek bir commit'te bisect yalnızca "şu commit kötü" der, nedenini söylemez. Bu yüzden 38.9'daki atomik commit ilkesi, hata avının ön koşuludur.

## Çözümlü Örnekler

Dört örnek, zorluk sırasına göre: ★, ★★, ★★, ★★★. Her birinde Bölüm 5'in altı adımını izliyoruz. Adım 6'da elle iz sürme tablosu var; kendi çözümünü bununla karşılaştır.

### Örnek 1 (★): Bir blob, tree ve commit'in hash'ini elle hesapla

**Problem:** `mat.c` dosyası (67 bayt) içeren iki commit'lik deneme deposunda, ilk commit'in tree'sini ve ikinci commit'in tree'sini git'e sormadan Python'da hesapla. Üç hash de `git`'in kendi çıktısıyla eşleşmeli.

**Adım 1 — Anla.** Git bir nesnenin adını, başlık ile gövdenin SHA-1'i olarak tanımlar. Blob'un başlığı `blob 67\0`, gövdesi dosyanın ham baytlarıdır. Tree'nin gövdesi ikilidir ve girdileri ada göre sıralıdır. Commit'in gövdesi düz metindir.

**Adım 2 — Örnekle.** `mat.c` 67 bayt, `mat.h` 17 bayt. İki commit var; ikincisi `kup` fonksiyonunu ekledi, ebeveyni ilk commit.

**Adım 3 — Kaba çöz.** En basit yol kabukla başlığı elle yazıp bir özet aracına vermektir. Bu, Python betiğinin yerini tutmaz ama doğru olduğunu anlamak için iyi bir ilk adımdır:

```term
$ (printf 'blob 67\0'; cat mat.c) | sha1sum
792c31b1273edc275c3980d9f8d18266bab3b013  -
$ git hash-object mat.c
792c31b1273edc275c3980d9f8d18266bab3b013
```

Bu, blob için yeterli. Ama tree ve commit için de aynısını yapmak, her birinin gövdesini elle baytlamak demektir. Daha iyisi bir kez yazılmış bir fonksiyon.

**Adım 4 — Örüntü.** Üç nesnede de kalıp aynıdır: `tür boyut\0` başlığı + gövde + SHA-1. Değişen tek şey gövdenin biçimidir: blob için ham bayt, tree için `mod ad\0ham20` girdileri, commit için metin satırları. Bu, tek bir `nesne_hash(tur, govde)` fonksiyonunun üç çağrıyla yetebileceği anlamına gelir.

**Adım 5 — İyileştir.** Bölüm 38.1'deki `kendin_hash.py` betiği bu örüntüyü uygular: blob, tree ve commit için tek fonksiyon, sonunda git ile karşılaştırma. Tree girdilerini ada göre sıralamayı unutma; git bunu bekler.

**Adım 6 — Doğrula.** Betiği çalıştırdığında ve her nesnenin boyutunu `nesne_oku.py` ile okuduğunda şu iz tablosunu elde ederiz:

| Nesne | Gövde boyutu | Başlık | Python hash'i | `git` hash'i | Eşleşme |
|---|---|---|---|---|---|
| blob `mat.c` | 67 | `blob 67\0` | 792c31b1… | 792c31b1… | evet |
| tree (ikinci) | 66 | `tree 66\0` | 7df8cc96… | 7df8cc96… | evet |
| commit (ikinci) | 226 | `commit 226\0` | a9594064… | a9594064… | evet |

Gövde boyutlarını iz tablosunda `nesne_oku.py`'nin çıktısından aldık: tree 66, commit 226 bayt. Bu üç satır aynı kalıbın üç uygulamasıdır.

**Bunu AI'sız yazabilir misin?** `mat.c`'ye sondan bir boşluk eklediğinde blob hash'in değişeceğini tahmin et. Tree hash'i de değişir mi, neden? Tahminini yaz, sonra `printf 'a ' >> mat.c` ile dosyayı değiştirip `git hash-object` ve betikle doğrula.

### Örnek 2 (★★): Reset ile kaybolan commit'i reflog'dan kurtar

**Problem:** Üç commit'lik bir depoda son commit (`deneysel is`) yanlışlıkla `git reset --hard HEAD~1` ile gitti. Commit'i geri getir ve dosyanın içeriğini doğrula.

**Adım 1 — Anla.** `reset --hard` dalı geri taşır ve çalışma dizinini sıfırlar. Commit'e artık hiçbir dal ya da etiket işaret etmez; nesne depoda durur ama erişilemez (dangling). Reflog HEAD'in her hareketini tuttuğu için kurtarma anahtarı oradadır.

**Adım 2 — Örnekle.** Depo: `a ilk` (f815980), `a ikinci` (8834243), `deneysel is` (b85ff72, `b.txt` = `onemli is`). Sonra `reset --hard HEAD~1` yapıldı ve `git log` artık yalnızca iki commit gösteriyor.

**Adım 3 — Kaba çöz.** Her commit'i aramak yerine tüm erişilemez nesneleri listeleyebilirsin: `git fsck --no-reflogs`. Bu, kaybolan commit'i dangling olarak verir. Ama hangisinin "son işim" olduğunu anlamak için tarihçeye ihtiyacın var; bunu reflog verir.

**Adım 4 — Örüntü.** `HEAD@{1}` ifadesi "HEAD'in bir önceki hareketinden önceki hali"dir. Reset'ten hemen önce HEAD `deneysel is` idi; reflog'da bu `HEAD@{1}` olarak duruyor. Kurtarma, bu girdinin hash'ine bir referans vermektir.

**Adım 5 — İyileştir.** Doğrudan `reset --hard HEAD@{1}` yapmak yerine önce bir dal aç: `git branch kurtarma b85ff72`. Böylece commit artık bir dal tarafından korunur ve kurtarma geri alınabilir bir işlem olur; sonra istersen dalı ana dala birleştirirsin.

**Adım 6 — Doğrula.** Her adımda HEAD'in durumunu izle:

| Adım | Komut | HEAD | Log'daki commit'ler | `b.txt` |
|---|---|---|---|---|
| 0 | (başlangıç) | b85ff72 | b85ff72, 8834243, f815980 | `onemli is` |
| 1 | `reset --hard HEAD~1` | 8834243 | 8834243, f815980 | yok |
| 2 | `reset --hard HEAD@{1}` | b85ff72 | b85ff72, 8834243, f815980 | `onemli is` |

Kurtarma sonrası `git log` ve `cat b.txt` başlangıçla aynı; yani commit ve içeriği tamamen geri geldi.

**Bunu AI'sız yazabilir misin?** Aynı durumda `reset --hard` yerine `git checkout -- b.txt` çalıştırsaydın ne olurdu? Hangi değişiklikler kurtarılabilir, hangileri değil? Reflog hangi işlemleri kaydeder, hangilerini kaydetmez?

### Örnek 3 (★★): Üç yollu birleştirme çakışmasını ortak ata üzerinden çöz

**Problem:** `ozellik-c` ile `main` dosyanın üçüncü satırını farklı değiştirdi. Çakışmayı, üç sürümü de göz önünde tutarak çöz; sonuç hem iki tarafın niyetini taşısın hem de tarihçede iki ebeveynli bir birleşme commit'i kalsın.

**Adım 1 — Anla.** Git hangi sürümün doğru olduğunu bilemediği için durdu. Üç sürüm mevcut: ortak ata (taban, aşama 1), senin tarafın (`ours`, aşama 2) ve birleştirdiğin tarafın (`theirs`, aşama 3). Bir çakışmayı çözmek için yalnızca iki tarafa bakmak yetmez; tabanın ne olduğunu da bilmek gerekir.

**Adım 2 — Örnekle.** Taban: `3 orta`. `main`: `3 MAIN-versiyon`. `ozellik-c`: `3 C-versiyon`. Dört satırlık dosya, sadece üçüncü satır çakışıyor.

**Adım 3 — Kaba çöz.** En hızlı çözüm `git checkout --ours m.txt` ile senin sürümünü almaktır. Bu bir çözümdür ama `theirs`'in niyetini tamamen siler; her zaman doğru değildir.

**Adım 4 — Örüntü.** Taban iki tarafın da değiştirdiği satırdır. Bu, iki tarafın ortak bir sorunu farklı yollarla çözmeye çalıştığını gösterir. Doğru çözüm genelde iki değişikliğin ortak amacını taşıyan üçüncü bir satırdır.

**Adım 5 — İyileştir.** Dosyayı elle düzelt: üçüncü satırı iki tarafı birleştiren tek bir metinle değiştir, çakışma işaretlerini sil, sonra `add` ve `commit` yap. Merge commit'i git tarafından otomatik oluşturulur ve iki ebeveyni taşır.

**Adım 6 — Doğrula.** Her aşamayı tablo ile izle:

| Ölçüt | Taban (aşama 1) | Ours (aşama 2) | Theirs (aşama 3) | Sonuç |
|---|---|---|---|---|
| 3. satır | `3 orta` | `3 MAIN-versiyon` | `3 C-versiyon` | `3 ortak-cozum: ...` |
| Ebeveyn sayısı | — | — | — | 2 (1fd5217, a078a8e) |

Çözüm sonrası `git log --graph` şu iki kolu gösterir: `main` (`1fd5217`) ve `ozellik-c` (`a078a8e`), birleşme commit'i `d18e991` altında. `git cat-file -p HEAD` ile iki `parent` satırını görürsün.

**Bunu AI'sız yazabilir misin?** Taban `3 orta` yerine `3 MAIN-versiyon` olsaydı ve `theirs` `3 orta`'yı hiç değiştirmemiş olsaydı, bu durumda git çakışma bildirir miydi? İpucu: değişiklik yalnızca bir tarafta ise ne olur? Üç yollu birleştirmenin mantığını taban üzerinden kur.

### Örnek 4 (★★★): git bisect run ile 128 commit'lik bir regresyonu bul

**Problem:** 128 commit'lik bir depoda bir ayar değeri bir commit'te `100`'den `99`'a değişiyor ve sonraki commit'lerde kalıyor. Hangi commit'in regresyonu soktuğunu, yalnızca bir test betiğiyle, en az sayıda testle bul.

**Adım 1 — Anla.** Bu bir regresyon: "iyi" durumdan "kötü" duruma geçişin tek bir noktası var ve sonrası kötü. Bu tür bir geçişi ikili aramayla bulabiliriz (Bölüm 14); toplam test sayısı yaklaşık log₂(128) = 7 olmalı.

**Adım 2 — Örnekle.** `HEAD` kötü, `HEAD~127` (ilk commit) iyi. Test betiği `limit.txt` içinde `limit=100` var mı diye bakıyor: varsa iyi (0), yoksa kötü (1). Gerçek suçlu, `is 91` commit'i.

**Adım 3 — Kaba çöz.** Her commit'i tek tek test etmek en fazla 127 test demektir. Bu, doğru ama yavaştır; ikili arama yüksek kazanç sağlar.

**Adım 4 — Örüntü.** Her testte aday aralığı yarılanır: iyi bir commit, sorunun sonrasındaki yarıyı; kötü bir commit, öncekinin yarısını eler. Bunun doğru çalışması için geçiş tek olmalıdır: bir kez kötüleşen sonra iyileşmeyen değer.

**Adım 5 — İyileştir.** Testi tek satırlık bir betiğe bağla ve `git bisect run sh test.sh` çalıştır. Git, her adımda ortadaki commit'i kendi seçer, testi çalıştırır, sonucu kaydeder. Derlenmeyen bir commit için betik 125 dönmeli ki git onu atlasın.

**Adım 6 — Doğrula.** Gerçek `git bisect log` çıktısıyla izlenen commit'ler ve sonuçlar:

| Adım | Test edilen commit | Sonuç | Kalan aday (yaklaşık) |
|---|---|---|---|
| 1 | `is 64` | iyi | 63 |
| 2 | `is 96` | kötü | 31 |
| 3 | `is 80` | iyi | 15 |
| 4 | `is 88` | iyi | 7 |
| 5 | `is 92` | kötü | 3 |
| 6 | `is 90` | iyi | 1 |
| 7 | `is 91` | kötü | 0: suçlu `e1c22f2` |

Yedi test; `git bisect log` aynı sırayı verir. Kalan aday sayısı, Şekil 38.10'daki ilerlemeyle birebir uyuşur.

**Bunu AI'sız yazabilir misin?** 128 commit'te test ortası bir commit'te derlenmiyor olsaydı (her derlenmeyen commit için 125) ne değişirdi? Bir adımda yanlışlıkla "iyi" işaretlersen sonuç hangi yöne kayar? Bunu bir örnekle göster.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçları **yasak**. Amaç hazır bir git klonu ya da hook paketi üretmek değil, nesne modelini, indeksi ve kancaları kendi elinle kurmak. Önce kâğıda çiz, küçük testler yaz, takıldığında Bölüm 38'in ilgili bölümünü tekrar oku. Çözümü dışarıdan alma.
:::

### Proje 1 (★★★): Mini git: init, hash-object, cat-file, add, commit, log

**Amaç:** Python ile gerçek git'in okuyabildiği bir nesne deposu yazmak. Yazdığın depoda oluşturulan blob ve commit'ler, aynı içerikle `git cat-file` tarafından okunabilmeli ve doğrulanabilmeli.

**Beklenen davranış:** `mini.py init` bir `.mini/objects` (ya da `.git/objects` biçimi) hazırlar. `hash-object dosya` nesnenin adını yazdırır; `-w` ile diske yazar. `cat-file -t/-p ad` türünü ve içeriği gösterir. `add dosya` basit bir indeks dosyasına yazar. `commit -m mesaj` indeksten bir tree kurar, commit nesnesi yazar ve dalı günceller. `log` geçmişi gösterir.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Nesne yazma için `zlib.compress` ve `hashlib.sha1` yeterli. Başlığı `tür boyut\0` olarak kur. Tree girdilerini ada göre sırala ve ham 20 baytı kullan. Yapılandırma dosyalarında `HEAD`'in `ref:` biçimini kopyala. Testlerin sonucunu gerçek git ile karşılaştır: `git -C dizin cat-file -p <hash>` çıktısı senin yazdıklarınla aynı olmalı.

**Başarı kriterleri:**
- Aynı içerik için `hash-object` çıktısı `git hash-object` ile birebir aynı.
- `commit` ile üretilen bir nesne, gerçek `git cat-file -p` ile okunabiliyor ve `git fsck` hata vermiyor.
- İki commit ile `log` çıktısı, gerçek git'in `log --oneline` çıktısıyla aynı hash sırasını veriyor.
- Tarihleri sabitlediğinde aynı komutlar her çalıştırmada aynı hash'leri üretiyor.

### Proje 2 (★★): Pre-commit paketi: biçim, büyük dosya, sır deseni, commit-msg

**Amaç:** Bölüm 38.9 ve 38.10'daki denetleyiciyi kendi kurallarınla genişletmek ve her kuralı bir test senaryosuyla sınamak.

**Beklenen davranış:** Pre-commit yalnızca sahnelenmiş içeriğe bakar ve şunları reddeder: 80 karakteri aşan satır, bilinen sır desenleri, 1 MB'tan büyük dosyalar. Bir ek kural olarak kendi seçeceğin bir biçim denetimi ekle (ör. tab karakteri ya da sondaki boşluk). Commit-msg konvansiyonel biçimi ve ilk satırın uzunluğunu denetler. Kurulum `core.hooksPath` ile yapılır.

**Önerilen yaklaşım (ipucu):** Her kuralı bağımsız bir fonksiyon yap ve bir `denetle_dosya` içinde topla. Kuralları veri olarak tut (desen ve açıklama listesi). Test için geçici bir depo kur, bir senaryo çalıştır, çıkış kodunu ve çıktıyı beklenenle karşılaştır. Yanlış pozitifleri sınamak için kasıtlı olarak iyi bir dosya da ekle.

**Başarı kriterleri:**
- Dört sorunlu senaryo (uzun satır, sahte anahtar, büyük dosya, kötü mesaj) her biri reddediliyor ve çıkış kodu 1.
- Sahnelenmemiş bir kötü değişiklik commit'i engellemiyor (indeks ilkesi) ve bu durum belgelenmiş.
- Temiz bir commit, her iki kancadan da geçiyor.
- Kurallar tek bir yerden değiştirilebiliyor; yeni bir kural eklemek 10 satırdan kısa.

### Ek Alıştırmalar

Aşağıdaki problemlerin çözümü bu kitapta yok. Önce kâğıda, sonra editöre geç; yapay zekâ yasak. Zorluk etiketine göre sırala.

1. **★ — Aynı içerik, farklı ad.** Aynı içeriğe sahip iki dosyayı farklı adlarla commit ettin. Depoda kaç blob ve kaç tree girdisi var? Bu ayrım dosya sisteminde inode ile dizin girdisi arasındaki ayrıma nasıl benziyor (Bölüm 28.9)?
2. **★ — Boş dosyanın hash'i.** Boş bir dosyanın blob hash'i `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`. Bu değeri Python ile hesapla ve neden sabit olduğunu açıkla.
3. **★ — Ayrık HEAD'de kaybolma.** Ayrık HEAD'de iki commit yaptın, sonra bir dala geçtin. Bu commit'lere hangi komutla ulaşabilirsin? Reflog'un süresi bitince ne olur?
4. **★★ — Soft ve mixed farkı.** `reset --soft` ile `reset --mixed` sonrası HEAD aynı, ama indeks farklı. `git status --short` çıktısı iki durumda nasıl görünür? Önce tahmin et, sonra dene.
5. **★★ — Mülakat: hızlı ileri.** Hangi durumda birleştirme bir birleşme commit'i üretmez ve bu tarihçe için neden önemlidir?
6. **★★ — Çakışmanın kapsamı.** İki dal aynı dosyanın farklı satırlarını değiştirdi ve bir üçüncü dosyayı da ikisi aynı satırda değiştirdi. Git hangi dosyalarda çakışma bildirir? Üç yollu birleştirme bunu nasıl ayırır?
7. **★★ — Rebase sonrası eski commit.** Bir rebase yaptıktan sonra eski commit'lere hangi araçla ulaşırsın? Bu araç ne kadar süre bu commit'leri tutar?
8. **★★ — Mülakat: cherry-pick ya da merge.** Bir dalın tek bir commit'ini başka bir dala taşımak için cherry-pick mi merge mi kullanırsın? Her seçimin bedelini söyle.
9. **★★★ — Mülakat: Myers ve LCS.** Myers algoritması neden LCS'nin tablo tabanlı çözümünden hızlıdır? Hangi durumda bu hız avantajı kaybolur?
10. **★★★ — Delta derinliği.** Bir nesneyi okumak için 50 delta uygulamak gerekiyorsa, `pack.depth` değerini düşürmenin disk ve okuma maliyetindeki etkisi nedir?
11. **★★★ — Mülakat: sır sızıntısı.** Bir API anahtarını commit'ten sildim, artık güvende miyim? Doğru yanıtın adımlarını sırala.
12. **★★★ — Bisect ve gürültü.** Test rastgele olarak bazen geçiyor, bazen kalıyorsa bisect'in sonucu ne olur? Bunu önlemek için hangi değişiklikleri yapardın?

## Kod Okuma Egzersizi

Bu bölümde git'in nesne başlığını nasıl üretip hash'e kattığını **gerçek** kaynaktan okuyacaksın. Kaynak: Git **2.43.0** sürümü, `object-file.c` dosyası. Dosya, `git/git` deposunun `v2.43.0` etiketinden (raw.githubusercontent.com üzerinden) indirildi ve birebir alındı. **Sadeleştirme:** iki ayrı parça alındı (1074–1089. satırlar ve 1791–1803. satırlar); aralarındaki kod atlandı. Tab karakterleri 4 boşluğa çevrildi. 70 karakteri aşan dört satır, token'lar değişmeden yeniden sarıldı (`BUG(...)` çağrısı iki string literal'e bölündü; C'de bitişik string literal'ler birleşir, anlam aynıdır).

```c
static int format_object_header_literally(char *str, size_t size,
                      const char *type, size_t objsize)
{
    return xsnprintf(str, size, "%s %"PRIuMAX, type,
                     (uintmax_t)objsize) + 1;
}

int format_object_header(char *str, size_t size,
                         enum object_type type, size_t objsize)
{
    const char *name = type_name(type);

    if (!name)
        BUG("could not get a type name for "
            "'enum object_type' value %d", type);

    return format_object_header_literally(str, size, name, objsize);
}

static void write_object_file_prepare(
                      const struct git_hash_algo *algo,
                      const void *buf, unsigned long len,
                      enum object_type type, struct object_id *oid,
                      char *hdr, int *hdrlen)
{
    git_hash_ctx c;

    /* Generate the header */
    *hdrlen = format_object_header(hdr, *hdrlen, type, len);

    /* Sha1.. */
    hash_object_body(algo, &c, buf, len, oid, hdr, hdrlen);
}
```

**Sorular — cevaplamadan geçme:**

1. `format_object_header_literally` döndürdüğü değere neden `+ 1` ekliyor? `xsnprintf`'in döndürdüğü uzunluk NUL bayt dahil midir? Başlık "blob 8" için kaç bayt tutar ve Bölüm 38.1'deki Python betiğindeki `\0` karakteriyle nasıl eşleşir?
2. `format_object_header` ile `format_object_header_literally` arasındaki fark nedir? Tür adı ne zaman `type_name` ile alınır ve `BUG` makrosu hangi durumda tetiklenir?
3. `write_object_file_prepare` başlığı ve gövdeyi hangi sırayla hash'e katar? Bölüm 38.1'deki `nesne_hash` fonksiyonunun sırasıyla karşılaştır.
4. `hash_object_body` çağrısına `hdr` ve `hdrlen` geçiliyor. Başlık neden gövdeden önce hash'e katılmak zorunda? Başlık olmasaydı bir blob ile bir tree'nin aynı gövde baytlarını taşıması hangi sorunu yaratırdı?
5. Kaynakta `format_object_header`, `type_name(type)` ile tür adını alıyor. Bu adın `blob`, `tree`, `commit` metinleriyle eşleşmesi, `cat-file -t` çıktısının neden aynı metinlerden oluştuğunu açıklar mı? Açıkla.
6. Bu koddan yola çıkarak, bir nesne türünün adını değiştirmenin (ör. `blob` yerine başka bir ad) mevcut depolardaki nesne adlarını değiştirip değiştirmeyeceğini tartış.

## Bölüm Özeti

- Git bir içerik adresli nesne deposudur: blob (dosya içeriği), tree (dizin), commit (anlık görüntü ve ebeveynler) ve tag (ad verilmiş nesne). Nesnenin adı `tür boyut\0` başlığıyla SHA-1 özetidir; Python ile birebir hesaplanır.
- Dallar, HEAD ve etiketler, nesnelere işaret eden küçük referans dosyalarıdır. Reflog HEAD'in geçmişini tutar; kaybolan commit'ler reflog ile kurtarılır.
- Üç ağaç (HEAD, indeks, çalışma dizini) her komutun hareketini açıklar. `reset --soft/--mixed/--hard` farkı bu üç katmanın hangisinin değiştiğidir.
- Hızlı ileri birleştirme yeni commit üretmez; üç yollu birleştirme ortak atayı kullanır ve çakışmada üç aşamalı indeks sunar. Çakışmayı çözmek için taban, ours ve theirs'i birlikte okumak gerekir.
- Rebase commit'leri yeniden oynatır ve yeni hash'ler üretir; paylaşılmış dalda yapılmaz. Cherry-pick bir değişikliği kopyalar; revert ters bir commit ekleyerek denetim izini korur.
- Diff, Myers algoritmasıyla en kısa düzenleme betiğini bulur (LCS ile ilişkili); patience ve histogram farklı hizalamalar üretebilir.
- Paketler gevşek nesneleri delta zincirleriyle sıkıştırır; `pack.depth` (varsayılan 50) okuma maliyetini sınırlar.
- Uzak depolarda push, hızlı ileri olmayan güncellemeyi reddeder; pull fetch ile merge'dür. Pull request, gözden geçirmeyi zorunlu bir kapıya dönüştürür.
- Hook'lar yerel hızlı geri bildirim sağlar; `core.hooksPath` ile sürüm kontrolüne alınır. Gerçek güvenlik sunucuda, korumalı dal ve CI kurallarıyla sağlanır.
- Sızan bir sır tarihçede kalır: önce anahtarı iptal et, sonra gerekirse tarihçeyi yeniden yaz. `bisect run` ile regresyon, 128 commit için 7 testte bulunur.

**Sonraki bölümde:** Bölüm 39 — Test Yazma. Bu bölümde commit'lerin neyi doğruladığını kanıtlamak için hook'larla yerel kapılar kurduk; bir sonraki bölümde o kapıdan geçecek testlerin nasıl yazılacağını, kapsama ölçümünü ve TDD döngüsünü göreceksin.

::: mulakat
1. Bir dosyayı değiştirmeden yalnızca adını değiştirip commit ettin. Git'in nesne deposunda hangi nesneler yeni hash alır, hangileri almaz? Nedenini açıkla.
2. `git reset --hard` ile bir commit'i kaybettin. Onu geri getirmenin yolu nedir ve bu kurtarmanın sınırı nedir?
3. İki dal aynı dosyanın farklı bölgelerini değiştirdi. Birleştirme neden çakışmaz? Üç yollu birleştirme bunu hangi bilgiyle anlar?
4. Ekip arkadaşın "main'i rebase edelim, geçmiş temiz olsun" diyor. Ne dersin ve neden?
5. Myers ile patience diff neden farklı sonuç verir? Hangisini ne zaman seçersin?
6. Bir regresyonu 1024 commit'lik bir aralıkta bulmak için en fazla kaç test gerekir? Bu sayıyı verirken hangi varsayımları yaptın?
7. Pre-commit hook'u koydun, ama ekip arkadaşın `--no-verify` ile atlıyor. Güvenliği nasıl sağlarsın?
:::
