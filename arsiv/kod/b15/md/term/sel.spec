gcc -O0 -Wall -Wextra -std=c11 sel.c -o sel_O0 ||| wsl: gcc -O0 -Wall -Wextra -std=c11 sel.c -o sel_O0 2>&1
gcc -O2 -Wall -Wextra -std=c11 sel.c -o sel_O2 ||| wsl: gcc -O2 -Wall -Wextra -std=c11 sel.c -o sel_O2 2>&1
./sel_O0 r 500 ||| wsl: ./sel_O0 r 500 2>/dev/null; echo "cikis=$?"
./sel_O0 r 600 ||| wsl: ./sel_O0 r 600 2>/dev/null; echo "cikis=$?"
./sel_O2 r 1000 ||| wsl: ./sel_O2 r 1000 2>/dev/null; echo "cikis=$?"
./sel_O2 y 1000 ||| wsl: ./sel_O2 y 1000 2>/dev/null; echo "cikis=$?"
