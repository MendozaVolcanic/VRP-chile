"""Pruebas del instrumento del A/B de fase de grilla S190 (experiments/_s190_l1b_ab/PREREGISTRO.md).

POR QUÉ: el lector `leer_ab.evaluar` decide un veredicto; un analizador que decide algo va envuelto en tests/ (S174). Se
prueba cada criterio con resultados sintéticos donde ese criterio, y solo ese, separa los veredictos; el manifiesto contra
lo sellado; y que el driver corre los 4 brazos de verdad sobre un barrido sintético (la fase cambia algo).
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AQUI = ROOT / "experiments" / "_s190_l1b_ab"
for p in (ROOT, AQUI, ROOT / "tests"):
    sys.path.insert(0, str(p))

import ab_fase as AB  # noqa: E402
import leer_ab as LA  # noqa: E402

MAN = json.load(open(AQUI / "manifiesto_s190.json", encoding="utf-8"))
POB = MAN["poblacion_por_estrato"]


# ------------------------------------------------------------------------------------------------ manifiesto
def test_manifiesto_es_el_sellado():
    puntua = [p for p in MAN["pasadas"] if p["rol"] == "puntua"]
    assert MAN["semilla"] == 190
    assert len(puntua) == 193 and MAN["n_replica_s185"] == 10
    assert MAN["muestra_por_estrato"] == {"calla": 12, "solo_via": 19, "rut_>=0.9": 44, "rut_0.8-0.9": 30, "rut_0.6-0.8": 30,
                                          "rut_0.3-0.6": 12, "rut_<0.3": 8, "amb_<1.2": 20, "amb_1.2-1.5": 10, "amb_>=1.5": 8}
    assert not any(p["volcan"] == "Tupungatito" and p["s185"] for p in puntua)
    assert sum(p["cat"] == "calla" and p["volcan"] != "Tupungatito" for p in puntua) == LA.N_CALLA_FUERA
    rep = [p for p in MAN["pasadas"] if p["rol"] == "replica_s185"]
    assert sum(p["cat"] == "calla" for p in rep) == LA.N_CALLA_S185 and all(p["volcan"] == "Tupungatito" for p in rep)


def test_manifiesto_categorias_coherentes_con_lo_publicado():
    for p in MAN["pasadas"]:
        det = (p["ref"]["publicado_n_pix"] or 0) > 0
        alerta_mirova = p["ref"]["mirova_tipo"] == "ALERTA_TERMICA"
        assert p["cat"] == {(True, True): "ambos", (True, False): "calla", (False, True): "solo_via",
                            (False, False): "rutina"}[(alerta_mirova, det)]
        assert p["l1b"][:3] in AB.PRODUCTOS and "_750" not in p["l1b"]


def test_partir_cubre_cada_granulo_una_vez():
    vistos = []
    for k in range(6):
        vistos += list(AB.partir(MAN["pasadas"], k, 6))
    assert sorted(vistos) == sorted({p["l1b"] for p in MAN["pasadas"]})


# ------------------------------------------------------------------------------------------------ driver
def test_grilla_corrida_y_brazos():
    g = {"ul_x": 1000.0, "ul_y": 5000.0, "paso": 750.0}
    assert AB.grilla_corrida(g, 0.0, 0.5)["ul_y"] == 5375.0 and AB.grilla_corrida(g, 0.5, 0.0)["ul_x"] == 1375.0
    assert AB.BRAZOS == {"A": (0.0, 0.0), "B": (0.0, 0.5), "C": (0.5, 0.5), "Z": (0.5, 0.0)}


def test_reproduce():
    cd = {"fila": 3, "col": 4, "margen": 0.9}
    ref = {"publicado_n_pix": 0, "publicado_celda_decisiva": dict(cd)}
    assert AB.reproduce({"n_pix": 0, "celda_decisiva": dict(cd)}, ref)
    assert not AB.reproduce({"n_pix": 1, "celda_decisiva": dict(cd)}, ref)
    assert not AB.reproduce({"n_pix": 0, "celda_decisiva": dict(cd, margen=0.902)}, ref)
    assert not AB.reproduce({"n_pix": 0, "celda_decisiva": dict(cd, col=5)}, ref)
    assert not AB.reproduce({"estado": "sin_record"}, ref)


def test_correr_brazos_sobre_barrido_sintetico_la_fase_cambia_algo():
    from test_probe_s185_l1b import barrido
    rad, lat, lon, ang = barrido(-33.4256, -69.7977, 750.0, 90, {"M13": 0.6, "M15": 7.0}, {(0, 0): 6.0, (0, 1): 3.0})
    p = {"volcan": "Tupungatito", "vent": [-33.389044, -69.826374], "inner_km": 7,
         "l1b": "VJ102MOD.A2026062.0548.021.2026062122629.nc"}
    r = AB.correr_brazos(rad, lat, lon, ang, p)
    assert set(r) == {"A", "B", "C", "Z"} and all("celda_decisiva" in v for v in r.values())
    margenes = {b: v["celda_decisiva"]["margen"] for b, v in r.items()}
    assert len({round(m, 6) for m in margenes.values()}) >= 2, margenes   # el instrumento puede dar distinto (A116)


# ------------------------------------------------------------------------------------------------ regla
def it(cat, estrato, A, B, C=None, Z=None, rol="puntua", margen=0.95, mir_vrp=0.3, volcan="X", dt="t"):
    br = {}
    for b, al in (("A", A), ("B", B), ("C", A if C is None else C), ("Z", A if Z is None else Z)):
        br[b] = {"n_pix": 1 if al else 0, "celda_decisiva": {"margen": margen * (1.1 if al and not A else 1.0)}}
    return {"volcan": volcan, "dt": dt, "cat": cat, "estrato": estrato, "rol": rol, "ok": True, "reproduce": True,
            "brazos": br, "ref": {"mirova_vrp_mw": mir_vrp, "publicado_celda_decisiva": {"margen": margen}}}


def base(gana_calla=8):
    """Conjunto sintético con todos los estratos; B recupera `gana_calla` de 12 calladas y no daña nada."""
    xs = [it("calla", "calla", False, i < gana_calla, dt=f"c{i}") for i in range(12)]
    xs += [it("solo_via", "solo_via", True, True, dt=f"s{i}") for i in range(19)]
    for e, n, m in (("rut_>=0.9", 44, .95), ("rut_0.8-0.9", 30, .85), ("rut_0.6-0.8", 30, .7), ("rut_0.3-0.6", 12, .4),
                    ("rut_<0.3", 8, .1)):
        xs += [it("rutina", e, False, False, margen=m, dt=f"{e}{i}") for i in range(n)]
    for e, n in (("amb_<1.2", 20), ("amb_1.2-1.5", 10), ("amb_>=1.5", 8)):
        xs += [it("ambos", e, True, True, margen=1.3, dt=f"{e}{i}") for i in range(n)]
    xs += [it("calla", "calla", False, True, rol="replica_s185", dt=f"r{i}") for i in range(6)]
    xs += [it("ambos", "amb_<1.2", True, True, rol="replica_s185", dt=f"ra{i}") for i in range(4)]
    return xs


def test_brazo_A_da_cero_por_construccion():
    r = LA.evaluar(base(), POB)
    assert r["metricas"]["A"]["G"] == 0 and r["metricas"]["A"]["D"] == 0 and r["metricas"]["A"]["cambios"] == 0


def test_cumple_cuando_todo_se_cumple():
    r = LA.evaluar(base(), POB)
    assert r["veredicto"] == "CUMPLE", r["criterios_B"]
    assert r["metricas"]["B"]["calla_recuperadas"] == 8


def test_C4_pocas_calladas():
    r = LA.evaluar(base(gana_calla=5), POB)
    assert not r["criterios_B"]["C4"] and r["veredicto"] == "NO CUMPLE"


def test_C2_una_rutina_baja_alertada_hunde():
    xs = base()
    xs[[i for i, x in enumerate(xs) if x["estrato"] == "rut_0.3-0.6"][0]] = it("rutina", "rut_0.3-0.6", False, True, margen=.4)
    r = LA.evaluar(xs, POB)
    assert not r["criterios_B"]["C2"] and not r["criterios_B"]["C3"] and r["veredicto"] == "NO CUMPLE"


def test_C1_protegida_perdida():
    xs = base()
    xs[[i for i, x in enumerate(xs) if x["estrato"] == "amb_>=1.5"][0]] = it("ambos", "amb_>=1.5", True, False, mir_vrp=2.0)
    r = LA.evaluar(xs, POB)
    assert not r["criterios_B"]["C1"] and r["veredicto"] == "NO CUMPLE"


def test_C3_dano_pesado_en_rutinas_altas():
    xs = base(gana_calla=6)
    idx = [i for i, x in enumerate(xs) if x["estrato"] == "rut_0.8-0.9"][:2]
    for i in idx:
        xs[i] = it("rutina", "rut_0.8-0.9", False, True, margen=.85)
    r = LA.evaluar(xs, POB)          # G = 6, D = 2 * 86 / 30 = 5,7: Net 0,3 < 3
    assert r["criterios_B"]["C1"] and r["criterios_B"]["C2"] and not r["criterios_B"]["C3"]


def test_C5_el_control_Z_gana_igual():
    xs = base()
    for x in xs:
        if x["cat"] == "calla":
            x["brazos"]["Z"] = dict(x["brazos"]["B"])
    r = LA.evaluar(xs, POB)
    assert not r["criterios_B"]["C5"] and r["veredicto"] == "NO CUMPLE"


def test_sin_dato_si_no_replica_o_no_reproduce():
    xs = base()
    for x in xs:
        if x["rol"] == "replica_s185":
            x["brazos"]["B"]["n_pix"] = 0
    assert LA.evaluar(xs, POB)["veredicto"] == "SIN DATO"
    xs = base()
    for x in xs[:40]:
        x["reproduce"] = False
    r = LA.evaluar(xs, POB)
    assert r["veredicto"] == "SIN DATO" and len(r["excluidas"]) == 40


def test_sin_efecto():
    xs = base(gana_calla=0)
    r = LA.evaluar(xs, POB)
    assert r["veredicto"] == "NO CUMPLE (sin efecto)"


def test_pasada_ausente_cuenta_en_el_denominador():
    xs = [x for x in base() if not (x["cat"] == "calla" and x["rol"] == "puntua")]
    falt = [{"volcan": "X", "dt": f"f{i}", "l1b": "g", "cat": "calla", "estrato": "calla", "rol": "puntua", "ok": False}
            for i in range(12)]
    r = LA.evaluar(xs + falt, POB)
    assert r["veredicto"] == "SIN DATO" and not r["validez"]["V1"]


@pytest.mark.parametrize("cat,A,B,esperado", [("calla", False, True, 1), ("calla", False, False, 0), ("solo_via", True, False, 1),
                                              ("ambos", True, False, -1), ("rutina", False, True, -1), ("rutina", False, False, 0)])
def test_evento(cat, A, B, esperado):
    assert LA.evento(it(cat, "e", A, B), "B") == esperado
