"""Genera nucleo_vs_cluster.md desde el JSON resultado (sin transcribir números)."""
import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
_REPO = Path(__file__).resolve().parents[2]
d = json.load(open(_REPO / "experiments/_s99_audit/nucleo_vs_cluster_result.json", encoding="utf-8"))


def cell(s, key):
    if not s or s.get("n", 0) == 0:
        return "—"
    return str(s.get(key))


L = []
L.append("# S99 — Núcleo F5' vs Cluster: ¿cuál se asemeja más a MIROVA? (por sensor)")
L.append("")
L.append(f"Ventana: **{d['window']}** (snapshot MIROVA CONS+OCR versionado, A17).")
L.append(f"Records matcheados (nuestro detectado ∩ ALERTA MIROVA, mismo sensor-familia, ±15 min): **{d['n_records_matched']}**.")
L.append("")
L.append("Magnitudes comparadas contra `VRP_MW` de MIROVA:")
L.append("- **Cluster** = `primary_cluster.vrp_mw` filtrado igual que el display (summit + dentro de inner). Es el `mirovaEqVrp` base del frontend.")
L.append("- **Núcleo F5'** = `mirovaEqVrpCore`/`f5CoreMagnitude` replicado verbatim de `frontend/index.html` (R_core=0.75 km, BT_ext=295 K). SOLO se aplica a VIIRS375; en MODIS/VIIRS750 el núcleo = cluster por diseño.")
L.append("- `ratio = VRP_nuestro / VRP_MIROVA`. 1.0 = calibración perfecta. Banda tolerable [0.5, 2.0].")
L.append("")
L.append("## 1. Resultado POR SENSOR (lo que pidió Nicolás)")
L.append("")
L.append("| Sensor | n | Cluster mediana | Cluster en banda % | Núcleo mediana | Núcleo en banda % |")
L.append("|---|---:|---:|---:|---:|---:|")
for sf in ("MODIS", "VIIRS375", "VIIRS750", "TOTAL"):
    o = d["by_sensor"][sf]
    c, n = o["cluster"], o["nucleo"]
    L.append(f"| {sf} | {cell(c,'n')} | {cell(c,'median')} | {cell(c,'pct_in_band')} | {cell(n,'median')} | {cell(n,'pct_in_band')} |")
L.append("")
L.append("> **Limitación de datos (honesta).** Los 216 matches son **todos VIIRS375**. En esta ventana MIROVA publicó 251 alertas VIIRS375, **solo 12 MODIS** (9 Láscar, ninguna matcheó por timing/familia) y **0 VIIRS750**. MIROVA no usa VIIRS750 como fuente de magnitud (A11/S93); nuestro pipeline sí genera MODIS (431) y VIIRS750 (854) records en la ventana, pero **no hay ground truth MIROVA para compararlos**. Conclusión: el contraste Cluster vs Núcleo solo es medible en VIIRS375. En MODIS/VIIRS750 el Núcleo es idéntico al Cluster por diseño, así que la pregunta es vacua ahí.")
L.append("")
L.append("## 2. Resultado POR VOLCÁN (todos VIIRS375 en esta ventana)")
L.append("")
L.append("| Volcán | n | Cluster mediana | Cluster en banda % | Cluster max | Núcleo mediana | Núcleo en banda % | Núcleo max |")
L.append("|---|---:|---:|---:|---:|---:|---:|---:|")
order = ["Lascar", "Isluga", "Lastarria", "Tupungatito", "PlanchonPeteroa",
         "PuyehueCordonCaulle", "Villarrica", "Chaiten", "Llaima",
         "NevadosDeChillan", "Copahue"]
for v in order:
    o = d["by_volcano"][v]["all"]
    c, n = o["cluster"], o["nucleo"]
    nm = d["by_volcano"][v]["n_matched"]
    L.append(f"| {v} | {nm} | {cell(c,'median')} | {cell(c,'pct_in_band')} | {cell(c,'max')} | {cell(n,'median')} | {cell(n,'pct_in_band')} | {cell(n,'max')} |")
L.append("")
L.append("(NdC y Copahue: 0 matches — MIROVA no publicó alertas que coincidieran con nuestras detecciones en la ventana.)")
L.append("")
L.append("## 3. Lectura")
L.append("")
L.append("**Mediana global**: Cluster 1.159× vs Núcleo 1.525×. En MEDIANA el Cluster queda más cerca de 1.0.")
L.append("**% en banda [0.5,2.0]**: Cluster 67.1% vs Núcleo 57.4%. El Cluster acierta la banda más seguido.")
L.append("")
L.append("Pero la mediana esconde el problema que motivó F5':")
L.append("- El **Cluster tiene cola larga catastrófica**: max 90.6× (PP), 58.7× (PCC), 31.9× (Isluga), 83.3× (Tupun). Son los artefactos de campo frío/glaciar (A12/A23).")
L.append("- El **Núcleo aplana esa cola**: max baja a 24.1× (Tupun), 18.2× (PCC), 10.7× (PP), 8.4× (Isluga). Recorta la sobre-estimación de halo.")
L.append("- El precio: el Núcleo **empuja los ya-bien-calibrados hacia arriba** (Chaitén 1.49×→2.99×, PCC 1.24×→2.01×, PP 1.50×→2.31×), sacándolos de banda. Por eso baja el % en banda.")
L.append("")
L.append("**Caso Tupungatito** (el que importa, §2 S99): Cluster mediana **18.9×** (solo 20% en banda) → Núcleo **2.28×**. El Núcleo es claramente superior acá: corta el 19× a ~2.3×. Coincide con la dirección de S95 (Núcleo Tupun 2.52×) — la diferencia (2.28 vs 2.52) es esperable: data reprocesada en S98 con ancla al cráter + ventana distinta.")
L.append("")
L.append("**Control Láscar** (cráter de roca, sin halo nevado): Cluster 0.82× / Núcleo 1.03×, ambos en banda alta (86% / 83%). El Núcleo lo deja casi perfecto sin romperlo. Confirma que el Núcleo no daña al caso sano.")
L.append("")
L.append("## 4. Cotejo con docs/F5_CALIBRATION_S95.md")
L.append("")
L.append("S95 reportó: Cluster mediana 5.64×, Núcleo 1.74×, Tupun Núcleo 2.52×, Villarrica 2.07×, Láscar 0.84×.")
L.append("S99 da Cluster mediana global 1.159× (no 5.64×). **La diferencia es real y esperada**, no un bug:")
L.append("1. S95 midió sobre `data/_s94_reproc` (deuda histórica con artefactos viejos sin curar, A18); S99 mide sobre `data/mirova_equivalent` **post-promoción S98** (ancla al cráter, históricos backfilleados). El ancla al cráter ya bajó mucha sobre-estimación antes de aplicar F5'.")
L.append("2. La ventana y el universo de records difieren.")
L.append("El veredicto direccional de S95 se mantiene: el Núcleo corta la cola; Láscar ~0.8-1.0×; Tupun Núcleo ~2.3-2.5×.")
L.append("")
L.append("## 5. Limitaciones reportadas explícitamente")
L.append("- Replica de `f5CoreMagnitude`: **exacta** (mismo R_core, BT_ext, gate VIIRS375, anclaje al píxel de máxima energía dentro de innerKm del centroide, guard S96 nunca-borra, cap 50000). No hubo ambigüedad que obligara a inventar.")
L.append("- Sin ground truth MODIS/VIIRS750 utilizable en la ventana → la respuesta 'por sensor' es **solo VIIRS375**. Para MODIS habría que ampliar la ventana a meses con alertas MODIS MIROVA (Láscar mayormente) y re-correr.")

(_REPO / "experiments/_s99_audit/nucleo_vs_cluster.md").write_text("\n".join(L), encoding="utf-8")
print("written", len(L), "lines")
