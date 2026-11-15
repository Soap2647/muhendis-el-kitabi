%% kisim_no: XV
%% kisim_ad: Derin Öğrenme
%% bolum_no: 69
%% baslik: Attention & Transformer

## Giriş: Bütün girdiye birden bakmak

Bölüm 68'de dizileri sırayla okudun. Bir RNN ya da LSTM her adımda bir öncekinin gizli durumunu bekler, sonra kendi durumunu üretir. Bu düzen iki bedel getirir. Birincisi, uzun bir dizinin başındaki bilgi her adımda biraz daha seyrelir; Bölüm 68'de LSTM'in kapıları bunu hafifletmişti ama ortadan kaldırmamıştı. İkincisi, `T` adımlık bir dizi `T` tane birbirine bağlı adımdan oluşur ve bu adımları GPU'da paralel çalıştıramazsın. Encoder–decoder yapısında bu sorun daha da büyür: tüm girdi, Bölüm 68'de gördüğün gibi, sabit boyutlu tek bir bağlam vektörüne sıkıştırılır.

Dikkat (attention) mekanizması bu iki sorunu birden çözer. Çıktının her adımı, girdinin bütün konumlarına doğrudan bakar ve hangisinin şu an önemli olduğunu kendisi öğrenir. Bağlam tek bir vektörde sıkışmaz; her konum, o anki soruya uygun bir ağırlıkla katkı verir. Tüm konumlar aynı anda hesaplanabildiği için de eğitim paralel yürür. 2017'de Vaswani ve arkadaşları, yalnızca dikkate dayanan Transformer mimarisini tanıttı. Bugünkü büyük dil modelleri, görüntü modelleri ve çok modlu modeller bu yapının çeşitlerinden oluşur. Bu alan genel bilgi olarak böyle özetlenebilir; kendi deneylerimizde olmayan makale iddialarını bu bölümde doğrulamadan kullanmayacağız.

Savunma sanayiinde bu bölümün karşılığı, uzun zaman serilerinde ve çok kanallı sensör akışlarında uzak ilişkileri yakalamaktır. Bir İHA'nın telemetri kaydında, kalkıştaki bir sensör sapması, saatler sonraki bir iniş kararıyla ilişkili olabilir. Bölüm 68'de bu tür uzun bağımlılıklar RNN için zordu; burada her adım her adımı doğrudan görür. Mert'in EV Dashboard projesindeki STM32 sensör akışı da aynı türden bir örnektir: önemli olay, her zaman hemen önceki örnekte değildir.

Mülakatlarda en sık gelen sorulardan biri budur: "Transformer neden RNN'den daha hızlı eğitilir ve neden uzun bağlamı daha iyi yakalar?" Bu soruya ezber cevap vermek yerine, bu bölümde her parçayı kendin kurarak cevap verebilmelisin. Bölümün sonunda, sıfırdan yazdığın küçük bir Transformer'ı üç görevde eğitip ölçeceğiz: dizi ters çevirme (encoder–decoder), karakter düzeyi dil modeli (decoder-only) ve küçük bir Vision Transformer (görüntü).

::: not
Bu bölümde `nn.Transformer` ve `nn.MultiheadAttention` modüllerini yalnızca karşılaştırma için kullanıyoruz. Attention'ın kendisi, başlara bölme, maskeler, konum kodlaması ve blok yapısı bizim kodumuzdur. Kütüphanenin sonucuna eşit olması, kendi gerçeklememizin doğru olduğunun kanıtıdır.
:::

## 69.1 RNN'in darboğazı ve dikkat fikri

Bölüm 68'deki encoder–decoder düzenini hatırla. Encoder girdi dizisini okur ve son gizli durumunu `c` olarak verir. Decoder, çıktı dizisini yalnızca bu `c` vektörüne bakarak üretir. Bu düzende bütün bilgi tek bir vektörden geçer. Bir İngilizce cümleyi Türkçeye çeviren model, cümle uzadıkça `c`'nin o kadar çok şey taşımasını bekler. Uzunluk sabit bir vektörün kapasitesini aştığında model önce ayrıntıları, sonra da bütün cümleyi unutur. Bu sınır, Bölüm 68'deki encoder–decoder düzeninin doğrudan sonucudur.

İkinci sorun hesap düzenidir. `h_t`, `h_{t−1}`'e bağlıdır. Yani `T` adımlık bir dizi için `T` sıralı adım gerekir ve bu adımları birbirinden bağımsız hesaplayamazsın. GPU çok sayıda işi aynı anda yapmakta iyidir; ama zincirin her halkası bir öncekini beklediği için bu gücün büyük kısmı boşa gider.

Dikkat fikri şöyle özetlenebilir: decoder her çıktı adımında, encoder'ın bütün konumlarına bir soru sorar: "Bu adımı üretmek için hangi girdi konumları önemli?" Cevap olarak her konum için bir ağırlık alır ve encoder durumlarının ağırlıklı toplamını bağlam olarak kullanır:

`c_t = Σ_j α_{t,j} · h_j`, burada `α_{t,j} ≥ 0` ve `Σ_j α_{t,j} = 1`.

Bu ağırlıklar sabit değildir; her çıktı adımında yeniden hesaplanır. Böylece bağlam vektörü artık tek bir sıkıştırılmış özet değil, adıma özel bir seçimdir. Bahdanau, Cho ve Bengio'nun 2015'teki makalesi bu fikri çeviri için önerdi; skoru küçük bir sinir ağıyla (toplamsal dikkat) hesaplıyordu. Aynı yıl Luong ve arkadaşları, skoru doğrudan iki vektörün çarpımıyla hesaplayan daha basit bir varyant (çarpımsal dikkat) önerdi. Bu iki makalenin ayrıntılarını bu bölümde yeniden türetmiyoruz; genel bilgi olarak veriyoruz. Önemli olan, skorun sonra bir softmax'tan geçip ağırlığa dönüşmesidir. Bu softmax'ı Bölüm 51.10'da çapraz entropi ile birlikte gördün.

Şekil 69.1, iki tasarımı yan yana gösteriyor. Sol panelde RNN tüm bilgiyi tek kutudan geçirir. Sağ panelde sorgu, her gizli duruma ayrı bir ağırlıkla bağlanır. Kalın çizgiler yüksek ağırlığa karşılık gelir.

![Şekil 69.1: Solda RNN encoder–decoder: tüm girdi tek bağlam vektörü c'den geçer. Sağda dikkat: sorgu her gizli duruma bir α ağırlığıyla bağlanır; çizgi kalınlığı ağırlıkla orantılıdır.](gorseller/b69_darbogaz.png)

Bölüm 68'deki teacher forcing eğitimi burada da geçerlidir: decoder eğitimde gerçek önceki belirteci görür, üretimde ise kendi tahminini kullanır. Dikkat bu konuda bir şey değiştirmez; ama her adımda girdiye doğrudan baktığı için uzun çıktı dizilerinde bağlamı daha az kaybeder. Bu bölümün ters çevirme deneyinde, RNN taban çizgisinin dizi uzadıkça nasıl çöktüğünü ayrıca ölçeceğiz.

## 69.2 Sorgu, anahtar ve değer: yumuşak sözlük araması

Bir sözlükte (dict) anahtar üzerinden arama yaparsın. Anahtar tam eşleşirse değeri alırsın; eşleşmezse hiçbir şey alamazsın. Dikkat bu fikrin yumuşak bir versiyonudur. Her anahtar sorguyla ne kadar benzer olduğuna göre bir ağırlık alır, sonuç da ağırlıklı bir değer toplamı olur. Sert eşleşme yerine yumuşak eşleşme vardır; bu yüzden fark türevlenebilir ve geri yayılımla eğitilebilir.

Üç rol vardır:

| Rol | Sembol | Ne işe yarar | Şekil (tek başlı) |
|---|---|---|---|
| Sorgu (query) | Q | "Ne arıyorum?" | T_sorgu × d_k |
| Anahtar (key) | K | "Ben neyle eşleşirim?" | T_anahtar × d_k |
| Değer (value) | V | "Eşleşirsem ne taşırım?" | T_anahtar × d_v |

Anahtar ile değerin ayrı tutulmasının nedeni, eşleşme ölçütü ile taşınan bilginin farklı olabilmesidir. Bir cümlede "o" zamiri, eşleşmek için "isim" özelliğine bakar; ama aldığı bilgi, ismin anlamını içeren vektördür. Bu nedenle `K` ve `V`, aynı girdinin iki ayrı doğrusal projeksiyonu olarak öğrenilir: `K = XW_K`, `V = XW_V`. Sorgu da `Q = XW_Q` ile üretilir. Üç ağırlık matrisi de eğitilir, yani hangi bilginin nasıl eşleşeceğini ve hangi bilginin taşınacağını ağ kendisi seçer.

Bu projeksiyonlar Bölüm 48'deki matris çarpımıyla hesaplanır: `X` bir `T × d` matrisi, `W_Q` bir `d × d_k` matrisidir ve `XW_Q` bir `T × d_k` matris verir. Her satır bir belirtecin sorgu vektörüdür. Bölüm 48.2'de gördüğün nokta çarpım burada benzerlik ölçüsüdür: iki vektör ne kadar aynı yöndeyse çarpımları o kadar büyür. Benzerlik skorunun softmax'tan geçmesi ise Bölüm 51'in olasılık dönüşümüdür.

Bu bölümde "öz-dikkat" (self-attention) ile "çapraz dikkat" (cross-attention) ayrımını sık kullanacağız. Öz-dikkatte `Q`, `K` ve `V` aynı diziden gelir: dizi kendi içinde bakar. Çapraz dikkatte sorgu bir diziden (decoder), anahtar ve değer başka bir diziden (encoder) gelir. Transformer'ın encoder–decoder biçiminde ikisi de bulunur. Hangisinin hangi katmanda olduğunu blok anlatımında yeniden göreceksin.

Burada bir noktayı açıkça söylemek gerekir: attention "anlam" hesaplamaz. Hesapladığı şey, sayılar arasındaki benzerliğin ağırlıklı ortalamasıdır. Anlamın ne olduğunu ağ, eğitim sırasında `W_Q`, `W_K` ve `W_V`'yi ayarlayarak öğrenir. Bu yüzden bu bölümün tüm deneyleri, sonucu sayıyla ölçmeye dayanır.

## 69.3 Ölçekli nokta çarpımı attention

Tek başlı ölçekli nokta çarpımı attention'ın formülü şudur:

`Attention(Q, K, V) = softmax(Q Kᵀ / √d_k) V`

Formül üç adımdan oluşur ve her adımın şeklini bilmek, hataların çoğunu daha kodlamadan yakalamanı sağlar. Tablo, `T` belirteçli bir dizi için her ara sonucun şeklini gösterir. Burada tek bir dizi ve tek bir baş düşünüyoruz; batch boyutunu `B` ile gösterirsek her şeyin önüne `B ×` eklenir.

| Adım | İşlem | Şekil |
|---|---|---|
| 1 | Projeksiyon: `Q = XW_Q`, `K = XW_K`, `V = XW_V` | `Q`, `K`: T × d_k; `V`: T × d_v |
| 2 | Skor: `S = Q Kᵀ` | `Kᵀ`: d_k × T; `S`: T × T |
| 3 | Ölçekleme: `S / √d_k` | T × T |
| 4 | Softmax (her satır ayrı): `A = softmax(S/√d_k)` | T × T, her satırın toplamı 1 |
| 5 | Birleştirme: `A V` | T × d_v |

`S` matrisinin `(i, j)` hücresi, `i`. sorgunun `j`. anahtara benzerliğidir. `A`'nın bir satırı, o sorgunun bütün anahtarlara verdiği ağırlıkların olasılık dağılımıdır. Çıktının `i`. satırı, bu ağırlıklarla `V`'nin satırlarının toplamıdır. Dolayısıyla attention'ın çıktısı girdi ile aynı uzunlukta bir dizidir; ama her belirteç artık bütün dizinin ağırlıklı özetini taşır.

**Neden `√d_k`?** Diyelim ki `q` ve `k` vektörlerinin bileşenleri birbirinden bağımsız, ortalaması 0 ve varyansı 1 olan sayılar. Bu durumda `q·k = Σ_{i=1}^{d_k} q_i k_i` toplamının ortalaması 0, varyansı `d_k`'dir. Yani skorun standart sapması `√d_k` ile büyür. `d_k = 512` olduğunda skorlar kabaca ±22 mertebesinde dağılır. Softmax'ın bu büyüklükteki sayılarda neredeyse tek bir `1`'e ve geri kalan `0`lara dönüştüğünü düşünebilirsin. Bu durumda çıktı, en büyük skora sahip tek bir anahtarın değeri olur; gradyan ise neredeyse sıfırdır, çünkü softmax'ın Jacobian'ı `diag(p) − ppᵀ` (Bölüm 55.6) olasılıklar 0 ya da 1'e yaklaştığında sıfıra gider. Skoru `√d_k`'ya bölersek varyans 1'e iner ve softmax doygunluktan çıkar.

Bu fikri sadece sözle bırakmayalım. Aşağıdaki program üç şeyi yapıyor. Birincisi, attention'ı NumPy ile sıfırdan yazıyor ve üç tokenlık bir örneği elle hesapladığımız değerlerle karşılaştırıyor. İkincisi, kendi gerçeklememizi PyTorch'un `F.scaled_dot_product_attention` fonksiyonuyla hem maskesiz hem nedensel durumda eşleştiriyor. Üçüncüsü, `d_k` değiştikçe ölçeklenmemiş ve ölçeklenmiş skorların davranışını ölçüyor. Tohum sabit (`default_rng(0)`) olduğu için sonuçlar her çalıştırmada aynıdır.

Aşağıdaki kod, `attention` fonksiyonunu ve üç deneyi birlikte içerir. Program yalnızca NumPy ve PyTorch kullanır ve CPU üzerinde çalışır; GPU'ya hiç dokunmaz.

```python
# -*- coding: utf-8 -*-
"""Bölüm 69 - Ölçekli nokta çarpımı attention, sıfırdan (NumPy)."""

import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""  # bu bölümde yalnızca CPU
import csv
import numpy as np
import torch
import torch.nn.functional as F

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
np.set_printoptions(precision=4, suppress=True)

def softmax(z, eksen=-1):
    z = z - z.max(axis=eksen, keepdims=True)  # taşmayı önler
    e = np.exp(z)
    return e / e.sum(axis=eksen, keepdims=True)

def attention(Q, K, V, maske=None):
    """softmax(QK^T/sqrt(d_k)) V; maske False -> -inf."""
    dk = Q.shape[-1]
    S = Q @ np.swapaxes(K, -1, -2) / np.sqrt(dk)
    if maske is not None:
        S = np.where(maske, S, -np.inf)
    A = softmax(S, eksen=-1)
    return A @ V, A
```

```python
def ornek_uc_token():
    print("--- 3 token, d_k = 2 ---")
    Q = np.array([[1, 0], [0, 1], [1, 1]], float)
    K = Q.copy()
    V = np.array([[1, 2], [3, 4], [5, 6]], float)
    print("QK^T =")
    print(Q @ K.T)
    out, A = attention(Q, K, V)
    print("A =")
    print(A)
    print("cikti =")
    print(out)

def sekiller():
    print("--- boyutlar (B=2, T=3, d_k=4, d_v=5) ---")
    rng = np.random.default_rng(0)
    Q = rng.normal(size=(2, 3, 4))
    K = rng.normal(size=(2, 3, 4))
    V = rng.normal(size=(2, 3, 5))
    S = Q @ np.swapaxes(K, -1, -2)
    out, A = attention(Q, K, V)
    print("Q", Q.shape, "K", K.shape, "V", V.shape)
    print("QK^T", S.shape, "A", A.shape, "cikti", out.shape)
    print("her satirin toplami:", np.allclose(A.sum(-1), 1.0))
```

```python
def torch_eslesme():
    print("--- NumPy ile PyTorch eslesmesi (float64) ---")
    rng = np.random.default_rng(1)
    Q, K, V = (rng.normal(size=(2, 5, 8)) for _ in range(3))
    t = lambda x: torch.tensor(x, dtype=torch.float64)
    out_np, _ = attention(Q, K, V)
    out_t = F.scaled_dot_product_attention(t(Q), t(K), t(V))
    print(
        "maks fark (maskesiz): %.2e"
        % np.abs(out_np - out_t.numpy()).max()
    )
    m = np.tril(np.ones((5, 5), bool))
    out_np, _ = attention(Q, K, V, m)
    out_t = F.scaled_dot_product_attention(
        t(Q), t(K), t(V), is_causal=True
    )
    print(
        "maks fark (nedensel): %.2e"
        % np.abs(out_np - out_t.numpy()).max()
    )
```

```python
def dk_doyma():
    print("--- d_k'ye gore softmax doyması (T=16, 500 deneme) ---")
    rng = np.random.default_rng(0)
    T, N = 16, 500
    satirlar = []
    print("  d_k  std(ham)  maks_ham  maks_olcekli  H_olcekli/logT")
    for dk in [2, 8, 32, 128, 512]:
        Q = rng.normal(size=(N, T, dk))
        K = rng.normal(size=(N, T, dk))
        ham = Q @ np.swapaxes(K, -1, -2)
        olc = ham / np.sqrt(dk)
        Ah, Ao = softmax(ham), softmax(olc)
        std_ham = ham.std()
        mh = Ah.max(-1).mean()
        mo = Ao.max(-1).mean()
        H = -(Ao * np.log(Ao)).sum(-1).mean() / np.log(T)
        print(
            "%5d  %8.3f  %8.4f  %12.4f  %14.4f"
            % (dk, std_ham, mh, mo, H)
        )
        satirlar.append(
            [
                dk,
                "%.4f" % std_ham,
                "%.4f" % mh,
                "%.4f" % mo,
                "%.4f" % H,
            ]
        )
    return satirlar
```

```python
if __name__ == "__main__":
    ornek_uc_token()
    sekiller()
    torch_eslesme()
    satirlar = dk_doyma()
    with open(
        os.path.join(VERI, "b69_dk_doyma.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(
            [
                "dk",
                "std_ham",
                "maks_olceksiz",
                "maks_olcekli",
                "entropi_olcekli",
            ]
        )
        w.writerows(satirlar)
```

Programın çıktısı şöyledir:

```term
$ python g01_attn.py
--- 3 token, d_k = 2 ---
QK^T =
[[1. 0. 1.]
 [0. 1. 1.]
 [1. 1. 2.]]
A =
[[0.4011 0.1978 0.4011]
 [0.1978 0.4011 0.4011]
 [0.2483 0.2483 0.5035]]
cikti =
[[3.     4.    ]
 [3.4067 4.4067]
 [3.5105 4.5105]]
--- boyutlar (B=2, T=3, d_k=4, d_v=5) ---
Q (2, 3, 4) K (2, 3, 4) V (2, 3, 5)
QK^T (2, 3, 3) A (2, 3, 3) cikti (2, 3, 5)
her satirin toplami: True
--- NumPy ile PyTorch eslesmesi (float64) ---
maks fark (maskesiz): 4.44e-16
maks fark (nedensel): 2.78e-16
--- d_k'ye gore softmax doyması (T=16, 500 deneme) ---
  d_k  std(ham)  maks_ham  maks_olcekli  H_olcekli/logT
    2     1.404    0.2986        0.2225          0.8680
    8     2.838    0.5635        0.2400          0.8547
   32     5.669    0.7767        0.2451          0.8508
  128    11.331    0.8922        0.2474          0.8498
  512    22.677    0.9442        0.2482          0.8489
```

Çıktının ilk bölümü, Örnek 1'de elle yapacağın işlemin bilgisayar karşılığıdır. `QKᵀ` matrisi, `(1, 0)·(1, 1) = 1` gibi nokta çarpımlarından oluşur. Satır `[1, 0, 1]` ilk sorgunun üç anahtarla skorlarıdır. Softmax'tan sonra `A`'nın ilk satırı `[0,4011, 0,1978, 0,4011]` olur; toplamları 1'dir. Çıktının ilk satırı `[3, 4]`tür. Bu, ağırlıklı toplamda `V`nin ilk satırı `(1, 2)`ye ağırlık `0,4011` ve üçüncü satırı `(5, 6)`ya ağırlık `0,4011` verilmesinin, ikinci satır `(3, 4)`ün ağırlığı `0,1978` ile birleşmesinin sonucudur. Sonuç tam olarak `3` ve `4`tür: `V₁` ile `V₃`ün ortalaması `(3, 4)`tür ve bu iki dış anahtara eşit ağırlık verildiği için toplam, ortadaki `V₂ = (3, 4)` ile aynı çıkar. Bunu not al; bu örnekte birkaç değer kasıtlı olarak sade seçildi.

İkinci bölüm, boyutları sınar: `Q`, `K`, `V` ve çıktı beklenen şekillerdedir ve `A` satır toplamları 1'dir. Üçüncü bölüm, bizim gerçeklememizin PyTorch'un sonucuyla `10⁻¹⁶` mertebesinde eşleştiğini gösterir. Bu fark makine hassasiyetidir; yani iki implementasyon aynı matematiği yapıyor. Son bölümde ise `d_k` arttıkça ne olduğunu görürsün.

Şekil 69.2, bu adımların veri akışını gösterir. Her kutunun altındaki şekil, o ara sonucun boyutudur.

![Şekil 69.2: Ölçekli nokta çarpımı attention'ın veri akışı. X'ten üç projeksiyonla Q, K, V üretilir; QKᵀ T×T skor matrisini verir; ölçekleme ve satır softmax'ından sonra A·V çıktıyı oluşturur.](gorseller/b69_akis.png)

Deneyin son bölümü `d_k`'ye göre tabloyu üretir. Her satır, 500 rastgele `Q` ve `K` örneği üzerinden ortalamadır. `T = 16` belirteçli bir dizide skorların standart sapması, `d_k` ile `√d_k` gibi büyür: `d_k = 2`de yaklaşık 1,40, `d_k = 512`de 22,68. Ölçeksiz softmax'ta satır başına en büyük ağırlık `d_k = 512`de 0,944 olur; yani dağılım neredeyse tek bir anahtara çökmüştür. Ölçekli versiyonda aynı büyüklük 0,248 ile sabit kalır. Sonuncu sütun, ölçekli dağılımın normalize entropisidir (`H / log T`); 1'e yakın değerler düzgün dağılıma yakın, 0'a yakın değerler tek bir noktaya çökmüş demektir. Şekil 69.3, bu sonuçları iki panelde gösterir.

![Şekil 69.3: Solda ham skorun standart sapması d_k ile √d_k gibi büyür (kesikli çizgi kuramsal değer). Sağda ölçeksiz softmax'ta en büyük ağırlık d_k arttıkça 1'e yaklaşır; ölçekli versiyon ise düzgün kalır. Veri: 500 deneme, T = 16.](gorseller/b69_dk_doyma.png)

Bu sonucun pratik anlamı şudur: `d_k` büyüdükçe ölçeklemeyi unutmak, modelin eğitimini sessizce bozar. Hata mesajı çıkmaz; kayıp düşmez ya da yavaş düşer. Bu tür hataları ancak skor dağılımına bakarak fark edersin. Bölüm 64.10'da kayıp eğrisini okumayı öğrendin; burada da "kayıp neden düşmüyor?" sorusuna bir cevap olarak attention skorlarının dağılımını kullanabilirsin.

Bir ayrıntı daha: `softmax` hesaplarken en büyük değeri çıkarmak gerekir (Bölüm 51.10'daki sayısal kararlılık). Kodumuzdaki `softmax` fonksiyonu bunu yapar. Büyük `d_k` ve büyük skorlarla çalışırken, bu adımı atlamak taşmaya yol açar.

## 69.4 Maskeleme: dolgu ve nedensel maske

Attention her sorguya bütün anahtarları gösterir. Bazen bu istenmez. İki durum vardır. Birincisi dolgu (padding): farklı uzunluktaki diziler, aynı batch'te kullanılabilmek için sona sıfır belirteçleri eklenerek eşitlenir. Bu dolgu konumları anlamlı bir girdi değildir; attention onlara ağırlık vermemelidir. İkincisi nedensel (causal) maske: bir dil modeli `t`. konumu üretirken `t + 1`den sonraki belirteçleri görmemelidir. Aksi halde eğitimde model sonucu zaten bilerek kopyalar ve üretimde işe yaramaz.

Maskeleme mekanizması basittir. Skor matrisi `S` softmax'a girmeden önce, izin verilmeyen hücrelere `−∞` eklenir. `exp(−∞) = 0` olduğu için bu hücrelerin ağırlığı tam olarak sıfır olur ve softmax kalan hücreleri kendi aralarında normalize eder. Yani maske bir çarpma değil, bir ekleme ile uygulanır; bu da satır toplamının 1 kalmasını sağlar. Nedensel maske, `T × T` boyutunda bir alt üçgen matristir (`np.tril`). Köşegenin üstündeki hücreler, yani gelecekteki konumlar, kapalıdır.

Maskenin doğru çalıştığını varsaymak yerine test ederiz. Test şu soruyu sorar: gelecekteki bir belirteci değiştirirsen, geçmişteki çıktılar değişir mi? Doğru maskeleme ile cevap hayırdır. Dolgu testinde ise dolgu konumlarındaki değerleri değiştiririz ve gerçek belirteçlerin çıktıları aynı kalmalıdır. Program bu iki testi ve bir tuzağı gösterir.

```python
# -*- coding: utf-8 -*-
"""Bölüm 69 - Dolgu ve nedensel maskeleme: gizlilik testleri."""

import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""  # bu bölümde yalnızca CPU
import numpy as np

np.set_printoptions(precision=3, suppress=True)

def softmax(z):
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)

def attention(Q, K, V, maske=None):
    S = Q @ K.T / np.sqrt(Q.shape[-1])
    if maske is not None:
        S = np.where(maske, S, -np.inf)
    A = softmax(S)
    return A @ V, A

def nedensel_maske(T):
    return np.tril(np.ones((T, T), dtype=bool))
```

```python
def gizlilik_testi():
    print(
        "--- Nedensel maske: gelecek degisince gecmis? ---"
    )
    rng = np.random.default_rng(0)
    T, d = 6, 4
    Q, K, V = (rng.normal(size=(T, d)) for _ in range(3))
    m = nedensel_maske(T)
    print("maske (1 = gorulebilir):")
    print(m.astype(int))
    out1, A = attention(Q, K, V, m)
    K2, V2 = K.copy(), V.copy()
    K2[4:], V2[4:] = rng.normal(size=(2, d)), rng.normal(size=(2, d))
    out2, _ = attention(Q, K2, V2, m)
    print("t<4 satirlarinda fark:", np.abs(out1[:4] - out2[:4]).max())
    print(
        "t>=4 satirlarinda fark:", np.abs(out1[4:] - out2[4:]).max()
    )
    print("3. satirin agirliklari:", A[3])
    out3, _ = attention(Q, K2, V2)  # maskesiz karsilastirma
    out4, _ = attention(Q, K, V)
    print("maskesiz: t<4 fark:", np.abs(out3[:4] - out4[:4]).max())
```

```python
def dolgu_testi():
    print("--- Dolgu maskesi: 2 ornek, uzunluklar 5 ve 3 ---")
    rng = np.random.default_rng(1)
    T, d = 5, 4
    uzunluk = [5, 3]
    Q = rng.normal(size=(2, T, d))
    K = rng.normal(size=(2, T, d))
    V = rng.normal(size=(2, T, d))
    for b, L in enumerate(uzunluk):
        m = np.zeros((T, T), dtype=bool)
        m[:, :L] = True  # anahtar tarafında dolguyu kapat
        K2, V2 = K.copy(), V.copy()
        K2[b, L:] = rng.normal(size=(T - L, d))
        V2[b, L:] = rng.normal(size=(T - L, d))
        o1, _ = attention(Q[b], K[b], V[b], m)
        o2, _ = attention(Q[b], K2[b], V2[b], m)
        print(
            "ornek %d: dolgu degisince cikti farki = %.1e"
            % (b, np.abs(o1 - o2).max())
        )

def nan_tuzagi():
    print("--- Tuzak: bir satirin tamamen maskelenmesi ---")
    rng = np.random.default_rng(2)
    T, d = 3, 2
    Q, K, V = (rng.normal(size=(T, d)) for _ in range(3))
    m = nedensel_maske(T)
    m[0, :] = False  # ilk sorgu hicbir anahtari gormez
    out, A = attention(Q, K, V, m)
    print("ilk satir:", A[0])
    print("NaN sayisi:", int(np.isnan(out).sum()))
    m2 = nedensel_maske(T)
    m2[0, :] = False
    S = Q @ K.T / np.sqrt(d)
    S2 = np.where(m2, S, -1e9)  # -inf yerine buyuk negatif
    print("-1e9 ile satir:", softmax(S2)[0])
```

```python
if __name__ == "__main__":
    gizlilik_testi()
    dolgu_testi()
    nan_tuzagi()
```

Çıktı şöyledir:

```term
$ python g02_maske.py
--- Nedensel maske: gelecek degisince gecmis? ---
maske (1 = gorulebilir):
[[1 0 0 0 0 0]
 [1 1 0 0 0 0]
 [1 1 1 0 0 0]
 [1 1 1 1 0 0]
 [1 1 1 1 1 0]
 [1 1 1 1 1 1]]
t<4 satirlarinda fark: 0.0
t>=4 satirlarinda fark: 0.5767878851858073
3. satirin agirliklari: [0.133 0.582 0.151 0.133 0.    0.   ]
maskesiz: t<4 fark: 0.8227768567947422
--- Dolgu maskesi: 2 ornek, uzunluklar 5 ve 3 ---
ornek 0: dolgu degisince cikti farki = 0.0e+00
ornek 1: dolgu degisince cikti farki = 0.0e+00
--- Tuzak: bir satirin tamamen maskelenmesi ---
ilk satir: [nan nan nan]
NaN sayisi: 2
-1e9 ile satir: [0.333 0.333 0.333]
```

Çıktının ilk bölümü nedensel maskenin şeklini gösterir. Dördüncü satır (`t = 3`), yalnızca ilk dört konuma bakabilen belirtecin ağırlıklarıdır: `[0,133 0,582 0,151 0,133 0 0]`. Son iki hücre tam sıfırdır. Gelecek değiştirildiğinde ilk dört satırın farkı `0,0` çıkar; yani geçmiş hiç etkilenmedi. Aynı deneyde maske kaldırılınca, aynı geçmiş satırların farkı `0,82` olur. Bu iki sayı arasındaki fark, maskenin işini yaptığını ölçülebilir biçimde gösterir.

Dolgu testinde iki örneğin de dolgu konumlarındaki değişiklik, gerçek belirteçlerin çıktısını `0,0` farkla bırakır. Burada tam sıfır, değerlerin kendilerinin çarpımda sıfır ile çarpılmasından gelir: dolgu sütunlarının ağırlığı `0`dır ve `0 · v = 0` tam olarak doğrudur. Gerçek bir sistemde yalnızca anahtar tarafı değil, sorgu tarafı da düşünülmelidir: dolgu satırlarının çıktısı zaten anlamsızdır ve kayıp hesabında dışlanmalıdır.

Son bölüm, pratikte en sık yapılan hatayı gösterir. Bir sorgu satırının tüm anahtarları maskelenirse, o satırın bütün skorları `−∞` olur. Softmax'ta payda `0` olur ve sonuç `NaN` çıkar. `NaN` bir kez ortaya çıkınca ağın geri kalanına yayılır ve eğitim tek bir adımda çöker. Program bu durumu bilerek kurar: ilk sorgu hiçbir anahtarı göremez. Çıktıda ilk satırın `NaN` olduğunu görürsün. Bu örnekte NumPy, bu satırın hesabında bir `RuntimeWarning` (geçersiz değer) uyarısı da verir; uyarı metni stderr'e gittiği için gösterilen çıktıda yer almıyor. Ayrıca, `−∞` yerine `−10⁹` kullanmak NaN'ı önler ama bu kez sessiz bir hataya yol açar: tüm ağırlıklar eşit (`0,333`) olur ve model fark etmeden anlamsız bir ortalama üretir. Bu yüzden maske satırlarının hiç boş kalmadığını ayrıca denetlemek gerekir. Gerçek kodda, bir sorgu satırının en az bir anahtarı görmesini garanti etmek, dolgu tasarımının bir parçası olmalıdır.

Şekil 69.4, iki maskeyi yan yana gösterir. Sol panel altı belirteçli nedensel maskedir; sağ panel uzunluğu üç olan ve beş konumluk bir dizide dolgu maskesidir.

![Şekil 69.4: Solda nedensel maske: sorgu i yalnızca j ≤ i anahtarlarını görür. Sağda uzunluğu 3 olan diziye 2 dolgu konumu eklenmiş hâl; dolgu anahtarları −∞ alır.](gorseller/b69_maske.png)

## 69.5 Çok başlı attention

Tek başlı attention, bütün ilişkileri tek bir ağırlık dağılımında öğrenmek zorundadır. Oysa bir cümlede farklı türden ilişkiler aynı anda vardır: yakın komşu (sıfat ve isim), uzak eşleşme (zamir ve öncülü), sözdizimi (özne ve fiil). Çok başlı attention (multi-head attention) bu sorunu, `d` boyutlu uzayı `h` paralel alt uzaya bölerek çözer. Her baş kendi `Q`, `K`, `V` dilimleriyle kendi ağırlık matrisini hesaplar. Sonunda başların çıktıları yan yana konur ve bir çıktı projeksiyonundan (`W_O`) geçer.

Matematik şöyledir. Her baş `j` için `d_k = d / h` alınır ve:

`head_j = softmax(Q_j K_jᵀ / √d_k) V_j`, burada `Q_j = Q[:, j·d_k : (j+1)·d_k]` ve benzeri.

Çıktı: `MultiHead = Concat(head_1, …, head_h) W_O`, burada `W_O` bir `d × d` matristir.

Uygulamada bölme için veri kopyalamak gerekmez. `Q`, `T × d` boyutunda bir matrisse, onu `T × h × d_k` olarak yeniden şekillendirip (`view`) sonra `h × T × d_k` olacak biçimde yer değiştirirsin (`transpose`). Bölüm 65'te gördüğün gibi `view` ve `transpose` yalnızca görünümü ve adım bilgisini (stride) değiştirir, veriyi taşımaz. Birleştirme adımında ise `transpose` sonrası bellek düzeni bitişik olmadığı için `reshape` gerektiğinde veriyi kopyalar. Bu kopyalama, çok başlı attention'ın bellek maliyetinde küçük ama gerçek bir paydır.

Aşağıdaki program bu adımları gösterir. Önce `Dikkat` sınıfının bölme davranışını kontrol eder: her başı ayrı ayrı hesaplayıp yan yana koyduğumuzda, toplu hesabın sonucuyla aynı olmalıdır. Sonra kendi gerçeklememizi `nn.MultiheadAttention` ile aynı ağırlıklarla karşılaştırır. Son olarak parametre sayımını formülle doğrular. Bu betik `tr69.py` kütüphanesindeki `Dikkat` ve `Blok` sınıflarını kullanır; kütüphanenin tamamını 69.9'da veriyoruz.

```python
# -*- coding: utf-8 -*-
"""Bölüm 69 - Çok başlı attention: bölme ve parametre."""

import math
import torch
import torch.nn as nn
from tr69 import Dikkat, Blok, tohum

torch.set_default_dtype(torch.float64)

def parametre(modul):
    return sum(p.numel() for p in modul.parameters())
```

```python
def bolme_testi(d=8, h=2, T=3):
    print("--- Bolme ve birlestirme (d=%d, h=%d) ---" % (d, h))
    tohum(0)
    m = Dikkat(d, h)
    x = torch.randn(1, T, d)
    q = m.wq(x)
    bolunmus = m._bol(q)
    print("wq(x)          :", tuple(q.shape))
    print("_bol(wq(x))    :", tuple(bolunmus.shape), "(B, h, T, dh)")
    # Her baş bağımsız hesaplanır, sonra yan yana konur.
    basli = []
    for j in range(h):
        sl = slice(j * m.dh, (j + 1) * m.dh)
        qj, kj, vj = (
            m.wq(x)[..., sl],
            m.wk(x)[..., sl],
            m.wv(x)[..., sl],
        )
        s = qj @ kj.transpose(-2, -1) / math.sqrt(m.dh)
        basli.append(torch.softmax(s, dim=-1) @ vj)
    birlesik = torch.cat(basli, dim=-1)  # (B, T, d)
    tam, _ = m(x, x)
    print(
        "tek tek baslar birlestirilince fark:",
        float(
            (birlesik @ m.wo.weight.T - (tam - m.wo.bias)).abs().max()
        ),
    )
    print("baslarin cikti boyutu:", tuple(birlesik.shape))
```

```python
def torch_eslesme(d=64, h=4, T=7):
    print(
        "--- nn.MultiheadAttention ile ayni agirliklarla eslesme ---"
    )
    tohum(1)
    mine = Dikkat(d, h)
    ref = nn.MultiheadAttention(d, h, batch_first=True)
    with torch.no_grad():
        ref.in_proj_weight.copy_(
            torch.cat(
                [mine.wq.weight, mine.wk.weight, mine.wv.weight]
            )
        )
        ref.in_proj_bias.copy_(
            torch.cat([mine.wq.bias, mine.wk.bias, mine.wv.bias])
        )
        ref.out_proj.weight.copy_(mine.wo.weight)
        ref.out_proj.bias.copy_(mine.wo.bias)
    x = torch.randn(2, T, d)
    m = torch.tril(torch.ones(T, T, dtype=torch.bool))
    a, _ = mine(x, x, m)
    b, _ = ref(x, x, x, attn_mask=~m, need_weights=False)
    print("maks farki (nedensel):", float((a - b).abs().max()))
```

```python
def parametre_sayimi():
    print("--- Parametre sayimi: 4 (d^2 + d) ---")
    for d, h in [(64, 1), (64, 4), (64, 8), (128, 8)]:
        m = Dikkat(d, h)
        print(
            "d=%3d h=%d  gercek=%6d  formul=%6d"
            % (d, h, parametre(m), 4 * (d * d + d))
        )
    print("--- Tam blok (pre-norm, capraz yok), d=64, h=4 ---")
    b = Blok(64, 4, "pre", 0.0, False)
    dikkat = parametre(b.oz)
    mlp = parametre(b.ff)
    norm = parametre(b.ln1) + parametre(b.ln2) + parametre(b.ln3)
    print(
        "dikkat=%d  MLP=%d  LayerNorm=%d  toplam=%d"
        % (dikkat, mlp, norm, parametre(b))
    )

if __name__ == "__main__":
    bolme_testi()
    torch_eslesme()
    parametre_sayimi()
```

Çıktı:

```term
$ python g03_cokbas.py
--- Bolme ve birlestirme (d=8, h=2) ---
wq(x)          : (1, 3, 8)
_bol(wq(x))    : (1, 2, 3, 4) (B, h, T, dh)
tek tek baslar birlestirilince fark: 5.551115123125783e-17
baslarin cikti boyutu: (1, 3, 8)
--- nn.MultiheadAttention ile ayni agirliklarla eslesme ---
maks farki (nedensel): 4.440892098500626e-16
--- Parametre sayimi: 4 (d^2 + d) ---
d= 64 h=1  gercek= 16640  formul= 16640
d= 64 h=4  gercek= 16640  formul= 16640
d= 64 h=8  gercek= 16640  formul= 16640
d=128 h=8  gercek= 66048  formul= 66048
--- Tam blok (pre-norm, capraz yok), d=64, h=4 ---
dikkat=16640  MLP=33088  LayerNorm=384  toplam=50112
```

Çıktı üç şeyi gösterir. Birincisi şekiller: `wq(x)` `(1, 3, 8)`dir, bölünce `(1, 2, 3, 4)` olur. Bu, `(B, h, T, d_k)` düzenidir ve `h` başın her birinin kendi `T × d_k` matrisini taşıdığını gösterir. İkincisi, başları ayrı ayrı hesaplayıp birleştirdiğimizde fark `5,6·10⁻¹⁷` çıkar; yani bölme doğru. Üçüncüsü, nedensel maskeli eşleşmede fark `4,4·10⁻¹⁶`dır. Bu da bizim gerçeklememizin `nn.MultiheadAttention` ile aynı sonucu verdiğini gösterir.

Parametre sayımı daha önemli bir noktayı öğretir. `d = 64` ve `h = 1, 4, 8` için parametre sayısı aynı, `16 640`tır. Formül `4(d² + d)`dir: dört projeksiyon (`W_Q`, `W_K`, `W_V`, `W_O`) her biri `d × d` ağırlık ve `d` sapma taşır. Başların sayısı parametre sayısını değiştirmez; yalnızca her başın boyutunu (`d_k = d/h`) değiştirir. Yani çok başlı attention, tek başlıya göre hem daha zengin bir ilişki kümesi öğrenir hem de aynı parametre bütçesini kullanır.

Bu betik ayrıca tek bir Transformer bloğunun parametrelerini ayırır: dikkat 16 640, MLP 33 088, üç LayerNorm 384, toplam 50 112. Dikkat ve MLP parametreleri birlikte blokun büyük kısmını oluşturur. Bu oranın nedenini 69.7'de göreceksin.

Şekil 69.5, bölme ve birleştirmeyi tek bakışta gösterir.

![Şekil 69.5: Çok başlı attention: X, h = 4 başa bölünür (her baş d/h boyutlu Q, K, V dilimleriyle çalışır). Başların çıktıları birleştirilir ve W_O ile T × d çıktıya dönüştürülür.](gorseller/b69_cok_bas.png)

Bir ayrıntı için mülakat cevabı hazırla: çok başlı attention'da başlar neden birbirinden bağımsız olur? Çünkü her başın kendi projeksiyonları (`W_Q^j`, `W_K^j`, `W_V^j`) vardır ve softmax başlar arasında paylaşılmaz. Başlar arasındaki tek bağlantı, son `W_O` projeksiyonudur. Başların gerçekten farklı desenler öğrendiğini 69.9'da, eğitilmiş bir modelin başlarını karşılaştırarak göstereceğiz.

## 69.6 Konumsal kodlama: attention neden sırayı bilmez?

Attention'ın formülünde belirteçlerin sırasını gösteren hiçbir şey yoktur. `QKᵀ`, `softmax` ve `AV` işlemleri, satırların yerleri değişse de aynı şekilde karışır. Bunu matematiksel olarak söylemek için bir permütasyon matrisi `P` düşün: `(PQ)(PK)ᵀ = P(QKᵀ)Pᵀ` ve softmax satır bazında çalıştığı için `softmax(PSPᵀ) = P softmax(S) Pᵀ`. Sonuçta `Attention(PX) = P · Attention(X)` olur. Buna permütasyon eşdeğişkenliği denir. Yani attention, belirteçleri bir torba (bag) gibi görür; "köpek kediyi kovaladı" ile "kedi köpeği kovaladı" aynı belirteç kümesidir ve aynı değerleri üretir.

Dil için bu kabul edilemez. Sıra anlamı taşır. Konumsal kodlama, sırayı girdiye ekleyerek bu sorunu çözer. Program, bu eşdeğişkenliği sayıyla doğrular ve sonra konum kodlamasının etkisini ölçer. Önce rastgele bir girdi için belirteç gömmelerini permüte edip çıktıyı permütasyonla karşılaştırır. Sonra aynı belirteçleri, konum kodlaması eklenmiş hâlde, ama konum kodunu yerinde tutarak karıştırır. Ayrıca programda sinüzoidal kodlamanın komşu konumlar arasındaki benzerliği ve RoPE'nin göreli konuma bağlılığı test edilir.

```python
# -*- coding: utf-8 -*-
"""Bölüm 69 - Konumsal kodlama: permütasyon, sinüzoidal, RoPE."""

import csv
import os
import torch
from tr69 import Dikkat, rotasyon, sinuzoidal, tohum

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
torch.set_default_dtype(torch.float64)

def permutasyon_testi(T=6, d=8):
    print("--- Permütasyon eşdeğişkenliği ---")
    tohum(0)
    m = Dikkat(d, 2)
    x = torch.randn(1, T, d)
    p = torch.tensor([3, 0, 5, 1, 4, 2])
    y, _ = m(x, x)
    yp, _ = m(x[:, p], x[:, p])
    print(
        "cikti(x[p]) - cikti(x)[p] :",
        float((yp - y[:, p]).abs().max()),
    )
    pe = sinuzoidal(T, d).double()
    y2, _ = m(x + pe, x + pe)  # konum eklendi
    # belirteçler karıştı, konum kodu yerinde kaldı
    yp2, _ = m(x[:, p] + pe, x[:, p] + pe)
    print(
        "konumlu, fark             :",
        float((yp2 - y2[:, p]).abs().max()),
    )
```

```python
def sinuzoidal_tablo(T=32, d=32):
    print("--- Sinüzoidal kodlama: komşu konum benzerliği ---")
    pe = sinuzoidal(T, d).double()
    for k in [0, 1, 2, 4, 8]:
        benz = float((pe[0] @ pe[k]) / (pe[0].norm() * pe[k].norm()))
        print("konum 0 ile %2d arasinda kosinus: %.4f" % (k, benz))
    with open(
        os.path.join(VERI, "b69_pe.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerows(
            [["%.6f" % v for v in satir] for satir in pe.tolist()]
        )

def rope_testi(T=12, dh=8):
    print("--- RoPE: skor yalnızca göreli konuma mı bağlı? ---")
    tohum(1)
    qv = torch.randn(dh)
    kv = torch.randn(dh)
    q = rotasyon(qv.expand(1, 1, T, dh).clone())
    k = rotasyon(kv.expand(1, 1, T, dh).clone())
    for m, n in [(5, 2), (9, 6), (11, 8), (3, 0), (11, 0)]:
        print(
            "m=%2d n=%2d  m-n=%2d  skor=%.6f"
            % (m, n, m - n, float(q[0, 0, m] @ k[0, 0, n]))
        )
    ham = float(qv @ kv)
    print("dönmemiş q.k =", round(ham, 6))

if __name__ == "__main__":
    permutasyon_testi()
    sinuzoidal_tablo()
    rope_testi()
```

Çıktı:

```term
$ python g04_konum.py
--- Permütasyon eşdeğişkenliği ---
cikti(x[p]) - cikti(x)[p] : 1.6653345369377348e-16
konumlu, fark             : 0.05789544177741068
--- Sinüzoidal kodlama: komşu konum benzerliği ---
konum 0 ile  0 arasinda kosinus: 1.0000
konum 0 ile  1 arasinda kosinus: 0.9571
konum 0 ile  2 arasinda kosinus: 0.8581
konum 0 ile  4 arasinda kosinus: 0.7288
konum 0 ile  8 arasinda kosinus: 0.6576
--- RoPE: skor yalnızca göreli konuma mı bağlı? ---
m= 5 n= 2  m-n= 3  skor=0.601243
m= 9 n= 6  m-n= 3  skor=0.601243
m=11 n= 8  m-n= 3  skor=0.601243
m= 3 n= 0  m-n= 3  skor=0.601243
m=11 n= 0  m-n=11  skor=0.288089
dönmemiş q.k = -1.213566
```

İlk satır eşdeğişkenliği gösterir: konum bilgisi yokken girdiyi permüte edip çıktıyı permüte etmek ile önce hesaplayıp sonra permüte etmek arasındaki fark `1,7·10⁻¹⁶`dır. Attention, konumdan habersizdir. İkinci satırda ise konum kodu yerinde tutulup belirteçler karıştırıldığında çıktı, permütasyonun öngördüğünden `0,058` kadar sapar. Yani konum kodlaması eklendiğinde model sırayı görmeye başlar. Bu sayının büyüklüğü rastgele ağırlıklara ve kodlamanın ölçeğine bağlıdır; burada değerin yönünü ölçüyoruz, büyüklüğünü değil. Konum kodlamasının *gerekli* olduğunu, konumsuz modelin ters çevirme görevinde nasıl başarısız olduğunu 69.9'da ayrıca göreceğiz.

**Sinüzoidal kodlama (Vaswani ve arkadaşları, 2017).** Her konum `t` için `d` boyutlu bir vektör üretilir:

`PE(t, 2i) = sin(t / 10000^{2i/d})`, `PE(t, 2i+1) = cos(t / 10000^{2i/d})`.

Her çift `(2i, 2i+1)` farklı bir frekansa sahiptir. Frekanslar `1`den `1/10000`e kadar geometrik olarak düşer. Düşük boyutlar hızlı salınır ve kısa mesafeleri ayırt eder; yüksek boyutlar yavaş salınır ve uzun mesafeleri ayırt eder. Önemli bir özellik şudur: `PE(t + k)`, `PE(t)`nin sabit bir doğrusal dönüşümüdür. Bu, `sin(a + b)` ve `cos(a + b)` toplam formüllerinden çıkar: her çift, `k`ye bağlı bir dönme matrisiyle dönüşür. Dolayısıyla model, göreli bir kaydırmayı öğrenmek için yalnızca bir doğrusal işleme ihtiyaç duyar.

Komşu konumların benzerliği programın ikinci bölümünde ölçülüyor. Konum `0` ile konum `1` arasındaki kosinüs benzerliği `0,9571`, `2` için `0,8581`, `4` için `0,7288`, `8` için `0,6576`dır. Benzerlik uzaklıkla azalır, ama bu azalma tek düze ve kesin olmak zorunda değildir; ölçtüğümüz dizi için böyle çıkıyor. Şekil 69.6 bu kodlamanın tamamını gösterir: her satır bir konum, her sütun bir boyut.

![Şekil 69.6: Sinüzoidal konum kodlaması PE(t, i), t = 0…31, i = 0…31. Düşük boyutlar hızlı, yüksek boyutlar yavaş salınır; her satır bir konumun parmak izidir.](gorseller/b69_konum_isi.png)

**Öğrenilen konum gömmeleri.** BERT ve GPT-2 gibi birçok model, konumlar için bir gömme tablosu (`maxT × d`) tanımlar ve bunu eğitimde öğrenir. Bu yöntem basit ve esnektir; ama tanımlı en büyük konumun ötesine geçemez. Tablonun `maxT` üstündeki satırları yoktur. Ayrıca eğitimde hiç görülmemiş konumların satırları rastgele kalır. Bu, uzunluk genellemesi sorununun doğrudan kaynağıdır ve 69.9'da ölçeceğiz.

**RoPE: döner konum gömmesi (Su ve arkadaşları, 2021).** Sinüzoidal kodlama konumu girdiye ekler. RoPE ise konumu sorguya ve anahtara, attention'ın içinde, dönme olarak uygular. `q` ve `k` vektörlerinin `(x_{2i}, x_{2i+1})` çiftleri, konuma bağlı bir açı kadar döndürülür: açı `m · θ_i` ve `θ_i = 10000^{−2i/d}`. Bu durumda `m`. konumdaki sorgunun `n`. konumdaki anahtarla skoru yalnızca göreli konuma bağlıdır:

`(R_m q)ᵀ (R_n k) = qᵀ R_{n−m} k`.

Yani mutlak konumlar değil, aradaki fark belirleyicidir. Kodda `rotasyon` fonksiyonu bunu uygular ve `g04` programı bunu sayıyla gösterir. Aynı `q` ve `k` vektörleri için `(5,2)`, `(9,6)`, `(11,8)` ve `(3,0)` konum çiftlerinin skoru, hepsi farkı `3` olduğu için `0,601243`tür. Farkı `11` olan `(11,0)` çifti ise `0,288089` verir. RoPE, V vektörlerine uygulanmaz; yalnızca Q ve K'ya uygulanır. Bu yöntem, bugünkü birçok büyük dil modelinde standarttır (genel bilgi).

**ALiBi (Press ve arkadaşları, 2021, genel bilgi).** Bu yöntem konum kodlamasını tamamen kaldırır ve skora, konumlar arası uzaklıkla orantılı bir ceza ekler. Eğitimde görülmeyen uzunluklara genelleme iddiasıyla kullanılır. Bu bölümde gerçekleştirmiyoruz; yalnızca yaklaşımın varlığını bilmen yeterli.

Bu dört yöntemin ortak özelliği, konumu modelin *öğrenebileceği* bir biçimde sunmalarıdır. Sinüzoidal ve öğrenilen yöntemler konumu girdiye ekler; RoPE ve ALiBi ise konum bilgisini doğrudan attention skorlarına karıştırır. Hangi yöntemin neden tercih edildiğini, uzunluk genellemesi deneyinin sonuçlarıyla birlikte değerlendireceğiz.

## 69.7 Transformer bloğu: artık, LayerNorm ve MLP

Attention tek başına bir katmandır; bir Transformer ise birçok bloğun üst üste konmasıyla oluşur. Her blok üç parçadan oluşur: çok başlı attention, bir ileri beslemeli ağ (MLP) ve bunları bağlayan artık bağlantılar ile LayerNorm. Bölüm 64.9'da artık bağlantının neden derin ağları eğitilebilir yaptığını gördün. Bölüm 64.7'de LayerNorm'u tanıdın ve burada onun Transformer'daki yerini göreceksin.

Blok, iki alt katmandan oluşur. İlk alt katmanda attention, ikincisinde MLP çalışır. Her ikisinin çevresinde artık bağlantı vardır. Bu iki alt katman birlikte şu iki satırda ifade edilir (pre-norm biçiminde):

`y = x + Attention(LN₁(x))`
`z = y + MLP(LN₂(y))`

MLP, iki doğrusal katman arasında GELU etkinleştirme taşır: `Linear(d, 4d) → GELU → Linear(4d, d)`. Genişletme oranı 4 standarttır. Bu genişleme, attention'ın yaptığı karıştırmadan sonra her belirteç üzerinde doğrusal olmayan bir dönüşüm yapar. Attention bilgiyi konumlar arasında taşır; MLP ise her konumun kendi bilgisini işler. Parametre sayısında MLP, attention'dan büyüktür (`8d²` ve `4d²`ye karşılık; blokun toplamı `12d²` mertebesindedir). Bu, 69.5'te gördüğün 33 088 ve 16 640 sayılarının nedenidir.

LayerNorm, Bölüm 64.7'deki gibi bir örneğin özellikleri üzerinden normalize eder; batch boyutundan bağımsızdır. Transformer'da BatchNorm yerine LayerNorm tercih edilmesinin üç nedeni vardır. Dizi uzunlukları değişkendir ve dolgu konumları batch istatistiklerini bozar. Çıkarımda batch boyutu genellikle 1'dir ve BatchNorm'un eğitimde biriktirdiği istatistikler anlamsızdır. Ayrıca LayerNorm her belirtecin kendi vektörünü normalize eder; bu, belirteçler arasında ölçek farkı yaratmaz.

**Pre-norm ve post-norm.** Özgün makalede LayerNorm, artık toplamından sonra gelir: `x → x + F(x) → LN`. Buna post-norm denir. Bugünkü çoğu model pre-norm kullanır: `x → LN → F → + x`. Fark yalnızca bir sıra değişikliği gibi görünür, ama eğitim davranışını değiştirir. Post-norm'da artık yol `LN`den geçer; derin ağda gradyan her katmanda bir normalizasyondan geçerek küçülüp büyüyebilir. Pre-norm'da ise artık yol hiçbir işlemden geçmez: `∂z/∂x = I + (...)` olduğu için gradyan, `I` terimi sayesinde doğrudan geriye akar. Bu nedenle pre-norm daha kararlıdır ve genellikle warmup'a daha az ihtiyaç duyar. Bu iddiayı bu bölümde ölçülebilir hâle getirmek için 69.10'da post-norm ile pre-norm'u, warmup'lı ve warmup'sız olarak eğitip karşılaştırıyoruz.

Şekil 69.7, iki sıralamayı yan yana gösterir. Bordo çizgiler artık yollarıdır.

![Şekil 69.7: Solda post-norm: artık toplamından sonra LayerNorm. Sağda pre-norm: LayerNorm dalın içinde, artık yol temiz. Bordo çizgi, toplamaya giden artık yoludur.](gorseller/b69_pre_post.png)

Dropout, Bölüm 64.8'de gördüğün gibi düzenlileştirme için kullanılır. Transformer'da dropout genellikle iki yere konur: attention çıktısının ve MLP çıktısının artığa eklenmeden önce. Attention ağırlıklarına da dropout uygulanabilir; bizim `tr69.py` kütüphanesinde bu yoktur, yalnızca blok çıktısında vardır. Eğitim ve çıkarım modları arasındaki fark, `model.eval()` çağrısıyla yönetilir (Bölüm 65'te).

## 69.8 Encoder, decoder ve üç aile

Transformer bloğunu tanıdın. Şimdi bu blokların nasıl bir araya geldiğine bakalım. Bloklar üç farklı düzende kullanılır ve bu düzenler, bugünkü modellerin büyük kısmını üç aileye ayırır. Aile seçimi, maskenin nerede olacağını, eğitim görevini ve modelin ne için kullanılacağını birlikte belirler.

| Aile | Maske | Eğitim görevi | Tipik kullanım |
|---|---|---|---|
| Yalnızca encoder (BERT tarzı) | Yok: her belirteç her belirteci görür | Maskelenmiş belirteci tahmin et | Sınıflandırma, arama, gömme |
| Yalnızca decoder (GPT tarzı) | Nedensel: yalnızca geçmişi görür | Sonraki belirteci tahmin et | Metin üretimi, sohbet, dil modeli |
| Encoder–decoder (özgün Transformer, T5 tarzı) | Encoder: yok; decoder: nedensel + çapraz | Girdiyi çıktı dizisine dönüştür | Çeviri, özetleme, dizi dönüşümü |

Yalnızca encoder modelleri, girdinin tamamını iki yönlü okur. Bir cümlenin bir kelimesini maskeleyip çevresinden tahmin ettirmek, bu tür bir ön eğitimin temelidir. Bu model çıktısında her belirtecin kendi bağlamla zenginleşmiş bir vektörü olur ve bu vektörler sınıflandırma ya da arama için kullanılır. Bölüm 70'te, bir metin temsilinin nasıl ön eğitildiğini ve ince ayarlandığını göreceksin. Yalnızca decoder modelleri, her adımda yalnızca geçmişi görür. Bu, bir sonraki belirteci tahmin eden dil modelinin doğal yapısıdır ve Bölüm 70 ile 71'in ana konusudur. Encoder–decoder modeller ise iki dizinin bir araya geldiği görevlerde doğaldır: kaynak dili oku, hedef dili üret.

Encoder–decoder yapısında bağlantı çapraz dikkat (cross-attention) ile kurulur. Decoder bloğu üç alt katman taşır: önce nedensel öz-dikkat, sonra çapraz dikkat, en sonunda MLP. Çapraz dikkatte sorgu (`Q`) decoder'ın o anki durumundan gelir; anahtar (`K`) ve değer (`V`) ise encoder'ın son çıktısından. Böylece decoder her adımda, kaynak dizinin bütün konumlarına bakarak hangisinin o adımda gerekli olduğunu seçer. Bu, Bölüm 68'deki tek bağlam vektörünün yerini alır. Bağlam artık her adımda yeniden kurulur ve kaynağın hiçbir konumu kaybolmaz.

Maske kuralı bu yapıda iki tarafta farklıdır. Encoder'ın kaynak tarafı yalnızca dolgu için maskelenir; hedef dizisinin geleceği zaten yoktur. Decoder'ın öz-dikkat katmanı nedenseldir: çıktının gelecekteki belirteçlerini görmemelidir. Çapraz dikkatte ise decoder adımı, kaynağın tamamına bakabilir; kaynak dizi bilinen bir girdidir, gelecek değildir. Bu ayrım, 69.4'te gördüğün iki maske türünün ikisini de bir arada kullanmak demektir.

Encoder–decoder modelinin kodlaması `tr69.py` kütüphanesinde `Model(cift=True)` ile yapılır: encoder blokları maskesiz çalışır, decoder blokları ise `capraz=True` ile kurulur. Decoder-only modelde ise `cift=False` olur ve decoder bloklarında çapraz dikkat yoktur. Aynı `Blok` sınıfının iki kullanımı, yapının ne kadar tekdüze olduğunu gösterir: fark yalnızca hangi alt katmanların ve maskelerin kurulduğudur.

Bu üç ailenin tek bir kuralla özetlenebileceğini düşünebilirsin: maske, belirteçlerin neyi görebileceğini belirler; görev ise modelin neyi öğreneceğini. Bu bölümde iki aileyi uygulayacağız. Ters çevirme görevinde encoder–decoder, karakter düzeyi dil modelinde ise decoder-only yapısını kuracağız. Encoder-only aileyi görüntü tarafında ViT ile ele alacağız; ViT, yamaları bir "belirteç dizisi" gibi işleyen bir encoder'dır.

## 69.9 Sıfırdan Transformer: dizi ters çevirme

Şimdiye kadar parçaları ayrı ayrı yazdın ve test ettin. Şimdi bunları bir araya getirip uçtan uca çalışan bir encoder–decoder modeli kuracağız. Görev, bir dizinin tersini üretmek: girdi `a b c d` ise çıktı `d c b a`. Görev basit görünür, ama iki şeyi zorlar. Birincisi, decoder'ın her adımda kaynağın doğru konumuna bakması gerekir; yani çapraz dikkatin gerçekten doğru konumu öğrenmesi gerekir. İkincisi, kaynak dizi uzadıkça modelin konumsal bilgiye ihtiyacı artar; çünkü ters çevirmek, her belirtecin nerede olduğunu bilmek demektir.

Görevin tanımı önemlidir. Sözlükte 13 sembol vardır (`3`–`15`), iki özel belirteç vardır: `BOS = 1` decoder'ın başlangıcı, `EOS = 2` çıktının sonu. Eğitimde her batch aynı uzunluğa sahiptir ve uzunluk `4` ile `12` arasından rastgele seçilir; böylece dolgu gerekmez. Decoder girdisi `BOS` ile başlar ve ters diziyi izler; hedef ise ters dizinin sonuna `EOS` eklenmiş hâlidir. Bu, teacher forcing'in (Bölüm 68) doğrudan bir uygulamasıdır: decoder eğitimde gerçek önceki belirteci görür.

Bu deneyde dört konum kodlaması karşılaştırıyoruz: sinüzoidal, öğrenilen, RoPE ve hiçbiri (konumsuz). Ayrıca Bölüm 68'deki tipte bir LSTM encoder–decoder taban çizgisi koyuyoruz. Bu taban çizgisi, Bölüm 68 ile aynı mimari ailesinden olan, dikkatsiz bir LSTM'dir: encoder son durumunu tek bir vektör olarak decoder'a verir. Bu, 69.1'de anlattığımız darboğazın ölçüsüdür. Her yöntem üç tohumla eğitilir. Eğitim 2 000 adım sürer, öğrenme oranı ilk 100 adımda doğrusal artar ve sonra sabit kalır. Test, eğitim aralığının içinde (4, 8, 12) ve dışında (16, 20, 24) uzunluklarda yapılır. Doğruluk, dizi düzeyindedir: tahmin edilen tüm belirteçler (EOS dahil) doğru olmalıdır.

Aşağıda kütüphanemizin tamamı yer alıyor. Bu betik ve sonraki deneyler `tr69.py` dosyasını içe aktarır; dosyayı kitapta tam olarak veriyoruz.

```python
# -*- coding: utf-8 -*-
"""Bölüm 69 ortak kütüphanesi: attention, blok, Transformer.

nn.Transformer ya da nn.MultiheadAttention KULLANILMAZ. Tüm
projeksiyonlar, bölmeler, maskeler ve konum kodlamaları buradadır.
"""

import math
import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""  # bu bölümde yalnızca CPU

import numpy as np
import torch
import torch.nn as nn

def tohum(s):
    np.random.seed(s)
    torch.manual_seed(s)

def sinuzoidal(T, d):
    """Vaswani 2017 sinüzoidal konum kodlaması, (T, d) boyutlu."""
    poz = np.arange(T)[:, None]
    i = np.arange(d // 2)[None, :]
    aci = poz / (10000.0 ** (2 * i / d))
    pe = np.zeros((T, d))
    pe[:, 0::2] = np.sin(aci)
    pe[:, 1::2] = np.cos(aci)
    return torch.tensor(pe, dtype=torch.float32)

def rotasyon(x, taban=10000.0):
    """RoPE: (x_2i, x_2i+1) çiftleri konuma göre döndürülür.
```

```python
    x boyutu (B, h, T, dh). Çiftler birbirine komşu indekslerdir.
    """
    T, dh = x.shape[-2], x.shape[-1]
    i = torch.arange(dh // 2, dtype=x.dtype)
    teta = taban ** (-2 * i / dh)
    aci = torch.arange(T, dtype=x.dtype)[:, None] * teta[None, :]
    c, s = torch.cos(aci), torch.sin(aci)
    x1, x2 = x[..., 0::2], x[..., 1::2]
    o1 = x1 * c - x2 * s
    o2 = x1 * s + x2 * c
    return torch.stack([o1, o2], dim=-1).flatten(-2)

class Dikkat(nn.Module):
    """Çok başlı ölçekli nokta çarpımı attention."""

    def __init__(self, d, h):
        super().__init__()
        assert d % h == 0
        self.h, self.dh = h, d // h
        self.wq = nn.Linear(d, d)
        self.wk = nn.Linear(d, d)
        self.wv = nn.Linear(d, d)
        self.wo = nn.Linear(d, d)
        self.son_A = None

    def _bol(self, z):
        """(B, T, d) -> (B, h, T, dh): başlara bölme."""
        B, T, _ = z.shape
        return z.view(B, T, self.h, self.dh).transpose(1, 2)
```

```python
    def forward(self, xq, xkv, maske=None, rope=False):
        B, T, d = xq.shape
        q = self._bol(self.wq(xq))
        k = self._bol(self.wk(xkv))
        v = self._bol(self.wv(xkv))
        if rope:
            q, k = rotasyon(q), rotasyon(k)
        s = q @ k.transpose(-2, -1) / math.sqrt(self.dh)
        if maske is not None:
            s = s.masked_fill(~maske, float("-inf"))
        A = torch.softmax(s, dim=-1)
        o = (A @ v).transpose(1, 2).reshape(B, T, d)  # birleştir
        self.son_A = A.detach()
        return self.wo(o), A

class Blok(nn.Module):
    """Transformer bloğu: attention, (varsa) çapraz attention, MLP."""

    def __init__(self, d, h, norm, drop, capraz):
        super().__init__()
        self.norm = norm
        self.oz = Dikkat(d, h)
        self.ln1 = nn.LayerNorm(d)
        self.capraz = Dikkat(d, h) if capraz else None
        self.ln2 = nn.LayerNorm(d)
        self.ff = nn.Sequential(
            nn.Linear(d, 4 * d), nn.GELU(), nn.Linear(4 * d, d)
        )
        self.ln3 = nn.LayerNorm(d)
        self.drop = nn.Dropout(drop)
```

```python
    def forward(self, x, enc=None, maske=None, rope=False):
        if self.norm == "pre":
            h = self.ln1(x)
            x = x + self.drop(self.oz(h, h, maske, rope)[0])
            if self.capraz is not None:
                x = x + self.drop(self.capraz(self.ln2(x), enc)[0])
            x = x + self.drop(self.ff(self.ln3(x)))
        else:  # post-norm: artık, sonra LayerNorm
            x = self.ln1(x + self.drop(self.oz(x, x, maske, rope)[0]))
            if self.capraz is not None:
                x = self.ln2(x + self.drop(self.capraz(x, enc)[0]))
            x = self.ln3(x + self.drop(self.ff(x)))
        return x

class Model(nn.Module):
    """Encoder-decoder (cift=True) ya da yalnız decoder."""
```

```python
    def __init__(
        self,
        V,
        d=64,
        h=4,
        L=2,
        maxT=32,
        konum="sin",
        norm="pre",
        cift=False,
        drop=0.0,
    ):
        super().__init__()
        self.konum, self.norm, self.cift = konum, norm, cift
        self.emb = nn.Embedding(V, d)
        if konum == "sin":
            self.register_buffer("pe", sinuzoidal(maxT, d))
        if konum == "ogr":
            self.pos = nn.Embedding(maxT, d)
        if cift:
            self.enc = nn.ModuleList(
                [Blok(d, h, norm, drop, False) for _ in range(L)]
            )
            self.enc_son = (
                nn.LayerNorm(d) if norm == "pre" else nn.Identity()
            )
        self.dec = nn.ModuleList(
            [Blok(d, h, norm, drop, cift) for _ in range(L)]
        )
        self.dec_son = (
            nn.LayerNorm(d) if norm == "pre" else nn.Identity()
        )
        self.cikis = nn.Linear(d, V)
```

```python
    def _konum(self, h):
        T = h.shape[1]
        if self.konum == "sin":
            return h + self.pe[:T]
        if self.konum == "ogr":
            return h + self.pos(torch.arange(T))
        return h  # "rope" ve "yok": eklenmez

    def kodla(self, src):
        h = self._konum(self.emb(src))
        for b in self.enc:  # maske yok: çift yönlü
            h = b(h, rope=self.konum == "rope")
        return self.enc_son(h)

    def forward(self, x, src=None):
        T = x.shape[1]
        maske = torch.tril(torch.ones(T, T, dtype=torch.bool))
        enc = self.kodla(src) if self.cift else None
        h = self._konum(self.emb(x))
        for b in self.dec:  # nedensel maske
            h = b(h, enc=enc, maske=maske, rope=self.konum == "rope")
        return self.cikis(self.dec_son(h))

@torch.no_grad()
def greedy_seq2seq(model, src, n_out, bos=1):
    """Açgözlü (greedy) çözme: her adımda en olası belirteci seç."""
    model.eval()
    ys = torch.full((src.shape[0], 1), bos, dtype=torch.long)
    for _ in range(n_out):
        logits = model(ys, src)
        ys = torch.cat([ys, logits[:, -1:].argmax(-1)], dim=1)
    return ys[:, 1:]
```

Ters çevirme deneyi aşağıda. Bu betik dört Transformer ve bir LSTM'i üç tohumla eğitir, dizi düzeyindeki doğruluğu ölçer, parametre sayılarını ve sürelerini raporlar, sonra eğitilmiş bir modelden çapraz dikkat ağırlıklarını ve baş istatistiklerini çıkarır. Program CPU'da çalışır ve GPU'ya dokunmaz.

```python
# -*- coding: utf-8 -*-
"""Bölüm 69 - Dizi ters çevirme: Transformer konum türleri ve LSTM."""

import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tr69 import Model, greedy_seq2seq, tohum

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
V, BOS, EOS = 16, 1, 2  # 3..15 arasi semboller
ADIM = 2000
EGITIM_L = (4, 12)  # egitimde uzunluk 4..12
TEST_L = [4, 8, 12, 16, 20, 24]  # 13 ve sonrasi: egitim disi
TOHUMLAR = [0, 1, 2]

class LSTMAy(nn.Module):
    """Bölüm 68'deki tipte LSTM encoder-decoder (dikkatsiz)."""

    def __init__(self, d=64, hid=128):
        super().__init__()
        self.emb = nn.Embedding(V, d)
        self.enc = nn.LSTM(d, hid, batch_first=True)
        self.dec = nn.LSTM(d, hid, batch_first=True)
        self.cikis = nn.Linear(hid, V)

    def forward(self, x, src):
        _, durum = self.enc(self.emb(src))  # sabit boyutlu bağlam
        h, _ = self.dec(self.emb(x), durum)
        return self.cikis(h)
```

```python
def grup(rng, L, n):
    src = rng.integers(3, V, size=(n, L))
    tin = np.concatenate([np.full((n, 1), BOS), src[:, ::-1]], axis=1)
    tout = np.concatenate(
        [src[:, ::-1], np.full((n, 1), EOS)], axis=1
    )
    return (torch.tensor(src), torch.tensor(tin), torch.tensor(tout))

def egit(model, rng):
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    # ilk 100 adımda öğrenme oranı doğrusal artar, sonra sabit kalır
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda a: min(1.0, (a + 1) / 100)
    )
    for _ in range(ADIM):
        L = int(rng.integers(EGITIM_L[0], EGITIM_L[1] + 1))
        src, tin, tout = grup(rng, L, 64)
        model.train()
        logits = model(tin, src)
        loss = F.cross_entropy(
            logits.reshape(-1, V), tout.reshape(-1)
        )
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
    return float(loss)

def dogruluk(model, L, n=300):
    """Dizi düzeyi doğruluk: EOS dahil tüm belirteçler doğru mu?"""
    src, _, tout = grup(np.random.default_rng(1000 + L), L, n)
    tahmin = greedy_seq2seq(model, src, L + 1)
    return float((tahmin == tout).all(dim=1).float().mean())
```

```python
def dikkat_analizi(model, L=10, n=200):
    """Başlar ne yapıyor? Önceki belirteç, kendisi ve ters köşegen."""
    src, tin, _ = grup(np.random.default_rng(7), L, n)
    model.eval()
    with torch.no_grad():
        model(tin, src)
    A_enc = model.enc[0].oz.son_A  # (B, h, L, L)
    A_cap = model.dec[-1].capraz.son_A  # (B, h, L+1, L)
    print("baş | enc:önceki | enc:kendisi | çapraz:ters köşegen")
    for h in range(A_enc.shape[1]):
        onceki = float(A_enc[:, h, 1:, :].diagonal(-1, -2, -1).mean())
        kendi = float(A_enc[:, h].diagonal(0, -2, -1).mean())
        ters = float(
            torch.stack(
                [A_cap[:, h, t, L - 1 - t] for t in range(L)]
            ).mean()
        )
        print(
            "%3d | %11.3f | %11.3f | %19.3f"
            % (h, onceki, kendi, ters)
        )
    satirlar = []
    for h in range(A_cap.shape[1]):
        for t in range(A_cap.shape[2]):
            for j in range(L):
                satirlar.append(
                    [h, t, j, "%.4f" % float(A_cap[0, h, t, j])]
                )
    with open(
        os.path.join(VERI, "b69_attn_ters.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["bas", "satir", "sutun", "agirlik"])
        w.writerows(satirlar)
```

```python
def main():
    sonuc = {}
    parametre = {}
    sure = {}
    modeller = {}
    konfig = {
        "Transformer sinüzoidal": dict(konum="sin"),
        "Transformer öğrenilen": dict(konum="ogr"),
        "Transformer RoPE": dict(konum="rope"),
        "Transformer konumsuz": dict(konum="yok"),
    }
    for ad, kw in list(konfig.items()) + [("LSTM (dikkatsiz)", None)]:
        sonuc[ad] = {L: [] for L in TEST_L}
        sure[ad] = []
        for s in TOHUMLAR:
            tohum(s)
            if kw is None:
                model = LSTMAy()
            else:
                model = Model(
                    V,
                    d=64,
                    h=4,
                    L=2,
                    maxT=32,
                    cift=True,
                    norm="pre",
                    **kw
                )
            parametre[ad] = sum(p.numel() for p in model.parameters())
            t0 = time.time()
            son = egit(model, np.random.default_rng(s))
            sure[ad].append(time.time() - t0)
            for L in TEST_L:
                sonuc[ad][L].append(dogruluk(model, L))
            print(
                "%-24s tohum=%d son_kayip=%.4f sure=%.0fs"
                % (ad, s, son, sure[ad][-1])
            )
            if s == 0 and kw is not None and kw["konum"] == "sin":
```

```python
                modeller["sin"] = model
    print()
    print("Parametre sayisi ve sure ortalamasi:")
    for ad in sonuc:
        print(
            "%-24s %7d  %5.0fs"
            % (ad, parametre[ad], np.mean(sure[ad]))
        )
    print()
    print("Dizi düzeyi doğruluk (ortalama±sapma, 3 tohum)")
    kisa = ["sin", "ogr", "RoPE", "yok", "LSTM"]
    print("L    " + " ".join("%-11s" % k for k in kisa))
    satirlar = []
    for L in TEST_L:
        hucre = []
        for ad in sonuc:
            v = np.array(sonuc[ad][L])
            hucre.append("%.3f±%.3f" % (v.mean(), v.std(ddof=1)))
            satirlar.append(
                [ad, L, "%.4f" % v.mean(), "%.4f" % v.std(ddof=1)]
            )
        print("%-4d " % L + " ".join("%-11s" % h for h in hucre))
    with open(
        os.path.join(VERI, "b69_uzunluk.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["model", "L", "ortalama", "sapma"])
        w.writerows(satirlar)
    print()
    print("Dikkat analizi (sinüzoidal, tohum 0, L=10):")
    dikkat_analizi(modeller["sin"])
```

```python
if __name__ == "__main__":
    main()
```

Çıktı:

```term
$ python g06_ters.py
Transformer sinüzoidal   tohum=0 son_kayip=0.0007 sure=58s
Transformer sinüzoidal   tohum=1 son_kayip=0.0002 sure=56s
Transformer sinüzoidal   tohum=2 son_kayip=0.0284 sure=60s
Transformer öğrenilen    tohum=0 son_kayip=0.0002 sure=60s
Transformer öğrenilen    tohum=1 son_kayip=0.0002 sure=57s
Transformer öğrenilen    tohum=2 son_kayip=0.0005 sure=50s
Transformer RoPE         tohum=0 son_kayip=0.0174 sure=65s
Transformer RoPE         tohum=1 son_kayip=0.0021 sure=66s
Transformer RoPE         tohum=2 son_kayip=0.0377 sure=64s
Transformer konumsuz     tohum=0 son_kayip=0.8824 sure=62s
Transformer konumsuz     tohum=1 son_kayip=0.8902 sure=55s
Transformer konumsuz     tohum=2 son_kayip=1.4780 sure=55s
LSTM (dikkatsiz)         tohum=0 son_kayip=0.0104 sure=21s
LSTM (dikkatsiz)         tohum=1 son_kayip=0.0091 sure=22s
LSTM (dikkatsiz)         tohum=2 son_kayip=0.2326 sure=20s

Parametre sayisi ve sure ortalamasi:
Transformer sinüzoidal    236048     58s
Transformer öğrenilen     238096     56s
Transformer RoPE          236048     65s
Transformer konumsuz      236048     57s
LSTM (dikkatsiz)          201744     21s

Dizi düzeyi doğruluk (ortalama±sapma, 3 tohum)
L    sin         ogr         RoPE        yok         LSTM
4    0.994±0.005 1.000±0.000 0.986±0.008 0.049±0.018 1.000±0.000
8    0.993±0.006 1.000±0.000 0.984±0.011 0.000±0.000 0.963±0.015
12   0.948±0.048 1.000±0.000 0.848±0.015 0.000±0.000 0.257±0.140
16   0.000±0.000 0.000±0.000 0.013±0.010 0.000±0.000 0.006±0.007
20   0.000±0.000 0.000±0.000 0.000±0.000 0.000±0.000 0.000±0.000
24   0.000±0.000 0.000±0.000 0.000±0.000 0.000±0.000 0.000±0.000

Dikkat analizi (sinüzoidal, tohum 0, L=10):
baş | enc:önceki | enc:kendisi | çapraz:ters köşegen
  0 |       0.095 |       0.155 |               0.556
  1 |       0.096 |       0.169 |               0.528
  2 |       0.098 |       0.093 |               0.657
  3 |       0.093 |       0.131 |               0.556
```

Sonuçlar üç tohumun ortalaması ve örnek sapmasıyla verilmiştir. Eğitim aralığının içinde (4, 8, 12) sinüzoidal kodlama `0,994`, `0,993` ve `0,948` doğruluk verdi; öğrenilen gömmeler `1,000` üç uzunlukta da; RoPE `0,986`, `0,984` ve `0,848`; konumsuz model ise `0,049` ve sonrasında sıfır. LSTM taban çizgisi `1,000`, `0,963` ve `0,257` ile, uzunluk arttıkça çöküyor; 12'de sapması da çok büyük (`±0,140`). Bu kısım, dikkatin darboğazı nasıl kaldırdığını gösteriyor: aynı uzunlukta Transformer `0,948` alırken LSTM `0,257` alıyor.

Eğitim aralığının dışına çıkınca tablo değişiyor. `L = 16`, `20` ve `24` için her varyant `0,013`ün altında kaldı; RoPE'de `16`da `0,013`, sinüzoidal ve öğrenilen gömmelerde sıfır. Yani bu kurulumda hiçbir konum kodlaması uzunluk genellemesi göstermedi. RoPE'nin, eğitimde görülmeyen uzunluklara genelleme iddiası bu deneyde doğrulanmadı; ölçtüğümüz şey, RoPE'nin eğitim aralığının içinde sinüzoidal kodlama ile benzer bir doğruluğa ulaştığı ve aralık dışında onunla birlikte çöktüğüdür. Olası nedenlerden biri, modelin yalnızca 4–12 uzunluğunda 2 000 adım görmesi ve bu uzunlukların ötesindeki konum örüntülerini hiç öğrenmemesidir. Bu yorumu doğrulamak için eğitim aralığını genişletmek ve adım sayısını artırmak gerekir; bu bölümde yapmadık. Öğrenilen gömmelerde de benzer bir durum var: `maxT = 32` olduğu için 16 ve üstü konumların satırları eğitilmedi, rastgele kaldı.

Konumsuz model ise kodlamanın gerekliliğini gösteriyor. Encoder sırayı göremediği için, ters çevirme dizisi çözülemez; yalnızca 4 uzunluğunda `%4,9` doğruluk alabiliyor. Bu, 69.6'daki permütasyon eşdeğişkenliğinin pratikteki sonucudur.

Parametre sayıları, konum kodlamasının türüne göre farklılık gösterir: sinüzoidal, RoPE ve konumsuz modeller `236 048`, öğrenilen gömmeli model `238 096` (fazladan `maxT × d` gömme tablosu), LSTM ise `201 744` parametreye sahip. Eğitim süreleri CPU'da paylaşılan bir makinede ölçüldü ve yeniden koşuda `21` ile `65` saniye arasında değişti (ilk koşuda CPU diğer süreçlerle paylaşıldığı için süreler daha uzundu); bu süreleri karşılaştırmada kullanmıyoruz.

Eğitilmiş sinüzoidal modelin (tohum 0, `L = 10`) çapraz dikkatine baktığımızda, ters köşegenin güçlü biçimde okunduğunu gördük: her başın ters köşegen üzerindeki ağırlık ortalaması `0,53` ile `0,66` arasındadır. Rastgele bir dağılımda bu değer yaklaşık `0,1` olurdu. En güçlü baş `2`dir (`0,657`). Encoder öz-dikkatinde ise başlar arasında belirgin bir ayrışma yok: önceki belirtece verilen ağırlık `0,093`–`0,098` aralığında, yani neredeyse düzgün bir dağılıma yakın. Dolayısıyla "başlar farklı desenler öğrendi" iddiasını bu modelde yalnızca kısmen destekleyebiliyoruz: çapraz dikkatte hizalama herkes tarafından yapılıyor, öz-dikkatte ise anlamlı bir uzmanlaşma ölçemedik.

![Şekil 69.8: Dizi ters çevirmede doğruluk, test dizisi uzunluğuna göre. Gölgeli bant eğitim aralığı (4–12). Hata çubukları 3 tohumun örnek sapması. Hiçbir varyant eğitim aralığının dışında genelleme yapmadı.](gorseller/b69_uzunluk.png)

![Şekil 69.9: Eğitilmiş sinüzoidal modelin (tohum 0, L = 10) dört başının çapraz dikkat ağırlıkları. Satırlar çıktı adımı, sütunlar kaynak konumu. Ters köşegen (j = L−1−t) her başta okunabilir.](gorseller/b69_attn_isi.png)

## 69.10 Eğitim pratiği: ısınma, normalizasyon ve düzenlileştirme

Transformer'ı eğitmek, Bölüm 64'te gördüğün eğitim sanatının bütün zorluklarını taşır, ama ek bir sorun getirir: öğrenme oranına karşı hassastır. Attention'ın skorları, eğitimin başında rastgele ağırlıklarla büyük değerler alabilir; bu da softmax'ı doyurur ve gradyanı bozar. Bu nedenle Transformer eğitiminde iki şey neredeyse her zaman birlikte kullanılır: doğrusal bir ısınma (warmup) ve kosinüs biçiminde bir azalma. Bölüm 64.5'te bu zamanlayıcıyı anlatmıştık. Burada yalnızca neden Transformer'da daha da kritik olduğunu ölçerek göreceğiz.

Ağırlık azaltma, Bölüm 64'te gördüğün AdamW ayrımıyla kullanılır: ağırlık azaltma gradyan güncellemesinden ayrı uygulanır. Gradyan kırpma (`clip_grad_norm_`) Bölüm 64.9'da anlatıldığı gibi patlayan gradyanı sınırlar; bu deneyde normu 1,0 ile kırpıyoruz. Dropout, Bölüm 64.8'deki gibi blok çıktılarında uygulanır.

Etiket yumuşatma (label smoothing), hedef dağılımında doğru sınıfın olasılığını `1 − ε`ye, kalan `ε`yi diğer sınıflara dağıtır. Bu, modeli aşırı kendinden emin olmaktan alıkoyar ve Bölüm 64.8'de gördüğün düzenlileştirme ailesine girer. Büyük Transformer eğitimlerinde yaygındır; bu bölümde ayrıca ölçmüyoruz. Pratik olarak `ε = 0,1` gibi küçük değerler kullanılır (genel bilgi).

Warmup neden önemli? Eğitimin başında Adam'ın ikinci moment tahmini henüz doğru değildir ve güncellemeler gerçek gradyanın ölçeğine göre fazla büyük olabilir. Bölüm 64'ün çözümlü örneğinde Adam'ın ilk adımlarını elle izlemiştin; bu durum orada da görülmüştü. Transformer'da bu sorun, attention skorlarının yüksek varyansı ve post-norm'un artık yoldaki normalizasyonu ile birleşir. Bu gerekçeler, warmup'ın gerekli olduğunu öngörür. Bunu 69.11'de, iki normalizasyon düzeni ve iki warmup seçeneğiyle ölçtük. Ölçümümüz yalnızca doğrulama perplexity'sine dayanır; eğitim kaybı ayrıca etiketlidir ve karşılaştırmaya girmez.

## 69.11 Karakter düzeyinde decoder-only dil modeli

Şimdi ilk gerçek dil modeli deneyine geçiyoruz. Veri, kitabın kendi bölümlerinden (48 ve 51) alınan düz metin. Kod, tablo ve başlıklar atılmıştır; kalan metin yaklaşık altmış bin karakterdir. Karakter düzeyinde model, her karakteri bir belirteç sayar. Bu, Bölüm 70'te alt-kelime belirteçlerle yapacağımız işin basitleştirilmiş hâlidir: sözlük küçüktür, ama bir dil modelinin temel mekanizması aynıdır.

Veri, ilk %90 eğitim, son %10 doğrulama olarak bölünür. Bu bir zaman serisi bölmesidir: doğrulama, eğitimden sonraki metinden oluşur ve karıştırılmaz. Model, 64 belirtek uzunluğunda pencerelerle eğitilir; her pencere için hedef, bir kaydırılmış dizidir. Nedensel maske, Bölüm 69.4'te gördüğün gibi her konumun yalnızca geçmişi görmesini sağlar.

Bir dil modelinin kalitesini ölçmek için kullandığımız ölçü perplexity'dir (Bölüm 51.10). Doğrulama perplexity'si, doğrulama metnindeki ortalama çapraz entropinin üstelidir: `exp(−(1/N) Σ log p(y_t | geçmiş))`. Düzgün bir dağılımda perplexity sözlük boyutuna eşittir; yani model her adımda "kaç seçenek arasında kaldığını" bu sayı verir. Taban çizgisi olarak bigram modelini kullanıyoruz: her karakter, yalnızca bir önceki karaktere bakar ve geçişler eğitim sayımlarından (Laplace benzeri, `α = 0,1`) hesaplanır. Bigram, attention'ın gerçekten bağlam kullanıp kullanmadığını görmek için bir ölçüttür. Eğer bir Transformer bigram'ı geçemiyorsa, ya eğitim hatalıdır ya da model gerçekten bağlam kullanmıyordur.

Model 2 katman, `d = 64`, 4 baş, pre-norm, sinüzoidal kodlama ve dropout `0,1` kullanır. Eğitim AdamW ile, en yüksek öğrenme oranı `3·10⁻³`, ağırlık azaltma `0,01` ve 1 500 adım boyuncadır. Ana yapılandırmada 200 adım warmup vardır ve ardından kosinüs azalması gelir. Karşılaştırma için dört yapılandırma vardır: pre-norm ve post-norm, her biri warmup'lı ve warmup'sız. Her yapılandırma üç tohumla eğitilir.

```python
# -*- coding: utf-8 -*-
"""Bölüm 69 - Karakter düzeyi decoder-only dil modeli."""

import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tr69 import Model, tohum

KOK = "D:/Mevcut Projeler/Kitap"
T = 64  # bağlam uzunluğu
BATCH = 32
ADIM = 1500
TOHUMLAR = [0, 1, 2]

def korpus():
    """Kitabın bölümlerinden düz metin (kod ve tablo atılır)."""
    satirlar, kod = [], False
    for no in ["48", "51"]:
        yol = os.path.join(KOK, "bolumler", "bolum_%s.md" % no)
        for s in open(yol, encoding="utf-8"):
            s = s.strip()
            if s.startswith("```"):
                kod = not kod
                continue
            if kod or not s or s[0] in "#|%!:-$":
                continue
            satirlar.append(s)
    metin = " ".join(satirlar)
    return metin.replace("**", "").replace("`", "")
```

```python
def egit(model, veri, rng, lr, isinma, adim=ADIM):
    opt = torch.optim.AdamW(
        model.parameters(), lr=lr, weight_decay=0.01
    )

    def cizelge(a):
        if a < isinma:  # doğrusal ısınma
            return (a + 1) / isinma
        ilerleme = (a - isinma) / max(1, adim - isinma)
        return 0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * ilerleme))

    sched = torch.optim.lr_scheduler.LambdaLR(opt, cizelge)
    kayip_son = []
    for a in range(adim):
        i = rng.integers(0, len(veri) - T - 1, size=BATCH)
        x = torch.stack([veri[k : k + T] for k in i])
        y = torch.stack([veri[k + 1 : k + T + 1] for k in i])
        model.train()
        loss = F.cross_entropy(
            model(x).reshape(-1, model.cikis.out_features),
            y.reshape(-1),
        )
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if a >= adim - 100:
            kayip_son.append(float(loss))
    return float(np.mean(kayip_son)) if kayip_son else float("nan")
```

```python
def ppl(model, veri):
    """Pencereleri üst üste binmeden değerlendir."""
    model.eval()
    xs, ys = [], []
    for i in range(0, len(veri) - T - 1, T):
        xs.append(veri[i : i + T])
        ys.append(veri[i + 1 : i + T + 1])
    x, y = torch.stack(xs), torch.stack(ys)
    with torch.no_grad():
        kayip = 0.0
        for b in range(0, len(x), 64):
            lo = model(x[b : b + 64])
            kayip += float(
                F.cross_entropy(
                    lo.reshape(-1, lo.shape[-1]),
                    y[b : b + 64].reshape(-1),
                    reduction="sum",
                )
            )
    return math.exp(kayip / y.numel())

def bigram_ppl(egitim, dogrulama, V, alfa=0.1):
    C = np.full((V, V), alfa)
    for a, b in zip(egitim[:-1], egitim[1:]):
        C[a, b] += 1
    P = C / C.sum(axis=1, keepdims=True)
    nll = -np.log(P[dogrulama[:-1], dogrulama[1:]]).mean()
    return math.exp(nll)
```

```python
@torch.no_grad()
def uret(model, sozluk, karakterler, baslangic, n, sicaklik, seed):
    model.eval()
    gen = torch.Generator().manual_seed(seed)
    ctx = torch.tensor([sozluk[c] for c in baslangic])[None]
    for _ in range(n):
        lo = model(ctx[:, -T:])[0, -1] / sicaklik
        p = torch.softmax(lo, dim=-1)
        nxt = torch.multinomial(p, 1, generator=gen)
        ctx = torch.cat([ctx, nxt[None]], dim=1)
    return "".join(karakterler[int(i)] for i in ctx[0])

if __name__ == "__main__":
    metin = korpus()
    karakterler = sorted(set(metin))
    V = len(karakterler)
    sozluk = {c: i for i, c in enumerate(karakterler)}
    veri = torch.tensor([sozluk[c] for c in metin], dtype=torch.long)
    n = int(0.9 * len(veri))
    egitim, dogrulama = veri[:n], veri[n:]
    print("Metin uzunluğu: %d karakter, sözlük: %d" % (len(metin), V))
    print("Eğitim: %d, doğrulama: %d karakter" % (n, len(dogrulama)))
    bp = bigram_ppl(egitim.numpy(), dogrulama.numpy(), V)
    print("Bigram taban çizgisi (doğrulama perplexity): %.3f" % bp)
```

```python
    konfig = [
        ("pre-norm + ısınma (ana)", "pre", 200, 3e-3),
        ("pre-norm, ısınma yok", "pre", 0, 3e-3),
        ("post-norm + ısınma", "post", 200, 3e-3),
        ("post-norm, ısınma yok", "post", 0, 3e-3),
    ]
    ana = None
    for ad, norm, isinma, lr in konfig:
        vals, egit_kay = [], []
        for s in TOHUMLAR:
            tohum(s)
            model = Model(
                V,
                d=64,
                h=4,
                L=2,
                maxT=T,
                konum="sin",
                norm=norm,
                cift=False,
                drop=0.1,
            )
            t0 = time.time()
            ek = egit(
                model,
                egitim,
                np.random.default_rng(s),
                lr,
                max(isinma, 1),
            )
            p = ppl(model, dogrulama)
            vals.append(p)
            egit_kay.append(ek)
            print(
                "%-24s t=%d ppl=%.3f kayip=%.3f %.0fs"
                % (ad, s, p, ek, time.time() - t0)
            )
            if s == 0 and norm == "pre" and isinma == 200:
                ana = model
        v = np.array(vals)
```

```python
        print(
            ">> %s: ppl %.3f ± %.3f" % (ad, v.mean(), v.std(ddof=1))
        )
    print(
        "Parametre sayısı (ana model):",
        sum(p.numel() for p in ana.parameters()),
    )
    print("--- Örnek üretim (ana model, tohum 0) ---")
    istem = metin[n : n + 20]  # doğrulama metninden istem
    for sic in [0.7, 1.0]:
        cik = uret(ana, sozluk, karakterler, istem, 120, sic, seed=3)
        duz = cik.replace("\n", " ")
        print("sicaklik=%.1f:" % sic)
        for k in range(0, len(duz), 70):
            print(duz[k : k + 70])
```

Çıktı:

```term
$ python g07_dil.py
Metin uzunluğu: 130102 karakter, sözlük: 165
Eğitim: 117091, doğrulama: 13011 karakter
Bigram taban çizgisi (doğrulama perplexity): 15.472
pre-norm + ısınma (ana)  t=0 ppl=6.637 kayip=1.632 63s
pre-norm + ısınma (ana)  t=1 ppl=6.433 kayip=1.605 43s
pre-norm + ısınma (ana)  t=2 ppl=6.590 kayip=1.610 44s
>> pre-norm + ısınma (ana): ppl 6.553 ± 0.107
pre-norm, ısınma yok     t=0 ppl=6.621 kayip=1.632 33s
pre-norm, ısınma yok     t=1 ppl=6.539 kayip=1.601 27s
pre-norm, ısınma yok     t=2 ppl=6.631 kayip=1.606 28s
>> pre-norm, ısınma yok: ppl 6.597 ± 0.051
post-norm + ısınma       t=0 ppl=6.537 kayip=1.609 31s
post-norm + ısınma       t=1 ppl=6.410 kayip=1.600 29s
post-norm + ısınma       t=2 ppl=6.498 kayip=1.584 29s
>> post-norm + ısınma: ppl 6.482 ± 0.065
post-norm, ısınma yok    t=0 ppl=6.448 kayip=1.596 29s
post-norm, ısınma yok    t=1 ppl=6.473 kayip=1.586 29s
post-norm, ısınma yok    t=2 ppl=6.593 kayip=1.580 28s
>> post-norm, ısınma yok: ppl 6.505 ± 0.077
Parametre sayısı (ana model): 121637
--- Örnek üretim (ana model, tohum 0) ---
sicaklik=0.7:
kayıp ln 2 ≈ 0,69dan bir kursayların sayısı için arasındaki bulok matr
is, çıkarı kısmı (yap fark verir ve güncü sözlemli geçipsi satır. Bu,
sicaklik=1.0:
kayıp ln 2 ≈ 0,69dan yaklaşık für: uzunluk iᵢ⁵ en için mektilerde S ob
u dene bir kısmız (condin bir formülüs oltudur, spayakları farklı nokt
```

Bigram taban çizgisi doğrulama perplexity'si `15,47` verdi. Ana model (pre-norm, 200 adım warmup, kosinüs azalması) üç tohumla `6,553 ± 0,107` aldı. Model, bigram'ın perplexity'sinin yaklaşık yarısına indi; bu, bağlamın gerçekten kullanıldığını gösterir. Parametre sayısı `121 637`dir.

Dört yapılandırmanın sonucu şöyledir: pre-norm ve warmup'lı `6,553 ± 0,107`, pre-norm ve warmup'sız `6,597 ± 0,051`, post-norm ve warmup'lı `6,482 ± 0,065`, post-norm ve warmup'sız `6,505 ± 0,077`. Dört sonuç birbirinden en fazla `0,12` perplexity birimi uzakta ve sapmaların boyutundadır. Bu koşulda, en yüksek öğrenme oranı `3·10⁻³` ile kısa bir eğitimde, warmup'ın da pre/post-norm seçiminin de ölçülebilir bir etkisi yok. Bu, warmup'ın gereksiz olduğu anlamına gelmez: daha yüksek öğrenme oranlarında, daha derin modellerde ya da daha uzun eğitimde fark ortaya çıkabilir. Biz bu bölümde yalnızca bu koşulları ölçtük. Özellikle post-norm'un warmup'sız bu öğrenme oranında ıraksamaması, 69.10'daki beklentinin bu ölçekte doğrulanmadığını gösterir.

Örnek üretimde (1 500 adımlık ana model, tohum 0) çıktı henüz tutarlı cümleler değil. Model Türkçe karakter sıklıklarını, bazı kısa kelime parçalarını ve noktalama düzenini öğrenmiş, ama uzun bağımlılıkları henüz kuramamış. Sıcaklık `0,7` çıktısı daha tekrarlı, `1,0` çıktısı daha rastgele. Bu, Bölüm 70'te daha büyük bir modelle ve alt-kelime belirteçlerle daha anlamlı üretimi hedefleyeceğimiz noktayı gösteriyor.

## 69.12 Karmaşıklık, KV önbelleği ve verimlilik

Attention'ın maliyeti, Bölüm 69.3'teki formülden doğrudan okunur. `T` belirteçli bir dizi için skor matrisi `T × T`dir. `QKᵀ` ve `AV` işlemleri her biri `T²·d` çarpma-toplama yapar; bu, zamanın `O(T²·d)` olduğu anlamına gelir. Skor matrisinin belleği ise `O(T²)`dir ve eğitimde geri yayılım için saklanması gerekir. Projeksiyonlar `O(T·d²)` maliyetindedir. Böylece kısa dizilerde doğrusal terim, uzun dizilerde karesel terim baskın olur. Çözümlü Örnek 4'te bu geçiş noktasının `T = 6d` olduğunu hesaplayacağız.

Otoregresif üretimde ek bir maliyet ortaya çıkar. Her yeni belirteç için model, tüm diziyi baştan işlerse, `N` adımlık üretim `O(N³)` gibi büyür (her adımda `O(N²)` iş, `N` adım). KV önbelleği bu tekrarı önler: her katmanda, geçmiş belirteçlerin anahtar ve değer vektörlerini (`K`, `V`) saklarız. Yeni bir belirteç geldiğinde yalnızca onun `q`, `k` ve `v`sini hesaplarız; yeni `k` ve `v` önbelleğe eklenir ve yeni `q`, önbelleğin tamamına bakar. Böylece her adımın maliyeti `O(N·d)`ye düşer ve toplam `O(N²)`dir. Bedeli bellektir: her katmanda `2 · N · d` sayı tutulur. Bu, Bölüm 71'deki servis etme ve bellek tartışmasının temelidir.

Önbellek çıktıyı değiştirmez. Bu, hesaplamanın matematiksel olarak aynı olmasından gelir: yeni belirtecin çıktısı, önbellekteki `k` ve `v`lerle hesaplanan aynı ağırlıklı toplamdır. Sayısal olarak küçük farklar olabilir; ama aynı ağırlıklarla ve aynı sayı tipinde, belirteç dizisi değişmez.

Şekil 69.10, bu iki maliyeti ölçüyor: solda tek bir attention katmanının süresi `T` ile, sağda önbelleksiz ve önbellekli üretimin süresi `N` ile.

```python
# -*- coding: utf-8 -*-
"""Bölüm 69 - Attention'ın süre ve bellek maliyeti, KV önbelleği."""

import csv
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
from tr69 import Dikkat, Model, tohum

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
V = 50
```

```python
@torch.no_grad()
def adim_onbellekli(model, x_son, t, onb):
    """Tek belirteç: yalnız yeni q; k, v önbellekten gelir."""
    h = model.emb(x_son) + model.pe[t]
    for i, b in enumerate(model.dec):
        n = b.ln1(h)
        q = b.oz._bol(b.oz.wq(n))
        k = b.oz._bol(b.oz.wk(n))
        v = b.oz._bol(b.oz.wv(n))
        if onb[i] is None:
            onb[i] = (k, v)
        else:
            onb[i] = (
                torch.cat([onb[i][0], k], 2),
                torch.cat([onb[i][1], v], 2),
            )
        K, Vv = onb[i]
        A = torch.softmax(
            q @ K.transpose(-2, -1) / math.sqrt(b.oz.dh), -1
        )
        o = (A @ Vv).transpose(1, 2).reshape(1, 1, -1)
        h = h + b.oz.wo(o)
        h = h + b.ff(b.ln3(h))
    return model.cikis(model.dec_son(h))[:, 0]

@torch.no_grad()
def onbellekli(model, ctx, n):
    P = ctx.shape[1]
    onb = [None] * len(model.dec)
    for t in range(P):  # istemi tek tek işle
        lo = adim_onbellekli(model, ctx[:, t : t + 1], t, onb)
    seq = ctx
    for t in range(P, P + n):
        nxt = lo.argmax(-1, keepdim=True)
        seq = torch.cat([seq, nxt], 1)
        lo = adim_onbellekli(model, nxt, t, onb)
    return seq, lo
```

```python
@torch.no_grad()
def onbellegiz(model, ctx, n):
    seq = ctx
    for _ in range(n):  # her adımda tüm diziyi yeniden
        lo = model(seq)[:, -1]
        seq = torch.cat([seq, lo.argmax(-1, keepdim=True)], 1)
    return seq, model(seq)[:, -1]

def eslesme():
    print(
        "--- KV önbelleği: aynı çıktı mı? (rastgele ağırlık) ---"
    )
    tohum(0)
    model = Model(
        V,
        d=64,
        h=4,
        L=2,
        maxT=512,
        konum="sin",
        norm="pre",
        cift=False,
        drop=0.0,
    ).eval()
    ctx = torch.randint(0, V, (1, 8))
    s1, lo1 = onbellekli(model, ctx, 200)
    s2, lo2 = onbellegiz(model, ctx, 200)
    print("belirteç dizileri aynı:", bool(torch.equal(s1, s2)))
    print(
        "son adım logit farkı: %.2e" % float((lo1 - lo2).abs().max())
    )
```

```python
def sure_olc(f, tekrar=5):
    zamanlar = []
    for _ in range(tekrar):
        t0 = time.perf_counter()
        f()
        zamanlar.append(time.perf_counter() - t0)
    zamanlar.sort()
    return zamanlar[len(zamanlar) // 2]  # medyan
```

```python
def kv_hizi():
    print("--- Üretim süresi: önbelleksiz ve önbellekli (P=8) ---")
    tohum(0)
    model = Model(
        V,
        d=64,
        h=4,
        L=2,
        maxT=1024,
        konum="sin",
        norm="pre",
        cift=False,
        drop=0.0,
    ).eval()
    ctx = torch.randint(0, V, (1, 8))
    satirlar = []
    print("   N  onbelleksiz_s  onbellekli_s  hizlanma")
    for N in [64, 128, 256, 512]:
        s_on = sure_olc(lambda: onbellekli(model, ctx, N), 3)
        s_ob = sure_olc(lambda: onbellegiz(model, ctx, N), 3)
        print(
            "%4d  %13.3f  %12.3f  %8.1fx"
            % (N, s_ob, s_on, s_ob / s_on)
        )
        satirlar.append([N, "%.4f" % s_ob, "%.4f" % s_on])
    with open(
        os.path.join(VERI, "b69_kv.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["N", "onbellegiz_s", "onbellekli_s"])
        w.writerows(satirlar)
```

```python
def olcek():
    print("--- Tek dikkat katmanı: süre ve skor matrisi belleği ---")
    tohum(0)
    m = Dikkat(64, 4).eval()
    satirlar = []
    print("    T  sure_ms  skor_matrisi_MB (h=4, float32)")
    for T in [64, 128, 256, 512, 1024, 2048]:
        x = torch.randn(1, T, 64)
        with torch.no_grad():
            s = sure_olc(lambda: m(x, x, None, False), 5) * 1000
        mb = 4 * T * T * 4 / 1e6
        print("%5d  %7.2f  %10.2f" % (T, s, mb))
        satirlar.append([T, "%.3f" % s, "%.2f" % mb])
    with open(
        os.path.join(VERI, "b69_olcek.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["T", "sure_ms", "matris_MB"])
        w.writerows(satirlar)

if __name__ == "__main__":
    print("torch iş parçacığı sayısı:", torch.get_num_threads())
    eslesme()
    kv_hizi()
    olcek()
```

Çıktı:

```term
$ python g08_kv.py
torch iş parçacığı sayısı: 8
--- KV önbelleği: aynı çıktı mı? (rastgele ağırlık) ---
belirteç dizileri aynı: True
son adım logit farkı: 5.96e-07
--- Üretim süresi: önbelleksiz ve önbellekli (P=8) ---
   N  onbelleksiz_s  onbellekli_s  hizlanma
  64          0.085         0.066       1.3x
 128          0.130         0.106       1.2x
 256          0.449         0.151       3.0x
 512          0.988         0.311       3.2x
--- Tek dikkat katmanı: süre ve skor matrisi belleği ---
    T  sure_ms  skor_matrisi_MB (h=4, float32)
   64     0.19        0.07
  128     0.19        0.26
  256     0.27        1.05
  512     0.62        4.19
 1024     4.52       16.78
 2048    17.59       67.11
```

KV önbelleğinin doğruluğu ilk satırlarda görülüyor: önbellekli ve önbelleksiz üretim, rastgele ağırlıklarla 200 belirteçlik dizide aynı belirteç dizisini verdi ve son adımdaki logit'lerdeki en büyük fark `6·10⁻⁷`dir; bu, `float32` yuvarlamasıdır. Hızlanma `N` ile artıyor: `N = 64`te `1,3` kat, `N = 256`da `3,0` kat, `N = 512`de `3,2` kat. Ölçüm gürültülüdür; `N = 128`de `1,2` kat çıktı, çünkü küçük `N`lerde süre Python yükü ve makinedeki diğer süreçler tarafından belirleniyor. Model çok küçük olduğu için kazanç, teorik `O(N)`ye kıyasla daha düşük kalıyor. Önbelleğin asimptotik kazancı `N` büyüdükçe artar; bu ölçümde bu eğilim açıkça görülüyor, ama `N = 512`de bile tam `O(N)` kazancına ulaşmadık.

Tek attention katmanının süresi `T = 64`ten `T = 512`ye kadar yavaş büyüdü (`0,19` ms'den `0,62` ms'ye); bu aralıkta Python ve bellek ayırma yükü baskın. `T = 1 024`ten `2 048`e geçişte süre `4,52` ms'den `17,59` ms'ye, yani yaklaşık `3,9` kat arttı; bu, `T²` beklentisine (4 kat) çok yakındır. Skor matrisinin belleği (`h = 4`, `float32`, tek örnek) `T = 2 048`de `67` MB'dır ve `T` ile karesel büyür. Ölçümler, aynı makinede diğer süreçlerin de CPU kullandığı bir ortamda alındı; her nokta beş çalıştırmanın medyanıdır. Mutlak sayılar makineye bağlıdır; karşılaştırılabilir olan eğilimdir.

![Şekil 69.10: Solda tek attention katmanının süresi T ile (log–log; kesikli çizgi T² referansı) ve skor matrisinin belleği. Sağda önbelleksiz ve KV önbellekli üretim süreleri N ile. Ölçümler CPU'da, medyan ile.](gorseller/b69_olcek_kv.png)

## 69.13 Görüntüye uzanım: Vision Transformer

Bölüm 66'da konvolüsyonun görüntüye yerel önseziyi (komşu pikseller ilişkilidir) ve ağırlık paylaşımını yerleştirdiğini gördün. Vision Transformer (ViT), Dosovitskiy ve arkadaşlarının 2020'de önerdiği yaklaşımda bu önseziyi bırakır: görüntüyü sabit boyutlu yamalara böler (ör. `8 × 8`), her yamayı doğrusal olarak bir belirteç gömmesine çevirir, sonra bu belirteç dizisini bir encoder'dan geçirir (genel bilgi). Yani ViT, Bölüm 69.8'de tanımladığımız encoder ailesinin görüntüye uygulanmasıdır.

Burada yanlılığın nedeni önemlidir. CNN, yerellik ve öteleme eşdeğişkenliğini mimariye gömer; ViT ise yalnızca yama gömmesini ve konum kodlamasını bilir. Büyük veriyle ViT, CNN'in üstüne çıkabilir. Az veride ise CNN'in gömülü önseziyi kullanması bir avantajdır. Bunu ölçmek için dört sınıflı bir sentetik görüntü görevi kuruyoruz: yatay çubuk, dikey çubuk, daire ve köşegen. Görüntüler 32 × 32 gri tonlu ve gürültülüdür; konum ve boyut rastgele değişir. Küçük bir ViT (yama 8, `d = 64`, 2 blok) ile küçük bir CNN (üç konvolüsyon bloğu) iki veri büyüklüğünde (300 ve 5 000 eğitim görüntüsü) karşılaştırılır. Test kümesi 1 000 görüntüdür ve tüm tohumlar için aynıdır. Veri artırma kullanılmaz; böylece karşılaştırma yalnızca mimariyi ölçer.

```python
# -*- coding: utf-8 -*-
"""Bölüm 69 - Küçük ViT ve küçük CNN: veri miktarı."""

import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tr69 import Blok, tohum

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
BOY = 32
ADIM = 1500
BATCH = 64
TOHUMLAR = [0, 1, 2]
```

```python
def uret(rng, n):
    """4 sınıf: yatay, dikey çubuk, daire, köşegen."""
    X = np.zeros((n, 1, BOY, BOY), np.float32)
    y = rng.integers(0, 4, size=n)
    yy, xx = np.mgrid[0:BOY, 0:BOY]
    for i in range(n):
        cx, cy = rng.integers(10, 22, size=2)
        r = int(rng.integers(4, 8))
        if y[i] == 0:
            m = (np.abs(yy - cy) <= 1) & (np.abs(xx - cx) <= r)
        elif y[i] == 1:
            m = (np.abs(xx - cx) <= 1) & (np.abs(yy - cy) <= r)
        elif y[i] == 2:
            d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
            m = np.abs(d - r) <= 1
        else:
            m = (np.abs((xx - cx) - (yy - cy)) <= 1) & (
                np.abs(xx - cx) <= r
            )
        parlaklik = 0.6 + 0.4 * rng.random()
        X[i, 0] = m * parlaklik + rng.normal(0, 0.25, (BOY, BOY))
    return torch.tensor(X), torch.tensor(y, dtype=torch.long)

class VitK(nn.Module):
    """Yama gömmesi + konum gömmesi + kodlayıcı blokları."""

    def __init__(self, d=64, h=4, L=2, yama=8):
        super().__init__()
        n = (BOY // yama) ** 2
        self.proj = nn.Conv2d(1, d, yama, stride=yama)
        self.pos = nn.Parameter(torch.randn(1, n, d) * 0.02)
        self.blocks = nn.ModuleList(
            [Blok(d, h, "pre", 0.0, False) for _ in range(L)]
        )
        self.son = nn.LayerNorm(d)
        self.cikis = nn.Linear(d, 4)
```

```python
    def forward(self, x):
        h = self.proj(x).flatten(2).transpose(1, 2) + self.pos
        for b in self.blocks:  # maske yok: çift yönlü
            h = b(h)
        return self.cikis(self.son(h).mean(dim=1))

class Cnn(nn.Module):
    """Üç konvolüsyon bloğu (yerel, öteleme-eşdeğişken)."""

    def __init__(self):
        super().__init__()
        self.ag = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(64, 4),
        )

    def forward(self, x):
        return self.ag(x)

def egit(model, X, y, seed):
    rng = np.random.default_rng(seed)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    for _ in range(ADIM):
        i = torch.tensor(rng.integers(0, len(X), size=BATCH))
        loss = F.cross_entropy(model(X[i]), y[i])
        opt.zero_grad()
        loss.backward()
        opt.step()
```

```python
@torch.no_grad()
def dogruluk(model, X, y):
    model.eval()
    tahmin = torch.cat(
        [
            model(X[b : b + 500]).argmax(-1)
            for b in range(0, len(X), 500)
        ]
    )
    return float((tahmin == y).float().mean())
```

```python
def main():
    Xt, yt = uret(np.random.default_rng(999), 1000)
    print("test kümesi: 1000 görüntü, 4 sınıf, tohum 999")
    sonuc = {}
    satirlar = []
    for N in [300, 5000]:
        for ad, kur in [("ViT (yama 8)", VitK), ("CNN", Cnn)]:
            sonuc[(ad, N)] = []
            for s in TOHUMLAR:
                tohum(s)
                X, y = uret(np.random.default_rng(100 + s), N)
                model = kur()
                t0 = time.time()
                egit(model, X, y, s)
                te = dogruluk(model, Xt, yt)
                tr = dogruluk(model, X[:1000], y[:1000])
                sonuc[(ad, N)].append(te)
                print(
                    "%-13s N=%5d tohum=%d test=%.3f egitim=%.3f "
                    "sure=%.0fs"
                    % (ad, N, s, te, tr, time.time() - t0)
                )
            v = np.array(sonuc[(ad, N)])
            satirlar.append(
                [ad, N, "%.4f" % v.mean(), "%.4f" % v.std(ddof=1)]
            )
    print()
    print(
        "Parametre sayısı: ViT %d, CNN %d"
        % (
            sum(p.numel() for p in VitK().parameters()),
            sum(p.numel() for p in Cnn().parameters()),
        )
    )
    print("Test doğruluğu (ortalama ± örnek sapması):")
    for N in [300, 5000]:
        for ad in ["ViT (yama 8)", "CNN"]:
            v = np.array(sonuc[(ad, N)])
            print(
                "N=%5d %-13s %.3f ± %.3f"
```

```python
                % (N, ad, v.mean(), v.std(ddof=1))
            )
    with open(
        os.path.join(VERI, "b69_vit.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["model", "N", "ortalama", "sapma"])
        w.writerows(satirlar)
```

```python
if __name__ == "__main__":
    main()
```

Çıktı:

```term
$ python g09_vit.py
test kümesi: 1000 görüntü, 4 sınıf, tohum 999
ViT (yama 8)  N=  300 tohum=0 test=0.805 egitim=1.000 sure=22s
ViT (yama 8)  N=  300 tohum=1 test=0.780 egitim=1.000 sure=20s
ViT (yama 8)  N=  300 tohum=2 test=0.768 egitim=1.000 sure=19s
CNN           N=  300 tohum=0 test=1.000 egitim=1.000 sure=31s
CNN           N=  300 tohum=1 test=0.998 egitim=1.000 sure=31s
CNN           N=  300 tohum=2 test=1.000 egitim=1.000 sure=23s
ViT (yama 8)  N= 5000 tohum=0 test=0.999 egitim=1.000 sure=13s
ViT (yama 8)  N= 5000 tohum=1 test=1.000 egitim=1.000 sure=13s
ViT (yama 8)  N= 5000 tohum=2 test=0.997 egitim=1.000 sure=13s
CNN           N= 5000 tohum=0 test=1.000 egitim=1.000 sure=22s
CNN           N= 5000 tohum=1 test=1.000 egitim=1.000 sure=22s
CNN           N= 5000 tohum=2 test=1.000 egitim=1.000 sure=22s

Parametre sayısı: ViT 105796, CNN 56004
Test doğruluğu (ortalama ± örnek sapması):
N=  300 ViT (yama 8)  0.784 ± 0.019
N=  300 CNN           0.999 ± 0.001
N= 5000 ViT (yama 8)  0.999 ± 0.002
N= 5000 CNN           1.000 ± 0.000
```

Sonuçlar, 1 000 görüntülük sabit test kümesinde üç tohumun ortalaması ve sapmasıdır. `N = 300` eğitim görüntüsüyle CNN `0,999 ± 0,001`, ViT `0,784 ± 0,019` aldı. Az veride CNN'in yerel ve öteleme-eşdeğişken önseziyi kullanması belirgin bir avantaj sağladı. `N = 5 000` eğitim görüntüsüyle ViT `0,999 ± 0,002`, CNN `1,000 ± 0,000` aldı; iki model de bu kolay görevde tavana yakındır ve fark ihmal edilebilir düzeydedir. Bu deney ViT'in büyük veride CNN'i geçtiğini göstermez; yalnızca, az veride yanlılık farkının görülebildiğini ve büyük veride kapandığını gösterir. Eğitim doğruluğu her iki durumda da `1,000`dir; yani az veride ViT ezberlemiş, genelleşememiştir.

Parametre sayıları ViT için `105 796`, CNN için `56 004`tür. Bu nedenle karşılaştırma, parametre sayısı bakımından eşit değildir; ViT daha büyüktür ve yine de az veride geride kalmıştır. Veri artırma kullanılmadı; bu, sonuçları mimariye bağlı tutar, ama pratikte ViT'in az veriyle eğitimi, veri artırma ve ön eğitimle birlikte değerlendirilmelidir.

## 69.14 Yorumlanabilirlik: attention ağırlıkları neyi kanıtlar?

Attention ağırlıkları, bir modelin "nereye baktığını" gösteren cazip bir araçtır. Isı haritası çizip "model şuraya baktı" demek kolaydır. Ancak bu tür açıklamanın sınırları vardır. Birincisi, ağırlıklar çıktının tek belirleyicisi değildir: değer vektörleri (`V`), çıkış projeksiyonu (`W_O`) ve artık bağlantılar sonucu da etkiler. Yüksek ağırlık, yüksek etkiye eşit değildir. İkincisi, çok katmanlı bir Transformer'da bir katmanın ağırlıkları, önceki katmanların karıştırdığı temsiller üzerinden hesaplanır; tek bir katmana bakmak bütün akışı göstermez. Üçüncüsü, çok başlı attention'da farklı başlar farklı desenler öğrenir; bunları birlikte yorumlamak gerekir ve tek bir başın anlamlı olduğunu varsaymak yanıltıcıdır.

Bu bölümün ters çevirme deneyinde, çapraz dikkatin ters köşegeni (`A[t, L−1−t]`) gerçekten yüksek çıktı; yani bu desen ağırlıklar tarafından okunabiliyor. Ancak yine de bu, nedensel bir kanıt değildir. Nedensel bir iddia için müdahale ve ablasyon gibi ek deneyler gerekir; Bölüm 57'de deney tasarımını ve karşılaştırma ilkelerini gördün. Savunma sanayiinde bir modelin kararını açıklaması gerektiğinde, attention ağırlığını tek başına gerekçe olarak sunmak, doğrulanmamış bir iddiadır. Açıklama için ağırlığa ek olarak bir müdahale testi (ör. ilgili konumu değiştirip kararın değişip değişmediğini ölçmek) eklenmelidir.

## Çözümlü Örnekler

Bu bölümdeki dört örnek zorluk sırasıyla ★, ★★, ★★ ve ★★★ olarak dizilmiştir. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntüyü bul, iyileştir ve doğrula. Doğrulama adımında elle iz sürme tablosu vardır. Her örneğin sonunda, hiçbir yapay zekâ aracı kullanmadan çözebilmen için bir varyasyon sorusu bulunur. Örneklerdeki sayılar elle hesaplandı ve bilgisayarla da kontrol edildi; ara değerleri üç ondalık basamakta yuvarladık.

### Örnek 1 (★): Üç belirteçli bir attention'ın elle hesabı

Tek boyutlu anahtar ve değerlerle çalışalım: `d_k = 1`, ölçek `1/√1 = 1`. Sorgular `q = (1, 0, 2)`, anahtarlar `k = (1, 1, 0)`, değerler `v = (10, 20, 30)`. Üç çıktı skaları bul.

**Adım 1 — Anla.** İstenen üç çıktı, `out_i = Σ_j softmax_j(q_i k_j) · v_j`. Ölçek 1 olduğu için skorlar doğrudan çarpımlardır.

**Adım 2 — Örnekle.** Skor matrisi `S[i, j] = q_i · k_j`. İlk sorgu `q_0 = 1`, anahtarlarla `1, 1, 0` çarpar. İkinci sorgu `q_1 = 0`, bütün çarpımları sıfır yapar. Üçüncü sorgu `q_2 = 2`, `2, 2, 0` verir.

**Adım 3 — Kaba çöz.** Her satır için `e^{S}` değerlerini al, toplama böl (softmax), sonra `v` ile ağırlıklı topla.

**Adım 4 — Örüntü.** İkinci satır tamamen sıfır skorlu olduğu için düzgün dağılır: her anahtara `1/3`. Birinci ve üçüncü satırlarda ilk iki anahtar aynı skora sahip, üçüncü anahtar farklı. Sorgunun büyüklüğü arttıkça (`q_2 = 2`), ağırlık, skoru yüksek olan iki anahtara daha da yığılır.

**Adım 5 — İyileştir.** Satır 0 için payda `e + e + 1 = 2e + 1`dir. Satır 2 için payda `2e² + 1`dir. Böylece her satırı tek bir payda ile hesaplarsın; üç satırda da üç terim yeterlidir.

**Adım 6 — Doğrula.** İz tablosu:

| Sorgu | Skorlar | `e^{skor}` | Toplam | Ağırlıklar | Çıktı |
|---|---|---|---|---|---|
| 0 | 1, 1, 0 | e, e, 1 | 2e + 1 = 6,437 | 0,422; 0,422; 0,155 | 0,422·10 + 0,422·20 + 0,155·30 = 17,33 |
| 1 | 0, 0, 0 | 1, 1, 1 | 3 | 0,333; 0,333; 0,333 | 20,00 |
| 2 | 2, 2, 0 | e², e², 1 | 2e² + 1 = 15,778 | 0,468; 0,468; 0,063 | 0,468·10 + 0,468·20 + 0,063·30 = 15,95 |

Üç çıktı `(17,33; 20,00; 15,95)`tir. Bilgisayarla hesaplandığında aynı sonuç çıkar.

**Bunu AI'sız yazabilir misin?** Aynı `q` ile `k = (1, 1, 1)` olsaydı üç çıktının hepsi ne olurdu? Hesaplamadan önce cevabı tahmin et, sonra nedenini bir cümleyle açıkla.

### Örnek 2 (★★): Nedensel maskenin 4×4 skor matrisine uygulanması

Dört belirteçli bir dizinin skor matrisi (ölçek uygulanmış) şöyle olsun:

    S = [[0, 1, 2, 0],
         [1, 0, 1, 2],
         [2, 1, 0, 1],
         [0, 2, 1, 0]]

Nedensel maske uygula ve her satırın ağırlıklarını elle hesapla.

**Adım 1 — Anla.** İstenen: `softmax(mask(S))`ün dört satırı. Maske, `j > i` olan hücreleri `−∞` yapar.

**Adım 2 — Örnekle.** Satır 0 yalnızca `j = 0`ı görür. Satır 1 `j = 0, 1`i görür. Satır 2 `j = 0, 1, 2`yi görür. Satır 3 hepsini görür.

**Adım 3 — Kaba çöz.** Her satırda görülebilen hücrelerin üssünü al, toplama böl. Maskelenmiş hücrelerin üssü `e^{−∞} = 0`dır ve toplama katkı vermez.

**Adım 4 — Örüntü.** Satır `i`nin payda terimi `i + 1` tanedir. İlk satırda tek terim olduğu için ağırlık `1`dir; her satırda ağırlık, o satırdaki en büyük skora yönelir ama maskelenmiş hücreler sıfıra iner.

**Adım 5 — İyileştir.** Satır 2'de maskesiz versiyonun ağırlıklarını (`0,534; 0,197; 0,072; 0,197`) bilmek, maskelenmiş sonucu türetmeyi kolaylaştırır: `j = 3` terimini paydadan çıkarırsın ve kalan üç terimi yeniden normalize edersin.

**Adım 6 — Doğrula.** İz tablosu (ondalık dört basamak):

| Satır | Görülen `j` | Maskelenmiş skorlar | Ağırlıklar |
|---|---|---|---|
| 0 | 0 | 0 | 1,0000; 0; 0; 0 |
| 1 | 0, 1 | 1, 0 | 0,7311; 0,2689; 0; 0 |
| 2 | 0, 1, 2 | 2, 1, 0 | 0,6652; 0,2447; 0,0900; 0 |
| 3 | 0–3 | 0, 2, 1, 0 | 0,0826; 0,6103; 0,2245; 0,0826 |

Satır 2'deki sayılar, maskesiz versiyonun `j = 3` terimi çıkarılıp yeniden normalize edildiğinde elde edilir: `(0,534; 0,197; 0,072) / (0,534 + 0,197 + 0,072) = (0,665; 0,245; 0,090)`. Tablo ile uyuşur.

**Bunu AI'sız yazabilir misin?** Aynı `S` ile satır 2'nin ağırlıklarını maske olmadan hesapla; sonra `j = 0` konumunu da maskele. Yeni dağılımın toplamının 1 olduğunu neden gösterebilirsin?

### Örnek 3 (★★): Sinüzoidal kodlamada konum farkının nokta çarpıma yansıması

Model boyutu `d = 4` ve sinüzoidal kodlama `PE(t, 2i) = sin(t ω_i)`, `PE(t, 2i+1) = cos(t ω_i)`, `ω_i = 10000^{−2i/d}`. İki frekans vardır: `ω_0 = 1` ve `ω_1 = 10000^{−1/2} = 0,01`. Dört konumun kodlamaları:

- `PE(0) = (0, 1, 0, 1)`
- `PE(1) = (0,8415; 0,5403; 0,0100; 1,0000)`
- `PE(2) = (0,9093; −0,4161; 0,0200; 0,9998)`
- `PE(3) = (0,1411; −0,9900; 0,0300; 0,9996)`

**Adım 1 — Anla.** İstenen: `PE(0)·PE(1)` ile `PE(0)·PE(2)` ve `PE(1)·PE(3)` değerleri. Bu değerlerin konuma mı yoksa farka mı bağlı olduğuna karar vermek.

**Adım 2 — Örnekle.** `PE(0)·PE(1) = 0·0,8415 + 1·0,5403 + 0·0,0100 + 1·1,0000 = 1,5403`.

**Adım 3 — Kaba çöz.** Her çift `(sin, cos)` için `sin(a) sin(b) + cos(a) cos(b) = cos(a − b)` özdeşliğini kullan. Böylece `PE(t)·PE(t+k) = Σ_i cos(k ω_i)` olur; yalnızca `k`ye bağlıdır.

**Adım 4 — Örüntü.** `k = 1` için `cos(1) + cos(0,01) = 0,5403 + 0,99995 = 1,5403`, hesapla uyuşur. `k = 2` için `cos(2) + cos(0,02) = −0,4161 + 0,9998 = 0,5837`. Yani `PE(0)·PE(2)` ile `PE(1)·PE(3)` birbirine eşit çıkar; çünkü ikisi de `k = 2` farkına sahiptir.

**Adım 5 — İyileştir.** Normu da hesaba kat: `‖PE(t)‖² = 2` olduğu için kosinüs benzerliği `PE(t)·PE(t+k) / 2`dir. Böylece `k = 1` için `1,5403 / 2 = 0,7701`, bu da Bölüm 69.6'daki ölçümle uyuşur.

**Adım 6 — Doğrula.** İz tablosu:

| Çift | Fark `k` | `cos(k·1)` | `cos(k·0,01)` | Toplam (nokta çarpım) |
|---|---|---|---|---|
| `PE(0)`, `PE(1)` | 1 | 0,5403 | 0,99995 | 1,5403 |
| `PE(0)`, `PE(2)` | 2 | −0,4161 | 0,9998 | 0,5837 |
| `PE(1)`, `PE(3)` | 2 | −0,4161 | 0,9998 | 0,5837 |

İki satırın son sütunu aynıdır. Yani skor, mutlak konumu değil, farkı izler. Bu, sinüzoidal kodlamanın göreli konumu kodladığının en basit kanıtıdır. Düşük boyutlu frekanslar (`ω_1`) uzun mesafelerde neredeyse sabit kalır; yüksek frekans (`ω_0`) ise kısa mesafeleri ayırt eder.

**Bunu AI'sız yazabilir misin?** `d = 4` yerine `d = 2` olsaydı yalnızca tek bir frekans kalırdı. Bu durumda `PE(0)·PE(k)` hangi fonksiyona eşit olurdu ve `k = 2π` için ne olurdu?

### Örnek 4 (★★★): Bir Transformer bloğunun parametre ve işlem sayısı

Model boyutu `d = 512`, başlar `h = 8`, MLP genişliği `4d = 2048`, dizi uzunluğu `T = 128`. Bir pre-norm bloğunun (yalnızca öz-dikkat, çapraz dikkat yok) parametre sayısını ve çarpma-toplama (MAC) sayısını bul. Sonra attention'ın `T²` teriminin hangi `T` değerinde doğrusal terimlerle eşit olduğunu çıkar.

**Adım 1 — Anla.** İstenen üç sayı: parametre sayısı, `T` boyutlu bir girdi için MAC sayısı ve iki terim arasındaki eşitlik noktası. Softmax, LayerNorm ve sapma (bias) çarpımlarını MAC sayımından çıkaracağız; bunlar doğrusal terimlere göre ihmal edilebilirdir.

**Adım 2 — Örnekle.** Dört doğrusal projeksiyon (`W_Q`, `W_K`, `W_V`, `W_O`) her biri `d × d`dir. Bu, `4d²` parametre (sapmalar hariç) demektir. MLP iki matris içerir: `d × 4d` ve `4d × d`; toplam `8d²`.

**Adım 3 — Kaba çöz.** Parametreler: attention `4d² + 4d = 1 050 624`, MLP `8d² + 5d = 2 099 712`, üç LayerNorm `3 · 2d = 3 072`. Toplam `3 153 408`dir. MAC için: projeksiyonlar `4·T·d²`, MLP `8·T·d²`, skor ve birleştirme `QKᵀ` ve `AV` için her biri `T²·d`.

**Adım 4 — Örüntü.** Doğrusal terimler `12·T·d²`, attention terimleri `2·T²·d`dir. Oranları `2T²d / (12Td²) = T / (6d)`dir. Yani attention'ın karesel maliyeti, dizi uzunluğu `6d`yi geçtiğinde baskın olur.

**Adım 5 — İyileştir.** `d = 512` için `6d = 3 072`dir. Bu, `T = 128` için attention payının yalnızca `%4` kadar olduğu anlamına gelir: sayılar `134 217 728 + 268 435 456 = 402 653 184` doğrusal ve `16 777 216` karesel MAC'tir.

**Adım 6 — Doğrula.** İz tablosu:

| Terim | Formül | Değer (`T = 128`, `d = 512`) |
|---|---|---|
| Projeksiyonlar | `4·T·d²` | 134 217 728 |
| MLP | `8·T·d²` | 268 435 456 |
| `QKᵀ` ve `AV` | `2·T²·d` | 16 777 216 |
| Toplam MAC | | 419 430 400 (≈ 419 M) |
| Parametre | `4d² + 4d + 8d² + 5d + 6d` | 3 153 408 |
| Oran (karesel/doğrusal) | `T / (6d)` | 0,0417 |

Parametre sayısı `Blok(512, 8, "pre", 0.0, False)` ile kodda da `3 153 408` çıkar. Toplam MAC sayısındaki `402 653 184 + 16 777 216 = 419 430 400` değeri tablodakiyle aynıdır.

**Bunu AI'sız yazabilir misin?** Aynı bloğu `T = 8 192` için düşün. Hangi terim baskın olur, karesel attention mi yoksa doğrusal katmanlar mı? Oranı formülle hesapla ve nedenini bir cümleyle açıkla.

## Kendin Yap Projeleri

::: dikkat
Bu iki projede önce kendi çözümünü yaz. Yapay zekâ aracını yalnızca bitirdikten sonra kodu okumak ya da bir hatayı bulmak için kullan. Bu bölümü geçmek için değil, bu bölümü öğrenmek için yapıyorsun.
:::

### Proje 1 (★★): Sıfırdan karakter düzeyinde mini-GPT

**Amaç.** Bu bölümdeki `tr69.py` kütüphanesini kullanmadan, boş bir dosyada bir decoder-only dil modeli yaz. Model, karakter düzeyinde çalışsın ve kitabın kendi metninde eğitilsin. Çok başlı nedensel attention, Transformer bloğu, KV önbellekli üretim ve sıcaklık ile top-k örneklemesi içersin.

**Yapılacak ve beklenen davranış.** Model şunları yapabilmeli: (a) bir metin dizisini alıp her konum için bir sonraki karakterin olasılıklarını vermek; (b) eğitim kaybını ve doğrulama perplexity'sini kaydetmek; (c) önbelleksiz ve önbellekli üretimin aynı belirteç dizisini vermesi (rastgele ağırlıklarla, sabit tohumla); (d) üretimde sıcaklık ve top-k parametrelerini komut satırından almak. Doğrulama kümesi yalnızca hiperparametre seçimi için kullanılmalı; test kümesi son raporda, bir kez kullanılmalı.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Önce tek bir attention katmanını sıfırdan yaz ve Bölüm 69.3'teki NumPy programının çıktılarıyla eşleştir. Sonra çok başlı hâline geçir ve `nn.MultiheadAttention` ile aynı ağırlıklarla karşılaştır. Bloğu tek başına kurup gradyanı sonlu farklarla kontrol et; küçük bir ağda bu kontrol, hataların çoğunu yakalar. Nedensel maskeyi bir kez oluşturup yeniden kullan. KV önbelleğinde yalnızca yeni belirtecin `q`'sunu hesapla; `k` ve `v` önbellekten gelsin. Üretimde `softmax`ten önce logit'leri sıcaklığa böl ve top-k dışındaki değerleri `−∞` yap.

**Başarı kriterleri.** (1) Tek başlı attention, NumPy gerçeklemesiyle `10⁻¹²`nin altında eşleşir. (2) Çok başlı attention `nn.MultiheadAttention` ile aynı ağırlıklarda `10⁻¹²`nin altında eşleşir. (3) Gradyan kontrolü her parametre grubu için göreli hata `10⁻⁵`in altındadır. (4) Önbellekli ve önbelleksiz üretim 200 belirtek boyunca birebir aynı dizi üretir. (5) Doğrulama perplexity'si, bigram taban çizgisi ile birlikte, beş tohumun ortalaması ve sapmasıyla raporlanır.

### Proje 2 (★★★): Çok değişkenli telemetri için Transformer ile tahmin

**Amaç.** Bölüm 68'de LSTM ve TCN ile kurduğun sentetik İHA telemetri tahmin problemini aynı veriyle yeniden çöz ve bir Transformer kodlayıcısı ile karşılaştır. Girdi çok değişkenli bir zaman serisi olsun (irtifa, hız, yatış açısı, motor sıcaklığı gibi kanallar); çıktı, gelecek `H` adımdaki değerler olsun.

**Yapılacak ve beklenen davranış.** Veriyi Bölüm 68'de kullandığın zaman sıralı bölmeyle ayır: eğitim, doğrulama ve test zamanda ardışık olsun, karıştırılmasın. Kodlayıcıda konum kodlamasını (sinüzoidal ya da RoPE) seç ve her seçimi ayrı ayrı raporla. Metrikler Bölüm 68'deki metriklerle aynı olsun (RMSE ve MAE gibi); sonuçları aynı tohum sayısı ve aynı bölmede karşılaştır. Bir Transformer'ın bu kadar kısa bağlamlı bir görevde LSTM'den üstün olup olmadığını, sapmayla birlikte cevapla.

**Önerilen yaklaşım (ipucu).** Her zaman adımını bir belirteç gibi düşün: girdiyi `d` boyutuna doğrusal olarak projekte et, sonra konum kodlaması ekle. Veri sızıntısı, bu problemde en büyük tuzaktır: normalizasyon istatistiklerini yalnızca eğitim penceresinden hesapla ve pencereleri, hedefleri gelecekten kesmeyecek biçimde kur. Nedensel maskeyi tahmin görevinde kullan, aksi halde model gelecek değerleri görür. Test kümesini tek bir kez kullan.

**Başarı kriterleri.** (1) Veri sızıntısı denetimi: normalizasyon istatistikleri yalnızca eğitim penceresinden hesaplanmış ve nedensel maske uygulanmış. (2) Test RMSE ve MAE, LSTM taban çizgisi ile birlikte, beş tohumun ortalaması ve sapmasıyla. (3) Konum kodlaması karşılaştırması: sinüzoidal ve RoPE, aynı mimari ve aynı eğitim bütçesiyle. (4) Eğitim kaybı ile doğrulama kaybı eğrisi ayrı raporlanmış, aşırı uydurma yorumu bu eğrilere dayanarak yapılmış. (5) Raporun sonunda, Transformer'ın bu veride neden ya da neden üstün olmadığını açıklayan bir paragraf.

### Ek Alıştırmalar

Aşağıdaki problemler kademelidir. ★ olanlar kavramı yoklar, ★★ olanlar bir türetme ya da küçük bir hesap ister, ★★★ olanlar birden çok konuyu birleştirir. Mülakat etiketli olanlar klasik sorulardır.

1. ★ `T = 10` belirteçli, `d = 16`, `h = 4` bir çok başlı attention için her başın `d_k`sını ve tek bir başın skor matrisinin boyutunu yaz. Tüm başların skor matrislerinin toplam eleman sayısı nedir?
2. ★ `d_k = 64` iken, `q` ve `k` vektörlerinin bileşenleri ortalaması 0, varyansı 1 olan bağımsız sayılar ise, `q·k`nın standart sapması nedir? Bölçekleme olmadan, bu skorlarla softmax'ın en büyük ağırlığının kabaca hangi değere yaklaşacağını tahmin et ve nedenini söyle. (Mülakat)
3. ★ Nedensel maske `T = 5` için kaç hücreyi `−∞` yapar? Dolgu maskesi, uzunluğu `3` olan bir dizi `T = 5` için kaç hücreyi kapatır? Her iki sayıyı formülle çıkar.
4. ★ `softmax` fonksiyonunu `z − max(z)` ile hesaplamanın matematiksel olarak neden değişmediğini göster. Hangi sayısal sorunu önler? (Mülakat)
5. ★★ Sinüzoidal kodlamada `PE(t)·PE(t+k)` nokta çarpımının yalnızca `k`ye bağlı olduğunu, Örnek 3'teki `cos(k ω_i)` toplamından yola çıkarak göster.
6. ★★ Bir RoPE döndürmesinde açı `m θ_i` olarak tanımlandığında, `(R_m q)ᵀ(R_n k) = qᵀ R_{n−m} k` özdeşliğini iki boyutlu bir çift için açıkça doğrula.
7. ★★ Pre-norm bir bloğun `z = x + F(LN(x))` olduğunu varsay. `∂z/∂x = I + ∂F/∂x · ∂LN/∂x` olduğunu zincir kuralıyla göster ve artık yolun gradyanı neden sönümlemediğini açıkla. (Mülakat)
8. ★★ Dört belirteçli bir dizide, nedensel maskeli attention'ın ilk satırının ağırlığı neden her zaman `1` olur? Son satırın ağırlıklarının toplamı neden yine `1` olur?
9. ★★ Çok başlı attention'da başlar sayısını `h = 1`den `h = 8`e çıkarmak `W_Q`, `W_K`, `W_V`, `W_O` parametre sayısını değiştirir mi? Her başın `d_k`sı ile skor matrisinin boyutu nasıl değişir?
10. ★★★ Bir Transformer'da `T = 4096`, `d = 768`, `h = 12` olsun. Tek bir katmanda attention skor matrisinin bellek tüketimini (float32) MB olarak hesapla ve bu değerin neden eğitimde `T²` ile büyüdüğünü açıkla. (Mülakat)
11. ★★★ Otoregresif üretimde KV önbelleği kullanılmadan `N` belirteç üretmek, `N` adım boyunca her adımda tüm diziyi yeniden işlemek demektir. Bu toplam işin `N` cinsinden kabaca büyüklüğünü ve önbellekle azalan kısmını yaz. (Mülakat)
12. ★★★ Bir modelin doğrulama perplexity'si düşüyor, ama üretilen metin tekrar eden kalıplarla dolu. Bu durumu hangi üç deneyle ayırt edersin ve sıcaklık ile top-k'nın bu soruna etkisi nedir? (Mülakat)

## Kod Okuma Egzersizi: PyTorch'un attention'ı

Bu bölümde attention'ı sıfırdan yazdık. Şimdi aynı işlemin gerçek bir kütüphanede nasıl yazıldığına bakalım. Kaynak, kurulu PyTorch 2.6.0 (`torch 2.6.0+cu124`) sürümünün `torch/nn/functional.py` dosyasıdır; yerel yol `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\torch\nn\functional.py`. Üç kesit aldık: birincisi `scaled_dot_product_attention` belgelerinde verilen referans gerçekleme (satır 5731–5757), ikincisi ve üçüncüsü `multi_head_attention_forward` fonksiyonunun projeksiyon ve başlara bölme (satır 6226–6230 ve 6294–6298) ile birleştirme (satır 6378–6384) adımları.

Kaynak satırlarının çoğu 70 sütunu aştığı için satırları parantez içinde kırdık ve girintileri başlangıç sütununa kaydırdık. Kırılmış her kesitin ayrıştırılmış ağacının (AST) orijinaliyle özdeş olduğunu doğruladık; yorumlar bu karşılaştırmanın dışında tutuldu. Kesitlerdeki `else` dalları ve yorumların bir kısmı, okunabilirlik için atlandı; atlanan yerleri aşağıda belirtiyoruz.

Birinci kesit, referans gerçeklemenin tamamıdır. Belgelerde verilen açıklama, kütüphanenin verimli çekirdeklerinin (C++ ve CUDA) aynı matematiği yaptığını söylüyor.

```python
# Efficient implementation equivalent to the following:
def scaled_dot_product_attention(query, key, value,
        attn_mask=None, dropout_p=0.0,
        is_causal=False, scale=None,
        enable_gqa=False) -> torch.Tensor:
    L, S = query.size(-2), key.size(-2)
    scale_factor = (1 / math.sqrt(query.size(-1))
                    if scale is None else scale)
    attn_bias = torch.zeros(L, S, dtype=query.dtype,
                            device=query.device)
    if is_causal:
        assert attn_mask is None
        temp_mask = (torch.ones(L, S, dtype=torch.bool)
                     .tril(diagonal=0))
        attn_bias.masked_fill_(temp_mask.logical_not(),
                               float("-inf"))
        attn_bias.to(query.dtype)

    if attn_mask is not None:
        if attn_mask.dtype == torch.bool:
            attn_bias.masked_fill_(attn_mask.logical_not(),
                                   float("-inf"))
        else:
            attn_bias = attn_mask + attn_bias

    if enable_gqa:
        key = key.repeat_interleave(query.size(-3) //
                                    key.size(-3), -3)
        value = value.repeat_interleave(query.size(-3) //
                                        value.size(-3), -3)

    attn_weight = query @ key.transpose(-2, -1) * scale_factor
    attn_weight += attn_bias
    attn_weight = torch.softmax(attn_weight, dim=-1)
    attn_weight = torch.dropout(attn_weight, dropout_p,
                                train=True)
    return attn_weight @ value
```

Bu kodda üç şey bizim gerçeklememizle birebir eşleşir: ölçek `1/√d_k`, satır bazında `softmax` ve son `A·V`. Fark, maske yönetiminde ortaya çıkar. Burada maske iki biçimde gelir: bool (`True` görülebilir) ya da float (eklenen bir değer). Bool maske `logical_not` ile `−∞`a çevrilir, float maske doğrudan eklenir. Bizim kodumuz yalnızca bool maske kullanıyordu. `enable_gqa` ve `repeat_interleave` ise sorgu başlarının sayısının anahtar-değer başlarından fazla olduğu durumlar içindir (gruplandırılmış sorgu dikkati); bu, Bölüm 71'deki bellek tasarrufunun bir parçasıdır.

İkinci kesit, `multi_head_attention_forward`'da paketli projeksiyonun kullanımıdır. Bu fonksiyon `nn.MultiheadAttention` tarafından çağrılır ve tek bir `in_proj_weight` matrisi (`3d × d`) ile Q, K, V'yi tek bir çarpımla hesaplar. Bizim `tr69.py` kütüphanesinde üç ayrı `nn.Linear` vardı; bu iki yaklaşım matematiksel olarak aynıdır, yalnızca ağırlıkların paketlenmesi farklıdır. Testte bu eşdeğerliği kullandık (`g03`).

```python
if not use_separate_proj_weight:
    assert (
        in_proj_weight is not None
    ), ("use_separate_proj_weight is False but "
        "in_proj_weight is None")
    q, k, v = _in_projection_packed(query, key, value,
                                    in_proj_weight, in_proj_bias)
# else dalı bu kesitte atlandı
```

Üçüncü kesit, başlara bölme ve Q, K, V'nin yeniden şekillendirilmesidir. Burada `view` ve `transpose` sırası bizden farklıdır: kütüphane `(T, B·h, d_k)` düzenini kullanır ve baş boyutunu batch ile birleştirir. Bizim `_bol` fonksiyonu `(B, h, T, d_k)` düzenini kullanır. İki düzen de aynı sonucu verir; fark, `nn.MultiheadAttention`'ın varsayılan `batch_first=False` düzeninden gelir (`T` ilk boyuttadır).

```python
# reshape q, k, v for multihead attention and make them
# batch first
q = q.view(tgt_len, bsz * num_heads, head_dim).transpose(0, 1)
if static_k is None:
    k = k.view(k.shape[0], bsz * num_heads,
               head_dim).transpose(0, 1)
# else dalı bu kesitte atlandı
```

Dördüncü kesit, başların birleştirilmesi ve çıkış projeksiyonudur. Kesitin başında `attn_output_weights`'in bmm ile `v`ye çarpılması vardır; bu, bizim `A @ v` satırımızın karşılığıdır.

```python
attn_output = torch.bmm(attn_output_weights, v)

attn_output = (
    attn_output.transpose(0, 1).contiguous()
    .view(tgt_len * bsz, embed_dim)
)
attn_output = linear(attn_output, out_proj_weight,
                     out_proj_bias)
attn_output = attn_output.view(tgt_len, bsz,
                               attn_output.size(1))
```

Birleştirme adımında `.contiguous()` çağrısı, Bölüm 65'te gördüğün bellek düzeni meselesidir: `transpose` sonrası bellek bitişik değildir ve `view` bunu doğrudan yapamaz. `contiguous` veriyi bitişik bir düzene kopyalar. Bizim `reshape` çağrımız bunu gerektiğinde kendisi yapar; sonuç aynıdır, ama kopyalamanın nerede olduğunu bilmek, profil çıkardığında önemlidir.

**Sorular — cevaplamadan geçme:**

1. Referans gerçeklemede ölçek, `query @ key.transpose(-2, -1) * scale_factor` ile uygulanır; bizim kodumuzda `q @ k.T / √d_k` vardır. Bu iki sıra arasında sayısal bir fark olabilir mi? Neden, ve hangi durumda önemli olur?
2. `attn_bias.masked_fill_(temp_mask.logical_not(), float("-inf"))` satırında bool maske neden tersine çevrilir? `True` ile hangi hücreler gösterilir ve bu bizim `tr69.py` kütüphanesindeki maske kuralıyla nasıl karşılaştırılır?
3. Referans kodda `attn_weight += attn_bias` bir yerinde (in-place) toplamadır. Autograd, bu tür bir işlemi nasıl izler ve bir gradyan hatasına yol açabilir mi?
4. `multi_head_attention_forward` içinde `q.view(tgt_len, bsz * num_heads, head_dim).transpose(0, 1)` sonrası şekil nedir? Bizim `_bol` çıktısıyla karşılaştır ve hangi boyutların yer değiştirdiğini say.
5. Birleştirmede `attn_output.transpose(0, 1).contiguous().view(tgt_len * bsz, embed_dim)` ifadesinde `contiguous` neden gerekli? Bu satır olmadan `view` hangi hatayı verir ve bu hatanın ne zaman ortaya çıktığını Bölüm 65'teki stride bilgisiyle açıkla.
6. Kütüphanede `dropout` yalnızca attention ağırlıklarına uygulanır (`attn_output_weights`). Bizim blok çıktısında dropout vardı, attention ağırlıklarında yoktu. Bu iki yerleşimin düzenlileştirme etkisi nasıl farklıdır?

## Bölüm Özeti

- RNN encoder–decoder'ında tüm girdi tek bir bağlam vektörüne sıkışır ve zincir sıralı hesaplanır. Dikkat, çıktının her adımında girdinin bütün konumlarına ağırlıklı bir bakış sağlar ve eğitimi paralel hâle getirir.
- Attention üç rolle çalışır: sorgu, anahtar ve değer. Skor `QKᵀ / √d_k` ile hesaplanır, satır bazında softmax ağırlığa dönüşür, sonuç `A·V`dir. Ölçekleme, skorun varyansını `d_k`dan bağımsız tutar; ölçeksiz softmax yüksek `d_k`de doyar ve gradyan sıfıra iner.
- Nedensel maske gelecek konumları `−∞` yapar ve geçmişin çıktısını değişmez kılar. Dolgu maskesi, dizi uzunlukları arasındaki farkı yok sayar. Tüm konumları kapatan bir satır NaN üretir; bunu denetlemek gerekir.
- Çok başlı attention, `d`yi `h` paralel alt uzaya böler. Parametre sayısı başlardan bağımsızdır (`4(d² + d)`), her baş kendi ağırlık dağılımını öğrenir. Bölme ve birleştirme view ve transpose ile yapılır; birleştirmede kopyalama gerekebilir.
- Attention permütasyon eşdeğişkendir: sırayı bilmez. Sinüzoidal kodlama, RoPE ve öğrenilen gömmeler bu bilgiyi farklı yollarla verir. RoPE, skoru yalnızca göreli konuma bağlar; sinüzoidal kodlamada nokta çarpım yalnızca farka bağlıdır. Ters çevirme deneyinde konumsuz model görevi çözemedi; ama eğitim aralığının (4–12) dışında hiçbir konum kodlaması genelleme göstermedi, RoPE dahil. Uzunluk genellemesi, ayrı bir çözüm gerektiren açık bir sorundur.
- Transformer bloğu, attention ve MLP'yi artık bağlantılar ve LayerNorm ile birleştirir. Pre-norm, artık yolu temiz tuttuğu için derin ağlarda daha kararlıdır.
- Encoder, decoder ve encoder–decoder aileleri, maskenin ve eğitim görevinin farklı kombinasyonlarıdır. Çapraz dikkat, decoder'ın kaynağın tamamına her adımda bakmasını sağlar.
- Attention'ın maliyeti `T` ile karesel büyür (zaman ve skor matrisi belleği). Otoregresif üretimde KV önbelleği, her adımda eski `k` ve `v`yi yeniden hesaplamayı önler ve çıktıyı değiştirmez.

**Sonraki bölümde:** Bölüm 70, NLP ve dil modelleri, bu bölümde kurduğumuz decoder-only yapıyı metne uygular. Tokenization (BPE gibi alt-kelime yöntemleri), kelime gömmeleri, ön eğitim, ince ayar ve LoRA gibi verimli ince ayar yöntemleri orada ele alınacak. Bu bölümde karakter düzeyinde kurduğumuz küçük model, Bölüm 70'te alt-kelime belirteçlerle yeniden kurulacak.

::: mulakat
1. Attention'da ölçekleme `√d_k` neden gereklidir? Skorların varyansı ile softmax'ın doygunluğu ve gradyanı arasındaki bağlantıyı açıkla.
2. Nedensel maske bir eğitim sırasında nasıl uygulanır ve neden bir çarpma yerine `−∞` eklemesi tercih edilir? Tüm hücreleri maskelenmiş bir satır ne üretir?
3. Attention'ın hesaplama ve bellek maliyeti `T` ile nasıl ölçeklenir? Hangi terim baskındır ve bu maliyeti azaltmak için hangi yaklaşımlar vardır?
4. Konumsal kodlama neden gereklidir? Attention'ın permütasyon eşdeğişkenliğini bir cümleyle ifade et ve sinüzoidal kodlama ile RoPE arasındaki temel farkı anlat.
5. Çok başlı attention'ın tek başlıya göre avantajı nedir? Başlar parametre sayısını nasıl etkiler ve neden birbirinden bağımsız çalışırlar?
6. KV önbelleği nedir? Otoregresif üretimde neyi saklar, neden çıktıyı değiştirmez ve bellek bedeli nasıl hesaplanır?
7. Pre-norm ile post-norm arasındaki fark nedir? Hangisi eğitimde neden daha kararlıdır ve gradyanın artık yoldan akışı bunu nasıl açıklar?
8. Transformer neden RNN'den daha hızlı eğitilir, ama uzun dizilerde bir bedeli vardır? Bu iki gözlemi tek bir hesaplama modeliyle açıkla.
:::
