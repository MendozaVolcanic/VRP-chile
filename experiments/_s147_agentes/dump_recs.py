# -*- coding: utf-8 -*-
import json, sys, collections
from pathlib import Path
ROOT = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT/"scripts"))
sys.path.insert(0, str(ROOT/"experiments"/"_s146_ab_sin_test1"))
import banco_paridad as bp
from evaluar import cargar_brazo, anotar_vrp_mirova
from referencia_mirova_unificada import cargar_referencia_unificada
ventana=("2026-09-01","2026-09-20")
coords=bp._coords_por_volcan(); inner=bp.inner_desde_html()
filas=cargar_referencia_unificada(ROOT/"experiments/_s145_paridad/_dl_referencia/registro_vrp_consolidado.csv",
                                  ROOT/"experiments/_s145_paridad/_dl_referencia/registro_vrp_ocr.csv")
por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana)
recs=cargar_brazo(str(ROOT/"data"/"mirova_equivalent"), coords, inner, ventana)
bp.etiquetar(recs, por_vb, ns, nv)
anotar_vrp_mirova(recs, por_vb)
out=[{k:(v.strftime("%Y-%m-%d %H:%M") if k=="dt" else v) for k,v in r.items()} for r in recs]
Path(sys.argv[1]).write_text(json.dumps(out), encoding="utf-8")
print("records", len(recs), "n_ref", n_ref)
print("neg_limpio por sensor:", collections.Counter(r["b"] for r in recs if r["lab"]=="neg_limpio"))
print("pos por sensor:", collections.Counter(r["b"] for r in recs if r["lab"]=="pos"))
print("records por fecha (ultimos):", sorted(collections.Counter(r["noche"] for r in recs).items())[-4:])
