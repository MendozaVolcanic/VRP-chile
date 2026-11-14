# -*- coding: utf-8 -*-
"""¿Queda alguna pasada VIIRS 750 de Cordón Caulle publicada con una región sensible distinta de `crater`? (S184)

POR QUÉ. La serie se pasa a `crater` en dos pasos: `aplicar_pcc_v750.sh` reemplaza hasta el último día del reproceso
(2026-11-13) y un despacho de `nrt.yml` con `overwrite` reescribe desde el 2026-11-14 hasta el día del merge de #999.
Entre medio, el NRT siguió escribiendo con `sens` y una descarga fallida (FileExistsError en runners de AWS) puede
dejar una pasada sin reescribir sin avisar. Este chequeo es la única prueba de que la serie quedó con una sola caja:
cuenta por caja y lista las que no son `crater`. Sale con 1 si queda alguna, con 0 si no.

Uso: python chequeo_caja.py <PuyehueCordonCaulle.json> [--desde 2025-02-15]
"""
import argparse
import collections
import json
import sys


def contar(store: dict, desde: str):
    v750 = [r for r in store.get("records", []) if str(r.get("sensor") or "").startswith("VIIRS")
            and str(r.get("sensor") or "").endswith("_750") and str(r.get("datetime_utc") or "")[:10] >= desde]
    caja = collections.Counter((r.get("diag_codigo_mirova") or {}).get("roi") for r in v750)
    otras = [(r.get("datetime_utc"), r.get("sensor"), (r.get("diag_codigo_mirova") or {}).get("roi"))
             for r in v750 if (r.get("diag_codigo_mirova") or {}).get("roi") != "crater"]
    return len(v750), caja, otras


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("serie")
    ap.add_argument("--desde", default="2025-02-15")
    a = ap.parse_args(argv)
    n, caja, otras = contar(json.load(open(a.serie, encoding="utf-8")), a.desde)
    print(f"VIIRS 750 de Cordón Caulle desde {a.desde}: {n} pasadas; por caja {dict(caja)}")
    for o in otras[:50]:
        print("  sin crater:", *o)
    if len(otras) > 50:
        print(f"  ... y {len(otras) - 50} más")
    return 1 if otras else 0


if __name__ == "__main__":
    raise SystemExit(main())
