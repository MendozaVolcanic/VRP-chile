# -*- coding: utf-8 -*-
"""Verificador del evaluador de D25 (S157). ¿La exclusión de las protegidas sólo OCR de Suomi NPP respeta el hito
del 2026-10-09 (§4: «hasta el 2026-10-09 ... esas pasadas no deciden»)? E.ocr_snpp no mira la fecha. Cuenta, en V1
con la referencia congelada de D25, las pasadas VIIRS de K (copia unida en temporales) que evaluar_d25 excluiría por
Suomi NPP, antes y después del hito. Sin publicar ni etiquetar: sólo la condición de exclusión (prot A + alerta sólo
OCR + plataforma SNPP). También cuenta las pasadas sin cenit (no entran a ningún estrato que decide).
Uso: python v3_snpp_hito.py > v3_salida.txt"""
import collections
import json
import sys
from pathlib import Path

REPO = Path(r"D:\vrp-trabajo\s157-prereg-d25")
sys.path.insert(0, str(REPO / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402

E, bp = X.E, X.bp
K = Path(r"D:\vrp-trabajo\temporales\s157d25\k_unido")
cfg = dict(X.VENTANAS["V1"])
tmp = Path(r"D:\vrp-trabajo\temporales\verif_eval\v3"); tmp.mkdir(parents=True, exist_ok=True)
ref = E.archivos_ref(cfg, tmp)
claves, plat, zen = set(), {}, {}
for v in bp.VOLS:
    for r in json.load(open(K / (v + ".json"), encoding="utf-8"))["records"]:
        b, t = bp.bucket(r.get("sensor")), r.get("datetime_utc", "")
        if b in X.SENS and cfg["desde"] <= t[:10] <= cfg["hasta"]:
            k = "|".join((v, b, t[:16])); claves.add(k); plat[k] = r.get("sensor"); zen[k] = r.get("sensor_zenith_deg")
prot = E.proteccion(claves, ref, cfg["desde"], cfg["hasta"])
c = collections.Counter()
for k in claves:
    if prot[k]["A"] and E.ocr_snpp(k, {"plataforma": plat[k]}, prot):
        c[(k.split("|")[1], "antes_o_igual_2026-10-09" if k.split("|")[2][:10] <= "2026-10-09" else "despues_2026-10-09")] += 1
print("protegidas A excluidas por ocr_snpp (sin mirar si K publica), por sensor y tramo del hito:")
for kk, n in sorted(c.items()):
    print("  ", kk, n)
sz = collections.Counter(k.split("|")[1] for k in claves if zen[k] is None)
print("pasadas VIIRS de K en V1 sin sensor_zenith_deg:", dict(sz), "de", len(claves))
