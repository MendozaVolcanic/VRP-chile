"""S130 · Cuánto oculta el piso VRP en el dashboard.

POR QUE: el bloque de arranque S130 heredó de S129 la afirmación "el piso pone en
cero record.vrp_mw, que el dashboard NO muestra". Trazando el frontend
(index.html:1372) resulta que `isValidDetection()` arranca con `(r.vrp_mw ?? 0) > 0`
y sólo cae a `triggered_test1` como segundo camino. Un record pisado SIN
triggered_test1 desaparece de todos los paneles que usan ese helper (curva VRE,
comparación vs MIROVA, tabla NRT, conteos por distancia).

Este script mide, sobre los JSON operacionales, cuántos records fueron pisados y
cuántos de esos quedan invisibles. Persiste el resultado (regla S91: ningún número
se transcribe a mano).
"""
import json
import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "mirova_equivalent"
OUT = pathlib.Path(__file__).parent / "resultado_piso.json"

# Los 11 Tier A (los que tienen data y alimentan el dashboard)
TIER_A = [
    "Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima",
    "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
    "Tupungatito", "Villarrica",
]


def sensor_bucket(sensor: str) -> str:
    """Convención del proyecto (A48): VIIRS_* sin sufijo = I-band 375 m."""
    if "750" in sensor:
        return "VIIRS750"
    if "MODIS" in sensor:
        return "MODIS"
    if sensor.startswith("VIIRS"):
        return "VIIRS375"
    return "otro"


def main() -> int:
    total = 0
    pisados = 0
    # el que importa: pisado Y sin el segundo camino de isValidDetection()
    invisibles = 0
    por_vol = defaultdict(lambda: {"total": 0, "pisados": 0, "invisibles": 0})
    por_sensor = defaultdict(lambda: {"total": 0, "pisados": 0, "invisibles": 0})
    raws = []

    for vol in TIER_A:
        p = DATA / f"{vol}.json"
        if not p.exists():
            print(f"[WARN] falta {p}", file=sys.stderr)
            continue
        recs = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(recs, dict):
            recs = recs.get("records", [])
        for r in recs:
            total += 1
            b = sensor_bucket(r.get("sensor", ""))
            por_vol[vol]["total"] += 1
            por_sensor[b]["total"] += 1
            raw = r.get("diag_vrp_raw_mw")
            if raw is None:
                continue
            pisados += 1
            por_vol[vol]["pisados"] += 1
            por_sensor[b]["pisados"] += 1
            raws.append(raw)
            # replica exacta de isValidDetection(r) del frontend
            if not ((r.get("vrp_mw") or 0) > 0) and r.get("triggered_test1") is not True:
                invisibles += 1
                por_vol[vol]["invisibles"] += 1
                por_sensor[b]["invisibles"] += 1

    raws.sort()
    res = {
        "definicion": (
            "pisados = records con diag_vrp_raw_mw presente (el piso por sensor de "
            "store.py:465 les puso vrp_mw=0). invisibles = subconjunto de pisados que "
            "ademas falla isValidDetection() del frontend (index.html:1372), o sea "
            "vrp_mw<=0 Y triggered_test1 != true: esos NO cuentan como deteccion en "
            "curva VRE, comparacion MIROVA, tabla NRT ni conteos por distancia."
        ),
        "fuente": "data/mirova_equivalent/<11 Tier A>.json",
        "total_records": total,
        "pisados": pisados,
        "pisados_pct": round(100 * pisados / total, 3) if total else 0.0,
        "invisibles": invisibles,
        "invisibles_pct_del_total": round(100 * invisibles / total, 3) if total else 0.0,
        "invisibles_pct_de_pisados": round(100 * invisibles / pisados, 1) if pisados else 0.0,
        "vrp_crudo_pisado_mw": {
            "min": raws[0] if raws else None,
            "mediana": raws[len(raws) // 2] if raws else None,
            "max": raws[-1] if raws else None,
        },
        "por_volcan": dict(por_vol),
        "por_sensor": dict(por_sensor),
    }
    OUT.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items()
                      if k not in ("por_volcan", "definicion")}, indent=2, ensure_ascii=False))
    print("\npor volcan:")
    for v, d in sorted(por_vol.items(), key=lambda kv: -kv[1]["invisibles"]):
        print(f"  {v:24s} total={d['total']:6d}  pisados={d['pisados']:5d}  invisibles={d['invisibles']:5d}")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
