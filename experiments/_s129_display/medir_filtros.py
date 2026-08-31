# -*- coding: utf-8 -*-
"""S129 V4 — cuanto dato suprime cada filtro del frontend, medido sobre los JSON.

POR QUE: el pipeline persiste records que el dashboard nunca dibuja. Nadie habia
contado cuantos. Este script REPLICA cada condicion del frontend (index.html con
sus defaults) sobre data/mirova_equivalent/*.json y persiste los conteos por
volcan y por sensor a resultados.json. Ningun numero se transcribe a mano (S91).

Defaults replicados (los que ve el operador al abrir el dashboard):
  includeFarDistance = false   (index.html:812)
  USE_F5_CORE        = true    (index.html:1017)
  onlyPrimaryPixel   = true    (index.html:816)
  sensorVisible      = todos   (no suprime nada por defecto)

Read-only sobre el repo. Solo escribe en este directorio.
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from _s126_lib import ROOT, VENTS, bucket, cargar_mirova, haversine  # noqa: E402

# inner_radius_km oficial MIROVA por volcan (index.html lo lee de volcanoes.yaml;
# diario.html:227 y mosaico.html:207-217 lo hardcodean con los mismos valores).
INNER_KM = {
    "Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "Villarrica": 5,
    "PuyehueCordonCaulle": 20, "Copahue": 4, "NevadosDeChillan": 5,
    "Llaima": 5, "Chaiten": 5, "PlanchonPeteroa": 3, "Isluga": 5,
}
VOLS = list(INNER_KM)
CAP = 50000.0            # index.html:981,992,1090 · diario:256 · mosaico:249,255
F5_R_CORE_KM = 0.75      # index.html:1018
F5_BT_EXT_K = 295.0      # index.html:1019
PIXEL_CAP_PER_RECORD = 10  # index.html:2545
TOL_MS = 3600.0          # +-60 min del match MIROVA del frontend (index.html:1350)


def g(r, k, d=None):
    v = r.get(k, d)
    return d if v is None else v


def ts(s):
    """'YYYY-MM-DD HH:MM' UTC -> epoch segundos (equivalente a parseUtcMs)."""
    try:
        return time.mktime(time.strptime(str(s)[:16], "%Y-%m-%d %H:%M")) - time.timezone
    except Exception:
        return None


# ---------------------------------------------------------------- helpers JS
def is_valid_detection(r):
    """index.html:1371-1375."""
    return g(r, "vrp_mw", 0) > 0 or r.get("triggered_test1") is True


def is_summit_detection(r):
    """index.html:1377-1385."""
    if g(r, "vrp_mw", 0) == 0 and r.get("discarded_reason") and not r.get("triggered_test1"):
        return False
    if r.get("distance_class") == "summit":
        return True
    if r.get("distance_class") == "far":
        return False
    return g(r, "vrp_vent_mw", 0) > 0


def mirova_eq_vrp(r, inner_km, include_far=False):
    """index.html:972-993 (identico en diario:239 y mosaico:245, salvo el
    fallback sin primary_cluster, que en diario NO lleva cap — ver informe)."""
    pc = r.get("primary_cluster")
    if not pc:
        vfb = r.get("vrp_mw")
        if vfb is None:
            vfb = g(r, "vrp_mir_mw", 0)
        return 0.0 if vfb > CAP else float(vfb)
    dc = r.get("distance_class")
    if dc and dc != "summit" and not include_far:
        return 0.0
    cd = pc.get("centroid_dist_km")
    if not include_far and cd is not None and cd > inner_km:
        return 0.0
    vmw = g(pc, "vrp_mw", 0)
    return 0.0 if vmw > CAP else float(vmw)


def f5_core(r, inner_km):
    """index.html:1031-1064. Devuelve None si no se puede recomputar."""
    px = r.get("anomaly_pixels")
    if not px:
        return None
    pc = r.get("primary_cluster")
    if not pc or pc.get("centroid_lat") is None or pc.get("centroid_lon") is None:
        return None
    c = (pc["centroid_lat"], pc["centroid_lon"])
    cand = [p for p in px if p.get("lat") is not None and p.get("lon") is not None
            and haversine((p["lat"], p["lon"]), c) <= inner_km]
    if not cand:
        return None
    peak = max(cand, key=lambda p: g(p, "vrp_mw", 0))
    pk = (peak["lat"], peak["lon"])
    s = 0.0
    for p in cand:
        keep = (p is peak
                or haversine((p["lat"], p["lon"]), pk) <= F5_R_CORE_KM
                or g(p, "bt_k", 0) >= F5_BT_EXT_K)
        if keep:
            s += g(p, "vrp_mw", 0)
    return s


def mirova_eq_core(r, inner_km):
    """index.html:1071-1091 — F5' SOLO en VIIRS I-band; MODIS/V750 sin cambio."""
    base = mirova_eq_vrp(r, inner_km)
    if base <= 0:
        return base
    s = str(r.get("sensor") or "").upper()
    if not (s.startswith("VIIRS") and not s.endswith("_750")):
        return base
    core = f5_core(r, inner_km)
    if core is None or core <= 0:
        return base          # guard S96: el nucleo nunca borra una deteccion
    return 0.0 if core > CAP else core


def is_cirrus(r, inner_km, confirmed):
    """index.html:1112-1116."""
    if confirmed:
        return False
    t = r.get("t_max_k")
    if t is None or t >= 273.15:
        return False
    return mirova_eq_vrp(r, inner_km) > 10


def is_diffuse(r, inner_km, confirmed):
    """index.html:1131-1139."""
    if confirmed:
        return False
    pc = r.get("primary_cluster")
    t = r.get("t_max_k")
    if not pc or t is None or t >= 278.15:
        return False
    npx = g(pc, "n_pixels", 0)
    if npx < 100:
        return False
    eq = mirova_eq_vrp(r, inner_km)
    return eq >= 50 and (eq / npx) < 1.0


# ------------------------------------------------------- ground truth MIROVA
def cargar_ref_frontend(vol):
    """data/mirova/<vol>.json — LO QUE EL NAVEGADOR REALMENTE CRUZA (index:903).
    Lista de (epoch, bucket) de alertas con VRP>0 y clasificacion != NULO/RUTINA."""
    p = os.path.join(ROOT, "data", "mirova", vol + ".json")
    if not os.path.exists(p):
        return []
    d = json.load(open(p, encoding="utf-8"))
    out = []
    smap = {"MODIS": "modis", "VIIRS375": "v375", "VIIRS": "v750"}
    for m in d.get("records", []):
        cls = str(m.get("clasificacion") or "").upper()
        if cls in ("NULO", "RUTINA"):
            continue
        try:
            v = float(m.get("VRP_MW") or 0)
        except (TypeError, ValueError):
            continue
        if v <= 0:
            continue
        b = smap.get(str(m.get("sensor") or "").strip())
        t = ts(m.get("datetime_utc"))
        if b and t:
            out.append((t, b))
    return out


def confirmado_frontend(r, ref):
    """index.html:1346-1359 — mismo bucket de sensor, +-60 min."""
    b = bucket(r.get("sensor"))
    t = ts(r.get("datetime_utc"))
    if not b or t is None:
        return False
    return any(rb == b and abs(rt - t) <= TOL_MS for rt, rb in ref)


# ------------------------------------------------------------------- medicion
def nuevo():
    return defaultdict(lambda: defaultdict(float))


def main():
    ventana = ("2000-01-01", "2100-01-01")
    mirova_full, _ = cargar_mirova(ventana)   # CONS u OCR nocturnas (A11/A14/A76)

    res = {}
    glob = defaultdict(lambda: defaultdict(float))
    for vol in VOLS:
        p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
        if not os.path.exists(p):
            continue
        inner = INNER_KM[vol]
        recs = json.load(open(p, encoding="utf-8"))["records"]
        ref = cargar_ref_frontend(vol)
        gt = mirova_full.get(vol, {})          # {(fecha, bucket): vrp}

        C = nuevo()          # C[sensor][metrica]
        D = defaultdict(list)  # distancias, para MEDIANA (A70: la media enganna)
        maxdate = max((str(r.get("datetime_utc"))[:10] for r in recs), default="")

        for r in recs:
            b = bucket(r.get("sensor"))
            if b is None:
                continue
            pc = r.get("primary_cluster") or {}
            pcv = g(pc, "vrp_mw", 0)
            fecha = str(r.get("datetime_utc"))[:10]
            conf_front = confirmado_frontend(r, ref)
            conf_gt = (fecha, b) in gt
            dist = r.get("final_hotspot_dist_km")

            C[b]["records"] += 1
            if pcv > 0:
                C[b]["con_cluster"] += 1
            if is_valid_detection(r):
                C[b]["valid"] += 1

            # ---- cascada del chart / tabla / tarjetas / metricas (eqVrp:1909)
            motivo = None
            if not is_valid_detection(r):
                motivo = "f1_no_valida"
            else:
                dc = r.get("distance_class")
                cd = pc.get("centroid_dist_km")
                if not pc:
                    vfb = r.get("vrp_mw")
                    vfb = g(r, "vrp_mir_mw", 0) if vfb is None else vfb
                    if vfb > CAP:
                        motivo = "f4_cap50k"
                elif dc and dc != "summit":
                    motivo = "f2_clase_far"
                elif cd is not None and cd > inner:
                    motivo = "f3_pc_fuera_inner"
                elif pcv > CAP:
                    motivo = "f4_cap50k"
                elif is_cirrus(r, inner, conf_front):
                    motivo = "f5a_cirrus"
                elif is_diffuse(r, inner, conf_front):
                    motivo = "f5b_difuso"
                elif mirova_eq_vrp(r, inner) <= 0:
                    motivo = "f6_pc_cero"

            if motivo:
                C[b][motivo] += 1
                if pcv > 0:
                    C[b][motivo + "_mw_ocultos"] += pcv
                    C[b][motivo + "_con_mw"] += 1
                if conf_gt:
                    C[b][motivo + "_gt_confirmado"] += 1
                if dist is not None:
                    C[b][motivo + "_dist_sum"] += dist
                    C[b][motivo + "_dist_n"] += 1
                    D[(b, motivo)].append(dist)

                # diario.html / mosaico.html NO tienen isValidDetection (0 usos de
                # triggered_test1 / discarded_reason en ambos): un record que index
                # oculta por f1 SI se dibuja alla si su cluster es summit e intra-inner.
                # A46 en su forma pura: la CLASE la fija final_hotspot (path MIR
                # absoluto, que en MODIS salta al salar/valle — A69/A82) pero la
                # MAGNITUD sale del cluster. Cuantos far tienen el cluster en el
                # crater = cuanto del filtro "Solo crater" es error de etiqueta.
                if motivo == "f2_clase_far":
                    cdd = pc.get("centroid_dist_km")
                    if cdd is not None and cdd <= inner:
                        C[b]["f2b_cluster_intra_inner"] += 1
                        C[b]["f2b_mw"] += pcv
                        if pc.get("geo_class") == "summit":
                            C[b]["f2b_geoclass_summit"] += 1
                        if conf_gt:
                            C[b]["f2b_gt_confirmado"] += 1
                        D[(b, "f2b_cluster_km")].append(cdd)

                if motivo == "f1_no_valida" and mirova_eq_vrp(r, inner) > 0:
                    C[b]["f1b_index_oculta_diario_muestra"] += 1
                    C[b]["f1b_mw"] += pcv
                    if conf_gt:
                        C[b]["f1b_gt_confirmado"] += 1
                    if r.get("discarded_reason"):
                        C[b]["f1b_por_discard"] += 1
                    raw, floor = r.get("diag_vrp_raw_mw"), r.get("diag_vrp_floor_mw")
                    if raw is not None and floor is not None and raw < floor:
                        C[b]["f1b_por_piso_vrp"] += 1
                    if dist is not None:
                        D[(b, "f1b")].append(dist)
            else:
                C[b]["visible_chart"] += 1
                base = mirova_eq_vrp(r, inner)
                core = mirova_eq_core(r, inner)
                C[b]["mw_base_visible"] += base
                C[b]["mw_core_visible"] += core
                if core < base - 1e-9:
                    C[b]["f7_core_reduce"] += 1
                    C[b]["f7_mw_restados"] += base - core
                if conf_gt:
                    C[b]["visible_gt_confirmado"] += 1

            # ---- mapa: universo propio (index:2456) y filtro de lejanas (2539)
            if g(r, "vrp_mw", 0) > 0 or g(r, "vrp_mir_mw", 0) > 0:
                C[b]["mapa_universo"] += 1
                dc = r.get("distance_class")
                if not dc and r.get("final_hotspot_dist_km") is not None:
                    dc = "summit" if r["final_hotspot_dist_km"] <= inner else "far"
                if dc == "far":
                    C[b]["f8_mapa_far_oculto"] += 1
                    if conf_gt:
                        C[b]["f8_mapa_far_oculto_gt"] += 1
                else:
                    C[b]["mapa_dibujado"] += 1
                    npx = len(r.get("anomaly_pixels") or [])
                    if r.get("final_hotspot_source") in ("test1_roi", "test1_nti_peak"):
                        npx += 1          # index:2495 antepone el ancla honesta
                    npx = max(npx, 1)
                    C[b]["px_disponibles"] += npx
                    C[b]["f9_px_ocultos_primario"] += npx - 1
                    C[b]["f9_px_ocultos_toggle_todos"] += max(0, npx - PIXEL_CAP_PER_RECORD)

            # ---- divergencia mapa vs chart: visible en el mapa, ausente del chart
            if (g(r, "vrp_mw", 0) > 0 and is_summit_detection(r)
                    and motivo in ("f3_pc_fuera_inner", "f4_cap50k", "f5a_cirrus",
                                   "f5b_difuso", "f6_pc_cero")):
                C[b]["div_mapa_si_chart_no"] += 1

            # ---- ventana _recent (100 d): lo que el dashboard NO baja al abrir
            if maxdate and fecha < _menos100(maxdate):
                C[b]["f10_fuera_recent100d"] += 1

            # ---- cinturon MIROVA del filtro de artefacto: index cruza data/mirova
            # (CONS) mientras el ground truth real es CONS u OCR. Cuenta los casos
            # donde el cinturon del navegador falla pero el GT si confirma.
            if motivo in ("f5a_cirrus", "f5b_difuso") and conf_gt and not conf_front:
                C[b]["f5_cinturon_perdido"] += 1

        med = {f"{b}|{m}": round(sorted(x)[len(x) // 2], 2)
               for (b, m), x in D.items() if x}
        res[vol] = {"inner_radius_km": inner, "n_records": len(recs),
                    "max_fecha": maxdate, "dist_km_mediana": med,
                    "sensores": {k: {kk: round(vv, 3) for kk, vv in v.items()}
                                 for k, v in C.items()}}
        for b, v in C.items():
            for kk, vv in v.items():
                glob[b][kk] += vv
        print(f"{vol:22s} n={len(recs):6d} "
              f"visible={int(sum(C[b]['visible_chart'] for b in C)):6d}")
        del recs

    res["_GLOBAL"] = {b: {k: round(v, 3) for k, v in d.items()} for b, d in glob.items()}
    out = os.path.join(HERE, "resultados.json")
    json.dump(res, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("->", out)


def _menos100(fecha):
    import datetime as _dt
    d = _dt.date(int(fecha[:4]), int(fecha[5:7]), int(fecha[8:10])) - _dt.timedelta(days=100)
    return d.isoformat()


if __name__ == "__main__":
    main()
