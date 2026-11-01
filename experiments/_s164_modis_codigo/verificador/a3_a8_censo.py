# -*- coding: utf-8 -*-
"""Verificador S164, A3 y A8 contra el censo MOD-D completo (D:/vrp-trabajo/temporales/s162_modd/censo, solo lectura).

A8: las 5 fixtures (tests/datos_s164_modis/grilla_*.npz) son byte a byte los arreglos del censo, y esperado.json
    reproduce los campos del censo y el VRP con la regla de MATLAB recalculado AQUI con el blob f273a47a
    (insumos/delaunay_perturbado_f273a47a.py), no con la via.
A3 (extendido): sobre TODAS las pasadas ok del censo (no solo 5), la via (pipeline.mirova_v750_codigo con
    FAMILIAS["MODIS"]) da los mismos pixeles alertados y los mismos n_abs/n_p1/n_p2 que port.fisica del censo; y, en
    las que alertan, el VRP de la via contra el VRP con hueco + f273a47a (que rellena fuera de la envolvente con el
    vecino mas cercano, mientras la via deja NaN). Se cuenta en cuantas alertas el fondo de la via es NaN.

Uso: python a3_a8_censo.py [--max-fill N]   (desde la raiz del worktree)
"""
import argparse
import glob
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(AQUI / "insumos"))
import delaunay_perturbado_f273a47a as DP  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402

CENSO = Path("D:/vrp-trabajo/temporales/s162_modd/censo")
DATOS = RAIZ / "tests/datos_s164_modis"
MODIS = MV.FAMILIAS["MODIS"]
COEF = 1.89e7 * 1.0 / 1e6


def hueco(m, mask):
    enm = m.copy()
    enm[mask] = np.nan
    n = int(mask.sum())
    k = 3 if n <= 4 else (5 if n <= 30 else 7)
    enm[binary_dilation(np.isnan(enm), structure=np.ones((k, k), bool))] = np.nan
    return enm


def cargar_censo():
    recs = {}
    n_total = n_ok = 0
    for f in glob.glob(str(CENSO / "run_*" / "*" / "ab_*.jsonl")):
        for l in open(f, encoding="utf-8"):
            r = json.loads(l)
            if r.get("tipo") != "record":
                continue
            n_total += 1
            if r.get("estado") != "ok" or not (r.get("port") or {}).get("fisica"):
                continue
            n_ok += 1
            recs[r["id"]] = (r, Path(f).parent / f"grilla_{r['id']:03d}.npz")
    return recs, n_total, n_ok


def igual_nan(a, b):
    return a.shape == b.shape and a.dtype == b.dtype and np.array_equal(a, b, equal_nan=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-fill", type=int, default=400)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.time()
    recs, n_total, n_ok = cargar_censo()
    print(f"censo: {n_total} records, {n_ok} ok con port.fisica, ids unicos {len(recs)}")

    # ---------------- A8
    esp = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))
    print("\n== A8 fixtures vs censo ==")
    for p in esp["pasadas"]:
        i = p["id"]
        r, gp = recs[i]
        z_fix = np.load(DATOS / f"grilla_{i}.npz")
        z_cen = np.load(gp)
        mismo = igual_nan(z_fix["mir"], z_cen["mir"]) and igual_nan(z_fix["tir"], z_cen["tir"])
        pf = r["port"]["fisica"]
        campos = {"vol": r["vol"] == p["vol"], "dt": r["dt"] == p["dt"], "lab": r["lab"] == p["lab"],
                  "inner": r["inner"] == p["inner"], "dayflag": r["dayflag"] == p["dayflag"],
                  "sunglint": r["sunglint"] == p["sunglint"], "npix": pf["npix"] == p["censo_npix"],
                  "pixeles": [q[:3] for q in pf["pixeles"]] == p["censo_pixeles"],
                  "vrp_port": pf["vrp_mw"] == p["censo_vrp_port"],
                  "n": (pf["n_abs"], pf["n_p1"], pf["n_p2"]) == (p["censo_n_abs"], p["censo_n_p1"], p["censo_n_p2"])}
        mir = z_cen["mir"].astype(float)
        mask = np.zeros(mir.shape, bool)
        for q in pf["pixeles"]:
            mask[q[0], q[1]] = True
        vr = None
        if mask.any():
            fondo = DP.rellenar(hueco(mir, mask), "xy_fila_col")[0]
            vr = (float(np.nansum(mir[mask])) - float(np.nansum(fondo[mask]))) * COEF
        ok_vr = (vr is None and p["vrp_regla_matlab"] is None) or (vr is not None and p["vrp_regla_matlab"] is not None
                                                                    and abs(vr - p["vrp_regla_matlab"]) < 1e-12)
        print(f"  id {i} {r['vol']} {r['dt']} dtype {z_fix['mir'].dtype} arreglos_iguales={mismo} "
              f"campos_ok={all(campos.values())} {'' if all(campos.values()) else campos} "
              f"vrp_regla recalculado={vr} esperado={p['vrp_regla_matlab']} ok={ok_vr}")

    # ---------------- A3 extendido: deteccion sobre todo el censo
    print("\n== A3 extendido: deteccion de la via vs port.fisica en todo el censo ==")
    g_cache = {}
    dif_pix, dif_n, con_alerta, sin_grilla, n_proc = [], [], [], [], 0
    box = MV.caja_roi("def", n=51, lado_sensible=MODIS["lado_sensible"], lado_anillo=MODIS["lado_anillo"],
                      paso_m=MODIS["paso_m"])
    for i, (r, gp) in sorted(recs.items()):
        if not gp.exists():
            sin_grilla.append(i)
            continue
        z = np.load(gp)
        mir, tir = z["mir"].astype(float), z["tir"].astype(float)
        mask, d = MV.detectar_mirova(mir, tir, box, r["dayflag"], r["sunglint"], devolver_diag=True,
                                     lam_mir=MODIS["lam_mir"], lam_tir=MODIS["lam_tir"])
        n_proc += 1
        pf = r["port"]["fisica"]
        pix_via = sorted([int(f), int(k)] for f, k in zip(*np.nonzero(mask)))
        pix_port = sorted([q[0], q[1]] for q in pf["pixeles"])
        if pix_via != pix_port:
            dif_pix.append((i, r["vol"], r["dt"], pix_via, pix_port))
        n_via = (d.get("n_abs") or 0, d.get("n_p1") or 0, d.get("n_p2") or 0)
        n_port = (pf["n_abs"] or 0, pf["n_p1"] or 0, pf["n_p2"] or 0)
        if n_via != n_port:
            dif_n.append((i, r["vol"], r["dt"], n_via, n_port))
        if mask.any():
            con_alerta.append((i, r, mir, mask, pf))
    print(f"  procesadas {n_proc}; sin grilla npz {len(sin_grilla)}; con alerta (via) {len(con_alerta)}")
    print(f"  pixeles distintos via vs port: {len(dif_pix)}")
    for x in dif_pix[:10]:
        print("    ", x)
    print(f"  (n_abs, n_p1, n_p2) distintos: {len(dif_n)}")
    for x in dif_n[:10]:
        print("    ", x)
    npix_hist = {}
    for _, _, _, mask, _ in con_alerta:
        npix_hist[int(mask.sum())] = npix_hist.get(int(mask.sum()), 0) + 1
    print(f"  histograma npix (via): {dict(sorted(npix_hist.items()))}")

    # ---------------- A3: VRP de la via vs regla f273a47a (independiente) en las que alertan
    print(f"\n== A3: VRP via (_fillmissing2_lineal) vs hueco + f273a47a.rellenar, hasta {a.max_fill} pasadas ==")
    iguales = distintos = nan_via = 0
    detalle = []
    por_vol = {}
    for i, r, mir, mask, pf in con_alerta[: a.max_fill]:
        v = MV.vrp_mirova(mir, mask, coef=MODIS["coef"])
        enm = hueco(mir, mask)
        f_dp = DP.rellenar(enm, "xy_fila_col")[0]
        f_via = MV._fillmissing2_lineal(enm)
        vr = (float(np.nansum(mir[mask])) - float(np.nansum(f_dp[mask]))) * COEF
        n_nan_via = int(np.isnan(f_via[mask]).sum())
        nan_via += n_nan_via > 0
        igual = abs(v["VRP_MW"] - vr) <= 1e-9 * max(1.0, abs(vr))
        iguales += igual
        distintos += not igual
        por_vol.setdefault(r["vol"], [0, 0])
        por_vol[r["vol"]][0 if igual else 1] += 1
        if not igual or n_nan_via:
            detalle.append((i, r["vol"], r["dt"], int(mask.sum()), round(v["VRP_MW"], 6), round(vr, 6), n_nan_via,
                            round(pf["vrp_mw"], 6) if pf.get("vrp_mw") is not None else None))
    print(f"  iguales {iguales}, distintos {distintos}, alertas con fondo NaN en la via {nan_via}")
    print(f"  por volcan (iguales, distintos): {por_vol}")
    for x in detalle[:30]:
        print("    id, vol, dt, npix, vrp_via, vrp_f273a47a, n_nan_via, vrp_port:", x)
    print(f"\ntiempo {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
