# -*- coding: utf-8 -*-
"""F4-06: ¿el laboratorio (experimental_v2, C0) es mas ciego que la replica (K) en MODIS? Mismas pasadas
(vol, datetime, sensor) en los dos directorios, 18-sep a 19-oct, contra las alertas MIROVA (lab_SN del
banco). Predicado del tablero (node) para ambos con el mismo inner (frontend/index.html).
P1: control positivo, VIIRS 375 debe mostrar al laboratorio publicando MUCHO mas (C0 sobre-publica).
P2: pasadas sin par se cuentan aparte."""
import io, json, sys, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import banco_paridad as bp
M = {(r["vol"], r["dt"], r["sensor"]): r for r in (json.loads(x) for x in open("main_jul_oct.jsonl", encoding="utf-8"))}
inner = bp.inner_desde_html()
recs, casos = [], []
ult = {}
for vol in bp.VOLS:
    p = ROOT / "data/experimental_v2" / f"{vol}.json"
    if not p.exists(): print("sin archivo", vol); continue
    rs = json.loads(p.read_text(encoding="utf-8"))["records"]
    ult[vol] = max(r["datetime_utc"] for r in rs)
    for r in rs:
        if not ("2026-09-18" <= r["datetime_utc"][:10] <= "2026-10-19"): continue
        recs.append((vol, r)); slim = {k: r.get(k) for k in bp.CAMPOS_JS}
        casos.append([slim, inner[vol]])
print("ultimo record del laboratorio por volcan:", ult)
pred = bp.correr_node(casos)
c = collections.Counter()
for (vol, r), p in zip(recs, pred):
    b = bp.bucket(r.get("sensor")); m = M.get((vol, r["datetime_utc"], r.get("sensor")))
    if m is None: c[(b, "sin_par")] += 1; continue
    lab = m.get("lab_SN")
    c[(b, "n")] += 1; c[(b, "pub_lab")] += p[4]; c[(b, "pub_op")] += m["pub"]
    if lab == "pos":
        c[(b, "pos")] += 1; c[(b, "pos_pub_lab")] += p[4]; c[(b, "pos_pub_op")] += m["pub"]
    if lab == "neg_limpio":
        c[(b, "neg")] += 1; c[(b, "neg_pub_lab")] += p[4]; c[(b, "neg_pub_op")] += m["pub"]
    c[(b, "op_pub_lab_no")] += (m["pub"] and not p[4])
for k in sorted(c, key=str): print(k, c[k])
