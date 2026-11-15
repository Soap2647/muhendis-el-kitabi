#define _POSIX_C_SOURCE 199309L
/* matris.c - ayni O(n^3) carpimin uc erisim duzeni.
 * ijk : B'yi sutun sutun okur (her adim N*8 bayt atlar).
 * ikj : B'yi satir satir okur (bellek sirasi).
 * blok: 32x32 kutularla calisir; kutular L1'e sigar.
 * Sonuclar tam sayi oldugu icin toplamlar birebir karsilastirilir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 matris.c -o matris
 */
#include <stdio.h>
#include <string.h>
#include <time.h>

#define N 1024
#define BL 32
#define DENEME 3

static double A[N][N], B[N][N], C[N][N];   /* global: yigin degil */

static double simdi_s(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

static void ijk(void)
{
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++) {
            double s = 0;
            for (int k = 0; k < N; k++)
                s += A[i][k] * B[k][j];
            C[i][j] = s;
        }
}

static void ikj(void)
{
    for (int i = 0; i < N; i++)
        for (int k = 0; k < N; k++) {
            double a = A[i][k];
            for (int j = 0; j < N; j++)
                C[i][j] += a * B[k][j];
        }
}

static void blok(void)
{
    for (int ii = 0; ii < N; ii += BL)
        for (int kk = 0; kk < N; kk += BL)
            for (int jj = 0; jj < N; jj += BL)
                for (int i = ii; i < ii + BL; i++)
                    for (int k = kk; k < kk + BL; k++) {
                        double a = A[i][k];
                        for (int j = jj; j < jj + BL; j++)
                            C[i][j] += a * B[k][j];
                    }
}

static double toplam(void)
{
    double s = 0;
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            s += C[i][j];
    return s;
}

static void calistir(const char *ad, void (*f)(void))
{
    double sn[DENEME], ss = 0;
    for (int r = 0; r < DENEME; r++) {
        memset(C, 0, sizeof C);
        double t0 = simdi_s();
        f();
        sn[r] = simdi_s() - t0;
    }
    ss = toplam();
    /* medyan: 3 denemenin ortancasi */
    double a = sn[0], b = sn[1], c = sn[2], m;
    if ((a <= b && b <= c) || (c <= b && b <= a)) m = b;
    else if ((b <= a && a <= c) || (c <= a && a <= b)) m = a;
    else m = c;
    printf("%-6s %8.3f s   toplam=%.0f\n", ad, m, ss);
}

int main(void)
{
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++) {
            A[i][j] = (i * j) % 7 + 1;
            B[i][j] = (i + j) % 5 + 1;
        }
    calistir("ijk", ijk);
    calistir("ikj", ikj);
    calistir("blok", blok);
    return 0;
}
