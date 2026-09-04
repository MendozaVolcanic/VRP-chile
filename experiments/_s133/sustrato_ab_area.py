# -*- coding: utf-8 -*-
"""S133 - de que volcanes y de que ventana se puede juzgar el A/B del area.

FICHA SDA (Resolucion CPLT N.372)
================================
Rol            : medicion off-line del SUSTRATO del A/B. NO participa de la deteccion
                 NRT ni escribe en `data/mirova_equivalent/`. Read-only.
Entradas       : data/mirova_equivalent/<vol>.json (records persistidos)
                 ground truth MIROVA CONS union OCR (via experiments/_s126_lib).
Salida         : experiments/_s133/sustrato_ab_area.json - de ahi salen los numeros
                 que cita el workflow, y no de esta consola (regla S91).

POR QUE ESTE SCRIPT EXISTE
==========================
El criterio pre-registrado (docs/s132/AB_AREA_GEOLOCALIZADA.md) pide que el bin del
nadir y el de 50 grados o mas queden AMBOS en banda, y que al menos 6 de 8 volcanes
esten en banda. Eso obliga a elegir los ocho volcanes y la ventana con el DATO, no con
el gusto: un volcan que casi no tiene pasadas oblicuas no puede ni confirmar ni refutar
una correccion que actua justamente sobre pasadas oblicuas, y meterlo en la matriz
gasta CI sin informar nada. Es la leccion de S130: la pregunta previa a "mejora algo?"
es "llega a ejecutarse?".

QUE CUENTA COMO PAR (la definicion, DENTRO de la afirmacion - A90)
==================================================================
Par = un record NUESTRO de VIIRS375 con `primary_cluster.vrp_mw > 0` y
`sensor_zenith_deg` persistido, emparejado con una fila ALERTA de MIROVA del mismo
volcan y el mismo bucket de sensor cuya hora de satelite cae a <= 20 min. Es pareo POR
PASADA, no por noche: el maximo de la noche mezcla pasadas de angulos distintos, y por
eso inflaba el gradiente cenital (S131, correccion de la seccion 4).

VIIRS375 = sensor VIIRS_* SIN sufijo; el sufijo _750 es M-band (A48). El bucket lo
resuelve `_s126_lib.bucket`, que ya conoce esa convencion; no se inventa un regex.

USO
===
    python experiments/_s133/sustrato_ab_area.py
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import ALIAS, FUENTES_GT, SENSOR_MAP, bucket  # noqa: E402

SALIDA = os.path.join(HERE, "sustrato_ab_area.json")
TOL = timedelta(minutes=20)
# La ventana nocturna 03-09 UTC es la del loader canonico: el MIR solo se usa de noche
# porque de dia lo contamina el sol reflejado.
HORAS_NOCHE = (3, 9)
BINS = ("0-15", "15-25", "25-35", "35-50", "50+")
# Los dos bins EXTREMOS son los que el criterio juzga: el nadir y el borde del swath.
BINS_JUZGADOS = ("0-15", "50+")
# Piso de n por bin para llamar "evaluable" a un volcan. Es el MIN_N que S131 uso en
# `experiments/_s131_audit/magnitud/03_pares_por_pasada.py`; se hereda para no cambiar
# la vara a mitad de camino.
MIN_N_POR_BIN = 15

VENTANAS = [
    ("2026-01-01", "2026-12-31"),
    ("2026-03-01", "2026-08-31"),
    ("2026-04-01", "2026-08-31"),
    ("2026-05-01", "2026-08-31"),
    ("2026-06-01", "2026-08-31"),
]


def _parse_dt(s):
    """El pipeline persiste `datetime_utc` con y sin segundos. Las dos formas valen."""
    s = (s or "").replace("T", " ").strip()[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def _bin_de(zen):
    z = abs(float(zen))
    if z < 15:
        return "0-15"
    if z < 25:
        return "15-25"
    if z < 35:
        return "25-35"
    if z < 50:
        return "35-50"
    return "50+"


def cargar_gt(ventana):
    """{(vol, bucket): [datetime]} de las ALERTAS nocturnas de MIROVA en la ventana."""
    out = defaultdict(list)
    for fname in FUENTES_GT:
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            continue
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                nom = (r.get("Volcan") or "").strip()
                vol = next((v for v, al in ALIAS.items() if nom in al), None)
                if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                    continue
                bk = SENSOR_MAP.get((r.get("Sensor") or "").strip().upper())
                f = r.get("Fecha_Satelite_UTC") or ""
                if not bk or not (ventana[0] <= f[:10] <= ventana[1]):
                    continue
                try:
                    vrp = float(r.get("VRP_MW") or 0)
                    d = datetime.strptime(f[:19], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
                if vrp <= 0 or not (HORAS_NOCHE[0] <= d.hour <= HORAS_NOCHE[1]):
                    continue
                out[(vol, bk)].append(d)
    return out


def medir(ventana):
    gt = cargar_gt(ventana)
    por_vol = {}
    for vol in ALIAS:
        p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
        if not os.path.exists(p):
            continue
        cuenta = dict((b, 0) for b in BINS)
        n_v375 = n_sin_zenith = 0
        with io.open(p, encoding="utf-8") as fh:
            recs = json.load(fh)["records"]
        for r in recs:
            if bucket(r.get("sensor")) != "v375":
                continue
            fecha = (r.get("datetime_utc") or "")[:10]
            if not (ventana[0] <= fecha <= ventana[1]):
                continue
            n_v375 += 1
            pc = r.get("primary_cluster") or {}
            try:
                ours = float(pc.get("vrp_mw"))
            except (TypeError, ValueError):
                continue
            if not ours > 0:
                continue
            zen = r.get("sensor_zenith_deg")
            if zen is None:            # mascara explicita: sin angulo no hay bin
                n_sin_zenith += 1
                continue
            d = _parse_dt(r.get("datetime_utc"))
            if d is None:
                continue
            if not any(abs(g - d) <= TOL for g in gt.get((vol, "v375"), ())):
                continue
            cuenta[_bin_de(zen)] += 1
        evaluable = all(cuenta[b] >= MIN_N_POR_BIN for b in BINS_JUZGADOS)
        por_vol[vol] = {
            "n_records_v375_en_ventana": n_v375,
            "n_sin_sensor_zenith_deg": n_sin_zenith,
            "n_pares_por_pasada": sum(cuenta.values()),
            "pares_por_bin": cuenta,
            "n_bin_nadir_0_15": cuenta["0-15"],
            "n_bin_50_mas": cuenta["50+"],
            "evaluable_en_los_dos_bins": bool(evaluable),
        }
    orden = sorted(por_vol, key=lambda v: -min(por_vol[v]["n_bin_nadir_0_15"],
                                               por_vol[v]["n_bin_50_mas"]))
    return {
        "ventana_utc": list(ventana),
        "dias": (datetime.strptime(ventana[1], "%Y-%m-%d")
                 - datetime.strptime(ventana[0], "%Y-%m-%d")).days,
        "ranking_por_min_de_los_dos_bins": orden,
        "n_volcanes_evaluables": sum(
            1 for v in por_vol if por_vol[v]["evaluable_en_los_dos_bins"]),
        "por_volcan": por_vol,
    }


def main():
    out = {
        "_que_es": ("Sustrato del A/B del area geolocalizada (S133): de que volcanes y "
                    "de que ventana se puede juzgar el criterio pre-registrado de "
                    "docs/s132/AB_AREA_GEOLOCALIZADA.md."),
        "_definicion_de_par": (
            "record VIIRS375 nuestro con primary_cluster.vrp_mw>0 y sensor_zenith_deg "
            "persistido, emparejado con una ALERTA MIROVA del mismo bucket a <=20 min "
            "(pareo POR PASADA, no por noche)."),
        "_min_n_por_bin": MIN_N_POR_BIN,
        "_bins_que_juzga_el_criterio": list(BINS_JUZGADOS),
        "_advertencia_denominador": (
            "Se mide sobre los records del perfil OPERACIONAL, que es el mejor proxy "
            "disponible de lo que produciran los brazos. El A/B genera records nuevos: "
            "estos numeros dimensionan la muestra, no la sustituyen (A90)."),
        "ventanas": [medir(v) for v in VENTANAS],
    }
    with io.open(SALIDA, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=False))
    print("Escrito:", SALIDA)
    for w in out["ventanas"]:
        print("\nventana %s..%s (%d dias) - evaluables: %d"
              % (w["ventana_utc"][0], w["ventana_utc"][1], w["dias"],
                 w["n_volcanes_evaluables"]))
        for vol in w["ranking_por_min_de_los_dos_bins"]:
            d = w["por_volcan"][vol]
            print("  %-22s pares=%4d  nadir=%3d  50+=%3d  %s"
                  % (vol, d["n_pares_por_pasada"], d["n_bin_nadir_0_15"],
                     d["n_bin_50_mas"], "OK" if d["evaluable_en_los_dos_bins"] else "-"))
    print("\nLos numeros se citan del JSON, no de esta consola (S91).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
