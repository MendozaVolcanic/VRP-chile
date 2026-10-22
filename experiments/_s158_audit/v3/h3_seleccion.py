# -*- coding: utf-8 -*-
"""V3, F3-H3: ¿cuánto de la energía alertada dentro del inner queda fuera de la magnitud publicada?
Población: records nocturnos (definición del pipeline) 2026-03-01..2026-10-21, 11 Tier A, distance_class summit,
cúmulo con centroid_dist_km <= inner, lista completa (n <= 100). Igual que F3 salvo: distancia DESDE EL CRÁTER
(get_detection_anchor), no dist_km del record (centro del volcán), y tramos de cenit.
Publicado = mirovaEqVrpCore aproximado (V375: f5_core_vrp_mw si > 0, si no pc.vrp_mw; V750/MODIS: pc.vrp_mw).
P1: si publicado = suma de los de dentro siempre, la razón es 1 en todas; se imprime la fracción con razón 1.
P2: records sin píxeles dentro salen y se cuentan (SIN DATO).
Además: la vara de MIROVA es la suma de TODOS los alertados de su ventana (código V750, VRP.m l. 83-85), así que
también doy publicado / suma de TODOS nuestros alertados (escena) como cota.
"""
import sys, io, json, os, collections
from pathlib import Path
from datetime import datetime, timezone
import numpy as np, pandas as pd, yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline.geo_utils import get_detection_anchor
from auto_audit_weekly import es_pasada_diurna_descartada
import banco_paridad as bp
Y = {v["name"]: v for v in yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
def hav(a, b, c, d):
    p1, p2 = np.radians(a), np.radians(c); dp = p2 - p1; dl = np.radians(d - b)
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2))
rows = []; sin_dentro = collections.Counter()
for v in bp.VOLS:
    inner = Y[v]["inner_radius_km"]; alat, alon = get_detection_anchor(Y[v])
    for r in json.load(open(ROOT / "data" / "mirova_equivalent" / f"{v}.json", encoding="utf-8"))["records"]:
        t = r.get("datetime_utc", ""); b = bp.bucket(r.get("sensor"))
        if b is None or not ("2026-03-01" <= t[:10] <= "2026-10-21"):
            continue
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if es_pasada_diurna_descartada(b, Y[v]["lat"], Y[v]["lon"], dt):
            continue
        pc = r.get("primary_cluster") or {}; px = r.get("anomaly_pixels") or []
        if r.get("distance_class") != "summit" or not pc or (pc.get("centroid_dist_km") or 0) > inner:
            continue
        if not px or len(px) != (r.get("n_anomalous_pixels") or 0):
            continue
        dv = np.array([hav(alat, alon, p["lat"], p["lon"]) for p in px]); e = np.array([p["vrp_mw"] for p in px])
        dc = np.array([p["dist_km"] for p in px])
        Ein, Einc, Eall = e[dv <= inner].sum(), e[dc <= inner].sum(), e.sum()
        f5 = r.get("f5_core_vrp_mw")
        pub = (f5 if (b == "VIIRS375" and isinstance(f5, (int, float)) and f5 > 0) else (pc.get("vrp_mw") or 0))
        if Ein <= 0:
            sin_dentro[b] += 1; continue
        rows.append({"vol": v, "b": b, "zen": r.get("sensor_zenith_deg"), "pub": pub, "Ein": Ein, "Einc": Einc, "Eall": Eall})
D = pd.DataFrame(rows)
print("records sin energía dentro (SIN DATO, salen):", dict(sin_dentro))
D["r"] = D.pub / D.Ein
print("\nPOR SENSOR: n | Σpub/ΣEin (cráter) | Σpub/ΣEin_centro (F3) | Σpub/ΣE_todos | frac razón==1 (±0,5 %) | idem cenit<=20")
for b, g in D.groupby("b"):
    z = g[g.zen <= 20]
    print(f"{b:9s} {len(g):5d} | {g.pub.sum()/g.Ein.sum():.3f} | {g.pub.sum()/g.Einc.sum():.3f} | {g.pub.sum()/g.Eall.sum():.3f} | "
          f"{(np.abs(g.r-1)<0.005).mean():.3f} | cenit<=20: n={len(z)} {z.pub.sum()/z.Ein.sum():.3f}")
print("\nPOR VOLCÁN y sensor (n>=20): Σpub/ΣEin cráter | centro | Σpub/ΣE_todos | p10 de la razón por pasada")
for (b, v), g in D.groupby(["b", "vol"]):
    if len(g) >= 20:
        print(f"{b:9s} {v:20s} n={len(g):4d} {g.pub.sum()/g.Ein.sum():.3f} | {g.pub.sum()/g.Einc.sum():.3f} | {g.pub.sum()/g.Eall.sum():.3f} | p10 {np.percentile(g.r,10):.3f}")
# concentración: cuánto del déficit lo aportan las 10 pasadas peores
for b, g in D.groupby("b"):
    deficit = (g.Ein - g.pub).clip(lower=0)
    top = deficit.sort_values(ascending=False)
    print(f"{b}: déficit total {deficit.sum():.2f} MW; las 10 pasadas peores aportan {top.head(10).sum()/max(deficit.sum(),1e-9):.2%}")
