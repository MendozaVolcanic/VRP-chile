# -*- coding: utf-8 -*-
"""S172 proyeccion V375-E: mide, con el MISMO etiquetado y la MISMA clase que el lector sellado
(experiments/_s168/v375e_sombra/leer_sombra_v375e.py, tag s170-v375e-lector), cuantas noches con dato y cuantas
alertas que deciden (pos_prot + pos_bajo) hubo por noche en NOAA-20 y NOAA-21 de VIIRS 375, records de K de origin/main."""
import os, sys, json, collections, importlib.util
from pathlib import Path
AQUI = Path(__file__).resolve().parent
REPO = AQUI / "repo"
os.environ["VRP_PROFILE"] = "mirova_equivalent"
for p in (REPO, REPO / "scripts"):
    sys.path.insert(0, str(p))
import banco_paridad as B
from clase_mirova import alerta_protegida
from referencia_mirova_unificada import cargar_referencia_unificada
spec = importlib.util.spec_from_file_location("lector", REPO / "experiments/_s168/v375e_sombra/leer_sombra_v375e.py")
LEC = importlib.util.module_from_spec(spec); sys.modules["lector"] = LEC; spec.loader.exec_module(LEC)

DESDE, HASTA = sys.argv[1], sys.argv[2]
filas_ref = cargar_referencia_unificada(AQUI/"ref/registro_vrp_consolidado.csv", AQUI/"ref/registro_vrp_ocr.csv",
                                        respaldo_path=None, historico_path=None)
coords, inner = B._coords_por_volcan(), B.inner_desde_html()
por_vb, ns, nv, _ = B.indexar_referencia(filas_ref, coords, (DESDE, HASTA), regla_minimas="SN")
recs = B.cargar_nuestros(coords, inner, (DESDE, HASTA))
B.etiquetar(recs, por_vb, ns, nv)
pob, fuera, snpp = LEC.poblacion(recs, por_vb, B, alerta_protegida)
# detalle: de la tabla (CONS) o solo OCR
out = {"ventana": [DESDE, HASTA], "n_pob": len(pob), "fuera": dict(fuera), "snpp_excluidos": snpp,
       "sensores": dict(collections.Counter(o["sensor"] for o in pob)),
       "clases": dict(collections.Counter(o["clase"] for o in pob)),
       "pob": [{k: o[k] for k in ("volcan","hora_utc","noche","sensor","clase","alerta_tabla","mirova_vrp")} for o in pob]}
json.dump(out, open(AQUI/f"pob_{DESDE}_{HASTA}.json","w"), ensure_ascii=False)
print(out["n_pob"], out["sensores"], out["clases"], out["fuera"], "snpp", snpp)
# etiquetas por noche (todas las clases) para diagnosticar noches sin poblacion
lab = collections.Counter((r["noche"], r["lab"]) for r in recs if r["b"]=="VIIRS375" and r.get("sensor")!="VIIRS_SNPP")
json.dump({f"{k[0]}|{k[1]}": v for k,v in lab.items()}, open(AQUI/"etiquetas_por_noche.json","w"))
