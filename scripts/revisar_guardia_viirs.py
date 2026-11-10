"""S176: revisa que una corrida de la guardia K de los dos VIIRS (.github/workflows/guardia-k-viirs.yml) haya producido K.

POR QUÉ. La guardia es K corriendo aparte de la vía «código MIROVA» en VIIRS 375 y VIIRS 750 (diseño
docs/superpowers/specs/2026-11-08-encendido-v375e-design.md, decisiones 2 y 7). Su vigilancia dispara la reversión cuando
la guardia publica una alerta protegida que producción calla. Una guardia muerta, o que corriera la vía, no da error:
da VERDE, porque nunca publica algo que producción calle. Esta es la misma revisión de la guardia de MODIS
(scripts/revisar_guardia_modis.py), que se reutiliza por import, con los dos sensores: si un VIIRS deja de escribir
aunque el otro siga vivo, ese sensor quedaría sin vigilar, así que cada uno se exige por separado.

Uso: python scripts/revisar_guardia_viirs.py --json data/guardia_k_viirs/<Volcan>.json --log pipeline.log
       --cobertura-json cobertura.json --ini A --fin B --desde-utc AAAA-MM-DDTHH:MM:SSZ --sha <GITHUB_SHA>
"""
from __future__ import annotations

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))
import revisar_guardia_modis as rgm  # noqa: E402

PERFIL = "guardia_k_viirs"
SENSORES = ("VIIRS375", "VIIRS750")


def revisar(registros, log_txt, ini, fin, desde_utc, cobertura, sha=None, errores_lectura=()):
    return rgm.revisar(registros, log_txt, ini, fin, desde_utc, cobertura, sha=sha, errores_lectura=errores_lectura,
                       sensores=SENSORES, perfil=PERFIL)


def main(argv=None):
    return rgm.main(argv, sensores=SENSORES, perfil=PERFIL, titulo="VIIRS 375 y VIIRS 750")


if __name__ == "__main__":
    sys.exit(main())
