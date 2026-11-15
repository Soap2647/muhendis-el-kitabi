/* msh.c: minik kabuk. Destek: argümanlar, |, <, >, &, cd, exit.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11
 *          -D_POSIX_C_SOURCE=200809L msh.c -o msh
 * HATA_ACIK tanımlanırsa ebeveyn boru yazma ucunu kapatmaz. */
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define MAX_ARG   64
#define MAX_KOMUT 8

typedef struct {
    char *argv[MAX_ARG];
    char *giris;               /* < dosyası, NULL ise yok */
    char *cikis;               /* > dosyası, NULL ise yok */
} Komut;

static volatile sig_atomic_t g_cocuk_bitti = 0;

/* İşleyici yalnızca bayrak kaldırır: printf, malloc
 * gibi async-signal-safe olmayan işlere girilmez. */
static void on_chld(int sig)
{
    (void)sig;
    g_cocuk_bitti = 1;
}

/* Satırı boru/yönlendirme/arka plan işaretlerine göre böler.
 * Dönüş: komut sayısı (>0), 0 boş satır, -1 sözdizimi hatası. */
static int ayristir(char *satir, Komut kom[], int *arka)
{
    int k = 0, a = 0;
    *arka = 0;
    memset(kom, 0, sizeof(Komut) * MAX_KOMUT);
    char *tok = strtok(satir, " \t\n");
    while (tok) {
        if (strcmp(tok, "|") == 0) {
            if (a == 0 || k + 1 >= MAX_KOMUT) return -1;
            kom[k].argv[a] = NULL;
            k++;
            a = 0;
        } else if (strcmp(tok, "<") == 0 || strcmp(tok, ">") == 0) {
            char *dosya = strtok(NULL, " \t\n");
            if (!dosya) return -1;
            if (tok[0] == '<') kom[k].giris = dosya;
            else               kom[k].cikis = dosya;
        } else if (strcmp(tok, "&") == 0) {
            *arka = 1;
        } else {
            if (a >= MAX_ARG - 1) return -1;
            kom[k].argv[a++] = tok;
        }
        tok = strtok(NULL, " \t\n");
    }
    if (a == 0)                  /* "ls |" gibi eksik komut */
        return (k == 0) ? 0 : -1;
    kom[k].argv[a] = NULL;
    return k + 1;
}

/* Ebeveyn bir çocuğu bekler. EINTR gelirse yeniden dener. */
static void bekle(pid_t pid)
{
    int durum = 0;
    while (waitpid(pid, &durum, 0) < 0 && errno == EINTR)
        ;
    if (WIFEXITED(durum) && WEXITSTATUS(durum) != 0)
        printf("[çıkış kodu %d]\n", WEXITSTATUS(durum));
    else if (WIFSIGNALED(durum))
        printf("[sinyal %d ile sonlandı]\n", WTERMSIG(durum));
}

/* Bitmiş arka plan çocuklarını topla (zombi temizliği).
 * WNOHANG: bitmiş çocuk yoksa asla bekleme yapma. */
static void arka_plan_topla(void)
{
    int durum;
    pid_t p;
    while ((p = waitpid(-1, &durum, WNOHANG)) > 0)
        printf("[arka plan %d bitti]\n", (int)p);
}

/* Boru hattını kur: her komut için fork. Komut i'nin
 * stdin'i önceki borudan, stdout'u sonraki boruya gelir. */
static void calistir(Komut kom[], int adet, int arka)
{
    pid_t pids[MAX_KOMUT];
    int onceki_oku = -1;

    for (int i = 0; i < adet; i++) {
        int boru[2] = {-1, -1};
        if (i < adet - 1 && pipe(boru) < 0) {
            perror("pipe");
            return;
        }
        pid_t pid = fork();
        if (pid < 0) {
            perror("fork");
            return;
        }
        if (pid == 0) {          /* ÇOCUK: exec öncesi ayar */
            if (onceki_oku != -1) {
                dup2(onceki_oku, STDIN_FILENO);
                close(onceki_oku);
            }
            if (i < adet - 1) {
                dup2(boru[1], STDOUT_FILENO);
                close(boru[1]);
                close(boru[0]);
            }
            if (kom[i].giris) {
                int fd = open(kom[i].giris, O_RDONLY);
                if (fd < 0) { perror(kom[i].giris); _exit(127); }
                dup2(fd, STDIN_FILENO);
                close(fd);
            }
            if (kom[i].cikis) {
                int fd = open(kom[i].cikis,
                              O_WRONLY | O_CREAT | O_TRUNC, 0644);
                if (fd < 0) { perror(kom[i].cikis); _exit(127); }
                dup2(fd, STDOUT_FILENO);
                close(fd);
            }
            execvp(kom[i].argv[0], kom[i].argv);
            /* exec dönerse buraya gelinir */
            perror(kom[i].argv[0]);
            _exit(127);          /* exit değil: tamponu boşaltma */
        }
        /* EBEVEYN: artık gerekmeyen uçları kapat */
        pids[i] = pid;
        if (onceki_oku != -1) close(onceki_oku);
        if (boru[1] != -1) {
#ifndef HATA_ACIK
            close(boru[1]);
#endif
        }
        onceki_oku = boru[0];
    }

    if (arka) {
        printf("[arka plan pid=%d]\n", (int)pids[adet - 1]);
        return;
    }
    for (int i = 0; i < adet; i++)
        bekle(pids[i]);
}

int main(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_chld;
    /* SA_RESTART: yarım kalan sistem çağrısı devam eder */
    sa.sa_flags = SA_RESTART;
    sigaction(SIGCHLD, &sa, NULL);

    char satir[512];
    Komut kom[MAX_KOMUT];
    for (;;) {
        arka_plan_topla();
        printf("msh> ");
        fflush(stdout);
        if (!fgets(satir, sizeof satir, stdin))
            break;               /* Ctrl+D */

        int arka = 0;
        int adet = ayristir(satir, kom, &arka);
        if (adet == 0) continue;
        if (adet < 0) {
            printf("sözdizimi hatası\n");
            continue;
        }
        if (strcmp(kom[0].argv[0], "exit") == 0) break;
        if (strcmp(kom[0].argv[0], "cd") == 0 && adet == 1) {
            /* cd bir yerleşik: çocukta yapılsa ebeveyn
             * dizini değişmez */
            const char *hedef = kom[0].argv[1];
            if (!hedef) hedef = getenv("HOME");
            if (chdir(hedef) < 0) perror("cd");
            continue;
        }
        calistir(kom, adet, arka);
    }
    return 0;
}
