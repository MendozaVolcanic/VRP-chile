# -*- coding: utf-8 -*-
"""
S133 - La medicion de cadencia del cron tiene que contar AUSENCIAS, que es lo que ningun
monitor del repo miraba.

POR QUE. El 2026-08-27 GitHub dejo de entregar la mitad de los eventos `schedule` del repo
y nadie se entero durante ocho dias. No fallo ningun monitor: `nrt-monitor` mira 3 fallas
seguidas y no hubo ninguna (200 corridas success), y `nrt-healthcheck` mira dato de mas de
48 h y nunca paso de 7. Las dos metricas verdes sobre un mecanismo degradado a la mitad
(A87). Una corrida que NO ocurre no deja rastro que un monitor de fallas pueda ver, asi que
hay que contarla contra lo declarado.
"""
import datetime as dt
import os
import sys

import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from scripts.medir_cadencia_cron import (CRITICO, ESPERADO_POR_DIA,  # noqa: E402
                                         a_markdown, medir)

AHORA = dt.datetime(2026, 9, 4, 12, 0, tzinfo=dt.timezone.utc)


def _corrida(nombre, horas_atras, event="schedule"):
    return {"name": nombre,
            "createdAt": (AHORA - dt.timedelta(hours=horas_atras)).isoformat(),
            "event": event}


def test_cron_puntual_da_entrega_cercana_al_100():
    """12 corridas del NRT en 24 h es exactamente lo declarado."""
    corridas = [_corrida(CRITICO, h) for h in range(0, 24, 2)]
    res = medir(corridas, AHORA, ventana_h=24)
    fila = next(f for f in res["filas"] if f["workflow"] == CRITICO)
    assert fila["obtenido"] == 12
    assert fila["entrega_pct"] == pytest.approx(100.0)
    assert res["alerta"] is False


def test_reproduce_la_degradacion_real_de_agosto():
    """El caso que motiva todo esto: la mitad de las corridas no ocurren."""
    corridas = [_corrida(CRITICO, h) for h in (1, 6, 11, 16, 21)]
    res = medir(corridas, AHORA, ventana_h=24)
    fila = next(f for f in res["filas"] if f["workflow"] == CRITICO)
    assert fila["obtenido"] == 5
    assert 40 <= fila["entrega_pct"] <= 42
    # Degradada pero NO alerta: no hay perdida de datos, y una alerta que no se puede
    # accionar es ruido (la leccion de la issue #567).
    assert res["alerta"] is False


def test_cero_corridas_del_critico_si_alerta():
    """La ausencia TOTAL del NRT es lo unico accionable por si solo."""
    otros = [_corrida("Deploy GitHub Pages", h) for h in range(0, 24, 2)]
    res = medir(otros, AHORA, ventana_h=24)
    assert res["corridas_del_critico"] == 0
    assert res["alerta"] is True
    assert CRITICO in res["motivo_alerta"]


def test_no_alerta_por_lista_vacia_de_otros_workflows():
    """Un solo NRT vivo basta para no alertar, aunque todo lo demas este en cero."""
    res = medir([_corrida(CRITICO, 3)], AHORA, ventana_h=24)
    assert res["alerta"] is False


def test_un_dispatch_manual_no_cuenta_como_puntualidad_del_cron():
    """Correr el workflow a mano no dice nada sobre si el cron esta llegando."""
    manual = [_corrida(CRITICO, h, event="workflow_dispatch") for h in range(0, 24, 2)]
    res = medir(manual, AHORA, ventana_h=24)
    assert res["corridas_del_critico"] == 0
    assert res["alerta"] is True


def test_las_corridas_fuera_de_la_ventana_no_cuentan():
    viejas = [_corrida(CRITICO, h) for h in (30, 40, 50)]
    res = medir(viejas, AHORA, ventana_h=24)
    assert res["corridas_del_critico"] == 0


def test_la_ventana_escala_lo_esperado_y_no_lo_deja_fijo():
    """Con media ventana se espera la mitad; si no, el porcentaje mentiria."""
    corridas = [_corrida(CRITICO, h) for h in range(0, 12, 2)]
    res = medir(corridas, AHORA, ventana_h=12)
    fila = next(f for f in res["filas"] if f["workflow"] == CRITICO)
    assert fila["esperado"] == pytest.approx(6.0)
    assert fila["obtenido"] == 6
    assert fila["entrega_pct"] == pytest.approx(100.0)


def test_un_workflow_desconocido_no_rompe_ni_se_cuela():
    res = medir([_corrida("Workflow Inventado", 1), _corrida(CRITICO, 1)],
                AHORA, ventana_h=24)
    assert {f["workflow"] for f in res["filas"]} == set(ESPERADO_POR_DIA)


def test_una_fecha_corrupta_se_ignora_en_vez_de_reventar():
    """El monitor no puede caerse por un registro mal formado: dejaria de vigilar."""
    corridas = [{"name": CRITICO, "createdAt": "no-es-fecha", "event": "schedule"},
                {"name": CRITICO, "createdAt": None, "event": "schedule"},
                _corrida(CRITICO, 2)]
    res = medir(corridas, AHORA, ventana_h=24)
    assert res["corridas_del_critico"] == 1


def test_el_markdown_dice_que_entrega_baja_no_es_perdida_de_datos():
    """Sin esa frase, quien lea el reporte va a leer 40 % como dato perdido."""
    res = medir([_corrida(CRITICO, h) for h in (1, 6, 11)], AHORA, ventana_h=24)
    md = a_markdown(res)
    assert "no implica perdida de datos" in md
    assert "|" in md and CRITICO in md


def test_el_markdown_muestra_el_motivo_cuando_alerta():
    res = medir([], AHORA, ventana_h=24)
    assert "⚠️" in a_markdown(res)


def test_lo_esperado_por_dia_coincide_con_el_cron_declarado_en_el_yml():
    """Si alguien cambia un cron y no el contrato, el porcentaje queda mintiendo."""
    import io
    import re
    esperado_de_yml = {
        "NRT VRP Pipeline (both profiles)": (".github/workflows/nrt.yml", 12),
        "Deploy GitHub Pages": (".github/workflows/pages-deploy.yml", 12),
    }
    for nombre, (ruta, por_dia) in esperado_de_yml.items():
        src = io.open(os.path.join(RAIZ, ruta), encoding="utf-8").read()
        m = re.search(r'-\s*cron:\s*["\']([^"\']+)["\']', src)
        assert m, "no encontre el cron en %s" % ruta
        hora = m.group(1).split()[1]          # campo de horas del cron
        paso = int(hora.split("/")[1]) if "/" in hora else 24
        assert 24 // paso == por_dia == ESPERADO_POR_DIA[nombre], (
            "%s declara cada %s h (=%d/dia) pero el contrato dice %d"
            % (ruta, paso, 24 // paso, ESPERADO_POR_DIA[nombre]))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
