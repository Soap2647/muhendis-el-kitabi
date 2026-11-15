gcc -O0 -Wall -Wextra -std=c11 kuyruk.c -o kuyruk_O0 ||| wsl: gcc -O0 -Wall -Wextra -std=c11 kuyruk.c -o kuyruk_O0 2>&1
./kuyruk_O0 k 100000 ||| wsl: ./kuyruk_O0 k 100000 2>/dev/null; echo "cikis=$?"
./kuyruk_O0 k 10000000 ||| wsl: ./kuyruk_O0 k 10000000 2>/dev/null; echo "cikis=$?"
gcc -O2 -Wall -Wextra -std=c11 kuyruk.c -o kuyruk_O2 ||| wsl: gcc -O2 -Wall -Wextra -std=c11 kuyruk.c -o kuyruk_O2 2>&1
./kuyruk_O2 k 10000000 ||| wsl: ./kuyruk_O2 k 10000000 2>/dev/null; echo "cikis=$?"
./kuyruk_O2 d 10000000 ||| wsl: ./kuyruk_O2 d 10000000 2>/dev/null; echo "cikis=$?"
