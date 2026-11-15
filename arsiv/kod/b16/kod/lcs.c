/* lcs.c: en uzun ortak altdizi, tablo ve geri izleme (C11) */
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* dp[i][j]: a'nin ilk i, b'nin ilk j karakteri icin LCS */
static size_t *tablo_olustur(const char *a, const char *b,
                             size_t n, size_t m) {
    size_t w = m + 1;
    size_t *dp = calloc((n + 1) * w, sizeof *dp);
    if (dp == NULL)
        return NULL;
    for (size_t i = 1; i <= n; i++) {
        for (size_t j = 1; j <= m; j++) {
            if (a[i - 1] == b[j - 1])
                dp[i * w + j] = dp[(i - 1) * w + (j - 1)] + 1;
            else if (dp[(i - 1) * w + j] >= dp[i * w + (j - 1)])
                dp[i * w + j] = dp[(i - 1) * w + j];
            else
                dp[i * w + j] = dp[i * w + (j - 1)];
        }
    }
    return dp;
}

/* Geri izleme: LCS dizgisini sonuc tamponuna yazar. */
static void geri_izle(const size_t *dp, const char *a, const char *b,
                      size_t n, size_t m, char *sonuc) {
    size_t w = m + 1, i = n, j = m, k = dp[n * w + m];
    sonuc[k] = '\0';
    while (i > 0 && j > 0) {
        if (a[i - 1] == b[j - 1]) {
            sonuc[--k] = a[i - 1];
            i--;
            j--;
        } else if (dp[(i - 1) * w + j] >= dp[i * w + (j - 1)]) {
            i--;
        } else {
            j--;
        }
    }
}

int main(void) {
    const char *a = "ABCBDAB";
    const char *b = "BDCABA";
    size_t n = strlen(a), m = strlen(b);
    size_t *dp = tablo_olustur(a, b, n, m);
    if (dp == NULL)
        return 1;
    size_t uzunluk = dp[n * (m + 1) + m];
    char *sonuc = malloc(uzunluk + 1);
    if (sonuc == NULL) {
        free(dp);
        return 1;
    }
    geri_izle(dp, a, b, n, m, sonuc);
    printf("LCS uzunlugu: %zu\n", uzunluk);
    printf("LCS: %s\n", sonuc);
    free(sonuc);
    free(dp);
    return 0;
}
