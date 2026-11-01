# -*- coding: utf-8 -*-
"""S159 frente N, paso 6: lista del censo que cierra cuántos negativos limpios enciende F (aprobado por Nicolás el
2026-10-21: «los 60 cúmulos de cumbre en 0 MW, los 59 far e Isluga 10-12»).

POR QUÉ UN CENSO. F no cambia la detección (mismo hot_mask y mismo cúmulo que K en 391 de 391, verificador v3), así
que sólo puede encender un negativo donde K ya tiene un cúmulo que no publica. En la población eso son 60 negativos
con cúmulo de cumbre en 0,0 MW y 59 con cúmulo `far` (verificador v3 y v5); los 5.303 restantes no tienen ningún
píxel alertado. Contarlos todos reemplaza al estimador ponderado, que el sorteo infló (6 elegibles de 140 en la
muestra contra 60 de 5.476 en la población).

Definiciones (las del verificador, `verificador/v3_estimador_elegibles.py` y `v5_far.py`), sobre
poblacion_completa.json sin el 2026-10-18 ni el 19:
  cumbre_0mw  lab == neg_limpio, pub_prod falso, dc == summit, pc_vrp == 0,0
  far         lab == neg_limpio, pub_prod falso, dc == far
  isluga_1012 Isluga 2026-10-12 05:48 (la única pasada de Isluga ese día en la población: alerta de MIROVA, cúmulo
              de cumbre en 0,0 MW, SIN DATO en el lote). No es ambigua.
  reintento_1012  Chillán 2026-10-12 05:18 (protegida) y 05:54: las otras dos SIN DATO del mismo día. Agregadas como
              reintento declarado; no entran al conteo de negativos.
Grilla del oráculo: la misma de 02_seleccion.py (esquina de GEO).
"""
import collections
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
import importlib.util
spec = importlib.util.spec_from_file_location("sel", AQUI / "02_seleccion.py")
SEL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SEL)

pob = [p for p in json.loads((AQUI / "poblacion_completa.json").read_text(encoding="utf-8"))["pasadas"]
       if p["hora_utc"][:10] not in SEL.EXCLUIDOS]
G = SEL.grillas()
out = []
for p in pob:
    k = None
    if p["lab"] == "neg_limpio" and not p["pub_prod"] and p.get("dc") == "summit" and p.get("pc_vrp") == 0.0:
        k = "cumbre_0mw"
    elif p["lab"] == "neg_limpio" and not p["pub_prod"] and p.get("dc") == "far":
        k = "far"
    elif (p["volcan"], p["hora_utc"]) == ("Isluga", "2026-10-12 05:48"):
        k = "isluga_1012"
    elif (p["volcan"], p["hora_utc"]) in (("NevadosDeChillan", "2026-10-12 05:18"), ("NevadosDeChillan", "2026-10-12 05:54")):
        k = "reintento_1012"
    if k:
        out.append({**p, "clase": k, "peso": 1.0, "grilla": G[SEL.TIF.get(p["volcan"], p["volcan"])]})
out.sort(key=lambda e: (e["granule"] or "", e["volcan"]))
for n, e in enumerate(out):
    e["id"] = 1000 + n
c = collections.Counter(e["clase"] for e in out)
print("censo:", dict(c), "| total", len(out), "| granulos unicos", len({e["granule"] for e in out}))
print("por volcan y clase:", dict(sorted(collections.Counter((e["volcan"], e["clase"]) for e in out).items())))
assert c["cumbre_0mw"] == 60 and c["far"] == 59 and c["isluga_1012"] == 1, "no reproduce los conteos del verificador"
(AQUI / "objetivos_censo.json").write_text(json.dumps(out, ensure_ascii=False, indent=0, default=str), encoding="utf-8")
print("escrito objetivos_censo.json")
