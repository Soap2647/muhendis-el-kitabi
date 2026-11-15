/* b32_c2_duzeltilmis.c: deger serbest birakmadan once okunur;
 * isaretci serbest birakildiktan sonra NULL yapilir.
 * Derleme: gcc -g -O0 -fsanitize=address -Wall -Wextra -std=c11 \
 *          b32_c2_duzeltilmis.c -o b32_c2_duzeltilmis
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct sensor {
    int id;
    char etiket[16];
};

int main(void)
{
    struct sensor *s = malloc(sizeof *s);
    if (s == NULL)
        return 1;
    s->id = 7;
    strcpy(s->etiket, "GPS");
    int id = s->id;               /* serbest birakmadan once oku */
    free(s);
    s = NULL;                     /* artik kullanilmayacak */
    printf("id=%d\n", id);
    return 0;
}
