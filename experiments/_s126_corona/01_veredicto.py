# -*- coding: utf-8 -*-
"""S126 — veredicto del A/B de la corona Eq.6, criterio por criterio.

Escrito ANTES de que el reproceso termine (A16), para que leer el resultado sea
mecanico y no haya margen de acomodar el criterio al numero.

Los 7 criterios estan fijados en docs/S126_CORONA_PREREGISTRO.md y se evaluan tal
cual, sin agregar ni sacar. El punto central: TODO va desagregado por volcan — la
leccion de S126 es que la mediana agrupada invirtio el veredicto del brazo E
(escondia que Planchon pasaba de 0,957 a 6,636).

Si el directorio del 4to brazo existe (_s126_corona_ctxoff), se agrega solo y el
2x2 se completa. Si no, se reporta lo que haya.

Persiste en 01_veredicto.json.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _s126_lib import (ROOT, VENTS, BANDA, bucket, cargar_brazo, cargar_mirova,   # noqa: E402
                       en_banda, haversine, ic95, interseccion, marca,
                       pares_por_noche, resumen)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

VENTANA = ("2026-06-25", "2026-08-24")
BRAZOS = {
    "control": "_s126_corona_off",
    "corona": "_s126_corona_on",
    "ctx_off": "_s125_viirs_e",          # anillo + filtro OFF (ya corrido)
    "corona+ctx_off": "_s126_corona_ctxoff",
}
VOLS = ["Villarrica", "PlanchonPeteroa", "Lascar", "PuyehueCordonCaulle",
        "NevadosDeChillan"]
EVENTO_CANARIO = ("NevadosDeChillan", "2026-06-16")   # A79
CAIDA_MAX_LASCAR = 0.20

mir, diurnas = cargar_mirova(VENTANA)
disp = {n: s for n, s in BRAZOS.items()
        if os.path.isdir(os.path.join(ROOT, "data", s))}
if "control" not in disp or "corona" not in disp:
    print("faltan los brazos minimos (control y corona). Nada que evaluar todavia.")
    sys.exit(0)

print("VEREDICTO DEL A/B DE LA CORONA Eq.6 — %s a %s" % VENTANA)
print("brazos con datos: %s" % ", ".join(disp))
print("alertas diurnas de MIROVA descartadas (A76): %d\n" % diurnas)

datos, pasadas = {}, {}
for nom, sub in disp.items():
    datos[nom], pasadas[nom] = {}, {}
    for vol in VOLS:
        d = cargar_brazo(sub, vol, VENTANA)
        if d is not None:
            datos[nom][vol], pasadas[nom][vol] = d, set(d)

comunes = {vol: interseccion([pasadas[n].get(vol) for n in disp]) for vol in VOLS}

res = {"ventana": list(VENTANA), "brazos": list(disp), "banda": list(BANDA),
       "diurnas_descartadas": diurnas, "por_volcan": {}, "criterios": {}}

# ── ratios por volcan y por brazo ────────────────────────────────────────────
print("RATIO NUESTRO/MIROVA EN VIIRS375, POR VOLCAN")
cab = "%-22s %5s" % ("volcan", "n") + "".join("%16s" % n for n in disp)
print(cab)
for vol in VOLS:
    fila, n_ref = {}, 0
    for nom in disp:
        if vol not in datos[nom]:
            continue
        pares = pares_por_noche(datos[nom][vol], comunes[vol], mir.get(vol), "v375")
        if not pares:
            continue
        rs = [a / b for _, a, b in pares]
        n_ref = max(n_ref, len(rs))
        fila[nom] = {"n": len(rs), "mediana": round(sorted(rs)[len(rs) // 2], 3)
                     if len(rs) % 2 else round(sum(sorted(rs)[len(rs) // 2 - 1:len(rs) // 2 + 1]) / 2, 3),
                     "ic95": ic95(rs), "en_banda": None}
        fila[nom]["en_banda"] = en_banda(fila[nom]["mediana"])
    if not fila:
        print("%-22s %5s   (sin pares)" % (vol, "-"))
        continue
    res["por_volcan"][vol] = fila
    print("%-22s %5d" % (vol, n_ref)
          + "".join(("%14.3f %s" % (fila[n]["mediana"], "✓" if fila[n]["en_banda"] else "✗"))
                    if n in fila else ("%16s" % "-") for n in disp))

# ── criterio 1: volcanes en banda ────────────────────────────────────────────
cuenta = {n: sum(1 for v in res["por_volcan"].values()
                 if n in v and v[n]["en_banda"]) for n in disp}
total = len(res["por_volcan"])
salidos = [v for v, f in res["por_volcan"].items()
           if f.get("control", {}).get("en_banda") and not f.get("corona", {}).get("en_banda")]
c1 = cuenta.get("corona", 0) >= cuenta.get("control", 0) and not salidos
res["criterios"]["1_volcanes_en_banda"] = {
    "por_brazo": {n: "%d/%d" % (cuenta[n], total) for n in disp},
    "salieron_de_banda": salidos, "cumple": c1}

# ── criterio 2: Villarrica tiene que BAJAR ───────────────────────────────────
vi = res["por_volcan"].get("Villarrica", {})
c2 = None
if "control" in vi and "corona" in vi:
    c2 = vi["corona"]["mediana"] < vi["control"]["mediana"]
    res["criterios"]["2_villarrica_baja"] = {
        "control": vi["control"]["mediana"], "corona": vi["corona"]["mediana"],
        "cumple": c2}

# ── criterio 3: Lascar, canario de falso negativo ────────────────────────────
la = res["por_volcan"].get("Lascar", {})
c3 = None
if "control" in la and "corona" in la:
    caida = 1 - (la["corona"]["mediana"] / la["control"]["mediana"]) \
        if la["control"]["mediana"] else None
    det_c = sum(1 for k in comunes["Lascar"]
                if (datos["control"]["Lascar"][k].get("primary_cluster") or {}).get("vrp_mw"))
    det_o = sum(1 for k in comunes["Lascar"]
                if (datos["corona"]["Lascar"][k].get("primary_cluster") or {}).get("vrp_mw"))
    c3 = (caida is not None and caida <= CAIDA_MAX_LASCAR) and det_o >= det_c
    res["criterios"]["3_lascar_canario"] = {
        "caida_magnitud": round(caida, 3) if caida is not None else None,
        "tope": CAIDA_MAX_LASCAR, "detecciones_control": det_c,
        "detecciones_corona": det_o, "cumple": c3}

# ── criterio 4: el evento NdC 06-16 sigue disparando (A79) ───────────────────
vol_c, fecha_c = EVENTO_CANARIO
c4 = None
if vol_c in datos.get("corona", {}):
    def dispara(brazo):
        return any((datos[brazo][vol_c][k].get("primary_cluster") or {}).get("vrp_mw")
                   for k in comunes[vol_c] if k[0][:10] == fecha_c)
    c4 = (not dispara("control")) or dispara("corona")
    res["criterios"]["4_evento_ndc_0616"] = {
        "dispara_control": dispara("control"), "dispara_corona": dispara("corona"),
        "cumple": c4}

# ── criterio 5: cero detecciones perdidas ────────────────────────────────────
perdidas = {}
for vol in VOLS:
    if vol not in datos.get("corona", {}):
        continue
    p = [k for k in comunes[vol]
         if (datos["control"][vol][k].get("primary_cluster") or {}).get("vrp_mw")
         and not (datos["corona"][vol][k].get("primary_cluster") or {}).get("vrp_mw")]
    if p:
        perdidas[vol] = len(p)
c5 = not perdidas
res["criterios"]["5_cero_detecciones_perdidas"] = {"perdidas": perdidas, "cumple": c5}

# ── criterio 6: control interno, MODIS y V750 no se mueven ───────────────────
movidos = {}
for b in ("modis", "v750"):
    for vol in VOLS:
        if vol not in datos.get("corona", {}):
            continue
        pc = pares_por_noche(datos["control"][vol], comunes[vol], mir.get(vol), b)
        po = pares_por_noche(datos["corona"][vol], comunes[vol], mir.get(vol), b)
        if pc != po:
            movidos["%s/%s" % (b, vol)] = "difieren"
c6 = not movidos
res["criterios"]["6_control_interno"] = {"movidos": movidos, "cumple": c6}

# ── criterio 7 (diagnostico): corona degradada ───────────────────────────────
deg = tot = 0
for vol in VOLS:
    if vol not in datos.get("corona", {}):
        continue
    for k in comunes[vol]:
        pc = datos["corona"][vol][k].get("primary_cluster") or {}
        if pc.get("vrp_mw"):
            tot += 1
            if pc.get("corona_degraded"):
                deg += 1
res["criterios"]["7_corona_degradada"] = {
    "records": tot, "degradados": deg,
    "pct": round(100 * deg / tot, 1) if tot else None}

print("\n" + "=" * 78)
print("CRITERIOS PRE-REGISTRADOS (docs/S126_CORONA_PREREGISTRO.md)")
etiquetas = {
    "1_volcanes_en_banda": "1. mas volcanes en banda y ninguno se sale",
    "2_villarrica_baja": "2. Villarrica BAJA la magnitud",
    "3_lascar_canario": "3. Lascar: 0 detecciones perdidas y caida <= 20%",
    "4_evento_ndc_0616": "4. el evento NdC 06-16 sigue disparando (A79)",
    "5_cero_detecciones_perdidas": "5. cero detecciones perdidas en total",
    "6_control_interno": "6. MODIS y V750 no se mueven",
}
fallan = []
for k, txt in etiquetas.items():
    d = res["criterios"].get(k)
    if not d or d.get("cumple") is None:
        print("   %-52s (no evaluable)" % txt)
        continue
    print("   %-52s %s" % (txt, marca(d["cumple"])))
    if not d["cumple"]:
        fallan.append(k)
d7 = res["criterios"]["7_corona_degradada"]
print("   %-52s %s%% (%d de %d) — diagnostico, no criterio"
      % ("7. corona degradada (cae al fondo regional)", d7["pct"], d7["degradados"], d7["records"]))

res["veredicto"] = "ADOPTAR" if not fallan else "NO ADOPTAR"
res["criterios_que_fallan"] = fallan
print("\nVEREDICTO: %s%s" % (res["veredicto"],
                             "" if not fallan else "  (fallan: %s)" % ", ".join(fallan)))
if "3_lascar_canario" in fallan:
    print("\nOJO — que falle el criterio 3 estaba PREVISTO (docs/S126_LASCAR_ES_UN_PIXEL.md):")
    print("  a Lascar le falta un pixel, no fondo, y la corona sola le saca energia sin")
    print("  darselo. Eso NO refuta la corona: refuta la corona SIN el segundo pixel.")
    print("  La celda que contesta eso es corona+ctx_off (_s126_corona_ctxoff).")

dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "01_veredicto.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
