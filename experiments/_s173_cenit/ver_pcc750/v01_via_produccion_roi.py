# -*- coding: utf-8 -*-
"""v01 (verificador S173, PCC VIIRS 750): la VIA «codigo MIROVA» DE PRODUCCION (repo/pipeline/mirova_v750_codigo.py de
origin/main f20495d3) corrida sobre las 72 grillas de PCC del censo N, con cada ROI que caja_roi() admite, pareada con
MIROVA por pasada y partida por cenit. Camino PROPIO: no usa el oraculo del auditor (src/s162/oraculo_ablacion.py) ni
sus brazos; usa las funciones que entrarian a produccion y el predicado del tablero ejecutado con node.

Pregunta que decide: ¿la via, con la ROI que grillas_mirova.yaml le da hoy a PCC («def», B0) y con las ROI candidatas
del prerregistro V750-B (B1 sens, B2 crater, B3 inner, B5 corona), queda cerca de 1 contra MIROVA? Y ¿que pasa si a esa
misma mascara se le pone el fondo de anillo de K (mediana de BT del anillo 5-25 km desde el centro, Planck, recorte a 0
por pixel, como process_viirs_mod.py l. 570 y l. 1070-1086)?

P1 (si estuviera roto, ¿lo veria?): control positivo de magnitud (+10 % de M13 en los alertados cambia el VRP);
    control positivo de deteccion (una fuente sintetica en la celda del crater tiene que alertar aun con la caja «def»,
    y la via tiene que verla; si no la ve, la via esta muerta para PCC, no muda). Control de identidad: la caja «def»
    de la via contra la del auditor (s02_por_pasada.csv, O_npix) pasada por pasada.
P2 (instrumento muerto): barajado del cenit (200, semilla 173) y pareo con la referencia corrida +1 dia.
Denominador: las 72 pasadas nocturnas de PCC con grilla (2026-04-07 a 2026-10-16); los positivos son las que tienen
alerta de MIROVA VIIRS 750 (SN, lectura A) a +-120 s.
Uso: python -B v01_via_produccion_roi.py  (escribe v01_salida.txt, v01_por_pasada.csv)
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
AUD = AQUI.parent / "pcc750"            # carpeta del auditor: solo lectura
REPO = AUD / "repo"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402

GRILLAS = Path("D:/vrp-trabajo/temporales/s159_n")
VOL = "PuyehueCordonCaulle"
VENT = (-40.525499, -72.146137)        # volcanoes.yaml PCC vent_lat/vent_lon (repo/volcanoes.yaml l. 26-27)
INNER = 20.0                           # inner_radius_km del tablero para PCC
ROIS = {"B0_def": "def", "B1_sens": "sens", "B2_crater": "crater", "B3_inner": "inner", "B5_corona": "corona"}
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
    out = []
    for _ in range(n):
        zz = rng.permutation(z)
        s = spearmanr(zz, r).statistic
        if np.isfinite(s):
            out.append(s)
    out.sort()
    lo, hi = out[int(0.025 * len(out))], out[int(0.975 * len(out)) - 1]
    return rho, (lo, hi), (rho < lo or rho > hi)


def linea(nombre, pares, corte=30.0):
    lo = [b for a, b in pares if a < corte]
    hi = [b for a, b in pares if a >= corte]
    rho, bj, fuera = sp_baraja([a for a, _ in pares], [b for _, b in pares])
    s = f"{nombre:26s} z<{corte:.0f} {q(lo)} | z>={corte:.0f} {q(hi)}"
    if rho is not None:
        s += f" | Spearman {rho:+.3f} barajado [{bj[0]:+.3f}, {bj[1]:+.3f}] {'FUERA' if fuera else 'dentro'}"
    else:
        s += " | Spearman - (n<4 o constante)"
    pr(s)
    return {"n_lo": len(lo), "n_hi": len(hi), "med_lo": (float(np.median(lo)) if lo else None),
            "med_hi": (float(np.median(hi)) if hi else None), "spearman": rho, "barajado": bj, "fuera": fuera}


def dist_centro_km(n, paso_m=750.0):
    c = n // 2
    r, k = np.indices((n, n))
    return np.hypot(r - c, k - c) * paso_m / 1000.0


def vrp_fondo_anillo_k(m13, mascara, dk, lam=MV.LAMBDA_M13, coef=MV.COEF_VRP_V750):
    """Fondo de K (process_viirs_mod.py l. 570 + detection_context.compute_bg_stats + l. 1070-1086): mediana de la BT
    M13 del anillo 5 a 25 km (sin excluir alertados, ENABLE_TEST1_K1_BG_EXCLUDE False), Planck a radiancia, exceso por
    pixel recortado a 0 y sumado. Devuelve (VRP_MW, t_bg)."""
    bt = MV.radiancia_a_temperatura(np.asarray(m13, float), lam)
    an = (dk >= 5.0) & (dk <= 25.0) & np.isfinite(bt)
    if an.sum() < 10 or not mascara.any():
        return (np.nan, np.nan)
    t_bg = float(np.median(bt[an]))
    L_bg = float(MV.temperatura_a_radiancia(np.float64(t_bg), lam))
    exc = np.maximum(np.asarray(m13, float)[mascara] - L_bg, 0.0)
    return float(np.nansum(exc) * coef), t_bg


def main():
    pr("== CONFIG")
    pr("repo:", (REPO / "COMMIT.txt").read_text().strip(), "| grillas:", GRILLAS)
    g = MV.grilla_del_volcan(VOL)
    pr("grilla via:", {k: g[k] for k in ("epsg", "ul_x", "ul_y", "n", "paso", "roi", "centro_lat", "centro_lon")})
    celda = MV.celda_de(g, *VENT)
    pos = MV.posicion_de(g, *VENT)
    pr("celda del crater (vent yaml) en la grilla:", celda, "| posicion fraccionaria:", tuple(round(p, 2) for p in pos),
       "| distancia crater-centro km:", round(float(np.hypot(pos[0] - (g['n'] // 2), pos[1] - (g['n'] // 2)) * 0.75), 2))
    dk = dist_centro_km(g["n"])
    # insumos del censo N (objetivos + resultados), solo lectura
    obj = {}
    for nom in ("objetivos_n.json", "objetivos_censo.json"):
        for o in json.loads((AUD / "insumos" / "n" / nom).read_text(encoding="utf-8")):
            obj[o["id"]] = o
    res = {}
    for f in sorted((AUD / "insumos" / "n").rglob("resultados_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok" or r["id"] not in res:
                res[r["id"]] = r
    ids = sorted(i for i, o in obj.items() if o["volcan"] == VOL and i in res and res[i].get("estado") == "ok"
                 and res[i].get("dayflag") == 0)
    pr("pasadas PCC nocturnas con resultado ok:", len(ids))
    # control de identidad contra la caja def del auditor
    aud = {int(x["id"]): x for x in csv.DictReader(open(AUD / "s02_por_pasada.csv", encoding="utf-8"))}
    # referencia MIROVA (vara del proyecto)
    bp.VOLS = [VOL]
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    assert inner[VOL] == INNER, inner[VOL]
    ventana = ("2026-04-01", "2026-10-31")
    ref = bp.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
    por_vb, _, _, _ = bp.indexar_referencia(ref, coords, ventana, regla_minimas="SN")
    lista = por_vb.get((VOL, "VIIRS750"), [])
    pr("filas de referencia VIIRS750 PCC (noche, SN) en", ventana, ":", len(lista))

    def mirova_de(dt):
        al = [f for f in bp.parear(lista, dt) if bp.es_alerta(f["tipo"]) and (f.get("vrp_mw") or 0) > 0]
        if not al:
            return None, None
        c = [f for f in al if f["source"] == "CONS"]
        f = (c or al)[0]
        return f["vrp_mw"], f

    filas, casos, idx = [], [], []
    ctrl = collections.Counter()
    for i in ids:
        o, r = obj[i], res[i]
        gp = None
        for run in ("run_39682867040", "run_39693661527", "run_39680724047"):
            c = sorted((GRILLAS / run).glob(f"*/grilla_{i:03d}.npz"))
            if c:
                gp = c[0]
                break
        if gp is None:
            ctrl["sin_grilla"] += 1
            continue
        z = np.load(gp)
        m13, m15 = np.asarray(z["m13"], float), np.asarray(z["m15"], float)
        dayflag, sg = r["dayflag"], r["sunglint"]
        k = (r["brazos"].get("K") or {}).get("record") or {}
        dt = datetime.strptime(o["hora_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        vM, fM = mirova_de(dt)
        vM1, _ = mirova_de(dt + timedelta(days=1))
        fila = {"id": i, "hora_utc": o["hora_utc"], "sensor": o["sensor"], "lab": o["lab"], "clase": o["clase"],
                "protegida": o.get("protegida"), "z": k.get("sensor_zenith_deg"),
                "z_centro": (r.get("geometria_centro") or {}).get("sensor_zenith"),
                "vM": vM, "srcM": (fM or {}).get("source"), "distM": (fM or {}).get("dist_km"), "vM_mas1d": vM1,
                "obj_mirova_vrp": o.get("mirova_vrp"), "k_pc_vrp": ((k.get("primary_cluster") or {}).get("vrp_mw")),
                "k_pub_prod": o.get("pub_prod"), "k_pc_vrp_obj": o.get("pc_vrp"), "sunglint": sg}
        if vM is not None and fl(o.get("mirova_vrp")) is not None and abs(vM - fl(o["mirova_vrp"])) > 1e-6:
            ctrl["vM_distinto_del_objetivo"] += 1
        if vM1:
            ctrl["par_corrido_1d"] += 1
        for nombre, tipo in ROIS.items():
            box = MV.caja_roi(tipo, n=g["n"], celda_crater=celda, inner_km=INNER)
            rec = MV.procesar_grilla(m13, m15, g, box, dayflag, sg, pos, INNER, o["sensor"])
            mask, _d = MV.detectar_mirova(m13, m15, box, dayflag, sg, devolver_diag=True)
            fila[f"{nombre}_npix"] = rec["n_anomalous_pixels"]
            fila[f"{nombre}_vrp"] = rec["vrp_mw"] if rec["n_anomalous_pixels"] else None
            fila[f"{nombre}_dc"] = rec["distance_class"]
            fila[f"{nombre}_dist"] = (rec.get("primary_cluster") or {}).get("centroid_dist_km")
            va, tb = vrp_fondo_anillo_k(m13, mask, dk)
            fila[f"{nombre}_vrp_anilloK"] = (va if rec["n_anomalous_pixels"] else None)
            fila[f"{nombre}_tbg_anilloK"] = tb
            # control positivo de magnitud
            if rec["n_anomalous_pixels"]:
                m13b = m13.copy()
                m13b[mask] *= 1.10
                v2 = MV.vrp_mirova(m13b, mask)["VRP_MW"]
                ctrl[f"pos_{nombre}_cambia" if abs(v2 - rec["vrp_mw"]) > 1e-9 else f"pos_{nombre}_NO"] += 1
            slim = {kk: rec.get(kk) for kk in bp.CAMPOS_JS if kk != "anomaly_pixels"}
            slim["anomaly_pixels"] = [{kk: p.get(kk) for kk in ("lat", "lon", "vrp_mw", "bt_k")}
                                      for p in (rec.get("anomaly_pixels") or [])]
            casos.append([slim, INNER])
            idx.append((len(filas), nombre))
        # identidad con la caja def del auditor (O)
        a = aud.get(i)
        if a is not None:
            same = int(a["O_npix"] or 0) == fila["B0_def_npix"] and (int(a["S_npix"] or 0) == fila["B1_sens_npix"])
            ctrl["identidad_def_sens_ok" if same else "identidad_def_sens_FALLA"] += 1
            if fila["B1_sens_npix"] and fl(a["S_vrp"]) is not None and abs(fl(a["S_vrp"]) - fila["B1_sens_vrp"]) > 1e-6:
                ctrl["S_vrp_distinto"] += 1
        # control positivo de deteccion: fuente sintetica en la celda del crater, caja def
        if i == ids[0] or i == ids[len(ids) // 2]:
            for extra, tag in ((0.5, "debil_+0.5"), (3.0, "fuerte_+3.0")):
                m13s = m13.copy()
                m13s[celda] += extra
                box0 = MV.caja_roi("def", n=g["n"])
                ms = MV.detectar_mirova(m13s, m15, box0, dayflag, sg)
                pr(f"control sintetico id {i} ({tag} W m-2 sr-1 um-1 en la celda del crater, caja def): alerta en el "
                   f"crater {bool(ms[celda])} | n alertados {int(ms.sum())} | sin inyectar {int(MV.detectar_mirova(m13, m15, box0, dayflag, sg).sum())}")
        filas.append(fila)
    pred = bp.correr_node(casos)
    for (fi, nombre), p in zip(idx, pred):
        filas[fi][f"{nombre}_disp"], filas[fi][f"{nombre}_pub"] = p[3], p[4]

    pr("\n== CONTROLES")
    pr("pasadas con grilla:", len(filas), "| sin grilla:", ctrl["sin_grilla"], "| ventana:",
       min(f["hora_utc"] for f in filas), "a", max(f["hora_utc"] for f in filas))
    pr("identidad caja def/sens de la via contra el oraculo del auditor (n alertados):",
       {k: v for k, v in ctrl.items() if k.startswith("identidad")}, "| S_vrp distinto:", ctrl["S_vrp_distinto"])
    pr("control positivo de magnitud (+10 % M13):", {k: v for k, v in ctrl.items() if k.startswith("pos_")})
    pr("VRP MIROVA distinto del objetivo del censo:", ctrl["vM_distinto_del_objetivo"],
       "| pares con la referencia corrida +1 dia:", ctrl["par_corrido_1d"], "de", len(filas))
    pr("pasadas con al menos un alertado, por ROI:", {n: sum(1 for f in filas if f[f"{n}_npix"]) for n in ROIS})
    pr("pasadas que el tablero PUBLICARIA, por ROI:", {n: sum(1 for f in filas if f[f"{n}_pub"] == 1) for n in ROIS})
    pr("distance_class por ROI (todas):", {n: dict(collections.Counter(f[f"{n}_dc"] for f in filas)) for n in ROIS})
    pos_ = [f for f in filas if f["vM"]]
    neg = [f for f in filas if not f["vM"] and f["lab"] == "neg_limpio"]
    pr("positivos (alerta MIROVA pareada):", len(pos_), "| negativos limpios:", len(neg),
       "| con cenit del record K:", sum(1 for f in filas if f["z"] is not None), "de", len(filas))
    pr("cenit de los positivos:", sorted(round(f["z"], 1) for f in pos_))
    pr("plataformas positivos:", dict(collections.Counter(f["sensor"] for f in pos_)))

    pr("\n== LO QUE DECIDE: razon via / MIROVA por pasada (positivos), con ceros (brazo sin VRP > 0 = 0)")
    resumen = {}
    for n in ROIS:
        resumen[n] = linea(f"{n} fondo codigo", [(f["z"], (fl(f[f"{n}_vrp"]) or 0) / f["vM"]) for f in pos_])
    pr("-- misma mascara, fondo de anillo de K (5-25 km, recorte por pixel)")
    for n in ROIS:
        resumen[n + "_anilloK"] = linea(f"{n} fondo anillo K",
                                        [(f["z"], (fl(f[f"{n}_vrp_anilloK"]) or 0) / f["vM"]) for f in pos_])
    pr("-- solo si el tablero PUBLICA (predicado node, inner 20 desde el crater), con ceros")
    for n in ROIS:
        resumen[n + "_pub"] = linea(f"{n} publicado", [(f["z"], ((f[f"{n}_disp"] or 0) / f["vM"]) if f[f"{n}_pub"] == 1 else 0.0)
                                                      for f in pos_])
    pr("-- sin ceros (solo pasadas con VRP > 0 del brazo)")
    for n in ROIS:
        resumen[n + "_sin0"] = linea(f"{n} sin ceros", [(f["z"], fl(f[f"{n}_vrp"]) / f["vM"]) for f in pos_ if fl(f[f"{n}_vrp"])])
    pr("-- K de produccion (record del runner N, pc.vrp_mw), con ceros, mismo denominador")
    resumen["K_pc"] = linea("K pc.vrp_mw", [(f["z"], (fl(f["k_pc_vrp"]) or 0) / f["vM"]) for f in pos_])
    pr("-- sin la pasada del 2026-10-10 05:54 (perdida aceptada, #865/#881)")
    pos2 = [f for f in pos_ if f["hora_utc"] != "2026-10-10 05:54"]
    for n in ("B0_def", "B1_sens", "B2_crater", "B3_inner"):
        linea(f"{n} sin 10-10", [(f["z"], (fl(f[f"{n}_vrp"]) or 0) / f["vM"]) for f in pos2])
    linea("K pc sin 10-10", [(f["z"], (fl(f["k_pc_vrp"]) or 0) / f["vM"]) for f in pos2])

    pr("\n== NEGATIVOS LIMPIOS: cuantos publicaria cada ROI (sobre-publicacion), por cenit")
    for n in ROIS:
        lo = [f for f in neg if f["z"] is not None and f["z"] < 30]
        hi = [f for f in neg if f["z"] is not None and f["z"] >= 30]
        pr(f"{n:12s} publica z<30 {sum(1 for f in lo if f[f'{n}_pub'] == 1)}/{len(lo)} | z>=30 "
           f"{sum(1 for f in hi if f[f'{n}_pub'] == 1)}/{len(hi)} | K produccion: z<30 "
           f"{sum(1 for f in lo if f['k_pub_prod'] == 1)}/{len(lo)} z>=30 {sum(1 for f in hi if f['k_pub_prod'] == 1)}/{len(hi)}")
    pr("\n== PROTEGIDAS (>= 1 MW) que cada ROI no publica")
    prot = [f for f in pos_ if f["vM"] >= 1.0]
    pr("protegidas pareadas:", len(prot), [(f["hora_utc"], f["vM"]) for f in prot])
    for n in ROIS:
        pr(f"  {n}: pierde", [f["hora_utc"] for f in prot if f[f"{n}_pub"] != 1])
    pr("  K produccion (pub_prod del censo): pierde", [f["hora_utc"] for f in prot if f["k_pub_prod"] != 1])

    pr("\n== DETALLE (positivos, orden de cenit): razon por ROI (fondo codigo) | anillo K | K pc")
    pr("hora_utc         z     vM   B0    B1    B2    B3    B5   | B1aK  B2aK | Kpc  | dcB2 distB2")
    for f in sorted(pos_, key=lambda y: y["z"]):
        def g_(v):
            v = fl(v)
            return f"{v / f['vM']:5.2f}" if v is not None else "  -  "
        pr(f"{f['hora_utc']} {f['z']:5.1f} {f['vM']:5.2f} {g_(f['B0_def_vrp'])} {g_(f['B1_sens_vrp'])} "
           f"{g_(f['B2_crater_vrp'])} {g_(f['B3_inner_vrp'])} {g_(f['B5_corona_vrp'])} | {g_(f['B1_sens_vrp_anilloK'])} "
           f"{g_(f['B2_crater_vrp_anilloK'])} | {g_(f['k_pc_vrp'])} | {f['B2_crater_dc']!s:6s} {fl(f['B2_crater_dist']) or -1:5.2f}")
    with open(AQUI / "v01_por_pasada.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    json.dump(resumen, open(AQUI / "v01_resumen.json", "w", encoding="utf-8"), indent=1, default=str)
    (AQUI / "v01_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
