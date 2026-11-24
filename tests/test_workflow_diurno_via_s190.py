# -*- coding: utf-8 -*-
"""S190, adenda V §5 y §6: el workflow del A/B diurno sobre la vía y su conteo de cobertura.

POR QUÉ. El workflow es copia de reproc-s151-ab-diurno.yml. Un default que apunte a los brazos viejos corre horas el
A/B equivocado (verificador V13 de S163); una línea FLAGS_BRAZO sin los flags de la vía deja a la compuerta I1 sin
nada que leer; un --no-night-filter abriría el día sin los flags (trampa de S92); y el conteo de S151 marcaba como
error justo lo que aquí se abre (MODIS de día). Estas pruebas leen el workflow ya parseado (A43) y corren el conteo
nuevo sobre directorios sintéticos.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "reproc-s190-ab-diurno-via.yml"
sys.path.insert(0, str(ROOT / "experiments" / "_s190_diurno"))

import contar_pasadas_via as cpv  # noqa: E402

CONTROL, DIURNO = "_s190_ab_diurno_via_control", "_s190_ab_diurno_via_on"


def _wf():
    texto = WF.read_text(encoding="utf-8")
    return texto, yaml.safe_load(texto)


def _codigo(texto):
    return "\n".join(ln for ln in texto.splitlines() if not ln.lstrip().startswith("#"))


def test_on_entre_comillas_y_entradas_con_los_brazos_de_s190():
    texto, d = _wf()
    assert '"on":' in texto and "on" in d
    ins = d["on"]["workflow_dispatch"]["inputs"]
    assert json.loads(ins["brazos"]["default"]) == [CONTROL, DIURNO]
    assert ins["control"]["default"] == CONTROL
    assert ins["preregistro_aprobado"]["default"] == "no"
    assert "_s190_diurno/ADENDA_VIA.md" in ins["preregistro_aprobado"]["description"]


def test_grupo_de_concurrencia_propio_y_max_parallel_3():
    _, d = _wf()
    assert d["concurrency"]["group"] == "s190-ab-diurno-via"
    assert d["jobs"]["reproc"]["strategy"]["max-parallel"] == 3


def test_flags_brazo_trae_la_via_y_los_dos_flags_del_dia():
    texto, _ = _wf()
    linea = [ln for ln in texto.splitlines() if "FLAGS_BRAZO ' + json.dumps" in ln]
    assert len(linea) == 1
    for k in ("ENABLE_MODIS_CODIGO_MIROVA", "ENABLE_V375_CODIGO_MIROVA", "ENABLE_V750_CODIGO_MIROVA",
              "ENABLE_DAYTIME_VIIRS", "ENABLE_DAYTIME_MODIS", "PROFILE_NAME", "DATA_SUBDIR"):
        assert "'%s'" % k in linea[0], k


def test_el_brazo_comprueba_los_dos_flags_del_dia_y_la_via_contra_el_control():
    texto, _ = _wf()
    paso = texto.split("El brazo LEE lo que declara")[1].split("Reproceso del brazo")[0]
    assert "ARM_CONTROL" in paso
    assert "p.ENABLE_DAYTIME_MODIS == (p.PROFILE_NAME != os.environ['ARM_CONTROL'])" in paso
    assert "aplica_filtro_nocturno(True, 'MODIS_AQUA')" in paso
    assert "p.ENABLE_MODIS_CODIGO_MIROVA and p.ENABLE_V375_CODIGO_MIROVA and p.ENABLE_V750_CODIGO_MIROVA" in paso


def test_sin_no_night_filter_solo_token_y_sin_push_a_main():
    texto, _ = _wf()
    cod = _codigo(texto)
    assert "--no-night-filter" not in cod
    assert "secrets.EARTHDATA_TOKEN" in cod
    assert "EARTHDATA_USERNAME" not in cod and "EARTHDATA_PASSWORD" not in cod
    assert not re.search(r"git push[^\n]*\bmain\b", cod)
    assert 'git push origin "$RAMA"' in cod and "RAMA: s190-ab-diurno-via/" in cod


def test_artefactos_y_salidas_con_prefijo_propio_y_conteo_nuevo():
    texto, _ = _wf()
    cod = _codigo(texto)
    assert "s151" not in cod
    assert "name: s190diurno-${{ matrix.profile }}-${{ matrix.volcano }}" in cod
    assert "pattern: s190diurno-*" in cod and "name: s190diurno-todo" in cod
    assert "experiments/_s190_diurno/contar_pasadas_via.py" in cod
    assert "experiments/_s190_diurno/salidas/${GITHUB_RUN_ID}" in cod


# ------------------------------------------------------------------------------------------- conteo de cobertura
def _escribir(d, vol, recs):
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{vol}.json").write_text(json.dumps({"records": recs}), encoding="utf-8")


def _r(sensor, t, dayflag):
    return {"sensor": sensor, "datetime_utc": t, "granule": "g" + t, "diag_codigo_mirova": {"dayflag": dayflag}}


NOCHE = [_r("MODIS_AQUA", "2026-11-10 05:00", 0), _r("VIIRS_NOAA20", "2026-11-10 06:00", 0)]
DIA = [_r("MODIS_AQUA", "2026-11-10 15:00", 1), _r("VIIRS_NOAA20", "2026-11-10 17:00", 1),
       _r("VIIRS_NOAA20_750", "2026-11-10 17:00", 1)]
COORDS = {"Lascar": (-23.37, -67.73)}


def test_conteo_acepta_el_brazo_diurno_con_los_tres_sensores(tmp_path):
    _escribir(tmp_path / CONTROL, "Lascar", NOCHE)
    _escribir(tmp_path / DIURNO, "Lascar", NOCHE + DIA)
    filas, mal = cpv.revisar(tmp_path / CONTROL, [tmp_path / DIURNO], ("2026-11-10", "2026-11-10"), COORDS)
    assert mal == []
    assert filas[1]["dia_dayflag1_por_sensor"] == {"MODIS": 1, "VIIRS375": 1, "VIIRS750": 1}


def test_conteo_avisa_si_modis_no_abrio_el_dia(tmp_path):
    _escribir(tmp_path / CONTROL, "Lascar", NOCHE)
    _escribir(tmp_path / DIURNO, "Lascar", NOCHE + DIA[1:])
    _, mal = cpv.revisar(tmp_path / CONTROL, [tmp_path / DIURNO], ("2026-11-10", "2026-11-10"), COORDS)
    assert any("CERO pasadas diurnas con dayflag 1 en MODIS" in m for m in mal)


def test_conteo_avisa_dia_en_el_control_y_noche_despareja(tmp_path):
    _escribir(tmp_path / CONTROL, "Lascar", NOCHE + DIA[:1])
    _escribir(tmp_path / DIURNO, "Lascar", NOCHE[:1] + DIA)
    _, mal = cpv.revisar(tmp_path / CONTROL, [tmp_path / DIURNO], ("2026-11-10", "2026-11-10"), COORDS)
    assert any("el CONTROL trae 1 pasadas diurnas" in m for m in mal)
    assert any("noches desparejas (faltan 1, sobran 0" in m for m in mal)
