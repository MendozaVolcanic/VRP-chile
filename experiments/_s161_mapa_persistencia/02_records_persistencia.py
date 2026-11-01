# -*- coding: utf-8 -*-
"""S161, persistencia de los mismos focos en NUESTROS records de producción, mes a mes, y capas del mapa.

Fenómeno y por qué: los TIF de MIROVA sólo cubren del 2026-05-09 al 2026-09-20; nuestros records cubren desde febrero de
2025. Nuestro pipeline es sólo nocturno (MIR sin sol), así que aquí no hay franja diurna: todos los records tienen cenit
solar > 90 grados (se comprueba). Se cuenta, por foco y mes, en cuántas pasadas hay un píxel anómalo nuestro a 1 km o
menos del foco (DETECTADO) y en cuántas el tablero publica un cúmulo cuyo centroide cae a 1 km o menos (PUBLICADO).

Instrumento:
- Datos: copia sólo lectura de producción, experiments/_s160_espacial/data/ (origin/main db0dfe847, la misma de S160).
- Focos: los de 01_tif_persistencia.json (forzados de S160 más descubiertos en la frecuencia de los TIF).
- Publicado: predicado del tablero (frontend/index.html de este worktree, ejecutado con node vía scripts/banco_paridad,
  A97). Control de identidad del predicado contra el guard del repo.
- Nulo (A110): 300 puntos al azar por volcán (semilla fija) dentro de 20 km del cráter y a más de 3 km de todo foco; la
  tasa mensual de «detectado» en esos puntos es lo que da el azar.
- Etiqueta de MIROVA para las capas del mapa (noches limpias y noches con alerta): banco_paridad.etiquetar con regla
  D-9 SN sobre la referencia unificada, ventana 2026-01-10 a 2026-10-22 (A119: la tabla es sana desde marzo; el OCR,
  dudoso antes del 2026-06-13).
P1 (roto): el cráter debe detectarse más que el nulo y más en pasadas con alerta que en negativos limpios.
P2 (muerto): n de pasadas por mes; 0 es SIN DATO.
Uso: python -I 02_records_persistencia.py > 02_records_persistencia_salida.txt
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun161 as C  # noqa: E402

sys.path.insert(0, str(C.WT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as BP  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

C.utf8_stdout()
OUT = Path(__file__).resolve().parent
R_FOCO_KM = 1.0
VENTANA_REF = ("2026-01-10", "2026-10-22")


def p(*a):
    print(" ".join(str(x) for x in a))


def km_xy(lat, lon, lat0, lon0):
    return (np.asarray(lon) - lon0) * 111.195 * np.cos(np.radians(lat0)), (np.asarray(lat) - lat0) * 111.195


def main():
    ident = BP.control_identidad_predicado()
    p("P1 control de identidad del predicado:", ident, "OK" if ident == ([0, 1, 1, 1, 0], [1, 0]) else "FALLA")
    p("datos:", C.DATA, "sha", (C.DATA / "SHA_ORIGIN_MAIN.txt").read_text().strip(), "; predicado:", BP.HTML)
    focos_all = json.load(open(OUT / "01_tif_persistencia.json", encoding="utf-8"))
    inner = {v: C.GEO[v]["inner_km"] for v in C.VOLS}
    html_inner = BP.inner_desde_html()
    for v in C.VOLS:
        assert html_inner[v] == inner[v], (v, html_inner[v], inner[v])
    coords = {"Tupungatito": (-33.4, -69.8), "PuyehueCordonCaulle": (-40.59, -72.117), "Isluga": (-19.15, -68.83)}
    filas = [f for f in cargar_referencia_unificada() if f["volcano"] in C.VOLS]
    por_vb, noche_sensor, noche_volcan, nref = BP.indexar_referencia(filas, coords, VENTANA_REF, regla_minimas="SN")
    p(f"referencia nocturna indexada: {nref} filas en {VENTANA_REF}; última fila de la referencia "
      f"{max(f['fecha_utc'] for f in filas)}")
    recs, casos = [], []
    n_dia = 0
    for v in C.VOLS:
        for r in json.load(open(C.DATA / f"{v}.json", encoding="utf-8"))["records"]:
            b = C.bucket(r.get("sensor"))
            if b is None:
                continue
            if (r.get("solar_zenith_deg") or 999) < 90:
                n_dia += 1
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            pc = r.get("primary_cluster") or {}
            ap = [x for x in (r.get("anomaly_pixels") or []) if x.get("lat") is not None]
            recs.append(dict(vol=v, b=b, dt=dt, noche=dt.strftime("%Y-%m-%d"), mes=dt.strftime("%Y-%m"), hora=r["datetime_utc"],
                             sensor=r.get("sensor"), dc=r.get("distance_class"), pc_vrp=pc.get("vrp_mw"), pc_n=pc.get("n_pixels"),
                             pc_lat=pc.get("centroid_lat"), pc_lon=pc.get("centroid_lon"), ap=ap, sz=r.get("solar_zenith_deg"),
                             t_bg=r.get("t_bg_k")))
            slim = {k: r.get(k) for k in BP.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: x.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for x in ap]
            casos.append([slim, inner[v]])
    pred = BP.correr_node(casos)
    for rec, pr in zip(recs, pred):
        rec["pub"] = pr[4]
        rec["disp"] = pr[3]
    p(f"records: {len(recs)}; con cenit solar < 90 (diurnos): {n_dia}; publicados por el tablero: {sum(r['pub'] for r in recs)}")
    en_ventana = [r for r in recs if VENTANA_REF[0] <= r["noche"] <= VENTANA_REF[1]]
    for r in recs:
        r["lab"] = None
    BP.etiquetar(en_ventana, por_vb, noche_sensor, noche_volcan)
    # ---- presencia por foco y mes
    filas_out = []
    rng = np.random.default_rng(161)
    nulo_pts = {}
    for v in C.VOLS:
        vent = C.GEO[v]["vent"]
        focos = focos_all[v]["focos"]
        pts = []
        while len(pts) < 300:
            dx, dy = rng.uniform(-20, 20, 2)
            if np.hypot(dx, dy) > 20:
                continue
            la = vent[0] + dy / 111.195
            lo = vent[1] + dx / (111.195 * np.cos(np.radians(vent[0])))
            if all(C.dist_km(fo["lat"], fo["lon"], la, lo) > 3 for fo in focos):
                pts.append((la, lo))
        nulo_pts[v] = np.array(pts)
    for r in recs:
        v = r["vol"]
        vent = C.GEO[v]["vent"]
        if r["ap"]:
            ax, ay = km_xy([x["lat"] for x in r["ap"]], [x["lon"] for x in r["ap"]], *vent)
        else:
            ax = ay = np.array([])
        nx, ny = km_xy(nulo_pts[v][:, 0], nulo_pts[v][:, 1], *vent)
        if len(ax):
            dmin = np.min(np.hypot(nx[:, None] - ax[None, :], ny[:, None] - ay[None, :]), axis=1)
            r["nulo"] = float((dmin <= R_FOCO_KM).mean())
        else:
            r["nulo"] = 0.0
        r["foco_det"], r["foco_pub"] = {}, {}
        for fo in focos_all[v]["focos"]:
            fx, fy = km_xy(fo["lat"], fo["lon"], *vent)
            r["foco_det"][fo["id"]] = int(len(ax) > 0 and np.min(np.hypot(ax - fx, ay - fy)) <= R_FOCO_KM)
            r["foco_pub"][fo["id"]] = int(bool(r["pub"]) and r["pc_lat"] is not None
                                          and C.dist_km(fo["lat"], fo["lon"], r["pc_lat"], r["pc_lon"]) <= R_FOCO_KM)
    meses = sorted({r["mes"] for r in recs})
    for v in C.VOLS:
        rv = [r for r in recs if r["vol"] == v]
        p(f"\n===== {v}: {len(rv)} records nocturnos de {rv[0]['hora']} a {rv[-1]['hora']}")
        for nombre, sel in (("todos los sensores", rv), ("VIIRS 375", [r for r in rv if r["b"] == "VIIRS375"]),
                            ("VIIRS 750", [r for r in rv if r["b"] == "VIIRS750"]), ("MODIS", [r for r in rv if r["b"] == "MODIS"])):
            p(f"  --- {nombre}: DETECTADO = pasadas con un píxel anómalo a <= 1 km del foco "
              f"(entre paréntesis, PUBLICADO: el cúmulo publicado cae a <= 1 km); n pasadas del mes en la 1.a fila")
            p("    " + "foco".ljust(10) + "".join(m[2:].rjust(10) for m in meses))
            p("    " + "n pasadas".ljust(10) + "".join(f"{sum(1 for r in sel if r['mes'] == m):10d}" for m in meses))
            p("    " + "nulo %".ljust(10) + "".join(
                (f"{100 * np.mean([r["nulo"] for r in sel if r["mes"] == m]):9.2f}%" if any(r['mes'] == m for r in sel) else "-".rjust(10))
                for m in meses))
            for fo in focos_all[v]["focos"]:
                celdas = []
                for m in meses:
                    s = [r for r in sel if r["mes"] == m]
                    if not s:
                        celdas.append("-".rjust(10))
                        continue
                    nd = sum(r["foco_det"][fo["id"]] for r in s)
                    npb = sum(r["foco_pub"][fo["id"]] for r in s)
                    celdas.append(f"{nd:4d}({npb:3d})".rjust(10))
                    filas_out.append(dict(vol=v, sensores=nombre, mes=m, foco=fo["id"], n_pasadas=len(s), n_det=nd, n_pub=npb,
                                          nulo_det=round(float(np.mean([r["nulo"] for r in s])), 4)))
                p("    " + fo["id"].ljust(10) + "".join(celdas))
        # control P1: cráter en pasadas con alerta vs negativos limpios (ventana de la referencia)
        for lab in ("pos", "neg_limpio"):
            s = [r for r in rv if r.get("lab") == lab]
            p(f"  control P1, {lab}: cráter detectado {sum(r['foco_det']['crater'] for r in s)}/{len(s)}, "
              f"publicado en el cráter {sum(r['foco_pub']['crater'] for r in s)}/{len(s)}")
    pd.DataFrame(filas_out).to_csv(OUT / "02_records_foco_mes.csv", index=False)
    # ---- capas del mapa: cúmulos publicados, por etiqueta de MIROVA (ventana de la referencia) y por régimen
    capas = defaultdict(list)
    for r in recs:
        if not r["pub"] or r["pc_lat"] is None:
            continue
        lab = r.get("lab") or "fuera_de_ventana"
        capas[r["vol"]].append(dict(t=r["hora"], s=r["b"], sensor=r["sensor"], lab=lab, lat=round(r["pc_lat"], 5),
                                    lon=round(r["pc_lon"], 5), vrp=r["pc_vrp"], n=r["pc_n"], dc=r["dc"],
                                    dv=round(C.dist_km(*C.GEO[r["vol"]]["vent"], r["pc_lat"], r["pc_lon"]), 2)))
    for v in C.VOLS:
        cnt = defaultdict(int)
        for c in capas[v]:
            cnt[c["lab"]] += 1
        p(f"capa {v}: cúmulos publicados por etiqueta {dict(cnt)}")
    # VE-01 y VE-02: nuestros records en esas pasadas (para el mapa)
    ve = []
    for v, hora in (("Tupungatito", "2026-09-29 04:54"), ("PuyehueCordonCaulle", "2026-10-21 05:48")):
        for r in recs:
            if r["vol"] == v and r["hora"] == hora:
                ve.append(dict(vol=v, t=hora, sensor=r["sensor"], pub=r["pub"], dc=r["dc"], pc_vrp=r["pc_vrp"], t_bg=r["t_bg"],
                               ap=[dict(lat=x["lat"], lon=x["lon"], bt=x.get("bt_k"), vrp=x.get("vrp_mw")) for x in r["ap"]]))
    json.dump(dict(capas=capas, ve=ve, meses=meses), open(OUT / "02_capas_mapa.json", "w", encoding="utf-8"), ensure_ascii=False)
    p("ve:", [(x["vol"], x["t"], x["sensor"], x["pub"], x["dc"], x["pc_vrp"], len(x["ap"])) for x in ve])


if __name__ == "__main__":
    main()
