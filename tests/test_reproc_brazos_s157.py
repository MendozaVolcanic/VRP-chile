"""S157: cobertura en run_pipeline y brazos de un A/B en el mismo job (scripts/reproc_brazos.py).

POR QUE. (1) Un dia que no se pudo buscar salia verde: run_pipeline tiene que decirlo, escribirlo y, en modo
estricto (reprocesos), salir distinto de cero. El NRT no usa el modo estricto. (2) En un A/B cada brazo volvia a
buscar y a bajar los mismos granulos. El driver corre los brazos en serie, dia por fuera y brazo por dentro, con la
misma cache de busquedas y el mismo directorio de granulos, y borra cada dia cuando lo usaron todos los brazos (un
dia ocupa ~1,3 GB; la ventana entera no cabe en el runner).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
_spec = importlib.util.spec_from_file_location("run_pipeline_s157", RAIZ / "scripts" / "run_pipeline.py")
rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rp)
fetch = rp.fetch

_spec2 = importlib.util.spec_from_file_location("reproc_brazos_s157", RAIZ / "scripts" / "reproc_brazos.py")
rb = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(rb)

FALLA = {"volcan": "Lascar", "fecha": "2026-09-02", "plataforma": "VIIRS_SNPP", "producto": "VIIRS_SNPP_GEO",
         "etapa": "busqueda", "motivo": "RuntimeError: HTTP 500"}


def _red_prohibida(*a, **k):
    raise AssertionError("una prueba no puede tocar NASA (ni auth con el netrc local, A71)")


@pytest.fixture(autouse=True)
def _limpio(monkeypatch):
    # Candado: ninguna prueba de este archivo llega a la red ni a la credencial local.
    monkeypatch.setattr(fetch, "auth", _red_prohibida)
    monkeypatch.setattr(fetch.earthaccess, "login", _red_prohibida)
    monkeypatch.setattr(fetch.earthaccess, "search_data", _red_prohibida)
    monkeypatch.setattr(fetch.earthaccess, "download", _red_prohibida)
    fetch.reiniciar_ventana()
    fetch.limpiar_fallas()
    for v in ("VRP_VENTANA_BUSQUEDA", "VRP_CACHE_BUSQUEDA_DIR", "VRP_CONSERVAR_GRANULOS", "VRP_BUSQUEDA_VENTANA",
              "GITHUB_STEP_SUMMARY", "GITHUB_ACTIONS"):
        monkeypatch.delenv(v, raising=False)
    yield
    fetch.reiniciar_ventana()
    fetch.limpiar_fallas()


# ---------------------------------------------------------------- run_pipeline: cobertura

def test_informar_cobertura_estricto_sale_con_3_y_escribe_el_archivo(tmp_path, capsys):
    ruta = tmp_path / "cob.json"
    assert rp.informar_cobertura([FALLA], ruta_json=ruta, estricto=True) == 3
    assert json.loads(ruta.read_text(encoding="utf-8"))["fallas"] == [FALLA]
    assert "2026-09-02" in capsys.readouterr().out


def test_informar_cobertura_sin_estricto_avisa_y_sale_con_0(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    resumen = tmp_path / "resumen.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(resumen))
    assert rp.informar_cobertura([FALLA], estricto=False) == 0
    assert "::warning" in capsys.readouterr().out
    assert "2026-09-02" in resumen.read_text(encoding="utf-8")


def test_informar_cobertura_completa_sale_con_0(tmp_path):
    ruta = tmp_path / "cob.json"
    assert rp.informar_cobertura([], ruta_json=ruta, estricto=True) == 0
    assert json.loads(ruta.read_text(encoding="utf-8"))["fallas"] == []


def _main(monkeypatch, argv, al_procesar=None):
    vistos = []

    def falso_process_date(volcano, date, **kw):
        vistos.append((volcano["name"], date.strftime("%Y-%m-%d"), dict(fetch._VENTANA or {})))
        if al_procesar:
            al_procesar(volcano, date)

    monkeypatch.setattr(rp, "process_date", falso_process_date)
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py"] + argv)
    with pytest.raises(SystemExit) as e:
        rp.main()
    return e.value.code, vistos


def test_main_estricto_sale_con_3_si_un_dia_no_se_pudo_buscar(monkeypatch, tmp_path):
    cod, _ = _main(monkeypatch, ["--volcano", "Lascar", "--date", "2026-09-02", "--estricto-cobertura",
                                 "--cobertura-json", str(tmp_path / "c.json")],
                   al_procesar=lambda v, d: fetch._FALLAS.append(dict(FALLA)))
    assert cod == 3
    assert len(json.loads((tmp_path / "c.json").read_text(encoding="utf-8"))["fallas"]) == 1


def test_main_sin_estricto_no_falla_por_cobertura(monkeypatch):
    cod, _ = _main(monkeypatch, ["--volcano", "Lascar", "--date", "2026-09-02"],
                   al_procesar=lambda v, d: fetch._FALLAS.append(dict(FALLA)))
    assert cod in (0, None)


def test_main_configura_la_ventana_con_sus_fechas(monkeypatch):
    cod, vistos = _main(monkeypatch, ["--volcano", "Lascar", "--start", "2026-09-01", "--end", "2026-09-03"])
    assert [v[1] for v in vistos] == ["2026-09-01", "2026-09-02", "2026-09-03"]
    assert all(v[2]["ini"] == "2026-09-01" and v[2]["fin"] == "2026-09-03" for v in vistos)


def test_main_toma_la_ventana_del_entorno_para_un_solo_dia(monkeypatch, tmp_path):
    monkeypatch.setenv("VRP_VENTANA_BUSQUEDA", "2026-09-01:2026-09-20")
    monkeypatch.setenv("VRP_CACHE_BUSQUEDA_DIR", str(tmp_path))
    cod, vistos = _main(monkeypatch, ["--volcano", "Lascar", "--date", "2026-09-05"])
    assert vistos[0][2]["ini"] == "2026-09-01" and vistos[0][2]["fin"] == "2026-09-20"
    assert Path(vistos[0][2]["cache_dir"]) == tmp_path


def test_main_rechaza_una_fecha_fuera_de_la_ventana_del_entorno(monkeypatch):
    monkeypatch.setenv("VRP_VENTANA_BUSQUEDA", "2026-09-01:2026-09-20")
    monkeypatch.setattr(rp, "process_date", lambda *a, **k: None)
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "--volcano", "Lascar", "--date", "2026-09-25"])
    with pytest.raises(SystemExit) as e:
        rp.main()
    assert e.value.code not in (0, None)


def _process_date_que_baja(monkeypatch, tmp_path):
    monkeypatch.setattr(rp, "TMP_DIR", tmp_path)

    def falso_fetch(volcano, date, volcano_tmp, **kw):
        (volcano_tmp / "VIIRS_SNPP").mkdir(parents=True, exist_ok=True)
        (volcano_tmp / "VIIRS_SNPP" / "VNP02IMG.A2026245.0600.nc").write_bytes(b"x")
        return {}

    monkeypatch.setattr(rp.fetch, "fetch_for_volcano", falso_fetch)
    v = {"name": "Lascar", "display_name": "Lascar", "lat": -23.37, "lon": -67.73, "radius_km": 25}
    rp.process_date(v, datetime(2026, 9, 2))
    return tmp_path / "Lascar" / "20260902"


def test_process_date_borra_los_granulos_por_defecto(monkeypatch, tmp_path):
    assert not _process_date_que_baja(monkeypatch, tmp_path).exists()


def test_process_date_conserva_los_granulos_para_el_brazo_siguiente(monkeypatch, tmp_path):
    monkeypatch.setenv("VRP_CONSERVAR_GRANULOS", "1")
    assert (_process_date_que_baja(monkeypatch, tmp_path) / "VIIRS_SNPP").exists()


# ---------------------------------------------------------------- driver de brazos

class Ejecutor:
    def __init__(self, trabajo, fallas_por=None, rc_por=None):
        self.trabajo = Path(trabajo)
        self.llamadas = []
        self.fallas_por = fallas_por or {}
        self.rc_por = rc_por or {}

    def __call__(self, cmd, env, stdout, stderr):
        perfil = cmd[cmd.index("--profile") + 1]
        fecha = cmd[cmd.index("--date") + 1]
        volcan = cmd[cmd.index("--volcano") + 1]
        dia = Path(env["VRP_TMP_DIR"]) / volcan / fecha.replace("-", "")
        self.llamadas.append({"perfil": perfil, "fecha": fecha, "env": env, "cmd": cmd,
                              "habia_granulos": dia.exists()})
        dia.mkdir(parents=True, exist_ok=True)
        (dia / "granulo.nc").write_bytes(b"x")
        cob = Path(cmd[cmd.index("--cobertura-json") + 1])
        cob.parent.mkdir(parents=True, exist_ok=True)
        cob.write_text(json.dumps({"fallas": self.fallas_por.get((perfil, fecha), [])}), encoding="utf-8")

        class R:
            returncode = self.rc_por.get((perfil, fecha), 0)
        return R()


def test_driver_dia_por_fuera_brazo_por_dentro_con_cache_compartida(tmp_path):
    ej = Ejecutor(tmp_path)
    rc = rb.correr("Lascar", "2026-09-01", "2026-09-02", ["_a", "_b", "_c"], tmp_path, ejecutar=ej)
    assert rc == 0
    assert [(c["fecha"], c["perfil"]) for c in ej.llamadas] == [
        ("2026-09-01", "_a"), ("2026-09-01", "_b"), ("2026-09-01", "_c"),
        ("2026-09-02", "_a"), ("2026-09-02", "_b"), ("2026-09-02", "_c")]
    for clave in ("VRP_TMP_DIR", "VRP_CACHE_BUSQUEDA_DIR", "VRP_VENTANA_BUSQUEDA", "VRP_CONSERVAR_GRANULOS"):
        assert len({c["env"][clave] for c in ej.llamadas}) == 1, clave
    assert ej.llamadas[0]["env"]["VRP_VENTANA_BUSQUEDA"] == "2026-09-01:2026-09-02"
    assert ej.llamadas[0]["env"]["VRP_CONSERVAR_GRANULOS"] == "1"
    # el segundo y el tercer brazo encuentran los granulos del primero; el dia siguiente arranca limpio
    assert [c["habia_granulos"] for c in ej.llamadas] == [False, True, True, False, True, True]
    assert not (tmp_path / "granulos" / "Lascar" / "20260901").exists()
    assert not (tmp_path / "granulos" / "Lascar" / "20260902").exists()
    assert all("--overwrite" in c["cmd"] for c in ej.llamadas)


def test_driver_falla_si_un_brazo_falla(tmp_path):
    ej = Ejecutor(tmp_path, rc_por={("_b", "2026-09-01"): 1})
    assert rb.correr("Lascar", "2026-09-01", "2026-09-02", ["_a", "_b"], tmp_path, ejecutar=ej) == 1
    assert len(ej.llamadas) == 4  # sigue con el resto: un brazo caido no tira los otros dias


def test_driver_estricto_sale_con_3_y_junta_la_cobertura(tmp_path):
    ej = Ejecutor(tmp_path, fallas_por={("_a", "2026-09-02"): [FALLA]})
    salida = tmp_path / "cobertura.json"
    assert rb.correr("Lascar", "2026-09-01", "2026-09-02", ["_a", "_b"], tmp_path, ejecutar=ej,
                     estricto=True, cobertura_json=salida) == 3
    datos = json.loads(salida.read_text(encoding="utf-8"))
    assert datos["fallas"] == [dict(FALLA, perfil="_a")]


def test_driver_sin_estricto_no_falla_por_cobertura(tmp_path):
    ej = Ejecutor(tmp_path, fallas_por={("_a", "2026-09-02"): [FALLA]})
    assert rb.correr("Lascar", "2026-09-01", "2026-09-02", ["_a"], tmp_path, ejecutar=ej) == 0
