/* b28_6_fsync_olcum.c: 4 KiB yazma ve kalıcılık gecikmesi.
 * Çıktı: mod,iter,us (her satır bir yazma turu) */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>

#define N      300     /* ölçülen tur sayısı */
#define ISIN   20      /* ısınma turları, yazılmaz */
#define BLOK   4096

static double simdi_us(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e6 + t.tv_nsec / 1e3;
}

/* kip: 0 yalnız write, 1 fdatasync, 2 fsync */
static void olc(const char *mod, int kip)
{
    static char blok[BLOK];
    memset(blok, 'x', sizeof blok);
    int fd = open("fsync_test.dat",
                  O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); exit(1); }

    for (int i = 0; i < N + ISIN; i++) {
        double t0 = simdi_us();
        if (write(fd, blok, BLOK) != BLOK) {
            perror("write"); exit(1);
        }
        if (kip == 1 && fdatasync(fd) < 0) {
            perror("fdatasync"); exit(1);
        }
        if (kip == 2 && fsync(fd) < 0) {
            perror("fsync"); exit(1);
        }
        double t1 = simdi_us();
        if (i >= ISIN)
            printf("%s,%d,%.1f\n", mod, i - ISIN, t1 - t0);
    }
    close(fd);
    unlink("fsync_test.dat");
}

int main(void)
{
    printf("mod,iter,us\n");
    olc("yalniz_write", 0);
    olc("fdatasync", 1);
    olc("fsync", 2);
    return 0;
}
