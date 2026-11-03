# -*- coding: utf-8 -*-
"""v1 (verificador S173, MODIS): lectura propia de 02_salida.json (re-corrido por el verificador en rerun/).

Pregunta 1 (si lo medido estuviera roto, se veria?): las razones se recalculan desde los campos crudos del JSON
(vrp_mw de cada brazo y vrp_mirova_mw), no se copian del txt; si el JSON y el txt no calzaran, se veria aqui.
Pregunta 2 (instrumento muerto): el control positivo es X2 (2 x V0 exacto en todas las filas, ya en 02); aqui se agrega
el control de conectividad: si todas las mascaras V0 fueran un solo cumulo 8-conexo, el brazo SC NO PUEDE diferir de
V0 por construccion (A116: un cero necesita un instrumento que pueda dar distinto de cero).

Que mide:
 (a) FA (fondo de K) partido en dos efectos: perdida (VRP 0) y razon CONDICIONAL a detectar, por tramo de cenit.
 (b) conectividad 8-vecinos de las celdas V0 de cada pasada: cuantos cumulos tiene cada una.
 (c) la pasada donde X2 no publica aunque V0 si (2026-10-01 08:35): campos del brazo.
 (d) FA = 0 contra 02b alertadas_sobre_anillo = 0.
Uso: python -B v1_analisis_02.py <carpeta con 02_salida.json y 02b_salida.json>
"""
import json
import statistics
import sys
from pathlib import Path

D = Path(sys.argv[1])
d = json.load(open(D / "02_salida.json", encoding="utf-8"))
con = [f for f in d["filas"] if f.get("grilla")]
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


def med(x):
    return round(statistics.median(x), 3) if x else None


pr(f"pasadas con grilla: {len(con)} (ventana de observacion {min(f['dt'] for f in con)} a {max(f['dt'] for f in con)})")
# (a) FA condicional
pr("\n(a) FA (fondo de anillo de K, exceso recortado a 0) por tramo de cenit: razon = vrp_mw del brazo / MIROVA")
for b in ("V0", "FA", "FSH"):
    for nombre, sel in (("z<30", lambda f: f["z"] < 30), ("z>=30", lambda f: f["z"] >= 30)):
        fs = [f for f in con if sel(f)]
        rr = [((f["brazos"][b]["vrp_mw"] or 0.0) / f["vrp_mirova_mw"]) for f in fs]
        ceros = sum(1 for r in rr if r == 0)
        cond = [r for r in rr if r > 0]
        pr(f"   {b:4s} {nombre:6s} n {len(rr)}  mediana con ceros {med(rr)}  ceros {ceros}  mediana condicional a VRP>0 "
           f"{med(cond)} (n {len(cond)})  publica {sum(f['brazos'][b].get('publica') or 0 for f in fs)}")
# FA / V0 por pasada (cuanto baja el fondo de K respecto del de la via, en las que sobreviven)
pr("   FA/V0 por pasada (ordenado por cenit):")
for f in sorted(con, key=lambda x: x["z"]):
    v0 = f["brazos"]["V0"]["vrp_mw"] or 0.0
    fa = f["brazos"]["FA"]["vrp_mw"] or 0.0
    pr(f"     {f['dt']} z {f['z']:5.1f} V0 {v0:6.2f} FA {fa:6.2f} FA/V0 {fa / v0 if v0 else float('nan'):5.2f}")

# (b) conectividad
pr("\n(b) cumulos 8-conexos en las celdas V0 de cada pasada (si todas dan 1, SC = V0 por construccion):")


def n_cumulos(celdas):
    celdas = [tuple(c) for c in celdas]
    s = set(celdas)
    vistos = set()
    n = 0
    for c in celdas:
        if c in vistos:
            continue
        n += 1
        pila = [c]
        vistos.add(c)
        while pila:
            a, b = pila.pop()
            for da in (-1, 0, 1):
                for db in (-1, 0, 1):
                    q = (a + da, b + db)
                    if q in s and q not in vistos:
                        vistos.add(q)
                        pila.append(q)
    return n


nc = {f["dt"]: n_cumulos(f["brazos"]["V0"]["celdas"]) for f in con}
pr("   " + ", ".join(f"{k}: {v}" for k, v in sorted(nc.items())))
pr(f"   pasadas con mas de un cumulo: {sum(v > 1 for v in nc.values())} de {len(nc)}")

# (c) X2 no publica
pr("\n(c) pasadas donde un brazo con VRP > 0 no publica (predicado del tablero):")
for f in con:
    for b, r in f["brazos"].items():
        if (r["vrp_mw"] or 0) > 0 and not r.get("publica"):
            pr(f"   {f['dt']} z {f['z']} brazo {b}: vrp {r['vrp_mw']} pc_vrp {r.get('pc_vrp_mw')} dc {r.get('distance_class')} "
               f"pc_dist {r.get('pc_dist_km')} npix {r.get('npix')} disp {r.get('disp')} motivo {r.get('motivo')}")
    v0 = f["brazos"]["V0"]
    x2 = f["brazos"]["X2"]
    if (v0.get("distance_class"), v0.get("pc_dist_km")) != (x2.get("distance_class"), x2.get("pc_dist_km")):
        pr(f"   {f['dt']}: V0 dc {v0.get('distance_class')} pc_dist {v0.get('pc_dist_km')} | X2 dc {x2.get('distance_class')} pc_dist {x2.get('pc_dist_km')}")

# (d) FA = 0 contra 02b
b2 = {f["dt"]: f for f in json.load(open(D / "02b_salida.json", encoding="utf-8"))}
pr("\n(d) FA = 0 <-> ninguna celda alertada sobre la mediana del anillo (02b):")
ok = 0
for f in con:
    fa0 = (f["brazos"]["FA"]["vrp_mw"] or 0) == 0
    sa0 = b2[f["dt"]]["alertadas_sobre_anillo"] == 0
    ok += fa0 == sa0
    if fa0 or sa0:
        pr(f"   {f['dt']} z {f['z']:5.1f} FA=0 {fa0} sobre_anillo=0 {sa0} (sobre_anillo {b2[f['dt']]['alertadas_sobre_anillo']}/{b2[f['dt']]['npix']})")
pr(f"   coinciden en {ok} de {len(con)}")
(D.parent / "v1_analisis_02_salida.txt" if D.name == "rerun" else D / "v1_analisis_02_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
