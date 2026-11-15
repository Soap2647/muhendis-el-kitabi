/* talep.c - talep uzerine sayfalama (demand paging) gozlemi.
 * mmap ile 16 sayfalik sanal bolge ayirir. Hicbir sayfaya
 * dokunmadan /proc/self/pagemap icindeki "present" bitini okur.
 * Sonra yalnizca 4. sayfaya yazar ve degisimi gozlemler.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 talep.c -o talep
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/resource.h>

#define SAYFA 4096
#define SAYI 16

static long kucuk_hata(void)
{
    struct rusage u;
    getrusage(RUSAGE_SELF, &u);
    return u.ru_minflt;
}

/* Sanal adresin sayfa tablosu girdisi "present" mi? */
static int mevcut(int fd, char *va)
{
    uint64_t e = 0;
    off_t ofs = ((uintptr_t)va / SAYFA) * 8;
    if (pread(fd, &e, sizeof e, ofs) != sizeof e) return -1;
    return (int)((e >> 63) & 1);
}

static void goster(const char *etiket, int fd, char *bolge)
{
    printf("%s", etiket);
    for (int i = 0; i < SAYI; i++)
        printf("%d", mevcut(fd, bolge + i * SAYFA));
    printf("\n");
}

int main(void)
{
    int fd = open("/proc/self/pagemap", O_RDONLY);
    char *bolge = mmap(NULL, SAYI * SAYFA, PROT_READ | PROT_WRITE,
                       MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (fd < 0 || bolge == MAP_FAILED) { perror("hata"); return 1; }

    goster("dokunmadan once : ", fd, bolge);

    long h0 = kucuk_hata();
    bolge[3 * SAYFA] = 42;                 /* 4. sayfaya ilk yazma */
    long h1 = kucuk_hata();
    goster("4. sayfaya yazma: ", fd, bolge);
    printf("kucuk hata (1 yazma): %ld\n", h1 - h0);

    h0 = kucuk_hata();
    for (int i = 0; i < SAYI; i++)
        bolge[i * SAYFA] = 1;              /* kalan sayfalar */
    printf("kalan 15 sayfa      : %ld kucuk hata\n",
           kucuk_hata() - h0);
    goster("hepsi dokundu    : ", fd, bolge);

    munmap(bolge, SAYI * SAYFA);
    close(fd);
    return 0;
}
