# -*- coding: utf-8 -*-
"""S165, MODIS: cuántas pasadas del censo MOD-D cambian de publicación entre la regla de la vía («más radiante») y
«cercano». Sólo lectura.

QUÉ HACE. Sobre las 5.465 pasadas nocturnas del censo MOD-D (D:\\vrp-trabajo\\temporales\\s162_modd, tag
s162-modd-tag), corre la VÍA de pipeline/ (MV.procesar_grilla, familia MODIS, caja de grillas_mirova.yaml como en
calcular_vrp_granulo, cráter = get_detection_anchor) sobre la grilla 51 x 51 que guardó el probe (grilla_NNNN.npz,
mir y tir). Del record de la vía salen la máscara y la distancia de la vía; las otras reglas se miden sobre esa misma
máscara (comun.reglas). Cada variante pasa por store.append_record y por el predicado del tablero con node.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Si la reconstrucción de la regla de la vía estuviera mal, la distancia de comun
no calzaría con el centroid_dist_km del record de procesar_grilla: se cuenta pasada por pasada. (2) Si el predicado
no mirara distance_class, cualquier conteo de cambios daría 0: control_predicado tiene que dar [True, False]. Y la
máscara de la vía se coteja con la del port del censo (brazo «fisica», el PM aprobado): si difieren, se dice cuántas.
Una pasada sin grilla o sin port es SIN DATO y se cuenta aparte.
Uso: python modis.py  (escribe modis_salida.txt y D:\\...\\s165_regla_posicion\\modis.json)
"""
import collections
import glob
import io
import json
import os
import subprocess
import sys
import time

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import comun as C  # noqa: E402
import banco_paridad as B  # noqa: E402

MV = C.MV
CENSO = r"D:\vrp-trabajo\temporales\s162_modd\censo"
LAB = {"protegida": "protegida", "bajo1": "bajo1", "neg_limpio": "neg_limpio"}
L = []


def pr(*x):
    s = " ".join(str(v) for v in x)
    L.append(s)
    print(s, flush=True)


def main():
    t0 = time.time()
    pr("== 0. procedencia")
    pr("   código:", json.dumps(C.procedencia_codigo()))
    pr("   regla de posición importada igual a origin/main:", json.dumps(C.misma_regla_que_main()))
    grillas = json.loads(subprocess.run(["git", "-C", str(C.RAIZ), "show",
                                         "s162-modd-tag:experiments/_s162_modis_paquete/grillas.json"],
                                        capture_output=True, text=True).stdout)
    recs, npz = [], {}
    for a in sorted(glob.glob(CENSO + r"\**\ab_parte*.jsonl", recursive=True)):
        for f in glob.glob(os.path.join(os.path.dirname(a), "grilla_*.npz")):
            npz[int(os.path.basename(f)[7:-4])] = f
        for x in open(a, encoding="utf-8"):
            r = json.loads(x)
            if r.get("tipo") == "record":
                recs.append(r)
    pr(f"   censo MOD-D: {len(recs)} records, {len(npz)} grillas guardadas; ventana "
       f"{min(r['dt'] for r in recs)} a {max(r['dt'] for r in recs)}")
    V = C.volcanes()
    inner_html = B.inner_desde_html()
    pr("   inner del tablero distinto del de volcanoes.yaml en:",
       [n for n in inner_html if V[n].get("inner_radius_km") != inner_html[n]])
    ctl = C.control_predicado()
    pr("   control del predicado (summit a 1 km publica, far a 9 km no):", ctl, "OK" if ctl == [True, False] else "FALLA")

    cfg = MV.FAMILIAS["MODIS"]
    sin = collections.Counter()
    filas = []
    dif_g = []
    orden = sorted(recs, key=lambda r: r["id"])
    if os.environ.get("S165_MAX"):            # sólo para probar el script
        orden = [r for r in orden if r["id"] in npz and (r.get("port") or {}).get("fisica", {}).get("npix")][: int(os.environ["S165_MAX"])]
    for k, r in enumerate(orden):
        if r["estado"] != "ok" or r.get("port_estado") != "ok" or not r.get("port"):
            sin[f"{r['estado']}|{r.get('port_estado')}"] += 1
            continue
        if r["id"] not in npz:
            sin["sin_grilla"] += 1
            continue
        z = np.load(npz[r["id"]])
        mir, tir = z["mir"].astype(np.float64), z["tir"].astype(np.float64)
        v = V[r["vol"]]
        g = MV.grilla_del_volcan(r["vol"], paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
        gt = grillas[r["vol"]]
        dif_g.append(max(abs(g["ul_x"] - gt["ul_x"]), abs(g["ul_y"] - gt["ul_y"])))
        la, lo = C.get_detection_anchor(v)
        pos = MV.posicion_de(g, la, lo)
        ref = ((g["ul_y"] - gt["Y0"]) / g["paso"] - 0.5, (gt["X0"] - g["ul_x"]) / g["paso"] - 0.5)
        box = MV.caja_roi(g.get("roi", "def"), n=g["n"], celda_crater=MV.celda_de(g, la, lo),
                          inner_km=v["inner_radius_km"], lado_sensible=cfg["lado_sensible"],
                          lado_anillo=cfg["lado_anillo"], paso_m=g["paso"])
        rec = MV.procesar_grilla(mir, tir, g, box, r["dayflag"], r["sunglint"], pos, v["inner_radius_km"],
                                 r["sensor"], familia="MODIS")
        celdas = [(p["fila"], p["col"]) for p in rec["anomaly_pixels"]]
        port = sorted((q[0], q[1]) for q in (r["port"].get("fisica") or {}).get("pixeles") or [])
        fila = {"id": r["id"], "volcan": r["vol"], "hora": r["dt"], "lab": r["lab"], "clase": LAB.get(r["lab"], "resto"),
                "npix_via": len(celdas), "npix_port": len(port), "misma_mascara_que_port": sorted(celdas) == port}
        if celdas:
            d = C.reglas(celdas, [mir[c] for c in celdas], g["n"], pos, ref, g["paso"] / 1000.0)
            fila["d"] = d
            fila["dc_via_record"] = rec["distance_class"]
            fila["d_via_record"] = rec["primary_cluster"]["centroid_dist_km"]
            fila["reconstruye"] = (abs(d["via"] - fila["d_via_record"]) <= 6e-4
                                   and C.clase_dc(d["via"], v["inner_radius_km"]) == rec["distance_class"])
            fila["vrp_via"] = rec["vrp_mw"]
            fila["constructor_igual"] = C.slim(C.record_desde_pixeles(celdas, [mir[c] for c in celdas], g, pos, v["inner_radius_km"], r["sensor"], rec["vrp_mw"], cfg["lam_mir"])) == C.slim(rec)
            # la referencia del censo: q[3] del port es la distancia a X0, Y0; tiene que calzar con la de comun
            q3 = {(q[0], q[1]): q[3] for q in (r["port"].get("fisica") or {}).get("pixeles") or []}
            fila["ref_calza_q3"] = all(abs(np.hypot(f - ref[0], c - ref[1]) * g["paso"] / 1000 - q3[(f, c)]) <= 6e-4
                                       for f, c in celdas if (f, c) in q3)
            fila["_rec"] = {"via": rec, "cerc_cr": C.variante(rec, d["cerc_cr"], v["inner_radius_km"]),
                            "cerc_ref": C.variante(rec, d["cerc_ref"], v["inner_radius_km"])}
        filas.append(fila)
        if (k + 1) % 500 == 0:
            print(f"   ... {k + 1} de {len(recs)} ({time.time() - t0:.0f} s)", flush=True)
    pr("   SIN DATO:", dict(sin), "| evaluadas:", len(filas), "| máx diferencia de grilla vía contra el probe (m):",
       round(max(dif_g), 4))
    pr("   evaluadas por clase:", dict(collections.Counter(f["clase"] for f in filas)))

    con = [f for f in filas if f["npix_via"]]
    pr("\n== 1. controles del instrumento")
    pr(f"   pasadas con alertados de la vía: {con and len(con)}; misma máscara que el port «fisica» del censo: "
       f"{sum(f['misma_mascara_que_port'] for f in filas)} de {len(filas)} (con alertados en alguno: "
       f"{sum(1 for f in filas if f['npix_via'] or f['npix_port'])})")
    pr("   máscaras distintas (id, volcán, hora, npix vía, npix port):",
       [(f["id"], f["volcan"], f["hora"], f["npix_via"], f["npix_port"]) for f in filas if not f["misma_mascara_que_port"]])
    pr(f"   la regla de comun reproduce la distancia y la clase del record de procesar_grilla: "
       f"{sum(f['reconstruye'] for f in con)} de {len(con)}")
    pr(f"   el constructor de record de VIIRS 750 (comun.record_desde_pixeles) da el mismo record recortado que "
       f"procesar_grilla: {sum(f['constructor_igual'] for f in con)} de {len(con)}")
    pr(f"   la referencia del censo (X0, Y0 de grillas.json) calza con el q[3] del port: "
       f"{sum(f['ref_calza_q3'] for f in con)} de {len(con)}")

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

    pr("\n== 2. cambios de publicación (predicado del tablero con node)")
    res = C.resumen_cambios(filas, pr, "MODIS")
    pr("   distancias distintas por más de una celda (1 km) entre vía y cercano, sin importar la publicación:",
       {r: sum(1 for f in con if abs(f["d"]["via"] - f["d"][r]) > 1.0) for r in ("cerc_cr", "cerc_ref")})
    cambios = []
    for f in con:
        if f["pub_via"] != f["pub_cerc_cr"] or f["pub_via"] != f["pub_cerc_ref"]:
            cambios.append({k: f[k] for k in ("id", "volcan", "hora", "lab", "clase", "npix_via", "vrp_via",
                                              "pub_via", "pub_cerc_cr", "pub_cerc_ref")} |
                           {"d": {k: round(f["d"][k], 3) for k in ("via", "cerc_cr", "cerc_ref", "via_ref")},
                            "n_cumulo": f["d"]["n_cumulo"], "inner": V[f["volcan"]]["inner_radius_km"]})
    pr("   detalle de las que cambian:")
    for c in cambios:
        pr("     ", json.dumps(c, ensure_ascii=False))

    idxr, proc = C.cargar_referencia()
    pr("\n   referencia de MIROVA usada para el cotejo:", json.dumps({k: {kk: v[kk] for kk in ("sha_commit", "fecha_commit", "sha256")}
                                                                    for k, v in proc.items() if k.endswith(".csv")}))
    for c in cambios:
        c["mirova_hoy"] = [{k: x[k] for k in ("source", "tipo", "vrp_mw", "dist_km")}
                           for x in C.parear(idxr, c["volcan"], "MODIS", c["hora"])]
        pr("      ", c["id"], c["volcan"], c["hora"], "MIROVA hoy:", c["mirova_hoy"])
    casos_cot = [{"volcan": f["volcan"], "hora": f["hora"], "clase": f["clase"], "d": f["d"]} for f in con]
    det = C.cotejo(casos_cot, idxr, "MODIS", C.CELDA_KM["MODIS"], pr, "MODIS")

    C.TEMP.mkdir(parents=True, exist_ok=True)
    (C.TEMP / "modis.json").write_text(json.dumps({"resumen": res, "cambios": cambios, "cotejo": det,
                                                   "sin_dato": dict(sin), "n_evaluadas": len(filas)},
                                                  ensure_ascii=False, indent=1), encoding="utf-8")
    (C.AQUI / "modis_cambios.json").write_text(json.dumps({"resumen": res, "cambios": cambios},
                                                          ensure_ascii=False, indent=1), encoding="utf-8")
    pr(f"\nlisto en {time.time() - t0:.0f} s")
    (C.AQUI / "modis_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
