# -*- coding: utf-8 -*-
"""Verificador S149. Reconteo independiente de la afirmacion 50 = 34 + 16 y 49,5 / 18,3 %.
NO usa bp.parear, bp.etiquetar, bp.indexar_referencia ni cargar_referencia_unificada: lee los dos
CSV congelados con csv.DictReader y rehace etiquetas y pareo. De tabla.json solo toma la lista de
pasadas nuestras y la decision de publicar (pub del evaluador con node y pub2 del port independiente).
Solo lee. Imprime a stdout."""
import csv, json, sys, io, collections
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
EXP = AQUI.parent
CONG = EXP / "_s146_ab_sin_test1" / "_congelado"
T = json.loads((EXP / "_s148_verificador_resultado" / "tabla.json").read_text(encoding="utf-8"))
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"
NOMBRE = {"Chaiten": "Chaiten", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Villarrica": "Villarrica",
          "Llaima": "Llaima", "Nevados de Chillan": "NevadosDeChillan", "Copahue": "Copahue",
          "PlanchonPeteroa": "PlanchonPeteroa", "Tupungatito": "Tupungatito", "Lastarria": "Lastarria",
          "Lascar": "Lascar", "Isluga": "Isluga"}
SENS = {"VIIRS375": "VIIRS375", "VIIRS": "VIIRS750", "MODIS": "MODIS"}

ref = collections.defaultdict(list)   # (vol, bucket) -> [(dt, tipo, vrp, source)]
sin_nombre = collections.Counter()
for nombre, src in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR")):
    with open(CONG / nombre, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            v = NOMBRE.get(r["Volcan"].strip()); s = SENS.get(r["Sensor"].strip())
            if v is None or s is None:
                sin_nombre[(r["Volcan"], r["Sensor"])] += 1; continue
            dt = datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S")
            try: vrp = float(r["VRP_MW"])
            except ValueError: vrp = None
            ref[(v, s)].append((dt, r["Tipo_Registro"].strip(), vrp, src))
print("filas descartadas por nombre o sensor desconocido:", dict(sin_nombre))


def filas_cerca(vol, b, dt, tol):
    return [x for x in ref.get((vol, b), []) if abs((x[0] - dt).total_seconds()) <= tol]


def es_noche(dt):   # pasada nocturna en Chile continental: 00 a 11 UTC
    return dt.hour < 12


def correr(tol, alerta_cualquier_sensor, campo_pub):
    # noches con alerta de MIROVA (filas nocturnas ALERTA*), por volcan, directo del CSV
    noche_alerta_vol, noche_alerta_375, noche_fp_375 = set(), set(), set()
    for (v, s), l in ref.items():
        for dt, tipo, vrp, src in l:
            if not es_noche(dt): continue
            if tipo.startswith("ALERTA"):
                noche_alerta_vol.add((v, dt.date()))
                if s == "VIIRS375": noche_alerta_375.add((v, dt.date()))
            if tipo.startswith("FALSO_POSITIVO") and s == "VIIRS375": noche_fp_375.add((v, dt.date()))
    out = []
    for k, val in T.items():
        vol, b, dts = k.split("|")
        if b != "VIIRS375": continue
        dt = datetime.strptime(dts[:16], "%Y-%m-%d %H:%M")
        ff = filas_cerca(vol, b, dt, tol)
        if any(t.startswith("ALERTA") for _, t, _, _ in ff): lab = "pos"
        elif any(t.startswith("FALSO_POSITIVO") for _, t, _, _ in ff): lab = "far_ref"
        else:
            rut = any(t == "RUTINA" and s_ == "CONS" and (vrp or 0) == 0 for _, t, vrp, s_ in ff)
            na = (vol, dt.date()) in noche_alerta_375; nf = (vol, dt.date()) in noche_fp_375
            lab = "neg_limpio" if (rut and not na and not nf) else "sin_info"
        rut = any(t == "RUTINA" and s_ == "CONS" and (vrp or 0) == 0 for _, t, vrp, s_ in ff)
        out.append(dict(vol=vol, dt=dt, lab=lab, rut=rut, nf=len(ff), lab_tabla=val[B]["lab"],
                        pB=val[B][campo_pub], pF=val[F][campo_pub], sat=val[B]["sensor"], z=val[B]["z"],
                        dts=dts))
    con = noche_alerta_vol if alerta_cualquier_sensor else noche_alerta_375
    cl = [r for r in out if r["lab"] == "sin_info" and (r["vol"], r["dt"].date()) in con]
    return out, cl


def informe(nom, cl):
    ap = [r for r in cl if r["pB"] and not r["pF"]]
    pb = [r for r in cl if r["pB"]]; sv = [r for r in cl if r["pF"]]
    rut = [r for r in cl if r["rut"]]
    print("%s" % nom)
    for n_, s in (("todas", cl), ("publica B", pb), ("apagadas por F", ap), ("sobreviven a F", sv)):
        print("   %-16s n %3d | RUTINA CONS VRP 0 %3d | sin fila %3d" % (n_, len(s), sum(r["rut"] for r in s), sum(not r["rut"] for r in s)))
    if rut: print("   tasa sobre RUTINA (n %d): B %.1f %% | F %.1f %%" % (len(rut), 100 * sum(r["pB"] for r in rut) / len(rut), 100 * sum(r["pF"] for r in rut) / len(rut)))
    print("   F publica y B no (deberia ser 0):", sum(1 for r in cl if r["pF"] and not r["pB"]))
    return ap


print("\n=== A. Replica de la definicion del documento: tol 120 s, noche con alerta en cualquier sensor, pub node")
out, cl = correr(120, True, "pub")
print("   discrepancias de etiqueta contra tabla.json (V375):", sum(1 for r in out if r["lab"] != r["lab_tabla"]), "de", len(out))
for r in out:
    if r["lab"] != r["lab_tabla"]: print("      ", r["vol"], r["dts"], "mio", r["lab"], "tabla", r["lab_tabla"])
ap = informe("A", cl)
print("\n=== B. Igual pero pareo EXACTO al minuto (tol 0)")
informe("B", correr(0, True, "pub")[1])
print("\n=== C. Igual que A con pub2 (port independiente del predicado)")
informe("C", correr(120, True, "pub2")[1])
print("\n=== D. Noche con alerta SOLO VIIRS 375 (la definicion de c1)")
informe("D", correr(120, False, "pub")[1])
print("\n=== E. Tolerancia ancha 600 s (si cambia, hay filas cercanas de otra pasada)")
informe("E", correr(600, True, "pub")[1])

print("\n=== F. Duplicados y ambiguedad del pareo")
for (v, s), l in ref.items():
    if s != "VIIRS375": continue
    c = collections.Counter((dt.strftime("%Y-%m-%d %H:%M"), src) for dt, _, _, src in l)
    d = {k: n for k, n in c.items() if n > 1}
    if d: print("   clave repetida", v, d)
print("   pasadas de la clase con mas de 1 fila pareada:", sum(1 for r in cl if r["nf"] > 1))
# distancia temporal minima entre dos filas V375 del mismo volcan (si < 240 s, tol 120 puede cruzar pasadas)
mn = []
for (v, s), l in ref.items():
    if s != "VIIRS375": continue
    ts = sorted({dt for dt, _, _, src in l if src == "CONS"})
    mn += [(b_ - a_).total_seconds() for a_, b_ in zip(ts, ts[1:])]
print("   separacion minima entre filas CONS V375 consecutivas del mismo volcan: %.0f s | bajo 600 s: %d" % (min(mn), sum(x < 600 for x in mn)))
# lo mismo para NUESTRAS pasadas
mn2 = collections.defaultdict(list)
for r in out: mn2[r["vol"]].append(r["dt"])
g = []
for v, l in mn2.items():
    l.sort(); g += [((b_ - a_).total_seconds(), v, a_, b_) for a_, b_ in zip(l, l[1:])]
print("   separacion minima entre pasadas NUESTRAS V375 consecutivas: %.0f s | bajo 600 s: %d" % (min(g)[0], sum(x[0] < 600 for x in g)))
for x in sorted(g)[:8]:
    if x[0] < 600: print("      ", x[1], x[2], x[3])

print("\n=== G. Por satelite: quien tiene fila y quien no (todas las V375 nocturnas de la tabla)")
c = collections.Counter((r["sat"], r["nf"] > 0) for r in out)
for sat in sorted({r["sat"] for r in out}):
    a_, b_ = c[(sat, True)], c[(sat, False)]
    print("   %-14s con fila %4d | sin fila %4d | %% sin fila %.1f" % (sat, a_, b_, 100 * b_ / (a_ + b_)))
print("   dentro de la clase (171):")
c = collections.Counter((r["sat"], r["rut"]) for r in cl)
for sat in sorted({r["sat"] for r in cl}):
    print("   %-14s RUTINA %3d | sin fila %3d" % (sat, c[(sat, True)], c[(sat, False)]))
print("   apagadas sin fila por satelite:", dict(collections.Counter(r["sat"] for r in ap if not r["rut"])))
print("   apagadas sin fila por fecha:", dict(sorted(collections.Counter(r["dts"][:10] for r in ap if not r["rut"]).items())))
print("   TODAS las sin fila V375 por fecha:", dict(sorted(collections.Counter(r["dts"][:10] for r in out if r["nf"] == 0).items())))
print("   TODAS las V375 por fecha:        ", dict(sorted(collections.Counter(r["dts"][:10] for r in out).items())))

print("\n=== H. Las 34 por volcan y zona")
a34 = [r for r in ap if r["rut"]]
print("  ", dict(collections.Counter(r["vol"] for r in a34)))
print("   z>=52:", sum(1 for r in a34 if r["z"] is not None and r["z"] >= 52), "de", len(a34))
json.dump([dict(vol=r["vol"], dt=r["dts"], rut=r["rut"], sat=r["sat"], z=r["z"]) for r in ap],
          open(AQUI / "apagadas_mias.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
