#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b15/kod
gcc -O2 -Wall -Wextra -std=c11 vezir_bit.c -o vezir_bit && ./vezir_bit > v1.txt; echo "cikis=$?" >> v1.txt
gcc -O1 -g -Wall -Wextra -std=c11 -fsanitize=address,undefined vezir_bit.c -o vezir_asan 2>&1 && ./vezir_asan > v2.txt 2>&1; echo "cikis=$?" >> v2.txt
cat v1.txt; echo ---; cat v2.txt
