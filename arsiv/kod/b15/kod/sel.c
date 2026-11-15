#include <stdio.h>
#include <stdlib.h>

/* 0 = bos, 1 = duvar, 2 = doldurulmus. Izgara n x n. */
static int n;
static unsigned char *izgara;
static long doldu = 0, derinlik = 0, en_derin = 0;

/* Ozyinelemeli flood fill: her cagri bir hucre. */
static void doldur(int r, int c) {
    if (r < 0 || c < 0 || r >= n || c >= n)
        return;
    if (izgara[r * n + c] != 0)
        return;
    izgara[r * n + c] = 2;
    doldu++;
    derinlik++;
    if (derinlik > en_derin)
        en_derin = derinlik;
    doldur(r + 1, c);
    doldur(r - 1, c);
    doldur(r, c + 1);
    doldur(r, c - 1);
    derinlik--;
}

/* Yigin tabanli surum: cagri yigini yerine kendi yiginimiz.
   Hucre itilirken isaretlenir; boylece her hucre en fazla
   bir kez yiginda olur ve yigin n*n cifti asmaz. */
static void doldur_yigin(int r0, int c0) {
    int *yigin = malloc((size_t)n * n * 2 * sizeof *yigin);
    if (yigin == NULL)
        return;
    int dr[4] = {1, -1, 0, 0};
    int dc[4] = {0, 0, 1, -1};
    long tepe = 0;
    izgara[r0 * n + c0] = 2;
    doldu++;
    yigin[tepe++] = r0;
    yigin[tepe++] = c0;
    while (tepe > 0) {
        int c = yigin[--tepe];
        int r = yigin[--tepe];
        for (int k = 0; k < 4; k++) {
            int nr = r + dr[k], nc = c + dc[k];
            if (nr < 0 || nc < 0 || nr >= n || nc >= n)
                continue;
            if (izgara[nr * n + nc] != 0)
                continue;
            izgara[nr * n + nc] = 2;
            doldu++;
            yigin[tepe++] = nr;
            yigin[tepe++] = nc;
        }
    }
    free(yigin);
}

int main(int argc, char **argv) {
    if (argc != 3)
        return 1;
    int yigin_modu = argv[1][0] == 'y';
    n = atoi(argv[2]);
    if (n <= 0) {
        printf("n=%d doldu=0\n", n);
        return 0;
    }
    izgara = calloc((size_t)n * n, 1);
    if (izgara == NULL)
        return 1;
    if (yigin_modu) {
        doldur_yigin(0, 0);
        printf("n=%d doldu=%ld\n", n, doldu);
    } else {
        doldur(0, 0);
        printf("n=%d doldu=%ld en_derin=%ld\n", n, doldu, en_derin);
    }
    free(izgara);
    return 0;
}
