# -*- coding: utf-8 -*-
"""S124 - Que senal honesta de CEGUERA tenemos en el dato ya persistido.

POR QUE: el grafico hoy dibuja "no hubo deteccion" igual que "no pudimos mirar".
En monitoreo volcanico esos dos estados son opuestos: el primero es informacion
(el volcan esta tranquilo), el segundo es ausencia de informacion (la nube tapo).
Antes de dibujar una banda hay que establecer que senal soporta el dato.
"""
import json, sys, io, collections, statistics, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

VOLS = ["NevadosDeChillan", "Villarrica", "Lascar", "Isluga", "Llaima", "Copahue",
        "Tupungatito", "Lastarria", "PuyehueCordonCaulle", "PlanchonPeteroa", "Chaiten"]
# ROI 25 km de radio -> 50x50 km. Pixel VIIRS I nadir = 375 m.
PIX_ROI_I = (50.0 / 0.375) ** 2

def cargar(v):
    p = pathlib.Path(f"data/mirova_equivalent/{v}.json")
    if not p.exists(): return []
    d = json.loads(p.read_text(encoding="utf-8"))
    return d["records"] if isinstance(d, dict) else d

print(f"{'volcan':22s} {'recs':>6s} {'I-band':>7s} {'ceg.med':>8s} {'p90':>6s} {'tbgNone':>8s}")
print("-" * 62)
resumen = {}
for v in VOLS:
    recs = cargar(v)
    if not recs: continue
    iband = [r for r in recs if r.get("n_cloud_masked") is not None]
    frac = sorted(100.0 * r["n_cloud_masked"] / PIX_ROI_I for r in iband)
    tn = sum(1 for r in recs if r.get("t_bg_k") is None)
    med = frac[len(frac)//2] if frac else float("nan")
    p90 = frac[int(len(frac)*.9)] if frac else float("nan")
    print(f"{v:22s} {len(recs):6d} {len(iband):7d} {med:7.1f}% {p90:5.1f}% {100*tn/len(recs):7.1f}%")
    resumen[v] = {"n": len(recs), "n_iband": len(iband),
                  "ceg_mediana_pct": med, "ceg_p90_pct": p90,
                  "tbg_none_pct": 100*tn/len(recs)}

# El claim que hice antes: NdC julio = apagon por nube, no por calma.
print("\n=== NdC mes a mes (VIIRS375): ceguera vs detecciones ===")
print(f"{'mes':9s} {'pasadas':>8s} {'ceg.med':>9s} {'>50%ciego':>10s} {'con VRP':>8s}")
recs = cargar("NevadosDeChillan")
por_mes = collections.defaultdict(list)
for r in recs:
    if r.get("n_cloud_masked") is not None:
        por_mes[r["datetime_utc"][:7]].append(r)
for m in sorted(por_mes)[-9:]:
    rs = por_mes[m]
    fr = sorted(100.0 * r["n_cloud_masked"] / PIX_ROI_I for r in rs)
    ciegas = sum(1 for f in fr if f > 50)
    convrp = sum(1 for r in rs if (r.get("primary_cluster") or {}).get("vrp_mw"))
    print(f"{m:9s} {len(rs):8d} {fr[len(fr)//2]:8.1f}% {100*ciegas/len(rs):9.0f}% {convrp:8d}")

pathlib.Path("experiments/_s124_observabilidad/01_resumen.json").write_text(
    json.dumps(resumen, indent=1), encoding="utf-8")
