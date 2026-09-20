"""S147 - el laboratorio no puede ver MENOS que el operacional.

EL DEFECTO QUE LO ORIGINA. El perfil `experimental` existe para ver la senal debil real que
MIROVA no publica, y su unica diferencia declarada con el operacional eran tres pisos de
magnitud. Cuando S124 los escribio (0,005 / 0,05 / 0,02 MW) el operacional tenia pisos MAS
ALTOS (0,02 / 0,15 / 0,05), asi que bajarlos tenia sentido. En S130 el operacional bajo sus
pisos a 0,0 y nadie actualizo el laboratorio: durante 17 sesiones el perfil declarado
"laboratorio" fue estrictamente MAS CIEGO que el instrumento que estudiaba, y el comentario de
`pipeline/store.py` siguio diciendo lo contrario.

Nadie recibio un error. El defecto no rompe nada: produce un laboratorio que ve menos, que es
justo lo que no se nota mirando una pantalla.

QUE MIDE ESTE GUARD, y que no:
- SI mide que ningun piso de magnitud del laboratorio sea mayor que el del operacional, para los
  tres sensores. La comparacion se hace resolviendo los perfiles como los resuelve el codigo
  (`pipeline.profile` con VRP_PROFILE), NUNCA leyendo el texto del YAML: en este proyecto ya paso
  que una clave escrita en la seccion equivocada se leyera siempre apagada (A89).
- NO mide que el laboratorio sea mas sensible. Hoy es IGUAL al operacional, y eso es correcto y
  deliberado: su diferenciacion real esta disenada y sin implementar.
- NO cubre otros parametros. Un umbral de deteccion mas estricto en el laboratorio seria el mismo
  error por otra puerta, pero no todos los parametros son monotonos en "ver mas", asi que
  generalizar a ciegas daria falsos rojos. Cuando se implemente la sensibilidad por zona, este
  guard se extiende con los parametros que SI lo son.

LAS DOS PREGUNTAS DEL INSTRUMENTO:
1. Si el defecto volviera, esto fallaria? SI: el caso de control de abajo comprueba que la
   comparacion detecta un piso mayor.
2. Si el instrumento estuviera muerto? El primer test exige que los dos perfiles resuelvan y que
   los tres atributos EXISTAN, asi que un fallo de resolucion no pasa como "todo bien".
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PISOS = ("MIN_VRP_MW_VIIRS375", "MIN_VRP_MW_VIIRS750", "MIN_VRP_MW_MODIS")


def _resolver(perfil: str) -> dict:
    """Vuelca los pisos efectivos de un perfil en un subproceso propio.

    Subproceso porque `pipeline.profile` lee la variable de entorno al importarse: dos perfiles en
    el mismo proceso devolverian el primero que se importo.
    """
    codigo = (
        "import json, pipeline.profile as p; "
        f"print(json.dumps({{k: getattr(p, k) for k in {list(PISOS)!r}}}))"
    )
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    salida = subprocess.run([sys.executable, "-c", codigo], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=120)
    assert salida.returncode == 0, f"no resolvio el perfil {perfil}: {salida.stderr[-400:]}"
    ultima = [l for l in salida.stdout.splitlines() if l.strip().startswith("{")]
    assert ultima, f"el volcado de {perfil} no trajo JSON: {salida.stdout[-300:]}"
    return json.loads(ultima[-1])


LABORATORIOS = ("experimental", "experimental_lowT", "experimental_ndc_focus")


@pytest.fixture(scope="module")
def pisos():
    d = {"mirova_equivalent": _resolver("mirova_equivalent")}
    for lab in LABORATORIOS:
        d[lab] = _resolver(lab)
    return d


def test_los_perfiles_resuelven_y_traen_los_tres_pisos(pisos):
    """Control del instrumento: sin esto, un fallo de resolucion pasaria por verde."""
    for perfil, d in pisos.items():
        assert set(d) == set(PISOS), f"{perfil} no trajo los tres pisos: {sorted(d)}"
        for k, v in d.items():
            assert isinstance(v, (int, float)), f"{perfil}.{k} no es un numero: {v!r}"


@pytest.mark.parametrize("laboratorio", LABORATORIOS)
@pytest.mark.parametrize("piso", PISOS)
def test_el_laboratorio_no_es_mas_ciego_que_el_operacional(pisos, laboratorio, piso):
    """El corazon del guard, sobre los TRES laboratorios vivos.

    `experimental_ndc_focus` tenia el mismo defecto y por la misma causa: su cabecera declara
    "UNA sola diferencia con la replica: el umbral", y esa diferencia apuntaba al reves desde
    S130.
    """
    lab = pisos[laboratorio][piso]
    op = pisos["mirova_equivalent"][piso]
    assert lab <= op, (
        f"el laboratorio {laboratorio} es MAS CIEGO que el operacional en {piso}: "
        f"{lab} contra {op}. Un perfil de laboratorio existe para ver la senal debil que el "
        "operacional descarta; un piso mayor lo convierte en lo contrario, y no da ningun "
        "error al correr.")


def test_control_un_piso_mayor_rompe_la_comparacion():
    """Control positivo: si la comparacion no pudiera ver el defecto, no serviria de nada."""
    op = {"MIN_VRP_MW_VIIRS375": 0.0}
    lab_sano = {"MIN_VRP_MW_VIIRS375": 0.0}
    lab_roto = {"MIN_VRP_MW_VIIRS375": 0.005}   # el valor real que tuvo entre S130 y S147
    assert lab_sano["MIN_VRP_MW_VIIRS375"] <= op["MIN_VRP_MW_VIIRS375"]
    assert not (lab_roto["MIN_VRP_MW_VIIRS375"] <= op["MIN_VRP_MW_VIIRS375"])
