#include <stdio.h>
enum durum { TAMAM, UYARI, KRITIK };
static int yardimci(void) { return 1; }
int kodu(enum durum d)
{
    switch (d) {
    case TAMAM: return 0;
    case UYARI: return 1;
    }
    return -1;
}
int main(void) { printf("%d\n", kodu(KRITIK)); return 0; }
