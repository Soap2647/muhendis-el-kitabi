/* otomatik uretildi: c_uret.py */
#include <stdint.h>

uint8_t agac_tahmin(const float x[3]) {
    if (x[0] <= 0.822449803f) {
        if (x[1] <= 60.3237228f) {
            if (x[0] <= 0.697952151f) {
                return 0;
            } else {
                return 0;
            }
        } else {
            if (x[0] <= 0.460168988f) {
                return 0;
            } else {
                return 0;
            }
        }
    } else {
        if (x[0] <= 1.21619737f) {
            if (x[1] <= 43.5918274f) {
                return 0;
            } else {
                return 1;
            }
        } else {
            return 1;
        }
    }
}
