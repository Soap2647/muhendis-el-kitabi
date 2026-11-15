/* b32_c2_hatali.c: serbest birakilmis bellegi kullanma
 * (use-after-free).
 * Derleme (ASan): gcc -g -O0 -fsanitize=address -Wall -Wextra
 *                 -std=c11 b32_c2_hatali.c -o b32_c2_hatali
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
    free(s);
    printf("id=%d\n", s->id);     /* HATA: bellek artik serbest */
    return 0;
}
