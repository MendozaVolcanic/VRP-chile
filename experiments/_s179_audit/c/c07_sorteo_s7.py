# -*- coding: utf-8 -*-
"""Frente C, auditoria S179. Instrumento c07: el sorteo de etiquetas del §7 con la lectura que Nicolas aprobo en S174.

POR QUE. El §7 sellado pide, antes de leer, barajar las etiquetas de MIROVA dentro de cada estrato (volcan x tramo de
10 grados de cenit) y ver que fraccion de barajados cumple «GANA o EMPATE» por azar. El lector lo corre con K contra K,
que da B = 0 siempre (SIN PODER). Nicolas aprobo el 2026-11-05 (decision 2 del bloque S174) leerlo con la via contra K;
la lectura de S178 no lo hizo. Aqui se corre: P2 de la via (radiante) contra K con las etiquetas barajadas.

QUE DICE EL RESULTADO. Si con etiquetas al azar la via «gana» seguido, P2 GANA no distingue una via que acierta donde
MIROVA alerta de una via que solo publica menos que K (los negativos limpios son muchos mas que las alertas debiles).

LAS DOS PREGUNTAS. (1) Si P2 premiara solo el silencio, esto lo ve: GANA apareceria en mas del 5 % de los barajados.
(2) Instrumento muerto: control positivo, sin barajar tiene que reproducir B y neto de c03 (se imprime); control
negativo, K contra K barajado tiene que dar B = 0 siempre.

Uso: python c07_sorteo_s7.py TABLA.json [N]
"""
import collections, json, sys
import numpy as np
sys.path.insert(0, ".")
from c03_lectura_propia import DECIDE, p2
sys.stdout.reconfigure(encoding="utf-8")
tabla = json.load(open(sys.argv[1], encoding="utf-8"))
N = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
for s, tr in DECIDE.items():
    ev = [f for f in tabla if f["b"] == s and f["tramo"] == tr and f["estado"] == "ok"]
    e, B, neto = p2(ev)[:3]
    print(f"\n{s} ({tr}; {len(ev)} pasadas evaluables). Observado (sin barajar): {e}, B {B}, neto {neto}")
    labs = [f["lab"] for f in ev]
    for nom, clave in (("volcan x tramo de 10 grados de cenit (el del §7)", lambda f: (f["vol"], None if f["z"] is None else int(float(f["z"]) // 10))),
                       ("volcan x plataforma x tramo de cenit", lambda f: (f["vol"], f["sensor"], None if f["z"] is None else int(float(f["z"]) // 10))),
                       ("todo el sensor (sin estratos)", lambda f: 0)):
        estr = collections.defaultdict(list)
        for i, f in enumerate(ev):
            estr[clave(f)].append(i)
        rng = np.random.default_rng(172)
        cuenta, netos, kk = collections.Counter(), [], 0
        for _ in range(N):
            nuevo = list(labs)
            for idx in estr.values():
                perm = rng.permutation(len(idx))
                for dst, src in zip(idx, perm):
                    nuevo[dst] = labs[idx[src]]
            bar = [dict(f, lab=l) for f, l in zip(ev, nuevo)]
            r = p2(bar)
            cuenta[r[0]] += 1
            netos.append(r[2])
            kk += p2(bar, a="pub_K")[1]
        netos = np.array(netos)
        print(f"  barajado en {nom}: {N} sorteos, {len(estr)} estratos -> {dict(sorted(cuenta.items()))}")
        print(f"     GANA por azar {100 * cuenta['GANA'] / N:.1f} %; GANA o EMPATE por azar {100 * (cuenta['GANA'] + cuenta['EMPATE']) / N:.1f} %; "
              f"neto barajado: mediana {np.median(netos):.0f}, p5 {np.percentile(netos, 5):.0f}, p95 {np.percentile(netos, 95):.0f}; "
              f"sorteos con neto <= observado ({neto}): {int((netos <= neto).sum())} de {N}; control K contra K: suma de B {kk}")
