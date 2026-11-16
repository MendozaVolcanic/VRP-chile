"""S173 (hallazgo 209, V2-02): hace fallar el job del NRT si un gránulo MODIS terminó en `ERROR processing`.
S179 (regla de VIIRS §5, VPR967-05 (a)): lo mismo para VIIRS 375 y VIIRS 750 cuando su vía está encendida.

POR QUÉ. Con la vía «código MIROVA» encendida en un sensor, una excepción de la vía en un gránulo no cae a K:
scripts/run_pipeline.py la atrapa (`except Exception`), imprime `ERROR processing <archivo>: <error>` y sigue con el
gránulo siguiente. Esa pasada queda sin record de producción y el job sale verde. La vigilancia de la guardia K lo
vería recién a las 24 h (protegida sin record, regla §4.4 (a)) o a los 3 días (frescura). Con este paso el job queda
rojo el mismo día y lo ve el monitor del NRT. No revierte nada: se investiga (reglas de reversión de MODIS,
experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md §4.4 (a), y de VIIRS,
experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md §4.4 (a) y §5).

QUÉ HACE. Lee el log de la corrida (el `pipeline.log` que nrt.yml llena con `tee`) y busca líneas
`ERROR processing <archivo>`. Clasifica cada archivo por sensor con los mismos nombres con que run_pipeline separa los
L1B: MODIS (`MOD021KM` de Terra, `MYD021KM` de Aqua), VIIRS 375 (`VNP02IMG`, `VJ102IMG`, `VJ202IMG`) y VIIRS 750
(`VNP02MOD`, `VJ102MOD`, `VJ202MOD`). Hacen fallar el job los errores de MODIS (como desde S173) y los de cada sensor
VIIRS cuya vía está encendida en el perfil de producción (`ENABLE_V375_CODIGO_MIROVA`, `ENABLE_V750_CODIGO_MIROVA` de
pipeline/profile.py con VRP_PROFILE=mirova_equivalent; A89: el flag efectivo, no el YAML). Así el paso sigue al
encendido y al revert de cada sensor sin tocar este archivo. Los demás errores se cuentan y se informan sin hacer
fallar. Si el log no existe, FALLA (no se puede decir que no hubo errores sin mirarlos). Si el perfil no se puede leer,
los errores de VIIRS hacen fallar (no saber si la vía está encendida no es lo mismo que saber que está apagada).
Salida 0 = sin errores que hagan fallar, 1 = con alguno o sin log.

Uso: python scripts/revisar_errores_modis_nrt.py --log pipeline.log [--volcan Lascar]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# `ERROR processing ` y después el nombre del archivo hasta los dos puntos que run_pipeline pone antes del error.
_ERROR = re.compile(r"(?<![A-Za-z0-9_])ERROR processing\s+([^\s:]+)")
# L1B por sensor, como token propio del nombre (A92: no por subcadena suelta).
_L1B = {
    "MODIS": re.compile(r"(?<![A-Za-z0-9])M[OY]D021KM(?![A-Za-z0-9])"),
    "VIIRS375": re.compile(r"(?<![A-Za-z0-9])(?:VNP02IMG|VJ102IMG|VJ202IMG)(?![A-Za-z0-9])"),
    "VIIRS750": re.compile(r"(?<![A-Za-z0-9])(?:VNP02MOD|VJ102MOD|VJ202MOD)(?![A-Za-z0-9])"),
}
_L1B_MODIS = _L1B["MODIS"]


def sensor_de(archivo: str) -> str:
    for sensor, rx in _L1B.items():
        if rx.search(archivo):
            return sensor
    return "otro"


def clasificar_por_sensor(log_txt: str) -> dict[str, list[str]]:
    """Líneas de error por sensor: {"MODIS": [...], "VIIRS375": [...], "VIIRS750": [...], "otro": [...]}."""
    out = {"MODIS": [], "VIIRS375": [], "VIIRS750": [], "otro": []}
    for ln in log_txt.splitlines():
        m = _ERROR.search(ln)
        if m:
            out[sensor_de(m.group(1))].append(ln.strip())
    return out


def clasificar(log_txt: str) -> tuple[list[str], list[str]]:
    """Devuelve (líneas de error de MODIS, líneas de error de otros sensores). Forma de S173, se conserva."""
    d = clasificar_por_sensor(log_txt)
    return d["MODIS"], d["VIIRS375"] + d["VIIRS750"] + d["otro"]


def sensores_que_fallan(v375: bool | None, v750: bool | None) -> set[str]:
    """MODIS siempre; cada VIIRS si su vía está encendida. None (perfil ilegible) cuenta como encendida."""
    falla = {"MODIS"}
    if v375 is None or v375:
        falla.add("VIIRS375")
    if v750 is None or v750:
        falla.add("VIIRS750")
    return falla


def flags_produccion() -> tuple[bool | None, bool | None, str]:
    """(vía V375, vía V750, nota) del perfil de producción, leídos de pipeline.profile (A89)."""
    os.environ["VRP_PROFILE"] = "mirova_equivalent"   # el NRT de producción, no el perfil del entorno
    sys.path.insert(0, str(ROOT))
    try:
        import pipeline.profile as pp
        return bool(pp.ENABLE_V375_CODIGO_MIROVA), bool(pp.ENABLE_V750_CODIGO_MIROVA), "perfil leído"
    except Exception as e:  # noqa: BLE001
        return None, None, f"no se pudo leer el perfil ({type(e).__name__}: {e})"


_NOMBRE = {"MODIS": "MODIS", "VIIRS375": "VIIRS 375", "VIIRS750": "VIIRS 750"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--log", required=True)
    ap.add_argument("--volcan", default="")
    a = ap.parse_args(argv)
    sufijo = f" ({a.volcan})" if a.volcan else ""
    lg = Path(a.log)
    try:
        log_txt = lg.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"::error title=NRT sin log{sufijo}::no se pudo leer {a.log} ({type(e).__name__}); "
              "no se puede comprobar si hubo errores de la vía")
        return 1
    v375, v750, nota = flags_produccion()
    if v375 is None:
        print(f"::warning title=Perfil de producción ilegible{sufijo}::{nota}; los errores de VIIRS hacen fallar")
    falla = sensores_que_fallan(v375, v750)
    por = clasificar_por_sensor(log_txt)
    malos = [(s, ln) for s in ("MODIS", "VIIRS375", "VIIRS750") if s in falla for ln in por[s]]
    for s, ln in malos[:20]:
        print(f"::error title=Error en un granulo {_NOMBRE[s]}{sufijo}::{ln}")
    if len(malos) > 20:
        print(f"::error title=Error en un granulo{sufijo}::y {len(malos) - 20} mas")
    no_fallan = sum(len(por[s]) for s in ("VIIRS375", "VIIRS750") if s not in falla) + len(por["otro"])
    resumen = (f"gránulos MODIS con ERROR processing: {len(por['MODIS'])}; "
               f"VIIRS 375: {len(por['VIIRS375'])} (vía {'encendida' if 'VIIRS375' in falla else 'apagada'}); "
               f"VIIRS 750: {len(por['VIIRS750'])} (vía {'encendida' if 'VIIRS750' in falla else 'apagada'}); "
               f"de otros sensores (no hacen fallar): {no_fallan}")
    print(resumen)
    ruta = os.environ.get("GITHUB_STEP_SUMMARY")
    if ruta and malos:
        try:
            with open(ruta, "a", encoding="utf-8") as fh:
                fh.write("### Error en un gránulo con la vía%s\n\n%s. Esa pasada quedó sin record de producción "
                         "(la vía no cae a K). Investigar según §4.4 (a) de la regla de reversión del sensor.\n\n"
                         "```\n%s\n```\n" % (sufijo, resumen, "\n".join(ln for _, ln in malos[:20])))
        except OSError:
            pass
    return 1 if malos else 0


if __name__ == "__main__":
    sys.exit(main())
