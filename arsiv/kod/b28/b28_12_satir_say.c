/* b28_12_satir_say.c: sınırlı tamponla satır sayma */
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>

/* Dosyadaki '\n' sayısını döner; hata olursa -1. */
long satir_say(const char *yol, size_t tampon_boyu)
{
    char *t = malloc(tampon_boyu);
    if (!t) return -1;
    int fd = open(yol, O_RDONLY);
    if (fd < 0) { free(t); return -1; }

    long satir = 0;
    for (;;) {
        ssize_t r = read(fd, t, tampon_boyu);
        if (r < 0) {
            if (errno == EINTR) continue;
            satir = -1;
            break;
        }
        if (r == 0) break;                   /* EOF */
        for (ssize_t i = 0; i < r; i++)
            if (t[i] == '\n') satir++;
    }
    close(fd);
    free(t);
    return satir;
}

int main(void)
{
    const char *yol = "satirlar.txt";
    int fd = open(yol, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) return 1;
    if (write(fd, "ab\ncd\nef\n", 9) != 9) return 1;
    close(fd);

    size_t boylar[] = {1, 4, 100};
    for (int i = 0; i < 3; i++)
        printf("tampon=%3zu -> satır=%ld\n",
               boylar[i], satir_say(yol, boylar[i]));
    return 0;
}
