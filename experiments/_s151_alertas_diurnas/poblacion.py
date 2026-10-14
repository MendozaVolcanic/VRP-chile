# -*- coding: utf-8 -*-
"""Tarea 1.13 (estudio C), pregunta 1: poblacion de alertas diurnas de MIROVA.

POR QUE. La replica procesa solo pasadas nocturnas (el Sol reflejado contamina el MIR de 3,7 a 4 um),
pero MIROVA publica alertas de dia. Con la lectura A del criterio de victoria (docs/MISSION.md) una
alerta de 1 MW o mas es protegida, y si cae de dia la perdemos por construccion sin que ningun
evaluador lo cuente. Este script mide cuantas son, con la MISMA regla que usa el pipeline:
`pipeline.store._solar_elevation` + `pipeline.store._reject_daytime` con el flag ENABLE_DAYTIME_MODIS
leido de `pipeline.profile` (perfil mirova_equivalent), igual que scripts/auto_audit_weekly.py.

Controles que pueden fallar (A110):
  C1. Reproducir el conteo de D27 (37 alertas de tabla entre 13 y 21 UTC, 19 de 1 MW o mas) sobre
      latest_consolidado.csv sin OCR. Si no da, el instrumento o el corte horario es otro.
  C2. Regla del pipeline sobre casos sinteticos con respuesta conocida: Lascar 05:00 UTC en junio debe
      ser noche (no rechazada) y Lascar 17:00 UTC en enero debe ser dia (rechazada) en los 3 sensores.
  C3. Concordancia entre la regla de elevacion solar y el corte horario 13-21 UTC: cuantas filas
      clasifica distinto cada uno (las de amanecer y atardecer).
Salida: poblacion_salida.txt y poblacion_filas.json (filas diurnas con su elevacion, para los demas scripts).
"""
from __future__ import annotations

import csv
import io
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import yaml  # noqa: E402

from pipeline import profile  # noqa: E402
from pipeline.store import _reject_daytime, _solar_elevation  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
from clase_mirova import alerta_protegida, clave_pasada, TIPOS_ALERTA  # noqa: E402
from pipeline.mirova_csv_loader import normalize_volcano_name  # noqa: E402

AQUI = Path(__file__).resolve().parent
BUCKET_SENSOR = {"MODIS": "MODIS_TERRA", "VIIRS375": "VIIRS_SNPP", "VIIRS750": "VIIRS_SNPP_750"}


def coords():
    with open(ROOT / "volcanoes.yaml", encoding="utf-8") as fh:
        return {v["name"]: (v["lat"], v["lon"]) for v in yaml.safe_load(fh)["volcanoes"] if "lat" in v}


def tramo_a119(fecha: str) -> str:
    """Tramos de A119 / scripts/calidad_referencia_mirova.py."""
    if fecha < "2026-03-01":
        return "T0 ene-feb (no se usa)"
    if fecha < "2026-06-13":
        return "T1 mar-12jun (decide la tabla)"
    return "T2 13jun-oct (tabla y OCR)"


def es_descartada(bucket, lat, lon, dt):
    elev = _solar_elevation(lat, lon, dt)
    return _reject_daytime(BUCKET_SENSOR[bucket], elev, profile.ENABLE_DAYTIME_MODIS), elev


def _texto_csv(commit=None):
    if commit is None:
        return (ROOT / "latest_consolidado.csv").read_text(encoding="utf-8")
    return subprocess.run(["git", "show", "%s:latest_consolidado.csv" % commit], cwd=ROOT,
                          capture_output=True, check=True).stdout.decode("utf-8")


def control_c1(commit=None):
    """D27: tabla sola (latest_consolidado.csv), ALERTA_TERMICA, hora UTC 13 a 21."""
    n_tot = n_13_21 = n_13_21_prot = 0
    det = Counter()
    hora_max = {}
    if True:
        for r in csv.DictReader(io.StringIO(_texto_csv(commit))):
            if (r.get("Tipo_Registro") or "").strip() != "ALERTA_TERMICA":
                continue
            if normalize_volcano_name(r.get("Volcan")) is None:
                continue
            n_tot += 1
            h = int(r["Fecha_Satelite_UTC"][11:13])
            try:
                v = float(r["VRP_MW"])
            except ValueError:
                v = 0.0
            for corte in (20, 21):
                if 13 <= h <= corte:
                    hora_max[corte] = hora_max.get(corte, 0) + 1
                    if v >= 1.0:
                        hora_max[(corte, "prot")] = hora_max.get((corte, "prot"), 0) + 1
            if 13 <= h <= 21:
                n_13_21 += 1
                if v >= 1.0:
                    n_13_21_prot += 1
                    det[(r["Sensor"].strip(), normalize_volcano_name(r["Volcan"]))] += 1
    return n_tot, n_13_21, n_13_21_prot, det, hora_max


def main():
    out = []
    p = out.append
    p("ENABLE_DAYTIME_MODIS (perfil %s) = %s" % (os.environ["VRP_PROFILE"], profile.ENABLE_DAYTIME_MODIS))

    # C2
    lat, lon = coords()["Lascar"]
    c2 = []
    for b in BUCKET_SENSOR:
        c2.append(es_descartada(b, lat, lon, datetime(2026, 6, 15, 5, 0))[0] is False)
        c2.append(es_descartada(b, lat, lon, datetime(2026, 1, 15, 17, 0))[0] is True)
    p("C2 regla sintetica (6 casos con respuesta conocida): %d de 6 correctos -> %s"
      % (sum(c2), "PASA" if all(c2) else "FALLA"))

    # C1
    n_tot, n1321, n1321p, det, hm = control_c1()
    p("C1 tabla sola latest_consolidado.csv: %d ALERTA_TERMICA; hora 13-21 UTC: %d, de ellas >= 1 MW: %d"
      " (D27 dice 1.642 / 37 / 19) -> %s" % (n_tot, n1321, n1321p, "PASA" if (n1321, n1321p) == (37, 19) else "NO REPRODUCE"))
    p("   corte 13-20: %d (%d >= 1 MW); corte 13-21: %d (%d)" % (hm.get(20, 0), hm.get((20, "prot"), 0),
                                                             hm.get(21, 0), hm.get((21, "prot"), 0)))
    p("   detalle >= 1 MW 13-21 UTC: " + ", ".join("%s %s %d" % (s, v, n) for (s, v), n in sorted(det.items())))
    # La version de hoy trae una fila nueva (NdC MODIS 2026-10-14 13:05, procesada 19:06 UTC, despues del
    # conteo de D27). La version del commit 1f73c2006 (sync de las 18:37 UTC) es la que D27 pudo ver.
    n_tot, n1321, n1321p, det, hm = control_c1("1f73c2006")
    p("C1' misma cuenta sobre latest_consolidado.csv del commit 1f73c2006 (18:37 UTC de hoy): %d / %d / %d -> %s"
      % (n_tot, n1321, n1321p, "PASA" if (n1321, n1321p) == (37, 19) else "NO REPRODUCE"))

    co = coords()
    filas = cargar_referencia_unificada()
    p("\nReferencia unificada: %d filas, %s a %s" % (len(filas), filas[0]["fecha_utc"], filas[-1]["fecha_utc"]))

    # todas las filas con su elevacion
    c3 = Counter()
    alertas = []
    pas_noche_prot = defaultdict(set)
    pas_dia_prot = defaultdict(set)
    pas_dia_alerta = defaultdict(set)
    pas_noche_alerta = defaultdict(set)
    sin_coord = Counter()
    for f in filas:
        if f["volcano"] not in co:
            sin_coord[f["volcano"]] += 1
            continue
        la, lo = co[f["volcano"]]
        dt = datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M")
        desc, elev = es_descartada(f["sensor_bucket"], la, lo, dt)
        f["elev_solar"] = round(elev, 2)
        f["descartada_replica"] = desc
        h = dt.hour
        if f["tipo"] in TIPOS_ALERTA:
            c3[(desc, 13 <= h <= 21)] += 1
            alertas.append(f)
            k = clave_pasada(f)
            tr = (f["sensor_bucket"], tramo_a119(f["fecha_utc"]))
            if desc:
                pas_dia_alerta[tr].add(k)
            else:
                pas_noche_alerta[tr].add(k)
            if alerta_protegida(f, lectura="A"):
                (pas_dia_prot if desc else pas_noche_prot)[tr].add(k)
    p("filas sin coordenadas: %s" % dict(sin_coord))

    p("\nContexto: TODAS las filas de la tabla (CONS), por sensor y luz (MIROVA si procesa el dia):")
    ctx = Counter((f["sensor_bucket"], "dia" if f["descartada_replica"] else "noche", f["tipo"])
                  for f in filas if f["source"] == "CONS" and "descartada_replica" in f)
    for s in BUCKET_SENSOR:
        for luz in ("dia", "noche"):
            tot = sum(n for (a, b, _t), n in ctx.items() if a == s and b == luz)
            al = ctx[(s, luz, "ALERTA_TERMICA")]
            p("   %-9s %-6s filas %5d  ALERTA %4d (%.1f %%)  FALSO_POSITIVO %4d  RUTINA %5d"
              % (s, luz, tot, al, 100.0 * al / max(tot, 1), ctx[(s, luz, "FALSO_POSITIVO")], ctx[(s, luz, "RUTINA")]))

    p("\nC3 regla de elevacion (descartada) contra corte 13-21 UTC, filas de alerta:")
    for (d, h), n in sorted(c3.items()):
        p("   descartada=%s  hora13-21=%s : %d" % (d, h, n))

    dia = [f for f in alertas if f["descartada_replica"]]
    noche = [f for f in alertas if not f["descartada_replica"]]
    p("\nFILAS de alerta (CONS + OCR, lectura A cuenta las dos): %d; diurnas (la replica las descarta): %d; nocturnas: %d"
      % (len(alertas), len(dia), len(noche)))
    prot_dia = [f for f in dia if alerta_protegida(f, lectura="A")]
    prot_noche = [f for f in noche if alerta_protegida(f, lectura="A")]
    p("FILAS protegidas (lectura A, >= 1 MW): diurnas %d, nocturnas %d" % (len(prot_dia), len(prot_noche)))

    def tabla(titulo, fs, clavef):
        p("\n" + titulo)
        c = Counter(clavef(f) for f in fs)
        for k, n in sorted(c.items(), key=lambda x: (str(x[0]))):
            p("   %-40s %d" % (k, n))

    tabla("Diurnas por sensor y canal (filas):", dia, lambda f: (f["sensor_bucket"], f["source"]))
    tabla("Diurnas protegidas por sensor y canal (filas):", prot_dia, lambda f: (f["sensor_bucket"], f["source"]))
    tabla("Diurnas por volcan (filas; entre parentesis protegidas):", dia, lambda f: f["volcano"])
    tabla("  protegidas por volcan:", prot_dia, lambda f: f["volcano"])
    tabla("Diurnas por hora UTC (filas):", dia, lambda f: f["fecha_utc"][11:13])
    tabla("Diurnas por banda de elevacion solar (grados):", dia,
          lambda f: "%02d-%02d" % (int(f["elev_solar"] // 10) * 10, int(f["elev_solar"] // 10) * 10 + 10))
    tabla("  protegidas por banda de elevacion solar:", prot_dia,
          lambda f: "%02d-%02d" % (int(f["elev_solar"] // 10) * 10, int(f["elev_solar"] // 10) * 10 + 10))
    tabla("Diurnas por mes:", dia, lambda f: f["fecha_utc"][:7])
    tabla("  protegidas por mes:", prot_dia, lambda f: f["fecha_utc"][:7])
    tabla("Diurnas protegidas por clase de VRP:", prot_dia,
          lambda f: "1-10 MW" if f["vrp_mw"] < 10 else ("10-100 MW" if f["vrp_mw"] < 100 else ">=100 MW"))

    p("\nPASADAS (volcan, sensor, minuto; junta CONS y OCR), por sensor y tramo A119:")
    p("   %-10s %-32s %8s %8s %10s %10s" % ("sensor", "tramo", "dia_al", "noche_al", "dia_prot", "noche_prot"))
    llaves = sorted(set(pas_dia_alerta) | set(pas_noche_alerta))
    tot = Counter()
    for tr in llaves:
        a, b, c, d = (len(pas_dia_alerta[tr]), len(pas_noche_alerta[tr]), len(pas_dia_prot[tr]), len(pas_noche_prot[tr]))
        tot.update({"a": a, "b": b, "c": c, "d": d})
        p("   %-10s %-32s %8d %8d %10d %10d" % (tr[0], tr[1], a, b, c, d))
    p("   %-43s %8d %8d %10d %10d" % ("TOTAL", tot["a"], tot["b"], tot["c"], tot["d"]))

    # elevacion de las nocturnas (control de que la regla no deja pasar crepusculo como noche muy cerca de 0)
    cerca = [f for f in alertas if abs(f["elev_solar"]) < 3]
    p("\nAlertas a menos de 3 grados del horizonte (cerca del terminador, sensibles a la hora): %d (%d protegidas)"
      % (len(cerca), sum(alerta_protegida(f) for f in cerca)))

    (AQUI / "poblacion_salida.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    json.dump({"dia": dia, "noche": noche}, open(AQUI / "poblacion_filas.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    print("\n".join(out))


if __name__ == "__main__":
    main()
