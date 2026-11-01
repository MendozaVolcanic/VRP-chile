# -*- coding: utf-8 -*-
"""Tabla resumen por gránulo del brazo P (produccion), calculada desde el jsonl del probe, para que ningun numero
del INFORME se transcriba a mano. Ademas compara el brazo P de dos corridas (nulo de ejecucion: deben ser iguales).

Las dos preguntas del instrumento: (1) los numeros salen del mismo jsonl cuyo control de identidad paso
(analizar.py); (2) el nulo de ejecucion entre runs tiene que dar 0 diferencias, y si diera distinto el resumen no vale.
Uso: python resumen.py <jsonl_run_a> <jsonl_run_b> > resumen_salida.txt
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
MIROVA = {"T1": 2.18, "T2": 1.72, "E1": 0.13, "E2": 7.09, "C1": 5.18, "C2": 12.97, "C3": 12.39}
INNER = 5.0


def margen(p):
    if p.get("thr_dnti") is None:
        return -1e9
    return min(p["dnti"] - p["thr_dnti"], p["deti"] - p["thr_deti"])


def main():
    a = {json.loads(x)["tag"]: json.loads(x) for x in open(sys.argv[1], encoding="utf-8")}
    b = {json.loads(x)["tag"]: json.loads(x) for x in open(sys.argv[2], encoding="utf-8")}
    difs = 0
    for t in a:
        for k in ("n_fp", "n_fp_inner", "n_F1_inner", "n_F2_inner", "n_F3_inner", "t_bg", "mu_dnti", "sd_dnti",
                  "mu_deti", "sd_deti", "thr", "pixeles"):
            difs += a[t]["P"].get(k) != b[t]["P"].get(k)
    print(f"NULO de ejecucion (brazo P, run A contra run B, 12 campos x {len(a)} granulos): {difs} diferencias")
    print()
    print("tag cenit  MIROVA  t_bg    sd_dNTI  umbral_dNTI(rama)  mejor_d  BTMIR-t_bg  MIR-TIR  BT31crat-anillo  "
          "z_dNTI  falta_dNTI  falta_BT_Test2  falta_BT_compuerta  falta_BT_dL>0")
    import os
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from pipeline import process_modis as PM
    for t in ("C3", "C1", "C2", "E2", "T2", "T1", "E1"):
        r = b[t]
        P = r["P"]
        dentro = [p for p in P["pixeles"] if p["d_km"] <= INNER and p.get("thr_dnti") is not None]
        m = max(dentro, key=margen)
        crat = [p for p in P["pixeles"] if [p["i"], p["j"]] == P["pixel_crater"][:2]][0]
        rama = "estad" if P["thr"]["dnti_sum"] > P["c1"]["dnti_sum"] else "C1"
        z = (m["dnti"] - P["mu_dnti"]) / P["sd_dnti"]
        falta = max(m["thr_dnti"] - m["dnti"], m["thr_deti"] - m["deti"])
        lam = PM.BAND22_LAMBDA if m["L22"] is not None else PM.BAND21_LAMBDA
        if falta > 0:
            nti_n = m["nti"] + falta
            M = m["L31"] * (1 + nti_n) / (1 - nti_n)
            fbt2 = float(PM.radiance_to_bt(M, lam)) - m["btmir"]
        else:
            fbt2 = 0.0
        fcomp = max(0.0, P["t_bg"] + 3.0 - m["btmir"])
        fdl = max(0.0, P["t_bg"] - m["btmir"])
        cen = (r.get("publicado") or {}).get("sensor_zenith_deg")
        print(f"{t}  {cen:5.2f}  {MIROVA[t]:6.2f}  {P['t_bg']:6.2f}  {P['sd_dnti']:.5f}  {P['thr']['dnti_sum']:.5f}({rama})  "
              f"{m['d_km']:5.2f}  {m['btmir'] - P['t_bg']:+7.2f}  {m['btmir'] - m['bt31']:+7.2f}  "
              f"{crat['bt31'] - P['bt31_anillo_mediana']:+7.2f}  {z:6.2f}  {max(falta, 0):.5f}  {fbt2:+6.2f}  "
              f"{fcomp:+6.2f}  {fdl:+6.2f}")
    # la compuerta depende del fondo del anillo: el mejor pixel de T1 y T2 contra el t_bg de C1
    tbg_c1 = b["C1"]["P"]["t_bg"]
    for t in ("T1", "T2"):
        P = b[t]["P"]
        dentro = [p for p in P["pixeles"] if p["d_km"] <= INNER and p.get("thr_dnti") is not None]
        m = max(dentro, key=margen)
        print(f"{t}: BT MIR del mejor pixel {m['btmir']:.2f} K; con su t_bg ({P['t_bg']:.2f}) queda {m['btmir'] - P['t_bg']:+.2f} K; "
              f"con el t_bg de C1 ({tbg_c1:.2f}) quedaria {m['btmir'] - tbg_c1:+.2f} K (la compuerta pide > +3)")


if __name__ == "__main__":
    main()
