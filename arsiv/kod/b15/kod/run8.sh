#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b15/kod
gcc -O2 -Wall -Wextra -std=c11 sel.c -o sel_O2 && gcc -O1 -g -Wall -Wextra -std=c11 -fsanitize=address,undefined sel.c -o sel_asan && echo BUILD_OK
./sel_asan y 0; echo "a cikis=$?"; ./sel_asan r 0; echo "b cikis=$?"; ./sel_asan y 1; ./sel_asan r 1; ./sel_asan y 300; echo "c cikis=$?"; ./sel_O2 r 500; ./sel_O2 y 500
