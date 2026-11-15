import ast, dis, gc, sys
print(sys.version.split()[0])
def f(a, b):
    return a + b * 2
dis.dis(f)
def g():
    return 2 * 3 + 4
print("---- g (sabit katlama)")
dis.dis(g)
print("---- ast")
agac = ast.parse("x = 2 + 3 * 4")
print(ast.dump(agac, indent=2))
print("---- gc")
class Dugum:
    def __init__(self):
        self.kom = None
a = Dugum(); b = Dugum(); a.kom = b; b.kom = a
del a, b
print("toplanan:", gc.collect())
x = []
y = x
print("refcount:", sys.getrefcount(x))
