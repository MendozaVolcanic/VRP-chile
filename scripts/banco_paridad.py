# -*- coding: utf-8 -*-
"""Banco de paridad por pasada con negativos (Fase 0, tarea 3 del plan de paridad S139).

POR QUE. La brecha con MIROVA no es de recall: en 874 de 877 noches de volcan con alerta
publicamos algo. Es de SOBRE-PUBLICACION: en noches que MIROVA miro sin ver nada, VIIRS 375
publicaba en ~2 de cada 3 pasadas (S139, docs/audit_s139/VERIFICADOR.md). Para medir eso hacen
falta negativos, y el negativo mas limpio que existe es POR PASADA: si MIROVA listo ESE granule con
VRP 0, lo proceso y no vio nada; si nosotros publicamos ahi, la divergencia es de ese granule y no
de pasadas que la referencia se salto.

QUE MIDE, por sensor y por volcan, en dos unidades (la pasada y la noche de volcan, que es como el
operador vive una alerta, A94):
  * recall en positivos (pasadas con ALERTA de MIROVA, consolidado u OCR);
  * tasa de publicacion en negativos limpios (spec §3.1: granule MIROVA con VRP 0, nocturno, sin
    ALERTA ni FALSO_POSITIVO esa noche y sensor, con record nuestro a +-2 min). Se informa tambien
    la variante estricta del verificador S139 (sin ALERTA ni FP en la noche del volcan, cualquier
    sensor), para que el 63,5 % de S139 siga siendo comparable;
  * `far_ref` (pedido de Nicolas 2026-09-14): FALSO_POSITIVO de MIROVA = calor fuera del limite del
    volcan, sin informacion para el crater. Sirve de control positivo de nuestras `far`: si MIROVA
    vio un foco lejano y nosotros no, es una perdida real (incendio o foco excentrico).
"Publica" = predicado del dashboard EJECUTADO con node desde frontend/index.html (nunca portado),
con el sha de ese archivo en la salida. _mirova_confirmed = false siempre: la etiqueta no puede
entrar al predicado.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
  P1 (si lo medido estuviera roto, lo veria): controles todo_publica / nada_publica sobre el mismo
     denominador dan 1 y 0; el oraculo (campo = etiqueta) da AUC 1.
  P2 (instrumento muerto): identidad del predicado contra los casos del guard S139; barajar las
     etiquetas dentro de cada volcan lleva el AUC a 0,5 (media de 50 barajados; el AUC agrupado NO
     sirve de control porque mezcla volcanes con distinta tasa de positivos, Simpson); las pasadas sin
     fila de referencia van a `sin_info` y nunca al denominador.

ORIGEN. Funciones copiadas sin reescribir de experiments/_s139_audit/eje2/banco_noches.py (bucket,
inner_desde_html, _JS, correr_node, control_identidad_predicado, auc) y del verificador
v1_negativo_por_pasada.py (zbin; `parear` cambia: devuelve TODAS las filas de la ventana, no la mas
cercana, porque una misma pasada puede tener fila CONS y fila OCR). Esos scripts no se tocan: son el
registro historico.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

T0 = time.time()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada  # noqa: E402
from referencia_mirova_unificada import (RESPALDO_20260408, SNAP_CONS,  # noqa: E402
                                         SNAP_OCR, bajar_remoto,
                                         cargar_referencia_unificada)

DATA = ROOT / "data" / "mirova_equivalent"
HTML = ROOT / "frontend" / "index.html"
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
BUCKETS = ["MODIS", "VIIRS375", "VIIRS750"]
INICIO_DEFECTO = "2026-03-01"  # spec §7.5: cobertura CONS >= 99 % y OCR confiable desde marzo
TOL_S = 120
N_BARAJADOS = 50
N_MIN_AUC = 5


def bucket(sensor):
    s = sensor or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def inner_desde_html():
    """inner_radius_km por volcan leido de la lista VOLCANOES de frontend/index.html."""
    src = HTML.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r'name:\s*"(\w+)".*?inner_radius_km:\s*([\d.]+)', src):
        out.setdefault(m.group(1), float(m.group(2)))
    return {v: out[v] for v in VOLS}


# ---------------------------------------------------------------- predicado del operador (node)
_JS = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function extraer(nombre) {
  const i = src.indexOf('function ' + nombre + '(');
  if (i < 0) throw new Error('no encontre function ' + nombre);
  let j = src.indexOf('{', i), d = 0;
  for (let k = j; k < src.length; k++) {
    if (src[k] === '{') d++;
    else if (src[k] === '}') { d--; if (d === 0) return src.slice(i, k + 1); }
  }
  throw new Error('no cerro ' + nombre);
}
function constante(nombre) {
  const m = src.match(new RegExp('const ' + nombre + '\\s*=\\s*([^;]+);'));
  if (!m) throw new Error('no encontre const ' + nombre);
  return m[0];
}
let USE_F5_CORE = true;
const codigo = [constante('F5_R_CORE_KM'), constante('F5_BT_EXT_K')].concat(
  ['_havKm','mirovaEqVrp','f5CoreMagnitude','mirovaEqVrpCore','mirovaEqVrpDisplay',
   'isCirrusArtifact','isDiffuseFieldArtifact','isThermalArtifact','isValidDetection',
   'isSummitDetection'].map(extraer)).join('\n');
eval(codigo);
const casos = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const out = casos.map(([r, inner]) => {
  const summit = isSummitDetection(r), valid = isValidDetection(r);
  const art = isThermalArtifact(r, inner), disp = mirovaEqVrpDisplay(r, inner, false);
  return [summit ? 1 : 0, valid ? 1 : 0, art ? 1 : 0, disp,
          (summit && valid && !art && disp > 0) ? 1 : 0];
});
console.log(JSON.stringify(out));
"""

CAMPOS_JS = ["primary_cluster", "distance_class", "vrp_mw", "vrp_mir_mw", "discarded_reason",
             "triggered_test1", "vrp_vent_mw", "t_max_k", "sensor", "f5_core_vrp_mw",
             "anomaly_pixels"]


def correr_node(casos):
    tmp = tempfile.mkdtemp()
    try:
        runner, datos = os.path.join(tmp, "r.js"), os.path.join(tmp, "c.json")
        Path(runner).write_text(_JS, encoding="utf-8")
        Path(datos).write_text(json.dumps(casos), encoding="utf-8")
        o = subprocess.run(["node", "--max-old-space-size=4096", runner, str(HTML), datos],
                           capture_output=True, text=True, timeout=600)
        if o.returncode != 0:
            raise RuntimeError("node fallo: " + o.stderr[-1500:])
        return json.loads(o.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def control_identidad_predicado():
    """Los 5 casos del guard S139 con isValidDetection; y dos casos de publicacion."""
    c = [{"vrp_mw": 0.0, "triggered_test1": True, "primary_cluster": {"vrp_mw": 0.0}},
         {"vrp_mw": 0.3, "triggered_test1": False, "primary_cluster": {"vrp_mw": 0.3}},
         {"vrp_mw": 0.0, "triggered_test1": True, "primary_cluster": None},
         {"vrp_mw": 1.2, "triggered_test1": False},
         {"vrp_mw": 0.0, "triggered_test1": False, "primary_cluster": None},
         # publica: summit, cumulo 0,4 MW a 1 km, inner 5
         {"vrp_mw": 0.4, "distance_class": "summit", "t_max_k": 290, "sensor": "MODIS_AQUA",
          "primary_cluster": {"vrp_mw": 0.4, "centroid_dist_km": 1.0, "n_pixels": 2}},
         # no publica: far aunque el cumulo tenga energia a 1 km (el caso Lascar del orquestador)
         {"vrp_mw": 5.0, "distance_class": "far", "t_max_k": 290, "sensor": "MODIS_AQUA",
          "primary_cluster": {"vrp_mw": 0.4, "centroid_dist_km": 1.0, "n_pixels": 2}}]
    res = correr_node([[x, 5.0] for x in c])
    return [r[1] for r in res[:5]], [r[4] for r in res[5:]]


def auc(pos, neg):
    """Mann-Whitney con empates; None si falta una clase."""
    if not pos or not neg:
        return None
    allv = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    rank_sum, i = 0.0, 0
    while i < len(allv):
        j = i
        while j < len(allv) and allv[j][0] == allv[i][0]:
            j += 1
        r = (i + j + 1) / 2.0
        rank_sum += r * sum(1 for x in allv[i:j] if x[1] == 1)
        i = j
    return (rank_sum - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def zbin(z):
    if z is None:
        return "z?"
    return "z<30" if z < 30 else ("z30-50" if z < 50 else ("z50-60" if z < 60 else "z>=60"))


# ---------------------------------------------------------------- referencia
def es_alerta(tipo):
    return tipo.startswith("ALERTA")


def es_fp(tipo):
    return tipo.startswith("FALSO_POSITIVO")


def indexar_referencia(filas, coords, ventana):
    """Filas nocturnas en ventana, indexadas por (volcan, sensor) y resumidas por noche."""
    # A119 (S149): la referencia no tiene la misma calidad todo el ano. El aviso lo da el cargador,
    # no la memoria de nadie. Solo imprime a stderr; no cambia ninguna fila ni ninguna etiqueta.
    try:
        from calidad_referencia_mirova import avisar as _avisar_calidad
    except ImportError:
        from scripts.calidad_referencia_mirova import avisar as _avisar_calidad
    _avisar_calidad(ventana[0], ventana[1])
    por_vb = collections.defaultdict(list)
    noche_sensor = collections.defaultdict(lambda: {"alerta": False, "fp": False})
    noche_volcan = collections.defaultdict(lambda: {"alerta": False, "fp": False})
    n = 0
    for f in filas:
        noche = f["fecha_utc"][:10]
        if not (ventana[0] <= noche <= ventana[1]):
            continue
        dt = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        lat, lon = coords[f["volcano"]]
        if es_pasada_diurna_descartada(f["sensor_bucket"], lat, lon, dt):
            continue
        n += 1
        por_vb[(f["volcano"], f["sensor_bucket"])].append((dt, f))
        for d in (noche_sensor[(f["volcano"], f["sensor_bucket"], noche)], noche_volcan[(f["volcano"], noche)]):
            d["alerta"] |= es_alerta(f["tipo"])
            d["fp"] |= es_fp(f["tipo"])
    for v in por_vb.values():
        v.sort(key=lambda x: x[0])
    return por_vb, noche_sensor, noche_volcan, n


def parear(lista, t, tol=TOL_S):
    """Todas las filas de referencia a +-tol segundos de t (lista ordenada de (dt, fila))."""
    ts = [x[0] for x in lista]
    i = bisect.bisect_left(ts, t - timedelta(seconds=tol))
    out = []
    while i < len(lista) and lista[i][0] <= t + timedelta(seconds=tol):
        out.append(lista[i][1])
        i += 1
    return out


# ---------------------------------------------------------------- nuestros records
def cargar_nuestros(coords, inner, ventana):
    recs, casos = [], []
    for vol in VOLS:
        with open(DATA / f"{vol}.json", encoding="utf-8") as fh:
            d = json.load(fh)
        for r in d["records"]:
            b = bucket(r.get("sensor"))
            if b is None or not (ventana[0] <= r.get("datetime_utc", "")[:10] <= ventana[1]):
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            if es_pasada_diurna_descartada(b, lat, lon, dt):
                continue
            pc = r.get("primary_cluster") or {}
            recs.append({"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                         "dc": r.get("distance_class"), "pc_vrp": pc.get("vrp_mw"),
                         "pc_dist": pc.get("centroid_dist_km"), "z": r.get("sensor_zenith_deg")})
            slim = {k: r.get(k) for k in CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = correr_node(casos) if casos else []
    for rec, p in zip(recs, pred):
        rec["disp"], rec["pub"] = p[3], p[4]
    return recs


def etiquetar(recs, por_vb, noche_sensor, noche_volcan):
    """Etiqueta cada pasada nuestra: pos | far_ref | neg_limpio | sin_info."""
    for r in recs:
        filas = parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
        ns = noche_sensor.get((r["vol"], r["b"], r["noche"]), {"alerta": False, "fp": False})
        nv = noche_volcan.get((r["vol"], r["noche"]), {"alerta": False, "fp": False})
        r["dist_ref"] = None
        r["neg_estricto"] = False
        # S149: dos campos ADITIVOS, no cambian ninguna etiqueta. `rutina_pasada`: la tabla de MIROVA
        # lista ESTA pasada con VRP 0 (fila RUTINA del consolidado), haya o no alerta en otra pasada
        # de la noche. El negativo limpio exige ademas una noche sin alerta, asi que una RUTINA en
        # noche con alerta cae en sin_info y el evaluador no la veia (docs/S149_COSTO_OCULTO_MAX.md).
        r["rutina_pasada"] = any(f["tipo"] == "RUTINA" and f["source"] == "CONS"
                                 and (f["vrp_mw"] or 0) == 0 for f in filas)
        r["noche_con_alerta_sensor"] = bool(ns["alerta"])
        if any(es_alerta(f["tipo"]) for f in filas):
            r["lab"] = "pos"
        elif any(es_fp(f["tipo"]) for f in filas):
            r["lab"] = "far_ref"
            r["dist_ref"] = next((f["dist_km"] for f in filas if es_fp(f["tipo"]) and f["dist_km"] is not None), None)
        elif (any(f["tipo"] == "RUTINA" and f["source"] == "CONS" and (f["vrp_mw"] or 0) == 0 for f in filas)
              and not ns["alerta"] and not ns["fp"]):
            r["lab"] = "neg_limpio"
            r["neg_estricto"] = not nv["alerta"] and not nv["fp"]
        else:
            r["lab"] = "sin_info"


def alertas_sin_record(por_vb, recs):
    """Pasadas con ALERTA nocturna de MIROVA sin record nuestro a +-2 min: cobertura, aparte."""
    nuestros = collections.defaultdict(list)
    for r in recs:
        nuestros[(r["vol"], r["b"])].append(r["dt"])
    for v in nuestros.values():
        v.sort()
    out = collections.Counter()
    vistos = set()
    for (vol, b), lista in por_vb.items():
        ts = nuestros.get((vol, b), [])
        for dt, f in lista:
            if not es_alerta(f["tipo"]) or (vol, b, f["fecha_utc"][:16]) in vistos:
                continue
            vistos.add((vol, b, f["fecha_utc"][:16]))
            i = bisect.bisect_left(ts, dt - timedelta(seconds=TOL_S))
            if not (i < len(ts) and ts[i] <= dt + timedelta(seconds=TOL_S)):
                out[(vol, b)] += 1
    return out


# ---------------------------------------------------------------- metricas
def _tasa(a, n):
    return round(a / n, 4) if n else None


def metricas(recs, sin_record, filtro):
    """Pasada y noche de volcan para el subconjunto `filtro(rec)`."""
    sel = [r for r in recs if filtro(r)]
    c = collections.Counter()
    for r in sel:
        c[r["lab"]] += 1
        c[r["lab"] + "_pub"] += r["pub"]
        if r["neg_estricto"]:
            c["neg_estricto"] += 1
            c["neg_estricto_pub"] += r["pub"]
    pasada = {"n_pos": c["pos"], "recall_pos": _tasa(c["pos_pub"], c["pos"]),
              "n_neg_limpio": c["neg_limpio"], "tasa_pub_neg": _tasa(c["neg_limpio_pub"], c["neg_limpio"]),
              "n_neg_estricto_noche_volcan": c["neg_estricto"],
              "tasa_pub_neg_estricto_noche_volcan": _tasa(c["neg_estricto_pub"], c["neg_estricto"]),
              "n_far_ref": c["far_ref"], "n_sin_info": c["sin_info"],
              "pos_sin_record": sum(v for (vol, b), v in sin_record.items() if filtro({"vol": vol, "b": b}))}
    noches = collections.defaultdict(lambda: {"labs": set(), "pub": 0})
    for r in sel:
        e = noches[(r["vol"], r["noche"])]
        e["labs"].add(r["lab"])
        e["pub"] = max(e["pub"], r["pub"])
    nc = collections.Counter()
    for e in noches.values():
        if "pos" in e["labs"]:
            lab = "pos"
        elif "neg_limpio" in e["labs"] and "far_ref" not in e["labs"]:
            lab = "neg"
        else:
            continue
        nc[lab] += 1
        nc[lab + "_pub"] += e["pub"]
    noche = {"n_pos": nc["pos"], "recall_pos": _tasa(nc["pos_pub"], nc["pos"]),
             "n_neg": nc["neg"], "tasa_pub_neg": _tasa(nc["neg_pub"], nc["neg"])}
    return pasada, noche


def _filtro(vol=None, b=None):
    def f(r):
        return (vol is None or r["vol"] == vol) and (b is None or r["b"] == b)
    return f


def resumen(recs, sin_record):
    por_sensor = {}
    for b in BUCKETS + [None]:
        p, n = metricas(recs, sin_record, _filtro(b=b))
        por_sensor[b or "CUALQUIERA"] = {"pasada": p, "noche_volcan": n}
    por_volcan = {}
    for vol in VOLS:
        por_volcan[vol] = {}
        for b in BUCKETS + [None]:
            p, n = metricas(recs, sin_record, _filtro(vol=vol, b=b))
            por_volcan[vol][b or "CUALQUIERA"] = {"pasada": p, "noche_volcan": n}
    return por_sensor, por_volcan


def metrica_far_ref(recs, noche_volcan):
    out = {}
    for b in BUCKETS:
        sel = [r for r in recs if r["b"] == b and r["lab"] == "far_ref"]
        con_dist = [r for r in sel if r["dist_ref"] is not None and r["pc_dist"] is not None]
        out[b] = {"n": len(sel),
                  "frac_far_con_cumulo": _tasa(sum(1 for r in sel if r["dc"] == "far" and (r["pc_vrp"] or 0) > 0), len(sel)),
                  "frac_publica": _tasa(sum(r["pub"] for r in sel), len(sel)),
                  "n_con_distancia": len(con_dist),
                  # diferencia de RADIOS, no de posiciones (A93): cota inferior de la separacion
                  "frac_radio_a_2km": _tasa(sum(1 for r in con_dist if abs(r["pc_dist"] - r["dist_ref"]) <= 2), len(con_dist))}
    out["noches_crater_tapado"] = sum(1 for e in noche_volcan.values() if e["alerta"] and e["fp"])
    return out


def controles(recs, sin_record, identidad):
    ctrl = {"identidad_predicado": identidad == ([0, 1, 1, 1, 0], [1, 0]),
            "identidad_valores": identidad}
    for nombre, val in (("todo_publica", 1), ("nada_publica", 0)):
        falsos = [dict(r, pub=val) for r in recs]
        ctrl[nombre] = {b: metricas(falsos, sin_record, _filtro(b=b))[0] for b in BUCKETS}
    # AUC de la magnitud del display en V375, pos contra neg_limpio, por volcan
    rng = random.Random(7)
    real, barajado = {}, {}
    for vol in VOLS:
        sel = [r for r in recs if r["vol"] == vol and r["b"] == "VIIRS375" and r["lab"] in ("pos", "neg_limpio")]
        labs = [r["lab"] for r in sel]
        vals = [r["disp"] for r in sel]
        if labs.count("pos") < N_MIN_AUC or labs.count("neg_limpio") < N_MIN_AUC:
            continue
        real[vol] = round(auc([v for v, l in zip(vals, labs) if l == "pos"],
                              [v for v, l in zip(vals, labs) if l == "neg_limpio"]), 3)
        acc = 0.0
        for _ in range(N_BARAJADOS):
            lb = labs[:]
            rng.shuffle(lb)
            acc += auc([v for v, l in zip(vals, lb) if l == "pos"], [v for v, l in zip(vals, lb) if l == "neg_limpio"])
        barajado[vol] = round(acc / N_BARAJADOS, 3)
    ctrl["auc_real_disp_v375_por_volcan"] = real
    ctrl["auc_barajado_por_volcan"] = barajado
    pos = [1.0 for r in recs if r["lab"] == "pos"]
    neg = [0.0 for r in recs if r["lab"] == "neg_limpio"]
    ctrl["auc_oraculo"] = auc(pos, neg)
    return ctrl


def cenital_neg_v375(recs):
    c = collections.defaultdict(lambda: [0, 0])
    for r in recs:
        if r["b"] == "VIIRS375" and r["lab"] in ("pos", "neg_limpio"):
            c[f'{r["lab"]}|{zbin(r["z"])}'][0] += r["pub"]
            c[f'{r["lab"]}|{zbin(r["z"])}'][1] += 1
    return {k: {"pub": v[0], "n": v[1]} for k, v in sorted(c.items())}


def sha_git(path):
    return subprocess.run(["git", "hash-object", str(path)], capture_output=True, text=True,
                          check=True, cwd=ROOT).stdout.strip()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snapshot", action="store_true", help="referencia desde el snapshot del repo (sin red)")
    ap.add_argument("--inicio", default=INICIO_DEFECTO)
    ap.add_argument("--fin", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    ap.add_argument("--dest", default=str(ROOT / "experiments" / "_s140" / "_dl_referencia"))
    ap.add_argument("--out", default=str(ROOT / "experiments" / "_s140" / "banco_paridad_out.json"))
    a = ap.parse_args(argv)
    ventana = (a.inicio, a.fin)

    if a.snapshot:
        cons, ocr = SNAP_CONS, SNAP_OCR
        procedencia = {"fuente": "snapshot", "sha_cons": sha_git(SNAP_CONS), "sha_ocr": sha_git(SNAP_OCR)}
    else:
        info = bajar_remoto(Path(a.dest))
        cons = Path(info["registro_vrp_consolidado.csv"]["path"])
        ocr = Path(info["registro_vrp_ocr.csv"]["path"])
        procedencia = {"fuente": "remoto", "commit_cons": info["registro_vrp_consolidado.csv"]["sha"],
                       "commit_ocr": info["registro_vrp_ocr.csv"]["sha"]}
    procedencia["sha_respaldo_20260408"] = sha_git(RESPALDO_20260408)

    coords = _coords_por_volcan()
    inner = inner_desde_html()
    identidad = control_identidad_predicado()
    filas = cargar_referencia_unificada(cons, ocr)
    por_vb, noche_sensor, noche_volcan, n_ref = indexar_referencia(filas, coords, ventana)
    recs = cargar_nuestros(coords, inner, ventana)
    etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    sin_record = alertas_sin_record(por_vb, recs)
    por_sensor, por_volcan = resumen(recs, sin_record)

    banco = {
        "meta": {"ventana": list(ventana), "sha_index_html": sha_git(HTML), "referencia": procedencia,
                 "inner_radius_km": inner, "n_filas_ref_nocturnas": n_ref, "n_records_nocturnos": len(recs),
                 "etiquetas": dict(collections.Counter(r["lab"] for r in recs)),
                 "tolerancia_pareo_s": TOL_S, "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "definiciones": {
                     "pos": "pasada nuestra con fila ALERTA (CONS u OCR) nocturna a +-2 min",
                     "far_ref": "pasada con fila FALSO_POSITIVO y sin ALERTA: sin informacion para el crater",
                     "neg_limpio": "fila CONS RUTINA con VRP 0 a +-2 min, sin ALERTA ni FP esa noche y sensor",
                     "neg_estricto_noche_volcan": "neg_limpio y sin ALERTA ni FP en la noche del volcan (verificador S139)",
                     "sin_info": "resto, fuera de todo denominador",
                     "noche_volcan": "pos si alguna pasada pos; neg si hay neg_limpio y ninguna pos ni far_ref; publica si alguna pasada publica",
                     "nocturna": "store._reject_daytime por elevacion solar (auto_audit_weekly.es_pasada_diurna_descartada)"}},
        "por_sensor": por_sensor,
        "por_volcan": por_volcan,
        "far_ref": metrica_far_ref(recs, noche_volcan),
        "cenital_v375": cenital_neg_v375(recs),
        "alertas_sin_record": {f"{v}|{b}": n for (v, b), n in sorted(sin_record.items())},
        "controles": controles(recs, sin_record, identidad),
    }
    banco["meta"]["segundos"] = round(time.time() - T0, 1)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(banco, indent=1, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(banco["meta"]["referencia"], ensure_ascii=False))
    print(f"ventana {ventana[0]} a {ventana[1]} | records nocturnos {len(recs)} | etiquetas {banco['meta']['etiquetas']}")
    for b in BUCKETS + ["CUALQUIERA"]:
        p, n = por_sensor[b]["pasada"], por_sensor[b]["noche_volcan"]
        print(f"{b:10s} pasada: recall {p['recall_pos']} (n {p['n_pos']}) pub_neg {p['tasa_pub_neg']} (n {p['n_neg_limpio']}) "
              f"estricto {p['tasa_pub_neg_estricto_noche_volcan']} (n {p['n_neg_estricto_noche_volcan']}) | "
              f"noche: recall {n['recall_pos']} (n {n['n_pos']}) pub_neg {n['tasa_pub_neg']} (n {n['n_neg']})")
    print("controles:", {k: v for k, v in banco["controles"].items() if k not in ("todo_publica", "nada_publica")})
    print(f"listo en {banco['meta']['segundos']} s -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
