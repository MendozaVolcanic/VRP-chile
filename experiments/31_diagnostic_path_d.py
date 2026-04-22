"""31_diagnostic_path_d.py — Verifica que Path D (dNTI contextual) esta firing.

Lee los JSONs de data/mirova_equivalent/ y cuenta cuantos records tienen
`n_dnti_ctx_path` o `diag_n_dnti_ctx_path` (dependiendo del sensor) con
valor > 0. Si hay 0 records con el campo, el fix P3.2 no se aplico. Si
hay records pero todos con 0, Path D no encontro nada (podria ser bug
o podria ser correcto si la escena no tiene anomalias contextuales).

Uso: python experiments/31_diagnostic_path_d.py
"""

import json
import sys
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "mirova_equivalent"


def main():
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print(f"{'Volcan':<22} {'Sensor':<20} {'N_records':>10} {'has_field':>10} "
          f"{'fired':>6} {'mean_px':>8} {'max_px':>6}")
    print("-" * 88)

    volcanoes = sorted(DATA_DIR.glob("*.json"))
    total_records = 0
    total_with_field = 0
    total_fired = 0

    for vfile in volcanoes:
        d = json.load(open(vfile, "r", encoding="utf-8"))
        recs = d.get("records", [])
        if not recs:
            continue
        by_sensor = {}
        for r in recs:
            s = r.get("sensor", "?")
            by_sensor.setdefault(s, []).append(r)
        for sensor, sr in sorted(by_sensor.items()):
            n = len(sr)
            # Field name varies: process_viirs/mod uses n_dnti_ctx_path,
            # process_modis uses diag_n_dnti_ctx_path.
            vals = []
            for r in sr:
                v = r.get("n_dnti_ctx_path")
                if v is None:
                    v = r.get("diag_n_dnti_ctx_path")
                if v is not None:
                    vals.append(int(v))
            has_field = len(vals)
            fired = sum(1 for v in vals if v > 0)
            mean_px = mean([v for v in vals if v > 0]) if fired else 0
            max_px = max(vals) if vals else 0
            total_records += n
            total_with_field += has_field
            total_fired += fired
            print(f"{vfile.stem:<22} {sensor:<20} {n:>10} {has_field:>10} "
                  f"{fired:>6} {mean_px:>8.1f} {max_px:>6}")

    print("-" * 88)
    print(f"Total records: {total_records}")
    print(f"Con campo Path D: {total_with_field} "
          f"({100*total_with_field/max(total_records,1):.0f}%)")
    print(f"Path D fired (>0 px): {total_fired} "
          f"({100*total_fired/max(total_with_field,1):.1f}% de los con campo)")
    if total_with_field == 0:
        print("\n>>> ALERTA: ningun record tiene el campo de Path D.")
        print("    Posibles causas:")
        print("    1. Ningun volcan fue reprocesado despues del commit P3.2.")
        print("    2. NRT corre con el codigo viejo (GitHub Actions no pusheado).")
        print("    3. Los records que habia eran pre-P3.2, habia que --overwrite.")
    elif total_fired == 0:
        print("\n>>> Path D no gatillo en ningun record.")
        print("    Puede ser correcto si no hubo anomalias contextuales, o un bug.")
        print("    Verificar manualmente con un granule de activity alta (Lascar 2026-04-21).")
    else:
        print(f"\n>>> OK: Path D esta firing en {total_fired} records.")


if __name__ == "__main__":
    main()
