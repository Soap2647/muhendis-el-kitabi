/* strassen.c: naif carpim ve Strassen (C11) */
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

static unsigned long long durum = 42; /* xorshift64, tohum 42 */

static double rastgele(void)
{
    durum ^= durum << 13;
    durum ^= durum >> 7;
    durum ^= durum << 17;
    return (double)(durum % 2000001ULL) / 1000000.0 - 1.0;
}

/* c = a * b, n x n, satir sirali. O(n^3). */
static void naif(const double *a, const double *b, double *c,
                 size_t n)
{
    memset(c, 0, n * n * sizeof *c);
    for (size_t i = 0; i < n; i++)
        for (size_t k = 0; k < n; k++) {
            double aik = a[i * n + k];
            for (size_t j = 0; j < n; j++)
                c[i * n + j] += aik * b[k * n + j];
        }
}

/* n x n matrisin (qi, qj) ceyregini d'ye (n/2 x n/2) kopyala. */
static void ceyrek_al(const double *a, size_t n, size_t qi,
                      size_t qj, double *d)
{
    size_t h = n / 2;
    for (size_t i = 0; i < h; i++)
        memcpy(d + i * h, a + (qi * h + i) * n + qj * h,
               h * sizeof *d);
}

static void ceyrek_yaz(double *c, size_t n, size_t qi, size_t qj,
                       const double *s)
{
    size_t h = n / 2;
    for (size_t i = 0; i < h; i++)
        memcpy(c + (qi * h + i) * n + qj * h, s + i * h,
               h * sizeof *s);
}

/* c = a * b. n <= esik ise naif, aksi halde Strassen.
   Donus: 0 basarili, -1 bellek hatasi. */
static int strassen(const double *a, const double *b, double *c,
                    size_t n, size_t esik)
{
    if (n <= esik) {
        naif(a, b, c, n);
        return 0;
    }
    size_t h = n / 2, hh = h * h;
    /* 8 alt matris + 7 carpim + 2 gecici = 17 blok */
    double *buf = malloc(17 * hh * sizeof *buf);
    if (!buf)
        return -1;
    double *A11 = buf, *A12 = buf + hh, *A21 = buf + 2 * hh;
    double *A22 = buf + 3 * hh;
    double *B11 = buf + 4 * hh, *B12 = buf + 5 * hh;
    double *B21 = buf + 6 * hh, *B22 = buf + 7 * hh;
    double *M[7];
    for (int t = 0; t < 7; t++)
        M[t] = buf + (8 + t) * hh;
    double *T1 = buf + 15 * hh, *T2 = buf + 16 * hh;

    ceyrek_al(a, n, 0, 0, A11); ceyrek_al(a, n, 0, 1, A12);
    ceyrek_al(a, n, 1, 0, A21); ceyrek_al(a, n, 1, 1, A22);
    ceyrek_al(b, n, 0, 0, B11); ceyrek_al(b, n, 0, 1, B12);
    ceyrek_al(b, n, 1, 0, B21); ceyrek_al(b, n, 1, 1, B22);
    int hata = 0;
    /* M1 */
    for (size_t i = 0; i < hh; i++) {
        T1[i] = A11[i] + A22[i]; T2[i] = B11[i] + B22[i]; }
    hata |= strassen(T1, T2, M[0], h, esik);
    /* M2 */
    for (size_t i = 0; i < hh; i++) T1[i] = A21[i] + A22[i];
    hata |= strassen(T1, B11, M[1], h, esik);
    /* M3 */
    for (size_t i = 0; i < hh; i++) T1[i] = B12[i] - B22[i];
    hata |= strassen(A11, T1, M[2], h, esik);
    /* M4 */
    for (size_t i = 0; i < hh; i++) T1[i] = B21[i] - B11[i];
    hata |= strassen(A22, T1, M[3], h, esik);
    /* M5 */
    for (size_t i = 0; i < hh; i++) T1[i] = A11[i] + A12[i];
    hata |= strassen(T1, B22, M[4], h, esik);
    /* M6 */
    for (size_t i = 0; i < hh; i++) {
        T1[i] = A21[i] - A11[i]; T2[i] = B11[i] + B12[i]; }
    hata |= strassen(T1, T2, M[5], h, esik);
    /* M7 */
    for (size_t i = 0; i < hh; i++) {
        T1[i] = A12[i] - A22[i]; T2[i] = B21[i] + B22[i]; }
    hata |= strassen(T1, T2, M[6], h, esik);
    /* Sonuc ceyrekleri */
    for (size_t i = 0; i < hh; i++)
        T1[i] = M[0][i] + M[3][i] - M[4][i] + M[6][i];
    for (size_t i = 0; i < hh; i++)
        T2[i] = M[2][i] + M[4][i];
    ceyrek_yaz(c, n, 0, 0, T1); ceyrek_yaz(c, n, 0, 1, T2);
    for (size_t i = 0; i < hh; i++)
        T1[i] = M[1][i] + M[3][i];
    for (size_t i = 0; i < hh; i++)
        T2[i] = M[0][i] - M[1][i] + M[2][i] + M[5][i];
    ceyrek_yaz(c, n, 1, 0, T1); ceyrek_yaz(c, n, 1, 1, T2);
    free(buf);
    return hata ? -1 : 0;
}

static double maks_fark(const double *x, const double *y, size_t m)
{
    double d = 0.0;
    for (size_t i = 0; i < m; i++)
        if (fabs(x[i] - y[i]) > d)
            d = fabs(x[i] - y[i]);
    return d;
}

static void doldur(double *m, size_t cnt)
{
    for (size_t i = 0; i < cnt; i++)
        m[i] = rastgele();
}

int main(int argc, char **argv)
{
    (void)argv;
    size_t boyut[] = {8, 64, 128};
    for (size_t t = 0; t < 3; t++) {
        size_t n = boyut[t], m = n * n;
        double *a = malloc(m * sizeof *a), *b = malloc(m * sizeof *b);
        double *c1 = malloc(m * sizeof *c1);
        double *c2 = malloc(m * sizeof *c2);
        if (!a || !b || !c1 || !c2)
            return 1;
        doldur(a, m);
        doldur(b, m);
        naif(a, b, c1, n);
        if (strassen(a, b, c2, n, 8) != 0)  /* esik 8 */
            return 1;
        printf("n=%4zu maks_fark=%.3e\n", n, maks_fark(c1, c2, m));
        free(a); free(b); free(c1); free(c2);
    }
    if (argc > 1) {                          /* olcum modu */
        size_t n = 512, m = n * n;
        double *a = malloc(m * sizeof *a), *b = malloc(m * sizeof *b);
        double *c = malloc(m * sizeof *c);
        doldur(a, m);
        doldur(b, m);
        clock_t t0 = clock();
        naif(a, b, c, n);
        clock_t t1 = clock();
        strassen(a, b, c, n, 64);
        clock_t t2 = clock();
        printf("n=512 naif=%.3f s strassen(esik=64)=%.3f s\n",
               (double)(t1 - t0) / CLOCKS_PER_SEC,
               (double)(t2 - t1) / CLOCKS_PER_SEC);
        free(a); free(b); free(c);
    }
    return 0;
}
