# -*- coding: utf-8 -*-
"""Verificador V750-C: mediciones propias sobre las mismas grillas e insumos que ablacion.py (S162).

Pregunta 1 (si lo medido estuviera roto, se veria): cada conteo se calcula con tolerancia 0 y 1 celda, y se
imprime la distancia en celdas entre la celda de K y el pixel detectado mas cercano; si la tolerancia fabricara
coincidencias, los conteos con tol 0 y tol 1 difieren.
Pregunta 2 (si el instrumento estuviera muerto, se veria distinto): el control positivo es el lote de 48 cumbres
donde MIROVA alerto, en que el .m detecta en el pixel de K en 33 de 48 (tol 1); si la celda de K estuviera mal
ubicada, ese 33 cae a ~0 con tol 0.
Uso: python medir.py --insumos <carpeta> --grillas D:/vrp-trabajo/temporales/s159_n [--csv <ablacion_por_pasada.csv>]
"""
from __future__ import annotations

import argparse
import collections
import csv
import statistics
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import ablacion as A  # noqa: E402
import oraculo_ablacion as OA  # noqa: E402
import banco_paridad as B  # noqa: E402

BRAZOS = ("O", "O_8vec", "O_todoK_sincomp", "O_sens", "O_circ")
RUNNER = ("geo_nearest", "geo_cubic", "r2_linear", "r2_nearest")


def dist_celdas(pix, rc):
    """Distancia Chebyshev minima en celdas entre la celda de K y los pixeles detectados (inf si no hay)."""
    if not pix:
        return np.inf
    return min(max(abs(a - rc[0]), abs(b - rc[1])) for a, b in pix)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insumos", required=True, type=Path)
    ap.add_argument("--grillas", required=True, type=Path)
    ap.add_argument("--csv", type=Path, default=None)
    a = ap.parse_args()
    res, obj = A.cargar(a.insumos)
    inner = B.inner_desde_html()
    ids = [i for i, r in res.items() if r.get("estado") == "ok" and r.get("oraculo") and r.get("dayflag") == 0
           and obj[i]["clase"] != "diurna"]
    print("pasadas nocturnas con oraculo:", len(ids))

    def k_de(r):
        k = (r.get("brazos") or {}).get("K", {}).get("record") or {}
        return k, (k.get("primary_cluster") or {})

    sel = {}
    for i in ids:
        r, o = res[i], obj[i]
        k, pc = k_de(r)
        cumbre0 = k.get("distance_class") == "summit" and pc.get("vrp_mw") == 0
        if o["clase"] == "cumbre_0mw":
            sel.setdefault("censo60", []).append(i)
        if cumbre0 and o["lab"] == "pos" and i < 1000:
            sel.setdefault("pos48", []).append(i)
        if o["lab"] == "pos" and o.get("decide") and o.get("protegida"):
            sel.setdefault("prot78", []).append(i)
    for g, v in sel.items():
        print(g, len(v))

    # ---------- V2 / V9 / control positivo: tolerancia de la celda de K
    box_def = OA.caja("def")
    filas = {}
    for g in ("censo60", "pos48"):
        print(f"\n== {g}: detecta en la celda de K, tol 0 / tol 1 (3x3) / tol 2 (5x5); n = {len(sel[g])}")
        cnt = collections.defaultdict(lambda: [0, 0, 0])
        dists = collections.defaultdict(list)
        for i in sel[g]:
            r, o = res[i], obj[i]
            k, pc = k_de(r)
            rc = A.celda_k(o, k)
            rc2 = A.celda_k(o, k, "r2")
            z = np.load(A.buscar_grilla(a.grillas, i))
            m13, m15 = z["m13"], z["m15"]
            inn = inner[o["volcan"]]
            fila = {"id": i, "volcan": o["volcan"], "rc": rc, "zona_k_def": None if not np.isfinite(box_def[rc]) else int(box_def[rc]),
                    "dist_centro_km": float(np.hypot(rc[0] - OA.N // 2, rc[1] - OA.N // 2) * 0.75), "inner": inn,
                    "k_pc_dist": pc.get("centroid_dist_km")}
            for b in BRAZOS:
                P = A.piezas(b)
                mask = OA.detectar(m13, m15, r["dayflag"], r["sunglint"], P, inner_km=inn)
                pix = [tuple(x) for x in zip(*np.nonzero(mask))]
                d = dist_celdas(pix, rc)
                dists[b].append(d)
                for t in (0, 1, 2):
                    cnt[b][t] += int(d <= t)
                fila[f"{b}_dcel"] = d
            for v in RUNNER:
                x = r["oraculo"].get(v) or {}
                pix = [(p[0], p[1]) for p in x.get("pixeles", [])]
                ref = rc2 if v.startswith("r2") else rc
                d = dist_celdas(pix, ref)
                dists[v].append(d)
                for t in (0, 1, 2):
                    cnt[v][t] += int(d <= t)
                fila[f"{v}_dcel"] = d
                fila[f"{v}_presente"] = bool(x)
            filas[i] = fila
        print(f"{'brazo':18s} tol0 tol1 tol2   distancias en celdas de los que caen a tol<=2")
        for b in list(BRAZOS) + list(RUNNER):
            dd = sorted(x for x in dists[b] if x <= 2)
            print(f"{b:18s} {cnt[b][0]:4d} {cnt[b][1]:4d} {cnt[b][2]:4d}   {collections.Counter(dd)}")
        print("zona de la caja por defecto donde cae la celda de K:",
              dict(collections.Counter(filas[i]["zona_k_def"] for i in sel[g])))
        print("distancia de la celda de K al centro de la grilla (km): mediana",
              round(statistics.median(filas[i]["dist_centro_km"] for i in sel[g]), 2),
              "| max", round(max(filas[i]["dist_centro_km"] for i in sel[g]), 2))
        print("pasadas sin resultado del runner (SIN DATO) por variante:",
              {v: sum(1 for i in sel[g] if not filas[i][f"{v}_presente"]) for v in RUNNER})

    # V9 Tupungatito
    tup = [i for i in sel["censo60"] if obj[i]["volcan"] == "Tupungatito"]
    print(f"\n== V9 Tupungatito en el censo: n = {len(tup)}")
    for v in ("geo_nearest", "r2_nearest", "O", "O_todoK_sincomp"):
        print(f"  {v:16s} tol0 {sum(filas[i][f'{v}_dcel'] <= 0 for i in tup)} tol1 {sum(filas[i][f'{v}_dcel'] <= 1 for i in tup)}"
              f" | con algun pixel {sum(np.isfinite(filas[i][f'{v}_dcel']) for i in tup)}"
              f" | distancias: {collections.Counter(str(int(filas[i][f'{v}_dcel'])) if np.isfinite(filas[i][f'{v}_dcel']) else 'inf' for i in tup)}")
    print("  Tupungatito: motivo_vacio / nan_m13 / n_abs,n_p1,n_p2 de geo_linear y geo_nearest en el runner (SIN DATO o cero real):")
    for i in tup:
        gl, gn = res[i]["oraculo"]["geo_linear"], res[i]["oraculo"]["geo_nearest"]
        print(f"    id {i} {obj[i]['hora_utc']} z {obj[i].get('z')} | lin: motivo {gl.get('motivo_vacio')} nan {gl.get('nan_m13')} "
              f"abs/p1/p2 {gl.get('n_abs')}/{gl.get('n_p1')}/{gl.get('n_p2')} | near: motivo {gn.get('motivo_vacio')} nan {gn.get('nan_m13')} "
              f"abs/p1/p2 {gn.get('n_abs')}/{gn.get('n_p1')}/{gn.get('n_p2')} | K pc_dist {obj[i].get('pc_dist')} rc {filas[i]['rc']} zona {filas[i]['zona_k_def']}")
    print("  motivo_vacio en el censo entero (geo_nearest):", dict(collections.Counter(
        (obj[i]['volcan'], res[i]['oraculo']['geo_nearest'].get('motivo_vacio')) for i in sel['censo60'])))
    print("  por volcan, geo_nearest tol1:", dict(collections.Counter(obj[i]["volcan"] for i in sel["censo60"]
                                                                   if filas[i]["geo_nearest_dcel"] <= 1)))
    print("  por volcan, censo:", dict(collections.Counter(obj[i]["volcan"] for i in sel["censo60"])))

    # ---------- V3: exceso nativo vs exceso de grilla, misma definicion?
    print("\n== V3: exceso de grilla (celda exacta de K vs max 3x3) / exceso nativo (F de K); estratos por halo k de F")
    for g in ("censo60", "pos48"):
        ex_max, ex_exacto, por_k, nhot = [], [], collections.defaultdict(list), []
        for i in sel[g]:
            r, o = res[i], obj[i]
            k, pc = k_de(r)
            rc = A.celda_k(o, k)
            z = np.load(A.buscar_grilla(a.grillas, i))
            m13 = z["m13"]
            F = r["brazos"].get("F") or {}
            lh, lb = (F.get("F_L_hot_pc") or [None])[0], (F.get("F_L_bk_pc") or [None])[0]
            if lh is None or lb is None:
                continue
            nat = lh - lb
            a0, b0 = max(rc[0] - 1, 0), max(rc[1] - 1, 0)
            win = m13[a0:rc[0] + 2, b0:rc[1] + 2]
            ia = np.unravel_index(np.nanargmax(win), win.shape)
            fm = np.zeros_like(m13, bool)
            fm[a0 + ia[0], b0 + ia[1]] = True
            vg = OA.vrp(m13, fm, OA.PIEZAS_MIROVA)
            fe = np.zeros_like(m13, bool)
            fe[rc] = True
            ve = OA.vrp(m13, fe, OA.PIEZAS_MIROVA)
            if nat > 0:
                ex_max.append((vg["L_hot"] - vg["L_bk"]) / nat)
                ex_exacto.append((ve["L_hot"] - ve["L_bk"]) / nat)
                por_k[F.get("F_k")].append((vg["L_hot"] - vg["L_bk"]) / nat)
                nhot.append(F.get("n_hot"))
        q = lambda v: (f"mediana {statistics.median(v):.3f} [q1 {np.percentile(v, 25):.3f}, q3 {np.percentile(v, 75):.3f}] n={len(v)}"
                       if v else "sin datos")
        print(f"  {g}: max 3x3 -> {q(ex_max)} | celda exacta -> {q(ex_exacto)}")
        print(f"  {g}: por halo k del fondo de F (k=3 si <=4 alertados en la escena): " +
              " | ".join(f"k={kk}: {q(v)}" for kk, v in sorted(por_k.items(), key=lambda x: str(x[0]))))
        print(f"  {g}: n_hot de K en la escena (define el halo de F): {collections.Counter(nhot)}")

    # ---------- V8: las protegidas que O pierde y O_sens recupera: donde cae el pixel
    print("\n== V8: protegidas que deciden; O pierde / O_sens u O_circ recupera; donde cae el pixel mas radiante")
    n_o = n_s = n_c = 0
    for i in sel["prot78"]:
        r, o = res[i], obj[i]
        inn = inner[o["volcan"]]
        z = np.load(A.buscar_grilla(a.grillas, i))
        m13, m15 = z["m13"], z["m15"]
        out = {}
        for b in ("O", "O_sens", "O_circ"):
            P = A.piezas(b)
            mask = OA.detectar(m13, m15, r["dayflag"], r["sunglint"], P, inner_km=inn)
            v = OA.vrp(m13, mask, P, inner_km=inn)
            rr, cc = np.nonzero(mask)
            pix = [(int(x), int(y), float(m13[x, y])) for x, y in zip(rr, cc)]
            out[b] = (A.publica(v["npix"], v["VRP_MW"], pix, inn), v, pix)
        n_o += out["O"][0]; n_s += out["O_sens"][0]; n_c += out["O_circ"][0]
        if not out["O"][0]:
            k, pc = k_de(r)
            for b in ("O_sens", "O_circ"):
                pub, v, pix = out[b]
                if pix:
                    pa, pb, _ = max(pix, key=lambda p: p[2])
                    dk = float(np.hypot(pa - OA.N // 2, pb - OA.N // 2) * 0.75)
                    zonas = collections.Counter(int(box_def[x, y]) for x, y, _ in pix if np.isfinite(box_def[x, y]))
                    print(f"  id {i} {o['volcan']} {o['hora_utc']} MIROVA {o['mirova_vrp']} inner {inn} | {b}: publica {pub} "
                          f"npix {v['npix']} vrp {v['VRP_MW']:.3f} | pico a {dk:.2f} km del centro, zonas(caja def) {dict(zonas)} "
                          f"| K pc_dist {pc.get('centroid_dist_km')} pc_vrp {pc.get('vrp_mw')} dc {k.get('distance_class')}")
                else:
                    print(f"  id {i} {o['volcan']} {o['hora_utc']} MIROVA {o['mirova_vrp']} | {b}: sin pixeles")
    print(f"  publica: O {n_o}/{len(sel['prot78'])}  O_sens {n_s}  O_circ {n_c}")

    # ---------- V5 / V6 desde el CSV (del re-run)
    if a.csv and a.csv.exists():
        rows = list(csv.DictReader(open(a.csv, encoding="utf-8")))
        f = lambda s: s == "True"
        negl = [x for x in rows if x["lab"] == "neg_limpio" and int(x["id"]) < 1000]
        print(f"\n== V5 desde {a.csv.name}: negativos limpios del lote {len(negl)}, ventana {min(x['hora_utc'] for x in negl)} a {max(x['hora_utc'] for x in negl)}")
        for b in ("O", "geo_nearest", "r2_linear", "O_todoK_sincomp"):
            pub = [x for x in negl if f(x[f"{b}_pub"])]
            print(f"  {b:16s} publica {len(pub):3d} (peso {sum(float(x['peso']) for x in pub):6.1f}) | por volcan "
                  f"{dict(collections.Counter(x['volcan'] for x in pub))} | con algun pixel {sum(1 for x in negl if x[f'{b}_npix'] not in ('', '0', 'None'))}")
        pos = [x for x in rows if x["lab"] == "pos" and f(x["decide"])]
        print(f"\n== V6 desde el CSV: alertas que deciden {len(pos)}; razon O/MIROVA por volcan")
        for b in ("O", "O_fanillo", "O_sinhalo"):
            por_v = collections.defaultdict(list)
            for x in pos:
                if f(x[f"{b}_pub"]) and x["mirova_vrp"] not in ("", "0", "0.0", "None"):
                    por_v[x["volcan"]].append(float(x[f"{b}_vrp"]) / float(x["mirova_vrp"]))
            print(f"  {b:10s} " + " | ".join(f"{v} {statistics.median(z):.3f} n={len(z)}" for v, z in sorted(por_v.items())))


if __name__ == "__main__":
    main()
