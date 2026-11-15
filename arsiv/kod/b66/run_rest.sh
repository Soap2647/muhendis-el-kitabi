#!/bin/bash
cd /c/Users/merty/AppData/Local/Temp/b66
until [ -f "/d/Mevcut Projeler/Kitap/engine/veri/b66_artik_son.csv" ]; do sleep 5; done
for t in t05_artirma t06_transfer t07_bozulma t08_verim t09_gradcam; do
  PYTHONIOENCODING=utf-8 python -u $t.py > ${t}_cikti.txt 2>&1
  echo "$t exit $?" >> run_log.txt
done
echo ALLDONE >> run_log.txt
