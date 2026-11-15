/* b32_c3_duzeltilmis.c: sahiplik tek noktada; serbest birakan kod
 * isaretciyi NULL yapar. free(NULL) tanimlidir ve hicbir sey yapmaz.
 * Derleme: gcc -g -O0 -fsanitize=address -Wall -Wextra -std=c11 \
 *          b32_c3_duzeltilmis.c -o b32_c3_duzeltilmis
 */
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static void tampon_bosalt(char **p)
{
    free(*p);
    *p = NULL;
}

int main(void)
{
    char *p = malloc(32);
    if (p == NULL)
        return 1;
    strcpy(p, "veri");
    tampon_bosalt(&p);
    tampon_bosalt(&p);            /* ikinci cagri zararsiz */
    puts("bitti");
    return 0;
}
