# graphlib_demo.py - Python'un topolojik siralayicisi ve dongu hatasi.
import graphlib

# Anahtar: dugum, deger: onun on kosullari (once bitmesi gerekenler)
ders = {
    "Bitirme": ["Ag", "Derleyici"],
    "Ag": ["Isletim"],
    "Derleyici": ["Algoritmalar"],
    "Algoritmalar": ["Veri"],
    "Isletim": ["Programlama"],
    "Veri": ["Programlama"],
}
print("Sira:", list(graphlib.TopologicalSorter(ders).static_order()))

donguyle = {"A": ["B"], "B": ["C"], "C": ["A"]}
try:
    list(graphlib.TopologicalSorter(donguyle).static_order())
except graphlib.CycleError as hata:
    print("Hata mesaji:", hata.args[0])
    print("Dongu:", hata.args[1])
