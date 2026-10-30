# -*- coding: utf-8 -*-
"""S169: la revisión diaria de la sombra «código MIROVA» juzga lo que escribió ESTA corrida, por sensor.

POR QUÉ (experiments/_s169/audit_patrones/f3/INFORME_F3.md P3-02 y P3-03, verificador VF3-01, en loop/activo).
La sombra corre cada día los últimos 8 días (scripts/ventana_sombra.py) y su JSON ya trae lo commiteado por las
corridas anteriores. La revisión contaba los records de toda la ventana, así que desde el segundo día una corrida
que no produjo nada (CMR caído, la vía descartando todo) salía verde con los records de ayer; un sensor entero podía
faltar mientras los otros dos sostenían el verde; y un record de K caído un día dejaba el job rojo los 8 días
siguientes, tapando cualquier falla nueva. Sobre esas noches se decide si la vía pasa a producción.

CÓMO SE PRUEBA. Cada caso arma en una carpeta temporal el JSON, el log y el JSON de cobertura que dejaría el job, y
corre la revisión con la LÍNEA DE COMANDOS QUE TRAE EL WORKFLOW (expresiones `${{ }}` reemplazadas por los valores
del caso). Así se prueba también el cableado: si el workflow no le pasara a la revisión la marca de inicio de la
corrida o la cobertura, los casos de corrida vacía saldrían verdes y la prueba quedaría en rojo (A118).

Las dos preguntas del instrumento: (1) si la revisión siguiera contando la ventana entera, los casos de corrida
vacía, de sensor faltante y de record de K viejo darían el resultado contrario (visto en rojo contra el código de
main cc3887290, INFORME.md de experiments/_s169/vigilancia_sombra/); (2) el control sano sale verde y el de
ERROR processing sale rojo, así que el instrumento puede dar los dos resultados.
"""
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "sombra-codigo-mirova.yml"
VOLCAN = "Lascar"
SENSORES = {"MODIS": "MODIS_AQUA", "VIIRS750": "VIIRS_NOAA20_750", "VIIRS375": "VIIRS_NOAA20"}
PLATAFORMAS = ["MODIS_TERRA", "MODIS_AQUA", "VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21",
               "VIIRS_SNPP_750", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750"]
CESE_SNPP = "2026-11-02T13:00:00Z"   # scripts/ceses_esperados.json


def rec(dia, sensor, sha, proc, hora="06:12", via=True):
    return {"datetime_utc": "2026-11-%02d %s" % (dia, hora), "sensor": sensor, "via_codigo_mirova": via,
            "processed_utc": proc, "regimen": {"perfil": "sombra_codigo_mirova", "codigo_sha": sha,
                                               "origen": "actions"}}


def de_la_corrida(dia, familias=("MODIS", "VIIRS750", "VIIRS375")):
    """Lo que escribe la corrida diaria del día `dia` (15:00 UTC): una pasada nocturna por sensor."""
    return [rec(dia, SENSORES[f], "sha%02d" % dia, "2026-11-%02dT15:20:%02dZ" % (dia, i))
            for i, f in enumerate(familias)]


def historial(desde, hasta, familias=("MODIS", "VIIRS750", "VIIRS375")):
    out = []
    for d in range(desde, hasta + 1):
        out += de_la_corrida(d, familias)
    return out


def cobertura(dia, fallas=0, sin_pasada=()):
    """JSON de --cobertura-json de run_pipeline (informar_cobertura): plataformas con gránulos, Suomi NPP retirada."""
    plat = {}
    for p in PLATAFORMAS:
        if "SNPP" in p:
            plat[p] = {"con_granulos": 0, "sin_granulos": 0, "retirada": 8, "cese_desde": CESE_SNPP}
        else:
            plat[p] = {"con_granulos": 8, "sin_granulos": 0, "retirada": 0, "cese_desde": None}
    incid = [{"tipo": "dia_parcial", "cuenta_estricto": True, "volcan": VOLCAN, "fecha": "2026-11-%02d" % dia,
              "plataforma": None, "motivo": "día en curso"}]
    for p in sin_pasada:
        plat[p]["sin_granulos"] += 1
        incid.append({"tipo": "sin_granulos", "cuenta_estricto": False, "volcan": VOLCAN,
                      "fecha": "2026-11-%02d" % dia, "plataforma": p, "motivo": "la búsqueda respondió sin gránulos"})
    fs = [{"volcan": None, "fecha": "2026-11-%02d" % dia, "plataforma": "VIIRS_NOAA20", "producto": "VIIRS_NOAA20_L1B",
           "etapa": "busqueda", "motivo": "SEARCH_CMR_TIMEOUT"} for _ in range(fallas)]
    return {"fallas": fs, "n": len(fs), "plataformas": plat, "retiradas": ["VIIRS_SNPP", "VIIRS_SNPP_750"],
            "sin_granulos": [], "incidencias": incid, "n_incidencias": len(incid)}


def comando_revisor(valores):
    """La línea de comandos de la revisión tal como la trae el workflow, con las expresiones reemplazadas."""
    d = yaml.safe_load(WF.read_text(encoding="utf-8"))
    paso = next(s for s in d["jobs"]["process"]["steps"] if "scripts/revisar_sombra.py" in s.get("run", ""))
    run = paso["run"].replace("\\\n", " ")
    lineas = [ln for ln in run.splitlines() if "revisar_sombra.py" in ln]
    assert len(lineas) == 1, lineas

    def sustituir(m):
        e = m.group(1).strip()
        assert e in valores, "el workflow pasa una expresión que la prueba no conoce: %s" % e
        return valores[e]

    args = shlex.split(re.sub(r"\$\{\{(.*?)\}\}", sustituir, lineas[0]))
    assert args[0] == "python" and args[1] == "scripts/revisar_sombra.py", args
    return [sys.executable, str(ROOT / args[1])] + args[2:]


def juzgar(tmp_path, dia, registros, log="", cob=None):
    """(código de salida, salida) de la revisión del día `dia` de noviembre a las 15:01 UTC."""
    (tmp_path / "data" / "sombra_codigo_mirova").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "sombra_codigo_mirova" / ("%s.json" % VOLCAN)).write_text(
        json.dumps({"volcano": VOLCAN, "records": registros}), encoding="utf-8")
    (tmp_path / "pipeline.log").write_text(log, encoding="utf-8")
    if cob is not None:
        (tmp_path / "cobertura.json").write_text(json.dumps(cob), encoding="utf-8")
    valores = {"matrix.volcano": VOLCAN,
               "steps.correr.outputs.ini": "2026-11-%02d" % max(3, dia - 7),
               "steps.correr.outputs.fin": "2026-11-%02d" % dia,
               "steps.correr.outputs.inicio": "2026-11-%02dT15:01:00Z" % dia,
               "github.sha": "sha%02d" % dia}
    p = subprocess.run(comando_revisor(valores), cwd=tmp_path, capture_output=True, text=True,
                       encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return p.returncode, p.stdout + p.stderr


# ---------------------------------------------------------------- controles

def test_control_corrida_sana_del_dia_2_sale_verde(tmp_path):
    rc, out = juzgar(tmp_path, 4, historial(3, 4), cob=cobertura(4))
    assert rc == 0, out


def test_control_error_processing_sale_rojo(tmp_path):
    rc, out = juzgar(tmp_path, 4, historial(3, 4), log="  ERROR processing VJ102IMG.x.nc: boom\n", cob=cobertura(4))
    assert rc != 0, out


def test_control_record_de_k_escrito_hoy_sale_rojo(tmp_path):
    k = rec(7, "MODIS_TERRA", "sha07", "2026-11-07T15:30:00Z", hora="03:40", via="geo_distinta")
    rc, out = juzgar(tmp_path, 7, historial(3, 7) + [k], cob=cobertura(7))
    assert rc != 0 and "geo_distinta" in out, out


# ---------------------------------------------------------------- P3-02: corrida vacía

def test_corrida_vacia_del_dia_2_con_cmr_caido_sale_roja(tmp_path):
    rc, out = juzgar(tmp_path, 4, historial(3, 3),
                     log="Cobertura INCOMPLETA: 30 búsquedas o descargas fallidas.\n", cob=cobertura(4, fallas=30))
    assert rc != 0, out


def test_corrida_vacia_del_dia_2_sin_fallas_de_busqueda_sale_roja(tmp_path):
    """NASA entregó gránulos y no quedó ningún record nuevo: la vía los descartó o el store no escribió."""
    rc, out = juzgar(tmp_path, 4, historial(3, 3), cob=cobertura(4))
    assert rc != 0, out


def test_corrida_vacia_del_dia_8_sale_roja(tmp_path):
    rc, out = juzgar(tmp_path, 10, historial(3, 9), cob=cobertura(10, fallas=30))
    assert rc != 0, out


def test_sin_json_de_cobertura_sale_roja(tmp_path):
    """Sin cobertura no se sabe qué se buscó: no se puede decir «no hubo pasada»."""
    rc, out = juzgar(tmp_path, 4, historial(3, 4), cob=None)
    assert rc != 0, out


def test_record_con_otro_codigo_no_cuenta_como_de_esta_corrida(tmp_path):
    ajeno = [dict(r, regimen=dict(r["regimen"], codigo_sha="sha03")) for r in de_la_corrida(4)]
    rc, out = juzgar(tmp_path, 4, historial(3, 3) + ajeno, cob=cobertura(4))
    assert rc != 0, out


# ---------------------------------------------------------------- P3-03: por sensor

def test_falta_un_sensor_entero_sale_rojo(tmp_path):
    rc, out = juzgar(tmp_path, 5, historial(3, 5, familias=("VIIRS750", "VIIRS375")), cob=cobertura(5))
    assert rc != 0 and "MODIS" in out, out


def test_un_sensor_que_esta_corrida_no_produjo_sale_rojo(tmp_path):
    regs = historial(3, 4) + de_la_corrida(5, familias=("MODIS", "VIIRS375"))
    rc, out = juzgar(tmp_path, 5, regs, cob=cobertura(5))
    assert rc != 0 and "VIIRS750" in out, out


def test_sin_pasada_legitima_se_dice_por_escrito_y_sale_verde(tmp_path):
    """La búsqueda de las dos plataformas vivas de VIIRS 750 respondió vacía hoy (Suomi NPP cesó): miró y no hubo."""
    regs = historial(3, 4) + de_la_corrida(5, familias=("MODIS", "VIIRS375"))
    rc, out = juzgar(tmp_path, 5, regs, cob=cobertura(5, sin_pasada=("VIIRS_NOAA20_750", "VIIRS_NOAA21_750")))
    assert rc == 0, out
    linea = [ln for ln in out.splitlines() if "VIIRS750" in ln]
    assert linea and any("no hubo pasada" in ln for ln in linea), out


def test_sin_pasada_de_una_sola_plataforma_no_alcanza(tmp_path):
    """NOAA-21 respondió vacía pero NOAA-20 sí trajo gránulos: que no haya record de VIIRS 750 es una falla."""
    regs = historial(3, 4) + de_la_corrida(5, familias=("MODIS", "VIIRS375"))
    rc, out = juzgar(tmp_path, 5, regs, cob=cobertura(5, sin_pasada=("VIIRS_NOAA21_750",)))
    assert rc != 0 and "VIIRS750" in out, out


# ---------------------------------------------------------------- VF3-01: rojo arrastrado

def test_record_de_k_viejo_no_enrojece_la_corrida_de_hoy(tmp_path):
    k = rec(5, "MODIS_TERRA", "sha05", "2026-11-05T15:30:00Z", hora="03:40", via="geo_distinta")
    rc, out = juzgar(tmp_path, 7, historial(3, 7) + [k], cob=cobertura(7))
    assert rc == 0, out


# ---------------------------------------------------------------- P3-04, parte del workflow

def _pasos():
    return yaml.safe_load(WF.read_text(encoding="utf-8"))["jobs"]["process"]["steps"]


def test_el_workflow_pide_cobertura_y_anota_el_inicio_antes_de_correr():
    correr = next(s for s in _pasos() if s.get("id") == "correr")["run"]
    i_run = correr.index("scripts/run_pipeline.py")
    assert "--cobertura-json cobertura.json" in correr[i_run:], "run_pipeline sin --cobertura-json"
    m = re.search(r'echo "inicio=', correr)
    assert m and m.start() < i_run, "la marca de inicio de la corrida tiene que quedar antes de correr"


def test_el_workflow_sube_log_y_cobertura_como_artefacto_aunque_falle():
    pasos = _pasos()
    i_run = next(i for i, s in enumerate(pasos) if s.get("id") == "correr")
    subir = [(i, s) for i, s in enumerate(pasos) if str(s.get("uses", "")).startswith("actions/upload-artifact@")]
    assert len(subir) == 1, subir
    i, s = subir[0]
    assert i > i_run
    assert s["if"].startswith("always()") and "steps.correr.outputs.corrio == 'true'" in s["if"]
    rutas = s["with"]["path"].split()
    assert "pipeline.log" in rutas and "cobertura.json" in rutas
    assert "matrix.volcano" in s["with"]["name"] and "github.run_attempt" in s["with"]["name"]
