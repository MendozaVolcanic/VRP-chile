# -*- coding: utf-8 -*-
"""S198 (auditoría de Codex, ronda 2, F6-114, opción (a) aprobada por Nicolás el 2026-11-24): barrido semanal de huecos.

POR QUÉ, COMO GEÓLOGO. Una pasada del satélite que no se pudo buscar ni bajar no deja record, y en el tablero esa noche
se lee como «sin anomalía». El NRT vuelve a buscar cada día durante 8 días (hoy y los 7 anteriores); pasado eso ningún
workflow vuelve a mirar ese día, así que una caída de NASA o de la red que dure lo suficiente se vuelve pérdida
permanente. El barrido semanal recorre los días 9 a 30 hacia atrás de los 11 volcanes del NRT y procesa SÓLO las
pasadas que no tienen record: no reprocesa lo que ya existe (nada de `--overwrite`) y no baja lo que ya está.

QUÉ EXIGE.
(1) `pipeline/fetch.py`: con la lista de pasadas existentes configurada, un gránulo cuya pasada (plataforma y minuto,
    la misma clave con que `store.py` deduplica) ya tiene record no se baja; los demás sí. Sin configurar, nada cambia
    (el NRT). Un gránulo cuyo minuto no se puede leer se baja igual (ante la duda, procesar).
(2) `scripts/run_pipeline.py --solo-sin-record`: arma esa lista con los records del volcán y la entrega a fetch antes
    de sus días; no se combina con `--overwrite`.
(3) `.github/workflows/barrido-huecos.yml`: semanal, los 11 del NRT, perfil `mirova_equivalent`, días 9 a 30, sólo
    token (A71), sin `--overwrite`, `git add` sólo del JSON del volcán y su propio grupo de concurrencia con el bucle
    de reintento del NRT (no `push-main`: así el NRT nunca espera detrás del barrido).

LAS DOS PREGUNTAS DEL INSTRUMENTO. ¿Puede dar rojo? Sí: antes del cambio (1) y (2) caen por AttributeError y (3) porque
el workflow no existe. Control: sin lista configurada se bajan todas las pasadas.
"""
from __future__ import annotations

import re
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import pipeline.fetch as fetch  # noqa: E402

WF = ROOT / ".github" / "workflows" / "barrido-huecos.yml"
NRT = ROOT / ".github" / "workflows" / "nrt.yml"

FECHA = datetime(2026, 11, 3)
AHORA = datetime(2026, 11, 24)
VOLCAN = {"name": "Lascar", "lat": -23.37, "lon": -67.73, "radius_km": 25, "sensors": ["MODIS"]}


def _granulo(producto: str, hhmm: str, ur: str | None = None) -> dict:
    inicio = f"2026-11-03T{hhmm[:2]}:{hhmm[2:]}:00.000Z"
    return {"umm": {"GranuleUR": ur or f"{producto}.A2026307.{hhmm}.061.2026307120000.hdf",
                    "TemporalExtent": {"RangeDateTime": {"BeginningDateTime": inicio}}}}


class Descarga:
    """Imita earthaccess.download y anota qué gránulos se pidieron."""

    def __init__(self):
        self.pedidos = []

    def __call__(self, granulos, local_path):
        rutas = []
        for g in granulos:
            self.pedidos.append(g["umm"]["GranuleUR"])
            p = Path(local_path) / (g["umm"]["GranuleUR"] + ".x")
            p.write_bytes(b"FALSO")
            rutas.append(str(p))
        return rutas


@pytest.fixture(autouse=True)
def _aislado(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr(fetch, "auth", lambda: None)
    fetch.limpiar_fallas()
    yield
    fetch.limpiar_fallas()
    if hasattr(fetch, "configurar_pasadas_existentes"):
        fetch.configurar_pasadas_existentes(None)


def _buscar(por_clave):
    return lambda clave, lat, lon, radius, date: list(por_clave.get(clave, []))


def _dos_pasadas(monkeypatch, ur_raro=False):
    a = [_granulo("MOD021KM", "0300"), _granulo("MOD03", "0300")]
    b = [_granulo("MOD021KM", "0440", ur="LAADS:9999" if ur_raro else None), _granulo("MOD03", "0440")]
    monkeypatch.setattr(fetch, "search_granules", _buscar({
        "MODIS_TERRA_L1B": [a[0], b[0]], "MODIS_TERRA_GEO": [a[1], b[1]]}))
    descarga = Descarga()
    monkeypatch.setattr(fetch.earthaccess, "download", descarga)
    return a, b, descarga


def _fetch(tmp_path):
    return fetch.fetch_for_volcano(VOLCAN, FECHA, tmp_path, nighttime_only=False, ahora=AHORA)


# ── (1) fetch ────────────────────────────────────────────────────────────────────────────────────

def test_control_sin_lista_se_bajan_todas_las_pasadas(monkeypatch, tmp_path):
    a, b, descarga = _dos_pasadas(monkeypatch)
    _fetch(tmp_path)
    assert sorted(descarga.pedidos) == sorted(g["umm"]["GranuleUR"] for g in a + b)


def test_pasada_con_record_no_se_baja(monkeypatch, tmp_path):
    a, b, descarga = _dos_pasadas(monkeypatch)
    fetch.configurar_pasadas_existentes({("MODIS_TERRA", "2026-11-03 03:00")})
    res = _fetch(tmp_path)
    assert sorted(descarga.pedidos) == sorted(g["umm"]["GranuleUR"] for g in b)
    assert len(res["MODIS_TERRA"]) == 2


def test_la_clave_es_por_plataforma(monkeypatch, tmp_path):
    """El mismo minuto en otra plataforma (Aqua) no tapa la pasada de Terra."""
    a, b, descarga = _dos_pasadas(monkeypatch)
    fetch.configurar_pasadas_existentes({("MODIS_AQUA", "2026-11-03 03:00")})
    _fetch(tmp_path)
    assert len(descarga.pedidos) == 4


def test_todas_con_record_no_baja_nada_ni_busca_geolocalizacion(monkeypatch, tmp_path):
    a, b, descarga = _dos_pasadas(monkeypatch)
    buscadas = []
    buscar = fetch.search_granules
    monkeypatch.setattr(fetch, "search_granules", lambda c, *x: buscadas.append(c) or buscar(c, *x))
    fetch.configurar_pasadas_existentes({("MODIS_TERRA", "2026-11-03 03:00"), ("MODIS_TERRA", "2026-11-03 04:40")})
    res = _fetch(tmp_path)
    assert descarga.pedidos == [] and "MODIS_TERRA" not in res
    assert "MODIS_TERRA_GEO" not in buscadas
    assert fetch.fallas_de_cobertura() == []


def test_minuto_desde_el_inicio_si_el_nombre_no_lo_trae(monkeypatch, tmp_path):
    a, b, descarga = _dos_pasadas(monkeypatch, ur_raro=True)
    fetch.configurar_pasadas_existentes({("MODIS_TERRA", "2026-11-03 04:40")})
    _fetch(tmp_path)
    assert "LAADS:9999" not in descarga.pedidos and len(descarga.pedidos) == 2


def test_granulo_sin_minuto_legible_se_baja_igual():
    g = {"umm": {"GranuleUR": "LAADS:1"}}
    fetch.configurar_pasadas_existentes({("MODIS_TERRA", "2026-11-03 03:00")})
    assert fetch._quitar_pasadas_existentes("MODIS_TERRA", [g]) == [g]


def test_el_minuto_del_granulo_es_el_del_record():
    """La clave del record sale del nombre del archivo (A<año><día>.<hhmm>), igual que aquí."""
    g = _granulo("VJ102MOD", "0606", ur="VJ102MOD_NRT.A2026328.0606.021.2026328083015.nc")
    assert fetch._minuto_granulo(g) == "2026-11-24 06:06"


# ── (2) run_pipeline ─────────────────────────────────────────────────────────────────────────────

def test_claves_con_record_usa_sensor_y_minuto():
    import scripts.run_pipeline as rp
    recs = [{"sensor": "MODIS_TERRA", "datetime_utc": "2026-11-03 03:00"},
            {"sensor": "VIIRS_NOAA20_750", "datetime_utc": "2026-11-03 06:06", "vrp_mw": 0},
            {"sensor": None, "datetime_utc": "2026-11-03 07:00"}]
    assert rp.claves_con_record(recs) == {("MODIS_TERRA", "2026-11-03 03:00"),
                                          ("VIIRS_NOAA20_750", "2026-11-03 06:06")}


def _main(monkeypatch, argv):
    import scripts.run_pipeline as rp
    vistos = []
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py"] + argv)
    monkeypatch.setattr(rp.store, "get_records",
                        lambda nombre, last_n=None: [{"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-01 06:40"}])
    monkeypatch.setattr(rp, "process_date", lambda *a, **k: vistos.append(fetch._PASADAS_EXISTENTES))
    monkeypatch.setattr(rp.fetch, "configurar_ventana", lambda *a, **k: False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    with pytest.raises(SystemExit) as e:
        rp.main()
    return e.value.code, vistos


def test_solo_sin_record_entrega_las_pasadas_del_volcan_a_fetch(monkeypatch):
    codigo, vistos = _main(monkeypatch, ["--volcano", "Lascar", "--start", "2026-11-01", "--end", "2026-11-02",
                                         "--solo-sin-record"])
    assert codigo == 0
    assert vistos == [{("MODIS_AQUA", "2026-11-01 06:40")}] * 2


def test_control_sin_la_bandera_fetch_no_filtra(monkeypatch):
    codigo, vistos = _main(monkeypatch, ["--volcano", "Lascar", "--date", "2026-11-01"])
    assert vistos == [None]


def test_solo_sin_record_no_se_combina_con_overwrite(monkeypatch):
    codigo, _ = _main(monkeypatch, ["--volcano", "Lascar", "--date", "2026-11-01", "--solo-sin-record",
                                    "--overwrite"])
    assert codigo == 2


# ── (3) workflow ─────────────────────────────────────────────────────────────────────────────────

def _wf():
    txt = WF.read_text(encoding="utf-8")
    return txt, yaml.safe_load(txt)


def _paso_pipeline(d):
    return next(s for s in d["jobs"]["process"]["steps"] if "run_pipeline.py" in s.get("run", ""))


def test_workflow_semanal_con_on_entre_comillas():
    txt, d = _wf()
    assert "on" in d and True not in d, "'on' entre comillas (A43)"
    assert set(d["on"]) == {"schedule", "workflow_dispatch"}
    [cron] = [c["cron"] for c in d["on"]["schedule"]]
    minuto, hora, dia_mes, mes, dia_semana = cron.split()
    assert dia_mes == "*" and mes == "*" and dia_semana.isdigit(), "una vez por semana"
    assert minuto not in ("0", "30", "12", "20", "50"), "minutos de nrt, nrt-retry, sync, watchdog y pages"


def test_workflow_cubre_los_11_del_nrt():
    _, d = _wf()
    nrt = yaml.safe_load(NRT.read_text(encoding="utf-8"))
    assert sorted(d["jobs"]["process"]["strategy"]["matrix"]["volcano"]) == \
        sorted(nrt["jobs"]["process"]["strategy"]["matrix"]["volcano"])
    assert len(d["jobs"]["process"]["strategy"]["matrix"]["volcano"]) == 11


def test_workflow_procesa_dias_9_a_30_solo_sin_record_y_sin_overwrite():
    txt, d = _wf()
    run = _paso_pipeline(d)["run"]
    assert "--profile mirova_equivalent" in run and "--solo-sin-record" in run
    assert "--overwrite" not in txt
    assert re.search(r"date -u -d ['\"]30 days ago['\"]", run) and re.search(r"date -u -d ['\"]9 days ago['\"]", run)
    assert "--start" in run and "--end" in run and "set -o pipefail" in run


def test_workflow_solo_token_y_corta_si_falta():
    txt, d = _wf()
    paso = _paso_pipeline(d)
    run = paso["run"]
    assert paso["env"]["EARTHDATA_TOKEN"] == "${{ secrets.EARTHDATA_TOKEN }}"
    assert '-z "$EARTHDATA_TOKEN"' in run and run.index('-z "$EARTHDATA_TOKEN"') < run.index("run_pipeline.py")
    assert "EARTHDATA_USERNAME" not in txt and "EARTHDATA_PASSWORD" not in txt


def test_workflow_parte_de_la_punta_de_la_rama():
    _, d = _wf()
    chk = [s for s in d["jobs"]["process"]["steps"] if str(s.get("uses", "")).startswith("actions/checkout@")]
    assert len(chk) == 1 and chk[0]["with"]["ref"] == "${{ github.ref }}"


def test_workflow_commitea_solo_el_json_del_volcan_con_grupo_propio_y_reintento():
    txt, d = _wf()
    commit = next(s for s in d["jobs"]["process"]["steps"] if "git push" in s.get("run", ""))
    assert re.findall(r'git add "([^"]+)"', commit["run"]) == ["data/mirova_equivalent/${{ matrix.volcano }}.json"]
    assert "for attempt in 1 2 3 4 5" in commit["run"] and "pull --rebase" in commit["run"]
    grupo = d["concurrency"]["group"]
    assert grupo != "push-main" and d["concurrency"]["cancel-in-progress"] is False
    otros = {(yaml.safe_load(p.read_text(encoding="utf-8")).get("concurrency") or {}).get("group")
             for p in (ROOT / ".github" / "workflows").glob("*.yml") if p != WF}
    assert grupo not in otros
    assert d["jobs"]["process"]["strategy"]["fail-fast"] is False
