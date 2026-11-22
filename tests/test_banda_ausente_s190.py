# -*- coding: utf-8 -*-
"""S190 (H03 de la auditoría de Codex, verificado en D:\\vrp-trabajo\\temporales\\s190_codex\\verif\\V2\\): un L1B
VIIRS al que le falta una banda que la vía «código MIROVA» necesita no puede pasar por una noche tranquila.

POR QUÉ, COMO GEÓLOGO. La vía mide el calor con dos bandas: la de infrarrojo medio (I04 en 375 m, M13 en 750 m), que
ve el material caliente, y la térmica (I05, M15), que da el fondo frío contra el que se compara. Si NASA entrega un
archivo sin una de ellas, esa pasada no se pudo medir. Hasta S190 el procesador devolvía `None` en silencio: la pasada
desaparecía sin record, sin incidencia y con «Cobertura: completa», como si el satélite no hubiera pasado. En una
erupción eso es un hueco que nadie ve.

QUÉ EXIGE. (1) El procesador de cada familia (VIIRS 375 y VIIRS 750) lanza un error que nombra la banda que falta y el
gránulo. (2) De punta a punta, `run_pipeline` lo registra como `error_procesamiento` (cuenta en modo estricto: salida
3) y deja la línea `ERROR processing` que el revisor de errores del NRT clasifica por sensor y convierte en rojo.
(3) La interfaz `None` de `leer_radiancia_l1b` no cambia (la usan otros consumidores).

LAS DOS PREGUNTAS DEL INSTRUMENTO. ¿Puede dar rojo? Sí: sin el arreglo (1) y (2) fallan por aserción (el procesador
devuelve None; la incidencia es `sin_record`, que no cuenta en modo estricto, y el revisor no ve ningún error).
Controles: con las dos bandas presentes no se informa ninguna banda ausente; el revisor sí clasifica un error de
control en cada sensor.
"""
import sys
from datetime import datetime
from pathlib import Path

import h5py
import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.run_pipeline as rp  # noqa: E402
import scripts.revisar_errores_modis_nrt as rev  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline import process_viirs, process_viirs_mod  # noqa: E402

LASCAR = next(v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]
              if v["name"] == "Lascar")
FECHA = datetime(2026, 11, 10)

# plataforma -> (módulo, flag de la vía, L1B, GEO, banda presente, banda ausente, clave del revisor)
CASOS = {
    "VIIRS_NOAA20": (process_viirs, "ENABLE_V375_CODIGO_MIROVA", "VJ102IMG.A2026314.0554.021.nc",
                     "VJ103IMG.A2026314.0554.021.nc", "I04", "I05", "VIIRS375"),
    "VIIRS_NOAA20_750": (process_viirs_mod, "ENABLE_V750_CODIGO_MIROVA", "VJ102MOD.A2026314.0554.021.nc",
                         "VJ103MOD.A2026314.0554.021.nc", "M13", "M15", "VIIRS750"),
}


def _l1b(ruta: Path, bandas) -> Path:
    """L1B mínimo: sólo `observation_data` con las bandas pedidas (DN 1, sin banderas)."""
    with h5py.File(ruta, "w") as f:
        g = f.create_group("observation_data")
        for b in bandas:
            g.create_dataset(b, data=np.ones((2, 2), dtype=np.uint16))
    return ruta


def _calcular(modulo, l1b: Path, geo: Path):
    return modulo.calculate_vrp(l1b, geo, LASCAR["lat"], LASCAR["lon"], LASCAR["radius_km"],
                                inner_radius_km=LASCAR.get("inner_radius_km"))


@pytest.mark.parametrize("plataforma", list(CASOS))
def test_procesador_nombra_la_banda_ausente(plataforma, tmp_path, monkeypatch):
    modulo, flag, n_l1b, n_geo, presente, ausente, _ = CASOS[plataforma]
    monkeypatch.setattr(modulo, flag, True)
    l1b = _l1b(tmp_path / n_l1b, [presente])
    geo = tmp_path / n_geo
    geo.write_bytes(b"no se lee: falta una banda antes de geolocalizar")
    with pytest.raises(ValueError) as exc:
        _calcular(modulo, l1b, geo)
    msg = str(exc.value)
    assert f"'{ausente}'" in msg or f" {ausente}" in msg, msg
    assert presente not in msg.replace(n_l1b, ""), f"nombra una banda que sí está: {msg}"
    assert n_l1b in msg, msg


@pytest.mark.parametrize("plataforma", list(CASOS))
def test_banda_ausente_deja_rojo_de_punta_a_punta(plataforma, tmp_path, monkeypatch, capsys):
    modulo, flag, n_l1b, n_geo, presente, ausente, clave = CASOS[plataforma]
    monkeypatch.setattr(modulo, flag, True)
    l1b = _l1b(tmp_path / n_l1b, [presente])
    geo = tmp_path / n_geo
    geo.write_bytes(b"no se lee")
    monkeypatch.setattr(rp, "TMP_DIR", tmp_path / "tmp")
    monkeypatch.setattr(rp.fetch, "fetch_for_volcano", lambda *a, **k: {plataforma: [l1b, geo]})
    monkeypatch.setattr(rp.store, "append_record", lambda *a, **k: None)
    for f in ("SENSOR_VIIRS_375", "SENSOR_VIIRS_750"):
        monkeypatch.setattr(rp.vrp_profile, f, True, raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    rp.fetch.limpiar_fallas()
    try:
        rp.process_date(LASCAR, FECHA, nighttime_only=False)
        log = capsys.readouterr().out
        incid = rp.fetch.incidencias_de_cobertura()
        cod = rp.informar_cobertura(rp.fetch.fallas_de_cobertura(), estricto=True, incidencias=incid)
        capsys.readouterr()
    finally:
        rp.fetch.limpiar_fallas()
    tipos = [i["tipo"] for i in incid]
    assert tipos == ["error_procesamiento"], tipos
    assert cod == 3, cod
    assert ausente in incid[0].get("motivo", ""), incid[0]
    por = rev.clasificar_por_sensor(log)
    assert len(por[clave]) == 1, (por, log)
    archivo_log = tmp_path / "nrt.log"
    archivo_log.write_text(log, encoding="utf-8")
    assert rev.main(["--log", str(archivo_log), "--volcan", "Lascar"]) == 1


def test_control_dos_bandas_presentes_no_informa_ausencia(tmp_path):
    for _, _, n_l1b, _, presente, ausente, _ in CASOS.values():
        l1b = _l1b(tmp_path / n_l1b, [presente, ausente])
        assert MV.bandas_ausentes_l1b(l1b, (presente, ausente)) == []
        assert MV.leer_radiancia_l1b(l1b, bandas=(presente, ausente)) is not None


def test_lector_conserva_interfaz_none(tmp_path):
    l1b = _l1b(tmp_path / "VJ102MOD.A2026314.0554.021.nc", ["M13"])
    assert MV.leer_radiancia_l1b(l1b) is None
    assert MV.bandas_ausentes_l1b(l1b, ("M13", "M15")) == ["M15"]


def test_control_revisor_clasifica_los_dos_sensores():
    log = ("  ERROR processing VJ102IMG.A2026314.0554.021.nc: control\n"
           "  ERROR processing VJ102MOD.A2026314.0554.021.nc: control\n")
    por = rev.clasificar_por_sensor(log)
    assert len(por["VIIRS375"]) == len(por["VIIRS750"]) == 1
