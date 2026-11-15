#include <stddef.h>
#include <stdio.h>

#define N 7

static int m[N][N];       /* komsuluk matrisi (yonsuz) */
static int ziyaret[N];

static void kenar(int u, int v) {
    m[u][v] = 1;
    m[v][u] = 1;
}

static void dfs(int u) {
    ziyaret[u] = 1;
    for (int v = 0; v < N; v++)
        if (m[u][v] && !ziyaret[v])
            dfs(v);
}

int main(void) {
    kenar(0, 1); kenar(0, 2); kenar(1, 3);
    kenar(2, 3); kenar(3, 4); kenar(5, 6);
    int bilesen = 0;
    for (int u = 0; u < N; u++) {
        if (!ziyaret[u]) {
            dfs(u);
            bilesen++;
            printf("bilesen %d, baslangic: %d\n", bilesen, u);
        }
    }
    printf("toplam bilesen: %d\n", bilesen);
    return 0;
}
