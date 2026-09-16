# -*- coding: utf-8 -*-
"""S142: con los flags D22 y D25 en OFF, la salida es BIT A BIT la de antes del cambio; con los dos
encendidos por perfil, MODIS y VIIRS 750 no se mueven.

POR QUÉ. El cron NRT corre 12 veces al día sobre 11 volcanes: un cambio que pase los tests
unitarios pero mueva un número se replica a cientos de records antes de verse (A45). El golden se
generó con el código previo (Tarea 1) y se compara como texto (NaN != NaN, S132), con los floats
escritos a `arnes.SIGNIFICATIVAS` cifras: el último dígito del float64 cambia entre Windows y Linux
y sin ese redondeo el golden medía la máquina, no el código (CI en rojo del PR #681).

CONTROLES DE INSTRUMENTO (S128). Un test de "no cambia nada" pasa trivialmente si la escena no
ejerce el camino que podría cambiar. Por eso, además de la comparación, este archivo comprueba que
el golden SÍ cubre las dos zonas que el verificador del plan encontró descubiertas:

- el camino del Test 1 (hallazgo H1): la escena `test1_difuso` publica por los bloques de magnitud
  del Test 1, y mover el anillo del que sale ese fondo cambia el golden. Sin ese control, una
  mutación del fondo de esos bloques pasaría la suite y llegaría al cron.
- la compuerta de temperatura en MODIS (hallazgo H6): la escena `nevado_vecino_tibio` de MODIS
  cambia si MODIS pierde la compuerta; las otras dos escenas MODIS no, y por sí solas habrían
  hecho pasar el test "MODIS no cambia" por construcción.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import arnes_sintetico_s142 as arnes  # noqa: E402
from arnes_sintetico_s142 import correr_en_subproceso  # noqa: E402

GOLDEN = ROOT / "tests" / "golden_s142" / "apagado.json"
PERFIL_VERIF = "_s142_verif_flags_nuevos"


def _canon(obj):
    # `arnes._redondear` es obligatorio: el golden se escribe con los floats a
    # `arnes.SIGNIFICATIVAS` cifras, así que comparar contra un lado sin redondear mide el último
    # dígito del float64 (que difiere entre Windows y Linux) y no el comportamiento del pipeline.
    return json.dumps(arnes._redondear(obj), sort_keys=True, default=arnes._a_json,
                      ensure_ascii=False)


def _golden():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_la_serializacion_ignora_el_ruido_del_ultimo_digito_pero_no_un_cambio_real():
    """El golden no puede depender de en qué máquina se generó (S142, CI en rojo del PR #681).

    POR QUÉ. El mismo cálculo en Windows y en Linux difiere en el último dígito del float64:
    `sd_dnti` 0,00025641447808233127 contra 0,0002564144780823313, o sea 1e-16 relativo. Eso es
    la aritmética de coma flotante, no el pipeline: ninguna decisión del algoritmo cambia con la
    cifra 17. Comparando el JSON como texto crudo, el test se cae en el CI y deja de decir lo que
    promete ("los flags apagados no cambian nada"): mide la máquina, no el código.

    QUÉ SE EXIGE. `canonico` redondea a SIGNIFICATIVAS cifras antes de serializar, así que el
    ruido del último dígito desaparece del texto, pero un cambio con sentido físico (acá 1e-6
    relativo, y los cambios reales del pipeline son mucho mayores: un VRP que pasa de 0,0 a
    0,097 MW) sigue cambiando el texto. Sin la segunda mitad, redondear sería tapar el problema.
    """
    base = {"vrp_mw": 0.09681234567890123, "diag": {"sd_dnti": 0.00025641447808233127}}
    ruido = {"vrp_mw": 0.09681234567890456, "diag": {"sd_dnti": 0.0002564144780823313}}
    real = {"vrp_mw": 0.09681244567890123, "diag": {"sd_dnti": 0.00025641547808233127}}
    assert arnes.canonico(base) == arnes.canonico(ruido), (
        "el ruido de coma flotante entre máquinas cambia el texto: el golden mide la máquina")
    assert arnes.canonico(base) != arnes.canonico(real), (
        "un cambio de 1e-6 relativo pasa desapercibido: el redondeo tapa cambios reales")


def test_perfil_operacional_reproduce_el_golden_bit_a_bit(tmp_path):
    texto = correr_en_subproceso(tmp_path, perfil="mirova_equivalent")
    assert texto == GOLDEN.read_text(encoding="utf-8"), (
        "la salida con el perfil operacional cambió respecto del código previo: los flags "
        "D22/D25 en OFF NO pueden cambiar nada")


def test_la_escena_del_test1_publica_por_los_bloques_del_test1():
    """H1: sin esta escena, el golden sólo cubría el camino contextual.

    Las cuatro propiedades juntas son la prueba de que lo publicado sale de los bloques de
    magnitud del Test 1: si `n_anomalous_pixels` es 0, el bloque contextual no corrió, así que
    el único código que pudo escribir `anomaly_pixels` es el que los reconstruye en el camino
    del Test 1 (process_viirs.py, bloque `final_hotspot_source == "test1"`).
    """
    t = _golden()["v375"]["test1_difuso|kernel=False"]
    assert t["triggered_test1"] is True
    assert t["final_hotspot_source"] == "test1_roi"
    assert t["n_anomalous_pixels"] == 0
    assert t["diag_n_first_pass_pixels"] == 0 and t["diag_n_dnti_ctx_path"] == 0
    assert len(t["anomaly_pixels"]) == 1 and t["anomaly_pixels"][0]["vrp_mw"] > 0


def test_un_cambio_en_el_fondo_de_los_bloques_del_test1_rompe_el_golden():
    """Control tipo M3: el fondo de esos bloques sale del anillo del Test 1. Al moverlo, la escena
    del Test 1 tiene que cambiar (y seguir disparando, para que el cambio sea del FONDO y no de
    haber perdido el disparo), mientras la escena contextual queda igual."""
    g = _golden()["v375"]
    mutada = arnes.correr_v375("test1_difuso", False, {"TEST1_INNER_RING_KM": 1.8})
    assert mutada["triggered_test1"] is True, "el control perdió el disparo: ya no aísla el fondo"
    assert _canon(mutada) != _canon(g["test1_difuso|kernel=False"])
    principal = arnes.correr_v375("nevado_vecino_tibio", False, {"TEST1_INNER_RING_KM": 1.8})
    assert _canon(principal) == _canon(g["nevado_vecino_tibio|kernel=False"]), (
        "el anillo del Test 1 movió también la escena contextual: el control no aísla nada")


def test_la_escena_modis_nevado_vecino_tibio_si_ejercita_la_compuerta():
    """H6: si MODIS perdiera la compuerta de temperatura, esta escena lo nota y las otras dos no."""
    import pipeline.process_modis as pm
    sensibles = {}
    for escena in arnes.ESCENAS_MODIS:
        base = arnes.correr_modis(escena)
        with patch.object(pm, "NTI_BT_SANITY_K", -1e9):
            sin_compuerta = arnes.correr_modis(escena)
        sensibles[escena] = _canon(base) != _canon(sin_compuerta)
    assert sensibles["nevado_vecino_tibio"] is True, (
        "la escena MODIS no distingue tener compuerta de no tenerla: el test de invariancia de "
        "MODIS pasaría por construcción")
    assert sensibles["nevado"] is False and sensibles["plana"] is False


@pytest.fixture(scope="module")
def salida_verif(tmp_path_factory):
    if not (ROOT / "pipeline" / "profiles" / f"{PERFIL_VERIF}.yaml").exists():
        pytest.fail(f"falta el perfil {PERFIL_VERIF} (Tarea 6)")
    return json.loads(correr_en_subproceso(tmp_path_factory.mktemp("verif"), perfil=PERFIL_VERIF))


def test_modis_y_viirs750_no_cambian_con_los_dos_flags_on(salida_verif):
    golden = _golden()
    for sensor in ("modis", "v750"):
        assert _canon(salida_verif[sensor]) == _canon(golden[sensor]), sensor


def test_los_helpers_con_su_default_no_cambian_con_los_flags_on(salida_verif):
    """Los helpers compartidos se llaman sin apply_bt_gate: el default debe seguir siendo la compuerta."""
    assert salida_verif["helpers"] == _golden()["helpers"]


def test_el_perfil_de_verificacion_si_mueve_viirs375(salida_verif):
    """Control de instrumento (S128): si V375 tampoco cambiara, el perfil no estaría leyendo sus flags
    y el test anterior pasaría por la razón equivocada."""
    golden = _golden()
    r_on = salida_verif["v375"]["nevado_vecino_tibio|kernel=False"]
    r_off = golden["v375"]["nevado_vecino_tibio|kernel=False"]
    assert r_on["diag_n_first_pass_pixels"] != r_off["diag_n_first_pass_pixels"]
    assert "diag_bg_vecinos_n_sin_vecinos" in r_on and "diag_bg_vecinos_n_sin_vecinos" not in r_off
    # y el camino del Test 1 también recibe el fondo nuevo (H1)
    t_on = salida_verif["v375"]["test1_difuso|kernel=False"]
    t_off = golden["v375"]["test1_difuso|kernel=False"]
    assert _canon(t_on["anomaly_pixels"]) != _canon(t_off["anomaly_pixels"])
