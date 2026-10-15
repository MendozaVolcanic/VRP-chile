"""Prueba de que mostrar las alertas DIURNAS de MIROVA no cambia ningun numero publicado (S151).

Reconstruye data/mirova/<Volcan>.json para los 11 Tier A con el script de una referencia vieja (por defecto el
commit base del PR, 9db82aa80) y con el de este arbol, sobre los MISMOS CSV, y compara:
- `records` tiene que ser identico salvo la clave `dia` en filas diurnas de la tabla;
- la marca `dia` tiene que coincidir con pipeline.store._solar_elevation > 0;
- todo lo nuevo tiene que estar en `records_dia_ocr`, y ser diurno y del OCR;
- y, de paso, el build viejo contra lo commiteado en data/mirova (si el CSV no cambio, deben ser iguales).

Todo se escribe en un directorio temporal que se borra al terminar.
Uso: python experiments/_s151_alertas_diurnas/comparar_rebuild_main_rama.py [REF]
"""
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.store import _solar_elevation  # noqa: E402

REF = sys.argv[1] if len(sys.argv) > 1 else "9db82aa80"
VOLS = [("PuyehueCordonCaulle", "Puyehue-Cordon Caulle"), ("Villarrica", "Villarrica"), ("Lascar", "Lascar"),
        ("Copahue", "Copahue"), ("NevadosDeChillan", "Nevados de Chillan"), ("Llaima", "Llaima"),
        ("Chaiten", "Chaiten"), ("PlanchonPeteroa", "PlanchonPeteroa"), ("Lastarria", "Lastarria"),
        ("Isluga", "Isluga"), ("Tupungatito", "Tupungatito")]
CONS = ROOT / "latest_consolidado.csv"
OCR = ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"


def cargar(nombre, path):
    spec = importlib.util.spec_from_file_location(nombre, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.RAIZ_REAL = ROOT          # volcanoes.yaml y pipeline/ de este arbol
    return m


def construir(mod, salida):
    mod.REPO = salida
    out = {}
    for stem, csvn in VOLS:
        with contextlib.redirect_stdout(io.StringIO()):
            mod.rebuild(stem, csvn, source=CONS, ocr=OCR)
        out[stem] = json.loads((salida / "data" / "mirova" / f"{stem}.json").read_text(encoding="utf-8"))
    return out


def elev(latlon, dt):
    return _solar_elevation(latlon[0], latlon[1],
                            datetime.strptime(dt, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc))


def main():
    coords = {v["name"]: (v["lat"], v["lon"])
              for v in yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"] if "lat" in v}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        viejo_src = subprocess.run(["git", "-C", str(ROOT), "show", f"{REF}:scripts/rebuild_mirova_from_consolidado.py"],
                                   check=True, capture_output=True).stdout
        (tmp / "viejo.py").write_bytes(viejo_src)
        viejo = construir(cargar("rb_viejo", tmp / "viejo.py"), tmp / "viejo")
        nuevo = construir(cargar("rb_nuevo", ROOT / "scripts" / "rebuild_mirova_from_consolidado.py"), tmp / "nuevo")

    ok = True
    tot = {"dia_tabla": 0, "dia_ocr": 0, "dia_ocr_sin_geometria": 0}
    print(f"referencia vieja: {REF}")
    print(f"{'volcan':22s} {'records':>8s} {'igual':>6s} {'dia_tabla':>9s} {'dia_ocr':>8s} {'sin_geo':>8s} {'viejo=commit':>12s}")
    for stem, _ in VOLS:
        a, b = viejo[stem]["records"], nuevo[stem]["records"]
        igual = a == [{k: v for k, v in r.items() if k != "dia"} for r in b]
        ok &= igual
        for r in b:
            if r.get("dia") != (True if elev(coords[stem], r["datetime_utc"]) > 0 else None) or (
                    r.get("dia") and r["source"] != "consolidado"):
                ok = False
                print("  marca dia incoherente en records:", stem, r)
        dia_ocr = nuevo[stem].get("records_dia_ocr", [])
        for r in dia_ocr:
            if not (elev(coords[stem], r["datetime_utc"]) > 0 and r.get("dia") is True and r["source"] == "ocr"):
                ok = False
                print("  fila mala en records_dia_ocr:", stem, r)
        commit = json.loads((ROOT / "data" / "mirova" / f"{stem}.json").read_text(encoding="utf-8"))["records"]
        nd, sg = sum(1 for r in b if r.get("dia")), sum(1 for r in dia_ocr if r.get("sin_geometria"))
        tot["dia_tabla"] += nd
        tot["dia_ocr"] += len(dia_ocr)
        tot["dia_ocr_sin_geometria"] += sg
        print(f"{stem:22s} {len(b):8d} {str(igual):>6s} {nd:9d} {len(dia_ocr):8d} {sg:8d} {str(commit == a):>12s}")
    print("TOTAL", tot)
    print("RESULTADO:", "OK, records identico salvo la marca dia" if ok else "FALLA")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
