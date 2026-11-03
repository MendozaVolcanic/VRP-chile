# -*- coding: utf-8 -*-
"""v03 (verificador S173, PCC VIIRS 750): por que el brazo S/C del auditor (oraculo S162) y la via de produccion con la
misma mascara dan VRP distinto en 27 de 27 pasadas con alerta (v01, control «S_vrp distinto: 27»). Hipotesis: el
oraculo usa _fillmissing2_lineal sin perturbar (scipy Delaunay, docstring del oraculo l. 196) y la via usa la
triangulacion perturbada al estilo MATLAB (mirova_v750_codigo.py, bloque «fillmissing2», S163). Se mide:
 (1) por pasada, VRP via (B1 sens) contra VRP oraculo (S) con la MISMA mascara, y el fondo de cada uno bajo los
     alertados; (2) la misma comparacion inyectando el fondo del oraculo en la via (monkeypatch local de
     MV._fillmissing2_lineal por OA._fillmissing2_lineal) para probar que esa es la unica diferencia;
 (3) la razon contra MIROVA por tramo de cenit de ambos fondos, mismo denominador que v01;
 (4) A2 por camino propio: BT del anillo 5-25 km (mediana) menos BT del fondo de la via bajo los alertados, y BT del
     alertado menos ese fondo, por tramo; mas Planck(t_bg del record K) contra la mediana del anillo en la grilla;
 (5) control positivo fino: minima inyeccion en la celda del crater que alerta con la caja «def» (para leer cuanto le
     falta al lacolito para pasar los umbrales conservadores);
 (6) A4: posicion del cumulo de K (centroid_dist_km desde el ancla) y n_pixels por tramo, desde v02_pares.csv.
Uso: python -B v03_fondo_via_vs_oraculo.py (escribe v03_salida.txt, v03_por_pasada.csv)
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
AUD = AQUI.parent / "pcc750"
REPO = AUD / "repo"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(AUD / "src" / "s162"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline import mirova_v750_codigo as MV  # noqa: E402
import oraculo_ablacion as OA  # noqa: E402

GRILLAS = Path("D:/vrp-trabajo/temporales/s159_n")
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def fl(x):
    try:
        v = float(x)
        return v if np.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def q(v):
    v = sorted(x for x in v if x is not None)
    if not v:
        return "sin datos"
    n = len(v)
    return f"med {np.median(v):.3f} [{v[n // 4]:.3f}, {v[(3 * n) // 4]:.3f}] media {np.mean(v):.3f} n={n}"


def sp_baraja(z, r, n=200, semilla=173):
    z = np.asarray(z, float)
    r = np.asarray(r, float)
    if len(z) < 4 or np.all(r == r[0]):
        return None, (None, None), False
    rho = spearmanr(z, r).statistic
    rng = np.random.RandomState(semilla)
    out = sorted(s for s in (spearmanr(rng.permutation(z), r).statistic for _ in range(n)) if np.isfinite(s))
    lo, hi = out[int(0.025 * len(out))], out[int(0.975 * len(out)) - 1]
    return rho, (lo, hi), (rho < lo or rho > hi)


def linea(nombre, pares, corte=30.0):
    lo = [b for a, b in pares if a < corte]
    hi = [b for a, b in pares if a >= corte]
    rho, bj, fuera = sp_baraja([a for a, _ in pares], [b for _, b in pares])
    s = f"{nombre:34s} z<{corte:.0f} {q(lo)} | z>={corte:.0f} {q(hi)}"
    s += (f" | Spearman {rho:+.3f} barajado [{bj[0]:+.3f}, {bj[1]:+.3f}] {'FUERA' if fuera else 'dentro'}"
          if rho is not None else " | Spearman -")
    pr(s)


def grilla_de(i):
    for run in ("run_39682867040", "run_39693661527", "run_39680724047"):
        c = sorted((GRILLAS / run).glob(f"*/grilla_{i:03d}.npz"))
        if c:
            return c[0]
    return None


def main():
    v01 = {int(x["id"]): x for x in csv.DictReader(open(AQUI / "v01_por_pasada.csv", encoding="utf-8"))}
    aud = {int(x["id"]): x for x in csv.DictReader(open(AUD / "s02_por_pasada.csv", encoding="utf-8"))}
    res = {}
    for f in sorted((AUD / "insumos" / "n").rglob("resultados_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok" or r["id"] not in res:
                res[r["id"]] = r
    g = MV.grilla_del_volcan("PuyehueCordonCaulle")
    n = g["n"]
    c = n // 2
    rr, kk = np.indices((n, n))
    dk = np.hypot(rr - c, kk - c) * 0.75
    box_sens = MV.caja_roi("sens", n=n)
    box_def = MV.caja_roi("def", n=n)
    celda = MV.celda_de(g, -40.525499, -72.146137)
    filas = []
    pr("== (1) y (2) VRP via contra VRP oraculo con la MISMA mascara (brazo sens / S), pasadas con alertados")
    pr("id   hora_utc           z   npix  vrp_via  vrp_orac  dif%   via_con_fondo_orac==orac  Lbk_via  Lbk_orac")
    for i in sorted(v01):
        x = v01[i]
        if not int(x["B1_sens_npix"] or 0):
            continue
        z = np.load(grilla_de(i))
        m13, m15 = np.asarray(z["m13"], float), np.asarray(z["m15"], float)
        r = res[i]
        mask = MV.detectar_mirova(m13, m15, box_sens, r["dayflag"], r["sunglint"])
        v_via = MV.vrp_mirova(m13, mask)
        v_or = OA.vrp(m13, mask, dict(OA.PIEZAS_MIROVA))
        # (2) via con el fondo del oraculo
        orig = MV._fillmissing2_lineal
        MV._fillmissing2_lineal = OA._fillmissing2_lineal
        try:
            v_mix = MV.vrp_mirova(m13, mask)
        finally:
            MV._fillmissing2_lineal = orig
        s_aud = fl(aud[i]["S_vrp"])
        same_mix = abs(v_mix["VRP_MW"] - v_or["VRP_MW"]) < 1e-9
        bt_bk_via = float(MV.radiancia_a_temperatura(np.array([v_via["L_bk"] / v_via["npix"]]), MV.LAMBDA_M13)[0])
        bt_hot = float(MV.radiancia_a_temperatura(np.array([v_via["L_hot"] / v_via["npix"]]), MV.LAMBDA_M13)[0])
        bt = MV.radiancia_a_temperatura(m13, MV.LAMBDA_M13)
        an = (dk >= 5) & (dk <= 25) & np.isfinite(bt)
        bt_an = float(np.median(bt[an]))
        k = (r["brazos"].get("K") or {}).get("record") or {}
        tbg_k = k.get("t_bg_k")
        fila = {"id": i, "hora_utc": x["hora_utc"], "z": fl(x["z"]), "vM": fl(x["vM"]), "npix": v_via["npix"],
                "vrp_via": v_via["VRP_MW"], "vrp_orac": v_or["VRP_MW"], "vrp_via_fondo_orac": v_mix["VRP_MW"],
                "S_vrp_auditor": s_aud, "Lbk_via": v_via["L_bk"], "Lbk_orac": v_or["L_bk"],
                "bt_bk_via": bt_bk_via, "bt_hot": bt_hot, "bt_anillo525": bt_an, "tbg_k_record": tbg_k,
                "L_tbg_k": (float(MV.temperatura_a_radiancia(np.float64(tbg_k), MV.LAMBDA_M13)) if tbg_k else None),
                "L_anillo525_med": float(np.median(m13[an]))}
        filas.append(fila)
        pr(f"{i:4d} {x['hora_utc']} {fila['z']:5.1f} {v_via['npix']:4d} {v_via['VRP_MW']:8.3f} {v_or['VRP_MW']:8.3f} "
           f"{100 * (v_via['VRP_MW'] - v_or['VRP_MW']) / v_or['VRP_MW'] if v_or['VRP_MW'] else float('nan'):6.1f} "
           f"{str(same_mix):>8s}  {v_via['L_bk']:8.4f} {v_or['L_bk']:8.4f}  S_aud {s_aud}")
    dif = [abs(f["vrp_via"] - f["vrp_orac"]) > 1e-6 for f in filas]
    pr("pasadas con alertados:", len(filas), "| via != oraculo:", sum(dif), "| via con fondo del oraculo == oraculo:",
       sum(1 for f in filas if abs(f["vrp_via_fondo_orac"] - f["vrp_orac"]) < 1e-9),
       "| oraculo == S del auditor:", sum(1 for f in filas if f["S_vrp_auditor"] is not None and abs(f["S_vrp_auditor"] - f["vrp_orac"]) < 1e-6))
    pr("via / oraculo (VRP), por tramo:")
    linea("  via/oraculo", [(f["z"], f["vrp_via"] / f["vrp_orac"]) for f in filas if f["vrp_orac"]])
    pr("\n== (3) razon contra MIROVA, misma mascara sens, los dos fondos (positivos; con ceros)")
    pos = [v01[i] for i in v01 if fl(v01[i]["vM"])]
    byid = {f["id"]: f for f in filas}
    linea("  via (Delaunay perturbado)", [(fl(x["z"]), (byid[int(x["id"])]["vrp_via"] if int(x["id"]) in byid else 0.0) / fl(x["vM"])) for x in pos])
    linea("  oraculo (scipy sin perturbar)", [(fl(x["z"]), (byid[int(x["id"])]["vrp_orac"] if int(x["id"]) in byid else 0.0) / fl(x["vM"])) for x in pos])
    linea("  via sin ceros", [(byid[int(x["id"])]["z"], byid[int(x["id"])]["vrp_via"] / fl(x["vM"])) for x in pos if int(x["id"]) in byid])
    linea("  oraculo sin ceros", [(byid[int(x["id"])]["z"], byid[int(x["id"])]["vrp_orac"] / fl(x["vM"])) for x in pos if int(x["id"]) in byid])
    pr("\n== (4) A2 por camino propio (positivos con alertados, fondo de la VIA)")
    P = [byid[int(x["id"])] for x in pos if int(x["id"]) in byid]
    linea("  BT anillo 5-25 - BT fondo via", [(f["z"], f["bt_anillo525"] - f["bt_bk_via"]) for f in P])
    linea("  BT alertado - BT fondo via", [(f["z"], f["bt_hot"] - f["bt_bk_via"]) for f in P])
    linea("  BT alertado - BT anillo", [(f["z"], f["bt_hot"] - f["bt_anillo525"]) for f in P])
    linea("  t_bg K record - BT anillo grilla", [(f["z"], f["tbg_k_record"] - f["bt_anillo525"]) for f in P if f["tbg_k_record"]])
    pr("  Planck(t_bg K record) / mediana L anillo grilla:", q([f["L_tbg_k"] / f["L_anillo525_med"] for f in P if f["L_tbg_k"]]))
    pr("\n== (5) control positivo fino: minima inyeccion (W m-2 sr-1 um-1) en la celda del crater que alerta con caja def")
    for i in [f["id"] for f in filas[:3]] + [f["id"] for f in filas[-3:]]:
        z = np.load(grilla_de(i))
        m13, m15 = np.asarray(z["m13"], float), np.asarray(z["m15"], float)
        r = res[i]
        base = float(m13[celda])
        hit = None
        for extra in (0.02, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3, 0.5):
            m = m13.copy()
            m[celda] += extra
            if MV.detectar_mirova(m, m15, box_def, r["dayflag"], r["sunglint"])[celda]:
                hit = extra
                break
        # y con la caja sens (zona sensible), la misma pregunta
        hit_s = None
        for extra in (0.0, 0.01, 0.02, 0.05, 0.08, 0.1, 0.15, 0.2):
            m = m13.copy()
            m[celda] += extra
            if MV.detectar_mirova(m, m15, box_sens, r["dayflag"], r["sunglint"])[celda]:
                hit_s = extra
                break
        pr(f"  id {i} {v01[i]['hora_utc']} z {fl(v01[i]['z']):.1f}: L crater {base:.4f}; alerta con def desde +{hit} | con sens desde +{hit_s}"
           f" (exceso real alertado-fondo via: {byid[i]['bt_hot'] - byid[i]['bt_bk_via']:.2f} K)")
    pr("\n== (6) A4: cumulo de K en las 53 alertas (v02_pares.csv): distancia del centroide al ancla y n (pc_dist, pc_n no esta en pares; se usa pc_dist)")
    pares = list(csv.DictReader(open(AQUI / "v02_pares.csv", encoding="utf-8")))
    linea("  pc_dist K (km) publicadas", [(fl(p["z"]), fl(p["pc_dist"])) for p in pares if p["pub"] == "1" and fl(p["pc_dist"]) is not None])
    linea("  distM MIROVA (km)", [(fl(p["z"]), fl(p["distM"])) for p in pares if fl(p["distM"]) is not None])
    with open(AQUI / "v03_por_pasada.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    (AQUI / "v03_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
