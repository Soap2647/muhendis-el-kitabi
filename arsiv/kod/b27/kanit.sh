#!/bin/bash
# Bolum 27 tum deneylerini derler, calistirir ve out/ altina kaydeder.
T=/mnt/c/Users/merty/AppData/Local/Temp/b27
C=$T/code; B=$T/bin; O=$T/out
cd $B
set -u
# 1) sayac++ yarisi
gcc -O0 -Wall -Wextra -std=c11 -pthread $C/b27_rmw.c -o rmw || exit 1
{ for m in plain volatile atomic mutex; do echo "\$ ./rmw $m 2"; ./rmw $m 2; echo; done
  echo "\$ ./rmw plain 1"; ./rmw plain 1; } > $O/rmw.txt
gcc -O0 -std=c11 -S -o - $C/b27_rmw.c | awk '/^art_plain:/{p=1} p{print} /ret/{if(p){exit}}' | grep -v cfi > $O/asm_plain.txt
# 2) bellek
bash $T/bellek_calistir.sh > $O/bellek.txt 2>&1
# 3) kilit ve sahte paylasim
bash $T/kilit_calistir.sh > /dev/null 2>&1
bash $T/fs_calistir.sh > /dev/null 2>&1
# 4) yigin
gcc -O2 -Wall -Wextra -std=c11 -pthread $C/b27_yigin.c -o yigin || exit 1
{ echo "\$ ./yigin aba"; ./yigin aba; echo; 
  for k in 1 2; do echo "\$ ./yigin naive 4 300000 0"; ./yigin naive 4 300000 0; echo; done
  for k in 1 2 3; do echo "\$ ./yigin naive 4 100000 1"; ./yigin naive 4 100000 1; echo; done
  for k in 1 2 3; do echo "\$ ./yigin tagged 4 100000 1"; ./yigin tagged 4 100000 1; echo; done
} > $O/yigin.txt
# 5) tampon
gcc -O2 -Wall -Wextra -std=c11 -pthread $C/b27_tampon.c -o tampon || exit 1
gcc -O2 -Wall -Wextra -std=c11 -pthread -DIF_HATASI $C/b27_tampon.c -o tampon_if || exit 1
{ echo "\$ ./tampon kv 3 3 200000"; ./tampon kv 3 3 200000; echo
  echo "\$ ./tampon sem 3 3 200000"; ./tampon sem 3 3 200000; echo
  echo "\$ ./tampon sahte"; ./tampon sahte; echo
  echo "\$ ./tampon_if sahte"; ./tampon_if sahte; } > $O/tampon.txt
# 6) kilitlenme
gcc -O2 -Wall -Wextra -std=c11 -pthread $C/b27_kilitlenme.c -o kilitlenme || exit 1
{ for m in banka-bozuk banka-sirali filozof-bozuk filozof-sirali filozof-trylock; do
    echo "\$ ./kilitlenme $m"; ./kilitlenme $m; echo "cikis kodu: $?"; echo; done
} > $O/kilitlenme.txt
# sirali filozof: zaman asimi sayimi (30 tekrar)
c=0; for k in $(seq 30); do timeout 20 ./kilitlenme filozof-sirali > /dev/null || c=$((c+1)); done
echo "filozof-sirali 30 tekrar, hatali cikis: $c" > $O/filozof_tekrar.txt
# 7) oncelik ve GIL: Python adimlari Windows Python ile ayrica calisir
# 8) TSan
gcc -O1 -g -Wall -Wextra -std=c11 -pthread -fsanitize=thread $C/b27_rmw.c -o rmw_tsan
gcc -O1 -g -Wall -Wextra -std=c11 -pthread -fsanitize=thread $C/b27_tampon.c -o tampon_tsan
gcc -O1 -g -Wall -Wextra -std=c11 -pthread -fsanitize=thread $C/b27_yigin.c -o yigin_tsan
cd $B
{ echo "\$ ./rmw_tsan plain 2"; setarch x86_64 -R ./rmw_tsan plain 2 2>&1 | head -12; echo
  echo "\$ ./rmw_tsan mutex 2"; setarch x86_64 -R ./rmw_tsan mutex 2 2>&1 | tail -5; echo
  echo "\$ ./tampon_tsan kv 3 3 20000"; setarch x86_64 -R ./tampon_tsan kv 3 3 20000 2>&1 | tail -1; echo
  echo "\$ ./yigin_tsan naive 4 20000 1"; setarch x86_64 -R ./yigin_tsan naive 4 20000 1 2>&1 | tail -2; echo
  echo "uyari sayisi (naive ABA): $(setarch x86_64 -R ./yigin_tsan naive 4 20000 1 2>&1 | grep -c 'WARNING: ThreadSanitizer')"
} > $O/tsan.txt
# 9) kontrol
gcc -O2 -Wall -std=c11 -pthread $C/b27_oncelik_kontrol.c -o oncelik_kontrol && ./oncelik_kontrol > $O/kontrol.txt
echo KANIT_BITTI
