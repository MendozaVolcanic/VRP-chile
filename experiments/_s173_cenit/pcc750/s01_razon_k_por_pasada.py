# -*- coding: utf-8 -*-
"""s01 (S173, cenit PCC V750): razón K / MIROVA POR PASADA en Puyehue-Cordón Caulle, VIIRS 750, por tramo de cenit.

POR QUÉ. El auto-audit del 2026-11-02 marca PCC VIIRS 750 con razón 0,512 (n 14 noches), «causa sin medir». Pero
divide nuestro máximo de la noche por el de MIROVA: dos pasadas que pueden ser distintas. Aquí se parea la MISMA
pasada (alerta de MIROVA VIIRS 750 contra nuestro record del mismo minuto, +-120 s), y se parte por el cenit que
guarda el record (sensor_zenith_deg). Si la caída con el cenit de Chillán se repite, el déficit es de pendiente; si la
razón es baja también cerca del nadir, es de nivel.

Vara: referencia del scraper Mirova-v1 (repo/data/mirova_reference/mirova_v1_snapshot de origin/main), unión CONS+OCR,
regla D-9 SN (banco_paridad.indexar_referencia regla_minimas="SN"; los avisos A119 salen por stderr), VRP de la fila
CONS si es ALERTA, si no la OCR. Magnitud nuestra = la que publica el tablero (predicado de node, banco_paridad.
cargar_nuestros: `disp`, pc.vrp_mw en VIIRS 750) y, aparte, campos crudos del record.

Unidad: la ALERTA de MIROVA (no nuestro record). Una alerta sin record nuestro o con record que no publica cuenta 0 en
la razón «con ceros»; la razón «publicada» sólo usa pares donde publicamos.

P1 (si lo medido estuviera roto, ¿lo vería?): control positivo, disp x2 dobla la mediana; control de lectura, `disp`
    del tablero contra pc.vrp_mw del JSON; cenit del record contra Zenith_Sat_deg del OCR cuando existe.
P2 (instrumento muerto): pareo con la referencia corrida +1 día (los pares deben caer a ~0); barajado del cenit 200
    veces, semilla 173.
Uso: python -B s01_razon_k_por_pasada.py   (escribe s01_salida.txt, s01_por_alerta.csv, s01_resumen.json)
"""
from __future__ import annotations

import collections
import csv
import io
import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
REPO = AQUI / "repo"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(AQUI))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402
from _est import fl, linea, med, q  # noqa: E402

VOL = "PuyehueCordonCaulle"
VENTANAS = {"auditoria": ("2026-09-03", "2026-11-02"), "amplia": ("2026-04-01", "2026-11-02")}
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def hav(a, b, c, e):
    R, r = 6371.0, math.pi / 180
    x = math.sin((c - a) * r / 2) ** 2 + math.cos(a * r) * math.cos(c * r) * math.sin((e - b) * r / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def main():
    bp.VOLS = [VOL]
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    pr("== CONFIG")
    pr("volcán:", VOL, "| coords:", coords[VOL], "| inner del tablero:", inner[VOL])
    pr("SNAP_CONS:", bp.SNAP_CONS, "| SNAP_OCR:", bp.SNAP_OCR)
    ident = bp.control_identidad_predicado()
    pr("identidad del predicado (node):", ident)
    ref = bp.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
    # zenith del OCR, para cruzar con el del record
    zocr = {}
    with open(bp.SNAP_OCR, encoding="utf-8") as fh:
        for f in csv.DictReader(fh):
            if "Puyehue" in f["Volcan"] and "750" in (f.get("Ruta Foto") or ""):
                zocr[f["Fecha_Satelite_UTC"][:16]] = fl(f.get("Zenith_Sat_deg"))
    d = json.load(open(REPO / "data" / "mirova_equivalent" / f"{VOL}.json", encoding="utf-8"))
    extra = {}
    for r in d["records"]:
        pc = r.get("primary_cluster") or {}
        px = r.get("anomaly_pixels") or []
        extra[(r.get("sensor"), r.get("datetime_utc"))] = {
            "pc_vrp": pc.get("vrp_mw"), "pc_n": pc.get("n_pixels"), "pc_lat": pc.get("centroid_lat"),
            "pc_lon": pc.get("centroid_lon"), "pc_dist_ancla": pc.get("centroid_dist_km"),
            "pc_single": pc.get("single_pixel_mode"), "escena_vrp": r.get("vrp_mw"),
            "n_anom": r.get("n_anomalous_pixels"), "n_px_lista": len(px),
            "suma_px_vrp": sum((p.get("vrp_mw") or 0) for p in px),
            "suma_px_vrp_pos": sum(max(p.get("vrp_mw") or 0, 0) for p in px),
            "t_bg": r.get("t_bg_k"), "L_bg": r.get("diag_L_bg_w_m2_sr_um"), "t_max": r.get("t_max_k"),
            "hs_dist_vol": r.get("hotspot_dist_km"), "fhs": r.get("final_hotspot_source"),
            "proc": r.get("processed_utc"), "sha": (r.get("regimen") or {}).get("codigo_sha"),
            "pc_dist_vol": (hav(pc["centroid_lat"], pc["centroid_lon"], *coords[VOL])
                            if pc.get("centroid_lat") is not None else None)}
    resumen = {}
    for nombre_v, ventana in VENTANAS.items():
        pr(f"\n################ VENTANA {nombre_v}: {ventana[0]} a {ventana[1]} (noche UTC)")
        por_vb, ns, nv, n_ref = bp.indexar_referencia(ref, coords, ventana, regla_minimas="SN")
        lista = por_vb.get((VOL, "VIIRS750"), [])
        recs = [r for r in bp.cargar_nuestros(coords, inner, ventana) if r["b"] == "VIIRS750"]
        pr("filas nocturnas de referencia (todos):", n_ref, "| filas VIIRS750 PCC:", len(lista),
           "| records K VIIRS750 PCC nocturnos:", len(recs))
        alertas = [(dt, f) for dt, f in lista if bp.es_alerta(f["tipo"]) and (f.get("vrp_mw") or 0) > 0]
        pr("alertas MIROVA VIIRS750 PCC (SN):", len(alertas), "| tipos:",
           dict(collections.Counter(f["tipo"] for _, f in alertas)),
           "| fuente:", dict(collections.Counter(f["source"] for _, f in alertas)))
        # agrupar filas por pasada (CONS y OCR de la misma pasada a +-120 s)
        pasadas = []
        usadas = set()
        for dt, f in alertas:
            if id(f) in usadas:
                continue
            fs = [g for g in bp.parear(lista, dt) if bp.es_alerta(g["tipo"]) and (g.get("vrp_mw") or 0) > 0]
            for g in fs:
                usadas.add(id(g))
            c = [g for g in fs if g["source"] == "CONS"]
            fm = (c or fs)[0]
            pasadas.append((dt, fm, bool(c)))
        pr("pasadas con alerta (CONS y OCR fundidos):", len(pasadas))
        rows = []
        ctrl = collections.Counter()
        for dt, fm, hay_cons in pasadas:
            cand = [r for r in recs if abs((r["dt"] - dt).total_seconds()) <= bp.TOL_S]
            # control +1 día: ¿hay alerta un día después del record?
            r0 = cand[0] if cand else None
            if len(cand) > 1:
                ctrl["varios_records"] += 1
            e = extra.get((r0["sensor"], r0["dt"].strftime("%Y-%m-%d %H:%M")), {}) if r0 else {}
            x = {"dt_M": fm["fecha_utc"][:16], "noche": fm["fecha_utc"][:10], "vM": fm["vrp_mw"], "srcM": fm["source"],
                 "hay_cons": hay_cons, "distM": fm.get("dist_km"), "tipoM": fm["tipo"],
                 "z_ocr": zocr.get(fm["fecha_utc"][:16]),
                 "tiene_record": r0 is not None, "sensor": (r0 or {}).get("sensor"),
                 "dt_K": r0["dt"].strftime("%Y-%m-%d %H:%M") if r0 else None, "z": (r0 or {}).get("z"),
                 "pub": (r0 or {}).get("pub"), "disp": (r0 or {}).get("disp"), "dc": (r0 or {}).get("dc"), **e}
            rows.append(x)
        # P2: referencia +1 día contra nuestros records publicados
        sh = 0
        for r in recs:
            fs = [g for g in bp.parear(lista, r["dt"] + timedelta(days=1)) if bp.es_alerta(g["tipo"])]
            if fs and r["pub"] == 1:
                sh += 1
        directo = 0
        for r in recs:
            fs = [g for g in bp.parear(lista, r["dt"]) if bp.es_alerta(g["tipo"])]
            if fs and r["pub"] == 1:
                directo += 1
        pr("\n== CONTROLES")
        pr("alertas sin record K a +-120 s:", sum(not x["tiene_record"] for x in rows), "de", len(rows))
        pr("alertas con más de un record K a +-120 s:", ctrl["varios_records"])
        pr("P2: records publicados pareados con alerta: directo", directo, "| con la referencia +1 día", sh)
        dl = [x for x in rows if x["pub"] == 1 and (x["disp"] or 0) > 0 and x["pc_vrp"] is not None
              and abs(x["disp"] - x["pc_vrp"]) > 1e-6]
        pr("control de lectura: disp del tablero distinto de pc.vrp_mw del JSON (publicados):", len(dl))
        zz = [(x["z"], x["z_ocr"]) for x in rows if x["z"] is not None and x["z_ocr"] is not None]
        pr("cenit del record contra Zenith_Sat_deg del OCR: n", len(zz), "| |dif| máx",
           round(max(abs(a - b) for a, b in zz), 2) if zz else None, "| mediana |dif|",
           round(med([abs(a - b) for a, b in zz]), 2) if zz else None)
        sinz = [x for x in rows if x["tiene_record"] and x["z"] is None]
        pr("records pareados sin sensor_zenith_deg:", len(sinz))
        pr("plataformas:", dict(collections.Counter(x["sensor"] for x in rows)))
        pr("noches:", len({x["noche"] for x in rows}), "| ventana de alertas:", min(x["dt_M"] for x in rows), "a",
           max(x["dt_M"] for x in rows))
        R = [x for x in rows if x["z"] is not None]
        pr("cenit de las alertas pareadas:", sorted(round(x["z"], 1) for x in R))
        pr("n z<30:", sum(x["z"] < 30 for x in R), "| n z>=30:", sum(x["z"] >= 30 for x in R))
        pr("publica el tablero: z<30", sum(1 for x in R if x["z"] < 30 and x["pub"] == 1), "| z>=30",
           sum(1 for x in R if x["z"] >= 30 and x["pub"] == 1))

        def razon_ceros(x, campo="disp"):
            v = x[campo] if campo != "disp" else (x["disp"] if x["pub"] == 1 else 0.0)
            v = fl(v) or 0.0
            return max(v, 0.0) / x["vM"]

        res = {}
        pr("\n== RAZÓN K / MIROVA POR PASADA")
        res["tablero_con_ceros"] = linea(pr, "tablero, con ceros", [(x["z"], razon_ceros(x)) for x in R])
        P = [x for x in R if x["pub"] == 1 and (x["disp"] or 0) > 0]
        res["tablero_publicadas"] = linea(pr, "tablero, publicadas", [(x["z"], x["disp"] / x["vM"]) for x in P])
        res["x2_control"] = linea(pr, "control x2", [(x["z"], 2 * x["disp"] / x["vM"]) for x in P])
        res["pc_json_con_ceros"] = linea(pr, "pc.vrp_mw JSON, c/ceros", [(x["z"], razon_ceros(x, "pc_vrp")) for x in R])
        res["escena_con_ceros"] = linea(pr, "escena (vrp_mw), c/ceros",
                                        [(x["z"], razon_ceros(x, "escena_vrp")) for x in R])
        res["suma_px_pos_con_ceros"] = linea(pr, "suma px>0, c/ceros",
                                             [(x["z"], razon_ceros(x, "suma_px_vrp_pos")) for x in R])
        C = [x for x in R if x["hay_cons"]]
        pr("\n-- sólo alertas con fila CONS (A119): n", len(C))
        res["cons_tablero_con_ceros"] = linea(pr, "CONS tablero c/ceros", [(x["z"], razon_ceros(x)) for x in C])
        pr("\n-- desde el 2026-06-13 (OCR con distancia medida, A119)")
        D = [x for x in R if x["noche"] >= "2026-06-13"]
        res["desde0613_con_ceros"] = linea(pr, "desde 06-13 c/ceros", [(x["z"], razon_ceros(x)) for x in D])

        pr("\n-- por noche (como el auto-audit: máximo nuestro publicado / máximo de MIROVA de la noche), referencia")
        noches = collections.defaultdict(list)
        for x in R:
            noches[x["noche"]].append(x)
        rn = []
        for n, v in noches.items():
            mm = max(y["vM"] for y in v)
            ours = [y["disp"] for y in v if y["pub"] == 1 and (y["disp"] or 0) > 0]
            if ours:
                rn.append(max(ours) / mm)
        pr("razón por noche (noches con publicación nuestra en pasada con alerta):", q(rn))

        pr("\n-- DESCOMPOSICIÓN (pares publicados), por cenit")
        for nombre, fn in (("pc n_pixels", lambda x: fl(x["pc_n"])),
                           ("n_anomalous escena", lambda x: fl(x["n_anom"])),
                           ("escena/pc (VRP)", lambda x: fl(x["escena_vrp"]) / x["disp"] if fl(x["escena_vrp"]) else None),
                           ("t_bg K", lambda x: fl(x["t_bg"])),
                           ("t_max K", lambda x: fl(x["t_max"])),
                           ("dist pc al volcán km", lambda x: fl(x["pc_dist_vol"])),
                           ("dist MIROVA km", lambda x: fl(x["distM"])),
                           ("vM MIROVA MW", lambda x: x["vM"])):
            v = [(x["z"], fn(x)) for x in P if fn(x) is not None]
            linea(pr, nombre, v)
        pr("\n== DETALLE (orden de cenit)")
        pr("dt_M              sensor             z     vM    src  pub disp   razón  pc_n esc_vrp n_an  t_bg   dpcV  dM")
        for x in sorted(R, key=lambda y: y["z"]):
            rz = razon_ceros(x)
            pr(f"{x['dt_M']} {x['sensor'] or '-':18s} {x['z']:5.1f} {x['vM']:5.2f} {x['srcM']:4s} {x['pub']!s:>3} "
               f"{(x['disp'] or 0):6.3f} {rz:6.3f} {x['pc_n']!s:>4} {fl(x['escena_vrp']) or 0:6.3f} {x['n_anom']!s:>4} "
               f"{fl(x['t_bg']) or 0:6.1f} {fl(x['pc_dist_vol']) or -1:5.2f} {fl(x['distM']) or -1:5.2f}")
        resumen[nombre_v] = {"ventana": ventana, "n_alertas": len(rows), "n_con_z": len(R), **res}
        with open(AQUI / f"s01_por_alerta_{nombre_v}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    json.dump(resumen, open(AQUI / "s01_resumen.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False,
              default=str)
    (AQUI / "s01_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
