#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b15/kod
gcc -O0 -Wall -Wextra -std=c11 sel.c -o sel_O0 && gcc -O2 -Wall -Wextra -std=c11 sel.c -o sel_O2 && gcc -O1 -g -Wall -Wextra -std=c11 -fsanitize=address,undefined sel.c -o sel_asan
for n in 1 2 100 500; do ./sel_O2 y $n; ./sel_O0 y $n; done
for n in 600 700 800 900; do ./sel_O0 r $n > /dev/null 2>&1; echo "O0 rec n=$n cikis=$?"; done
./sel_asan y 300; echo "asan cikis=$?"
ASAN_OPTIONS=detect_leaks=1 ./sel_asan r 50; echo "asan rec cikis=$?"
