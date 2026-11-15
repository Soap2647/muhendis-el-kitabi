#!/bin/bash
cd /mnt/c/Users/merty/AppData/Local/Temp/b15/kod
objdump -d --no-show-raw-insn derin_O0 | awk '/<derin>:/,/^$/' | grep -E "sub .*rsp|call" > r30.txt
objdump -d --no-show-raw-insn derin | grep -c "call.*<derin>" > r31.txt
objdump -d --no-show-raw-insn kuyruk_O2 | grep -c "call.*<topla_" > r32.txt
