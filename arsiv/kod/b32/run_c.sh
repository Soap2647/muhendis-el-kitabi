#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b32
A=$(printf 'A%.0s' {1..40})
echo "== c1 ASan kisa girdi"; gcc -g -O0 -fno-omit-frame-pointer -fsanitize=address -Wall -Wextra -std=c11 b32_c1_hatali.c -o c1a && ./c1a ali; echo "exit=$?"
echo "== c1 ASan 40 karakter"; ./c1a "$A" 2>&1 | head -12; echo "exit=${PIPESTATUS[0]}"
echo "== c1 duzeltilmis 40 karakter"; gcc -O2 -Wall -Wextra -std=c11 b32_c1_duzeltilmis.c -o c1d && ./c1d "$A"; echo "exit=$?"; ./c1d ali; echo "exit=$?"
