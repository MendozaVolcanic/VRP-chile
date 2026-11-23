#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Latencia del NRT de VRP Chile contra MIROVA, por sensor y por volcán (S196, paso 2 del camino de independencia, E2a).

POR QUÉ. Un operador del OVDAS de turno no pregunta sólo «¿la alerta es la misma que la de MIROVA?», también «¿cuánto
después del paso del satélite la veo?». S150 lo midió una vez (`experiments/_s150_latencia/`, 2026-09-14 a 2026-10-02):
VRP Chile mediana 5,05 h, MIROVA 2,77 h. Desde entonces cada record trae `first_processed_utc` (la hora en que la pasada
entró por primera vez a nuestros datos; se hereda en el paso de NRT a estándar y en los reprocesos), así que repetirla no
exige recorrer el historial completo de git.

QUÉ MIDE. Para cada pasada de los 11 Tier A en la ventana:
  * NASA: adquisición -> producción del gránulo NRT (la hora de producción va en el nombre del archivo, «.AAAADDDhhmmss.»;
    sólo en records cuyo gránulo es NRT, porque tras el paso a estándar el nombre es el del estándar).
  * repo: adquisición -> `first_processed_utc` (el runner del NRT escribió el record).
  * commit: adquisición -> primer commit de `data/mirova_equivalent/<Volcan>.json` que contiene ese `first_processed_utc`
    (verificado leyendo el archivo en cada commit, no supuesto por la hora).
  * tablero: adquisición -> término del primer despliegue exitoso de GitHub Pages (`pages-deploy.yml`) creado después de
    ese commit. No incluye la caché del CDN ni la del navegador del operador (SIN MEDIR; del orden de minutos).
  * MIROVA: adquisición -> `Fecha_Proceso_UTC` del consolidado de Mirova-v1, la primera vez que el scraper vio la pasada en
    mirovaweb.it. Es la latencia de MIROVA tal como le llega hoy al OVDAS (por el scraper), y es cota superior de la de
    mirovaweb.it misma: incluye el atraso del scraper.
Pareo con MIROVA como S150: mismo volcán, misma familia de sensor, adquisición a 3 min o menos.

FRANJA. Noche o día según la elevación solar sobre el volcán a la hora del record, con `pipeline/store.py::_solar_elevation`
(la compuerta que guarda o rechaza un record diurno). Sólo MODIS tiene día desde #1090 (mergeado 2026-11-22 06:58:25 UTC);
los records diurnos anteriores a esa hora entraron por relleno, no por el NRT, y quedan fuera.

EXCLUSIONES (se cuentan, no se esconden): records con `first_processed_utc` más de 48 h después de la adquisición (entrada
por reproceso o relleno, no por el NRT), records sin `first_processed_utc` y MODIS diurno anterior a #1090.

Uso:
  python experiments/_s196_latencia/latencia.py --desde 2026-11-09 --hasta 2026-11-22 \
      --cons <consolidado de Mirova-v1> --pages <pages_runs.json> --out experiments/_s196_latencia
  (--bajar-pages y --bajar-mirova los bajan con gh y guardan lo bajado en --out para repetir la cuenta.)
"""
from __future__ import annotations

import argparse
import bisect
import csv
import json
import re
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pipeline.store import _solar_elevation  # noqa: E402  (sólo lectura; A45 no se toca)
from banco_paridad import VOLS, bucket  # noqa: E402
from auto_audit_weekly import _coords_por_volcan  # noqa: E402

REPO = "MendozaVolcanic/VRP-chile"
MERGE_1090 = datetime(2026, 11, 22, 6, 58, 25, tzinfo=timezone.utc)   # gh pr view 1090 --json mergedAt
MAX_H = 48.0
TOL_PAREO = timedelta(minutes=3)
NOMBRE_MIROVA = {"Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Nevados de Chillan": "NevadosDeChillan",
                 "Planchon-Peteroa": "PlanchonPeteroa", "Planchon Peteroa": "PlanchonPeteroa"}
SENSOR_MIROVA = {"MODIS": "MODIS", "VIIRS": "VIIRS750", "VIIRS375": "VIIRS375"}
RE_FP = re.compile(r'"first_processed_utc":\s*"([^"]+)"')
RE_PROD = re.compile(r"\.(\d{13})\.")


def _utc(s, fmt):
    return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)


def _h(a, b):
    return None if a is None or b is None else round((b - a).total_seconds() / 3600.0, 4)


def _relativa(path):
    """Ruta relativa al repo si cuelga de él (las salidas se commitean: sin rutas del computador de nadie)."""
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return Path(path).name


def produccion_nasa(granule):
    """Hora de producción del gránulo NRT (AAAADDDhhmmss en el nombre); None si no es NRT o no se lee."""
    g = granule or ""
    if "NRT" not in g.upper():
        return None
    m = RE_PROD.findall(g)
    if not m:
        return None
    s = m[-1]
    try:
        return (datetime.strptime(s[:7], "%Y%j").replace(tzinfo=timezone.utc)
                + timedelta(hours=int(s[7:9]), minutes=int(s[9:11]), seconds=int(s[11:13])))
    except ValueError:
        return None


def cargar_records(data_dir, desde, hasta_excl, coords):
    out, excl = [], defaultdict(int)
    for vol in VOLS:
        d = json.loads((Path(data_dir) / f"{vol}.json").read_text(encoding="utf-8"))
        lat, lon = coords[vol]
        for r in d.get("records", []):
            b = bucket(r.get("sensor"))
            try:
                acq = _utc(r["datetime_utc"], "%Y-%m-%d %H:%M")
            except (KeyError, ValueError):
                continue
            if b is None or not (desde <= acq < hasta_excl):
                continue
            franja = "dia" if _solar_elevation(lat, lon, acq) > 0 else "noche"
            fp_s = r.get("first_processed_utc")
            if not fp_s:
                excl["sin_first_processed_utc"] += 1
                continue
            fp = _utc(fp_s, "%Y-%m-%dT%H:%M:%SZ")
            if franja == "dia" and acq < MERGE_1090:
                excl["modis_dia_antes_de_1090"] += 1
                continue
            if (fp - acq).total_seconds() / 3600.0 > MAX_H:
                excl["entrada_mas_de_48h"] += 1
                continue
            out.append({"vol": vol, "b": b, "sensor": r.get("sensor"), "franja": franja, "acq": acq, "fp": fp,
                        "fp_s": fp_s, "nasa": produccion_nasa(r.get("granule")),
                        "origen": (r.get("regimen") or {}).get("origen")})
    return out, dict(excl)


def primer_commit(vol, fps, desde):
    """{first_processed_utc: (sha, hora del commit)} del primer commit del archivo del volcán que contiene cada uno."""
    path = f"data/mirova_equivalent/{vol}.json"
    log = subprocess.run(["git", "-C", str(ROOT), "log", "--reverse", "--format=%H %cI",
                          f"--since={(desde - timedelta(days=1)).isoformat()}", "--", path],
                         capture_output=True, text=True, check=True).stdout.split("\n")
    pend, out = set(fps), {}
    for linea in log:
        if not linea.strip() or not pend:
            continue
        sha, ci = linea.split(" ", 1)
        raw = subprocess.run(["git", "-C", str(ROOT), "show", f"{sha}:{path}"], capture_output=True).stdout
        presentes = set(RE_FP.findall(raw.decode("utf-8", errors="replace"))) & pend
        t = datetime.fromisoformat(ci).astimezone(timezone.utc)
        for fp in presentes:
            out[fp] = (sha[:9], t)
        pend -= presentes
    return out


def bajar_pages(desde, destino):
    q = (".workflow_runs[] | {id, created_at, updated_at, conclusion, head_sha}")
    raw = subprocess.run(["gh", "api", "-X", "GET", f"repos/{REPO}/actions/workflows/pages-deploy.yml/runs",
                          "-f", f"created=>={(desde - timedelta(days=1)).strftime('%Y-%m-%d')}", "-f", "per_page=100",
                          "--paginate", "-q", q], capture_output=True, text=True, check=True).stdout
    runs = [json.loads(l) for l in raw.splitlines() if l.strip()]
    Path(destino).write_text(json.dumps(runs, indent=0), encoding="utf-8")
    return runs


def indice_pages(runs):
    ok = sorted((datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")),
                 datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00"))) for r in runs
                if r.get("conclusion") == "success")
    return [c for c, _ in ok], [u for _, u in ok]


def publicado(creados, terminados, t):
    i = bisect.bisect_left(creados, t)
    return terminados[i] if i < len(creados) else None


def cargar_mirova(cons):
    por = defaultdict(list)
    with open(cons, encoding="utf-8", errors="replace") as fh:
        for f in csv.DictReader(fh):
            vol = NOMBRE_MIROVA.get(f.get("Volcan"), f.get("Volcan"))
            b = SENSOR_MIROVA.get(f.get("Sensor"))
            vis = f.get("Fecha_Proceso_UTC") or ""
            if vol not in VOLS or b is None or not vis:
                continue
            try:
                acq = _utc(f["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S")
                visto = _utc(vis, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue
            por[(vol, b)].append((acq, visto, f.get("Tipo_Registro")))
    for v in por.values():
        v.sort()
    return por


def parear_mirova(por, vol, b, acq):
    lst = por.get((vol, b), [])
    ts = [x[0] for x in lst]
    i = bisect.bisect_left(ts, acq - TOL_PAREO)
    mejor = None
    while i < len(lst) and lst[i][0] <= acq + TOL_PAREO:
        if mejor is None or abs(lst[i][0] - acq) < abs(mejor[0] - acq):
            mejor = lst[i]
        i += 1
    return mejor


def resumen(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return {"n": 0}
    q = statistics.quantiles(xs, n=10) if len(xs) > 1 else [xs[0]] * 9
    return {"n": len(xs), "mediana_h": round(statistics.median(xs), 2), "p10_h": round(q[0], 2),
            "p90_h": round(q[8], 2), "min_h": round(xs[0], 2), "max_h": round(xs[-1], 2)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--desde", required=True, help="AAAA-MM-DD, primer día UTC de la ventana")
    ap.add_argument("--hasta", required=True, help="AAAA-MM-DD, último día UTC incluido")
    ap.add_argument("--hasta-dia-modis", help="último día UTC del MODIS diurno (por defecto --hasta)")
    ap.add_argument("--data", default=str(ROOT / "data" / "mirova_equivalent"))
    ap.add_argument("--cons", help="consolidado de Mirova-v1")
    ap.add_argument("--bajar-mirova", action="store_true", help="bajar el consolidado del remoto a --out")
    ap.add_argument("--pages", help="pages_runs.json")
    ap.add_argument("--bajar-pages", action="store_true", help="bajar los despliegues de Pages a --out")
    ap.add_argument("--out", default=str(Path(__file__).parent))
    a = ap.parse_args(argv)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    desde = _utc(a.desde, "%Y-%m-%d")
    hasta = _utc(a.hasta, "%Y-%m-%d") + timedelta(days=1)
    hasta_dia = _utc(a.hasta_dia_modis or a.hasta, "%Y-%m-%d") + timedelta(days=1)
    coords = _coords_por_volcan()

    recs, excl = cargar_records(a.data, desde, max(hasta, hasta_dia), coords)
    fuera_ventana = [r for r in recs if (r["franja"] == "noche" and r["acq"] >= hasta)
                     or (r["franja"] == "dia" and r["acq"] >= hasta_dia)]
    recs = [r for r in recs if r not in fuera_ventana]

    commits = {}
    for vol in VOLS:
        fps = {r["fp_s"] for r in recs if r["vol"] == vol}
        commits[vol] = primer_commit(vol, fps, desde)
        print(f"{vol}: {len(fps)} first_processed_utc, {len(commits[vol])} con commit", flush=True)

    if a.bajar_pages:
        runs = bajar_pages(desde, out / "pages_runs.json")
    else:
        runs = json.loads(Path(a.pages).read_text(encoding="utf-8"))
    creados, terminados = indice_pages(runs)

    info_mirova = {"fuente": a.cons}
    if a.bajar_mirova:
        from referencia_mirova_unificada import sha_remoto, URL_RAW  # noqa: E402
        import urllib.request
        sha = sha_remoto("registro_vrp_consolidado.csv")
        destino = out / "registro_vrp_consolidado.csv"
        urllib.request.urlretrieve(URL_RAW.format(sha=sha, nombre="registro_vrp_consolidado.csv"), destino)
        info_mirova = {"fuente": "remoto Mirova-v1", "sha": sha, "archivo": destino.name}
        a.cons = str(destino)
    mirova = cargar_mirova(a.cons)

    filas = []
    for r in sorted(recs, key=lambda x: (x["acq"], x["vol"], x["sensor"])):
        c = commits[r["vol"]].get(r["fp_s"])
        t_commit = c[1] if c else None
        t_pub = publicado(creados, terminados, t_commit) if t_commit else None
        m = parear_mirova(mirova, r["vol"], r["b"], r["acq"])
        filas.append({"vol": r["vol"], "b": r["b"], "sensor": r["sensor"], "franja": r["franja"],
                      "acq": r["acq"].strftime("%Y-%m-%d %H:%M"), "origen": r["origen"],
                      "h_nasa": _h(r["acq"], r["nasa"]), "h_repo": _h(r["acq"], r["fp"]),
                      "h_commit": _h(r["acq"], t_commit), "h_tablero": _h(r["acq"], t_pub),
                      "sha_commit": c[0] if c else None,
                      "h_mirova": _h(m[0], m[1]) if m else None, "tipo_mirova": m[2] if m else None})

    grupos = {}
    for b in ("MODIS", "VIIRS375", "VIIRS750"):
        for franja in ("noche", "dia"):
            fs = [f for f in filas if f["b"] == b and f["franja"] == franja]
            if not fs:
                continue
            par = [f for f in fs if f["h_mirova"] is not None and f["h_tablero"] is not None]
            g = {"n_pasadas": len(fs),
                 "nasa": resumen([f["h_nasa"] for f in fs]), "repo": resumen([f["h_repo"] for f in fs]),
                 "commit": resumen([f["h_commit"] for f in fs]), "tablero": resumen([f["h_tablero"] for f in fs]),
                 "pareadas_con_mirova": len(par),
                 "tablero_pareadas": resumen([f["h_tablero"] for f in par]),
                 "mirova_pareadas": resumen([f["h_mirova"] for f in par]),
                 "diferencia_tablero_menos_mirova": resumen([f["h_tablero"] - f["h_mirova"] for f in par]),
                 "vrp_primero": sum(f["h_tablero"] < f["h_mirova"] for f in par),
                 "por_volcan": {}}
            for vol in VOLS:
                fv = [f for f in fs if f["vol"] == vol]
                pv = [f for f in fv if f in par]
                if fv:
                    g["por_volcan"][vol] = {"n": len(fv), "tablero_mediana_h": resumen([f["h_tablero"] for f in fv]).get("mediana_h"),
                                            "mirova_mediana_h": resumen([f["h_mirova"] for f in pv]).get("mediana_h"),
                                            "n_pareadas": len(pv)}
            grupos[f"{b}|{franja}"] = g

    salida = {"meta": {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "ventana_noche": [a.desde, a.hasta], "ventana_dia_modis": [MERGE_1090.isoformat(), (hasta_dia - timedelta(days=1)).strftime("%Y-%m-%d")],
                       "data": _relativa(a.data), "mirova": info_mirova, "n_despliegues_pages": len(runs),
                       "n_despliegues_pages_exitosos": len(creados), "excluidos": excl,
                       "n_fuera_de_ventana": len(fuera_ventana),
                       "sin_commit": sum(f["sha_commit"] is None for f in filas),
                       "sin_despliegue": sum(f["h_tablero"] is None for f in filas),
                       "pareo_mirova": "mismo volcán y familia de sensor, adquisición a 3 min o menos",
                       "origenes": sorted({str(f["origen"]) for f in filas})},
              "grupos": grupos}
    (out / "resumen.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(out / "pasadas.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()) if filas else ["vol"])
        w.writeheader()
        w.writerows(filas)
    for k, g in grupos.items():
        print(f"{k:16s} n={g['n_pasadas']:5d} nasa {g['nasa'].get('mediana_h')} repo {g['repo'].get('mediana_h')} "
              f"tablero {g['tablero'].get('mediana_h')} | pareadas {g['pareadas_con_mirova']} VRP "
              f"{g['tablero_pareadas'].get('mediana_h')} MIROVA {g['mirova_pareadas'].get('mediana_h')} "
              f"VRP primero {g['vrp_primero']}")
    print("excluidos", excl, "| meta", {k: salida["meta"][k] for k in ("sin_commit", "sin_despliegue")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
