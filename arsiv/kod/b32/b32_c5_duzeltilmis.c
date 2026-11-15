/* b32_c5_duzeltilmis.c: girdi her zaman bir argumana verilir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 b32_c5_duzeltilmis.c \
 *          -o b32_c5_duzeltilmis
 */
#include <stdio.h>

int main(int argc, char **argv)
{
    if (argc != 2)
        return 2;
    printf("%s\n", argv[1]);           /* girdi veri olarak */
    return 0;
}
