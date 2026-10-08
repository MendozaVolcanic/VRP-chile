# -*- coding: utf-8 -*-
"""S150 (auditoria S150, D-02, verificado). La auditoria semanal confundio un apagon con una falla de
deteccion: el 2026-10-05 abrio #757 ("recall VIIRS 375 bajo la banda") cuando 11 de sus 14 fallos eran
noches del apagon del NRT sin ningun record nuestro; contando solo noches con dato, el recall era 98,4 %.

Tres defectos, cada uno con su caso:
  1. el denominador del recall contaba noches con alerta de MIROVA en que no teniamos NINGUN record
     (no miramos != no vimos);
  2. la guarda de cobertura contaba dias con DETECCION en el crater, no dias con DATOS, y no miraba la cola
     de la ventana: diez dias sin datos al final dejan 83,6 %, sobre el umbral de 80 %;
  3. el veredicto DEGRADADO no abria issue (eso vive en .github/workflows/audit-weekly.yml).

Las dos preguntas del instrumento: si la funcion siguiera contando las noches sin datos, o ignorara la
cola, test_noche_sin_datos_no_entra_al_denominador y test_apagon_al_final_avisa fallan.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.auto_audit_weekly import cobertura_de_ventana, recall_por_sensor  # noqa: E402

HOY = date(2026, 10, 5)
WIN = ((HOY - timedelta(days=60)).isoformat(), HOY.isoformat())


def dias(desde, hasta):
    d, out = desde, set()
    while d <= hasta:
        out.add(d.isoformat()); d += timedelta(days=1)
    return out


def test_cobertura_completa_no_avisa():
    c = cobertura_de_ventana(dias(HOY - timedelta(days=60), HOY), WIN, HOY)
    assert c["avisos"] == [] and c["cobertura_propia_pct"] == 100.0


def test_apagon_al_final_avisa():
    """El caso real: datos hasta el 2026-10-02, auditoria el 2026-10-05 (y la variante de 10 dias)."""
    for corte in (3, 10):
        c = cobertura_de_ventana(dias(HOY - timedelta(days=60), HOY - timedelta(days=corte)), WIN, HOY)
        assert c["cola_sin_datos_dias"] == corte
        assert any("sin datos" in a for a in c["avisos"]), c


def test_hoy_sin_datos_todavia_no_avisa():
    """El NRT procesa con retraso: que hoy no tenga records todavia no es un apagon."""
    c = cobertura_de_ventana(dias(HOY - timedelta(days=60), HOY - timedelta(days=1)), WIN, HOY)
    assert c["avisos"] == []


def test_hueco_en_medio_no_avisa_por_cola():
    d = dias(HOY - timedelta(days=60), HOY) - dias(HOY - timedelta(days=40), HOY - timedelta(days=31))
    c = cobertura_de_ventana(d, WIN, HOY)
    assert c["cola_sin_datos_dias"] == 0 and c["avisos"] == []


def test_noche_sin_datos_no_entra_al_denominador():
    mir = {("Lascar", "VIIRS375", "2026-10-03"): 0.5, ("Lascar", "VIIRS375", "2026-09-30"): 0.4,
           ("Villarrica", "VIIRS375", "2026-09-30"): 0.2}
    vistos = {("Lascar", "VIIRS375", "2026-09-30"), ("Villarrica", "VIIRS375", "2026-09-30")}
    ours = {("Lascar", "VIIRS375", "2026-09-30"): {"crater": [0.3], "dash": [0.3], "npix": [1]}}
    r = recall_por_sensor(mir, vistos, ours, ["VIIRS375"], {"Lascar", "Villarrica"})["VIIRS375"]
    assert r["n_noches"] == 2 and r["noches_sin_datos"] == 1
    assert r["recall_crater_pct"] == 50.0


def test_el_workflow_abre_issue_tambien_si_degradado():
    wf = (ROOT / ".github" / "workflows" / "audit-weekly.yml").read_text(encoding="utf-8")
    assert '"DEGRADADO"' in wf
