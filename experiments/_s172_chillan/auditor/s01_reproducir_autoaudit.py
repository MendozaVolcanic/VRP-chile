# -*- coding: utf-8 -*-
"""s01 (S172, auditoria Chillan): reproduce las tres razones de Chillan del auto-audit del 2026-10-26.

POR QUE: antes de descomponer un numero hay que mostrar que el instrumento propio lee los mismos datos que el
auto-audit. Si reproduzco 0,56 / 0,662 / 0,683 con las funciones del propio auto_audit_weekly sobre la copia del
commit que escribio latest.json, la carga es la misma; si no, cualquier descomposicion posterior mide otra cosa.

P1 (si lo medido estuviera roto, lo veria): si la carga de records o de la referencia fallara, n_noches y la
    mediana no coincidirian con latest.json (se imprimen lado a lado).
P2 (instrumento muerto): control negativo, se desplaza la referencia un dia; las noches comunes deben cambiar.
Uso: python -B s01_reproducir_autoaudit.py <raiz copia> <salida json>
"""
import json, os, sys
from collections import defaultdict
from datetime import datetime, timedelta

ROOT, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
os.chdir(ROOT)
import auto_audit_weekly as aw  # noqa: E402

VOL = "NevadosDeChillan"
aw.VOLS = [VOL]
win = ("2026-08-27", "2026-10-26")
frontera = aw.leer_frontera_k()
vigente = aw.detector_vigente(frontera)
alertas = aw.alertas_mirova()
coords = aw._coords_por_volcan()
filas_ref = aw.cargar_filas_referencia()
mir, inst, n_diur = aw.noches_mirova_con_instante(aw.aplicar_d9(alertas, aw.REGLA_MINIMAS, filas_ref), coords, win)
ceses, err = aw.leer_ceses()
desde = aw.juzga_desde(ceses, datetime(2026, 10, 26).date())
mir, aparte = aw.partir_por_plataformas(mir, desde)
d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", VOL + ".json"), encoding="utf-8"))
nu = aw.nuestros_por_noche({VOL: d["records"]}, win, frontera)
ev = aw.evaluar_detector(mir, nu["ours"], nu["vistos"], vigente, frontera)
lat = json.load(open(os.path.join(ROOT, "data", "audit_continuous", "latest.json"), encoding="utf-8"))
res = {"frontera": frontera, "vigente": vigente, "ventana": win, "err_ceses": err,
       "mio": {k: v for k, v in ev["magnitud_publicada_by_vol_sensor"].items()},
       "latest": {k: v for k, v in lat["magnitud_publicada_by_vol_sensor"].items() if k.startswith(VOL)}}
# control negativo: referencia corrida un dia
mir_shift = {(v, s, (datetime.fromisoformat(f) + timedelta(days=1)).date().isoformat()): x for (v, s, f), x in mir.items()}
ev2 = aw.evaluar_detector(mir_shift, nu["ours"], nu["vistos"], vigente, frontera)
res["control_desplazado_1d"] = ev2["magnitud_publicada_by_vol_sensor"]
# detalle por noche (para s02): razon max(pub)/max(MIROVA)
det = []
for (v, s, f), m in sorted(mir.items()):
    o = nu["ours"].get((v, s, f))
    det.append({"sensor": s, "noche": f, "mirova_max": m, "mirova_inst": inst.get((v, s, f)),
                "pub": (o or {}).get("pub"), "dt_pub": (o or {}).get("dt_pub"), "z_pub": (o or {}).get("z_pub"),
                "npix": (o or {}).get("npix"),
                "razon": (max(o["pub"]) / m) if (o and o["dash"] and m > 0) else None})
res["noches"] = det
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
print("frontera", frontera, "vigente", vigente, "ceses_err", err)
for k in sorted(set(res["mio"]) | set(res["latest"])):
    print(k, "mio", res["mio"].get(k), "| latest", res["latest"].get(k), "| desplazado", res["control_desplazado_1d"].get(k))
