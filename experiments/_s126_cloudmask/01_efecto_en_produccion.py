# -*- coding: utf-8 -*-
"""S126 — cuanto cambio la produccion cuando el PR #535 apago la mascara de nube.

El comentario de process_viirs.py afirmaba que el cambio era "NO-OP en produccion"
porque mirova_equivalent.yaml fijaria cloud_mask_bt_k: 260.0. Ese YAML declara 0.0
desde S29 y #535 no lo toco, asi que la mascara de VIIRS375 quedo APAGADA en vivo.

Este script mide el efecto sobre la data operacional partiendo los records por el
timestamp del merge. El indicador es `diag_n_bg_used_first_pass`: los pixeles que
sobrevivieron para estimar el fondo. Con la mascara encendida, en las noches de
nieve a altura el filtro descartaba el ROI entero y ese contador caia a 0 — la
"noche ciega", donde el record dice "sin senal" cuando en realidad no se miro.

LIMITACION DECLARADA: al correrlo hay pocas horas de data post-merge, asi que el
n del grupo POST es chico (2-4 pasadas por volcan). La MAGNITUD de la mediana no
es robusta con ese n; lo que si es inequivoco es la desaparicion del minimo en 0,
porque un solo record con fondo no-nulo en una noche que antes cegaba ya lo
prueba. Por eso el script reporta n, mediana Y minimo, y no solo la mediana.

Persiste en 01_efecto_en_produccion.json.
"""
import io, json, os, statistics as st, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")

# merge de https://github.com/MendozaVolcanic/VRP-chile/pull/535
CORTE = "2026-08-28T23:00"
DESDE = "2026-08-10"          # ventana previa comparable, no toda la historia
VOLS = ["NevadosDeChillan", "Villarrica", "Lascar", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]


def resumen(xs):
    if not xs:
        return None
    return {"n": len(xs), "mediana": round(st.median(xs)), "min": min(xs),
            "max": max(xs), "noches_ciegas": sum(1 for x in xs if x == 0)}


res = {"corte_utc": CORTE, "ventana_desde": DESDE, "pr": 535,
       "indicador": "diag_n_bg_used_first_pass", "por_volcan": {}}

print("EFECTO DEL PR #535 EN PRODUCCION — mascara de nube de VIIRS375")
print("corte: %s (merge)   ventana previa desde %s\n" % (CORTE, DESDE))
print("%-22s %-6s %5s %10s %8s %14s" %
      ("volcan", "grupo", "n", "mediana", "min", "noches ciegas"))

for vol in VOLS:
    path = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    if not os.path.exists(path):
        print("%-22s (sin archivo)" % vol)
        continue
    recs = json.load(open(path, encoding="utf-8"))["records"]
    pre, post = [], []
    for r in recs:
        s = (r.get("sensor") or "").upper()
        if "VIIRS" not in s or "750" in s or "MODIS" in s:
            continue
        dt = r["datetime_utc"].replace(" ", "T")
        if dt[:10] < DESDE:
            continue
        nbg = r.get("diag_n_bg_used_first_pass")
        if nbg is None:
            continue
        (post if dt >= CORTE else pre).append(int(nbg))
    d = {"pre_535": resumen(pre), "post_535": resumen(post)}
    res["por_volcan"][vol] = d
    for g, k in (("pre", "pre_535"), ("POST", "post_535")):
        e = d[k]
        if e:
            print("%-22s %-6s %5d %10d %8d %14d"
                  % (vol if g == "pre" else "", g, e["n"], e["mediana"],
                     e["min"], e["noches_ciegas"]))

print("\nLECTURA")
tot_pre = sum((d["pre_535"] or {}).get("noches_ciegas", 0) for d in res["por_volcan"].values())
tot_post = sum((d["post_535"] or {}).get("noches_ciegas", 0) for d in res["por_volcan"].values())
res["noches_ciegas_totales"] = {"pre": tot_pre, "post": tot_post}
print("  noches ciegas (fondo = 0 pixeles): %d antes del merge, %d despues"
      % (tot_pre, tot_post))
print("  OJO: el n del grupo POST es chico; la mediana no es robusta, la")
print("  desaparicion del minimo en 0 si lo es.")

dest = os.path.join(os.path.dirname(__file__), "01_efecto_en_produccion.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
