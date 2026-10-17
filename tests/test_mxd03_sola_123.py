# -*- coding: utf-8 -*-
"""Tarea 1.23 del loop: tests del pre-registro del probe MxD03 sola (nulo en pixeles y vara VIIRS).

POR QUE. La 1.21 dejo a MxD03 sola ni refutada ni probada: sus 2 perdidas protegidas son la etiqueta
fragil de Lascar (A46) y su nulo, con un solo rumbo por granulo y del tamano en km, perdia 4 y era
anisotropo sobre 50 grados de cenit. Estos tests fijan, antes de gastar una corrida:

  1. que la muestra es la de la 1.17 y que los 24 medios jobs la cubren exacta;
  2. que el nulo tiene el tamano del corrimiento real EN PIXELES (no en km), con rumbos equiespaciados,
     deterministas y parejos, y que eso cambia algo frente al nulo de la 1.21 (control negativo);
  3. que la vara VIIRS quedo congelada con la referencia de la 1.17 y sin cumulos del Test 1;
  4. que el probe sintetico pasa por el pipeline real y que una mutacion lo hace fallar;
  5. que el evaluador PUEDE dar cada estado, con su control (A110, A116);
  6. el workflow: candado, solo EARTHDATA_TOKEN, "on" entre comillas, grupo propio y timeouts.

Criterio y diseno: experiments/_s151_mxd03_sola_123/README.md
"""
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
EXP = ROOT / "experiments" / "_s151_mxd03_sola_123"
EXP117 = ROOT / "experiments" / "_s151_mxd03_etiquetas"
EXP121 = ROOT / "experiments" / "_s151_mxd03_cumulo_121"
for p in (ROOT, ROOT / "scripts", EXP117, EXP121, EXP):
    sys.path.insert(0, str(p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import evaluar_sola as ES  # noqa: E402
import jobs_123 as J  # noqa: E402

NODE = shutil.which("node") is not None
SHA_POBLACION_117 = "89a526cc7745264bb21c198a460dbd37b20536bcc93c8ad5f430392b8369c9e8"   # LF


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ 1. la muestra y los medios jobs
def test_la_muestra_es_la_de_la_117_sin_tocar():
    b = (EXP117 / "poblacion.json").read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(b).hexdigest() == SHA_POBLACION_117


def test_los_medios_jobs_cubren_la_muestra_exacta():
    pob = J.cargar()
    partes = J.partir(pob)
    assert len(partes) == 24 and max(len(x["granulos"]) for x in partes.values()) <= 24
    for j, x in pob["jobs"].items():
        a, b = partes[j + "a"]["granulos"], partes[j + "b"]["granulos"]
        assert sorted(a + b) == sorted(x["granulos"]) and not set(a) & set(b)
        assert partes[j + "a"]["volcan"] == x["volcan"] == partes[j + "b"]["volcan"]


# ------------------------------------------------------------------ 2. el nulo en pixeles
def test_rumbos_deterministas_equiespaciados_y_parejos():
    import probe_sola as S
    assert S.rumbos("MOD021KM.A2026110.0130") == S.rumbos("MOD021KM.A2026110.0130")
    r = S.rumbos("MOD021KM.A2026110.0130")
    d = sorted((x - r[0]) % 360 for x in r)
    assert all(abs(b - a - 18.0) < 1e-6 for a, b in zip(d[:-1], d[1:]))
    # cada rumbo por si solo es uniforme: 4.000 claves, 10 sectores de 36 grados
    for k in (0, 7):
        cuenta = [0] * 10
        for i in range(4000):
            cuenta[int(S.rumbos("clave%d" % i)[k] // 36) % 10] += 1
        assert all(330 <= c <= 470 for c in cuenta), cuenta


def _grilla(paso_lin_km=1.0, paso_frame_km=1.0, n=41, lat0=-23.37, lon0=-67.73):
    k = n // 2
    lats = lat0 + paso_lin_km * (k - np.arange(n)) / 111.32
    lons = lon0 + paso_frame_km * (np.arange(n) - k) / (111.32 * np.cos(np.radians(lat0)))
    return np.meshgrid(lats, lons, indexing="ij")


def test_jacobiano_y_pixeles_en_una_grilla_anisotropa():
    import probe_sola as S
    lat, lon = _grilla(1.0, 2.0)
    jac = S.jacobiano(lat, lon, 20, 20)
    assert np.allclose(np.abs(jac), [[1.0, 0.0], [0.0, 2.0]], atol=1e-3)
    pl, pf = S.a_pixeles(jac, 0.0, 2.0)          # 2 km al este = 1 frame
    assert abs(pl) < 1e-6 and abs(abs(pf) - 1.0) < 1e-6
    kms = [math.hypot(*S.vector_nulo(jac, 1.0, a)) for a in S.rumbos("x")]
    assert 0.99 <= min(kms) and max(kms) <= 2.01 and max(kms) - min(kms) > 0.8


def test_el_nulo_de_la_121_no_tenia_el_tamano_en_pixeles():
    """Control negativo de la correccion: el nulo de la 1.21 (mismo tamano en km, rumbo al azar) movia la
    grilla anisotropa entre 1 y 2 pixeles; el de la 1.23, siempre 1."""
    import probe_sola as S
    lat, lon = _grilla(1.0, 2.0)
    jac = S.jacobiano(lat, lon, 20, 20)
    px_121 = [math.hypot(*S.a_pixeles(jac, 2.0 * math.cos(math.radians(a)), 2.0 * math.sin(math.radians(a))))
              for a in range(0, 360, 18)]
    px_123 = [math.hypot(*S.a_pixeles(jac, *S.vector_nulo(jac, 1.0, a))) for a in S.rumbos("x")]
    assert max(px_121) - min(px_121) > 0.9
    assert max(px_123) - min(px_123) < 1e-6


def test_trasladar_ne_aplica_el_vector_pedido():
    import probe_sola as S
    import probe_etiquetas as P
    lat, lon = _grilla(1.0, 1.0)
    vent = (float(lat[20, 20]), float(lon[20, 20]))
    lat2, lon2 = S.trasladar_ne(lat.astype(np.float32), lon.astype(np.float32), 0.7, -1.1)
    ap = P.desplazamiento_crater(lat2, lon2, lat, lon, vent)
    assert abs(ap["dn_km"] - 0.7) < 0.005 and abs(ap["de_km"] + 1.1) < 0.005


# ------------------------------------------------------------------ 3. la vara congelada
def test_la_vara_usa_la_referencia_de_la_117_y_ningun_cumulo_del_test1():
    v = _json(EXP / "vara_viirs.json")
    pob = J.cargar()
    assert v["meta"]["referencia"] == pob["meta"]["referencia"]
    assert v["meta"]["excluye_fuente"] == "test1*" and v["meta"]["ventana_h"] == 6.0
    assert len(v["granulos"]) == 471
    for g in v["granulos"].values():
        est = {(p["datetime_utc"], p["sensor"]) for p in g["estricta"]["pasadas"]}
        amp = {(p["datetime_utc"], p["sensor"]) for p in g["amplia"]["pasadas"]}
        assert est <= amp
        for p in g["amplia"]["pasadas"]:
            assert not str(p.get("fuente") or "").startswith("test1")
            assert p["sensor"] in ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21")
        for p in g["estricta"]["pasadas"]:
            assert p["lab"] == "pos"


def test_el_conjunto_principal_de_la_vara_es_el_declarado():
    """README, «Poder»: 76 granulos MODIS con alerta de MIROVA y vara estricta (70 de Lascar, 6 de Nevados
    de Chillan; 30 Terra, 46 Aqua). Si cambia, el pre-registro cambio."""
    v = _json(EXP / "vara_viirs.json")
    pob = J.cargar()
    sel = [(vol, g) for vol, x in pob["volcanes"].items() for g in x["muestra"]
           if g["lab"] == "pos" and v["granulos"]["%s|%s" % (vol, g["clave"])]["estricta"]["noche"]]
    assert len(sel) == 76
    assert sum(vol == "Lascar" for vol, _ in sel) == 70
    assert sum(g["sensor"] == "MODIS_TERRA" for _, g in sel) == 30


# ------------------------------------------------------------------ 4. el probe sintetico
@pytest.mark.skipif(not NODE, reason="necesita node para el predicado del tablero")
def test_prueba_sintetica_completa():
    import probar_probe_sola as T
    assert T.fallas_de(T.correr()) == []


@pytest.mark.skipif(not NODE, reason="necesita node para el predicado del tablero")
def test_si_el_nulo_fuera_isotropo_en_km_la_prueba_falla():
    """Mutacion (A116): con el nulo de la 1.21 (tamano en km, sin jacobiano) el caso ANISO tiene que fallar."""
    import probar_probe_sola as T
    import probe_sola as S

    def en_km(jac, modulo_px, angulo):
        km = math.hypot(*(jac @ np.array([modulo_px, 0.0])))   # el tamano real en km
        a = math.radians(angulo)
        return km * math.cos(a), km * math.sin(a)
    with patch.object(S, "vector_nulo", en_km):
        fallas = T.fallas_de({"aniso": T._caso(T.escena_aniso(), de_km=-2.0), "posicion": T.correr()["posicion"],
                              "test1": T._caso(T.T21.escena_test1(), dn_km=-1.2), "ausente": T._caso(T.T.escena())})
    assert any("ANISO" in f or "px contra" in f for f in fallas), fallas


# ------------------------------------------------------------------ 5. el evaluador: cada estado
def test_p_de_monte_carlo():
    assert ES.p_rango(2, [0] * 20, "alta") == round(1 / 21, 4)
    assert ES.p_rango(2, [5] * 20, "alta") == 1.0
    assert ES.p_rango(0, [1] * 20, "baja") == round(1 / 21, 4)


def _fila(clave, lab="neg_limpio", prot=False, sensor="MODIS_TERRA", fecha="2026-04-20 01:30", cenit=10.0):
    return {"clave": clave, "estrato": "A", "lab": lab, "prot": prot, "censo": lab == "pos",
            "datetime_utc": fecha, "sensor": sensor, "sensor_zenith_deg": cenit, "sensor_azimuth_deg": 80.0,
            "vrp_ref": 1.3 if prot else None}


def _medida(clave, pub=None, modulo=1.0, cprima=None, test1=None, pc=None, pico=None):
    pub = dict({b: 0 for b in ES.BRAZOS}, **(pub or {}))
    t1 = test1 or {}
    pc = pc or {}
    nulos = [{"k": k, "angulo_grados": (5.0 + 18.0 * k) % 360, "dn_km": 0.0, "de_km": modulo, "km": modulo,
              "km_aplicado": modulo, "px_aplicado": modulo} for k in range(ES.K_NULOS)]
    brazos = {}
    for b in ES.BRAZOS:
        lat, lon = pc.get(b, (-23.37, -67.73))
        brazos[b] = {"dc": "summit" if pub[b] else "far", "fuente": "eruption", "final_lat": lat, "final_lon": lon,
                     "pc_lat": lat, "pc_lon": lon, "pc_vrp": 0.3, "test1_llamadas": 1,
                     "test1": t1.get(b, {"triggered": False, "caliente_en_anillo": False})}
    return {"clave": clave, "estado": "ok", "pub": pub, "cprima_igual": cprima, "brazos": brazos, "nulos": nulos,
            "corrimiento_px": {"linea": 0.0, "frame": modulo, "modulo": modulo},
            "desplazamiento": {"km": modulo, "linea": 1000, "frame": 600, "dn_km": 0.0, "de_km": modulo},
            "pico": pico}


def _caso(filas, medidas, commit="abc123"):
    """Una poblacion de un volcan con un solo job de la 1.17, partido en sus dos mitades."""
    n = {}
    for f in filas:
        n.setdefault(f["estrato"], {}).setdefault(f["lab"], 0)
        n[f["estrato"]][f["lab"]] += 1
    pob = {"volcanes": {"a": {"N": n, "muestra": filas, "inner_radius_km": 5.0}},
           "jobs": {"a": {"volcan": "a", "granulos": [f["clave"] for f in filas]}}}
    por = {m["clave"]: m for m in medidas}
    sal = {}
    for j, x in J.partir(pob).items():
        sal[j] = {"job": j, "volcan": "a", "completo": True, "commit": commit, "k_nulos": ES.K_NULOS,
                  "brazos": list(ES.BRAZOS), "flag_ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER": False,
                  "granulos": [por[c] for c in x["granulos"] if c in por]}
        sal[j]["granulos"][0]["cprima_igual"] = True if sal[j]["granulos"] else None
    return pob, sal


def _limpio(n=10):
    filas = [_fila("g%d" % i) for i in range(n)]
    return filas, [_medida(f["clave"]) for f in filas]


def test_estado_medido_y_no_adoptable_sin_mejora():
    r = ES.evaluar(*_caso(*_limpio()))
    assert r["veredicto"] == "MEDIDO" and r["adoptable_en_la_replica"] is False
    assert r["regla1"]["letra"] == "NO PIERDE"


@pytest.mark.parametrize("mutar,motivo", [
    (lambda m: m.update(cprima_igual=False), "C'"),
    (lambda m: m["nulos"][3].update(px_aplicado=1.5), "px"),
    (lambda m: m["nulos"][3].update(km_aplicado=0.9), "km"),
    (lambda m: m["nulos"][3].update(angulo_grados=1.0), "rumbos"),
    (lambda m: m["brazos"]["R07"].update(test1_llamadas=0), "espia"),
])
def test_estados_invalidos(mutar, motivo):
    f, m = _limpio()
    mutar(m[2])
    r = ES.evaluar(*_caso(f, m))
    assert r["veredicto"] == "INVALIDO", r["motivos_invalido"]


def test_invalido_si_la_etiqueta_no_es_la_de_produccion():
    pob, sal = _caso(*_limpio())
    sal["ab"]["flag_ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER"] = True
    assert ES.evaluar(pob, sal)["veredicto"] == "INVALIDO"


def test_estados_incompletos():
    f, m = _limpio()
    pob, sal = _caso(f, m)
    del sal["ab"]
    assert ES.evaluar(pob, sal)["veredicto"] == "INCOMPLETO"
    pob, sal = _caso(f, m)
    sal["ab"]["commit"] = "otro"
    assert ES.evaluar(pob, sal)["veredicto"] == "INCOMPLETO"
    pob, sal = _caso(f, [x for x in m if x["clave"] != "g4"])
    assert ES.evaluar(pob, sal)["veredicto"] == "INCOMPLETO"
    assert ES.evaluar(pob, sal, ausentes=[{"volcan": "a", "clave": "g4", "prot": False, "lab": "neg_limpio"}])[
        "veredicto"] == "MEDIDO"
    pob, sal = _caso(f, [dict(x) for x in m])
    del sal["aa"]["granulos"][2]["pub"]["R11"]
    assert ES.evaluar(pob, sal)["veredicto"] == "INCOMPLETO"
    pob, sal = _caso(f, m)
    sal["aa"]["granulos"][0]["cprima_igual"] = None
    assert ES.evaluar(pob, sal)["veredicto"] == "INCOMPLETO"


def test_nombres_de_las_mitades():
    pob, _ = _caso(*_limpio())
    assert sorted(J.partir(pob)) == ["aa", "ab"]


def _con_protegidas(pub_por_pasada):
    """Protegidas p0, p1, ... con la publicacion de cada brazo dada; el resto, negativos limpios."""
    f, m = _limpio()
    for i, pub in enumerate(pub_por_pasada):
        f.append(_fila("p%d" % i, lab="pos", prot=True))
        m.append(_medida("p%d" % i, pub=pub))
    return _caso(f, m)


def _pub(C, M, nulos):
    d = {"C": C, "M": M}
    d.update({b: nulos[k] for k, b in enumerate(ES.NULOS)})
    return d


def test_perdidas_como_el_azar_y_especificas():
    # M pierde p0 y la pierden 10 de los 20 nulos: como el azar
    pob, sal = _con_protegidas([_pub(1, 0, [k % 2 for k in range(20)])])
    r = ES.evaluar(pob, sal)
    assert r["regla1"]["letra"] == "PIERDE PROTEGIDA" and r["adoptable_en_la_replica"] is False
    assert r["regla1"]["perdidas"]["estado"] == "PERDIDAS COMO EL AZAR"
    assert r["regla1"]["M_pierde_lo_que_C_publica"] == ["p0"]
    # ningun nulo la pierde: la perdida es de MxD03
    pob, sal = _con_protegidas([_pub(1, 0, [1] * 20)])
    assert ES.evaluar(pob, sal)["regla1"]["perdidas"]["estado"] == "PERDIDAS ESPECIFICAS DE MXD03"


def test_ganancias_especificas_y_menos_perdidas_que_el_azar():
    pob, sal = _con_protegidas([_pub(0, 1, [0] * 20)])
    r = ES.evaluar(pob, sal)
    assert r["regla1"]["ganadas"]["estado"] == "GANANCIAS ESPECIFICAS DE MXD03"
    assert r["regla1"]["C_pierde_lo_que_M_publica"] == ["p0"] and r["regla1"]["letra"] == "NO PIERDE"
    pob, sal = _con_protegidas([_pub(1, 1, [0] * 20)])
    assert ES.evaluar(pob, sal)["regla1"]["perdidas"]["estado"] == "MENOS PERDIDAS QUE EL AZAR"


def test_adoptable_solo_con_mejora_y_sin_perdidas():
    filas = [_fila("n%d" % i) for i in range(40)]
    meds = []
    for i, f in enumerate(filas):
        pub = {b: 1 for b in ES.BRAZOS}
        if i < 30:
            pub["M"] = 0
        meds.append(_medida(f["clave"], pub=pub))
    pob, sal = _caso(filas, meds)
    pob["volcanes"]["a"]["N"]["A"]["neg_limpio"] = 400
    r = ES.evaluar(pob, sal)
    assert r["balance_regla2"]["veredicto_M_contra_C"] == "MEJORA" and r["adoptable_en_la_replica"] is True
    assert r["balance_regla2"]["rango"]["estado"] == "BALANCE MEJOR QUE EL AZAR"


def test_test1_propiedad_del_test1_y_especifica():
    def t1(trig):
        return {b: {"triggered": trig[b], "caliente_en_anillo": False, "delta_L_integrated": 1.0,
                    "sigma_bg": 1.0, "n_roi": 28} for b in ES.BRAZOS}
    f, m = _limpio()
    for i, x in enumerate(m):     # M cruza en 2 granulos y cada nulo en 2 (como el azar)
        trig = {b: False for b in ES.BRAZOS}
        trig["M"] = i < 2
        for k, b in enumerate(ES.NULOS):
            trig[b] = i == (k % 10) or i == ((k + 1) % 10)
        x["brazos"] = _medida(x["clave"], test1=t1(trig))["brazos"]
    r = ES.evaluar(*_caso(f, m))
    assert r["test1"]["cruces"]["estado"] == "PROPIEDAD DEL TEST 1 (M CRUZA COMO EL AZAR)"
    for i, x in enumerate(m):     # ahora solo M cruza
        trig = {b: False for b in ES.BRAZOS}
        trig["M"] = i < 5
        x["brazos"] = _medida(x["clave"], test1=t1(trig))["brazos"]
    assert ES.evaluar(*_caso(f, m))["test1"]["cruces"]["estado"] == "MXD03 CRUZA MAS QUE EL AZAR"


def test_borde_salta_mas_que_el_azar():
    f, m = [], []
    for i in range(10):
        f.append(_fila("b%d" % i, cenit=60.0))
        pc = {b: (-23.37, -67.73) for b in ES.BRAZOS}
        pc["M"] = (-23.37 + 9.0 / 111.32, -67.73)        # el cumulo de M salta 9 km (corrimiento 1 km)
        m.append(_medida("b%d" % i, pc=pc))
    r = ES.evaluar(*_caso(f, m))
    assert r["borde"]["50-90"]["estado"] == "MXD03 SALTA MAS QUE EL AZAR"
    assert ES.evaluar(*_caso(*_limpio()))["borde"]["0-20"]["estado"] == "SALTA COMO EL AZAR"


# ---- la vara
VENT = (-23.37, -67.73)


def _ll(n, e):
    return [VENT[0] + n / 111.32, VENT[1] + e / (111.32 * math.cos(math.radians(VENT[0])))]


def _vara_caso(verdad="M", n=30, sesgo=(0.0, 0.0), sats=("MODIS_TERRA", "MODIS_AQUA"), ruido=0.2, seed=3):
    import random
    rng = random.Random(seed)
    ok, tab = [], {"granulos": {}}
    for i in range(n):
        sat = sats[i % len(sats)]
        s = (0.0, 1.4) if sat == "MODIS_TERRA" else (0.0, -1.4)     # C = M + s; sentidos opuestos
        x0 = (rng.gauss(0, 0.3), rng.gauss(0, 0.3))
        off = {"M": (0.0, 0.0), "C": (-s[0], -s[1]), "medio": (-s[0] / 2, -s[1] / 2)}[verdad]
        m = (x0[0] + off[0] + rng.gauss(0, ruido), x0[1] + off[1] + rng.gauss(0, ruido))
        c = (m[0] + s[0], m[1] + s[1])
        v = (x0[0] + sesgo[0] + rng.gauss(0, 0.1), x0[1] + sesgo[1] + rng.gauss(0, 0.1))
        u = rng.random()
        pos = {"C": _ll(*c), "M": _ll(*m)}
        for k, b in enumerate(ES.NULOS):
            a = 2 * math.pi * ((u + k / 20) % 1)
            pos[b] = _ll(c[0] + 1.4 * math.cos(a), c[1] + 1.4 * math.sin(a))
        clave = "v%d" % i
        ok.append({"volcan": "a", "clave": clave, "lab": "pos", "datetime_utc": "2026-04-%02d 01:30" % (1 + i % 28),
                   "sensor": sat, "sensor_zenith_deg": 10.0, "pico": {"pos": pos}})
        tab["granulos"]["a|" + clave] = {"vent": list(VENT), "estricta": {"noche": {"n_km": v[0], "e_km": v[1]}}}
    return ok, tab


@pytest.mark.parametrize("verdad,esperado", [("M", "MXD03 MAS CERCA"), ("C", "INTERP MAS CERCA"),
                                             ("medio", "INDECIDIBLE")])
def test_vara_da_cada_estado(verdad, esperado):
    ok, tab = _vara_caso(verdad)
    o = ES.vara(ok, tab, "pico", "estricta", "pos")
    assert o["estado"] == esperado, (o["estado"], o["dd_ic95"], o["nulo_del_estadistico"])
    if verdad == "M":
        assert 0.7 < o["lambda_mediana"] < 1.3
        assert o["M_contra_el_azar"]["estado"] == "M MAS CERCA QUE EL AZAR"
    if verdad == "C":
        assert -0.3 < o["lambda_mediana"] < 0.3


def test_vara_sin_vara_y_sin_control_de_sesgo():
    ok, tab = _vara_caso("M", n=6)
    assert ES.vara(ok, tab)["estado"] == "SIN VARA"
    ok, tab = _vara_caso("M", sats=("MODIS_AQUA",))
    assert ES.vara(ok, tab)["estado"] == "MXD03 MAS CERCA SIN CONTROL DE SESGO"


def test_vara_sesgo_por_satelite():
    """Una vara corrida 1,2 km al este con el objeto a medio camino: favorece a C en Terra (C al este de M)
    y a M en Aqua. Con el IC sumado de un lado, el control por satelite tiene que verlo."""
    ok, tab = _vara_caso("medio", n=40, sesgo=(0.0, 1.2), ruido=0.05)
    o = ES.vara(ok, tab)
    signos = {s: v["dd_mediana_km"] > 0 for s, v in o["por_satelite"].items()}
    assert signos["TERRA"] != signos["AQUA"]
    assert o["estado"] in ("SESGO POR SATELITE", "INDECIDIBLE")
    ok2 = [x for x in ok if x["sensor"] == "MODIS_TERRA"] + [x for x in ok if x["sensor"] == "MODIS_AQUA"][:6]
    o2 = ES.vara(ok2, tab)
    assert o2["estado"] == "SESGO POR SATELITE", (o2["dd_ic95"], o2["por_satelite"], o2["nulo_del_estadistico"])


def test_el_nulo_del_estadistico_se_cancela_y_una_asimetria_lo_rompe():
    """A110: con nulos simetricos las 20 medianas de los pares (k, k + 4) rodean el 0 y el efecto de M queda
    fuera de todas; si un bug pone 10 nulos justo en la vara, los pares dejan de cancelarse, el nulo crece
    y la vara deja de declarar a M aunque su efecto sea real."""
    ok, tab = _vara_caso("medio", n=40)
    nul = ES.vara(ok, tab)["nulo_del_estadistico"]
    assert nul["pares"] == 20 and min(nul["medianas_km"]) < 0 < max(nul["medianas_km"])
    ok, tab = _vara_caso("M", n=40)
    o = ES.vara(ok, tab)
    assert o["estado"] == "MXD03 MAS CERCA" and o["nulo_del_estadistico"]["max_abs_km"] < abs(o["dd_mediana_km"])
    for x in ok:
        t = tab["granulos"]["a|" + x["clave"]]["estricta"]["noche"]
        for b in ES.NULOS[:10]:
            x["pico"]["pos"][b] = _ll(t["n_km"], t["e_km"])     # el bug: el nulo cae justo en la vara
    o = ES.vara(ok, tab)
    assert o["estado"] == "INDECIDIBLE" and o["nulo_del_estadistico"]["max_abs_km"] > abs(o["dd_mediana_km"])


def test_la_vara_entra_al_evaluador_completo():
    ok, tab = _vara_caso("M", n=12)
    filas = [_fila(x["clave"], lab="pos", sensor=x["sensor"], fecha=x["datetime_utc"]) for x in ok]
    meds = [_medida(x["clave"], pico=x["pico"]) for x in ok]
    pob, sal = _caso(filas, meds)
    r = ES.evaluar(pob, sal, tabla_vara=tab)
    assert r["vara"]["principal"]["n"] == 12 and r["vara"]["principal"]["estado"].startswith("MXD03 MAS CERCA")


# ------------------------------------------------------------------ las salidas medidas quedaron escritas
def test_la_sensibilidad_del_test1_medida_quedo_escrita():
    txt = (EXP / "sensibilidad_test1_121_salida.txt").read_text(encoding="utf-8")
    assert "Granulos con C, M y R medidos: 469" in txt
    assert re.search(r"todos\s+n=126 .*\|dk\| M 0\.515, R 0\.595", txt)
    assert "M: {'de': 149, 'dispara_C_no_M': 17, 'dispara_M_no_C': 19}" in txt
    assert "R: {'de': 149, 'dispara_C_no_R': 15, 'dispara_R_no_C': 14}" in txt


def test_el_presupuesto_medido_quedo_escrito():
    txt = (EXP / "presupuesto_tiempo_salida.txt").read_text(encoding="utf-8")
    m = re.findall(r"maximo propio ([\d.]+) min, maximo peor caso ([\d.]+) min", txt)
    assert len(m) == 2 and float(m[1][1]) <= 30.0


def test_el_poder_de_la_vara_quedo_escrito():
    txt = (EXP / "poder_vara_salida.txt").read_text(encoding="utf-8")
    assert "Conjunto principal: 76 granulos" in txt
    linea = next(x for x in txt.splitlines() if x.startswith("verdad M     ruido pixel 0.5"))
    assert float(re.search(r"'MXD03 MAS CERCA': ([\d.]+)", linea).group(1)) >= 0.9


# ------------------------------------------------------------------ 6. el workflow
WF = ROOT / ".github" / "workflows" / "probe-s151-mxd03-sola-123.yml"


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
    otros = set()
    for p in (ROOT / ".github" / "workflows").glob("*.yml"):
        if p != WF:
            g = (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("concurrency")
            if isinstance(g, dict):
                otros.add(g.get("group"))
    assert grupo not in otros
    assert d["concurrency"]["cancel-in-progress"] is False
    assert "git push" not in txt
    for s in d["jobs"]["probe"]["steps"] + d["jobs"]["agregar"]["steps"]:
        if "| tee" in s.get("run", ""):
            assert "set -o pipefail" in s["run"]


def test_workflow_timeouts_con_margen_sobre_el_presupuesto():
    import yaml
    d = yaml.safe_load(WF.read_text(encoding="utf-8"))
    probe = d["jobs"]["probe"]
    # A92: "probe_sola.py" es subcadena de "probar_probe_sola.py"; el paso se busca por su bandera
    paso = next(s for s in probe["steps"] if "--presupuesto-min" in s.get("run", ""))
    assert re.search(r"_s151_mxd03_sola_123/probe_sola\.py --job", paso["run"])
    presupuesto = float(re.search(r"--presupuesto-min (\d+)", paso["run"]).group(1))
    assert probe["timeout-minutes"] >= 1.3 * presupuesto + 5        # A15, mas la instalacion
    peor = max(float(x) for x in re.findall(r"maximo peor caso ([\d.]+) min",
                                             (EXP / "presupuesto_tiempo_salida.txt").read_text(encoding="utf-8"))[1:])
    assert presupuesto >= 1.3 * peor
    for s in probe["steps"] + d["jobs"]["agregar"]["steps"]:
        for ruta in re.findall(r"experiments/\S+?\.py", s.get("run", "")):
            assert (ROOT / ruta).exists(), ruta
