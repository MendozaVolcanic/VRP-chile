# -*- coding: utf-8 -*-
"""S172 (mini auditoría MA172-101/302): la vigilancia de la sombra de K no cuenta como K los records MODIS de la vía.

POR QUÉ. scripts/vigilancia_sombra.py compara K (producción) contra C0 (el laboratorio) y, si C0 publica una alerta
protegida que K calla, abre el issue que pre-autoriza revertir K (#850). Separaba «records de K» por `codigo_sha`, y
desde el encendido de MODIS los records de la vía también lo traen: una protegida que la vía calla y C0 publica habría
pedido revertir K por una pérdida que no es de K. La pérdida de la vía la vigila la guardia
(scripts/vigilancia_guardia_modis.py). Y como desde el encendido MODIS de producción ya no es K, la frescura de K en
MODIS deja de exigirse (si no, la vigilancia de K quedaría ciega para siempre tres días después del encendido).
Sin records de la vía, la salida es la de siempre (lo comprueba el informe sobre data/ de hoy).
"""
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.vigilancia_sombra as vs  # noqa: E402

DT = datetime(2026, 11, 10, 7, 20, tzinfo=timezone.utc)
VIA = {("NevadosDeChillan", "MODIS_AQUA", "2026-11-10 07:20")}


def _banco(monkeypatch, prod):
    bp = types.SimpleNamespace(
        inner_desde_html=lambda: {},
        cargar_nuestros=lambda coords, inner, win, data=None: [] if data == vs.SOMBRA else list(prod),
        indexar_referencia=lambda filas, coords, win, regla_minimas="original": (None, None, None, 0),
        etiquetar=lambda recs, *a: [r.__setitem__("lab", "x") for r in recs])
    monkeypatch.setitem(sys.modules, "banco_paridad", bp)
    monkeypatch.setitem(sys.modules, "referencia_mirova_unificada",
                        types.SimpleNamespace(cargar_referencia_unificada=lambda cons, ocr: []))
    monkeypatch.setattr(vs.aa, "_coords_por_volcan", lambda: {})


def test_los_records_modis_de_la_via_no_entran_como_k(monkeypatch):
    via = {"vol": "NevadosDeChillan", "b": "MODIS", "sensor": "MODIS_AQUA", "dt": DT, "sha": "f" * 40}
    k = {"vol": "NevadosDeChillan", "b": "MODIS", "sensor": "MODIS_TERRA", "dt": DT, "sha": "f" * 40}
    c0 = {"vol": "NevadosDeChillan", "b": "MODIS", "sensor": "MODIS_TERRA", "dt": DT, "sha": None}
    _banco(monkeypatch, [via, k, c0])
    _, prod, _ = vs.cargar_insumos(("2026-11-01", "2026-11-20"), via=VIA)
    assert prod == [k]
    # control: sin claves de la vía, el record de la vía entra como K (lo de antes de S172)
    _, prod, _ = vs.cargar_insumos(("2026-11-01", "2026-11-20"), via=set())
    assert via in prod and k in prod and c0 not in prod


def test_las_claves_de_la_via_salen_de_los_records_de_produccion(monkeypatch):
    recs = {"NevadosDeChillan": [
        {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-10 07:20", "via_codigo_mirova": True},
        {"sensor": "MODIS_TERRA", "datetime_utc": "2026-11-10 03:10", "via_codigo_mirova": "sin_mxd03"},
        {"sensor": "VIIRS_NOAA20_750", "datetime_utc": "2026-11-10 05:00", "via_codigo_mirova": True}]}
    monkeypatch.setattr(vs.aa, "cargar_records", lambda: (recs, {}))
    assert vs.claves_via() == VIA


@pytest.fixture
def insumos(monkeypatch):
    def poner(via, sin_modis):
        rel = [{"vol": v, "b": s, "dt": DT, "noche": "2026-11-19", "pub": False, "sensor": "x", "perfil": None,
                "lab": "sin_info", "lab_original": "sin_info"}
               for v in ("NevadosDeChillan",) for s in vs.aa.SENSORS]
        prod = [r for r in rel if not (sin_modis and r["b"] == "MODIS")]   # con la vía, producción no tiene K en MODIS
        filas = [{"volcano": "Lascar", "sensor_bucket": "MODIS", "fecha_utc": "2026-11-19 06:00:00", "vrp_mw": 0.0,
                  "tipo": "RUTINA", "source": "CONS"}]
        monkeypatch.setattr(vs, "cargar_insumos", lambda win, via=None: (filas, prod, rel))
        monkeypatch.setattr(vs, "claves_via", lambda: via)
        monkeypatch.setattr(vs.aa, "leer_frontera_k", lambda *a: "2026-09-18")
        monkeypatch.setattr(vs, "leer_adopcion", lambda *a: "2026-10-18 09:57:30")
        monkeypatch.setattr(vs, "_diurna_por_defecto", lambda: (lambda *a: False))
        monkeypatch.setattr(vs.aa, "VOLS", ["NevadosDeChillan"])
        monkeypatch.setattr(vs, "leer_juzgadas", lambda *a: {})
        monkeypatch.setattr(vs, "leer_rachas_juzgadas", lambda *a: {})
    return poner


def test_con_la_via_la_frescura_de_k_no_se_exige_en_modis(insumos):
    insumos(VIA, sin_modis=True)
    out = vs.evaluar("2026-11-20")
    assert out["veredicto"] == "VERDE", out["avisos"]
    assert out["via_modis_excluida"] == 1


def test_control_sin_la_via_una_produccion_sin_modis_si_es_ciega(insumos):
    """Sin records de la vía, producción sin MODIS sigue siendo vigilancia ciega (lo de S156), y no hay clave nueva."""
    insumos(set(), sin_modis=True)
    out = vs.evaluar("2026-11-20")
    assert out["veredicto"] == "VIGILANCIA_CIEGA" and "via_modis_excluida" not in out
    insumos(set(), sin_modis=False)
    assert vs.evaluar("2026-11-20")["veredicto"] == "VERDE"
