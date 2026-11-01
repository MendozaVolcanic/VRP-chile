"""03b: por que los 10 brazos no publican las 6. La publicacion del port la decide el record sintetico de evaluar.py
(regla «cercano»: distancia del alertado mas cercano al crater; «centroide» informa) y el predicado del tablero. Aca se
usa la MISMA funcion `evaluar.dist_regla` sobre los pixeles «fisica» del runner guardados en 03_evidencia_por_pasada.json.
Pregunta 1: si el port tuviera un alertado dentro del inner, la distancia «cercano» saldria <= inner y la clase «summit».
Pregunta 2: control positivo = las 29 protegidas de la tabla del lote (03), cuyo «cercano» tiene que caer dentro del inner.
"""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ / "experiments/_s162_v375"))
import evaluar as E
ev = json.loads((AQUI / "03_evidencia_por_pasada.json").read_text(encoding="utf-8"))
OBJ = {o["id"]: o for o in json.loads((RAIZ / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8"))}
print("id  volcan        hora              inner  cercano_km  centroide_km  clase_cercano  clase_centroide  vrp_port  vrp_mirova")
for i, f in ev.items():
    o = OBJ[int(i)]
    p = {"pixeles": f["port_runner"]["pixeles"], "npix": f["port_runner"]["npix"], "vrp_mw": f["port_runner"]["vrp"]}
    dc = E.dist_regla(p, o["grilla"], "cercano"); dd = E.dist_regla(p, o["grilla"], "centroide")
    rc = E.record_sintetico(p, o["grilla"], f["inner_km"], o["sensor"], "cercano")
    rd = E.record_sintetico(p, o["grilla"], f["inner_km"], o["sensor"], "centroide")
    print(f"{i}  {f['volcan']:12s} {f['hora']}  {f['inner_km']:>4}   {dc:9.2f}   {dd:11.2f}   {rc['distance_class']:12s}   "
          f"{rd['distance_class']:14s}   {f['port_runner']['vrp']:6.3f}    {f['mirova_ocr'][0]['vrp']}")
print("\ncontrol positivo (protegidas de la tabla del lote S159 con grilla, regla cercano):")
import numpy as np
ART = Path(r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945")
res = {}
for fjs in sorted(ART.glob("s159-portes-VIIRS375-*/resultados_VIIRS375_*.json")):
    for r in json.loads(fjs.read_text(encoding="utf-8")):
        res[r["id"]] = r
n_ok = n = 0
for oid, o in sorted(OBJ.items()):
    if o.get("clase") == "pos_prot" and o.get("alerta_tabla") and o["b"] == "VIIRS375" and oid in res and res[oid]["estado"] == "ok":
        fis = res[oid]["port"]["fisica"]
        if not fis["npix"]:
            continue
        n += 1
        n_ok += int(E.record_sintetico(fis, o["grilla"], E.volcanes()[o["volcan"]]["inner_radius_km"], o["sensor"], "cercano")["distance_class"] == "summit")
print(f"  summit con la regla cercano: {n_ok} de {n}")
assert n and n_ok == n, "control positivo FALLA"
