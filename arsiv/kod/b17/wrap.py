import os
os.chdir(r"C:\Users\merty\AppData\Local\Temp\b17\code")
R = {
"astar.py": {
"                    heapq.heappush(yigin, (yeni + h(nr, nc), yeni, (nr, nc)))":
"                    f = yeni + h(nr, nc)\n                    heapq.heappush(yigin, (f, yeni, (nr, nc)))",
"    while a_star(izgara, (0, 0), hedef)[0] == INF:   # ulasilabilir olana kadar":
"    # ulasilabilir bir izgara bulana kadar yeniden uret\n    while a_star(izgara, (0, 0), hedef)[0] == INF:",
},
"bellman.py": {
"# Ayni grafta Dijkstra'nin negatif kenarda neden yanlis sonuc verdigini de gosterir.":
"# Ayni grafta Dijkstra'nin negatif kenarda neden yanlis sonuc\n# verdigini de gosterir.",
"            if dist[u] + w < dist[v]:  # INF + w = INF: erismeyen atlanir":
"            if dist[u] + w < dist[v]:  # INF + w = INF: atlanir",
"            break                      # erken durma: artik degisiklik yok":
"            break                      # erken durma",
"    for u, v, w in kenarlar:           # V. tur: hala gevsetilebiliyorsa":
"    for u, v, w in kenarlar:           # V. tur: hala gevsetiliyor mu?",
"    print(\"Negatif dongu:\", bellman_ford(n, kenarlar + [(1, 2, 1)], 0))":
"    donguly = kenarlar + [(1, 2, 1)]\n    print(\"Negatif dongu:\", bellman_ford(n, donguly, 0))",
},
"bipartite.py": {
"    (False, (u, v)): ayni renkli iki komsu, yani tek bir cift kenar.\"\"\"":
"    (False, (u, v)): ayni renkli iki komsu (cakisan kenar).\"\"\"",
"                    return False, (u, v)     # cakisma: tek sayida kenarli dongu":
"                    return False, (u, v)     # cakisma: tek dongu",
},
"cross_test.py": {
"# cross_test.py - Algoritmalari birbirine ve bagimsiz referanslara karsi":
"# cross_test.py - Algoritmalari birbirine ve bagimsiz\n# referanslara karsi",
"        beklenen = any(fd[s][v] < INF and fd[v][v] < 0 for v in range(n))":
"        beklenen = any(fd[s][v] < INF and fd[v][v] < 0\n                       for v in range(n))",
"        a = bfs_mesafe(n, komsu(n, k1), s) == dijkstra(n, komsu(n, k1), s)[0]":
"        a = (bfs_mesafe(n, komsu(n, k1), s)\n             == dijkstra(n, komsu(n, k1), s)[0])",
"        b = zero_one_bfs(n, komsu(n, k2), s) == dijkstra(n, komsu(n, k2), s)[0]":
"        b = (zero_one_bfs(n, komsu(n, k2), s)\n             == dijkstra(n, komsu(n, k2), s)[0])",
"    k = [(rng.randrange(v), v, rng.randint(1, 5)) for v in range(1, n)]":
"    k = [(rng.randrange(v), v, rng.randint(1, 5))\n         for v in range(1, n)]",
"        ok += t1 == t2 and len(s1) == n - 1 and len(s2) == n - 1 and bagli":
"        ok += (t1 == t2 and len(s1) == n - 1\n               and len(s2) == n - 1 and bagli)",
"    \"\"\"Sinir durumlari: bos graf, tek dugum, ulasilamayan, esit agirlik.\"\"\"":
"    \"\"\"Sinir durumlari: bos graf, tek dugum, ulasilamayan dugum,\n    esit agirlik.\"\"\"",
"        r = [[i == j or w[i][j] < INF for j in range(n)] for i in range(n)]":
"        r = [[i == j or w[i][j] < INF for j in range(n)]\n             for i in range(n)]",
"        beklenen = {frozenset(v for v in range(n) if r[u][v] and r[v][u])":
"        beklenen = {frozenset(v for v in range(n)\n                              if r[u][v] and r[v][u])",
"    \"\"\"Kopru: silince bilesen artar. Eklem: dugumu silince bilesen artar.\"\"\"":
"    \"\"\"Kopru: silince bilesen artar. Eklem: dugum silince\n    bilesen artar.\"\"\"",
"        kenar = sorted({tuple(sorted(e)) for e in adaylar if e[0] != e[1]})":
"        kenar = sorted({tuple(sorted(e)) for e in adaylar\n                        if e[0] != e[1]})",
"                              if bilesen_sayisi(n, [f for f in kenar if f != e]) > b0)":
"                              if bilesen_sayisi(\n                                  n, [f for f in kenar if f != e]) > b0)",
"                              if bilesen_sayisi(n, [e for e in kenar if u not in e]) - 1 > b0)":
"                              if bilesen_sayisi(\n                                  n, [e for e in kenar if u not in e])\n                              - 1 > b0)",
"    \"\"\"Kahn ve DFS: gecerli siralar; dongu tespiti graphlib ile ayni.\"\"\"":
"    \"\"\"Kahn ve DFS: gecerli siralar; dongu tespiti graphlib ile\n    ayni.\"\"\"",
"                gecerli = gecerli and all(poz[u] < poz[v] for u, v in k)":
"                gecerli = gecerli and all(poz[u] < poz[v]\n                                          for u, v in k)",
"    \"\"\"DAG'da en kisa yol = BF (negatif kenar serbest); 2-renk = brute.\"\"\"":
"    \"\"\"DAG'da en kisa yol = BF (negatif kenar serbest); 2-renk\n    brute force ile karsilastirilir.\"\"\"",
"        k = [(u, v, rng.randint(-3, 9)) for u in range(n) for v in range(u + 1, n)":
"        k = [(u, v, rng.randint(-3, 9)) for u in range(n)\n             for v in range(u + 1, n)",
"        ok += dag_en_kisa(n, komsu(n, k), s) == bellman_ford(n, k, s)[0]":
"        ok += (dag_en_kisa(n, komsu(n, k), s)\n               == bellman_ford(n, k, s)[0])",
"    print(f\"Test 9 DAG en kisa yol: {ok}/{top}; iki renkli: {ok2}/{top}\")":
"    print(f\"Test 9 DAG en kisa yol: {ok}/{top}; \"\n          f\"iki renkli: {ok2}/{top}\")",
},
"graphlib_demo.py": {
"# graphlib_demo.py - Python'un kendi topolojik siralayicisi ve dongu hatasi.":
"# graphlib_demo.py - Python'un topolojik siralayicisi ve dongu hatasi.",
},
"mst.py": {
"        while self.ata[x] != kok:             # 2. gecis: yolu sikistir":
"        while self.ata[x] != kok:             # 2. gecis: sikistir",
"            ra, rb = rb, ra                   # kucuk agaci buyuge bagla":
"            ra, rb = rb, ra                   # kucugu buyuge bagla",
"    \"\"\"kenarlar: [(agirlik, u, v)], yonsuz. Donus: (toplam, secilen).\"\"\"":
"    \"\"\"kenarlar: [(agirlik, u, v)], yonsuz.\n    Donus: (toplam, secilen).\"\"\"",
"    yigin = [(0, 0, -1)]                      # (agirlik, dugum, ebeveyn)":
"    yigin = [(0, 0, -1)]              # (agirlik, dugum, ebeveyn)",
},
"ornek1_ders.py": {
"# ornek1_ders.py - Ders on kosullari: gecerli sira ve dongu tespiti (Kahn).":
"# ornek1_ders.py - Ders on kosullari: gecerli sira, dongu (Kahn).",
"    dersler = [\"Programlama\", \"Matematik\", \"Veri Yapilari\", \"Algoritmalar\",":
"    dersler = [\"Programlama\", \"Matematik\", \"Veri Yapilari\",\n               \"Algoritmalar\",",
"    onkosul = [(\"Programlama\", \"Veri Yapilari\"), (\"Programlama\", \"Isletim\"),":
"    onkosul = [(\"Programlama\", \"Veri Yapilari\"),\n               (\"Programlama\", \"Isletim\"),",
"               (\"Veri Yapilari\", \"Algoritmalar\"), (\"Matematik\", \"Algoritmalar\"),":
"               (\"Veri Yapilari\", \"Algoritmalar\"),\n               (\"Matematik\", \"Algoritmalar\"),",
"               (\"Algoritmalar\", \"Derleyici\"), (\"Algoritmalar\", \"Bitirme\"),":
"               (\"Algoritmalar\", \"Derleyici\"),\n               (\"Algoritmalar\", \"Bitirme\"),",
},
"ornek2_gecikme.py": {
"# ornek2_gecikme.py - Ag yonlendiricileri arasi en dusuk gecikmeli yol.":
"# ornek2_gecikme.py - Yonlendiriciler arasi en dusuk gecikmeli yol.",
},
"ornek3_sehir.py": {
"# ornek3_sehir.py - Sehirleri en ucuz sekilde baglama (Kruskal + Union-Find).":
"# ornek3_sehir.py - Sehirleri en ucuz baglama (Kruskal + Union-Find).",
"        print(f\"  {SEHIR[u]}-{SEHIR[v]} ({w:>2})  kok {SEHIR[ku]}/{SEHIR[kv]}\"":
"        print(f\"  {SEHIR[u]}-{SEHIR[v]} ({w:>2})  \"\n              f\"kok {SEHIR[ku]}/{SEHIR[kv]}\"",
},
"ornek4_arbitraj.py": {
"    \"\"\"kenar: [(u, v, w)]. Tum dugumler 0'dan baslar (sanal kaynak gibi).":
"    \"\"\"kenar: [(u, v, w)]. Tum dugumler 0'dan baslar\n    (sanal kaynak gibi).",
"    for u, v, w in kenar:                       # n. tur: hala gevserse dongu":
"    for u, v, w in kenar:               # n. tur: gevserse dongu var",
"            for _ in range(n):                  # n adim geri: dongunun icinde":
"            for _ in range(n):          # n adim geri: dongunun icinde",
"        print(f\"  {PB[u]}->{PB[v]} kur {r}  -ln(kur) = {-math.log(r):.4f}\")":
"        print(f\"  {PB[u]}->{PB[v]} kur {r}  \"\n              f\"-ln(kur) = {-math.log(r):.4f}\")",
},
"tarjan.py": {
"# tarjan.py - Tarjan: guclu bagli bilesenler (yonlu) ve kopru/eklem (yonsuz).":
"# tarjan.py - Tarjan: guclu bagli bilesen (yonlu), kopru/eklem.",
"    \"\"\"Yonlu graf. Donus: bilesen listesi; her bilesen sirali dugum listesi.\"\"\"":
"    \"\"\"Yonlu graf. Donus: bilesen listesi (her biri sirali).\"\"\"",
"    low = [0] * n               # kendi alt agacindan erisilen en kucuk index":
"    low = [0] * n               # alt agactan erisilen en kucuk index",
"            elif ycinde[v]:                 # yiginda: ayni bilesende olabilir":
"            elif ycinde[v]:                 # yiginda: ayni bilesen",
"            if v == ata:                    # ebeveyne giden kenari atla":
"            if v == ata:                    # ebeveyne kenari atla",
"                if low[v] > disc[u]:        # v'nin altagaci u'yu asmiyor":
"                if low[v] > disc[u]:        # v'nin altagaci u'yu asmaz",
"        if ata == -1 and cocuk > 1:         # kok: iki ya da fazla cocuk":
"        if ata == -1 and cocuk > 1:         # kok, 2+ cocuk",
},
"topo.py": {
"# topo.py - Topolojik siralama: Kahn (derece + kuyruk) ve DFS (bitis sirasi).":
"# topo.py - Topolojik siralama: Kahn (derece+kuyruk) ve DFS.",
"    sira, dongulu = kahn(n, [[v for v, _ in adj[u]] for u in range(n)])":
"    komsu = [[v for v, _ in adj[u]] for u in range(n)]\n    sira, dongulu = kahn(n, komsu)",
"    adj[6].append(0)                   # Derleyici -> Programlama: dongu":
"    adj[6].append(0)                   # Derleyici -> Programlama",
},
"dfs.c": {
"    int komsu[MAXN][MAXD];    /* komsu[u][i]: u'nun i. kenarinin hedefi */":
"    int komsu[MAXN][MAXD];    /* komsu[u][i]: u'nun i. kenari */",
"/* Dogru yinelemeli DFS: yiginda (dugum, siradaki kenar) cifti tutulur. */":
"/* Dogru yinelemeli DFS: yiginda (dugum, siradaki kenar) tutulur. */",
"/* Naif yinelemeli DFS: tum komsular yigina itilir, cikista ziyaret edilir.":
"/* Naif yinelemeli DFS: tum komsular yigina itilir; ziyaret cikista.",
" * 'gorulen' tum kokler arasinda paylasilir; ziyaret sirasi 'cikti'ya yazilir. */":
" * 'gorulen' tum kokler arasinda paylasilir; sira 'cikti'ya yazilir. */",
"static int dfs_naif(const Graf *g, int s, int *gorulen, int *cikti, int k) {":
"static int dfs_naif(const Graf *g, int s, int *gorulen, int *cikti,\n                    int k) {",
"/* Kesif zamanina gore dugumleri sirala (ozyinelemeli siranin kaydi). */":
"/* Kesif zamanina gore dugumleri sirala (ozyinelemeli sira). */",
"    for (size_t i = 0; i < sizeof kenarlar / sizeof kenarlar[0]; i++) {":
"    size_t m = sizeof kenarlar / sizeof kenarlar[0];\n    for (size_t i = 0; i < m; i++) {",
"    printf(\"  yinelemeli == ozyinelemeli (d ve f): %d/%d\\n\", dogru, TUR);":
"    printf(\"  yinelemeli == ozyinelemeli (d ve f): %d/%d\\n\",\n           dogru, TUR);",
},
}
for fn, reps in R.items():
    src = open(fn, encoding="utf-8").read()
    for a, b in reps.items():
        if a not in src:
            print("MISSING in", fn, ":", a[:60])
        src = src.replace(a, b, 1)
    open(fn, "w", encoding="utf-8").write(src)
print("done")
