#!/bin/bash
# Bolum 29 birlestirici: parts/p1..p5.md -> bolumler/bolum_29.md
# @@KOD dosya bas son dil@@        -> kaynak dosyadan kod blogu ($ = son satir)
# @@CIKTI dosya [bas son]@@        -> out/ altindaki gercek cikti (term blogu)
# @@KERNEL dosya bas son dil@@     -> kernel basligi (sekmeler 4 bosluk)
B=/c/Users/merty/AppData/Local/Temp/b29
OUT=$B/out
MD="/d/Mevcut Projeler/Kitap/bolumler/bolum_29.md"
: > "$MD"

kirp() { sed -e :a -e '/^[[:space:]]*$/{$d;N;ba' -e '}'; }

for p in p1 p2 p3 p4 p5; do
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      @@KOD\ *|@@KERNEL\ *|@@CIKTI\ *)
        set -- $(printf '%s' "$line" | sed 's/^@@//; s/@@$//')
        kind=$1; shift
        printf '\n' >> "$MD"
        if [ "$kind" = CIKTI ]; then
          f=$OUT/$1
          if [ -n "$2" ]; then
            e=$3; [ "$e" = '$' ] && e=$(wc -l < "$f")
            printf '```term\n' >> "$MD"
            sed -n "$2,${e}p" "$f" | sed 's/[[:space:]]*$//' | kirp >> "$MD"
          else
            printf '```term\n' >> "$MD"
            sed 's/[[:space:]]*$//' "$f" | kirp >> "$MD"
          fi
          printf '```\n' >> "$MD"
        else
          if [ "$kind" = KOD ]; then f=$B/$1; else f=$B/$1; fi
          s=$2; e=$3; lang=$4
          [ "$e" = '$' ] && e=$(wc -l < "$f")
          printf '```%s\n' "$lang" >> "$MD"
          if [ "$kind" = KERNEL ]; then
            expand -t4 "$f" | sed -n "$s,${e}p" | kirp >> "$MD"
          else
            sed -n "$s,${e}p" "$f" | kirp >> "$MD"
          fi
          printf '```\n' >> "$MD"
        fi
        printf '\n' >> "$MD"
        ;;
      *)
        printf '%s\n' "$line" >> "$MD"
        ;;
    esac
  done < "$B/parts/$p.md"
  printf '\n' >> "$MD"
done
echo "yazildi: $(wc -l < "$MD") satir"
