# -*- coding: utf-8 -*-
"""Tarea 1.7 del loop. Lo que la BASE DE MIROVA dice de la caja, antes de correr nada (A115: el umbral se le
pregunta a la referencia, no se inventa).

EL FENOMENO. Si MIROVA aplica el umbral permisivo solo en una caja de 5 x 5 km (Coppola 2016a p. 6; Coppola et
al. 2023 p. 3), sus alertas deberian concentrarse dentro de la caja: fuera de ella solo alerta lo que pasa el
umbral estricto, que es calor fuerte. Si en cambio las alertas de MIROVA se reparten por todo el circulo de
`inner_radius_km` como las nuestras, la caja no es lo que separa a MIROVA de la replica.

QUE MIDE. Para las alertas nocturnas de MIROVA (filas ALERTA del scraper), la distancia que publica
(`Distancia_km`) en tres tramos: hasta 2,5 km (dentro de la caja con cualquier acimut), de 2,5 a 3,54 km (depende
del acimut, que el CSV no trae, A93) y sobre 3,54 km (fuera de la caja con cualquier acimut). Y el VRP de cada
tramo: si la caja es real, lo de afuera deberia ser mas fuerte.

LIMITES DECLARADOS. (1) `Distancia_km` se mide desde el punto de referencia de MIROVA y esta cuantizada a su
grilla (D15): en Tupungatito, Puyehue Cordon Caulle y Planchon Peteroa ese punto esta a 4,78, 7,58 y 2,00 km del
crater (TIF, S147), asi que alli no dice donde cae la alerta respecto de una caja centrada en el crater; se
informan aparte. (2) Las alertas mas alla del limite del scraper (5 km, 7 en Tupungatito) no son ALERTA sino
FALSO_POSITIVO: este conteo no ve lo que MIROVA detecta lejos. (3) Las filas del OCR de Suomi NPP hasta el
2026-10-09 pueden traer la distancia de otra pasada (A119): se cuentan aparte.

CONTROL (puede fallar): la misma cuenta sobre los NEGATIVOS no tiene sentido (no traen distancia), asi que el
control es de instrumento: la distancia de las filas FALSO_POSITIVO tiene que estar, toda, sobre el limite del
scraper de su volcan, que es su inner_radius_km (si no, el tramo de distancias esta mal leido). La primera
version usaba 5 km para todos y el control FALLO en Planchon Peteroa (3,46 km) y Lastarria (3,77 km), cuyo
limite es 3 km: es el control funcionando sobre un supuesto mio, no sobre el dato.

Uso: python prediccion_mirova.py > prediccion_mirova_salida.txt
"""
from __future__ import annotations

import collections, statistics, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
for _p in (str(RAIZ), str(RAIZ / "scripts"), str(RAIZ / "experiments" / "_s146_ab_sin_test1")):
    sys.path.insert(0, _p)
import evaluar as ev  # noqa: E402
import clase_mirova as cm  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
bp = ev.bp

CONG_V1 = RAIZ / "experiments" / "_s151_prereg_fk_11" / "_congelado_v1"
OFFSET_CENTRO = {"Tupungatito", "PuyehueCordonCaulle", "PlanchonPeteroa"}   # S147, centro de grilla de MIROVA lejos del crater
SEMIDIAGONAL = 2.5 * 2 ** 0.5
# El limite del scraper es el inner_radius_km de cada volcan (el del KML de MIROVA, el mismo del tablero): 3 km en
# Lastarria y Planchon Peteroa, 4 en Copahue, 7 en Tupungatito, 20 en Puyehue Cordon Caulle, 5 en el resto.
LIMITE_SCRAPER = bp.inner_desde_html()


def tramo(d):
    if d is None:
        return "sin distancia"
    return "<=2,5" if d <= 2.5 else ("2,5-3,54" if d <= SEMIDIAGONAL else ">3,54")


def cuenta(filas, ventana, titulo):
    coords = bp._coords_por_volcan()
    por_vb, _, _, n = bp.indexar_referencia(filas, coords, ventana)
    alertas, fps = [], []
    for (vol, b), lista in por_vb.items():
        for dt, f in lista:
            if bp.es_alerta(f["tipo"]):
                alertas.append((vol, b, dt, f))
            elif bp.es_fp(f["tipo"]):
                fps.append((vol, b, dt, f))
    print("\n== %s: %s a %s | filas nocturnas %d | alertas %d | falsos positivos lejanos %d" % (titulo, ventana[0], ventana[1], n, len(alertas), len(fps)))
    # control: los FALSO_POSITIVO del scraper estan sobre su limite
    bajo = [(v, f["dist_km"]) for v, b, dt, f in fps if f["dist_km"] is not None and f["dist_km"] <= LIMITE_SCRAPER[v]]
    print("   control: FALSO_POSITIVO con distancia bajo el limite del scraper: %d de %d %s | %s" % (
        len(bajo), len(fps), bajo[:5], "OK" if not bajo else "REVISAR la lectura de distancias"))
    for grupo, sel in (("los 8 volcanes con el centro de MIROVA en el crater", lambda v: v not in OFFSET_CENTRO),
                       ("Tupungatito, Puyehue Cordon Caulle y Planchon Peteroa (centro corrido: no decide)", lambda v: v in OFFSET_CENTRO)):
        print("   -- %s" % grupo)
        for s in ("MODIS", "VIIRS375", "VIIRS750"):
            xs = [(v, f) for v, b, dt, f in alertas if b == s and sel(v)]
            snpp = [(v, f) for v, f in xs if f["source"] == "OCR"]
            c = collections.Counter(tramo(f["dist_km"]) for v, f in xs)
            vrp = {t: [f["vrp_mw"] for v, f in xs if tramo(f["dist_km"]) == t and f["vrp_mw"] is not None] for t in ("<=2,5", "2,5-3,54", ">3,54")}
            prot = collections.Counter(tramo(f["dist_km"]) for v, f in xs if cm.alerta_protegida(f, lectura="A"))
            print("      %-8s alertas %4d | <=2,5 km %4d | 2,5-3,54 %3d | >3,54 %3d | sin distancia %3d | de ellas del OCR %d | protegidas A por tramo %s" % (
                s, len(xs), c["<=2,5"], c["2,5-3,54"], c[">3,54"], c["sin distancia"], len(snpp), dict(prot)))
            print("               VRP mediano por tramo: %s" % " | ".join("%s %s (n %d)" % (t, ("%.3f MW" % statistics.median(v)) if v else "-", len(v)) for t, v in vrp.items()))
            porvol = collections.defaultdict(collections.Counter)
            for v, f in xs:
                porvol[v][tramo(f["dist_km"])] += 1
            print("               por volcan (<=2,5 / 2,5-3,54 / >3,54): %s" % ", ".join(
                "%s %d/%d/%d" % (v, x["<=2,5"], x["2,5-3,54"], x[">3,54"]) for v, x in sorted(porvol.items())))
    return alertas


def main():
    v1 = cargar_referencia_unificada(CONG_V1 / "registro_vrp_consolidado.csv", CONG_V1 / "registro_vrp_ocr.csv",
                                     historico_path=CONG_V1 / "consolidado_filas_perdidas.csv", respaldo_path=CONG_V1 / "respaldo_20260408.csv")
    cuenta(v1, ("2026-08-29", "2026-10-08"), "V1, referencia congelada del pre-registro de F y K (tabla y OCR)")
    union = cargar_referencia_unificada()
    tabla = [f for f in union if f["source"] == "CONS"]
    cuenta(tabla, ("2026-04-01", "2026-10-08"), "ABRIL A OCTUBRE, solo la tabla (sin OCR: la distancia del OCR no es confiable antes del 2026-06-13, A119)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
