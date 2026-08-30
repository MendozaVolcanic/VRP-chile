# -*- coding: utf-8 -*-
"""S128 Fase 1 — los 9 pendientes "SIN RESPALDO" de AUDIT_S125 §3, medidos.

Regla B: cada uno termina CONFIRMADO con script, REFUTADO con script, o IMPOSIBLE
con la razon escrita. Nada de prosa.

Los que se pueden medir con el dato que hay en disco:
  D5   "calibracion lograda, ratio 1,35x"      -> recomputar la tabla de hoy
  A12  ΔT por volcan (t_max - t_bg)            -> recomputar la mediana
  D9   residuo "24-83x post-cap" del path D    -> re-medir post nadir-fijo
  R2   ratio suma/maximo del cluster           -> medir sobre el dato persistido
  D14  "la mascara no es el driver del gap"    -> el A/B pareado, que es mejor que
                                                  la correlacion r=-0,23 sin script

Los que NO se pueden, y por que, va en el JSON con su razon.

Regla del proyecto: un par por NOCHE, maximo de ambos lados; pc.vrp_mw nunca
record.vrp_mw (A10); estratificar POR VOLCAN (S126). Todo eso vive en _s126_lib.
Read-only.
"""
import io
import json
import os
import statistics as st
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import (VENTS, bucket, cargar_brazo, cargar_mirova,   # noqa: E402
                       ic95, pares_por_noche, resumen)

VENTANA = ("2026-01-01", "2026-08-30")
R = {}
mirova, diurnas = cargar_mirova(VENTANA)
print("ground truth: %d volcanes con alertas nocturnas | %d diurnas descartadas (A76)"
      % (len(mirova), diurnas))

# ══ D5 · "calibracion lograda, ratio 1,35x" ════════════════════════════════
# El ratio nuestro/MIROVA de hoy, por volcan y por sensor. Si la mediana global
# esta bajo 1, la divergencia marcada "resuelta con 1,35x" describe el frente
# abierto con el signo invertido.
d5 = {}
todos = []
for vol in sorted(VENTS):
    recs = cargar_brazo("mirova_equivalent", vol, VENTANA)
    if not recs:
        continue
    fila = {}
    for buck in ("v375", "v750", "modis"):
        pares = pares_por_noche(recs, set(recs), mirova.get(vol, {}), buck)
        rs = [n / m for _f, n, m in pares if m > 0]
        if not rs:
            fila[buck] = None
            continue
        fila[buck] = {**resumen(rs), "ic95_mediana": ic95(rs)}
        todos += rs
    d5[vol] = fila
R["D5_ratio_hoy"] = {
    "afirmacion_S125": "D5 dice 'calibracion lograda, ratio 1,35x'; la tabla de hoy "
                       "daria mediana ~0,75 = sub-reporte (signo invertido)",
    "global": {**(resumen(todos) or {}), "ic95_mediana": ic95(todos)},
    "por_volcan_sensor": d5,
}

# ══ A12 · ΔT por volcan ═══════════════════════════════════════════════════
# La regla A12 clasifica los volcanes por (t_max - t_bg): <12 K "necesita
# kernel-bg", >20 K "ya calibrado". Cita Lascar 21,6 K e Isluga ~20 K.
a12 = {}
for vol in sorted(VENTS):
    p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    if not os.path.exists(p):
        continue
    por_b = {}
    for rec in json.load(open(p, encoding="utf-8"))["records"]:
        b = bucket(rec.get("sensor"))
        tmax = rec.get("t_max_i04_k") or rec.get("t_max_k")
        tbg = rec.get("t_bg_k")
        if b is None or tmax is None or tbg is None:
            continue
        por_b.setdefault(b, []).append(tmax - tbg)
    a12[vol] = {b: {"n": len(v), "mediana_dT_K": round(st.median(v), 1),
                    "p75": round(sorted(v)[3 * len(v) // 4], 1)}
                for b, v in sorted(por_b.items()) if v}
R["A12_delta_T"] = {
    "afirmacion_A12": "Lascar 21,6 K e Isluga ~20 K -> 'ya calibrados'; <12 K "
                      "necesita kernel-bg",
    "por_volcan_sensor": a12,
}

# ══ D9 · el residuo del path D, re-medido post nadir-fijo ════════════════
# S71 reporto 24-83x de residuo post-cap para el path dNTI contextual. Ese numero
# es ANTERIOR a nadir-fijo (S102/S103), que llevo la magnitud global a 0,78-0,80x.
d9 = {}
for vol in sorted(VENTS):
    recs = cargar_brazo("mirova_equivalent", vol, VENTANA)
    if not recs:
        continue
    solo_d, con_bt = [], []
    for k, rec in recs.items():
        pc = rec.get("primary_cluster") or {}
        v = pc.get("vrp_mw") or 0
        if v <= 0:
            continue
        nd = rec.get("diag_n_dnti_ctx_path") or rec.get("n_dnti_ctx_path") or 0
        nb = rec.get("diag_n_bt_path") or rec.get("n_bt_path") or 0
        nn = rec.get("diag_n_nti_path") or rec.get("n_nti_path") or 0
        (solo_d if (nd > 0 and nb == 0 and nn == 0) else con_bt).append((k, v))
    mv = mirova.get(vol, {})

    def ratios(lst):
        out = []
        for k, v in lst:
            b = bucket(k[1])
            m = mv.get((k[0][:10], b))
            if m and m > 0:
                out.append(v / m)
        return out

    d9[vol] = {"path_D_puro": {"n_records": len(solo_d),
                               "vs_mirova": resumen(ratios(solo_d))},
               "con_BT_o_NTI": {"n_records": len(con_bt),
                                "vs_mirova": resumen(ratios(con_bt))}}
R["D9_residuo_path_D"] = {
    "afirmacion_S125": "el residuo '24-83x post-cap' de D9 es de S71, anterior a "
                       "nadir-fijo; nadie lo re-midio",
    "por_volcan": d9,
}

# ══ R2 · ratio suma/maximo del cluster ═══════════════════════════════════
# Para un cluster de UN pixel suma y maximo son el mismo numero (invariante S127).
# Cuanto se separan en el dato real dice cuanto pesa la eleccion.
r2 = {}
for vol in sorted(VENTS):
    p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    if not os.path.exists(p):
        continue
    rs, un_px = [], 0
    for rec in json.load(open(p, encoding="utf-8"))["records"]:
        pc = rec.get("primary_cluster") or {}
        v = pc.get("vrp_mw") or 0
        npx = pc.get("n_pixels") or 0
        if v <= 0 or not npx:
            continue
        if npx == 1:
            un_px += 1
        px = [q.get("vrp_mw") or 0 for q in (pc.get("pixels") or [])]
        if px and max(px) > 0:
            rs.append(sum(px) / max(px))
    r2[vol] = {"n": len(rs), "clusters_de_1_pixel": un_px,
               "suma_sobre_maximo": resumen(rs) if rs else None}
R["R2_suma_sobre_maximo"] = {
    "afirmacion_S125": "R2 (ratio suma/maximo) quedo sin respaldo",
    "por_volcan": r2,
}

# ══ Los que NO se pueden medir, con la razon ═════════════════════════════
R["_imposibles"] = {
    "A54_95_4_pct_FP_fisicamente_reales": {
        "estado": "IMPOSIBLE de recomputar automaticamente",
        "razon": "la clasificacion a/b/c/d de AUDIT_S86 fue un juicio FISICO por "
                 "record (rasgo volcanico real vs artefacto), hecha a mano con "
                 "conocimiento del volcan. No hay etiqueta persistida en el schema "
                 "que permita reproducirla. Lo unico automatizable es el "
                 "DENOMINADOR (cuantos records sin contraparte MIROVA hay hoy), "
                 "que no es lo que A54 afirma.",
        "que_haria_falta": "re-etiquetar una muestra estratificada por volcan con "
                           "criterio explicito y persistir la etiqueta en el record",
    },
    "D13_31_pct": {"estado": "PENDIENTE", "razon": "el script citado no esta en el "
                   "directorio; el re-calculo del eje 3 dio 27,8 % con denominador "
                   "no declarado. Necesita que se declare el denominador primero."},
    "A84_probe_no_esta_en_git": {
        "estado": "CONFIRMADO por inspeccion",
        "razon": "scratchpad/probe_ctx_cluster_s117.py no esta versionado; sus "
                 "numeros no se recomputan. La otra pata (A/B S106) si esta firme."},
}

out = os.path.join(AQUI, "02_s125_sin_respaldo.json")
json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("escrito:", out)

print("\n══ D5 · ratio nuestro/MIROVA HOY ══")
print("GLOBAL:", json.dumps(R["D5_ratio_hoy"]["global"], ensure_ascii=False))
print("%-22s %26s %26s %26s" % ("volcan", "VIIRS375", "VIIRS750", "MODIS"))
for v, f in d5.items():
    def c(b):
        d = f.get(b)
        return "-" if not d else "n=%-4d med=%5.2f [%s,%s]" % (
            d["n"], d["mediana"], d["ic95_mediana"][0], d["ic95_mediana"][1])
    print("%-22s %26s %26s %26s" % (v, c("v375"), c("v750"), c("modis")))

print("\n══ A12 · ΔT mediano (t_max - t_bg), K ══")
print("%-22s %10s %10s %10s" % ("volcan", "v375", "v750", "modis"))
for v, f in a12.items():
    print("%-22s %10s %10s %10s" % (v,
          f.get("v375", {}).get("mediana_dT_K", "-"),
          f.get("v750", {}).get("mediana_dT_K", "-"),
          f.get("modis", {}).get("mediana_dT_K", "-")))

print("\n══ D9 · path D puro vs MIROVA (post nadir-fijo) ══")
print("%-22s %10s %28s %10s %28s" % ("volcan", "n_D_puro", "ratio D puro",
                                     "n_otros", "ratio otros"))
for v, f in d9.items():
    a, b = f["path_D_puro"], f["con_BT_o_NTI"]
    print("%-22s %10d %28s %10d %28s" % (
        v, a["n_records"],
        "med=%.2f n=%d" % (a["vs_mirova"]["mediana"], a["vs_mirova"]["n"])
        if a["vs_mirova"] else "-",
        b["n_records"],
        "med=%.2f n=%d" % (b["vs_mirova"]["mediana"], b["vs_mirova"]["n"])
        if b["vs_mirova"] else "-"))

print("\n══ R2 · suma/maximo del cluster ══")
for v, f in r2.items():
    print("  %-22s n=%-5d 1px=%-5d %s" % (v, f["n"], f["clusters_de_1_pixel"],
                                          json.dumps(f["suma_sobre_maximo"],
                                                     ensure_ascii=False)))
