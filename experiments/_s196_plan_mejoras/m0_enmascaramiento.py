# -*- coding: utf-8 -*-
"""Medición previa del ítem P0 del plan S196: ¿una anomalía conocida grande sube el umbral y esconde focos chicos?

POR QUÉ. El detector de la vía (el `.m` de MIROVA, `pipeline/mirova_v750_codigo.py::_pasada_contextual`) compara el
contraste de cada celda con max(mu + s·sd, piso), y mu y sd salen de TODA la grilla de 50 km. Un lacolito o un lago de
lava activo, con su halo de celdas tibias, agranda sd; si mu + s·sd pasa sobre el piso, el umbral sube en todo el
edificio y un foco nuevo y débil en otro flanco queda bajo él. El segundo pase saca del fondo los alertados del primero,
pero no el halo tibio que no alertó. El tablero no lo muestra: publica una posición (la del cúmulo más radiante).

Qué hace, sin reprocesar: cada record nocturno de la vía guarda en `diag_codigo_mirova` mu, sd y los cuatro umbrales de
cada pase. Para los 11 Tier A, de 2026-03-01 a 2026-11-22 y por familia de sensor, agrupa los records por la potencia
de la escena (`vrp_mw`, que es la suma de todos los alertados) y da la mediana de los umbrales del SEGUNDO pase (el que
decide si un foco chico se suma), la fracción de records en que mu + s·sd supera al piso (el umbral ya no es el piso
fijo: lo pone la escena) y cuántas veces el piso queda superado. Un umbral que sube con la potencia de la escena es la
firma del enmascaramiento; uno plano, su ausencia a ese nivel de potencia.

Uso: python experiments/_s196_plan_mejoras/m0_enmascaramiento.py
"""
import collections
import json
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp  # noqa: E402

DESDE, HASTA = "2026-03-01", "2026-11-22"
TRAMOS = [(0.0, 0.0, "0 MW"), (0.0, 1.0, "(0, 1]"), (1.0, 10.0, "(1, 10]"), (10.0, 100.0, "(10, 100]"),
          (100.0, 1e12, "> 100")]
PISOS = {"u_nti2": 0.003, "u_eti2": 0.003, "u_nti1": 0.02, "u_eti1": 0.01}   # noche, .m l. 177-199


def tramo(v):
    if v <= 0:
        return "0 MW"
    for a, b, n in TRAMOS[1:]:
        if a < v <= b:
            return n
    return None


def pases(diag):
    for v in diag.values():
        if isinstance(v, dict) and "pasada2" in v:
            return v
    return None


def main():
    filas = collections.defaultdict(list)
    vols = collections.defaultdict(lambda: collections.defaultdict(list))
    for vol in bp.VOLS:
        for r in json.loads((bp.DATA / ("%s.json" % vol)).read_text(encoding="utf-8"))["records"]:
            if not r.get("via_codigo_mirova") or not (DESDE <= r.get("datetime_utc", "")[:10] <= HASTA):
                continue
            d = r.get("diag_codigo_mirova") or {}
            if d.get("dayflag") != 0:
                continue
            p = pases(d)
            if not p:
                continue
            p2 = p["pasada2"]
            if any(p2.get(k) is None for k in PISOS):
                continue
            t = tramo(r.get("vrp_mw") or 0.0)
            fam = bp.bucket(r.get("sensor"))
            filas[(fam, t)].append(p2)
            vols[vol][t].append(p2)
    print("records nocturnos de la vía, 11 Tier A, %s a %s; umbrales del SEGUNDO pase (diag_codigo_mirova)" % (DESDE, HASTA))
    print("piso de noche: u_nti2 y u_eti2 0,003 (región sensible); u_nti1 0,02 y u_eti1 0,01 (conservadora y zona 0)\n")
    print("%-9s %-10s %6s %10s %10s %10s %10s %8s %8s" % ("familia", "VRP escena", "n", "u_nti2", "u_eti2", "u_nti1",
                                                          "u_eti1", "%nti2>p", "%nti1>p"))
    for fam in bp.BUCKETS:
        for _, _, t in TRAMOS:
            L = filas.get((fam, t), [])
            if not L:
                continue
            med = {k: statistics.median(x[k] for x in L) for k in PISOS}
            f2 = 100.0 * sum(1 for x in L if x["u_nti2"] > PISOS["u_nti2"] * 1.0001) / len(L)
            f1 = 100.0 * sum(1 for x in L if x["u_nti1"] > PISOS["u_nti1"] * 1.0001) / len(L)
            print("%-9s %-10s %6d %10.5f %10.5f %10.5f %10.5f %7.0f%% %7.0f%%" % (
                fam, t, len(L), med["u_nti2"], med["u_eti2"], med["u_nti1"], med["u_eti1"], f2, f1))
    print("\nPor volcán, todas las familias: mediana de u_nti2 del segundo pase y su máximo, por tramo de VRP de la escena")
    for vol in bp.VOLS:
        partes = []
        for _, _, t in TRAMOS:
            L = vols[vol].get(t, [])
            if L:
                partes.append("%s: n %d, med %.4f, máx %.4f" % (t, len(L), statistics.median(x["u_nti2"] for x in L),
                                                               max(x["u_nti2"] for x in L)))
        print("  %-20s %s" % (vol, " | ".join(partes)))


if __name__ == "__main__":
    main()
