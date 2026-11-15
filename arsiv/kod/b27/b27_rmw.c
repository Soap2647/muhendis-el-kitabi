/* b27_rmw.c - sayac++ yaris kosulu ve kayip guncelleme.
 * Derleme: gcc -O0 -Wall -Wextra -std=c11 -pthread b27_rmw.c
 * Kullanim: ./a.out <mod> <thread_sayisi>
 *   mod: plain | volatile | atomic | mutex
 */
#define _POSIX_C_SOURCE 200809L
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>

#define ITER 10000000L

static long plain_sayac;
static volatile long vol_sayac;
static atomic_long at_sayac;
static long mtx_sayac;
static pthread_mutex_t kilit = PTHREAD_MUTEX_INITIALIZER;

static void art_plain(void)    { plain_sayac++; }
static void art_volatile(void) { vol_sayac++; }
static void art_atomic(void)   { atomic_fetch_add(&at_sayac, 1); }

static void art_mutex(void)
{
    pthread_mutex_lock(&kilit);
    mtx_sayac++;
    pthread_mutex_unlock(&kilit);
}

typedef void (*artis_fn)(void);

struct is_arg {
    artis_fn f;
    long n;
};

static void *is_parcacik(void *p)
{
    struct is_arg *a = p;
    for (long i = 0; i < a->n; i++)
        a->f();
    return NULL;
}

static double simdi(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr, "kullanim: %s <mod> <thread>\n", argv[0]);
        return 1;
    }
    const char *mod = argv[1];
    int t = atoi(argv[2]);
    artis_fn f;
    if (!strcmp(mod, "plain"))         f = art_plain;
    else if (!strcmp(mod, "volatile")) f = art_volatile;
    else if (!strcmp(mod, "atomic"))   f = art_atomic;
    else if (!strcmp(mod, "mutex"))    f = art_mutex;
    else { fprintf(stderr, "bilinmeyen mod\n"); return 1; }

    pthread_t th[64];
    struct is_arg a = { f, ITER };
    double t0 = simdi();
    for (int i = 0; i < t; i++)
        pthread_create(&th[i], NULL, is_parcacik, &a);
    for (int i = 0; i < t; i++)
        pthread_join(th[i], NULL);
    double dt = simdi() - t0;

    long gercek;
    if (f == art_plain)         gercek = plain_sayac;
    else if (f == art_volatile) gercek = vol_sayac;
    else if (f == art_atomic)   gercek = atomic_load(&at_sayac);
    else                        gercek = mtx_sayac;

    long beklenen = (long)t * ITER;
    printf("mod=%-8s thread=%d n=%ld\n", mod, t, ITER);
    printf("beklenen = %ld\n", beklenen);
    printf("gercek   = %ld\n", gercek);
    printf("kayip    = %ld (%.2f%%)\n", beklenen - gercek,
           100.0 * (beklenen - gercek) / beklenen);
    printf("sure     = %.3f s\n", dt);
    return 0;
}
