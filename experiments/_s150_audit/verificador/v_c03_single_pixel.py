"""Verificador S150, hallazgo C-03.

Llama a la funcion REAL pipeline.single_pixel_mode.apply_single_pixel_mode con los
valores que lee pipeline.profile bajo VRP_PROFILE=mirova_equivalent (no los del YAML a
mano, A89), sobre casos sinteticos alrededor del corte y sobre los tres records reales
VIIRS 750 de Nevados de Chillan del 2026-10-01 (05:24, 06:00, 06:18).

Preguntas del instrumento:
1. Si el corte no existiera, ¿lo veria? Si: los pares sinteticos 4,8 / 5,1 MW darian
   ambos la suma.
2. Si el instrumento estuviera muerto (flag apagado o funcion passthrough), ¿se veria
   distinto? Si: imprimo el flag leido; con enabled=False el control da la suma.
Control positivo: el record real de 05:24 trae pc.vrp_mw = 2,655 en el JSON; la funcion
tiene que reproducir ese numero desde los per-pixel guardados.
"""
import io
import json
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
import pipeline.profile as P  # noqa: E402
from pipeline.single_pixel_mode import apply_single_pixel_mode  # noqa: E402

EN = P.ENABLE_SINGLE_PIXEL_SUB_MW_MODE
TH = P.SUB_MW_REGIME_THRESHOLD_MW
MX = P.SINGLE_PIXEL_MAX_CLUSTER_PIXELS
print(f"perfil: enabled={EN} threshold_mw={TH} max_pixels={MX}")


def run(px, enabled=EN):
    pc = {"vrp_mw": round(sum(px), 4), "n_pixels": len(px)}
    out = apply_single_pixel_mode(pc, px, enabled=enabled, threshold_mw=TH, max_pixels=MX)
    return pc["vrp_mw"], out["vrp_mw"], out.get("single_pixel_mode")


print("\nSinteticos (pixeles -> suma, publicado, modo):")
for px in ([1.6, 1.6, 1.6], [1.7, 1.7, 1.7], [2.49, 2.49], [2.51, 2.51],
           [4.9, 0.05], [1.0, 1.0, 1.0, 1.0]):
    print("  ", px, "->", run(px))
print("control enabled=False [1.6]*3 ->", run([1.6, 1.6, 1.6], enabled=False))

print("\nReales Chillan 2026-10-01 V750 (per-pixel del JSON):")
recs = json.loads((REPO / "data/mirova_equivalent/NevadosDeChillan.json").read_text(encoding="utf-8"))["records"]
for r in recs:
    d = r.get("datetime_utc") or ""
    if d.startswith("2026-10-01") and r.get("sensor", "").endswith("_750") and d[11:] in ("05:24", "06:00", "06:18"):
        px = [p["vrp_mw"] for p in (r.get("anomaly_pixels") or [])]
        s, pub, modo = run(px)
        print(f"   {d} {r['sensor']}: pixeles={px} suma={s} funcion={pub} modo={modo} "
              f"JSON pc.vrp_mw={(r.get('primary_cluster') or {}).get('vrp_mw')}")
