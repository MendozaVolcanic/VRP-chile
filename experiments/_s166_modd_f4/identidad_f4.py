# -*- coding: utf-8 -*-
"""S168, candado de MOD-D fase 4 (PREREGISTRO_MODD_F4.md §8.2 y §11 punto 3): IDENTIDAD de punta a punta.

POR QUÉ. La fase 3 probó que la vía de pipeline/ reproduce al port del censo sobre las grillas que guardó el censo, pero
no pudo probar el camino desde el HDF (pyhdf no corre en Windows y el censo no guardó los gránulos). Este script mide
justo eso: en cada pasada de C con grilla del censo (las 5.321 marcadas `grilla_censo` en poblacion_f4.json), corre la
vía (`procesar_grilla` de pipeline/mirova_v750_codigo.py, sin modificarla, familia MODIS) sobre la grilla 51 x 51 del
censo (V-grilla) y la compara con lo que dejó el runner para esa pasada, que leyó el L1B y el MxD03 con las funciones
de producción. Si la lectura o el remuestreo del runner difieren de los del censo, la máscara, el VRP o la clase
cambian y el control queda en rojo.

V-grilla usa los mismos argumentos que calcular_vrp_granulo: la grilla de grillas_mirova.yaml (roi_modis), la caja
caja_roi(roi, celda del cráter, inner), la posición fraccionaria del cráter (get_detection_anchor del volcán como lo
carga run_pipeline), el inner_radius_km y el sensor; dayflag y sunglint son los que registró el censo para su grilla.
La grilla del censo está en float32 (así la guardó el probe); se pasa a float64 como hicieron la fase 3 y S165.

FORMATO DEL RUNNER. probe_f4.py (S168) guarda grillas/grilla_<vol>_<AAAAMMDDHHMM>.npz con mir, tir, box, pos_crater,
mascara, vrp_mw, dayflag, sunglint, inner_km, epsg, ul_x, ul_y, paso y n, SIN distance_class, y en la fila del jsonl
l1b_usado, geo_usado y otro_granulo. Este script lee ese formato: la clase del runner sale de re-correr la vía sobre
la grilla del runner (no la guarda el npz), y box y pos_crater se cotejan con los de este script (box_igual,
pos_crater_igual). El formato que sigue, escrito antes de que existiera probe_f4.py, también se acepta:
  <art>/**/grilla_<vol>_<AAAAMMDDHHMM>.npz, uno por pasada en que la vía corrió, con
    mir, tir         (51, 51) float64: la radiancia MIR y TIR remuestreada que recibió procesar_grilla (m13g, m15g)
    mascara          (51, 51) bool: las celdas alertadas del record que devolvió procesar_grilla (fila, col de
                     anomaly_pixels)
    vrp_mw           escalar: record["vrp_mw"] que devolvió procesar_grilla, ANTES de store.append_record
    distance_class   str: la del mismo record ("" si None)
    dayflag, sunglint  escalares que recibió procesar_grilla
    l1b, geo         str: nombre del L1B y del MxD03 que leyó el runner
  y en <art>/**/f4_parte*.jsonl, la fila tipo "record" de la pasada (vol, dt): `otro_granulo` (bool: el arnés no pudo
  pedir por nombre el archivo del censo y bajó el vigente), `motivo` y `estado`; si trae `l1b` y `geo`, mandan sobre
  los del npz; `v_slim` informa (record de V después de store).
POR QUÉ se compara contra el record de procesar_grilla y no contra el de store: el censo nunca pasó por store, y store
puede reescribir campos de un record (vrp, clase) por caminos que no son la lectura del gránulo; la identidad mide la
lectura. Lo que hace store con V se informa aparte (`v_slim_vrp_igual`).

Salida identidad.json: `pasadas` = [{vol, dt, mismo_granulo, misma_mascara, dvrp, misma_clase, max_dif_radiancia,
...diagnósticos}], que es lo que lee evaluar_f4.control_identidad. Una pasada con grilla del censo que el runner sacó
por un motivo sellado (sin grilla del runner) va con misma_mascara False y dvrp None: el evaluador la cuenta como otro
gránulo si mismo_granulo es False y, si no, en rojo (N-01). Una pasada sin nada del runner no se escribe (el evaluador
la cuenta como faltante) y se lista en `sin_runner`.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si la lectura del runner difiriera de la del censo, ¿se vería? Sí: probar_identidad_f4.py arma un runner con una
   celda cambiada y otro con otro gránulo, y control_identidad del evaluador sale en rojo en los dos.
2. Si el runner guardara una captura incoherente (máscara de un record, grilla de otro), ¿se vería? Sí: además de
   comparar con V-grilla, se re-corre procesar_grilla sobre la grilla del runner (`captura_coherente`).

Uso: python identidad_f4.py --art DIR [--poblacion poblacion_f4.json] [--salida identidad.json]
     [--censo D:/vrp-trabajo/temporales/s162_modd/censo] [--solo N]
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

CENSO = Path("D:/vrp-trabajo/temporales/s162_modd/censo")
FAM = MV.FAMILIAS["MODIS"]


def nombre_npz(vol, dt):
    return f"grilla_{vol}_{dt.replace('-', '').replace(' ', '').replace(':', '')}.npz"


# ------------------------------------------------------------------ volcán, grilla y caja (como calcular_vrp_granulo)
_VOL = {}


def contexto(vol):
    """grilla, caja, posición del cráter e inner del volcán, con los argumentos que usa la vía en producción."""
    if vol not in _VOL:
        import run_pipeline as rp
        v = rp.load_volcanoes(vol)[0]
        nombre = MV.volcan_por_coordenadas(v["lat"], v["lon"])
        g = MV.grilla_del_volcan(nombre, paso_m=FAM["paso_m"], clave_roi=FAM["clave_roi"])
        la, lo = get_detection_anchor(v)
        inner = v.get("inner_radius_km")
        box = MV.caja_roi(g.get("roi", "def"), n=g["n"], celda_crater=MV.celda_de(g, la, lo), inner_km=inner,
                          lado_sensible=FAM["lado_sensible"], lado_anillo=FAM["lado_anillo"], paso_m=g["paso"])
        _VOL[vol] = {"g": g, "box": box, "pos": MV.posicion_de(g, la, lo), "inner": inner, "nombre": nombre}
    return _VOL[vol]


def mascara_de(rec, n):
    m = np.zeros((n, n), bool)
    for p in rec.get("anomaly_pixels") or []:
        m[p["fila"], p["col"]] = True
    return m


def via(mir, tir, vol, dayflag, sunglint, sensor):
    c = contexto(vol)
    return MV.procesar_grilla(np.asarray(mir, np.float64), np.asarray(tir, np.float64), c["g"], c["box"], dayflag,
                              sunglint, c["pos"], c["inner"], sensor, familia="MODIS")


def vrp_de(rec):
    return float(rec.get("vrp_mw") or 0.0)


# ------------------------------------------------------------------ censo y runner
def leer_censo_ab(censo):
    out = {}
    for a in sorted(glob.glob(str(Path(censo) / "run_*" / "*" / "ab_parte*.jsonl"))):
        for x in open(a, encoding="utf-8"):
            r = json.loads(x)
            if r.get("tipo") == "record":
                out[r["id"]] = {"dayflag": r.get("dayflag"), "sunglint": r.get("sunglint"), "sensor": r.get("sensor"),
                                "vol": r["vol"], "dt": r["dt"]}
    return out


def leer_runner(art):
    """{(vol, dt): {"npz": ruta o None, "fila": fila del jsonl o None}}."""
    out = collections.defaultdict(lambda: {"npz": None, "fila": None})
    for p in sorted(glob.glob(str(Path(art) / "**" / "f4_parte*.jsonl"), recursive=True)):
        for x in open(p, encoding="utf-8"):
            r = json.loads(x)
            if r.get("tipo") == "record":
                out[(r["vol"], r["dt"])]["fila"] = r
    por_nombre = {}
    for p in glob.glob(str(Path(art) / "**" / "grilla_*.npz"), recursive=True):
        n = Path(p).name
        if n in por_nombre:
            raise RuntimeError(f"grilla del runner repetida: {por_nombre[n]} y {p}")
        por_nombre[n] = p
    return out, por_nombre


def comparar(p, censo_ab, censo_dir, run):
    """Una entrada de identidad para la pasada p de la población (con grilla_censo)."""
    cab = censo_ab[p["id_censo"]]
    if (cab["vol"], cab["dt"]) != (p["vol"], p["dt"]):
        raise RuntimeError(f"id_censo {p['id_censo']} no es la pasada {p['vol']} {p['dt']}")
    fila = run["fila"] or {}
    z = np.load(run["npz"]) if run["npz"] else None
    # probe_f4.py escribe l1b_usado y geo_usado en la fila; se aceptan también l1b y geo (en la fila o en el npz)
    l1b = fila.get("l1b_usado") or fila.get("l1b") or (str(z["l1b"]) if z is not None and "l1b" in z.files else None)
    geo = fila.get("geo_usado") or fila.get("geo") or (str(z["geo"]) if z is not None and "geo" in z.files else None)
    mismo = bool(l1b == p["l1b"] and geo == p["geo"] and not fila.get("otro_granulo"))
    e = {"vol": p["vol"], "dt": p["dt"], "mismo_granulo": mismo, "l1b_runner": l1b, "geo_runner": geo,
         "otro_granulo_declarado": bool(fila.get("otro_granulo")), "motivo_runner": fila.get("motivo"),
         "estado_runner": fila.get("estado")}
    if z is None:
        e.update({"misma_mascara": False, "dvrp": None, "misma_clase": False, "max_dif_radiancia": None,
                  "sin_grilla_del_runner": True})
        return e
    zc = np.load(Path(censo_dir) / p["grilla_censo"])
    mir_c, tir_c = zc["mir"].astype(np.float64), zc["tir"].astype(np.float64)
    vg = via(mir_c, tir_c, p["vol"], cab["dayflag"], cab["sunglint"], cab["sensor"])
    n = mir_c.shape[0]
    mask_g = mascara_de(vg, n)
    mir_r, tir_r = np.asarray(z["mir"], np.float64), np.asarray(z["tir"], np.float64)
    mask_r = np.asarray(z["mascara"], bool)
    vrp_r = float(z["vrp_mw"])
    vrp_nan = math.isnan(vrp_r)
    vrp_r = 0.0 if vrp_nan else vrp_r
    df_r = z["dayflag"].item() if "dayflag" in z.files else cab["dayflag"]
    sg_r = float(z["sunglint"]) if "sunglint" in z.files else cab["sunglint"]
    # la vía sobre la grilla del runner, con la geometría que recibió el runner: da la clase del runner cuando el npz
    # no la trae (probe_f4.py no la guarda) y la coherencia de la captura (máscara y VRP)
    vr = via(mir_r, tir_r, p["vol"], df_r, sg_r, cab["sensor"])
    dc_npz = (str(z["distance_class"]) or None) if "distance_class" in z.files else None
    dc_r = dc_npz if "distance_class" in z.files else vr.get("distance_class")
    dif, n_nan = [], 0
    for a, b in ((mir_r, mir_c), (tir_r, tir_c)):
        if a.shape != b.shape:
            n_nan = -1
            continue
        fin = np.isfinite(a) & np.isfinite(b)
        n_nan += int((np.isnan(a) != np.isnan(b)).sum())
        if fin.any():
            dif.append(float(np.max(np.abs(a[fin] - b[fin]))))
    misma_m = bool(mask_r.shape == mask_g.shape and np.array_equal(mask_r, mask_g))
    e.update({"misma_mascara": misma_m, "dvrp": round(vrp_r - vrp_de(vg), 6),
              "misma_clase": dc_r == vg.get("distance_class"),
              "max_dif_radiancia": max(dif) if dif else None, "n_nan_distinto": n_nan,
              "npix_runner": int(mask_r.sum()), "npix_grilla": int(mask_g.sum()),
              "vrp_runner": vrp_r, "vrp_grilla": vrp_de(vg), "dc_runner": dc_r, "dc_grilla": vg.get("distance_class"),
              "grilla_igual_float32": bool(mir_r.shape == zc["mir"].shape and
                                           np.array_equal(mir_r.astype(np.float32), zc["mir"], equal_nan=True) and
                                           np.array_equal(tir_r.astype(np.float32), zc["tir"], equal_nan=True)),
              "geom_distinta": (z["dayflag"].item() if "dayflag" in z.files else None) != cab["dayflag"] or
              ("sunglint" in z.files and not math.isclose(float(z["sunglint"]), float(cab["sunglint"]), abs_tol=0.01))})
    # coherencia de la captura: la vía sobre la grilla del runner tiene que dar lo que el runner dijo que dio
    e["vrp_runner_nan"] = vrp_nan
    e["clase_runner_de"] = "npz" if "distance_class" in z.files else "via_sobre_grilla_runner"
    c = contexto(p["vol"])
    if "box" in z.files:
        e["box_igual"] = bool(np.array_equal(np.asarray(z["box"], float), np.asarray(c["box"], float)))
    if "pos_crater" in z.files:
        e["pos_crater_igual"] = bool(np.allclose(np.asarray(z["pos_crater"], float), np.asarray(c["pos"], float),
                                                 atol=1e-9))
    e["captura_coherente"] = bool(np.array_equal(mascara_de(vr, n), mask_r) and abs(vrp_de(vr) - vrp_r) <= 1e-9
                                  and vr.get("distance_class") == dc_r)
    if not (misma_m and abs(e["dvrp"]) <= 1e-3 and e["misma_clase"]):
        # diagnóstico: ¿la diferencia es sólo la precisión float32 con que el censo guardó su grilla?
        v32 = via(mir_r.astype(np.float32), tir_r.astype(np.float32), p["vol"], cab["dayflag"], cab["sunglint"],
                  cab["sensor"])
        e["con_grilla_runner_en_float32"] = {"misma_mascara": bool(np.array_equal(mascara_de(v32, n), mask_g)),
                                             "dvrp": round(vrp_de(v32) - vrp_de(vg), 6),
                                             "misma_clase": v32.get("distance_class") == vg.get("distance_class")}
    vs = fila.get("v_slim")
    if isinstance(vs, dict):
        e["v_slim_vrp_igual"] = vs.get("vrp_mw") == round(vrp_r, 3) or vs.get("vrp_mw") == vrp_r
        e["v_slim_dc_igual"] = vs.get("distance_class") == dc_r
    return e


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True)
    ap.add_argument("--poblacion", default=str(AQUI / "poblacion_f4.json"))
    ap.add_argument("--salida", default=str(AQUI / "identidad.json"))
    ap.add_argument("--censo", default=str(CENSO))
    ap.add_argument("--solo", type=int, default=0, help="sólo las primeras N pasadas con grilla (prueba)")
    a = ap.parse_args(argv)
    t0 = time.time()
    pob = json.load(open(a.poblacion, encoding="utf-8"))
    con = [p for p in pob["pasadas"] if p.get("grilla_censo")]
    if a.solo:
        con = con[: a.solo]
    censo_ab = leer_censo_ab(a.censo)
    runner, npz = leer_runner(a.art)
    pasadas, sin_runner = [], []
    for p in con:
        k = (p["vol"], p["dt"])
        r = runner.get(k) or {"npz": None, "fila": None}
        r = {"npz": npz.get(nombre_npz(*k)), "fila": r["fila"]}
        if r["npz"] is None and r["fila"] is None:
            sin_runner.append(list(k))
            continue
        pasadas.append(comparar(p, censo_ab, a.censo, r))
    def igual(e):
        return bool(e["mismo_granulo"] and e["misma_mascara"] and e["dvrp"] is not None and abs(e["dvrp"]) <= 1e-3
                    and e["misma_clase"])
    ok = [e for e in pasadas if igual(e)]
    res = {"n_con_grilla_en_poblacion": len(con), "n_comparadas": len(pasadas), "n_sin_runner": len(sin_runner),
           "n_iguales": len(ok), "n_otro_granulo": sum(1 for e in pasadas if not e["mismo_granulo"]),
           "n_distintas_mismo_granulo": sum(1 for e in pasadas if e["mismo_granulo"] and not igual(e)),
           "n_sin_grilla_del_runner": sum(1 for e in pasadas if e.get("sin_grilla_del_runner")),
           "n_captura_incoherente": sum(1 for e in pasadas if e.get("captura_coherente") is False),
           "n_grilla_igual_float32": sum(1 for e in pasadas if e.get("grilla_igual_float32")),
           "max_dif_radiancia": max((e["max_dif_radiancia"] for e in pasadas if e.get("max_dif_radiancia") is not None),
                                    default=None),
           "segundos": round(time.time() - t0, 1)}
    print("identidad_f4:", json.dumps(res, ensure_ascii=False))
    for e in pasadas:
        if not igual(e):
            print("  distinta u otro gránulo:", json.dumps(e, ensure_ascii=False, default=str)[:400])
    out = {"poblacion": a.poblacion, "art": a.art, "censo": a.censo, "resumen": res, "pasadas": pasadas,
           "sin_runner": sin_runner}
    Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=0, default=str), encoding="utf-8")
    print("escrito", a.salida)
    return out


if __name__ == "__main__":
    main()
