"""S167: ventana de fechas de la sombra prospectiva de las vías «código MIROVA» (.github/workflows/sombra-codigo-mirova.yml).

POR QUÉ. Los tres pre-registros de fase 4 (V750-A §4.3, V375-E §3.3, MOD-D fase 4 §12.6) miden la sombra desde el
2026-11-03: Suomi NPP cesa el 2026-11-02 13:00 UTC y lo de después es otro régimen (programa por sensor, ventana P).
Un record de la carpeta de sombra anterior a esa fecha mezclaría los dos regímenes y nadie lo notaría al leer, así que
la fecha mínima se aplica aquí, antes de correr, y no se deja a cada lector.

QUÉ HACE. Imprime `INI FIN` (o nada, con salida 0, si todavía no toca correr):
  - modo normal (el que commitea): los mismos 8 días que el NRT (hoy y 7 atrás, scripts/run_pipeline.py
    default_date_window), recortados por abajo en la fecha mínima. Un despacho a mano puede pedir otra ventana
    (para rellenar un día que falló), pero nunca antes de la fecha mínima: eso sale con error 2.
  - modo medir (no commitea; sirve para medir el costo en el runner sobre una ventana pasada): la ventana pedida tal
    cual, sin fecha mínima, porque lo que corre ahí se descarta con el runner.

Uso: python scripts/ventana_sombra.py [--hoy AAAA-MM-DD] [--start A] [--end B] [--medir]
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta, timezone

FECHA_MINIMA = date(2026, 11, 3)
LOOKBACK_DIAS = 7   # el mismo de scripts/run_pipeline.py::default_date_window


def _fecha(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def ventana(hoy, start=None, end=None, medir=False, minima=FECHA_MINIMA, lookback=LOOKBACK_DIAS):
    """(ini, fin) a correr, o None si todavía no toca. ValueError si la ventana pedida no se puede correr."""
    if bool(start) != bool(end):
        raise ValueError("start y end van juntos")
    if start:
        ini, fin = _fecha(start), _fecha(end)
        if fin < ini:
            raise ValueError(f"end {fin} antes que start {ini}")
        if not medir and ini < minima:
            raise ValueError(f"la sombra no escribe antes del {minima} (otro régimen); pediste {ini}")
        return ini, fin
    if medir:
        raise ValueError("el modo medir pide start y end explícitos")
    if hoy < minima:
        return None
    return max(minima, hoy - timedelta(days=lookback)), hoy


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--hoy", default=None, help="fecha UTC de hoy (por defecto, la del reloj)")
    ap.add_argument("--start", default="")
    ap.add_argument("--end", default="")
    ap.add_argument("--medir", action="store_true")
    a = ap.parse_args(argv)
    hoy = _fecha(a.hoy) if a.hoy else datetime.now(timezone.utc).date()
    try:
        v = ventana(hoy, a.start or None, a.end or None, a.medir)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if v is None:
        print(f"todavía no: la sombra parte el {FECHA_MINIMA} y hoy es {hoy}", file=sys.stderr)
        return 0
    print(f"{v[0]:%Y-%m-%d} {v[1]:%Y-%m-%d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
