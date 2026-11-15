#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b15/kod
timeout 3 ./tab_O2 5 > t5.txt 2>&1; echo "cikis=$?" >> t5.txt
cat t5.txt
