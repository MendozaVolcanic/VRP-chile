# -*- coding: utf-8 -*-
"""S163, pendientes del instrumento: estratos por cenit y régimen (tarea 1.35) y causa de cada pasada ausente.

POR QUÉ, estratos. Un píxel oblicuo es más grande y más deformado, y en Chillán la razón contra MIROVA cae con el
cenit del sensor (experiments/_s154_chillan/razon_por_cenit.py); un agregado sobre todas las pasadas promedia esa
curva y una ventana con más pasadas de borde se lee como efecto del brazo (A90, A114). El programa por sensor pide
todo por tramos de 10° de cenit y por régimen (antes y después de #535 y de K). Estas pruebas fijan que los estratos
particionan el agregado y que no cambian ningún veredicto.

POR QUÉ, causa de la ausencia. Una pasada que MIROVA publicó y que un lado no tiene puede ser legítima (el gránulo
llegó y no dejó record: volcán fuera de la escena, escena inválida) o un hueco de NASA (la búsqueda falló o respondió
vacía, el L1B vino sin geolocalización). El 2026-10-12, en V1 de D25, CMR respondió vacío para NOAA-21 y Suomi NPP y
el job dijo «Cobertura: completa» (experiments/_s162_vuelta2/RECORD_FALTANTE_CHILLAN_12OCT.md). Desde #909 el run
deja esas incidencias en el JSON de cobertura; el evaluador las cruza con las pasadas de MIROVA.
"""
import json
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


def rec(fecha, pub=True, disp=0.5, vol=CH, b="VIIRS750", z=None):
    r = {"vol": vol, "b": b, "dt": datetime.strptime(fecha, "%Y-%m-%d %H:%M"), "pub": pub, "disp": disp}
    if z is not None:
        r["z"] = z
    return r


def pasadas(filas):
    return cm.resumir_pasadas(filas, regla_minimas="original")


# ------------------------------------------------------------------ 1.35: tramos y régimen
def test_tramo_cenit_de_10_grados_y_sin_cenit_aparte():
    assert ec.tramo_cenit(None) == "sin_cenit"
    assert ec.tramo_cenit(0.0) == "z00-10"
    assert ec.tramo_cenit(9.99) == "z00-10"
    assert ec.tramo_cenit(10.0) == "z10-20"
    assert ec.tramo_cenit(49.9) == "z40-50"
    assert ec.tramo_cenit(67.6) == "z60-70"
    assert ec.tramo_cenit(70.0) == "z70-80"


def test_regimen_por_hora_de_la_pasada_con_los_bordes_exactos():
    d = lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M:%S")  # noqa: E731
    assert ec.regimen(d("2026-08-28 22:59:59")) == "antes_535"
    assert ec.regimen(d("2026-08-28 23:00:00")) == "535_a_K"
    assert ec.regimen(d("2026-10-18 09:57:29")) == "535_a_K"
    assert ec.regimen(d("2026-10-18 09:57:30")) == "desde_K"


def test_cortes_de_regimen_son_los_del_resto_del_proyecto():
    """A102: una sola definición. #535 es la del auto-audit; K, la hora de adopción que lee la vigilancia."""
    import auto_audit_weekly as aa
    import vigilancia_sombra as vs
    assert ec.CORTE_535.strftime("%Y-%m-%d %H:%M") == aa.CORTE_535
    assert ec.CORTE_K.strftime("%Y-%m-%d %H:%M:%S") == vs.leer_adopcion()


def test_tabla_lleva_el_cenit_del_control_y_el_regimen():
    ref = [fila("2026-08-28 05:18:02", "ALERTA_TERMICA", 0.5), fila("2026-10-19 05:18:02", "ALERTA_TERMICA", 0.5),
           fila("2026-10-20 05:18:02", "ALERTA_TERMICA", 0.5)]
    lados = {"prod": [rec("2026-08-28 05:18", z=55.0), rec("2026-10-19 05:18", z=12.0)],
             "D": [rec("2026-08-28 05:18", z=99.0), rec("2026-10-19 05:18", z=99.0),
                   rec("2026-10-20 05:18", z=33.0)]}
    T = ec.tabla_por_pasada(pasadas(ref), lados, "prod")
    assert [(f["z"], f["regimen"]) for f in T] == [(55.0, "antes_535"), (12.0, "desde_K"), (None, "desde_K")]
    assert [ec.estrato_cenit(f) for f in T] == ["z50-60", "z10-20", "sin_cenit"]
    assert [ec.estrato_regimen(f) for f in T] == ["antes_535", "desde_K", "desde_K"]


def _tabla_variada():
    """Tres noches, dos volcanes, cenit distinto, con P1b, RUTINA, P2 y faltas de cobertura en el brazo D."""
    ref, prod, D = [], [], []
    noches = [("2026-08-20", 15.0), ("2026-09-20", 45.0), ("2026-10-20", 65.0)]
    for vol in (CH, "Lascar"):
        for dia, z in noches:
            ref += [fila(dia + " 04:30:00", "RUTINA", 0.0, vol=vol),                 # negativo limpio salvo alerta
                    fila(dia + " 05:20:00", "ALERTA_TERMICA", 2.0, vol=vol),          # protegida
                    fila(dia + " 06:10:00", "ALERTA_TERMICA", 0.3, vol=vol)]          # alerta bajo 1 MW
            prod += [rec(dia + " 04:30", pub=False, disp=0, vol=vol, z=z), rec(dia + " 05:20", disp=1.5, vol=vol, z=z),
                     rec(dia + " 06:10", pub=False, disp=0, vol=vol, z=z + 2)]
            D += [rec(dia + " 04:30", pub=True, disp=0.2, vol=vol, z=z), rec(dia + " 05:20", disp=0.8, vol=vol, z=z)]
    # y una noche de negativos limpios de Láscar donde el brazo publica uno y el control no
    ref += [fila("2026-10-21 04:30:00", "RUTINA", 0.0, vol="Lascar"), fila("2026-10-21 05:20:00", "RUTINA", 0.0,
                                                                              vol="Lascar")]
    prod += [rec("2026-10-21 04:30", pub=False, disp=0, vol="Lascar", z=25.0),
             rec("2026-10-21 05:20", pub=True, disp=0.1, vol="Lascar", z=25.0)]
    D += [rec("2026-10-21 04:30", pub=True, disp=0.1, vol="Lascar", z=25.0),
          rec("2026-10-21 05:20", pub=False, disp=0, vol="Lascar", z=25.0)]
    lados = {"prod": prod, "D": D}
    return ec.tabla_por_pasada(pasadas(ref), lados, "prod"), lados


def _agregado(T, lados):
    est = ec.metricas_por_estrato(T, "prod", ["D"], lambda f: "todo")
    return est["todo"]


def test_estratos_particionan_el_agregado_en_todas_las_metricas():
    T, lados = _tabla_variada()
    total = _agregado(T, lados)
    for por in (ec.estrato_cenit, ec.estrato_regimen):
        est = ec.metricas_por_estrato(T, "prod", ["D"], por)
        assert sum(e["pasadas"] for e in est.values()) == total["pasadas"] == len(T)
        for lado in ("prod", "D"):
            for estado in (ec.OBSERVADO, ec.FALTA, ec.NO_OBSERVADO):
                assert sum(e["cobertura"][lado][estado] for e in est.values()) == total["cobertura"][lado][estado]
            for k in ("publica_en_noche_con_alerta", "publica_en_noche_sin_alerta", "rutinas_observadas"):
                assert sum(e["rutina"][lado][k] for e in est.values()) == total["rutina"][lado][k]
        for k in ("abajo", "arriba"):
            assert sum(e["p1b"]["D"][k] for e in est.values()) == total["p1b"]["D"][k]
        for k in ("neto", "n_discordantes"):
            assert sum(e["p2"]["D"][k] for e in est.values()) == total["p2"]["D"][k]


def test_el_agregado_coincide_con_las_funciones_de_siempre():
    T, lados = _tabla_variada()
    total = _agregado(T, lados)
    c = ec.cobertura(T, lados, "prod")["por_lado"]
    assert {lado: dict(total["cobertura"][lado]) for lado in lados} == {
        lado: {k: c[lado][k] for k in (ec.OBSERVADO, ec.FALTA, ec.NO_OBSERVADO)} for lado in lados}
    p = ec.p1b(T, "prod", "D")
    assert total["p1b"]["D"] == {"abajo": len(p["abajo"]), "arriba": sum(len(v) for v in p["arriba"].values())}
    contrib = ec.contribuciones_p2(T, "prod", "D")
    assert total["p2"]["D"]["neto"] == sum(x["c"] for x in contrib)
    assert total["p2"]["D"]["n_discordantes"] == len(contrib) > 0
    assert total["p1b"]["D"]["abajo"] > 0 and total["cobertura"]["D"][ec.FALTA] > 0


def test_estrato_cae_donde_dice_su_cenit():
    T, lados = _tabla_variada()
    est = ec.metricas_por_estrato(T, "prod", ["D"], ec.estrato_cenit)
    # las protegidas de 05:20 de la noche de 45° son las únicas en z40-50: P1b abajo 2 (dos volcanes)
    assert est["z40-50"]["p1b"]["D"]["abajo"] == 2
    assert est["z40-50"]["pasadas"] == 6          # 45° y 47°: las tres pasadas de dos volcanes
    assert est["z60-70"]["pasadas"] == 6          # 65° y 67°
    assert est["z20-30"]["pasadas"] == 2
    assert est["z20-30"]["p2"]["D"] == {"neto": 0, "n_discordantes": 2, "B": 1}   # la noche simétrica de Láscar
    assert "z30-40" not in est                    # un tramo sin pasadas no aparece


def test_estratos_no_cambian_ningun_veredicto():
    """La cobertura y P1b de siempre dan lo mismo con y sin cenit en los records."""
    T, lados = _tabla_variada()
    sin_z = {lado: [{k: v for k, v in r.items() if k != "z"} for r in recs] for lado, recs in lados.items()}
    refs = [f["pasada"] for f in T]
    T2 = ec.tabla_por_pasada(refs, sin_z, "prod")
    assert ec.cobertura(T, lados, "prod") == ec.cobertura(T2, sin_z, "prod")
    assert ec.p1b(T, "prod", "D") == ec.p1b(T2, "prod", "D")
    assert ec.publicaciones_sobre_rutina(T, ["prod", "D"]) == ec.publicaciones_sobre_rutina(T2, ["prod", "D"])


def test_cargar_lado_lleva_el_cenit_del_record(tmp_path, monkeypatch):
    import banco_paridad as bp
    monkeypatch.setattr(bp, "correr_node", lambda casos: [[None, None, None, 0.7, True] for _ in casos])
    base = {"distance_class": "summit", "primary_cluster": {"vrp_mw": 0.7}, "vrp_mw": 0.7}
    recs = [dict(base, datetime_utc="2026-10-12 05:18", sensor="VIIRS_NOAA21_750", sensor_zenith_deg=41.5),
            dict(base, datetime_utc="2026-10-12 06:12", sensor="VIIRS_NOAA20_750")]
    (tmp_path / "Lascar.json").write_text(json.dumps({"records": recs}), encoding="utf-8")
    out, _ = ec.cargar_lado(tmp_path, ("2026-10-01", "2026-10-20"), ("VIIRS750",), bp._coords_por_volcan(),
                            {v: 5.0 for v in bp.VOLS})
    assert [r["z"] for r in out] == [41.5, None]


# ------------------------------------------------------------------ causa de la ausencia (hueco de NASA)
REF_12 = [fila("2026-10-12 04:36:10", "RUTINA", 0.0), fila("2026-10-12 05:18:02", "ALERTA_TERMICA", 8.44, dist=1.68),
          fila("2026-10-12 05:54:20", "ALERTA_TERMICA", 0.40), fila("2026-10-12 06:12:05", "RUTINA", 0.0)]
PROD_12 = [rec("2026-10-12 04:36", pub=False, disp=0), rec("2026-10-12 05:18", disp=3.46),
           rec("2026-10-12 05:54", pub=False, disp=0), rec("2026-10-12 06:12", pub=False, disp=0)]
BRAZO_12 = [rec("2026-10-12 04:36", pub=False, disp=0), rec("2026-10-12 06:12", pub=False, disp=0)]


def _json_cobertura(path, fallas=(), incidencias=()):
    path.write_text(json.dumps({"fallas": list(fallas), "n": len(fallas), "incidencias": list(incidencias),
                                "n_incidencias": len(incidencias), "plataformas": {}, "retiradas": [],
                                "sin_granulos": []}), encoding="utf-8")
    return path


def _inc(tipo, plataforma, volcan=CH, fecha="2026-10-12"):
    return {"tipo": tipo, "cuenta_estricto": tipo != "sin_granulos", "volcan": volcan, "fecha": fecha,
            "plataforma": plataforma, "motivo": "x"}


def _falla(etapa, plataforma, volcan=CH, fecha="2026-10-12"):
    return {"volcan": volcan, "fecha": fecha, "plataforma": plataforma, "producto": "P", "etapa": etapa,
            "motivo": "SEARCH_CMR_TIMEOUT"}


def test_cargar_eventos_lee_fallas_e_incidencias_de_varios_json(tmp_path):
    a = _json_cobertura(tmp_path / "a.json", fallas=[_falla("busqueda", "VIIRS_NOAA21_750")])
    b = _json_cobertura(tmp_path / "b.json", incidencias=[_inc("sin_granulos", "VIIRS_SNPP_750"),
                                                          _inc("dia_parcial", None)])
    ev = ec.cargar_eventos_cobertura([a, b])
    assert sorted((e["tipo"], e["plataforma"]) for e in ev) == [
        ("dia_parcial", None), ("falla_busqueda", "VIIRS_NOAA21_750"), ("sin_granulos", "VIIRS_SNPP_750")]


def _fila_T(ref=REF_12, lados=None):
    lados = lados or {"prod": PROD_12, "K": list(BRAZO_12)}
    return ec.tabla_por_pasada(pasadas(ref), lados, "prod")


def test_causa_de_la_ausencia_por_tipo_de_evento():
    T = _fila_T()
    f = [x for x in T if x["pasada"].instante.strftime("%H:%M") == "05:18"][0]
    assert f["cob"]["K"] == ec.FALTA
    causa = lambda ev: ec.causa_ausencia(f, "K", ev)  # noqa: E731
    assert causa(None) == ec.CAUSA_SIN_REGISTRO
    assert causa([]) == ec.CAUSA_SIN_INCIDENCIA
    assert causa([{"tipo": "falla_busqueda", "volcan": CH, "fecha": "2026-10-12", "plataforma": "VIIRS_NOAA21_750"}]) \
        == ec.CAUSA_HUECO
    assert causa([{"tipo": "falla_descarga", "volcan": CH, "fecha": "2026-10-12", "plataforma": "VIIRS_NOAA21_750"}]) \
        == ec.CAUSA_HUECO
    assert causa([{"tipo": "sin_geolocalizacion", "volcan": CH, "fecha": "2026-10-12",
                   "plataforma": "VIIRS_NOAA20_750"}]) == ec.CAUSA_HUECO
    assert causa([{"tipo": "dia_parcial", "volcan": CH, "fecha": "2026-10-12", "plataforma": None}]) == ec.CAUSA_HUECO
    assert causa([{"tipo": "sin_granulos", "volcan": CH, "fecha": "2026-10-12", "plataforma": "VIIRS_NOAA21_750"}]) \
        == ec.CAUSA_VACIA
    # la falla manda sobre la búsqueda vacía
    assert causa([{"tipo": "sin_granulos", "volcan": CH, "fecha": "2026-10-12", "plataforma": "VIIRS_SNPP_750"},
                  {"tipo": "falla_busqueda", "volcan": CH, "fecha": "2026-10-12", "plataforma": "VIIRS_NOAA21_750"}]) \
        == ec.CAUSA_HUECO


def test_eventos_de_otro_sensor_volcan_o_dia_no_explican_la_ausencia():
    T = _fila_T()
    f = [x for x in T if x["pasada"].instante.strftime("%H:%M") == "05:18"][0]
    for ev in ({"tipo": "falla_busqueda", "volcan": CH, "fecha": "2026-10-12", "plataforma": "VIIRS_NOAA21"},  # 375
               {"tipo": "falla_busqueda", "volcan": CH, "fecha": "2026-10-12", "plataforma": "MODIS_AQUA"},
               {"tipo": "falla_busqueda", "volcan": "Lascar", "fecha": "2026-10-12", "plataforma": "VIIRS_NOAA21_750"},
               {"tipo": "falla_busqueda", "volcan": CH, "fecha": "2026-10-11", "plataforma": "VIIRS_NOAA21_750"},
               {"tipo": "sin_granulos", "volcan": CH, "fecha": "2026-10-12", "plataforma": "VIIRS_NOAA21"}):
        assert ec.causa_ausencia(f, "K", [ev]) == ec.CAUSA_SIN_INCIDENCIA, ev


def test_falla_sin_volcan_cubre_todos_los_volcanes_del_dia():
    T = _fila_T()
    f = [x for x in T if x["pasada"].instante.strftime("%H:%M") == "05:18"][0]
    ev = [{"tipo": "falla_busqueda", "volcan": None, "fecha": "2026-10-12", "plataforma": None}]
    assert ec.causa_ausencia(f, "K", ev) == ec.CAUSA_HUECO


def test_lado_con_record_no_tiene_causa():
    T = _fila_T()
    f = [x for x in T if x["pasada"].instante.strftime("%H:%M") == "05:18"][0]
    assert ec.causa_ausencia(f, "prod", []) is None


def test_el_caso_del_12_oct_queda_como_busqueda_vacia_y_no_cambia_el_veredicto(tmp_path):
    """Los logs del A/B: SEARCH_DONE VIIRS_NOAA21_750 n_l1b=0 y Suomi NPP igual; NOAA-20 sí entregó."""
    lados = {"prod": PROD_12, "K": list(BRAZO_12), "D": list(BRAZO_12)}
    T = ec.tabla_por_pasada(pasadas(REF_12), lados, "prod")
    veredicto_antes = ec.cobertura(T, lados, "prod")
    jk = _json_cobertura(tmp_path / "k.json", incidencias=[_inc("sin_granulos", "VIIRS_NOAA21_750"),
                                                           _inc("sin_granulos", "VIIRS_SNPP_750")])
    ev = {"K": ec.cargar_eventos_cobertura([jk]), "D": ec.cargar_eventos_cobertura([jk]), "prod": []}
    h = ec.huecos(T, ev)
    assert h["K"]["por_causa"] == {ec.CAUSA_VACIA: {ec.FALTA: 2}}       # 05:18 protegida y 05:54
    assert h["K"]["protegidas"] == ["%s|VIIRS750|2026-10-12 05:18:02 (MIROVA 8.44 MW) %s %s"
                                    % (CH, ec.FALTA, ec.CAUSA_VACIA)]
    assert h["prod"]["por_causa"] == {} and h["prod"]["protegidas"] == []
    assert ec.cobertura(T, lados, "prod") == veredicto_antes and veredicto_antes["veredicto"] == ec.INVALIDO


def test_huecos_cuenta_tambien_las_no_observadas_y_sin_registro():
    ref = REF_12 + [fila("2026-10-12 07:00:00", "ALERTA_TERMICA", 3.0)]   # nadie la tiene
    lados = {"prod": PROD_12, "K": list(BRAZO_12)}
    T = ec.tabla_por_pasada(pasadas(ref), lados, "prod")
    h = ec.huecos(T, {"prod": [], "K": None})
    assert h["prod"]["por_causa"] == {ec.CAUSA_SIN_INCIDENCIA: {ec.NO_OBSERVADO: 1}}
    assert h["K"]["por_causa"] == {ec.CAUSA_SIN_REGISTRO: {ec.FALTA: 2, ec.NO_OBSERVADO: 1}}
    assert len(h["K"]["protegidas"]) == 2 and len(h["prod"]["protegidas"]) == 1


def test_huecos_respeta_dias_excluidos():
    lados = {"prod": PROD_12, "K": list(BRAZO_12)}
    T = ec.tabla_por_pasada(pasadas(REF_12), lados, "prod")
    h = ec.huecos(T, {"prod": [], "K": []}, dias_excluidos=("2026-10-12",))
    assert h["K"]["por_causa"] == {} and h["K"]["protegidas"] == []


# ------------------------------------------------------------------ CLI
def test_main_informa_estratos_y_causas_sin_tocar_el_veredicto(tmp_path, monkeypatch):
    import banco_paridad as bp
    import referencia_mirova_unificada as rmu
    lados = {"prod": [dict(r, z=40.0) for r in PROD_12], "K": [dict(r, z=40.0) for r in BRAZO_12]}
    monkeypatch.setattr(rmu, "cargar_referencia_unificada", lambda *a, **k: REF_12)
    monkeypatch.setattr(bp, "_coords_por_volcan", lambda: {})
    monkeypatch.setattr(bp, "inner_desde_html", lambda: {})
    monkeypatch.setattr(ec, "cargar_lado", lambda d, *a: (lados[Path(d).name], []))
    monkeypatch.setattr(ec, "pasadas_nocturnas", lambda ref, *a: pasadas(ref))
    (tmp_path / "cob").mkdir()
    _json_cobertura(tmp_path / "cob" / "c1.json", incidencias=[_inc("sin_granulos", "VIIRS_NOAA21_750")])
    _json_cobertura(tmp_path / "cob" / "c2.json", fallas=[_falla("descarga", "VIIRS_SNPP_750")])
    salida = tmp_path / "s.json"
    cod = ec.main(["--lado", "prod=%s" % (tmp_path / "prod"), "--lado", "K=%s" % (tmp_path / "K"),
                   "--control", "prod", "--desde", "2026-10-01", "--hasta", "2026-10-20", "--ref", str(tmp_path),
                   "--cobertura", "K=%s" % (tmp_path / "cob" / "c*.json"), "--salida", str(salida)])
    res = json.loads(salida.read_text(encoding="utf-8"))
    assert cod == 2 and res["cobertura"]["veredicto"] == ec.INVALIDO
    assert res["huecos"]["K"]["por_causa"] == {ec.CAUSA_HUECO: {ec.FALTA: 2}}   # la falla de c2 manda
    assert res["huecos"]["prod"]["por_causa"] == {}
    assert list(res["estratos"]["cenit"]) == ["z40-50"]       # el control observa las cuatro, todas a 40°
    assert res["estratos"]["regimen"]["535_a_K"]["pasadas"] == 4
    assert res["estratos"]["cenit"]["z40-50"]["p1b"]["K"] == {"abajo": 0, "arriba": 0}
