# -*- coding: utf-8 -*-
"""S127 — guard: ninguna clave se declara en una seccion donde el codigo no la lee.

POR QUE: `modis_vent_threshold_k: 2.5` y `modis_vent_vrp_floor_mw: 0.3` estaban
declaradas bajo `paths:` en 31 de los 51 perfiles. El codigo las lee de `thresholds:`
(`profile.py:106-107`, `_t.get`), donde valen 1.0 y 0.0. Las de `paths:` eran letra
muerta: se leian como configuracion vigente y no lo eran.

No hacian dano porque `enable_vent_path_modis` esta en false — o sea la trampa esperaba
justo al que encendiera ese path, que es el momento en que menos se la busca. Es la
misma familia que `enable_utm_regrid` en S124 (se escribia en el nivel superior y se
leia de `thresholds:`; un perfil de laboratorio con el flag en true arrancaba APAGADO y
el A/B habria corrido cuatro brazos identicos).

El guard es GENERICO a proposito: no lista las dos claves, deriva de `profile.py` de que
seccion se lee cada una y verifica que ningun perfil la declare en otra. Cierra la clase,
no el caso.

Tecnica T9 — docs/PROTOCOLO_AUDITORIA_PROFUNDA.md.
"""
import collections
import glob
import io
import os
import re

import yaml

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# De que variable lee `profile.py` cada seccion del YAML.
VARIABLE_DE_SECCION = {
    "_t": "thresholds",
    "_cfg": "<raiz>",
    "_bg": "background",
    "_paths": "paths",
}


def _origen_de_cada_clave():
    """clave -> {secciones de las que el codigo la lee}, derivado de profile.py."""
    src = io.open(os.path.join(RAIZ, "pipeline", "profile.py"),
                  encoding="utf-8").read()
    origen = collections.defaultdict(set)
    for var, seccion in VARIABLE_DE_SECCION.items():
        pat = re.compile(r'\b%s(?:\.get\(\s*|\[\s*)["\']([a-z0-9_]+)["\']' % re.escape(var))
        for clave in pat.findall(src):
            origen[clave].add(seccion)
    return origen


def test_profile_py_sigue_siendo_legible_por_el_guard():
    """Si el guard deja de encontrar claves, no protege nada y hay que arreglarlo.

    Un guard que pasa porque no mira nada es peor que no tenerlo: da confianza falsa.
    """
    origen = _origen_de_cada_clave()
    assert len(origen) > 40, (
        "el guard solo pudo derivar %d claves de profile.py. Cambio la forma de leer "
        "la config y hay que actualizar VARIABLE_DE_SECCION, o este test esta "
        "aprobando sin mirar." % len(origen))
    assert "thresholds" in origen.get("cloud_mask_bt_k", set())


def test_ningun_perfil_declara_una_clave_donde_el_codigo_no_la_lee():
    origen = _origen_de_cada_clave()
    fantasmas = collections.defaultdict(set)

    for p in sorted(glob.glob(os.path.join(RAIZ, "pipeline", "profiles", "*.yaml"))):
        d = yaml.safe_load(io.open(p, encoding="utf-8")) or {}
        nombre = os.path.basename(p)
        for seccion, contenido in d.items():
            if not isinstance(contenido, dict):
                continue
            for clave in contenido:
                secs = origen.get(clave)
                if secs and seccion not in secs:
                    fantasmas[(clave, seccion, tuple(sorted(secs)))].add(nombre)
        for clave, valor in d.items():
            if isinstance(valor, dict):
                continue
            secs = origen.get(clave)
            if secs and "<raiz>" not in secs:
                fantasmas[(clave, "<raiz>", tuple(sorted(secs)))].add(nombre)

    assert not fantasmas, (
        "hay claves declaradas donde el codigo NO las lee (letra muerta que se lee "
        "como configuracion vigente):\n"
        + "\n".join(
            "  %s declarada en `%s:` pero el codigo la lee de `%s` — en %d perfil(es): %s"
            % (k, sec, ",".join(secs), len(v), ", ".join(sorted(v)[:4]))
            for (k, sec, secs), v in sorted(fantasmas.items()))
        + "\nO la movés a la sección correcta, o la borrás. Dejarla donde está "
          "significa que el próximo que la lea va a creer que rige.")
