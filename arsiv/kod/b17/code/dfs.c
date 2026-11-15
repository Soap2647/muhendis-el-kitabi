/* dfs.c - Yonlu graf uzerinde DFS: ozyinelemeli, yinelemeli (dogru ve
 * naif) ve kenar siniflandirmasi. Rastgele graflarda uc surumu sinar.
 * Derleme: gcc -std=c11 -Wall -Wextra -O2 dfs.c -o dfs
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define MAXN 64
#define MAXD 4           /* bir dugumun en fazla cikis kenari */
#define BEYAZ 0
#define GRI 1
#define SIYAH 2

typedef struct {
    int n;
    int dere[MAXN];           /* dere[u]: u'nun cikis kenari sayisi */
    int komsu[MAXN][MAXD];    /* komsu[u][i]: u'nun i. kenari */
} Graf;

static int renk[MAXN], d[MAXN], f[MAXN], zaman;
static int say[4];
static const char *ad[4] = {"agac", "geri", "ileri", "capraz"};

static void sifirla(void) {
    memset(renk, 0, sizeof renk);
    memset(d, 0, sizeof d);
    memset(f, 0, sizeof f);
    memset(say, 0, sizeof say);
    zaman = 0;
}

/* u -> v kenarini siniflandirir. Kenar, v beyazken cagrilmalidir. */
static void sinifla(int u, int v, int yaz) {
    int t;
    if (renk[v] == BEYAZ)     t = 0;  /* agac: v yeni kesfedildi */
    else if (renk[v] == GRI)  t = 1;  /* geri: v, u'nun atasi */
    else if (d[u] < d[v])     t = 2;  /* ileri: v, u'nun torunu */
    else                      t = 3;  /* capraz: v farkli bir dal */
    say[t]++;
    if (yaz)
        printf("  %d -> %d : %s\n", u, v, ad[t]);
}

static void dfs_rec(const Graf *g, int u, int yaz) {
    renk[u] = GRI;
    d[u] = ++zaman;
    for (int i = 0; i < g->dere[u]; i++) {
        int v = g->komsu[u][i];
        sinifla(u, v, yaz);
        if (renk[v] == BEYAZ)
            dfs_rec(g, v, yaz);
    }
    renk[u] = SIYAH;
    f[u] = ++zaman;
}

/* Dogru yinelemeli DFS: yiginda (dugum, siradaki kenar) tutulur. */
static void dfs_yin(const Graf *g, int s) {
    int yigin[MAXN], sira[MAXN], ust = 0;
    renk[s] = GRI;
    d[s] = ++zaman;
    sira[s] = 0;
    yigin[ust++] = s;
    while (ust > 0) {
        int u = yigin[ust - 1];
        if (sira[u] < g->dere[u]) {          /* siradaki kenar */
            int v = g->komsu[u][sira[u]++];
            sinifla(u, v, 0);
            if (renk[v] == BEYAZ) {
                renk[v] = GRI;
                d[v] = ++zaman;
                sira[v] = 0;
                yigin[ust++] = v;
            }
        } else {                             /* kenarlar bitti: cik */
            renk[u] = SIYAH;
            f[u] = ++zaman;
            ust--;
        }
    }
}

/* Naif yinelemeli DFS: tum komsular yigina itilir; ziyaret cikista.
 * 'gorulen' kokler arasinda paylasilir; sira 'cikti'ya yazilir. */
static int dfs_naif(const Graf *g, int s, int *gorulen, int *cikti,
                    int k) {
    int yigin[MAXN * MAXD], ust = 0;
    yigin[ust++] = s;
    while (ust > 0) {
        int u = yigin[--ust];
        if (gorulen[u])
            continue;
        gorulen[u] = 1;
        cikti[k++] = u;
        for (int i = 0; i < g->dere[u]; i++)
            yigin[ust++] = g->komsu[u][i];
    }
    return k;
}

/* Kesif zamanina gore dugumleri sirala (ozyinelemeli sira). */
static void kesif_sirasi(int n, int *cikti) {
    int k = 0;
    for (int t = 1; t <= 2 * n; t++)
        for (int u = 0; u < n; u++)
            if (d[u] == t)
                cikti[k++] = u;
}

static uint32_t durum = 42;             /* xorshift32, tohum 42 */
static uint32_t rnd(void) {
    durum ^= durum << 13;
    durum ^= durum >> 17;
    durum ^= durum << 5;
    return durum;
}

static void graf_uret(Graf *g, int n) {
    g->n = n;
    for (int u = 0; u < n; u++) {
        g->dere[u] = (int)(rnd() % (MAXD + 1));
        for (int i = 0; i < g->dere[u]; i++)
            g->komsu[u][i] = (int)(rnd() % (uint32_t)n);
    }
}

static void tum_kokler(const Graf *g, int yaz) {
    for (int u = 0; u < g->n; u++)
        if (renk[u] == BEYAZ)
            dfs_rec(g, u, yaz);
}

int main(void) {
    Graf g;
    int kenarlar[][2] = {{0,1},{0,3},{0,2},{1,2},{2,0},{3,2},{4,5}};
    g.n = 6;
    memset(g.dere, 0, sizeof g.dere);
    size_t m = sizeof kenarlar / sizeof kenarlar[0];
    for (size_t i = 0; i < m; i++) {
        int u = kenarlar[i][0];
        g.komsu[u][g.dere[u]++] = kenarlar[i][1];
    }

    sifirla();
    printf("Kenar siniflandirmasi (ozyinelemeli DFS):\n");
    tum_kokler(&g, 1);
    printf("Dugum  d  f\n");
    for (int u = 0; u < g.n; u++)
        printf("  %d    %2d %2d\n", u, d[u], f[u]);
    printf("Sayim: agac=%d geri=%d ileri=%d capraz=%d\n",
           say[0], say[1], say[2], say[3]);

    int kesif[MAXN], gor[MAXN], ns[MAXN], k = 0;
    kesif_sirasi(g.n, kesif);
    memset(gor, 0, sizeof gor);
    for (int u = 0; u < g.n; u++)
        k = dfs_naif(&g, u, gor, ns, k);
    printf("Ozyinelemeli ziyaret: ");
    for (int i = 0; i < g.n; i++)
        printf("%d ", kesif[i]);
    printf("\nNaif ziyaret       : ");
    for (int i = 0; i < g.n; i++)
        printf("%d ", ns[i]);
    printf("\n");

    /* Rastgele graflarda uc surumu karsilastir. */
    enum { TUR = 200, N = 40 };
    int dogru = 0, naif_farkli = 0;
    for (int t = 0; t < TUR; t++) {
        Graf r;
        graf_uret(&r, N);

        sifirla();
        tum_kokler(&r, 0);
        int d_rec[MAXN], f_rec[MAXN], rec_sira[MAXN];
        memcpy(d_rec, d, sizeof d);
        memcpy(f_rec, f, sizeof f);
        kesif_sirasi(N, rec_sira);

        sifirla();
        for (int u = 0; u < N; u++)
            if (renk[u] == BEYAZ)
                dfs_yin(&r, u);
        if (memcmp(d_rec, d, sizeof d) == 0 &&
            memcmp(f_rec, f, sizeof f) == 0)
            dogru++;

        int gorulen[MAXN], naif_sira[MAXN], k = 0;
        memset(gorulen, 0, sizeof gorulen);
        for (int u = 0; u < N; u++)
            k = dfs_naif(&r, u, gorulen, naif_sira, k);
        for (int i = 0; i < N; i++)
            if (naif_sira[i] != rec_sira[i]) {
                naif_farkli++;
                break;
            }
    }
    printf("\nRastgele %d graf (n=%d, tohum 42):\n", TUR, N);
    printf("  yinelemeli == ozyinelemeli (d ve f): %d/%d\n",
           dogru, TUR);
    printf("  naif sira ozyinelemeliden farkli   : %d/%d\n",
           naif_farkli, TUR);
    return 0;
}
