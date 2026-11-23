# -*- coding: utf-8 -*-
"""Medición previa de MEJ-8 (plan S196): ¿sirve la bandera de alerta de NHI-v1 como vara en los dos volcanes con lago?

POR QUÉ. Las detecciones sobre agua se concentran en Laguna del Maule y Carrán-Los Venados (`experiments/_s193_lagos/
resumen.txt`: 33 y 20 pasadas con el pico sobre agua a 5 km o menos). La idea natural es preguntarle a SWIR si esas
noches había calor en la superficie. Pero SWIR de día sobre agua tiene su propio artefacto (reflejo del sol en el lago,
bordes de nube), y ninguno de los dos volcanes tiene un foco térmico superficial conocido en la RNVV. Si NHI alerta a
menudo en ellos, su bandera no puede decir «esto era agua y no volcán»: hay que mirar la escena. Este script sólo
cuenta lo que NHI dice, por sensor, a un commit fijo de NHI-v1.

Uso: python experiments/_s196_plan_mejoras/m8_nhi_en_lagos.py --commit <sha de NHI-v1> --dest <carpeta temporal>
"""
import argparse
import collections
import json
import statistics
import subprocess
import sys
import urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
CARPETAS = ["Laguna del Maule", "Carran - Los Venados"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", required=True)
    ap.add_argument("--dest", required=True)
    a = ap.parse_args()
    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    print("NHI-v1 commit %s" % a.commit)
    for nom in CARPETAS:
        ruta = "docs/nhi_data/%s/nhi_timeseries.json" % nom
        o = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                            "repos/MendozaVolcanic/NHI-v1/contents/%s?ref=%s" % (urllib.parse.quote(ruta), a.commit)],
                           capture_output=True, check=True)
        (dest / (nom.replace(" ", "_") + ".json")).write_bytes(o.stdout)
        serie = [e for e in json.loads(o.stdout.decode("utf-8")) if e.get("fecha")]
        print("\n%s: %d escenas, %s a %s" % (nom, len(serie), min(e["fecha"] for e in serie),
                                             max(e["fecha"] for e in serie)))
        por = collections.defaultdict(list)
        for e in serie:
            por[e.get("sensor")].append(e)
        for s, L in sorted(por.items()):
            al = [e for e in L if e.get("alerta") is True]
            pc = [e.get("pixeles_calientes") or 0 for e in al]
            nub = [e.get("cloud_cover") or 0 for e in al]
            print("  %-11s %3d escenas, %3d con alerta; píxeles calientes en las alertas: mediana %s, máx %s; "
                  "nubosidad mediana de las alertas %s" % (
                      s, len(L), len(al), statistics.median(pc) if pc else "-", max(pc) if pc else "-",
                      ("%.1f" % statistics.median(nub)) if nub else "-"))
        meses = collections.Counter(e["fecha"][:7] for e in serie if e.get("alerta") is True)
        print("  alertas por mes: %s" % dict(sorted(meses.items())))


if __name__ == "__main__":
    main()
