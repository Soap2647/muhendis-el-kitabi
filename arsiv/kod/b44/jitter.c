/* jitter.c - setitimer ile periyodik SIGALRM olcumu.
 * Bu bir ANA BILGISAYAR (Linux / WSL2) olcumudur, MCU degil.
 * Isleyici yalnizca sayaci artirir (async-signal-safe kural).
 * Kullanim: ./jitter <ornek_sayisi> <periyot_us> */
#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t sayac = 0;

static void isleyici(int sig)
{
    (void)sig;
    sayac++;
}

static long long ns_simdi(void)
{
    struct timespec t;

    clock_gettime(CLOCK_MONOTONIC, &t);
    return (long long)t.tv_sec * 1000000000LL + t.tv_nsec;
}

int main(int argc, char **argv)
{
    int n = argc > 1 ? atoi(argv[1]) : 2000;
    int us = argc > 2 ? atoi(argv[2]) : 1000;
    long long *zaman = malloc(sizeof(long long) * (size_t)(n + 1));
    struct sigaction sa = {0};
    struct itimerval it = {0};
    int k = 0, son = 0;

    if (!zaman) return 1;
    sa.sa_handler = isleyici;
    sigaction(SIGALRM, &sa, NULL);
    it.it_interval.tv_usec = us;
    it.it_value.tv_usec = us;
    setitimer(ITIMER_REAL, &it, NULL);

    zaman[k++] = ns_simdi();
    while (k <= n) {
        pause();                      /* SIGALRM gelene kadar uyu */
        if (sayac != son) {           /* ana dongude damgala */
            son = sayac;
            zaman[k++] = ns_simdi();
        }
    }
    it.it_value.tv_usec = 0;          /* zamanlayiciyi durdur */
    it.it_interval.tv_usec = 0;
    setitimer(ITIMER_REAL, &it, NULL);

    printf("aralik_us\n");
    for (int i = 1; i <= n; i++)
        printf("%.3f\n", (zaman[i] - zaman[i - 1]) / 1000.0);
    free(zaman);
    return 0;
}
