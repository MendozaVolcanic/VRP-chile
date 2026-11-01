# -*- coding: utf-8 -*-
"""Guard S158: desde la frontera de K, la serie que publica el tablero no trae records del detector anterior.

POR QUÉ. Tras el reemplazo del histórico con K (tarea 1.24) quedaban 64 pasadas de Suomi NPP del 5 y 6 de agosto de
2026 sin reprocesar (NASA no tiene ni el NRT ni el estándar de esos días) y 26 de MODIS Terra de fines de septiembre y
octubre que el NRT escribió con C0 antes de la adopción (sin estándar de Terra para el reproceso de 30 días). Ninguna
trae `regimen.codigo_sha`. El verificador limpio de S158 midió que 25 de las de agosto publican, juntas en las mismas
dos pasadas del 2026-08-06 en 8 volcanes: un pulso térmico simultáneo que es el detector viejo y no los volcanes.
La prueba de frontera de S155 no lo ve porque admite un 5 % sin marca. Nicolás decidió el 2026-10-21 sacarlas a
`data/_c0_residuales/` (nada se borra) y dejar la serie publicada pura K.

Esta prueba exige el 100 % desde `DATOS_K_DESDE_UTC` y que los residuos apartados sigan existiendo y sean C0.
"""
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data" / "mirova_equivalent"
RESIDUOS = RAIZ / "data" / "_c0_residuales"
MODULO = RAIZ / "frontend" / "cambio_detector.js"
TIER_A = ["Lascar", "Lastarria", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue", "Llaima",
          "Villarrica", "PuyehueCordonCaulle", "Chaiten", "Isluga"]


def frontera() -> str:
    m = re.search(r'^\s*const DATOS_K_DESDE_UTC = "(\d{4}-\d{2}-\d{2})T00:00:00Z";',
                  MODULO.read_text(encoding="utf-8"), re.M)
    assert m, "cambio_detector.js tiene que declarar DATOS_K_DESDE_UTC"
    return m.group(1)


def es_k(r: dict) -> bool:
    return bool((r.get("regimen") or {}).get("codigo_sha"))


def sin_marca_desde(records: list, desde: str) -> list:
    return [(r.get("datetime_utc"), r.get("sensor")) for r in records
            if (r.get("datetime_utc") or "")[:10] >= desde and not es_k(r)]


def test_control_la_cuenta_ve_un_record_sin_marca():
    """Control positivo: un solo record C0 dentro de K tiene que aparecer en la cuenta."""
    recs = [{"datetime_utc": "2026-08-06 05:12", "sensor": "VIIRS_SNPP", "regimen": {"codigo_sha": "abc"}},
            {"datetime_utc": "2026-08-06 06:48", "sensor": "VIIRS_SNPP", "regimen": None},
            {"datetime_utc": "2025-01-01 05:00", "sensor": "VIIRS_SNPP"}]
    assert sin_marca_desde(recs, "2025-02-15") == [("2026-08-06 06:48", "VIIRS_SNPP")]


def test_la_serie_publicada_es_pura_k_desde_la_frontera():
    desde = frontera()
    problemas = {}
    for v in TIER_A:
        recs = json.loads((DATOS / f"{v}.json").read_text(encoding="utf-8")).get("records", [])
        malos = sin_marca_desde(recs, desde)
        if malos:
            problemas[v] = (len(malos), malos[:3])
    assert not problemas, (
        f"records sin marca de K desde {desde} en la serie publicada (apartarlos a data/_c0_residuales/ con "
        f"experiments/_s158_reemplazo/apartar_c0.py, no borrarlos): {problemas}")


def test_los_residuos_apartados_existen_y_son_c0():
    """Lo apartado no se pierde: cada archivo de residuos trae records C0 con motivo, y ninguno sigue en la serie."""
    archivos = sorted(RESIDUOS.glob("*.json"))
    assert archivos, "no hay residuos apartados en data/_c0_residuales/"
    for p in archivos:
        d = json.loads(p.read_text(encoding="utf-8"))
        assert d.get("motivo", "").strip(), f"{p.name}: sin motivo"
        recs = d.get("records", [])
        assert recs and not any(es_k(r) for r in recs), f"{p.name}: vacío o con records de K"
        serie = json.loads((DATOS / p.name).read_text(encoding="utf-8")).get("records", [])
        claves = {(r.get("datetime_utc"), r.get("sensor")) for r in serie}
        dup = [(r.get("datetime_utc"), r.get("sensor")) for r in recs
               if (r.get("datetime_utc"), r.get("sensor")) in claves]
        assert not dup, f"{p.name}: {len(dup)} residuos siguen también en la serie, p. ej. {dup[:2]}"
