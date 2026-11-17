# -*- coding: utf-8 -*-
"""S190 (H07 y H08 de la auditoría de Codex, verificados en D:\\vrp-trabajo\\temporales\\s190_codex\\verif\\V4\\):
«Cobertura: completa» no puede decirse de una corrida en la que un gránulo bajado no se procesó.

POR QUÉ, COMO GEÓLOGO. Una pasada que el satélite hizo, que NASA entregó y que se bajó, pero que el procesador no pudo
leer (archivo truncado, banda ausente, una excepción de la vía), no es una noche tranquila: es una noche sin dato. Hasta
S190 `scripts/run_pipeline.py` atrapaba la excepción, imprimía `ERROR processing` y el resumen de cobertura decía
«completa» con salida 0, también con `--estricto-cobertura`, que es el modo con que los reprocesos reemplazan la
historia publicada. Lo mismo con un `None` del procesador: la pasada desaparecía sin rastro en la cobertura. Sólo
`nrt.yml` corría el revisor de errores del log; `sombra-34.yml` (los 34 que el tablero muestra desde la ficha v1.26),
`reproc-historia-via.yml` y `reproc-retro-paquete.yml` no.

QUÉ EXIGE. (1) Excepción del procesador: incidencia `error_procesamiento`, que cuenta en modo estricto (salida 3) y
deja la línea `ERROR processing` que leen los revisores. (2) `None` del procesador: incidencia `sin_record`, sin juicio
(el descarte de borde de la vía y el volcán fuera del gránulo son legítimos y frecuentes): no cuenta en modo estricto,
pero el resumen deja de decir «completa». (3) Sin modo estricto la salida sigue en 0 (el NRT no cambia de color).
(4) Los tres workflows corren el revisor como ÚLTIMO paso del job, para que no frene ningún paso anterior.
(5) El perfil sombra_34 no dice que el tablero no lo lee.

LAS DOS PREGUNTAS DEL INSTRUMENTO. ¿Puede dar rojo? Sí: sin el arreglo, (1), (2) y (4) fallan por aserción (rojo
guardado en la descripción del PR). Controles: una corrida con record sigue «completa» y en 0; si el procesador ya
registró su propia incidencia (cráter sin posición) no se agrega `sin_record`.
"""
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.run_pipeline as rp  # noqa: E402

VOLCAN = {"name": "Mentolat", "display_name": "Mentolat", "lat": -44.70, "lon": -73.08, "radius_km": 5,
          "inner_radius_km": 5}
FECHA = datetime(2026, 11, 16)

# plataforma -> (módulo procesador, L1B, GEO)
SENSORES = {
    "MODIS_AQUA": ("process_modis", "MYD021KM.A2026320.0710.061.2026320191510.hdf",
                   "MYD03.A2026320.0710.061.2026320185000.hdf"),
    "VIIRS_NOAA20": ("process_viirs", "VJ102IMG.A2026320.0500.021.2026320090000.nc",
                     "VJ103IMG.A2026320.0500.021.2026320090000.nc"),
    "VIIRS_NOAA20_750": ("process_viirs_mod", "VJ102MOD.A2026320.0500.021.2026320090000.nc",
                         "VJ103MOD.A2026320.0500.021.2026320090000.nc"),
}
RECORD = {"sensor": "X", "vrp_mw": 0.0, "t_bg_k": 263.0, "t_max_k": 270.0, "n_anomalous_pixels": 0}


@pytest.fixture
def correr(monkeypatch, tmp_path, capsys):
    """Corre process_date con un solo gránulo de `plataforma` y el procesador `calcular`; devuelve
    (log, incidencias, código estricto, resumen estricto, código no estricto)."""
    def _correr(plataforma, calcular):
        modulo, l1b, geo = SENSORES[plataforma]
        d = tmp_path / "g"
        d.mkdir(exist_ok=True)
        for n in (l1b, geo):
            (d / n).write_bytes(b"")
        monkeypatch.setattr(rp, "TMP_DIR", tmp_path / "tmp")
        monkeypatch.setattr(rp.fetch, "fetch_for_volcano", lambda *a, **k: {plataforma: [d / l1b, d / geo]})
        monkeypatch.setattr(getattr(rp, modulo), "calculate_vrp", calcular)
        monkeypatch.setattr(rp.store, "append_record", lambda *a, **k: None)
        for flag in ("SENSOR_MODIS", "SENSOR_VIIRS_375", "SENSOR_VIIRS_750"):
            monkeypatch.setattr(rp.vrp_profile, flag, True, raising=False)
        monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
        rp.fetch.limpiar_fallas()
        rp.process_date(VOLCAN, FECHA, nighttime_only=False)
        log = capsys.readouterr().out
        incid = rp.fetch.incidencias_de_cobertura()
        cod_e = rp.informar_cobertura(rp.fetch.fallas_de_cobertura(), estricto=True, incidencias=incid)
        resumen_e = capsys.readouterr().out
        cod_n = rp.informar_cobertura(rp.fetch.fallas_de_cobertura(), estricto=False, incidencias=incid)
        capsys.readouterr()
        rp.fetch.limpiar_fallas()
        return log, incid, cod_e, resumen_e, cod_n
    return _correr


def _explota(*a, **k):
    raise RuntimeError("Unable to open file (truncated file)")


@pytest.mark.parametrize("plataforma", sorted(SENSORES))
def test_excepcion_del_procesador_cuenta_en_modo_estricto(correr, plataforma):
    log, incid, cod_e, resumen_e, cod_n = correr(plataforma, _explota)
    tipos = [i["tipo"] for i in incid]
    assert tipos == ["error_procesamiento"], incid
    assert incid[0]["cuenta_estricto"] is True and incid[0]["plataforma"] == plataforma, incid
    assert SENSORES[plataforma][1] in incid[0]["motivo"], incid
    assert cod_e == 3, resumen_e
    assert "Cobertura: completa" not in resumen_e, resumen_e
    assert cod_n == 0                     # el NRT no usa el modo estricto: no cambia de color
    # los revisores (revisar_errores_modis_nrt.py, revisar_sombra.py) leen esta línea: no puede cambiar
    assert f"ERROR processing {SENSORES[plataforma][1]}: Unable to open file" in log, log


@pytest.mark.parametrize("plataforma", sorted(SENSORES))
def test_none_del_procesador_queda_como_incidencia_sin_juicio(correr, plataforma):
    log, incid, cod_e, resumen_e, cod_n = correr(plataforma, lambda *a, **k: None)
    assert [i["tipo"] for i in incid] == ["sin_record"], incid
    assert incid[0]["cuenta_estricto"] is False, incid
    assert SENSORES[plataforma][1] in incid[0]["motivo"], incid
    assert "Cobertura: completa" not in resumen_e and "NO COMPLETA" in resumen_e, resumen_e
    assert cod_e == 0 and cod_n == 0, resumen_e


@pytest.mark.parametrize("plataforma", sorted(SENSORES))
def test_control_con_record_sigue_completa(correr, plataforma):
    log, incid, cod_e, resumen_e, cod_n = correr(plataforma, lambda *a, **k: dict(RECORD))
    assert incid == [], incid
    assert cod_e == 0 and "Cobertura: completa" in resumen_e, resumen_e


def test_control_si_el_procesador_ya_registro_su_incidencia_no_se_agrega_sin_record(correr):
    def calcular(*a, al_sin_dato=None, **k):
        al_sin_dato("cráter sin posición en el gránulo")
        return None
    log, incid, cod_e, resumen_e, cod_n = correr("MODIS_AQUA", calcular)
    assert [i["tipo"] for i in incid] == ["crater_sin_dato"], incid


def test_los_tipos_nuevos_tienen_titulo_en_el_resumen():
    for tipo in ("error_procesamiento", "sin_record"):
        assert tipo in rp.fetch.TIPOS_INCIDENCIA, tipo
    assert rp.fetch.TIPOS_INCIDENCIA["error_procesamiento"] is True
    assert rp.fetch.TIPOS_INCIDENCIA["sin_record"] is False


# ---------------------------------------------------------------------------------------------- workflows
WORKFLOWS = {
    "sombra-34.yml": "process",
    "reproc-historia-via.yml": "reproc",
    "reproc-retro-paquete.yml": "reproc",
}
_REVISOR = re.compile(r"python scripts/revisar_errores_modis_nrt\.py --log pipeline\.log\b")


@pytest.mark.parametrize("nombre,job", sorted(WORKFLOWS.items()))
def test_el_revisor_de_errores_corre_como_ultimo_paso(nombre, job):
    """Último paso: así un rojo del revisor no salta ningún paso anterior (la subida del trozo en los reprocesos, el
    commit en sombra-34); sólo hace visible el hueco en el color del job."""
    texto = (ROOT / ".github" / "workflows" / nombre).read_text(encoding="utf-8")
    assert re.search(r'^"on":', texto, re.M), "Norway Problem (A43): «on» entre comillas"
    d = yaml.safe_load(texto)
    pasos = d["jobs"][job]["steps"]
    con_revisor = [i for i, p in enumerate(pasos) if _REVISOR.search(p.get("run") or "")]
    assert con_revisor == [len(pasos) - 1], (nombre, [p.get("name") for p in pasos])
    cond = str(pasos[-1].get("if") or "")
    assert "!cancelled()" in cond or "always()" in cond, cond     # corre también si el paso de la corrida falló


def test_nrt_sigue_con_su_revisor():
    texto = (ROOT / ".github" / "workflows" / "nrt.yml").read_text(encoding="utf-8")
    assert _REVISOR.search(texto)


# ---------------------------------------------------------------------------------------------- H08
def test_sombra_34_no_dice_que_el_tablero_no_lo_lee():
    perfil = (ROOT / "pipeline" / "profiles" / "sombra_34.yaml").read_text(encoding="utf-8")
    index = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert "data/sombra_34/" in index           # premisa: el tablero sí lo lee
    plano = " ".join(perfil.split()).lower()
    # A113: el texto viejo se conserva citado tras «texto anterior:»; esa cita no cuenta como afirmación vigente
    plano = re.sub(r"texto anterior: «.*?»", "", plano)
    for falso in ("nada lo lee el tablero", "no publica", "sin publicar nada", "no operacional"):
        assert falso not in plano, falso
    assert "tablero" in plano and "publica" in plano
