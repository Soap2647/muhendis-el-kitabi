/* b32_c6_fortify.c: hedef boyutu derleme zamaninda bilinen tampona
 * kopya. _FORTIFY_SOURCE=2 ile -O2 altinda memcpy, __memcpy_chk'a
 * donusur; tasma tespit edilince program durdurulur.
 * Derleme: gcc -O2 -D_FORTIFY_SOURCE=2 -Wall -Wextra -std=c11 \
 *          b32_c6_fortify.c -o b32_c6_fortify
 */
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
    char hedef[8];
    if (argc != 2)
        return 2;
    size_t n = strlen(argv[1]) + 1;
    memcpy(hedef, argv[1], n);           /* n > 8 ise tasma */
    printf("kopyalandi: %s\n", hedef);
    return 0;
}
