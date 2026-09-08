"""S136 - tests del evaluador del test de conformidad A6 (Villarrica, 24-jun-2009).

POR QUE ESTOS TESTS. En esta misma sesion el evaluador del probe de 3 brazos imprimio su
desenlace DESPUES de declarar invalido el run, contradiciendo su propio criterio, y el numero
quedo escrito. El criterio pre-registrado tiene que poder DETENER al evaluador, no solo
advertir. Estos tests atan esa propiedad con escenas sinteticas, antes de que el probe corra
con datos reales: asi el criterio no se puede reinterpretar despues de ver los resultados.

Criterio: docs/PREREGISTRO_CONFORMIDAD_A6_S136.md
"""
import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


def _cargar_modulo():
    """Importa el probe sin ejecutar main() ni tocar la red."""
    sys.path.insert(0, str(RAIZ))
    sys.path.insert(0, str(RAIZ / "scripts"))
    ruta = RAIZ / "experiments" / "_s136" / "conformidad_a6.py"
    spec = importlib.util.spec_from_file_location("conformidad_a6", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _cargar_modulo()


VOL = {"inner_radius_km": 5.0, "vent_lat": -39.420227, "vent_lon": -71.939876}


def _fila(nti, vrp=0.5, d_crater=0.4, d_lago=40.0):
    return {"granule": "g", "inicio": "2009-06-24 05:00:00", "nocturna": True,
            "nti_max": nti, "vrp_pc_mw": vrp,
            "dist_crater_km": d_crater, "dist_lago_km": d_lago}


def test_la_banda_de_control_es_la_del_preregistro(mod):
    """El paper entrega un solo numero, NTI ~ -0,93. La banda lo contiene."""
    assert mod.BANDA_CONTROL == (-0.97, -0.85)
    assert mod.BANDA_CONTROL[0] <= mod.NTI_PAPER <= mod.BANDA_CONTROL[1]
    assert mod.FECHA == "2009-06-24"


def test_sin_pasadas_nocturnas_es_indeterminado_y_no_emite_desenlace(mod, capsys):
    """El pipeline es night-only; si la fecha solo tuvo pasadas diurnas NO es un fallo nuestro."""
    mod.evaluar([{"granule": "g", "nocturna": False, "motivo": "diurna"}], VOL)
    out = capsys.readouterr().out
    assert "INDETERMINADO" in out
    assert "CONFORME" not in out.replace("NO CONFORME", "")
    assert "DESENLACE" not in out


def test_control_fallido_DETIENE_el_evaluador(mod, capsys):
    """La leccion del probe de 3 brazos: el control tiene que detener, no solo advertir.

    Una escena cuyo nti_max esta lejos del del paper no es la escena del paper. Aunque los
    numeros de deteccion se vean perfectos, no se emite desenlace.
    """
    filas = [_fila(-0.40, vrp=1.0, d_crater=0.2)]   # deteccion impecable, escena equivocada
    mod.evaluar(filas, VOL)
    out = capsys.readouterr().out
    assert "INDETERMINADO POR CONTROL" in out
    assert "DESENLACE" not in out, "el desenlace no puede imprimirse tras un control fallido"


def test_conforme_cuando_detecta_la_cumbre_y_no_el_lago(mod, capsys):
    mod.evaluar([_fila(-0.93, vrp=0.5, d_crater=0.4, d_lago=40.0)], VOL)
    out = capsys.readouterr().out
    assert "control SUPERADO" in out
    assert ">>> CONFORME" in out
    assert "NO CONFORME" not in out


def test_falso_negativo_cuando_no_detecta_la_cumbre(mod, capsys):
    """El paper detecta una anomalia de NTI ~ -0,93; si nosotros no publicamos nada, es FN."""
    mod.evaluar([_fila(-0.93, vrp=0.0, d_crater=0.4)], VOL)
    out = capsys.readouterr().out
    assert "FALSO NEGATIVO" in out
    assert ">>> CONFORME" not in out


def test_cumulo_fuera_del_inner_radius_no_cuenta_como_cumbre(mod, capsys):
    """A93: la distancia decide, y se mide desde el crater. 9 km no es la cumbre."""
    mod.evaluar([_fila(-0.93, vrp=0.5, d_crater=9.0, d_lago=40.0)], VOL)
    assert "FALSO NEGATIVO" in capsys.readouterr().out


def test_falso_positivo_cuando_publica_sobre_el_lago(mod, capsys):
    """El paper: 'the warm lake surface almost disappears in the ETI map'.

    Con ENABLE_EXCLUDE_ZONES=False nada oculta el lago, asi que si aparece es nuestro ETI.
    """
    filas = [_fila(-0.93, vrp=0.5, d_crater=0.4, d_lago=40.0),
             _fila(-0.93, vrp=2.0, d_crater=30.0, d_lago=2.0)]
    mod.evaluar(filas, VOL)
    out = capsys.readouterr().out
    assert "FALSO POSITIVO" in out
    assert "A69" in out, "el desenlace debe nombrar el mecanismo que localiza"


def test_ambos_defectos_se_reportan_juntos(mod, capsys):
    """No detecta la cumbre Y publica el lago: las dos cosas, no la primera que aparezca."""
    mod.evaluar([_fila(-0.93, vrp=2.0, d_crater=30.0, d_lago=2.0)], VOL)
    out = capsys.readouterr().out
    assert "FALSO NEGATIVO" in out and "FALSO POSITIVO" in out


def test_el_lago_del_probe_es_el_declarado_en_volcanoes_yaml(mod):
    """El centro del lago no se inventa: sale de la zona declarada para Villarrica."""
    import yaml
    vc = yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))
    vil = next(v for v in vc["volcanoes"] if v["name"] == "Villarrica")
    zona = next(z for z in vil["exclude_zones"] if "Villarrica" in z["name"])
    assert (mod.LAGO[0], mod.LAGO[1]) == (zona["lat"], zona["lon"])
    assert mod.LAGO[2] == zona["radius_km"]


def test_el_probe_no_escribe_en_data(mod):
    """Read-only sobre el operacional: el probe no puede tocar data/."""
    src = (RAIZ / "experiments" / "_s136" / "conformidad_a6.py").read_text(encoding="utf-8")
    for prohibido in ("store.append_record", "data/mirova_equivalent", "append_record("):
        assert prohibido not in src, f"el probe no debe usar {prohibido}"
