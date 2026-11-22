# -*- coding: utf-8 -*-
"""Variante «cumbre primero» de la regla de posición de la vía (S193). Ver PREREGISTRO.md de esta carpeta.

POR QUÉ: con «radiante» (D8'), una pasada con un alertado débil en el cráter y un cúmulo más radiante lejos queda `far` y
el tablero no la publica en la vista por defecto, aunque MIROVA publique esa pasada en la cumbre. Aquí se reaplica la
posición sobre los records guardados (sin reprocesar: los records traen todos los alertados con fila, columna y
temperatura de brillo) con las dos reglas, se pasan los records por el predicado real del tablero (node sobre
frontend/index.html, scripts/banco_paridad.py) y se cuenta contra MIROVA con tabla sola y con tabla más OCR (lectura A).

Sólo lectura del repo. Escribe las copias de los records en --tmp (fuera del repo) y la salida en esta carpeta.
Uso: python -B experiments/_s193_radiante_variante/medir_variante.py --tmp D:/vrp-trabajo/temporales/s193_radiante_variante
"""
from __future__ import annotations

import argparse
import collections
import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import yaml  # noqa: E402

import banco_paridad as bp  # noqa: E402
import comparacion_via_k as cvk  # noqa: E402
from clase_mirova import MODO_MINIMAS  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402

INICIO = "2026-03-01"
FIN_PRINCIPAL = "2026-11-18"
FIN_INFORMATIVO = "2026-11-20"
CODEX_12 = {("PuyehueCordonCaulle", "2026-05-09 06:18"), ("Lascar", "2026-03-15 05:00"), ("Lascar", "2026-04-25 05:00"),
            ("Lascar", "2026-06-12 05:00"), ("Lascar", "2026-10-01 05:18"), ("Isluga", "2026-03-20 05:06"),
            ("Isluga", "2026-03-24 05:30"), ("Isluga", "2026-04-07 06:12"), ("Isluga", "2026-06-17 05:06"),
            ("Isluga", "2026-09-28 05:12"), ("Isluga", "2026-10-03 05:18"), ("Lastarria", "2026-05-30 06:18")}


def familia(sensor):
    s = sensor or ""
    if s.startswith("MODIS"):
        return "MODIS"
    return "VIIRS750" if s.endswith("_750") else "VIIRS375"


def volcanes():
    y = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]
    return {v["name"]: v for v in y}


_GEOM = {}


def geometria(vol, fam, vdef):
    """Grilla de MIROVA y posición fraccionaria del cráter, con las mismas funciones y el mismo ancla que el procesador
    (vent_lat/vent_lon, o lat/lon si no hay vent; process_viirs_mod.py y process_modis.py, llamada a
    calcular_vrp_granulo)."""
    k = (vol, fam)
    if k not in _GEOM:
        cfg = MV.FAMILIAS[fam]
        g = MV.grilla_del_volcan(vol, paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
        vlat = vdef.get("vent_lat") if vdef.get("vent_lat") is not None else vdef["lat"]
        vlon = vdef.get("vent_lon") if vdef.get("vent_lon") is not None else vdef["lon"]
        _GEOM[k] = (g, MV.posicion_de(g, vlat, vlon))
    return _GEOM[k]


def cumulo(celdas, semilla):
    """Cúmulo 8-conexo de `semilla` dentro del conjunto `celdas` (como _cumulo_del_mas_radiante)."""
    vistos, pila = {semilla}, [semilla]
    while pila:
        a, b = pila.pop()
        for da in (-1, 0, 1):
            for db in (-1, 0, 1):
                q = (a + da, b + db)
                if q in celdas and q not in vistos:
                    vistos.add(q)
                    pila.append(q)
    return sorted(vistos)


def posicion(r, regla, g, pos, inner):
    """Posición del record con la regla pedida. Devuelve los campos que cambian y un diagnóstico."""
    paso_km = float(g["paso"]) / 1000.0
    bt = {(int(p["fila"]), int(p["col"])): float(p["bt_k"]) for p in r["anomaly_pixels"]}
    dist = {c: math.hypot(c[0] - pos[0], c[1] - pos[1]) * paso_km for c in bt}
    btmax = max(bt.values())
    empate = sum(1 for v in bt.values() if v == btmax) > 1
    dentro = [c for c in bt if dist[c] <= inner]
    if regla == "cumbre" and dentro:
        semilla = max(dentro, key=lambda c: (bt[c], -dist[c]))
        empate = empate or sum(1 for c in dentro if bt[c] == bt[semilla]) > 1
    else:
        semilla = max(bt, key=lambda c: (bt[c], -dist[c]))
    cu = cumulo(set(bt), semilla)
    fr = sum(a for a, _ in cu) / len(cu)
    fc = sum(b for _, b in cu) / len(cu)
    dcen = math.hypot(fr - pos[0], fc - pos[1]) * paso_km
    clat, clon = MV.latlon_de(g, fr, fc)
    pico = max(cu, key=lambda c: bt[c])
    plat, plon = MV.latlon_de(g, *pico)
    dpico = math.hypot(pico[0] - pos[0], pico[1] - pos[1]) * paso_km
    campos = {"distance_class": "summit" if dcen <= inner else "far",
              "pc": {"n_pixels": len(cu), "centroid_lat": round(clat, 5), "centroid_lon": round(clon, 5),
                     "centroid_dist_km": round(dcen, 3)},
              "hotspot_lat": round(plat, 5), "hotspot_lon": round(plon, 5), "hotspot_dist_km": round(dpico, 3),
              "final_hotspot_lat": round(clat, 5), "final_hotspot_lon": round(clon, 5),
              "final_hotspot_dist_km": round(dcen, 3), "t_max_k": round(bt[pico], 2)}
    diag = {"empate": empate, "n_dentro": len(dentro), "dist_px": dist, "min_dist": min(dist.values())}
    return campos, diag


def aplicar(r, campos):
    out = copy.deepcopy(r)
    out["distance_class"] = campos["distance_class"]
    out["primary_cluster"].update(campos["pc"])
    for k in ("hotspot_lat", "hotspot_lon", "hotspot_dist_km", "final_hotspot_lat", "final_hotspot_lon",
              "final_hotspot_dist_km", "t_max_k"):
        out[k] = campos[k]
    return out


def preparar(tmp):
    """Copias de los records de la ventana: original, «radiante» recalculado y variante. Controles C1 y C2."""
    vdefs = volcanes()
    c1 = collections.Counter()
    c1_excepciones, c2_malos = [], []
    info = {}  # (vol, sensor, dt) -> diagnóstico por record
    for nombre in ("original", "radiante", "cumbre"):
        (tmp / nombre).mkdir(parents=True, exist_ok=True)
    for vol in bp.VOLS:
        inner = float(vdefs[vol]["inner_radius_km"])
        d = json.loads((ROOT / "data" / "mirova_equivalent" / f"{vol}.json").read_text(encoding="utf-8"))
        recs = [r for r in d["records"] if INICIO <= r.get("datetime_utc", "")[:10] <= FIN_INFORMATIVO]
        rad, cum = [], []
        for r in recs:
            if r.get("via_codigo_mirova") is not True or not r.get("n_anomalous_pixels") or not r.get("primary_cluster"):
                rad.append(r)
                cum.append(r)
                continue
            g, pos = geometria(vol, familia(r["sensor"]), vdefs[vol])
            cr, dr = posicion(r, "radiante", g, pos, inner)
            cc, dc_ = posicion(r, "cumbre", g, pos, inner)
            # C2: distancias de cada alertado
            for p in r["anomaly_pixels"]:
                e = abs(dr["dist_px"][(int(p["fila"]), int(p["col"]))] - p["dist_km"])
                c1["c2_alertados"] += 1
                if e > 0.006:
                    c2_malos.append((vol, r["datetime_utc"], r["sensor"], p["dist_km"], round(e, 4)))
            # C1: radiante recalculado contra lo guardado
            pc = r["primary_cluster"]
            igual = (cr["distance_class"] == r.get("distance_class")
                     and abs(cr["pc"]["centroid_dist_km"] - (pc.get("centroid_dist_km") or -9)) <= 0.0011)
            c1["c1_records"] += 1
            c1["c1_iguales"] += igual
            if not igual:
                c1_excepciones.append({"vol": vol, "dt": r["datetime_utc"], "sensor": r["sensor"],
                                       "guardado": [r.get("distance_class"), pc.get("centroid_dist_km")],
                                       "recalculado": [cr["distance_class"], cr["pc"]["centroid_dist_km"]],
                                       "empate_bt": dr["empate"]})
            rad.append(aplicar(r, cr))
            cum.append(aplicar(r, cc))
            info[(vol, r["sensor"], r["datetime_utc"])] = {
                "min_dist": round(dr["min_dist"], 3), "n_dentro": dc_["n_dentro"], "npix": len(r["anomaly_pixels"]),
                "dc_rad": cr["distance_class"], "dc_cum": cc["distance_class"],
                "d_rad": cr["pc"]["centroid_dist_km"], "d_cum": cc["pc"]["centroid_dist_km"],
                "cambia": cr["pc"]["centroid_dist_km"] != cc["pc"]["centroid_dist_km"],
                "empate": dr["empate"] or dc_["empate"], "vrp_mw": r.get("vrp_mw")}
        for nombre, lst in (("original", recs), ("radiante", rad), ("cumbre", cum)):
            (tmp / nombre / f"{vol}.json").write_text(json.dumps({"records": lst}), encoding="utf-8")
    return c1, c1_excepciones, c2_malos, info


def evaluar(carpeta, coords, inner, ventana):
    sin_medir = cvk.escenas_sin_medir(carpeta)
    return cvk.quitar_escenas_sin_medir(bp.cargar_nuestros(coords, inner, ventana, data=carpeta), sin_medir)


def clave(p):
    return (p["vol"], p["sensor"], p["dt"].strftime("%Y-%m-%d %H:%M"))


def control_c4(coords, inner):
    """Record sintético: un alertado débil en el cráter de Láscar (V750) y un cúmulo fuerte a unos 15 km."""
    vdefs = volcanes()
    g, pos = geometria("Lascar", "VIIRS750", vdefs["Lascar"])
    r0, c0 = int(round(pos[0])), int(round(pos[1]))
    lejos = [(r0, c0 + 20), (r0, c0 + 21), (r0 + 1, c0 + 20)]
    pix = [{"fila": r0, "col": c0, "bt_k": 300.0, "lat": 0, "lon": 0, "dist_km": 0}] + \
          [{"fila": a, "col": b, "bt_k": 400.0, "lat": 0, "lon": 0, "dist_km": 0} for a, b in lejos]
    base = {"sensor": "VIIRS_NOAA20_750", "via_codigo_mirova": True, "vrp_mw": 3.0, "n_anomalous_pixels": 4,
            "anomaly_pixels": pix, "t_max_k": 400.0, "triggered_test1": False, "vrp_vent_mw": 0.0,
            "primary_cluster": {"vrp_mw": 3.0, "n_pixels": 3, "single_pixel_mode": False}}
    out = {}
    for regla in ("radiante", "cumbre"):
        c, _ = posicion(base, regla, g, pos, inner["Lascar"])
        rr = aplicar(base, c)
        slim = {k: rr.get(k) for k in bp.CAMPOS_JS}
        out[regla] = {"dc": rr["distance_class"], "dist": rr["primary_cluster"]["centroid_dist_km"],
                      "pub": bp.correr_node([[slim, inner["Lascar"]]])[0][4]}
    out["ok"] = out["radiante"]["pub"] == 0 and out["cumbre"]["pub"] == 1
    return out


def contar(rad, cum, info, fin):
    """Métricas G1, G2, L1, L2, L3, L4 e informativas, por lectura, sensor y volcán, en la ventana hasta `fin`."""
    res = {}
    for lectura in ("tabla", "combinado"):
        filas = []
        for p in rad[lectura]:
            if p["noche"] > fin:
                continue
            q = cum[lectura].get(clave(p))
            if q is None:
                continue
            i = info.get(clave(p), {})
            filas.append({"vol": p["vol"], "b": p["b"], "sensor": p["sensor"], "dt": clave(p)[2], "noche": p["noche"],
                          "lab": p["lab"], "prot": p["protegida"], "neg_estricto": p.get("neg_estricto", False),
                          "pub_r": p["pub"], "pub_c": q["pub"], "disp_c": q["disp"], "vrp_mirova": p["vrp_mirova"],
                          "dc_r": p["dc"], "dc_c": q["dc"], "npix": i.get("npix", 0), "min_dist": i.get("min_dist"),
                          "n_dentro": i.get("n_dentro"), "d_rad": i.get("d_rad"), "d_cum": i.get("d_cum"),
                          "empate": i.get("empate", False)})
        estratos = collections.defaultdict(collections.Counter)
        detalle = collections.defaultdict(list)
        for f in filas:
            for e in ("total", "b=" + f["b"], "vol=" + f["vol"], f"vol_b={f['vol']}|{f['b']}"):
                c = estratos[e]
                c["pasadas"] += 1
                c["cambia_posicion"] += f["d_rad"] is not None and f["d_rad"] != f["d_cum"]
                c["cambia_pub"] += f["pub_r"] != f["pub_c"]
                if f["lab"] == "pos":
                    c["pos"] += 1
                    c["G2_alertas_recuperadas"] += f["pub_r"] == 0 and f["pub_c"] == 1
                    c["alertas_perdidas"] += f["pub_r"] == 1 and f["pub_c"] == 0
                    if f["prot"]:
                        c["protegidas"] += 1
                        c["protegidas_no_pub_radiante"] += f["pub_r"] == 0
                        c["protegidas_no_pub_cumbre"] += f["pub_c"] == 0
                        c["G1_protegidas_recuperadas"] += f["pub_r"] == 0 and f["pub_c"] == 1
                        c["L1_protegidas_perdidas"] += f["pub_r"] == 1 and f["pub_c"] == 0
                if f["lab"] == "neg_limpio":
                    c["neg_limpio"] += 1
                    c["neg_limpio_pub_radiante"] += f["pub_r"]
                    c["L2_nuevas_en_neg_limpio"] += f["pub_r"] == 0 and f["pub_c"] == 1
                    c["L2_quitadas_en_neg_limpio"] += f["pub_r"] == 1 and f["pub_c"] == 0
                    c["L2_nuevas_en_neg_estricto"] += f["neg_estricto"] and f["pub_r"] == 0 and f["pub_c"] == 1
                if f["lab"] == "far_ref":
                    c["far_ref"] += 1
                    c["L3_nuevas_en_far_ref"] += f["pub_r"] == 0 and f["pub_c"] == 1
                    c["L3_quitadas_en_far_ref"] += f["pub_r"] == 1 and f["pub_c"] == 0
                if f["lab"] in ("sin_info", "sin_geometria"):
                    c["nuevas_en_" + f["lab"]] += f["pub_r"] == 0 and f["pub_c"] == 1
                    c["quitadas_en_" + f["lab"]] += f["pub_r"] == 1 and f["pub_c"] == 0
                if f["npix"] and f["lab"] in ("pos", "far_ref"):
                    ref = "summit" if f["lab"] == "pos" else "far"
                    c["L4_n"] += 1
                    c["L4_igual_radiante"] += f["dc_r"] == ref
                    c["L4_igual_cumbre"] += f["dc_c"] == ref
            if f["pub_r"] != f["pub_c"]:
                detalle[f["lab"] + ("_protegida" if f["prot"] else "")].append(f)
        for c in estratos.values():
            if c["L4_n"]:
                c["L4_pct_radiante"] = round(100 * c["L4_igual_radiante"] / c["L4_n"], 2)
                c["L4_pct_cumbre"] = round(100 * c["L4_igual_cumbre"] / c["L4_n"], 2)
        # noches-satélite con protegida (A94): publica alguna pasada de la noche
        nn = collections.defaultdict(lambda: {"prot": False, "r": 0, "c": 0})
        for f in filas:
            e = nn[(f["vol"], f["sensor"], f["noche"])]
            e["prot"] |= f["prot"]
            e["r"] |= f["pub_r"]
            e["c"] |= f["pub_c"]
        noches = collections.Counter()
        for e in nn.values():
            if e["prot"]:
                noches["noches_con_protegida"] += 1
                noches["sin_pub_radiante"] += not e["r"]
                noches["sin_pub_cumbre"] += not e["c"]
                noches["recuperadas"] += (not e["r"]) and e["c"]
                noches["perdidas"] += e["r"] and not e["c"]
        # C5: protegidas no publicadas con «radiante» que tienen un alertado dentro del inner
        c5 = sorted((f["vol"], f["dt"]) for f in filas if f["lab"] == "pos" and f["prot"] and f["pub_r"] == 0
                    and f["n_dentro"])
        res[lectura] = {"estratos": {k: dict(v) for k, v in sorted(estratos.items())}, "noches": dict(noches),
                        "detalle_cambios": {k: v for k, v in sorted(detalle.items())}, "c5": c5}
    return res


def veredicto(r):
    t, c = r["tabla"]["estratos"]["total"], r["combinado"]["estratos"]["total"]
    L1 = (t.get("L1_protegidas_perdidas", 0), c.get("L1_protegidas_perdidas", 0))
    G1c = c.get("G1_protegidas_recuperadas", 0)
    if max(L1) > 0:
        return "NO GANA (veto: pierde protegidas)", L1, G1c
    if G1c == 0:
        return "NO GANA (sin sustrato: no recupera protegidas)", L1, G1c
    caida = t.get("L4_pct_radiante", 0) - t.get("L4_pct_cumbre", 0)
    if t.get("L2_nuevas_en_neg_limpio", 0) <= G1c and caida <= 0.5:
        return "GANA", L1, G1c
    return "DECIDE NICOLÁS (recupera protegidas, pero su costo pasa el corte)", L1, G1c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmp", required=True)
    a = ap.parse_args()
    tmp = Path(a.tmp)
    c1, c1_exc, c2_malos, info = preparar(tmp)
    print("C1 radiante recalculado = guardado:", c1["c1_iguales"], "de", c1["c1_records"], "| excepciones",
          len(c1_exc))
    for e in c1_exc[:20]:
        print("   ", e)
    print("C2 alertados con distancia reproducida a 0,006 km:", c1["c2_alertados"] - len(c2_malos), "de",
          c1["c2_alertados"])
    for e in c2_malos[:10]:
        print("   ", e)
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    yinner = {v: float(d["inner_radius_km"]) for v, d in volcanes().items() if v in bp.VOLS}
    print("inner del tablero = inner de volcanoes.yaml:", inner == yinner)
    ventana = (INICIO, FIN_INFORMATIVO)
    pas = {n: evaluar(tmp / n, coords, inner, ventana) for n in ("original", "radiante", "cumbre")}
    po = {clave(p): p["pub"] for p in pas["original"]}
    c3 = sum(po.get(clave(p)) == p["pub"] for p in pas["radiante"])
    print("claves únicas (vol, sensor, minuto):", len({clave(p) for p in pas["radiante"]}), "de", len(pas["radiante"]))
    print("C3 pub(original) = pub(radiante recalculado):", c3, "de", len(pas["radiante"]), "| pasadas originales",
          len(pas["original"]))
    c4 = control_c4(coords, inner)
    print("C4 sintético:", c4)
    filas_ref = cargar_referencia_unificada()
    refs = {"tabla": [f for f in filas_ref if f["source"] == "CONS"], "combinado": filas_ref}
    rad, cum = {}, {}
    for nombre, fil in refs.items():
        idx = bp.indexar_referencia(fil, coords, ventana, regla_minimas=MODO_MINIMAS)
        rad[nombre] = cvk.etiquetar(pas["radiante"], idx)
        cum[nombre] = {clave(p): p for p in cvk.etiquetar(pas["cumbre"], idx)}
    salida = {"meta": {"base": "76f52c7ec", "ventana_principal": [INICIO, FIN_PRINCIPAL],
                       "ventana_informativa": [INICIO, FIN_INFORMATIVO], "regla_minimas": MODO_MINIMAS,
                       "n_filas_referencia": {k: len(v) for k, v in refs.items()}},
              "controles": {"C1": {"iguales": c1["c1_iguales"], "records": c1["c1_records"], "excepciones": c1_exc},
                            "C2": {"alertados": c1["c2_alertados"], "malos": c2_malos},
                            "C3": {"iguales": c3, "pasadas": len(pas["radiante"]), "originales": len(pas["original"])},
                            "C4": c4},
              "principal": contar(rad, cum, info, FIN_PRINCIPAL),
              "informativa": contar(rad, cum, info, FIN_INFORMATIVO)}
    salida["principal"]["veredicto"] = veredicto(salida["principal"])
    salida["informativa"]["veredicto"] = veredicto(salida["informativa"])
    c5 = set(salida["principal"]["combinado"]["c5"])
    salida["controles"]["C5"] = {"nuestras": sorted(c5), "codex_12": sorted(CODEX_12),
                                 "en_ambas": len(c5 & CODEX_12), "solo_nuestras": sorted(c5 - CODEX_12),
                                 "solo_codex": sorted(CODEX_12 - c5)}
    out = Path(__file__).with_name("resultado.json")
    out.write_text(json.dumps(salida, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("C5:", {k: v for k, v in salida["controles"]["C5"].items() if k not in ("codex_12",)})
    for vent in ("principal", "informativa"):
        print(f"== {vent}: veredicto {salida[vent]['veredicto']}")
        for lectura in ("tabla", "combinado"):
            print(f"  -- {lectura}: noches {salida[vent][lectura]['noches']}")
            for e, c in salida[vent][lectura]["estratos"].items():
                if e == "total" or e.startswith("b=") or (vent == "principal" and c.get("cambia_pub")):
                    print(f"    {e:34s}", {k: v for k, v in c.items() if v})
    print("->", out)


if __name__ == "__main__":
    main()
