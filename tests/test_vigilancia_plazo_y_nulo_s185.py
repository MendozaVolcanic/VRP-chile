# -*- coding: utf-8 -*-
"""S185: dos defectos de las vigilancias de la guardia K que no cambian ningún resultado de hoy.

D1. El plazo por días de la regla de reversión (§4.6: 29 protegidas o 120 días DESDE EL ENCENDIDO) se comparaba por fecha
(`hoy >= vence`): desde las 00:00 UTC del día de vencimiento la vigilancia daba el plazo por cumplido, aunque el encendido
es un instante (MODIS 2026-11-02 20:11:43 UTC; VIIRS 2026-11-11 13:39:30 y 13:45:35). Sólo afecta el rótulo `fase` y el
campo `duracion.cumplida`: `reversion` y `fuera_de_plazo` dependen del instante de cada pasada, que ya se comparaba bien.

D2. El nulo (antes del encendido, guardia y producción K publican lo mismo) declara una ventana de DIAS_NULO = 14 días, pero
la guardia empieza después (MODIS 2026-10-26, VIIRS 2026-11-03): el tramo que de verdad mide es menor y la salida no lo
decía. Se declara la ventana efectiva como campo aditivo y un aviso INFORMATIVO. No es un aviso de `avisos`: ese
convertiría un VERDE en VIGILANCIA_CIEGA, que es un cambio de la regla (la de VIIRS pide «al menos tres noches», §3).

Cada prueba tiene su control: el caso vecino que no tiene que cambiar. Contra el código original las pruebas nuevas tienen
que fallar por aserción con mensaje, no por KeyError: por eso se leen los campos nuevos con `.get()`.
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.vigilancia_guardia_viirs as vv  # noqa: E402

vg = vv.vg
NOCHE = lambda *a: False  # noqa: E731
VOLS_CASO = ["NevadosDeChillan", "Lascar"]
ENC_MODIS = "2026-11-02 20:11:43"
ENC_V375 = "2026-11-11 13:45:35"
ENC_V750 = "2026-11-11 13:39:30"
COTAS = {"muy_bajo": 2, "sobrepublicacion": 3}
SENS = {"MODIS": "MODIS_AQUA", "VIIRS375": "VIIRS_NOAA20", "VIIRS750": "VIIRS_NOAA20_750"}
ENCENDIDO = {"MODIS": ENC_MODIS, "VIIRS375": ENC_V375, "VIIRS750": ENC_V750}


def _vence(enc):
    return (datetime.strptime(enc, "%Y-%m-%d %H:%M:%S") + timedelta(days=vg.DIAS_MAXIMOS)).strftime("%Y-%m-%d %H:%M:%S")


def _rec(vol, fecha, hhmm, pub, b="MODIS", via=None):
    dt = datetime.strptime(f"{fecha} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha, "pub": pub, "sensor": SENS[b], "perfil": None,
            "lab": "sin_info", "via": via, "caida_k": None}


def _fila(vol, fecha, vrp, tipo="ALERTA_TERMICA", b="MODIS"):
    return {"volcano": vol, "sensor_bucket": b, "fecha_utc": fecha, "vrp_mw": vrp, "tipo": tipo, "source": "CONS"}


def _ventana(nulo):
    """`nulo.ventana_efectiva`, o una falla por aserción (no un KeyError) si el código no la declara."""
    v = (nulo or {}).get("ventana_efectiva")
    assert v is not None, "D2: el nulo no declara su ventana efectiva (falta nulo.ventana_efectiva)"
    return v


def _avisos_ventana(nulo):
    f = getattr(vg, "avisos_ventana_nulo", None)
    assert callable(f), "D2: falta avisos_ventana_nulo, el aviso informativo de la ventana del nulo"
    return f(nulo)


def _informativos(out):
    av = out.get("avisos_informativos")
    assert av is not None, "D2: la salida no trae el campo avisos_informativos"
    return av


class _Reloj:
    """Congela `datetime.now` de un módulo en un instante UTC: el `ahora` real de `evaluar` (D1 de punta a punta)."""

    def __init__(self, monkeypatch):
        self.mp = monkeypatch

    def en(self, modulo, instante):
        fijo = datetime.strptime(instante, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

        class Falso(datetime):
            @classmethod
            def now(cls, tz=None):
                return fijo if tz else fijo.replace(tzinfo=None)

        self.mp.setattr(modulo, "datetime", Falso)


# ------------------------------------------------------------------ D1: el plazo vence al instante, no a la medianoche
@pytest.mark.parametrize("sensor", ["MODIS", "VIIRS375", "VIIRS750"])
def test_d1_el_plazo_de_120_dias_vence_a_la_hora_del_encendido(sensor):
    enc = ENCENDIDO[sensor]
    vence = _vence(enc)
    dia = vence[:10]

    def cumplida(ahora):
        d = vg.disparadores([], [], [], hoy=dia, encendido=enc, ahora=ahora, sensor=sensor, cotas=COTAS)
        return d["duracion"]["cumplida"]

    # el defecto: a las 00:00 UTC del día de vencimiento y hasta el instante del encendido, el plazo seguía vigente
    assert cumplida(f"{dia} 00:00:00") is False, "D1: el plazo se da por cumplido a la medianoche del día de vencimiento"
    assert cumplida(f"{dia} 00:00:01") is False
    ultimo = (datetime.strptime(vence, "%Y-%m-%d %H:%M:%S") - timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")
    assert cumplida(ultimo) is False
    # control: en el instante y después, cumplido
    assert cumplida(vence) is True
    assert cumplida(f"{dia} 23:59:59") is True
    # control: el día siguiente completo, cumplido
    siguiente = (datetime.strptime(dia, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    assert cumplida(f"{siguiente} 00:00:00") is True


@pytest.mark.parametrize("sensor", ["MODIS", "VIIRS750"])
def test_d1_sin_ahora_el_dia_de_vencimiento_no_da_el_plazo_por_cumplido(sensor):
    """`ahora` por omisión es la medianoche de `hoy` (así lo usan las pruebas y la re-lectura): ese instante es anterior."""
    enc = ENCENDIDO[sensor]
    dia = _vence(enc)[:10]
    d = vg.disparadores([], [], [], hoy=dia, encendido=enc, sensor=sensor, cotas=COTAS)
    assert d["duracion"]["cumplida"] is False, "D1: cumplida con `hoy` igual al día de vencimiento y sin hora"
    d = vg.disparadores([], [], [], hoy=(datetime.strptime(dia, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
                        encendido=enc, sensor=sensor, cotas=COTAS)
    assert d["duracion"]["cumplida"] is True


def test_d1_las_29_protegidas_siguen_cumpliendo_el_plazo_antes_del_vencimiento():
    """Control: el otro límite del plazo no se tocó."""
    pas = [{"volcano": "A", "sensor": "MODIS", "fecha_utc": f"2026-11-{6 + i // 4:02d} {10 + i % 4:02d}:00",
            "instante_utc": f"2026-11-{6 + i // 4:02d} {10 + i % 4:02d}:00:00", "vrp_mirova_mw": 2.0,
            "protegida": True, "minima": False, "referencia_sospechosa": False, "prod_pub": True,
            "guardia_pub": True, "prod_via": True} for i in range(29)]
    d = vg.disparadores(pas, [], [], hoy="2026-11-21", encendido="2026-11-05 22:10:00", ahora="2026-11-21 10:00:00")
    assert d["duracion"]["protegidas_vistas_en_guardia"] == 29 and d["duracion"]["cumplida"] is True


def test_d1_la_reversion_depende_del_instante_de_la_pasada_no_de_cumplida():
    """Control (verificador S185): D1 corrige el rótulo, no la decisión. Una candidata 1 h antes del vencimiento es
    REVERSION_CANDIDATA a toda hora del día de vencimiento, con el arreglo y sin él."""
    enc = ENC_V750
    vence = _vence(enc)
    antes = (datetime.strptime(vence, "%Y-%m-%d %H:%M:%S") - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    pas = [{"volcano": "A", "sensor": "VIIRS750", "fecha_utc": antes, "instante_utc": antes + ":00",
            "vrp_mirova_mw": 2.0, "protegida": True, "minima": False, "referencia_sospechosa": False, "prod_pub": False,
            "guardia_pub": True, "prod_via": True}]
    for ahora in (f"{vence[:10]} 00:00:00", f"{vence[:10]} 23:59:59"):
        d = vg.disparadores(pas, [], [], hoy=vence[:10], encendido=enc, ahora=ahora, sensor="VIIRS750", cotas=COTAS)
        assert d["veredicto"] == "REVERSION_CANDIDATA", ahora


# ------------------------------------------------------------------ D2: ventana efectiva del nulo
def _nulo(sensor, enc, inicio_guardia, hoy="2026-11-20"):
    """Guardia con un record diario desde `inicio_guardia`; producción K con el mismo record antes del encendido."""
    b = sensor
    inicio = datetime.strptime(inicio_guardia, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    limite = datetime.strptime(enc, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    guardia, prod, t = [], [], inicio
    while t < limite:
        for lista in (guardia, prod):
            lista.append(_rec("A", t.strftime("%Y-%m-%d"), t.strftime("%H:%M"), False, b=b))
        t += timedelta(days=1)
    return vg.disparadores([], prod, guardia, hoy=hoy, encendido=enc, sensor=sensor, cotas=COTAS)["nulo"]


def test_d2_viirs750_declara_que_el_nulo_cubre_unos_8_dias_y_avisa():
    n = _nulo("VIIRS750", ENC_V750, "2026-11-03 01:30")
    v = _ventana(n)
    assert v.get("inicio_guardia") == "2026-11-03 01:30:00"
    assert v.get("desde") == "2026-11-03 01:30:00" and v.get("hasta") == ENC_V750
    assert v.get("desde_nominal") == "2026-10-28 13:39:30" and v.get("dias_declarados") == 14
    assert v.get("dias_cubiertos") == 8.5
    av = _avisos_ventana(n)
    assert len(av) == 1 and "8.5 de los 14" in av[0] and "2026-11-03" in av[0]


def test_d2_control_guardia_desde_antes_de_la_ventana_cubre_los_14_dias_sin_aviso():
    n = _nulo("VIIRS750", ENC_V750, "2026-10-20 01:30")
    v = _ventana(n)
    assert v.get("dias_cubiertos") == 14.0 and v.get("desde") == v.get("desde_nominal") == "2026-10-28 13:39:30"
    assert v.get("inicio_guardia") == "2026-10-20 01:30:00"
    assert _avisos_ventana(n) == []


def test_d2_el_nulo_mismo_no_cambia_con_la_ventana_efectiva():
    """Aditivo: pares, distintas y sin_medir son los de siempre, con guardia corta o larga."""
    for inicio in ("2026-11-03 01:30", "2026-10-20 01:30"):
        n = _nulo("VIIRS750", ENC_V750, inicio)
        assert n["pares"] > 0 and n["distintas"] == 0 and n["sin_medir"] is False
        assert "ventana_efectiva" in n, "D2: el nulo no declara su ventana efectiva"
        assert set(n) >= {"pares", "distintas", "detalle", "sin_medir", "nota", "ventana_efectiva"}


def test_d2_guardia_sin_records_cubre_0_dias_y_el_nulo_sigue_sin_medir():
    d = vg.disparadores([], [], [], hoy="2026-11-20", encendido=ENC_V750, sensor="VIIRS750", cotas=COTAS)
    n = d["nulo"]
    assert n["sin_medir"] is True
    v = _ventana(n)
    assert v.get("dias_cubiertos") == 0.0 and v.get("desde") is None
    assert len(_avisos_ventana(n)) == 1          # informativo; el de «sin pares» sigue siendo avisos_nulo
    assert vg.avisos_nulo(n)


def test_d2_el_nulo_sellado_conserva_la_ventana_efectiva_viva():
    vivo = {"pares": 0, "distintas": 0, "detalle": [], "sin_medir": True,
            "ventana_efectiva": {"desde": "2026-11-03 01:30:00", "hasta": ENC_V750, "desde_nominal": "2026-10-28 13:39:30",
                                 "dias_declarados": 14, "dias_cubiertos": 8.5, "inicio_guardia": "2026-11-03 01:30:00"}}
    sello = {"VIIRS750": {"encendido_utc": ENC_V750, "pares": 270, "distintas": 0, "detalle": [],
                          "ventana_utc": ["2026-10-28 13:39:30", ENC_V750], "medido_utc": "2026-11-12 04:52:32"}}
    n = vg.nulo_vigente(vivo, "VIIRS750", ENC_V750, sellado=sello)
    assert n["sellado"] is True and n["pares"] == 270 and n["sin_medir"] is False
    assert _ventana(n).get("dias_cubiertos") == 8.5, "D2: el nulo sellado perdió la ventana efectiva"
    assert n.get("ventana_sellada") == ["2026-10-28 13:39:30", ENC_V750]
    assert len(_avisos_ventana(n)) == 1 and vg.avisos_nulo(n) == []
    # un nulo vivo con pares manda y no se toca
    medido = dict(vivo, pares=5, sin_medir=False)
    assert vg.nulo_vigente(medido, "VIIRS750", ENC_V750, sellado=sello) is medido


def test_d2_modis_declara_7_7_dias_de_14():
    """El caso real de MODIS: la guardia arranca el 2026-10-26 y el encendido es el 2026-11-02 20:11:43."""
    n = _nulo("MODIS", ENC_MODIS, "2026-10-26 03:00")
    assert _ventana(n).get("dias_cubiertos") == 7.7
    assert len(_avisos_ventana(n)) == 1


# ------------------------------------------------------------------ de punta a punta: evaluar() de cada vigilancia
def _caso(b, inicio_guardia, fin="2026-11-11"):
    """Pasadas de relleno de la guardia y de producción (K) desde `inicio_guardia` hasta antes de `fin` (el día del
    encendido, o el siguiente), una alerta protegida que las dos publican y registros frescos para que no haya ceguera."""
    filas = [_fila("NevadosDeChillan", "2026-11-12 07:20:00", 2.18, b=b),
             _fila("Lascar", "2026-11-19 06:00:00", 0.0, tipo="RUTINA", b=b)]
    prod = [_rec("NevadosDeChillan", "2026-11-12", "07:20", True, b=b, via=True)]
    guardia = [_rec("NevadosDeChillan", "2026-11-12", "07:20", True, b=b)]
    for v in VOLS_CASO:
        prod.append(_rec(v, "2026-11-19", "03:00", False, b=b, via=True))
        guardia.append(_rec(v, "2026-11-19", "03:00", False, b=b))
    t = datetime.strptime(inicio_guardia, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    while t < datetime.strptime(fin, "%Y-%m-%d").replace(tzinfo=timezone.utc):
        for v in VOLS_CASO:
            prod.append(_rec(v, t.strftime("%Y-%m-%d"), "03:00", False, b=b))
            guardia.append(_rec(v, t.strftime("%Y-%m-%d"), "03:00", False, b=b))
        t += timedelta(days=1)
    return filas, prod, guardia


@pytest.fixture
def poner(monkeypatch):
    """Insumos falsos para `vv.evaluar` (VIIRS) y para `vg.evaluar` (MODIS)."""
    def _poner(filas, prod, guardia, sensor, enc):
        monkeypatch.setattr(vg, "flag_produccion_encendido", lambda s="MODIS": True)
        monkeypatch.setattr(vg.vs, "_diurna_por_defecto", lambda: NOCHE)
        monkeypatch.setattr(vg.aa, "VOLS", VOLS_CASO)
        if sensor == "MODIS":
            monkeypatch.setattr(vg, "cargar_insumos", lambda win, via, caidas=None: (filas, prod, guardia, 0))
            monkeypatch.setattr(vg, "leer_encendido", lambda: {"encendido_utc": enc, "primera_observacion": None,
                                                              "via": set()})
            monkeypatch.setattr(vg, "leer_juzgadas", lambda *a: {})
        else:
            monkeypatch.setattr(vv, "cargar_insumos", lambda win, via, caidas, s: (filas, prod, guardia, 0))
            monkeypatch.setattr(vv, "leer_encendido", lambda s: {"encendido_utc": enc, "primera_observacion": None,
                                                                "via": set()})
            monkeypatch.setattr(vv, "leer_juzgadas", lambda *a: {})
            monkeypatch.setattr(vv, "volcanes_sens", lambda: [])
    return _poner


def _evaluar(sensor, hoy):
    """La `evaluar` de cada vigilancia: MODIS (vg) o VIIRS (vv, con clave v375 o v750)."""
    if sensor == "MODIS":
        return vg.evaluar(hoy)
    return vv.evaluar(hoy, {"VIIRS375": "v375", "VIIRS750": "v750"}[sensor])


def _modulo(sensor):
    return vg if sensor == "MODIS" else vv


@pytest.mark.parametrize("sensor,corto,largo,fin", [
    ("VIIRS750", "2026-11-03", "2026-10-20", "2026-11-11"),
    ("VIIRS375", "2026-11-03", "2026-10-20", "2026-11-11"),
    # MODIS (M7 del verificador): su camino de `evaluar` es otro código que el de VIIRS
    ("MODIS", "2026-10-26", "2026-10-15", "2026-11-03"),
])
def test_d2_evaluar_avisa_la_ventana_corta_sin_cambiar_el_veredicto(poner, sensor, corto, largo, fin, capsys):
    enc = ENCENDIDO[sensor]
    poner(*_caso(sensor, corto, fin), sensor=sensor, enc=enc)
    out_corto = _evaluar(sensor, "2026-11-20")
    assert out_corto["veredicto"] == "VERDE", out_corto["avisos"]
    assert out_corto["avisos"] == [], "el aviso informativo no puede entrar en `avisos` (cambiaría el veredicto)"
    assert len(_informativos(out_corto)) == 1, "D2: no avisa que el nulo cubre menos de los días declarados"
    assert _ventana(out_corto["nulo"])["dias_cubiertos"] < 14
    _modulo(sensor).imprimir(out_corto)
    salida = capsys.readouterr().out
    assert "AVISO (informativo):" in salida and "días (" in salida
    # control: con la guardia desde antes de la ventana, mismo veredicto, sin aviso informativo
    poner(*_caso(sensor, largo, fin), sensor=sensor, enc=enc)
    out_largo = _evaluar(sensor, "2026-11-20")
    assert out_largo["veredicto"] == "VERDE" and _informativos(out_largo) == []
    assert _ventana(out_largo["nulo"])["dias_cubiertos"] == 14.0
    assert out_largo["nulo"]["pares"] > out_corto["nulo"]["pares"] > 0


@pytest.mark.parametrize("sensor", ["MODIS", "VIIRS750", "VIIRS375"])
def test_d1_evaluar_con_su_ahora_real_no_cumple_el_plazo_antes_de_la_hora_del_encendido(poner, monkeypatch, sensor):
    """D1 de punta a punta: `evaluar` toma `ahora` del reloj. El día de vencimiento, antes de la hora del encendido, la fase
    sigue en «vigilando» y `cumplida` es False; desde la hora del encendido, «plazo_cumplido». Contra el defecto
    (`hoy >= vence`) la primera mitad falla; contra un `ahora` que cae a la medianoche dentro de `evaluar` (M10) falla la
    segunda."""
    enc = ENCENDIDO[sensor]
    vence = _vence(enc)
    dia = vence[:10]
    fin = "2026-11-03" if sensor == "MODIS" else "2026-11-11"
    poner(*_caso(sensor, "2026-10-26" if sensor == "MODIS" else "2026-11-03", fin), sensor=sensor, enc=enc)
    reloj = _Reloj(monkeypatch)
    # 1 h antes del vencimiento, el mismo día UTC
    antes = (datetime.strptime(vence, "%Y-%m-%d %H:%M:%S") - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    assert antes[:10] == dia
    reloj.en(_modulo(sensor), antes)
    out = _evaluar(sensor, dia)
    assert out["duracion"]["cumplida"] is False, "D1: el plazo se da por cumplido antes de la hora del encendido"
    assert out["fase"] == "vigilando", out["fase"]
    # 1 h después, el mismo día: cumplido (si `ahora` cayera a la medianoche dentro de `evaluar`, seguiría vigente)
    despues = (datetime.strptime(vence, "%Y-%m-%d %H:%M:%S") + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    assert despues[:10] == dia
    reloj.en(_modulo(sensor), despues)
    out = _evaluar(sensor, dia)
    assert out["duracion"]["cumplida"] is True and out["fase"] == "plazo_cumplido", out["fase"]
