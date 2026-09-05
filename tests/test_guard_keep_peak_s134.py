# -*- coding: utf-8 -*-
"""Guards de la regla B para los dos defectos CONFIRMADOS y NO arreglados de AUDIT_S134 §3.

POR QUÉ. La regla B del protocolo (docs/PROTOCOLO_AUDITORIA_PROFUNDA.md) prohíbe cerrar un
hallazgo con prosa. Pero acá el hallazgo es un defecto vivo que la auditoría no arregla (A45:
nada en pipeline/ sin tag y confirmación). Un test que «fije» el defecto sería absurdo; un test
que describa el comportamiento correcto hoy falla. La forma canónica es el **xfail estricto**:
el test afirma lo correcto, se marca como falla esperada, y el día que un cambio lo cure el
XPASS rompe la suite y obliga a actualizar docs/AUDIT_S134.md, docs/MIROVA_DIVERGENCES.md y
este archivo. Así el arreglo no puede entrar en silencio ni el defecto volver sin ruido.

Fenómeno (F3 H1, verificado gravedad 5): en un cono nevado el píxel más caliente en MIR de un
disco de 3 km alrededor de la cumbre es el borde del disco, no el cráter (A69). El filtro
contextual del Test 1 con `keep_peak` (pipeline/process_viirs.py:1777-1786) conserva sólo ese
píxel cuando la máscara dNTI está vacía, y el ancla honesta (pipeline/anchor.py:89) lo publica
como summit a 0,0 km con la magnitud de un píxel que está bajo el fondo global.

Fenómeno (F3 H2, verificado gravedad 3): `second_pass_adjacent` corre con conjunto activo vacío
y sin la compuerta térmica del first pass (pipeline/detection_context.py:877-879 vs :518-523),
contra Coppola 2016a (documentacion/sp426_5.txt:329-341), y publica píxeles a 3-4 km.

Las dos preguntas del instrumento están en cada docstring.
"""
import json
import math
import os

import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data", "mirova_equivalent")
DESDE = "2026-06-01"


def _hav(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))


def _vent(vol):
    with open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8") as fp:
        cfg = yaml.safe_load(fp)
    vols = cfg["volcanoes"] if isinstance(cfg, dict) and "volcanoes" in cfg else cfg
    it = vols if isinstance(vols, list) else [dict(name=k, **x) for k, x in vols.items()]
    v = next(v for v in it if v.get("name") == vol)
    return v["vent_lat"], v["vent_lon"]


def _summit_v375(vol):
    p = os.path.join(DATA, vol + ".json")
    if not os.path.exists(p):
        pytest.skip("sin data local de %s" % vol)
    with open(p, encoding="utf-8") as fp:
        d = json.load(fp)
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    out = []
    for r in recs:
        if not isinstance(r, dict):
            continue
        s = str(r.get("sensor", ""))
        if not (s.startswith("VIIRS") and not s.endswith("750")):
            continue
        if str(r.get("datetime_utc", ""))[:10] < DESDE or r.get("distance_class") != "summit":
            continue
        pc = r.get("primary_cluster") or {}
        mag = r.get("f5_core_vrp_mw") or pc.get("vrp_mw")
        if not mag or mag <= 0:
            continue
        out.append({k: r.get(k) for k in ("final_hotspot_source", "final_hotspot_dist_km", "t_bg_k",
                                           "anomaly_pixels", "diag_n_first_pass_pixels",
                                           "diag_n_second_pass_recapture")})
    return out


@pytest.mark.xfail(strict=True, reason=(
    "AUDIT_S134 §3 H1 (gravedad 5): keep_peak publica el borde del disco del Test 1 como summit a "
    "0,0 km con BT bajo el fondo global. Si este test pasa, alguien lo curó: actualizar AUDIT_S134, "
    "MIROVA_DIVERGENCES y quitar el xfail."))
def test_keep_peak_no_publica_pixeles_bajo_el_fondo_como_summit():
    """Comportamiento correcto: un record publicado como summit a 0,0 km desde el Test 1 no debería
    tener su único píxel a más de 2 km del cráter Y más frío que el fondo global. Pregunta 1: si el
    mecanismo estuviera roto (como hoy) la fracción es ~70 % en Villarrica y el assert falla — por
    eso es xfail. Pregunta 2: se exige n ≥ 50 records `test1_roi` para que el resultado no sea un
    cero de «no medí» (con menos, skip, no pass)."""
    la, lo = _vent("Villarrica")
    t1 = [r for r in _summit_v375("Villarrica") if r["final_hotspot_source"] == "test1_roi"
          and r["anomaly_pixels"] and r["t_bg_k"] is not None]
    if len(t1) < 50:
        pytest.skip("muy pocos records test1_roi para medir (n=%d)" % len(t1))
    malos = 0
    for r in t1:
        px = max(r["anomaly_pixels"], key=lambda q: q.get("vrp_mw") or 0)
        d = _hav(px["lat"], px["lon"], la, lo)
        if d > 2.0 and px.get("bt_k") is not None and px["bt_k"] < r["t_bg_k"] and r["final_hotspot_dist_km"] == 0.0:
            malos += 1
    frac = malos / len(t1)
    assert frac < 0.10, (
        "%d de %d records test1_roi de Villarrica (%.0f %%) publican a 0,0 km un píxel a >2 km del "
        "cráter más frío que el fondo" % (malos, len(t1), 100 * frac))


@pytest.mark.xfail(strict=True, reason=(
    "AUDIT_S134 §3 H2 (gravedad 3): second_pass_adjacent corre con conjunto activo vacío y publica "
    "records sin primer pase, contra Coppola 2016a. Si pasa, alguien lo curó: actualizar docs."))
def test_second_pass_no_publica_sin_primer_pase():
    """Comportamiento correcto (Coppola 2016a): el second run sólo refina vecinos de píxeles ya
    activos, así que ningún record publicado debería tener first pass = 0 y recaptura > 0.
    Pregunta 1: hoy son 89/323 en Chaitén → falla (xfail). Pregunta 2: se exige que existan los
    campos diag en ≥ 50 records; si no, skip."""
    recs = [r for r in _summit_v375("Chaiten") if r["diag_n_first_pass_pixels"] is not None
            and r["diag_n_second_pass_recapture"] is not None]
    if len(recs) < 50:
        pytest.skip("sin diag_n_* suficientes en Chaitén (n=%d)" % len(recs))
    sin_fp = sum(1 for r in recs if r["diag_n_first_pass_pixels"] == 0 and r["diag_n_second_pass_recapture"] > 0)
    assert sin_fp == 0, "%d de %d records summit de Chaitén publicados por second pass sin primer pase" % (sin_fp, len(recs))
