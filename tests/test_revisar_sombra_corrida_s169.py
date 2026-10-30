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
main 161536698, INFORME.md de experiments/_s169/vigilancia_sombra/); (2) el control sano sale verde y el de
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


def cobertura(dia, fallas=0, sin_pasada=(), dia_fallas=None, dia_sin_pasada=None):
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
                      "fecha": "2026-11-%02d" % (dia_sin_pasada or dia), "plataforma": p,
                      "motivo": "la búsqueda respondió sin gránulos"})
    fs = [{"volcan": None, "fecha": "2026-11-%02d" % (dia_fallas or dia), "plataforma": "VIIRS_NOAA20", "producto": "VIIRS_NOAA20_L1B",
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


def juzgar(tmp_path, dia, registros, log="", cob=None, ini=None, inicio=None, json_crudo=None, cob_cruda=None):
    """(código de salida, salida) de la revisión del día `dia` de noviembre a las 15:01 UTC. El resumen del job
    (GITHUB_STEP_SUMMARY) va siempre a `tmp_path/resumen.md`, también en CI, para no escribir en el del job real.
    `json_crudo` y `cob_cruda` escriben el texto tal cual (para probar archivos corruptos)."""
    (tmp_path / "data" / "sombra_codigo_mirova").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "sombra_codigo_mirova" / ("%s.json" % VOLCAN)).write_text(
        json_crudo if json_crudo is not None else json.dumps({"volcano": VOLCAN, "records": registros}),
        encoding="utf-8")
    (tmp_path / "pipeline.log").write_text(log, encoding="utf-8")
    if cob_cruda is not None:
        (tmp_path / "cobertura.json").write_text(cob_cruda, encoding="utf-8")
    elif cob is not None:
        (tmp_path / "cobertura.json").write_text(json.dumps(cob), encoding="utf-8")
    valores = {"matrix.volcano": VOLCAN,
               "steps.correr.outputs.ini": ini or "2026-11-%02d" % max(3, dia - 7),
               "steps.correr.outputs.fin": "2026-11-%02d" % dia,
               "steps.correr.outputs.inicio": "2026-11-%02dT15:01:00Z" % dia if inicio is None else inicio,
               "github.sha": "sha%02d" % dia}
    p = subprocess.run(comando_revisor(valores), cwd=tmp_path, capture_output=True, text=True,
                       encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8",
                                                 GITHUB_STEP_SUMMARY=str(tmp_path / "resumen.md")))
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


# ================================================================ Ronda 2 (verificador de 16d9e894d)
# D:/vrp-trabajo/temporales/s169_ver_vigilancia/INFORME_VERIFICACION.md; decisiones de la coordinadora en el
# INFORME.md de experiments/_s169/vigilancia_sombra/, sección «Ronda 2».

def _reescritos_hoy(dias, hoy):
    """Records de días viejos que la corrida de `hoy` reescribió (reemplazo NRT a estándar, pipeline/store.py)."""
    out = []
    for d in dias:
        for i, f in enumerate(SENSORES):
            out.append(rec(d, SENSORES[f], "sha%02d" % hoy, "2026-11-%02dT15:30:%02dZ" % (hoy, i)))
    return out


def test_vv01_reemplazos_de_dias_viejos_no_cumplen_el_control_por_sensor(tmp_path):
    """Hoy (día 6) no salió nada del 5 ni del 6; sólo se reescribieron pasadas del 3 y el 4: es falla."""
    regs = historial(5, 5) + _reescritos_hoy((3, 4), 6)
    rc, out = juzgar(tmp_path, 6, regs, cob=cobertura(6))
    assert rc != 0 and "MODIS" in out and "VIIRS750" in out and "VIIRS375" in out, out


def test_vv01_un_record_de_ayer_escrito_hoy_no_tapa_el_dia_de_hoy(tmp_path):
    """Ronda 3 (control por día): una pasada de ayer escrita hoy sirve para ayer, no para hoy. Hoy sin records y sin
    prueba de que no hubo pasada es falla. (En la ronda 2 esta prueba exigía verde: la víspera tapaba el día.)"""
    regs = historial(3, 4) + _reescritos_hoy((5,), 6)
    rc, out = juzgar(tmp_path, 6, regs, cob=cobertura(6))
    assert rc != 0 and "2026-11-06" in out, out
    rc, out = juzgar(tmp_path, 6, regs + de_la_corrida(6), cob=cobertura(6))
    assert rc == 0, out


def test_vv02_catalogo_vacio_en_los_tres_sensores_es_falla(tmp_path):
    """Como el 2026-10-18 (R2-13): CMR responde vacío para todo. Que ningún sensor pase de noche no es físico."""
    vivas = [p for p in PLATAFORMAS if "SNPP" not in p]
    rc, out = juzgar(tmp_path, 5, historial(3, 4), cob=cobertura(5, sin_pasada=vivas))
    assert rc != 0 and "catálogo" in out, out


def test_vv02_viirs_750_y_375_vacios_a_la_vez_es_falla(tmp_path):
    vivas = [p for p in PLATAFORMAS if "SNPP" not in p and p.startswith("VIIRS")]
    regs = historial(3, 4) + de_la_corrida(5, familias=("MODIS",))
    rc, out = juzgar(tmp_path, 5, regs, cob=cobertura(5, sin_pasada=vivas))
    assert rc != 0 and "catálogo" in out, out


def test_vv03_falla_de_busqueda_de_un_dia_viejo_es_nota(tmp_path):
    """El día 3 ya lo cubrió la corrida del 3; si no, el control por sensor de ese día lo vio."""
    rc, out = juzgar(tmp_path, 5, historial(3, 5), cob=cobertura(5, fallas=4, dia_fallas=3))
    assert rc == 0, out
    assert any(ln.strip().startswith("NOTA") and "2026-11-03" in ln for ln in out.splitlines()), out


def test_g_falla_de_busqueda_del_ultimo_dia_es_falla_aunque_el_log_no_lo_diga(tmp_path):
    rc, out = juzgar(tmp_path, 5, historial(3, 5), log="", cob=cobertura(5, fallas=1))
    assert rc != 0 and "búsquedas o descargas fallidas" in out, out


def test_e_sin_granulos_de_otro_dia_no_justifica_el_de_hoy(tmp_path):
    regs = historial(3, 4) + de_la_corrida(5, familias=("MODIS", "VIIRS375"))
    rc, out = juzgar(tmp_path, 5, regs, cob=cobertura(5, sin_pasada=("VIIRS_NOAA20_750", "VIIRS_NOAA21_750"),
                                                      dia_sin_pasada=4))
    assert rc != 0 and "VIIRS750" in out, out


def test_a_record_de_ayer_con_el_mismo_sha_no_cuenta(tmp_path):
    """Dos corridas sobre el mismo sha (main sin commits en 24 h, o un relanzamiento): sólo las separa la hora.
    Ronda 3: la ventana está completa (el control por día pasa) y sólo el control «esta corrida escribió algo» la ve:
    la corrida que se revisa empezó a las 18:00 y todo lo que hay se escribió antes, con el mismo sha."""
    regs = [dict(r, regimen=dict(r["regimen"], codigo_sha="sha04")) for r in historial(3, 4)]
    rc, out = juzgar(tmp_path, 4, regs, cob=cobertura(4), inicio="2026-11-04T18:00:00Z")
    assert rc != 0 and "ningún record" in out, out
    # control: con la hora de verdad, las mismas filas son de esta corrida y sale verde
    rc, out = juzgar(tmp_path, 4, regs, cob=cobertura(4), inicio="2026-11-04T15:01:00Z")
    assert rc == 0, out


def test_vv05_los_k_caidos_quedan_a_la_vista_en_el_resumen_del_job(tmp_path):
    """El record de K no se reemplaza (pipeline/store.py sin overwrite): la cuenta acumulada se escribe cada día."""
    k = rec(5, "MODIS_TERRA", "sha05", "2026-11-05T15:30:00Z", hora="03:40", via="geo_distinta")
    rc, out = juzgar(tmp_path, 7, historial(3, 7) + [k], cob=cobertura(7))
    assert rc == 0, out
    assert "K caídos en la ventana: 1" in out and "geo_distinta" in out, out
    resumen = (tmp_path / "resumen.md").read_text(encoding="utf-8")
    assert "K caídos en la ventana: 1" in resumen, resumen


def test_vv05_la_linea_de_k_esta_aunque_sea_cero(tmp_path):
    rc, out = juzgar(tmp_path, 4, historial(3, 4), cob=cobertura(4))
    assert rc == 0 and "K caídos en la ventana: 0" in out, out
    assert "K caídos en la ventana: 0" in (tmp_path / "resumen.md").read_text(encoding="utf-8")


def test_p_el_inicio_anotado_es_la_hora_de_la_corrida_en_el_formato_del_store():
    """Una constante o un formato distinto del de processed_utc rompen la comparación sin dar error."""
    correr = next(s for s in _pasos() if s.get("id") == "correr")["run"]
    m = re.search(r"^\s*INICIO=\$\(date -u \+(%Y-%m-%dT%H:%M:%SZ)\)\s*$", correr, re.M)
    assert m, "INICIO tiene que salir de `date -u` en el momento de correr"
    assert 'echo "inicio=$INICIO"' in correr
    assert correr.index("INICIO=$(date") < correr.index("scripts/run_pipeline.py")
    store = (ROOT / "pipeline" / "store.py").read_text(encoding="utf-8")
    assert 'record["processed_utc"] = datetime.now(timezone.utc).strftime("%s")' % m.group(1) in store


def test_vv07_el_log_se_tacha_antes_de_subirlo(tmp_path):
    pasos = _pasos()
    i_subir = next(i for i, s in enumerate(pasos) if str(s.get("uses", "")).startswith("actions/upload-artifact@"))
    tachar = [(i, s) for i, s in enumerate(pasos) if "scripts/tachar_secreto_log.py" in s.get("run", "")]
    assert len(tachar) == 1, "falta el paso que tacha el token en el log antes de subirlo"
    i, s = tachar[0]
    assert i < i_subir and s["if"] == "always() && steps.correr.outputs.corrio == 'true'"
    assert s["env"]["EARTHDATA_TOKEN"] == "${{ secrets.EARTHDATA_TOKEN }}"
    assert "pipeline.log" in s["run"] and "cobertura.json" in s["run"]
    # y el script hace lo que dice
    token = "eyJ0eXAiOiJKV1Qi.eyJzdWIiOiJ4In0.firma-falsa_123"
    (tmp_path / "pipeline.log").write_text("ok\nAuthorization: Bearer %s\n" % token, encoding="utf-8")
    (tmp_path / "cobertura.json").write_text('{"motivo": "%s"}' % token, encoding="utf-8")
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "tachar_secreto_log.py"), "pipeline.log",
                        "cobertura.json", "no_existe.txt"], cwd=tmp_path, capture_output=True, text=True,
                       encoding="utf-8", env=dict(os.environ, EARTHDATA_TOKEN=token, PYTHONIOENCODING="utf-8"))
    assert p.returncode == 0, p.stdout + p.stderr
    for f in ("pipeline.log", "cobertura.json"):
        txt = (tmp_path / f).read_text(encoding="utf-8")
        assert token not in txt and "***" in txt, txt
    assert token not in p.stdout + p.stderr


# ================================================================ Ronda 3 (verificador de f743d7b8f)
# D:/vrp-trabajo/temporales/s169_ver_vigilancia_r2/INFORME_VERIFICACION_R2.md; decisión de la coordinadora: además de
# «esta corrida escribió algo», el CONTENIDO de la ventana se juzga día por día y sensor por sensor.

def _sin(regs, dia, familia=None):
    """Los records sin las pasadas del día `dia` (de un solo sensor si se da `familia`)."""
    return [r for r in regs if not (r["datetime_utc"].startswith("2026-11-%02d" % dia)
                                    and (familia is None or r["sensor"] == SENSORES[familia]))]


def test_r3_un_dia_viejo_perdido_sigue_rojo_mientras_este_en_la_ventana(tmp_path):
    """VR2-01: el día 4 se perdió entero. En la corrida del 5 y en la del 9 sigue en rojo, con la fecha en el texto."""
    for hoy in (5, 9):
        regs = _sin(historial(3, hoy), 4)
        rc, out = juzgar(tmp_path, hoy, regs, cob=cobertura(hoy, fallas=2, dia_fallas=4))
        assert rc != 0 and "2026-11-04" in out, (hoy, out)
        rc, out = juzgar(tmp_path, hoy, regs, cob=cobertura(hoy))
        assert rc != 0 and "2026-11-04" in out, (hoy, out)


def test_r3_un_dia_viejo_sin_pasada_probada_es_nota(tmp_path):
    """Si la cobertura de esta corrida prueba que el día 4 no hubo gránulos de VIIRS 750, el hueco está explicado."""
    regs = _sin(historial(3, 5), 4, "VIIRS750")
    rc, out = juzgar(tmp_path, 5, regs, cob=cobertura(5, sin_pasada=("VIIRS_NOAA20_750", "VIIRS_NOAA21_750"),
                                                      dia_sin_pasada=4))
    assert rc == 0, out
    assert any(ln.strip().startswith("NOTA") and "VIIRS750" in ln and "2026-11-04" in ln for ln in out.splitlines()), out


def test_r3_el_catalogo_vacio_de_hoy_no_lo_tapa_la_vispera(tmp_path):
    """VR2-02: hoy CMR respondió vacío para todo, y la víspera se reescribió hoy (reemplazo NRT a estándar)."""
    vivas = [p for p in PLATAFORMAS if "SNPP" not in p]
    regs = historial(3, 3) + _reescritos_hoy((4,), 5)
    rc, out = juzgar(tmp_path, 5, regs, cob=cobertura(5, sin_pasada=vivas))
    assert rc != 0 and "catálogo" in out, out


def test_r3_los_dias_antes_de_la_fecha_minima_no_se_juzgan(tmp_path):
    """Un despacho medir puede pedir una ventana que empieza antes del 2026-11-03: esos días no son de la sombra."""
    rc, out = juzgar(tmp_path, 3, historial(3, 3), cob=cobertura(3), ini="2026-10-29")
    assert rc == 0, out
    assert "2026-10-3" not in out and "2026-11-01" not in out, out


def test_r3_cobertura_de_otro_dia_no_prueba_la_ausencia(tmp_path):
    """La prueba de «no hubo pasada» tiene que ser del mismo día que falta, no de otro."""
    regs = _sin(historial(3, 5), 4, "VIIRS750")
    rc, out = juzgar(tmp_path, 5, regs, cob=cobertura(5, sin_pasada=("VIIRS_NOAA20_750", "VIIRS_NOAA21_750"),
                                                      dia_sin_pasada=3))
    assert rc != 0 and "2026-11-04" in out, out


def test_r3_la_fecha_minima_es_la_de_ventana_sombra():
    sys.path.insert(0, str(ROOT / "scripts"))
    import revisar_sombra
    import ventana_sombra
    assert revisar_sombra.FECHA_MINIMA == ventana_sombra.FECHA_MINIMA.isoformat()


def _sin_traceback(rc, out):
    assert rc != 0, out
    assert "Traceback" not in out, out
    assert "K caídos en la ventana" in out, out


def test_vr2_04_json_corrupto_da_falla_con_mensaje_y_linea_de_k(tmp_path):
    rc, out = juzgar(tmp_path, 4, [], cob=cobertura(4), json_crudo="{ esto no es json")
    _sin_traceback(rc, out)
    assert "JSON de la sombra" in out


def test_vr2_04_cobertura_corrupta_da_falla_con_mensaje_y_linea_de_k(tmp_path):
    rc, out = juzgar(tmp_path, 4, historial(3, 4), cob_cruda="[1, 2,")
    _sin_traceback(rc, out)
    assert "cobertura" in out


def test_vr2_04_desde_utc_vacio_da_falla_con_mensaje_y_linea_de_k(tmp_path):
    rc, out = juzgar(tmp_path, 4, historial(3, 4), cob=cobertura(4), inicio="")
    _sin_traceback(rc, out)
    assert "--desde-utc" in out


def test_vr2_05_una_falla_de_cobertura_sin_fecha_es_falla(tmp_path):
    cob = cobertura(4, fallas=1)
    cob["fallas"][0]["fecha"] = None
    rc, out = juzgar(tmp_path, 4, historial(3, 4), cob=cob)
    assert rc != 0 and "búsquedas o descargas fallidas" in out, out


def _tachar(tmp_path, token_env, archivos, antes=()):
    for nombre, txt in archivos.items():
        (tmp_path / nombre).write_text(txt, encoding="utf-8")
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "tachar_secreto_log.py")] + list(antes)
                          + list(archivos),
                          cwd=tmp_path, capture_output=True, text=True, encoding="utf-8",
                          env=dict(os.environ, EARTHDATA_TOKEN=token_env, PYTHONIOENCODING="utf-8"))


def test_vr2_03_tacha_las_variantes_url_y_json_del_token(tmp_path):
    from urllib.parse import quote, quote_plus
    token = "abc/def+ghi=jkl.mn"
    variantes = {"url.log": "x?t=%s\n" % quote(token, safe=""), "plus.log": "t=%s\n" % quote_plus(token),
                 "json.log": '{"t": "%s"}\n' % token.replace("/", "\\/"), "lit.log": token + "\n"}
    p = _tachar(tmp_path, token, variantes)
    assert p.returncode == 0, p.stdout + p.stderr
    for nombre in variantes:
        txt = (tmp_path / nombre).read_text(encoding="utf-8")
        assert "***" in txt, (nombre, txt)
        for v in (token, quote(token, safe=""), quote_plus(token), token.replace("/", "\\/")):
            assert v not in txt, (nombre, v, txt)


def test_vr2_03_el_tachado_falla_cerrado(tmp_path):
    """Si un archivo no se puede tachar, el script sale distinto de 0, sigue con los demás y no imprime el token."""
    token = "eyJ0eXAi.secreto.firma"
    (tmp_path / "pipeline.log").mkdir()                         # un directorio no se puede leer como texto
    p = _tachar(tmp_path, token, {"cobertura.json": '{"m": "%s"}' % token}, antes=["pipeline.log"])
    assert p.returncode != 0, p.stdout + p.stderr
    assert token not in (tmp_path / "cobertura.json").read_text(encoding="utf-8")
    assert token not in p.stdout + p.stderr


def test_vr2_03_el_artefacto_solo_sube_si_el_tachado_salio_bien():
    pasos = _pasos()
    tachar = next(s for s in pasos if "scripts/tachar_secreto_log.py" in s.get("run", ""))
    subir = next(s for s in pasos if str(s.get("uses", "")).startswith("actions/upload-artifact@"))
    assert tachar.get("id") == "tachar" and not tachar.get("continue-on-error"), tachar
    assert "steps.tachar.outcome == 'success'" in subir["if"], subir["if"]


def test_vr2_05_el_token_se_toma_sin_espacios_ni_salto_de_linea(tmp_path):
    token = "eyJ0eXAi.secreto.firma"
    p = _tachar(tmp_path, token + "\n", {"pipeline.log": "Bearer %s\n" % token})
    assert p.returncode == 0 and token not in (tmp_path / "pipeline.log").read_text(encoding="utf-8")


def test_vr2_05_con_token_vacio_no_toca_nada(tmp_path):
    for vacio in ("", "   "):
        p = _tachar(tmp_path, vacio, {"pipeline.log": "linea normal\n"})
        assert p.returncode == 0, p.stdout + p.stderr
        assert (tmp_path / "pipeline.log").read_text(encoding="utf-8") == "linea normal\n"
