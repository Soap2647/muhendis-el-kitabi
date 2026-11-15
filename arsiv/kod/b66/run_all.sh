#!/bin/bash
cd /c/Users/merty/AppData/Local/Temp/b66
export PYTHONIOENCODING=utf-8
run() { python -u "$1.py" > "$2" 2>&1; echo "$1 exit $?" >> run2_log.txt; }
run t00_gorsel t00_cikti.txt
run t01_konv_np t01_cikti.txt
run t02_cnn_digits t02_cikti.txt
run t03_kayma t03_cikti.txt
run kontrol_b66 kontrol_b66_cikti.txt
run t05_artirma t05_artirma_cikti.txt
run t07_bozulma t07_bozulma_cikti.txt
run t08_verim t08_verim_cikti.txt
run t09_gradcam t09_gradcam_cikti.txt
run t06_transfer t06_transfer_cikti.txt
run t04_artik t04_cikti.txt
echo ALLDONE >> run2_log.txt
