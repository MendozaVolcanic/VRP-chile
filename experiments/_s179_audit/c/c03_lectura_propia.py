# -*- coding: utf-8 -*-
"""Frente C, auditoria S179. Instrumento c03: lectura propia de F26 (P1, P2, magnitud) y poder de los controles.

Lee la tabla por pasada de c02 (no importa leer_retro.py ni sus reglas). Implementacion propia de:
  * P1: protegidas de la tabla que K publica y la via no.
  * P2: prueba de signos por bloque noche-volcan (D-45), EXACTA por convolucion para cualquier B (el lector sortea
    10.000 signos cuando B > 20; aqui se enumera), con el corte SIN SUSTRATO B <= 4 y el 5 % por cola.
  * Magnitud: razon via/MIROVA y K/MIROVA, d y d' (ganancia uniforme descontada) con bootstrap por bloque propio.
  * C-K propio: K-gemelo contra K de disco con el criterio sellado (publica y pc.vrp_mw a 0,001) y con campos de mas.
  * Cobertura del K-gemelo sobre las pasadas que deciden P2 y P1.
  * Sorteo de etiquetas del §7 con la lectura aprobada en S174 (la via contra K con etiquetas barajadas por estrato).
  * Noche del operador (§5.5): denominadores.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si P1 o P2 del lector estuvieran rotos, esta medicion lo veria? Si: recalcula B, neto y el estado desde las
   pasadas, y se compara contra lectura.json al final (seccion COMPARACION). Limite: mide el brazo radiante (el
   record tal cual); el brazo cercano de VIIRS 375 usa la regla sellada de V375-E y aqui no se reimplementa.
2. Si este instrumento estuviera muerto? Controles positivos: (a) un brazo MUDO (nunca publica) TIENE que dar P1
   con todas las protegidas perdidas; (b) el brazo K contra K TIENE que dar B = 0; (c) el placebo K x 1,2 TIENE
   que dar d' = 0. Se imprimen.

Uso: python c03_lectura_propia.py TABLA.json [LECTURA.json]
"""
import collections
import json
import math
import statistics
import sys
from datetime import datetime

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
DECIDE = {"MODIS": "F26-M", "VIIRS375": "F26-V", "VIIRS750": "F26-V"}
# §3.1 (b) del pre-registro sellado (l. 146 a 162). MODIS trae hora; VIIRS 750 de febrero trae SOLO la fecha.
B_MODIS = [("Lascar", "2026-02-11 01:20"), ("Lascar", "2026-02-11 07:00"), ("Lascar", "2026-02-16 01:20"),
           ("Lastarria", "2026-02-24 07:05")]
B_V750_FECHA = [("Lascar", "2026-02-04"), ("Lascar", "2026-02-05"), ("Lascar", "2026-02-12"), ("Lascar", "2026-02-21"),
                ("Lascar", "2026-02-25"), ("Lascar", "2026-02-26"), ("Isluga", "2026-02-26"),
                ("PuyehueCordonCaulle", "2026-02-01"), ("Tupungatito", "2026-02-26"), ("Lascar", "2026-03-11")]
# las horas que puso el lector (PASADAS_B de leer_retro.py l. 167 a 179), para comparar con la lectura por fecha
B_V750_HORA_LECTOR = [("Lascar", "2026-02-04 05:54"), ("Lascar", "2026-02-05 05:36"), ("Lascar", "2026-02-12 06:24"),
                      ("Lascar", "2026-02-21 05:12"), ("Lascar", "2026-02-25 06:00"), ("Lascar", "2026-02-26 05:42"),
                      ("Isluga", "2026-02-26 05:36"), ("PuyehueCordonCaulle", "2026-02-01 05:12"),
                      ("Tupungatito", "2026-02-26 05:42"), ("Lascar", "2026-03-11 06:18")]


def _t(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def cerca(f, lista):
    return any(f["vol"] == v and abs((_t(f["dt"]) - _t(h)).total_seconds()) <= 120 for v, h in lista)


def signos(sumas, neto):
    """Prueba de signos por bloque, exacta: cada bloque cambia de signo con probabilidad 1/2."""
    dist = {0: 1}
    for x in sumas:
        nueva = collections.Counter()
        for v, k in dist.items():
            nueva[v + x] += k
            nueva[v - x] += k
        dist = nueva
    den = 2 ** len(sumas)
    return (sum(k for v, k in dist.items() if v <= neto), sum(k for v, k in dist.items() if v >= neto), den)


def estado_p2(sumas):
    B, neto = len(sumas), sum(sumas)
    g, p, den = signos(sumas, neto)
    if B <= 4:
        e = "SIN SUSTRATO"
    elif neto < 0 and 20 * g <= den:
        e = "GANA"
    elif neto > 0 and 20 * p <= den:
        e = "PIERDE"
    elif neto > 0:
        e = "BLOQUEA"
    else:
        e = "EMPATE"
    return e, B, neto, g / den, p / den


def err(f, pub, lejana=False):
    if f["lab"] == "bajo1":
        return pub == 0
    if f["lab"] == "neg_limpio":
        return pub == 1
    if lejana and f["lab"] == "far_ref":
        return pub == 1
    return False


def p2(filas, a="pub_V", r="pub_K", lejana=False, lab=None):
    por = collections.Counter()
    disc = []
    for f in filas:
        if lab is not None:
            f = dict(f, lab=lab[id(f)]) if False else f
        ea, er = err(f, f[a], lejana), err(f, f[r], lejana)
        if ea != er:
            por[f["vol"] + "|" + f["noche"]] += 1 if ea else -1
            disc.append(f)
    sumas = [por[k] for k in sorted(por)]
    return estado_p2(sumas) + (disc, dict(por))


def p1(filas, a="pub_V", r="pub_K"):
    return ([f for f in filas if f["lab"] == "protegida" and f[r] == 1 and f[a] == 0],
            [f for f in filas if f["lab"] == "protegida" and f[r] == 0 and f[a] == 0],
            [f for f in filas if f["lab"] == "protegida" and f[r] == 0 and f[a] == 1])


def magnitud(filas, a="mag_V", pa="pub_V", semilla=179, n_boot=4000):
    P = [f for f in filas if f["lab"] in ("protegida", "bajo1") and f["pub_K"] == 1 and f[pa] == 1
         and f["mag_K"] > 0 and f[a] > 0 and (f.get("mir") or 0) > 0]
    if not P:
        return {"n": 0}
    lk = np.array([math.log10(f["mag_K"] / f["mir"]) for f in P])
    ld = np.array([math.log10(f[a] / f["mir"]) for f in P])
    d = np.abs(ld) - np.abs(lk)
    g = float(np.median(ld - lk))
    dp = np.abs(ld) - np.abs(lk + g)
    bloques = sorted({f["vol"] + "|" + f["noche"] for f in P})
    ib = np.array([bloques.index(f["vol"] + "|" + f["noche"]) for f in P])
    rng = np.random.default_rng(semilla)
    md, mdp = [], []
    for _ in range(n_boot):
        el = rng.integers(0, len(bloques), size=len(bloques))
        w = np.bincount(el, minlength=len(bloques))[ib]
        sel = np.repeat(np.arange(len(P)), w)
        if len(sel) == 0:
            continue
        gb = float(np.median((ld - lk)[sel]))
        md.append(float(np.median(d[sel])))
        mdp.append(float(np.median((np.abs(ld) - np.abs(lk + gb))[sel])))
    ic = lambda x: [round(float(np.percentile(x, 2.5)), 4), round(float(np.percentile(x, 97.5)), 4)]
    return {"n": len(P), "bloques": len(bloques), "razon_a_mediana": round(float(np.median(10 ** ld)), 4),
            "razon_K_mediana": round(float(np.median(10 ** lk)), 4), "ganancia_g": round(10 ** g, 4),
            "d_mediana": round(float(np.median(d)), 4), "d_ic95": ic(md), "dprima_mediana": round(float(np.median(dp)), 4),
            "dprima_ic95": ic(mdp), "dprima_max_abs": round(float(np.max(np.abs(dp))), 6),
            "por_volcan": dict(collections.Counter(f["vol"] for f in P))}


def main():
    tabla = json.load(open(sys.argv[1], encoding="utf-8"))
    lect = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 else None
    print("tabla:", sys.argv[1], "| pasadas:", len(tabla))
    print("estados de la via fuera de ok:", dict(collections.Counter(
        f["estado"] for f in tabla if f["estado"] != "ok")))
    resumen = {}
    for s, tr in DECIDE.items():
        todas = [f for f in tabla if f["b"] == s and f["tramo"] == tr]
        ev = [f for f in todas if f["estado"] == "ok"]
        print("\n" + "=" * 100)
        print(f"{s}, tramo {tr} (ventana UTC {tr}); pasadas con K {sum(1 for f in todas if f['estado'] != 'sobra_en_via')}; "
              f"evaluables {len(ev)}")
        print("  etiquetas (tabla sola) de las evaluables:", dict(collections.Counter(f["lab"] for f in ev)))
        print("  protegidas por volcan:", dict(collections.Counter(f["vol"] for f in ev if f["lab"] == "protegida")))
        sin = [f for f in todas if f["estado"] == "sin_dato_cobertura"]
        print(f"  K sin pasada de la via: {len(sin)}; por etiqueta {dict(collections.Counter(f['lab'] for f in sin))}; "
              f"de ellas K publica {sum(f['pub_K'] for f in sin)}; por volcan {dict(collections.Counter(f['vol'] for f in sin))}")
        sob = [f for f in todas if f["estado"] == "sobra_en_via"]
        print(f"  via sin K de disco (sobran): {len(sob)}; de ellas la via publica {sum(f.get('pub_V', 0) for f in sob)}; "
              f"etiquetas {dict(collections.Counter(f['lab'] for f in sob))}")
        # ---- P1
        perd, ning, solo_v = p1(ev)
        print(f"  P1: protegidas {sum(1 for f in ev if f['lab'] == 'protegida')}; K publica y la via no: {len(perd)} "
              f"{[(f['vol'], f['dt']) for f in perd]}; ninguno: {len(ning)} {[(f['vol'], f['dt']) for f in ning]}; "
              f"la via si y K no: {len(solo_v)} {[(f['vol'], f['dt'], f['mir']) for f in solo_v]}")
        ocr = [f for f in ev if f["lab_union"] == "protegida" and f["lab"] != "protegida"]
        print(f"  protegidas solo del OCR (union si, tabla no): {len(ocr)}; K publica y la via no: "
              f"{[(f['vol'], f['dt'], f['sensor']) for f in ocr if f['pub_K'] and not f['pub_V']]}")
        # ---- P2
        e, B, neto, pg, pp, disc, por = p2(ev)
        el, Bl, netol, _, _, _, _ = p2(ev, lejana=True)
        sk = sum(1 for f in ev if err(f, f["pub_K"]))
        sv = sum(1 for f in ev if err(f, f["pub_V"]))
        print(f"  P2 (via radiante contra K): {e}; B {B}; neto {neto}; p de GANA {pg:.5f}; errores de K {sk}; de la via {sv}")
        print(f"     discordantes por etiqueta y sentido: "
              f"{dict(collections.Counter((f['lab'], 'solo yerra la via' if err(f, f['pub_V']) else 'solo yerra K') for f in disc))}")
        print(f"     discordantes por volcan: {dict(collections.Counter(f['vol'] for f in disc))}")
        print(f"  P2' con lejanas: {el}; B {Bl}; neto {netol}")
        # ---- sin las pasadas (b)
        if s == "MODIS":
            sinb = [f for f in ev if not cerca(f, B_MODIS)]
            e2 = p2(sinb)
            print(f"  sin las 4 pasadas MODIS de §3.1 (b) ({len(ev) - len(sinb)} quitadas): P2 {e2[0]}; B {e2[1]}; neto {e2[2]}; "
                  f"P1 perdidas {len(p1(sinb)[0])}")
        if s == "VIIRS750":
            sinb_h = [f for f in ev if not cerca(f, B_V750_HORA_LECTOR)]
            sinb_f = [f for f in ev if (f["vol"], f["noche"]) not in set(B_V750_FECHA)]
            for nom, x in (("por hora (como el lector)", sinb_h), ("por fecha (como dice el texto)", sinb_f)):
                e2 = p2(x)
                print(f"  sin las pasadas VIIRS 750 de §3.1 (b), {nom}: quitadas {len(ev) - len(x)}; P2 {e2[0]}; B {e2[1]}; "
                      f"neto {e2[2]}; P1 perdidas {len(p1(x)[0])}; protegidas que quedan "
                      f"{sum(1 for f in x if f['lab'] == 'protegida')}")
        # ---- magnitud
        m = magnitud(ev)
        mp = magnitud(ev, a="mag_PL", pa="pub_PL")
        print(f"  magnitud via (pares donde los dos publican): {m}")
        print(f"  control positivo, placebo K x 1,2: d mediana {mp.get('d_mediana')}, d' max abs {mp.get('dprima_max_abs')} "
              f"(tiene que ser 0), ganancia {mp.get('ganancia_g')}")
        rp = [f["mag_V"] / f["mir"] for f in ev if f["lab"] == "protegida" and f["pub_V"] and f["mag_V"] > 0 and (f["mir"] or 0) > 0]
        rk = [f["mag_K"] / f["mir"] for f in ev if f["lab"] == "protegida" and f["pub_K"] and f["mag_K"] > 0 and (f["mir"] or 0) > 0]
        print(f"  razon en protegidas: via {statistics.median(rp) if rp else None:.4f} (n {len(rp)}); "
              f"K {statistics.median(rk) if rk else None:.4f} (n {len(rk)})")
        # ---- controles positivos del instrumento
        for f in ev:
            f["pub_MUDO"] = 0
        print(f"  CONTROL (a) brazo mudo: P1 perdidas {len(p1(ev, a='pub_MUDO')[0])} de "
              f"{sum(1 for f in ev if f['lab'] == 'protegida' and f['pub_K'])} que K publica; P2 mudo contra K: {p2(ev, a='pub_MUDO')[:3]}")
        print(f"  CONTROL (b) K contra K: P2 {p2(ev, a='pub_K')[:3]}")
        # ---- sorteo del §7 con la lectura de S174 (la via contra K, etiquetas barajadas por estrato)
        rng = np.random.default_rng(172)
        estr = collections.defaultdict(list)
        for i, f in enumerate(ev):
            estr[(f["vol"], None if f["z"] is None else int(float(f["z"]) // 10))].append(i)
        cuenta = collections.Counter()
        labs = [f["lab"] for f in ev]
        for _ in range(200):
            nuevo = list(labs)
            for idx in estr.values():
                perm = rng.permutation(len(idx))
                for dst, src in zip(idx, perm):
                    nuevo[dst] = labs[idx[src]]
            bar = [dict(f, lab=l) for f, l in zip(ev, nuevo)]
            cuenta[p2(bar)[0]] += 1
        print(f"  sorteo §7, lectura de S174 (via contra K, etiquetas barajadas en volcan x tramo de cenit, 200, semilla 172): "
              f"{dict(cuenta)}; estratos {len(estr)}")
        # mismo sorteo, barajando en TODO el sensor (sin estratos): cuanto de GANA es solo publicar menos
        cuenta2 = collections.Counter()
        for _ in range(200):
            perm = rng.permutation(len(ev))
            bar = [dict(f, lab=labs[j]) for f, j in zip(ev, perm)]
            cuenta2[p2(bar)[0]] += 1
        print(f"  sorteo sin estratos (etiquetas barajadas en todo el sensor, 200): {dict(cuenta2)}")
        print(f"     tasa de publicacion sobre evaluables: K {sum(f['pub_K'] for f in ev)}/{len(ev)}, via {sum(f['pub_V'] for f in ev)}/{len(ev)}")
        # ---- cobertura del K-gemelo sobre lo que decide
        kg = [f for f in ev if f["en_kg"]]
        dkg = [f for f in disc if f["en_kg"]]
        bl_disc = {f["vol"] + "|" + f["noche"] for f in disc}
        bl_disc_kg = {f["vol"] + "|" + f["noche"] for f in disc if f["en_kg"]}
        pr = [f for f in ev if f["lab"] == "protegida"]
        print(f"  K-gemelo: cubre {len(kg)} de {len(ev)} evaluables ({100 * len(kg) / len(ev):.1f} %); por volcan "
              f"{dict(collections.Counter(f['vol'] for f in kg))}")
        print(f"     de las {len(disc)} pasadas discordantes de P2 cubre {len(dkg)}; de los {len(bl_disc)} bloques, {len(bl_disc_kg)}; "
              f"discordantes NO cubiertas por volcan: {dict(collections.Counter(f['vol'] for f in disc if not f['en_kg']))}")
        print(f"     de las {len(pr)} protegidas cubre {sum(f['en_kg'] for f in pr)}")
        negpub = [f for f in ev if f["lab"] == "neg_limpio" and f["pub_K"]]
        print(f"     de los {len(negpub)} negativos limpios que K de disco publica, el K-gemelo cubre {sum(f['en_kg'] for f in negpub)} "
              f"y de esos publica {sum(f.get('pub_KG', 0) for f in negpub if f['en_kg'])}")
        # ---- noche del operador
        por_n = collections.defaultdict(list)
        for f in todas:
            if f["estado"] != "sobra_en_via":
                por_n[(f["vol"], f["noche"])].append(f)
        n_tot = len(por_n)
        n_todas_ev = sum(1 for fs in por_n.values() if all(f["estado"] == "ok" for f in fs))
        n_limpias = sum(1 for fs in por_n.values() if all(f["estado"] == "ok" for f in fs)
                        and all(f["lab"] == "neg_limpio" for f in fs))
        n_con_sin_info = sum(1 for fs in por_n.values() if any(f["lab"] == "sin_info" for f in fs))
        n21 = sum(1 for fs in por_n.values() if any("NOAA21" in f["sensor"] and f["lab"] == "sin_info" for f in fs))
        print(f"  noche del operador: noches-volcan {n_tot}; con todas las pasadas evaluables {n_todas_ev}; LIMPIAS (todas con "
              f"fila RUTINA) {n_limpias}; con alguna pasada sin fila {n_con_sin_info}; con una NOAA-21 sin fila {n21}")
        resumen[s] = {"B": B, "neto": neto, "p2": e, "p1_perdidas": len(perd), "protegidas": len(pr), "evaluables": len(ev)}

    # ================= C-K propio
    print("\n" + "=" * 100)
    print("C-K PROPIO: K-gemelo (D3) contra K de disco (e7cfbaf54), todas las pasadas con los dos")
    con = [f for f in tabla if f["en_kg"] and "pub_K" in f]
    print("  pasadas comparadas:", len(con), "| por (tramo, sensor):",
          dict(sorted(collections.Counter((f["tramo"], f["b"]) for f in con).items())))
    crit = [f for f in con if f["pub_K"] != f["pub_KG"] or abs((f.get("pc_K") or 0) - (f.get("pc_KG") or 0)) > 1e-3]
    print("  criterio sellado (publicacion distinta o pc.vrp_mw a mas de 0,001 MW): diferencias", len(crit))
    extra = collections.Counter()
    for f in con:
        if abs(f["mag_K"] - f["mag_KG"]) > 1e-3:
            extra["magnitud mostrada"] += 1
        if f.get("dc_K") != f.get("dc_KG"):
            extra["distance_class"] += 1
        if f.get("npx_K") != f.get("npx_KG"):
            extra["n de pixeles anomalos"] += 1
        if (f.get("fh_K") is None) != (f.get("fh_KG") is None) or (f.get("fh_K") is not None
                                                                and abs(f["fh_K"] - f["fh_KG"]) > 1e-3):
            extra["final_hotspot_dist_km"] += 1
        if (f.get("f5_K") is None) != (f.get("f5_KG") is None) or (f.get("f5_K") is not None
                                                                and abs(f["f5_K"] - f["f5_KG"]) > 1e-3):
            extra["f5_core_vrp_mw"] += 1
        if f.get("gran_K") and f.get("sha_K") != f.get("sha_KG"):
            extra["codigo_sha distinto (esperado)"] += 1
    print("  campos de mas (no pedidos por el sello):", dict(extra) or "0 diferencias en magnitud mostrada, clase, pixeles, distancia y f5")
    print("  sustrato de C-K: de las comparadas, K de disco publica", sum(f["pub_K"] for f in con),
          "; con cumulo (pc.vrp_mw > 0)", sum(1 for f in con if (f.get("pc_K") or 0) > 0),
          "; codigo_sha de K de disco:", dict(collections.Counter(f.get("sha_K") for f in con).most_common(6)))
    print("  K-gemelo que K de disco no tiene (dentro de tramos): se ve en c01 (3.282 records de D3 contra 3.138 comparadas)")
    print("  placebo K x 1,2: pasadas donde cambia la PUBLICACION respecto de K:",
          sum(1 for f in tabla if "pub_K" in f and f["pub_K"] != f["pub_PL"]), "de", sum(1 for f in tabla if "pub_K" in f))

    # ================= caja de VIIRS 750
    print("\n" + "=" * 100)
    print("CAJA de VIIRS 750 en los records de la via (diag_codigo_mirova.roi), por volcan y tramo:")
    c = collections.Counter((f["vol"], f.get("roi_V")) for f in tabla if f["b"] == "VIIRS750" and "pub_V" in f)
    for k, v in sorted(c.items()):
        print("   ", k, v)

    # ================= comparacion con lectura.json
    if lect:
        print("\n" + "=" * 100)
        print("COMPARACION con lectura.json (el lector, objeto de la auditoria):")
        for s in DECIDE:
            r = lect["sensores"][s]
            rr = r["otros_brazos"].get("radiante") if s == "VIIRS375" else r["regla"]
            print(f"  {s}: lector radiante B {rr.get('B')} neto {rr.get('neto')} p2 {rr.get('p2')} | propio B {resumen[s]['B']} "
                  f"neto {resumen[s]['neto']} p2 {resumen[s]['p2']} | evaluables lector {r['n_evaluables']} propio {resumen[s]['evaluables']} "
                  f"| etiquetas lector {r['etiquetas']}")


if __name__ == "__main__":
    main()
