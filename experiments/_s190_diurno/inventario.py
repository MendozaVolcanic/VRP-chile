# -*- coding: utf-8 -*-
"""S190 diurno, paso 0: cuantas alertas diurnas publica MIROVA y cuantas pasadas diurnas tenemos nosotros.

POR QUE. Produccion corre la via "codigo MIROVA" en los tres sensores, y el detector de la via ya trae la rama
diurna del .m (dayflag, sun-glint bajo 12 grados). Pero el dia se corta antes de llegar a el: en el filtro previo a la
descarga (fetch.py, run_pipeline.process_date) y en store._reject_daytime. Este script mide (1) el tamano de lo que
perdemos por construccion: alertas diurnas de MIROVA por sensor desde marzo, con la tabla sola y con OCR (A119, el OCR
solo cuenta desde el 2026-06-13); y (2) que nuestros records publicados de verdad no tienen pasadas diurnas.

Dia = elevacion solar > 0 sobre el volcan, la misma regla de pipeline.store._solar_elevation.

Controles que pueden fallar (A110, A116):
  C1. Regla sintetica: Lascar 2026-06-15 05:00 UTC debe ser noche y 2026-01-15 17:00 UTC dia.
  C2. El contador de records puede dar distinto de cero: se le pasa un record falso diurno y debe contarlo.
Salida: inventario_salida.txt (esta misma impresion).
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import yaml  # noqa: E402

from pipeline import profile  # noqa: E402
from pipeline.store import _solar_elevation  # noqa: E402
import referencia_mirova_unificada as RMU  # noqa: E402
from clase_mirova import alerta_protegida, clave_pasada, TIPOS_ALERTA  # noqa: E402

DESDE = "2026-03-01"
OCR_DESDE = "2026-06-13"   # A119: OCR mal calibrado hasta el 2026-06-11; tramo T2 de calidad_referencia_mirova


def coords():
    with open(ROOT / "volcanoes.yaml", encoding="utf-8") as fh:
        return {v["name"]: (v["lat"], v["lon"]) for v in yaml.safe_load(fh)["volcanoes"] if "lat" in v}


def es_dia(lat, lon, fecha):
    dt = datetime.strptime(fecha[:16].replace("T", " "), "%Y-%m-%d %H:%M")
    return _solar_elevation(lat, lon, dt) > 0


def ultimo_commit(path):
    r = subprocess.run(["git", "log", "-1", "--format=%cI %h", "--", str(path)], cwd=ROOT,
                       capture_output=True, text=True)
    return r.stdout.strip()


def contar_records_diurnos(records, lat, lon):
    n_dia, n_tot, dayflag1 = 0, 0, 0
    for r in records:
        f = r.get("datetime_utc") or ""
        if len(f) < 16:
            continue
        n_tot += 1
        if es_dia(lat, lon, f):
            n_dia += 1
        if (r.get("diag_codigo_mirova") or {}).get("dayflag") == 1:
            dayflag1 += 1
    return n_tot, n_dia, dayflag1


def main():
    co = coords()
    print("Perfil:", os.environ["VRP_PROFILE"], "| ENABLE_DAYTIME_VIIRS =", profile.ENABLE_DAYTIME_VIIRS,
          "| ENABLE_DAYTIME_MODIS =", profile.ENABLE_DAYTIME_MODIS)
    print("Tabla:", Path(RMU.SNAP_CONS).name, "ultimo commit", ultimo_commit(RMU.SNAP_CONS))
    print("OCR  :", Path(RMU.SNAP_OCR).name, "ultimo commit", ultimo_commit(RMU.SNAP_OCR))

    la, lo = co["Lascar"]
    c1 = (not es_dia(la, lo, "2026-06-15 05:00")) and es_dia(la, lo, "2026-01-15 17:00")
    print("C1 regla sintetica de dia/noche:", "PASA" if c1 else "FALLA")
    falso = [{"datetime_utc": "2026-01-15T17:00:00Z", "diag_codigo_mirova": {"dayflag": 1}},
             {"datetime_utc": "2026-06-15T05:00:00Z"}]
    c2 = contar_records_diurnos(falso, la, lo) == (2, 1, 1)
    print("C2 el contador de records puede dar distinto de cero:", "PASA" if c2 else "FALLA")

    filas = [f for f in RMU.cargar_referencia_unificada() if f["fecha_utc"][:10] >= DESDE]
    print("\nReferencia desde %s: %d filas, %s a %s" % (DESDE, len(filas), filas[0]["fecha_utc"][:16],
                                                       filas[-1]["fecha_utc"][:16]))
    print("campos de una fila:", sorted(filas[0].keys()))
    sin_coord = Counter(f["volcano"] for f in filas if f["volcano"] not in co)
    if sin_coord:
        print("filas sin coordenadas:", dict(sin_coord))

    tab = {}
    for f in filas:
        if f["volcano"] not in co:
            continue
        k = clave_pasada(f)
        lat, lon = co[f["volcano"]]
        d = tab.setdefault(k, {"dia": es_dia(lat, lon, f["fecha_utc"]), "at": False, "pt": False,
                               "ac": False, "pc": False})
        alerta = f["tipo"] in TIPOS_ALERTA
        prot = alerta_protegida(f)
        es_tabla = f["source"] == "CONS"
        cuenta_ocr = f["fecha_utc"][:10] >= OCR_DESDE
        if es_tabla:
            d["at"] |= alerta
            d["pt"] |= prot
        if es_tabla or cuenta_ocr:
            d["ac"] |= alerta
            d["pc"] |= prot
    print("fuentes:", dict(Counter(f["source"] for f in filas)))

    print("\nPasadas de MIROVA (volcan, sensor, minuto) desde %s, y cuantas son alerta" % DESDE)
    print("  tab = solo tabla latest.php; comb = tabla + OCR desde %s (A119); prot = >= 1 MW lectura A" % OCR_DESDE)
    print("  %-10s %-6s %8s %10s %10s %10s %10s" % ("sensor", "luz", "pasadas", "alerta_tab", "prot_tab",
                                                     "alerta_comb", "prot_comb"))
    for sen in sorted({k[1] for k in tab}):
        for luz in ("dia", "noche"):
            sel = [d for (v, s, _), d in tab.items() if s == sen and d["dia"] == (luz == "dia")]
            fila = (len(sel), sum(d["at"] for d in sel), sum(d["pt"] for d in sel),
                    sum(d["ac"] for d in sel), sum(d["pc"] for d in sel))
            print("  %-10s %-6s %8d %10d %10d %10d %10d" % ((sen, luz) + fila))

    print("\nAlertas diurnas (comb) por volcan y sensor; entre parentesis protegidas >= 1 MW; [tabla sola]:")
    cv, cp, ct = Counter(), Counter(), Counter()
    for (vol, sen, _), d in tab.items():
        if d["dia"] and d["ac"]:
            cv[(vol, sen)] += 1
            cp[(vol, sen)] += d["pc"]
            ct[(vol, sen)] += d["at"]
    for (vol, sen), n in sorted(cv.items(), key=lambda x: (-x[1], x[0])):
        print("  %-24s %-10s %4d (%d) [%d]" % (vol, sen, n, cp[(vol, sen)], ct[(vol, sen)]))

    print("\nAlertas diurnas (comb) por mes y sensor:")
    cm = Counter()
    for (vol, sen, minuto), d in tab.items():
        if d["dia"] and d["ac"]:
            cm[(minuto[:7], sen)] += 1
    for (m, s), n in sorted(cm.items()):
        print("  %s %-10s %d" % (m, s, n))

    print("\nNuestros records en data/mirova_equivalent/, pasadas diurnas por sensor (debe ser 0 hoy):")
    porsen, porsen_dia, porsen_flag = Counter(), Counter(), Counter()
    for p in sorted((ROOT / "data" / "mirova_equivalent").glob("*.json")):
        vol = p.stem
        if vol not in co:
            continue
        try:
            js = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        lat, lon = co[vol]
        grupos = {}
        for r in js.get("records", []):
            grupos.setdefault(r.get("sensor", "?"), []).append(r)
        for s, rs in grupos.items():
            n, nd, nf = contar_records_diurnos(rs, lat, lon)
            porsen[s] += n
            porsen_dia[s] += nd
            porsen_flag[s] += nf
    for s in sorted(porsen):
        print("  %-22s records %7d  diurnos %5d  dayflag=1 %5d" % (s, porsen[s], porsen_dia[s], porsen_flag[s]))


if __name__ == "__main__":
    main()
