%% kisim_no: XVI
%% kisim_ad: ML Mühendisliği & Araştırma
%% bolum_no: 80
%% baslik: Bitirme: Uçtan Uca Sistem

## Giriş: Kitabın son bölümü, tek bir sistem

Bu kitapta 79 bölüm boyunca parça parça şeyler öğrendik. Veri yapıları, algoritmalar, işletim sistemi, ağ, gömülü yazılım, matematik ve makine öğrenmesi ayrı ayrı anlatıldı. Bu bölümde hepsini tek bir sistemde bir araya getireceğiz. Sistem, bir İHA'nın gözetleme videosundan hava hedeflerini bulacak, onları kareler boyunca izleyecek, sonucu bir operatöre iz listesi olarak sunacak ve kendi performansını izleyecek.

Savunma sanayiinde bu tür bir sistemin karşılığı durumsal farkındalık (situational awareness) adıyla bilinir. Gözetleme kamerası bir şey görür, bilgisayar görüşü bunu tespit eder, takip bunun aynı nesne olduğunu korur, operatör de kararını verir. Mülakatlarda bu zincirin her halkası ayrı bir soru olarak çıkar; projede ise bu halkaların birbirine nasıl bağlandığı asıl iştir.

Sistemin hiçbir parçası gerçek bir İHA verisiyle ölçülmedi. Veri sentetik, donanım bir dizüstü bilgisayarın işlemcisi ve bir GPU, edge cihazı ise yalnızca bir vekil (proxy). Bu sınırları bölüm boyunca açıkça yazacağız. Sayılara güvenmenin yolu, hangi koşulda ölçüldüklerini bilmekten geçer.

::: not
Bu bölümde gösterilen tüm sayılar, bölümün betikleriyle yeniden üretilebilir. Betikler sabit tohum kullanır, ama GPU eğitiminde bit düzeyinde tekrarlanabilirlik yoktur; aynı kodu iki kez çalıştırınca test mAP@0,5 değerleri yaklaşık ±0,003 oynar. Sayılar ilk bakışta kesin görünse de, her sayının yanında belirsizliği de okumak gerekir.
:::

## 80.1 Gereksinimler: önce ne yapacağımızı yazmak

Bir mühendislik projesi kod yazmadan önce ne yapması gerektiğini yazar. Bu adım sıkıcı görünür, ama sonradan "başarılı oldu mu?" sorusunun cevabı buna bağlıdır. "Hedefi iyi tespit etsin" gibi bir cümle ölçülemez; ölçülemeyen bir gereksinim de kabul edilemez. Bu yüzden gereksinimleri en baştan sayısal kabul ölçütlerine çevireceğiz.

Görev tanımı şöyle: sentetik bir İHA gözetleme videosunda hava hedeflerini (daire, kare, üçgen) algılamak, kareler boyunca her birine sabit bir kimlik vermek ve bunu operatöre iz listesi olarak sunmak. Sistem, kendi güvenilmez olduğu durumları da işaretlemeli. Son olarak, veri dağılımı değiştiğinde bunu fark edip yeniden eğitim gerektiğini bildirmeli.

Bu görevin kapsamı sınırlıdır ve bilinçli olarak sınırlanmıştır. Bu bölümün 67.20 bölümündeki savunma bağlamı notunu tekrar edelim: sistem **algılama, takip, operatöre bilgi ve güvence** için vardır. Hedef seçimi, silahlandırma ya da angajman kararı bu sistemin işi değildir ve bu bölümde bu tür kararları destekleyen hiçbir yöntem anlatılmaz. Operatör her zaman karar vericidir.

Çalışma varsayımlarımızı açıkça yazalım, çünkü sonraki her sayının anlamı bunlara bağlıdır:

- **Veri:** Gerçek İHA görüntüsü yok. Veri, 96 x 96 piksel gri tonlu sentetik sahnelerden oluşur. Bölüm 67'deki sahne üreticisi genişletilir.
- **Donanım:** Eğitim RTX 3060 (6 GB) üzerinde yapılır. Edge ölçümü, bir dizüstü bilgisayarın CPU'sunda ONNX Runtime ile yapılır ve bu bir vekildir. Cortex-M ve Jetson sınıfı donanım ölçülmedi.
- **Kare hızı:** Operatör akıcı bir görüntü istiyorsa saniyede 30 kare hedeflenir. Bu, kare başına en fazla 33 ms demektir.
- **Kapsam:** Tek bir kamera, tek bir İHA, gerçek zamanlı çevrim içi öğrenme yok.

Gereksinimleri iki gruba ayıralım. İşlevsel gereksinimler sistemin **ne** yaptığını, işlevsel olmayanlar **ne kadar iyi** yaptığını söyler.

| No | Tür | Gereksinim |
|---|---|---|
| F1 | İşlevsel | Her karede hedefleri üç sınıfta (daire, kare, üçgen) algıla |
| F2 | İşlevsel | Kareler boyunca her hedefe kararlı bir kimlik ver |
| F3 | İşlevsel | Operatöre iz listesi ver; güvenilmez tespitleri "doğrulat" diye işaretle |
| F4 | İşlevsel | Girdi ve performans kaymasını izle; alarm ver |
| F5 | İşlevsel | Yeniden eğitimi otomatik değil, insan onayıyla tetikle |
| N1 | Doğruluk | Nominal veride mAP@0,5 yüksek olsun |
| N2 | Doğruluk | Operasyonel kaymada da kullanılabilir kalsın |
| N3 | Takip | Test videolarında MOTA yüksek, kimlik değişimi düşük olsun |
| N4 | Gecikme | Kare başına süre bütçede kalsın |
| N5 | Bellek | Model ve ara tamponlar makul sınırda olsun |
| N6 | Güvenilirlik | Güvence katmanı kapsamayı çok bozmadan yanlış alarmı düşürsün |
| N7 | Tekrarlanabilirlik | Model dışa aktarımı PyTorch ile aynı kutuları üretsin |

Bu gereksinimlerin her birini ölçülebilir bir kabul ölçütüne çevirmek gerekir. Tablo, her birine bir eşik ve bir ölçüm yöntemi verir. Eşikleri bu bölümün ölçümlerine bakmadan önce koyduk; bölümün sonunda hangilerinin tutulduğunu ayrıca göstereceğiz.

| Kod | Ölçü | Eşik | Nerede ölçülür |
|---|---|---|---|
| R1 | mAP@0,5, nominal test (3 tohum ort.) | >= 0,90 | 80.4 |
| R2 | mAP@0,5, operasyonel kayma (3 tohum ort.) | >= 0,80 | 80.4 |
| R3 | MOTA, nominal test videoları | >= 0,90 | 80.5 |
| R4 | Kimlik değişimi (IDSW) / GT sayısı | <= %1 | 80.5 |
| R5 | int8 kuantizasyonunda mAP@0,5 kaybı | <= 2 puan | 80.6 |
| R6 | int8 kuantizasyonunda mAP@[0,5:0,95] kaybı | <= 5 puan | 80.6 |
| R7 | Uçtan uca kare süresi p95, 96 px, 4 iş parçacığı | <= 33 ms | 80.6 |
| R8 | 640 px girdide ağın çıkarım süresi p95 (4 iş parçacığı) | <= 33 ms | 80.6 |
| R9 | Model dosyası (int8) | <= 1 MB | 80.6 |
| R10 | En büyük ara tampon (int8, 96 px) | <= 256 KB | 80.6 |
| R11 | OOD'de görüntü başına yanlış alarm, korumasıza göre azalma | >= %50 | 80.7 |
| R12 | Test kapsaması, korumasıza göre kayıp | <= 5 puan | 80.7 |
| R13 | Kayma alarmı gecikmesi ve nominal pencerelerde alarm sayısı | <= 5 pencere, 0 alarm | 80.8 |
| R14 | PyTorch ile ONNX kutu farkı (maks) | <= 1e-4 | 80.6 |

R7 ve R8 aynı eşiği taşıyor ama farklı bir şeyi ölçüyor. R7 96 piksellik girdi için uçtan uca hattın süresidir; R8 ise 640 piksellik girdi için yalnızca ağın çıkarım süresidir. İkincisini ekledik çünkü 96 piksel bir oyuncak boyutudur. Gerçek bir İHA görüntüsünde 8 ile 24 piksellik hedefler, 96 pikselde bir karede birkaç pikselden ibaret olur. Çözünürlük ile gecikme arasındaki bu gerilim sistemin en önemli tasarım kararıdır ve 80.6'da geri döneceğiz.

## 80.2 Mimari: parçalar, sözleşmeler ve hatalar

Sistemi bir zincir olarak düşünmek kolaydır, ama gerçek sistemler zincir değil, birbirine veri gönderen kutulardan oluşur. Her kutunun girdisi ve çıktısı belli olmalıdır; bu belirleme **veri sözleşmesi** olarak adlandırılır. Sözleşme yazılmazsa, bir kutunun değişikliği diğerini sessizce bozar. Bölüm 46.7'deki uçta ön işleme ile Bölüm 77.8'deki eğitim ve servis çarpıklığı aynı sorunu anlatır: eğitimdeki ön işleme ile çıkarımdaki ön işleme farklıysa model hata vermeden kötüleşir.

Şekil 80.1, uçtan uca yaşam döngüsünü gösterir. Veri üretiminden başlayıp eğitime, değerlendirmeye, dışa aktarmaya ve edge hattına uzanır. Edge hattından gelen bilgi operatöre gider, izleme ise kayma olup olmadığına bakar ve gerekiyorsa yeniden eğitimi tetikler.

![Şekil 80.1: Uçtan uca yaşam döngüsü: veriden operatöre ve geri bildirime](gorseller/b80_mimari.png)

Edge hattının içi Şekil 80.2'de görünür. Her ok bir veri sözleşmesidir ve her sözleşmenin biçimi kutunun içine yazılmıştır. Bu şekil, sistemin en kritik yerini gösterir: kare, ön işlemeye girdiğinde uint8 ile gelir ve float32'ye dönüşürken aralığı [0, 1] olarak sabitlenir. Eğitimde de aynı dönüşüm kullanılır; bu tutarlılık sistem düzeyinde bir gereksinimdir.

![Şekil 80.2: Edge çıkarım hattı ve her aşamanın veri sözleşmesi](gorseller/b80_hat.png)

Sözleşmeleri tablo hâline de getirelim. Bu tablo, bir arayüz değiştiğinde hangi kutuların etkileneceğini gösterir.

| Arayüz | Veri | Biçim ve aralık | Sıklık |
|---|---|---|---|
| Sensör -> ön işleme | Kare | 96 x 96, uint8, 0..255 | 30 kare/s |
| Ön işleme -> dedektör | Tensör | (1, 1, 96, 96), float32, 0..1 | Kare başına |
| Dedektör -> son işleme | Ham çıktı | (1, 12, 12, 16), float32, sınırsız | Kare başına |
| Son işleme -> takipçi | Kutular | (N, 4) xyxy piksel, skor, sınıf | Kare başına |
| Takipçi -> güvence | İz listesi | (id, kutu) ve geçmiş isabet sayısı | Kare başına |
| Güvence -> operatör | Alarm | Kimlik, kutu, skor, "otomatik" veya "doğrulat" | Olay bazlı |
| Edge -> izleme | Özet | Pencere başına girdi istatistiği ve skor dağılımı | Pencere başına |
| İzleme -> eğitim | Tetik | Tarih, pencere aralığı, alarm türü, insan onayı | Olay bazlı |

Son satır bir insan onayı gerektirir. Bu tasarım kararı bilinçlidir: bir izleme alarmı bir modelin otomatik olarak yeniden eğitilip yayınlanması anlamına gelmez. Bölüm 77.11'de yeniden eğitim politikalarını tartıştık; burada politikayı basit tuttuk: iki ardışık alarm, bir insan onayı.

### Hata modları ve etkileri (FMEA)

Mühendislikte bir sistemin nasıl bozulacağını önceden yazmak, bozulduğunda şaşırmamanın yoludur. FMEA (Failure Mode and Effects Analysis), her hata modu için etkiyi, tespit yolunu ve önlemi bir tabloda toplar. Aşağıdaki tablo kısadır; amaç yöntemi göstermektir.

| Hata modu | Etki | Tespit | Önlem |
|---|---|---|---|
| Kamera kontrastı düşer (sis, yansıma) | Tespit kaçırır, mAP düşer | PSI ve KS alarmı (80.8) | Yeniden eğitim tetiği, insan onayı |
| Küçük hedefler kaçar | FN artar, MOTA düşer | MOTA ve FN takibi (80.5) | Çözünürlük seçimi (80.6) |
| Kuş veya gölge tespit edilir | Yanlış alarm (FP) | OOD testi, tohum uyumu (80.7) | Güvence: "doğrulat" işareti |
| İki hedef kesişir | Kimlik değişimi (IDSW) | Kimlik takibi (80.5) | Macar eşleştirme, kayıt |
| int8 modelde bozulma | Lokalizasyon hatası | PyTorch ile eşleşme testi (80.6) | Kabul kapısı (R5, R6) |
| Model dosyası bozulur veya yanlış sürüm yüklenir | Tahmin tamamen yanlış | SHA-256 kontrolü (77.4) | Kayıt defteri ve özet doğrulaması |
| Kare süresi bütçeyi aşar | Kare atlanır, takip kopar | Kare süresi p95 izleme (80.6) | Kare atlama politikası, model küçültme |
| Yanlış veriyle yeniden eğitim | Model kötüleşir | Kalite kapısı (77.7) | Eğitim öncesi veri doğrulama |

Tabloda bir eksik var: model dosyası ve veri kaynağının güvenliği. Bölüm 32'deki savunma odaklı güvenlik ilkeleri bu noktada devreye girer. Eğitilmiş bir modeli pickle ile yüklemek, güvenilmeyen bir kaynaktan gelen kodu çalıştırmak demektir. Bu yüzden model dosyalarını ONNX ya da state_dict olarak taşıyor ve yüklemeden önce özetini kontrol ediyoruz.

## 80.3 Veri: sentetik sahneden operasyonel akışa

Modelin ne öğrendiğini anlamak için önce ona ne gösterdiğimizi bilmeliyiz. Bu bölümde veri üreticisini Bölüm 67'deki sentetik sahne üreticisinden (67.10) yola çıkarak dört yönde genişlettik: aydınlatma, gürültü, bulanıklık ve ölçek. Ayrıca iki yeni küme ekledik. Birincisi operasyonel kaymayı temsil eder: sis ya da yansımayla parlayan bir arka plan, azalmış kontrast, artmış gürültü, hafif bulanıklık ve uzaklaşan hedefler. İkincisi OOD (out-of-distribution, dağılım dışı) kümesidir: eğitimde hiç görülmemiş, kuşa benzeyen yatay iki kanatlı şekiller içerir ve bunların etiketi yoktur.

Üreticinin ayarları üç sözlükte toplanır. Her sahne, parlaklık, gürültü ve ölçek değerlerini bu aralıklardan rastgele seçer. `EGITIM` eğitim ve nominal test için kullanılır; `DRIFT` operasyonel kaymayı; `DRIFT_AGIR` ise bilerek sert seçilmiş bir kontrol kümesini üretir. Sert kaymanın neden ayrıca tutulduğunu 80.4'te göreceğiz.

Kodun ilk parçası sabitleri ve ayarları verir. Bulanıklık (`bul`) bir olasılık ve sigma aralığıdır; ölçek (`olcek`) hedef boyutunu çarpar.

```python
# -*- coding: utf-8 -*-
# b80_veri.py: Bolum 67'nin sentetik sahne ureticisinin genisletilmis
# hali. Sekil maskeleri b67_veri._sekil'den gelir. Eklenenler: isik,
# gurultu, bulaniklik, olcek kaymasi, OOD (kus benzeri) nesneler ve
# video dizileri. Her sey tohumla tekrarlanabilir.
import numpy as np
from scipy.ndimage import gaussian_filter
from b67_veri import _sekil

# Ayar: her sahne icin bu araliklardan orneklenir.
# bul = (olasilik, sigma_alt, sigma_ust): bulaniklik ihtimali.
EGITIM = dict(
    bg=(0.15, 0.40),
    par=(0.55, 1.00),
    gur=(0.01, 0.06),
    bul=(0.4, 0.5, 1.0),
    olcek=(0.9, 1.1),
)
NOMINAL = EGITIM  # ayni dagilim, farkli tohum (sahne duzeyi)
# Operasyonel kayma: arka plan parlar (sis, yansima), kontrast biraz
# duser, gurultu artar, kamera hafif bulanir, hedefler uzaklasir.
DRIFT = dict(
    bg=(0.30, 0.45),
    par=(0.60, 0.90),
    gur=(0.04, 0.07),
    bul=(1.0, 0.8, 1.2),
    olcek=(0.80, 0.95),
)
# Sert kayma (kontrol): ayirt edilemez seviyeye iner.
DRIFT_AGIR = dict(
    bg=(0.40, 0.55),
    par=(0.45, 0.65),
    gur=(0.06, 0.09),
    bul=(1.0, 1.0, 1.4),
    olcek=(0.75, 0.90),
)
```

Kuşa benzeyen OOD şekli, iki yatay elipsin birleşimidir. Hedef sınıflarından (daire, kare, üçgen) farklı bir siluet vermek için seçildi. Şekil maskelerinin geri kalanı Bölüm 67'deki `_sekil` fonksiyonundan gelir; yeniden yazmak yerine kullandık.

```python
def kus_maske(s, cx, cy, xx, yy):
    """Kus benzeri OOD sekli: iki yatay elipsin birlesimi (kanat)."""
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    e1 = ((dx + 0.35 * s) / (0.42 * s)) ** 2 + (dy / (0.14 * s)) ** 2
    e2 = ((dx - 0.35 * s) / (0.42 * s)) ** 2 + (dy / (0.14 * s)) ** 2
    return (e1 <= 1) | (e2 <= 1)


def sahne(rng, ayar, boyut=96, nmin=0, nmax=5, kus=0):
    """Bir sahne. Donus: img (HxW float32), nesneler (etiketli)."""
    H = W = boyut
    o = boyut / 96.0
    yy, xx = np.mgrid[0:H, 0:W]
    bg = rng.uniform(*ayar["bg"])
    gur = rng.uniform(*ayar["gur"])
    n = int(rng.integers(nmin, nmax + 1))
    adaylar = []  # (sinif, maske, parlaklik, ood)
    for k in range(n + kus):
        ood = k >= n
        s = rng.uniform(8, 24) * o * rng.uniform(*ayar["olcek"])
        cx = rng.uniform(s / 2 + 1, W - s / 2 - 1)
        cy = rng.uniform(s / 2 + 1, H - s / 2 - 1)
        par = rng.uniform(*ayar["par"])
        if ood:
            adaylar.append(
                (-1, kus_maske(s, cx, cy, xx, yy), par, True)
            )
        else:
            sek = int(rng.integers(0, 3))
            adaylar.append(
                (sek, _sekil(sek, s, cx, cy, xx, yy), par, False)
            )
    img = np.full((H, W), bg)
    gorunur = np.full((H, W), -1, dtype=np.int64)
    for k, (sek, m, par, ood) in enumerate(adaylar):
        gorunur[m] = k  # sonra cizilen onceki nesneyi ortar
        img[m] = par
    p, lo, hi = ayar["bul"]
```

Sahne üretimi üç adımda ilerler: arka planı doldur, nesneleri katman sırasıyla çiz ve sonra gürültü ekle. Bir nesnenin etiket kutusu, yalnızca görünen piksellerinden hesaplanır; üst üste binen ve neredeyse tamamen kapanmış nesneler etiketlenmez. OOD nesneleri hiçbir zaman etiketlenmez. Bu kural, OOD'deki tespitlerin neden yanlış sayıldığını açıklar.

```python
    if rng.uniform() < p:
        img = gaussian_filter(img, rng.uniform(lo, hi))
    img = np.clip(img + gur * rng.standard_normal((H, W)), 0, 1)
    nesneler = []
    for k, (sek, m, par, ood) in enumerate(adaylar):
        if ood:
            continue  # OOD nesnesinin etiketi yok
        mk = gorunur == k
        alan = int(mk.sum())
        if alan < 15 * o * o:  # cok ortulu: kutu etiketi yok
            continue
        ys, xs = np.where(mk)
        box = [
            int(xs.min()),
            int(ys.min()),
            int(xs.max()) + 1,
            int(ys.max()) + 1,
        ]
        nesneler.append({"cls": sek, "box": box, "alan": alan})
    return img.astype(np.float32), nesneler


def veri_seti(n, seed, ayar=EGITIM, boyut=96, nmin=0, nmax=5, kus=0):
    """n sahneden X (n,1,H,W) ve etiket listesi uretir."""
    rng = np.random.default_rng(seed)
    X = np.zeros((n, 1, boyut, boyut), dtype=np.float32)
    Y = []
    for i in range(n):
        img, nes = sahne(rng, ayar, boyut, nmin, nmax, kus)
        X[i, 0] = img
        Y.append(nes)
    return X, Y
```

Video üretimi, takip için ayrı bir fonksiyondur. Dört nesne doğrusal hareket eder ve ikisi (0 ve 1) aynı bölgede kesişir; bu, kimlik değişimi riskinin en klasik durumudur (Bölüm 67.18). Beşinci nesne, kuş benzeri OOD hedeftir ve kareler boyunca yavaşça yatay gider.

```python
def video(seed, T=120, ayar=NOMINAL, kus=1):
    """Dort nesne + bir kus (OOD) hareket eder. Nesne 0 ve 1 ayni
    bolgede kesisir (kimlik degisimi riski). Her kare: goruntu, gt_id,
    gt (xyxy) ve sinif. Kus nesnesinin kimligi gt'ye girmez."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:96, 0:96]
    # x, y, vx, vy, boyut, sinif, parlaklik, t0, t1
    nes = [
        [12.0, 30.0, 1.0, 0.2, 14, 0, 0.90, 0, T],
        [84.0, 34.0, -1.0, 0.0, 14, 1, 0.80, 0, T],
        [48.0, 70.0, 0.0, -0.6, 12, 2, 0.85, 0, T],
        [20.0, 80.0, 1.2, -0.4, 10, 1, 0.75, 10, 90],
    ]
    for _ in range(kus):  # OOD: sinif -1, gt'ye girmez
        nes.append([0.0, 55.0, 1.4, 0.0, 16, -1, 0.70, 5, T])
    kareler = []
    for t in range(T):
        img = np.full((96, 96), rng.uniform(*ayar["bg"]))
        gt_id, gt, cls = [], [], []
        for k, d in enumerate(nes):
            x, y, vx, vy, s, sek, par, t0, t1 = d
            if not (t0 <= t < t1):
                continue
            x += vx
            y += vy
            d[0], d[1] = x, y
            d[2] += (
                0.01 * rng.standard_normal()
            )  # kucuk ivme gurultusu
            d[3] += 0.01 * rng.standard_normal()
            if sek < 0:
                m = kus_maske(s, x, y, xx, yy)
            else:
                m = _sekil(sek, s, x, y, xx, yy)
            img[m] = par
        p, lo, hi = ayar["bul"]
        if rng.uniform() < p:
            img = gaussian_filter(img, rng.uniform(lo, hi))
```

Kodun devamı, her karenin görüntüsünü ve gerçek kutularını üretir. Burada bir kural önemlidir: bir nesne karenin dışına çıkmışsa, görünür alanı yüzde 50'nin altına düştüğünde etiketlenmez. Bu kuralı sonradan ekledik; ilk sürümde kareden çıkmış nesneler de etiketleniyordu ve bu, aşağıda anlatacağımız bir ölçüm hatasına yol açtı.

```python
        img = np.clip(
            img + ayar["gur"][1] * rng.standard_normal((96, 96)), 0, 1
        ).astype(np.float32)
        for k, d in enumerate(nes):
            if d[5] < 0 or not (d[7] <= t < d[8]):
                continue
            x, y, s = d[0], d[1], d[4]
            kutu = [
                int(round(x - s / 2)),
                int(round(y - s / 2)),
                int(round(x + s / 2)),
                int(round(y + s / 2)),
            ]
            # gorunur alan >= %50 ise etiketlenir
            kirpik = [
                max(kutu[0], 0),
                max(kutu[1], 0),
                min(kutu[2], 96),
                min(kutu[3], 96),
            ]
            tam = (kutu[2] - kutu[0]) * (kutu[3] - kutu[1])
            gorunur_a = max(kirpik[2] - kirpik[0], 0) * max(
                kirpik[3] - kirpik[1], 0
            )
            if gorunur_a < 0.5 * tam:
                continue
            gt_id.append(k)
            gt.append(kirpik)
            cls.append(d[5])
        kareler.append(
            {"img": img, "gt_id": gt_id, "gt": gt, "cls": cls}
        )
    return kareler
```

Bu betiğin `__main__` bölümü, üreticinin çıktı istatistiklerini basar. Sınıf dağılımının dengeli olduğunu ve kayma kümesinin piksel ortalamasının nominalden belirgin biçimde yüksek olduğunu bu çıktıdan görürüz.

```python
if __name__ == "__main__":
    X, Y = veri_seti(200, seed=0)
    print(
        "sahne:",
        X.shape,
        "ort. nesne:",
        round(np.mean([len(y) for y in Y]), 2),
    )
    print(
        "sinif:",
        np.bincount([o["cls"] for y in Y for o in y]).tolist(),
    )
    X, Y = veri_seti(200, seed=888, ayar=DRIFT)
    print("drift ort. piksel:", round(float(X.mean()), 3))
    X, Y = veri_seti(200, seed=0)
    print("nominal ort. piksel:", round(float(X.mean()), 3))
```

```term
$ python b80_veri.py
sahne: (200, 1, 96, 96) ort. nesne: 2.68
sinif: [170, 191, 175]
drift ort. piksel: 0.391
nominal ort. piksel: 0.298
```

### Ayrım: sahne düzeyinde, tohumla

Bölüm 54'ün ve Bölüm 57'nin ilk kuralı, eğitim ve test verisinin birbirine karışmamasıdır. Burada her küme ayrı bir tohumdan üretildiği için sahneler bağımsızdır; bir sahne ya da video iki kümede birden yer almaz. Tablo, kümelerin nasıl kurulduğunu gösterir.

| Küme | Tohum | Boyut | Ayar | Kullanım |
|---|---|---|---|---|
| Eğitim | 0 | 3 000 sahne | EGITIM | Model eğitimi |
| Doğrulama | 5 | 300 sahne | EGITIM | Eşik ve takip modu seçimi |
| Test (nominal) | 777 | 500 sahne | NOMINAL | Son ölçüm (R1) |
| Operasyonel kayma | 888 | 500 sahne | DRIFT | R2 ve izleme |
| Sert kayma (kontrol) | 890 | 500 sahne | DRIFT_AGIR | Bilgi amaçlı |
| OOD | 999 | 500 sahne, +1 kuş | NOMINAL | Güvence (80.7) |
| Video doğrulama | 200 ... 204 | 5 video x 120 kare | NOMINAL | Takip modu seçimi |
| Video test | 300 ... 304 | 5 video x 120 kare | NOMINAL | Takip ölçümü |
| Video kayma | 400 ... 404 | 5 video x 120 kare | DRIFT | Takip ölçümü |

Dikkat edilecek nokta, nominal test kümesinin eğitim dağılımıyla aynı olmasıdır. Bu bilerek yapıldı: nominal test "içinde kalan" veriyi ölçer, kayma ise "dışında kalan" veriyi. Nominal test sayısı, eğitimdeki sahnelerin üreticisinin gerçek dağılımını temsil eder; bu bir sınırlılıktır ve 80.9'daki model kartında yazılıdır.

### Etiket hatası: ölçümü bozan şey modelin değil etiketin hatasıydı

İlk video ölçümümüzde doğrulama MOTA'sı 0,60 civarındaydı. Takip modeli kötü görünüyordu, bu yüzden takip parametrelerini ayarlamaya başlamıştık. Sonra kareden çıkmış nesnelerin hâlâ "gerçek" sayıldığını fark ettik. Bu nesneler karede piksel olarak yoktu, ama gerçek kutuları duruyordu. Dedektör bunları bulamıyordu ve her biri bir kaçırma (FN) olarak sayılıyordu.

Kural düzeltildikten sonra aynı model ve aynı takipçi için doğrulama MOTA'sı 0,60'tan 0,77'ye çıktı. Yani ölçümdeki sorunun büyük kısmı etiketteydi, modelde değil. Bu, değerlendirme hatalarının neden bu kadar sinsi olduğunu gösterir: sayı düşük çıktığında ilk şüphe modele gider, ama kendi ölçüm aracınızı da sorgulamalısınız. Bölüm 57'de tartıştığımız değerlendirme disiplini tam olarak bunu koruma amacı taşır.

Şekil 80.3, üç kümeden birer örnek gösterir. Üst satır nominal test, orta satır operasyonel kayma ve alt satır OOD'dir. Kayma satırında arka plan daha açık ve gürültü daha belirgindir; OOD satırındaki kuş benzeri şekiller etiketsizdir ve bir dedektör için tuzak oluşturur.

![Şekil 80.3: Üç kümeden örnek sahneler (yeşil kutu: etiketli nesne)](gorseller/b80_sahneler.png)

## 80.4 Model: eğitim, temel çizgi ve mAP

Dedektör olarak Bölüm 67.10'daki küçük tek aşamalı ağı (`MiniYolo`) yeniden kullanıyoruz. Ağ 96 x 96 girdiyi üç kez ikiye bölerek 12 x 12'lik bir ızgaraya indirir; her hücrede iki anchor ve üç sınıf için tahmin üretir (Bölüm 67.8 ve 67.9). Kayıp fonksiyonu üçe ayrılır: nesnellik (BCE, pozitiflere üç kat ağırlık), kutu (MSE) ve sınıf (çapraz entropi). Kutu ve sınıf kaybı yalnızca pozitif hücrelerde hesaplanır. Bu tasarımın gerekçesi Bölüm 67'de ayrıntılı olarak anlatıldı; burada yeniden türetmeyeceğiz.

Eğitim ayarları Bölüm 64'teki pratiklerle uyumludur: AdamW, en yüksek öğrenme oranı 2e-3, OneCycle takvimi, 60 epoch ve 64'lük yığın. Üç tohum (1, 2, 3) aynı veriyle eğitilir. Üç tohum, tek bir koşunun şansını değil, yöntemin tutarlılığını ölçer; sonuçları ortalama ± standart sapma olarak raporlarız (Bölüm 57).

Kodun ilk parçası, klasik temel çizgiyi tanımlar. Bu temel çizgi bir öğrenme yöntemi değil, bir kural setidir: sabit bir eşikle ikili görüntü üretir, bağlı bileşenleri bulur ve her bileşenin doluluk oranına bakarak sınıfını seçer. Dolu bir daire bbox alanının yaklaşık yüzde 78,5'ini, kare yüzde 100'ünü, üçgen yaklaşık yüzde 50'sini kaplar. Bu basit kural, veri kendi içinde ayırt edilebilir olduğunda ne kadar yol alabileceğimizi gösterir.

```python
# -*- coding: utf-8 -*-
# b80_egit.py: uc tohumlu MiniYolo egitimi (GPU), klasik taban ve
# test / operasyonel (drift) / OOD degerlendirmesi. Sayilar CSV'ye.
import os
import pickle
import time
import numpy as np
import torch
from scipy.ndimage import label, find_objects
from b80_veri import veri_seti, EGITIM, NOMINAL, DRIFT, DRIFT_AGIR
from b67_04_yolo_mini import (
    hedef_tensorleri,
    egit,
    tahmin,
    degerlendir,
)

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
TOHUMLAR = [1, 2, 3]
ESIK_KLASIK = 0.45  # sabit esik (elle secildi)
DOLULUK = {0: 0.785, 1: 1.0, 2: 0.5}  # daire, kare, ucgen
```

Kodun ikinci parçası bu temel çizgiyi tanımlar. Dikkat edilecek nokta, skorun bileşenin ortalama parlaklığı olmasıdır; bu, tespitleri mAP hesabında sıralayabilmek için gereklidir. Bir eşik değeri (0,45) elle seçilmiştir ve bu seçim doğrulama kümesine bakılarak değil, arka plan ve nesne parlaklıklarının ortasına bakılarak yapılmıştır. Kayma kümesinde bu eşik çöker; bunu aşağıda göreceğiz.

```python
def klasik(img):
    """Esikleme + bagli bilesenler. Sinif: kutu icindeki doluluk
    oranina gore en yakin sekil. Skor: bilesenin ort. parlakligi."""
    etk, _ = label(img > ESIK_KLASIK)
    kut, skor, cls = [], [], []
    for k, sl in enumerate(find_objects(etk), 1):
        maske = etk[sl] == k
        alan = int(maske.sum())
        if alan < 15:
            continue
        doluluk = alan / maske.size
        c = min(DOLULUK, key=lambda c: abs(doluluk - DOLULUK[c]))
        kut.append([sl[1].start, sl[0].start, sl[1].stop, sl[0].stop])
        skor.append(float(img[sl][maske].mean()))
        cls.append(c)
    return (
        np.array(kut, float).reshape(-1, 4),
        np.array(skor),
        np.array(cls, int),
    )
```

Ana fonksiyon beş kümeyi üretir (doğrulama, test, kayma, sert kayma, OOD), klasik temel çizgiyi her birinde değerlendirir, sonra üç tohumla eğitip her birini aynı kümelerde ölçer. Her koşunun süresi ve GPU adı yazılır; süre ölçümleri tek koşudur ve bir sistematik kıyas değildir. Eğitimden önce kartın boşta olduğu `nvidia-smi` ile doğrulandı (kullanım yüzde 0 ile 10 arasında).

```python
def main():
    print("GPU:", torch.cuda.get_device_name(0))
    Xtr, Ytr = veri_seti(3000, seed=0, ayar=EGITIM)
    kumeler = {
        "val": veri_seti(300, seed=5, ayar=EGITIM),
        "test": veri_seti(500, seed=777, ayar=NOMINAL),
        "drift": veri_seti(500, seed=888, ayar=DRIFT),
        "agir": veri_seti(500, seed=890, ayar=DRIFT_AGIR),
        "ood": veri_seti(500, seed=999, ayar=NOMINAL, kus=1),
    }
    satirlar = []  # (yontem, tohum, kume, m50, m)
    for ad, (X, Y) in kumeler.items():
        pred = [klasik(img) for img in X[:, 0]]
        m50, m5095 = degerlendir(pred, Y)
        satirlar.append(("klasik", 0, ad, m50, m5095))
        print(
            "klasik %-6s mAP@0.5=%.4f  mAP@[.5:.95]=%.4f"
            % (ad, m50, m5095)
        )
    ptr, otg, ctr = hedef_tensorleri(Ytr)
    tahminler = {}
    for seed in TOHUMLAR:
        t0 = time.time()
        model = egit(seed, Xtr, ptr, otg, ctr, epoch=60)
        sure = time.time() - t0
        torch.save(
            model.state_dict(),
            os.path.join(KLASOR, "yolo_t%d.pt" % seed),
        )
        for ad, (X, Y) in kumeler.items():
            pred = tahmin(model, X)
            tahminler[(seed, ad)] = pred
            m50, m5095 = degerlendir(pred, Y)
            satirlar.append(("cnn", seed, ad, m50, m5095))
            print(
                "tohum %d %-6s mAP@0.5=%.4f  mAP@[.5:.95]=%.4f"
                % (seed, ad, m50, m5095)
            )
```

Kodun son parçası, tahminleri ve ölçümleri diske yazar. Tahminleri pickle ile saklamamızın nedeni, sonraki betiklerin (güvence, izleme) aynı tahminleri yeniden hesaplamadan kullanabilmesidir.

```python
        print("tohum %d egitim suresi: %.0f s" % (seed, sure))
    with open(os.path.join(KLASOR, "tahminler.pkl"), "wb") as f:
        pickle.dump(tahminler, f)
    with open(
        os.path.join(VERI, "b80_detektor.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("yontem,tohum,kume,map50,map5095\n")
        for s in satirlar:
            f.write("%s,%d,%s,%.4f,%.4f\n" % s)
    print("\nOzet (cnn: 3 tohum ort. +- ss):")
    for ad in kumeler:
        a = np.array(
            [s[3] for s in satirlar if s[0] == "cnn" and s[2] == ad]
        )
        b = np.array(
            [s[4] for s in satirlar if s[0] == "cnn" and s[2] == ad]
        )
        print(
            "%-6s mAP@0.5 = %.4f +- %.4f | mAP@[.5:.95] = %.4f"
            % (ad, a.mean(), a.std(ddof=1), b.mean())
        )


if __name__ == "__main__":
    main()
```

```term
$ python b80_egit.py
GPU: NVIDIA GeForce RTX 3060 Laptop GPU
klasik val    mAP@0.5=0.5969  mAP@[.5:.95]=0.5103
klasik test   mAP@0.5=0.6005  mAP@[.5:.95]=0.5228
klasik drift  mAP@0.5=0.2016  mAP@[.5:.95]=0.0910
klasik agir   mAP@0.5=0.0039  mAP@[.5:.95]=0.0015
klasik ood    mAP@0.5=0.4428  mAP@[.5:.95]=0.3841
tohum 1 val    mAP@0.5=0.9286  mAP@[.5:.95]=0.6477
tohum 1 test   mAP@0.5=0.9390  mAP@[.5:.95]=0.6387
tohum 1 drift  mAP@0.5=0.8725  mAP@[.5:.95]=0.5474
tohum 1 agir   mAP@0.5=0.0710  mAP@[.5:.95]=0.0324
tohum 1 ood    mAP@0.5=0.8952  mAP@[.5:.95]=0.6053
tohum 1 egitim suresi: 20 s
tohum 2 val    mAP@0.5=0.9392  mAP@[.5:.95]=0.6386
tohum 2 test   mAP@0.5=0.9407  mAP@[.5:.95]=0.6400
tohum 2 drift  mAP@0.5=0.8820  mAP@[.5:.95]=0.5462
tohum 2 agir   mAP@0.5=0.0708  mAP@[.5:.95]=0.0310
tohum 2 ood    mAP@0.5=0.8662  mAP@[.5:.95]=0.5917
tohum 2 egitim suresi: 20 s
tohum 3 val    mAP@0.5=0.9404  mAP@[.5:.95]=0.6340
tohum 3 test   mAP@0.5=0.9325  mAP@[.5:.95]=0.6366
tohum 3 drift  mAP@0.5=0.8699  mAP@[.5:.95]=0.5367
tohum 3 agir   mAP@0.5=0.0585  mAP@[.5:.95]=0.0271
tohum 3 ood    mAP@0.5=0.8869  mAP@[.5:.95]=0.6002
tohum 3 egitim suresi: 20 s

Ozet (cnn: 3 tohum ort. +- ss):
val    mAP@0.5 = 0.9361 +- 0.0065 | mAP@[.5:.95] = 0.6401
test   mAP@0.5 = 0.9374 +- 0.0043 | mAP@[.5:.95] = 0.6384
drift  mAP@0.5 = 0.8748 +- 0.0064 | mAP@[.5:.95] = 0.5434
agir   mAP@0.5 = 0.0668 +- 0.0072 | mAP@[.5:.95] = 0.0302
ood    mAP@0.5 = 0.8828 +- 0.0150 | mAP@[.5:.95] = 0.5991
```

### Sonuçlar

Tablo, iki yöntemin beş kümedeki mAP@0,5 ve mAP@[0,5:0,95] değerlerini verir. CNN satırı üç tohumun ortalamasıdır.

| Küme | Klasik mAP@0,5 | CNN mAP@0,5 | Klasik mAP@[0,5:0,95] | CNN mAP@[0,5:0,95] |
|---|---|---|---|---|
| Doğrulama | 0,597 | 0,936 ± 0,007 | 0,510 | 0,640 |
| Test (nominal) | 0,601 | 0,937 ± 0,004 | 0,523 | 0,638 |
| Operasyonel kayma | 0,202 | 0,875 ± 0,006 | 0,091 | 0,543 |
| Sert kayma (kontrol) | 0,004 | 0,067 ± 0,007 | 0,002 | 0,030 |
| OOD (kuş eklenmiş) | 0,443 | 0,883 ± 0,015 | 0,384 | 0,599 |

Birinci satır şunu söyler: doğrulama ve test değerleri birbirine çok yakın. Eşikleri ve takip modunu doğrulama kümesinde seçtiğimiz için, test kümesindeki bu yakınlık bir aşırı uyum (overfitting) göstergesi değildir. R1 (nominal mAP@0,5 >= 0,90) geçildi: 0,937 ± 0,004.

Operasyonel kaymada klasik temel çizgi 0,20'ye düşer, CNN ise 0,87'de kalır. Kayma, arka plan parlaklığını yükseltir ve kontrastı düşürür; sabit bir eşik bu durumda bir nesneyi arka plandan ayıramaz. CNN'in bunu öğrenmesinin nedeni, eğitimde aynı genişlikte bir aydınlatma çeşitliliği görmesidir. Bu bir avantajdır, ama bir uyarı da içerir: model, eğitimde gördüğü aralığın dışında ne kadar güvenilir kalır? Sert kayma kontrolü bu soruyu cevaplar. Her iki yöntem de 0,07'nin altına düşer. Yani eğitim dağılımının çok dışına çıkıldığında model sessizce bozulur. Bu nedenle R2'yi (operasyonel kayma >= 0,80) geçmek yeterli değildir; izleme ve güvence katmanına ihtiyacımız vardır (80.7 ve 80.8).

OOD satırı, kuş benzeri şekillerin dedektörü ne kadar yanılttığını gösterir. OOD kümesinde mAP 0,883'e düşer, çünkü kuşlar yanlış alarm (FP) olarak sayılır. Bu düşüş, güvence katmanının neden gerektiğinin en açık kanıtıdır.

Ölçümlerin belirsizliğine dair bir not. Aynı kodla yapılan iki eğitim koşusunda test mAP@0,5 ortalaması 0,9357 ve 0,9374 çıktı. Fark, GPU'nun bit düzeyinde tekrarlanabilir olmamasından kaynaklanır (cuDNN çekirdekleri her koşuda farklı sırayla toplama yapabilir). Bu nedenle sonuçlar arasındaki yaklaşık ±0,003 fark bilgi taşımaz; bu bölümdeki karşılaştırmaların hepsi bu gürültünün çok üzerindedir.

Son olarak deneyin kaydı. Bölüm 77.5'teki SQLite deney takipçisi, her tohumun parametrelerini, metriklerini ve model dosyasının özetini tutar. Bu kayıt betiğini 80.9'da çalıştıracağız; şimdi, şekli üreten veri hazırlık betiğine bakalım.

```python
# -*- coding: utf-8 -*-
# b80_ornek.py: sekiller icin ornek sahneleri ve seed-1 tespitlerini
# engine/veri/b80_ornek_sahne.npz dosyasina yazar (deterministik).
import os
import pickle
import numpy as np
from b80_veri import veri_seti, NOMINAL, DRIFT
from b67_01_iou_nms import iou_matris

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def paketle(X, Y, pred, n=3):
    """n goruntu: goruntu, gt kutu (-1 dolgu), tespit (skor>=0.3)."""
    img = X[:n, 0]
    gt = -np.ones((n, 8, 4))
    gcls = -np.ones((n, 8), int)
    dk = -np.ones((n, 8, 4))
    dsk = -np.ones((n, 8))
    dcl = -np.ones((n, 8), int)
    for i in range(n):
        for j, o in enumerate(Y[i][:8]):
            gt[i, j] = o["box"]
            gcls[i, j] = o["cls"]
        kut, skor, cls = pred[i]
        m = np.where(skor >= 0.3)[0][:8]
        dk[i, : len(m)] = kut[m]
        dsk[i, : len(m)] = skor[m]
        dcl[i, : len(m)] = cls[m]
    return img, gt, gcls, dk, dsk, dcl
```

Bu betik, şekil için üç kümeden üç örnek sahne ve seed-1 modelinin tespitlerini tek bir dosyaya yazar. Dosya, çizim betiğinin Temp klasörüne bağımlı olmadan çalışmasını sağlar.

```python
def main():
    tah = pickle.load(
        open(os.path.join(KLASOR, "tahminler.pkl"), "rb")
    )
    cikti = {}
    for ad, seed_k, ayar_kus in [
        ("test", 777, 0),
        ("drift", 888, 0),
        ("ood", 999, 1),
    ]:
        X, Y = veri_seti(
            500,
            seed=seed_k,
            ayar=DRIFT if ad == "drift" else NOMINAL,
            kus=ayar_kus,
        )
        img, gt, gc, dk, dsk, dcl = paketle(X, Y, tah[(1, ad)])
        cikti[ad + "_img"] = img
        cikti[ad + "_gt"] = gt
        cikti[ad + "_gc"] = gc
        cikti[ad + "_dk"] = dk
        cikti[ad + "_dsk"] = dsk
        cikti[ad + "_dc"] = dcl
    np.savez_compressed(
        os.path.join(VERI, "b80_ornek_sahne.npz"), **cikti
    )
    print("yazildi: b80_ornek_sahne.npz (%d dizi)" % len(cikti))


if __name__ == "__main__":
    main()
```

```term
$ python b80_ornek.py
yazildi: b80_ornek_sahne.npz (18 dizi)
```

Şekil 80.4, bu örnekleri gösterir. Kırmızı kutular modelin tespitleri (skor en az 0,30), kesikli yeşil kutular gerçek kutulardır. Nominal sahnelerde kutular gerçeğe çok yakındır. Kayma satırında bazı nesneler kaçırılır ve bir tanesinde skor düşüktür. OOD satırında kuş, bir ya da iki kırmızı kutuyla yanlış alarm üretir.

![Şekil 80.4: Tespit sonuçları: nominal, kayma ve OOD (kırmızı: tespit, kesikli yeşil: gerçek)](gorseller/b80_tespit.png)

## 80.5 Takip: her karede aynı nesneyi bulmak

Dedektör her karede bağımsız çalışır. Bir karedeki üçgen ile bir sonraki karedeki üçgenin aynı nesne olduğunu bilmez. Takip (tracking) bu bağlantıyı kurar. Bölüm 67.15'te gördüğümüz tespit-ile-takip yaklaşımında üç parça vardır: her iz için bir durum (Kalman filtresi, Bölüm 62.6), bir hareket tahmini, ve tahminlerle yeni tespitlerin eşleştirilmesi (veri ilişkilendirme, Bölüm 67.16).

Bu bölümde iz durumu altı boyutludur: merkez (cx, cy), genişlik ve yükseklik (w, h) ile merkezin hızı (vx, vy). Tahmin adımı merkezi hızla ilerletir; güncelleme adımı tespit kutusuyla durumu düzeltir. Eşleştirmede maliyet, izin tahmini kutusu ile tespit kutusu arasındaki IoU'dur; eşleşme için en düşük IoU 0,3'tür. Bir iz en az üç karede isabet almadan onaylanmaz (min_hits) ve on kareden uzun süre eşleşmeden kalırsa silinir (max_age).

Bu parametreleri ve eşleştirme yöntemini Bölüm 67'deki `Izleyici` sınıfından alıyoruz. Dört mod vardır: `acgozlu_iou` her adımda en yüksek IoU'lu çifti seçer (açgözlü), `macar_iou` tüm maliyet matrisi için Macar algoritmasını çalıştırır (bu, SORT'un eşleştirmesidir), `macar_tum` skor eşiği olmadan tüm tespitleri iz başlatmaya açar, `byte` ise iki aşamalıdır: önce yüksek skorlu tespitler, sonra kalan izler için düşük skorlu tespitler (Bölüm 67.16'daki ByteTrack fikri).

Sistemin takip performansı için MOTA (Multiple Object Tracking Accuracy) kullanıyoruz (Bölüm 67.17):

MOTA = 1 - (FN + FP + IDSW) / GT

Bu formüldeki her terimin bir anlamı var: FN bir kaçırmadır, FP bir yanlış iz, IDSW bir kimlik değişimi, GT ise gerçek nesne-kare sayısıdır. Test videosunda macar_iou ve kare dışı filtresi için sayılar şunlardır: FN = 94, FP = 205, IDSW = 24 ve GT = 1 735. MOTA = 1 - (94 + 205 + 24) / 1 735 = 1 - 0,186 = 0,814. Bu, tablodaki 0,8138 ile uyumludur. Elle hesabı yapmadan bir MOTA değerine güvenmeyin; bu formülü bir kez elle sürmek, neyin neyi düşürdüğünü görmenin en hızlı yoludur.

Takip kodu şu şekilde yazılmıştır. Önce izleyiciyi ve iz çıktısını üreten `takip` fonksiyonunu görürüz; `cerceve` parametresi, kare dışına çıkmış izleri çıktıdan gizler (iz kendisi silinmez, yalnızca çıktı kesilir).

```python
# -*- coding: utf-8 -*-
# b80_takip.py: tespit-ile-takip. CNN tespitleri (tohum 1) ve Bolum
# 67'nin izleyicileri. Takip modu SECIMI yalnizca dogrulama
# videolarinda yapilir; test ve operasyonel videolar sonra okunur.
import csv
import os
import numpy as np
import torch
from b80_veri import video, NOMINAL, DRIFT
from b67_04_yolo_mini import MiniYolo, tahmin
from b67_08_takip import Izleyici, mota

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
MODLAR = ["acgozlu_iou", "macar_iou", "macar_tum", "byte"]


def model_yukle(seed):
    m = MiniYolo().to("cuda")
    m.load_state_dict(
        torch.load(os.path.join(KLASOR, "yolo_t%d.pt" % seed))
    )
    return m.eval()


def video_tespitleri(model, kareler):
    X = np.stack([k["img"] for k in kareler])[:, None]
    return tahmin(model, X)
```

Kodun ikinci parçası, tahmin ve sonuç toplamasını yapar. Her video için MOTA'yı hesaplayıp birleştiriyoruz; böylece tek bir uzun video yerine beş kısa videonun toplamı üzerinden ölçüm yapmış oluyoruz.

```python
def takip(mod, tespitler, cerceve=False):
    """cerceve=True: merkezi kare disina cikmis izler ciktiya girmez.
    Kaybolan nesnenin izi max_age karesi boyunca yasar; bu filtre
    o artik izleri susturur (iz silinmez, yalnizca cikti kesilir)."""
    izleyici = Izleyici(mod)
    cikti = []
    for kut, skor, _ in tespitler:
        iz = izleyici.guncelle(kut, skor)
        if cerceve:
            iz = [
                (i, b)
                for i, b in iz
                if 0 <= (b[0] + b[2]) / 2 <= 96
                and 0 <= (b[1] + b[3]) / 2 <= 96
            ]
        cikti.append(iz)
    return cikti
```

```python
def degerlendir(model, videolar, mod, cerceve=False):
    """Videolar uzerinde toplam MOTA, FN, FP, IDSW (birlesik)."""
    fn = fp = idsw = 0
    mt = []
    toplam = 0
    for kareler in videolar:
        tes = video_tespitleri(model, kareler)
        m, f_n, f_p, ids, _ = mota(takip(mod, tes, cerceve), kareler)
        mt.append(m)
        fn += f_n
        fp += f_p
        idsw += ids
        toplam += sum(len(k["gt"]) for k in kareler)
    return {
        "mota": 1 - (fn + fp + idsw) / toplam,
        "fn": fn,
        "fp": fp,
        "idsw": idsw,
        "gt": toplam,
    }


def videolar(baslangic, sayi, ayar, kus=1):
    return [
        video(s, ayar=ayar, kus=kus)
        for s in range(baslangic, baslangic + sayi)
    ]
```

Ana fonksiyon önce doğrulama videolarında her mod ve her çerçeve seçeneği için ölçüm yapar. Seçim yalnızca doğrulama MOTA'sına göre yapılır; test ve kayma videoları seçimden sonra okunur. Bu kural bir ayarı test kümesine göre seçmemizi engeller, bu da Bölüm 57'deki kötü uygulamanın en yaygın biçimidir.

```python
def main():
    model = model_yukle(1)
    dog = videolar(200, 5, NOMINAL)  # dogrulama
    test = videolar(300, 5, NOMINAL)  # test
    drift = videolar(400, 5, DRIFT)  # operasyonel
    satirlar = []
    for cer in (False, True):
        for mod in MODLAR:
            r = degerlendir(model, dog, mod, cer)
            satirlar.append(("dogrulama", mod, cer, r))
            print(
                "dogrulama cerceve=%d %-12s MOTA=%.4f FN=%d FP=%d "
                "IDSW=%d"
                % (cer, mod, r["mota"], r["fn"], r["fp"], r["idsw"])
            )
    # secim yalnizca dogrulama MOTA'sina gore (test'e bakilmadan)
    en = max(satirlar, key=lambda s: s[3]["mota"])
    secilen, cer_sec = en[1], en[2]
    print(
        "secilen (yalnizca dogrulama): mod=%s cerceve=%d"
        % (secilen, cer_sec)
    )
    sonuc = []
    for ad, kume in [("test", test), ("drift", drift)]:
        for cer in (False, True):
            for mod in MODLAR:
                r = degerlendir(model, kume, mod, cer)
                sonuc.append((ad, mod, cer, r))
                print(
                    "%-6s cer=%d %-12s MOTA=%.4f FN=%d FP=%d "
                    "IDSW=%d (GT=%d)"
                    % (
                        ad,
                        cer,
                        mod,
                        r["mota"],
                        r["fn"],
                        r["fp"],
```

```python
                        r["idsw"],
                        r["gt"],
                    )
                )
    nl = chr(10)
    with open(
        os.path.join(VERI, "b80_takip.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("kume,mod,cerceve,mota,fn,fp,idsw,gt" + nl)
        for ad, mod, cer, r in satirlar + sonuc:
            f.write(
                "%s,%s,%d,%.4f,%d,%d,%d,%d"
                % (
                    ad,
                    mod,
                    cer,
                    r["mota"],
                    r["fn"],
                    r["fp"],
                    r["idsw"],
                    r["gt"],
                )
                + nl
            )
    # Sekil icin: test videosu 0, secilen yapilandirmayla yorunge
    kareler = test[0]
    tes = video_tespitleri(model, kareler)
    iz = takip(secilen, tes, cer_sec)
    with open(
        os.path.join(VERI, "b80_takip_iz.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("kare,tip,id,x1,y1,x2,y2" + nl)
        for t, k in enumerate(kareler):
            for g, b in zip(k["gt_id"], k["gt"]):
                f.write("%d,gt,%d,%d,%d,%d,%d" % (t, g, *b) + nl)
            for tid, b in iz[t]:
                f.write(
                    "%d,iz,%d,%.1f,%.1f,%.1f,%.1f" % (t, tid, *b) + nl
```

Son parça, secilen yapılandırmayla test videosu 0'ın iz çıktısını bir CSV'ye yazar; şekil 80.5 bu dosyadan çizilir.

```python
                )


if __name__ == "__main__":
    main()
```

```term
$ python b80_takip.py
dogrulama cerceve=0 acgozlu_iou  MOTA=0.7549 FN=94 FP=309 IDSW=19
dogrulama cerceve=0 macar_iou    MOTA=0.7561 FN=90 FP=310 IDSW=20
dogrulama cerceve=0 macar_tum    MOTA=0.1190 FN=71 FP=1367 IDSW=79
dogrulama cerceve=0 byte         MOTA=0.6086 FN=68 FP=578 IDSW=28
dogrulama cerceve=1 acgozlu_iou  MOTA=0.7909 FN=94 FP=247 IDSW=19
dogrulama cerceve=1 macar_iou    MOTA=0.7921 FN=90 FP=248 IDSW=20
dogrulama cerceve=1 macar_tum    MOTA=0.1794 FN=71 FP=1263 IDSW=79
dogrulama cerceve=1 byte         MOTA=0.6400 FN=68 FP=524 IDSW=28
secilen (yalnizca dogrulama): mod=macar_iou cerceve=1
test   cer=0 acgozlu_iou  MOTA=0.7700 FN=91 FP=283 IDSW=25 (GT=1735)
test   cer=0 macar_iou    MOTA=0.7712 FN=94 FP=279 IDSW=24 (GT=1735)
test   cer=0 macar_tum    MOTA=0.2617 FN=68 FP=1151 IDSW=62 (GT=1735)
test   cer=0 byte         MOTA=0.6012 FN=69 FP=593 IDSW=30 (GT=1735)
test   cer=1 acgozlu_iou  MOTA=0.8127 FN=91 FP=209 IDSW=25 (GT=1735)
test   cer=1 macar_iou    MOTA=0.8138 FN=94 FP=205 IDSW=24 (GT=1735)
test   cer=1 macar_tum    MOTA=0.3372 FN=68 FP=1020 IDSW=62 (GT=1735)
test   cer=1 byte         MOTA=0.6553 FN=69 FP=499 IDSW=30 (GT=1735)
drift  cer=0 acgozlu_iou  MOTA=0.6875 FN=149 FP=384 IDSW=26 (GT=1789)
drift  cer=0 macar_iou    MOTA=0.7043 FN=139 FP=366 IDSW=24 (GT=1789)
drift  cer=0 macar_tum    MOTA=-0.4980 FN=90 FP=2415 IDSW=175 (GT=1789)
drift  cer=0 byte         MOTA=0.3220 FN=104 FP=1023 IDSW=86 (GT=1789)
drift  cer=1 acgozlu_iou  MOTA=0.7132 FN=149 FP=338 IDSW=26 (GT=1789)
drift  cer=1 macar_iou    MOTA=0.7255 FN=139 FP=328 IDSW=24 (GT=1789)
drift  cer=1 macar_tum    MOTA=-0.4354 FN=90 FP=2303 IDSW=175 (GT=1789)
drift  cer=1 byte         MOTA=0.3488 FN=104 FP=975 IDSW=86 (GT=1789)
```

### Ne ölçüldü, ne seçildi

Doğrulama tablosu, dört modun iki çerçeve seçeneğiyle ne yaptığını gösterir. MOTA, FN ve IDSW, doğrulama videolarında (1 722 GT) ölçülmüştür.

| Mod | Çerçeve filtresi kapalı | Çerçeve filtresi açık | FP (açık) | IDSW (açık) |
|---|---|---|---|---|
| acgozlu_iou | 0,755 | 0,791 | 247 | 19 |
| macar_iou (seçilen) | 0,756 | 0,792 | 248 | 20 |
| macar_tum | 0,119 | 0,179 | 1 263 | 79 |
| byte | 0,609 | 0,640 | 524 | 28 |

İki sonuç hemen görülüyor. Birincisi, kare dışı filtresi her modda MOTA'yı yaklaşık 0,035 artırıyor. Bunun sebebi, kaybolan nesnenin izinin max_age süresince kalması ve bu süre boyunca tahmin kutusunun FP üretmesidir. Filtre bu hayalet izleri susturur. İkincisi, macar_tum felaketidir: skor eşiği olmadan her zayıf tespit yeni iz açar ve FP patlar. Bu, "daha fazla tespit daha iyi takip demektir" yanılgısının bedelidir.

Seçilen mod, macar_iou ile açgözlü eşleştirme arasındaki farkın yalnızca 0,001 olduğu bir yarışta kazandı. Bu fark gürültü düzeyindedir. Yine de SORT'u seçmek savunulabilir, çünkü Macar eşleştirmesi bir kez anlaşıldığında açgözlü olandan daha az sürprizlidir: her zaman küresel olarak en iyi toplamı verir. Karar, seçilen ilk kuralın sade olmasına dayanır; sonuçların bu kadar yakın olduğunu da bilerek.

Test ve kayma sonuçları aşağıdadır. Seçilen mod macar_iou ve çerçeve filtresi açıktır.

| Küme | Mod | MOTA | FN | FP | IDSW | GT |
|---|---|---|---|---|---|---|
| Test (nominal) | macar_iou (seçilen) | 0,814 | 94 | 205 | 24 | 1 735 |
| Test (nominal) | acgozlu_iou | 0,813 | 91 | 209 | 25 | 1 735 |
| Operasyonel kayma | macar_iou (seçilen) | 0,726 | 139 | 328 | 24 | 1 789 |
| Operasyonel kayma | byte | 0,349 | 104 | 975 | 86 | 1 789 |

R3 (test MOTA >= 0,90) geçilemedi: 0,814. R4 (IDSW <= %1 GT) da geçilemedi: 24 / 1 735 = %1,4. Bu bir başarısızlıktır ve nedenlerini bilmek gerekir. FN 94 kare-nesne, yani GT'nin yaklaşık yüzde 5,4'ü. Bunların büyük kısmı kenarda kalan ve küçük ya da bulanık nesnelerdir; yani dedektörün kaçırmalarıdır, takipçinin değil. FP 205'in bir kısmı kuş OOD nesnesinden gelir; kalanı, dedektörün nominal sahnelerdeki sahte tespitleri ile kesişme sırasında kısa ömürlü yanlış izlerdir. IDSW 24 ise 0 ve 1 numaralı nesnelerin kesişmesinde (Bölüm 67.18) yoğunlaşır: iki iz kesişme anında birbirinin kimliğini alır ve Macar eşleştirmesi bunu düzeltmek için tek bir kareye yetecek bilgiye sahip değildir.

Şekil 80.5, seçilen yapılandırmanın test videosu 0 üzerindeki çıktısını gösterir. Gri noktalar gerçek yörüngeleri, renkli noktalar ise iz kimliklerini gösterir. Nesneler 0 ve 1 yaklaşık 35. karede aynı bölgeden geçer; kimlik değişimi riski en çok bu aralıkta vardır. Şekil tek bir videonun görsel özetidir. Kimlik değişimlerinin toplam sayısı için yukarıdaki IDSW değerlerine bakın.

![Şekil 80.5: Test videosu 0'da iz yörüngeleri ve gerçek yörüngeler](gorseller/b80_takip.png)

## 80.6 Edge dağıtım: katla, dışa aktar, küçült, ölç

Eğitilmiş bir model laboratuvarda işe yarar; edge'de ise üç şey daha ister. Birincisi, eğitim çatısından bağımsız bir biçim (ONNX), ikincisi daha küçük sayılar (int8), üçüncüsü ise kanıtlanmış bir süre bütçesi. Bölüm 75'te bu üç adımı teoriyle gördük; burada bunları tek bir hatta birleştiriyoruz ve her adımın bedelini ölçüyoruz.

İlk adım BatchNorm'u katlamaktır. Eğitimde BatchNorm, her kanalın ortalamasını ve varyansını kullanarak normalizasyon yapar; çıkarımda bu istatistikler sabittir. Bu yüzden Conv ile BN ardışık ise, BN'nin doğrusal dönüşümü Conv'un ağırlıklarına ve sapmasına gömülebilir. Bölüm 75'teki formül şöyledir: s = gamma / sqrt(var + eps); W' = W * s; b' = beta - mu * s. Katlama sonrası ağ BN içermez ve bir katman daha az çalıştırılır. Kodun ilk parçası sınıfları ve katlama fonksiyonunu tanımlar.

```python
# -*- coding: utf-8 -*-
# b80_onnx.py: BatchNorm katlama, ONNX disa aktarma, ONNX Runtime
# eslesme testi ve statik int8 kuantizasyon (QDQ). Kalibrasyon
# verisi egitimden ve test kumelerinden ayri bir tohumdan gelir.
import os
import time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import onnx
import onnxruntime as ort
from onnxruntime.quantization import (
    quantize_static,
    CalibrationDataReader,
    QuantType,
    QuantFormat,
)
import logging

logging.basicConfig(level=logging.ERROR)
ort.set_default_logger_severity(3)
from b80_veri import veri_seti, EGITIM, NOMINAL, DRIFT
from b67_04_yolo_mini import MiniYolo, degerlendir, decode, G, A, C

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ONNX32 = os.path.join(KLASOR, "yolo_fp32.onnx")
ONNX8 = os.path.join(KLASOR, "yolo_int8.onnx")
```

Kodun ikinci parçası, katlanmış ağırlıkları yeni bir `Dagitim` modülüne yükler. Bu modül yalnızca Conv, ReLU ve son 1 x 1 kafa katmanından oluşur. Orijinal `MiniYolo` ile yeni modül arasındaki sayısal fark, katlamanın doğruluğunu ölçer.

```python
def katla(conv, bn):
    """Conv2d (bias yok) + BatchNorm2d (eval) -> (W', b').
    s = gamma / sqrt(var + eps); W' = W * s; b' = beta - mu * s."""
    s = bn.weight / torch.sqrt(bn.running_var + bn.eps)
    w = conv.weight * s[:, None, None, None]
    b = bn.bias - bn.running_mean * s
    return w.detach(), b.detach()


class Dagitim(nn.Module):
    """BN'siz, yalnizca Conv + ReLU + 1x1 bas.

    Cikti: (B, A*(5+C), G, G)."""

    def __init__(self, model):
        super().__init__()
        self.convs = nn.ModuleList()
        self.adim = []
        for blk in model.govde:
            conv, bn = blk[0], blk[1]
            w, b = katla(conv, bn)
            c = nn.Conv2d(
                conv.in_channels,
                conv.out_channels,
                3,
                conv.stride,
                1,
                bias=True,
            )
            c.weight.data.copy_(w)
            c.bias.data.copy_(b)
            self.convs.append(c)
        self.bas = nn.Conv2d(64, A * (5 + C), 1)
        self.bas.load_state_dict(model.bas.state_dict())
```

Üçüncü parçada modülün ileri geçişi ve ham çıktıyı Bölüm 67'deki kod çözme biçimine çeviren `ham_to_cikti` fonksiyonu yer alır. Bir ağ çıktısının düzeni, son işlemenin doğru çalışması için bir sözleşmedir; burada sözleşme "kanal sırası = anchor x (5 + sınıf)" biçimindedir. `Veri` sınıfı ise statik kuantizasyon için kalibrasyon verisini sağlar.

```python
    def forward(self, x):
        for c in self.convs:
            x = F.relu(c(x))
        return self.bas(x)


def ham_to_cikti(ham):
    """(B, A*(5+C), G, G) -> (B, G, G, A, 5+C), b67 ile ayni duzen."""
    b = ham.shape[0]
    return ham.reshape(b, A, 5 + C, G, G).transpose(0, 3, 4, 1, 2)


class Veri(CalibrationDataReader):
    """Kalibrasyon: egitimden ayri tohum, 200 sahne (sadece girdi)."""

    def __init__(self, X):
        self.X = X
        self.i = 0

    def get_next(self):
        if self.i >= len(self.X):
            return None
        girdi = {"girdi": self.X[self.i : self.i + 1]}
        self.i += 1
        return girdi


def ort_oturum(yol, threads=4):
    opt = ort.SessionOptions()
    opt.intra_op_num_threads = threads
    opt.inter_op_num_threads = 1
    return ort.InferenceSession(
        yol, opt, providers=["CPUExecutionProvider"]
    )
```

Dördüncü parça, ONNX Runtime oturumunu iş parçacığı sayısıyla yapılandırır ve ONNX çıktısını aynı `decode` fonksiyonundan geçirerek PyTorch ile karşılaştırılabilir kutulara dönüştürür. Bu ortak son işleme, iki yolun farkını yalnızca ağa bağlar.

```python
def ort_tahmin(oturum, X):
    """ONNX ciktisi -> b67 decode'u ile kutular."""
    ciktilar = []
    ad = oturum.get_inputs()[0].name
    for i in range(0, len(X), 64):
        ham = oturum.run(None, {ad: X[i : i + 64]})[0]
        ciktilar.append(ham_to_cikti(ham))
    return decode(np.concatenate(ciktilar))


def main():
    base = MiniYolo()
    base.load_state_dict(
        torch.load(
            os.path.join(KLASOR, "yolo_t1.pt"), map_location="cpu"
        )
    )
    base.eval()
    dag = Dagitim(base).eval()
    Xte, Yte = veri_seti(500, seed=777, ayar=NOMINAL)
    Xdr, Ydr = veri_seti(500, seed=888, ayar=DRIFT)
    Xod, Yod = veri_seti(500, seed=999, ayar=NOMINAL, kus=1)
    Xcal, _ = veri_seti(200, seed=4242, ayar=EGITIM)

    # 1) BN katlama dogrulamasi (PyTorch, CPU)
    with torch.no_grad():
        x = torch.tensor(Xte[:200])
        a = base(x)
        b = ham_to_cikti(dag(x).numpy())
        a = a.numpy()
    fark = float(np.abs(a - b).max())
    print("BN katlama maks |fark| = %.2e" % fark)
```

Beşinci parça, katlamanın sayısal doğruluğunu ölçer ve modeli ONNX'e aktarır. Dışa aktarmada yükseklik ve genişlik eksenlerini dinamik bırakıyoruz; aksi hâlde 96 px'te donmuş bir graf, 640 px senaryosunu ölçmemize izin vermezdi. Bu küçük bir karardır ama sonradan 80.6'nın ikinci yarısında önem kazanır.

```python
    # 2) ONNX disa aktarma
    dummy = torch.zeros(1, 1, 96, 96)
    torch.onnx.export(
        dag,
        dummy,
        ONNX32,
        input_names=["girdi"],
        output_names=["cikti"],
        opset_version=17,
        dynamic_axes={
            "girdi": {0: "n", 2: "h", 3: "w"},
            "cikti": {0: "n", 2: "oh", 3: "ow"},
        },
        dynamo=False,
    )
    onnx.checker.check_model(onnx.load(ONNX32))
    print("ONNX fp32 boyut: %d bayt" % os.path.getsize(ONNX32))

    # 3) Statik int8 kuantizasyon (QDQ, kanal basina agirlik)
    quantize_static(
        ONNX32,
        ONNX8,
        Veri(Xcal),
        quant_format=QuantFormat.QDQ,
        per_channel=True,
        weight_type=QuantType.QInt8,
        activation_type=QuantType.QUInt8,
    )
    print("ONNX int8 boyut: %d bayt" % os.path.getsize(ONNX8))
```

Altıncı parça statik int8 kuantizasyonu yapar. QDQ biçimi, her tensörün etrafına QuantizeLinear ve DequantizeLinear düğümleri koyar. Ağırlıklar kanal başına simetrik int8, aktivasyonlar tensör başına asimetrik uint8 olarak kuantize edilir. Kalibrasyon için kullanılan 200 sahne, eğitimden ve test kümelerinden farklı bir tohumdan (4242) gelir; böylece kuantizasyon aralıkları test verisini görmez.

```python
    # 4) Dogruluk: PyTorch, ONNX fp32, ONNX int8
    satirlar = []
    sess32 = ort_oturum(ONNX32)
    sess8 = ort_oturum(ONNX8)
    ps = {}
    for ad, (X, Y) in {
        "test": (Xte, Yte),
        "drift": (Xdr, Ydr),
        "ood": (Xod, Yod),
    }.items():
        with torch.no_grad():
            pt = decode(
                np.concatenate(
                    [
                        base(torch.tensor(X[i : i + 64])).numpy()
                        for i in range(0, len(X), 64)
                    ]
                )
            )
        p32 = ort_tahmin(sess32, X)
        p8 = ort_tahmin(sess8, X)
        for yontem, pred in [
            ("pytorch", pt),
            ("onnx_fp32", p32),
            ("onnx_int8", p8),
        ]:
            m50, m5095 = degerlendir(pred, Y)
            satirlar.append((yontem, ad, m50, m5095))
            print(
                "%-10s %-6s mAP@0.5=%.4f  mAP@[.5:.95]=%.4f"
                % (yontem, ad, m50, m5095)
            )
        ps[ad] = (pt, p32, p8)
    # ONNX fp32 ile PyTorch arasindaki kutu farki (test)
    d = 0.0
    for (kp, sp, cp), (kq, sq, cq) in zip(
        ps["test"][0], ps["test"][1]
    ):
```

Son parça ölçüm çıktısını ve kutu farkını yazar. Bu dosyadaki `quantize_static` çağrısı, ONNX Runtime 1.25.1'in kendi kuantizasyon modülünü kullanır; kaynağını Kod Okuma bölümünde inceleyeceğiz.

```python
        if len(kp) and len(kq) and len(kp) == len(kq):
            d = max(d, float(np.abs(kp - kq).max()))
    print("test: ONNX fp32 ile PyTorch kutu maks farki = %.2e" % d)
    boyut = {
        "pytorch": os.path.getsize(
            os.path.join(KLASOR, "yolo_t1.pt")
        ),
        "onnx_fp32": os.path.getsize(ONNX32),
        "onnx_int8": os.path.getsize(ONNX8),
    }
    with open(
        os.path.join(VERI, "b80_onnx.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("yontem,kume,map50,map5095,boyut_bayt\n")
        for yontem, ad, m50, m5095 in satirlar:
            f.write(
                "%s,%s,%.4f,%.4f,%d\n"
                % (yontem, ad, m50, m5095, boyut[yontem])
            )


if __name__ == "__main__":
    main()
```

```term
$ python b80_onnx.py
BN katlama maks |fark| = 1.10e-05
ONNX fp32 boyut: 246582 bayt
ONNX int8 boyut: 71173 bayt
pytorch    test   mAP@0.5=0.9390  mAP@[.5:.95]=0.6386
onnx_fp32  test   mAP@0.5=0.9390  mAP@[.5:.95]=0.6386
onnx_int8  test   mAP@0.5=0.9276  mAP@[.5:.95]=0.5433
pytorch    drift  mAP@0.5=0.8725  mAP@[.5:.95]=0.5474
onnx_fp32  drift  mAP@0.5=0.8725  mAP@[.5:.95]=0.5474
onnx_int8  drift  mAP@0.5=0.8358  mAP@[.5:.95]=0.4719
pytorch    ood    mAP@0.5=0.8952  mAP@[.5:.95]=0.6052
onnx_fp32  ood    mAP@0.5=0.8952  mAP@[.5:.95]=0.6052
onnx_int8  ood    mAP@0.5=0.8869  mAP@[.5:.95]=0.5161
test: ONNX fp32 ile PyTorch kutu maks farki = 7.99e-06
```

### Doğruluk: katlama bedava, int8 bedeli var

Tablo, PyTorch, ONNX fp32 ve ONNX int8 modellerinin üç kümedeki mAP değerlerini verir. Tek bir tohum (1) kullanılmıştır; bu bölüm amacı, dışa aktarma ve kuantizasyonun etkisini izole etmektir.

| Küme | Yöntem | mAP@0,5 | mAP@[0,5:0,95] | Kayıp (mAP@0,5) | Kayıp (mAP@[0,5:0,95]) |
|---|---|---|---|---|---|
| Test | PyTorch | 0,939 | 0,639 | - | - |
| Test | ONNX fp32 | 0,939 | 0,639 | 0 | 0 |
| Test | ONNX int8 | 0,928 | 0,543 | 1,1 puan | 9,5 puan |
| Kayma | PyTorch | 0,873 | 0,547 | - | - |
| Kayma | ONNX int8 | 0,836 | 0,472 | 3,7 puan | 7,6 puan |
| OOD | PyTorch | 0,895 | 0,605 | - | - |
| OOD | ONNX int8 | 0,887 | 0,516 | 0,8 puan | 8,9 puan |

İlk iki satır sağlam bir sonuçtur. BN katlama farkı maksimum 1,10e-5, ONNX ile PyTorch kutuları arasındaki en büyük fark ise 7,99e-6'dır. Yani dışa aktarma ve katlama, R14 eşiğinin (1e-4) çok altında kaldı. Bu, Bölüm 75'te savunduğumuz "önce eşleşme testi" ilkesinin pratikteki karşılığıdır.

int8 tablosu daha ilginçtir. mAP@0,5 kaybı nominal test için 1,1 puan, yani R5 (<= 2 puan) geçildi. Ama mAP@[0,5:0,95] kaybı 9,5 puan, yani R6 (<= 5 puan) geçilemedi. Fark, metriğin ne ölçtüğündedir. mAP@0,5 kutunun kabaca doğru yerde olduğunu ister; mAP@[0,5:0,95] ise on farklı IoU eşiğinde kutunun ne kadar hassas olduğunu ister. Kuantizasyon, kutu koordinatlarını hafifçe kaydırıyor; kutu kabaca doğru ama kesin değil. Hipotezimiz, kafa katmanındaki ofset ve log-ölçek kodlamasının (Bölüm 67.8) kuantizasyon hatasına karşı hassas olduğudur: w = anchor * exp(t_w) gibi bir üstel, küçük bir t_w hatasını ölçekle büyütür. Bu hipotezi bu bölümde doğrulamadık. Doğrulamak için kafa katmanını fp32 tutan bir karma hassasiyet deneyi yapılabilir; Ek alıştırmalarda bunu bir soru olarak bıraktık.

Boyut açısından int8 bir kazanımdır. PyTorch durum dosyası 255 304 bayt, ONNX fp32 246 582 bayt ve ONNX int8 71 173 bayt. Modelin kendi sabitleri (ağırlık ve sapmalar) 64 366 bayttır. Bu, Cortex-M sınıfı bir mikrodenetleyicinin flaşına sığacak bir boyuttur ve R9'u (<= 1 MB) bol bol geçer.

### Gecikme: ölçüm disiplini ve bütçe

Gecikme ölçümü, Bölüm 75.2'deki disiplinle yapılır: bir ısınma dönemi (30 kare), sonra 300 kare üzerinden p50 ve p95 değerleri; ölçüm CPU'da yapılır çünkü edge hedefimiz CPU'dur. Her kare, bir sensör çıktısı simülasyonuyla başlar (float'tan uint8'e ve geri), sonra sırasıyla ön işleme, çıkarım, son işleme, takip ve güvence kuralı çalışır. Her aşama ayrı zamanlanır.

Kodun ilk parçası sabitleri ve import'ları tanımlar; ölçüm döngüsü ikinci parçadadır.

```python
# -*- coding: utf-8 -*-
# b80_gecikme.py: kare basina gecikme (CPU, ONNX Runtime), asama
# dokumu (on isleme, cikarim, son isleme, takip, guvence) ve bellek /
# MAC hesabi. Olcum CPU'da yapilir; Cortex-M ya da Jetson olculmedi.
import os
import time
import numpy as np
import onnx
from b80_veri import video, NOMINAL
from b80_onnx import ort_oturum, ham_to_cikti, ONNX32, ONNX8
from b67_04_yolo_mini import decode
from b67_08_takip import Izleyici

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ISINMA, OLCUM = 30, 300
ASAMALAR = ["on_isleme", "cikarim", "son_isleme", "takip", "guvence"]
```

Kodun ikinci parçası ölçüm döngüsüdür. `time.perf_counter` her aşamanın başında ve sonunda çağrılır; ısınma kareleri atılır. Gecikmeler milisaniye cinsinden kaydedilir.

```python
def olc(yol, threads, kareler):
    sess = ort_oturum(yol, threads)
    ad = sess.get_inputs()[0].name
    iz = Izleyici("acgozlu_iou")
    zaman = {a: [] for a in ASAMALAR}
    for t in range(ISINMA + OLCUM):
        img = kareler[t % len(kareler)]["img"]
        t0 = time.perf_counter()
        kare_u8 = (img * 255).astype(np.uint8)  # sensor ciktisi
        x = kare_u8.astype(np.float32).reshape(1, 1, 96, 96) / 255.0
        t1 = time.perf_counter()
        ham = sess.run(None, {ad: x})[0]
        t2 = time.perf_counter()
        kut, skor, _ = decode(ham_to_cikti(ham))[0]
        t3 = time.perf_counter()
        iz.guncelle(kut, skor)
        t4 = time.perf_counter()
        _ = [s < 0.6 for s in skor]  # guvence kurali
        t5 = time.perf_counter()
        if t >= ISINMA:
            for a, (p, q) in zip(
                ASAMALAR,
                [(t0, t1), (t1, t2), (t2, t3), (t3, t4), (t4, t5)],
            ):
                zaman[a].append((q - p) * 1000.0)
    return {a: np.array(v) for a, v in zaman.items()}


def conv_mac(h, w, cin, cout, k=3):
    return h * w * cin * cout * k * k
```

Üçüncü parça, konvolüsyonun çarpma-toplama sayısını (MAC) hesaplar. Bir konvolüsyonun MAC sayısı, çıktı alanı x giriş kanalı x çıkış kanalı x çekirdek alanıdır. Bu hesap, işlem yükünü bellek ve gecikmeden bağımsız olarak verir; Bölüm 75.1'deki maliyet modelinin doğrudan uygulamasıdır.

```python
def mac_tablosu(boyut):
    """Bolum 67/75'in 4 konvolusyonu + 1x1 bas. Adim 2,2,2,1."""
    katman = [(1, 16, 2), (16, 32, 2), (32, 64, 2), (64, 64, 1)]
    h = boyut
    toplam, cikis_bayt = 0, []
    for cin, cout, adim in katman:
        h = h // adim
        toplam += conv_mac(h, h, cin, cout)
        cikis_bayt.append(cout * h * h)  # int8: 1 bayt / eleman
    toplam += h * h * 64 * 16  # 1x1 bas
    return toplam, cikis_bayt
```

Dördüncü parça ana fonksiyonun ilk yarısıdır: iki iş parçacığı sayısı (4 ve 1) ve iki hassasiyet (int8, fp32) için ölçümleri çalıştırır, sonuçları yazdırır.

```python
def main():
    kareler = video(300, kus=1)
    satirlar = []
    print(
        "%-10s %-6s %-12s %8s %8s"
        % ("is_parcacigi", "model", "asama", "p50_ms", "p95_ms")
    )
    for threads in (4, 1):
        for ad, yol in [("int8", ONNX8), ("fp32", ONNX32)]:
            z = olc(yol, threads, kareler)
            toplam = sum(z[a] for a in ASAMALAR)
            for a in ASAMALAR + ["toplam"]:
                v = toplam if a == "toplam" else z[a]
                p50, p95 = np.percentile(v, 50), np.percentile(v, 95)
                satirlar.append((threads, ad, a, p50, p95))
                print(
                    "%-10d %-6s %-12s %8.3f %8.3f"
                    % (threads, ad, a, p50, p95)
                )
    with open(
        os.path.join(VERI, "b80_gecikme.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("threads,model,asama,p50_ms,p95_ms\n")
        for s in satirlar:
            f.write("%d,%s,%s,%.3f,%.3f\n" % s)
    # Bilesen cubugu: int8, 4 thread, p50 degerleri
    with open(
        os.path.join(VERI, "b80_gecikme_bilesen.csv"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("senaryo,asama,p50_ms\n")
        for s in satirlar:
            if s[1] == "int8" and s[2] != "toplam":
                f.write("%d_thread,%s,%.3f\n" % (s[0], s[2], s[3]))
    # Olcek senaryosu: ayni ag 640x640 girdide (yalnizca cikarim
    # suresi; bu boyutta egitilmedi, dogruluk yok)
    nl = chr(10)
```

Beşinci parça 640 piksellik senaryoyu ölçer. Bu boyutta ağ eğitilmedi; yalnızca çıkarım süresi ölçülür. Dolayısıyla bu satır bir doğruluk değil, bir hız tahminidir.

```python
    rng = np.random.default_rng(0)
    x640 = rng.random((1, 1, 640, 640), dtype=np.float32)
    with open(
        os.path.join(VERI, "b80_gecikme_640.csv"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("threads,girdi,p50_ms,p95_ms" + nl)
        for threads in (4, 1):
            sess = ort_oturum(ONNX8, threads)
            ad = sess.get_inputs()[0].name
            zs = []
            for t in range(10 + 60):
                t0 = time.perf_counter()
                sess.run(None, {ad: x640})
                if t >= 10:
                    zs.append((time.perf_counter() - t0) * 1000.0)
            zs = np.array(zs)
            p50, p95 = np.percentile(zs, 50), np.percentile(zs, 95)
            print(
                "640x640 int8 %d thread: cikarim p50=%.2f ms "
                "p95=%.2f ms" % (threads, p50, p95)
            )
            f.write("%d,640,%.3f,%.3f" % (threads, p50, p95) + nl)
    # Bellek ve MAC: Cortex-M sinifi icin 96x96 ve 640x640 girdi
    m = onnx.load(ONNX8)
    flash = sum(
        int(np.prod(t.dims))
        * (
            4
            if t.data_type == 1
            else 1 if t.data_type in (2, 3) else 4
        )
        for t in m.graph.initializer
    )
    print(
        "\nint8 model agirlik ve sabitler (yaklasik): %d bayt" % flash
    )
```

Son parça bellek hesabını yapar: model sabitlerinin toplam baytı ve iki girdi boyutu için MAC ile en büyük ara tamponu. Bu sayılar, Cortex-M tartışmasının sayısal temelidir.

```python
    for boyut in (96, 640):
        mac, cikislar = mac_tablosu(boyut)
        print(
            "girdi %dx%d: MAC = %.1f milyon, en buyuk ara tampon "
            "= %d bayt" % (boyut, boyut, mac / 1e6, max(cikislar))
        )
    with open(
        os.path.join(VERI, "b80_bellek.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("girdi,mac,en_buyuk_ara_bayt,agirlik_bayt\n")
        for boyut in (96, 640):
            mac, cikislar = mac_tablosu(boyut)
            f.write(
                "%d,%d,%d,%d\n" % (boyut, mac, max(cikislar), flash)
            )


if __name__ == "__main__":
    main()
```

```term
$ python b80_gecikme.py
is_parcacigi model  asama          p50_ms   p95_ms
4          int8   on_isleme       0.019    0.026
4          int8   cikarim         0.115    0.152
4          int8   son_isleme      0.288    0.549
4          int8   takip           0.300    0.455
4          int8   guvence         0.002    0.003
4          int8   toplam          0.747    1.092
4          fp32   on_isleme       0.020    0.029
4          fp32   cikarim         0.120    0.145
4          fp32   son_isleme      0.260    0.543
4          fp32   takip           0.294    0.477
4          fp32   guvence         0.002    0.003
4          fp32   toplam          0.703    1.146
1          int8   on_isleme       0.019    0.026
1          int8   cikarim         0.214    0.238
1          int8   son_isleme      0.266    0.477
1          int8   takip           0.286    0.361
1          int8   guvence         0.002    0.003
1          int8   toplam          0.812    1.074
1          fp32   on_isleme       0.019    0.027
1          fp32   cikarim         0.203    0.223
1          fp32   son_isleme      0.249    0.413
1          fp32   takip           0.284    0.357
1          fp32   guvence         0.002    0.003
1          fp32   toplam          0.779    0.991
640x640 int8 4 thread: cikarim p50=2.83 ms p95=3.08 ms
640x640 int8 1 thread: cikarim p50=7.83 ms p95=8.06 ms

int8 model agirlik ve sabitler (yaklasik): 64366 bayt
girdi 96x96: MAC = 11.1 milyon, en buyuk ara tampon = 36864 bayt
girdi 640x640: MAC = 493.2 milyon, en buyuk ara tampon = 1638400 bayt
```

Tabloda kare başına sürenin aşamalara göre dağılımı vardır. Değerler p50 ve p95 olarak milisaniye cinsindendir.

| Aşama | int8, 4 iş p. (p50 / p95) | fp32, 4 iş p. (p50 / p95) | int8, 1 iş p. (p50 / p95) |
|---|---|---|---|
| Ön işleme | 0,019 / 0,026 | 0,020 / 0,029 | 0,019 / 0,026 |
| Çıkarım | 0,115 / 0,152 | 0,120 / 0,145 | 0,214 / 0,238 |
| Son işleme (kod çözme, NMS) | 0,288 / 0,549 | 0,260 / 0,543 | 0,266 / 0,477 |
| Takip | 0,300 / 0,455 | 0,294 / 0,477 | 0,286 / 0,361 |
| Güvence | 0,002 / 0,003 | 0,002 / 0,003 | 0,002 / 0,003 |
| Toplam | 0,747 / 1,092 | 0,703 / 1,146 | 0,812 / 1,074 |

![Şekil 80.6: Doğruluk ve gecikme: PyTorch, ONNX fp32 ve int8 (gecikme uçtan uca, CPU)](gorseller/b80_karsilastirma.png)

Bu tablo iki açıdan öğreticidir. İlki, çıkarımın toplamın yalnızca yaklaşık yüzde 15'i olmasıdır. Son işleme ve takip birlikte, toplamın yaklaşık yüzde 80'ini oluşturur. Şekil 80.7, bu dağılımı yığılı çubukla gösterir.

![Şekil 80.7: Kare başına gecikmenin aşamalara göre dağılımı (int8, p50)](gorseller/b80_bilesen.png)

Hızlandırmak istediğimiz şeyi yanlış seçersek, çıkarımı iki katına çıkarsak bile toplam yalnızca birkaç yüzde kazanır. Bölüm 53'teki Amdahl yasası tam olarak budur: bir parçanın payı küçükse, o parçayı hızlandırmanın üst sınırı küçüktür.

İkincisi, int8'in bu ölçekte hız kazandırmadığıdır. 4 iş parçacığında int8 çıkarımı 0,115 ms, fp32 ise 0,120 ms; 1 iş parçacığında ise int8 0,214 ms, fp32 0,203 ms. Fark, ölçüm gürültüsünün içinde. Nedeni, ağın çok küçük olması ve kuantizasyon düğümlerinin (QuantizeLinear, DequantizeLinear) sabit bir ek yük getirmesidir. int8'in gerçek hız kazancı, daha büyük katmanlarda ve tam sayı çekirdeklerinin desteklendiği donanımda ortaya çıkar; bu bir genel bilgidir ve bu makinede ölçülmedi. Kazancı belirleyen şey, kuantizasyonun bir modeli küçültüp küçültmediği değil, modelin ölçeğine ve donanımın tam sayı yeteneğine bağlıdır.

R7'yi (96 px, uçtan uca p95 <= 33 ms) geçtik: 1,09 ms. Ama bu rakam 96 piksel için geçerlidir ve 96 piksel gerçek bir İHA için yeterli çözünürlük değildir. Hedefler 8 ile 24 piksel arasındaydı; 1920 x 1080'lik bir kareyi 96 x 96'ya indirmek, bir hedefi birkaç piksele düşürür.

### Çözünürlük ve Cortex-M: neden 640 px sorun?

Bu yüzden 640 x 640 girdiyle aynı ağın çıkarım süresini de ölçtük. Ağ tamamen konvolüsyonel olduğu için girdi boyutunu değiştirmek, ağırlıkları değiştirmez; bu yalnızca bir hız ölçümüdür, doğruluk değildir. Sonuç: int8 çıkarımı 4 iş parçacığında 2,83 ms (p50), 1 iş parçacığında 7,83 ms. Yani ağın kendisi 33 ms bütçesinin içinde kalır, ama bu, uçtan uca bir kanıt değildir: 640 pikselde kod çözme, 80 x 80 ızgara üzerinde çalışır ve bu, 12 x 12'ye göre yaklaşık 44 kat daha fazla hücre demektir. Mevcut son işleme Python döngüleriyle yazılmıştır. Bu aşama ölçülmedi. R8 yalnızca ağ için geçildi; R7'nin 640 px karşılığı ise "ölçülmedi" olarak kalır.

Bellek tarafını da hesaplayalım. Tablo, iki girdi boyutu için MAC sayısını ve en büyük ara tamponu verir.

| Girdi | MAC (kare başına) | En büyük ara tampon (int8) | Model sabitleri |
|---|---|---|---|
| 96 x 96 | 11,1 milyon | 36 864 bayt (36 KB) | 64 366 bayt |
| 640 x 640 | 493,2 milyon | 1 638 400 bayt (1,6 MB) | 64 366 bayt |

96 piksel için sayılar bir mikrodenetleyiciye yakındır: 64 KB sabit, 36 KB ara tampon. Bölüm 75.8'de bir Cortex-M4'te int8 MLP'nin nasıl kurulacağını gördük; bu ağ da aynı türden işlemlerden oluşur. Ama 640 piksel için tampon tek başına 1,6 MB'dır; birçok Cortex-M4 ve M7 çipinin toplam SRAM'inden büyüktür (genel bilgi, bu makinede ölçülmedi). Ayrıca 640 pikselde kare başına 493 milyon MAC, 30 kare/s için saniyede yaklaşık 15 milyar MAC demektir. Bir Cortex-M4 bunu, SIMD dahil bile, yapamaz (genel bilgi). Bu yüzden bu sistemin hedef donanımı, Cortex-M sınıfı değil, Jetson sınıfı bir GPU veya bir NPU olmalıdır. Jetson'da ölçüm yapmadık; bu yalnızca bir tahmin ve bir tasarım gerekçesidir.

Kısacası karar şudur: 96 piksellik bir sistem bir mikrodenetleyiciye sığabilir ama işe yaramaz; 640 piksellik bir sistem işe yarayabilir ama bir mikrodenetleyiciye sığmaz. Gereksinimler, donanımın seçimini zorlar. Bu, gömülü sistemlerde sık karşılaşılan bir ikilemdir ve Bölüm 75.9'da edge tasarımı için verilen kararlarla aynı yönü gösterir.

## 80.7 Güvence: ne zaman "emin değilim" demeli

Bir dedektörün en tehlikeli davranışı, yanlış olduğu bir tespiti yüksek güvenle göstermesidir. Skor 0,9 olan bir kuş, operatörün gözünde bir İHA olabilir. Güvence katmanının işi, sistemin ne bildiğini ve ne bilmediğini ayırmaktır. Bu bölümde iki basit kural kuruyoruz ve hangisinin hangi koşulda işe yaradığını ölçüyoruz.

Birinci kural tek skora bakar: skor eşiğin (tau) üstündeyse tespit "otomatik alarm" olur, altındaysa "operatöre doğrulat" olarak işaretlenir. Bu, en ucuz güvence biçimidir ve sıfır ek işlem gerektirir.

İkinci kural tohum uyumuna bakar. Aynı mimari, farklı başlangıç ağırlıklarıyla üç kez eğitildi. Eğitim verisi aynı olduğu hâlde, üç modelin bir tespit üzerinde hemfikir olması, o tespitin veriden kaynaklanan bir örüntü olduğunu gösterir. Biri tespit ederken diğerleri etmiyorsa, tespit başlangıç rastgeleliğine bağlıdır ve güvenilmez. Bu, belirsizliğin bir parçasıdır: ağın kendi bilgisindeki eksikliği (epistemik belirsizlik). Belirsizlik tahminini ve dağılım dışı (OOD) tespitini Bölüm 78'de derinlemesine işlemiştik; burada yalnızca bu sinyalin sisteme nasıl bağlandığını gösteriyoruz.

Uyum kuralı şöyle tanımlanır: bir tespitin, diğer iki tohumdan birinde aynı sınıfta, IoU en az 0,5 ile örtüşen ve skoru en az 0,3 olan bir karşılığı varsa, o tespit "uyumlu" sayılır. Otomatik alarm için hem skor eşiğini geçmesi hem de iki tohumla da uyumlu olması gerekir.

Kodun ilk parçası uyum ölçümünü ve doğru eşleştirme için kullanılan gerçek eşleştirme fonksiyonunu tanımlar. Eşleştirme Bölüm 67.7'deki AP hesabıyla aynı mantığı izler: skora göre azalan sırada, en yüksek IoU'lu ve henüz kullanılmamış gerçek kutuyu seçer.

```python
# -*- coding: utf-8 -*-
# b80_guvence.py: guvence katmani. Her tespit iki kurala gore
# 'otomatik alarm' (operatore dogrudan gider) ya da 'operatore
# dogrulat' olarak ayrilir:
#   tek_skor : skor >= tau
#   topluluk : skor >= tau VE tohum 2 ile 3 da ayni sinifta ortusen
#              bir tespit uretir (IoU >= 0.5, skor >= 0.3)
# Esik yalnizca dogrulama kumesinde secilir (kesinlik >= 0.90 kosulu,
# kapsama en yuksek). Test ve OOD kumeleri sonra okunur.
import os
import pickle
import numpy as np
from b80_veri import veri_seti, EGITIM, NOMINAL, DRIFT
from b67_01_iou_nms import iou_matris

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
TAUS = np.round(np.arange(0.05, 0.96, 0.05), 2)
KESINLIK_HEDEF = 0.90


def uyum(d1, d2):
    """d1'in her tespiti icin d2'de ayni sinifli, IoU >= 0.5 ve skor
    >= 0.3 olan bir tespit var mi? (bool dizisi)"""
    kut1, _, cls1 = d1
    kut2, skor2, cls2 = d2
    out = np.zeros(len(kut1), bool)
    if len(kut1) == 0 or len(kut2) == 0:
        return out
    iou = iou_matris(kut1, kut2)
    ok = (
        (cls1[:, None] == cls2[None, :])
        & (iou >= 0.5)
        & (skor2[None, :] >= 0.3)
    )
    return ok.any(axis=1)
```

Kodun ikinci parçası, eşleştirme fonksiyonunun devamıdır. Burada bir karar, gerçek kutulara bir kez eşlenen tespitlerin doğruluğunu sağlar; aynı gerçek kutuya birden fazla tespit eşlenemez.

```python
def tp_maske(kut, skor, cls, gk, gc):
    """Skora gore azalan sirada acgozlu eslesme; TP mask'i (kumulatif
    degil, her tespit icin)."""
    tp = np.zeros(len(kut), bool)
    if len(kut) == 0 or len(gk) == 0:
        return tp
    kullanildi = np.zeros(len(gk), bool)
    iou = iou_matris(kut, gk)
    for i in np.argsort(-skor, kind="stable"):
        aday = np.where((~kullanildi) & (gc == cls[i]), iou[i], -1.0)
        j = int(np.argmax(aday))
        if aday[j] >= 0.5:
            tp[i] = True
            kullanildi[j] = True
    return tp


def maske_uret(pred, kural, tau, tohum_preds):
    """Gorsel basina otomatik alarm maskeleri."""
    maskeler = []
    for i, (kut, skor, cls) in enumerate(pred):
        m = skor >= tau
        if kural == "topluluk":
            a = uyum((kut, skor, cls), tohum_preds[0][i]) & uyum(
                (kut, skor, cls), tohum_preds[1][i]
            )
            m = m & a
        maskeler.append(m)
    return maskeler
```

Üçüncü parça, bir kurala ve eşiğe göre hangi tespitlerin otomatik alarm olduğunu belirleyen maskeyi üretir.

```python
def olc(pred, Y, maskeler):
    """Donus: kesinlik, kapsama, gorsel basina yanlis alarm."""
    n_oto = tp = gt_say = 0
    for (kut, skor, cls), objs, m in zip(pred, Y, maskeler):
        gk = np.array([o["box"] for o in objs], float).reshape(-1, 4)
        gc = np.array([o["cls"] for o in objs], int)
        gt_say += len(gc)
        idx = np.where(m)[0]
        t = tp_maske(kut[idx], skor[idx], cls[idx], gk, gc)
        n_oto += len(idx)
        tp += int(t.sum())
    kesinlik = tp / n_oto if n_oto else float("nan")
    kapsama = tp / max(gt_say, 1)
    yanlis = (n_oto - tp) / len(Y)
    return kesinlik, kapsama, yanlis
```

Dördüncü parça, bir maske ile birlikte kesinlik, kapsama ve görüntü başına yanlış alarmı hesaplar. Üç ölçü birlikte okunmalıdır; biri tek başına yanıltır.

```python
def main():
    tahminler = pickle.load(
        open(os.path.join(KLASOR, "tahminler.pkl"), "rb")
    )
    kumeler = {
        "val": veri_seti(300, seed=5, ayar=EGITIM),
        "test": veri_seti(500, seed=777, ayar=NOMINAL),
        "drift": veri_seti(500, seed=888, ayar=DRIFT),
        "ood": veri_seti(500, seed=999, ayar=NOMINAL, kus=1),
    }
    # tohum 1 bir kayit; tohum 2 ve 3 uyum icin
    sonuc = []
    secim = {}
    for kural in ["tek_skor", "topluluk"]:
        # esik secimi: yalnizca dogrulama
        en_iyi = None
        for tau in TAUS:
            Xv, Yv = kumeler["val"]
            t2 = tahminler[(2, "val")]
            t3 = tahminler[(3, "val")]
            m = maske_uret(
                tahminler[(1, "val")], kural, tau, [t2, t3]
            )
            k, c, y = olc(tahminler[(1, "val")], Yv, m)
            sonuc.append((kural, "val", tau, k, c, y))
            if not np.isnan(k) and k >= KESINLIK_HEDEF:
                if en_iyi is None or c > en_iyi[1]:
                    en_iyi = (tau, c)
        secim[kural] = en_iyi[0] if en_iyi else None
        print(
            "%s: dogrulamada secilen tau = %s" % (kural, secim[kural])
        )
    # Korumasiz referans: tum tespitler otomatik (tau = 0.05)
    for ad, (X, Y) in kumeler.items():
        if ad == "val":  # dogrulama zaten yukarida
            continue
        for kural in ["tek_skor", "topluluk"]:
            for tau in TAUS:
```

Beşinci parça ana akıştır. Eşik seçimi yalnızca doğrulama kümesinde yapılır: iki kural için eşikler taranır ve kesinlik en az 0,90 olan eşikler arasından kapsaması en yüksek olan seçilir. Bu, Bölüm 57'deki maliyet temelli eşik seçiminin basit bir biçimidir: yanlış alarm pahalıysa kesinlik hedefi yükselir, kaçırılan hedef pahalıysa kapsama hedefi yükselir. 0,90 bir maliyet varsayımıdır, bir ölçüm değildir; bunu açıkça kabul ediyoruz.

```python
                m = maske_uret(
                    tahminler[(1, ad)],
                    kural,
                    tau,
                    [tahminler[(2, ad)], tahminler[(3, ad)]],
                )
                k, c, y = olc(tahminler[(1, ad)], Y, m)
                sonuc.append((kural, ad, tau, k, c, y))
        m = [np.ones(len(p[1]), bool) for p in tahminler[(1, ad)]]
        k, c, y = olc(tahminler[(1, ad)], Y, m)
        sonuc.append(("korumasiz", ad, 0.0, k, c, y))
    with open(
        os.path.join(VERI, "b80_guvence.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("kural,kume,tau,kesinlik,kapsama,yanlis_alarm_gor\n")
        for kural, ad, tau, k, c, y in sonuc:
            f.write(
                "%s,%s,%.2f,%.4f,%.4f,%.4f\n"
                % (kural, ad, tau, k, c, y)
            )
    print("\nSecilen esiklerle (test ve OOD):")
    for kural in ["tek_skor", "topluluk"]:
        tau = secim[kural]
        for ad in ["test", "drift", "ood"]:
            X, Y = kumeler[ad]
            m = maske_uret(
                tahminler[(1, ad)],
                kural,
                tau,
                [tahminler[(2, ad)], tahminler[(3, ad)]],
            )
            k, c, y = olc(tahminler[(1, ad)], Y, m)
            print(
                "%-9s %-5s tau=%.2f kesinlik=%.3f kapsama=%.3f "
                "yanlis/gorsel=%.3f" % (kural, ad, tau, k, c, y)
            )
    for ad in ["test", "ood"]:
        X, Y = kumeler[ad]
```

Son parça, korumasız (her tespit otomatik) referansı ölçer ve sonuçları CSV'ye yazar. Korumasız referans, güvencenin ne kazandırdığını ve ne kaybettirdiğini gösteren tabandır.

```python
        m = [np.ones(len(p[1]), bool) for p in tahminler[(1, ad)]]
        k, c, y = olc(tahminler[(1, ad)], Y, m)
        print(
            "korumasiz %-5s kesinlik=%.3f kapsama=%.3f "
            "yanlis/gorsel=%.3f" % (ad, k, c, y)
        )


if __name__ == "__main__":
    main()
```

```term
$ python b80_guvence.py
tek_skor: dogrulamada secilen tau = 0.3
topluluk: dogrulamada secilen tau = 0.05

Secilen esiklerle (test ve OOD):
tek_skor  test  tau=0.30 kesinlik=0.917 kapsama=0.923 yanlis/gorsel=0.202
tek_skor  drift tau=0.30 kesinlik=0.814 kapsama=0.849 yanlis/gorsel=0.472
tek_skor  ood   tau=0.30 kesinlik=0.730 kapsama=0.899 yanlis/gorsel=0.824
topluluk  test  tau=0.05 kesinlik=0.961 kapsama=0.878 yanlis/gorsel=0.086
topluluk  drift tau=0.05 kesinlik=0.939 kapsama=0.775 yanlis/gorsel=0.122
topluluk  ood   tau=0.05 kesinlik=0.939 kapsama=0.870 yanlis/gorsel=0.140
korumasiz test  kesinlik=0.593 kapsama=0.955 yanlis/gorsel=1.588
korumasiz ood   kesinlik=0.377 kapsama=0.948 yanlis/gorsel=3.886
```

### Sonuçlar: iki kuralın ödünleşimi

Doğrulama kümesinde tek skor kuralı için seçilen eşik 0,30 (kesinlik 0,913, kapsama 0,904). Tohum uyumu kuralı için seçilen eşik 0,05 (kesinlik 0,963, kapsama 0,879). Tohum uyumu, eşik düşük olsa bile kesinliği artırır, çünkü yalnızca iki tohumun da hemfikir olduğu tespitleri geçirir.

Tablo, seçilen eşiklerde test, kayma ve OOD kümelerini gösterir. "Yanlış/görüntü" sütunu, bir görüntüde operatöre giden yanlış otomatik alarm sayısıdır.

| Kural | Küme | Kesinlik | Kapsama | Yanlış / görüntü |
|---|---|---|---|---|
| Korumasız | Test | 0,593 | 0,955 | 1,588 |
| Tek skor (tau 0,30) | Test | 0,917 | 0,923 | 0,202 |
| Tohum uyumu (tau 0,05) | Test | 0,961 | 0,878 | 0,086 |
| Korumasız | OOD | 0,377 | 0,948 | 3,886 |
| Tek skor (tau 0,30) | OOD | 0,730 | 0,899 | 0,824 |
| Tohum uyumu (tau 0,05) | OOD | 0,939 | 0,870 | 0,140 |
| Tek skor (tau 0,30) | Kayma | 0,814 | 0,849 | 0,472 |
| Tohum uyumu (tau 0,05) | Kayma | 0,939 | 0,775 | 0,122 |

OOD satırları, güvencenin asıl işini gösterir. Korumasız sistemde her görüntüde ortalama 3,9 yanlış otomatik alarm vardır; bunların çoğu kuş benzeri şekillerdir. Tek skor kuralı bunu 0,82'ye indirir (yüzde 79 azalma). Tohum uyumu ise 0,14'e indirir (yüzde 96 azalma). İki kuralın da R11'i (en az yüzde 50 azalma) geçtiğini görüyoruz.

Asıl ödünleşim kapsamadadır. Korumasız sistemin test kapsaması 0,955'tir; tek skor kuralı bunu 0,923'e, tohum uyumu ise 0,878'e indirir. R12 (kapsama kaybı en fazla 5 puan) tek skor kuralı için geçildi (3,2 puan kayıp), tohum uyumu için geçilemedi (7,7 puan kayıp). Yani tohum uyumu daha temiz bir alarm akışı sağlar, ama bunun bedelini kaçırılan hedeflerle öder. Hangisinin doğru olduğu bir mühendislik kararıdır ve bu karar, operatörün ne kadar kaçırmayı göze alabileceğine bağlıdır. Bu nedenle eşik değil, kuralın seçimi operasyonel bir karardır.

Tohum uyumunun bir maliyeti de vardır. Her kare için üç model çalıştırmak gerekir. Bu bölümün ölçümlerine göre bir modelin çıkarım süresi yaklaşık 0,115 ms ve son işleme süresi yaklaşık 0,29 ms'dir (80.6). Üç modelle ek yük kabaca iki model daha demektir; bu, yaklaşık 0,8 ms'lik bir ek süredir. Bu bir tahmindir, ölçülmedi; ama sonucu değiştirmeyecek kadar küçüktür. 640 piksel ölçeğinde ise bu ek yük ağın kendisi kadar büyür ve ayrıca değerlendirilmelidir.

Şekil 80.8, eşiğe bağlı davranışı gösterir. Sol panelde kapsama, eşik arttıkça düşer; iki kural da yüksek eşiklerde hızla kapsama kaybeder. Sağ panelde OOD'deki yanlış alarm, simetrik log eksende gösterilmiştir. Kesikli çizgi korumasız taban değerdir. Tohum uyumu eğrisi her eşikte tek skor eğrisinin altında kalır: aynı eşikte daha az yanlış alarm verir, ama kapsaması da daha düşüktür. İki eğri arasındaki asıl soru, hangi kapsama kaybının kabul edilebilir olduğudur.

![Şekil 80.8: Skor eşiğine göre kapsama (test) ve OOD'de görüntü başına yanlış alarm](gorseller/b80_guvence.png)

## 80.8 İzleme: kayma ne zaman alarm olur?

Model sahaya çıktığında dünya değişir. Kamera yaşlanır, hava kararır, sis gelir, yeni tip bir İHA görünür. Model bu değişiklikleri kendi kendine fark etmez; kötüleşir ve bunu bir hata mesajıyla bildirmez. Bölüm 77.9 ve 77.10'da bu sessiz bozulmayı, drift adıyla anlatmıştık. Burada bu fikri uçtan uca bağlıyoruz: hangi ölçüleri izleyeceğiz, hangi eşiklerde alarm vereceğiz ve alarm geldiğinde ne olacak.

Üç sinyal izliyoruz. Birincisi girdi kayması: her görüntünün ortalama parlaklığı, referans pencerelerdeki dağılıma göre PSI ile karşılaştırılır (Bölüm 77.10'daki PSI tanımı). İkincisi skor kayması: her görüntünün en yüksek tespit skoru, referans dağılımına göre iki örnekli KS testiyle karşılaştırılır. Üçüncüsü performans: mAP@0,5, gerçek etiketlerle hesaplanır, ama etiketler gecikmeli gelir. Bu gecikme gerçekçidir; bir İHA görüntüsünün doğru etiketi genellikle sonradan bir insan tarafından yazılır.

Girdi ve skor sinyalleri etiketsizdir; yani her pencerede hemen hesaplanabilirler. Performans sinyali ise en güvenilir olanıdır ama en geç gelendir. Bu üçlünün birlikte kullanılması, Bölüm 77.10'daki "etiketsiz kayma yakalanır, kavram kayması etiketle yakalanır" ayrımının uygulamasıdır.

Simülasyon altmış pencere (her biri 200 sahne) üretir. Pencere 0 ile 19 referanstır ve yalnızca nominal veri içerir. Pencere 20'den itibaren kayma karışımı kademeli olarak artar: pencere 20'de sıfır, pencere 30'da bir. Bir pencerede her sahne, karışım oranı kadar olasılıkla kayma ayarından üretilir. Böylece kayma ani değil, bir sis ya da bir ışık değişimi gibi kademeli olur.

Kodun ilk parçası sabitleri, PSI fonksiyonunu ve kayma oranını tanımlar.

```python
# -*- coding: utf-8 -*-
# b80_izleme.py: operasyonel akista kayma izleme ve yeniden egitim
# tetigi. 60 pencere x 200 sahne. Pencere 0-19 referans (nominal),
# 20-30 arasinda kayma kademeli artar, 30 ve sonrasi tam kayma.
# Girdi kaymasi: PSI (girdi parlakligi). Skor kaymasi: KS (en yuksek
# tespit skoru). Performans: mAP@0.5, 3 pencere gecikmeli etiketle.
import os
import numpy as np
import torch
from scipy.stats import ks_2samp
from b80_veri import sahne, veri_seti, EGITIM, DRIFT
from b67_04_yolo_mini import (
    MiniYolo,
    tahmin,
    degerlendir,
    hedef_tensorleri,
    egit,
)

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
PENCERE = 60
N = 200  # pencere basina sahne
REF = range(0, 20)  # referans pencereler (nominal)
GECIKME = 3  # etiket gecikmesi (pencere)
PSI_ESIK, KS_ESIK, PERF_DUS = 0.2, 0.01, 0.05


def psi(ref, yeni, kutu=10):
    """Populasyon Kararlilik Indeksi (Bolum 77.10 ile ayni)."""
    kenar = np.quantile(ref, np.linspace(0, 1, kutu + 1))
    kenar[0], kenar[-1] = -np.inf, np.inf
    e = np.histogram(ref, kenar)[0] / len(ref)
    a = np.histogram(yeni, kenar)[0] / len(yeni)
    e, a = np.clip(e, 1e-4, None), np.clip(a, 1e-4, None)
    return float(np.sum((a - e) * np.log(a / e)))
```

Kodun ikinci parçası pencere üretimini ve tohum seçimini tanımlar. Her pencerenin kendi tohumu (1000 + w) vardır; bu, herhangi bir pencerenin bağımsız yeniden üretilebilmesini sağlar.

```python
def alpha(w):
    """Kayma karisim orani: 0 (referans), 1 (tam kayma)."""
    return float(np.clip((w - 20) / 10.0, 0.0, 1.0))


def pencere(w):
    """Pencere w: N sahne. Her sahne alpha olasiligiyla DRIFT'ten."""
    rng = np.random.default_rng(1000 + w)
    a = alpha(w)
    X = np.zeros((N, 1, 96, 96), np.float32)
    Y = []
    for i in range(N):
        ayar = DRIFT if rng.uniform() < a else EGITIM
        img, nes = sahne(rng, ayar)
        X[i, 0] = img
        Y.append(nes)
    return X, Y
```

Üçüncü parça ana fonksiyonun başıdır: model yüklenir, pencereler üretilir, her pencerede tahmin ve mAP hesaplanır. Referans istatistikleri (girdi parlaklığı ve skor dağılımı) pencere 0 ile 19 arasından çıkarılır.

```python
def main():
    model = MiniYolo().to("cuda")
    model.load_state_dict(
        torch.load(os.path.join(KLASOR, "yolo_t1.pt"))
    )
    model.eval()
    veriler, tahminler = [], []
    for w in range(PENCERE):
        X, Y = pencere(w)
        veriler.append((X, Y))
        tahminler.append(tahmin(model, X))
    parlaklik = [v[0].reshape(N, -1).mean(1) for v in veriler]
    skor = [
        np.array([d[1].max() if len(d[1]) else 0.0 for d in t])
        for t in tahminler
    ]
    map_w = [
        degerlendir(tahminler[w], veriler[w][1])[0]
        for w in range(PENCERE)
    ]
    ref_p = np.concatenate([parlaklik[w] for w in REF])
    ref_s = np.concatenate([skor[w] for w in REF])
    ref_map = float(np.mean([map_w[w] for w in REF]))
    satirlar = []
    art_ust = 0
    tetik = None
    for w in range(PENCERE):
        p = psi(ref_p, parlaklik[w])
        ks_p = ks_2samp(ref_s, skor[w]).pvalue
        g_alarm = p > PSI_ESIK
        s_alarm = ks_p < KS_ESIK
        # performans alarmi: etiketler GECIKME pencere sonra gelir
        perf = None
        if w - GECIKME >= 0:
            perf = map_w[w - GECIKME]
        p_alarm = perf is not None and (ref_map - perf) > PERF_DUS
        alarm = g_alarm or s_alarm
        art_ust = art_ust + 1 if alarm else 0
```

Dördüncü parça, her pencerede alarmları ve yeniden eğitim tetiğini belirler. Tetik kuralı basittir: girdi veya skor alarmı iki ardışık pencerede gelirse tetik çalışır ve insan onayına gönderilir. Performans alarmı ise etiket geldikçe devreye girer ve tetiğe dahil edilmez; onun rolü, tetiğin doğru olduğunu teyit etmektir.

```python
        if tetik is None and art_ust >= 2:
            tetik = w  # iki ardisik alarm -> yeniden egit
        satirlar.append(
            (
                w,
                alpha(w),
                p,
                ks_p,
                map_w[w],
                int(g_alarm),
                int(s_alarm),
                int(p_alarm),
            )
        )
        print(
            "pencere %2d a=%.2f PSI=%.3f KS_p=%.4f mAP=%.4f "
            "girdi=%d skor=%d perf=%d"
            % (
                w,
                alpha(w),
                p,
                ks_p,
                map_w[w],
                g_alarm,
                s_alarm,
                p_alarm,
            )
        )
    print("referans mAP (0-19) = %.4f" % ref_map)
    print("yeniden egitim tetigi: pencere", tetik)
    # Yeniden egitim: karisik (nominal + sert olmayan kayma) veriyle
    if tetik is not None:
        Xa, Ya = veri_seti(1500, seed=2001, ayar=EGITIM)
        Xb, Yb = veri_seti(1500, seed=2002, ayar=DRIFT)
        Xr = np.concatenate([Xa, Xb])
        Yr = Ya + Yb
        ptr, otg, ctr = hedef_tensorleri(Yr)
        yeni = egit(11, Xr, ptr, otg, ctr, epoch=60)
```

Beşinci parça, tetik çalıştıysa yeni bir modeli (eğitim ve kayma karışımı) eğitir ve tetikten sonraki pencerelerde eski ve yeni modelin mAP'lerini karşılaştırır. Son olarak sonuçları CSV'ye yazar.

```python
        yeni_map = {}
        for w in range(tetik, PENCERE):
            yeni_map[w] = degerlendir(
                tahmin(yeni, veriler[w][0]), veriler[w][1]
            )[0]
        print(
            "yeni model, pencere %d..%d ort. mAP = %.4f"
            % (tetik, PENCERE - 1, np.mean(list(yeni_map.values())))
        )
        print(
            "eski model ayni pencerelerde = %.4f"
            % np.mean([map_w[w] for w in range(tetik, PENCERE)])
        )
    else:
        yeni_map = {}
    with open(
        os.path.join(VERI, "b80_izleme.csv"), "w", encoding="utf-8"
    ) as f:
        f.write(
            "pencere,alpha,psi,ks_p,map_eski,girdi_alarm,"
            "skor_alarm,perf_alarm,map_yeni\n"
        )
        for s in satirlar:
            w = s[0]
            yn = "%.4f" % yeni_map[w] if w in yeni_map else ""
            f.write(
                "%d,%.2f,%.4f,%.6f,%.4f,%d,%d,%d,%s\n"
                % (s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], yn)
            )


if __name__ == "__main__":
    main()
```

```term
$ python b80_izleme.py
pencere  0 a=0.00 PSI=0.095 KS_p=0.4158 mAP=0.9399 girdi=0 skor=0 perf=0
pencere  1 a=0.00 PSI=0.056 KS_p=0.4934 mAP=0.9369 girdi=0 skor=0 perf=0
...
pencere 20 a=0.00 PSI=0.025 KS_p=0.5542 mAP=0.9190 girdi=0 skor=0 perf=0
pencere 21 a=0.10 PSI=0.070 KS_p=0.2996 mAP=0.9356 girdi=0 skor=0 perf=0
pencere 22 a=0.20 PSI=0.059 KS_p=0.1877 mAP=0.9322 girdi=0 skor=0 perf=0
pencere 23 a=0.30 PSI=0.220 KS_p=0.0552 mAP=0.8746 girdi=1 skor=0 perf=0
pencere 24 a=0.40 PSI=0.296 KS_p=0.0044 mAP=0.9100 girdi=1 skor=1 perf=0
pencere 25 a=0.50 PSI=0.303 KS_p=0.0286 mAP=0.9190 girdi=1 skor=0 perf=0
pencere 26 a=0.60 PSI=0.561 KS_p=0.0001 mAP=0.9061 girdi=1 skor=1 perf=1
pencere 27 a=0.70 PSI=0.887 KS_p=0.0013 mAP=0.8681 girdi=1 skor=1 perf=0
pencere 28 a=0.80 PSI=1.141 KS_p=0.0013 mAP=0.8796 girdi=1 skor=1 perf=0
pencere 29 a=0.90 PSI=2.221 KS_p=0.0000 mAP=0.8573 girdi=1 skor=1 perf=0
pencere 30 a=1.00 PSI=3.653 KS_p=0.0000 mAP=0.9098 girdi=1 skor=1 perf=1
...
referans mAP (0-19) = 0.9369
yeniden egitim tetigi: pencere 24
yeni model, pencere 24..59 ort. mAP = 0.9090
eski model ayni pencerelerde = 0.8742
```

Çıktıda `...` ile gösterilen satırlar kısaltmadır; tam çıktı CSV dosyasında bulunur. Çıktı, her pencerenin PSI, KS p değeri, mAP değeri ve üç alarm bayrağını verir. Alarm bayrakları girdi, skor ve performans için 1 ya da 0'dır.

### Ne zaman alarm verdi?

Tablo, kayma başlangıcından (pencere 20) sonra ilk alarmların geldiği pencereleri özetler.

| Pencere | Alfa | PSI | KS p | mAP | Olay |
|---|---|---|---|---|---|
| 20 | 0,00 | 0,025 | 0,554 | 0,919 | Kayma başlıyor (karışım sıfır) |
| 22 | 0,20 | 0,059 | 0,188 | 0,932 | Hâlâ alarm yok |
| 23 | 0,30 | 0,220 | 0,055 | 0,875 | PSI alarmı (girdi) |
| 24 | 0,40 | 0,296 | 0,004 | 0,910 | KS alarmı (skor); iki ardışık alarm, tetik |
| 26 | 0,60 | 0,561 | 0,0001 | 0,906 | Performans alarmı (etiketli pencere 23) |
| 30 | 1,00 | 3,654 | 0,000 | 0,910 | Tam kayma |

Referans mAP (pencere 0 ile 19 ortalaması) 0,937'dir. Performans alarmı, etiketli pencere 23'ün mAP'i (0,875) referansın 0,05 altına düştüğü için devreye girdi; düşüş 0,062'dir. Girdi alarmı pencere 23'te, skor alarmı ise pencere 24'te geldi. Kayma 20'de başladığı için tespit gecikmesi üç pencere oldu. Nominal pencerelerde (0 ile 22 arası) hiçbir alarm yoktur: yanlış alarm sayısı sıfırdır. R13 bu iki koşulu da geçti (gecikme <= 5 pencere, nominal alarm = 0).

Şekil 80.9, üç sinyali ve yeni modelin performansını birlikte gösterir. Gölgeli bölge kayma karışımının olduğu pencereleri (20 ile 30), kesikli çizgi ise tetiği (pencere 24) işaretler. PSI, kayma başladıktan sonra sert biçimde yükselir; KS p değeri pencere 26'dan itibaren neredeyse sıfıra düşer. Alt panelde, eski modelin mAP'i tam kayma altında 0,87 civarındadır; yeni model ise 0,91 civarında kalır.

![Şekil 80.9: Kayma izleme: PSI, KS p değeri ve eski ile yeni modelin mAP'i](gorseller/b80_drift.png)

### Yeniden eğitim: iyimser bir üst sınır

Tetikten sonra yeni bir model eğitildi. Eğitim verisi, yarısı nominal, yarısı kayma kümesinden (üreticinin aynı ayarlarından) oluşur. Pencere 24'ten 59'a kadar yeni modelin ortalama mAP'i 0,909, eski modelin ise 0,874'tür. Bu bir iyileşme, ama dürüst olmak gerekirse, bu sonuç iyimserdir. Simülasyonda kaymanın üretici tanımı biliniyor ve yeniden eğitim verisi aynı üreticiden geliyor. Gerçek bir sahada yeni model, yeni işaretlenmiş operasyonel veriyle eğitilmeli ve ayrı bir kümede ölçülmelidir. Bu sayı, yeniden eğitimin ne kadar kurtardığı değil, yeterli veri varsa neyin mümkün olabileceği hakkında bir üst sınırdır.

Bu noktada yeniden eğitim bir kalite kapısından (Bölüm 77.7) geçmelidir: yeni model, mevcut modelden doğrulama kümesinde iyi olmalı, kayma kümesinde kötüleşmemeli ve dağıtım öncesi insan onayını almalıdır. Bu bölümde kalite kapısını ayrıca kodlamadık; ama tetiğin çıktısı bir kapıya girmeli, doğrudan üretime gitmemelidir.

## 80.9 Doğrulama raporu: kabul ölçütleri ve model kartı

Gereksinimleri 80.1'de yazdık. Şimdi her birini ölçtüğümüz değerle karşılaştırıyoruz. Tabloda üç sütun var: ölçülen değer, eşik ve sonuç. Sonuç sütunu iki kelimeden biridir: GEÇTİ ya da KALDI. Bir ölçüm yapılamadıysa "ÖLÇÜLMEDİ" yazarız; bu, geçmek anlamına gelmez.

Burada hangi kalemin neden kaldığını açıkça yazmak önemlidir. Bir mühendislik raporunda kalanları gizlemek, geçenleri vurgulamaktan daha zararlıdır: okuyan, sistemin hangi koşullarda güvenilmez olduğunu bilmeden kullanır.

| Kod | Gereksinim | Ölçülen | Eşik | Sonuç |
|---|---|---|---|---|
| R1 | Nominal mAP@0,5 | 0,937 ± 0,004 | >= 0,90 | GEÇTİ |
| R2 | Kayma mAP@0,5 | 0,875 ± 0,006 | >= 0,80 | GEÇTİ |
| R3 | Test MOTA | 0,814 | >= 0,90 | KALDI |
| R4 | IDSW / GT (test) | 24 / 1 735 = %1,4 | <= %1 | KALDI (nokta tahmini; %95 aralık eşiği kapsıyor) |
| R5 | int8 mAP@0,5 kaybı (test) | 1,1 puan | <= 2 puan | GEÇTİ |
| R6 | int8 mAP@[0,5:0,95] kaybı (test) | 9,5 puan | <= 5 puan | KALDI |
| R7 | Uçtan uca p95, 96 px, 4 iş p. | 1,09 ms | <= 33 ms | GEÇTİ (yalnız 96 px) |
| R8 | 640 px ağın çıkarım p95, 4 iş p. | 3,08 ms | <= 33 ms | GEÇTİ (yalnız ağ) |
| R8b | 640 px uçtan uca p95 | ÖLÇÜLMEDİ | <= 33 ms | ÖLÇÜLMEDİ |
| R9 | int8 model dosyası | 71 173 bayt | <= 1 MB | GEÇTİ |
| R10 | En büyük ara tampon, 96 px | 36 864 bayt | <= 256 KB | GEÇTİ |
| R10b | En büyük ara tampon, 640 px | 1 638 400 bayt | <= 256 KB | KALDI |
| R11 | OOD yanlış alarm azalması | Tek skor %79, tohum uyumu %96 | >= %50 | GEÇTİ |
| R12 | Test kapsama kaybı | Tek skor 3,2 puan, tohum uyumu 7,7 puan | <= 5 puan | GEÇTİ (tek skor) / KALDI (tohum uyumu) |
| R13 | Kayma alarmı gecikmesi ve nominal alarm | 3 pencere, 0 alarm | <= 5, 0 | GEÇTİ |
| R14 | ONNX ile PyTorch kutu farkı | 8,0e-6 | <= 1e-4 | GEÇTİ |

Sayım dürüst olmak gerekirse şöyle: on bir ölçüm geçti (R12'de yalnızca tek skor kuralı için). Beş kalem kaldı: test MOTA (R3), kimlik değişimi (R4), int8 lokalizasyon kaybı (R6), 640 px ara tamponu (R10b) ve tohum uyumu kuralının kapsama kaybı (R12). Bir kalem ölçülmedi: 640 px uçtan uca gecikme (R8b).

R3 ve R4'ün kaldığı nedenleri 80.5'te gösterdik: kaçırmalar (kenar ve küçük hedefler), kuş benzeri OOD nesnelerinden gelen yanlış izler ve kesişmede kimlik değişimi. R6'nın kaldığı nedenin bir hipotezi var (kafa katmanında üstel kodlama ve kuantizasyon hatası), ama bunu doğrulamadık. R10b ise bir mimari seçimin sonucudur: 640 pikselde ara tampon, mikrodenetleyici sınıfı belleğin dışındadır.

Kalan sorunlar bir "tamamlandı" işaretini hak etmez. Bu, sistemin hangi koşullarda kullanılabileceğini belirleyen bir çıktıdır. Operatöre verilecek bir sistemin sınırları bu tabloda yazılı olmalıdır.

### Model kartı

Model kartı, bir modelin ne için yapıldığını, neyle eğitildiğini, nerede güvenilmez olduğunu ve kimin sorumlu olduğunu tek bir sayfada anlatan belgedir. Bölüm 77'deki izlenebilirlik düşüncesinin son adımıdır. Aşağıdaki kart, bu sistemin dedektörü için yazılmıştır.

| Alan | Değer |
|---|---|
| Amaç | Sentetik gözetleme videosunda hava hedeflerini algılamak ve izlemek; operatöre iz listesi ve güvence işareti sunmak |
| Kapsam dışı | Hedef seçimi, silahlandırma, angajman ve sınıflandırmanın yerine geçen karar; insan operatörün yerine karar verme |
| Mimari | MiniYolo: 4 konvolüsyon bloğu (BatchNorm ve ReLU), 1 x 1 kafa; 61 440 parametre; 12 x 12 ızgara, 2 anchor, 3 sınıf |
| Girdi | 96 x 96 piksel, gri tonlu, değerler 0..1 |
| Eğitim verisi | Sentetik, 3 000 sahne, tohum 0, EGITIM ayarı (aydınlatma, gürültü, bulanıklık, ölçek) |
| Eğitim | AdamW, en yüksek öğrenme oranı 2e-3, OneCycle, 60 epoch, yığın 64; tohumlar 1, 2, 3; GPU RTX 3060 (6 GB) |
| Ölçüm | Nominal test (500 sahne), kayma (500), sert kayma (500), OOD (500, kuş eklenmiş), videolar (5 x 120 kare) |
| Bilinen sınırlar | Sentetik veri; 96 px çözünürlük; üç sınıf; kuş benzeri OOD yalnızca bir şekil ailesi; kayma üreticinin tanımıyla simüle edildi |
| Bilinen hatalar | int8'de kutu hassasiyeti düşer (R6); kenar ve küçük hedefler kaçırılır; kuşlar FP üretir; kesişmede IDSW |
| Güvence | Tohum uyumu ya da skor eşiği ile "doğrulat" işareti; eşikler yalnızca doğrulama kümesinde seçildi |
| Sürüm izi | yolo_t1.pt ve yolo_int8.onnx; int8 model SHA-256 özeti (ilk 16 karakter) 34f1c9ef6dac1a5b |
| Ortam | Windows 11; Python 3.12.10; PyTorch 2.6.0+cu124; ONNX Runtime 1.25.1; ONNX 1.23.2; NumPy 2.3.5 |
| Sorumlu | Proje sahibi; yeniden eğitim yalnızca insan onayıyla yayınlanır |

Model kartındaki "bilinen hatalar" satırı, bir modelin kendi raporudur. Kullanıcının beklentisini modelin gerçek kapasitesine uydurmak için vardır. Bu satır olmadan okuyan, modelin her sahnede çalıştığını varsayar.

### Deney kaydı

Son olarak Bölüm 77.5'teki deney takipçisine kayıt. Her tohum için bir deney satırı, parametreler, metrikler ve model dosyasının özeti yazılır. Bu kayıt, bir sonraki koşuda sonuçların neden değiştiğini sorgulamamızı sağlar.

```python
# -*- coding: utf-8 -*-
# b80_kayit.py: ch80 deney sonuclarini Bolum 77'nin deney takipcisine
# (SQLite) yazar. Her tohum icin bir deney: parametreler, metrikler,
# model dosyasi artefakt olarak SHA-256 ozetiyle kaydedilir.
import csv
import os
from b77_takip import Takip

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def satirlar():
    with open(
        os.path.join(VERI, "b80_detektor.csv"), encoding="utf-8"
    ) as f:
        return list(csv.DictReader(f))
```

Kayıt betiği, `Takip` sınıfını Bölüm 77'den kullanır. Kodun ikinci parçası üç tohum için deneyi ve metriklerini yazar.

```python
def main():
    db = Takip(os.path.join(KLASOR, "deney.db"))
    rows = satirlar()
    for seed in (1, 2, 3):
        ad = "b80_yolo_t%d" % seed
        d = db.baslat(
            ad,
            "b80_veri:egitim3000:seed0",
            KLASOR,
            "torch-2.6.0+cu124",
        )
        db.parametre(
            d,
            {
                "tohum": seed,
                "epoch": 60,
                "bs": 64,
                "lr_max": 2e-3,
                "egitim_sahne": 3000,
            },
        )
        for r in rows:
            if r["yontem"] == "cnn" and int(r["tohum"]) == seed:
                db.metrik(d, r["kume"] + "_map50", r["map50"])
                db.metrik(d, r["kume"] + "_map5095", r["map5095"])
        db.artefakt(d, os.path.join(KLASOR, "yolo_t%d.pt" % seed))
    print(
        "kayit sayisi:",
        db.db.execute("SELECT COUNT(*) FROM deney").fetchone()[0],
    )
    for satir in db.sirala("test_map50"):
        print(
            "id=%d ad=%s test_map50=%.4f"
            % (satir[0], satir[1], satir[5])
        )
```

Son parça betiğin giriş noktasıdır; sıralanmış sonuçları yazdırır.

```python
if __name__ == "__main__":
    main()
```

```term
$ python b80_kayit.py
kayit sayisi: 3
id=2 ad=b80_yolo_t2 test_map50=0.9407
id=1 ad=b80_yolo_t1 test_map50=0.9390
id=3 ad=b80_yolo_t3 test_map50=0.9325
```

Çıktıda deneyler test mAP@0,5 değerine göre azalan sırada listelenir. Üç tohum arasındaki sıralama, ortalamayı değiştirmez; yalnızca sonuçların ne kadar dağıldığını gösterir. Bu sıralamaya bakarak "en iyi tohumu" seçmek, bir test kümesine göre seçim yapmak olur. Edge hattına yalnızca tohum 1 aktarıldı. Tohum uyumu kuralını edge'de kullanmak için tohum 2 ve 3'ün de ONNX'e aktarılması ve birlikte ölçülmesi gerekir. Bu bölümde tohum uyumu yalnızca PyTorch ile ölçüldü; edge karşılığı açık bir iştir.

## 80.10 Kapanış: kitabın tamamı bu sistemde nerede?

Bu sistemi kurarken kitabın on altı kısmının hepsine dokunduk, ama bazılarına diğerlerinden çok daha fazla. Şekil 80.10, her kısmın sistemdeki karşılığını gösterir. Haritayı okurken şunu hatırlayın: bir kısmın karşılığı, o kısmın yalnızca bir sayfasından değil, o kısımdaki zihinsel modelden gelir.

![Şekil 80.10: Kitabın 16 kısmının bitirme sistemindeki karşılığı](gorseller/b80_kitap_haritasi.png)

Veri yapıları ve algoritmalar (Kısım III ve IV) sistemin en yoğun kullanılan kısımlarıdır. Kutu listeleri, izler ve bağlı bileşenler (Bölüm 11'deki graf düşüncesi, Bölüm 67'deki eşleştirme) ile NMS ve Macar eşleştirmesi, takip ve tespit kodunun omurgasıdır. Bölüm 12'deki Big-O düşüncesi, her karede kaç kutuyla karşılaştırma yapıldığını hesaplamamızı sağladı; NMS'in karmaşıklığının kutu sayısıyla nasıl büyüdüğünü bu düşünceyle anladık.

Sayısal kısımlar (Kısım XII ve XIV) sistemin doğruluk dilini oluşturur. IoU, Kalman tahmini, PSI ve KS testi, MOTA'nın formülü ve tohumlar arası belirsizlik, Bölüm 49 ve 57'nin araçlarıdır. Kısım XV'in (derin öğrenme) ağı ve eğitimi, Kısım XVI'nın (ML mühendisliği) kuantizasyonu, güvence ve izlemesi bu iki kısmın üzerine kuruludur.

Sistemin en az görünen ama en çok iş yapan kısmı işletim sistemi ve iş parçacıklarıdır. Kare hattında iş parçacığı sayısını (Kısım VI ve XIII) değiştirmek, gecikmeyi değiştirdi; bu, Bölüm 26 ve 53'teki paralelliğin pratikte nasıl görüneceğini göstermesi açısından öğreticiydi. Ağ katmanı (Kısım VII) ise bu sistemde yalnızca kavramsaldır: sensör ve operatör arayüzü gerçek bir ağ üzerinden çalışmaz. Bu, bir eksiklik değil, bilinçli bir kapsam sınırıdır; ama gerçek bir sistemde ağ, gecikme ve kayıp hesaplarının bu hatta girmesi gerekir.

## Bu sistemi yapay zekâ olmadan kurabilmek için neler bilinmeli?

Bu bölümdeki her adımı bir yapay zekâ aracı olmadan tekrarlayabilmek, kitabın asıl başarı ölçütüdür. Aşağıdaki kontrol listesi bunu bir sınama gibi kullanmanızı sağlar. Her maddeyi kağıtta, ekransız ve kaynaksız yapabiliyor musunuz, sorusunu sorun.

1. Bir tespit kutusunun IoU değerini ve iki kutunun NMS ile nasıl bastırıldığını elle hesaplayabiliyor musunuz?
2. Beş tahminlik bir listeden PR eğrisini ve AP değerini sıfırdan çıkarabiliyor musunuz?
3. Kalman filtresinin tahmin ve güncelleme adımlarını, sabit hız modeliyle bir kutu için yazabiliyor musunuz?
4. Üç izi üç tespitle Macar ya da açgözlü yöntemle eşleştirip MOTA ve IDSW'yi sayabiliyor musunuz?
5. BatchNorm'un Conv'a nasıl katlandığını, formülünü türeterek gösterebiliyor musunuz?
6. Simetrik int8 kuantizasyonunda ölçek ve sıfır noktasını bir tensörden hesaplayabiliyor musunuz?
7. Bir ağın kare başına gecikmesini, ısınma ve p50/p95 ile doğru ölçebiliyor musunuz?
8. PSI ve KS değerlerini bir referans ve bir pencere için el ile hesaplayabiliyor musunuz?
9. Bir değerlendirme sonucunun neden test kümesinde değil doğrulama kümesinde seçilmesi gerektiğini bir mülakatta anlatabiliyor musunuz?
10. Bir mAP farkının gürültüden ayrılması için kaç tohuma ihtiyaç olduğunu tartışabiliyor musunuz?
11. Bir gereksinimi, ölçülebilir bir kabul ölçütüne ve bir test planına çevirebiliyor musunuz?
12. Bir FMEA tablosunu bir sistem için, en az altı hata modu ile yazabiliyor musunuz?

Bu listedeki her madde, kitabın bir bölümüne dayanır. Bir maddede takılırsanız, o bölüme dönün; sistemi kurmak, bu parçaları birleştirmekten ibarettir.

## Açık kalanlar: dürüst bir liste

Bölüm 39'da bir söz verdik: Bölüm 80'de simülatör ile gerçek donanım arasındaki farkı ölçeceksiniz. Bu sözü tam olarak tutamadık. Gerçek bir gömülü kart yoktu; ölçüm dizüstü bilgisayarın CPU'sunda yapıldı. Bu bir vekil ölçümdür ve gerçek donanım farkı hâlâ ölçülmedi. Bunu, Kendin Yap bölümündeki ek alıştırmalardan birinde, bir STM32 kartında aynı ağı çalıştırarak kendiniz yapabilirsiniz.

Diğer açık kalanlar da açıkça yazılmalıdır:

- Gerçek İHA verisi yok. Tüm sayılar sentetik veriye aittir ve gerçek bir kamerada farklı olabilir.
- Cortex-M ve Jetson ölçülmedi. Cortex-M için bellek ve işlem hesabı yapıldı, Jetson için yalnızca genel bilgi var.
- 640 piksel için uçtan uca gecikme ölçülmedi; kod çözme ve takip bu boyutta yeniden ölçülmeli.
- int8 kuantizasyonunda kutu hassasiyeti düşüyor (R6). Hipotezimiz kafa katmanıdır, ama bu doğrulanmadı.
- Tohum uyumu kuralı yalnızca PyTorch ile ölçüldü; edge'de üç modelin birlikte ölçümü yapılmadı.
- Kayma simülasyonu, üreticinin kendi tanımıyla yapıldı; gerçek kaymalar bu kadar düzenli olmaz.
- Yeniden eğitimin kazancı iyimserdir; gerçek bir sahada yeni etiketli veriyle yeniden ölçülmeli.

Son bir not. Bu sistemin bir savunma sanayii ürününe dönüşmesi için sertifikasyon yolu, yalnızca teknik bir süreç değildir. Havacılıkta yazılım ve donanım için DO-178C ve DO-254 gibi standartlar bulunur (genel bilgi, bu bölümde uygulanmadı). Model yeniden eğitimi, güvence kuralları ve izleme, bu standartların gerektirdiği izlenebilirlik ve doğrulama kanıtlarıyla ilişkilidir. Bölüm 78 ve 77.12, bu konuya giriş niteliğindedir.

## Çözümlü Örnekler

Dört örnek, zorluk sırasına göre (★, ★★, ★★, ★★★) sıralanmıştır. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntü, iyileştir, doğrula. Doğrulama adımında bir tablo ile kendi sonucunuzu elle kontrol edersiniz. Örneklerdeki sayılar bu bölümün ölçümlerinden alınmıştır; her yerde kaynağını yazdık.

### Örnek 1 (★): Kare bütçesini bileşenlere dağıtmak

Bir gözetleme sistemi saniyede 30 kare işlemek zorundadır. Bu, her kare için en fazla 33 ms demektir. Sistemin 96 piksel ölçümünde int8, 4 iş parçacığı ile p50 toplamı 0,747 ms'dir. Bütçenin ne kadarının kullanıldığını ve 640 pikselde ne olabileceğini bilmek istiyoruz.

**Adım 1 — Anla.** Soru iki parçalıdır. Birincisi bugünkü durumda bütçenin ne kadarı kullanılıyor. İkincisi 640 piksele geçersek bütçe nasıl değişir. İkinci soru bir tahmindir; ölçüm yapılmadan cevaplanamaz, ama bir tahminin dürüst yazılması gerekir.

**Adım 2 — Örnekle.** 96 pikselde ölçülen bileşenler şunlardır (p50, ms): ön işleme 0,019, çıkarım 0,115, son işleme 0,288, takip 0,300, güvence 0,002. Bunların toplamı 0,724 ms eder. Ölçülen toplam p50 ise 0,747 ms'dir. Fark, medyanların toplamının toplamın medyanına eşit olmamasından gelir; bu bir hata değil, bir istatistiksel gerçektir.

**Adım 3 — Kaba çöz.** 96 pikselde bütçenin yüzde 2,3'ü kullanılıyor (0,747 / 33). Bu kadar büyük bir boşluk, 640 pikselde gelişmenin mümkün olduğunu gösterir. Ama 640'ta son işlemenin ne yapacağını bilmiyoruz: ızgara 12 x 12'den 80 x 80'e çıkar, yani hücre sayısı yaklaşık 44 kat artar. İki varsayım seçelim. Varsayım A: son işleme ve takip değişmez. Varsayım B: son işleme hücre sayısıyla doğru orantılı büyür.

**Adım 4 — Örüntü.** Ağın çıkarım süresi 640'ta ölçüldü: p50 2,83 ms. Bu bir ölçümdür, varsayım değildir. Örüntü şudur: ağ ile son işleme aynı oranda büyümez. Ağın büyümesi konvolüsyonun doğasında vardır (yaklaşık 44 kat MAC, ama donanım bunu paralel yapar); son işleme ise Python döngüsüyle yazılmıştır ve doğrusal büyür.

**Adım 5 — İyileştir.** Varsayım B'nin sonucu, bütçeyi zorlar. Bunu azaltmanın yolu son işlemeyi vektörleştirmektir (Bölüm 56'daki NumPy vektörleştirme). Ama önce ölçmek gerekir: son işlemeyi 80 x 80 ızgara ile bir kez çalıştırıp süreyi görmeden kod yazmayın. Bölüm 75.2'deki disiplin, önce ölçümü ister.

**Adım 6 — Doğrula.** Aşağıdaki tablo iki varsayımı yan yana koyar. Ağın 2,83 ms'lik değeri ölçümdür; son işleme için A'da 0,288, B'de 0,288 x 44,4 = 12,8 ms alınır; takip sabit kalır.

| Senaryo | Ağ | Son işleme | Takip | Diğer | Toplam | Bütçe kullanımı |
|---|---|---|---|---|---|---|
| 96 px (ölçüm) | 0,115 | 0,288 | 0,300 | 0,021 | 0,747 | %2,3 |
| 640 px, A | 2,83 | 0,288 | 0,300 | 0,021 | 3,44 | %10,4 |
| 640 px, B | 2,83 | 12,8 | 0,300 | 0,021 | 15,95 | %48,3 |

Sonuç: Varsayım B bile bütçede kalıyor. Ancak p95 değeri ölçülmediği için kesin bir karar veremeyiz. Bu tablo, "bütçe tutuyor mu" sorusunun cevabının, hangi varsayımla yanıtlandığına bağlı olduğunu gösterir. Bir mühendis bu cevabı yazarken iki varsayımı da yazar ve hangisinin ölçülmesi gerektiğini belirtir.

**Bunu AI'sız yazabilir misin?** Ön işleme 96 pikselde 0,019 ms, son işleme 0,288 ms olsun. Ağ 640 pikselde 4 ms, son işleme hücre sayısıyla doğrusal büyüsün ve takip sabit kalsın. Toplamı ve 33 ms bütçesindeki payını hesapla.

### Örnek 2 (★★): Bir gereksinimi ölçülebilir kabul ölçütüne çevirmek

Gereksinim şudur: "Takip sırasında kimlikler kararlı olmalı." Bu cümle ölçülemez. Kararlı ne demek? Kaç kimlik değişimi kabul edilebilir? Bu örnekte bu cümleyi bir test tasarımına çevireceğiz.

**Adım 1 — Anla.** "Kararlı" kelimesi bir ölçü değildir. Ölçü, kimlik değişimi sayısının gerçek nesne-kare sayısına oranı olabilir (IDSW / GT). Bu, Bölüm 67.17'deki tanımdır. Eşiği de seçmemiz gerekir: bu bölümde yüzde 1.

**Adım 2 — Örnekle.** Test kümesinde 1 735 gerçek nesne-kare ve 24 kimlik değişimi ölçtük. Oran 24 / 1 735 = 0,0138, yani yüzde 1,38. Eşiğin üstünde görünüyor.

**Adım 3 — Kaba çöz.** Bu bir nokta tahmini. Bir nokta tahmini yalnızca bir sayıdır; belirsizliğini bilmeden karar vermek, bir zarın tek bir atışına bakıp zarın hilekâr olduğuna karar vermek gibidir. Kaba bir güven aralığı için binom yaklaşımına (Wald) bakalım: standart hata = karekök(p (1 - p) / n).

**Adım 4 — Örüntü.** Kimlik değişimleri, kesişme anlarında yoğunlaşır (Şekil 80.5). Yani değişimler bağımsız rastgele olaylar değildir; kümelenmişlerdir. Wald aralığı bağımsızlık varsayar, dolayısıyla gerçek belirsizlik daha geniş olabilir. Bu, aralığı bir alt sınır olarak okumamız gerektiği anlamına gelir.

**Adım 5 — İyileştir.** Kararı netleştirmek için iki şey yapılabilir: GT sayısını artırmak (daha fazla video) ve kesişme sahnelerini ayrı bir alt küme olarak ölçmek. Ayrıca kriteri "IDSW / GT <= %1" yerine "her kesişme olayında en fazla bir değişim" gibi daha yapısal bir ölçüye çevirmek de düşünülebilir.

**Adım 6 — Doğrula.** Tabloda hem test hem doğrulama kümesinin Wald %95 aralıkları vardır.

| Küme | GT | IDSW | Oran | Standart hata | %95 aralık |
|---|---|---|---|---|---|
| Test (macar_iou, çerçeve açık) | 1 735 | 24 | %1,38 | %0,28 | [%0,83; %1,93] |
| Doğrulama (macar_iou, çerçeve açık) | 1 722 | 20 | %1,16 | %0,26 | [%0,66; %1,67] |

Sonuç: Test oranı eşiğin üstünde, ama %95 aralığı eşiği (%1) kapsıyor. Bu, "kesin olarak kaldı" demenin yanlış olacağını gösterir. Doğru ifade şudur: "Nokta tahmini eşiği aşıyor; belirsizlik aralığı eşiği kapsıyor; karar için daha fazla GT gerekir." Bu bölümde R4'ü bu yüzden "KALDI (nokta tahmini)" olarak işaretledik.

**Bunu AI'sız yazabilir misin?** 12 000 nesne-karede 9 kimlik değişimi ölçtün. Oran nedir? Wald %95 aralığını hesapla ve eşiğin (%0,1) aralığın içinde olup olmadığına karar ver.

### Örnek 3 (★★): Kayıtlardan kök neden analizi

İzleme sisteminde mAP'nin bir pencerede düştüğünü görüyorsunuz. Operatör "model bozuldu, yeniden eğitelim" diyor. Ama tetiğe basmadan önce kök nedeni bulmanız gerekir. Kayıtlar elinizde: her pencerenin PSI, KS p değeri, mAP ve üç alarm bayrağı.

**Adım 1 — Anla.** Soru "ne oldu?" değil "neden oldu?" sorusudur. İki olası neden var: kovaryat kayması (girdi dağılımı değişti, ilişki aynı) ya da kavram kayması (girdi ile etiket arasındaki ilişki değişti). İkisi farklı müdahale gerektirir. Kavram kayması etiket gerektirir (performans sinyali), kovaryat kayması etiketsiz de görülebilir (PSI).

**Adım 2 — Örnekle.** Aşağıdaki kayıtlar pencere 22 ile 26 arasını gösterir.

**Adım 3 — Kaba çöz.** İlk değişen sinyal PSI'dır: pencere 22'de 0,059 iken 23'te 0,220'ye çıkıyor. mAP de aynı pencerede düşüyor (0,932'den 0,875'e). Yani kayma girdiden başlıyor gibi görünüyor. Ama bu, tek bir pencereye dayanarak vardığımız bir sonuç.

**Adım 4 — Örüntü.** mAP bir sonraki pencerede (24) 0,910'a geri yükseliyor. PSI ise 24'te daha da arttı (0,296). Yani mAP tek başına güvenilir bir sinyal değil; 200 sahnelik pencerelerde gürültülü. Bu durumda mAP'ye bakarak kavram kaymasına karar vermek yanlış olur. Örüntü, girdi kaymasının monoton arttığı, mAP'nin ise gürültüyle birlikte aşağı yönlü bir eğilim gösterdiğidir.

**Adım 5 — İyileştir.** Karar için daha sağlam bir yol: performans sinyalini tek pencereye değil, üç pencerenin hareketli ortalamasına bağlamak, ve kavram kaymasını ayrı bir testle (Bölüm 77.10'daki alan sınıflandırıcısı) kontrol etmek. Bu, yanlış alarm riskini de düşürür.

**Adım 6 — Doğrula.** Tablo, kayıtlardan okuduğumuz değerleri ve sonucu gösterir.

| Pencere | PSI | KS p | mAP | Girdi | Skor | Performans | Yorum |
|---|---|---|---|---|---|---|---|
| 22 | 0,059 | 0,188 | 0,932 | 0 | 0 | 0 | Sakin |
| 23 | 0,220 | 0,055 | 0,875 | 1 | 0 | 0 | Girdi kayması başladı |
| 24 | 0,296 | 0,004 | 0,910 | 1 | 1 | 0 | mAP toparlandı, kayma sürüyor |
| 26 | 0,561 | 0,0001 | 0,906 | 1 | 1 | 1 | Performans alarmı, etiket gecikmeli |

Sonuç: Kök neden, kovaryat (girdi) kaymasıdır; kavram kayması kanıtı yoktur. Ama bu sonuç, tek bir mAP değerine dayanamaz. Müdahale: yeniden eğitimi tetiklemek (iki ardışık girdi ve skor alarmı var) ve insan onayıyla yeni işaretli veriyle eğitmek. Bu noktada yapılacak en önemli iş, kararı yazmak ve kanıtını kaydetmektir.

**Bunu AI'sız yazabilir misin?** Pencere 30'da PSI 3,65 ve mAP 0,910 olsun; pencere 31'de PSI 3,75 ve mAP 0,871 olsun. Hangi sinyal daha güvenilir ve neden?

### Örnek 4 (★★★): Bir değişikliğin bütün kabul ölçütlerine etkisi: int8'e geçiş

Ekipten biri "int8'e geçelim, model 3 kat küçülür, hız artar" diyor. Bu bir değişiklik önerisidir ve kararı kabul ölçütlerine bakarak vermeliyiz. Karar, bir mühendisin en sık verdiği karar türüdür: bir kazancın hangi kayıplarla geldiğini tartmak.

**Adım 1 — Anla.** Değişiklik, fp32 ağırlıklar ve aktivasyonlardan int8'e geçiştir. Beklenen kazanım: boyut, bellek ve (belki) hız. Beklenen kayıp: doğruluk, özellikle kutu hassasiyeti. Kabul ölçütleri 80.1'deki R tablosudur. Değişiklik yalnızca bu tabloya göre değerlendirilir.

**Adım 2 — Örnekle.** Ölçümler elimizde: int8 mAP@0,5 kaybı 1,1 puan, mAP@[0,5:0,95] kaybı 9,5 puan. Model dosyası 255 KB'den 71 KB'ye düştü. 96 px uçtan uca p95: fp32 1,146 ms, int8 1,092 ms. 640 px'te yalnızca int8 ağ süresi ölçüldü (2,83 ms p50).

**Adım 3 — Kaba çöz.** Her R için fp32 ve int8'in durumunu sıralayalım. fp32'de kayıp sıfırdır; bellek değerleri ise dört katıdır, çünkü fp32 bir eleman için 4 bayt, int8 için 1 bayt harcar.

**Adım 4 — Örüntü.** Kazançlar boyut ve ara tamponda, kayıplar kutu hassasiyetinde. Kutu hassasiyeti mAP@[0,5:0,95] ile ölçülür ve tam olarak R6'da zorlanır. Örüntü: int8, sınıflandırma kadar lokalizasyon için uygun değildir (bu, bu ağda; genel bir yasa değildir).

**Adım 5 — İyileştir.** Üç seçenek var. (a) Karma hassasiyet: ağın kafa katmanını (yalnızca 1 024 ağırlık) fp32 tutmak; boyut artışı ihmal edilebilir, lokalizasyon kaybı büyük olasılıkla düşer; ama bu ölçülmedi. (b) int8'i olduğu gibi kabul edip R6 kaybını belgelemek. (c) int8'i reddedip fp32 ile devam etmek, boyut ve bellek kazancını vazgeçmek. Öneri: (a), ölçüm sonrası karar.

**Adım 6 — Doğrula.** Tablo, değişikliğin her kabul ölçütüne etkisini gösterir.

| Kod | Ölçüt | fp32 | int8 | Etki |
|---|---|---|---|---|
| R5 | mAP@0,5 kaybı <= 2 puan | 0 | 1,1 | GEÇTİ |
| R6 | mAP@[0,5:0,95] kaybı <= 5 puan | 0 | 9,5 | KALDI |
| R7 | 96 px uçtan uca p95 <= 33 ms | 1,146 | 1,092 | GEÇTİ (her ikisi) |
| R8 | 640 px ağ p95 <= 33 ms | ÖLÇÜLMEDİ | 3,08 | GEÇTİ (int8) |
| R9 | Model <= 1 MB | 246 KB | 71 KB | GEÇTİ (her ikisi) |
| R10 | 96 px ara tampon <= 256 KB | ~144 KB | 36 KB | GEÇTİ (her ikisi) |
| R10b | 640 px ara tampon <= 256 KB | ~6,5 MB | 1,6 MB | KALDI (her ikisi) |
| R14 | ONNX ile PyTorch kutu farkı <= 1e-4 | 8e-6 | (fp32 yolu) | GEÇTİ |

Sonuç: int8, boyut ve bellekte kazandırır, ama R6'da kaldığı için lokalizasyon hassasiyeti gerektiren bir kullanımda kabul edilemez. Karma hassasiyet (a) seçeneği, bu eksiği kapatma olasılığı taşıyor ve bir sonraki deney olarak öneriliyor. Ekibe söylenecek cümle şöyle olabilir: "int8 kazancı gerçek, ama R6 kaybı ölçüldü ve kabul edilmedi; kafa katmanı fp32 ile yeniden ölçülene kadar int8 yayına alınmamalı."

**Bunu AI'sız yazabilir misin?** Bir modelin fp32 boyutu 4 MB, int8 boyutu 1 MB olsun; ara tampon fp32'de 300 KB ise int8'de kaç KB olur ve 256 KB sınırına göre hangisi geçer?

## Kendin Yap Projeleri

::: dikkat
Bu projelerde bir yapay zekâ aracına kod yazdırmayın, hata ayıklatmayın ya da cevap sormayın. Kitabı kapatıp boş bir dosyayla başlayın. Her projenin sonunda, kodunuzun ne yaptığını bir sayfada anlatabiliyor olmalısınız. Yardım gerekirse, önce ilgili bölüme dönün; ipuçları çözüm değildir, yalnızca yönü gösterir.
:::

### Proje 1 (★★): Sistemi kendi kameranıza taşıma

**Amaç.** Bu bölümün sistemini, kendi kameranızla kendi çektiğiniz kısa bir videoda çalıştırmak. Kayıt, kendi bahçenizde ya da kendi odanızda, sizin mülkünüzde olmalı. Başkalarını ya da mülkiyeti belirsiz alanları kaydetmeyin; kayıtları yalnızca bu projede kullanın ve paylaşmayın. Hedef, sistemin gerçek bir sensörde nasıl davrandığını görmek ve kaymayı ölçmektir.

**Yapılacak ve beklenen davranış.** Üç ila beş dakikalık bir video kaydedin. Videonun bir bölümünü etiketleyin (en az 100 kare, ayrı bir küme olarak). Videonun kare ortalama parlaklığını eğitim referansıyla karşılaştırın ve PSI değerini hesaplayın. Videoyu 96 x 96 gri tonlamaya indirin ve modeli bu girdiyle çalıştırın. Sonucu, eğitim ve nominal test sonuçlarıyla karşılaştıran bir tablo yazın.

**Önerilen yaklaşım (ipucu).** Önce PSI'yı hesaplayın; bu, sorunun ne kadar büyük olduğunu gösterir. Bölüm 77.10'daki PSI formülünü ve 80.8'deki izleme betiğini inceleyin, ama kodu kopyalamayın; kendi referansınızla yeniden yazın. Ön işleme (gri dönüşüm, boyutlandırma, normalizasyon) eğitimle birebir aynı olmalı; Bölüm 77.8'deki çarpıklık sorununu hatırlayın. Kamera ışığı değiştiğinde ne olduğunu gözlemleyin.

**Başarı kriterleri.**
- Kendi videonuz için PSI (parlaklık) değerini ve referansla karşılaştırmasını bir tabloda verin.
- Etiketlediğiniz 100 kare üzerinde mAP@0,5 değerini ölçün ve sonucu sayısal olarak raporlayın; hedef eşik yoktur, ama düşük çıkarsa nedenini açıklayın.
- Aynı videoda kare başına gecikmeyi p50 ve p95 olarak ölçün; ölçüm koşullarını (işlemci, iş parçacığı, pil durumu) yazın.
- Bir sayfalık bir rapor: kaymanın hangi özellikten (parlaklık, kontrast, bulanıklık, ölçek) geldiğini kanıtla birlikte söyleyin.

### Proje 2 (★★★): İkinci sensör ekleyip Kalman ile füzyon

**Amaç.** Sisteme sentetik bir radar ekleyip kamera tespitleriyle birleştirmek. Hedef, tek kamerada kaybolan ya da kesişmede kimliği karışan nesnelerde, radar bilgisinin takibi ne kadar iyileştirdiğini ölçmektir. Bölüm 62.9'daki sensör füzyonu fikrini uygulamış olacaksınız.

**Yapılacak ve beklenen davranış.** Radar simülatörü yazın: her karede gerçek nesnelerin (x, y) konumunu gürültüyle ölçsün, bazı karelerde ölçümü olasılıkla düşürsün (örneğin yüzde 20). Kamera tespitleriyle birlikte Kalman filtresinin güncelleme adımını iki ölçümle (kamera kutusunun merkezi ve radar konumu) sırayla çalıştırın. Sadece kamera ile füzyonu aynı test videolarında karşılaştırın.

**Önerilen yaklaşım (ipucu).** Durum vektörünü Bölüm 67.15'teki gibi (cx, cy, w, h, vx, vy) tutun. Radar ölçümü yalnızca (cx, cy) bileşenlerini ölçer; bu durumda gözlem matrisi H'nin yalnızca ilk iki satırı birdir. Radar ölçüm gürültüsü R_radar'ı ayrı bir köşegen matrisle verin. Kameranın ve radarın koordinatları aynı olmadığı için bir dönüşüm varsayımı yazın ve bunu bir ipucu olarak değil, bir varsayım olarak raporlayın. Kayıp kareleri, Kalman tahmin adımının tek başına çalıştığı durumlar olarak ele alın.

**Başarı kriterleri.**
- Üç tohumla (her tohum için ayrı radar gürültüsü) test videolarında MOTA ve IDSW değerlerini kamera-only ile karşılaştırın; ortalama ve standart sapma yazın.
- Füzyonun MOTA'yı en az 0,03 artırdığını ya da bunun olmadığını, tohumlar arası farkın gürültüden büyük olup olmadığını (Bölüm 57) belirterek söyleyin.
- Radar kaybı senaryosunda takibin max_age süresince kopmadığını gösteren bir iz şekli üretin.
- Radarın gerçekçi olmadığını, bu bir varsayım olduğunu rapora yazın; gerçek sensör hatasıyla ilgili hiçbir iddiada bulunmayın.

### Ek Alıştırmalar

Aşağıdaki on iki problem, zorluk etiketiyle sıralanmıştır. Her biri bir ya da üç cümledir; cevapları kendiniz yazın. (Mülakat) etiketli olanlar klasik mülakat sorularıdır.

1. ★ 96 x 96 bir görüntüde iki kutunun IoU değerini, (a) hiç kesişmediklerinde, (b) birinin diğerinin içinde olduğunda, (c) tam çakıştıklarında elle hesaplayın.
2. ★ (Mülakat) NMS'de eşik 0,3 ve 0,5 olsun. Hangisi daha çok tespit bastırır ve bu, kaçırmayı mı yanlış alarmı mı artırır?
3. ★★ (Mülakat) Bir sınıflandırıcının eşiğini değiştirmek mAP'i değiştirir mi? Cevabınızı bir örnekle gerekçelendirin.
4. ★★ (Mülakat) Bir dedektörün mAP@0,5 değeri yüksek, mAP@[0,5:0,95] değeri düşük. Bu ne anlatır ve nasıl iyileştirilebilir?
5. ★★ Bir 3 x 4 maliyet matrisi verildiğinde, Macar algoritmasının hangi tespiti eşleştirmeden bırakacağını ve nedenini elle bulun.
6. ★★★ (Mülakat) Kaybolan bir nesnenin izi max_age boyunca FP üretiyor. Üç farklı önlem önerin ve her birinin maliyetini yazın.
7. ★★ 8-bit simetrik kuantizasyonda bir tensörün en büyük mutlak değeri 3,2 ise ölçeği hesaplayın ve 1,7 değerinin kuantize edilmiş karşılığını yazın.
8. ★★ Bir Conv katmanının bir çıkış kanalı için ağırlıklar, BN gamma, beta, ortalama ve varyans verildiğinde, katlanmış ağırlık ve sapmayı el ile hesaplayın.
9. ★★★ (Mülakat) İki modelin test mAP'i 0,92 ve 0,93, test kümesi 200 nesne. Hangi kararı verirsiniz ve hangi istatistiği kullanırsınız (Bölüm 49 ve 57)?
10. ★★ (Mülakat) PSI 0,25 ve KS p değeri 0,5 olsun. Hangi sinyale güvenirsiniz ve neden?
11. ★★★ (Mülakat) Bir gözetleme sisteminin kare bütçesi 33 ms; ağ 20 ms, takip 8 ms. Bütçe aşılmış mı, hangi ölçüme bakarsınız ve hangi iyileştirmeyi önce denersiniz?
12. ★ (Mülakat) "Modelim test kümesinde yüzde 99 doğru" diyen birine ilk soru ne olmalı?

## Kod Okuma Egzersizi

Bu bölümde kendi yazdığımız kodun yanında gerçek bir kütüphanenin kodunu da okuyacağız. Kaynak, bu sistemin int8 kuantizasyon adımını çalıştıran ONNX Runtime'ın Python kısmıdır: `onnxruntime` 1.25.1 sürümünün `quantization/quantize.py` dosyasındaki `quantize_static` fonksiyonu. Kendi kurulumumuzdan birebir alındı; yol `C:/Users/merty/AppData/Local/Programs/Python/Python312/Lib/site-packages/onnxruntime/quantization/quantize.py`.

Fonksiyonun imzası 479. satırda başlar ve on beş parametre alır. Aşağıdaki kesit, gövdenin 640. satırından itibaren, başındaki iki işi gösterir: varsayılan değerlerin hazırlanması ve modelin yüklenmesi. Kesit, dosyadan kelimesi kelimesine alınmıştır; hiçbir satır değiştirilmedi. Yalnızca gövdenin devamı (kalibrasyon seçenekleri ve SmoothQuant dalı) dışarıda bırakıldı, çünkü bu bölümde kullanmadık.

```python
    nodes_to_exclude = nodes_to_exclude or []
    nodes_to_quantize = nodes_to_quantize or []
    op_types_to_quantize = op_types_to_quantize or []
    mode = QuantizationMode.QLinearOps

    if not op_types_to_quantize or len(op_types_to_quantize) == 0:
        q_linear_ops = list(QLinearOpsRegistry.keys())
        qdq_ops = list(QDQRegistry.keys())
        op_types_to_quantize = list(set(q_linear_ops + qdq_ops))

    model = (
        save_and_reload_model_with_shape_infer(model_input)
        if isinstance(model_input, onnx.ModelProto)
        else load_model_with_shape_infer(Path(model_input))
    )

    pre_processed: bool = model_has_pre_process_metadata(model)
    if not pre_processed:
```

Kesitin 658 ile 662 satırları, ön işleme uyarısını kaydeden `logging.warning` çağrısıdır. Uyarının metni bir bağlantı içerdiği için kesitte yer almıyor; mesajın başı şöyledir: "Please consider to run pre-processing before quantization." Bu uyarıyı çalıştırmamızda gördük ve 80.6'da çıktıdan kapattık. Kapatmanın doğru olup olmadığını aşağıdaki sorularla tartışın.

**Sorular — cevaplamadan geçme:**

1. Satır 640-642 neden `nodes_to_exclude or []` gibi bir ifade kullanıyor? Parametrelere doğrudan `[]` varsayılanı yazılsaydı hangi tuzak ortaya çıkardı? Python'un değiştirilebilir varsayılan argüman tuzağını Bölüm 3'te hatırlayarak yanıtlayın.
2. `op_types_to_quantize` boşsa, hangi operatör türleri kuantize edilir? Bu kümeyi oluşturan iki kayıt defterinin (`QLinearOpsRegistry` ve `QDQRegistry`) ne tuttuğunu, kaynağın başka bir yerinde arayarak bulun.
3. Satır 650-654 neden iki farklı yükleme fonksiyonu arasında seçim yapıyor? Modelin dinamik eksenleri (`h` ve `w`) bu şekil çıkarımını nasıl etkiler? Bunu 80.6'daki dışa aktarma kararıyla ilişkilendirin.
4. Satır 658'deki uyarı, graf düzeyinde bir ön işlemenin (ör. şekil ve sabit katlama) yapılmadığını söyler. Bu bizim modelimizde kaliteyi etkiler mi? Etkilemesi için hangi ölçüm gerekirdi? Bölüm 77.3'teki tekrarlanabilirlik ilkesiyle yazın.
5. Satır 643'teki `mode = QuantizationMode.QLinearOps` değişkeni, bizim QDQ formatımızda kullanılıyor mu? Yanıtınızı, `quant_format` parametresinin gövdedeki hangi dalda okunduğunu göstererek verin.
6. Kalibrasyonda `CalibMovingAverage` ve `CalibPercentile` seçenekleri, MinMax yönteminin aşırı değerlere (outlier) karşı davranışını nasıl değiştirir? Bu değişim, 80.6'da gördüğümüz 9,5 puanlık kutu hassasiyeti kaybını açıklayabilir mi? Bir hipotez yazın ve nasıl sınanacağını tarif edin.

## Bölüm Özeti

- Bitirme sistemi, bir İHA gözetleme videosunda hava hedeflerini algılayan, izleyen, güvence işareti koyan ve kendi kaymasını izleyen bir zincirdir. Her halka ölçülebilir bir kabul ölçütüne bağlıdır; bu bölümde on dört ölçüt tanımladık.
- Veri üretimi ve küme ayrımı sonucu belirler. Kareden çıkmış nesnelerin yanlış etiketlenmesi, takip MOTA'sını 0,60 gibi yanlış bir değere indirdi. Düzeltmeden sonra aynı model 0,77'ye çıktı. Değerlendirme hataları modelde değil ölçüm aracındadır.
- Dedektör, klasik temel çizgiyi nominal veride belirgin biçimde geçti (0,94'e karşı 0,60). Operasyonel kaymada da kullanılabilir kaldı (0,87), ama sert kaymada çöktü (0,07). Bu, izleme ve güvencenin neden gerektiğinin kanıtıdır.
- Takip, SORT'a dayanan Macar eşleştirmesi ve kare dışı filtresiyle test MOTA'sında 0,81'e ulaştı. R3 (0,90) ve R4 (IDSW <= %1) geçilemedi. Kaçırmalar, OOD kaynaklı yanlış izler ve kesişmedeki kimlik değişimi nedenlerdir.
- BatchNorm katlama, ONNX dışa aktarma ve PyTorch eşleşmesi kanıtlandı (kutu farkı 8e-6). int8 boyutu 3,6 kat küçülttü, ama lokalizasyon kaybı (9,5 puan) R6'yı geçmedi. CPU'da int8, bu küçük ağda hız kazandırmadı; zaman, son işleme ve takipte harcandı.
- Çözünürlük ve donanım birbirini belirler. 96 piksel bir mikrodenetleyiciye sığar ama tespit için yetersizdir; 640 piksel ise ara tamponuyla (1,6 MB) mikrodenetleyici sınıfı belleğe sığmaz.
- Tohum uyumu güvencesi OOD'de yanlış alarmı yüzde 96 azaltır, ama test kapsamasını 7,7 puan düşürür. Tek skor kuralı daha dengelidir (yüzde 79 azalma, 3,2 puan kayıp). Hangisinin seçileceği operasyonel bir karardır.
- İzleme, girdi kaymasını (PSI) skor ve performans sinyallerinden önce yakaladı; yeniden eğitim tetiği iki ardışık alarmla çalıştı. Yeniden eğitimin kazancı iyimserdir, çünkü simülasyonda kaymanın üretici tanımı biliniyor.

**Bundan sonrası:** Kitabın sonu bir sonun değil, bir yolun başlangıcıdır. Bu bölümdeki sistem, gerçek bir sensör ve gerçek veri olmadan tamamlanmış sayılmaz. Bir sonraki adım, kendi kayıtlarınızla (Kendin Yap Proje 1) ve bir gömülü kartla (Ek Alıştırmalar) sistemin ilk gerçek ölçümünü yapmaktır. Bölüm 39'daki simülatör-gerçek donanım farkı sözü, orada tamamlanacaktır. Sonrasında makale okuma ve yeniden üretme becerisi (Bölüm 79), sistemin bir araştırma sorusuna dönüşmesini sağlar: hangi güvence yöntemi gerçek kaymada daha iyi çalışır, hangi kuantizasyon kafa katmanında kayıp üretmez? Bu soruların cevabı, bu kitabın en başında sorulan sorudur: bir sistemin doğru olduğunu nasıl bilirsin? Cevap, bu bölümün her tablosunda aynıdır: ölçersin, koşulu yazarsın, belirsizliğini söylersin.

::: mulakat
1. Bir gözetleme sisteminde takip kimlikleri sık sık değişiyor. Hangi üç veriye bakar ve sırayla ne yaparsın?
2. Kare bütçen 33 ms, sistemin p95 değeri 40 ms. Ölçümün tekrarlanabilir olduğunu nasıl kanıtlarsın?
3. int8 modelin mAP@0,5 kaybı küçük, mAP@[0,5:0,95] kaybı büyük. Bu, hangi kararı değiştirir?
4. Bir izleme sisteminde PSI yükseldi, ama mAP düşmedi. Bunu nasıl yorumlar ve ne yaparsın?
5. Güvence katmanı yanlış alarmı azalttı, ama kapsamayı düşürdü. Bu bir mühendislik kararı mı, bir ölçüm sorunu mu? Açıkla.
6. Bir model kartında "bilinen sınırlar" bölümü neden zorunludur ve bu bölümü yazmamanın bedeli nedir?
7. Bir ekip "modeli her gün yeniden eğitelim, en güncel hâli olsun" diyor. Yanıtın ne olur?
8. Bu bölümde hangi gereksinim en çok belirsizdi ve onu ölçülebilir hâle getirmek için ne yaptın?
:::
