gcc -O0 -Wall -Wextra -std=c11 derin.c -o derin_O0 ||| wsl: gcc -O0 -Wall -Wextra -std=c11 derin.c -o derin_O0 2>&1
./derin_O0 10000 ||| wsl: ./derin_O0 10000 2>/dev/null; echo "cikis=$?"
./derin_O0 100000 ||| wsl: ./derin_O0 100000 2>/dev/null; echo "cikis=$?"
