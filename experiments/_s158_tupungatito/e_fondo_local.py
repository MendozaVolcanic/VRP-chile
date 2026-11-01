# -*- coding: utf-8 -*-
"""S158. ¿Cuánto más frío que el anillo de 5 a 25 km está el entorno inmediato del cráter de Tupungatito, y
cuánto del déficit de magnitud de K se explica por restar el fondo equivocado?

POR QUÉ: con el detector anterior (C0), en las pasadas en que ganaba el Test 1 integrado
(final_hotspot_source = test1_roi) el VRP de cada píxel se restaba contra la mediana de la radiancia MIR de un
anillo de 1 a 3 km alrededor del cráter (pipeline/test1_integrated.py, compute_test1_mir: roi_km 3,
inner_ring_km 1; select_test1_effective_lbg cae al «local» en Tupungatito). K apagó ese camino (D30) y hoy todo
píxel se resta contra la mediana del anillo de 5 a 25 km (t_bg_k), que en un volcán glaciar de 5.600 m es valle
más tibio que la cumbre. El fondo de 1 a 3 km no se guardó en el record, pero se puede despejar: con la misma
temperatura de brillo, el mismo coeficiente y la misma área nadir, el único T de fondo que reproduce el VRP
guardado del píxel es ese fondo local. Se comprueba que todos los píxeles de un mismo record den el mismo T.

QUÉ MIDE:
  1. dT_local = t_bg (anillo 5-25 km) - T_local (anillo 1-3 km), por pasada C0 test1_roi, por banda de cenit y
     por estación (el anillo frío es nieve: invierno contra verano).
  2. Sobre las pasadas de d_pasadas_salida.json (K, misma pasada que una alerta de la tabla a <= 7 km):
       G_local = suma de nuestros píxeles K con fondo = t_bg - dT_local, sobre M.
     dT_local de la misma pasada si C0 la tiene en test1_roi; si no, la mediana de su banda de cenit.
  3. Reparto multiplicativo por pasada: R = F_rec · (G_local/G)^-1 ... se informa como
       R = F_rec x G,   G = G_local / alza_fondo,   y lo que falta tras fondo y área: resto = G_local · f_area.

Uso: python -I e_fondo_local.py --c0 <Tupungatito.json del commit padre de #883>
"""
import argparse
import io
import json
import math
import os
import statistics as st
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline.constants import C1_PLANCK, C2_PLANCK  # noqa: E402
from pipeline import process_viirs as pv  # noqa: E402

LAM, KW, AREA = pv.I04_LAMBDA, pv.WOOSTER_COEFF, pv.NADIR_PIXEL_AREA_M2
SENSORES = ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21")
INNER = 7.0


def L(t):
    return C1_PLANCK / (LAM ** 5 * (math.exp(C2_PLANCK / (LAM * t)) - 1.0))


def T_de_L(l):
    return C2_PLANCK / (LAM * math.log(1.0 + C1_PLANCK / (LAM ** 5 * l)))


def vrp(bt, tb):
    return KW * AREA * max(L(bt) - L(tb), 0.0) / 1e6


def banda(z):
    return "<30" if z < 30 else ("30-50" if z < 50 else ">=50")


def estacion(dt):
    m = int(dt[5:7])
    return "invierno (may-sep)" if 5 <= m <= 9 else "verano (nov-mar)" if m in (11, 12, 1, 2, 3) else "transición (abr, oct)"


def med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--c0", required=True)
    a = ap.parse_args()
    c0 = [r for r in json.load(open(a.c0, encoding="utf-8"))["records"]
          if not (r.get("regimen") or {}).get("codigo_sha") and r["sensor"] in SENSORES]

    # 1. fondo local despejado de los records C0 test1_roi
    locales = {}
    n_rec = n_coherentes = 0
    for r in c0:
        if r.get("final_hotspot_source") != "test1_roi" or not r.get("t_bg_k"):
            continue
        pix = [p for p in (r.get("anomaly_pixels") or []) if p.get("dist_km") is not None and p["dist_km"] <= INNER
               and p["vrp_mw"] > 0]
        if not pix:
            continue
        n_rec += 1
        ts = [T_de_L(L(p["bt_k"]) - p["vrp_mw"] * 1e6 / (KW * AREA)) for p in pix
              if L(p["bt_k"]) - p["vrp_mw"] * 1e6 / (KW * AREA) > 0]
        if not ts:
            continue
        coherente = (max(ts) - min(ts)) < 0.3   # el VRP guardado viene redondeado: tolerancia de 0,3 K
        n_coherentes += coherente
        locales[(r["sensor"], r["datetime_utc"])] = {
            "T_local": st.median(ts), "dT_local": r["t_bg_k"] - st.median(ts), "rango_T": max(ts) - min(ts),
            "coherente": coherente, "cenital": r.get("sensor_zenith_deg"), "n_pix": len(pix), "dt": r["datetime_utc"]}

    coh = [v for v in locales.values() if v["coherente"]]
    L_ = []
    P = L_.append
    P(f"C0 VIIRS 375 test1_roi con píxeles a <= {INNER} km: {n_rec}; con T_local despejable: {len(locales)}; "
      f"coherentes (todos sus píxeles dan el mismo T a 0,3 K): {n_coherentes}")
    P(f"dT_local = t_bg(5-25 km) - T_local(1-3 km), pasadas coherentes: mediana {med([v['dT_local'] for v in coh]):.2f} K, "
      f"p10 {sorted(v['dT_local'] for v in coh)[len(coh) // 10]:.2f}, p90 {sorted(v['dT_local'] for v in coh)[9 * len(coh) // 10]:.2f}; "
      f"T_local < t_bg en {sum(1 for v in coh if v['dT_local'] > 0)} de {len(coh)}")
    por_banda = {}
    for zb in ("<30", "30-50", ">=50"):
        g = [v["dT_local"] for v in coh if v["cenital"] is not None and banda(v["cenital"]) == zb]
        por_banda[zb] = med(g)
        P(f"  cenital {zb:6s} n {len(g):3d}  dT_local mediana {med(g):.2f} K" if g else f"  cenital {zb} sin pasadas")
    for es in ("verano (nov-mar)", "transición (abr, oct)", "invierno (may-sep)"):
        g = [v["dT_local"] for v in coh if estacion(v["dt"]) == es]
        P(f"  {es:22s} n {len(g):3d}  dT_local mediana {med(g):.2f} K" if g else f"  {es} sin pasadas")

    # 2. aplicar a las pasadas K pareadas con la tabla
    d = json.load(open(AQUI / "d_pasadas_salida.json", encoding="utf-8"))
    crudos = {(r["sensor"], r["datetime_utc"]): r
              for r in json.load(open(ROOT / "data" / "mirova_equivalent" / "Tupungatito.json", encoding="utf-8"))["records"]}
    filas = []
    for f in d["pasadas"]:
        r = crudos[(f["sensor"], f["pasada"])]
        pix = [p for p in (r.get("anomaly_pixels") or []) if p.get("dist_km") is not None and p["dist_km"] <= INNER]
        misma = locales.get((f["sensor"], f["pasada"]))
        if misma and misma["coherente"]:
            dT, origen = misma["dT_local"], "misma pasada"
        else:
            dT, origen = por_banda[f["banda"]], "mediana de la banda"
        S_loc = sum(vrp(p["bt_k"], f["t_bg"] - dT) for p in pix)

        def dT_que_cierra(objetivo):
            # cuántos K bajo la mediana del anillo tendría que estar el fondo para que la suma de NUESTROS
            # píxeles (con el recorte a cero del procesador) llegue a `objetivo`; None si ni a 60 K alcanza
            if sum(vrp(p["bt_k"], f["t_bg"] - 60.0) for p in pix) < objetivo:
                return None
            lo, hi = -30.0, 60.0
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                if sum(vrp(p["bt_k"], f["t_bg"] - mid) for p in pix) >= objetivo:
                    hi = mid
                else:
                    lo = mid
            return hi
        dT_c = dT_que_cierra(f["M"])
        dT_c_area = dT_que_cierra(f["M"] / f["f_area"]) if f["f_area"] else None
        G_loc = S_loc / f["M"]
        filas.append({"pasada": f["pasada"], "banda": f["banda"], "lado": f["lado"], "R": f["R"], "F_rec": f["F_rec"],
                      "G": f["G"], "dT_local": dT, "origen_dT": origen, "G_local": G_loc,
                      "alza_fondo": G_loc / f["G"] if f["G"] else None, "f_area": f["f_area"],
                      "G_local_area": G_loc * f["f_area"] if f["f_area"] else None, "R_C0": f["R_C0"],
                      "dT_cierra": dT_c, "dT_cierra_con_area": dT_c_area})
    P("")
    P(f"pasadas K pareadas con la tabla (d_pasadas): {len(filas)}; dT_local de la misma pasada en "
      f"{sum(1 for x in filas if x['origen_dT'] == 'misma pasada')}")
    P("estrato              n   R     G     alza_fondo G_local f_area G_local·f_area  R_C0")
    out_e = {}
    grupos = [("todas", filas)] + [(f"cenital {zb}", [x for x in filas if x["banda"] == zb]) for zb in ("<30", "30-50", ">=50")] \
        + [(f"lado {l_}", [x for x in filas if x["lado"] == l_]) for l_ in ("este", "oeste")] \
        + [("sólo dT de la misma pasada", [x for x in filas if x["origen_dT"] == "misma pasada"])]
    for nom, g in grupos:
        e = {k: med([x[k] for x in g]) for k in ("R", "G", "alza_fondo", "G_local", "f_area", "G_local_area", "R_C0",
                                                  "dT_local", "dT_cierra", "dT_cierra_con_area")}
        e["n"] = len(g)
        out_e[nom] = e
        f2 = lambda v: f"{v:5.2f}" if v is not None else "  -  "  # noqa: E731
        P(f"{nom:20s} {len(g):3d} {f2(e['R'])} {f2(e['G'])} {f2(e['alza_fondo'])}      {f2(e['G_local'])}   "
          f"{f2(e['f_area'])}  {f2(e['G_local_area'])}           {f2(e['R_C0'])}")
    P("")
    P("fondo que cierra cada pasada (K bajo la mediana del anillo, mediana por pasada), contra el fondo local de C0:")
    P("estrato                     n   dT_local  dT_cierra  dT_cierra_con_area  (sin solución)")
    for nom, g in grupos:
        e = out_e[nom]
        f1 = lambda v: f"{v:6.1f}" if v is not None else "   -  "  # noqa: E731
        P(f"{nom:26s} {e['n']:3d}  {f1(e['dT_local'])}    {f1(e['dT_cierra'])}     {f1(e['dT_cierra_con_area'])}"
          f"              ({sum(1 for x in g if x['dT_cierra'] is None)})")
    # reparto en log (mediana de cada término por pasada, no cociente de medianas)
    lr = [math.log(x["R"]) for x in filas]
    lf = [math.log(x["alza_fondo"]) for x in filas if x["alza_fondo"]]
    la = [math.log(x["f_area"]) for x in filas]
    lres = [math.log(x["G_local_area"]) for x in filas if x["G_local_area"]]
    P("")
    P(f"reparto del déficit en logaritmo natural (medianas por pasada): -ln R {-st.median(lr):.2f} = "
      f"fondo {st.median(lf):.2f} + área {st.median(la):.2f} + resto {-st.median(lres):.2f} "
      f"(los términos son medianas por separado: no suman exacto)")
    txt = "\n".join(L_)
    print(txt)
    (AQUI / "e_fondo_local_salida.txt").write_text(txt + "\n", encoding="utf-8")
    (AQUI / "e_fondo_local_salida.json").write_text(json.dumps(
        {"locales": {f"{k[0]} {k[1]}": v for k, v in locales.items()}, "dT_por_banda": por_banda,
         "estratos": out_e, "pasadas": filas}, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
