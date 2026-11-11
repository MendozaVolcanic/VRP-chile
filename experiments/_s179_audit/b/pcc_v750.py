# -*- coding: utf-8 -*-
"""Auditoría S179 frente B. Cordón Caulle en VIIRS 750 durante la sombra: record crudo de la vía y de K contra MIROVA.
Pregunta 1 (¿vería algo roto?): se imprime el VRP crudo del record y el mostrado; si difieren, el tablero recorta.
Pregunta 2 (¿instrumento muerto?): cada pasada sale con su fila de MIROVA; sin fila se imprime None."""
import json, os, sys
from pathlib import Path
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding="utf-8")
MAIN = Path(r"D:\vrp-trabajo\temporales\s179-audit\main"); DATOS = Path(r"D:\vrp-trabajo\temporales\s179-audit\b\datos")
os.environ["VRP_PROFILE"] = "mirova_equivalent"
for p in (str(MAIN), str(MAIN / "scripts")): sys.path.insert(0, p)
import vigilancia_guardia_viirs as vv, banco_paridad as bp, referencia_mirova_unificada as rmu
vg, vs, aa = vv.vg, vv.vs, vv.aa
WIN = ("2026-11-03", "2026-11-10")
coords = aa._coords_por_volcan(); inner = bp.inner_desde_html()
filas = rmu.cargar_referencia_unificada(MAIN / "latest_consolidado.csv", DATOS / "ref" / "registro_vrp_ocr.csv",
    respaldo_path=DATOS / "ref" / "registro_vrp_consolidado_respaldo_20260408.csv",
    historico_path=DATOS / "union" / "consolidado_filas_perdidas.csv")
for vol, sensor in (("PuyehueCordonCaulle", "VIIRS750"), ("PuyehueCordonCaulle", "VIIRS375"), ("Tupungatito", "VIIRS750")):
    print(f"\n== {vol} {sensor}: pasadas nocturnas con alerta de MIROVA, {WIN[0]} a {WIN[1]}")
    via = [r for r in bp.cargar_nuestros(coords, inner, WIN, data=DATOS / "sombra_codigo_mirova") if r["b"] == sensor and r["vol"] == vol]
    k = [r for r in bp.cargar_nuestros(coords, inner, WIN, data=DATOS / "mirova_equivalent") if r["b"] == sensor and r["vol"] == vol]
    crudos = {}
    for carpeta in ("sombra_codigo_mirova", "mirova_equivalent"):
        with open(DATOS / carpeta / f"{vol}.json", encoding="utf-8") as fh:
            for r in json.load(fh)["records"]:
                crudos[(carpeta, r.get("sensor"), str(r.get("datetime_utc"))[:16])] = r
    for p in vs.pasadas_de_alerta(filas, via, k, WIN, diurna=vs._diurna_por_defecto()):
        if p["volcano"] != vol or p["sensor"] != sensor: continue
        dt = datetime.strptime(p["instante_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        fs = [f for f in filas if f["volcano"] == vol and f["sensor_bucket"] == sensor and f["fecha_utc"][:16] == p["fecha_utc"][:16]]
        ref = [(f["tipo"], f["vrp_mw"], f.get("dist_km"), f["source"]) for f in fs]
        out = []
        for nombre, recs, carpeta in (("vía", via, "sombra_codigo_mirova"), ("K", k, "mirova_equivalent")):
            c = [r for r in recs if abs((r["dt"] - dt).total_seconds()) <= vg.TOL_S]
            if not c: out.append(f"{nombre}: sin record"); continue
            rc = crudos.get((carpeta, c[0]["sensor"], c[0]["dt"].strftime("%Y-%m-%d %H:%M"))) or {}
            pc = rc.get("primary_cluster") or {}
            out.append(f"{nombre}: pub {c[0]['pub']} mostrado {c[0]['disp']} | crudo vrp_mw {rc.get('vrp_mw')} pc.vrp {pc.get('vrp_mw')} "
                       f"n_pix {rc.get('n_anomalous_pixels')} clase {rc.get('distance_class')} dist {rc.get('final_hotspot_dist_km')} "
                       f"roi {(rc.get('diag_codigo_mirova') or {}).get('roi')} t_max {rc.get('t_max_k')}")
        print(f"  {p['fecha_utc']} MIROVA {ref}\n      " + "\n      ".join(out))
