# -*- coding: utf-8 -*-
"""S155 frente 5: discriminar fondo contra area con la MISMA pasada vista en I4 (375 m) y M13 (750 m).

POR QUE. En una misma pasada los dos productos comparten satelite, hora y cenit. Un mecanismo puramente geometrico
de huella (area, remuestreo) actua con el mismo factor sobre los dos si siguen la misma ley de agregacion (SUPUESTO:
el verificador de la tarea 1.19 dice que M13 no se agrega; si es asi la ley de M13 es otra, ver el informe). El fondo
NO actua igual: el pixel de 750 m diluye la lava en 4 veces mas superficie, su BT queda mas cerca del fondo y la resta
del fondo pesa mucho mas (frac_bg mediana 0,44 en M contra 0,09 en I). Entonces Q = Rinner(750)/Rinner(375) por pasada:
  - plano con el cenit  -> lo que cae con el angulo es comun a los dos (geometria);
  - cae con el cenit    -> hay un mecanismo extra de M13 que crece con el angulo (fondo, o una ley de area distinta).
Y Q con fondo cero (Qnobg): si el fondo es ese mecanismo extra, Qnobg deberia quedar plano.
Pregunta del instrumento 2: si el pareo de pasadas estuviera roto, Q en nadir no daria ~1; se informa Q nadir.
Poblacion: pasadas con alerta protegida de MIROVA en LOS DOS productos y cumulo nuestro en los dos."""
import io, json, os, sys, statistics as st
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import math
def spearman(x, y):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); rk = [0.0] * len(v); i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                rk[o[k]] = (i + j) / 2.0
            i = j + 1
        return rk
    rx, ry = rank(x), rank(y); mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den
ok = json.load(open(os.path.join(D, "estratos.json"), encoding="utf-8"))
by = {}
for f in ok:
    by.setdefault(f["t"], {})[f["b"]] = f
P = [(t, v["VIIRS375"], v["VIIRS750"]) for t, v in sorted(by.items()) if "VIIRS375" in v and "VIIRS750" in v]
print("\n\n=== MISMA PASADA I4 contra M13: n=%d" % len(P))
print("t zen | Rinner375 Rinner750 Q | Rnobg375 Rnobg750 Qnobg | Rbg20 375 750 Qbg20 | frac_bg 375 750")
rows = []
for t, a, b in P:
    q, qn, qb = b["Rinner"] / a["Rinner"], b["Rnobg"] / a["Rnobg"], b["Rbg20"] / a["Rbg20"]
    rows.append((a["zen"], q, qn, qb))
    print("%s %5.1f | %5.2f %5.2f %5.2f | %5.2f %5.2f %5.2f | %5.2f %5.2f %5.2f | %4.2f %4.2f" % (
        t, a["zen"], a["Rinner"], b["Rinner"], q, a["Rnobg"], b["Rnobg"], qn, a["Rbg20"], b["Rbg20"], qb, a["frac_bg"], b["frac_bg"]))
z = [r[0] for r in rows]
for nombre, i in (("Q", 1), ("Qnobg", 2), ("Qbg20", 3)):
    v = [r[i] for r in rows]
    bins = [(0, 30), (30, 45), (45, 60), (60, 90)]
    meds = ["%d-%d: %.2f (n=%d)" % (lo, hi, st.median([r[i] for r in rows if lo <= r[0] < hi]),
                                    sum(1 for r in rows if lo <= r[0] < hi)) for lo, hi in bins]
    print("%-6s spearman(cenit)=%+.2f | %s" % (nombre, spearman(z, v), " | ".join(meds)))
