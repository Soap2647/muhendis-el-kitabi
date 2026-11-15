gcc -O1 -g -fsanitize=address,undefined -std=c11 sel.c -o sel_asan ||| wsl: gcc -O1 -g -fsanitize=address,undefined -std=c11 sel.c -o sel_asan 2>&1
./sel_asan y 0 ||| wsl: ./sel_asan y 0 2>/dev/null; echo "cikis=$?"
./sel_asan r 1 ||| wsl: ./sel_asan r 1 2>/dev/null; echo "cikis=$?"
