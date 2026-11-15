# Mühendis El Kitabı — Haiku Denetimi ve Yeni Üretim Hattı Raporu

Tarih: 18 Ekim 2026 · Kapsam: Bölüm 1–10 (yazılmış olanların tamamı)

## 1. Temel soru: Kitabı okuyan biri yapay zekâ olmadan ayakta kalabilir mi?

**Cevap: Şu an HAYIR.** Haiku denetimi öncesindeki durumda bile değildi; onarımdan sonra yazılan 10 bölüm büyük ölçüde bu standarda yaklaştı. Ama kitabın bütünü için cevap hâlâ hayır, çünkü:

1. **Kapsam:** 64 bölümün yalnızca 10'u yazıldı (Kısım I–II tam, Kısım III'te 4/5 bölüm). Ağ, işletim sistemi, veritabanı, sistem tasarımı, gömülü/savunma, ML gibi Mert'in mesleğini doğrudan belirleyen kısımlar henüz yok.
2. **Denetim öncesi kalite açıkları** (aşağıda §3): çözümlü örneklerde düşünme süreci (6 adım + iz tablosu) yoktu, alıştırma hacmi düşüktü, olgusal hatalar ve tanımsız davranış (UB) yanlış adlandırmaları vardı, Kod Okuma bölümleri kaynak/sürüm vermiyordu.
3. **Bağımsızlık ölçütü** yalnızca "bilgi"yle değil, **çözülmemiş problem hacmiyle** kazanılır. Her bölüme 10–12 cevapsız, kademeli alıştırma (`Ek Alıştırmalar`) zorunlu hâle getirildi; bu, kitabın AI'sız çalışmayı öğretme iddiasının belkemiği.

Baştan yazma **gerekmedi**: mevcut bölümlerin iskeleti ve pedagojisi sağlamdı; sorunlar onarılabilir türdendi. Karar: **onar + kaldığı yerden devam et.**

## 2. Yöntem

| Adım | Kim | Ne yapıldı |
|---|---|---|
| Denetim | 9 Haiku ajanı (bölüm başına 1) | Bölümü baştan sona okuyup 10 puanlık ölçütle puanladı: doğruluk, AI'sız uygulanabilirlik, örnek süreç kalitesi, alıştırma hacmi, kaynak dürüstlüğü, dizgi |
| Doğrulama | Opus | Bildirilen her hatayı kaynakla karşılaştırdı; yanlış alarmlar elendi |
| Sözleşme | Opus | `docs/MASTER_PROMPT.md` — kitabı sıfırdan yazdırabilecek, kendi kendine yeten yazar sözleşmesi |
| Onarım | Haiku düzelticiler (2 tur) | Doğrulanmış hatalar + yeni zorunlu yapılar (6 adım, iz tablosu, Ek Alıştırmalar) |
| Pilot | Haiku yazar | Bölüm 10 (Tree) sıfırdan, MASTER_PROMPT'a göre |
| Son denetim | Opus | Kontak sayfaları, diyagram yakın bakışı, olgu taraması, otomatik dizgi denetçileri |

## 3. Denetim puanları (onarım öncesi)

| Bölüm | Konu | Puan | Öne çıkan bulgular |
|---|---|---|---|
| 1 | Bilgisayar nasıl çalışır | 4/10 | Endianness örneğinde hız sayısı yanlış yorum; Şekil 1.6 PC'nin ilerleme anını metinle çelişik anlatıyordu |
| 2 | C temelleri | 6/10 | `qsort` ikinci sıralama çıktısı yoktu; Kod Okuma kaynaksız, K&R kesiti gerçek kaynakmış gibi |
| 3 | Python temelleri | 6/10 | `list_resize` kesitinde tanımsız değişkenler, sürüm yok |
| 4 | Linux/Bash/Git/derleme | 5/10 | `tar`, `date`, `$(...)` öğretilmeden kullanılıyordu; Redis kaynağı sürümsüz |
| 5 | Problemi parçala | 6/10 | Tarih iddiası kaynaksız; örnekler 6 adımı açıkça göstermiyordu |
| 6 | Debugging | 5/10 | `ayristir()` tanımsız; KLOG kurgu kaynak gerçekmiş gibi sunuluyordu |
| 7 | Array & Linked List | 5/10 | Java `ArrayList` büyüme katsayısı ×2 (doğrusu ×1,5); list.h sürümsüz |
| 8 | Stack & Queue | 6/10 | C kesitlerinde eksik `#include` |
| 9 | Hash Table | 6/10 | Java treeify koşulu eksik (≥8 zincir **ve** ≥64 tablo); rehash ifadesi belirsiz |
| **Ort.** | | **≈5,4** | |

Ortak zaaflar: örneklerde düşünme süreci görünmüyordu, alıştırmalar azdı, C'de UB "hata" diye geçiştiriliyordu, Windows/WSL notları eksikti, Kod Okuma'da gerçek dosya yolu + sürüm yoktu.

## 4. MASTER_PROMPT v2 (docs/MASTER_PROMPT.md)

Kitabı tek başına yeniden yazdırabilecek sözleşme. İçeriği: amaç ve okur profili, 1–64 bölüm listesi ve alt konular, zorunlu bölüm yapısı, üslup, Markdown sözdizimi, dizgi kuralları (öksüz başlık yasağı, tanıtım-blok yapışması, kod ≤70 / terminal ≤74 karakter), diyagram kuralları, derleme/denetim komutları ve **§8b Sert Kurallar v2**:

1. Her çözümlü örnek: **Adım 1 Anla → 2 Örnekle → 3 Kaba çöz → 4 Planla → 5 İyileştir → 6 Doğrula**, Adım 6'da iz tablosu; zorluk sırası ★, ★★, ★★, ★★★.
2. C'de tanımsız davranış doğru adıyla anılır.
3. Windows (LLP64) / WSL2 farkları belirtilir.
4. Mimari farklar (x86 / ARM) gerektiğinde belirtilir.
5. Kod Okuma: gerçek yol + sürüm; sadeleştirme açıkça işaretlenir; uydurma alıntı yok.
6. Sayılar tohumla tekrarlanabilir.
7. Kod derlenebilir; terminal çıktısı `printf` ile birebir.
8. Kütüphane gerçekleri (Java ×1,5, treeify ≥8 & ≥64, `qsort` kararsız, `strdup` POSIX/C23, Python sürüm farkları).
9. Kendin Yap sonunda **10–12 cevapsız Ek Alıştırma**.
10. Öğretilmemiş kavram kullanılmaz.

## 5. Onarım sonuçları

**Tur 1 (geniş onarım):** 9 bölüme 6 adım + iz tabloları, Ek Alıştırmalar, doğrulanmış olgu düzeltmeleri.

**Tur 2 (açık kalanlar, bugün):**

| Bölüm | Düzeltme | Opus doğrulaması |
|---|---|---|
| 1 | Şekil 1.6 açıklaması: PC getirme aşamasında ilerler, dallanma yürütmede üzerine yazar | Opus yaptı |
| 1 | Proje 2 ipuçları mantıksal sıraya (temel → döngü → kenar durumlar) | ✓ |
| 2 | Kod Okuma: Linux v6.6 `lib/string.c` gerçek `strlen`/`strcpy` (sadeleştirme işaretli) | ✓ |
| 2 | `qsort` ikinci sıralama çıktısı WSL'de (glibc 2.39, gcc 13.3) gerçekten çalıştırılıp eklendi; kararlılık notu glibc'ye özgü | ✓ |
| 3 | `list_resize`: CPython 3.12.10'dan, formül birebir, tüm değişkenler tanımlı; "sıkıştırır" yazımı | ✓ formül gerçek kaynakla aynı |
| 4 | Yeni alt başlık: `$(...)`, `date`, `tar`; Redis 7.2 `src/Makefile` (sadeleştirilmiş) | ✓ |
| 5 | Haiku "2006"yı belirsizleştirmişti → Opus kesin bilgiyi geri koydu: Bloch 2006, hata Java'da ~9 yıl fark edilmedi | Opus düzeltti |
| 6 | `ayristir()` okura bırakılan imzayla tanımlandı; KLOG "öğretici kurgu" diye işaretlendi; glibc 2.39 `assert/assert.h` | ✓ |
| 7 | Linux 6.6 LTS `list.h`, çıkarılan `__list_add_valid`/`WRITE_ONCE` belirtildi | ✓ |
| 8 | Eksik `#include`'lar | ✓ |
| 9 | Rehash: zincirleme α>0,75, açık adresleme α>0,66, M→2M; kodla tutarlı (M=16'da 13. eleman) | ✓ hesap doğru |
| 10 | `heapq` max-heap fonksiyonlarının Python 3.14'te kamuya açıldığı notu | Opus yaptı |

## 6. Pilot: Bölüm 10 (Tree), Haiku yazdı

- 938 satır, 10 diyagram, 39 sayfa; C kodu WSL'de ASan/UBSan ile derlendi.
- İçerik: terminoloji, gezinmeler, BST, dengesizlik, AVL (LL/RR/LR/RL), heap + heapify O(n), öncelik kuyruğu/`heapq`; Kod Okuma CPython 3.12 `Lib/heapq.py`.
- **Opus bulguları:** AVL rotasyon ve heap diyagramları doğru; 1,44·log₂n sınırı doğru; bir güncellik hatası (heapq/3.14) düzeltildi. Dizgi kurallara uygun, ancak Haiku uzun kod bloklarını peş peşe koyduğu için 17. sayfada yarım sayfa boşluk var. Kural ihlali değil, estetik bir bedel.
- **Sonuç:** Haiku, MASTER_PROMPT ile yayına yakın bölüm üretebiliyor; ama sürüm/olgu iddialarında **Opus denetimi şart** (bu turda Haiku'nun iki hatası Opus'ta yakalandı: heapq sürümü ve gereksiz yumuşatılan 2006 bilgisi).

## 7. Güncel durum

| | |
|---|---|
| Yazılan bölüm | 10 / 64 |
| Toplam sayfa | **320** (B1 30 · B2 33 · B3 36 · B4 32 · B5 33 · B6 31 · B7 30 · B8 27 · B9 29 · B10 39) |
| Dizgi denetçisi (öksüz başlık / kenar ihlali) | 10/10 temiz |
| Uzun kod satırı | 0 |
| PDF'te görünür `**` | 0 (kalanların hepsi meşru kod: `char **argv`, `2 ** 10`, `**kwargs`) |

## 8. Kalan riskler

- glibc 2.39 `assert.h` yolu ve Redis 7.2 Makefile kesiti ağ engeli yüzünden canlı doğrulanamadı; yollar bilinen gerçeklerle uyumlu, ama yayın öncesi bir kez göz atılmalı.
- 1–9. bölümlerdeki sayısal çıktıların tamamı yeniden çalıştırılmadı (yalnızca dokunulan örnekler).
- Peş peşe uzun kod blokları yer yer yarım sayfa boşluk bırakıyor; motor bunu kural gereği kabul ediyor.

## 9. Devam planı

Her bölüm için hat:

1. **Haiku yazar** (`model: haiku`): MASTER_PROMPT + önceki bölümün özeti → `bolumler/bolum_NN.md` + `engine/diagrams_bNN.py` + derleme + denetçiler.
2. **Opus denetçi:** kontak sayfası, diyagram yakın bakış, olgu/sürüm taraması, kodu çalıştırma, gerekirse Haiku'ya düzeltme listesi.
3. Bölüm başına bir tur; aynı kısım içinde en fazla 2–3 bölüm paralel (bölümler arası atıflar tutarlı kalsın diye sıralı ilerlemek daha güvenli).

Kalan iş: **54 bölüm**. Bölüm 10'un ölçüsüyle (~35 sayfa) kitap ~2200 sayfa civarına çıkar; bu, başlangıçtaki ~1700 tahmininden fazla, ama "maksimum verim" direktifiyle uyumlu.

Sıradaki: **Bölüm 11 — Graph** (Kısım III'ün son bölümü), ardından Kısım IV — Algoritmalar.
