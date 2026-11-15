/* b32_c7_aslr.c: adres uzayi yerlesiminin calistirmalar arasindaki
 * degisimini gosterir. Yalnizca kendi adreslerimizi yazdiriyoruz.
 * Derleme: gcc -O0 -Wall -Wextra -std=c11 b32_c7_aslr.c
 *          -o b32_c7_aslr
 */
#include <stdio.h>
#include <stdlib.h>

static void islev(void) { }

int main(void)
{
    int yerel = 0;
    int *yigin = &yerel;
    int *yigin_tam = malloc(sizeof *yigin_tam);
    printf("yigin=%p yigin-kod=%p heap=%p\n",
           (void *)yigin, (void *)islev, (void *)yigin_tam);
    free(yigin_tam);
    return 0;
}
