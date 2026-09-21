"""S148 - de donde pudo salir el "43 de 135 positivos fuera de la caja" del pre-registro de la caja.

El pre-registro (experiments/_s147_ab_conectiva/PREREGISTRO_CAJA.md, seccion 2) da, sobre el brazo
sin Test 1 del run 35521542153: VIIRS 375 43 de 135 y 63 de 105; VIIRS 750 9 de 13 y 23 de 36;
MODIS 0 de 1 y 30 de 39. No hay script en el repo que lo produzca. Esto prueba definiciones
candidatas de "fuera" sobre esos mismos datos y dice cual reproduce los seis numeros.

Datos: los JSON del brazo _s146_ab_sin_test1 de la rama origin/s146-ab/35521542153, extraidos con
git show a un directorio temporal que se pasa como argumento (no estan en main).
Uso: PYTHONIOENCODING=utf-8 python experiments/_s148_caja_traza/origen_43_de_135.py <dir_con_los_json>
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "_s148_caja"))
import lectura_caja as lc  # noqa: E402

bp = lc.bp
DIR = Path(sys.argv[1])
V = ("2026-09-01", "2026-09-20")


def caja(lat, lon, c, half=2.5):
    if lat is None or lon is None or c is None or c[0] is None:
        return None
    return lc.en_caja(lat, lon, c) if half == 2.5 else None


def main():
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = lc.cargar_referencia_unificada(lc.CONGELADO / "registro_vrp_consolidado.csv",
                                           lc.CONGELADO / "registro_vrp_ocr.csv")
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, V)
    anc = lc.anclas()
    recs = lc.cargar_brazo(DIR, coords, inner, V)
    bp.etiquetar(recs, por_vb, ns, nv)
    crudo = {}
    for vol in bp.VOLS:
        for r in json.load(open(DIR / f"{vol}.json", encoding="utf-8"))["records"]:
            crudo[(vol, r.get("granule"))] = r

    defs = {
        "centroide del cumulo, caja desde el ancla de deteccion (= lectura_caja.py)":
            lambda r, x: not lc.en_caja(r["pc_lat"], r["pc_lon"], anc[r["vol"]]),
        "centroide del cumulo, caja desde la coordenada del volcan":
            lambda r, x: not lc.en_caja(r["pc_lat"], r["pc_lon"], coords[r["vol"]]),
        "centroid_dist_km > 2,5 (radio, no caja)":
            lambda r, x: r["pc_dist"] > 2.5,
        "centroid_dist_km > 2,5*raiz(2) = 3,54 (esquina de la caja)":
            lambda r, x: r["pc_dist"] > 2.5 * math.sqrt(2),
        "final_hotspot, caja desde el ancla":
            lambda r, x: not lc.en_caja(x["final_hotspot_lat"], x["final_hotspot_lon"], anc[r["vol"]]),
        "final_hotspot_dist_km > 2,5":
            lambda r, x: x["final_hotspot_dist_km"] > 2.5,
        "hotspot (pixel mas caliente de la escena), caja desde el ancla":
            lambda r, x: not lc.en_caja(x["hotspot_lat"], x["hotspot_lon"], anc[r["vol"]]),
        "hotspot_dist_km > 2,5":
            lambda r, x: x["hotspot_dist_km"] > 2.5,
        "ALGUN anomaly_pixel fuera de la caja (ancla)":
            lambda r, x: any(not lc.en_caja(q["lat"], q["lon"], anc[r["vol"]]) for q in x.get("anomaly_pixels") or []),
        "diag_t_max_dist_km > 2,5":
            lambda r, x: x["diag_t_max_dist_km"] > 2.5,
    }
    print("objetivo del pre-registro: V375 43/135 y 63/105 | V750 9/13 y 23/36 | MODIS 0/1 y 30/39\n")
    for nombre, f in defs.items():
        out = []
        for b in ("VIIRS375", "VIIRS750", "MODIS"):
            for lab in ("pos", "neg_limpio"):
                n = k = err = 0
                for r in recs:
                    if r["b"] != b or r["lab"] != lab or not r["pub"]:
                        continue
                    n += 1
                    try:
                        k += int(bool(f(r, crudo[(r["vol"], r["granule"])])))
                    except (TypeError, KeyError):
                        err += 1
                out.append(f"{k}/{n}" + (f"(sin dato {err})" if err else ""))
        print(f"{nombre:75} V375 {out[0]:>8} {out[1]:>8} | V750 {out[2]:>6} {out[3]:>6} | MODIS {out[4]:>5} {out[5]:>6}")


if __name__ == "__main__":
    main()
