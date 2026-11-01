# -*- coding: utf-8 -*-
"""Verificador S157: analisis read-only de op vs reproceso por volcan."""
import json, sys, io, math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[5]  # raiz del repo
DESDE, HASTA = "2025-02-15", "2026-09-17"
vols = sys.argv[1:] or ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima", "PlanchonPeteroa",
                         "PuyehueCordonCaulle", "Tupungatito", "Villarrica"]
out = {}
for v in vols:
    op = json.load(open(RAIZ / "data/mirova_equivalent" / f"{v}.json", encoding="utf-8"))
    re_ = json.load(open(RAIZ / "data/_s154_reproc_k_historico" / f"{v}.json", encoding="utf-8"))
    o = {}
    o["top_op"] = sorted(k for k in op if k != "records")
    o["top_re"] = sorted(k for k in re_ if k != "records")
    R_op, R_re = op["records"], re_["records"]
    en = lambda r: DESDE <= (r.get("datetime_utc") or "")[:10] <= HASTA
    o["dt_none_op"] = sum(1 for r in R_op if not r.get("datetime_utc"))
    o["dt_none_re"] = sum(1 for r in R_re if not r.get("datetime_utc"))
    o["dt_formats_op"] = dict(Counter(len(r.get("datetime_utc") or "") for r in R_op))
    o["dt_formats_re"] = dict(Counter(len(r.get("datetime_utc") or "") for r in R_re))
    o["rango_op"] = [min(r["datetime_utc"] for r in R_op), max(r["datetime_utc"] for r in R_op)]
    o["rango_re"] = [min(r["datetime_utc"] for r in R_re), max(r["datetime_utc"] for r in R_re)]
    o["op_antes_ventana"] = sum(1 for r in R_op if (r.get("datetime_utc") or "")[:10] < DESDE)
    o["op_despues_ventana"] = sum(1 for r in R_op if (r.get("datetime_utc") or "")[:10] > HASTA)
    o["re_fuera"] = Counter("antes" if r["datetime_utc"][:10] < DESDE else "despues" for r in R_re if not en(r))
    # regimen por mes en op
    reg = defaultdict(Counter)
    for r in R_op:
        g = r.get("regimen") or {}
        reg[r["datetime_utc"][:7]][(g.get("perfil"), (g.get("codigo_sha") or "")[:9])] += 1
    o["regimen_op_por_mes"] = {m: {f"{a}|{b}": n for (a, b), n in c.items()} for m, c in sorted(reg.items())}
    regre = Counter()
    for r in R_re:
        g = r.get("regimen") or {}
        regre[(g.get("perfil"), g.get("codigo_sha"), g.get("origen"))] += 1
    o["regimen_re"] = {f"{a}|{b}|{c}": n for (a, b, c), n in regre.items()}
    # claves
    kop = Counter((r.get("datetime_utc"), r.get("sensor")) for r in R_op if en(r))
    kre = Counter((r.get("datetime_utc"), r.get("sensor")) for r in R_re if en(r))
    o["dup_op"] = sum(n - 1 for n in kop.values() if n > 1)
    o["dup_re"] = sum(n - 1 for n in kre.values() if n > 1)
    op_d = {(r["datetime_utc"], r.get("sensor")): r for r in R_op if en(r)}
    re_d = {(r["datetime_utc"], r.get("sensor")): r for r in R_re if en(r)}
    comunes = [k for k in re_d if k in op_d]
    agreg = [k for k in re_d if k not in op_d]
    # schema
    keys_op, keys_re = Counter(), Counter()
    for k in comunes:
        keys_op.update(op_d[k].keys()); keys_re.update(re_d[k].keys())
    o["campos_solo_op"] = {f: keys_op[f] for f in keys_op if keys_re[f] < keys_op[f] * 0.5}
    o["campos_solo_re"] = {f: keys_re[f] for f in keys_re if keys_op[f] < keys_re[f] * 0.5}
    # product_version
    o["pv_pares"] = dict(Counter(f"{op_d[k].get('product_version')}->{re_d[k].get('product_version')}" for k in comunes))
    o["pv_agregados"] = dict(Counter(re_d[k].get("product_version") for k in agreg))
    # agregados cercanos a una pasada op del mismo sensor (posible duplicado con hora distinta)
    por_sensor = defaultdict(list)
    for (dt, s) in op_d:
        por_sensor[s].append(datetime.fromisoformat(dt.replace("Z", "")))
    for s in por_sensor: por_sensor[s].sort()
    import bisect
    cerca = 0; ejemplos = []
    for (dt, s) in agreg:
        t = datetime.fromisoformat(dt.replace("Z", ""))
        L = por_sensor.get(s, [])
        i = bisect.bisect_left(L, t)
        for j in (i - 1, i):
            if 0 <= j < len(L) and abs((L[j] - t).total_seconds()) <= 600:
                cerca += 1; ejemplos.append((dt, s, str(L[j]))); break
    o["agregados_a_10min_de_op"] = cerca
    o["agregados_ejemplos_cerca"] = ejemplos[:5]
    # agregados fuera de nov-ene
    o["agregados_raros"] = sorted(dt + " " + s for (dt, s) in agreg if dt[:7] not in ("2025-11", "2025-12", "2026-01"))[:20]
    # solo op: product_version y mes
    solo = [k for k in op_d if k not in re_d]
    o["solo_op"] = sorted(f"{k[0]} {k[1]} {op_d[k].get('product_version')}" for k in solo)
    # cambios publicados aproximados: summit con vrp>0
    def pub(r):
        try:
            return r.get("distance_class") == "summit" and (r.get("vrp_mw") or 0) > 0
        except Exception:
            return False
    o["pub_op_comunes"] = sum(pub(op_d[k]) for k in comunes)
    o["pub_re_comunes"] = sum(pub(re_d[k]) for k in comunes)
    o["pub_agregados"] = sum(pub(re_d[k]) for k in agreg)
    o["pub_solo_op"] = sum(pub(op_d[k]) for k in solo)
    nan_vrp = sum(1 for k in comunes for x in (op_d[k].get("vrp_mw"), re_d[k].get("vrp_mw")) if isinstance(x, float) and math.isnan(x))
    o["nan_vrp_comunes"] = nan_vrp
    # tamano de anomaly_pixels
    o["mean_len_anomaly_pixels_op"] = sum(len(op_d[k].get("anomaly_pixels") or []) for k in comunes) / max(1, len(comunes))
    o["mean_len_anomaly_pixels_re"] = sum(len(re_d[k].get("anomaly_pixels") or []) for k in comunes) / max(1, len(comunes))
    # first_processed_utc
    o["fpu_agregados"] = Counter((re_d[k].get("first_processed_utc") or "None")[:7] for k in agreg).most_common(3)
    o["fpu_op_comunes"] = Counter(bool(op_d[k].get("first_processed_utc")) for k in comunes)
    o["fpu_op_presente_pero_falsy"] = sum(1 for k in comunes if "first_processed_utc" in op_d[k] and not op_d[k]["first_processed_utc"])
    out[v] = o
    print(v, "listo", file=sys.stderr)
    del op, re_, R_op, R_re, op_d, re_d
json.dump(out, open(Path(__file__).parent / f"analisis_{'_'.join(vols) if len(vols)<3 else 'todos'}.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
print("ok")
