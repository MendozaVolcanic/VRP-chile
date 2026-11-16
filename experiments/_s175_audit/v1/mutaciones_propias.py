#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V1 (S175): mutaciones propias sobre scripts/vigilancia_guardia_modis.py (root_base), por otro camino que el auditor.

V0 (control, tiene que dar VERDE como el commiteado).
V2d: la vía deja de escribir en Chaitén desde el 2026-11-04 SIN reponer K (es lo que hace el código real cuando
     calcular_vrp_granulo devuelve None: process_modis.py:657-658 no cae a K). Si la frescura por volcán funciona,
     tiene que dar VIGILANCIA_CIEGA (pregunta 2: control positivo del aviso de frescura).
V2e: la vía cae a K («geo_distinta», marca alcanzable desde run_pipeline) en NevadosDeChillan, todos sus records de
     la vía; el resto sigue. Pregunta 1: si la vigilancia viera el detector por volcán, avisaría. Además se lee
     duracion.protegidas_vistas_en_guardia: si sigue contando la protegida de Chillán del 2026-11-05 (que ahora es K
     contra K), el plazo de 29 avanza con pasadas en que la vía no corrió.
Uso: python mutaciones_propias.py <root_base> <hoy>
"""
import json, os, shutil, sys
from pathlib import Path
ROOT, HOY = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, ROOT)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp
import vigilancia_guardia_modis as vgm
MUT = Path(r"C:/Users/nmend/vrp-temporales/s175_audit/v1/mut_propias")
P0, G0 = Path(ROOT) / "data" / "mirova_equivalent", Path(ROOT) / "data" / "guardia_k_modis"

def preparar():
    if MUT.exists():
        shutil.rmtree(MUT)
    (MUT / "prod").mkdir(parents=True); (MUT / "guardia").mkdir(parents=True)
    for v in bp.VOLS:
        shutil.copy(P0 / f"{v}.json", MUT / "prod" / f"{v}.json")
        shutil.copy(G0 / f"{v}.json", MUT / "guardia" / f"{v}.json")

def correr():
    vgm.PRODUCCION = str(MUT / "prod"); vgm.GUARDIA = str(MUT / "guardia"); bp.DATA = MUT / "prod"
    o = vgm.evaluar(HOY)
    return {"veredicto": o["veredicto"], "avisos": o["avisos"], "encendido": o["encendido_modis_utc"],
            "reversion": [(p["volcano"], p["fecha_utc"]) for p in o["reversion"]],
            "sin_record": [(p["volcano"], p["fecha_utc"]) for p in o["protegidas_sin_record_produccion"]],
            "vistas": o["duracion"]["protegidas_vistas_en_guardia"],
            "borde_171_01": o["borde_171_01"]["por_semana"]}

def editar(vol, fn):
    p = MUT / "prod" / f"{vol}.json"
    j = json.load(open(p, encoding="utf-8")); n = fn(j); json.dump(j, open(p, "w", encoding="utf-8")); return n

res = {}
preparar(); res["V0_sin_mutar"] = correr()

preparar()
def quitar(j):
    antes = len(j["records"])
    j["records"] = [r for r in j["records"] if not (r.get("via_codigo_mirova") is True
                                                     and str(r.get("datetime_utc"))[:10] >= "2026-11-04")]
    return antes - len(j["records"])
n = editar("Chaiten", quitar)
res[f"V2d_via_deja_de_escribir_Chaiten_desde_2026-11-04 ({n} records quitados, sin reponer)"] = correr()

preparar()
def caer(j):
    n = 0
    for r in j["records"]:
        if r.get("via_codigo_mirova") is True:
            r["via_codigo_mirova"] = "geo_distinta"; n += 1
    return n
n = editar("NevadosDeChillan", caer)
res[f"V2e_via_cae_a_K_geo_distinta_NevadosDeChillan ({n} records)"] = correr()
shutil.rmtree(MUT)
print(json.dumps(res, indent=1, ensure_ascii=False))
