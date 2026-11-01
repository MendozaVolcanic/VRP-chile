# -*- coding: utf-8 -*-
"""S159 frente N, paso 3: lee los artefactos del workflow y calcula lo pre-registrado en PREREGISTRO_N.md.

Orden (pre-registro §7): primero cobertura, nulo, K contra producción, contadores y controles positivos; recién
después el veredicto por brazo. «Publica» = predicado del tablero ejecutado con node (banco_paridad.correr_node) sobre
el record que escribió store.append_record para ese brazo.

Las dos preguntas del instrumento.
P1 (si un brazo estuviera roto, ¿se vería?): los contadores de reemplazo y el control positivo de F (Láscar 10-08,
K = 0,0 MW) tienen que mostrar efecto; si F no cambiara nada en ninguna pasada, la tabla de cambios lo dice.
P2 (instrumento muerto): pasadas sin estado ok se cuentan aparte (SIN DATO) y nunca entran al denominador; K2 contra K
mide que el instrumento da idéntico consigo mismo; K contra el record publicado mide que el envoltorio es producción.
Uso: python 03_analizar.py --art D:\\vrp-trabajo\\temporales\\s159_n\\run_<id> [--out sufijo]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import random
import statistics
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402

BRAZOS = ("K", "K2", "C", "F", "FC")
SEM = 159
NBOOT = 2000


def slim(rec):
    keep = {k: rec.get(k) for k in B.CAMPOS_JS if k != "anomaly_pixels"}
    keep["anomaly_pixels"] = []
    return keep


def pub_oraculo(o, inner):
    if not o or not o.get("npix") or (o.get("vrp_mw") or 0) <= 0:
        return False
    px = max(o["pixeles"], key=lambda p: p[4])
    return px[3] <= inner


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True, nargs="+")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    obj = {o["id"]: o for o in json.loads((AQUI / "objetivos_n.json").read_text(encoding="utf-8"))}
    res = {}
    for d in a.art:
        for f in sorted(Path(d).rglob("resultados_*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                if r.get("estado") == "ok" or r["id"] not in res:   # un redisparo ok reemplaza a un SIN DATO
                    res[r["id"]] = r
    inner = B.inner_desde_html()
    L = []
    pr = lambda *x: (print(*x), L.append(" ".join(str(y) for y in x)))

    # ---------------- 1. cobertura
    pr("== 1. cobertura (A108): objetivos", len(obj), "| con resultado", len(res))
    cob = collections.defaultdict(collections.Counter)
    for i, o in obj.items():
        r = res.get(i)
        est = "sin_resultado" if r is None else r.get("estado", "?")
        if est == "ok" and o["clase"] != "diurna":
            br = r.get("brazos") or {}
            if any("error" in (br.get(b) or {"error": 1}) for b in BRAZOS):
                est = "ok_con_error_en_brazo"
        cob[o["clase"]][est] += 1
    for k, c in sorted(cob.items()):
        pr(f"   {k:10s}", dict(c))
    sin = [(i, obj[i]["volcan"], obj[i]["hora_utc"], (res.get(i) or {}).get("estado", "sin_resultado"))
           for i in obj if (res.get(i) or {}).get("estado") != "ok"]
    pr("   SIN DATO (sin contar las que no tienen resultado):", [x for x in sin if x[3] != "sin_resultado"])
    pr("   sin resultado:", sum(1 for x in sin if x[3] == "sin_resultado"))

    # ---------------- 2. predicado con node para todos los brazos (y bandas de F/FC)
    casos, idx = [], []
    for i, r in res.items():
        if r.get("estado") != "ok" or not r.get("brazos"):
            continue
        v = obj[i]["volcan"]
        for b in BRAZOS:
            x = r["brazos"].get(b) or {}
            rec = x.get("record")
            if rec is None:
                continue
            casos.append([slim(rec), inner[v]])
            idx.append((i, b, "c"))
            if b in ("F", "FC") and x.get("F_pc_banda") and rec.get("primary_cluster"):
                for nm, val in (("lo", x["F_pc_banda"][0]), ("hi", x["F_pc_banda"][1])):
                    s = slim(rec)
                    s["primary_cluster"] = dict(s["primary_cluster"], vrp_mw=round(val, 3))
                    casos.append([s, inner[v]])
                    idx.append((i, b, nm))
    pred = B.correr_node(casos) if casos else []
    P = {}
    for (i, b, nm), p in zip(idx, pred):
        P[(i, b, nm)] = bool(p[4])

    def pub(i, b, modo="c"):
        """modo c = central; lo/hi = extremos de la banda (sólo F y FC); sin banda, el central."""
        if (i, b, "c") not in P:
            return False   # record None: calculate_vrp no devolvió nada = no publica
        if modo != "c" and (i, b, modo) in P:
            return P[(i, b, modo)]
        return P[(i, b, "c")]

    ok = [i for i, r in res.items() if r.get("estado") == "ok" and r.get("brazos")
          and all("error" not in (r["brazos"].get(b) or {"error": 1}) for b in BRAZOS)]
    pr("== 2. pasadas con los cinco brazos ok:", len(ok))

    # ---------------- 3. nulo K2 = K
    dif = [i for i in ok if json.dumps(res[i]["brazos"]["K"]["record"], sort_keys=True)
           != json.dumps(res[i]["brazos"]["K2"]["record"], sort_keys=True)]
    pr("== 3. nulo: K2 distinto de K en", len(dif), "de", len(ok), dif[:10])

    # ---------------- 4. K contra el record publicado en data/
    d_pub, d_vrp = [], []
    for i in ok:
        o = obj[i]
        if o.get("pub_prod") is None:
            continue
        k = res[i]["brazos"]["K"]["record"] or {}
        kv = (k.get("primary_cluster") or {}).get("vrp_mw")
        if pub(i, "K") != bool(o["pub_prod"]):
            d_pub.append((i, o["volcan"], o["hora_utc"], o["pub_prod"], pub(i, "K"), o["pc_vrp"], kv))
        if not ((kv is None and o["pc_vrp"] is None) or (kv is not None and o["pc_vrp"] is not None
                                                          and abs(kv - o["pc_vrp"]) <= 0.001)):
            d_vrp.append((i, o["volcan"], o["hora_utc"], o["pc_vrp"], kv))
    pr("== 4. K contra produccion: publica distinto en", len(d_pub), d_pub[:10])
    pr("   pc.vrp_mw distinto (>0,001 MW) en", len(d_vrp), d_vrp[:15])

    # ---------------- 5. contadores y control positivo de F
    sin_fondo = [i for i in ok if (res[i]["brazos"]["K"].get("n_hot") or 0) > 0
                 and not ((res[i]["brazos"]["F"].get("contadores") or {}).get("fondo"))]
    sin_rec = [i for i in ok if (res[i]["brazos"]["K"].get("n_hot") or 0) > 0
               and not ((res[i]["brazos"]["F"].get("contadores") or {}).get("proxy_recortes"))]
    sin_comp = [i for i in ok if not ((res[i]["brazos"]["C"].get("contadores") or {}).get("compuerta"))]
    pr("== 5. contadores: F sin fondo con K alertado", sin_fondo[:10], "| F sin recorte evitado", sin_rec[:10],
       "| C sin compuerta", sin_comp[:10])
    # F central post-hoc contra el pc del pipeline (antes de store)
    dc = [(i, res[i]["brazos"]["F"].get("F_pc_central"), (res[i]["brazos"]["F"].get("crudo_pc") or {}).get("vrp_mw"))
          for i in ok if res[i]["brazos"]["F"].get("F_pc_central") is not None]
    malo = [x for x in dc if x[2] is None or abs(round(x[1], 3) - x[2]) > 0.0015]
    pr("   F: magnitud post-hoc contra la del pipeline, distintas en", len(malo), "de", len(dc), malo[:5])
    cambia = {b: sum(1 for i in ok if json.dumps((res[i]["brazos"][b]["record"] or {}).get("primary_cluster"),
                                                  sort_keys=True)
                     != json.dumps((res[i]["brazos"]["K"]["record"] or {}).get("primary_cluster"), sort_keys=True))
              for b in ("C", "F", "FC")}
    pr("   pasadas donde el cumulo cambia respecto de K:", cambia)
    for i in ok:
        o = obj[i]
        if (o["volcan"], o["hora_utc"]) == ("Lascar", "2026-10-08 05:42"):
            pr("   control positivo F, Lascar 10-08 05:42: K pc", (res[i]["brazos"]["K"]["record"] or {}).get(
                "primary_cluster"), "| F pc", (res[i]["brazos"]["F"]["record"] or {}).get("primary_cluster"),
               "banda", res[i]["brazos"]["F"].get("F_pc_banda"))

    # ---------------- 6. control positivo del oráculo (grilla vieja R2, lineal) y efecto de la grilla de GEO
    pr("== 6. oraculo")
    esperado = {("Lascar", "2026-10-08 05:42"): (1, 0.33), ("NevadosDeChillan", "2026-10-10 05:54"): (5, 12.37),
                ("Villarrica", "2026-09-19 05:48"): (2, 0.47)}
    for i, r in res.items():
        o = obj[i]
        key = (o["volcan"], o["hora_utc"])
        orc = r.get("oraculo") or {}
        if key in esperado:
            x = orc.get("r2_linear", {})
            pr(f"   control {key}: esperado {esperado[key]} | r2_linear {x.get('npix')} px {x.get('vrp_mw')} "
               f"banda {x.get('vrp_banda')}")
        if key in esperado or key in (("Lascar", "2026-09-26 05:48"), ("Chaiten", "2026-10-06 05:30"),
                                      ("PuyehueCordonCaulle", "2026-10-10 05:54"),
                                      ("PuyehueCordonCaulle", "2026-10-16 05:42"), ("Tupungatito", "2026-08-21 05:48")):
            pr(f"   {key} MIROVA {o.get('mirova_vrp')} | " + " | ".join(
                f"{n} {v.get('npix')}px {None if v.get('vrp_mw') is None else round(v['vrp_mw'], 3)}"
                for n, v in orc.items()))

    # ---------------- 7. tabla por pasada
    filas = []
    for i in sorted(res):
        o, r = obj[i], res[i]
        br = r.get("brazos") or {}
        f = {"id": i, "volcan": o["volcan"], "hora_utc": o["hora_utc"], "clase": o["clase"], "peso": o["peso"],
             "protegida": o.get("protegida"), "decide": o.get("decide"), "z": o.get("z"),
             "mirova_vrp": o.get("mirova_vrp"), "prod_pc": o.get("pc_vrp"), "prod_pub": o.get("pub_prod"),
             "estado": r.get("estado"), "dayflag": r.get("dayflag")}
        for n in ("geo_linear", "geo_nearest", "geo_cubic", "r2_linear", "geo_linear_anillo_sensible"):
            x = (r.get("oraculo") or {}).get(n) or {}
            f[f"O_{n}_npix"] = x.get("npix")
            f[f"O_{n}_vrp"] = None if x.get("vrp_mw") is None else round(x["vrp_mw"], 4)
        f["O_pub"] = pub_oraculo((r.get("oraculo") or {}).get("geo_linear"), inner[o["volcan"]])
        f["O_banda"] = ((r.get("oraculo") or {}).get("geo_linear") or {}).get("vrp_banda")
        for b in BRAZOS:
            x = br.get(b) or {}
            pc = (x.get("record") or {}).get("primary_cluster") or {}
            f[f"{b}_pc"] = pc.get("vrp_mw")
            f[f"{b}_n"] = pc.get("n_pixels")
            f[f"{b}_dc"] = (x.get("record") or {}).get("distance_class")
            f[f"{b}_pub"] = pub(i, b) if i in ok else None
            f[f"{b}_n_primer_pase"] = x.get("pc_pix_primer_pase")
            if b in ("F", "FC"):
                f[f"{b}_banda"] = x.get("F_pc_banda")
                f[f"{b}_pub_lo"] = pub(i, b, "lo") if i in ok else None
                f[f"{b}_pub_hi"] = pub(i, b, "hi") if i in ok else None
        filas.append(f)
    sal = AQUI / f"tabla_por_pasada{a.out}.csv"
    with open(sal, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        w.writeheader()
        for f in filas:
            w.writerow({k: (json.dumps(v) if isinstance(v, list) else v) for k, v in f.items()})
    pr("== 7. tabla por pasada:", sal.name, len(filas), "filas")

    # ---------------- 8. veredicto por brazo (sólo si los controles 3 y 4 no fallan: se imprime igual, marcado)
    F = {f["id"]: f for f in filas}
    base = [i for i in ok if obj[i]["peso"] > 0]
    pr("== 8. veredicto (pasadas con peso > 0 y cinco brazos ok:", len(base), ")")
    if dif or d_pub:
        pr("   AVISO: controles 3 o 4 con diferencias; el veredicto queda condicionado a explicarlas")

    def estrato(i):
        o = obj[i]
        return o["clase"] if o["clase"] != "neg_resto" else f"neg_resto|{o['volcan']}|{o['estrato_z']}"

    def conteos(ids, b, modo, peso=None):
        """Cuentas ponderadas de la regla de MISSION para el brazo b (modo c/lo/hi) y para K."""
        c = collections.Counter()
        for i in ids:
            o = obj[i]
            w = o["peso"] if peso is None else peso[i]
            pk, px = pub(i, "K"), pub(i, b, modo)
            if o["lab"] == "pos":
                if not o["decide"]:
                    continue
                if o["protegida"]:
                    c["prot_perdidas"] += w * (pk and not px)
                    c["prot_ganadas"] += w * (px and not pk)
                    c["prot_n"] += w
                else:
                    c["mb_ganadas"] += w * (px and not pk)
                    c["mb_perdidas"] += w * (pk and not px)
                    c["mb_fn_K"] += w * (not pk)
                    c["mb_fn_X"] += w * (not px)
                    c["mb_n"] += w
            elif o["lab"] == "neg_limpio":
                c["neg_encendidos"] += w * (px and not pk)
                c["neg_apagados"] += w * (pk and not px)
                c["neg_pub_K"] += w * pk
                c["neg_pub_X"] += w * px
                c["neg_n"] += w
        c["E_K"] = c["mb_fn_K"] + c["neg_pub_K"]
        c["E_X"] = c["mb_fn_X"] + c["neg_pub_X"]
        c["dE"] = c["E_X"] - c["E_K"]
        return c

    grupos = collections.defaultdict(list)
    for i in base:
        grupos[estrato(i)].append(i)
    N_est = {}
    for i in base:
        N_est[estrato(i)] = obj[i]["peso"] * 0 + N_est.get(estrato(i), 0)
    # tamaño poblacional de cada estrato = peso x n (el peso ya es N/n del estrato)
    Npop = {k: sum(obj[i]["peso"] for i in v) for k, v in grupos.items()}
    rng = random.Random(SEM)
    resumen = {}
    for b in ("C", "F", "FC", "K2"):
        cs = {m: conteos(base, b, m) for m in ("c", "lo", "hi")}
        boots = []
        for _ in range(NBOOT):
            ids, peso = [], {}
            for k, v in grupos.items():
                if k in ("pos_nopub", "pos_prot", "neg_pub"):
                    elegido = v
                else:
                    elegido = [rng.choice(v) for _ in v]
                for i in elegido:
                    ids.append(i)
                    peso[i] = peso.get(i, 0) + Npop[k] / len(v)
            boots.append(conteos(list(dict.fromkeys(ids)), b, "c", peso)["dE"])
        boots.sort()
        ic = (boots[int(0.025 * NBOOT)], boots[int(0.975 * NBOOT) - 1])
        c = cs["c"]
        dEs = [cs[m]["dE"] for m in ("c", "lo", "hi")]
        if c["prot_perdidas"] > 0:
            ver = "PIERDE PROTEGIDA"
        elif all(x < 0 for x in dEs):
            ver = "GANA"
        elif all(x > 0 for x in dEs):
            ver = "ENCIENDE DE MAS"
        elif all(x == 0 for x in dEs):
            ver = "EMPATE"
        else:
            ver = "AMBIGUO"
        if ver in ("GANA", "ENCIENDE DE MAS") and ic[0] <= 0 <= ic[1]:
            ver += " (no resuelto por este lote)"
        resumen[b] = {"veredicto": ver, "dE_central": round(c["dE"], 2), "dE_banda": [round(x, 2) for x in dEs],
                      "ic95_dE": [round(ic[0], 2), round(ic[1], 2)],
                      **{k: round(v, 2) for k, v in c.items()}}
        pr(f"   {b}: {ver} | dE {c['dE']:.1f} (banda {[round(x, 1) for x in dEs]}, IC95 {ic[0]:.1f} a {ic[1]:.1f}) | "
           f"prot perdidas {c['prot_perdidas']:.0f} ganadas {c['prot_ganadas']:.0f} de {c['prot_n']:.0f} | "
           f"bajo 1 MW ganadas {c['mb_ganadas']:.1f} perdidas {c['mb_perdidas']:.1f} de {c['mb_n']:.1f} | "
           f"neg encendidos {c['neg_encendidos']:.1f} apagados {c['neg_apagados']:.1f} de {c['neg_n']:.1f} "
           f"(K publica {c['neg_pub_K']:.1f}, X {c['neg_pub_X']:.1f})")
    # crudo (sin pesos) por clase
    pr("   muestra cruda (sin pesos), publica por clase y brazo:")
    for cl in ("pos_nopub", "pos_prot", "pos_resto", "neg_pub", "neg_resto"):
        ids = [i for i in ok if obj[i]["clase"] == cl]
        pr(f"     {cl:9s} n={len(ids):3d} " + " ".join(f"{b}={sum(pub(i, b) for i in ids)}" for b in BRAZOS)
           + " O=" + str(sum(F[i]["O_pub"] for i in ids)))
    # por estrato: volcán y cenit
    pr("   por volcan y cenit (crudo): pos publicadas K/C/F/FC/O y neg publicadas K/C/F/FC/O")
    for v in sorted({obj[i]["volcan"] for i in ok}):
        for z in ("z<=40", "z>40"):
            ids = [i for i in ok if obj[i]["volcan"] == v and obj[i].get("estrato_z") == z]
            if not ids:
                continue
            ps = [i for i in ids if obj[i]["lab"] == "pos" and obj[i]["decide"]]
            ns = [i for i in ids if obj[i]["lab"] == "neg_limpio"]
            pr(f"     {v:20s} {z:5s} pos {len(ps):3d}: " + "/".join(str(sum(pub(i, b) for i in ps))
                                                             for b in ("K", "C", "F", "FC"))
               + f"/{sum(F[i]['O_pub'] for i in ps)}  neg {len(ns):3d}: "
               + "/".join(str(sum(pub(i, b) for i in ns)) for b in ("K", "C", "F", "FC"))
               + f"/{sum(F[i]['O_pub'] for i in ns)}")
    # tramo A119 y sólo OCR
    for et, cond in (("antes 06-13", lambda o: o["hora_utc"] < "2026-06-13"),
                     ("desde 06-13", lambda o: o["hora_utc"] >= "2026-06-13")):
        ps = [i for i in ok if obj[i]["lab"] == "pos" and obj[i]["decide"] and cond(obj[i])]
        pr(f"   tramo {et}: pos {len(ps)} publicadas " + " ".join(f"{b}={sum(pub(i, b) for i in ps)}"
                                                                 for b in ("K", "C", "F", "FC")))
    ocr = [i for i in ok if obj[i]["lab"] == "pos" and not obj[i]["decide"]]
    pr("   alertas solo OCR antes de 06-13 (no deciden):", len(ocr), " ".join(
        f"{b}={sum(pub(i, b) for i in ocr)}" for b in ("K", "C", "F", "FC")))

    # ---------------- 9. magnitud
    pr("== 9. razon de magnitud brazo / MIROVA en alertas que el brazo publica (mediana [q1, q3], n)")

    def q(xs):
        xs = sorted(xs)
        if not xs:
            return "sin datos"
        n = len(xs)
        return f"{statistics.median(xs):.3f} [{xs[n // 4]:.3f}, {xs[(3 * n) // 4]:.3f}] n={n}"
    for b in ("K", "C", "F", "FC", "placebo"):
        for et, cond in (("todas", lambda i: True), ("1 px", lambda i: (F[i]["K_n"] or 0) == 1 if b in ("K", "placebo")
                                                    else (F[i][f"{b}_n"] or 0) == 1),
                         ("2+ px", lambda i: (F[i]["K_n"] or 0) >= 2 if b in ("K", "placebo")
                          else (F[i][f"{b}_n"] or 0) >= 2)):
            bb = "K" if b == "placebo" else b
            xs = [(F[i][f"{bb}_pc"] * (1.2 if b == "placebo" else 1.0)) / obj[i]["mirova_vrp"]
                  for i in ok if obj[i]["lab"] == "pos" and obj[i]["decide"] and pub(i, bb)
                  and obj[i]["mirova_vrp"] and cond(i)]
            pr(f"   {b:8s} {et:6s} {q(xs)}")
    xs = [((F[i]["O_geo_linear_vrp"] or 0) / obj[i]["mirova_vrp"]) for i in ok
          if obj[i]["lab"] == "pos" and obj[i]["decide"] and F[i]["O_pub"] and obj[i]["mirova_vrp"]]
    pr(f"   O        todas  {q(xs)}")
    # banda de F en un píxel
    an = [(i, obj[i]["volcan"], obj[i]["hora_utc"], F[i]["F_banda"]) for i in ok
          if F[i].get("F_pub_lo") != F[i].get("F_pub_hi")]
    pr("   F ambiguas (la banda cruza el predicado):", len(an), an[:10])

    # ---------------- 10. VA-1: de dónde salen los píxeles del cúmulo
    pr("== 10. VA-1: cumulos con pixeles solo del segundo pase (por brazo, pasadas ok)")
    for b in ("K", "C", "F", "FC"):
        tot = [i for i in ok if (F[i][f"{b}_n"] or 0) > 0]
        solo2 = [i for i in tot if F[i][f"{b}_n_primer_pase"] == 0]
        cero = [i for i in tot if (F[i][f"{b}_pc"] or 0) == 0]
        cero2 = [i for i in cero if F[i][f"{b}_n_primer_pase"] == 0]
        pr(f"   {b}: con cumulo {len(tot)}, sin pixel del primer pase {len(solo2)}; en 0,0 MW {len(cero)} "
           f"(de ellos sin primer pase {len(cero2)})")

    (AQUI / f"resumen{a.out}.json").write_text(json.dumps(resumen, indent=1, ensure_ascii=False), encoding="utf-8")
    (AQUI / f"03_analizar{a.out}_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
