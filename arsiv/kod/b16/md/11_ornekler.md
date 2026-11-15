## Çözümlü Örnekler

Bu bölümdeki dört örnek ★ zorluğundan ★★★'e doğru ilerler. Her örnekte Bölüm 5'teki altı adımı izleyeceğiz. Adım 6'da elle iz sürme tablosu olacak; tablodaki değerler örnekte verilen programın çıktısıyla aynıdır. Çözüm kodunu okumadan önce her örneğin ilk üç adımını kendi kâğıdında dene.

### Örnek 1 (★): Engelli ızgarada yol sayma

**Problem:** `n × m` boyutunda bir ızgara var. Boş hücreler `0`, engeller `1` ile gösterilir. Sol üst köşeden sağ alt köşeye, yalnızca sağa ya da aşağı hareket ederek kaç farklı yol var? Engelli hücreden geçilemez.

**Adım 1 — Anla.** Girdi bir 0/1 matrisidir; çıktı bir sayıdır. Kenar durumlar: başlangıç ya da bitiş hücresi engelli ise cevap 0'dır; tek hücrelik ızgarada cevap 1'dir (hücre boşsa).

**Adım 2 — Örnekle.** Bu örnekte kullanacağımız ızgara 4 × 4'tür:

```
0 0 0 0
0 1 0 0
0 0 0 1
1 0 0 0
```

Bu ızgarada üç yol vardır: `DDRDRR`, `DDRRDR` ve `RRDDDR` (`D` aşağı, `R` sağa). Yolların hiçbiri `(1,1)`, `(2,3)` ya da `(3,0)` hücrelerinden geçmez.

**Adım 3 — Kaba çöz.** Her hücrede iki seçenek var: sağa ya da aşağı. Tüm dalları özyinelemeyle dene ve hedefe ulaşanları say. Bu doğrudur, ama her çağrı iki dala ayrılır; derinlik `n + m - 2` olduğu için çağrı sayısının üst sınırı `2^(n+m-2)`'dir ve aynı hücreler birçok kez hesaplanır.

**Adım 4 — Örüntü.** `(i, j)` hücresine yalnızca yukarıdan ya da soldan gelinebilir. Bu yüzden `dp[i][j]`, `dp[i-1][j]` ve `dp[i][j-1]` toplamıdır; engelli hücrede `dp[i][j] = 0`. Taban: `dp[0][0] = 1` (boşsa). Bu, Bölüm 16.2'deki protokolün tam uygulamasıdır: durum, bağıntı, taban ve sıra.

**Adım 5 — İyileştir.** Hesabı satır satır, soldan sağa, yukarıdan aşağıya yap. Her hücre yalnızca daha önce hesaplanmış iki komşuya bakar; bu yüzden tek bir döngü yeter, toplam `O(nm)`. Programın ilk kısmı tabloyu üretir, ikinci kısmı kaba kuvvetle karşılaştırır.

{{KOD:ornek1.py:1:31}}

Ana fonksiyon sabit ızgarayı çözer, tabloyu yazdırır ve 300 rastgele ızgarada kaba kuvvetle eşleşmeyi doğrular.

{{KOD:ornek1.py:32:54}}

**Adım 6 — Doğrula.** Programı çalıştırdık:

{{TERM}}
python ornek1.py ||| python ornek1.py
{{/TERM}}

Aşağıdaki tablo, `dp` matrisinin elle doldurulmuş hâlidir; satırlar `i` (0'dan 3'e), sütunlar `j` (0'dan 3'e). Programın çıktısıyla birebir aynıdır ve son hücre `3` yazar: Adım 2'deki üç yolla uyumlu.

| `i \ j` | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 1 |
| 1 | 1 | 0 (engel) | 1 | 2 |
| 2 | 1 | 1 | 2 | 0 (engel) |
| 3 | 0 (engel) | 1 | 3 | 3 |

Tablonun elle doğrulanması şöyle yapılır. İlk satırda hiçbir engel yok, bu yüzden her hücre 1'dir. İkinci satırda `(1,1)` engel olduğu için 0; `(1,2)`, `dp[0][2] + dp[1][1] = 1 + 0 = 1` ve `(1,3)`, `dp[0][3] + dp[1][2] = 1 + 1 = 2`. Son hücre `dp[3][3] = dp[2][3] + dp[3][2] = 0 + 3 = 3`'tür; `(2,3)` engelli olduğu için `0` alındı.

**Bunu AI'sız yazabilir misin?** Hareketlerin yalnızca sağa ve aşağı değil, dört yöne (sol ve sağ dahil) izinli olduğunu düşün. Bu durumda tablo bağıntısı neden çalışmaz? Hangi yapısal değişiklik (ör. bir döngü ya da ziyaret kümesi) gerekir?

### Örnek 2 (★★): Ev soygunu, dairesel varyant

**Problem:** Bir sokakta `n` ev var; her evin içinde `v_i` değerinde bir mal var. Komşu iki ev aynı gece soyulursa alarm çalar. Ev dizisi dairesel olsun: ilk ev ile son ev de komşudur. Alarm çalmadan en çok ne kadar mal alınabilir?

**Adım 1 — Anla.** Girdi negatif olmayan tamsayılar dizisidir. Kısıt: seçilen evlerin indeksleri arasında fark en az 2 olmalı ve ilk ile son birlikte seçilemez. Çıktı en büyük toplamdır. Kenar durum: `n = 1` ise tek ev alınabilir.

**Adım 2 — Örnekle.** `[2, 3, 2]` dairesel dizisinde ilk ve son ev komşudur. Doğrusal düşünürsek `2 + 2 = 4` (evler 0 ve 2) seçilebilir. Dairesel kısıtla bu yasaktır; en iyi seçim `3`'tür (yalnızca orta ev).

**Adım 3 — Kaba çöz.** Tüm `2^n` alt kümeyi dene, komşuluk kısıtını ve dairesellik kısıtını uygula, en büyük toplamı al. Doğru, ama `n` büyüdükçe kullanışsız.

**Adım 4 — Örüntü.** Doğrusal sürüm için `dp[i]`, `i`. eve kadar (dahil) olan evlerden alınabilecek en büyük toplamdır. Bağıntı: `dp[i] = max(dp[i-1], dp[i-2] + v_i)`; ya `i`. evi atlarsın, ya da alır ve `i-1`'i atlarsın. Dairesel durumda ilk ve son ev birlikte seçilemez; bu yüzden iki doğrusal problemin en büyüğünü alırız: ya ilk evi atlayıp `[1..n-1]`'i, ya son evi atlayıp `[0..n-2]`'yi çözeriz.

**Adım 5 — İyileştir.** Doğrusal DP yalnızca iki değişkenle tutulabilir (`onceki`, `simdiki`), bu yüzden bellek `O(1)`'dir. Dairesel sürüm iki doğrusal çağrının maksimumudur; toplam `O(n)`.

{{KOD:ornek2.py:1:31}}

Ana fonksiyon `[2, 3, 2]` ve `[1, 2, 3, 1]` örneklerini çözer, rastgele 300 dizide kaba kuvvetle karşılaştırır.

{{KOD:ornek2.py:32:51}}

**Adım 6 — Doğrula.** Programı çalıştırdık:

{{TERM}}
python ornek2.py ||| python ornek2.py
{{/TERM}}

`[2, 3, 2]` için iki doğrusal çağrının iz tablosu:

| Çağrı | Eleman `v` | `onceki` | `simdiki` (yeni) |
|---|---|---|---|
| `dogrusal([2, 3])` | 2 | 0 | 2 |
| | 3 | 2 | 3 |
| `dogrusal([3, 2])` | 3 | 0 | 3 |
| | 2 | 3 | 3 |

İki çağrı da 3 verir; dairesel cevap `max(3, 3) = 3`'tür. Aynı dizi için doğrusal çözüm `4` verir (`2 + 2`), ki bu dairesel kısıtta yasaktır. Bu fark, dairesel varyantın neden ayrı bir kontrol gerektirdiğini gösterir.

**Bunu AI'sız yazabilir misin?** `n = 1` durumunda kod neden ayrı bir dal içeriyor? `dairesel([v])` için `dogrusal(degerler[:-1])` ve `dogrusal(degerler[1:])` ikisi de boş dizi üzerinde çalışır mı, yoksa sonuç yanlış mı olur?

### Örnek 3 (★★): Kelime bölme ve geri kurma

**Problem:** Bir `s` dizgisi ve bir sözlük (kelime kümesi) verilsin. `s`'yi sözlükteki kelimelerin ardışık birleşimine bölebilir misin? Bölebiliyorsan, bir bölmeyi kelime listesi olarak döndür; bölemiyorsan `None` döndür.

**Adım 1 — Anla.** Girdi bir dizgi ve bir kümedir; çıktı bir liste ya da `None`'dır. Kenar durumlar: `s` boşsa bölme boş listedir; sözlükte hiçbir kelime `s`'nin başıyla eşleşmiyorsa `None`'dır. Geri kurma istendiği için yalnızca "var" demek yetmez.

**Adım 2 — Örnekle.** `s = "yazilimmuhendisligi"` ve sözlük `{yazi, yazilim, muhendis, ligi, li, gi}` için iki bölme vardır: `yazilim | muhendis | ligi` ve `yazilim | muhendis | li | gi`. `"yazilimx"` için bölme yoktur.

**Adım 3 — Kaba çöz.** `s`'nin başından her önekin sözlükte olup olmadığına bak; varsa kalanı özyinelemeyle böl. Bu, kesim noktalarının tüm kombinasyonlarını (`2^(n-1)` tane) dener.

**Adım 4 — Örüntü.** `dp[i]` = `s[:i]` bölünebilir mi? Bağıntı: `dp[i]` doğrudur, eğer bir `j < i` için `dp[j]` doğru ve `s[j:i]` sözlüktedir. Bölünebilirlik yetmez, geri kurmak için `j`'yi de saklamalısın: `kaynak[i] = j`. Böylece sondan başa giderek bölmeyi çıkarabilirsin.

**Adım 5 — İyileştir.** Tek bir `kaynak` dizisi hem "bölünebilir mi" bilgisini (`None` değil mi) hem de geri kurma bilgisini taşır. Her `i` için en fazla bir `j` tutulur: ilk bulunan. Döngüler `O(n^2)` denetim yapar; her denetim bir dilim oluşturduğu için pratikte biraz daha maliyetlidir.

{{KOD:ornek3.py:1:34}}

Ana fonksiyon örneği çözer, erişilebilir `kaynak` değerlerini yazdırır ve 300 rastgele küçük sözlükte kaba kuvvet ile karşılaştırır.

{{KOD:ornek3.py:35:62}}

**Adım 6 — Doğrula.** Programı çalıştırdık:

{{TERM}}
python ornek3.py ||| python ornek3.py
{{/TERM}}

Programın yazdırdığı `kaynak` sözlüğü (`{0: -1, 4: 0, 6: 4, 7: 0, 15: 7, 17: 15, 19: 15}`) erişilebilir indeksleri verir. Bunu iz tablosu olarak düzenledik:

| `i` | `kaynak[i]` | `s[kaynak[i]:i]` | Anlamı |
|---|---|---|---|
| 0 | -1 | (boş) | Boş önek bölünebilir |
| 4 | 0 | `yazi` | `s[:4]` bir kelime |
| 6 | 4 | `li` | `s[:6]` = yazi + li |
| 7 | 0 | `yazilim` | `s[:7]` bir kelime |
| 15 | 7 | `muhendis` | `s[:15]` = yazilim + muhendis |
| 17 | 15 | `li` | `s[:17]` = ... + li |
| 19 | 15 | `ligi` | Tüm dizgi |

Geri kurma son satırdan başlar: `19 → 15` (`ligi`), `15 → 7` (`muhendis`), `7 → 0` (`yazilim`). Okunuşu tersten yapınca `yazilim | muhendis | ligi` çıkar. Programın çıktısı da aynı bölmeyi verdi. Dikkat: `19`'a `17` üzerinden de ulaşılabilir (`s[17:19] = gi`, `kaynak[17] = 15`), ama `kaynak` her `i` için yalnızca ilk bulunan `j`'yi tutar. Bu yüzden program tek bir bölme döndürür; ikinci bölme `yazilim | muhendis | li | gi` de geçerlidir. Tek bir bölme bulmak ile tüm bölmeleri listelemek farklı sorulardır.

**Bunu AI'sız yazabilir misin?** `kaynak[i]` her `i` için tek bir `j` tutuyor. Tüm olası bölmeleri listelemek istesen, bu yapıyı nasıl değiştirirsin? Ve bölme sayısını (kaç farklı bölme var?) bulmak için `kaynak` yerine hangi dizi gerekir?

### Örnek 4 (★★★): Yazım denetimi: en yakın sözcükler ve işlem dizisi

**Problem:** Kullanıcının yazdığı bozuk bir sözcük (`kitp`) ve bir sözlük verilsin. En yakın üç sözcüğü, düzenleme mesafeleriyle birlikte bul; en yakın sözcüğe giden düzenleme işlemlerini de yaz. Düzenleme işlemleri ekleme, silme ve değiştirmedir; her biri 1 birim maliyetlidir.

**Adım 1 — Anla.** Girdi bir dizgi ve bir sözcük listesidir; çıktı üç çift `(mesafe, sözcük)` ve bir işlem dizisidir. Kenar durumlar: girdi boşsa mesafe sözcük uzunluğudur; sözcük girdiyle aynıysa mesafe 0'dır ve işlem listesi yalnızca eşleşmelerden oluşur.

**Adım 2 — Örnekle.** `kitp` ile sözlük `kitap, kapi, kopya, kedi, kitle, kapak` için mesafeler: `kitap` 1, `kitle` 2, `kapi` 3. En yakın `kitap`'a giden tek işlem `a` eklemektir.

**Adım 3 — Kaba çöz.** Her sözcük için rekürsif bir `mesafe(i, j)` fonksiyonu yaz; üç seçeneği (değiştir, sil, ekle) dene. Bu, her çağrının üç çağrıya dallandığı bir ağaç üretir; aynı `(i, j)` çiftleri tekrar tekrar hesaplanır.

**Adım 4 — Örüntü.** Bu, Bölüm 16.8'deki tablonun aynısıdır. `dp[i][j]`, `kitp`'nin ilk `i` karakterinin, sözcüğün ilk `j` karakterine dönüşmesinin maliyetidir. Geri izleme için her hücrede hangi seçeneğin geçerli olduğunu bilmek gerekir: eşleşme, değiştirme, silme ya da ekleme.

**Adım 5 — İyileştir.** Her sözcük için bir tablo doldurulur. Üç komşu hücreye bakılır; geri izleme ise tablo üzerinde ters yönde yürür. Her sözcük için `O(nm)` iş vardır; sözlük `k` sözcükse toplam `O(k · nm)`.

{{KOD:ornek4.py:1:35}}

Ana fonksiyon her sözcük için tabloyu hesaplar, mesafeye göre sıralar, ilk üçü yazdırır ve en iyi adayın tablosunu gösterir.

{{KOD:ornek4.py:36:54}}

**Adım 6 — Doğrula.** Programı çalıştırdık:

{{TERM}}
python ornek4.py ||| python ornek4.py
{{/TERM}}

`kitp` ile `kitap` arasındaki tablo (satırlar `kitp`, sütunlar `kitap`):

| | `""` | `k` | `i` | `t` | `a` | `p` |
|---|---|---|---|---|---|---|
| `""` | 0 | 1 | 2 | 3 | 4 | 5 |
| `k` | 1 | 0 | 1 | 2 | 3 | 4 |
| `i` | 2 | 1 | 0 | 1 | 2 | 3 |
| `t` | 3 | 2 | 1 | 0 | 1 | 2 |
| `p` | 4 | 3 | 2 | 1 | 1 | 1 |

Son hücre 1'dir. Son satırda `p` ile `p` eşleşir (`dp[4][5] = dp[3][4] = 1`), yani sondan başlayan geri izleme köşegenden gider ve `a` için bir ekleme işlemi üretir. Tablonun köşegeni `k`, `i`, `t` eşleşmelerini gösterir ve sıfırlarla ilerler. İşlem listesi `ekle a` olarak çıktı.

**Bunu AI'sız yazabilir misin?** Ekleme ve silme maliyetini 1 yerine 2 yapsaydın, `dp` bağıntısında neyi değiştirirdin? Değiştirme ile sil-ekle çiftinin maliyeti eşit olduğunda hangi işlem geri izlemede tercih edilir ve bu neden önemli olabilir?
