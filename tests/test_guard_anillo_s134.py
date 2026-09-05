# -*- coding: utf-8 -*-
"""Guards de la regla B para los hallazgos de posición de AUDIT_S134 (plan §3).

POR QUÉ. S133 midió un «anillo» del cúmulo a 2,3-2,8 km del cráter en 9 de 11 volcanes y lo
leyó como «integramos otro objeto que MIROVA». S134 (F1, F2, F3) mostró que el anillo vive en
las pasadas que MIROVA NO publica y que Láscar, el control positivo, pone el cúmulo en el cráter
cuando la fuente es fuerte. Estos guards fijan dos cosas para que ningún reproceso futuro las
mueva en silencio: (1) el control positivo permanente — Láscar VIIRS375 con el cúmulo a < 0,5 km
en la mayoría de las pasadas publicadas; (2) que los scripts de posición de la auditoría anclen
en `vent_lat/vent_lon` y no en el `lat/lon` del catálogo (A13: 0,85 km de diferencia en
Villarrica; cinco de los once Tier A tienen vent ≠ catálogo).

Las dos preguntas del instrumento van en el docstring de cada test.
"""
import glob
import json
import math
import os
import re
import statistics

import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data", "mirova_equivalent")
AUDIT = os.path.join(ROOT, "experiments", "_s134_audit")


def _hav(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))


def _vent(vol):
    with open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8") as fp:
        cfg = yaml.safe_load(fp)
    vols = cfg["volcanoes"] if isinstance(cfg, dict) and "volcanoes" in cfg else cfg
    it = vols if isinstance(vols, list) else [dict(name=k, **x) for k, x in vols.items()]
    for v in it:
        if v.get("name") == vol:
            assert v.get("vent_lat") is not None, "%s sin vent_lat" % vol
            return v["vent_lat"], v["vent_lon"]
    raise AssertionError("volcán %s no está en volcanoes.yaml" % vol)


def test_control_positivo_lascar_cumulo_en_el_crater():
    """Control positivo permanente (plan S134 §3). Pregunta 1: si el pipeline empezara a
    poner el cúmulo de Láscar en el flanco, la mediana sube y la fracción cae → falla.
    Pregunta 2: se exige n ≥ 50 records publicados para que el resultado no sea un cero
    de «no medí». Umbrales holgados respecto de lo medido (S133: 0,22 km · 79 %;
    S134 F1: 0,17 km · 99 % en pasadas con MIROVA) para no romper por ruido."""
    p = os.path.join(DATA, "Lascar.json")
    if not os.path.exists(p):
        pytest.skip("sin data local de Láscar")
    with open(p, encoding="utf-8") as fp:
        d = json.load(fp)
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    la, lo = _vent("Lascar")
    dist = []
    for r in recs:
        if not isinstance(r, dict):
            continue
        s = str(r.get("sensor", ""))
        if not (s.startswith("VIIRS") and not s.endswith("750")):
            continue
        if str(r.get("datetime_utc", ""))[:10] < "2026-06-01":
            continue
        pc = r.get("primary_cluster") or {}
        mag = r.get("f5_core_vrp_mw") or pc.get("vrp_mw")
        if not mag or mag <= 0 or pc.get("centroid_lat") is None or r.get("distance_class") != "summit":
            continue
        dist.append(_hav(pc["centroid_lat"], pc["centroid_lon"], la, lo))
    assert len(dist) >= 50, "muy pocos records publicados de Láscar V375 desde 2026-06-01 (n=%d)" % len(dist)
    med = statistics.median(dist)
    frac = sum(1 for x in dist if x <= 0.5) / len(dist)
    assert med < 0.5, "Láscar V375: mediana del cúmulo al cráter %.2f km (esperado < 0,5)" % med
    assert frac >= 0.6, "Láscar V375: sólo %.0f %% a <= 0,5 km del cráter (esperado >= 60)" % (100 * frac)


def test_scripts_de_posicion_s134_anclan_en_vent():
    """Guard A13 (plan S134 §3). Pregunta 1: un script de `experiments/_s134_audit/` que
    calcule distancias al cráter leyendo `lat`/`lon` del catálogo sin mencionar `vent_lat`
    hace fallar el assert. Pregunta 2: se exige que haya al menos un script que calcule
    distancia (si el glob diera vacío, el test avisa en vez de pasar en verde)."""
    scripts = [f for f in glob.glob(os.path.join(AUDIT, "f*", "*.py")) if "verif_" not in os.path.basename(f)]
    assert scripts, "no hay scripts en experiments/_s134_audit/f*/"
    calcula_dist = []
    sin_vent = []
    for f in scripts:
        with open(f, encoding="utf-8", errors="replace") as fp:
            src = fp.read()
        if not re.search(r"haversine|def hav|_hav|asin\(", src):
            continue
        calcula_dist.append(f)
        usa_catalogo = re.search(r"""\[\s*['"]lat['"]\s*\]|\.get\(\s*['"]lat['"]""", src)
        if usa_catalogo and "vent_lat" not in src and "mirova_center_lat" not in src:
            sin_vent.append(os.path.relpath(f, ROOT))
    assert calcula_dist, "ningún script de _s134_audit calcula distancias: el guard no midió nada"
    assert not sin_vent, "scripts de posición que leen lat/lon del catálogo sin vent_*: %s" % sin_vent
