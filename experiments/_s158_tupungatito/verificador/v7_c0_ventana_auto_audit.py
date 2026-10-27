# -*- coding: utf-8 -*-
"""Verificador S158. El 0,825 de C0 que cita el README (§En corto 4: «#864 ve 0,27 donde C0 veía 0,83») sale de
data/audit_continuous/latest.json, sobre OTRAS noches (2026-08-20 a 2026-09-17, C0). Se reproduce con
auto_audit_weekly.evaluar_detector sobre el JSON previo a #883 y se lista noche por noche, marcando las noches
cuya alerta máxima es sólo OCR (puede ser lejana) para ver si el 0,825 tiene el mismo problema que el 0,266.

Uso: python -I v7_c0_ventana_auto_audit.py <Tupungatito_pre883.json>
"""
import io, json, os, statistics as st, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import auto_audit_weekly as aw  # noqa: E402

pre = json.load(open(sys.argv[1], encoding="utf-8"))["records"]
recs = {"Tupungatito": pre}
coords = aw._coords_por_volcan()
alertas = aw.aplicar_d9(aw.alertas_mirova(), aw.REGLA_MINIMAS, aw.cargar_filas_referencia())
win, frontera = ("2026-08-20", "2026-10-19"), "2026-09-18"
mir, inst, _ = aw.noches_mirova_con_instante(alertas, coords, win)
nn = aw.nuestros_por_noche(recs, win, frontera)
L = []
for det in ("C0", "K"):
    ev = aw.evaluar_detector(mir, nn["ours"], nn["vistos"], det, frontera)
    L.append(f"{det}: Tupungatito|VIIRS375 {ev['magnitud_publicada_by_vol_sensor'].get('Tupungatito|VIIRS375')}")
fuente = {(a["fecha_utc"] or "")[:16]: a.get("source") for a in alertas
          if a["volcano"] == "Tupungatito" and a["sensor_bucket"] == "VIIRS375"}
L.append("noches C0 (noche, M, instante, fuente de M, publicado, R):")
rs = []
for (vol, s, f), m in sorted(mir.items()):
    if vol != "Tupungatito" or s != "VIIRS375" or aw.detector_de_noche(f, frontera) != "C0":
        continue
    o = nn["ours"].get((vol, s, f))
    if not (o and o["dash"]) or m <= 0:
        continue
    R = max(o["pub"]) / m
    rs.append((R, fuente.get(inst[(vol, s, f)][:16])))
    L.append(f"  {f} M {m:5.2f} {inst[(vol, s, f)][:16]} {fuente.get(inst[(vol, s, f)][:16])} pub {max(o['pub']):.3f} R {R:.3f}")
L.append(f"mediana todas {st.median(r for r, _ in rs):.3f} (n {len(rs)}); sólo noches con M de tabla "
         f"{st.median(r for r, fu in rs if fu == 'CONS'):.3f} (n {sum(1 for _, fu in rs if fu == 'CONS')})")
txt = "\n".join(L); print(txt)
(AQUI / "v7_c0_ventana_auto_audit_salida.txt").write_text(txt + "\n", encoding="utf-8")
