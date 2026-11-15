## 16.10 Sözde-polinomluk, DP'yi tanımak ve gerçek dünya

Sırt çantası çözümümüzün karmaşıklığı `O(nW)`'dir. Bu ifade, sayıya bakınca polinomdur gibi görünür; ama bir ayrım gerekir. `W` bir **değerdir**, girdinin uzunluğu değildir. Kapasiteyi `W` yazmak için yalnızca `log W` bit gerekir. Dolayısıyla `O(nW)`, girdi uzunluğu cinsinden üstel olabilir. Buna sözde-polinom (pseudo-polynomial) denir.

Rakamla bak: `n = 100` eşya ve `W = 10^9` kapasite için tablo `10^11` hücredir. Bu bellek ve süre açısından uygulanamaz. Girdi ise çok küçük: `W`'nin ikilik gösterimi 30 bit, değer ve ağırlıklar birkaç bitlik sayılar. `W`'ye yalnızca bir bit eklemek onu iki katına çıkarır ve tabloyu da yaklaşık iki katına çıkarır; girdinin uzunluğu ise bir bit artar.

Bu yüzden 0/1 sırt çantasının karar sürümü (değeri en az `V` olan bir seçim var mı?) NP-tamdır; Karp'ın 1972 listesinde yer alır. DP burada bir çözüm sağlar, ama genel bir polinom zamanlı çözüm değildir. Mülakatta bu soru geldiğinde "DP `O(nW)` ile çözer" demek yetmez: ayrıca "W girdinin uzunluğuna göre üstel" demen beklenir.

### DP'yi tanıma sinyalleri

DP sorularını tanımak, kod yazmaktan daha zordur. Aşağıdaki sinyaller, bir problemin DP olabileceğini gösterir; kesin bir kural değildir.

- Sorunun cevabı bir **en iyi değer** (en az, en çok) ya da bir **sayım** (kaç yol, kaç çözüm).
- Problem, **sıralı kararlardan** oluşur: her adımda bir seçim yapılır ve sonraki seçenekler öncekine bağlıdır.
- Girdi bir **dizi**, bir **aralık** ya da bir **kapasite** içerir ve alt problemler bu girdinin önekleri ya da alt aralıklarıdır.
- Aynı alt problem farklı yollarla tekrar tekrar gelir (16.1'deki ağaç).
- Açgözlü (greedy) bir seçim bazen yanlış sonuç verir; ama yanlışlığı bir karşı örnekle gösterebilirsen DP'ye geçmek doğru olabilir.

Son madde önemlidir. Açgözlü algoritma, her adımda en iyi görünen seçimi yapar. Bu hızlıdır, ama her problemde doğru değildir: 0/1 sırt çantasında en değerli-ağırlık oranlı eşyayı seçmek yanlış olabilir. Bölüm 18'de açgözlü algoritmanın ne zaman doğru olduğunu kanıtlamayı göreceksin; bu bölümdeki karşı örnek, DP'ye geçmenin gerekçesidir.

### Gerçek dünyada DP

DP, yalnızca ders kitabında kalan bir teknik değildir. Dört alanda doğrudan karşına çıkar.

**Diff ve sürüm kontrolü.** Git'te dosyalar arası farkı hesaplamanın temelinde LCS fikri vardır. Bir birleştirme (merge) sırasında hangi satırların iki tarafta da değiştiğini anlamak için kullanılan karşılaştırmalar da aynı ailedendir. Bölüm 38'de Git'i derinlemesine göreceksin; orada gördüğün `diff` çıktıları, bu bölümdeki LCS fikrine dayanır.

**Biyoinformatik.** İki DNA ya da protein dizisini hizalamak, DP'nin en büyük uygulamalarından biridir. Needleman–Wunsch, iki dizinin tamamını (global hizalama) hizalamak için edit distance'a benzer bir tabloyu kullanır; Smith–Waterman ise yalnızca en iyi yerel eşleşmeyi arar. Hizalama skoru, eşleşme, uyumsuzluk ve boşluk cezalarının toplamıdır; yani edit distance'ın ağırlıklı bir türüdür.

**Viterbi ve HMM.** Gizli Markov Modelinde (HMM), gözlemlenen bir dizinin en olası gizli durum dizisini bulmak için Viterbi algoritması kullanılır. Bu algoritma, durumlar üzerinden zamana bağlı bir tablo doldurur: her zaman adımı ve her durum için en olası önceki durumu tutar, sonunda geri izleme yapar. Yapısı, bu bölümdeki LCS ve sırt çantası tabloları ile aynıdır. Bölüm 62'de HMM'yi ve Viterbi'yi ayrıntılı göreceksin.

**Pekiştirmeli öğrenme.** Bir ajanın ödülünü en büyüten politikayı bulmak için Bellman denklemi kullanılır. Bir durumun değeri, o durumda en iyi eylemi seçtiğinde alınacak anlık ödülle, sonraki durumun (indirgenmiş, yani bir indirim katsayısıyla çarpılmış) değerinin toplamıdır. Bu denklem, bir DP geçişinin tam olarak aynısıdır: durum, geçiş ve hesaplama sırası. Bölüm 74'te (Pekiştirmeli Öğrenme) bu denklemden Q-learning ve policy gradient yöntemlerine geçeceğiz.

Bu dört örnekte ortak olan şey, problemin bir **alt problemler tablosu** olarak düşünülebilmesidir. Bu düşünce biçimini kazandığında, yeni bir problemle karşılaştığında önce durumunu tanımlayabilirsin ve Bölüm 16.2'deki protokol ile ilerlersin.
