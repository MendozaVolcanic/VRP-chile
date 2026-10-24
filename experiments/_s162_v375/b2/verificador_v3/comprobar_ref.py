"""Comprueba, leyendo los artefactos de S162 directamente, que ref_M14 / granule / hora del CTL son los del id_ref."""
import json, hashlib
from pathlib import Path
ART = Path("C:/vrp-trabajo/temporales/s162_v375/run_40116289866")
EXP = Path(__file__).resolve().parent.parent.parent
R = {}
for f in sorted(ART.rglob("resultados_VIIRS375_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")):
        R[r["id"]] = r
o162 = {o["id"]: o for o in json.loads((EXP / "objetivos_v375_bc.json").read_text(encoding="utf-8"))["pasadas"]}
b2 = json.loads((EXP / "b2/objetivos_v375_b2.json").read_text(encoding="utf-8"))
print("sha256 objetivos_v375_b2.json:", hashlib.sha256((EXP / "b2/objetivos_v375_b2.json").read_bytes()).hexdigest())
ctl = [o for o in b2["pasadas"] if o["lote"] == "CTL"]
malos = 0
for o in ctl:
    r = R[o["id_ref"]]; oo = o162[o["id_ref"]]
    m = r["port"]["M14"]
    ok = (m["npix"] == o["ref_M14"][0] and m["vrp_mw"] == o["ref_M14"][1] and r["granule"] == o["granule"]
          and oo["hora_utc"] == o["hora_utc"] and oo["volcan"] == o["volcan"] and oo["clase"] == o["clase_ref"]
          and r["estado"] == "ok")
    malos += not ok
    print(o["id"], o["id_ref"], o["volcan"], o["clase_ref"], "npix", m["npix"], "vrp", m["vrp_mw"], "OK" if ok else "DISTINTO")
print("CTL:", len(ctl), "con pixeles:", sum(1 for o in ctl if o["ref_M14"][0] > 0), "distintos de S162:", malos)
# los ids de S162 que entran al CTL, estan tambien en el lote S162b? (deberian no: S162b es neg_resto nuevo)
claves_b2 = {(o["volcan"], o["hora_utc"]) for o in b2["pasadas"] if o["lote"] == "S162b"}
print("CTL repetidos dentro de S162b:", sum(1 for o in ctl if (o["volcan"], o["hora_utc"]) in claves_b2))
