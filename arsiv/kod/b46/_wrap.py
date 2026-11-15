import io
R = {
"telemetri.py": [
 ("Sira: [ort(4), std(4), min(4), maks(4), egim(4)], indeks = tur*4 + kanal.",
  "Sira: [ort(4), std(4), min(4), maks(4), egim(4)].\nIndeks = tur*4 + kanal."),
 ("    T = T0 + rng.normal(0.0, 0.08, L) + 0.01 * rng.uniform(0, 1) * np.arange(L)",
  "    drift = 0.01 * rng.uniform(0, 1) * np.arange(L)\n    T = T0 + rng.normal(0.0, 0.08, L) + drift"),
 ("        p[:, 0] -= siddet * rng.uniform(0.10, 0.30) * np.linspace(0, 1, L)",
  "        rampa = np.linspace(0, 1, L)\n        p[:, 0] -= siddet * rng.uniform(0.10, 0.30) * rampa"),
 ("        p[:, 1] += siddet * rng.uniform(6, 18) * np.linspace(0, 1, L) ** 1.5",
  "        rampa = np.linspace(0, 1, L) ** 1.5\n        p[:, 1] += siddet * rng.uniform(6, 18) * rampa"),
],
"egit.py": [
 ("Gradyan inisi: softmax capraz entropi kaybi, geri yayilim elle yazildi.",
  "Gradyan inisi: softmax capraz entropi kaybi.\nGeri yayilim elle yazildi."),
 ("            kayip = -np.log(softmax(z2)[np.arange(n), ytr] + 1e-12).mean()",
  "            olas = softmax(z2)[np.arange(n), ytr]\n            kayip = -np.log(olas + 1e-12).mean()"),
],
"bit_tara.py": [
 ('"""Bit genisligi taramasi: 8, 7, ... 2 bit (sahte kuantizasyon, float).',
  '"""Bit genisligi taramasi: 8, 7, ... 2 bit (sahte kuantizasyon).'),
 ("  minmax         : agirlik + girdi + ara aktivasyon, min/maks kalibrasyon",
  "  minmax         : agirlik + girdi + ara aktivasyon, min/maks\n                   kalibrasyon"),
 ('    """Asimetrik: [lo, hi] araligi 2^b seviyeye, sifir temsil edilir."""',
  '    """Asimetrik: [lo, hi] araligi 2^b seviyeye.\n\n    Sifir her zaman temsil edilir."""'),
],
"sinir.py": [
 ('"""Tam aralikli rastgele int8 girdiler (doygunluk / tasma sinamasi)."""',
  '"""Tam aralikli rastgele int8 girdiler (doygunluk/tasma sinamasi)."""'),
],
"tinyml.c": [
 ('    __asm__ ("smlad %0, %1, %2, %3" : "=r"(r) : "r"(a), "r"(b), "r"(c));',
  '    __asm__ ("smlad %0, %1, %2, %3"\n             : "=r"(r) : "r"(a), "r"(b), "r"(c));'),
 ("        int64_t p = (int64_t)acc * TM_M1[i] + ((int64_t)1 << (rs - 1));",
  "        int64_t p = (int64_t)acc * TM_M1[i];\n        p += (int64_t)1 << (rs - 1);   /* yuvarlama */"),
],
"test_host.c": [
 ('    float (*ozp)[20] = oku(d, "test_ozellik.bin", sizeof(float) * N * 20);',
  '    float (*ozp)[20] = oku(d, "test_ozellik.bin",\n                           sizeof(float) * N * 20);'),
 ('    int32_t (*bek)[3] = oku(d, "test_beklenen.bin", sizeof(int32_t) * N * 3);',
  '    int32_t (*bek)[3] = oku(d, "test_beklenen.bin",\n                            sizeof(int32_t) * N * 3);'),
 ('    int32_t (*rbek)[2] = oku(d, "test_r_beklenen.bin", sizeof(int32_t) * NR * 2);',
  '    int32_t (*rbek)[2] = oku(d, "test_r_beklenen.bin",\n                             sizeof(int32_t) * NR * 2);'),
 ('    printf("girdi kuantizasyonu uyusmazlik    : %d / %d\n", girdi_uyus, N);',
  '    printf("girdi kuantizasyonu uyusmazlik    : %d / %d\n",\n           girdi_uyus, N);'),
 ('    printf("int8 logit uyusmazlik (bit-tam)   : %d / %d\n", logit_uyus, N);',
  '    printf("int8 logit uyusmazlik (bit-tam)   : %d / %d\n",\n           logit_uyus, N);'),
 ('    printf("rastgele tam aralik uyusmazlik    : %d / %d\n", r_uyus, NR);',
  '    printf("rastgele tam aralik uyusmazlik    : %d / %d\n",\n           r_uyus, NR);'),
 ('    return (girdi_uyus == 0 && logit_uyus == 0 && r_uyus == 0) ? 0 : 2;',
  '    if (girdi_uyus || logit_uyus || r_uyus) return 2;\n    return 0;'),
],
"kuantize.py": [
 ('"""float32 -> int8 kuantizasyon, tamsayi referans cikarimi, C aktarimi.',
  '"""float32 -> int8 kuantizasyon, tamsayi referans, C aktarimi.'),
 ('    """Tam tamsayi cikarim. Doner: a1 (int8 degerler), logit (int32)."""',
  '    """Tam tamsayi cikarim.\n\n    Doner: a1 (int8 degerler), logit (int32)."""'),
 ('    out = ["/* Otomatik uretildi: kuantize.py. Elle degistirmeyin. */\n",',
  '    out = ["/* Otomatik uretildi: kuantize.py.\n",\n           "   Elle degistirmeyin. */\n",'),
 ('           "static const float TM_SIN = %.9ef;\n\n" % float(Q["S_in"])]',
  '           "static const float TM_SIN = %.9ef;\n\n"\n           % float(Q["S_in"])]'),
 ('        print("int8 (%-24s) dogruluk: %.4f" % (ad, (tah == yte).mean()))',
  '        print("int8 (%-24s) dogruluk: %.4f"\n              % (ad, (tah == yte).mean()))'),
 ('    Q = modeli_kuantize(p, Xn_tr, "minmax", True)   # secilen: C\'ye gider',
  '    # Secilen varyant (kanal basina, minmax) C\'ye aktarilir\n    Q = modeli_kuantize(p, Xn_tr, "minmax", True)'),
 ('    Fte.astype(np.float32).tofile(os.path.join(HERE, "test_ozellik.bin"))',
  '    yol = os.path.join(HERE, "test_ozellik.bin")\n    Fte.astype(np.float32).tofile(yol)'),
 ('    Xte.astype(np.float32).tofile(os.path.join(HERE, "test_pencere.bin"))',
  '    yol = os.path.join(HERE, "test_pencere.bin")\n    Xte.astype(np.float32).tofile(yol)'),
],
}
for f, reps in R.items():
    s = io.open(f, encoding="utf-8").read()
    for a, b in reps:
        n = s.count(a)
        if n != 1:
            print("UYARI", f, n, a[:60])
        s = s.replace(a, b)
    io.open(f, "w", encoding="utf-8", newline="\n").write(s)
print("bitti")
