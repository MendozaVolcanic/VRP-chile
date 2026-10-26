# -*- coding: utf-8 -*-
"""Verificador S159: afirmaciones 2 (cola) y 3. Usa el predicado del tablero (node) via banco_paridad, sin parches.

Pregunta 1 (lo veria?): si las pasadas partidas publicaran igual que las enteras, la tasa daria parecida;
si el exceso fuera solo por tener dos records (dos chances), la tasa por record del miembro sin la fila
de MIROVA daria la de las enteras. Mido las dos cosas.
Pregunta 2 (instrumento muerto?): control positivo: el banco tiene que dar n_neg y tasas del orden del informe
(V375 ~4.260 negativos, ~2,7 %); si el predicado no corriera, pub seria 0 en todo.
Ventana: 2026-01-10 a 2026-10-21, regla D-9 original (la del banco por defecto).
"""
import collections, json, os, sys
from datetime import timedelta
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(sys.argv[1])
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp
from auto_audit_weekly import _coords_por_volcan
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
from scipy.stats import fisher_exact

ventana = ("2026-01-10", "2026-10-21")
coords = _coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana)
recs = bp.cargar_nuestros(coords, inner, ventana)
bp.etiquetar(recs, por_vb, ns, nv)
nbg = {}
for vol in bp.VOLS:
    for r in json.load(open(RAIZ / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]:
        nbg[(vol, r["sensor"], r["datetime_utc"][:16])] = r.get("diag_n_bg_anillo") or 0
for r in recs:
    r["nbg"] = nbg.get((r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M")), 0)
print("control: pub total", sum(r["pub"] for r in recs), "de", len(recs))
print("etiquetas por sensor:", {b: dict(collections.Counter(r["lab"] for r in recs if r["b"] == b)) for b in bp.BUCKETS})
for b in bp.BUCKETS:
    neg = [r for r in recs if r["b"] == b and r["lab"] == "neg_limpio"]
    print(f"  {b} neg_limpio por record {len(neg)}, publica {sum(r['pub'] for r in neg)}")

# cadenas por sensor (plataforma), paso exacto
g = collections.defaultdict(list)
for r in recs:
    g[(r["vol"], r["sensor"])].append(r)
cad = []
for (vol, s), lst in g.items():
    lst.sort(key=lambda r: r["dt"])
    p = timedelta(minutes=5 if s.startswith("MODIS") else 6)
    cur = [lst[0]]
    for r in lst[1:]:
        if r["dt"] - cur[-1]["dt"] == p: cur.append(r)
        else: cad.append(cur); cur = [r]
    cad.append(cur)
print("largo de cadenas:", collections.Counter(len(c) for c in cad))
for b in bp.BUCKETS:
    enteras = [c[0] for c in cad if len(c) == 1 and c[0]["b"] == b and c[0]["lab"] == "neg_limpio"]
    part = []
    for c in cad:
        if len(c) != 2 or c[0]["b"] != b: continue
        labs = [x["lab"] for x in c]
        if "neg_limpio" in labs and all(l in ("neg_limpio", "sin_info") for l in labs) and labs.count("neg_limpio") == 1:
            part.append(c)
    k1 = sum(r["pub"] for r in enteras); n1 = len(enteras)
    k2 = sum(any(x["pub"] for x in c) for c in part); n2 = len(part)
    odds, pv = fisher_exact([[k2, n2 - k2], [k1, n1 - k1]])
    # quien publica: el miembro de MIROVA (neg_limpio) o el otro (sin_info); fraccion del anillo del que publica
    quien = collections.Counter(); frac_mir = []
    for c in part:
        mir = next(x for x in c if x["lab"] == "neg_limpio"); otro = next(x for x in c if x is not mir)
        tot = (mir["nbg"] + otro["nbg"]) or 1
        fm = mir["nbg"] / tot
        frac_mir.append(fm)
        if mir["pub"]: quien["publica el de MIROVA"] += 1
        if otro["pub"]: quien["publica el otro"] += 1
        if otro["pub"] and not mir["pub"]:
            quien["solo el otro, fm<0.5" if fm < 0.5 else "solo el otro, fm>=0.5"] += 1
        pubs = [x for x in c if x["pub"]]
        if pubs:
            mayor = max(c, key=lambda x: x["nbg"])
            quien["publica el de anillo mayor" if all(x is mayor for x in pubs) else "publica el de anillo menor (o ambos)"] += 1
    otros = [next(x for x in c if x["lab"] == "sin_info") for c in part]
    print(f"{b}: enteras {k1}/{n1} = {k1/max(n1,1):.4f}; partidas (al menos uno publica) {k2}/{n2} = {k2/max(n2,1):.4f};"
          f" Fisher p = {pv:.5f}; por record del miembro sin fila {sum(x['pub'] for x in otros)}/{len(otros)};"
          f" fm<0,5 en {sum(f < 0.5 for f in frac_mir)} de {n2}; {dict(quien)}")
    if b != "VIIRS375":
        continue
    # afirmacion 2: los negativos limpios del gr. de MIROVA con fm<0,5, como fraccion de todos los neg_limpio por record
    nneg = sum(1 for r in recs if r["b"] == b and r["lab"] == "neg_limpio")
for b in bp.BUCKETS:
    part_all = [c for c in cad if len(c) == 2 and c[0]["b"] == b]
    n_low = 0
    for c in part_all:
        labs = [x["lab"] for x in c]
        if labs.count("neg_limpio") != 1 or not all(l in ("neg_limpio", "sin_info") for l in labs): continue
        mir = next(x for x in c if x["lab"] == "neg_limpio"); otro = next(x for x in c if x is not mir)
        if (mir["nbg"] + otro["nbg"]) and mir["nbg"] / (mir["nbg"] + otro["nbg"]) < 0.5: n_low += 1
    nneg = sum(1 for r in recs if r["b"] == b and r["lab"] == "neg_limpio")
    print(f"afirmacion 2, {b}: negativos limpios con el granulo de MIROVA bajo la mitad del anillo {n_low} de {nneg} = {n_low/nneg:.4f}")

# --- detalle V375: cada partida que publica, y Fisher por miembro (dos chances)
b = "VIIRS375"
part = [c for c in cad if len(c) == 2 and c[0]["b"] == b and [x["lab"] for x in c].count("neg_limpio") == 1
        and all(x["lab"] in ("neg_limpio", "sin_info") for x in c)]
for c in part:
    if any(x["pub"] for x in c):
        tot = sum(x["nbg"] for x in c) or 1
        print("  V375 partida publica:", c[0]["vol"], c[0]["sensor"], [(x["dt"].strftime("%m-%d %H:%M"), x["lab"], x["pub"], round(x["nbg"] / tot, 2)) for x in c])
enteras = [c[0] for c in cad if len(c) == 1 and c[0]["b"] == b and c[0]["lab"] == "neg_limpio"]
k1, n1 = sum(r["pub"] for r in enteras), len(enteras)
for quien in ("neg_limpio", "sin_info"):
    mm = [next(x for x in c if x["lab"] == quien) for c in part]
    k = sum(x["pub"] for x in mm)
    print(f"  Fisher por record, miembro {quien}: {k}/{len(mm)} contra {k1}/{n1}: p = {fisher_exact([[k, len(mm)-k], [k1, n1-k1]])[1]:.4f}")
# esperado si cada miembro publicara a la tasa de las enteras (dos chances)
q = k1 / n1
print(f"  esperado con dos chances a la tasa de enteras: {147*(1-(1-q)**2):.1f} de 147")
