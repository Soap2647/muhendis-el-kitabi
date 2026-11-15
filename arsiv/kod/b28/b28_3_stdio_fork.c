/* b28_3_stdio_fork.c: stdio tamponu ve fork: çift çıktı */
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>

int main(int argc, char **argv)
{
    const char *kip = argc > 1 ? argv[1] : "varsayilan";

    if (strcmp(kip, "satir") == 0)
        setvbuf(stdout, NULL, _IOLBF, 0);   /* satır tamponu */

    printf("merhaba\n");
    if (strcmp(kip, "flush") == 0)
        fflush(stdout);                     /* fork'tan önce boşalt */

    /* tampon iki sürece kopyalanır */
    pid_t pid = fork();
    if (pid < 0)
        return 1;
    if (pid == 0)
        return 0;                  /* çocuk: çıkışta boşaltır */

    wait(NULL);
    return 0;                       /* ana: çıkışta boşaltır */
}
