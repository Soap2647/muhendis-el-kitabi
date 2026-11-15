#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b32
echo "== c2 UAF ASan"; gcc -g -O0 -fsanitize=address -Wall -Wextra -std=c11 b32_c2_hatali.c -o c2h && ./c2h > /tmp/o2.txt 2>&1; echo "exit=$?"; head -4 /tmp/o2.txt | cut -c1-120
echo "== c2 duz"; gcc -g -O0 -fsanitize=address -Wall -Wextra -std=c11 b32_c2_duzeltilmis.c -o c2d && ./c2d; echo "exit=$?"
echo "== c3 double free ASan"; gcc -g -O0 -fsanitize=address -Wall -Wextra -std=c11 b32_c3_hatali.c -o c3h && ./c3h > /tmp/o3.txt 2>&1; echo "exit=$?"; head -4 /tmp/o3.txt | cut -c1-120
echo "== c3 duz"; gcc -g -O0 -fsanitize=address -Wall -Wextra -std=c11 b32_c3_duzeltilmis.c -o c3d && ./c3d; echo "exit=$?"
echo "== c4 hatali UBSan+ASan"; gcc -g -O0 -fsanitize=address,undefined -Wall -Wextra -std=c11 b32_c4_hatali.c -o c4h && ./c4h 1073741825 > /tmp/o4.txt 2>&1; echo "exit=$?"; head -6 /tmp/o4.txt | cut -c1-140
echo "== c4 duz"; gcc -g -O0 -fsanitize=address,undefined -Wall -Wextra -std=c11 b32_c4_duzeltilmis.c -o c4d && ./c4d 1073741825; echo "exit=$?"; ./c4d 10; echo "exit=$?"
echo "== c5 uyari"; gcc -O2 -Wall -Wextra -std=c11 b32_c5_hatali.c -o c5h 2>&1 | head -5; ./c5h "yuzde %% isareti"; ./c5duz 2>/dev/null; gcc -O2 -Wall -Wextra -std=c11 b32_c5_duzeltilmis.c -o c5d && ./c5d "yuzde %% isareti"
echo "== c6 fortify"; gcc -O2 -D_FORTIFY_SOURCE=2 -Wall -Wextra -std=c11 b32_c6_fortify.c -o c6 && ./c6 kisa; echo "exit=$?"; ./c6 "bu metin sekiz bayttan uzun" > /tmp/o6.txt 2>&1; echo "exit=$?"; cat /tmp/o6.txt | head -3
echo "== c7 aslr"; gcc -O0 -Wall -Wextra -std=c11 b32_c7_aslr.c -o c7 && for i in 1 2 3; do ./c7; done; echo "-- setarch -R:"; for i in 1 2; do setarch x86_64 -R ./c7; done; cat /proc/sys/kernel/randomize_va_space
