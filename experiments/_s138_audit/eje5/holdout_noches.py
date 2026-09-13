"""S138 eje 5 - cuenta el HOLDOUT propuesto para el A/B de D21/D22: noches confirmadas por MIROVA
(CONS union OCR) en los 11 Tier A, ventana 2026-06-01 a 2026-08-31, por volcan y sensor.

POR QUE. Tres correcciones al pipeline se estan eligiendo sobre nueve escenas de un paper de 2016.
Antes de adoptar hay que medirlas sobre noches que NO participaron en la eleccion. Este script solo
cuenta cuantas hay (denominador del pre-registro) y con que cobertura, usando el MISMO loader y el
MISMO filtro diurno que la auditoria semanal (scripts/auto_audit_weekly.py), para que el universo sea
el que el proyecto ya usa y no uno inventado aca.

LAS DOS PREGUNTAS. (1) Si el CSV estuviera vacio en la ventana, se ve: se imprime la fecha maxima de
cada CSV y el total de filas en ventana; un cero aqui es SIN DATO, no "no hubo alertas". (2) Control
positivo: Villarrica y Lascar tienen alertas casi todas las semanas; si salen 0 el loader esta mal.

READ-ONLY. Escribe solo en experiments/_s138_audit/eje5/out/.
"""
import io
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[2]
sys.path.insert(0, str(RAIZ))
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402
from pipeline.store import _reject_daytime, _solar_elevation  # noqa: E402
from pipeline.profile import ENABLE_DAYTIME_MODIS  # noqa: E402
import yaml  # noqa: E402

SNAP = RAIZ / "data" / "mirova_reference" / "mirova_v1_snapshot"
CONS, OCR = SNAP / "registro_vrp_consolidado.csv", SNAP / "registro_vrp_ocr.csv"
INI, FIN = "2026-06-01", "2026-08-31"
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten", "Tupungatito",
        "Copahue", "PlanchonPeteroa", "PuyehueCordonCaulle", "NevadosDeChillan"]
# scripts/build_c2ab_windows.py:41-42 (S131). OJO: experiments/_s114_audit/*.py ponen Lastarria,
# Isluga, PlanchonPeteroa y PCC entre los NEVADOS; las dos listas no coinciden. Se usa la de S131 y se
# declara la discrepancia.
FOCAL = ["Lascar", "Lastarria", "Isluga", "PlanchonPeteroa", "PuyehueCordonCaulle"]
NEVADO = ["Llaima", "Copahue", "Villarrica", "NevadosDeChillan", "Tupungatito", "Chaiten"]
SENSORES = ["MODIS", "VIIRS750", "VIIRS375"]
_BUCKET_SENSOR = {"MODIS": "MODIS_TERRA", "VIIRS375": "VIIRS_SNPP", "VIIRS750": "VIIRS_SNPP_750"}


def diurna(bucket, lat, lon, dt_utc):
    return _reject_daytime(_BUCKET_SENSOR.get(bucket, bucket), _solar_elevation(lat, lon, dt_utc),
                           ENABLE_DAYTIME_MODIS)


def fecha_max(path):
    import csv
    with open(path, encoding="utf-8", errors="replace") as fh:
        f = [(r.get("Fecha_Satelite_UTC") or "")[:10] for r in csv.DictReader(fh)]
    f = [x for x in f if x[:4].isdigit()]
    return max(f), min(f), len(f)


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    coords = {v["name"]: (v["lat"], v["lon"]) for v in
              yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"] if "lat" in v}
    print("=== COBERTURA DE LA REFERENCIA (pregunta 2: SIN DATO no es cero) ===")
    for p in (CONS, OCR, RAIZ / "latest_consolidado.csv"):
        mx, mn, n = fecha_max(p)
        print(f"  {p.name:32} filas {n:6d}  fechas {mn} .. {mx}")
    alertas = load_mirova_alertas(cons_path=str(CONS), ocr_path=str(OCR))
    print(f"  ALERTAs CONS u OCR (toda la historia, 11 Tier A): {len(alertas)}")
    noches = defaultdict(set)          # (vol, sensor) -> {fecha}
    noches_any = defaultdict(set)      # vol -> {fecha}
    fuente = defaultdict(lambda: defaultdict(int))
    n_win, n_diur = 0, 0
    for a in alertas:
        f = (a["fecha_utc"] or "")[:10]
        if not (INI <= f <= FIN) or a["sensor_bucket"] not in SENSORES:
            continue
        n_win += 1
        ll = coords.get(a["volcano"])
        try:
            dt = datetime.fromisoformat(a["fecha_utc"]).replace(tzinfo=timezone.utc)
        except ValueError:
            dt = None
        if ll and dt and diurna(a["sensor_bucket"], ll[0], ll[1], dt):
            n_diur += 1
            continue
        noches[(a["volcano"], a["sensor_bucket"])].add(f)
        noches_any[a["volcano"]].add(f)
        fuente[a["volcano"]][a["source"]] += 1
    print(f"  pasadas-ALERTA en ventana {INI}..{FIN}: {n_win}; diurnas excluidas (como el pipeline): {n_diur}")

    print(f"\n=== NOCHES CONFIRMADAS POR MIROVA, {INI} a {FIN} (92 dias), nocturnas, CONS u OCR ===")
    print(f"{'volcan':20} {'regimen':8} {'MODIS':>6} {'V750':>6} {'V375':>6} {'cualquiera':>11} {'CONS/OCR pasadas':>18}")
    tabla = {}
    tot = defaultdict(int)
    for v in VOLS:
        reg = "focal" if v in FOCAL else "nevado"
        fila = {s: len(noches[(v, s)]) for s in SENSORES}
        fila["cualquiera"] = len(noches_any[v])
        fila["regimen"] = reg
        fila["pasadas_CONS"] = fuente[v]["CONS"]
        fila["pasadas_OCR"] = fuente[v]["OCR"]
        tabla[v] = fila
        for s in SENSORES:
            tot[s] += fila[s]
        tot["cualquiera"] += fila["cualquiera"]
        tot[reg + "_MODIS"] += fila["MODIS"]
        tot[reg + "_any"] += fila["cualquiera"]
        print(f"{v:20} {reg:8} {fila['MODIS']:6d} {fila['VIIRS750']:6d} {fila['VIIRS375']:6d} {fila['cualquiera']:11d} "
              f"{fila['pasadas_CONS']:8d}/{fila['pasadas_OCR']:<8d}")
    print(f"{'TOTAL':20} {'':8} {tot['MODIS']:6d} {tot['VIIRS750']:6d} {tot['VIIRS375']:6d} {tot['cualquiera']:11d}")
    print(f"  estrato focal : MODIS {tot['focal_MODIS']}  cualquier sensor {tot['focal_any']}")
    print(f"  estrato nevado: MODIS {tot['nevado_MODIS']}  cualquier sensor {tot['nevado_any']}")
    ctrl = tabla["Villarrica"]["cualquiera"] > 0 and tabla["Lascar"]["cualquiera"] > 0
    print(f"  control positivo (Villarrica y Lascar > 0 noches): {'OK' if ctrl else 'FALLA, loader roto'}")
    (HERE / "out" / "holdout_noches.json").write_text(json.dumps(
        {"ventana": [INI, FIN], "noches": tabla, "totales": dict(tot), "pasadas_en_ventana": n_win,
         "diurnas_excluidas": n_diur, "control_ok": ctrl}, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
