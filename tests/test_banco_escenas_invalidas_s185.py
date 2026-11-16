# -*- coding: utf-8 -*-
"""S185 (decisión b.1 de Nicolás): el banco de paridad y el auto-audit no cuentan como pasada «sin anomalía» una escena
que la vía no pudo medir.

POR QUÉ. La vía «código MIROVA» deja vacía una escena cuando la mitad o más de la grilla no tiene dato útil, o por
reflejo solar, la guarda con 0 MW y sin píxeles y lo anota en `diag_codigo_mirova.motivo_vacio`. En el código de
MIROVA esa escena queda NaN (su tabla a veces lista la pasada con VRP 0; si es medición o NaN escrito como 0 es SIN
DATO). El tablero (#1005) y la comparación vía/K (#1006) ya las sacaron; el banco y el auto-audit las seguían
contando: si MIROVA había listado la pasada con VRP 0, como negativo limpio acertado (infla la especificidad); si
MIROVA alertaba ahí, como pasada vista sin publicar (una pérdida de detección que no fue: no miramos, S150).

QUÉ VIGILA.
1. `cargar_nuestros(..., excluir_escenas_invalidas=True)` no devuelve la escena inválida y sí la válida de al lado;
   con el valor por defecto devuelve las dos (los demás llamadores no cambian).
2. El banco (`main`) y el auto-audit llaman con `excluir_escenas_invalidas=True`; las vigilancias de la guardia y de
   la sombra NO (su regla sellada pre-autoriza revertir cuando producción «calla»; ese cambio no es de este PR).
3. `auto_audit_weekly.nuestros_por_noche` no marca vista la noche ni agrega la pasada por una escena inválida, sí
   cuenta el día y la informa en `fuera_de_detector["escena_invalida"]`.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Si el filtro no estuviera, la prueba 1 y la 3 fallan (la escena inválida
aparece). (2) Cada prueba tiene su control: la escena válida de la misma noche sí aparece, y con el valor por defecto
la inválida también, así que el instrumento puede dar los dos resultados.
"""
import ast
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import banco_paridad as bp  # noqa: E402
import scripts.auto_audit_weekly as aa  # noqa: E402

node = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")

VOL = "Villarrica"
VENTANA = ("2026-11-13", "2026-11-13")
# Escena real de Villarrica VIIRS 750 del 2026-11-13 06:12 (la que #1005 muestra como «escena sin datos»), reducida.
INVALIDA = {"sensor": "VIIRS_NOAA20_750", "datetime_utc": "2026-11-13 06:12", "distance_class": None,
            "vrp_mw": 0.0, "anomaly_pixels": [], "primary_cluster": None, "via_codigo_mirova": True,
            "diag_codigo_mirova": {"motivo_vacio": "escena_invalida", "roi": "def"}}
VALIDA = {"sensor": "VIIRS_NOAA21_750", "datetime_utc": "2026-11-13 05:20", "distance_class": None,
          "vrp_mw": 0.0, "anomaly_pixels": [], "primary_cluster": None, "via_codigo_mirova": True,
          "diag_codigo_mirova": {"roi": "def"}}


def test_es_escena_invalida_solo_con_motivo():
    assert bp.es_escena_invalida(INVALIDA)
    assert not bp.es_escena_invalida(VALIDA)
    assert not bp.es_escena_invalida({"diag_codigo_mirova": {"motivo_vacio": None}})
    assert not bp.es_escena_invalida({"diag_codigo_mirova": None})
    assert not bp.es_escena_invalida({})


def _carpeta(tmp_path):
    for vol in bp.VOLS:
        (tmp_path / f"{vol}.json").write_text(
            json.dumps({"records": [INVALIDA, VALIDA] if vol == VOL else []}), encoding="utf-8")
    return tmp_path


@node
def test_cargar_nuestros_excluye_la_escena_invalida_solo_si_se_pide(tmp_path):
    inner, coords = bp.inner_desde_html(), bp._coords_por_volcan()
    data = _carpeta(tmp_path)
    por_defecto = bp.cargar_nuestros(coords, inner, VENTANA, data=data)
    # control: con el valor por defecto entran las dos (y ninguna cae en el filtro diurno)
    assert sorted(r["sensor"] for r in por_defecto) == ["VIIRS_NOAA20_750", "VIIRS_NOAA21_750"], por_defecto
    filtrado = bp.cargar_nuestros(coords, inner, VENTANA, data=data, excluir_escenas_invalidas=True)
    assert [r["sensor"] for r in filtrado] == ["VIIRS_NOAA21_750"], filtrado
    # el predicado de node sigue alineado con su record tras el filtro (zip de recs y casos)
    assert filtrado[0]["pub"] == next(r["pub"] for r in por_defecto if r["sensor"] == "VIIRS_NOAA21_750")


def _llamadas(path):
    """(nombre de la función que llama, tiene excluir_escenas_invalidas=True) por cada llamada a cargar_nuestros."""
    arbol = ast.parse(Path(path).read_text(encoding="utf-8"))
    out = []
    for fn in ast.walk(arbol):
        if not isinstance(fn, ast.FunctionDef):
            continue
        for n in ast.walk(fn):
            if isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", None)) == "cargar_nuestros":
                kw = {k.arg: k.value for k in n.keywords}
                v = kw.get("excluir_escenas_invalidas")
                out.append((fn.name, isinstance(v, ast.Constant) and v.value is True))
    return out


def test_banco_y_auto_audit_filtran():
    banco = _llamadas(ROOT / "scripts" / "banco_paridad.py")
    assert ("main", True) in banco, banco
    audit = _llamadas(ROOT / "scripts" / "auto_audit_weekly.py")
    assert audit and all(f for _, f in audit), audit


@pytest.mark.parametrize("script", ["vigilancia_guardia_modis.py", "vigilancia_guardia_viirs.py",
                                    "vigilancia_sombra.py"])
def test_vigilancias_de_reversion_no_filtran(script):
    llamadas = _llamadas(ROOT / "scripts" / script)
    assert llamadas, f"{script} ya no llama a cargar_nuestros: revisar esta prueba"
    assert not any(f for _, f in llamadas), (f"{script} filtra escenas inválidas: eso cambia «calla» por «sin record» "
                                             f"en la regla de reversión y no es de b.1: {llamadas}")


def _aa_rec(rec):
    r = json.loads(json.dumps(rec))
    r["regimen"] = {"perfil": "mirova_equivalent", "codigo_sha": None}
    return r


def test_auto_audit_no_marca_vista_la_noche_por_una_escena_invalida():
    win = ("2026-11-01", "2026-11-14")
    frontera = aa.leer_frontera_k()
    via = aa.fronteras_via({VOL: [_aa_rec(INVALIDA), _aa_rec(VALIDA)]})
    solo_invalida = aa.nuestros_por_noche({VOL: [_aa_rec(INVALIDA)]}, win, frontera, via_modis=via)
    assert (VOL, "VIIRS750", "2026-11-13") not in solo_invalida["vistos"], solo_invalida["vistos"]
    assert not solo_invalida["pasadas"].get((VOL, "VIIRS750")), solo_invalida["pasadas"]
    assert "2026-11-13" in solo_invalida["dias_con_datos"]
    assert solo_invalida["fuera_de_detector"].get("escena_invalida") == 1, solo_invalida["fuera_de_detector"]
    # control: la escena válida de la misma noche sí la marca vista y agrega su pasada
    con_valida = aa.nuestros_por_noche({VOL: [_aa_rec(INVALIDA), _aa_rec(VALIDA)]}, win, frontera, via_modis=via)
    assert (VOL, "VIIRS750", "2026-11-13") in con_valida["vistos"], con_valida
    assert [p[0] for p in con_valida["pasadas"][(VOL, "VIIRS750")]] == ["2026-11-13 05:20"], con_valida["pasadas"]
