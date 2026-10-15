# -*- coding: utf-8 -*-
"""Tarea 1.14, parte A: descomposicion EXACTA de la razon contra MIROVA, pasada por pasada, con el OSF v2.5.

POR QUE el OSF: es la unica fuente donde MIROVA dice, por pasada, cuantos pixeles sumo (Npix) y cuanta
radiancia caliente y de fondo sumo (Tot_Lmir_hot, Tot_Lmir_bk). Con eso y nuestros anomaly_pixels la razon
se separa sin supuestos en recorte, conteo, nivel caliente y fondo (PREREGISTRO.md). El costo: es 2025, y
nuestros records de 2025 son del regimen previo a #535 (A104). La parte B mira 2026 con lo que se puede.

Uso:  python a_osf_exacto.py [--osf RUTA_CSV]
Salida: a_osf_exacto_salida.json y a_osf_exacto_salida.txt (junto a este script).
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(AQUI))

from pipeline.f5_core import f5_core_vrp_mw  # noqa: E402
import comun as C  # noqa: E402

OSF_DEFECTO = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv")
MAP = {"Láscar": "Lascar", "Lastarria": "Lastarria", "Isluga": "Isluga", "Llaima": "Llaima", "Villarrica": "Villarrica",
       "Chaitén": "Chaiten", "Copahue": "Copahue", "Planchón-Peteroa": "PlanchonPeteroa",
       "Puyehue-Cordón Caulle": "PuyehueCordonCaulle", "Chillán, Nevados de": "NevadosDeChillan",
       "Tupungatito": "Tupungatito"}
RES2B = {375: "VIIRS375", 750: "VIIRS750", 1000: "MODIS"}
T0, T1 = datetime(2025, 2, 15), datetime(2025, 12, 1)
FACT = ["ln_rec", "ln_n", "ln_hot", "ln_bg", "ln_sel"]   # ln_sel = ln_n + ln_hot (seleccion neta)


def crater(r, v):
    """Predicado de S139 (eje 6): cumulo con energia dentro del inner, summit o sin clase."""
    pc = r.get("primary_cluster") or {}
    vr, d = pc.get("vrp_mw") or 0, pc.get("centroid_dist_km")
    return vr > 0 and d is not None and d <= C.INNER[v] and vr <= 50000 and r.get("distance_class") in ("summit", None)


def cargar_nuestros():
    ours = defaultdict(list)
    for v in C.VOLS:
        for r in json.load(open(ROOT / f"data/mirova_equivalent/{v}.json", encoding="utf-8"))["records"]:
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
            if T0 - timedelta(hours=7) <= dt < T1 + timedelta(hours=7):
                ours[(v, C.bucket(r["sensor"]))].append((dt, r))
    for k in ours:
        ours[k].sort(key=lambda x: x[0])
    return ours


def mas_cercano(ours, v, b, t, tol_min=10):
    lista = ours.get((v, b), [])
    ts = [x[0] for x in lista]
    i = bisect.bisect_left(ts, t)
    best = None
    for j in (i - 1, i):
        if 0 <= j < len(lista) and abs((lista[j][0] - t).total_seconds()) <= tol_min * 60:
            if best is None or abs((lista[j][0] - t).total_seconds()) < abs((best[0] - t).total_seconds()):
                best = lista[j]
    return best


def pares(osf, ours, shift_h=0):
    filas, motivos = [], Counter()
    for x in osf.itertuples(index=False):
        b = RES2B[int(x.Resolution)]
        m = mas_cercano(ours, x.vol, b, x.t.to_pydatetime() + timedelta(hours=shift_h))
        if m is None:
            motivos["sin_record"] += 1
            continue
        r = m[1]
        if not crater(r, x.vol):
            motivos["no_crater"] += 1
            continue
        pc = r["primary_cluster"]
        if b == "VIIRS375":
            f5 = r.get("f5_core_vrp_mw")
            d_pub = f5 if f5 is not None else pc["vrp_mw"]
        else:
            d_pub = pc["vrp_mw"]
        s_in, n_pos, lh, n_cero = C.pixeles_inner(r, x.vol)
        fila = {"vol": x.vol, "b": b, "t": x.t.isoformat(), "noche_id": f"{x.vol}|{x.t.date()}",
                "satzen": abs(float(x.SatZen)), "Npix": int(x.Npix), "V_M": float(x.VRP) / 1e6,
                "Lh_M": float(x.Tot_Lmir_hot) / x.Npix, "Lbk_M": float(x.Tot_Lmir_bk) / x.Npix,
                "D": d_pub, "S_in": s_in, "n_pos": n_pos, "n_cero": n_cero, "Lh": lh,
                "fuente": r.get("final_hotspot_source"), "kernel": x.vol in C.KERNEL, "rec": r}
        filas.append(fila)
    return filas, motivos


def factores(f):
    """Logaritmos de los cuatro factores; None con el motivo si la pasada no se puede separar."""
    if not (f["D"] and f["D"] > 0):
        return "D_cero"
    if f["S_in"] <= 0 or f["n_pos"] == 0:
        return "S_in_cero"
    if f["Lh_M"] <= f["Lbk_M"]:
        return "mirova_exceso_no_positivo"
    lbg = C.fondo_implicito(f["S_in"], f["n_pos"], f["Lh"], f["b"])
    if f["Lh"] <= f["Lbk_M"]:
        return "nuestro_caliente_bajo_fondo_mirova"
    f["Lbg"] = lbg
    f["R"] = f["D"] / f["V_M"]
    f["ln_rec"] = math.log(f["D"] / f["S_in"])
    f["ln_n"] = math.log(f["n_pos"] / f["Npix"])
    f["ln_hot"] = math.log((f["Lh"] - f["Lbk_M"]) / (f["Lh_M"] - f["Lbk_M"]))
    f["ln_bg"] = math.log((f["Lh"] - lbg) / (f["Lh"] - f["Lbk_M"]))
    f["banda_z"] = C.banda_z(f["satzen"])
    f["ln_sel"] = f["ln_n"] + f["ln_hot"]
    # Verificador de #814 (arreglo a): la particion selección / fondo depende de la bisagra. Arriba la bisagra es
    # NUESTRO nivel caliente (fondo medido a Lh); la alternativa es el caliente de MIROVA (fondo medido a Lh_M).
    # El promedio de las dos ordenes es el valor de Shapley de dos factores. ln_rec, ln_n y el producto no cambian.
    if f["Lh_M"] > lbg:
        f["ln_hot2"] = math.log((f["Lh"] - lbg) / (f["Lh_M"] - lbg))
        f["ln_bg2"] = math.log((f["Lh_M"] - lbg) / (f["Lh_M"] - f["Lbk_M"]))
        f["ln_sel2"] = f["ln_n"] + f["ln_hot2"]
        f["ln_sel_sh"] = (f["ln_sel"] + f["ln_sel2"]) / 2
        f["ln_bg_sh"] = (f["ln_bg"] + f["ln_bg2"]) / 2
    else:
        for k in ("ln_hot2", "ln_bg2", "ln_sel2", "ln_sel_sh", "ln_bg_sh"):
            f[k] = float("nan")
    f["ln_selbg"] = f["ln_sel"] + f["ln_bg"]
    f["test1"] = bool(f["rec"].get("triggered_test1"))
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--osf", default=str(OSF_DEFECTO))
    a = ap.parse_args(argv)
    osf = pd.read_csv(a.osf)
    osf["t"] = pd.to_datetime(osf.timeUTC, format="%d/%m/%Y %H:%M", errors="coerce")
    o = osf[osf.Volc_Name.isin(MAP) & (osf.t >= T0) & (osf.t < T1) & (osf.Dayflag == 0)
            & (osf["class"] == 1) & (osf.VRP > 0)].copy()
    o["vol"] = o.Volc_Name.map(MAP)
    ours = cargar_nuestros()
    out, txt = {"poblacion": {}, "controles": {}, "reparto": {}, "cenital": {}}, []

    filas, motivos = pares(o, ours)
    neg, _ = pares(o, ours, shift_h=6)
    out["poblacion"] = {"filas_osf": int(len(o)), "pares_crater": len(filas), "descartes_pareo": dict(motivos),
                        "por_sensor": dict(Counter(f["b"] for f in filas))}
    # ---- controles
    c5 = len(neg) / max(1, len(filas))
    c2 = [C.control_un_pixel(f["rec"]) for f in filas]
    c2 = [x for x in c2 if x is not None]
    c3 = []
    for f in filas:
        if f["b"] == "VIIRS375" and f["rec"].get("f5_core_vrp_mw") is not None:
            rec = f5_core_vrp_mw(f["rec"], C.INNER[f["vol"]])
            c3.append(rec is not None and abs(rec - f["rec"]["f5_core_vrp_mw"]) <= 0.001)
    c4, c4_por = [], defaultdict(list)
    for f in filas:
        r = f["rec"]
        if f["kernel"] or f["fuente"] == "test1_roi" or not r.get("t_bg_k"):
            continue
        lring = C.planck(r["t_bg_k"], f["b"])
        for p in r.get("anomaly_pixels") or []:
            if (p.get("vrp_mw") or 0) > 0 and p.get("bt_k"):
                limp = C.planck(p["bt_k"], f["b"]) - p["vrp_mw"] * 1e6 / C.KA[f["b"]]
                c4.append(abs(limp - lring) / lring <= 0.01)
                c4_por[f"{f['b']}|{'test1' if r.get('triggered_test1') else 'sin_test1'}"].append(c4[-1])
    out["controles"] = {
        "C2_cumulo_un_pixel": {"n": len(c2), "acierto": round(float(np.mean(c2)), 4) if c2 else None, "pasa": bool(c2) and np.mean(c2) >= 0.98},
        "C3_f5_replica": {"n": len(c3), "acierto": round(float(np.mean(c3)), 4) if c3 else None, "pasa": bool(c3) and np.mean(c3) >= 0.99},
        "C4_fondo_implicito_vs_anillo": {"n_pixeles": len(c4), "acierto": round(float(np.mean(c4)), 4) if c4 else None,
                                         "pasa": bool(c4) and np.mean(c4) >= 0.90,
                                         "por_sensor_y_test1": {k: [int(sum(v)), len(v), round(float(np.mean(v)), 4)]
                                                                for k, v in sorted(c4_por.items())}},
        "C5_pareo_corrido_6h": {"pares_corridos": len(neg), "pares_reales": len(filas), "fraccion": round(c5, 4), "pasa": c5 <= 0.02},
    }
    # ---- factores
    sep, excl = [], Counter()
    for f in filas:
        m = factores(f)
        if m:
            excl[(f["b"], m)] += 1
        else:
            sep.append(f)
    # C7 (enmienda declarada en el README): el producto de los factores es D / (kA Npix (Lh_M - Lbk_M)), no D / V_M.
    # La identidad de codigo se compara contra ese denominador; la diferencia con V_M es la consistencia del propio
    # OSF (VRP publicado contra kA por la suma de radiancias), que se informa aparte.
    c7 = max(abs(math.exp(f["ln_rec"] + f["ln_n"] + f["ln_hot"] + f["ln_bg"])
                 / (f["D"] * 1e6 / (C.KA[f["b"]] * f["Npix"] * (f["Lh_M"] - f["Lbk_M"]))) - 1) for f in sep)
    c7_osf = max(abs(f["V_M"] * 1e6 / (C.KA[f["b"]] * f["Npix"] * (f["Lh_M"] - f["Lbk_M"])) - 1) for f in sep)
    out["controles"]["C7_identidad"] = {"max_error_relativo_codigo": c7, "pasa": c7 < 1e-9,
                                        "max_error_relativo_osf_vrp_vs_kA_suma": c7_osf}
    out["poblacion"]["excluidas_de_la_separacion"] = {f"{b}|{m}": n for (b, m), n in excl.items()}
    out["poblacion"]["separadas"] = dict(Counter(f["b"] for f in sep))

    def estrato(nombre, sub):
        rep = C.reparto_con_ic(sub, FACT)
        if rep:
            rep["Npix_mediana"] = float(np.median([f["Npix"] for f in sub]))
            rep["n_pos_mediana"] = float(np.median([f["n_pos"] for f in sub]))
            rep["dT_fondo_mediana_K"] = float(np.nanmedian([_t(f["Lbg"], f["b"]) - _t(f["Lbk_M"], f["b"]) for f in sub]))
            rep["F_sel_gm_por_banda_z"] = {bz: [round(C.gm([math.exp(f["ln_sel"]) for f in sub if f["banda_z"] == bz]), 3),
                                                sum(1 for f in sub if f["banda_z"] == bz)]
                                           for bz in ("0-20", "20-35", "35-50", "50-90")}
            rep["angulo_en_sel"] = C.frac_angulo_con_ic(sub, "ln_sel")
            rep["angulo_en_bg"] = C.frac_angulo_con_ic(sub, "ln_bg")
            rep["angulo_en_sel_x_bg"] = C.frac_angulo_con_ic(sub, "ln_selbg")
            # arreglo (a): reparto con las dos bisagras y Shapley, sobre las pasadas donde la alternativa existe
            alt = [f for f in sub if np.isfinite(f["ln_bg2"])]
            r2 = C.reparto_con_ic(alt, ["ln_rec", "ln_sel", "ln_bg", "ln_sel2", "ln_bg2", "ln_sel_sh", "ln_bg_sh"])
            if r2:
                rep["bisagras"] = {"n_pasadas": r2["n_pasadas"], "excluidas_sin_bisagra_alternativa": len(sub) - len(alt),
                                   "frac_rec": r2["frac_ln_rec"],
                                   "bisagra_nuestra": {"frac_sel": r2["frac_ln_sel"], "frac_bg": r2["frac_ln_bg"],
                                                       "F_sel": r2["ln_sel"], "F_bg": r2["ln_bg"]},
                                   "bisagra_mirova": {"frac_sel": r2["frac_ln_sel2"], "frac_bg": r2["frac_ln_bg2"],
                                                      "F_sel": r2["ln_sel2"], "F_bg": r2["ln_bg2"]},
                                   "shapley": {"frac_sel": r2["frac_ln_sel_sh"], "frac_bg": r2["frac_ln_bg_sh"],
                                               "F_sel": r2["ln_sel_sh"], "F_bg": r2["ln_bg_sh"]}}
            # arreglo (c): si el angulo fuera remuestreo, el Npix de MIROVA creceria hacia el borde
            rep["por_banda_z"] = {bz: {"n": len(s), "Npix_mediana": float(np.median([f["Npix"] for f in s])),
                                       "n_pos_mediana": float(np.median([f["n_pos"] for f in s])),
                                       "F_n": round(C.gm([math.exp(f["ln_n"]) for f in s]), 3),
                                       "F_hot": round(C.gm([math.exp(f["ln_hot"]) for f in s]), 3),
                                       "F_bg": round(C.gm([math.exp(f["ln_bg"]) for f in s]), 3),
                                       "R": round(C.gm([f["R"] for f in s]), 3)}
                                  for bz in ("0-20", "20-35", "35-50", "50-90")
                                  for s in [[f for f in sub if f["banda_z"] == bz]] if s}
            rep["test1_dispara"] = [sum(f["test1"] for f in sub), len(sub)]
            out["reparto"][nombre] = rep

    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        sb = [f for f in sep if f["b"] == b]
        estrato(b, sb)
        for v in C.VOLS:
            sv = [f for f in sb if f["vol"] == v]
            if len(sv) >= 10:
                estrato(f"{b}|{v}", sv)
        ef = C.efecto_cenital(sb, "ln_sel")
        efn = C.efecto_cenital(sb, "ln_n")
        aporte = [ef.get(f["banda_z"], (None,))[0] for f in sb]
        aporte = [x for x in aporte if x is not None]
        mlr = np.mean([math.log(f["R"]) for f in sb]) if sb else float("nan")
        out["cenital"][b] = {"efecto_ln_sel_por_banda": {k: [None if v[0] is None else round(v[0], 4), v[1]] for k, v in ef.items()},
                             "efecto_ln_n_por_banda": {k: [None if v[0] is None else round(v[0], 4), v[1]] for k, v in efn.items()},
                             "n_por_banda": dict(Counter(f["banda_z"] for f in sb)),
                             "frac_del_deficit_por_angulo": round(float(np.mean(aporte) / mlr), 4) if aporte and mlr else None,
                             "n_con_efecto": len(aporte), "n": len(sb)}
    # fondo de MIROVA vs nuestro anillo en kelvin y por tipo de volcan (con o sin kernel local)
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        for k, nom in ((True, "con_kernel"), (False, "sin_kernel")):
            sub = [f for f in sep if f["b"] == b and f["kernel"] == k]
            if len(sub) >= 10:
                estrato(f"{b}|{nom}", sub)
    for f in sep:
        f.pop("rec", None)
    pd.DataFrame(sep).to_csv(AQUI / "a_osf_exacto_pares.csv", index=False)
    (AQUI / "a_osf_exacto_salida.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=_js), encoding="utf-8")
    txt.append(json.dumps(out["poblacion"], ensure_ascii=False))
    txt.append(json.dumps(out["controles"], ensure_ascii=False, default=_js))
    txt.append("estrato | n pasadas/noches | R mediana | R gm [IC] | F_rec | F_sel | F_bg | F_n | F_hot | "
               "frac rec/sel/bg [IC] | Npix med | n+ med | dT fondo K | F_sel por banda z")
    for k, r in out["reparto"].items():
        txt.append(f"{k} | {r['n_pasadas']}/{r['n_noches']} | {r['R_mediana']:.3f} | {r['R_gm']} | {r['ln_rec']} | {r['ln_sel']} | "
                   f"{r['ln_bg']} | {r['ln_n']} | {r['ln_hot']} | {r['frac_ln_rec']}/{r['frac_ln_sel']}/{r['frac_ln_bg']} | "
                   f"{r['Npix_mediana']} | {r['n_pos_mediana']} | {r['dT_fondo_mediana_K']:.2f} | {r['F_sel_gm_por_banda_z']} | "
                   f"angulo dentro de sel: {r['angulo_en_sel']}")
    txt.append(json.dumps(out["cenital"], ensure_ascii=False))
    (AQUI / "a_osf_exacto_salida.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print("\n".join(txt))


def _js(o):
    return o.item() if hasattr(o, "item") else str(o)


def _t(L, b):
    lam = C.LAM[b]
    return C.C2 / (lam * math.log(C.C1 / (lam ** 5 * L) + 1)) if L > 0 else float("nan")


if __name__ == "__main__":
    main()
