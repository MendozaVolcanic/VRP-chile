# -*- coding: utf-8 -*-
"""S162, instrumento T3: placebo de ganancia y comparador d′ (D-28) y P2 con signos por bloque (D-45) y los placebos
de D-44, en el evaluador común (VIIRS y MODIS).

POR QUÉ. K queda bajo MIROVA, así que un brazo que sólo multiplica la magnitud de K por 1,2 «se acerca» en promedio
y la regla simétrica de M le da MEJORA (R2-8 de AUDIT_S158_R2). El comparador d′ tiene que dejarlo sin MEJORA, y un
brazo que sube justo los pares que debe subir tiene que pasar. En P2, un placebo que apaga sólo negativos limpios
tiene que GANAR, uno que apaga sólo alertas bajo 1 MW tiene que PERDER, y el simétrico tiene que dar pocos falsos:
si no, la prueba no mide lo que dice (V42-10). La equivalencia con evaluar_d25.py del tag s161-d25-lectura se prueba
aparte (experiments/_s162_instrumento/t3_equivalencia.py), porque ese archivo no está en main.
"""
import random
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts import clase_mirova as cm  # noqa: E402
from scripts import evaluador_comun as ec  # noqa: E402

VOLS = ["Lascar", "Isluga", "NevadosDeChillan", "Villarrica"]


def pares_bajo_mirova(n=40, semilla=1):
    """K bajo MIROVA (razón ~0,55) con dispersión, 4 volcanes y 10 noches."""
    rng = random.Random(semilla)
    P = []
    for i in range(n):
        v, dia = VOLS[i % 4], "2026-10-%02d" % (1 + i % 10)
        m = 10 ** rng.uniform(-1, 1)
        k = m * 10 ** (-0.26 + rng.gauss(0, 0.15))
        P.append({"k": k, "d": k, "m": m, "clave": "%s|VIIRS750|%s 05:%02d" % (v, dia, i), "bloque": "%s|%s" % (v, dia)})
    return P


# ------------------------------------------------------------------ M y el comparador
def test_placebo_de_ganancia_da_mejora_sin_comparador_y_no_con_comparador():
    P = pares_bajo_mirova()
    r = ec.placebo_ganancia(P, "decide")
    assert r["1.2"]["sin_comparador"] == "MEJORA"          # el defecto que el comparador corrige
    assert r["1.2"]["con_comparador"] != "MEJORA"
    assert r["0.8"]["sin_comparador"] == "EMPEORA"


def test_dprima_de_una_ganancia_pareja_es_cero_exacto():
    P = [dict(p, d=p["k"] * 1.2) for p in pares_bajo_mirova()]
    W = ec.pesos_bloque([p["bloque"] for p in P])
    det = ec.comparar_con_ganancia(P, W, [p["bloque"] for p in P])
    assert det["dprima_max_abs"] == 0.0 and abs(det["g_hat_factor"] - 1.2) < 1e-9


def test_brazo_que_corrige_cada_par_hacia_mirova_da_mejora_con_comparador():
    P = [dict(p, d=p["m"] * 10 ** (0.3 * __import__("math").log10(p["k"] / p["m"]))) for p in pares_bajo_mirova()]
    r, det = ec.decidir_estrato(P, "decide")
    assert r == "MEJORA" and det.get("dprima_da_mejora") is True
    # el control positivo de la calibración (todos los d hacia MIROVA) tiene que dar MEJORA con 40 pares
    assert det["poder"] is True


def test_brazo_que_aleja_de_mirova_da_empeora():
    P = [dict(p, d=p["k"] * 0.5) for p in pares_bajo_mirova()]
    assert ec.decidir_estrato(P, "decide")[0] == "EMPEORA"


def test_estrato_que_solo_bloquea_no_deja_pasar_mejora():
    P = [dict(p, d=p["m"] * 10 ** (0.3 * __import__("math").log10(p["k"] / p["m"]))) for p in pares_bajo_mirova()]
    assert ec.decidir_estrato(P, "bloquea")[0] == "NEUTRO"
    assert ec.decidir_estrato(P, "informa")[0] == "MEJORA"


def test_mejora_de_un_solo_volcan_no_cuenta():
    P = pares_bajo_mirova()
    P = [dict(p, d=(p["m"] if p["clave"].startswith("Lascar") else p["k"])) for p in P]
    r, det = ec.decidir_estrato(P, "decide")
    assert r != "MEJORA"


def test_mejora_que_sostiene_un_solo_volcan_queda_neutro_por_la_regla_de_volcanes():
    # 30 pares de Láscar corregidos hacia MIROVA y 10 de Isluga sin cambio: la mediana de d es negativa (MEJORA de la
    # regla) pero sólo un volcán con 3 pares o más la sostiene (H4 de la adenda D-27).
    rng = __import__("random").Random(5)
    P = []
    for i in range(40):
        v = "Lascar" if i < 30 else "Isluga"
        dia = "2026-10-%02d" % (1 + i % 10)
        m = 10 ** rng.uniform(-1, 1)
        k = m * 10 ** (-0.26 + rng.gauss(0, 0.05))
        d = m * 10 ** (0.3 * __import__("math").log10(k / m)) if v == "Lascar" else k
        P.append({"k": k, "d": d, "m": m, "clave": "%s|VIIRS750|%s 05:%02d" % (v, dia, i), "bloque": "%s|%s" % (v, dia)})
    r, det = ec.decidir_estrato(P, "decide")
    assert det["regla"] == "MEJORA" and r == "NEUTRO"
    assert "menos de 2 volcanes" in det["nota"]


def test_sin_sustrato_con_pocos_pares_o_pocas_noches():
    P = pares_bajo_mirova(4)
    assert ec.decidir_estrato(P, "decide")[0] == "SIN SUSTRATO"
    P = [dict(p, bloque="Lascar|2026-10-01") for p in pares_bajo_mirova(10)]
    assert ec.decidir_estrato(P, "decide")[0] == "SIN SUSTRATO"


def test_d_par_signo():
    assert ec.d_par(0.5, 1.0, 1.0) < 0 < ec.d_par(1.0, 0.5, 1.0)


# ------------------------------------------------------------------ P2: prueba de signos
def test_prueba_de_signos_exacta_siete_noches_iguales():
    pr = ec.prueba_signos_p2([1] * 7, 7)
    assert pr["metodo"] == "exacto" and pr["pierde"] == [1, 128]
    assert ec.regla_signos_p2(7, 7, pr) == "PIERDE"


def test_prueba_de_signos_sin_sustrato_y_bloquea():
    assert ec.regla_signos_p2(4, 4, ec.prueba_signos_p2([1] * 4, 4)) == "SIN SUSTRATO"
    sumas = [1, 1, -1, 1, 1]
    assert ec.regla_signos_p2(3, 5, ec.prueba_signos_p2(sumas, 3)) == "BLOQUEA"
    sumas = [-1, -1, 1, -1, -1]
    assert ec.regla_signos_p2(-3, 5, ec.prueba_signos_p2(sumas, -3)) == "EMPATE"


def test_prueba_de_signos_por_sorteos_desde_21_bloques():
    pr = ec.prueba_signos_p2([1] * 21, 21)
    assert pr["metodo"] == "sorteos" and pr["minimo"] == [1, 10001] and pr["pierde"][0] >= 1


# ------------------------------------------------------------------ P2 sobre la tabla y los placebos de D-44
def tabla_sintetica(semilla=3, noches=24):
    """Control tipo K: publica casi todas las alertas bajo 1 MW y algunos negativos limpios."""
    rng = random.Random(semilla)
    filas, recs = [], []
    for i in range(noches):
        v, dia = VOLS[i % 4], "2026-%02d-%02d" % (9 + i // 28, 1 + i % 28)
        for j, (tipo, vrp) in enumerate((("ALERTA_TERMICA", 0.4), ("RUTINA", 0.0), ("ALERTA_TERMICA", 0.3)) if i % 2
                                        else (("RUTINA", 0.0), ("RUTINA", 0.0), ("RUTINA", 0.0))):
            t = "%s 0%d:%02d" % (dia, 4 + j, 10)
            filas.append({"volcano": v, "sensor_bucket": "VIIRS750", "fecha_utc": t + ":00", "source": "CONS",
                          "tipo": tipo, "vrp_mw": vrp, "dist_km": 1.0, "sin_geometria": False})
            pub = rng.random() < (0.9 if tipo != "RUTINA" else 0.3)
            recs.append({"vol": v, "b": "VIIRS750", "dt": datetime.strptime(t, "%Y-%m-%d %H:%M"), "pub": pub,
                         "disp": 0.3 if pub else 0.0})
    ps = cm.resumir_pasadas(filas, regla_minimas="original")
    return ec.tabla_por_pasada(ps, {"prod": recs}, "prod")


def test_clase_p2_negativo_exige_noche_sin_alerta_ni_fp():
    T = tabla_sintetica()
    clases = {f["clave"]: ec.clase_p2(f) for f in T}
    # noches impares tienen alerta: su RUTINA no es negativo limpio
    assert all(c != "negativo" for f, c in zip(T, clases.values()) if f["noche_con_alerta"])
    assert sum(c == "negativo" for c in clases.values()) > 0 and sum(c == "alerta_mb" for c in clases.values()) > 0


def _tabla(filas, recs):
    return ec.tabla_por_pasada(cm.resumir_pasadas(filas, regla_minimas="original"), {"prod": recs}, "prod")


def _f(h, tipo, vrp, dist=1.0):
    return {"volcano": "Lascar", "sensor_bucket": "VIIRS750", "fecha_utc": "2026-10-12 0%d:00:00" % h, "source": "CONS",
            "tipo": tipo, "vrp_mw": vrp, "dist_km": dist, "sin_geometria": False}


def _r(h, pub):
    return {"vol": "Lascar", "b": "VIIRS750", "dt": datetime(2026, 10, 12, h, 0), "pub": pub, "disp": 0.3 if pub else 0}


def test_rutina_en_noche_con_falso_positivo_no_es_negativo_limpio():
    T = _tabla([_f(1, "RUTINA", 0.0), _f(2, "FALSO_POSITIVO", 2.0, dist=15.0)], [_r(1, True), _r(2, False)])
    assert T[0]["noche_con_fp"] and ec.clase_p2(T[0]) == "otra"
    T = _tabla([_f(1, "RUTINA", 0.0), _f(2, "RUTINA", 0.0)], [_r(1, True), _r(2, False)])
    assert ec.clase_p2(T[0]) == "negativo"


def test_placebo_c_voltea_lo_mismo_de_cada_lado_en_un_bloque_asimetrico():
    # Un bloque con 3 alertas bajo 1 MW publicadas (lado +1) y 1 sin publicar (lado -1): se voltea UNA, salga el lado
    # que salga, así el aporte es ±1 con probabilidad 1/2.
    filas = [_f(h, "ALERTA_TERMICA", 0.4) for h in (1, 2, 3, 4)]
    T = _tabla(filas, [_r(1, True), _r(2, True), _r(3, True), _r(4, False)])
    netos = set()
    for s in range(12):
        res, det = ec.placebo_p2(T, "prod", "c", 1.0, s)
        assert det["tocadas"] == 1, (s, det)
        netos.add(det["neto"])
    assert netos == {1, -1}


def test_control_contra_si_mismo_no_tiene_discordantes():
    T = tabla_sintetica()
    T2 = [dict(f, rec=dict(f["rec"], copia=f["rec"]["prod"]), cob=dict(f["cob"], copia=f["cob"]["prod"])) for f in T]
    assert ec.contribuciones_p2(T2, "prod", "copia") == []
    assert ec.decidir_p2([])[0] == "SIN SUSTRATO"


def test_placebo_a_apagar_negativos_gana():
    assert ec.placebo_p2(tabla_sintetica(), "prod", "a", 1.0, 0)[0] == "GANA"


def test_placebo_b_apagar_alertas_pierde():
    assert ec.placebo_p2(tabla_sintetica(), "prod", "b", 1.0, 0)[0] == "PIERDE"


def test_placebo_c_simetrico_pocos_falsos_y_voltea_por_noche():
    T = tabla_sintetica(noches=48)
    res = [ec.placebo_p2(T, "prod", "c", 0.5, s) for s in range(40)]
    falsos = sum(r in ("GANA", "PIERDE") for r, _ in res)
    assert falsos <= 4                                   # 10 % de 40, holgura sobre el 5 % por cola
    assert all(d["tocadas"] > 0 for _, d in res)
    # no deja rastro del brazo sintético en la tabla
    assert all(set(f["rec"]) == {"prod"} for f in T)


def test_pares_m_solo_alertas_que_los_dos_publican_y_observan():
    filas = [{"volcano": "Lascar", "sensor_bucket": "VIIRS750", "fecha_utc": "2026-10-12 0%d:00:00" % h, "source": "CONS",
              "tipo": tipo, "vrp_mw": v, "dist_km": 1.0, "sin_geometria": False}
             for h, tipo, v in ((1, "ALERTA_TERMICA", 2.0), (2, "ALERTA_TERMICA", 0.5), (3, "RUTINA", 0.0),
                                (4, "ALERTA_TERMICA", 0.8), (5, "ALERTA_TERMICA", 0.6))]
    t = lambda h: datetime(2026, 10, 12, h, 0)  # noqa: E731
    prod = [{"vol": "Lascar", "b": "VIIRS750", "dt": t(h), "pub": p, "disp": d}
            for h, p, d in ((1, True, 1.0), (2, True, 0.3), (3, True, 0.2), (4, False, 0.0))]
    D = [{"vol": "Lascar", "b": "VIIRS750", "dt": t(h), "pub": p, "disp": d}
         for h, p, d in ((1, True, 1.5), (2, True, 0.4), (3, True, 0.2), (4, True, 0.5), (5, True, 0.6))]
    T = ec.tabla_por_pasada(cm.resumir_pasadas(filas, regla_minimas="original"), {"prod": prod, "D": D}, "prod")
    pares, salen = ec.pares_m(T, "prod", "D", lambda f: "todo")
    assert [(p["k"], p["d"], p["m"]) for p in pares["todo"]] == [(1.0, 1.5, 2.0), (0.3, 0.4, 0.5)]
    assert salen == {"D publica, prod no": 1}      # la de las 04:00; la de las 05:00 no la observó el control
    assert pares["todo"][0]["bloque"] == "Lascar|2026-10-12"


def test_placebo_desconocido_falla_fuerte():
    try:
        ec.placebo_p2(tabla_sintetica(), "prod", "z", 0.5, 0)
    except ValueError:
        return
    raise AssertionError("un placebo desconocido no puede pasar en silencio")
