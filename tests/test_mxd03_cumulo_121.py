# -*- coding: utf-8 -*-
"""Tarea 1.21 del loop: tests del pre-registro del probe MxD03 + etiqueta desde el cumulo.

POR QUE. La 1.17 dio PIERDE PROTEGIDA por la letra, pero su verificador mostro que las 2 perdidas son
de la etiqueta (A46/A81), no de la posicion, que al modelo de corrimiento le faltaba el termino a lo
largo de la traza, y que el control C' no era un control del efecto. Estos tests fijan, antes de gastar
una corrida:

  1. que el brazo con etiqueta del cumulo cambia el flag EFECTIVO (A89, A118): el nombre que leen los
     dos consumidores en process_modis, no el de pipeline.profile, y que no aparecio otro consumidor;
  2. el modelo de corrimiento con los dos ejes;
  3. el brazo de ruido: determinista, del tamano pedido, y capaz de cambiar una publicacion;
  4. que el evaluador PUEDE dar cada estado (A116), con su control negativo;
  5. que el estimador del balance cubre con respuesta conocida y que el veredicto es alcanzable con la
     poblacion real (prediccion del replay);
  6. el workflow: candado, solo EARTHDATA_TOKEN, "on" entre comillas, grupo propio y timeouts.

Criterio y diseno: experiments/_s151_mxd03_cumulo_121/README.md
"""
import ast
import copy
import hashlib
import json
import math
import os
import re
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "_s151_mxd03_cumulo_121"
EXP117 = ROOT / "experiments" / "_s151_mxd03_etiquetas"
for p in (ROOT, ROOT / "scripts", EXP117, EXP):
    sys.path.insert(0, str(p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import evaluar_cumulo as E  # noqa: E402
import modelo_corrimiento as MC  # noqa: E402

FLAG = "ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER"
NODE = shutil.which("node") is not None
SHA_POBLACION_117 = "89a526cc7745264bb21c198a460dbd37b20536bcc93c8ad5f430392b8369c9e8"   # LF


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ 0. misma poblacion que la 1.17
def test_la_muestra_es_la_de_la_117_sin_tocar():
    b = (EXP117 / "poblacion.json").read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(b).hexdigest() == SHA_POBLACION_117


def test_la_prediccion_reproduce_la_poblacion_de_la_117():
    pred = _json(EXP / "prediccion_cumulo.json")
    for vol, v in pred["volcanes"].items():
        assert v["N_por_estrato_igual_a_poblacion_117"], vol
        assert v["muestra_lab_o_prot_distinta"] == 0, vol
        assert v["muestra_pub_guardada_distinta"] == 0, vol
    assert sum(len(x) for x in pred["poblacion"].values()) == 5395


def test_el_unico_ausente_del_archivo_no_esta_en_el_censo():
    """archivo_cmr.json (CMR, antes de correr): de los 471, solo falta el granulo de Tupungatito que la
    1.17 no pudo bajar, y no es alerta ni protegida. Si esta lista crece, el pre-registro cambio."""
    d = _json(EXP / "archivo_cmr.json")
    assert d["granulos_consultados"] == 471
    assert [(a["volcan"], a["clave"]) for a in d["ausentes"]] == [("Tupungatito", "MOD021KM.A2026275.0225")]
    assert not any(a["censo"] or a["prot"] or a["lab"] == "pos" for a in d["ausentes"])


# ------------------------------------------------------------------ 1. el flag efectivo (A89, A118)
def _arbol(rel):
    return ast.parse((ROOT / rel).read_text(encoding="utf-8"))


def test_process_modis_importa_el_flag_por_valor():
    """Por eso el brazo lo parchea en el modulo process_modis y no en pipeline.profile."""
    imps = [n for n in ast.walk(_arbol("pipeline/process_modis.py"))
            if isinstance(n, ast.ImportFrom) and n.module in ("pipeline.profile", ".profile", "profile")]
    assert any(FLAG in {a.name for a in n.names} for n in imps)


def test_los_consumidores_del_flag_son_las_dos_llamadas_a_derivar():
    llamadas = [n for n in ast.walk(_arbol("pipeline/process_modis.py")) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name) and n.func.id == "derivar_distance_class"]
    assert len(llamadas) == 2
    for c in llamadas:
        assert len(c.args) == 4 and isinstance(c.args[3], ast.Name) and c.args[3].id == FLAG
    usos = [n for n in ast.walk(_arbol("pipeline/process_modis.py")) if isinstance(n, ast.Name) and n.id == FLAG]
    assert len(usos) == 2, "aparecio otro uso del flag en process_modis: el brazo MC puede no llegar a el"


def test_ningun_otro_modulo_lee_el_flag():
    """A118: si aparece otro consumidor (store, otro procesador, el tablero), este probe lo pierde."""
    patron = re.compile(r"distance_class_from_cluster", re.I)
    lectores = []
    for d, globo in (("pipeline", "*.py"), ("scripts", "*.py"), ("frontend", "*.html")):
        for p in sorted((ROOT / d).glob(globo)):
            if patron.search(p.read_text(encoding="utf-8", errors="ignore")):
                lectores.append(p.relative_to(ROOT).as_posix())
    assert lectores == ["pipeline/process_modis.py", "pipeline/profile.py"]


def test_el_flag_de_produccion_sigue_apagado():
    import pipeline.profile as prof
    assert getattr(prof, FLAG) is False


@pytest.mark.skipif(not NODE, reason="el predicado del tablero corre con node")
def test_parchear_pipeline_profile_no_llega_y_parchear_el_modulo_si():
    """La trampa de A89, medida: el mismo cambio en el lugar equivocado no mueve la etiqueta."""
    import pipeline.profile as prof
    import probar_probe_cumulo as T
    import probe_cumulo as Q
    import probe_etiquetas as P
    d = T.escena_a46()
    lector = lambda _p: P._copia(d)  # noqa: E731
    with patch.object(prof, FLAG, True):
        mal = P.procesar_brazo(T.T.L1B, Path("g.hdf"), T.T.VOLCAN, None, None, lector)
    bien, visto, _ = Q.procesar(T.T.L1B, Path("g.hdf"), T.T.VOLCAN, None, None, lector, True)
    assert mal["distance_class"] == "far"
    assert bien["distance_class"] == "summit" and visto == [True]


@pytest.mark.skipif(not NODE, reason="el predicado del tablero corre con node")
def test_prueba_sintetica_completa():
    import probar_probe_cumulo as T
    r = T.correr()
    assert T.fallas_de(r) == []
    e = r["etiqueta"]
    assert e["flag_visto"] == {"C": [False], "CC": [True], "M": [False], "MC": [True], "R": [False], "RC": [True]}
    t = r["test1"]
    assert t["brazos"]["C"]["fuente"] == "test1" and t["pub"]["C"] == 1 and t["pub"]["CC"] == 0
    # el espia guarda los cuatro argumentos y el resultado: CC se etiqueto con el cumulo del Salar
    final, pc, inner, desde, res = t["derivar"]["CC"][-1]
    assert desde is True and res == "far" and pc > 10 and inner == 5
    assert t["cumulo_etiqueta"]["CC"]["distinto"] and t["cumulo_etiqueta"]["CC"]["guardado_km"] < 1


@pytest.mark.skipif(not NODE, reason="el predicado del tablero corre con node")
def test_el_replay_no_ve_la_rama_del_test1():
    """Bloqueante 1 del verificador, medido: sobre el record de produccion de la escena TEST1, el replay
    dice que CC publica, y el brazo CC medido no publica. Por eso en fuente test1 la prediccion es cota."""
    import predecir_etiqueta_cumulo as PR
    import probar_probe_cumulo as T
    import probe_cumulo as Q
    import probe_etiquetas as P
    d = T.escena_test1()
    rec_c, _, _ = Q.procesar(T.T.L1B, Path("g.hdf"), T.T.VOLCAN, None, None, lambda _p: P._copia(d), False)
    rec_cc, _, _ = Q.procesar(T.T.L1B, Path("g.hdf"), T.T.VOLCAN, None, None, lambda _p: P._copia(d), True)
    assert rec_c["final_hotspot_source"] == "test1"
    assert P.publica([PR.replay_cumulo(rec_c, 5.0), rec_cc], 5.0) == [1, 0]


@pytest.mark.skipif(not NODE, reason="el predicado del tablero corre con node")
def test_la_prueba_sintetica_falla_si_se_ignora_la_rama_del_test1():
    """Mutacion: un instrumento que publicara CC en la escena TEST1 (lo que dice el replay) es atrapado."""
    import probar_probe_cumulo as T
    r = T.correr()
    r["test1"]["pub"]["CC"] = 1
    assert any(f.startswith("TEST1") for f in T.fallas_de(r))
    r = T.correr()
    r["test1"]["cumulo_etiqueta"]["CC"]["distinto"] = False
    assert any(f.startswith("TEST1") for f in T.fallas_de(r))


def test_la_prediccion_declara_la_fuente_test1_como_cota():
    t = _json(EXP / "prediccion_cumulo.json")["total"]
    assert sum(v for k, v in t.items() if k.startswith("fuente_test1|") and k.endswith("|n")) == 126
    assert t["fuente_test1|protegida|n"] == 4 and t["fuente_test1|protegida|pub_C"] == 4
    assert "COTA SUPERIOR" in (EXP / "predecir_etiqueta_cumulo.py").read_text(encoding="utf-8")


@pytest.mark.skipif(not NODE, reason="el predicado del tablero corre con node")
def test_si_el_brazo_mc_no_cambia_el_flag_la_prueba_falla():
    """Mutacion: un probe cuyo brazo MC corre con la etiqueta de produccion tiene que ser atrapado."""
    import probar_probe_cumulo as T
    import probe_cumulo as Q
    with patch.dict(Q.CUMULO, {"MC": False}):
        r = T.correr()
    with patch.dict(Q.CUMULO, {"MC": False}):
        fallas = T.fallas_de(r)
    assert any("ETIQUETA" in f for f in fallas)


# ------------------------------------------------------------------ 2. modelo de corrimiento
def test_termino_a_lo_largo_de_la_traza():
    assert MC.lineas_a_lo_largo(0) == pytest.approx(2.0)
    assert MC.lineas_a_lo_largo(386) == pytest.approx(1.239, abs=0.002)     # 2026-04-30, medido 1,213
    assert MC.lineas_a_lo_largo(1136) == pytest.approx(-0.239, abs=0.002)   # 2026-04-20, medido -0,275
    assert MC.lineas_a_lo_largo(2029) == pytest.approx(-2.0, abs=0.002)
    assert MC.km_por_linea(0.0) == pytest.approx(1.0, abs=1e-3)
    assert MC.km_por_linea(60.0) > MC.km_por_linea(30.0) > 1.0


def test_el_modelo_nuevo_suma_los_dos_ejes_y_el_peor_caso_acota():
    z, az, sen = 10.0, 80.0, "MODIS_TERRA"
    a = MC.S.corrimiento_predicho(z, az, sen)
    assert MC.corrimiento_predicho_traza(z, az, sen, 1015) == pytest.approx(a, abs=0.01)   # medio granulo
    assert MC.corrimiento_predicho_traza(z, az, sen, 0) == pytest.approx(math.hypot(a, 2 * MC.km_por_linea(z)))
    assert MC.corrimiento_predicho_traza(z, az, sen, None) >= MC.corrimiento_predicho_traza(z, az, sen, 386)
    assert MC.corrimiento_predicho_traza(None, az, sen) is None


def test_la_validacion_contra_la_117_quedo_escrita():
    """validar_modelo_117_salida.txt sale de los artefactos del run 38894508138: bajo 20 grados el modelo
    nuevo predice el 1,1 a 1,3 km medido, y casi ningun granulo excede la banda (eran 87 de 470)."""
    filas = [json.loads(x) for x in (EXP / "validar_modelo_117_salida.txt").read_text(encoding="utf-8").splitlines()
             if x.startswith("{")]
    b = {f["cenit"]: f for f in filas}
    assert 1.1 <= b["0-20"]["medido_mediana"] <= 1.3
    assert abs(b["0-20"]["nuevo_mediana"] - b["0-20"]["medido_mediana"]) < 0.15
    assert b["0-90"]["exceden_viejo_mas_1"] == 87 and b["0-90"]["exceden_nuevo_mas_1"] <= 5


# ------------------------------------------------------------------ 3. el ruido
def test_angulo_de_ruido_determinista_y_parejo():
    import probe_cumulo as Q
    assert Q.angulo_ruido("MOD021KM.A2026110.0130") == Q.angulo_ruido("MOD021KM.A2026110.0130")
    angs = [Q.angulo_ruido("X%05d" % i) for i in range(4000)]
    cuad = np.histogram(angs, bins=4, range=(0, 360))[0]
    assert cuad.min() > 900 and abs(np.mean(np.cos(np.radians(angs)))) < 0.05


def test_trasladar_aplica_el_tamano_pedido():
    import probe_cumulo as Q
    import probe_etiquetas as P
    k = 40
    lats = -23.36 + (k - np.arange(81)) / 111.32
    lons = -67.73 + (np.arange(81) - k) / (111.32 * np.cos(np.radians(-23.36)))
    lat, lon = np.meshgrid(lats, lons, indexing="ij")
    for km, ang in ((1.3, 0.0), (2.7, 135.0), (4.0, 290.0)):
        la, lo = Q.trasladar(lat, lon, km, ang)
        assert P.desplazamiento_crater(la, lo, lat, lon, (-23.36, -67.73))["km"] == pytest.approx(km, abs=0.01)
    la, lo = Q.trasladar(lat, lon, 0.0, 77.0)
    assert np.allclose(la, lat, atol=1e-6) and np.allclose(lo, lon, atol=1e-6)


@pytest.mark.skipif(not NODE, reason="el predicado del tablero corre con node")
def test_el_ruido_puede_cambiar_la_publicacion():
    """Control positivo del brazo R: con 2 km hacia el norte el foco pasa de 4 a 6 km (inner 5) y se
    apaga; hacia el sur no. Sin esto, un R que nunca cambia nada pareceria un nulo limpio."""
    import probar_probe_cumulo as T
    import probe_cumulo as Q
    with patch.object(Q, "angulo_ruido", lambda c: 0.0):
        norte = T._caso(T.T.escena(), T.T.CORRIMIENTO_KM)
    with patch.object(Q, "angulo_ruido", lambda c: 180.0):
        sur = T._caso(T.T.escena(), T.T.CORRIMIENTO_KM)
    assert norte["pub"]["C"] == 1 and norte["pub"]["R"] == 0 and norte["pub"]["RC"] == 0
    assert sur["pub"]["R"] == 1


# ------------------------------------------------------------------ 4. evaluador: cada estado
def _fila(clave, estrato="A", lab="neg_limpio", prot=False, censo=False):
    return {"clave": clave, "estrato": estrato, "lab": lab, "prot": prot, "censo": censo,
            "datetime_utc": "2026-04-20 01:30", "sensor": "MODIS_TERRA", "sensor_zenith_deg": 10.0,
            "sensor_azimuth_deg": 80.0, "vrp_ref": 1.3 if prot else None}


def _medida(clave, pub=None, dc=None, cprima=None, ruido=(0.5, 0.5), visto=None):
    pub = dict({b: 0 for b in E.BRAZOS}, **(pub or {}))
    dc = dict({b: "far" for b in E.BRAZOS}, **(dc or {}))
    visto = visto or {b: [E.CUMULO[b]] for b in E.BRAZOS}
    return {"clave": clave, "estado": "ok", "pub": pub, "cprima_igual": cprima, "flag_visto": visto,
            "brazos": {b: {"dc": dc[b], "fuente": "eruption", "final_lat": -23.3, "final_lon": -67.7,
                           "pc_lat": -23.37, "pc_lon": -67.73, "pc_vrp": 0.3} for b in E.BRAZOS},
            "ruido": {"km_objetivo": ruido[0], "angulo_grados": 10.0, "km_aplicado": ruido[1]},
            "desplazamiento": {"km": 0.5, "linea": 1000, "frame": 600, "dn_km": 0.5, "de_km": 0.0}}


def _caso(filas_por_vol, medidas_por_vol):
    pob = {"volcanes": {}, "jobs": {}}
    sal = {}
    for vol, filas in filas_por_vol.items():
        n = {}
        for f in filas:
            n.setdefault(f["estrato"], {}).setdefault(f["lab"], 0)
            n[f["estrato"]][f["lab"]] += 1
        pob["volcanes"][vol] = {"N": n, "muestra": filas, "inner_radius_km": 5.0}
        pob["jobs"][vol] = {"volcan": vol, "granulos": [f["clave"] for f in filas]}
        if vol in medidas_por_vol:
            sal[vol] = {"job": vol, "volcan": vol, "completo": True, "brazos": list(E.BRAZOS),
                        "granulos": medidas_por_vol[vol]}
    return pob, sal


def _limpio(vol="a", n=10):
    filas = [_fila("%s%d" % (vol, i)) for i in range(n)]
    meds = [_medida(f["clave"], cprima=(True if i == 0 else None)) for i, f in enumerate(filas)]
    return filas, meds


def test_estado_sin_cambio_observado():
    f, m = _limpio()
    r = E.evaluar(*_caso({"a": f}, {"a": m}))
    assert r["veredicto"] == "SIN CAMBIO OBSERVADO" and r["adoptable_en_la_replica"] is False


def test_estado_invalido_por_c_prima():
    f, m = _limpio()
    m[0]["cprima_igual"] = False
    assert E.evaluar(*_caso({"a": f}, {"a": m}))["veredicto"] == "INVALIDO"


def test_estado_invalido_si_el_brazo_mc_no_vio_el_flag():
    f, m = _limpio()
    m[3]["flag_visto"]["MC"] = [False]
    r = E.evaluar(*_caso({"a": f}, {"a": m}))
    assert r["veredicto"] == "INVALIDO" and any("MC" in x for x in r["motivos_invalido"])


def test_estado_invalido_si_un_brazo_de_produccion_vio_el_flag_encendido():
    f, m = _limpio()
    m[2]["flag_visto"]["C"] = [True]
    assert E.evaluar(*_caso({"a": f}, {"a": m}))["veredicto"] == "INVALIDO"


def test_estado_invalido_si_el_ruido_no_es_el_pedido():
    f, m = _limpio()
    m[4]["ruido"]["km_aplicado"] = 0.3
    assert E.evaluar(*_caso({"a": f}, {"a": m}))["veredicto"] == "INVALIDO"


def test_estado_incompleto_por_job_faltante():
    fa, ma = _limpio("a")
    fb, _ = _limpio("b")
    assert E.evaluar(*_caso({"a": fa, "b": fb}, {"a": ma}))["veredicto"] == "INCOMPLETO"


def test_estado_incompleto_por_un_solo_granulo_faltante_y_el_ausente_del_archivo_no_cuenta():
    f, m = _limpio()
    m[5] = {"clave": m[5]["clave"], "estado": "error", "error": "timeout"}
    pob, sal = _caso({"a": f}, {"a": m})
    assert E.evaluar(pob, sal)["veredicto"] == "INCOMPLETO"
    aus = [{"volcan": "a", "clave": m[5]["clave"], "prot": False, "lab": "neg_limpio"}]
    assert E.evaluar(pob, sal, ausentes=aus)["veredicto"] == "SIN CAMBIO OBSERVADO"


def test_estado_incompleto_si_un_brazo_falta_en_un_granulo():
    f, m = _limpio()
    del m[6]["pub"]["RC"]
    r = E.evaluar(*_caso({"a": f}, {"a": m}))
    assert r["veredicto"] == "INCOMPLETO" and r["conteo_por_brazo"]["RC"]["granulos"] == 9


def test_estado_incompleto_sin_ningun_c_prima():
    f, m = _limpio()
    m[0]["cprima_igual"] = None
    assert E.evaluar(*_caso({"a": f}, {"a": m}))["veredicto"] == "INCOMPLETO"


def test_estado_pierde_protegida_y_su_control_negativo():
    f, m = _limpio()
    f.append(_fila("p1", estrato="control", lab="pos", prot=True, censo=True))
    m.append(_medida("p1", pub={"C": 1, "MC": 0, "CC": 1, "M": 1, "R": 1, "RC": 1}))
    r = E.evaluar(*_caso({"a": f}, {"a": m}))
    assert r["veredicto"] == "PIERDE PROTEGIDA"
    assert r["comparaciones"]["principal"]["regla1"]["perdidas"] == 1
    assert r["comparaciones"]["principal"]["fragil"] is False      # el ruido no la pierde
    m[-1]["pub"]["MC"] = 1
    assert E.evaluar(*_caso({"a": f}, {"a": m}))["veredicto"] == "SIN CAMBIO OBSERVADO"


def test_fragil_cuando_el_ruido_tambien_pierde_la_misma_pasada():
    f, m = _limpio()
    f.append(_fila("p1", estrato="control", lab="pos", prot=True, censo=True))
    m.append(_medida("p1", pub={"C": 1, "MC": 0, "CC": 1, "M": 1, "R": 1, "RC": 0}))
    r = E.evaluar(*_caso({"a": f}, {"a": m}))
    c = r["comparaciones"]["principal"]
    assert r["veredicto"] == "PIERDE PROTEGIDA" and c["fragil"] is True and c["fragil_pasadas"] == ["a|p1"]


def test_no_es_fragil_si_el_ruido_pierde_otra_pasada():
    """Control negativo del bloqueante 2: el nulo pierde una protegida distinta de la que pierde MC."""
    f, m = _limpio()
    f.append(_fila("p1", estrato="control", lab="pos", prot=True, censo=True))
    f.append(_fila("p2", estrato="control", lab="pos", prot=True, censo=True))
    m.append(_medida("p1", pub={"C": 1, "MC": 0, "CC": 1, "M": 1, "R": 1, "RC": 1}))
    m.append(_medida("p2", pub={"C": 1, "MC": 1, "CC": 1, "M": 1, "R": 1, "RC": 0}))
    r = E.evaluar(*_caso({"a": f}, {"a": m}))
    c = r["comparaciones"]["principal"]
    assert r["veredicto"] == "PIERDE PROTEGIDA" and c["fragil"] is False
    assert c["perdidas_que_el_nulo_no_pierde"] == ["a|p1"]
    assert r["comparaciones"]["nulo_de_principal"]["regla1"]["perdidas"] == 1


def test_prueba_del_replay_por_grupo():
    f, m = _limpio()
    pred = {"total": {"delta": 1}, "granulos": {}}
    for i, x in enumerate(f):
        pred["granulos"]["a|%s" % x["clave"]] = {"pub_cc_replay": 0, "pub_c_guardada": 0,
                                                  "fuente": "test1" if i < 3 else "eruption"}
    for x in m[:3]:
        x["pub"]["CC"] = 1          # la rama del Test 1: el medido no es el replay
    r = E.evaluar(*_caso({"a": f}, {"a": m}), prediccion=pred)["prueba_del_replay"]
    assert r["fuente_test1"] == {"acuerdo": 0, "de": 3, "CC_medido_1_replay_0": 3, "CC_medido_0_replay_1": 0}
    assert r["resto"]["acuerdo"] == 7 and r["creible_fuera_de_test1"] is True


def test_deriva_de_c_sobre_las_protegidas():
    f, m = _limpio()
    f.append(dict(_fila("p1", estrato="control", lab="pos", prot=True, censo=True), pub_guardada=1))
    m.append(_medida("p1", pub={b: 0 for b in E.BRAZOS}))
    r = E.evaluar(*_caso({"a": f}, {"a": m}))
    assert r["deriva_protegidas"]["distintas"][0]["clave"] == "p1"


def _muchos(n_cambian, cambio, n=40):
    filas = [_fila("n%d" % i) for i in range(n)]
    meds = []
    for i, f in enumerate(filas):
        pub = {b: 1 if cambio == "apaga" else 0 for b in E.BRAZOS}
        if i < n_cambian:
            pub.update({"MC": 0 if cambio == "apaga" else 1})
        meds.append(_medida(f["clave"], pub=pub, cprima=(True if i == 0 else None)))
    pob, sal = _caso({"a": filas}, {"a": meds})
    pob["volcanes"]["a"]["N"]["A"]["neg_limpio"] = 400     # 40 medidos de 400: se expande
    return pob, sal


def test_estado_mejora_y_adoptable():
    r = E.evaluar(*_muchos(30, "apaga"))
    assert r["veredicto"] == "MEJORA" and r["adoptable_en_la_replica"] is True


def test_estado_empeora():
    assert E.evaluar(*_muchos(30, "enciende"))["veredicto"] == "EMPEORA"


def test_estado_indeterminado():
    assert E.evaluar(*_muchos(1, "enciende"))["veredicto"] == "INDETERMINADO"


def test_las_alertas_bajo_1_mw_entran_exactas():
    f, m = _limpio(n=5)
    for i in range(6):
        f.append(_fila("al%d" % i, lab="pos", censo=True))
        m.append(_medida("al%d" % i, pub={"C": 1}))
    r = E.evaluar(*_caso({"a": f}, {"a": m}))
    c = r["comparaciones"]["principal"]["regla2"]
    assert c["alertas_perdidas"] == 6 and c["intervalo"] == [6.0, 6.0] and r["veredicto"] == "EMPEORA"


def test_tramo_a119_de_modis():
    assert E.tramo_a119("2026-04-20 01:30") == "desde 2026-03-01"
    assert E.tramo_a119("2026-10-11 01:30") == "desde 2026-10-10"


# ------------------------------------------------------------------ 5. estimador con la poblacion real
def _sintetico_real(fn_pub):
    """Salidas con TODA la muestra real medida, publicacion por brazo segun fn_pub(vol, clave, brazo)."""
    pob = _json(EXP117 / "poblacion.json")
    sal = {}
    for j, x in pob["jobs"].items():
        meds = []
        for i, c in enumerate(x["granulos"]):
            m = _medida(c, cprima=(True if i == 0 else None))
            m["pub"] = {b: fn_pub(x["volcan"], c, b) for b in E.BRAZOS}
            meds.append(m)
        sal[j] = {"job": j, "volcan": x["volcan"], "completo": True, "brazos": list(E.BRAZOS), "granulos": meds}
    return pob, sal


ANCHO_NULO_MAX = 800.0   # medido en la v1: 790 (ancho total hi - lo bajo el nulo con poblacion.json)


def test_nulo_real_tiene_ancho_acotado():
    pob, sal = _sintetico_real(lambda v, c, b: 0)
    r = E.evaluar(pob, sal)
    lo, hi = r["comparaciones"]["principal"]["regla2"]["intervalo"]
    assert r["veredicto"] == "SIN CAMBIO OBSERVADO"
    assert 0 < hi - lo <= ANCHO_NULO_MAX


def test_con_la_prediccion_del_replay_el_veredicto_es_alcanzable():
    """Si el probe mide lo que predice el replay, la principal y la etiqueta salen EMPEORA (no
    INDETERMINADO) y la regla 1 no pierde ninguna protegida."""
    pred = _json(EXP / "prediccion_cumulo.json")["granulos"]

    def pub(v, c, b):
        p = pred["%s|%s" % (v, c)]
        return p["pub_cc_replay"] if E.CUMULO[b] else p["pub_c_guardada"]
    pob, sal = _sintetico_real(pub)
    r = E.evaluar(pob, sal)
    assert r["veredicto"] == "EMPEORA"
    assert r["comparaciones"]["etiqueta"]["veredicto"] == "EMPEORA"
    assert r["comparaciones"]["principal"]["regla1"]["perdidas"] == 0
    assert r["comparaciones"]["posicion_produccion"]["veredicto"] == "SIN CAMBIO OBSERVADO"


def test_mejora_alcanzable_con_la_poblacion_real():
    """Apagar en MC todas las publicaciones guardadas en negativos limpios tiene que poder dar MEJORA."""
    pob = _json(EXP117 / "poblacion.json")
    labs = {(v, g["clave"]): g for v, d in pob["volcanes"].items() for g in d["muestra"]}

    def pub(v, c, b):
        g = labs[(v, c)]
        base = g["pub_guardada"]
        return 0 if (b in ("MC",) and g["lab"] == "neg_limpio") else base
    r = E.evaluar(*_sintetico_real(pub))
    assert r["veredicto"] == "MEJORA", r["comparaciones"]["principal"]["regla2"]


def test_control_del_estimador_con_respuesta_conocida():
    """El total por censo del replay (3.867 negativos limpios que se encienden) cae dentro del
    intervalo que el estimador da con la muestra de 471."""
    total, res = E.control_estimador(_json(EXP117 / "poblacion.json"), _json(EXP / "prediccion_cumulo.json"))
    assert total == 3867
    assert res["intervalo"][0] <= total <= res["intervalo"][1]
    assert res["intervalo"][0] > 0


def test_la_cobertura_medida_quedo_escrita():
    """cobertura_estimador_salida.txt: el intervalo principal cubre al menos 95 % en los cinco escenarios
    y decide el signo del efecto grande; el de Dirichlet que se descarto no cubre el efecto grande."""
    lineas = (EXP / "cobertura_estimador_salida.txt").read_text(encoding="utf-8").splitlines()
    cob = {}
    for x in lineas:
        m = re.match(r"(\w+)\s+verdad\s+(-?\d+) \| (.+?)\s+cobertura ([\d.]+) \| ancho mediano\s+([\d.]+) \| "
                     r"decide el signo ([\d.]+)", x)
        if m:
            cob[(m.group(1), m.group(3).split(" ")[0])] = (float(m.group(4)), float(m.group(6)))
    for esc in ("replay", "nulo", "raro", "A_solo", "mezcla", "apaga_50", "apaga_70", "apaga_90",
                "enciende_5", "enciende_10"):
        assert cob[(esc, "principal")][0] >= 0.95, esc
    # poder (verificador del pre-registro): MEJORA exige apagar la mayoria de las falsas alarmas de C
    assert cob[("apaga_50", "principal")][1] < 0.2 and cob[("apaga_90", "principal")][1] > 0.6
    assert cob[("replay", "principal")][1] == 1.0 and cob[("mezcla", "principal")][1] == 1.0
    assert cob[("replay", "dirichlet_1/2")][0] < 0.5


# ------------------------------------------------------------------ 6. el workflow
WF = ROOT / ".github" / "workflows" / "probe-s151-mxd03-cumulo-121.yml"


def test_workflow_con_candado_token_y_grupo_propio():
    import yaml
    txt = WF.read_text(encoding="utf-8")
    d = yaml.safe_load(txt)
    assert "on" in d and True not in d, "'on' tiene que ir entre comillas (A43)"
    assert d["on"]["workflow_dispatch"]["inputs"]["preregistro_aprobado"]["default"] == "no"
    assert 'preregistro_aprobado }}" != "si"' in txt
    assert "EARTHDATA_USERNAME" not in txt and "EARTHDATA_PASSWORD" not in txt
    assert "secrets.EARTHDATA_TOKEN" in txt
    grupo = d["concurrency"]["group"]
    assert grupo not in ("s146-ab-sin-test1", "s151-ab-diurno", "push-main", "probe-s151-mxd03-etiquetas")
    assert d["concurrency"]["cancel-in-progress"] is False
    assert "git push" not in txt


def test_workflow_timeouts_con_margen_sobre_el_presupuesto():
    import yaml
    d = yaml.safe_load(WF.read_text(encoding="utf-8"))
    probe = d["jobs"]["probe"]
    # ojo A92: "probe_cumulo.py" es subcadena de "probar_probe_cumulo.py"; se busca el paso por su bandera
    paso = next(s for s in probe["steps"] if "--presupuesto-min" in s.get("run", ""))
    assert "_s151_mxd03_cumulo_121/probe_cumulo.py --job" in paso["run"]
    presupuesto = float(re.search(r"--presupuesto-min (\d+)", paso["run"]).group(1))
    assert probe["timeout-minutes"] >= 1.25 * presupuesto        # A15
    for s in probe["steps"]:
        for ruta in re.findall(r"experiments/\S+?\.py", s.get("run", "")):
            assert (ROOT / ruta).exists(), ruta
