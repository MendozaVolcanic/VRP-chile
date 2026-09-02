# -*- coding: utf-8 -*-
"""S131 auditoria MAGNITUD - items 3 y 4: ley de area por angulo (VIIRS) y cruce con datos.

POR QUE. S131 mostro que el ratio nuestro/MIROVA cae con el angulo cenital en VIIRS y
que MIROVA es plano. La hipotesis es que MIROVA remuestrea a celdas de area nominal
(Coppola 2014 s2.2) y nosotros integramos con area nominal FIJA sobre el pixel real,
mas grande en oblicuo. Para la magnitud, "regrid + area nominal" equivale a "area real
sin regrid" (Sum k*A0*dL sobre A/A0 celdas = k*A*dL). Este script aplica esa
correccion a `pc.vrp_mw` READ-ONLY y mira si el gradiente se aplana.

LA LEY DE AREA. El ATBD de geolocalizacion VIIRS (423-ATBD-002) NO da tabla ni formula
de area vs angulo: da (a) los extremos de la Tabla 2.2-1 (HSI nadir / end of scan),
(b) los angulos de cambio de zona de agregacion (3:1 -> 2:1 en 31.589 deg de scan,
2:1 -> 1:1 en 44.680 deg, fin de scan 56.063 deg) y (c) la Figura 3.3-1, que es un
grafico no transcribible. Por eso se construyen DOS brazos, y se dice cual es cual:

  B  "modelo geometrico anclado": esfera R=6371 km, h=829 km; angulo de scan desde el
     cenital del record por sin(ts) = R*sin(tz)/(R+h); crecimiento along-track =
     rango inclinado / h; along-scan crudo = along-track / cos(tz); agregacion 3/2/1
     por zona de scan. f = g_track * g_scan_crudo * agg/3. NO es el ATBD: es un modelo
     que reproduce sus dos extremos (1.00 en nadir; 4.48 vs 4.38 al borde, +2 %) y sus
     saltos. Se declara como modelo.
  C  "lineal en (1-cos)": f = 1 + (4.38-1) * (1-cos tz)/(1-cos 70.3 deg). Brazo
     extremo pedido en el encargo; no tiene los saltos.
  A  sin correccion (lo publicado hoy).

DEFINICIONES (A90): identicas a `experiments/_s131_remuestreo/factor_requerido.py` —
un par por (volcan, fecha, bucket), maximo de cada lado, `pc.vrp_mw` (A10), loader
CONS union OCR (A11), solo nocturnas, ventana 2026, 11 Tier A, angulo =
|sensor_zenith_deg| del record (es el del pixel mas cercano al hotspot final, S122).
La correccion se aplica con el angulo del record, no por pixel: el cluster es
compacto y el angulo varia poco dentro de el. Con n<15 no se afirma nada.
"""
import io
import json
import math
import os
import statistics as st
import sys
from collections import defaultdict

if __name__ == "__main__":   # al importarlo desde 03 no re-envolver stdout
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import bucket, cargar_mirova, ic95  # noqa: E402

OUT = os.path.join(HERE, "02_correccion_area_por_angulo.json")
VOLS = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima",
        "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "Tupungatito", "Villarrica"]
BINS = ["0-15", "15-25", "25-35", "35-50", "50+"]
MIN_N = 15
R_KM, H_KM = 6371.0, 829.0
SCAN_3TO2, SCAN_2TO1, SCAN_END = 31.589, 44.680, 56.063
AREA_BORDE = 4.38          # Tabla 2.2-1 ATBD, I4: (0.80*0.789)/(0.371*0.388)
BANDA = (0.7, 1.4)


def bin_de(sz):
    a = abs(sz)
    return "0-15" if a < 15 else "15-25" if a < 25 else "25-35" if a < 35 \
        else "35-50" if a < 50 else "50+"


def scan_desde_cenital(tz_deg):
    s = R_KM * math.sin(math.radians(tz_deg)) / (R_KM + H_KM)
    return math.degrees(math.asin(min(1.0, s)))


def f_modelo(tz_deg):
    """Brazo B. Modelo geometrico anclado al ATBD (ver docstring)."""
    tz = min(abs(tz_deg), 70.3)
    ts = scan_desde_cenital(tz)
    gamma = math.radians(tz - ts)
    slant = math.sqrt(R_KM ** 2 + (R_KM + H_KM) ** 2
                      - 2 * R_KM * (R_KM + H_KM) * math.cos(gamma))
    g_track = slant / H_KM
    g_scan_raw = g_track / math.cos(math.radians(tz))
    agg = 3 if ts < SCAN_3TO2 else 2 if ts < SCAN_2TO1 else 1
    return g_track * g_scan_raw * agg / 3.0


def f_lineal(tz_deg):
    """Brazo C. Lineal en (1-cos), de 1.0 en nadir a AREA_BORDE en 70.3 deg."""
    tz = min(abs(tz_deg), 70.3)
    return 1.0 + (AREA_BORDE - 1.0) * (1 - math.cos(math.radians(tz))) \
        / (1 - math.cos(math.radians(70.3)))


def tabla_modelo():
    print("LEY DE AREA — brazo B (modelo) y C (lineal), cenital en tierra:")
    print(f"  {'cenital':>8s} {'scan':>7s} {'zona':>5s} {'f_B':>6s} {'f_C':>6s}")
    filas = []
    for tz in (0, 10, 20, 30, 36.2, 36.4, 40, 45, 50, 52.5, 52.7, 55, 60, 65, 69.6, 70.3):
        ts = scan_desde_cenital(tz)
        zona = "3:1" if ts < SCAN_3TO2 else "2:1" if ts < SCAN_2TO1 else "1:1"
        fb, fc = f_modelo(tz), f_lineal(tz)
        filas.append({"cenital_deg": tz, "scan_deg": round(ts, 2), "zona": zona,
                      "f_modelo": round(fb, 3), "f_lineal": round(fc, 3)})
        print(f"  {tz:8.1f} {ts:7.2f} {zona:>5s} {fb:6.3f} {fc:6.3f}")
    return filas


def med(xs):
    return round(st.median(xs), 3)


def main():
    filas_ley = tabla_modelo()
    mir, _ = cargar_mirova(("2026-01-01", "2026-12-31"))
    pares = []   # (vol, bk, zen, ours, mirova)
    for v in VOLS:
        p = os.path.join(ROOT, "data", "mirova_equivalent", v + ".json")
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            bk = bucket(r.get("sensor"))
            if bk is None:
                continue
            sol = r.get("solar_zenith_deg")
            if sol is not None and sol < 90:
                continue
            sen = r.get("sensor_zenith_deg")
            pcv = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
            if sen is None or pcv <= 0:
                continue
            m = (mir.get(v) or {}).get((r.get("datetime_utc", "")[:10], bk))
            if not m or m <= 0:
                continue
            pares.append((v, bk, abs(sen), pcv, m))
    # un par por (vol, fecha, bucket): maximo de cada lado ya lo garantiza el loader
    # del lado MIROVA; del lado nuestro se toma el maximo por (vol, fecha, bucket).
    mejor = {}
    for v in VOLS:
        p = os.path.join(ROOT, "data", "mirova_equivalent", v + ".json")
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            bk = bucket(r.get("sensor"))
            sol = r.get("solar_zenith_deg")
            if bk is None or (sol is not None and sol < 90):
                continue
            sen = r.get("sensor_zenith_deg")
            pcv = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
            if sen is None or pcv <= 0:
                continue
            k = (v, r.get("datetime_utc", "")[:10], bk)
            if pcv > mejor.get(k, (0, 0))[0]:
                mejor[k] = (pcv, abs(sen))
    pares = []
    for (v, fecha, bk), (pcv, sen) in mejor.items():
        m = (mir.get(v) or {}).get((fecha, bk))
        if m and m > 0:
            pares.append((v, bk, sen, pcv, m))

    brazos = {"A_sin": lambda z: 1.0, "B_modelo": f_modelo, "C_lineal": f_lineal}
    res = {"definicion": __doc__, "ley": filas_ley, "por_sensor": {}, "por_volcan": {}}
    for bk, nom in (("v375", "VIIRS375"), ("v750", "VIIRS750"), ("modis", "MODIS")):
        sub = [p for p in pares if p[1] == bk]
        if len(sub) < MIN_N:
            continue
        print(f"\n{nom}  n_pares={len(sub)}  (MODIS: solo brazo A; la ley es VIIRS)")
        usar = ("A_sin",) if bk == "modis" else tuple(brazos)
        print(f"  {'bin':7s} {'n':>5s} " + " ".join(f"{b:>10s}" for b in usar))
        out_b = {}
        for b in BINS:
            xs = [p for p in sub if bin_de(p[2]) == b]
            if len(xs) < MIN_N:
                continue
            fila = {"n": len(xs), "zen_mediano": med([p[2] for p in xs])}
            for br in usar:
                fila[br] = med([p[3] * brazos[br](p[2]) / p[4] for p in xs])
            out_b[b] = fila
            print(f"  {b:7s} {len(xs):5d} " + " ".join(f"{fila[br]:10.3f}" for br in usar))
        glob = {}
        for br in usar:
            rs = [p[3] * brazos[br](p[2]) / p[4] for p in sub]
            glob[br] = {"mediana": med(rs), "ic95": ic95(rs), "n": len(rs),
                        "n_sobre_2": sum(1 for x in rs if x > 2.0),
                        "pct_sobre_2": round(100 * sum(1 for x in rs if x > 2.0) / len(rs), 1),
                        "n_en_banda": sum(1 for x in rs if BANDA[0] <= x <= BANDA[1])}
            print(f"  global {br:9s} mediana={glob[br]['mediana']:.3f} IC95={glob[br]['ic95']} "
                  f">2.0: {glob[br]['n_sobre_2']}/{len(rs)} ({glob[br]['pct_sobre_2']}%)  "
                  f"en banda [0.7,1.4]: {glob[br]['n_en_banda']}")
        res["por_sensor"][bk] = {"bins": out_b, "global": glob}
        # por volcan (regla S126)
        print(f"  por volcan (n>=15): {'volcan':20s} {'n':>4s} " + " ".join(f"{b:>9s}" for b in usar))
        pv = {}
        for v in VOLS:
            xs = [p for p in sub if p[0] == v]
            if len(xs) < MIN_N:
                pv[v] = {"n": len(xs)}
                continue
            fila = {"n": len(xs), "zen_mediano": med([p[2] for p in xs])}
            for br in usar:
                rs = [p[3] * brazos[br](p[2]) / p[4] for p in xs]
                fila[br] = med(rs)
                fila[br + "_sobre_2"] = sum(1 for x in rs if x > 2.0)
            pv[v] = fila
            print(f"    {v:20s} {len(xs):4d} " + " ".join(
                f"{fila[br]:9.3f}" for br in usar)
                + "   en banda: " + " ".join(
                    f"{br}={'si' if BANDA[0] <= fila[br] <= BANDA[1] else 'NO'}" for br in usar))
        res["por_volcan"][bk] = pv
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
