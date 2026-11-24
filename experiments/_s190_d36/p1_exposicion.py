# -*- coding: utf-8 -*-
# FICHA (SDA, CPLT 372): script de medición sobre los records, sólo lectura.
"""D36 punto 1, lo que se puede medir sin gránulos (A2): exposición de la vía MODIS a los dos números del .m.

POR QUÉ: el piso de 0,02 sólo actúa en las zonas 0 y 1 de la caja (fuera de la cumbre sensible 5 x 5) y sólo cuando
mu + 10 sd < 0,02; el K1 sólo cuando una celda tiene NTI > umbral. Los records guardan, por pasada, mu, sd y los
umbrales de cada pase (diag_codigo_mirova.s1), n_abs y las celdas alertadas. Con eso se cuenta en cuántas escenas el
piso manda (la Tabla 1 bajaría el umbral fuera de la cumbre), cuánto bajaría, y en qué zona caen nuestros alertados.
No dice cuántas celdas nuevas alertarían: eso necesita los gránulos (p1_runner.py).
Ventana: records nocturnos de la vía MODIS de los 11 Tier A desde DESDE (por defecto 2026-03-01).
Uso: python experiments/_s190_d36/p1_exposicion.py <raiz_repo> <salida.json> [DESDE]
"""
import collections
import json
import sys
from pathlib import Path

ROOT, OUT = sys.argv[1], sys.argv[2]
DESDE = sys.argv[3] if len(sys.argv) > 3 else "2026-03-01"
sys.path.insert(0, ROOT)
from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
import yaml  # noqa: E402

VOLC = {x["name"]: x for x in yaml.safe_load(open(Path(ROOT) / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}

TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan", "Llaima",
          "PlanchonPeteroa", "Tupungatito", "Isluga", "Lastarria", "Chaiten"]
fam = MV.FAMILIAS["MODIS"]
res = {"desde": DESDE, "por_volcan": {}}
tot = collections.Counter()
for v in TIER_A:
    recs = json.load(open(Path(ROOT) / "data/mirova_equivalent" / (v + ".json"), encoding="utf-8"))["records"]
    g = MV.grilla_del_volcan(v, paso_m=fam["paso_m"], clave_roi=fam["clave_roi"])
    alat, alon = get_detection_anchor(VOLC[v])
    alat, alon = (VOLC[v]["lat"], VOLC[v]["lon"]) if alat is None else (alat, alon)
    box = MV.caja_roi(g.get("roi", "def"), n=g["n"], celda_crater=MV.celda_de(g, alat, alon),
                      inner_km=VOLC[v].get("inner_radius_km"), lado_sensible=fam["lado_sensible"],
                      lado_anillo=fam["lado_anillo"], paso_m=g["paso"])
    c = collections.Counter()
    nuevos_u = []
    for r in recs:
        if not (str(r.get("sensor", "")).startswith("MODIS") and r.get("via_codigo_mirova") is True
                and r["datetime_utc"][:10] >= DESDE):
            continue
        dg = r.get("diag_codigo_mirova") or {}
        if dg.get("dayflag") != 0:
            c["no_nocturna"] += 1
            continue
        c["n"] += 1
        s1 = dg.get("s1") or {}
        p1, p2 = s1.get("pasada1") or {}, s1.get("pasada2") or {}
        if not p1:
            c["sin_s1_" + str(dg.get("motivo_vacio"))] += 1
            continue
        c["con_s1"] += 1
        for nom, p in (("p1", p1), ("p2", p2)):
            mu, sd = p.get("mu_nti"), p.get("sd_nti")
            if mu is None or sd is None:
                continue
            u_hoy = max(mu + 10 * sd, 0.02)
            u_tab = max(mu + 10 * sd, 0.01)
            if u_tab < u_hoy:
                c["piso_manda_" + nom] += 1
                if nom == "p1":
                    nuevos_u.append(u_tab)
        if (dg.get("n_abs") or 0) > 0:
            c["n_abs_mayor_0"] += 1
        celdas = r.get("anomaly_pixels") or []
        if celdas:
            c["con_alerta"] += 1
            zonas = {int(box[p["fila"], p["col"]]) for p in celdas}
            c["alerta_con_celda_zona_0_1"] += bool(zonas & {0, 1})
            c["alerta_solo_zona_2"] += zonas == {2}
            for p in celdas:
                c["celdas_zona_%d" % int(box[p["fila"], p["col"]])] += 1
    nuevos_u.sort()
    c_d = dict(c)
    c_d["u_tabla1_p1_mediana_si_baja"] = nuevos_u[len(nuevos_u) // 2] if nuevos_u else None
    c_d["roi"] = g.get("roi", "def")
    res["por_volcan"][v] = c_d
    tot.update({k: x for k, x in c.items()})
    print(v, {k: c_d[k] for k in sorted(c_d)}, flush=True)
res["total"] = dict(tot)
print("TOTAL", dict(sorted(tot.items())))
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
