"""S136 - tests de la bateria de conformidad contra el Apendice A de Coppola 2016a.

POR QUE. Los tres casos NEGATIVOS del apendice son los que miden sobre-deteccion contra la
referencia del autor, y por eso el evaluador tiene que tratarlos al reves que los positivos: en
un negativo, publicar algo es el FALLO. Un evaluador que se equivoque de signo convertiria el
hallazgo mas valioso de la bateria en un "todo bien". Estos tests fijan los dos signos, y el
control de validez que puede detener un caso, ANTES de correr con datos reales.
"""
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
YML = RAIZ / "experiments" / "_s136" / "apendice_a.yaml"


@pytest.fixture(scope="module")
def mod():
    sys.path.insert(0, str(RAIZ))
    sys.path.insert(0, str(RAIZ / "scripts"))
    ruta = RAIZ / "experiments" / "_s136" / "conformidad_apendice.py"
    spec = importlib.util.spec_from_file_location("conformidad_apendice", ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def casos():
    return yaml.safe_load(YML.read_text(encoding="utf-8"))["casos"]


# ---------------------------------------------------------------- el conjunto de casos

def test_estan_los_nueve_casos_del_apendice(casos):
    assert len(casos) == 9
    assert {c["caso"] for c in casos} == {f"A{i}" for i in range(1, 10)}


def test_seis_positivos_y_tres_negativos(casos):
    """El paper detecta en seis escenas y deliberadamente no detecta en tres."""
    det = [c for c in casos if c["veredicto"] == "detecta"]
    neg = [c for c in casos if c["veredicto"] == "no_detecta"]
    assert len(det) == 6 and len(neg) == 3
    assert {c["name"] for c in neg} == {"Dubbi", "Tolbachik", "Stromboli"}


def test_cada_caso_tiene_lo_minimo_para_correr(casos):
    for c in casos:
        for k in ("name", "caso", "fecha", "veredicto", "lat", "lon", "gvp_id", "nota"):
            assert c.get(k) is not None, f"{c.get('caso')} sin {k}"
        assert -90 <= c["lat"] <= 90 and -180 <= c["lon"] <= 180
        assert 100000 <= c["gvp_id"] <= 999999, "gvp_id es un entero de 6 cifras"


def test_control_de_identidad_por_altitud(casos):
    """Si la altitud del catalogo difiere mucho de la del paper, es OTRO volcan.

    Es el unico control disponible contra confundir un homonimo o otro cono del mismo
    complejo, y por eso las coordenadas no se estimaron: salen del catalogo Smithsonian.
    """
    for c in casos:
        ap, ag = c.get("alt_paper_m"), c.get("alt_gvp_m")
        if ap is None or ag is None:
            continue
        assert abs(ap - ag) <= 100, (
            f"{c['name']}: altitud paper {ap} vs catalogo {ag} — probable volcan equivocado")


def test_el_nti_del_paper_solo_donde_el_paper_lo_da(casos):
    """A5, A6 y A8 son los unicos con NTI publicado; los demas NO deben inventarlo."""
    con = {c["caso"] for c in casos if c.get("nti_paper") is not None}
    assert con == {"A5", "A6", "A8"}
    for c in casos:
        if c.get("nti_paper") is not None:
            assert -1.0 < c["nti_paper"] < 0.0


def test_geometria_uniforme_es_el_ROI1_del_paper(mod):
    """MISSION prohibe geometria per-volcan; el paper usa un ROI1 de 5 km para todos (D18)."""
    assert mod.INNER_KM == 5.0
    assert mod.RADIUS_KM == 25.0


# ---------------------------------------------------------------- el evaluador

def _p(nti=-0.93, vrp=0.5, d=0.4):
    return {"granule": "g", "inicio": "x", "nti_max": nti, "vrp_pc_mw": vrp,
            "dist_crater_km": d}


POS = {"caso": "A1", "name": "X", "veredicto": "detecta"}
NEG = {"caso": "A9", "name": "Y", "veredicto": "no_detecta"}


def test_sin_pasadas_es_indeterminado(mod):
    for c in (POS, NEG):
        v, _ = mod.evaluar_caso(c, [])
        assert v == "INDETERMINADO"


def test_positivo_que_publica_es_conforme(mod):
    v, _ = mod.evaluar_caso(POS, [_p()])
    assert v == "CONFORME"


def test_positivo_que_no_publica_es_falso_negativo(mod):
    v, _ = mod.evaluar_caso(POS, [_p(vrp=0.0)])
    assert "falso negativo" in v


def test_NEGATIVO_que_publica_es_falso_POSITIVO(mod):
    """El caso que da valor a la bateria: publicar donde el autor no detecta es sobre-deteccion."""
    v, det = mod.evaluar_caso(NEG, [_p(vrp=1.25)])
    assert "falso positivo" in v
    assert "sobre-deteccion" in det


def test_NEGATIVO_que_no_publica_nada_es_conforme(mod):
    v, _ = mod.evaluar_caso(NEG, [_p(vrp=0.0)])
    assert v == "CONFORME"


def test_el_signo_de_los_dos_veredictos_es_opuesto(mod):
    """Blindaje explicito contra invertir el signo: la MISMA pasada da veredictos distintos."""
    pas = [_p(vrp=0.7)]
    assert mod.evaluar_caso(POS, pas)[0] == "CONFORME"
    assert "falso positivo" in mod.evaluar_caso(NEG, pas)[0]


def test_cumulo_fuera_del_ROI_no_cuenta_como_publicar(mod):
    """A93: la distancia decide y se mide desde el crater. Fuera del ROI1 no es el volcan."""
    lejos = [_p(vrp=2.0, d=12.0)]
    assert "falso negativo" in mod.evaluar_caso(POS, lejos)[0]
    assert mod.evaluar_caso(NEG, lejos)[0] == "CONFORME"


def test_control_de_validez_DETIENE_el_caso(mod):
    """Si el NTI observado no es el del paper, no es su escena: nada mas es interpretable."""
    caso = {"caso": "A5", "name": "Ubinas", "veredicto": "detecta", "nti_paper": -0.91}
    v, det = mod.evaluar_caso(caso, [_p(nti=-0.40, vrp=1.0)])   # deteccion impecable
    assert v == "INDETERMINADO"
    assert "control de validez" in det


def test_el_control_no_aplica_donde_el_paper_no_da_numero(mod):
    """Sin NTI publicado no hay control; se evalua igual y se declara asi en el doc."""
    v, _ = mod.evaluar_caso(POS, [_p(nti=None, vrp=0.5)])
    assert v == "CONFORME"


def test_el_probe_no_escribe_en_data(mod):
    src = (RAIZ / "experiments" / "_s136" / "conformidad_apendice.py").read_text(encoding="utf-8")
    for prohibido in ("store.append_record", "data/mirova_equivalent", "append_record("):
        assert prohibido not in src


def test_la_bateria_no_contamina_el_catalogo_operacional():
    """Ocho de los nueve son extranjeros: si entraran a volcanoes.yaml, el cron los procesaria."""
    vc = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
    nombres = {v["name"] for v in vc["volcanoes"]}
    casos = yaml.safe_load(YML.read_text(encoding="utf-8"))["casos"]
    intrusos = {c["name"] for c in casos if c["name"] != "Villarrica"} & nombres
    assert not intrusos, f"volcanes del apendice filtrados al catalogo operacional: {intrusos}"
