# -*- coding: utf-8 -*-
"""S139 eje 2: analisis sobre el banco (importa banco_noches, no reimplementa). READ-ONLY.

Imprime: (a) linea base por volcan y sensor, config por defecto cons_ocr|pipeline|rutina_estricta;
(b) paridad de cobertura; (c) poder estadistico; (d) AUC por volcan de cada campo, con control
barajado POR VOLCAN; (e) reproduccion de los numeros preliminares del orquestador;
(f) contaminacion de RUTINA por OCR.

P1: si el predicado estuviera roto (todo/nada publica) los controles C_TODO/C_NADA del banco lo
    muestran; aqui se reusa la misma tabla. P2: SIN DATO se imprime aparte en cada celda.
"""
import collections
import importlib.util
import json
import random
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("banco", HERE / "banco_noches.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)

coords = B._coords_por_volcan()
inner = B.inner_desde_html()
filas = B.cargar_referencia(coords)
recs = B.cargar_nuestros(coords, inner)
VENT = (min(f["dt"] for f in filas).strftime("%Y-%m-%d"), max(f["dt"] for f in filas).strftime("%Y-%m-%d"))
print("ventana referencia (fecha UTC):", VENT)

ref, nos = B.armar(filas, recs, "cons_ocr", "pipeline", None)
tabla, fa = B.evaluar(ref, nos, "rutina_estricta", "pub", True, VENT)
print("\n(a) LINEA BASE cons_ocr|pipeline|rutina_estricta, predicado dashboard; formato det/total")
print(f"{'volcan':20s}" + "".join(f"{b:>34s}" for b in B.BUCKETS + ['CUALQUIERA']))
for v in B.VOLS:
    s = f"{v:20s}"
    for b in B.BUCKETS + ["CUALQUIERA"]:
        c = tabla.get(f"{v}|{b}")
        if not c:
            s += f"{'-':>34s}"
            continue
        s += f"  pos {c['pos_det']:3d}/{c['pos']:3d} neg {c['neg_det']:4d}/{c['neg']:4d} sd{c['pos_sin_dato']:2d}/{c['neg_sin_dato']:3d}"
    print(s)

print("\n(b) PARIDAD DE COBERTURA (ventana referencia, diurno pipeline, cons_ocr)")
cov = collections.defaultdict(collections.Counter)
for k in set(ref) | set(nos):
    if not (VENT[0] <= k[2] <= VENT[1]):
        continue
    tiene_ref = k in ref and (ref[k]["cons_rows"] + ref[k]["ocr_rows"]) > 0
    tiene_nos = k in nos and nos[k]["n"] > 0
    cov[k[1]][("ambos" if tiene_ref and tiene_nos else "solo_ref" if tiene_ref else "solo_nos")] += 1
    if tiene_ref and not tiene_nos and ref[k]["alerta"] > 0:
        cov[k[1]]["solo_ref_con_alerta"] += 1
for b, c in cov.items():
    print(" ", b, dict(c))
# meses sin records nuestros con filas de referencia
hueco = collections.Counter()
for k, e in ref.items():
    if VENT[0] <= k[2] <= VENT[1] and (k not in nos or nos[k]["n"] == 0):
        hueco[(k[0], k[2][:7])] += 1
print("  noches-sensor con referencia y sin record nuestro, por volcan-mes (>=10):",
      {f"{a}|{m}": n for (a, m), n in sorted(hueco.items()) if n >= 10})

print("\n(c) PODER: positivos por volcan y sensor (con cobertura)")
for b in B.BUCKETS:
    print(" ", b, {v: tabla.get(f"{v}|{b}", {}).get("pos", 0) for v in B.VOLS})

print("\n(d) AUC POR VOLCAN (noche-sensor, maximo por noche) y control barajado por volcan")
rng = random.Random(11)
fa_b = []
grupos = collections.defaultdict(list)
for i, x in enumerate(fa):
    grupos[(x[0], x[1])].append(i)
fa_b = list(fa)
for idx in grupos.values():
    labs = [fa[i][2] for i in idx]
    rng.shuffle(labs)
    for i, lab in zip(idx, labs):
        fa_b[i] = (fa[i][0], fa[i][1], lab, fa[i][3])
res_auc = {}
for b in B.BUCKETS:
    a = B.aucs(fa, b)
    ab = B.aucs(fa_b, b)
    res_auc[b] = a
    print(f"  == {b}")
    for campo in a:
        pv = {v: x["auc"] for v, x in a[campo]["por_volcan"].items() if x["n_pos"] >= 5 and x["n_neg"] >= 5}
        print(f"    {campo:20s} pooled {a[campo]['pooled']}  media/vol {a[campo]['media_por_volcan_pond_npos(npos>=5)']}"
              f"  [barajado media/vol {ab[campo]['media_por_volcan_pond_npos(npos>=5)']}]  por vol (npos>=5): {pv}")
(HERE / "auc_por_volcan.json").write_text(json.dumps(res_auc, indent=1), encoding="utf-8")

print("\n(e) REPRODUCCION DE NUMEROS PRELIMINARES (MODIS, hora UTC<12, CONS)")
ref_u, nos_u = B.armar(filas, recs, "cons", "utc12", None)
for cob in (True, False):
    t, fa_u = B.evaluar(ref_u, nos_u, "sin_alerta", "pub", cob, None)
    c = t.get("Lascar|MODIS")
    print(f"  exigir_cobertura={cob} Lascar MODIS: alerta det {c['pos_det']}/{c['pos']} (sin dato {c['pos_sin_dato']})")
    tot = collections.Counter()
    for v in B.VOLS:
        cc = t.get(f"{v}|MODIS", {})
        for kk in ("neg", "neg_det", "pos", "pos_det"):
            tot[kk] += cc.get(kk, 0)
    print(f"    11 vol MODIS: sin alerta con deteccion {tot['neg_det']}/{tot['neg']}; alertas det {tot['pos_det']}/{tot['pos']}")
    for v in ("PuyehueCordonCaulle", "Chaiten"):
        cc = t[f"{v}|MODIS"]
        print(f"    {v}: neg det {cc['neg_det']}/{cc['neg']} = {cc['neg_det']/cc['neg']:.2f}")
    t2, _ = B.evaluar(ref_u, nos_u, "sin_alerta", "cum_inner", cob, None)
    tot = collections.Counter()
    for v in B.VOLS:
        cc = t2.get(f"{v}|MODIS", {})
        for kk in ("neg", "neg_det", "pos", "pos_det"):
            tot[kk] += cc.get(kk, 0)
    print(f"    predicado cumulo (pc.vrp>0 y centroide<=inner, sin distance_class): alertas {tot['pos_det']}/{tot['pos']}, sin alerta {tot['neg_det']}/{tot['neg']}")
# Lascar: noches alerta con cumulo cerca y far
al_l = [k for k, e in ref_u.items() if k[0] == "Lascar" and k[1] == "MODIS" and e["alerta"] > 0]
far_cerca, fh = 0, []
for k in al_l:
    n = nos_u.get(k)
    if n and not n["pub"] and n["far_cum_cerca"]:
        far_cerca += 1
rl = [r for r in recs if r["vol"] == "Lascar" and r["b"] == "MODIS" and r["dc"] == "far" and r["cum_inner"]
      and r["dt"].hour < 12 and (r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d")) in set(al_l)]
print(f"  Lascar MODIS noches ALERTA no publicadas con cumulo en inner y far: {far_cerca} de {len(al_l)};"
      f" mediana final_hotspot_dist_km de esos records {statistics.median([r['fh_dist'] for r in rl if r['fh_dist'] is not None]):.1f} km (n={len(rl)}),"
      f" mediana pc_dist {statistics.median([r['pc_dist'] for r in rl]):.2f} km")
_, fa_u = B.evaluar(ref_u, nos_u, "sin_alerta", "pub", True, None)
a = B.aucs(fa_u, "MODIS")
print("  Lascar MODIS AUC (sin_alerta, utc12, cons): pc_vrp", a["pc_vrp"]["por_volcan"]["Lascar"],
      "nti_max", a["nti_max"]["por_volcan"]["Lascar"], "summitgated", a["pc_vrp_summitgated"]["por_volcan"]["Lascar"])

print("\n(f) CONTAMINACION DE RUTINA POR OCR (diurno pipeline)")
ref_c, _ = B.armar(filas, recs, "cons", "pipeline", None)
for b in B.BUCKETS:
    rut = [k for k, e in ref_c.items() if e["cons_rows"] and e["rutina"] and not e["fp"] and not e["alerta"] and k[1] == b]
    con_ocr = [k for k in rut if ref[k]["alerta"] > 0]
    print(f"  {b}: noches RUTINA estricta CONS {len(rut)}; con ALERTA OCR esa noche-sensor {len(con_ocr)}"
          f" ({100*len(con_ocr)/max(1,len(rut)):.1f} %) por volcan {dict(collections.Counter(k[0] for k in con_ocr))}")
# pasadas OCR alerta sin fila CONS en +-10 min
cons_idx = collections.defaultdict(list)
for f in filas:
    if f["fuente"] == "CONS":
        cons_idx[(f["vol"], f["b"])].append(f["dt"])
sin = collections.Counter(); tot = collections.Counter(); con_rut = collections.Counter()
cons_tipo = {(f["vol"], f["b"], f["dt"]): f["tipo"] for f in filas if f["fuente"] == "CONS"}
for f in filas:
    if f["fuente"] != "OCR" or not f["tipo"].startswith("ALERTA"):
        continue
    tot[f["b"]] += 1
    near = [d for d in cons_idx[(f["vol"], f["b"])] if abs((d - f["dt"]).total_seconds()) <= 600]
    if not near:
        sin[f["b"]] += 1
    elif all(cons_tipo[(f["vol"], f["b"], d)] == "RUTINA" for d in near):
        con_rut[f["b"]] += 1
print("  alertas OCR:", dict(tot), "| sin pasada CONS a +-10 min:", dict(sin), "| con pasada CONS RUTINA a +-10 min:", dict(con_rut))

print("\n(g) TASA DE PUBLICACION POR NOCHE-SENSOR, TODAS LAS NOCHES CON RECORD (ventana ref, sin etiqueta)")
for b in B.BUCKETS:
    ks = [k for k in nos if k[1] == b and VENT[0] <= k[2] <= VENT[1] and nos[k]["n"]]
    print(f"  {b}: {sum(nos[k]['pub'] for k in ks)}/{len(ks)}")
