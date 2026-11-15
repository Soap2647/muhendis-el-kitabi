#!/bin/bash
for i in 0 1 2 3; do
  d=/sys/devices/system/cpu/cpu0/cache/index$i
  echo "L$(cat $d/level) $(cat $d/type)" \
       "size=$(cat $d/size)" \
       "ways=$(cat $d/ways_of_associativity)" \
       "sets=$(cat $d/number_of_sets)" \
       "line=$(cat $d/coherency_line_size)" \
       "shared=$(cat $d/shared_cpu_list)"
done
getconf -a | grep -iE "DCACHE|L2_CACHE|L3_CACHE|PAGESIZE"
