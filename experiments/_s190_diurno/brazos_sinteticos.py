# -*- coding: utf-8 -*-
"""Brazo perfecto y brazo ruidoso sintéticos sobre la referencia congelada (S190, ADENDA_VIA.md §5, tercer punto).

POR QUÉ. Antes de despachar hay que ver que la regla puede dar las dos respuestas sobre la estructura real de W2 a W7
(cuántas pasadas, qué volcanes, cuántas protegidas en Chillán y en W7), no sólo en escenas armadas a mano:
  * el brazo PERFECTO publica justo las alertas diurnas de MIROVA (protegidas y bajo 1 MW, con la magnitud de MIROVA)
    y nada más: no puede salir NO ADOPTAR en ningún flag;
  * el brazo RUIDOSO publica todas las pasadas diurnas: no puede salir ADOPTAR en ningún flag.
Los dos con cobertura completa (un record por pasada de MIROVA, de noche idéntico en los dos brazos, de día con
dayflag 1 y ángulos) y el sha del tag sintético. Se usa el evaluador entero (`evaluar_completo`, con la robustez de
S163 §6.4), no una parte.

Uso: python -I experiments/_s190_diurno/brazos_sinteticos.py --ref <referencia congelada> > brazos_sinteticos_salida.txt
Sale con 1 si algún brazo viola su control, con 3 si la referencia no es la del sustrato.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import evaluar_diurno_via as ev  # noqa: E402

SHA = "f" * 40
C, B = "_control_sintetico", "_brazo_sintetico"


def records(pasadas, modo):
    rc, rb = [], []
    for p in pasadas:
        dt = p.instante.replace(tzinfo=None)
        dia = ev.ek.es_dia_vol(p.volcano, dt)
        alerta = p.estado == "alerta"
        if not dia:
            for lado in (rc, rb):
                lado.append({"vol": p.volcano, "b": p.sensor_bucket, "dt": dt, "es_dia": False, "pub": False,
                             "disp": 0.0, "t1": False, "fuente_hotspot": None, "sha": SHA, "via": True,
                             "dayflag": 0, "motivo": None, "soz": 120.0, "huella": "n"})
            continue
        pub = alerta if modo == "perfecto" else True
        disp = (p.vrp_mw or 0.3) if alerta else 0.5
        rb.append({"vol": p.volcano, "b": p.sensor_bucket, "dt": dt, "es_dia": True, "pub": pub,
                   "disp": disp if pub else 0.0, "t1": False, "fuente_hotspot": "codigo_mirova", "sha": SHA,
                   "via": True, "dayflag": 1, "motivo": None, "soz": 50.0, "huella": "d"})
    return {C: rc, B: rb}


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--sustrato", default=str(AQUI / "sustrato_via.json"))
    a = ap.parse_args(argv)
    import sustrato_k as sk
    sus = json.loads(Path(a.sustrato).read_text(encoding="utf-8"))
    ref = Path(a.ref)
    if [n for n in sk.ARCHIVOS_REF if ev.ek.sha256(ref / n) != sus["sha256"][n]]:
        print("REFERENCIA DISTINTA DE LA DEL SUSTRATO")
        return 3
    print("referencia congelada del commit %s; sha256 %s" % (sus["commit_referencia"], sus["sha256"]))
    filas = sk.cargar_ref(ref)
    ventanas = [(w[0], w[1], w[2]) for w in ev.sv.VENTANAS]
    p_sup = ev.p_sup_de_vara(sus["vara_cobertura_nocturna_produccion"])
    pas_u = ev.pasadas_de(filas, "union", ventanas)
    print("pasadas de MIROVA W2 a W7 (unión): %d, diurnas %d" % (
        len(pas_u), sum(1 for p in pas_u if ev.ek.es_dia_vol(p.volcano, p.instante))))
    fallas = []
    for modo, prohibido in (("perfecto", ev.NO_ADOPTAR), ("ruidoso", ev.ADOPTAR)):
        r = ev.evaluar_completo(filas, records(pas_u, modo), C, B, p_sup, SHA, ventanas, (), ev.ek._filas_1_13())
        p = r["principal"]
        print("\n=== brazo %s" % modo)
        print("compuertas: inválido %s | indecidible %s" % (p["compuertas"]["invalido"][:5],
                                                             p["compuertas"]["indecidible"][:5]))
        for s, m in p["por_sensor"].items():
            print("  %s: protegidas %d de %d | alertas<1MW %d de %d | negativos publicados %d de %d | neto %+d | P2 %s | "
                  "D %s | base %s (caso %s) | sin Chillán %s | sin W7 %s | M5 %s | M8 %d -> %s %s"
                  % (s, m["P"], m["P_obs"], m["amb_recuperadas"], m["amb_obs"], m["neg_pub"], m["neg_obs"], m["neto"],
                     m["p2"], m["D"], m["base"], m["caso"], m["sin_chillan"], m["sin_W7"], m["M5"], m["M8"]["n_1mw"],
                     m["veredicto"], m["motivos"]))
        print("flags principal: %s" % p["flags"])
        print("variantes: %s" % r["variantes"])
        print("final: %s" % r["final"])
        for flag, (v, motivo) in r["final"].items():
            if v == prohibido:
                fallas.append("%s: %s salió %s (%s)" % (modo, flag, v, motivo))
    print()
    if fallas:
        print("CONTROL FALLIDO:", fallas)
        return 1
    print("controles de los brazos sintéticos: OK (el perfecto no sale NO ADOPTAR; el ruidoso no sale ADOPTAR)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
