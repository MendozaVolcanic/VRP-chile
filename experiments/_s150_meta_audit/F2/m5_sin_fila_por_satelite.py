# -*- coding: utf-8 -*-
"""F2 M5. "14 de las 16 sin fila son SNPP" (memoria S149). Cuenta la plataforma de las 50 apagadas por F en
noches con alerta (S148, 2026-09-01 a 09-20, post #535) por veredicto de MIROVA. Lee las tablas de S148/S149.
Pregunta 2: si el campo sensor estuviera vacio, saldria 'None' en todas (instrumento muerto visible)."""
import json, collections, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
T = json.load(open('_s148_verificador_resultado/tabla.json', encoding='utf-8'))
S = {(r['vol'], r['dt']): r for r in json.load(open('_s149_costo_oculto/sin_info_v375.json', encoding='utf-8'))}
B = "_s146_ab_sin_test1"
npos = {(k.split("|")[0], k.split("|")[2][:10]) for k, v in T.items() if v[B]["lab"] == "pos"}
c = collections.Counter()
for (v, d), r in S.items():
    if (v, d[:10]) not in npos or not r["pB"] or r["pF"]: continue
    sen = T["%s|VIIRS375|%s" % (v, d)][B]["sensor"]
    c[("RUTINA" if r["rut"] else "sin_fila", sen)] += 1
for k, n in sorted(c.items()): print(k, n)
print("total", sum(c.values()))
