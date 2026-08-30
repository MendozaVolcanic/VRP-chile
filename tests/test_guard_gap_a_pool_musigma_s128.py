# -*- coding: utf-8 -*-
"""Guard S128 — el GAP #A está ABIERTO, y el flag que lo gobierna no es el que dice
la documentación.

POR QUÉ EXISTE ESTE GUARD
=========================
Cuatro documentos (CLAUDE.md, MISSION.md, MIROVA_DIVERGENCES.md, AUDIT_S114) declaran
el GAP #A "RESUELTO S115 = mislabel, NO reabrir". El cierre se apoya en dos
afirmaciones, y S128 verificó que **las dos son falsas**:

  (1) «"discarded for further steps" = fuera del pool μ,σ, ya cubierto por el
      second-run» — FALSO. El second-run recibe `active_mask=hot_mask_2d`, y
      `hot_mask_2d = fp_hot` (sólo Tests 2∧3). Los píxeles de Test 1 K1
      (`nti_path_hot`) nunca entran ahí.
  (2) «el flag ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK controla el REPORTE, no el
      pool» — FALSO. Ese flag decide si `nti_path_hot` se pasa como `test1_mask`
      a `first_pass_tests_2_and_3`, y adentro `build_unsuitable_mask` hace
      `unsuitable = unsuitable | test1_mask`, que ES el pool de μ y σ.

Es A89 de manual: el flag se juzgó por su NOMBRE ("...RETIRE_FROM_HOT_MASK" suena a
reporte) en vez de por cómo lo lee el código.

EL FENÓMENO, para que se entienda qué está en juego
---------------------------------------------------
Coppola 2016a manda calcular la media y el desvío del fondo sobre los píxeles
"suitable", y define como no-suitable justamente a los que ya dispararon el Test 1:

    «Pixels that satisfy Test 1 are flagged as 'active' and subsequently discarded
     (unsuitable) for further steps.»                          (sp426_5.txt:297-300)
    «m and s are the arithmetic mean and standard deviation of all the suitable
     pixels within the image.»                                 (sp426_5.txt:326-329)

Los píxeles del Test 1 son, por construcción, los más calientes de la escena. Dejarlos
dentro del fondo infla μ y sobre todo σ; el umbral de los Tests 2 y 3 es μ + C2·σ, así
que un fondo inflado **sube el umbral y vuelve la detección menos sensible**. La
dirección del error es hacia el falso negativo, que es el error caro en monitoreo.

QUÉ HACE ESTE TEST
------------------
No cambia el comportamiento ni exige encender el flag: la adopción necesita su propio
A/B con reproceso real (A45/A18). Lo que hace es **impedir que el gap se vuelva a
cerrar con prosa**. Falla si:

  · alguien vuelve a escribir en la documentación que el flag controla sólo el reporte,
    o que el second-run ya cubre el retiro del pool;
  · el cableado deja de ser el que S128 verificó (y entonces hay que re-medir, no
    re-afirmar).
"""
import os
import re

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _leer(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        pytest.skip("no existe %s" % rel)
    return open(p, encoding="utf-8", errors="replace").read()


def test_el_flag_gatea_el_pool_de_mu_sigma_no_el_reporte():
    """El cableado que S128 verificó: el flag decide el `test1_mask` del first-pass."""
    src = _leer("pipeline/process_modis.py")
    m = re.search(
        r"_test1_mask_for_fp\s*=\s*\(\s*nti_path_hot\s+if\s+"
        r"ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK\s+else\s+None", src)
    assert m, (
        "cambió el cableado del GAP #A en process_modis.py. Si el cambio es "
        "deliberado, re-medí el efecto sobre el pool μ/σ y actualizá este guard "
        "con el resultado — no lo borres.")

    ctx = _leer("pipeline/detection_context.py")
    assert re.search(r"unsuitable\s*=\s*unsuitable\s*\|\s*test1_mask", ctx), (
        "`test1_mask` ya no alimenta la máscara de no-suitable. Ese `|` es lo que "
        "hace que el flag gobierne el POOL de μ/σ y no sólo el reporte.")


def test_el_second_run_no_cubre_el_retiro_de_los_K1():
    """La otra pata del cierre de S115: el second-run recibe sólo Tests 2 y 3."""
    src = _leer("pipeline/process_modis.py")
    assert re.search(r"active_mask\s*=\s*hot_mask_2d", src), \
        "el second_pass_adjacent ya no recibe hot_mask_2d; re-verificar el GAP #A"
    assert re.search(r"^\s*hot_mask_2d\s*=\s*fp_hot\s*$", src, re.M), (
        "`hot_mask_2d = fp_hot` era lo que dejaba a los K1 (`nti_path_hot`) fuera "
        "del second-run. Si esto cambió, el argumento de S115 puede haberse vuelto "
        "cierto — medilo antes de re-cerrarlo.")


def test_nti_path_hot_es_el_test_1_K1():
    """Sin esto, los dos tests de arriba hablarían de otra cosa."""
    lineas = _leer("pipeline/process_modis.py").splitlines()
    i = next((k for k, l in enumerate(lineas)
              if re.match(r"\s*nti_path_hot\s*=", l)), None)
    cuerpo = "\n".join(lineas[i:i + 10]) if i is not None else ""
    assert i is not None and "NTI_K1_NIGHT" in cuerpo, (
        "`nti_path_hot` ya no se define por el umbral K1; este guard asume que esa "
        "máscara ES el Test 1 de Coppola 2016a.")


def test_la_documentacion_no_puede_volver_a_cerrarlo_con_prosa():
    """Regla B del protocolo: cierre por guard, no por prosa.

    Las frases del cierre de S115 quedan prohibidas como AFIRMACIÓN vigente. Se
    permiten si están tachadas (`~~...~~`) o marcadas como corregidas por S128,
    porque el historial se conserva — lo que no se puede es volver a declararlas.
    """
    patrones = [
        (r"controla el REPORTE.{0,40}no el pool", "«el flag controla el reporte, no el pool»"),
        (r"ya cubierto por el second-run", "«ya cubierto por el second-run»"),
    ]
    ofensas = []
    for rel in ("CLAUDE.md", "docs/MISSION.md", "docs/MIROVA_DIVERGENCES.md",
                "docs/AUDIT_S114_PARITY_BY_SENSOR.md"):
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        for n, linea in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
            for pat, etiqueta in patrones:
                if not re.search(pat, linea, re.I):
                    continue
                # Se acepta si la línea está tachada o citada como corregida en S128.
                if "~~" in linea or re.search(r"S128", linea):
                    continue
                ofensas.append("%s:%d — %s" % (rel, n, etiqueta))
    assert not ofensas, (
        "S128 verificó contra el código y contra el paper que estas afirmaciones son "
        "falsas. Si volvés a cerrarlo, hacelo con una MEDICIÓN y actualizá este "
        "guard.\n  " + "\n  ".join(ofensas))


def test_el_efecto_va_hacia_el_falso_negativo():
    """El mecanismo, en aritmética: meter los píxeles calientes en el fondo sube el
    umbral μ + C2·σ. Es el sentido físico del hallazgo, y lo fija numéricamente."""
    rng = np.random.default_rng(20260830)
    fondo = rng.normal(0.0, 0.01, 2500)          # escena tranquila
    calientes = np.array([0.20, 0.25, 0.31, 0.42])   # los Test 1 K1
    c2 = 5.0

    umbral_fiel = fondo.mean() + c2 * fondo.std()                      # sin los K1
    mezcla = np.concatenate([fondo, calientes])
    umbral_actual = mezcla.mean() + c2 * mezcla.std()                  # con los K1

    assert umbral_actual > umbral_fiel, (
        "incluir los píxeles del Test 1 en el pool tiene que INFLAR el umbral")
    assert umbral_actual / umbral_fiel > 1.5, (
        "el efecto debería ser sustancial, no marginal: %.3f vs %.3f"
        % (umbral_actual, umbral_fiel))
