#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoría S179, frente B. Detalle de la semana de la sombra (2026-11-03 a 11-09), sensor por sensor.

POR QUÉ. Tres cosas que la regla de reversión deja sin cota o que los PR dejan «por probar»:
(a) las pasadas que la guardia K registra y la vía no (la vía no escribe record cuando el gránulo no cubre el volcán):
    cuántas son, en qué volcán, y si MIROVA alertó en ellas (la cota (i) no las ve y la regla sólo mira las protegidas);
(b) qué magnitud MUESTRA el tablero con un record de la vía (el predicado del tablero ejecutado con node, no leído),
    contra MIROVA, por volcán: es lo que el operador verá saltar el día del encendido;
(c) las Muy Bajo que la vía calla: por qué las calla (sin detección, o detección que el tablero no publica).

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si lo medido estuviera roto, ¿lo vería? (b) trae a K al lado en las mismas pasadas: K tiene que dar cerca de 0,5 y
   la vía cerca de 1 (cifras ya medidas por otros); si las dos dieran lo mismo, el montaje estaría leyendo un solo lado.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Cada cifra lleva su n; con n = 0 se imprime SIN DATO.

Base: código main 438a60a1e; datos de 438a60a1e. Guardia = data/guardia_k_viirs; vía = data/sombra_codigo_mirova.
"""
import json
import os
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
MAIN = Path(r"D:\vrp-trabajo\temporales\s179-audit\main")
DATOS = Path(r"D:\vrp-trabajo\temporales\s179-audit\b\datos")
AQUI = Path(__file__).resolve().parent
os.environ["VRP_PROFILE"] = "mirova_equivalent"
for p in (str(MAIN), str(MAIN / "scripts")):
    sys.path.insert(0, p)
import vigilancia_guardia_viirs as vv  # noqa: E402
import banco_paridad as bp  # noqa: E402
import referencia_mirova_unificada as rmu  # noqa: E402

vg, vs, aa = vv.vg, vv.vs, vv.aa
WIN = ("2026-11-03", "2026-11-09")


def crudo(carpeta, vol, sensor_txt, minuto):
    with open(DATOS / carpeta / f"{vol}.json", encoding="utf-8") as fh:
        for r in json.load(fh)["records"]:
            if r.get("sensor") == sensor_txt and str(r.get("datetime_utc"))[:16] == minuto:
                return r
    return None


def main():
    coords = aa._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = rmu.cargar_referencia_unificada(MAIN / "latest_consolidado.csv", DATOS / "ref" / "registro_vrp_ocr.csv",
                                            respaldo_path=DATOS / "ref" / "registro_vrp_consolidado_respaldo_20260408.csv",
                                            historico_path=DATOS / "union" / "consolidado_filas_perdidas.csv")
    res = {}
    for sensor in ("VIIRS375", "VIIRS750"):
        print(f"\n================ {sensor} · noches {WIN[0]} a {WIN[1]}")
        via = [r for r in bp.cargar_nuestros(coords, inner, WIN, data=DATOS / "sombra_codigo_mirova") if r["b"] == sensor]
        gua = [r for r in bp.cargar_nuestros(coords, inner, WIN, data=DATOS / "guardia_k_viirs") if r["b"] == sensor]
        bp.etiquetar(gua, *bp.indexar_referencia(filas, coords, WIN, regla_minimas="SN")[:3])
        ivia = defaultdict(list)
        for r in via:
            ivia[r["vol"]].append(r)
        # (a) pasadas que la guardia registra y la vía no
        faltan = [g for g in gua if not [r for r in ivia[g["vol"]] if abs((r["dt"] - g["dt"]).total_seconds()) <= vg.TOL_S]]
        print(f"(a) la guardia K registra {len(gua)} pasadas; la vía no tiene record en {len(faltan)} "
              f"({100 * len(faltan) / max(len(gua), 1):.1f} %). Por volcán: {dict(Counter(g['vol'] for g in faltan))}; "
              f"por etiqueta de MIROVA: {dict(Counter(g['lab'] for g in faltan))}; la guardia publica en "
              f"{sum(1 for g in faltan if g['pub'])}")
        for g in faltan:
            print(f"      {g['vol']} {g['sensor']} {g['dt']:%Y-%m-%d %H:%M} cenit {g['z']} etiqueta {g['lab']} "
                  f"guardia_pub {g['pub']} VRP mostrado por K {g['disp']}")
        # (b) magnitud mostrada contra MIROVA en pasadas con alerta, vía y K, mismas pasadas
        pasadas = [p for p in vs.pasadas_de_alerta(filas, via, gua, WIN, diurna=vs._diurna_por_defecto())
                   if p["sensor"] == sensor and not p["minima"]]
        igua = defaultdict(list)
        for r in gua:
            igua[r["vol"]].append(r)
        razones = defaultdict(lambda: {"via": [], "k": []})
        for p in pasadas:
            dt = datetime.strptime(p["instante_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            v = [r for r in ivia[p["volcano"]] if abs((r["dt"] - dt).total_seconds()) <= vg.TOL_S]
            k = [r for r in igua[p["volcano"]] if abs((r["dt"] - dt).total_seconds()) <= vg.TOL_S]
            m = p["vrp_mirova_mw"]
            if not (v and k and m and v[0]["pub"] and k[0]["pub"]):
                continue
            razones[p["volcano"]]["via"].append(v[0]["disp"] / m)
            razones[p["volcano"]]["k"].append(k[0]["disp"] / m)
            razones["TODOS"]["via"].append(v[0]["disp"] / m)
            razones["TODOS"]["k"].append(k[0]["disp"] / m)
        print("(b) VRP que MUESTRA el tablero sobre el de MIROVA, pasadas con alerta que los dos publican (mediana, n):")
        for vol, d in sorted(razones.items()):
            n = len(d["via"])
            print(f"      {vol}: n {n}; vía {statistics.median(d['via']):.3f}; K {statistics.median(d['k']):.3f}; "
                  f"salto vía/K {statistics.median(d['via']) / statistics.median(d['k']):.2f}")
        if not razones:
            print("      SIN DATO")
        res[sensor] = {"guardia": len(gua), "via_sin_record": len(faltan),
                       "razones": {v: {"n": len(d["via"]), "via": round(statistics.median(d["via"]), 3),
                                       "k": round(statistics.median(d["k"]), 3)} for v, d in razones.items()}}
        # (c) Muy Bajo que K publica y la vía calla: cómo es el record de la vía
        print("(c) alertas de MIROVA bajo 1 MW (sobre 0,05) que K publica y la vía, con record, no publica:")
        n_c = 0
        for p in pasadas:
            if p["protegida"] or not (p["sombra_pub"] is True and p["prod_pub"] is False):
                continue
            n_c += 1
            dt = datetime.strptime(p["instante_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            v = [r for r in ivia[p["volcano"]] if abs((r["dt"] - dt).total_seconds()) <= vg.TOL_S][0]
            rc = crudo("sombra_codigo_mirova", v["vol"], v["sensor"], v["dt"].strftime("%Y-%m-%d %H:%M")) or {}
            kc = [r for r in igua[p["volcano"]] if abs((r["dt"] - dt).total_seconds()) <= vg.TOL_S][0]
            print(f"      {p['volcano']} {p['fecha_utc']} MIROVA {p['vrp_mirova_mw']} MW: vía n_alertados "
                  f"{rc.get('n_anomalous_pixels')}, vrp_mw {rc.get('vrp_mw')}, distance_class {rc.get('distance_class')}, "
                  f"dist {rc.get('final_hotspot_dist_km')} km, motivo {(rc.get('diag_codigo_mirova') or {}).get('motivo_vacio')}; "
                  f"K mostraba {kc['disp']} MW")
        if not n_c:
            print("      ninguna")
    with open(AQUI / "re_detalle_sombra_salida.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    print("\nsalida 0")


if __name__ == "__main__":
    main()
