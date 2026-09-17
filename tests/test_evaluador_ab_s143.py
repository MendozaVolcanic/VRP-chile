# -*- coding: utf-8 -*-
"""S143: evaluador del A/B D22/D25 (VIIRS 375), escrito ANTES de ver datos del A/B.

POR QUE. El pre-registro (docs/PREREGISTRO_AB_D22_D25_S143.md) fija tres criterios y el verificador
limpio (docs/PREREGISTRO_AB_D22_D25_S143_VERIFICADOR.md) encontro que no habia un instrumento que los
aplicara tal como estan escritos. Si el evaluador se escribe despues de mirar resultados, cada
decision de implementacion es un grado de libertad. Estos tests fijan esas decisiones con fixtures
sinteticas chicas, una por requisito del verificador:

  * hallazgo 3/17: fusion de tramos generica que avisa de solapes con contenido distinto;
  * hallazgo 15: cobertura simetrica (claves de mas y de menos) y mismo product_version;
  * hallazgo 2: perdida = el brazo no publica un objeto que pase la MISMA cota que el control;
  * hallazgo 7: toda perdida cuenta; tambien se reportan ganancias;
  * hallazgo 14: bootstrap estratificado por volcan, determinista con semilla, y margen de signo;
  * hallazgo 4: magnitud sobre pasadas publicadas por ambos; n minimo contado en las pos del
    control; una fila MIROVA por pasada, CONS antes que OCR;
  * A97: el predicado es el del dashboard con node; el cargador reproduce al del banco.
"""
import json
import math
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIR_EVAL = os.path.join(ROOT, "experiments", "_s143_evaluador")
for p in (ROOT, os.path.join(ROOT, "scripts"), DIR_EVAL):
    if p not in sys.path:
        sys.path.insert(0, p)

import fusionar  # noqa: E402
import evaluar  # noqa: E402

HAY_NODE = shutil.which("node") is not None


# ------------------------------------------------------------------ utilidades de fixtures
def _rec(dt, sensor="VIIRS_NOAA20", **kw):
    r = {"datetime_utc": dt, "sensor": sensor, "product_version": "standard"}
    r.update(kw)
    return r


def _escribir(base, nombre_dir, vol, records):
    d = os.path.join(base, nombre_dir)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{vol}.json"), "w", encoding="utf-8") as fh:
        json.dump({"volcano": vol, "records": records}, fh)


def _pasada(vol, noche, hora="03:00", pub=0, lab="neg_limpio", cen=None, disp=0.0,
            art=0, predisp=None, sensor="VIIRS_NOAA20", mir_vrp=None, cen_final=None):
    dtu = f"{noche} {hora}"
    return {"vol": vol, "noche": noche, "b": "VIIRS375", "datetime_utc": dtu, "sensor": sensor,
            "clave": (vol, dtu, sensor), "lab": lab, "pub": pub, "art": art,
            "predisp": pub if predisp is None else predisp, "disp": disp,
            "pos_centroide": cen, "pos_final_hotspot_si_test1": cen if cen_final is None else cen_final,
            "mir_vrp": mir_vrp}


# ------------------------------------------------------------------ fusion de tramos
def test_fusion_une_tramos_y_avisa_solape_conflictivo(tmp_path):
    t1, t2, out = tmp_path / "t1", tmp_path / "t2", tmp_path / "out"
    a = _rec("2026-06-01 03:00", vrp_mw=0.1)
    b = _rec("2026-06-02 03:00", vrp_mw=0.2)
    b_distinto = _rec("2026-06-02 03:00", vrp_mw=9.9)
    c = _rec("2026-07-01 03:00", vrp_mw=0.3)
    _escribir(t1, "pfx-_brazo_x-Isluga", "Isluga", [a, b])
    _escribir(t2, "pfx-_brazo_x-Isluga", "Isluga", [b_distinto, c])
    inf = fusionar.fusionar([(str(t1), ""), (str(t2), "")], "pfx-", ["_brazo_x"], ["Isluga"],
                            str(out))
    assert len(inf["conflictos"]) == 1
    assert inf["conflictos"][0]["clave"] == ["2026-06-02 03:00", "VIIRS_NOAA20"]
    with open(out / "pfx-_brazo_x-Isluga" / "Isluga.json", encoding="utf-8") as fh:
        recs = json.load(fh)["records"]
    assert [r["datetime_utc"] for r in recs] == ["2026-06-01 03:00", "2026-06-02 03:00",
                                                 "2026-07-01 03:00"]


def test_fusion_solape_identico_no_es_conflicto_y_sufijo_por_tramo(tmp_path):
    base, out = tmp_path / "base", tmp_path / "out"
    a = _rec("2026-06-01 03:00", vrp_mw=0.1)
    _escribir(base, "otro-_b-Lascar__run1", "Lascar", [a])
    _escribir(base, "otro-_b-Lascar__run2", "Lascar", [a, _rec("2026-08-01 03:00")])
    inf = fusionar.fusionar([(str(base), "__run1"), (str(base), "__run2")], "otro-", ["_b"],
                            ["Lascar"], str(out))
    assert inf["conflictos"] == []
    assert inf["duplicados_identicos"] == 1
    assert inf["archivos"][0]["n_fusion"] == 2


def test_fusion_falta_un_tramo_no_escribe_salida(tmp_path):
    t1, t2, out = tmp_path / "t1", tmp_path / "t2", tmp_path / "out"
    _escribir(t1, "p-_b-Isluga", "Isluga", [_rec("2026-06-01 03:00")])
    inf = fusionar.fusionar([(str(t1), ""), (str(t2), "")], "p-", ["_b"], ["Isluga"], str(out))
    assert inf["faltantes"] and not (out / "p-_b-Isluga").exists()


def test_parse_tramo():
    assert fusionar.parse_tramo("C:/x/y::__run5") == ("C:/x/y", "__run5")
    assert fusionar.parse_tramo("/x/y") == ("/x/y", "")


# ------------------------------------------------------------------ cobertura
def test_cobertura_simetrica_detecta_claves_de_mas_y_de_menos():
    ctrl = {("2026-06-01 03:00", "S"): "standard", ("2026-06-02 03:00", "S"): "standard"}
    brazo = {("2026-06-02 03:00", "S"): "standard", ("2026-06-03 03:00", "S"): "standard"}
    det, desp = evaluar.cobertura({"_c": {"V": ctrl}, "_b": {"V": brazo}}, "_c", ["V"])
    assert det["V"]["_b"]["solo_control"] == 1
    assert det["V"]["_b"]["solo_brazo"] == 1
    assert "V" in desp


def test_cobertura_product_version_distinto_es_desparejo():
    ctrl = {("2026-06-01 03:00", "S"): "standard"}
    brazo = {("2026-06-01 03:00", "S"): "nrt"}
    det, desp = evaluar.cobertura({"_c": {"V": ctrl}, "_b": {"V": brazo}}, "_c", ["V"])
    assert det["V"]["_b"]["product_version_distinto"] == 1
    assert "V" in desp


def test_cobertura_pareja_y_archivo_faltante():
    k = {("2026-06-01 03:00", "S"): "standard"}
    det, desp = evaluar.cobertura({"_c": {"V": k, "W": k}, "_b": {"V": dict(k)}}, "_c", ["V", "W"])
    assert "V" not in desp
    assert "W" in desp  # el brazo no tiene archivo de W


# ------------------------------------------------------------------ criterio 1
CENTRO = (-19.0, -68.0)


def _desplazado(km_norte):
    return (CENTRO[0] + km_norte / 111.195, CENTRO[1])


def test_estado_noches_aplica_cota_desde_mirova_center():
    noches_alerta = {"V": {"2026-07-01"}}
    dist = {("V", "2026-07-01"): [1.0]}
    pas = [_pasada("V", "2026-07-01", pub=1, cen=_desplazado(1.2), lab="pos"),
           _pasada("V", "2026-07-01", hora="04:00", pub=1, cen=_desplazado(4.0), lab="pos")]
    est = evaluar.estado_noches(pas, noches_alerta, dist, {"V": CENTRO}, 0.55)
    assert est["V"]["pub_cota"] == {"2026-07-01"}
    # objeto lejano solo: publica pero no pasa la cota
    est2 = evaluar.estado_noches(pas[1:], noches_alerta, dist, {"V": CENTRO}, 0.55)
    assert est2["V"]["pub"] == {"2026-07-01"} and est2["V"]["pub_cota"] == set()
    assert abs(est2["V"]["descartadas"]["2026-07-01"] - 3.0) < 0.01


def test_posiciones_de_record_segun_la_fuente():
    """Para un record del Test 1 integrado la posicion oficial del proyecto es `final_hotspot`: el
    `primary_cluster` de esos records es el footprint de la integral, arrastrado por la topografia
    (A69, S106/A84, `latestDetection` en frontend/index.html). Para el resto, el centroide."""
    pc = {"centroid_lat": -23.0, "centroid_lon": -67.0}
    t1 = {"primary_cluster": pc, "final_hotspot_source": "test1_roi",
          "final_hotspot_lat": -23.02, "final_hotspot_lon": -67.03}
    ctx = {"primary_cluster": pc, "final_hotspot_source": "ctx_cluster",
           "final_hotspot_lat": -23.02, "final_hotspot_lon": -67.03}
    sin_fh = {"primary_cluster": pc, "final_hotspot_source": "test1_roi"}
    assert evaluar.posiciones_de_record(t1) == {"pos_centroide": (-23.0, -67.0),
                                                "pos_final_hotspot_si_test1": (-23.02, -67.03)}
    assert evaluar.posiciones_de_record(ctx) == {"pos_centroide": (-23.0, -67.0),
                                                 "pos_final_hotspot_si_test1": (-23.0, -67.0)}
    # sin coordenadas de final_hotspot no se puede reanclar: queda el centroide
    assert evaluar.posiciones_de_record(sin_fh)["pos_final_hotspot_si_test1"] == (-23.0, -67.0)
    assert evaluar.posiciones_de_record({})["pos_centroide"] is None


def test_estado_noches_cambia_segun_el_campo_de_posicion():
    """El mismo record, la misma cota: pasa medido desde el centroide y no pasa desde el
    final_hotspot. Cual de los dos manda es una decision abierta, no una constante del codigo."""
    noches_alerta = {"V": {"2026-07-01"}}
    dist = {("V", "2026-07-01"): [1.0]}
    p = _pasada("V", "2026-07-01", pub=1, cen=_desplazado(1.2), cen_final=_desplazado(4.0),
                lab="pos")
    e_cen = evaluar.estado_noches([p], noches_alerta, dist, {"V": CENTRO}, 0.55,
                                  campo="pos_centroide")
    e_fh = evaluar.estado_noches([p], noches_alerta, dist, {"V": CENTRO}, 0.55,
                                 campo="pos_final_hotspot_si_test1")
    assert e_cen["V"]["pub_cota"] == {"2026-07-01"} and e_cen["V"]["descartadas"] == {}
    assert e_fh["V"]["pub_cota"] == set()
    assert abs(e_fh["V"]["descartadas"]["2026-07-01"] - 3.0) < 0.01
    # el campo por defecto es el centroide, la semantica de S135
    assert evaluar.estado_noches([p], noches_alerta, dist, {"V": CENTRO}, 0.55) == e_cen
    assert evaluar.CAMPOS_POSICION["centroide"] == "pos_centroide"
    assert evaluar.CAMPOS_POSICION["final_hotspot_si_test1"] == "pos_final_hotspot_si_test1"


def test_perdida_exige_la_misma_cota_en_el_brazo():
    """Hallazgo 2: el brazo publica esa noche pero un objeto a 3 km de lo que vio MIROVA."""
    noches_alerta = {"V": {"2026-07-01", "2026-07-02"}}
    dist = {("V", "2026-07-01"): [1.0], ("V", "2026-07-02"): [1.0]}
    ctrl = [_pasada("V", "2026-07-01", pub=1, cen=_desplazado(1.0), lab="pos"),
            _pasada("V", "2026-07-02", pub=1, cen=_desplazado(1.0), lab="pos")]
    brazo = [_pasada("V", "2026-07-01", pub=1, cen=_desplazado(4.0), lab="pos"),
             _pasada("V", "2026-07-02", pub=0, cen=_desplazado(1.0), lab="pos")]
    c = {"V": CENTRO}
    r = evaluar.criterio1(evaluar.estado_noches(ctrl, noches_alerta, dist, c, 0.55),
                          evaluar.estado_noches(brazo, noches_alerta, dist, c, 0.55))
    assert r["perdidas"] == [{"volcan": "V", "fecha": "2026-07-01"},
                             {"volcan": "V", "fecha": "2026-07-02"}]
    assert r["perdidas_sin_filtro_brazo"] == [{"volcan": "V", "fecha": "2026-07-02"}]
    assert r["n_perdidas"] == 2 and r["cumple"] is False


def test_ganancias_y_cumple_sin_perdidas():
    noches_alerta = {"V": {"2026-07-01", "2026-07-02"}}
    dist = {("V", "2026-07-01"): [1.0], ("V", "2026-07-02"): [1.0]}
    ctrl = [_pasada("V", "2026-07-01", pub=1, cen=_desplazado(1.0), lab="pos")]
    brazo = [_pasada("V", "2026-07-01", pub=1, cen=_desplazado(1.1), lab="pos"),
             _pasada("V", "2026-07-02", pub=1, cen=_desplazado(0.9), lab="pos")]
    c = {"V": CENTRO}
    r = evaluar.criterio1(evaluar.estado_noches(ctrl, noches_alerta, dist, c, 0.55),
                          evaluar.estado_noches(brazo, noches_alerta, dist, c, 0.55))
    assert r["n_perdidas"] == 0 and r["cumple"] is True
    assert r["ganancias"] == [{"volcan": "V", "fecha": "2026-07-02"}]


def test_noche_sin_alerta_no_es_confirmada_y_sin_distancia_pasa():
    """Sin distancia de MIROVA la cota no se puede calcular: se acepta y se cuenta aparte."""
    noches_alerta = {"V": {"2026-07-01"}}
    pas = [_pasada("V", "2026-07-01", pub=1, cen=_desplazado(9.0), lab="pos"),
           _pasada("V", "2026-07-05", pub=1, cen=_desplazado(1.0), lab="neg_limpio")]
    est = evaluar.estado_noches(pas, noches_alerta, {}, {"V": CENTRO}, 0.55)
    assert est["V"]["pub_cota"] == {"2026-07-01"}
    assert est["V"]["sin_cota"] == {"2026-07-01"}


# ------------------------------------------------------------------ criterio 2
def _grupos_ruidosos(n_noches=120):
    """Fixture con suficientes noches y suficiente varianza para que el percentil distinga dos
    semillas: con 5 noches el intervalo es tan grueso que dos corridas distintas coinciden y el
    test de determinismo pasa aunque se saque la semilla (H4 del verificador externo).

    Las noches tienen entre 1 y 4 pasadas y el brazo publica una fraccion variable de cada una, asi
    que la razon cae en una grilla fina: con 120 noches por volcan, 30 semillas dan 30 intervalos
    distintos (medido antes de fijar la fixture)."""
    grupos = {}
    for vol, sesgo in (("A", 0), ("B", 1)):
        grupos[vol] = []
        for i in range(n_noches):
            n_pasadas = 1 + (i + sesgo) % 4
            grupos[vol].append((n_pasadas, n_pasadas, (i * 7 + sesgo) % (n_pasadas + 1)))
    return grupos


def test_bootstrap_estratificado_determinista_con_semilla():
    grupos = _grupos_ruidosos()
    x = evaluar.bootstrap_estratificado(grupos, B=500, semilla=143)
    y = evaluar.bootstrap_estratificado(grupos, B=500, semilla=143)
    assert x == y
    assert x[0] < x[1], "el intervalo tiene que tener ancho, si no el test no distingue semillas"


def test_bootstrap_cambia_con_la_semilla():
    """Si el intervalo no dependiera de la semilla, el test de determinismo no probaria nada:
    pasaria igual con `default_rng()` sin semilla (H4). Con cuatro semillas, cuatro intervalos."""
    grupos = _grupos_ruidosos()
    vistos = [evaluar.bootstrap_estratificado(grupos, B=500, semilla=s) for s in (143, 7, 2026, 99)]
    assert len(set(vistos)) == len(vistos)


def test_bootstrap_remuestrea_dentro_de_cada_volcan():
    """Si todas las noches de un volcan son iguales entre si, remuestrear DENTRO del volcan no
    cambia nada y el intervalo colapsa al punto. Un bootstrap sobre el total mezclado cambiaria la
    composicion por volcan y abriria el intervalo: este test distingue los dos."""
    grupos = {"A": [(2, 2, 0)] * 10, "B": [(2, 0, 0)] * 3}
    lo, hi = evaluar.bootstrap_estratificado(grupos, B=300, semilla=7)
    punto = (0 - 20) / 26
    assert math.isclose(lo, punto) and math.isclose(hi, punto)


def test_criterio2_mismas_pasadas_margen_y_acompanantes():
    ctrl = [_pasada("A", "2026-06-01", pub=1), _pasada("A", "2026-06-01", hora="04:00", pub=1),
            _pasada("A", "2026-06-02", pub=0),
            _pasada("B", "2026-06-01", pub=0, art=1, predisp=1),
            _pasada("B", "2026-06-03", pub=1, lab="pos")]
    brazo = [dict(p) for p in ctrl]
    brazo[0]["pub"] = 0
    brazo[0]["predisp"] = 0
    brazo[3]["art"] = 0
    brazo[3]["predisp"] = 0
    brazo.append(_pasada("B", "2026-06-09", pub=1))  # clave que el control no tiene: no entra
    est = {"A": "focal", "B": "nevado"}
    r = evaluar.criterio2(ctrl, brazo, est.get, B=200, semilla=143)
    t = r["total"]
    assert t["n"] == 4
    assert t["pub_control"] == 2 and t["pub_brazo"] == 1
    assert math.isclose(t["dif"], -0.25)
    assert t["solo_brazo"] == 0 and t["solo_control"] == 1 and t["margen_signo"] == 1
    assert r["por_estrato"]["focal"]["n"] == 3 and r["por_estrato"]["nevado"]["n"] == 1
    assert r["por_volcan"]["B"]["dif"] == 0.0
    ac = r["acompanantes_neg_limpio"]
    assert ac["tasa_art_control"] == 0.25 and ac["tasa_art_brazo"] == 0.0
    assert ac["tasa_predisplay_control"] == 0.75 and ac["tasa_predisplay_brazo"] == 0.25


def test_criterio2_cumple_exige_ic_total_bajo_cero_y_ningun_estrato_positivo():
    ctrl = [_pasada("A", f"2026-06-{d:02d}", pub=1) for d in range(1, 21)]
    ctrl += [_pasada("B", f"2026-06-{d:02d}", pub=0) for d in range(1, 6)]
    brazo = [dict(p, pub=0) for p in ctrl[:20]] + [dict(p) for p in ctrl[20:]]
    r = evaluar.criterio2(ctrl, brazo, {"A": "focal", "B": "nevado"}.get, B=500, semilla=143)
    assert r["total"]["ic95"][1] < 0 and r["cumple"] is True
    brazo[-1]["pub"] = 1  # una pasada nevada que sube: el estrato queda positivo
    r2 = evaluar.criterio2(ctrl, brazo, {"A": "focal", "B": "nevado"}.get, B=500, semilla=143)
    assert r2["por_estrato"]["nevado"]["dif"] > 0 and r2["cumple"] is False
    assert r2["por_estrato"]["nevado"]["margen_signo"] == 1


def test_criterio2_no_cumple_si_el_intervalo_cruza_el_cero():
    """La regla del pre-registro es que el intervalo TOTAL quede entero bajo cero. Con el extremo
    bajo alcanzaria cualquier diferencia negativa: aca la puntual es negativa y el intervalo cruza."""
    ctrl = [_pasada("A", "2026-06-01", pub=1), _pasada("A", "2026-06-01", hora="04:00", pub=1),
            _pasada("A", "2026-06-02", pub=0), _pasada("A", "2026-06-03", pub=0),
            _pasada("A", "2026-06-04", pub=0), _pasada("A", "2026-06-05", pub=0)]
    brazo = [dict(p) for p in ctrl]
    brazo[0]["pub"] = 0
    brazo[1]["pub"] = 0          # la noche 06-01 aporta -2
    brazo[2]["pub"] = 1          # la noche 06-02 aporta +1
    r = evaluar.criterio2(ctrl, brazo, {"A": "focal"}.get, B=2000, semilla=143)
    t = r["total"]
    assert t["dif"] < 0, "la diferencia puntual es negativa"
    assert t["ic95"][0] < 0 < t["ic95"][1], "el intervalo cruza el cero"
    assert r["cumple"] is False


# ------------------------------------------------------------------ criterio 3
def test_fila_mirova_cons_antes_que_ocr():
    cons = {"tipo": "ALERTA_TERMICA", "source": "CONS", "vrp_mw": 1.0, "fecha_utc": "2026-06-01 03:01:00"}
    ocr = {"tipo": "ALERTA_TERMICA_OCR", "source": "OCR", "vrp_mw": 2.0, "fecha_utc": "2026-06-01 03:00:00"}
    rut = {"tipo": "RUTINA", "source": "CONS", "vrp_mw": 0.0, "fecha_utc": "2026-06-01 03:00:00"}
    assert evaluar.fila_mirova([ocr, cons])["vrp_mw"] == 1.0
    assert evaluar.fila_mirova([rut, ocr])["vrp_mw"] == 2.0
    assert evaluar.fila_mirova([rut]) is None


def test_criterio3_decisivo_sobre_pasadas_publicadas_por_ambos():
    ctrl = [_pasada("A", "2026-06-01", lab="pos", pub=1, disp=1.0, mir_vrp=1.0),
            _pasada("A", "2026-06-02", lab="pos", pub=1, disp=0.5, mir_vrp=1.0),
            _pasada("A", "2026-06-03", lab="pos", pub=1, disp=0.1, mir_vrp=1.0)]
    brazo = [dict(ctrl[0], disp=0.9), dict(ctrl[1], disp=0.6), dict(ctrl[2], pub=0, disp=0.0)]
    r = evaluar.criterio3(ctrl, brazo, {"A": "focal"}.get, n_min=30)
    t = r["total"]
    assert t["n_pares_decisivo"] == 2
    assert math.isclose(t["mediana_control_decisivo"], 0.75)
    assert math.isclose(t["mediana_brazo_decisivo"], 0.75)
    assert t["n_control_informativo"] == 3 and math.isclose(t["mediana_control_informativo"], 0.5)
    assert t["n_brazo_informativo"] == 2
    assert r["cumple"] is True


def test_criterio3_n_min_se_cuenta_en_las_pos_del_control():
    """Un volcan con muchas pos en el control no escapa al chequeo porque el brazo deje de publicar."""
    ctrl = [_pasada("A", f"2026-06-{d:02d}", lab="pos", pub=1, disp=1.0, mir_vrp=1.0)
            for d in range(1, 31)]
    brazo = [dict(p, disp=0.5) if i < 2 else dict(p, pub=0, disp=0.0) for i, p in enumerate(ctrl)]
    r = evaluar.criterio3(ctrl, brazo, {"A": "focal"}.get, n_min=30)
    v = r["por_volcan"]["A"]
    assert v["n_pos_control"] == 30 and v["evaluado"] is True
    assert v["n_pares_decisivo"] == 2
    assert v["empeora_mas_de_tolerancia"] is True and r["cumple"] is False


def test_criterio3_no_cumple_si_el_brazo_se_aleja_de_uno():
    """La direccion de la desigualdad decide: el brazo no puede alejarse de 1 mas que el control."""
    ctrl = [_pasada("A", f"2026-06-{d:02d}", lab="pos", pub=1, disp=1.0, mir_vrp=1.0)
            for d in range(1, 6)]
    peor = [dict(p, disp=0.5) for p in ctrl]
    mejor = [dict(p, disp=1.0) for p in [dict(q, disp=0.5) for q in ctrl]]
    r_peor = evaluar.criterio3(ctrl, peor, {"A": "focal"}.get, n_min=30)
    assert r_peor["total"]["dist_a_1_brazo"] > r_peor["total"]["dist_a_1_control"]
    assert r_peor["cumple"] is False
    ctrl_lejos = [dict(p, disp=0.5) for p in ctrl]
    r_mejor = evaluar.criterio3(ctrl_lejos, mejor, {"A": "focal"}.get, n_min=30)
    assert r_mejor["total"]["dist_a_1_brazo"] < r_mejor["total"]["dist_a_1_control"]
    assert r_mejor["cumple"] is True


def test_criterio3_volcan_evaluado_sin_pares_decisivos_cuenta_como_que_empeora():
    """Dejar de publicar no puede ser la forma de escapar al chequeo por volcan: el total lo dan
    los pares del volcan B y, sin el castigo, el brazo cumpliria pese a apagar el volcan A."""
    ctrl = [_pasada("A", f"2026-06-{d:02d}", lab="pos", pub=1, disp=1.0, mir_vrp=1.0)
            for d in range(1, 31)]
    ctrl += [_pasada("B", f"2026-07-{d:02d}", lab="pos", pub=1, disp=1.0, mir_vrp=1.0)
             for d in range(1, 6)]
    brazo = [dict(p, pub=0, disp=0.0) if p["vol"] == "A" else dict(p) for p in ctrl]
    est = {"A": "focal", "B": "focal"}.get
    r = evaluar.criterio3(ctrl, brazo, est, n_min=30)
    assert r["total"]["n_pares_decisivo"] == 5
    assert r["total"]["dist_a_1_brazo"] == r["total"]["dist_a_1_control"]
    assert r["por_volcan"]["A"]["evaluado"] is True
    assert r["por_volcan"]["A"]["n_pares_decisivo"] == 0
    assert r["por_volcan"]["A"]["empeora_mas_de_tolerancia"] is True
    assert r["volcanes_que_empeoran"] == ["A"] and r["cumple"] is False


def test_criterio1_una_sola_perdida_ya_no_cumple():
    """El umbral es 0, no 'casi 0' (decision de Nicolas del 2026-09-07)."""
    noches_alerta = {"V": {"2026-07-01", "2026-07-02"}}
    dist = {("V", "2026-07-01"): [1.0], ("V", "2026-07-02"): [1.0]}
    c = {"V": CENTRO}
    ctrl = [_pasada("V", "2026-07-01", pub=1, cen=_desplazado(1.0), lab="pos"),
            _pasada("V", "2026-07-02", pub=1, cen=_desplazado(1.0), lab="pos")]
    brazo = [dict(ctrl[0]), dict(ctrl[1], pub=0)]
    r = evaluar.criterio1(evaluar.estado_noches(ctrl, noches_alerta, dist, c, 0.55),
                          evaluar.estado_noches(brazo, noches_alerta, dist, c, 0.55))
    assert r["n_perdidas"] == 1 and r["cumple"] is False


# ------------------------------------------------------------------ parametros congelados
def test_fusion_acepta_un_prefijo_por_tramo(tmp_path):
    """El workflow del A/B nombra los artefactos con el tramo adentro (s143ab-t1-, s143ab-t2-), asi
    que la fusion tiene que aceptar un prefijo por tramo o no encuentra el segundo."""
    import fusionar as fus
    def escribir(base, prefijo, dt):
        d = os.path.join(base, f"{prefijo}_brazo-Isluga")
        os.makedirs(d)
        with open(os.path.join(d, "Isluga.json"), "w", encoding="utf-8") as fh:
            json.dump({"volcano": "Isluga", "records": [{"datetime_utc": dt, "sensor": "VIIRS_SNPP"}]}, fh)
    t1, t2 = str(tmp_path / "t1"), str(tmp_path / "t2")
    escribir(t1, "s143ab-t1-", "2026-06-02 05:00")
    escribir(t2, "s143ab-t2-", "2026-07-20 05:00")
    out = str(tmp_path / "fus")
    inf = fus.fusionar([(t1, ""), (t2, "")], ["s143ab-t1-", "s143ab-t2-"], ["_brazo"], ["Isluga"], out)
    assert inf["faltantes"] == [], inf
    with open(os.path.join(out, "s143ab-t1-_brazo-Isluga", "Isluga.json"), encoding="utf-8") as fh:
        assert len(json.load(fh)["records"]) == 2
    # con un solo prefijo, el segundo tramo no aparece
    inf2 = fus.fusionar([(t1, ""), (t2, "")], "s143ab-t1-", ["_brazo"], ["Isluga"], str(tmp_path / "fus2"))
    assert inf2["faltantes"], "un prefijo unico deberia dejar el tramo 2 como faltante"


def test_parametros_congelados_son_los_del_preregistro():
    """H1: los parametros de la corrida no pueden elegirse despues de ver datos. Viven en
    `experiments/_s143_evaluador/parametros.json`, versionado, y el evaluador los lee por defecto."""
    with open(os.path.join(DIR_EVAL, "parametros.json"), encoding="utf-8") as fh:
        p = json.load(fh)
    assert p["ventana"] == ["2026-06-01", "2026-08-31"]
    # Nueve desde la v2 del pre-registro: Chaitén entra al estrato nevado (mayor denominador de
    # negativos, 221, y única magnitud que hoy se pasa arriba de 1, que es el contraejemplo de un
    # cambio de fondo que la sube). Hallazgo 12 del verificador del pre-registro.
    assert p["volcanes"] == ["Isluga", "Lascar", "Lastarria", "PlanchonPeteroa",
                             "PuyehueCordonCaulle", "Tupungatito", "Chaiten", "Villarrica",
                             "NevadosDeChillan"]
    assert p["control"] == "_s142_ab_control"
    assert p["brazos"] == ["_s142_ab_control", "_s142_ab_literal", "_s142_ab_lit_sin_fondo",
                           "_s142_ab_lit_con_compuerta", "_s142_ab_lit_sp_suelto",
                           "_s142_ab_lit_keep_peak"]
    assert p["prefijo"] == "s143ab-"
    assert p["cota_km"] == 0.55
    assert p["B"] == 10000
    assert p["semilla"] == 143
    assert p["n_min_magnitud"] == 30
    assert p["tol_magnitud"] == 0.05
    # decision abierta de Nicolas: por ahora decide el centroide, la semantica de S135
    assert p["campo_posicion_cota"] == "centroide"
    assert evaluar.CAMPO_POSICION_DEFECTO == p["campo_posicion_cota"]
    assert evaluar.argumentos(dir="x").campo_posicion == p["campo_posicion_cota"]
    # el modulo usa exactamente esos valores, no una copia que pueda driftear
    assert evaluar.PRESUPUESTO_COTA_KM == p["cota_km"]
    assert evaluar.TOL_MAGNITUD == p["tol_magnitud"]
    assert evaluar.B_DEFECTO == p["B"]
    assert evaluar.SEMILLA_DEFECTO == p["semilla"]
    assert evaluar.N_MIN_MAGNITUD == p["n_min_magnitud"]
    assert evaluar.PARAMETROS == p


def test_la_salida_copia_los_parametros_congelados_con_su_sha():
    proc = evaluar.procedencia_archivo(os.path.join(DIR_EVAL, "parametros.json"))
    assert proc["archivo"] == "experiments/_s143_evaluador/parametros.json"
    assert proc["blob"] and len(proc["blob"]) == 40


# ------------------------------------------------------------------ fuentes del repo
def test_estratos_y_radios_para_los_once_tier_a():
    import build_c2ab_windows as b
    vols = b.FOCAL + b.NEVADO
    assert len(vols) == 11
    rad = evaluar.radios(vols)
    for v in vols:
        assert rad[v]["inner"] > 0
        lat, lon = rad[v]["mirova_center"]
        assert -60 < lat < -15 and -80 < lon < -60
        assert evaluar.estrato_de(v) in ("focal", "nevado")


def test_seguimiento_estado_de_noches_por_brazo():
    estados = {"_c": {"V": {"pub_cota": {"2026-07-01"}, "pub": {"2026-07-01"}}},
               "_d": {"V": {"pub_cota": set(), "pub": {"2026-07-01"}}}}
    s = evaluar.seguimiento(estados, [{"volcan": "V", "fecha": "2026-07-01"}])
    assert s[0]["_c"] == {"publica_cota": True, "publica": True}
    assert s[0]["_d"] == {"publica_cota": False, "publica": True}


def test_informe_markdown_sale_del_json_y_sin_guiones_largos():
    noches_alerta = {"V": {"2026-07-01"}}
    dist = {("V", "2026-07-01"): [1.0]}
    c = {"V": CENTRO}
    ctrl = [_pasada("V", "2026-07-01", pub=1, cen=_desplazado(1.0), lab="pos", disp=1.0, mir_vrp=2.0),
            _pasada("V", "2026-07-02", pub=1)]
    brazo = [dict(ctrl[0], pub=0, disp=0.0), dict(ctrl[1], pub=0)]
    est = {"_c": evaluar.estado_noches(ctrl, noches_alerta, dist, c, 0.55),
           "_b": evaluar.estado_noches(brazo, noches_alerta, dist, c, 0.55)}
    res = {
        "meta": {"ventana": ["2026-06-01", "2026-08-31"], "brazos": ["_c", "_b"], "control": "_c",
                 "volcanes": ["V"], "volcanes_evaluados": ["V"], "estratos": {"V": "focal"},
                 "procedencia": {"evaluador_commit": None}, "parametros": {"B": 100, "semilla": 143}},
        "cobertura": {"detalle": {}, "excluidos": {}},
        "noches_confirmadas": evaluar.resumen_confirmadas(est["_c"], {"V": "focal"}.get),
        "brazos": {"_b": {"criterio1": evaluar.criterio1(est["_c"], est["_b"]),
                          "criterio2": evaluar.criterio2(ctrl, brazo, {"V": "focal"}.get, B=100, semilla=143),
                          "criterio3": evaluar.criterio3(ctrl, brazo, {"V": "focal"}.get, n_min=30)}},
        "seguimiento": evaluar.seguimiento(est, [{"volcan": "V", "fecha": "2026-07-01"}]),
    }
    res = json.loads(json.dumps(res, default=evaluar.json_default))
    md = evaluar.informe_markdown(res)
    assert "\u2014" not in md and "\u2013" not in md
    assert "_b" in md and "2026-07-01" in md
    assert res["noches_confirmadas"]["total"] == 1


# ------------------------------------------------------------------ node: predicado y cargador
@pytest.mark.skipif(not HAY_NODE, reason="node no esta instalado: el predicado del dashboard se ejecuta con node (A97)")
def test_cargador_reproduce_al_banco_de_paridad(tmp_path, monkeypatch):
    """El evaluador no reescribe el predicado ni la seleccion de records: sobre el mismo JSON debe
    enviar a node los mismos casos y obtener las mismas `disp`/`pub` que banco_paridad."""
    import banco_paridad as bp
    vol = "Lascar"
    recs = [
        _rec("2026-06-10 06:10", vrp_mw=0.4, distance_class="summit", t_max_k=300,
             primary_cluster={"vrp_mw": 0.4, "centroid_dist_km": 1.0, "n_pixels": 2,
                              "centroid_lat": -23.37, "centroid_lon": -67.73},
             anomaly_pixels=[{"lat": -23.37, "lon": -67.73, "vrp_mw": 0.4, "bt_k": 300}]),
        _rec("2026-06-10 06:12", sensor="VIIRS_NOAA20_750", vrp_mw=0.0, distance_class="far",
             primary_cluster=None),
        _rec("2026-06-11 16:00", vrp_mw=0.3, distance_class="summit"),  # diurna: fuera
    ]
    _escribir(tmp_path, "data", vol, recs)
    monkeypatch.setattr(bp, "DATA", tmp_path / "data")
    monkeypatch.setattr(bp, "VOLS", [vol])
    coords = bp._coords_por_volcan()
    inner = {vol: 5.0}
    ventana = ("2026-06-01", "2026-06-30")
    esperado = bp.cargar_nuestros(coords, inner, ventana)
    pas = evaluar.construir_pasadas({vol: recs}, coords, inner, ventana,
                                    buckets=("MODIS", "VIIRS375", "VIIRS750"))
    assert len(pas) == len(esperado) == 2
    for p, e in zip(pas, esperado):
        assert (p["vol"], p["b"], p["dt"], p["disp"], p["pub"]) == (e["vol"], e["b"], e["dt"], e["disp"], e["pub"])
    assert pas[0]["pub"] == 1 and pas[0]["summit"] == 1 and pas[0]["valid"] == 1


@pytest.mark.skipif(not HAY_NODE, reason="node no esta instalado: el predicado del dashboard se ejecuta con node (A97)")
def test_identidad_del_predicado_node():
    import banco_paridad as bp
    assert bp.control_identidad_predicado() == ([0, 1, 1, 1, 0], [1, 0])


# ------------------------------------------------------------------ de punta a punta
CABECERA_CONS = ("timestamp,Fecha_Satelite_UTC,Fecha_Captura_Chile,Volcan,Sensor,VRP_MW,"
                 "Distancia_km,Tipo_Registro,Clasificacion Mirova,Ruta Foto,Fecha_Proceso_GitHub,"
                 "Ultima_Actualizacion,Editado,Nota_Validacion")


def _fila_ref(vol, fecha, tipo, vrp, dist):
    return (f"0,{fecha},{fecha},{vol},VIIRS375,{vrp},{dist},{tipo},NULO,No descargada,{fecha},"
            f"{fecha},NO,")


def _record_publicable(dt, lat, lon):
    return _rec(dt, vrp_mw=0.4, distance_class="summit", t_max_k=300,
                primary_cluster={"vrp_mw": 0.4, "centroid_dist_km": 0.5, "n_pixels": 2,
                                 "centroid_lat": lat, "centroid_lon": lon},
                anomaly_pixels=[{"lat": lat, "lon": lon, "vrp_mw": 0.4, "bt_k": 300}])


@pytest.mark.skipif(not HAY_NODE, reason="node no esta instalado: el predicado del dashboard se ejecuta con node (A97)")
def test_evaluar_excluye_del_veredicto_al_volcan_con_cobertura_despareja(tmp_path):
    """De punta a punta: un volcan al que al brazo le falta una pasada no entra al veredicto, su
    'perdida' seria del experimento y no del algoritmo."""
    ctrl, brazo = "_ctrl", "_brazo"
    centros = evaluar.radios(["Lascar", "Lastarria"])
    recs = {}
    for vol in ("Lascar", "Lastarria"):
        lat, lon = centros[vol]["mirova_center"]
        recs[vol] = [_record_publicable("2026-06-01 05:00", lat, lon),
                     _record_publicable("2026-06-02 05:00", lat, lon)]
    art = tmp_path / "art"
    for arm in (ctrl, brazo):
        for vol, rs in recs.items():
            if arm == brazo and vol == "Lastarria":
                rs = rs[:1]          # al brazo le falta una pasada de Lastarria
            _escribir(art, f"{arm}-{vol}", vol, rs)
    cons = tmp_path / "cons.csv"
    filas = [CABECERA_CONS]
    for vol in ("Lascar", "Lastarria"):
        filas.append(_fila_ref(vol, "2026-06-01 05:00:00", "ALERTA_TERMICA", "1.0", "0.5"))
        filas.append(_fila_ref(vol, "2026-06-02 05:00:00", "RUTINA", "0.0", "0.0"))
    cons.write_text("\n".join(filas) + "\n", encoding="utf-8")
    ocr = tmp_path / "ocr.csv"
    ocr.write_text(CABECERA_CONS + "\n", encoding="utf-8")

    a = evaluar.argumentos(dir=str(art), prefijo="", brazos=[ctrl, brazo], control=ctrl,
                           volcanes=["Lascar", "Lastarria"], inicio="2026-06-01", fin="2026-06-30",
                           ref_cons=str(cons), ref_ocr=str(ocr), B=200)
    res = evaluar.evaluar(a)
    assert "Lastarria" in res["cobertura"]["excluidos"]
    assert res["meta"]["volcanes_evaluados"] == ["Lascar"]
    assert list(res["noches_confirmadas"]["por_volcan"]) == ["Lascar"]
    assert list(res["brazos"][brazo]["criterio1"]["por_volcan"]) == ["Lascar"]
    assert res["controles_instrumento"]["identidad_predicado_node"] is True
    assert res["meta"]["parametros_congelados"]["contenido"] == evaluar.PARAMETROS
    assert res["meta"]["referencia_fijada_por_sha"] is False  # la corrida usa CSV locales


def _mover(lat, lon, km_norte):
    return (lat + km_norte / 111.195, lon)


@pytest.mark.skipif(not HAY_NODE, reason="node no esta instalado: el predicado del dashboard se ejecuta con node (A97)")
def test_evaluar_reporta_los_dos_campos_de_posicion_y_decide_con_el_parametro(tmp_path):
    """El brazo publica un record del Test 1 cuyo centroide cae donde MIROVA informo pero cuyo
    `final_hotspot` esta a 3 km: con un campo la noche se conserva y con el otro se pierde. El JSON
    trae los dos y el que decide sale de `parametros.json`."""
    ctrl, brazo = "_ctrl", "_brazo"
    vol, vol2 = "Lascar", "Lastarria"
    rad = evaluar.radios([vol, vol2])
    art, filas = tmp_path / "art", [CABECERA_CONS]
    # Lascar: el control publica un cumulo contextual cerca; el brazo publica un record del Test 1
    # cuyo centroide cae igual de cerca pero cuyo final_hotspot esta a 3 km.
    cerca = _mover(*rad[vol]["mirova_center"], 0.5)
    lejos = _mover(*rad[vol]["mirova_center"], 3.5)
    rec_ctrl = _record_publicable("2026-06-01 05:00", *cerca)
    rec_ctrl["final_hotspot_source"] = "ctx_cluster"
    rec_brazo = _record_publicable("2026-06-01 05:00", *cerca)
    rec_brazo["final_hotspot_source"] = "test1_roi"
    rec_brazo["final_hotspot_lat"], rec_brazo["final_hotspot_lon"] = lejos
    _escribir(art, f"{ctrl}-{vol}", vol, [rec_ctrl])
    _escribir(art, f"{brazo}-{vol}", vol, [rec_brazo])
    filas.append(_fila_ref(vol, "2026-06-01 05:00:00", "ALERTA_TERMICA", "1.0", "0.5"))
    # Lastarria: los dos publican el MISMO record del Test 1 corrido, asi que no hay perdida pero
    # la noche deja de estar confirmada cuando la cota se mide desde el final_hotspot.
    cerca2 = _mover(*rad[vol2]["mirova_center"], 0.5)
    lejos2 = _mover(*rad[vol2]["mirova_center"], 3.5)
    rec2 = _record_publicable("2026-06-02 05:00", *cerca2)
    rec2["final_hotspot_source"] = "test1_roi"
    rec2["final_hotspot_lat"], rec2["final_hotspot_lon"] = lejos2
    for arm in (ctrl, brazo):
        _escribir(art, f"{arm}-{vol2}", vol2, [dict(rec2)])
    filas.append(_fila_ref(vol2, "2026-06-02 05:00:00", "ALERTA_TERMICA", "1.0", "0.5"))
    cons = tmp_path / "cons.csv"
    cons.write_text("\n".join(filas) + "\n", encoding="utf-8")
    ocr = tmp_path / "ocr.csv"
    ocr.write_text(CABECERA_CONS + "\n", encoding="utf-8")

    def correr(campo):
        a = evaluar.argumentos(dir=str(art), prefijo="", brazos=[ctrl, brazo], control=ctrl,
                               volcanes=[vol, vol2], inicio="2026-06-01", fin="2026-06-30",
                               ref_cons=str(cons), ref_ocr=str(ocr), B=200, campo_posicion=campo)
        return evaluar.evaluar(a)

    res = correr("centroide")
    por_campo = res["brazos"][brazo]["criterio1_por_campo_de_posicion"]
    conf = res["noches_confirmadas_por_campo_de_posicion"]
    assert set(por_campo) == {"centroide", "final_hotspot_si_test1"}
    assert por_campo["centroide"]["n_perdidas"] == 0
    assert por_campo["final_hotspot_si_test1"]["n_perdidas"] == 1
    assert conf["centroide"]["total"] == 2 and conf["final_hotspot_si_test1"]["total"] == 1
    # con el parametro congelado decide el centroide
    assert res["meta"]["campo_posicion_cota"] == "centroide"
    assert res["brazos"][brazo]["criterio1"] == por_campo["centroide"]
    assert res["noches_confirmadas"] == conf["centroide"]

    # cambiar el parametro cambia cual decide, y no cambia lo que se reporta al lado
    res2 = correr("final_hotspot_si_test1")
    assert res2["meta"]["campo_posicion_cota"] == "final_hotspot_si_test1"
    assert res2["brazos"][brazo]["criterio1"]["n_perdidas"] == 1
    assert res2["brazos"][brazo]["criterio1"] == res2["brazos"][brazo]["criterio1_por_campo_de_posicion"]["final_hotspot_si_test1"]
    assert res2["noches_confirmadas"] == res2["noches_confirmadas_por_campo_de_posicion"]["final_hotspot_si_test1"]
    assert res2["noches_confirmadas"]["total"] == 1
    assert res2["brazos"][brazo]["criterio1_por_campo_de_posicion"] == por_campo
