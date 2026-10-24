# -*- coding: utf-8 -*-
"""S162, instrumento T4 y T6: una sola definicion de alerta y protegida, por PASADA.

POR QUE. Hasta S161 la referencia de MIROVA se juzgaba fila por fila: `alerta_protegida` mira una fila y
`pasadas_protegidas` junta las protegidas por minuto. Con eso, si la tabla de MIROVA (latest.php, el canal mas
creible, feedback S159) dice FALSO_POSITIVO o RUTINA en una pasada y el OCR de la imagen dice ALERTA de 1 MW o mas en
la misma pasada, la pasada cuenta como protegida (riesgo latente de
`experiments/_s159/mirova_v1_auditoria/INFORME.md:246-250`). Y la fila de la tabla (05:18:02) y la del OCR
(05:17:58) de una misma pasada caen en minutos distintos y cuentan como dos pasadas. La definicion nueva agrupa las
filas de una pasada a +-120 s (`VENTANA_S`, la del pareo) y decide con la tabla cuando la tabla tiene la pasada.

T6 (V375-A): la "protegida de crater" se informa AL LADO de la lectura A, nunca la reemplaza. Saca las protegidas
cuya distancia no es de su pasada (solo OCR de Suomi NPP antes del 2026-10-09; solo OCR antes del 2026-06-13, A119),
las que no tienen distancia y las que estan fuera del radio del crater (`experiments/_s159/portes/INFORME.md` P-5).
"""
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import clase_mirova as cm  # noqa: E402


def fila(fecha, tipo, vrp, source="CONS", vol="NevadosDeChillan", sensor="VIIRS750", dist=1.0, sin_geo=False):
    return {"volcano": vol, "sensor_bucket": sensor, "fecha_utc": fecha, "source": source, "tipo": tipo,
            "vrp_mw": vrp, "dist_km": dist, "sin_geometria": sin_geo}


def una(pasadas):
    assert len(pasadas) == 1, pasadas
    return pasadas[0]


# ------------------------------------------------------------------ T4: la tabla manda en su pasada
def test_tabla_falso_positivo_le_gana_a_alerta_ocr_de_la_misma_pasada():
    filas = [fila("2026-10-12 05:18:02", "FALSO_POSITIVO", 8.44, dist=12.0),
             fila("2026-10-12 05:18:00", "ALERTA_TERMICA_OCR", 8.0, source="OCR", dist=1.76)]
    p = una(cm.resumir_pasadas(filas, regla_minimas="original"))
    assert p.estado == "fp"
    assert p.fuente == "CONS"
    assert p.ocr_contradice_tabla is True
    assert not cm.es_protegida(p)
    # El defecto que esto arregla: la funcion vieja, fila por fila, la daba por protegida.
    assert ("NevadosDeChillan", "VIIRS750", "2026-10-12 05:18") in cm.pasadas_protegidas(filas)


def test_tabla_rutina_le_gana_a_alerta_ocr():
    filas = [fila("2026-10-12 05:18:02", "RUTINA", 0.0),
             fila("2026-10-12 05:19:10", "ALERTA_TERMICA_OCR", 2.0, source="OCR")]
    p = una(cm.resumir_pasadas(filas, regla_minimas="original"))
    assert p.estado == "rutina" and p.ocr_contradice_tabla and not cm.es_protegida(p)


def test_alerta_solo_ocr_cuenta_en_union_y_no_existe_en_tabla_sola():
    filas = [fila("2026-09-14 06:18:00", "ALERTA_TERMICA_OCR", 2.22, source="OCR", vol="Tupungatito",
                  sensor="VIIRS375", dist=1.0)]
    p = una(cm.resumir_pasadas(filas, regla_minimas="original"))
    assert p.estado == "alerta" and p.solo_ocr and p.fuente == "OCR" and cm.es_protegida(p)
    assert cm.resumir_pasadas(filas, canal="tabla", regla_minimas="original") == []


def test_canal_tabla_ignora_el_ocr_aunque_diga_otra_cosa():
    filas = [fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 0.9),
             fila("2026-10-12 05:18:00", "ALERTA_TERMICA_OCR", 1.5, source="OCR")]
    for canal in ("union", "tabla"):
        p = una(cm.resumir_pasadas(filas, canal=canal, regla_minimas="original"))
        assert p.vrp_mw == 0.9 and not cm.es_protegida(p), canal


def test_canal_desconocido_falla_fuerte():
    try:
        cm.resumir_pasadas([], canal="ocr")
    except ValueError:
        return
    raise AssertionError("un canal desconocido no puede caer en silencio en el de por defecto")


# ------------------------------------------------------------------ agrupacion a +-120 s
def test_filas_a_menos_de_120_s_son_una_pasada_aunque_cambie_el_minuto():
    filas = [fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 8.44),
             fila("2026-10-12 05:17:59", "ALERTA_TERMICA_OCR", 8.0, source="OCR")]
    p = una(cm.resumir_pasadas(filas, regla_minimas="original"))
    assert p.instante == datetime(2026, 10, 12, 5, 17, 59)
    assert len(p.filas) == 2
    # La vieja las contaba como dos pasadas protegidas.
    assert len(cm.pasadas_protegidas(filas)) == 2


def test_borde_de_la_ventana_120_s_entra_121_no():
    a = [fila("2026-10-12 05:18:00", "ALERTA_TERMICA", 1.2), fila("2026-10-12 05:20:00", "RUTINA", 0.0)]
    assert len(cm.resumir_pasadas(a, regla_minimas="original")) == 1
    b = [fila("2026-10-12 05:18:00", "ALERTA_TERMICA", 1.2), fila("2026-10-12 05:20:01", "RUTINA", 0.0)]
    assert len(cm.resumir_pasadas(b, regla_minimas="original")) == 2


def test_la_ventana_se_mide_desde_la_primera_fila_no_encadena():
    # Tres filas a 100 s una de otra: la tercera queda a 200 s de la primera y no es la misma pasada.
    filas = [fila("2026-10-12 05:18:00", "RUTINA", 0.0), fila("2026-10-12 05:19:40", "RUTINA", 0.0),
             fila("2026-10-12 05:21:20", "RUTINA", 0.0)]
    assert len(cm.resumir_pasadas(filas, regla_minimas="original")) == 2


def test_otro_volcan_u_otro_sensor_no_se_juntan():
    filas = [fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 8.44),
             fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 7.31, sensor="VIIRS375"),
             fila("2026-10-12 05:18:02", "RUTINA", 0.0, vol="Lascar")]
    assert len(cm.resumir_pasadas(filas, regla_minimas="original")) == 3


# ------------------------------------------------------------------ magnitud y estados
def test_vrp_de_la_pasada_es_la_mayor_alerta_de_la_fuente_que_decide():
    filas = [fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 0.6, dist=0.84),
             fila("2026-10-12 05:18:30", "ALERTA_TERMICA", 1.4, dist=1.68)]
    p = una(cm.resumir_pasadas(filas, regla_minimas="original"))
    assert p.vrp_mw == 1.4 and p.dist_km == 1.68 and cm.es_protegida(p)


def test_alerta_sin_vrp_no_es_protegida():
    p = una(cm.resumir_pasadas([fila("2026-10-12 05:18:02", "ALERTA_TERMICA", None)], regla_minimas="original"))
    assert p.estado == "alerta" and p.vrp_mw is None and not cm.es_protegida(p)


def test_sin_geometria_no_es_alerta_de_la_lectura_a_pero_si_de_la_b():
    f = fila("2026-10-15 05:00:00", "ALERTA_SIN_GEOMETRIA_OCR", 22.13, source="OCR", sensor="VIIRS375",
             dist=None, sin_geo=True)
    p = una(cm.resumir_pasadas([f], regla_minimas="original"))
    assert p.estado == "sin_geometria"
    assert not cm.es_protegida(p) and cm.es_protegida(p, lectura="B")


def test_umbral_protegida_borde():
    for v, esperado in ((1.0, True), (0.99, False)):
        p = una(cm.resumir_pasadas([fila("2026-10-12 05:18:02", "ALERTA_TERMICA", v)], regla_minimas="original"))
        assert cm.es_protegida(p) is esperado, v


def test_lectura_b_cuenta_falso_positivo_de_la_tabla_y_nunca_rutina():
    p = una(cm.resumir_pasadas([fila("2026-10-12 05:18:02", "FALSO_POSITIVO", 3.0, dist=15.0)],
                               regla_minimas="original"))
    assert not cm.es_protegida(p) and cm.es_protegida(p, lectura="B")
    r = una(cm.resumir_pasadas([fila("2026-10-12 05:18:02", "RUTINA", 0.0)], regla_minimas="original"))
    assert not cm.es_protegida(r, lectura="B")


def test_regla_sn_por_defecto_vuelve_rutina_la_alerta_minima_de_viirs375():
    f = fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 0.04, sensor="VIIRS375")
    assert cm.MODO_MINIMAS == "SN"
    assert una(cm.resumir_pasadas([f])).estado == "rutina"
    assert una(cm.resumir_pasadas([f], regla_minimas="original")).estado == "alerta"
    assert una(cm.resumir_pasadas([f], regla_minimas="SE")).estado == "minima"


def test_no_muta_las_filas_de_entrada():
    filas = [fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 0.04, sensor="VIIRS375")]
    copia = [dict(f) for f in filas]
    cm.resumir_pasadas(filas)
    assert filas == copia


# ------------------------------------------------------------------ T6: protegida de crater (al lado de la A)
def test_protegida_de_crater_tabla_dentro_del_radio():
    p = una(cm.resumir_pasadas([fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 8.44, dist=1.68)],
                               regla_minimas="original"))
    assert cm.protegida_de_crater(p, radio_km=5.0) == (True, ())


def test_protegida_fuera_del_radio_no_es_de_crater_pero_sigue_protegida_a():
    p = una(cm.resumir_pasadas([fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 2.0, dist=6.5)],
                               regla_minimas="original"))
    assert cm.es_protegida(p)
    assert cm.protegida_de_crater(p, radio_km=5.0) == (False, ("lejos_del_crater",))
    assert cm.protegida_de_crater(p, radio_km=6.5) == (True, ())


def test_solo_ocr_de_suomi_npp_antes_del_hito_no_es_de_crater():
    f = fila("2026-09-14 06:18:00", "ALERTA_TERMICA_OCR", 2.22, source="OCR", vol="Tupungatito",
             sensor="VIIRS375", dist=1.0)
    p = una(cm.resumir_pasadas([f], regla_minimas="original"))
    assert cm.protegida_de_crater(p, radio_km=7.0, plataforma="VIIRS_SNPP") == (False, ("ocr_snpp_antes_del_hito",))
    assert cm.protegida_de_crater(p, radio_km=7.0, plataforma="VIIRS_NOAA20") == (True, ())
    # Sin saber la plataforma no se puede descartar que sea Suomi NPP: no se la da por crater.
    assert cm.protegida_de_crater(p, radio_km=7.0) == (False, ("plataforma_desconocida_antes_del_hito",))


def test_el_hito_de_snpp_es_el_9_de_octubre():
    antes = fila("2026-10-08 23:59:00", "ALERTA_TERMICA_OCR", 2.0, source="OCR", sensor="VIIRS375")
    desde = fila("2026-10-09 00:00:00", "ALERTA_TERMICA_OCR", 2.0, source="OCR", sensor="VIIRS375")
    pa = una(cm.resumir_pasadas([antes], regla_minimas="original"))
    pd = una(cm.resumir_pasadas([desde], regla_minimas="original"))
    assert not cm.protegida_de_crater(pa, radio_km=5.0, plataforma="VIIRS_SNPP")[0]
    assert cm.protegida_de_crater(pd, radio_km=5.0, plataforma="VIIRS_SNPP")[0]


def test_solo_ocr_antes_de_la_distancia_medida_no_es_de_crater():
    f = fila("2026-06-12 05:00:00", "ALERTA_TERMICA_OCR", 3.0, source="OCR", sensor="VIIRS375", dist=1.0)
    p = una(cm.resumir_pasadas([f], regla_minimas="original"))
    assert cm.protegida_de_crater(p, radio_km=5.0, plataforma="VIIRS_NOAA20") == (
        False, ("ocr_sin_distancia_medida",))
    g = dict(f, fecha_utc="2026-06-13 05:00:00")
    assert cm.protegida_de_crater(una(cm.resumir_pasadas([g], regla_minimas="original")), radio_km=5.0,
                                  plataforma="VIIRS_NOAA20") == (True, ())


def test_la_tabla_no_lleva_las_marcas_del_ocr():
    # Fila de la tabla de Suomi NPP antes del hito: la tabla trae su propia distancia, no se marca.
    p = una(cm.resumir_pasadas([fila("2026-09-14 06:18:00", "ALERTA_TERMICA", 2.0, sensor="VIIRS375")],
                               regla_minimas="original"))
    assert cm.protegida_de_crater(p, radio_km=5.0, plataforma="VIIRS_SNPP") == (True, ())


def test_sin_distancia_no_es_de_crater():
    p = una(cm.resumir_pasadas([fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 2.0, dist=None)],
                               regla_minimas="original"))
    assert cm.protegida_de_crater(p, radio_km=5.0) == (False, ("sin_distancia",))


def test_no_protegida_nunca_es_de_crater():
    p = una(cm.resumir_pasadas([fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 0.5)], regla_minimas="original"))
    assert cm.protegida_de_crater(p, radio_km=5.0) == (False, ("no_protegida",))


def test_motivos_se_acumulan():
    f = fila("2026-09-14 06:18:00", "ALERTA_TERMICA_OCR", 2.22, source="OCR", sensor="VIIRS375", dist=12.5)
    p = una(cm.resumir_pasadas([f], regla_minimas="original"))
    assert cm.protegida_de_crater(p, radio_km=5.0, plataforma="VIIRS_SNPP") == (
        False, ("ocr_snpp_antes_del_hito", "lejos_del_crater"))
