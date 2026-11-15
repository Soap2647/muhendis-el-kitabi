#!/bin/bash
export PYTHONIOENCODING=utf-8
cd "C:/Users/merty/AppData/Local/Temp/b72"
for s in b72_01_kl_yeniden b72_02_ae_pca b72_03_derin_ae_anomali b72_04_kodek b72_05_vae b72_06_gan_2d b72_07_dcgan_digits b72_08_diff_2d b72_09_cfg_2d b72_10_ddpm_digits b72_11_aileler b72_12_veri_artirma; do
  python -u $s.py > out/$s.txt 2>&1
  echo "$s exit=$?"
done
echo ALLDONE
