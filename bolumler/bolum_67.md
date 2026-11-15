%% kisim_no: XV
%% kisim_ad: Derin Öğrenme
%% bolum_no: 67
%% baslik: Nesne Tespiti, Segmentasyon & Takip

## Giriş: Görüntüde ne var, nerede, ve zaman içinde kim?

Sınıflandırma bölümünde (Bölüm 66) bir görüntüye tek bir etiket veriyorduk: "bu fotoğrafta bir uçak var". Gerçek dünyada soru genellikle daha zor. Bir İHA'nın kamerasında "bir uçak var" yetmez; kaç tane olduğunu, her birinin nerede olduğunu, hangisinin hangisi olduğunu ve bir sonraki karede nereye gideceğini bilmen gerekir. Bu bölüm bu üç soruyu sırayla ele alıyor: nesne tespiti (nerede ve ne), segmentasyon (her pikselin hangi sınıfa ait olduğu) ve takip (aynı nesneyi kareler boyunca tek kimlikle izlemek).

Bu konular savunma sanayiinde doğrudan karşına çıkar. Bir gözetleme İHA'sında yapay zekâ modeli saniyede onlarca kare işler; her karedeki tespitler kararsız, gürültülü ve bazen tamamen yanlıştır. İnsan operatörün ekranında bunların ancak tutarlı bir iz olarak göründüğü anlamlıdır. Bir kare "bir şey var" diyip sonraki karede onu unutursa ya da aynı nesneye iki farklı kimlik verirse, sistem güvenilmez olur. Bu yüzden tespit, segmentasyon ve takip tek bir hattın parçalarıdır ve birinin hatası diğerine taşınır.

Bölüm 46'da bir İHA'nın bağlantısı kesildiğinde bile kendi sensöründen karar verebilmesi gerektiğini ve modelin uçakta çalışması gerektiğini konuşmuştuk. Burada o fikri somutlaştırıyoruz: küçük bir tek aşamalı dedektör, bir U-Net ve bir takipçiyi sıfırdan yazıp ölçeceğiz. Ölçümlerin hepsi sentetik veri üzerinde yapılacak; bu veriler gerçek bir uçuş kaydı değildir ve sonuçlar gerçek bir sistemin doğruluğu olarak okunmamalıdır.

::: not
Bu bölümde kullanılan her veri sentetiktir: sabit tohumla üretilmiş gri sahneler ve hareket eden nesne dizileri. Metin boyunca "sentetik" ifadesi bu veriyi işaret eder. Kod satırları 70, terminal çıktısı satırları 74 karakterle sınırlıdır; uzun satırlar anlamı değiştirmeden bölünmüştür. Egitim ve test kümeleri ayrıdır; egitim skorları yalnızca model davranışını anlamak için verilir, başarı iddiası her zaman test kümesi üzerindedir.
:::

## 67.1 Dört görev, bir görüntü: çıktı biçimi neyi değiştirir?

Aynı sahne üzerinde altı farklı görev düşünebilirsin. Hepsi "bu görüntüyü anlamak" diye özetlenebilir ama her birinin çıktısı farklıdır ve hangi metriğin kullanılacağını belirler. Tablo 67.1 bu farkı özetler.

| Görev | Çıktı | Tipik metrik | Ne zaman yeterli? |
|---|---|---|---|
| Sınıflandırma | Tek bir etiket ya da olasılık vektörü | Doğruluk, AUC | Görüntüde tek nesne ya da sadece "ne" sorusu varsa |
| Yerelleştirme | Tek nesnenin kutusu | IoU | Tek nesnenin konumu gerekiyorsa |
| Tespit | Her nesne için (kutu, sınıf, skor) | mAP | Birden çok nesne, sayı ve konum önemliyse |
| Anlamsal segmentasyon | Her piksel için sınıf | mIoU, Dice | Alan, sınır ve şekil önemliyse; örnekler ayrılmıyorsa |
| Örnek segmentasyonu | Her nesne için ayrı piksel maskesi | mask-AP | Aynı sınıftan iki nesne birbirine değiyorsa |
| Takip | Kareler boyunca kimlikli kutular | MOTA, IDF1, HOTA | Zaman içinde aynı nesnenin sürekliliği gerekiyorsa |

Tablo 67.1: Görevler ve çıktı biçimleri. Metrikler görev türüne göre seçilir.

Şekil 67.1 aynı sentetik sahneyi altı görev açısından gösterir. Sahnede bir kare, bir daire ve bir üçgen görünüyor; bazı nesneler birbirini kısmen örtüyor.

![Şekil 67.1: Aynı sahnede altı görev: sınıflandırma, yerelleştirme, tespit, anlamsal ve örnek segmentasyonu, takip](gorseller/b67_gorev_turleri.png)

Dikkat edilecek nokta şu: sınıflandırmada "kare" ya da "daire" gibi tek bir cevap vardır ve sahnedeki diğer nesneler görünmez. Tespit çıktısında her nesne için kutu ve skor vardır, ancak iki nesne aynı pikseli paylaşıyorsa kutular üst üste bindiği için ayrım zordur. Anlamsal segmentasyonda aynı sınıftan iki nesne tek bir renge boyanır ve kaç nesne olduğu kaybolur. Örnek segmentasyonu bu sorunu çözer ama daha pahalıdır. Takipte ise aynı nesneye zaman içinde aynı kimliğin verilmesi gerekir; bu, bir karenin tek başına çözemeyeceği bir sorudur.

::: baglanti
Sınıflandırma ve olasılık çıktısı için Bölüm 57'deki karışıklık matrisine ve PR eğrisine, takip için Bölüm 62'deki Kalman filtresine dayanacağız. Bu bölümde sık sık "Bölüm 57'de gördüğümüz gibi" diye atıf yapacağız.
:::

## 67.2 Kutu geometrisi ve IoU: iki kutu ne kadar örtüşür?

Tespit çıktısının ilk birimi kutudur. Bir kutuyu iki farklı biçimde yazabilirsin: köşe biçimi (x1, y1, x2, y2), sol üst ile sağ alt köşe; ya da merkez biçimi (cx, cy, w, h), merkez ile genişlik ve yükseklik. Ağlar genellikle merkez biçimini tahmin eder, değerlendirme ise köşe biçimini kullanır. Bu yüzden ikisi arasında güvenilir bir dönüşüm gerekir.

Kutular arasındaki benzerliğin standart ölçüsü **IoU** (Intersection over Union, kesişim üzerine birleşim) değeridir:

IoU(A, B) = |A ∩ B| / |A ∪ B| = I / (|A| + |B| − I)

Burada |A| kutunun alanı, I kesişim alanı, |A ∪ B| ise birleşim alanıdır. IoU 0 ile 1 arasındadır: 1 aynı kutu, 0 hiç örtüşmeyen kutu demektir. Bölüm 49'da gördüğün olasılık terminolojisine benzer biçimde, IoU bir küme benzerliği ölçüsüdür (Jaccard indeksi).

Kodu yazmaya başlamadan önce, IoU hesabında üç kenar durumu düşün: kutular hiç örtüşmüyorsa kesişim negatif olabilir (bunu 0'a kırpmalısın); kutular yalnızca bir kenarda değiyorsa kesişim alanı 0'dır; bir kutu öteki içinde ise kesişim küçük kutunun alanına eşittir. Ayrıca genişliği ya da yüksekliği 0 olan dejenere bir kutunun alanı 0'dır ve birleşim de 0 olabilir; bu durumda bölme yapamazsın. Aşağıdaki kod, bu durumları vektörleştirilmiş biçimde ele alır.

Önce biçim dönüşümleri ile alan ve kesişim/birleşim yardımcılarını yazıyoruz. Yardımcılar bir matris döndürür: N kutu ile M kutu için N × M IoU değerleri tek seferde hesaplanır.

```python
# b67_01_iou_nms.py: kutu donusumu, IoU, GIoU, NMS, Soft-NMS.
# Sifirdan yazilmis surumleri torchvision ile karsilastirir.
import numpy as np
import torch
from torchvision.ops import box_iou as tv_iou
from torchvision.ops import nms as tv_nms
from torchvision.ops import batched_nms as tv_bnms


def xywh_to_xyxy(c):
    """(cx, cy, w, h) -> (x1, y1, x2, y2)."""
    c = np.asarray(c, dtype=np.float64)
    return np.stack([c[:, 0] - c[:, 2] / 2, c[:, 1] - c[:, 3] / 2,
                     c[:, 0] + c[:, 2] / 2, c[:, 1] + c[:, 3] / 2], 1)


def xyxy_to_xywh(b):
    """(x1, y1, x2, y2) -> (cx, cy, w, h)."""
    b = np.asarray(b, dtype=np.float64)
    w, h = b[:, 2] - b[:, 0], b[:, 3] - b[:, 1]
    return np.stack([b[:, 0] + w / 2, b[:, 1] + h / 2, w, h], 1)
```

Kodun ikinci yarısında IoU matrisi, GIoU ve NMS yer alır. Bir kutunun alanını negatif genişlikle hesaplamamak için `alan` fonksiyonu değerleri 0'da kırpar.

```python
def alan(b):
    """Dejenere kutularda (negatif genislik) alan 0 sayilir."""
    return np.clip(b[:, 2] - b[:, 0], 0, None) * \
        np.clip(b[:, 3] - b[:, 1], 0, None)


def kesisim_birlik(a, b):
    """Kesisim ve birlik alanlari, (N,M) matrisler olarak."""
    x1 = np.maximum(a[:, None, 0], b[None, :, 0])
    y1 = np.maximum(a[:, None, 1], b[None, :, 1])
    x2 = np.minimum(a[:, None, 2], b[None, :, 2])
    y2 = np.minimum(a[:, None, 3], b[None, :, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    birlik = alan(a)[:, None] + alan(b)[None, :] - inter
    return inter, birlik


def iou_matris(a, b):
    """a: (N,4), b: (M,4) -> (N,M) IoU. Birlik 0 ise IoU = 0."""
    inter, birlik = kesisim_birlik(a, b)
    return np.where(birlik > 0,
                    inter / np.maximum(birlik, 1e-12), 0.0)


def giou_matris(a, b):
    """GIoU = IoU - (C - B) / C; C kapsayan kutunun alani."""
    inter, birlik = kesisim_birlik(a, b)
    iou = np.where(birlik > 0, inter / np.maximum(birlik, 1e-12), 0.0)
    x1 = np.minimum(a[:, None, 0], b[None, :, 0])
    y1 = np.minimum(a[:, None, 1], b[None, :, 1])
    x2 = np.maximum(a[:, None, 2], b[None, :, 2])
    y2 = np.maximum(a[:, None, 3], b[None, :, 3])
    c = (x2 - x1) * (y2 - y1)
    return np.where(c > 0,
                    iou - (c - birlik) / np.maximum(c, 1e-12), iou)
```

Şekil 67.2, IoU'nun geometrisini somut bir örnekle gösterir: A = (10, 10, 50, 50) ve B = (12, 12, 52, 52). Kesişim 38 × 38 = 1444 piksel, birleşim 1600 + 1600 − 1444 = 1756 piksel ve IoU = 1444 / 1756 ≈ 0,822'dir.

![Şekil 67.2: İki kutunun kesişimi ve birleşimi: IoU = 1444 / 1756](gorseller/b67_iou_geometri.png)

## 67.3 Kenar durumları ve GIoU: IoU'nun neyi kaçırdığı

IoU güzel bir ölçüdür ama bir zayıflığı vardır: iki kutu hiç örtüşmüyorsa IoU her zaman 0'dır. Bir kutu diğerine ne kadar yakın, ne kadar uzak olursa olsun, sıfır IoU sıfırdır. Bu durum bir eğitim sinyali olarak çok kötüdür: ağ, kutusunu hedefe ne kadar yaklaştırdığını IoU üzerinden göremez, çünkü gradyan yoktur.

**GIoU** (Generalized IoU, genel bilgi: Rezatofighi ve diğerleri, 2019) bu sorunu, iki kutuyu da içine alan en küçük kutunun alanı C ile çözer:

GIoU = IoU − (C − B) / C

Burada B iki kutunun birleşim alanıdır. Eğer kutular örtüşmüyorsa IoU = 0 olur ama (C − B)/C terimi kutular birbirinden uzaklaştıkça büyür, dolayısıyla GIoU negatif olur. GIoU −1 ile 1 arasındadır ve tam örtüşmede 1'e ulaşır. Bu yüzden regresyon kaybı olarak IoU yerine 1 − GIoU kullanılabilir.

Aşağıdaki test fonksiyonu, IoU ve GIoU'yu elle bildiğimiz kenar durumlarında kontrol eder. Her durum için beklenen değeri önce kağıtta hesapla, sonra kodla karşılaştır. Örneğin "hiç örtüşmüyor" durumunda kutular (0,0,10,10) ile (20,20,30,30) arasında kesişim 0'dır, birleşim 100 + 100 = 200'dür; C = 30 × 30 = 900 olduğu için GIoU = 0 − (900 − 200)/900 ≈ −0,7778 çıkar.

```python
def testler():
    print("== Kenar durumlari (IoU) ==")
    k = np.array([[0, 0, 10, 10.0]])
    durum = {
        "ayni kutu": (k, k),
        "hic ortusmuyor": (k, np.array([[20, 20, 30, 30.0]])),
        "yalnizca kenar temas": (k, np.array([[10, 0, 20, 10.0]])),
        "ic ice (1 / 4 kare)": (np.array([[0, 0, 4, 4.0]]),
                                np.array([[1, 1, 3, 3.0]])),
        "dejenere (genislik 0)": (k, np.array([[5, 5, 5, 9.0]])),
        "iki dejenere": (np.array([[2, 2, 2, 2.0]]),
                         np.array([[2, 2, 2, 2.0]])),
    }
    for ad, (a, b) in durum.items():
        print("%-24s IoU=%.4f  GIoU=%.4f" % (
            ad, iou_matris(a, b)[0, 0], giou_matris(a, b)[0, 0]))
    print("\n== torchvision karsilastirmasi (rastgele, tohum 0) ==")
    rng = np.random.default_rng(0)
    xy = rng.uniform(0, 100, (300, 2))
    wh = rng.uniform(1, 40, (300, 2))
    A = np.hstack([xy, xy + wh])
    B = np.hstack([rng.uniform(0, 100, (250, 2)),
                   rng.uniform(0, 100, (250, 2))])
    B[:, 2:] = B[:, :2] + rng.uniform(1, 40, (250, 2))
    ours = iou_matris(A, B)
    tv = tv_iou(torch.tensor(A, dtype=torch.float32),
                torch.tensor(B, dtype=torch.float32)).numpy()
    print("maks |fark| IoU: %.2e" % np.abs(ours - tv).max())
    print("IoU > 0 olan cift sayisi:", int((ours > 0).sum()))
```

## 67.4 Açgözlü NMS: aynı nesnenin fazla kutularını temizlemek

Bir tespit ağı tek bir nesne için birden çok kutu üretir. Hücre komşuluğundaki birkaç hücre aynı nesneye "ben de buradayım" diyebilir ve her biri biraz farklı bir kutu ile sonuçlanır. Bunları sırayla bırakırsan aynı nesne için onlarca tespit kalır; hem mAP'i (yanlış pozitifler yüzünden) hem de takibi bozarlar. **Maksimum bastırma** (NMS, Non-Maximum Suppression) bu fazlalığı temizler.

Açgözlü NMS algoritması şöyledir: (1) tüm kutuları skora göre azalan sırala; (2) en yüksek skorlu kutuyu tut; (3) geri kalan her kutu için tutulan kutuyla IoU'yu hesapla ve IoU eşiğini aşıyorsa o kutuyu sil; (4) listede kutu kalmayana kadar 2'ye dön. Algoritmanın her adımı bir "tut" kararı verir ve bu karar geri alınmaz; bu yüzden "açgözlü"dür.

Eşik seçimi kritiktir. IoU eşiği 0,5 çoğu tespit senaryosunda makul bir başlangıçtır; düşük eşik (ör. 0,1) iki farklı ama birbirine yakın nesneyi tek bir nesne sayabilir, yüksek eşik (ör. 0,9) aynı nesnenin fazla kutularını tutar. Aşağıdaki kod açgözlü NMS'i ve sınıf başına NMS'i (farklı sınıftaki kutular birbirini bastırmaz) yazar.

```python
def nms(kutular, skorlar, esik):
    """Acgozlu NMS. IoU > esik olan kutular bastirilir."""
    sira = np.argsort(-skorlar, kind="stable")
    tutulan = []
    while sira.size > 0:
        i = sira[0]
        tutulan.append(i)
        if sira.size == 1:
            break
        iou = iou_matris(kutular[i:i + 1], kutular[sira[1:]])[0]
        sira = sira[1:][iou <= esik]
    return np.array(tutulan, dtype=np.int64)


def sinif_nms(kutular, skorlar, siniflar, esik):
    """Sinif basina NMS: farkli siniflar birbirini bastirmaz.
    Ofset numarasi: her sinifin kutularini ayri bir koordinat
    bolgesine kaydirir (torchvision batched_nms da ayni fikri)."""
    if len(kutular) == 0:
        return np.zeros(0, dtype=np.int64)
    ofset = siniflar[:, None].astype(np.float64) * (
        kutular.max() + 1.0)
    tutulan = nms(kutular + ofset, skorlar, esik)
    return tutulan
```

Açgözlü NMS'in karmaşıklığı kabaca O(n²)'dir: her tutulan kutu için kalan kutuların hepsiyle IoU hesaplanır. Yüz binlerce kutu için bu pahalıdır; gerçek kütüphaneler ya ızgara tabanlı ön eleme ya da C/CUDA çekirdekleri kullanır. Bölüm 67.19'da gecikme bütçesine bakarken bu maliyetin ne kadar büyük olduğunu ölçeceğiz.

Şekil 67.3, altı kutuluk küçük bir örnekte NMS'in etkisini gösterir: soldaki panelde tüm kutular, sağda eşik 0,5 ile kalanlar.

![Şekil 67.3: NMS öncesi (solda) ve sonrası (sağda): IoU > 0,5 olan kutular bastırıldı](gorseller/b67_nms.png)

## 67.5 Soft-NMS: silmek yerine zayıflatmak

Sert NMS bir kutuyu tamamen siler. Ama iki gerçek nesne gerçekten birbirine yakınsa (kalabalık bir sürüde iki İHA gibi), ikincisi de silinebilir. **Soft-NMS** (Bodla ve diğerleri, 2017, genel bilgi) bu sorunu, silmek yerine skoru IoU'ya bağlı olarak azaltarak çözer. Gauss biçiminde:

s_i ← s_i · exp(−IoU(M, b_i)² / σ)

Burada M, o anda en yüksek skorlu tutulan kutudur. IoU büyükse skor güçlü biçimde düşer, IoU küçükse neredeyse değişmez. Skor eşiğin altına düşen kutu listeden çıkarılır. Bu yöntem sert NMS'in tek bir eşik kararından kurtarır, ama skorların anlamı değişir: Soft-NMS sonrası skorlar artık "bu kutu bir nesne" olasılığı değildir.

Soft-NMS'in gerçeklemesi aşağıdadır. Döngü her adımda kalan kutular içinde en yüksek skorluyu seçer, onu sonuç listesine ekler ve kalanların skorlarını yukarıdaki Gauss çarpanıyla azaltır; skoru `esik_min`'in altına düşen kutu listeden çıkar.

```python
def soft_nms(kutular, skorlar, sigma=0.5, esik_min=0.001):
    """Gauss Soft-NMS: bastirma yerine skoru IoU'ya gore azaltir."""
    skor = skorlar.astype(np.float64).copy()
    kalan = np.arange(len(skor))
    sirali, yeni = [], []
    while kalan.size > 0:
        m = int(np.argmax(skor[kalan]))
        i = kalan[m]
        sirali.append(i)
        yeni.append(skor[i])
        kalan = np.delete(kalan, m)
        if kalan.size == 0:
            break
        iou = iou_matris(kutular[i:i + 1], kutular[kalan])[0]
        skor[kalan] *= np.exp(-(iou ** 2) / sigma)
        kalan = kalan[skor[kalan] >= esik_min]
    return np.array(sirali), np.array(yeni)
```

Aşağıdaki kod kalan iki bölümü de içerir: 01 betiğinin en alt kısmındaki örnek ve torchvision ile birebir karşılaştırma. Karşılaştırma tohum 0 ile rastgele kutular üzerinde yapılır; `nms` ve `batched_nms` için sonuçların birebir aynı olup olmadığı kontrol edilir.

```python
def nms_ornegi():
    print("\n== NMS ornegi (altı kutu) ==")
    kutu = np.array([
        [10, 10, 50, 50], [12, 12, 52, 52], [60, 60, 100, 100],
        [58, 58, 98, 98], [10, 60, 40, 90], [30, 30, 70, 70]], float)
    skor = np.array([0.90, 0.85, 0.80, 0.75, 0.70, 0.65])
    print("IoU(1,2) = %.4f  IoU(3,4) = %.4f" % (
        iou_matris(kutu[0:1], kutu[1:2])[0, 0],
        iou_matris(kutu[2:3], kutu[3:4])[0, 0]))
    for esik in (0.5, 0.1):
        t = nms(kutu, skor, esik)
        print("esik=%.1f tutulan indisler: %s" % (esik, t.tolist()))
    ref = tv_nms(torch.tensor(kutu, dtype=torch.float32),
                 torch.tensor(skor, dtype=torch.float32), 0.5).numpy()
    print("torchvision nms(0.5):", ref.tolist())
    sn, ss = soft_nms(kutu, skor, sigma=0.5)
    print("soft-NMS sirasi:", sn.tolist())
    print("soft-NMS skorlari:", np.round(ss, 4).tolist())
```

```python
def rastgele_karsilastirma():
    print("\n== NMS ve sinif-NMS: torchvision ile birebir mi? ==")
    rng = np.random.default_rng(1)
    eslesen, toplam = 0, 0
    for _ in range(200):
        n = int(rng.integers(5, 60))
        xy = rng.uniform(0, 80, (n, 2))
        K = np.hstack([xy, xy + rng.uniform(4, 30, (n, 2))])
        s = rng.uniform(0, 1, n)
        for esik in (0.3, 0.5, 0.7):
            ours = nms(K, s, esik)
            ref = tv_nms(torch.tensor(K, dtype=torch.float32),
                         torch.tensor(s, dtype=torch.float32), esik)
            eslesen += int(np.array_equal(ours, ref.numpy()))
            toplam += 1
    print("tek sinif: %d / %d koşu birebir ayni" % (eslesen, toplam))
    eslesen = 0
    for _ in range(100):
        n = int(rng.integers(5, 40))
        xy = rng.uniform(0, 80, (n, 2))
        K = np.hstack([xy, xy + rng.uniform(4, 30, (n, 2))])
        s = rng.uniform(0, 1, n)
        c = rng.integers(0, 3, n)
        ours = sinif_nms(K, s, c, 0.5)
        ref = tv_bnms(torch.tensor(K, dtype=torch.float32),
                      torch.tensor(s, dtype=torch.float32),
                      torch.tensor(c), 0.5).numpy()
        eslesen += int(np.array_equal(ours, ref))
    print("sinif-NMS: %d / 100 koşu birebir ayni" % eslesen)


if __name__ == "__main__":
    testler()
    nms_ornegi()
    rastgele_karsilastirma()
```

Yukarıdaki betiğin tam çıktısı aşağıdadır. Kenar durumları, IoU'nun torchvision karşılaştırması (maksimum fark 6,5 × 10⁻⁷, float32 yuvarlaması), altı kutuluk NMS örneği ve sınıf başına NMS sonuçlarını içerir.

```term
$ python b67_01_iou_nms.py
== Kenar durumlari (IoU) ==
ayni kutu                IoU=1.0000  GIoU=1.0000
hic ortusmuyor           IoU=0.0000  GIoU=-0.7778
yalnizca kenar temas     IoU=0.0000  GIoU=0.0000
ic ice (1 / 4 kare)      IoU=0.2500  GIoU=0.2500
dejenere (genislik 0)    IoU=0.0000  GIoU=0.0000
iki dejenere             IoU=0.0000  GIoU=0.0000

== torchvision karsilastirmasi (rastgele, tohum 0) ==
maks |fark| IoU: 6.54e-07
IoU > 0 olan cift sayisi: 9450

== NMS ornegi (altı kutu) ==
IoU(1,2) = 0.8223  IoU(3,4) = 0.8223
esik=0.5 tutulan indisler: [0, 2, 4, 5]
esik=0.1 tutulan indisler: [0, 2, 4]
torchvision nms(0.5): [0, 2, 4, 5]
soft-NMS sirasi: [0, 2, 4, 5, 1, 3]
soft-NMS skorlari: [0.9, 0.8, 0.7, 0.6205, 0.2063, 0.1931]

== NMS ve sinif-NMS: torchvision ile birebir mi? ==
tek sinif: 600 / 600 koşu birebir ayni
sinif-NMS: 100 / 100 koşu birebir ayni
```

Çıktıda iki nokta dikkat çekicidir. Birincisi, eşik 0,5 ile kutu 1 ve 2 (IoU = 0,8223) arasında kutu 2 bastırılır; eşik 0,1 ile kutu 6 (IoU(1,6) ≈ 0,143) da bastırılır. Yani eşik seçimi, "hangi kutu gerçek bir ayrı nesne" sorusunun cevabını değiştirir. İkincisi, Soft-NMS hiçbir kutuyu tamamen silmez; sadece skorları düşürür: kutu 2'nin skoru 0,85'ten 0,2063'e iner ama listede kalır. Bu, eşik seçimini skor sıralamasına taşır, ama dikkat: Soft-NMS sonrası sabit bir skor eşiği ile kesmen gerekir.

::: dikkat
Kenar durumlarını kodla kontrol etmeden IoU fonksiyonuna güvenme. Birçok tespit hatası aslında "IoU 0 bölü 0" gibi bir sayısal kenar durumundan çıkar: iki dejenere kutunun birleşimi 0 olduğunda bölme NaN üretir. Bu yüzden yukarıdaki kod birleşimi 0 olduğunda IoU'yu 0 sayar.
:::

## 67.6 Değerlendirme: TP, FP ve precision–recall eğrisi

Bir tespit ağını nasıl ölçeceğiz? Önce bir kutunun doğru (TP, True Positive) ya da yanlış (FP, False Positive) sayılması için bir kural gerekir. Standart kural şudur: bir tahmin kutusu, IoU ≥ eşik olan ve daha önce başka bir tahmin tarafından eşleşmemiş en yüksek IoU'lu gerçek kutuyla eşleşirse TP'dir; aksi halde FP'dir. Eşleşmemiş her gerçek kutu ise FN (False Negative, kaçırılan) sayılır. Bir gerçek kutu en fazla bir kez eşleşebilir; bu kural, aynı nesneyi iki kez saymayı engeller.

Tahminleri skora göre azalan sırada işlersen, her tahmin noktasında kümülatif TP ve FP sayılarından **precision** (doğru tahminlerin oranı, TP / (TP + FP)) ve **recall** (bulunan gerçeklerin oranı, TP / gerçek sayısı) hesaplanır. Skor eşiğini düşürdükçe recall artar, precision genellikle düşer. Bu iki değerin eğrisine **precision–recall eğrisi** denir; Bölüm 57'de gördüğün PR eğrisinin tespit versiyonudur.

Eğrinin altında kalan alan **AP** (Average Precision) değerini verir. AP'yi hesaplamanın iki yaygın yolu vardır:

- **11 nokta interpolasyonu** (VOC 2007, genel bilgi): recall 0, 0,1, ..., 1 noktalarında "bu recall'a ulaşan en yüksek precision" değerlerinin ortalaması alınır.
- **Tüm noktalar** (VOC 2010 ve sonrası, genel bilgi): precision eğrisi önce "zarfa" alınır (her recall için sağdaki en büyük precision), sonra recall adımları ile çarpılıp toplanır.

Zarf adımı önemlidir. Precision eğrisi zigzag yapar; zarf, eğriyi azalmayan bir fonksiyona dönüştürür. Bu, bir sonraki recall düzeyinde daha iyi bir precision mümkünse daha kötüsünü sayma; yani ölçüm bir yönde dürüst kalır.

Aşağıdaki kod TP/FP eşleştirmesini, PR eğrisini ve üç AP biçimini yazar. Eşleştirme "eşleşmemiş en yüksek IoU" kuralını uygular; bu, COCO değerlendirmesinin de kullandığı yaklaşımdır (genel bilgi).

```python
# b67_02_ap.py: TP/FP eslestirme, PR egrisi, AP (11 nokta, 101 nokta,
# tum noktalar) ve mAP@0.5, mAP@[0.5:0.95]. Elle hesaplanmis ornek
# ve sayisal integral ile dogrulama.
import numpy as np
from b67_01_iou_nms import iou_matris
from b67_veri import veri_seti


def eslestir(tahmin, gt, esik):
    """Tek gorsel, tek sinif. tahmin: (K,4) skor sirasina gore azalan.
    Her tahmin, eslesmemis en yuksek IoU'lu gercek kutuyla eslesir
    (IoU >= esik). Eslesme yoksa FP. Her gercek kutu en fazla bir
    kez eslesir."""
    tp = np.zeros(len(tahmin), dtype=bool)
    if len(tahmin) == 0 or len(gt) == 0:
        return tp
    iou = iou_matris(tahmin, gt)
    kullanildi = np.zeros(len(gt), dtype=bool)
    for k in range(len(tahmin)):
        aday = np.where(~kullanildi, iou[k], -1.0)
        j = int(np.argmax(aday))
        if aday[j] >= esik:
            tp[k] = True
            kullanildi[j] = True
    return tp
```

```python
def pr_egrisi(skor, tp, n_gt):
    """Skora gore azalan sirada kumulatif precision ve recall."""
    sira = np.argsort(-skor, kind="stable")
    tp = tp[sira].astype(np.float64)
    dogru = np.cumsum(tp)
    yanlis = np.cumsum(1 - tp)
    precision = dogru / np.maximum(dogru + yanlis, 1e-12)
    recall = dogru / max(n_gt, 1)
    return precision, recall


def ap_hesapla(skor, tp, n_gt, yontem="tum"):
    """AP. yontem: '11' (VOC2007), '101' (COCO tarzi), 'tum'
    (VOC2010+)."""
    p, r = pr_egrisi(skor, tp, n_gt)
    if len(p) == 0:
        return 0.0
    if yontem in ("11", "101"):
        noktalar = (np.linspace(0, 1, 11) if yontem == "11"
                    else np.linspace(0, 1, 101))
        toplam = 0.0
        for rt in noktalar:
            uygun = p[r >= rt - 1e-9]  # kayan nokta toleransi
            toplam += uygun.max() if uygun.size else 0.0
        return toplam / len(noktalar)
    # tum noktalar: precision zarfi (artan kisim) x recall adimi
    mrec = np.concatenate([[0.0], r, [r[-1]]])
    mpre = np.concatenate([[0.0], p, [0.0]])
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    i = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1]))
```

Yukarıdaki iki blok `eslestir`, `pr_egrisi` ve `ap_hesapla` fonksiyonlarını içerir. `ap_hesapla` içinde `yontem` parametresi üç değerden birini alır: `'11'` (VOC 2007), `'101'` (COCO tarzı, 101 nokta) ve `'tum'` (tüm noktalar). Hangi yöntemin kullanıldığını her zaman raporda belirtmelisin; aynı tahminler için farklı yöntemler birbirinden farklı mAP değerleri verir.

Elle hesaplanabilen küçük bir örnek, bu fonksiyonların doğruluğunu kontrol etmek için iyi bir yoldur. Beş tahmin var, skorlar 0,95; 0,90; 0,85; 0,70; 0,60; TP bayrakları sırasıyla 1, 0, 1, 1, 0 ve gerçek kutu sayısı 4. Kümülatif TP: 1, 1, 2, 3, 3; FP: 0, 1, 1, 1, 2. Precision: 1; 0,5; 0,667; 0,75; 0,6. Recall: 0,25; 0,25; 0,5; 0,75; 0,75. Tüm noktalar AP'si: zarf değerleri 1; 0,75; 0,75; 0,75; 0,6 ile recall adımları 0,25 ile çarpılıp toplanınca 0,25 + 0,1875 + 0,1875 = 0,625 çıkar. 11 nokta AP'si ise 0,6136'dır.

Kodun çıktısı bu değerleri birebir üretir. Ayrıca sayısal bir doğrulama yapılır: rastgele 50 tahmin kümesi için tüm noktalar AP'si, zarfın sayısal integraliyle karşılaştırılır; fark 3,47 × 10⁻⁶ mertebesindedir.

## 67.7 Ortalama AP: mAP@0,5 ve mAP@[0,5:0,95]

Tek bir sınıfın AP'si, birden çok sınıf için **mAP** (mean Average Precision) olur: her sınıfın AP'si hesaplanır, ortalaması alınır. Bu ortalamanın yanında bir eşik sorusu vardır: IoU eşiğini 0,5 seçersen, kutusu biraz kaymış ama nesneyi bulmuş bir tespit iyi sayılır. Oysa uygulamada 0,5 IoU ile yetinmek yanıltıcı olabilir.

**mAP@0,5** tek bir IoU eşiğini (0,5) kullanır (Pascal VOC'un geleneği). **mAP@[0,5:0,95]** ise 0,5'ten 0,95'e 0,05 adımlarla on eşiğin her birinde mAP hesaplar ve ortalamasını alır (COCO'nun tanımı, genel bilgi). İkincisi daha katıdır: kutu konumu ne kadar hassas olursa o kadar yüksek puan alırsın.

Aşağıdaki deneyde sentetik bir test kümesi (300 sahne) üzerinde gerçek kutulara gürültü eklenerek mAP'in nasıl düştüğü gösterilecek. Bu deney için sentetik veri üreteci gerekir. Üreteç, gri 96 × 96 sahneler üretir; sahnede 0 ila 5 nesne vardır, nesneler daire (0), kare (1) ve üçgen (2) biçimindedir. Nesneler birbirini örtebilir; etiket, nesnenin **görünür** kısmının kutusudur ve görünür alanı 15 pikselin altında kalan nesnelere kutu etiketi verilmez. Üreteç her görüntü için bir sabit tohumla çalışır: aynı tohum her zaman aynı sahneyi verir.

```python
# b67_veri.py: sentetik sahne ve video ureteci (sabit tohum).
# Siniflar: daire (0), kare (1), ucgen (2). Bunlar sentetik "hava
# hedefleri"dir; gercek bir ucus veri kumesi DEGILDIR. Etiket,
# GORUNUR kisminin kutusu ve piksel maskesidir.
import numpy as np

SINIFLAR = ["daire", "kare", "ucgen"]
```

```python
def _sekil(sek, s, cx, cy, xx, yy):
    """Tam (ortusmemis) sekil maskesi. Piksel merkezi x+0.5 alinir."""
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    if sek == 0:  # daire, yaricap s/2
        return dx * dx + dy * dy <= (s / 2) ** 2
    if sek == 1:  # kare, kenar s
        return (np.abs(dx) <= s / 2) & (np.abs(dy) <= s / 2)
    # ucgen: tepe yukarida, taban asagida, yukseklik s
    t = (dy + s / 2) / s  # 0 tepe, 1 taban
    return (t >= 0) & (t <= 1) & (np.abs(dx) <= t * s / 2)
```

```python
def sahne(rng, boyut=96, nmin=0, nmax=5):
    """Bir gri sahne. Donus: img (float32 HxW), nesneler, seg (HxW).
    seg: 0 = arka plan, 1..3 = sinif+1 (gorunur piksel maskesi).
    nesneler: dict listesi (cls, box=[x1,y1,x2,y2) , alan)."""
    W = H = boyut
    olcek = boyut / 96.0
    yy, xx = np.mgrid[0:H, 0:W]
    img = 0.25 + 0.04 * rng.standard_normal((H, W))
    n = int(rng.integers(nmin, nmax + 1))
    adaylar = []
    for _ in range(n):
        s = rng.uniform(8, 24) * olcek
        cx = rng.uniform(s / 2 + 1, W - s / 2 - 1)
        cy = rng.uniform(s / 2 + 1, H - s / 2 - 1)
        sek = int(rng.integers(0, 3))
        par = rng.uniform(0.6, 1.0)
        m = _sekil(sek, s, cx, cy, xx, yy)
        adaylar.append((sek, m, par))
    # Cizim sirasi = katman sirasi: sonra cizilen onceki nesneyi
    # ortusturur.
    gorunur = np.full((H, W), -1, dtype=np.int64)
    for k, (sek, m, par) in enumerate(adaylar):
        gorunur[m] = k
        img[m] = par
    img = np.clip(img + 0.02 * rng.standard_normal((H, W)), 0, 1)
    nesneler, seg = [], np.zeros((H, W), dtype=np.int64)
    for k, (sek, m, par) in enumerate(adaylar):
        mk = gorunur == k
        seg[mk] = sek + 1
        alan = int(mk.sum())
        if alan < 15 * olcek * olcek:  # cok ortulu: kutu etiketi yok
            continue
        ys, xs = np.where(mk)
        box = [int(xs.min()), int(ys.min()), int(xs.max()) + 1,
               int(ys.max()) + 1]
        nesneler.append({"cls": sek, "box": box, "alan": alan})
    return img.astype(np.float32), nesneler, seg
```

```python
def veri_seti(n, seed, boyut=96, nmin=0, nmax=5):
    """n sahneden X (n,1,H,W), kutu listesi ve maske dizisi uretir."""
    rng = np.random.default_rng(seed)
    X = np.zeros((n, 1, boyut, boyut), dtype=np.float32)
    Y, S = [], np.zeros((n, boyut, boyut), dtype=np.int64)
    for i in range(n):
        img, nes, seg = sahne(rng, boyut, nmin, nmax)
        X[i, 0] = img
        Y.append(nes)
        S[i] = seg
    return X, Y, S
```

Aşağıdaki iki blok, takip deneyleri için kullanılan video üreticisini içerir. Video üreticisini bu bölümde ilk olarak takip kısmında kullanacağız; ancak tüm betikler aynı modülden yararlandığı için kod burada tam hâliyle verilir.

```python
def video(seed, T=120, W=200, H=200, p_kacir=0.10, n_rast=4):
    """Sabit hizli, gurultulu hareket eden nesneler (takip icin).
    Nesne 0 ve 1 ayni yolda kesisir (kimlik degisimi riski).
    Nesne 2, 60-70. karelerde tamamen ortulur (ardisik kayip).
    Donus: kareler listesi; her kare: gt_id, gt (xyxy), det (xyxy),
    skor, dedektor tespitleri, ve sahte alarm (clutter) kutulari."""
    rng = np.random.default_rng(seed)
    # (x, y, vx, vy, w, h, t_baslangic, t_bitis)
    nes = [
        (20.0, 100.0, 2.0, 0.30, 16, 16, 0, T),
        (180.0, 104.0, -2.0, -0.20, 16, 16, 0, T),
        (30.0, 40.0, 1.0, 0.60, 14, 14, 0, T),
        (170.0, 160.0, -1.2, -0.80, 18, 18, 5, T),
    ]
    for _ in range(n_rast):  # rastgele ek nesneler
        nes.append((rng.uniform(20, 180), rng.uniform(20, 180),
                    rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5),
                    rng.uniform(12, 20), rng.uniform(12, 20),
                    int(rng.integers(0, 40)), T))
    durum = [list(n) for n in nes]
    kareler = []
    for t in range(T):
        gt_id, gt, det, skor = [], [], [], []
        for k, d in enumerate(durum):
            x, y, vx, vy, w, h, t0, t1 = d
            if not (t0 <= t < t1):
                continue
            # kisa surecli ivme gurultusu, sonra sabit hiz
            d[2] += 0.02 * rng.standard_normal()
            d[3] += 0.02 * rng.standard_normal()
            box = [x - w / 2, y - h / 2, x + w / 2, y + h / 2]
            gt_id.append(k)
            gt.append(box)
            ortulu = (k == 2 and 60 <= t < 70)
            if ortulu or rng.uniform() < p_kacir:
                pass  # dedektor kacirdi
            else:
                gx = x + rng.normal(0, 1.5)
                gy = y + rng.normal(0, 1.5)
                gw = max(4.0, w + rng.normal(0, 1.0))
                gh = max(4.0, h + rng.normal(0, 1.0))
                det.append([gx - gw / 2, gy - gh / 2,
                            gx + gw / 2, gy + gh / 2])
                # gercek nesneler: cogunlukla yuksek, bazen dusuk skor
                if rng.uniform() < 0.2:
                    skor.append(rng.uniform(0.20, 0.45))
                else:
                    skor.append(rng.uniform(0.55, 0.99))
            d[0] += d[2]
            d[1] += d[3]
```

```python
        # sahte alarmlar (Poisson, ortalama 1)
        for _ in range(rng.poisson(1.0)):
            cx, cy = rng.uniform(10, W - 10), rng.uniform(10, H - 10)
            s = rng.uniform(12, 20)
            det.append([cx - s / 2, cy - s / 2,
                        cx + s / 2, cy + s / 2])
            skor.append(rng.uniform(0.10, 0.70))
        kareler.append({"gt_id": gt_id, "gt": gt, "det": det,
                        "skor": skor})
    return kareler


if __name__ == "__main__":
    X, Y, S = veri_seti(200, seed=0)
    adet = [len(y) for y in Y]
    print("sahne:", X.shape, "ort. nesne:", round(np.mean(adet), 2))
    print("sinif sayilari:", np.bincount(
        [o["cls"] for y in Y for o in y]).tolist())
    k = video(seed=1)
    print("video kare:", len(k), "ilk kare tespit:", len(k[0]["det"]))
```

Gürültü deneyi için her görüntü için gerçek kutuların koordinatlarına normal dağılımlı gürültü eklenir (sigma piksel), her görüntüye bir sahte kutu (skor 0,3) eklenir. Şimdi kodu okuyalım: `gurultu_deneyi` sigma'yı 0, 2 ve 5 piksel olarak değiştirir; her sigma için mAP@0,5 (101 nokta) ve mAP@[0,5:0,95] hesaplanır.

```python
def map_hesapla(tahminler, gtler, esik, yontem="tum"):
    """tahminler/gtler: gorsel listesi; her biri (kutular, skorlar,
    sinif) ve (kutular, sinif). Donus: (sinif basina AP, ortalama)."""
    siniflar = sorted({int(c) for _, _, cl in tahminler for c in cl} |
                      {int(c) for _, cl in gtler for c in cl})
    aplar = []
    for s in siniflar:
        skor_l, tp_l, ngt = [], [], 0
        for (tk, ts, tc), (gk, gc) in zip(tahminler, gtler):
            mt = tc == s
            mg = gc == s
            ngt += int(mg.sum())
            kutu = tk[mt]
            puan = ts[mt]
            sira = np.argsort(-puan, kind="stable")
            kutu, puan = kutu[sira], puan[sira]
            tp = eslestir(kutu, gk[mg], esik)
            skor_l.append(puan)
            tp_l.append(tp)
        skor = np.concatenate(skor_l) if skor_l else np.zeros(0)
        tp = np.concatenate(tp_l) if tp_l else np.zeros(0, bool)
        aplar.append(ap_hesapla(skor, tp, ngt, yontem))
    return aplar, float(np.mean(aplar))
```

```python
def el_ile_ornek():
    print("== Elle hesaplanmis ornek (5 tahmin, 4 gercek kutu) ==")
    skor = np.array([0.95, 0.90, 0.85, 0.70, 0.60])
    tp = np.array([1, 0, 1, 1, 0], dtype=bool)
    p, r = pr_egrisi(skor, tp, 4)
    for k in range(5):
        print("tahmin %d: skor=%.2f TP=%d  P=%.4f  R=%.4f"
              % (k + 1, skor[k], tp[k], p[k], r[k]))
    print("AP (11 nokta)   = %.4f" % ap_hesapla(skor, tp, 4, "11"))
    print("AP (tum)        = %.4f" % ap_hesapla(skor, tp, 4, "tum"))
    # Zarfsiz, basamakli toplam (zarf yok): sadece karsilastirma
    basamak = np.sum(np.diff(np.concatenate([[0], r])) * p)
    print("zarfsiz basamak = %.4f  (zarf yok, daha dusuk)" % basamak)
```

```python
def sayisal_dogrulama():
    print("\n== Sayisal integral dogrulamasi (rastgele, tohum 3) ==")
    rng = np.random.default_rng(3)
    hata = 0.0
    for _ in range(50):
        n = int(rng.integers(5, 60))
        skor = rng.uniform(0, 1, n)
        tp = rng.uniform(0, 1, n) < 0.5
        ngt = int(tp.sum() + rng.integers(0, 10))
        ap = ap_hesapla(skor, tp, ngt, "tum")
        p, r = pr_egrisi(skor, tp, ngt)
        # zarf: her r icin max{P_k : R_k >= r}; sayisal integral
        izgara = np.linspace(0, 1, 100001)[:-1] + 0.5 / 100000
        zarf = np.zeros_like(izgara)
        for k in range(len(r) - 1, -1, -1):
            maske = izgara <= r[k]
            zarf[maske] = np.maximum(zarf[maske], p[k])
        sayi = zarf.mean()
        hata = max(hata, abs(sayi - ap))
    print("maks |AP_adim - AP_integral| = %.2e" % hata)
```

```python
def coco_tarzi_map(tahminler, gtler):
    esikler = np.arange(0.5, 0.96, 0.05)
    degerler = []
    for e in esikler:
        _, m = map_hesapla(tahminler, gtler, e, "101")
        degerler.append(m)
    return float(np.mean(degerler)), degerler
```

```python
def gurultu_deneyi():
    print("\n== Kutu gurultusu arttikca mAP (300 gorsel) ==")
    _, Y, _ = veri_seti(300, seed=2024)
    rng = np.random.default_rng(7)
    for sigma in (0.0, 2.0, 5.0):
        tah, gtl = [], []
        for objs in Y:
            gk = np.array([o["box"] for o in objs],
                          float).reshape(-1, 4)
            gc = np.array([o["cls"] for o in objs], int)
            gtl.append((gk, gc))
            kutu = gk + rng.normal(0, sigma, gk.shape)
            puan = rng.uniform(0.5, 1.0, len(gk))
            # her goruntuye 1 sahte kutu (gurultulu) ekle
            sahte = np.array([[5, 5, 20, 20.0]]) + rng.uniform(0, 60)
            kutu = np.vstack([kutu, sahte]) if len(gk) else sahte
            puan = np.concatenate([puan, [0.3]])
            cls = np.concatenate([gc, [0]])
            tah.append((kutu, puan, cls))
        ap5, m5 = map_hesapla(tah, gtl, 0.5, "101")
        m_coco, _ = coco_tarzi_map(tah, gtl)
        print("sigma=%.1f px  mAP@0.5=%.4f  mAP@[.5:.95]=%.4f"
              % (sigma, m5, m_coco))


if __name__ == "__main__":
    el_ile_ornek()
    sayisal_dogrulama()
    gurultu_deneyi()
```

Aşağıdaki çıktı 02 betiğinin tamamıdır. İlk bölüm elle hesaplanan örneği, ikinci bölüm sayısal doğrulamayı, üçüncü bölüm gürültü deneyini gösterir.

```term
$ python b67_02_ap.py
== Elle hesaplanmis ornek (5 tahmin, 4 gercek kutu) ==
tahmin 1: skor=0.95 TP=1  P=1.0000  R=0.2500
tahmin 2: skor=0.90 TP=0  P=0.5000  R=0.2500
tahmin 3: skor=0.85 TP=1  P=0.6667  R=0.5000
tahmin 4: skor=0.70 TP=1  P=0.7500  R=0.7500
tahmin 5: skor=0.60 TP=0  P=0.6000  R=0.7500
AP (11 nokta)   = 0.6136
AP (tum)        = 0.6250
zarfsiz basamak = 0.6042  (zarf yok, daha dusuk)

== Sayisal integral dogrulamasi (rastgele, tohum 3) ==
maks |AP_adim - AP_integral| = 3.47e-06

== Kutu gurultusu arttikca mAP (300 gorsel) ==
sigma=0.0 px  mAP@0.5=1.0000  mAP@[.5:.95]=1.0000
sigma=2.0 px  mAP@0.5=0.7795  mAP@[.5:.95]=0.2722
sigma=5.0 px  mAP@0.5=0.0792  mAP@[.5:.95]=0.0161
```

Çıktı üç şeyi söyler. Birincisi, elle hesaplanan değerler (0,6136 ve 0,6250) kodun verdiği değerlerle birebir aynıdır; bu, fonksiyonların en azından bu örnekte doğru olduğunu gösterir. İkincisi, zarfsız basamaklı toplam (0,6042) tüm noktalar AP'sinden düşüktür; zarf, precision'ı yukarı çeker ve bu yüzden standart yöntemlerde kullanılır. Üçüncüsü ve en önemlisi, gürültü arttıkça mAP@0,5 değeri 1,0'dan 0,78'e, sonra 0,08'e düşer; mAP@[0,5:0,95] ise daha da hızlı düşer (0,27'den 0,016'ya). Bu yüzden bir tespit sisteminin raporunda mAP@[0,5:0,95] ve mAP@0,5 birlikte verilmelidir: ilki yerelleştirme hassasiyetini, ikincisi ayrım gücünü ölçer.

::: dikkat
Eşitlik karşılaştırmaları kayan noktada kırılgandır. Bu bölümü hazırlarken 11 nokta AP'si, recall 0,6 gibi tam değerlerde yanlış sonuç verdi; nedeni `np.linspace` değerinin 0,6000000000000001 çıkmasıydı. Karşılaştırmayı toleransla (`r >= t - 1e-9`) yaptıktan sonra değer 0,6667 oldu. Çözümlü Örnek 3'te bu hatayı adım adım anlatıyoruz.
:::

::: dikkat
Yukarıdaki gürültü deneyinde sahte kutunun skoru 0,3 sabittir ve gerçek kutuların skorları 0,5-1,0 arasındadır. Bu seçim sahte kutuyu hep alt sıralara iter. Gerçek bir sistemde sahte alarmların skor dağılımı gerçek nesnelerle örtüşebilir; o durumda mAP çok daha düşük çıkar. Bu tür bir varsayımı rapora yazmadan sonuçları yorumlama.
:::

## 67.8 Anchor kutuları ve ofset kodlama

Bir ağın doğrudan piksel koordinatlarını tahmin etmesi zordur: 96 piksellik bir görüntüde nesnenin merkezi 0 ile 96 arasında herhangi bir değer alabilir ve ağ her seferinde bu aralığı öğrenmek zorunda kalır. Modern dedektörlerin çözümü **anchor kutuları** (önceden tanımlanmış şekil ve boyutlarda referans kutular) ile **ofset kodlamadır**: ağ, bir anchor'a göre küçük bir düzeltme (ofset) tahmin eder.

Anchor'lar genellikle ızgaranın her hücresine yerleştirilir. Bir hücrenin merkezinde birkaç anchor olabilir; her anchor'ın bir genişlik ve yükseklik çifti vardır. Bir gerçek kutuyu hangi anchor'a atayacağın, şekil IoU'suna bakılarak belirlenir: iki kutu merkezleri çakışacak şekilde yerleştirildiğinde IoU ne kadar büyükse, o anchor kutuyu daha iyi temsil eder. Bu, anchor boyutlarını veri setine uydurman gerektiği anlamına gelir; gerçek sistemlerde anchor'lar genellikle veri üzerinde k-means ile seçilir (genel bilgi).

Ofset kodlamanın iki yaygın biçimi vardır. **Faster R-CNN tarzı** (Ren ve diğerleri, 2015; genel bilgi) kodlama, merkez ofsetini anchor genişliğine göre normalize eder ve genişlik farkını logaritma ile alır:

tx = (gx − ax) / aw,  ty = (gy − ay) / ah,  tw = log(gw / aw),  th = log(gh / ah)

Çözme işlemi tersine çevirmektir: gx = ax + tx·aw, gw = aw·exp(tw). Logaritma sayesinde genişlik farkı negatif olamaz ve küçük ile büyük kutular benzer ölçekte öğrenilir. **YOLO tarzı** kodlama ise hücre içi merkezi bir sigmoid ile [0, 1] aralığına sıkıştırır, genişliği ise anchor'a göre üstel biçimde ayarlar: cx = (gx_hücre + σ(tx))·S, w = aw·exp(tw). Burada S hücre boyudur ve bir nesnenin merkezi yalnızca bir hücreye atanır; bu, sorumluluğun tek bir hücrede toplanmasını sağlar.

Aşağıdaki kod iki kodlamayı yazar, gidiş-dönüş testlerini yapar, anchor'ı şekil IoU'suna göre seçer ve bir görüntünün gerçek kutularını ızgaraya atar. Kodun sabitleri bu bölümdeki dedektörle aynıdır: S = 8 piksel, iki anchor (10 × 10 ve 20 × 20 piksel), 12 × 12 ızgara.

```python
# b67_03_anchor.py: anchor kutulari, kutu ofset kodlama/cozme ve
# hucre-anchor hedef atamasi. Iki kodlama: Faster R-CNN tarzi
# (log-olcek) ve YOLO tarzi (sigmoid ile hucre ici ofset).
import numpy as np
from b67_01_iou_nms import iou_matris

S = 8                                  # hucre boyu (piksel), stride
ANCHORS = np.array([[10.0, 10.0],      # (genislik, yukseklik)
                    [20.0, 20.0]])
```

```python
def frcnn_kodla(kutu, capa):
    """Gercek kutu ve anchor (cx,cy,w,h): ofset ve log-olcek."""
    tx = (kutu[:, 0] - capa[:, 0]) / capa[:, 2]
    ty = (kutu[:, 1] - capa[:, 1]) / capa[:, 3]
    tw = np.log(kutu[:, 2] / capa[:, 2])
    th = np.log(kutu[:, 3] / capa[:, 3])
    return np.stack([tx, ty, tw, th], 1)


def frcnn_coz(t, capa):
    """Ters donusum: ofsetleri kutuya geri cevirir."""
    cx = capa[:, 0] + t[:, 0] * capa[:, 2]
    cy = capa[:, 1] + t[:, 1] * capa[:, 3]
    w = capa[:, 2] * np.exp(t[:, 2])
    h = capa[:, 3] * np.exp(t[:, 3])
    return np.stack([cx, cy, w, h], 1)


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def yolo_coz(ham, hucre, aw):
    """ham: (N,4) ham ag cikisi (tx,ty,tw,th); hucre: (N,2) hucre
    indisleri (gx,gy); aw: (N,2) anchor (w,h). Donus: cx,cy,w,h."""
    cx = (hucre[:, 0] + sigmoid(ham[:, 0])) * S
    cy = (hucre[:, 1] + sigmoid(ham[:, 1])) * S
    w = aw[:, 0] * np.exp(ham[:, 2])
    h = aw[:, 1] * np.exp(ham[:, 3])
    return np.stack([cx, cy, w, h], 1)


def yolo_kodla(kutu_cxcywh, hucre, aw):
    """Yolo_coz'un tersi: ham ag ciktisi hedefi (logit ve log)."""
    ox = kutu_cxcywh[:, 0] / S - hucre[:, 0]
    oy = kutu_cxcywh[:, 1] / S - hucre[:, 1]
    ox, oy = np.clip(ox, 1e-6, 1 - 1e-6), np.clip(oy, 1e-6, 1 - 1e-6)
    tx = np.log(ox / (1 - ox))
    ty = np.log(oy / (1 - oy))
    tw = np.log(kutu_cxcywh[:, 2] / aw[:, 0])
    th = np.log(kutu_cxcywh[:, 3] / aw[:, 1])
    return np.stack([tx, ty, tw, th], 1)
```

```python
def sekil_iou(w, h, aw, ah):
    """Ortak merkezde iki kutunun IoU'su (yalnizca boyuta bakar)."""
    inter = np.minimum(w, aw) * np.minimum(h, ah)
    return inter / (w * h + aw * ah - inter)


def hedefle(kutular, siniflar, G):
    """Gercek kutulari (xyxy, piksel) G x G hucreye ve en iyi anchor'a
    atar. Donus: pozitif maske (G,G,A), hedef kutu (G,G,A,4) [ham],
    sinif (G,G,A) ve cakisma sayisi (ayni hucre+anchor'a iki kutu)."""
    A = len(ANCHORS)
    poz = np.zeros((G, G, A), bool)
    hedef = np.zeros((G, G, A, 4))
    sinif = np.zeros((G, G, A), int)
    cakisma = 0
    for (x1, y1, x2, y2), c in zip(kutular, siniflar):
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        w, h = x2 - x1, y2 - y1
        gx, gy = int(cx // S), int(cy // S)
        gx, gy = min(gx, G - 1), min(gy, G - 1)
        a = int(np.argmax(sekil_iou(w, h, ANCHORS[:, 0],
                                    ANCHORS[:, 1])))
        if poz[gy, gx, a]:
            cakisma += 1
        poz[gy, gx, a] = True
        kut = np.array([[cx, cy, w, h]])
        hucre = np.array([[gx, gy]], float)
        hedef[gy, gx, a] = yolo_kodla(kut, hucre, ANCHORS[a:a + 1])[0]
        sinif[gy, gx, a] = c
    return poz, hedef, sinif, cakisma
```

Aşağıdaki kod anchor testlerinin ilk yarısını içerir (şekil IoU tablosu ve gidiş-dönüş testleri). İkinci yarı hedef atamasını ve doğrulamayı yapar.

```python
def testler():
    rng = np.random.default_rng(0)
    print("== Anchor tablosu: sekil IoU'su (ortak merkez) ==")
    ornek = np.array([[8, 8], [12, 12], [16, 24], [24, 24.0]])
    for w, h in ornek:
        v = sekil_iou(w, h, ANCHORS[:, 0], ANCHORS[:, 1])
        print("kutu %4.0fx%-4.0f  IoU(a1)=%.3f  IoU(a2)=%.3f  -> %d"
              % (w, h, v[0], v[1], int(np.argmax(v)) + 1))
    print("\n== Faster R-CNN kodlama gidis-donus (tohum 0) ==")
    capa = np.column_stack([rng.uniform(20, 70, 500),
                            rng.uniform(20, 70, 500),
                            rng.uniform(6, 30, 500),
                            rng.uniform(6, 30, 500)])
    kutu = capa + rng.normal(0, 1.0, capa.shape) * capa[:, 2:3]
    kutu[:, 2:] = np.abs(kutu[:, 2:]) + 1e-3
    geri = frcnn_coz(frcnn_kodla(kutu, capa), capa)
    print("maks |fark| = %.2e" % np.abs(geri - kutu).max())
    print("\n== YOLO tarzi kodlama gidis-donus ==")
    hucre = rng.integers(0, 12, (500, 2)).astype(float)
    kutu_c = np.column_stack([(hucre[:, 0] + rng.uniform(0.01, 0.99,
                              500)) * S, (hucre[:, 1] + rng.uniform(
                              0.01, 0.99, 500)) * S,
                              rng.uniform(6, 30, 500),
                              rng.uniform(6, 30, 500)])
    aw = ANCHORS[rng.integers(0, 2, 500)]
    geri = yolo_coz(yolo_kodla(kutu_c, hucre, aw), hucre, aw)
    print("maks |fark| = %.2e" % np.abs(geri - kutu_c).max())
```

```python
    print("\n== Hedef atamasi: gorsel basina pozitif ve cakisma ==")
    from b67_veri import veri_seti
    _, Y, _ = veri_seti(300, seed=0)
    pozlar, cakismalar = [], 0
    for objs in Y:
        kut = np.array([o["box"] for o in objs], float).reshape(-1, 4)
        cls = np.array([o["cls"] for o in objs], int)
        poz, _, _, c = hedefle(kut, cls, 12)
        pozlar.append(int(poz.sum()))
        cakismalar += c
    print("ort. pozitif/gorsel = %.2f, nesne = %d, cakisma = %d"
          % (np.mean(pozlar), sum(len(y) for y in Y), cakismalar))
    print("\n== Atama dogrulamasi: en iyi anchor brute force ile ==")
    hata = 0
    for objs in Y[:100]:
        for o in objs:
            x1, y1, x2, y2 = o["box"]
            kut = np.array([[x1, y1, x2, y2]], float)
            w, h = x2 - x1, y2 - y1
            ref = iou_matris(
                np.array([[-w / 2, -h / 2, w / 2, h / 2]], float),
                np.column_stack([-ANCHORS / 2, ANCHORS / 2]))
            beklenen = int(np.argmax(ref[0]))
            poz, _, _, _ = hedefle(kut, [o["cls"]], 12)
            a = int(np.argmax(poz.any(axis=(0, 1))))
            hata += int(a != beklenen)
    print("yanlis anchor atamasi: %d" % hata)
```

```python
if __name__ == "__main__":
    testler()
```

Hedef atamasındaki en önemli karar, hücre ve anchor seçimidir. `hedefle` fonksiyonu gerçek kutunun merkezinin düştüğü hücreyi bulur, sonra şekil IoU'suna göre en iyi anchor'ı seçer. Aynı hücre ve anchor'a iki kutu düşerse ikincisi birincinin üstüne yazılır; kod bu çakışmaları sayar. Aşağıdaki çıktı 03 betiğinin tamamıdır.

```term
$ python b67_03_anchor.py
== Anchor tablosu: sekil IoU'su (ortak merkez) ==
kutu    8x8     IoU(a1)=0.640  IoU(a2)=0.160  -> 1
kutu   12x12    IoU(a1)=0.694  IoU(a2)=0.360  -> 1
kutu   16x24    IoU(a1)=0.260  IoU(a2)=0.690  -> 2
kutu   24x24    IoU(a1)=0.174  IoU(a2)=0.694  -> 2

== Faster R-CNN kodlama gidis-donus (tohum 0) ==
maks |fark| = 1.42e-14

== YOLO tarzi kodlama gidis-donus ==
maks |fark| = 7.11e-15

== Hedef atamasi: gorsel basina pozitif ve cakisma ==
ort. pozitif/gorsel = 2.28, nesne = 687, cakisma = 4

== Atama dogrulamasi: en iyi anchor brute force ile ==
yanlis anchor atamasi: 0
```

Çıktıdaki tablo anchor seçiminin mantığını gösterir: 8 × 8 kutu ve 12 × 12 kutu 10 × 10 anchor'a (a1) daha çok benzer; 16 × 24 ve 24 × 24 kutular ise 20 × 20 anchor'a (a2) daha çok benzer. Gidiş-dönüş hataları 10⁻¹⁴ mertebesinde kalır; bu, iki kodlamanın tersinin gerçekten tersi olduğunu gösterir. Veri üzerinde 300 sahnede 687 gerçek nesne için sahne başına ortalama 2,28 pozitif hücre-anchor çifti çıkar. Dört çakışma vardır: iki nesne aynı hücre ve anchor'a düşmüştür. Atama brute-force ile karşılaştırıldığında 100 sahnede hiç yanlış anchor atanmamıştır.

Şekil 67.4, 12 × 12 ızgarayı, bir gerçek kutuyu ve iki anchor'ı aynı ölçekte gösterir. Gerçek kutunun merkezi 52, 44 noktasındadır; bu merkez 6, 5 hücresinin merkezine denk gelir, bu yüzden ofset 0,5 ve 0,5 olur.

![Şekil 67.4: 12 × 12 ızgara üzerinde gerçek kutu, iki anchor ve hücre ofseti](gorseller/b67_anchor_izgara.png)

## 67.9 Tek aşamalı tespit: YOLO fikri

İki aşamalı dedektörler (R-CNN ailesi; R-CNN 2014, Fast R-CNN 2015, Faster R-CNN 2015, genel bilgi) önce "nesne olabilecek bölgeleri" önerir, sonra her bölgeyi sınıflandırır. Bu yaklaşım doğrudur ama iki ayrı ağ geçişi gerektirir. **Tek aşamalı** dedektörler bu iki adımı tek bir ileri geçişte birleştirir: görüntüyü bir ızgaraya böler ve her hücre için doğrudan kutu, nesnellik ve sınıf tahmin eder.

YOLO (Redmon ve diğerleri, 2016; genel bilgi), bu fikri popüler yapan ilk sistemdir. Görüntü bir S × S ızgaraya bölünür; bir nesnenin merkezi düştüğü hücre o nesneden "sorumludur". Her hücre birkaç kutu ve her kutu için beş sayı tahmin eder: merkez (x, y), genişlik ve yükseklik ile bir **nesnellik skoru** (kutuda bir nesne olma olasılığı × kutunun IoU'su). Ek olarak her hücre bir sınıf olasılık vektörü üretir. Son skor sınıf olasılığı ile nesnelliğin çarpımıdır.

Bu bölümdeki dedektör bu fikri takip eder, ama modern sürümlerin üç önemli farkını içerir. Birincisi anchor kullanır (67.8'de gördün). İkincisi çok ölçekli özellik haritaları kullanır: büyük nesneler için kaba bir harita, küçük nesneler için ince bir harita (FPN, Lin ve diğerleri, 2017; genel bilgi). Üçüncüsü kayıp fonksiyonunda sınıf dengesizliğini hesaba katar (focal loss, genel bilgi).

Kayıp fonksiyonu üç bileşenden oluşur:

- **Nesnellik** (ikili çapraz entropi): her hücre-anchor çifti için "burada bir nesne var mı?" sorusu. Nesne olmayan hücreler çoğunluktadır; bu dengesizliği azaltmak için pozitiflere daha yüksek ağırlık verilebilir.
- **Kutu regresyonu** (MSE): yalnızca pozitif hücreler için ofset ve log-genişlik farkı. YOLO'da bu terim genellikle 5 ile çarpılır.
- **Sınıf** (çapraz entropi): yalnızca pozitif hücreler için sınıf tahmini.

Bu üç terimin ağırlıkları bir hiperparametredir. Kutu terimini ağırlıklandırmak, nesnelliği ağırlıklandırmaktan farklı bir davranış üretir; ağırlıkları seçmek için doğrulama kümesini kullanmalısın.

Anchor-free yaklaşımlar (FCOS, Tian ve diğerleri, 2019; CenterNet, Zhou ve diğerleri, 2019; genel bilgi) anchor'ları kaldırır ve doğrudan nesnenin merkezini ya da kenarlarını tahmin eder. YOLO ailesinin sonraki sürümleri de bu yönde ilerlemiştir; sürüm ayrıntılarını ve hangi sürümün hangi özellikleri kullandığını burada vermiyorum, çünkü bu hızla değişir ve her yeni sürümde mimari ayrıntılar değişebilir.

::: dikkat
YOLO ailesi üzerine yazılan birçok kaynak, sürümler arasındaki farkları karıştırır. Kullandığın kodun hangi sürüme ait olduğunu, hangi kayıp fonksiyonu ve hangi anchor ya da anchor-free yaklaşımı kullandığını kontrol etmeden bir sonuç karşılaştırma. Bu bölümde verdiğimiz şema genel fikirdir, belirli bir sürümün birebir tanımı değildir.
:::

Aşağıdaki kod, bir Ultralytics YOLO modelinin nasıl çağrıldığını gösterir. Bu kod bu bölümde **çalıştırılmamıştır**: önceden eğitilmiş ağırlık dosyası indirmek internet gerektirir ve bu bölümde internetten veri ya da ağırlık indirmiyoruz. Yalnızca API biçimini tanımak için yazılmıştır.

```python
from ultralytics import YOLO

# Bu kod CALISTIRILMADI: agirlik dosyasi internetten iner.
model = YOLO("yolov8n.pt")         # onceden egitilmis agirliklar
sonuc = model("ucus_kaydi.jpg")    # tek karede tespit
for kutu in sonuc[0].boxes:
    print(kutu.cls, kutu.conf, kutu.xyxy)
```

Gerçek projelerde bu API hızlı bir başlangıçtır; ancak bir modelin ne yaptığını anlamak için yukarıdaki kodun her satırının neyi temsil ettiğini bilmen gerekir: `kutu.xyxy` köşe biçimidir, `kutu.conf` sınıf olasılığı ile nesnelliğin çarpımıdır ve `model(...)` içinde NMS zaten uygulanmıştır.

## 67.10 Sıfırdan küçük bir tek aşamalı dedektör

Şimdi yukarıdaki fikirleri sıfırdan uyguluyoruz. Ağ 96 × 96 gri girdi alır, üç konvolüsyon bloğu ile 8 kat küçültür (12 × 12 ızgara), her hücre için iki anchor ve üç sınıf tahmin eder. Kodda kullanılan blok, Bölüm 66'daki konvolüsyon ile Bölüm 64'teki BatchNorm ve ReLU kalıbının aynısıdır; ağ mimarisi bilerek küçük tutulmuştur, çünkü amaç doğru bir tespit hattının bileşenlerini görmektir, gerçek bir sistemde kullanılacak bir model yaratmak değildir.

Eğitim sırasında üç kayıp terimi (nesnellik, kutu, sınıf) birlikte optimize edilir. Nesnelliğin pozitiflerine 3 kat ağırlık verilir (pozitif hücre sayısı az olduğu için), kutu terimi 5 ile çarpılır. Eğitim verisi 2000 sahne (tohum 0), test verisi 500 sahne (tohum 777) ile ayrıdır. Egitim skoru (eğitim kümesinin ilk 300 sahnesi) yalnızca ezberleme olup olmadığını görmek için verilir; başarı iddiası test kümesi üzerinde yapılır.

Aşağıdaki kod modeli, kayıp fonksiyonunu, eğitimi, tahmin çözmeyi (decode) ve mAP değerlendirmesini içerir. Üç tohumla (1, 2, 3) eğitim yapılır; her tohum için ayrı bir model çıkar.

```python
# b67_04_yolo_mini.py: tek asamali (YOLO tarzi) mini dedektor.
# 12x12 izgara, hucre basina 2 anchor, 3 sinif. Sentetik veri,
# GPU egitimi. Egitim: tohum 0 (2000 sahne); test: tohum 777 (500).
import os
import time
import pickle
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from b67_veri import veri_seti
from b67_03_anchor import hedefle, ANCHORS, S, yolo_coz
from b67_01_iou_nms import sinif_nms, xywh_to_xyxy
from b67_02_ap import map_hesapla, coco_tarzi_map

G, A, C = 12, 2, 3
AYGIT = "cuda"
KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
GX, GY = np.meshgrid(np.arange(G), np.arange(G))
```

```python
def cbr(giris, cikis, adim):
    return nn.Sequential(
        nn.Conv2d(giris, cikis, 3, adim, 1, bias=False),
        nn.BatchNorm2d(cikis), nn.ReLU(inplace=True))


class MiniYolo(nn.Module):
    """96x96 gri girdi -> (B, G, G, A, 5+C). Adim 8 (3 kez /2)."""

    def __init__(self):
        super().__init__()
        self.govde = nn.Sequential(cbr(1, 16, 2), cbr(16, 32, 2),
                                   cbr(32, 64, 2), cbr(64, 64, 1))
        self.bas = nn.Conv2d(64, A * (5 + C), 1)

    def forward(self, x):
        y = self.bas(self.govde(x))
        b, _, g, _ = y.shape      # izgara boyutu girdiden okunur
        return y.view(b, A, 5 + C, g, g).permute(0, 3, 4, 1, 2)
```

```python
def hedef_tensorleri(Y):
    """Kutu listesinden egitim hedefleri. Ofsetler (sigmoid uzayi) ve
    log-olcekli genislik/yukseklik hedefleri olarak saklanir."""
    n = len(Y)
    poz = np.zeros((n, G, G, A), bool)
    otg = np.zeros((n, G, G, A, 4), np.float32)
    cls = np.zeros((n, G, G, A), np.int64)
    for i, objs in enumerate(Y):
        kut = np.array([o["box"] for o in objs], float).reshape(-1, 4)
        c = np.array([o["cls"] for o in objs], int)
        p, h, s, _ = hedefle(kut, c, G)
        poz[i], cls[i] = p, s
        otg[i, ..., 0:2] = 1 / (1 + np.exp(-h[..., 0:2]))
        otg[i, ..., 2:4] = h[..., 2:4]
    return poz, otg, cls
```

```python
def kayip(out, poz, otg, cls):
    """Nesnellik (BCE, pozitiflere x3 agirlik) + kutu (MSE, x5)
    + sinif (CE). Kutu ve sinif kaybi yalnizca pozitif hucrelerde."""
    obj = out[..., 4]
    agirlik = torch.tensor(3.0, device=out.device)
    l_obj = F.binary_cross_entropy_with_logits(
        obj, poz.float(), pos_weight=agirlik)
    pb = out[..., :4][poz]
    tb = otg[poz]
    l_box = F.mse_loss(torch.sigmoid(pb[:, 0:2]), tb[:, 0:2]) + \
        F.mse_loss(pb[:, 2:4], tb[:, 2:4])
    l_cls = F.cross_entropy(out[..., 5:][poz], cls[poz])
    return l_obj + 5.0 * l_box + l_cls
```

```python
def egit(seed, X, poz, otg, cls, epoch=60, bs=64):
    torch.manual_seed(seed)
    g = torch.Generator().manual_seed(seed)
    model = MiniYolo().to(AYGIT)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3,
                            weight_decay=1e-4)
    adim = int(np.ceil(len(X) / bs))
    sch = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=2e-3, total_steps=epoch * adim)
    Xt = torch.tensor(X, device=AYGIT)
    Pt = torch.tensor(poz, device=AYGIT)
    Ot = torch.tensor(otg, device=AYGIT)
    Ct = torch.tensor(cls, device=AYGIT)
    model.train()
    for _ in range(epoch):
        perm = torch.randperm(len(X), generator=g)
        for i in range(0, len(X), bs):
            idx = perm[i:i + bs].to(AYGIT)
            out = model(Xt[idx])
            L = kayip(out, Pt[idx], Ot[idx], Ct[idx])
            opt.zero_grad()
            L.backward()
            opt.step()
            sch.step()
    return model.eval()
```

```python
def decode(out, esik=0.05, en_cok=100):
    """(N,G,G,A,8) ham cikti -> gorsel basina (kutu, skor, sinif)."""
    sonuc = []
    for o in out:
        obj = 1 / (1 + np.exp(-o[..., 4]))
        e = np.exp(o[..., 5:] - o[..., 5:].max(-1, keepdims=True))
        pr = e / e.sum(-1, keepdims=True)
        sk = obj[..., None] * pr
        gy, gx, a, c = np.where(sk > esik)
        skor = sk[gy, gx, a, c]
        hc = np.stack([gx, gy], 1).astype(float)
        kut = yolo_coz(o[gy, gx, a, :4], hc, ANCHORS[a])
        kut = np.clip(xywh_to_xyxy(kut), 0, 96)
        tut = sinif_nms(kut, skor, c, 0.5)[:en_cok]
        sonuc.append((kut[tut], skor[tut], c[tut]))
    return sonuc


@torch.no_grad()
def tahmin(model, X):
    cikti = []
    for i in range(0, len(X), 128):
        xb = torch.tensor(X[i:i + 128], device=AYGIT)
        cikti.append(model(xb).float().cpu().numpy())
    return decode(np.concatenate(cikti))
```

```python
def gercek(Y):
    return [(np.array([o["box"] for o in objs], float).reshape(-1, 4),
             np.array([o["cls"] for o in objs], int)) for objs in Y]


def degerlendir(pred, Y):
    """Donus: mAP@0.5 (tum noktalar) ve mAP@[.5:.95] (101 nokta)."""
    gt = gercek(Y)
    _, m50 = map_hesapla(pred, gt, 0.5, "tum")
    m_coco, _ = coco_tarzi_map(pred, gt)
    return m50, m_coco
```

```python
if __name__ == "__main__":
    print("GPU:", torch.cuda.get_device_name(0))
    Xtr, Ytr, _ = veri_seti(2000, seed=0)
    Xte, Yte, _ = veri_seti(500, seed=777)
    Ptr, Otr, Ctr = hedef_tensorleri(Ytr)
    print("egitim pozitif hucre/gorsel: %.2f"
          % Ptr.reshape(len(Ptr), -1).sum(1).mean())
    satirlar = []
    for seed in (1, 2, 3):
        t0 = time.time()
        model = egit(seed, Xtr, Ptr, Otr, Ctr)
        sure = time.time() - t0
        ap_tr, _ = degerlendir(tahmin(model, Xtr[:300]), Ytr[:300])
        ap_te, coco_te = degerlendir(tahmin(model, Xte), Yte)
        print("tohum %d: egitim mAP@0.5=%.4f | test mAP@0.5=%.4f"
              "  test mAP@[.5:.95]=%.4f  (%.0f s)"
              % (seed, ap_tr, ap_te, coco_te, sure))
        satirlar.append((seed, ap_tr, ap_te, coco_te))
        if seed == 1:
            pred1 = tahmin(model, Xte)
            yol = os.path.join(KLASOR, "cnn_pred.pkl")
            with open(yol, "wb") as f:
                pickle.dump(pred1, f)
            torch.save(model.state_dict(),
                       os.path.join(KLASOR, "yolo_t1.pt"))
    te = np.array([s[2] for s in satirlar])
    co = np.array([s[3] for s in satirlar])
    print("test mAP@0.5 = %.4f +- %.4f" % (te.mean(), te.std(ddof=1)))
    print("test mAP@[.5:.95] = %.4f +- %.4f"
          % (co.mean(), co.std(ddof=1)))
    with open(os.path.join(VERI, "b67_yolo_tohum.csv"), "w",
              encoding="utf-8") as f:
        f.write("tohum,egitim_map50,test_map50,test_map_5095\n")
        for s in satirlar:
            f.write("%d,%.4f,%.4f,%.4f\n" % s)
```

`decode` fonksiyonu, tüm ızgara-anchor-sınıf üçlüleri için skoru hesaplar (nesnellik × sınıf olasılığı), 0,05'in üstündekileri alır, kutuyu çözer ve sınıf başına NMS uygular. Bu, Bölüm 67.4'te yazdığımız NMS'in doğrudan kullanımıdır.

Aşağıdaki çıktı 04 betiğinin tamamıdır. Kod 3 tohumla eğitimi yapar, her model için eğitim ve test mAP'ini yazar ve son olarak tohumlar arasında ortalama ± standart sapma verir.

```term
$ python b67_04_yolo_mini.py
GPU: NVIDIA GeForce RTX 3060 Laptop GPU
egitim pozitif hucre/gorsel: 2.48
tohum 1: egitim mAP@0.5=0.9666 | test mAP@0.5=0.9272  test
    mAP@[.5:.95]=0.5758  (13 s)
tohum 2: egitim mAP@0.5=0.9759 | test mAP@0.5=0.9365  test
    mAP@[.5:.95]=0.6253  (12 s)
tohum 3: egitim mAP@0.5=0.9635 | test mAP@0.5=0.9328  test
    mAP@[.5:.95]=0.5873  (13 s)
test mAP@0.5 = 0.9322 +- 0.0047
test mAP@[.5:.95] = 0.5961 +- 0.0259
```

Test kümesinde mAP@0,5 üç tohumda 0,9272, 0,9365 ve 0,9328 çıkmıştır; ortalama 0,9322 ± 0,0047. Aynı tohumlar için mAP@[0,5:0,95] ise 0,5758, 0,6253 ve 0,5873'tür; ortalama 0,5961 ± 0,0259. Eğitim kümesinde mAP@0,5 0,963-0,976 arasındadır (eğitim skoru). Eğitim ve test arasındaki fark (0,03 ile 0,04 arası) ezberlemenin küçük bir işareti olabilir; ama bu sayıda parametreli küçük bir ağ ve 2000 sahnelik veri için bu fark kabul edilebilir düzeydedir, çünkü test skoru yüksek kalmaya devam eder.

Önemli bir uyarı: GPU üzerinde cuDNN, aynı tohumla bile her koşuda biraz farklı indirgeme sırası kullanabilir. Bu bölümü hazırlarken aynı kodu dört kez çalıştırdık. Koşular arasında kodun davranışını değiştirmeyen küçük düzenlemeler de yaptık; tohum başına test mAP@0,5 değerleri 0,925 ile 0,937 arasında kaldı, dört koşunun ortalamaları ise 0,9314 ile 0,9322 arasında çıktı. Tohum sabitlemek sonuçları birebir yeniden üretmek için yeterli değildir; binde birkaç düzeyindeki farklar gerçektir ve bunları raporlarken belirtmelisin. Bu bölümdeki tüm rakamlar, kitaba konan son koşunun çıktısıdır.

Şekil 67.5, test kümesinden altı sahne üzerinde modelin tahminlerini gösterir: yeşil kesikli kutular gerçek nesneler, kırmızı kutular skoru 0,5'in üzerindeki CNN tahminleridir.

Hata analizi (05 betiği) ilginç bir sonuç verir. CNN için skor ≥ 0,5 işletim noktasında, 1265 gerçek kutunun 1050'si bulundu, 26 yanlış pozitif vardı. Kaçırılan 172 kutunun 65'i küçük (alan < 200 piksel kare), 107'si büyük nesnelerdi. Bu, küçük nesnelerin kaçırılma oranının (küçük gerçek kutuların yaklaşık %9'u) büyüklerinkinden (büyük gerçek kutuların yaklaşık %20'si) düşük olduğu anlamına gelir; beklentinin tersidir. Nedenini bu bölümde kesin olarak bilmiyoruz. Bir olasılık, büyük nesnelerin daha sık örtülmesi ve görünür alanın etiketinin şekli tam temsil etmemesidir; bir diğeri, iki sabit anchor'un (10 × 10 ve 20 × 20) en büyük nesneleri yeterince kapsamamasıdır. Bunu ayırt etmek için ablasyon (anchor boyutunu değiştirip yeniden eğitmek) gerekir; bu bölümde yapmadık ve bunu bir alıştırma olarak bırakıyoruz.

![Şekil 67.5: Sentetik test sahneleri: gerçek kutular (yeşil kesik) ve CNN tahminleri (kırmızı, skor ≥ 0,5)](gorseller/b67_tespit_sonuc.png)

## 67.11 Klasik taban, hata analizi ve PR eğrileri

Derin öğrenme bir sonucu ancak bir taban ile yan yana konunca anlam kazanır. Bu yüzden önce klasik bir tespit yöntemi yazıyoruz: görüntüyü bir eşikle ikili maskeye çeviriyor, 8-komşuluklu bağlı bileşenleri buluyor, her bileşen için bir kutu çıkarıyor ve kutunun dolgu oranına bakarak sınıf atıyoruz. Dolgu oranı, bileşenin alanının kutu alanına oranıdır: bir daire için yaklaşık π/4 ≈ 0,785, kare için 1, üçgen için yaklaşık 0,5. Sahne gürültüsü ve nesne parlaklığı (0,6-1,0) arka plandan (0,25) belirgin olduğu için eşik 0,45 seçildi; bu seçim sentetik veriye özgüdür.

Bu yöntem bir CNN'den çok daha basittir ve parametresi az, ama bir zayıflığı vardır: iki nesne birbirine değerse tek bir bileşen olarak görünürler. Aşağıdaki kod hem taban yöntemi hem de CNN tahminlerini aynı test kümesinde değerlendirir ve her gerçek kutuyu dört kategoriden birine koyar: doğru bulundu, yanlış sınıf, yerelleştirme hatası (IoU 0,3-0,5) ve kaçırıldı. Her kategori küçük (alan < 200 piksel kare) ve büyük nesneler için ayrı sayılır.

```python
# b67_05_taban_hata.py: klasik taban (esikleme + bagli bilesen +
# dolgu orani ile siniflandirma) ve CNN/taban hata analizi.
# Test seti ayni: tohum 777, 500 sahne. CNN tahminleri b67_04'ten.
import os
import pickle
import numpy as np
from scipy import ndimage
from b67_veri import veri_seti
from b67_01_iou_nms import iou_matris
from b67_02_ap import map_hesapla
from b67_04_yolo_mini import gercek, degerlendir, VERI, KLASOR

ESIK = 0.45                        # arka plan ~0.25, nesne >= 0.6
DOLGU = {0: np.pi / 4, 1: 1.0, 2: 0.5}  # daire, kare, ucgen
```

```python
def klasik_tespit(img):
    """Esikleme, 8-komsuluk bagli bilesen, kutu ve dolgu orani."""
    etiket, _ = ndimage.label(img > ESIK, structure=np.ones((3, 3)))
    kutular, skor, sinif = [], [], []
    for k, sl in enumerate(ndimage.find_objects(etiket), 1):
        ys, xs = sl
        w, h = xs.stop - xs.start, ys.stop - ys.start
        alan = int((etiket[sl] == k).sum())
        if alan < 15:
            continue
        dolgu = alan / (w * h)
        c = min(DOLGU, key=lambda s: abs(DOLGU[s] - dolgu))
        kutular.append([xs.start, ys.start, xs.stop, ys.stop])
        skor.append(alan / 96.0 ** 2)
        sinif.append(c)
    return (np.array(kutular, float).reshape(-1, 4),
            np.array(skor, float), np.array(sinif, int))
```

```python
def hata_siniflandir(tahmin, Y, esik_skor):
    """Her gercek kutu icin: bulundu, yanlis sinif, yerellestirme,
    kacirildi. Kucuk (<200 px^2) ve buyuk nesneler ayri sayilir."""
    sayac = {"bulundu": [0, 0], "yanlis_sinif": [0, 0],
             "yerellestirme": [0, 0], "kacirildi": [0, 0]}
    fp = 0
    for (tk, ts, tc), objs in zip(tahmin, Y):
        m = ts >= esik_skor
        tk, tc = tk[m], tc[m]
        gk = np.array([o["box"] for o in objs], float).reshape(-1, 4)
        gc = np.array([o["cls"] for o in objs], int)
        iou = iou_matris(gk, tk) if len(tk) else \
            np.zeros((len(gk), 0))
        for i in range(len(gk)):
            alan_i = (gk[i, 2] - gk[i, 0]) * (gk[i, 3] - gk[i, 1])
            kucuk = alan_i < 200
            grup = 1 if kucuk else 0
            if iou.shape[1] == 0:
                sayac["kacirildi"][grup] += 1
                continue
            j = int(np.argmax(iou[i]))
            v = iou[i, j]
            if v >= 0.5 and tc[j] == gc[i]:
                sayac["bulundu"][grup] += 1
            elif v >= 0.5:
                sayac["yanlis_sinif"][grup] += 1
            elif v >= 0.3:
                sayac["yerellestirme"][grup] += 1
            else:
                sayac["kacirildi"][grup] += 1
        if len(tk):
            en_iyi = iou.max(axis=0) if len(gk) else np.zeros(len(tk))
            fp += int((en_iyi < 0.5).sum())
    return sayac, fp
```

```python
def yazdir(ad, sayac, fp, toplam):
    print("%s (toplam gercek kutu = %d, yanlis pozitif = %d)"
          % (ad, toplam, fp))
    for anahtar, (k, b) in sayac.items():
        print("   %-14s kucuk=%4d  buyuk=%4d" % (anahtar, k, b))
```

```python
if __name__ == "__main__":
    Xte, Yte, _ = veri_seti(500, seed=777)
    toplam = sum(len(y) for y in Yte)
    gt = gercek(Yte)

    taban = [klasik_tespit(img[0]) for img in Xte]
    _, m50_t = map_hesapla(taban, gt, 0.5, "tum")
    print("Klasik taban: mAP@0.5 = %.4f" % m50_t)
    # pickle: yalnizca bu projenin b67_04 betiginin kendi urettigi,
    # yerel bir ara dosya okunuyor (guvenilmeyen kaynak degil).
    with open(os.path.join(KLASOR, "cnn_pred.pkl"), "rb") as f:
        cnn = pickle.load(f)
    m50_c, mco_c = degerlendir(cnn, Yte)
    print("CNN (tohum 1): mAP@0.5 = %.4f, mAP@[.5:.95] = %.4f"
          % (m50_c, mco_c))

    print("\n== Hata analizi (CNN skor >= 0.50; taban hepsi) ==")
    s_c, fp_c = hata_siniflandir(cnn, Yte, 0.50)
    s_t, fp_t = hata_siniflandir(taban, Yte, 0.0)
    yazdir("CNN", s_c, fp_c, toplam)
    yazdir("Taban", s_t, fp_t, toplam)

    kayit = os.path.join(VERI, "b67_hata_analizi.csv")
    with open(kayit, "w", encoding="utf-8") as f:
        f.write("yontem,kategori,kucuk,buyuk,yanlis_pozitif\n")
        for ad, s, fp in (("cnn", s_c, fp_c), ("taban", s_t, fp_t)):
            for anahtar, (k, b) in s.items():
                f.write("%s,%s,%d,%d,%d\n"
                        % (ad, anahtar, k, b,
                           fp if anahtar == "bulundu" else 0))
    print("\nkaydedildi:", kayit)
```

Aşağıdaki çıktı 05 betiğinin tamamıdır. CNN satırında işletim noktası skor ≥ 0,5 olarak alınmıştır; taban yöntemde her tespit değerlendirmeye dahildir.

```term
$ python b67_05_taban_hata.py
Klasik taban: mAP@0.5 = 0.7144
CNN (tohum 1): mAP@0.5 = 0.9272, mAP@[.5:.95] = 0.5758

== Hata analizi (CNN skor >= 0.50; taban hepsi) ==
CNN (toplam gercek kutu = 1265, yanlis pozitif = 26)
   bulundu        kucuk= 646  buyuk= 404
   yanlis_sinif   kucuk=  10  buyuk=   3
   yerellestirme  kucuk=  16  buyuk=  14
   kacirildi      kucuk=  65  buyuk= 107
Taban (toplam gercek kutu = 1265, yanlis pozitif = 47)
   bulundu        kucuk= 564  buyuk= 429
   yanlis_sinif   kucuk=  52  buyuk=   2
   yerellestirme  kucuk=  85  buyuk=  17
   kacirildi      kucuk=  36  buyuk=  80

kaydedildi: D:/Mevcut Projeler/Kitap/engine/veri\b67_hata_analizi.csv
```

Klasik taban test kümesinde mAP@0,5 = 0,7144 üretiyor; CNN (tohum 1) ise 0,9272. Taban yöntem için bu sonuç, sentetik verinin klasik yöntemler için görece kolay olduğunu da gösterir: nesneler parlak, arka plan düzgün ve gürültü düşük. Gerçek bir görüntüde (yağmur, sis, değişken arka plan) aynı eşik çalışmaz; bu yüzden bu karşılaştırmadan "derin öğrenme her zaman kazanır" sonucunu çıkarma. Çıkarılacak ders, yöntemleri aynı test kümesi ve aynı metrikle karşılaştırmaktır.

Hata dağılımı iki ilginç şeyi ortaya koyar. Birincisi, taban yöntemin hatalarının çoğu küçük nesnelerde yoğunlaşır: 52 küçük nesne yanlış sınıflanmış (dolgu oranı küçük nesnelerde gürültüye duyarlıdır) ve 85 küçük nesnede yerelleştirme hatası (IoU 0,3-0,5) vardır. Bu, eşikleme sınırının nesne kenarını kesmiş olabileceğini düşündürür; ama bunu doğrulamadık. İkincisi, büyük nesnelerde taban yöntem 80 kutuyu kaçırırken CNN 107 kutu kaçırıyor; yani bu kategoride taban CNN'den daha az kaçırıyor. Bunun olası nedeni, birbirine değen büyük nesnelerin tek bir bileşen oluşturması ve bu bileşenin ya hiç kutu üretmemesi ya da yanlış sınıfla tek kutu üretmesidir; ama bu açıklamayı ayrıca sınamadık.

CNN tarafında tablo başka bir şey söyler: 1265 gerçek kutunun 1050'si bulunmuş, 26 yanlış pozitif olmuştur. Kaçırılan 172 kutunun 107'si büyük nesnedir. Bu sonuç 67.10'da tartıştığımız, beklentinin tersi olan örüntüyü doğrular.

Şekil 67.6, aynı test kümesinde CNN'in sınıf başına PR eğrisini gösterir. Her sınıf için AP ayrı hesaplanmış, mAP ise üç sınıfın ortalamasıdır. Eğrilerin yüksek precision ile yüksek recall'a ulaştığı noktaya kadar düz gitmesi, modelin skor sırasının iyi olduğunu gösterir. Eğrinin sağ alt kısmındaki dik düşüş ise son yüzde birkaç gerçek kutunun düşük skorlarla geldiği ve bunların yanlış pozitiflerle karıştığı bölgedir.

```python
# b67_06_pr_ornek.py: sinif basina PR egrisi ve AP (CNN ve taban),
# sekil icin ornek tespit verisinin disari aktarimi.
import os
import pickle
import numpy as np
from b67_veri import veri_seti, SINIFLAR
from b67_02_ap import eslestir, pr_egrisi, ap_hesapla
from b67_04_yolo_mini import VERI, KLASOR
from b67_05_taban_hata import klasik_tespit
```

```python
def sinif_pr(tahmin, Y, sinif, esik=0.5):
    """Tek sinif icin skor sirali PR ve AP (tum noktalar)."""
    skor, tp, ngt = [], [], 0
    for (tk, ts, tc), objs in zip(tahmin, Y):
        gk = np.array([o["box"] for o in objs], float).reshape(-1, 4)
        gc = np.array([o["cls"] for o in objs], int)
        mg, mt = gc == sinif, tc == sinif
        ngt += int(mg.sum())
        kk, ss = tk[mt], ts[mt]
        sira = np.argsort(-ss, kind="stable")
        kk, ss = kk[sira], ss[sira]
        skor.append(ss)
        tp.append(eslestir(kk, gk[mg], esik))
    skor = np.concatenate(skor)
    tp = np.concatenate(tp)
    p, r = pr_egrisi(skor, tp, ngt)
    return p, r, ap_hesapla(skor, tp, ngt, "tum")
```

```python
if __name__ == "__main__":
    Xte, Yte, _ = veri_seti(500, seed=777)
    taban = [klasik_tespit(img[0]) for img in Xte]
    with open(os.path.join(KLASOR, "cnn_pred.pkl"), "rb") as f:
        cnn = pickle.load(f)  # yerel, kendi urettigimiz ara dosya

    satirlar = ["yontem,sinif,recall,precision"]
    for ad, tah in (("cnn", cnn), ("taban", taban)):
        print("== %s: sinif basina AP (tum noktalar) ==" % ad)
        aplar = []
        for s, isim in enumerate(SINIFLAR):
            p, r, ap = sinif_pr(tah, Yte, s)
            aplar.append(ap)
            print("%-6s AP = %.4f  (son recall = %.3f)"
                  % (isim, ap, r[-1] if len(r) else 0.0))
            for ri, pi in zip(r[::5], p[::5]):
                satirlar.append("%s,%s,%.4f,%.4f"
                                % (ad, isim, ri, pi))
        print("mAP@0.5 = %.4f\n" % np.mean(aplar))

    with open(os.path.join(VERI, "b67_pr_egri.csv"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")

    # Sekil icin: ilk 6 test sahnesi, kutular ve sinif adlari
    ornek = [0, 1, 2, 3, 4, 5]
    sat = ["gorsel,tur,sinif,skor,x1,y1,x2,y2"]
    for i in ornek:
        for o in Yte[i]:
            x1, y1, x2, y2 = o["box"]
            sat.append("%d,gercek,%s,1.00,%d,%d,%d,%d"
                       % (i, SINIFLAR[o["cls"]], x1, y1, x2, y2))
        kk, ss, cc = cnn[i]
        for b, s_, c in zip(kk, ss, cc):
            if s_ >= 0.5:
                sat.append("%d,cnn,%s,%.2f,%d,%d,%d,%d" % (
                    i, SINIFLAR[c], s_, b[0], b[1], b[2], b[3]))
    with open(os.path.join(VERI, "b67_tespit_ornek.csv"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(sat) + "\n")
    np.savez_compressed(os.path.join(VERI, "b67_ornek_sahne.npz"),
                        X=Xte[ornek, 0])
    print("ornek satir sayisi:", len(sat) - 1)
    print("kaydedildi: engine/veri/b67_pr_egri.csv,")
    print("            engine/veri/b67_tespit_ornek.csv")
```

```term
$ python b67_06_pr_ornek.py
== cnn: sinif basina AP (tum noktalar) ==
daire  AP = 0.9360  (son recall = 0.955)
kare   AP = 0.9572  (son recall = 0.968)
ucgen  AP = 0.8884  (son recall = 0.919)
mAP@0.5 = 0.9272

== taban: sinif basina AP (tum noktalar) ==
daire  AP = 0.6747  (son recall = 0.783)
kare   AP = 0.7179  (son recall = 0.718)
ucgen  AP = 0.7506  (son recall = 0.836)
mAP@0.5 = 0.7144

ornek satir sayisi: 30
kaydedildi: engine/veri/b67_pr_egri.csv,
            engine/veri/b67_tespit_ornek.csv
```

Aşağıdaki PR şekli, bu çıktıdaki sınıf başına eğrilerin çizimidir. Eğriler `b67_pr_egri.csv` dosyasındaki değerlerden çizilir; her eğriden her beşinci nokta alınmıştır, bu yüzden şekil ile AP değerleri arasında küçük bir görsel fark olabilir.

![Şekil 67.6: CNN için sınıf başına precision–recall eğrisi, IoU ≥ 0,5 (test kümesi)](gorseller/b67_pr_egri.png)

## 67.12 Anlamsal segmentasyon: piksel düzeyinde kayıp

Tespit bize bir kutu verir; segmentasyon ise her pikseli bir sınıfa atar. Bu, çıktının boyutunun (96 × 96 × 4 bu bölüm için) ve kayıp fonksiyonunun değişmesi anlamına gelir. Girdi görüntüsünün her pikseli için bir sınıf olasılık vektörü üretilir; eğitim kaybı bu piksellerin hepsi üzerinden hesaplanır.

En basit kayıp piksel başına çapraz entropidir: L_CE = −(1/N) Σ log p(y_i). Ama sınıflar dengesizse (çoğu piksel arka plan, nesneler küçük) bu kayıp arka planı öğrenerek düşük bir değere ulaşabilir ve nesneleri ihmal edebilir. Bu yüzden segmentasyonda sık kullanılan ikinci bir terim **Dice kaybıdır**. Dice katsayısı iki kümenin örtüşmesini ölçer:

Dice(X, Y) = 2 |X ∩ Y| / (|X| + |Y|)

Yumuşak (soft) sürümde X yerine olasılıklar kullanılır: her sınıf için p ile gerçek maskenin çarpımı toplanır. Dice kaybı 1 − Dice'tır. Arka plan sınıfı için Dice hesaplamak genellikle anlamsız olur (arka plan çok büyüktür ve tahmini kolaydır), bu yüzden kayıp yalnızca nesne sınıfları üzerinden ortalanır. Bu bölümde kullanılan kayıp, piksel çapraz entropisi ile arka plan hariç yumuşak Dice'ın toplamıdır.

Segmentasyonun ölçümü için mIoU (sınıf başına IoU'nun ortalaması) ve Dice kullanılır. IoU ile Dice birbirine bağlıdır: Dice = 2·IoU / (1 + IoU). Ama ortalamaları farklıdır; bu yüzden raporda hangisinin kullanıldığını belirtmek gerekir.

Son olarak, sınır pikselleri segmentasyonun en zor kısmıdır. Bir nesnenin iç kısmındaki pikseller kolayca doğru sınıflanır; kenarda ise tek piksellik bir kayma bile sınır hatası sayılır. Bu yüzden bu bölümde, gerçek maskenin sınırından iki piksel içeride kalan bölgedeki doğruluğu ayrıca raporluyoruz. Bu, U-Net'in atlama bağlantısının neden önemli olduğunu gösteren ölçümdür.

## 67.13 U-Net: kodlayıcı, çözücü ve atlama bağlantıları

Segmentasyon için en bilinen mimari U-Net'tir (Ronneberger ve diğerleri, 2015; genel bilgi). Adını şeklinden alır: sol kol **kodlayıcıdır** (encoder), görüntüyü küçülterek ne olduğunu (bağlam) öğrenir; sağ kol **çözücüdür** (decoder), özellik haritalarını yeniden büyüterek her pikseli sınıflandırır. Kodlayıcıdan çözücüye uzanan **atlama bağlantıları** (skip connections), kodlayıcının her ölçekteki ayrıntılı özelliklerini çözücüye doğrudan taşır.

Atlama bağlantısının neden gerekli olduğunu görmek için şu soruyu sor: bir nesnenin sınırını doğru çizmek için hangi bilgiye ihtiyacın var? Sınır, ince bir ayrıntıdır; küçük bir ızgarada (12 × 12) bu ayrıntı çoktan kaybolmuştur. Bağlantı olmadan çözücü sınırı yalnızca en derin, en kaba haritadan tahmin etmek zorundadır. Atlama bağlantısıyla ise çözücü her ölçekte kodlayıcının ince özelliklerini yanına alır. Bu bölümde bunu bir ablasyonla ölçüyoruz: aynı mimariyi bir kez atlama bağlantılarıyla, bir kez onlarsız eğitiyoruz.

Şekil 67.7, bu bölümde kullandığımız mimariyi gösterir: 96 × 96 girdi, 16, 32, 64 kanallı kodlayıcı blokları, 12 × 12 × 128 orta katman ve simetrik bir çözücü. Çözücüdeki büyütme işlemi bir **transpoze konvolüsyon** (ConvTranspose2d, 2 × 2, adım 2) ile yapılır; bu, öğrenilebilir bir büyütmedir. Büyütülmüş harita, aynı ölçekteki kodlayıcı haritasıyla kanal boyutunda birleştirilir (torch.cat) ve bir konvolüsyon bloğundan geçer.

![Şekil 67.7: U-Net: kodlayıcı, orta katman, çözücü ve atlama bağlantıları](gorseller/b67_unet_mimari.png)

Kayıp fonksiyonu 67.12'de anlatılan biçimdedir: piksel başına çapraz entropi ile arka plan hariç yumuşak Dice kaybının toplamı. Eğitim 2000 sahne (tohum 0), 30 epoch, AdamW ve bir OneCycle öğrenme hızı programı ile yapılır. Test kümesi 500 sahneden oluşur (tohum 777) ve eğitimde hiç kullanılmaz. Eğitim kümesinin ilk 300 sahnesindeki mIoU, yalnızca ezberlemeyi görmek için verilir ve "eğitim" diye etiketlenir.

Aşağıdaki kod U-Net'i, kaybı, eğitimi, tahmini ve ölçümleri içerir. `UNet(atlama=False)` ablasyon için kullanılır: çözücü bloklarına kodlayıcı özelliği birleştirilmez ve kanal sayıları buna göre küçülür.

```python
# b67_07_unet.py: sifirdan U-Net (anlamsal segmentasyon), atlama
# baglantisi ablasyonu, CE + Dice kaybi. 4 sinif: arka plan, daire,
# kare, ucgen. Test: tohum 777 (500 sahne), egitim: tohum 0.
import os
import time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy import ndimage
from b67_veri import veri_seti

C = 4
AYGIT = "cuda"
KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def blok(giris, cikis):
    """Iki 3x3 konvolusyon + BatchNorm + ReLU."""
    return nn.Sequential(
        nn.Conv2d(giris, cikis, 3, 1, 1, bias=False),
        nn.BatchNorm2d(cikis), nn.ReLU(inplace=True),
        nn.Conv2d(cikis, cikis, 3, 1, 1, bias=False),
        nn.BatchNorm2d(cikis), nn.ReLU(inplace=True))
```

```python
class UNet(nn.Module):
    """Kodlayici 96 -> 48 -> 24 -> 12; cozucu 12 -> 24 -> 48 -> 96.
    atlama=True: kodlayici ozellikleri cozucuye birlestirilir."""

    def __init__(self, atlama=True):
        super().__init__()
        self.atlama = atlama
        self.e1 = blok(1, 16)
        self.e2 = blok(16, 32)
        self.e3 = blok(32, 64)
        self.orta = blok(64, 128)
        self.havuz = nn.MaxPool2d(2)
        self.u3 = nn.ConvTranspose2d(128, 64, 2, 2)
        self.d3 = blok(128 if atlama else 64, 64)
        self.u2 = nn.ConvTranspose2d(64, 32, 2, 2)
        self.d2 = blok(64 if atlama else 32, 32)
        self.u1 = nn.ConvTranspose2d(32, 16, 2, 2)
        self.d1 = blok(32 if atlama else 16, 16)
        self.son = nn.Conv2d(16, C, 1)

    def forward(self, x):
        e1 = self.e1(x)
        e2 = self.e2(self.havuz(e1))
        e3 = self.e3(self.havuz(e2))
        b = self.orta(self.havuz(e3))
        d = self.u3(b)
        d = self.d3(torch.cat([d, e3], 1) if self.atlama else d)
        d = self.u2(d)
        d = self.d2(torch.cat([d, e2], 1) if self.atlama else d)
        d = self.u1(d)
        d = self.d1(torch.cat([d, e1], 1) if self.atlama else d)
        return self.son(d)
```

```python
def kayip(logit, y):
    """Piksel basina CE + arka plan haric yumusak Dice."""
    ce = F.cross_entropy(logit, y)
    p = torch.softmax(logit, 1)
    oh = F.one_hot(y, C).permute(0, 3, 1, 2).float()
    kesisim = (p * oh).sum((0, 2, 3))
    toplam = p.sum((0, 2, 3)) + oh.sum((0, 2, 3))
    dice = (2 * kesisim + 1) / (toplam + 1)
    return ce + (1 - dice[1:].mean())
```

```python
def egit(seed, X, Y, atlama, epoch=30, bs=32):
    torch.manual_seed(seed)
    g = torch.Generator().manual_seed(seed)
    model = UNet(atlama).to(AYGIT)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3,
                            weight_decay=1e-4)
    adim = int(np.ceil(len(X) / bs))
    sch = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=2e-3, total_steps=epoch * adim)
    Xt = torch.tensor(X, device=AYGIT)
    Yt = torch.tensor(Y, device=AYGIT)
    model.train()
    for _ in range(epoch):
        perm = torch.randperm(len(X), generator=g)
        for i in range(0, len(X), bs):
            idx = perm[i:i + bs].to(AYGIT)
            L = kayip(model(Xt[idx]), Yt[idx])
            opt.zero_grad()
            L.backward()
            opt.step()
            sch.step()
    return model.eval()


@torch.no_grad()
```

```python
def tahmin(model, X):
    out = []
    for i in range(0, len(X), 100):
        xb = torch.tensor(X[i:i + 100], device=AYGIT)
        out.append(model(xb).argmax(1).cpu().numpy())
    return np.concatenate(out)
```

```python
def sinir_bandi(y, genislik=2):
    """Gercek maskede sinir piksellerinin genislik-2 komsulugu."""
    e = np.zeros(y.shape, bool)
    e[:, 1:] |= y[:, 1:] != y[:, :-1]
    e[:, :-1] |= y[:, :-1] != y[:, 1:]
    e[1:, :] |= y[1:, :] != y[:-1, :]
    e[:-1, :] |= y[:-1, :] != y[1:, :]
    return np.stack([ndimage.binary_dilation(m, iterations=genislik)
                     for m in e])
```

```python
def olcu(p, y):
    """mIoU (4 sinif), foreground Dice ve sinir bandi dogrulugu."""
    kar = np.zeros((C, C), np.int64)
    np.add.at(kar, (y.ravel(), p.ravel()), 1)
    tp = np.diag(kar).astype(float)
    fp = kar.sum(0) - tp
    fn = kar.sum(1) - tp
    iou = tp / np.maximum(tp + fp + fn, 1)
    dice = 2 * tp[1:] / np.maximum(2 * tp[1:] + fp[1:] + fn[1:], 1)
    band = sinir_bandi(y)
    sinir = float((p[band] == y[band]).mean())
    return float(iou.mean()), float(dice.mean()), sinir, iou
```

```python
if __name__ == "__main__":
    print("GPU:", torch.cuda.get_device_name(0))
    Xtr, _, Str = veri_seti(2000, seed=0)
    Xte, _, Ste = veri_seti(500, seed=777)
    satirlar = ["atlama,tohum,mIoU,dice_on_plan,sinir_bandi"]
    for atlama in (True, False):
        ad = "atlamali" if atlama else "atlamasiz"
        for seed in (1, 2, 3):
            t0 = time.time()
            model = egit(seed, Xtr, Str, atlama)
            sure = time.time() - t0
            miou_tr, _, _, _ = olcu(tahmin(model, Xtr[:300]),
                                    Str[:300])
            p = tahmin(model, Xte)
            miou, dice, sinir, iou = olcu(p, Ste)
            print("%-10s tohum %d: test mIoU=%.4f  Dice(on)=%.4f  "
                  "sinir bandi=%.4f  [egitim mIoU=%.4f]  (%.0f s)"
                  % (ad, seed, miou, dice, sinir, miou_tr, sure))
            print("           sinif IoU (arka, daire, kare, ucgen):",
                  np.round(iou, 3).tolist())
            satirlar.append("%s,%d,%.4f,%.4f,%.4f"
                            % (ad, seed, miou, dice, sinir))
            if atlama and seed == 1:
                np.savez_compressed(
                    os.path.join(VERI, "b67_unet_ornek.npz"),
                    gercek=Ste[:6], tahmin=p[:6], X=Xte[:6, 0])
    with open(os.path.join(VERI, "b67_unet.csv"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
```

`sinir_bandi` fonksiyonu, gerçek maskede sınır piksellerini (komşusu farklı sınıfta olan pikseller) bulur ve iki piksel genişliğinde bir bant çıkarır. `olcu` fonksiyonu mIoU, sınıf başına IoU, Dice ve bu bant üzerindeki doğruluğu hesaplar.

Aşağıdaki çıktı 07 betiğinin tamamıdır. Üç tohum ve iki mimari için altı koşu yapılmıştır. Süreler (45-50 saniye) yalnızca kabaca bilgi içindir; bu koşularda GPU ölçüm amaçlı boşaltılmamıştır.

```term
$ python b67_07_unet.py
GPU: NVIDIA GeForce RTX 3060 Laptop GPU
atlamali   tohum 1: test mIoU=0.9860  Dice(on)=0.9906  sinir bandi=0.9977 
    [egitim mIoU=0.9969]  (47 s)
           sinif IoU (arka, daire, kare, ucgen): [1.0, 0.98, 0.983, 0.981]
atlamali   tohum 2: test mIoU=0.9871  Dice(on)=0.9913  sinir bandi=0.9979 
    [egitim mIoU=0.9942]  (49 s)
sinif IoU (arka, daire, kare, ucgen): [1.0, 0.981, 0.985, 0.983]
atlamali   tohum 3: test mIoU=0.9866  Dice(on)=0.9910  sinir bandi=0.9979 
    [egitim mIoU=0.9945]  (50 s)
sinif IoU (arka, daire, kare, ucgen): [1.0, 0.982, 0.986, 0.979]
atlamasiz  tohum 1: test mIoU=0.9731  Dice(on)=0.9818  sinir bandi=0.9944 
    [egitim mIoU=0.9918]  (45 s)
sinif IoU (arka, daire, kare, ucgen): [0.999, 0.956, 0.973, 0.964]
atlamasiz  tohum 2: test mIoU=0.9711  Dice(on)=0.9805  sinir bandi=0.9938 
    [egitim mIoU=0.9906]  (45 s)
sinif IoU (arka, daire, kare, ucgen): [0.999, 0.951, 0.97, 0.965]
atlamasiz  tohum 3: test mIoU=0.9729  Dice(on)=0.9817  sinir bandi=0.9943 
    [egitim mIoU=0.9922]  (47 s)
sinif IoU (arka, daire, kare, ucgen): [0.999, 0.954, 0.973, 0.965]
```

Sonuçlar iki ayrı soruyu yanıtlar. İlki, U-Net'in sentetik segmentasyonu ne kadar iyi yaptığıdır: atlama bağlantılı modelde test mIoU 0,9866 ± 0,0006 (üç tohum, ortalama ± örnek standart sapma), Dice (yalnızca nesne sınıfları) 0,9910 ± 0,0004'tür. Eğitim kümesinin mIoU'su 0,9952 çıkmıştır; bu fark küçüktür, yani ağ ezberlemeye yakın bir çalışma yapmamıştır, ama test skorunu eğitim skorundan ayrı olarak raporluyoruz.

İkincisi, atlama bağlantısının ne kazandırdığıdır. Atlamasız mimari test mIoU'sunda 0,9724 ± 0,0011 ve Dice'ta 0,9813 ± 0,0007 çıkmıştır. Fark mIoU'da yaklaşık 0,014'tür. Asıl dikkat çekici fark sınır bandında görülür: atlamalı modelde 0,9978 ± 0,0001, atlamasız modelde 0,9942 ± 0,0003. Sınıf başına IoU'ya bakıldığında fark en çok daire sınıfındadır (ortalama 0,981'e karşı 0,954); dairenin eğri sınırı, bağlantısız çözücünün en kötü yaptığı yerdir. Kare ve üçgen sınıflarındaki fark daha küçüktür (yaklaşık 0,013 ve 0,016); düz kenarlar bağlantısız çözücü için daha kolaydır.

Bu ablasyon bir sınırlamaya da dikkat çekiyor. Her iki mimari için üç tohum kullandık ve tohumlar arasındaki sapma (0,0006-0,0011) mimari farkın (0,014) yanında küçüktür; bu yüzden fark güvenilirdir. Ancak sınır bandı farkı (0,0036) daha küçüktür ve yine de her üç tohumda aynı yönde kalmıştır. Yine de sentetik veri üzerindeki bu sonuçların gerçek bir sahneye taşınabileceğini varsayma: gerçek görüntülerde sınıf sayısı, sınır karmaşıklığı ve nesne dokusu farklıdır.

Şekil 67.8, test kümesinden üç sahnede girdiyi, gerçek maskeyi ve atlamalı modelin tahminini gösterir. Tahmin ile gerçek maske görsel olarak neredeyse aynıdır. Piksel düzeyindeki hata haritasını bu bölümde ayrıca çizmedik; sınır bandı ölçümü bu farkı sayısal olarak verir.

![Şekil 67.8: Atlamalı U-Net (tohum 1): girdi, gerçek maske ve tahmin](gorseller/b67_segmentasyon.png)

::: ipucu
Segmentasyon ölçülerini raporlarken yalnızca mIoU vermek yanıltıcı olabilir. Nesneler görüntünün küçük bir kısmını kapladığında arka plan IoU'su yüksek çıkar ve ortalamayı şişirir. Bu yüzden nesne sınıflarının IoU'sunu, Dice'ı ve sınır bandı doğruluğunu ayrı ayrı raporla.
:::

## 67.14 Örnek segmentasyonu: aynı sınıftan iki nesneyi ayırmak

Anlamsal segmentasyon, iki daireyi birbirine değdiğinde tek bir "daire" bölgesi olarak görür. Örnek segmentasyonu her nesneye ayrı bir maske verir. Bunun için iki ana yaklaşım vardır. **Önce tespit, sonra maske** yaklaşımında (Mask R-CNN, He ve diğerleri, 2017; genel bilgi) bir dedektör her nesne için kutu üretir, sonra her kutunun içinde küçük bir ağ bir ikili maske tahmin eder. **Yoğunluk tabanlı** yaklaşımlarda ise her piksel için bir "hangi nesneye ait" vektörü öğrenilir ve bu vektörlerin kümelenmesi nesneleri ayırır.

Bu bölümde örnek segmentasyonunu kodlamadık; ama yukarıdaki görev şeklindeki örnek panelinde yaptığımız şey, bağlı bileşen analiziyle sınıf maskelerinden nesneleri ayırmaktır. Bu yöntem, nesnelerin birbirine değmediği durumda çalışır. Birbirine değen aynı sınıftan iki nesne tek bir bileşen olarak görünür ve yöntem onları ayıramaz. Mask R-CNN'in ve diğer örnek segmentasyon yöntemlerinin varlık sebebi tam olarak budur.

Örnek segmentasyonunun ölçümü, mask-AP adıyla, kutu IoU'su yerine maske IoU'su ile yapılan bir AP'dir (genel bilgi). Bu bölümde yalnızca fikri ve neden gerektiğini gösterdik; bir örnek segmentasyon ağını sıfırdan eğitmek bu bölümün kapsamının dışındadır.

## 67.15 Çoklu nesne takibi: tespit-ile-takip ve Kalman

Bir İHA'nın kamerasında aynı araç on kare boyunca görünür. Tespit ağı her karede o aracı bağımsız olarak bulur ama bu tespitlerin hangisinin hangi önceki tespitle aynı nesne olduğunu söylemez. **Çoklu nesne takibi** (MOT, Multiple Object Tracking) bu bağı kurar: her nesneye bir kimlik verir ve kareler boyunca bu kimliği korur. Bu bölümde kullandığımız yaklaşım **tespit-ile-takip**tir (tracking-by-detection): tespit ağı her karede kutuları üretir, takipçi bu kutuları önceki izlere bağlar.

Tespit-ile-takip üç bileşenden oluşur. **İz durumu** (track state) her nesnenin o anki kestirimini taşır. **Tahmin** adımında her izin konumu bir hareket modeliyle bir sonraki kareye taşınır. **Veri ilişkilendirme** adımında bu tahminler yeni tespitlerle eşleştirilir. Eşleşen izler güncellenir, eşleşmeyen tespitler yeni iz açar, uzun süre eşleşmeyen izler silinir.

Hareket modeli olarak Bölüm 62.6'daki Kalman filtresini kullanıyoruz. Durum vektörü kutunun merkezini, boyutunu ve merkezin hızını taşır: x = [cx, cy, w, h, vx, vy]. Hızı filtre ölçümlerden kestirir; tahmin adımında merkez hızla ilerler: cx ← cx + vx. Ölçüm ise kutunun dört değeridir: z = [cx, cy, w, h]. Sabit hız modeli, nesnenin kısa sürede doğrusal hareket ettiği varsayımıdır; küçük bir süreç gürültüsü (Q) bu varsayımdaki sapmaları karşılar.

Aşağıdaki kod, bir izin durumunu, tahmin ve güncelleme adımlarını ve Kalman matrislerini tanımlar. R matrisi, sentetik videodaki ölçüm gürültüsünden (konum için σ = 1,5 piksel, boyut için σ = 1 piksel) biraz büyük seçilmiştir: köşegen değerleri 2,25 ve 1 çarpı 1,5 güvenlik payıdır.

```python
# b67_08_takip.py: tespit-ile-takip (tracking-by-detection).
# Sabit hiz Kalman (kutu durumu), veri iliskilendirme (acgozlu ve
# Macar), iz yasam dongusu, ByteTrack tarzi iki asamali eslestirme,
# MOTA ve kimlik degisimi (IDSW) olcumu. Sentetik videolar.
import os
import itertools
import numpy as np
from scipy.optimize import linear_sum_assignment
from b67_01_iou_nms import iou_matris, xyxy_to_xywh, xywh_to_xyxy
from b67_veri import video

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
F = np.eye(6)
F[0, 4] = F[1, 5] = 1.0          # cx += vx, cy += vy (dt = 1 kare)
H = np.zeros((4, 6))
H[0, 0] = H[1, 1] = H[2, 2] = H[3, 3] = 1.0
Q = np.diag([0.05, 0.05, 0.01, 0.01, 0.05, 0.05])
R = np.diag([2.25, 2.25, 1.0, 1.0]) * 1.5
```

```python
class Iz:
    """Tek bir iz: Kalman durumu, sayaclar ve kimlik."""

    def __init__(self, kimlik, kutu):
        cx, cy, w, h = xyxy_to_xywh(kutu[None])[0]
        self.id = kimlik
        self.x = np.array([cx, cy, w, h, 0.0, 0.0])
        self.P = np.diag([10.0, 10.0, 10.0, 10.0, 100.0, 100.0])
        self.hits = 1
        self.kacirma = 0          # son ardisik karede eslesmedi mi

    def tahmin(self):
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + Q

    def guncelle(self, kutu):
        cx, cy, w, h = xyxy_to_xywh(kutu[None])[0]
        z = np.array([cx, cy, w, h])
        y = z - H @ self.x                       # inovasyon
        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)      # Kalman kazanci
        self.x = self.x + K @ y
        self.P = (np.eye(6) - K @ H) @ self.P
        self.hits += 1
        self.kacirma = 0

    def kutu(self):
        return xywh_to_xyxy(self.x[None, :4])[0]
```

## 67.16 Veri ilişkilendirme: açgözlü mu, Macar mı?

Veri ilişkilendirme, her izi en fazla bir tespitle, her tespiti en fazla bir izle eşleştirmektir. Maliyet matrisi, her iz–tespit çifti için bir benzerlik (ör. IoU) ya da uzaklık (ör. merkezler arası mesafe) içerir. Açgözlü eşleştirme en yüksek benzerlikli çifti seçer, sonra o satırı ve sütunu siler, ve bu böyle devam eder. Bu yöntem hızlıdır ama her adımda yalnızca yerel en iyiyi seçer; toplam benzerliği en çoklu hale getirmeyi garanti etmez.

Bir örnekle bunu görelim: 2 × 2 bir benzerlik matrisi [[0,9; 0,8], [0,85; 0,1]] olsun. Açgözlü yöntem 0,9'u seçer (iz 1 – tespit 1), geriye yalnızca 0,1 kalır; toplam 1,0 olur. Oysa iz 1 – tespit 2 (0,8) ve iz 2 – tespit 1 (0,85) eşleşmesi toplamda 1,65 verir. **Macar algoritması** (Kuhn, 1955; genel bilgi), iki parçalı bir grafta toplam maliyeti en küçük (veya benzerliği en büyük) tam eşleştirmeyi polinom zamanda bulur. Bölüm 17'de iki parçalı graflar ve eşleştirme fikrini gördün; Macar algoritması bu fikrin ağırlıklı ve en iyi çözümünü verir.

Kodda Macar için SciPy'nin `linear_sum_assignment` fonksiyonunu kullanıyoruz; bu fonksiyon, maliyeti en küçük olan tam eşleştirmeyi döndürür. Geçersiz çiftleri (eşiğin altındaki IoU) büyük bir ceza ile dışlıyoruz. Açgözlü ve Macar eşleştirme aynı arayüzle yazılmıştır, böylece deneylerde yalnızca bu bileşeni değiştiririz.

```python
def acgozlu_eslestir(maliyet, esik_gecer):
    """Her adimda en yuksek skorlu cifti secer (benzerlik icin)."""
    cift, kul_t, kul_d = [], set(), set()
    pairs = sorted(
        [(maliyet[i, j], i, j) for i in range(maliyet.shape[0])
         for j in range(maliyet.shape[1]) if esik_gecer[i, j]],
        reverse=True)
    for s, i, j in pairs:
        if i in kul_t or j in kul_d:
            continue
        cift.append((i, j))
        kul_t.add(i)
        kul_d.add(j)
    return cift


def macar_eslestir(maliyet, esik_gecer):
    """Toplam maliyeti en az olan tam eslestirme
    (linear_sum_assignment). Gecersiz ciftler cezalandirilir."""
    buyuk = 1e6
    c = np.where(esik_gecer, -maliyet, buyuk)
    satir, sutun = linear_sum_assignment(c)
    return [(i, j) for i, j in zip(satir, sutun) if esik_gecer[i, j]]
```

Aşağıdaki kod, `Izleyici` sınıfını içerir. Bu sınıf beş farklı modu destekler: açgözlü IoU, Macar IoU (SORT'un yaklaşımı), Macar merkez mesafesi, tüm tespitlerle Macar IoU ve ByteTrack tarzı iki aşamalı eşleştirme. Yaşam döngüsü kuralları da burada yer alır: yeni bir iz, `min_hits` kare boyunca eşleşirse onaylanır; onaylanmamış bir iz bir kare bile kaçırırsa silinir; onaylanmış bir iz `max_age` kareye kadar tahminle yaşar (kısa örtülmelerde kimliği korumak için).

```python
class Izleyici:
    """mod:
       'acgozlu_iou' : yalnizca yuksek skorlu tespit, acgozlu IoU
       'macar_iou'   : yalnizca yuksek skorlu tespit, Macar IoU (SORT)
       'macar_mesafe': yalnizca yuksek skorlu tespit, Macar, merkez
       'macar_tum'   : tum tespitler (skor esigi yok), Macar IoU
       'byte'        : yuksek skor + ikinci asama, dusuk skorlu tespit
    """

    def __init__(self, mod, esik_yuksek=0.5, esik_dusuk=0.1,
                 iou_esik=0.3, mesafe_esik=20.0, min_hits=3,
                 max_age=10):
        self.mod = mod
        self.esik_yuksek = esik_yuksek
        self.esik_dusuk = esik_dusuk
        self.iou_esik = iou_esik
        self.mesafe_esik = mesafe_esik
        self.min_hits = min_hits
        self.max_age = max_age
        self.izler = []
        self.sayac = 0

    def _yeni(self, kutu):
        self.sayac += 1
        self.izler.append(Iz(self.sayac, kutu))
```

```python
    def _esle(self, izler, kutular, metrik, yontem):
        if len(izler) == 0 or len(kutular) == 0:
            return []
        tk = np.array([t.kutu() for t in izler])
        if metrik == "iou":
            iou = iou_matris(tk, kutular)
            gecer = iou >= self.iou_esik
            maliyet = iou
        else:
            ca = tk[:, :2] + (tk[:, 2:] - tk[:, :2]) / 2
            cd = kutular[:, :2] + \
                (kutular[:, 2:] - kutular[:, :2]) / 2
            d = np.linalg.norm(ca[:, None] - cd[None], axis=2)
            gecer = d <= self.mesafe_esik
            maliyet = -d
        if yontem == "acgozlu":
            return acgozlu_eslestir(maliyet, gecer)
        return macar_eslestir(maliyet, gecer)
```

```python
    def guncelle(self, kutular, skorlar):
        for t in self.izler:
            t.tahmin()
            t.kacirma += 1
        kutular = np.asarray(kutular, float).reshape(-1, 4)
        skorlar = np.asarray(skorlar, float)
        yuksek = np.where(skorlar >= self.esik_yuksek)[0]
        dusuk = np.where((skorlar >= self.esik_dusuk) &
                         (skorlar < self.esik_yuksek))[0]
        if self.mod == "macar_tum":
            asama1 = np.where(skorlar >= self.esik_dusuk)[0]
        else:
            asama1 = yuksek
        yontem = "acgozlu" if self.mod == "acgozlu_iou" else "macar"
        metrik = "mesafe" if self.mod == "macar_mesafe" else "iou"
        eslesen_iz = set()
        eslesen_det = set()
        cift = self._esle(self.izler, kutular[asama1], metrik, yontem)
        for i, j in cift:
            d = asama1[j]
            self.izler[i].guncelle(kutular[d])
            eslesen_iz.add(i)
            eslesen_det.add(d)
        if self.mod == "byte":
            kalan = [i for i in range(len(self.izler))
                     if i not in eslesen_iz]
            cift2 = self._esle([self.izler[i] for i in kalan],
                               kutular[dusuk], "iou", "macar")
            for a, j in cift2:
                i = kalan[a]
                d = dusuk[j]
                self.izler[i].guncelle(kutular[d])
                eslesen_iz.add(i)
        for j in asama1:
            if j not in eslesen_det:
                self._yeni(kutular[j])
        # onaylanmamis iz (hits < min_hits) bir kare bile kacirirsa
        # silinir; onaylanmis iz max_age kareye kadar yasar
        self.izler = [
            t for t in self.izler
            if (t.hits < self.min_hits and t.kacirma == 0)
            or (t.hits >= self.min_hits
                and t.kacirma <= self.max_age)]
        return [(t.id, t.kutu()) for t in self.izler
                if t.hits >= self.min_hits
                and t.kacirma <= self.max_age]
```

ByteTrack (Zhang ve diğerleri, 2022; genel bilgi) bir fikri öne sürer: düşük skorlu tespitler de yararlıdır; çünkü bir nesne kısmen örtüldüğünde ya da bulanıklaştığında detektör skorunu düşürür ama kutu hâlâ doğrudur. Bu yüzden önce yüksek skorlu tespitleri eşleştirir, sonra kalan izleri düşük skorlu tespitlerle eşleştirir. Bizim `byte` modumuz bu iki aşamayı uygular; düşük skorlu tespitlerin sentetik veride %20 oranında gerçek nesnelere ait olduğunu hatırla. Tüm bu yapılar sınıfın `guncelle` yönteminde birleşir.

Kodun geri kalanı, Macar algoritmasının doğruluğunu brute-force ile kontrol eden testi, açgözlü ile Macar'ın karşılaştırmasını, metrikleri ve 20 video üzerinde değerlendirme döngüsünü içerir.

## 67.17 Takip metrikleri: MOTA ve kimlik değişimi

Takip için standart metrik **MOTA** (Multiple Object Tracking Accuracy, CLEAR MOT ailesi; Bernardin ve Stiefelhagen, 2008; genel bilgi) şöyle tanımlanır:

MOTA = 1 − (FN + FP + IDSW) / GT

Burada FN kaçırılan gerçek nesne sayısı, FP yanlış izler, IDSW kimlik değişimi sayısı ve GT toplam gerçek nesne–kare sayısıdır. MOTA 1'e yaklaştıkça iyi, negatife düşebilir (çok sayıda hata olduğunda). Kimlik değişimi (ID switch), aynı gerçek nesnenin eşleştiği izin kimliğinin değişmesidir; takibin en yıkıcı hatalarından biridir, çünkü operatör iki nesnenin yerini karıştırır.

Aşağıdaki `mota` fonksiyonu, her karede gerçek kutular ile iz kutularını IoU ≥ 0,5 eşiğiyle Macar algoritmasıyla eşleştirir. Bir gerçek nesne için bir önceki karedeki eşleşen izle şimdiki eşleşen iz farklıysa bir IDSW sayılır. Sonra, sentetik videoların tamamı üzerinde yöntemler karşılaştırılır.

```python
def mota(cikti, kareler):
    """CLEAR MOT tarzi: IoU >= 0.5 ile kare basina Macar eslestirmesi.
    Donus: MOTA, FN, FP, IDSW ve eslesen GT -> iz kimligi kaydi."""
    fn = fp = idsw = toplam = 0
    son = {}
    kayit = []
    for (izler, kare) in zip(cikti, kareler):
        gk = np.array(kare["gt"], float).reshape(-1, 4)
        gid = kare["gt_id"]
        toplam += len(gk)
        if len(izler) == 0 or len(gk) == 0:
            fn += len(gk)
            fp += len(izler)
            kayit.append({})
            continue
        ik = np.array([b for _, b in izler])
        iid = [i for i, _ in izler]
        iou = iou_matris(gk, ik)
        gecer = iou >= 0.5
        c = np.where(gecer, -iou, 1e6)
        satir, sutun = linear_sum_assignment(c)
        eslesmis = {}
        for r, s in zip(satir, sutun):
            if gecer[r, s]:
                eslesmis[r] = iid[s]
        fn += len(gk) - len(eslesmis)
        fp += len(izler) - len(eslesmis)
        for r, tid in eslesmis.items():
            g = gid[r]
            if g in son and son[g] != tid:
                idsw += 1
            son[g] = tid
        kayit.append({gid[r]: t for r, t in eslesmis.items()})
    mota_d = 1 - (fn + fp + idsw) / max(toplam, 1)
    return mota_d, fn, fp, idsw, kayit
```

```python
def macar_kontrol(n_deneme=300):
    """Macar cozumu kaba kuvvet (permütasyon) ile ayni toplam maliyeti
    veriyor mu?"""
    rng = np.random.default_rng(5)
    uyusan = 0
    for _ in range(n_deneme):
        m = rng.uniform(0, 1, (4, 4))
        s, t = linear_sum_assignment(m)
        en_iyi = min(sum(m[i, p[i]] for i in range(4))
                     for p in itertools.permutations(range(4)))
        uyusan += int(abs(m[s, t].sum() - en_iyi) < 1e-12)
    print("Macar = kaba kuvvet (4x4, %d deneme): %d uyumlu"
          % (n_deneme, uyusan))
```

```python
def acgozlu_ornek():
    """Acgozlu eslestirmenin Macar'dan kotu oldugu bir durum."""
    # satir: iz, sutun: tespit
    m = np.array([[0.9, 0.8], [0.85, 0.1]])
    gecer = np.ones((2, 2), bool)
    print("acgozlu toplam =", round(sum(
        m[i, j] for i, j in acgozlu_eslestir(m, gecer)), 3),
        "| Macar toplam =", round(sum(
        m[i, j] for i, j in macar_eslestir(m, gecer)), 3))
```

```python
MODLAR = ["acgozlu_iou", "macar_iou", "macar_mesafe", "macar_tum",
          "byte"]
```

```python
def degerlendir(sayi=20):
    sonuc = {m: [] for m in MODLAR}
    for seed in range(100, 100 + sayi):
        kareler = video(seed)
        for mod in MODLAR:
            izci = Izleyici(mod)
            cikti = []
            for k in kareler:
                cikti.append(izci.guncelle(k["det"], k["skor"]))
            sonuc[mod].append(mota(cikti, kareler)[:4])
    return sonuc


if __name__ == "__main__":
    macar_kontrol()
    acgozlu_ornek()
    print("\n== Iz ilişkilendirme karşılaştırması (20 video) ==")
    sonuc = degerlendir(20)
    satirlar = ["yontem,mota_ort,mota_ss,idsw_ort,fn_ort,fp_ort"]
    for mod in MODLAR:
        a = np.array(sonuc[mod], float)
        print("%-13s MOTA=%.3f +- %.3f  IDSW=%.1f  FN=%.1f  FP=%.1f"
              % (mod, a[:, 0].mean(), a[:, 0].std(ddof=1),
                 a[:, 3].mean(), a[:, 1].mean(), a[:, 2].mean()))
        satirlar.append("%s,%.4f,%.4f,%.2f,%.2f,%.2f" % (
            mod, a[:, 0].mean(), a[:, 0].std(ddof=1),
            a[:, 3].mean(), a[:, 1].mean(), a[:, 2].mean()))
    with open(os.path.join(VERI, "b67_takip_karsilastirma.csv"),
              "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
```

Aşağıdaki çıktı 08 betiğinin tamamıdır. İlk iki satır Macar algoritmasının doğrulamasını ve açgözlü-Macar örneğini gösterir. Sonra 20 sentetik video (tohum 100-119, her biri 120 kare) üzerinde beş yöntemin MOTA, IDSW, FN ve FP ortalamaları verilir.

```term
$ python b67_08_takip.py
Macar = kaba kuvvet (4x4, 300 deneme): 300 uyumlu
acgozlu toplam = 1.0 | Macar toplam = 1.65

== Iz ilişkilendirme karşılaştırması (20 video) ==
acgozlu_iou   MOTA=0.920 +- 0.033  IDSW=2.3  FN=52.6  FP=15.3
macar_iou     MOTA=0.920 +- 0.034  IDSW=2.2  FN=52.5  FP=15.2
macar_mesafe  MOTA=0.926 +- 0.026  IDSW=1.9  FN=50.5  FP=12.6
macar_tum     MOTA=0.955 +- 0.016  IDSW=1.6  FN=27.6  FP=9.8
byte          MOTA=0.951 +- 0.020  IDSW=1.7  FN=32.9  FP=8.0
```

Sonuçlar ilk bakışta tutarlıdır: Macar eşleştirmesi, kaba kuvvetle 300 rastgele 4 × 4 matrisin 300'ünde de aynı toplam maliyeti verir; açgözlü örnekte 1,0, Macar'da 1,65 çıkar. Dört nokta dikkat çekicidir.

Birincisi, `macar_tum` (tüm tespitlerle Macar IoU) MOTA'da en yüksek değeri alır (0,955 ± 0,016) ve `byte` (0,951 ± 0,020) ona yakındır. Bu iki yöntemin ortak noktası düşük skorlu tespitleri kullanmalarıdır. Yüksek skorlu tespitlerle yetinen SORT benzeri `macar_iou` (0,920 ± 0,034) ve açgözlü `acgozlu_iou` (0,920 ± 0,033) bu kayıp yüzünden daha çok FN (kaçırma) üretir: 52,5'e karşı 27,6.

İkincisi, Macar eşleştirmesinin açgözlüye üstünlüğü bu veri setinde görünmedi (MOTA 0,920 ve 0,920). Açgözlü eşleştirme her adımda yerel en iyiyi seçer; sentetik sahnede çoğu zaman tek bir iz tek bir tespit için yarıştığı için iki yöntem aynı sonucu verdi. Kesişen çiftte de durum aynıdır: 67.18'de göreceğimiz gibi açgözlü ve Macar eşit sayıda (10) kimlik değişimi üretir. Bunun muhtemel nedeni, sabit hız tahmini sayesinde iki izin tahmin konumlarının kesişme anında bile ayrık kalmasıdır; bu açıklamayı ayrıca sınamadık, ama Macar'ın avantajının ancak ilişkilendirme belirsizliği daha büyük olduğunda görüleceğini söyleyebiliriz.

Üçüncüsü, merkez mesafesi ile eşleştirme (`macar_mesafe`) IoU'dan biraz daha iyi (MOTA 0,926) çıkar ve IDSW'yi düşürür (1,9 ve 2,2). Hareket eden küçük nesnelerde IoU, konum hatasına çok duyarlıdır; merkez mesafesi bu duyarlılığı azaltır.

Dördüncüsü, FP farkları beklenenden farklıdır: `macar_iou` 15,2 FP üretirken `macar_tum` 9,8 üretir. Bu farkın nedenini ayrıca incelemedik. Bir olasılık, düşük skorlu gerçek tespitlerin atılmasının kısa kesintilere ve yeni, onaylanmamış izlerin doğmasına yol açmasıdır; ama bu açıklamayı sınamadık.

Son olarak bir uyarı: bu sonuçlar sentetik senaryonun parametrelerine bağlıdır (örneğin düşük skorlu gerçek tespitlerin oranı %20 seçilmiştir, kesişen yörüngeler tasarlanmıştır). Bu karşılaştırmadan "ByteTrack her zaman en iyidir" sonucunu çıkarma; gerçek bir İHA videosunda sonuç farklı olabilir.

## 67.18 Kesişen yörüngeler: kimlik değişimi neden olur?

Kimlik değişimini en iyi, iki nesnenin birbirinin yanından geçtiği anlarda görürsün. Sentetik her videonun ilk iki nesnesi, 200 piksellik sahnede zıt yönlerde yatay olarak hareket eder; başlangıçta dikeyde yalnızca 4 piksel ayrıdırlar ve yaklaşık 40. karede x konumları çakışır (o anda dikey ayrım yaklaşık 16 piksel). Aşağıdaki kod, bu çiftin kimlik değişimini yöntemler arasında karşılaştırır: 20 videoda her gerçek nesne için IDSW sayılır, ve tohum 107 videosunda gerçek ile atanan kimlik zaman içinde çizilir.

```python
# b67_08b_kesisim.py: kesisen cift (GT 0 ve GT 1) icin kimlik
# degisimi (IDSW). (a) 20 videoda GT basina IDSW toplami,
# (b) tohum 107'de GT 0 ve 1'in atanan kimlikleri (sekil icin).
import os
import numpy as np
from scipy.optimize import linear_sum_assignment
from b67_veri import video
from b67_01_iou_nms import iou_matris
from b67_08_takip import Izleyici, MODLAR, VERI, mota
```

```python
def idsw_gt(cikti, kareler):
    """GT kimligi -> IDSW sayisi (CLEAR MOT ile ayni kural)."""
    son, sayim = {}, {}
    for izler, kare in zip(cikti, kareler):
        gk = np.array(kare["gt"], float).reshape(-1, 4)
        gid = kare["gt_id"]
        if not izler or len(gk) == 0:
            continue
        ik = np.array([b for _, b in izler])
        iid = [i for i, _ in izler]
        iou = iou_matris(gk, ik)
        gecer = iou >= 0.5
        r, s = linear_sum_assignment(np.where(gecer, -iou, 1e6))
        for a, b in zip(r, s):
            if gecer[a, b]:
                k = gid[a]
                if k in son and son[k] != iid[b]:
                    sayim[k] = sayim.get(k, 0) + 1
                son[k] = iid[b]
    return sayim
```

```python
if __name__ == "__main__":
    toplam = {m: [0, 0, 0] for m in MODLAR}
    for seed in range(100, 120):
        kareler = video(seed)
        for m in MODLAR:
            izci = Izleyici(m)
            cikti = [izci.guncelle(k["det"], k["skor"])
                     for k in kareler]
            s = idsw_gt(cikti, kareler)
            toplam[m][0] += s.get(0, 0)
            toplam[m][1] += s.get(1, 0)
            toplam[m][2] += sum(v for k, v in s.items()
                                if k not in (0, 1))
    print("20 video: kesisen cift (GT 0, 1) ve diger IDSW toplami:")
    satirlar = ["yontem,gt0_idsw,gt1_idsw,diger_idsw"]
    for m in MODLAR:
        g0, g1, d = toplam[m]
        print("%-13s GT0=%2d  GT1=%2d  diger=%2d" % (m, g0, g1, d))
        satirlar.append("%s,%d,%d,%d" % (m, g0, g1, d))
    with open(os.path.join(VERI, "b67_kesisim_ozet.csv"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")

    # Sekil icin: tohum 107, GT 0 ve 1'in atanan iz kimlikleri
    kareler = video(107)
    satirlar = ["yontem,kare,gt_id,cx,cy,iz_id"]
    for m in MODLAR:
        izci = Izleyici(m)
        cikti = [izci.guncelle(k["det"], k["skor"]) for k in kareler]
        _, _, _, _, kayit = mota(cikti, kareler)
        for t, kare in enumerate(kareler):
            for g in (0, 1):
                if g in kare["gt_id"]:
                    k = kare["gt_id"].index(g)
                    b = kare["gt"][k]
                    cx = (b[0] + b[2]) / 2
                    cy = (b[1] + b[3]) / 2
                    satirlar.append("%s,%d,%d,%.1f,%.1f,%d" % (
                        m, t, g, cx, cy, kayit[t].get(g, -1)))
    with open(os.path.join(VERI, "b67_kesisim.csv"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
    print("kaydedildi: b67_kesisim_ozet.csv, b67_kesisim.csv")
```

```term
$ python b67_08b_kesisim.py
20 video: kesisen cift (GT 0, 1) ve diger IDSW toplami:
acgozlu_iou   GT0= 6  GT1= 4  diger=36
macar_iou     GT0= 6  GT1= 4  diger=34
macar_mesafe  GT0= 5  GT1= 6  diger=28
macar_tum     GT0= 3  GT1= 2  diger=26
byte          GT0= 4  GT1= 1  diger=29
kaydedildi: b67_kesisim_ozet.csv, b67_kesisim.csv
```

Çıktı, 20 videoda kesişen çiftin (GT 0 ve GT 1) IDSW toplamını verir: açgözlü IoU'da 6 + 4 = 10, Macar IoU'da 6 + 4 = 10, Macar mesafesinde 5 + 6 = 11, tüm tespitlerle Macar'da 3 + 2 = 5, ByteTrack tarzında 4 + 1 = 5. Diğer nesnelerdeki IDSW sayıları (26-36) bu çiftten daha yüksektir; yani kesişme, kimlik değişiminin tek kaynağı değildir ama en tipik kaynağıdır. Düşük skorlu tespitleri de kullanan iki yöntem (tüm tespitlerle Macar ve ByteTrack tarzı), kesişme sırasında daha fazla bilgiyle iki izi ayırt eder ve kimlik değişimini yaklaşık yarıya indirir.

Şekil 67.9 tohum 107 videosunda dört yöntemin davranışını gösterir. Macar IoU (b) GT 0'ın kimliğini kısa süre 8'e, sonra yeniden 5'e çevirir; bu iki IDSW demektir. ByteTrack tarzı (d) kimliği 3'e geçirip geri döndürür. Macar tüm tespitlerle (c) ise hiç kimlik değişimi yaşamaz.

![Şekil 67.9: Kesişen yörüngeler (a) ve dört yöntemde atanan kimlikler: (b) Macar IoU, (c) Macar tüm tespitlerle, (d) ByteTrack tarzı](gorseller/b67_takip_kesisim.png)

Bu sonuç, takip hatalarının kaynağını doğru yerde aramayı öğretir: kimlik değişimi çoğunlukla nesneler birbirine yaklaştığında ve tek bir tespit ile iki iz birbirine benzediğinde olur. Yöntem değişikliği etkilidir, ama ilişkilendirme maliyeti, hareket modeli ve tespit kalitesi birlikte düşünülmelidir. Bölüm 78'de bu tür belirsizlikleri nasıl ölçeceğimizi göreceğiz.

## 67.19 Gerçek zamanlı ve gömülü: kare bütçesi

Bir tespit ve takip hattı, kamera her kare üretirken yetişmek zorundadır. 30 kare/saniye (FPS) hedefi, her kare için 1000 / 30 = 33,3 milisaniyelik bir **bütçe** demektir. Bu bütçe kameradan görüntünün alınmasını, ön işlemeyi, ağ ileri geçişini, son işlemeyi (NMS dahil), takipçiyi ve sonucun iletilmesini kapsar. Bütçenin herhangi bir aşaması aşılırsa sistem kare atlar ya da gecikme biriktirir; bir İHA'da bu gecikme, operatörün gördüğü ile gerçeğin arasında bir fark demektir.

Gecikme ölçümü, ağın kendisinden daha fazlasını kapsar. Bu bölümde ölçülen bileşenler şunlardır: (1) dedektörün GPU'da ileri geçişi (fp32 ve fp16, girdi boyutu 96, 192 ve 384 piksel), (2) 96 piksel girdi için son işleme (karar eşiği ve NMS), (3) CPU'da macar_tum takipçisinin kare başına süresi. Girdi boyutu 192 ve 384 için yalnızca hız ölçüldü; bu boyutlar için ağı yeniden eğitmedik, dolayısıyla bu boyutlardaki doğruluğu bilmiyoruz. Bu, çözünürlük–doğruluk–hız üçlüsünün tamamını ölçmediğimiz anlamına gelir: bu bölüm çözünürlük ile hızı karşılaştırır, ama doğruluğu yalnızca 96 piksel için raporlar.

Ölçüm için iki koşul önemlidir. Birincisi, GPU ölçümden önce boşta olmalıdır: ölçüm öncesinde kart kullanımı %0 ve bellek 0 MiB olarak kaydedildi. İkincisi, ölçüm her seferinde CUDA senkronizasyonu ile yapılmalıdır, yoksa GPU'nun asenkron çalışması süreyi olduğundan kısa gösterir. Ölçüm sonrasında `nvidia-smi` çıktısındaki %20 kullanım ve 149 MiB bellek, betiğin kendi CUDA bağlamından gelir; bu değer ölçümün bir parçası değildir. Aşağıdaki kod ağın ileri geçiş süresini, son işlemeyi ve takipçi süresini ölçer.

```python
# b67_09_gecikme.py: gecikme olcumu. GPU'da dedektor (ag ileri gecis
# ve son isleme), CPU'da takipci. Girdi boyutu ve karisik hassasiyet
# (fp16) karsilastirilir. Olcumden once GPU'nun bos oldugu dogrulanir.
import os
import subprocess
import time
import numpy as np
import torch
from b67_04_yolo_mini import MiniYolo, decode, AYGIT, VERI, KLASOR
from b67_veri import video, veri_seti
from b67_08_takip import Izleyici

N_OLCUM, N_ISINMA = 200, 30
```

```python
def gpu_durumu():
    return subprocess.run(
        ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used",
         "--format=csv,noheader"],
        capture_output=True, text=True).stdout.strip()


def ag_suresi(model, boyut, fp16=False):
    """Yalnizca ag ileri gecisi; her olcum CUDA senkronizasyonlu."""
    x = torch.rand(1, 1, boyut, boyut, device=AYGIT)
    sure = []
    with torch.no_grad(), torch.autocast("cuda", torch.float16,
                                         enabled=fp16):
        for _ in range(N_ISINMA):
            model(x)
        torch.cuda.synchronize()
        for _ in range(N_OLCUM):
            t0 = time.perf_counter()
            model(x)
            torch.cuda.synchronize()
            sure.append(time.perf_counter() - t0)
    sure = np.array(sure) * 1e3
    return float(np.median(sure)), float(np.percentile(sure, 90))
```

```python
def son_isleme_suresi(model, X):
    """Gercek 96 px sahnelerde karar + NMS suresi (CPU), ms."""
    with torch.no_grad():
        ham = model(torch.tensor(X[:1], device=AYGIT)).cpu().numpy()
    sure = []
    for _ in range(N_OLCUM):
        t0 = time.perf_counter()
        decode(ham)
        sure.append(time.perf_counter() - t0)
    return float(np.median(np.array(sure) * 1e3))
```

```python
def takipci_suresi():
    """macar_tum takipcisi, kare basina CPU suresi (ms)."""
    kareler = video(seed=100)
    izci = Izleyici("macar_tum")
    t0 = time.perf_counter()
    for k in kareler:
        izci.guncelle(k["det"], k["skor"])
    return (time.perf_counter() - t0) * 1e3 / len(kareler)
```

```python
if __name__ == "__main__":
    print("GPU durumu (olcum oncesi):", gpu_durumu())
    model = MiniYolo().to(AYGIT)
    # yalnizca tensor sozlugu yukleniyor (weights_only=True)
    model.load_state_dict(torch.load(
        os.path.join(KLASOR, "yolo_t1.pt"), map_location=AYGIT,
        weights_only=True))
    model.eval()
    X, _, _ = veri_seti(8, seed=777)
    print("GPU adi:", torch.cuda.get_device_name(0))
    satirlar = ["boyut,hassasiyet,ag_medyan_ms,ag_p90_ms,fps"]
    for boyut in (96, 192, 384):
        for fp16 in (False, True):
            med, p90 = ag_suresi(model, boyut, fp16)
            ad = "fp16" if fp16 else "fp32"
            print("%3d px  %s  ag medyan=%.2f ms  p90=%.2f ms  "
                  "(~%.0f FPS)" % (boyut, ad, med, p90, 1000 / med))
            satirlar.append("%d,%s,%.3f,%.3f,%.1f"
                            % (boyut, ad, med, p90, 1000 / med))
    son = son_isleme_suresi(model, X)
    tak = takipci_suresi()
    print("son isleme (96 px, NMS dahil) medyan = %.3f ms" % son)
    print("takipci (macar_tum, CPU) kare basina = %.3f ms" % tak)
    print("GPU durumu (olcum sonrasi):", gpu_durumu())
    with open(os.path.join(VERI, "b67_gecikme.csv"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
        f.write("# son_isleme_ms=%.3f, takipci_ms=%.3f\n"
                % (son, tak))
```

Aşağıdaki çıktı 09 betiğinin tamamıdır. Her ağ satırı 200 ölçümün medyanını ve 90. yüzdeliği verir; FPS değeri 1000 bölü medyan olarak hesaplanmıştır.

```term
$ python b67_09_gecikme.py
GPU durumu (olcum oncesi): 0 %, 0 MiB
GPU adi: NVIDIA GeForce RTX 3060 Laptop GPU
 96 px  fp32  ag medyan=0.65 ms  p90=0.69 ms  (~1534 FPS)
 96 px  fp16  ag medyan=0.71 ms  p90=0.84 ms  (~1402 FPS)
192 px  fp32  ag medyan=0.64 ms  p90=0.70 ms  (~1571 FPS)
192 px  fp16  ag medyan=0.72 ms  p90=0.76 ms  (~1393 FPS)
384 px  fp32  ag medyan=0.60 ms  p90=0.64 ms  (~1653 FPS)
384 px  fp16  ag medyan=0.72 ms  p90=0.76 ms  (~1393 FPS)
son isleme (96 px, NMS dahil) medyan = 0.397 ms
takipci (macar_tum, CPU) kare basina = 0.571 ms
GPU durumu (olcum sonrasi): 20 %, 149 MiB
```

Sonuçlar beklenmedik bir şey gösterir: bu küçük ağın ileri geçişi, girdi boyutu 96'dan 384'e çıktığında neredeyse değişmez (fp32 için 0,65'ten 0,60 milisaniyeye). Bunun nedeni, ağın hesap yükünün, çekirdek başlatma ve Python çağrı yükünün altında kalmasıdır; yani GPU bu boyutlarda gerçek bir darboğaz değildir. Benzer biçimde fp16 de bu ağda hızlandırma sağlamadı (0,71 ve 0,72 milisaniye): küçük konvolüsyonlar ve BatchNorm, yarı hassasiyetin avantajını kullanacak kadar büyük değildir. Bu, "çözünürlüğü düşürmek her zaman hızlandırır" ya da "yarı hassasiyet her zaman daha hızlıdır" gibi genellemelerin doğru olmadığını gösterir; hız, modelin büyüklüğü ve donanımın birlikte belirler.

Kare bütçesi açısından bakıldığında tablo daha net: 96 piksel dedektör ileri geçişi 0,65 milisaniye, son işleme 0,40 milisaniye, CPU'daki takipçi 0,57 milisaniye sürüyor. Toplam yaklaşık 1,6 milisaniye, 33,3 milisaniyelik bütçenin yaklaşık yirmide biridir. Bu sayılar sentetik ve küçük bir ağ içindir; gerçek bir İHA dedektörü (daha büyük bir girdi, daha derin bir ağ, gerçek sahnelerde çok daha fazla tespit) bu bütçeyi kolayca aşabilir. Bölüm 75'te (verimli çıkarım) bu bütçeyi nasıl tuttuğumuzu, Bölüm 46'daki gömülü çıkarım kısıtlarıyla birlikte göreceğiz.

Şekil 67.10, ağ gecikmesinin girdi boyutuna göre neredeyse düz olduğunu ve kare bütçesinin aşamalarını gösterir.

![Şekil 67.10: Solda girdi boyutuna göre ağ gecikmesi (fp32 ve fp16), sağda kare başına aşama süreleri](gorseller/b67_cozunurluk_fps.png)

::: dikkat
Bu gecikme ölçümü bir masaüstü GPU'da (RTX 3060 Laptop) yapıldı. Bir İHA'nın gömülü işlemcisinde (Jetson gibi) veya bir mikrodenetleyicide sonuçlar çok farklı olur; o platformlar için ayrı ölçüm gerekir. Bölüm 46'da mikrodenetleyici sınırlarını görmüştük.
:::

## 67.20 Savunma bağlamı: neyi ölçmeli, neyi sormamalı

Savunma sanayiinde bu tekniklerin kullanıldığı yerler gözetleme, durumsal farkındalık ve sensör füzyonudur. Bir İHA'nın kamerasından gelen görüntüde küçük ve uzak hedefler, kötü ışık ve yağmur, sahte alarmlar (kuş, gölge, yansıma) ve hedef gizlenmesi sık karşılaşılan sorunlardır. Bu bölümdeki ölçümler, bu sorunların her birinin nasıl bir hata olarak ortaya çıktığını göstermeyi amaçladı: küçük nesneler kaçırılır, sahte alarmlar (FP) mAP'i düşürür, kimlik değişimleri (IDSW) operatörün yanılmasına yol açar.

Üç ilke öne çıkar. Birincisi, **yanlış alarmın maliyeti asimetriktir.** Gözetlemede bir kaçırılan hedef ile bir sahte alarm aynı ağırlıkta değildir; eşik seçimi bu maliyet dengesine göre yapılmalıdır ve bu, mAP gibi tek bir sayıyla yapılamaz. Bölüm 57'deki maliyet temelli eşik seçimi bu noktada bir araçtır. İkincisi, **tespit tek başına karar değildir.** Bir tespit, sensör füzyonu (Bölüm 62.9) ile birleştirilmeli ve insan operatörün kararına sunulmalıdır; otomatik karar ile insan-döngüde karar arasındaki çizgi, güvenilirlik ve sorumluluk meseleleridir (Bölüm 78). Üçüncüsü, **ölçüm koşulu raporun parçasıdır.** Bu bölümün her sayısı sentetik veriye, belirli bir tohuma ve belirli bir donanıma aittir; bir sistemin gerçek performansı, kendi veri setinde ve kendi donanımında ölçülmelidir.

Bu bölümün kapsamı, algılama, takip ve durumsal farkındalık ile sınırlıdır. Hedef seçimi, silahlandırma ya da angajman kararlarıyla ilgili yöntemleri bu kitapta anlatmıyoruz; bu tür kararlar, teknik bir ölçüt değil, hukuki ve etik bir çerçeve gerektirir.

## Çözümlü Örnekler

Aşağıdaki dört örnek artan zorlukta. Her birinde önce sayıları elle, sonra kodla kontrol ediyoruz. Kodla kontrol edilen değerler bu bölümdeki betiklerle birebir aynıdır.

### Örnek 1 (★): İki kutunun IoU'su ve GIoU'su

**Adım 1 — Anla.** Köşe biçiminde iki kutu var: A = (0, 0, 20, 10) ve B = (5, 4, 25, 14). İstenen, IoU ve GIoU. Hangi bilgilere ihtiyaç var? Kesişim, birleşim ve iki kutuyu kapsayan kutunun alanı.

**Adım 2 — Örnekle.** A genişliği 20, yüksekliği 10 olan bir kutudur; alanı 200. B de 20 × 10 boyutunda ama 5 piksel sağda ve 4 piksel aşağıda. İkisi kısmen örtüşüyor; örtüşme bir dikdörtgendir.

**Adım 3 — Kaba çöz.** Kesişimin sınırları, iki kutunun sol ve üst kenarlarının büyüğü, sağ ve alt kenarlarının küçüğüdür: x1 = max(0, 5) = 5, y1 = max(0, 4) = 4, x2 = min(20, 25) = 20, y2 = min(10, 14) = 10. Kesişim genişliği 15, yüksekliği 6, alanı 90. Birleşim 200 + 200 − 90 = 310. IoU = 90 / 310 ≈ 0,2903.

**Adım 4 — Örüntü.** Kesişim formülünde iki kutu hiç örtüşmüyorsa genişlik ya da yükseklik negatif çıkar; bunu 0'a kırpmak gerekir. Bu yüzden kesişim her zaman `max(0, ...)` ile hesaplanır. GIoU için kapsayan kutu, iki kutunun en küçük ve en büyük koordinatlarından oluşur.

**Adım 5 — İyileştir.** Kapsayan kutu C: x1 = min(0, 5) = 0, y1 = min(0, 4) = 0, x2 = max(20, 25) = 25, y2 = max(10, 14) = 14; alanı 25 × 14 = 350. GIoU = IoU − (C − birleşim) / C = 0,2903 − (350 − 310) / 350 = 0,2903 − 0,1143 = 0,1760.

**Adım 6 — Doğrula.** Aşağıdaki tablo ara değerleri gösterir:

| Adım | Değer | Hesap |
|---|---|---|
| Kesişim sınırları | (5, 4, 20, 10) | sol/üst büyük, sağ/alt küçük |
| Kesişim alanı | 90 | 15 × 6 |
| Birleşim | 310 | 200 + 200 − 90 |
| IoU | 0,2903 | 90 / 310 |
| Kapsayan kutu C | 350 | 25 × 14 |
| GIoU | 0,1760 | 0,2903 − 40 / 350 |

Kodla kontrol: `iou_matris` ve `giou_matris` fonksiyonları bu iki kutu için 0,2903 ve 0,1760 döndürür (b67_01 betiğinin ilk bloğunu aynı kutularla çağırmak yeterlidir).

**Bunu AI'sız yazabilir misin?** İki kutu için IoU'yu tek bir fonksiyon olarak yaz. Kesişim negatif olduğunda ve birleşim sıfır olduğunda ne döndürdüğünü açıkla.

### Örnek 2 (★★): Beş kutuda NMS'i elle izlemek

**Adım 1 — Anla.** Altı kutu yerine bu örnekte beş kutu var: P, Q, R, S, T, U. Her birinin bir skoru var. Eşik 0,5. İstenen: hangi kutular tutulur, hangileri bastırılır ve sebebi.

**Adım 2 — Örnekle.** Önce skora göre sırala: Q (0,95), S (0,90), P (0,80), R (0,70), T (0,60), U (0,55). Kutular: P = (0, 0, 10, 10), Q = (1, 1, 11, 11), R = (20, 0, 30, 10), S = (21, 1, 31, 11), T = (0, 20, 6, 26), U = (3, 3, 13, 13). Hangi çiftler örtüşüyor? Yalnızca P–Q, R–S, Q–U ve P–U çiftleri kesişir; T hiçbiriyle örtüşmez.

**Adım 3 — Kaba çöz.** Sırayla ilerle, her kutuyu o ana kadar tutulan kutularla karşılaştır:

| Sıra | Kutu | Skor | Karar | Neden |
|---|---|---|---|---|
| 1 | Q | 0,95 | tut | ilk kutu |
| 2 | S | 0,90 | tut | Q ile IoU = 0 |
| 3 | P | 0,80 | sil | IoU(P, Q) = 0,6807 > 0,5 |
| 4 | R | 0,70 | sil | IoU(R, S) = 0,6807 > 0,5 |
| 5 | T | 0,60 | tut | hiçbiriyle örtüşmüyor |
| 6 | U | 0,55 | tut | IoU(U, Q) = 0,4706 ≤ 0,5 |

**Adım 4 — Örüntü.** Bastırma yalnızca tutulan kutularla yapılır. P ve R silindiği için artık hiçbir karşılaştırmada rol oynamazlar; bu yüzden U ile P'nin IoU'su (0,3245) hiçbir şeyi değiştirmez. Bastırılmış bir kutu, başka bir kutuyu bastıramaz.

**Adım 5 — İyileştir.** Eşik 0,3 olsaydı ne olurdu? U ile Q'nun IoU'su 0,4706 > 0,3 olacağından U silinirdi; sonuç Q, S, T olurdu. Eşik seçimi, iki yakın ama farklı nesnenin ayrı tutulup tutulmayacağını belirler. Bu yüzden eşiği bir doğrulama kümesinde ayarlamak gerekir.

**Adım 6 — Doğrula.** Tutulan kutuların indisleri (0 tabanlı) [1, 3, 4, 5] olmalı; bu Q, S, T, U'ya karşılık gelir:

| Kutu | Skor | Durum |
|---|---|---|
| Q | 0,95 | tutuldu |
| S | 0,90 | tutuldu |
| T | 0,60 | tutuldu |
| U | 0,55 | tutuldu |
| P, R | 0,80; 0,70 | bastırıldı |
 Kod `nms(K, S, 0.5)` çağrısı ile tam bu sonucu verir. Aynı kutularla torchvision'ın `nms` fonksiyonunu da çağırıp sonucu karşılaştırabilirsin.

**Bunu AI'sız yazabilir misin?** Yukarıdaki sırayla NMS'i bir döngü olarak yaz. Bastırılmış bir kutunun sonraki karşılaştırmalarda neden kullanılmadığını kodunla göster.

### Örnek 3 (★★): Beş tahminde PR ve AP'nin elle hesabı

**Adım 1 — Anla.** Tek bir sınıf için altı tahmin var, gerçek kutu sayısı 5. Skorlar 0,9; 0,8; 0,7; 0,6; 0,5; 0,4 ve TP bayrakları 1, 0, 1, 1, 0, 1. İstenen: PR noktaları, tüm noktalar AP'si ve 11 nokta AP'si.

**Adım 2 — Örnekle.** Skor sırası zaten azalan. Her tahminden sonra kümülatif TP ve FP sayılarını tut; her noktada precision = TP / (TP + FP), recall = TP / 5.

**Adım 3 — Kaba çöz.**

| Sıra | Skor | TP | Kümülatif TP | Kümülatif FP | Precision | Recall |
|---|---|---|---|---|---|---|
| 1 | 0,9 | 1 | 1 | 0 | 1,0000 | 0,2 |
| 2 | 0,8 | 0 | 1 | 1 | 0,5000 | 0,2 |
| 3 | 0,7 | 1 | 2 | 1 | 0,6667 | 0,4 |
| 4 | 0,6 | 1 | 3 | 1 | 0,7500 | 0,6 |
| 5 | 0,5 | 0 | 3 | 2 | 0,6000 | 0,6 |
| 6 | 0,4 | 1 | 4 | 2 | 0,6667 | 0,8 |

**Adım 4 — Örüntü.** Precision eğrisi zigzag yapıyor. Zarf, her noktada kendinden sonraki en büyük precision'a eşitlenir: k = 6'da 0,6667; k = 5'te max(0,6; 0,6667) = 0,6667; k = 4'te 0,75; k = 3'te 0,75; k = 2'de 0,75; k = 1'de 1,0.

**Adım 5 — İyileştir.** Tüm noktalar AP'si, zarf değerini recall artışıyla çarpıp toplamaktır: 0,2 · 1,0 + 0 · 0,75 + 0,2 · 0,75 + 0,2 · 0,75 + 0 · 0,6667 + 0,2 · 0,6667 = 0,2 + 0,15 + 0,15 + 0,1333 = 0,6333. 11 nokta AP'si için recall 0, 0,1, ..., 1 noktalarında zarfın değerini alıp ortalarız: 0 ile 0,2 arası için 1,0 (üç nokta), 0,3 ile 0,6 arası için 0,75 (dört nokta), 0,7 ve 0,8 için 0,6667 (iki nokta), 0,9 ve 1,0 için 0 (iki nokta). Toplam 7,3333 / 11 = 0,6667.

**Adım 6 — Doğrula.**

| Ölçüt | Elle | Kod (düzeltilmiş) |
|---|---|---|
| Tüm noktalar AP | 0,6333 | 0,6333 |
| 11 nokta AP | 0,6667 | 0,6667 |

Kod, tüm noktalar AP'si için 0,6333 ve 11 nokta AP'si için 0,6667 üretir. Burada yaşanan bir hatayı da açıkça anlatmak istiyoruz. Kodun ilk sürümü 11 nokta değerini 0,6591 olarak veriyordu. Nedeni şuydu: recall 0,6 tam olarak 3/5'tir, ama `np.linspace(0, 1, 11)` içindeki 0,6 değeri kayan nokta gösteriminde 0,6000000000000001 çıkar. Karşılaştırma `r >= 0.6000000000000001` olduğunda tam eşitlikteki nokta dışlanır ve o recall seviyesinde zarf 0,75 yerine 0,6667 alınır. Düzeltme, karşılaştırmaya 10⁻⁹ toleransı eklemekti. Bu hata, eşitlik karşılaştırmalarının kayan noktada ne kadar kırılgan olduğunu gösterir; değerlendirme kodunda eşitlik sınırlarını her zaman toleranslı yaz.

**Bunu AI'sız yazabilir misin?** Beşinci tahmin TP olsaydı (skor 0,5 için TP = 1), tüm noktalar AP'sinin nasıl değişeceğini elle hesapla. Sonra değeri kodla doğrula.

### Örnek 4 (★★★): 3 × 3 eşleştirme, açgözlü ile Macar ve bir Kalman güncellemesi

**Adım 1 — Anla.** Üç iz (T1, T2, T3) ve üç tespit (D1, D2, D3) var. Benzerlik IoU ile ölçülüyor. Bir kapı (gating) eşiği 0,3: bu eşiğin altındaki çiftler hiç eşleştirilmez. İstenen: açgözlü ve Macar eşleştirmelerinin toplam benzerliği, eşleşen çift sayısı ve eşleşen izlerden birinin Kalman güncellemesi.

**Adım 2 — Örnekle.** Benzerlik matrisi (satır: iz, sütun: tespit):

| | D1 | D2 | D3 |
|---|---|---|---|
| T1 | 0,90 | 0,80 | 0,00 |
| T2 | 0,85 | 0,10 | 0,00 |
| T3 | 0,00 | 0,00 | 0,70 |

**Adım 3 — Kaba çöz.** Açgözlü: en yüksek çifti al. 0,90 (T1–D1) alınır. Sonra 0,85 (T2–D1) D1 kullanıldığı için reddedilir; 0,80 (T1–D2) T1 kullanıldığı için reddedilir. 0,70 (T3–D3) alınır. Kalan 0,10 (T2–D2) kapının altında olduğu için alınmaz. Açgözlü sonuç: 2 eşleşme, toplam 1,60.

Macar: 3 izin 3 tespite tüm olası eşleşmelerine bakıyoruz. T1–D2, T2–D1, T3–D3 çiftleri üçü de kapının üstündedir ve toplam 0,80 + 0,85 + 0,70 = 2,35 eder. Bu, geçerli eşleşmeler arasındaki en büyük toplamdır.

**Adım 4 — Örüntü.** Açgözlü yöntem her adımda en büyük tek değeri seçer ve bu, T1'i D1'e bağlayarak T2'nin D1'i kullanma şansını yok eder. Yerel en iyi seçim (0,90), global en iyi çözüm (2,35) ile çelişir. Macar algoritması bu çelişkiyi bütün eşleşmeleri birlikte değerlendirerek çözer.

**Adım 5 — İyileştir.** Macar sonucu T1–D2 çiftini verdiğinden, T1'in durumunu bu tespitle güncelleyelim. Basitlik için tek boyutlu bir Kalman adımı: önsel x⁻ = 10, P⁻ = 4; ölçüm z = 12, R = 4. Kazanç K = P⁻ / (P⁻ + R) = 4 / 8 = 0,5. Güncelleme x = x⁻ + K (z − x⁻) = 10 + 0,5 · 2 = 11 ve P = (1 − K) P⁻ = 0,5 · 4 = 2. Ölçüme yarı yarıya güvendik ve belirsizliğimiz 4'ten 2'ye düştü.

**Adım 6 — Doğrula.** Sonuçları tabloda topluyoruz:

| Yöntem | Eşleşmeler | Eşleşen çift sayısı | Toplam benzerlik |
|---|---|---|---|
| Açgözlü + kapı | T1–D1, T3–D3 | 2 | 1,60 |
| Macar + kapı | T1–D2, T2–D1, T3–D3 | 3 | 2,35 |

Kodla kontrol: SciPy'nin `linear_sum_assignment` fonksiyonuna (negatif benzerlikle, çünkü fonksiyon minimum maliyet arar) bu matrisi verdiğimizde T1–D2, T2–D1, T3–D3 çiftlerini ve toplam 2,35'i döndürür. Kalman sonucu elle yapılan hesapla aynıdır.

**Bunu AI'sız yazabilir misin?** 3 × 3 matris için altı permütasyonun tamamını deneyerek en büyük toplamı bul; sonra açgözlü ile arasındaki farkın neden yalnızca belirli matrislerde ortaya çıktığını açıkla.

## Kendin Yap Projeleri

::: dikkat
Aşağıdaki projelerde bir yapay zekâ aracından kod üretmeden önce kendi çözümünü yaz. Bu bölümdeki betikler size bir başlangıç verir; ama projenin amacı, tespit, takip ve segmentasyonun her bileşenini kendi elinle kurup ölçmektir. Kodun bir kısmını aldığında, sonucu bu bölümün ölçümleriyle karşılaştır.
:::

### Proje 1 (★★): Sentetik İHA gözetleme hattı

**Amaç.** Bu bölümdeki sentetik veri üreticisi, tek aşamalı dedektör ve takipçi bileşenlerini birleştirerek kare kare çalışan bir gözetleme hattı kur. Hat her karede tespit yapar, tespitleri takipçiye verir ve kimlikli izleri çıktı olarak üretir.

**Beklenen davranış.** Hattın giriş olarak bir video dizisi (kare listesi) alması, her karede ekranda izlenen kimlikli kutuları üretmesi ve sonunda bir rapor çıkarması gerekir. Rapor mAP@0,5 (test kümesinde), MOTA, IDSW sayısı ve kare başına ortalama süreyi içermelidir.

**Önerilen yaklaşım (ipucu).** Tespit kısmında 04 betiğindeki `MiniYolo` ve `decode` fonksiyonlarını yeniden kullanabilirsin; takip kısmında 08 betiğindeki `Izleyici` sınıfını ve `mota` fonksiyonunu. Önce tek bir videoda hatı çalıştır, sonra 20 videoyu topla. Gecikme ölçümünü yapmadan önce GPU'nun boşta olduğunu kontrol et.

**Başarı kriterleri.** (1) Test kümesinde mAP@0,5, üç tohumun ortalaması ve standart sapmasıyla raporlanmış olmalı. (2) Takip sonuçları 20 video üzerinde ortalama ± standart sapma olarak verilmeli; `macar_tum` ve `byte` yöntemlerini karşılaştırmalısın. (3) Kare başına süre, GPU ve CPU ayrı ayrı, milisaniye cinsinden ölçülmeli ve 33,3 ms bütçesiyle kıyaslanmalı. (4) Rapor, hangi sonucun hangi tohum ve hangi veri koşuluyla elde edildiğini açıkça belirtmeli.

### Proje 2 (★★★): Sıfırdan U-Net ile sentetik hasar segmentasyonu

**Amaç.** Bu bölümdeki sentetik sahnelere dördüncü bir sınıf ekle: "hasar". Hasar, sahnede rastgele bir çizgi ya da kesik olsun. Bu sınıfı içeren bir U-Net eğiterek hasarın piksel düzeyinde segmentasyonunu yap.

**Beklenen davranış.** Model, her piksel için beş sınıftan (arka plan, daire, kare, üçgen, hasar) birini tahmin etmelidir. Eğitim kaybı CE ve Dice'ın bir bileşimi olmalı. Test kümesinde mIoU, sınıf başına IoU ve sınır bandı doğruluğu raporlanmalıdır.

**Önerilen yaklaşım (ipucu).** Veri üreticisine hasar çizgisini ekleyip piksel maskesini güncelle; maske değerini 4 olarak kodla. 07 betiğindeki `UNet` sınıfının çıkış kanal sayısını 5'e çıkar. Dice kaybını sınıfsal olarak ağırlıklandırmayı dene ama her değişikliği yalnızca doğrulama kümesinde karşılaştır, test kümesini son ana kadar saklamalısın.

**Başarı kriterleri.** (1) Her deney üç tohumla yapılmalı; sonuçlar ortalama ± standart sapma olarak verilmeli. (2) En az iki ablasyon yapılmalı: atlama bağlantısı var/yok ve kayıp yalnızca CE ile CE + Dice. (3) Hasar sınıfının IoU'su ayrıca raporlanmalı; hasar çizgileri ince olduğu için mIoU bu sınıfı gizleyebilir. (4) Hangi hataların (sınır, kaçırılan ince çizgiler, yanlış hasar) baskın olduğu, sınır bandı ve hata haritasıyla gösterilmeli.

### Ek Alıştırmalar

1. ★ (Mülakat) İki kutunun IoU'sunu hesapla: A = (0, 0, 4, 4), B = (2, 2, 6, 6). Kesişim ve birleşimi açıkça yaz.
2. ★ Genişliği 0 olan bir kutunun alanı nedir? Bu kutunun IoU'su tanımlı mıdır? Kodun bu durumda ne döndürmesi gerektiğini savun.
3. ★ (Mülakat) NMS neden gereklidir? Eğer NMS uygulamazsan bir nesne için hangi sorunlar ortaya çıkar?
4. ★★ NMS eşiğini 0,5 yerine 0,3 yaparsan hangi tür hatalar artar? Hangi tür hatalar azalır?
5. ★★ (Mülakat) mAP nedir? İki sınıfın AP'si 0,9 ve 0,5 ise mAP kaçtır? Bu değer neyi gizleyebilir?
6. ★★ 11 nokta AP ile tüm noktalar AP'si ne zaman en çok farklılaşır? Bu farkı bir PR eğrisi üzerinde göster.
7. ★★ Gerçek kutunun genişliği 16 ve anchor genişliği 20 ise tw değeri nedir? Kodlayıp çözmenin neden aynı kutuyu verdiğini açıkla.
8. ★★ Bir tahminin IoU'su 0,5 ise Dice katsayısı kaçtır? Dice ile IoU arasındaki ilişkiyi formülle türet.
9. ★★★ (Mülakat) Takipte kimlik değişimi neden olur? Üç olası nedeni, iki nesnenin birbirine yaklaştığı bir sahne üzerinde açıkla.
10. ★★ Açgözlü ile Macar eşleştirmesinin farkını 2 × 2 bir matrisle göster. Hangi matrislerde ikisi aynı sonucu verir?
11. ★★★ Bir görüntüde 288 hücre ve ortalama 2,48 pozitif hücre var. Pozitif hücrelerin oranı nedir? Nesnellik kaybında pozitiflere neden ağırlık verilir?
12. ★★ mAP@[0,5:0,95] neden mAP@0,5'ten her zaman düşük ya da ona eşit olur? Hangi tür tespit hataları bu farkı büyütür?

## Kod Okuma Egzersizi

Aşağıdaki kesitler, bu bölümde kullandığımız IoU ve NMS fikirlerinin üretim kalitesindeki karşılığıdır. Kaynak: torchvision 0.21.0+cu124, `torchvision/ops/boxes.py`. Kod, kurulu paketin dosyasından birebir kopyalanmıştır (`C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\torchvision\ops\boxes.py`); bölme ya da değişiklik yapılmamıştır. Kesitlerdeki yorum satırları da olduğu gibi korunmuştur. Kitabın 70 karakterlik kod genişliği için uzun satırlar anlamı değiştirmeden bölünmüştür: yorumlar iki satıra ayrılmış, kod satırları ters eğik çizgiyle devam ettirilmiştir. scipy'nin `linear_sum_assignment` fonksiyonu, yerel kurulumda derlenmiş bir modüldedir ve Python kaynağı içermediği için bu egzersizde kullanılmamıştır.

Önce torchvision'ın birleşim ve kesişimi nasıl hesapladığına bak. `_box_inter_union`, bizim `kesisim_birlik` fonksiyonumuzun birebir karşılığıdır.

```python
# implementation from
# https://github.com/kuangliu/torchcv/blob/master/torchcv/utils/box.py
# with slight modifications
def _box_inter_union(boxes1: Tensor, boxes2: Tensor) -> \
    Tuple[Tensor, Tensor]:
    area1 = box_area(boxes1)
    area2 = box_area(boxes2)

    lt = torch.max(boxes1[:, None, :2], boxes2[:, :2])  # [N,M,2]
    rb = torch.min(boxes1[:, None, 2:], boxes2[:, 2:])  # [N,M,2]

    wh = _upcast(rb - lt).clamp(min=0)  # [N,M,2]
    inter = wh[:, :, 0] * wh[:, :, 1]  # [N,M]

    union = area1[:, None] + area2 - inter

    return inter, union
```

Aşağıdaki `box_iou`, yukarıdaki iki fonksiyonu birleştirir. Son satırda bölme vardır ve bir epsilon yoktur.

```python
def box_iou(boxes1: Tensor, boxes2: Tensor) -> Tensor:
    """
    Return intersection-over-union (Jaccard index) between two sets
        of boxes.

    Both sets of boxes are expected to be in ``(x1, y1, x2, y2)``
        format with
    ``0 <= x1 < x2`` and ``0 <= y1 < y2``.

    Args:
        boxes1 (Tensor[N, 4]): first set of boxes
        boxes2 (Tensor[M, 4]): second set of boxes

    Returns:
        Tensor[N, M]: the NxM matrix containing the pairwise IoU
            values for every element in boxes1 and boxes2
    """
    if not torch.jit.is_scripting() and not torch.jit.is_tracing():
        _log_api_usage_once(box_iou)
    inter, union = _box_inter_union(boxes1, boxes2)
    iou = inter / union
    return iou


# Implementation adapted from
# https://github.com/facebookresearch/detr/blob/master/util/box_ops.py
```

Aşağıda batched NMS'in karar bloğu (URL içeren iki yorum satırı atlanmıştır), ardından koordinat numarası hilesini uygulayan fonksiyon yer alır. Bu hile, Bölüm 67.4'te gördüğümüz sınıf başına NMS fikrinin ta kendisidir.

```python
    if boxes.numel() > (4000 if boxes.device.type == "cpu" else \
        20000) and not torchvision._is_tracing():
        return _batched_nms_vanilla(boxes, scores, idxs, \
            iou_threshold)
    else:
        return _batched_nms_coordinate_trick(boxes, scores, idxs, \
            iou_threshold)
```

```python
@torch.jit._script_if_tracing
def _batched_nms_coordinate_trick(
    boxes: Tensor,
    scores: Tensor,
    idxs: Tensor,
    iou_threshold: float,
) -> Tensor:
    # strategy: in order to perform NMS independently per class,
    # we add an offset to all the boxes. The offset is dependent
    # only on the class idx, and is large enough so that boxes
    # from different classes do not overlap
    if boxes.numel() == 0:
        return torch.empty((0,), dtype=torch.int64, \
            device=boxes.device)
    max_coordinate = boxes.max()
    offsets = idxs.to(boxes) * (max_coordinate + \
        torch.tensor(1).to(boxes))
    boxes_for_nms = boxes + offsets[:, None]
    keep = nms(boxes_for_nms, scores, iou_threshold)
    return keep
```

**Sorular — cevaplamadan geçme:**

1. `_box_inter_union` içinde `boxes1[:, None, :2]` ve `boxes2[:, :2]` gibi indeksleme, N × M sonucu nasıl üretir? Bu yapıya ne ad verilir ve neden döngüye gerek kalmaz?
2. `wh = _upcast(rb - lt).clamp(min=0)` satırı hangi durumu engeller? Bu satırı kaldırırsan hangi IoU değerleri bozulur?
3. Birlik `area1[:, None] + area2 - inter` ifadesinde kesişim neden çıkarılır? Bu çıkarma olmasaydı IoU'nun üst sınırı ne olurdu?
4. `box_iou` içinde bölme `inter / union` olarak yapılır ve epsilon yoktur. Birlik sıfır olursa (iki dejenere kutu) bu bölme ne üretir? Bizim `iou_matris` fonksiyonunun bu durumda döndürdüğü değerle karşılaştır.
5. `_batched_nms_coordinate_trick` neden her kutuya `max_coordinate + 1` ile çarpılmış bir sınıf ofseti ekler? Bu ofset yeterince büyük değilse hangi iki sınıfın kutuları birbirini bastırabilir?
6. `batched_nms` neden kutu sayısına göre iki farklı yol seçiyor (4000 ve 20000 eşikleri)? Bu eşiklerin doğru olduğunu nasıl ölçerdin? Bu bölümde bu ölçümü yapmadık; bunu bir alıştırma olarak düşün.

## Bölüm Özeti

- Tespit, segmentasyon ve takip, tek bir görsel hattın üç farklı çıktısıdır; her biri farklı bir metrikle ölçülür.
- IoU, kutular arasındaki örtüşmenin standart ölçüsüdür; GIoU, örtüşmeyen kutular için bir eğitim sinyali verir.
- NMS, aynı nesnenin fazla kutularını bastırır; eşik seçimi, yakın nesnelerin ayrı tutulup tutulmayacağını belirler. Soft-NMS skoru azaltır, siler değil.
- AP, PR eğrisinin altındaki alandır; 11 nokta, COCO tarzı 101 nokta ve tüm noktalar yöntemleri farklı değerler verir ve raporda belirtilmelidir.
- mAP@0,5 ile mAP@[0,5:0,95] birlikte verilmelidir; ilki ayrım gücünü, ikincisi yerelleştirme hassasiyetini ölçer.
- Anchor ve ofset kodlama, ağın kutuyu doğrudan piksel koordinatlarında değil, anchor'a göre bir düzeltme olarak öğrenmesini sağlar.
- U-Net, kodlayıcı–çözücü yapısı ve atlama bağlantılarıyla segmentasyonu yapar; atlama bağlantısı özellikle sınır doğruluğunu artırır.
- Açgözlü eşleştirme yerel en iyiyi, Macar algoritması ise global en iyi eşleşmeyi bulur; kimlik değişimi çoğunlukla nesneler birbirine yaklaştığında ortaya çıkar.
- Gerçek zamanlı bir hatta her aşamanın süresi ayrı ölçülmeli; bu küçük ağda GPU ile girdi boyutu arasındaki ilişki düz çıktı, gecikme çekirdek başlatma yükü tarafından belirlendi.

**Sonraki bölümde:** Bu bölümde her karenin bağımsız işlendiğini varsaydık. Gerçek bir İHA'da ise kareler bir zaman serisi oluşturur ve telemetri (hız, irtifa, sensör okumaları) da aynı zaman ekseninde akar. Bölüm 68'de dizi modellerini (RNN, LSTM, GRU) ve zaman serisi tahminini göreceksin; takipteki hareket modeli ile dizi modelleri arasındaki ilişkiyi de orada kuracağız.

::: mulakat
1. IoU'yu tanımla ve iki kutu hiç örtüşmediğinde neden GIoU'nun IoU'ya tercih edildiğini açıkla.
2. NMS neden gereklidir ve açgözlü NMS'in karmaşıklığı nedir? Karmaşıklığı azaltmak için hangi yaklaşımlar kullanılır?
3. mAP nedir? mAP@0,5 ile mAP@[0,5:0,95] arasındaki farkı ve hangisinin hangi hatayı yakaladığını açıkla.
4. Anchor kutuları nedir ve neden kullanılır? Anchor'sız (anchor-free) dedektörlerin bu fikirden hangi bileşeni çıkardığını söyle.
5. Tek aşamalı ve iki aşamalı dedektörler arasındaki temel farkı ve bu farkın hız–doğruluk takasına etkisini açıkla.
6. U-Net'te atlama bağlantıları neden sınır doğruluğunu artırır? Bu bağlantılar olmadan çözücü hangi bilgiyi kaybeder?
7. Takipte kimlik değişimi (ID switch) neden olur? Açgözlü ile Macar eşleştirmesinin bu hatayı nasıl etkilediğini açıkla.
8. Bir gerçek zamanlı tespit hattında 30 FPS hedefini karşılamak için hangi bileşenlerin süresini ölçerdin ve hangi sırayla iyileştirirdin?
