#!/bin/bash
# Bolum 29 icin gercek ciktilari toplar. Calistirma: wsl bash collect.sh
D=/mnt/c/Users/merty/AppData/Local/Temp/b29
O=$D/out
VERI="/mnt/d/Mevcut Projeler/Kitap/engine/veri"
mkdir -p "$O"
cd "$D" || exit 1

{ echo '$ ip -4 -br addr'; ip -4 -br addr;
  echo '$ ip route';       ip route;
  echo '$ ip neigh';       ip neigh; } > "$O/ag_komut.txt"

{ echo '$ ip link show eth0';
  ip link show eth0 | sed -E 's/ qdisc .*//' | \
    sed -E 's/(link\/ether [0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}):[0-9a-f:]+/\1:xx:xx:xx/'; } > "$O/mtu.txt"

{ echo '$ ping -c 1 -t 1 -W 2 8.8.8.8';
  ping -c 1 -t 1 -W 2 8.8.8.8 | sed -n 2p;
  echo '$ ping -c 1 -t 2 -W 2 8.8.8.8';
  ping -c 1 -t 2 -W 2 8.8.8.8 | sed -n 2p; } > "$O/ttl.txt"

{ echo '$ sysctl net.ipv4.tcp_congestion_control';
  sysctl net.ipv4.tcp_congestion_control;
  echo '$ sysctl net.ipv4.tcp_available_congestion_control';
  sysctl net.ipv4.tcp_available_congestion_control; } > "$O/cc.txt"

{ echo '$ python3 tcp_durum.py';
  timeout 30 python3 tcp_durum.py; } > "$O/tcp_durum.txt" 2>&1

{ echo '$ python3 nagle_olcum.py'; timeout 90 python3 nagle_olcum.py "$D/nagle_son.csv"; } > "$O/nagle.txt" 2>&1
cp "$D/nagle_son.csv" "$VERI/b29_nagle.csv"

{ echo '$ python3 ag_hesap.py'; timeout 60 python3 ag_hesap.py; } > "$O/ag_hesap.txt" 2>&1
{ echo '$ python3 paket_coz.py'; timeout 60 python3 paket_coz.py; } > "$O/paket_coz.txt" 2>&1
{ echo '$ python3 aimd_sim.py b29_aimd.csv'; timeout 60 python3 aimd_sim.py "$VERI/b29_aimd.csv"; } > "$O/aimd.txt" 2>&1
echo DONE
