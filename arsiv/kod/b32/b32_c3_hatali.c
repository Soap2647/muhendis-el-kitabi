/* b32_c3_hatali.c: ayni bellegi iki kez serbest birakma
 * (double free).
 * Derleme (ASan): gcc -g -O0 -fsanitize=address -Wall -Wextra
 *                 -std=c11 b32_c3_hatali.c -o b32_c3_hatali
 */
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static void tampon_bosalt(char *p)
{
    free(p);
}

int main(void)
{
    char *p = malloc(32);
    if (p == NULL)
        return 1;
    strcpy(p, "veri");
    tampon_bosalt(p);
    tampon_bosalt(p);             /* HATA: ikinci free */
    puts("bitti");
    return 0;
}
