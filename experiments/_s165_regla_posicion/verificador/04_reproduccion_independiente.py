# -*- coding: utf-8 -*-
"""Verificador S165 (regla de posición), 4: reproducción independiente del conteo de cambios en los tres sensores.
Sólo lectura; el almacén temporal va a D:\\vrp-trabajo\\temporales\\s165_regla_posicion_verif.

QUÉ HACE DISTINTO. Las reglas se calculan con código propio (scipy.ndimage.label con estructura 3 x 3 para el cúmulo
8-conexo del píxel más radiante; centroide y mínimo con numpy), no con comun.reglas ni con _cumulo_del_mas_radiante.
Se cotejan con comun.reglas y con el record de procesar_grilla (donde hay grilla) pasada por pasada. La publicación
sigue por la misma cadena del informe (comun.variante -> store.append_record -> predicado con node), que 03 ya
mostró capaz de dar las dos direcciones. Además cuenta los CRUCES del inner (una regla dentro y la otra fuera) sin
importar la publicación, y los cruces que NO cambian la publicación, para ver si el predicado esconde alguno.
Uso: python 04_reproduccion_independiente.py  (escribe 04_reproduccion_independiente_salida.txt y el detalle en
D:\\vrp-trabajo\\temporales\\s165_regla_posicion_verif\\04_detalle.json)
"""
import collections
import glob
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(AQUI.parent))
import comun as C  # noqa: E402
import banco_paridad as B  # noqa: E402

TEMPV = Path(r"D:\vrp-trabajo\temporales\s165_regla_posicion_verif")
TEMPV.mkdir(parents=True, exist_ok=True)
C.TEMP = TEMPV
MV = C.MV
L = []


def pr(*x):
    s = " ".join(str(v) for v in x)
    L.append(s)
    print(s, flush=True)


def reglas_propias(celdas, rad, n, pos_crater, pos_ref, paso_km):
    """Independiente de comun.reglas: ndimage.label 8-conexo, semilla = argmax de la radiancia."""
    m = np.zeros((n, n), bool)
    r = np.full((n, n), -np.inf)
    for (f, c), v in zip(celdas, rad):
        m[f, c] = True
        r[f, c] = v
    lab, _ = ndimage.label(m, structure=np.ones((3, 3), int))
    semilla = np.unravel_index(np.argmax(np.where(m, r, -np.inf)), r.shape)
    cu = np.argwhere(lab == lab[semilla])
    cen = cu.mean(axis=0)
    P = np.array(celdas, float)

    def d(p, q):
        return float(np.hypot(p[0] - q[0], p[1] - q[1]) * paso_km)
    return {"via": d(cen, pos_crater), "via_ref": d(cen, pos_ref),
            "cerc_cr": float(np.min(np.hypot(P[:, 0] - pos_crater[0], P[:, 1] - pos_crater[1]) * paso_km)),
            "cerc_ref": float(np.min(np.hypot(P[:, 0] - pos_ref[0], P[:, 1] - pos_ref[1]) * paso_km)),
            "n_cumulo": int(len(cu))}


def evaluar(sensor, filas, V, inner_html, celda_km):
    """filas: [{id, volcan, hora, clase, celdas, rad, g, pos, ref, rec_via (o None), vrp}] -> conteos."""
    con = [f for f in filas if f["celdas"]]
    pr(f"\n== {sensor}: {len(filas)} pasadas evaluadas, {len(con)} con alertados; por clase",
       dict(collections.Counter(f["clase"] for f in filas)))
    dif_comun, dif_rec = 0, 0
    for f in con:
        v = V[f["volcan"]]
        inner = v["inner_radius_km"]
        g = f["g"]
        paso_km = g["paso"] / 1000.0
        mine = reglas_propias(f["celdas"], f["rad"], g["n"], f["pos"], f["ref"], paso_km)
        suyo = C.reglas(f["celdas"], f["rad"], g["n"], f["pos"], f["ref"], paso_km)
        if any(abs(mine[k] - suyo[k]) > 1e-6 for k in ("via", "via_ref", "cerc_cr", "cerc_ref")) or mine["n_cumulo"] != suyo["n_cumulo"]:
            dif_comun += 1
        f["d"] = mine
        if f["rec_via"] is None:
            f["rec_via"] = C.record_desde_pixeles(f["celdas"], f["rad"], g, f["pos"], inner, f["sensor_label"],
                                                  f["vrp"], f["lam"])
        else:
            if abs(f["rec_via"]["primary_cluster"]["centroid_dist_km"] - mine["via"]) > 6e-4 or \
                    f["rec_via"]["distance_class"] != C.clase_dc(mine["via"], inner):
                dif_rec += 1
        f["cruce"] = {k: (mine["via"] <= inner) != (mine[k] <= inner) for k in ("cerc_cr", "cerc_ref")}
        f["calla_geom"] = {k: (mine["via"] <= inner) and not (mine[k] <= inner) for k in ("cerc_cr", "cerc_ref")}
        f["_rec"] = {"via": f["rec_via"], "cerc_cr": C.variante(f["rec_via"], mine["cerc_cr"], inner),
                     "cerc_ref": C.variante(f["rec_via"], mine["cerc_ref"], inner)}
    pr(f"   reglas propias contra comun.reglas: difieren en {dif_comun} de {len(con)}; contra el record de "
       f"procesar_grilla (donde hay grilla): difieren en {dif_rec}")
    casos, idx = [], []
    for n, f in enumerate(con):
        v = V[f["volcan"]]
        for regla, rr in f["_rec"].items():
            st = C.por_el_almacen(rr, f["volcan"], v, f["hora"])
            casos.append((st, inner_html[f["volcan"]]))
            idx.append((n, regla))
    P = C.publicar(casos)
    for (n, regla), p in zip(idx, P):
        con[n][f"pub_{regla}"] = p
    for f in filas:
        if not f["celdas"]:
            f.update({"pub_via": False, "pub_cerc_cr": False, "pub_cerc_ref": False})
    res = C.resumen_cambios(filas, pr, sensor)
    cambios = sorted({f["id"] for f in con if f["pub_via"] != f["pub_cerc_cr"] or f["pub_via"] != f["pub_cerc_ref"]})
    pr("   ids que cambian:", cambios)
    for k in ("cerc_cr", "cerc_ref"):
        cr = [f for f in con if f["cruce"][k]]
        sin_cambio = [f for f in cr if f["pub_via"] == f[f"pub_{k}"]]
        pr(f"   cruces del inner con {k} (sin mirar la publicación): {len(cr)}; de ellos sin cambio de publicación: "
           f"{len(sin_cambio)}; geometría «calla» (vía dentro, {k} fuera): {sum(f['calla_geom'][k] for f in con)}")
        for f in sin_cambio:
            pr(f"      cruce sin cambio: {f['id']} {f['volcan']} {f['hora']} clase {f['clase']} vrp {f['vrp']} "
               f"npix {len(f['celdas'])} via {f['d']['via']:.3f} {k} {f['d'][k]:.3f} pub_via {f['pub_via']} "
               f"pub_{k} {f[f'pub_{k}']}")
    det = [{k: f[k] for k in ("id", "volcan", "hora", "clase", "vrp", "pub_via", "pub_cerc_cr", "pub_cerc_ref",
                              "cruce", "d")} | {"npix": len(f["celdas"])} for f in con]
    return {"resumen": res, "cambios": cambios, "detalle": det, "n": len(filas), "n_con": len(con)}


def modis(V, inner_html):
    CENSO = r"D:\vrp-trabajo\temporales\s162_modd\censo"
    LAB = {"protegida": "protegida", "bajo1": "bajo1", "neg_limpio": "neg_limpio"}
    grillas = json.loads(subprocess.run(["git", "-C", str(RAIZ), "show",
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
    pr(f"\n== MODIS: censo {len(recs)} records, {len(npz)} grillas; por lab",
       dict(collections.Counter(r["lab"] for r in recs)))
    sin = collections.Counter()
    cfg = MV.FAMILIAS["MODIS"]
    filas = []
    for r in sorted(recs, key=lambda r: r["id"]):
        if r["estado"] != "ok" or r.get("port_estado") != "ok" or not r.get("port") or r["id"] not in npz:
            sin[(r["lab"], r["estado"], r.get("port_estado"))] += 1
            continue
        z = np.load(npz[r["id"]])
        mir, tir = z["mir"].astype(np.float64), z["tir"].astype(np.float64)
        v = V[r["vol"]]
        g = MV.grilla_del_volcan(r["vol"], paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
        gt = grillas[r["vol"]]
        la, lo = C.get_detection_anchor(v)
        pos = MV.posicion_de(g, la, lo)
        ref = ((g["ul_y"] - gt["Y0"]) / g["paso"] - 0.5, (gt["X0"] - g["ul_x"]) / g["paso"] - 0.5)
        box = MV.caja_roi(g.get("roi", "def"), n=g["n"], celda_crater=MV.celda_de(g, la, lo),
                          inner_km=v["inner_radius_km"], lado_sensible=cfg["lado_sensible"],
                          lado_anillo=cfg["lado_anillo"], paso_m=g["paso"])
        rec = MV.procesar_grilla(mir, tir, g, box, r["dayflag"], r["sunglint"], pos, v["inner_radius_km"],
                                 r["sensor"], familia="MODIS")
        celdas = [(p["fila"], p["col"]) for p in rec["anomaly_pixels"]]
        filas.append({"id": r["id"], "volcan": r["vol"], "hora": r["dt"], "clase": LAB.get(r["lab"], "resto"),
                      "celdas": celdas, "rad": [mir[c] for c in celdas], "g": g, "pos": pos, "ref": ref,
                      "rec_via": rec if celdas else None, "vrp": rec["vrp_mw"], "sensor_label": r["sensor"],
                      "lam": cfg["lam_mir"]})
    pr("   SIN DATO (lab, estado, port_estado):", dict(sin))
    return evaluar("MODIS", filas, V, inner_html, 1.0)


def v750(V, inner_html):
    OBJ = RAIZ / "experiments/_s159/oraculo_censo/objetivos.json"
    ART = [Path(r"D:\vrp-trabajo\temporales\s159_oraculo\censo_39713438252"),
           Path(r"D:\vrp-trabajo\temporales\s159_oraculo\rescate_39715348772")]
    obj = {o["id"]: o for o in json.loads(OBJ.read_text(encoding="utf-8"))}
    res = {}
    for d in ART:
        for f in sorted(Path(d).rglob("resultados_*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                if r.get("estado") == "ok" or r["id"] not in res:
                    res[r["id"]] = r
    lam = MV.FAMILIAS["VIIRS750"]["lam_mir"]
    filas, sin = [], collections.Counter()
    cajas = collections.Counter()
    for i in sorted(obj):
        o, r = obj[i], res.get(i)
        if r is None or r.get("estado") != "ok":
            sin[(o["lab"], (r or {}).get("estado", "sin_resultado"))] += 1
            continue
        cajas[tuple(sorted((r.get("oraculo") or {}).keys()))] += 1
        p = (r.get("oraculo") or {}).get("geo_linear")
        if p is None:
            sin[(o["lab"], "sin_geo_linear")] += 1
            continue
        v = V[o["volcan"]]
        g = MV.grilla_del_volcan(o["volcan"])
        la, lo = C.get_detection_anchor(v)
        pos = MV.posicion_de(g, la, lo)
        celdas = [(q[0], q[1]) for q in p["pixeles"]] if p.get("npix") else []
        clase = ("protegida" if o["protegida"] else "bajo1") if o["lab"] == "pos" else (
            "neg_limpio" if o["lab"] == "neg_limpio" else "resto")
        filas.append({"id": i, "volcan": o["volcan"], "hora": o["hora_utc"], "clase": clase, "celdas": celdas,
                      "rad": [q[4] for q in p["pixeles"]] if celdas else [], "g": g, "pos": pos, "ref": (33.0, 33.0),
                      "rec_via": None, "vrp": p.get("vrp_mw"), "sensor_label": o["sensor"], "lam": lam})
    pr("\n== VIIRS 750: cajas guardadas por el oráculo:", dict(cajas))
    pr("   SIN DATO (lab, estado):", dict(sin))
    return evaluar("VIIRS 750", filas, V, inner_html, 0.75)


def v375(V, inner_html):
    sys.path.insert(0, str(RAIZ / "experiments/_s162_v375"))
    import evaluar as E
    V375 = RAIZ / "experiments/_s162_v375"
    ART = {"S162": Path(r"C:\vrp-trabajo\temporales\s162_v375\run_40116289866"),
           "S162b": Path(r"C:\vrp-trabajo\temporales\s162_v375\run_40131572769"),
           "S159": Path(r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945")}
    CLASE = {"pos_prot": "protegida", "pos_bajo": "bajo1", "neg_pub": "neg_limpio", "neg_resto": "neg_limpio"}
    obj = {}
    for o in json.loads((V375 / "objetivos_v375_bc.json").read_text(encoding="utf-8"))["pasadas"]:
        obj[o["id"]] = dict(o)
    for o in json.loads((V375 / "b2/objetivos_v375_b2.json").read_text(encoding="utf-8"))["pasadas"]:
        obj[o["id"]] = dict(o)
    for o in json.loads((RAIZ / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8")):
        if o["b"] == "VIIRS375" and o["hora_utc"][:10] not in E.EXCLUIDOS:
            obj[o["id"]] = {**o, "lote": "S159"}
    res = {}
    for lote, art in ART.items():
        for i, r in E.leer_resultados(art).items():
            if i in obj and obj[i]["lote"] == lote:
                res[i] = r
    cfg = MV.FAMILIAS["VIIRS375"]
    filas, sin = [], collections.Counter()
    t0 = time.time()
    for k, i in enumerate(sorted(obj)):
        o, r = obj[i], res.get(i)
        if r is None or r.get("estado") != "ok":
            sin[(o.get("clase"), (r or {}).get("estado", "sin_resultado"))] += 1
            continue
        gz = E.grilla_npz(ART[o["lote"]], i)
        if gz is None:
            sin[(o.get("clase"), "sin_grilla")] += 1
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
        filas.append({"id": i, "volcan": o["volcan"], "hora": o["hora_utc"], "clase": CLASE.get(o.get("clase"), "resto"),
                      "celdas": celdas, "rad": [mir[c] for c in celdas], "g": g, "pos": pos, "ref": ref,
                      "rec_via": rec if celdas else None, "vrp": rec["vrp_mw"], "sensor_label": o["sensor"],
                      "lam": cfg["lam_mir"]})
        if (k + 1) % 400 == 0:
            print(f"   ... {k + 1} de {len(obj)} ({time.time() - t0:.0f} s)", flush=True)
    pr("\n== VIIRS 375: pipeline/ de main (familia VIIRS375 y caja_v375 ya en origin/main tras #921)")
    pr("   SIN DATO (clase, estado):", dict(sin))
    return evaluar("VIIRS 375", filas, V, inner_html, 0.375)


def main():
    t0 = time.time()
    pr("== procedencia:", json.dumps(C.procedencia_codigo()))
    pr("   regla importada igual a origin/main:", json.dumps(C.misma_regla_que_main()))
    V = C.volcanes()
    inner_html = B.inner_desde_html()
    out = {}
    for nombre, fn in (("modis", modis), ("v750", v750), ("v375", v375)):
        try:
            out[nombre] = fn(V, inner_html)
        except Exception as e:                      # se informa y se sigue con el siguiente sensor
            import traceback
            pr(f"   ERROR en {nombre}: {e!r}")
            pr(traceback.format_exc())
    (TEMPV / "04_detalle.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    pr(f"\nlisto en {time.time() - t0:.0f} s")
    (AQUI / "04_reproduccion_independiente_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
