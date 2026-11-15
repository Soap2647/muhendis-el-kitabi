/* b28_11_append.c: O_APPEND ile eşzamanlı kayıt ekleme.
 *   ./b28_11_append ekle   tek write() ile O_APPEND (doğru)
 *   ./b28_11_append konum  lseek(SEEK_END) + write (yanlış) */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/stat.h>

#define SUREC   4
#define KAYIT   2000
#define BOY     100     /* bir kayıt: satır sonu dahil bayt */

static void surec_yaz(const char *yol, int s, int ekle)
{
    int fd = open(yol, O_WRONLY | (ekle ? O_APPEND : 0));
    char kayit[BOY];
    for (int i = 0; i < KAYIT; i++) {
        int n = snprintf(kayit, sizeof kayit, "surec=%d kayit=%05d ",
                         s, i);
        memset(kayit + n, '.', BOY - 1 - n);
        kayit[BOY - 1] = '\n';
        if (!ekle)
            lseek(fd, 0, SEEK_END);      /* ayrı adım: yarış */
        if (write(fd, kayit, BOY) != BOY) _exit(2);
    }
    close(fd);
}

/* Her satırı kontrol et: biçimi doğru mu, her (süreç, kayıt)
 * çiftinden tam bir tane var mı? */
static void dogrula(const char *yol)
{
    static int gorulen[SUREC][KAYIT];
    char satir[BOY + 1];
    struct stat st;
    stat(yol, &st);
    FILE *f = fopen(yol, "r");
    int dogru = 0, bozuk = 0;
    while (fgets(satir, sizeof satir, f)) {
        int s, i;
        if (strlen(satir) == BOY &&
            sscanf(satir, "surec=%d kayit=%d", &s, &i) == 2 &&
            s >= 0 && s < SUREC && i >= 0 && i < KAYIT) {
            gorulen[s][i]++;
            dogru++;
        } else {
            bozuk++;
        }
    }
    fclose(f);
    int eksik = 0;
    for (int s = 0; s < SUREC; s++)
        for (int i = 0; i < KAYIT; i++)
            if (gorulen[s][i] != 1) eksik++;
    printf("boyut=%ld (beklenen %d)\n", (long)st.st_size,
           SUREC * KAYIT * BOY);
    printf("dogru=%d bozuk=%d eksik/fazla=%d\n", dogru, bozuk, eksik);
}

int main(int argc, char **argv)
{
    int ekle = !(argc > 1 && strcmp(argv[1], "konum") == 0);
    const char *yol = "kayitlar.log";
    int fd0 = open(yol, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd0 < 0) return 1;
    close(fd0);

    for (int s = 0; s < SUREC; s++) {
        pid_t pid = fork();
        if (pid == 0) {
            surec_yaz(yol, s, ekle);
            _exit(0);
        }
    }
    while (wait(NULL) > 0)
        ;
    printf("mod=%s\n", ekle ? "O_APPEND" : "lseek+write");
    dogrula(yol);
    return 0;
}
