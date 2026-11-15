%% kisim_no: X
%% kisim_ad: Yazılım Mühendisliği Pratiği
%% bolum_no: 42
%% baslik: Docker & Deployment

## Giriş: "Bende çalışıyor" bir mühendislik sonucu değildir

Bölüm 6'da "bende çalışıyor" cümlesinin neden yanıltıcı olduğunu anlattık. Her ortam, kodun dışında kalan bir dizi varsayımla birlikte gelir: kullandığın kütüphanenin sürümü, ortam değişkenleri, işletim sistemi, dosya sisteminin satır sonu ve büyük-küçük harf kuralları, hatta çekirdeğin sürümü. Bu varsayımlardan biri değiştiğinde aynı kod farklı davranır ve kimse neyin değiştiğini hemen söyleyemez.

Dağıtım (deployment), bu sorunun üretim ortamındaki hâlidir. Yazdığın servisin kendi bilgisayarında çalışması yetmez; onu bir sunucuda ya da bir yer istasyonunda, sen orada değilken, kontrollü biçimde açabilmelisin. Bu bölümde ortamı koda gömmenin araçlarını göreceğiz: konteynerler, imajlar, Dockerfile, Compose, sürekli entegrasyon ve dağıtım stratejileri. Ama konteynerin içinde hangi Linux mekanizmalarının çalıştığını görmeden Docker'ı ezberlemek yüzeysel kalır. Bu yüzden önce o mekanizmaları kendi elimizle çalıştıracağız.

Mülakatlarda "Docker nedir?" sorusu bir kelime sorusu gibi gelir, ama asıl soru çoğu zaman şudur: konteyner bir sanal makineden neden hafiftir ve bir konteyner neyi paylaşır, neyi paylaşmaz? Savunma sanayiinde aynı soru izlenebilirliğe dönüşür: bir yazılımın hangi kaynaktan, hangi araç zinciriyle ve hangi bağımlılıklarla üretildiğini gösterebilmek gerekir. Bu bölümdeki her ara adım, yani imaj özeti, sürüm etiketi ve tekrarlanabilir arşiv, bu izlenebilirliğin parçasıdır.

Bölüm 26'da gördüğün `clone()` çağrısı ve Bölüm 25'teki sanal bellek bu bölümde yeniden karşımıza çıkacak. Konteyner, aslında yeni bir süreç yaratan ve o sürecin çevresine görünürlük sınırları çizen bir çekirdek özelliğinden başka bir şey değildir.

::: not
Deneyleri Windows 11 üzerinde, WSL2 içindeki Ubuntu 24.04'te yaptık (çekirdek: 6.6.87.2-microsoft-standard-WSL2). Docker Desktop bu makinede kuruluydu, ama Linux motoru oturum boyunca açılmadı; yaklaşık 110 saniye beklemeye rağmen Docker'ın named pipe'ı oluşmadı. Bu yüzden bu bölümde `docker build` ve `docker run` çıktısı yoktur. Konteyner mekanizmalarını Linux'un altında ölçtük; Dockerfile, compose ve CI dosyalarını yazıp `docker compose config`, `ci.sh` ve Python betikleriyle doğruladık. Çalıştırılmayan her şeyi metinde açıkça belirttik.
:::

## 42.1 Bende çalışıyor: ortam da bir bağımlılıktır

Bir programın çalışması üç şeye bağlıdır: kodun kendisine, kodun kullandığı kütüphanelere ve çalıştığı ortama. Üçüncüsü en çok unutulandır. Ortam; işletim sistemini, çekirdek sürümünü, kurulu araç zincirini, ortam değişkenlerini, saat dilimini, dosya sisteminin davranışını ve hatta hangi kullanıcıyla çalıştığını kapsar. Kodda bir `import` satırı görürsün, ama bir `$PATH` farkını görmezsin.

Bu bölümü yazarken tam bu sorunun küçük bir örneğini yaşadık. Katman özetleri modelimiz (Bölüm 42.6'da göreceğiz) aynı dosyaları Windows'ta ve WSL'de hash'lediğinde iki farklı değer üretti. Kodda bir hata yoktu, ama iki ortamda iki ayrı davranış vardı. Sebep iki katmandaydı. Birincisi, `pathlib` ile dizin ağacını dolaşırken dosyaları sıralıyorduk; Windows yol sıralaması büyük-küçük harfe duyarsız, Linux ise duyarlı. Aynı dosyalar farklı sırayla hash'lenince özet değişti. İkincisi, metni `write_text` ile yazmak Windows'ta satır sonunu `\r\n` yapıyordu; Linux'ta `\n` kalıyordu. Düzeltme, sıralamayı açık bir anahtarla yapmak ve dosyaları bayt olarak yazmaktı. Bunu 42.6'daki kodda göreceksin.

Bu olayın dersi, tekrarlanabilirliğin üç ayağıdır. Birincisi ortamı tanımlamak: Dockerfile gibi bir dosya "bu ortam şudur" der. İkincisi girdileri sabitlemek: sürümleri, bağımlılıkları ve arşivin baytlarını. Üçüncüsü çıktıyı içerik adresiyle işaretlemek: bir özet, "bu bayt dizisi budur" der. Bölümün geri kalanı bu üç ayağın konteyner dünyasındaki karşılıklarını inceliyor.

## 42.2 Sanal makine mi, konteyner mi: çekirdeği kim taşır?

Sanal makine (VM), bir hipervizörün üzerinde tam bir bilgisayar taklidi çalıştırır. Her VM kendi işletim sistemi çekirdeğini (misafir çekirdeği) taşır, kendi sanal donanımını görür ve diğer VM'lerden donanım düzeyinde ayrılır. Bu güçlü bir yalıtımdır: bir VM'in çekirdeğinde açık olan bir hata, ana makineyi doğrudan etkilemez (her yalıtım gibi, hipervizördeki hatalar hariç).

Konteyner ise farklı bir sözleşme sunar. Konteyner, ana makinenin çekirdeğini paylaşan bir süreçtir. Ona kendi dosya ağacı, kendi süreç listesi ve kendi ağı görünür, ama çekirdek tektir. Bu yüzden konteyner hafiftir: ayrı bir çekirdek açılmaz, ayrı bir donanım taklit edilmez. Bedeli de vardır: konteyner, ana makinenin çekirdeğine bağlıdır. Linux çekirdeği için yazılmış bir imaj, Windows çekirdeğinde doğrudan çalışmaz.

Şekil 42.1, iki yaklaşımın katmanlarını yan yana gösteriyor. Sol sütunda her uygulamanın altında kendi çekirdeği var; sağ sütunda uygulamalar aynı çekirdeği paylaşıyor.

![Şekil 42.1: Sanal makinede her VM kendi çekirdeğini taşır; konteynerde uygulamalar ana makinenin çekirdeğini paylaşır, yalnızca kütüphane katmanları ayrıdır.](gorseller/b42_vm_konteyner.png)

Karşılaştırmayı tek tabloda toparlayalım. Burada yalnızca yapısal farkları yazıyoruz; açılış süresi ve bellek tüketimi gibi sayısal değerleri bu bölümde ölçmedik ve bu yüzden vermiyoruz.

| Özellik | Sanal makine | Konteyner |
|---|---|---|
| Çekirdek | Her VM kendi çekirdeğini taşır | Ana makinenin çekirdeği paylaşılır |
| Yalıtım | Donanım taklidi, güçlü | Çekirdek paylaşımı, süreç düzeyi |
| İşletim sistemi uyumu | Misafir çekirdeği farklı olabilir | Konteyner çekirdeği ile aynı olmalı |
| Taşıdığı şey | Tam bir sistem | Uygulama ve bağımlılıkları |

Bu makinede WSL2'nin çekirdeği, Windows'un içinde hafif bir Linux sanal makinesidir. Docker Desktop, Windows'ta Linux konteynerlerini bu tür bir Linux sanal makinesinin içinde çalıştırır (genel bilgi). Yani bu bölümde gördüğümüz Linux mekanizmaları, Windows'ta bile bir Linux çekirdeğinin içinde çalışır. Çekirdek sürümünü kontrol edelim:

```term
$ uname -r
6.6.87.2-microsoft-standard-WSL2
```

::: baglanti
Çekirdeğin süreç ve bellek soyutlamalarını Bölüm 26 ve Bölüm 25'te gördük. Bu bölümde aynı soyutlamaların nasıl dilimlenip süreçlere dağıtıldığını göreceğiz.
:::

## 42.3 Linux ad alanları: konteynerin "gördükleri"

Ad alanı (namespace), bir sürecin belirli bir sistem kaynağını nasıl gördüğünü değiştiren çekirdek özelliğidir. Aynı çekirdekte iki süreç farklı bir hostname, farklı bir süreç listesi ya da farklı bir ağ arayüzü görebilir. Konteynerin "yalıtımı" büyük ölçüde budur: ayrı bir görünüm kümesi.

Ad alanları, `clone()` sistem çağrısının bayraklarıyla oluşturulur. Bölüm 26'da `CLONE_THREAD` ve `CLONE_VM` gibi bayrakların neyin paylaşılacağını belirlediğini gördük. Ad alanı bayrakları ise tersini yapar: hangi kaynağın paylaşılmayacağını söyler. Çekirdek sürümü 6.6'da bu bayrakların adları ve değerleri `include/uapi/linux/sched.h` dosyasında tanımlıdır. Ad alanları ve bayrakları şöyledir:

| Ad alanı | Bayrak | İzole edilen görünüm |
|---|---|---|
| mount | `CLONE_NEWNS` | bağlama noktaları, dosya ağacı |
| UTS | `CLONE_NEWUTS` | hostname ve domain adı |
| IPC | `CLONE_NEWIPC` | SysV IPC ve POSIX mesaj kuyrukları |
| PID | `CLONE_NEWPID` | süreç numaraları (içeride PID 1 olabilir) |
| ağ (network) | `CLONE_NEWNET` | ağ arayüzleri, yönlendirme, portlar |
| kullanıcı (user) | `CLONE_NEWUSER` | uid ve gid eşlemesi |
| cgroup | `CLONE_NEWCGROUP` | cgroup hiyerarşisinin görünümü |
| zaman (time) | `CLONE_NEWTIME` | önyükleme ve monotonik saat ofseti |

Bu bayrakları elle `clone()` ile kullanmak yerine `unshare(1)` komutuyla deneyebilirsin. `unshare`, mevcut süreci verilen ad alanlarına yerleştirip bir komut çalıştırır. Ad alanı bir süreç için oluşturulur ve süreç bitince ad alanı yok olur.

Önce kullanıcı ad alanını deneyelim, çünkü diğerlerinin hepsi onun izniyle açılabilir. `-r` bayrağı, dışarıdaki kullanıcıyı içeride root olarak eşler:

```term
$ id -u
1000
$ unshare -r sh -c 'echo "uid içeride: $(id -u)"'
uid içeride: 0
```

Dışarıda uid 1000 olan kullanıcı, içeride uid 0 görünür; ama bu bir eşlemedir, gerçek bir root yetkisi değildir. Ana makinenin dosyalarına hâlâ 1000 olarak erişirsin. Konteyner motorlarının çoğu bunu ve mount işlemlerini root olarak yapar; rootless kurulumlar ise bu kullanıcı ad alanı mekanizmasına dayanır (genel bilgi).

Şimdi PID ad alanını deneyelim. Yeni PID ad alanında ilk süreç PID 1 olur. `--mount-proc` bayrağı, `/proc`'u yeni ad alanına göre yeniden bağlar; böylece `ps` doğru listeyi gösterir:

```term
$ readlink /proc/$$/ns/pid
pid:[4026532223]
$ unshare -r -p -f --mount-proc sh -c 'readlink /proc/$$/ns/pid; \
    echo "PID: $$"; ps -e -o pid,comm'
pid:[4026532230]
PID: 1
    PID COMMAND
      1 sh
      3 ps
```

İki satırda iki ayrı ad alanı kimliği görüyorsun: `pid:[...]` sayısı ad alanının çekirdekteki kimliğidir. Dışarıdaki kabuk ile içerideki `sh` farklı kimliklere sahip. İçeride `sh` PID 1'dir: konteynerin "init" süreci budur ve bu rol, bu bölümün ilerleyen kısmında çok önemli bir sorumluluk getirecek.

UTS ad alanı ise yalnızca hostname'i ayırır. Ana makinenin adı değişmez, içerideki değişir:

```term
$ unshare -r -u sh -c 'hostname konteyner; echo "içeride: $(hostname)"'
içeride: konteyner
$ echo "dışarıda: $(hostname)"
dışarıda: Mert
```

Şekil 42.2, bir sürecin etrafındaki ad alanlarını ve cgroup'u birlikte gösteriyor. Ad alanları "ne görür" sorusunu, cgroup ise "ne kadar kullanır" sorusunu yanıtlar.

![Şekil 42.2: Bir süreç, PID, mount, ağ, UTS ve IPC ad alanlarıyla çevrilidir; kullanıcı ad alanı eşlemeyi yapar; cgroup ise kaynak sınırlarını uygular.](gorseller/b42_ad_alanlari.png)

Kaynak kodda bu bayrakların değerlerini görmek istersen, Linux v6.6 `include/uapi/linux/sched.h` dosyasındaki kesit Kod Okuma bölümünde. Orada bayrakların tek bitlik değerler olduğunu, bu yüzden birden çok ad alanının tek bir `clone` çağrısında birleştirilebildiğini göreceksin.

::: ipucu
`unshare` denemesi yaparken ana makineyi etkilemek istemiyorsan, her zaman ad alanı bayrağıyla birlikte `-r` (kullanıcı ad alanı) kullan. Bu sayede ana makinede gerçek bir root yetkisi gerekmez ve yanlışlıkla sistem dosyalarına dokunma riski azalır.
:::

### cgroup'lar: "ne kadar kullanabilir?"

Ad alanı bir sürece neyi gösterdiğini belirler, ama o sürecin ne kadar CPU, bellek ya da süreç numarası kullanabileceğini belirlemez. Bu iş **cgroup** (control group) mekanizmasının işidir. cgroup, süreçleri bir grup içinde toplar ve grubun kaynaklarını denetleyiciler (controller) aracılığıyla sınırlar.

Linux'ta bugün kullanılan model cgroup v2'dir. Tek bir hiyerarşisi vardır ve her denetleyici bir dosya arayüzüyle yönetilir. Bu makinede çekirdeğin kullanılabilir denetleyicileri cpu, memory, pids, io gibi olan bir kümeden oluşuyor. Konteynerin kaynak sınırları, kabaca şu dosyalara yazılan değerlerdir:

- `memory.max`: grubun kullanabileceği en fazla bellek (bayt). `max` sınır olmadığı anlamına gelir.
- `cpu.max`: "kota periyot" biçiminde CPU sınırı. `max 100000` sınır olmadığı, periyodun 100 ms olduğu anlamına gelir.
- `pids.max`: grubun açabileceği en fazla süreç ve iş parçacığı sayısı. Bölüm 26'daki fork bombasının sınırlandırılmasının çekirdek karşılığı budur.

Kendi süreç grubumuzun dosyalarını okuyabiliriz:

```term
$ cat /proc/self/cgroup
0::/init.scope
$ cd /sys/fs/cgroup/init.scope && cat memory.max pids.max
max
18722
```

Yeni bir alt cgroup oluşturup sınır koymak istediğimizde ise izin yoktu:

```term
$ cd /sys/fs/cgroup/init.scope && mkdir deneme
mkdir: cannot create directory ‘deneme’: Permission denied
```

Bu sonuç, kullanıcı düzeyinde cgroup yazamadığımızı gösteriyor; cgroup hiyerarşisinin bu kullanıcıya devredilmediğini (delegasyon yapılmadığını) söylüyor. Yani bellek sınırını gerçekten uygulayıp bir sürecin ölüp ölmediğini bu makinede ölçemedik. Bunu metinde açıkça belirtmek zorundayız: **cgroup sınırlarını yalnızca okuduk, yazıp uygulayamadık.** Sınırların gerçek davranışını görmek için delegasyonlu bir Linux makineye ihtiyacın olacak.

Yazma yetkisi olsaydı, 256 MiB'lik bir bellek sınırı kabaca `memory.max` dosyasına `268435456` yazmak olurdu. Docker'ın `--memory 256m`, `--cpus 1` ve `--pids-limit 64` gibi bayrakları da arka planda bu tür dosyalara değer yazar (genel bilgi). Bir konteyner sınırını aştığında çekirdek, bellek için OOM öldürücüsünü devreye sokar; bu konuyu Bölüm 25'teki sanal bellek ve sayfa hatası bağlamında düşünebilirsin.

::: dikkat
cgroup sınırları ile ad alanları karıştırılmamalıdır. Konteynerin "sadece 512 MB" kullanması, bir ad alanı değil cgroup işidir. Bir ad alanı yalnızca neyin görüneceğini belirler; yani bellek sınırı koymak için PID ad alanı yeterli değildir.
:::

## 42.4 Birleşik dosya sistemi: overlayfs ve chroot

Konteynerin dosya sistemi, tek bir dizin ağacı gibi görünür, ama altında birden çok kaynak yatar. Dosyaların bir kısmı salt okunur bir imajdan gelir, bir kısmı konteynerin kendi yazdığı yeni bir katmandır. Bu birleşimi sağlayan Linux mekanizması **overlayfs**'tir. Bölüm 28'de dosya tanımlayıcılarının ve G/Ç yığınının katmanlarını gördük; overlayfs bu yığının yukarısında, dizin ağacının kendisini katmanlara böler.

Overlayfs dört dizinle çalışır. **lower** (alt) dizin salt okunur katmandır; **upper** (üst) dizin yazılabilir katmandır; **work** overlayfs'in iç işleri için gereken geçici bir alandır; **merged** (birleşik) dizin ise süreçlerin gördüğü son görünümdür. Kurallar basittir. Okuma, üst katmanda varsa oradan, yoksa alt katmandan yapılır. Alt katmandaki bir dosyaya yazılmak istendiğinde dosya önce üst katmana kopyalanır (**copy-up**) ve yazma orada yapılır. Alt katman hiç değişmez. Bu, Bölüm 26'daki kopyala-yazarken-kopyala (COW) fikrinin dosya düzeyindeki karşılığıdır.

Silme işlemi için overlayfs bir **whiteout** (beyaz liste) işareti kullanır. Alt katmandaki bir dosyayı sildiğinde o dosya alt katmanda hâlâ durur; üst katmana, o yolun silindiğini söyleyen özel bir kayıt yazılır. Bu kayıt karakter aygıtı biçiminde görünür ve 0/0 numarasına sahiptir. Şekil 42.3, dört dizinin birbirine nasıl bağlandığını gösteriyor.

![Şekil 42.3: Overlayfs birleşik görünümü, üst yazılabilir katmandan ve salt okunur alt katmandan oluşturur. Silinen dosya, üst katmanda 0/0 aygıtı olarak işaretlenir.](gorseller/b42_overlay.png)

Bu yapıyı kendi makinemizde kurup denedik. Kullanıcı ad alanı içinde overlayfs bağlamak için root yetkisi gerekmedi. Önce alt katmanı hazırladık, sonra bağladık ve birleşik görünümde bir dosya yazıp bir dosya sildik:

```term
$ B=/tmp/b42ov; mkdir -p $B/lower $B/upper $B/work $B/merged
$ echo "altta bir dosya" > $B/lower/alt.txt
$ unshare -r -m sh -c "mount -t overlay overlay \
    -o lowerdir=$B/lower,upperdir=$B/upper,workdir=$B/work \
    $B/merged; find $B/merged -type f | sort"
/tmp/b42ov/merged/alt.txt
/tmp/b42ov/merged/etc/ayar.conf
```

Şimdi aynı bağlamanın içinde bir değişiklik ve bir silme yapalım, sonra üst katmanın ne tuttuğuna bakalım. Komutlar bağlama içinde çalıştığı için sonuçlar yalnızca ilgili ad alanında görünür; alt katman ise ana makinede her zaman aynı kalır:

```term
$ unshare -r -m sh -c "echo yeni > $B/merged/yeni.txt; \
    echo degisti > $B/merged/etc/ayar.conf; \
    rm $B/merged/alt.txt; find $B/upper | sort"
/tmp/b42ov/upper
/tmp/b42ov/upper/alt.txt
/tmp/b42ov/upper/etc
/tmp/b42ov/upper/etc/ayar.conf
/tmp/b42ov/upper/yeni.txt
$ ls -l $B/upper
c--------- 2 root root 0, 0 Oct 21 21:53 alt.txt
drwxr-xr-x 2 root root 4096 Oct 21 21:53 etc
-rw-r--r-- 1 root root   11 Oct 21 21:53 yeni.txt
$ cat $B/lower/etc/ayar.conf; ls $B/lower
alt-etc
alt.txt
etc
```

Üç şeyi gözle. Birincisi, üst katman yalnızca değişiklikleri tutar: `etc/ayar.conf` ve `yeni.txt`. İkincisi, silinen `alt.txt`, üst katmanda `c---------` izniyle, 0/0 numaralı bir karakter aygıtı olarak durur; bu whiteout kaydıdır. Üçüncüsü, alt katmandaki `ayar.conf` içeriği `alt-etc` olarak kaldı ve `alt.txt` hâlâ `lower` dizininde duruyor. Yani konteynerde yapılan her değişiklik üst katmanda birikir, imaj ise değişmez.

Bu son gözlemin pratik sonucu büyüktür. Bir Dockerfile'da bir dosyayı bir talimatta oluşturup sonraki talimatta silersen, dosya o katmanda hâlâ durur; imajın boyutu küçülmez. Silme yalnızca üst katmana bir whiteout yazar. Bunu 42.6'da bir uyarı olarak tekrar göreceğiz.

### chroot ile kök dizin değiştirmek

Overlayfs, konteynerin dosya ağacını hazırlar; ama süreç hangi kökü "/" olarak göreceğini ayrıca bilmelidir. Bunun en eski yolu `chroot(2)` çağrısıdır: sürecin kök dizinini başka bir dizine taşır. Konteynerler de bu fikri kullanır, ama gerçek uygulamada genellikle `pivot_root` tercih edilir çünkü eski kök dizinin tamamen ayrılmasını sağlar (genel bilgi).

Kavramı görmek için yalnızca `/bin/sh` ve bağımlı olduğu kütüphanelerden oluşan minik bir kök dizin hazırlayıp `chroot` ile içine girdik. Kök dizin bu kadar küçük olduğunda, süreç ana makinenin `/home` dizinini göremez:

```term
$ unshare -r -m chroot $R /bin/sh -c 'echo "konum: $PWD"; \
    for f in /*; do echo "  $f"; done; \
    printf "123456789" | /bin/crc'
konum: /
  /bin
  /lib
  /lib64
cbf43926
$ unshare -r -m chroot $R /bin/sh -c 'if [ -d /home ]; then echo var; \
    else echo yok; fi'
yok
```

`$R`, minik kök dizinin yoludur. Son satırdaki `cbf43926`, bu bölümün CRC aracının statik derlenmiş sürümünün (42.7'de göreceğiz) aynı kök dizinde çalıştığını gösteriyor. Kök dizin yalnızca gereken dosyaları içerdiğinde, uygulama o dosyalarla yetinmek zorundadır. Konteynerin dosya ağacı da böyle bir kök dizindir.

## 42.5 İmajlar: katmanlar, özetler ve tekrarlanabilirlik

Bir **imaj**, bir konteynerin başlangıç durumunun paketidir. İmaj üç parçadan oluşur: yapılandırma (hangi komutla başlayacağı, ortam değişkenleri, hangi kullanıcıyla çalışacağı), bir **manifest** (kullanılan katmanların sıralı listesi) ve katman arşivleri. Her katman, bir önceki katmana göre dosya sistemi farkını taşıyan bir tar arşividir. Konteyner başlarken bu katmanlar overlayfs'in alt katmanları olarak üst üste bindirilir; üstte konteynerin yazılabilir katmanı durur.

Şekil 42.4, bir imajın katmanlarını ve her katmanın özetini gösteriyor. Özet, arşivin baytlarının kriptografik özetidir: aynı baytlar aynı özeti üretir, bir bayt değişirse özet tamamen değişir.

![Şekil 42.4: İmaj, manifest ve katman arşivlerinden oluşur. Her katmanın kimliği, arşivin baytlarından hesaplanan sha256 özetidir.](gorseller/b42_imaj_katman.png)

Bu fikir Bölüm 38'de gördüğün git nesne deposuna çok benzer. Git, her nesnenin adını içeriğinden hesaplar. Bir fark var: Git nesne adlarında bugün SHA-1 kullanır (Bölüm 38), OCI imajlarında ise standart olarak SHA-256 kullanılır (genel bilgi). Her iki durumda da "adres içerikten gelir" ilkesi aynıdır ve bu sayede bir katmanın değiştiğini özet karşılaştırmasıyla anlarsın.

Tekrarlanabilirlik için kritik soru şudur: aynı dosyaları iki kez arşivlersen aynı özeti alır mısın? Cevap, arşivin **normalleştirilmesine** bağlıdır. Tar arşivi, dosyaların değiştirilme zamanını, sahibini ve sıralamasını da içerir. Bu bilgiler değişirse özet de değişir, içerik aynı olsa bile. Kendi makinemizde bunu iki farklı tar çağrısıyla ölçtük:

```term
$ tar --sort=name --mtime='@0' --owner=0 --group=0 \
    --numeric-owner -cf a1.tar .
$ sha256sum a1.tar | cut -c1-16
98d4e7d74e051acc
$ touch app/main.c   # yalnız zaman damgası değişir
$ tar --sort=name --mtime='@0' --owner=0 --group=0 \
    --numeric-owner -cf a2.tar .
$ sha256sum a2.tar | cut -c1-16
98d4e7d74e051acc
$ tar -cf b1.tar . ; touch app/main.c; tar -cf b2.tar .
$ sha256sum b1.tar b2.tar | cut -c1-16
1182577fd8191bd0
a806c795816940a2
```

Normalleştirilmiş arşivde (`--sort=name`, sabit `--mtime`, sayısal sahiplik) yalnızca zaman damgası değişince özet değişmedi. Normalleştirilmemiş arşivde aynı işlem iki farklı özet üretti. Bu fark, aynı kaynaktan aynı imajı yeniden üretmek istediğinde senin dışındaki bir değişkenin (ana makinenin saati, dosyayı kimin kaydettiği, dizin tarama sırası) sonucu değiştirebileceğini gösteriyor. Bu tür değişkenleri kaldırmaya **tekrarlanabilir derleme** (reproducible build) denir ve tedarik zinciri güvenliği için önemlidir; bunu 42.13'te tekrar ele alacağız.

Son olarak içeriğin değiştiğinde özetin de değiştiğini görmek için kaynak dosyanın bir baytını değiştirdik. Özet, normalleştirilmiş arşiv için yeni bir değer verdi (`5e98f7f84db6788b`); bu, özetin içeriği izlediğinin kanıtıdır.

::: dikkat
Tekrarlanabilirlik, yalnızca tar'a bağlı değildir. Aynı kaynağın iki kez farklı bir `RUN` komutuyla (örneğin `apt-get install` ile en güncel paketi çekerek) derlenmesi, iki farklı imaj üretebilir. Sürümleri sabitlemek (pinning) bu yüzden Dockerfile'ın bir parçasıdır.
:::

## 42.6 Dockerfile ve katman önbelleği

Dockerfile, bir imajın nasıl üretileceğini anlatan düz metin dosyasıdır. Her satır bir **talimat**tır ve çoğu talimat, bir katman üretir ya da mevcut yapılandırmayı değiştirir. Aşağıdaki tablo, bu bölümde kullanacağımız talimatları özetliyor.

| Talimat | Ne yapar | Dikkat edilecek nokta |
|---|---|---|
| `FROM` | Temel imajı seçer | Etiket yerine özet (digest) sabitlemek daha güvenlidir (genel bilgi) |
| `WORKDIR` | Sonraki talimatların çalışma dizini | Dizin yoksa oluşturulur |
| `COPY` | Bağlam dizininden dosya kopyalar | Dosya içeriği önbellek anahtarına girer |
| `RUN` | Derleme sırasında komut çalıştırır | Komut metni anahtara girer, ağ sonucu girmez |
| `ENV` | Ortam değişkeni tanımlar | Değer imaj yapılandırmasında kalır; sır koyma |
| `USER` | Sonraki süreçlerin kullanıcısı | Root olarak çalıştırmamak için kullanılır |
| `EXPOSE` | Hangi portun kullanıldığını belgeler | Port yayımlamaz; yalnızca belgeler |
| `HEALTHCHECK` | Konteynerin sağlık komutunu tanımlar | Çıkış kodu 0 sağlıklı, 1 sağlıksız demektir |
| `ENTRYPOINT` / `CMD` | Konteyner başladığında çalışacak komut | Exec biçimi (JSON dizisi) kullanılmalıdır |

Dockerfile'ın en önemli özelliği **önbelleğidir**. Docker bir talimatı her derlemede baştan çalıştırmaz; talimatın önceki bir derlemede ürettiği katman varsa onu yeniden kullanır. Bu, derlemeyi dakikalardan saniyelere indirir. Kural, bir talimatın önbellek anahtarının şu üç şeyden oluşmasıdır: talimatın metni, bir önceki katmanın anahtarı ve (`COPY` ise) kopyalanan dosyaların içeriği. Anahtarların üst üste bağlı olması, önemli bir sonuç doğurur: bir katman yeniden çalışınca, o katmanın altındaki bütün talimatlar da yeniden çalışır. Önbellek, yalnızca üstten başlayan bir önek gibi davranır.

Bu kuralı somutlaştırmak için bir modelimizi yazdık. Bu bir Docker kodu değildir; yalnızca anahtar zincirinin mantığını gösterir. Dosya özetinin nasıl hesaplandığına ve sıralama tuzağına dikkat et. Kod üç parça hâlinde verilmiştir.

```python
# -*- coding: utf-8 -*-
# katman_onbellek.py: Dockerfile önbellek anahtarının MODELİ.
# Gerçek Docker kodu değildir; kuralı gösterir:
#   anahtar_i = sha256(anahtar_(i-1) | talimat | COPY özeti)
# Bir anahtar üst katmana bağlı olduğundan, bir talimat
# yeniden çalışınca altındaki tüm talimatlar da çalışır.
import hashlib
import pathlib
import tempfile

A_DOCKERFILE = [
    "FROM gcc:13",
    "WORKDIR /src",
    "COPY . .",
    "RUN apt-get install -y make",
    "RUN make",
]
B_DOCKERFILE = [
    "FROM gcc:13",
    "WORKDIR /src",
    "COPY deps.txt .",
    "RUN apt-get install -y make",
    "COPY . .",
    "RUN make",
]
```

Dosya özeti, dizin ağacının dosyalarını sıralı olarak dolaşır ve her dosyanın göreli adını ile baytlarını karma fonksiyonuna verir. Burada sıralama bir ayrıntı değil, sonucu belirleyen bir karardır.

```python
def sha(metin):
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()[:10]

def dosya_ozeti(baglam, yol):
    """COPY için: dosya adlarından ve baytlarından özet."""
    kok = pathlib.Path(baglam) / yol
    # Sıralama açık anahtarla yapılır. Path sıralaması Windows'ta
    # büyük-küçük harf duyarsız, Linux'ta duyarlıdır; özet değişirdi.
    if kok.is_file():
        dosyalar = [kok]
    else:
        dosyalar = sorted(
            kok.rglob("*"),
            key=lambda f: f.relative_to(baglam).as_posix())
    h = hashlib.sha256()
    for f in dosyalar:
        if f.is_file():
            h.update(str(f.relative_to(baglam)).encode("utf-8"))
            h.update(f.read_bytes())
    return h.hexdigest()[:10]
```

Derleme fonksiyonu, her talimat için bir anahtar üretir ve bu anahtarın ortak önbellekte olup olmadığına bakar. Anahtarlar bir önceki anahtara bağlı olduğu için zincir ilk değişen talimattan sonra tamamen yeniden kurulur.

```python
def derle(talimatlar, baglam, onbellek):
    """Her talimat için anahtar üretir: önbellekte varsa CACHED,
    yoksa REBUILT. Anahtarlar ortak önbelleğe eklenir."""
    anahtar = "kok"
    satirlar = []
    for tal in talimatlar:
        kom = tal.split()[0]
        girdi = ""
        if kom == "COPY":
            girdi = dosya_ozeti(baglam, tal.split()[1])
        anahtar = sha(anahtar + "|" + tal + "|" + girdi)
        durum = "CACHED" if anahtar in onbellek else "REBUILT"
        onbellek.add(anahtar)
        satirlar.append((tal, durum, anahtar))
    return satirlar

def yaz_dosya(yol, metin):
    # write_text Windows'ta satır sonunu değiştirir. Baytları doğrudan
    # yazarak özetin her işletim sisteminde aynı kalmasını sağlarız.
    yol.write_bytes(metin.encode("utf-8"))
```

Kalan kısım çıktı biçimlendirme ve senaryo kurulumudur. Senaryoda `crc32_arac.c` dosyasının yalnızca içeriği değişiyor; diğer her şey aynı kalıyor.

```python
def yaz(baslik, satirlar):
    print(baslik)
    for tal, durum, anahtar in satirlar:
        print("  %-28s %-8s %s" % (tal, durum, anahtar))

def ana():
    with tempfile.TemporaryDirectory() as baglam:
        p = pathlib.Path(baglam)
        yaz_dosya(p / "deps.txt", "make\n")
        yaz_dosya(p / "Makefile", "all:\n\tgcc crc32_arac.c\n")
        yaz_dosya(p / "crc32_arac.c", "int main(void){return 0;}\n")
        onbellek = set()
        yaz("A ilk derleme:", derle(A_DOCKERFILE, baglam, onbellek))
        yaz("B ilk derleme:", derle(B_DOCKERFILE, baglam, onbellek))
        # Yalnızca kaynak kodu değişir
        yaz_dosya(p / "crc32_arac.c", "int main(void){return 1;}\n")
        a = derle(A_DOCKERFILE, baglam, onbellek)
        yaz("A kaynak değişti:", a)
        b = derle(B_DOCKERFILE, baglam, onbellek)
        yaz("B kaynak değişti:", b)

if __name__ == "__main__":
    ana()
```

Modeli çalıştırdığımızda şu çıktıyı aldık. A ve B aynı önbelleği paylaşıyor; bu yüzden B'nin ilk iki talimatı A'nın ilk derlemesinde ürettiği `FROM` ve `WORKDIR` katmanlarını yeniden kullandı. Her satırda talimat, durum ve (kısaltılmış) anahtar görünüyor:

```term
$ python katman_onbellek.py
A ilk derleme:
  FROM gcc:13                  REBUILT  8212247907
  WORKDIR /src                 REBUILT  331d86ee39
  COPY . .                     REBUILT  4b8c111351
  RUN apt-get install -y make  REBUILT  69d1253d30
  RUN make                     REBUILT  db6426386f
B ilk derleme:
  FROM gcc:13                  CACHED   8212247907
  WORKDIR /src                 CACHED   331d86ee39
  COPY deps.txt .              REBUILT  89af631ec2
  RUN apt-get install -y make  REBUILT  05982ff6eb
  COPY . .                     REBUILT  7d4eb49c60
  RUN make                     REBUILT  ed1ca41250
A kaynak değişti:
  FROM gcc:13                  CACHED   8212247907
  WORKDIR /src                 CACHED   331d86ee39
  COPY . .                     REBUILT  fed74c9e08
  RUN apt-get install -y make  REBUILT  3d78964603
  RUN make                     REBUILT  64c398d860
B kaynak değişti:
  FROM gcc:13                  CACHED   8212247907
  WORKDIR /src                 CACHED   331d86ee39
  COPY deps.txt .              CACHED   89af631ec2
  RUN apt-get install -y make  CACHED   05982ff6eb
  COPY . .                     REBUILT  e03c142262
  RUN make                     REBUILT  30880d193a
```

Şekil 42.5, aynı sonucu iki Dockerfile yan yana gösteriyor: A'da kaynak kodu önce kopyalandığı için `apt-get` katmanı da yeniden çalışıyor; B'de bağımlılık listesi önce kopyalandığı için o katman önbellekten geliyor.

![Şekil 42.5: Kaynak kod değişti. A'da kaynak kopyası bağımlılık katmanının önünde olduğu için kurulum da yeniden çalışır; B'de bağımlılık katmanı önbellekten gelir.](gorseller/b42_onbellek.png)

Bu sonucun pratik kuralı şudur: sık değişen şeyleri (kaynak kodu) en sona, seyrek değişen şeyleri (bağımlılık listesi) en öne koy. Dosyaları iki aşamada kopyalamak, bağımlılıkların yeniden kurulumunu önler. Bir de bu modelin bize öğrettiği bir kural var: model, dosya özetini sıralamaya bağlıydı; Docker de dosyaları kendi içinde sabit bir sırayla işlemelidir. Bu yüzden önbellek anahtarları da ortama bağlı olmamalıdır.

Dockerfile yazarken üç tuzağa daha dikkat etmelisin. Birincisi, `RUN apt-get update` ve `RUN apt-get install` ayrı talimatlar olursa, `update` önbellekten gelip eski paket listesiyle kurulum yapılabilir. Bu yüzden ikisi tek `RUN` içinde birleştirilir (genel bilgi). İkincisi, `.dockerignore` dosyası bağlam dizininden hangi dosyaların gönderileceğini belirler; `.git` ve derleme çıktılarını dışarıda tutmazsan hem imaj büyür hem önbellek gereksiz yere geçersiz kalır. Üçüncüsü, bir dosyayı bir `RUN`'da oluşturup sonraki `RUN`'da silmek imajı küçültmez; silme, üstteki katmanda bir whiteout yazar ve dosya alttaki katmanda kalır (42.4'te gördüğümüz gibi).

## 42.7 Çok aşamalı derleme ve küçük imajlar

Bir C programını derlemek için gcc gerekir, ama çalıştırmak için gerekmez. Derleyici, başlık dosyaları ve kabuk, son imajda bulunmasına gerek olmayan şeylerdir. **Çok aşamalı derleme** (multi-stage build), bu ayrımı Dockerfile içinde yapar: birinci aşamada derlersin, ikinci aşamaya yalnızca üretilen ikiliyi kopyalarsın.

Bu bölümün CRC aracı için Dockerfile şöyle:

```bash
# Çok aşamalı derleme: araç zinciri yalnızca birinci aşamada.
FROM gcc:13 AS derle
WORKDIR /src
COPY crc32_arac.c .
RUN mkdir /cikti && \
    gcc -O2 -Wall -Wextra -Werror -std=c11 -static \
        crc32_arac.c -o /cikti/crc32_arac

# Çalışma aşaması: boş imaj. İçinde kabuk, paket yöneticisi yok.
FROM scratch
COPY --from=derle /cikti/crc32_arac /crc32_arac
USER 65532:65532
ENTRYPOINT ["/crc32_arac"]
```

Birinci aşamanın adı `derle`'dir ve yalnızca orada gcc bulunur. İkinci aşama `scratch` imajıdır: hiçbir dosyası olmayan boş bir imaj. Bu imajın içine yalnızca `crc32_arac` kopyalanır. Dosya statik bağlanmış olduğu için paylaşımlı kütüphanelere ihtiyaç duymaz; bu nedenle boş imajda çalışabilir. `USER 65532:65532` satırını dikkat çekici bulabilirsin: `scratch` içinde `/etc/passwd` olmadığı için kullanıcı adıyla değil sayısal kimlikle çalışmak zorundayız.

Statik bağlamanın bedelini ölçebiliriz. Aynı kaynağı iki biçimde derledik: varsayılan (dinamik) ve `-static` ile:

```term
$ gcc -O2 -Wall -Wextra -std=c11 crc32_arac.c -o crc_dyn
$ gcc -O2 -Wall -Wextra -std=c11 -static crc32_arac.c -o crc_st
$ stat -c "%s %n" crc_dyn crc_st
16088 crc_dyn
785496 crc_st
$ ldd ./crc_dyn
	linux-vdso.so.1 (0x00007ffc71de7000)
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007d0c28c00000)
	/lib64/ld-linux-x86-64.so.2 (0x00007d0c28ecd000)
$ printf "123456789" | ./crc_st
cbf43926
```

Dinamik ikili 16 088 bayt, statik ikili 785 496 bayt. Dinamik ikili çalışmak için `libc.so.6` ve yükleyiciye ihtiyaç duyar; `ldd` bunları listeler. Statik ikili bu bağımlılıkları içine gömer, bu yüzden daha büyüktür ama boş bir imajda çalışabilir. Bölüm 37'de aynı ölçümü farklı bir programla yapmıştık ve benzer büyüklükte bir fark bulmuştuk; bu kıyas, boyut farkının programa değil bağlama biçimine bağlı olduğunu gösteriyor.

Şekil 42.6, iki aşamayı ve aralarındaki kopyalama bağını gösteriyor. Derleme aşamasının boyutunu bu makinede ölçemedik, çünkü Docker çalışmıyordu; bu yüzden tabloya yalnızca ikili boyutlarını yazıyoruz.

![Şekil 42.6: Çok aşamalı derleme. Derleyici yalnızca birinci aşamada yaşar; son imaj yalnızca statik bağlanmış tek ikili taşır.](gorseller/b42_cok_asama.png)

Statik bağlamanın bir bedeli daha vardır: kütüphanedeki bir güvenlik düzeltmesi, o kütüphaneyi gömmüş her ikiliyi yeniden derlemeyi gerektirir. Dinamik bağlamada yalnızca paylaşılan kütüphane güncellenir (genel bilgi). Hangi yaklaşımın doğru olduğu, dağıtımın güncelleme hızına ve güvenlik politikasına bağlıdır; bu bir mühendislik kararıdır, tek doğru yanıtı yoktur.

::: baglanti
Bağlama süreci, sembol çözümü ve statik ile dinamik bağlamanın ayrıntıları Bölüm 37'de. Bu bölümde yalnızca bağlamanın imaj boyutuna etkisini ölçtük.
:::

## 42.8 Konteyner çalışma zamanı: PID 1, sinyaller ve zombiler

Bir konteynerin içindeki ilk süreç, PID ad alanının PID 1'idir. Bu süreç sıradan bir uygulama gibi görünse de, Linux'ta **init** rolünü de üstlenir ve iki sorumluluğu vardır. Birincisi, konteynerin durdurulması istendiğinde gelen sinyallere doğru tepki vermek. İkincisi, yetim kalan süreçlerin zombilerini toplamak. Bölüm 26'da zombi süreci ve yetim süreçleri gördük; burada bu iki sorumluluğun konteyner içinde neden kritik olduğunu ölçeceğiz.

Önce sinyal davranışını ele alalım. Aşağıdaki küçük C programı SIGTERM için bir işleyici kurabilir ya da kurmayabilir. Komut satırı argümanı bunu seçer. Program, 30 saniye boyunca bekler ve SIGTERM gelip gelmediğini bildirir:

```c
/* sinyal_pid1.c: PID ad alanında 1 numaralı süreçte SIGTERM.
 * Kullanım: ./sinyal_pid1 yok   (işleyici yok)
 *           ./sinyal_pid1 var   (işleyici var)
 * Derleme: gcc -O2 -Wall -Wextra -std=c11
 *          -D_POSIX_C_SOURCE=200809L sinyal_pid1.c */
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

static volatile sig_atomic_t alindi = 0;

static void on_term(int sig)
{
    (void)sig;
    alindi = 1;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc > 1 && strcmp(argv[1], "var") == 0) {
        struct sigaction sa;
        memset(&sa, 0, sizeof sa);
        sa.sa_handler = on_term;
        sigaction(SIGTERM, &sa, NULL);
    }
    printf("pid=%d hazir\n", (int)getpid());
    for (int i = 0; i < 30 && !alindi; i++)
        sleep(1);
    printf("pid=%d %s\n", (int)getpid(),
           alindi ? "SIGTERM yakalandi, temiz cikis"
                  : "30 sn bitti, SIGTERM gelmedi");
    return 0;
}
```

Programı yeni bir PID ad alanında başlattık ve ana makineden, yani ad alanının dışından, SIGTERM gönderdik. İşleyici olmayan sürümün tepkisi şuydu:

```term
$ unshare -r -p -f --mount-proc ./sinyal_pid1 yok > p1.log &
$ kill -TERM <ana makine PID'i>
SIGTERM sonrasi: S+   sinyal_pid1
$ cat p1.log
pid=1 hazir
```

Süreç SIGTERM'den sonra da hayatta kaldı (`S+` durumu) ve günlüğe başka bir şey yazmadı. İşleyici kuran sürümde ise tablo değişti:

```term
$ unshare -r -p -f --mount-proc ./sinyal_pid1 var > p2.log &
$ kill -TERM <ana makine PID'i>
$ cat p2.log
pid=1 hazir
pid=1 SIGTERM yakalandi, temiz cikis
```

Bu fark bir çekirdek kuralından gelir: bir ad alanının init süreci için çekirdek, işleyicisi kurulmamış sinyalleri yok sayar. SIGKILL (ve SIGSTOP) bu kuralın dışındadır; çekirdek bunları her zaman uygular (genel bilgi). `docker stop` gibi araçlar önce SIGTERM gönderir, belirli bir süre bekler, sonra SIGKILL gönderir (genel bilgi). Yani PID 1 bir işleyici kurmamışsa her durdurma, zaman aşımına uğrayıp zorla öldürmeyle biter.

Aynı davranış Python için de geçerlidir. Python, SIGTERM'i varsayılan olarak yakalamaz; PID 1 olarak çalışan bir Python betiği SIGTERM'i yok sayar:

```term
$ unshare -r -p -f --mount-proc python3 -c 'import time,os; \
    print("pid", os.getpid(), flush=True); time.sleep(3); \
    print("bitti", flush=True)' > /tmp/e13.log 2>&1 &
$ kill -TERM <ana makine PID'i>
SIGTERM sonrasi hayatta mi: evet
$ cat /tmp/e13.log
pid 1
bitti
```

Bu makinede deneyi "SIGTERM gönder, sonra bekle" biçiminde yaptık: betik SIGTERM'den sonra da çalışmaya devam etti ve normal şekilde bitti.

Zombi toplama ikinci sorumluluktur. Bir konteynerde bir süreç, ebeveyni çıkmadan kendi çocuğunu bırakırsa, o çocuk yetim kalır ve PID 1'e devredilir. PID 1 çocuğu `wait` ile toplamazsa çocuk zombi olarak kalır. Aşağıdaki Python betiği bu durumu kurar: alt kabuk, bir torun süreç başlatıp çıkar; torun yetim kalır. Betik PID 1 olarak çalıştığı için torunu toplamaz:

```python
import os, subprocess, time
# Torun süreç yetim kalır: ebeveyni (sh) çıkar, PID 1 toplamaz
subprocess.run(["sh", "-c", "sleep 0.3 & exit 0"])
time.sleep(1.0)
for n in sorted(int(p) for p in os.listdir("/proc") if p.isdigit()):
    try:
        f = open("/proc/%d/stat" % n).read()
    except OSError:
        continue
    alan = f.rsplit(")", 1)[1].split()
    durum, ppid = alan[0], alan[1]
    comm = f[f.index("(") + 1:f.rindex(")")]
    print("pid=%d ppid=%s durum=%s ad=%s" % (n, ppid, durum, comm))
```

Betiği yeni bir PID ad alanında çalıştırdığımızda çıktı şuydu:

```term
$ unshare -r -p -f --mount-proc python3 zombi_snippet.py
pid=1 ppid=0 durum=R ad=python3
pid=3 ppid=1 durum=Z ad=sleep
```

`pid=3` olan `sleep` sürecinin durumu `Z`, yani zombi. Ebeveyni PID 1'dir ve PID 1 onu toplamamıştır. Bir konteynerde bu sorun birikir: çok sayıda zombi süreç süreç tablosundaki yerleri doldurur. Bunu önlemek için PID 1'in ya çocukları toplamasını sağlayacak bir hafif init kullanılır, ya da uygulamanın kendisi bu sorumluluğu üstlenir.

Bu iki deneyin sonucu, uygulamanın konteyner içinde nasıl tasarlanacağını belirler:

- Uygulama PID 1 olarak çalışacaksa, SIGTERM için bir işleyici kurmalı ve kapanırken yeni istek kabul etmeyi bırakmalıdır.
- Uygulama çocuk süreç üretiyorsa, PID 1 olarak bir init (tini gibi) kullanmak daha güvenlidir. Docker'da `docker run --init` bu işi yapar ve Compose'da `init: true` aynı anlama gelir (genel bilgi).

Aşağıdaki API, ilk maddeyi uygular: SIGTERM geldiğinde yeni istek kabul etmeyi bırakır, mevcut işi bitirir ve kapanış günlüğü yazar. Bu API'yi PID 1 olarak bir ad alanında çalıştırıp dışarıdan SIGTERM gönderdik. API'ye istek gönderen küçük istemci şu:

```python
import json
import urllib.request as u

TABAN = "http://127.0.0.1:18080"
print("health:", u.urlopen(TABAN + "/health").read().decode())
yuk = json.dumps({"sira": 3, "irtifa_m": 1234.5}).encode()
r = u.Request(TABAN + "/telemetri", data=yuk)
print("telemetri:", u.urlopen(r).status)
try:
    u.urlopen(u.Request(TABAN + "/telemetri", data=b'{"sira":"x"}'))
except u.HTTPError as e:
    print("gecersiz govde:", e.code)
```

Deneyin çıktısı şöyle. Günlük satırlarındaki `zaman` değerlerini okunaklı olması için kısalttık; olayların sırası ve alanları gerçek çıktıdır:

```term
$ PORT=18080 APP_VERSION=1.2.0 unshare -r -p -f --mount-proc \
    python3 telemetri_api.py &
$ python3 istemci.py
health: {"durum": "canli", "surum": "1.2.0"}
telemetri: 201
gecersiz govde: 400
$ kill -TERM <ana makine PID'i>
SIGTERM sonrasi hayatta mi: hayir
$ cat /tmp/api_pid1.log
{"zaman": ..., "olay": "basladi", "port": 18080, "surum": "1.2.0"}
{"zaman": ..., "olay": "kabul", "sira": 3, "irtifa_m": 1234.5}
{"zaman": ..., "olay": "sinyal", "sinyal": "SIGTERM"}
{"zaman": ..., "olay": "kapandi", "kabul": 1}
```

Günlükteki zaman damgalarının uzunluğunu kısalttık (`...`); olayların sırası ve sayıları gerçek çıktıdır. API, PID 1 olarak SIGTERM'i yakaladı, `kapandi` olayını yazdı ve kabul sayısını (1) raporladı.

::: dikkat
Sinyal işleyicisinin kendisi dikkatli yazılmalıdır. Bölüm 26'da gördüğümüz gibi, bir işleyici yalnızca async-signal-safe işlemler yapmalıdır. Python'da işleyici, kapatma olayını başka bir iş parçacığına devreder; C'de yalnızca bir bayrak kaldırmak yeterlidir (sinyal_pid1.c'deki gibi).
:::

## 42.9 Compose, yapılandırma ve 12 faktör

Gerçek bir uygulama tek bir süreçten oluşmaz. Bir API, bir veritabanı ve bir ters vekil (reverse proxy) birlikte çalışır. **Docker Compose**, bu çok servisli yapıyı tek bir YAML dosyasında tanımlar: her servisin imajı ya da derleme bağlamı, hangi ağlarda olduğu, hangi hacimleri (kalıcı veri) kullandığı, hangi sırları aldığı ve hangi sağlık koşuluna bağlı olduğu.

Bu bölümün compose dosyası üç servisten oluşur: API, Postgres veritabanı ve nginx ters vekili. Dosyanın ilk yarısı API ve veritabanını tanımlar:

```yaml
name: telemetri

services:
  api:
    build: ./api
    init: true
    read_only: true
    tmpfs: [/tmp]
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    environment:
      APP_VERSION: "1.2.0"
      PORT: "8080"
      DB_HOST: db
    expose: ["8080"]
    depends_on:
      db:
        condition: service_healthy
    networks: [ic]

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: telemetri
      POSTGRES_USER: telemetri
      POSTGRES_PASSWORD_FILE: /run/secrets/db_parola
    secrets: [db_parola]
    volumes:
      - veri:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U telemetri -d telemetri"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks: [ic]
```

İkinci yarısı vekili, hacmi, ağları ve sırları tanımlar:

```yaml
  proxy:
    image: nginx:1.27
    ports: ["8080:80"]
    volumes:
      - ./proxy/default.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on: [api]
    networks: [ic, dis]

volumes:
  veri:

networks:
  ic:
    internal: true
  dis: {}

secrets:
  db_parola:
    file: ./secrets/db_parola.txt
```

Dosyada birkaç güvenlik ve ağ kararı var. `ic` ağı `internal: true` ile işaretlendi; bu ağdaki servisler dış dünyaya doğrudan çıkamaz. Dış dünyaya açılan tek yer `dis` ağına bağlı olan vekildir. API `read_only: true` ve `cap_drop: [ALL]` ile çalışır; yani kök dosya sistemine yazamaz ve Linux yeteneklerinin hiçbirine sahip değildir. `init: true` PID 1 sorununa karşı 42.8'de anlattığımız init sürecini ekler. Veritabanı, parolasını bir dosyadan (`/run/secrets/db_parola`) okur; sır, ortam değişkeni olarak görünmez.

Şekil 42.7, servislerin ağlara ve hacimlere bağlanma biçimini gösteriyor.

![Şekil 42.7: Compose servis grafiği. Vekil iki ağda da bulunur; API ve veritabanı yalnızca dışa kapalı iç ağda çalışır. Veritabanı, sağlık denetimini geçtikten sonra API'nin başlamasını sağlar.](gorseller/b42_compose_graf.png)

Vekilin yönlendirme yapılandırması tek bir `server` bloğudur. Dış isteği iç ağdaki `api` servisine iletir:

```bash
server {
    listen 80;

    location / {
        proxy_pass http://api:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
```

Compose dosyasının sözdizimini Docker motoru olmadan da denetleyebilirsin. `docker compose config` komutu dosyayı ayrıştırıp birleşik yapılandırmayı üretir; bu işlem motora bağlanmaz. Dosyayı denetleyip hata çıktısı almadık:

```term
$ docker compose config -q
$ echo $?
0
```

Bu, dosyanın sözdiziminin geçerli olduğunu gösterir, ama konteynerlerin gerçekten ayağa kalkıp birbirine bağlandığını göstermez. O doğrulama için motorun çalışması gerekir; bu bölümde bunu yapamadık.

### 12 faktör: uygulama konteyner için nasıl yazılır?

Heroku'nun 2011'de yayımladığı **12 faktör uygulama** ilkeleri (genel bilgi), konteynere uygun servisler yazmanın pratik bir kontrol listesidir. Her ilke, dağıtımda sorun çıkaran bir alışkanlığa karşılık gelir. Aşağıdaki tabloda hangi ilkenin API kodunda nerede karşılandığını gösteriyoruz.

| İlke | Ne demek | Bu bölümde nerede |
|---|---|---|
| Yapılandırma ortamda | Sürüme göre değişen değer kodda olmaz | `PORT`, `APP_VERSION` ortam değişkenlerinden okunur |
| Arka uç servisleri bağlı kaynak | Veritabanı bir ağ adresidir | compose'da `DB_HOST: db` |
| Durumsuz süreçler | Kalıcı veri süreçte değil hacimde tutulur | API'de yalnızca sayaç var; veri hacimde olmalı |
| Günlükler akış olarak | Dosyaya yazmak yerine stdout'a yaz | `gunluk()` JSON satırlarını stdout'a yazar |
| Kolay kapanma | SIGTERM'e temiz tepki | `kapat()` işleyicisi ve `/hazir` 503 döner |

Bu ilkeleri uygulayan API'nin kodu aşağıda. Bölüm 40'ta tasarlayacağın API bu kodun yerine geçebilir. Burada ise dağıtım zincirini gösterebilmek için yalnızca standart kütüphaneyle yazılmış bağımsız bir karşılık kullanıyoruz. Dosya üç parça hâlinde verilmiştir.

```python
# -*- coding: utf-8 -*-
"""Telemetri API'si: Bölüm 40'taki arayüzün bu bölümdeki karşılığı.

Yapılandırma ortamdan okunur (12 faktör). Yalnızca standart
kütüphane. Günlükler stdout'a JSON satırı olarak yazılır.
"""
import json
import os
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SURUM = os.environ.get("APP_VERSION", "gelistirme")
PORT = int(os.environ.get("PORT", "8080"))

durum = {"kapaniyor": False, "kabul": 0}
kilit = threading.Lock()

def gunluk(olay, **alanlar):
    kayit = {"zaman": round(time.time(), 3), "olay": olay}
    kayit.update(alanlar)
    print(json.dumps(kayit, ensure_ascii=False), flush=True)
```

Sınıfın GET isteklerini yanıtlayan kısmı, sağlık ve hazırlık uçlarını içerir. `/health` süreç canlıysa 200 döner; `/hazir` ise kapanış başladıysa 503 döner. Bu ayrım, 42.11'deki dağıtım stratejilerinde önemli olacak.

```python
class Istekci(BaseHTTPRequestHandler):

    def _yanit(self, kod, govde):
        veri = json.dumps(govde, ensure_ascii=False).encode("utf-8")
        self.send_response(kod)
        tur = "application/json; charset=utf-8"
        self.send_header("Content-Type", tur)
        self.send_header("Content-Length", str(len(veri)))
        self.end_headers()
        self.wfile.write(veri)

    def do_GET(self):
        if self.path == "/health":
            self._yanit(200, {"durum": "canli", "surum": SURUM})
        elif self.path == "/hazir":
            if durum["kapaniyor"]:
                self._yanit(503, {"durum": "kapaniyor"})
            else:
                self._yanit(200, {"durum": "hazir"})
        else:
            self._yanit(404, {"hata": "bulunamadi"})
```

Telemetri uç noktası gelen JSON gövdesini doğrular. Geçersiz gövde 400 döner ve sayaç artmaz; geçerli gövde 201 ile kabul edilir ve JSON günlüğüne yazılır.

```python
    def do_POST(self):
        if self.path != "/telemetri":
            self._yanit(404, {"hata": "bulunamadi"})
            return
        uzunluk = int(self.headers.get("Content-Length", "0"))
        try:
            veri = json.loads(self.rfile.read(uzunluk))
            sira = int(veri["sira"])
            irtifa = float(veri["irtifa_m"])
        except (ValueError, KeyError, TypeError):
            self._yanit(400, {"hata": "geçersiz gövde"})
            return
        with kilit:
            durum["kabul"] += 1
        gunluk("kabul", sira=sira, irtifa_m=irtifa)
        self._yanit(201, {"kabul": True, "sira": sira})

    def log_message(self, format, *args):
        pass  # erişim satırları kapalı; kendi günlüğümüz var
```

Son parça sunucuyu kurar ve SIGTERM/SIGINT işleyicisini bağlar. İşleyici kapanış bayrağını kaldırır ve sunucuyu ayrı bir iş parçacığında durdurur.

```python
def sunucu_olustur(port):
    srv = ThreadingHTTPServer(("0.0.0.0", port), Istekci)
    srv.daemon_threads = True
    return srv

def main():
    srv = sunucu_olustur(PORT)

    def kapat(sig, kare):
        durum["kapaniyor"] = True
        gunluk("sinyal", sinyal=signal.Signals(sig).name)
        # shutdown() serve_forever döngüsünü durdurur ve bitmesini
        # bekler. Ana iş parçacığından çağrılırsa kilitlenir; bu
        # yüzden ayrı bir iş parçacığında çağırıyoruz.
        threading.Thread(target=srv.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, kapat)
    signal.signal(signal.SIGINT, kapat)
    gunluk("basladi", port=PORT, surum=SURUM)
    srv.serve_forever()
    srv.server_close()
    gunluk("kapandi", kabul=durum["kabul"])

if __name__ == "__main__":
    main()
```

Konteyner sağlık denetimi için aynı uç noktayı kullanan küçük bir betik ve imajın Dockerfile'ı:

```python
# -*- coding: utf-8 -*-
# saglik.py: HEALTHCHECK için. Çıkış kodu 0 sağlıklı, 1 sağlıksız.
import sys
import urllib.request

URL = "http://127.0.0.1:8080/health"
try:
    r = urllib.request.urlopen(URL, timeout=1)
    sys.exit(0 if r.status == 200 else 1)
except OSError:
    sys.exit(1)
```

```bash
# Tek aşama: bağımlılık yok, bu yüzden requirements.txt yok.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PORT=8080 APP_VERSION=1.2.0
RUN useradd --uid 10001 --no-create-home uygulama
WORKDIR /uygulama
COPY telemetri_api.py saglik.py ./
USER 10001
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=2s --retries=3 \
  CMD ["python", "saglik.py"]
ENTRYPOINT ["python", "telemetri_api.py"]
```

Dockerfile, uygulamayı root olmayan bir kullanıcıyla (`uid 10001`) çalıştırır ve `HEALTHCHECK` ile konteyner sağlığını sürekli denetler. Bağımlılık olmadığı için `requirements.txt` yoktur; Bölüm 39'daki pytest gibi bir bağımlılık eklenirse, bağımlılık listesini kaynak kodundan önce kopyalamak 42.6'daki önbellek kuralına göre doğru olur.

## 42.10 Sürekli entegrasyon ve sürüm etiketleme

**Sürekli entegrasyon** (CI), her değişiklikte kodun derlendiğini, testlerin geçtiğini ve artefaktın üretildiğini otomatik olarak doğrulayan bir hattır. Bölüm 39'da yazdığımız testler, ancak bir CI hattında her commit'te çalışırsa bir anlam taşır. Bölüm 38'de gördüğümüz etiketler (tag) ise hattın ürettiği artefaktın hangi kaynak sürümüne ait olduğunu söyler.

Şekil 42.8, hattın adımlarını ve her adımı yerelde çalıştıran komutları gösteriyor. Hattın her adımı bir kapıdır: biri başarısız olursa sonraki adımlar çalışmaz.

![Şekil 42.8: CI hattı. Her adım ci.sh'ın bir alt komutudur; aynı betik yerelde ve CI iş akışında çağrılır.](gorseller/b42_ci_hatti.png)

Hattın tüm adımlarını tek bir betikte topladık: `ci.sh`. Betik, GitHub Actions'a bağlı değildir; böylece adımları kendi makinende aynen çalıştırabilirsin. Betik dört parçadan oluşur.

```bash
#!/usr/bin/env bash
# ci.sh: CI adımlarının yerel sürümü. GitHub Actions da bu betiği
# çağırır.
# Kullanım: ./ci.sh [lint|testler|kapsama|derle|imaj|tum]
set -euo pipefail
cd "$(dirname "$0")"
ESIK=${KAPSAMA_ESIK:-80}

surum() {
  git describe --tags --always --dirty 2>/dev/null || echo surumsuz
}

lint() {
  echo "[lint] C: uyarılar hataya dönüşür"
  gcc -Wall -Wextra -Werror -std=c11 -O2 -c crc32_arac.c \
      -o /dev/null
  echo "[lint] Python: derleme denetimi"
  python3 -W error -m py_compile \
      api/telemetri_api.py api/test_telemetri_api.py
}

testler() {
  echo "[testler] Python birim testleri"
  (cd api && python3 -m unittest -q test_telemetri_api 2>&1 \
     | tail -n 3)
  echo "[testler] C denetim değerleri"
  gcc -O2 -std=c11 crc32_arac.c -o crc32_test
  [ "$(printf '123456789' | ./crc32_test)" = "cbf43926" ]
  [ "$(printf '' | ./crc32_test)" = "00000000" ]
  echo "[testler] tamam"
}
```

İkinci parça, C kapsamasını ölçen adımı içerir. Kapsama için `gcov` kullandık: derleyicinin ürettiği sayaçlarla hangi satırların çalıştığını ölçer. Eşik değeri `KAPSAMA_ESIK` ortam değişkeniyle geçersiz kılınabilir.

```bash
kapsama() {
  echo "[kapsama] gcov ile C satır kapsaması, eşik %$ESIK"
  rm -f crc32_arac.gcda crc32_arac.gcno crc32_arac.o
  # Nesne dosyasını ayrı derlemek .gcda adını kaynağa bağlar
  gcc -O0 --coverage -std=c11 -c crc32_arac.c -o crc32_arac.o
  gcc --coverage crc32_arac.o -o crc32_kapsa
  printf '123456789' | ./crc32_kapsa > /dev/null
  printf '' | ./crc32_kapsa > /dev/null
  oran=$(gcov crc32_arac.c 2>/dev/null \
         | sed -n 's/^Lines executed:\([0-9.]*\)%.*/\1/p' \
         | head -n 1 || true)
  if [ -z "$oran" ]; then
    echo "[kapsama] gcov oranı okunamadı"; exit 1
  fi
  echo "satır kapsaması: %$oran"
  awk -v o="$oran" -v e="$ESIK" \
    'BEGIN { exit !(o + 0 >= e + 0) }' \
    || { echo "[kapsama] BAŞARISIZ"; exit 1; }
}
```

Üçüncü parça, statik derlemeyi ve sürüm dosyasını üretir. Sürüm, `git describe` ile etiketten türetilir.

```bash
derle() {
  mkdir -p dist
  gcc -O2 -Wall -Wextra -Werror -std=c11 -static \
      crc32_arac.c -o dist/crc32_arac
  surum > dist/SURUM
  (cd dist && sha256sum crc32_arac SURUM > SHA256SUMS)
  echo "[derle] sürüm: $(cat dist/SURUM)"
  ls -l dist
}

imaj() {
  if command -v docker > /dev/null 2>&1 \
     && docker info > /dev/null 2>&1; then
    docker build -t "crc32-arac:$(surum)" .
  elif [ "${IMAJ_ZORUNLU:-0}" = 1 ]; then
    echo "[imaj] docker yok, IMAJ_ZORUNLU=1: BAŞARISIZ"; exit 1
  else
    echo "[imaj] docker kullanılamıyor: adım yerelde atlandı"
  fi
}
```

Dördüncü parça, komut satırı argümanını adımlara eşleyen `case` bloğudur.

```bash
case "${1:-tum}" in
  lint)    lint ;;
  testler) testler ;;
  kapsama) kapsama ;;
  derle)   derle ;;
  imaj)    imaj ;;
  tum)     lint; testler; kapsama; derle; imaj ;;
  *) echo "kullanım: $0 [lint|testler|kapsama|derle|imaj|tum]"
     exit 2 ;;
esac
```

Python testleri, API'nin beş davranışını doğrular: sağlık, kabul, geçersiz gövde, kapanış sırasında hazır olmama ve bilinmeyen yol. Test dosyası şöyle:

```python
# -*- coding: utf-8 -*-
import json
import threading
import unittest
import urllib.error
import urllib.request

import telemetri_api as api

class ApiTest(unittest.TestCase):

    def setUp(self):
        api.durum.update(kapaniyor=False, kabul=0)
        # 0 numaralı port: işletim sistemi boş bir port seçer
        self.srv = api.sunucu_olustur(0)
        port = self.srv.server_address[1]
        self.taban = "http://127.0.0.1:%d" % port
        sunucu = threading.Thread(target=self.srv.serve_forever,
                                  daemon=True)
        sunucu.start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()

    def istek(self, yol, govde=None):
        veri = None if govde is None else json.dumps(govde).encode()
        req = urllib.request.Request(self.taban + yol, data=veri)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())
```

```python
    def test_saglik(self):
        kod, govde = self.istek("/health")
        self.assertEqual((kod, govde["durum"]), (200, "canli"))

    def test_telemetri_kabul(self):
        yuk = {"sira": 7, "irtifa_m": 120.5}
        kod, _ = self.istek("/telemetri", yuk)
        self.assertEqual(kod, 201)
        self.assertEqual(api.durum["kabul"], 1)

    def test_gecersiz_govde(self):
        kod, _ = self.istek("/telemetri", {"sira": "yok"})
        self.assertEqual(kod, 400)
        self.assertEqual(api.durum["kabul"], 0)

    def test_kapanirken_hazir_degil(self):
        api.durum["kapaniyor"] = True
        kod, govde = self.istek("/hazir")
        self.assertEqual((kod, govde["durum"]), (503, "kapaniyor"))

    def test_bilinmeyen_yol(self):
        kod, _ = self.istek("/yok")
        self.assertEqual(kod, 404)

if __name__ == "__main__":
    unittest.main()
```

Hattı `tum` argümanıyla çalıştırdık. Kullanılabilir olmayan Docker adımı, zorunlu değilse yerelde atlanır; CI'da zorunlu tutulur. Çıktı şöyle:

```term
$ ./ci.sh tum
[lint] C: uyarılar hataya dönüşür
[lint] Python: derleme denetimi
[testler] Python birim testleri
Ran 5 tests in 2.532s

OK
[testler] C denetim değerleri
[testler] tamam
[kapsama] gcov ile C satır kapsaması, eşik %80
satır kapsaması: %100.00
[derle] sürüm: v1.2.0
total 776
-rw-r--r-- 1 merty merty    149 Oct 21 22:05 SHA256SUMS
-rw-r--r-- 1 merty merty      7 Oct 21 22:05 SURUM
-rwxr-xr-x 1 merty merty 785496 Oct 21 22:05 crc32_arac
[imaj] docker kullanılamıyor: adım yerelde atlandı
tum_rc=0
$ ./ci.sh imaj (IMAJ_ZORUNLU=1)
[imaj] docker yok, IMAJ_ZORUNLU=1: BAŞARISIZ
imaj_rc=1
$ ./ci.sh bilinmeyen
kullanım: ci.sh [lint|testler|kapsama|derle|imaj|tum]
bilinmeyen_rc=2
```

İlk satır (`$ ./ci.sh tum`) hattı başlatan komut, `tum_rc=0` ise betiğin başarılı çıktığını gösterir. `IMAJ_ZORUNLU=1` ile imaj adımı yeniden çalıştırıldığında ise betik, Docker olmadığı için başarısız oldu ve çıkış kodu 1 döndü. Bu fark, yerel geliştirme ile CI arasındaki sözleşmeyi gösterir: yerelde eksik araç uyarıdır, CI'da hatadır.

Sürüm etiketi, hattın ürettiği artefaktı kaynağa bağlar. Geçici bir Git deposunda şunu gördük:

```term
$ git describe --tags --always --dirty   (etiket tam üstünde)
v1.2.0
$ git describe --tags --always --dirty   (etiketten sonra 1 commit)
v1.2.0-1-g312b8d3
$ git describe --tags --always --dirty   (kirli çalışma ağacı)
v1.2.0-1-g312b8d3-dirty
```

`v1.2.0` etiketin üstünde olduğumuzu, `-1-g312b8d3` etiketten sonra bir commit ve o commit'in kısa kimliğini, `-dirty` ise commit edilmemiş değişiklik olduğunu gösterir. Bu üç bilgi, bir artefaktın hangi kaynaktan ve hangi temizlik düzeyinde üretildiğini kanıtlar. Savunma sanayiinde bu tür bir izlenebilirlik, değişiklik yönetiminin temelidir.

GitHub Actions iş akışı ise aynı adımları YAML'da çağırır. Bu dosyayı yazdık ve ayrıştırılabilirliğini doğruladık, ama GitHub üzerinde çalıştırmadık:

```yaml
name: ci
on:
  push:
  pull_request:

jobs:
  dogrula:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # git describe tüm etiketleri görmeli
      - name: Lint
        run: ./ci.sh lint
      - name: Test
        run: ./ci.sh testler
      - name: Kapsama eşiği
        run: KAPSAMA_ESIK=80 ./ci.sh kapsama
      - name: Statik derleme
        run: ./ci.sh derle
      - name: İmaj derle (zorunlu)
        env:
          IMAJ_ZORUNLU: "1"
        run: ./ci.sh imaj
      - uses: actions/upload-artifact@v4
        with:
          name: crc32-arac-${{ github.sha }}
          path: dist/
```

Dosyayı Python'un YAML ayrıştırıcısıyla okuduğumuzda yapısı şöyle göründü:

```term
$ python -c "import yaml; d=yaml.safe_load(open('ci.yml')); \
    print('jobs:', list(d['jobs'])); \
    print('adim sayisi:', len(d['jobs']['dogrula']['steps']))"
jobs: ['dogrula']
adim sayisi: 7
```

::: baglanti
Git etiketlerinin ve commit kimliklerinin nasıl üretildiğini Bölüm 38'de, testlerin kapsama ölçümünü Bölüm 39'da gördük. Bu hat, o iki bölümün çıktısını tek bir otomatik akışta birleştirir.
:::

## 42.11 Dağıtım stratejileri ve geri alma

Bir yazılım sürümünü kullanıcıya ulaştırmanın birkaç yolu vardır. Her yolun kullanıcıya görünen bir kesinti, ayrı bir kaynak maliyeti ve farklı bir geri alma (rollback) hızı vardır. Aşağıdaki tablo, sık kullanılan beş stratejiyi bu üç ölçüte göre karşılaştırıyor.

| Strateji | Nasıl çalışır | Kesinti | Ek kaynak | Geri alma |
|---|---|---|---|---|
| Yeniden oluştur (recreate) | Eskiyi tamamen durdur, yeniyi başlat | Var | Yok | Eski sürümü yeniden başlat |
| Yuvarlanan (rolling) | Kopyaları tek tek değiştir | Yok (kapasite düşebilir) | Az (birkaç kopya) | Aynı yöntemle geriye yuvarla |
| Mavi-yeşil (blue-green) | Tam yeni ortam kur, trafiği bir anda geçir | Yok | Tam çift kapasite | Trafiği eski ortama geri çevir |
| Kanarya (canary) | Yeni sürümü küçük bir trafik dilimine aç | Yok | Az | Dilimi sıfırla |
| Özellik bayrağı | Kod hep dağıtılır, özellik çalışma anında açılır | Yok | Yok | Bayrağı kapat |

Bu tablodaki "geri alma" sütunu önemlidir: iyi bir strateji, kötü bir sürümden en hızlı çıkışı sağlayan stratejidir. Bu yüzden karar tablosu, sürümün risk düzeyine bağlıdır. Veri şeması değişmiyorsa ve yeni sürüm küçük bir hata taşıyorsa, yuvarlanan dağıtım genellikle yeterlidir. Veri şeması değişiyorsa ve geri dönüş zorsa, mavi-yeşil veya kanarya gibi trafik kontrollü stratejiler tercih edilir. Hiçbir strateji, veri tabanı şemasının geri dönüşsüzlüğünü ortadan kaldırmaz; bu yüzden şema değişikliklerini sürüm değişikliklerinden ayrı tutmak gerekir (genel bilgi).

Dağıtımın kararlı çalışması için yeni kopyanın trafik almaya hazır olduğunu bilmek gerekir. Bunun için iki sonda kullanılır. **Canlılık** (liveness) sondası süreç hâlâ çalışıyor mu sorusunu yanıtlar; yanıt hayırsa süreç yeniden başlatılır. **Hazırlık** (readiness) sondası trafik alabilir mi sorusunu yanıtlar; yanıt hayırsa süreç yük dengeleyicinin havuzundan çıkarılır ama öldürülmez. API'miz bu ayrımı `/health` ve `/hazir` uç noktalarıyla yapar: kapanış başladığında `/hazir` 503 döner, `/health` ise hâlâ 200 döner, çünkü süreç hâlâ canlıdır.

Stratejileri karşılaştırmak için basit bir zaman modeli yazdık. Model, dört kopyalık bir servisi ve iki tiklik açılış süresini kullanır. Tik bir zaman adımıdır; gerçek saniye değildir. Sayılar bir modelin parametreleridir, bir ölçüm değildir; amaç stratejilerin davranış farkını görmektir.

```python
# -*- coding: utf-8 -*-
# dagitim_strateji.py: üç dağıtım stratejisinin ZAMAN MODELİ.
# N = 4 kopya; pod açılışı 2 tik sürer. Tik bir zaman adımıdır,
# gerçek saniye değildir. Çıktı CSV'dir (engine/veri/ için).
import csv
import os
import sys

N = 4
ACILIS = 2
TIKLER = 6

class Pod:
    def __init__(self, surum, t):
        self.surum = surum
        self.hazir_t = t + ACILIS

    def hazir(self, t):
        return t >= self.hazir_t

def sayim(pods, t, hizmet):
    """Trafiği alan sürümün hazır pod sayısı; diğeri 0 sayılır."""
    v1 = sum(1 for p in pods if p.surum == "v1" and p.hazir(t))
    v2 = sum(1 for p in pods if p.surum == "v2" and p.hazir(t))
    if hizmet == "v1":
        v2 = 0
    elif hizmet == "v2":
        v1 = 0
    return (v1, v2, len(pods))

def yeniden_olustur():
    """Önce v1 tamamen silinir, sonra v2 başlatılır."""
    pods = [Pod("v2", 0) for _ in range(N)]
    return [sayim(pods, t, None) for t in range(TIKLER)]
```

Mavi-yeşil stratejisi, tüm yeni kopyaları açtıktan sonra trafiği bir anda geçirir ve eski sürümü ancak o zaman kaldırır. Yuvarlanan strateji ise tek bir sürüm kuralı uygular: her an en az `N - maxUnavailable` kadar hazır kopya bulunmalıdır.

```python
def mavi_yesil():
    """v2 tam kapasiteyle açılır. t=2'de trafik geçer,
    t=3'te v1 kaldırılır."""
    pods = [Pod("v1", -10) for _ in range(N)]
    pods += [Pod("v2", 0) for _ in range(N)]
    kayit = []
    for t in range(TIKLER):
        if t == 3:
            pods = [p for p in pods if p.surum == "v2"]
        hizmet = "v1" if t < 2 else "v2"
        kayit.append(sayim(pods, t, hizmet))
    return kayit

def yuvarlanan():
    """maxSurge=1, maxUnavailable=1: N=4 için en az 3 hazır pod."""
    pods = [Pod("v1", -10) for _ in range(N)]
    olusturulan, kayit = 0, []
    for t in range(TIKLER):
        if len(pods) < N + 1 and olusturulan < N:
            pods.append(Pod("v2", t))
            olusturulan += 1
        hazir = sum(1 for p in pods if p.hazir(t))
        eskiler = [p for p in pods if p.surum == "v1"]
        if eskiler and hazir - 1 >= N - 1:
            pods.remove(eskiler[0])
        kayit.append(sayim(pods, t, None))
    return kayit
```

```python
def ana():
    csv_yolu = sys.argv[1] if len(sys.argv) > 1 else "b42_dagitim.csv"
    satirlar = []
    for ad, fn in (("yeniden_olustur", yeniden_olustur),
                   ("mavi_yesil", mavi_yesil),
                   ("yuvarlanan", yuvarlanan)):
        print(ad)
        print("  tik  v1  v2  toplam  kesinti")
        for t, (v1, v2, top) in enumerate(fn()):
            kes = 1 if v1 + v2 == 0 else 0
            print("  %-4d %-3d %-3d %-7d %d" % (t, v1, v2, top, kes))
            satirlar.append([ad, t, v1, v2, top, kes])
    with open(csv_yolu, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["strateji", "tik", "v1", "v2", "toplam",
                    "kesinti"])
        w.writerows(satirlar)
    print("yazildi:", os.path.basename(csv_yolu))

if __name__ == "__main__":
    ana()
```

Modeli çalıştırdığımızda üç stratejinin tik tik izi şu çıktıyı verdi. Model, her tikte trafiği alan sürümün hazır kopya sayısını ve kesinti olup olmadığını yazar:

```term
$ python dagitim_strateji.py b42_dagitim.csv
yeniden_olustur
  tik  v1  v2  toplam  kesinti
  0    0   0   4       1
  1    0   0   4       1
  2    0   4   4       0
  3    0   4   4       0
  4    0   4   4       0
  5    0   4   4       0
mavi_yesil
  tik  v1  v2  toplam  kesinti
  0    4   0   8       0
  1    4   0   8       0
  2    0   4   8       0
  3    0   4   4       0
  4    0   4   4       0
  5    0   4   4       0
yuvarlanan
  tik  v1  v2  toplam  kesinti
  0    3   0   4       0
  1    3   0   5       0
  2    2   1   4       0
  3    1   2   4       0
  4    1   2   5       0
  5    0   3   4       0
yazildi: b42_dagitim.csv
```

Bu çıktıdaki iki satır özellikle öğreticidir. Yeniden oluşturmada ilk iki tikte hiçbir kopya hizmet vermiyor (kesinti). Yuvarlanan dağıtımda ise hiçbir tikte hizmet veren kopya sayısı 3'ün altına düşmüyor. Şekil 42.9 aynı veriyi zaman çizelgesi olarak gösteriyor; verisi, modelin yazdığı CSV dosyasından okunuyor.

![Şekil 42.9: Üç dağıtım stratejisinin zaman çizelgesi. Yeniden oluşturmada tik 0 ve 1'de kesinti var; mavi-yeşilde trafik tik 2'de geçer; yuvarlanan dağıtımda kapasite hiçbir an 3'ün altına inmez.](gorseller/b42_dagitim_zaman.png)

## 42.12 Orkestrasyon: Kubernetes kavramları ve uzlaştırma döngüsü

Tek bir makinede birkaç konteyneri Compose ile yönetmek kolaydır. Yüzlerce makinede binlerce kopyayı yönetmek ise bir **orkestratör** ister. Kubernetes bu alanın yaygın bir çözümüdür; bu bölümde kavramlarını anlatıyoruz, bir küme kurup çalıştırmadık.

Kubernetes'in temel nesneleri şunlardır (genel bilgi): **Pod**, bir ya da birkaç konteynerin birlikte planlandığı en küçük birimdir. **ReplicaSet**, belirli sayıda eşdeğer Pod'un her an var olmasını sağlar. **Deployment**, ReplicaSet'lerin sürüm geçişini (yuvarlanan dağıtım dahil) yönetir. **Service**, Pod'ların değişken IP adreslerinin önüne sabit bir ad ve yük dengeleme koyar; yük dengelemenin genel mantığı Bölüm 41'de tasarlanacak.

Bu nesnelerin ortak ilkesi **istenen durum** (desired state) modelidir. Yazdığın bir YAML dosyası "3 kopya olsun" der; sistem bunun gerçekleşmesini sağlamak zorundadır. Bunu yapan parça bir **uzlaştırma döngüsü**dür (reconciliation loop): sürekli olarak istenen durumu ve gözlenen durumu karşılaştırır, aradaki farkı kapatacak eylemleri üretir ve bunu tekrarlar.

Döngünün mantığını, 3 kopyalık bir istenen durumla ve birkaç olayla bir model üzerinde gösterdik. Model, Kubernetes'in kendisi değildir; yalnızca döngünün karar mantığını taşır. Her tik, döngünün bir turudur: önce sağlıksız kopyaları siler, sonra eksikleri ekler, en son fazlaları siler.

```python
# -*- coding: utf-8 -*-
# uzlastirma.py: uzlaştırma döngüsünün (reconciliation loop) modeli.
# Denetleyici istenen durumla (kopya sayısı) gözlenen durumu
# (pod listesi) karşılaştırır, farkı kapatan eylemleri üretir.
import itertools

_sayac = itertools.count(1)

class Pod:
    def __init__(self):
        self.ad = "pod-%d" % next(_sayac)
        self.saglikli = True

def uzlastir(istenen, pods):
    """Tek tur: sağlıksızı sil, eksiği ekle, fazlayı sil."""
    eylemler = []
    for p in list(pods):
        if not p.saglikli:
            pods.remove(p)
            eylemler.append("-" + p.ad)
    while len(pods) < istenen:
        p = Pod()
        pods.append(p)
        eylemler.append("+" + p.ad)
    while len(pods) > istenen:
        p = pods.pop()
        eylemler.append("-" + p.ad)
    return eylemler
```

```python
def senaryo():
    pods, istenen = [], 3
    print("tik olay                 istenen mevcut eylemler")
    for t in range(1, 9):
        olay = "-"
        if t == 1:
            olay = "ilk durum"
        elif t == 4:
            olay = "pod-2 sağlıksız"
            for p in pods:
                if p.ad == "pod-2":
                    p.saglikli = False
        elif t == 6:
            olay = "istenen 3 -> 5"
            istenen = 5
        elif t == 8:
            olay = "pod-4 elle silindi"
            pods[:] = [p for p in pods if p.ad != "pod-4"]
        eylemler = uzlastir(istenen, pods)
        print("%-3d %-19s %-7d %-6d %s"
              % (t, olay, istenen, len(pods),
                 ", ".join(eylemler) or "(yok)"))

if __name__ == "__main__":
    senaryo()
```

Senaryo, dört olay içerir: 4. tikte bir kopyanın sağlık denetimini geçememesi, 6. tikte istenen sayının 3'ten 5'e çıkarılması ve 8. tikte bir kopyanın elle silinmesi. Modelin çıktısı şöyle:

```term
$ python uzlastirma.py
tik olay                 istenen mevcut eylemler
1   ilk durum           3       3      +pod-1, +pod-2, +pod-3
2   -                   3       3      (yok)
3   -                   3       3      (yok)
4   pod-2 sağlıksız     3       3      -pod-2, +pod-4
5   -                   3       3      (yok)
6   istenen 3 -> 5      5       5      +pod-5, +pod-6
7   -                   5       5      (yok)
8   pod-4 elle silindi  5       5      +pod-7
```

Her satır bir tiki gösterir. Dördüncü tikte `pod-2` sağlıksız olduğu için döngü onu siler ve yerine `pod-4`'ü açar. Sekizinci tikte biri elle silindiğinde döngü eksik kopyayı tamamlar. Şekil 42.10, döngünün dört adımını ve her adımda ne yaptığını gösteriyor.

![Şekil 42.10: Uzlaştırma döngüsü. Döngü, istenen ve gözlenen durumu karşılaştırır, farkı eylemlere çevirir ve her tikte bu turu tekrarlar.](gorseller/b42_uzlastirma.png)

Bu döngünün önemli bir özelliği vardır: olaylara değil **duruma** tepki verir. Döngü, neden bir kopyanın eksik olduğunu bilmek zorunda değildir; yalnızca istenen ile gözlenen arasındaki farkı görür. Bu, hataya dayanıklılığın temel nedenidir. Bu sayede bir kopya nasıl kaybolursa kaybolsun, döngü bir sonraki turda eksiği tamamlar.

## 42.13 Tedarik zinciri, altyapı kod olarak ve gözlemlenebilirlik

Bu bölümde yazdığımız her dosya, Dockerfile'dan compose dosyasına, CI betiğinden iş akışına kadar, bir **altyapı kodudur**. Sunucu ayarlarını elle tıklayarak yapmak yerine metin dosyasında tanımlamak, değişikliği gözden geçirilebilir, geri alınabilir ve tekrarlanabilir kılar. Bulut ortamında bunun için Terraform gibi araçlar, sunucu yapılandırması için Ansible gibi araçlar yaygındır (genel bilgi). Bu araçların ortak ilkesi, istenen durumu bildirmek ve aracın gerçek durumla farkı kapatmasını sağlamaktır; bunu 42.12'deki uzlaştırma döngüsünde zaten gördün.

**Tedarik zinciri** kavramı, yazılımın kaynağından çalışan kopyasına kadar geçen her adımın güvenilirliğini kapsar. Üç pratik öne çıkıyor. Birincisi, bağımlılıkları ve temel imajı sabitlemek: "en güncel" yerine belirli bir sürüm ya da özet kullanmak. İkincisi, yazılım bileşen listesi (SBOM) üretmek: imajın hangi kütüphaneleri içerdiğini bir belge olarak çıkarmak, böylece bir güvenlik açığı duyurulduğunda etkilenen imajları hızla bulmak. Üçüncüsü, imajları dijital olarak imzalamak ve dağıtımda imzayı doğrulamak (genel bilgi; bunun için Sigstore gibi araçlar kullanılır). Bu üçü, 42.5'te gördüğümüz tekrarlanabilir derleme ve özet kavramının üzerine kurulur.

**Gözlemlenebilirlik** (observability), dağıtılmış bir sistemin dışarıdan ne yaptığını anlamaya yarayan üç veri türüdür: günlükler, metrikler ve izler. API'miz bu kısmın en küçük parçasını uygular: her olay tek bir JSON satırı olarak stdout'a yazılır, böylece bir günlük toplayıcı bu satırları okuyabilir. Metrikler ve dağıtık izler, Bölüm 41'de sistem tasarımı çerçevesinde ele alınacak.

## 42.14 Konteynerin uymadığı yerler: gömülü ve savunma bağlamı

Konteyner güçlü bir araçtır, ama her yerde kullanılamaz. Konteyner, bir Linux çekirdeğinin üzerinde çalışan süreçler için tasarlanmıştır. Bu varsayım sağlanmadığında konteyner anlamını yitirir.

Bir mikrodenetleyici ile başlayalım. Bu kitapta EV Dashboard projen için kullandığın STM32 gibi bir Cortex-M kartında Linux yoktur. Bu çekirdeğin sanal bellek birimi (MMU) de yoktur; genellikle yalnızca bir bellek koruma birimi (MPU) bulunur (genel bilgi). Ad alanları, cgroup'lar ve overlayfs gibi bu bölümün tüm mekanizmaları bir Linux çekirdeği gerektirir. Gömülü cihazda "dağıtım", derlenmiş bir ikilinin (genellikle bir `.bin` ya da `.hex` dosyası) flash belleğe yazılmasıdır ve güncelleme için havadan güncelleme (OTA) mekanizması gerekir (genel bilgi). Bu konuya Bölüm 43 (Bare-Metal C), Bölüm 44 (kesme ve zamanlayıcı) ve Bölüm 45 (UART, SPI, I2C) içinde iniyoruz.

Bir kenar (edge) cihazında ise durum farklıdır. NVIDIA Jetson gibi bir kart tam bir Linux çalıştırır ve GPU'ya sahiptir; burada konteyner kullanımı yaygındır, çünkü GPU sürücüsüne erişim için özel bir çalışma zamanı kullanılır (genel bilgi). Bu tür cihazlarda model çıkarımını dağıtmak, Bölüm 46 (Edge AI ve TinyML) ve Bölüm 75 (verimli çıkarım) konularının bir parçasıdır.

Hava boşluklu (air-gapped) ağlarda, yani internete hiç bağlanamayan ortamlarda dağıtım başka bir sorun çıkarır: imajlar bir kayıt defterinden çekilemez. Bunun yerine imaj bir arşiv olarak taşınır ve yerel bir kayıt defterine yüklenir (genel bilgi). Bu durumda 42.5'teki özet doğrulaması ve imza kontrolü, taşınan dosyanın değiştirilmediğinin tek kanıtıdır. Bölüm 38'de gördüğün git nesne deposu da aynı ilkeyle çalışır: içerik değişirse özet değişir.

Savunma sanayiinde ise asıl zorluk teknik olmaktan çok düzenleyicidir. Havacılık yazılımı için DO-178C gibi standartlar, yazılımın hangi yapılandırmayla üretildiğinin izlenebilir olmasını ister (genel bilgi). Bu nedenle bir temel imajı güncellemek, yalnızca bir paket değişikliği gibi görülemez: yeni bir ortam, yeni bir doğrulama turu anlamına gelebilir. Bu bölümün sürüm etiketi, özet ve tekrarlanabilir derleme fikirleri, bu izlenebilirlik gereksiniminin teknik karşılığıdır. Yapılandırma yönetimi süreçleri ve kapsama ölçümü (Bölüm 39'daki MC/DC) bu çerçevenin diğer yarısıdır.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, Bölüm 5'teki altı adımı izler. Her örnekte, önce soruyu anlarsın, sonra küçük bir durumla denersin, kaba bir çözüm bulur, örüntüyü çıkarır, iyileştirir ve elle iz sürerek doğrularsın. Son adım her zaman bir iz tablosudur.

### Örnek 1 (★): Talimat sırası ve önbellek izi

Bir C projesinde Dockerfile'ın iki farklı sıralamasını düşün. A'da kaynak kodu önce, bağımlılık kurulumu sonra kopyalanır. B'de bağımlılık listesi önce kopyalanır. Yalnızca `crc32_arac.c` değiştiğinde hangi talimatlar yeniden çalışır?

**Adım 1 — Anla.** Önbellek anahtarı talimat metninden, bir önceki katmandan ve `COPY` için dosya içeriğinden oluşur. Soru, değişikliğin hangi anahtarları geçersiz kılacağıdır.

**Adım 2 — Örnekle.** Yalnızca `crc32_arac.c` içeriği değişti. A'da `COPY . .` bu dosyayı kapsar; B'de `COPY . .` yine kapsar ama `COPY deps.txt .` kapsamaz.

**Adım 3 — Kaba çöz.** Her değişiklikte bütün talimatları baştan çalıştırmak, anahtarları hiç kontrol etmemek demektir. Bu güvenlidir ama her seferinde kurulum süresini öder.

**Adım 4 — Örüntü.** Anahtar zinciridir: bir talimat yeniden çalışınca altındakilerin hepsi de çalışır. Bu nedenle değişiklik, zincirde ne kadar yukarıda olduğuna göre maliyet üretir. Sık değişen dosyalar en sonda, seyrek değişenler en başta olmalıdır.

**Adım 5 — İyileştir.** B'deki sıralama, yalnızca bağımlılık listesinin değişmesi durumunda kurulumu yeniden çalıştırır. Kaynak değişikliğinde kurulum önbellekten gelir.

**Adım 6 — Doğrula.** Modelin çıktısını talimat talimat izleyelim:

| Talimat | A: kaynak değişti | B: kaynak değişti | Neden |
|---|---|---|---|
| `FROM gcc:13` | CACHED | CACHED | Değişiklik yok |
| `WORKDIR /src` | CACHED | CACHED | Değişiklik yok |
| `COPY . .` (A) / `COPY deps.txt .` (B) | REBUILT | CACHED | A tüm dosyaları kapsar, B yalnızca bağımlılığı |
| `RUN apt-get install` | REBUILT | CACHED | A'da üst katman değişti; B'de değişmedi |
| `COPY . .` (yalnız B) | — | REBUILT | Kaynak değişti |
| `RUN make` | REBUILT | REBUILT | Her iki durumda da kaynak değişti |

A'da üç talimat yeniden çalışır, B'de iki. Kurulum farkı, yani en pahalı adım, yalnızca A'da tekrarlanır. Bu ölçüm bir modelle yapıldığı için sonuç, kuralın doğruluğunu gösterir; gerçek Docker'daki süre farkını bu bölümde ölçmedik.

**Bunu AI'sız yazabilir misin?** Bir Python projesinde `requirements.txt` ile kaynak kodu arasında doğru kopyalama sırasını ve her iki durumda hangi katmanların önbellekten geleceğini, bir tablo yazarak açıkla.

### Örnek 2 (★★): Çok aşamalı derlemeyle boyut küçültme

Aynı CRC aracını iki biçimde paketleyeceğiz: tek aşamada gcc içeren bir imaj ve iki aşamalı, son imajı yalnızca statik ikiliyle taşıyan bir imaj. Hangi aşamanın ne kadar yer tuttuğunu ölçmek istiyoruz.

**Adım 1 — Anla.** İmaj boyutu, son katmanlardaki dosyaların toplamıdır. Derleyici ve başlık dosyaları son imajda gerekli değilse, onları bu katmanlardan ayırmak gerekir.

**Adım 2 — Örnekle.** Dinamik ikili `libc.so.6` ile çalışır, statik ikili bu kütüphaneyi içerir. İkisinin ikili boyutu ve bağımlılıkları farklıdır.

**Adım 3 — Kaba çöz.** Tek aşamada her şeyi bırakmak en basit yoldur: derleyici, kabuk ve kütüphanelerle birlikte imaj büyük olur.

**Adım 4 — Örüntü.** Derleme aşaması ile çalışma aşamasının bağımlılıkları ayrıdır. Çalışma aşaması yalnızca çalışma zamanı bağımlılıklarını taşımalıdır; statik bağlama bu bağımlılıkları sıfıra indirebilir.

**Adım 5 — İyileştir.** İki aşamalı Dockerfile'ı kullanıyoruz: derleme `gcc:13` imajında, çalışma `scratch` imajında. Son imajda yalnızca tek ikili var.

**Adım 6 — Doğrula.** Ölçülen değerleri ve doğrulama sonuçlarını tabloya döküyoruz:

| Aşama / ikili | İçerik | Ölçülen boyut | Doğrulama |
|---|---|---|---|
| 1. aşama (`gcc:13`) | gcc, başlıklar, kabuk | ölçülmedi (Docker yok) | — |
| Dinamik ikili | kod + `libc.so.6` bağımlılığı | 16 088 bayt | `ldd` libc ve yükleyiciyi listeledi |
| 2. aşama (`scratch`) için statik ikili | kod + gömülü libc | 785 496 bayt | Minik kök dizinde `cbf43926` üretti |

Statik ikili, 16 088 bayttan büyük ama bağımlılığı yok. Dinamik ikili daha küçük ama çalışmak için kütüphane gerektirir. Son imajın toplam boyutunu ölçemediğimiz için sonucu ikili boyutuyla sınırlıyoruz.

**Bunu AI'sız yazabilir misin?** Bir C programı için iki aşamalı bir Dockerfile yaz; ilk aşamada derle, ikinci aşamada yalnızca ikiliyi kopyala. İkinci aşamanın hangi kullanıcıyla çalışacağını ve neden sayısal bir kullanıcı kimliği gerektiğini açıkla.

### Örnek 3 (★★): Yuvarlanan dağıtımda kapasite ve sürüm karışımı

Dört kopyalık bir servisi yuvarlanan dağıtımla v1'den v2'ye geçiriyoruz. Kural: en fazla bir kopya kapatılabilir (`maxUnavailable = 1`), en fazla bir fazla kopya açılabilir (`maxSurge = 1`). Her tikte kaç kopya hizmet veriyor ve iki sürüm aynı anda ne kadar trafik alıyor?

**Adım 1 — Anla.** Kapasite, yalnızca hazır olan kopyalardan oluşur. Yeni kopya açılış süresi boyunca hazır değildir; eski kopya kapatılınca kapasite düşer.

**Adım 2 — Örnekle.** `N = 4`, `maxUnavailable = 1`. Bu, her an en az `N - 1 = 3` hazır kopya olması demektir.

**Adım 3 — Kaba çöz.** Tüm v1'leri silip v2'leri açmak en basit yoldur; ama bu süreçte hizmet yoktur (yeniden oluşturma stratejisi).

**Adım 4 — Örüntü.** Yuvarlanan dağıtımda her tikte iki şey kontrol edilir: yeni bir kopya açılabilir mi (toplam `N + maxSurge`'ü geçmemeli) ve bir eski kopya kapatılabilir mi (kalan hazır kopya sayısı `N - maxUnavailable` veya üzerinde kalmalı).

**Adım 5 — İyileştir.** Bu kontrolü bir döngüde yaparsak, her tikte ne olduğu izlenebilir. Model kodu bu iki kuralı doğrudan uygular.

**Adım 6 — Doğrula.** Modelin yuvarlanan izini elle izleyelim:

| Tik | v1 hizmet | v2 hizmet | Toplam pod | Hizmet toplamı | Sınır (en az 3) korundu mu? |
|---|---|---|---|---|---|
| 0 | 3 | 0 | 4 | 3 | evet |
| 1 | 3 | 0 | 5 | 3 | evet |
| 2 | 2 | 1 | 4 | 3 | evet |
| 3 | 1 | 2 | 4 | 3 | evet |
| 4 | 1 | 2 | 5 | 3 | evet |
| 5 | 0 | 3 | 4 | 3 | evet |

Tablodaki "hizmet toplamı" her tikte 3'tür, yani sınır tam olarak korunmuştur. Sürüm karışımı tik 2'den tik 4'e kadar sürer: bu sürede iki sürüm birlikte trafik alır. Bu karışım bir hata değil, yuvarlanan dağıtımın doğal sonucudur; bu yüzden v1 ve v2 arasındaki veri ve API uyumluluğu bu dönemde korunmalıdır.

**Bunu AI'sız yazabilir misin?** `N = 5`, `maxUnavailable = 0`, `maxSurge = 1` için yuvarlanan dağıtımın ilk üç tikini elle yaz. Her tikte hizmet toplamının asla 5'in altına düşmediğini göster.

### Örnek 4 (★★★): Uzlaştırma döngüsünün hata senaryosu boyunca izi

Üç kopyalık bir istenen durum var. Döngü, bir kopyanın sağlık denetimini geçememesini, istenen sayının artırılmasını ve bir kopyanın elle silinmesini izliyor. Her olayın döngü üzerindeki etkisini, eylemler dahil, izle.

**Adım 1 — Anla.** Döngü tek bir soruyu sorar: istenen ile gözlenen arasında fark var mı? Olayın nedenini bilmez; yalnızca durumdaki değişikliği görür.

**Adım 2 — Örnekle.** Sekiz tik var. 1. tikte ilk durum, 4. tikte `pod-2`'nin sağlıksızlığı, 6. tikte istenenin 5'e çıkması, 8. tikte `pod-4`'ün elle silinmesi.

**Adım 3 — Kaba çöz.** Her olay için hangi eylemin gerektiğini el ile hesaplamak mümkündür: sağlıksızı sil, eksikleri ekle, fazlayı sil. Bu, döngünün kendisinin yaptığı iştir.

**Adım 4 — Örüntü.** Döngü her turda aynı üç adımı uygular. Sonuç, olayların sırasından bağımsızdır: her tik yalnızca mevcut durumu görür. Bu, döngüyü dayanıklı kılan özelliktir.

**Adım 5 — İyileştir.** Döngünün ürettiği eylemleri izleyerek bir iz tablosu çıkarırsak, hata senaryosunun etkisi açıkça görünür.

**Adım 6 — Doğrula.** Modelin çıktısına göre iz tablosu:

| Tik | Olay | İstenen | Gözlenen (eylem öncesi) | Eylem | Gözlenen (sonra) |
|---|---|---|---|---|---|
| 1 | ilk durum | 3 | 0 | oluştur pod-1, pod-2, pod-3 | 3 |
| 2–3 | — | 3 | 3 | yok | 3 |
| 4 | pod-2 sağlıksız | 3 | 3 (biri sağlıksız) | sil pod-2, oluştur pod-4 | 3 |
| 5 | — | 3 | 3 | yok | 3 |
| 6 | istenen 3 → 5 | 5 | 3 | oluştur pod-5, pod-6 | 5 |
| 7 | — | 5 | 5 | yok | 5 |
| 8 | pod-4 elle silindi | 5 | 4 | oluştur pod-7 | 5 |

Dikkat edilecek iki nokta var. Birincisi, 4. tikte sağlıksız kopya silinmeden önce gözlenen sayı 3'tür; yani döngü "eksik" değil "bozuk" bir kopyayı yeniden üretir. İkincisi, 8. tikte elle silme yapıldığında döngü yalnızca eksik sayıyı tamamlar; hangi kopyanın silindiğini bilmek zorunda değildir.

Şimdi bir uyarı. Bu modelde tek bir döngü var. Gerçek bir sistemde iki denetleyici aynı anda 8. tiki görürse, ikisi de "eksik 1" sonucuna varıp `pod-7`'yi iki kez oluşturabilir ve toplam 6 kopya olur. Bunu önlemek için bir denetleyicinin "lider" seçilmesi, ya da oluşturma işlemlerinin benzersiz adlarla idempotent yapılması gerekir (genel bilgi). Bu konu, Bölüm 41'de dağıtık sistemlerde koordinasyon başlığında tekrar ele alınacak.

**Bunu AI'sız yazabilir misin?** Bu modelde 6. tikte istenen sayı 3'e geri indirilirse döngünün ne yapacağını iz tablosuyla göster. Hangi kopyaların silineceğini kodun hangi kuralla belirlediğini de açıkla.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı kullanma. Kodu, Dockerfile'ı ve betikleri kendi elinle yaz. Takıldığında yalnızca bu bölümdeki kavramlara ve kendi ölçümlerine dön; hazır bir çözüm arama. Projenin amacı teslimat hattının her parçasını bir kez kendin kurmaktır.
:::

### Proje 1 (★★★): Mini konteyner çalıştırıcı

**Amaç.** Bu bölümde kullanılan ad alanları ve kök dizin mekanizmasını birleştirip, bir programı kendi "konteyner"ında çalıştıran küçük bir araç yazmak. Araç root yetkisi gerektirmemeli; kullanıcı ad alanı ile çalışmalı.

**Beklenen davranış.** `./minikonteyner <kok_dizin> <komut> [argümanlar]` biçiminde çağrıldığında: yeni PID, UTS ve mount ad alanlarında çalışmalı; kök dizini verilen dizine çevirmeli; ad alanı içinde hostname'i ayrı bir değere ayarlamalı; komutu PID 1 olarak başlatmalı ve komutun çıkış kodunu döndürmeli. Dışarıdan bakıldığında kök dizindeki dosyalar dışında hiçbir şey görünmemeli.

**Önerilen yaklaşım (ipucu).** Ad alanlarını `clone(2)` ya da `unshare(2)` ile açmayı dene; `CLONE_NEWUSER` ile başla, çünkü diğer bayraklar onun izniyle çalışabilir. Kök dizini değiştirmek için `chroot` yeterli olabilir; `pivot_root` daha sağlamdır ama önce hangi dizinin bağlanacağını ve bağlama yayılımını (propagation) düşünmelisin. Bu bölümdeki deneyin bağlama ayarlarını hatırla: `mount --make-rprivate` gibi bir adım gerekebilir. `/proc`'u yeni PID ad alanında bağlamayı unutma; bu, `ps` çıktısının doğru olması için gerekir.

**Başarı kriterleri.**
- Konteyner içinde `echo $$` çıktısı 1'dir ve `ps` yalnızca konteynerin süreçlerini gösterir.
- Konteyner içinde değiştirilen hostname, ana makinede değişmez.
- Konteyner içinde ana makinenin `/home` dizini görünmez.
- Komut 30 saniye içinde bitmezse ve dışarıdan SIGTERM gelirse, PID 1 davranışını (işleyici olup olmadığını) gözlemleyip raporlayabilirsin.
- Çıkış kodu, komutun çıkış kodu ile aynıdır.

### Proje 2 (★★): Bölüm 40 API'si için teslimat hattı

**Amaç.** Bölüm 40'ta tasarlayacağın API'yi (ya da bu bölümdeki telemetri API'sini) bir teslimat hattından geçirmek: derleme, test, kapsama, imaj, sürüm etiketi ve mavi-yeşil geçiş.

**Beklenen davranış.** Üç bileşen olmalı. Birincisi, `ci.sh tum` betiği her adımı sırayla çalıştırır ve bir adım başarısız olursa durur. İkincisi, `mavi_yesil.sh` iki örnek başlatır (mavi ve yeşil, farklı portlarda), yeşil örneğin `/hazir` ucu 200 dönmeden trafiği değiştirmez; trafik değiştikten sonra mavi örneği kapatır. Üçüncüsü, bir `geri_al` komutu trafiği tek adımda önceki örneğe döndürür.

**Önerilen yaklaşım (ipucu).** Trafik yönlendirmesi için basit bir yapılandırma dosyası kullan: içinde tek bir satırda hangi portun aktif olduğu yazsın. Geçiş, bu dosyayı atomik olarak değiştirip bir ters vekil ya da yönlendirici yeniden yükleyerek yapılır; bu betikte bir `sed` ve yeniden başlatma yeterli olabilir. Yeşil örneğin sağlığını beklemek için `/hazir` ucuna belirli aralıklarla istek atan bir döngü yaz; zaman aşımı olursa geçişi iptal et.

**Başarı kriterleri.**
- Yeşil örnek hazır değilken trafik hiçbir zaman ona geçmez (kanıtı günlükten göster).
- Geri alma komutu, bir saniyenin altında trafiği eski örneğe döndürür.
- `ci.sh tum` yerelde yeşil çalışır ve sürüm etiketi `git describe` çıktısıyla eşleşir.
- Mavi-yeşil geçiş sırasında hiçbir istek hata dönmez; bu, `for` döngüsüyle geçiş sırasında sürekli istek atarak doğrulanır.

### Ek Alıştırmalar

**Zorluk etiketleri:** ★ kolay, ★★ orta, ★★★ zor. Mülakat etiketli sorular klasik mülakat problemleridir; önce cevabını yazmadan düşün, sonra bir deney ya da model ile sına.

1. **(★) Whiteout izi.** Alt katmanda `a.txt` ve `b.txt` olan bir overlayfs bağla. Üst katmanda `a.txt`'yi sil, `b.txt`'yi değiştir. Üst katmandaki her kaydın türünü ve nedenini yaz.
2. **(★) Üç bağımlılık.** Bir Dockerfile'da `COPY . .` ile `RUN make` arasına bir `RUN pip install` koyduğunda önbellek davranışı nasıl değişir? Önce elle tahmin et, sonra 42.6'daki modeli bu sıralamaya göre değiştirip sına.
3. **(★★) Mülakat: PID 1 ve docker stop.** Bir konteyner PID 1 olarak SIGTERM'i yok sayıyorsa `docker stop` ne yapar? Zaman aşımının rolünü ve SIGKILL'in neden her zaman işe yaradığını açıkla.
4. **(★★) Mülakat: bellek sınırı.** Bir sürecin cgroup `memory.max` sınırını aşması durumunda çekirdeğin ne yaptığını, sanal bellek ve sayfa hatası kavramlarını kullanarak açıkla (Bölüm 25 ve 42.3).
5. **(★) Ad alanı seçimi.** Bir konteynerin kendi ağ arayüzü olmazsa ne olur? Hangi uygulamalar bundan etkilenmez, hangileri etkilenir?
6. **(★★) Mülakat: tekrarlanabilir imaj.** Aynı kaynak ağacından iki farklı zamanda üretilen iki imajın özetleri farklı çıkıyor. Olası üç nedeni sırala ve her birini nasıl sabitleyeceğini yaz (42.5'teki tar normalleştirmesini kullan).
7. **(★★) .dockerignore olmadan.** `COPY . .` yaparken `.dockerignore` dosyası yoksa iki ayrı risk nedir? Biri güvenlik, biri önbellek ile ilgili olsun.
8. **(★★★) Mülakat: iki denetleyici.** Uzlaştırma döngüsünün iki kopyası aynı anda çalışırsa aynı eksik kopyayı iki kez oluşturabilir. Lider seçimi olmadan bu yarış koşulunu nasıl engelleyebilirsin? Çözümünü bir iz tablosuyla göster.
9. **(★★) Mavi-yeşilde şema.** Mavi ve yeşil örnekler aynı veritabanını kullanıyorsa, veri şeması değişikliğini hangi sırayla yapmalısın ki geri alma mümkün kalsın?
10. **(★★★) Mülakat: yuvarlanan dağıtımda sağlık.** Yeni sürümün hazırlık sondası bazen geçip bazen geçmiyorsa, yuvarlanan dağıtım hangi tikte durur ve neden? Eşik ve zaman aşımı değerlerinin rolünü tartış.
11. **(★) Statik bağlamanın bedeli.** Bir C kütüphanesinde güvenlik düzeltmesi çıktığında hangi ikililerin yeniden derlenmesi gerekir? Dinamik ve statik bağlamayı karşılaştır.
12. **(★★) Mülakat: root ve konteyner.** Konteyner içinde root olarak çalışan bir süreç, kullanıcı ad alanı ve `cap_drop` olmadan neden tehlikelidir? Bu bölümdeki compose ayarlarından hangisi bu riski azaltır?

## Kod Okuma Egzersizi

Bu egzersizde iki gerçek kaynak kesiti okuyacaksın. Birincisi Linux çekirdeği v6.6'nın `include/uapi/linux/sched.h` dosyasından, ad alanı bayraklarının tanımlarıdır (satır 20 ve 28–33). Kesitte yorumlar kaldırıldı ve tab karakterleri tek boşluğa çevrildi; değerler ve adlar birebir aynıdır.

```c
#define CLONE_NEWNS 0x00020000
#define CLONE_NEWCGROUP 0x02000000
#define CLONE_NEWUTS 0x04000000
#define CLONE_NEWIPC 0x08000000
#define CLONE_NEWUSER 0x10000000
#define CLONE_NEWPID 0x20000000
#define CLONE_NEWNET 0x40000000
```

İkinci kesit, Docker'ın varsayılan Linux yapılandırmasındaki ad alanı listesidir: `moby/moby` deposunun v26.1.0 etiketindeki `oci/defaults.go` dosyası, satır 125–131. Tab karakterleri dört boşluğa çevrildi; başka değişiklik yok.

```go
            Namespaces: []specs.LinuxNamespace{
                {Type: specs.MountNamespace},
                {Type: specs.NetworkNamespace},
                {Type: specs.UTSNamespace},
                {Type: specs.PIDNamespace},
                {Type: specs.IPCNamespace},
            },
```

**Sorular — cevaplamadan geçme:**

1. `CLONE_NEWNS` bayrağı için kaynakta "New mount namespace group" yazıyor. Bir mount ad alanı ile bir "mount namespace group" arasındaki farkı, Bölüm 26'daki bayrak mantığını hatırlayarak açıkla.
2. Sekiz ad alanı bayrağının tümü tek bit biçiminde tanımlı. Bu tasarımın bir clone çağrısında birden çok ad alanını birleştirmeye nasıl izin verdiğini açıkla.
3. Moby'nin varsayılan listesinde `CLONE_NEWUSER` (kullanıcı ad alanı) yok. Bu, varsayılan konteynerin root olarak çalıştığı anlamına mı gelir? Bu bölümdeki `unshare -r` deneyiyle karşılaştır.
4. Varsayılan listede cgroup ad alanı da yok. Bu bölümde `unshare -C` ile gördüğün `0::/` çıktısı, cgroup ad alanının ne işe yaradığını nasıl gösteriyor?
5. Bu listede zaman ad alanı (`CLONE_NEWTIME`) da yok; bu kesitte görünmüyor. Bunun nedenini, sched.h'daki `CLONE_NEWTIME`'ın değerinin diğerlerinden neden farklı bir bit konumunda olduğuna bakarak tahmin et ve kaynakta doğrula.
6. Kesitte `Namespaces` alanının yanında `Devices`, `Capabilities` gibi alanlar da olabilir. Bu kesit yalnızca ad alanlarını gösteriyor. Bir konteynerin "izole" sayılması için yalnızca ad alanlarının yeterli olmadığını, cgroup ve yetenek (capability) kısıtlarının da gerektiğini kendi cümlelerinle açıkla.

## Bölüm Özeti

Bu bölümde "bende çalışıyor" sorununun mühendislik karşılığını aradık ve bunu Linux'un altındaki mekanizmalardan başlayarak kurduk:

- **Ortam bir bağımlılıktır.** Sıralama, satır sonu ve çekirdek gibi görünmez ayrıntılar çıktıyı değiştirir. Tekrarlanabilirlik, ortamı tanımlamak, girdileri sabitlemek ve çıktıyı özetle işaretlemekle sağlanır.
- **Konteyner, çekirdeği paylaşan bir süreçtir.** Sanal makine çekirdeğini de taşır; konteyner taşımaz. Bu, hafifliğin ve Linux'a bağımlılığın iki yüzüdür.
- **Ad alanları neyin görüneceğini, cgroup'lar ne kadar kullanılacağını belirler.** Yazma yetkimiz olmadığı için cgroup sınırlarını yalnızca okuyabildik; bu sınırın etkisini bu makinede ölçemedik.
- **Overlayfs katmanları birleştirir.** Yazılar üst katmana gider, silmeler whiteout olarak kaydedilir ve alt katman değişmez. Bu yüzden silinen bir dosya imajda boyut olarak kalır.
- **İmaj, katmanlar ve özetlerdir.** Tar normalleştirilmediğinde aynı içerik farklı özet üretebilir. Dockerfile talimat sırası önbelleği belirler: sık değişen şeyler en sona konur.
- **Çok aşamalı derleme ve statik bağlama, imaj boyutunu ve yüzey alanını küçültür.** Statik ikili 785 496 bayt, dinamik ikili 16 088 bayttır; bedeli güvenlik güncellemelerinin yeniden derlenmesidir.
- **PID 1 bir sorumluluktur.** İşleyicisi olmayan bir init SIGTERM'i yok sayar; yetim zombileri toplamazsa süreç tablosu dolar. Uygulama ya işleyici kurar ya da bir init kullanılır.
- **Dağıtım stratejileri bir kesinti ve geri alma değiş tokuşudur.** Yuvarlanan, mavi-yeşil, kanarya ve özellik bayrakları farklı risklere karşılık gelir. Kapasite sınırını (yuvarlanan dağıtımda `N - maxUnavailable`) zaman modeliyle doğruladık.
- **Uzlaştırma döngüsü duruma tepki verir.** Olayın nedenini bilmeden, istenen ile gözlenen arasındaki farkı kapatır; yinelenen denetleyiciler ise yarış koşulu yaratabilir.

Kısım X (Yazılım Mühendisliği Pratiği) bu bölümle kapanıyor. Bölüm 38'de git ile sürüm geçmişini, Bölüm 39'da testi, Bölüm 40'ta API sözleşmesini, Bölüm 41'de sistem tasarımını ve bu bölümde dağıtımı gördün. Bu beş bölüm, bir kodun kaynak kontrolünden kullanıcıya ulaşana kadarki yolu tek bir hat olarak kurar.

**Sonraki bölümde:** Bölüm 43 — Bare-Metal C. Kısım XI (Gömülü Sistem) burada başlıyor. Bu bölümde konteynerin Linux çekirdeği gerektirdiğini gördük; gömülü dünyada ise işletim sistemi yoktur ve C programın doğrudan donanımla konuşur. Bölüm 43'te başlangıç kodunu, bellek haritasını ve kesme vektörlerini kendi elimizle kuracağız.

::: mulakat
Klasik sorular — hemen cevaplamaya çalışma, her birini birkaç dakika düşün:

1. Konteyner ile sanal makine arasındaki fark nedir? Bir konteynerin çekirdek açığından neden daha fazla etkilendiğini söyleyebilir misin?
2. Bir konteynerin içinde `ps` çalıştırdığında PID 1'i görüyorsan bu ne anlama gelir ve PID 1'in hangi sorumlulukları vardır?
3. Bir Dockerfile'da `COPY . .` talimatını `RUN pip install -r requirements.txt`'den önce koymak neden önbelleği bozar?
4. Bir imajdan bir dosyayı sonraki bir `RUN` ile silmek imaj boyutunu neden düşürmez?
5. Yuvarlanan dağıtımla mavi-yeşil dağıtım arasındaki fark, kesinti ve geri alma açısından nedir? Hangi durumda birini diğerine tercih edersin?
6. Liveness ve readiness sondaları neden ayrı tutulur? İkisini karıştırmanın somut bir sonucu ne olur?
7. Bir uzlaştırma döngüsü, neden kendisine verilen olayları değil, durumu izler? Bu tasarım hataya dayanıklılığa nasıl katkı sağlar?
8. Statik bağlamanın imaj boyutuna ve güvenlik güncellemelerine etkisi nedir? Bir savunma yazılımında bu kararı nasıl verirsin?
:::
