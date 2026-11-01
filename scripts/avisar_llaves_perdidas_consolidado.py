# -*- coding: utf-8 -*-
"""Aviso S160 (hallazgo 245 de docs/AUDIT_S160.md): la copia nueva del consolidado de MIROVA perdió llaves
que la copia vigente tenía.

POR QUÉ. El registro de MIROVA sólo crece: una pasada que ya se registró no deja de haber ocurrido. Pero el
CSV del scraper Mirova-v1 a veces llega con filas de menos por una carrera de sus propios workflows, y la
copia horaria las propagaba sin decir nada: 7 encogimientos en 64 días, 1.948 filas que salieron y no
volvieron, 14 de ellas alertas protegidas (experiments/_s160_audit/f3/ y v3/). Contar filas no basta (uno de
los siete encogimientos no perdió filas y el archivo crece mientras pierde llaves viejas): se comparan las
llaves (Volcan, Sensor, Fecha_Satelite_UTC).

Avisa, no rechaza (decisión de Nicolás, 2026-10-22): rechazar una copia más corta puede dejar congelada la
referencia. La copia nueva entra igual; este script escribe `llaves_perdidas=N` en $GITHUB_OUTPUT y el
último paso del workflow deja la corrida en rojo si N > 0, con la lista en el resumen.

Uso: python scripts/avisar_llaves_perdidas_consolidado.py <copia_vigente.csv> <copia_nueva.csv>
Siempre sale con 0 (el rojo lo pone el workflow). Sin copia vigente legible no hay con qué comparar: lo
dice y escribe llaves_perdidas=0.
"""
import csv
import io
import os
import sys
from pathlib import Path

LLAVE = ("Volcan", "Sensor", "Fecha_Satelite_UTC")
TIPOS_ALERTA = ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR")  # los de scripts/clase_mirova.py
UMBRAL_PROTEGIDA_MW = 1.0                                # scripts/clase_mirova.py, lectura A


def _filas(ruta):
    texto = Path(ruta).read_bytes().decode("utf-8", "replace")
    lector = csv.DictReader(io.StringIO(texto))
    if any(c not in (lector.fieldnames or []) for c in LLAVE):
        return None
    return {tuple(f[c] for c in LLAVE): f for f in lector}


def _vrp(f):
    try:
        return float(f.get("VRP_MW") or "nan")
    except ValueError:
        return float("nan")


def comparar(vieja, nueva):
    """Devuelve (perdidas, alertas_perdidas, protegidas_perdidas) como listas de filas, o None si no se
    puede leer alguna de las dos copias."""
    a, b = _filas(vieja), _filas(nueva)
    if a is None or b is None:
        return None
    perdidas = [a[k] for k in sorted(set(a) - set(b))]
    alertas = [f for f in perdidas if f.get("Tipo_Registro") in TIPOS_ALERTA]
    protegidas = [f for f in alertas if _vrp(f) >= UMBRAL_PROTEGIDA_MW]
    return perdidas, alertas, protegidas


def _salida(clave, valor):
    ruta = os.environ.get("GITHUB_OUTPUT")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as fh:
            fh.write(f"{clave}={valor}\n")


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 0
    vieja, nueva = argv[1], argv[2]
    if not Path(vieja).exists():
        print(f"sin copia vigente ({vieja}): no hay con qué comparar")
        _salida("llaves_perdidas", 0)
        return 0
    r = comparar(vieja, nueva)
    if r is None:
        print("no se pudieron leer las columnas de la llave en alguna copia: la guarda de llaves lo dirá")
        _salida("llaves_perdidas", 0)
        return 0
    perdidas, alertas, protegidas = r
    _salida("llaves_perdidas", len(perdidas))
    if not perdidas:
        print("consolidado: ninguna llave de la copia vigente se perdió")
        return 0
    print(f"::warning title=Consolidado perdió llaves::{len(perdidas)} pasadas de la copia vigente no están en la "
          f"nueva ({len(alertas)} alertas, {len(protegidas)} protegidas de 1 MW o más)")
    for f in (protegidas or alertas or perdidas)[:10]:
        print(f"  {f.get('Volcan')} {f.get('Sensor')} {f.get('Fecha_Satelite_UTC')} "
              f"{f.get('Tipo_Registro')} {f.get('VRP_MW')} MW")
    resumen = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumen:
        with open(resumen, "a", encoding="utf-8") as fh:
            fh.write(f"### El consolidado de MIROVA perdió {len(perdidas)} llaves\n"
                     f"{len(alertas)} alertas, {len(protegidas)} protegidas. La copia nueva entró igual "
                     "(avisa, no rechaza).\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
