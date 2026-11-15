#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b15/kod
timeout 2 ./tab_O2 5; echo "cikis=$?"
timeout 2 ./tab_O0 5 2>/dev/null; echo "O0 cikis=$?"
bash -c './tab_O0 5' 2>/dev/null; echo "O0b cikis=$?"
