/* b32_c5_hatali.c: kullanici girdisi bicim dizesi olarak
 * kullaniliyor.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 b32_c5_hatali.c
 *          -o b32_c5_hatali
 */
#include <stdio.h>

int main(int argc, char **argv)
{
    if (argc != 2)
        return 2;
    printf(argv[1]);                     /* girdi = biçim dizesi */
    printf("\n");
    return 0;
}
