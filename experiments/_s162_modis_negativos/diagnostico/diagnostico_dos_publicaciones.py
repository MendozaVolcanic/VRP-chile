# -*- coding: utf-8 -*-
"""S162 MOD-C, diagnóstico físico de las dos publicaciones del port en neg_resto que deciden el veredicto (pedido de la
coordinadora, sólo lectura): Láscar 2026-05-11 07:55 (id 1251) y Llaima 2026-07-24 01:05 (id 1120).

POR QUÉ. Con 0 publicaciones el lote habría confirmado el «gana contra K»; con estas 2 queda INDECIDIBLE. Para el censo
de MOD-D importa si son calor real (señal que MIROVA calló en MODIS esa pasada) o artefacto (costo real). Tres fuentes,
independientes del gránulo MODIS donde el port publicó (A109: la otra pasada del mismo gránulo no es independiente):
1. las otras pasadas de la misma noche a 12 h, de otros sensores y gránulos (VIIRS 375 y 750, el otro MODIS), con lo
   que publica nuestro K (data/ del main congelado);
2. lo que dijo MIROVA a 12 h y en las noches vecinas, en todos los canales (referencia congelada del MANIFIESTO);
3. el píxel mismo en su recorte nativo: exceso de MIR (B22) sobre TIR (B31) contra el anillo de 5 a 25 km y contra sus
   vecinos, detector del barrido (costura si es 0 o 9) y TIR fría (nube).
Las dos preguntas del instrumento: (1) si hubiera calor en el cráter esa noche, ¿se vería? Sí: VIIRS 375 tiene un píxel
siete veces menor y la noche de Láscar muestra que lo ve; (2) si el recorte estuviera mal georreferenciado, el píxel del
cráter caería lejos del cráter: se imprime su distancia (MxD03).

Uso (desde el worktree de main congelado D:/vrp-trabajo/s162-mxd03, que trae pipeline/, scripts/ y data/):
    python -I diagnostico_dos_publicaciones.py --raiz D:/vrp-trabajo/s162-mxd03
        --art C:/vrp-trabajo/temporales/s162_negmodis/run_40120713181 --ref D:/vrp-trabajo/temporales/s162_mxd03/ref
"""
import argparse
import collections
import glob
import io
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

CASOS = ((1251, "Lascar", "2026-05-11 07:55"), (1120, "Llaima", "2026-07-24 01:05"))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", required=True)
    ap.add_argument("--art", required=True)
    ap.add_argument("--ref", required=True)
    a = ap.parse_args()
    raiz = Path(a.raiz)
    sys.path.insert(0, str(raiz))
    sys.path.insert(0, str(raiz / "scripts"))
    import yaml
    from pipeline import process_modis as pm
    from pipeline.geo_utils import get_detection_anchor
    from referencia_mirova_unificada import cargar_referencia_unificada
    filas = cargar_referencia_unificada(Path(a.ref) / "registro_vrp_consolidado.csv", Path(a.ref) / "registro_vrp_ocr.csv")
    vols = {v["name"]: v for v in yaml.safe_load(open(raiz / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}

    def es(f, vol):
        return str(f["volcano"]).replace(" ", "").replace("-", "").lower() == vol.lower()

    for i, vol, hh in CASOS:
        t = datetime.strptime(hh, "%Y-%m-%d %H:%M")
        print(f"\n===== {vol} {hh} (id {i})")
        recs = json.load(open(raiz / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
        print("1. otras pasadas a 12 h (nuestro K, data/ del main congelado):")
        for r in recs:
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
            if abs((dt - t).total_seconds()) <= 12 * 3600:
                pc = r.get("primary_cluster") or {}
                print(f"   {r['datetime_utc']} {r['sensor']:<18} dc {str(r.get('distance_class')):<7} pc_vrp "
                      f"{pc.get('vrp_mw')} pc_dist {pc.get('centroid_dist_km')} cenit {r.get('sensor_zenith_deg')}")
        print("2. MIROVA a 12 h (todos los canales):")
        for f in filas:
            if not es(f, vol):
                continue
            try:
                dt = datetime.strptime(str(f["fecha_utc"])[:16], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if abs((dt - t).total_seconds()) <= 12 * 3600:
                print(f"   {str(f['fecha_utc'])[:16]} {f['sensor_bucket']:<9} {f['tipo']:<24} vrp {f['vrp_mw']} "
                      f"dist {f['dist_km']} {f['source']}")
        print("   noches vecinas (+-5): pasadas con cumulo summit nuestro por sensor | alertas de MIROVA")
        for k in range(-5, 6):
            d = (t + timedelta(days=k)).strftime("%Y-%m-%d")
            s = collections.Counter(r["sensor"] for r in recs if r["datetime_utc"][:10] == d
                                    and r.get("distance_class") == "summit")
            al = [(str(f["fecha_utc"])[11:16], f["sensor_bucket"], f["vrp_mw"]) for f in filas
                  if es(f, vol) and str(f["fecha_utc"])[:10] == d and "ALERTA" in str(f["tipo"])]
            print(f"   {d} summit {sum(s.values())} {dict(s)} | MIROVA {len(al)} {al[:4]}")
        print("3. el pixel en el recorte nativo:")
        z = np.load(glob.glob(str(Path(a.art) / "*" / f"nativo_{i:04d}.npz"))[0])
        vent = get_detection_anchor(vols[vol])
        lat, lon = z["lat_mxd03"], z["lon_mxd03"]
        dist = np.hypot((lat - vent[0]) * 111.32, (lon - vent[1]) * 111.32 * math.cos(math.radians(vent[0])))
        bm = pm.radiance_to_bt(pm.merge_mir_bands(z["b21"], z["b22"], True), pm.BAND22_LAMBDA)
        bt = pm.radiance_to_bt(z["b31"], pm.BAND31_LAMBDA)
        exc = bm - bt
        k = np.unravel_index(np.nanargmax(np.where(dist < 6, exc, -99)), exc.shape)
        anillo = (dist >= 5) & (dist <= 25)
        r, c = k
        vec = exc[max(r - 1, 0):r + 2, max(c - 1, 0):c + 2].copy()
        vec[min(r, 1), min(c, 1)] = np.nan
        tw = bt[max(r - 2, 0):r + 3, max(c - 2, 0):c + 3]
        print(f"   pixel de mayor exceso MIR-TIR a menos de 6 km: a {dist[k]:.2f} km del crater, linea {int(z['linea'][k])} "
              f"(detector {int(z['linea'][k]) % 10}; costura si 0 o 9), cenit {float(z['sensor_zenith'][k]):.1f}")
        print(f"   BT MIR {bm[k]:.2f} K, TIR {bt[k]:.2f} K, exceso {exc[k]:.2f} K | vecinos 3x3: max {np.nanmax(vec):.2f} K")
        print(f"   anillo 5-25 km: exceso mediano {np.nanmedian(exc[anillo]):.2f} K, p99 {np.nanpercentile(exc[anillo], 99):.2f} K;"
              f" TIR mediana {np.nanmedian(bt[anillo]):.2f} K; fraccion TIR < 240 K {np.mean(bt[anillo] < 240):.3f}")
        print(f"   rango de TIR en el 5x5 alrededor: {np.nanmax(tw) - np.nanmin(tw):.1f} K")
        print("   exceso MIR-TIR 5x5 (filas = lineas):")
        print("   " + np.array2string(np.round(exc[max(r - 2, 0):r + 3, max(c - 2, 0):c + 3], 1)).replace("\n", "\n   "))


if __name__ == "__main__":
    main()
