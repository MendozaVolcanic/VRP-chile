#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auto-audit semanal de paridad vs MIROVA (S120, propuesta §8 AUDIT_S119).

POR QUÉ (fenómeno → mecanismo): la paridad con MIROVA se validaba en auditorías
episódicas (A51, cada ~20 sesiones). Entre auditorías, una regresión silenciosa
(un flip de flag, un cambio NASA, un drift del ground truth) puede correr semanas
sin detección. Este script empaqueta los criterios EXACTOS del Eje 2 de la
auditoría S119 (experiments/_s119_audit/eje2_recall_magnitud.py) en una corrida
semanal con ventana rodante → data/audit_continuous/latest.json. El workflow
audit-weekly.yml lo corre por cron y abre un issue si algo sale de banda.

Criterios (idénticos a S119, regla S91 — no re-derivar):
  - CRÁTER: pc.vrp_mw>0 AND pc.centroid_dist_km<=inner AND vrp<=50000 (A10).
  - DASHBOARD: CRÁTER AND distance_class in {summit, None}.
  - Recall por bucket de sensor sobre noches ALERTA del loader canónico (A11).
  - Magnitud: mediana per-vol de max(dash)/max(MIROVA VRP) por noche común.

Bandas (referencia S119 − margen 5pp; magnitud banda paridad [0.5, 2.0]):
  - recall crater VIIRS375 >= 93.4 (ref 98.4), VIIRS750 >= 79.5 (ref 84.5),
    MODIS >= 95.0 (ref 100) — solo si n_noches >= MIN_N_RECALL.
  - magnitud: vol fuera de banda con n>=5 → flag. Excepción documentada:
    Lastarria sub-banda es cat-b Lazufre conocido (AUDIT_S119 §2.3) — solo
    flaggea si ratio > 2.0 (sobre-estimación, que sí sería nuevo).
  - integridad: parse errors o duplicados (datetime_utc, sensor) > 0 → flag.
"""
import sys
import io
import json
import os
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402
from pipeline.store import _reject_daytime, _solar_elevation  # noqa: E402
from pipeline.profile import ENABLE_DAYTIME_MODIS  # noqa: E402
import yaml  # noqa: E402

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
CONS = os.path.join(SNAP, "registro_vrp_consolidado.csv")
OCR = os.path.join(SNAP, "registro_vrp_ocr.csv")
OUTDIR = os.path.join(ROOT, "data", "audit_continuous")
VOLCANOES_YAML = os.path.join(ROOT, "volcanoes.yaml")

WINDOW_DAYS = 60
MIN_N_RECALL = 15   # noches ALERTA mínimas para que el recall del bucket sea flaggeable
MIN_N_RATIO = 5     # noches comunes mínimas para que el ratio per-vol sea flaggeable

# --- S124: guarda de COBERTURA ---
# Sin esto la auditoría tiene una asimetría perversa: grita cuando fallamos
# nosotros y se calla cuando falla la REFERENCIA. Dos modos concretos, ambos
# ya ocurridos:
#   (a) el NRT se cae (20-jul→04-ago, token expirado) y MIROVA sigue publicando
#       → las noches en que no miramos entran al DENOMINADOR del recall y el
#       veredicto culpa a la detección. Abrió 3 issues seguidos por un problema
#       que no era de detección (#499/#500/#504).
#   (b) el scraper de mirovaweb se congela → en la ventana rodante `n` cae bajo
#       los mínimos, los flags se SALTAN y el veredicto sale VERDE. La referencia
#       muerta se lee como "todo bien".
# Un veredicto solo es interpretable si la ventana tuvo cobertura de AMBOS lados.
MAX_GT_STALE_DAYS = 7      # días sin ALERTA nueva de MIROVA → referencia sospechosa
MIN_COVERAGE_PCT = 80.0    # % de días de la ventana con datos nuestros

VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten",
        "Tupungatito", "Copahue", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "NevadosDeChillan"]
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
         "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
SENSORS = ["MODIS", "VIIRS750", "VIIRS375"]
CAP = 50000
RECALL_MIN = {"VIIRS375": 93.4, "VIIRS750": 79.5, "MODIS": 95.0}
# --- S124: DOS bandas, no una ---
# `~memory/reference_paridad_mirova_umbrales.md` las distingue por una razón
# física. MIROVA declara ±30 % de error en el método MIR, así que el ratio de una
# noche PUNTUAL fluctúa naturalmente entre 0,54 y 1,85 sin que haya nada roto —
# de ahí la banda ancha. Pero una MEDIANA sobre decenas de noches ya no fluctúa:
# textual, *"más estricto que individual porque mide tendencia central, no
# outliers puntuales. Mediana 2.0 = sesgo sistemático, no ruido"*.
#
# Hasta S124 este script aplicaba la banda ANCHA a la mediana: 4× de ancho donde
# el criterio propio pide 2×. Con eso, cuatro volcanes sub-reportando 35-50 %
# quedaban invisibles (Lascar 0,62 · Isluga 0,61 · Lastarria 0,47 · Llaima 0,36)
# y dos selecciones de cluster que difieren 17 % "pasaban" las dos.
# Ver docs/S124_LA_PARIDAD_ESCONDE_UN_PROBLEMA.md.
RATIO_BAND_INDIVIDUAL = (0.5, 2.0)   # una detección suelta (referencia, no se usa acá)
RATIO_BAND_MEDIAN = (0.7, 1.4)       # la mediana per-volcán: lo que este script juzga
RATIO_BAND = RATIO_BAND_MEDIAN       # compat con lectores externos del módulo
# Excepciones físicas documentadas (AUDIT_S119 §2.3): sub-banda esperada, no flaggear.
UNDER_BAND_KNOWN = {"Lastarria"}


def evaluar_ratio_mediano(volcan: str, ratio: float, n_noches: int):
    """Veredicto del ratio mediano de un volcán. None = en banda / no concluyente.

    Devuelve un texto que NOMBRA el hallazgo S124, para que el déficit de
    régimen débil ya documentado no se lea como una regresión nueva cada semana.
    """
    if n_noches < MIN_N_RATIO:
        return None
    lo, hi = RATIO_BAND_MEDIAN
    if ratio > hi:
        return (f"magnitud {volcan} {ratio}x > {hi} (SOBRE-estima, n={n_noches})")
    if ratio < lo and volcan not in UNDER_BAND_KNOWN:
        return (f"magnitud {volcan} {ratio}x < {lo} (SUB-estima, n={n_noches}) "
                f"— déficit de régimen débil S124, ver "
                f"docs/S124_LA_PARIDAD_ESCONDE_UN_PROBLEMA.md")
    return None


# --- S124: no evaluarnos con pasadas DIURNAS de MIROVA ---
# De día el Sol reflejado en nube o nieve entra en la banda MIR de 3,7-4 µm con
# intensidad comparable a la de un foco incandescente: el sensor no distingue
# "caliente" de "brillante". MIROVA publica de vez en cuando alertas diurnas que
# son reflexión (A76); nuestro pipeline las descarta por diseño. Sin este filtro
# esas pasadas entraban al DENOMINADOR del recall y nos penalizaban por no ver
# lo que decidimos no mirar (82 de 1338 alertas = 6,1 % en la ventana S124; en
# Nevados de Chillán la alerta MÁS GRANDE del período era diurna).
#
# Se reusa `_reject_daytime` de store.py A PROPÓSITO en vez de un umbral propio:
# la auditoría debe excluir EXACTAMENTE lo que el pipeline excluye. Si algún día
# se activa MODIS diurno (ENABLE_DAYTIME_MODIS), la auditoría lo sigue sola.
_BUCKET_SENSOR = {"MODIS": "MODIS_TERRA",
                  "VIIRS375": "VIIRS_SNPP",       # sin sufijo = I-band 375 m (A48)
                  "VIIRS750": "VIIRS_SNPP_750"}


def bucket_representative_sensor(bucket: str) -> str:
    """Nombre de sensor representativo del bucket, en la convención del proyecto."""
    return _BUCKET_SENSOR.get(bucket, bucket)


def es_pasada_diurna_descartada(bucket, lat, lon, dt_utc) -> bool:
    """¿El pipeline habría descartado esta pasada por diurna?"""
    elev = _solar_elevation(lat, lon, dt_utc)
    return _reject_daytime(bucket_representative_sensor(bucket), elev,
                           ENABLE_DAYTIME_MODIS)


def _coords_por_volcan():
    with open(VOLCANOES_YAML, encoding="utf-8") as fh:
        return {v["name"]: (v["lat"], v["lon"])
                for v in yaml.safe_load(fh)["volcanoes"] if "lat" in v}


def our_bucket(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    if sensor.endswith("_750"):
        return "VIIRS750"
    if sensor.startswith("VIIRS"):
        return "VIIRS375"
    return None


def _csv_ultima_fecha(path):
    """Fecha más reciente registrada en el CSV MIROVA (cualquier Tipo_Registro).

    Devuelve 'YYYY-MM-DD' o None si no se puede leer. Incluye RUTINA a
    propósito: es lo que distingue "el scraper murió" de "no hubo actividad".
    """
    try:
        import csv as _csv
        with open(path, encoding="utf-8", errors="replace") as fh:
            fechas = [r.get("Fecha_Satelite_UTC") or "" for r in _csv.DictReader(fh)]
        fechas = [f[:10] for f in fechas if f[:4].isdigit()]
        return max(fechas) if fechas else None
    except (OSError, KeyError):
        return None


def main():
    today = datetime.now(timezone.utc).date()
    win = ((today - timedelta(days=WINDOW_DAYS)).isoformat(), today.isoformat())

    def in_win(dt):
        return bool(dt) and win[0] <= dt[:10] <= win[1]

    # 1. MIROVA (loader canónico, CONS ∪ OCR): noches ALERTA por (vol, bucket, fecha)
    alertas = load_mirova_alertas(cons_path=CONS, ocr_path=OCR)
    coords = _coords_por_volcan()
    mir = defaultdict(float)
    n_diurnas_excluidas = 0
    for a in alertas:
        dt = a["fecha_utc"] or ""
        if not in_win(dt) or a["sensor_bucket"] not in SENSORS:
            continue
        # S124: las pasadas diurnas no nos evalúan — el pipeline no las mira.
        latlon = coords.get(a["volcano"])
        if latlon:
            try:
                dt_obj = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
            except ValueError:
                dt_obj = None
            if dt_obj and es_pasada_diurna_descartada(a["sensor_bucket"],
                                                      latlon[0], latlon[1], dt_obj):
                n_diurnas_excluidas += 1
                continue
        key = (a["volcano"], a["sensor_bucket"], dt[:10])
        mir[key] = max(mir[key], a["vrp_mw"] or 0.0)

    # 2. Nuestros records (mismos criterios crater/dash del eje2 S119) + integridad
    ours = defaultdict(lambda: {"crater": [], "dash": [], "npix": []})
    integrity = {"parse_errors": [], "duplicates_total": 0}
    for vol in VOLS:
        path = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 — A47-style corrupción es justo lo vigilado
            integrity["parse_errors"].append(f"{vol}: {e}")
            continue
        seen = set()
        for rec in d["records"]:
            k2 = (rec.get("datetime_utc"), rec.get("sensor"))
            if k2 in seen:
                integrity["duplicates_total"] += 1
            seen.add(k2)
            dt = rec.get("datetime_utc")
            if not in_win(dt):
                continue
            b = our_bucket(rec.get("sensor", ""))
            if b is None:
                continue
            pc = rec.get("primary_cluster") or {}
            vrp = pc.get("vrp_mw") or 0.0
            cdist = pc.get("centroid_dist_km")
            if (0 < vrp <= CAP) and (cdist is not None and cdist <= INNER[vol]):
                key = (vol, b, dt[:10])
                ours[key]["crater"].append(vrp)
                dclass = rec.get("distance_class")
                if not dclass or dclass == "summit":
                    ours[key]["dash"].append(vrp)
                    # S124: el conteo de pixeles es la variable que estratifica
                    # los DOS modos de falla (ver bloque de estratificación).
                    ours[key]["npix"].append(len(rec.get("anomaly_pixels") or []))

    # 3. Recall por sensor + magnitud per-vol
    agg = {s: {"n": 0, "c": 0, "d": 0} for s in SENSORS}
    ratios_by_vol = defaultdict(list)
    ratios_by_npix = defaultdict(list)
    for (vol, s, date), mvrp in mir.items():
        if vol not in VOLS:
            continue
        agg[s]["n"] += 1
        o = ours.get((vol, s, date))
        if o and o["crater"]:
            agg[s]["c"] += 1
        if o and o["dash"]:
            agg[s]["d"] += 1
            if mvrp > 0:
                _r = max(o["dash"]) / mvrp
                ratios_by_vol[vol].append(_r)
                # S124 — estratificación por conteo de píxeles. La mediana sola
                # promedia dos modos de falla OPUESTOS y los vuelve invisibles:
                # en régimen débil (1-2 px) sub-integramos y en campo difuso
                # (6+ px) sobre-integramos. Publicar los bins es lo que impide
                # que se vuelva a esconder.
                #
                # OJO al leerlo: acá los bins se agrupan sobre los 11 volcanes y
                # sobre el valor del DASHBOARD (pc.vrp intra-inner, summit). El
                # análisis de docs/S124_LA_PARIDAD_ESCONDE_UN_PROBLEMA.md es
                # per-volcán y sobre la escena COMPLETA, por eso ahí el patrón
                # sale monótono y acá no: agrupar mezcla regímenes distintos.
                # Este bin sirve como señal de deriva semana a semana, no como
                # medición del gap — para eso, el script per-volcán.
                _n = max(o["npix"]) if o["npix"] else 0
                _bin = ("1px" if _n == 1 else "2px" if _n == 2
                        else "3-5px" if _n <= 5 else "6+px")
                ratios_by_npix[_bin].append(_r)

    recall = {}
    for s in SENSORS:
        n = agg[s]["n"]
        recall[s] = {"n_noches": n,
                     "recall_crater_pct": round(agg[s]["c"] / n * 100, 1) if n else None,
                     "recall_dash_pct": round(agg[s]["d"] / n * 100, 1) if n else None}
    magnitud = {v: {"n_noches": len(r), "ratio_mediano": round(statistics.median(r), 3)}
                for v, r in sorted(ratios_by_vol.items())}

    # 4. Flags contra bandas
    flags = []
    for s in SENSORS:
        r = recall[s]
        if r["n_noches"] >= MIN_N_RECALL and r["recall_crater_pct"] is not None \
                and r["recall_crater_pct"] < RECALL_MIN[s]:
            flags.append(f"recall {s} {r['recall_crater_pct']}% < banda {RECALL_MIN[s]}% "
                         f"(n={r['n_noches']})")
    for v, m in magnitud.items():
        veredicto = evaluar_ratio_mediano(v, m["ratio_mediano"], m["n_noches"])
        if veredicto:
            flags.append(veredicto)
    if integrity["parse_errors"]:
        flags.append(f"integridad: {len(integrity['parse_errors'])} JSON con parse error")
    if integrity["duplicates_total"]:
        flags.append(f"integridad: {integrity['duplicates_total']} records duplicados (datetime,sensor)")

    # --- S124: cobertura de la ventana, ANTES de interpretar los flags ---
    dias_ventana = WINDOW_DAYS + 1
    dias_nuestros = {d for (_v, _s, d) in ours.keys()}
    cobertura_pct = round(100.0 * len(dias_nuestros) / dias_ventana, 1)

    # Frescura del ground truth: se mide sobre TODO el CSV, no sobre las ALERTAS.
    # Un período sin alertas es información legítima (los volcanes pueden estar
    # tranquilos); lo que delata a un scraper muerto es que el archivo entero
    # deje de crecer, y el CSV trae también los registros de RUTINA (los "miré y
    # no había nada"), que se generan todos los días haya o no actividad.
    gt_ultima, gt_stale_dias = _csv_ultima_fecha(CONS), None
    if gt_ultima:
        # ojo: `date` se usa como nombre de variable en los loops de este script,
        # así que se parsea vía datetime para no depender del import sombreado.
        gt_stale_dias = (today - datetime.fromisoformat(gt_ultima).date()).days

    cobertura_avisos = []
    if cobertura_pct < MIN_COVERAGE_PCT:
        cobertura_avisos.append(
            f"cobertura propia {cobertura_pct}% < {MIN_COVERAGE_PCT}% "
            f"({len(dias_nuestros)}/{dias_ventana} días con datos): el recall de esta "
            f"ventana NO es interpretable — las noches sin datos cuentan como fallos")
    if gt_stale_dias is None:
        cobertura_avisos.append("no se pudo leer la fecha del ground truth: referencia sospechosa")
    elif gt_stale_dias > MAX_GT_STALE_DAYS:
        cobertura_avisos.append(
            f"ground truth stale: el CSV MIROVA no registra nada hace "
            f"{gt_stale_dias} días (> {MAX_GT_STALE_DAYS}) — es el scraper, no los volcanes")

    cobertura = {
        "cobertura_propia_pct": cobertura_pct,
        "dias_con_datos": len(dias_nuestros),
        "dias_ventana": dias_ventana,
        "gt_ultima_fecha_csv": gt_ultima,
        "gt_stale_dias": gt_stale_dias,
        # Transparencia: un filtro que descarta en silencio es tan malo como no
        # tenerlo. Si este número se dispara, es señal de otra cosa (A76).
        "alertas_diurnas_excluidas": n_diurnas_excluidas,
        "avisos": cobertura_avisos,
    }

    # DEGRADADO gana sobre todo: si no sabemos si la ventana es interpretable,
    # decirlo es más honesto que un VERDE o un FUERA_DE_BANDA que no se sostiene.
    if cobertura_avisos:
        verdict = "DEGRADADO"
    elif flags:
        verdict = "FUERA_DE_BANDA"
    else:
        verdict = "VERDE"

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": list(win),
        "cobertura": cobertura,
        "criteria": ("eje2 S119 (crater A10 + dash), loader canónico CONS∪OCR, referencia filtrada a pasadas nocturnas con la misma regla del pipeline (_reject_daytime, S124)"),
        "recall": recall,
        "magnitud_ratio_by_vol": magnitud,
        "magnitud_ratio_by_npix": {
            b: {"n_noches": len(r), "ratio_mediano": round(statistics.median(r), 3)}
            for b, r in sorted(ratios_by_npix.items()) if r},
        "integrity": integrity,
        "flags": flags,
        "verdict": verdict,
    }
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    hist_line = {"date": out["generated_utc"][:10], "verdict": out["verdict"],
                 "cobertura_pct": cobertura_pct, "gt_stale_dias": gt_stale_dias,
                 "recall": {s: recall[s]["recall_crater_pct"] for s in SENSORS},
                 "n_flags": len(flags)}
    with open(os.path.join(OUTDIR, "history.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(hist_line, ensure_ascii=False) + "\n")

    print(f"Auto-audit semanal — ventana {win[0]} → {win[1]}")
    for s in SENSORS:
        r = recall[s]
        print(f"  {s:<9} recall crater {r['recall_crater_pct']}% (n={r['n_noches']})")
    for v, m in magnitud.items():
        print(f"  ratio {v:<20} {m['ratio_mediano']}x (n={m['n_noches']})")
    for av in cobertura_avisos:
        print(f"COBERTURA: {av}")
    print(f"VEREDICTO: {out['verdict']}" + (f" — {len(flags)} flags" if flags else ""))
    for fl in flags:
        print("  ⚠", fl)


if __name__ == "__main__":
    main()
