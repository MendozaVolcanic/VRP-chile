#!/usr/bin/env python
"""V2: F2-201. De las 171 protegidas (lectura A), cuantas son «de crater» segun clase_mirova.protegida_de_crater (V375-A, la
lectura del propio proyecto que se informa al lado de A) y cuantas de las no publicadas lo son.
P1: control positivo: forzar pub=1 a las perdidas da 171/171 (hecho en v2_indep_banco.py); aca el control es que al menos una protegida
SI sea de crater (si todas dieran False el clasificador estaria muerto). P2: n de cada denominador impreso."""
import collections, os, sys
from pathlib import Path
ARBOL = Path(sys.argv[1]); sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL)); os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp, clase_mirova as cm
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html(); V = ("2026-03-01", "2026-11-07")
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
recs = bp.cargar_nuestros(coords, inner, V)
por_vb, ns, nv, n = bp.indexar_referencia(filas, coords, V, regla_minimas="SN"); bp.etiquetar(recs, por_vb, ns, nv)
pas = cm.resumir_pasadas(filas, canal="union", regla_minimas="SN")
idx = collections.defaultdict(list)
for q in pas:
    if q.sensor_bucket == "VIIRS375": idx[q.volcano].append(q)
c = collections.Counter(); motivos = collections.Counter()
for r in recs:
    if r["b"] != "VIIRS375": continue
    par = bp.parear(por_vb.get((r["vol"], "VIIRS375"), []), r["dt"])
    if not any(cm.alerta_protegida(f) for f in par): continue
    qs = [q for q in idx[r["vol"]] if abs((q.instante.replace(tzinfo=None) - r["dt"].replace(tzinfo=None)).total_seconds()) <= 120]
    if not qs: c["sin_pasada_resumida"] += 1; continue
    ok = any(cm.protegida_de_crater(q, inner[r["vol"]], r["sensor"])[0] for q in qs)
    for q in qs:
        for m in cm.protegida_de_crater(q, inner[r["vol"]], r["sensor"])[1]: motivos[m] += 1
    c["prot"] += 1; c["prot_pub"] += r["pub"]
    if ok: c["de_crater"] += 1; c["de_crater_pub"] += r["pub"]
    else: c["no_crater"] += 1; c["no_crater_pub"] += r["pub"]
L = [f"protegidas {dict(c)}", f"motivos de no-crater (por pasada resumida) {dict(motivos)}"]
Path(sys.argv[2]).write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))
