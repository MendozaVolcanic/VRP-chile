# -*- coding: utf-8 -*-
"""Lectura del humo de MOD-D fase 4 (S170, run 41164864021, tag s170-modd-f4-candado) contra lo que el §11 pide del
humo: cobertura de la lista, gránulos pedidos por nombre (otro_granulo), tiempo por pasada, control K = producción,
marca de la vía, publicación por brazo y versiones del runner. La identidad se lee aparte con identidad_f4.py.
Uso: python leer_humo_f4.py <carpeta del artefacto de la parte> <identidad.json>  (escribe a stdout)
"""
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")
art, idn = Path(sys.argv[1]), json.load(open(sys.argv[2], encoding="utf-8"))
L = [json.loads(x) for x in open(art / "f4_parte_humo.jsonl", encoding="utf-8")]
cab = [r for r in L if r.get("tipo") == "cabecera"]
rec = [r for r in L if r.get("tipo") == "record"]
lista = [ln.split("#")[0].strip() for ln in open(RAIZ / "experiments/_s166_modd_f4/humo_f4.txt", encoding="utf-8")]
lista = {tuple(x.split("|")) for x in lista if x}
claves = Counter((r["vol"], r["dt"]) for r in rec)
print("cabeceras:", len(cab), "| commit", cab[0]["commit"][:9], "| tag", cab[0]["tag"], "| ref", cab[0]["ref"])
print("versiones del runner:", json.dumps(cab[0]["versiones"], ensure_ascii=False))
print("flags:", json.dumps(cab[0]["flags"], ensure_ascii=False))
print("cobertura: lista %d, filas %d, faltan %s, sobran %s, repetidas %s" % (
    len(lista), len(rec), sorted(lista - set(claves)), sorted(set(claves) - lista),
    sorted(k for k, n in claves.items() if n > 1)))
print("estado:", dict(Counter(r["estado"] for r in rec)), "| motivo:", dict(Counter(str(r["motivo"]) for r in rec)))
print("marca de la vía (v_marca):", dict(Counter(str(r["v_marca"]) for r in rec)))
print("otro_granulo:", sum(1 for r in rec if r.get("otro_granulo")), "de", len(rec),
      [(r["vol"], r["dt"]) for r in rec if r.get("otro_granulo")])
print("pidió por nombre y usó el mismo L1B/MxD03:", sum(1 for r in rec if r["l1b_pedido"] == r["l1b_usado"]
                                                       and r["geo_pedido"] == r["geo_usado"]), "de", len(rec))
kd = Counter(str(r.get("k_difiere_de_guardado")) for r in rec)
print("K = producción: k_difiere_de_guardado", dict(kd), "| difiere y reproducida en su sha:",
      sum(1 for r in rec if r.get("k_difiere_de_guardado") and r.get("k_reproducida_en_su_sha")),
      "| difiere sin reproducir:", [(r["vol"], r["dt"]) for r in rec
                                    if r.get("k_difiere_de_guardado") and not r.get("k_reproducida_en_su_sha")],
      "| sin record guardado (k_guardado vacío):", sum(1 for r in rec if not r.get("k_guardado")))
print("pub_runner con K:", sum(1 for r in rec if "K" in (r.get("pub_runner") or {})), "de", len(rec))
seg = [r["segundos"] for r in rec if r.get("segundos") is not None]
print("segundos por pasada: n %d, mediana %.2f, media %.2f, máx %.2f, suma %.1f" % (
    len(seg), statistics.median(seg), statistics.mean(seg), max(seg), sum(seg)))
print("cenit: fuente", dict(Counter(str(r.get("z_fuente")) for r in rec)))
for r in sorted(rec, key=lambda r: (r["vol"], r["dt"])):
    k, v = r.get("k_slim") or {}, r.get("v_slim") or {}
    print("  %-20s %s %-6s motivo=%-24s marca=%-5s K %.3f %s | V %.3f %s | alertadas %s" % (
        r["vol"], r["dt"], r["estado"], r["motivo"], r["v_marca"], k.get("vrp_mw") or 0, k.get("distance_class"),
        v.get("vrp_mw") or 0, v.get("distance_class"), r.get("n_alertadas")))
p = idn["pasadas"]
print("identidad: %d pasadas medidas; mismo gránulo %d; misma máscara %d; |dvrp| <= 0,001 MW %d; misma clase %d" % (
    len(p), sum(x["mismo_granulo"] for x in p), sum(bool(x["misma_mascara"]) for x in p),
    sum(abs(x["dvrp"]) <= 1e-3 for x in p if x.get("dvrp") is not None), sum(bool(x["misma_clase"]) for x in p)))
print("identidad distintas:", [(x["vol"], x["dt"], x.get("dvrp"), x.get("misma_mascara"), x.get("misma_clase"))
                               for x in p if not (x["mismo_granulo"] and x["misma_mascara"] and x["misma_clase"]
                                                  and abs(x["dvrp"]) <= 1e-3)])
md = [x.get("max_dif_radiancia") for x in p if x.get("max_dif_radiancia") is not None]
print("máxima diferencia de radiancia runner contra censo: máx %s" % (max(md) if md else None))

# Costo de t1, t2 y t3 (estimado desde el humo): pasadas por parte con la partición del arnés (--de 24) por la mediana
# de segundos por pasada del humo, más lo que el job probe del humo gastó fuera de las pasadas (instalación, descarga
# del MxD03, prueba previa). Las 8 partes de cada tanda corren en paralelo (max-parallel 8): la tanda dura su parte
# más larga. La prueba previa corre una vez por tanda antes del probe.
from datetime import datetime as _dt
pob = json.load(open(RAIZ / "experiments/_s166_modd_f4/poblacion_f4.json", encoding="utf-8"))["pasadas"]
run = json.load(open(Path(__file__).resolve().parent / "humo_run_41164864021.json", encoding="utf-8"))
dur = {j["name"]: (_dt.fromisoformat(j["completedAt"].rstrip("Z")) - _dt.fromisoformat(j["startedAt"].rstrip("Z")))
       .total_seconds() / 60 for j in run["jobs"]}
fijo = dur["probe (0)"] - sum(seg) / 60
por_parte = -(-len(pob) // 24)
m = por_parte * statistics.median(seg) / 60
print("jobs del humo (min):", {k: round(v, 1) for k, v in dur.items()})
print("t1/t2/t3: %d pasadas, %d por parte; parte ~%.1f min de pasadas + %.1f min fijos; tanda ~%.0f min con la "
      "prueba previa (%.1f min), sin colas del runner ni re-corridas en su sha" % (
          len(pob), por_parte, m, fijo, dur["prueba"] + m + fijo, dur["prueba"]))
