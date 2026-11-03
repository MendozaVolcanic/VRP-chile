# -*- coding: utf-8 -*-
"""04 (S173): escribe la lista de pasadas para el workflow (experiments/_s173_cenit_modis/pasadas_chillan_modis.json de
la rama) desde 01_salida.json. Los números salen de 01 (s02 de S172 sobre origin/main), no se transcriben.
Agrega la razón del brazo V de la lectura del A/B de MOD-D (modd_resultado_f4.json) donde existe, para el control V.
Uso: python -B 04_lista_para_workflow.py <ruta destino> <commit de main medido>"""
import json, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent
dst, commit = Path(sys.argv[1]), sys.argv[2]
pas = json.load(open(AQUI / "01_salida.json", encoding="utf-8"))["pasadas"]
md = json.load(open(AQUI / "modd_resultado_f4.json", encoding="utf-8"))["chillan"]
rb = {p["dt"]: p["razon_b"] for p in md["pares"]}
rb.update({p["dt"]: p["razon"] for p in md["recuperadas"]})
campos = ("dt", "sensor", "z", "vrp_mirova_mw", "fuente_M", "pub_K", "disp_mw", "razon", "granule", "product_version",
          "via_codigo_mirova", "codigo_sha")
out = {"origen": f"01_pasadas_y_salidas_existentes.py sobre origin/main {commit}; alerta = lectura A con D-9 SN, "
                 "pareo +-120 s (s02 de S172); cenit = sensor_zenith_deg del record",
       "pasadas": [{**{k: p[k] for k in campos}, "razon_V_lectura_ab": rb.get(p["dt"])} for p in pas]}
dst.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{len(out['pasadas'])} pasadas escritas en {dst}; con razón V de la lectura: {sum(p['razon_V_lectura_ab'] is not None for p in out['pasadas'])}")
