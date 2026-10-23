"""S159, tarea I1: lo que la cobertura no veía (AUDIT_S158_R2, R2-9 y VB-1).

POR QUE. Hasta S158 el resumen de cobertura de run_pipeline sólo contaba búsquedas y descargas que FALLARON. Tres
situaciones salían como «Cobertura: completa» sin serlo:
  (a) la búsqueda responde con cero gránulos: puede ser normal (la plataforma no pasó) o un catálogo vacío, como el
      18-oct, cuando CMR devolvía cero gránulos de todo el día (R2-13). El código no tiene un modelo de órbita para
      saber cuál es, así que se registra «sin gránulos, sin juicio» y NO cuenta como falla, ni con el modo estricto;
  (b) un L1B llega sin su geolocalización (el 20-oct CMR tenía 72 MOD021KM NRT contra 68 MOD03, VB-1): se
      descartaba en silencio. Eso sí es pérdida segura: con --estricto-cobertura el job sale con 3;
  (c) el día no había terminado (más la latencia mínima de LANCE) cuando se buscó: el NRT procesa el día en curso
      siempre, y ese día es parcial por construcción. Con --estricto-cobertura sale con 3 (un reproceso que incluye un
      día sin terminar deja un tramo que después cambia, A108).
El NRT no usa --estricto-cobertura: en los tres casos su código de salida sigue en 0 (el cron no cambia de color).

Las pruebas corren el main() real de run_pipeline con process_date real; sólo la red está reemplazada.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
_spec = importlib.util.spec_from_file_location("run_pipeline_s159", RAIZ / "scripts" / "run_pipeline.py")
rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rp)
fetch = rp.fetch

PASADO = "2026-10-18"


def _red_prohibida(*a, **k):
    raise AssertionError("una prueba no puede tocar NASA (ni auth con el netrc local, A71)")


def _gran(t):
    return {"umm": {"TemporalExtent": {"RangeDateTime": {"BeginningDateTime": t, "EndingDateTime": t}},
                    "GranuleUR": "falso_" + t}}


def _es_geo(short_name):
    return "03" in short_name      # MOD03, MYD03, VNP03IMG, VJ103MOD...; ningún L1B tiene «03» en el nombre


def _buscador(dia, sin_geo=False, vacio=False):
    def buscar(**kw):
        if vacio:
            return []
        if _es_geo(kw.get("short_name", "")) and sin_geo:
            return []
        return [_gran(dia + "T05:35:00Z")]
    return buscar


@pytest.fixture(autouse=True)
def _limpio(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch, "auth", lambda: None)
    monkeypatch.setattr(fetch.earthaccess, "login", _red_prohibida)
    monkeypatch.setattr(fetch.earthaccess, "search_data", _red_prohibida)
    monkeypatch.setattr(fetch.earthaccess, "download", _red_prohibida)
    monkeypatch.setattr(fetch, "_diag", lambda *a, **k: None)
    # el caso es de catálogo, no de sol: el filtro nocturno deja pasar todo
    monkeypatch.setattr(fetch, "_filter_nighttime_granules", lambda g, lat, lon, **k: g)
    # «descarga» sin red: rutas que no existen (process_date las filtra y no procesa nada)
    monkeypatch.setattr(fetch, "download_granules", lambda gs, d: [Path(d) / ("falso_%d" % i) for i in range(len(gs))])
    monkeypatch.setattr(rp, "TMP_DIR", tmp_path / "tmp")
    monkeypatch.setenv("VRP_BUSQUEDA_VENTANA", "0")
    for v in ("VRP_VENTANA_BUSQUEDA", "VRP_CACHE_BUSQUEDA_DIR", "VRP_CONSERVAR_GRANULOS",
              "GITHUB_STEP_SUMMARY", "GITHUB_ACTIONS"):
        monkeypatch.delenv(v, raising=False)
    fetch.reiniciar_ventana()
    fetch.limpiar_fallas()
    yield
    fetch.reiniciar_ventana()
    fetch.limpiar_fallas()


def _correr(monkeypatch, capsys, tmp_path, fecha, buscador, estricto):
    monkeypatch.setattr(fetch.earthaccess, "search_data", buscador)
    ruta = tmp_path / "cob.json"
    argv = ["run_pipeline.py", "--volcano", "Lascar", "--date", fecha, "--cobertura-json", str(ruta)]
    if estricto:
        argv.append("--estricto-cobertura")
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as e:
        rp.main()
    out = capsys.readouterr().out
    return (e.value.code or 0), out, json.loads(ruta.read_text(encoding="utf-8"))


def _tipos(cob):
    return {i.get("tipo") for i in cob.get("incidencias", [])}


def _hoy():
    return datetime.utcnow().strftime("%Y-%m-%d")


# ---------------------------------------------------------------- control: un día limpio sigue diciendo «completa»

@pytest.mark.parametrize("estricto", [False, True])
def test_control_dia_pasado_con_granulos_y_geolocalizacion_es_completa(monkeypatch, capsys, tmp_path, estricto):
    cod, out, cob = _correr(monkeypatch, capsys, tmp_path, PASADO, _buscador(PASADO), estricto)
    assert "Cobertura: completa" in out, out[-1500:]
    assert cod == 0
    assert cob["fallas"] == [] and cob.get("incidencias", []) == []


# ---------------------------------------------------------------- (a) cero gránulos

@pytest.mark.parametrize("estricto", [False, True])
def test_cero_granulos_no_es_completa_y_no_es_falla(monkeypatch, capsys, tmp_path, estricto):
    cod, out, cob = _correr(monkeypatch, capsys, tmp_path, PASADO, _buscador(PASADO, vacio=True), estricto)
    assert "Cobertura: completa" not in out, "cero gránulos se informó como cobertura completa (R2-9)"
    assert "sin juicio" in out
    assert _tipos(cob) == {"sin_granulos"}
    assert cob["fallas"] == []          # no es una búsqueda fallida
    assert cod == 0                     # ni con --estricto-cobertura: el código no sabe si debía haber gránulos
    plataformas = {i["plataforma"] for i in cob["incidencias"]}
    assert "MODIS_TERRA" in plataformas and "VIIRS_SNPP" in plataformas
    assert all(i["volcan"] == "Lascar" and i["fecha"] == PASADO for i in cob["incidencias"])


def test_cero_granulos_por_la_ventana_tambien_queda_registrado(monkeypatch, capsys, tmp_path):
    """El camino por ventana (S157) devuelve [] para un día sin gránulos sin pasar por search_granules por día."""
    monkeypatch.setenv("VRP_BUSQUEDA_VENTANA", "1")
    monkeypatch.setenv("VRP_VENTANA_BUSQUEDA", "2026-10-16:2026-10-18")
    cod, out, cob = _correr(monkeypatch, capsys, tmp_path, PASADO, _buscador(PASADO, vacio=True), False)
    assert "Cobertura: completa" not in out
    assert _tipos(cob) == {"sin_granulos"}


def test_una_busqueda_caida_no_se_cuenta_ademas_como_sin_granulos(monkeypatch, capsys, tmp_path):
    """Si la búsqueda falló, ya es falla: no se duplica como «sin gránulos» (distingue «no devolvió» de «no pudo»)."""
    from requests.exceptions import ReadTimeout

    def caido(**kw):
        raise ReadTimeout("simulado")
    monkeypatch.setattr(fetch, "ENABLE_CMR_SEARCH_BREAKER", True)
    cod, out, cob = _correr(monkeypatch, capsys, tmp_path, PASADO, caido, True)
    assert cod == 3 and cob["fallas"]
    assert "sin_granulos" not in _tipos(cob)


# ---------------------------------------------------------------- (b) L1B sin geolocalización

@pytest.mark.parametrize("estricto,codigo", [(False, 0), (True, 3)])
def test_l1b_sin_geolocalizacion_queda_registrado(monkeypatch, capsys, tmp_path, estricto, codigo):
    cod, out, cob = _correr(monkeypatch, capsys, tmp_path, PASADO, _buscador(PASADO, sin_geo=True), estricto)
    assert "Cobertura: completa" not in out, "un L1B sin geolocalización se descartó en silencio (VB-1)"
    assert "sin_geolocalizacion" in _tipos(cob)
    assert cod == codigo                # el NRT (sin estricto) no cambia de código de salida


def test_geolocalizacion_que_no_llega_al_disco_queda_registrada(monkeypatch, capsys, tmp_path):
    """El par se encontró, pero sólo el L1B quedó en disco: process_date lo descartaba con un print."""
    def baja_solo_l1b(gs, d):
        d.mkdir(parents=True, exist_ok=True)
        p = d / "MOD021KM.A2026291.0535.061.nrt.hdf"
        p.write_bytes(b"x")
        return [p]
    monkeypatch.setattr(fetch, "download_granules", baja_solo_l1b)
    cod, out, cob = _correr(monkeypatch, capsys, tmp_path, PASADO, _buscador(PASADO), True)
    assert "Cobertura: completa" not in out
    assert "sin_geolocalizacion" in _tipos(cob)
    assert cod == 3


# ---------------------------------------------------------------- (c) día parcial

@pytest.mark.parametrize("estricto,codigo", [(False, 0), (True, 3)])
def test_dia_en_curso_es_parcial(monkeypatch, capsys, tmp_path, estricto, codigo):
    hoy = _hoy()
    cod, out, cob = _correr(monkeypatch, capsys, tmp_path, hoy, _buscador(hoy), estricto)
    assert "Cobertura: completa" not in out, "el día en curso se informó como cobertura completa (R2-9)"
    assert "dia_parcial" in _tipos(cob)
    assert cod == codigo
    parciales = [i for i in cob["incidencias"] if i["tipo"] == "dia_parcial"]
    assert len(parciales) == 1          # una por volcán y día, no una por plataforma


def test_dia_parcial_depende_del_reloj_no_de_la_fecha_pedida():
    """Unidad: el día 2026-10-18 es parcial a las 02:00 del 19 (dentro de la latencia mínima) y no a las 04:00."""
    d = datetime(2026, 10, 18)
    assert fetch.dia_incompleto(d, ahora=datetime(2026, 10, 18, 23, 0))
    assert fetch.dia_incompleto(d, ahora=datetime(2026, 10, 19, 2, 0))
    assert not fetch.dia_incompleto(d, ahora=datetime(2026, 10, 19, 4, 0))
    assert not fetch.dia_incompleto(datetime(2026, 10, 18, 14, 32), ahora=datetime(2026, 10, 20))


# ---------------------------------------------------------------- el JSON que lee reproc_brazos

def test_reproc_brazos_cuenta_lo_que_el_estricto_cuenta(tmp_path):
    _spec2 = importlib.util.spec_from_file_location("reproc_brazos_s159", RAIZ / "scripts" / "reproc_brazos.py")
    rb = importlib.util.module_from_spec(_spec2)
    _spec2.loader.exec_module(rb)

    def ejecutar(cmd, env=None, stdout=None, stderr=None):
        cob = Path(cmd[cmd.index("--cobertura-json") + 1])
        cob.parent.mkdir(parents=True, exist_ok=True)
        cob.write_text(json.dumps({"fallas": [], "n": 0, "incidencias": [
            {"tipo": "sin_geolocalizacion", "cuenta_estricto": True, "volcan": "Lascar", "fecha": "2026-09-01"},
            {"tipo": "sin_granulos", "cuenta_estricto": False, "volcan": "Lascar", "fecha": "2026-09-01"}]}),
            encoding="utf-8")

        class R:
            returncode = 0
        return R()
    salida = tmp_path / "c.json"
    assert rb.correr("Lascar", "2026-09-01", "2026-09-01", ["p"], tmp_path, estricto=True,
                     cobertura_json=salida, ejecutar=ejecutar) == 3
    assert rb.correr("Lascar", "2026-09-01", "2026-09-01", ["p"], tmp_path, estricto=False,
                     cobertura_json=salida, ejecutar=ejecutar) == 0
    assert len(json.loads(salida.read_text(encoding="utf-8"))["incidencias"]) == 2
