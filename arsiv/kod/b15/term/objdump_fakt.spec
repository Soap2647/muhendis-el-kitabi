objdump -d cerceve ||| wsl: objdump -d --no-show-raw-insn cerceve | awk '/<faktoriyel>:/,/^$/' | expand
