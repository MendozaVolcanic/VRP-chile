# -*- coding: utf-8 -*-
"""Guard S129 — A15 dejó de ser una recomendación y pasó a ser un test.

QUÉ PASÓ
========
El A/B de S129 se lanzó con una ventana de **176 días** y el `timeout-minutes: 320`
copiado de un template que usaba **89 días**. Ocho de quince jobs murieron a los 321
minutos exactos, contra el límite de 320. Seis horas de CI perdidas y el experimento
sin resultado.

La regla ya existía: **A15 — `timeout >= duración_esperada × 1,3`**. No falló la
regla: falló que era prosa. Se copió el número del template sin recalcular la
duración, que es exactamente lo que una regla escrita no puede impedir y un test sí.

LA CALIBRACIÓN, medida y no inventada
=====================================
Dos puntos de dato reales del repo:

  · `_archive/reproc-ab-unsuitable-only.yml`: 89 días con 320 min → **funcionó**
    (≤ 3,6 min/día)
  · `reproc-s129-ab-fondos.yml` (1er intento): 176 días con 320 min → **murió**
    (> 1,82 min/día)

O sea el costo real está entre 1,82 y 3,6 minutos por día de ventana. Se toma la
cota inferior medida —1,82— y se le aplica el factor 1,3 de A15: **2,4 min/día**.

Comprobación contra los dos casos: 89 × 2,4 = 214 ≤ 320 ✓ (acepta el que funcionó);
176 × 2,4 = 422 > 320 ✗ (rechaza el que murió). El guard discrimina.

⚠️ Y el techo que no se negocia: **GitHub corta a las 6 h (360 min) por job**. Subir
el reloj no es salida — pasada cierta ventana hay que partirla en chunks.
"""
import datetime as dt
import os
import re

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WF = os.path.join(ROOT, ".github", "workflows")

MIN_POR_DIA = 2.4          # 1,82 medido × 1,3 (A15)
TECHO_GITHUB_MIN = 360     # 6 h duras por job


def _workflows_de_reproceso():
    """Los que corren `run_pipeline.py` sobre una ventana con `start`/`end`."""
    out = []
    if not os.path.isdir(WF):
        return out
    for f in sorted(os.listdir(WF)):
        if not f.endswith((".yml", ".yaml")):
            continue
        txt = open(os.path.join(WF, f), encoding="utf-8", errors="replace").read()
        if "run_pipeline.py" not in txt:
            continue
        try:
            d = yaml.safe_load(txt)
        except yaml.YAMLError:
            continue
        disp = ((d.get("on") or {}).get("workflow_dispatch") or {}) if isinstance(
            d.get("on"), dict) else {}
        ins = disp.get("inputs") or {}
        if "start" not in ins or "end" not in ins:
            continue
        out.append((f, d, ins))
    return out


def _dias(ins):
    try:
        a = dt.date.fromisoformat(str(ins["start"].get("default")))
        b = dt.date.fromisoformat(str(ins["end"].get("default")))
    except (ValueError, TypeError, AttributeError):
        return None
    return (b - a).days


def _timeout_del_paso_de_reproceso(d):
    """El reloj EFECTIVO del paso que corre el pipeline.

    Si el step no declara `timeout-minutes`, hereda el del job — y entonces el que
    manda es ese. La primera version de este guard exigia el del step y marcaba como
    bug a `reproc-s121-d12-modis-ab.yml`, que no lo tiene pero cuyo job declara 340
    min para 89 dias. Era un falso positivo DEL GUARD, no del workflow.
    """
    for job in (d.get("jobs") or {}).values():
        for step in (job.get("steps") or []):
            if "run_pipeline.py" in str(step.get("run", "")):
                return step.get("timeout-minutes") or job.get("timeout-minutes")
    return None


@pytest.mark.parametrize("caso", _workflows_de_reproceso(),
                         ids=lambda c: c[0] if isinstance(c, tuple) else str(c))
def test_el_timeout_alcanza_para_la_ventana_por_defecto(caso):
    """A15, ejecutable: `timeout >= dias × 2,4`."""
    nombre, d, ins = caso
    dias = _dias(ins)
    if dias is None:
        pytest.skip("%s no declara fechas por defecto parseables" % nombre)
    tmo = _timeout_del_paso_de_reproceso(d)
    assert tmo is not None, (
        "%s corre run_pipeline.py sin `timeout-minutes` ni en el step ni en el job. "
        "Sin reloj el modo de falla es un cuelgue de horas sin rastro." % nombre)
    necesario = round(dias * MIN_POR_DIA)
    assert tmo >= necesario, (
        "%s: ventana por defecto de %d días necesita >= %d min y declara %d.\n"
        "Es A15 (`timeout >= duración × 1,3`), calibrada sobre dos corridas reales "
        "del repo. Si la ventana es la correcta, PARTILA EN CHUNKS: subir el reloj "
        "no sirve porque GitHub corta a los %d min por job."
        % (nombre, dias, necesario, tmo, TECHO_GITHUB_MIN))


@pytest.mark.parametrize("caso", _workflows_de_reproceso(),
                         ids=lambda c: c[0] if isinstance(c, tuple) else str(c))
def test_el_timeout_no_supera_el_techo_de_github(caso):
    """Un reloj sobre 360 min es una mentira: GitHub mata el job igual."""
    nombre, d, _ins = caso
    tmo = _timeout_del_paso_de_reproceso(d)
    if tmo is None:
        pytest.skip("%s sin timeout en el step" % nombre)
    assert tmo <= TECHO_GITHUB_MIN, (
        "%s declara %d min y GitHub corta a los %d. El job muere igual, pero sin "
        "que el reloj propio deje el rastro." % (nombre, tmo, TECHO_GITHUB_MIN))


def test_el_guard_sigue_mirando_algo():
    """Un guard que pasa por no encontrar nada da confianza falsa (patrón S127)."""
    encontrados = _workflows_de_reproceso()
    assert encontrados, (
        "El guard no encontró ningún workflow de reproceso. O se archivaron todos, "
        "o cambió el nombre del script y la detección quedó ciega — verificar antes "
        "de dar por bueno que este test pase.")
