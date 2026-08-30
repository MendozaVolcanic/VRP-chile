# -*- coding: utf-8 -*-
"""S126 - una clave repetida en un perfil se resuelve en silencio y miente.

DOS PATRONES, los dos peligrosos y los dos invisibles:

  (1) MISMA clave dos veces en la MISMA seccion. YAML se queda con la ultima sin
      avisar. Paso en esta sesion: al armar `_s126_corona_ctxoff` se inserto
      `enable_test1_contextual_filter: false` cerca del principio de `paths:`, pero
      mas abajo ya existia el mismo flag en `true` — el perfil quedo con el filtro
      ENCENDIDO mientras su cabecera decia que estaba apagado. Lo atrapo la
      verificacion por `pipeline.profile`, no el YAML.

  (2) MISMA clave en secciones DISTINTAS. `pipeline/profile.py` lee cada valor de
      una seccion concreta (`_t = _cfg["thresholds"]`, `_p = _cfg["paths"]`), asi
      que la copia de la otra seccion es letra muerta — pero se lee como si valiera.
      Hoy pasa con dos claves en 31 de los 51 perfiles:

          modis_vent_threshold_k   paths=2.5  thresholds=1.0  -> gana 1.0
          modis_vent_vrp_floor_mw  paths=0.3  thresholds=0.0  -> gana 0.0

      Quien lea `paths:` creeria que el umbral del vent-path de MODIS es 2,5 K
      cuando el pipeline usa 1,0 K.

El patron 1 se prohibe: no hay ningun caso legitimo.
El patron 2 se congela en la lista de abajo: no se arregla acá porque tocar
`mirova_equivalent.yaml` exige el ciclo A45 (tag + confirmacion de Nicolas), y
porque conviene verificar que la limpieza sea de verdad un no-op comparando TODOS
los atributos resueltos antes y despues — la leccion de
docs/S126_CLOUDMASK_YA_ESTA_VIVA.md. Mientras tanto el test impide que crezca.
"""
import re
from collections import defaultdict
from pathlib import Path

import pytest

PERFILES = sorted((Path(__file__).resolve().parents[1] / "pipeline" / "profiles").glob("*.yaml"))

# Deuda conocida (patron 2). Si una entra o sale de esta lista, el test lo dice.
#
# VACIA desde S127: `modis_vent_threshold_k` y `modis_vent_vrp_floor_mw` estaban
# declaradas bajo `paths:` en 31 de 51 perfiles y el codigo nunca las leyo de ahi
# (`profile.py:106-107` las lee de `thresholds:`, donde valen 1.0 y 0.0 y no 2.5 y 0.3).
# Se quitaron. La limpieza se probo no-op como este test pedia: se comparo el valor
# RESUELTO de los cuatro atributos en los 51 perfiles antes y despues, y no se movio
# ninguno.
#
# El guard generico que impide que la clase vuelva -- cualquier clave, no solo estas --
# esta en tests/test_guard_claves_fantasma_s127.py: deriva de profile.py de que seccion
# se lee cada clave y falla si algun perfil la declara en otra.
CROSS_CONOCIDAS = set()


def _claves_por_seccion(path):
    """{seccion: {clave: [lineas]}} — parseo textual, porque yaml.safe_load ya
    colapso los duplicados y no los puede reportar."""
    out = defaultdict(lambda: defaultdict(list))
    seccion = None
    for n, linea in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if re.match(r"^[A-Za-z_]+:", linea):
            seccion = linea.split(":")[0]
            continue
        m = re.match(r"^  ([a-z_0-9]+):", linea)
        if m and seccion:
            out[seccion][m.group(1)].append(n)
    return out


@pytest.mark.parametrize("perfil", PERFILES, ids=lambda p: p.name)
def test_ninguna_clave_repetida_dentro_de_la_misma_seccion(perfil):
    dups = []
    for seccion, claves in _claves_por_seccion(perfil).items():
        for clave, lineas in claves.items():
            if len(lineas) > 1:
                dups.append(f"{seccion}.{clave} en lineas {lineas}")
    assert not dups, (
        f"{perfil.name} repite claves dentro de una seccion: {'; '.join(dups)}. "
        "YAML se queda con la ULTIMA en silencio, asi que el perfil hace algo "
        "distinto de lo que su cabecera dice. Editar la clave que ya existe en "
        "vez de agregar otra.")


def test_las_claves_repetidas_entre_secciones_son_solo_las_conocidas():
    encontradas = set()
    detalle = defaultdict(list)
    for perfil in PERFILES:
        secciones = _claves_por_seccion(perfil)
        donde = defaultdict(set)
        for seccion, claves in secciones.items():
            for clave in claves:
                donde[clave].add(seccion)
        for clave, secs in donde.items():
            if len(secs) > 1:
                encontradas.add(clave)
                detalle[clave].append(perfil.name)

    nuevas = encontradas - CROSS_CONOCIDAS
    assert not nuevas, (
        f"claves nuevas repetidas entre secciones: {sorted(nuevas)}. "
        "profile.py lee cada valor de UNA seccion, asi que la otra copia es letra "
        "muerta que se lee como si valiera. Dejar una sola.")

    resueltas = CROSS_CONOCIDAS - encontradas
    assert not resueltas, (
        f"{sorted(resueltas)} ya no esta duplicada: sacala de CROSS_CONOCIDAS y "
        "confirma en el commit que la limpieza fue un no-op comparando los "
        "atributos resueltos de todos los perfiles antes y despues.")


def test_el_2x2_de_la_corona_declara_lo_que_su_cabecera_dice():
    """Guard concreto del experimento en curso — se verifica por modulo, no por YAML."""
    import importlib
    import os

    import pipeline.profile as prof

    esperado = {
        "_s126_corona_off":    (False, True),    # (corona, filtro contextual)
        "_s126_corona_on":     (True,  True),
        "_s125_viirs_e":       (False, False),
        "_s126_corona_ctxoff": (True,  False),
    }
    previo = os.environ.get("VRP_PROFILE")
    try:
        for nombre, (corona, ctx) in esperado.items():
            os.environ["VRP_PROFILE"] = nombre
            p = importlib.reload(prof)
            assert p.ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375 is corona, nombre
            assert p.ENABLE_TEST1_CONTEXTUAL_FILTER is ctx, nombre
            assert p.DATA_SUBDIR == nombre, nombre
    finally:
        if previo is None:
            os.environ.pop("VRP_PROFILE", None)
        else:
            os.environ["VRP_PROFILE"] = previo
        importlib.reload(prof)
