#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b32
gcc -g -O0 -fsanitize=address -Wall -Wextra -std=c11 b32_c2_hatali.c -o c2h
./c2h > o2.txt 2>&1; echo "c2h exit=$?"; head -3 o2.txt | cut -c1-110
gcc -g -O0 -fsanitize=address -Wall -Wextra -std=c11 b32_c2_duzeltilmis.c -o c2d
./c2d; echo "c2d exit=$?"
gcc -g -O0 -fsanitize=address,undefined -Wall -Wextra -std=c11 b32_c4_duzeltilmis.c -o c4d
./c4d 4611686018427387904; echo "c4d exit=$?"
./c4d 16; echo "c4d exit=$?"
