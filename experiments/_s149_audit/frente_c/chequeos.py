# -*- coding: utf-8 -*-
"""S149, FRENTE C. Dos chequeos de mecanismo, solo lectura.
 (a) VIIRS 750: en las alertas de MIROVA que produccion no publica, el pixel del cumulo es mas FRIO que
     el fondo del anillo (t_bg_k)? Control positivo: las alertas que si publica, donde deberia ser al reves.
 (b) MODIS: la etiqueta far separa alertas de negativos? Se cuenta, en positivos y en negativos limpios,
     cuantas pasadas tienen cumulo con energia dentro del inner (lo que se veria si la etiqueta no ocultara).
P2: toda tasa con su n. Ventana y sensor en cada linea.
"""
import collections, io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev  # noqa: E402
bp = ev.bp
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = ev.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
crudo = {}
for vol in bp.VOLS:
    for r in json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))["records"]:
        crudo[(vol, r.get("sensor"), r.get("datetime_utc"))] = r


def correr(ventana):
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana)
    recs = ev.cargar_brazo(bp.DATA, coords, inner, ventana)
    bp.etiquetar(recs, por_vb, ns, nv); ev.anotar_vrp_mirova(recs, por_vb)
    return recs


print("(a) VIIRS 750, ventana 2026-06-13 a 2026-09-21, alertas de MIROVA con record")
recs = correr(("2026-06-13", "2026-09-21"))
for nombre, sel in (("NO publicadas", [r for r in recs if r["b"] == "VIIRS750" and r["lab"] == "pos" and not r["pub"]]),
                    ("publicadas", [r for r in recs if r["b"] == "VIIRS750" and r["lab"] == "pos" and r["pub"]])):
    frio = n = 0; difs = []
    for r in sel:
        c = crudo[(r["vol"], r["plataforma"], r["dt"].strftime("%Y-%m-%d %H:%M"))]
        px = [p for p in (c.get("anomaly_pixels") or []) if p.get("bt_k") is not None]
        if not px or c.get("t_bg_k") is None:
            continue
        n += 1; m = max(p["bt_k"] for p in px); difs.append(round(m - c["t_bg_k"], 1)); frio += int(m < c["t_bg_k"])
    difs.sort()
    print("   %-14s n %3d | pixel mas caliente del record MAS FRIO que el fondo del anillo: %d | (bt_max_px - t_bg) mediana %s, min %s, max %s" % (
        nombre, n, frio, difs[len(difs) // 2] if difs else None, difs[0] if difs else None, difs[-1] if difs else None))

print("\n(b) MODIS, ventana 2026-03-01 a 2026-08-28 (un solo regimen, anterior a #535), y 2026-08-29 a 2026-09-21")
for ventana in (("2026-03-01", "2026-08-28"), ("2026-08-29", "2026-09-21")):
    recs = correr(ventana)
    for vol in ("Lascar", None):
        for lab in ("pos", "neg_limpio"):
            s = [r for r in recs if r["b"] == "MODIS" and r["lab"] == lab and (vol is None or r["vol"] == vol)]
            dentro = sum(1 for r in s if (r["pc_vrp"] or 0) > 0 and r["pc_dist"] is not None and r["pc_dist"] <= inner[r["vol"]])
            far = sum(1 for r in s if r["dc"] == "far")
            print("   %s | %-7s | %-10s n %4d | publica %4d (%5.1f %%) | cumulo con energia dentro del inner %4d (%5.1f %%) | etiqueta far %4d (%5.1f %%)" % (
                ventana, vol or "los 11", lab, len(s), sum(r["pub"] for r in s), 100 * sum(r["pub"] for r in s) / len(s) if s else float("nan"),
                dentro, 100 * dentro / len(s) if s else float("nan"), far, 100 * far / len(s) if s else float("nan")))
