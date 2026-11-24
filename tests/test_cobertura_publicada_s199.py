# -*- coding: utf-8 -*-
"""S199 (auditoría externa con Codex, ronda 2, F6-112): pasadas no medidas, escritas en data/ y mostradas en el tablero.

POR QUÉ. Una pasada que el sistema no pudo medir (búsqueda en CMR caída, descarga o lectura fallida) no dejaba ninguna
fila en data/: una pasada no medida y una noche sin pasada se veían igual, y el tablero las mostraba como «sin
anomalía». Ahora el NRT y el barrido semanal escriben data/cobertura/<volcán>.json (scripts/cobertura_publicada.py) y
las tres vistas lo leen (frontend/cobertura.js).

QUÉ FIJA:
(1) La corrida deja en su JSON de cobertura cada búsqueda hecha (ok o fallida) y el minuto de la pasada que no se bajó
    (pipeline/fetch.py, scripts/run_pipeline.py), con su control: un día limpio deja búsquedas ok y ninguna falla.
(2) cobertura_publicada.actualizar: búsqueda fallida y pasada sin bajar quedan; una corrida sin fallas las borra; si fue
    después del cierre del día, el día queda cerrado y una falla posterior no lo reabre; antes del cierre, sí; un record
    que aparece borra su pasada; lo de otro volcán, la búsqueda vacía, el día parcial y sin_record no cuentan; 30 días.
(3) El CLI sólo reescribe el archivo cuando cambia lo que dice (no un commit por corrida).
(4) De punta a punta: run_pipeline con CMR caído, luego con CMR sano, sobre el mismo archivo.
(5) nrt.yml y barrido-huecos.yml corren el paso antes del commit y suben data/cobertura/<volcán>.json.
(6) frontend/cobertura.js (con node): filtra por intervalo y plataforma, distingue día sin búsqueda de pasada sin medir;
    las tres vistas cargan el módulo y lo pintan.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código mal? Cada prueba que marca tiene su control que no debe
marcar (día limpio, observación ok, record de otra plataforma). (2) ¿Y si la carga muriera? Las pruebas de node exigen
returncode 0 y cargan el módulo con require; las de run_pipeline leen el JSON que escribe la corrida, que no existe si
la corrida no llega al final.
"""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("run_pipeline_s199", ROOT / "scripts" / "run_pipeline.py")
rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rp)
fetch = rp.fetch

_spec2 = importlib.util.spec_from_file_location("cobertura_publicada_s199", ROOT / "scripts" / "cobertura_publicada.py")
cp = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(cp)

PASADO = "2026-10-18"
UTC = timezone.utc


def _red_prohibida(*a, **k):
    raise AssertionError("una prueba no puede tocar NASA (ni auth con el netrc local, A71)")


def _gran(t):
    # Nombre con el tiempo de la pasada, como los L1B reales (.A<año><día>.<hhmm>.)
    d = datetime.strptime(t[:16], "%Y-%m-%dT%H:%M")
    ur = "MOD021KM.A%04d%03d.%02d%02d.061.falso.hdf" % (d.year, d.timetuple().tm_yday, d.hour, d.minute)
    return {"umm": {"TemporalExtent": {"RangeDateTime": {"BeginningDateTime": t, "EndingDateTime": t}},
                    "GranuleUR": ur}}


def _buscador(dia):
    return lambda **kw: [_gran(dia + "T05:35:00Z")]


@pytest.fixture(autouse=True)
def _limpio(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch, "auth", lambda: None)
    monkeypatch.setattr(fetch.earthaccess, "login", _red_prohibida)
    monkeypatch.setattr(fetch.earthaccess, "search_data", _red_prohibida)
    monkeypatch.setattr(fetch.earthaccess, "download", _red_prohibida)
    monkeypatch.setattr(fetch, "_diag", lambda *a, **k: None)
    monkeypatch.setattr(fetch, "_filter_nighttime_granules", lambda g, lat, lon, **k: g)
    monkeypatch.setattr(fetch, "download_granules", lambda gs, d: [Path(d) / ("falso_%d" % i) for i in range(len(gs))])
    monkeypatch.setattr(rp, "TMP_DIR", tmp_path / "tmp")
    monkeypatch.setenv("VRP_BUSQUEDA_VENTANA", "0")
    for v in ("VRP_VENTANA_BUSQUEDA", "VRP_CACHE_BUSQUEDA_DIR", "VRP_CONSERVAR_GRANULOS",
              "GITHUB_STEP_SUMMARY", "GITHUB_ACTIONS"):
        monkeypatch.delenv(v, raising=False)
    fetch.reiniciar_ventana()
    fetch.limpiar_fallas()
    yield
    fetch.reiniciar_ventana()
    fetch.limpiar_fallas()


def _correr(monkeypatch, capsys, tmp_path, fecha, buscador, nombre="cob.json"):
    monkeypatch.setattr(fetch.earthaccess, "search_data", buscador)
    ruta = tmp_path / nombre
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "--volcano", "Lascar", "--date", fecha,
                                      "--cobertura-json", str(ruta)])
    with pytest.raises(SystemExit):
        rp.main()
    capsys.readouterr()
    return ruta, json.loads(ruta.read_text(encoding="utf-8"))


def _caido(**kw):
    from requests.exceptions import ReadTimeout
    raise ReadTimeout("simulado")


# ── (1) la corrida dice qué buscó y qué pasada no bajó ─────────────────────────────────────────────────────────────

def test_control_dia_limpio_deja_busquedas_ok_y_ninguna_falla(monkeypatch, capsys, tmp_path):
    _, cob = _correr(monkeypatch, capsys, tmp_path, PASADO, _buscador(PASADO))
    assert cob["fallas"] == []
    assert cob["busquedas"], "la corrida no dejó sus búsquedas en la cobertura"
    assert all(b["ok"] and b["volcan"] == "Lascar" and b["fecha"] == PASADO for b in cob["busquedas"])
    assert {"MODIS_TERRA", "MODIS_AQUA"} <= {b["plataforma"] for b in cob["busquedas"]}
    assert cob.get("generado_utc")


def test_busqueda_caida_queda_como_busqueda_no_ok(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(fetch, "ENABLE_CMR_SEARCH_BREAKER", True)
    _, cob = _correr(monkeypatch, capsys, tmp_path, PASADO, _caido)
    assert cob["fallas"]
    assert cob["busquedas"] and not any(b["ok"] for b in cob["busquedas"])


def test_descarga_fallida_lleva_el_minuto_de_la_pasada(monkeypatch, capsys, tmp_path):
    def baja_mal(gs, d):
        raise OSError("corte simulado")
    monkeypatch.setattr(fetch, "download_granules", baja_mal)
    _, cob = _correr(monkeypatch, capsys, tmp_path, PASADO, _buscador(PASADO))
    descargas = [f for f in cob["fallas"] if f["etapa"] == "descarga"]
    assert descargas and all(f.get("pasada") == PASADO + " 05:35" for f in descargas)
    assert all(b["ok"] for b in cob["busquedas"])     # la búsqueda sí respondió


def test_minuto_de_archivo_lee_el_nombre_del_l1b():
    assert rp._minuto_de_archivo(Path("VJ102MOD.A2026328.0612.021.2026328.nc")) == "2026-11-24 06:12"
    assert rp._minuto_de_archivo(Path("sin_tiempo.hdf")) is None


# ── (2) cobertura_publicada.actualizar ───────────────────────────────────────────────────────────────────────────

def _cob(busquedas=(), fallas=(), incidencias=(), generado="2026-11-24T14:40:00Z"):
    return {"busquedas": list(busquedas), "fallas": list(fallas), "incidencias": list(incidencias),
            "generado_utc": generado}


def _b(fecha, plat, ok, utc, volcan="Lascar"):
    return {"volcan": volcan, "fecha": fecha, "plataforma": plat, "ok": ok, "utc": utc}


def _fb(fecha, plat, volcan="Lascar"):
    return {"volcan": volcan, "fecha": fecha, "plataforma": plat, "etapa": "busqueda", "producto": "X", "motivo": "m"}


def _fd(fecha, plat, minuto, volcan="Lascar"):
    return {"volcan": volcan, "fecha": fecha, "plataforma": plat, "etapa": "descarga", "producto": "X", "motivo": "m",
            "pasada": minuto}


AHORA = datetime(2026, 11, 24, 15, 0, tzinfo=UTC)


def _act(estado, cob, records=None, ahora=AHORA):
    return cp.actualizar(estado, cob, "Lascar", ahora, records=records)


def test_busqueda_fallida_queda_y_control_ok_no():
    e = _act(None, _cob([_b("2026-11-24", "MODIS_AQUA", False, "2026-11-24T14:35:00Z"),
                         _b("2026-11-24", "MODIS_TERRA", True, "2026-11-24T14:35:00Z")],
                        [_fb("2026-11-24", "MODIS_AQUA")]))
    assert [(i["fecha"], i["plataforma"], i["motivo"]) for i in e["no_medidas"]] == \
        [("2026-11-24", "MODIS_AQUA", "busqueda_fallida")]
    assert e["dias_cerrados"] == {}                    # el día en curso no se cierra


def test_ok_despues_del_cierre_borra_y_cierra_y_una_falla_posterior_no_reabre():
    e = _act(None, _cob([_b("2026-11-20", "VIIRS_NOAA20", False, "2026-11-20T10:00:00Z")], [_fb("2026-11-20", "VIIRS_NOAA20")]))
    assert len(e["no_medidas"]) == 1
    e = _act(e, _cob([_b("2026-11-20", "VIIRS_NOAA20", True, "2026-11-21T04:00:00Z")]))
    assert e["no_medidas"] == [] and e["dias_cerrados"] == {"2026-11-20": ["VIIRS_NOAA20"]}
    e = _act(e, _cob([_b("2026-11-20", "VIIRS_NOAA20", False, "2026-11-24T14:00:00Z")], [_fb("2026-11-20", "VIIRS_NOAA20")]))
    assert e["no_medidas"] == [], "una caída de CMR reabrió un día que ya se había medido entero"


def test_ok_antes_del_cierre_borra_pero_no_cierra_y_una_falla_posterior_reabre():
    e = _act(None, _cob([_b("2026-11-24", "MODIS_AQUA", False, "2026-11-24T03:00:00Z")], [_fb("2026-11-24", "MODIS_AQUA")]))
    e = _act(e, _cob([_b("2026-11-24", "MODIS_AQUA", True, "2026-11-24T06:00:00Z")]))
    assert e["no_medidas"] == [] and e["dias_cerrados"] == {}
    e = _act(e, _cob([_b("2026-11-24", "MODIS_AQUA", False, "2026-11-24T14:00:00Z")], [_fb("2026-11-24", "MODIS_AQUA")]))
    assert [i["motivo"] for i in e["no_medidas"]] == ["busqueda_fallida"]
    assert e["no_medidas"][0]["desde_utc"] == "2026-11-24T14:00:00Z"


def test_desde_utc_se_conserva_mientras_sigue_sin_medirse():
    e = _act(None, _cob([_b("2026-11-24", "MODIS_AQUA", False, "2026-11-24T03:00:00Z")], [_fb("2026-11-24", "MODIS_AQUA")]))
    e = _act(e, _cob([_b("2026-11-24", "MODIS_AQUA", False, "2026-11-24T05:00:00Z")], [_fb("2026-11-24", "MODIS_AQUA")]))
    assert e["no_medidas"][0]["desde_utc"] == "2026-11-24T03:00:00Z"


def test_pasada_sin_bajar_queda_y_su_record_la_borra_pero_no_el_de_otra_plataforma():
    cob = _cob([_b("2026-11-23", "VIIRS_NOAA20_750", True, "2026-11-24T04:00:00Z")],
               [_fd("2026-11-23", "VIIRS_NOAA20_750", "2026-11-23 06:12")])
    e = _act(None, cob)
    assert e["no_medidas"][0]["motivo"] == "pasadas_no_medidas"
    assert e["no_medidas"][0]["pasadas"] == [{"minuto": "2026-11-23 06:12", "etapa": "descarga"}]
    assert e["dias_cerrados"] == {}                    # con una pasada perdida el día no queda cerrado
    otra = _act(None, cob, records=[{"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-23 06:12"}])
    assert len(otra["no_medidas"]) == 1                # control: record de otra plataforma
    misma = _act(None, cob, records=[{"sensor": "VIIRS_NOAA20_750", "datetime_utc": "2026-11-23 06:12"}])
    assert misma["no_medidas"] == []


def test_error_de_procesamiento_es_pasada_no_medida_y_las_incidencias_sin_juicio_no():
    inc = [{"tipo": "error_procesamiento", "volcan": "Lascar", "fecha": "2026-11-22", "plataforma": "MODIS_TERRA",
            "pasada": "2026-11-22 03:05"},
           {"tipo": "sin_granulos", "volcan": "Lascar", "fecha": "2026-11-22", "plataforma": "MODIS_AQUA"},
           {"tipo": "sin_record", "volcan": "Lascar", "fecha": "2026-11-22", "plataforma": "VIIRS_NOAA21"},
           {"tipo": "dia_parcial", "volcan": "Lascar", "fecha": "2026-11-22", "plataforma": None}]
    bus = [_b("2026-11-22", p, True, "2026-11-23T05:00:00Z") for p in ("MODIS_TERRA", "MODIS_AQUA", "VIIRS_NOAA21")]
    e = _act(None, _cob(bus, [], inc))
    assert [(i["plataforma"], i["pasadas"]) for i in e["no_medidas"]] == \
        [("MODIS_TERRA", [{"minuto": "2026-11-22 03:05", "etapa": "procesamiento"}])]
    assert e["dias_cerrados"] == {"2026-11-22": ["MODIS_AQUA", "VIIRS_NOAA21"]}


def test_otro_volcan_no_entra():
    e = _act(None, _cob([_b("2026-11-24", "MODIS_AQUA", False, "2026-11-24T14:00:00Z", volcan="Llaima")],
                        [_fb("2026-11-24", "MODIS_AQUA", volcan="Llaima")]))
    assert e["no_medidas"] == []


def test_ventana_de_30_dias():
    viejo = {"no_medidas": [{"fecha": "2026-10-01", "plataforma": "MODIS_AQUA", "motivo": "busqueda_fallida",
                             "pasadas": [], "desde_utc": "x"}],
             "dias_cerrados": {"2026-10-01": ["MODIS_TERRA"], "2026-11-20": ["MODIS_TERRA"]}}
    e = _act(viejo, _cob())
    assert e["no_medidas"] == [] and e["dias_cerrados"] == {"2026-11-20": ["MODIS_TERRA"]}


def test_latencia_igual_a_la_de_fetch():
    assert cp.LATENCIA_MINIMA_NRT_H == fetch.LATENCIA_MINIMA_NRT_H


# ── (3) CLI: sólo reescribe si cambió lo que dice ─────────────────────────────────────────────────────────────────

def test_cli_no_reescribe_sin_cambios(tmp_path):
    ent = tmp_path / "cob.json"
    ent.write_text(json.dumps(_cob([_b("2026-11-24", "MODIS_AQUA", False, "2026-11-24T14:00:00Z")],
                                   [_fb("2026-11-24", "MODIS_AQUA")])), encoding="utf-8")
    arch = tmp_path / "data" / "cobertura" / "Lascar.json"
    args = ["--entrada", str(ent), "--volcan", "Lascar", "--archivo", str(arch)]
    assert cp.main(args + ["--ahora", "2026-11-24T14:50:00Z"]) == 0
    d1 = json.loads(arch.read_text(encoding="utf-8"))
    assert d1["actualizado_utc"] == "2026-11-24T14:50:00Z" and len(d1["no_medidas"]) == 1
    assert cp.main(args + ["--ahora", "2026-11-24T16:50:00Z"]) == 0
    assert json.loads(arch.read_text(encoding="utf-8"))["actualizado_utc"] == "2026-11-24T14:50:00Z"
    assert cp.main(["--entrada", str(tmp_path / "no_existe.json"), "--volcan", "Lascar", "--archivo", str(arch)]) == 0


# ── (4) de punta a punta ─────────────────────────────────────────────────────────────────────────────────────────

def test_punta_a_punta_caida_y_recuperacion(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(fetch, "ENABLE_CMR_SEARCH_BREAKER", True)
    arch = tmp_path / "Lascar_cob_pub.json"
    ruta, _ = _correr(monkeypatch, capsys, tmp_path, PASADO, _caido, "c1.json")
    cp.main(["--entrada", str(ruta), "--volcan", "Lascar", "--archivo", str(arch), "--ahora", "2026-10-20T00:00:00Z"])
    caido = json.loads(arch.read_text(encoding="utf-8"))
    assert caido["no_medidas"] and all(i["motivo"] == "busqueda_fallida" and i["fecha"] == PASADO
                                       for i in caido["no_medidas"])
    fetch.limpiar_fallas()
    fetch.reiniciar_ventana()
    ruta, _ = _correr(monkeypatch, capsys, tmp_path, PASADO, _buscador(PASADO), "c2.json")
    cp.main(["--entrada", str(ruta), "--volcan", "Lascar", "--archivo", str(arch), "--ahora", "2026-10-20T02:00:00Z"])
    sano = json.loads(arch.read_text(encoding="utf-8"))
    assert sano["no_medidas"] == []
    assert PASADO in sano["dias_cerrados"]


# ── (5) workflows ────────────────────────────────────────────────────────────────────────────────────────────────

def _pasos(nombre):
    d = yaml.safe_load((ROOT / ".github" / "workflows" / nombre).read_text(encoding="utf-8"))
    return d["jobs"]["process"]["steps"]


@pytest.mark.parametrize("nombre,entrada", [("nrt.yml", "cobertura_nrt/"), ("barrido-huecos.yml", "cobertura_barrido/")])
def test_workflow_publica_antes_del_commit_y_sube_el_archivo(nombre, entrada):
    pasos = _pasos(nombre)
    i_pub = next(i for i, s in enumerate(pasos) if "cobertura_publicada.py" in s.get("run", ""))
    i_commit = next(i for i, s in enumerate(pasos) if "git push" in s.get("run", ""))
    i_pipe = next(i for i, s in enumerate(pasos) if "run_pipeline.py --profile mirova_equivalent" in s.get("run", ""))
    pub = pasos[i_pub]
    assert i_pipe < i_pub < i_commit
    assert pub.get("continue-on-error") is True
    assert "--entrada \"" + entrada in pub["run"] and '--archivo "data/cobertura/${{ matrix.volcano }}.json"' in pub["run"]
    assert "--cobertura-json \"" + entrada in pasos[i_pipe]["run"]
    assert 'git add "data/cobertura/${{ matrix.volcano }}.json"' in pasos[i_commit]["run"]


# ── (6) tablero ──────────────────────────────────────────────────────────────────────────────────────────────────

MODULO = ROOT / "frontend" / "cobertura.js"


def _node(cuerpo, datos=None):
    js = ("'use strict';\nconst C = require(" + json.dumps(str(MODULO)) + ");\n"
          "const DATOS = JSON.parse(require('fs').readFileSync(0, 'utf8'));\n" + cuerpo)
    r = subprocess.run(["node", "-e", js], input=json.dumps(datos), capture_output=True, text=True, encoding="utf-8",
                       timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


DATOS_TABLERO = {"no_medidas": [
    {"fecha": "2026-11-24", "plataforma": "MODIS_AQUA", "motivo": "busqueda_fallida", "pasadas": []},
    {"fecha": "2026-11-23", "plataforma": "VIIRS_NOAA20_750", "motivo": "pasadas_no_medidas",
     "pasadas": [{"minuto": "2026-11-23 06:12", "etapa": "descarga"}]},
    {"fecha": "2026-11-10", "plataforma": "VIIRS_NOAA21", "motivo": "busqueda_fallida", "pasadas": []}]}


@pytest.mark.skipif(shutil.which("node") is None, reason="el módulo se prueba con node")
def test_modulo_filtra_por_intervalo_y_plataforma_y_distingue_los_motivos():
    r = _node("""
const d0 = Date.parse('2026-11-23T00:00:00Z'), d1 = Date.parse('2026-11-24T23:59:59Z');
const todo = C.pendientes(DATOS, {desdeMs: d0, hastaMs: d1});
const modis = C.pendientes(DATOS, {desdeMs: d0, hastaMs: d1, filtro: p => p.startsWith('MODIS')});
const tarde = C.pendientes(DATOS, {desdeMs: Date.parse('2026-11-23T07:00:00Z'), hastaMs: d1});
const nada = C.pendientes({no_medidas: []}, {});
console.log(JSON.stringify({todo: todo.map(i => i.plataforma), modis: modis.map(i => i.plataforma),
  tarde: tarde.map(i => i.plataforma), texto: C.textoCorto(todo), nada: C.textoCorto(nada),
  linea0: C.lineaItem(todo[0]), linea1: C.lineaItem(todo[1]), titulo: C.titulo(todo)}));
""", DATOS_TABLERO)
    assert r["todo"] == ["MODIS_AQUA", "VIIRS_NOAA20_750"]          # el del 10 queda fuera del intervalo
    assert r["modis"] == ["MODIS_AQUA"]
    assert r["tarde"] == ["MODIS_AQUA"]                             # la pasada de las 06:12 queda antes del corte
    assert r["nada"] == ""                                           # control: nada que decir
    assert "1 día-satélite sin búsqueda" in r["texto"] and "1 pasada sin medir" in r["texto"]
    assert "no respondió" in r["linea0"] and "MODIS Aqua" in r["linea0"]
    assert "06:12 UTC no se pudo bajar" in r["linea1"] and "VIIRS 750 NOAA-20" in r["linea1"]
    assert "no son noches tranquilas" in r["titulo"]


@pytest.mark.parametrize("vista,llamada", [("index.html", "CoberturaTablero.pintar(cobEl"),
                                           ("index.html", "CoberturaTablero.pintar(cobHost"),
                                           ("diario.html", "CoberturaTablero.pintar(sCob"),
                                           ("mosaico.html", "CoberturaTablero.pintar(cobEl")])
def test_las_tres_vistas_cargan_el_modulo_y_lo_pintan(vista, llamada):
    txt = (ROOT / "frontend" / vista).read_text(encoding="utf-8")
    assert re.search(r'<script src="cobertura\.js"></script>', txt), vista + " no carga frontend/cobertura.js"
    assert llamada in txt
