# -*- coding: utf-8 -*-
"""Lee el jsonl del probe y aplica el criterio sellado en PREREGISTRO.md.

Las dos preguntas del instrumento:
1. Si el primer pase estuviera roto en los objetivos, lo veria? Si: cada etapa (finito, Test 2, Test 3, compuerta) se
   evalua por pixel con la replica que el probe exigio identica a la funcion original, y los contrafactuales salen de la
   funcion original (F1 a F3) o de la misma replica (F4).
2. Si el instrumento estuviera muerto, se veria distinto? Si: los controles C1 a C3 tienen que pasar las cuatro etapas
   (control positivo) y los 7 records del probe tienen que reproducir los publicados. Un granulo que no reproduce es
   SIN DATO.
Uso: python analizar.py <probe_chillan.jsonl> > analizar_salida.txt
"""
import io
import json
import math
import os
import statistics
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from pipeline import process_modis as PM  # noqa: E402

INNER = 5.0
C2_SUM, C2_SCE = 5.0, 10.0
MIROVA = {"T1": (2.18, 2.24), "T2": (1.72, 2.24), "E1": (0.13, 0.0), "E2": (7.09, 2.83), "C1": (5.18, 2.24),
          "C2": (12.97, 2.24), "C3": (12.39, 1.41)}
K_MODIS = 18.9  # VRP_MW = 18.9 * dL (W m-2 sr-1 um-1), A_pix nadir fijo (CLAUDE.md del proyecto, reglas cientificas)


def rel(a, b):
    if a is None or b is None:
        return None
    if a == b:
        return 0.0
    return abs(a - b) / max(abs(a), abs(b), 1e-12)


def margen(p):
    if p.get("thr_dnti") is None or p.get("dnti") is None or p.get("deti") is None:
        return -math.inf
    return min(p["dnti"] - p["thr_dnti"], p["deti"] - p["thr_deti"])


def etapa(p, t_bg):
    if p.get("btmir") is None or p.get("dnti") is None or p.get("deti") is None or not p.get("en_roi"):
        return "a) no finito o fuera del ROI"
    if not p["pasa2"]:
        return "b) Test 2 (dNTI)"
    if not p["pasa3"]:
        return "c) Test 3 (dETI)"
    if not p["pasa_compuerta"]:
        return "d) compuerta 3 K"
    return "pasa las cuatro"


def main():
    filas = [json.loads(x) for x in open(sys.argv[1], encoding="utf-8")]
    por = {r["tag"]: r for r in filas}
    ctrl = [por[t]["P"] for t in ("C1", "C2", "C3") if t in por and "P" in por[t]]
    sd_ctrl = (statistics.median([c["sd_dnti"] for c in ctrl]), statistics.median([c["sd_deti"] for c in ctrl]))
    print(f"sigma de control (mediana C1-C3): sd_dnti={sd_ctrl[0]:.6f} sd_deti={sd_ctrl[1]:.6f} (n={len(ctrl)})")
    print()
    for tag in ("T1", "T2", "E1", "E2", "C1", "C2", "C3"):
        r = por.get(tag)
        print("=" * 100)
        if r is None or "error" in r:
            print(tag, "SIN DATO", (r or {}).get("error"))
            continue
        P, B = r["P"], r.get("B21", {})
        pub = r.get("publicado") or {}
        rec = P.get("rec") or {}
        print(f"{tag} {r['granulo']} version {r.get('version')} archivo {r.get('archivo')}  MIROVA {MIROVA[tag][0]} MW a {MIROVA[tag][1]} km")
        # control de instrumento
        reprod = {
            "replica_fp_identica": P.get("replica_identica"),
            "replica_sp_identica": P.get("sp_replica_identica"),
            "n_fp == pub": P.get("n_fp") == pub.get("diag_n_first_pass_pixels"),
            "n_fp_inner == pub summit": P.get("n_fp_inner") == pub.get("diag_n_first_pass_summit"),
            "rec 2p == pub": rec.get("diag_n_second_pass_recapture") == pub.get("diag_n_second_pass_recapture"),
            "t_bg rel": rel(rec.get("t_bg_k"), pub.get("t_bg_k")),
            "mu_dnti rel": rel(rec.get("diag_mu_dnti"), pub.get("diag_mu_dnti")),
            "sd_dnti rel": rel(rec.get("diag_sd_dnti"), pub.get("diag_sd_dnti")),
            "pc pub": pub.get("pc"), "pc probe": rec.get("pc"),
        }
        ok = (all(reprod[k] for k in ("replica_fp_identica", "n_fp == pub", "n_fp_inner == pub summit", "rec 2p == pub"))
              and all((reprod[k] or 0) <= 1e-3 for k in ("t_bg rel", "mu_dnti rel", "sd_dnti rel")))
        print("CONTROL instrumento:", json.dumps(reprod, default=str), "->", "REPRODUCE" if ok else "NO REPRODUCE (SIN DATO)")
        print(f"cenit pub {pub.get('sensor_zenith_deg')}  t_bg {P['t_bg']}  sigma_bg_anillo(pub) {pub.get('diag_sigma_bg_k')}  "
              f"mu/sd dNTI {P['mu_dnti']}/{P['sd_dnti']}  mu/sd dETI {P['mu_deti']}/{P['sd_deti']}  n_bg {P['n_bg']}")
        print(f"umbrales: {P['thr']}  rama estadistica: {P['stat']}  C1: {P['c1']}")
        print(f"pixel del crater (i,j,d): {P['pixel_crater']}  factor de area sec (no usado en VRP) {P['area_factor_crater']}  "
              f"lineas {P['n_lineas']}")
        print(f"conteos dentro del inner: produccion {P['n_fp_inner']} (escena {P['n_fp']}); F1 sin compuerta {P['n_F1_inner']}; "
              f"F2 conectiva min {P['n_F2_inner']}; F3 las dos {P['n_F3_inner']}; B21 {B.get('n_fp_inner')}; "
              f"segundo pase nuevos dentro {P.get('sp_n_nuevos_inner')} (escena {P.get('sp_n_nuevos')})")
        pix = P["pixeles"]
        en4 = [p for p in pix if p["d_km"] <= 4.0]
        sat = [p for p in en4 if p["dn21"] > 32767 or p["dn22"] > 32767]
        nofin = [p for p in en4 if p["btmir"] is None]
        print(f"saturacion a <=4 km: {len(en4)} pixeles, DN>32767 en 21 o 22: {len(sat)}, BT MIR no finita: {len(nofin)}; "
              f"BT22 max {max((p['bt22'] or 0) for p in en4):.2f} K, BT21 max {max((p['bt21'] or 0) for p in en4):.2f} K")
        # F4
        dentro = [p for p in pix if p["d_km"] <= INNER and p.get("thr_dnti") is not None]
        n_f4 = 0
        for p in dentro:
            c2 = C2_SUM if p["cumbre"] else C2_SCE
            c1 = P["c1"]["dnti_sum"] if p["cumbre"] else P["c1"]["dnti_sce"]
            t2 = max(c1, P["mu_dnti"] + c2 * sd_ctrl[0])
            t3 = max(c1, P["mu_deti"] + c2 * sd_ctrl[1])
            n_f4 += (p["dnti"] > t2) and (p["deti"] > t3) and p["pasa_compuerta"] and p["en_roi"]
        print(f"F4 sigma de control: {n_f4} dentro del inner")
        # mejor pixel
        mejor = max(dentro, key=margen) if dentro else None
        if mejor:
            m = mejor
            print(f"MEJOR pixel dentro del inner: i={m['i']} j={m['j']} d={m['d_km']} km cumbre={m['cumbre']}  ETAPA: {etapa(m, P['t_bg'])}")
            print(f"   DN 21/22/31 {m['dn21']}/{m['dn22']}/{m['dn31']}  BT21 {m['bt21']} BT22 {m['bt22']} BTMIR {m['btmir']} BT31 {m['bt31']}")
            print(f"   NTI {m['nti']} media8 {m['mean_nti8']} dNTI {m['dnti']} (umbral {m['thr_dnti']})  dETI {m['deti']} (umbral {m['thr_deti']})")
            print(f"   compuerta: BT MIR - t_bg = {m['btmir'] - P['t_bg']:.2f} K (pide > 3)")
            falta = max(m["thr_dnti"] - m["dnti"], m["thr_deti"] - m["deti"])
            lam = PM.BAND22_LAMBDA if m["L22"] is not None else PM.BAND21_LAMBDA
            lmir = m["L22"] if m["L22"] is not None else m["L21"]
            if falta > 0:
                nti_n = m["nti"] + falta
                M = m["L31"] * (1 + nti_n) / (1 - nti_n)
                bt_n = float(PM.radiance_to_bt(M, lam))
                lbg = float(PM.bt_to_radiance(P["t_bg"], lam))
                print(f"   LE FALTA dNTI/dETI {falta:.5f}: L_MIR {lmir:.5f} -> {M:.5f} W/m2/sr/um (BT MIR {m['btmir']} -> {bt_n:.2f} K), "
                      f"VRP equivalente del pixel {K_MODIS * (lmir - lbg):.3f} -> {K_MODIS * (M - lbg):.3f} MW (L_bg a t_bg {lbg:.5f})")
            else:
                lbg = float(PM.bt_to_radiance(P["t_bg"], lam))
                print(f"   pasa los dos tests con margen {-falta:.5f}; VRP equivalente del pixel {K_MODIS * (lmir - lbg):.3f} MW")
        print(f"   contexto: BT31 crater {[p['bt31'] for p in pix if [p['i'], p['j']] == P['pixel_crater'][:2]]} vs mediana anillo {P['bt31_anillo_mediana']}; "
              f"BT MIR anillo {P['btmir_anillo_mediana']}")
        print("   pixeles <= 5 km (d, cumbre, BTMIR, BT31, dNTI/umbral, dETI/umbral, pasa2, pasa3, compuerta, hot, F1, F2, F3, sp_dNTI/umbral, sp_out):")
        for p in sorted(dentro, key=margen, reverse=True)[:12]:
            print(f"     {p['d_km']:5.2f} {int(p['cumbre'])} {p['btmir']:7.2f} {p['bt31']:7.2f} {p['dnti']:+.5f}/{p['thr_dnti']:.5f} "
                  f"{p['deti']:+.5f}/{p['thr_deti']:.5f} {int(p['pasa2'])}{int(p['pasa3'])}{int(p['pasa_compuerta'])} "
                  f"{int(p['hot'])}{int(p['F1'])}{int(p['F2'])}{int(p['F3'])}  "
                  f"{(p.get('sp_dnti') or 0):+.5f}/{(p.get('sp_thr_dnti') or 0):.5f} {int(bool(p.get('sp_out')))} 3x3={int(p['vecindad_3x3'])}")
        print(f"   segundo pase: mu/sd dNTI {P.get('sp_mu_dnti')}/{P.get('sp_sd_dnti')} mu/sd dETI {P.get('sp_mu_deti')}/{P.get('sp_sd_deti')} "
              f"n_bg {P.get('sp_n_bg')} kw {P.get('sp_kw')}")


if __name__ == "__main__":
    main()
