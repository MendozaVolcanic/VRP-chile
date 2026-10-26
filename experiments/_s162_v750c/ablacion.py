# -*- coding: utf-8 -*-
"""V750-C (S162): ablación del oráculo de MIROVA VIIRS 750 sobre las grillas del frente N de S159.

POR QUÉ. Nuestro detector K encuentra, en la cumbre de Isluga, Tupungatito, Láscar y otros, píxeles tibios aislados que
deja en 0,0 MW; el código de MIROVA, en su grilla, no los ve (censo de N: 1 de 60 negativos limpios). Antes de adoptar
el paquete del código hay que saber QUÉ pieza los calla: si es el remuestreo a la grilla fija, el remuestreo (D17) es
condición del paquete; si es otra pieza (media 3 x 3 con el central, umbrales, segundo pase, caja), se puede aislar.
Y en las alertas, qué pieza da la magnitud.

Brazos: cada pieza del .m reemplazada por la de K, una a la vez, sobre la grilla GEO lineal (la única guardada:
probe_n.py:383); más las variantes de remuestreo que N ya corrió en el runner (vecino más cercano, cúbico, grilla de
R2), leídas de los resultados con la posición de cada píxel. «Sin remuestreo» no se puede correr: las grillas no
traen la ventana nativa. Sustituto: la radiancia nativa del píxel de K (F_L_hot_pc, F_L_bk_pc de los resultados de N)
contra la de la celda de la grilla.

Controles (se imprimen ANTES de los resultados): (1) identidad: con las piezas del .m este módulo da la misma máscara y
el mismo VRP que el port de R2 en todas las grillas; (2) las grillas son las del runner: el brazo O reproduce npix y
vrp_mw de geo_linear de los resultados en todas las pasadas; (3) cada brazo cambia al menos una máscara o un VRP
(si no, el reemplazo no actúa).

Uso: python ablacion.py --insumos <carpeta de extraer_insumos.sh> --grillas D:\\vrp-trabajo\\temporales\\s159_n
"""
from __future__ import annotations

import argparse
import collections
import csv
import importlib.util
import json
import statistics
import sys
from pathlib import Path

import numpy as np
from pyproj import Transformer

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(ROOT / "scripts"))
import oraculo_ablacion as OA  # noqa: E402
import banco_paridad as B  # noqa: E402

BRAZOS = {
    "O": {},
    "O_8vec": {"ocho_vecinos": True},
    "O_regp1": {"reg_p1": True},
    "O_umbK": {"umbrales_k": True},
    "O_comp": {"compuerta": "ambos"},
    "O_comp1": {"compuerta": "p1"},
    "O_sens": {"caja": "sens"},
    "O_circ": {"caja": "circ"},
    "O_rec": {"recorte": True},
    "O_fanillo": {"fondo": "anillo"},
    "O_sinhalo": {"fondo": "sin_halo"},
    # K en la grilla: todas las piezas de K que existen en la grilla. Si ni esto ve las cumbres, lo que las calla
    # es el remuestreo (la única pieza que este brazo no cambia).
    "O_todoK": {"ocho_vecinos": True, "reg_p1": True, "umbrales_k": True, "compuerta": "p1", "caja": "circ",
                "recorte": True, "fondo": "anillo"},
    "O_todoK_sincomp": {"ocho_vecinos": True, "reg_p1": True, "umbrales_k": True, "caja": "circ"},
}
RUNNER = ("geo_nearest", "geo_cubic", "r2_linear", "r2_nearest")
ORDEN_RUNS = ("run_39682867040", "run_39693661527", "run_39680724047")


def piezas(b):
    p = dict(OA.PIEZAS_MIROVA)
    p.update(BRAZOS[b])
    return p


def cargar(ins):
    res = {}
    for f in sorted((ins / "n").rglob("resultados_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok" or r["id"] not in res:
                res[r["id"]] = r
    obj = {}
    for nom in ("objetivos_n.json", "objetivos_censo.json"):
        for o in json.loads((ins / "n" / nom).read_text(encoding="utf-8")):
            obj[o["id"]] = o
    return res, obj


def buscar_grilla(raiz, i):
    for run in ORDEN_RUNS:
        for p in sorted((raiz / run).glob(f"*/grilla_{i:03d}.npz")):
            return p
    return None


def celda_k(o, rec, utm_ul="geo"):
    """Fila y columna de la grilla donde cae el centroide del cúmulo de K."""
    pc = rec["primary_cluster"]
    g = o["grilla"]
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
    x, y = t.transform(pc["centroid_lon"], pc["centroid_lat"])
    ulx, uly = (g["ul_x"], g["ul_y"]) if utm_ul == "geo" else (g["ul_x_r2"], g["ul_y_r2"])
    return int(np.floor((uly - y) / OA.CELDA)), int(np.floor((x - ulx) / OA.CELDA))


def en_celda(pixeles_rc, rc, tol=1):
    return any(abs(a - rc[0]) <= tol and abs(b - rc[1]) <= tol for a, b in pixeles_rc)


def publica(npix, vrp_mw, pix_rc_m13, inner):
    """Predicado de N (04_oraculo_grilla.alerta): >= 1 píxel, VRP > 0, píxel más radiante a <= inner del centro."""
    if not npix or not vrp_mw or not np.isfinite(vrp_mw) or vrp_mw <= 0:
        return False
    a, b, _ = max(pix_rc_m13, key=lambda p: p[2])
    c = OA.N // 2
    return float(np.hypot(a - c, b - c) * 0.75) <= inner


def margen_en_k(d, rc, box):
    """Fracción del umbral que alcanza el mejor píxel del entorno 3 x 3 de la celda de K en el pase 1:
    min(c_nti/u_nti, c_eti/u_eti) con los umbrales de su zona. >= 1 sería alerta del pase 1."""
    p = d.get("pasada1") or {}
    if "c_eti" not in p:
        return np.nan, None
    mejor, zona = -np.inf, None
    for a in range(rc[0] - 1, rc[0] + 2):
        for b in range(rc[1] - 1, rc[1] + 2):
            if not (0 <= a < OA.N and 0 <= b < OA.N) or not np.isfinite(box[a, b]):
                continue
            z = int(box[a, b])
            un, ue = (p["u_nti2"], p["u_eti2"]) if z == 2 else (p["u_nti1"], p["u_eti1"])
            cn, ce = p["c_nti"][a, b], p["c_eti"][a, b]
            if not (np.isfinite(cn) and np.isfinite(ce)):
                continue
            f = min(cn / un, ce / ue)
            if f > mejor:
                mejor, zona = f, z
    return (mejor if np.isfinite(mejor) else np.nan), zona


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insumos", required=True, type=Path)
    ap.add_argument("--grillas", required=True, type=Path)
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("r2", a.insumos / "oraculo_r2" / "mirova_v750_r2.py")
    R2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(R2)
    res, obj = cargar(a.insumos)
    inner = B.inner_desde_html()
    L = []

    def pr(*x):
        s = " ".join(str(y) for y in x)
        print(s, flush=True)
        L.append(s)

    ids = [i for i, r in res.items() if r.get("estado") == "ok" and r.get("oraculo") and r.get("dayflag") == 0
           and obj[i]["clase"] != "diurna"]
    filas, salida = [], {}
    ctrl = collections.Counter()
    for i in sorted(ids):
        r, o = res[i], obj[i]
        gp = buscar_grilla(a.grillas, i)
        if gp is None:
            ctrl["sin_grilla"] += 1
            continue
        z = np.load(gp)
        m13, m15 = z["m13"], z["m15"]
        inn = inner[o["volcan"]]
        dayflag, sg = r["dayflag"], r["sunglint"]
        # control 1: identidad contra el port de R2
        box_def = OA.caja("def")
        mr2, _l = R2.detectar(m13, m15, box_def, dayflag, sg)
        vr2 = R2.vrp(m13, mr2)
        s = {}
        for b in BRAZOS:
            P = piezas(b)
            mask, d = OA.detectar(m13, m15, dayflag, sg, P, inner_km=inn, devolver_diag=True)
            v = OA.vrp(m13, mask, P, inner_km=inn)
            rr, cc = np.nonzero(mask)
            s[b] = {"mask": mask, "npix": v["npix"], "vrp": v["VRP_MW"], "d": d,
                    "pix": [(int(x), int(y), float(m13[x, y])) for x, y in zip(rr, cc)]}
        dO = s["O"]["d"]
        if dO.get("excluidos_p2") and "coef" in dO.get("pasada1", {}) and "coef" in dO.get("pasada2", {}):
            ctrl["regp1_pasadas_con_excluidos"] += 1
            if not np.allclose(dO["pasada1"]["coef"], dO["pasada2"]["coef"], rtol=0, atol=0):
                ctrl["regp1_coef_distinto"] += 1
                dif = np.nanmax(np.abs(s["O_regp1"]["d"]["pasada2"]["c_eti"] - dO["pasada2"]["c_eti"]))
                ctrl["regp1_max_dif_ceti_x1e6"] = max(ctrl["regp1_max_dif_ceti_x1e6"], int(dif * 1e6))
        same = np.array_equal(s["O"]["mask"], mr2) and (
            (vr2["npix"] == 0 and s["O"]["npix"] == 0) or abs(vr2["VRP_MW"] - s["O"]["vrp"]) < 1e-9)
        ctrl["identidad_ok" if same else "identidad_FALLA"] += 1
        gl = r["oraculo"]["geo_linear"]
        runner_ok = gl["npix"] == s["O"]["npix"] and (
            gl["vrp_mw"] is None and s["O"]["npix"] == 0
            or gl["vrp_mw"] is not None and abs(gl["vrp_mw"] - s["O"]["vrp"]) < 1e-6)
        ctrl["runner_ok" if runner_ok else "runner_FALLA"] += 1
        for b in BRAZOS:
            if b != "O" and (not np.array_equal(s[b]["mask"], s["O"]["mask"])
                             or (s[b]["npix"] and not np.isclose(s[b]["vrp"], s["O"]["vrp"]))):
                ctrl[f"actua_{b}"] += 1
        # el píxel de K
        k = (r.get("brazos") or {}).get("K", {}).get("record") or {}
        pc = k.get("primary_cluster") or {}
        es_cumbre0 = k.get("distance_class") == "summit" and pc.get("vrp_mw") == 0
        rc = celda_k(o, k) if pc.get("centroid_lat") is not None else None
        rc2 = celda_k(o, k, "r2") if rc else None
        fila = {"id": i, "volcan": o["volcan"], "hora_utc": o["hora_utc"], "lab": o["lab"], "clase": o["clase"],
                "protegida": o.get("protegida"), "decide": o.get("decide"), "mirova_vrp": o.get("mirova_vrp"),
                "peso": o.get("peso"), "k_cumbre0": es_cumbre0, "k_pc_vrp": pc.get("vrp_mw"),
                "k_dist": pc.get("centroid_dist_km"), "k_rc": rc}
        for b in BRAZOS:
            fila[f"{b}_npix"] = s[b]["npix"]
            fila[f"{b}_vrp"] = None if not s[b]["npix"] else s[b]["vrp"]
            fila[f"{b}_pub"] = publica(s[b]["npix"], s[b]["vrp"], s[b]["pix"], inn)
            fila[f"{b}_enK"] = bool(rc) and en_celda([(x, y) for x, y, _ in s[b]["pix"]], rc)
        for v in RUNNER:
            x = r["oraculo"].get(v) or {}
            pix = [(p[0], p[1], p[4]) for p in x.get("pixeles", [])]
            fila[f"{v}_npix"] = x.get("npix")
            fila[f"{v}_vrp"] = x.get("vrp_mw")
            fila[f"{v}_pub"] = publica(x.get("npix"), x.get("vrp_mw"), pix, inn) if pix else False
            ref = rc2 if v.startswith("r2") else rc
            fila[f"{v}_enK"] = bool(ref) and en_celda([(p[0], p[1]) for p in pix], ref)
        if es_cumbre0 and rc:
            f_, zona = margen_en_k(s["O"]["d"], rc, s["O"]["d"]["box"])
            fila["O_margen_p1"], fila["O_zona_k"] = f_, zona
            f8, _z = margen_en_k(s["O_8vec"]["d"], rc, s["O_8vec"]["d"]["box"])
            fila["O8_margen_p1"] = f8
            Fk = r["brazos"].get("F") or {}
            lh, lb = (Fk.get("F_L_hot_pc") or [None])[0], (Fk.get("F_L_bk_pc") or [None])[0]
            a0, b0 = max(rc[0] - 1, 0), max(rc[1] - 1, 0)
            win = m13[a0:rc[0] + 2, b0:rc[1] + 2]
            fila["L_nativa"], fila["L_bk_nativa"] = lh, lb
            fila["L_grilla_max3x3"] = float(np.nanmax(win))
            # exceso en la grilla con el fondo del código, forzando la alerta en la celda más radiante del entorno
            ia = np.unravel_index(np.nanargmax(win), win.shape)
            fm = np.zeros_like(m13, bool)
            fm[a0 + ia[0], b0 + ia[1]] = True
            vg = OA.vrp(m13, fm, OA.PIEZAS_MIROVA)
            fila["exceso_grilla"] = vg["L_hot"] - vg["L_bk"]
            fila["exceso_nativo"] = None if lh is None or lb is None else lh - lb
        filas.append(fila)

    pr("== CONTROLES (leer antes de los resultados)")
    pr("pasadas nocturnas con oráculo:", len(ids), "| sin grilla en disco:", ctrl["sin_grilla"])
    pr("(1) identidad contra el port de R2: ok", ctrl["identidad_ok"], "FALLA", ctrl["identidad_FALLA"])
    pr("(2) brazo O = geo_linear del runner (npix y vrp): ok", ctrl["runner_ok"], "FALLA", ctrl["runner_FALLA"])
    pr("(3) pasadas en que cada brazo cambia máscara o VRP contra O:",
       {b: ctrl[f"actua_{b}"] for b in BRAZOS if b != "O"})
    pr("(3b) O_regp1: pasadas con excluidos del pase 1:", ctrl["regp1_pasadas_con_excluidos"],
       "| con coeficiente del pase 2 distinto del pase 1:", ctrl["regp1_coef_distinto"],
       "| máxima diferencia en c_eti del pase 2 (x1e-6):", ctrl["regp1_max_dif_ceti_x1e6"])

    def grupo(nombre, sel):
        g = [f for f in filas if sel(f)]
        pr(f"\n== {nombre}: n = {len(g)}")
        if not g:
            return g
        pr(f"{'brazo':18s} detecta_en_pixel_K  publica(predicado N)  con_algun_pixel")
        for b in list(BRAZOS) + list(RUNNER):
            pr(f"{b:18s} {sum(f[f'{b}_enK'] for f in g):5d}           {sum(f[f'{b}_pub'] for f in g):5d}"
               f"             {sum(bool(f[f'{b}_npix']) for f in g):5d}")
        return g

    c60 = grupo("CENSO: cumbres de K en 0,0 MW, negativos limpios (MIROVA RUTINA)",
                lambda f: f["clase"] == "cumbre_0mw")
    n6 = grupo("LOTE: cumbres de K en 0,0 MW, negativos limpios (los 6 de F)",
               lambda f: f["k_cumbre0"] and f["lab"] == "neg_limpio" and f["id"] < 1000)
    p48 = grupo("LOTE: cumbres de K en 0,0 MW donde MIROVA SÍ alertó (pos_nopub)",
                lambda f: f["k_cumbre0"] and f["lab"] == "pos" and f["id"] < 1000)
    for nombre, g in (("censo 60", c60), ("lote neg 6", n6), ("lote pos", p48)):
        m = [f["O_margen_p1"] for f in g if np.isfinite(f.get("O_margen_p1", np.nan))]
        m8 = [f["O8_margen_p1"] for f in g if np.isfinite(f.get("O8_margen_p1", np.nan))]
        dil = [f["exceso_grilla"] / f["exceso_nativo"] for f in g
               if f.get("exceso_nativo") and f["exceso_nativo"] > 0 and f.get("exceso_grilla") is not None]
        rl = [f["L_grilla_max3x3"] / f["L_nativa"] for f in g if f.get("L_nativa")]
        q = lambda v: (f"mediana {statistics.median(v):.3f} [q1 {np.percentile(v, 25):.3f}, q3 "
                       f"{np.percentile(v, 75):.3f}] n={len(v)}") if v else "sin datos"
        pr(f"\n-- {nombre}: margen del pase 1 en el entorno del píxel de K (>=1 alertaría), O: {q(m)}")
        pr(f"   mismo margen con 8 vecinos: {q(m8)}")
        pr(f"   zona de la caja por defecto donde cae el mejor píxel: "
           f"{dict(collections.Counter(f.get('O_zona_k') for f in g))}")
        pr(f"   L M13 de la grilla (máx 3x3) / L nativa del píxel de K: {q(rl)}")
        pr(f"   exceso sobre el fondo del código, grilla / nativo (píxel con exceso nativo > 0): {q(dil)}")
        pr(f"   píxeles con exceso nativo <= 0 (el fondo del código en el gránulo no los ve calientes): "
           f"{sum(1 for f in g if f.get('exceso_nativo') is not None and f['exceso_nativo'] <= 0)}")

    # alertas que deciden: detección y magnitud
    pos = [f for f in filas if f["lab"] == "pos" and f["decide"]]
    prot = [f for f in pos if f["protegida"]]
    negl = [f for f in filas if f["lab"] == "neg_limpio" and f["id"] < 1000]
    pr(f"\n== ALERTAS QUE DECIDEN (lote): {len(pos)}, protegidas {len(prot)}; negativos limpios del lote "
       f"{len(negl)} (peso total {sum(f['peso'] for f in negl):.1f}); censo de cumbres y far: "
       f"{sum(1 for f in filas if f['id'] >= 1000)}")
    pr(f"{'brazo':18s} alertas  protegidas  neg_lote(crudo, ponderado)  neg_censo   razón brazo/MIROVA "
       f"mediana [q1, q3] n   entre 0,8 y 1,25   máscara distinta de O en alertas")
    for b in list(BRAZOS) + list(RUNNER):
        det = [f for f in pos if f[f"{b}_pub"]]
        dp = sum(1 for f in prot if f[f"{b}_pub"])
        dn = [f for f in negl if f[f"{b}_pub"]]
        dc = sum(1 for f in filas if f["id"] >= 1000 and f[f"{b}_pub"])
        rz = sorted(f[f"{b}_vrp"] / f["mirova_vrp"] for f in det if f["mirova_vrp"])
        n = len(rz)
        cerca = sum(1 for x in rz if 0.8 <= x <= 1.25)
        dist = (sum(1 for f in pos if f[f"{b}_npix"] != f["O_npix"]) if b in BRAZOS else "-")
        pr(f"{b:18s} {len(det):4d}/{len(pos)}  {dp:3d}/{len(prot)}   {len(dn):3d} ({sum(f['peso'] for f in dn):6.1f})"
           f"      {dc:3d}     "
           + (f"{statistics.median(rz):.3f} [{rz[n // 4]:.3f}, {rz[(3 * n) // 4]:.3f}] n={n}   {cerca}/{n}"
              if n else "sin datos") + f"   {dist}")
    # razón por número de píxeles del oráculo, brazos de fondo
    for b in ("O", "O_rec", "O_fanillo", "O_sinhalo"):
        for et, c in (("1 px", lambda x: x == 1), ("2-4 px", lambda x: 2 <= x <= 4), ("5+ px", lambda x: x >= 5)):
            rz = sorted(f[f"{b}_vrp"] / f["mirova_vrp"] for f in pos
                        if f[f"{b}_pub"] and f["mirova_vrp"] and c(f[f"{b}_npix"]))
            n = len(rz)
            pr(f"  {b} {et}: " + (f"{statistics.median(rz):.3f} [{rz[n // 4]:.3f}, {rz[(3 * n) // 4]:.3f}] n={n}"
                                   if n else "sin datos"))

    cols = sorted({k for f in filas for k in f})
    with open(AQUI / "ablacion_por_pasada.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for f in filas:
            w.writerow({k: f.get(k) for k in cols})
    (AQUI / "ablacion_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
