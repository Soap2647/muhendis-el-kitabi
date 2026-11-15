/* noprintf.c - ayni program, printf yok (karsilastirma) */
#include <stdint.h>
volatile uint32_t sonuc;
int main(void)
{
    sonuc = sonuc + 1u;
    return 0;
}
