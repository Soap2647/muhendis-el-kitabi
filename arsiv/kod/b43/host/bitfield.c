/* bitfield.c - bit alani ile maske yazmanin makine kodu */
#include <stdint.h>

typedef struct {
    uint32_t dusuk  : 4;   /* bit 0-3 */
    uint32_t orta   : 8;   /* bit 4-11 */
    uint32_t yuksek : 20;  /* bit 12-31 */
} alan_t;

void alan_yaz(volatile alan_t *r)
{
    r->orta = 0x5Au;
}

void maske_yaz(volatile uint32_t *r)
{
    *r = (*r & ~(0xFFu << 4)) | (0x5Au << 4);
}
