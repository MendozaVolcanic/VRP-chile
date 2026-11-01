# -*- coding: utf-8 -*-
"""Verificador S158. ¿El 0,83 de C0 contra el 0,27 de K en #864 es diferencia de detector (fondo) o de noches?
Mide, con la misma función del auto-audit, K (JSON de hoy, todo K) y C0 (JSON previo a #883) sobre las MISMAS
noches de la ventana C0 de #864 (2026-08-20 a 2026-09-17), y anota la fuente final_hotspot_source del record C0
que da el máximo publicado de cada noche.

Uso: python -I v8_k_en_noches_c0.py <Tupungatito_pre883.json>
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
hoy, _ = aw.cargar_records()
coords = aw._coords_por_volcan()
alertas = aw.aplicar_d9(aw.alertas_mirova(), aw.REGLA_MINIMAS, aw.cargar_filas_referencia())
win = ("2026-08-20", "2026-09-17")
mir, inst, _ = aw.noches_mirova_con_instante(alertas, coords, win)
fuente = {(a["fecha_utc"] or "")[:16]: a.get("source") for a in alertas
          if a["volcano"] == "Tupungatito" and a["sensor_bucket"] == "VIIRS375"}
c0 = aw.nuestros_por_noche({"Tupungatito": pre}, win, "2026-09-18")["ours"]
k = aw.nuestros_por_noche({"Tupungatito": hoy["Tupungatito"]}, win, "2025-01-01")["ours"]
src = {r["datetime_utc"][:16]: r.get("final_hotspot_source") for r in pre if not (r.get("regimen") or {}).get("codigo_sha")
       and r["sensor"] in ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21")}
L = ["noche       M     fuenteM  R_C0   R_K    fuente C0 de la pasada publicada máxima"]
rc, rk = [], []
for (vol, s, f), m in sorted(mir.items()):
    if vol != "Tupungatito" or s != "VIIRS375" or m <= 0:
        continue
    a, b = c0.get((vol, s, f)), k.get((vol, s, f))
    ra = max(a["pub"]) / m if a and a["dash"] else None
    rb = max(b["pub"]) / m if b and b["dash"] else None
    fu = None
    if a and a["dash"]:
        i = a["pub"].index(max(a["pub"]))
        fu = src.get(a["dt_pub"][i])
    if ra is not None and rb is not None:
        rc.append((ra, fuente.get(inst[(vol, s, f)][:16]))); rk.append((rb, fuente.get(inst[(vol, s, f)][:16])))
    L.append(f"{f}  {m:5.2f}  {fuente.get(inst[(vol, s, f)][:16])}  "
             f"{'%.3f' % ra if ra is not None else '  -  '}  {'%.3f' % rb if rb is not None else '  -  '}  {fu}")
L.append(f"noches con los dos: {len(rc)}; mediana R_C0 {st.median(r for r, _ in rc):.3f}, R_K {st.median(r for r, _ in rk):.3f}")
L.append(f"sólo M de tabla: n {sum(1 for _, x in rc if x == 'CONS')}, R_C0 {st.median(r for r, x in rc if x == 'CONS'):.3f}, "
         f"R_K {st.median(r for r, x in rk if x == 'CONS'):.3f}")
txt = "\n".join(L); print(txt)
(AQUI / "v8_k_en_noches_c0_salida.txt").write_text(txt + "\n", encoding="utf-8")
