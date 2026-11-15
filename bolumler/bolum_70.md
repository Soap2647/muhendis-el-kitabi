%% kisim_no: XV
%% kisim_ad: Derin Öğrenme
%% bolum_no: 70
%% baslik: NLP & Dil Modelleri

## Giriş: Dil, sayılara çevrilince bir model olur

Bilgisayarın dünyada gördüğü tek şey sayılardır. Bir fotoğraf piksel değerlerinden, bir sensör telemetrisi ölçümlerden oluşur. Dil ise sayı değildir: harfler, kelimeler, noktalama ve anlam vardır. Bu bölümde şunu soruyoruz: bir metni sayılara çevirdiğimizde, o sayılardan bir sonraki kelimeyi tahmin etmeyi öğrenebilir miyiz? Cevap evet, ama bu iki adımın her birinde kararlar gerekir. Önce metin nasıl parçalanacak (tokenizasyon), sonra her parça nasıl bir vektöre dönecek (gömme) ve son olarak bu vektörler hangi görevle eğitilecek (dil modelleme) sorusu cevaplanmalıdır.

Bu sorular mülakatta çok sık çıkar. "BPE nasıl çalışır?", "perplexity nedir?", "LoRA neden az parametreyle çalışır?", "sıcaklık ve top-p örneklemesi çıktıyı nasıl değiştirir?" gibi sorular, büyük dil modelleri üzerine yapılan her projede ve her ürün görüşmesinde karşına çıkar. Savunma sanayiinde de benzer bir ihtiyaç vardır: bir operatörün yazılı raporlarını, bakım kayıtlarını ya da istihbarat metinlerini sınıflandırmak, özetlemek ya da içinde arama yapmak. Bu işleri yapan sistemlerin çoğu bu bölümde kurduğumuz parçaların bir çeşididir.

Bölüm 69'da dikkat mekanizmasını ve Transformer bloğunu, karakter düzeyinde bir decoder-only modeli ve KV önbelleği gördük. Burada aynı mimariyi kullanacağız, ama iki fark var. Birincisi girdi: karakter yerine BPE ile öğrenilmiş alt-sözcük parçaları. İkincisi amaç: sadece bir metni taklit etmek değil, metnin kendi içinde ne kadar öngörülebilir olduğunu ölçmek ve bu öngörülebilirliği başka bir göreve aktarmak. Bunun için önce "sayım" tabanlı klasik yöntemleri (kelime torbası, TF-IDF, n-gram) kuracağız; sonra onların sınırlarını göreceğiz ve GPT'ye geçeceğiz.

Bu bölümdeki her deneyin verisi, kitabın kendi metnidir: 67 bölümün Türkçe düz metni. Bu seçim bilerek yapıldı. Kitabın metni bizim elimizde, telif sorusu taşımıyor ve bir dilin gerçek, teknik ve tutarlı bir örneğini veriyor. Ancak bu tek bir kitabın dili, bir dil modelinin genel dil bilgisine kıyasla çok küçük ve dar. Bu yüzden sonuçlar, büyük modellerin mutlak değerleri olarak değil, yöntemlerin nasıl davrandığını gösteren ölçüler olarak okunmalı. Her sayıyı, onu üreten kodla birlikte veriyoruz.

::: not
Bu bölümdeki bütün ölçümler tek bir derlem üzerinde yapıldı: kitabın 67 bölümünün paragrafları. Bölümler, bölüm numarasının 7'ye göre kalanıyla eğitim, doğrulama ve test olarak ayrıldı; böylece aynı bölümün cümleleri iki kümeye birden düşmedi. Derlem bir anlık görüntüdür: kitabın bölümleri değiştikçe sayılar da değişir. Ölçümler, Bölüm 65 metninin o günkü sürümü ile yapıldı; metinde değişiklik yapıldığında sayılar yeniden üretilmelidir.
:::

### Veri: kitabın kendi metni ve bölme

Derlem, kitabın 67 bölümünden çıkarılır. Önce işaretleme temizlenir: kod blokları, tablolar, şekil satırları, kutu işaretleri ve kalın/italik yıldızları atılır; kalan düz metin paragraflara ayrılır ve en az 150 karakterlik paragraflar alınır. Her paragraf, bölüm numarası ve kısım etiketi (`%% kisim_no`) ile birlikte tutulur. Bölme, bölüm numarasının 7'ye göre kalanıyla yapılır: kalanı 3 olan bölümler test, 5 olanlar doğrulama, geri kalanı eğitim kümesidir. Böylece bir bölümün paragrafları iki kümeye birden düşmez.

`g01_korpus.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""
Bölüm 70 - Derlem hazırlığı: kitabın kendi metninden düz metin
külliyatı.

Kullanım:  python g01_korpus.py
Çıktılar (bu klasörde):
  paragraflar.json : [{"n": bölüm, "kisim": 0..14, "metin": "..."}]
  bolum_bolme.json : {"egitim": [...], "dogrulama": [...], "test":
  [...]}
Bölme bölüm düzeyindedir: n % 7 == 3 test, n % 7 == 5 doğrulama,
kalanı eğitim.
Böylece aynı bölümün paragrafları iki kümeye birden düşmez (sızıntı
yok).
"""

import glob
import json
import os
import re

KITAP = "D:/Mevcut Projeler/Kitap/bolumler"
KLASOR = os.path.dirname(os.path.abspath(__file__))
ROMEN = [
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "XI",
    "XII",
```

`g01_korpus.py`, 37–72. satırlar:

```python
    "XIII",
    "XIV",
    "XV",
    "XVI",
]
# Snapshot: yalnızca bu tarihte var olan bölümler (68, 69, 70
# yazılıyor).
BOLUMLER = list(range(1, 68))


def temizle(md):
    """İşaretlemeyi at; yalnızca doğal dil cümlelerini bırak."""
    satirlar = []
    kod = False
    for s in md.splitlines():
        if s.startswith("```"):
            kod = not kod
            continue
        if kod:
            continue
        t = s.strip()
        if not t or t.startswith("%%") or t.startswith("|"):
            continue
        if t.startswith("![") or t.startswith("---"):
            continue
        if t.startswith("::: ") or t == ":::":
            continue
        if t.startswith("#"):
            t = t.lstrip("#").strip()
        t = re.sub(r"https?://\S+", " ", t)
        t = re.sub(r"`([^`]*)`", r"\1", t)
        t = re.sub(r"\*\*?([^*]+)\*\*?", r"\1", t)
        t = re.sub(
            r"\$[^$]*\$", " ", t
        )  # satır içi LaTeX yoksa bile güvenli
        t = re.sub(r"^\s*(\d+\.|-)\s+", "", t)
```

`g01_korpus.py`, 73–108. satırlar:

```python
        satirlar.append(t)
    metin = "\n".join(satirlar)
    metin = re.sub(r"[ \t]+", " ", metin)
    return metin


def kisim_no(md):
    m = re.search(r"%% kisim_no:\s*([IVXL]+)", md)
    if not m:
        return None
    return ROMEN.index(m.group(1))


def main():
    paragraflar = []
    for n in BOLUMLER:
        yol = os.path.join(KITAP, "bolum_%02d.md" % n)
        md = open(yol, encoding="utf-8").read()
        k = kisim_no(md)
        assert k is not None, n
        metin = temizle(md)
        for p in metin.split("\n"):
            p = p.strip()
            if len(p) >= 150:
                paragraflar.append({"n": n, "kisim": k, "metin": p})
    bolme = {"egitim": [], "dogrulama": [], "test": []}
    for i, p in enumerate(paragraflar):
        r = p["n"] % 7
        anahtar = (
            "test"
            if r == 3
            else ("dogrulama" if r == 5 else "egitim")
        )
        bolme[anahtar].append(i)
    with open(
        os.path.join(KLASOR, "paragraflar.json"),
```

`g01_korpus.py`, 109–144. satırlar:

```python
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(paragraflar, f, ensure_ascii=False)
    with open(
        os.path.join(KLASOR, "bolum_bolme.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(bolme, f)
    # Düz metin külliyatı: eğitim+doğrulama+test bölümlerinin
    # birleşimi (ayrı dosyalar)
    for anahtar in ("egitim", "dogrulama", "test"):
        with open(
            os.path.join(KLASOR, "korpus_%s.txt" % anahtar),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(
                "\n".join(
                    paragraflar[i]["metin"] for i in bolme[anahtar]
                )
            )
    print("paragraf:", len(paragraflar))
    for anahtar in bolme:
        ch = sum(len(paragraflar[i]["metin"]) for i in bolme[anahtar])
        print(
            "%-10s paragraf=%6d karakter=%9d"
            % (anahtar, len(bolme[anahtar]), ch)
        )
    kis = {}
    for p in paragraflar:
        kis[p["kisim"]] = kis.get(p["kisim"], 0) + 1
    print(
        "kısım dağılımı (paragraf):",
        [kis.get(k, 0) for k in range(15)],
```

`g01_korpus.py`, 145–149. satırlar:

```python
    )


if __name__ == "__main__":
    main()
```


Çıktı (`cikti_g01.txt`):

```term
paragraf: 10738
egitim     paragraf=  7716 karakter=  2419957
dogrulama  paragraf=  1509 karakter=   465070
test       paragraf=  1513 karakter=   481105
kısım dağılımı (paragraf):
[444, 217, 495, 1155, 652, 906, 674, 544, 422, 913, 655, 980,
 311, 1479, 891]
```


Derlem 10 738 paragraftan oluşur; eğitim kümesi 7 716 paragraf ve yaklaşık 2,42 milyon karakter, doğrulama ve test kümeleri ise yaklaşık 0,47 ve 0,48 milyon karakterdir. Kısım dağılımı dengesizdir: Kısım XIV en çok paragrafa (1 479) sahiptir, Kısım II en az (217). Bu dengesizlik, sınıflandırma görevinde ayrıca önem taşıyacaktır.

Tokenizer ve tüm dil modelleri yalnızca eğitim kümesinden öğrenir. Belirteç dizileri aşağıdaki betikle üretilir; bu betik 70.4'te anlatılan BPE'yi kullanır.

`g03_tok_hazirla.py` dosyasının tamamı (34 satır):

```python
# -*- coding: utf-8 -*-
"""Bölüm 70 - GPT ve n-gram için ortak tokenizer ve token dizileri.

Tokenizer yalnızca EĞİTİM bölümlerinden öğrenilir (sızıntı yok).
Sözlük: alfabe 245 + birleştirme 1903 + <unk> = 2149.
Çıktılar: bpe_b70.json, tok_egitim.npy, tok_dogrulama.npy,
tok_test.npy
"""

import json, os
import numpy as np
from bpe_sifirdan import BPE

K = os.path.dirname(os.path.abspath(__file__))
oku = lambda a: open(os.path.join(K, a), encoding="utf-8").read()
egitim = oku("korpus_egitim.txt")
b = BPE(egitim, 1903)
print("sözlük boyutu (unk dahil):", b.boyut())
json.dump(
    {"alfabe": b.alfabe, "kurallar": b.kurallar},
    open(os.path.join(K, "bpe_b70.json"), "w", encoding="utf-8"),
    ensure_ascii=False,
)
for ad, dosya in [
    ("egitim", "korpus_egitim.txt"),
    ("dogrulama", "korpus_dogrulama.txt"),
    ("test", "korpus_test.txt"),
]:
    ids = np.array(b.kodla(oku(dosya)), dtype=np.uint16)
    np.save(os.path.join(K, "tok_%s.npy" % ad), ids)
    print(
        "%-10s token=%d  unk=%d"
        % (ad, len(ids), int((ids == b.unk).sum()))
    )
```


Çıktı (`cikti_g03.txt`):

```term
sözlük boyutu (unk dahil): 2149
egitim     token=782840  unk=0
dogrulama  token=152185  unk=44
test       token=157868  unk=5
```


Dil karşılaştırması için, yerel Python kurulumunun belgeleri ve paket README dosyaları İngilizce bir külliyat olarak kullanılır. Bu metin, bölümdeki Türkçe ölçümlerin karşısına konan bir karşılaştırma verisidir; İngilizce modellemesi yapılmaz.

`g01b_en.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""Karşılaştırma için İngilizce düz metin.
Kaynaklar (yerel kurulum): Python 3.12 pydoc_data/topics.py (dil
belgesi;
yalnızca girintisiz düz cümleler alınır) ve site-packages altındaki
README/RST belgeleri (kod blokları atılır). Çıktı: korpus_en.txt"""

import glob, os, re

PY = "C:/Users/merty/AppData/Local/Programs/Python/Python312/Lib"
KOK = PY + "/site-packages"
parcalar = []
import sys

sys.path.insert(0, PY)
import pydoc_data.topics as tp

for metin in tp.topics.values():
    satirlar = [
        s
        for s in metin.splitlines()
        if s and not s.startswith(" ") and not s.startswith("\t")
    ]
    parcalar.append(" ".join(satirlar))
for yol in sorted(
    glob.glob(KOK + "/**/*.md", recursive=True)
    + glob.glob(KOK + "/**/*.rst", recursive=True)
):
    try:
        s = open(yol, encoding="utf-8").read()
    except Exception:
        continue
    s = re.sub(r"```.*?```", " ", s, flags=re.S)
    s = re.sub(r"`[^`]*`", " ", s)
    s = re.sub(r"https?://\S+", " ", s)
    harf = sum(c.isascii() and c.isalpha() for c in s)
```

`g01b_en.py`, 37–48. satırlar:

```python
    if len(s) >= 500 and harf / max(1, len(s)) >= 0.7:
        parcalar.append(re.sub(r"[ \t]+", " ", s))
metin = re.sub(r"[ \t]+", " ", "\n".join(parcalar))
metin = re.sub(r"\n\s*\n+", "\n", metin)[:1000000]
open(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "korpus_en.txt"
    ),
    "w",
    encoding="utf-8",
).write(metin)
print("karakter", len(metin))
```


Çıktı (`cikti_g01b.txt`):

```term
karakter 521716
```


## 70.1 Metni sayıya çevirmek: kelime torbası ve TF-IDF

En basit fikir şudur: bir belgeyi, içindeki kelimelerin sayılarından oluşan bir vektörle temsil et. Bu fikre **kelime torbası** (bag of words) denir. Belgenin kelime sırası atılır; yalnızca hangi kelimeden kaç tane olduğu tutulur. "Dil modeli bir sonraki kelimeyi tahmin eder" ile "bir sonraki kelimeyi tahmin eder dil modeli" aynı torbaya düşer. Bu kayıp, bilgi kaybıdır. Ama sınıflandırma gibi birçok görevde şaşırtıcı derecede iyi çalışır, çünkü belgenin konusu çoğu zaman kelime seçiminde gizlidir.

Kelime torbasının bir sorunu var: sık geçen kelimeler ("ve", "bir", "bu") her belgede büyük sayılar alır ama bir belgeyi ayırt etmek için bir işe yaramazlar. **TF-IDF** bu sorunu çözer. İki parçası vardır. **TF** (terim frekansı), kelimenin belgedeki sayısıdır. **IDF** (ters belge frekansı), kelimenin kaç belgede geçtiğine bakar: az belgede geçen kelime daha bilgilendiricidir. Sklearn'ün varsayılanında bu, şöyle yazılır:

idf(t) = ln((1 + n) / (1 + df(t))) + 1

Burada `n` eğitimdeki belge sayısı, `df(t)` kelime `t`'nin geçtiği belge sayısıdır. Her belgenin vektörü `tf(t, d) · idf(t)` değerlerinden oluşur ve son olarak L2 normuna bölünür. Normlama, uzun belgelerin kelime sayısı yüzünden daha büyük vektörler üretmesini engeller. Kosinüs benzerliğini (Bölüm 48) kullandığımızda normlu vektörler işimizi kolaylaştırır.

Aşağıdaki betik TF-IDF'i sıfırdan yazar ve sklearn'ün `TfidfVectorizer` sınıfıyla karşılaştırır. Aynı görev için TF-IDF üzerinde bir lojistik regresyon (Bölüm 58) baseline'ı kurar. Görev, bir paragrafın kitabın hangi kısmından (Kısım I–XV) geldiğini tahmin etmektir. Etiket, her bölümün `%% kisim_no` ön bilgisinden alınır. Eğitim ve test bölümleri ayrıdır; bu yüzden model, test bölümlerini görmeden tahmin yapar.

`g07_tfidf.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""Bölüm 70 - Kelime torbası ve TF-IDF, sıfırdan; sklearn ile eşleşme;
aynı görev için TF-IDF + lojistik regresyon (baseline)."""

import json, math, os, re
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

K = os.path.dirname(os.path.abspath(__file__))
par = json.load(
    open(os.path.join(K, "paragraflar.json"), encoding="utf-8")
)
bol = json.load(
    open(os.path.join(K, "bolum_bolme.json"), encoding="utf-8")
)


def kucuk(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def belirtec(s):
    return re.findall(r"(?u)\b\w\w+\b", kucuk(s))


tr_m = [par[i]["metin"] for i in bol["egitim"]]
te_m = [par[i]["metin"] for i in bol["test"]]
ytr = np.array([par[i]["kisim"] for i in bol["egitim"]])
yte = np.array([par[i]["kisim"] for i in bol["test"]])


# --- Sıfırdan kelime torbası + TF-IDF (sklearn varsayılanı: smooth
# idf, l2) ---
```

`g07_tfidf.py`, 37–72. satırlar:

```python
def tfidf_fit(docs):
    kelimeler = sorted({w for d in docs for w in set(belirtec(d))})
    dizin = {w: j for j, w in enumerate(kelimeler)}
    n = len(docs)
    df = Counter(w for d in docs for w in set(belirtec(d)))
    idf = np.array(
        [math.log((1 + n) / (1 + df[w])) + 1 for w in kelimeler]
    )
    return dizin, idf


def tfidf_donustur(docs, dizin, idf):
    X = np.zeros((len(docs), len(dizin)))
    for i, d in enumerate(docs):
        for w, c in Counter(belirtec(d)).items():
            if w in dizin:
                X[i, dizin[w]] = c
    X = X * idf
    norm = np.sqrt((X**2).sum(1, keepdims=True))
    return X / np.where(norm == 0, 1, norm)


dizin, idf = tfidf_fit(tr_m)
Xtr = tfidf_donustur(tr_m, dizin, idf)
Xte = tfidf_donustur(te_m, dizin, idf)
vec = TfidfVectorizer(
    token_pattern=r"(?u)\b\w\w+\b", preprocessor=kucuk
)
Str = vec.fit_transform(tr_m).toarray()
Ste = vec.transform(te_m).toarray()
print(
    "sözlük: sıfırdan=%d sklearn=%d"
    % (len(dizin), len(vec.vocabulary_))
)
# Sütun sırası farklı olabilir: sklearn sözlüğüyle hizala
sira = [
```

`g07_tfidf.py`, 73–104. satırlar:

```python
    dizin[w]
    for w, _ in sorted(vec.vocabulary_.items(), key=lambda t: t[1])
]
A = Xtr[:, sira]
print(
    "eğitim matrisi maks. mutlak fark = %.2e" % np.abs(A - Str).max()
)
print(
    "sınama  matrisi maks. mutlak fark = %.2e"
    % np.abs(Xte[:, sira] - Ste).max()
)
print(
    "seyreklik (sıfır oranı, eğitim) = %.4f" % (1 - (Str > 0).mean())
)

# --- Baseline sınıflandırıcı ---
ayrik = np.bincount(ytr, minlength=15).argmax()
print(
    "çoğunluk sınıfı baseline: test doğruluk=%.4f"
    % accuracy_score(yte, np.full_like(yte, ayrik))
)
lr = LogisticRegression(C=10.0, max_iter=3000)
lr.fit(Str, ytr)
tah = lr.predict(Ste)
print(
    "TF-IDF + lojistik (C=10): test doğruluk=%.4f  makro-F1=%.4f"
    % (accuracy_score(yte, tah), f1_score(yte, tah, average="macro"))
)
print(
    "eğitim doğruluğu (bilgi amaçlı, eğitim skoru)=%.4f"
    % lr.score(Str, ytr)
)
```


Betiğin çıktısı şöyledir. Sıfırdan yazdığımız TF-IDF matrisi ile sklearn'ün matrisi arasındaki en büyük fark `10⁻¹⁶` mertebesindedir; yani iki hesap aynı sonucu verir. Sınama kümesi için de fark aynı büyüklüktedir.

Çıktı (`cikti_g07.txt`):

```term
sözlük: sıfırdan=33597 sklearn=33597
eğitim matrisi maks. mutlak fark = 3.33e-16
sınama  matrisi maks. mutlak fark = 2.22e-16
seyreklik (sıfır oranı, eğitim) = 0.9989
çoğunluk sınıfı baseline: test doğruluk=0.1038
TF-IDF + lojistik (C=10): test doğruluk=0.2987  makro-F1=0.2015
eğitim doğruluğu (bilgi amaçlı, eğitim skoru)=0.9988
```


Sonuçta birkaç şey dikkat çekicidir. Matrisin yüzde 99,9'u sıfırdır: test paragraflarında bir paragraf ortalama 41 farklı sözcük kullanır; 33 bin sözcüklük sözlüğün çok küçük bir kısmıdır. Bu seyreklik, kelime torbası vektörlerinin bellekte ve hesapta neden sıkıştırılmış (seyrek) biçimde tutulduğunun nedenidir. Eğitim doğruluğu yüzde 99,9'a çıkarken test doğruluğu yüzde 29,9'da kalır. Bu, kelime torbası modelinin ezberlemesidir: sözlük, eğitim paragraflarının her birini kendi kelime kümesiyle ayırt edebilir, ama yeni bir bölümün kelimelerine genellenemez. Çoğunluk sınıfı (en sık Kısım) tahmininin doğruluğu yüzde 10,4'tür; yani TF-IDF modeli çoğunluk tahmininin yaklaşık üç katı başarılıdır, ama görev zordur.

Burada dikkat edilmesi gereken bir nokta var. İnce ayar deneylerinde doğrulama doğruluğu test doğruluğundan belirgin biçimde yüksektir; bunun nedeni, bölüm düzeyinde bölünmüş derlemde bölümlerin konularının birbirinden farklı olmasıdır. Bu bölümün ileride karşılaştıracağımız tüm sonuçları aynı test kümesinde ölçülmüştür; model seçimi yalnızca doğrulama kümesinde yapılmıştır.

## 70.2 n-gram dil modeli ve perplexity

Kelime torbası sıranın tamamen dışında kalır. Dil modeli ise tam tersine, sıranın olasılığını hesaplamak ister. Bir cümlenin olasılığı, kelimelerin zincir kuralıyla çarpımıdır:

P(w₁, …, w_T) = Π_t P(w_t | w₁, …, w_{t−1})

Bu koşullu olasılıkları tahmin etmenin en eski yolu **n-gram** modelidir. Bağlam olarak yalnızca son `n − 1` belirteci alırız:

P(w_t | w_{t−n+1}, …, w_{t−1}) ≈ C(h, w_t) / C(h)

Burada `h` bağlamın son `n − 1` belirtecidir ve `C(·)` sayım demektir. Bu tahminin iki sorunu vardır. Birincisi, eğitimde hiç görülmeyen bir bağlam-belirteç çifti sıfır olasılık alır; bu tek bir kayıp durumunda bütün cümlenin olasılığını sıfıra indirir. İkincisi, `n` büyüdükçe olası bağlam sayısı üstel artar (V^{n−1}) ve çoğu bağlam hiç görülmez. Birinci sorunu **Laplace** (add-k) düzeltmesi çözer: her sayıma sabit bir `k` eklenir.

P_k(w | h) = (C(h, w) + k) / (C(h) + k · V)

Burada `V` sözlük boyutudur. `k = 1` Laplace düzeltmesidir; `k` küçük değerler (0,1, 0,01) daha az düzeltme yapar. Bölüm 62'de çok terimli naive Bayes'te aynı sayım ve düzeltme fikrini kullanmıştık; orada sınıf koşullu kelime olasılıklarını bu şekilde tahmin ettik. Dil modelinde değişen tek şey, koşullandığımız şeyin bir sınıf değil bir önceki belirteçler olmasıdır.

**Perplexity** (şaşkınlık), bir modelin test metnini ne kadar "şaşırtıcı" bulduğunu ölçer. Bölüm 51'de çapraz entropiyi bit cinsinden tanımlamıştık. Bir modelin test metnindeki token başına ortalama çapraz entropisi `H` bit ise perplexity:

PP = 2^H

Bu sayı, modelin her adımda ortalama kaç eşit olasılıklı seçenek arasında tereddüt ettiğini söyler. Düzgün 50 000 kelimelik bir dağılımın perplexity'si 50 000'dir; iyi bir model bu sayıyı düşürür. Perplexity her zaman doğal logaritma ile de tanımlanabilir (`exp(−ortalama ln p)`); iki tanım aynı sonucu verir, çünkü `2^H = e^{H ln 2}` ilişkisi bunu sağlar. Bölüm 51'de öğrendiğimiz gibi, ortalama çapraz entropi 1 bit azaldığında perplexity tam olarak yarıya iner.

Aşağıdaki betik, aynı BPE belirteçleri (bu bölümde bir sonraki adımda öğreneceğimiz tokenizer) üzerinde unigram, bigram ve trigram modellerini eğitir. Her `n` için Laplace'ın `k` değerini doğrulama kümesinde seçer; test kümesinde yalnızca son raporlama yapar. Belirteçler için gerekli dosyalar, aşağıda anlatılacak olan `g03` adımında üretilir; burada bu dosyaları hazır varsayıyoruz.

`g04_ngram.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""
Bölüm 70 - n-gram dil modelleri (sayım + Laplace/add-k) ve perplexity.
Aynı token dizileri (g03) üzerinde; GPT ile adil karşılaştırma."""

import math, os
from collections import Counter, defaultdict
import numpy as np

K = os.path.dirname(os.path.abspath(__file__))
V = 2149
tr = np.load(os.path.join(K, "tok_egitim.npy")).tolist()
va = np.load(os.path.join(K, "tok_dogrulama.npy")).tolist()
te = np.load(os.path.join(K, "tok_test.npy")).tolist()


def egit(dizi, n):
    """n-gram sayımları: bağlam -> {sonraki token: sayı}."""
    say = defaultdict(Counter)
    for i in range(n - 1, len(dizi)):
        say[tuple(dizi[i - n + 1 : i])][dizi[i]] += 1
    toplam = {h: sum(c.values()) for h, c in say.items()}
    return say, toplam


def ppl(model, dizi, n, k):
    say, toplam = model
    nll, m = 0.0, 0
    for i in range(n - 1, len(dizi)):
        h = tuple(dizi[i - n + 1 : i]) if n > 1 else ()
        c = say[h][dizi[i]] if h in say else 0
        t = toplam.get(h, 0)
        p = (c + k) / (t + k * V)
        nll -= math.log(p)
        m += 1
    return math.exp(nll / m)
```

`g04_ngram.py`, 37–72. satırlar:

```python


sonuc = {}
for n in [1, 2, 3]:
    model = egit(tr, n)
    en_iyi = None
    for k in [1.0, 0.1, 0.01, 0.001]:
        p = ppl(model, va, n, k)
        if en_iyi is None or p < en_iyi[1]:
            en_iyi = (k, p)
    k = en_iyi[0]
    pt = ppl(model, te, n, k)
    sonuc[n] = (k, en_iyi[1], pt)
    print(
        "n=%d  add-k en iyi k=%g  doğrulama ppl=%.2f  test ppl=%.2f"
        % (n, k, en_iyi[1], pt)
    )
    if n == 1:
        pl = ppl(model, va, n, 1.0)
        print("n=1 Laplace (k=1) doğrulama ppl=%.2f" % pl)
    if n == 3:
        pl = ppl(model, va, n, 1.0)
        print("n=3 Laplace (k=1) doğrulama ppl=%.2f" % pl)

import csv

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
with open(
    os.path.join(VERI, "b70_ngram.csv"),
    "w",
    encoding="utf-8",
    newline="",
) as f:
    cw = csv.writer(f)
    cw.writerow(["model", "dogrulama_ppl", "test_ppl", "k"])
    for n in [1, 2, 3]:
```

`g04_ngram.py`, 73–74. satırlar:

```python
        k, pv, pt = sonuc[n]
        cw.writerow(["%d-gram" % n, round(pv, 3), round(pt, 3), k])
```


Çıktı (`cikti_g04.txt`):

```term
n=1  add-k en iyi k=1  doğrulama ppl=827.25  test ppl=827.76
n=1 Laplace (k=1) doğrulama ppl=827.25
n=2  add-k en iyi k=0.1  doğrulama ppl=123.46  test ppl=126.82
n=3  add-k en iyi k=0.01  doğrulama ppl=239.77  test ppl=246.13
n=3 Laplace (k=1) doğrulama ppl=844.18
```


Sonuçlar, n-gram'ın tipik davranışını gösterir. Tekli model (unigram) bağlam kullanmaz ve yaklaşık 828 perplexity verir: her belirteci yalnızca genel sıklığına göre tahmin eder. İkili model (bigram) bir önceki belirteci kullanınca perplexity 127'ye iner. Üçlü model (trigram) daha fazla bağlam görmesine rağmen 246'ya çıkar. Bunun nedeni seyrekliktir: 2149 belirteçlik sözlükte üçlü bağlamların büyük çoğunluğu eğitimde hiç görülmemiştir. Bu durumda trigram, çoğu adımda Laplace düzeltmesinden gelen neredeyse düzgün dağılımı kullanır. `k` için seçilen değer 0,01 olduğu için bu düzeltme küçük kalır; yine de her bağlamın sayısı azdır ve tahminler gürültülüdür. Laplace (k = 1) ile üçlü model doğrulamada 844'e kadar kötüleşir; bu da düzeltmenin ne kadar güçlü bir ağırlık taşıdığını gösterir.

Bu sonuç, sinir ağlarının neden gerekli olduğunu gösterir. Bir sinir ağı, bağlamı sayılarla değil, ortak bir gömme uzayındaki vektörlerle temsil eder (aşağıda 70.5). Böylece "eğitimde hiç görülmemiş ama anlamca benzer" bir bağlam, benzer bir olasılık dağılımına götürülebilir. 70.7'de aynı belirteçler üzerinde küçük bir GPT eğittiğimizde doğrulama perplexity'sinin 60 civarında olduğunu göreceğiz; bu, üçlü n-gram'ın yaklaşık dörtte biridir.

Son bir uyarı: n-gram perplexity'si yalnızca aynı belirteç sözlüğü üzerinde karşılaştırılabilir. Farklı tokenizer'larla hesaplanan perplexity'ler birbirine doğrudan karşılaştırılamaz, çünkü bir belirteç bir karakterden de uzun olabilir. Bu tuzağı 70.4'te ayrıca ele alacağız.

## 70.3 Tokenizasyon: karakter, sözcük ve alt-sözcük

Bir dil modeli metni doğrudan okumaz; önce onu **belirteç** (token) dizisine çevirir. Belirteç, modelin tek bir adımda tahmin ettiği birimdir. Metni nasıl parçaladığımız üç şeyi belirler: modelin sözlüğünün boyutunu, bir metnin kaç adımda işleneceğini (dizi uzunluğu) ve modelin bilmediği kelimelerle ne kadar iyi başa çıkacağını.

Üç temel düzey vardır. Aşağıdaki şekil aynı cümlenin üç farklı parçalanışını gösterir. Cümle: "Dil modeli bir sonraki tokeni tahmin eder."

![Şekil 70.1: Aynı cümlenin karakter, sözcük ve alt-sözcük (BPE) düzeyindeki parçalanışı](gorseller/b70_tokenizasyon_duzeyleri.png)

**Karakter düzeyi** en küçük sözlüğü kullanır: alfabedeki karakterler (ve noktalama). Sözlük boyutu birkaç yüzdür, hiçbir kelime "bilinmeyen" olmaz, ama dizi çok uzar: bu cümle 42 adım eder. Bir adım, bir kelimenin anlamını taşıyan birkaç karakteri tek başına tahmin etmek zorundadır; bu yüzden model uzun bağımlılıkları öğrenmek için daha çok adıma ve daha çok işleme ihtiyaç duyar.

**Sözcük düzeyi** dizi uzunluğunu kısaltır (bu cümle 8 adım), ama sözlük patlar. Türkçe bu konuda zor bir dildir. Sondan eklemeli yapısı yüzünden aynı sözcük kökünden çok sayıda biçim üretilir: "kullanılabilirliğinden", "kullanılabilirlik", "kullanılabilir" birbirinden ayrı sözcükler olur. Bu sözcüklerden hiçbirinin eğitimde görülmemesi, modelin onları tanımayacağı anlamına gelir. Buna **OOV** (sözlük dışı, out-of-vocabulary) sorunu denir.

**Alt-sözcük düzeyi** iki uç arasında bir uzlaşmadır. Sık geçen kelimeler tek bir belirteç olarak kalır ("tahmin"), nadir kelimeler ise daha küçük parçalara bölünür ("ilik" + "eti" + ...). Bu sayede sözlük makul bir boyutta kalır ve yeni bir kelime, bilinen parçalardan kurulabilir. Şekilde alt-sözcük düzeyi 11 parçaya iner: "Dil" bir parça, "modeli" bir parça, "tokeni" iki parça ("tok" ve "eni"). Bu parçalanış, BPE'nin öğrendiği birleştirmelerden gelir; bunu 70.4'te sıfırdan yazacağız.

Aşağıdaki betik, kitabın derleminde üç düzeyin ölçülebilir sonuçlarını çıkarır: sözcük sözlüğü büyümesi ve OOV oranı, farklı birleştirme sayılarında BPE takası ve iki dil arasındaki maliyet farkı. Kod, 70.4'te öğreneceğimiz `bpe_sifirdan.py` dosyasını kullanır; bu nedenle betik bu bölümün ilerleyen kısmına bağlıdır, ama okumak için sırası önemli değildir.

`g02_tokenizasyon.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""
Bölüm 70 - Tokenizasyon ölçümleri: karakter, sözcük, OOV, BPE takası,
dil karşılaştırması ve bayt maliyeti. Çıktılar
engine/veri/b70_*.csv."""

import csv, os, re, time
from bpe_sifirdan import BPE

K = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
oku = lambda a: open(os.path.join(K, a), encoding="utf-8").read()
tr, te, en = (
    oku("korpus_egitim.txt"),
    oku("korpus_test.txt"),
    oku("korpus_en.txt"),
)
n_tr = 500000


def sozcukler(m):
    return re.findall(
        r"\w+", m.replace("İ", "i").replace("I", "ı").lower()
    )


def yaz(ad, basliklar, satirlar):
    with open(
        os.path.join(VERI, ad), "w", encoding="utf-8", newline=""
    ) as f:
        cw = csv.writer(f)
        cw.writerow(basliklar)
        cw.writerows(satirlar)


print(
```

`g02_tokenizasyon.py`, 37–72. satırlar:

```python
    "== 1. Karakter ve sözcük istatistikleri (eşit boyut %d) =="
    % n_tr
)
for ad, m in [("Türkçe", tr[:n_tr]), ("İngilizce", en[:n_tr])]:
    w = sozcukler(m)
    print(
        "%-10s karakter=%d sözcük=%d tekil=%d alfabe=%d  "
        "bayt/karakter=%.4f"
        % (
            ad,
            len(m),
            len(w),
            len(set(w)),
            len(set(m)),
            len(m.encode("utf-8")) / len(m),
        )
    )

print(
    "\n== 2. Sözcük düzeyi: sözlük büyümesi ve OOV (sınama: "
    "test bölümleri) =="
)
w_tr, w_te = sozcukler(tr), sozcukler(te)
satirlar = []
for oran in [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]:
    alt = w_tr[: int(len(w_tr) * oran)]
    kume = set(alt)
    oov = sum(1 for x in w_te if x not in kume) / len(w_te)
    satirlar.append((oran, len(alt), len(kume), round(100 * oov, 3)))
    print(
        "eğitim %%%3d  sözcük=%7d  sözlük=%6d  OOV=%%%.2f"
        % (oran * 100, len(alt), len(kume), 100 * oov)
    )
yaz(
    "b70_sozluk_buyume.csv",
    ["oran", "sozcuk", "sozluk", "oov_yuzde"],
```

`g02_tokenizasyon.py`, 73–108. satırlar:

```python
    satirlar,
)

print(
    "\n== 3. Alt-sözcük (BPE) takası: eğitim derlemi "
    "üzerinde öğrenildi =="
)
takas = []
for m in [0, 250, 500, 1000, 1500, 2000, 3000]:
    t0 = time.time()
    b = BPE(tr[:n_tr], m)
    sn = time.time() - t0
    ids = b.kodla(te)
    unk = sum(1 for i in ids if i == b.unk) / len(ids)
    # Geri dönüş: yalnızca alfabedeki karakterlerden oluşan metin
    alt = "".join(c for c in te if c in b.alfabe)
    ok = b.coz(b.kodla(alt)) == alt
    kt = len(te) / len(ids)
    takas.append(
        (m, b.boyut(), len(ids), round(kt, 4), round(100 * unk, 4))
    )
    print(
        "birleştirme=%4d sözlük=%5d token=%7d kar/token=%.3f "
        "unk=%%%.3f "
        "geri-dönüş=%s (%.1f sn)"
        % (m, b.boyut(), len(ids), kt, 100 * unk, ok, sn)
    )
yaz(
    "b70_bpe_takas.csv",
    ["birlestirme", "sozluk", "token", "kar_token", "unk_yuzde"],
    takas,
)

print(
    "\n== 4. Dil karşılaştırması: 300 bin karakterle "
    "eğitilmiş tokenizer =="
```

`g02_tokenizasyon.py`, 109–144. satırlar:

```python
)
# Eğitim: TR için tr[:300k], EN için en[:300k]. Sınama: TR için te,
# EN için en[300k:] (eğitimde kullanılmayan parça).
bt = BPE(tr[:300000], 1000)
be = BPE(en[:300000], 1000)
satirlar = []
for ad, b, metin in [
    ("TR tok. / TR metin", bt, te),
    ("EN tok. / EN metin", be, en[300000:]),
    ("EN tok. / TR metin", be, te),
    ("TR tok. / EN metin", bt, en[300000:]),
]:
    ids = b.kodla(metin)
    unk = sum(1 for i in ids if i == b.unk) / len(ids)
    kt = len(metin) / len(ids)
    tks = len(ids) / len(sozcukler(metin))
    satirlar.append(
        (
            ad,
            b.boyut(),
            round(kt, 4),
            round(tks, 4),
            round(100 * unk, 4),
        )
    )
    print(
        "%-20s sözlük=%5d kar/token=%.3f token/sözcük=%.3f unk=%%%.3f"
        % (ad, b.boyut(), kt, tks, 100 * unk)
    )
yaz(
    "b70_dil_takas.csv",
    [
        "tokenizer_metin",
        "sozluk",
        "kar_token",
        "token_sozcuk",
```

`g02_tokenizasyon.py`, 145–157. satırlar:

```python
        "unk_yuzde",
    ],
    satirlar,
)

print(
    "\n== 5. Bayt düzeyi (UTF-8): Türkçe karakterlerin bayt "
    "maliyeti =="
)
for c in "aığüşöçıİ":
    print(
        "%s U+%04X -> %d bayt" % (c, ord(c), len(c.encode("utf-8")))
    )
```


Çıktı (`cikti_g02.txt`):

```term
== 1. Karakter ve sözcük istatistikleri (eşit boyut 500000) ==
Türkçe     karakter=500000 sözcük=74646 tekil=12766 alfabe=145
    bayt/karakter=1.1020
İngilizce  karakter=500000 sözcük=73334 tekil=5635 alfabe=141
    bayt/karakter=1.0023

== 2. Sözcük düzeyi: sözlük büyümesi ve OOV (sınama: test bölümleri) ==
eğitim % 10  sözcük=  36142  sözlük=  8476  OOV=%23.46
eğitim % 20  sözcük=  72285  sözlük= 12488  OOV=%18.27
eğitim % 40  sözcük= 144571  sözlük= 19553  OOV=%12.94
eğitim % 60  sözcük= 216857  sözlük= 24947  OOV=%10.46
eğitim % 80  sözcük= 289143  sözlük= 29815  OOV=%8.21
eğitim %100  sözcük= 361429  sözlük= 33687  OOV=%7.24

== 3. Alt-sözcük (BPE) takası: eğitim derlemi üzerinde öğrenildi ==
birleştirme=   0 sözlük=  146 token= 482617 kar/token=1.000 unk=%0.036
    geri-dönüş=True (0.1 sn)
birleştirme= 250 sözlük=  396 token= 258682 kar/token=1.866 unk=%0.068
    geri-dönüş=True (0.7 sn)
birleştirme= 500 sözlük=  646 token= 218268 kar/token=2.211 unk=%0.081
    geri-dönüş=True (1.1 sn)
birleştirme=1000 sözlük= 1146 token= 185441 kar/token=2.603 unk=%0.095
    geri-dönüş=True (2.0 sn)
birleştirme=1500 sözlük= 1646 token= 169106 kar/token=2.854 unk=%0.104
    geri-dönüş=True (3.4 sn)
```

Çıktının devamı (`cikti_g02.txt`):

```term
birleştirme=2000 sözlük= 2146 token= 159409 kar/token=3.028 unk=%0.110
    geri-dönüş=True (4.7 sn)
birleştirme=3000 sözlük= 3146 token= 147682 kar/token=3.268 unk=%0.119
    geri-dönüş=True (8.2 sn)

== 4. Dil karşılaştırması: 300 bin karakterle eğitilmiş tokenizer ==
TR tok. / TR metin   sözlük= 1142 kar/token=2.594 token/sözcük=2.581
    unk=%0.112
EN tok. / EN metin   sözlük= 1131 kar/token=2.145 token/sözcük=3.157
    unk=%0.039
EN tok. / TR metin   sözlük= 1131 kar/token=1.490 token/sözcük=4.494
    unk=%9.287
TR tok. / EN metin   sözlük= 1142 kar/token=1.541 token/sözcük=4.395
    unk=%0.043

== 5. Bayt düzeyi (UTF-8): Türkçe karakterlerin bayt maliyeti ==
a U+0061 -> 1 bayt
ı U+0131 -> 2 bayt
ğ U+011F -> 2 bayt
ü U+00FC -> 2 bayt
ş U+015F -> 2 bayt
ö U+00F6 -> 2 bayt
ç U+00E7 -> 2 bayt
ı U+0131 -> 2 bayt
İ U+0130 -> 2 bayt
```


Çıktının ilk iki bölümü sözcük düzeyinin sınırlarını gösterir. Eşit boyuttaki (500 bin karakter) Türkçe ve İngilizce metinlerde Türkçe metinde 12 766 farklı sözcük vardır; İngilizcede bu sayı 5 635'tir. Aynı uzunlukta bir Türkçe metin, İngilizceye göre neredeyse iki kat fazla farklı sözcük içerir. Bu, Türkçenin eklemeli yapısının doğrudan sonucudur. Sözlük büyümesi tablosu ise bir başka gerçeği gösterir: eğitim verisinin yüzde 10'unu gördüğümüzde sözlük 8 476 sözcük olur ve test sözcüklerinin yüzde 23,5'i OOV'dur. Tüm eğitim verisiyle bile sözlük 33 687 sözcüğe çıkar ve yüzde 7,2'lik bir OOV oranı kalır. Bu, sözcük düzeyi için sözlüğü büyütmenin sınırlı bir çare olduğunu gösterir.

![Şekil 70.2: Sözcük sözlüğü büyümesi ve test kümesindeki OOV oranı](gorseller/b70_sozluk_buyume.png)

Üçüncü bölümde BPE birleştirme sayısını artırdıkça ne olduğunu görüyoruz. Birleştirme sayısı 0 iken her belirteç bir karakterdir (kar/token = 1,000); 1000 birleştirmede sözlük 1146 olur ve bir belirteç ortalama 2,6 karakter taşır; 3000 birleştirmede ise 3,27 karaktere çıkar. Bu, sözlük ile dizi uzunluğu arasındaki takastır: sözlük büyüdükçe aynı metin daha az adımda kodlanır, ama her adımın tahmin edilmesi gereken sözlük de büyür. Dikkat edilmesi gereken, kar/token eğrisinin artan birleştirmelerle düzleşmesidir: ilk birleştirmeler çok sayıda çifti birleştirir, sonrakiler daha az sıklıkta olan çiftlere dokunur. Bu takas Şekil 70.3'te görülüyor.

![Şekil 70.3: Birleştirme sayısına göre sözlük boyutu ve token başına karakter](gorseller/b70_bpe_takas.png)

Dil karşılaştırması tablosu (çıktının 4. bölümü), tokenizer'ın eğitildiği dille uyum konusunu gösterir. Dört satırın her biri 300 bin karakterle eğitilmiş bir tokenizer'ı, bir metin üzerinde ölçer.

Burada iki sayıya dikkat etmek gerekir (Şekil 70.4). "EN tokenizer / TR metin" satırında sözcük başına token 4,49'a çıkar (Türkçe tokenizer ile aynı metinde 2,58), üstelik bilinmeyen (unk) oranı yüzde 9,3'e fırlar. Bunun nedeni, İngilizce derlemin Türkçe harfleri (ş, ğ, ı, ö, ü, ç) hiç içermemesidir: bu harfler sözlükte olmadığı için unk olur. Karakter başına ölçüm de aynı sonucu verir: Türkçe tokenizer Türkçe metinde 2,59 karakter/token, İngilizce tokenizer aynı metinde 1,49. Yani Türkçe metin, İngilizce ağırlıklı bir tokenizer ile kodlandığında yaklaşık yüzde 74 daha fazla belirteç tutar. Bu, bilinen bir gözlemdir; yukarıdaki ölçüm bunu kendi derlemimizde, aynı yöntemle sayısallaştırır (genel bilgi: ticari büyük dil modellerinin tokenizer'ları çoğunlukla İngilizce ağırlıklı verilerle eğitilir, bu yüzden Türkçe için maliyet genellikle daha yüksek çıkar; bu bölümde o modellerin tokenizer'ı ölçülmedi).

![Şekil 70.4: Aynı Türkçe metin için tokenizer eşleşmesinin token maliyeti](gorseller/b70_dil_takas.png)

Bir uyarı daha. "EN tokenizer / EN metin" ile "TR tokenizer / EN metin" satırlarında İngilizce metin, Türkçe tokenizer ile kodlandığında karakter/token 1,54'e düşer. Demek ki bir tokenizer'ın verimliliği, dilden çok eğitildiği veri dağılımına bağlıdır. Dili, derlemi ve sözlük boyutunu birlikte raporlamayan bir token sayısı anlamsızdır.

::: not
Dikkat: "token" sayısı, tokenizer'a bağlı bir ölçüdür. İki modelin perplexity'sini ya da bağlam uzunluğunu karşılaştırırken aynı tokenizer'ı kullanmadıysan, ölçümler adil değildir. Bu bölümde her karşılaştırmada aynı belirteç dizisi kullanıldı.
:::

## 70.4 BPE: birleştirmeleri öğrenmek, kodlamak ve çözmek

Alt-sözcük tokenizasyonunun en yaygın yöntemi **bayt çifti kodlaması** (Byte Pair Encoding, BPE)'dır. Fikir, Gage'in 1994'te veri sıkıştırma için önerdiği algoritmadan gelir; Sennrich ve arkadaşları 2016'da bunu makine çevirisi için alt-sözcük birimlerine uyarladı (genel bilgi). Algoritma çok basittir: metni karakterlerle başlat; en sık bitişik çifti bul; o çifti tek bir yeni simgeyle değiştir; bu işlemi istediğin sözlük boyutuna ulaşana kadar tekrarla.

Küçük bir örnekle düşünelim. Derlem "kod kodu koda kod" olsun. Önce metni sözcüklere ayırırız. Ancak burada bir ayrıntı var: sözcüğün başındaki boşluğu da bir karakter olarak tutarız. Böylece "kod" ile " kod" (boşluklu) farklı biçimler olarak öğrenilir ve çözme sırasında kelimeler arası boşluk kaybolmaz. Bu ön işleme, GPT-2'nin kullandığına benzer bir düzenli ifade ile yapılır (genel bilgi).

Her adımda, kelimelerin çift frekanslarını sayarız. Frekansı en yüksek çift birleştirilir. Eşitlik bozulması için (aynı sayıda çift varsa) sözlük sırasını kullanıyoruz; böylece sonuç her çalıştırmada aynıdır. Aşağıdaki betik bu üç adımı elle izlenebilir biçimde yazdırır.

`g15_bpe_ornek.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""
Bölüm 70 - Elle izlenen BPE örneği: 4 kelimelik derlem, üç birleştirme
adımı.
"""

from collections import Counter
from bpe_sifirdan import egit, on_isle

metin = "kod kodu koda kod"
frek = Counter(on_isle(metin))
print("ön işleme parçaları:", dict(frek))
parca = {w: list(w) for w in frek}


def ciftler(parca):
    c = Counter()
    for w, s in parca.items():
        for a, b in zip(s, s[1:]):
            c[(a, b)] += frek[w]
    return c


for adim in range(1, 4):
    c = ciftler(parca)
    en = max(c, key=lambda p: (c[p], p))
    print(
        "adım %d: en sık çift %r sayı=%d | sayımlar: %s"
        % (
            adim,
            en,
            c[en],
            sorted(
                ((k, v) for k, v in c.items()),
                key=lambda t: (-t[1], t[0]),
            )[:5],
```

`g15_bpe_ornek.py`, 37–51. satırlar:

```python
        )
    )
    yeni = en[0] + en[1]
    for w, s in parca.items():
        t, i = [], 0
        while i < len(s):
            if i + 1 < len(s) and (s[i], s[i + 1]) == en:
                t.append(yeni)
                i += 2
            else:
                t.append(s[i])
                i += 1
        parca[w] = t
    print("   durum:", {w: s for w, s in parca.items()})
print("egit(…,3) =", egit(metin, 3))
```


Çıktı (`cikti_g15.txt`):

```term
ön işleme parçaları: {'kod': 1, ' kodu': 1, ' koda': 1, ' kod': 1}
adım 1: en sık çift ('o', 'd') sayı=4 | sayımlar: [(('k', 'o'), 4),
    (('o', 'd'), 4), ((' ', 'k'), 3), (('d', 'a'), 1), (('d', 'u'), 1)]
   durum: {'kod': ['k', 'od'], ' kodu': [' ', 'k', 'od', 'u'], ' koda':
    [' ', 'k', 'od', 'a'], ' kod': [' ', 'k', 'od']}
adım 2: en sık çift ('k', 'od') sayı=4 | sayımlar: [(('k', 'od'), 4),
    ((' ', 'k'), 3), (('od', 'a'), 1), (('od', 'u'), 1)]
   durum: {'kod': ['kod'], ' kodu': [' ', 'kod', 'u'], ' koda': [' ',
    'kod', 'a'], ' kod': [' ', 'kod']}
adım 3: en sık çift (' ', 'kod') sayı=3 | sayımlar: [((' ', 'kod'), 3),
    (('kod', 'a'), 1), (('kod', 'u'), 1)]
   durum: {'kod': ['kod'], ' kodu': [' kod', 'u'], ' koda': [' kod',
    'a'], ' kod': [' kod']}
egit(…,3) = [('o', 'd'), ('k', 'od'), (' ', 'kod')]
```


İlk adımda `('k','o')` ve `('o','d')` çiftleri dört kez geçer; eşitlik olduğu için sözlük sırası `('o','d')`yi seçer. Sonuçta `od` simgesi oluşur. İkinci adımda `('k','od')` dört kez geçer ve `kod` simgesi çıkar. Üçüncü adımda boşluk içeren `(' ', 'kod')` üç kez geçer. Üç birleştirmeden sonra `kod` kelimesi tek bir simgedir, ama `kodu` ve `koda` kelimelerinde "u" ve "a" ayrı simgeler olarak kalır. Bu yüzden eklerin Türkçedeki eklemeli yapısı, BPE'de ayrı birimler olarak öğrenilebilir: `kod` kökü ile `u` ve `a` ekleri ayrı kalır. Yani Türkçenin çok sayıda ek kombinasyonunu sözlükte tek tek saklamak yerine, birkaç ek simgesiyle kurabiliriz.

### Öğrenme: çift sayımlarını verimli güncellemek

Gerçek bir derlemde her adımda bütün kelimeleri yeniden taramak yavaştır. Bu yüzden öğrenme sırasında iki tablo tutarız: çift → toplam frekans ve çift → o çifti içeren kelimeler. Bir birleştirme yapıldığında yalnızca o çifti içeren kelimeleri güncelleriz. Bu, algoritmanın pratik olarak çalışmasını sağlayan önemli bir ayrıntıdır. Aşağıdaki betik, bu bölümün BPE'sinin tamamını içerir: öğrenme (`egit`), birleştirme kurallarını tutan sınıf (`BPE`), kodlama ve çözme.

`bpe_sifirdan.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""Bölüm 70 - Bayt çifti kodlaması (BPE), sıfırdan.

Yalnızca standart kütüphane kullanır. Birleştirme kuralları metinden
öğrenilir; kodlama, öğrenilen kuralları sırayla uygular; çözme, sembol
dizilerini yeniden birleştirir. Ön işleme (pretokenization) metni
kelime ve noktalama parçalarına böler; her parçanın başındaki boşluk
parçanın bir parçası olarak tutulur, böylece kodla-çöz tam olarak
orijinal metni verir.
"""

import re
from collections import Counter, defaultdict

DESEN = re.compile(r" ?\w+| ?[^\w\s]+|\s+")


def on_isle(metin):
    return DESEN.findall(metin)


def egit(metin, birlestirme):
    """En sık çifti tekrar tekrar birleştirerek kuralları öğrenir."""
    frekans = Counter(on_isle(metin))
    parca = {
        w: list(w) for w in frekans
    }  # her kelime bir sembol listesi
    cift = Counter()  # çift -> toplam frekans
    konum = defaultdict(set)  # çift -> o çifti içeren kelimeler
    for w, f in frekans.items():
        s = parca[w]
        for a, b in zip(s, s[1:]):
            cift[(a, b)] += f
            konum[(a, b)].add(w)
    kurallar = []
    for _ in range(birlestirme):
```

`bpe_sifirdan.py`, 37–72. satırlar:

```python
        if not cift:
            break
        # Eşitlikte sözlük sırası: sonuç her çalıştırmada aynı olsun.
        en = max(cift, key=lambda p: (cift[p], p))
        if cift[en] <= 0:
            break
        kurallar.append(en)
        yeni = en[0] + en[1]
        for w in list(konum[en]):
            f, s = frekans[w], parca[w]
            for a, b in zip(s, s[1:]):  # eski çiftleri düş
                cift[(a, b)] -= f
            t, i = [], 0
            while i < len(s):  # soldan sağa birleştir
                if i + 1 < len(s) and (s[i], s[i + 1]) == en:
                    t.append(yeni)
                    i += 2
                else:
                    t.append(s[i])
                    i += 1
            parca[w] = t
            for a, b in zip(t, t[1:]):  # yeni çiftleri ekle
                cift[(a, b)] += f
                konum[(a, b)].add(w)
    return kurallar


class BPE:
    """Öğrenilmiş kurallarla kodlayan ve çözen tokenizer."""

    def __init__(self, metin, birlestirme):
        self.alfabe = sorted(set(metin))
        self.kurallar = egit(metin, birlestirme)
        self._kur()

    @classmethod
```

`bpe_sifirdan.py`, 73–108. satırlar:

```python
    def yukle(cls, alfabe, kurallar):
        """
        Kaydedilmiş alfabe ve kurallardan tokenizer'ı yeniden kurar.
        """
        b = cls.__new__(cls)
        b.alfabe = list(alfabe)
        b.kurallar = [tuple(p) for p in kurallar]
        b._kur()
        return b

    def _kur(self):
        self.sozluk = {}
        for c in self.alfabe:
            self.sozluk.setdefault(c, len(self.sozluk))
        for a, b in self.kurallar:
            self.sozluk.setdefault(a + b, len(self.sozluk))
        self.ters = {i: s for s, i in self.sozluk.items()}
        self.sira = {p: i for i, p in enumerate(self.kurallar)}
        self.unk = len(self.sozluk)  # alfabe dışı karakter için
        self.onbellek = {}

    def boyut(self):
        return len(self.sozluk) + 1

    def _parcala(self, w):
        if w in self.onbellek:
            return self.onbellek[w]
        s = list(w)
        while len(s) > 1:
            aday = [
                (self.sira[(a, b)], i)
                for i, (a, b) in enumerate(zip(s, s[1:]))
                if (a, b) in self.sira
            ]
            if not aday:
                break
```

`bpe_sifirdan.py`, 109–122. satırlar:

```python
            _, i = min(aday)  # en erken öğrenilen kural
            s[i : i + 2] = [s[i] + s[i + 1]]
        self.onbellek[w] = s
        return s

    def kodla(self, metin):
        ids = []
        for w in on_isle(metin):
            for sembol in self._parcala(w):
                ids.append(self.sozluk.get(sembol, self.unk))
        return ids

    def coz(self, ids):
        return "".join(self.ters.get(i, "") for i in ids)
```


Kodu okurken dikkat edilmesi gereken üç nokta var. Birincisi, `egit` içinde `konum` tablosu yalnızca etkilenen kelimeleri yeniden işler; bu olmadan 2000 birleştirme yapmak dakikalar sürerdi. İkincisi, `_parcala` fonksiyonu bir kelimeyi öğrenilmiş sıraya göre birleştirir: her adımda o kelimedeki en erken öğrenilmiş çifti seçer. Üçüncüsü, `coz` fonksiyonu yalnızca simgeleri birleştirir; BPE'nin kodunu çözmek için ayrı bir sözlük ters çevirmesi yapılmıştır. Bu, `decode(encode(x)) == x` özelliğini sağlar; bu özelliği 70.3'teki ölçümde her birleştirme sayısı için doğruladık (geri-dönüş = True).

Birleştirme kurallarının bir uzantısı, çözümün iki ayrı kaynaktan gelebilmesidir: bir kelimenin kodunu çözerken hangi karakterlerin alfabede olduğunu bilmek gerekir. Eğitimde görülmemiş bir karakter (örneğin bir emoji) sözlükte olmadığı için **unk** (bilinmeyen) belirtecine düşer ve çözümde kaybolur. Bu yüzden geri-dönüş testi yalnızca alfabedeki karakterlerden oluşan metin üzerinde yapılır. Bayt düzeyi BPE bu sorunu baştan çözer; onu aşağıda göreceğiz.

### Bayt düzeyi BPE: unk olmadan Türkçe

GPT-2 ve sonraki birçok model, BPE'yi karakterler yerine **baytlar** üzerinde çalıştırır (genel bilgi, Radford ve arkadaşları 2019). Metin UTF-8 bayt dizisine çevrilir; her bayt 0–255 arasında bir sayıdır ve tam olarak 256 olası değer vardır. Bu 256 bayt, okunabilir ve kontrol karakteri olmayan 256 simgeye eşlenir. Böylece hiçbir karakter unk olmaz: en kötü durumda bir karakter birkaç bayta bölünür.

Bu maliyet Türkçede belirgindir. Ölçümümüzde (70.3, 5. bölüm) ı, ğ, ü, ş, ö, ç ve İ harfleri UTF-8'de iki bayta kodlanır; ASCII harfleri bir bayt tutar. Bu yüzden 500 bin karakterlik Türkçe metin ortalama 1,102 bayt/karakter, İngilizce metin 1,002 bayt/karakter taşır. Aşağıdaki betik, transformers kütüphanesinin kendi bayt-simge eşlemesini kullanır ve bu iki baytlık harflerin nasıl göründüğünü gösterir.

`g17_bayt.py` dosyasının tamamı (17 satır):

```python
# -*- coding: utf-8 -*-
"""Bölüm 70 - Bayt düzeyi BPE: UTF-8 baytlarının okunabilir simgelere
eşlenmesi. Eşleme, kurulu transformers 4.57.6 kaynağındaki
bytes_to_unicode() fonksiyonudur; burada yalnızca içe aktarılır."""

from transformers.models.gpt2.tokenization_gpt2 import (
    bytes_to_unicode,
)

eslem = bytes_to_unicode()
print("eşleme boyutu:", len(eslem))
for metin in ["ğ", "ı", "ü", "a", " ", "çözüm"]:
    baytlar = list(metin.encode("utf-8"))
    simgeler = [eslem[b] for b in baytlar]
    print(
        "%-7r bayt=%s simge=%s" % (metin, baytlar, "".join(simgeler))
    )
```


Çıktı (`cikti_g17.txt`):

```term
eşleme boyutu: 256
'ğ'     bayt=[196, 159] simge=ÄŁ
'ı'     bayt=[196, 177] simge=Ä±
'ü'     bayt=[195, 188] simge=Ã¼
'a'     bayt=[97] simge=a
' '     bayt=[32] simge=Ġ
'çözüm' bayt=[195, 167, 195, 182, 122, 195, 188, 109] simge=Ã§Ã¶zÃ¼m
```


Çıktıda `ğ` harfi iki simgeye (`Ä` ve `Ł`) dönüşür. Bu simgeler anlamsızdır, ama BPE onları diğer baytlarla birlikte öğrenir ve sık geçen Türkçe harf dizilerini tek birimlere birleştirebilir. Bayt düzeyinin bedeli, birçok Türkçe harfin iki belirteç tutmasıdır; faydası ise hiçbir girdinin "bilinmeyen" olmamasıdır.

WordPiece (BERT'in tokenizer'ı; Schuster ve Nakajima 2012, Devlin ve arkadaşları 2019), Unigram dil modeli tokenizasyonu (Kudo 2018) ve SentencePiece (Kudo ve Richardson 2018) alt-sözcük yöntemlerinin diğer aileleridir (genel bilgi). WordPiece birleştirmeyi çift olasılığının artışına göre seçer; Unigram ise büyük bir sözlükten başlayıp olasılığı en az etkileyen simgeleri budar; SentencePiece ise metni bir boşluk ayırıcısı olmadan, ham akış olarak işler ve boşluğu özel bir simgeyle temsil eder. Bu yöntemlerin ayrıntısı bu bölümde kodlanmadı; amacımız, BPE'nin mekanizmasını ve bağlarını kavramaktır.

Son olarak tokenizasyonun maliyete etkisi: dizi uzunluğu, dikkat mekanizmasının maliyetini belirler (Bölüm 69'da gördüğün gibi dikkat maliyeti, dizi uzunluğunun karesiyle büyür). Aynı metnin iki farklı tokenizer ile kodlanması, işlenecek adım sayısını değiştirir; bu da hem eğitim süresini hem de çıkarım maliyetini etkiler. Türkçe için kötü bir tokenizer, aynı metni daha pahalı işlemek demektir.

## 70.5 Gömmeler: one-hot'tan yoğun vektöre

Bir belirteç, modele bir sayı olarak girmez. Her belirteç bir **indeks**tir; bu indeksi bir vektöre çevirmek gerekir. En basit yol **one-hot** kodlamadır: `V` boyutlu bir vektör, yalnızca belirtecin indeksinde 1, diğer yerlerde 0 taşır. Bu temsil, eşit uzaklıkta olan bağımsız simgeler üretir: "kedi" ile "köpek" arasındaki uzaklık, "kedi" ile "masa" arasındaki uzaklıkla aynıdır. Anlam bilgisi taşımaz ve 2149 belirteçlik sözlükte her vektör 2149 boyutludur.

Yoğun **gömme** (embedding), her belirteç için `d` boyutlu (genelde birkaç yüz) öğrenilmiş bir vektör tutar. Burada iki önemli gözlem vardır. Birincisi, gömme katmanı bir **matris çarpımıdır**: one-hot vektör `e` ile gömme matrisi `W` (V × d) çarpılırsa, sonuç `W`'nin yalnızca bir satırıdır. Yani gömme katmanı bir arama tablosudur; one-hot çarpımı bu tabloyu daha yavaş bir biçimde okur. İkincisi, `W` eğitimle öğrenilir ve belirteçler arasındaki benzerlik, eğitim verisinden doğar.

Aşağıdaki betik, bu eşdeğerliği 3 belirteçlik bir sözlük ve 2 boyutlu bir gömme ile sayısal olarak gösterir.

`g16_ornek_hesap.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""Bölüm 70 - Çözümlü örnekler için el hesapları, kodla doğrulama:
(a) 4 belirteçlik derlemde bigram + Laplace ve perplexity;
(b) gömme tablosu = one-hot × matris (satır seçimi)."""

import math
from collections import Counter

# (a) Derlem: a b a c ; sözlük V = 3 (a, b, c)
derlem = ["a", "b", "a", "c"]
V = 3
bigram = Counter(zip(derlem, derlem[1:]))
baglam = Counter(derlem[:-1])
print("bigram sayımları:", dict(bigram))
print("bağlam sayımları:", dict(baglam))


def p_lap(sonraki, once):
    return (bigram[(once, sonraki)] + 1) / (baglam[once] + V)


cumle = ["a", "b", "a", "c"]
olasiliklar = [
    p_lap(cumle[i + 1], cumle[i]) for i in range(len(cumle) - 1)
]
print("P(b|a) =", p_lap("b", "a"), " P(a|b) =", p_lap("a", "b"))
print("P(c|a) =", p_lap("c", "a"), " P(a|a) =", p_lap("a", "a"))
print("adım olasılıkları:", olasiliklar)
ce = -sum(math.log2(p) for p in olasiliklar) / len(olasiliklar)
print("çapraz entropi (bit/belirteç) =", round(ce, 4))
print("perplexity = 2^H =", round(2**ce, 4))

# (b) Gömme: one-hot × W satır seçimi
W = [[0.2, -0.5], [1.0, 0.3], [-0.7, 0.9]]  # V=3, d=2
onehot = [0, 1, 0]  # 'b' belirteci
carpim = [
```

`g16_ornek_hesap.py`, 37–39. satırlar:

```python
    sum(onehot[i] * W[i][j] for i in range(3)) for j in range(2)
]
print("one-hot x W =", carpim, " satır =", W[1])
```


Çıktı (`cikti_g16.txt`):

```term
bigram sayımları: {('a', 'b'): 1, ('b', 'a'): 1, ('a', 'c'): 1}
bağlam sayımları: {'a': 2, 'b': 1}
P(b|a) = 0.4  P(a|b) = 0.5
P(c|a) = 0.4  P(a|a) = 0.2
adım olasılıkları: [0.4, 0.5, 0.4]
çapraz entropi (bit/belirteç) = 1.2146
perplexity = 2^H = 2.3208
one-hot x W = [1.0, 0.3]  satır = [1.0, 0.3]
```


Çıktıda one-hot × `W` sonucu, doğrudan 'b' satırına eşittir: (1,0 ve 0,3). Bu, bir hesaplama numarası değil, bir veri yapısı tercihidir: gömme tablosu bir dizi indeksleme ile okunur, çarpılmaz. Büyük modellerde V yüz binlere ulaşır; one-hot çarpımı bu boyutta gereksiz yere pahalı olur.

### word2vec: skip-gram ve negatif örnekleme, sıfırdan

Gömmelerin anlamlı olması için bir öğrenme görevi gerekir. **word2vec** (Mikolov ve arkadaşları 2013, genel bilgi) iki basit fikre dayanır: "aynı bağlamda geçen kelimeler benzerdir" (dağılım hipotezi) ve bu benzerliği, bir merkez kelimenin etrafındaki bağlam kelimelerini tahmin ederek öğren. **Skip-gram** varyantında merkez kelimeden bağlam kelimeleri tahmin edilir. Tam softmax, bütün sözlük üzerinden normalizasyon gerektirdiği için pahalıdır; **negatif örnekleme** bunu, gerçek bağlam çiftini birkaç rastgele "yanlış" çiftle ayırt eden bir ikili sınıflandırma problemine çevirerek ucuzlatır.

Bir merkez `c` ve gerçek bağlam `o` için kayıp `−ln σ(u_o · v_c) − Σ ln σ(−u_n · v_c)` biçimindedir; burada `n` rastgele seçilmiş negatif örneklerdir, `σ` sigmoid fonksiyonudur (Bölüm 58). Negatif örnekler, birlik dağılımının 0,75 kuvvetine göre seçilir; bu, çok sık kelimelerin negatif olarak aşırı seçilmesini azaltır (genel bilgi, Mikolov 2013). Aşağıdaki betik bu görevi NumPy ile yazar: iki gömme matrisi (`v` merkez, `u` bağlam), minibatch güncellemeleri ve negatif örnekleme.

`g10_gomme.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""
Bölüm 70 - Skip-gram + negatif örnekleme (word2vec, Mikolov 2013),
sıfırdan NumPy.
Öğrenilen giriş gömmeleri: v (merkez), çıktı gömmeleri: u (bağlam).
Çıktılar: engine/veri/b70_gomme_pca.csv, konsol: en yakın komşular."""

import csv, os, re
from collections import Counter
import numpy as np

K = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
rng = np.random.default_rng(0)
metin = open(
    os.path.join(K, "korpus_egitim.txt"), encoding="utf-8"
).read()
kelimeler = re.findall(
    r"\w+", metin.replace("İ", "i").replace("I", "ı").lower()
)
say = Counter(kelimeler)
sozluk = [w for w, c in say.most_common() if c >= 5]
dizin = {w: i for i, w in enumerate(sozluk)}
seq = np.array([dizin[w] for w in kelimeler if w in dizin])
Vw, D, PENCERE, NEG, EPOK, BATCH, LR = (
    len(sozluk),
    100,
    2,
    5,
    5,
    1024,
    0.01,
)
print("sözcük=%d sözlük(min5)=%d boyut=%d" % (len(kelimeler), Vw, D))
v = (rng.random((Vw, D)) - 0.5) / D
u = np.zeros((Vw, D))
```

`g10_gomme.py`, 37–72. satırlar:

```python
p_neg = np.array([say[w] for w in sozluk], dtype=float) ** 0.75
p_neg /= p_neg.sum()
sig = lambda z: 1 / (1 + np.exp(-np.clip(z, -30, 30)))
for ep in range(EPOK):
    # Çiftler: her (merkez, bağlam) çifti, ±PENCERE içinde
    ms, cs = [], []
    for off in range(1, PENCERE + 1):
        ms += [seq[:-off], seq[off:]]
        cs += [seq[off:], seq[:-off]]
    M = np.concatenate(ms)
    C = np.concatenate(cs)
    sira = rng.permutation(len(M))
    M, C = M[sira], C[sira]
    kayip, n = 0.0, 0
    lr = LR * (1 - ep / EPOK)
    for i in range(0, len(M), BATCH):
        mc, oc = M[i : i + BATCH], C[i : i + BATCH]
        neg = rng.choice(Vw, size=(len(mc), NEG), p=p_neg)
        vc = v[mc]  # (B, D)
        uo = u[oc]  # (B, D)
        un = u[neg]  # (B, K, D)
        s_pos = sig(np.sum(vc * uo, 1))  # σ(u_o · v_c)
        s_neg = sig(np.einsum("bd,bkd->bk", vc, un))  # σ(u_n · v_c)
        g_pos = (s_pos - 1)[:, None]
        g_neg = s_neg[:, :, None]
        grad_v = g_pos * uo + np.sum(g_neg * un, 1)
        grad_uo = g_pos * vc
        grad_un = g_neg * vc[:, None, :]
        np.add.at(v, mc, -lr * grad_v)
        np.add.at(u, oc, -lr * grad_uo)
        np.add.at(u, neg.reshape(-1), -lr * grad_un.reshape(-1, D))
        kayip += (
            -np.log(s_pos + 1e-10).sum()
            - np.log(1 - s_neg + 1e-10).sum()
        )
        n += len(mc)
```

`g10_gomme.py`, 73–108. satırlar:

```python
    print(
        "epoch %d  ortalama kayıp/çift=%.4f  (lr=%.4f)"
        % (ep + 1, kayip / n, lr)
    )
np.save(os.path.join(K, "gomme_v.npy"), v)
json_sozluk = sozluk
open(
    os.path.join(K, "gomme_sozluk.txt"), "w", encoding="utf-8"
).write("\n".join(sozluk))

# Ortak yönü çıkar (anizotropi): ortalama vektörü düş, sonra normalize
# et
vm = v - v.mean(0)
norm = vm / np.linalg.norm(vm, axis=1, keepdims=True)


def komsu(w, k=6):
    i = dizin[w]
    s = norm @ norm[i]
    s[i] = -1
    idx = np.argsort(-s)[:k]
    return [(sozluk[j], round(float(s[j]), 3)) for j in idx]


for w in [
    "model",
    "gömme",
    "kayıp",
    "dikkat",
    "tokenizasyon",
    "kelime",
    "sinir",
    "eğitim",
]:
    if w in dizin:
        print("%-14s -> %s" % (w, komsu(w)))
```

`g10_gomme.py`, 109–134. satırlar:

```python
    else:
        print("%-14s sözlükte yok" % w)

# PCA (SVD) ile 2B izdüşüm: en sık 120 sözcük
ilk = 120
X = norm[:ilk] - norm[:ilk].mean(0)
U, S, Vt = np.linalg.svd(X, full_matrices=False)
Z = X @ Vt[:2].T
oran = (S[:2] ** 2).sum() / (S**2).sum()
print("PCA ilk iki bileşen açıklanan varyans = %.3f" % oran)
with open(
    os.path.join(VERI, "b70_gomme_pca.csv"),
    "w",
    encoding="utf-8",
    newline="",
) as f:
    cw = csv.writer(f)
    cw.writerow(["sozcuk", "x", "y"])
    for j in range(ilk):
        cw.writerow(
            [
                sozluk[j],
                round(float(Z[j, 0]), 5),
                round(float(Z[j, 1]), 5),
            ]
        )
```


Çıktı (`cikti_g10.txt`):

```term
sözcük=361429 sözlük(min5)=8276 boyut=100
epoch 1  ortalama kayıp/çift=3.4461  (lr=0.0100)
epoch 2  ortalama kayıp/çift=2.7165  (lr=0.0080)
epoch 3  ortalama kayıp/çift=2.5789  (lr=0.0060)
epoch 4  ortalama kayıp/çift=2.5259  (lr=0.0040)
epoch 5  ortalama kayıp/çift=2.5000  (lr=0.0020)
model          -> [('kümesinde', 0.806), ('koşulu', 0.797), ('sınıfta',
    0.79), ('neredeyse', 0.763), ('kümesi', 0.76), ('su', 0.758)]
gömme          -> [('tutarsızlık', 0.993), ('dolu_degil', 0.992),
    ('vektörleştirilmiş', 0.992), ('saldırıya', 0.992),
    ('denetleyicisi', 0.991), ('downsampling', 0.991)]
kayıp          -> [('tehdit', 0.938), ('simetrik', 0.938), ('ortalama',
    0.932), ('üstel', 0.926), ('pay', 0.923), ('aralık', 0.92)]
dikkat         -> [('kodun', 0.88), ('sorunun', 0.874), ('indeksin',
    0.872), ('biz', 0.867), ('çıkacak', 0.864), ('ilke', 0.862)]
tokenizasyon   sözlükte yok
kelime         -> [('gizli', 0.939), ('deneme', 0.925), ('matrisin',
    0.922), ('gradyanını', 0.919), ('geldiğinde', 0.918), ('kur',
    0.916)]
sinir          -> [('uygulamasıdır', 0.939), ('veritabanı', 0.938),
    ('dag', 0.923), ('cümleyle', 0.92), ('ekip', 0.919), ('gidiş',
    0.912)]
eğitim         -> [('doğruluğu', 0.833), ('test', 0.826), ('doğruluk',
    0.821), ('kümesinde', 0.779), ('kaybı', 0.765), ('öğrenme', 0.763)]
PCA ilk iki bileşen açıklanan varyans = 0.378
```


Çıktı, bu küçük derlemde (361 bin sözcük, eşik 5 ile 8276 sözcüklük sözlük) gömmenin ne kadar işe yaradığını dürüstçe gösterir. Kayıp 3,45'ten 2,50'ye iner. Ham gömmelerin tüm benzerlikleri 0,9 üzerinde çıkıyordu; çünkü vektörler ortak bir yön etrafında toplanmıştı (**anizotropi**). Ortalamayı çıkarıp normalize ettikten sonra "eğitim" için en yakın komşular `doğruluğu` (0,833), `test` (0,826), `doğruluk` (0,821), `kaybı` (0,765), `öğrenme` (0,763) olur; bunlar makul sözcüklerdir. Ama "dikkat" için komşular (`kodun`, `sorunun`) anlamsal olarak zayıftır. Bu, küçük bir derlemde gömmenin sınırıdır. Büyük, çeşitli bir derlemde aynı algoritma, çok daha iyi komşular üretir (genel bilgi).

Bu sonucu okurken iki tuzağa dikkat et. Birincisi, "tokenizasyon" sözcüğü sözlükte yoktur: eşik 5'ten az geçtiği için word2vec ona gömme atamaz. Bu, sözcük düzeyi gömmenin OOV problemidir ve BPE'nin neden tercih edildiğinin başka bir nedenidir. İkincisi, benzerlik yalnızca yönü ölçer; "benzer" bir kelime, eşanlamlı olmak zorunda değildir. "Eğitim" ile "doğruluk" aynı alanda geçer, ama eşanlamlı değildir.

Şekil 70.5, öğrenilen gömmelerin ilk iki ana bileşenini (PCA, Bölüm 61) gösterir. Yalnızca en sık 120 sözcük çizilmiştir; ilk iki bileşenin açıkladığı varyans yüzde 37,8'dir. Bu kadar düşük bir oran, iki boyutun geniş bir anlam yapısını taşımadığını gösterir; şekil, görselleştirme için bir kolaylıktır, bir kanıt değildir.

![Şekil 70.5: Skip-gram gömmelerinin en sık 120 sözcüğün PCA izdüşümü](gorseller/b70_gomme_pca.png)

### Statik ve bağlamsal gömmeler

word2vec gömmesi **statiktir**: "yüz" kelimesi (yüz sayısı mı, yüz ifadesi mi?) her bağlamda aynı vektörü alır. Bir dil modeli ise her belirtecin gömmesini, içinde bulunduğu bağlama göre yeniden hesaplar. Bölüm 69'daki Transformer bloklarının ilk katmanına giren gömme statiktir, ama sonraki katmanların çıktısı bağlamsaldır. Bu fark, modern dil modellerinin neden sözcük anlamını bağlamdan çözebildiğini açıklar. Statik gömmeler hâlâ yararlıdır: hızlıdır, yorumlanması kolaydır ve küçük veride eğitilebilir; ama belirsiz sözcüklerde yetersiz kalırlar.

## 70.6 Dil modelleme amaçları: nedensel, maskeli ve dizi-dizi

Bir modeli dil için eğitmek için birçok amaç seçilebilir. Hangisinin seçileceği, modelin ne için kullanılacağına bağlıdır. Üç ana aile vardır.

**Nedensel dil modeli** (causal LM) sonraki belirteci tahmin eder: `P(w_t | w_{<t})`. Bir belirteç, yalnızca kendisinden önceki belirteçleri görür. Bölüm 69'da maskeleme ile uyguladığımız üçgen maske bunu sağlar. GPT ailesi bu yaklaşımı kullanır; metin üretme için doğaldır, çünkü üretim de soldan sağa adım adım yapılır. Bu bölümde kurduğumuz mini-GPT bu ailedendir.

**Maskeli dil modeli** (masked LM) bir cümlenin belirli belirteçlerini gizler ve onları çevresindeki bağlamdan tahmin eder. BERT bu amaçla eğitilmiştir (Devlin ve arkadaşları 2019, genel bilgi). Her belirteç, hem soluna hem sağına bakabildiği için sınıflandırma ve anlama görevlerinde güçlüdür; ancak doğrudan metin üretmek için uygun değildir, çünkü üretim sırasında sağdaki belirteçler henüz yoktur. Maskeleme şeması kısaca şöyledir: rastgele seçilen belirteçlerin (genelde yüzde 15) bir kısmı özel bir `[MASK]` simgesiyle değiştirilir, bir kısmı rastgele başka bir belirteçle, geri kalanı olduğu gibi bırakılır; kayıp yalnızca seçilen konumlarda hesaplanır.

**Dizi-dizi** (seq2seq) modelde bir kodlayıcı girdiyi okur, bir çözücü çıktıyı üretir. T5 bütün görevleri bu biçime çevirerek eğitilir (genel bilgi, Raffel ve arkadaşları 2020). Çeviri ve özetleme doğal olarak bu ailedendir; kodlayıcının çift yönlü bağlamı, çözücünün ise nedensel üretimi kullanır.

Bu bölümde yalnızca nedensel modeli eğitiyoruz. Hem üretim hem de perplexity ölçümü için en basit çerçeve budur ve bu çerçeve, sonraki bölümde gördüğümüz LLM sistemlerinin temelidir.

## 70.7 Küçük bir GPT'yi sıfırdan eğitmek

Şimdi her parçayı bir araya getiriyoruz. Mimari Bölüm 69'daki Transformer bloğuyla aynıdır: çok başlı nedensel dikkat, önce-normalizasyon (LayerNorm girişte), GELU'lu bir MLP ve artık bağlantılar. Girdi gömmesi ile çıktı başlığı aynı matrisi paylaşır (**ağırlık paylaşımı**); bu, parametre sayısını yaklaşık yarıya indirmez ama 2149 × 128'lik büyük bir matrisi iki kez saklamayı önler.

Aşağıdaki modül, bloğu ve modeli sıfırdan yazar. Bölüm 69'da gördüğümüz tek fark, dikkat hesabının açıkça yazılmış olmasıdır: `QKᵀ/√d` ölçekleme, nedensel maske ve softmax.

`gpt_b70.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""Bölüm 70 - Küçük nedensel (decoder-only) GPT, sıfırdan.

Bölüm 69'daki blokların aynısı: çok başlı nedensel dikkat, önce-
normalizasyon
(pre-LN), GELU'lu MLP ve artık bağlantılar. Ağırlık paylaşımı: girdi
gömmesi ile çıktı başlığı aynı matrisi kullanır.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class CokBasliDikkat(nn.Module):
    def __init__(self, d, bas, ctx, dusme):
        super().__init__()
        self.bas, self.hd = bas, d // bas
        self.qkv = nn.Linear(d, 3 * d)
        self.proj = nn.Linear(d, d)
        self.dusme = nn.Dropout(dusme)
        maske = torch.tril(torch.ones(ctx, ctx)).view(1, 1, ctx, ctx)
        self.register_buffer("maske", maske, persistent=False)

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.qkv(x).split(C, dim=2)
        q = q.view(B, T, self.bas, self.hd).transpose(1, 2)
        k = k.view(B, T, self.bas, self.hd).transpose(1, 2)
        v = v.view(B, T, self.bas, self.hd).transpose(1, 2)
        a = (q @ k.transpose(-2, -1)) / math.sqrt(self.hd)
        a = a.masked_fill(
            self.maske[:, :, :T, :T] == 0, float("-inf")
        )
        a = self.dusme(F.softmax(a, dim=-1))
```

`gpt_b70.py`, 37–72. satırlar:

```python
        y = (a @ v).transpose(1, 2).reshape(B, T, C)
        return self.dusme(self.proj(y))


class Blok(nn.Module):
    def __init__(self, d, bas, ctx, dusme):
        super().__init__()
        self.ln1 = nn.LayerNorm(d)
        self.dikkat = CokBasliDikkat(d, bas, ctx, dusme)
        self.ln2 = nn.LayerNorm(d)
        self.mlp = nn.Sequential(
            nn.Linear(d, 4 * d),
            nn.GELU(),
            nn.Linear(4 * d, d),
            nn.Dropout(dusme),
        )

    def forward(self, x):
        x = x + self.dikkat(self.ln1(x))
        return x + self.mlp(self.ln2(x))


class MiniGPT(nn.Module):
    def __init__(self, sozluk, ctx=128, d=128, L=4, bas=4, dusme=0.1):
        super().__init__()
        self.ctx = ctx
        self.tok = nn.Embedding(sozluk, d)
        self.pos = nn.Embedding(ctx, d)
        self.drop = nn.Dropout(dusme)
        self.bloklar = nn.ModuleList(
            Blok(d, bas, ctx, dusme) for _ in range(L)
        )
        self.ln_f = nn.LayerNorm(d)
        self.head = nn.Linear(d, sozluk, bias=False)
        self.head.weight = self.tok.weight  # ağırlık paylaşımı
        self.apply(self._ilk)
```

`gpt_b70.py`, 73–103. satırlar:

```python

    @staticmethod
    def _ilk(m):
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, std=0.02)
        if isinstance(m, nn.Linear) and m.bias is not None:
            nn.init.zeros_(m.bias)

    def gizli(self, idx):
        T = idx.shape[1]
        konum = torch.arange(T, device=idx.device)
        x = self.drop(self.tok(idx) + self.pos(konum))
        for blok in self.bloklar:
            x = blok(x)
        return self.ln_f(x)

    def forward(self, idx, hedef=None):
        h = self.gizli(idx)
        logit = self.head(h)
        if hedef is None:
            return logit, None
        kayip = F.cross_entropy(
            logit.reshape(-1, logit.size(-1)), hedef.reshape(-1)
        )
        return logit, kayip


def parametre_say(model):
    return sum(
        p.numel() for p in model.parameters() if p.requires_grad
    )
```


Eğitim betiği ayrı bir dosyadadır. Veri, eğitim belirteçlerinden 129'luk bloklara ayrılır: her blok 128 girdi ve bir kaydırılmış hedef belirteci içerir. Her adımda 32 blok rastgele seçilir. Optimizer AdamW'dir (Bölüm 64): ağırlık azaltma yalnızca 2 boyutlu ağırlıklara uygulanır, normalizasyon ve sapma parametrelerine uygulanmaz. Öğrenme oranı 200 adımlık bir ısınma ile 10⁻³'e yükselir, sonra kosinüs eğrisiyle 10⁻⁴'e iner. Gradyanlar 1,0'da kırpılır. GPU'da karma hassasiyet (AMP, Bölüm 65) kullanılır. Doğrulama perplexity'si her 250 adımda ölçülür ve en iyi nokta, bu ölçüme göre seçilir; test kümesi yalnızca son raporlamada kullanılır.

`g05_gpt.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""Bölüm 70 - Küçük GPT'yi sıfırdan ön-eğitmek (dil modelleme).

Kullanım:
  python g05_gpt.py --seed 0 --tag ana --save 1
  python g05_gpt.py --seed 0 --d 64 --L 2 --frac 0.25 --tag olcek
Veri: tok_egitim.npy (eğitim), tok_dogrulama.npy (en iyi noktayı
seçmek
için), tok_test.npy (yalnızca son raporlama). Pencereler bloklardır:
her blok ctx+1 tokendir; hedef, girdinin bir kaydırılmış hâlidir.
"""

import argparse, csv, math, os, time
import numpy as np
import torch
from gpt_b70 import MiniGPT, parametre_say

K = os.path.dirname(os.path.abspath(__file__))
V = 2149


def bloklar(dizi, ctx):
    n = len(dizi) // (ctx + 1)
    return torch.tensor(
        dizi[: n * (ctx + 1)].reshape(n, ctx + 1), dtype=torch.long
    )


def degerlendir(model, veri, cihaz, ctx):
    model.eval()
    toplam, sayi = 0.0, 0
    with torch.no_grad():
        for i in range(0, len(veri), 64):
            b = veri[i : i + 64].to(cihaz)
            x, y = b[:, :-1], b[:, 1:]
            with torch.autocast(
```

`g05_gpt.py`, 37–72. satırlar:

```python
                cihaz.type, enabled=cihaz.type == "cuda"
            ):
                _, kayip = model(x, y)
            toplam += kayip.item() * y.numel()
            sayi += y.numel()
    model.train()
    return math.exp(toplam / sayi)


def egit(
    seed=0,
    d=128,
    L=4,
    bas=4,
    ctx=128,
    steps=3000,
    frac=1.0,
    lr=1e-3,
    batch=32,
    tag="ana",
    save=False,
    log=True,
):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    cihaz = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    tr = np.load(os.path.join(K, "tok_egitim.npy")).astype(np.int64)
    va = np.load(os.path.join(K, "tok_dogrulama.npy")).astype(
        np.int64
    )
    te = np.load(os.path.join(K, "tok_test.npy")).astype(np.int64)
    B_tr = bloklar(tr, ctx)
    # Veri ölçeği: rastgele bir blok alt kümesi (sabit tohumla)
    secim = rng.choice(
```

`g05_gpt.py`, 73–108. satırlar:

```python
        len(B_tr), size=int(frac * len(B_tr)), replace=False
    )
    B_tr = B_tr[torch.as_tensor(secim)]
    B_va, B_te = bloklar(va, ctx), bloklar(te, ctx)

    model = MiniGPT(V, ctx=ctx, d=d, L=L, bas=bas, dusme=0.1).to(
        cihaz
    )
    dec = [p for p in model.parameters() if p.dim() >= 2]
    nodec = [p for p in model.parameters() if p.dim() < 2]
    opt = torch.optim.AdamW(
        [
            {"params": dec, "weight_decay": 0.1},
            {"params": nodec, "weight_decay": 0.0},
        ],
        lr=lr,
        betas=(0.9, 0.95),
    )
    isinma = 200

    def takvim(adim):
        if adim < isinma:
            return lr * (adim + 1) / isinma
        ilerleme = (adim - isinma) / max(1, steps - isinma)
        return lr * (
            0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * ilerleme))
        )

    amp = cihaz.type == "cuda"
    olcekleyici = torch.amp.GradScaler("cuda", enabled=amp)
    en_iyi = (float("inf"), None, 0)
    kayitlar = []
    t0 = time.time()
    kayip_top = 0.0
    for adim in range(steps):
        for g in opt.param_groups:
```

`g05_gpt.py`, 109–144. satırlar:

```python
            g["lr"] = takvim(adim)
        sec = torch.randint(len(B_tr), (batch,))
        b = B_tr[sec].to(cihaz)
        x, y = b[:, :-1], b[:, 1:]
        with torch.autocast(cihaz.type, enabled=amp):
            _, kayip = model(x, y)
        opt.zero_grad(set_to_none=True)
        olcekleyici.scale(kayip).backward()
        olcekleyici.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        olcekleyici.step(opt)
        olcekleyici.update()
        kayip_top += kayip.item()
        if (adim + 1) % 250 == 0 or adim == steps - 1:
            vp = degerlendir(model, B_va, cihaz, ctx)
            egitim_loss = (
                kayip_top / 250
                if (adim + 1) % 250 == 0
                else kayip_top / ((adim % 250) + 1)
            )
            kayitlar.append((adim + 1, egitim_loss, vp))
            if log:
                print(
                    "adım %5d  eğitim kayıp=%.4f  doğrulama "
                    "ppl=%.2f  (%.0f sn)"
                    % (adim + 1, egitim_loss, vp, time.time() - t0)
                )
            kayip_top = 0.0
            if vp < en_iyi[0]:
                en_iyi = (
                    vp,
                    {
                        k: v.detach().clone()
                        for k, v in model.state_dict().items()
                    },
                    adim + 1,
```

`g05_gpt.py`, 145–180. satırlar:

```python
                )
    sure = time.time() - t0
    model.load_state_dict(en_iyi[1])
    test_ppl = degerlendir(model, B_te, cihaz, ctx)
    sonuc = {
        "seed": seed,
        "d": d,
        "L": L,
        "frac": frac,
        "parametre": parametre_say(model),
        "en_iyi_adim": en_iyi[2],
        "dogrulama_ppl": en_iyi[0],
        "test_ppl": test_ppl,
        "sure_sn": sure,
        "adim_basi_ms": 1000 * sure / steps,
        "cihaz": str(cihaz),
        "egri": kayitlar,
        "model": model,
    }
    if save:
        torch.save(
            {
                "state": en_iyi[1],
                "d": d,
                "L": L,
                "bas": bas,
                "ctx": ctx,
            },
            os.path.join(K, "gpt_%s_%d.pt" % (tag, seed)),
        )
    with open(
        os.path.join(K, "egri_%s_%d.csv" % (tag, seed)),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
```

`g05_gpt.py`, 181–216. satırlar:

```python
        cw = csv.writer(f)
        cw.writerow(["adim", "egitim_kayip", "dogrulama_ppl"])
        cw.writerows(kayitlar)
    return sonuc


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--d", type=int, default=128)
    p.add_argument("--L", type=int, default=4)
    p.add_argument("--bas", type=int, default=4)
    p.add_argument("--steps", type=int, default=3000)
    p.add_argument("--frac", type=float, default=1.0)
    p.add_argument("--tag", type=str, default="ana")
    p.add_argument("--save", type=int, default=0)
    a = p.parse_args()
    s = egit(
        seed=a.seed,
        d=a.d,
        L=a.L,
        bas=a.bas,
        steps=a.steps,
        frac=a.frac,
        tag=a.tag,
        save=bool(a.save),
    )
    print(
        "parametre=%d  en iyi adım=%d  doğrulama ppl=%.2f  "
        "test ppl=%.2f  "
        "süre=%.0f sn  adım başı=%.1f ms  cihaz=%s"
        % (
            s["parametre"],
            s["en_iyi_adim"],
            s["dogrulama_ppl"],
            s["test_ppl"],
```

`g05_gpt.py`, 217–221. satırlar:

```python
            s["sure_sn"],
            s["adim_basi_ms"],
            s["cihaz"],
        )
    )
```


Model 1 084 800 parametre taşır ve üç tohumla eğitilmiştir. Aşağıda seed 0 için eğitim ve doğrulama eğrisinin işaretli noktaları yer alır.

Çıktı (`out_ana_0.txt`):

```term
adım   250  eğitim kayıp=6.4448  doğrulama ppl=224.27  (9 sn)
adım   500  eğitim kayıp=5.0561  doğrulama ppl=127.75  (19 sn)
adım   750  eğitim kayıp=4.6769  doğrulama ppl=104.46  (28 sn)
adım  1000  eğitim kayıp=4.4727  doğrulama ppl=90.15  (37 sn)
adım  1250  eğitim kayıp=4.3242  doğrulama ppl=80.83  (46 sn)
adım  1500  eğitim kayıp=4.2082  doğrulama ppl=74.56  (56 sn)
adım  1750  eğitim kayıp=4.1169  doğrulama ppl=69.76  (65 sn)
adım  2000  eğitim kayıp=4.0401  doğrulama ppl=66.36  (74 sn)
adım  2250  eğitim kayıp=3.9814  doğrulama ppl=64.20  (84 sn)
adım  2500  eğitim kayıp=3.9371  doğrulama ppl=62.69  (93 sn)
adım  2750  eğitim kayıp=3.9058  doğrulama ppl=61.55  (102 sn)
adım  3000  eğitim kayıp=3.8865  doğrulama ppl=60.77  (111 sn)
parametre=1084800  en iyi adım=3000  doğrulama ppl=60.77  test ppl=62.83
    süre=111 sn  adım başı=37.1 ms  cihaz=cuda
```


Tohum 0 için: adım 250'de doğrulama perplexity'si 224, adım 1000'de 90, adım 2000'de 66, adım 3000'de 60,8 olur. Eğitim kaybı 6,44'ten 3,89 nat'a iner. Eğri 3000 adımda hâlâ düşmektedir; yani bu bütçe, modeli tam olarak yakınsatmaz. Bu bilinçli bir seçimdir: amacımız, uzun bir eğitimi değil, eğitim döngüsünün davranışını ve ölçeklemeyi görmek. Eğitim kaybı 3,89 nat (bu, yaklaşık 49 perplexity'ye karşılık gelir) iken doğrulama perplexity'si 60,8 (ln 60,8 ≈ 4,11 nat) olur. Aradaki fark, hafif bir genelleme boşluğudur; bu bütçede belirgin bir aşırı uyum yoktur.

![Şekil 70.6: Eğitim kaybı ve doğrulama perplexity'si; üç tohum ve n-gram tabanları](gorseller/b70_gpt_egri.png)

Üç tohumun test perplexity'leri 62,83, 62,41 ve 62,35'tir; ortalama 62,53, örneklem standart sapması 0,26'dır. Aynı belirteçler üzerinde unigram 828, bigram 127, trigram 246 veriyordu. Mini-GPT bigram'ın yaklaşık yarısı kadar şaşırır. Yani bağlamı yalnızca bir önceki belirteçle sınırlı olmayan, paylaşımlı bir gömme uzayı kullanan model, seyrekliği büyük ölçüde aşar. Bu, Bölüm 70.2'de seyrekliğin neden tıkandığını gösteren ölçümün doğrudan devamıdır.

Eğitim hızına bakalım. Bu ölçüm, GPU'nun gerçekten boş olduğu bir anda alınmıştır (başlangıçta kullanım yüzde 0; ölçüm sırasında kullanım yüzde 12'ye çıkmıştır, bu yüzden biraz gürültülü olabilir). Aşağıdaki betik adım süresini ve üretim hızını ölçer.

`g13_zaman.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""
Bölüm 70 - Zamanlama: eğitim adımı ve KV önbelleksiz üretim (token/s).
Yalnızca GPU boşken çalıştırılır; nvidia-smi durumu başta ve sonda
yazılır."""

import os, statistics, subprocess, time
import torch
from gpt_b70 import MiniGPT

K = os.path.dirname(os.path.abspath(__file__))


def gpu():
    return subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=utilization.gpu,memory.used",
            "--format=csv,noheader",
        ],
        capture_output=True,
        text=True,
    ).stdout.strip()


print("başlangıç GPU:", gpu())
dev = torch.device("cuda")
torch.manual_seed(0)
m = MiniGPT(2149, ctx=128, d=128, L=4, bas=4, dusme=0.1).to(dev)
opt = torch.optim.AdamW(m.parameters(), lr=1e-4)
scaler = torch.amp.GradScaler("cuda")
x = torch.randint(0, 2149, (32, 128), device=dev)
y = torch.randint(0, 2149, (32, 128), device=dev)


def adim():
```

`g13_zaman.py`, 37–72. satırlar:

```python
    with torch.autocast("cuda", dtype=torch.float16):
        _, k = m(x, y)
    opt.zero_grad()
    scaler.scale(k).backward()
    scaler.step(opt)
    scaler.update()


for _ in range(30):
    adim()
torch.cuda.synchronize()
olcumler = []
for _ in range(3):
    t0 = time.time()
    for _ in range(200):
        adim()
    torch.cuda.synchronize()
    olcumler.append(1000 * (time.time() - t0) / 200)
print(
    "eğitim adımı (batch 32 x ctx 128, AMP): ms = %s, medyan=%.2f"
    % ([round(v, 2) for v in olcumler], statistics.median(olcumler))
)
m.eval()
with torch.no_grad():
    idx = torch.randint(0, 2149, (1, 16), device=dev)
    for _ in range(20):
        idx = torch.cat(
            [
                idx,
                m(idx[:, -128:])[0][:, -1].argmax(-1, keepdim=True),
            ],
            1,
        )
    torch.cuda.synchronize()
    t0 = time.time()
    for _ in range(200):
```

`g13_zaman.py`, 73–86. satırlar:

```python
        idx = torch.cat(
            [
                idx,
                m(idx[:, -128:])[0][:, -1].argmax(-1, keepdim=True),
            ],
            1,
        )
    torch.cuda.synchronize()
print(
    "üretim (KV önbelleksiz, bağlam<=128): %.2f ms/token = "
    "%.1f token/s"
    % (1000 * (time.time() - t0) / 200, 200 / (time.time() - t0))
)
print("bitiş GPU:", gpu())
```


Çıktı (`cikti_g13.txt`):

```term
başlangıç GPU: 0 %, 1143 MiB
eğitim adımı (batch 32 x ctx 128, AMP): ms = [17.59, 17.37, 17.39],
    medyan=17.39
üretim (KV önbelleksiz, bağlam<=128): 3.81 ms/token = 262.7 token/s
bitiş GPU: 12 %, 1609 MiB
```


Boş kartta, batch 32 × bağlam 128 ile bir eğitim adımı medyan 17,4 ms sürer. Ön-eğitim koşularının kendisi ise GPU paylaşılırken yapıldı ve adım başına 34–37 ms ölçüldü; bu yüzden eğitim sürelerini raporlarken hangi koşulda ölçüldüğünü yazmak gerekir. Üretim tarafında her yeni belirteç için tüm bağlamın yeniden işlendiği (KV önbelleği olmadan) basit bir döngü 3,8 ms/belirteç, yani yaklaşık 263 belirteç/saniye verir. Bölüm 69'da gördüğümüz KV önbelleği bu adımın maliyetini, yeni belirteç başına yalnızca tek bir sorgu hesabına indirir.

### Ölçekleme: model boyutu ve veri miktarı

Büyük dil modellerinin davranışına ilişkin en tanınmış gözlem, doğrulama kaybının model boyutu, veri miktarı ve işlem gücüyle **kuvvet yasası** biçiminde azaldığıdır (Kaplan ve arkadaşları 2020; Hoffmann ve arkadaşları 2022, genel bilgi). Bu gözlemi, bu bölümün küçük ölçeğinde kendi ölçümümüzle sınarız. İki eksen vardır: model boyutu (d ve L değişir, veri aynıdır) ve veri miktarı (model aynıdır, eğitim blokları alt küme olarak seçilir). Her noktada tek bir tohum ve 3000 adım kullanılmıştır.

Aşağıdaki betik bu koşuları ve ölçekleme tablosunu hazırlar. Koşuların kendisi `g05_gpt.py` ile `--d`, `--L` ve `--frac` seçenekleriyle yapılmıştır; `g14_ozet.py` bu çıktılardan tabloyu üretir ve bu bölümün ilk ince ayar özetini de yazar.

`g14_ozet.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""
Şekil/tablo CSV'leri: ince ayar özeti (3 tohum) ve ölçekleme
noktaları.
"""

import csv, json, os, re, statistics as st
from collections import defaultdict

K = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
rows = [
    json.loads(l)
    for l in open(
        os.path.join(K, "sonuc_ince_ayar.jsonl"), encoding="utf-8"
    )
]
g = defaultdict(list)
for r in rows:
    g[(r["mod"], r["r"])].append(r)
sira = [
    ("sifirdan", 0),
    ("tam", 0),
    ("dogrusal", 0),
    ("lora", 1),
    ("lora", 2),
    ("lora", 4),
    ("lora", 8),
    ("lora", 16),
]
with open(
    os.path.join(VERI, "b70_ince_ayar.csv"),
    "w",
    encoding="utf-8",
    newline="",
) as f:
```

`g14_ozet.py`, 37–72. satırlar:

```python
    cw = csv.writer(f)
    cw.writerow(
        [
            "yontem",
            "r",
            "egitilebilir",
            "toplam",
            "test_acc_ort",
            "test_acc_sd",
            "test_f1_ort",
            "lm_once",
            "lm_sonra_ort",
            "lm_adaptor_kapali",
        ]
    )
    for k in sira:
        v = g[k]
        ta = [x["test_acc"] for x in v]
        lm_s = [x["lm_ppl_sonra"] for x in v]
        lm_k = [x["lm_ppl_adaptor_kapali"] for x in v]
        cw.writerow(
            [
                k[0],
                k[1],
                v[0]["egitilebilir"],
                v[0]["toplam"],
                round(st.mean(ta), 4),
                round(st.stdev(ta), 4),
                round(st.mean(x["test_f1"] for x in v), 4),
                v[0]["lm_ppl_once"] if k[0] != "sifirdan" else "",
                round(st.mean(lm_s), 3) if k[0] != "sifirdan" else "",
                round(st.mean(lm_k), 3) if k[0] == "lora" else "",
            ]
        )
print("ince ayar CSV yazildi")
# Ölçekleme: ad, parametre, veri (token), en iyi doğrulama ppl, test
```

`g14_ozet.py`, 73–108. satırlar:

```python
# ppl
adlar = [
    ("olcek_d64", "d=64,L=2"),
    ("ana", "d=128,L=4 (ana)"),
    ("olcek_d192", "d=192,L=6"),
    ("olcek_f125", "veri %12.5"),
    ("olcek_f25", "veri %25"),
    ("olcek_f50", "veri %50"),
]
with open(
    os.path.join(VERI, "b70_olcek.csv"),
    "w",
    encoding="utf-8",
    newline="",
) as f:
    cw = csv.writer(f)
    cw.writerow(
        [
            "ad",
            "parametre",
            "egitim_token",
            "dogrulama_ppl",
            "test_ppl",
        ]
    )
    for tag, ad in adlar:
        fn = os.path.join(K, "egri_%s_0.csv" % tag)
        s = open(
            os.path.join(
                K,
                (
                    "out_%s.txt" % tag
                    if tag != "ana"
                    else "out_ana_0.txt"
                ),
            ),
```

`g14_ozet.py`, 109–132. satırlar:

```python
            encoding="utf-8",
        ).read()
        m = re.search(
            r"parametre=(\d+).*?doğrulama ppl=([\d.]+)\s+test "
            r"ppl=([\d.]+)",
            s,
        )
        frac = 1.0
        if "f125" in tag:
            frac = 0.125
        if "f25" in tag:
            frac = 0.25
        if "f50" in tag:
            frac = 0.5
        cw.writerow(
            [
                ad,
                m.group(1),
                int(int(frac * (782840 // 129)) * 129),
                m.group(2),
                m.group(3),
            ]
        )
        print(ad, m.groups())
```


Çıktı (`cikti_g14.txt`):

```term
ince ayar CSV yazildi
d=64,L=2 ('245824', '93.37', '96.58')
d=128,L=4 (ana) ('1084800', '60.77', '62.83')
d=192,L=6 ('3106752', '50.94', '52.21')
veri %12.5 ('1084800', '161.28', '165.82')
veri %25 ('1084800', '115.63', '118.12')
veri %50 ('1084800', '73.41', '75.47')
```


Model boyutu ekseninde üç nokta vardır: 245 bin parametreli modelin test perplexity'si 96,6, 1,08 milyonlu modelin 62,8 ve 3,1 milyonlu modelin 52,2'dir. Log-log eğimi −0,25'tir. Veri ekseninde dört nokta vardır: eğitim belirteçlerinin yüzde 12,5'i (97 782 belirteç) ile 165,8, yüzde 25 ile 118,1, yüzde 50 ile 75,5 ve tamamı (782 772) ile 62,8 perplexity verir; log-log eğimi −0,48'dir. Veri ekseninin eğimi, model ekseninkinden daha diktir. Bu, bu küçük ölçekte veri eklemenin model büyütmekten daha verimli olduğunu düşündürür; ama bu bir tek tohumlu ölçümdür ve model, bütçe olarak eşit değildir (büyük modeller aynı 3000 adımı daha pahalı yapar). Bu nedenle bu eğimleri evrensel sabitler olarak okumak yanlış olur.

![Şekil 70.7: Test perplexity'sinin model boyutuna ve eğitim belirteç sayısına göre log-log ölçeklemesi](gorseller/b70_olcek.png)

Veri eğrisinde dikkat çeken bir ayrıntı daha var. Yüzde 12,5 veri ile eğitilen modelin en iyi doğrulama noktası adım 500'dedir; sonrasında doğrulama kaybı yükselir. Yani az veriyle uzun eğitim, belleğe alma (ezberleme) demektir. Bu, aşırı uyumun (overfitting) ölçeklemedeki görünümüdür ve bir sonraki kısımda, ezberlemeyi ölçerken yeniden karşımıza çıkacaktır. Tam veriyle (782 772 belirteç) ise en iyi nokta 3000. adımdadır; bu bütçede model hâlâ öğrenmektedir.

## 70.8 Örnekleme: açgözlü, sıcaklık, top-k ve top-p

Eğitilmiş bir model her adımda bir olasılık dağılımı üretir. Bir sonraki belirteci bu dağılımdan nasıl seçtiğimiz, çıktının niteliğini belirler. En basit yol **açgözlü** (greedy) seçimdir: en yüksek olasılıklı belirteci al. Bu, kararlı ama tekrara düşmeye yatkın bir davranıştır.

Dağılımın keskinliğini ayarlamak için **sıcaklık** (temperature) `T` kullanılır: logitler `T`'ye bölünür, sonra softmax alınır. `T < 1` dağılımı keskinleştirir (açgözlüye yaklaşır), `T > 1` düzleştirir (daha rastgele). **Top-k** örneklemesi, yalnızca en yüksek `k` logitli belirteçleri tutar ve geri kalanları sıfırlar. **Top-p** (çekirdek, nucleus) örneklemesi ise olasılık kütlesi `p`'ye ulaşana kadar en olası belirteçleri tutar; sabit bir sayı yerine dağılımın şekline uyum sağlar. Bu yöntemlerin her biri ayrıca normalizasyon gerektirir: seçilmeyen belirteçlerin logiti `−∞` yapılır ve softmax yeniden alınır.

Bunu elle görmek için bir örnek yeterlidir. Logitler `[2,0; 1,0; 0,5; −1,0; 0,0]` olsun. Aşağıdaki betik, bu logitler üzerinde sıcaklık, top-k ve top-p dağılımlarını hesaplar. Ardından aynı eğitilmiş modelden dört yöntemle 300 belirteçlik üretim yapar ve her birinin çeşitliliğini (farklı ardışık belirteç çiftlerinin oranı, distinct-2) ölçer. Son olarak ezberlemeyi ölçer: üretilen 8 belirteçlik dizilerin kaçı eğitim verisinde birebir geçiyor?

`g08_ornekleme.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""Bölüm 70 - Örnekleme yöntemleri, tekrar ve ezberleme ölçümü.
(a) El ile logit örneği: sıcaklık, top-k, top-p dağılımları.
(b) ana_0 GPT'sinden üretim: açgözlü, sıcaklık, top-k, top-p.
(c) Ezberleme: üretilen 8-token dizilerinin eğitim verisinde birebir
geçmesi,
    doğrulama metninin kendi örtüşme taban oranıyla
    karşılaştırılır."""

import math, os, random
import numpy as np
import torch
import torch.nn.functional as F
from bpe_sifirdan import BPE
from gpt_b70 import MiniGPT

K = os.path.dirname(os.path.abspath(__file__))
V = 2149

# (a) El ile logit örneği
logit = np.array([2.0, 1.0, 0.5, -1.0, 0.0])


def softmax(z):
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


print("(a) logit =", logit)
for T in [1.0, 0.5, 2.0]:
    print("  T=%.1f p=" % T, np.round(softmax(logit / T), 4))


def topk(z, k):
    m = np.full_like(z, -np.inf)
```

`g08_ornekleme.py`, 37–72. satırlar:

```python
    idx = np.argsort(-z)[:k]
    m[idx] = z[idx]
    return softmax(m)


print("  top-k=2 p=", np.round(topk(logit, 2), 4))


def topp(z, p):
    s = softmax(z)
    o = np.argsort(-s)
    c = np.cumsum(s[o])
    son = np.searchsorted(c, p) + 1
    m = np.full_like(z, -np.inf)
    m[o[:son]] = z[o[:son]]
    return softmax(m), son


pp, son = topp(logit, 0.9)
print("  top-p=0.9 çekirdek boyutu=%d p=" % son, np.round(pp, 4))

# (b) Üretim
cihaz = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ck = torch.load(
    os.path.join(K, "gpt_ana_0.pt"),
    map_location="cpu",
    weights_only=True,
)
model = MiniGPT(
    V, ctx=ck["ctx"], d=ck["d"], L=ck["L"], bas=ck["bas"], dusme=0.0
)
model.load_state_dict(ck["state"])
model.to(cihaz).eval()
bj = __import__("json").load(
    open(os.path.join(K, "bpe_b70.json"), encoding="utf-8")
)
```

`g08_ornekleme.py`, 73–108. satırlar:

```python
b = BPE.yukle(bj["alfabe"], bj["kurallar"])


@torch.no_grad()
def uret(model, baslangic, n, yontem, T=1.0, k=40, p=0.9, tohum=0):
    g = torch.Generator(device=cihaz).manual_seed(tohum)
    idx = torch.tensor([baslangic], device=cihaz)
    for _ in range(n):
        ctx = idx[:, -model.ctx :]
        z = model(ctx)[0][:, -1, :].float()[0]
        if yontem == "acgozlu":
            nxt = int(z.argmax())
        else:
            z = z / T
            if yontem == "topk":
                v, _ = torch.topk(z, k)
                z[z < v[-1]] = -float("inf")
            if yontem == "topp":
                s, o = torch.sort(z, descending=True)
                c = torch.cumsum(F.softmax(s, 0), 0)
                # ilk p'yi aşan belirteç hariç
                maske = c - F.softmax(s, 0) > p
                s[maske] = -float("inf")
                z = torch.full_like(z, -float("inf"))
                z[o] = s
            nxt = int(
                torch.multinomial(F.softmax(z, 0), 1, generator=g)
            )
        idx = torch.cat([idx, torch.tensor([[nxt]], device=cihaz)], 1)
    return idx[0].tolist()


def d2(ids):
    bigram = list(zip(ids, ids[1:]))
    return len(set(bigram)) / max(1, len(bigram))

```

`g08_ornekleme.py`, 109–144. satırlar:

```python

ba = b.kodla("Bölüm 70: dil modelleri")
print(
    "\n(b) üretim (300 token), baslangic: 'Bölüm 70: dil modelleri'"
)
for ad, yon, T in [
    ("açgözlü", "acgozlu", 1.0),
    ("sıcaklık 0.8", "sicaklik", 0.8),
    ("top-k 40", "topk", 1.0),
    ("top-p 0.9", "topp", 1.0),
]:
    ids = (
        uret(
            model,
            ba,
            300,
            "topk" if yon == "sicaklik" else yon,
            T=T,
            tohum=1,
        )
        if yon != "sicaklik"
        else None
    )
    if yon == "sicaklik":
        ids = uret(model, ba, 300, "topp", T=T, p=1.0, tohum=1)
    print(
        "  %-14s distinct-2=%.3f  metin: %s..."
        % (
            ad,
            d2(ids[len(ba) :]),
            b.coz(ids[len(ba) :])[:90].replace("\n", " "),
        )
    )
print(
    "  not: sıcaklık satırı p=1.0 top-p ile yalnız sıcaklık "
    "etkisini ölçer"
```

`g08_ornekleme.py`, 145–180. satırlar:

```python
)

# (c) Ezberleme
tr = np.load(os.path.join(K, "tok_egitim.npy")).tolist()
va = np.load(os.path.join(K, "tok_dogrulama.npy")).tolist()
N = 8
egitim_ngram = set(tuple(tr[i : i + N]) for i in range(len(tr) - N))


def oran(dizi):
    top = len(dizi) - N
    return (
        sum(
            1
            for i in range(top)
            if tuple(dizi[i : i + N]) in egitim_ngram
        )
        / top
    )


print(
    "\n(c) ezberleme (%d-token dizi, eğitimde birebir geçen oranı)"
    % N
)
print("  doğrulama (taban örtüşme)  = %.4f" % oran(va[:20000]))
rng = random.Random(0)
uretim = uret(model, ba, 3000, "topp", T=1.0, p=0.9, tohum=7)[
    len(ba) :
]
print("  üretim (top-p 0.9, 3000 token)   = %.4f" % oran(uretim))
ilk = [model] * 0
rastgele = MiniGPT(
    V, ctx=ck["ctx"], d=ck["d"], L=ck["L"], bas=ck["bas"], dusme=0.0
)
rastgele.to(cihaz).eval()
```

`g08_ornekleme.py`, 181–187. satırlar:

```python
ru = uret(rastgele, ba, 3000, "topp", T=1.0, p=0.9, tohum=7)[
    len(ba) :
]
print("  rastgele (ilklenmemiş) model     = %.4f" % oran(ru))
open(
    os.path.join(K, "ornek_uretim.txt"), "w", encoding="utf-8"
).write(b.coz(uretim[:600]))
```


Çıktı (`cikti_g08.txt`):

```term
(a) logit = [ 2.   1.   0.5 -1.   0. ]
  T=1.0 p= [0.563  0.2071 0.1256 0.028  0.0762]
  T=0.5 p= [0.8292 0.1122 0.0413 0.0021 0.0152]
  T=2.0 p= [0.3745 0.2272 0.1769 0.0836 0.1378]
  top-k=2 p= [0.7311 0.2689 0.     0.     0.    ]
  top-p=0.9 çekirdek boyutu=4 p= [0.5793 0.2131 0.1293 0.     0.0784]

(b) üretim (300 token), baslangic: 'Bölüm 70: dil modelleri'
  açgözlü        distinct-2=0.070  metin: , bir sensöründen biridir. Bu
    bölümde gördüğümüz gibi bir sensöründen bir sensöründen biri...
  sıcaklık 0.8   distinct-2=0.793  metin: , 4 ve 58'de anlatük şekilde
    göreceğiz. Ölçüm, dört yöntemi ve iki hatayı sınır üzerinde (...
  top-k 40       distinct-2=0.853  metin: , Linux'ta sertOSIG, LSONCBAG
    (RF) ile yapıldı (GPICEYICEOAYEREMERT) ve WCTLSET baytı, bir...
  top-p 0.9      distinct-2=0.973  metin: , 48 bitten sonra fark, her
    segmentin de aynı döngünün bir düştüğüyoruz. Türü süreyi gecik...
  not: sıcaklık satırı p=1.0 top-p ile yalnız sıcaklık etkisini ölçer

(c) ezberleme (8-token dizi, eğitimde birebir geçen oranı)
  doğrulama (taban örtüşme)  = 0.0270
  üretim (top-p 0.9, 3000 token)   = 0.0027
  rastgele (ilklenmemiş) model     = 0.0000
```


El ile logitlerde sonuçlar şöyledir. `T = 1` için dağılım `[0,563; 0,207; 0,126; 0,028; 0,076]`tir (sıralama korunur, toplam 1). `T = 0,5` en olası belirtecin olasılığını 0,829'a çıkarır; `T = 2` dağılımı 0,375'e çeker. Top-k (k = 2) yalnızca iki belirtece izin verir ve dağılım `[0,731; 0,269]` olur. Top-p (p = 0,9) ise 0,563 + 0,207 + 0,126 + 0,076 = 0,972 olasılık kütlesine ulaşan dört belirteci tutar; beşincisi (0,028) dışarıda kalır. Burada top-p ile top-k farkı açıktır: top-k sabit sayıda belirteç seçer, top-p ise dağılımın durumuna göre seçimi değiştirir.

Üretim tablosu (aynı başlangıç metni, 300 belirteç) iki şeyi gösterir. Açgözlü üretim distinct-2 = 0,070 verir: yani belirteç çiftlerinin yüzde 7'si farklıdır, metin "bir sensöründen bir sensöründen" gibi bir döngüye girer. Top-p 0,9 ile çeşitlilik 0,973'e çıkar; ancak bu, metnin daha iyi olduğu anlamına gelmez. Yüksek çeşitlilik çoğu zaman tutarsızlıkla birlikte gelir; bu küçük modelin ürettiği "Linux'ta sertOSIG" gibi parçalar bunu gösterir. Tekrar ile tutarlılık arasındaki denge, sıcaklık ve top-p'nin birlikte ayarlanmasıyla kurulur ve görevden göreve değişir.

Ezberleme ölçümü, bir modelin eğitim verisini ne ölçüde kopyaladığını gösterir. Doğrulama metninin kendi 8 belirteçlik dizilerinin yüzde 2,70'i eğitim verisinde geçiyor; bu, kitabın kendi tekrarlarının (aynı terimler ve kalıplar) doğal taban oranıdır. Modelin ürettiği metinde bu oran yüzde 0,27'dir. Rastgele, eğitilmemiş bir modelde ise yüzde 0,00'dır. Yani üretilen metin, doğrulama metninden bile daha az eğitim dizisi kopyalar: model ezberlemiyor, dağılımı genelliyor. Bu sonuç, tek bir tohum ve tek bir üretim ile sınırlıdır; ezberlemeyi güvenle ölçmek için tüm test kümesinde ve birden çok üretimle değerlendirme gerekir.

## 70.9 İnce ayar: sınıflandırmadan LoRA'ya

Ön-eğitim, modeli genel bir dil bilgisiyle donatır. Bir görev için bu bilgiyi kullanmanın yolu **ince ayardır** (fine-tuning): ön-eğitimli ağırlıklardan başlayıp yeni görev üzerinde eğitmek. Bu bölümde görev, bir paragrafın kitabın hangi kısmından geldiğini tahmin etmektir (15 sınıf). Yöntemleri dört ailede karşılaştırıyoruz:

- **Sıfırdan** (scratch): aynı mimari, rastgele başlangıç; tüm ağırlıklar eğitilir. Ön-eğitimin değerini ölçmek için referanstır.
- **Tam ince ayar**: ön-eğitimli ağırlıkların tamamı, yeni görev üzerinde güncellenir.
- **Doğrusal sonda** (linear probe): ön-eğitimli gövde donuk; yalnızca üstüne eklenen sınıflandırma başlığı eğitilir.
- **LoRA** (düşük ranklı uyarlama; Hu ve arkadaşları 2021, genel bilgi): gövde donuk; her dikkat katmanına küçük, düşük ranklı bir güncelleme eklenir ve yalnızca o güncelleme eğitilir.

Görev için paragraflar, bölüm düzeyindeki bölmeden gelir: 7 716 eğitim, 1 509 doğrulama ve 1 513 test paragrafı. Model girdisi en fazla 128 belirteçtir; sınıflandırma, dizinin maskeli ortalamasına (son gizli durumların ortalaması) bir doğrusal katman uygulanarak yapılır. Nedensel modelde her konum, kendisinden öncekileri gördüğü için ortalama bir özet olarak kullanılabilir.

### LoRA: düşük ranklı güncelleme, sıfırdan

Tam ince ayarın sorunu, her görev için tam bir model kopyası gerektirmesidir. Bir `W` matrisi (d × d) için güncelleme `ΔW` de aynı boyuttadır. LoRA'nın gözlemi, büyük modellerin ince ayar sırasındaki `ΔW` değişimlerinin genellikle düşük ranklı olduğudur (Hu ve arkadaşları 2021, genel bilgi). Bu gözlemi Bölüm 48'deki SVD'den tanıyorsun: rankı `r` olan bir matris, `d × r` ve `r × d` iki matrisin çarpımı olarak yazılabilir. Bu yüzden güncellemeyi `ΔW = B A` olarak öğreniriz, burada `A` (r × d) Gauss ile, `B` (d × r) sıfır ile başlatılır. Sıfır başlatma, eğitimin başında `ΔW = 0` olmasını sağlar: model, ön-eğitimli haliyle başlar.

İleri geçiş şöyledir:

y = W x + (α / r) · B (A x)

![Şekil 70.8: LoRA güncellemesi: donuk W ve eğitilen A, B yolları](gorseller/b70_lora_semasi.png)

Ölçek `α / r` iki şeyi ayırır (Şekil 70.8 yapıyı gösterir): `r` değiştikçe güncellemenin büyüklüğünün kendiliğinden dengelenmesi. `α` sabit tutulursa, `r` arttığında her ek sütunun katkısı küçülür. Eğitilebilir parametre sayısı `2rd` (bir matris için) olur; tam matris `d²`dir. `d = 128` ve `r = 8` için bu, yüzde 12,5'tir (`2 · 8 · 128 = 2048` ile `128² = 16384`). Bu bölümde yalnızca dikkat katmanındaki üç doğrusal dönüşüme (QKV ve çıkış projeksiyonu) LoRA uyguladık. Blok başına eğitilebilir parametre `6rd`'dir; dört blok ve sınıflandırma başlığı için toplam `24rd + 1935` olur.

Aşağıdaki modül, LoRA'yı bir `Linear` katmanı etrafında sarmalayan bir sınıftır. Taban katman donar; `A` ve `B` eğitilir; birleştirme (merge) işlemi `W' = W + (α/r) B A` ile tek bir matris üretir, böylece çıkarım sırasında ek bir gecikme kalmaz.

`lora_b70.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""Bölüm 70 - LoRA (düşük ranklı uyarlama), sıfırdan.

Donmuş W (d_çıkış x d_giriş) yerine öğrenilen güncelleme:
    y = W x + (alpha / r) * B (A x)
A: r x d_giriş (Gauss ile başlar), B: d_çıkış x r (sıfır ile başlar).
B sıfırla başladığı için eğitimin başında çıktı, taban modelle
aynıdır.
"""

import math
import torch
import torch.nn as nn


class LoRALinear(nn.Module):
    def __init__(self, taban, r, alpha):
        super().__init__()
        self.taban = taban
        for p in self.taban.parameters():
            p.requires_grad = False  # W ve sapma donmuş
        self.r = r
        self.olcek = alpha / r
        giris = taban.in_features
        self.A = nn.Parameter(
            torch.randn(r, giris) / math.sqrt(giris)
        )
        self.B = nn.Parameter(torch.zeros(taban.out_features, r))
        self.acik = True  # adaptör etkin mi?

    def forward(self, x):
        if not self.acik:  # adaptör kapalı: yalnızca taban W
            return self.taban(x)
        delta = (x @ self.A.t()) @ self.B.t()
        return self.taban(x) + self.olcek * delta

```

`lora_b70.py`, 37–72. satırlar:

```python
    @torch.no_grad()
    def birlestir(self):
        """W' = W + (alpha/r) B A: çıkarımda ek gecikme kalmaz."""
        yeni = nn.Linear(
            self.taban.in_features,
            self.taban.out_features,
            bias=self.taban.bias is not None,
        )
        yeni.weight.copy_(
            self.taban.weight + self.olcek * (self.B @ self.A)
        )
        if self.taban.bias is not None:
            yeni.bias.copy_(self.taban.bias)
        return yeni


def lora_uygula(model, r, alpha=16.0, hedefler=("qkv", "proj")):
    """
    Her blokta dikkat katmanındaki seçilmiş doğrusal katmanları sarar.
    """
    for blok in model.bloklar:
        for ad in hedefler:
            taban = getattr(blok.dikkat, ad)
            setattr(blok.dikkat, ad, LoRALinear(taban, r, alpha))
    return model


def lora_parametreleri(model):
    return [
        p
        for n, p in model.named_parameters()
        if n.endswith((".A", ".B"))
    ]


def egitilebilir_say(model):
```

`lora_b70.py`, 73–84. satırlar:

```python
    return sum(
        p.numel() for p in model.parameters() if p.requires_grad
    )


def adaptor_durumu(model, acik):
    """
    Tüm LoRA katmanlarında adaptörü açar (True) ya da kapatır (False).
    """
    for m in model.modules():
        if isinstance(m, LoRALinear):
            m.acik = acik
```


Modülün doğruluğunu iki şekilde sınarız. Birincisi, küçük bir örnek: d = 4, r = 1. Aşağıdaki betik, bu örneği elle hesaplanabilir sayılarla kurar ve gerçek `LoRALinear` sınıfıyla karşılaştırır.

`g12_lora_ornek.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""
Bölüm 70 - LoRA küçük örneği (d=4, r=1): ileri geçiş, parametre
sayısı,
birleştirme (merge) eşdeğerliği. Gerçek LoRALinear sınıfı
kullanılır."""

import torch
from lora_b70 import LoRALinear

torch.set_default_dtype(torch.float64)
lin = torch.nn.Linear(4, 4, bias=False)
with torch.no_grad():
    lin.weight.copy_(torch.diag(torch.tensor([1.0, 2.0, 1.0, 0.5])))
lo = LoRALinear(lin, r=1, alpha=2.0)
with torch.no_grad():
    lo.A.copy_(torch.tensor([[0.5, 0.0, 1.0, 0.0]]))
    lo.B.copy_(torch.tensor([[2.0], [0.0], [0.0], [1.0]]))
x = torch.tensor([1.0, 2.0, 0.0, -1.0])
print("W x            =", lin(x).tolist())
print("A x            =", (lo.A @ x).tolist())
print("olcek=alpha/r  =", lo.olcek)
print("delta          =", (lo.olcek * (lo.B @ (lo.A @ x))).tolist())
print("y (adaptor)    =", lo(x).tolist())
print(
    "eğitilebilir: LoRA=%d, tam matris=%d"
    % (lo.A.numel() + lo.B.numel(), lin.weight.numel())
)
w2 = lo.birlestir()
print("W' = W+olcek*BA satırları:")
print(w2.weight.tolist())
print("y (birleşik)   =", w2(x).tolist())
print(
    "maks fark (birleşik - adaptör) = %.3e"
    % (w2(x) - lo(x)).abs().max().item()
)
```

`g12_lora_ornek.py`, 37–43. satırlar:

```python
X = torch.randn(1000, 4)
print(
    "1000 rastgele girdide maks fark = %.3e"
    % (w2(X) - lo(X)).abs().max().item()
)
lo.acik = False
print("adaptör kapalı y =", lo(x).tolist())
```


Çıktı (`cikti_g12.txt`):

```term
W x            = [1.0, 4.0, 0.0, -0.5]
A x            = [0.5]
olcek=alpha/r  = 2.0
delta          = [2.0, 0.0, 0.0, 1.0]
y (adaptor)    = [3.0, 4.0, 0.0, 0.5]
eğitilebilir: LoRA=8, tam matris=16
W' = W+olcek*BA satırları:
[[3.0, 0.0, 4.0, 0.0], [0.0, 2.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [1.0,
    0.0, 2.0, 0.5]]
y (birleşik)   = [3.0, 4.0, 0.0, 0.5]
maks fark (birleşik - adaptör) = 0.000e+00
1000 rastgele girdide maks fark = 1.776e-15
adaptör kapalı y = [1.0, 4.0, 0.0, -0.5]
```


Elle hesap şöyledir: `x = [1, 2, 0, −1]`, `A x = 0,5`, ölçek `α/r = 2`, `B (A x) = [2; 0; 0; 1] · 0,5 = [1; 0; 0; 0,5]`, dolayısıyla adaptör katkısı `2 · [1; 0; 0; 0,5] = [2; 0; 0; 1]`. Taban `W x = [1; 4; 0; −0,5]` olduğundan `y = [3; 4; 0; 0,5]`tir ve kod da aynı sonucu verir. Eğitilebilir parametre sayısı `2rd = 8`dir; tam matris 16 parametredir. İkinci ve daha önemli test birleştirme (merge) eşdeğerliğidir: `W' = W + (α/r) B A` ile hesaplanan tek matris, adaptörlü çıktıyla aynı sonucu verir (fark 0). Rastgele 1000 girdide en büyük fark 1,8·10⁻¹⁵ mertebesindedir; bu, kayan noktanın yuvarlama hatasıdır. Adaptör kapalıyken ise çıktı tamamen taban modelinkine döner (1; 4; 0; −0,5).

### Sınıflandırma ve felaket unutma: deneyin tasarımı

Üç tohumla dört aileyi karşılaştırmadan önce öğrenme oranlarını **yalnızca doğrulama kümesinde** seçtik. Her yöntem için iki aday, tohum 0 ile, beş epoch boyunca denendi. Sıfırdan için 10⁻³ (doğrulama doğruluğu 0,353; 3·10⁻⁴ için 0,345), tam ince ayar için 10⁻⁴ (0,396; 3·10⁻⁵ için 0,370), LoRA (r = 8) için 10⁻³ (0,366; 3·10⁻³ için 0,363) ve doğrusal sonda için 10⁻³ (0,303) seçildi. Her koşuda en iyi epoch, doğrulama doğruluğuna göre seçilir. Test kümesi yalnızca son raporlamada kullanılır.

Felaket unutmayı ölçmek için, her yöntem sonrasında ön-eğitim görevinin (sonraki belirteç tahmini) doğrulama perplexity'sini de ölçtük. Bu ölçüm, ön-eğitim doğrulama bloklarının 400 tanesi (yaklaşık 51 600 belirteç) üzerinde yapılır. Sınıflandırma başlığı bu ölçümde kullanılmaz; ölçüm, gövdenin tekrar bir dil modeli olarak ne kadar çalıştığını söyler. LoRA'da bu ölçümü, sınıflandırma eğitimi bittikten sonra, seçilen en iyi epoch'un ağırlıklarıyla iki durumda yaptık: adaptör açıkken (eğitilmiş modelin normal kullanımı) ve adaptör kapalıyken (aynı modelde yalnızca adaptör katkısı kesilmiş; bu, taban ağırlıkların durumudur).

Deney, tek bir betikte toplanır. Betik, dört yöntemi ve üç tohumu çalıştırır; her koşunun satırını bir JSON dosyasına ekler. Öğrenme oranı ızgarası da aynı betikle, adaptör kapalı perplexity ölçümü eklenmeden önce yapıldı; bu ölçüm dışında betik değişmedi.

`g06_ince_ayar.py`, 1–36. satırlar:

```python
# -*- coding: utf-8 -*-
"""
Bölüm 70 - Aşağı akış görevi: bir paragrafın hangi KISIMDAN geldiğini
sınıflandırmak (15 sınıf, Kısım I..XV). Etiket: %% kisim_no ön
bilgisi.

Modlar:
  sifirdan  : aynı mimari, rastgele ilk değerler, tüm ağırlıklar
  eğitilir
  tam       : ön-eğitimli GPT, tüm ağırlıklar eğitilir (tam ince ayar)
  dogrusal  : ön-eğitimli GPT donuk, yalnızca sınıflandırma başlığı
  (linear probe)
  lora      : ön-eğitimli GPT donuk, LoRA (A, B) + başlık eğitilir

Kullanım: python g06_ince_ayar.py --mod lora --r 8 --lr 1e-3 --seed 0
Sonuç satırı: sonuc_ince_ayar.jsonl (ek yazılır).
"""

import argparse, json, math, os, time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import f1_score
from bpe_sifirdan import BPE
from gpt_b70 import MiniGPT
from lora_b70 import lora_uygula, egitilebilir_say, adaptor_durumu

K = os.path.dirname(os.path.abspath(__file__))
V, CTX, SINIF = 2149, 128, 15
cihaz = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def veri_hazirla():
    par = json.load(
        open(os.path.join(K, "paragraflar.json"), encoding="utf-8")
```

`g06_ince_ayar.py`, 37–72. satırlar:

```python
    )
    bol = json.load(
        open(os.path.join(K, "bolum_bolme.json"), encoding="utf-8")
    )
    bj = json.load(
        open(os.path.join(K, "bpe_b70.json"), encoding="utf-8")
    )
    b = BPE.yukle(bj["alfabe"], bj["kurallar"])
    out = {}
    for anahtar in ("egitim", "dogrulama", "test"):
        idler = bol[anahtar]
        X = torch.zeros(len(idler), CTX, dtype=torch.long)
        M = torch.zeros(len(idler), CTX)
        y = torch.zeros(len(idler), dtype=torch.long)
        for j, i in enumerate(idler):
            t = b.kodla(par[i]["metin"])[:CTX]
            X[j, : len(t)] = torch.tensor(t)
            M[j, : len(t)] = 1.0
            y[j] = par[i]["kisim"]
        out[anahtar] = (X, M, y)
    return out


def taban_yukle():
    ck = torch.load(
        os.path.join(K, "gpt_ana_0.pt"),
        map_location="cpu",
        weights_only=True,
    )
    m = MiniGPT(
        V,
        ctx=ck["ctx"],
        d=ck["d"],
        L=ck["L"],
        bas=ck["bas"],
        dusme=0.1,
```

`g06_ince_ayar.py`, 73–108. satırlar:

```python
    )
    m.load_state_dict(ck["state"])
    return m


class Siniflandirici(nn.Module):
    def __init__(self, gpt):
        super().__init__()
        self.gpt = gpt
        self.baslik = nn.Linear(gpt.tok.embedding_dim, SINIF)

    def forward(self, x, m):
        h = self.gpt.gizli(x)  # (B, T, d)
        m = m.unsqueeze(-1)
        ortalama = (h * m).sum(1) / m.sum(1).clamp(
            min=1.0
        )  # maskeli ortalama
        return self.baslik(ortalama)


def modeli_kur(mod, r, seed, alpha=16.0):
    torch.manual_seed(seed)
    if mod == "sifirdan":
        gpt = MiniGPT(V, ctx=CTX, d=128, L=4, bas=4, dusme=0.1)
    else:
        gpt = taban_yukle()
    sn = Siniflandirici(gpt)
    if mod == "dogrusal":
        for p in sn.gpt.parameters():
            p.requires_grad = False
    elif mod == "lora":
        for p in sn.gpt.parameters():
            p.requires_grad = False
        lora_uygula(sn.gpt, r, alpha)
        for ad, p in sn.gpt.named_parameters():
            if ad.endswith((".A", ".B")):
```

`g06_ince_ayar.py`, 109–144. satırlar:

```python
                p.requires_grad = True
    return sn.to(cihaz)


@torch.no_grad()
def dogruluk(sn, X, M, y):
    sn.eval()
    tahmin = []
    for i in range(0, len(X), 128):
        tahmin.append(
            sn(X[i : i + 128].to(cihaz), M[i : i + 128].to(cihaz))
            .argmax(1)
            .cpu()
        )
    sn.train()
    t = torch.cat(tahmin)
    return (t == y).float().mean().item(), f1_score(
        y.numpy(), t.numpy(), average="macro"
    )


@torch.no_grad()
def dil_ppl(gpt, bloklar):
    """Ön-eğitim görevi (sonraki token): felaket unutmayı ölçer."""
    gpt.eval()
    toplam, say = 0.0, 0
    for i in range(0, len(bloklar), 64):
        b = bloklar[i : i + 64].to(cihaz)
        x, y = b[:, :-1], b[:, 1:]
        _, kayip = gpt(x, y)
        toplam += kayip.item() * y.numel()
        say += y.numel()
    gpt.train()
    return math.exp(toplam / say)


```

`g06_ince_ayar.py`, 145–180. satırlar:

```python
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mod", default="lora")
    p.add_argument("--r", type=int, default=8)
    p.add_argument("--alpha", type=float, default=16.0)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--batch", type=int, default=32)
    a = p.parse_args()

    veri = veri_hazirla()
    sn = modeli_kur(a.mod, a.r, a.seed, a.alpha)
    egitilebilir = egitilebilir_say(sn)
    toplam = sum(q.numel() for q in sn.parameters())
    params = [q for q in sn.parameters() if q.requires_grad]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.01)
    Xtr, Mtr, ytr = [t.to(cihaz) for t in veri["egitim"]]
    Xva, Mva, yva = veri["dogrulama"]
    Xte, Mte, yte = veri["test"]
    # Ön-eğitim doğrulama bloklarından 400 blok (LM kaybı, felaket
    # unutma)
    dva = np.load(os.path.join(K, "tok_dogrulama.npy")).astype(
        np.int64
    )
    n = len(dva) // 129
    lm_blok = torch.tensor(dva[: n * 129].reshape(n, 129))[:400]
    lm_taban = (
        dil_ppl(sn.gpt, lm_blok)
        if a.mod != "sifirdan"
        else float("nan")
    )

    en_iyi = (-1.0, None, 0)
    t0 = time.time()
    gecmis = []
```

`g06_ince_ayar.py`, 181–216. satırlar:

```python
    for ep in range(a.epochs):
        sira = torch.randperm(len(Xtr), device=cihaz)
        for i in range(0, len(sira), a.batch):
            s = sira[i : i + a.batch]
            logit = sn(Xtr[s], Mtr[s])
            kayip = F.cross_entropy(logit, ytr.to(cihaz)[s])
            opt.zero_grad(set_to_none=True)
            kayip.backward()
            opt.step()
        dv_acc, dv_f1 = dogruluk(sn, Xva, Mva, yva)
        gecmis.append(round(dv_acc, 4))
        if dv_acc > en_iyi[0]:
            en_iyi = (
                dv_acc,
                {
                    k: v.detach().clone()
                    for k, v in sn.state_dict().items()
                },
                ep + 1,
            )
    sn.load_state_dict(en_iyi[1])
    te_acc, te_f1 = dogruluk(sn, Xte, Mte, yte)
    lm_son = (
        dil_ppl(sn.gpt, lm_blok)
        if a.mod != "sifirdan"
        else float("nan")
    )
    # Adaptör kapalıyken LM ppl (LoRA ise): taban W'nin değişmediğini
    # gösterir
    lm_kapali = float("nan")
    if a.mod == "lora":
        adaptor_durumu(sn.gpt, False)
        lm_kapali = dil_ppl(sn.gpt, lm_blok)
        adaptor_durumu(sn.gpt, True)
    sonuc = {
        "mod": a.mod,
```

`g06_ince_ayar.py`, 217–242. satırlar:

```python
        "r": a.r if a.mod == "lora" else 0,
        "lr": a.lr,
        "seed": a.seed,
        "egitilebilir": egitilebilir,
        "toplam": toplam,
        "dogrulama_acc_gecmis": gecmis,
        "en_iyi_epoch": en_iyi[2],
        "dogrulama_acc": round(en_iyi[0], 4),
        "test_acc": round(te_acc, 4),
        "test_f1": round(te_f1, 4),
        "lm_ppl_once": round(lm_taban, 3),
        "lm_ppl_sonra": round(lm_son, 3),
        "lm_ppl_adaptor_kapali": round(lm_kapali, 3),
        "sure_sn": round(time.time() - t0, 1),
    }
    with open(
        os.path.join(K, "sonuc_ince_ayar.jsonl"),
        "a",
        encoding="utf-8",
    ) as f:
        f.write(json.dumps(sonuc, ensure_ascii=False) + "\n")
    print(json.dumps(sonuc, ensure_ascii=False))


if __name__ == "__main__":
    main()
```


Sonuçlar, üç tohumun ortalaması ve örneklem standart sapması ile aşağıdadır.

Çıktı (`cikti_g14.txt`):

```term
ince ayar CSV yazildi
d=64,L=2 ('245824', '93.37', '96.58')
d=128,L=4 (ana) ('1084800', '60.77', '62.83')
d=192,L=6 ('3106752', '50.94', '52.21')
veri %12.5 ('1084800', '161.28', '165.82')
veri %25 ('1084800', '115.63', '118.12')
veri %50 ('1084800', '73.41', '75.47')
```


Tabloyu üç bölümde okumak gerekir. İlki doğruluk: test doğruluğu, tam ince ayarda 0,294 ± 0,017, LoRA'nın en yüksek rankında (r = 16) 0,293 ± 0,016, sıfırdan eğitimde 0,258 ± 0,011 ve doğrusal sonda 0,236 ± 0,011'dir. TF-IDF ile lojistik regresyonun tek koşudaki doğruluğu ise 0,299'dur. Yani bu görevde basit bir kelime tabanlı baseline, ön-eğitimli bir transformer'ın tam ince ayarıyla yarışır. Bu, görevin zorluğu ve küçük ölçekli ön-eğitimin sınırı hakkında bir ders verir: ön-eğitim gerçekten bilgi aktarır (sıfırdan eğitimden belirgin şekilde iyi), ama bu aktarımın üstüne ne kadar güçlü bir sınıflandırıcı kurulacağı, modelin büyüklüğü ve ön-eğitimin kalitesi kadar veriye de bağlıdır.

İkincisi, rank: LoRA'da doğruluk r = 1'den r = 16'ya 0,257'den 0,293'e çıkar; ama r = 1 ile r = 2 arasındaki fark, tohum sapmalarının içinde kalır. Eğitilebilir parametre sayısı ise 5 007'den 51 087'ye (tam modelin yüzde 4,7'si) çıkar. Yani küçük bir rank, bu görevde neredeyse aynı doğruluğu verir: r = 1, tam modelin eğitilebilir parametrelerinin yaklaşık 217'de biridir.

![Şekil 70.9: LoRA rank'ına göre test doğruluğu (3 tohum) ve eğitilebilir parametre sayısı](gorseller/b70_lora_rank.png)

Üçüncüsü ve en önemlisi, felaket unutma. Tam ince ayardan sonra ön-eğitim perplexity'si 59,3'ten ortalama 335,6'ya çıkar: model yeni görevde iyileşirken eski dil bilgisini büyük ölçüde kaybeder. LoRA'da ise adaptör açıkken perplexity 92 ile 131 arasında artar; rank büyüdükçe artış da büyür. Adaptör kapalıyken aynı model için perplexity her rank'ta tam olarak 59,278'dir: yani taban ağırlıklar değişmemiştir ve dil modelleme davranışındaki tüm kayıp adaptörden gelmektedir. Doğrusal sonda ise gövdeyi hiç değiştirmediği için perplexity'yi 59,28'de sabit tutar.

![Şekil 70.10: İnce ayar yöntemlerinden sonra ön-eğitim perplexity'si (felaket unutma)](gorseller/b70_unutma.png)

Bu sonuç, öğrenme oranı seçiminin de bir ders olduğunu gösterir. Doğrulama doğruluğuna göre seçilen 10⁻⁴ oranı, tam ince ayarda en iyi doğrulama doğruluğunu verdi; ama aynı oran en çok unutmaya neden oldu. Seçim ölçütüne yalnızca görevin doğruluğu konursa, modelin geri kalan yeteneği görünmez kalır. Gerçek sistemlerde doğruluğun yanında unutma, güvenlik ve genel yetenek ölçütleri birlikte izlenir.

Felaket unutma, sürekli öğrenme sorunudur: model yeni bir görevi öğrendikçe eski görevleri unutur. Bu bölümdeki ölçüm, bunun en basit ölçülebilir hâlidir. LoRA, taban ağırlıkları değiştirmediği için unutmayı azaltır; ama adaptör katkısı açıkken unutma tamamen ortadan kalkmaz (perplexity 59'dan 92–131'e). Bu nedenle LoRA da bir ödünleşimdir: daha az parametre ve daha az unutma, ama sıfır unutma değil.

### Diğer PEFT yöntemleri ve talimat ince ayarı

LoRA, **parametre açısından verimli ince ayar** (PEFT) ailesinin en yaygın üyesidir, ama tek değildir (genel bilgi). **Adaptör katmanları** (Houlsby ve arkadaşları 2019), her bloğun içine küçük bir darboğaz (düşür-doğrusal olmayan-yükselt) katmanı ekler; çıkarımda ek gecikme getirir, çünkü birleştirilemez. **Önek (prefix) ve prompt tuning**, girdinin başına eğitilebilir sanal belirteçler ekler; model ağırlıkları değişmez, yalnızca bu sanal belirteçlerin gömmeleri öğrenilir. Bu yöntemler uzun bağlam kullanımını azaltır, ama görev başına sanal belirteç sayısına duyarlıdır.

**Talimat ince ayarı** (instruction tuning), modeli "soru → cevap" gibi talimat-yanıt çiftleriyle eğitir; böylece model, serbest metin tamamlamak yerine bir isteği yerine getirmeyi öğrenir. **RLHF** (insan geri bildirimli pekiştirmeli öğrenme) bunun üzerine, insanların tercih ettiği yanıtları ödüllendiren bir ödül modeli ve pekiştirmeli öğrenme ekler; **DPO** ise aynı tercih verisini ödül modeli olmadan doğrudan bir kayıp fonksiyonuna çevirir (genel bilgi). Bu konuların ayrıntısını Bölüm 71 (LLM sistemleri) ve Bölüm 74 (pekiştirmeli öğrenme) işleyecek. Burada önemli olan şudur: bu yöntemler de aynı tuzağa düşer. Tercih verisi küçük ve dar ise model, o verinin tonunu öğrenir ve genel yeteneğini kaybedebilir.

## 70.10 Değerlendirme ve dürüstlük

Dil modellerinin değerlendirilmesi, bu bölümde kurduğumuz ölçülerin en tehlikeli kısmıdır. Üç tuzağa dikkat etmek gerekir.

**Perplexity'nin sınırı.** Perplexity, bir belirtecin doğru tahmin edilip edilmediğini değil, dağılımın ne kadar keskin olduğunu ve gerçek belirteçe ne kadar olasılık verildiğini ölçer. İki modelin perplexity'si yalnızca aynı belirteç sözlüğü, aynı test metni ve aynı bağlam uzunluğu ile karşılaştırılabilir. Bu bölümde her karşılaştırma bu koşulu sağlar; yine de üretim kalitesini perplexity'den tahmin etmek yanıltıcıdır. Düşük perplexity, akıcı bir metin garantisi değildir.

**Test kümesi kirlenmesi.** Test metni eğitimde görüldüyse ölçülen sayı yapaydır. Bu bölümde test bölümleri eğitimden tamamen ayrıdır ve tokenizer yalnızca eğitim bölümlerinden öğrenilmiştir (70.4'teki ölçüm). Ancak kitabın kendi tekrarları, bölümler arasında aynı kalıpları taşır: doğrulama metninin yüzde 2,70'inin 8 belirteçlik dizileri eğitimde zaten geçer. Bu, ezberleme değil, konu ve dilin doğal tekrarıdır; ama bir değerlendirme kümesi seçerken bu tür örtüşmeyi ölçmek gerekir. Gerçek dünyada, büyük ölçekli web derlemleriyle eğitilen modellerde test kümesi kirlenmesi, benzer bir ölçümle (n-gram örtüşmesi) denetlenir.

**Ezberleme.** Yukarıda gördüğümüz gibi üretilen metnin eğitim dizilerini kopyalama oranı düşüktür; ama bu, ezberlemenin hiç olmadığı anlamına gelmez. Az veriyle uzun eğitimde (70.7'deki yüzde 12,5 veri koşusu) doğrulama kaybının yükselmesi, ezberlemenin ilk işaretidir. Büyük ölçekte ezberleme, özel bilgilerin (kişisel veri, gizli belgeler) modelden çıkması riskini doğurur; bu, savunma sanayiinde sınıflandırılmış bilgilerle eğitilen bir modelin neden izole edilmesi gerektiğinin nedenlerinden biridir.

**Önyargı ve güvenlik.** Model, eğitim derleminin dilini, konu dağılımını ve yazarın kalıplarını öğrenir. Bu derlem yalnızca tek bir kitaptır; bu yüzden modelin "Kısım XIV en sık tahmin edilen kısımdır" gibi bir yanlılığı vardır (sınıf dağılımı tablosu). Gerçek bir sistemde önyargı, veri seçiminde ve değerlendirme alt kümelerinin temsiliyetinde ölçülür. Güvenlik tarafında, bir dil modelinin zararlı içerik üretmemesi için ayrıca eğitim ve filtreleme gerekir; bunun ayrıntısı Bölüm 78 (güvenilir ve güvenli yapay zekâ) kapsamındadır.

## 70.11 Verimlilik: çıkarım, bellek ve kuantizasyon

Bir dil modelinin pratik değeri, ne kadar hızlı ve ne kadar küçük çalıştığına da bağlıdır. Bu bölümde ölçtüğümüz üretim hızı (3,8 ms/belirteç, KV önbelleği olmadan) iki darboğazı gösterir. Birincisi dikkat: KV önbelleği yoksa her adımda tüm bağlam yeniden işlenir ve maliyet, dizi boyunca karesel büyür. Bölüm 69'daki KV önbelleği, geçmiş anahtar ve değer vektörlerini saklayarak adım başına yalnızca yeni belirteçle ilgili işi yapar. İkincisi bellek: ağırlıklar, 16 bitlik sayılarla bile büyük modellerde gigabaytlara ulaşır. **Kuantizasyon**, ağırlıkları 8 bit ya da daha az bit ile temsil ederek belleği ve bellek bant genişliği ihtiyacını azaltır; bu konu Bölüm 71 ve Bölüm 75'te ayrıntılı işlenecek.

Eğitimin kendisi de verimlilik sorunudur. Bu bölümdeki ölçümler, tek bir RTX 3060 Laptop (6 GB) üzerinde yapıldı; model ve batch bu bellek sınırına göre seçildi. Eğitim koşularının sürelerini, kartın paylaşılması nedeniyle olduğundan biraz uzun ölçtük; bu yüzden süreleri birbiriyle karşılaştırırken koşulları aynı tutmak gerekir. LoRA'nın en somut faydası da burada görünür: eğitilebilir parametre sayısı ve bu parametrelerin optimizer durumu (AdamW'de iki moment) küçüldüğü için bellek ihtiyacı da küçülür.

## Çözümlü Örnekler

Aşağıdaki dört örnekte Bölüm 5'teki altı adımı izleyeceğiz. Her örnekte elle hesaplanabilen bir ölçek kullanılır; sayıları kodla da doğrularız.

### Örnek 1 (★): Üç BPE adımını elle izlemek

**Adım 1 — Anla.** Derlem `kod kodu koda kod`. Soru: BPE üç birleştirmeden sonra hangi simgeleri öğrenir ve her adımda hangi çift seçilir?

**Adım 2 — Örnekle.** Önce derlemi ön işlemeden geçirelim. Parçalar: `kod`, ` kodu`, ` koda`, ` kod`. İlk parçanın başında boşluk yok, diğer üçünün var. Frekanslar 1, 1, 1, 1; `kod` ve ` kod` ayrı parçalardır.

**Adım 3 — Kaba çöz.** Her parçayı karakterlere ayır: `k o d`, ` k o d u`, ` k o d a`, ` k o d`. Tüm bitişik çiftleri say ve en sıkını birleştir. Sonra yeni dizilerle tekrarla.

**Adım 4 — Örüntü.** Her adımda sayımı yap, en sık çifti seç, parçalarda birleştir. Eşitlikte sözlük sırasını kullan.

**Adım 5 — İyileştir.** Tekrar eden taramayı önlemek için yalnızca çiftin geçtiği parçaları güncelleyeceğiz; bu, `egit` içindeki `konum` tablosunun amacıdır. Küçük örnekte bu bir kazanç değildir ama aynı mantık büyük derlemde gereklidir.

**Adım 6 — Doğrula.** Aşağıdaki iz tablosu, koddan çıkan sonuçla aynıdır.

| Adım | En sık çift | Sayı | Birleşim | Parçalar (örnek) |
|---|---|---|---|---|
| 0 | `(k,o)` ve `(o,d)` | 4, 4 | — | `k o d`, ` k o d u` |
| 1 | `(o,d)` (eşitlikte sözlük sırası) | 4 | `od` | `k od`, ` k od u` |
| 2 | `(k,od)` | 4 | `kod` | `kod`, ` kod u` |
| 3 | `( ,kod)` | 3 | ` kod` | `kod`, ` kod u` |

Üç adımda öğrenilen kurallar `(o,d)`, `(k,od)` ve ` (kod)` sırasıyla ve `kod` bu derlemin tek simgesidir. **Bunu AI'sız yazabilir misin?** Derlemi `ara ara arada` olarak değiştir ve üç adımı elle izle. Sonra birleşimlerin hangi sırayla oluştuğunu iki cümleyle açıkla.

### Örnek 2 (★★): Bigram, Laplace ve perplexity'yi elle hesaplamak

**Adım 1 — Anla.** Derlem `a b a c`, sözlük `V = 3` (a, b, c). Soru: Laplace (k = 1) düzeltmeli bigram modelinde `a b a c` cümlesinin perplexity'si nedir?

**Adım 2 — Örnekle.** Bigramlar: `(a,b)`, `(b,a)`, `(a,c)`. Bağlam sayıları: `C(a) = 2`, `C(b) = 1`.

**Adım 3 — Kaba çöz.** Olasılıklar `P(w|h) = (C(h,w) + 1) / (C(h) + 3)`. `P(b|a) = (1+1)/(2+3) = 0,4`, `P(a|b) = (1+1)/(1+3) = 0,5`, `P(c|a) = (1+1)/(2+3) = 0,4`.

**Adım 4 — Örüntü.** Cümlenin olasılığı üç adımın çarpımıdır: `0,4 · 0,5 · 0,4 = 0,08`. Ortalama çapraz entropi `H = −(log₂0,4 + log₂0,5 + log₂0,4)/3 = 1,2146` bit.

**Adım 5 — İyileştir.** Perplexity `2^H` ile hesaplanır; `2^1,2146 = 2,3208`. Eşdeğer biçimde `0,08^{−1/3} = 2,3208`tir; bu da perplexity'nin çarpımın geometrik ortalamasının tersi olduğunu gösterir.

**Adım 6 — Doğrula.** Aşağıdaki tabloyu kodun çıktısıyla karşılaştır.

| Adım | Bağlam → sonraki | Sayım | Olasılık |
|---|---|---|---|
| 1 | a → b | 1 | 0,4 |
| 2 | b → a | 1 | 0,5 |
| 3 | a → c | 1 | 0,4 |
| Toplam | | | 0,08 |

Kod (`g16_ornek_hesap.py`) aynı değerleri verir: `P(b|a) = 0,4`, `P(a|b) = 0,5`, `H = 1,2146`, `PP = 2,3208`. **Bunu AI'sız yazabilir misin?** Derlemi `a b a b` olarak değiştir, sözlük boyutunu `V = 2` al ve perplexity'yi elle hesapla. Laplace yerine `k = 0,1` kullanırsan sonucun nasıl değiştiğini açıkla.

### Örnek 3 (★★): Sıcaklık, top-k ve top-p dağılımlarını elle hesaplamak

**Adım 1 — Anla.** Logitler `[2,0; 1,0; 0,5; −1,0; 0,0]`. Soru: `T = 1`, `T = 0,5`, `T = 2`, top-k (k = 2) ve top-p (p = 0,9) için olasılık dağılımları nedir?

**Adım 2 — Örnekle.** Önce `T = 1` için `exp` değerlerini al: `e²=7,389`, `e¹=2,718`, `e⁰·⁵=1,649`, `e⁻¹=0,368`, `e⁰=1`. Toplam `13,124`.

**Adım 3 — Kaba çöz.** Olasılıklar `0,563; 0,207; 0,126; 0,028; 0,076`. Sıcaklık için logitleri `T`'ye böl ve aynı işlemi yap. Top-k için yalnızca en büyük iki logiti tut, diğerlerini `−∞` yap. Top-p için olasılıkları büyükten küçüğe sırala ve birikimli toplam `0,9`u geçene kadar belirteç tut.

**Adım 4 — Örüntü.** Sıcaklık düşükse dağılım tek bir belirtece yığılır; yüksekse düzleşir. Top-k sabit sayıda belirteç bırakır; top-p, dağılımın şekline göre bırakılan belirteç sayısını değiştirir.

**Adım 5 — İyileştir.** `T = 0,5` için logitler 2 ile çarpılır: `[4; 2; 1; −2; 0]`. Paydanın toplamı `54,60 + 7,389 + 2,718 + 0,135 + 1 = 65,84`tür; en olası belirtecin olasılığı `54,60 / 65,84 = 0,829` olur. Düşük sıcaklık, dağılımı tek belirtece yığar.

**Adım 6 — Doğrula.** Kod sonuçlarını tabloyla karşılaştır.

| Yöntem | p(1) | p(2) | p(3) | p(4) | p(5) |
|---|---|---|---|---|---|
| T = 1 | 0,563 | 0,207 | 0,126 | 0,028 | 0,076 |
| T = 0,5 | 0,829 | 0,112 | 0,041 | 0,002 | 0,015 |
| T = 2 | 0,375 | 0,227 | 0,177 | 0,084 | 0,138 |
| top-k (k = 2) | 0,731 | 0,269 | 0 | 0 | 0 |
| top-p (p = 0,9) | 0,579 | 0,213 | 0,129 | 0 | 0,078 |

Top-p satırında çekirdek şöyle kurulur: olasılıklar büyükten küçüğe `0,563; 0,207; 0,126; 0,076; 0,028`. İlk üçü birlikte `0,896` eder; bu 0,9'un altında olduğu için dördüncü belirteç (logit 0, olasılık 0,076) eklenir ve birikim `0,972` olur. Beşinci belirtecin (logit −1, olasılık 0,028) önündeki birikim 0,972 > 0,9 olduğu için o dışarıda kalır. Bu yüzden tablodaki top-p satırında dördüncü sütun 0, beşinci sütun 0,078 çıkar. **Bunu AI'sız yazabilir misin?** Logitleri `[1,0; 1,0; 1,0]` yap ve `T = 0,1`, `T = 10` için dağılımları hesapla; neden biri tek belirteç, diğeri düzgün dağılım çıkar?

### Örnek 4 (★★★): LoRA'nın d = 4, r = 1 örneğinde eğitilebilir parametreler ve birleştirme

**Adım 1 — Anla.** `W = diag(1, 2, 1, 0,5)` (4 × 4). LoRA rankı `r = 1`, ölçek `α = 2` (yani `α/r = 2`). Soru: adaptörlü çıktıyı, eğitilebilir parametre sayısını ve birleştirilmiş matrisin eşdeğerliğini elle bul.

**Adım 2 — Örnekle.** `x = [1, 2, 0, −1]`, `A = [0,5, 0, 1, 0]` (1 × 4), `B = [2; 0; 0; 1]` (4 × 1).

**Adım 3 — Kaba çöz.** `W x = [1; 4; 0; −0,5]`. `A x = 0,5`. `B (A x) = [1; 0; 0; 0,5]`. Adaptör katkısı `2 · [1; 0; 0; 0,5] = [2; 0; 0; 1]`.

**Adım 4 — Örüntü.** `y = W x + (α/r) B (A x) = [3; 4; 0; 0,5]`. Eğitilebilir parametre: `A` 4 sayı, `B` 4 sayı; toplam 8. Tam matris `W` 16 sayıdır. Birleştirilmiş matris `W' = W + 2 · B A`:

| | sütun 1 | sütun 2 | sütun 3 | sütun 4 |
|---|---|---|---|---|
| satır 1 | 3 | 0 | 4 | 0 |
| satır 2 | 0 | 2 | 0 | 0 |
| satır 3 | 0 | 0 | 1 | 0 |
| satır 4 | 1 | 0 | 2 | 0,5 |

**Adım 5 — İyileştir.** Birleştirilmiş matrisle kontrol et: `W' x` satır satır `3·1 + 0·2 + 4·0 + 0·(−1) = 3`, `2·2 = 4`, `1·0 = 0` ve `1·1 + 0·2 + 2·0 + 0,5·(−1) = 0,5` verir; sonuç `[3; 4; 0; 0,5]`, yani adaptörlü çıktıyla aynıdır. Bu, birleştirmenin çıkarımda sıfır ek gecikme getirdiğini gösterir.

**Adım 6 — Doğrula.** Kod (`g12_lora_ornek.py`) aynı sayıları verir: `y = [3; 4; 0; 0,5]`, eğitilebilir `8`, merge farkı `0`; rastgele girdilerde fark `1,8·10⁻¹⁵`. **Bunu AI'sız yazabilir misin?** `r = 2` için `A`'yı `2 × 4`, `B`'yi `4 × 2` yap; eğitilebilir sayıyı, `α/r` ölçeğini ve birleştirilmiş matrisin hesabını elle göster. `α = 16` sabit tutulursa `r` arttığında ölçek nasıl değişir?

## Kendin Yap Projeleri

::: dikkat
Aşağıdaki projelerde yapay zekâ aracı kullanmadan çalış. Tokenizer, n-gram ve dil modeli eğitim döngüsünü kendi elinle kur. Bir ölçüm şüpheli görünürse, önce kendi kodunu ve veri bölmesini denetle; sonra sonuca bak. Bölüm metnindeki betikleri başlangıç noktası olarak kullanmak serbesttir, ama ölçümleri kendin yeniden üret.
:::

### Proje 1 (★★): Türkçe için sıfırdan BPE tokenizer ve dil modeli karşılaştırması

**Amaç.** Bu bölümdeki BPE'yi kendi derlemin üzerinde eğit, tokenizer'ı ölç ve aynı belirteçler üzerinde n-gram ile küçük bir sinir modelini karşılaştır.

**Yapılacak / Beklenen davranış.** (1) Kendi Türkçe derlemini (en az 500 KB, bölüm düzeyinde eğitim/doğrulama/test ayrımıyla) hazırla. (2) BPE'yi birleştirme sayısına göre eğit; her birleştirme sayısı için sözlük boyutunu, test metninde kar/token ve unk oranını raporla. (3) Gidiş-dönüş testini alfabedeki karakterlerden oluşan metinlerde doğrula. (4) Aynı belirteç dizisi üzerinde unigram, bigram ve trigram (Laplace'ın `k` değerini doğrulamada seç) ile perplexity hesapla. (5) Küçük bir dönüştürücü modeli aynı belirteçlerle eğit; test perplexity'sini n-gram ile karşılaştır.

**Önerilen yaklaşım (ipucu, tam çözüm değildir).** BPE öğrenmede çift sayımlarını bir sözlükte tut ve her birleştirmede yalnızca etkilenen kelimeleri güncelle. Gidiş-dönüş için ön işlemenin boşlukları kaybetmediğinden emin ol. N-gram için `log` yerine olasılık çarpımı yerine log-toplam kullan; sayısal taşmayı önle.

**Başarı kriterleri.** (a) `decode(encode(x)) == x` tüm alfabe-içi testlerde doğru. (b) Birleştirme sayısı arttıkça sözlük boyutu ve kar/token tablosu üretilmiş. (c) n-gram ve sinir modeli, aynı tokenizer ve aynı test kümesiyle karşılaştırılmış; test kümesi hiçbir seçimde kullanılmamış. (d) Sonuçlar tek bir tohumla değil, en az üç tohumla ve ortalama ± sapma olarak verilmiş. (e) Kullanılan derlemin bölüm listesi ve boyutu raporda yazılı.

### Proje 2 (★★★): Mini-GPT ile LoRA tabanlı kısım sınıflandırıcı

**Amaç.** Bu bölümdeki deneyi, kendi kurduğun bir modelle tekrarla: önce küçük bir GPT'yi ön-eğit, sonra bir sınıflandırma görevi için sıfırdan, tam ince ayar, doğrusal sonda ve LoRA ile karşılaştır. Felaket unutmayı da ölç.

**Yapılacak / Beklenen davranış.** (1) Ön-eğitim: en az iki farklı boyutta mini-GPT'yi eğit, doğrulama perplexity'sini ölç. (2) Görev: paragraflardan etiket (ör. belge bölümü, konu) tahmini; eğitim, doğrulama ve test ayrımı bölüm düzeyinde. (3) Dört yöntem: sıfırdan, tam ince ayar, doğrusal sonda, LoRA (en az üç farklı rank). (4) Her yöntem için eğitilebilir parametre sayısı, test doğruluğu ve makro-F1; LoRA için adaptör açık/kapalı perplexity. (5) TF-IDF + lojistik regresyon baseline'ı.

**Önerilen yaklaşım (ipucu, tam çözüm değildir).** Sınıflandırma başlığını, dizinin maskeli ortalaması üzerine kur; dolgu belirteçlerini hesaba katma. LoRA'da yalnızca `A` ve `B` ile başlığı eğit; taban parametrelerin `requires_grad` değerini açıkça kapat. Öğrenme oranlarını doğrulama kümesinde seç ve test kümesini yalnızca son ölçümde kullan.

**Başarı kriterleri.** (a) Her yöntem için üç tohum ile ortalama ± sapma. (b) Adaptör kapalıyken LoRA modelinin perplexity'si ön-eğitim değerine eşit (fark 10⁻⁶'dan küçük). (c) Birleştirilmiş LoRA matrisinin çıktısı, adaptörlü çıktıyla 10⁻⁶ içinde aynı. (d) Felaket unutma tablosu: her yöntem için ön-eğitim perplexity'sinin ön-eğitim değerinden oranı. (e) Ölçümler hangi koşulda (GPU paylaşımı, süre, tohum) yapıldı, raporda yazılı.

### Ek Alıştırmalar

1. ★ Sözcük torbasında "kedi kovaladı köpeği" ile "köpek kovaladı kediyi" cümlelerinin vektörleri aynı mı? Neden?
2. ★ Bir TF-IDF vektörünün L2 normu 1 ise, iki vektörün kosinüs benzerliği ile iç çarpımı arasındaki ilişki nedir?
3. ★ Bir bigram modelde `C(h) = 0` olan bir bağlam için Laplace (k = 1) tahmini neye eşittir? Sözlük boyutu `V = 2149` ise bu değer kaçtır?
4. ★★ Mülakat: Perplexity ile çapraz entropi arasındaki ilişki nedir? Perplexity 50 olan bir model, bit cinsinden kaç çapraz entropiye karşılık gelir?
5. ★★ Mülakat: BPE neden kelime düzeyi tokenizasyondan daha iyi genelleme yapar? Hangi durumda kötüleşir?
6. ★★ BPE'de birleştirme sayısı 0 iken sözlük boyutu ile alfabe boyutu arasındaki fark nedir? Unk belirteci hangi durumda kullanılır?
7. ★★ Bir tokenizer'ın İngilizce ağırlıklı eğitildiğini ve Türkçe metin için `token/sözcük` değerinin yüksek çıktığını düşün. Bu değeri düşürmek için hangi iki değişiklik işe yarar ve neden?
8. ★★ Mülakat: LoRA'da `B`'yi sıfırla, `A`'yı Gauss ile başlatmanın nedeni nedir? İkisini de sıfırla başlatırsak ne olur?
9. ★★ Mülakat: Adaptör açıkken perplexity arttı, kapalıyken aynı kaldı. Bu sonuç, taban ağırlıkların değişmediği anlamına mı gelir? Hangi ölçümle doğrularsın?
10. ★★★ Top-p örneklemesinde dağılım çok keskinse (ilk belirteç 0,99) ne olur? Çok düzse (tüm belirteçler eşit) ne olur? Her iki durumda kaç belirteç seçilir?
11. ★★★ Mülakat: Bir sinir dil modelinin doğrulama perplexity'si eğitim boyunca düşmeye devam ederken test perplexity'si yükselmeye başladı. Üç olası neden ve her biri için bir ölçüm öner.
12. ★★★ Mülakat: Tam ince ayar ile LoRA aynı doğruluğu veriyor, ama LoRA'da unutma daha az. Bu iki sonuç bir arada nasıl açıklanır, ve hangi koşulda LoRA'nın doğruluğu da düşer?

## Kod Okuma Egzersizi

Bu bölümde BPE'yi sıfırdan yazdık. Şimdi gerçek bir kütüphanedeki eşdeğer koda bakalım. Kaynak: Hugging Face `transformers` kütüphanesi, sürüm 4.57.6, `transformers/models/gpt2/tokenization_gpt2.py` dosyası (yerel kurulum: `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\transformers\models\gpt2\`). Önce baytların simgelere eşlenmesini gösteren `bytes_to_unicode` fonksiyonu:

`tokenization_gpt2.py` dosyasının 36–58. satırları (Python 3.12 ile transformers 4.57.6 kaynağı):

```python
@lru_cache
def bytes_to_unicode():
    """
    Returns list of utf-8 byte and a mapping to unicode strings. We
    specifically avoids mapping to whitespace/control
    characters the bpe code barfs on.

    The reversible bpe codes work on unicode strings. This means you
    need a large # of unicode characters in your vocab
    if you want to avoid UNKs. When you're at something like a 10B
    token dataset you end up needing around 5K for
    decent coverage. This is a significant percentage of your normal,
    say, 32K bpe vocab. To avoid that, we want lookup
    tables between utf-8 bytes and unicode strings.
    """
    bs = (
        list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"),
        ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    )
    cs = bs[:]
    n = 0
    for b in range(2**8):
        if b not in bs:
            bs.append(b)
            cs.append(2**8 + n)
            n += 1
    cs = [chr(n) for n in cs]
    return dict(zip(bs, cs))
```


Bu fonksiyon, bir byte-to-unicode tablosu üretir. Ayrı tutulan ASCII aralıkları (`!`–`~`, `¡`–`¬`, `®`–`ÿ`) doğrudan kendi karakterleriyle eşlenir; geri kalan baytlar 256 ve sonrasındaki kod noktalarına atanır. Bu yüzden 70.4'teki çıktıda boşluk baytı (32) `Ġ` simgesine düşer. Kaynak fonksiyon, kendi yorumunda bu tasarımın gerekçesini de yazar.

Şimdi `bpe` yöntemi. Bu yöntem, bir "kelimeyi" (ön işlemeden geçmiş parça) öğrenilmiş birleştirmelere göre parçalar; sınıfın `bpe_ranks` sözlüğü, bizim `sira` sözlüğümüzle aynı rolü oynar:

`tokenization_gpt2.py` dosyasının 187–227. satırları (Python 3.12 ile transformers 4.57.6 kaynağı):

```python
    def bpe(self, token):
        if token in self.cache:
            return self.cache[token]
        word = tuple(token)
        pairs = get_pairs(word)

        if not pairs:
            return token

        while True:
            bigram = min(pairs, key=lambda pair:
            self.bpe_ranks.get(pair, float("inf")))
            if bigram not in self.bpe_ranks:
                break
            first, second = bigram
            new_word = []
            i = 0
            while i < len(word):
                try:
                    j = word.index(first, i)
                except ValueError:
                    new_word.extend(word[i:])
                    break
                else:
                    new_word.extend(word[i:j])
                    i = j

                if word[i] == first and i < len(word) - 1 and word[i +
                1] == second:
                    new_word.append(first + second)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            new_word = tuple(new_word)
            word = new_word
            if len(word) == 1:
                break
            else:
                pairs = get_pairs(word)
        word = " ".join(word)
        self.cache[token] = word
        return word
```


**Sorular — cevaplamadan geçme:**

1. `bpe` içinde `min(pairs, key=lambda pair: self.bpe_ranks.get(pair, inf))` satırı, bizim `_parcala` fonksiyonumuzdaki `min(aday)` ile hangi açıdan aynıdır? Hangi çiftin seçildiğini belirleyen tek şey nedir?
2. `while True` döngüsünde `if bigram not in self.bpe_ranks: break` koşulu neden gereklidir? Hangi durumda döngü kendiliğinden biter?
3. İç döngüdeki `word.index(first, i)` çağrısı, bizim BPE'mizdeki hangi döngünün yerini tutar ve neden iki belirteç birden birleştirilir (`i += 2`)?
4. `self.cache` sözlüğü neden gereklidir? Bu önbelleği bizim `onbellek` sözlüğümüzle karşılaştır; hangisi bir kelimenin sonucunu saklar, hangisi bir çiftin sonucunu?
5. Kaynak kod, birleştirme sonucunu `" ".join(word)` ile bir dizge olarak saklar ve döndürür. Bu tasarım, bizim `_parcala` fonksiyonunun liste döndürmesine göre hangi avantaja ve hangi dezavantaja sahiptir?
6. `bytes_to_unicode` tablosu neden 256 ayrı simge üretir ve bu tablo olmadan GPT-2'nin Türkçe karakterleri ne olurdu? Bu sorunun ters yönünü (bayt-simge tablosunun geri çevrilmesi) nasıl yapardın?

## Bölüm Özeti

- Metni sayıya çevirmek için kelime torbası ve TF-IDF kullanılır; TF-IDF'in idf terimi, yaygın kelimelerin ağırlığını düşürür. Sıfırdan yazılan TF-IDF, sklearn ile `10⁻¹⁶` mertebesinde eşleşir.
- n-gram dil modeli, bağlamı sayarak olasılık tahmin eder; Laplace düzeltmesi sıfır olasılığı önler. Seyreklik nedeniyle üçlü modelin doğrulama perplexity'si ikiliden kötü çıkabilir.
- Perplexity `2^H` ile hesaplanır ve yalnızca aynı belirteç sözlüğü üzerinde karşılaştırılabilir.
- Tokenizasyonun üç düzeyi (karakter, sözcük, alt-sözcük) sözlük, dizi uzunluğu ve OOV arasında takas yapar. Türkçenin eklemeli yapısı sözcük düzeyini zorlar.
- BPE, en sık çifti tekrar tekrar birleştirerek kuralları öğrenir; kodlama öğrenilen sırayla uygulanır; çözme simgeleri birleştirir. Bayt düzeyi BPE, unk sorununu ortadan kaldırır ama Türkçe harflere iki bayt maliyeti getirir.
- Gömme bir arama tablosudur; one-hot × matris çarpımının satır seçimi ile eşdeğerdir. word2vec (skip-gram + negatif örnekleme) bu tabloyu bağlam tahmin görevinde öğrenir; küçük bir derlemde komşular kısmen anlamlıdır.
- Küçük bir GPT (1,08 milyon parametre), tek GPU'da üç tohumla test perplexity'si 62,5'e ulaşır; bu, bigram'ın yarısıdır. Ölçekleme eğrileri model boyutu ve veri miktarıyla düzgün azalır.
- Örnekleme yöntemleri (sıcaklık, top-k, top-p) dağılımı farklı biçimlerde keser; açgözlü üretim tekrara, yüksek çeşitlilik tutarsızlığa yol açar.
- İnce ayar yöntemleri arasında doğruluk ve unutma ödünleşir. Tam ince ayar en çok unutmaya neden olur; LoRA adaptörü kapatıldığında taban perplexity'yi tam olarak korur.

**Sonraki bölümde:** Bölüm 71'de (LLM sistemleri) bu parçaları bir araya getirip büyük dil modellerinin üretim sistemlerine nasıl bağlandığını göreceğiz: istem tasarımı, geri getirme destekli üretim (RAG), değerlendirme, araç kullanan ajanlar ve servis etme. KV önbelleği ve kuantizasyon orada ayrıntılı ele alınacak.

::: mulakat
1. BPE nasıl çalışır? Eğitim ve kodlama adımlarını ayrı ayrı anlat; neden kodlama, eğitimdeki sırayı izlemek zorundadır?
2. Perplexity nedir ve çapraz entropiyle ilişkisi nedir? İki modelden hangisinin daha iyi olduğunu nasıl söylersin, hangi koşulda karşılaştırma geçersizdir?
3. Bir Türkçe metin için tokenizer'ın token/sözcük değeri neden İngilizce metne göre daha yüksek çıkabilir? Bunu azaltmak için iki yol öner.
4. Neden gömme katmanı bir matris çarpımı değil, bir arama tablosu olarak uygulanır?
5. LoRA neden az parametreyle çalışır? `B`'nin sıfırla başlatılmasının etkisi nedir, ve birleştirme sonrası çıkarım neden değişmez?
6. Top-k ile top-p arasındaki fark nedir? Dağılım keskinken ve düzken hangisi daha tutarlı seçim yapar?
7. Bir modeli bir görev için ince ayarladıktan sonra genel dil yeteneğini kaybettiğini nasıl ölçersin? Kaybı azaltmak için hangi yöntemleri deneyebilirsin?
8. Bir sinir dil modeli eğitim verisini ezberlediğini nasıl anlarsın? Ezberlemeyi ölçmek için hangi deneyi tasarlarsın ve hangi sonuç bir alarm sayılır?
:::
