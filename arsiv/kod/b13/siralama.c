/* siralama.c: Bolum 13 siralama laboratuvari */
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct {
    int anahtar;   /* siralanacak deger */
    int sira;      /* giristeki konum (kararlilik testi icin) */
} Kayit;

static long long kars, yaz;   /* karsilastirma ve yazma sayaci */
static int izle;              /* 1 ise ara durumlari yazdir */
static unsigned long long durum = 42;

static unsigned rastgele(void) {          /* xorshift64, tohum 42 */
    durum ^= durum << 13;
    durum ^= durum >> 7;
    durum ^= durum << 17;
    return (unsigned)(durum >> 32);
}

static int kucuk(const Kayit *x, const Kayit *y) {
    kars++;
    return x->anahtar < y->anahtar;
}

static void takas(Kayit *x, Kayit *y) {
    Kayit t = *x;
    *x = *y;
    *y = t;
    yaz += 2;
}

static void goster(const char *ad, const Kayit *a, size_t n) {
    printf("%-10s", ad);
    for (size_t i = 0; i < n; i++)
        printf(" %d", a[i].anahtar);
    printf("\n");
}

static void kabarcik(Kayit *a, size_t n) {
    for (size_t son = n; son > 1; son--) {
        int degisti = 0;
        for (size_t i = 0; i + 1 < son; i++) {
            /* yalniz kesin buyukse takas: kararlilik */
            if (kucuk(&a[i + 1], &a[i])) {
                takas(&a[i], &a[i + 1]);
                degisti = 1;
            }
        }
        if (izle) goster("kabarcik", a, n);
        if (!degisti) break;
    }
}

static void secmeli(Kayit *a, size_t n) {
    for (size_t i = 0; i + 1 < n; i++) {
        size_t en = i;
        for (size_t j = i + 1; j < n; j++)
            if (kucuk(&a[j], &a[en])) en = j;
        if (en != i) takas(&a[i], &a[en]);
        if (izle) goster("secmeli", a, n);
    }
}

static void eklemeli(Kayit *a, size_t n) {
    for (size_t i = 1; i < n; i++) {
        Kayit x = a[i];
        size_t j = i;
        while (j > 0 && kucuk(&x, &a[j - 1])) {
            a[j] = a[j - 1];
            yaz++;
            j--;
        }
        a[j] = x;
        yaz++;
        if (izle) goster("eklemeli", a, n);
    }
}

static void birlestir(Kayit *a, Kayit *g, size_t lo,
                      size_t orta, size_t hi) {
    size_t i = lo, j = orta, k = lo;
    while (i < orta && j < hi) {
        /* sag eleman yalniz kesin kucukse once gelir */
        if (kucuk(&a[j], &a[i]))
            g[k++] = a[j++];
        else
            g[k++] = a[i++];
        yaz++;
    }
    while (i < orta) { g[k++] = a[i++]; yaz++; }
    while (j < hi)   { g[k++] = a[j++]; yaz++; }
    for (k = lo; k < hi; k++) { a[k] = g[k]; yaz++; }
}

static void birlesme_rec(Kayit *a, Kayit *g, size_t lo, size_t hi) {
    if (hi - lo < 2) return;
    size_t orta = lo + (hi - lo) / 2;
    birlesme_rec(a, g, lo, orta);
    birlesme_rec(a, g, orta, hi);
    birlestir(a, g, lo, orta, hi);
}

static void birlestirme(Kayit *a, size_t n) {
    if (n < 2) return;
    Kayit *g = malloc(n * sizeof *g);
    if (!g) { fprintf(stderr, "bellek yok\n"); exit(1); }
    birlesme_rec(a, g, 0, n);
    free(g);
}

/* x, y, z indekslerinden degeri ortanca olanin indeksi */
static ptrdiff_t uc_medyan(const Kayit *a, ptrdiff_t x,
                           ptrdiff_t y, ptrdiff_t z) {
    if (kucuk(&a[x], &a[y])) {
        if (kucuk(&a[y], &a[z])) return y;
        if (kucuk(&a[x], &a[z])) return z;
        return x;
    }
    if (kucuk(&a[x], &a[z])) return x;
    if (kucuk(&a[y], &a[z])) return z;
    return y;
}

/* Pivotu a[lo]'ya tasi. strat: 0 ilk, 1 rastgele, 2 ucun medyani */
static void pivot_sec(Kayit *a, ptrdiff_t lo, ptrdiff_t hi,
                      int strat) {
    ptrdiff_t k = lo;
    if (strat == 1)
        k = lo + (ptrdiff_t)(rastgele() % (unsigned)(hi - lo + 1));
    else if (strat == 2)
        k = uc_medyan(a, lo, lo + (hi - lo) / 2, hi);
    takas(&a[lo], &a[k]);
}

/* Hoare bolumlemesi: pivot a[lo]; donus j, [lo..j] <= p */
/* ve [j+1..hi] >= p. Pivot a[hi]'ya gelmez, j < hi. */
static ptrdiff_t hoare(Kayit *a, ptrdiff_t lo, ptrdiff_t hi) {
    Kayit p = a[lo];
    ptrdiff_t i = lo - 1, j = hi + 1;
    for (;;) {
        do { i++; } while (kucuk(&a[i], &p));
        do { j--; } while (kucuk(&p, &a[j]));
        if (i >= j) return j;
        takas(&a[i], &a[j]);
    }
}

/* Kucuk parcaya ozyinele, buyuk parcayi dongu ile isle */
static void hizli_rec(Kayit *a, ptrdiff_t lo, ptrdiff_t hi,
                      int strat) {
    while (lo < hi) {
        pivot_sec(a, lo, hi, strat);
        ptrdiff_t p = hoare(a, lo, hi);
        if (p - lo + 1 <= hi - p) {
            hizli_rec(a, lo, p, strat);
            lo = p + 1;
        } else {
            hizli_rec(a, p + 1, hi, strat);
            hi = p;
        }
    }
}

static void hizli_ilk(Kayit *a, size_t n) {
    if (n > 1) hizli_rec(a, 0, (ptrdiff_t)n - 1, 0);
}
static void hizli_medyan(Kayit *a, size_t n) {
    if (n > 1) hizli_rec(a, 0, (ptrdiff_t)n - 1, 2);
}
static void hizli_rastgele(Kayit *a, size_t n) {
    if (n > 1) hizli_rec(a, 0, (ptrdiff_t)n - 1, 1);
}

/* Lomuto: pivot son eleman. Esit degerlerde ayrim yapamaz. */
static ptrdiff_t lomuto(Kayit *a, ptrdiff_t lo, ptrdiff_t hi) {
    Kayit p = a[hi];
    ptrdiff_t i = lo;
    for (ptrdiff_t j = lo; j < hi; j++) {
        if (kucuk(&a[j], &p)) {
            takas(&a[i], &a[j]);
            i++;
        }
    }
    takas(&a[i], &a[hi]);
    return i;
}

static void lomuto_rec(Kayit *a, ptrdiff_t lo, ptrdiff_t hi) {
    if (lo >= hi) return;
    ptrdiff_t p = lomuto(a, lo, hi);
    lomuto_rec(a, lo, p - 1);
    lomuto_rec(a, p + 1, hi);
}

static void lomuto_sar(Kayit *a, size_t n) {
    if (n > 1) lomuto_rec(a, 0, (ptrdiff_t)n - 1);
}

/* Yigin: en buyuk ust, a[0..n-1] icinde */
static void elen(Kayit *a, ptrdiff_t n, ptrdiff_t i) {
    for (;;) {
        ptrdiff_t en = i, sol = 2 * i + 1, sag = 2 * i + 2;
        if (sol < n && kucuk(&a[en], &a[sol])) en = sol;
        if (sag < n && kucuk(&a[en], &a[sag])) en = sag;
        if (en == i) return;
        takas(&a[i], &a[en]);
        i = en;
    }
}

static void yigin_sirala(Kayit *a, size_t n_) {
    ptrdiff_t n = (ptrdiff_t)n_;
    for (ptrdiff_t i = n / 2 - 1; i >= 0; i--)
        elen(a, n, i);
    for (ptrdiff_t son = n - 1; son > 0; son--) {
        takas(&a[0], &a[son]);
        elen(a, son, 0);
    }
}

/* Sayma: anahtarlar 0..k-1 arasinda. Kararlilik icin sondan basla */
static void sayma_sirala(Kayit *a, size_t n, size_t k) {
    size_t *say = calloc(k, sizeof *say);
    Kayit *c = malloc(n * sizeof *c);
    if (!say || !c) { fprintf(stderr, "bellek yok\n"); exit(1); }
    for (size_t i = 0; i < n; i++)
        say[a[i].anahtar]++;
    for (size_t v = 1; v < k; v++)
        say[v] += say[v - 1];
    for (size_t i = n; i-- > 0; ) {
        c[--say[a[i].anahtar]] = a[i];
        yaz++;
    }
    memcpy(a, c, n * sizeof *a);
    yaz += n;
    free(say);
    free(c);
}

static void sayma_sar(Kayit *a, size_t n) {
    sayma_sirala(a, n, 1000000);
}

/* LSD radix: 8 bitlik kovalar, 4 gecis. Her gecis kararli. */
static void radix_sirala(Kayit *a, size_t n) {
    Kayit *c = malloc(n * sizeof *c);
    if (!c) { fprintf(stderr, "bellek yok\n"); exit(1); }
    for (unsigned sh = 0; sh < 32; sh += 8) {
        size_t say[256] = {0};
        for (size_t i = 0; i < n; i++)
            say[((unsigned)a[i].anahtar >> sh) & 255]++;
        size_t t = 0;
        for (int v = 0; v < 256; v++) {
            size_t s = say[v];
            say[v] = t;
            t += s;
        }
        for (size_t i = 0; i < n; i++)
            c[say[((unsigned)a[i].anahtar >> sh) & 255]++] = a[i];
        memcpy(a, c, n * sizeof *a);
    }
    free(c);
}

static int sirali(const Kayit *a, size_t n) {
    for (size_t i = 1; i < n; i++)
        if (a[i - 1].anahtar > a[i].anahtar) return 0;
    return 1;
}

static int kararli(const Kayit *a, size_t n) {
    for (size_t i = 1; i < n; i++)
        if (a[i - 1].anahtar == a[i].anahtar &&
            a[i - 1].sira > a[i].sira) return 0;
    return 1;
}

/* tur: 0 rastgele, 1 sirali, 2 ters, 3 yalniz 10 farkli deger */
static void veri_uret(Kayit *a, size_t n, int tur) {
    for (size_t i = 0; i < n; i++) {
        int k;
        switch (tur) {
        case 0:  k = (int)(rastgele() % 1000000); break;
        case 1:  k = (int)i; break;
        case 2:  k = (int)(n - i); break;
        default: k = (int)(rastgele() % 10); break;
        }
        a[i].anahtar = k;
        a[i].sira = (int)i;
    }
}

typedef void (*Siralayici)(Kayit *, size_t);

typedef struct {
    const char *ad;
    Siralayici f;
} Alg;

static const Alg algler[] = {
    {"kabarcik", kabarcik},         {"secmeli", secmeli},
    {"eklemeli", eklemeli},         {"birlestirme", birlestirme},
    {"hizli-ilk", hizli_ilk},       {"hizli-medyan", hizli_medyan},
    {"hizli-rast", hizli_rastgele}, {"lomuto", lomuto_sar},
    {"yigin", yigin_sirala},        {"sayma", sayma_sar},
    {"radix", radix_sirala},
};
#define ALG_SAYI (sizeof algler / sizeof algler[0])
static const char *turler[] = {"rastgele", "sirali", "ters",
                               "10 deger"};

/* Olcum: en iyi sure (3 tekrar). Sayac ve kararlilik son tekrardan */
static double olc(Siralayici f, const Kayit *ana, size_t n,
                  long long *k_out, int *kar_out) {
    Kayit *a = malloc(n * sizeof *a);
    double en = 1e30;
    if (!a) { fprintf(stderr, "bellek yok\n"); exit(1); }
    for (int t = 0; t < 3; t++) {
        memcpy(a, ana, n * sizeof *a);
        kars = yaz = 0;
        clock_t t0 = clock();
        f(a, n);
        double s = (double)(clock() - t0) / CLOCKS_PER_SEC;
        if (s < en) en = s;
        if (!sirali(a, n)) printf("HATA: sirali degil\n");
    }
    *k_out = kars;
    *kar_out = kararli(a, n);
    free(a);
    return en;
}

static int tablo_modu(void) {
    size_t n = 20000;
    static Kayit ana[20000];
    long long kt[ALG_SAYI][4];
    double zt[ALG_SAYI][4];
    int kr[ALG_SAYI][4];
    printf("n = %zu\n\n", n);
    for (int tur = 0; tur < 4; tur++) {
        veri_uret(ana, n, tur);
        for (size_t g = 0; g < ALG_SAYI; g++) {
            long long k = 0;
            int r = 0;
            zt[g][tur] = olc(algler[g].f, ana, n, &k, &r);
            kt[g][tur] = k;
            kr[g][tur] = r;
        }
    }
    printf("Karsilastirma sayisi:\n%-13s", "");
    for (int tur = 0; tur < 4; tur++) printf("%12s", turler[tur]);
    printf("\n");
    for (size_t g = 0; g < ALG_SAYI; g++) {
        printf("%-13s", algler[g].ad);
        for (int tur = 0; tur < 4; tur++)
            printf("%12lld", kt[g][tur]);
        printf("\n");
    }
    printf("\nSure (ms):\n%-13s", "");
    for (int tur = 0; tur < 4; tur++) printf("%12s", turler[tur]);
    printf("\n");
    for (size_t g = 0; g < ALG_SAYI; g++) {
        printf("%-13s", algler[g].ad);
        for (int tur = 0; tur < 4; tur++)
            printf("%12.2f", zt[g][tur] * 1000.0);
        printf("\n");
    }
    printf("\nKararli mi (10 deger):\n");
    for (size_t g = 0; g < ALG_SAYI; g++)
        printf("%-13s %s\n", algler[g].ad,
               kr[g][3] ? "evet" : "hayir");
    printf("\ndogrulama tamam\n");
    return 0;
}

static void kur(Kayit *a, const int *deger, int n) {
    for (int i = 0; i < n; i++) {
        a[i].anahtar = deger[i];
        a[i].sira = i;
    }
}

static int iz_modu(void) {
    Kayit a[6];
    int deger[6] = {5, 2, 4, 6, 1, 3};
    izle = 1;
    printf("kabarcik:\n");
    kur(a, deger, 6);
    kabarcik(a, 6);
    printf("secmeli:\n");
    kur(a, deger, 6);
    secmeli(a, 6);
    printf("eklemeli:\n");
    kur(a, deger, 6);
    eklemeli(a, 6);
    izle = 0;
    return 0;
}

static int olcek_modu(void) {
    static Kayit ana[1 << 20];
    size_t n;
    int kr;
    long long k;
    printf("O(n^2) grup, rastgele girdi (ms)\n");
    for (n = 2000; n <= 16000; n *= 2) {
        veri_uret(ana, n, 0);
        printf("n=%7zu kabarcik %9.2f secmeli %9.2f eklemeli %8.2f\n",
               n, olc(kabarcik, ana, n, &k, &kr) * 1000,
               olc(secmeli, ana, n, &k, &kr) * 1000,
               olc(eklemeli, ana, n, &k, &kr) * 1000);
    }
    printf("n log n grubu, rastgele girdi (ms)\n");
    for (n = 65536; n <= 1048576; n *= 2) {
        veri_uret(ana, n, 0);
        printf("n=%7zu birlestirme %7.2f hizli %8.2f yigin %8.2f"
               " radix %7.2f\n", n,
               olc(birlestirme, ana, n, &k, &kr) * 1000,
               olc(hizli_medyan, ana, n, &k, &kr) * 1000,
               olc(yigin_sirala, ana, n, &k, &kr) * 1000,
               olc(radix_sirala, ana, n, &k, &kr) * 1000);
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc > 1 && strcmp(argv[1], "iz") == 0) return iz_modu();
    if (argc > 1 && strcmp(argv[1], "olcek") == 0)
        return olcek_modu();
    return tablo_modu();
}
