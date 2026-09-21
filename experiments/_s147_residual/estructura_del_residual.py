"""S147 - DONDE vive el residual de sobre-publicacion, y como se comporta MIROVA en ese mismo lugar.

Complementa a `diseccion.py`. Aquel compara variable por variable; este estratifica la TASA de
publicacion en negativos limpios por las dos variables que resultaron separar (zona del barrido y
temperatura del fondo), las cruza, descarta la cuantizacion de MIROVA como explicacion, y le
pregunta a los propios datos de MIROVA (archivo OSF) como se reparte SU deteccion a lo ancho del
barrido.

LA FISICA DE LA ZONA DEL BARRIDO. VIIRS banda I agrega muestras a bordo: tres por pixel cerca del
nadir (hasta ~31,6 grados de angulo de barrido), dos en la zona media (hasta ~44,7) y ninguna en el
borde. Un pixel de una sola muestra es raiz(3) = 1,73 veces mas ruidoso que uno de tres. En angulo
cenital medido en el suelo esos cortes caen cerca de 36 y 52 grados. Con un umbral FIJO, mas ruido
por pixel significa mas cruces espurios; con un umbral que escala con la dispersion de la escena,
no. Esa es la diferencia entre las dos lecturas de la conectiva de Coppola 2016a p. 7.

LAS DOS PREGUNTAS DEL INSTRUMENTO:
1. Si la tasa no dependiera de la zona ni del fondo, esto lo mostraria? SI: las filas saldrian
   iguales. De hecho en el brazo de CONTROL salen casi iguales (80 a 92 %), porque el Test 1
   integrado satura todo; la estructura solo aparece al quitarlo, y el script imprime los dos.
2. Si el instrumento estuviera muerto? Los totales tienen que cuadrar con el evaluador del A/B:
   366 negativos limpios y 105 publicadas en VIIRS 375 del brazo sin Test 1.

LIMITES DECLARADOS:
- Ventana 2026-09-01 a 2026-09-20, 20 dias, entera posterior a #535 (A104).
- `t_bg < 260 K` mezcla NUBE con ALTITUD (A68): Tupungatito tiene fondo mediano de 247 K y
  Lastarria de 256 K por altura, no por cirrus. Se usa como estrato descriptivo, no como mascara.
- Los cortes de 36 y 52 grados son la traduccion aproximada a cenital de los cortes de agregacion
  por angulo de barrido: SOSPECHA hasta cotejar con el User Guide de VIIRS L1B.
- La eficiencia de MIROVA por zona compara el reparto de SUS detecciones (OSF 2013 a 2025, que es
  un producto FILTRADO, A105) contra el reparto de NUESTRAS pasadas (2025 a 2026). Sirve para la
  forma de la curva, no como tasa absoluta.

Uso: python experiments/_s147_residual/estructura_del_residual.py
"""
from __future__ import annotations
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for _p in (str(ROOT), str(ROOT / "scripts"), str(ROOT / "experiments" / "_s146_ab_sin_test1")):
    sys.path.insert(0, _p)

import banco_paridad as bp  # noqa: E402
from evaluar import cargar_brazo, clave  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

DATOS = (ROOT / "experiments" / "_s147_residual" / "_datos" / "experiments"
         / "_s146_ab_sin_test1" / "salidas" / "35521542153")
CONGELADO = ROOT / "experiments" / "_s146_ab_sin_test1" / "_congelado"
VENTANA = ("2026-09-01", "2026-09-20")
ZONAS = ("1 nadir <36", "2 medio 36-52", "3 borde >52")
FONDOS = ("<260 K", "260-270", ">270 K")


def zona(z):
    return ZONAS[0] if z < 36 else (ZONAS[1] if z < 52 else ZONAS[2])


def fondo(t):
    return FONDOS[0] if t < 260 else (FONDOS[1] if t < 270 else FONDOS[2])


def cargar(brazo, por_vb, ns, nv, coords, inner):
    recs = cargar_brazo(DATOS / brazo, coords, inner, VENTANA)
    bp.etiquetar(recs, por_vb, ns, nv)
    raw = {}
    for vol in bp.VOLS:
        for r in json.loads((DATOS / brazo / f"{vol}.json").read_text(encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor"))
            if b:
                raw[(vol, b, r.get("datetime_utc"))] = r
    return [(r, raw[clave(r)]) for r in recs if clave(r) in raw]


def tasa(sel):
    return f"{100 * sum(r['pub'] for r in sel) / len(sel):5.1f}% ({sum(r['pub'] for r in sel)}/{len(sel)})" if sel else "n/a"


def main():
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(CONGELADO / "registro_vrp_consolidado.csv",
                                        CONGELADO / "registro_vrp_ocr.csv")
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, VENTANA)

    for brazo, nombre in (("_s146_ab_control", "CONTROL (produccion)"),
                          ("_s146_ab_sin_test1", "SIN TEST 1")):
        d = [(r, x) for r, x in cargar(brazo, por_vb, ns, nv, coords, inner)
             if r["b"] == "VIIRS375" and x.get("sensor_zenith_deg") is not None
             and x.get("t_bg_k") is not None]
        print(f"\n=== {nombre} | VIIRS 375 | ventana {VENTANA[0]} a {VENTANA[1]} ===")
        print(f"{'estrato':18} {'publica en NEGATIVOS limpios':>30} {'recall en POSITIVOS':>24}")
        for z in ZONAS:
            print(f"{z:18} {tasa([r for r, x in d if zona(x['sensor_zenith_deg']) == z and r['lab'] == 'neg_limpio']):>30} "
                  f"{tasa([r for r, x in d if zona(x['sensor_zenith_deg']) == z and r['lab'] == 'pos']):>24}")
        for t in FONDOS:
            print(f"fondo {t:12} {tasa([r for r, x in d if fondo(x['t_bg_k']) == t and r['lab'] == 'neg_limpio']):>30} "
                  f"{tasa([r for r, x in d if fondo(x['t_bg_k']) == t and r['lab'] == 'pos']):>24}")
        if brazo.endswith("sin_test1"):
            print("\n  cruce, solo negativos limpios:")
            print(f"  {'':16}" + "".join(f"{t:>22}" for t in FONDOS))
            for z in ZONAS:
                print(f"  {z:16}" + "".join(
                    f"{tasa([r for r, x in d if zona(x['sensor_zenith_deg']) == z and fondo(x['t_bg_k']) == t and r['lab'] == 'neg_limpio']):>22}"
                    for t in FONDOS))
            print("\n  MIROVA procesa el borde? (pasadas nuestras con alguna fila de MIROVA a +-2 min)")
            for z in ZONAS:
                sel = [r for r, x in d if zona(x["sensor_zenith_deg"]) == z]
                lis = [r for r in sel if bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])]
                print(f"    {z:16} {len(lis):4} de {len(sel):4} = {100 * len(lis) / len(sel):5.1f}%")

    # La cuantizacion de MIROVA, descartada como explicacion.
    ref = pd.read_csv(ROOT / "experiments" / "_s145_paridad" / "_dl_referencia" / "registro_vrp_consolidado.csv") \
        if (ROOT / "experiments" / "_s145_paridad" / "_dl_referencia" / "registro_vrp_consolidado.csv").exists() \
        else pd.read_csv(CONGELADO / "registro_vrp_consolidado.csv")
    pos = ref[ref.VRP_MW > 0]
    print("\n=== MIROVA cuantiza el VRP que publica ===")
    print("  valores positivos mas bajos:", sorted(pos.VRP_MW.unique())[:6])
    for s, g in pos.groupby("Sensor"):
        print(f"  {s:10} n={len(g):5}  minimo {g.VRP_MW.min():.2f}  p05 {g.VRP_MW.quantile(.05):.2f}  mediana {g.VRP_MW.median():.2f}")

    # Como se reparte la deteccion de MIROVA a lo ancho del barrido, con sus propios datos.
    osf_p = ROOT / "data" / "mirova_reference" / "VRP_GLOBAL_ARCHIVE_2025.csv"
    if osf_p.exists():
        osf = pd.read_csv(osf_p, low_memory=False)
        v = osf[(osf.Resolution == 375) & (osf.Dayflag == 0) & (osf.Volc_LAT < -17) & (osf.Volc_LAT > -56)
                & (osf.Volc_LON < -66) & (osf.Volc_LON > -76)].copy()
        v["zona"] = v.SatZen.apply(zona)
        pas = Counter()
        for f in (ROOT / "data" / "mirova_equivalent").glob("*.json"):
            d = json.loads(f.read_text(encoding="utf-8"))
            for r in (d["records"] if isinstance(d, dict) else d):
                s = str(r.get("sensor", ""))
                if s.startswith("VIIRS") and not s.endswith("_750") and r.get("sensor_zenith_deg") is not None:
                    pas[zona(r["sensor_zenith_deg"])] += 1
        tp = sum(pas.values())
        print(f"\n=== eficiencia de MIROVA por zona (OSF, volcanes de Chile, n={len(v)}; pasadas nuestras n={tp}) ===")
        print(f"  {'zona':16} {'% pasadas':>10} {'% detecciones MIROVA':>22} {'eficiencia':>11}")
        for z in ZONAS:
            a, b = 100 * pas[z] / tp, 100 * (v.zona == z).mean()
            print(f"  {z:16} {a:9.1f}% {b:21.1f}% {b / a:11.2f}")


if __name__ == "__main__":
    main()
