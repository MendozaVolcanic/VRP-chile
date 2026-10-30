# -*- coding: utf-8 -*-
"""S162 V750-B, R4 (2026-11-03): cuenta las pasadas N-3 de la lista sellada al generar los objetivos (adenda 3 §3).

POR QUÉ. La adenda 3 (sellada, tag `s167-v750b-adenda3-sellada`) manda contar e informar las N-3 de la lista sellada
antes de leer cualquier resultado: son etiquetas de la referencia, no resultados, y la cuenta vigila que `alerta_tabla`
venga bien calculado (adenda 3 §5). Una N-3 sólo puede pesar donde es etiqueta protegida: alerta que decide
(`lab == "pos"`, `decide`), protegida, y en la ventana O (desde el 2026-06-13), porque en T una pasada sin alerta de la
tabla nunca decide.

La condición es la del lector sellado, no una copia: se toma `DEFINICION` de `adenda3/leer_n3_v750b.py` (exige el
sha256 LF de ese lector en el commit sellado) y se ejecuta para obtener `no_veta_n3`.
Uso: python contar_n3_v750b.py --objetivos <experiments/_s162_v750b/objetivos_v750b.json>
Salida: 0; 2 si el lector de la adenda 3 no es el sellado.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
LECTOR_A3 = AQUI.parent / "adenda3" / "leer_n3_v750b.py"
SHA_LECTOR_A3_LF = "fa6d61a7d1fd4bebbfe27f61ec81c925b4d1380aeef6bf38a9bb938dcb930d5e"   # tag s167-v750b-adenda3-sellada
FRONTERA_OCR = "2026-06-13"


def sha_lf(ruta):
    return hashlib.sha256(Path(ruta).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--objetivos", required=True)
    a = ap.parse_args()
    if sha_lf(LECTOR_A3) != SHA_LECTOR_A3_LF:
        print("RECHAZO: adenda3/leer_n3_v750b.py no es el sellado (tag s167-v750b-adenda3-sellada)")
        return 2
    spec = importlib.util.spec_from_file_location("leer_n3_sellado", LECTOR_A3)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ns = {}
    exec(m.DEFINICION, ns)
    no_veta_n3 = ns["no_veta_n3"]
    crudo = Path(a.objetivos).read_bytes()
    obj = json.loads(crudo.decode("utf-8"))
    print(f"lista: {a.objetivos} | sha256 {hashlib.sha256(crudo).hexdigest()} | {len(obj)} pasadas")
    prot = [o for o in obj if o.get("lab") == "pos" and o.get("decide") and o.get("protegida")]
    n3 = [o for o in prot if no_veta_n3(o)]
    n3_o = [o for o in n3 if o["hora_utc"] >= FRONTERA_OCR]
    print(f"protegidas que deciden: {len(prot)} | N-3 entre ellas: {len(n3)} (en O, donde pesan: {len(n3_o)})")
    print("N-3 en O por volcán:", dict(sorted(collections.Counter(o["volcan"] for o in n3_o).items())) or "ninguna")
    for o in sorted(n3_o, key=lambda o: (o["volcan"], o["hora_utc"])):
        print(f"   {o['volcan']} {o['hora_utc']} {o['sensor']} granule {o.get('granule')}")
    sin_tabla = [o for o in prot if not o.get("alerta_tabla")]
    print(f"control: protegidas que deciden sin alerta de la tabla {len(sin_tabla)}, de ellas Suomi NPP "
          f"{sum(o.get('sensor') == 'VIIRS_SNPP_750' for o in sin_tabla)} y NOAA "
          f"{sum(o.get('sensor') != 'VIIRS_SNPP_750' for o in sin_tabla)}; en T (no deberían decidir) "
          f"{sum(o['hora_utc'] < FRONTERA_OCR for o in sin_tabla)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
