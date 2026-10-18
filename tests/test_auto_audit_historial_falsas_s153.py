# -*- coding: utf-8 -*-
"""S153 (adopcion de K, REGLA_ADOPCION.md §4.8): la linea de `history.jsonl` lleva la publicacion en
negativos limpios por sensor.

POR QUE: con K la publicacion de VIIRS 375 en pasadas donde MIROVA miro y no vio nada cae de 85 a 88 %
a 2,5 a 3,7 % (experiments/_s153_fk_v2/combinado.log y v2.log, seccion 9). Hasta S153 ese numero se
calculaba cada semana (`falsas_publicaciones` en latest.json) pero no entraba al historial, que es lo
unico que se conserva semana a semana: latest.json se sobrescribe. Sin la serie, la sombra del §4.9
(investigar si la publicacion en negativos limpios sube por sobre lo medido en el A/B) no tiene contra
que comparar.

DECISION S140 que se mantiene: medir SIN alarma. El test exige que la linea nueva no agregue flags ni
cambie el veredicto.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.auto_audit_weekly as aa  # noqa: E402


def _out(falsas, flags=None):
    return {"generated_utc": "2026-10-19T12:00:00Z", "verdict": "VERDE",
            "recall": {s: {"recall_crater_pct": 99.0} for s in aa.SENSORS},
            "falsas_publicaciones": falsas, "flags": list(flags or [])}


def _falsas(pcts):
    return {"por_sensor": {s: {"n_neg_limpio": 100, "n_publica": int(p or 0),
                               "falsas_pub_pct": p} for s, p in pcts.items()},
            "alarma": False}


def test_la_linea_lleva_la_publicacion_en_negativos_limpios_por_sensor():
    falsas = _falsas({"MODIS": 0.9, "VIIRS375": 3.7, "VIIRS750": 1.1})
    linea = aa.linea_historial(_out(falsas), cobertura_pct=100.0, gt_stale_dias=0)
    assert linea["falsas_pub_pct"] == {"MODIS": 0.9, "VIIRS375": 3.7, "VIIRS750": 1.1}
    assert linea["n_neg_limpio"] == {s: 100 for s in aa.SENSORS}


def test_conserva_las_claves_viejas_y_no_agrega_alarma():
    falsas = _falsas({"MODIS": 50.0, "VIIRS375": 90.0, "VIIRS750": 40.0})
    out = _out(falsas, flags=["recall MODIS 90% < banda 95%"])
    linea = aa.linea_historial(out, cobertura_pct=95.1, gt_stale_dias=1)
    assert linea["date"] == "2026-10-19"
    assert linea["verdict"] == "VERDE"
    assert linea["cobertura_pct"] == 95.1 and linea["gt_stale_dias"] == 1
    assert linea["recall"] == {s: 99.0 for s in aa.SENSORS}
    # sin alarma (S140): la metrica no cuenta como flag ni toca el veredicto
    assert linea["n_flags"] == 1
    assert out["flags"] == ["recall MODIS 90% < banda 95%"]


def test_si_el_banco_no_corrio_queda_none_y_el_error_a_la_vista():
    falsas = {"error": "FileNotFoundError: node", "alarma": False}
    linea = aa.linea_historial(_out(falsas), cobertura_pct=100.0, gt_stale_dias=0)
    assert linea["falsas_pub_pct"] == {s: None for s in aa.SENSORS}
    assert linea["falsas_error"] is True


def test_main_escribe_la_linea_con_el_helper():
    """El helper no sirve si main() sigue armando el dict a mano: se exige la llamada, con frontera
    de palabra (A92), y que el armado viejo inline ya no exista."""
    src = Path(aa.__file__).read_text(encoding="utf-8")
    cuerpo = src[src.index("def main("):]
    assert re.search(r"(?<![A-Za-z0-9_])linea_historial\s*\(", cuerpo)
    assert "hist_line = {" not in cuerpo
