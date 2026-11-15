gcc -O0 -Wall -Wextra -std=c11 tabansiz.c -o tab_O0 ||| wsl: gcc -O0 -Wall -Wextra -std=c11 tabansiz.c -o tab_O0 2>&1 | grep -m1 warning | sed "s/ \[-W.*//"
./tab_O0 5 ||| wsl: ./tab_O0 5 2>/dev/null; echo "cikis=$?"
gcc -O2 -Wall -Wextra -std=c11 tabansiz.c -o tab_O2 ||| wsl: gcc -O2 -Wall -Wextra -std=c11 tabansiz.c -o tab_O2 2>/dev/null
timeout 3 ./tab_O2 5 ||| wsl: timeout 3 ./tab_O2 5 2>/dev/null; echo "cikis=$?"
objdump -d tab_O2 ||| wsl: objdump -d --no-show-raw-insn tab_O2 | awk '/<faktoriyel>:/,/^$/' | expand
