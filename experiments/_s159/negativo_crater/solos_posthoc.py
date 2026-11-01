# -*- coding: utf-8 -*-
"""S159, negativo limpio con crater: POST HOC (no estaba en la regla de §0). Records SOLOS cuyo anillo es chico.

POR QUE. La regla NLC deja todos los records solos (el indicador de fraccion necesita un companero). Pero un
record solo puede tener el ROI recortado (N-8: Chaiten 2026-05-15 04:24 V750, nbg 10, el pixel mas cercano a
23,5 km). Como el perfil corre sin mascara de nube (cloud_mask_bt_k: 0.0 en mirova_equivalent.yaml), el anillo
es casi pura geometria: rho = nbg / mediana de nbg de los records solos del mismo volcan y plataforma con cenit a
+-3 grados. rho < 0,5 sugiere que el crater no esta en el granulo (y el de MIROVA es el mismo granulo).

P1 (lo veria?): control positivo, Chaiten 05-15 04:24 tiene que dar rho muy bajo. P2 (instrumento muerto?):
si nbg fuera constante, rho seria 1 en todos y no saldria nada; se imprime la distribucion.
Uso: python -I solos_posthoc.py <espejo>
"""
import collections
import os
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = Path(sys.argv[1])
sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402
import auto_audit_weekly as aw  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR  # noqa: E402
import nlc  # noqa: E402

NBG, COMP, _ = nlc.indice_anillo(bp.DATA, bp.VOLS)
COORDS = aw._coords_por_volcan(); INNER = bp.inner_desde_html()
FILAS = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)


def clave(r):
    return (r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"))


for ventana, regla in ((("2026-01-10", "2026-10-21"), "original"), ((aw.INICIO_REGIMEN_FALSAS, "2026-10-21"), "SN")):
    por_vb, ns, nv, _ = bp.indexar_referencia(FILAS, COORDS, ventana, regla_minimas=regla)
    recs = bp.cargar_nuestros(COORDS, INNER, ventana)
    bp.etiquetar(recs, por_vb, ns, nv)
    solos = [r for r in recs if COMP.get(clave(r)) is None and r.get("z") is not None]
    grupo = collections.defaultdict(list)
    for r in solos:
        grupo[(r["vol"], r["sensor"])].append(r)
    print(f"\n=== ventana {ventana}, regla {regla}")
    for b in bp.BUCKETS:
        neg = [r for r in solos if r["b"] == b and r["lab"] == "neg_limpio"]
        rhos = []
        bajos = []
        for r in neg:
            ref = [NBG[clave(x)] for x in grupo[(r["vol"], r["sensor"])] if abs(x["z"] - r["z"]) <= 3]
            med = statistics.median(ref) if ref else None
            rho = NBG[clave(r)] / med if med else None
            rhos.append(rho)
            if rho is not None and rho < 0.5:
                bajos.append((r, rho))
        qs = sorted(x for x in rhos if x is not None)
        print(f"{b}: solos en neg_limpio {len(neg)}; rho p1 {qs[len(qs)//100]:.2f} p5 {qs[len(qs)//20]:.2f} mediana "
              f"{statistics.median(qs):.2f}; rho<0,5: {len(bajos)}, K/todos publican ahi: {sum(r['pub'] for r, _ in bajos)}"
              f" (publican en todos los solos: {sum(r['pub'] for r in neg)})")
        for r, rho in bajos:
            if r["pub"]:
                print(f"    rho<0,5 y publica: {r['vol']} {r['sensor']} {r['dt']:%Y-%m-%d %H:%M} rho {rho:.2f}")
        for r, rho in bajos:
            if r["vol"] == "Chaiten" and r["dt"].strftime("%Y-%m-%d %H:%M") == "2026-05-15 04:24":
                print(f"    control positivo Chaiten 05-15 04:24 {r['sensor']}: rho {rho:.3f} nbg {NBG[clave(r)]}")
