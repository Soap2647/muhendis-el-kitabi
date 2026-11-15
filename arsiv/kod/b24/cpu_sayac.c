/* Saat frekansı tahmini, rdtsc, sistem çağrısı maliyeti (Linux) */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <x86intrin.h>

#define ZINCIR_TEKRAR 1000000   /* her turda 1000 bağımlı add */
#define OLCUM 5
#define SYS_TEKRAR 3000000

static volatile long sink;

static double simdi_s(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}

/* 1000 bağımlı 'add': her biri bir öncekinin sonucunu bekler */
static inline uint64_t zincir1000(uint64_t x)
{
    __asm__ volatile(
        ".rept 1000\n\t"
        "add $1, %0\n\t"
        ".endr"
        : "+r"(x));
    return x;
}

__attribute__((noinline))
static long kucuk(long x)
{
    return x + 1;
}

static int cmp_dbl(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

int main(void)
{
    double t[OLCUM], ts[OLCUM], sys_t[OLCUM], cag_t[OLCUM];
    double dt[OLCUM];
    uint64_t tsc0, tsc1;
    uint64_t x = 0;

    /* 1) bağımlı add zinciri: varsayım her add 1 çevrim */
    for (int k = 0; k < OLCUM; k++) {
        double b = simdi_s();
        for (long r = 0; r < ZINCIR_TEKRAR; r++)
            x = zincir1000(x);
        t[k] = simdi_s() - b;
    }
    /* 2) aynı döngü rdtsc ile */
    for (int k = 0; k < OLCUM; k++) {
        double b = simdi_s();
        tsc0 = __rdtsc();
        for (long r = 0; r < ZINCIR_TEKRAR; r++)
            x = zincir1000(x);
        tsc1 = __rdtsc();
        ts[k] = simdi_s() - b;
        sys_t[k] = (double)(tsc1 - tsc0);
    }
    /* 3) sistem çağrısı getppid ve doğrudan çağrı */
    for (int k = 0; k < OLCUM; k++) {
        double b = simdi_s();
        for (long r = 0; r < SYS_TEKRAR; r++)
            sink = syscall(SYS_getppid);
        cag_t[k] = simdi_s() - b;
    }
    for (int k = 0; k < OLCUM; k++) {
        double b = simdi_s();
        for (long r = 0; r < SYS_TEKRAR; r++)
            sink = kucuk((long)r);
        dt[k] = simdi_s() - b;
    }
    qsort(t, OLCUM, sizeof t[0], cmp_dbl);
    qsort(ts, OLCUM, sizeof ts[0], cmp_dbl);
    qsort(sys_t, OLCUM, sizeof sys_t[0], cmp_dbl);
    qsort(cag_t, OLCUM, sizeof cag_t[0], cmp_dbl);
    qsort(dt, OLCUM, sizeof dt[0], cmp_dbl);

    double adim = (double)ZINCIR_TEKRAR * 1000.0;
    printf("olcum,deger\n");
    printf("add_zinciri_en_az_s,%.4f\n", t[0]);
    printf("frekans_tahmini_GHz,%.3f\n", adim / t[0] / 1e9);
    printf("tsc_hizi_GHz,%.3f\n", sys_t[0] / ts[0] / 1e9);
    printf("syscall_getppid_ns,%.2f\n", cag_t[0] * 1e9 / SYS_TEKRAR);
    printf("dogrudan_cagri_ns,%.2f\n", dt[0] * 1e9 / SYS_TEKRAR);
    (void)x;
    return 0;
}
