# MASTER PROMPT — "Mühendis El Kitabı" Bölüm Yazarı

Bu dosya, kitabın bölümlerini yazan her ajanın (insan ya da model) uyması gereken
tam sözleşmedir. Kendi kendine yeterlidir: sohbet geçmişi olmadan bu dosyayı okuyan
bir yazar, kitabın geri kalanıyla tutarlı bir bölüm üretebilmelidir.

---

## 1. Kitabın amacı (her satırın hizmet ettiği hedef)

Okur **Mert**: 2-3. sınıf Bilgisayar Mühendisliği öğrencisi. AI araçlarıyla hızlı üretmeye
alışkın; bu kitapla temelini derinleştirmek, algoritma kurma ve sıfırdan kod yazma
becerisini AI'sız da sağlamlaştırmak istiyor.
Hedefi: **ML/AI uzmanlığı; savunma ve gömülü sistemler gibi yüksek güvenilirlik isteyen alanlar.**

**Kitabın tek başarı ölçütü:** Kitabı baştan sona okuyup alıştırmalarını yapan biri,
**hiçbir yapay zekâ aracı olmadan** (a) whiteboard mülakatında problemi sıfırdan
çözebilmeli, (b) boş IDE'de çalışan kod yazabilmeli, (c) gerçek bir projede hatayı
kendi bulabilmeli, (d) konuyu başkasına anlatabilmeli.

Bu yüzden: yüzeysel anlatım, "bunu internetten öğrenebilirsin", copy-paste bilgi
YASAKTIR. Her kavram "neden?" sorusuyla birlikte, ilk kez duyan ama zeki bir okura
anlatılır gibi yazılır.

Mert'in projeleri (doğal referans için, zoraki değil): **MertOS** (C/C++ işletim
sistemi, `kstring.hpp`, Command Pattern, klavye sürücüsü), **ÖZCE** (semantic
communication codec), **WakeBreaker**, **EV Dashboard** (STM32 sensör verisi),
**Sessiz Köprü** (Flutter), **Mert Studio Code** (Türkçe parser).

## 2. Bölüm listesi (16 kısım, 80 bölüm)

- **Kısım I — Programlama Temelleri:** 1 Bilgisayar Nasıl Düşünür · 2 C Dili · 3 Python (C bilene fark odaklı) · 4 Terminal & Araçlar — *YAZILDI*
- **Kısım II — Problemi Çözmeyi Öğrenmek:** 5 Problemi Parçala · 6 Debugging Sanatı — *YAZILDI*
- **Kısım III — Veri Yapıları:** 7 Array & Linked List · 8 Stack & Queue · 9 Hash Table — *YAZILDI* · **10 Tree** (traversal inorder/preorder/postorder/level-order, BST insert/delete/search, AVL rotasyon, heap min/max, priority queue, trie) · **11 Graph** (adjacency list vs matrix, weighted/unweighted, directed/undirected, "ne zaman graph düşünürüm" sezgisi, modelleme örnekleri)
- **Kısım IV — Algoritmalar:** 12 Algoritma Analizi (Big-O/Ω/Θ, amortize, best/worst/average, space, Master Theorem) · 13 Sıralama (bubble, selection, insertion, merge, quick+pivot, heap, counting, radix, stability) · 14 Arama (linear, binary + lower/upper bound, rotated array, matrix search, interpolation) · 15 Recursion & Backtracking (şablon, base case, call stack görselleştirme, N-Queens, Sudoku, subset/permutation) · 16 Dynamic Programming (memo vs tabulation, state tanımlama; Fibonacci, 0/1 & unbounded knapsack, LCS, LIS, coin change, edit distance, matrix chain, rod cutting) · 17 Graph Algoritmaları (BFS, DFS iter+rec, Dijkstra, Bellman-Ford, Floyd-Warshall, Kruskal+Union-Find, Prim, topological sort Kahn+DFS, cycle detection, connected components, bipartite) · 18 Greedy (activity selection, fractional knapsack, Huffman, MST bağlantısı, greedy choice kanıtı) · 19 Divide & Conquer (closest pair, Strassen, Master Theorem uygulaması)
- **Kısım V — OOP & Yazılım Tasarımı:** 20 OOP Temelleri (C++ ve Python paralel) · 21 SOLID · 22 Design Patterns (Factory, Singleton, Builder, Adapter, Decorator, Facade, Observer, Strategy, Command, State; MertOS Command Pattern) · 23 Clean Code
- **Kısım VI — İşletim Sistemi & Mimari:** 24 CPU Mimarisi · 25 Bellek Hiyerarşisi · 26 Process & Thread · 27 Senkronizasyon · 28 File System & I/O
- **Kısım VII — Ağ:** 29 OSI & TCP/IP · 30 HTTP, DNS, DHCP · 31 Socket Programming · 32 Güvenlik
- **Kısım VIII — Veritabanı:** 33 İlişkisel Model · 34 SQL Derinlemesine · 35 NoSQL
- **Kısım IX — Otomata & Derleme:** 36 Formal Diller · 37 Derleyici Nasıl Çalışır
- **Kısım X — Yazılım Mühendisliği Pratiği:** 38 Git Derinlemesine · 39 Test Yazma · 40 API Tasarımı · 41 System Design · 42 Docker & Deployment
- **Kısım XI — Gömülü Sistem:** 43 Bare-Metal C · 44 Kesme & Zamanlayıcı · 45 İletişim Protokolleri (UART/SPI/I2C) · 46 Edge AI & TinyML
- **Kısım XII — Matematik:** 47 Ayrık Matematik · 48 Lineer Cebir (vektör uzayı, matris çarpımının geometrisi, özdeğer/özvektör, SVD, normlar, NumPy ile; ML'de her yerde) · 49 Olasılık & İstatistik (dağılımlar, Bayes, beklenen değer/varyans, MLE/MAP, hipotez testi, güven aralığı, bootstrap) · 50 Optimizasyon (konveksite, gradient descent türevleri, Lagrange, kısıtlı optimizasyon) · 51 Bilgi Teorisi (entropi, çapraz entropi, KL, karşılıklı bilgi — kayıp fonksiyonlarının kökeni)
- **Kısım XIII — Sinyal & Paralel:** 52 DSP Temelleri · 53 Paralel & Eşzamanlı Programlama
- **Kısım XIV — Makine Öğrenmesi:** 54 ML'e Giriş & Pipeline (problem çerçeveleme, veri bölme, veri sızıntısı, baseline) · 55 ML için Kalkülüs & Otomatik Türev (çok değişkenli türev, gradyan, Jacobian, matris türevleri, zincir kuralı; micrograd tarzı autodiff'i sıfırdan yaz) · 56 Veriyle Çalışmak (NumPy derinlemesine/vektörleştirme/broadcasting, pandas, temizleme, eksik veri, feature engineering, dengesiz veri) · 57 Değerlendirme & Deney Tasarımı (metrikler, ROC/PR, cross-validation, bias-variance, kalibrasyon, istatistiksel anlamlılık, A/B) · 58 Doğrusal Modeller (lineer/lojistik regresyon sıfırdan, softmax, L1/L2, GLM) · 59 Ağaçlar & Ensemble (karar ağacı sıfırdan, bagging, random forest, gradient boosting, XGBoost/LightGBM; tablo verisinde neden hâlâ kral) · 60 SVM & Kernel Yöntemleri · 61 Denetimsiz Öğrenme (k-means, GMM+EM, PCA, t-SNE/UMAP, anomali tespiti) · 62 Olasılıksal Modeller & Bayesçi ML (naive Bayes, Bayes ağları, HMM, Kalman/parçacık filtresi — hedef takibi ve sensör füzyonu bağlantısı)
- **Kısım XV — Derin Öğrenme:** 63 Sinir Ağı Sıfırdan (NumPy ile MLP, backprop türetmesi) · 64 Eğitimin Sanatı (SGD/momentum/Adam/AdamW, init, BatchNorm/LayerNorm, dropout, LR schedule, eğitim hatası ayıklama: loss eğrisi okumak, overfit-tek-batch testi) · 65 PyTorch Derinlemesine (tensor, autograd, nn.Module, Dataset/DataLoader, mixed precision, checkpoint, tekrarlanabilirlik) · 66 CNN & Bilgisayarlı Görü (konvolüsyon sıfırdan, ResNet, augmentation, transfer learning) · 67 Nesne Tespiti, Segmentasyon & Takip (IoU, NMS, anchor, YOLO ailesi, U-Net, çoklu nesne takibi — İHA/savunma odaklı) · 68 Dizi Modelleri & Zaman Serisi (RNN, LSTM, GRU, TCN, sensör/telemetri verisi) · 69 Attention & Transformer (sıfırdan, satır satır; konumsal kodlama, maskeleme) · 70 NLP & Dil Modelleri (tokenization/BPE, embedding, ön-eğitim, fine-tuning, LoRA/PEFT, küçük bir GPT'yi sıfırdan eğitmek) · 71 LLM Sistemleri (prompting, RAG, değerlendirme, ajanlar/araç kullanımı, KV cache, quantization, servis etme) · 72 Üretken Modeller (autoencoder, VAE, GAN, diffusion; ÖZCE semantic codec bağlantısı) · 73 Temsil Öğrenme & Self-Supervised (contrastive learning, CLIP, çok modlu modeller) · 74 Pekiştirmeli Öğrenme (MDP, dinamik programlama, Q-learning, DQN, policy gradient, PPO, sim-to-real)
- **Kısım XVI — ML Mühendisliği & Araştırma:** 75 Verimli Çıkarım & Edge (quantization, pruning, distillation, ONNX, TensorRT, Jetson; Bölüm 46 TinyML'in devamı) · 76 GPU Programlama & Dağıtık Eğitim (CUDA temelleri, bellek hiyerarşisi, DDP/FSDP, profiling) · 77 MLOps (veri/model versiyonlama, deney takibi, CI/CD, izleme, drift) · 78 Güvenilir & Güvenli AI (adversarial saldırılar, robustness, açıklanabilirlik, belirsizlik tahmini, savunma sanayiinde doğrulama/sertifikasyon) · 79 Makale Okuma & Araştırma Yöntemi (makale okuma protokolü, yeniden üretim, ablation, deney günlüğü, yayın) · 80 Bitirme: Uçtan Uca Sistem (İHA görüntüsünden nesne tespiti → takip → edge'e dağıtım → izleme)

Bir bölüm yazarken spec'teki **her** alt konuyu kapsa. Atlarsan gerekçesini dipnotla
değil, metinde "Bölüm X'te derinleşir" diye bağlantıyla ver.

## 3. Her bölümün zorunlu yapısı (sırayla)

1. `## Giriş: <başlık>` — neden önemli, mülakatta/projede/savunma sanayiinde nerede çıkar, varsa Mert'in projesine doğal referans. 3-5 paragraf + bir `::: not` kutusu.
2. **Teori** — `## N.1 ...`, `## N.2 ...` numaralı alt bölümler (genelde 7-10 tane). Bölümün ağırlık merkezi. Her soyut kavram için somut analoji; önce basit sonra gerçek versiyon; formül/kanıt eskizleri; C ve/veya Python kodu; tablolar; en az **5-7 şekil**.
3. `## Çözümlü Örnekler` — **4 örnek**, zorluk ★ → ★★ → ★★ → ★★★. Her örnek **Bölüm 5'in altı adımını** izler: Anla → Örnekle → Kaba çöz → Örüntü → İyileştir → Doğrula. Doğrulamada **elle iz sürme tablosu** olsun. Her örnek `**Bunu AI'sız yazabilir misin?**` ile biten bir varyasyon sorusuyla kapanır.
4. `## Kendin Yap Projeleri` — önce `::: dikkat` (AI yasağı), sonra **2 proje** (★★ ve ★★★). Her projede: **Amaç**, **Yapılacak/Beklenen davranış**, **Önerilen yaklaşım** (ipucu, TAM ÇÖZÜM DEĞİL), **Başarı kriterleri** (ölçülebilir).
5. `## Kod Okuma Egzersizi` — **gerçek** bir açık kaynak projeden kısa kesit (Linux kernel, CPython, SQLite, Redis, glibc, PyTorch, TensorFlow...), kaynağı belirt, ardından `**Sorular — cevaplamadan geçme:**` ve 5-6 madde.
6. `## Bölüm Özeti` — 7-10 madde imli özet + `**Sonraki bölümde:**` geçiş paragrafı.
7. Son blok `::: mulakat` — 6-8 numaralı, **cevapsız**, düşündürücü klasik mülakat sorusu.

## 4. Üslup

- Tamamen Türkçe; teknik terim ilk geçtiğinde Türkçe + parantezde İngilizce: "yığın (stack)".
- "Sana anlatıyorum" tonu: arkadaşça ama ciddi. "Kanka" yok. "Çok basit aslında" gibi küçümseyici ifadeler YASAK.
- Zor olana zor de, sonra parçala. Kısa net cümleler. Akademik jargon minimum.
- Her konudan önce "neden önemli?" sorusu cevaplanır.
- Önceki bölümlere sık ve doğru çapraz referans ver (ör. "Bölüm 7'deki amortize analiz", "Bölüm 1'in iki'ye tümleyeni"). Bu, kitabı tek bir zihinsel model hâline getirir.
- Teknik doğruluk pazarlıksız: emin olmadığın sayı/tarih/API adı yazma; yazıyorsan doğru olsun.

## 5. Markdown sözdizimi (motorun anladığı tek dil)

Dosya başı (ön bilgi):

```
%% kisim_no: III
%% kisim_ad: Veri Yapıları
%% bolum_no: 10
%% baslik: Tree
```

Yeni bir kısmın İLK bölümüyse ayrıca `%% kisim_ayrac: evet` ekle.

| Yazım | Sonuç |
|---|---|
| `## Başlık` / `### Başlık` / `#### Başlık` | H2 / H3 / H4. H2'ler `## 10.3 Başlık` biçiminde numaralı |
| ```` ```c ```` , ```` ```python ```` , ```` ```bash ```` | satır numaralı, renkli kod kartı |
| ```` ```term ```` | koyu terminal kutusu; `$ ` ile başlayan satır komut olur |
| `::: dikkat` / `ipucu` / `baglanti` / `not` / `mulakat` ... `:::` | çağrı kutusu (içinde tek paragraf; kod bloğu KOYMA) |
| `![Şekil 10.3: açıklama](gorseller/b10_ad.png)` | şekil + açıklama (tek satır) |
| `\| a \| b \|` + `\|---\|---\|` | tablo |
| `- madde`, `1. madde` | listeler |
| `**kalın**`, `*italik*`, `` `kod` `` | satır içi |

Paragraflar arasında boş satır bırak. Paragraf satırını `- ` ya da `1. ` ile başlatma.

## 6. Sert dizgi kuralları (kırılırsa bölüm REDDEDİLİR)

- **Kod bloğu satırı ≤ 70 karakter**, terminal bloğu satırı ≤ 74 karakter. Uzunsa böl, yorumu kısalt ya da ayrı satıra al.
- Emoji kullanma (⭐ yerine metin içinde `★` serbest; motor çevirir ama temiz tut).
- Bir kod/terminal/tablo/şeklin hemen önündeki paragraf onun tanıtımıdır ("Aşağıdaki kod ...:") — motor bunları birbirine yapıştırır; tanıtımı mutlaka yaz.
- Şekil numaraları bölüm içinde ardışık: Şekil 10.1, 10.2, ...
- Tek bir kod bloğu ≤ ~40 satır. Daha uzunsa mantıklı parçalara böl, aralarına açıklama paragrafı koy.

## 7. Diyagramlar

Her bölüm için `engine/diagrams_bNN.py` dosyası yazılır. Kurallar:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)
MONO = {"family": "DejaVu Sans Mono"}
```

- **Şekil yazıları Türkçe karakterlidir** (ğ, ü, ş, ı, ö, ç, İ): "düğüm", "aşama", "ölçüm" — ASCII'leştirilmiş Türkçe ("dugum", "asama") YASAK; DejaVu Sans hepsini destekler. Dosya başında `# -*- coding: utf-8 -*-`.
- **Ölçüm verisi okuyan şekiller** veriyi `engine/veri/` altından okur; Temp dizinine bağımlı diyagram yasak (kitap yeniden üretilebilir olmalı).
- `_box(ax, x, y, w, h, metin, fill, edge, fs=..., bold=..., tcol=...)`, `_arrow(ax, x1, y1, x2, y2, col=..., lw=..., rad=...)`, `_save(fig, path)`.
- Palet: `FILL[0..4]` / `EDGE[0..4]` (arduvaz, yeşil, hardal, bordo, mor-gri), `ACCENT` bordo, `MUTED` gri, `RULE` açık çizgi, `INK` metin.
- Tipik tuval: `fig, ax = plt.subplots(figsize=(9.6, 4.0)); ax.set_xlim(0, 14); ax.set_ylim(0, 6); ax.axis("off")`.
- Metinler kutuların ve birbirlerinin ÜZERİNE BİNMEMELİ; tuval kenarından taşmamalı. Uzun yazıyı iki satıra böl.
- Matematiksel eğri gerektiğinde gerçek veriyle grafik çiz (numpy).
- Dosya adları `gorseller/bNN_<kisa_ad>.png`. `if __name__ == "__main__":` bloğunda hepsini üret.

## 8. Derleme ve doğrulama komutları

```
python engine/diagrams_bNN.py
python build/check_code_width.py bolumler/bolum_NN.md     # 0 olmalı
python build/make_bolum.py NN
python build/check_layout.py "pdf/bolum_NN_*.pdf"          # TEMİZ olmalı
```

## 8b. Denetimden çıkan SERT KURALLAR (v2 — 9 bölümlük Haiku denetiminden sonra eklendi)

Bu kurallar ilk 9 bölümde tekrar tekrar ihlal edildi; ihlal eden bölüm REDDEDİLİR.

1. **Çözümlü örneklerin her biri** şu kalın etiketleri sırayla taşır: `**Adım 1 — Anla.**`, `**Adım 2 — Örnekle.**`, `**Adım 3 — Kaba çöz.**`, `**Adım 4 — Örüntü.**`, `**Adım 5 — İyileştir.**`, `**Adım 6 — Doğrula.**` — ve Adım 6'da **mutlaka bir elle iz sürme tablosu** (markdown tablo) vardır. Zorluk sırası kesin: ★, ★★, ★★, ★★★.
2. **C'de tanımsız davranış (UB) doğru adlandırılır:** işaretli tamsayı taşması, NULL izleme, dizi sınırı dışı erişim, serbest bırakılmış bellek kullanımı UB'dir. "Negatife sarar", "anında çöker" gibi kesin sonuç vaat etme; "tipik olarak ... ama garanti değil (UB)" de.
3. **Platform farkını yaz:** Okur Windows kullanıyor. `long` Windows 64-bit'te 4 bayttır (LLP64). gdb/valgrind/ASan/core dump gibi Linux araçlarında "WSL2 içinde" notu düş.
4. **Mimari farkını yaz:** x86'ya özgü davranışları (ör. `call` dönüş adresini yığına iter) genelleme; ARM'da (STM32!) dönüş adresi LR yazmacına konur.
5. **Kod Okuma kesitleri:** gerçek dosya yolu ve proje sürümü/yılı belirt (`CPython 3.12, Objects/dictobject.c`). Sadeleştirdiysen "sadeleştirilmiş" yaz ve anlamı bozan satırı (ör. boyut güncellemesi) atma. Tırnak içinde "kaynaktaki yorum" diye uydurma alıntı YAPMA.
6. **Her sayı doğrulanabilir olmalı:** ölçüm çıktısı gösteriyorsan onu üreten kodu ve `random.seed(...)` tohumunu ver. Kaynaksız istatistik ("5-10 kat", "yarısından fazlası") yerine "tipik olarak", "ölçümüne göre değişir" de ve okura ölçtür.
7. **Kod derlenebilir olmalı:** gerekli `#include`'ları yaz (`size_t` için `<stddef.h>`), kullanılan her fonksiyon ya metinde tanımlı ya da "Bölüm X'teki ..." diye işaretli olsun. Terminal çıktısı kodun `printf`'iyle birebir eşleşsin.
8. **Kütüphane gerçekleri:** Java `ArrayList` ×1.5 büyür; Java `HashMap` treeify için zincir ≥8 VE tablo ≥64 ister; `qsort` kararlı değildir; `strdup` POSIX'tir (C23'te standart). Python sürüm farklarını belirt (ör. `heapq` max-heap fonksiyonları 3.14'te kamuya açıldı; 3.12'de `_heapify_max` özeldir). Emin olmadığın kütüphane iç ayrıntısını yazma.
9. **Pratik hacmi:** `## Kendin Yap Projeleri` bölümünün sonuna `### Ek Alıştırmalar` alt başlığı ekle: zorluk etiketli (★/★★/★★★) **10-12 cevapsız problem**, her biri 1-3 cümle, en az 4 tanesi klasik mülakat problemi. Okurun refleksi okumayla değil bu hacimle oluşur.
10. **Teoride öğretilmeyen şeyi örnekte/projede kullanma.** Projede gerekecek her komut/kavram teoride en az bir kez açıklanmış olmalı.

## 9. Kalite kontrol soruları (yazar kendine sorar, denetçi de sorar)

1. Bu bölümü okuyan konuyu gerçekten anlar mı, yoksa ezberler mi?
2. Kodları boş IDE'de yazabilir mi? (Her kodun *neden* öyle yazıldığı anlatıldı mı?)
3. Mülakatta bu konudan soru gelince cevap verebilir mi?
4. Bölüm başka kaynağa ihtiyaç duymadan kendi kendine yeterli mi?
5. Spec'teki alt konuların hepsi var mı?
6. Teknik hata var mı? (karmaşıklık, API, tarih, sayı)
