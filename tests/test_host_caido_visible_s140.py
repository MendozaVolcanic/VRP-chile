# -*- coding: utf-8 -*-
"""Fase 0 tarea 8d (S140): el host de descarga caido (A64) queda visible en GitHub Actions.

POR QUE: el circuit-breaker de S102 marca un host de NASA como caido para toda la corrida y salta
sus descargas. Es la decision correcta (reintentar un host caido colgaba el job 50 min), pero hoy
solo deja una linea `[diag]` enterrada en el log: el job termina verde con menos granules y nadie lo
ve. S139 midio el costo en cobertura. Ahora cada host caido emite un `::warning::` (una vez por
host, no por granule, para no inundar la pagina del run) y el resumen del job cuenta las descargas
saltadas.
"""
import pytest

import pipeline.fetch as fetch

HOST = "nrt3.modaps.eosdis.nasa.gov"


@pytest.fixture(autouse=True)
def _limpio():
    fetch.reset_transient_breakers()
    yield
    fetch.reset_transient_breakers()


def test_un_warning_por_host_y_linea_en_el_resumen(monkeypatch, tmp_path, capsys):
    resumen = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(resumen))
    fetch._avisar_host_caido({HOST}, "MYD021KM.A2026247.0750.061.2026247092322.NRT.hdf")
    fetch._avisar_host_caido({HOST}, "otro granule")
    out = capsys.readouterr().out
    assert out.count("::warning") == 1
    assert HOST in resumen.read_text(encoding="utf-8")


def test_descarga_saltada_se_cuenta(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    fetch._DOWN_DOWNLOAD_HOSTS.add(HOST)
    monkeypatch.setattr(fetch, "_granule_hosts", lambda granules: {HOST})
    for _ in range(2):
        with pytest.raises(RuntimeError):
            fetch.download_granules([{}], tmp_path)
    assert fetch.descargas_saltadas() == 2
    assert capsys.readouterr().out.count("::warning") == 1


def test_fuera_de_actions_no_imprime_comandos_de_github(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    fetch._avisar_host_caido({HOST}, "x")
    assert "::warning" not in capsys.readouterr().out


def test_resumen_final_del_volcan(monkeypatch, tmp_path):
    resumen = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(resumen))
    fetch._DOWN_DOWNLOAD_HOSTS.add(HOST)
    monkeypatch.setattr(fetch, "_granule_hosts", lambda granules: {HOST})
    with pytest.raises(RuntimeError):
        fetch.download_granules([{}], tmp_path)
    fetch._resumen_hosts_caidos("Lascar")
    texto = resumen.read_text(encoding="utf-8")
    assert "Lascar" in texto and HOST in texto and "1" in texto


def test_sin_host_caido_el_resumen_no_escribe(monkeypatch, tmp_path):
    resumen = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(resumen))
    fetch._resumen_hosts_caidos("Lascar")
    assert not resumen.exists()


def test_reset_limpia_contador_y_avisos(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    fetch._avisar_host_caido({HOST}, "x")
    fetch.reset_transient_breakers()
    assert fetch.descargas_saltadas() == 0
    fetch._avisar_host_caido({HOST}, "y")
    assert capsys.readouterr().out.count("::warning") == 2
