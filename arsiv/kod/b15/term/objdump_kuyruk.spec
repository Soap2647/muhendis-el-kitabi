objdump -d kuyruk_O2 ||| wsl: objdump -d --no-show-raw-insn kuyruk_O2 | awk '/<topla_kuyruk>:/,/^$/' | expand
