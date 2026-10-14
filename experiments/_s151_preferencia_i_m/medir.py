# -*- coding: utf-8 -*-
"""Tarea 1.9 del loop: ¿el NRT de MIROVA prefiere la banda M (750 m) sobre la I (375 m) cuando coinciden?

POR QUE. Coppola et al. 2026 (Scientific Data, p. idx 6) dice que en el archivo OSF, cuando una deteccion
VIIRS de 375 m y una de 750 m coinciden, se conserva la de 750 m (F-07, docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md).
Si el canal NRT, que es el que clonamos, hiciera lo mismo, publicar las dos bandas en paralelo seria
sobre-publicacion y una regla de preferencia la bajaria sin tocar umbrales. A105 advierte que el archivo
no es el NRT. Esto lo mide en la tabla latest.php (consolidado de la referencia unificada).

Control: las parejas I/M de una misma pasada salen del mismo granulo y deben tener la misma hora al segundo;
si no la tuvieran, la clave al minuto estaria juntando pasadas distintas.
"""
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402


def main():
    ref = [f for f in cargar_referencia_unificada()
           if f["sensor_bucket"] in ("VIIRS375", "VIIRS750") and f["source"] == "CONS"]
    por = defaultdict(dict)
    for f in ref:
        por[(f["volcano"], f["fecha_utc"][:16])][f["sensor_bucket"]] = f
    bandas = Counter(tuple(sorted(v)) for v in por.values())
    ambas = [v for v in por.values() if len(v) == 2]
    mismo_segundo = sum(v["VIIRS375"]["fecha_utc"] == v["VIIRS750"]["fecha_utc"] for v in ambas)
    alerta = lambda f: f["tipo"] == "ALERTA_TERMICA"  # noqa: E731
    print("pasadas VIIRS de la tabla por bandas presentes:", dict(bandas))
    print(f"con las dos bandas: {len(ambas)}; control, misma hora al segundo: {mismo_segundo} ({100 * mismo_segundo / len(ambas):.1f} %)")
    print("alerta en las dos:", sum(alerta(v["VIIRS375"]) and alerta(v["VIIRS750"]) for v in ambas),
          "| solo 375:", sum(alerta(v["VIIRS375"]) and not alerta(v["VIIRS750"]) for v in ambas),
          "| solo 750:", sum(alerta(v["VIIRS750"]) and not alerta(v["VIIRS375"]) for v in ambas))
    print("pasadas con las dos bandas por mes:",
          dict(sorted(Counter(k[1][:7] for k, v in por.items() if len(v) == 2).items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
