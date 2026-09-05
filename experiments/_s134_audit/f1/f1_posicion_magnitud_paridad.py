# -*- coding: utf-8 -*-
"""S134 · F1 — Posición del cúmulo → magnitud publicada → paridad con MIROVA, por PASADA.

FICHA SDA — medición read-only sobre records persistidos y sobre el ground truth scrapeado.
No toca la detección ni ningún archivo del repositorio fuera de experiments/_s134_audit/f1/.

POR QUÉ (el fenómeno antes que el código)
-----------------------------------------
S133 midió que en 9 de los 11 Tier A el centroide del cúmulo que publicamos en VIIRS 375 m está
a 2,3-2,8 km del cráter (docs/s133/ANILLO_TIER_A.md). La hipótesis física abierta: si nosotros
integramos el calor de la frontera nieve-roca del flanco y MIROVA integra la celda del cráter,
las dos magnitudes son de dos objetos distintos y ninguna corrección de área o de banda cierra la
brecha. Nadie encadenó posición → magnitud → paridad con la MISMA pasada y la MISMA ancla. Eso
hace este script. Láscar (cúmulo en el cráter y aun así ~0,47 de razón) es el contraejemplo que
la hipótesis tiene que explicar.

CRITERIO PRE-REGISTRADO (escrito ANTES de correr nada, 2026-09-05)
------------------------------------------------------------------
«La posición explica la paridad» si, en VIIRS 375 m, la razón mediana ours/MIROVA del bin
d_crater ≤ 0,5 km está dentro de [0,7; 1,4] **y** la del bin > 1,5 km está fuera de esa banda,
en ≥ 6 de los 9 volcanes con anillo (los 11 Tier A menos Láscar e Isluga). Si la razón NO
depende de d_crater (Spearman ~0, medianas por bin todas dentro o todas fuera de la banda), la
hipótesis queda refutada y se dice así.

LAS DOS PREGUNTAS DEL INSTRUMENTO
---------------------------------
1. Si la posición NO explicara nada, ¿lo vería? Sí: las medianas por bin saldrían iguales y el
   Spearman razón~d_crater saldría ~0. Si la posición lo explicara TODO, el bin ≤0,5 km daría
   ~1 y el bin >1,5 km se alejaría de 1 en todos los volcanes.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Controles:
   - Línea base roja: correr con --ancla catalogo y después con --ancla vent. Villarrica DEBE
     cambiar (catálogo a 0,85 km del cráter, A13); si no cambia, la ancla no se usa (A89).
   - Control positivo: Láscar VIIRS375 desde 2026-06-01 debe dar mediana d_crater ≈0,2 km y
     ~79 % a <500 m (S133). Si no, el script está mal, no Láscar.
   - Control del pareo: ≥50 % de las ALERTAS MIROVA de Láscar VIIRS375 desde 2026-06 deben tener
     pasada nuestra a ±TOL min. Si no, revisar tolerancia/bucket/alias antes de seguir.
   - Control negativo: records `far` pareados — la razón ahí debe ser ruido.
   - SIN DATO ≠ FALLA ≠ OK: cada conjunto vacío se reporta como n=0 con su denominador, nunca
     como «0 %».

DENOMINADORES Y VENTANA (A90): cada número lleva n y la ventana (desde --desde, hasta la fecha
del snapshot de MIROVA 2026-08-31 para los pares; hasta el último record en disco para las
distribuciones de posición).

Uso:
  python f1_posicion_magnitud_paridad.py --ancla catalogo --out resultados_ancla_catalogo.json
  python f1_posicion_magnitud_paridad.py --ancla vent     --out resultados.json
"""
import argparse
import bisect
import io
import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

import numpy as np
import yaml
from scipy.stats import spearmanr

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_WT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # raíz del worktree
sys.path.insert(0, ROOT_WT)
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

# El worktree es sparse y NO tiene data/: los JSON y el ground truth se leen SÓLO LECTURA
# desde la raíz canónica (README de experiments/_s134_audit/).
DATA_ROOT = os.environ.get(
    "VRP_DATA_ROOT",
    "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
DATA_DIR = os.path.join(DATA_ROOT, "data", "mirova_equivalent")
SNAP = os.path.join(DATA_ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
CONS = os.path.join(SNAP, "registro_vrp_consolidado.csv")
OCR = os.path.join(SNAP, "registro_vrp_ocr.csv")

TIER = ["Lascar", "Isluga", "Lastarria", "Llaima", "Villarrica", "Copahue", "Chaiten",
        "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle", "Tupungatito"]
ANILLO = [v for v in TIER if v not in ("Lascar", "Isluga")]   # los 9 del criterio
SENSORES = ["VIIRS375", "VIIRS750", "MODIS"]
BINS = [("<=0.5", 0.0, 0.5), ("0.5-1.5", 0.5, 1.5), ("1.5-3", 1.5, 3.0), (">3", 3.0, 1e9)]
BANDA = (0.7, 1.4)
N_BOOT = 5000
RNG = np.random.default_rng(134)


# ----------------------------------------------------------------------------- utilidades
def hav(lat1, lon1, lat2, lon2):
    """Haversine, R=6371 km (misma que pipeline/f5_core.py y el frontend)."""
    p = math.pi / 180.0
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def bucket_ours(sensor):
    """Convención del repo (A48), verificada hoy con Counter(r['sensor']) sobre los 11 Tier A:
    VIIRS_{SNPP,NOAA20,NOAA21} = I-band 375 m; sufijo _750 = M-band; MODIS_* = MODIS."""
    s = str(sensor or "")
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS"):
        return "VIIRS750" if s.endswith("_750") else "VIIRS375"
    return None


def es_iband(sensor):
    s = str(sensor or "").upper()
    return s.startswith("VIIRS") and not s.endswith("_750")


def t_ours(r):
    return datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")


def t_mir(a):
    return datetime.strptime(a["fecha_utc"], "%Y-%m-%d %H:%M:%S")


def fnum(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def mediana(xs):
    return float(np.median(xs)) if len(xs) else None


def ic_boot_mediana(xs, n_boot=N_BOOT):
    """IC 95 % bootstrap de la mediana (T8). Sólo si n ≥ 10; si no, None (no se inventa)."""
    xs = np.asarray(xs, dtype=float)
    if xs.size < 10:
        return None
    idx = RNG.integers(0, xs.size, size=(n_boot, xs.size))
    meds = np.median(xs[idx], axis=1)
    return [round(float(np.percentile(meds, 2.5)), 3), round(float(np.percentile(meds, 97.5)), 3)]


def resumen_razon(rs):
    """n, mediana, IC, y la DISTRIBUCIÓN (T3): cuántos >1,4, cuántos <0,7, cuántos en banda."""
    rs = [r for r in rs if r is not None and r > 0]
    if not rs:
        return {"n": 0, "mediana": None, "ic95": None, "n_sobre_1.4": 0, "n_bajo_0.7": 0,
                "n_en_banda": 0}
    return {"n": len(rs), "mediana": round(mediana(rs), 3), "ic95": ic_boot_mediana(rs),
            "p25": round(float(np.percentile(rs, 25)), 3),
            "p75": round(float(np.percentile(rs, 75)), 3),
            "n_sobre_1.4": sum(1 for r in rs if r > BANDA[1]),
            "n_bajo_0.7": sum(1 for r in rs if r < BANDA[0]),
            "n_en_banda": sum(1 for r in rs if BANDA[0] <= r <= BANDA[1])}


def en_banda(m):
    return m is not None and BANDA[0] <= m <= BANDA[1]


def bin_de(d):
    if d is None:
        return None
    for nombre, lo, hi in BINS:
        if lo <= d < hi if nombre != "<=0.5" else d <= hi:
            return nombre
    return None


# ----------------------------------------------------------------------------- carga
def cargar_anclas(modo):
    cfg = yaml.safe_load(io.open(os.path.join(ROOT_WT, "volcanoes.yaml"), encoding="utf-8"))
    vols = cfg["volcanoes"] if isinstance(cfg, dict) and "volcanoes" in cfg else cfg
    items = vols if isinstance(vols, list) else [dict(name=k, **x) for k, x in vols.items()]
    anclas, faltan, inner = {}, [], {}
    for v in items:
        if v["name"] not in TIER:
            continue
        inner[v["name"]] = float(v["inner_radius_km"])
        if modo == "vent":
            if v.get("vent_lat") is None or v.get("vent_lon") is None:
                faltan.append(v["name"])
                anclas[v["name"]] = (float(v["lat"]), float(v["lon"]))
            else:
                anclas[v["name"]] = (float(v["vent_lat"]), float(v["vent_lon"]))
        else:
            anclas[v["name"]] = (float(v["lat"]), float(v["lon"]))
    return anclas, inner, faltan


def cargar_records(vol, desde):
    """Records del volcán desde `desde`, deduplicados por (sensor, granule) — pendiente P4.

    Política de dedupe: se conserva el record con product_version 'standard' si lo hay (el
    store hace auto-upgrade NRT→Standard); si son de la misma versión, el ÚLTIMO en el archivo.
    Se cuenta cuántos duplicados había y en cuántos la magnitud publicada difería.
    """
    p = os.path.join(DATA_DIR, vol + ".json")
    d = json.load(io.open(p, encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    recs = [r for r in recs if isinstance(r, dict) and str(r.get("datetime_utc") or "")[:10] >= desde
            and r.get("granule") and r.get("sensor")]
    por = {}
    dup, dup_distintos, sin_granule = 0, 0, 0
    for r in recs:
        k = (r["sensor"], r["granule"])
        if k in por:
            dup += 1
            a, b = por[k], r
            if (fnum((a.get("primary_cluster") or {}).get("vrp_mw")) or 0) != \
               (fnum((b.get("primary_cluster") or {}).get("vrp_mw")) or 0):
                dup_distintos += 1
            if a.get("product_version") == "standard" and b.get("product_version") != "standard":
                continue
        por[k] = r
    return list(por.values()), {"n_total_ventana": len(recs), "n_dedupe": len(por),
                                "n_duplicados": dup, "n_duplicados_con_pc_vrp_distinto": dup_distintos}


# ----------------------------------------------------------------------------- por record
def describir(r, vol, ancla, inner_km, ancla_cat=None):
    """Todo lo que F1 necesita de un record, con la regla de magnitud del OPERADOR.

    Regla replicada de frontend/index.html mirovaEqVrpCore (l. 1039-1185, leída hoy):
      gate: distance_class == 'summit' Y pc.centroid_dist_km <= inner_km, si no → 0;
      base = pc.vrp_mw; para I-band, core = f5_core_vrp_mw si es número (fallback a base si
      falta o es ≤0); MODIS y M-band publican base. Cap 50000 → 0.
    Además se conserva `mag_pc` (pc.vrp_mw sin gate) para el estrato MODIS summit ∪ far.
    """
    pc = r.get("primary_cluster") or {}
    la, lo = ancla
    clat, clon = fnum(pc.get("centroid_lat")), fnum(pc.get("centroid_lon"))
    d_crater = hav(clat, clon, la, lo) if clat is not None and clon is not None else None
    # d_catalogo: SIEMPRE desde lat/lon del catálogo, para comparar con la Distancia_km de MIROVA
    # (que se mide desde SU centro de grilla, cuantizada — D15; la comparación es indicativa).
    d_cat = None
    off_n = off_e = None
    if clat is not None and clon is not None:
        if ancla_cat is not None:
            d_cat = hav(clat, clon, ancla_cat[0], ancla_cat[1])
        # offset direccional (A70): km hacia el N y hacia el E desde el ancla
        off_n = (clat - la) * 111.2
        off_e = (clon - lo) * 111.2 * math.cos(math.radians(la))
    # d_pico: píxel de máximo vrp_mw de anomaly_pixels, medido desde lat/lon (nunca dist_km, A48)
    pix = [p for p in (r.get("anomaly_pixels") or []) if p.get("lat") is not None]
    d_pico, pico_vrp = None, None
    if pix:
        pk = max(pix, key=lambda p: fnum(p.get("vrp_mw")) or 0.0)
        d_pico = hav(pk["lat"], pk["lon"], la, lo)
        pico_vrp = fnum(pk.get("vrp_mw"))
    mag_pc = fnum(pc.get("vrp_mw")) or 0.0
    if mag_pc > 50000:
        mag_pc = 0.0
    cdist = fnum(pc.get("centroid_dist_km"))
    gate_ok = (r.get("distance_class") == "summit") and not (cdist is not None and cdist > inner_km)
    fuente = "pc.vrp_mw"
    f5_fallback = False
    mag_pub = 0.0
    if gate_ok and mag_pc > 0:
        mag_pub = mag_pc
        if es_iband(r.get("sensor")):
            core = fnum(r.get("f5_core_vrp_mw"))
            if core is not None and core > 0:
                mag_pub = core if core <= 50000 else 0.0
                fuente = "f5_core_vrp_mw"
            else:
                f5_fallback = True
                fuente = "pc.vrp_mw(fallback f5)"
    # Filtro de artefacto del frontend (isThermalArtifact, l. 1203-1235), sólo para CONTAR
    tmax = fnum(r.get("t_max_k"))
    base_gate = mag_pc if gate_ok else 0.0
    cirrus = tmax is not None and tmax < 273.15 and base_gate > 10
    difuso = (tmax is not None and tmax < 278.15 and (pc.get("n_pixels") or 0) >= 100
              and base_gate >= 50 and base_gate / max(pc.get("n_pixels") or 1, 1) < 1.0)
    return {
        "vol": vol, "sensor": r["sensor"], "bucket": bucket_ours(r["sensor"]),
        "granule": r["granule"], "t": t_ours(r), "datetime_utc": r["datetime_utc"],
        "distance_class": r.get("distance_class"), "gate_ok": bool(gate_ok),
        "d_crater": d_crater, "d_pico": d_pico, "pico_vrp": pico_vrp,
        "d_catalogo": d_cat, "off_n_km": off_n, "off_e_km": off_e,
        "centroid_dist_km_pipeline": cdist,
        "mag_pub": mag_pub, "mag_pc": mag_pc, "fuente": fuente, "f5_fallback": f5_fallback,
        "f5_presente": r.get("f5_core_vrp_mw") is not None,
        "n_pixels": pc.get("n_pixels"), "single_pixel_mode": pc.get("single_pixel_mode"),
        "zenith": fnum(r.get("sensor_zenith_deg")), "t_max_k": tmax,
        "artefacto_frontend": bool(cirrus or difuso), "n_anomaly_pixels": len(pix),
        "triggered_test1": bool(r.get("triggered_test1")),
    }


# ----------------------------------------------------------------------------- pareo
def parear(ours, alertas, tol_min):
    """Pareo POR PASADA (±tol_min) por (volcán, bucket). Nunca por noche.

    Devuelve pares y los otros dos conjuntos: nuestros publicados sin ALERTA MIROVA, y ALERTAS
    MIROVA sin nosotros — estas últimas partidas en «sin pasada nuestra» (no hay record a ±tol:
    cobertura) y «pasada nuestra sin publicar» (hay record pero mag_pub = 0: FN de verdad).
    """
    tol = timedelta(minutes=tol_min)
    idx = defaultdict(list)
    for o in ours:
        if o["bucket"]:
            idx[(o["vol"], o["bucket"])].append(o)
    for k in idx:
        idx[k].sort(key=lambda o: o["t"])
    tiempos = {k: [o["t"] for o in v] for k, v in idx.items()}

    pares, mir_sin_pasada, mir_pasada_sin_pub, ambiguas = [], [], [], 0
    usados = set()
    for a in alertas:
        k = (a["volcano"], a["sensor_bucket"])
        ts = tiempos.get(k, [])
        ta = t_mir(a)
        i = bisect.bisect_left(ts, ta - tol)
        cands = []
        while i < len(ts) and ts[i] <= ta + tol:
            cands.append(idx[k][i])
            i += 1
        if not cands:
            mir_sin_pasada.append(a)
            continue
        if len({c["granule"] for c in cands}) > 1:
            ambiguas += 1
        o = min(cands, key=lambda c: abs((c["t"] - ta).total_seconds()))
        usados.add((o["sensor"], o["granule"]))
        par = dict(o)
        par.update({"mir_vrp": a["vrp_mw"], "mir_dist_km": a["dist_km"], "mir_source": a["source"],
                    "mir_t": ta, "dt_min": (o["t"] - ta).total_seconds() / 60.0,
                    "razon_pub": (o["mag_pub"] / a["vrp_mw"]) if a["vrp_mw"] and o["mag_pub"] > 0 else None,
                    "razon_pc": (o["mag_pc"] / a["vrp_mw"]) if a["vrp_mw"] and o["mag_pc"] > 0 else None})
        if o["mag_pub"] > 0:
            pares.append(par)
        else:
            mir_pasada_sin_pub.append(par)
    ours_sin_mir = [o for o in ours if o["mag_pub"] > 0 and (o["sensor"], o["granule"]) not in usados]
    return pares, ours_sin_mir, mir_sin_pasada, mir_pasada_sin_pub, ambiguas


# ----------------------------------------------------------------------------- tablas
def tabla_bins(pares, clave_razon="razon_pub", clave_d="d_crater"):
    out = {}
    for nombre, _, _ in BINS:
        rs = [p[clave_razon] for p in pares if bin_de(p[clave_d]) == nombre]
        out[nombre] = resumen_razon(rs)
    out["todos"] = resumen_razon([p[clave_razon] for p in pares])
    rs = [(p[clave_d], p[clave_razon]) for p in pares if p[clave_razon] and p[clave_d] is not None]
    if len(rs) >= 10:
        rho, pval = spearmanr([x for x, _ in rs], [y for _, y in rs])
        out["spearman_razon_vs_d"] = {"rho": round(float(rho), 3), "p": float(pval), "n": len(rs)}
    else:
        out["spearman_razon_vs_d"] = {"rho": None, "p": None, "n": len(rs)}
    return out


def criterio(pares_v375):
    """Veredicto pre-registrado sobre los 9 volcanes con anillo, VIIRS375."""
    filas, cumplen, evaluables = {}, 0, 0
    for vol in ANILLO:
        pv = [p for p in pares_v375 if p["vol"] == vol]
        cerca = resumen_razon([p["razon_pub"] for p in pv if p["d_crater"] is not None and p["d_crater"] <= 0.5])
        lejos = resumen_razon([p["razon_pub"] for p in pv if p["d_crater"] is not None and p["d_crater"] > 1.5])
        ok = None
        if cerca["n"] >= 5 and lejos["n"] >= 5:   # sin n mínimo la mediana no decide nada (T8)
            evaluables += 1
            ok = en_banda(cerca["mediana"]) and not en_banda(lejos["mediana"])
            cumplen += int(ok)
        filas[vol] = {"n_pares": len(pv), "cerca_<=0.5": cerca, "lejos_>1.5": lejos,
                      "cumple": ok, "evaluable": cerca["n"] >= 5 and lejos["n"] >= 5}
    return {"regla": "mediana(<=0.5 km) en [0.7,1.4] Y mediana(>1.5 km) fuera, n>=5 en ambos bins, "
                     ">=6 de 9 volcanes con anillo, VIIRS375",
            "volcanes_evaluables": evaluables, "volcanes_que_cumplen": cumplen,
            "veredicto": "CUMPLE" if cumplen >= 6 else "NO CUMPLE",
            "por_volcan": filas}


def posicion_por_vol(descr, vol, bucket, desde=None):
    """Distribución de d_crater y d_pico sobre records PUBLICADOS (mag_pub>0), como S133."""
    xs = [o for o in descr if o["vol"] == vol and o["bucket"] == bucket and o["mag_pub"] > 0
          and o["d_crater"] is not None and (desde is None or o["datetime_utc"][:10] >= desde)]
    if not xs:
        return {"n": 0}
    dc = [o["d_crater"] for o in xs]
    dp = [o["d_pico"] for o in xs if o["d_pico"] is not None]
    return {"n": len(xs), "d_crater_mediana": round(mediana(dc), 2),
            "frac_crater_<=0.5": round(sum(1 for d in dc if d <= 0.5) / len(dc), 3),
            "n_con_pico": len(dp),
            "d_pico_mediana": round(mediana(dp), 2) if dp else None,
            "frac_pico_<=0.5": round(sum(1 for d in dp if d <= 0.5) / len(dp), 3) if dp else None,
            "frac_centroide_>1.5_y_pico_<=0.5": round(sum(
                1 for o in xs if o["d_pico"] is not None and o["d_crater"] > 1.5 and o["d_pico"] <= 0.5) / len(xs), 3),
            "frac_single_pixel_mode": round(sum(1 for o in xs if o["single_pixel_mode"]) / len(xs), 3),
            "n_pixels_mediana": mediana([o["n_pixels"] for o in xs if o["n_pixels"] is not None])}


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ancla", choices=["vent", "catalogo"], default="vent")
    ap.add_argument("--desde", default="2026-04-01")
    ap.add_argument("--tol-min", type=float, default=20.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out_path = args.out or os.path.join(HERE, "resultados.json" if args.ancla == "vent"
                                        else "resultados_ancla_catalogo.json")

    anclas, inner, faltan = cargar_anclas(args.ancla)
    anclas_cat, _, _ = cargar_anclas("catalogo")
    print(f"ANCLA = {args.ancla} | desde {args.desde} | tolerancia ±{args.tol_min:.0f} min")
    if faltan:
        print("  ¡volcanes SIN vent_lat/vent_lon (cayeron a catálogo)!:", faltan)

    # 1 · records nuestros, dedupe P4
    descr, dedupe = [], {}
    for vol in TIER:
        recs, info = cargar_records(vol, args.desde)
        dedupe[vol] = info
        for r in recs:
            descr.append(describir(r, vol, anclas[vol], inner[vol], anclas_cat[vol]))
    ultimo = max(o["datetime_utc"] for o in descr)
    print(f"records en ventana (dedupe): {len(descr)} · último {ultimo} · duplicados: "
          f"{sum(v['n_duplicados'] for v in dedupe.values())} "
          f"(con pc.vrp distinto: {sum(v['n_duplicados_con_pc_vrp_distinto'] for v in dedupe.values())})")
    print("  sensores:", dict(Counter(o["sensor"] for o in descr)))

    # instrumento: ¿centroid_dist_km del pipeline mide desde la misma ancla que yo?
    chk = {}
    for vol in TIER:
        dd = [abs(o["centroid_dist_km_pipeline"] - o["d_crater"]) for o in descr
              if o["vol"] == vol and o["centroid_dist_km_pipeline"] is not None and o["d_crater"] is not None]
        chk[vol] = {"n": len(dd), "mediana_abs_diff_km": round(mediana(dd), 3) if dd else None,
                    "p95_abs_diff_km": round(float(np.percentile(dd, 95)), 3) if dd else None}

    # 2 · ground truth MIROVA
    alertas = [a for a in load_mirova_alertas(cons_path=CONS, ocr_path=OCR)
               if a["volcano"] in TIER and a["sensor_bucket"] in SENSORES
               and (a["fecha_utc"] or "")[:10] >= args.desde and (a["vrp_mw"] or 0) > 0]
    fin_mir = max(a["fecha_utc"] for a in alertas)
    print(f"ALERTAS MIROVA (CONS∪OCR) en ventana: {len(alertas)} · última {fin_mir} · "
          f"fuentes {dict(Counter(a['source'] for a in alertas))}")
    # para los pares sólo cuentan nuestros records hasta el fin del snapshot MIROVA
    descr_par = [o for o in descr if o["datetime_utc"] <= fin_mir]

    pares, ours_sin_mir, mir_sin_pasada, mir_pasada_sin_pub, ambiguas = parear(descr_par, alertas, args.tol_min)
    print(f"PARES (mag_pub>0): {len(pares)} · MIROVA sin pasada nuestra: {len(mir_sin_pasada)} · "
          f"MIROVA con pasada nuestra sin publicar (FN): {len(mir_pasada_sin_pub)} · "
          f"nuestros publicados sin MIROVA: {len(ours_sin_mir)} · alertas con ≥2 granules a ±tol: {ambiguas}")
    print("  |dt| pares (min): mediana %.1f · p95 %.1f" % (
        mediana([abs(p["dt_min"]) for p in pares]), np.percentile([abs(p["dt_min"]) for p in pares], 95)))

    # 3 · los tres conjuntos por sensor y volcán
    conjuntos = {}
    for s in SENSORES:
        for vol in TIER:
            f = lambda L: sum(1 for x in L if (x.get("vol") or x.get("volcano")) == vol
                              and (x.get("bucket") or x.get("sensor_bucket")) == s)
            conjuntos[f"{vol}|{s}"] = {
                "pares": f(pares), "mirova_sin_pasada_nuestra": f(mir_sin_pasada),
                "mirova_con_pasada_sin_publicar_FN": f(mir_pasada_sin_pub),
                "nuestros_publicados_sin_mirova": f(ours_sin_mir),
                "alertas_mirova_total": f(alertas)}

    # 4 · paridad por sensor × bin (magnitud del operador)
    por_sensor = {s: tabla_bins([p for p in pares if p["bucket"] == s]) for s in SENSORES}
    por_sensor_dpico = {s: tabla_bins([p for p in pares if p["bucket"] == s], clave_d="d_pico") for s in SENSORES}
    # por volcán × sensor × bin
    por_vol = {}
    for vol in TIER:
        por_vol[vol] = {s: tabla_bins([p for p in pares if p["bucket"] == s and p["vol"] == vol]) for s in SENSORES}

    # 5 · criterio pre-registrado (VIIRS375) + versión agrupando sensores (informativa)
    v375 = [p for p in pares if p["bucket"] == "VIIRS375"]
    crit = criterio(v375)
    crit_todos = criterio(pares)
    crit_todos["regla"] += " — VARIANTE INFORMATIVA con los 3 sensores juntos"

    # 6 · estrato MODIS doble (y los otros dos, etiquetados): sólo summit (operador) vs summit∪far con pc.vrp_mw
    # Para summit∪far hay que re-parear con mag_pc como magnitud.
    descr_pc = []
    for o in descr_par:
        q = dict(o)
        q["mag_pub"] = q["mag_pc"]
        descr_pc.append(q)
    pares_pc, _, _, mir_sin_pub_pc, _ = parear(descr_pc, alertas, args.tol_min)
    estrato_doble = {}
    for s in SENSORES:
        ps = [p for p in pares if p["bucket"] == s]
        pp = [p for p in pares_pc if p["bucket"] == s]
        estrato_doble[s] = {
            "solo_summit_operador": {"n_pares": len(ps), "razon": resumen_razon([p["razon_pub"] for p in ps]),
                                     "bins": {b: por_sensor[s][b] for b, _, _ in BINS}},
            "summit_U_far_pc_vrp": {"n_pares": len(pp), "razon": resumen_razon([p["razon_pc"] for p in pp]),
                                    "bins": tabla_bins(pp, clave_razon="razon_pc"),
                                    "clase": dict(Counter(p["distance_class"] for p in pp)),
                                    "FN_restantes": sum(1 for p in mir_sin_pub_pc if p["bucket"] == s)},
        }
    # control negativo: los records far pareados (magnitud pc.vrp_mw)
    far = [p for p in pares_pc if p["distance_class"] == "far"]
    ctrl_negativo = {s: resumen_razon([p["razon_pc"] for p in far if p["bucket"] == s]) for s in SENSORES}

    # 7 · posición: d_crater vs d_pico por volcán × sensor (records publicados desde --desde y desde 2026-06-01)
    posicion = {vol: {s: posicion_por_vol(descr, vol, s) for s in SENSORES} for vol in TIER}
    posicion_jun = {vol: {s: posicion_por_vol(descr, vol, s, "2026-06-01") for s in SENSORES} for vol in TIER}

    # 8 · controles
    lascar_v375_jun = posicion_jun["Lascar"]["VIIRS375"]
    al_lascar_jun = [a for a in alertas if a["volcano"] == "Lascar" and a["sensor_bucket"] == "VIIRS375"
                     and a["fecha_utc"][:10] >= "2026-06-01"]
    con_par = sum(1 for p in pares + mir_pasada_sin_pub if p["vol"] == "Lascar" and p["bucket"] == "VIIRS375"
                  and p["datetime_utc"][:10] >= "2026-06-01")
    con_pub = sum(1 for p in pares if p["vol"] == "Lascar" and p["bucket"] == "VIIRS375"
                  and p["datetime_utc"][:10] >= "2026-06-01")
    controles = {
        "positivo_lascar_v375_desde_2026-06-01": {**lascar_v375_jun,
                                                  "esperado_S133": {"mediana_km": 0.22, "frac_500m": 0.79, "n": 208},
                                                  "pasa": bool(lascar_v375_jun.get("n") and lascar_v375_jun["d_crater_mediana"] <= 0.4
                                                               and lascar_v375_jun["frac_crater_<=0.5"] >= 0.6)},
        "pareo_lascar_v375_desde_2026-06-01": {"alertas_mirova": len(al_lascar_jun),
                                               "con_pasada_nuestra_±tol": con_par,
                                               "con_pasada_publicada": con_pub,
                                               "frac_con_pasada": round(con_par / len(al_lascar_jun), 3) if al_lascar_jun else None,
                                               "pasa": bool(al_lascar_jun) and con_par / len(al_lascar_jun) >= 0.5},
        "negativo_far_razon_pc": ctrl_negativo,
        "villarrica_d_crater_mediana_v375_publicados": posicion["Villarrica"]["VIIRS375"].get("d_crater_mediana"),
        "centroid_dist_km_pipeline_vs_mi_haversine": chk,
        "f5_fallback_en_pares_v375": {"n_pares": len(v375),
                                      "n_fallback_a_pc": sum(1 for p in v375 if p["f5_fallback"]),
                                      "n_sin_campo_f5": sum(1 for p in v375 if not p["f5_presente"])},
        "artefactos_frontend_en_pares": dict(Counter((p["bucket"], p["artefacto_frontend"]) for p in pares if p["artefacto_frontend"])),
        "single_pixel_mode_en_pares": {s: {"n": sum(1 for p in pares if p["bucket"] == s),
                                           "n_single_pixel_mode": sum(1 for p in pares if p["bucket"] == s and p["single_pixel_mode"])}
                                       for s in SENSORES},
    }

    # 9 · (añadido en la retoma) ¿DÓNDE está el cúmulo en los pares vs en lo que MIROVA NO publica?
    # Es el eje espacial de A83: si el anillo vive en los no-pares, la paridad no puede depender de él.
    def pos_resumen(xs):
        dc = [o["d_crater"] for o in xs if o["d_crater"] is not None]
        if not dc:
            return {"n": 0}
        on = [o["off_n_km"] for o in xs if o["off_n_km"] is not None]
        oe = [o["off_e_km"] for o in xs if o["off_e_km"] is not None]
        cuad = Counter(("N" if a > 0 else "S") + ("E" if b > 0 else "W") for a, b in zip(on, oe))
        return {"n": len(dc), "d_crater_mediana": round(mediana(dc), 2),
                "frac_<=0.5": round(sum(1 for d in dc if d <= 0.5) / len(dc), 3),
                "frac_>1.5": round(sum(1 for d in dc if d > 1.5) / len(dc), 3),
                "offset_mediano_N_km": round(mediana(on), 2), "offset_mediano_E_km": round(mediana(oe), 2),
                "iqr_N_km": [round(float(np.percentile(on, 25)), 2), round(float(np.percentile(on, 75)), 2)],
                "iqr_E_km": [round(float(np.percentile(oe, 25)), 2), round(float(np.percentile(oe, 75)), 2)],
                "cuadrantes": dict(cuad)}
    pares_vs_sin = {}
    for vol in TIER:
        pares_vs_sin[vol] = {}
        for s in SENSORES:
            pares_vs_sin[vol][s] = {
                "pares_mirova_confirma": pos_resumen([p for p in pares if p["vol"] == vol and p["bucket"] == s]),
                "nuestros_sin_mirova": pos_resumen([o for o in ours_sin_mir if o["vol"] == vol and o["bucket"] == s]),
            }

    # 10 · la razón contra otras covariables (¿de qué SÍ depende, si no de la posición?)
    def tabla_cov(ps, clave, cortes):
        out = {}
        for lo, hi in cortes:
            rs = [p["razon_pub"] for p in ps if p.get(clave) is not None and lo <= p[clave] < hi]
            out[f"[{lo},{hi})"] = resumen_razon(rs)
        return out
    covariables = {}
    for s in SENSORES:
        ps = [p for p in pares if p["bucket"] == s]
        covariables[s] = {
            "n_anomaly_pixels_nuestros": tabla_cov(ps, "n_anomaly_pixels", [(1, 2), (2, 4), (4, 10), (10, 100000)]),
            "vrp_mirova_mw": tabla_cov(ps, "mir_vrp", [(0, 0.3), (0.3, 1), (1, 3), (3, 1e9)]),
            "zenith_deg": tabla_cov(ps, "zenith", [(0, 20), (20, 40), (40, 90)]),
            "single_pixel_mode": {str(k): resumen_razon([p["razon_pub"] for p in ps if bool(p["single_pixel_mode"]) == k])
                                  for k in (True, False)},
            "n_exactamente_1_anomaly_pixel": sum(1 for p in ps if p["n_anomaly_pixels"] == 1),
        }

    # 11 · nuestra distancia desde el CATÁLOGO vs Distancia_km de MIROVA en el MISMO par (indicativo, D15)
    def dist_vs_mirova(ps):
        dd = [(p["d_catalogo"], p["mir_dist_km"]) for p in ps if p["d_catalogo"] is not None and p["mir_dist_km"] is not None]
        if not dd:
            return {"n": 0}
        dif = [a - b for a, b in dd]
        return {"n": len(dd), "ours_catalogo_mediana_km": round(mediana([a for a, _ in dd]), 2),
                "mirova_dist_mediana_km": round(mediana([b for _, b in dd]), 2),
                "diff_mediana_km": round(mediana(dif), 2),
                "diff_iqr_km": [round(float(np.percentile(dif, 25)), 2), round(float(np.percentile(dif, 75)), 2)],
                "n_mirova_dist_0": sum(1 for _, b in dd if b == 0),
                "valores_mirova_mas_comunes": [[round(v, 2), c] for v, c in Counter(round(b, 2) for _, b in dd).most_common(4)]}
    dist_par = {s: {"todos": dist_vs_mirova([p for p in pares if p["bucket"] == s]),
                    "por_fuente": {src: dist_vs_mirova([p for p in pares if p["bucket"] == s and p["mir_source"] == src]) for src in ("CONS", "OCR")},
                    "por_volcan": {vol: dist_vs_mirova([p for p in pares if p["bucket"] == s and p["vol"] == vol]) for vol in TIER}}
                for s in SENSORES}
    # ¿la razón depende del DESACUERDO de posición con MIROVA?
    razon_vs_desacuerdo = {}
    for s in SENSORES:
        ps = [dict(p, desac=abs(p["d_catalogo"] - p["mir_dist_km"])) for p in pares
              if p["bucket"] == s and p["d_catalogo"] is not None and p["mir_dist_km"] is not None]
        razon_vs_desacuerdo[s] = tabla_cov(ps, "desac", [(0, 0.5), (0.5, 1.5), (1.5, 3), (3, 1e9)])

    # 12 · pareo: FN que tienen OTRO granule nuestro publicado a ±tol (ambigüedad que castiga de más)
    pt = defaultdict(list)
    for p in pares:
        pt[(p["vol"], p["bucket"])].append(p["t"])
    fn_con_vecino_pub = sum(1 for f in mir_pasada_sin_pub
                            if any(abs((x - f["t"]).total_seconds()) <= args.tol_min * 60 for x in pt[(f["vol"], f["bucket"])]))
    fn_detalle = {"n_FN": len(mir_pasada_sin_pub), "n_FN_con_otro_granule_publicado_±tol": fn_con_vecino_pub,
                  "por_bucket_clase": {f"{k[0]}|{k[1]}": v for k, v in Counter((f["bucket"], f["distance_class"]) for f in mir_pasada_sin_pub).items()},
                  "n_FN_con_pc_vrp>0": sum(1 for f in mir_pasada_sin_pub if f["mag_pc"] > 0),
                  "vrp_mirova_mediana_FN": round(mediana([f["mir_vrp"] for f in mir_pasada_sin_pub]), 3) if mir_pasada_sin_pub else None,
                  "sin_pasada_por_bucket_vol": {f"{k[0]}|{k[1]}": v for k, v in Counter((a["sensor_bucket"], a["volcano"]) for a in mir_sin_pasada).most_common()}}

    # 13 · MODIS far pareado (summit ∪ far): ¿dónde está el cúmulo?
    modis_far_pos = pos_resumen([p for p in pares_pc if p["bucket"] == "MODIS" and p["distance_class"] == "far"])

    # ----------------------------------------------------------------- impresión
    print("\n== CONTROLES ==")
    print(json.dumps(controles["positivo_lascar_v375_desde_2026-06-01"], ensure_ascii=False))
    print(json.dumps(controles["pareo_lascar_v375_desde_2026-06-01"], ensure_ascii=False))
    print("Villarrica d_crater mediana V375 publicados:", controles["villarrica_d_crater_mediana_v375_publicados"])
    print("centroid_dist_km pipeline vs mi haversine (mediana |diff| km):",
          {v: c["mediana_abs_diff_km"] for v, c in chk.items()})

    print("\n== PARIDAD por sensor × bin d_crater (razón ours/MIROVA, magnitud del operador) ==")
    for s in SENSORES:
        t = por_sensor[s]
        print(f"[{s}] n={t['todos']['n']} mediana={t['todos']['mediana']} IC={t['todos']['ic95']} "
              f"spearman={t['spearman_razon_vs_d']}")
        for b, _, _ in BINS:
            x = t[b]
            print(f"   {b:>7}: n={x['n']:4d} med={x['mediana']} IC={x['ic95']} >1.4:{x['n_sobre_1.4']} <0.7:{x['n_bajo_0.7']} banda:{x['n_en_banda']}")

    print("\n== CRITERIO PRE-REGISTRADO (VIIRS375, 9 volcanes con anillo) ==")
    for vol, f in crit["por_volcan"].items():
        c, l = f["cerca_<=0.5"], f["lejos_>1.5"]
        print(f"  {vol:20s} pares={f['n_pares']:3d} cerca n={c['n']:3d} med={c['mediana']} IC={c['ic95']} | "
              f"lejos n={l['n']:3d} med={l['mediana']} IC={l['ic95']} | cumple={f['cumple']}")
    print(f"  → evaluables {crit['volcanes_evaluables']}/9 · cumplen {crit['volcanes_que_cumplen']} · {crit['veredicto']}")

    print("\n== POSICIÓN d_crater vs d_pico (records publicados desde %s) ==" % args.desde)
    for vol in TIER:
        for s in SENSORES:
            x = posicion[vol][s]
            if x["n"]:
                print(f"  {vol:20s} {s:8s} n={x['n']:4d} d_crater med={x['d_crater_mediana']} (<=0.5: {x['frac_crater_<=0.5']}) "
                      f"d_pico med={x['d_pico_mediana']} (<=0.5: {x['frac_pico_<=0.5']}) "
                      f"centro>1.5&pico<=0.5: {x['frac_centroide_>1.5_y_pico_<=0.5']} spm={x['frac_single_pixel_mode']}")

    print("\n== ESTRATO DOBLE (solo summit vs summit∪far con pc.vrp_mw) ==")
    for s in SENSORES:
        e = estrato_doble[s]
        print(f"  {s}: summit n={e['solo_summit_operador']['n_pares']} med={e['solo_summit_operador']['razon']['mediana']} | "
              f"summit∪far n={e['summit_U_far_pc_vrp']['n_pares']} med={e['summit_U_far_pc_vrp']['razon']['mediana']} "
              f"clases={e['summit_U_far_pc_vrp']['clase']} FN_restantes={e['summit_U_far_pc_vrp']['FN_restantes']}")

    print("\n== POSICIÓN del cúmulo V375: pares (MIROVA confirma) vs nuestros sin MIROVA ==")
    for vol in TIER:
        a, b = pares_vs_sin[vol]["VIIRS375"]["pares_mirova_confirma"], pares_vs_sin[vol]["VIIRS375"]["nuestros_sin_mirova"]
        print(f"  {vol:20s} pares n={a.get('n',0):3d} med={a.get('d_crater_mediana')} <=0.5:{a.get('frac_<=0.5')} "
              f"| sin MIROVA n={b.get('n',0):3d} med={b.get('d_crater_mediana')} <=0.5:{b.get('frac_<=0.5')} "
              f"offN={b.get('offset_mediano_N_km')} offE={b.get('offset_mediano_E_km')} cuad={b.get('cuadrantes')}")
    print("\n== RAZÓN vs covariables (V375) ==")
    for k, v in covariables["VIIRS375"].items():
        if isinstance(v, dict):
            print(f"  {k}: " + " · ".join(f"{b} n={x['n']} med={x['mediana']}" for b, x in v.items()))
        else:
            print(f"  {k}: {v}")
    print("\n== d_catalogo nuestra vs Distancia_km MIROVA (V375) ==")
    print("  ", dist_par["VIIRS375"]["todos"])
    print("  razón vs |desacuerdo|:", {b: (x["n"], x["mediana"]) for b, x in razon_vs_desacuerdo["VIIRS375"].items()})
    print("\n== FN ==", json.dumps(fn_detalle, ensure_ascii=False))
    print("== MODIS far pareado, posición ==", modis_far_pos)

    print("\n== LOS TRES CONJUNTOS por sensor ==")
    for s in SENSORES:
        agg = Counter()
        for vol in TIER:
            for k, v in conjuntos[f"{vol}|{s}"].items():
                agg[k] += v
        print(f"  {s}: {dict(agg)}")

    # ----------------------------------------------------------------- JSON
    def limpiar(p):
        q = {k: v for k, v in p.items() if k not in ("t", "mir_t")}
        for k in ("d_crater", "d_pico", "razon_pub", "razon_pc", "dt_min", "mag_pub", "mag_pc", "pico_vrp",
                  "d_catalogo", "off_n_km", "off_e_km"):
            if q.get(k) is not None:
                q[k] = round(q[k], 4)
        return q

    salida = {
        "meta": {"ancla": args.ancla, "desde": args.desde, "tol_min": args.tol_min,
                 "ultimo_record_en_disco": ultimo, "ultima_alerta_mirova": fin_mir,
                 "n_records_ventana_dedupe": len(descr), "n_alertas_mirova_ventana": len(alertas),
                 "n_pares": len(pares), "n_ambiguas": ambiguas, "banda": BANDA, "n_boot": N_BOOT,
                 "volcanes_sin_vent": faltan, "anclas_usadas": anclas, "inner_km": inner,
                 "criterio_preregistrado": crit["regla"]},
        "dedupe_P4": dedupe,
        "controles": controles,
        "criterio": crit,
        "criterio_variante_3_sensores": crit_todos,
        "paridad_por_sensor_bin_d_crater": por_sensor,
        "paridad_por_sensor_bin_d_pico": por_sensor_dpico,
        "paridad_por_volcan_sensor_bin": por_vol,
        "estrato_doble_summit_vs_summit_U_far": estrato_doble,
        "posicion_d_crater_vs_d_pico_desde": posicion,
        "posicion_d_crater_vs_d_pico_desde_2026-06-01": posicion_jun,
        "tres_conjuntos": conjuntos,
        "posicion_pares_vs_nuestros_sin_mirova": pares_vs_sin,
        "razon_vs_covariables": covariables,
        "d_catalogo_vs_distancia_mirova_por_par": dist_par,
        "razon_vs_desacuerdo_posicion_con_mirova": razon_vs_desacuerdo,
        "fn_detalle": fn_detalle,
        "modis_far_pareado_posicion": modis_far_pos,
        "pares": [limpiar(p) for p in pares],
        "mirova_con_pasada_sin_publicar_FN": [limpiar(p) for p in mir_pasada_sin_pub],
        "mirova_sin_pasada_nuestra": [{"vol": a["volcano"], "bucket": a["sensor_bucket"], "fecha_utc": a["fecha_utc"],
                                       "vrp_mw": a["vrp_mw"], "dist_km": a["dist_km"], "source": a["source"]}
                                      for a in mir_sin_pasada],
        "nuestros_publicados_sin_mirova_resumen": {s: {vol: sum(1 for o in ours_sin_mir if o["vol"] == vol and o["bucket"] == s)
                                                       for vol in TIER} for s in SENSORES},
    }
    json.dump(salida, io.open(out_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    print("\nescrito:", out_path)


if __name__ == "__main__":
    main()
