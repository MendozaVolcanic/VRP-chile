# -*- coding: utf-8 -*-
"""Cruza CMR público, LAADS y LANCE sobre los gránulos que cubren a los 11 Tier A.

Geometría: huella de CMR del mismo día; si CMR no tiene el gránulo, huella del mismo
HHMM 16 días antes (ciclo de repetición exacto de Terra, Aqua, SNPP, NOAA-20 y NOAA-21).
La predicción se valida en el día sano 2026-10-15 contra la huella real de CMR.
Lee sólo 01_listar_resultado.json (no consulta la red).
"""
import io, json, sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# stdout lo envuelve 01_listar al importarse
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from importlib import import_module
L = import_module("01_listar".replace("01_listar", "01_listar"))  # noqa
res = json.loads((AQUI / "01_listar_resultado.json").read_text(encoding="utf-8"))
vols = L.tier_a()
DIAS = res["dias"]
L1B = {"MOD021KM": "MOD03", "MYD021KM": "MYD03", "VNP02IMG": "VNP03IMG", "VNP02MOD": "VNP03MOD",
       "VJ102IMG": "VJ103IMG", "VJ102MOD": "VJ103MOD", "VJ202IMG": "VJ203IMG", "VJ202MOD": "VJ203MOD"}


def cubre(polys):
    return sorted({n for n, lo, la in vols for p in polys if L.dentro(lo, la, p)})


def idx_cmr(key):
    d = res["cmr"][key]
    if d["g"] is None:
        return None
    out = defaultdict(dict)
    for g in d["g"]:
        out[g["dia"]][g["hhmm"]] = g
    return out


print("== Estado de las consultas (SIN DATO si status != 200)")
for k, v in res["cmr"].items():
    print(f"CMR {k:18s} st={v['st']} n={'SIN DATO' if v['g'] is None else len(v['g'])}")
for k, v in res["cmr_analogo"].items():
    print(f"CMR análogo {k:10s} st={v['st']} n={'SIN DATO' if v['g'] is None else len(v['g'])}")
print("\n== Listados diarios: total de archivos del día (sano ~240 VIIRS, ~288 MODIS)")
print(f"{'producto':10s} " + " ".join(f"{d[5:]:>11s}" for d in DIAS + ['2026-10-30']))
for src in ("laads", "lance"):
    for p in L.PROD:
        cel = []
        for d in DIAS + ["2026-10-30"]:
            v = res[src][f"{p}|{d}"]
            cel.append(f"{len(v['l']):>11d}" if v["l"] is not None else f"{'SD:' + str(v['st']):>11s}")
        print(f"{src[:5]:5s} {p:10s}" + " ".join(cel))

recs = res["recs"]
for r in recs:   # los records NRT de VIIRS llevan el sufijo _NRT en el nombre del gránulo
    r["nrt_nombre"] = r["prod"].endswith("_NRT")
    r["prod"] = r["prod"].replace("_NRT", "")
rec_idx = defaultdict(set)
rec_name = {}
for r in recs:
    rec_idx[(r["prod"], r["dia"])].add(r["hhmm"])
    rec_name[(r["prod"], r["dia"], r["hhmm"])] = r["granule"]

# análogos
ana = {}
for p, v in res["cmr_analogo"].items():
    a = defaultdict(dict)
    for g in (v["g"] or []):
        a[g["dia"]][g["hhmm"]] = g
    ana[p] = a


def relevantes(p, dia, usar_analogo_solo=False):
    """{hhmm: (dn, volcanes, fuente_geom)} para gránulos que cubren >=1 Tier A."""
    out = {}
    std = idx_cmr(f"{p}|std") or {}
    nrt = idx_cmr(f"{p}|nrt") or {}
    mismo = dict(nrt.get(dia, {})); mismo.update(std.get(dia, {}))
    if not usar_analogo_solo:
        for h, g in mismo.items():
            v = cubre(g["polys"])
            if v:
                out[h] = (g["dn"], v, "cmr_mismo_dia")
    d16 = (datetime.strptime(dia, "%Y-%m-%d") - timedelta(days=16)).strftime("%Y-%m-%d")
    # MODIS: la predicción D-16 falla en el control del 2026-10-15 (0 de 8 Terra, 0 de 4 Aqua;
    # Terra y Aqua ya no mantienen el ciclo de repetición). Sólo VIIRS usa el análogo.
    for h, g in ({} if p.startswith(("MOD", "MYD")) else ana.get(p, {}).get(d16, {})).items():
        v = cubre(g["polys"])
        if v and h not in out:
            out[h] = (g["dn"], v, "analogo_d16")
    for h in rec_idx.get((p, dia), set()):
        if h not in out:
            out[h] = ("?", ["(record)"], "record")
    return out


print("\n== Control de la predicción D-16 en el día sano 2026-10-15")
for p in L1B:
    real = {h for h, x in relevantes(p, "2026-10-15").items() if x[2] == "cmr_mismo_dia"}
    pred = {h for h, x in relevantes(p, "2026-10-15", usar_analogo_solo=True).items() if x[2] == "analogo_d16"}
    print(f"{p:10s} real {len(real):2d} pred {len(pred):2d} coinciden {len(real & pred):2d} "
          f"sólo real {sorted(real - pred)} sólo pred {sorted(pred - real)}")

print("\n== Tabla día x producto (gránulos que cubren >=1 Tier A; noche / total)")
print("columnas: REL relevantes | REC con record nuestro | CMRs CMR std | CMRn CMR NRT | "
      "LAs LAADS L1B+GEO | LAn LANCE L1B+GEO | RESC recuperables (en depósito con GEO, no en CMR)")
filas, rescatables = [], []
for dia in DIAS:
    for p, geo in L1B.items():
        rel = relevantes(p, dia)
        cs = (idx_cmr(f"{p}|std") or {}).get(dia, {})
        cn = (idx_cmr(f"{p}|nrt") or {}).get(dia, {})
        gs = (idx_cmr(f"{geo}|std") or {}).get(dia, {})
        gn = (idx_cmr(f"{geo}|nrt") or {}).get(dia, {})
        la = res["laads"][f"{p}|{dia}"]["l"]; lag = res["laads"][f"{geo}|{dia}"]["l"]
        ln = res["lance"][f"{p}|{dia}"]["l"]; lng = res["lance"][f"{geo}|{dia}"]["l"]
        cnt = defaultdict(lambda: [0, 0])
        for h, (dn, vv, fg) in rel.items():
            noche = dn == "NIGHT"
            en_cmr = (h in cs and h in gs) or (h in cn and h in gn)
            en_la = la is not None and lag is not None and h in la and h in lag
            en_ln = ln is not None and lng is not None and h in ln and h in lng
            for k, ok in (("REL", True), ("REC", h in rec_idx.get((p, dia), set())),
                          ("CMRs", h in cs), ("CMRn", h in cn), ("LAs", en_la), ("LAn", en_ln),
                          ("RESC", (not en_cmr) and (en_la or en_ln))):
                if ok:
                    cnt[k][1] += 1
                    cnt[k][0] += noche
            if (not en_cmr) and (en_la or en_ln):
                rescatables.append({"dia": dia, "prod": p, "hhmm": h, "dn": dn, "vols": vv, "geom": fg,
                                    "laads": la.get(h) if en_la else None,
                                    "laads_geo": lag.get(h) if en_la else None,
                                    "lance": ln.get(h) if en_ln else None,
                                    "url_laads": res["laads"][f"{p}|{dia}"]["url"],
                                    "url_lance": res["lance"][f"{p}|{dia}"]["url"],
                                    "record": rec_name.get((p, dia, h))})
        sd = lambda x: "" if x is not None else "*"
        fila = (dia, p, {k: cnt[k] for k in ("REL", "REC", "CMRs", "CMRn", "LAs", "LAn", "RESC")},
                sd(la) + sd(lag), sd(ln) + sd(lng))
        filas.append(fila)
        c = fila[2]
        print(f"{dia} {p:9s} " + " ".join(f"{k}={c[k][0]}/{c[k][1]}" for k in c) +
              (f"  [LAADS SIN DATO]" if fila[3] else "") + (f"  [LANCE SIN DATO]" if fila[4] else ""))

print(f"\n== Recuperables: {len(rescatables)} (noche: {sum(r['dn']=='NIGHT' for r in rescatables)})")
for r in rescatables:
    print(json.dumps({k: r[k] for k in ("dia", "prod", "hhmm", "dn", "geom", "vols", "laads", "lance", "record")},
                     ensure_ascii=False))

print("\n== Control positivo 2026-10-15: records nuestros presentes en cada fuente")
for p, geo in L1B.items():
    hs = rec_idx.get((p, "2026-10-15"), set())
    if not hs:
        continue
    cs = (idx_cmr(f"{p}|std") or {}).get("2026-10-15", {}); cn = (idx_cmr(f"{p}|nrt") or {}).get("2026-10-15", {})
    la = res["laads"][f"{p}|2026-10-15"]["l"] or {}; ln = res["lance"][f"{p}|2026-10-15"]["l"] or {}
    print(f"{p:9s} records(gránulos distintos) {len(hs):2d} CMRstd {len(hs & set(cs)):2d} CMRnrt {len(hs & set(cn)):2d} "
          f"LAADS {len(hs & set(la)):2d} LANCE {len(hs & set(ln)):2d}")

print("\n== Records cuyo gránulo hoy en LAADS tiene otro sello de producción (reproceso)")
cambio = defaultdict(lambda: [0, 0, 0])
for r in recs:
    p = r["prod"]
    if p not in L1B:
        continue
    la = res["laads"][f"{p}|{r['dia']}"]["l"]
    if la is None:
        continue
    k = (r["dia"], p)
    cambio[k][0] += 1
    actual = la.get(r["hhmm"])
    if actual is None:
        cambio[k][2] += 1
    elif actual.rsplit(".", 2)[0] != r["granule"].rsplit(".", 2)[0] or actual.split(".")[4] != r["granule"].split(".")[4]:
        cambio[k][1] += 1
for k in sorted(cambio):
    print(f"{k[0]} {k[1]:9s} records {cambio[k][0]:3d} sello distinto {cambio[k][1]:3d} ausente en LAADS {cambio[k][2]:3d}")

print("\n== Casos nombrados")
for dia, p, h in (("2026-10-12", "VJ202MOD", "0518"), ("2026-10-12", "VJ202IMG", "0518"),
                  ("2026-10-12", "VNP02MOD", "0548"), ("2026-10-12", "VNP02MOD", "0554")):
    geo = L1B[p]
    out = {}
    for src in ("laads", "lance"):
        out[src] = ((res[src][f"{p}|{dia}"]["l"] or {}).get(h), (res[src][f"{geo}|{dia}"]["l"] or {}).get(h))
    for tag in ("std", "nrt"):
        out["cmr_" + tag] = (h in (idx_cmr(f"{p}|{tag}") or {}).get(dia, {}),
                             h in (idx_cmr(f"{geo}|{tag}") or {}).get(dia, {}))
    out["record"] = rec_name.get((p, dia, h))
    print(dia, p, h, json.dumps(out))

(AQUI / "02_rescatables.json").write_text(json.dumps(rescatables, ensure_ascii=False, indent=1), encoding="utf-8")

print("\n== Gránulos nocturnos sobre Tier A en LAADS Standard (L1B+GEO) que CMR Standard no indexa hoy")
tot = 0
for dia in DIAS:
    for p, geo in L1B.items():
        rel = relevantes(p, dia)
        cs = (idx_cmr(f"{p}|std") or {}).get(dia, {}); gs = (idx_cmr(f"{geo}|std") or {}).get(dia, {})
        cn = (idx_cmr(f"{p}|nrt") or {}).get(dia, {})
        la = res["laads"][f"{p}|{dia}"]["l"] or {}; lag = res["laads"][f"{geo}|{dia}"]["l"] or {}
        hs = sorted(h for h, x in rel.items() if x[0] == "NIGHT" and h in la and h in lag and not (h in cs and h in gs))
        if hs:
            tot += len(hs)
            print(f"{dia} {p:9s} {len(hs)}: {hs}  (en CMR NRT: {sum(h in cn for h in hs)}) "
                  f"{res['laads'][f'{p}|{dia}']['url']}")
print("total", tot)

print("\n== CMR Standard: entradas nocturnas sobre Tier A cuyo nombre ya no está en LAADS (enlace muerto)")
for dia in DIAS:
    for p, geo in L1B.items():
        cs = (idx_cmr(f"{p}|std") or {}).get(dia, {})
        la = res["laads"][f"{p}|{dia}"]["l"] or {}
        rel = relevantes(p, dia)
        muertos = [(h, cs[h]["name"], la.get(h)) for h in sorted(cs) if h in rel and rel[h][0] == "NIGHT"
                   and la.get(h) != cs[h]["name"]]
        for m in muertos:
            print(dia, p, *m)
