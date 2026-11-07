# -*- coding: utf-8 -*-
"""Línea base roja (1): con los records y la referencia del commit 79f41069 (el que escribió latest.json del 2026-11-02,
19:29 UTC) y el código del audit de la base, ¿se reproducen recall y n_misma_pasada (125/194, 32/42, 14/16)?
Uso: python linea_base_1102.py <root>. Imprime JSON."""
import os, sys, json, collections
from datetime import date
ROOT = sys.argv[1]
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.stdout.reconfigure(encoding="utf-8")
import auto_audit_weekly as aw
assert os.path.realpath(aw.ROOT) == os.path.realpath(ROOT)
win = ("2026-09-03", "2026-11-02")
fr = aw.leer_frontera_k(); vig = aw.detector_vigente(fr)
al = aw.alertas_mirova(); co = aw._coords_por_volcan(); fref = aw.cargar_filas_referencia()
mir, inst, _ = aw.noches_mirova_con_instante(aw.aplicar_d9(al, aw.REGLA_MINIMAS, fref), co, win)
ceses, _ = aw.leer_ceses(); mir, _ = aw.partir_por_plataformas(mir, aw.juzga_desde(ceses, date(2026, 11, 2)))
rpv, _ = aw.cargar_records(); vm = aw.frontera_via_modis(rpv)
nu = aw.nuestros_por_noche(rpv, win, fr, via_modis=vm)
dets = ("K",) + (("VIA_MODIS",) if vm else ())
pd = {d: aw.evaluar_detector(mir, nu["ours"], nu["vistos"], d, fr, vm) for d in dets}
ev = aw.evaluacion_vigente(pd, vig, vm)
est = aw.estratificar_magnitud(mir, nu["ours"], fr, vig, inst, vm)
c = collections.Counter()
for k, v in est["por_regimen"].items():
    for rg, x in v.items():
        c[k.split("|")[1] + "|n"] += x["n_noches"]; c[k.split("|")[1] + "|misma"] += x["n_misma_pasada"] or 0
lj = json.load(open(os.path.join(ROOT, "data", "audit_continuous", "latest.json"), encoding="utf-8"))
print(json.dumps({"root": ROOT, "via_modis": vm, "recall": ev["recall"], "n_misma": dict(c), "latest_json_recall": lj["recall"]}, ensure_ascii=False))
