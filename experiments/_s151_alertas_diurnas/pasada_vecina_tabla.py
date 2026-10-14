# -*- coding: utf-8 -*-
"""Tarea 1.13 (estudio C), pregunta 2: la pasada vecina en la TABLA de MIROVA, de dia contra de noche.

EL FENOMENO. Un foco volcanico de 3 a 7 MW no se apaga en veinte minutos. Si una alerta diurna es calor
real en el crater, la pasada siguiente del mismo sensor (otro satelite VIIRS, minutos despues) deberia
verlo tambien. Si es Sol reflejado en una nube o en una ladera con la geometria justa, la pasada siguiente,
con otro angulo de vision, no lo repite.

QUE SE MIDE. Para cada alerta (CONS u OCR, lectura A protegida y tambien todas) se busca la fila de la TABLA
(latest.php, canal CONS) del mismo volcan y sensor mas cercana en el tiempo, excluyendo la propia pasada
(misma hora al minuto), dentro de +-60 min, y se anota su tipo.
Control que puede fallar: el mismo calculo sobre las alertas NOCTURNAS. De noche no hay reflejo; si la
pasada vecina tampoco repite la alerta de noche (por ejemplo, porque el otro satelite mira con mas angulo
y pierde el foco), entonces "la vecina no la repite" no distingue nada de dia.
Salida: pasada_vecina_tabla_salida.txt.
"""
from __future__ import annotations

import io
import json
import os
import sys
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
from clase_mirova import alerta_protegida  # noqa: E402

AQUI = Path(__file__).resolve().parent


def t_min(fecha):
    return datetime.strptime(fecha[:16], "%Y-%m-%d %H:%M").timestamp() / 60.0


def main():
    out = []
    p = out.append
    pob = json.load(open(AQUI / "poblacion_filas.json", encoding="utf-8"))
    tabla = defaultdict(list)
    for f in cargar_referencia_unificada():
        if f["source"] == "CONS":
            tabla[(f["volcano"], f["sensor_bucket"])].append((t_min(f["fecha_utc"]), f["tipo"], f["vrp_mw"] or 0.0))
    for k in tabla:
        tabla[k].sort()

    def vecina(f):
        L = tabla[(f["volcano"], f["sensor_bucket"])]
        ts = [x[0] for x in L]
        t = t_min(f["fecha_utc"])
        cand = [x for x in L[bisect_left(ts, t - 60):bisect_right(ts, t + 60)] if abs(x[0] - t) >= 1]
        if not cand:
            return None
        return min(cand, key=lambda x: abs(x[0] - t)), t

    for luz in ("noche", "dia"):
        for nombre, filtro in (("todas las alertas", lambda f: True),
                               ("protegidas (lectura A)", lambda f: alerta_protegida(f, lectura="A"))):
            fs = [f for f in pob[luz] if filtro(f)]
            c = Counter()
            off = Counter()
            for f in fs:
                r = vecina(f)
                if r is None:
                    c["sin vecina en +-60 min"] += 1
                    continue
                (tv, tipo, v), t = r
                c[tipo if tipo != "ALERTA_TERMICA" else ("ALERTA >= 1 MW" if v >= 1 else "ALERTA < 1 MW")] += 1
                off[round(tv - t)] += 1
            con = sum(n for k, n in c.items() if k != "sin vecina en +-60 min")
            rep = c["ALERTA >= 1 MW"] + c["ALERTA < 1 MW"]
            p("%-5s %-24s n=%4d  vecina en la tabla: %s" % (luz, nombre, len(fs), dict(sorted(c.items()))))
            p("      la vecina repite alerta en %d de %d con vecina (%.1f %%); desfases mas comunes (min): %s"
              % (rep, con, 100.0 * rep / max(con, 1), off.most_common(5)))
        # por volcan, protegidas diurnas
    p("\nDiurnas protegidas: tipo de la pasada vecina en la tabla, por volcan")
    por = defaultdict(Counter)
    for f in pob["dia"]:
        if not alerta_protegida(f, lectura="A"):
            continue
        r = vecina(f)
        if r is None:
            por[f["volcano"]]["sin vecina"] += 1
        else:
            (tv, tipo, v), t = r
            por[f["volcano"]][tipo if tipo != "ALERTA_TERMICA" else "ALERTA"] += 1
    for v in sorted(por):
        p("   %-20s %s" % (v, dict(sorted(por[v].items()))))
    p("\nControl por volcan: TODAS las alertas, tipo de la vecina en la tabla, noche contra dia")
    for luz in ("noche", "dia"):
        por = defaultdict(Counter)
        for f in pob[luz]:
            r = vecina(f)
            if r is None:
                por[f["volcano"]]["sin vecina"] += 1
            else:
                (tv, tipo, v), t = r
                por[f["volcano"]][tipo if tipo != "ALERTA_TERMICA" else "ALERTA"] += 1
        for v in ("Lascar", "Lastarria", "Isluga", "NevadosDeChillan"):
            p("   %-5s %-20s %s" % (luz, v, dict(sorted(por[v].items()))))
    (AQUI / "pasada_vecina_tabla_salida.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
