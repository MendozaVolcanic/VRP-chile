# -*- coding: utf-8 -*-
"""S141, Fase 1 (v2): muestra de pasadas VIIRS 375 m para el probe del vecino del foco.

POR QUÉ. Sumamos 1 píxel donde MIROVA suma 3 o más (S139). Para medir dónde se pierden los
vecinos tibios hay que comparar el MISMO foco. El v1 no lo controlaba: en Nevados de Chillán el
píxel caliente de MIROVA estaba a 13 a 17 km del cráter (VERIFICADOR.md V5), así que la brecha
era entre dos anomalías distintas. Aquí una pasada sólo entra si el punto LAT/LON del OSF está a
≤ 0,75 km del cráter o de nuestro píxel pico persistido (corrección §6.1); las demás se reportan
en excluidas.json con su motivo y sus distancias. Las 40 pasadas del v1 ya se miraron y quedan
fuera por construcción.

INSTRUMENTO. El OSF está supervisado a mano: se usa pasada contra pasada, nunca para conteos.
Candidatos: MIROVA ≥ 3 píxeles y nosotros 1 (núcleo F5 del backfill). Controles: publicábamos
tantos como MIROVA. Selección determinista, repartida en el tiempo dentro de cada volcán.
Plan: docs/superpowers/plans/2026-09-15-fase1-probe-vecinos-v2.md

USO: python experiments/_s141_fase1_probe_v2/muestra.py --osf <VRP_GLOBAL_ARCHIVE_2025.csv>
Salida: pasadas.json, excluidas.json y muestra_resumen.json en esta carpeta.
"""
import argparse
import collections
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
for _p in (R, R / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from build_c2ab_windows import FOCAL  # noqa: E402  (mismo estrato que el v1)
from pipeline.f5_core import _hav_km  # noqa: E402

RADIO_FOCO_KM = 0.75
V1_PASADAS = R / "experiments" / "_s141_fase1_probe" / "pasadas.json"


def _finito(*xs):
    return all(x is not None and isinstance(x, (int, float, np.floating)) and math.isfinite(x) for x in xs)


def _num(v, nd=None):
    if not _finito(v):
        return None
    return float(v) if nd is None else round(float(v), nd)


def _espaciados(filas, k):
    if len(filas) <= k:
        return filas
    idx = sorted(set(np.linspace(0, len(filas) - 1, k).round().astype(int)))
    return [filas[i] for i in idx]


def _fila(x, clase, dc, dp):
    return {
        "volcan": x.vol, "pasada_utc": x.t_ours.strftime("%Y-%m-%d %H:%M"), "sensor": x.sensor,
        "clase": clase, "regimen": "focal" if x.vol in FOCAL else "nevado",
        "osf": {"Npix": int(x.Npix), "vrp_mw": float(x.osf_mw), "satzen": float(x.satzen),
                "t_osf": x.t_osf.strftime("%Y-%m-%d %H:%M"), "lat": _num(x.lat), "lon": _num(x.lon),
                "dist_crater_km": _num(dc, 3), "dist_pico_km": _num(dp, 3)},
        "persistido": {"pub_n": int(x.pub_n), "pub_mw": float(x.pub_mw), "pc_n": int(x.pc_n),
                       "t_bg_k": _num(x.t_bg), "pico_lat": _num(getattr(x, "pico_lat", None)),
                       "pico_lon": _num(getattr(x, "pico_lon", None))},
    }


def seleccionar(d, vents, excluir=(), por_volcan=6, controles_por_volcan=2):
    """Devuelve {"pasadas": [...], "excluidas": [...]}. `vents`: {volcan: (lat, lon)} del cráter;
    `excluir`: pares (volcan, pasada_utc) ya usados (v1)."""
    excluir = set(excluir)
    v = d[d.res == 375]
    universo = (("candidato", v[(v.Npix >= 3) & (v.pub_n == 1)], por_volcan),
                ("control", v[(v.Npix >= 3) & (v.pub_n >= v.Npix)], controles_por_volcan))
    pasadas, excluidas = [], []
    for clase, base, k in universo:
        for vol in sorted(base.vol.unique()):
            aptas = []
            for x in base[base.vol == vol].sort_values("t_osf").itertuples():
                pas = x.t_ours.strftime("%Y-%m-%d %H:%M")
                vlat, vlon = vents[vol]
                dc = _hav_km(x.lat, x.lon, vlat, vlon) if _finito(x.lat, x.lon) else None
                plat, plon = getattr(x, "pico_lat", None), getattr(x, "pico_lon", None)
                dp = _hav_km(x.lat, x.lon, plat, plon) if _finito(x.lat, x.lon, plat, plon) else None
                if (vol, pas) in excluir:
                    motivo = "pasada_del_v1"
                elif dc is None:
                    motivo = "sin_posicion_osf"
                elif min(dc, dp if dp is not None else math.inf) > RADIO_FOCO_KM:
                    motivo = "foco_mirova_lejos"
                else:
                    aptas.append(_fila(x, clase, dc, dp))
                    continue
                excluidas.append({"volcan": vol, "pasada_utc": pas, "clase": clase, "motivo": motivo,
                                  "dist_foco_crater_km": _num(dc, 3), "dist_foco_pico_km": _num(dp, 3)})
            pasadas.extend(_espaciados(aptas, k))
    return {"pasadas": pasadas, "excluidas": excluidas}


def resumen_muestra(sel):
    por = collections.defaultdict(lambda: {"candidato": 0, "control": 0})
    for x in sel["pasadas"]:
        por[x["volcan"]][x["clase"]] += 1
    exc = collections.defaultdict(collections.Counter)
    for x in sel["excluidas"]:
        exc[x["volcan"]][f"{x['clase']}:{x['motivo']}"] += 1
    return {"radio_foco_km": RADIO_FOCO_KM, "n_pasadas": len(sel["pasadas"]),
            "por_volcan": {k: por[k] for k in sorted(por)},
            "excluidas_por_volcan": {k: dict(exc[k]) for k in sorted(exc)}}


def _pico_persistido(m, fila):
    """Píxel pico (mayor VRP, primero en empate, igual que f5_core) del núcleo F5 del record pareado."""
    par = m.nearest(fila.vol, fila.res, fila.t_osf.to_pydatetime())
    if par is None:
        return None, None
    cp = m.core_pixels(par[1], m.INNER[fila.vol])
    if not cp:
        return None, None
    pk = 0
    for i in range(1, len(cp)):
        if (cp[i].get("vrp_mw") or 0) > (cp[pk].get("vrp_mw") or 0):
            pk = i
    return cp[pk].get("lat"), cp[pk].get("lon")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Muestra v2 del probe del vecino (S141)")
    ap.add_argument("--osf", required=True, help="ruta a VRP_GLOBAL_ARCHIVE_2025.csv")
    ap.add_argument("--por-volcan", type=int, default=6)
    ap.add_argument("--controles", type=int, default=2)
    a = ap.parse_args(argv)
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    import descomponer_magnitud_osf as m
    from run_pipeline import load_volcanoes  # mismos VOLCANO_OVERRIDES que usa el probe
    m.cargar(a.osf)
    d = m.build(0)
    osf = m.o[["t", "vol", "res", "LAT", "LON"]].rename(columns={"t": "t_osf", "LAT": "lat", "LON": "lon"})
    d = d.merge(osf, on=["t_osf", "vol", "res"], how="left").drop_duplicates(subset=["t_osf", "vol", "res"])
    picos = [_pico_persistido(m, x) for x in d.itertuples()]
    d["pico_lat"] = [p[0] for p in picos]
    d["pico_lon"] = [p[1] for p in picos]
    d["pico_lat"] = d["pico_lat"].astype(float)
    d["pico_lon"] = d["pico_lon"].astype(float)
    vents = {v["name"]: (v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])) for v in load_volcanoes()}
    excluir = {(x["volcan"], x["pasada_utc"]) for x in json.loads(V1_PASADAS.read_text(encoding="utf-8"))}
    sel = seleccionar(d, vents, excluir, a.por_volcan, a.controles)
    (HERE / "pasadas.json").write_text(json.dumps(sel["pasadas"], indent=1, ensure_ascii=False), encoding="utf-8")
    (HERE / "excluidas.json").write_text(json.dumps(sel["excluidas"], indent=1, ensure_ascii=False), encoding="utf-8")
    res = resumen_muestra(sel)
    (HERE / "muestra_resumen.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
