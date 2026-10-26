# -*- coding: utf-8 -*-
"""S162, instrumento T1, T2 y T5: evaluador común (cobertura contra MIROVA, «no observado», P1b, RUTINA).

POR QUÉ. El 2026-10-12, en V1 del A/B de D25, a los tres brazos les faltaba la pasada de NOAA-21 de las 05:18 sobre
Chillán (protegida de 8,44 MW en VIIRS 750) que producción sí tenía, y el evaluador dijo «cobertura pareja: OK»
porque partía de los records y comparaba brazos entre sí (`experiments/_s162_vuelta2/RECORD_FALTANTE_CHILLAN_12OCT.md`).
Estas pruebas fijan que el evaluador común parte de las pasadas de MIROVA y que ese caso da INVALIDO.
"""
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts import clase_mirova as cm  # noqa: E402
from scripts import evaluador_comun as ec  # noqa: E402

CH = "NevadosDeChillan"


def fila(fecha, tipo, vrp, vol=CH, sensor="VIIRS750", source="CONS", dist=1.0):
    return {"volcano": vol, "sensor_bucket": sensor, "fecha_utc": fecha, "source": source, "tipo": tipo,
            "vrp_mw": vrp, "dist_km": dist, "sin_geometria": False}


def rec(fecha, pub=True, disp=0.5, vol=CH, b="VIIRS750"):
    return {"vol": vol, "b": b, "dt": datetime.strptime(fecha, "%Y-%m-%d %H:%M"), "pub": pub, "disp": disp}


# Noche del 2026-10-12 en Chillán, VIIRS 750: NOAA-20 04:36 (RUTINA), NOAA-21 05:18 (protegida 8,44 MW),
# Suomi NPP 05:54 (alerta 0,40), NOAA-20 06:12 (RUTINA).
REF_12 = [fila("2026-10-12 04:36:10", "RUTINA", 0.0), fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 8.44, dist=1.68),
          fila("2026-10-12 05:54:20", "ALERTA_TERMICA", 0.40), fila("2026-10-12 06:12:05", "RUTINA", 0.0)]
PROD_12 = [rec("2026-10-12 04:36", pub=False, disp=0), rec("2026-10-12 05:18", disp=3.46),
           rec("2026-10-12 05:54", pub=False, disp=0), rec("2026-10-12 06:12", pub=False, disp=0)]
BRAZO_12 = [rec("2026-10-12 04:36", pub=False, disp=0), rec("2026-10-12 06:12", pub=False, disp=0)]


def pasadas(filas):
    return cm.resumir_pasadas(filas, regla_minimas="original")


def evaluar(ref, lados, control="prod", excl=()):
    T = ec.tabla_por_pasada(pasadas(ref), lados, control)
    return T, ec.cobertura(T, lados, control, excl)


# ------------------------------------------------------------------ T1: el caso del 12-oct
def test_protegida_sin_record_en_todos_los_brazos_que_produccion_tiene_es_invalido():
    lados = {"prod": PROD_12, "K": list(BRAZO_12), "D": list(BRAZO_12)}
    T, c = evaluar(REF_12, lados)
    assert c["veredicto"] == ec.INVALIDO
    assert c["protegidas_sin_record_en_brazos"] == ["%s|VIIRS750|2026-10-12 05:18:02 (MIROVA 8.44 MW) falta en D, K" % CH]
    # La alerta no protegida de las 05:54 se avisa, no invalida.
    assert c["aviso_alertas_no_protegidas_sin_record_en_brazos"] == [
        "%s|VIIRS750|2026-10-12 05:54:20 (MIROVA 0.4 MW) falta en D, K" % CH]
    # Lo que el evaluador viejo hacía: comparar brazos entre sí. Son idénticos y eso no dice nada.
    assert [r["dt"] for r in lados["K"]] == [r["dt"] for r in lados["D"]]


def test_protegida_que_falta_en_un_solo_brazo_tambien_invalida():
    # Verificador de #904, hallazgo 1 (gravedad 3): un brazo con menos cobertura sesga el veredicto igual que un hueco
    # común. Antes esto daba COBERTURA OK (y una prueba lo fijaba como correcto).
    lados = {"prod": PROD_12, "K": BRAZO_12 + [rec("2026-10-12 05:18", disp=3.0)], "D": list(BRAZO_12)}
    _, c = evaluar(REF_12, lados)
    assert c["veredicto"] == ec.INVALIDO
    assert c["protegidas_sin_record_en_brazos"] == ["%s|VIIRS750|2026-10-12 05:18:02 (MIROVA 8.44 MW) falta en D" % CH]


def test_control_que_no_tiene_una_protegida_que_un_brazo_si_tiene_invalida():
    # Verificador de #904, hallazgo 2 (gravedad 3): con un control incompleto (K sin el 12-oct) la pasada quedaba
    # «no observada» y el evaluador daba OK. Un control así no sirve de vara de cobertura.
    lados = {"K": list(BRAZO_12), "prod": PROD_12}
    _, c = evaluar(REF_12, lados, control="K")
    assert c["veredicto"] == ec.INVALIDO
    assert c["control_sin_protegida_que_un_brazo_tiene"] == [
        "%s|VIIRS750|2026-10-12 05:18:02 (MIROVA 8.44 MW) la tiene prod" % CH]
    assert c["aviso_control_sin_record_que_un_brazo_tiene"] == 1   # la alerta de 0,40 de las 05:54


def test_no_observado_se_agrupa_por_dia_para_ver_huecos_comunes():
    # Verificador de #904, hallazgo 3: dos de las seis no observadas de V1 caen el 12-oct, el día del hueco de NASA.
    ref = REF_12 + [fila("2026-10-11 05:00:00", "RUTINA", 0.0)]
    lados = {"prod": [r for r in PROD_12 if r["dt"].hour != 4], "K": [r for r in PROD_12 if r["dt"].hour != 4]}
    _, c = evaluar(ref, lados)
    assert c["no_observado_por_dia"] == {"2026-10-12": 1, "2026-10-11": 1}


def test_dia_excluido_no_cuenta_pero_se_informa():
    lados = {"prod": PROD_12, "K": list(BRAZO_12)}
    _, c = evaluar(REF_12, lados, excl=("2026-10-12",))
    assert c["veredicto"] == ec.COBERTURA_OK
    assert len(c["en_dias_excluidos"]) == 2 and c["protegidas_sin_record_en_brazos"] == []


def test_dia_con_pasadas_de_mirova_y_cero_records_en_un_brazo_es_invalido():
    ref = [fila("2026-10-18 05:06:00", "ALERTA_TERMICA", 0.5), fila("2026-10-18 06:00:00", "RUTINA", 0.0)]
    lados = {"prod": [rec("2026-10-18 05:06"), rec("2026-10-18 06:00")], "K": []}
    _, c = evaluar(ref, lados)
    assert c["veredicto"] == ec.INVALIDO
    assert c["dias_con_pasadas_de_mirova_y_sin_records"] == [
        "%s|VIIRS750|2026-10-18 sin records en K (MIROVA 2 pasadas, control 2 records)" % CH]


def test_dia_vacio_tambien_en_el_control_igual_invalida():
    # Un hueco común con producción no deja evaluar ese día; se informa con el conteo del control.
    ref = [fila("2026-10-18 05:06:00", "RUTINA", 0.0)]
    _, c = evaluar(ref, {"prod": [], "K": []})
    assert c["veredicto"] == ec.INVALIDO
    assert c["dias_con_pasadas_de_mirova_y_sin_records"][0].endswith("control 0 records)")


def test_cobertura_completa_da_ok():
    lados = {"prod": PROD_12, "K": list(PROD_12)}
    _, c = evaluar(REF_12, lados)
    assert c["veredicto"] == ec.COBERTURA_OK
    assert c["por_lado"]["K"] == {"pasadas": 4, ec.OBSERVADO: 4, ec.FALTA: 0, ec.NO_OBSERVADO: 0}


def test_pareo_a_120_s_borde():
    ref = [fila("2026-10-12 05:18:00", "ALERTA_TERMICA", 2.0)]
    T = ec.tabla_por_pasada(pasadas(ref), {"prod": [rec("2026-10-12 05:20")]}, "prod")
    assert T[0]["cob"]["prod"] == ec.OBSERVADO
    T = ec.tabla_por_pasada(pasadas(ref), {"prod": [rec("2026-10-12 05:21")]}, "prod")
    assert T[0]["cob"]["prod"] == ec.NO_OBSERVADO


def test_pareo_a_120_s_borde_por_abajo():
    ref = [fila("2026-10-12 05:18:00", "ALERTA_TERMICA", 2.0)]
    T = ec.tabla_por_pasada(pasadas(ref), {"prod": [rec("2026-10-12 05:16")]}, "prod")
    assert T[0]["cob"]["prod"] == ec.OBSERVADO
    T = ec.tabla_por_pasada(pasadas(ref), {"prod": [rec("2026-10-12 05:15")]}, "prod")
    assert T[0]["cob"]["prod"] == ec.NO_OBSERVADO


def test_el_pareo_toma_el_record_mas_cercano():
    ref = [fila("2026-10-12 05:18:50", "ALERTA_TERMICA", 2.0)]
    lejos, cerca = rec("2026-10-12 05:17", disp=0.1), rec("2026-10-12 05:19", disp=2.2)
    T = ec.tabla_por_pasada(pasadas(ref), {"prod": [lejos, cerca]}, "prod")
    assert T[0]["rec"]["prod"] is cerca


def test_otro_volcan_u_otro_sensor_no_parean():
    ref = [fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 2.0)]
    lados = {"prod": [rec("2026-10-12 05:18", b="VIIRS375"), rec("2026-10-12 05:18", vol="Lascar")]}
    assert ec.tabla_por_pasada(pasadas(ref), lados, "prod")[0]["cob"]["prod"] == ec.NO_OBSERVADO


def test_control_desconocido_falla_fuerte():
    try:
        ec.tabla_por_pasada([], {"K": []}, "prod")
    except ValueError:
        return
    raise AssertionError("un control que no está entre los lados no puede pasar en silencio")


# ------------------------------------------------------------------ T2: no observado
def test_no_observado_es_estado_propio_y_sale_del_denominador():
    ref = [fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 2.0), fila("2026-10-12 06:12:05", "RUTINA", 0.0)]
    # Nadie tiene la pasada de las 05:18 (fuera del gránulo o escena inválida): no observada.
    lados = {"prod": [rec("2026-10-12 06:12", pub=False, disp=0)], "K": [rec("2026-10-12 06:12", disp=1.5)]}
    T, c = evaluar(ref, lados)
    assert T[0]["cob"] == {"prod": ec.NO_OBSERVADO, "K": ec.NO_OBSERVADO}
    assert c["por_lado"]["K"][ec.NO_OBSERVADO] == 1
    assert c["protegidas_sin_record_en_brazos"] == []   # el control tampoco la tiene: no es falla del brazo
    assert not ec.observada_en(T[0], "prod", "K") and ec.observada_en(T[1], "prod", "K")
    # Fuera del denominador de P1b: la protegida no observada no aparece como cruce.
    assert ec.p1b(T, "prod", "K")["abajo"] == []


def test_falta_cobertura_es_distinto_de_no_observado():
    T, c = evaluar(REF_12, {"prod": PROD_12, "K": list(BRAZO_12)})
    estados = {f["clave"][-8:]: f["cob"]["K"] for f in T}
    assert estados == {"04:36:10": ec.OBSERVADO, "05:18:02": ec.FALTA, "05:54:20": ec.FALTA, "06:12:05": ec.OBSERVADO}
    assert c["por_lado"]["K"][ec.FALTA] == 2 and c["por_lado"]["prod"][ec.FALTA] == 0


# ------------------------------------------------------------------ T5: P1b en las dos direcciones
def test_p1b_abajo_protegida_que_cae_bajo_1_mw():
    ref = [fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 8.44)]
    lados = {"prod": [rec("2026-10-12 05:18", disp=3.46)], "D": [rec("2026-10-12 05:18", disp=0.8)]}
    T = ec.tabla_por_pasada(pasadas(ref), lados, "prod")
    r = ec.p1b(T, "prod", "D")
    assert len(r["abajo"]) == 1 and r["arriba"] == {}


def test_p1b_abajo_exige_que_los_dos_publiquen_y_el_borde_de_1_mw():
    ref = [fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 8.44)]
    for c_disp, d_disp, d_pub, n in ((1.0, 0.99, True, 1), (0.99, 0.5, True, 0), (3.0, 0.0, False, 0),
                                     (3.0, 1.0, True, 0)):
        lados = {"prod": [rec("2026-10-12 05:18", disp=c_disp)], "D": [rec("2026-10-12 05:18", disp=d_disp, pub=d_pub)]}
        assert len(ec.p1b(ec.tabla_por_pasada(pasadas(ref), lados, "prod"), "prod", "D")["abajo"]) == n, (c_disp, d_disp)


def test_p1b_arriba_por_estado_de_mirova():
    ref = [fila("2026-10-12 04:36:10", "RUTINA", 0.0), fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 0.6),
           fila("2026-10-12 05:54:20", "FALSO_POSITIVO", 2.0, dist=15.0),
           fila("2026-10-12 06:12:05", "ALERTA_TERMICA", 3.0)]
    lados = {"prod": [rec("2026-10-12 04:36", pub=False, disp=0), rec("2026-10-12 05:18", disp=0.4),
                      rec("2026-10-12 05:54", disp=0.9), rec("2026-10-12 06:12", disp=0.7)],
             "D": [rec("2026-10-12 04:36", disp=1.2), rec("2026-10-12 05:18", disp=1.0),
                   rec("2026-10-12 05:54", disp=1.1), rec("2026-10-12 06:12", disp=1.4)]}
    r = ec.p1b(ec.tabla_por_pasada(pasadas(ref), lados, "prod"), "prod", "D")
    assert {k: len(v) for k, v in r["arriba"].items()} == {"rutina": 1, "alerta": 1, "fp": 1, "protegida": 1}
    assert r["abajo"] == []


def test_p1b_arriba_no_cuenta_si_el_control_ya_estaba_sobre_1_mw():
    ref = [fila("2026-10-12 05:18:02", "RUTINA", 0.0)]
    lados = {"prod": [rec("2026-10-12 05:18", disp=1.0)], "D": [rec("2026-10-12 05:18", disp=5.0)]}
    assert ec.p1b(ec.tabla_por_pasada(pasadas(ref), lados, "prod"), "prod", "D")["arriba"] == {}


def test_p1b_arriba_no_cuenta_pasadas_que_el_control_no_observo():
    ref = [fila("2026-10-12 05:18:02", "RUTINA", 0.0)]
    lados = {"prod": [], "D": [rec("2026-10-12 05:18", disp=1.5)]}
    T = ec.tabla_por_pasada(pasadas(ref), lados, "prod")
    assert T[0]["cob"] == {"prod": ec.NO_OBSERVADO, "D": ec.OBSERVADO}
    assert ec.p1b(T, "prod", "D")["arriba"] == {}


def test_p1b_el_valor_de_un_record_no_publicado_es_cero():
    # El control calculó 1,5 MW pero el tablero no lo publicó: para el operador vale 0 y el brazo que publica 1,2 sube.
    ref = [fila("2026-10-12 05:18:02", "RUTINA", 0.0)]
    lados = {"prod": [rec("2026-10-12 05:18", pub=False, disp=1.5)], "D": [rec("2026-10-12 05:18", disp=1.2)]}
    r = ec.p1b(ec.tabla_por_pasada(pasadas(ref), lados, "prod"), "prod", "D")
    assert {k: len(v) for k, v in r["arriba"].items()} == {"rutina": 1}


def test_p1b_respeta_dias_excluidos():
    ref = [fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 8.44)]
    lados = {"prod": [rec("2026-10-12 05:18", disp=3.46)], "D": [rec("2026-10-12 05:18", disp=0.8)]}
    T = ec.tabla_por_pasada(pasadas(ref), lados, "prod")
    assert ec.p1b(T, "prod", "D", dias_excluidos=("2026-10-12",))["abajo"] == []


# ------------------------------------------------------------------ T5: publicaciones sobre RUTINA (VE162-03)
def test_publicaciones_sobre_rutina_separadas_por_noche_con_alerta():
    ref = [fila("2026-10-12 04:36:10", "RUTINA", 0.0), fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 8.44),
           fila("2026-10-13 05:00:00", "RUTINA", 0.0),
           fila("2026-10-13 06:00:00", "RUTINA", 0.0, source="OCR")]   # el OCR no tiene RUTINA real: no cuenta
    lados = {"prod": [rec("2026-10-12 04:36", pub=False, disp=0), rec("2026-10-12 05:18", disp=3.0),
                      rec("2026-10-13 05:00", pub=False, disp=0), rec("2026-10-13 06:00", pub=False, disp=0)],
             "D": [rec("2026-10-12 04:36", disp=0.3), rec("2026-10-12 05:18", disp=3.0),
                   rec("2026-10-13 05:00", disp=0.2), rec("2026-10-13 06:00", disp=0.2)]}
    r = ec.publicaciones_sobre_rutina(ec.tabla_por_pasada(pasadas(ref), lados, "prod"), ["prod", "D"])
    assert r["D"]["rutinas_observadas"] == 2
    assert r["D"]["publica_en_noche_con_alerta"] == ["%s|VIIRS750|2026-10-12 04:36:10" % CH]
    assert r["D"]["publica_en_noche_sin_alerta"] == ["%s|VIIRS750|2026-10-13 05:00:00" % CH]
    assert r["prod"]["publica_en_noche_con_alerta"] == [] and r["prod"]["publica_en_noche_sin_alerta"] == []


def test_falso_positivo_no_cuenta_como_rutina():
    ref = [fila("2026-10-13 05:00:00", "FALSO_POSITIVO", 2.0, dist=15.0)]
    lados = {"prod": [rec("2026-10-13 05:00", pub=False, disp=0)], "D": [rec("2026-10-13 05:00", disp=0.2)]}
    r = ec.publicaciones_sobre_rutina(ec.tabla_por_pasada(pasadas(ref), lados, "prod"), ["prod", "D"])
    assert r["D"]["rutinas_observadas"] == 0 and r["D"]["publica_en_noche_sin_alerta"] == []


def test_rutina_no_observada_no_cuenta():
    ref = [fila("2026-10-13 05:00:00", "RUTINA", 0.0)]
    lados = {"prod": [], "D": [rec("2026-10-13 05:00", disp=0.2)]}
    r = ec.publicaciones_sobre_rutina(ec.tabla_por_pasada(pasadas(ref), lados, "prod"), ["prod", "D"])
    assert r["D"]["rutinas_observadas"] == 0 and r["D"]["publica_en_noche_sin_alerta"] == []


# ------------------------------------------------------------------ carga real (verificador de #904, hallazgo 4)
def test_cargar_lado_filtra_ventana_sensor_y_dia_e_informa_volcanes_sin_archivo(tmp_path, monkeypatch):
    import json
    import banco_paridad as bp
    vistos = []

    def node_falso(casos):
        vistos.extend(casos)
        return [[None, None, None, 0.7, True] for _ in casos]

    monkeypatch.setattr(bp, "correr_node", node_falso)
    base = {"distance_class": "summit", "primary_cluster": {"vrp_mw": 0.7}, "vrp_mw": 0.7}
    recs = [dict(base, datetime_utc="2026-10-12 05:18", sensor="VIIRS_NOAA21_750"),   # entra
            dict(base, datetime_utc="2026-10-12 17:30", sensor="VIIRS_NOAA21_750"),   # de día: fuera
            dict(base, datetime_utc="2026-10-30 05:18", sensor="VIIRS_NOAA21_750"),   # fuera de la ventana
            dict(base, datetime_utc="2026-10-12 03:00", sensor="MODIS_AQUA")]          # sensor no pedido
    (tmp_path / "Lascar.json").write_text(json.dumps({"records": recs}), encoding="utf-8")
    out, faltan = ec.cargar_lado(tmp_path, ("2026-10-01", "2026-10-20"), ("VIIRS750",), bp._coords_por_volcan(),
                                 {v: 5.0 for v in bp.VOLS})
    assert [(r["vol"], r["b"], r["dt"].strftime("%H:%M"), r["pub"], r["disp"]) for r in out] == [
        ("Lascar", "VIIRS750", "05:18", True, 0.7)]
    assert len(vistos) == 1 and vistos[0][1] == 5.0
    assert "Lascar" not in faltan and len(faltan) == len(bp.VOLS) - 1


def test_pasadas_nocturnas_filtra_igual_que_los_records():
    import banco_paridad as bp
    filas = [fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 2.0, vol="Lascar"),
             fila("2026-10-12 17:30:00", "ALERTA_TERMICA", 2.0, vol="Lascar"),
             fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 2.0, vol="Lascar", sensor="MODIS"),
             fila("2026-10-30 05:18:02", "ALERTA_TERMICA", 2.0, vol="Lascar")]
    ps = ec.pasadas_nocturnas(filas, ("2026-10-01", "2026-10-20"), ("VIIRS750",), bp._coords_por_volcan(), "union",
                              "original")
    assert [(p.volcano, p.sensor_bucket, p.instante.strftime("%H:%M")) for p in ps] == [("Lascar", "VIIRS750", "05:18")]
