"""Verificador: de donde salen las protegidas que cuenta ritmo_protegidas.py (fuente CONS/OCR, mes, volcan)
y cuantas contaria la unidad del vigilante (pasada de MIROVA con record nuestro a +-120 s)."""
import collections, io, sys, json
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path.cwd(); sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp
import clase_mirova as cm
ventana = (sys.argv[1], sys.argv[2])
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = bp.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
print("MODO_MINIMAS =", bp.MODO_MINIMAS, "| filas ref:", len(filas), "| tipos:", collections.Counter(f["tipo"] for f in filas).most_common())
print("fuentes:", collections.Counter(f.get("source") for f in filas))
print("ultima fila ref:", max(f["fecha_utc"] for f in filas))
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana, regla_minimas=bp.MODO_MINIMAS)
recs = bp.cargar_nuestros(coords, inner, ventana)
bp.etiquetar(recs, por_vb, ns, nv)
prot = collections.defaultdict(list)
for r in recs:
    if r["lab"] != "pos": continue
    fp = [f for f in bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"]) if bp.es_alerta(f["tipo"])]
    if fp and max((f["vrp_mw"] or 0) for f in fp) >= 1.0:
        fuentes = {f.get("source") for f in fp if (f["vrp_mw"] or 0) >= 1.0}
        r["_fuentes"] = "+".join(sorted(fuentes)); r["_vmax"] = max((f["vrp_mw"] or 0) for f in fp)
        r["_claves"] = {cm.clave_pasada(f) for f in fp if (f["vrp_mw"] or 0) >= 1.0}
        prot[r["b"]].append(r)
for s in sorted(prot):
    L = prot[s]
    print(f"\n== {s}: {len(L)} records protegidos (unidad del instrumento)")
    print("   por fuente de las filas >=1 MW:", dict(collections.Counter(r["_fuentes"] for r in L)))
    print("   solo OCR por volcan:", dict(collections.Counter(r["vol"] for r in L if r["_fuentes"] == "OCR")))
    # unidad vigilante: pasadas MIROVA distintas
    claves = set().union(*[r["_claves"] for r in L])
    print("   pasadas MIROVA distintas (clave_pasada) detras de esos records:", len(claves))
    # records distintos que comparten una misma pasada MIROVA
    cnt = collections.Counter(k for r in L for k in r["_claves"])
    print("   pasadas MIROVA pareadas por mas de un record:", sum(1 for k, v in cnt.items() if v > 1))
    pm = collections.defaultdict(collections.Counter)
    for r in L: pm[r["vol"]][r["noche"][:7]] += 1
    for v in sorted(pm, key=lambda v: -sum(pm[v].values())):
        print(f"   {v:22s}", dict(sorted(pm[v].items())))
    ch = [r for r in L if r["vol"] == "NevadosDeChillan"]
    if ch:
        print("   Chillan: primera", ch[0]["dt"], "ultima", ch[-1]["dt"], "| por semana desde sept:",
              dict(sorted(collections.Counter(r["dt"].strftime("%G-W%V") for r in ch if r["noche"] >= "2026-09-01").items())))
        print("   Chillan vrp MIROVA min/mediana/max desde 2026-10-15:",
              (lambda x: (min(x), sorted(x)[len(x)//2], max(x)) if x else None)([r["_vmax"] for r in ch if r["noche"] >= "2026-10-15"]))
# unidad del vigilante completa: pasadas MIROVA protegidas nocturnas (lectura A) con y sin record nuestro
diurna = lambda b, vol, dt: bp.es_pasada_diurna_descartada(b, coords[vol][0], coords[vol][1], dt)
por_pasada = collections.defaultdict(list)
for f in filas:
    if f.get("tipo") in cm.TIPOS_ALERTA and ventana[0] <= f["fecha_utc"][:10] <= ventana[1]:
        por_pasada[cm.clave_pasada(f)].append(f)
idx = collections.defaultdict(list)
for r in recs: idx[(r["vol"], r["b"])].append(r)
res = collections.defaultdict(lambda: collections.Counter())
for (vol, b, minuto), fs in por_pasada.items():
    dt = datetime.fromisoformat(fs[0]["fecha_utc"][:19]).replace(tzinfo=timezone.utc)
    if diurna(b, vol, dt): continue
    if not any(cm.alerta_protegida(f) for f in fs): continue
    cerca = [r for r in idx.get((vol, b), []) if abs((r["dt"] - dt).total_seconds()) <= 120]
    src = "+".join(sorted({f.get("source") for f in fs if cm.alerta_protegida(f)}))
    res[b][("con_record" if cerca else "sin_record", src)] += 1
print("\n== unidad del vigilante (pasada MIROVA protegida nocturna, lectura A), record = produccion:")
for b in sorted(res): print("  ", b, dict(res[b]))
