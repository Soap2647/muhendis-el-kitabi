#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct Kenar {
    int hedef;
    struct Kenar *sonraki;
} Kenar;

typedef struct {
    int n;               /* dugum sayisi: 0 .. n-1 */
    Kenar **bas;         /* bas[u]: u'nun komsu listesinin basi */
} Graf;

Graf *graf_yap(int n) {
    Graf *g = malloc(sizeof *g);
    if (g == NULL) return NULL;
    g->n = n;
    g->bas = calloc((size_t)n, sizeof *g->bas);  /* hepsi NULL */
    if (g->bas == NULL) {
        free(g);
        return NULL;
    }
    return g;
}

static int yonlu_ekle(Graf *g, int u, int v) {
    Kenar *k = malloc(sizeof *k);
    if (k == NULL) return 0;
    k->hedef = v;
    k->sonraki = g->bas[u];   /* basa ekle: O(1) */
    g->bas[u] = k;
    return 1;
}

int kenar_ekle(Graf *g, int u, int v) {
    if (!yonlu_ekle(g, u, v)) return 0;
    return yonlu_ekle(g, v, u);   /* yonsuz: ters yon de */
}

void graf_serbest(Graf *g) {
    if (g == NULL) return;
    for (int u = 0; u < g->n; u++) {
        Kenar *k = g->bas[u];
        while (k != NULL) {
            Kenar *sonraki = k->sonraki;  /* once ilerini kaydet */
            free(k);
            k = sonraki;
        }
    }
    free(g->bas);
    free(g);
}

void liste_yaz(const Graf *g) {
    for (int u = 0; u < g->n; u++) {
        printf("%d:", u);
        for (const Kenar *k = g->bas[u]; k != NULL; k = k->sonraki)
            printf(" %d", k->hedef);
        printf("\n");
    }
}

void dfs(const Graf *g, int u, int *ziyaret) {
    ziyaret[u] = 1;
    printf("%d ", u);
    for (const Kenar *k = g->bas[u]; k != NULL; k = k->sonraki)
        if (!ziyaret[k->hedef])
            dfs(g, k->hedef, ziyaret);
}

void bfs(const Graf *g, int s) {
    int *ziyaret = calloc((size_t)g->n, sizeof *ziyaret);
    int *kuyruk = malloc((size_t)g->n * sizeof *kuyruk);
    if (ziyaret == NULL || kuyruk == NULL) {
        free(ziyaret);
        free(kuyruk);
        return;
    }
    size_t bas = 0, son = 0;
    kuyruk[son++] = s;
    ziyaret[s] = 1;
    while (bas < son) {
        int u = kuyruk[bas++];
        printf("%d ", u);
        for (const Kenar *k = g->bas[u]; k != NULL; k = k->sonraki) {
            if (!ziyaret[k->hedef]) {
                ziyaret[k->hedef] = 1;   /* isaretle */
                kuyruk[son++] = k->hedef;
            }
        }
    }
    free(ziyaret);
    free(kuyruk);
}

int main(void) {
    Graf *g = graf_yap(7);
    if (g == NULL) return 1;
    int kenarlar[][2] = {{0,1},{0,2},{1,3},{2,3},{3,4},{5,6}};
    for (size_t i = 0; i < 6; i++)
        kenar_ekle(g, kenarlar[i][0], kenarlar[i][1]);
    liste_yaz(g);
    int *z = calloc((size_t)g->n, sizeof *z);
    if (z == NULL) {
        graf_serbest(g);
        return 1;
    }
    printf("DFS: ");
    dfs(g, 0, z);
    printf("\nBFS: ");
    bfs(g, 0);
    printf("\n");
    free(z);
    graf_serbest(g);
    return 0;
}
