"""tests/test_golden_records.py — anti-regresión M1 (instalado S18; REGENERADO S116 2026-06-27).

Records canónicos que capturan casos físicos representativos del pipeline ACTUAL.
Si el JSON de los volcanes Tier A pierde alguno o sus valores caen fuera de las
tolerancias, los tests fallan y bloquean el merge.

S116 (regeneración, cierra contradicción C3 de AUDIT_S116): los 8 goldens previos
fueron capturados S18 con pipeline pre-S27 (vent-path activo, dual-ROI BT off,
exclude_zones on, cap=7K, magnitudes pre-nadir/focal infladas ~1000×) y quedaron
SKIPPED desde S32 sin regenerar — la suite "verde" enmascaraba la pérdida de
cobertura. Re-derivados contra el estado actual: se descartaron los casos que
probaban mecanismos REMOVIDOS (vent-path `vrp_vent_mw`, Regla D vent-priority
`final_hotspot_source="vent"`), un record que ya no se detecta (Chaitén V750,
cat-b sub-umbral → ~0, como MIROVA) y otro que ya no existe en la ventana de datos
(Tupungatito Jan). Los reemplazan casos del pipeline vigente:
  1. Lascar 2026-04-12 05:48 VIIRS_NOAA21 — summit fuerte VIIRS375 (~1.19 MW post de-inflación nadir/focal).
  2. Lascar 2026-04-08 05:18 VIIRS_NOAA21 — integración NOAA-21 (H10): si vrp=0/sensor!=NOAA21 → regresión.
  3. Lastarria 2026-04-08 05:18 VIIRS_NOAA21 — clasificación ancla-honesta `ctx_cluster` summit (Lazufre/A69).
  4. Villarrica 2026-05-09 06:36 VIIRS_NOAA20 — sub-pixel lava lake `test1_roi` (guard FN sub-umbral).
La geometría MODIS (far→summit/D12, A82) queda cubierta por test_r2_pixel_level
(caso "Isluga MODIS hot"), no se fuerza un golden MODIS-summit limpio (no existe
por el bug de etiquetado A46 irreducible a 1 km, AUDIT_S114).

Tolerancias (no comparamos bit-equivalence — los reprocesos pueden variar
ligeramente por pixel area + scan angle + orden de pixels):
  - vrp_mw: ~±10% del valor de referencia (captura drift estructural tipo
    de-inflación 1000×, tolera jitter de reproceso).
  - t_max_i04_k / t_max_k: ±1.5 K.
  - final_hotspot_dist_km: ±0.3 km.
  - distance_class, sensor, final_hotspot_source: igual exacto.
  - diag_n_dnti_ctx_path: rango (captura si el path se apaga/cambia).

Ejecutar: pytest tests/test_golden_records.py -v
Regenerar snapshots cuando un cambio sea INTENCIONAL: editar GOLDEN dict abajo
(documentando en el commit por qué cambió el valor de referencia).

S158 (reemplazo del histórico con K, tarea 1.24): el golden 4 se DIO VUELTA. Villarrica 2026-05-09
06:36 VIIRS_NOAA20 lo publicaba el detector anterior por el Test 1 integrado (~0,04 MW), pero en
esa pasada MIROVA no vio nada: el consolidado del scraper la trae como RUTINA con 0,0 MW en VIIRS375
y en VIIRS (data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv). Era una
publicación de más, no sensibilidad. K la calla, como MIROVA. El golden vigila ahora esa paridad:
si K vuelve a publicar ahí, falla. La sensibilidad sub-píxel real de Villarrica la vigila la
sombra del paso 9 (scripts/vigilancia_sombra.py), contra las alertas de MIROVA y no contra C0.
"""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "mirova_equivalent"

# Cada entrada: identidad del record + expected con rangos.
# Valores de referencia capturados S116 2026-06-27 del estado actual de
# data/mirova_equivalent/ (todos product_version=standard).
GOLDEN = [
    {
        "id": "lascar_strong_summit_noaa21_2026_04_12",
        "volcano": "Lascar",
        "datetime_utc": "2026-04-12 05:48",
        "sensor": "VIIRS_NOAA21",
        "why": "Detección summit fuerte VIIRS375 cerca del cráter Lascar. Magnitud "
               "post de-inflación nadir/focal (~1.19 MW; pre-S102 reportaba ~1164). "
               "Si baja a ~0 o sube ~1000× → regresión de magnitud o detección eruption-path.",
        "expected": {
            # Rangos: (min, max) para floats; o valor exacto para strings.
            "vrp_mw":                (1.07, 1.31),
            "t_max_i04_k":           (302.0, 304.5),
            "final_hotspot_dist_km": (0.0, 0.45),
            "distance_class":        "summit",
            "sensor":                "VIIRS_NOAA21",
        },
        # S180: valor de la vía (reproceso P4, run 42749607584, código a7a6ae360): 1,41 MW, t_max_k 294,0 K, 0,149 km.
        "expected_via": {
            "vrp_mw":                (1.27, 1.55),
            "t_max_k":               (292.5, 295.5),
            "final_hotspot_dist_km": (0.0, 0.45),
            "distance_class":        "summit",
            "final_hotspot_source":  "codigo_mirova",
            "sensor":                "VIIRS_NOAA21",
        },
    },
    {
        "id": "lascar_summit_noaa21_2026_04_08",
        "volcano": "Lascar",
        "datetime_utc": "2026-04-08 05:18",
        "sensor": "VIIRS_NOAA21",
        "why": "Caso clave de validación H10 — sin la integración NOAA-21 (S18) este "
               "record no existía. Si vrp=0 o sensor!=VIIRS_NOAA21 → regresión NOAA-21.",
        "expected": {
            "vrp_mw":                (0.72, 0.89),
            "t_max_i04_k":           (296.0, 299.0),
            "final_hotspot_dist_km": (0.0, 0.45),
            "distance_class":        "summit",
            "sensor":                "VIIRS_NOAA21",
        },
        # S180: valor de la vía (P4): 1,541 MW, t_max_k 296,57 K, 0,112 km.
        "expected_via": {
            "vrp_mw":                (1.39, 1.70),
            "t_max_k":               (295.0, 298.0),
            "final_hotspot_dist_km": (0.0, 0.45),
            "distance_class":        "summit",
            "final_hotspot_source":  "codigo_mirova",
            "sensor":                "VIIRS_NOAA21",
        },
    },
    {
        "id": "lastarria_honest_anchor_ctxcluster_2026_04_08",
        "volcano": "Lastarria",
        "datetime_utc": "2026-04-08 05:18",
        "sensor": "VIIRS_NOAA21",
        "why": "Clasificación por ancla honesta: el dNTI contextual (Path D, "
               "diag_n_dnti_ctx_path>0) ancla en ctx_cluster y clasifica summit el "
               "campo fumarólico Lazufre (A69 extensión real). Anti-regresión de la "
               "cascada de posición S106-S111. No verificamos magnitud (sub-MW volátil).",
        "expected": {
            "distance_class":       "summit",
            "final_hotspot_source": "ctx_cluster",
            "diag_n_dnti_ctx_path": (1, 8),
            "sensor":               "VIIRS_NOAA21",
        },
        # S180: la vía no tiene ancla ctx_cluster ni path D; publica 0,111 MW a 2,254 km, summit (dentro de los 3 km
        # del inner de Lastarria). Se vigila la clase y la fuente, no la magnitud (sub-MW volátil, como antes).
        "expected_via": {
            "distance_class":       "summit",
            "final_hotspot_source": "codigo_mirova",
            "sensor":               "VIIRS_NOAA21",
        },
    },
    {
        "id": "villarrica_negativo_limpio_noaa20_2026_05_09",
        "volcano": "Villarrica",
        "datetime_utc": "2026-05-09 06:36",
        "sensor": "VIIRS_NOAA20",
        "why": "S158: pasada en que MIROVA no vio nada (RUTINA, 0,0 MW) y que el detector "
               "anterior publicaba por el Test 1 integrado. Con K el record queda sin "
               "detección, como MIROVA. Si vrp vuelve a ser > 0, K volvió a publicar de "
               "más donde MIROVA calla. Antes (S116) era el golden sub-píxel test1_roi.",
        "expected": {
            "vrp_mw":                (0.0, 0.0),
            "distance_class":        None,
            "final_hotspot_source":  None,
            "sensor":                "VIIRS_NOAA20",
        },
    },
]


def _find_record(volcano, datetime_utc, sensor):
    p = DATA_DIR / f"{volcano}.json"
    if not p.exists():
        pytest.skip(f"{p} no existe — los tests golden requieren JSONs Tier A presentes")
    d = json.load(open(p, "r", encoding="utf-8"))
    for r in d.get("records", []):
        if r.get("datetime_utc", "").startswith(datetime_utc) and r.get("sensor") == sensor:
            return r
    return None


def _check_field(record, field, expected, golden_id):
    actual = record.get(field)
    if isinstance(expected, tuple):
        lo, hi = expected
        assert actual is not None, f"[{golden_id}] field '{field}' es None, esperaba rango [{lo}, {hi}]"
        assert lo <= actual <= hi, (
            f"[{golden_id}] field '{field}' = {actual} fuera del rango [{lo}, {hi}]"
        )
    else:
        assert actual == expected, (
            f"[{golden_id}] field '{field}' = {actual!r}, esperaba {expected!r}"
        )


def _expected_de(g, rec):
    """S180: la historia publicada pasa de K a la vía «código MIROVA» (reemplazo de la historia, decisión de Nicolás
    del 2026-11-11). Cada golden fija el valor del detector que escribió el record: `expected` el de K y
    `expected_via` el de la vía (capturado del reproceso P4). Sin `expected_via`, el mismo `expected` vale para los dos
    (Villarrica, negativo limpio: la vía también calla). Cuando no quede K publicado, `expected` de K se puede retirar."""
    if rec.get("via_codigo_mirova") is True and "expected_via" in g:
        return g["expected_via"]
    return g["expected"]


@pytest.mark.parametrize("g", GOLDEN, ids=[g["id"] for g in GOLDEN])
def test_golden_record_present(g):
    """Cada golden record debe estar presente en el JSON correspondiente."""
    rec = _find_record(g["volcano"], g["datetime_utc"], g["sensor"])
    assert rec is not None, (
        f"[{g['id']}] record no encontrado en data/mirova_equivalent/{g['volcano']}.json: "
        f"datetime_utc={g['datetime_utc']!r}, sensor={g['sensor']!r}"
    )


def test_expected_por_detector_elige_segun_la_marca():
    g = {"expected": {"x": 1}, "expected_via": {"x": 2}}
    assert _expected_de(g, {"via_codigo_mirova": True}) == {"x": 2}
    assert _expected_de(g, {}) == {"x": 1}
    assert _expected_de(g, {"via_codigo_mirova": "sin_grilla"}) == {"x": 1}   # caída a K: valores de K
    assert _expected_de({"expected": {"x": 1}}, {"via_codigo_mirova": True}) == {"x": 1}


@pytest.mark.parametrize("g", GOLDEN, ids=[g["id"] for g in GOLDEN])
def test_golden_record_values(g):
    """Cada field del expected debe estar dentro de tolerancia."""
    rec = _find_record(g["volcano"], g["datetime_utc"], g["sensor"])
    if rec is None:
        pytest.skip(f"record no presente — ver test_golden_record_present")
    for field, expected in _expected_de(g, rec).items():
        _check_field(rec, field, expected, g["id"])
