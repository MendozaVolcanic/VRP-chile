# -*- coding: utf-8 -*-
"""S165, regla de posición «más radiante» contra «cercano»: piezas comunes a los tres sensores. Sólo lectura.

POR QUÉ. La vía «código MIROVA» (pipeline/mirova_v750_codigo.py, compartida por VIIRS 750, MODIS y VIIRS 375) ubica
el record en el cúmulo 8-conexo de la alertada MÁS RADIANTE y mide desde el cráter la distancia de su CENTROIDE; con
eso decide summit o far (procesar_grilla: `dc = "summit" if dcen <= inner_km else "far"`, frontera inclusiva). El
evaluador de V375 (experiments/_s162_v375/evaluar.py, REGLA_DECIDE = "cercano") usa en cambio la distancia del
alertado MÁS CERCANO al punto de referencia de MIROVA (X0, Y0). Cuando una escena tiene un píxel débil en el cráter y
una fuente más radiante lejos, las dos reglas publican distinto. Este módulo NO reimplementa la regla de la vía: la
selección del cúmulo es `_cumulo_del_mas_radiante` importada de pipeline/ (idéntica a origin/main; cada script lo
comprueba con git diff y lo imprime). Lo único escrito aquí son las tres líneas que procesar_grilla aplica después
(centroide, hipotenusa por el paso, `<=`), y cada script las coteja contra el record de procesar_grilla donde hay
grilla (MODIS, VIIRS 375).

Reglas medidas (todas sobre la MISMA máscara de alertados):
  via        centroide del cúmulo de la más radiante, desde el cráter (lo que hace la vía)
  cerc_cr    alertado más cercano, desde el cráter (la regla «cercano» puesta en la vía: sólo cambia la regla)
  cerc_ref   alertado más cercano, desde el punto de referencia del censo (lo que hace evaluar.py)
  via_ref    centroide del cúmulo de la más radiante, desde el punto de referencia (para el cotejo con MIROVA)
  pico_ref   la alertada más radiante, desde el punto de referencia (informa)
"""
from __future__ import annotations

import collections
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from bisect import bisect_left
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
TEMP = Path(r"D:\vrp-trabajo\temporales\s165_regla_posicion")
# VIIRS 375: la familia VIIRS375 y caja_v375 todavía no están en main (viven en el worktree de V375-E); v375.py pone
# S165_PIPELINE_RAIZ para importar ese pipeline/ y misma_regla_que_main() comprueba que la regla de posición sea la de main.
RAIZ_PIPELINE = Path(os.environ.get("S165_PIPELINE_RAIZ", str(RAIZ)))
for p in (RAIZ / "scripts", RAIZ_PIPELINE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

ARCHIVOS_MAIN = ("pipeline/mirova_v750_codigo.py", "pipeline/geo_utils.py", "pipeline/store.py",
                 "pipeline/grillas_mirova.yaml", "volcanoes.yaml", "frontend/index.html", "scripts/banco_paridad.py",
                 "scripts/clase_mirova.py", "scripts/referencia_mirova_unificada.py")
CELDA_KM = {"MODIS": 1.0, "VIIRS750": 0.75, "VIIRS375": 0.375}
CLASES = ("protegida", "bajo1", "neg_limpio", "resto")


def procedencia_codigo():
    """sha de HEAD y de origin/main, y si los archivos importados difieren de origin/main (tiene que ser vacío)."""
    def g(*a):
        return subprocess.run(["git", "-C", str(RAIZ), *a], capture_output=True, text=True).stdout.strip()
    dif = g("diff", "--name-only", "origin/main", "--", *ARCHIVOS_MAIN)
    sucio = g("status", "--porcelain", "--", *ARCHIVOS_MAIN)
    return {"head": g("rev-parse", "HEAD"), "origin_main": g("rev-parse", "origin/main"),
            "difieren_de_origin_main": dif.split() if dif else [], "sin_commitear": sucio.split("\n") if sucio else []}


def misma_regla_que_main():
    """El texto de _cumulo_del_mas_radiante y procesar_grilla del módulo importado contra el de origin/main."""
    import ast
    import inspect
    src = subprocess.run(["git", "-C", str(RAIZ), "show", "origin/main:pipeline/mirova_v750_codigo.py"],
                         capture_output=True, text=True, encoding="utf-8").stdout
    arbol = ast.parse(src)
    out = {"modulo": MV.__file__}
    for nombre in ("_cumulo_del_mas_radiante", "procesar_grilla"):
        nodo = next(n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == nombre)
        de_main = ast.get_source_segment(src, nodo)
        out[nombre] = inspect.getsource(getattr(MV, nombre)).strip() == de_main.strip()
    return out


def volcanes():
    import yaml
    d = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
    return {v["name"]: v for v in d["volcanoes"]}


# ---------------------------------------------------------------- reglas sobre una máscara
def reglas(celdas, rad, n, pos_crater, pos_ref, paso_km):
    """celdas: [(fila, col)] alertadas; rad: radiancia MIR de cada una (mismo orden); n: lado de la grilla.
    Devuelve las distancias de las cinco reglas (km) y el cúmulo que elige la vía."""
    mascara = np.zeros((n, n), bool)
    m13 = np.zeros((n, n), float)
    for (f, c), L in zip(celdas, rad):
        mascara[f, c] = True
        m13[f, c] = L
    cu = MV._cumulo_del_mas_radiante(mascara, m13)          # la función de la vía, sin tocar
    fr, fc = float(np.mean([a for a, _ in cu])), float(np.mean([b for _, b in cu]))
    pico = max(cu, key=lambda p: m13[p])

    def d(a, b, ref):
        return float(np.hypot(a - ref[0], b - ref[1]) * paso_km)
    return {"via": d(fr, fc, pos_crater), "via_ref": d(fr, fc, pos_ref), "pico_ref": d(*pico, pos_ref),
            "cerc_cr": min(d(f, c, pos_crater) for f, c in celdas),
            "cerc_ref": min(d(f, c, pos_ref) for f, c in celdas),
            "n_cumulo": len(cu), "n_alertados": len(celdas), "centroide": [fr, fc], "pico": [int(pico[0]), int(pico[1])]}


def record_desde_pixeles(celdas, rad, g, pos_crater, inner, sensor, vrp_mw, lam_mir):
    """El record que armaría procesar_grilla a partir de una máscara ya conocida (para VIIRS 750, donde el censo guardó
    los alertados del oráculo pero no la grilla): mismos campos y mismas expresiones, con el VRP del oráculo y sin
    t_bg_k (el predicado no lo lee). modis.py y v375.py comprueban que, con el VRP de la vía, da el mismo record
    recortado (slim) que procesar_grilla."""
    n = g["n"]
    paso_km = float(g.get("paso", MV.PASO_V750_M)) / 1000.0
    mascara = np.zeros((n, n), bool)
    m13 = np.zeros((n, n), float)
    for (f, c), L in zip(celdas, rad):
        mascara[f, c] = True
        m13[f, c] = L
    cu = MV._cumulo_del_mas_radiante(mascara, m13)
    fr, fc = float(np.mean([a for a, _ in cu])), float(np.mean([b for _, b in cu]))
    dcen = float(np.hypot(fr - pos_crater[0], fc - pos_crater[1]) * paso_km)
    clat, clon = MV.latlon_de(g, fr, fc)
    pico = max(cu, key=lambda p: m13[p])
    plat, plon = MV.latlon_de(g, *pico)
    dpico = float(np.hypot(pico[0] - pos_crater[0], pico[1] - pos_crater[1]) * paso_km)
    t_max = float(MV.radiancia_a_temperatura(np.array([m13[pico]]), lam_mir)[0])
    pix = []
    for f, k in zip(*np.nonzero(mascara)):
        la, lo = MV.latlon_de(g, f, k)
        pix.append({"lat": round(la, 5), "lon": round(lo, 5),
                    "dist_km": round(float(np.hypot(f - pos_crater[0], k - pos_crater[1]) * paso_km), 2),
                    "bt_k": round(float(MV.radiancia_a_temperatura(np.array([m13[f, k]]), lam_mir)[0]), 2),
                    "fila": int(f), "col": int(k)})
    v = round(float(vrp_mw), 3)
    return {"sensor": sensor, "triggered_test1": False, "vrp_vent_mw": 0.0, "via_codigo_mirova": True,
            "n_anomalous_pixels": len(celdas), "vrp_mw": v, "t_max_k": round(t_max, 2),
            "distance_class": clase_dc(dcen, inner), "anomaly_pixels": pix, "t_bg_k": None,
            "primary_cluster": {"vrp_mw": v, "n_pixels": len(cu), "centroid_lat": round(clat, 5),
                                "centroid_lon": round(clon, 5), "centroid_dist_km": round(dcen, 3),
                                "single_pixel_mode": False},
            "hotspot_lat": round(plat, 5), "hotspot_lon": round(plon, 5), "hotspot_dist_km": round(dpico, 3),
            "final_hotspot_lat": round(clat, 5), "final_hotspot_lon": round(clon, 5),
            "final_hotspot_dist_km": round(dcen, 3), "final_hotspot_source": "codigo_mirova"}


def clase_dc(dist, inner):
    return "summit" if dist <= inner else "far"            # procesar_grilla: dcen <= inner_km


def variante(rec, dist, inner):
    """El record de la vía con la distancia de otra regla: sólo cambian distance_class, el centroide del cúmulo y el
    final_hotspot (el guard A46 de store y mirovaEqVrp del tablero leen pc.centroid_dist_km)."""
    r = copy.deepcopy(rec)
    if not r.get("primary_cluster"):
        return r
    r["distance_class"] = clase_dc(dist, inner)
    r["primary_cluster"]["centroid_dist_km"] = round(dist, 3)
    r["final_hotspot_dist_km"] = round(dist, 3)
    return r


def por_el_almacen(rec, nombre, v, dt):
    """Como en producción: store.append_record sobre un directorio temporal; devuelve el record que quedó escrito o
    None si el almacén no lo escribió."""
    from pipeline import store
    rec = json.loads(json.dumps(rec))
    rec["datetime_utc"] = dt
    rec.setdefault("product_version", "standard")
    tmp = Path(tempfile.mkdtemp(prefix="s165rp_", dir=str(TEMP)))
    viejo = store.DATA_DIR
    store.DATA_DIR = tmp
    try:
        store.append_record(nombre, rec, max_hotspot_dist_km=v.get("radius_km"),
                            enable_pixel_level_distance_filter=True, max_cluster_pixels=v.get("max_cluster_pixels"),
                            inner_radius_km=v.get("inner_radius_km"), overwrite=True)
        f = tmp / f"{nombre}.json"
        if not f.exists():
            return None
        recs = json.loads(f.read_text(encoding="utf-8"))["records"]
        return recs[-1] if recs else None
    finally:
        store.DATA_DIR = viejo
        for q in tmp.glob("*"):
            q.unlink()
        tmp.rmdir()


def slim(rec):
    import banco_paridad as B
    rec = rec or {}
    s = {k: rec.get(k) for k in B.CAMPOS_JS}
    if s.get("anomaly_pixels") is None:
        s["anomaly_pixels"] = []
    return s


def publicar(casos):
    """casos: [(record o None, inner)] -> [bool] con el predicado del tablero ejecutado con node."""
    import banco_paridad as B
    out = B.correr_node([[slim(r), inner] for r, inner in casos])
    return [bool(x[4]) for x in out]


def control_predicado():
    """Pregunta 2 del instrumento: el predicado tiene que cambiar con distance_class (si no, cualquier conteo de
    cambios da 0 por construcción). Un record summit a 1 km publica; el mismo far, no."""
    base = {"vrp_mw": 0.4, "distance_class": "summit", "t_max_k": 290, "sensor": "MODIS_AQUA",
            "triggered_test1": False, "primary_cluster": {"vrp_mw": 0.4, "centroid_dist_km": 1.0, "n_pixels": 2}}
    lejos = copy.deepcopy(base)
    lejos["distance_class"] = "far"
    lejos["primary_cluster"]["centroid_dist_km"] = 9.0
    return publicar([(base, 5.0), (lejos, 5.0)])


# ---------------------------------------------------------------- referencia de MIROVA (copia de hoy)
REF_DIR = TEMP / "ref"


def cargar_referencia():
    """La copia de hoy bajada por referencia.py (procedencia en ref/procedencia.json)."""
    from referencia_mirova_unificada import cargar_referencia_unificada
    proc = json.loads((REF_DIR / "procedencia.json").read_text(encoding="utf-8"))
    filas = cargar_referencia_unificada(REF_DIR / "registro_vrp_consolidado.csv", REF_DIR / "registro_vrp_ocr.csv")
    idx = collections.defaultdict(list)
    for f in filas:
        dt = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        idx[(f["volcano"], f["sensor_bucket"])].append((dt, f))
    for v in idx.values():
        v.sort(key=lambda x: x[0])
    return idx, proc


def parear(idx, volcan, bucket, hora, tol_s=None):
    from clase_mirova import VENTANA_S
    tol = VENTANA_S if tol_s is None else tol_s
    lst = idx.get((volcan, bucket), [])
    t = datetime.strptime(hora[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    ts = [x[0] for x in lst]
    i = bisect_left(ts, t - timedelta(seconds=tol + 60))
    out = []
    while i < len(lst) and lst[i][0] <= t + timedelta(seconds=tol + 60):
        dt = (lst[i][0] - t).total_seconds()
        if -tol <= dt <= tol + 59:          # la hora del censo viene truncada al minuto
            out.append(lst[i][1])
        i += 1
    return out


def cotejo(casos, idx, bucket, celda_km, pr, titulo):
    """casos: [{volcan, hora, clase, d: {regla: km}}]. Para cada par de reglas, sobre las pasadas donde las dos
    distancias difieren en más de una celda y MIROVA tiene fila con VRP > 0 y Distancia_km, cuenta cuál queda más
    cerca de la de MIROVA. Canal tabla (CONS) decide; OCR aparte. Devuelve el detalle."""
    pares = (("via_ref", "cerc_ref", "mismo punto de referencia (el del censo): sólo cambia la regla"),
             ("via", "cerc_ref", "como están implementadas: vía desde el cráter, cercano de evaluar.py desde X0, Y0"),
             ("pico_ref", "cerc_ref", "informa: la alertada más radiante contra la más cercana, desde la referencia"))
    det = {}
    pr(f"\n== {titulo}: cotejo con la Distancia_km de MIROVA (celda {celda_km} km)")
    for a, b, txt in pares:
        pr(f"   {a} contra {b} ({txt})")
        det[f"{a}|{b}"] = {}
        for canal in ("CONS", "OCR"):
            filas = []
            for c in casos:
                da, db = c["d"][a], c["d"][b]
                if abs(da - db) <= celda_km:
                    continue
                ref = [f for f in parear(idx, c["volcan"], bucket, c["hora"])
                       if f["source"] == canal and f["dist_km"] is not None and (f["vrp_mw"] or 0) > 0]
                for f in ref:
                    ea, eb = abs(da - f["dist_km"]), abs(db - f["dist_km"])
                    gana = a if ea < eb - 1e-9 else (b if eb < ea - 1e-9 else "empate")
                    filas.append({"volcan": c["volcan"], "hora": c["hora"], "clase": c["clase"], "tipo": f["tipo"],
                                  "vrp_mirova": f["vrp_mw"], "dist_mirova": f["dist_km"], a: round(da, 3),
                                  b: round(db, 3), "gana": gana, "dentro_media_celda": {
                                      a: ea <= celda_km / 2 + 1e-9, b: eb <= celda_km / 2 + 1e-9}})
            cnt = collections.Counter(x["gana"] for x in filas)
            alerta = [x for x in filas if x["tipo"].startswith("ALERTA")]
            cnt_al = collections.Counter(x["gana"] for x in alerta)
            n_pas = len({(x["volcan"], x["hora"]) for x in filas})
            pr(f"      canal {canal}{' (DECIDE)' if canal == 'CONS' else ' (informa)'}: {len(filas)} filas en {n_pas} "
               f"pasadas | más cerca de MIROVA: {a} {cnt[a]}, {b} {cnt[b]}, empate {cnt['empate']} | sólo filas "
               f"ALERTA: {a} {cnt_al[a]}, {b} {cnt_al[b]}, empate {cnt_al['empate']} (de {len(alerta)}) | a media "
               f"celda o menos: {a} {sum(x['dentro_media_celda'][a] for x in filas)}, "
               f"{b} {sum(x['dentro_media_celda'][b] for x in filas)}")
            for x in filas[:60]:
                pr("        ", json.dumps(x, ensure_ascii=False))
            det[f"{a}|{b}"][canal] = filas
    return det


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def resumen_cambios(filas, pr, etiqueta, reglas_=("cerc_cr", "cerc_ref")):
    """filas: [{clase, pub_via, pub_cerc_cr, pub_cerc_ref, ...}] -> tabla por clase y dirección."""
    out = {}
    for regla in reglas_:
        c = collections.Counter()
        for f in filas:
            if f["pub_via"] == f[f"pub_{regla}"]:
                continue
            c[(f["clase"], "publica_de_mas" if f[f"pub_{regla}"] else "calla")] += 1
        tot = sum(c.values())
        pr(f"   {etiqueta} | regla {regla}: cambian {tot} de {len(filas)}")
        for cl in CLASES:
            n_cl = sum(1 for f in filas if f["clase"] == cl)
            pr(f"      {cl:10s} (n {n_cl:5d}): con «cercano» publica y la vía no {c[(cl, 'publica_de_mas')]:3d} | "
               f"la vía publica y con «cercano» calla {c[(cl, 'calla')]:3d}")
        out[regla] = {f"{k[0]}|{k[1]}": v for k, v in c.items()}
        out[regla]["total"] = tot
    return out
