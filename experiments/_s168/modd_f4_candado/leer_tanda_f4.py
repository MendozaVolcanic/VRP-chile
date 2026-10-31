# -*- coding: utf-8 -*-
"""Lectura de una tanda de MOD-D fase 4 (t1, t2 o t3) contra lo que el §11 pide antes de seguir: por parte, cobertura
contra la partición del arnés (probe_f4.pasadas_de_la_parte, la misma que corrió el runner), estado y motivo, gránulos
por nombre (otro_granulo), K = producción, marca de la vía, versiones de cada cabecera, tiempo, y la identidad de las
pasadas con grilla del censo. No es el veredicto del A/B: ése se lee con evaluar_f4 cuando estén las tres tandas.
Uso: python leer_tanda_f4.py <carpeta de la tanda> <identidad.json> <parte> [<parte> ...]
"""
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "experiments/_s166_modd_f4"))
sys.stdout.reconfigure(encoding="utf-8")
import probe_f4  # noqa: E402

tanda, idn, partes = Path(sys.argv[1]), json.load(open(sys.argv[2], encoding="utf-8")), [int(x) for x in sys.argv[3:]]
pob = json.load(open(RAIZ / "experiments/_s166_modd_f4/poblacion_f4.json", encoding="utf-8"))
todas, versiones, commits = [], set(), set()
for parte in partes:
    arch = sorted(tanda.glob("*-parte-%d/f4_parte*.jsonl" % parte))
    L = [json.loads(x) for a in arch for x in open(a, encoding="utf-8")]
    cab = [r for r in L if r.get("tipo") == "cabecera"]
    rec = [r for r in L if r.get("tipo") == "record"]
    esperadas = {(p["vol"], p["dt"]) for g in probe_f4.pasadas_de_la_parte(pob, parte, 24).values() for p in g}
    claves = Counter((r["vol"], r["dt"]) for r in rec)
    for c in cab:
        versiones.add(json.dumps(c.get("versiones"), sort_keys=True))
        commits.add((c.get("commit"), c.get("ref")))
    seg = [r["segundos"] for r in rec if r.get("segundos") is not None]
    print("parte %2d: cabeceras %d | esperadas %d filas %d | faltan %d sobran %d repetidas %d | estado %s | motivo %s | "
          "marca %s | otro_granulo %d | k_difiere %s | pub_runner K %d | s/pasada mediana %.2f máx %.2f" % (
              parte, len(cab), len(esperadas), len(rec), len(esperadas - set(claves)), len(set(claves) - esperadas),
              sum(1 for n in claves.values() if n > 1), dict(Counter(r["estado"] for r in rec)),
              dict(Counter(str(r["motivo"]) for r in rec)), dict(Counter(str(r["v_marca"]) for r in rec)),
              sum(1 for r in rec if r.get("otro_granulo")), dict(Counter(str(r.get("k_difiere_de_guardado")) for r in rec)),
              sum(1 for r in rec if "K" in (r.get("pub_runner") or {})), statistics.median(seg) if seg else 0,
              max(seg) if seg else 0))
    todas += rec
print("commits y refs de las cabeceras:", sorted(commits))
print("versiones distintas entre cabeceras:", len(versiones), sorted(versiones))
r = todas
print("TOTAL: %d filas | estado %s | motivo %s | marca %s | otro_granulo %d | k_difiere verdadero %d (reproducidas en su "
      "sha %d, sin reproducir %s) | sin record guardado %d" % (
          len(r), dict(Counter(x["estado"] for x in r)), dict(Counter(str(x["motivo"]) for x in r)),
          dict(Counter(str(x["v_marca"]) for x in r)), sum(1 for x in r if x.get("otro_granulo")),
          sum(1 for x in r if x.get("k_difiere_de_guardado")),
          sum(1 for x in r if x.get("k_difiere_de_guardado") and x.get("k_reproducida_en_su_sha")),
          [(x["vol"], x["dt"]) for x in r if x.get("k_difiere_de_guardado") and not x.get("k_reproducida_en_su_sha")],
          sum(1 for x in r if not x.get("k_guardado"))))
sel = [p for p in pob["pasadas"] if (p["vol"], p["dt"]) in {(x["vol"], x["dt"]) for x in r}]
sellado_con_grilla = [(p["vol"], p["dt"]) for p in sel if p.get("grilla_censo")
                      and next(x for x in r if (x["vol"], x["dt"]) == (p["vol"], p["dt"]))["motivo"] is not None]
print("con grilla del censo en la tanda: %d | con grilla y motivo sellado (N-01): %s" % (
    sum(1 for p in sel if p.get("grilla_censo")), sellado_con_grilla))
p = idn["pasadas"]
mal = [(x["vol"], x["dt"]) for x in p if not (x["mismo_granulo"] and x["misma_mascara"] and x["misma_clase"]
                                             and abs(x["dvrp"]) <= 1e-3)]
print("identidad: %d medidas, %d iguales, distintas %s" % (len(p), len(p) - len(mal), mal[:20]))
