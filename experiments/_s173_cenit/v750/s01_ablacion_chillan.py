# -*- coding: utf-8 -*-
"""s01 (S173, cenit V750): la ablación de V750-C (S162) restringida a Nevados de Chillán, pasada por pasada.

POR QUÉ. En Chillán la razón K / MIROVA de VIIRS 750 cae con el cenit (S172: Spearman -0,81, n 39). La ablación de
V750-C reemplaza, sobre la grilla GEO lineal que guardó el runner de N (S159), cada pieza del programa de MIROVA por la
de K, de a una. Si al meter una pieza de K reaparece la caída oblicua, esa pieza es la causa; si con TODAS las piezas
de K que existen en la grilla (O_todoK) la razón sigue plana mientras K nativo cae, lo que queda es lo que la grilla no
cambia: el remuestreo y la geometría nativa del píxel (D17).

Este script sólo CORRE los brazos (reusa BRAZOS, piezas, cargar, buscar_grilla y publica de ablacion.py sin tocarlos) y
escribe una fila por pasada de Chillán. El pareo con MIROVA y los estratos van en s02.

Controles (se imprimen ANTES de cualquier resultado, sobre las pasadas de Chillán):
 (1) identidad: brazo O de este módulo = port de R2 (máscara y VRP) en cada grilla de Chillán;
 (2) brazo O = geo_linear del runner (npix y vrp_mw) en cada grilla de Chillán;
 (3) cuántas pasadas de Chillán cambia cada brazo contra O (un brazo que no cambia nada no mide su pieza);
 (4) control positivo: O con la grilla M13 multiplicada por 1,1 en el excedente debe cambiar el VRP (el instrumento
     ve un cambio de radiancia); se hace sobre el brazo O.
Uso: python -B s01_ablacion_chillan.py
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
import banco_paridad as B  # noqa: E402,F401  (pre-importado para que ablacion.py lo tome de sys.modules)

sys.path.insert(0, str(AQUI / "src" / "s162"))
import oraculo_ablacion as OA  # noqa: E402
import ablacion as AB  # noqa: E402

INS = AQUI / "insumos"
GRILLAS = Path("D:/vrp-trabajo/temporales/s159_n")
VOL = "NevadosDeChillan"
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


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
    pr("== INVENTARIO Chillán")
    pr("objetivos de Chillán:", len(todos), "| con resultado ok, oráculo y noche:", len(ids))
    pr("estados de los que quedan fuera:",
       dict(collections.Counter((res.get(i, {}).get("estado"), obj[i]["clase"]) for i in todos if i not in ids)))
    # el redisparo no lo lee ablacion.cargar (rglob 'resultados_*.json' no calza con 'redisparo_..._resultados_*')
    red = list((INS / "n").rglob("redisparo_*.json"))
    red_ch = []
    for f in red:
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r["id"] in obj and obj[r["id"]]["volcan"] == VOL:
                red_ch.append((r["id"], r.get("estado"), obj[r["id"]]["clase"]))
    pr("redisparo (no leído por ablacion.cargar), filas de Chillán:", red_ch)

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
        for b in AB.BRAZOS:
            P = AB.piezas(b)
            mask, d = OA.detectar(m13, m15, dayflag, sg, P, inner_km=inn, devolver_diag=True)
            v = OA.vrp(m13, mask, P, inner_km=inn)
            rr, cc = np.nonzero(mask)
            s[b] = {"mask": mask, "npix": v["npix"], "vrp": v["VRP_MW"], "L_hot": v["L_hot"], "L_bk": v["L_bk"],
                    "pix": [(int(x), int(y), float(m13[x, y])) for x, y in zip(rr, cc)]}
        same = np.array_equal(s["O"]["mask"], mr2) and (
            (vr2["npix"] == 0 and s["O"]["npix"] == 0) or abs(vr2["VRP_MW"] - s["O"]["vrp"]) < 1e-9)
        ctrl["identidad_ok" if same else "identidad_FALLA"] += 1
        gl = r["oraculo"]["geo_linear"]
        runner_ok = gl["npix"] == s["O"]["npix"] and (
            gl["vrp_mw"] is None and s["O"]["npix"] == 0
            or gl["vrp_mw"] is not None and abs(gl["vrp_mw"] - s["O"]["vrp"]) < 1e-6)
        ctrl["runner_ok" if runner_ok else "runner_FALLA"] += 1
        for b in AB.BRAZOS:
            if b != "O" and (not np.array_equal(s[b]["mask"], s["O"]["mask"])
                             or (s[b]["npix"] and not np.isclose(s[b]["vrp"], s["O"]["vrp"]))):
                ctrl[f"actua_{b}"] += 1
        # (4) control positivo: subir 10 % la radiancia M13 de los píxeles alertados por O (misma máscara)
        if s["O"]["npix"]:
            m13b = np.array(m13, float)
            m13b[s["O"]["mask"]] *= 1.10
            vb = OA.vrp(m13b, s["O"]["mask"], AB.piezas("O"), inner_km=inn)
            ctrl["pos_cambia" if not np.isclose(vb["VRP_MW"], s["O"]["vrp"]) else "pos_NO_cambia"] += 1
        k = (r.get("brazos") or {}).get("K", {}).get("record") or {}
        pc = k.get("primary_cluster") or {}
        geo = r.get("geometria_centro") or {}
        fila = {"id": i, "hora_utc": o["hora_utc"], "lab": o["lab"], "clase": o["clase"],
                "protegida": o.get("protegida"), "decide": o.get("decide"), "obj_mirova_vrp": o.get("mirova_vrp"),
                "archivo0": (r.get("archivos") or [None])[0], "grilla": str(gp.relative_to(GRILLAS)),
                "z_record_K": k.get("sensor_zenith_deg"), "z_geometria_centro": geo.get("sensor_zenith"),
                "k_sensor": k.get("sensor"), "k_datetime": k.get("datetime_utc"), "k_pc_vrp": pc.get("vrp_mw"),
                "k_pc_npix": pc.get("n_pixels"), "k_dc": k.get("distance_class")}
        for b in AB.BRAZOS:
            fila[f"{b}_npix"] = s[b]["npix"]
            fila[f"{b}_vrp"] = None if not s[b]["npix"] else s[b]["vrp"]
            fila[f"{b}_Lhot"] = None if not s[b]["npix"] else s[b]["L_hot"]
            fila[f"{b}_Lbk"] = None if not s[b]["npix"] else s[b]["L_bk"]
            fila[f"{b}_pub"] = AB.publica(s[b]["npix"], s[b]["vrp"], s[b]["pix"], inn)
        for v in AB.RUNNER:
            x = r["oraculo"].get(v) or {}
            pix = [(p[0], p[1], p[4]) for p in x.get("pixeles", [])]
            fila[f"{v}_npix"] = x.get("npix")
            fila[f"{v}_vrp"] = x.get("vrp_mw")
            fila[f"{v}_pub"] = AB.publica(x.get("npix"), x.get("vrp_mw"), pix, inn) if pix else False
        filas.append(fila)

    pr("\n== CONTROLES sobre Chillán (leer antes de los resultados)")
    pr("pasadas de Chillán con grilla:", len(filas), "| sin grilla en disco:", ctrl["sin_grilla"])
    pr("ventana de datos (hora_utc):", min(f["hora_utc"] for f in filas), "a", max(f["hora_utc"] for f in filas))
    pr("(1) identidad contra el port de R2: ok", ctrl["identidad_ok"], "FALLA", ctrl["identidad_FALLA"])
    pr("(2) brazo O = geo_linear del runner (npix y vrp): ok", ctrl["runner_ok"], "FALLA", ctrl["runner_FALLA"])
    pr("(3) pasadas de Chillán en que cada brazo cambia máscara o VRP contra O:",
       {b: ctrl[f"actua_{b}"] for b in AB.BRAZOS if b != "O"})
    pr("(4) control positivo (+10 % en M13 de los alertados por O): cambia", ctrl["pos_cambia"], "NO cambia",
       ctrl["pos_NO_cambia"])
    zk = [(f["z_record_K"], f["z_geometria_centro"]) for f in filas]
    dif = [abs(a - b) for a, b in zk if a is not None and b is not None]
    pr("cenit: record K presente en", sum(a is not None for a, _ in zk), "de", len(zk),
       "| geometria_centro presente en", sum(b is not None for _, b in zk),
       "| |record - centro| máx:", round(max(dif), 3) if dif else None, "mediana:",
       round(float(np.median(dif)), 3) if dif else None)
    pr("clases:", dict(collections.Counter((f["lab"], f["clase"]) for f in filas)))

    cols = list(filas[0].keys())
    with open(AQUI / "s01_por_pasada.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for f in filas:
            w.writerow(f)
    (AQUI / "s01_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
