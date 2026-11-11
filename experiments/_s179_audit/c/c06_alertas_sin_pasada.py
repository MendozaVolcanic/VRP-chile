# -*- coding: utf-8 -*-
"""Frente C, auditoria S179. Instrumento c06: alertas de la tabla de MIROVA sin pasada nuestra, DENTRO de cada tramo.

POR QUE. El §6 (C-cobertura) del pre-registro pide listar toda alerta o bajo 1 MW de la tabla sin pasada nuestra a
+-120 s. El lector la cuenta sobre una sola ventana que va del primer al ultimo dia de las pasadas (2026-02-01 a
2026-10-16), o sea incluye abril a septiembre, donde la prueba no tiene pasadas por construccion. Aqui se cuenta
tramo por tramo. Una alerta sin pasada nuestra no entra a P1 ni a P2 en ningun brazo: es invisible para el veredicto.

VARAS: banco_paridad.indexar_referencia (SN) y clase_mirova.alerta_protegida (lectura A) de main 438a60a1e, sobre la
referencia congelada de la retrospectiva, tabla sola.

LAS DOS PREGUNTAS. (1) Si hubiera protegidas de MIROVA fuera del denominador, esto las ve y las lista. (2) Si el
instrumento estuviera muerto: control positivo, con la lista de pasadas nuestras VACIA todas las alertas del tramo
tienen que salir sin pasada (se imprime el total de alertas nocturnas del tramo).

Uso: python c06_alertas_sin_pasada.py
"""
import bisect, collections, json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
MAIN = Path("D:/vrp-trabajo/temporales/s179-audit/main")
WT = Path("D:/vrp-trabajo/worktrees/s178-lectura")
T = Path("D:/vrp-trabajo/temporales/s179-audit/c")
sys.path.insert(0, str(MAIN / "scripts")); sys.path.insert(0, str(MAIN))
import banco_paridad as bp
import clase_mirova as clase
import referencia_mirova_unificada as rmu
TR = {"F26-M": ("2026-02-01", "2026-02-28", "MODIS"), "F26-V 375": ("2026-02-01", "2026-03-31", "VIIRS375"),
      "F26-V 750": ("2026-02-01", "2026-03-31", "VIIRS750"), "DM MODIS": ("2026-10-01", "2026-10-16", "MODIS"),
      "DM 375": ("2026-10-01", "2026-10-16", "VIIRS375"), "DM 750": ("2026-10-01", "2026-10-16", "VIIRS750")}
coords = bp._coords_por_volcan()
tabla = json.load(open(T / "tabla_tag.json", encoding="utf-8"))
ref = rmu.cargar_referencia_unificada(
    WT / "experiments/_s178_lectura/_congelado/registro_vrp_consolidado.csv",
    WT / "experiments/_s178_lectura/_congelado/registro_vrp_ocr.csv",
    respaldo_path=WT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv",
    historico_path=WT / "data/mirova_reference/union_historica/consolidado_filas_perdidas.csv")
cons = [r for r in ref if r["source"] == "CONS"]
nuestras = collections.defaultdict(list)
for f in tabla:
    nuestras[(f["vol"], f["b"])].append(datetime.strptime(f["dt"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc))
for v in nuestras.values():
    v.sort()
for nom, (a, z, b) in TR.items():
    por_vb, _ns, _nv, _n = bp.indexar_referencia(cons, coords, (a, z), regla_minimas="SN")
    tot = sin = 0
    lista = []
    vistos = set()
    for (vol, bb), filas in por_vb.items():
        if bb != b or (vol == "Tupungatito" and a < "2026-02-23" and False):
            continue
        ts = nuestras.get((vol, b), [])
        for dt, f in filas:
            if not bp.es_alerta(f["tipo"]) or (vol, f["fecha_utc"][:16]) in vistos:
                continue
            if vol == "Tupungatito" and f["fecha_utc"][:10] < "2026-02-23":
                continue
            vistos.add((vol, f["fecha_utc"][:16]))
            tot += 1
            i = bisect.bisect_left(ts, dt - timedelta(seconds=120))
            if not (i < len(ts) and ts[i] <= dt + timedelta(seconds=120)):
                sin += 1
                j = bisect.bisect_left(ts, dt)
                cerca = min([abs((ts[x] - dt).total_seconds()) for x in (j - 1, j) if 0 <= x < len(ts)] or [None])
                lista.append((vol, f["fecha_utc"][:16], f["vrp_mw"], "protegida" if clase.alerta_protegida(f, lectura="A") else "bajo1",
                              f["tipo"], None if cerca is None else round(cerca / 60, 1)))
    prot = [x for x in lista if x[3] == "protegida"]
    print(f"\n{nom} ({a} a {z} UTC, {b}): alertas nocturnas de la tabla (tras SN) {tot}; sin pasada nuestra a +-120 s: {sin} "
          f"(protegidas {len(prot)}, bajo 1 MW {sin - len(prot)}); por volcan {dict(collections.Counter(x[0] for x in lista))}")
    for x in prot[:30]:
        print("    PROTEGIDA sin pasada:", x[0], x[1], x[2], "MW;", x[4], "; pasada nuestra mas cercana a", x[5], "min")
    for x in [y for y in lista if y[3] != "protegida"][:8]:
        print("    bajo 1 MW sin pasada:", x[0], x[1], x[2], "MW;", x[4], "; mas cercana a", x[5], "min")
    print(f"   control positivo: sin pasadas nuestras, saldrian {tot} de {tot}")
