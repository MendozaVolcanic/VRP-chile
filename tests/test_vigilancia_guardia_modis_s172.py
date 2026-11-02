# -*- coding: utf-8 -*-
"""S172: la vigilancia de la guardia K de MODIS dispara lo que pide la regla de reversión de MOD-D.

POR QUÉ. Con la vía «código MIROVA» encendida en MODIS, K corre aparte como guardia
(experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md §3 y §4, rama loop/activo; diseño, decisión 3). El
peor caso es una señal débil o de borde que K publica y la vía calla. La vigilancia compara cada día, en MODIS,
producción (la vía) contra la guardia (K) contra MIROVA, y una vigilancia ciega no da error, da VERDE: por eso cada
caso tiene su prueba, con escenas sintéticas, y cada disparador su control (el caso vecino que no tiene que disparar).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.vigilancia_guardia_modis as vg  # noqa: E402

ENC = "2026-11-05 22:10:00"
NOCHE = lambda *a: False  # noqa: E731
VENTANA = ("2026-10-25", "2026-12-31")
VOLS_CASO = ["NevadosDeChillan", "Lascar"]


def _fila(vol, fecha, vrp, tipo="ALERTA_TERMICA", b="MODIS", source="CONS"):
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": tipo, "source": source}


def _rec(vol, fecha, hhmm, pub, via=None, perfil=None, b="MODIS", sensor="MODIS_AQUA", lab="sin_info"):
    dt = datetime.strptime(f"{fecha} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha, "pub": pub, "sensor": sensor, "perfil": perfil,
            "lab": lab, "via": via}


def _pasada(vol, fecha, protegida, prod, guardia, vrp=None, prod_via=None):
    return {"volcano": vol, "sensor": "MODIS", "fecha_utc": fecha[:16], "instante_utc": fecha[:16] + ":00",
            "vrp_mirova_mw": vrp if vrp is not None else (2.0 if protegida else 0.3), "protegida": protegida,
            "minima": False, "referencia_sospechosa": False, "prod_pub": prod, "guardia_pub": guardia,
            "prod_via": prod_via}


def _disp(pas, prod=(), guardia=(), hoy="2026-11-20", enc=ENC, juzgadas=None, ahora=None):
    return vg.disparadores(list(pas), list(prod), list(guardia), hoy=hoy, encendido=enc, juzgadas=juzgadas,
                           ahora=ahora)


# ------------------------------------------------------------------ encendido desde los datos
def test_el_encendido_sale_del_primer_record_modis_de_la_via():
    raw = {"NevadosDeChillan": [
        {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-05 06:30", "first_processed_utc": "2026-11-05T08:00:00Z"},
        {"sensor": "MODIS_TERRA", "datetime_utc": "2026-11-04 03:10", "via_codigo_mirova": True,
         "first_processed_utc": "2026-11-05T22:10:00Z", "processed_utc": "2026-11-06T22:00:00Z"},
        {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-06 06:30", "via_codigo_mirova": True,
         "processed_utc": "2026-11-06T09:00:00Z"},
        # la caída a K no es la vía, y la vía de VIIRS no es la de MODIS
        {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-03 06:30", "via_codigo_mirova": "sin_mxd03",
         "processed_utc": "2026-11-01T00:00:00Z"},
        {"sensor": "VIIRS_NOAA20_750", "datetime_utc": "2026-11-01 06:30", "via_codigo_mirova": True,
         "processed_utc": "2026-11-01T00:00:00Z"}]}
    e = vg.encendido_desde_datos(raw)
    # MA172-206 (mini auditoría S172): el upgrade de NRT a estándar re-escribe con la vía pasadas viejas y les deja el
    # `first_processed_utc` de K (pipeline/store.py hereda ese campo en todo reemplazo). El encendido es el menor
    # `processed_utc` de la vía, que sólo puede ser posterior al merge: aquí 2026-11-06 09:00, no el 11-05 22:10 heredado.
    assert e["encendido_utc"] == "2026-11-06 09:00:00"
    assert e["primera_observacion"] == "2026-11-04 03:10"
    assert e["via"] == {("NevadosDeChillan", "MODIS_TERRA", "2026-11-04 03:10"),
                        ("NevadosDeChillan", "MODIS_AQUA", "2026-11-06 06:30")}


def test_sin_records_de_la_via_no_hay_encendido():
    raw = {"Lascar": [{"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-05 06:30"}]}
    assert vg.encendido_desde_datos(raw)["encendido_utc"] is None


# ------------------------------------------------------------------ pasadas
def test_pasadas_solo_modis_con_guardia_y_marca_de_la_via():
    filas = [_fila("NevadosDeChillan", "2026-11-10 07:20:00", 2.18),
             _fila("NevadosDeChillan", "2026-11-10 05:00:00", 3.0, b="VIIRS375")]
    prod = [_rec("NevadosDeChillan", "2026-11-10", "07:21", False, via=True),
            _rec("NevadosDeChillan", "2026-11-10", "05:00", False, b="VIIRS375", sensor="VIIRS_NOAA20")]
    guardia = [_rec("NevadosDeChillan", "2026-11-10", "07:21", True)]
    p = vg.pasadas_modis(filas, prod, guardia, VENTANA, diurna=NOCHE)
    assert len(p) == 1
    assert (p[0]["sensor"], p[0]["protegida"], p[0]["prod_pub"], p[0]["guardia_pub"], p[0]["prod_via"]) == (
        "MODIS", True, False, True, True)


# ------------------------------------------------------------------ disparadores
def test_una_protegida_que_la_guardia_publica_y_produccion_calla_dispara_la_reversion():
    d = _disp([_pasada("NevadosDeChillan", "2026-11-10 07:20", True, False, True)])
    assert d["veredicto"] == "REVERSION_CANDIDATA" and len(d["reversion"]) == 1


def test_una_protegida_que_las_dos_publican_no_dispara():
    d = _disp([_pasada("NevadosDeChillan", "2026-11-10 07:20", True, True, True)])
    assert d["veredicto"] == "VERDE" and d["reversion"] == []


def test_mutacion_produccion_sin_record_o_guardia_que_calla_no_es_reversion():
    assert _disp([_pasada("A", "2026-11-10 07:20", True, None, True)])["reversion"] == []
    assert _disp([_pasada("A", "2026-11-10 07:20", True, False, False)])["reversion"] == []


def test_protegida_que_la_guardia_publica_sin_record_de_produccion_pide_investigar():
    """MA172-202 (mini auditoría S172): la vía descarta en silencio los gránulos de borde (171-01), así que el peor caso
    de la regla es una protegida que la guardia publica y de la que producción no tiene record. Para el operador eso es
    silencio igual que una pasada que no publica. No está pre-autorizada como reversión (la regla habla de «calla»):
    pide investigar, pasado el plazo de espera del NRT (ESPERA_SIN_RECORD_H, propuesta; la fija Nicolás)."""
    p = _pasada("NevadosDeChillan", "2026-11-10 06:40", True, None, True, vrp=2.5)
    d = _disp([p], ahora="2026-11-12 00:00:00")
    assert d["reversion"] == [] and d["veredicto"] == "INVESTIGAR"
    assert [x["fecha_utc"] for x in d["protegidas_sin_record_produccion"]] == ["2026-11-10 06:40"]
    # recién pasada: el NRT puede no haberla procesado todavía; no dispara
    d = _disp([p], ahora="2026-11-10 09:00:00")
    assert d["veredicto"] == "VERDE" and d["protegidas_sin_record_produccion"] == []
    # control: si la guardia tampoco la publica, o no es protegida, no dispara
    assert _disp([_pasada("A", "2026-11-10 06:40", True, None, False)], ahora="2026-11-12 00:00:00")["veredicto"] == "VERDE"
    assert _disp([_pasada("A", "2026-11-10 06:40", False, None, True)], ahora="2026-11-12 00:00:00")["veredicto"] == "VERDE"
    # una juzgada no vuelve a disparar
    j = {("NevadosDeChillan", "MODIS", "2026-11-10 06:40"): {"decision": "investigada"}}
    assert _disp([p], ahora="2026-11-12 00:00:00", juzgadas=j)["veredicto"] == "VERDE"


def test_el_nulo_sin_pares_no_se_lee_como_nulo_sano():
    """MA172-208: 0 pares no es «guardia y producción coinciden», es «no medí»."""
    d = _disp([], [], [], hoy="2026-11-03", enc=None)
    assert d["nulo"]["pares"] == 0 and d["nulo"]["sin_medir"] is True


def test_la_frescura_de_la_referencia_se_mide_en_las_filas_de_modis():
    """MA172-204: una referencia con VIIRS fresco y MODIS detenido deja la vigilancia sin alertas MODIS que comparar."""
    viirs = [_fila("Lascar", "2026-11-19 05:00:00", 0.0, tipo="RUTINA", b="VIIRS375")]
    modis_viejo = [_fila("Lascar", "2026-11-01 06:00:00", 0.0, tipo="RUTINA")]
    av = vg.avisos_referencia_modis(viirs + modis_viejo, "2026-11-20")
    assert av and "MODIS" in av[0]
    assert vg.avisos_referencia_modis(viirs, "2026-11-20"), "sin ninguna fila MODIS también es aviso"
    assert vg.avisos_referencia_modis(viirs + [_fila("Lascar", "2026-11-19 06:00:00", 0.0, tipo="RUTINA")],
                                      "2026-11-20") == []


def test_lo_anterior_al_encendido_es_retrospectivo_salvo_que_la_via_haya_escrito_el_record():
    """Cuenta desde el encendido (§4). Pero una pasada anterior cuyo record de producción ya es de la vía (el NRT
    re-escribe 8 días hacia atrás) no puede quedar sin mirar: no dispara la reversión, pide investigar."""
    d = _disp([_pasada("A", "2026-11-04 07:20", True, False, True)])
    assert d["veredicto"] == "VERDE" and len(d["retrospectivo"]["protegidas_que_la_guardia_publica_y_prod_calla"]) == 1
    d = _disp([_pasada("A", "2026-11-04 07:20", True, False, True, prod_via=True)])
    assert d["reversion"] == [] and d["veredicto"] == "INVESTIGAR" and d["borde_del_encendido"]


def test_muy_bajo_perdidas_sobre_la_cota_de_dos_pide_investigar():
    base = [_pasada("A", f"2026-11-1{i} 07:20", False, False, True, vrp=0.3) for i in range(2)]
    assert _disp(base)["muy_bajo"]["dispara"] is False and _disp(base)["veredicto"] == "VERDE"
    tres = base + [_pasada("A", "2026-11-15 07:20", False, False, True, vrp=0.3)]
    d = _disp(tres)
    assert d["muy_bajo"]["k"] == 3 and d["muy_bajo"]["dispara"] is True and d["veredicto"] == "INVESTIGAR"


def test_mutacion_muy_bajo_no_cuenta_las_de_0_05_mw_o_menos():
    pas = [_pasada("A", f"2026-11-1{i} 07:20", False, False, True, vrp=0.05) for i in range(4)]
    assert _disp(pas)["muy_bajo"]["k"] == 0


def test_sobrepublicacion_en_negativos_limpios_sobre_la_cota_de_tres_pide_investigar():
    def par(i, prod_pub, g_pub):
        f = f"2026-11-1{i}"
        return (_rec("A", f, "07:20", prod_pub, via=True, lab="neg_limpio"), _rec("A", f, "07:20", g_pub))
    pares = [par(i, True, False) for i in range(3)] + [par(5, True, True), par(6, False, False)]
    prod, guardia = [p for p, _ in pares], [g for _, g in pares]
    d = _disp([], prod, guardia)
    assert d["sobrepublicacion"]["k"] == 3 and d["sobrepublicacion"]["dispara"] is False
    p4, g4 = par(7, True, False)
    d = _disp([], prod + [p4], guardia + [g4])
    assert d["sobrepublicacion"]["k"] == 4 and d["sobrepublicacion"]["dispara"] is True
    assert d["veredicto"] == "INVESTIGAR"


def test_pasadas_que_la_guardia_registra_y_produccion_no_se_cuentan_por_semana():
    guardia = [_rec("A", "2026-11-10", "07:20", False), _rec("A", "2026-11-11", "07:20", False),
               _rec("A", "2026-11-18", "07:20", False)]
    prod = [_rec("A", "2026-11-18", "07:21", False, via=True)]          # a ±120 s: registrada
    d = _disp([], prod, guardia)
    assert d["borde_171_01"]["por_semana"] == {"2026-W46": 2}
    assert d["veredicto"] == "VERDE", "sin cota en la regla: se informa, no dispara (A115)"


def test_antes_del_encendido_guardia_y_produccion_tienen_que_publicar_lo_mismo():
    """El nulo medido de la guardia (diseño, decisión 1; A110): mientras producción siga en K son el mismo detector."""
    prod = [_rec("A", "2026-11-01", "07:20", True), _rec("A", "2026-11-02", "07:20", False)]
    guardia = [_rec("A", "2026-11-01", "07:20", True), _rec("A", "2026-11-02", "07:20", False)]
    d = _disp([], prod, guardia, hoy="2026-11-03", enc=None)
    assert d["nulo"]["pares"] == 2 and d["nulo"]["distintas"] == 0 and d["veredicto"] == "VERDE"
    guardia[1]["pub"] = True
    d = _disp([], prod, guardia, hoy="2026-11-03", enc=None)
    assert d["nulo"]["distintas"] == 1 and d["veredicto"] == "INVESTIGAR"
    # el nulo mide los DIAS_NULO días previos: una diferencia de hace un mes ya no es el nulo de hoy
    assert _disp([], prod, guardia, hoy="2026-12-10", enc=None)["nulo"]["pares"] == 0


def test_una_pasada_juzgada_no_dispara():
    pas = [_pasada("NevadosDeChillan", "2026-11-10 07:20", True, False, True)]
    j = {("NevadosDeChillan", "MODIS", "2026-11-10 07:20"): {"decision": "no revertir"}}
    d = _disp(pas, juzgadas=j)
    assert d["reversion"] == [] and d["veredicto"] == "VERDE" and len(d["juzgadas"]) == 1


def test_plazo_29_protegidas_o_120_dias():
    pas = [_pasada("A", f"2026-11-{6 + i // 4:02d} {10 + i % 4:02d}:00", True, True, True) for i in range(29)]
    pas.append(_pasada("A", "2026-11-20 07:20", True, False, True))      # la 30.a: fuera de plazo
    d = _disp(pas, hoy="2026-11-21")
    assert d["reversion"] == [] and len(d["fuera_de_plazo"]) == 1 and d["veredicto"] == "CANDIDATA_FUERA_DE_PLAZO"
    d = _disp([_pasada("A", "2027-03-10 07:20", True, False, True)], hoy="2027-03-11")    # más de 120 días
    assert d["reversion"] == [] and d["duracion"]["cumplida"] is True


# ------------------------------------------------------------------ evaluar(): ciega y de punta a punta
@pytest.fixture
def insumos(monkeypatch):
    def poner(filas, prod, guardia, enc=ENC, flag=True, raw_guardia_con_via=0):
        monkeypatch.setattr(vg, "cargar_insumos", lambda win, via: (filas, prod, guardia, raw_guardia_con_via))
        monkeypatch.setattr(vg, "leer_encendido", lambda: {"encendido_utc": enc, "primera_observacion": None,
                                                          "via": set()})
        monkeypatch.setattr(vg, "flag_produccion_encendido", lambda: flag)
        monkeypatch.setattr(vg.vs, "_diurna_por_defecto", lambda: NOCHE)
        monkeypatch.setattr(vg.aa, "VOLS", VOLS_CASO)
        monkeypatch.setattr(vg, "leer_juzgadas", lambda *a: {})
    return poner


def _relleno(fecha="2026-11-19", via=None):
    return [_rec(v, fecha, "03:00", False, via=via) for v in VOLS_CASO]


def _caso():
    filas = [_fila("NevadosDeChillan", "2026-11-10 07:20:00", 2.18),
             _fila("Lascar", "2026-11-19 06:00:00", 0.0, tipo="RUTINA")]            # la referencia está viva
    prod = [_rec("NevadosDeChillan", "2026-11-10", "07:20", True, via=True)] + _relleno(via=True)
    guardia = [_rec("NevadosDeChillan", "2026-11-10", "07:20", True)] + _relleno()
    # S172 ronda 2 (MA172-208): pasadas anteriores al encendido en que guardia y producción (las dos K) coinciden, para
    # que el nulo tenga pares
    prod += _relleno("2026-11-01")
    guardia += _relleno("2026-11-01")
    return filas, prod, guardia


def test_evaluar_verde_con_guardia_y_produccion_frescas(insumos):
    insumos(*_caso())
    out = vg.evaluar("2026-11-20")
    assert out["veredicto"] == "VERDE", out.get("avisos")


def test_evaluar_dispara_la_reversion(insumos):
    filas, prod, guardia = _caso()
    prod[0]["pub"] = False
    insumos(filas, prod, guardia)
    assert vg.evaluar("2026-11-20")["veredicto"] == "REVERSION_CANDIDATA"


def test_una_guardia_sin_datos_frescos_da_vigilancia_ciega(insumos):
    filas, prod, guardia = _caso()
    guardia = [g for g in guardia if g["vol"] != "Lascar"] + [_rec("Lascar", "2026-11-10", "03:00", False)]
    insumos(filas, prod, guardia)
    out = vg.evaluar("2026-11-20")
    assert out["veredicto"] == "VIGILANCIA_CIEGA" and any("guardia" in a and "Lascar" in a for a in out["avisos"])


def test_produccion_sin_datos_frescos_da_vigilancia_ciega(insumos):
    filas, prod, guardia = _caso()
    insumos(filas, [p for p in prod if p["vol"] != "Lascar"], guardia)
    out = vg.evaluar("2026-11-20")
    assert out["veredicto"] == "VIGILANCIA_CIEGA"


def test_flag_encendido_sin_records_de_la_via_da_vigilancia_ciega(insumos):
    """La vía cayendo siempre a K dejaría guardia = producción: VERDE para siempre sin vigilar nada."""
    filas, prod, guardia = _caso()
    insumos(filas, prod, guardia, enc=None, flag=True)
    out = vg.evaluar("2026-11-20")
    assert out["veredicto"] == "VIGILANCIA_CIEGA" and any("vía" in a for a in out["avisos"])
    # control: con el flag apagado (antes del PR B) no hay encendido que esperar y el nulo manda
    insumos(filas, [dict(p, via=None) for p in prod], guardia, enc=None, flag=False)
    assert vg.evaluar("2026-11-20")["veredicto"] == "VERDE"


def test_una_guardia_con_records_de_la_via_da_vigilancia_ciega(insumos):
    insumos(*_caso(), raw_guardia_con_via=3)
    out = vg.evaluar("2026-11-20")
    assert out["veredicto"] == "VIGILANCIA_CIEGA" and any("dejó de ser K" in a for a in out["avisos"])


def test_evaluar_con_nulo_sin_pares_da_vigilancia_ciega(insumos):
    """MA172-208: si la guardia arranca junto con el encendido, el nulo no se midió y no se puede leer VERDE."""
    filas, prod, guardia = _caso()
    insumos(filas, [p for p in prod if p["noche"] != "2026-11-01"], [g for g in guardia if g["noche"] != "2026-11-01"])
    out = vg.evaluar("2026-11-20")
    assert out["veredicto"] == "VIGILANCIA_CIEGA" and any("nulo" in a for a in out["avisos"])


def test_evaluar_con_referencia_sin_modis_da_vigilancia_ciega(insumos):
    """MA172-204: con VIIRS fresco y MODIS detenido en la referencia no hay alertas MODIS contra qué comparar."""
    filas, prod, guardia = _caso()
    filas = [f for f in filas if f["sensor_bucket"] != "MODIS"] + [
        _fila("Lascar", "2026-11-19 05:00:00", 0.0, tipo="RUTINA", b="VIIRS375")]
    insumos(filas, prod, guardia)
    out = vg.evaluar("2026-11-20")
    assert out["veredicto"] == "VIGILANCIA_CIEGA" and any("MODIS" in a and "referencia" in a for a in out["avisos"])


def test_un_aviso_no_tapa_una_reversion(insumos):
    filas, prod, guardia = _caso()
    prod[0]["pub"] = False
    insumos(filas, [p for p in prod if p["vol"] != "Lascar"], guardia)
    assert vg.evaluar("2026-11-20")["veredicto"] == "REVERSION_CANDIDATA"


def test_main_escribe_latest_e_historial(insumos, monkeypatch, tmp_path):
    insumos(*_caso())
    monkeypatch.setattr(vg, "OUTDIR", str(tmp_path))
    vg.main([])
    out = json.loads((tmp_path / "guardia_modis_latest.json").read_text(encoding="utf-8"))
    assert out["veredicto"] in ("VERDE", "VIGILANCIA_CIEGA", "REVERSION_CANDIDATA", "INVESTIGAR",
                                "CANDIDATA_FUERA_DE_PLAZO")
    assert len((tmp_path / "guardia_modis_history.jsonl").read_text(encoding="utf-8").splitlines()) == 1


# ------------------------------------------------------------------ archivo de juzgadas y workflow
def test_el_archivo_de_juzgadas_nace_vacio_con_su_esquema_y_se_lee():
    d = json.loads(Path(vg.JUZGADAS).read_text(encoding="utf-8"))
    assert d["pasadas"] == [] and "esquema" in d and "por_que" in d
    assert vg.leer_juzgadas() == {}


def test_el_workflow_escucha_a_la_guardia_y_abre_issues_con_su_prefijo():
    wf = yaml.safe_load((ROOT / ".github/workflows/vigilancia-guardia-modis.yml").read_text(encoding="utf-8"))
    guardia = yaml.safe_load((ROOT / ".github/workflows/guardia-k-modis.yml").read_text(encoding="utf-8"))
    assert "on" in wf and True not in wf
    assert wf["on"]["workflow_run"]["workflows"] == [guardia["name"]]
    assert wf["on"].get("schedule") and "workflow_dispatch" in wf["on"]
    pasos = wf["jobs"]["vigilar"]["steps"]
    issue = next(p for p in pasos if p.get("name") == "Open issue")
    assert issue.get("if") == "always()"
    titulos = [t for t in __import__("re").findall(r'abrir "([^"]+)"', issue["run"])]
    assert titulos and all(t.startswith("Guardia K de MODIS:") for t in titulos), titulos
    assert "scripts/vigilancia_guardia_modis.py" in json.dumps(wf)
    commit = next(p for p in pasos if "git push" in p.get("run", ""))
    assert "for attempt in 1 2 3 4 5" in commit["run"]
    assert wf["concurrency"]["group"] == "vigilancia-guardia-modis"


def test_no_modifica_la_vigilancia_de_k():
    """vigilancia_sombra.py y su workflow vigilan K y están en plazo: el script nuevo los importa, no los cambia.
    S172 ronda 2 (PR B, mini auditoría MA172-101): el PR B sí cambia vigilancia_sombra.py, a propósito y en lo mínimo
    (deja de contar como K los records MODIS de la vía; tests/test_vigilancia_sombra_via_modis_s172.py). El workflow
    de esa vigilancia sigue sin tocar."""
    import subprocess
    r = subprocess.run(["git", "diff", "--name-only", "pre-s171-adopcion-modd", "HEAD", "--",
                        ".github/workflows/vigilancia-sombra.yml"],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        pytest.skip("sin el tag pre-s171-adopcion-modd en este checkout")
    assert r.stdout.strip() == ""
