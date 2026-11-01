# -*- coding: utf-8 -*-
"""Vigilancia por plataforma (S159, cese de Suomi NPP el 2026-11-02 13:00 UTC).

POR QUÉ: cuando un satélite deja de entregar, CMR devuelve cero gránulos, `pipeline/fetch.py` lo vive como
«no hubo pasada», el job sale verde con «Cobertura: completa» y el tablero pierde esa plataforma sin aviso.
Ninguna vigilancia del proyecto miraba por plataforma: con NOAA-20 o NOAA-21 vivos, el bucket VIIRS seguía
«fresco» (experiments/_s159/cese_snpp/INFORME.md de la rama de pruebas, H1 y H2). Estas pruebas fijan las
cuatro respuestas del instrumento con datos sintéticos (controles positivos incluidos) y su nulo medido sobre
los datos reales: con la regla de 72 h, ni NOAA-20, ni NOAA-21, ni Terra, ni Aqua habrían alarmado una sola
vez entre el 2026-01-29 y el 2026-10-21.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from scripts import vigilar_plataformas as vp  # noqa: E402

SNPP = ("VIIRS_SNPP", "VIIRS_SNPP_750")
MODIS = ("MODIS_TERRA", "MODIS_AQUA")
CESE = datetime(2026, 11, 2, 13, 0, tzinfo=timezone.utc)


def _sinteticos(hasta, dias=20, quitar=(), quitar_desde=None):
    """Una pasada nocturna por sensor y día, como en los Tier A. `quitar` deja de producir desde `quitar_desde`."""
    regs = []
    for i in range(dias):
        dia = hasta - timedelta(days=i)
        for j, s in enumerate(vp.SENSORES):
            t = dia.replace(hour=4, minute=0) + timedelta(minutes=20 * j)
            if t > hasta:
                t -= timedelta(days=1)
            if s in quitar and (quitar_desde is None or t >= quitar_desde):
                continue
            regs.append((s, t))
    return regs


def _ceses():
    return vp.cargar_ceses()


# ── La configuración ────────────────────────────────────────────────────────


def test_la_lista_de_ceses_trae_snpp_con_fecha_y_fuente():
    ceses = _ceses()
    snpp = [c for c in ceses if c["plataforma"] == "Suomi NPP"]
    assert len(snpp) == 1
    assert tuple(snpp[0]["sensores"]) == SNPP
    assert snpp[0]["desde"] == CESE
    assert snpp[0]["fuente"].startswith("https://www.earthdata.nasa.gov/")


def test_los_sensores_vigilados_son_los_que_escribe_el_pipeline():
    # A48: la convención real del campo `sensor`, verificada en data/mirova_equivalent/Villarrica.json.
    assert set(vp.SENSORES) == {"VIIRS_SNPP", "VIIRS_SNPP_750", "VIIRS_NOAA20", "VIIRS_NOAA20_750",
                                "VIIRS_NOAA21", "VIIRS_NOAA21_750", "MODIS_TERRA", "MODIS_AQUA"}


# ── Las cuatro respuestas, con controles positivos ──────────────────────────


def test_todo_vivo_no_avisa():
    ahora = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    v = vp.evaluar(_sinteticos(ahora), ahora, _ceses())
    assert v["estado"] == "ok"
    assert v["alarmas"] == [] and v["ceses_confirmados"] == []


def test_sin_modis_alarma_por_plataforma():
    ahora = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    regs = _sinteticos(ahora, quitar=MODIS, quitar_desde=ahora - timedelta(days=5))
    v = vp.evaluar(regs, ahora, _ceses())
    assert v["estado"] == "alarma"
    assert sorted(a["plataforma"] for a in v["alarmas"]) == ["Aqua", "Terra"]
    assert v["ceses_confirmados"] == []


def test_sin_snpp_antes_del_cese_es_alarma():
    ahora = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    regs = _sinteticos(ahora, quitar=SNPP, quitar_desde=ahora - timedelta(days=5))
    v = vp.evaluar(regs, ahora, _ceses())
    assert v["estado"] == "alarma"
    assert [a["plataforma"] for a in v["alarmas"]] == ["Suomi NPP"]
    assert v["ceses_confirmados"] == []


def test_sin_snpp_despues_del_cese_es_solo_informativo():
    ahora = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)
    regs = _sinteticos(ahora, quitar=SNPP, quitar_desde=CESE - timedelta(hours=6))
    v = vp.evaluar(regs, ahora, _ceses())
    assert v["estado"] == "ok"
    assert v["alarmas"] == []
    assert [c["plataforma"] for c in v["ceses_confirmados"]] == ["Suomi NPP"]


def test_snpp_muerto_y_ademas_noaa21_muerto_despues_del_cese_alarma_por_noaa21():
    ahora = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)
    regs = _sinteticos(ahora, quitar=SNPP + ("VIIRS_NOAA21", "VIIRS_NOAA21_750"), quitar_desde=CESE)
    v = vp.evaluar(regs, ahora, _ceses())
    assert v["estado"] == "alarma"
    assert [a["plataforma"] for a in v["alarmas"]] == ["NOAA-21"]
    assert [c["plataforma"] for c in v["ceses_confirmados"]] == ["Suomi NPP"]


def test_dato_vacio_total_es_caida_general_y_no_por_plataforma():
    ahora = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    v = vp.evaluar([], ahora, _ceses())
    assert v["estado"] == "caida_general"
    assert v["alarmas"] == [] and v["ceses_confirmados"] == []
    # También si todo calló hace más de la ventana: no se culpa a ninguna plataforma.
    viejos = _sinteticos(ahora - timedelta(days=10))
    assert vp.evaluar(viejos, ahora, _ceses())["estado"] == "caida_general"


def test_el_borde_de_la_ventana_es_72_horas():
    assert vp.VENTANA_H == 72
    ahora = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    base = [(s, ahora - timedelta(hours=1)) for s in vp.SENSORES if s != "VIIRS_NOAA20"]
    dentro = base + [("VIIRS_NOAA20", ahora - timedelta(hours=71, minutes=59))]
    fuera = base + [("VIIRS_NOAA20", ahora - timedelta(hours=72, minutes=1))]
    assert vp.evaluar(dentro, ahora, _ceses())["alarmas"] == []
    assert [a["sensores"] for a in vp.evaluar(fuera, ahora, _ceses())["alarmas"]] == [["VIIRS_NOAA20"]]


# ── Qué hace con los issues ─────────────────────────────────────────────────


def _veredicto_cese():
    ahora = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)
    return vp.evaluar(_sinteticos(ahora, quitar=SNPP, quitar_desde=CESE), ahora, _ceses())


def _veredicto_alarma():
    ahora = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    return vp.evaluar(_sinteticos(ahora, quitar=MODIS, quitar_desde=ahora - timedelta(days=5)), ahora, _ceses())


def test_el_informativo_se_abre_una_sola_vez():
    v = _veredicto_cese()
    primero = vp.planear_issues(v, abiertos_alarma=[], existentes_cese=[])
    crear = [a for a in primero if a[0] == "create"]
    assert len(crear) == 1 and crear[0][1] == vp.titulo_cese("Suomi NPP")
    assert crear[0][2] == vp.LABEL_CESE
    # Ya existe (abierto o cerrado, misma etiqueta y título): nada más.
    ya = [{"number": 9, "title": vp.titulo_cese("Suomi NPP"), "state": "CLOSED"}]
    assert vp.planear_issues(v, abiertos_alarma=[], existentes_cese=ya) == []


def test_la_alarma_abre_y_si_existe_comenta():
    v = _veredicto_alarma()
    primero = vp.planear_issues(v, abiertos_alarma=[], existentes_cese=[])
    crear = [a for a in primero if a[0] == "create"]
    assert len(crear) == 1 and crear[0][1] == vp.TITULO_ALARMA and crear[0][2] == vp.LABEL_ALARMA
    assert vp.TITULO_ALARMA != vp.titulo_cese("Suomi NPP")
    abierto = [{"number": 12, "title": vp.TITULO_ALARMA, "body": "viejo"}]
    luego = vp.planear_issues(v, abiertos_alarma=abierto, existentes_cese=[])
    assert [a[0] for a in luego] == ["comment"] and luego[0][1] == 12


def test_al_recuperarse_cierra_la_alarma():
    ahora = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    sano = vp.evaluar(_sinteticos(ahora), ahora, _ceses())
    abierto = [{"number": 12, "title": vp.TITULO_ALARMA, "body": "x"}]
    acciones = vp.planear_issues(sano, abiertos_alarma=abierto, existentes_cese=[])
    assert [a[0] for a in acciones] == ["comment", "close"] and all(a[1] == 12 for a in acciones)


def test_la_caida_general_no_toca_issues_de_plataforma():
    ahora = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    caida = vp.evaluar([], ahora, _ceses())
    abierto = [{"number": 12, "title": vp.TITULO_ALARMA, "body": "x"}]
    assert vp.planear_issues(caida, abiertos_alarma=abierto, existentes_cese=[]) == []


def test_el_informe_dice_caida_general_en_palabras():
    ahora = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    txt = vp.informe(vp.evaluar([], ahora, _ceses()))
    assert "caída general" in txt.lower()
    assert "\u2014" not in txt and "\u2013" not in txt   # guiones largo y medio


# ── El enganche al workflow ─────────────────────────────────────────────────


def test_el_healthcheck_corre_la_vigilancia_con_permisos_minimos():
    ruta = RAIZ / ".github" / "workflows" / "nrt-healthcheck.yml"
    src = ruta.read_text(encoding="utf-8")
    wf = yaml.safe_load(src)
    assert "on" in wf, "la clave on debe ir entre comillas (A43)"
    job = wf["jobs"]["healthcheck"]
    assert job["permissions"] == {"contents": "read", "issues": "write"}
    pasos = [p for p in job["steps"] if "vigilar_plataformas.py" in (p.get("run") or "")]
    assert len(pasos) == 1, "el healthcheck debe correr scripts/vigilar_plataformas.py una vez"
    paso = pasos[0]
    assert "--issues" in paso["run"]
    assert paso.get("if") and '"' not in paso["if"], "if: con comillas simples"
    assert paso.get("env", {}).get("GH_TOKEN")


# ── El nulo medido sobre los datos reales (A110, A116) ──────────────────────


@pytest.fixture(scope="module")
def reales():
    regs = vp.cargar_registros(RAIZ / "data" / "mirova_equivalent")
    if not regs:
        pytest.skip("sin datos de los Tier A en este checkout")
    return regs


def test_nulo_en_los_datos_reales_ninguna_plataforma_viva_habria_alarmado(reales):
    """Repetición diaria a las 12:00 UTC del 2026-01-29 al 2026-10-21 (después del hueco del backfill)."""
    desde = datetime(2026, 1, 29, 12, 0, tzinfo=timezone.utc)
    hasta = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    rep = vp.repetir(reales, desde, hasta, _ceses())
    assert rep["dias"] == 266
    otras = {s: n for s, n in rep["alarmas_por_sensor"].items() if s not in SNPP}
    assert otras == {}, f"una plataforma sana habría alarmado: {otras}"
    assert rep["caidas_generales"] == 0


def test_control_positivo_en_los_datos_reales_quitar_noaa21_alarma(reales):
    corte = datetime(2026, 10, 10, 0, 0, tzinfo=timezone.utc)
    sin21 = [(s, t) for s, t in reales if not (s.startswith("VIIRS_NOAA21") and t >= corte)]
    ahora = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    v = vp.evaluar(sin21, ahora, _ceses())
    assert [a["plataforma"] for a in v["alarmas"]] == ["NOAA-21"]
