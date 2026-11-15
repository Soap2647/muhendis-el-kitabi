%% kisim_no: IV
%% kisim_ad: Algoritmalar
%% bolum_no: 16
%% baslik: Dynamic Programming

## Giriş: Aynı işi ikinci kez yapmamak

Bölüm 15'te fib ağacında aynı alt problemin defalarca çözüldüğünü gördük. `fib(3)` ağacın birden fazla yerinde çıkıyor, her seferinde sıfırdan hesaplanıyor. Bu bölümde o tekrarı bir kez yapıp sonucu saklamayı öğreneceğiz. Bu fikrin adı dinamik programlamadır (dynamic programming, DP). Terimi Richard Bellman bulmuştur; ad bir programlama tekniğinden çok, çözümü aşamalara bölme biçimini anlatır.

DP, Bölüm 12'de gördüğümüz karmaşıklık analizinin en kullanışlı uygulamalarından biridir. Üstel süren bir özyinelemeyi, durum sayısı ile geçiş maliyetinin çarpımı kadar sürecek bir hesaba çevirir. Fibonacci'de bu, `2^n`'den `n`'e düşmek demektir. Bölüm 12'deki Big-O dilini burada somut bir karara dönüştürüyoruz: hangi alt problemler gerçekten hesaplanmalı, hangileri saklanmalı?

Mülakatta DP soruları çoğu zaman "en az", "en çok", "kaç yol" ya da "bu seçimlerden hangisi en iyisi" kalıbıyla gelir. Adayın ilk tepkisi genellikle kaba kuvvetle başlamaktır. DP'yi bilmek, o kaba kuvvetin neden aynı şeyi tekrar hesapladığını görüp onu tabloya dönüştürebilmek demektir. Savunma sanayiinde de benzer problemler var: bir İHA'nın rotasında yakıtı en az tutan yolu bulmak, bir sensör kaydını bir referans dizisine hizalamak ya da bir sinyal modelinde en olası durum dizisini çıkarmak DP ile çözülür. Bölüm 62'deki HMM ve Viterbi algoritması bu bölümün doğrudan devamıdır.

Mert'in projelerine de yakın bir bağlantı var. Bu bölümün sonunda kendi `diff` aracını yazacaksın; bu araç iki metin dosyasının en uzun ortak altdizisini bulmak için LCS'i kullanır. Mert Studio Code'daki Türkçe parser'a eklenebilecek bir yazım denetimi ise edit distance ile yapılır. EV Dashboard'daki batarya enerji bütçesi de bir sırt çantası problemidir.

::: not
Bu bölümdeki her program Python 3.12.10 ile çalıştırıldı. C programları WSL'de gcc 13.3 ile `-std=c11` ve `-Wall -Wextra` uyarılarıyla derlendi; bellek hataları için `-fsanitize=address,undefined` ile de denendi. Kodlardaki rastgele örnekler `random.Random(42)` tohumuyla üretildi, böylece sayılar sizde de aynı çıkar. Windows'ta `long` 4 bayttır (LLP64), bu yüzden C kodunda tamsayı boyutlarını `long long` ve `size_t` ile açıkça seçtik.
:::
