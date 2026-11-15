# -*- coding: utf-8 -*-
p = "C:/Users/merty/AppData/Local/Temp/b38/p3.md"
s = open(p, encoding="utf-8").read()


def span_replace(s, start_marker, end_marker, new_text):
    a = s.index(start_marker)
    b = s.index(end_marker, a) + len(end_marker)
    return s[:a] + new_text + s[b:]


def para_replace(s, start_marker, new_text):
    a = s.index(start_marker)
    b = s.index("\n\n", a)
    return s[:a] + new_text + s[b:]


NEW_A = open("C:/Users/merty/AppData/Local/Temp/b38/new_a.txt",
             encoding="utf-8").read()
s = span_replace(s, "Biz de deneyelim.", "bu örnek açıklar.", NEW_A)

s = para_replace(s, "Patience algoritması çapa olarak",
    "Patience algoritması, yalnızca iki dosyada da tek kez geçen satırları eşleştirme çapası olarak kullanır (bu örnekte `u02`, `u05`, `u08` gibi satırlar bu niteliktedir) ve çapalar arasını ayrı ayrı hizalar. Bu, en kısa betiği garanti etmez: Patience bu örnekte daha uzun bir değişiklik üretti. Yani bir ödünleşim var: minimal değişikliği mi, yoksa \"insan gözünde anlamlı\" hizalamayı mı istediğine karar vermen gerekir. Patience ve histogram, kod taşıma ve büyük yeniden düzenlemelerde genelde daha okunaklı diff'ler üretir; ama her zaman daha kısa değildir.")

s = para_replace(s, "Bu farkın ne kadar yaygın olduğunu ölçmek için",
    "Bu farkın ne kadar yaygın olduğunu görmek için bir deney daha yaptık. Her denemede 14-22 satırlık bir dosya kuruldu; satırlar `}`, boş satır ve benzersiz satırların karışımıydı. Sonra dosyadan 4 satırlık bir blok rastgele bir yere taşındı (tohum 38, 150 deneme). 150 denemenin 31'inde üç algoritma farklı sayıda satır değiştirdi. Bu bir örneklem değil, tek bir düzenekteki sayımdır; genel bir yüzde iddiası olarak okunmamalı, ama Myers ile patience'ın sonuçlarının kodun yapısına bağlı olarak ayrıldığını gösteriyor.")

s = s.replace("200 commit'in her biri bir commit, bir tree ve bir blob nesnesi ürettiği için 603 nesne (200 · 3 + ilk commit'in üç nesnesi) var.",
              "İlk commit ile birlikte 201 commit, 201 tree ve 201 blob vardır: toplam 603 nesne.")

s = para_replace(s, "`-c pack.threads=1` bayrağını neden",
    "`-c pack.threads=1` bayrağını neden kullandığımızı açıklamamız gerekiyor. Git paketlemede delta eşleşmelerini aramak için birden çok iş parçacığı kullanabilir. Bu deneyde çok iş parçacıklı paketleme, aynı betiğin iki çalıştırmasında birkaç baytlık farkla farklı paket dosyaları üretti; paket dosyasının adı (içindeki nesnelerin özetinden türetilir) da değişti. Tek iş parçacığıyla iki çalıştırma birebir aynı sonucu verdi. Bu, ölçümü tekrarlanabilir kılmak için yaptığımız bir ayardır; git'in genel davranışı hakkında bir iddia değildir.")

a = s.index("```term\n$ git verify-pack -v")
b = s.index("```", a + 10) + 3
NEW_V = open("C:/Users/merty/AppData/Local/Temp/b38/new_v.txt",
             encoding="utf-8").read()
s = s[:a] + NEW_V + s[b:]

s = s.replace("Sütunlar sırasıyla: nesne adı, tür, `size`, `size-in-pack`, paketteki `offset` (konum), `depth` (derinlik) ve delta ise temel nesne. İlk satır tam saklanmış temel blob'dur: 52500 bayt, pakette 10426 bayt (sıkıştırılmış). İkinci satır bir delta: `size` sütunu burada 22 gösteriyor, ama bu nesnenin gerçek boyutu değil, delta verisinin boyutudur.",
              "Sütunlar sırasıyla: nesne adı, tür, `size`, `size-in-pack`, paketteki `offset` (konum), `depth` (derinlik) ve delta ise temel nesnenin adı. İlk satır tam saklanmış temel blob'dur: 52500 bayt, pakette 10426 bayt (sıkıştırılmış). İkinci satır (`4226b714`) bir delta, derinliği 1: 23 baytlık delta verisi. Üçüncü satır (`52806c5b`) derinliği 2 olan bir delta; `size` sütunu burada 22 gösteriyor, ama bu nesnenin gerçek boyutu değil, delta verisinin boyutudur.")

s = s.replace("![Şekil 38.7: Paketleme ölçümü. Solda delta derinliklerinin dağılımı: çoğu nesne derinlik sınırına yakın, tek bir tam temel nesneden türemiş. Sağda gevşek nesnelerin ve paketin toplam boyutu.]",
              "![Şekil 38.7: Paketleme ölçümü. Solda delta derinliklerinin dağılımı: nesnelerin çoğu 44-50 aralığında, en büyük küme sınırdaki 50'de. Sağda gevşek nesnelerin ve paketin toplam boyutu.]")

s = s.replace("Bu, Bölüm 35'te LSM", "Bu, Bölüm 35.5'te LSM")
s = s.replace("Bölüm 35.5'te LSM ağaçlarında birleştirme (compaction) ile okuma-yazma-alan (write amplification) dengesini gördün; git paketlemesinde de benzer bir takas var: birleştirme (gc) disk alanı kazandırır, ama okuma derinliğini artırır.",
              "Bölüm 35.5'te LSM ağaçlarında birleştirmenin yazma yükseltmesi (write amplification) ile okuma maliyeti arasında bir takas yaptığını gördün; git paketlemesinde de benzer bir takas var: `gc` disk alanı kazandırır, ama delta zincirlerinin okuma derinliğini artırır.")

s = para_replace(s, "`pull`'un `--no-rebase` ile çağrılması bilinçli",
    "`pull`'un `--no-rebase` ya da `--rebase` ile açıkça çağrılması iyi bir alışkanlıktır: pull'un varsayılan davranışı ve uyarıları git sürümüne ve yapılandırmaya göre değişebilir. Hangi davranışı istediğini kalıcı kılmak için `pull.rebase` yapılandırması vardır, ama ekip içinde tutarlı olması şarttır.")

s = s.replace("Savunma projelerinde planlı sürümler ve sertifikasyon olduğu için Git Flow benzeri, sürüm dallı bir model sık görülür; ama birleşmelerin küçük ve sık olması hâlâ geçerlidir.",
              "Planlı sürümler ve sertifikasyon gerektiren bazı savunma projelerinde Git Flow benzeri, sürüm dallı bir model tercih edilebilir; ama birleşmelerin küçük ve sık olması yine de geçerlidir.")

open(p, "w", encoding="utf-8").write(s)
print("done", len(s))
