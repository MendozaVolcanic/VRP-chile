# -*- coding: utf-8 -*-
"""S193 (auditoría Codex ronda 2, hallazgos F11-101, F9-101, F11-V301 y F11-106): tres defensas que callaban.

POR QUÉ, COMO GEÓLOGO.
1. F11-101 y F9-101. Una alerta protegida de MIROVA (1 MW o más, lectura A) que producción (la vía) no publica es lo
   más grave que puede pasar: el operador no ve un cráter que MIROVA sí ve. La vigilancia de la guardia sólo avisaba
   cuando la guardia K la publicaba (reversión o investigar). Si a la guardia le faltaba esa pasada, o si K también la
   callaba, la pasada quedaba listada en `protegidas_sin_publicar_produccion` y el veredicto salía VERDE: nadie se
   enteraba hasta el auto-audit del lunes. El 2026-11-21 pasaba de verdad: Chaitén MODIS 2026-11-19 02:30 UTC,
   MIROVA 1,07 MW, la vía y K callan, vigilancia VERDE. Arreglo: esas pasadas van a
   `protegidas_sin_publicar_sin_aviso` y el workflow abre un issue propio («protegida sin publicar»). Es un AVISO: el
   veredicto de la regla no cambia y nunca pide revertir (una pérdida que K también tiene no dice nada de K contra
   la vía).
2. F11-V301. El auto-audit semanal toma el inicio de la vía de los datos (la primera pasada con la marca) y llamaba
   vía a toda noche desde ahí, para siempre. Tras revertir un sensor, los records K nuevos caían en «K en noche
   VIA_MODIS» y el detector que volvió a producción quedaba sin medir. Ahora la vigencia la dice el flag de producción
   (`pipeline.profile`, perfil mirova_equivalent): con el flag encendido nada cambia; apagado, la vía va del primer al
   último record con la marca y lo posterior es K.
3. F11-106. La vigilancia de la sombra C0 compara C0 contra K de producción. Desde el reemplazo de la historia del
   2026-11-12 no hay K en producción en ningún sensor y salía VERDE sin comparar nada. Ahora dice SIN_OBJETO.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Cada caso nuevo tiene su control con la misma escena y el resultado contrario
(la pasada publicada, el flag encendido, un sensor todavía en K), así que la prueba puede dar los dos resultados. (2)
Antes del arreglo cada prueba nueva cae por aserción o por la clave que falta (comprobado sobre main `27ded66ee`).
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import auto_audit_weekly as aa  # noqa: E402
import scripts.vigilancia_guardia_modis as vg  # noqa: E402  (el mismo módulo que parchea el fixture `disco`)
import vigilancia_sombra as vs  # noqa: E402
from test_vigilancia_guardia_por_volcan_s175 import (  # noqa: E402,F401  (fixture `disco` y la escena de S175)
    ALERTA, REF_FRESCA, _crudo, _disco_base, _fila, disco)
from test_vigilancia_sombra_s156 import _caso_pcc, insumos  # noqa: E402,F401  (fixture `insumos` de S156)

ENC = "2026-11-05 22:10:00"
WF_MODIS = ROOT / ".github" / "workflows" / "vigilancia-guardia-modis.yml"
WF_VIIRS = ROOT / ".github" / "workflows" / "vigilancia-guardia-viirs.yml"
WF_SOMBRA = ROOT / ".github" / "workflows" / "vigilancia-sombra.yml"


def _pasada(vol, fecha, protegida, prod, guardia, prod_via=True, sensor="MODIS", vrp=None):
    return {"volcano": vol, "sensor": sensor, "fecha_utc": fecha[:16], "instante_utc": fecha[:16] + ":00",
            "vrp_mirova_mw": vrp if vrp is not None else (1.07 if protegida else 0.3), "protegida": protegida,
            "minima": False, "referencia_sospechosa": False, "prod_pub": prod, "guardia_pub": guardia,
            "prod_via": prod_via}


def _disp(pas, juzgadas=None, sensor="MODIS"):
    return vg.disparadores(list(pas), [], [], hoy="2026-11-21", encendido=ENC, juzgadas=juzgadas, sensor=sensor)


def _sin_aviso(d):
    return [(p["volcano"], p["fecha_utc"]) for p in d["protegidas_sin_publicar_sin_aviso"]]


# ------------------------------------------------------------------ F11-101 / F9-101: la protegida que nadie avisa
def test_f9_101_k_tambien_calla_la_protegida_queda_con_aviso_y_sin_reversion():
    """El caso real del 2026-11-21 (Chaitén): la vía calla y K también. No es reversión (K no publica), pero avisa."""
    d = _disp([_pasada("Chaiten", "2026-11-19 02:30", True, False, False)])
    assert _sin_aviso(d) == [("Chaiten", "2026-11-19 02:30")]
    assert d["reversion"] == [] and d["fuera_de_plazo"] == []
    assert d["veredicto"] == "VERDE", "es un aviso aparte: el veredicto de la regla no cambia"
    # control: la misma pasada publicada por producción no deja aviso
    assert _sin_aviso(_disp([_pasada("Chaiten", "2026-11-19 02:30", True, True, False)])) == []


def test_f11_101_la_guardia_sin_la_pasada_no_tapa_el_aviso():
    d = _disp([_pasada("Lascar", "2026-11-19 06:00", True, False, None)])
    assert _sin_aviso(d) == [("Lascar", "2026-11-19 06:00")] and d["veredicto"] == "VERDE"
    # control: una Muy Bajo (no protegida) que producción calla no es este aviso
    assert _sin_aviso(_disp([_pasada("Lascar", "2026-11-19 06:00", False, False, None)])) == []


def test_lo_que_ya_tiene_issue_no_se_repite():
    """Reversión, fuera de plazo y caída a K ya abren su issue: no se duplican en el aviso."""
    d = _disp([_pasada("Lascar", "2026-11-19 06:00", True, False, True)])
    assert d["veredicto"] == "REVERSION_CANDIDATA" and _sin_aviso(d) == []
    d = _disp([_pasada("Lascar", "2026-11-19 06:00", True, False, True, prod_via=False)])
    assert d["veredicto"] == "INVESTIGAR" and _sin_aviso(d) == []
    # control: con otra pasada que K también calla, ésa sí va al aviso y la reversión sigue
    d = _disp([_pasada("Lascar", "2026-11-19 06:00", True, False, True),
               _pasada("Chaiten", "2026-11-19 02:30", True, False, False)])
    assert d["veredicto"] == "REVERSION_CANDIDATA" and _sin_aviso(d) == [("Chaiten", "2026-11-19 02:30")]


def test_una_pasada_juzgada_deja_de_avisar():
    p = _pasada("Chaiten", "2026-11-19 02:30", True, False, False)
    assert _sin_aviso(_disp([p], juzgadas={vs._clave(p): {"decision": "artefacto"}})) == []


def test_el_aviso_es_por_sensor_en_viirs():
    d = _disp([_pasada("Lascar", "2026-11-19 06:00", True, False, False, sensor="VIIRS375")], sensor="VIIRS375")
    assert _sin_aviso(d) == [("Lascar", "2026-11-19 06:00")] and d["veredicto"] == "VERDE"


def test_cadena_real_desde_el_disco_la_guardia_sin_pasada_avisa(disco):
    """Desde los JSON: MIROVA da 25 MW, producción (la vía) calla y la guardia no tiene la pasada."""
    prod, guardia = _disco_base()
    prod["NevadosDeChillan"].append(_crudo(ALERTA, False, marca=True))
    disco(prod, guardia, REF_FRESCA + [_fila("NevadosDeChillan", ALERTA + ":00", 25.0)])
    out = vg.evaluar("2026-11-20")
    assert [(p["volcano"], p["fecha_utc"]) for p in out["protegidas_sin_publicar_sin_aviso"]] == [
        ("NevadosDeChillan", ALERTA)]
    assert out["reversion"] == [] and out["veredicto"] == "VERDE"
    # control: la vía la publica y no hay aviso
    prod, guardia = _disco_base()
    prod["NevadosDeChillan"].append(_crudo(ALERTA, True, marca=True))
    disco(prod, guardia, REF_FRESCA + [_fila("NevadosDeChillan", ALERTA + ":00", 25.0)])
    assert vg.evaluar("2026-11-20")["protegidas_sin_publicar_sin_aviso"] == []


def _paso_issue(wf, job="vigilar"):
    return next(p for p in yaml.safe_load(wf.read_text(encoding="utf-8"))["jobs"][job]["steps"]
                if p.get("name") == "Open issue")["run"]


def test_los_workflows_abren_el_aviso_fuera_del_case_del_veredicto():
    """El aviso no depende del veredicto: con REVERSION_CANDIDATA o VERDE igual se abre, y no usa la rama de reversión."""
    for wf, titulo in ((WF_MODIS, 'abrir "Guardia K de MODIS: protegida sin publicar"'),
                       (WF_VIIRS, 'abrir "Guardia K de $ETIQUETA: protegida sin publicar"')):
        run = _paso_issue(wf)
        assert titulo in run, wf.name
        assert run.index("esac") < run.index(titulo), f"{wf.name}: el aviso va después del case del veredicto"
        assert "protegidas_sin_publicar_sin_aviso" in run[run.index("esac"):run.index(titulo)], wf.name
        assert "revert" not in run[run.index(titulo):].split("\n")[0].lower(), wf.name


# ------------------------------------------------------------------ F11-V301: la vigencia de la vía no sale de los datos
def _rec_audit(dt, via=None, sensor="MODIS_AQUA"):
    r = {"datetime_utc": dt, "sensor": sensor, "regimen": {"perfil": "mirova_equivalent", "codigo_sha": "abc"},
         "primary_cluster": {"vrp_mw": 2.0, "centroid_dist_km": 1.0}, "distance_class": "summit", "vrp_mw": 2.0,
         "n_anomalous_pixels": 3, "anomaly_pixels": [{"lat": 0, "lon": 0}]}
    if via is not None:
        r["via_codigo_mirova"] = via
    return r


HISTORIA = {"Lascar": [_rec_audit("2025-02-15 06:00", via=True), _rec_audit("2026-11-16 06:00", via=True),
                       _rec_audit("2026-11-21 06:00")]}     # el último es el K que el NRT escribe tras el revert
WIN = ("2026-11-15", "2026-11-25")


def test_v301_tras_el_revert_el_record_k_nuevo_se_cuenta():
    via = aa.fronteras_via(HISTORIA, {"MODIS": False, "VIIRS375": True, "VIIRS750": True})
    out = aa.nuestros_por_noche(HISTORIA, WIN, "2025-02-15", via_modis=via)
    assert ("Lascar", "MODIS", "2026-11-21") in out["vistos"]
    assert "K en noche VIA_MODIS" not in out["fuera_de_detector"], out["fuera_de_detector"]
    assert ("Lascar", "MODIS", "2026-11-16") in out["vistos"], "la noche de la vía sigue separada como vía"
    assert aa.detector_vigente_de("MODIS", "K", via) == "K"
    assert aa.detector_de_noche("2026-11-16", "2025-02-15", "MODIS", via) == "VIA_MODIS"
    assert aa.detector_de_noche("2026-11-21", "2025-02-15", "MODIS", via) == "K"


def test_v301_control_con_el_flag_encendido_es_lo_de_siempre():
    for encendidos in ({"MODIS": True, "VIIRS375": True, "VIIRS750": True}, None):
        via = aa.fronteras_via(HISTORIA, encendidos)
        assert via == {"MODIS": "2025-02-15"}, "con la vía vigente la salida es la de antes"
        out = aa.nuestros_por_noche(HISTORIA, WIN, "2025-02-15", via_modis=via)
        assert out["fuera_de_detector"] == {"K en noche VIA_MODIS": 1}
        assert aa.detector_vigente_de("MODIS", "K", via) == "VIA_MODIS"


def test_v301_una_via_cerrada_no_es_vigente_en_ningun_consumidor():
    via = aa.fronteras_via(HISTORIA, {"MODIS": False})
    assert aa._fronteras(via) == {}
    por_detector = {"K": {"recall": {}, "marca": "K"}}
    assert aa.evaluacion_vigente(por_detector, "K", via) is por_detector["K"]
    assert aa.sensores_sin_juzgar({}, {}, [], set(), via_modis=via) == {}
    assert aa.etiqueta_vigente("K", via) == "K"


def test_v301_main_lee_los_flags_de_produccion():
    """main() pasa a fronteras_via los flags del perfil de producción, leídos de pipeline.profile (A89)."""
    import inspect
    assert "fronteras_via(records_por_volcan, encendidos_de_produccion())" in inspect.getsource(aa.main)
    enc = aa.encendidos_de_produccion()
    assert set(enc) == {"MODIS", "VIIRS375", "VIIRS750"} and all(isinstance(v, bool) for v in enc.values())


# ------------------------------------------------------------------ F11-106: la sombra C0 sin K que comparar
TRES_VIAS = {("PuyehueCordonCaulle", "MODIS_AQUA", "2026-11-02 18:10"),
             ("PuyehueCordonCaulle", "VIIRS_NOAA20", "2026-11-11 06:54"),
             ("PuyehueCordonCaulle", "VIIRS_NOAA20_750", "2026-11-11 06:54")}


def test_f11_106_sin_k_en_ningun_sensor_dice_sin_objeto(insumos, monkeypatch):
    filas, _, sombra = _caso_pcc()
    insumos(filas, [], sombra)
    monkeypatch.setattr(vs, "claves_via", lambda: TRES_VIAS)
    out = vs.evaluar("2026-10-25")
    assert out["veredicto"] == "SIN_OBJETO", out["veredicto"]
    assert out["sensores_k"] == [] and "sin K" in out["sin_objeto"]


def test_f11_106_control_con_un_sensor_en_k_sigue_vigilando(insumos, monkeypatch):
    filas, prod, sombra = _caso_pcc()
    insumos(filas, prod, sombra)
    monkeypatch.setattr(vs, "claves_via", lambda: {("PuyehueCordonCaulle", "MODIS_AQUA", "2026-11-02 18:10")})
    out = vs.evaluar("2026-10-25")
    assert out["veredicto"] != "SIN_OBJETO" and "sin_objeto" not in out


def test_f11_106_un_disparador_no_se_tapa_con_sin_objeto(insumos, monkeypatch):
    """Si quedara K residual que calla una protegida que C0 publica, el disparador manda sobre SIN_OBJETO."""
    filas, prod, sombra = _caso_pcc()
    insumos(filas, prod, sombra)
    monkeypatch.setattr(vs, "claves_via", lambda: TRES_VIAS)
    monkeypatch.setattr(vs, "disparadores", lambda *a, **k: {"veredicto": "INVESTIGAR"})
    assert vs.evaluar("2026-10-25")["veredicto"] == "INVESTIGAR"


def test_f11_106_el_workflow_no_abre_issue_con_sin_objeto():
    run = _paso_issue(WF_SOMBRA)
    rama = run[run.index("SIN_OBJETO)"):]
    rama = rama[:rama.index(";;")]
    assert "abrir" not in rama and "echo" in rama
