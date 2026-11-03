# -*- coding: utf-8 -*-
"""v02 (verificador S173, PCC VIIRS 750): razon K / MIROVA por pasada con un pareo PROPIO, desde el JSON de produccion
de origin/main (repo/data/mirova_equivalent/PuyehueCordonCaulle.json, sha256 c5598df6..., igual a origin/main
f20495d3 normalizado a LF) y los CSV del scraper del mismo commit. Verifica la afirmacion A1 (0,571 / 0,117, Spearman
-0,508, 53 alertas) y A3 (la pendiente sale de ceros) por otro camino que s01: pareo hecho a mano sobre las filas del
scraper, Spearman de scipy, barajado con numpy, y estratos que s01 no imprime (plataforma, media ademas de mediana,
sin la pasada del 2026-10-10, dejar una noche fuera, publicadas sin ceros).

Vara: scraper (CONS + OCR) indexado por banco_paridad.indexar_referencia con regla SN (D-9) y avisos A119; magnitud
nuestra = `disp` del predicado del tablero (node) sobre el record (pc.vrp_mw en VIIRS 750), y pc.vrp_mw crudo al lado.
P1: control de escala (x2 dobla la mediana); control de que el pareo ve algo: pareo contra la referencia corrida +1 dia
    debe caer a ~0. P2: barajado del cenit 200 veces, semilla 173; dejar una noche fuera.
Uso: python -B v02_razon_k_pareo_propio.py  (escribe v02_salida.txt, v02_pares.csv)
"""
from __future__ import annotations

import collections
import csv
import io
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
AUD = AQUI.parent / "pcc750"
REPO = AUD / "repo"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402

VOL = "PuyehueCordonCaulle"
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
    s = f"{nombre:30s} z<{corte:.0f} {q(lo)} | z>={corte:.0f} {q(hi)}"
    s += (f" | Spearman {rho:+.3f} barajado [{bj[0]:+.3f}, {bj[1]:+.3f}] {'FUERA' if fuera else 'dentro'}"
          if rho is not None else " | Spearman - (n<4 o constante)")
    pr(s)
    return rho


def main():
    bp.VOLS = [VOL]
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    ventana = ("2026-04-01", "2026-11-02")
    pr("== CONFIG: ventana", ventana, "| volcan", VOL, coords[VOL], "| inner", inner[VOL])
    ref = bp.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
    por_vb, _, _, _ = bp.indexar_referencia(ref, coords, ventana, regla_minimas="SN")
    lista = por_vb.get((VOL, "VIIRS750"), [])
    por_vb_o, _, _, _ = bp.indexar_referencia(ref, coords, ventana, regla_minimas="original")
    lista_o = por_vb_o.get((VOL, "VIIRS750"), [])
    recs = [r for r in bp.cargar_nuestros(coords, inner, ventana) if r["b"] == "VIIRS750"]
    pr("filas de referencia VIIRS750 PCC nocturnas: SN", len(lista), "| original", len(lista_o),
       "| records K VIIRS750 nocturnos:", len(recs), "| sin sensor_zenith_deg:", sum(1 for r in recs if r["z"] is None))
    # alertas SN: una por pasada (fundir CONS y OCR a +-120 s), VRP de la CONS si la hay
    pasadas = []
    vistos = []
    for dt, f in lista:
        if not (bp.es_alerta(f["tipo"]) and (f.get("vrp_mw") or 0) > 0):
            continue
        if any(abs((dt - d0).total_seconds()) <= bp.TOL_S for d0 in vistos):
            continue
        fs = [g for g in bp.parear(lista, dt) if bp.es_alerta(g["tipo"]) and (g.get("vrp_mw") or 0) > 0]
        c = [g for g in fs if g["source"] == "CONS"]
        fm = (c or fs)[0]
        vistos.append(dt)
        pasadas.append((dt, fm))
    # alertas que la regla SN descarta (<= 0,05 MW): estrato aparte
    chicas = [(dt, f) for dt, f in lista_o if bp.es_alerta(f["tipo"]) and 0 < (f.get("vrp_mw") or 0) <= 0.05]
    pr("alertas MIROVA (SN, lectura A) por pasada:", len(pasadas), "| descartadas por SN (<= 0,05 MW):", len(chicas),
       "| fuente:", dict(collections.Counter(f["source"] for _, f in pasadas)),
       "| noches:", len({dt.strftime('%Y-%m-%d') for dt, _ in pasadas}))
    pares = []
    for dt, fm in pasadas:
        cand = [r for r in recs if abs((r["dt"] - dt).total_seconds()) <= bp.TOL_S]
        r0 = min(cand, key=lambda r: abs((r["dt"] - dt).total_seconds())) if cand else None
        pares.append({"dt_M": dt.strftime("%Y-%m-%d %H:%M"), "noche": dt.strftime("%Y-%m-%d"), "vM": fm["vrp_mw"],
                      "srcM": fm["source"], "distM": fm.get("dist_km"), "tiene_record": r0 is not None,
                      "n_cand": len(cand), "sensor": (r0 or {}).get("sensor"), "z": (r0 or {}).get("z"),
                      "pub": (r0 or {}).get("pub"), "disp": (r0 or {}).get("disp"), "pc_vrp": (r0 or {}).get("pc_vrp"),
                      "dc": (r0 or {}).get("dc"), "pc_dist": (r0 or {}).get("pc_dist")})
    pr("\n== CONTROLES")
    pr("alertas sin record K a +-120 s:", sum(1 for p in pares if not p["tiene_record"]), "| con mas de un candidato:",
       sum(1 for p in pares if p["n_cand"] > 1), "| records pareados sin cenit:",
       sum(1 for p in pares if p["tiene_record"] and p["z"] is None))
    sh = sum(1 for r in recs if r["pub"] == 1 and any(bp.es_alerta(g["tipo"]) for g in bp.parear(lista, r["dt"] + timedelta(days=1))))
    di = sum(1 for r in recs if r["pub"] == 1 and any(bp.es_alerta(g["tipo"]) for g in bp.parear(lista, r["dt"])))
    pr("P2 pareo: records publicados con alerta a la misma hora", di, "| con la referencia corrida +1 dia", sh)
    dl = sum(1 for p in pares if p["pub"] == 1 and p["disp"] and p["pc_vrp"] is not None and abs(p["disp"] - p["pc_vrp"]) > 1e-6)
    pr("control de lectura: disp del tablero != pc.vrp_mw en publicados:", dl)
    R = [p for p in pares if p["z"] is not None]
    pr("plataformas:", dict(collections.Counter(p["sensor"] for p in R)))
    pr("n z<30:", sum(p["z"] < 30 for p in R), "| n z>=30:", sum(p["z"] >= 30 for p in R),
       "| publica: z<30", sum(1 for p in R if p["z"] < 30 and p["pub"] == 1), "z>=30", sum(1 for p in R if p["z"] >= 30 and p["pub"] == 1))
    pr("ceros por causa: sin record", sum(1 for p in R if not p["tiene_record"]), "| record sin cumulo (pc None)",
       sum(1 for p in R if p["tiene_record"] and p["pc_vrp"] is None), "| cumulo pero no publica (far u otro)",
       sum(1 for p in R if p["pc_vrp"] is not None and p["pub"] != 1), "| publica",
       sum(1 for p in R if p["pub"] == 1))
    pr("  no publica con cumulo: ", [(p["dt_M"], p["dc"], p["pc_vrp"], p["pc_dist"]) for p in R if p["pc_vrp"] is not None and p["pub"] != 1])

    def rz(p):
        return ((p["disp"] or 0) / p["vM"]) if p["pub"] == 1 else 0.0

    pr("\n== RAZON K / MIROVA POR PASADA (A1)")
    linea("tablero con ceros", [(p["z"], rz(p)) for p in R])
    linea("control x2", [(p["z"], 2 * rz(p)) for p in R])
    P = [p for p in R if p["pub"] == 1]
    linea("tablero publicadas (sin ceros)", [(p["z"], rz(p)) for p in P])
    linea("pc.vrp_mw crudo con ceros", [(p["z"], max(p["pc_vrp"] or 0, 0) / p["vM"]) for p in R])
    pr("-- cero = 1 si no publica (A3: ¿la pendiente es de ceros?)")
    linea("indicadora no publica", [(p["z"], 0.0 if p["pub"] == 1 else 1.0) for p in R])
    pr("-- sin la pasada del 2026-10-10 05:54 (perdida aceptada #865/#881)")
    R2 = [p for p in R if p["dt_M"] != "2026-10-10 05:54"]
    linea("con ceros, sin 10-10", [(p["z"], rz(p)) for p in R2])
    pr("-- solo CONS (A119: antes del 2026-06-13 decide la tabla)")
    linea("CONS con ceros", [(p["z"], rz(p)) for p in R if p["srcM"] == "CONS"])
    linea("CONS publicadas", [(p["z"], rz(p)) for p in P if p["srcM"] == "CONS"])
    pr("-- por plataforma, con ceros")
    for s in sorted({p["sensor"] for p in R}):
        linea(f"{s} con ceros", [(p["z"], rz(p)) for p in R if p["sensor"] == s])
    pr("-- por tramo: antes y despues de #535 (2026-08-28) y de la adopcion de K (2026-10-18), con ceros")
    linea("hasta 2026-08-28", [(p["z"], rz(p)) for p in R if p["noche"] <= "2026-08-28"])
    linea("desde 2026-08-29", [(p["z"], rz(p)) for p in R if p["noche"] > "2026-08-28"])
    pr("-- ventana del auto-audit (2026-09-03 a 2026-11-02)")
    A = [p for p in R if p["noche"] >= "2026-09-03"]
    linea("auto-audit con ceros", [(p["z"], rz(p)) for p in A])
    linea("auto-audit publicadas", [(p["z"], rz(p)) for p in A if p["pub"] == 1])
    pr("-- corte alternativo 40 grados")
    linea("tablero con ceros", [(p["z"], rz(p)) for p in R], corte=40.0)
    linea("tablero publicadas", [(p["z"], rz(p)) for p in P], corte=40.0)
    pr("-- dejar una noche fuera (con ceros y publicadas): Spearman [min, max], replicas FUERA")
    for nombre, S in (("con ceros", R), ("publicadas", P)):
        noches = sorted({p["noche"] for p in S})
        sps, fuera = [], 0
        for n in noches:
            T = [p for p in S if p["noche"] != n]
            rho, bj, fu = sp_baraja([p["z"] for p in T], [rz(p) for p in T])
            sps.append(rho)
            fuera += bool(fu)
        pr(f"  {nombre:12s} Spearman [{min(sps):+.3f}, {max(sps):+.3f}] FUERA {fuera}/{len(noches)}")
    pr("-- MIROVA misma: ¿su VRP cae con el cenit? (si cayera, la razon no lo veria)")
    linea("vM MIROVA", [(p["z"], p["vM"]) for p in R])
    pr("-- alertas descartadas por SN (<= 0,05 MW): estrato SE, informado aparte")
    for dt, f in chicas:
        cand = [r for r in recs if abs((r["dt"] - dt).total_seconds()) <= bp.TOL_S]
        pr("  ", dt.strftime("%Y-%m-%d %H:%M"), f["source"], f["vrp_mw"], "| K:", [(r["sensor"], r["z"], r["pub"], r["disp"]) for r in cand])
    with open(AQUI / "v02_pares.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(pares[0].keys()))
        w.writeheader()
        w.writerows(pares)
    (AQUI / "v02_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
