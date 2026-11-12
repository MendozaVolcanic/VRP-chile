# -*- coding: utf-8 -*-
"""S180: la unión commiteada en experiments/_s180_reemplazo_via/historia_via/ es la que el reemplazo publicaría.

POR QUÉ. `aplicar-reemplazo.yml` pasa esos .json.gz a `data/mirova_equivalent/` sin rehacer la unión. Si alguien los
regenera con un trozo de menos, con records K o con otro perfil, el tablero publicaría eso como historia. La unión
pasa a alimentar el tablero, así que deja de ser descartable (A88). Esta prueba fija lo que se verificó al
commitearla: los 11 Tier A, del 2025-02-15 al 2026-11-11, sin huecos de calendario, todos los records con la vía y
con el perfil del brazo.
"""
import gzip
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
UNION = ROOT / "experiments" / "_s180_reemplazo_via" / "historia_via"
TIER_A = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "Chaiten",
          "Villarrica", "NevadosDeChillan", "Llaima", "Copahue"]
DESDE, HASTA = "2025-02-15", "2026-11-11"


def _dias_con_pasada(recs):
    return {r["datetime_utc"][:10] for r in recs}


@pytest.mark.parametrize("v", TIER_A)
def test_union_del_volcan_completa_y_toda_con_la_via(v):
    s = json.loads(gzip.decompress((UNION / f"{v}.json.gz").read_bytes()))
    recs = s["records"]
    assert s["volcano"] == v and recs
    assert all(r.get("via_codigo_mirova") is True for r in recs), "record sin la vía en la unión"
    assert all((r.get("regimen") or {}).get("perfil") == "_s172_retro_paquete" for r in recs)
    assert min(r["datetime_utc"] for r in recs)[:10] >= DESDE
    assert max(r["datetime_utc"] for r in recs)[:10] <= HASTA
    claves = [(r["datetime_utc"], r["sensor"]) for r in recs]
    assert len(claves) == len(set(claves)), "clave repetida"
    # Una semana sin ninguna pasada sería un trozo que falta (los trozos son de 10 a 20 días). Medido al commitear:
    # la peor racha sin pasada es 0 días en los 11 volcanes.
    d0, d1 = date.fromisoformat(DESDE), date.fromisoformat(HASTA)
    con = _dias_con_pasada(recs)
    racha, peor = 0, 0
    for n in range((d1 - d0).days + 1):
        racha = 0 if (d0 + timedelta(n)).isoformat() in con else racha + 1
        peor = max(peor, racha)
    assert peor < 7, f"{v}: {peor} días seguidos sin pasada en la unión"


def test_informe_de_la_union_sin_huecos():
    inf = json.loads((UNION / "informe_union.json").read_text(encoding="utf-8"))
    assert sorted(inf["volcanes"]) == sorted(TIER_A)
    for v, x in inf["volcanes"].items():
        assert (x["desde"], x["hasta"], x["huecos"]) == (DESDE, HASTA, []), v
