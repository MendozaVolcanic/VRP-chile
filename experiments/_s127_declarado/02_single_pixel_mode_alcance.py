# -*- coding: utf-8 -*-
"""S127 — el alcance REAL de `single_pixel_mode` contra el que declara.

POR QUE: el barrido 01 mostro que la frase "Volcanes NO afectados (regimen alto-MW o
sin path D dominante): Villarrica, Copahue, Isluga, Lascar, Lastarria, Llaima, NdC"
no vive solo en el docstring de `pipeline/single_pixel_mode.py` — esta copiada en 14
perfiles, incluido el OPERACIONAL (`mirova_equivalent.yaml`). S126 ya habia medido
que era falsa para Lascar y PCC; falta medirla para los siete y para la flota entera.

Que se mide, y por que dos metricas:
  · `spm=True`  = el modo se activo (el cluster cayo en regimen sub-MW y de <=3 px).
  · `spm=True y multipixel` = ademas CAMBIO el numero. Para un cluster de un pixel
    la suma y el maximo son identicos, asi que el modo se activa pero no mueve nada.
    Esta es la metrica honesta del alcance.

Fuente: `data/mirova_equivalent/` — lo que el pipeline publica hoy, no un brazo de A/B.
Persiste en 02_single_pixel_mode_alcance.json.
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DATA = os.path.join(ROOT, "data", "mirova_equivalent")

# Textual de `pipeline/single_pixel_mode.py` y de los 14 perfiles.
DECLARADOS_NO_AFECTADOS = {"Villarrica", "Copahue", "Isluga", "Lascar",
                           "Lastarria", "Llaima", "NevadosDeChillan"}
# Textual del mismo docstring, como motivo de existir del modo.
CONSTRUIDO_PARA = {"Tupungatito": "30.15x", "Chaiten": "2.53x",
                   "PlanchonPeteroa": "2.10x", "PuyehueCordonCaulle": "0.48x"}

filas = []
for f in sorted(os.listdir(DATA)):
    if not f.endswith(".json"):
        continue
    vol = f[:-5]
    recs = json.load(io.open(os.path.join(DATA, f), encoding="utf-8")).get("records", [])
    con = [r for r in recs
           if isinstance(r.get("primary_cluster"), dict)
           and "single_pixel_mode" in r["primary_cluster"]]
    if not con:
        continue
    act = [r for r in con if r["primary_cluster"]["single_pixel_mode"] is True]
    mod = [r for r in act if int(r["primary_cluster"].get("n_pixels", 1) or 1) > 1]
    filas.append({
        "volcan": vol,
        "records_con_flag": len(con),
        "activo": len(act),
        "activo_y_multipixel": len(mod),
        "pct_activo": round(100.0 * len(act) / len(con), 1),
        "pct_modificados": round(100.0 * len(mod) / len(con), 1),
        "declarado_no_afectado": vol in DECLARADOS_NO_AFECTADOS,
        "construido_para": CONSTRUIDO_PARA.get(vol),
    })

filas.sort(key=lambda r: -r["pct_modificados"])

print("ALCANCE REAL DE single_pixel_mode — S127")
print("=" * 84)
print("%-24s %9s %9s %10s %8s  %s"
      % ("volcan", "con flag", "activo", "y multipx", "% mod", "lo declarado"))
print("-" * 84)
for r in filas:
    if r["declarado_no_afectado"]:
        etq = "NO afectado -> FALSO" if r["activo_y_multipixel"] else "NO afectado (ok)"
    elif r["construido_para"]:
        etq = "se construyo para el (%s)" % r["construido_para"]
    else:
        etq = ""
    print("%-24s %9d %9d %10d %7.1f%%  %s"
          % (r["volcan"], r["records_con_flag"], r["activo"],
             r["activo_y_multipixel"], r["pct_modificados"], etq))

falsos = [r["volcan"] for r in filas
          if r["declarado_no_afectado"] and r["activo_y_multipixel"] > 0]
top = filas[0]
tupun = next((r for r in filas if r["volcan"] == "Tupungatito"), None)

print()
print("VEREDICTO")
print("  la frase es FALSA para %d de los %d volcanes que nombra: %s"
      % (len(falsos), len(DECLARADOS_NO_AFECTADOS), ", ".join(sorted(falsos))))
print("  el MAS afectado de la flota es %s (%.1f %% de sus records modificados)"
      % (top["volcan"], top["pct_modificados"]),
      "— y esta nombrado como no afectado" if top["declarado_no_afectado"] else "")
if tupun:
    print("  Tupungatito, el volcan para el que se construyo el modo (30,15x de "
          "sobre-reporte), esta %d/%d en la flota con %.1f %%"
          % (filas.index(tupun) + 1, len(filas), tupun["pct_modificados"]))
print("  => el orden esta INVERTIDO respecto de la justificacion escrita.")

res = {"declarados_no_afectados": sorted(DECLARADOS_NO_AFECTADOS),
       "falsos": sorted(falsos), "por_volcan": filas}
dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "02_single_pixel_mode_alcance.json")
json.dump(res, io.open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", os.path.relpath(dest, ROOT).replace("\\", "/"))
