def f(k, e, m):
    r = []
    t = 0.0
    for i in k:
        if i[0] is None or i[1] is None or i[2] is None:
            continue
        if i[3] != 1:
            continue
        if i[1] < e:
            continue
        v = i[1] * 0.92 + i[2] * 0.08
        if v <= 85.0:
            continue
        r.append((i[0], v))
        t = t + v
    if len(r) == 0:
        return None
    if m == "ortalama":
        return t / len(r)
    if m == "liste":
        return r
    raise ValueError(m)
