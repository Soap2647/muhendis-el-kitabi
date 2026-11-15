#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b32
gcc -O2 -Wall -Wextra -std=c11 b32_c1_hatali.c -o k_varsayilan 2>/dev/null
gcc -O2 -fno-stack-protector -U_FORTIFY_SOURCE -no-pie -z execstack -Wl,-z,norelro -std=c11 b32_c1_hatali.c -o k_zayif 2>/dev/null
gcc -O2 -fstack-protector-strong -U_FORTIFY_SOURCE -std=c11 b32_c1_hatali.c -o k_kanarili 2>/dev/null
python3 b32_korumalar.py ./k_varsayilan ./k_zayif
echo "== kanarili (FORTIFY kapali), 40 karakter"
./k_kanarili $(printf 'A%.0s' {1..40}) > k_out.txt 2>&1; echo "exit=$?"; cat k_out.txt | cut -c1-80
echo "== varsayilan, 40 karakter"
./k_varsayilan $(printf 'A%.0s' {1..40}) > k_out2.txt 2>&1; echo "exit=$?"; cat k_out2.txt | cut -c1-80
echo "== zayif, 40 karakter (bilincli zafiyetli ikili)"
./k_zayif $(printf 'A%.0s' {1..40}) > k_out3.txt 2>&1; echo "exit=$?"; head -c 300 k_out3.txt | cut -c1-80
echo "== static analyzer c2"; gcc -fanalyzer -Wall -Wextra -std=c11 -c b32_c2_hatali.c -o /dev/null 2>&1 | head -30
echo "== fanalyzer c3"; gcc -fanalyzer -Wall -Wextra -std=c11 -c b32_c3_hatali.c -o /dev/null 2>&1 | head -20
echo "== fanalyzer c1"; gcc -fanalyzer -Wall -Wextra -std=c11 -c b32_c1_hatali.c -o /dev/null 2>&1 | head -30
