"""S124 — un perfil nuevo debe DERIVAR del operacional, no copiarlo.

El patrón que motiva esto ya causó dos incidentes reales:

  · `experimental` era una copia literal de la configuración de S15. Cien
    sesiones después seguía corriendo ese algoritmo: en Nevados de Chillán daba
    VRP mediano 5.686 MW contra 0.357 del operacional, con máximos de 522 MW y
    distancia mediana de 25.4 km — o sea detectando en el BORDE del radio de
    búsqueda, no en el volcán. No era "más sensible", era ruido.

  · `mirova_equivalent_villarrica_test1` es peor, porque **corre en producción**
    y escribe en la base operacional: 32 constantes efectivas distintas del
    operacional. Villarrica se publica sin nadir-fijo (la corrección de área que
    la curó de 18.3× a 1.0× en S103), sin ancla honesta, sin dual-ROI, sin
    magnitud focal, y con parches que MISSION describe como anuladores de la
    diferenciación summit/scene.

La causa es la misma en los dos casos y es estructural: **un YAML standalone
congela el algoritmo del día en que nació**, y los flags que no declara caen a
defaults que a veces ENCIENDEN cosas que el operacional apagó. `extends:` existe
desde S75 justo para esto — el perfil declara solo en qué diverge, y hereda el
resto.

Este test no arregla los perfiles viejos (eso es una decisión con reproceso de
por medio); impide que nazca el próximo.
"""
from pathlib import Path

import pytest
import yaml

PROFILES = Path(__file__).parent.parent / "pipeline" / "profiles"

# Perfiles standalone que YA existían al crear este test. Cada uno congela el
# algoritmo de su fecha. Están acá para que el test sea útil desde el día uno
# sin exigir un reproceso masivo — NO como permiso para agregar más.
#
# Para sacar uno de esta lista: convertirlo a `extends: mirova_equivalent`
# declarando solo sus divergencias reales, y reprocesar su serie si tenía datos.
CONGELADOS_CONOCIDOS = {
    # EN PRODUCCIÓN — el más urgente de migrar (issue #513)
    "mirova_equivalent_villarrica_test1",
    # A/B históricos: cumplieron su función, no deberían volver a correrse tal cual
    "mirova_equivalent_bt_path_on_v1",
    "mirova_equivalent_f_s81_a_intra_radio_disabled",
    "mirova_equivalent_f_s81_a_intra_radio_enabled",
    "mirova_equivalent_f_s81_b_prime_2nd_pass_gate_disabled",
    "mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled",
    "mirova_equivalent_lbg_global",
    "mirova_equivalent_no_cap_v1",
    "mirova_equivalent_path_d_atm_gate_v1",
    "mirova_equivalent_path_d_cap_v1",
    "mirova_equivalent_path_d_covalidation_v1",
    "mirova_equivalent_phase2",
    "mirova_equivalent_test1_retire_only_v1",
    "mirova_equivalent_test1pix_filter",
    "mirova_equivalent_unsuitable_only_v1",
}

# El operacional es la raíz de la jerarquía: no deriva de nadie.
RAIZ = "mirova_equivalent"


def _vivos():
    """Perfiles vivos: los `_`-prefijados son experimentos A/B archivables."""
    return [p for p in PROFILES.glob("*.yaml") if not p.name.startswith("_")]


def test_todo_perfil_nuevo_deriva_del_operacional():
    sin_extends = []
    for p in _vivos():
        n = p.stem
        if n == RAIZ or n in CONGELADOS_CONOCIDOS:
            continue
        cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if not cfg.get("extends"):
            sin_extends.append(n)

    assert not sin_extends, (
        f"Perfiles sin `extends`: {sin_extends}. Un YAML standalone congela el "
        f"algoritmo del día en que nació: los flags que no declara caen a "
        f"defaults, y algunos ENCIENDEN paths que el operacional apagó. Usá "
        f"`extends: {RAIZ}` y declará solo en qué diverge.")


def test_la_lista_de_congelados_no_crece_sin_darse_cuenta():
    """Si un congelado se migra, sale de la lista; si desaparece, también."""
    existentes = {p.stem for p in PROFILES.glob("*.yaml")}
    fantasmas = CONGELADOS_CONOCIDOS - existentes
    assert not fantasmas, (
        f"Perfiles en CONGELADOS_CONOCIDOS que ya no existen: {fantasmas}. "
        f"Sacalos de la lista.")

    ya_migrados = []
    for n in CONGELADOS_CONOCIDOS & existentes:
        cfg = yaml.safe_load((PROFILES / f"{n}.yaml").read_text(encoding="utf-8")) or {}
        if cfg.get("extends"):
            ya_migrados.append(n)
    assert not ya_migrados, (
        f"Estos perfiles YA usan extends: {ya_migrados}. Sacalos de "
        f"CONGELADOS_CONOCIDOS para que el test los vigile de verdad.")


@pytest.mark.parametrize("perfil", ["experimental", "experimental_ndc_focus",
                                    "experimental_lowT"])
def test_los_perfiles_experimentales_derivan_del_operacional(perfil):
    """Guard de intención: el laboratorio hereda la detección, no la reinventa.

    Divergir en umbrales o en geometría es el punto de un perfil experimental.
    Divergir en la DETECCIÓN por omisión —heredar el algoritmo de hace cien
    sesiones sin querer— es el bug que este test previene.
    """
    cfg = yaml.safe_load((PROFILES / f"{perfil}.yaml").read_text(encoding="utf-8")) or {}
    assert cfg.get("extends") == RAIZ
