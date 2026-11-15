%% kisim_no: XV
%% kisim_ad: Derin Öğrenme
%% bolum_no: 74
%% baslik: Pekiştirmeli Öğrenme

## Giriş: Denemeden öğrenmek

Bölüm 49'da olasılığı, Bölüm 50'de gradyan inişini, Bölüm 54'te ise denetimli öğrenmenin çerçevesini gördük. Denetimli öğrenmede her girdinin yanında doğru cevabı veren bir öğretmen vardır. Model, hatasını bu cevaba bakarak ölçer. Gerçek dünyada çoğu zaman böyle bir öğretmen yoktur. Bir İHA'nın rüzgârda irtifasını tutması için kimse her saniye "doğru gaz değeri budur" diye söylemez. Yalnızca sonuçları görürsün: yükseklik hedefe yakın mı, enerji ne kadar harcandı, düşüp düşmedi. Pekiştirmeli öğrenme (reinforcement learning, RL) tam olarak bu durum için tasarlanmıştır: bir ajan eylem yapar, ortam tepki verir, ajan da bu tepkilerden, yani ödüllerden, zamanla iyi bir davranış öğrenir.

Bu bölüm kitabın Derin Öğrenme kısmının son bölümüdür ve bu yüzden burada iki tarafı birleştiriyoruz. Bir yanda Bölüm 16'daki dinamik programlama, Bölüm 17'deki en kısa yol ve Bölüm 62'deki Markov zincirleri ve Kalman filtresi var: karar ve durum geçişleri üzerine kurulu, sıralı hesaplama. Öbür yanda Bölüm 63–69'daki sinir ağları ve türev alma var: büyük, esnek fonksiyonları gradyanla eğitme. Pekiştirmeli öğrenme bu iki fikri birleştirir. Bölüm 70 ve 71'de gördüğün RLHF ve DPO fikri de buradan doğmuştur; bu bölümün sonunda o köprüyü kuracağız.

Savunma sanayiinde karşılığı açıktır. Bir İHA'nın uçuş kontrolcüsü, irtifa ve konum tutma gibi görevleri yıllardır PID ve benzeri klasik yöntemlerle yapar. Bu yöntemler iyi çalışır ve güvenilirdir. Ama rüzgâr bozucuları, kütle değişimi, hasarlı bir pervane ya da doğrusal olmayan aerodinamik durumlarda ayar kazançlarının sabit kalması yetmeyebilir. Pekiştirmeli öğrenme bu boşluğa bir aday sunar. Ancak bu bölümde göreceğin gibi, RL bir sihirli değnek değildir: simülasyonda öğrendiği bir politika gerçek uçağa taşınırken ciddi bir "simülasyon-gerçek" boşluğu (sim-to-real gap) ile karşılaşır, güvenlik kısıtları ayrıca tasarlanmak zorundadır ve iyi ayarlanmış bir PID çoğu zaman dürüst bir karşılaştırmada hâlâ rakipsizdir. Bu dengeyi kurmak, bu bölümün asıl hedefidir.

::: not
Bu bölümde gerçek bir ortam kütüphanesi (Gymnasium gibi) kullanmıyoruz. Kurulu değildi ve bu bölümün amacı, ortamın kendisini de sıfırdan yazmaktır. Her ortam, `ortam74.py` dosyasında, açıkça tanımlanmış denklemlerle yazılmıştır. CartPole fiziği Barto, Sutton ve Anderson'ın 1983 denklemlerinden alındı; diğer her şey bu bölümde kurduğumuz küçük modellerdir.
:::

Bölüm boyunca her deneyi tekrarlanabilir kılmak için aynı ortamı kullandık: Python 3.12.10, NumPy 2.3.5, PyTorch 2.6.0+cu124. Sinir ağı deneyleri CPU üzerinde, tek iş parçacığıyla çalıştı. GPU bu sırada paylaşımlıydı ve bu bölümdeki küçük ağlar CPU'da yeterince hızlıydı. Her sayısal sonuç en az beş tohumla (0–4) ölçüldü; RL'de tohum varyansının ne kadar büyük olabileceğini Bölüm 74.15'te ayrıntılı göreceksin.

## 74.1 Ajan, ortam ve ödül: problemin çerçevesi

Pekiştirmeli öğrenmenin her türlü varyantı aynı döngüyle başlar. Ajan, t anında bir durum `s_t` gözlemler. Bir politikaya (policy) göre bir eylem `a_t` seçer. Ortam bu eyleme tepki verir: yeni bir durum `s_{t+1}` ve bir ödül `r_{t+1}` üretir. Ajan bu döngüyü defalarca tekrarlar ve amacı, beklenen toplam ödülü en büyütmektir.

Şekil 74.1 bu döngüyü gösteriyor. Dikkat et: ok yönleri bilgi akışını gösteriyor, ama zamanla birlikte bir çevrim oluşur. Her eylem bir sonraki durumu değiştirir ve bu yüzden ajanın verileri, kendi politikasından bağımsız değildir. Bu, denetimli öğrenmeyle en büyük farktır ve sonraki bölümlerde defalarca karşımıza çıkacak.

![Şekil 74.1: Ajan–ortam döngüsü. Ajan politikasına göre eylem seçer; ortam yeni durumu ve ödülü üretir; ajan bu geri bildirimle politikasını günceller.](gorseller/b74_ajan_ortam.png)

Denetimli öğrenmeden dört temel fark vardır. Birincisi, **gecikmeli ödül**: bir eylemin sonucu bazen yüzlerce adım sonra görülür. Bir İHA'nın bugünkü gaz kararı, on saniye sonra bir sapmaya yol açabilir. İkincisi, **veri politikaya bağlıdır**: ajan kötü bir politika izlerse, öğrenmek için gördüğü veri de kötü olur. Üçüncüsü, **keşif zorunluluğu**: ajan hiç denemediği bir eylemin değerini bilemez, bu yüzden bilinmeyeni de denemek zorundadır. Dördüncüsü, **ödül tasarımı**: "ne istediğini" bir sayıyla anlatmak zordur ve yanlış sayı ajanın istenmeyen davranışlar bulmasına yol açar (74.14'te göreceksin).

Ödül hipotezi (reward hypothesis), bu çerçevenin temel varsayımıdır: amaçlanan her hedef, beklenen toplam (indirimli) ödülü en büyütmek olarak ifade edilebilir. Hipotez güçlüdür ama kendiliğinden doğru değildir. Ödül yanlış tanımlanırsa ajan, sana değil ödüle hizmet eder.

::: ipucu
Bölüm 50'deki optimizasyon dilini hatırla: değişkenler (politika parametreleri), amaç fonksiyonu (beklenen getiri) ve kısıtlar (eylem sınırları). RL, bu amaç fonksiyonunu doğrudan bir ortam örneklemesi üzerinden tahmin etmek zorunda olan bir optimizasyon problemidir. Gradyanı ortamın içinden geçerek hesaplamak, RL'nin en zor kısmıdır.
:::

Bu bölümde kullandığımız dört ortam ailesi, bu çerçevenin farklı yüzlerini gösterir: ızgara dünyası (adım adım gezinme), uçurum yürüyüşü (güvenli yol ile kısa yol arasındaki seçim), çok kollu haydut (yalnızca eylem, durum yok) ve CartPole ile İHA irtifa ortamı (sürekli dinamikler). Tüm ortamlar aşağıdaki betikte.

Aşağıdaki betik `ortam74.py`, bu bölümde kullanılan ortamların tamamını içerir. Her sınıf aynı küçük arayüzü paylaşır: `reset()` yeni bir bölüm başlatır, `step(a)` bir eylem alır ve bir sonraki durumu ile ödülü döndürür. Izgara ortamı ayrıca bir geçiş tablosu `P` tutar: `P[(s, a)]` bir listedir ve her öğesi `(olasılık, s', ödül, bitti)` üçlüsüdür. Model bilindiğinde dinamik programlama bu tabloyu doğrudan kullanır; model bilinmediğinde ajan yalnızca `step` ile örnek toplar.

```python
# -*- coding: utf-8 -*-
"""Bolum 74 - Ortamlar (sifirdan). Gymnasium kullanilmaz.

Icerik: GridWorld (kayganlik ve ruzgar), ucurum yuruyusu, Bernoulli
haydut, CartPole (Barto, Sutton, Anderson 1983 denklemleri, Euler),
1B IHA irtifa tutma (ivme, surukleme, ruzgar bozucusu, itki siniri).
"""

import math
import numpy as np

HAREKETLER = [
    (-1, 0),
    (0, 1),
    (1, 0),
    (0, -1),
]  # yukari sag asagi sol


class GridWorld:
    """Durum s = r*W + c. Ruzgar: sutun basina yukari kaydirma.
    Kayganlik: slip olasiligiyla eylem rastgele bir eylemle degisir.
    Her adim odulu -1; hedef mutlak (absorbing), hedefte odul 0."""

    def __init__(
        self, H=4, W=4, start=0, goal=None, slip=0.0, wind=None
    ):
        self.H, self.W, self.S = H, W, H * W
        self.start = start
        self.goal = self.S - 1 if goal is None else goal
        self.slip = slip
        self.wind = [0] * W if wind is None else list(wind)
        self.nA = 4
        self.P = self._kur()
        self.rng = np.random.default_rng(0)
        self.s = self.start

    def _adim(self, s, b):
        r, c = divmod(s, self.W)
        dr, dc = HAREKETLER[b]
        r = min(max(r + dr, 0), self.H - 1)
        c = min(max(c + dc, 0), self.W - 1)
        r = max(r - self.wind[c], 0)  # ruzgar yukari iter
        return r * self.W + c
```

```python
    def _kur(self):
        P = {}
        for s in range(self.S):
            for a in range(self.nA):
                if s == self.goal:
                    P[(s, a)] = [(1.0, s, 0.0, True)]
                    continue
                sonuc = {}
                for b in range(self.nA):
                    p = (1 - self.slip) * (
                        b == a
                    ) + self.slip / self.nA
                    if p == 0:
                        continue
                    s2 = self._adim(s, b)
                    sonuc[s2] = sonuc.get(s2, 0.0) + p
                P[(s, a)] = [
                    (
                        p,
                        s2,
                        0.0 if s2 == self.goal else -1.0,
                        s2 == self.goal,
                    )
                    for s2, p in sonuc.items()
                ]
        return P

    def reset(self, seed=None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.s = self.start
        return self.s

    def step(self, a):
        """Ornekleme: P'den bir sonuc cek."""
        olas = self.P[(self.s, a)]
        idx = self.rng.choice(len(olas), p=[o[0] for o in olas])
        _, s2, r, done = olas[idx]
        self.s = s2
        return s2, r, done
```

```python

class UcurumYuruyusu:
    """4x12 ucurum yuruyusu (Sutton & Barto, genel bilgi). Baslangic
    sol alt,
    hedef sag alt. Alt satirdaki ara hucreler ucurum: -100 ve
    baslangica don.
    Her adim -1. Deterministik."""

    def __init__(self):
        self.H, self.W = 4, 12
        self.S = self.H * self.W
        self.start = 3 * self.W
        self.goal = 3 * self.W + 11
        self.nA = 4
        self.s = self.start

    def ucurum(self, s):
        return s >= 3 * self.W + 1 and s <= 3 * self.W + 10

    def reset(self):
        self.s = self.start
        return self.s

    def step(self, a):
        r, c = divmod(self.s, self.W)
        dr, dc = HAREKETLER[a]
        r = min(max(r + dr, 0), self.H - 1)
        c = min(max(c + dc, 0), self.W - 1)
        s2 = r * self.W + c
        if self.ucurum(s2):
            self.s = self.start
            return self.s, -100.0, False
        self.s = s2
        return s2, -1.0, s2 == self.goal


class Haydut:
    """Bernoulli cok kollu haydut. Odul 1 veya 0, olasilik p[k]."""
```

```python
    def __init__(self, p, rng):
        self.p = np.asarray(p, dtype=float)
        self.rng = rng

    def cek(self, k):
        return float(self.rng.random() < self.p[k])


class CartPole:
    """Barto, Sutton, Anderson (1983) denklemleri, Euler integrasyonu.
    Gymnasium'daki CartPoleEnv ile ayni sabitler ve ayni guncelleme
    sirasi.
    Durum: [x, x_dot, theta, theta_dot]. Eylem: 0 sola, 1 saga iter.
    """

    def __init__(self, rng=None, max_adim=500):
        self.g, self.mc, self.mp = 9.8, 1.0, 0.1
        self.mt = self.mc + self.mp
        self.l = 0.5  # yarim sarkac uzunlugu
        self.mpl = self.mp * self.l
        self.F = 10.0
        self.tau = 0.02
        self.esik_t = 12 * 2 * math.pi / 360
        self.esik_x = 2.4
        self.max_adim = max_adim
        self.rng = (
            rng if rng is not None else np.random.default_rng(0)
        )
        self.durum = None
        self.adim = 0

    def ivme(self, kuvvet, th, thd):
        c, s = math.cos(th), math.sin(th)
        gecici = (kuvvet + self.mpl * thd * thd * s) / self.mt
        th_acc = (self.g * s - c * gecici) / (
            self.l * (4.0 / 3.0 - self.mp * c * c / self.mt)
        )
        x_acc = gecici - self.mpl * th_acc * c / self.mt
        return x_acc, th_acc
```

```python
    def reset(self, seed=None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.durum = self.rng.uniform(-0.05, 0.05, size=4)
        self.adim = 0
        return self.durum.copy()

    def step(self, a):
        x, xd, th, thd = self.durum
        kuvvet = self.F if a == 1 else -self.F
        x_acc, th_acc = self.ivme(kuvvet, th, thd)
        x = x + self.tau * xd
        xd = xd + self.tau * x_acc
        th = th + self.tau * thd
        thd = thd + self.tau * th_acc
        self.durum = np.array([x, xd, th, thd])
        self.adim += 1
        bitti = abs(x) > self.esik_x or abs(th) > self.esik_t
        kesildi = self.adim >= self.max_adim
        return self.durum.copy(), 1.0, bitti, kesildi


class IhaIrtifa:
    """1B IHA irtifa tutma (sadelestirilmis, arastirma amacli).
    Durum: h - h_ref [m], v [m/s]. Eylem: u in [-1,1], itki s=(u+1)/2.
    Dinamik (ileri Euler, dt = 0.05 s):
      a = twr*g*s/kutle - g - kd*v + w(t)
      v <- v + dt*a ; h <- h + dt*v
    w(t): ruzgar bozucusu (sinuzoidal + basamak ruzgar). Kutle,
    surukleme
    ve ruzgar genligi parametre olarak degistirilebilir (alan
    kaymasi).
    Odul: -(e^2 + 0.1 s^2); zemine dusme (h<=0): ek -100 ve bitis."""

    G = 9.81

    def __init__(
        self,
```

```python
        rng=None,
        kutle=1.0,
        kd=0.3,
        twr=2.0,
        ruzgar=1.0,
        h_ref=10.0,
        T=400,
        dt=0.05,
    ):
        self.kutle, self.kd, self.twr = kutle, kd, twr
        self.ruzgar = ruzgar
        self.h_ref, self.T, self.dt = h_ref, T, dt
        self.rng = (
            rng if rng is not None else np.random.default_rng(0)
        )
        self.adim = 0
```

```python
    def ruzgar_at(self, t):
        # sabit faz: test sonuclarini her kosuda ayni kilmak icin
        return self.ruzgar * (
            0.8 * math.sin(2 * math.pi * t / 8.0)
            + 0.5 * (1.0 if 6.0 <= t < 10.0 else 0.0)
        )

    def reset(self, seed=None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.h = self.h_ref + self.rng.uniform(-3.0, 3.0)
        self.v = 0.0
        self.adim = 0
        return self.gozlem()

    def gozlem(self):
        return np.array([(self.h - self.h_ref) / 5.0, self.v / 2.0])

    def step(self, u):
        u = float(np.clip(u, -1.0, 1.0))
        s = (u + 1.0) / 2.0
        t = self.adim * self.dt
        a = (
            self.twr * self.G * s / self.kutle
            - self.G
            - self.kd * self.v
            + self.ruzgar_at(t)
        )
        self.v = self.v + self.dt * a
        self.h = self.h + self.dt * self.v
        self.adim += 1
        e = self.h - self.h_ref
        odul = -(e * e + 0.1 * s * s)
        yere = self.h <= 0.0
        if yere:
            odul -= 100.0
        bitti = yere or self.adim >= self.T
        return self.gozlem(), odul, yere, bitti, s
```

::: dikkat
Yukarıdaki ortamları ezberlemeye gerek yok, ama her birinin neyi modellediğini anlamak gerekir. İHA ortamında sürtünme, rüzgâr ve itki sınırı açıkça kodlandı. Gerçek bir uçağın aerodinamiği bundan çok daha karmaşıktır; sonraki bölümlerde bu sadeleştirmenin sonuçlarını ölçeceğiz.
:::

## 74.2 Keşif ve sömürü: çok kollu haydut

Bir kumar makinesinin beş kolu olduğunu düşün. Her kolun kazanma olasılığı farklı, ama bilmiyorsun. Bir kolu çekip para kazanabilirsin. Amacın, belirli bir sayıda çekişte toplam kazancı en büyütmek. Bu, çok kollu haydut (multi-armed bandit) problemidir ve pekiştirmeli öğrenmenin en küçük, en temiz modelidir: durum yoktur, yalnızca eylem ve ödül vardır.

Bu problem bize **keşif–sömürü ikilemini** (exploration–exploitation dilemma) öğretir. En iyi bildiğin kolu çekmek (sömürü) o anki ödülü maksimize eder, ama daha iyi bir kol olup olmadığını öğrenmez. Yeni kolları denemek (keşif) kısa vadede zarar verir, uzun vadede belki bütün problemi çözer. Hangi dengenin doğru olduğu, kaç çekişimiz kaldığına bağlıdır.

Pişmanlık (regret) bu problemin doğal ölçüsüdür. En iyi kolun beklenen ödülü `p*` olsun. t adımda `a_t` kolunu çektiğinde beklenen kayıp `p* − p[a_t]` olur. Toplam pişmanlık, bu farkların birikimidir:

R(T) = Σ_{t=1}^{T} (p* − p[a_t])

Rastgele bir politika, her adımda ortalama `p* − p̄` kadar kaybeder ve pişmanlığı doğrusal büyür. İyi bir algoritma, en iyi kolu öğrendikten sonra neredeyse hiç yanlış kol çekmez; bu durumda pişmanlık logaritmik büyür. Üç yöntem karşılaştıracağız.

**ε-açgözlü (ε-greedy).** Her adımda olasılık `1 − ε` ile o ana kadar en iyi görünen kolu çekersin; olasılık `ε` ile rastgele bir kol seçersin. Basit ve sağlamdır, ama ε sabit olduğu için keşfe her zaman aynı oranda pay ayırır; bu yüzden pişmanlık doğrusal büyür.

**UCB1 (Upper Confidence Bound).** Her kol için bir üst güven sınırı hesaplarsın: ortalama ödül artı `√(2 ln t / n_a)`. Az denenmiş kollar büyük bir belirsizlik bonusu alır ve sistematik olarak denenir. Bu, "belirsizlik karşısında iyimserlik" ilkesidir. Teoride pişmanlığı logaritmik sınırlar; pratikte sabit katsayı ortama göre ayarlanmalıdır.

**Thompson örneklemesi.** Bayesçi bir yaklaşım: her kol için bir önsel (prior) tutarsın, her adımda bu önseldeki belirsizlikten bir örnek çekersin ve örneği en büyük olan kolu seçersin. Bernoulli ödüllerde kolun başarı olasılığı için Beta önseli kullanmak doğaldır. Bölüm 49'da gördüğün eşlenik önsel, burada da birebir kullanılabilir: `Beta(α, β)` önseli, `s` başarı ve `f` başarısızlık gözleminden sonra `Beta(α + s, β + f)` sonsalına dönüşür. Bu bağ, Bölüm 49'un Beta–Bernoulli modelinin doğrudan bir uygulamasıdır.

Şekil 74.2, üç yöntemin pişmanlık eğrisini beş tohumla gösteriyor. Ortalama etrafındaki bant, tohumlar arası bir sapmadır (±1 standart sapma). Ortam beş kollu bir Bernoulli haydutudur: `p = [0.30, 0.45, 0.55, 0.40, 0.25]`, en iyi kol üçüncüdür. Her yöntem `T = 2000` adım oynar.

Aşağıdaki betik `bandit74.py`, üç yöntemi, pişmanlık hesabını ve sonuç dosyasını içerir. Beş tohum (`0..4`) her yöntem için ayrı bir `numpy` üreteci kullanır; böylece bir yöntemin sonucu diğerinin rastgeleliğinden etkilenmez.

```python
# -*- coding: utf-8 -*-
"""Bolum 74 - Cok kollu haydut: eps-acgozlu, UCB1, Thompson ornekleme.

Ortam: K=5 Bernoulli kolu, p = [0.30, 0.45, 0.55, 0.40, 0.25].
Pismanlik (pseudo-regret): R_T = sum_t (p* - p[a_t]).
5 tohum (0..4), her tohum icin T = 2000 adim.
"""

import os
import numpy as np
from ortam74 import Haydut

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
P = [0.30, 0.45, 0.55, 0.40, 0.25]
T = 2000
TOHUMLAR = [0, 1, 2, 3, 4]


def eps_acgozlu(rng, K, T, eps=0.1):
    n = np.zeros(K)
    q = np.zeros(K)
    secim = []
    env = Haydut(P, rng)
    for t in range(T):
        if rng.random() < eps:
            a = int(rng.integers(K))
        else:
            a = int(
                np.argmax(q + 1e-12 * rng.random(K))
            )  # bagli kiriklari
        r = env.cek(a)
        n[a] += 1
        q[a] += (r - q[a]) / n[a]  # ortalama guncellemesi
        secim.append(a)
    return secim


def ucb1(rng, K, T):
```

```python
    n = np.zeros(K)
    q = np.zeros(K)
    secim = []
    env = Haydut(P, rng)
    for t in range(T):
        if t < K:
            a = t  # her kolu bir kez dene
        else:
            guven = np.sqrt(2 * np.log(t + 1) / n)
            a = int(np.argmax(q + guven))
        r = env.cek(a)
        n[a] += 1
        q[a] += (r - q[a]) / n[a]
        secim.append(a)
    return secim
```

```python

def thompson(rng, K, T):
    """Beta(1,1) onsel; her kol icin Beta(alfa, beta) sonsal, orneklem
    al."""
    alfa = np.ones(K)
    beta = np.ones(K)
    secim = []
    env = Haydut(P, rng)
    for t in range(T):
        ornek = rng.beta(alfa, beta)
        a = int(np.argmax(ornek))
        r = env.cek(a)
        alfa[a] += r
        beta[a] += 1 - r
        secim.append(a)
    return secim


def pismanlik(secim):
    p = np.asarray(P)
    gap = p.max() - p[np.asarray(secim)]
    return np.cumsum(gap)


if __name__ == "__main__":
    yontemler = {
        "eps-acgozlu (0,1)": eps_acgozlu,
        "UCB1": ucb1,
        "Thompson": thompson,
    }
    satirlar = ["algoritma,t,ort,sd"]
    son = {}
    for ad, fn in yontemler.items():
        egriler = []
        for tohum in TOHUMLAR:
            rng = np.random.default_rng(tohum)
            egriler.append(pismanlik(fn(rng, len(P), T)))
        E = np.array(egriler)
```

```python
        son[ad] = E[:, -1]
        for t in range(T):
            satirlar.append(
                "%s,%d,%.4f,%.4f"
                % (ad, t + 1, E[:, t].mean(), E[:, t].std(ddof=1))
            )
        print(
            "%-18s R_T ort=%.2f sd=%.2f"
            % (
                ad,
                E[:, -1].mean(),
                E[:, -1].std(ddof=1),
            )
        )
    os.makedirs(VERI, exist_ok=True)
    with open(
        os.path.join(VERI, "b74_bandit.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")
```

Betiği çalıştırdığında şu sonuçları alırsın:

```term
eps-acgozlu (0,1)  R_T ort=92.24 sd=51.54
UCB1               R_T ort=111.75 sd=18.60
Thompson           R_T ort=30.43 sd=11.23
```

Sonuçlar üç şeyi gösteriyor. Birincisi, Thompson örneklemesi bu ortamda en düşük pişmanlığa sahip (ortalama 30,4). İkincisi, ε-açgözlü yöntemin ortalaması 92,2 olsa da tohumlar arası sapması 51,5 ile çok büyük: beş tohumdan biri 167 gibi yüksek bir değere ulaşırken, diğeri 38'de kalıyor. Üçüncüsü ve en şaşırtıcısı, UCB1'in bu ortamda ε-açgözlüden de kötü olması (111,8). Bunun nedeni, UCB1'in `√(2 ln t)` bonusunun T = 2000 için hâlâ büyük olması ve kollar arası farkların (0,1–0,25) küçük olmasıdır: algoritma, iyi kolu bulduktan sonra da yanlış kolları fazla dener. Bu, UCB1'in kuramsal garantisinin yanlış okunmaması gerektiğini gösterir: logaritmik büyüme sabit katsayı içerir ve bu katsayı ortama göre büyük olabilir.

![Şekil 74.2: Beş kollu Bernoulli haydutu. Birikmiş pişmanlık R(t) (5 tohumun ortalaması ± 1 sapma). Thompson örneklemesi en düşük ve en kararlı eğridir.](gorseller/b74_bandit_pismanlik.png)

::: mulakat
1. Keşif–sömürü ikileminde ε-açgözlü yöntemin ε değerini zamanla azaltmak neden tek başına yeterli değildir? Azaltma takvimi ortamın hangi özelliğine bağlı olmalı?
2. UCB1'de `√(2 ln t / n_a)` terimi neden az denenmiş kolları öne çıkarır? Bir kolu çok deneyince bonusun neden küçüldüğünü açıkla.
3. Thompson örneklemesi ile UCB1 arasındaki temel fark nedir? Hangisi belirsizliği bir önsel üzerinden, hangisi bir üst sınır üzerinden ele alır?
:::

## 74.3 Markov karar süreci: tanımlar ve Bellman denklemleri

Keşif–sömürü problemi durumsuzdu. Gerçek ortamlarda eylemin etkisi bir sonraki durumu değiştirir ve bu yüzden ajanın kararları birbirine bağlıdır. Bu yapıyı kesin bir dille tanımlamak için **Markov karar süreci** (Markov decision process, MDP) kullanılır. Bölüm 62'de Markov zincirlerini ve gizli Markov modellerini görmüştün; MDP, bir zincire eylem ve ödül eklenmiş hâlidir.

Bir MDP beş öğeden oluşur: durum kümesi `S`, eylem kümesi `A`, geçiş olasılığı `P(s' | s, a)`, ödül `R(s, a, s')` ve indirim katsayısı `γ ∈ [0, 1)`. Ajanın davranışı bir politika `π(a | s)` ile verilir: her durumda hangi eylemin hangi olasılıkla seçildiğini söyler. Markov özelliği, bir sonraki durumun yalnızca şimdiki durum ve eylemle belirlenmesi demektir. Geçmiş, şimdiki durumda zaten özetlenmiştir; bu varsayım, Bölüm 62'deki HMM'nin tersine, durumun gözlemlenebilir olduğunu kabul eder. Gözlemlenemiyorsa problem kısmi gözlemlenebilir bir MDP'ye (POMDP) dönüşür; bu, Bölüm 62'deki Kalman ve HMM kestirimiyle birleşir.

Bir bölümde ajanın aldığı toplam indirimli ödül, getiri (return) olarak adlandırılır:

G_t = r_{t+1} + γ r_{t+2} + γ² r_{t+3} + ... = Σ_{k≥0} γ^k r_{t+k+1}

İndirim katsayısı `γ` iki iş görür. Matematiksel olarak sonsuz toplamı sonlu tutar (ödüller sınırlıysa). Pratik olarak ise "yakın ödül uzak ödülden daha değerlidir" tercihini kodlar. `γ = 0,9` ise 10 adım sonraki bir ödülün bugünkü değeri `0,9¹⁰ ≈ 0,35` katıdır; `γ = 0,99` ise `0,99¹⁰ ≈ 0,90` katı. Bu tercih, İHA'da bir sonraki saniyenin ve on saniye sonrasının farklı ağırlıklarla düşünülmesi gibidir.

Değer fonksiyonları, bir politikanın durumlara ve durum–eylem çiftlerine ne kadar değer verdiğini söyler:

V^π(s) = E_π[G_t | s_t = s]
Q^π(s, a) = E_π[G_t | s_t = s, a_t = a]

İkisi arasında doğrudan bir ilişki vardır: `V^π(s) = Σ_a π(a | s) Q^π(s, a)`. Q, bir eylemin değerini, V ise durumun değerini ölçer. Politikanın kendisini V ya da Q'dan kolayca türetebilirsin, bu yüzden değer fonksiyonları RL'nin kalbidir.

### Bellman beklenti denklemi

Bu denklem, değer fonksiyonunun kendi kendine tutarlılığını anlatır. Getiri, bir adım sonrasının getirisi cinsinden yazılabilir:

G_t = r_{t+1} + γ G_{t+1}

Bu özdeşliği koşullu beklentiye al. `s_t = s` verildiğinde `r_{t+1}` ve `s_{t+1}`, politika `π` ve geçiş `P` tarafından belirlenir. Önce eylem üzerinden, sonra sonraki durum üzerinden topla:

V^π(s) = Σ_a π(a | s) Σ_{s'} P(s' | s, a) [ R(s, a, s') + γ V^π(s') ]

Bu, **Bellman beklenti denklemidir**. Bölüm 16'da gördüğün DP tablosundaki `T[i] = min(...)` geçişinin tam karşılığıdır: bir durumun değeri, alt problemlerin değerlerinden ve bir yerel seçimden oluşur. Fark şudur: orada seçim minimumdu ve geçişler belliydi; burada geçişler olasılıksaldır ve seçim politikanın dağılımıdır.

Denklem, `|S|` bilinmeyenli bir doğrusal sistemdir. Matris biçiminde, `P^π(s, s') = Σ_a π(a | s) P(s' | s, a)` ve `R^π(s) = Σ_a π(a | s) Σ_{s'} P(s' | s, a) R(s, a, s')` diyelim. O zaman

V^π = R^π + γ P^π V^π, yani V^π = (I − γ P^π)^{-1} R^π

Bu tersin var olduğunu görmek için `γ < 1` ve `P^π` bir olasılık matrisi olduğu için `‖γ P^π‖_∞ = γ < 1` olduğuna bakman yeterlidir: `I − γ P^π` tersinirdir (Bölüm 48.10'daki koşul sayısı mantığı). Gerçekte ters almak yerine `solve` ile çözmek daha kararlıdır; Bölüm 48'de bunun nedenini gördün.

### Bellman optimallik denklemi

Amaç en iyi politikayı bulmaksa, her durumda en iyi eylemi seçersin. Optimal değer fonksiyonu `V*(s) = max_π V^π(s)` şöyle yazılır:

V*(s) = max_a Σ_{s'} P(s' | s, a) [ R(s, a, s') + γ V*(s') ]

ve optimal Q:

Q*(s, a) = Σ_{s'} P(s' | s, a) [ R(s, a, s') + γ max_{a'} Q*(s', a') ]

Bu denklemin max içermesi, doğrusal olmadığı anlamına gelir. Yine de bir çözümü vardır ve onu bulmak için iki klasik yöntem kullanılır: politika iterasyonu ve değer iterasyonu.

## 74.4 Dinamik programlama: model biliniyorsa

Dinamik programlama (DP), geçiş olasılıkları `P` ve ödül `R` biliniyorsa Bellman denklemlerini doğrudan çözer. Bu, RL'nin "model bilinen" uç durumudur. Gerçek hayatta model nadiren tam bilinir, ama DP hem öğretici hem de sonraki yöntemlerin ölçüt (referans) çözümüdür: model-serbest bir algoritmanın ne kadar iyi olduğunu ölçmek için önce DP ile doğru cevabı bilmen gerekir.

Üç bileşen vardır. **Politika değerlendirme**, belirli bir `π` için `V^π`'yi hesaplar. **Politika iyileştirme**, `V^π`'ye göre açgözlü yeni bir politika seçer: `π'(s) = argmax_a Q^π(s, a)`. Politika iyileştirme teoremi bunun `π`'den kötü olmayan bir politika ürettiğini garanti eder. **Politika iterasyonu**, bu ikisini değişmeyen bir politikaya ulaşana kadar tekrarlar. **Değer iterasyonu** ise iki adımı birleştirir: her yinelemede doğrudan optimallik denklemini bir güncelleme kuralı olarak kullanır.

Değer iterasyonunun neden yakınsadığını anlamak için operatör yazarız. `T` bir değer fonksiyonunu alıp Bellman optimallik sağ tarafını hesaplayan bir eşleme olsun: `(TV)(s) = max_a Σ P [R + γ V(s')]`. Her `U, V` çifti için

‖TV − TU‖_∞ ≤ γ ‖V − U‖_∞

Bu bir **büzülme eşlemesidir** (contraction mapping). Banach'ın sabit nokta teoremi gereği `T`'nin tek bir sabit noktası vardır ve `V_{k+1} = T V_k` dizisi her başlangıçtan o noktaya yakınsar. Hızı bir üst sınırla verir:

‖V_k − V*‖_∞ ≤ γ^k ‖V_0 − V*‖_∞

Bu sınır, Bölüm 50'deki gradyan inişinin yakınsama hızını hatırlatır: büzülme katsayısı `γ`, öğrenme oranı gibi davranır. `γ` 1'e yaklaştıkça yakınsama yavaşlar. Yukarıdaki sınır bir **üst sınırdır**: her zaman geçerlidir ama her zaman sıkı değildir. Bunu aşağıda ölçeceğiz.

Aşağıdaki betik `dp74.py`, dört şeyi yapar: doğrusal çözüm ile yinelemeli politika değerlendirmesinin eşleştiğini gösterir, politika ve değer iterasyonunun aynı optimuma vardığını doğrular, Bellman optimallik kalıntısını ölçer ve yakınsamanın `γ` ile nasıl değiştiğini kaydeder. `SabitOdul` sınıfı, sonsuz bir döngüyü temsil eden tek durumlu bir MDP'dir; yakınsamanın tam olarak `γ^k` olduğunu göstermek için kullanılır.

```python
# -*- coding: utf-8 -*-
"""Bolum 74 - Dinamik programlama: politika degerlendirme, politika
iterasyonu, deger iterasyonu ve gamma'ya gore yakinsama.

Model bilindiginde (P ve R) Bellman denklemleri dogrudan cozulur.
"""

import os
import numpy as np
from ortam74 import GridWorld

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
np.set_printoptions(precision=3, suppress=True)


def matris(env, pi):
    """Politika icin P_pi (S x S) ve beklenen anlik odul R_pi (S)."""
    S = env.S
    P = np.zeros((S, S))
    R = np.zeros(S)
    for s in range(S):
        for p, s2, r, _ in env.P[(s, pi[s])]:
            P[s, s2] += p
            R[s] += p * r
    return P, R


def degerlendir_dogrusal(env, pi, gamma):
    """V = (I - gamma P_pi)^-1 R_pi  (kapali bicim)."""
    P, R = matris(env, pi)
    return np.linalg.solve(np.eye(env.S) - gamma * P, R)


def degerlendir_yinelemeli(env, pi, gamma, esik=1e-10):
    """V_{k+1} = R_pi + gamma P_pi V_k  (sabit nokta yinelemesi)."""
    P, R = matris(env, pi)
    V = np.zeros(env.S)
    for k in range(100000):
        V_yeni = R + gamma * P @ V
        if np.max(np.abs(V_yeni - V)) < esik:
            return V_yeni, k + 1
        V = V_yeni
    return V, k
```

```python

def q_hesapla(env, V, gamma):
    """Q(s,a) = sum p (r + gamma V(s'))."""
    Q = np.zeros((env.S, env.nA))
    for s in range(env.S):
        for a in range(env.nA):
            Q[s, a] = sum(
                p * (r + gamma * V[s2])
                for (p, s2, r, _) in env.P[(s, a)]
            )
    return Q


def politika_iterasyonu(env, gamma):
    pi = np.zeros(env.S, dtype=int)  # baslangic: hep yukari
    for it in range(1, 100):
        V = degerlendir_dogrusal(env, pi, gamma)
        Q = q_hesapla(env, V, gamma)
        yeni = np.argmax(Q, axis=1)
        # esitlik kiriciligi: mevcut eylem Q'da en iyiyse koru
        mevcut_iyi = Q[np.arange(env.S), pi] >= Q.max(axis=1) - 1e-12
        yeni = np.where(mevcut_iyi, pi, yeni)
        if np.array_equal(yeni, pi):
            return V, pi, it
        pi = yeni
    return V, pi, it


def deger_iterasyonu(env, gamma, esik=1e-8):
    """V_{k+1}(s) = max_a sum p (r + gamma V_k(s')). Kalinti dizisi
    doner."""
    V = np.zeros(env.S)
    kalintilar = []
    for k in range(100000):
        Q = q_hesapla(env, V, gamma)
        V_yeni = Q.max(axis=1)
        kalinti = float(np.max(np.abs(V_yeni - V)))
        kalintilar.append(kalinti)
        V = V_yeni
        if kalinti < esik:
            break
    pi = np.argmax(q_hesapla(env, V, gamma), axis=1)
    return V, pi, kalintilar
```

```python

class SabitOdul:
    """Tek durum, tek eylem, odul +1, bitis yok (sonsuz donguyu
    temsil)."""

    def __init__(self):
        self.S, self.nA = 1, 1
        self.P = {(0, 0): [(1.0, 0, 1.0, False)]}


def bellman_optimallik_kalinti(env, V, gamma):
    Q = q_hesapla(env, V, gamma)
    return float(np.max(np.abs(Q.max(axis=1) - V)))


if __name__ == "__main__":
    # 1) 4x4, deterministik: en kisa yol 6 adim (son adim odulsuz),
    # V(0) kapali bicim
    env = GridWorld(4, 4, slip=0.0)
    V44, _, _ = deger_iterasyonu(env, 0.9)
    # 6 adim; son adim hedefte 0 odul verir, yani 5 terim: -1 cezasi
    kapali = -(1 - 0.9**5) / (1 - 0.9)
    print(
        "Deterministik 4x4, V(0) = %.6f, kapali bicim = %.6f"
        % (V44[0], kapali)
    )

    # 2) 5x5, kayganlik 0.1, rastgele politika: dogrusal vs yinelemeli
    env = GridWorld(5, 5, slip=0.1)
    rng = np.random.default_rng(0)
    pi_rast = rng.integers(0, 4, size=env.S)
    V_dog = degerlendir_dogrusal(env, pi_rast, 0.9)
    V_yin, k = degerlendir_yinelemeli(env, pi_rast, 0.9)
    print(
        "Dogrusal ve yinelemeli eslesme farki: %.2e (%d yineleme)"
        % (np.max(np.abs(V_dog - V_yin)), k)
    )
```

```python
    # 3) Politika ve deger iterasyonu, ayni optimum
    for gamma in (0.9, 0.99):
        Vp, pip, it = politika_iterasyonu(env, gamma)
        Vv, piv, kal = deger_iterasyonu(env, gamma)
        print(
            "gamma=%.2f PI: %d it, VI: %d it"
            % (gamma, it, len(kal))
        )
        print(
            "  max|V_PI-V_VI|=%.2e Bellman=%.2e"
            % (
                np.max(np.abs(Vp - Vv)),
                bellman_optimallik_kalinti(env, Vv, gamma),
            )
        )

    # 4) Yakinsama: gamma'ya gore kalinti dizisi
    # (a) 5x5 izgara, hedef mutlak: oran gamma'dan cok kucuk olabilir
    # (b) tek durumlu, odulu +1 olan dongu: kalinti tam olarak gamma^k
    satirlar = ["senaryo,gamma,iter,kalinti"]
    for gamma in (0.5, 0.9, 0.99):
        _, _, kal = deger_iterasyonu(env, gamma, esik=1e-8)
        for i, k_ in enumerate(kal, 1):
            satirlar.append("izgara,%.2f,%d,%.6e" % (gamma, i, k_))
        w = min(10, len(kal) - 2)
        oran = np.array(kal[-w - 1 : -1]) / np.array(kal[-w - 2 : -2])
        print(
            "izgara gamma=%.2f it=%d son %d oran ort=%.4f"
            % (gamma, len(kal), w, oran.mean())
        )
    dongu = SabitOdul()
    for gamma in (0.5, 0.9, 0.99):
        _, _, kal = deger_iterasyonu(dongu, gamma, esik=1e-8)
        for i, k_ in enumerate(kal, 1):
            satirlar.append("dongu,%.2f,%d,%.6e" % (gamma, i, k_))
        oran = np.array(kal[1:]) / np.array(kal[:-1])
        print(
            "dongu gamma=%.2f it=%d oran=%s"
            % (gamma, len(kal), np.round(oran[:2], 2))
        )
    os.makedirs(VERI, exist_ok=True)
    with open(
        os.path.join(VERI, "b74_vi_gamma.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")
```

```python
    # 5) Gorsel icin: optimal V ve politika (5x5, gamma=0.9)
    V, pi, _ = deger_iterasyonu(env, 0.9)
    satirlar = ["satir,sutun,V,politika"]
    for s_ in range(env.S):
        r_, c_ = divmod(s_, env.W)
        satirlar.append("%d,%d,%.5f,%d" % (r_, c_, V[s_], pi[s_]))
    with open(
        os.path.join(VERI, "b74_grid_v.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    print("V* (5x5):")
    print(V.reshape(5, 5))
```

Betiği çalıştırdığında:

```term
Deterministik 4x4, V(0) = -4.095100, kapali bicim = -4.095100
Dogrusal ve yinelemeli eslesme farki: 8.50e-10 (219 yineleme)
gamma=0.90 PI: 4 it, VI: 26 it
  max|V_PI-V_VI|=2.38e-09 Bellman=1.60e-09
gamma=0.99 PI: 4 it, VI: 28 it
  max|V_PI-V_VI|=4.67e-09 Bellman=2.96e-09
izgara gamma=0.50 it=17 son 10 oran ort=0.2532
izgara gamma=0.90 it=26 son 10 oran ort=0.3708
izgara gamma=0.99 it=28 son 10 oran ort=0.4056
dongu gamma=0.50 it=28 oran=[0.5 0.5]
dongu gamma=0.90 it=176 oran=[0.9 0.9]
dongu gamma=0.99 it=1834 oran=[0.99 0.99]
V* (5x5):
[[-5.556 -5.037 -4.442 -3.776 -3.069]
 [-5.037 -4.467 -3.79  -3.029 -2.217]
 [-4.442 -3.79  -3.028 -2.173 -1.237]
 [-3.776 -3.029 -2.173 -1.212 -0.133]
 [-3.069 -2.217 -1.237 -0.133  0.   ]]
```

Sonuçları tek tek okuyalım. İlk satır, deterministik 4×4 ızgarada başlangıç durumunun değerini kapalı biçimle karşılaştırır. Başlangıçtan hedefe en kısa yol 6 adımdır, ama son adım hedefte 0 ödül verir ve yalnızca 5 adımın `−1` cezası toplanır: `−(1 − 0,9⁵)/(1 − 0,9) = −4,0951`. Bu, bir "tuzak" değildir, Bellman denkleminin kendisidir: hedef durumun değeri 0'dır ve geçiş ödülü hedefe giden adımda alınmaz. Bu ayrıntıyı atlamak, Bölüm 74.14'teki ödül tasarımında da karşına çıkacak.

İkinci satır, doğrusal çözüm `(I − γP^π)^{-1}R^π` ile yinelemeli değerlendirmenin 5×5 kaygan ızgarada `8,5 × 10⁻¹⁰` farkla eşleştiğini gösterir. Yinelemeli yöntem 219 adımda durdu. İki yol aynı cevabı verir; hangisinin kullanılacağı büyüklüğe ve hız gereksinimine bağlıdır.

Üçüncü ve dördüncü satırlar politika iterasyonu ile değer iterasyonunu karşılaştırır. Politika iterasyonu yalnızca 4 dış adımda yakınsadı; değer iterasyonu 26–28 adım sürdü. Ama her politika iterasyonu adımı bir doğrusal çözüm gerektirdiği için maliyeti değer iterasyonundan yüksektir. İki yöntemin optimumu `10⁻⁹` düzeyinde aynıdır; bu, Bellman optimallik kalıntısının da `10⁻⁹` düzeyinde olduğunu gösterir: bulunan `V` gerçekten optimallik denklemini sağlıyor.

Betiğin son kısmı yakınsamayı ölçüyor. Burada ilginç bir şey var: ızgarada kalıntı oranı (son adımların `kalıntı_{k+1}/kalıntı_k` ortalaması) `γ` değerlerinden çok daha küçük: 0,25, 0,37, 0,41. Bunun nedeni, ızgarada hedef durumun **mutlak** olması ve ajanın hedefe ulaşma olasılığının yüksek olmasıdır: değer, birkaç adım içinde kesin değerine ulaşır. Oysa tek durumlu sonsuz döngüde (`SabitOdul`) kalıntı tam olarak `γ^k` ile azalır (oran 0,5, 0,9, 0,99). Yani `γ^k` bir üst sınırdır; ızgara bu sınırın çok altında kalır, döngü ona tam olarak eşit olur. Şekil 74.4 bu ikisini yan yana gösteriyor.

Son bölümde, 5×5 ızgarada `γ = 0,9` için hesaplanan optimal değer fonksiyonu ve politikası Şekil 74.3'te görülüyor. Her hücrenin rengi `V*`'ı, üzerindeki sayı değeri, ok ise optimal eylemi gösterir. Sağ alt köşedeki hedefe giden okların yönü, değer kademeli olarak yükseldiği için sezgisel olarak doğrudur. Kayganlık (`slip = 0,1`) nedeniyle değer hedefe uzak hücrelerde biraz daha düşük ve hedefe yakın hücrelerde biraz daha az negatiftir; bu, rastgele kayma olasılığının bir cezası olarak yansır.

![Şekil 74.3: 5×5 kaygan ızgarada (slip 0,1, γ = 0,9) optimal değer fonksiyonu V* ve optimal eylemler. Hedef sağ alt köşe (kalın çerçeve), her adım −1 ceza.](gorseller/b74_izgara_deger.png)

![Şekil 74.4: Değer iterasyonunda kalıntı max|V_{k+1} − V_k| (logaritmik ölçek). Sol: 5×5 ızgara; ızgarada yakınsama γ'dan hızlıdır. Sağ: tek durumlu sonsuz döngü; kalıntı tam olarak γ^k ile azalır.](gorseller/b74_vi_yakinsama.png)

::: baglanti
Dinamik programlama ile en kısa yol (Bölüm 17) aynı fikre dayanır: bir düğümün değeri, komşularının değerlerinden ve bir yerel seçimden hesaplanır. Bölüm 17'deki Bellman–Ford, bu değer iterasyonunun ağırlıklı bir grafta, en fazla `|V| − 1` adımda sona eren bir biçimidir. Fark, orada geçişlerin deterministik olması ve minimum almamızdır; burada geçişlerin olasılıksal olması ve maksimum almamızdır.
:::

Bu bölümde DP'nin tek başına bir ajan eğitmediğini unutma. DP, model bilindiğinde doğru cevabı verir; ama gerçek dünyada `P` ve `R` çoğu zaman bilinmez. Bir sonraki bölümde, modeli bilmeden, yalnızca örneklerden değer tahmin etmeyi göreceğiz.

## 74.5 Modelsiz tahmin: Monte Carlo ve zamansal fark

Dinamik programlama `P`'yi bilmeyi gerektiriyordu. Gerçek ortamda ajan yalnızca örnekler toplayabilir: durum, eylem, ödül ve bir sonraki durum. Bu bölümde iki temel fikri, Monte Carlo ve zamansal fark (TD) öğrenmesini, aynı tahmin problemi üzerinde karşılaştıracağız: sabit bir politika için `V^π`'yi tahmin etmek.

**Monte Carlo (MC).** Değeri tanımına sadık kalarak hesaplar: `V^π(s)` bir beklenen getiri olduğuna göre, bir bölüm bittiğinde o bölümde `s` durumunu ziyaret ettikten sonra gerçekleşen getiriyi kaydeder ve bu getirilerin ortalamasını alırsın. "İlk ziyaret" varyantı, her bölümde bir durumun yalnızca ilk görülmesini sayar. Bölüm 49'daki örnek ortalaması ile aynı fikirdir: `V(s) ← V(s) + α (G − V(s))`, `α = 1/n` ise tam ortalama. MC tarafsızdır, ama bölüm sonuna kadar beklemek ve getirinin çok değişkenli olması onu yavaş ve gürültülü kılar. Yalnızca bölümsel (episodik) görevlerde çalışır.

**Zamansal fark (TD(0)).** Bölüm bitmeden, her adımda güncelleme yapar. Bellman denkleminden yola çıkar: `V(s) = E[r + γ V(s')]`. Örnek bir geçiş `(s, r, s')` için **TD hatası** şudur:

δ_t = r_{t+1} + γ V(s_{t+1}) − V(s_t)

ve güncelleme `V(s_t) ← V(s_t) + α δ_t` biçimindedir. Bu, **önyükleme** (bootstrapping) yapar: bir tahmini başka bir tahminle günceller. Bu sayede daha düşük varyanslı olur (tek bir adımın rastgeleliğine bağlıdır), ama tahmin yanlı olabilir, çünkü hedef `V(s_{t+1})`'in kendisi de hatalıdır. Bu, sonraki bölümlerde defalarca karşımıza çıkacak denge: **yanlılık ile varyans arasında takas**.

Bu ikisinin arasında bir spektrum vardır. `n`-adım dönüşlerde hedef, `n` gerçek ödül ve ardından `V(s_{t+n})` ile hesaplanır. `n = 1` TD(0), `n = ∞` MC'dir. TD(λ) bu dönüşlerin ağırlıklı bir karışımını alır. Bu bölümde yalnızca iki uç noktayı ölçüyoruz, ama fikir aynıdır: hedefte ne kadar gerçek ödül kullanırsan, o kadar az yanlı ve o kadar çok gürültülü olursun.

Bir uyarı: TD hatası, Bölüm 74.7'deki fonksiyon yaklaşımında da aynı rolü oynar. Orada `V` bir tablo değil, bir sinir ağı olduğunda, bu hata bir gradyan adımı olarak yeniden görünecek ve işler zorlaşacak.

## 74.6 Kontrol: SARSA ve Q-learning

Tahmin problemi, politikayı değiştirmeden değeri ölçer. Kontrol (control) problemi ise hem değeri hem de politikayı aynı anda öğrenmeyi ister. İki klasik yöntem, durum–eylem değerini `Q` üzerinden öğrenir ve bu iki yöntem arasındaki fark, RL'nin en öğretici kavramlarından biridir: **on-policy** ve **off-policy** öğrenme.

**SARSA** (State–Action–Reward–State–Action) güncellemesi:

Q(s, a) ← Q(s, a) + α [ r + γ Q(s', a') − Q(s, a) ]

Burada `a'`, ajanın bir sonraki adımda **gerçekten seçeceği** eylemdir. Hedef, izlenen politikanın değeri üzerinden hesaplanır. Bu nedenle SARSA on-policy'dir: öğrendiği değer, keşif yaparken kullandığı politikaya aittir.

**Q-learning** güncellemesi:

Q(s, a) ← Q(s, a) + α [ r + γ max_{a'} Q(s', a') − Q(s, a) ]

Burada hedef, bir sonraki durumda en iyi eylemin değeridir; ajanın gerçekte ne yapacağına bakmaz. Bu nedenle Q-learning off-policy'dir: davranış politikası (keşif yapan) ile öğrenilen politika (açgözlü) farklıdır. Bellman optimallik denkleminin (74.3) doğrudan örneklenmiş bir hâlidir: `max` sayesinde Q-learning `Q*`'a doğrudan yönelir.

Bu fark, bir yoldaki riski nasıl ele aldığında ortaya çıkar. **Uçurum yürüyüşü** (cliff walking) klasik bir örnektir (Sutton ve Barto, genel bilgi). Ajan 4×12'lik bir ızgarada sol alt köşeden sağ alt köşeye gitmek zorundadır. Alt satırın ortası bir uçurumdur: oraya düşen ajan −100 alır ve başlangıca döner. Her adım −1 kazandırır. En kısa yol, uçurumun hemen üstündeki sırada yürümektir; ama keşif için rastgele bir eylem (ε = 0,1) seçildiğinde ajan uçuruma düşebilir. En güvenli yol, en üstteki sırada yürümektir; daha uzun ama uçurumdan uzak.

Q-learning, kısa yolu öğrenir: uçurumun kenarında yürür, çünkü hedefi açgözlü politikaya göre hesaplar ve keşif sırasındaki düşme riskini hesaba katmaz. SARSA ise davranış politikasının, yani ε-açgözlü politikanın değerini öğrenir ve kenar boyunca yürümenin riskini görür; bu yüzden güvenli yolu seçer. Eğitim sırasında elde edilen toplam ödüller bunu açıkça gösterir.

Şekil 74.5 iki yolu ve eğitim eğrilerini gösteriyor. Aşağıdaki betik `td74.py`, bu bölümdeki tablosal deneylerin tamamını içerir: uçurum yürüyüşü (SARSA ve Q-learning), 4×4 kaygan ızgarada Q-learning'in DP çözümüne yakınsaması ve MC ile TD(0)'ın karşılaştırması. Her deney beş tohumla yapılır.

```python
# -*- coding: utf-8 -*-
"""Bolum 74 - Model-serbest tablosal yontemler.

(a) Ucurum yuruyusu: SARSA (on-policy) ve Q-learning (off-policy),
eps=0.1
(b) 4x4 kayganlik 0.1 izgarada Q-learning'in DP cozumune yakinsamasi
(c) MC (ilk ziyaret) ve TD(0) tahmini, V^pi'ye karsi RMSE
5 tohum (0..4) her deneyde.
"""

import os
import numpy as np
from ortam74 import GridWorld, UcurumYuruyusu
from dp74 import deger_iterasyonu, q_hesapla, degerlendir_dogrusal

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
TOHUMLAR = [0, 1, 2, 3, 4]


def eps_secim(q, eps, rng):
    if rng.random() < eps:
        return int(rng.integers(len(q)))
    enb = np.flatnonzero(q == q.max())  # esitlikte rastgele
    return int(rng.choice(enb))


def ogren(
    env,
    yontem,
    seed,
    bolum,
    gamma=1.0,
    eps=0.1,
    alfa=0.5,
    adim_siniri=1000,
    Q_yildiz=None,
    kayit_her=None,
):
```

```python
    """SARSA veya Q-learning. alfa=None ise 1/n(s,a) (Robbins-
    Monro)."""
    rng = np.random.default_rng(seed)
    env.rng = np.random.default_rng(seed + 1000)
    Q = np.zeros((env.S, env.nA))
    n = np.zeros((env.S, env.nA))
    getiri, hatalar = [], []
    for ep in range(1, bolum + 1):
        s = env.reset()
        a = eps_secim(Q[s], eps, rng)
        G, adim = 0.0, 0
        while True:
            s2, r, bitti = env.step(a)
            G += r
            adim += 1
            a2 = eps_secim(Q[s2], eps, rng)
            n[s, a] += 1
            al = alfa if alfa is not None else 1.0 / n[s, a]
            if bitti:
                hedef = r
            elif yontem == "sarsa":
                hedef = r + gamma * Q[s2, a2]
            else:  # q-learning
                hedef = r + gamma * Q[s2].max()
            Q[s, a] += al * (hedef - Q[s, a])
            if bitti or adim >= adim_siniri:
                break
            s, a = s2, a2
        getiri.append(G)
        if Q_yildiz is not None and kayit_her and ep % kayit_her == 0:
            hatalar.append((ep, float(np.max(np.abs(Q - Q_yildiz)))))
    return Q, np.array(getiri), hatalar
```

```python

def acgozlu_yol(Q, env, adim=40):
    """Acgozlu politikayi takip edip yolu koordinat olarak dondur."""
    s = env.reset()
    yol = [s]
    for _ in range(adim):
        a = int(np.argmax(Q[s]))
        s, _, bitti = env.step(a)
        yol.append(s)
        if bitti:
            break
    return yol


def v_stokastik(env, gamma):
    """Tek tip rastgele politika icin V^pi (kapali bicim)."""
    S = env.S
    P = np.zeros((S, S))
    R = np.zeros(S)
    for s in range(S):
        for a in range(env.nA):
            for p, s2, r, _ in env.P[(s, a)]:
                P[s, s2] += p / env.nA
                R[s] += p * r / env.nA
    return np.linalg.solve(np.eye(S) - gamma * P, R)


def mc_td_tahmin(
    env, V_hedef, seed, bolum, gamma=0.9, alfa=0.1, yontem="td"
):
    """Tek tip rastgele politika; RMSE(V, V^pi) her 'kayit'
    bolumde."""
    rng = np.random.default_rng(seed)
    env.rng = np.random.default_rng(seed + 2000)
    V = np.zeros(env.S)
    sonuc = {}
    for ep in range(1, bolum + 1):
        s = env.reset()
```

```python
        yol = []
        bitti = False
        adim = 0
        while not bitti and adim < 500:
            a = int(rng.integers(env.nA))
            s2, r, bitti = env.step(a)
            adim += 1
            if yontem == "td":
                hedef = r + (0.0 if bitti else gamma * V[s2])
                V[s] += alfa * (hedef - V[s])
            else:
                yol.append((s, r))
            s = s2
        if yontem == "mc":
            # ilk ziyaret MC: geri donus getirileri, ilk gorulen yerde
            # guncelle
            geri = []
            G = 0.0
            for st, r in reversed(yol):
                G = r + gamma * G
                geri.append((st, G))
            geri.reverse()
            gorulen = set()
            for st, Gt in geri:
                if st not in gorulen:
                    gorulen.add(st)
                    V[st] += alfa * (Gt - V[st])
        if ep in (10, 100, 1000, bolum):
            sonuc[ep] = float(np.sqrt(np.mean((V - V_hedef) ** 2)))
    return sonuc
```

```python

if __name__ == "__main__":
    os.makedirs(VERI, exist_ok=True)

    # (a) Ucurum yuruyusu
    satirlar = ["yontem,bolum,ort,sd"]
    yol_satir = ["yontem,r,c"]
    son_ort = {}
    for yontem in ("sarsa", "qlearn"):
        E = []
        for tohum in TOHUMLAR:
            env = UcurumYuruyusu()
            Q, G, _ = ogren(env, yontem, tohum, 500)
            E.append(G)
            if tohum == 0:
                yol = acgozlu_yol(Q, env)
                for s in yol:
                    r, c = divmod(s, env.W)
                    yol_satir.append("%s,%d,%d" % (yontem, r, c))
        E = np.array(E)
        # 10'luk kayan ortalama (her tohum icin), sonra tohum
        # ortalamasi
        kay = np.array(
            [
                np.convolve(e, np.ones(10) / 10, mode="valid")
                for e in E
            ]
        )
        for i in range(kay.shape[1]):
            satirlar.append(
                "%s,%d,%.3f,%.3f"
                % (
                    yontem,
                    i + 10,
                    kay[:, i].mean(),
                    kay[:, i].std(ddof=1),
                )
            )
```

```python
        son = E[:, -100:].mean(axis=1)
        son_ort[yontem] = son
        print(
            "%-7s son100 ort=%.2f sd=%.2f"
            % (yontem, son.mean(), son.std(ddof=1))
        )
    with open(
        os.path.join(VERI, "b74_cliff_egri.csv"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    with open(
        os.path.join(VERI, "b74_cliff_yol.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(yol_satir) + "\n")
```

```python
    # (b) 4x4 kaygan izgara: Q-learning, Q* ile maksimum sapma
    env = GridWorld(4, 4, slip=0.1)
    V_star, _, _ = deger_iterasyonu(env, 0.9)
    Q_star = q_hesapla(env, V_star, 0.9)
    eg = []
    greedy_hata = []
    for tohum in TOHUMLAR:
        env = GridWorld(4, 4, slip=0.1)
        Q, _, h = ogren(
            env,
            "qlearn",
            tohum,
            20000,
            gamma=0.9,
            eps=0.2,
            alfa=None,
            Q_yildiz=Q_star,
            kayit_her=1000,
        )
        eg.append([x[1] for x in h])
        pi_g = np.argmax(Q, axis=1)
        Vg = degerlendir_dogrusal(env, pi_g, 0.9)
        greedy_hata.append(float(np.max(np.abs(Vg - V_star))))
    eg = np.array(eg)
    satirlar = ["bolum,ort,sd"]
    for i in range(eg.shape[1]):
        satirlar.append(
            "%d,%.5f,%.5f"
            % ((i + 1) * 1000, eg[:, i].mean(), eg[:, i].std(ddof=1))
        )
    with open(
        os.path.join(VERI, "b74_q_dp.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    print(
        "Q-learning max|Q-Q*|: 1000. bolum %.3f, 20000. bolum %.4f"
        % (eg[:, 0].mean(), eg[:, -1].mean())
    )
    print(
        "Greedy V - V* (max, 5 tohum):",
        np.round(greedy_hata, 4),
    )
```

```python
    # (c) MC ve TD(0) tahmini (rastgele politika, gamma=0.9)
    env = GridWorld(4, 4, slip=0.1)
    V_pi = v_stokastik(env, 0.9)
    tablo = {}
    for yontem in ("mc", "td"):
        kayitlar = [
            mc_td_tahmin(
                GridWorld(4, 4, slip=0.1),
                V_pi,
                t,
                1000,
                yontem=yontem,
            )
            for t in TOHUMLAR
        ]
        for ep in (10, 100, 1000):
            vals = np.array([k[ep] for k in kayitlar])
            tablo[(yontem, ep)] = (vals.mean(), vals.std(ddof=1))
    print("RMSE(V, V^pi), 5 tohum ort (sd):")
    for ep in (10, 100, 1000):
        print(
            "  %5d bolum  MC %.3f (%.3f)   TD(0) %.3f (%.3f)"
            % (ep, *tablo[("mc", ep)], *tablo[("td", ep)])
        )
```

Betiğin çıktısı:

```term
sarsa   son100 ort=-28.17 sd=4.89
qlearn  son100 ort=-53.70 sd=5.41
Q-learning max|Q-Q*|: 1000. bolum 1.059, 20000. bolum 0.2896
Greedy V - V* (max, 5 tohum): [0.    0.014 0.014 0.021 0.014]
RMSE(V, V^pi), 5 tohum ort (sd):
     10 bolum  MC 3.483 (0.601)   TD(0) 4.596 (0.883)
    100 bolum  MC 0.592 (0.237)   TD(0) 0.307 (0.131)
   1000 bolum  MC 0.612 (0.067)   TD(0) 0.402 (0.153)
```

Uçurum deneyinde son 100 bölümün eğitim getirisi SARSA için −28,2 ± 4,9, Q-learning için −53,7 ± 5,4. Beş tohumun her birinde SARSA, Q-learning'den yüksek getiri aldı: SARSA için −23,2 ile −33,5 arası, Q-learning için −46,6 ile −61,8 arası. İki aralık hiç örtüşmüyor. Açgözlü yolların farkı (Şekil 74.5 sol) bu sayıları açıklar: Q-learning uçurumun bir üst sırasında, SARSA ise en üst sırada yürür. Eğitim eğrilerinde (sağ) yaklaşık 210. bölüm civarında görülen geniş sapma bandı, tek bir tohumun o bölgede geçici olarak kötü bir politika izlemesinin izidir; tohumlar arası dalgalanma, tek bir koşuya bakarak karar vermenin neden yanıltıcı olabileceğini gösterir.

Q-learning'in DP çözümüne yakınsamasını ölçmek için, kaygan 4×4 ızgarada `Q*` (DP ile) ile Q-learning tablosunun maksimum sapmasına baktık. Değiştirme (`α = 1/n(s, a)`) ve `ε = 0,2` keşif ile 20 000 bölüm sonunda maksimum sapma 1,06'dan 0,29'a düşüyor. Ama bu sayıyı yanıltıcı okumamak gerekir: en büyük sapma, ziyaret sayısı çok az olan bazı `(s, a)` çiftlerinde kalır. Daha anlamlı ölçüt, açgözlü politikanın değeridir: `V^{π_Q}` ile `V*` arasındaki maksimum fark beş tohumda 0,000–0,021 aralığındadır. Yani politika, optimal politikaya neredeyse aynı değerle ulaşmış; tablonun her köşesi değil, politika için önemli olan köşeler doğru hale gelmiştir. Bu ayrım, RL'de ölçüm yaparken "neyi ölçtüğünü bilmenin" önemini gösterir.

MC ile TD(0)'ın karşılaştırması, aynı rastgele politika (her eylem eşit olasılıkla) ile yapıldı ve `V^π` kapalı biçim çözümüne karşı RMSE ile ölçüldü. Sabit `α = 0,1` kullanıldığı için her iki yöntemde de bir gürültü tabanı vardır; bu yüzden değerler yakınsama değil, bu tabana ulaşma hızını gösterir. On bölümde MC'nin hatası (3,48) TD'ninkinden (4,60) düşük; 100 bölümde TD (0,31) MC'yi (0,59) geçer; 1000 bölümde MC'nin tabanı (0,61) TD'nin (0,40) üzerinde kalır. Bu, teoriyle tutarlıdır: MC'nin getirisi çok değişkendir ve sabit `α` ile büyük bir gürültü tabanı oluşturur; TD ise daha düşük varyanslıdır, ama önyükleme yanlılığı taşır. Hangisinin daha iyi olduğu, `α` takvimine ve ortamın uzunluğuna bağlıdır.

![Şekil 74.5: Uçurum yürüyüşü. Sol: açgözlü politikanın yolları; SARSA en üst sırada güvenli yolu, Q-learning uçurum kenarındaki kısa yolu izler. Sağ: eğitim getirisi (10'lu ortalama), 5 tohum, ε = 0,1.](gorseller/b74_ucurum.png)

::: not
Keşif takvimi, öğrenme kalitesinin bir parçasıdır. Sabit ε (burada 0,1) hiçbir zaman tam sömürüye geçmez: eğitimin sonunda bile ajan %10 oranında rastgele hareket eder. Pratikte ε zamanla azaltılır. Robbins–Monro koşulu, `Σ α_t = ∞` ve `Σ α_t² < ∞`, tablosal yakınsamanın güvencesidir; `α = 1/n` bu koşulu sağlar, sabit `α = 0,1` sağlamaz. Bu bölümdeki Q-learning–DP deneyinde `α = 1/n` kullandık.
:::

::: mulakat
1. Q-learning ile SARSA arasındaki fark nedir? Uçurum yürüyüşünde hangisi neden güvenli olmayan yolu seçer, hangisi neden güvenli yolu seçer?
2. TD(0) hatası `δ_t` nedir? Bir tahmin neden kendi tahminiyle güncellenirse yanlı olur ama daha az değişken olur?
3. Monte Carlo yöntemi neden yalnızca bölümsel görevlerde çalışır? Sürekli bir görevde bu yöntemi nasıl uyarlarsın?
:::

## 74.7 Fonksiyon yaklaşımı ve ölümcül üçlü

Tablosal yöntemler, her durum–eylem çifti için ayrı bir sayı tutar. Durum sayısı büyüdüğünde bu imkânsızlaşır: bir İHA'nın sensör durumu sürekli bir uzaydır ve tablo bu uzayı yalnızca dışarıdan görebilir. Çözüm, `Q(s, a)`'yı bir parametrik fonksiyonla yaklaştırmaktır: `Q(s, a; θ)`, Bölüm 63–65'te gördüğün doğrusal model ya da sinir ağı olabilir. Bu, pekiştirmeli öğrenmeyi denetimli öğrenmeye yaklaştırır: her adımda bir hedef `y` ve bir tahmin `Q(s, a; θ)` olur, kayıp da aralarındaki farktır.

Burada tehlikeli bir durum ortaya çıkar. Doğrusal yaklaşımla birlikte üç özellik bir araya gelirse öğrenme ıraksayabilir. Bu üç özelliğe **ölümcül üçlü** (deadly triad) denir (Sutton ve Barto 2018, genel bilgi):

1. **Fonksiyon yaklaşımı:** `V` bir tablo değil, sınırlı kapasiteli bir fonksiyon.
2. **Önyükleme (bootstrapping):** hedef, kendi tahmininden oluşur (TD gibi).
3. **Politika dışı (off-policy) öğrenme:** güncellemelerin dağılımı, hedef politikanın dağılımından farklı.

Üçü birlikte varsa, ağırlıkların sınırsız büyüyebildiği bilinen karşı örnekler vardır. En ünlüsü **Baird'in karşı örneğidir**: 7 durumlu, 8 ağırlıklı, ödülün her zaman sıfır olduğu bir MDP. Hedef politika her zaman "solid" eylemi seçer ve bu eylem durum 6'ya (alt sağ) gider. Davranış politikası ise çoğunlukla "dashed" seçer ve bu eylem üst durumlardan birine rastgele gider. Ödül sıfır olduğu için doğru değer fonksiyonu sıfırdır: ağırlıklar sıfıra gitmelidir. Yine de ıraksarlar.

Ne olduğunu anlamak için iki güncelleme dağılımına bakalım. Betik, tüm durumlar üzerinde **senkron** (sweep) güncelleme yapar; her durumun güncellemesi, o durumun dağılımdaki ağırlığıyla çarpılır. Politika içi (on-policy) dağılımda ağırlık yalnızca durum 6'dadır, çünkü hedef politika altında ajan oraya yerleşir. Politika dışı durumda ise ağırlık düzgündür (her durum 1/7). Aynı özellikler, aynı ödüller, aynı `γ = 0,99` ve `α = 0,01` kullanılır; yalnızca güncelleme dağılımı değişir.

Aşağıdaki betik `baird74.py` bu iki durumu karşılaştırır.

```python
# -*- coding: utf-8 -*-
"""Bolum 74 - Olumcul ucluu (deadly triad): Baird'in karsi ornegi.

Dogrusal fonksiyon yaklasimi + onyukleme (bootstrap) + politika disi
(off-policy) ogrenme birlikte kararsizlik uretebilir. Sutton & Barto
(2018), Ornek 11.1'in yapisinin sadelestirilmis gerceklemesi (genel
bilgi).
7 durum (0..5 ust, 6 alt-sag), 8 agirlik, odul 0, gamma = 0.99, alfa =
0.01.

Beklenen (sentetik, senkron) TD guncellemesi:
  theta <- theta + alfa * sum_s d(s) * rho_bek(s) * delta_s * x(s)
Iki guncelleme dagilimi:
  on-policy : d = hedef politikanin duragan dagilimi (yalnizca durum
  6)
  off-policy: d = duzgun (her durum 1/7); davranis-hedef farki burada
Ust durumlarda E_b[rho] = 1 (dashed rho=0, solid rho=7 w.p. 1/7).
"""

import numpy as np

GAMMA, ALFA = 0.99, 0.01


def ozellik(s):
    x = np.zeros(8)
    if s < 6:
        x[s] = 2.0
        x[7] = 1.0
    else:
        x[6] = 1.0
        x[7] = 2.0
    return x


def adim(th, dagilim):
    x6 = ozellik(6)
    yeni = th.copy()
    for s in range(7):
        if dagilim[s] == 0:
            continue
        xs = ozellik(s)
        delta = GAMMA * th @ x6 - th @ xs
        yeni = yeni + ALFA * dagilim[s] * delta * xs
    return yeni
```

```python

if __name__ == "__main__":
    th0 = np.array([1, 1, 1, 1, 1, 1, 10, 1], dtype=float)
    on = np.array([0, 0, 0, 0, 0, 0, 1.0])
    off = np.full(7, 1 / 7)
    th_on, th_off = th0.copy(), th0.copy()
    print(
        "sweep   ||theta|| on-policy   ||theta|| off-policy (uniform)"
    )
    for k in range(1, 1001):
        th_on = adim(th_on, on)
        th_off = adim(th_off, off)
        if k in (1, 50, 100, 200, 300, 500, 1000):
            print(
                "%5d   %15.4f   %25.4e"
                % (k, np.linalg.norm(th_on), np.linalg.norm(th_off))
            )
    print("off-policy theta (1000 sweep):")
    print(np.array2string(th_off, precision=2, max_line_width=70))
```

```term
sweep   ||theta|| on-policy   ||theta|| off-policy (uniform)
    1           10.3427                  1.0366e+01
   50           10.2759                  1.2585e+01
  100           10.2107                  1.6826e+01
  200           10.0885                  2.9650e+01
  300            9.9767                  4.7511e+01
  500            9.7809                  1.0122e+02
 1000            9.4230                  4.3686e+02
off-policy theta (1000 sweep):
[114.43 114.43 114.43 114.43 114.43 114.43   6.85 335.  ]
```

Politika içi dağılımda `‖θ‖` 10,3'ten 9,4'e yavaşça düşer: ağırlıklar sıfıra doğru gider, bu doğrudur. Politika dışı, düzgün dağılımda ise ağırlık normu 10,4'ten 436,9'a çıkar ve hâlâ büyümektedir; 1000 süpürme sonunda birinci ağırlık 114 olur ve yedinci ağırlık 335'e ulaşır. Aynı fonksiyon yaklaşımı, aynı ödül, aynı adım boyu; tek fark, güncellemelerin hangi dağılımdan geldiğidir. Bu, ölümcül üçlünün "politika dışı" ayağının ne anlama geldiğini gösterir: hedef, güncellemelerin yapıldığı dağılımla uyumlu değilse, yaklaşım hatası bir geri besleme döngüsünde büyür.

Bu ne anlama gelir? Derin RL ağlarını eğitirken her üç özelliği de kullanırsın: bir sinir ağı, önyükleme ve tipik olarak replay tamponundan gelen politika dışı örnekler. Bu yüzden DQN'in neden kararsız olabileceğini ve neden iki kritik tekniğe (hedef ağ ve replay) ihtiyaç duyduğunu anlamak için bu karşı örneği görmek gerekir. Bir sonraki bölümde bunların etkisini ölçeceğiz.

## 74.8 DQN: derin Q-öğrenme

DQN (Deep Q-Network, Mnih ve arkadaşları 2015, genel bilgi), Q-learning'in `Q(s, a; θ)` için bir sinir ağı kullanan hâlidir. Q-learning'in güncelleme hedefi `y = r + γ max_{a'} Q(s', a'; θ)` idi. DQN bu hedefi ve kaybı şöyle kurar:

L(θ) = E[ Huber( y − Q(s, a; θ) ) ], y = r + γ (1 − d) max_{a'} Q(s', a'; θ⁻)

Burada üç kritik bileşen var, ve her biri ölçülecek:

**Deneyim tekrarı (experience replay).** Ajanın geçişleri `(s, a, r, s', d)` bir tampona yazılır ve eğitim, tampondan rastgele örneklerle yapılır. Bu, ardışık geçişlerin yüksek korelasyonunu kırar ve her verinin birden çok kez kullanılmasını sağlar. Tampon bir **dairesel tampondur** (Bölüm 7.7'de gördüğün yapı): kapasite dolunca en eski geçiş üzerine yazılır. Tampon, politika dışı örneklerin kaynağıdır; Baird'de gördüğün ölümcül üçlünün üçüncü ayağıdır. Tekrar yine de faydalıdır, çünkü tampondaki geçişler artık hedef politika ile daha az uyumludur ama hedef ağ bu kaymayı yumuşatır.

**Hedef ağ (target network).** Hedefteki `θ⁻` parametreleri, tahmin ağının `θ` parametrelerinin ayrı bir kopyasıdır ve yalnızca belirli aralıklarla (bu betikte her 250 adımda) güncellenir. Böylece hedef, her adımda değişen bir hedef değil, sabit bir referans olur. Bu, Baird'de gördüğümüz geri besleme döngüsünü kırar: hedef, tahminin hemen ardından kendi değişimine tepki vermez.

**Huber kaybı.** Büyük hatalar için kare kaybı yerine doğrusal bir ceza kullanılır: `|x| ≤ 1` için `0,5 x²`, değilse `|x| − 0,5`. Bu, aykırı bir hedefin gradyanı patlatmasını önler. Ayrıca gradyan normu 10 ile kırpılır (Bölüm 64.9).

**Double DQN.** Standart hedefte `max` işlemi, aynı ağla hem eylemi seçer hem değerlendirir. Gürültülü tahminlerde maksimum almak, değerleri yukarı yanlı tahmin eder (bu, Bölüm 49'da gördüğün "gürültülü tahminlerin maksimumu" sorunudur). Double DQN, seçimi çevrimiçi ağa, değerlendirmeyi hedef ağa bırakır: `y = r + γ Q(s', argmax_{a'} Q(s', a'; θ); θ⁻)`. Bu, yanlılığı azaltır, yok etmez.

Ajanın davranışı ε-açgözlüdür ve ε, ilk 5000 adımda 1,0'dan 0,05'e doğrusal düşer. Eğitim 500 geçişten sonra başlar; her adımda tampondan 64 geçişle bir gradyan adımı atılır. Kendi CartPole'umuz (Bölüm 74.1'deki `ortam74.py`) üzerinde, 40 000 adım eğitip her 2000 adımda bir değerlendirme yapıyoruz.

### Hiperparametre ayarı: hangi tohumlar kullanıldı?

RL'de ayar, değerlendirme tohumlarını sızdırmamalıdır. İlk denemede tek bir koşu (tohum 0) yaptık; bu, kodun öğrenip öğrenmediğini görmek içindi ve tohum 0 değerlendirme tohumlarından biridir. Sonra ayarları yalnızca **ayar tohumları 10 ve 11** üzerinde seçtik. Dört aday, aynı kodla ama farklı sabitlerle denendi:

| Aday | LR | Hedef güncelleme | ε süresi | Başlama | Batch | Ayar tohumları (son) |
|---|---|---|---|---|---|---|
| A (seçilen) | 5e-4 | 250 | 5000 | 500 | 64 | 500, 500 |
| B | 1e-3 | 1000 | 10000 | 1000 | 64 | 92, 104 |
| C | 2,5e-4 | 500 | 10000 | 1000 | 64 (60 000 adım) | 353, 171 |
| D | 5e-4 | 500 | 5000 | 500 | 128 | 500, 96 |

Aday A, her iki ayar tohumunda da son değerlendirmede 500'e ulaştı (en iyi son sonuç); bu yüzden onu seçtik. Aday D tepe değerde 500'e ulaştı ama son değerlendirmede tohum 11'de 96'da kaldı. Aday seçimi, değerlendirme tohumlarında (0–4) hiç yapılmadı. Ayar betiği `tune74.py` aşağıda; her aday için ayar tohumlarının son ve en yüksek değerlendirme getirilerini yazar.

```python
# -*- coding: utf-8 -*-
"""Bolum 74 - DQN ayar denemesi (ayar tohumlari 10 ve 11).

Kullanim: python tune74.py '{"LR": 0.0005, "HEDEF_GUNCELLE": 250}'
Degerlendirme tohumlari (0-4) bu betikte kullanilmaz.
"""

import json
import sys

import dqn74

cfg = json.loads(sys.argv[1])
for k, v in cfg.items():
    setattr(dqn74, k, v)
son, enb = [], []
for t in (10, 11):
    r = dqn74.calistir(("tam", t))
    son.append(round(r["son"]))
    enb.append(round(max(g for _, g in r["egri"])))
for k, v in cfg.items():
    print("  %s = %s" % (k, v))
print("  son (tohum 10, 11) =", son)
print("  en yuksek (tohum 10, 11) =", enb)
```

Her aday, `tune74.py` ile ayrı bir süreçte çalıştırıldı ve sonuçları birer dosyaya yazıldı; aşağıda dört aday birlikte veriliyor.

```term
  LR = 0.0005
  HEDEF_GUNCELLE = 250
  EPS_SURE = 5000
  BASLAMA = 500
  son (tohum 10, 11) = [500, 500]
  en yuksek (tohum 10, 11) = [500, 500]
  LR = 0.001
  HEDEF_GUNCELLE = 1000
  EPS_SURE = 10000
  BASLAMA = 1000
  son (tohum 10, 11) = [92, 104]
  en yuksek (tohum 10, 11) = [500, 228]
  LR = 0.00025
  HEDEF_GUNCELLE = 500
  EPS_SURE = 10000
  ADIM = 60000
  BASLAMA = 1000
  son (tohum 10, 11) = [353, 171]
  en yuksek (tohum 10, 11) = [500, 216]
  LR = 0.0005
  HEDEF_GUNCELLE = 500
  EPS_SURE = 5000
  BASLAMA = 500
  BATCH = 128
  son (tohum 10, 11) = [500, 96]
  en yuksek (tohum 10, 11) = [500, 224]
```

Son ayarla, `dqn74.py` tam dört ablasyonu beş tohumla çalıştırır. Dört yapı şunlardır: **tam** DQN; **hedef ağ yok** (hedef, tahminle aynı ağdır, yani hareketli bir hedef); **replay yok** (tampon kapasitesi batch boyutuna, yani 64'e eşittir: ajan yalnızca son 64 geçişi görür); **Double DQN**. Her koşu bağımsız bir süreçte, tek iş parçacığıyla çalışır.

```python
# -*- coding: utf-8 -*-
"""Bolum 74 - DQN, sifirdan (PyTorch 2.6.0, CPU).

Bilesenler: dairesel deneyim tamponu (replay), hedef ag (hard update),
Huber kaybi, epsilon takvimi, gradyan kirpma. Double DQN bayragi var.
Ablasyon: hedef ag yok, replay yok (tampon = batch boyutu), Double
DQN.
Ortam: kendi CartPole'umuz (ortam74.py). 5 tohum, 40000 adim.
"""

import os
import sys
import time
import numpy as np
import torch

torch.set_num_threads(4)
import torch.nn as nn
import torch.nn.functional as F
from ortam74 import CartPole

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
BASE = "C:/Users/merty/AppData/Local/Temp/b74"
ADIM = 40000
BATCH = 64
GAMMA = 0.99
LR = 5e-4
HEDEF_GUNCELLE = 250  # hedef agin guncelleme araligi (adim)
EPS_BASLA, EPS_BIT, EPS_SURE = 1.0, 0.05, 5000
BASLAMA = 500  # bu kadar gecis birikince egitime basla
DEGERLENDIR_HER = 2000
TOHUMLAR = [0, 1, 2, 3, 4]


def ag_kur():
    return nn.Sequential(
        nn.Linear(4, 128),
        nn.ReLU(),
        nn.Linear(128, 128),
        nn.ReLU(),
        nn.Linear(128, 2),
    )
```

```python

class Tampon:
    """Dairesel tampon: kapasite dolunca en eski gecis uzerine
    yazilir."""

    def __init__(self, kapasite, rng):
        self.k, self.rng = kapasite, rng
        self.i, self.dolu = 0, 0
        self.s = np.zeros((kapasite, 4), np.float32)
        self.a = np.zeros(kapasite, np.int64)
        self.r = np.zeros(kapasite, np.float32)
        self.s2 = np.zeros((kapasite, 4), np.float32)
        self.d = np.zeros(kapasite, np.float32)

    def ekle(self, s, a, r, s2, d):
        j = self.i
        self.s[j], self.a[j], self.r[j] = s, a, r
        self.s2[j], self.d[j] = s2, d
        self.i = (self.i + 1) % self.k
        self.dolu = min(self.dolu + 1, self.k)

    def ornekle(self, n):
        idx = self.rng.integers(0, self.dolu, size=n)
        return (
            torch.as_tensor(self.s[idx]),
            torch.as_tensor(self.a[idx]),
            torch.as_tensor(self.r[idx]),
            torch.as_tensor(self.s2[idx]),
            torch.as_tensor(self.d[idx]),
        )


def egit_bir_adim(q, hedef, opt, tampon, double):
    s, a, r, s2, d = tampon.ornekle(BATCH)
    with torch.no_grad():
        if double:
            # secim: cevrimici ag; degerlendirme: hedef ag
            a_star = q(s2).argmax(dim=1, keepdim=True)
```

```python
            q2 = hedef(s2).gather(1, a_star).squeeze(1)
        else:
            q2 = hedef(s2).max(dim=1).values
        y = r + GAMMA * (1.0 - d) * q2
    qsa = q(s).gather(1, a.unsqueeze(1)).squeeze(1)
    kayip = F.smooth_l1_loss(qsa, y)  # Huber
    opt.zero_grad()
    kayip.backward()
    nn.utils.clip_grad_norm_(q.parameters(), 10.0)
    opt.step()
    return float(kayip.item())
```

```python

def degerlendir(q, adet, tohum):
    env = CartPole(rng=np.random.default_rng(tohum))
    getiriler = []
    for ep in range(adet):
        s = env.reset(seed=tohum * 1000 + ep)
        G, bitti, kesildi = 0.0, False, False
        while not (bitti or kesildi):
            with torch.no_grad():
                a = int(
                    q(
                        torch.as_tensor(s, dtype=torch.float32)
                    ).argmax()
                )
            s, r, bitti, kesildi = env.step(a)
            G += r
        getiriler.append(G)
    return float(np.mean(getiriler))


def calistir(args):
    yapi, tohum = args
    torch.set_num_threads(4)
    torch.manual_seed(tohum)
    rng = np.random.default_rng(tohum)
    env = CartPole(rng=np.random.default_rng(tohum + 77))
    q = ag_kur()
    hedef = ag_kur()
    hedef.load_state_dict(q.state_dict())
    if yapi == "hedef_yok":
        hedef = q  # ayni ag: hareketli hedef
    kapasite = BATCH if yapi == "replay_yok" else 50000
    tampon = Tampon(kapasite, rng)
    opt = torch.optim.Adam(q.parameters(), lr=LR)
    double = yapi == "double"
    s = env.reset(seed=tohum)
    egri = []
    kayiplar = []
```

```python
    t0 = time.time()
    for adim in range(1, ADIM + 1):
        eps = max(
            EPS_BIT,
            EPS_BASLA - (EPS_BASLA - EPS_BIT) * adim / EPS_SURE,
        )
        if rng.random() < eps:
            a = int(rng.integers(2))
        else:
            with torch.no_grad():
                a = int(
                    q(
                        torch.as_tensor(s, dtype=torch.float32)
                    ).argmax()
                )
        s2, r, bitti, kesildi = env.step(a)
        tampon.ekle(s, a, r, s2, float(bitti))  # kesilme != bitis
        s = s2
        if bitti or kesildi:
            s = env.reset()
        if tampon.dolu >= BASLAMA:
            kayiplar.append(
                egit_bir_adim(q, hedef, opt, tampon, double)
            )
        if yapi != "hedef_yok" and adim % HEDEF_GUNCELLE == 0:
            hedef.load_state_dict(q.state_dict())
        if adim % DEGERLENDIR_HER == 0:
            egri.append((adim, degerlendir(q, 5, 500 + tohum)))
    son = degerlendir(q, 20, 900 + tohum)
    return {
        "yapi": yapi,
        "tohum": tohum,
        "egri": egri,
        "son": son,
        "sure": time.time() - t0,
    }
```

```python

if __name__ == "__main__":
    import json
    import sys

    yapilar = ["tam", "hedef_yok", "replay_yok", "double"]
    kismi = os.path.join(BASE, "dqn_kismi")
    os.makedirs(kismi, exist_ok=True)
    if len(sys.argv) == 3:
        # tek kosu: python dqn74.py <yapi> <tohum>
        yapi, t = sys.argv[1], int(sys.argv[2])
        r = calistir((yapi, t))
        r["egri"] = [[int(a), float(g)] for a, g in r["egri"]]
        with open(
            os.path.join(kismi, "%s_%d.json" % (yapi, t)),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(r, f)
        print(
            "kayit yazildi:",
            yapi,
            t,
            "son=%.1f" % r["son"],
            flush=True,
        )
    else:
        # birlestirme
        sonuclar = []
        for y in yapilar:
            for t in TOHUMLAR:
                with open(
                    os.path.join(kismi, "%s_%d.json" % (y, t)),
                    encoding="utf-8",
                ) as f:
                    sonuclar.append(json.load(f))
        os.makedirs(VERI, exist_ok=True)
        satirlar = ["yapi,adim,ort,sd"]
```

```python
        for y in yapilar:
            R = [z for z in sonuclar if z["yapi"] == y]
            adimlar = [a for a, _ in R[0]["egri"]]
            M = np.array([[g for _, g in z["egri"]] for z in R])
            for i, a in enumerate(adimlar):
                satirlar.append(
                    "%s,%d,%.2f,%.2f"
                    % (y, a, M[:, i].mean(), M[:, i].std(ddof=1))
                )
            son = np.array([z["son"] for z in R])
            print(
                "%-10s ort=%.1f sd=%.1f tohumlar=%s"
                % (
                    y,
                    son.mean(),
                    son.std(ddof=1),
                    np.round(son).astype(int).tolist(),
                )
            )
        with open(
            os.path.join(VERI, "b74_dqn_egri.csv"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write("\n".join(satirlar) + "\n")
        print(
            "sure (ort, sn):",
            round(np.mean([z["sure"] for z in sonuclar]), 1),
        )
```

Betiğin sonucu:

```term
tam        ort=364.7 sd=179.4 tohumlar=[499, 173, 488, 163, 500]
hedef_yok  ort=9.2 sd=0.2 tohumlar=[9, 9, 9, 9, 9]
replay_yok ort=25.5 sd=36.4 tohumlar=[91, 9, 9, 9, 9]
double     ort=366.2 sd=154.1 tohumlar=[121, 390, 490, 500, 330]
sure (ort, sn): 62.6
```

Son değerlendirmeler (20 bölüm, ε = 0, değerlendirme tohumları 900+) şu şekilde: tam DQN 364,7 ± 179,4 (tohumlar: 499, 173, 488, 163, 500); Double DQN 366,2 ± 154,1 (121, 390, 490, 500, 330); hedef ağ yok 9,2 ± 0,2 (beş tohumun hepsi 9 — yani direk düşen çubuk); replay yok 25,5 ± 36,4 (91, 9, 9, 9, 9).

Bu sonuçların üç yorumu var. Birincisi, **hedef ağ** en kritik bileşendir: onu kaldırmak öğrenmeyi tamamen engeller (beş tohumun hepsi 9 adımda düşer). Bu, Baird'de gördüğümüz geri besleme döngüsünün gerçek bir sinir ağında ortaya çıkışıdır. İkincisi, **replay** tek başına da önemlidir ama etkisi tek tohumda kendini gösterdi; dört tohumda çökme vardır, bir tohumda 91 gibi düşük bir öğrenme olur. Üçüncüsü, **Double DQN** ile tam DQN arasındaki fark (366 ve 365) beş tohumla anlamlı değildir; tohumlar arası sapma (154–179) farktan çok büyüktür. Double DQN'in asıl kazancı, değer aşırı tahmininin ölçüldüğü ortamlarda görünür; bu CartPole'da bu kadar belirgin değildir.

Şekil 74.6, dört yapının değerlendirme eğrilerini beş tohumun ortalaması ± 1 sapma olarak gösteriyor. Tam DQN ve Double DQN, yaklaşık 22 000 ile 30 000 adım arasında yükseliyor (tam DQN 223'ten 386'ya, Double DQN 304'ten 486'ya); 30 000 adımdan sonra ise 330–390 düzeyinde dalgalanıyor. Bu dalgalanma, beş tohumdan ikisinin düşük kalmasından kaynaklanır ve son sapmayı açıklar. Hedef ağ yok ve replay yok eğrileri ise hiç değişmiyor: ölçülen değer ilk noktadan itibaren sabit (9,48 ve 25,56). Bu, değerlendirme politikasının ilk ölçümden itibaren hiç değişmediği anlamına gelir; sabit bir eylemle CartPole birkaç adımda devrildiği için bölüm uzunluğu da sabit kalır. Yani bu iki yapıda ağ, tek bir eylemi sürekli üstün gösterecek bir Q yapısına kilitlenmiş ve gerçek bir öğrenme yaşanmamıştır.

![Şekil 74.6: DQN öğrenme eğrileri (kendi CartPole'umuz). Değerlendirme getirisi (ε = 0), 5 tohum; tam DQN ve Double DQN yükselir; hedef ağ yok ve replay yok eğrileri düz ve düşük kalır.](gorseller/b74_dqn_egri.png)

::: dikkat
Bu bölümdeki tüm ayarlar kendi ortamımızda, kendi ölçütümüzle yapıldı. Gerçek bir projede, RL sonuçlarını bir baz çizgi (bir PID, bir kural) ve birkaç tohum olmadan raporlamak, sonuçları sahte bir kesinlikle sunmak olur. Bu yüzden Bölüm 74.15 değerlendirme disiplinine ayrılmıştır.
:::

::: mulakat
1. DQN neden hedef ağa ihtiyaç duyar? Hedef ağ olmadan hangi geri besleme döngüsü oluşur ve bunu Baird'in karşı örneğiyle nasıl ilişkilendirirsin?
2. Replay tamponu neden politika dışı bir veri kaynağıdır? Tamponun boyutu ile öğrenmenin kararlılığı arasında nasıl bir takas vardır?
3. Standart Q hedefi neden değerleri yukarı yanlı tahmin eder? Double DQN bu yanlılığı nasıl azaltır ve neden tamamen ortadan kaldıramaz?
:::

## 74.9 Politika gradyanı: değeri değil politikayı öğrenmek

Şimdiye kadarki yöntemler önce bir değer fonksiyonu öğrenip, sonra politikayı ondan türetiyordu: `π(s) = argmax_a Q(s, a)`. Bu dolaylı yol iki sorun taşır. Birincisi, politika her zaman açgözlüdür; sürekli eylem uzaylarında (bir İHA'nın itki değeri gibi) argmax tanımlı değildir ve ε-açgözlü keşif kaba bir çözümdür. İkincisi, değerdeki küçük bir hata politikada büyük bir değişikliğe yol açabilir. **Politika gradyanı** yöntemleri bu dolaylılığı atlar: politikayı doğrudan `π_θ(a | s)`, bir parametrik fonksiyon olarak yazar ve beklenen getiriyi parametrelerine göre artırır.

Amaç fonksiyonu, bir politikanın beklenen toplam ödülüdür: `J(θ) = E_{τ ~ π_θ}[ G(τ) ]`. Burada `τ = (s_0, a_0, s_1, a_1, ...)` bir yörüngedir ve `G(τ)` onun indirimli toplam ödülüdür. Amaç, `∇_θ J(θ)`'yi bulup gradyan çıkışı yapmaktır. Zor kısım, beklentinin dağılımının `θ`'ya bağlı olmasıdır: ortamın dinamiklerini (`P`) bilmeden bu gradyan nasıl hesaplanır?

### Log-türev hilesi

Yörüngenin olasılığı, politika ve ortamın çarpımıdır:

p_θ(τ) = p(s_0) Π_t [ π_θ(a_t | s_t) P(s_{t+1} | s_t, a_t) ]

Ortamın terimleri (`p(s_0)` ve `P`) `θ`'ya bağlı değildir. Log alıp türev alırsan, yalnızca politika terimleri kalır:

∇_θ log p_θ(τ) = Σ_t ∇_θ log π_θ(a_t | s_t)

Şimdi `∇J`'yi açalım. `J(θ) = ∫ p_θ(τ) G(τ) dτ` olduğu için

∇J = ∫ ∇p_θ(τ) G(τ) dτ = ∫ p_θ(τ) ∇ log p_θ(τ) G(τ) dτ = E_τ[ ∇ log p_θ(τ) · G(τ) ]

Son adım, `∇p = p ∇ log p` özdeşliğinin, yani `∇ log x = (∇x)/x` tanımının doğrudan kullanılmasıdır. Bu "log-türev hilesi" (log-derivative trick) adını buradan alır. Sonucu şöyle yazarız:

∇J(θ) = E_τ [ Σ_t ∇_θ log π_θ(a_t | s_t) · G(τ) ]

Bu ifade, ortamın dinamiklerine hiç ihtiyaç duymaz: gradyanı tahmin etmek için yalnızca ajanın gerçekten izlediği yörüngeleri ve her eylemin `log π` gradyanını kullanırız. Model-serbest politika gradyanının kalbi budur.

### Nedensellik: ödül-öncesi (reward-to-go)

Bu ifadede her `∇ log π(a_t | s_t)` terimi, tüm `G(τ)` ile çarpılır. Ama `t` anındaki bir eylem, `t`'den önce gelen ödüllerin hiçbirini etkileyemez. Bu nedenle gereksiz bir gürültü eklenir. Terimi `G_t = Σ_{k≥t} γ^{k−t} r_{k+1}` (ödül-öncesi) ile değiştirmek, beklentiyi değiştirmeden varyansı düşürür:

∇J(θ) = E_τ [ Σ_t ∇_θ log π_θ(a_t | s_t) · G_t ]

Bu, **REINFORCE** algoritmasının (Williams, 1992, genel bilgi) güncelleme kuralıdır: bir bölüm oyna, her adımın `G_t`'sini hesapla, `θ ← θ + α Σ_t ∇ log π(a_t | s_t) G_t` uygula. Politikanın kaybı, gradyanı bu olarak tanımlanan `−Σ_t log π(a_t | s_t) G_t`'dir. Betikte bunu `kayip_hesapla` ile uyguluyoruz.

### Taban çizgisi (baseline) ve varyans

REINFORCE'un büyük sorunu varyanstır. Bir bölümdeki `G_t` büyük ve değişkense, gradyan kestirimi o kadar gürültülü olur. Bir `b(s_t)` taban çizgisi, yani `s_t`'ye bağlı ama `a_t`'ye bağlı olmayan bir fonksiyon, gradyanı değiştirmez:

E_a [ ∇_θ log π_θ(a | s) · b(s) ] = b(s) Σ_a π_θ(a | s) ∇_θ log π_θ(a | s) = b(s) Σ_a ∇_θ π_θ(a | s) = b(s) ∇_θ 1 = 0

Son eşitlikte `Σ_a π(a | s) = 1` olduğu kullanıldı. Yani `G_t` yerine `G_t − b(s_t)` yazmak beklentiyi değiştirmez ama varyansı azaltabilir. En iyi `b` değeri, durumun beklenen getirisi `V^π(s)`'dir: bu durumda `G_t − V(s_t)` avantajdır (`A(s, a) = Q(s, a) − V(s)`). Kestirimde `V` ayrı bir ağla öğrenilir: bu fikir aktör–eleştirmen yöntemlerinin temelidir.

Bu bölümde taban çizgisi olarak tek bir sabit kullanıyoruz: bir batch'teki tüm getirilerin ortalaması. Bu, `V(s)`'in en kaba kestirimidir (durumdan bağımsız), ama yine de varyansı belirgin biçimde azaltır; ne kadar azalttığını Şekil 74.7 gösterecek.

### Aktör–eleştirmen, avantaj ve GAE

Aktör–eleştirmen (actor–critic) yöntemlerinde iki ağ vardır: **aktör** politikayı (`π_θ`), **eleştirmen** değeri (`V_φ`) öğrenir. Eleştirmen, gradyan kestirimindeki `G_t − b` terimini daha doğru yapar. En basit kestirim, bir adımlık TD hatasıdır: `A_t ≈ δ_t = r_{t+1} + γ V(s_{t+1}) − V(s_t)`. Bu, Bölüm 74.5'teki TD(0) ile aynıdır: düşük varyans, yanlılık. Monte Carlo getirisi `G_t − V(s_t)` ise tam tersidir: yanlılık yok, yüksek varyans.

**Genelleştirilmiş avantaj kestirimi** (GAE, Schulman ve arkadaşları 2016, genel bilgi), bu ikisi arasında bir spektrumdur. `n`-adımlık avantajların `λ` ile üstel ağırlıklı bir karışımını alır:

A_t^GAE(γ, λ) = Σ_{l ≥ 0} (γλ)^l δ_{t+l}

`λ = 0` yalnızca `δ_t` (TD(0)), `λ = 1` ise MC avantajıdır. Pratikte `λ = 0,95` yaygın bir seçimdir ve betikte de bu kullanılır. Hesap, sondan başa doğru bir yinelemeyle yapılır: `A_t = δ_t + γλ A_{t+1}` (bölüm sınırında `A` sıfırlanır). Bu, Bölüm 16'daki DP tablosunun sondan başa dolumuna benzer.

Bu teorinin ne kadar işe yaradığını ölçmek için, `pg74.py` betiğiyle CartPole üzerinde iki REINFORCE eğitimi yaptık: biri çıplak ödül-öncesi getiriyle, diğeri batch ortalamasını taban çizgisi olarak çıkararak. Her iki yöntem beş tohumla, 200 iterasyon boyunca çalıştı; her iterasyonda 10 bölüm toplanıp tek bir gradyan adımı atıldı. Politika, 64 birimli değil, 32 birimli tek gizli katmanlı tanh ağıdır (`ag` işlevi). Bölüm uzunluğu 200 adımla sınırlandığı için getiriler en fazla 200'dür.

Varyans ölçümünde bir ayrıntı var: iterasyon sayısı 200 bırakıldı, ama her 20 iterasyonda bir ölçüm yapıldı ve her ölçümde M = 10 bağımsız batch kullanıldı. İlk planımız her 10 iterasyonda M = 30 batch idi; ancak bu, tek bir koşuyu 15 dakikanın çok üstüne çıkardığı için maliyet nedeniyle küçültüldü. Ölçümün standart sapması M = 10 ile kaba olduğundan, gösterilen değerleri kesin sayılar değil, büyüklük mertebesi olarak okuyun.

```python
# -*- coding: utf-8 -*-
"""Bolum 74 - Politika gradyani: REINFORCE, taban cizgisi ile
varyans azaltma. CartPole (kendi fizigimiz), 5 tohum, 200 iterasyon.

Her 20 iterasyonda: ayni politika uzerinde M = 10 bagimsiz batch icin
gradyan kestiriminin parametre basina varyansi olculur.
"""

import os
import numpy as np
import torch

torch.set_num_threads(4)
import torch.nn as nn
from torch.distributions import Categorical
from ortam74 import CartPole

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
BASE = "C:/Users/merty/AppData/Local/Temp/b74"
ITER, N, M = 200, 10, 10
TOHUMLAR = [0, 1, 2, 3, 4]


def ag():
    return nn.Sequential(
        nn.Linear(4, 32), nn.Tanh(), nn.Linear(32, 2)
    )


def bolum_topla(pol, env, seed_bol):
    """Bir bolum: (log pi listesi, odul listesi)."""
    s = env.reset(seed=seed_bol)
    logps, odulalr = [], []
    bitti = kes = False
    while not (bitti or kes):
        st = torch.as_tensor(s, dtype=torch.float32)
        d = Categorical(logits=pol(st))
        a = d.sample()
        logps.append(d.log_prob(a))
        s, r, bitti, kes = env.step(int(a))
        odulalr.append(r)
    return logps, odulalr
```

```python

def getiri_git(odulalr):
    G, geri = 0.0, []
    for r in reversed(odulalr):
        G = r + G  # gamma = 1 (CartPole, sonlu bolum)
        geri.append(G)
    return list(reversed(geri))


def kayip_hesapla(pol, rng, taban):
    """N bolum topla; kayip = -(1/N) sum_t log pi(a_t|s_t) (G_t - b).
    taban=True ise b, bu batch'teki tum getirilerin ortalamasidir."""
    env = CartPole(rng=rng, max_adim=200)
    tum = []
    for _ in range(N):
        lp, od = bolum_topla(pol, env, int(rng.integers(10**9)))
        tum.append((lp, getiri_git(od)))
    b = (
        float(np.mean([x for _, G in tum for x in G]))
        if taban
        else 0.0
    )
    kayip = 0.0
    for lp, G in tum:
        for lpt, Gt in zip(lp, G):
            kayip = kayip + lpt * (Gt - b)
    return -kayip / N


def batch_gradyani(pol, rng, taban):
    pol.zero_grad()
    kayip_hesapla(pol, rng, taban).backward()
    return np.concatenate(
        [p.grad.detach().numpy().ravel() for p in pol.parameters()]
    )


def varyans_olc(pol, seed, taban):
```

```python
    rng = np.random.default_rng(seed)
    gs = []
    for _ in range(M):
        g = batch_gradyani(pol, rng, taban)
        gs.append(g)
    G = np.array(gs)
    return G.var(axis=0, ddof=1).mean(), np.linalg.norm(
        G.mean(axis=0)
    )
```

```python

def kos(args):
    tohum, taban = args
    torch.set_num_threads(4)
    torch.manual_seed(tohum)
    pol = ag()
    opt = torch.optim.Adam(pol.parameters(), lr=1e-2)
    rng = np.random.default_rng(tohum + 99)
    kayit = []
    for it in range(ITER + 1):
        if it % 50 == 0:
            print(
                "tohum", tohum, "taban", taban, "iter", it, flush=True
            )
        if it % 20 == 0:
            v, nrm = varyans_olc(pol, 5000 + it, taban)
            kayit.append((it, v, nrm))
        if it == ITER:
            break
        # tek gradyan adimi (N bolum)
        opt.zero_grad()
        kayip_hesapla(pol, rng, taban).backward()
        opt.step()
    return tohum, taban, kayit


if __name__ == "__main__":
    import json
    import sys

    kismi = os.path.join(BASE, "pg_kismi")
    os.makedirs(kismi, exist_ok=True)
    if len(sys.argv) == 3:
        # tek kosu: python pg74.py <tohum> <taban: 0|1>
        t, b = int(sys.argv[1]), bool(int(sys.argv[2]))
        _, _, kayit = kos((t, b))
        ad = "var" if b else "yok"
        with open(
```

```python
            os.path.join(kismi, "%s_%d.json" % (ad, t)),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                [[int(i), float(v), float(n)] for i, v, n in kayit], f
            )
        print("kayit yazildi:", t, b, flush=True)
    else:
        # birlestirme: 10 kismi kosunun ortalamasi
        sat = ["iter,yontem,var_ort,var_sd,grad_norm_ort"]
        for ad, kok in (("taban_yok", "yok"), ("taban_var", "var")):
            R = []
            for t in TOHUMLAR:
                with open(
                    os.path.join(kismi, "%s_%d.json" % (kok, t)),
                    encoding="utf-8",
                ) as f:
                    R.append(json.load(f))
            for i in range(len(R[0])):
                vals = np.array([r[i][1] for r in R])
                nrm = np.array([r[i][2] for r in R])
                sat.append(
                    "%d,%s,%.4e,%.4e,%.4e"
                    % (
                        R[0][i][0],
                        ad,
                        vals.mean(),
                        vals.std(ddof=1),
                        nrm.mean(),
                    )
                )
            it0 = np.mean([r[0][1] for r in R])
            it200 = np.mean([r[-1][1] for r in R])
            print(
                "%-10s varyans: it0=%.3e it200=%.3e"
                % (ad, it0, it200),
                flush=True,
            )
        os.makedirs(VERI, exist_ok=True)
        with open(
            os.path.join(VERI, "b74_pg_varyans.csv"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write("\n".join(sat) + "\n")
```

Betiğin çıktısı:

```term
taban_yok  varyans: it0=2.917e+00 it200=4.399e+03
taban_var  varyans: it0=1.886e+00 it200=9.590e+02
```

Sonuçlar iki şeyi birlikte gösteriyor. Birincisi, taban çizgisi gradyan kestiriminin varyansını belirgin biçimde düşürüyor: 0. iterasyonda 2,92 yerine 1,89 (yaklaşık 1,5 kat), 40. iterasyonda 2211 yerine 877 (2,5 kat), 200. iterasyonda 4399 yerine 959 (4,6 kat). İkincisi, mutlak varyans her iki yöntemde de öğrenme ilerledikçe büyüyor. Bunun nedeni, politika keskinleştikçe ve getiriler 20 civarından 200'e çıktıkça gradyanın ölçeğinin büyümesidir; varyans bu ölçeğin karesi ile orantılı büyür. Bu yüzden asıl ölçü, mutlak değerden çok iki yöntem arasındaki orandır ve taban çizgisi, öğrenmenin geç döneminde daha büyük bir kazanç sağlıyor.

Şekil 74.7, bu iki eğriyi 5 tohumun ortalaması ± 1 sapma olarak gösteriyor. Ölçek logaritmiktir; taban çizgili eğri her noktada daha alttadır, ama aradaki farkın iterasyonla büyüdüğünü de görürsünüz.

![Şekil 74.7: REINFORCE'ta gradyan kestiriminin parametre başına varyansı (5 tohum, M = 10 batch, her 20 iterasyonda). Taban çizgisiz (üst) ve batch ortalamalı taban çizgisi ile (alt). Logaritmik ölçek.](gorseller/b74_reinforce_varyans.png)

Bu deney, öğrenme eğrisini (bölüm getirisinin zamanla değişimi) raporlamıyor; yalnızca gradyan kestiriminin kalitesini ölçüyor. Bir yöntemin öğrenme hızı ayrı bir ölçüttür ve varyansın azalması, bu anlamda otomatik olarak daha hızlı öğrenme anlamına gelmez; ancak aynı adım sayısında daha az gürültülü adımlar attığını gösterir.

::: not
REINFORCE, bu bölümde yalnızca varyans karşılaştırması için kullanıldı. Aynı politikanın öğrenme eğrisini ölçmek için bir sonraki adım, bölüm getirisini her iterasyonda kaydetmek olurdu; bunu bilinçli olarak yapmadık, çünkü PPO bölümünde aynı ortamda (CartPole) öğrenme eğrisini zaten ölçtük.
:::

::: mulakat
1. Taban çizgisi, politika gradyanının yanlılığını neden değiştirmez? Bunu `Σ_a ∇π(a|s) = 0` özdeşliğiyle açıkla.
2. REINFORCE'ta varyansın öğrenme sırasında büyümesinin nedenini, getiri ölçeği ve politika keskinliği üzerinden açıkla. Bu, taban çizgisinin ne zaman en çok yardımcı olacağı hakkında ne söyler?
3. Gradyan kestiriminin varyansını ölçerken M (batch sayısı) ile standart sapma tahmininin kalitesi arasındaki ilişki nedir? M = 10 ile ne kadar güvenilir bir sapma elde edilir?
:::

## 74.10 PPO: kırpılmış vekil amaç

Politika gradyanı bir sorunu daha taşır: adım boyu. Gradyan yönü doğru olsa bile, bir adım politikayı çok büyük değiştirirse, toplanan veri artık yeni politikaya ait değildir ve öğrenme çöker. **Proksimal politika optimizasyonu** (PPO, Schulman ve arkadaşları 2017, genel bilgi), politikayı bir güven bölgesi içinde tutmanın basit bir yolunu verir.

Eski politika `π_old`'a göre oran `r_t(θ) = π_θ(a_t | s_t) / π_old(a_t | s_t)` olsun. Doğrudan vekil amaç (surrogate objective) `E[ r_t(θ) A_t ]`'dir; oran `1`'den uzaklaştıkça bu amaç da sınırsız büyüyebilir. PPO bunu şöyle kırpar:

L^CLIP(θ) = E_t [ min( r_t(θ) A_t , clip(r_t(θ), 1 − ε, 1 + ε) A_t ) ]

`ε` tipik olarak 0,2'dir. Kırpmanın etkisi, avantajın işaretine göre değişir (Şekil 74.8):

- `A > 0` (iyi bir eylem): oran `1 + ε`'nin üstüne çıkarsa amaç sabitlenir; yani eylem olasılığını bu eşikten fazla artırmanın bir getirisi yoktur. Gradyan orada sıfırdır.
- `A < 0` (kötü bir eylem): oran `1 − ε`'nın altına inerse amaç sabitlenir; eylem olasılığını bu eşikten fazla düşürmenin bir getirisi yoktur. Gradyan orada da sıfırdır.

Bu nedenle minimum, kötü yönde bir adımı cezalandırır ama iyi yönde bir adımı aşırıya kaçırmaz. Minimum almak önemlidir: kırpma, amacı yalnızca yukarıdan değil, iyi yönde aşırı adımda da sınırlar. Bu minimum sayesinde vekil amaç, gerçek amacın alttan bir sınırıdır (bu, güven bölgesi yöntemlerinin temel fikridir).

PPO'nun tam kaybı üç parçadan oluşur: vekil amaç (maksimize edilir), değer kaybı `c_v (V_φ(s_t) − G_t)²` ve entropi bonusu `c_e H(π_θ(· | s_t))`. Entropi bonusu, politikanın erken çökmesini önler: ajan, tek bir eylemde kilitlenmek yerine seçeneklerini açık tutar. Bu bölümün deneylerinde entropi katsayısını `c_e = 0` tuttuk; böylece kırpmanın ve GAE'nin etkisini entropi teriminden ayırarak ölçebildik. Entropi bonusu kodda bir parametre olarak duruyor. Her toplanan veri bloğu üzerinde `K` epoch ve küçük mini-batch'lerle birden çok gradyan adımı atılır; kırpma, bu tekrarların politikayı çok uzaklaştırmasını önler.

Şekil 74.8, `A > 0` ve `A < 0` için vekil amacı oranın fonksiyonu olarak gösteriyor. Noktalı çizgi kırpılmamış `r·A`, kalın çizgi kırpılmış minimumdur. Dikey çizgiler `1 ± ε` sınırlarıdır. Kalın çizginin düz kısımlarında gradyan sıfırdır.

![Şekil 74.8: PPO kırpılmış vekil amacı. Sol: A > 0; oran 1 + ε'yi geçtikten sonra amaç sabittir. Sağ: A < 0; oran 1 − ε'nın altına indikten sonra amaç sabittir.](gorseller/b74_ppo_kirpma.png)

::: ipucu
Kırpma, bir "güven bölgesi" değil bir "güven eşiğidir". Gerçek bir güven bölgesi (TRPO) bir KL kısıtı ve ikinci dereceden bir optimizasyon gerektirir; PPO bu karmaşıklığı yalnızca bir min ve clip ile yaklaşık olarak sağlar. Bu, PPO'yu hem basit hem de sağlam kılar.
:::

::: mulakat
1. Politika gradyanı teoremini log-türev hilesiyle türet. Hangi adımda ortamın dinamiklerinin gradyanının neden sıfır olduğunu kullandın?
2. Taban çizgisi beklentiyi değiştirmez, ama varyansı değiştirebilir. Bunu `Σ_a ∇π(a|s) = 0` özdeşliğiyle açıkla.
3. PPO neden vekil amacın minimumunu alır, neden yalnızca `r·A`'yı kırpmaz? İki tarafın da sınırlandığı bir örnek ver.
:::

## 74.11 PPO'yu sıfırdan yazmak ve CartPole'da eğitmek

Bölüm 74.10'da anlattığımız PPO'nun tüm parçaları, aşağıdaki `ppo74.py` dosyasında bir arada. Yazarken dikkat edeceğin üç nokta var. Birincisi, veri toplama ve güncelleme ayrı döngülerdir: önce `T = 1024` adımlık bir blok toplanır, sonra bu blok üzerinde `K = 4` epoch boyunca mini-batch güncellemeleri yapılır. İkincisi, GAE sondan başa bir yinelemeyle hesaplanır ve bölüm sınırlarında (hem sonlanma hem kesilme için) bastırılır. Üçüncüsü, eylem dağılımı ayrıktır (`Categorical`) ya da sürekli (`Normal`, durumdan bağımsız `log_std` ile). Ayrık durumda CartPole'un iki eylemi, sürekli durumda İHA'nın itki sinyali bu iki dağılımdan birini kullanır.

Kırpma fonksiyonu, `oran = exp(lp − LP[b])` ile eski log olasılıktan yeni log olasılığa geçer. Bu, Bölüm 74.9'daki log-türev hilesinin pratik karşılığıdır: oran, log olasılıkların farkının üstelidir ve bu yüzden kod hiçbir yerde doğrudan bölme yapmaz.

```python
# -*- coding: utf-8 -*-
"""Bolum 74 - PPO, sifirdan (PyTorch 2.6.0, CPU).

Kirpilmis vekil amac (clip), GAE (lambda), birden cok epoch mini-
batch,
entropi bonusu, deger kaybi. Ayrik eylemde Categorical, surekli
eylemde
durumdan bagimsiz log_std ile Gauss politikasi (eylem [-1,1]'e
kirpilir).
"""

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Categorical, Normal


def mlp(giris, cikis):
    return nn.Sequential(
        nn.Linear(giris, 64),
        nn.Tanh(),
        nn.Linear(64, 64),
        nn.Tanh(),
        nn.Linear(64, cikis),
    )


class Politika(nn.Module):
    def __init__(self, obs_dim, act_dim, ayrik):
        super().__init__()
        self.ayrik = ayrik
        self.aktor = mlp(obs_dim, act_dim)
        self.elestirmen = mlp(obs_dim, 1)
        if not ayrik:
            self.log_std = nn.Parameter(torch.full((act_dim,), -0.5))

    def dagilim(self, s):
        mu = self.aktor(s)
        if self.ayrik:
            return Categorical(logits=mu)
        return Normal(mu, self.log_std.exp())
```

```python
    def deger(self, s):
        return self.elestirmen(s).squeeze(-1)


def gae(r, v, v_son, term, done, gamma, lam):
    """Genellestirilmis avantaj kestirimi.
    delta_t = r_t + gamma (1 - term_t) V(s_{t+1}) - V(s_t)
    A_t = delta_t + gamma lam (1 - done_t) A_{t+1}"""
    T = len(r)
    adv = np.zeros(T, dtype=np.float32)
    son = 0.0
    for t in reversed(range(T)):
        delta = r[t] + gamma * (1.0 - term[t]) * v_son[t] - v[t]
        son = delta + gamma * lam * (1.0 - done[t]) * son
        adv[t] = son
    return adv, adv + v


def ppo_egit(
    ortam_fn,
    obs_dim,
    act_dim,
    ayrik,
    toplam_adim,
    seed,
    eval_fn=None,
    eval_her=10000,
    T=1024,
    K=4,
    mb=64,
    lr=3e-4,
    gamma=0.99,
    lam=0.95,
    eps=0.2,
    c_v=0.5,
    c_ent=0.0,
    kirp=0.5,
):
```

```python
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    pol = Politika(obs_dim, act_dim, ayrik)
    opt = torch.optim.Adam(pol.parameters(), lr=lr)
    env = ortam_fn(seed)
    s = env.reset()
    adim, egri = 0, []
    while adim < toplam_adim:
        obs, nxt, acts, logps, rews, vals = [], [], [], [], [], []
        terms, dones = [], []
        for _ in range(T):
            st = torch.as_tensor(s, dtype=torch.float32)
            with torch.no_grad():
                d = pol.dagilim(st)
                a = d.sample()
                lp = d.log_prob(a)
                if not ayrik:
                    lp = lp.sum()
            ev = a.item() if ayrik else a.numpy()
            s2, r, term, trunc = env.step_ppo(ev)
            obs.append(s)
            nxt.append(s2)
            acts.append(a.numpy())
            logps.append(float(lp))
            rews.append(r)
            terms.append(float(term))
            dones.append(float(term or trunc))
            adim += 1
            s = s2
            if term or trunc:
                s = env.reset()
        O = torch.as_tensor(np.array(obs), dtype=torch.float32)
        N = torch.as_tensor(np.array(nxt), dtype=torch.float32)
        with torch.no_grad():
            V = pol.deger(O).numpy()
            Vn = pol.deger(N).numpy()
        adv, ret = gae(
            np.array(rews, np.float32),
```

```python
            V,
            Vn,
            np.array(terms),
            np.array(dones),
            gamma,
            lam,
        )
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        A = torch.as_tensor(np.array(acts))
        LP = torch.as_tensor(np.array(logps), dtype=torch.float32)
        ADV = torch.as_tensor(adv)
        RET = torch.as_tensor(ret)
        for _ in range(K):
            idx = rng.permutation(T)
            for j in range(0, T, mb):
                b = idx[j : j + mb]
                d = pol.dagilim(O[b])
                if ayrik:
                    lp = d.log_prob(A[b].long())
                else:
                    lp = d.log_prob(A[b]).sum(-1)
                oran = torch.exp(lp - LP[b])
                s1 = oran * ADV[b]
                s2_ = torch.clamp(oran, 1 - eps, 1 + eps) * ADV[b]
                kayip_pi = -torch.min(s1, s2_).mean()
                kayip_v = (pol.deger(O[b]) - RET[b]).pow(2).mean()
                ent = d.entropy()
                ent = ent if ayrik else ent.sum(-1)
                kayip = kayip_pi + c_v * kayip_v - c_ent * ent.mean()
                opt.zero_grad()
                kayip.backward()
                nn.utils.clip_grad_norm_(pol.parameters(), kirp)
                opt.step()
        if eval_fn is not None and (adim // eval_her) > (
            (adim - T) // eval_her
        ):
            egri.append((adim, eval_fn(pol)))
    return pol, egri
```

```python

def acgozlu_eylem(pol, s, ayrik):
    with torch.no_grad():
        st = torch.as_tensor(s, dtype=torch.float32)
        mu = pol.aktor(st)
        if ayrik:
            return int(mu.argmax())
        return np.clip(mu.numpy(), -1.0, 1.0)
```

Bir CartPole (Barto, Sutton, Anderson 1983 fiziği, `ortam74.py`) deneyi, `cartpole_ppo74.py` ile yapıldı. Her tohum, 100 000 ortam adımı boyunca eğitildi ve her 10 000 adımda bir, ayrı tohumlu (`700000+`) 10 bölümde greedy (argmax) politika değerlendirildi. Eğitim, `ProcessPoolExecutor` ile dört süreçte paralel çalıştı.

```python
# -*- coding: utf-8 -*-
"""Bolum 74 - CartPole'da PPO (kendi fizigimiz). 5 tohum, 100000 adim.
Degerlendirme: ayri tohumlu 10 bolum, greedy (argmax) politika."""

import os
import numpy as np
import torch

torch.set_num_threads(2)  # en fazla 2 is parcacigi
from concurrent.futures import ProcessPoolExecutor
from ortam74 import CartPole
from ppo74 import ppo_egit, acgozlu_eylem

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
TOHUMLAR = [0, 1, 2, 3, 4]
TOPLAM = 100000


class KartWrap:
    def __init__(self, seed):
        self.env = CartPole(
            rng=np.random.default_rng(seed), max_adim=500
        )
        self.seed = seed
        self.sayac = 0

    def reset(self):
        self.sayac += 1
        return self.env.reset(seed=self.seed * 100000 + self.sayac)

    def step_ppo(self, a):
        s2, r, bitti, kesildi = self.env.step(int(a))
        return s2, r, bitti, kesildi and not bitti


def degerlendir(pol, adet=10):
    G = []
    for ep in range(adet):
```

```python
        env = CartPole(rng=np.random.default_rng(0), max_adim=500)
        s = env.reset(seed=700000 + ep)
        g, bitti, kes = 0.0, False, False
        while not (bitti or kes):
            a = acgozlu_eylem(pol, s, True)
            s, r, bitti, kes = env.step(a)
            g += r
        G.append(g)
    return float(np.mean(G))
```

```python

def kos(tohum):
    torch.set_num_threads(2)
    pol, egri = ppo_egit(
        lambda sd: KartWrap(sd),
        4,
        2,
        True,
        TOPLAM,
        tohum,
        eval_fn=degerlendir,
        eval_her=10000,
    )
    return tohum, egri


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=2) as ex:
        sonuc = list(ex.map(kos, TOHUMLAR))
    os.makedirs(VERI, exist_ok=True)
    satirlar = ["adim,ort,sd"]
    adimlar = [a for a, _ in sonuc[0][1]]
    M = np.array([[g for _, g in e] for _, e in sonuc])
    for i, a in enumerate(adimlar):
        satirlar.append(
            "%d,%.2f,%.2f" % (a, M[:, i].mean(), M[:, i].std(ddof=1))
        )
    with open(
        os.path.join(VERI, "b74_cartpole_ppo.csv"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    son = M[:, -1]
    print("PPO CartPole son (%d adim):" % TOPLAM)
    print(
        "  ort=%.1f sd=%.1f tohumlar=%s"
        % (son.mean(), son.std(ddof=1), son.round().tolist())
    )
    print(
        "egri (ort):", np.round(M.mean(axis=0)).astype(int).tolist()
    )
```

Betiğin sonucu:

```term
PPO CartPole son (100000 adim):
  ort=500.0 sd=0.0 tohumlar=[500.0, 500.0, 500.0, 500.0, 500.0]
egri (ort): [419, 361, 402, 428, 390, 434, 486, 442, 447, 500]
```

Beş tohumun hepsi 100 000 adımdan sonra 500'e (CartPole'un tavanı) ulaştı; sapma sıfır. Ortalama eğri, 10 000 adımda 419 ± 87 ile başlıyor, 20 000 adımda 361 ± 120'ye düşüp yeniden yükseliyor, 70 000 adımdan sonra 486 ± 32 ile yükselmeye devam ediyor ve 100 000'de 500'e ulaşıyor. Bu eğri, PPO'nun tipik davranışıdır: politika kısa süreli bir gerileme yaşayabilir (olası nedenlerden biri, her blokta veri dağılımının değişmesidir; kırpma bir adımı sınırlar ama bloklar arası dalgalanmayı tamamen önlemez), ama genel yön yukarıdır. Dikkat çekici olan, 10 000 adımda bile ortalama getirinin 419 olmasıdır; CartPole, dinamik olarak kolay bir ortamdır ve bu bölümde amaç, PPO'nun bileşenlerini kendi kodumuzda doğrulamaktır, bir kıyas yapmak değildir.

Bu sonucun bir sınırı var: CartPole'da 500 tavandır ve tavan doyduğunda yöntemler arasındaki farkı görmek zordur. Bu yüzden asıl sınama, İHA ortamında, sürekli eylemle ve bir baz çizgiyle yapıldı (Bölüm 74.12–74.13). Ayrıca Bölüm 74.8'deki DQN ile bu CartPole'da yaklaşık 365 (±179) değerine ulaşmıştık; PPO ise 100 000 adımda tavana ulaştı. Bu bir kıyas sayılmaz, çünkü DQN'in adım bütçesi (40 000) ve hiperparametreleri farklıdır; yine de iki yöntemin bu kolay ortamdaki davranışını birlikte okumak faydalıdır.

Şekil 74.8, kırpmanın etkisini görselleştirir; PPO'nun ortalama eğrisi ise yukarıdaki çıktıda verildi. Kırpma, bir politikanın tek bir güncellemede ne kadar değişebileceğini sınırlar; eğitim, bu sınırın altında kaldıkça kararlıdır.

::: not
Betikteki değerlendirme `degerlendir` fonksiyonu, eğitim sırasındaki stokastik politikayı değil argmax politikasını kullanır. Eğitim getirisi (stokastik) ile değerlendirme getirisi (açgözlü) farklı olabilir; raporda hangisinin verildiği her zaman belirtilmelidir.
:::

::: mulakat
1. PPO'da oran `exp(lp − LP_eski)` olarak hesaplanır. Bu neden log uzayında yapılır ve bu, sayısal kararlılığı nasıl etkiler?
2. Eğitim sırasında PPO'nun kısa süreli bir gerileme yaşamasının olası nedenleri nelerdir? Bu gerilemeyi nasıl ayırt edersin?
3. Bir ajanı tek bir ortam üzerinde 500'de doygunluğa ulaştırmak neden tek başına bir yöntemin üstünlüğünü kanıtlamaz?
:::

## 74.12 İHA irtifa tutma: ortam, PID ve PPO

Bu bölümün asıl sınaması, savunma sanayiine yakın bir problemde yapılır: bir İHA'nın irtifasını rüzgâra ve kütle değişimine karşı tutmak. Gerçek bir uçağın dinamiği çok karmaşıktır; burada 1B bir modelle başlıyoruz. Model, `ortam74.py`'deki `IhaIrtifa` sınıfıdır ve şu denklemlere dayanır (ileri Euler, `dt = 0,05 s`):

a = twr · g · s / kütle − g − k_d · v + w(t)
v ← v + dt · a,  h ← h + dt · v

Burada `h` irtifa, `v` dikey hız, `s ∈ [0, 1]` itki (gaz) oranı, `twr` maksimum itki/ağırlık oranı, `k_d` doğrusal sürükleme katsayısı ve `w(t)` rüzgârın ivme olarak etkisidir. Rüzgâr, bir sinüs ve bir basamak bileşeninden oluşur: `w(t) = ruzgar · (0,8 sin(2πt/8) + 0,5 · [6 ≤ t < 10])`. Nominal değerler `kütle = 1`, `k_d = 0,3`, `twr = 2`, `ruzgar = 1` olarak alındı. Bu durumda hover itkisi `s_h = kütle / twr = 0,5`'tir: yani gazın yarısında uçak yerinde durur.

Bu basit modelin üç özelliği önemlidir. Birincisi, **itki sınırlıdır**: `s` 0 ile 1 arasındadır, dolayısıyla ulaşılabilir ivme aralığı sınırlıdır. İkincisi, **zemin bir sınırdır**: `h ≤ 0` olduğunda uçak düşmüştür ve bölüm `−100` cezasıyla biter. Üçüncüsü, **rüzgâr bilinmeyen bir bozucudur**: kontrolcü `w(t)`'yi doğrudan görmez, yalnızca irtifa ve hız üzerinden dolaylı olarak hisseder.

Gözlem üç sayıdan oluşur: hata `e = (h − h_ref)/5`, hız `v/2` ve hatanın integrali `I/50`. Integral bileşeni bilinçli bir seçimdir. Bir politika ağı, bir PID'nin integral terimi gibi geçmişi kendi başına saklamaz; kütle değişiminde sürekli bir hata kalmasının bir nedeni de budur. Integral'i gözleme koyarak politikanın da bu bilgiyi kullanabilmesini sağladık. Eylem, `[−1, 1]` aralığında bir Gauss örneği olarak üretilir ve ortama `s = (u + 1)/2` olarak iletilir.

Ödül, bölümde `e² + 0,1 s²` cezasıdır ve bu, ortamın ham ödülüdür. Eğitimde kullanılan ödül ise Bölüm 74.14'te açıklanan sınırlı bir biçimdir: `0,04 · (25 − min(e², 25) − 0,1 s²)`, yere düşmede ise sıfır. Başarı ölçütü ödülden bağımsızdır: bir bölümün **başarılı** sayılması için zemine düşmemesi ve son 10 saniyede `max|e| ≤ 1 m` olması gerekir. Bu ölçüt, eğitim ödülünün tasarımına bağlı değildir ve tüm karşılaştırmalarda aynı kullanılır.

### Kontrolcüler

**PID taban çizgisi.** Denetleyici `s = s_h − K_p e − K_i I − K_d v` biçimindedir; `I`, `e`'nin zaman integralidir ve ±20 ile sınırlandırılır (basit bir anti-windup). Kazançlar, `K_p ∈ {0,05; 0,1; 0,2; 0,4}`, `K_i ∈ {0; 0,01; 0,02; 0,05}` ve `K_d ∈ {0,1; 0,2; 0,4; 0,8}` ızgarasında, **ayar tohumları 100–109** üzerinde ortalama maliyetle (`e² + 0,1 s²` ortalaması ve düşme cezası) seçildi. Değerlendirme tohumları (3000+) kullanılmadı. Seçilen kazanç `K_p = 0,4`, `K_i = 0`, `K_d = 0,1`'dir. Bu seçim dürüsttür ama önemli bir not içerir: nominal ortamda `K_i = 0` yeterince iyi çalıştığı için ızgara bunu seçti, oysa kütle değiştiğinde integral terimsiz bir PID'nin kalıcı bir hatası olacaktır. Bu, tam olarak alan kaymasının sınadığı şeydir; 74.13'te integral terimli bir PID ile de karşılaştıracağız.

**PPO.** Politika ve değer ağları 64–64 `tanh` katmanlıdır. Eğitim, `ppo74.py` ile 200 000 adım sürer; `T = 1024`, `K = 4`, mini-batch 64, öğrenme oranı `3·10⁻⁴`, `γ = 0,99`, `λ = 0,95`, `ε = 0,2`, değer katsayısı `0,5`, entropi katsayısı `0` ve gradyan kırpma `0,5`. İki eğitim rejimi var: **nominal** (her bölümde nominal parametreler) ve **alan rastgeleleştirme (DR)** (her bölümde kütle `U(0,8; 1,25)`, `k_d ∈ U(0,1; 0,6)`, `twr ∈ U(1,8; 2,2)`, `ruzgar ∈ U(0; 1,8)`). Her rejim beş tohumla eğitildi. Değerlendirme, her eğitim tohumunun politikasıyla 100 bölümde (tohum 3000–3099) yapıldı.

**Alan kayması taraması.** Kayma şiddeti `α` ile parametreler birlikte değişir: `kütle = 1 + 0,5α`, `k_d = 0,3 + 0,5α`, `twr = 2 − 0,4α`, `ruzgar = 1 + α`. `α = 0`, nominal; `α = 1`, DR aralığının dışında; `α` 0,25 adımlarla 0'dan 1'e tarandı. Bu, RL'nin "eğitim ailesinin içinde" ve "dışında" ne yaptığını görmek için bir ölçektir.

Aşağıdaki betik `iha74.py`, PID ayarını, iki PPO eğitimini, kayma taramasını, güvenlik kalkanının etkisini ve bir yörünge kaydını tek bir yerde yapar. Kalkanın tanımı da bu dosyadadır: nominal modelle bir adım ileriye bakar; bir sonraki irtifa `h_min = 2 m`'nin altına inecekse itkiyi en az gereken değere kaldırır.

```python
# -*- coding: utf-8 -*-
"""Bolum 74 - IHA irtifa tutma: PID taban cizgisi, PPO, alan
rastgelelestirme (domain randomization), guvenlik kalkani.

Ayarlar (degistirmeyin, ortam74.IhaIrtifa ile birebir):
  nominal: kutle 1.0, surukleme kd 0.3, itki/agirlik twr 2.0, ruzgar
  1.0
Basari: zemine dusmeme VE son 10 saniyede max|e| <= 1.0 m.
Ayarlama (PID kazancı, eğitim sürümü): tohum 100-109.
Degerlendirme: tohum 3000+ (100 bolum / kontrolcu / alfa); PPO icin 5
egitim tohumu.
"""

import os
import sys
import numpy as np
import torch
from concurrent.futures import ProcessPoolExecutor
from ortam74 import IhaIrtifa
from ppo74 import ppo_egit, acgozlu_eylem, Politika

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
MODEL = "C:/Users/merty/AppData/Local/Temp/b74/model"
NOM = dict(kutle=1.0, kd=0.3, twr=2.0, ruzgar=1.0)
DT, HREF, T = 0.05, 10.0, 400
TOHUMLAR = [0, 1, 2, 3, 4]
RODUL_OLCEK = 0.04
EMAX = 25.0
DR_ARALIK = dict(
    kutle=(0.8, 1.25),
    kd=(0.1, 0.6),
    twr=(1.8, 2.2),
    ruzgar=(0.0, 1.8),
)


def alfa_parametre(alfa):
    """Alan kaymasi: alfa=0 nominal, alfa=1 DR araliginin disinda."""
    return dict(
        kutle=1 + 0.5 * alfa,
        kd=0.3 + 0.5 * alfa,
        twr=2.0 - 0.4 * alfa,
        ruzgar=1.0 + alfa,
    )
```

```python

def gozlem(env, I):
    e = env.h - env.h_ref
    return np.array(
        [e / 5.0, env.v / 2.0, I / 50.0], dtype=np.float32
    )


class PID:
    def __init__(self, kp, ki, kd, s_h=0.5):
        self.kp, self.ki, self.kd, self.s_h = kp, ki, kd, s_h

    def reset(self):
        self.I = 0.0

    def act(self, env):
        e = env.h - env.h_ref
        self.I = float(np.clip(self.I + e * DT, -20.0, 20.0))
        s = (
            self.s_h
            - self.kp * e
            - self.ki * self.I
            - self.kd * env.v
        )
        return 2.0 * min(max(s, 0.0), 1.0) - 1.0


class PpoKontrol:
    def __init__(self, pol):
        self.pol = pol

    def reset(self):
        self.I = 0.0

    def act(self, env):
        self.I += (env.h - env.h_ref) * DT
        o = gozlem(env, self.I)
        return float(
            np.clip(acgozlu_eylem(self.pol, o, False)[0], -1, 1)
        )
```

```python

def kalkan(env, s_cmd, h_min=2.0):
    """Tek adimlik ileri bakis: nominal modelle bir sonraki irtifa
    h_min'in altina inecekse itkiyi en az gereken degere kaldir.
    Model uyumsuzlugu kalkanin bilmedigi bir hataya neden olabilir;
    sinirlilik budur."""
    m, kd, twr, g = 1.0, 0.3, 2.0, IhaIrtifa.G
    h, v = env.h, env.v
    s_min = (
        (h_min - h - DT * v + DT * DT * (g + kd * v))
        * m
        / (DT * DT * twr * g)
    )
    s_saf = min(max(max(s_cmd, s_min), 0.0), 1.0)
    return s_saf, s_saf > s_cmd + 1e-12


class IhaWrap:
    """Egitim ortami: PPO arayuzu (reset, step_ppo)."""

    def __init__(self, seed, dr):
        self.seed, self.dr = seed, dr
        self.rng = np.random.default_rng(seed + 555)
        self.env = IhaIrtifa(rng=np.random.default_rng(seed), **NOM)
        self.sayac = 0

    def reset(self):
        self.sayac += 1
        if self.dr:
            p = {
                k: self.rng.uniform(*DR_ARALIK[k]) for k in DR_ARALIK
            }
        else:
            p = NOM
        for k, v in p.items():
            setattr(self.env, k, float(v))
        self.env.reset(seed=self.seed * 100000 + self.sayac)
        self.I = (self.env.h - self.env.h_ref) * DT
        return gozlem(self.env, self.I)
```

```python
    def step_ppo(self, a):
        u = float(np.clip(a[0], -1.0, 1.0))
        _, _, yere, bitti, s = self.env.step(u)
        self.I += (self.env.h - self.env.h_ref) * DT
        e = self.env.h - self.env.h_ref
        # Egitim odulu: hayatta kalma tabani - sinirli sapma - efor.
        # Yere carpmada taban kazanilmaz (ceza ayrica yok): sinirsiz
        # sapma cezasi yerine tavan (EMAX) kullanilir; bkz. Bolum 74
        # metni.
        r = (
            0.0
            if yere
            else RODUL_OLCEK * (EMAX - min(e * e, EMAX) - 0.1 * s * s)
        )
        return gozlem(self.env, self.I), r, yere, bitti and not yere


def olc_bolum(kontrol, params, seed, shield=False, kayit=False):
    """Tek bolum: basari, RMS, IAE, efor, kalkan mudahale sayisi."""
    env = IhaIrtifa(rng=np.random.default_rng(seed), **params)
    env.reset(seed=seed)
    kontrol.reset()
    es, ss, ws, hs = [], [], [], []
    mudahale, yere = 0, False
    while True:
        u = kontrol.act(env)
        if shield:
            s_saf, m = kalkan(env, (u + 1) / 2)
            mudahale += int(m)
            u = 2 * s_saf - 1
        if kayit:
            ws.append(env.ruzgar_at(env.adim * DT))
            hs.append(env.h)
        _, r, yere, bitti, s = env.step(u)
        es.append(env.h - env.h_ref)
        ss.append(s)
        if bitti:
            break
```

```python
    es, ss = np.array(es), np.array(ss)
    son = es[-200:]
    basari = (
        (not yere) and (len(es) >= T) and np.max(np.abs(son)) <= 1.0
    )
    out = dict(
        basari=bool(basari),
        yere=bool(yere),
        rms=float(np.sqrt(np.mean(son**2))) if not yere else np.nan,
        iae=float(np.mean(np.abs(es[100:]))) if not yere else np.nan,
        efor=float(np.mean(ss**2)),
        mudahale=mudahale,
    )
    if kayit:
        out["traj"] = (np.array(hs), np.array(ws), es, ss)
    return out
```

```python

def ozet(sonuclar):
    basari = np.mean([r["basari"] for r in sonuclar])
    yere = np.mean([r["yere"] for r in sonuclar])
    iae = np.nanmean([r["iae"] for r in sonuclar])
    efor = np.mean([r["efor"] for r in sonuclar])
    mud = np.mean([r["mudahale"] for r in sonuclar])
    return basari, yere, iae, efor, mud


def egri_ol(pol):
    """Egitim sirasinda: nominal 10 bolumde basari orani."""
    ks = PpoKontrol(pol)
    return float(
        np.mean(
            [
                olc_bolum(ks, NOM, 4000 + i)["basari"]
                for i in range(10)
            ]
        )
    )


def egit(args):
    dr, tohum = args
    torch.set_num_threads(1)
    pol, egri = ppo_egit(
        lambda sd: IhaWrap(sd, dr),
        3,
        1,
        False,
        200000,
        tohum,
        eval_fn=egri_ol,
        eval_her=20000,
    )
    os.makedirs(MODEL, exist_ok=True)
    ad = "dr" if dr else "nom"
    torch.save(
        pol.state_dict(),
        os.path.join(MODEL, "%s_%d.pt" % (ad, tohum)),
    )
    return dr, tohum, egri
```

```python

def pid_ayarla():
    """Kazanc izgarasi; amac: tohum 100-109 (nominal) uzerinde
    ortalama maliyet = e^2 + 0.1 s^2 + 1000 * dusme orani."""
    en_iyi, en_j = None, np.inf
    for kp in (0.05, 0.1, 0.2, 0.4):
        for ki in (0.0, 0.01, 0.02, 0.05):
            for kd in (0.1, 0.2, 0.4, 0.8):
                pid = PID(kp, ki, kd)
                J = []
                for i in range(10):
                    env = IhaIrtifa(
                        rng=np.random.default_rng(100 + i), **NOM
                    )
                    env.reset(seed=100 + i)
                    pid.reset()
                    e2, s2, dus = [], [], 0
                    while True:
                        u = pid.act(env)
                        _, _, yere, bitti, s = env.step(u)
                        e2.append((env.h - env.h_ref) ** 2)
                        s2.append(s * s)
                        if bitti:
                            dus = int(yere)
                            break
                    J.append(
                        np.mean(e2) + 0.1 * np.mean(s2) + 1000 * dus
                    )
                j = float(np.mean(J))
                if j < en_j:
                    en_j, en_iyi = j, (kp, ki, kd)
    return en_iyi, en_j


if __name__ == "__main__":
    (kp, ki, kd), j = pid_ayarla()
    print(
        "PID kazanclari (tohum 100-109): "
        "kp=%.2f ki=%.2f kd=%.2f J=%.4f"
        % (kp, ki, kd, j)
    )
    PIDK = PID(kp, ki, kd)
```

```python
    with ProcessPoolExecutor(max_workers=5) as ex:
        isler = [(d, t) for d in (False, True) for t in TOHUMLAR]
        egitim = list(ex.map(egit, isler))
    print("PPO egitimi tamam (10 kosu)")

    pol_nom, pol_dr = {}, {}
    for dr, t, _ in egitim:
        p = Politika(3, 1, False)
        p.load_state_dict(
            torch.load(
                os.path.join(
                    MODEL, "%s_%d.pt" % ("dr" if dr else "nom", t)
                ),
                weights_only=True,
            )
        )
        (pol_dr if dr else pol_nom)[t] = p

    # Alan kaymasi taramasi: basari orani (5 egitim tohumu x 100
    # bolum)
    satirlar = ["alfa,kontrolcu,ort,sd"]
    tablo = {}
    for alfa in (0.0, 0.25, 0.5, 0.75, 1.0):
        prm = alfa_parametre(alfa)
        seeds = range(3000, 3100)
        b = [olc_bolum(PIDK, prm, s)["basari"] for s in seeds]
        tablo[(alfa, "PID")] = (np.mean(b), 0.0)
        satirlar.append("%.2f,PID,%.3f,0.000" % (alfa, np.mean(b)))
        for ad, bank in (("PPO-nom", pol_nom), ("PPO-DR", pol_dr)):
            vals = []
            for t in TOHUMLAR:
                kon = PpoKontrol(bank[t])
                vals.append(
                    np.mean(
                        [
                            olc_bolum(kon, prm, s)["basari"]
                            for s in seeds
                        ]
```

```python
                    )
                )
            vals = np.array(vals)
            tablo[(alfa, ad)] = (vals.mean(), vals.std(ddof=1))
            satirlar.append(
                "%.2f,%s,%.3f,%.3f"
                % (alfa, ad, vals.mean(), vals.std(ddof=1))
            )
    with open(
        os.path.join(VERI, "b74_iha_dr.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    print("alfa   PID          PPO-nom       PPO-DR     (basari, sd)")
    for alfa in (0.0, 0.25, 0.5, 0.75, 1.0):
        print(
            "%.2f  " % alfa
            + "  ".join(
                "%.2f(%.2f)" % tablo[(alfa, k)]
                for k in ("PID", "PPO-nom", "PPO-DR")
            )
        )
```

```python
    # Ayrinti tablosu: nominal ve alfa=1 (efor, IAE, dusme)
    for alfa in (0.0, 1.0):
        prm = alfa_parametre(alfa)
        seeds = range(3000, 3100)
        r = ozet([olc_bolum(PIDK, prm, s) for s in seeds])
        print(
            "alfa=%.1f PID: basari=%.2f dusme=%.2f IAE=%.3f efor=%.3f"
            % (alfa, r[0], r[1], r[2], r[3])
        )
        for ad, bank in (("PPO-nom", pol_nom), ("PPO-DR", pol_dr)):
            rr = [
                ozet(
                    [
                        olc_bolum(PpoKontrol(bank[t]), prm, s)
                        for s in seeds
                    ]
                )
                for t in TOHUMLAR
            ]
            rr = np.array(rr)
            print(
                "alfa=%.1f %s: basari=%.2f dusme=%.2f "
                "IAE=%.3f efor=%.3f"
                % (
                    alfa,
                    ad,
                    rr[:, 0].mean(),
                    rr[:, 1].mean(),
                    rr[:, 2].mean(),
                    rr[:, 3].mean(),
                )
            )

    # Guvenlik kalkani: alfa=1.0, nominal ve DR, kalkan var/yok
    prm = alfa_parametre(1.0)
    seeds = range(3000, 3100)
    for ad, bank in (("PPO-nom", pol_nom), ("PPO-DR", pol_dr)):
        for kal in (False, True):
```

```python
            rr = np.array(
                [
                    ozet(
                        [
                            olc_bolum(
                                PpoKontrol(bank[t]),
                                prm,
                                s,
                                shield=kal,
                            )
                            for s in seeds
                        ]
                    )
                    for t in TOHUMLAR
                ]
            )
            print(
                "kalkan=%s %s (a=1): dusme=%.3f basari=%.3f "
                "mudahale=%.1f"
                % (
                    kal,
                    ad,
                    rr[:, 1].mean(),
                    rr[:, 0].mean(),
                    rr[:, 4].mean(),
                )
            )
```

```python
    # Yorunge: kutle +20%, ruzgar x1.5 (DR araligi icinde), tohum 3000
    prm = dict(kutle=1.2, kd=0.3, twr=2.0, ruzgar=1.5)
    yol = {
        "PID": olc_bolum(PIDK, prm, 3001, kayit=True)["traj"],
        "PPO-DR": olc_bolum(
            PpoKontrol(pol_dr[0]), prm, 3001, kayit=True
        )["traj"],
        "PPO-nom": olc_bolum(
            PpoKontrol(pol_nom[0]), prm, 3001, kayit=True
        )["traj"],
    }
    n = len(yol["PID"][2])
    sat = ["t,referans,ruzgar,pid_h,dr_h,nom_h,pid_s,dr_s,nom_s"]
    for i in range(n):
        sat.append(
            "%.2f,%.2f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f"
            % (
                i * DT,
                HREF,
                yol["PID"][1][i],
                yol["PID"][0][i],
                yol["PPO-DR"][0][i],
                yol["PPO-nom"][0][i],
                (yol["PID"][3][i]),
                yol["PPO-DR"][3][i],
                yol["PPO-nom"][3][i],
            )
        )
    with open(
        os.path.join(VERI, "b74_iha_yorunge.csv"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("\n".join(sat) + "\n")
    for k, v in yol.items():
        e = v[2]
        print(
            "yorunge %-7s max|e|=%.2f (t>=5s: %.2f)  efor=%.3f"
            % (
                k,
                np.max(np.abs(e)),
                np.max(np.abs(e[100:])),
                np.mean(v[3] ** 2),
            )
        )
    print("PID kazanclari:", (kp, ki, kd))
```

Betiğin çıktısı, `iha_out2.txt`'ten (yeniden çalıştırma) alınmıştır; önceki koşuyla sayısal olarak aynıdır:

```term
PID kazanclari (tohum 100-109): kp=0.40 ki=0.00 kd=0.10 J=0.0949
PPO egitimi tamam (10 kosu)
alfa   PID          PPO-nom       PPO-DR     (basari, sd)
0.00  1.00(0.00)  1.00(0.00)  1.00(0.00)
0.25  1.00(0.00)  1.00(0.00)  1.00(0.00)
0.50  1.00(0.00)  1.00(0.00)  1.00(0.00)
0.75  0.00(0.00)  1.00(0.00)  1.00(0.00)
1.00  0.00(0.00)  0.00(0.00)  0.00(0.00)
alfa=0.0 PID: basari=1.00 dusme=0.00 IAE=0.074 efor=0.245
alfa=0.0 PPO-nom: basari=1.00 dusme=0.00 IAE=0.041 efor=0.245
alfa=0.0 PPO-DR: basari=1.00 dusme=0.00 IAE=0.029 efor=0.246
alfa=1.0 PID: basari=0.00 dusme=0.00 IAE=1.575 efor=0.819
alfa=1.0 PPO-nom: basari=0.00 dusme=0.00 IAE=0.787 efor=0.826
alfa=1.0 PPO-DR: basari=0.00 dusme=0.00 IAE=0.594 efor=0.830
kalkan=False PPO-nom (a=1): dusme=0.000 basari=0.000 mudahale=0.0
kalkan=True PPO-nom (a=1): dusme=0.000 basari=0.000 mudahale=0.0
kalkan=False PPO-DR (a=1): dusme=0.000 basari=0.000 mudahale=0.0
kalkan=True PPO-DR (a=1): dusme=0.000 basari=0.000 mudahale=0.0
yorunge PID     max|e|=2.48 (t>=5s: 0.45)  efor=0.349
yorunge PPO-DR  max|e|=2.48 (t>=5s: 0.13)  efor=0.348
yorunge PPO-nom max|e|=2.48 (t>=5s: 0.15)  efor=0.352
PID kazanclari: (0.4, 0.0, 0.1)
```

Kayma taramasının özeti şu:

| α | PID (K_i = 0) | PPO-nom | PPO-DR |
|---|---|---|---|
| 0,00 | 1,00 | 1,00 | 1,00 |
| 0,25 | 1,00 | 1,00 | 1,00 |
| 0,50 | 1,00 | 1,00 | 1,00 |
| 0,75 | 0,00 | 1,00 | 1,00 |
| 1,00 | 0,00 | 0,00 | 0,00 |

Başarı oranları 100 bölüm üzerinden; PPO için beş eğitim tohumunun ortalaması (beş tohumun hepsi aynı oranı verdi, sapma 0). Nominal ortamda ayrıntılar daha da anlamlıdır: PID'nin ortalama mutlak sapması (IAE) 0,074 iken PPO-nom 0,041 ve PPO-DR 0,029'dur; kontrol çabası (`ort s²`) üçünde de 0,245 civarındadır. Yani nominal koşulda PPO-nom'un IAE'si PID'nin yaklaşık yarısıdır (0,041'e karşı 0,074) ve efor aynıdır.

Şekil 74.9, bu taramayı görsel olarak gösteriyor. α = 0,75'te PID'nin başarısı 0'a düşerken her iki PPO da 100 bölümün hepsinde başarılı. Bu sonucu yorumlamak için integral terimli bir PID'ye bakalım (74.13).

![Şekil 74.9: Parametre kayması altında başarı oranı (100 bölüm). Nominal ayarlı PID (K_i = 0) α = 0,75'te çöker; integral terimli PID (K_i = 0,02) ve iki PPO bu noktaya kadar başarılıdır; α = 1'de hiçbiri başarılı değildir.](gorseller/b74_alan_kaymasi.png)

α = 1'de üç kontrolcü de başarısızdı, ama bu başarısızlıklar **düşme değildi**: düşme oranı sıfırdı (dusme = 0,000). Başarısızlık, son 10 saniyede irtifanın 1 m bandının dışında kalmasıdır ve bu, fiziksel bir sınırdan kaynaklanır. α = 1'de kütle 1,5 ve `twr = 1,6` olduğundan hover itkisi `1,5 / 1,6 = 0,94`'tür; yani gazın yalnızca `1 − 0,94 = 0,06`'lık bir payı kalır. Rüzgârın aşağı yönlü ivmesi 0,65 m/s²'yi aşınca gereken itki 1'in üstüne çıkar ve irtifa sapar. Hiçbir kontrolcü, itki sınırının ötesinde bir kuvvet üretemez; ne PID ne PPO bunu aşabilir. Bu, alan rastgeleleştirmenin de aşamayacağı bir sınırdır: DR aralığının dışındaki ortam, fiziksel olarak zor ya da imkânsız olabilir.

Güvenlik kalkanının sonucu ise bu deneyde **bilgi vermiyor**. Her iki PPO ile `α = 1`'de kalkan açıkken ve kapalıyken hiçbir bölümde zemine düşme olmadı, bu yüzden kalkan hiç müdahale etmedi (mudahale = 0). Kalkan, düşmeyi önleyecek bir durum oluşmadığı için devreye girmedi. Kalkanın değerini ölçmek için, düşmenin gerçekten oluştuğu bir koşul gerekir: örneğin modelin yanlış olduğu, itkinin daha zayıf olduğu ya da ilk irtifanın daha düşük olduğu bir senaryo. Bu bölümde bu senaryoyu kurmadık; kalkanın kodu ve tanımı yukarıdadır, ama etkisini kanıtlamış sayılmaz.

Bir son gözlem: PPO-DR, α = 1'de PPO-nom'dan daha küçük bir IAE verdi (0,594'e karşılık 0,787). Bu, DR'nin uç koşulda sapmayı azaltabildiğini gösterir, ama başarı oranını değiştirmedi. Alan rastgeleleştirmenin asıl avantajı, bu tabloda, sapmanın azalması olarak kendini gösterdi; başarı eşiğinin üstüne çıkmadı.

::: dikkat
Bu tabloyu okurken "RL, PID'den dayanıklı" sonucunu aceleyle çıkarma. Tablo bir tek ortam ailesi, tek bir kayma yönü (üç parametrenin birlikte değişmesi) ve 100 bölümlük bir değerlendirme ile elde edildi. Başka bir kayma yönünde, örneğin yalnızca sürükleme değiştiğinde, ya da farklı bir rüzgâr profilinde sonuç farklı çıkabilir.
:::

## 74.13 RL mi, klasik kontrol mü? Dürüst bir karşılaştırma

Yukarıdaki tablo, PID ile PPO arasında bir fark gösteriyor, ama bu farkın nedenini yanlış okumak kolaydır. PID'nin α = 0,75'te çökmesi, PID'nin kötü bir kontrolcü olduğunu göstermez: PID, nominal ortamda `K_i = 0` ile seçildi ve kütle değiştiğinde kalıcı bir hata biriktirdi. Bunu test etmek için aynı `K_p` ve `K_d` ile integral kazancı `K_i ∈ {0; 0,02; 0,05}` olan üç varyantı, aynı kayma taramasında karşılaştırdık. Aşağıdaki betik `pidki74.py` bu karşılaştırmayı yapar ve sonuçları `b74_pid_ki.csv`'ye yazar.

```python
# -*- coding: utf-8 -*-
"""Bolum 74 - PID'in integral terimi: alan kaymasi taramasi.

iha74.py'deki nominal ayarli PID (kp=0.4, ki=0, kd=0.1) ile ayni
kp ve kd'de, integral kazancini ki = 0.02 ve 0.05 yapan iki varyant,
ayni 100 degerlendirme bolumu (tohum 3000+) uzerinde olculur.
"""

import numpy as np
from iha74 import PID, alfa_parametre, olc_bolum

KP, KD = 0.4, 0.1
ALFALAR = (0.0, 0.25, 0.5, 0.75, 1.0)

if __name__ == "__main__":
    import csv
    import os

    veri = "D:/Mevcut Projeler/Kitap/engine/veri"
    satirlar = []
    print(
        "alfa  | ki=0.00 basari IAE | ki=0.02 basari IAE"
        " | ki=0.05 basari IAE"
    )
    for alfa in ALFALAR:
        prm = alfa_parametre(alfa)
        satir = "%.2f " % alfa
        for ki in (0.0, 0.02, 0.05):
            kon = PID(KP, ki, KD)
            sonuc = [
                olc_bolum(kon, prm, s) for s in range(3000, 3100)
            ]
            basari = np.mean([r["basari"] for r in sonuc])
            iae = np.nanmean([r["iae"] for r in sonuc])
            satir += "   %.2f  %.3f         " % (basari, iae)
            satirlar.append((alfa, ki, basari, iae))
        print(satir)
    with open(
```

```python
        os.path.join(veri, "b74_pid_ki.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        yazar = csv.writer(f)
        yazar.writerow(["alfa", "ki", "basari", "iae"])
        for a, k, b, i in satirlar:
            yazar.writerow(
                ["%.2f" % a, "%.2f" % k, "%.3f" % b, "%.4f" % i]
            )
```

```term
alfa  | ki=0.00 basari IAE | ki=0.02 basari IAE | ki=0.05 basari IAE
0.00    1.00  0.074            1.00  0.074            1.00  0.075         
0.25    1.00  0.205            1.00  0.141            1.00  0.122         
0.50    1.00  0.449            1.00  0.259            1.00  0.190         
0.75    0.00  0.722            1.00  0.410            1.00  0.274         
1.00    0.00  1.575            0.00  1.173            0.00  1.052         
```

Sonuçlar, PPO'nun üstünlüğünün büyük kısmının integral terimden geldiğini gösteriyor. `K_i = 0,02` ile PID, α = 0,75'te de başarılıdır (IAE 0,410); yani başarı aralığı, iki PPO ile aynıdır. `K_i = 0,05` ile α = 0,75'teki IAE 0,274'e düşer. α = 1'de ise üç PID varyantı da başarısızdır; `K_i = 0,05`'in IAE'si (1,052) PPO-DR'nin (0,594) üzerindedir. Yani uç koşulda PPO'nun sapması hâlâ daha küçüktür, ama bu fark başarı oranında görünmez.

Nominal koşul için de dürüst olmak gerekir: integral terimli PID'nin nominal IAE'si (0,074) ile PPO-nom'un (0,041) arasındaki fark, bu ölçümle ancak sınırlı bir yönü gösterir. PID'ye ayrıca bir ayar yapmadık; kazançları yalnızca bir ızgarada seçtik. Bu nedenle "RL, PID'den daha iyi takip eder" gibi genel bir cümle kurmak yanlış olur. Doğru cümle şudur: bu ortamda, uygun bir integral terimle, PID alan kaymasına karşı PPO ile aynı başarı aralığına ulaşır; PPO, uç koşulda sapmayı biraz daha küçük tutar.

![Şekil 74.10: Kütle +%20 ve rüzgâr ×1,5 (DR aralığı içinde, tohum 3001) için irtifa yörüngeleri. Üst: PID (K_i = 0), PPO (nominal eğitim) ve PPO (alan rastgeleleştirme). Alt: rüzgâr ivmesi.](gorseller/b74_iha_yorunge.png)

Şekil 74.10, bu senaryodaki yörüngeleri gösteriyor. Başlangıçtaki 2,5 m'lik sapma 1–2 saniyede bastırılıyor; bu geçişte PID hedefin 0,82 m altına inen bir aşım yapar, PPO-DR ise 0,06 m'den fazla inmez. Ondan sonra fark belirginleşiyor: 4–9 saniye arasında (rüzgâr basamağının olduğu aralıkta) PID'nin ortalama mutlak sapması 0,28 m, PPO-nom'un 0,11 m, PPO-DR'nin 0,09 m'dir. Beş saniyeden sonraki ortalama `|e|` ise sırasıyla 0,22, 0,10 ve 0,07 m'dir; PID hedefin sürekli altında bir sapma taşır. Kontrol çabası üçünde de neredeyse aynı (ortalama `s²` 0,348–0,352). Yani bu senaryoda RL, aynı efor ile daha küçük bir sapma sağladı. Bu da, kütle farkına karşı integral eksikliğinin bedelini gösterir; integral terimli PID bu bedeli büyük ölçüde kapatır.

Bu bölümün sonunda, RL'nin klasik kontrol karşısında ne zaman gereksiz olduğunu özetlemek gerekir. Eğer sistem doğrusala yakınsa, bilinen bir model varsa ve tasarım gereksinimleri (kararlılık payı, sapma, efor) klasik yöntemlerle karşılanabiliyorsa, PID ya da durum geri beslemesi (Bölüm 52'deki kontrol ve sinyal bakışıyla birlikte) çoğu zaman daha basit, daha kolay doğrulanabilir ve daha ucuz bir çözümdür. RL'nin değeri, modelin belirsiz olduğu, ortamın doğrusal olmadığı ve amacın birden çok karmaşık hedeften oluştuğu durumlarda ortaya çıkar. Bu bölümdeki İHA deneyinde bile, RL'nin kazancı, PID'ye bir integral terimi eklendiğinde büyük ölçüde kayboldu. Bu dersi, bir RL projesi başlatmadan önce hatırlamak gerekir.

::: baglanti
PID ve durum geri beslemesi, Bölüm 50'deki optimizasyon çerçevesinde kazanç seçimi olarak da görülebilir: kazançlar değişkendir, amaç fonksiyonu sapma ve efordur, kısıt itki sınırıdır. Bu bölümdeki ızgara araması, bu optimizasyonun en kaba biçimidir; daha iyi bir yöntem (örneğin Bayesçi optimizasyon) aynı problemi daha az deneme ile çözebilir.
:::

::: mulakat
1. Bir İHA irtifa kontrolcüsünde integral terimin rolü nedir? Kütle değişimi altında integral terimi olmayan bir PID neden kalıcı bir hata verir?
2. Bir politikaya integral bilgisini gözlem olarak vermek ile PID'ye integral terimi eklemek arasındaki fark nedir? Hangisi kontrol teorisinin diliyle daha kolay açıklanır?
3. Bir RL kontrolcüsü, bir PID'den daha iyi görünebilir. Bunun gerçek bir üstünlük olup olmadığını nasıl sınarsın? Hangi baz çizgi ayarlarını yapmadan karşılaştırma yapılamaz?
:::

## 74.14 Ödül hackleme, sim-to-real ve güvenlik

Pekiştirmeli öğrenmede en tehlikeli hata, yanlış çalışan bir algoritma değil, doğru çalışan ama yanlış şeyi optimize eden bir algoritmadır. Ödül, ajanın amacının tek sayılık bir temsilidir; temsil ile niyet arasındaki boşluğu ajan bulur ve sömürür. Buna **ödül hackleme** (reward hacking) denir. Bu bölümde iki örnekle bunu görelim: biri tasarlanmış küçük bir koridor, diğeri kendi İHA ortamımızda karşılaştığımız bir gerçek olay.

### Örnek 1: Tekrarlanabilen bir bonus

Koridor, altı konumdan oluşur. Ajan 0'dan başlar, 5'e (hedef) varınca +10 alır ve bölüm biter. Konum 2'de +1 ödül vardır. Bu bonusun tasarımı iki şekilde olabilir: ilk ziyarette tüketilir ya da her ziyarette yeniden doğar. Tasarımcı, bonusun yalnızca bir kez alınabileceğini düşünerek yenilenen versiyonu yazmış olabilir. Model bilindiği için (74.4'teki gibi) optimal politikayı deger iterasyonuyla bulabiliriz. İndirim `γ = 0,99`.

Aşağıdaki betik `hack74.py`, iki tasarımın optimal politikasını ve başlangıçtan izlenen yolu gösterir.

```python
# -*- coding: utf-8 -*-
"""Bolum 74 - Odul hackleme (reward hacking): kucuk bir koridor.

Koridor: konumlar 0..5, baslangic 0, hedef 5 (odul +10, biter).
Konum 2'de +1 odul var. Iki tasarim:
  yenilenir=True : +1 her girisinde (sinirsiz tekrar) -> ajan dongu
                   kurup hedefe hic gitmeyebilir
  yenilenir=False: +1 yalnizca ilk girişte (tuketilir)
Model bilindigi icin deger iterasyonu (dp74.py) ile optimum bulunur.
gamma = 0.99.
"""

import textwrap
import numpy as np
from dp74 import deger_iterasyonu

GAMMA = 0.99


class Koridor:
    def __init__(self, yenilenir):
        self.y = yenilenir
        self.L, self.hedef, self.bonus = 6, 5, 2
        self.nA = 2  # 0 sol, 1 sag
        self.S = 6 if yenilenir else 12  # konum (ve tuketim)
        self.P = {}
        for p in range(6):
            for c in ((0,) if yenilenir else (0, 1)):
                s = self.idx(p, c)
                for a in (0, 1):
                    if p == self.hedef:
                        self.P[(s, a)] = [(1.0, s, 0.0, True)]
                        continue
                    p2 = max(0, p - 1) if a == 0 else min(5, p + 1)
                    if p2 == self.hedef:
                        self.P[(s, a)] = [
                            (1.0, self.idx(p2, c), 10.0, True)
                        ]
```

```python
                        continue
                    r, c2 = 0.0, c
                    if p2 == self.bonus and (yenilenir or c == 0):
                        r = 1.0
                        c2 = c if yenilenir else 1
                    self.P[(s, a)] = [
                        (1.0, self.idx(p2, c2), r, False)
                    ]
```

```python
    def idx(self, p, c=0):
        return p if self.y else 2 * p + c


def iz(env, pi, s0_p, adim=12):
    """Acgozlu politikanin izini (konum, odul) olarak dondur."""
    p, c = s0_p, 0
    s = env.idx(p, c)
    kayit = []
    for _ in range(adim):
        a = int(pi[s])
        ((_, s2, r, bitti),) = env.P[(s, a)]
        kayit.append(("sol" if a == 0 else "sag", s2, r))
        if bitti:
            break
        s = s2
    return kayit


if __name__ == "__main__":
    for yenilenir in (True, False):
        env = Koridor(yenilenir)
        V, pi, kal = deger_iterasyonu(env, GAMMA)
        ad = (
            "yenilenir (hack)"
            if yenilenir
            else "tuketilir (duzeltilmis)"
        )
        print("%s: V(baslangic=0)=%.3f" % (ad, V[env.idx(0, 0)]))
        yol = iz(env, pi, 0)
        satir = " ".join("%s->%d(r=%g)" % y for y in yol)
        print("  acgozlu iz:")
        for parca in textwrap.wrap(satir, 68):
            print("    " + parca)
        toplam, gamma_k = 0.0, 1.0
        for k, (_, _, r) in enumerate(yol):
            toplam += gamma_k * r
            gamma_k *= GAMMA
        print("  ilk 12 adimin indirimli toplam odulu: %.3f" % toplam)
    # Hackle: sadece ilk gecisin ortalama odulu vs sinirsiz dongu
    # degeri
    print(
        "Sinirsiz dongu (konum 2<->3, her 2 adimda +1) degeri: %.3f"
        % (GAMMA**2 / (1 - GAMMA**2))
    )
    print("Hedefe gitme degeri (2 -> 5, +10): %.3f" % (GAMMA**2 * 10))
```

```term
yenilenir (hack): V(baslangic=0)=49.749
  acgozlu iz:
    sag->1(r=0) sag->2(r=1) sol->1(r=0) sag->2(r=1) sol->1(r=0)
    sag->2(r=1) sol->1(r=0) sag->2(r=1) sol->1(r=0) sag->2(r=1)
    sol->1(r=0) sag->2(r=1)
  ilk 12 adimin indirimli toplam odulu: 5.652
tuketilir (duzeltilmis): V(baslangic=0)=10.596
  acgozlu iz:
    sag->2(r=0) sag->5(r=1) sag->7(r=0) sag->9(r=0) sag->11(r=10)
  ilk 12 adimin indirimli toplam odulu: 10.596
Sinirsiz dongu (konum 2<->3, her 2 adimda +1) degeri: 49.251
Hedefe gitme degeri (2 -> 5, +10): 9.801
```

Sonuçlar tasarımın ne kadar yanıltıcı olabileceğini gösteriyor. Yenilenen bonusla optimal politika, 1 ile 2 konumları arasında sonsuza dek gidip gelmektir: her iki adımda bir +1 almak, toplamda `γ²/(1 − γ²) ≈ 49,25` değerini verir. Hedefe gitmek ise `γ² · 10 ≈ 9,80` eder. Ajan, `V(0) = 49,75` değeri ile hedefi hiç görmeden döngüye girer. Bonus tüketilebilir olunca ise optimal yol önce bonusu alır, sonra hedefe gider; değer `10,596`'dır ve bu, `γ·1 + γ⁴·10 = 0,99 + 9,606` toplamıdır. Tasarım değişikliği yalnızca bir durum bayrağıdır, ama ajanın davranışını kökten değiştirir.

Ödül hackleme için bu, en basit ve en öğretici biçimdir: ödülün ifade ettiği ile tasarımcının kastettiği farklıdır ve optimizasyon, ilkini izler. Gerçek sistemlerde bu tür boşluklar ancak ajanın çok karmaşık davranışlar bulmasıyla fark edilir; bu yüzden her ödül tasarımı, ajanın verdiği yanıtlarla birlikte bir kez daha okunmalıdır.

### Örnek 2: Kendini öldürme: sınırsız sapma cezasının tuzağı

Bu örnek, bu bölümdeki İHA ortamında gerçekten karşılaştığımız bir durumdur. Ödül, sapma (`−e²`) ve efor (`−0,1 s²`) cezalarının toplamıdır; zemine düşmede ek `−100` vardır. Yer çekiminin ve sürüklenmenin olduğu bir ortamda, bir kez kontrolü kaybeden ajan, her adımda büyüyen bir sapma cezası biriktirir. Eğer tüm bölüm boyunca bu ceza, çarpma cezasından (−100) daha büyük olacak şekilde birikirse, ajan için yere çarpmak, uzun bir süre kötü uçuşa devam etmekten daha ucuzdur. Ödül ölçeğine bağlı olarak bu sınır değişir; biz, ödülü `0,1` ile ölçekleyip ilk denemeyi yaptığımızda tam bu davranışı gözlemledik: alan rastgeleleştirmeli eğitimle 30 000 adım sonra tek tohumlu bir politika, nominal ortamda değerlendirildiğinde yere çarpıyordu; değerlendirme başarı oranı 0'dı.

Düzeltme, bu cezanın sınırını kaldırmak ve bir **hayatta kalma tabanı** eklemekti. Eğitim ödülü şöyle yazıldı:

r_t = 0,04 · (25 − min(e_t², 25) − 0,1 s_t²), zemine düşmede r_t = 0

Burada sapma cezası 25 ile sınırlandı (çok büyük sapmalar bir tavan görür), ve her adımda sabit bir taban (25) eklendi. Bu sayede her adımın ödülü sıfırdan büyük (ya da neredeyse sıfır) ve yere çarpmak, kazanılacak ödülleri keser; çarpma artık ayrıca cezalandırılmasa da en büyük kayıp, gelecekteki tabanın kaybıdır. İki tasarım arasındaki fark küçük bir değişiklik gibi görünse de davranışı tersine çevirir: sınırsız ceza, intiharı teşvik ederken; sınırlı ceza ve taban, hayatta kalmayı teşvik eder.

Bu örneğin sınırı da bellidir: tek bir tohumla ve 30 000 adımlık bir ilk denemeyi anlatıyoruz; bu, sistematik bir ölçüm değil, bir tasarım hatasının gözlemidir. Bu bir istatistiksel kanıt değildir; ama tasarım hatasının nasıl ortaya çıktığını ve düzeltmenin hangi yönde olduğunu göstermeye yeter. Bölüm 74.15'teki değerlendirme disiplini, bu tür gözlemleri beş tohumla tekrarlamayı zorunlu kılar.

::: dikkat
Ödül hackleme, çoğu zaman "ajan kötü" olarak yanlış teşhis edilir. Oysa ajan, tanımladığın ödülü mükemmel optimize etmiştir. Her ödül tasarımına şu soruyu sor: "Bu ödülü en çok büyüten davranış nedir ve ben bunu istiyor muyum?" Cevap hayırsa, ödül yanlıştır, ajan değil.
:::

### Simülasyon–gerçek boşluğu ve alan rastgeleleştirme

Simülasyonda öğrenilen bir politika, gerçek dünyaya taşındığında genellikle kötüleşir. Bu **simülasyon–gerçek boşluğu** (sim-to-real gap) olarak bilinir. Kaynakları çok çeşitlidir: kütle ve atalet değerleri yanlıştır, sürükleme ve sürtünme basitleştirilmiştir, sensör gecikmesi ve gürültüsü ihmal edilmiştir, aktüatör doğrusal değildir. Bu bölümdeki İHA ortamı da bu boşluğun bir modelidir: sürtünmeyi tek bir `kd` ile, itkiyi doğrusal bir `twr` ile, rüzgârı bir sinüs ve basamakla yazdık. Gerçek bir uçak bu basitleştirmelerin hiçbirine tam uymaz.

Bu boşluğu kapatmanın iki klasik yolu vardır. **Sistem tanımlama** (system identification), gerçek veriden fiziksel parametreleri kestirip simülasyonu buna göre düzeltmektir: Bölüm 62'deki Kalman filtresi, parametre tahmininin de bir durum kestirimi olarak yazılabildiği yerdir. **Alan rastgeleleştirme** (domain randomization), farklı bir yol izler: eğitimde parametreleri her bölümde rastgele seçersin, böylece politika tek bir ortama değil, bir parametre ailesine uymak zorunda kalır. Test, ailenin dışında kalan bir parametrede yapılır. Eğer politika, eğitim ailesinin dışındaki bir ortamda da başarılıysa, o politika parametre kaymasına karşı sağlamdır.

Alan rastgeleleştirmenin bir sınırı vardır: politika, parametre ailesinin **içinde** kalan ortamlarda iyi çalışır, dışında ise tahmin edilemez biçimde davranabilir. Bu sınırı ölçmek, bu bölümün en önemli deneylerinden biridir (Bölüm 74.12).

### Güvenli RL: kısıtlar ve kalkan

Bir İHA'da bazı durumlar hiçbir ödül ile telafi edilemez: zemine çarpma, irtifa sınırını aşma, itki limitinin ötesine geçme. Bu tür kısıtlar ödül ceza olarak eklenerek yumuşatılabilir, ama ajan yine de ihlal edebilir: cezanın büyüklüğü ile ihlalin faydası arasındaki takas, ödül ölçeğine bağlıdır (az önceki örnek bunu gösterdi). **Güvenlik kalkanı** (shield), kısıtı öğrenmeye bırakmaz: politikanın önerdiği eylemi, kısıtı ihlal etmeyecek en yakın eylemle değiştirir.

Bu bölümde kullandığımız kalkan basit bir ileri bakıştır. Nominal modelle, politikanın eylemi uygulandığında bir sonraki irtifanın `h_min = 2 m`'nin altına inip inmeyeceğini hesaplarız. İnecekse, itkiyi irtifayı tam `h_min`'e tutacak en küçük değere yükseltiriz. Kalkan, modelin doğru olduğunu varsayar; bu da onun asıl sınırıdır. Model yanlışsa, kalkanın hesabı da yanlıştır. Bu sınır, alan kaymasında kalkanın neden tam bir güvence olmadığını açıklar (Bölüm 74.12).

Kalkan, eğitimi değil, yalnızca yürütmeyi değiştirir. Politika eğitiminde kalkan kullanılmazsa, politika kısıtı hiç öğrenmez ve kalkan sürekli müdahale etmek zorunda kalır. Bu tasarım seçimi, kalkanın ne kadar iş gördüğünü ölçerek görülebilir: sayılan müdahale sayısı, politikanın kısıta ne kadar yakın çalıştığının bir göstergesidir.

### Çevrimdışı RL

Son bir kavram: **çevrimdışı RL** (offline RL), ajanın yeni veri toplamadan, önceden kaydedilmiş bir veri kümesinden öğrenmesidir. Bu, bir İHA'nın uçuş kayıtlarından bir politika çıkarmak gibidir: yeni uçuş yapmak pahalı ve tehlikeli olabilir. Ama çevrimdışı veri, politika dışıdır ve Baird'in karşı örneğindeki ölümcül üçlünün tüm ayaklarını taşır: fonksiyon yaklaşımı, önyükleme ve politika dışı dağılım. Bu yüzden çevrimdışı yöntemler, veriyi önceki politikaya yakın tutmaya (kısıtlı güncellemeler) çalışır. Bu bölümde çevrimdışı deneyi yapmadık; kavram olarak, Bölüm 74.16'daki RLHF/DPO köprüsünde yeniden karşımıza çıkacak.

## 74.15 Değerlendirme disiplini: tohum, ayrım ve belirsizlik

Pekiştirmeli öğrenmede bir sonucu güvenilir kılmak, denetimli öğrenmeden daha zordur. Bunun üç nedeni var. Birincisi, veri ajanın kendi politikasına bağlıdır: aynı kod, farklı tohumla çok farklı bir veri kümesi üretir. İkincisi, ortam ve ajan birlikte stokastiktir: tek bir bölüm, şansın ürünü olabilir. Üçüncüsü, eğitim sırasında hiperparametreleri değiştirmek kolaydır ve bu, değerlendirme ortamını sızdırır.

Bu bölümdeki deneylerde şu kurallara uyduk ve bunları raporlamanın parçası olarak görüyoruz.

**Kural 1: Birden çok tohum.** Her sonuç en az beş tohumla verildi. Tek bir koşu, bir RL sonucu sayılmaz. Tablo ve şekillerde ortalama ile birlikte sapma ya da bant gösterildi. Bu bölümün en açıklayıcı örneği, DQN'de tam ve Double DQN'in son değerlerinin 365 ile 366 olmasına rağmen tohum sapmalarının (179 ve 154) farktan kat kat büyük olmasıdır. Bu iki yöntemi "eşit" saymak da, "Double DQN daha iyi" demek de yanlıştır: beş tohum, bu ayrımı yapmaya yetmez.

**Kural 2: Değerlendirme tohumlarını ayırmak.** Eğitim ve değerlendirme başlangıçları farklı tohumlardan gelir. Bu bölümde eğitim ortamının başlangıç durumları, tohum `0..4` ile; değerlendirme ise `3000+`, `4000+`, `900+` ve `700000+` gibi ayrı bir aralıkla belirlendi. Hiperparametreler yalnızca ayar tohumlarında (10, 11, 100–109) seçildi ve değerlendirme tohumları hiçbir karar için kullanılmadı. Bu ayrım, ilk DQN denemesinde kasten gözden geçirildi: o denemenin tek tohumu (0) değerlendirme tohumlarından biriydi ve yalnızca kodun öğrenip öğrenmediğini görmek için kullanıldı.

**Kural 3: Baz çizgi.** Bir RL sonucu yalnızca "çalıştı" diye değerlendirilemez; bir taban çizgiyle karşılaştırılmalıdır. İHA deneyinde taban çizgisi PID'di; bu bölümde ayrıca, rastgele bir politika ve dinamik programlama ile hesaplanmış optimum da referanslar olarak kullanıldı. Baz çizgi zayıf seçilirse (örneğin ayarlanmamış bir PID), RL sonucu anlamsız bir üstünlük gibi görünür. Bu yüzden PID'imizi nominal ortamda ayarladık ve kazancı değerlendirme tohumlarında değil, ayar tohumlarında seçtik.

**Kural 4: Belirsizlik.** Sonuçlar ortalama ± sapma ile verilir. Küçük örneklemde güven aralığı hesaplamak için Bölüm 57.11'deki bootstrap yöntemi kullanılabilir: beş tohumun değerlerini yerine koyarak yeniden örnekle ve her seferinde ortalamayı hesapla. Ancak beş değer, bootstrap için çok azdır; bu yüzden bu tür aralıklar kaba kalır ve yalnızca bir yönü gösterir. Daha sağlam bir yol, daha fazla tohum koşmaktır. Bu, RL'de çoğu zaman hesaplama bütçesinin en değerli kullanım biçimidir.

**Kural 5: Son performans ile öğrenme eğrisi alanı.** Tek bir son değer, sürekli dalgalanan bir eğrinin hangi noktasında ölçüldüğüne bağlıdır. DQN eğrisinde tam DQN 30 000 adımdan sonra 330–390 arasında dalgalandı; son değeri hangi adımda aldığın, sonucu değiştirebilir. Bu yüzden hem son değeri hem de eğrinin tamamını (alan) raporlamak gerekir. Eğrinin alanı, öğrenmenin hızını ve kararlılığını birlikte gösterir.

**Kural 6: Gözlem ile kanıtı ayırmak.** Yukarıdaki iki örnekte (ödül hackleme ve ilk İHA denemesi) tek tohumla gözlemler yaptık. Bunlar gözlem olarak anlatıldı ve birer kanıt olarak sunulmadı. Gözlemin kanıta dönüşmesi için aynı koşulun beş tohumla tekrarlanması ve bir karşıt koşulun (sınırlı ödül ile sınırsız ödül gibi) karşılaştırılması gerekir.

::: ipucu
Bir RL deneyi raporlarken bu altı kuralı kendine bir kontrol listesi olarak kullan: tohum sayısı kaç, değerlendirme tohumları eğitimden ayrık mı, bir baz çizgi var mı, sapma ve bant nedir, son değer ile eğri alanı birlikte verildi mi, gözlem ile kanıt ayrıldı mı?
:::

## 74.16 Köprü: RLHF ve DPO

Bölüm 70 ve 71'de, bir dil modelini talimat ince ayarından sonra insan tercihleriyle hizalamanın yollarını gördün. Bu hizalamanın pekiştirmeli öğrenme ile bağı şudur: bir dil modelinin çıktısı bir "eylem dizisidir" (her belirteç bir eylem), ödül ise bir ödül modelinin insan tercihini tahmin eden skoru olabilir. Bu fikir, **insan geri bildirimiyle pekiştirmeli öğrenme** (RLHF) olarak bilinir: önce tercihlerden bir ödül modeli eğitilir, sonra dil modeli PPO ile bu ödülü maksimize edecek şekilde güncellenir (genel bilgi).

Bu yaklaşımın iki zorluğu vardır. Birincisi, ödül modeli bir vekildir ve vekil, ödülün kendisi değildir: Bölüm 74.14'teki ödül hackleme burada da geçerlidir. Modelin tercih tahmininde bir boşluk varsa, politika bu boşluğu sömürür ve metin gerçek kaliteden çok ödül modelinin sevdiği biçimlere yönelir. İkincisi, PPO'nun güncellemeleri pahalıdır ve dil modelinde politika ile referans modeli birlikte tutmak bellek ister.

**DPO** (Direct Preference Optimization, Rafailov ve arkadaşları 2023, genel bilgi), bu adımlardan birini ortadan kaldırır: ödül modelini ve RL döngüsünü açıkça eğitmez. Tercih çiftleri üzerinde doğrudan bir kayıp fonksiyonu yazar; bu kayıp, politikanın tercih edilen yanıtın göreli olasılığını, referans politikaya göre artırmasını sağlar. Matematiksel olarak ödül ile politika arasındaki ilişkiyi kullanır: optimal KL-kısıtlı politikanın ödül fonksiyonu, politika ve referans oranının logaritmasıyla ifade edilebilir. Bu sayede RL'nin amacını koruyup döngüyü kaldırır.

Bölüm 70'te not ettiğimiz tuzak burada da geçerlidir: tercih verisi küçük ve dar olduğunda model, bu verinin tonunu öğrenir ve genel yeteneğini kaybedebilir. Pekiştirmeli öğrenmenin bize öğrettiği dersle bunu bağlayalım: ödül (ya da tercih) ne kadar dar ve vekil ise, politika onu o kadar yanlış optimize edebilir. Bu yüzden dil modelleri için de sınırlı güncellemeler (KL cezası), referans politikaya yakınlık ve değerlendirme seti üzerinde genel yeteneğin takibi zorunludur.

::: baglanti
RLHF'de PPO, Bölüm 74.10'da anlattığımız kırpılmış vekil amacı kullanır. Dil modelindeki oran `π_θ(y | x) / π_referans(y | x)` olur ve kırpma, modelin referanstan çok uzaklaşmasını engeller. Bölüm 71.7'deki güvenlik ve sızıntı tartışması, bu ödül vekilinin kötüye kullanılmasının dil modelindeki karşılığıdır.
:::

Bu bölümde dil modeli üzerinde bir RLHF ya da DPO deneyi yapmadık. Bu konuyu bir köprü olarak ele aldık: pekiştirmeli öğrenmenin kavramları (ödül, politika, KL kısıtı, vekil ödül) dil modellerinin hizalanmasında doğrudan yeniden kullanılır.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, zorluk sırasıyla ★, ★★, ★★ ve ★★★ olarak dizilmiştir. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntüyü bul, iyileştir ve doğrula. Doğrulama adımında elle iz sürme tablosu bulunur.

### Örnek 1 (★): İki durumlu bir zincirde V^π'nin elle hesabı

İki durum var: `A` ve `B`. Tek bir eylem var: "git". Geçişler deterministik: `A → B` ödül `+2`, `B → A` ödül `0`. İndirim `γ = 0,5`. Bu politika altında `V^π(A)` ve `V^π(B)` değerlerini bul.

**Adım 1 — Anla.** Bir bölüm `A`'dan başlar, `B`'ye geçer, `A`'ya döner ve böyle sonsuza kadar sürer. Bulmamız gereken iki sayı var: her durumun beklenen indirimli getirisi. Bellman beklenti denkleminin (74.3) bu tekrarlı yapı için yazılmış hâli bize iki denklem verir.

**Adım 2 — Örnekle.** `A`'dan başlayan bir yörünge: `A → B → A → B ...`, ödüller `2, 0, 2, 0, ...`. Getiri `G = 2 + 0,5·0 + 0,25·2 + 0,125·0 + ...`. Yani `G(A) = 2 + 0,25·2 + 0,25²·2 + ... = 2 / (1 − 0,25) = 2,667`. Bu, sayıyı tahmin etmek için bir kontrol noktasıdır.

**Adım 3 — Kaba çöz.** Bellman'ı yinelemeli olarak uygula, `V_0 = (0, 0)` ile başla: `V(A) ← 2 + 0,5 V(B)` ve `V(B) ← 0,5 V(A)`. Her satırda güncellemeyi eski değerlerle yap.

**Adım 4 — Örüntü.** İki denklem açıkça yazılınca bir doğrusal sistem olur:

V(A) = 2 + 0,5 V(B)
V(B) = 0,5 V(A)

İkinci denklemi birinciye koy: `V(A) = 2 + 0,25 V(A)`, yani `V(A) = 2 / (1 − γ²) = 2 / 0,75`. Ardından `V(B) = V(A) / 2`.

**Adım 5 — İyileştir.** Matris biçimi `(I − γP) V = R`'dir. Burada `P = [[0, 1], [1, 0]]`, `R = [2, 0]`:

[[1, −0,5], [−0,5, 1]] · [V(A), V(B)] = [2, 0]

Determinant `1 − 0,25 = 0,75`. Ters matrisle `V = (1/0,75) [[1, 0,5], [0,5, 1]] [2, 0] = [2,667, 1,333]`. Bu, Bölüm 48'deki 2×2 çözümle aynıdır; `solve` ile çözmek de aynı sonucu verir.

**Adım 6 — Doğrula.** Değerleri Bellman'a geri koy: `V(A) = 2 + 0,5·1,333 = 2,667` ✓; `V(B) = 0,5·2,667 = 1,333` ✓. İterasyon izi, kaba çözümün `V`'ye nasıl yakınsadığını gösterir:

| k | V(A) | V(B) |
|---|---|---|
| 0 | 0,000 | 0,000 |
| 1 | 2,000 | 0,000 |
| 2 | 2,000 | 1,000 |
| 3 | 2,500 | 1,000 |
| 4 | 2,500 | 1,250 |
| 5 | 2,625 | 1,250 |
| 6 | 2,625 | 1,313 |

Değerler `(2,667, 1,333)`'e yakınsıyor ve her adımda `γ = 0,5` ile büzülüyor.

**Bunu AI'sız yazabilir misin?** Üç durumlu bir zincir (`A → B → C → A`, ödüller sırasıyla `1, 0, 3`, `γ = 0,9`) için `V^π`'yi iki yolla (doğrusal sistem ve yinelemeli çözüm) hesapla ve sonuçların uyduğunu göster.

### Örnek 2 (★★): 3×3 ızgarada değer iterasyonunun elle izlenmesi

3×3 deterministik bir ızgara düşün. Her hareket `−1` öder. Sağ alt köşe `(2, 2)` mutlak bir hedeftir (değeri 0). `γ = 0,9`. Değer iterasyonu ile `V_1, V_2, V_3` değerlerini hesapla ve Bellman optimallik denklemini sağlayıp sağlamadığını kontrol et.

**Adım 1 — Anla.** Her hücrenin değeri, komşularından birine gidip oradan devam etmenin en iyi getirisidir. Hedefe yakın hücreler daha yüksek (daha az negatif) değer alır. Üç iterasyon, hedeften iki komşuluk uzaklığa kadar bilgi yayılmasını gösterir.

**Adım 2 — Örnekle.** Hedefe bitişik `(1, 2)` hücresini düşün. Tek adımda hedefe gider: `−1 + 0,9·0 = −1`. `(0, 0)` ise en az dört adım uzakta; ama bu sayı yalnızca değer iterasyonu ilerledikçe ortaya çıkar.

**Adım 3 — Kaba çöz.** `V_0 = 0` (her yerde). Her iterasyonda her hücre için dört eylemin `−1 + 0,9·V_{k−1}(komşu)` değerinin maksimumunu al; hedef hücre sabit `0`'dır.

**Adım 4 — Örüntü.** `V_1` her yerde `−1`'dir, çünkü `V_0 = 0`. `V_2`'de hedefe bitişik hücreler `−1`'de kalır, diğerleri `−1 + 0,9·(−1) = −1,9` olur. Yani her iterasyonda bilgi bir komşuluk daha yayılır ve değerler `−1`, `−1,9`, `−2,71` diye kademe kademe artar. Dikkat et: bu, `γ = 0,9`'un her kademede çarpan olarak girmesinden gelir.

**Adım 5 — İyileştir.** Bunu bir tabloya yazarak ilerleyelim:

| k | (0,0) | (0,1) | (0,2) | (1,0) | (1,1) | (1,2) | (2,0) | (2,1) |
|---|---|---|---|---|---|---|---|---|
| 1 | −1,00 | −1,00 | −1,00 | −1,00 | −1,00 | −1,00 | −1,00 | −1,00 |
| 2 | −1,90 | −1,90 | −1,90 | −1,90 | −1,90 | −1,00 | −1,90 | −1,00 |
| 3 | −2,71 | −2,71 | −1,90 | −2,71 | −1,90 | −1,00 | −1,90 | −1,00 |

**Adım 6 — Doğrula.** Her hücre için Bellman'ı yeniden kontrol et. `V_3(0, 0) = −2,71`: en iyi eylem `(0, 1)` ya da `(1, 0)`'a gitmek, her ikisinin de `V_2 = −1,90` değeri var: `−1 + 0,9·(−1,90) = −2,71` ✓. `V_3(1, 1) = −1,90`: en iyi komşu `(1, 2)` (`V_2 = −1,00`) veya `(2, 1)`: `−1 + 0,9·(−1,00) = −1,90` ✓. Tabloda her hücre, bir önceki iterasyonun komşusuna bağlı olarak doğru kademede artmıştır. Aynı güncelleme, Bölüm 74.4'teki `dp74.py` içindeki `deger_iterasyonu` fonksiyonunun yaptığı iştir; 3×3 ızgarayı bu fonksiyona verip üç iterasyon sonrasını kendi tablonla karşılaştırmak iyi bir kontroldür.

**Bunu AI'sız yazabilir misin?** Aynı ızgarada hedefi sol üst köşeye taşı ve `V_3`'ü elle hesapla. Sonra hedefi bir hücre kaydır ve hangi hücrelerin değerinin değişmeden kaldığını açıkla.

### Örnek 3 (★★): Aynı geçiş dizisinde SARSA ve Q-learning güncellemelerinin farkı

Bir ajan `S1` durumunda `a1` eylemini seçip `S2`'ye geçiyor ve `−1` ödül alıyor. `S2`'de iki eylem var: `sağ` ve `sol`. Mevcut tahminler `Q(S2, sağ) = 4`, `Q(S2, sol) = 1`. Ajan bu adımda keşif yapar ve `sol`'u seçer. `α = 0,5`, `γ = 0,9`, başlangıçta `Q(S1, a1) = 0`. SARSA ve Q-learning'in `Q(S1, a1)` için yaptığı güncellemeleri karşılaştır.

**Adım 1 — Anla.** İki algoritma aynı geçişi görüyor. Fark, hedefte `Q(S2, ·)` için hangi değerin kullanıldığında yatıyor: SARSA gerçekte seçilen `sol` eylemini, Q-learning ise en büyük `sağ` eylemini kullanır.

**Adım 2 — Örnekle.** Bu adımda `S2`'de gerçekte ne yapıldığını bil: `sol`. SARSA'nın hedefi `r + γ Q(S2, sol)`, Q-learning'in hedefi `r + γ max Q(S2, ·)`.

**Adım 3 — Kaba çöz.** Her iki hedef de tek bir sayıdır. SARSA: `−1 + 0,9·1 = −0,1`. Q-learning: `−1 + 0,9·4 = 2,6`.

**Adım 4 — Örüntü.** Güncelleme her iki yöntemde de `Q ← Q + α (hedef − Q)` biçimindedir. Fark tek bir terimde: SARSA'da `Q(S2, sol)`, Q-learning'de `max`. Bu da Q-learning'in, ajanın o anda yaptığı keşif hatasını yok sayıp "en iyi olası gelecek"i öğrendiğini gösterir.

**Adım 5 — İyileştir.** Güncellemeleri uygula:
- Q-learning: `Q(S1, a1) = 0 + 0,5 (2,6 − 0) = 1,3`
- SARSA: `Q(S1, a1) = 0 + 0,5 (−0,1 − 0) = −0,05`

Q-learning, `S1`'deki eylemi bir "iyi" eylem olarak puanlar; çünkü yanındaki `S2`'de (ajanın bilmediği) bir sağ eylem vardır. SARSA ise yalnızca gerçekten yapılan `sol`'u görür ve eylemi zayıf bulur.

**Adım 6 — Doğrula.** İz tablosu:

| Yöntem | Hedef | Güncelleme formülü | Yeni Q(S1, a1) |
|---|---|---|---|
| Q-learning | −1 + 0,9·max(4, 1) = 2,6 | 0 + 0,5·(2,6 − 0) | 1,30 |
| SARSA | −1 + 0,9·Q(S2, sol) = −0,1 | 0 + 0,5·(−0,1 − 0) | −0,05 |

Hedefleri elle kontrol ettik: `max(4, 1) = 4`, `4 · 0,9 = 3,6`, `3,6 − 1 = 2,6` ✓; `1 · 0,9 = 0,9`, `0,9 − 1 = −0,1` ✓. Bu, uçurum yürüyüşündeki (74.6) davranış farkının kaynağıdır: Q-learning kenarda yürümeyi "ucuz" görür, SARSA görmez.

**Bunu AI'sız yazabilir misin?** Aynı durumda `S2`'de ajan `sağ`'ı seçseydi SARSA'nın ve Q-learning'in güncellemelerinin neden aynı çıkacağını açıkla. Bu, iki yöntemin hangi koşulda ayrıştığını gösterir.

### Örnek 4 (★★★): PPO kırpılmış amacının elle hesabı ve gradyanın sıfırlandığı bölgeler

Bir PPO partisinde dört örnek var. Her örnek için oran `r = π_θ(a|s)/π_eski(a|s)` ve avantaj `A` verildi. Kırpma `ε = 0,2`. Her örnek için vekil amacı, `∂L/∂r` gradyanını ve gradyanın sıfırlanıp sıfırlanmadığını belirle. Örnekler: `(r, A) = (0,5; +2)`, `(1,5; +2)`, `(0,5; −2)`, `(1,5; −2)`.

**Adım 1 — Anla.** Her örnek için `L = min(r A, clip(r, 0,8, 1,2) A)`. Minimumun hangi terimden geldiğine bağlı olarak gradyan ya `A` (kırpılmamış) ya da `0` (kırpılmış) olur. Soru, hangi örneklerde hangisinin olduğudur.

**Adım 2 — Örnekle.** `(0,5; +2)` için: `r A = 1,0`; `clip(0,5) = 0,8`, `0,8·2 = 1,6`. Hangisi daha küçük? `1,0 < 1,6`, minimum kırpılmamış terim.

**Adım 3 — Kaba çöz.** Dört örneği aynı kalıpla hesapla. Tablo, her örneğin ham terimini, kırpılmış terimini ve minimumu verir.

**Adım 4 — Örüntü.** Kural: `A > 0` ve `r > 1 + ε` ise kırpılmış terim `(1 + ε) A` ham terim `r A`'dan küçük kalır ve minimum onu seçer; gradyan sıfırdır. `A < 0` ve `r < 1 − ε` ise kırpılmış terim `(1 − ε) A` (negatif olduğu için) ham terimden küçük kalır ve minimum onu seçer; gradyan yine sıfırdır. Yani gradyanın sıfırlandığı iki bölge vardır: iyi eylemin olasılığı zaten fazla arttıysa ve kötü eylemin olasılığı zaten fazla düştüyse. Bunlar, politikayı zaten "yeterince" değiştirmiş örneklerdir.

**Adım 5 — İyileştir.** Tabloyu doldur:

| (r, A) | r·A | clip(r)·A | min | Kırpılmış mı? | ∂L/∂r |
|---|---|---|---|---|---|
| (0,5; +2) | 1,0 | 1,6 | 1,0 | hayır | +2 |
| (1,5; +2) | 3,0 | 2,4 | 2,4 | evet | 0 |
| (0,5; −2) | −1,0 | −1,6 | −1,6 | evet | 0 |
| (1,5; −2) | −3,0 | −2,4 | −3,0 | hayır | −2 |

Üçüncü ve dördüncü satırlar simetriktir: `A < 0`'da `r = 0,5` kırpılır (çünkü `r A = −1,0 > −1,6`, kırpılmış değer minimum olur), `r = 1,5` kırpılmaz (`r A = −3,0 < −2,4`).

**Adım 6 — Doğrula.** Her satırın minimumunu iki kez kontrol et: `min(1,0; 1,6) = 1,0` ✓; `min(3,0; 2,4) = 2,4` ✓; `min(−1,0; −1,6) = −1,6` ✓; `min(−3,0; −2,4) = −3,0` ✓. Gradyan kontrolü: kırpılmamış satırlarda `∂(r A)/∂r = A`, yani `+2` ve `−2`. Kırpılmış satırlarda minimum sabit bir terim olduğu için `0`. Bu partide iki örnek (`r = 0,5, A = +2` ve `r = 1,5, A = −2`) gradyana katkı verir; diğer ikisi sıfırdır. Bölgeyi çizgiyle görmek için Şekil 74.8'e bak.

**Bunu AI'sız yazabilir misin?** `ε = 0,1` ve `(r, A) = (1,05; +1)`, `(0,95; −1)`, `(1,25; +3)` için kırpılma durumunu ve gradyanı belirle. Hangi örnek bir sınırın hemen öte yanında olduğunu ve neden bu örneğin gradyana sıfır katkı verdiğini açıkla.

## Kendin Yap Projeleri

::: dikkat
Bu iki projede önce kendi çözümünü yaz. Yapay zekâ aracını yalnızca bitirdikten sonra kodu okumak ya da bir hatayı bulmak için kullan. Bu bölümü geçmek için değil, bu bölümü öğrenmek için yapıyorsun.
:::

### Proje 1 (★★): Kendi irtifa ortamın için bir PID–PPO karşılaştırma raporu

**Amaç.** Bu bölümdeki `IhaIrtifa` ortamını kullanarak kendi PID denetleyicini, kendi PPO'nu ve bir alan rastgeleleştirme (domain randomization) eğitimini yaz. Hepsini aynı ölçütle karşılaştıran ve beş tohumlu bir rapor üret.

**Yapılacak ve beklenen davranış.** Kontrolcün her bölümde 400 adım boyunca irtifayı `h_ref = 10 m`'de tutmalı. Başarı, zemine düşmeme ve son 10 saniyede `max|e| ≤ 1 m` olarak tanımlanır. Rapor, nominal ortamda ve `α = 0, 0,25, 0,5, 0,75, 1` kayma seviyelerinde başarı oranını (100 bölüm), ortalama mutlak sapmayı (IAE) ve kontrol çabasını (`mean s²`) verir.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Önce yalnızca PID'i yaz ve nominal ortamda kazanç ayarla. Kazanç ayarını ayrı tohumlarda yap, değerlendirme tohumlarında değil. Sonra PPO'yu ekle; gözlem olarak hatanın integralini de vermek gerekebilir (PID'in integral terimi politikanın belleği olur). Kütle değişimi altında PID'in neden kalıcı hata verebileceğini ve bunun integral terimle nasıl düzeldiğini düşün.

**Başarı kriterleri.** (1) PID ve PPO'nun nominal başarı oranları ve IAE'leri raporlanmış ve tohum sapmalarıyla verilmiş olsun. (2) Kayma tarama tablosunda hangi kayma seviyesinde her kontrolcünün başarısının düştüğü belirtilmiş olsun. (3) Güvenlik kalkanı varken ve yokken, `α = 1` için yere düşme oranı ayrı ayrı raporlanmış olsun. (4) Raporda, PID'in nominal hassasiyetinin RL'den iyi olduğu (ya da olmadığı) dürüstçe yazılmış olsun.

### Proje 2 (★★★): Sıfırdan bir DQN kütüphanesi ve birim testleri

**Amaç.** `dqn74.py`'deki bileşenleri (dairesel tampon, hedef ağ, Huber kaybı, Double DQN bayrağı, ε takvimi) yeniden kullanılabilir bir kütüphane olarak düzenle ve her bileşeni birim testleriyle doğrula.

**Yapılacak ve beklenen davranış.** Kütüphane şu arayüzü sağlamalı: bir `Tampon` sınıfı (ekle, rastgele örnekle, dolu olmadan örnekleme hatası ver), bir `hedef_guncelle` işlevi (parametreleri kopyalar), bir `kayip` işlevi (Huber ve Double seçeneği). Birim testleri: tampon kapasitesi dolunca en eski öğenin üzerine yazılmalı; Huber kaybı `|x| ≤ 1` ve `|x| > 1` sınırında süreklilik göstermeli; Double DQN hedefi, standart hedeften aynı ağırlıklar ve geçişlerle ayrılmalı.

**Önerilen yaklaşım (ipucu).** Önce tamponu ve Huber kaybını yaz, her birinin testini bitir. Sonra hedef ağ güncellemesini ekle ve CartPole'da tek tohumla ilk öğrenmeyi gör. Son olarak `dqn74.py`'deki dört ablasyonu kütüphaneyle yeniden üret: sonuçların sayısal olarak yakın olması, kütüphanenin doğru olduğunun en iyi kanıtıdır.

**Başarı kriterleri.** (1) Tüm birim testleri geçsin, en az on test olsun. (2) Tam DQN'in beş tohumdaki son ortalaması, bu bölümdeki sonuçla (364,7 ± 179,4) ±50 içinde kalsın. (3) Hedef ağ yok ablasyonu, tam DQN'den istatistiksel olarak ayrışsın. (4) Rapor, her bileşenin neden gerektiğini bir ablasyonla göstersin.

### Ek Alıştırmalar

Aşağıdaki problemler kademelidir. ★ olanlar kavramı yoklar, ★★ olanlar bir türetme ya da küçük bir hesap ister, ★★★ olanlar birden çok konuyu birleştirir. Mülakat etiketli olanlar klasik sorulardır.

1. ★ Q-learning ile SARSA arasındaki farkı iki cümleyle açıkla. Hangisi on-policy, hangisi off-policy?
2. ★ Bir ödül `r = +1` ve `γ = 0,9` için sonsuz bir döngüdeki değer nedir? `γ = 0,99` için ne olur? Hangi γ'da değer 10'u aşar?
3. ★ Beş kollu bir haydutta, her kol bir kez denendikten sonra UCB1'in hangi kolu seçeceğini ve neden olduğunu açıkla.
4. ★★ Üç durumlu bir zincirde `A → B` (ödül 0), `B → C` (ödül 1), `C` terminal (ödül 0), `γ = 1`. `V(A)` ve `V(B)` nedir? (Mülakat)
5. ★★ Politika gradyanı teoreminde `E[∇ log π(a|s) · b(s)] = 0` özdeşliğini `Σ_a ∇π = 0` ile türet. Bu özdeşlik olmadan taban çizgisi neden kullanılamazdı?
6. ★★ Bir DQN tamponunda kapasite 50 000, batch 64 ve ajan her adımda bir gradyan adımı atıyor. Bir geçişin ortalama kaç gradyan adımında kullanıldığını hesapla (tamponun doluluk durumunu tam doldu varsay). (Mülakat)
7. ★★ Double DQN'de hedef `r + γ Q(s', argmax_a Q(s', a; θ); θ⁻)` yazılır. Eğer `θ⁻ = θ` olursa bu hedef standart DQN hedefiyle aynı mıdır? Neden?
8. ★★ Bir PPO partisinde `ε = 0,2`, `A = −1` ve `r = 0,7` olan bir örnek var. Vekil amaç nedir ve gradyan sıfır mıdır? (Mülakat)
9. ★★ GAE'de `λ = 0` ve `λ = 1` durumlarında avantaj kestirimi neye karşılık gelir? Hangi uç yanlı, hangisi yüksek varyanslıdır?
10. ★★★ Bir İHA irtifa ortamında ödülü `−(e² + 0,1 s²)` ve çarpma cezasını `−100` alan bir ajan, ilk eğitimde zemine çarpmayı öğrenebilir. Bunu, bir bölümde kalmanın beklenen toplam cezası ile çarpmanın toplam cezasını karşılaştırarak açıkla. Ödülü nasıl tasarlarsın?
11. ★★★ Bir politikanın eğitim sonuçları beş tohumda `[500, 173, 488, 163, 500]`. Bu sonuçlar için bir güven aralığı yaklaşık olarak nasıl kurulur? Bootstrap yöntemi (Bölüm 57.11) bu küçük örneklemde neden dikkatli kullanılmalıdır?
12. ★★★ Baird'in karşı örneğinde güncellemeleri düzgün dağılım yerine politika içi dağılımla yaparsan ne olur? Bu, ölümcül üçlünün hangi ayağını ortadan kaldırır ve neden?

## Kod Okuma Egzersizi: PyTorch'ta politika log olasılığı

Bu bölümde politika gradyanını kendi elimizle kurduk; `log π(a|s)` terimi, REINFORCE ve PPO kaybının her yerinde var. Şimdi bu terimin gerçek bir kütüphanede nasıl hesaplandığına bakalım. Kaynak, kurulu PyTorch 2.6.0+cu124 sürümünün `torch/distributions/categorical.py` dosyasıdır (yerel yol `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\torch\distributions\categorical.py`). Aşağıdaki iki yöntem dosyadan birebir alınmıştır: `sample` (satır 130–135) ve `log_prob` (satır 137–143). Yalnızca bir satır, sayfa genişliğine sığması için parantezlerle iki satıra bölündü; anlamı değişmedi.

```python
def sample(self, sample_shape=torch.Size()):
    if not isinstance(sample_shape, torch.Size):
        sample_shape = torch.Size(sample_shape)
    probs_2d = self.probs.reshape(-1, self._num_events)
    samples_2d = torch.multinomial(
        probs_2d, sample_shape.numel(), True
    ).T
    return samples_2d.reshape(self._extended_shape(sample_shape))

def log_prob(self, value):
    if self._validate_args:
        self._validate_sample(value)
    value = value.long().unsqueeze(-1)
    value, log_pmf = torch.broadcast_tensors(value, self.logits)
    value = value[..., :1]
    return log_pmf.gather(-1, value).squeeze(-1)
```

**Sorular — cevaplamadan geçme:**

1. `__init__` içinde `logits` verildiğinde `self.logits = logits - logits.logsumexp(dim=-1, keepdim=True)` yazılır. Bu normalizasyon neden gereklidir ve `log_prob`'un döndürdüğü değeri nasıl etkiler?
2. `log_prob` içinde `value.long().unsqueeze(-1)` ve `broadcast_tensors` neden gerekli? Örneğin `value` şekli `(64,)`, `logits` şekli `(64, 2)` ise hangi şekiller oluşur?
3. `gather(-1, value)` işlemi, `log_pmf` üzerinde tam olarak hangi öğeyi seçer? Bu bölümdeki `Politika.dagilim` çağrısı için `lp = d.log_prob(a)` ifadesinde neden `sum` almadık?
4. `sample` `torch.multinomial` kullanır, yani örneklemeyi `probs` üzerinden yapar. Bu, bölümdeki `REINFORCE` kodunda `log_prob`'un neden `sample`'dan ayrı hesaplandığını nasıl açıklar?
5. Dosyanın `log_prob`'unda `_validate_args` denetimi var. Eğitim döngüsünde bu denetimi açık tutmanın bir maliyeti var mı? Bu maliyeti bir sayıyla tahmin etmeye çalış.
6. Bu kod, politika gradyanında `∇ log π` ifadesinin otomatik türevi için ne sağlar? `log_prob`'un çıktısı bir tensör olduğu için hangi işlem, Bölüm 65.5'teki `backward`'ı mümkün kılar?

## Bölüm Özeti

- Pekiştirmeli öğrenme, bir ajanın bir ortamla etkileşerek indirimli toplam ödülü en büyüttüğü bir problemdir. Denetimli öğrenmeden farkı gecikmeli ödül, politikaya bağlı veri, keşif zorunluluğu ve ödül tasarımıdır.
- Çok kollu haydutta keşif–sömürü ikilemi pişmanlıkla ölçülür. ε-açgözlü doğrusal pişmanlık üretir; UCB1 ve Thompson örneklemesi daha iyi ama ortama göre farklı davranır. Bu ortamda Thompson en iyisiydi (ortalama 30,4), UCB1 ε-açgözlüden kötüydü.
- MDP, Bellman beklenti ve optimallik denklemleriyle tanımlanır. Politika değerlendirmesi bir doğrusal sistemdir; değer iterasyonu bir büzülme eşlemesidir ve yakınsama hızı γ ile sınırlıdır. Izgarada yakınsama bu sınırın çok altındadır; sürekli ödüllü döngüde tam olarak γ^k'dır.
- Model-serbest tahminde Monte Carlo tarafsız ama gürültülüdür; TD(0) önyüklemeli ve düşük varyanslıdır. Kontrolde SARSA on-policy, Q-learning off-policy'dir; uçurum yürüyüşünde biri güvenli, diğeri kenar boyunca yolu seçer.
- Fonksiyon yaklaşımı ile önyükleme ve politika dışı öğrenme birleşince ıraksama olabilir (ölümcül üçlü). Baird'in karşı örneğinde düzgün dağılımda ağırlık normu 10'dan 437'ye çıktı.
- DQN, replay tamponu, hedef ağ ve Huber kaybıyla bu sorunları yönetir; hedef ağı kaldırmak CartPole'da öğrenmeyi tamamen engelledi. Double DQN ile tam DQN arasındaki fark, beş tohumla anlamlı değildi.
- Politika gradyanı, log-türev hilesiyle ortamın dinamiklerine ihtiyaç duymadan gradyan verir. Ödül-öncesi getiri ve taban çizgisi varyansı azaltır. Aktör–eleştirmen ve GAE, yanlılık ile varyans arasında bir takas sunar.
- PPO, oranı `1 ± ε` içinde kırparak vekil amacın gradyanını bir güven eşiği içinde tutar. Entropi ve değer terimleri eklenir; sürekli eylemler için Gauss politikası kullanılır.
- İHA irtifa ortamında nominal ayarlı PID, kütle, sürükleme ve itki değiştiğinde (α = 0,75) çöktü; integral terimli bir PID ise PPO ile aynı başarı aralığına ulaştı. Nominal koşulda PPO'nun sapması PID'nin yaklaşık yarısıydı. Alan rastgeleleştirmenin başarı oranına katkısı görülmedi; sapmayı, özellikle uç koşulda, biraz azalttı. α = 1'de hiçbir kontrolcü başarılı olmadı, çünkü gerekli itki sınırın üstüne çıktı. Güvenlik kalkanı bu deneyde hiç devreye girmedi ve etkisi ölçülmedi.
- Ödül tasarımı, ajanın istenmeyen davranışlar bulmasına yol açabilir: sınırsız tekrarlanan bir ödül ya da kendini öldürmenin daha ucuz olduğu bir ceza yapısı, bunun iki örneğidir.

**Sonraki bölümde:** Bölüm 75, Kısım XVI'nın ilk bölümü olan Verimli Çıkarım ve Edge'e geçiyor. Bu bölümde gördüğümüz küçük bir PPO politikasının bile gerçek bir İHA'da uçuş kontrolcüsü olarak çalıştırılması, hesaplama ve bellek bütçesini zorlar. Quantization, pruning, distillation, ONNX ve TensorRT gibi araçlarla, Bölüm 46'daki TinyML'in ve Bölüm 65'teki PyTorch çıkarım fikirlerinin ötesine geçeceğiz. Bu bölümdeki politikanın boyutunun (birkaç bin parametre) gömülü bir işlemcide nasıl çalıştığını, Bölüm 75'in ilk ölçümüyle göreceksin.

::: mulakat
1. Politika gradyanı teoremini log-türev hilesiyle türetir misin? Taban çizgisi neden beklentiyi değiştirmez?
2. Değer iterasyonunun yakınsamasını büzülme eşlemesiyle açıkla. Hangi koşullarda yakınsama `γ`'dan çok daha hızlıdır?
3. DQN'de hedef ağ ve replay tamponu neden birlikte gerekir? Biri olmadan hangi sorun ortaya çıkar?
4. PPO'nun kırpılmış amacı neden minimum alır? Kırpmanın gradyanı sıfırladığı iki bölgeyi tarif et.
5. Model-serbest bir RL ajanını gerçek bir İHA'da eğitmeden önce hangi üç güvenlik ve doğrulama adımını uygularsın?
6. Sim-to-real boşluğu nedir? Alan rastgeleleştirme bu boşluğu nasıl kapatmaya çalışır ve neden her zaman yeterli olmaz?
7. RLHF ile DPO'nun ortak fikri nedir? Tercih verisi neden küçük ve dar olduğunda modelin genel yeteneğini kaybetmesine yol açabilir?
8. Bir RL sonucunu raporlarken hangi üç ölçütü (tohum sayısı, değerlendirme tohumlarının ayrılması, bir baz çizgi) mutlaka verirsin ve neden?
:::
