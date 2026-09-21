# -*- coding: utf-8 -*-
"""S149 FRENTE C. Estado contra la tabla CONGELADA de terminado (spec 2026-09-13 seccion 2, lineas 75-95;
bandas en scripts/auto_audit_weekly.py:148-153). Y si MIROVA cumple esas bandas contra si misma.
P1: usa el etiquetador y el predicado del banco (controles ya corridos en medir_brechas.py sobre las mismas
ventanas). P2: toda tasa con n; n 0 = SIN DATO.
Uso: python contra_tabla_congelada.py DESDE HASTA
"""
import collections, io, math, statistics, sys
from datetime import timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev  # noqa: E402
import auto_audit_weekly as aw  # noqa: E402
bp = ev.bp
V = (sys.argv[1], sys.argv[2])
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = ev.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, V)
recs = ev.cargar_brazo(bp.DATA, coords, inner, V); bp.etiquetar(recs, por_vb, ns, nv); ev.anotar_vrp_mirova(recs, por_vb)
print("VENTANA", V, "| bandas", aw.FALSAS_BANDA_TERMINADO)
t = lambda k, n: "SIN DATO" if not n else "%.1f %% (%d/%d)" % (100 * k / n, k, n)
print("\n1. FALSAS por pasada en negativos limpios, por sensor y regimen (banda focal 10, nevado 15)")
for b in bp.BUCKETS:
    for reg in ("focal", "nevado"):
        s = [r for r in recs if r["b"] == b and r["lab"] == "neg_limpio" and aw.REGIMEN[r["vol"]] == reg]
        print("   %-9s %-7s %s" % (b, reg, t(sum(r["pub"] for r in s), len(s))))
print("   volcanes que cumplen su banda, por sensor:")
for b in bp.BUCKETS:
    ok = []
    for vol in bp.VOLS:
        s = [r for r in recs if r["b"] == b and r["lab"] == "neg_limpio" and r["vol"] == vol]
        if s and 100 * sum(r["pub"] for r in s) / len(s) <= aw.FALSAS_BANDA_TERMINADO[aw.REGIMEN[vol]]:
            ok.append(vol)
    print("   %-9s %d de 11: %s" % (b, len(ok), ok))
print("\n2. DETECCION por NOCHE de volcan y sensor (la unidad de la tabla) y por PASADA")
for b in bp.BUCKETS:
    noches = collections.defaultdict(lambda: [0, 0])
    for r in recs:
        if r["b"] == b:
            e = noches[(r["vol"], r["noche"])]
            e[0] |= int(r["lab"] == "pos"); e[1] |= int(r["pub"])
    pn = [k for k, e in noches.items() if e[0]]; perd = [k for k in pn if not noches[k][1]]
    pos = [r for r in recs if r["b"] == b and r["lab"] == "pos"]
    pp = [r for r in pos if not r["pub"]]
    print("   %-9s noches con alerta %3d, perdidas por el sensor %3d | pasadas con alerta %3d, perdidas %3d | de las pasadas perdidas: bajo 0,10 MW %d, 0,10 a 0,50 %d, 0,50 o mas %d" % (
        b, len(pn), len(perd), len(pos), len(pp), sum(1 for r in pp if (r["vrp_ref"] or 0) < .1),
        sum(1 for r in pp if .1 <= (r["vrp_ref"] or 0) < .5), sum(1 for r in pp if (r["vrp_ref"] or 0) >= .5)))
print("\n3. MAGNITUD: mediana nuestra/MIROVA por volcan con n >= 30 (banda 0,8 a 1,25)")
for b in bp.BUCKETS:
    for vol in bp.VOLS:
        rz = [r["disp"] / r["vrp_ref"] for r in recs if r["b"] == b and r["vol"] == vol and r["lab"] == "pos" and r["pub"] and r["vrp_ref"] and r["disp"]]
        if len(rz) >= 30:
            m = statistics.median(rz)
            print("   %-9s %-20s n %3d mediana %.2f %s" % (b, vol, len(rz), m, "CUMPLE" if .8 <= m <= 1.25 else "NO CUMPLE"))
print("\n4. MODIS Lascar por NOCHE: publica en noches con alerta MODIS contra noches sin alerta (neg limpio)")
n = collections.defaultdict(lambda: [set(), 0])
for r in recs:
    if r["b"] == "MODIS" and r["vol"] == "Lascar":
        n[r["noche"]][0].add(r["lab"]); n[r["noche"]][1] |= int(r["pub"])
ca = [e for e in n.values() if "pos" in e[0]]; sa = [e for e in n.values() if "pos" not in e[0] and "neg_limpio" in e[0] and "far_ref" not in e[0]]
print("   con alerta", t(sum(e[1] for e in ca), len(ca)), "| sin alerta", t(sum(e[1] for e in sa), len(sa)))

print("\n5. MIROVA CONTRA SI MISMA frente a las bandas")
TOL = timedelta(seconds=120)
P = collections.defaultdict(list)
for (vol, b), lista in por_vb.items():
    for dt, f in lista:
        P[(vol, b)].append((dt, f))
# magnitud 750/375 mismo instante, por volcan
rz = collections.defaultdict(list)
for (vol, b), lista in P.items():
    if b != "VIIRS375":
        continue
    for dt, f in lista:
        if not bp.es_alerta(f["tipo"]) or not f["vrp_mw"]:
            continue
        g = [x for d2, x in P.get((vol, "VIIRS750"), []) if abs(d2 - dt) <= TOL and bp.es_alerta(x["tipo"]) and x["vrp_mw"]]
        if g:
            rz[vol].append(g[0]["vrp_mw"] / f["vrp_mw"])
tod = [x for v in rz.values() for x in v]
if tod:
    print("   razon 750/375 de MIROVA, misma escena: n %d, mediana %.2f, fraccion de pares dentro de 0,8 a 1,25: %s" % (
        len(tod), statistics.median(tod), t(sum(1 for x in tod if .8 <= x <= 1.25), len(tod))))
    for vol, v in rz.items():
        if len(v) >= 10:
            print("      %-20s n %3d mediana %.2f %s" % (vol, len(v), statistics.median(v), "dentro" if .8 <= statistics.median(v) <= 1.25 else "FUERA de la banda"))
# noche: MIROVA 750 "pierde" noches que MIROVA 375 alerta (misma senal, otro sensor de la misma casa)
nn = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0.0]))
for (vol, b), lista in P.items():
    for dt, f in lista:
        e = nn[(vol, f["fecha_utc"][:10])][b]; e[0] |= int(bp.es_alerta(f["tipo"])); e[1] = max(e[1], f["vrp_mw"] or 0 if bp.es_alerta(f["tipo"]) else 0)
for a, c in (("VIIRS750", "VIIRS375"), ("VIIRS375", "VIIRS750")):
    s = [d for d in nn.values() if d[a][0] and c in d]
    print("   noches en que %s de MIROVA alerta y %s fue listado: %d | %s tambien alerta: %s" % (a, c, len(s), c, t(sum(d[c][0] for d in s), len(s))))
