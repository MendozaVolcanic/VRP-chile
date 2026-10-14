# -*- coding: utf-8 -*-
"""Tarea 1.10 del loop: `max` en VIIRS 750 contra el criterio de victoria (suma de errores).

POR QUE. El criterio de Nicolas (2026-10-13; tasks/LOOP_OBJETIVOS.md §1.2) veta todo cambio que pierda una
alerta protegida (VRP de la pasada >= 1 MW, docs/S151_CRITERIO_CLASE_MIROVA.md) y, por debajo, suma alertas
perdidas y publicaciones de mas con el mismo peso. VERIFICADOR_DATOS S150 D4 encontro que `max` (brazo F)
pierde en VIIRS 750 cuatro alertas que el brazo sin Test 1 (B) publicaba: 0,65, 0,41, 0,39 y 0,32 MW. Ninguna
llega a 1 MW, asi que no vetan; queda saber si la suma de errores mejora o empeora.

Fuente: las salidas del evaluador por mes (experiments/_s149_prereg_invierno/resultados/<mes>_VIIRS750.txt),
control = B, brazo = F (S150_RESULTADO_MESES.md §4). Los numeros se leen de esos archivos, no se transcriben.

Limite: el evaluador da el recall como "de lo que publica el control, cuanto conserva el brazo"; no cuenta
positivas que el brazo publique y el control no. Para la suma se supone 0 de esas (cota conservadora contra F:
si existieran, F tendria menos errores, no mas). Los negativos publicados salen del porcentaje redondeado a
una decima, asi que cada conteo tiene un error de +-1 pasada.
"""
import re
import sys
from pathlib import Path

RES = Path(__file__).resolve().parents[1] / "_s149_prereg_invierno" / "resultados"
MESES = ["abril", "mayo", "junio", "julio", "agosto"]
P1 = re.compile(r"^P1\. publicacion en negativos limpios \(n (\d+)\): control ([\d.]+) % \| brazo ([\d.]+) %")
P4 = re.compile(r"^\s+positivas (\d+) \| publica el control (\d+) \| de esas conserva el brazo (\d+) \|.*?perdidas con 0\.5 MW o mas: (\d+)")


def leer(mes):
    neg = pos = None
    for linea in (RES / f"{mes}_VIIRS750.txt").read_text(encoding="utf-8").splitlines():
        if neg is None and (m := P1.match(linea)):
            neg = (int(m[1]), float(m[2]), float(m[3]))
        elif pos is None and (m := P4.match(linea)):
            pos = tuple(int(x) for x in m.groups())
    if neg is None or pos is None:
        raise ValueError(f"{mes}: no encontre P1 o P4")
    return neg, pos


def main():
    tot = {"c": 0, "b": 0, "perd": 0}
    print("mes      | alertas sin publicar  | negativos publicados | suma de errores | perdidas >=0,5 MW")
    print("         | control  brazo        | control  brazo       | control  brazo  |")
    for mes in MESES:
        (n_neg, pc, pb), (n_pos, pub_c, cons_b, perd05) = leer(mes)
        miss_c, miss_b = n_pos - pub_c, n_pos - cons_b
        neg_c, neg_b = round(n_neg * pc / 100), round(n_neg * pb / 100)
        e_c, e_b = miss_c + neg_c, miss_b + neg_b
        tot["c"] += e_c; tot["b"] += e_b; tot["perd"] += pub_c - cons_b
        print(f"{mes:8s} | {miss_c:5d}  {miss_b:5d}         | {neg_c:5d}  {neg_b:5d}        | {e_c:5d}  {e_b:5d}   | {perd05}")
    print(f"total    | suma de errores: control {tot['c']}, brazo {tot['b']} | alertas que el brazo deja de publicar: {tot['perd']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
