# -*- coding: utf-8 -*-
"""S190: inventario de escenarios de falso positivo sobre las pasadas que el tablero publica, con su costo en
alertas protegidas de MIROVA.

POR QUÉ. Una defensa contra falsos positivos que calla una alerta que MIROVA publica (FN) es peor que el falso
positivo. Antes de proponer una MARCA o un FILTRO hay que saber, para cada escenario, cuántas pasadas publicadas
caen en su firma, cuántas de ellas publicó también MIROVA y cuántas noches con alerta protegida (lectura A, 1 MW o
más) se perderían si se filtrara. Este script sólo lee records que ya existen; no cambia producción ni el tablero.

Qué es «publicada»: el predicado `mirovaEqVrp` de `frontend/index.html` (vrp > 0, `distance_class == "summit"` y
centroide del cúmulo a `inner_radius_km` o menos; los 34 sin MIROVA con 5 km, como el tablero).
Referencia MIROVA: `referencia_mirova_unificada.cargar_referencia_unificada` + `clase_mirova.resumir_pasadas`,
pareo ±120 s por volcán y sensor (`clase_mirova.VENTANA_S`). Ventanas sanas (A119): canal «union» desde 2026-06-11
(OCR calibrado), canal «tabla» desde 2026-03-01. Los 34 no tienen referencia MIROVA: su columna de MIROVA es SIN DATO.
Noche = (volcán, fecha UTC) de las pasadas de 00 a 12 UTC (todas las nocturnas de Chile caen ahí).

Uso (desde la raíz del repo, en un checkout de origin/main):
    python experiments/_s190_escenarios_fp/escenarios_fp.py [--csv RUTA] > experiments/_s190_escenarios_fp/salida.txt
"""
from __future__ import annotations

import argparse
import bisect
import csv
import io
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import yaml  # noqa: E402

import clase_mirova as cm  # noqa: E402
import referencia_mirova_unificada as rmu  # noqa: E402

DESDE = {"union": datetime(2026, 6, 11), "tabla": datetime(2026, 3, 1)}
INNER_34 = 5.0
VENTANA = timedelta(seconds=cm.VENTANA_S)

# Umbrales de cada firma: declarados acá, con su variante de sensibilidad en `VARIANTES`.
DIST_LEJOS_KM = 2.0          # E1: fuera del cráter (los incendios no están en la cumbre)
LAT_FORESTAL = -36.0         # E1: al sur de esta latitud hay bosque y quemas agrícolas
MESES_VERANO = (12, 1, 2, 3)  # E1: temporada de incendios del centro-sur
DTBG_NUBE_K = -8.0           # E2: fondo más frío que la mediana del volcán-sensor-mes
TBG_NEVADO_K = 255.0         # E3: fondo de nieve o hielo
DT_NEVADO_K = 8.0            # E3: píxel apenas más tibio que el fondo
CENIT_BORDE = 55.0           # E5a: borde de barrido
AISLADO_H = 48               # E6: sin otra publicada del volcán a ±48 h
CELDA_GRADOS = 0.01          # E4b/E7: celda de ~1 km para la fuente fija
NOCHES_FIJA = 5              # E4b/E7: noches distintas en la misma celda
DIST_FIJA_KM = 1.5           # E4b/E7: fuera del cráter


def hav_km(la1, lo1, la2, lo2):
    r = 6371.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = p2 - p1, math.radians(lo2 - lo1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def bucket(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    return "VIIRS750" if sensor.endswith("_750") else "VIIRS375"


def ts(s):
    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")


def es_noche(r):
    dg = r.get("diag_codigo_mirova") or {}
    if dg.get("dayflag") is not None:
        return dg["dayflag"] == 0
    sz = r.get("solar_zenith_deg")
    return None if sz is None else sz > 90


def publicada(r, inner):
    """Copia literal de mirovaEqVrp (frontend/index.html) con includeFar=false, devuelve el VRP publicado."""
    pc = r.get("primary_cluster")
    if not pc:
        v = r.get("vrp_mw") or r.get("vrp_mir_mw") or 0
        return 0 if v > 50000 else v
    if r.get("distance_class") and r["distance_class"] != "summit":
        return 0
    if pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] > inner:
        return 0
    v = pc.get("vrp_mw") or 0
    return 0 if v > 50000 else v


# --------------------------------------------------------------------------------------------- volcanes y records
VOLC = {v["name"]: v for v in yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
TIER_A = sorted(n for n, v in VOLC.items() if v.get("inner_radius_km") is not None)
CENTRO = {n: (float(v["lat"]), float(v["lon"])) for n, v in VOLC.items()}


def cargar():
    """{(conjunto, volcán): {(sensor, datetime): (record, origen)}}. Para los 34 la sombra pisa a la historia."""
    out = defaultdict(dict)
    for n in TIER_A:
        for r in json.load(open(ROOT / "data/mirova_equivalent" / f"{n}.json", encoding="utf-8"))["records"]:
            out[("11", n)][(r["sensor"], r["datetime_utc"])] = (r, "mirova_equivalent")
    # data/mirova_equivalent/<uno de los 34>.json son fósiles de abril de 2026 (detector anterior, sin `regimen`);
    # el tablero no los lee (lee data/sombra_34), así que no entran.
    for d in ("historia_34", "sombra_34"):
        for f in sorted((ROOT / "data" / d).glob("*.json")):
            n = f.stem
            if n in TIER_A:
                continue
            for r in json.load(open(f, encoding="utf-8"))["records"]:
                out[("34", n)][(r["sensor"], r["datetime_utc"])] = (r, d)
    return out


def fila(conj, n, r, origen):
    dg = r.get("diag_codigo_mirova") or {}
    pc = r.get("primary_cluster") or {}
    cd = (dg.get("s1") or {}).get("celda_decisiva") or {}
    p1 = (dg.get("s1") or {}).get("pasada1") or {}
    inner = INNER_34 if conj == "34" else float(VOLC[n]["inner_radius_km"])
    t = ts(r["datetime_utc"])
    la, lo = r.get("final_hotspot_lat"), r.get("final_hotspot_lon")
    otro, d_otro = None, None
    if la is not None and lo is not None:
        for m, (cla, clo) in CENTRO.items():
            if m == n:
                continue
            d = hav_km(la, lo, cla, clo)
            if d_otro is None or d < d_otro:
                otro, d_otro = m, d
    d_propio = hav_km(la, lo, *CENTRO[n]) if la is not None else None
    return {
        "conj": conj, "volcan": n, "origen": origen, "sensor": r["sensor"], "bucket": bucket(r["sensor"]),
        "t": t, "noche": (n, t.date()) if t.hour < 12 else (n, f"{t.date()}D"), "es_noche": es_noche(r),
        "vrp_pub": publicada(r, inner), "vrp_mw": r.get("vrp_mw") or 0, "inner": inner,
        "npix": r.get("n_anomalous_pixels"), "dist": pc.get("centroid_dist_km"), "lat": la, "lon": lo,
        "d_propio_centro": d_propio, "vecino": otro, "d_vecino": d_otro,
        "cenit": r.get("sensor_zenith_deg"), "t_bg": r.get("t_bg_k"), "t_max": r.get("t_max_k"),
        "n_abs": dg.get("n_abs"), "zona": cd.get("zona"), "sd_nti": p1.get("sd_nti"),
        "celdas_sin_dato": dg.get("celdas_sin_dato"), "L_bk": dg.get("L_bk"), "via": r.get("via_codigo_mirova"),
        "motivo_vacio": dg.get("motivo_vacio"),
    }


# --------------------------------------------------------------------------------------------- MIROVA
def pasadas_mirova():
    filas = rmu.cargar_referencia_unificada()
    out = {}
    for canal in ("union", "tabla"):
        idx = defaultdict(list)
        for p in cm.resumir_pasadas(filas, canal=canal):
            if p.instante >= DESDE[canal]:
                idx[(p.volcano, p.sensor_bucket)].append(p)
        out[canal] = idx
    return out


def par_mirova(idx, f):
    best = None
    for p in idx.get((f["volcan"], f["bucket"]), []):
        dt = abs(p.instante - f["t"])
        if dt <= VENTANA + timedelta(seconds=60) and (best is None or dt < abs(best.instante - f["t"])):
            best = p   # +60 s: nuestro datetime_utc viene truncado al minuto
    return best


# --------------------------------------------------------------------------------------------- firmas
def preparar(F, todas):
    """Rasgos que dependen de otras pasadas: anomalía de fondo, aislamiento temporal, confirmación, celda fija."""
    # mediana de t_bg por volcán-sensor-mes sobre TODAS las pasadas nocturnas válidas (publicadas o no)
    tb = defaultdict(list)
    sd = defaultdict(list)
    for g in todas:
        if g["es_noche"] and g["t_bg"] is not None and not g["motivo_vacio"]:
            tb[(g["volcan"], g["bucket"], g["t"].month)].append(g["t_bg"])
        if g["es_noche"] and g["sd_nti"] is not None and not g["motivo_vacio"]:
            sd[(g["volcan"], g["bucket"])].append(g["sd_nti"])
    med_tb = {k: statistics.median(v) for k, v in tb.items() if len(v) >= 10}
    med_sd = {k: statistics.median(v) for k, v in sd.items() if len(v) >= 10}
    for g in todas:
        m = med_tb.get((g["volcan"], g["bucket"], g["t"].month))
        g["dtbg"] = (g["t_bg"] - m) if (m is not None and g["t_bg"] is not None) else None
        s = med_sd.get((g["volcan"], g["bucket"]))
        g["sd_rel"] = (g["sd_nti"] / s) if (s and g["sd_nti"] is not None) else None
    por_v = defaultdict(list)
    for f in F:
        por_v[f["volcan"]].append(f)
    for v, L in por_v.items():
        L.sort(key=lambda x: x["t"])
        ts_ = [x["t"] for x in L]
        buckets_noche = defaultdict(set)
        for x in L:
            buckets_noche[x["noche"]].add(x["bucket"])
        for i, f in enumerate(L):
            lo_ = bisect.bisect_left(ts_, f["t"] - timedelta(hours=AISLADO_H))
            hi_ = bisect.bisect_right(ts_, f["t"] + timedelta(hours=AISLADO_H))
            f["aislado"] = (hi_ - lo_) <= 1
            f["confirmada_otro_sensor"] = len(buckets_noche[f["noche"]] - {f["bucket"]}) > 0
    celda_noches = defaultdict(set)
    for f in F:
        if f["lat"] is not None and f["dist"] is not None and f["dist"] >= DIST_FIJA_KM:
            f["celda"] = (f["volcan"], round(f["lat"] / CELDA_GRADOS), round(f["lon"] / CELDA_GRADOS))
            celda_noches[f["celda"]].add(f["noche"])
        else:
            f["celda"] = None
    for f in F:
        f["noches_celda"] = len(celda_noches[f["celda"]]) if f["celda"] else 0
    return celda_noches


def firmas(f):
    lejos = f["dist"] is not None and f["dist"] >= DIST_LEJOS_KM
    sur = f["lat"] is not None and CENTRO[f["volcan"]][0] < LAT_FORESTAL
    contraste = f["n_abs"] == 0
    return {
        "E1_incendio_verano": lejos and sur and f["t"].month in MESES_VERANO,
        "E1b_lejano_10km": f["dist"] is not None and f["dist"] >= 10.0,
        "E1c_control_invierno": lejos and sur and f["t"].month not in MESES_VERANO,
        "E2_nube_fondo_frio": contraste and f["dtbg"] is not None and f["dtbg"] <= DTBG_NUBE_K,
        "E2b_nube_fondo_heterogeneo": contraste and f["sd_rel"] is not None and f["sd_rel"] >= 2.0,
        "E3_nevado_gradiente": contraste and (f["vrp_pub"] < 1.0) and f["t_bg"] is not None and f["t_max"] is not None
                                and f["t_bg"] < TBG_NEVADO_K and (f["t_max"] - f["t_bg"]) < DT_NEVADO_K,
        "E4_geotermia_lago_debil": f["volcan"] in ("Copahue", "PuyehueCordonCaulle") and f["vrp_pub"] < 1.0,
        "E4b_fuente_fija_fuera_crater": f["noches_celda"] >= NOCHES_FIJA,
        "E5a_borde_barrido_1px": f["cenit"] is not None and f["cenit"] >= CENIT_BORDE and f["npix"] == 1,
        "E5b_mas_cerca_de_vecino": f["d_vecino"] is not None and f["d_propio_centro"] is not None
                                    and f["d_vecino"] < f["d_propio_centro"],
        "E6_1px_aislado_sin_confirmar": f["npix"] == 1 and f["aislado"] and not f["confirmada_otro_sensor"],
        "E7_norte_fuente_fija": CENTRO[f["volcan"]][0] > -28.0 and f["noches_celda"] >= NOCHES_FIJA,
        "E8_diurna": f["es_noche"] is False,
        "E9_roi_incompleta": (f["celdas_sin_dato"] or 0) > 0 or f["L_bk"] == 0.0,
    }


# --------------------------------------------------------------------------------------------- informe
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=None, help="CSV con una fila por pasada publicada y sus firmas")
    a = ap.parse_args(argv)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    recs = cargar()
    todas = [fila(c, n, r, o) for (c, n), d in recs.items() for (r, o) in d.values()]
    F = [g for g in todas if g["vrp_pub"] > 0]
    celda_noches = preparar(F, todas)
    for f in F:
        f.update(firmas(f))
    claves = list(firmas(F[0]).keys())
    mir = pasadas_mirova()
    for f in F:
        for canal in ("union", "tabla"):
            p = par_mirova(mir[canal], f) if f["conj"] == "11" and f["t"] >= DESDE[canal] else None
            f[f"mir_{canal}"] = (p.estado if p else ("sin_fila" if f["conj"] == "11" and f["t"] >= DESDE[canal] else None))
            f[f"mir_{canal}_prot"] = bool(p and cm.es_protegida(p))
            f[f"mir_{canal}_vrp"] = p.vrp_mw if p else None

    print(f"raíz: {ROOT}")
    for conj in ("11", "34"):
        T = [g for g in todas if g["conj"] == conj]
        P = [f for f in F if f["conj"] == conj]
        tmin, tmax = min(g["t"] for g in T), max(g["t"] for g in T)
        print(f"conjunto {conj}: {len(T)} records, {len(P)} pasadas publicadas en {len({f['noche'] for f in P})} noches-volcán; "
              f"ventana {tmin:%Y-%m-%d} a {tmax:%Y-%m-%d}; nocturnas publicadas {sum(1 for f in P if f['es_noche'])}; "
              f"origen {dict(Counter(f['origen'] for f in P))}")

    # noches protegidas por canal: (volcán, noche) con >= 1 pasada protegida A de MIROVA en ventana
    prot_noche = {}
    for canal in ("union", "tabla"):
        S = set()
        for (vol, sb), L in mir[canal].items():
            for p in L:
                if cm.es_protegida(p) and p.instante.hour < 12:
                    S.add((vol, p.instante.date()))
        prot_noche[canal] = S
    pub_noche = defaultdict(list)
    for f in F:
        if f["conj"] == "11":
            pub_noche[f["noche"]].append(f)
    for canal in ("union", "tabla"):
        cub = [k for k in prot_noche[canal] if k in pub_noche]
        print(f"noches protegidas A ({canal}, desde {DESDE[canal]:%Y-%m-%d}): {len(prot_noche[canal])}; "
              f"con >= 1 pasada nuestra publicada esa noche: {len(cub)}")

    print("\nfirma | conj | publicadas (pasadas) | noches | %pasadas | volcanes top | "
          "MIROVA union: alerta/fp/minima/sin_geo/rutina/sin_fila (n en ventana) | protegidas A pareadas union/tabla | "
          "noches protegidas perdidas si se filtra union/tabla")
    resumen = {}
    for k in claves:
        for conj in ("11", "34"):
            P = [f for f in F if f["conj"] == conj]
            S = [f for f in P if f[k]]
            nn = len({f["noche"] for f in S})
            top = Counter(f["volcan"] for f in S).most_common(4)
            if conj == "11":
                est = Counter(f["mir_union"] for f in S if f["mir_union"] is not None)
                nven = sum(est.values())
                estt = Counter(f["mir_tabla"] for f in S if f["mir_tabla"] is not None)
                pp_u = sum(f["mir_union_prot"] for f in S)
                pp_t = sum(f["mir_tabla_prot"] for f in S)
                perd = {}
                for canal in ("union", "tabla"):
                    perd[canal] = sorted(nk for nk in prot_noche[canal]
                                         if nk in pub_noche and all(x[k] for x in pub_noche[nk]))
                mtxt = (f"{est.get('alerta',0)}/{est.get('fp',0)}/{est.get('minima',0)}/{est.get('sin_geometria',0)}/"
                        f"{est.get('rutina',0)}/{est.get('sin_fila',0)} (n={nven}); tabla alerta {estt.get('alerta',0)} "
                        f"de {sum(estt.values())}")
                ptxt = f"{pp_u}/{pp_t}"
                ltxt = f"{len(perd['union'])}/{len(perd['tabla'])}"
                resumen[(k, conj)] = {"n": len(S), "noches": nn, "est_union": dict(est), "n_union": nven,
                                      "est_tabla": dict(estt), "prot_par_union": pp_u, "prot_par_tabla": pp_t,
                                      "perdidas_union": [f"{v} {d}" for v, d in perd["union"]],
                                      "perdidas_tabla": [f"{v} {d}" for v, d in perd["tabla"]]}
            else:
                mtxt, ptxt, ltxt = "SIN DATO (MIROVA no publica los 34)", "-", "-"
                resumen[(k, conj)] = {"n": len(S), "noches": nn}
            print(f"{k} | {conj} | {len(S)} de {len(P)} | {nn} | {100*len(S)/max(1,len(P)):.1f} % | {top} | {mtxt} | {ptxt} | {ltxt}")

    # combinaciones propuestas: la unión de firmas puede perder noches que ninguna pierde sola
    COMBOS = {"MARCA_tablero": ("E1b_lejano_10km", "E3_nevado_gradiente", "E5a_borde_barrido_1px", "E5b_mas_cerca_de_vecino",
                                "E6_1px_aislado_sin_confirmar", "E9_roi_incompleta"),
              "FILTRO_laboratorio": ("E1b_lejano_10km", "E3_nevado_gradiente", "E5a_borde_barrido_1px", "E5b_mas_cerca_de_vecino")}
    NL = chr(10)
    print(NL + "combinaciones (si se filtraran todas a la vez):")
    for nombre, ks in COMBOS.items():
        for f in F:
            f[nombre] = any(f[k] for k in ks)
        for conj in ("11", "34"):
            S = [f for f in F if f["conj"] == conj and f[nombre]]
            txt = f"  {nombre} | {conj} | {len(S)} pasadas en {len({f['noche'] for f in S})} noches"
            if conj == "11":
                est = Counter(f["mir_union"] for f in S if f["mir_union"] is not None)
                perd = {c: sorted(nk for nk in prot_noche[c] if nk in pub_noche and all(x[nombre] for x in pub_noche[nk]))
                        for c in ("union", "tabla")}
                txt += (f" | MIROVA union {dict(est)} | protegidas A pareadas union {sum(f['mir_union_prot'] for f in S)} "
                        f"tabla {sum(f['mir_tabla_prot'] for f in S)} | noches protegidas perdidas union {perd['union']} "
                        f"tabla {perd['tabla']}")
            print(txt)

    # detalle: noches protegidas que se perderían, por firma (sólo las que pierden algo)
    print("\nnoches protegidas perdidas por firma (canal union | tabla):")
    for (k, conj), d in resumen.items():
        if conj == "11" and (d["perdidas_union"] or d["perdidas_tabla"]):
            print(f"  {k}: union {d['perdidas_union'][:12]}{' ...' if len(d['perdidas_union'])>12 else ''} | "
                  f"tabla {d['perdidas_tabla'][:12]}{' ...' if len(d['perdidas_tabla'])>12 else ''}")

    # E2 enriquecimiento: ¿las publicadas tienen fondo frío más a menudo que las pasadas nocturnas válidas?
    print("\nE2 control (A110): fracción con dtbg <= %.0f K entre detecciones (t_bg_k sólo existe cuando la pasada detectó algo: la base son todas las detecciones nocturnas, publicadas o lejanas, no las escenas despejadas sin detección) y entre publicadas:" % DTBG_NUBE_K)
    for conj in ("11", "34"):
        V = [g for g in todas if g["conj"] == conj and g["es_noche"] and not g["motivo_vacio"] and g.get("dtbg") is not None]
        P = [f for f in F if f["conj"] == conj and f.get("dtbg") is not None]
        a_ = sum(g["dtbg"] <= DTBG_NUBE_K for g in V)
        b_ = sum(f["dtbg"] <= DTBG_NUBE_K for f in P)
        print(f"  {conj}: detecciones {a_}/{len(V)} = {100*a_/max(1,len(V)):.1f} %; publicadas {b_}/{len(P)} = {100*b_/max(1,len(P)):.1f} %")
        for umbral in (-5.0, -12.0):
            a2 = sum(g["dtbg"] <= umbral for g in V)
            b2 = sum(f["dtbg"] <= umbral for f in P)
            print(f"     variante {umbral:.0f} K: detecciones {100*a2/max(1,len(V)):.1f} %, publicadas {100*b2/max(1,len(P)):.1f} %")

    # E1 control estacional: tasa de publicadas lejos del cráter en el sur, por mes, contra pasadas válidas del mes
    print("\nE1 control estacional (sur de %.0f°, centroide >= %.1f km): publicadas lejos / pasadas nocturnas válidas, por mes" %
          (LAT_FORESTAL, DIST_LEJOS_KM))
    for conj in ("11", "34"):
        V = Counter(g["t"].month for g in todas if g["conj"] == conj and g["es_noche"] and not g["motivo_vacio"]
                    and CENTRO[g["volcan"]][0] < LAT_FORESTAL)
        L = Counter(f["t"].month for f in F if f["conj"] == conj and (f["E1_incendio_verano"] or f["E1c_control_invierno"]))
        print(f"  {conj}: " + "; ".join(f"m{m}: {L.get(m,0)}/{V.get(m,0)}" for m in range(1, 13)))

    # E4b / E7: fuentes fijas fuera del cráter
    print("\nfuentes fijas fuera del cráter (celda ~1 km, >= %d noches, centroide >= %.1f km):" % (NOCHES_FIJA, DIST_FIJA_KM))
    for c, ns in sorted(celda_noches.items(), key=lambda x: -len(x[1])):
        if len(ns) < NOCHES_FIJA:
            continue
        S = [f for f in F if f["celda"] == c]
        alertas = sum(1 for f in S if f["mir_union"] == "alerta")
        con_ref = sum(1 for f in S if f["mir_union"] is not None)
        print(f"  {c[0]} ({c[1]*CELDA_GRADOS:.2f}, {c[2]*CELDA_GRADOS:.2f}): {len(ns)} noches, {len(S)} pasadas, "
              f"dist mediana {statistics.median(f['dist'] for f in S):.1f} km, VRP mediano {statistics.median(f['vrp_pub'] for f in S):.2f} MW, "
              f"sensores {dict(Counter(f['bucket'] for f in S))}, MIROVA alerta {alertas} de {con_ref} con referencia")

    # E1: lista de las pasadas de verano lejos del cráter (un incendio dura días y lo ven varios sensores)
    print("\nE1 detalle (verano, sur, centroide >= %.1f km):" % DIST_LEJOS_KM)
    for f in sorted((f for f in F if f["E1_incendio_verano"]), key=lambda x: (x["volcan"], x["t"])):
        print(f"  {f['volcan']} {f['t']:%Y-%m-%d %H:%M} {f['sensor']} {f['npix']} px {f['vrp_pub']:.2f} MW "
              f"({f['lat']:.3f}, {f['lon']:.3f}) {f['dist']:.1f} km noches_celda {f['noches_celda']}")

    # E6: dónde cae y qué dijo MIROVA, por sensor
    for conj in ("11", "34"):
        S = [f for f in F if f["conj"] == conj and f["E6_1px_aislado_sin_confirmar"]]
        print(f"\nE6 detalle {conj}: sensores {dict(Counter(f['bucket'] for f in S))}; centroide <= 1,5 km "
              f"{sum(1 for f in S if f['dist'] is not None and f['dist'] <= 1.5)} de {len(S)}; VRP >= 1 MW "
              f"{sum(1 for f in S if f['vrp_pub'] >= 1)}; MIROVA union por sensor "
              f"{dict(Counter((f['bucket'], f['mir_union']) for f in S if f['mir_union']))}")
    for k in ("E2_nube_fondo_frio", "E2b_nube_fondo_heterogeneo"):
        print(f"{k}: protegidas A pareadas (union) por volcán "
              f"{dict(Counter(f['volcan'] for f in F if f[k] and f['mir_union_prot']))}")
    print("\nE1b detalle (centroide >= 10 km):")
    for f in sorted((f for f in F if f["E1b_lejano_10km"]), key=lambda x: (x["volcan"], x["t"])):
        print(f"  {f['volcan']} {f['t']:%Y-%m-%d %H:%M} {f['sensor']} {f['npix']} px {f['vrp_pub']:.2f} MW "
              f"({f['lat']:.3f}, {f['lon']:.3f}) {f['dist']:.1f} km; MIROVA union {f['mir_union']} tabla {f['mir_tabla']}")

    # E5b: detalle de vecinos
    print("\nE5b detalle (volcán -> vecino más cercano al punto publicado):")
    print("  " + str(Counter((f["volcan"], f["vecino"]) for f in F if f["E5b_mas_cerca_de_vecino"]).most_common(12)))
    dup = Counter((f["sensor"], f["t"], round(f["lat"], 2), round(f["lon"], 2)) for f in F if f["lat"] is not None)
    print("  mismo píxel publicado por dos volcanes en la misma pasada: %d casos" % sum(1 for v in dup.values() if v > 1))

    if a.csv:
        campos = [c for c in F[0].keys() if c not in ("noche", "celda")]
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=campos + ["noche"])
            w.writeheader()
            for f in F:
                row = {c: f[c] for c in campos}
                row["noche"] = f"{f['noche'][0]} {f['noche'][1]}"
                w.writerow(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
