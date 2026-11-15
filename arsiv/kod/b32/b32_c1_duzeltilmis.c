/* b32_c1_duzeltilmis.c: tampon tasmasinin sinirli kopya ile
 * onlenmesi.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 b32_c1_duzeltilmis.c \
 *          -o b32_c1_duzeltilmis
 */
#include <stdio.h>

static int ad_yaz(const char *girdi)
{
    char ad[16];
    /* snprintf en fazla sizeof(ad)-1 karakter yazar ve sonunu NUL ile
     * kapatir. Donus degeri, kesilmis olsaydi yazilacak uzunluk. */
    int n = snprintf(ad, sizeof ad, "%s", girdi);
    if (n < 0 || (size_t)n >= sizeof ad) {
        fprintf(stderr, "ad cok uzun (en fazla %zu karakter)\n",
                sizeof ad - 1);
        return -1;                /* kesmek yerine reddet */
    }
    printf("merhaba, %s\n", ad);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "kullanim: %s METIN\n", argv[0]);
        return 2;
    }
    return ad_yaz(argv[1]) == 0 ? 0 : 1;
}
