/* b28_2_kisa_io.c: kısa okuma ve tam_oku / tam_yaz */
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/wait.h>

/* Tüm n baytı okur; kısa okumada tekrar dener. */
ssize_t tam_oku(int fd, void *tampon, size_t n)
{
    size_t toplam = 0;
    while (toplam < n) {
        ssize_t r = read(fd, (char *)tampon + toplam, n - toplam);
        if (r < 0) {
            if (errno == EINTR) continue;   /* sinyal: tekrar dene */
            return -1;                       /* gerçek hata */
        }
        if (r == 0) break;                   /* EOF */
        toplam += (size_t)r;
    }
    return (ssize_t)toplam;
}

/* Tüm n baytı yazar; kısa yazmada tekrar dener. */
ssize_t tam_yaz(int fd, const void *tampon, size_t n)
{
    size_t toplam = 0;
    while (toplam < n) {
        ssize_t w = write(fd,
                          (const char *)tampon + toplam, n - toplam);
        if (w < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        toplam += (size_t)w;
    }
    return (ssize_t)toplam;
}

int main(void)
{
    int boru[2];
    if (pipe(boru) < 0) { perror("pipe"); return 1; }

    pid_t pid = fork();
    if (pid == 0) {                      /* yazıcı çocuk */
        close(boru[0]);
        char parca[1000];
        memset(parca, 'a', sizeof parca);
        for (int i = 0; i < 8; i++) {
            tam_yaz(boru[1], parca, sizeof parca);
            usleep(30000);               /* 30 ms bekle */
        }
        close(boru[1]);
        _exit(0);
    }
    close(boru[1]);

    char tampon[8000];
    ssize_t r = read(boru[0], tampon, sizeof tampon);
    printf("tek read: istenen=%zu, dönen=%zd\n", sizeof tampon, r);

    ssize_t kalan = tam_oku(boru[0], tampon + r, sizeof tampon - r);
    printf("tam_oku kalan=%zd bayt okudu\n", kalan);

    ssize_t son = tam_oku(boru[0], tampon, 1);
    printf("EOF sonrası tam_oku=%zd\n", son);

    close(boru[0]);
    wait(NULL);
    return 0;
}
