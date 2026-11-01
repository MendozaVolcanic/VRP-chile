# -*- coding: utf-8 -*-
"""Noches-volcan con ALERTA nocturna de MIROVA (consolidado u OCR) en que NINGUNA pasada nuestra
publica (predicado del dashboard ejecutado con node, via scripts/banco_paridad.py), por ventana.
Sirve para contrastar A98 («874 de 877 noches con alerta detectadas; la brecha es sobre-publicacion,
no recall», medida bajo C0) con los records de K.
P1: si K perdiera noches, aparecen aca con su VRP de MIROVA; si no, la lista sale vacia.
P2: controles heredados de banco_paridad (identidad del predicado con node); ademas la ventana C0
previa debe dar una lista corta (A98 decia 3 de 877) para que una lista larga en K signifique algo.
Referencia: snapshot del repo (worktree en origin/main de hoy). Regla de minimas: 'original'
(la del pre-registro de K) y 'SN' (D-9, la de MISSION).
"""
import sys, io, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402

def correr(ventana, regla):
    coords = B._coords_por_volcan(); inner = B.inner_desde_html()
    ident = B.control_identidad_predicado()
    assert ident == ([0, 1, 1, 1, 0], [1, 0]), ident
    filas = B.cargar_referencia_unificada(B.SNAP_CONS, B.SNAP_OCR)
    por_vb, ns, nv, _ = B.indexar_referencia(filas, coords, ventana, regla_minimas=regla)
    recs = B.cargar_nuestros(coords, inner, ventana)
    B.etiquetar(recs, por_vb, ns, nv)
    # VRP maximo de MIROVA por noche-volcan (alertas)
    vrp = collections.defaultdict(float); sens = collections.defaultdict(set)
    for (vol, b), lista in por_vb.items():
        for dt, f in lista:
            if B.es_alerta(f["tipo"]):
                k = (vol, f["fecha_utc"][:10]); vrp[k] = max(vrp[k], f["vrp_mw"] or 0); sens[k].add(b)
    pub = collections.defaultdict(int); tiene = set()
    for r in recs:
        k = (r["vol"], r["noche"]); tiene.add(k); pub[k] += r["pub"]
    alert_nights = [k for k, d in nv.items() if d["alerta"] and k in tiene]
    perdidas = sorted(k for k in alert_nights if pub[k] == 0)
    return alert_nights, perdidas, vrp, sens
for nombre, v in [("C0 previa", ("2026-08-18", "2026-09-17")), ("K", ("2026-09-18", "2026-10-18"))]:
    for regla in ("original", "SN"):
        an, per, vrp, sens = correr(v, regla)
        prot = [k for k in per if vrp[k] >= 1.0]
        print(f"\n== {nombre} {v} regla {regla}: noches con alerta y record {len(an)} | sin publicar {len(per)} | de ellas con VRP MIROVA >= 1 MW: {len(prot)}")
        for k in per:
            print("   ", k, "VRP_MIROVA_max", round(vrp[k], 3), "sensores_alerta", sorted(sens[k]))
