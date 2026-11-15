#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/claude/D--Mevcut-Projeler-Kitap/cb731bd7-a681-4dce-86ad-586fb39601bd/scratchpad/b22 || exit 1
for f in factory ayar tekil adaptor sarici fasad strateji gozlemci komut durum; do
  echo "=== $f.cpp"
  g++ -std=c++17 -O2 -Wall -Wextra -pthread -fsanitize=address,undefined -o "bin_$f" "$f.cpp" 2>&1
  if [ -x "bin_$f" ]; then
    ./"bin_$f" 2>&1
    echo "[exit $?]"
  fi
done
