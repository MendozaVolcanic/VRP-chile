# -*- coding: utf-8 -*-
"""S165, VIIRS 375: la regla de posición de la vía contra «cercano». Sólo lectura.

DOS PARTES. (A) Lee la equivalencia de V375-E (equivalencia_v375e.json del worktree cranky-payne-f7d913, S165), que ya
midió cuántas pasadas publican distinto entre la vía y el port con «cercano», y las estratifica por clase: no se
recalcula. (B) Para el cotejo con la Distancia_km de MIROVA hacen falta las distancias de las dos reglas en TODAS las
pasadas, no sólo en las que cambian de publicación: corre la vía de pipeline/ (MV.procesar_grilla, familia VIIRS375,
caja_v375, cráter = get_detection_anchor) sobre las mismas grillas guardadas de los lotes S162, S162b y S159, mide las
reglas sobre esa máscara (comun.reglas) y, de paso, rehace el conteo de (A) con la variante del record de la vía, como
control cruzado de (A).
Población: la MUESTRA estratificada de V375-B/C (clases pos_prot, pos_bajo, neg_pub, neg_resto; no es un censo, los
conteos son de la muestra, sin pesos).
Uso: python v375.py  (escribe v375_salida.txt)
"""
import collections
import io
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = Path(__file__).resolve().parents[2] / ".claude/worktrees/cranky-payne-f7d913"
os.environ["S165_PIPELINE_RAIZ"] = str(WT)     # la vía de 375 (FAMILIAS["VIIRS375"], caja_v375) sólo existe ahí
import comun as C  # noqa: E402
import banco_paridad as B  # noqa: E402

sys.path.insert(0, str(C.RAIZ / "experiments/_s162_v375"))
import evaluar as E  # noqa: E402

MV = C.MV
V375 = C.RAIZ / "experiments/_s162_v375"
EQUIV = C.RAIZ / ".claude/worktrees/cranky-payne-f7d913/experiments/_s165_v375_via/equivalencia_v375e.json"
ART = {"S162": Path(r"C:\vrp-trabajo\temporales\s162_v375\run_40116289866"),
       "S162b": Path(r"C:\vrp-trabajo\temporales\s162_v375\run_40131572769"),
       "S159": Path(r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945")}
CLASE = {"pos_prot": "protegida", "pos_bajo": "bajo1", "neg_pub": "neg_limpio", "neg_resto": "neg_limpio"}
L = []


def pr(*x):
    s = " ".join(str(v) for v in x)
    L.append(s)
    print(s, flush=True)


def objetivos():
    """Copia de equivalencia_v375e.objetivos() (S165 V375-E), la misma población."""
    obj = {}
    for o in json.loads((V375 / "objetivos_v375_bc.json").read_text(encoding="utf-8"))["pasadas"]:
        obj[o["id"]] = dict(o)
    for o in json.loads((V375 / "b2/objetivos_v375_b2.json").read_text(encoding="utf-8"))["pasadas"]:
        assert o["id"] not in obj
        obj[o["id"]] = dict(o)
    for o in json.loads((C.RAIZ / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8")):
        if o["b"] == "VIIRS375" and o["hora_utc"][:10] not in E.EXCLUIDOS:
            assert o["id"] not in obj
            obj[o["id"]] = {**o, "lote": "S159"}
    return obj


def parte_a():
    pr("== A. lectura de la equivalencia de V375-E (sin recalcular)")
    pr("   archivo:", EQUIV, "sha256", C.sha256(EQUIV))
    d = json.loads(EQUIV.read_text(encoding="utf-8"))
    F = {f["i"]: f for f in d["filas"]}
    pr("   pasadas:", len(d["filas"]), "| ventana", min(f["hora"] for f in d["filas"]), "a",
       max(f["hora"] for f in d["filas"]), "| por clase:", dict(collections.Counter(CLASE.get(f["clase"], "resto")
                                                                                     for f in d["filas"])))
    filas = [{"clase": CLASE.get(f["clase"], "resto"), "pub_via": f["pub_via"],
              "pub_cerc_ref": f["pub_port"]["cercano"]} for f in d["filas"]]
    pr("   (en V375-E «cercano» es el port de evaluar.py: alertado más cercano a X0, Y0, regla cerc_ref)")
    res = C.resumen_cambios(filas, pr, "VIIRS 375 (V375-E)", ("cerc_ref",))
    ids = sorted(x[0] for x in d["publicacion"]["cercano"]["distintas"])
    for x in d["publicacion"]["cercano"]["distintas"]:
        f = F[x[0]]
        pr(f"      {x[0]} {x[1]} {x[2]} clase {f['clase']} | vía publica {x[3]}, cercano {x[4]} | npix {x[5]} | "
           f"vía {x[6]} km del cráter, cercano {x[7]} km de X0, Y0, inner {x[8]} | misma máscara {f['misma_mascara']}")
    return res["cerc_ref"], set(ids)


def main():
    t0 = time.time()
    pr("== 0. procedencia")
    pr("   código:", json.dumps(C.procedencia_codigo()))
    pr("   pipeline/ de VIIRS 375 desde el worktree de V375-E:", C.RAIZ_PIPELINE, "HEAD",
       __import__("subprocess").run(["git", "-C", str(WT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip())
    pr("   regla de posición importada igual a origin/main:", json.dumps(C.misma_regla_que_main()))
    ctl = C.control_predicado()
    pr("   control del predicado (summit a 1 km publica, far a 9 km no):", ctl, "OK" if ctl == [True, False] else "FALLA")
    res_a, ids_a = parte_a()

    pr("\n== B. la vía sobre las grillas guardadas")
    V = C.volcanes()
    inner_html = B.inner_desde_html()
    obj = objetivos()
    res = {}
    for lote, art in ART.items():
        for i, r in E.leer_resultados(art).items():
            if i in obj and obj[i]["lote"] == lote:
                res[i] = r
    ids = sorted(obj)
    if os.environ.get("S165_MAX"):
        ids = ids[: int(os.environ["S165_MAX"])]
    sin = collections.Counter()
    filas = []
    for k, i in enumerate(ids):
        o, r = obj[i], res.get(i)
        if r is None or r.get("estado") != "ok":
            sin["sin_resultado_ok"] += 1
            continue
        gz = E.grilla_npz(ART[o["lote"]], i)
        if gz is None:
            sin["sin_grilla_guardada"] += 1
            continue
        mir, tir, _ = gz
        v = V[o["volcan"]]
        g = MV.grilla_del_volcan(o["volcan"], paso_m=375.0, clave_roi="roi_v375")
        go = o["grilla"]
        la, lo = C.get_detection_anchor(v)
        pos = MV.posicion_de(g, la, lo)
        ref = ((g["ul_y"] - go["Y0"]) / g["paso"] - 0.5, (go["X0"] - g["ul_x"]) / g["paso"] - 0.5)
        box = MV.caja_v375(g, la, lo)
        rec = MV.procesar_grilla(mir, tir, g, box, r["dayflag"], r["sunglint"], pos, v["inner_radius_km"],
                                 o["sensor"], familia="VIIRS375")
        celdas = [(p["fila"], p["col"]) for p in rec["anomaly_pixels"]]
        f = {"id": i, "volcan": o["volcan"], "hora": o["hora_utc"], "clase_censo": o.get("clase"),
             "clase": CLASE.get(o.get("clase"), "resto"), "npix_via": len(celdas)}
        if celdas:
            d = C.reglas(celdas, [mir[c] for c in celdas], g["n"], pos, ref, g["paso"] / 1000.0)
            f["d"] = d
            f["reconstruye"] = (abs(d["via"] - rec["primary_cluster"]["centroid_dist_km"]) <= 6e-4
                                and C.clase_dc(d["via"], v["inner_radius_km"]) == rec["distance_class"])
            f["vrp_via"] = rec["vrp_mw"]
            f["constructor_igual"] = C.slim(C.record_desde_pixeles(celdas, [mir[c] for c in celdas], g, pos, v["inner_radius_km"], o["sensor"], rec["vrp_mw"], MV.FAMILIAS["VIIRS375"]["lam_mir"])) == C.slim(rec)
            f["_rec"] = {"via": rec, "cerc_cr": C.variante(rec, d["cerc_cr"], v["inner_radius_km"]),
                         "cerc_ref": C.variante(rec, d["cerc_ref"], v["inner_radius_km"])}
        filas.append(f)
        if (k + 1) % 200 == 0:
            print(f"   ... {k + 1} de {len(ids)} ({time.time() - t0:.0f} s)", flush=True)
    pr("   SIN DATO:", dict(sin), "| evaluadas:", len(filas), "| por clase:",
       dict(collections.Counter(f["clase"] for f in filas)))
    con = [f for f in filas if f["npix_via"]]
    pr(f"   con alertados de la vía: {len(con)}; la regla de comun reproduce distancia y clase del record de "
       f"procesar_grilla: {sum(f['reconstruye'] for f in con)} de {len(con)}")

    pr(f"   el constructor de record de VIIRS 750 (comun.record_desde_pixeles) da el mismo record recortado que "
       f"procesar_grilla: {sum(f['constructor_igual'] for f in con)} de {len(con)}")
    casos, idx = [], []
    for n, f in enumerate(con):
        v = V[f["volcan"]]
        for regla, rr in f["_rec"].items():
            st = C.por_el_almacen(rr, f["volcan"], v, f["hora"])
            f.setdefault("dc_store", {})[regla] = None if st is None else st.get("distance_class")
            casos.append((st, inner_html[f["volcan"]]))
            idx.append((n, regla))
    P = C.publicar(casos)
    for (n, regla), p in zip(idx, P):
        con[n][f"pub_{regla}"] = p
    for f in filas:
        if not f["npix_via"]:
            f.update({"pub_via": False, "pub_cerc_cr": False, "pub_cerc_ref": False})
    pr("   el almacén cambió la distance_class de alguna variante:",
       sum(1 for f in con for regla, rr in f["_rec"].items() if f["dc_store"][regla] != rr.get("distance_class")))
    res_b = C.resumen_cambios(filas, pr, "VIIRS 375 (recálculo)")
    ids_b = {f["id"] for f in con if f["pub_via"] != f["pub_cerc_ref"]}
    pr(f"   control cruzado con V375-E (regla cerc_ref): mismas pasadas que cambian: {ids_b == ids_a} "
       f"(V375-E {sorted(ids_a)}, recálculo {sorted(ids_b)})")
    pr("   distancias distintas por más de una celda (0,375 km) entre vía y cercano, sin importar la publicación:",
       {r: sum(1 for f in con if abs(f["d"]["via"] - f["d"][r]) > 0.375) for r in ("cerc_cr", "cerc_ref")})
    cambios = []
    for f in con:
        if f["pub_via"] != f["pub_cerc_cr"] or f["pub_via"] != f["pub_cerc_ref"]:
            cambios.append({k: f[k] for k in ("id", "volcan", "hora", "clase_censo", "clase", "npix_via", "vrp_via",
                                              "pub_via", "pub_cerc_cr", "pub_cerc_ref")} |
                           {"d": {k: round(f["d"][k], 3) for k in ("via", "cerc_cr", "cerc_ref", "via_ref")},
                            "n_cumulo": f["d"]["n_cumulo"], "inner": V[f["volcan"]]["inner_radius_km"]})
    idxr, proc = C.cargar_referencia()
    pr("   referencia de MIROVA del cotejo:", json.dumps({k: {kk: v[kk] for kk in ("sha_commit", "fecha_commit", "sha256")}
                                                         for k, v in proc.items() if k.endswith(".csv")}))
    pr("   detalle de las que cambian (con lo que MIROVA tiene hoy en esa pasada):")
    for c in cambios:
        c["mirova_hoy"] = [{k: x[k] for k in ("source", "tipo", "vrp_mw", "dist_km")}
                           for x in C.parear(idxr, c["volcan"], "VIIRS375", c["hora"])]
        pr("     ", json.dumps(c, ensure_ascii=False))
    det = C.cotejo([{"volcan": f["volcan"], "hora": f["hora"], "clase": f["clase"], "d": f["d"]} for f in con],
                   idxr, "VIIRS375", C.CELDA_KM["VIIRS375"], pr, "VIIRS 375")
    (C.AQUI / "v375_cambios.json").write_text(json.dumps({"parte_a": res_a, "recalculo": res_b, "cambios": cambios},
                                                         ensure_ascii=False, indent=1), encoding="utf-8")
    (C.TEMP / "v375.json").write_text(json.dumps({"recalculo": res_b, "cambios": cambios, "cotejo": det,
                                                  "sin_dato": dict(sin), "n": len(filas)}, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    pr(f"\nlisto en {time.time() - t0:.0f} s")
    (C.AQUI / "v375_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
