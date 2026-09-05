# -*- coding: utf-8 -*-
"""Guards de la regla B para los pendientes que AUDIT_S134 §0 cerró (P1, P4, P5, P10).

POR QUÉ. El protocolo de auditoría (docs/PROTOCOLO_AUDITORIA_PROFUNDA.md, regla B) prohíbe
cerrar un pendiente con prosa: nueve hallazgos se redescubrieron en más de una auditoría
porque nadie dejó un test que midiera que seguían cerrados. Cada test de acá mide el
invariante que F5 verificó a mano el 2026-09-05 (experiments/_s134_audit/f5/REGLA_C.md).

Las dos preguntas del instrumento, por test, están en su docstring.
"""
import functools
import glob
import json
import os
from collections import Counter

import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data", "mirova_equivalent")
TIER_A = [
    "Lascar", "Isluga", "Lastarria", "Llaima", "Villarrica", "Copahue", "Chaiten",
    "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle", "Tupungatito",
]


@functools.lru_cache(maxsize=None)
def _records(vol):
    p = os.path.join(DATA, vol + ".json")
    if not os.path.exists(p):
        pytest.skip("sin data local para %s" % vol)
    with open(p, encoding="utf-8") as fp:
        d = json.load(fp)
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    # Sólo lo que los guards miran: baja la memoria ~10× (el disco al 100 % dejó sin pagefile en S134).
    return tuple({k: r.get(k) for k in ("sensor", "granule", "datetime_utc", "diag_nti_max", "primary_cluster")}
                 for r in recs if isinstance(r, dict))


def test_p1_gazetteer_existe_con_pcc_y_lastarria():
    """P1. Si el gazetteer se borrara o perdiera sus dos entradas, falla (pregunta 1: sí).
    Si el YAML no se leyera, `safe_load` levanta: no hay cero silencioso (pregunta 2: sí)."""
    p = os.path.join(ROOT, "pipeline", "volcanic_features.yaml")
    assert os.path.exists(p), "el gazetteer A54 vive en pipeline/volcanic_features.yaml (S88)"
    with open(p, encoding="utf-8") as fp:
        cfg = yaml.safe_load(fp)
    texto = json.dumps(cfg, ensure_ascii=False)
    assert "Caulle" in texto and "Lazufre" in texto, (
        "el gazetteer perdió el lacolito de PCC o el campo Lazufre de Lastarria")


@pytest.mark.parametrize("vol", TIER_A)
def test_p4_sin_records_duplicados_por_granule(vol):
    """P4. Un record repetido por (sensor, granule) infla n y la magnitud agregada.
    Pregunta 1: un duplicado real hace fallar el assert. Pregunta 2: si el JSON no
    cargara, `_records` levanta o salta; el 0 sólo aparece con n > 0 (se exige)."""
    recs = _records(vol)
    claves = Counter(
        (r.get("sensor"), r.get("granule")) for r in recs
        if isinstance(r, dict) and r.get("granule"))
    assert sum(claves.values()) > 0, "sin records con granule: el instrumento no midió nada"
    dup = {k: n for k, n in claves.items() if n > 1}
    assert not dup, "records duplicados por (sensor, granule) en %s: %s" % (vol, list(dup)[:5])


def test_p5_diag_nti_max_persistido_en_modis():
    """P5. El nombre en el punto de uso es `diag_nti_max` (A89), no `nti_max`.
    Pregunta 1: si el pipeline dejara de persistirlo, la fracción cae y falla.
    Pregunta 2: se exige n ≥ 20 records MODIS para que el cero no sea «no medí»."""
    recs = [r for r in _records("Villarrica")
            if isinstance(r, dict) and str(r.get("sensor", "")).startswith("MODIS")
            and str(r.get("datetime_utc", ""))[:10] >= "2026-06-01"]
    assert len(recs) >= 20, "muy pocos records MODIS desde 2026-06-01 para medir (n=%d)" % len(recs)
    con = sum(1 for r in recs if r.get("diag_nti_max") is not None)
    assert con / len(recs) >= 0.95, "diag_nti_max falta en %d de %d records MODIS" % (len(recs) - con, len(recs))


def test_p10_cap_path_d_activo_en_perfil_operacional():
    """P10. El cap de path D (A72) se lee del perfil por `pipeline.profile`, no del YAML.
    Pregunta 1: si alguien lo quita del perfil, el valor efectivo es None y falla.
    Pregunta 2: se lee el módulo efectivo, no un grep del texto."""
    os.environ["VRP_PROFILE"] = "mirova_equivalent"
    import importlib
    import pipeline.profile as p
    importlib.reload(p)
    assert p.PATH_D_ONLY_CAP_MW is not None and p.PATH_D_ONLY_CAP_TBG_MAX_K is not None, (
        "el cap de path D dejó de estar en el perfil operacional")
    recs = _records("PuyehueCordonCaulle")
    con = sum(1 for r in recs if isinstance(r, dict)
              and (r.get("primary_cluster") or {}).get("d9_capped") is not None)
    assert con > 0, "ningún record de PCC persiste primary_cluster.d9_capped"
