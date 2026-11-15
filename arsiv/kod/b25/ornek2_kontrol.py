# Sanal adresi 4 seviyeli sayfa tablosu indekslerine boler,
# sonra geri birlestirip ozgun adresle karsilastirir.
adres = 0x7F3A12C4B5E8
pml4 = (adres >> 39) & 0x1FF
pdpt = (adres >> 30) & 0x1FF
pd = (adres >> 21) & 0x1FF
pt = (adres >> 12) & 0x1FF
ofset = adres & 0xFFF
print("PML4=%d PDPT=%d PD=%d PT=%d ofset=%d"
      % (pml4, pdpt, pd, pt, ofset))
geri = (pml4 << 39) | (pdpt << 30) | (pd << 21) | (pt << 12) | ofset
print("geri birlestirme dogru:", geri == adres)
girdi = 1 << 9
print("tablo girdisi:", girdi, "girdi boyutu: 8 bayt")
print("tablo boyutu:", girdi * 8, "bayt")
