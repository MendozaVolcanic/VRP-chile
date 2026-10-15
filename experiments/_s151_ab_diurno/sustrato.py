# -*- coding: utf-8 -*-
"""Sustrato del A/B diurno (D-10): cuántos positivos y negativos diurnos caben en cada ventana.

POR QUÉ. El pre-registro (PREREGISTRO.md) fija ventanas y umbrales ANTES de correr. Un A/B sin
sustrato no mide nada (S130: el A/B sin sustrato); y un umbral que no sale de los datos es un
gusto (A115). Este script cuenta, sobre la referencia de MIROVA y con la MISMA regla día/noche del
pipeline (`store._solar_elevation`, elevación > 0), para cada ventana propuesta:

  * POSITIVOS: pasadas VIIRS 375 y 750 diurnas con alerta protegida (lectura A, >= 1 MW), usables
    bajo A119 (desde el 2026-06-13 cuenta todo; del 1 de marzo al 12 de junio sólo una pasada con
    fila de la tabla; enero y febrero fuera). Los 3 positivos MODIS de las 40 no entran: la rama
    diurna de D-10 es sólo VIIRS.
  * NEGATIVOS DIURNOS LIMPIOS: pasadas VIIRS diurnas de la TABLA (CONS) en que todas las filas de la
    pasada son RUTINA (MIROVA miró y no vio nada) y MIROVA no alertó ese volcán en todo ese día
    diurno (ningún sensor, ninguna fuente). Es el análogo diurno del negativo limpio nocturno de
    scripts/banco_paridad.py (S139).
  * PARSIMONIA DE MIROVA: fracción de pasadas VIIRS diurnas de la tabla en que MIROVA alerta. Es la
    vara con que se compara nuestra tasa de publicación diurna (la réplica tiene que ser tan callada
    como MIROVA de día, no más ruidosa).

Controles (A110): (C1) el total de positivos VIIRS usables tiene que dar 37 (las 40 del estudio
experiments/_s151_alertas_diurnas/ menos 3 MODIS); (C2) la regla día/noche sobre dos casos con
respuesta conocida. Si un control falla, el script sale con error.

Salida: sustrato_salida.txt (stdout) y sustrato.json.
"""
from __future__ import annotations

import io
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pipeline.store import _solar_elevation  # noqa: E402
from auto_audit_weekly import _coords_por_volcan  # noqa: E402
from clase_mirova import alerta_protegida, TIPOS_ALERTA  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
import calidad_referencia_mirova as calidad  # noqa: E402

# Ventanas por tramo A119 (inclusive). W1 sólo Láscar: es el único volcán con positivos usables
# antes del 13 de junio (todos de tabla). Las demás cubren los 11 Tier A.
VENTANAS = [
    ("W1", "2026-03-01", "2026-03-20", ["Lascar"]),
    ("W2", "2026-06-13", "2026-06-30", None),
    ("W3", "2026-07-20", "2026-07-31", None),
    ("W4", "2026-08-13", "2026-08-31", None),
    ("W5", "2026-09-01", "2026-09-20", None),
    ("W6", "2026-10-01", "2026-10-14", None),
]
VIIRS = ("VIIRS375", "VIIRS750")


def es_dia(fila, coords):
    lat, lon = coords[fila["volcano"]]
    dt = datetime.strptime(fila["fecha_utc"][:16], "%Y-%m-%d %H:%M")
    return _solar_elevation(lat, lon, dt) > 0


def usable_a119(fila):
    f = fila["fecha_utc"][:10]
    if f < "2026-03-01":
        return False
    if f < "2026-06-13":
        return fila["source"] == "CONS"
    return True


def dia_local(fila):
    """Día diurno del volcán: la fecha UTC menos 4 h cae en la fecha local de la tarde chilena."""
    dt = datetime.strptime(fila["fecha_utc"][:16], "%Y-%m-%d %H:%M") - timedelta(hours=4)
    return dt.date().isoformat()


def main():
    coords = _coords_por_volcan()
    # C2: casos con respuesta conocida (Láscar).
    lat, lon = coords["Lascar"]
    assert _solar_elevation(lat, lon, datetime(2026, 6, 15, 5, 0)) < 0, "C2: Láscar 05 UTC no es noche"
    assert _solar_elevation(lat, lon, datetime(2026, 6, 15, 17, 24)) > 0, "C2: Láscar 17:24 UTC no es día"

    filas = [f for f in cargar_referencia_unificada() if f["volcano"] in coords]
    diurnas = [f for f in filas if es_dia(f, coords)]

    # Pasadas con alerta (cualquier sensor, cualquier fuente) por volcán y día local.
    alerta_dia = set()
    for f in diurnas:
        if f["tipo"] in TIPOS_ALERTA:
            alerta_dia.add((f["volcano"], dia_local(f)))

    # Positivos: pasadas VIIRS diurnas protegidas y usables bajo A119.
    pos = {}
    for f in diurnas:
        if f["sensor_bucket"] in VIIRS and alerta_protegida(f) and usable_a119(f):
            pos[(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])] = f

    # Pasadas VIIRS diurnas de la tabla, agrupadas por pasada.
    tabla = defaultdict(list)
    for f in diurnas:
        if f["sensor_bucket"] in VIIRS and f["source"] == "CONS":
            tabla[(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])].append(f)
    neg = {k: v for k, v in tabla.items()
           if all(x["tipo"] == "RUTINA" for x in v) and (k[0], dia_local(v[0])) not in alerta_dia}
    con_alerta_tabla = {k for k, v in tabla.items() if any(x["tipo"] in TIPOS_ALERTA for x in v)}
    # Parsimonia con el OCR (verificador PR #821): una pasada de la tabla cuenta como «MIROVA
    # alertó» si hay una fila de alerta de CUALQUIER fuente del mismo volcán y sensor a 120 s o
    # menos (la tolerancia de banco_paridad). Sin esto la vara de G2 subestima a MIROVA, porque
    # el OCR trae alertas diurnas que la tabla no lista.
    horas_alerta = defaultdict(list)
    for f in diurnas:
        if f["sensor_bucket"] in VIIRS and f["tipo"] in TIPOS_ALERTA:
            horas_alerta[(f["volcano"], f["sensor_bucket"])].append(
                datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M"))

    def alerta_cerca(k):
        t0 = datetime.strptime(k[2], "%Y-%m-%d %H:%M")
        return any(abs((h - t0).total_seconds()) <= 120 for h in horas_alerta[(k[0], k[1])])
    con_alerta_cualquiera = {k for k in tabla if alerta_cerca(k)}

    total_pos = len(pos)
    print("Positivos VIIRS diurnos protegidos usables bajo A119 (toda la referencia): %d" % total_pos)
    if total_pos != 37:
        raise SystemExit("C1 FALLA: se esperaban 37 (40 del estudio menos 3 MODIS), salieron %d" % total_pos)

    out = {"ventanas": [], "positivos_fuera_de_ventana": []}
    cubiertos = set()
    print("\n%-3s %-10s %-10s %-9s  pos(V375/V750)  neg_limpios(V375/V750)  pasadas_tabla  alerta_tabla  parsimonia"
          % ("W", "inicio", "fin", "volcanes"))
    for nombre, ini, fin, vols in VENTANAS:
        calidad.avisar(ini, fin, archivo=sys.stdout)

        def dentro(k):
            return ini <= k[2][:10] <= fin and (vols is None or k[0] in vols)
        p = [k for k in pos if dentro(k)]
        n = [k for k in neg if dentro(k)]
        t = [k for k in tabla if dentro(k)]
        a = [k for k in con_alerta_tabla if dentro(k)]
        cubiertos.update(p)
        cuenta = {s: (sum(1 for k in p if k[1] == s), sum(1 for k in n if k[1] == s)) for s in VIIRS}
        pars = len(a) / len(t) if t else float("nan")
        print("%-3s %-10s %-10s %-9s  %3d (%d/%d)      %5d (%d/%d)            %5d          %4d       %.4f"
              % (nombre, ini, fin, "Lascar" if vols else "11 TierA", len(p), cuenta["VIIRS375"][0],
                 cuenta["VIIRS750"][0], len(n), cuenta["VIIRS375"][1], cuenta["VIIRS750"][1],
                 len(t), len(a), pars))
        # Parsimonia por sensor (vara de G2 del pre-registro, se compara por sensor).
        ac = [k for k in con_alerta_cualquiera if dentro(k)]
        por_sensor = {s: (sum(1 for k in t if k[1] == s), sum(1 for k in a if k[1] == s),
                          sum(1 for k in ac if k[1] == s)) for s in VIIRS}
        print("    por sensor (alerta de tabla / alerta de tabla u OCR / pasadas de tabla): " + "  ".join(
            "%s %d/%d/%d" % (s, por_sensor[s][1], por_sensor[s][2], por_sensor[s][0]) for s in VIIRS))
        out["ventanas"].append({
            "nombre": nombre, "inicio": ini, "fin": fin, "volcanes": vols or "11 Tier A",
            "positivos": sorted("|".join(k) for k in p),
            "positivos_por_fuente": {fu: sum(1 for k in p if pos[k]["source"] == fu)
                                     for fu in ("CONS", "OCR")},
            "n_negativos_limpios": {s: cuenta[s][1] for s in VIIRS},
            "n_pasadas_tabla": len(t), "n_pasadas_tabla_con_alerta": len(a),
            "pasadas_tabla_por_sensor": {s: por_sensor[s][0] for s in VIIRS},
            "con_alerta_por_sensor": {s: por_sensor[s][1] for s in VIIRS},
            "con_alerta_tabla_u_ocr_por_sensor": {s: por_sensor[s][2] for s in VIIRS},
            "parsimonia_mirova": pars,
        })
    fuera = sorted("|".join(k) for k in pos if k not in cubiertos)
    out["positivos_fuera_de_ventana"] = fuera
    print("\nPositivos cubiertos por las ventanas: %d de %d; fuera: %s" % (len(cubiertos), total_pos, fuera))
    tot_t = sum(w["n_pasadas_tabla"] for w in out["ventanas"])
    tot_a = sum(w["n_pasadas_tabla_con_alerta"] for w in out["ventanas"])
    tot_n = sum(sum(w["n_negativos_limpios"].values()) for w in out["ventanas"])
    print("Total ventanas: pasadas VIIRS diurnas de tabla %d, con alerta %d (parsimonia %.4f), negativos limpios %d"
          % (tot_t, tot_a, tot_a / max(tot_t, 1), tot_n))
    # Totales W2 a W6 por sensor (W1 se informa aparte: tramo A119 anterior a abril).
    w26 = [w for w in out["ventanas"] if w["nombre"] != "W1"]
    tot_s = {s: (sum(w["pasadas_tabla_por_sensor"][s] for w in w26),
                 sum(w["con_alerta_por_sensor"][s] for w in w26),
                 sum(w["n_negativos_limpios"][s] for w in w26),
                 sum(w["con_alerta_tabla_u_ocr_por_sensor"][s] for w in w26)) for s in VIIRS}
    for s in VIIRS:
        print("W2-W6 %s: pasadas diurnas de tabla %d, con alerta de tabla %d (%.4f), con alerta de tabla u OCR"
              " %d (p_MIROVA %.4f), negativos limpios %d"
              % (s, tot_s[s][0], tot_s[s][1], tot_s[s][1] / max(tot_s[s][0], 1), tot_s[s][3],
                 tot_s[s][3] / max(tot_s[s][0], 1), tot_s[s][2]))
    pos_fuente = {fu: sum(1 for k in pos if pos[k]["source"] == fu) for fu in ("CONS", "OCR")}
    w2 = next(w for w in out["ventanas"] if w["nombre"] == "W2")
    print("Positivos por fuente (todas las ventanas): %s; W2: %d positivos, %s, alertas de tabla en W2: %d"
          % (pos_fuente, len(w2["positivos"]), w2["positivos_por_fuente"], w2["n_pasadas_tabla_con_alerta"]))
    out["totales"] = {"pasadas_tabla": tot_t, "con_alerta": tot_a, "negativos_limpios": tot_n,
                      "positivos_cubiertos": len(cubiertos), "positivos_total": total_pos,
                      "w2_w6_por_sensor": {s: {"pasadas_tabla": tot_s[s][0], "con_alerta": tot_s[s][1],
                                              "con_alerta_tabla_u_ocr": tot_s[s][3],
                                              "negativos_limpios": tot_s[s][2]} for s in VIIRS},
                      "positivos_por_fuente": pos_fuente}
    (Path(__file__).parent / "sustrato.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
