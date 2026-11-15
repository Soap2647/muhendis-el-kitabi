gcc -O0 -g -fsanitize=address,undefined -std=c11 tabansiz.c -o tab_asan ||| wsl: gcc -O0 -g -fsanitize=address,undefined -std=c11 tabansiz.c -o tab_asan
./tab_asan 5 ||| wsl: bash -c './tab_asan 5' 2>&1 | grep -E "ERROR|#[0-2] " | sed -E 's/==[0-9]+==/==PID==/; s/0x[0-9a-f]+/0xADRES/g; s/ \(pc.*//; s#/mnt/[^ ]*/##' | head -4
