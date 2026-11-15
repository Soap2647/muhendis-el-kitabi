import glob

FIX = {
"aritmetik.py": [
 ("# aritmetik.py: tamsayı aritmetik kodlayıcı (Witten, Neal, Cleary 1987).",
  "# aritmetik.py: tamsayı aritmetik kodlayıcı\n# (Witten, Neal, Cleary 1987)."),
 ("        b = self.bits[self.konum] if self.konum < len(self.bits) else 0",
  "        var = self.konum < len(self.bits)\n        b = self.bits[self.konum] if var else 0"),
 ("    mesaj = [rnd.choices([0, 1, 2], weights=frek)[0] for _ in range(20000)]",
  "    mesaj = [rnd.choices([0, 1, 2], weights=frek)[0]\n             for _ in range(20000)]"),
],
"entropi_temel.py": [
 ('    print("Çarpık yazı-tura (0.9): H = %.4f bit" % entropi([0.9, 0.1]))',
  '    print("Çarpık yazı-tura (0.9): H = %.4f bit"\n          % entropi([0.9, 0.1]))'),
 ('    print("Bağımsız tablo için I(X;Y) = %.1e" % karsilikli_bilgi(bagimsiz))',
  '    print("Bağımsız tablo için I(X;Y) = %.1e"\n          % karsilikli_bilgi(bagimsiz))'),
],
"hamming_kanal.py": [
 ("# hamming_kanal.py: Hamming(7,4) kodlayıcı ve sendrom çözücü; ikili simetrik\n# kanal (BSC) üzerinde kodsuz, tekrar(3) ve Hamming(7,4) bit hata oranı.",
  "# hamming_kanal.py: Hamming(7,4) kodlayıcı ve sendrom çözücü;\n# ikili simetrik kanal (BSC) üzerinde kodsuz, tekrar(3) ve\n# Hamming(7,4) bit hata oranı."),
 ('    print("ornek: 1011 -> %s" % "".join(map(str, kodla([1, 0, 1, 1]))))',
  '    c = "".join(map(str, kodla([1, 0, 1, 1])))\n    print("ornek: 1011 -> %s" % c)'),
 ("        berh = sum(a != b for a, b in zip(cozulen, veri_bitler)) / len(\n            veri_bitler)",
  "        hata = sum(a != b for a, b in zip(cozulen, veri_bitler))\n        berh = hata / len(veri_bitler)"),
 ('        satirlar.append([p, "%.6f" % ber0, "%.6f" % ber3, "%.6f" % berh,\n                         "%.6f" % (3 * p * p - 2 * p ** 3)])',
  '        formul = 3 * p * p - 2 * p ** 3\n        satirlar.append([p, "%.6f" % ber0, "%.6f" % ber3,\n                         "%.6f" % berh, "%.6f" % formul])'),
 ('    with open(os.path.join(veri, "b51_ber.csv"), "w", encoding="utf-8",\n              newline="") as f:',
  '    yol = os.path.join(veri, "b51_ber.csv")\n    with open(yol, "w", encoding="utf-8", newline="") as f:'),
 ('        w.writerow(["p", "kodsuz", "tekrar3", "hamming74", "tekrar3_formul"])',
  '        w.writerow(["p", "kodsuz", "tekrar3", "hamming74",\n                    "tekrar3_formul"])'),
],
"kanal_kapasite.py": [
 ("# kanal_kapasite.py: BSC kapasitesi C = 1 - H(p), veri işleme eşitsizliği\n# (iki BSC'nin zinciri) ve Shannon-Hartley C = B log2(1 + S/N).",
  "# kanal_kapasite.py: BSC kapasitesi C = 1 - H(p), veri işleme\n# eşitsizliği (iki BSC'nin zinciri) ve Shannon-Hartley\n# C = B log2(1 + S/N)."),
 ("    hyx = -sum(v * math.log2(v / 0.5) for v in ortak.values() if v > 0)",
  "    hyx = -sum(v * math.log2(v / 0.5)\n               for v in ortak.values() if v > 0)"),
 ('    print("5 Mbit/s icin gereken B = %.3f MHz (SNR 10 dB)" % (b / 1e6))',
  '    print("5 Mbit/s icin gereken B = %.3f MHz (SNR 10 dB)"\n          % (b / 1e6))'),
],
"kl_ce.py": [
 ("        return math.exp(-0.5 * ((x - m) / s) ** 2) / (s * math.sqrt(2 * math.pi))",
  "        ust = math.exp(-0.5 * ((x - m) / s) ** 2)\n        return ust / (s * math.sqrt(2 * math.pi))"),
 ('    print("KL([1,0] || [0.5,0.5]) = %.4f" % kl([1.0, 0.0], [0.5, 0.5]))',
  '    print("KL([1,0] || [0.5,0.5]) = %.4f"\n          % kl([1.0, 0.0], [0.5, 0.5]))'),
],
"kodlama_olcum.py": [
 ("    # 3) Türkçe harf akışı: frekanslar tamsayıya ölçeklenir (toplam 2^16)",
  "    # 3) Türkçe harf akışı: frekanslar tamsayıya ölçeklenir\n    #    (toplam yaklaşık 2^16)"),
],
"kraft_huffman.py": [
 ("# kraft_huffman.py: Kraft eşitsizliği, Huffman kod uzunlukları, entropiye\n# uzaklık (H <= L < H + 1) ve Huffman'ın optimalliğinin kaba kuvvet denetimi.",
  "# kraft_huffman.py: Kraft eşitsizliği, Huffman kod uzunlukları,\n# entropiye uzaklık (H <= L < H + 1) ve Huffman'ın optimalliğinin\n# kaba kuvvet denetimi."),
 ("    # Tüm tamsayı uzunluk vektörlerini dene; Kraft <= 1 olanlar arasında",
  "    # Tüm tamsayı uzunluk vektörlerini dene; Kraft <= 1 olanlar\n    # arasında"),
 ("        w = [rnd.random() ** 3 + 1e-6 for _ in range(rnd.randint(2, 8))]",
  "        n = rnd.randint(2, 8)\n        w = [rnd.random() ** 3 + 1e-6 for _ in range(n)]"),
 ("        if abs(kaba_kuvvet(q) - ortalama(q, huffman_uzunluk(q))) < 1e-9:",
  "        opt = ortalama(q, huffman_uzunluk(q))\n        if abs(kaba_kuvvet(q) - opt) < 1e-9:"),
 ('    print("300 rastgele 4\'lu kaynakta Huffman = kaba kuvvet: %d" % eslesen)',
  '    print("300 rastgele 4\'lu kaynakta Huffman = kaba kuvvet: %d"\n          % eslesen)'),
],
"lz77_zlib.py": [
 ("# lz77_zlib.py: LZ77 sözlük kodlamasının sezgisi, DEFLATE = LZ77 + Huffman\n# ve sıkıştırılamaz veri (rastgele ve \"şifreli benzeri\") ölçümü.",
  "# lz77_zlib.py: LZ77 sözlük kodlamasının sezgisi, DEFLATE = LZ77 +\n# Huffman ve sıkıştırılamaz veri (rastgele ve \"şifreli benzeri\")\n# ölçümü."),
 ("            while k < azami and i + k < len(s) - 1 and s[j + k] == s[i + k]:",
  "            while (k < azami and i + k < len(s) - 1\n                   and s[j + k] == s[i + k]):"),
 ("    # Örtüşen kopyalar için bayt bayt yazılır (ofset < uzunluk olabilir).",
  "    # Örtüşen kopyalar bayt bayt yazılır (ofset < uzunluk olabilir)."),
 ("        ks = hashlib.sha256(anahtar + blok.to_bytes(8, \"big\")).digest()",
  "        sayac = blok.to_bytes(8, \"big\")\n        ks = hashlib.sha256(anahtar + sayac).digest()"),
],
"olcum_metin.py": [
 ("    # Türkçe büyük/küçük harf: I -> ı, İ -> i (Python'un varsayılanı yanlış)",
  "    # Türkçe büyük/küçük harf: I -> ı, İ -> i\n    # (Python'un varsayılanı yanlış)"),
 ("    # Kod bloklarını, tabloları, şekil satırlarını ve kutu işaretlerini at.",
  "    # Kod bloklarını, tabloları, şekil satırlarını, kutu işaretlerini\n    # at."),
 ("    kgram = Counter(tuple(dizi[i:i + k]) for i in range(len(dizi) - k + 1))",
  "    n = len(dizi) - k + 1\n    kgram = Counter(tuple(dizi[i:i + k]) for i in range(n))"),
 ('    print("corpus sha256:", hashlib.sha256(ham).hexdigest()[:16], "...")',
  '    ozet = hashlib.sha256(ham).hexdigest()[:16]\n    print("corpus sha256:", ozet, "...")'),
 ('    with open(os.path.join(veri, "b51_harf.csv"), "w", encoding="utf-8",\n              newline="") as f:',
  '    yol = os.path.join(veri, "b51_harf.csv")\n    with open(yol, "w", encoding="utf-8", newline="") as f:'),
],
"softmax_gradyan.py": [
 ("# softmax_gradyan.py: softmax + çapraz entropi kaybı, sayısal kararlılık\n# (log-sum-exp) ve gradyanın sayısal denetimi. Birim: nat (ln).",
  "# softmax_gradyan.py: softmax + çapraz entropi kaybı, sayısal\n# kararlılık (log-sum-exp) ve gradyanın sayısal denetimi.\n# Birim: nat (ln)."),
 ("        en_buyuk = max(en_buyuk, max(abs(u - v) for u, v in zip(a, s)))",
  "        fark = max(abs(u - v) for u, v in zip(a, s))\n        en_buyuk = max(en_buyuk, fark)"),
 ('    print("500 rastgele z icin max |analitik - sayisal| = %.2e" % en_buyuk)',
  '    print("500 rastgele z icin max |analitik - sayisal| = %.2e"\n          % en_buyuk)'),
 ("    yum = [(1 - eps) * (1.0 if i == 0 else 0.0) + eps / k for i in range(k)]",
  "    yum = [(1 - eps) * (i == 0) + eps / k for i in range(k)]"),
],
}

for f, reps in FIX.items():
    s = open(f, encoding="utf-8").read()
    for old, new in reps:
        n = s.count(old)
        assert n == 1, (f, n, old[:60])
        s = s.replace(old, new)
    open(f, "w", encoding="utf-8").write(s)

for f in sorted(glob.glob("*.py")):
    if f == "fix_width.py":
        continue
    for i, l in enumerate(open(f, encoding="utf-8").read().split("\n")):
        if len(l) > 70:
            print("LONG", f, i + 1, len(l))
print("fixed")
