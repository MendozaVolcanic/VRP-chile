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


# S193: `laboratorio` (paso 1 del plan docs/PLAN_EXPERIMENTAL_S190.md) entra a la comparación de pisos como los otros.
LABORATORIOS = ("experimental", "experimental_lowT", "experimental_ndc_focus", "laboratorio")


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


# ------------------------------------------------------------------------------------------------ S193, G8
# La sensibilidad por zona que este docstring dejaba prevista ya tiene parámetro (perfil `laboratorio`, plan
# docs/PLAN_EXPERIMENTAL_S190.md §6 y docs/superpowers/plans/2026-11-21-laboratorio-paso1.md): el multiplicador de
# sigma de la zona A en el criterio contextual nocturno de la vía. Es monótono en «ver más» (menor multiplicador, más
# alertas), así que entra aquí: el de la zona A no puede ser mayor que el de la región sensible del .m (s2 nocturno),
# que es lo que producción ya usa en el cráter. Hoy vale null (el paso 3 lo elige); la comparación queda armada.
import ast  # noqa: E402
import re  # noqa: E402


def _s2_nocturno_del_detector() -> float:
    """s2 nocturno leído de detectar_mirova (no copiado aquí: si el .m portado cambia, la vara cambia con él)."""
    src = (ROOT / "pipeline" / "mirova_v750_codigo.py").read_text(encoding="utf-8")
    m = re.search(r"if dayflag == 0:[^\n]*\n\s*u_abs, s1, s2, n1, n2, e1, e2 = ([^\n#]+)", src)
    assert m, "no encontré los umbrales nocturnos de detectar_mirova"
    return float(ast.literal_eval("(" + m.group(1).strip() + ")")[2])


def _zona_a_del_laboratorio(perfil: str = "laboratorio") -> dict:
    codigo = "import pipeline.profile as p; print('@@' + repr(p.LAB_ZONA_A))"
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    salida = subprocess.run([sys.executable, "-c", codigo], cwd=ROOT, env=env, capture_output=True, text=True,
                            timeout=120)
    assert salida.returncode == 0, f"no resolvio el laboratorio: {salida.stderr[-400:]}"
    lineas = [l for l in salida.stdout.splitlines() if l.startswith("@@")]
    assert lineas, salida.stdout[-300:]
    return ast.literal_eval(lineas[-1][2:])


def _no_mas_ciego_en_zona_a(valor, s2) -> bool:
    return valor is None or valor <= s2


def test_s193_la_zona_a_no_es_mas_estricta_que_la_region_sensible():
    s2 = _s2_nocturno_del_detector()
    assert s2 == 5.0, f"control: el s2 nocturno del .m es 5 (l. 177-199); se leyó {s2}"
    zona = _zona_a_del_laboratorio()
    assert zona.get("parametro") == "sigma_contextual_nocturno", zona
    assert _no_mas_ciego_en_zona_a(zona.get("valor"), s2), (
        f"la zona A del laboratorio tiene multiplicador {zona.get('valor')}, mayor que el s2 nocturno de la vía ({s2}): "
        "el laboratorio vería MENOS que producción justo en el cráter")


# S195 (paso 3): los 9 brazos del barrido (perfiles _s195_lab_s50 a _s195_lab_s10) encienden la zona con valor; ninguno
# puede pasar del s2 nocturno, y el brazo s = 5,0 lo iguala (control del barrido sellado).
@pytest.mark.parametrize("perfil", ["_s195_lab_s%02d" % t for t in (50, 45, 40, 35, 30, 25, 20, 15, 10)])
def test_s195_ningun_brazo_del_barrido_es_mas_estricto_que_la_region_sensible(perfil):
    s2 = _s2_nocturno_del_detector()
    zona = _zona_a_del_laboratorio(perfil)
    assert zona.get("parametro") == "sigma_contextual_nocturno", zona
    assert zona.get("valor") is not None, f"control: el brazo {perfil} declara su valor"
    assert _no_mas_ciego_en_zona_a(zona.get("valor"), s2), (perfil, zona.get("valor"), s2)


def test_s193_control_un_multiplicador_mayor_rompe_la_comparacion():
    assert _no_mas_ciego_en_zona_a(None, 5.0) and _no_mas_ciego_en_zona_a(3.0, 5.0)
    assert not _no_mas_ciego_en_zona_a(6.0, 5.0)
