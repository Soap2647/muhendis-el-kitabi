/* sig.c: SIGTERM yakalanır; SIGKILL yakalanamaz.
 * Ebeveyn iki çocuk oluşturur ve sinyalleri kendisi gönderir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 sig.c -o sig */
#define _DEFAULT_SOURCE
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static volatile sig_atomic_t g_dur = 0;

/* İşleyici: yalnızca bayrak kaldırır ve write(2)
 * kullanır. printf burada async-signal-safe değildir. */
static void on_term(int sig)
{
    static const char m[] = "[çocuk] SIGTERM alındı\n";
    (void)sig;
    g_dur = 1;
    ssize_t r = write(STDOUT_FILENO, m, sizeof m - 1);
    (void)r;
}

static void cocuk_bekle_term(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_term;
    sigaction(SIGTERM, &sa, NULL);
    while (!g_dur)
        pause();             /* sinyal gelene kadar uyu */
    printf("[çocuk] temiz kapanış\n");
    exit(3);
}

int main(void)
{
    struct sigaction sa;
    int durum = 0;
    /* fork öncesi tampon kopyalanmasın */
    setvbuf(stdout, NULL, _IONBF, 0);
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_term;
    if (sigaction(SIGKILL, &sa, NULL) < 0)
        printf("SIGKILL için sigaction: %s\n", strerror(errno));

    pid_t c1 = fork();
    if (c1 == 0)
        cocuk_bekle_term();
    /* çocuğun işleyiciyi kurmasını bekle */
    usleep(200000);
    kill(c1, SIGTERM);
    waitpid(c1, &durum, 0);
    if (WIFEXITED(durum))
        printf("çocuk1 normal çıktı, kod=%d\n", WEXITSTATUS(durum));

    pid_t c2 = fork();
    if (c2 == 0) {
        pause();
        _exit(0);
    }
    usleep(200000);
    kill(c2, SIGKILL);       /* yakalanamaz: zorla öldürülür */
    waitpid(c2, &durum, 0);
    if (WIFSIGNALED(durum))
        printf("çocuk2 sinyal ile sonlandı: %d\n", WTERMSIG(durum));
    return 0;
}
