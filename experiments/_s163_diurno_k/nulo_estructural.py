# -*- coding: utf-8 -*-
"""Nulo medido de la regla del A/B diurno sobre K, antes de despachar (PREREGISTRO.md §5.1, A110).

POR QUÉ. Una regla que nunca se corrió sobre un caso donde la respuesta se conoce no se sabe si mide lo que dice. Aquí
la respuesta se conoce porque el brazo es sintético: sobre la estructura REAL de W2 a W6 (las pasadas de MIROVA de la
referencia congelada y los records nocturnos de producción, que es K desde #883 y hace de control), el brazo diurno
publica cada pasada diurna VIIRS al azar con probabilidad q, sin mirar si es alerta o negativo. Un detector así no
discrimina nada, así que la regla no debería adoptarlo:
  (i)  P2 diurno da GANA en no más del 5 % de las repeticiones;
  (ii) el veredicto por sensor da ADOPTAR en no más del 5 % (con e-i, la opción recomendada, y con e-ii);
  (iii) control positivo: un brazo que publica exactamente las alertas diurnas de MIROVA y nada más da ADOPTAR en
        VIIRS 375 y en VIIRS 750;
  (iv) control negativo: un brazo que publica todas las pasadas diurnas da NO ADOPTAR en los dos sensores.
Si (i), (iii) o (iv) fallan, el instrumento no sirve. (ii) por encima de 5 % se informa como debilidad de la regla.

Uso: python -I experiments/_s163_diurno_k/nulo_estructural.py --ref <carpeta congelada> > experiments/_s163_diurno_k/nulo_estructural_salida.txt
"""
from __future__ import annotations

import argparse
import collections
import os
import random
import sys
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
for _p in (str(ROOT), str(ROOT / "scripts"), str(AQUI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import clase_mirova as cm  # noqa: E402
import evaluador_comun as ec  # noqa: E402
import evaluar_diurno_k as ev  # noqa: E402
import sustrato_k as sk  # noqa: E402

TASAS = (0.005, 0.02, 0.05, 0.2)
REPS = 200
SEMILLA = 163


def armar(ref):
    import banco_paridad as bp
    filas = sk.cargar_ref(ref)
    ventanas = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
    pas = []
    for p in cm.resumir_pasadas(filas, canal="union", regla_minimas=ev.REGLA_MINIMAS):
        d = p.instante.strftime("%Y-%m-%d")
        if p.volcano in ev.coords() and p.sensor_bucket in ev.SENSORES_DIA and any(w[1] <= d <= w[2] for w in ventanas):
            pas.append(p)
    ctrl = ev.cargar_brazo([ROOT / "data"], "mirova_equivalent", ventanas, bp.inner_desde_html())
    ctrl = [r for r in ctrl if r["b"] in ev.SENSORES_DIA and not r["es_dia"]]
    sint = []
    for p in pas:
        if ev.es_dia_vol(p.volcano, p.instante):
            sint.append({"vol": p.volcano, "b": p.sensor_bucket, "dt": p.instante.replace(tzinfo=None), "es_dia": True,
                         "pub": False, "disp": 0.0, "diag_dia": True})
    brazo = [dict(r) for r in ctrl] + sint
    T = ec.tabla_por_pasada(pas, {"ctrl": ctrl, "diurno": brazo}, "ctrl")
    for f in T:
        f["es_dia"] = ev.es_dia_vol(f["pasada"].volcano, f["pasada"].instante)
    ev.banderas_por_periodo(T)
    ev.completar_control_diurno(T, "ctrl", "diurno")
    return T, sint


def veredictos(T, sint):
    out = {}
    for s in ev.SENSORES_DIA:
        m = ev.metricas_sensor(T, sint, "ctrl", "diurno", s)
        out[s] = (m, ev.veredicto_sensor(m, "e-i")[0], ev.veredicto_sensor(m, "e-ii")[0])
    return out


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    a = ap.parse_args(argv)
    T, sint = armar(a.ref)
    ids = {id(r) for r in sint}
    filas_dia = [f for f in T if f["es_dia"] and f["rec"]["diurno"] is not None and id(f["rec"]["diurno"]) in ids]
    print("pasadas: %d; diurnas VIIRS con record sintético: %d" % (len(T), len(sint)))
    for s in ev.SENSORES_DIA:
        c = collections.Counter(("protegida" if f["protegida"] else ec.clase_p2(f)) for f in filas_dia
                                if f["pasada"].sensor_bucket == s)
        print("  %s: %s" % (s, dict(c)))
    prob = []

    # (iii) control positivo y (iv) control negativo
    for nombre, regla in (("positivo (sólo las alertas)", lambda f: f["pasada"].estado == "alerta"),
                          ("negativo (todas las diurnas)", lambda f: True)):
        for r in sint:
            r["pub"], r["disp"] = False, 0.0
        for f in filas_dia:
            if regla(f):
                f["rec"]["diurno"]["pub"], f["rec"]["diurno"]["disp"] = True, 0.3
        v = veredictos(T, sint)
        for s in ev.SENSORES_DIA:
            m, vi, vii = v[s]
            print("control %s %s: P2 %s neto %+d, P %d de %d, Q_d %.4f, Q_n %.4f (de %d negativos nocturnos de "
                  "producción), D %s -> e-i %s / e-ii %s" % (nombre, s, m["p2"], m["neto"], m["P"], m["P_obs"], m["Qd"],
                                                             m["Qn"], m["Qn_den"], m["D"], vi, vii))
            esperado = ev.ADOPTAR if nombre.startswith("positivo") else ev.NO_ADOPTAR
            if vi != esperado:
                prob.append("control %s %s: e-i dio %s, se esperaba %s" % (nombre, s, vi, esperado))

    # (i) y (ii): brazos que publican al azar
    rng = random.Random(SEMILLA)
    for q in TASAS:
        cuenta = {s: collections.Counter() for s in ev.SENSORES_DIA}
        for _ in range(REPS):
            for r in sint:
                pub = rng.random() < q
                r["pub"], r["disp"] = pub, (0.3 if pub else 0.0)
            v = veredictos(T, sint)
            for s in ev.SENSORES_DIA:
                m, vi, vii = v[s]
                cuenta[s]["GANA"] += m["p2"] == "GANA"
                cuenta[s]["ADOPTAR e-i"] += vi == ev.ADOPTAR
                cuenta[s]["ADOPTAR e-ii"] += vii == ev.ADOPTAR
                cuenta[s]["D cumple"] += bool(m["D"])
                cuenta[s]["P>=1"] += m["P"] >= 1
        for s in ev.SENSORES_DIA:
            c = cuenta[s]
            print("azar q=%.3f %s (%d rep): GANA %d, ADOPTAR e-i %d, ADOPTAR e-ii %d, D cumple %d, P>=1 %d"
                  % (q, s, REPS, c["GANA"], c["ADOPTAR e-i"], c["ADOPTAR e-ii"], c["D cumple"], c["P>=1"]))
            if c["GANA"] > 0.05 * REPS:
                prob.append("(i) q=%.3f %s: GANA en %d de %d" % (q, s, c["GANA"], REPS))
            if c["ADOPTAR e-i"] > 0.05 * REPS:
                print("   DEBILIDAD (ii): ADOPTAR con e-i en %d de %d" % (c["ADOPTAR e-i"], REPS))
    if prob:
        print("\nFALLA EL INSTRUMENTO:")
        for x in prob:
            print("  ", x)
        return 1
    print("\n(i), (iii) y (iv): OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
