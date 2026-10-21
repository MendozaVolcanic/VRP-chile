# -*- coding: utf-8 -*-
"""V3, hallazgo F4-H1: ¿cuántas veces el mínimo fijo de dNTI de escena decide el umbral (prose branch = max)?
P1: si el mínimo nunca decidiera, la fracción saldría 0; si siempre, 1: la medición distingue ambos extremos.
P2: records sin diag_mu_dnti/diag_sd_dnti se cuentan aparte (SIN DATO), no como 'no decide'.
Control positivo: el umbral cumbre con C1=0,003 y C2=5 (decide casi nunca según F4) contra el de escena.
Ventana 2026-03-01..2026-10-21, noche del pipeline, 11 Tier A, TODOS los records nocturnos (no sólo pos+neg_limpio).
Umbrales evaluados: 0,010 (nuestro), 0,020 (código V750, unidades 3x3), 0,0225 (0,02 en unidades de 8 vecinos).
"""
import sys, io, json, os, collections
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada
import pipeline.profile as P
print("C1 scene", P.DNTI_CONTEXTUAL_C1_SCENE, "C2 scene", P.C2_DNTI_SCENE_NIGHT, "prose", P.ENABLE_TESTS_23_PROSE_BRANCH)
VENT = ("2026-03-01", "2026-10-21"); coords = _coords_por_volcan()
acc = collections.defaultdict(list); sin = collections.Counter()
for vol in bp.VOLS:
    for r in json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))["records"]:
        b = bp.bucket(r.get("sensor")); t = r.get("datetime_utc", "")
        if b is None or not (VENT[0] <= t[:10] <= VENT[1]):
            continue
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if es_pasada_diurna_descartada(b, *coords[vol], dt):
            continue
        mu, sd, mue, sde = r.get("diag_mu_dnti"), r.get("diag_sd_dnti"), r.get("diag_mu_deti"), r.get("diag_sd_deti")
        if mu is None or sd is None:
            sin[b] += 1; continue
        acc[b].append((mu + 10 * sd, mu + 5 * sd, (mue + 10 * sde) if mue is not None else np.nan))
for b in bp.BUCKETS:
    a = np.array(acc[b]); t10, t5, te = a[:, 0], a[:, 1], a[:, 2]
    print(f"{b}: n={len(a)} (sin diag {sin[b]}) | escena dNTI mu+10s < 0,010: {(t10<0.010).mean():.3f}  < 0,020: {(t10<0.020).mean():.3f}"
          f"  < 0,0225: {(t10<0.0225).mean():.3f}  mediana {np.median(t10):.4f} | cumbre mu+5s<0,003: {(t5<0.003).mean():.3f}"
          f" | escena dETI mu+10s<0,010: {np.nanmean(te<0.010):.3f}")
