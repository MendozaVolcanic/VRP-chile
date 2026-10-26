# cuantos picos de la vara principal estan cerca del borde de la seleccion (inner) y no en el crater
import sys, math, statistics as st
sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2]]
exec(open(__file__.replace("conteo_borde.py", "controles_vara.py"), encoding="utf-8").read().split("informe(\"principal")[0])
for nombre, fs in (("principal", filas()), ("estricta todos", filas(filtro="todos")), ("amplia todos", filas(nivel="amplia", filtro="todos"))):
    for lo, hi in ((0, 35), (35, 90)):
        sel = [x for x in fs if lo <= x["cenit"] < hi]
        mx = [max(math.hypot(*x["C"]), math.hypot(*x["M"])) for x in sel]
        lejos = [x for x, m in zip(sel, mx) if m > 3.0]
        print("%-15s cenit %2d-%2d n=%3d  max(|C|,|M|) mediana %.2f  >3 km: %3d  dd mediana de esos %s  dd del resto %s" % (
            nombre, lo, hi, len(sel), st.median(mx), len(lejos),
            round(st.median(dd_v(x) for x in lejos), 3) if lejos else None,
            round(st.median(dd_v(x) for x, m in zip(sel, mx) if m <= 3.0), 3) if len(lejos) < len(sel) else None))
