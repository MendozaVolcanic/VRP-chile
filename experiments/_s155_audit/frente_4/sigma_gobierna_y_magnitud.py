# -*- coding: utf-8 -*-
"""Dos re-mediciones baratas sobre records de K (2026-09-18 a 2026-10-18) y C0 (2026-08-18 a 2026-09-17).

(1) A103 / H_S141_VECINO_FOCO_V2 afirman que «el umbral efectivo es el piso C1 = 0,003 en los 70»
    (medido bajo `min`). Bajo `max` el umbral efectivo del dNTI en la cumbre es max(C1, mu + C2 sigma).
    Se cuenta en que fraccion de records nocturnos mu + C2*sigma (diag_mu_dnti, diag_sd_dnti; C2 = 5 de
    cumbre, leidos de pipeline.profile) supera C1 = 0,003: ahi, bajo K, el piso NO es el umbral.
    P1: si el sigma nunca gobernara, la fraccion daria 0. P2: los campos diag_* se cuentan como
    presentes/ausentes; un campo ausente es SIN DATO, no 'no gobierna'.
(2) Magnitud publicada (mirovaEqVrpDisplay por node, banco_paridad) contra la VRP de MIROVA en las
    pasadas con ALERTA, mediana del cociente por sensor y ventana. Contrasta los 0,78x / 0,80x de S103
    (R3, bajo C0) y el 0,7 de A99. P1: si K no cambiara la magnitud, las medianas coincidirian.
    P2: denominador = pasadas pos con disp > 0 y VRP MIROVA > 0; se informa n.
"""
import sys, io, json, statistics, collections, os
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as B  # noqa: E402
import pipeline.profile as P  # noqa: E402
C1 = P.DNTI_CONTEXTUAL_C1_SUMMIT; C2 = P.C2_DNTI_SUMMIT_NIGHT
ven = {"C0": ("2026-08-18", "2026-09-17"), "K": ("2026-09-18", "2026-10-18")}
print("C1", C1, "C2", C2)
for nombre, (a, b) in ven.items():
    c = collections.Counter()
    for v in B.VOLS:
        for r in json.load(open(B.DATA / f"{v}.json", encoding="utf-8"))["records"]:
            if not (a <= r.get("datetime_utc", "")[:10] <= b):
                continue
            s = B.bucket(r.get("sensor"))
            mu, sd = r.get("diag_mu_dnti"), r.get("diag_sd_dnti")
            if mu is None or sd is None:
                c[(s, "sin_dato")] += 1; continue
            c[(s, "n")] += 1
            c[(s, "sigma_gobierna")] += (mu + C2 * sd) > C1
    print(f"\n(1) {nombre} {a}..{b}")
    for s in B.BUCKETS:
        n = c[(s, "n")]
        print(f"   {s:9} sigma gobierna {c[(s,'sigma_gobierna')]}/{n} ({100*c[(s,'sigma_gobierna')]/max(n,1):.1f} %), sin dato {c[(s,'sin_dato')]}")
coords = B._coords_por_volcan(); inner = B.inner_desde_html()
assert B.control_identidad_predicado() == ([0, 1, 1, 1, 0], [1, 0])
filas = B.cargar_referencia_unificada(B.SNAP_CONS, B.SNAP_OCR)
for nombre, v in ven.items():
    por_vb, ns, nv, _ = B.indexar_referencia(filas, coords, v)
    recs = B.cargar_nuestros(coords, inner, v)
    B.etiquetar(recs, por_vb, ns, nv)
    rat = collections.defaultdict(list)
    for r in recs:
        if r["lab"] != "pos" or not r["disp"]:
            continue
        al = [f for f in B.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"]) if B.es_alerta(f["tipo"]) and (f["vrp_mw"] or 0) > 0]
        if al:
            rat[r["b"]].append(r["disp"] / max(f["vrp_mw"] for f in al))
    print(f"\n(2) {nombre} {v}")
    for s in B.BUCKETS:
        x = rat[s]
        print(f"   {s:9} n {len(x)} mediana disp/MIROVA {statistics.median(x):.3f}" if x else f"   {s:9} n 0")
