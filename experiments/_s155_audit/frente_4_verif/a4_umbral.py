# -*- coding: utf-8 -*-
"""F4-04: ¿que termino gobierna el umbral de los Tests 2 y 3? Con max gobierna mu+C2*sigma si supera a C1; con min,
gobierna C1 en ese mismo caso. Se mide con los diag_mu/sd del primer pase persistidos en cada record (noche:
C1 summit 0.003 / scene 0.010, C2 5 / 10, leidos de pipeline.profile).
P1: si sigma fuera 0 en todos los records, la fraccion 'estadistico > C1' daria 0; se imprime la distribucion.
P2: records sin diag (None) se cuentan aparte como SIN DATO, no como 0.
"""
import io, json, sys, collections, os, statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT)); os.environ["VRP_PROFILE"] = "mirova_equivalent"
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pipeline.profile as P
C1s, C1e, C2s, C2e = P.DNTI_CONTEXTUAL_C1_SUMMIT, P.DNTI_CONTEXTUAL_C1_SCENE, P.C2_DNTI_SUMMIT_NIGHT, P.C2_DNTI_SCENE_NIGHT
print("C1 summit/scene", C1s, C1e, "C2", C2s, C2e)
M = [json.loads(x) for x in open("main_jul_oct.jsonl", encoding="utf-8")]
for reg, lo, hi in (("C0", "2026-08-29", "2026-09-17"), ("K", "2026-09-18", "2026-10-19")):
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        c = collections.Counter(); st = []
        for r in M:
            if r["b"] != b or r["reg"] != reg or not (lo <= r["noche"] <= hi): continue
            mu, sd, me, se = r["diag_mu_dnti"], r["diag_sd_dnti"], r["diag_mu_deti"], r["diag_sd_deti"]
            if None in (mu, sd, me, se): c["sin_dato"] += 1; continue
            c["n"] += 1
            c["dnti_sum_stat>C1"] += (mu + C2s * sd) > C1s
            c["deti_sum_stat>C1"] += (me + C2s * se) > C1s
            c["dnti_sce_stat>C1"] += (mu + C2e * sd) > C1e
            c["deti_sce_stat>C1"] += (me + C2e * se) > C1e
            st.append(mu + C2s * sd)
        n = c["n"] or 1
        print(reg, b, dict(c), {k: round(v / n, 3) for k, v in c.items() if ">" in k},
              "mediana mu+5sd dNTI", round(statistics.median(st), 4) if st else None)
