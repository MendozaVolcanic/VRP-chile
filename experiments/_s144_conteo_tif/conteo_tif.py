# -*- coding: utf-8 -*-
"""S144: conteo versionado de pasadas VIIRS 375 nocturnas con TIF UTM de MIROVA, alerta y patrón keep_peak.

POR QUÉ. La decisión 1 del traspaso S144 (medir `keep_peak` con dirección) se apoyaba en un conteo
exploratorio sin script en el repo. Este script lo rehace con las definiciones escritas antes en
README.md y con cada entrada fijada por sha: records del repo, índice de TIF de
`mirova-tif-archive` (leído por la API, nunca pull: pesa 17 GB) y referencia CONS/OCR de Mirova-v1.

Reutiliza sin reescribir: `banco_paridad` (bucket, nocturnidad, pareo, etiquetas, predicado node) y
`evaluar.fila_mirova` de S143 (qué fila MIROVA cuenta como alerta).

USO: python experiments/_s144_conteo_tif/conteo_tif.py [--sha-records SHA] [--sha-indice SHA] [--sha-cons SHA --sha-ocr SHA] [--sin-tif]
"""
from __future__ import annotations

import argparse
import bisect
import collections
import csv
import io
import json
import math
import os
import statistics
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (ROOT, ROOT / "scripts", ROOT / "experiments" / "_s143_evaluador"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

REPO_TIF = "MendozaVolcanic/mirova-tif-archive"
TOL_TIF_S = 15 * 60          # README §2
UMBRAL_SEPARACION_KM = 0.5   # README §4
PLACEBO_H = 6                # README P1
DL = HERE / "_dl_tif"

# carpeta TIF de MIROVA -> nombre en volcanoes.yaml / data (copiado de _s142_ndc/pixeles_mirova.py)
NOMBRE_TIF = {
    "ChillanNevadosde": "NevadosDeChillan", "Chaiten": "Chaiten", "Copahue": "Copahue",
    "Isluga": "Isluga", "Lascar": "Lascar", "Lastarria": "Lastarria", "Llaima": "Llaima",
    "PlanchonPeteroa": "PlanchonPeteroa", "PuyehueCordonCaulle": "PuyehueCordonCaulle",
    "Tupungatito": "Tupungatito", "Villarrica": "Villarrica",
}


def _t(s):
    return datetime.fromisoformat(s.strip()).astimezone(timezone.utc)


def hav(la1, lo1, la2, lo2):
    rt = 6371.0088
    p = math.radians
    dla, dlo = p(la2 - la1), p(lo2 - lo1)
    a = math.sin(dla / 2) ** 2 + math.cos(p(la1)) * math.cos(p(la2)) * math.sin(dlo / 2) ** 2
    return 2 * rt * math.asin(math.sqrt(a))


# ------------------------------------------------------------------ índice de TIF
def cargar_indice_tif(texto):
    """vol -> lista ordenada de (adquisición, fila). Sólo VIIRS 375, no vacíos, con hora de
    adquisición (la hora del nombre del archivo puede no ser la de la pasada, A106)."""
    idx = collections.defaultdict(list)
    for f in csv.DictReader(io.StringIO(texto)):
        if f["sensor"] != "VIIRS375" or f["size_bytes"] in ("", "0") or not f["acquisition_utc"].strip():
            continue
        vol = NOMBRE_TIF.get(f["volcano"], f["volcano"])
        idx[vol].append((_t(f["acquisition_utc"]), f))
    # Enmienda S144 (post-hoc, ver README): MIROVA a veces vuelve a servir una imagen vieja bajo una
    # adquisición nueva. La imagen es "propia" sólo de la primera adquisición en que aparece su md5.
    primera = {}
    for vol, lista in idx.items():
        for t, f in lista:
            k = (vol, f["md5"])
            primera[k] = min(primera.get(k, t), t)
    for vol, lista in idx.items():
        for t, f in lista:
            f["propia"] = primera[(vol, f["md5"])] == t
    for v in idx.values():
        v.sort(key=lambda x: x[0])
    return dict(idx)


def inicio_utm(idx):
    return min(lista[0][0] for lista in idx.values() if lista)


def emparejar_tif(idx, vol, dt, tol_s=TOL_TIF_S):
    """(fila, |Δt| en s) de la adquisición más cercana a ±tol, o None."""
    lista = idx.get(vol) or []
    ts = [x[0] for x in lista]
    i = bisect.bisect_left(ts, dt - timedelta(seconds=tol_s))
    mejor = None
    while i < len(lista) and lista[i][0] <= dt + timedelta(seconds=tol_s):
        d = abs((lista[i][0] - dt).total_seconds())
        if mejor is None or d < mejor[1]:
            mejor = (lista[i][1], int(round(d)))
        i += 1
    return mejor


# ------------------------------------------------------------------ patrón keep_peak
def patron_keep_peak(r, umbral_km=UMBRAL_SEPARACION_KM):
    """Firma de D19 en el record: el ancla publica `test1_roi` y el cúmulo es un píxel en otro lugar."""
    pc = r.get("primary_cluster") or {}
    if r.get("final_hotspot_source") != "test1_roi" or pc.get("n_pixels") != 1:
        return False
    vals = (r.get("final_hotspot_lat"), r.get("final_hotspot_lon"), pc.get("centroid_lat"), pc.get("centroid_lon"))
    if any(v is None for v in vals):
        return False
    return hav(*map(float, vals)) > umbral_km


def es_utm_375(crs, res, tol_m=5.0):
    """CRS UTM (EPSG 326xx/327xx) y píxel de ~375 m."""
    s = str(crs or "")
    utm = s.startswith("EPSG:326") or s.startswith("EPSG:327")
    return bool(utm and all(abs(abs(float(x)) - 375.0) <= tol_m for x in res))


def tabla_cruce(ps, clave_tif="tif"):
    ps = [dict(p, tif=p[clave_tif]) for p in ps]
    c = lambda f: sum(1 for p in ps if f(p))  # noqa: E731
    return {"pasadas": len(ps),
            "con_tif": c(lambda p: p["tif"]),
            "con_alerta": c(lambda p: p["alerta"]),
            "alerta_y_tif": c(lambda p: p["alerta"] and p["tif"]),
            "patron": c(lambda p: p["patron"]),
            "patron_y_tif": c(lambda p: p["patron"] and p["tif"]),
            "patron_alerta_tif": c(lambda p: p["patron"] and p["alerta"] and p["tif"]),
            "publicadas": c(lambda p: p["pub"]),
            "patron_publicadas": c(lambda p: p["patron"] and p["pub"]),
            "patron_publicadas_tif": c(lambda p: p["patron"] and p["pub"] and p["tif"])}


# ------------------------------------------------------------------ entradas fijadas por sha
def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, check=True, cwd=ROOT, **kw).stdout


def _gh_raw(ruta, ref):
    return _run(["gh", "api", "-H", "Accept: application/vnd.github.raw", f"repos/{REPO_TIF}/contents/{ruta}?ref={ref}"])


def indice_por_sha(sha=None):
    sha = sha or _run(["gh", "api", f"repos/{REPO_TIF}/commits?path=index.csv&per_page=1", "-q", ".[0].sha"],
                      text=True).strip()
    destino = DL / f"{sha[:12]}_index.csv"
    if not destino.exists() or destino.stat().st_size == 0:
        DL.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(_gh_raw("index.csv", sha))
    return destino.read_text(encoding="utf-8"), sha


def leer_tif(fila, sha):
    """Baja un TIF (KB) por la API y devuelve CRS, resolución y etiquetas de fecha."""
    import rasterio
    destino = DL / sha[:12] / fila["tif_path"]
    if not destino.exists() or destino.stat().st_size == 0:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(_gh_raw(fila["tif_path"], sha))
    with rasterio.open(destino) as ds:
        crs = ds.crs.to_string() if ds.crs else None
        return {"crs": crs, "res": list(ds.res), "tags": {k: v for k, v in ds.tags().items() if "DATE" in k.upper() or "TIME" in k.upper()}}


def records_por_sha(sha, vols):
    out = {}
    for v in vols:
        txt = _run(["git", "show", f"{sha}:data/mirova_equivalent/{v}.json"])
        out[v] = json.loads(txt.decode("utf-8"))["records"]
    return out


def informe_md(res):
    """RESULTADO.md generado desde resultado.json (ningún número transcrito a mano, S91)."""
    m, c = res["meta"], res["controles"]
    L = ["# S144: resultado del conteo de pasadas VIIRS 375 con TIF de MIROVA", "",
         "> Generado por `conteo_tif.py`; no editar a mano. Definiciones en `README.md`, incluida la enmienda.", "",
         f"Entradas: records `{m['sha_records'][:12]}`, índice de TIF `{m['sha_indice_tif'][:12]}`, "
         f"CONS `{m['referencia']['registro_vrp_consolidado.csv'][:12]}`, OCR `{m['referencia']['registro_vrp_ocr.csv'][:12]}`, "
         f"`frontend/index.html` `{m['sha_index_html'][:12]}`. Última pasada: {m['ultima_pasada']} UTC. "
         f"Primera adquisición del índice: {m['primera_adquisicion_indice'][:16]}.", ""]
    cols = ["pasadas", "con_tif", "con_alerta", "alerta_y_tif", "patron", "patron_y_tif", "patron_alerta_tif",
            "publicadas", "patron_publicadas_tif"]
    for w, t in res["tablas"].items():
        L += [f"## Ventana `{w}`", "", "| nivel de TIF | " + " | ".join(cols) + " |",
              "|---|" + "---|" * len(cols)]
        for n, x in t.items():
            L.append(f"| {n} | " + " | ".join(str(x[k]) for k in cols) + " |")
        L += ["", f"Etiquetas de todas las pasadas: {res['etiquetas'][w]}. "
                  f"Patrón con TIF propio: {res['etiquetas_patron_tif_propia'][w]}.", ""]
    L += ["## Por volcán (historia, TIF propio)", "",
          "| volcán | pasadas | patrón | patrón y TIF | patrón, alerta y TIF | patrón publicado y TIF |", "|---|---|---|---|---|---|"]
    for v, t in res["por_volcan"].items():
        x = t["tif_propia"]
        L.append(f"| {v} | {x['pasadas']} | {x['patron']} | {x['patron_y_tif']} | {x['patron_alerta_tif']} | {x['patron_publicadas_tif']} |")
    L += ["", "## Contra el conteo exploratorio (ventana desde 2026-09-14 06:36)", "",
          "| conjunto | exploratorio | TIF cualquiera | TIF propio | TIF UTM 375 |", "|---|---|---|---|---|"]
    ce = res["comparacion_exploratorio"]
    for k in ce["tif_cualquiera"]:
        L.append(f"| {k} | {ce['tif_cualquiera'][k]['exploratorio']} | {ce['tif_cualquiera'][k]['ahora']} | "
                 f"{ce['tif_propia'][k]['ahora']} | {ce['tif_utm_375'][k]['ahora']} |")
    d = c["dt_tif_s"]
    L += ["", "## Controles del instrumento", "",
          f"- P2, predicado node: identidad {'OK' if c['identidad_predicado'] else 'FALLA'}.",
          f"- P1, placebo (+6 h): {c['placebo_+6h_con_tif']} pasadas con TIF.",
          f"- P1, lectura directa: {c['tif_leidos']} TIF leídos con rasterio; CRS {c['crs_vistos']}.",
          f"- Adquisiciones con TIF UTM de 375 m: {', '.join(x[:16] for x in c['tif_utm_fechas'])}.",
          f"- |Δt| TIF-record: n {d['n']}, mín {d['min']} s, mediana {d['mediana']} s, máx {d['max']} s; "
          f"{d['n_cero']} en 0 s, {d['n_mayor_14min']} sobre 14 min.",
          f"- TIF emparejados con más de una pasada nuestra: {c['tif_compartidos']}.",
          f"- Etiquetas de fecha dentro de los TIF: {c['etiquetas_fecha_en_tif'] or 'ninguna'}.", ""]
    return "\n".join(L)


# ------------------------------------------------------------------ corrida
def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    import banco_paridad as bp
    import evaluar
    from referencia_mirova_unificada import bajar_remoto, cargar_referencia_unificada

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sha-records", default=None, help="por defecto origin/main")
    ap.add_argument("--sha-indice", default=None, help="commit de mirova-tif-archive; por defecto el último que tocó index.csv")
    ap.add_argument("--sha-cons", default=None, help="commit de Mirova-v1 para el consolidado (con --sha-ocr)")
    ap.add_argument("--sha-ocr", default=None)
    ap.add_argument("--sin-tif", action="store_true", help="no bajar los TIF (salta el control de lectura)")
    a = ap.parse_args(argv)

    sha_rec = a.sha_records or _run(["git", "rev-parse", "origin/main"], text=True).strip()
    texto_idx, sha_idx = indice_por_sha(a.sha_indice)
    idx = cargar_indice_tif(texto_idx)
    t0 = inicio_utm(idx)
    if a.sha_cons and a.sha_ocr:
        import urllib.request
        import referencia_mirova_unificada as rmu
        info_ref = {}
        for nombre, sha in (("registro_vrp_consolidado.csv", a.sha_cons), ("registro_vrp_ocr.csv", a.sha_ocr)):
            destino = DL / "referencia" / f"{sha[:12]}_{nombre}"
            if not destino.exists() or destino.stat().st_size == 0:
                destino.parent.mkdir(parents=True, exist_ok=True)
                urllib.request.urlretrieve(rmu.URL_RAW.format(sha=sha, nombre=nombre), destino)
            info_ref[nombre] = {"sha": sha, "path": str(destino)}
    else:
        info_ref = bajar_remoto(DL / "referencia")
    cons = Path(info_ref["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info_ref["registro_vrp_ocr.csv"]["path"])

    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    identidad = bp.control_identidad_predicado()
    if identidad != ([0, 1, 1, 1, 0], [1, 0]):
        raise SystemExit(f"P2: el predicado node no pasa el control de identidad: {identidad}")

    fin = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ventana = (t0.strftime("%Y-%m-%d"), fin)
    filas = cargar_referencia_unificada(cons, ocr)
    por_vb, noche_sensor, noche_volcan, _ = bp.indexar_referencia(filas, coords, ventana)

    recs_vol = records_por_sha(sha_rec, bp.VOLS)
    ps, casos = [], []
    for vol, records in recs_vol.items():
        for r in records:
            if bp.bucket(r.get("sensor")) != "VIIRS375":
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            if dt < t0:
                continue
            lat, lon = coords[vol]
            if bp.es_pasada_diurna_descartada("VIIRS375", lat, lon, dt):
                continue
            m = emparejar_tif(idx, vol, dt)
            placebo = emparejar_tif(idx, vol, dt + timedelta(hours=PLACEBO_H))
            f = evaluar.fila_mirova(bp.parear(por_vb.get((vol, "VIIRS375"), []), dt), dt)
            pc = r.get("primary_cluster") or {}
            ps.append({"vol": vol, "b": "VIIRS375", "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                       "datetime_utc": r["datetime_utc"], "sensor": r.get("sensor"),
                       "tif": m is not None, "tif_path": m[0]["tif_path"] if m else None,
                       "tif_acq": m[0]["acquisition_utc"] if m else None, "tif_dt_s": m[1] if m else None,
                       "tif_propia": bool(m and m[0]["propia"]),
                       "placebo_tif": placebo is not None,
                       "alerta": f is not None, "mir_vrp": float(f["vrp_mw"]) if f else None,
                       "mir_fuente": f["source"] if f else None,
                       "mir_dist_km": f.get("dist_km") if f else None,
                       "patron": patron_keep_peak(r),
                       "final_hotspot_source": r.get("final_hotspot_source"),
                       "final_hotspot": [r.get("final_hotspot_lat"), r.get("final_hotspot_lon")],
                       "centroide": [pc.get("centroid_lat"), pc.get("centroid_lon")],
                       "pc_n_pixels": pc.get("n_pixels"), "pc_vrp_mw": pc.get("vrp_mw"),
                       "pc_dist_km": pc.get("centroid_dist_km")})
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos)
    if len(pred) != len(ps):
        raise RuntimeError(f"node devolvió {len(pred)} para {len(ps)} pasadas")
    for p, o in zip(ps, pred):
        p["pub"] = int(bool(o[4]))
    bp.etiquetar(ps, por_vb, noche_sensor, noche_volcan)

    # P1, lectura directa: cada TIF emparejado debe ser UTM de 375 m
    lectura = {}
    if not a.sin_tif:
        for p in ps:
            if p["tif"] and p["tif_path"] not in lectura:
                fila = next(f for _, f in idx[p["vol"]] if f["tif_path"] == p["tif_path"])
                lectura[p["tif_path"]] = leer_tif(fila, sha_idx)
        for p in ps:
            li = lectura.get(p["tif_path"]) if p["tif"] else None
            p["tif_crs"] = li["crs"] if li else None
            p["tif_utm"] = bool(li and es_utm_375(li["crs"], li["res"]))
    no_utm = sorted({k for k, v in lectura.items() if not es_utm_375(v["crs"], v["res"])})

    # Enmienda S144: tres niveles de TIF y dos ventanas (README, "Enmienda tras la primera corrida")
    for p in ps:
        p["tif_cualquiera"] = p["tif"]
        p["tif_propia_"] = p["tif"] and p["tif_propia"]
    desde_utm = datetime(2026, 9, 14, 6, 36, tzinfo=timezone.utc)
    ventanas = {"historia": ps, "desde_2026-09-14_0636": [p for p in ps if p["dt"] >= desde_utm]}
    niveles = {"tif_cualquiera": "tif_cualquiera", "tif_propia": "tif_propia_", "tif_utm_375": "tif_utm"}
    tablas = {w: {n: tabla_cruce(sel, c) for n, c in niveles.items()} for w, sel in ventanas.items()}

    dts = [p["tif_dt_s"] for p in ps if p["tif_dt_s"] is not None]
    por_vol = {v: {n: tabla_cruce([p for p in ps if p["vol"] == v], c) for n, c in niveles.items()} for v in bp.VOLS}
    campos = ("vol", "datetime_utc", "sensor", "tif_path", "tif_acq", "tif_dt_s", "tif_crs", "tif_propia",
              "alerta", "mir_fuente", "mir_vrp", "mir_dist_km", "lab", "pub", "final_hotspot", "centroide",
              "pc_vrp_mw", "pc_dist_km")
    muestra = [{k: p.get(k) for k in campos} for p in ps if p["patron"] and p["tif_propia_"]]
    exploratorio = {"pasadas": 290, "con_tif": 122, "con_alerta": 58, "alerta_y_tif": 23,
                    "patron": 81, "patron_y_tif": 34, "patron_alerta_tif": 2}
    tabla = tablas["desde_2026-09-14_0636"]
    res = {
        "meta": {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "sha_records": sha_rec, "sha_indice_tif": sha_idx,
                 "referencia": {k: v["sha"] for k, v in info_ref.items()},
                 "sha_index_html": bp.sha_git(bp.HTML),
                 "primera_adquisicion_indice": t0.isoformat(), "ultima_pasada": max(p["datetime_utc"] for p in ps),
                 "tol_tif_s": TOL_TIF_S, "umbral_separacion_km": UMBRAL_SEPARACION_KM,
                 "definiciones": "experiments/_s144_conteo_tif/README.md"},
        "tablas": tablas,
        "etiquetas": {w: dict(collections.Counter(p["lab"] for p in sel)) for w, sel in ventanas.items()},
        "etiquetas_patron_tif_propia": {w: dict(collections.Counter(p["lab"] for p in sel if p["patron"] and p["tif_propia_"]))
                                        for w, sel in ventanas.items()},
        "comparacion_exploratorio": {n: {k: {"exploratorio": v, "ahora": tabla[n][k], "bajo": tabla[n][k] < v}
                                         for k, v in exploratorio.items()} for n in niveles},
        "controles": {
            "identidad_predicado": True,
            "placebo_+6h_con_tif": sum(p["placebo_tif"] for p in ps),
            "tif_leidos": len(lectura), "tif_no_utm_375": no_utm,
            "crs_vistos": dict(collections.Counter(v["crs"] for v in lectura.values())),
            "etiquetas_fecha_en_tif": sorted({k for v in lectura.values() for k in v["tags"]}),
            "dt_tif_s": {"n": len(dts), "min": min(dts) if dts else None,
                         "mediana": statistics.median(dts) if dts else None, "max": max(dts) if dts else None,
                         "n_cero": sum(1 for d in dts if d == 0), "n_mayor_14min": sum(1 for d in dts if d > 840)},
            "tif_compartidos": sum(1 for _, n in collections.Counter(p["tif_path"] for p in ps if p["tif_path"]).items() if n > 1),
            "tif_utm_fechas": sorted({p["tif_acq"] for p in ps if p["tif_utm"]})},
        "por_volcan": por_vol,
        "muestra_patron_con_tif": muestra,
    }
    (HERE / "RESULTADO.md").write_text(informe_md(json.loads(json.dumps(res, default=str))), encoding="utf-8", newline="\n")
    (HERE / "resultado.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str),
                                         encoding="utf-8", newline="\n")
    print(json.dumps({k: res[k] for k in ("meta", "tablas", "etiquetas", "etiquetas_patron_tif_propia",
                                          "comparacion_exploratorio", "controles")}, indent=1, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
