# -*- coding: utf-8 -*-
"""F5 medicion 6. Cobertura del brazo de control del A/B de D25 (run 39530508296, rama s146-ab/39530508296 @4b6d7f5f,
la que dejo el intento 1) contra produccion (data/mirova_equivalent), ventana V1 2026-08-29 a 2026-10-18, por volcan y
sensor VIIRS. Pasada = volcan|bucket|minuto. Las pasadas no dependen del detector, asi que produccion sirve de
referencia de cobertura (es lo que hace evaluar_d25.claves_cobertura cuando no hay historico, PREREGISTRO §7.1).
Instrumento 1: si al brazo le faltara un dia entero, esta medicion lo veria (cuenta por fecha). Instrumento 2: si los
archivos bajados estuvieran vacios, el total seria 0 y se imprime. Umbral del evaluador: MAX_FALTA_COBERTURA = 0,05."""
import collections, io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp  # noqa
V = ("2026-08-29", "2026-10-18")
falt_dia = collections.Counter(); tot = 0
print("volcan               sensor    prod  brazo  faltan  frac   sobran | dias con faltantes")
for vol in bp.VOLS:
    a = json.load(open(RAIZ / "experiments/_s158_audit/f5/_rama" / ("ctrl_%s.json" % vol), encoding="utf-8"))["records"]
    b = json.load(open(RAIZ / "data/mirova_equivalent" / (vol + ".json"), encoding="utf-8"))["records"]
    for s in ("VIIRS375", "VIIRS750"):
        ka = {r["datetime_utc"][:16] for r in a if bp.bucket(r.get("sensor")) == s and V[0] <= r["datetime_utc"][:10] <= V[1]}
        kb = {r["datetime_utc"][:16] for r in b if bp.bucket(r.get("sensor")) == s and V[0] <= r["datetime_utc"][:10] <= V[1]}
        f = kb - ka; tot += len(ka)
        dias = collections.Counter(x[:10] for x in f)
        for d, n in dias.items():
            falt_dia[d] += n
        print("%-20s %-8s %5d %6d %7d %6.3f %6d | %s" % (vol, s, len(kb), len(ka), len(f), len(f) / len(kb) if kb else -1,
                                                       len(ka - kb), dict(sorted(dias.items()))))
print("total pasadas VIIRS en el brazo:", tot)
print("faltantes por dia (todos los volcanes):", dict(sorted(falt_dia.items())))
