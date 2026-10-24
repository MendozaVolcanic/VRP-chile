# -*- coding: utf-8 -*-
"""S162 V750-B, análisis pre-registrado (PREREGISTRO_V750B.md §4 a §7) y lectura del brazo nativo de V750-C.

POR QUÉ. La ROI del paquete V750-A se elige midiendo contra MIROVA en las dos direcciones: no perder ninguna alerta de
1 MW o más (P1, veto) y equivocarse lo menos posible bajo 1 MW (P2, prueba de signos por bloque noche-volcán, D-45).
Este script aplica la regla escrita antes de los datos; los controles se imprimen primero y, si caen, no se imprime
ningún veredicto.

Record de cada brazo del oráculo (§4): posición y clase de distancia del cúmulo 8-conexo del píxel alertado más
radiante (corrige C-4 del censo S159), VRP de la unión de los alertados (lo que el .m entrega). Publica = el predicado
del tablero ejecutado con node (A97, banco_paridad.correr_node). B4 = B1 en Cordón Caulle y Tupungatito, B0 en el resto.

P2 por brazo contra B1: e = 1 si la pasada es un error bajo 1 MW (alerta bajo 1 MW que decide y no se publica, o
negativo limpio publicado); contribución c = e(brazo) - e(B1); bloque = (noche UTC, volcán); `prueba_signos_p2` y
`regla_signos_p2` de experiments/_s157_prereg_d25/evaluar_d25.py en el tag s161-d25-lectura (se pasa con --evaluador).

Las dos preguntas del instrumento: (1) el nulo del contador (perturbar records publicados y cambiar la publicación, como
el censo S159) y el control positivo (B0 pierde protegidas de Cordón Caulle); (2) K = producción y B0, B1 = censo S159.
Uso: python analizar_v750b.py --art <carpetas del run> --objetivos objetivos_v750b.json --evaluador <evaluar_d25.py>
     [--censo-art <run del censo S159> --censo-objetivos <objetivos.json del censo>] [--solo-controles]
"""
from __future__ import annotations

import argparse
import collections
import copy
import json
import random
import statistics
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "experiments/_s158_audit_r2/oraculo"))
import banco_paridad as B  # noqa: E402
from clase_mirova import alerta_protegida  # noqa: E402
import mirova_v750_r2 as ORA  # noqa: E402

CAJAS = ("B0", "B1", "B2", "B3")
BRAZOS = ("K", "B0", "B1", "B2", "B3", "B4")
PREF = ("B4", "B2", "B1", "B3")          # §6.3: cercanía al .m
VOL_SENS = ("PuyehueCordonCaulle", "Tupungatito")
FRONTERA_OCR = "2026-06-13"
C = 33


NOMBRES_SIGNOS = ("SEMILLA", "SEMILLA_P2_SIGNOS", "N_SORTEOS_P2_SIGNOS", "MAX_B_EXACTO_P2", "MAX_B_SIN_SUSTRATO_P2",
                  "TOPE_P2_DEN", "prueba_signos_p2", "regla_signos_p2")


def cargar_signos(ruta):
    """Extrae de evaluar_d25.py (tag s161-d25-lectura), con ast y sin copiar a mano, el texto literal de la prueba de
    signos de D-45 y de sus constantes, y lo ejecuta aparte: importar el archivo entero arrastra todo el evaluador
    de D25 (evaluar_fk y otros), que aquí no hace falta. Falla si falta alguna pieza."""
    import ast
    import types
    src = Path(ruta).read_text(encoding="utf-8")
    arbol = ast.parse(src)
    piezas = []
    for nodo in arbol.body:
        if isinstance(nodo, ast.FunctionDef):
            nombres = {nodo.name}
        elif isinstance(nodo, ast.Assign):   # incluye las asignaciones dobles (`N_BOOT, SEMILLA = 10000, 157`)
            nombres = {e.id for t in nodo.targets for e in (t.elts if isinstance(t, ast.Tuple) else [t])
                       if isinstance(e, ast.Name)}
        else:
            continue
        if nombres & set(NOMBRES_SIGNOS):
            piezas.append((nombres, ast.get_source_segment(src, nodo)))
    faltan = set(NOMBRES_SIGNOS) - set().union(*(n for n, _ in piezas))
    assert not faltan, f"evaluar_d25.py sin {faltan}"
    m = types.ModuleType("signos_d45")
    m.__dict__.update({"collections": collections, "np": np})
    exec(compile("\n\n".join(t for _, t in piezas), str(ruta), "exec"), m.__dict__)
    assert m.SEMILLA_P2_SIGNOS == 162 and m.MAX_B_EXACTO_P2 == 20 and m.TOPE_P2_DEN == 20
    return m


def cargar(dirs):
    res = {}
    for d in dirs:
        for f in sorted(Path(d).rglob("resultados_*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                if r.get("estado") == "ok" or r["id"] not in res:
                    res[r["id"]] = r
    return res


def cumulo_del_mas_radiante(px):
    """Píxeles (fila, columna) del cúmulo 8-conexo que contiene al alertado de mayor M13."""
    pos = {(p[0], p[1]) for p in px}
    semilla = max(px, key=lambda p: p[4])
    vistos, pila = {(semilla[0], semilla[1])}, [(semilla[0], semilla[1])]
    while pila:
        a, b = pila.pop()
        for da in (-1, 0, 1):
            for db in (-1, 0, 1):
                q = (a + da, b + db)
                if q in pos and q not in vistos:
                    vistos.add(q)
                    pila.append(q)
    return sorted(vistos)


def record_cumulo(o, inner, sensor):
    if not o or not o.get("npix") or o.get("vrp_mw") is None:
        return {"sensor": sensor, "vrp_mw": 0.0, "primary_cluster": None, "distance_class": None}
    px = o["pixeles"]
    cu = cumulo_del_mas_radiante(px)
    fr, fc = np.mean([a for a, _ in cu]), np.mean([b for _, b in cu])
    dcen = float(np.hypot(fr - C, fc - C) * 0.75)
    Lmax = max(p[4] for p in px)
    tmax = float(ORA.radiancia_a_temperatura(np.array([Lmax]), ORA.LAMBDA_M13)[0])
    v = round(float(o["vrp_mw"]), 3)
    return {"sensor": sensor, "vrp_mw": v, "t_max_k": tmax, "triggered_test1": False,
            "distance_class": "summit" if dcen <= inner else "far",
            "primary_cluster": {"vrp_mw": v, "n_pixels": len(cu), "centroid_dist_km": round(dcen, 3)}}


def slim(rec):
    s = {k: rec.get(k) for k in B.CAMPOS_JS if k != "anomaly_pixels"}
    s["anomaly_pixels"] = []
    return s


def caja_de(brazo, volcan):
    if brazo == "B4":
        return "B1" if volcan in VOL_SENS else "B0"
    return brazo


def partida(r):
    if r.get("estado") == "volcan_fuera_del_granulo":
        return "fuera"
    c = r.get("cobertura")
    if not c:
        return "sin_cobertura"
    return "sin_crater" if (c["nan_7"] > 0 or c["nan_centro"]) else "observada"


def tramo_z(z):
    if z is None:
        return "z?"
    lo = int(z // 10) * 10
    return f"{lo}-{lo + 10}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True, nargs="+")
    ap.add_argument("--objetivos", required=True)
    ap.add_argument("--evaluador", required=True, help="evaluar_d25.py del tag s161-d25-lectura")
    ap.add_argument("--censo-art", nargs="*", default=[])
    ap.add_argument("--censo-objetivos", default="")
    ap.add_argument("--solo-controles", action="store_true")
    ap.add_argument("--salida", default=str(AQUI / "analizar_v750b_salida.txt"))
    a = ap.parse_args()
    EV = cargar_signos(a.evaluador)
    obj = {o["id"]: o for o in json.loads(Path(a.objetivos).read_text(encoding="utf-8"))}
    res = cargar(a.art)
    inner = B.inner_desde_html()
    L = []

    def pr(*x):
        s = " ".join(str(y) for y in x)
        print(s, flush=True)
        L.append(s)

    # ---------------------------------------------------------------- cobertura y estados
    est = collections.Counter((obj[i]["lab"], (res.get(i) or {}).get("estado", "sin_resultado")[:40]) for i in obj)
    pr("== cobertura: objetivos", len(obj), "con resultado", len(res), dict(sorted(est.items())))

    def ok(i):
        r = res.get(i) or {}
        k = (r.get("brazos") or {}).get("K") or {}
        return (r.get("estado") == "ok" and r.get("dayflag") == 0 and set(CAJAS) <= set(r.get("oraculo") or {})
                and "error" not in k and "record" in k and partida(r) == "observada")

    oks = [i for i in obj if ok(i)]
    no_obs = collections.Counter(partida(res[i]) for i in obj if i in res and res[i].get("estado") in
                                 ("ok", "volcan_fuera_del_granulo") and not ok(i))
    sin = [i for i in obj if i not in oks and (res.get(i) or {}).get("estado") not in ("ok", "volcan_fuera_del_granulo")]
    pr(f"   ok y observadas: {len(oks)} | no observadas (fuera del denominador): {dict(no_obs)} | SIN DATO: {len(sin)}")
    prot_sin = [(obj[i]["volcan"], obj[i]["hora_utc"]) for i in sin if obj[i].get("protegida")]
    pr("   protegidas SIN DATO (falla de cobertura, no de brazo):", prot_sin or "ninguna")

    # ---------------------------------------------------------------- publicación con node
    casos, idx = [], []
    for i in oks:
        o, r = obj[i], res[i]
        casos.append([slim(r["brazos"]["K"]["record"]), inner[o["volcan"]]])
        idx.append((i, "K"))
        for c in CAJAS:
            casos.append([record_cumulo(r["oraculo"][c], inner[o["volcan"]], o["sensor"]), inner[o["volcan"]]])
            idx.append((i, c))
    P = {k: bool(p[4]) for k, p in zip(idx, B.correr_node(casos))}

    def pub(i, b):
        return P[(i, "K")] if b == "K" else P[(i, caja_de(b, obj[i]["volcan"]))]

    def vrp(i, b):
        if b == "K":
            return ((res[i]["brazos"]["K"]["record"] or {}).get("primary_cluster") or {}).get("vrp_mw") or 0.0
        return res[i]["oraculo"][caja_de(b, obj[i]["volcan"])].get("vrp_mw") or 0.0

    # ---------------------------------------------------------------- controles
    nulo, nidx = [], []
    for i in oks:
        for c in CAJAS:
            if P[(i, c)]:
                base = record_cumulo(res[i]["oraculo"][c], inner[obj[i]["volcan"]], obj[i]["sensor"])
                a0 = copy.deepcopy(base)
                a0["primary_cluster"]["vrp_mw"] = 0.0
                a0["vrp_mw"] = 0.0
                b0 = copy.deepcopy(base)
                b0["distance_class"] = "far"
                for rr in (a0, b0):
                    nulo.append([rr, inner[obj[i]["volcan"]]])
                    nidx.append(True)
    rng = random.Random(162)
    neg_no = [i for i in oks if obj[i]["lab"] == "neg_limpio" and not P[(i, "B0")]]
    for i in rng.sample(neg_no, min(50, len(neg_no))):
        rr = {"sensor": obj[i]["sensor"], "vrp_mw": 0.3, "t_max_k": 290.0, "triggered_test1": False,
              "distance_class": "summit", "primary_cluster": {"vrp_mw": 0.3, "n_pixels": 1, "centroid_dist_km": 0.5}}
        nulo.append([rr, inner[obj[i]["volcan"]]])
        nidx.append(False)
    NP = [bool(p[4]) for p in B.correr_node(nulo)] if nulo else []
    c_nulo = sum(1 for era, p in zip(nidx, NP) if p == era)
    pr(f"== control nulo del contador: {len(nidx)} perturbaciones; las que NO cambian la publicación: {c_nulo} (tiene que ser 0)")
    dpub = [i for i in oks if bool(obj[i].get("pub_prod")) != P[(i, "K")]]
    dvrp = [i for i in oks if abs((vrp(i, "K") or 0) - (obj[i].get("pc_vrp") or 0)) > 0.001]
    pr(f"== control K = producción: publica distinto {len(dpub)}, pc.vrp_mw distinto {len(dvrp)} (tienen que ser 0)")
    c_censo = "no pedido"
    if a.censo_art and a.censo_objetivos:
        cobj = {(o["volcan"], o["hora_utc"]): o["id"]
                for o in json.loads(Path(a.censo_objetivos).read_text(encoding="utf-8"))}
        cres = cargar(a.censo_art)
        cnt = collections.Counter()
        for i in oks:
            j = cobj.get((obj[i]["volcan"], obj[i]["hora_utc"]))
            rc = cres.get(j) if j is not None else None
            if not rc or rc.get("estado") != "ok":
                continue
            for c, ref in (("B0", "geo_linear"), ("B1", "geo_linear_anillo_sensible")):
                x, y = res[i]["oraculo"][c], (rc.get("oraculo") or {}).get(ref) or {}
                igual = x.get("npix") == y.get("npix") and abs((x.get("vrp_mw") or 0) - (y.get("vrp_mw") or 0)) < 1e-6
                cnt[f"{c}_{'igual' if igual else 'DISTINTO'}"] += 1
        c_censo = dict(cnt)
    pr("== control B0 y B1 = censo S159 en pasadas comunes:", c_censo)
    ctrl_ok = c_nulo == 0 and not dpub and not dvrp and not any("DISTINTO" in k for k in (c_censo if isinstance(c_censo, dict) else {}))
    pr("== controles generales:", "EN VERDE" if ctrl_ok else "CAÍDOS: no se imprime veredicto")

    # ---------------------------------------------------------------- etiquetas por pasada
    def prot_tabla(o):
        return any(alerta_protegida(f) for f in o.get("mirova") or [] if f.get("source") == "CONS")

    def etiqueta(o, canal):
        """'prot', 'baja' (alerta bajo 1 MW que decide), 'neg' o None (no entra). canal: 'todo' o 'tabla'."""
        if o["lab"] == "neg_limpio":
            return "neg"
        if o["lab"] != "pos" or not o.get("decide"):
            return None
        if canal == "tabla" and not o.get("alerta_tabla"):
            return None
        p = prot_tabla(o) if canal == "tabla" else o.get("protegida")
        return "prot" if p else "baja"

    def ventana(o, v):
        h = o["hora_utc"]
        return v == "TO" or (v == "T" and h < FRONTERA_OCR) or (v == "O" and h >= FRONTERA_OCR)

    def metricas(b, v, canal):
        m = collections.Counter()
        for i in oks:
            o = obj[i]
            e = etiqueta(o, canal)
            if e is None or not ventana(o, v):
                continue
            pb, vb = pub(i, b), vrp(i, b)
            m[f"n_{e}"] += 1
            if e == "prot" and not pb:
                m["P1"] += 1
            if e == "prot" and pb and vb < 1.0:
                m["P1b_abajo"] += 1
            if e in ("baja", "neg") and pb and vb >= 1.0:
                m["P1b_arriba"] += 1
            if e == "baja" and not pb:
                m["E_baja"] += 1
            if e == "neg" and pb:
                m["E_neg"] += 1
        m["E"] = m["E_baja"] + m["E_neg"]
        return m

    def p2(b, v, canal, ref="B1"):
        sumas = collections.defaultdict(int)
        for i in oks:
            o = obj[i]
            e = etiqueta(o, canal)
            if e not in ("baja", "neg") or not ventana(o, v):
                continue
            err = lambda x: int((e == "baja" and not pub(i, x)) or (e == "neg" and pub(i, x)))
            c = err(b) - err(ref)
            if c:
                sumas[(o["hora_utc"][:10], o["volcan"])] += c
        claves = sorted(sumas)
        s = [sumas[k] for k in claves]
        neto = sum(s)
        pr_ = EV.prueba_signos_p2(s, neto)
        return EV.regla_signos_p2(neto, len(s), pr_), neto, len(s), pr_

    if a.solo_controles or not ctrl_ok:
        Path(a.salida).write_text("\n".join(L) + "\n", encoding="utf-8")
        return 0 if ctrl_ok else 3

    # control negativo del evaluador: B1 contra sí mismo
    pr("== control negativo P2 (B1 contra B1):", p2("B1", "TO", "todo")[:3])
    # control positivo: B0 pierde protegidas de Cordón Caulle
    pcc = [obj[i]["hora_utc"] for i in oks if obj[i]["volcan"] == "PuyehueCordonCaulle"
           and etiqueta(obj[i], "todo") == "prot" and not pub(i, "B0")]
    pr("== control positivo (B0 pierde protegidas de Cordón Caulle):", len(pcc), pcc[:10])

    # ---------------------------------------------------------------- métricas y regla §6
    veredicto = {}
    for canal in ("tabla", "todo"):
        for v in ("T", "O", "TO"):
            pr(f"\n== ventana {v}, canal {canal}")
            for b in BRAZOS:
                m = metricas(b, v, canal)
                linea = (f"   {b:3s} prot {m['n_prot']:4d} P1 {m['P1']:3d} | P1b abajo {m['P1b_abajo']:3d} arriba "
                         f"{m['P1b_arriba']:3d} | E {m['E']:4d} (bajas sin publicar {m['E_baja']} de {m['n_baja']}, "
                         f"neg publicados {m['E_neg']} de {m['n_neg']})")
                if b not in ("B1", "K"):
                    reg, neto, nb, prr = p2(b, v, canal)
                    linea += f" | P2 contra B1: {reg} (neto {neto}, bloques {nb}, p gana {prr['gana']}, pierde {prr['pierde']})"
                    veredicto[(b, v, canal)] = (m["P1"], reg, m["E"])
                else:
                    veredicto[(b, v, canal)] = (m["P1"], None, m["E"])
                pr(linea)
    elegibles = [b for b in ("B0", "B1", "B2", "B3", "B4")
                 if all(veredicto[(b, v, c)][0] == 0 for v in ("T", "O") for c in ("tabla", "todo"))]
    pr("\n== §6.1 elegibles (P1 = 0 en T y O, con la tabla sola y con todo):", elegibles)
    ganan = [b for b in elegibles if b != "B1" and veredicto[(b, "TO", "todo")][1] == "GANA"
             and veredicto[(b, "TO", "tabla")][1] in ("GANA", "EMPATE", "SIN SUSTRATO")]
    if ganan:
        elegido = min(ganan, key=lambda b: veredicto[(b, "TO", "todo")][2])
        motivo = f"gana contra B1 (§6.2): {ganan}"
    else:
        cand = [b for b in PREF if b in elegibles]
        elegido = cand[0] if cand else None
        motivo = "ninguno gana contra B1; orden de cercanía al .m (§6.3)" if cand else "NINGÚN BRAZO ELEGIBLE"
    pr(f"== §6 ROI elegida: {elegido} ({motivo})")
    if elegido in ("B2", "B4"):
        pr("   §6.5: ROI por volcán; Nicolás confirma que es fidelidad al .m antes de pasarla a V750-A")

    # ---------------------------------------------------------------- descriptivas
    pr("\n== razón brazo/MIROVA en alertas que deciden publicadas (mediana [q1, q3] n), y por volcán")
    for b in BRAZOS:
        rz = sorted(vrp(i, b) / obj[i]["mirova_vrp"] for i in oks if etiqueta(obj[i], "todo") in ("prot", "baja")
                    and pub(i, b) and obj[i].get("mirova_vrp"))
        n = len(rz)
        pr(f"   {b}: " + (f"{statistics.median(rz):.3f} [{rz[n // 4]:.3f}, {rz[(3 * n) // 4]:.3f}] n={n}" if n else "-"))
    for vol in ("PuyehueCordonCaulle", "Tupungatito", "PlanchonPeteroa"):
        lin = []
        for b in BRAZOS:
            m = collections.Counter()
            for i in oks:
                if obj[i]["volcan"] != vol:
                    continue
                e = etiqueta(obj[i], "todo")
                if e:
                    m[e] += 1
                    m[e + "_pub"] += pub(i, b)
            lin.append(f"{b} prot {m['prot_pub']}/{m['prot']} baja {m['baja_pub']}/{m['baja']} neg {m['neg_pub']}/{m['neg']}")
        pr(f"   {vol}: " + " | ".join(lin))
    pr("\n== por tramo de 10° de cenit: negativos publicados y protegidas perdidas")
    for b in BRAZOS:
        t = collections.Counter()
        for i in oks:
            e = etiqueta(obj[i], "todo")
            z = tramo_z(obj[i].get("z"))
            if e == "neg" and pub(i, b):
                t[(z, "neg")] += 1
            if e == "prot" and not pub(i, b):
                t[(z, "P1")] += 1
        pr(f"   {b}: {dict(sorted(t.items()))}")

    # ---------------------------------------------------------------- V750-C: brazo nativo en S_C
    sc = [i for i in oks if obj[i].get("en_sc") and res[i].get("nativo")]
    pr(f"\n== V750-C, brazo nativo: pasadas de S_C con nativo {len(sc)}")

    def en_pixel_k(i, nombre):
        k = res[i]["brazos"]["K"]
        pix = k.get("pc_pix") or []
        r0, c0 = res[i]["nativo_esquina_fila_col"]
        al = [(p[0], p[1]) for p in res[i]["nativo"][nombre]["pixeles"]]
        return any(abs(a - (f - r0)) <= 1 and abs(b - (c - c0)) <= 1 for f, c in pix for a, b in al)

    grupos = {"cumbre0_neg": lambda o: o.get("dc") == "summit" and o.get("pc_vrp") == 0 and o["lab"] == "neg_limpio",
              "cumbre0_pos": lambda o: o.get("dc") == "summit" and o.get("pc_vrp") == 0 and o["lab"] == "pos",
              "neg_sin_K": lambda o: o["lab"] == "neg_limpio" and not o.get("pc_n")}
    for g, f in grupos.items():
        ids = [i for i in sc if f(obj[i])]
        if not ids:
            continue
        lin = [f"{g} n={len(ids)}"]
        for nombre, grilla in (("N0", "B0"), ("N1", "B1")):
            det_k = sum(en_pixel_k(i, nombre) for i in ids)
            alg = sum(bool(res[i]["nativo"][nombre]["npix"]) for i in ids)
            alg_g = sum(bool(res[i]["oraculo"][grilla]["npix"]) for i in ids)
            lin.append(f"{nombre}: en el píxel de K {det_k}, con algún píxel {alg} (grilla {grilla}: {alg_g})")
        pr("   " + " | ".join(lin))
    Path(a.salida).write_text("\n".join(L) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
