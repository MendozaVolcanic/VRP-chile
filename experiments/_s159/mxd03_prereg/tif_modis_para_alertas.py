"""S159, pre-registro de MxD03: ¿cuántas alertas MODIS de MIROVA de la ventana tienen un GeoTIFF MODIS de MIROVA de
ESA pasada? (vara espacial de paridad)

Cruza las filas de alerta MODIS nocturnas de la referencia unificada (consolidado + OCR, mismo cargador que
banco_paridad) con el index.csv de mirova-tif-archive: mismo volcán, sensor MODIS, `acquisition_utc` a ±5 min de la
hora de la fila. Cuenta además cuántas de esas imágenes son la PRIMERA aparición de su md5 (A106: MIROVA a veces
vuelve a servir una imagen vieja bajo una hora nueva).

Las dos preguntas del instrumento:
1. Si no hubiera TIF para ninguna alerta, ¿se vería? Sí: imprime cuántas alertas hay en el tramo con TIF (mayo a
   septiembre) y cuántas tienen par; un cero con alertas en el tramo es un cero medido.
2. Si el cruce de nombres de volcán estuviera roto, ¿se vería distinto? Sí: imprime por volcán las filas del índice
   y las alertas; un volcán con alertas y 0 filas de índice delata el alias (A14).

Uso: python tif_modis_para_alertas.py RUTA_index.csv DIR_REF --desde 2026-03-01 --hasta 2026-10-16
"""
import collections
import csv
import io
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(r"C:\vrp-trabajo\s159-pruebas")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
import banco_paridad as bp  # noqa: E402

ALIAS_TIF = {"ChillanNevadosde": "NevadosDeChillan"}


def arg(n, d=None):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    idx, ref = Path(sys.argv[1]), Path(sys.argv[2])
    desde, hasta = arg("--desde", "2026-03-01"), arg("--hasta", "2026-10-16")
    filas_idx = [f for f in csv.DictReader(idx.open(encoding="utf-8")) if f["sensor"] == "MODIS"]
    vistos, tif = set(), collections.defaultdict(list)
    for f in sorted(filas_idx, key=lambda f: f["captured_at_utc"]):
        primera = f["md5"] not in vistos
        vistos.add(f["md5"])
        if not f["acquisition_utc"]:
            continue
        v = ALIAS_TIF.get(f["volcano"], f["volcano"])
        t = datetime.strptime(f["acquisition_utc"][:16], "%Y-%m-%dT%H:%M")
        tif[v].append((t, primera, f["tif_path"]))
    print("filas de índice MODIS con hora de adquisición, por volcán:", {k: len(v) for k, v in sorted(tif.items())})
    filas = cargar_referencia_unificada(ref / "registro_vrp_consolidado.csv", ref / "registro_vrp_ocr.csv")
    alertas = [f for f in filas if f["sensor_bucket"] == "MODIS" and bp.es_alerta(f["tipo"])
               and desde <= f["fecha_utc"][:10] <= hasta]
    print(f"filas de alerta MODIS de MIROVA {desde} a {hasta} (día y noche, sin deduplicar): {len(alertas)}")
    cuenta = collections.Counter()
    ejemplos = []
    for f in alertas:
        t = datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M")
        en_tramo = datetime(2026, 5, 9) <= t <= datetime(2026, 9, 22, 23, 59)
        cand = [x for x in tif.get(f["volcano"], []) if abs((x[0] - t).total_seconds()) <= 300]
        prot = (f["vrp_mw"] or 0) >= 1.0
        clave = ("protegida" if prot else "bajo1", "en_tramo_tif" if en_tramo else "fuera_tramo")
        cuenta[clave] += 1
        if cand:
            cuenta[clave + ("con_tif",)] += 1
            if any(x[1] for x in cand):
                cuenta[clave + ("con_tif_md5_nuevo",)] += 1
            if len(ejemplos) < 8:
                ejemplos.append((f["volcano"], f["fecha_utc"][:16], f["vrp_mw"], f.get("dist_km"), cand[0][2]))
    for k in sorted(cuenta):
        print("  ", k, cuenta[k])
    print("ejemplos:")
    for e in ejemplos:
        print("  ", e)


if __name__ == "__main__":
    main()
