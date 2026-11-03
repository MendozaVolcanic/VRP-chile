# -*- coding: utf-8 -*-
"""s02 (S173, cenit PCC V750): la ablación de V750-C (S162) restringida a Puyehue-Cordón Caulle, pasada por pasada,
con los brazos de fondo corregidos para un inner de 20 km.

POR QUÉ. En Chillán la caída de la razón con el cenit la reprodujo, dentro de la grilla, sólo el fondo de anillo de K.
PCC es otro fenómeno: el lacolito de Cordón Caulle es una anomalía débil y extensa a ~7,6 km del punto del volcán, en
una meseta alta, rodeada a 5-25 km por valles y lagos más bajos. Si el fondo de anillo es la palanca también aquí, el
brazo que mete ese fondo tiene que bajar la razón (nivel) y hacerla caer con el cenit (pendiente).

DEFECTO DE INSTRUMENTO QUE ESTE SCRIPT CORRIGE (sólo en sus brazos propios, sin tocar el original): en
oraculo_ablacion.py el anillo del fondo (vrp, fondo='anillo') y el de la compuerta (detectar, compuerta) van de
inner_km a 25 km del centro de la grilla. En Chillán inner = 5 y eso coincide con K. Pero K usa SIEMPRE 5 a 25 km
(pipeline/process_viirs_mod.py l. 570, `bg_mask = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)`; BG_INNER_KM 5,0,
BG_OUTER_KM 25,0 en pipeline.profile), y en PCC inner = 20: los brazos O_fanillo, O_comp, O_comp1 y O_todoK del
original miden un anillo de 20 a 25 km que K no usa. Se corren igual (para comparar) y se agregan brazos «K525» con
el anillo de K: se pasa inner_km = 5 al oráculo y se fija el círculo de la caja 'circ' en 20 km (monkeypatch local de
OA.caja, sólo en este proceso).

Controles (antes de los resultados): identidad O = port de R2; O = geo_linear del runner; cuántas pasadas cambia cada
brazo; control positivo (+10 % de M13 en los alertados de O cambia el VRP); los brazos K525 cambian contra sus
gemelos de 20-25 km (si no, el arreglo no actúa).
Uso: python -B s02_ablacion_pcc.py
"""
from __future__ import annotations

import collections
import csv
import importlib.util
import io
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
REPO = AQUI / "repo"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
import banco_paridad as B  # noqa: E402,F401

sys.path.insert(0, str(AQUI / "src" / "s162"))
import oraculo_ablacion as OA  # noqa: E402
import ablacion as AB  # noqa: E402

INS = AQUI / "insumos"
GRILLAS = Path("D:/vrp-trabajo/temporales/s159_n")
VOL = "PuyehueCordonCaulle"
INNER_K_FONDO = 5.0  # BG_INNER_KM de K
L = []
_caja_orig = OA.caja
_CIRC_KM = {"v": None}


def _caja_parcheada(tipo, inner_km=None):
    if tipo == "circ" and _CIRC_KM["v"] is not None:
        return _caja_orig(tipo, _CIRC_KM["v"])
    return _caja_orig(tipo, inner_km)


OA.caja = _caja_parcheada

def _arms():
    """Brazos: base (O = caja del ejemplo 'def', S = 'sens' 21 x 21 sensible = B1 de V750-B, C = círculo de inner
    20 km sensible = B3) más una pieza de K cada vez. Sufijo 525: la pieza usa el anillo de K (5-25 km del centro);
    sufijo 2025: el anillo del original (inner a 25 km). Valor: (cambios sobre PIEZAS_MIROVA, usa_anillo_525)."""
    a = {}
    for base, caja in (("O", "def"), ("S", "sens"), ("C", "circ")):
        b0 = {"caja": caja}
        a[base] = (b0, False)
        a[f"{base}_8vec"] = ({**b0, "ocho_vecinos": True}, False)
        a[f"{base}_regp1"] = ({**b0, "reg_p1": True}, False)
        a[f"{base}_umbK"] = ({**b0, "umbrales_k": True}, False)
        a[f"{base}_comp1_525"] = ({**b0, "compuerta": "p1"}, True)
        a[f"{base}_comp_525"] = ({**b0, "compuerta": "ambos"}, True)
        a[f"{base}_rec"] = ({**b0, "recorte": True}, False)
        a[f"{base}_fan525"] = ({**b0, "fondo": "anillo"}, True)
        a[f"{base}_fan525_rec"] = ({**b0, "fondo": "anillo", "recorte": True}, True)
        a[f"{base}_fan2025"] = ({**b0, "fondo": "anillo"}, False)
        a[f"{base}_sinhalo"] = ({**b0, "fondo": "sin_halo"}, False)
    todo = {"ocho_vecinos": True, "reg_p1": True, "umbrales_k": True, "compuerta": "p1", "caja": "circ",
            "recorte": True, "fondo": "anillo"}
    a["todoK525"] = (todo, True)
    a["todoK525_fcodigo"] = ({k: v for k, v in todo.items() if k != "fondo"}, True)
    a["todoK525_sinrec"] = ({k: v for k, v in todo.items() if k != "recorte"}, True)
    a["todoK525_sincomp"] = ({k: v for k, v in todo.items() if k != "compuerta"}, True)
    a["todoK525_fcodigo_sincomp"] = ({k: v for k, v in todo.items() if k not in ("fondo", "compuerta")}, True)
    a["todoK2025"] = (todo, False)  # = O_todoK del original (anillo 20-25)
    return a


ARMS = _arms()


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def correr(m13, m15, dayflag, sg, P, inn, k525):
    if k525:
        _CIRC_KM["v"] = inn
        try:
            mask, d = OA.detectar(m13, m15, dayflag, sg, P, inner_km=INNER_K_FONDO, devolver_diag=True)
            v = OA.vrp(m13, mask, P, inner_km=INNER_K_FONDO)
        finally:
            _CIRC_KM["v"] = None
    else:
        mask, d = OA.detectar(m13, m15, dayflag, sg, P, inner_km=inn, devolver_diag=True)
        v = OA.vrp(m13, mask, P, inner_km=inn)
    return mask, d, v


def main():
    spec = importlib.util.spec_from_file_location("r2", INS / "oraculo_r2" / "mirova_v750_r2.py")
    R2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(R2)
    res, obj = AB.cargar(INS)
    inner = B.inner_desde_html()
    inn = inner[VOL]
    todos = [i for i in obj if obj[i]["volcan"] == VOL]
    ids = [i for i in todos if i in res and res[i].get("estado") == "ok" and res[i].get("oraculo")
           and res[i].get("dayflag") == 0 and obj[i]["clase"] != "diurna"]
    pr("== INVENTARIO PCC")
    pr("inner del tablero:", inn, "| objetivos de PCC:", len(todos), "| con resultado ok, oráculo y noche:", len(ids))
    pr("fuera:", dict(collections.Counter((res.get(i, {}).get("estado"), obj[i]["clase"]) for i in todos
                                          if i not in ids)))
    red = list((INS / "n").rglob("redisparo_*.json"))
    red_p = []
    for f in red:
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r["id"] in obj and obj[r["id"]]["volcan"] == VOL:
                red_p.append((r["id"], r.get("estado"), obj[r["id"]]["clase"]))
    pr("redisparo (no leído por ablacion.cargar), filas de PCC:", red_p)
    cen = {(o["grilla"]["centro_lat"], o["grilla"]["centro_lon"]) for i, o in obj.items() if o["volcan"] == VOL}
    pr("centros de grilla de PCC:", cen)

    brazos = {}
    for b, (cambio, k525) in ARMS.items():
        P = dict(OA.PIEZAS_MIROVA)
        P.update(cambio)
        brazos[b] = (P, k525)
    filas = []
    ctrl = collections.Counter()
    for i in sorted(ids):
        r, o = res[i], obj[i]
        gp = AB.buscar_grilla(GRILLAS, i)
        if gp is None:
            ctrl["sin_grilla"] += 1
            continue
        z = np.load(gp)
        m13, m15 = z["m13"], z["m15"]
        dayflag, sg = r["dayflag"], r["sunglint"]
        mr2, _l = R2.detectar(m13, m15, OA.caja("def"), dayflag, sg)
        vr2 = R2.vrp(m13, mr2)
        s = {}
        for b, (P, k525) in brazos.items():
            mask, d, v = correr(m13, m15, dayflag, sg, P, inn, k525)
            rr, cc = np.nonzero(mask)
            s[b] = {"mask": mask, "npix": v["npix"], "vrp": v["VRP_MW"], "L_hot": v["L_hot"], "L_bk": v["L_bk"],
                    "t_bg": d.get("t_bg"),
                    "pix": [(int(x), int(y), float(m13[x, y])) for x, y in zip(rr, cc)]}
        same = np.array_equal(s["O"]["mask"], mr2) and (
            (vr2["npix"] == 0 and s["O"]["npix"] == 0) or abs(vr2["VRP_MW"] - s["O"]["vrp"]) < 1e-9)
        ctrl["identidad_ok" if same else "identidad_FALLA"] += 1
        gl = r["oraculo"]["geo_linear"]
        runner_ok = gl["npix"] == s["O"]["npix"] and (
            gl["vrp_mw"] is None and s["O"]["npix"] == 0
            or gl["vrp_mw"] is not None and abs(gl["vrp_mw"] - s["O"]["vrp"]) < 1e-6)
        ctrl["runner_ok" if runner_ok else "runner_FALLA"] += 1

        def difiere(a, b):
            return (not np.array_equal(s[a]["mask"], s[b]["mask"])
                    or (s[a]["npix"] and not np.isclose(s[a]["vrp"], s[b]["vrp"], equal_nan=True)))

        for b in brazos:
            base = b.split("_")[0] if b[0] in "OSC" and (len(b) == 1 or b[1] == "_") else "C"
            if b != base and difiere(b, base):
                ctrl[f"actua_{b}"] += 1
        for base in ("O", "S", "C"):
            if difiere(f"{base}_fan525", f"{base}_fan2025"):
                ctrl[f"525_vs_2025_{base}"] += 1
        if difiere("todoK525", "todoK2025"):
            ctrl["525_vs_2025_todoK"] += 1
        for base in ("O", "S", "C"):
            if s[base]["npix"]:
                m13b = np.array(m13, float)
                m13b[s[base]["mask"]] *= 1.10
                vb = OA.vrp(m13b, s[base]["mask"], brazos[base][0], inner_km=inn)
                ctrl[f"pos_{base}_cambia" if not np.isclose(vb["VRP_MW"], s[base]["vrp"]) else f"pos_{base}_NO"] += 1
        # fondos medidos en la grilla: mediana del anillo 5-25 y 20-25 km (sin máscara), y fondo del código bajo el
        # pico de O
        dk = OA.dist_km_centro()
        fin = np.isfinite(m13)
        a525 = float(np.median(m13[(dk >= 5) & (dk <= 25) & fin]))
        a2025 = float(np.median(m13[(dk > 20) & (dk <= 25) & fin]))
        k = (r.get("brazos") or {}).get("K", {}).get("record") or {}
        pc = k.get("primary_cluster") or {}
        geo = r.get("geometria_centro") or {}
        rc_k = AB.celda_k(o, k) if pc.get("centroid_lat") is not None else None
        # posición de O: pico (más radiante) y celdas
        c = OA.N // 2
        posic = {}
        for base in ("O", "S", "C"):
            pO = s[base]["pix"]
            if pO:
                pk = max(pO, key=lambda p: p[2])
                posic[f"{base}_pk_rc"] = (pk[0], pk[1])
                posic[f"{base}_pk_dcen_km"] = float(np.hypot(pk[0] - c, pk[1] - c) * 0.75)
                rr_ = np.array([p[0] for p in pO]); cc_ = np.array([p[1] for p in pO])
                posic[f"{base}_cen_rc"] = (float(rr_.mean()), float(cc_.mean()))
            else:
                posic[f"{base}_pk_rc"] = posic[f"{base}_pk_dcen_km"] = posic[f"{base}_cen_rc"] = None
            if rc_k is not None and pO:
                posic[f"d_k_{base}pico_km"] = float(np.hypot(rc_k[0] - pk[0], rc_k[1] - pk[1]) * 0.75)
                posic[f"d_k_{base}cerca_km"] = float(min(np.hypot(rc_k[0] - p[0], rc_k[1] - p[1]) for p in pO) * 0.75)
            else:
                posic[f"d_k_{base}pico_km"] = posic[f"d_k_{base}cerca_km"] = None
        fila = {"id": i, "hora_utc": o["hora_utc"], "lab": o["lab"], "clase": o["clase"],
                "protegida": o.get("protegida"), "decide": o.get("decide"), "obj_mirova_vrp": o.get("mirova_vrp"),
                "grilla": str(gp.relative_to(GRILLAS)), "z_record_K": k.get("sensor_zenith_deg"),
                "z_geometria_centro": geo.get("sensor_zenith"), "k_sensor": k.get("sensor"),
                "k_datetime": k.get("datetime_utc"), "k_pc_vrp": pc.get("vrp_mw"), "k_pc_npix": pc.get("n_pixels"),
                "k_dc": k.get("distance_class"), "k_t_bg": k.get("t_bg_k"), "k_L_bg": k.get("diag_L_bg_w_m2_sr_um"),
                "k_rc": rc_k, "k_dcen_km": (float(np.hypot(rc_k[0] - c, rc_k[1] - c) * 0.75) if rc_k else None),
                **posic,
                "anillo525_L_med": a525, "anillo2025_L_med": a2025}
        for b in brazos:
            fila[f"{b}_npix"] = s[b]["npix"]
            fila[f"{b}_vrp"] = None if not s[b]["npix"] else s[b]["vrp"]
            fila[f"{b}_Lhot"] = None if not s[b]["npix"] else s[b]["L_hot"]
            fila[f"{b}_Lbk"] = None if not s[b]["npix"] else s[b]["L_bk"]
            fila[f"{b}_pub"] = AB.publica(s[b]["npix"], s[b]["vrp"], s[b]["pix"], inn)
            fila[f"{b}_tbg"] = s[b]["t_bg"]
        for v in AB.RUNNER:
            x = r["oraculo"].get(v) or {}
            pix = [(p[0], p[1], p[4]) for p in x.get("pixeles", [])]
            fila[f"{v}_npix"] = x.get("npix")
            fila[f"{v}_vrp"] = x.get("vrp_mw")
            fila[f"{v}_pub"] = AB.publica(x.get("npix"), x.get("vrp_mw"), pix, inn) if pix else False
        filas.append(fila)

    pr("\n== CONTROLES sobre PCC (leer antes de los resultados)")
    pr("pasadas con grilla:", len(filas), "| sin grilla en disco:", ctrl["sin_grilla"])
    pr("ventana de datos (hora_utc):", min(f["hora_utc"] for f in filas), "a", max(f["hora_utc"] for f in filas))
    pr("(1) identidad contra el port de R2: ok", ctrl["identidad_ok"], "FALLA", ctrl["identidad_FALLA"])
    pr("(2) brazo O = geo_linear del runner: ok", ctrl["runner_ok"], "FALLA", ctrl["runner_FALLA"])
    pr("(3) pasadas en que cada brazo cambia máscara o VRP contra O:",
       {b: ctrl[f"actua_{b}"] for b in brazos if b != "O"})
    pr("(3b) anillo 5-25 contra 20-25 (máscara o VRP distintos):",
       {k_: v for k_, v in ctrl.items() if k_.startswith("525_vs")})
    pr("(4) control positivo (+10 % M13 en alertados de la base):",
       {k_: v for k_, v in ctrl.items() if k_.startswith("pos_")})
    pr("pasadas con al menos un alertado por base:", {b: sum(1 for f in filas if f[f"{b}_npix"]) for b in "OSC"})
    zk = [(f["z_record_K"], f["z_geometria_centro"]) for f in filas]
    dif = [abs(a - b) for a, b in zk if a is not None and b is not None]
    pr("cenit: record K presente en", sum(a is not None for a, _ in zk), "de", len(zk), "| |record - centro| máx:",
       round(max(dif), 3) if dif else None, "mediana:", round(float(np.median(dif)), 3) if dif else None)
    pr("clases:", dict(collections.Counter((f["lab"], f["clase"]) for f in filas)))
    cols = list(filas[0].keys())
    with open(AQUI / "s02_por_pasada.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
    (AQUI / "s02_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
