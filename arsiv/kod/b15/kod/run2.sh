#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b15/kod
gcc -O0 -Wall -Wextra -std=c11 tabansiz.c -o tab_O0
gcc -O2 -Wall -Wextra -std=c11 tabansiz.c -o tab_O2 2>&1
gcc -O0 -g -fsanitize=address,undefined -std=c11 tabansiz.c -o tab_asan
./tab_O0 5 > t1.txt 2>&1; echo "cikis=$?" >> t1.txt
./tab_O2 5 > t2.txt 2>&1; echo "cikis=$?" >> t2.txt
./tab_asan 5 > t3.txt 2>&1; echo "cikis=$?" >> t3.txt
ASAN_OPTIONS=detect_leaks=0 ./tab_asan 5 2>&1 | sed -E 's/0x[0-9a-f]+/0xADRES/g' | head -8 > t4.txt
for f in t1 t2 t3 t4; do echo "== $f"; head -c 600 $f.txt; echo; done
