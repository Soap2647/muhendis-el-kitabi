/* b32_c1_hatali.c: yigin tamponu tasmasi (sinirsiz kopya).
 * Derleme (ASan): gcc -g -O0 -fno-omit-frame-pointer \
 *                 -fsanitize=address -Wall -Wextra -std=c11 \
 *                 b32_c1_hatali.c -o b32_c1_hatali
 */
#include <stdio.h>
#include <string.h>

static void ad_yaz(const char *girdi)
{
    char ad[16];
    strcpy(ad, girdi);            /* sinir denetimi yok */
    printf("merhaba, %s\n", ad);
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "kullanim: %s METIN\n", argv[0]);
        return 2;
    }
    ad_yaz(argv[1]);
    return 0;
}
