# -*- coding: utf-8 -*-
"""S149. La etiqueta neg_limpio exige que NO haya alerta esa noche en ese sensor (banco_paridad.etiquetar).
O sea que una pasada donde MIROVA miro y dijo RUTINA, en una noche con alerta por otra pasada, cae en
sin_info. Aca se separan las sin_info de noches con alerta en: (a) MIROVA tiene fila RUTINA CONS con
VRP 0 para ESA pasada (miro y no vio), (b) no hay fila. La clase (a) es arbitrable por MIROVA."""
import json, sys, io, collections, statistics as st
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev
bp = ev.bp
T = json.loads((AQUI.parent / "_s148_verificador_resultado" / "tabla.json").read_text(encoding="utf-8"))
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"
par = json.loads(ev.PARAMETROS.read_text(encoding="utf-8")); ventana = tuple(par["ventana"])
coords = bp._coords_por_volcan()
filas = ev.cargar_referencia_unificada(ev.CONGELADO / "registro_vrp_consolidado.csv", ev.CONGELADO / "registro_vrp_ocr.csv")
por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana)
def zona(z): return "nadir" if z < 36 else ("medio" if z < 52 else "borde")
rows = []
for k, v in T.items():
    vol, b, dts = k.split("|")
    if b != "VIIRS375" or v[B]["lab"] != "sin_info": continue
    dt = (datetime.strptime(dts, "%Y-%m-%d %H:%M") if len(dts) == 16 else datetime.fromisoformat(dts)).replace(tzinfo=timezone.utc)
    ff = bp.parear(por_vb.get((vol, b), []), dt)
    rut = any(f["tipo"] == "RUTINA" and f["source"] == "CONS" and (f["vrp_mw"] or 0) == 0 for f in ff)
    noche = None
    rows.append(dict(vol=vol, dt=dts, rut=rut, nfilas=len(ff), tipos=sorted({f["tipo"] + "/" + f["source"] for f in ff}),
                     pB=v[B]["pub"], pF=v[F]["pub"], dB=v[B]["disp"] or 0, z=v[B]["z"], dist=v[B]["pc_dist"]))
print("V375 sin_info total:", len(rows))
c = collections.Counter(tuple(r["tipos"]) for r in rows)
print("tipos de fila pareada:", dict(c))
a = [r for r in rows if r["rut"]]
print("\n(a) MIROVA miro ESA pasada y dijo RUTINA con VRP 0 (negativo de pasada en noche con alerta): n", len(a))
print("    control B publica %d (%.1f %%) | brazo F publica %d (%.1f %%)" % (sum(r["pB"] for r in a), 100 * sum(r["pB"] for r in a) / len(a), sum(r["pF"] for r in a), 100 * sum(r["pF"] for r in a) / len(a)))
for zn in ("nadir", "medio", "borde"):
    s = [r for r in a if r["z"] is not None and zona(r["z"]) == zn]
    if s: print("      %-6s n %3d | B %3d (%4.1f %%) | F %3d (%4.1f %%)" % (zn, len(s), sum(r["pB"] for r in s), 100 * sum(r["pB"] for r in s) / len(s), sum(r["pF"] for r in s), 100 * sum(r["pF"] for r in s) / len(s)))
ap = [r for r in a if r["pB"] and not r["pF"]]
print("    apagadas por F dentro de (a):", len(ap), dict(collections.Counter(r["vol"] for r in ap)))
b_ = [r for r in rows if not r["rut"]]
print("\n(b) sin fila RUTINA CONS VRP 0 para esa pasada: n", len(b_), "| B pub", sum(r["pB"] for r in b_), "| F pub", sum(r["pF"] for r in b_),
      "| apagadas", sum(1 for r in b_ if r["pB"] and not r["pF"]))
print("    de (b), sin ninguna fila:", sum(1 for r in b_ if r["nfilas"] == 0), "| con fila de otro tipo:", dict(collections.Counter(tuple(r["tipos"]) for r in b_ if r["nfilas"])))
json.dump(rows, open(AQUI / "sin_info_v375.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
