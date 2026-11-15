/* zombi_yetim.c:
 *   ./zombi_yetim zombi -> çocuk çıkar, ebeveyn 20 sn
 *                          wait çağırmadan uyur (zombi oluşur)
 *   ./zombi_yetim yetim -> ebeveyn önce çıkar, çocuk yetim
 *                          kalır ve yeni ebeveyne devredilir */
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc < 2) {
        fprintf(stderr, "kullanım: %s zombi|yetim\n", argv[0]);
        return 1;
    }

    pid_t pid = fork();
    if (pid == 0) {
        if (strcmp(argv[1], "zombi") == 0) {
            printf("çocuk %d: çıkıyorum\n", (int)getpid());
            /* ebeveyn wait etmezse zombi olur */
            return 0;
        }
        /* yetim senaryosu: ebeveyn çıkana kadar bekle */
        sleep(3);
        printf("yetim %d: yeni ebeveyn ppid=%d\n",
               (int)getpid(), (int)getppid());
        sleep(10);
        return 0;
    }

    if (strcmp(argv[1], "zombi") == 0) {
        printf("ebeveyn %d: çocuk=%d, 20 sn uyuyorum (wait yok)\n",
               (int)getpid(), (int)pid);
        sleep(20);                    /* bu sürede ps ile bak */
        waitpid(pid, NULL, 0);        /* sonunda topla */
    } else {
        printf("ebeveyn %d: çıkıyorum, çocuk=%d yetim kalacak\n",
               (int)getpid(), (int)pid);
    }
    return 0;
}
