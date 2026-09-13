# -*- coding: utf-8 -*-
"""S139 eje 2: banco de prueba noche de volcan x sensor con TODOS los datos (CONS y OCR, tres
sensores, 11 Tier A, todas las fechas) y linea base del pipeline de hoy. READ-ONLY sobre data/.

QUE ARMA. Una tabla (volcan, bucket, noche) con:
  * referencia: filas CONS (ALERTA_TERMICA / FALSO_POSITIVO / RUTINA) y OCR (ALERTA_TERMICA_OCR /
    FALSO_POSITIVO_OCR) del snapshot Mirova-v1, tras el filtro diurno elegido;
  * nuestro lado: records de data/mirova_equivalent/<vol>.json del mismo bucket y noche, y si
    ALGUNO publica en el dashboard segun el predicado del operador, EJECUTADO con node desde
    frontend/index.html (no reescrito): isSummitDetection && isValidDetection &&
    !isThermalArtifact && mirovaEqVrpDisplay(r, inner_radius_km) > 0 (el mismo que latestDetection
    l. 1509-1513, sin isSensorVisible, que es un toggle de interfaz). _mirova_confirmed = false
    siempre: el banco no puede dejar que la etiqueta entre al predicado (seria circular).
  * maximos por noche de los campos persistidos, para AUC.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
  P1. Si el predicado estuviera roto del todo (todo publica / nada publica), el banco lo veria:
      los controles C_TODO y C_NADA dan recall 1 / 0 y tasa en negativos 1 / 0 sobre el mismo
      denominador, y se imprimen.
  P2. Si el instrumento estuviera muerto (node no corre, CSV vacio, JSON sin records), las filas
      SIN_DATO (referencia con fila y nosotros sin record, o al reves) se cuentan aparte y nunca
      entran como acierto ni como error. El control de identidad del predicado reproduce los 5
      casos sinteticos del guard tests/test_isvaliddetection_coherencia_s139.py.

PARAMETROS (todos en CONFIGS al final; cada combinacion se evalua y se guarda):
  fuentes    : "cons" | "cons_ocr"
  diurno     : "pipeline" (store._reject_daytime por elevacion solar, via auto_audit_weekly) |
               "utc12" (hora UTC < 12) | "ninguno"
  negativo   : "rutina_estricta"  noche-sensor con fila CONS y todas RUTINA (sin FP, sin ALERTA
                                   de la fuente elegida, en ese sensor)
               "sin_alerta"       sin ALERTA de la fuente elegida en ese sensor (RUTINA o FP)
               "volcan_quieto"    rutina_estricta y ademas ninguna ALERTA de ningun sensor del
                                   volcan en +-MARGEN dias (3)
               "solo_fp"          noches con FALSO_POSITIVO (CONS u OCR) y sin ALERTA
  radio_ref  : None | km  -> un positivo exige al menos una ALERTA con dist_km <= radio (dist None
               cuenta como dentro, supuesto declarado)
Noche = fecha UTC de la pasada (convencion de auto_audit_weekly y del eje 4 S138).

Salida: banco_noches_out.json (resumen por configuracion) + banco_tabla.json (tabla base con la
configuracion por defecto, para reutilizar).
"""
import collections
import csv
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
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

from pipeline.mirova_csv_loader import (load_mirova_alertas, normalize_sensor,  # noqa: E402
                                        normalize_volcano_name, parse_ocr_distance)
from auto_audit_weekly import es_pasada_diurna_descartada, _coords_por_volcan  # noqa: E402

SNAP = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot"
DATA = ROOT / "data" / "mirova_equivalent"
HTML = ROOT / "frontend" / "index.html"
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
BUCKETS = ["MODIS", "VIIRS375", "VIIRS750"]
MARGEN = 3


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


# ---------------------------------------------------------------- carga
def cargar_referencia(coords):
    """Filas por pasada de CONS y OCR, normalizadas, con marca diurna calculada."""
    filas = []
    for fuente, nombre in (("CONS", "registro_vrp_consolidado.csv"), ("OCR", "registro_vrp_ocr.csv")):
        with open(SNAP / nombre, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                vol = normalize_volcano_name(r.get("Volcan"))
                if vol is None:
                    continue
                b = normalize_sensor(r.get("Sensor"))
                dt = r.get("Fecha_Satelite_UTC") or ""
                try:
                    dto = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                tipo = (r.get("Tipo_Registro") or "").strip()
                if fuente == "OCR":
                    try:
                        dk = float(r.get("Distancia_km") or 0)
                    except ValueError:
                        dk = 0.0
                    dist = dk if dk > 0 else parse_ocr_distance(r.get("Nota_Validacion", ""))
                else:
                    try:
                        dist = float(r.get("Distancia_km"))
                    except (TypeError, ValueError):
                        dist = None
                try:
                    vrp = float(r.get("VRP_MW") or 0)
                except ValueError:
                    vrp = 0.0
                lat, lon = coords[vol]
                filas.append({"fuente": fuente, "vol": vol, "b": b, "dt": dto, "tipo": tipo,
                              "vrp": vrp, "dist": dist,
                              "clas": (r.get("Clasificacion Mirova") or "").strip(),
                              "diurna_pipe": es_pasada_diurna_descartada(b, lat, lon, dto)})
    return filas


def cargar_nuestros(coords, inner):
    recs, casos = [], []
    for vol in VOLS:
        d = json.load(open(DATA / f"{vol}.json", encoding="utf-8"))
        for r in d["records"]:
            b = bucket(r.get("sensor"))
            try:
                dto = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            if b is None:
                continue
            lat, lon = coords[vol]
            pc = r.get("primary_cluster") or {}
            recs.append({
                "vol": vol, "b": b, "dt": dto,
                "diurna_pipe": es_pasada_diurna_descartada(b, lat, lon, dto),
                "pc_vrp": pc.get("vrp_mw"), "pc_dist": pc.get("centroid_dist_km"),
                "pc_npx": pc.get("n_pixels"), "dc": r.get("distance_class"),
                "fh_dist": r.get("final_hotspot_dist_km"),
                "f5": r.get("f5_core_vrp_mw"), "nti_max": r.get("diag_nti_max"),
                "dT": (r["t_max_k"] - r["t_bg_k"]) if r.get("t_max_k") is not None and r.get("t_bg_k") is not None else None,
                "t1k": r.get("test1_k_observed"), "n_anom": r.get("n_anomalous_pixels"),
                "fp_summit": r.get("diag_n_first_pass_summit"), "vrp_rec": r.get("vrp_mw"),
            })
            slim = {k: r.get(k) for k in CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    t = time.time()
    pred = correr_node(casos)
    for rec, p in zip(recs, pred):
        rec["summit"], rec["valid"], rec["art"], rec["disp"], rec["pub"] = p
        rec["cum_inner"] = int((rec["pc_vrp"] or 0) > 0 and rec["pc_dist"] is not None
                               and rec["pc_dist"] <= inner[rec["vol"]])
    print(f"[node] {len(recs)} records evaluados con el predicado real en {time.time()-t:.1f}s")
    return recs


# ---------------------------------------------------------------- tabla por noche
def es_diurna(x, modo):
    if modo == "pipeline":
        return x["diurna_pipe"]
    if modo == "utc12":
        return x["dt"].hour >= 12
    return False


CAMPOS_AUC = [("pc_vrp_summitgated", "max"), ("pc_vrp", "max"), ("f5", "max"), ("nti_max", "max"),
              ("dT", "max"), ("t1k", "max"), ("n_anom", "max"), ("pc_npx", "max"),
              ("fp_summit", "max"), ("vrp_rec", "max"), ("disp", "max"), ("pc_dist", "min")]


def armar(filas, recs, fuentes, diurno, radio_ref):
    ref = collections.defaultdict(lambda: {"cons_rows": 0, "alerta": 0, "alerta_cerca": 0,
                                           "fp": 0, "rutina": 0, "ocr_rows": 0, "alerta_ocr_only": 0,
                                           "vrp_ref": 0.0})
    for f in filas:
        if es_diurna(f, diurno):
            continue
        if fuentes == "cons" and f["fuente"] == "OCR":
            continue
        k = (f["vol"], f["b"], f["dt"].strftime("%Y-%m-%d"))
        e = ref[k]
        if f["fuente"] == "CONS":
            e["cons_rows"] += 1
        else:
            e["ocr_rows"] += 1
        if f["tipo"].startswith("ALERTA"):
            e["alerta"] += 1
            e["vrp_ref"] = max(e["vrp_ref"], f["vrp"])
            if radio_ref is None or f["dist"] is None or f["dist"] <= radio_ref:
                e["alerta_cerca"] += 1
            if f["fuente"] == "OCR":
                e["alerta_ocr_only"] += 1
        elif f["tipo"].startswith("FALSO_POSITIVO") or f["clas"].upper() == "FALSO POSITIVO":
            e["fp"] += 1
        elif f["tipo"] == "RUTINA":
            e["rutina"] += 1
    nos = collections.defaultdict(lambda: {"n": 0, "pub": 0, "cum_inner": 0,
                                           "far_cum_cerca": 0, "vals": {}})
    for r in recs:
        if es_diurna(r, diurno):
            continue
        k = (r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d"))
        e = nos[k]
        e["n"] += 1
        e["pub"] = max(e["pub"], r["pub"])
        e["cum_inner"] = max(e["cum_inner"], r["cum_inner"])
        if r["dc"] == "far" and r["cum_inner"]:
            e["far_cum_cerca"] = 1
        vals = dict(r)
        vals["pc_vrp_summitgated"] = r["pc_vrp"] if r["summit"] else 0.0
        for c, agg in CAMPOS_AUC:
            v = vals.get(c)
            if v is None:
                continue
            old = e["vals"].get(c)
            e["vals"][c] = v if old is None else (max(old, v) if agg == "max" else min(old, v))
    return ref, nos


def etiqueta(ref, k, negativo, alerta_vol_fechas):
    """'pos' | 'neg' | 'excl' | 'sin_fila' para una noche-sensor."""
    e = ref.get(k)
    if e is None:
        return "sin_fila"
    if e["alerta_cerca"] > 0:
        return "pos"
    if e["alerta"] > 0:
        return "excl"  # alerta pero fuera del radio: ni positivo ni negativo
    if negativo == "sin_alerta":
        return "neg"
    if negativo == "solo_fp":
        return "neg" if e["fp"] > 0 else "excl"
    estricta = e["cons_rows"] > 0 and e["fp"] == 0 and e["rutina"] > 0
    if negativo == "rutina_estricta":
        return "neg" if estricta else "excl"
    if negativo == "volcan_quieto":
        if not estricta:
            return "excl"
        vol, _, f = k
        d0 = datetime.strptime(f, "%Y-%m-%d")
        for dd in range(-MARGEN, MARGEN + 1):
            if (vol, (d0 + timedelta(days=dd)).strftime("%Y-%m-%d")) in alerta_vol_fechas:
                return "excl"
        return "neg"
    raise ValueError(negativo)


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


def evaluar(ref, nos, negativo, pred="pub", exigir_cobertura=True, ventana=None):
    alerta_vol_fechas = {(v, f) for (v, b, f), e in ref.items() if e["alerta"] > 0}
    claves = set(ref) | set(nos)
    if ventana:
        claves = {k for k in claves if ventana[0] <= k[2] <= ventana[1]}
    cel = collections.defaultdict(lambda: {"pos": 0, "pos_det": 0, "neg": 0, "neg_det": 0,
                                           "pos_sin_dato": 0, "neg_sin_dato": 0,
                                           "solo_nuestro": 0, "noches": set()})
    filas_auc = []
    # por sensor
    for k in claves:
        vol, b, f = k
        lab = etiqueta(ref, k, negativo, alerta_vol_fechas)
        n = nos.get(k)
        c = cel[(vol, b)]
        if lab == "sin_fila":
            if n and n["n"]:
                c["solo_nuestro"] += 1
            continue
        if lab == "excl":
            continue
        if not n or n["n"] == 0:
            c[lab + "_sin_dato"] += 1
            if exigir_cobertura:
                continue
        det = bool(n and n[pred])
        c[lab] += 1
        c[lab + "_det"] += int(det)
        c["noches"].add(f)
        if n:
            filas_auc.append((vol, b, lab, n["vals"]))
    # cualquier sensor por noche de volcan
    vn = collections.defaultdict(lambda: {"labs": [], "det": 0, "cov": 0})
    for k in claves:
        vol, b, f = k
        lab = etiqueta(ref, k, negativo, alerta_vol_fechas)
        n = nos.get(k)
        e = vn[(vol, f)]
        e["labs"].append(lab)
        if n and n["n"]:
            e["cov"] = 1
            e["det"] = max(e["det"], int(bool(n[pred])))
    for (vol, f), e in vn.items():
        labs = e["labs"]
        if "pos" in labs:
            lab = "pos"
        elif "neg" in labs and all(x in ("neg", "sin_fila") for x in labs):
            lab = "neg"
        elif all(x == "sin_fila" for x in labs):
            if e["cov"]:
                cel[(vol, "CUALQUIERA")]["solo_nuestro"] += 1
            continue
        else:
            continue
        c = cel[(vol, "CUALQUIERA")]
        if not e["cov"]:
            c[lab + "_sin_dato"] += 1
            if exigir_cobertura:
                continue
        c[lab] += 1
        c[lab + "_det"] += e["det"]
        c["noches"].add(f)
    out = {}
    for (vol, b), c in cel.items():
        ns = sorted(c["noches"])
        out[f"{vol}|{b}"] = {k: v for k, v in c.items() if k != "noches"} | {
            "ventana": [ns[0], ns[-1]] if ns else None}
    return out, filas_auc


def agregar(tabla, por="b"):
    agg = collections.defaultdict(collections.Counter)
    for key, c in tabla.items():
        vol, b = key.split("|")
        g = b if por == "b" else vol
        for k in ("pos", "pos_det", "neg", "neg_det", "pos_sin_dato", "neg_sin_dato", "solo_nuestro"):
            agg[g][k] += c[k]
    res = {}
    for g, c in agg.items():
        res[g] = dict(c) | {"recall": round(c["pos_det"] / c["pos"], 3) if c["pos"] else None,
                            "tasa_neg": round(c["neg_det"] / c["neg"], 3) if c["neg"] else None}
    return res


def aucs(filas_auc, bucket_sel):
    res = {}
    for campo, _ in CAMPOS_AUC:
        por_vol, pooled_p, pooled_n = {}, [], []
        num = den = 0.0
        for vol in VOLS:
            p = [v[campo] for (vv, b, lab, v) in filas_auc if vv == vol and b == bucket_sel
                 and lab == "pos" and campo in v]
            n = [v[campo] for (vv, b, lab, v) in filas_auc if vv == vol and b == bucket_sel
                 and lab == "neg" and campo in v]
            a = auc(p, n)
            if campo == "pc_dist" and a is not None:
                a = 1 - a  # menor distancia = mas positivo
            por_vol[vol] = {"auc": None if a is None else round(a, 3), "n_pos": len(p), "n_neg": len(n)}
            pooled_p += p
            pooled_n += n
            if a is not None and len(p) >= 5:
                w = len(p)
                num += a * w
                den += w
        ap = auc(pooled_p, pooled_n)
        if campo == "pc_dist" and ap is not None:
            ap = 1 - ap
        res[campo] = {"pooled": None if ap is None else round(ap, 3),
                      "media_por_volcan_pond_npos(npos>=5)": round(num / den, 3) if den else None,
                      "por_volcan": por_vol}
    return res


def main():
    coords = _coords_por_volcan()
    inner = inner_desde_html()
    print("inner_radius_km (frontend):", inner)
    ident_valid, ident_pub = control_identidad_predicado()
    print("CONTROL identidad isValidDetection (esperado [F,T,T,T,F]):", ident_valid,
          "| publicacion (esperado [1,0]):", ident_pub)
    filas = cargar_referencia(coords)
    print(f"[ref] {len(filas)} filas CONS+OCR; ventana CONS "
          f"{min(f['dt'] for f in filas if f['fuente']=='CONS'):%Y-%m-%d} a "
          f"{max(f['dt'] for f in filas if f['fuente']=='CONS'):%Y-%m-%d}; OCR "
          f"{min(f['dt'] for f in filas if f['fuente']=='OCR'):%Y-%m-%d} a "
          f"{max(f['dt'] for f in filas if f['fuente']=='OCR'):%Y-%m-%d}")
    # cruce con el loader oficial: mismas ALERTAS (dedup) que load_mirova_alertas
    al = load_mirova_alertas(cons_path=str(SNAP / "registro_vrp_consolidado.csv"),
                             ocr_path=str(SNAP / "registro_vrp_ocr.csv"))
    mias = {(f["dt"].strftime("%Y-%m-%d %H:%M"), f["vol"], f["b"]) for f in filas if f["tipo"].startswith("ALERTA")}
    ofic = {(a["fecha_utc"][:16], a["volcano"], a["sensor_bucket"]) for a in al}
    print(f"CONTROL loader oficial: alertas oficiales {len(ofic)} claves, mias {len(mias)}, "
          f"solo oficial {len(ofic-mias)}, solo mias {len(mias-ofic)}")
    recs = cargar_nuestros(coords, inner)
    fechas_nos = sorted(r["dt"] for r in recs)
    print(f"[nos] {len(recs)} records, {fechas_nos[0]:%Y-%m-%d} a {fechas_nos[-1]:%Y-%m-%d}; "
          f"publican {sum(r['pub'] for r in recs)}; diurnos segun pipeline {sum(r['diurna_pipe'] for r in recs)}")
    ventana_ref = (min(f["dt"] for f in filas).strftime("%Y-%m-%d"),
                   max(f["dt"] for f in filas).strftime("%Y-%m-%d"))

    resultados = {"meta": {"inner": inner, "ventana_ref": ventana_ref,
                           "ventana_nos": [f"{fechas_nos[0]:%Y-%m-%d}", f"{fechas_nos[-1]:%Y-%m-%d}"],
                           "n_records": len(recs), "n_filas_ref": len(filas),
                           "control_identidad": [ident_valid, ident_pub]},
                  "configs": {}}
    cache = {}
    CONFIGS = []
    for fuentes in ("cons", "cons_ocr"):
        for diurno in ("pipeline", "utc12", "ninguno"):
            for negativo in ("rutina_estricta", "sin_alerta", "volcan_quieto", "solo_fp"):
                CONFIGS.append((fuentes, diurno, negativo, None))
    CONFIGS += [("cons_ocr", "pipeline", "rutina_estricta", 5.0),
                ("cons_ocr", "pipeline", "volcan_quieto", 5.0)]
    for fuentes, diurno, negativo, radio in CONFIGS:
        ck = (fuentes, diurno, radio)
        if ck not in cache:
            cache[ck] = armar(filas, recs, fuentes, diurno, radio)
        ref, nos = cache[ck]
        nombre = f"{fuentes}|{diurno}|{negativo}|radio={radio}"
        tabla, fa = evaluar(ref, nos, negativo, "pub", True, ventana_ref)
        tabla_cum, _ = evaluar(ref, nos, negativo, "cum_inner", True, ventana_ref)
        cfg = {"por_sensor": agregar(tabla, "b"), "por_sensor_pred_cumulo": agregar(tabla_cum, "b")}
        if negativo in ("rutina_estricta", "volcan_quieto") and radio is None:
            cfg["celdas"] = tabla
            cfg["celdas_pred_cumulo"] = tabla_cum
            if diurno == "pipeline":
                cfg["auc"] = {b: aucs(fa, b) for b in BUCKETS}
        # controles del instrumento: todo publica / nada publica
        for nom, val in (("C_TODO", 1), ("C_NADA", 0)):
            nos_c = {k: dict(v, pub=val) for k, v in nos.items()}
            t, _ = evaluar(ref, nos_c, negativo, "pub", True, ventana_ref)
            cfg[nom] = agregar(t, "b")
        resultados["configs"][nombre] = cfg
        g = cfg["por_sensor"]
        print(f"{nombre:52s} " + "  ".join(
            f"{b}: rec {g.get(b,{}).get('pos_det')}/{g.get(b,{}).get('pos')} neg {g.get(b,{}).get('neg_det')}/{g.get(b,{}).get('neg')}"
            for b in BUCKETS + ["CUALQUIERA"]))

    # control negativo: etiquetas barajadas dentro de (volcan, sensor) -> AUC ~0,5
    ref, nos = cache[("cons_ocr", "pipeline", None)]
    _, fa = evaluar(ref, nos, "rutina_estricta", "pub", True, ventana_ref)
    rng = random.Random(7)
    grupos = collections.defaultdict(list)
    for i, x in enumerate(fa):
        grupos[(x[0], x[1])].append(i)
    fa_b = list(fa)
    for idx in grupos.values():
        labs = [fa[i][2] for i in idx]
        rng.shuffle(labs)
        for i, lab in zip(idx, labs):
            fa_b[i] = (fa[i][0], fa[i][1], lab, fa[i][3])
    # OJO: el AUC agrupado (pooled) NO vuelve a 0,5 con etiquetas barajadas dentro de cada volcan,
    # porque la mezcla de volcanes con distinta tasa de positivos y distinto nivel del campo crea
    # senal espuria (Simpson). Solo la media por volcan es un instrumento valido.
    resultados["control_barajado_auc"] = {b: {c: {"pooled": v["pooled"],
                                                  "media_por_volcan": v["media_por_volcan_pond_npos(npos>=5)"]}
                                              for c, v in aucs(fa_b, b).items()} for b in BUCKETS}
    # control positivo de AUC: campo oraculo = etiqueta
    fa_o = [(v, b, lab, dict(vals, pc_vrp=1.0 if lab == "pos" else 0.0)) for v, b, lab, vals in fa]
    resultados["control_oraculo_auc_pc_vrp"] = {b: aucs(fa_o, b)["pc_vrp"]["pooled"] for b in BUCKETS}

    # tabla base reutilizable (config por defecto)
    base = []
    alerta_vol_fechas = {(v, f) for (v, b, f), e in ref.items() if e["alerta"] > 0}
    for k in sorted(set(ref) | set(nos)):
        e, n = ref.get(k), nos.get(k)
        base.append({"vol": k[0], "b": k[1], "noche": k[2],
                     "ref": None if e is None else dict(e),
                     "etq_rutina_estricta": etiqueta(ref, k, "rutina_estricta", alerta_vol_fechas),
                     "etq_volcan_quieto": etiqueta(ref, k, "volcan_quieto", alerta_vol_fechas),
                     "nos": None if n is None else {kk: vv for kk, vv in n.items()}})
    (HERE / "banco_tabla.json").write_text(json.dumps(base), encoding="utf-8")
    resultados["segundos"] = round(time.time() - T0, 1)
    (HERE / "banco_noches_out.json").write_text(json.dumps(resultados, indent=1), encoding="utf-8")
    print("controles barajado AUC:", resultados["control_barajado_auc"])
    print("control oraculo AUC:", resultados["control_oraculo_auc_pc_vrp"])
    print(f"listo en {resultados['segundos']} s")


if __name__ == "__main__":
    main()
