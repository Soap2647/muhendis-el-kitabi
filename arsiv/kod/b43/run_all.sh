#!/usr/bin/env bash
# run_all.sh - kitaptaki tum ciktilari bu betikle uretir.
set -e
B=/c/Users/merty/AppData/Local/Temp/b43
export PATH="/c/ST/STM32CubeIDE_1.19.0/STM32CubeIDE/plugins/com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.13.3.rel1.win32_1.0.0.202411081344/tools/bin:$PATH"
CF="-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -ffreestanding -fno-tree-loop-distribute-patterns -Wall -Wextra -std=c11"
mkdir -p $B/cikti
cd $B/ornek
arm-none-eabi-gcc $CF -O2 -fstack-usage -c startup.c -o startup.o
arm-none-eabi-gcc $CF -O2 -fstack-usage -c blink.c -o blink.o
arm-none-eabi-gcc $CF -O2 -nostdlib -nostartfiles -T link.ld \
  -Wl,-Map=blink.map startup.o blink.o -o blink.elf
arm-none-eabi-objcopy -O binary blink.elf blink.bin
arm-none-eabi-size blink.elf > $B/cikti/size_blink.txt
arm-none-eabi-objdump -h blink.elf > $B/cikti/objdump_h.txt
arm-none-eabi-nm -n blink.elf > $B/cikti/nm_blink.txt
arm-none-eabi-objdump -s -j .isr_vector blink.elf > $B/cikti/vec.txt
arm-none-eabi-objdump -d blink.elf > $B/cikti/disasm_blink.txt
cat blink.su > $B/cikti/su_blink.txt
cd $B/emu
python -I harness.py ../ornek/blink.elf ../ornek/blink.bin \
  $B/cikti > $B/cikti/emu_cikti.txt
cd $B/host
arm-none-eabi-gcc $CF -O2 -c volatile_deney.c -o volatile_deney.o
arm-none-eabi-objdump -d volatile_deney.o > $B/cikti/disasm_volatile.txt
arm-none-eabi-gcc $CF -O2 -c bitfield.c -o bitfield.o
arm-none-eabi-objdump -d bitfield.o > $B/cikti/disasm_bitfield.txt
cd $B/cmsis
arm-none-eabi-gcc $CF -std=c11 -Wall -I. -c ofs_testi.c -o ofs_testi.o
echo "ofs_testi derlendi, rc=$?" > $B/cikti/ofs.txt
arm-none-eabi-size ofs_testi.o >> $B/cikti/ofs.txt
cd $B/boyut
cp $B/ornek/startup.c .
arm-none-eabi-gcc $CF -O2 -c startup.c -o startup.o
RS="-nostdlib -nostartfiles -T $B/ornek/link.ld"
: > $B/cikti/boyut.txt
for opt in O0 O2 Os; do
  arm-none-eabi-gcc $CF -$opt $RS startup.o app.c -o app_$opt.elf
  echo "app -$opt $(arm-none-eabi-size app_$opt.elf | tail -1)" >> $B/cikti/boyut.txt
done
arm-none-eabi-gcc $CF -Os -ffunction-sections -fdata-sections $RS \
  -Wl,--gc-sections startup.o app.c -o app_gc.elf
echo "app -Os gc $(arm-none-eabi-size app_gc.elf | tail -1)" >> $B/cikti/boyut.txt
NANO="--specs=nano.specs --specs=nosys.specs"
arm-none-eabi-gcc $CF -Os $NANO -nostartfiles -T $B/ornek/link.ld \
  startup.o printf_yok.c -o pyok.elf 2>/dev/null
echo "printf_yok nano -Os $(arm-none-eabi-size pyok.elf | tail -1)" >> $B/cikti/boyut.txt
arm-none-eabi-gcc $CF -Os $NANO -nostartfiles -T $B/ornek/link.ld \
  startup.o printf_deney.c -o pnano.elf 2>/dev/null
echo "printf nano -Os $(arm-none-eabi-size pnano.elf | tail -1)" >> $B/cikti/boyut.txt
arm-none-eabi-gcc $CF -Os -ffunction-sections -fdata-sections $NANO \
  -Wl,--gc-sections -nostartfiles -T $B/ornek/link.ld \
  startup.o printf_deney.c -o pnano_gc.elf 2>/dev/null
echo "printf nano -Os gc $(arm-none-eabi-size pnano_gc.elf | tail -1)" >> $B/cikti/boyut.txt
arm-none-eabi-gcc $CF -O1 -fstack-usage -c yigin.c -o yigin.o
cp yigin.su $B/cikti/yigin_su.txt
cat $B/cikti/boyut.txt
arm-none-eabi-gcc $CF -Os -ffunction-sections -fdata-sections -c app.c -o app.o
arm-none-eabi-gcc $CF -Os -nostdlib -nostartfiles -T $B/ornek/link.ld   -Wl,--gc-sections -Wl,--print-gc-sections startup.o app.o -o app_gc2.elf   > $B/cikti/gc_ham.txt 2>&1
grep -o "removing unused section.*" $B/cikti/gc_ham.txt > $B/cikti/gc_print.txt
arm-none-eabi-size app_gc2.elf | tail -1 >> $B/cikti/gc_print.txt
cd $B/host
arm-none-eabi-objdump -d volatile_deney.o | awk '/^[0-9a-f]+ <(gecikme_normal|bekle_normal|sonsuz_normal|bekle_satir)>:/{p=1} /^$/{p=0} p' > $B/cikti/volatile_secim.txt
cd $B/ornek
arm-none-eabi-objdump -d blink.elf | awk '/^[0-9a-f]+ <(Reset_Handler|menzil_hesapla)>:/{p=1} /^$/{p=0} p' > $B/cikti/disasm_secim.txt
MSYS_NO_PATHCONV=1 wsl bash -c "cd /mnt/c/Users/merty/AppData/Local/Temp/b43/host && gcc -O2 -Wall -Wextra -std=c11 -fsanitize=address,undefined bit_testleri.c -o bit_testleri && ./bit_testleri; echo EXIT=\$?" | tr -d '\r' > $B/cikti/host_bit.txt
cat $B/cikti/host_bit.txt
echo ALL_DONE
