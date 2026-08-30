# -*- coding: utf-8 -*-
"""S127 — guard: no se declara por escrito a que volcanes afecta un mecanismo.

POR QUE: la frase "Volcanes NO afectados (regimen alto-MW o sin path D dominante):
Villarrica, Copahue, Isluga, Lascar, Lastarria, Llaima, NdC" vivio en el docstring de
`single_pixel_mode.py` y copiada en 13 perfiles, incluido el OPERACIONAL. Medida contra
`data/mirova_equivalent/` era falsa para LOS SIETE, y el orden estaba invertido: Lascar
-nombrado como no afectado- es el mas afectado de la flota (33,9 % de sus records
modificados) y Tupungatito -el volcan para el que se construyo el modo- el menos (7,5 %).

Dirigio decisiones durante sesiones: S126 la encontro primero para Lascar y PCC, y aun
asi las 13 copias sobrevivieron.

El guard no verifica que la lista sea correcta -- eso es imposible sin correr el
pipeline sobre datos frescos. Verifica que la lista NO EXISTA. Un alcance por volcan
depende de los datos y envejece solo; se mide con
`experiments/_s127_declarado/02_single_pixel_mode_alcance.py`, no se escribe.

Es la tecnica T9: una afirmacion sobre el estado del sistema necesita un test detras, o
no es una afirmacion — es una intencion.
"""
import glob
import io
import os

import pytest
import yaml

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Frases que declaran a que volcanes afecta (o no) un mecanismo. Cada una es una
# afirmacion sobre el estado del sistema que ningun test puede sostener.
FRASES_PROHIBIDAS = [
    "Volcanes NO afectados",
    "volcanes no afectados",
    "Vols NO afectados",
]


def _archivos_vigilados():
    """`pipeline/` entero salvo caches. Los docs y experiments quedan afuera a
    proposito: ahi una lista fechada es un registro historico legitimo; en el codigo
    y en los perfiles se lee como el estado actual."""
    for p in glob.glob(os.path.join(RAIZ, "pipeline", "**", "*.py"), recursive=True):
        if "__pycache__" not in p:
            yield p
    for p in glob.glob(os.path.join(RAIZ, "pipeline", "**", "*.yaml"), recursive=True):
        yield p


def test_ningun_perfil_ni_modulo_declara_a_que_volcanes_afecta():
    """Prohibe DECLARARLA; permite CITARLA como historia.

    La distincion es por contexto, no por archivo: una ocurrencia vale solo si su
    entorno inmediato dice que la lista era falsa. Asi el texto que documenta el
    incidente sobrevive y una lista nueva escrita de buena fe no.
    """
    ofensores = []
    for p in _archivos_vigilados():
        texto = io.open(p, encoding="utf-8", errors="replace").read()
        bajo = texto.lower()
        for frase in FRASES_PROHIBIDAS:
            desde = 0
            while True:
                i = texto.find(frase, desde)
                if i < 0:
                    break
                desde = i + 1
                ventana = bajo[max(0, i - 700):i + 700]
                if "falsa" in ventana or "s127" in ventana:
                    continue      # es la cita historica, no una declaracion nueva
                ofensores.append(
                    (os.path.relpath(p, RAIZ).replace("\\", "/"), frase))
    assert not ofensores, (
        "vuelve a haber una lista de volcanes afectados declarada en el codigo:\n  "
        + "\n  ".join("%s -> %r" % o for o in sorted(set(ofensores)))
        + "\nEsa clase de afirmacion envejece sola (fue falsa para 7 de 7 en S127). "
          "Medila con experiments/_s127_declarado/02_single_pixel_mode_alcance.py "
          "en vez de escribirla.")


def test_el_perfil_operacional_conserva_los_flags_del_modo():
    """La correccion fue de COMENTARIO: ningun valor del perfil se movio.

    El PR #535 apago la mascara de nube en produccion creyendo que era un no-op, asi
    que un cambio "solo de comentarios" en `mirova_equivalent.yaml` necesita su propia
    prueba, no una afirmacion.

    Los tres viven en el NIVEL SUPERIOR del YAML, no bajo `thresholds:` -- y asi los
    lee `profile.py:681` (`_cfg.get`), no `_t`. Se afirma acá explicitamente porque el
    bug gemelo existio: en S124 `enable_utm_regrid` se escribia en el nivel superior y
    se leia de `thresholds:`, y el flag arrancaba siempre apagado.
    """
    p = os.path.join(RAIZ, "pipeline", "profiles", "mirova_equivalent.yaml")
    cfg = yaml.safe_load(io.open(p, encoding="utf-8"))
    assert cfg["enable_single_pixel_sub_mw_mode"] is True
    assert cfg["sub_mw_regime_threshold_mw"] == pytest.approx(5.0)
    assert cfg["single_pixel_max_cluster_pixels"] == 3
    assert "enable_single_pixel_sub_mw_mode" not in cfg.get("thresholds", {}), (
        "el flag aparece ADEMAS bajo thresholds:, donde el codigo no lo lee — es el "
        "modo de falla de enable_utm_regrid en S124")


def test_los_13_perfiles_siguen_parseando():
    """Un comentario mal cerrado en YAML puede tragarse la clave siguiente (A49)."""
    fallos = []
    for p in glob.glob(os.path.join(RAIZ, "pipeline", "profiles", "*.yaml")):
        try:
            d = yaml.safe_load(io.open(p, encoding="utf-8"))
        except yaml.YAMLError as e:
            fallos.append((os.path.basename(p), str(e)[:80]))
            continue
        if not isinstance(d, dict) or not d:
            fallos.append((os.path.basename(p), "no parsea a dict no vacio"))
    assert not fallos, "perfiles rotos: %s" % fallos
