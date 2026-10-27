# -*- coding: utf-8 -*-
"""Pruebas del evaluador del A/B de MxD03 sobre K: las 12 del §8 del pre-registro (PREREGISTRO_MXD03.md) y las 5
mutaciones que pide. Cada prueba se corrio primero contra un evaluador vacio (`--modulo evaluar_vacio`) y tiene que
FALLAR ahi por la razon que dice; con el evaluador correcto tiene que PASAR (S140). Las mutaciones se cuentan solo si
las atrapa una ASERCION de este archivo; una excepcion no cuenta (S156, control de caida).

Uso: python probar_evaluar_mxd03.py [--modulo evaluar_mxd03] [--mutaciones]
"""
import argparse
import importlib
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
NULOS = tuple("R%02d" % k for k in range(20))


# ------------------------------------------------------------------ fabricas de filas sinteticas
def fila(vol="Lascar", dt="2026-03-14 07:05", lab="neg_limpio", z=20.0, pub_k=0, pub_x=0, pub_r=None, sensor="MODIS_AQUA",
         partida=False, hermanos=(), vrp_k=None, vrp_x=None, vrp_m=None, r_mueve=True, k2_igual=True, estado="ok",
         difiere=False, decide=None, expuesta=False, sha="3695f6758aaa", brazos_x_none=False):
    """Una fila ya unida (poblacion + salida del arnes). pub_r: lista de 20 publicaciones de R (None si z > 35)."""
    r_nulos = z <= 35
    if pub_r is None and r_nulos:
        pub_r = [pub_k] * 20
    pub = {"K": pub_k, "K2": pub_k, "X": pub_x}
    br = {"K": {"pc_vrp": vrp_k, "pc_lat": -23.37, "pc_lon": -67.73, "dc": "summit" if pub_k else None},
          "K2": {"pc_vrp": vrp_k, "pc_lat": -23.37, "pc_lon": -67.73, "dc": "summit" if pub_k else None},
          "X": None if brazos_x_none else {"pc_vrp": vrp_x, "pc_lat": -23.37, "pc_lon": -67.73,
                                            "dc": "summit" if pub_x else None}}
    nulos = []
    if r_nulos:
        for k, p in enumerate(pub_r):
            pub[NULOS[k]] = p
            # el nulo «vivo» mueve su cumulo publicado 0,6 km al norte en la mitad de los rumbos
            br[NULOS[k]] = {"pc_vrp": vrp_k, "pc_lat": -23.37 + (0.6 / 111.32 if (r_mueve and k % 2) else 0.0),
                            "pc_lon": -67.73, "dc": "summit" if p else None}
            nulos.append({"k": k, "km_pedido": 2.0, "km_aplicado": 2.0, "angulo_grados": 18.0 * k})
    if decide is None:
        decide = lab in ("protegida", "bajo1") or expuesta or (lab == "neg_limpio" and pub_k)
    return {"tipo": "record", "vol": vol, "dt": dt, "lab": lab, "z": z, "sensor": sensor, "estado": estado,
            "pub": pub, "brazos": br, "k2_igual": k2_igual, "partida": partida, "hermanos_lab": list(hermanos),
            "vrp_mirova": vrp_m, "inner": 5.0, "r_nulos": r_nulos, "nulos": nulos, "k_difiere_de_guardado": difiere,
            "decide": decide, "expuesta": expuesta, "codigo_sha": sha, "pub_guardada": pub_k, "pc_vrp_guardada": vrp_k,
            "desplazamiento": {"km": 2.0}}


def base(n_neg=30):
    """Poblacion minima: una protegida que todos publican, una bajo 1 MW y negativos sin publicar, todo <= 35."""
    out = [fila(lab="protegida", dt="2026-03-27 07:10", pub_k=1, pub_x=1, vrp_k=1.2, vrp_x=1.2, vrp_m=1.5),
           fila(lab="bajo1", dt="2026-03-28 07:10", pub_k=1, pub_x=1, vrp_k=0.3, vrp_x=0.3, vrp_m=0.5)]
    for i in range(n_neg):
        out.append(fila(vol="PuyehueCordonCaulle" if i % 3 == 0 else "Lascar",
                        dt=(datetime(2026, 4, 1) + timedelta(days=i)).strftime("%Y-%m-%d 02:00")))
    return out


def con_saldo(filas, dx, dr):
    """Fuerza S(X)-S(K) = dx y S(Rk)-S(K) = dr[k] encendiendo negativos limpios <= 35 (fuera de Cordon Caulle)."""
    negs = [f for f in filas if f["lab"] == "neg_limpio" and f["vol"] == "Lascar" and f["z"] <= 35]
    for j, f in enumerate(negs):
        f["pub"]["X"] = 1 if j < dx else 0
        for k in range(20):
            f["pub"][NULOS[k]] = 1 if j < dr[k] else 0
    return filas


# ------------------------------------------------------------------ las 12 pruebas
def pruebas(E):
    res = []

    def caso(nombre, fn):
        try:
            ok, detalle = fn()
        except Exception as e:  # noqa: BLE001
            ok, detalle = False, "EXCEPCION %s: %s" % (type(e).__name__, e)
        res.append((nombre, bool(ok), detalle))

    def t1():
        f = base()
        f.append(fila(lab="protegida", dt="2026-04-08 01:50", pub_k=1, pub_x=0, pub_r=[0] * 15 + [1] * 5, vrp_k=1.1,
                      vrp_m=1.3))
        r = E.p1(f)
        return r["estado"] == "VETADO" and r["perdidas"][0]["fragilidad"] == 15, r
    caso("1 protegida apagada por X: VETADO aunque 15 R tambien la apaguen", t1)

    def t2():
        out = []
        for dx, dr, esp in ((3, [-1, 1] * 10, "PIERDE"), (1, [-3, 3] * 10, "EMPATE"), (-3, [-1, 1] * 10, "GANA")):
            out.append((E.regla_p2(dx, dr, True), esp))
        return all(a == b for a, b in out), out
    caso("2 regla de P2: +3 contra +-1 PIERDE; +1 contra +-3 EMPATE; -3 GANA", t2)

    def t3():
        f = base()
        for x in f:
            if x["r_nulos"]:
                for k in range(20):
                    x["brazos"][NULOS[k]]["pc_lat"] = x["brazos"]["K"]["pc_lat"]
        f = con_saldo(f, 3, [0] * 20)
        r = E.p2(f)
        return r["estado"] == "INDECIDIBLE", r
    caso("3 R sin mover ningun cumulo: P2 INDECIDIBLE (control 2), no PIERDE", t3)

    def t4():
        f = base()
        f.append(fila(lab="neg_limpio", dt="2026-05-01 02:00", z=40.0, pub_k=0, pub_x=1))
        r, inf = E.p2(f), E.p2_informe(f)
        return r["delta_x"] == 0 and inf["sobre35"]["delta_x"] == 1, (r, inf["sobre35"])
    caso("4 cambio de X a 40 grados: fuera de la decision de P2, dentro de su informe", t4)

    def t5():
        f = base()
        cc = [x for x in f if x["vol"] == "PuyehueCordonCaulle"][0]
        cc["pub"]["X"] = 1
        r, inf = E.p2(f), E.p2_informe(f)
        return r["delta_x"] == 1 and inf["sin_cc_le35"]["delta_x"] == 0, (r["delta_x"], inf["sin_cc_le35"])
    caso("5 negativo de Cordon Caulle publicado de mas: cambia P2, no P2 sin Cordon Caulle", t5)

    def t6():
        f = base()
        f.append(fila(lab="neg_limpio", dt="2026-05-02 07:05", pub_k=0, pub_x=1, partida=True, hermanos=("sin_info",)))
        r, p6 = E.p2(f), E.p6(f)
        return r["delta_x"] == 0 and any(x["dt"] == "2026-05-02 07:05" for x in p6), (r["delta_x"], p6)
    caso("6 cambio en mitad partida con hermana sin_info: en P6, no en P2", t6)

    def t7():
        f = base()
        f[3]["k2_igual"] = False
        return E.control_k2(f) == "INDECIDIBLE" and E.control_k2(base()) == "OK", E.control_k2(f)
    caso("7 K2 distinto de K: INDECIDIBLE", t7)

    def t8():
        f = base()
        f[0]["k_difiere_de_guardado"] = True
        no = E.control_arnes(f, [{"vol": f[0]["vol"], "dt": f[0]["dt"], "estado": "no_reproduce"}])
        si = E.control_arnes(f, [{"vol": f[0]["vol"], "dt": f[0]["dt"], "estado": "deriva_de_version"}])
        return no["estado"] == "INDECIDIBLE" and si["estado"] == "OK" and len(si["deriva"]) == 1, (no, si)
    caso("8 alerta con K distinto de data/: sin reproducir INDECIDIBLE, reproducida en su sha deriva y sigue", t8)

    def t9():
        f = base()
        # magnitudes de 1,5 a 2,6 MW: con 0,97 ninguna cruza 1 MW (si cruzara, P1b mandaria a Nicolas, y con razon)
        al = [fila(lab="protegida", dt="2026-06-%02d 07:10" % (i + 1), pub_k=1, pub_x=1, vrp_k=1.5 + 0.1 * i,
                   vrp_x=0.97 * (1.5 + 0.1 * i), vrp_m=3.0 + 0.1 * i) for i in range(12)]
        f += al
        m = E.m_informa(f)
        v1 = E.veredicto(E.evaluar_filas(f, [], vara="NO DETIENE"))
        return m["regla_d"] == "EMPEORA" and abs(m["g"] - 0.97) < 1e-6 and v1 == "CUMPLE SIN DAÑO", (m, v1)
    caso("9 X = 0,97 K en todas las alertas: M informa EMPEORA y g = 0,97, el veredicto no cambia", t9)

    def t10():
        a = E.regla_vara("INTERP MAS CERCA", "INTERP MAS CERCA")
        b = E.regla_vara("INTERP MAS CERCA", "MXD03 MAS CERCA")
        c = E.regla_vara("MXD03 MAS CERCA", "MXD03 MAS CERCA")
        return (a, b, c) == ("DETIENE", "SESGO POR SATELITE", "NO DETIENE"), (a, b, c)
    caso("10 vara: X mas lejos con el mismo signo en Terra y Aqua detiene; signos opuestos SESGO POR SATELITE", t10)

    def t11():
        f = base()
        f[4]["brazos"]["X"] = None
        f[4]["pub"]["X"] = 0
        c = E.control_cobertura(f, [(x["vol"], x["dt"]) for x in f])
        return c["none_por_brazo"].get("X") == 1 and c["estado"] == "OK", c
    caso("11 un None solo en X se cuenta en cobertura y no rompe", t11)

    def t12():
        t = datetime(2026, 3, 27, 7, 10)
        lista = [(t + timedelta(seconds=150), {"tipo": "ALERTA_TERMICA", "vrp_mw": 2.0})]
        lista2 = [(t + timedelta(seconds=110), {"tipo": "ALERTA_TERMICA", "vrp_mw": 2.0})]
        return E.pareadas(lista, t) == [] and len(E.pareadas(lista2, t)) == 1, (E.pareadas(lista, t),)
    caso("12 una alerta pareada a 150 s no entra (pareo 120 s)", t12)

    # ---- pruebas agregadas tras el verificador (VMX-03): fijan el camino que main() usa de verdad
    def t13():
        return E.regla_p2(3, [5] + [1] * 19, True) == "PIERDE", E.regla_p2(3, [5] + [1] * 19, True)
    caso("13 el ruido de P2 es el SEGUNDO mayor |dR| (no el maximo): +3 contra [5, 1 x 19] PIERDE", t13)

    def t14():
        f = base()
        f[1]["pub"]["X"] = 0                       # X apaga la bajo 1 MW que K publica
        return E.p2(f)["delta_x"] == 1, E.p2(f)["delta_x"]
    caso("14 el saldo de P2 cuenta las bajo 1 MW que el brazo deja sin publicar", t14)

    def t15():
        m = {e: E.vara_desde_estado(e) for e in ("INTERP MAS CERCA", "INTERP MAS CERCA SIN CONTROL DE SESGO",
                                                  "SESGO POR SATELITE", "MXD03 MAS CERCA", "SIN VARA", "INDECIDIBLE")}
        esp = {"INTERP MAS CERCA": "DETIENE", "INTERP MAS CERCA SIN CONTROL DE SESGO": "DETIENE SIN CONTROL DE SESGO",
               "SESGO POR SATELITE": "SESGO POR SATELITE", "MXD03 MAS CERCA": "NO DETIENE", "SIN VARA": "NO DETIENE",
               "INDECIDIBLE": "NO DETIENE"}
        return m == esp, m
    caso("15 vara_desde_estado (la que usa main) mapea los estados de evaluar_sola", t15)

    def t16():
        f = base()
        a = E.veredicto(E.evaluar_filas(f, [], vara=None))
        b = E.veredicto(E.evaluar_filas(f, [], vara="DETIENE SIN CONTROL DE SESGO"))
        c = E.veredicto(E.evaluar_filas(f, [], vara="NO DETIENE", externos={"geometria": {"estado": "INDECIDIBLE"}}))
        d = E.veredicto(E.evaluar_filas(f, [], vara="DETIENE"))
        return (a, b, c, d) == ("PENDIENTE DE LA VARA", "DECIDE NICOLÁS", "INDECIDIBLE", "DETENIDO POR LA VARA"), (a, b, c, d)
    caso("16 veredicto: sin vara PENDIENTE; vara sin control DECIDE NICOLAS; control externo rojo INDECIDIBLE", t16)

    def t17():
        f = [x for x in base() if x["lab"] != "protegida"]
        f.append(fila(lab="protegida", dt="2026-07-01 07:10", pub_k=1, pub_x=1, vrp_k=1.2, vrp_x=0.9, vrp_m=1.5))
        return (len(E.p1b(f)) == 1 and E.veredicto(E.evaluar_filas(f, [], vara="NO DETIENE")) == "DECIDE NICOLÁS",
                E.p1b(f))
    caso("17 P1b: protegida que cruza bajo 1 MW se lista y manda a Nicolas", t17)

    def t18():
        f = base()
        f[0]["nulos"][3]["km_aplicado"] = 2.02
        g = base()
        g[0]["hash_grilla"] = {"K": "a", "X": "a", **{b: "r%d" % k for k, b in enumerate(NULOS)}}
        return (E.control_r_modulo(f)["estado"] == "INDECIDIBLE" and E.control_r_modulo(base())["estado"] == "OK"
                and E.control_cableado(g)["estado"] == "INDECIDIBLE"), (E.control_r_modulo(f), E.control_cableado(g))
    caso("18 controles 2 y 8: modulo aplicado a 20 m del pedido e hash de X igual al de K dan INDECIDIBLE", t18)

    def t19():
        f = base()
        sin = E.control_geometria(f)["estado"]
        f[0]["control_s151"] = {"obs_hacia_sensor_km": 2.58}
        bien = E.control_geometria(f)["estado"]
        f[0]["control_s151"] = {"obs_hacia_sensor_km": 2.70}
        mal = E.control_geometria(f)["estado"]
        return (sin, bien, mal) == ("INDECIDIBLE", "OK", "INDECIDIBLE"), (sin, bien, mal)
    caso("19 control 1: sin granulo S151 o fuera de 2,581 +- 0,05 km da INDECIDIBLE", t19)

    def t20():
        f = base()
        return (E.control_duplicados(f + [dict(f[3])])["estado"] == "INDECIDIBLE"
                and E.control_duplicados(f)["estado"] == "OK"), E.control_duplicados(f + [dict(f[3])])
    caso("20 una pasada repetida (humo y tanda en la misma carpeta) da INDECIDIBLE", t20)

    def t21():
        pobf = {("Lascar", "2026-03-27 07:10"): {"lab": "protegida", "z": 20.0, "partida": False, "vrp_mirova": 1.5}}
        igual = {"granulos": [{"records": [dict(vol="Lascar", dt="2026-03-27 07:10", lab="protegida", z=20.0,
                                                 partida=False, vrp_mirova=1.5)]}]}
        otra = {"granulos": [{"records": [dict(vol="Lascar", dt="2026-03-27 07:10", lab="bajo1", z=20.0,
                                                partida=False, vrp_mirova=0.5)]}]}
        return (E.control_reetiquetado(pobf, igual)["estado"] == "OK"
                and E.control_reetiquetado(pobf, otra)["estado"] == "INDECIDIBLE"), E.control_reetiquetado(pobf, otra)
    caso("21 re-etiquetado desde la referencia: una etiqueta distinta da INDECIDIBLE", t21)

    def t22():
        f = base()
        f.append(fila(lab="bajo1", dt="2026-05-03 07:05", pub_k=1, pub_x=0, partida=True, hermanos=("sin_info",),
                      vrp_k=0.2, vrp_m=0.4))
        f.append(fila(lab="neg_limpio", dt="2026-05-04 07:05", pub_k=0, pub_x=1, partida=True, hermanos=("neg_limpio",)))
        r, p6 = E.p2(f), E.p6(f)
        return (r["delta_x"] == 2 and {x["dt"] for x in p6} >= {"2026-05-03 07:05", "2026-05-04 07:05"}), (r["delta_x"], p6)
    caso("22 una bajo 1 MW partida si entra a P2 y P6 lista todas las partidas que cambian", t22)
    return res


# ------------------------------------------------------------------ mutaciones del evaluador
def mutaciones(E):
    def ruido_de_k2(dr):
        return 0          # el ruido sale de K2: 0 por construccion
    real_filas_p2 = E.filas_p2

    def todo_el_cenit(filas):
        return [f for f in real_filas_p2([dict(f, z=min(f["z"], 35.0)) for f in filas])]
    real_p1 = E.p1

    def veto_absuelto(filas):
        r = real_p1(filas)
        r["perdidas"] = [p for p in r["perdidas"] if p["fragilidad"] < 10]
        r["estado"] = "VETADO" if r["perdidas"] else "SIN PERDIDA"
        return r
    real_ver = E.veredicto

    def m_bloquea(res):
        if res.get("m", {}).get("regla_d") == "EMPEORA":
            return "NO CUMPLE"
        return real_ver(res)
    return (("ruido de P2 tomado de K2", patch.object(E, "ruido_p2", ruido_de_k2)),
            ("P2 decidido sobre todo el cenit", patch.object(E, "filas_p2", todo_el_cenit)),
            ("veto absuelto por R", patch.object(E, "p1", veto_absuelto)),
            ("M bloqueando", patch.object(E, "veredicto", m_bloquea)),
            ("pareo a 300 s", patch.object(E, "TOL_S", 300)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modulo", default="evaluar_mxd03")
    ap.add_argument("--mutaciones", action="store_true")
    a = ap.parse_args()
    E = importlib.import_module(a.modulo)
    res = pruebas(E)
    for n, ok, d in res:
        print(("PASA " if ok else "FALLA") + " | " + n + ("" if ok else " | " + str(d)[:300]))
    n_ok = sum(ok for _, ok, _ in res)
    print("pruebas: %d de %d pasan con %s" % (n_ok, len(res), a.modulo))
    if a.mutaciones:
        atrapadas = 0
        for nombre, parche in mutaciones(E):
            with parche:
                r = pruebas(E)
            caidas = [n for n, ok, d in r if not ok and str(d).startswith("EXCEPCION")]
            fallan = [n for n, ok, d in r if not ok and not str(d).startswith("EXCEPCION")]
            atrapada = bool(fallan)
            atrapadas += atrapada
            print("MUTACION %-35s %s%s" % (nombre, "ATRAPADA por: " + "; ".join(x[:2] for x in fallan) if atrapada
                                          else "NO ATRAPADA", " (caidas: %d)" % len(caidas) if caidas else ""))
        print("mutaciones atrapadas por asercion: %d de 5" % atrapadas)
        sys.exit(0 if (n_ok == len(res) and atrapadas == 5) else 1)
    sys.exit(0 if n_ok == len(res) else 1)


if __name__ == "__main__":
    main()
