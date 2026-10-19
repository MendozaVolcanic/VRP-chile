"""Que habria dicho la vigilancia si el retrospectivo (K reprocesado, sombra desde 2026-10-02) fuera prospectivo.
Mide el comportamiento real de (i), (ii) y (iii) con K tal como es. Uso: python ... <raiz> <ref>"""
import os, sys, json
from collections import Counter
raiz, ref = sys.argv[1:3]
sys.path.insert(0, raiz); sys.path.insert(0, os.path.join(raiz, "scripts"))
import scripts.vigilancia_sombra as vs
vs.aa.CONS = os.path.join(ref, "registro_vrp_consolidado.csv"); vs.aa.OCR = os.path.join(ref, "registro_vrp_ocr.csv")
hoy = "2026-10-19"; win = (vs.aa.leer_frontera_k(), hoy)
filas, prod, sombra = vs.cargar_insumos(win)
print("prod lab != lab_original:", sum(r["lab"] != r["lab_original"] for r in prod), "de", len(prod),
      Counter((r["lab_original"], r["lab"]) for r in prod if r["lab"] != r["lab_original"]))
pas = vs.pasadas_de_alerta(filas, prod, sombra, win)
print("pasadas minimas:", sum(p["minima"] for p in pas), "| minimas con los dos records:", sum(p["minima"] and p["prod_pub"] is not None and p["sombra_pub"] is not None for p in pas))
for corte in ("2026-10-02 00:00:00",):
    d = vs.disparadores(pas, prod, hoy, corte)
    print("corte", corte, "veredicto", d["veredicto"])
    for k, m in d["muy_bajo"].items():
        print("   muy_bajo", k, m)
    print("   persistencia", d["persistencia"]); print("   negativos", d["negativos_VIIRS375"])
    print("   reversion", [(p["volcano"], p["sensor"], p["fecha_utc"]) for p in d["reversion"]])
    mb = [p for p in pas if p["instante_utc"] >= corte and not p["protegida"] and p["prod_pub"] is not None and p["sombra_pub"] is not None]
    print("   (i) perdidas detalle:", [(p["volcano"], p["sensor"], p["fecha_utc"], p["vrp_mirova_mw"], p["minima"]) for p in mb if p["sombra_pub"] and not p["prod_pub"]])
    # misma cuenta sin minimas (lectura D-9 SN)
    sn = Counter(); 
    for p in mb:
        if p["minima"]: continue
        c = sn.setdefault((p["volcano"], p["sensor"]), [0, 0]); c[1] += 1; c[0] += bool(p["sombra_pub"] and not p["prod_pub"])
    print("   (i) con SN:", {f"{k[0]}|{k[1]}": v for k, v in sn.items() if k[1] == "VIIRS375"})
