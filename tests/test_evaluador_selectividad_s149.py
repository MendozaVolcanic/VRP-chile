"""S149: tres arreglos del evaluador del A/B (experiments/_s146_ab_sin_test1/evaluar.py).

POR QUE EXISTE
--------------
1. C8 pedia que el contraste quedara FUERA del nulo barajado a dos colas, y un apagador al azar lo
   cumplia en 200 de 200 semillas (verificador S148): no probaba selectividad. El reemplazo mide
   supervivencia de positivas contra negativos SOLO entre las pasadas que el control publica, a una
   cola. Aca se prueba con datos sinteticos lo que importa: un apagador al azar NO lo cumple, uno
   selectivo SI, y uno selectivo al reves (apaga las positivas) NO.
2. La banda del control positivo esta calibrada para produccion de septiembre; con otro control u
   otra ventana imprimia INDECIDIBLE sin que nada estuviera mal. Se apaga solo por parametro.
3. Una pasada donde MIROVA lista VRP 0 en una noche con alerta por otra pasada cae en sin_info, y el
   evaluador no la veia (docs/S149_COSTO_OCULTO_MAX.md). Campos aditivos, ninguna etiqueta cambia.
"""
import os
import random
import sys
from datetime import datetime, timedelta, timezone

import importlib.util

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Se carga POR RUTA y con nombre propio: en el repo hay mas de un `evaluar.py` (el de S143, este) y
# dentro de la suite completa `import evaluar` devolvia el que otro test habia cargado antes. Pasaba
# solo y fallaba acompanado, que es el peor modo de fallar.
_spec = importlib.util.spec_from_file_location(
    "evaluar_s146_para_s149", os.path.join(RAIZ, "experiments", "_s146_ab_sin_test1", "evaluar.py"))
ev = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = ev
_spec.loader.exec_module(ev)

bp = ev.bp


def _corpus(n_vol=4, n_pos=40, n_neg=40):
    """Control que publica todo: n_pos positivas y n_neg negativos limpios por volcan."""
    ctrl = []
    t0 = datetime(2026, 9, 1, 5, 0, tzinfo=timezone.utc)
    for v in range(n_vol):
        for i in range(n_pos + n_neg):
            ctrl.append({"vol": "V%d" % v, "b": "VIIRS375", "dt": t0 + timedelta(minutes=7 * i + v),
                         "lab": "pos" if i < n_pos else "neg_limpio", "pub": 1})
    return ctrl


def _brazo(ctrl, apaga):
    return [dict(c, pub=0 if apaga(c) else 1) for c in ctrl]


def test_un_apagador_al_azar_no_cumple_la_selectividad():
    ctrl = _corpus()
    cumple = 0
    for s in range(40):
        rnd = random.Random(s)
        brazo = _brazo(ctrl, lambda c: rnd.random() < 0.4)
        cumple += ev.selectividad_supervivencia(ctrl, brazo, 200, s)["cumple"]
    # a una cola y al 2,5 %, 40 intentos dan 1 en promedio; 6 seria un instrumento descalibrado
    assert cumple <= 5, "el apagador al azar cumple %d de 40: el criterio no discrimina" % cumple


def test_un_apagador_selectivo_de_negativos_cumple():
    ctrl = _corpus()
    rnd = random.Random(1)
    brazo = _brazo(ctrl, lambda c: c["lab"] == "neg_limpio" and rnd.random() < 0.8)
    r = ev.selectividad_supervivencia(ctrl, brazo, 300, 1)
    assert r["cumple"] and r["observado"] > 0.5


def test_un_apagador_que_mata_las_positivas_no_cumple_aunque_quede_fuera_del_nulo():
    """La razon de la cola unica: el C8 viejo aceptaba CUALQUIER lado."""
    ctrl = _corpus()
    rnd = random.Random(2)
    brazo = _brazo(ctrl, lambda c: c["lab"] == "pos" and rnd.random() < 0.8)
    r = ev.selectividad_supervivencia(ctrl, brazo, 300, 2)
    assert not r["cumple"] and r["observado"] < 0


def test_sin_sustrato_no_cumple_y_lo_dice():
    ctrl = [c for c in _corpus() if c["lab"] == "pos"]
    r = ev.selectividad_supervivencia(ctrl, _brazo(ctrl, lambda c: False), 50, 0)
    assert r["cumple"] is False and r["n_neg"] == 0 and "nota" in r


def _par(**extra):
    p = {"banda_control_tasa_pub_neg": {"VIIRS375": [0.80, 0.92]}, "min_fraccion_cobertura_control": 0.97,
         "min_fraccion_publicacion_identica": 0.98}
    p.update(extra)
    return p


def _records_para_control():
    # todo negativo limpio y nada publicado: tasa 0,0, FUERA de la banda 0,80 a 0,92
    t0 = datetime(2026, 9, 1, 5, 0, tzinfo=timezone.utc)
    base = {"vol": "V0", "b": "VIIRS375", "lab": "neg_limpio", "pub": 0, "disp": 0.0, "dc": "summit",
            "pc_vrp": 0.0, "pc_dist": 1.0, "t1": False, "fuente": "x", "neg_estricto": True, "noche": "2026-09-01",
            "plataforma": "NOAA20"}
    return [dict(base, dt=t0 + timedelta(minutes=7 * i)) for i in range(30)]


def test_la_banda_sigue_decidiendo_por_defecto():
    recs = _records_para_control()
    r = ev.control_positivo_control(recs, recs, _par())
    assert r["banda_control_aplica"] is True and r["cumple"] is False


def test_la_banda_se_apaga_solo_por_parametro_explicito():
    recs = _records_para_control()
    r = ev.control_positivo_control(recs, recs, _par(banda_control_aplica=False))
    assert r["banda_control_aplica"] is False and r["cumple"] is True
    assert r["bandas_tasa_pub_neg"]["VIIRS375"]["dentro"] is False, "la banda se sigue INFORMANDO aunque no decida"


def test_rutina_en_noche_con_alerta_se_etiqueta_sin_cambiar_la_etiqueta():
    t = datetime(2026, 9, 5, 5, 0, tzinfo=timezone.utc)
    fila = {"tipo": "RUTINA", "source": "CONS", "vrp_mw": 0.0, "dist_km": None, "fecha_utc": "2026-09-05 05:00:00"}
    por_vb = {("V0", "VIIRS375"): [(t, fila)]}
    rec = {"vol": "V0", "b": "VIIRS375", "dt": t, "noche": "2026-09-05"}
    limpio = dict(rec)
    bp.etiquetar([rec], por_vb, {("V0", "VIIRS375", "2026-09-05"): {"alerta": True, "fp": False}}, {})
    bp.etiquetar([limpio], por_vb, {}, {})
    assert rec["lab"] == "sin_info" and rec["rutina_pasada"] and rec["noche_con_alerta_sensor"]
    assert limpio["lab"] == "neg_limpio" and limpio["rutina_pasada"] and not limpio["noche_con_alerta_sensor"]


def test_el_estrato_informativo_cuenta_control_y_brazo():
    t0 = datetime(2026, 9, 5, 5, 0, tzinfo=timezone.utc)
    ctrl = [{"vol": "V0", "b": "VIIRS375", "dt": t0 + timedelta(minutes=100 * i), "lab": "sin_info", "pub": 1,
             "rutina_pasada": i < 3, "noche_con_alerta_sensor": True} for i in range(5)]
    brazo = [dict(c, pub=0) for c in ctrl]
    r = ev.rutina_en_noche_con_alerta(ctrl, brazo)
    assert r == {"VIIRS375": {"n": 3, "pub_control": 3, "pub_brazo": 0}}
