# -*- coding: utf-8 -*-
"""V3 (verificador G, item 1) - la firma aritmetica del ruido en los records reales.

LA PREDICCION. Bajo ruido puro (sin ninguna fuente caliente), la mitad de los pixeles del disco
queda por encima de la mediana del anillo, POR DEFINICION de mediana. Entonces:
    n_contributing  ~=  n_roi / 2
    delta_L         ~=  n_roi * sigma * E[max(0,Z)]  =  0.3989 * n_roi * sigma   (Z normal)
    k_observed      =   delta_L / (sigma * sqrt(n_roi))  ~=  0.3989 * sqrt(n_roi)
                    ~=  0.3989 * sqrt(2 * n_contributing)
La ultima igualdad no tiene ningun parametro libre: no depende de sigma, ni del volcan, ni de la
banda, ni de si hay lava. Si los records reales caen sobre esa curva, el estadistico esta midiendo
el tamano del disco y no el calor.

(1) Si lo que mide estuviera roto, ¿fallaria?
    Si el Test 1 estuviera dominado por calor real y no por el piso de ruido, la razon
    k_observed / (0.3989*sqrt(2*n_contributing)) seria >> 1 y dispersa. Vale 1 solo si el
    campo es ruido. El script imprime la razon, no un si/no.
(2) Si el instrumento estuviera muerto, ¿se veria distinto?
    Si: el CONTROL usa las pasadas con la magnitud publicada mas alta (decil superior de
    primary_cluster.vrp_mw), donde SI hay un foco fuerte. Ahi la razon DEBE despegarse de 1.
    Si diera 1 tambien ahi, la relacion seria una identidad algebraica del codigo y no un
    hallazgo, y habria que descartar todo este script.

Semilla no aplica (no hay sorteo). Ventana 2026-09-01 en adelante.
"""
import io
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "mirova_equivalent"
OUT = Path(__file__).with_suffix(".json")
INICIO = "2026-09-01"
PHI0 = 0.3989422804014327  # E[max(0,Z)] para Z normal estandar


def bucket(s):
    s = s or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def med(xs):
    s = sorted(xs)
    return s[len(s) // 2] if s else None


def main():
    filas = []
    for f in sorted(DATA.glob("*.json")):
        d = json.load(open(f, encoding="utf-8"))
        for r in d.get("records", []):
            if r.get("datetime_utc", "") < INICIO:
                continue
            b = bucket(r.get("sensor"))
            if b is None or not r.get("triggered_test1"):
                continue
            n = r.get("n_test1_pixels")
            k = r.get("test1_k_observed")
            if not n or k is None or n <= 0:
                continue
            pc = (r.get("primary_cluster") or {}).get("vrp_mw")
            filas.append({"vol": f.stem, "b": b, "n": n, "k": k,
                          "pred": PHI0 * math.sqrt(2.0 * n),
                          "razon": k / (PHI0 * math.sqrt(2.0 * n)),
                          "pc_vrp": pc if pc is not None else 0.0})

    out = {"ventana_desde": INICIO, "n_filas": len(filas), "por_sensor": {}, "control_decil_alto": {}}
    por_b = defaultdict(list)
    for r in filas:
        por_b[r["b"]].append(r)
    for b, lista in sorted(por_b.items()):
        rz = [r["razon"] for r in lista]
        s = sorted(rz)
        out["por_sensor"][b] = {
            "n": len(lista),
            "razon_mediana": med(rz), "razon_p10": s[len(s) // 10], "razon_p90": s[9 * len(s) // 10],
            "k_mediana": med([r["k"] for r in lista]),
            "k_predicho_mediana": med([r["pred"] for r in lista]),
            "n_contrib_mediana": med([r["n"] for r in lista]),
        }
        # CONTROL: decil superior de magnitud publicada -> foco real, la razon debe despegarse
        alto = sorted(lista, key=lambda r: r["pc_vrp"])[int(0.9 * len(lista)):]
        bajo = sorted(lista, key=lambda r: r["pc_vrp"])[:int(0.5 * len(lista))]
        out["control_decil_alto"][b] = {
            "n_alto": len(alto), "razon_mediana_decil_alto": med([r["razon"] for r in alto]),
            "pc_vrp_mediana_decil_alto": med([r["pc_vrp"] for r in alto]),
            "n_bajo": len(bajo), "razon_mediana_mitad_baja": med([r["razon"] for r in bajo]),
            "pc_vrp_mediana_mitad_baja": med([r["pc_vrp"] for r in bajo]),
        }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"records con Test 1 disparado desde {INICIO}: {out['n_filas']}\n")
    print(f"{'sensor':10s} {'n':>5s} {'n_contrib':>9s} {'k_obs':>7s} {'k_pred':>7s} "
          f"{'razon':>7s} {'p10':>6s} {'p90':>6s}")
    for b, d in out["por_sensor"].items():
        print(f"{b:10s} {d['n']:5d} {d['n_contrib_mediana']:9d} {d['k_mediana']:7.3f} "
              f"{d['k_predicho_mediana']:7.3f} {d['razon_mediana']:7.3f} "
              f"{d['razon_p10']:6.3f} {d['razon_p90']:6.3f}")
    print("\nCONTROL (decil superior de magnitud publicada vs mitad baja):")
    for b, d in out["control_decil_alto"].items():
        print(f"  {b:10s} razon alto={d['razon_mediana_decil_alto']:.3f} "
              f"(VRP med {d['pc_vrp_mediana_decil_alto']:.3f})   "
              f"razon bajo={d['razon_mediana_mitad_baja']:.3f} "
              f"(VRP med {d['pc_vrp_mediana_mitad_baja']:.3f})")
    print("\nJSON:", OUT)


if __name__ == "__main__":
    main()
