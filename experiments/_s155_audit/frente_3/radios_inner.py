"""F3: inner_radius_km de las cuatro fuentes que usan los instrumentos (auto_audit_weekly.INNER,
audit_metrics.INNER_RADIUS_KM_TIER_A, frontend/index.html vía banco_paridad.inner_desde_html, volcanoes.yaml).
P1: una diferencia se imprimiría como DISTINTO. P2: un volcán ausente lanza KeyError (no un cero)."""
import os, sys, yaml
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, ROOT)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import auto_audit_weekly as aw, banco_paridad as bp
from pipeline.audit_metrics import INNER_RADIUS_KM_TIER_A as A
h = bp.inner_desde_html()
y = {v["name"]: v.get("inner_radius_km") for v in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
for v in aw.VOLS:
    vals = (aw.INNER[v], A[v], h[v], y[v])
    print(v, vals, "IGUAL" if len({float(x) for x in vals}) == 1 else "DISTINTO")
