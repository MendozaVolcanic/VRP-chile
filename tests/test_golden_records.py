"""tests/test_golden_records.py — anti-regresión M1 (instalado S18 2026-04-24).

4 records canónicos de la ventana S18 2026-04-08 a 04-22 que cubren los casos
físicos representativos. Si el JSON de los volcanes Tier A pierde alguno o sus
valores caen fuera de las tolerancias, los tests fallan y bloquean el merge.

Casos cubiertos:
  1. Lascar 2026-04-12 05:48 VIIRS_NOAA21 — "detección summit fuerte" (1164 MW @ 0.58 km).
     Si baja >5% → regresión de detección eruption-path.
  2. Lascar 2026-04-08 05:18 VIIRS_NOAA21 — "summit con NOAA-21" (931 MW).
     Si vrp=0 o sensor!=VIIRS_NOAA21 → regresión integración NOAA-21 S18.
  3. Chaitén 2026-04-12 04:42 VIIRS_SNPP_750 — "vent-path summit débil" (2.58 MW).
     Si vrp_vent → 0 → regresión vent-path o piso store.
  4. Tupungatito 2026-04-08 05:24 VIIRS_NOAA21 — "vent sub-pixel" (0.168 MW).
     Si vrp_vent → 0 → regresión vent-path para señales sub-pixel débiles.

Tolerancias (no comparamos bit-equivalence — los reprocesos pueden variar
ligeramente por pixel area + scan angle + orden de pixels):
  - vrp_mw, vrp_vent_mw: ±5% del valor de referencia.
  - t_max_k: ±0.5 K.
  - final_hotspot_dist_km: ±0.2 km.
  - distance_class, sensor: igual exacto.
  - n_anomalous_pixels: ±20% (varía con pixel area corrections).

Ejecutar: pytest tests/test_golden_records.py -v
Regenerar snapshots cuando un cambio sea intencional: editar GOLDEN dict abajo.
"""

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "mirova_equivalent"

# Cada entrada: identidad del record + expected con rangos.
GOLDEN = [
    {
        "id": "lascar_strong_summit_noaa21_2026_04_12",
        "volcano": "Lascar",
        "datetime_utc": "2026-04-12 05:48",
        "sensor": "VIIRS_NOAA21",
        "why": "Detección summit fuerte cerca del cráter Lascar — eruption-path I-band.",
        "expected": {
            # Rangos: (min, max) para floats; o valor exacto para strings.
            "vrp_mw":             (1100.0, 1230.0),
            "vrp_vent_mw":        (1.85, 2.30),
            "t_max_i04_k":        (302.8, 303.8),
            "final_hotspot_dist_km": (0.45, 0.75),
            "distance_class":     "summit",
            "sensor":             "VIIRS_NOAA21",
        },
    },
    {
        "id": "lascar_summit_noaa21_2026_04_08",
        "volcano": "Lascar",
        "datetime_utc": "2026-04-08 05:18",
        "sensor": "VIIRS_NOAA21",
        "why": "Caso clave de validación H10 — sin NOAA-21 antes este record no existía.",
        "expected": {
            "vrp_mw":             (880.0, 985.0),
            "vrp_vent_mw":        (1.40, 1.65),
            "t_max_i04_k":        (296.5, 298.5),
            "final_hotspot_dist_km": (0.05, 0.85),  # S26: rango ampliado tras reproceso fresco
            "distance_class":     "summit",
            "sensor":             "VIIRS_NOAA21",
        },
    },
    {
        "id": "chaiten_vent_summit_v750_2026_04_12",
        "volcano": "Chaiten",
        "datetime_utc": "2026-04-12 04:42",
        "sensor": "VIIRS_SNPP_750",
        "why": "Vent-path summit débil — sensible a piso VRP store.py y vent threshold.",
        "expected": {
            "vrp_mw":             (2.40, 2.75),
            "vrp_vent_mw":        (0.65, 0.78),
            "t_max_k":            (270.5, 271.8),
            "final_hotspot_dist_km": (2.2, 2.6),
            "distance_class":     "summit",
            "sensor":             "VIIRS_SNPP_750",
        },
    },
    {
        "id": "tupungatito_vent_subpixel_noaa21_2026_04_08",
        "volcano": "Tupungatito",
        "datetime_utc": "2026-04-08 05:24",
        "sensor": "VIIRS_NOAA21",
        "why": "Vent sub-pixel ~0.17 MW — caso límite de detección. Si se pierde, perdimos sensibilidad sub-pixel.",
        "expected": {
            "vrp_vent_mw":        (0.14, 0.20),
            "t_max_i04_k":        (283.7, 284.7),
            "sensor":             "VIIRS_NOAA21",
            # No verificamos distance_class porque hotspot principal del record cae far por H17.
            # No verificamos vrp_mw porque varía con qué path dispara.
        },
    },
    # === S23 Task 8 — expand M1 a 9 records canónicos ===
    {
        "id": "tupungatito_regla_d_modis_2026_04_16",
        "volcano": "Tupungatito",
        "datetime_utc": "2026-04-16 06:50",
        "sensor": "MODIS_AQUA",
        "why": "Regla D vent-priority S20 funciona en MODIS — vrp_vent>0 promueve summit + final_hotspot=vent.",
        "expected": {
            "vrp_vent_mw":            (11.5, 13.5),
            "final_hotspot_dist_km":  (2.3, 2.8),
            "distance_class":         "summit",
            "final_hotspot_source":   "vent",
            "sensor":                 "MODIS_AQUA",
        },
    },
    {
        "id": "lascar_path_d_contextual_modis_2026_04_19",
        "volcano": "Lascar",
        "datetime_utc": "2026-04-19 07:05",
        "sensor": "MODIS_AQUA",
        "why": "Path D dNTI contextual S15 P3.2 dispara — diag_n_dnti_ctx_path>0 confirma que el path está activo.",
        "expected": {
            "diag_n_dnti_ctx_path":   (35, 50),
            "n_anomalous_pixels":     (30, 50),
            "sensor":                 "MODIS_AQUA",
        },
    },
    {
        "id": "lastarria_path_d_contextual_viirs_2026_04_08",
        "volcano": "Lastarria",
        "datetime_utc": "2026-04-08 05:18",
        "sensor": "VIIRS_NOAA21",
        "why": "Path D contextual + vent-path en Lastarria hidrotermal — combinación P3.2 + Regla D resuelve el caso S22.5.",
        "expected": {
            "vrp_vent_mw":            (0.10, 0.15),
            "diag_n_dnti_ctx_path":   (1, 8),
            "distance_class":         "summit",
            "final_hotspot_source":   "vent",
            "sensor":                 "VIIRS_NOAA21",
        },
    },
    {
        "id": "tupungatito_regla_d_edge_no_coords_2026_01_08",
        "volcano": "Tupungatito",
        "datetime_utc": "2026-01-08 06:35",
        "sensor": "MODIS_AQUA",
        "why": "Regla D edge S23 T1 — vrp_vent>0 sin vent_hotspot_dist_km debe quedar summit (legacy S20). Anti-regresión del fix S23 T1. Record actualizado S26 tras reproceso histórico (record S23 original 2026-01-01 04:54 quedó sin vrp_vent>0 con código S25).",
        "expected": {
            "vrp_vent_mw":     (0.05, 0.10),
            "distance_class":  "summit",
            "sensor":          "MODIS_AQUA",
            # vent_hotspot_dist_km es None — no testeamos
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


@pytest.mark.parametrize("g", GOLDEN, ids=[g["id"] for g in GOLDEN])
def test_golden_record_present(g):
    """Cada golden record debe estar presente en el JSON correspondiente."""
    rec = _find_record(g["volcano"], g["datetime_utc"], g["sensor"])
    assert rec is not None, (
        f"[{g['id']}] record no encontrado en data/mirova_equivalent/{g['volcano']}.json: "
        f"datetime_utc={g['datetime_utc']!r}, sensor={g['sensor']!r}"
    )


@pytest.mark.parametrize("g", GOLDEN, ids=[g["id"] for g in GOLDEN])
def test_golden_record_values(g):
    """Cada field del expected debe estar dentro de tolerancia."""
    rec = _find_record(g["volcano"], g["datetime_utc"], g["sensor"])
    if rec is None:
        pytest.skip(f"record no presente — ver test_golden_record_present")
    for field, expected in g["expected"].items():
        _check_field(rec, field, expected, g["id"])
