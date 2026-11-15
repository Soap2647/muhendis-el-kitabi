# -*- coding: utf-8 -*-
"""Kapsam ve hata örnekleri: çıktıları bölümde gösterilir."""
from mini import vm_ile_calistir
from mini_on import HataDerleme

kapsam = """
let x = 1;
let y = x + 1;
if (y > 1) {
    let x = y * 10;
    print x;
}
print x;
"""
print("kapsam:", vm_ile_calistir(kapsam).ciktilar)

hatalar = [
    "let a = 1;\nprint z;",
    "let a = 1;\nlet b = a + true;",
    "fn f(x) { return x; }\nprint f(1, 2);",
]
for k in hatalar:
    try:
        vm_ile_calistir(k)
    except HataDerleme as e:
        print("HATA", e)
