import re
def rep(path, old, new, regex=False):
    s = open(path, encoding="utf-8").read()
    if regex:
        s2, n = re.subn(old, new, s)
    else:
        n = s.count(old); s2 = s.replace(old, new)
    assert n >= 1, (path, old[:50])
    open(path, "w", encoding="utf-8").write(s2)
    return n

rep("b77_ab.py", '    print("n=%d guc(sim)=%.3f" % (n // 2, guc_sim(0.05, 0.06, n // 2)))',
    '    yari = n // 2\n    print("n=%d guc(sim)=%.3f" % (yari, guc_sim(0.05, 0.06, yari)))')
rep("b77_drift.py", 'm = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500))',
    'm = make_pipeline(StandardScaler(),\n                      LogisticRegression(max_iter=500))')
rep("b77_drift.py", "Bir tohum icin W pencerelik akisi izler; satir listesi doner.",
    "Bir tohum icin W pencerelik akis; satir listesi doner.")
rep("b77_drift.py", "ref, _ = uret(2000, rng)                  # referans",
    "ref, _ = uret(2000, rng)     # referans")
rep("b77_drift.py", 'once = [s[yontem] for s in satirlar if s["pencere"] < KAYMA_BAS]',
    'once = [s[yontem] for s in satirlar\n                if s["pencere"] < KAYMA_BAS]')
rep("b77_drift.py", "ozetler = {seed: yontem_ozeti(tohum_satir[seed]) for seed in SEEDS}",
    "ozetler = {seed: yontem_ozeti(tohum_satir[seed])\n               for seed in SEEDS}")
rep("b77_drift.py", 'if r["pencere"] >= KAYMA_BAS and r["psi_max"] > esik]',
    'if r["pencere"] >= KAYMA_BAS\n                   and r["psi_max"] > esik]')
rep("b77_kapi.py", "Dort aday modelden birini egitir. Doner: (model, sutun dilimi).",
    "Dort adaydan birini egitir. Doner: (model, sutun dilimi).")
rep("b77_kapi.py", '    print("gerilim yok     :", veri_denetle(df.drop(columns="gerilim")))',
    '    print("gerilim yok     :",\n          veri_denetle(df.drop(columns="gerilim")))')
rep("b77_kayit.py", 'surumler.append({"surum": n, "dosya": yol, "sha256": ozet(yol),',
    'surumler.append({"surum": n, "dosya": yol,\n                         "sha256": ozet(yol),')
rep("b77_kayit.py", "Asama atar. 'production' ise eski uretim surumu arsive gider.",
    "Asama atar. 'production' ise eski surum arsive gider.")
rep("b77_kayit.py", 'raise ValueError("%s v%d bozulmus" % (ad, s["surum"]))',
    'raise ValueError(\n                        "%s v%d bozulmus" % (ad, s["surum"]))')
rep("b77_kayit.py", 'return joblib.load(s["dosya"])   # yalniz kendi dosyani yukle',
    '# yalniz kendi dosyani yukle\n                return joblib.load(s["dosya"])')
rep("b77_kayit.py", "Uretimdeki surumu, en son arsivlenmis surumle degistirir.",
    "Uretimdeki surumu, son arsiv surumuyle degistirir.")
rep("b77_kok_neden.py", '"""Her satir: gun, cihaz, firmware, ham girdi (4 sutun), gercek etiket,\n    model tahmini. Ham girdi, seri hattindan sonra kaydedilen degerdir."""',
    '"""Her satir bir kayit: gun, cihaz, firmware, ham girdi (4 sutun),\n    gercek etiket ve model tahmini. Ham girdi, seri hattindan sonra\n    kaydedilen degerdir."""')
rep("b77_kok_neden.py", 'print("   40. gunden sonra: %.4f" % roc_auc_score(y[sonra], p[sonra]))',
    'print("   40. gunden sonra: %.4f" %\n          roc_auc_score(y[sonra], p[sonra]))')
rep("b77_kok_neden.py", r'for ad, kume in \[\("v1, 0-39", once & ~v2\), \("v2, 0-39", once & v2\),\s+\("v1, 40-59", sonra & ~v2\), \("v2, 40-59", sonra & v2\)\]:',
    'grup = [("v1, 0-39", once & ~v2), ("v2, 0-39", once & v2),\n            ("v1, 40-59", sonra & ~v2), ("v2, 40-59", sonra & v2)]\n    for ad, kume in grup:', regex=True)
rep("b77_ornek1.py", "Ornek 1: PSI'nin elle hesabi (dort kutu, kagit kalemi karsiligi).",
    "Ornek 1: PSI'nin elle hesabi (dort kutu, kagit kalemiyle).")
rep("b77_ornek2.py", 'with open(HAM, "a", encoding="utf-8") as f:   # ham veriye bir satir eklendi',
    '# ham veriye bir satir eklenir\nwith open(HAM, "a", encoding="utf-8") as f:')
rep("b77_ortam.py", '    print("ortam parmak izi:", hashlib.sha256(metin.encode()).hexdigest()[:16])',
    '    ozet = hashlib.sha256(metin.encode()).hexdigest()\n    print("ortam parmak izi:", ozet[:16])')
rep("b77_servis.py", 'if varyant == "yuvarlama":          # gerilim 1 ondaliga yuvarlanir',
    'if varyant == "yuvarlama":  # gerilim 1 ondalik')
rep("b77_servis.py", 'print("varyant      AUC(11)  AUC(22)  AUC(33)  ort.    tahmin-degisimi")',
    'print("varyant      AUC(11)  AUC(22)  AUC(33)  ort.   tahmin")')
rep("b77_takip.py", r'\[\(deney, k, str\(v\)\) for k, v in d\.items\(\)\]\)',
    '[(deney, k, str(v))\n                            for k, v in d.items()])', regex=True)
rep("b77_takip.py", "Deneyleri metriğe göre azalan sırada, parametreyle birlikte.",
    "Deneyleri metriğe göre azalan sırada listeler.")
rep("b77_takip.py", '    with open(os.path.join(yol, "egitim.py"), "w", encoding="utf-8") as f:',
    '    ep = os.path.join(yol, "egitim.py")\n    with open(ep, "w", encoding="utf-8") as f:')
rep("b77_telemetri.py", "ortam_kaymasi:   sicaklik dagiliminin otelenmesi (kovaryat kaymasi).",
    "ortam_kaymasi:  sicaklik dagiliminin otelenmesi (kovaryat).")
rep("b77_yeniden_egitim.py", "    return sc, LogisticRegression(max_iter=500).fit(sc.transform(X), y)",
    "    lr = LogisticRegression(max_iter=500)\n    return sc, lr.fit(sc.transform(X), y)")
rep("b77_yeniden_egitim.py", "maliyet += FN * np.sum(~pred & (y == 1)) + FP * np.sum(pred & (y == 0))",
    "maliyet += FN * np.sum(~pred & (y == 1))\n        maliyet += FP * np.sum(pred & (y == 0))")
rep("b77_yeniden_egitim.py", "t = w - GECIKME                      # etiketi simdi gelen pencere",
    "t = w - GECIKME    # etiketi simdi gelen pencere")
rep("b77_yeniden_egitim.py", 'print("politika   maliyet (ort +- ss)   AUC (ort)   yeniden (ort)")',
    'print("politika  maliyet (ort +- ss)  AUC (ort)  yeniden")')
rep("b77_yeniden_egitim.py", r"\(ad, m\.mean\(\), m\.std\(ddof=1\), np\.mean\(\[x\[1\] for x in s\]\),",
    "(ad, m.mean(), m.std(ddof=1),\n               np.mean([x[1] for x in s]),", regex=True)
print("duzeltmeler tamam")
