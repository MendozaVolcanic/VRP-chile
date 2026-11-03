# -*- coding: utf-8 -*-
"""v02 (verificador V375, S173): caminos sobre los lotes retrospectivos y el cenit, leyendo los JSON de los lotes y
la salida s02 de mi re-corrida (no la del auditor).

Mide:
  (a) granulos contados dos veces entre lotes: distintas claves (sensor, hora) con el MISMO nombre de granulo, y el mismo
      nombre de granulo con distinta hora (redondeo). Control positivo: se inyecta un duplicado artificial.
  (b) cenit: K_z (record, pixel del final_hotspot) contra z_via (geometria_centro del lote, centro del volcan): cuantos
      de los pares de B cambian de tramo en 30 grados segun cual se use.
  (c) C13 del probe contra la via re-corrida: diferencia absoluta y relativa, npix, y si la banda de jitter del probe
      (vrp_banda, 20 semillas de perturbacion del relleno) cubre el valor de la via. Si la cubre, la diferencia es la
      degeneracion del relleno (triangulacion), no otra cosa.
  (d) hitos A119 dentro de los 66 pares: cuantos pares toman el VRP de MIROVA de una fila OCR, por plataforma y fecha
      respecto del 2026-10-09 / 2026-10-10.
  (e) lotes con codigo distinto: sha de K del probe por lote (probeK) contra sha del record de produccion (K_sha).
P2: si los lotes no se leyeran, n_entradas = 0; se imprime por lote.
Uso: python -I v02_lotes_cenit_c13.py <s02_v375e_pasadas.csv mio> <s01_k_pasadas.csv mio> <salida.json>
"""
import csv, glob, json, math, os, sys
from collections import Counter, defaultdict

VCSV, KCSV, OUT = sys.argv[1:4]
VOL = "NevadosDeChillan"
LOTES = {"S162": "C:/vrp-trabajo/temporales/s162_v375/run_40116289866",
         "S162b": "C:/vrp-trabajo/temporales/s162_v375/run_40131572769",
         "S159": "D:/vrp-trabajo/temporales/s159_portes/run_39712862945",
         "FAR": "D:/vrp-trabajo/temporales/s167_v375e_far/run_40773794395"}
PLAT = {"VNP": "VIIRS_SNPP", "VJ1": "VIIRS_NOAA20", "VJ2": "VIIRS_NOAA21"}


def f(x):
    try:
        y = float(x)
        return None if math.isnan(y) else y
    except (TypeError, ValueError):
        return None


out = {}
# (a) + (c) + (e): leer lotes
ent = []
for lote, base in LOTES.items():
    n = 0
    for fn in glob.glob(os.path.join(base, "**", "resultados_VIIRS375*.json"), recursive=True):
        for x in json.load(open(fn, encoding="utf-8")):
            if x.get("volcan") != VOL:
                continue
            n += 1
            kr = (x.get("K") or {}).get("record") or {}
            ent.append({"lote": lote, "granule": x.get("granule"), "hora": x.get("hora_utc"), "estado": x.get("estado"),
                        "plat": PLAT.get((x.get("granule") or "")[:3]), "id": x.get("id"),
                        "c13": ((x.get("port") or {}).get("C13") or {}),
                        "k_sha": (kr.get("regimen") or {}).get("codigo_sha"), "k_proc": kr.get("processed_utc")})
    out[f"entradas_{lote}"] = n
ok = [e for e in ent if e["estado"] == "ok"]
por_gran = defaultdict(set)
for e in ok:
    por_gran[e["granule"]].add((e["plat"], e["hora"]))
out["granulos_distintos_ok"] = len(por_gran)
out["claves_(plat,hora)_distintas_ok"] = len({(e["plat"], e["hora"]) for e in ok})
out["granulo_con_dos_horas"] = {g: sorted(v) for g, v in por_gran.items() if len(v) > 1}
por_clave = defaultdict(set)
for e in ok:
    por_clave[(e["plat"], e["hora"])].add(e["granule"])
out["clave_con_dos_granulos"] = {str(k): sorted(v) for k, v in por_clave.items() if len(v) > 1}
# control positivo (a)
pg2 = defaultdict(set)
for e in ok + [dict(ok[0], hora="1999-01-01 00:00")]:
    pg2[e["granule"]].add((e["plat"], e["hora"]))
out["control_pos_granulo_dos_horas_(+1 artificial)"] = sum(1 for v in pg2.values() if len(v) > 1)
# (e) sha de K del probe por lote
out["probeK_sha_por_lote"] = {l: dict(Counter((e["k_sha"] or "?")[:9] for e in ok if e["lote"] == l)) for l in LOTES}

# (b) cenit y (c) C13, sobre mi s02
V = list(csv.DictReader(open(VCSV, encoding="utf-8")))
K = {(r["sensor"], r["dt"]): r for r in csv.DictReader(open(KCSV, encoding="utf-8")) if r["b"] == "VIIRS375"}
B = [r for r in V if f(r["vrp_M"]) and f(r["vrp_M"]) > 0 and r["K_pub"] == "1" and f(r["K_disp"]) and f(r["K_disp"]) > 0
     and r["via_pub"] == "1" and f(r["via_disp"]) and f(r["via_disp"]) > 0]
out["n_B"] = len(B)
cambia = [(r["dt"], r["sensor"], f(r["K_z"]), f(r["z_via"])) for r in B
          if (f(r["K_z"]) < 30) != (f(r["z_via"]) < 30)]
out["B_cambian_de_tramo_30_segun_cenit"] = cambia
out["B_dz_max_Kz_menos_zvia"] = max(abs(f(r["K_z"]) - f(r["z_via"])) for r in B)
out["B_K_sha"] = dict(Counter((r["K_sha"] or "?")[:9] for r in B))
out["B_K_proc_min_max"] = [min(r["K_proc"] for r in B), max(r["K_proc"] for r in B)]
out["B_lotes"] = dict(Counter(r["lotes"] for r in B))
# cenit del record contra el del pixel: distancia del final_hotspot al crater en los pares de A (66)
# (c) C13
c13 = {}
for e in ok:
    c13[(e["plat"], e["hora"])] = e["c13"]
difs = []
for r in V:
    if not r["via_npix"] or r["br_C13"] in ("", None):
        continue
    a, b = f(r["via_vrp_rec"]), f(r["br_C13"])
    if a is None or b is None:
        continue
    banda = c13.get((r["sensor"], r["dt"]), {}).get("vrp_banda")
    npc = c13.get((r["sensor"], r["dt"]), {}).get("npix")
    difs.append({"dt": r["dt"], "plat": r["sensor"], "npix_via": int(float(r["via_npix"])), "npix_C13": npc,
                 "via": a, "C13": b, "dif_abs": round(abs(a - b), 4), "dif_rel_%": round(100 * abs(a - b) / max(b, 1e-9), 2),
                 "banda_C13": banda, "via_dentro_banda": (banda is not None and min(banda) - 1e-6 <= a <= max(banda) + 1e-6)})
gt = [x for x in difs if x["dif_abs"] > 1e-3]
out["C13_n_pares"] = len(difs)
out["C13_n_dif_gt_1e-3"] = len(gt)
out["C13_n_dif_gt_1e-3_y_npix_gt_4"] = sum(1 for x in gt if x["npix_via"] > 4)
out["C13_npix_distinto"] = sum(1 for x in difs if x["npix_C13"] is not None and x["npix_C13"] != x["npix_via"])
out["C13_dif_rel_max_%_npix_gt_4"] = max([x["dif_rel_%"] for x in gt if x["npix_via"] > 4], default=None)
out["C13_gt_dentro_banda"] = sum(1 for x in gt if x["via_dentro_banda"])
out["C13_detalle_gt"] = gt
# (d) A119 en los 66 pares del auditor (fuente del VRP de MIROVA)
A = [r for r in K.values() if f(r["vrp_M"]) and f(r["vrp_M"]) > 0 and r["pub"] == "1" and f(r["disp"]) and f(r["disp"]) > 0]
out["A_n"] = len(A)
out["A_src_M"] = dict(Counter(r["src_M"] for r in A))
out["A_OCR_detalle"] = [(r["dt"], r["sensor"], r["vrp_M"], r["vrp_M_cons"]) for r in A if r["src_M"] == "OCR"]
out["A_sha"] = dict(Counter((r["sha"] or "?")[:9] for r in A))
out["A_solz_min"] = min(f(r["solz"]) for r in A if f(r["solz"]) is not None)
out["A_noches_distintas"] = len({r["noche"] for r in A})
json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
