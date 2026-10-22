# -*- coding: utf-8 -*-
"""S159, censo del oráculo en VIIRS 750, paso 2: lee el censo y cuenta lo pre-registrado (PREREGISTRO.md).

Pregunta 1 (si el oráculo estuviera roto, ¿se vería?): control 4, el oráculo tiene que detectar las alertas de
MIROVA con razón cercana a 1; y control 2, tiene que repetir pasada por pasada lo que midió el frente N.
Pregunta 2 (instrumento muerto): control 1, K tiene que reproducir la publicación y el pc.vrp_mw de producción; y
control 3, el contador (predicado del tablero con node) tiene que cambiar cuando se perturba un record. Las pasadas que
no corrieron son SIN DATO y se cuentan aparte, nunca como «no publica».
Ventana de todo número: VIIRS 750 nocturno, 2026-04-01 a 2026-10-21 sin el 18 y 19 de octubre (población del frente N).
Uso: python 02_analizar.py --art <carpeta(s) del censo> [--n-art <carpetas de N para el control 2>] [--salida sufijo]
"""
from __future__ import annotations

import argparse
import collections
import copy
import csv
import importlib.util
import json
import random
import statistics
import sys
from pathlib import Path

import numpy as np
import yaml

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "experiments/_s158_audit_r2/oraculo"))
import banco_paridad as B  # noqa: E402

spec = importlib.util.spec_from_file_location("cen", ROOT / "experiments/_s159/n/07_censo_analizar.py")
CEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CEN)
record_oraculo, slim = CEN.record_oraculo, CEN.slim   # copiadas sin cambios (pre-registro §3)

CAJAS = ("geo_linear", "geo_linear_anillo_sensible")
NOM = {"geo_linear": "O-def", "geo_linear_anillo_sensible": "O-sens"}


def cargar(dirs):
    res = {}
    for d in dirs:
        for f in sorted(Path(d).rglob("resultados_*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                if r.get("estado") == "ok" or r["id"] not in res:
                    res[r["id"]] = r
    return res


def pos_volcan_en_grilla(g, lat, lon):
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
    x, y = t.transform(lon, lat)
    return (g["ul_y"] - y) / 750.0 - 0.5, (x - g["ul_x"]) / 750.0 - 0.5   # fila, columna fraccionarias


def record_oraculo_volcan(o, inner, sensor, fila_v, col_v):
    """Sensibilidad declarada: la distancia del centroide se mide desde la coordenada de volcanoes.yaml."""
    r = record_oraculo(o, inner, sensor)
    if r.get("primary_cluster"):
        px = o["pixeles"]
        fr, fc = np.mean([p[0] for p in px]), np.mean([p[1] for p in px])
        d = float(np.hypot(fr - fila_v, fc - col_v) * 0.75)
        r["primary_cluster"]["centroid_dist_km"] = round(d, 3)
        r["distance_class"] = "summit" if d <= inner else "far"
    return r


def tramo_z(z):
    if z is None:
        return "z?"
    for lim, n in ((20, "0-20"), (40, "20-40"), (50, "40-50"), (60, "50-60")):
        if z <= lim:
            return n
    return ">60"


def partida(r):
    if r.get("estado") == "volcan_fuera_del_granulo":
        return "fuera"
    c = r.get("cobertura")
    if not c:
        return "sin_cobertura"
    if c["nan_7"] > 0 or c["nan_centro"]:
        return "sin_crater"
    return "partida_con_crater" if c["nan_67"] > 0 else "entera"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True, nargs="+")
    ap.add_argument("--n-art", nargs="*", default=[str(AQUI.parent / "n/run_39682867040"),
                                                  str(AQUI.parent / "n/run_39693661527")])
    ap.add_argument("--objetivos", default=str(AQUI / "objetivos.json"))
    ap.add_argument("--salida", default="")
    a = ap.parse_args()
    obj = {o["id"]: o for o in json.loads(Path(a.objetivos).read_text(encoding="utf-8"))}
    res = cargar(a.art)
    inner = B.inner_desde_html()
    vy = {v["name"]: v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    pv = {}
    L = []

    def pr(*x):
        s = " ".join(str(y) for y in x)
        print(s)
        L.append(s)

    # ---------------------------------------------------------------- cobertura
    pr("== cobertura: objetivos", len(obj), "con resultado", len(res))
    est = collections.Counter((obj[i]["lab"], (res.get(i) or {}).get("estado", "sin_resultado")) for i in obj)
    pr("  ", dict(sorted(est.items())))

    def ok(i):
        r = res.get(i) or {}
        k = (r.get("brazos") or {}).get("K") or {}
        return (r.get("estado") == "ok" and set(CAJAS) <= set(r.get("oraculo") or {})
                and "error" not in k and "record" in k)

    oks = [i for i in obj if ok(i)]
    fuera = [i for i in obj if (res.get(i) or {}).get("estado") == "volcan_fuera_del_granulo"]
    sin = [i for i in obj if i not in oks and i not in fuera]
    sin_mot = collections.Counter(((res.get(i) or {}).get("estado", "sin_resultado")[:60], obj[i]["lab"]) for i in sin)
    pr("   ok:", len(oks), "| fuera del granulo:", len(fuera), "| SIN DATO:", len(sin), dict(sin_mot))

    # ---------------------------------------------------------------- casos para node
    casos, idx = [], []

    def agrega(rec, i, etiqueta):
        casos.append([rec, inner[obj[i]["volcan"]]])
        idx.append((i, etiqueta))

    for i in oks:
        o = obj[i]
        r = res[i]
        agrega(slim(r["brazos"]["K"]["record"]), i, "K")
        if o["volcan"] not in pv:
            pv[o["volcan"]] = pos_volcan_en_grilla(o["grilla"], vy[o["volcan"]]["lat"], vy[o["volcan"]]["lon"])
        for c in CAJAS:
            agrega(record_oraculo(r["oraculo"][c], inner[o["volcan"]], o["sensor"]), i, c)
            agrega(record_oraculo_volcan(r["oraculo"][c], inner[o["volcan"]], o["sensor"], *pv[o["volcan"]]), i,
                   c + "|volcan")
    P = {k: bool(p[4]) for k, p in zip(idx, B.correr_node(casos))}
    pub = lambda i, b: P[(i, b)]

    # ---------------------------------------------------------------- control 3: nulo del instrumento
    nulo, nidx = [], []
    for i in oks:
        for c in CAJAS:
            if pub(i, c):
                base = record_oraculo(res[i]["oraculo"][c], inner[obj[i]["volcan"]], obj[i]["sensor"])
                a0 = copy.deepcopy(base)
                a0["primary_cluster"]["vrp_mw"] = 0.0
                a0["vrp_mw"] = 0.0
                b0 = copy.deepcopy(base)
                b0["distance_class"] = "far"
                for t, rr in (("vrp0", a0), ("far", b0)):
                    nulo.append([rr, inner[obj[i]["volcan"]]])
                    nidx.append((i, c, t, True))
    rng = random.Random(159)
    neg_no = [i for i in oks if obj[i]["lab"] == "neg_limpio" and not pub(i, "geo_linear")]
    for i in rng.sample(neg_no, min(50, len(neg_no))):
        rr = {"sensor": obj[i]["sensor"], "vrp_mw": 0.3, "t_max_k": 290.0, "triggered_test1": False,
              "distance_class": "summit", "primary_cluster": {"vrp_mw": 0.3, "n_pixels": 1, "centroid_dist_km": 0.5}}
        nulo.append([rr, inner[obj[i]["volcan"]]])
        nidx.append((i, "inyectado", "summit_0.3", False))
    NP = [bool(p[4]) for p in B.correr_node(nulo)] if nulo else []
    fallo_nulo = [(i, c, t) for (i, c, t, era), p in zip(nidx, NP) if p == era]
    pr(f"== control 3 (nulo): {len(nidx)} perturbaciones ({sum(1 for x in nidx if x[3])} sobre publicados, "
       f"{sum(1 for x in nidx if not x[3])} inyectadas); las que NO cambian la publicacion: {fallo_nulo}")

    # ---------------------------------------------------------------- control 1: K = produccion
    dpub = [(i, obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["pub_prod"], pub(i, "K")) for i in oks
            if bool(obj[i]["pub_prod"]) != pub(i, "K")]
    dvrp = []
    for i in oks:
        kv = ((res[i]["brazos"]["K"]["record"] or {}).get("primary_cluster") or {}).get("vrp_mw")
        pvv = obj[i].get("pc_vrp")
        if not ((kv is None and pvv is None) or (kv is not None and pvv is not None and abs(kv - pvv) <= 0.001)):
            dvrp.append((i, obj[i]["volcan"], obj[i]["hora_utc"], pvv, kv))
    pr(f"== control 1 (K = produccion) sobre {len(oks)} ok: publica distinto {len(dpub)} {dpub[:20]} | "
       f"pc.vrp_mw distinto {len(dvrp)} {dvrp[:20]}")

    # ---------------------------------------------------------------- control 2: oraculo = N
    if a.n_art:
        rn = {}
        for d in a.n_art:
            for f in sorted(Path(d).rglob("*resultados_*.json")):
                for r in json.loads(f.read_text(encoding="utf-8")):
                    if r.get("estado") == "ok":
                        rn[(r["volcan"], r["hora_utc"])] = r
        comp, dif = 0, []
        for i in oks:
            k = (obj[i]["volcan"], obj[i]["hora_utc"])
            if k not in rn or not rn[k].get("oraculo"):
                continue
            for c in CAJAS:
                if c not in rn[k]["oraculo"]:
                    continue
                comp += 1
                x, y = res[i]["oraculo"][c], rn[k]["oraculo"][c]
                vx, vy_ = x.get("vrp_mw"), y.get("vrp_mw")
                if x.get("npix") != y.get("npix") or ((vx is None) != (vy_ is None)) or \
                        (vx is not None and abs(vx - vy_) > 1e-6):
                    dif.append((i, k, c, x.get("npix"), vx, y.get("npix"), vy_))
        pr(f"== control 2 (oraculo = N): {comp} comparaciones (pasada x caja) en "
           f"{len({(obj[i]['volcan'], obj[i]['hora_utc']) for i in oks} & set(rn))} pasadas; distintas {len(dif)} {dif[:20]}")

    # ---------------------------------------------------------------- control 4: control positivo
    dec = [i for i in oks if obj[i]["lab"] == "pos" and obj[i]["decide"]]
    for c in CAJAS:
        det = [i for i in dec if res[i]["oraculo"][c].get("npix")]
        raz = [res[i]["oraculo"][c]["vrp_mw"] / obj[i]["mirova_vrp"] for i in det
               if obj[i].get("mirova_vrp") and res[i]["oraculo"][c].get("vrp_mw") is not None]
        q = np.percentile(raz, [25, 50, 75]) if raz else [None] * 3
        pr(f"== control 4 {NOM[c]}: detecta {len(det)} de {len(dec)} alertas que deciden "
           f"(protegidas {sum(1 for i in det if obj[i]['protegida'])} de {sum(1 for i in dec if obj[i]['protegida'])}); "
           f"razon O/MIROVA mediana {q[1]:.3f} [{q[0]:.3f}, {q[2]:.3f}] n {len(raz)}; "
           f"entre 0,8 y 1,25: {sum(1 for x in raz if 0.8 <= x <= 1.25)}")

    # ---------------------------------------------------------------- conteo pre-registrado
    neg_all = [i for i in obj if obj[i]["lab"] == "neg_limpio"]
    neg = [i for i in oks if obj[i]["lab"] == "neg_limpio"]
    neg_sin = [i for i in sin if obj[i]["lab"] == "neg_limpio"]
    neg_fuera = [i for i in fuera if obj[i]["lab"] == "neg_limpio"]
    prot = [i for i in obj if obj[i]["lab"] == "pos" and obj[i]["decide"] and obj[i]["protegida"]]
    mb = [i for i in obj if obj[i]["lab"] == "pos" and obj[i]["decide"] and not obj[i]["protegida"]]
    resumen = {"ventana": "V750 nocturno 2026-04-01 a 2026-10-21 sin 10-18 y 10-19", "n_obj": len(obj),
               "ok": len(oks), "fuera": len(fuera), "sin_dato": len(sin), "cajas": {}}
    filas_pub = []
    for c in list(CAJAS) + [c + "|volcan" for c in CAJAS]:
        nombre = NOM[c.split("|")[0]] + (" (distancia desde volcanoes.yaml)" if "|" in c else "")
        pK = sum(pub(i, "K") for i in neg)
        pO = sum(pub(i, c) for i in neg)
        enc = [i for i in neg if pub(i, c) and not pub(i, "K")]
        apa = [i for i in neg if pub(i, "K") and not pub(i, c)]
        # alertas: las fuera del granulo cuentan como no publicadas por los dos (no miran el volcan)
        okp = lambda i: i in oks
        prot_perd = [i for i in prot if okp(i) and pub(i, "K") and not pub(i, c)]
        prot_gan = [i for i in prot if okp(i) and pub(i, c) and not pub(i, "K")]
        mb_fnK = sum(1 for i in mb if okp(i) and not pub(i, "K"))
        mb_fnO = sum(1 for i in mb if okp(i) and not pub(i, c))
        mb_gan = [i for i in mb if okp(i) and pub(i, c) and not pub(i, "K")]
        mb_per = [i for i in mb if okp(i) and pub(i, "K") and not pub(i, c)]
        sin_mb = [i for i in mb if i in sin]
        sin_prot = [i for i in prot if i in sin]
        dE = (mb_fnO + pO) - (mb_fnK + pK)
        lo = dE - len(sin_mb)          # alertas SIN DATO todas ganadas, negativos SIN DATO ninguno encendido
        hi = dE + len(neg_sin)         # negativos SIN DATO todos encendidos, alertas SIN DATO ninguna ganada
        if prot_perd:
            et = "PIERDE PROTEGIDAS"
        elif hi < 0:
            et = "GANA EN EL CENSO"
        elif lo > 0:
            et = "PIERDE"
        else:
            et = "SIN RESOLVER"
        pr(f"== {nombre}")
        pr(f"   negativos limpios publicados: K {pK} de {len(neg)} ok ({pK / len(neg):.2%}); O {pO} ({pO / len(neg):.2%}) "
           f"| denominador poblacion {len(neg_all)} (ok {len(neg)}, fuera {len(neg_fuera)}, SIN DATO {len(neg_sin)})")
        pr(f"   encendidos {len(enc)}, apagados {len(apa)}")
        pr(f"   protegidas (de {len(prot)}, ok {sum(1 for i in prot if okp(i))}): perdidas {len(prot_perd)} "
           f"{[(obj[i]['volcan'], obj[i]['hora_utc'], obj[i]['mirova_vrp']) for i in prot_perd]} | ganadas {len(prot_gan)} "
           f"| SIN DATO {len(sin_prot)} {[(obj[i]['volcan'], obj[i]['hora_utc']) for i in sin_prot]}")
        pr(f"   bajo 1 MW (de {len(mb)}, ok {sum(1 for i in mb if okp(i))}): sin publicar K {mb_fnK}, O {mb_fnO}; "
           f"ganadas {len(mb_gan)}, perdidas {len(mb_per)}; SIN DATO {len(sin_mb)}")
        pr(f"   dE = ({mb_fnO} + {pO}) - ({mb_fnK} + {pK}) = {dE:+d}  (rango por SIN DATO {lo:+d} a {hi:+d}) -> {et}")
        resumen["cajas"][nombre] = {"neg_pub_K": pK, "neg_pub_O": pO, "neg_ok": len(neg), "neg_pob": len(neg_all),
                                    "encendidos": len(enc), "apagados": len(apa), "prot_perdidas": len(prot_perd),
                                    "prot_ganadas": len(prot_gan), "mb_fn_K": mb_fnK, "mb_fn_O": mb_fnO,
                                    "mb_ganadas": len(mb_gan), "mb_perdidas": len(mb_per), "dE": dE,
                                    "dE_rango": [lo, hi], "etiqueta": et}
        if "|" in c:
            continue
        # desgloses
        for eje, f in (("volcan", lambda i: obj[i]["volcan"]), ("estrato_z", lambda i: obj[i]["estrato_z"]),
                       ("tramo_z", lambda i: tramo_z(obj[i].get("z"))), ("partida", lambda i: partida(res.get(i) or {})),
                       ("satelite", lambda i: obj[i]["sensor"])):
            g = collections.defaultdict(list)
            for i in neg + neg_fuera:
                g[f(i)].append(i)
            pr(f"   por {eje}: " + " | ".join(
                f"{k}: K {sum(pub(i, 'K') for i in v if i in oks)} O {sum(pub(i, c) for i in v if i in oks)} "
                f"de {len(v)}" for k, v in sorted(g.items())))
        sinfuera = [i for i in neg if partida(res[i]) not in ("fuera", "sin_crater")]
        pr(f"   sin 'fuera' ni 'sin crater': K {sum(pub(i, 'K') for i in sinfuera)} O {sum(pub(i, c) for i in sinfuera)} "
           f"de {len(sinfuera)}")
        for i in neg:
            if pub(i, c) or pub(i, "K"):
                oo = res[i]["oraculo"][c]
                rec = record_oraculo(oo, inner[obj[i]["volcan"]], obj[i]["sensor"])
                filas_pub.append({"caja": NOM[c], "id": i, "volcan": obj[i]["volcan"], "hora_utc": obj[i]["hora_utc"],
                                  "sensor": obj[i]["sensor"], "z": obj[i]["z"], "pub_K": int(pub(i, "K")),
                                  "pub_O": int(pub(i, c)), "K_pc_vrp": obj[i]["pc_vrp"], "O_npix": oo.get("npix"),
                                  "O_vrp": oo.get("vrp_mw"), "O_banda": oo.get("vrp_banda"),
                                  "O_dist": (rec.get("primary_cluster") or {}).get("centroid_dist_km"),
                                  "O_tmax": rec.get("t_max_k"), "partida": partida(res[i]),
                                  "en_n": obj[i]["en_n"], "dc_prod": obj[i]["dc"]})
        lista = [x for x in filas_pub if x["caja"] == NOM[c] and x["pub_O"]]
        pr(f"   negativos que publica {NOM[c]} ({len(lista)}):")
        for x in sorted(lista, key=lambda x: (x["volcan"], x["hora_utc"])):
            amb = x["O_banda"] and x["O_banda"][0] <= 0 < x["O_banda"][1]
            pr(f"     {x['id']} {x['volcan']} {x['hora_utc']} z {x['z']} O {x['O_npix']} px {x['O_vrp']:.3f} MW "
               f"a {x['O_dist']} km Tmax {x['O_tmax']:.1f} | K pub {x['pub_K']} pc {x['K_pc_vrp']} | {x['partida']}"
               f"{' | AMBIGUA banda ' + str([round(b, 3) for b in x['O_banda']]) if amb else ''} | en N {x['en_n']}")
    # alertas sólo OCR (no deciden)
    ocr = [i for i in oks if obj[i]["lab"] == "pos" and not obj[i]["decide"]]
    pr("== alertas solo OCR antes del 06-13 (no deciden):", len(ocr), "| K", sum(pub(i, "K") for i in ocr),
       "| O-def", sum(pub(i, "geo_linear") for i in ocr), "| O-sens", sum(pub(i, "geo_linear_anillo_sensible") for i in ocr))
    # SIN DATO detallado
    pr("== SIN DATO:", [(i, obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["lab"], obj[i]["protegida"],
                          (res.get(i) or {}).get("estado", "sin_resultado")[:80]) for i in sin])
    pr("== fuera del granulo:", [(i, obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["lab"],
                                  round((res.get(i) or {}).get("dist_min_km") or -1, 1)) for i in fuera])
    suf = a.salida
    (AQUI / f"02_analizar_salida{suf}.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    (AQUI / f"resumen{suf}.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(AQUI / f"negativos_publicados{suf}.csv", "w", newline="", encoding="utf-8") as fh:
        if filas_pub:
            w = csv.DictWriter(fh, fieldnames=list(filas_pub[0]))
            w.writeheader()
            w.writerows(filas_pub)
    # tabla por pasada (compacta)
    with open(AQUI / f"tabla_por_pasada{suf}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "volcan", "hora_utc", "lab", "decide", "protegida", "mirova_vrp", "z", "pub_prod", "estado",
                    "partida", "pub_K", "K_pc_vrp", "Odef_npix", "Odef_vrp", "pub_Odef", "Osens_npix", "Osens_vrp",
                    "pub_Osens"])
        for i in sorted(obj):
            o, r = obj[i], res.get(i) or {}
            oc = r.get("oraculo") or {}
            kk = (((r.get("brazos") or {}).get("K") or {}).get("record") or {})
            w.writerow([i, o["volcan"], o["hora_utc"], o["lab"], o["decide"], o["protegida"], o.get("mirova_vrp"),
                        o.get("z"), o["pub_prod"], r.get("estado", "sin_resultado")[:40], partida(r),
                        int(pub(i, "K")) if i in oks else "", (kk.get("primary_cluster") or {}).get("vrp_mw"),
                        (oc.get("geo_linear") or {}).get("npix"), (oc.get("geo_linear") or {}).get("vrp_mw"),
                        int(pub(i, "geo_linear")) if i in oks else "",
                        (oc.get("geo_linear_anillo_sensible") or {}).get("npix"),
                        (oc.get("geo_linear_anillo_sensible") or {}).get("vrp_mw"),
                        int(pub(i, "geo_linear_anillo_sensible")) if i in oks else ""])


if __name__ == "__main__":
    main()
