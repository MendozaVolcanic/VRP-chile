"""Miniaturas por pasada para las «Últimas 10 imágenes» del tablero (diseño: docs/DISENO_MINIATURAS_POR_PASADA.md).

POR QUÉ estas pruebas: una pasada con VRP 0 no dice si el volcán estaba tranquilo, nublado o con la escena cortada;
la miniatura lo muestra. Lo que no puede pasar es que la miniatura mienta (gris que no es el NTI, sin dato pintado
como foco, alertados que no son los del record), que la clave interna llegue al JSON del store, que la rotación pierda
la imagen de una pasada porque NASA no entregó el gránulo en esta corrida, o que el NRT haga un commit cada 2 h sin
pasadas nuevas. Sin red: grillas y gránulos sintéticos.
"""
import io
import json
import re
import sys
import zlib
from pathlib import Path

import numpy as np
import pytest
import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline import miniaturas as MINI  # noqa: E402


# ----------------------------------------------------------------------------------------- utilidades de prueba
def _decodificar_png_gris(datos):
    """Decodificador mínimo de PNG gris de 8 bits (los cinco filtros), para no depender de Pillow en la prueba."""
    assert datos[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, ancho, alto = 8, b"", None, None
    while pos < len(datos):
        largo = int.from_bytes(datos[pos:pos + 4], "big")
        tipo = datos[pos + 4:pos + 8]
        cuerpo = datos[pos + 8:pos + 8 + largo]
        if tipo == b"IHDR":
            ancho, alto = int.from_bytes(cuerpo[:4], "big"), int.from_bytes(cuerpo[4:8], "big")
            assert cuerpo[8] == 8 and cuerpo[9] == 0, "se espera gris de 8 bits"
        elif tipo == b"IDAT":
            idat += cuerpo
        pos += 12 + largo
    crudo = zlib.decompress(idat)
    out = np.zeros((alto, ancho), np.uint8)
    previa = np.zeros(ancho, np.int32)
    for f in range(alto):
        fila = crudo[f * (ancho + 1):(f + 1) * (ancho + 1)]
        filtro, x = fila[0], np.frombuffer(fila[1:], np.uint8).astype(np.int32)
        rec = np.zeros(ancho, np.int32)
        for c in range(ancho):
            a = rec[c - 1] if c else 0
            b = previa[c]
            cc = previa[c - 1] if c else 0
            if filtro == 0:
                p = 0
            elif filtro == 1:
                p = a
            elif filtro == 2:
                p = b
            elif filtro == 3:
                p = (a + b) // 2
            else:
                pa, pb, pc = abs(b - cc), abs(a - cc), abs(a + b - 2 * cc)
                p = a if pa <= pb and pa <= pc else (b if pb <= pc else cc)
            rec[c] = (x[c] + p) % 256
        out[f] = rec
        previa = rec
    return out


def _nti_cuerpo_negro(T, familia):
    cfg = MV.FAMILIAS[familia]
    a = MV.temperatura_a_radiancia(T, cfg["lam_mir"])
    b = MV.temperatura_a_radiancia(T, cfg["lam_tir"])
    return (a - b) / (a + b)


def _grillas(T_mir, T_tir, familia="VIIRS750", n=67):
    cfg = MV.FAMILIAS[familia]
    m13 = MV.temperatura_a_radiancia(np.full((n, n), float(T_mir)), cfg["lam_mir"])
    m15 = MV.temperatura_a_radiancia(np.full((n, n), float(T_tir)), cfg["lam_tir"])
    return m13, m15


# ----------------------------------------------------------------------------------------- 1. la imagen
def test_png_gris_es_un_png_valido_y_sin_perdida():
    rng = np.random.default_rng(1)
    u8 = rng.integers(0, 256, (37, 23), dtype=np.uint8)
    datos = MINI.png_gris(u8)
    assert np.array_equal(_decodificar_png_gris(datos), u8)


def test_png_gris_es_determinista():
    """Mismos datos, mismos bytes: si no, git vería un cambio en cada corrida del NRT."""
    u8 = np.arange(64 * 64, dtype=np.uint32).reshape(64, 64).astype(np.uint8)
    assert MINI.png_gris(u8) == MINI.png_gris(u8.copy())


@pytest.mark.parametrize("familia", ["VIIRS750", "VIIRS375", "MODIS"])
def test_la_escala_es_el_nti_de_un_cuerpo_negro_entre_las_dos_temperaturas(familia):
    lo, hi = MV.escala_nti(familia)
    t_lo, t_hi = MV.ESCALA_MINIATURA_T_K
    assert lo == pytest.approx(float(_nti_cuerpo_negro(t_lo, familia)))
    assert hi == pytest.approx(float(_nti_cuerpo_negro(t_hi, familia)))
    assert lo < hi


@pytest.mark.parametrize("familia", ["VIIRS750", "VIIRS375", "MODIS"])
def test_frio_es_negro_tibio_es_blanco_y_sin_dato_es_255(familia):
    t_lo, t_hi = MV.ESCALA_MINIATURA_T_K
    m13, m15 = _grillas(t_lo, t_lo, familia, n=9)
    m13[0, 0] = MV.temperatura_a_radiancia(t_hi, MV.FAMILIAS[familia]["lam_mir"])
    m15[0, 0] = MV.temperatura_a_radiancia(t_hi, MV.FAMILIAS[familia]["lam_tir"])
    m13[1, 1] = MV.temperatura_a_radiancia(900.0, MV.FAMILIAS[familia]["lam_mir"])   # foco: satura en 254, no en 255
    m13[2, 2] = np.nan                                                               # fuera de la franja
    m15[3, 3] = np.nan
    mini = MV.miniatura_nti(m13, m15, [[1, 1]], familia)
    u = mini["u8"]
    assert u.dtype == np.uint8 and u.shape == (9, 9)
    assert u[4, 4] == 0
    assert u[0, 0] == 254
    assert u[1, 1] == 254
    assert u[2, 2] == 255 and u[3, 3] == 255
    assert int((u == 255).sum()) == 2
    assert mini["alertadas"] == [[1, 1]]
    assert mini["n"] == 9
    assert mini["escala_nti"] == pytest.approx(list(MV.escala_nti(familia)))


def test_una_nube_fria_sale_mas_oscura_que_el_suelo():
    """El por qué de usar el NTI: de noche una nube es fría y sale oscura, como en el térmico."""
    m13, m15 = _grillas(270.0, 270.0)
    nube = (slice(10, 20), slice(10, 20))
    m13[nube] = MV.temperatura_a_radiancia(245.0, MV.LAMBDA_M13)
    m15[nube] = MV.temperatura_a_radiancia(245.0, MV.LAMBDA_M15)
    u = MV.miniatura_nti(m13, m15, [], "VIIRS750")["u8"]
    assert u[15, 15] < u[40, 40]


def test_los_percentiles_del_nti_van_en_la_miniatura_para_calibrar_la_escala():
    """Redondeados a 5 decimales (el índice queda chico; la escala se calibra a la milésima)."""
    m13, m15 = _grillas(260.0, 260.0)
    mini = MV.miniatura_nti(m13, m15, [], "VIIRS750")
    assert mini["nti_p2"] == pytest.approx(float(_nti_cuerpo_negro(260.0, "VIIRS750")), abs=1e-5)
    assert mini["nti_p98"] == pytest.approx(float(_nti_cuerpo_negro(260.0, "VIIRS750")), abs=1e-5)
    m13[:] = np.nan
    vacia = MV.miniatura_nti(m13, m15, [], "VIIRS750")
    assert vacia["nti_p2"] is None and vacia["nti_p98"] is None and int((vacia["u8"] == 255).sum()) == 67 * 67


# ----------------------------------------------------------------------------------------- 2. la vía
def _granulo_sintetico(lat0, lon0, familia, t_foco=600.0, n=81, span=0.3):
    cfg = MV.FAMILIAS[familia]
    la = lat0 + np.linspace(-span, span, n)
    lo = lon0 + np.linspace(-span, span, n) / np.cos(np.radians(lat0))
    LO, LA = np.meshgrid(lo, la[::-1])
    rng = np.random.default_rng(184)
    tm = 270.0 + rng.normal(0, 0.3, LA.shape)
    tt = 265.0 + rng.normal(0, 0.3, LA.shape)
    i, j = np.unravel_index(np.argmin((LA - lat0) ** 2 + ((LO - lon0) * np.cos(np.radians(lat0))) ** 2), LA.shape)
    tm[i, j] = t_foco
    b_mir, b_tir = cfg["bandas"]
    rad = {b_mir: MV.temperatura_a_radiancia(tm, cfg["lam_mir"]), b_tir: MV.temperatura_a_radiancia(tt, cfg["lam_tir"])}
    ang = {k: np.full(LA.shape, val) for k, val in (("solar_zenith", 120.0), ("sensor_zenith", 10.0),
                                                     ("solar_azimuth", 0.0), ("sensor_azimuth", 90.0))}
    return rad, LA, LO, ang


def _villarrica():
    vs = yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]
    return next(v for v in vs if v["name"] == "Villarrica")


def test_la_via_no_agrega_la_miniatura_con_el_interruptor_apagado(monkeypatch):
    """Apagado por defecto: 49 archivos llaman a la vía o a los procesadores y ninguno debe ver la clave."""
    assert MV.GENERAR_MINIATURA is False
    v = _villarrica()
    rad, LA, LO, ang = _granulo_sintetico(v["lat"], v["lon"], "VIIRS750")
    rec = MV.calcular_vrp_granulo(rad, LA, LO, ang, v["name"], v["lat"], v["lon"], 5.0, "SINTETICO")
    assert rec is not None and MINI.CLAVE not in rec


@pytest.mark.parametrize("familia,n", [("VIIRS750", 67), ("VIIRS375", 134), ("MODIS", 51)])
def test_la_via_agrega_la_grilla_entera_con_los_alertados_del_record(monkeypatch, familia, n):
    monkeypatch.setattr(MV, "GENERAR_MINIATURA", True)
    v = _villarrica()
    rad, LA, LO, ang = _granulo_sintetico(v["lat"], v["lon"], familia)
    rec = MV.calcular_vrp_granulo(rad, LA, LO, ang, v["name"], v["lat"], v["lon"], 5.0, "SINTETICO",
                                  familia=familia)
    mini = rec[MINI.CLAVE]
    assert mini["u8"].shape == (n, n) and mini["n"] == n
    assert rec["n_anomalous_pixels"] >= 1
    assert mini["alertadas"] == [[p["fila"], p["col"]] for p in rec["anomaly_pixels"]]
    f, c = mini["alertadas"][0]
    assert mini["u8"][f, c] >= 200   # el foco sale claro
    # la grilla entera, no la ROI del detector: hay gris (no 255) lejos del cráter
    assert mini["u8"][2, 2] != 255


def test_la_via_agrega_miniatura_tambien_sin_anomalia(monkeypatch):
    monkeypatch.setattr(MV, "GENERAR_MINIATURA", True)
    v = _villarrica()
    rad, LA, LO, ang = _granulo_sintetico(v["lat"], v["lon"], "VIIRS750", t_foco=270.0)
    rec = MV.calcular_vrp_granulo(rad, LA, LO, ang, v["name"], v["lat"], v["lon"], 5.0, "SINTETICO")
    assert rec["vrp_mw"] == 0.0 and rec[MINI.CLAVE]["alertadas"] == []


def _rec_sin_miniatura(monkeypatch, encendida, familia, t_foco, sin_radiancia):
    monkeypatch.setattr(MV, "GENERAR_MINIATURA", encendida)
    v = _villarrica()
    rad, LA, LO, ang = _granulo_sintetico(v["lat"], v["lon"], familia, t_foco=t_foco)
    if sin_radiancia:
        for b in rad:
            rad[b] = np.full(rad[b].shape, np.nan)
    rec = MV.calcular_vrp_granulo(rad, LA, LO, ang, v["name"], v["lat"], v["lon"], 5.0, "SINTETICO",
                                  familia=familia)
    assert (MINI.CLAVE in rec) is encendida
    rec.pop(MINI.CLAVE, None)
    return json.dumps(rec, sort_keys=True, default=str)


@pytest.mark.parametrize("familia", ["VIIRS750", "VIIRS375", "MODIS"])
@pytest.mark.parametrize("t_foco,sin_radiancia", [(600.0, False), (270.0, False), (270.0, True)])
def test_encender_la_miniatura_no_cambia_el_record_de_la_via(monkeypatch, familia, t_foco, sin_radiancia):
    """S198 (merge con main, A45 de Nicolás para #1015): con el interruptor encendido el record de la vía es byte a byte
    el mismo que apagado, salvo la clave interna que run_pipeline saca antes del store: mismo VRP, mismos alertados
    (máscara), misma posición y clase. Con foco, sin anomalía y sin radiancia válida (S192, grilla toda sin dato)."""
    apagado = _rec_sin_miniatura(monkeypatch, False, familia, t_foco, sin_radiancia)
    encendido = _rec_sin_miniatura(monkeypatch, True, familia, t_foco, sin_radiancia)
    assert apagado == encendido
    rec = json.loads(apagado)
    if t_foco == 600.0:   # el caso con foco ejercita VRP, máscara y posición, no sólo una escena vacía
        assert rec["vrp_mw"] > 0 and rec["n_anomalous_pixels"] >= 1 and rec["final_hotspot_lat"] is not None


# ----------------------------------------------------------------------------------------- 3. recolección y rotación
def _rec(dt, sensor="VIIRS_NOAA21", granule=None, vrp=0.0, via=True, pv="standard"):
    return {"datetime_utc": dt, "sensor": sensor, "granule": granule or f"G.{sensor}.{dt}", "product_version": pv,
            "vrp_mw": vrp, "sensor_zenith_deg": 30.0, "sensor_azimuth_deg": -80.0, "solar_zenith_deg": 120.0,
            "via_codigo_mirova": via, "n_anomalous_pixels": 1 if vrp else 0, "distance_class": None,
            "final_hotspot_dist_km": None,
            "diag_codigo_mirova": {"motivo_vacio": None, "celdas_sin_dato": 0, "dayflag": 0}}


def _mini(valor=100, n=4):
    return {"u8": np.full((n, n), valor, np.uint8), "n": n, "escala_nti": [-0.97, -0.88], "alertadas": [],
            "nti_p2": -0.95, "nti_p98": -0.93}


def test_familia_de_sensor():
    assert MINI.familia_de_sensor("VIIRS_NOAA21") == "VIIRS375"
    assert MINI.familia_de_sensor("VIIRS_SNPP_750") == "VIIRS750"
    assert MINI.familia_de_sensor("MODIS_AQUA") == "MODIS"
    assert MINI.familia_de_sensor("SINTETICO") is None


def test_recoger_saca_la_clave_del_record():
    rc = MINI.Recolector()
    r = _rec("2026-11-15 06:18")
    r[MINI.CLAVE] = _mini()
    rc.recoger("Llaima", r)
    assert MINI.CLAVE not in r
    json.dumps(r)   # el store lo puede guardar
    sin = _rec("2026-11-15 05:00")
    rc.recoger("Llaima", sin)   # un record sin miniatura (K) no rompe
    assert rc.cantidad("Llaima") == 1


def test_rotacion_deja_las_10_mas_nuevas_y_borra_las_viejas(tmp_path):
    rc = MINI.Recolector()
    recs = [_rec(f"2026-11-{d:02d} 05:00") for d in range(1, 13)]
    for r in recs:
        r[MINI.CLAVE] = _mini()
        rc.recoger("Llaima", r)
    viejo = tmp_path / "Llaima" / "VIIRS375" / "20261020_0500_VIIRS_NOAA21.png"
    viejo.parent.mkdir(parents=True)
    viejo.write_bytes(b"x")
    idx = rc.escribir_volcan("Llaima", recs, tmp_path)
    pngs = sorted(p.name for p in (tmp_path / "Llaima" / "VIIRS375").glob("*.png"))
    assert len(pngs) == 10 and not viejo.exists()
    fechas = [e["datetime_utc"] for e in idx["familias"]["VIIRS375"]]
    assert fechas == sorted(fechas, reverse=True) and fechas[0] == "2026-11-12 05:00" and len(fechas) == 10
    assert idx["familias"]["VIIRS750"] == [] and idx["familias"]["MODIS"] == []
    en_disco = json.loads((tmp_path / "Llaima" / "indice.json").read_text(encoding="utf-8"))
    assert en_disco == json.loads(json.dumps(idx))
    for e in idx["familias"]["VIIRS375"]:
        assert (tmp_path / "Llaima" / e["archivo"]).exists()


def test_sin_gránulo_en_esta_corrida_se_conserva_la_imagen_anterior(tmp_path):
    recs = [_rec("2026-11-14 05:00"), _rec("2026-11-15 05:00")]
    rc1 = MINI.Recolector()
    for r in recs:
        r2 = dict(r, **{MINI.CLAVE: _mini(50)})
        rc1.recoger("Llaima", r2)
    idx1 = rc1.escribir_volcan("Llaima", recs, tmp_path)
    rc2 = MINI.Recolector()           # corrida siguiente: NASA no entregó el gránulo del 14
    rc2.recoger("Llaima", dict(recs[1], **{MINI.CLAVE: _mini(50)}))
    idx2 = rc2.escribir_volcan("Llaima", recs, tmp_path)
    e14 = [e for e in idx2["familias"]["VIIRS375"] if e["datetime_utc"] == "2026-11-14 05:00"][0]
    assert e14["archivo"] is not None and (tmp_path / "Llaima" / e14["archivo"]).exists()
    assert idx1 == idx2


def test_reemplazo_nrt_a_estandar_sin_imagen_nueva_no_reusa_la_del_nrt(tmp_path):
    nrt = _rec("2026-11-15 05:00", granule="G_NRT", pv="nrt")
    rc1 = MINI.Recolector()
    rc1.recoger("Llaima", dict(nrt, **{MINI.CLAVE: _mini()}))
    rc1.escribir_volcan("Llaima", [nrt], tmp_path)
    est = _rec("2026-11-15 05:00", granule="G_STD", pv="standard")
    idx = MINI.Recolector().escribir_volcan("Llaima", [est], tmp_path)
    e = idx["familias"]["VIIRS375"][0]
    assert e["granule"] == "G_STD" and e["archivo"] is None and e["sin_imagen"] == "sin_granulo_en_esta_corrida"
    assert list((tmp_path / "Llaima" / "VIIRS375").glob("*.png")) == []


def test_la_imagen_sigue_al_gránulo_del_record_guardado(tmp_path):
    """Si la corrida trae una miniatura de otro gránulo que el guardado, no se usa."""
    est = _rec("2026-11-15 05:00", granule="G_STD")
    rc = MINI.Recolector()
    rc.recoger("Llaima", dict(est, granule="G_NRT", **{MINI.CLAVE: _mini()}))
    e = rc.escribir_volcan("Llaima", [est], tmp_path)["familias"]["VIIRS375"][0]
    assert e["archivo"] is None


def test_pasada_de_k_queda_sin_imagen_con_su_motivo(tmp_path):
    k = _rec("2026-11-15 05:00", sensor="MODIS_AQUA", via="sin_mxd03")
    e = MINI.Recolector().escribir_volcan("Llaima", [k], tmp_path)["familias"]["MODIS"][0]
    assert e["archivo"] is None and e["sin_imagen"] == "detector_k"
    assert e["via_codigo_mirova"] == "sin_mxd03"


def test_el_indice_copia_los_campos_del_record(tmp_path):
    r = _rec("2026-11-15 06:18", vrp=1.857)
    r["diag_codigo_mirova"].update({"motivo_vacio": "escena_invalida", "celdas_sin_dato": 9309})
    rc = MINI.Recolector()
    rc.recoger("Llaima", dict(r, **{MINI.CLAVE: dict(_mini(), alertadas=[[2, 3]])}))
    e = rc.escribir_volcan("Llaima", [r], tmp_path)["familias"]["VIIRS375"][0]
    assert e["vrp_mw"] == 1.857 and e["sensor_zenith_deg"] == 30.0 and e["sensor_azimuth_deg"] == -80.0
    assert e["motivo_vacio"] == "escena_invalida" and e["celdas_sin_dato"] == 9309 and e["dayflag"] == 0
    assert e["alertadas"] == [[2, 3]] and e["n"] == 4 and e["escala_nti"] == [-0.97, -0.88]
    assert e["archivo"] == "VIIRS375/20261115_0618_VIIRS_NOAA21.png"


def test_dos_corridas_iguales_no_cambian_ningun_byte(tmp_path):
    """Sin pasadas nuevas no hay commit: ni el índice ni los PNG cambian (no hay sello de hora de la corrida)."""
    recs = [_rec(f"2026-11-{d:02d} 05:00") for d in range(10, 15)]

    def correr():
        rc = MINI.Recolector()
        for r in recs:
            rc.recoger("Llaima", dict(r, **{MINI.CLAVE: _mini(77)}))
        rc.escribir_volcan("Llaima", recs, tmp_path)
        return {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in sorted(tmp_path.rglob("*")) if p.is_file()}

    assert correr() == correr()


# ----------------------------------------------------------------------------------------- 4. cableado
def test_run_pipeline_tiene_el_argumento_y_saca_la_clave_antes_de_cada_append_record():
    src = (RAIZ / "scripts" / "run_pipeline.py").read_text(encoding="utf-8")
    assert '"--miniaturas"' in src
    llamadas = len(re.findall(r"store\.append_record\(", src))
    recogidas = len(re.findall(r"_MINIATURAS\.recoger\(", src))
    assert llamadas >= 3 and recogidas == llamadas, (llamadas, recogidas)
    assert "_MINIATURAS.escribir_volcan(" in src


def test_solo_el_nrt_de_produccion_genera_miniaturas():
    """Sólo el paso del perfil mirova_equivalent de nrt.yml: un reproceso o una sombra escribiría fechas viejas o
    carpetas que nadie limpia, y dos escritores sobre la misma carpeta rompen A47."""
    flujos = sorted((RAIZ / ".github" / "workflows").glob("*.yml"))
    con = [p.name for p in flujos if "--miniaturas" in p.read_text(encoding="utf-8")]
    assert con == ["nrt.yml"]
    nrt = (RAIZ / ".github" / "workflows" / "nrt.yml").read_text(encoding="utf-8")
    linea = [ln for ln in nrt.splitlines() if "--miniaturas" in ln and not ln.strip().startswith("#")]
    assert len(linea) == 1
    bloque = nrt[nrt.index("--profile mirova_equivalent"):]
    assert bloque.index("--miniaturas") < bloque.index("\n\n")
    assert 'git add -A -- "data/miniaturas/${{ matrix.volcano }}"' in nrt
