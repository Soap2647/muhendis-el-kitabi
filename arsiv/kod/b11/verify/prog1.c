#include <stddef.h>
#include <stdio.h>

#define N 7

/* Komsuluk matrisi: m[u][v] == 1 ise u ile v bagli. */
static int m[N][N];

void kenar_ekle(int u, int v) {
    m[u][v] = 1;
    m[v][u] = 1;      /* yonsuz: iki yonu de yaz */
}

int kenar_var_mi(int u, int v) {
    return m[u][v];          /* O(1): dogrudan bak */
}

int derece(int u) {
    int d = 0;
    for (int v = 0; v < N; v++)
        d += m[u][v];        /* satirdaki 1'leri say: O(V) */
    return d;
}

int main(void) {
    int kenarlar[][2] = {{0,1},{0,2},{1,3},{2,3},{3,4},{5,6}};
    size_t e = sizeof kenarlar / sizeof kenarlar[0];
    for (size_t i = 0; i < e; i++)
        kenar_ekle(kenarlar[i][0], kenarlar[i][1]);
    int toplam = 0;
    for (int u = 0; u < N; u++) {
        printf("derece(%d) = %d\n", u, derece(u));
        toplam += derece(u);
    }
    printf("toplam = %d, 2 * |E| = %zu\n", toplam, 2 * e);
    printf("1-3 var mi? %d, 0-5 var mi? %d\n",
           kenar_var_mi(1, 3), kenar_var_mi(0, 5));
    return 0;
}
