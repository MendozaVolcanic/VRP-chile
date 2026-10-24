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
import hashlib
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

CAJAS = ("B0", "B1", "B2", "B3", "B5")
BRAZOS = ("K", "B0", "B1", "B2", "B3", "B4", "B5")
CANDIDATOS = ("B0", "B1", "B2", "B3", "B4", "B5")
PREF = ("B4", "B2", "B5", "B1", "B3")    # §6.3: cercanía al .m
SHA_EVALUADOR = "2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747"   # evaluar_d25.py, s161-d25-lectura
MAX_SIN_DATO = 0.02                      # §9: con más del 2 % sin procesar (o una protegida) no se lee el veredicto
MAX_K_DISTINTO = 0.01                    # §7: con más del 1 % de pasadas con K distinto de producción, se detiene
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
    import hashlib
    import types
    crudo = Path(ruta).read_bytes()
    assert hashlib.sha256(crudo).hexdigest() == SHA_EVALUADOR, "evaluar_d25.py no es el del tag s161-d25-lectura"
    src = crudo.decode("utf-8")
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


def record_cumulo(o, inner, sensor, ancla=(C, C)):
    """ancla: posición (fila, columna) desde donde se mide la distancia; el análisis usa el cráter (VB-07, como
    producción, que mide desde get_detection_anchor) e informa al lado el centro de la grilla."""
    if not o or not o.get("npix") or o.get("vrp_mw") is None:
        return {"sensor": sensor, "vrp_mw": 0.0, "primary_cluster": None, "distance_class": None}
    px = o["pixeles"]
    cu = cumulo_del_mas_radiante(px)
    fr, fc = np.mean([a for a, _ in cu]), np.mean([b for _, b in cu])
    dcen = float(np.hypot(fr - ancla[0], fc - ancla[1]) * 0.75)
    Lmax = max(p[4] for p in px)
    tmax = float(ORA.radiancia_a_temperatura(np.array([Lmax]), ORA.LAMBDA_M13)[0])
    v = round(float(o["vrp_mw"]), 3)
    return {"sensor": sensor, "vrp_mw": v, "t_max_k": tmax, "triggered_test1": False,
            "distance_class": "summit" if dcen <= inner else "far",
            "primary_cluster": {"vrp_mw": v, "n_pixels": len(cu), "centroid_dist_km": round(dcen, 3)}}


def slim(rec):
    """Record de K para el predicado. Un record None (K no armó record: ROI vacía o el store no escribió; VB-02) es
    «K no publica»; el control K = producción lo detecta si producción sí tenía algo."""
    rec = rec or {}
    s = {k: rec.get(k) for k in B.CAMPOS_JS if k != "anomaly_pixels"}
    s["anomaly_pixels"] = []
    return s


def caja_de(brazo, volcan):
    if brazo == "B4":
        return "B1" if volcan in VOL_SENS else "B0"
    return brazo


def partida(r):
    """'fuera' (el gránulo no mira el volcán), 'sin_crater' (celdas sin dato en el 7 x 7 del CRÁTER, VB-16), 'observada',
    o None si la pasada no se procesó (SIN DATO: no baja, grilla incompleta, error de K; VB-04)."""
    if r.get("estado") == "volcan_fuera_del_granulo":
        return "fuera"
    if r.get("estado") != "ok":
        return None
    c = r.get("cobertura") or {}
    n7, nc = c.get("nan_7_crater", c.get("nan_7")), c.get("nan_crater", c.get("nan_centro"))
    if n7 is None:
        return None
    return "sin_crater" if (n7 > 0 or nc) else "observada"


def tramo_z(z):
    if z is None:
        return "z?"
    lo = int(z // 10) * 10
    return f"{lo}-{lo + 10}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True, nargs="+")
    ap.add_argument("--objetivos", required=True)
    ap.add_argument("--evaluador", required=True, help="evaluar_d25.py del tag s161-d25-lectura (sha256 fijado)")
    ap.add_argument("--censo-art", nargs="*", default=[])
    ap.add_argument("--censo-objetivos", default="")
    ap.add_argument("--sin-granulo", default=str(AQUI / "sin_granulo_v750b.json"),
                    help="pasadas que el generador sacó de la lista por no tener gránulo (VB2-07)")
    ap.add_argument("--solo-controles", action="store_true")
    ap.add_argument("--censo-omitido-solo-pruebas", action="store_true",
                    help="SÓLO para baterías sintéticas: da por bueno el control del censo; el veredicto no vale para el run")
    ap.add_argument("--leer-con-faltantes", default="",
                    help="MOTIVO de la decisión (coordinadora y Nicolás, §4) para leer con cobertura insuficiente o sin "
                         "el control del censo; cada línea de veredicto sale marcada y el código de salida es 5")
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

    def salir(cod):
        Path(a.salida).write_text("\n".join(L) + "\n", encoding="utf-8")
        return cod

    # ---------------------------------------------------------------- cobertura (§4, §9)
    est = collections.Counter((obj[i]["lab"], (res.get(i) or {}).get("estado", "sin_resultado")[:40]) for i in obj)
    pr("== cobertura: objetivos", len(obj), "con resultado", len(res), dict(sorted(est.items())))
    part = {i: partida(res.get(i) or {}) for i in obj}
    sin = [i for i in obj if part[i] is None or (part[i] == "observada" and res[i].get("dayflag") != 0)]
    no_obs = collections.Counter(part[i] for i in obj if part[i] in ("fuera", "sin_crater"))
    oks = [i for i in obj if part[i] == "observada" and res[i].get("dayflag") == 0
           and set(CAJAS) <= set(res[i].get("oraculo") or {})]
    pr(f"   observadas: {len(oks)} | no observadas (fuera del denominador): {dict(no_obs)} | SIN DATO: {len(sin)}")
    pr("   SIN DATO por motivo:", dict(collections.Counter((res.get(i) or {}).get("estado", "sin_resultado")[:40]
                                                         for i in sin)))
    prot_sin = [(obj[i]["volcan"], obj[i]["hora_utc"]) for i in sin if obj[i].get("protegida")]
    # VB2-07: las pasadas sin gránulo nunca llegan al probe; el generador las deja en un archivo y aquí cuentan como
    # SIN DATO, y una protegida entre ellas también frena la lectura
    # VB3-02: el archivo es obligatorio y tiene que corresponder a esta lista de objetivos; si falta o no corresponde,
    # es SIN DATO (cierra la cobertura), nunca «cero pasadas sin gránulo»
    sg = Path(a.sin_granulo)
    sha_obj = hashlib.sha256(Path(a.objetivos).read_bytes()).hexdigest()
    sg_ok, sin_g = False, []
    if sg.exists():
        dsg = json.loads(sg.read_text(encoding="utf-8"))
        sg_ok = isinstance(dsg, dict) and dsg.get("objetivos_sha256") == sha_obj
        sin_g = dsg.get("pasadas", []) if sg_ok else []
    pr(f"   pasadas sin gránulo (del generador): {len(sin_g)}"
       + ("" if sg_ok else f" | ARCHIVO {'AUSENTE' if not sg.exists() else 'DE OTRA LISTA DE OBJETIVOS'}: SIN DATO"))
    prot_sin += [(x["volcan"], x["hora_utc"]) for x in sin_g if x.get("protegida")]
    pr("   protegidas no observadas (fuera del denominador, por nombre):",
       [(obj[i]["volcan"], obj[i]["hora_utc"], part[i]) for i in obj if part[i] in ("fuera", "sin_crater")
        and obj[i].get("protegida")] or "ninguna")
    pr("   protegidas SIN DATO (falla de cobertura, no de brazo):", prot_sin or "ninguna")
    # VB3-07: el denominador del 2 % es el de las pasadas que cuentan (sin «fuera» ni «sin_crater»)
    den_cob = max(1, len(obj) + len(sin_g) - no_obs["fuera"] - no_obs["sin_crater"])
    cob_ok = sg_ok and len(sin) + len(sin_g) <= MAX_SIN_DATO * den_cob and not prot_sin
    pr("== cobertura:", "SUFICIENTE" if cob_ok else
       f"INSUFICIENTE (más de {MAX_SIN_DATO:.0%} sin procesar o una protegida): relanzar con SOLO las faltantes")

    # ---------------------------------------------------------------- publicación con node
    def ancla(i):
        return tuple(obj[i].get("pos_crater") or (C, C))

    casos, idx = [], []
    for i in oks:
        o, r = obj[i], res[i]
        casos.append([slim((r.get("brazos") or {}).get("K", {}).get("record")), inner[o["volcan"]]])
        idx.append((i, "K"))
        for c in CAJAS:
            casos.append([record_cumulo(r["oraculo"][c], inner[o["volcan"]], o["sensor"], ancla(i)), inner[o["volcan"]]])
            idx.append((i, c))
            casos.append([record_cumulo(r["oraculo"][c], inner[o["volcan"]], o["sensor"]), inner[o["volcan"]]])
            idx.append((i, c + "|centro"))
    P = {k: bool(p[4]) for k, p in zip(idx, B.correr_node(casos))}
    camb = collections.Counter((c, obj[i]["volcan"]) for i in oks for c in CAJAS if P[(i, c)] != P[(i, c + "|centro")])
    pr("== publicación con ancla en el cráter contra ancla en el centro de la grilla (pasadas que cambian):",
       dict(sorted(camb.items())) or "ninguna")

    def pub(i, b):
        return P[(i, "K")] if b == "K" else P[(i, caja_de(b, obj[i]["volcan"]))]

    def vrp(i, b):
        if b == "K":
            rec = (res[i].get("brazos") or {}).get("K", {}).get("record") or {}
            return (rec.get("primary_cluster") or {}).get("vrp_mw") or 0.0
        return res[i]["oraculo"][caja_de(b, obj[i]["volcan"])].get("vrp_mw") or 0.0

    # ---------------------------------------------------------------- controles generales (§7)
    nulo, nidx = [], []
    for i in oks:
        for c in CAJAS:
            if P[(i, c)]:
                base = record_cumulo(res[i]["oraculo"][c], inner[obj[i]["volcan"]], obj[i]["sensor"], ancla(i))
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
    pr(f"== control nulo del contador: {len(nidx)} perturbaciones; las que NO cambian la publicación: {c_nulo} "
       "(tiene que ser 0, con al menos una perturbación)")
    k_none = [i for i in oks if not (res[i].get("brazos") or {}).get("K", {}).get("record")]
    k_dist = sorted({i for i in oks if bool(obj[i].get("pub_prod")) != P[(i, "K")]}
                    | {i for i in oks if abs((vrp(i, "K") or 0) - (obj[i].get("pc_vrp") or 0)) > 0.001})
    k_dist_prot = [(obj[i]["volcan"], obj[i]["hora_utc"]) for i in k_dist if obj[i].get("protegida")]
    pr(f"== control K = producción: distintas {len(k_dist)} de {len(oks)} (protegidas {k_dist_prot or 'ninguna'}); "
       f"K sin record {len(k_none)}; lista completa {[(obj[i]['volcan'], obj[i]['hora_utc']) for i in k_dist]}")
    k_ok = len(k_dist) <= MAX_K_DISTINTO * max(1, len(oks)) and not k_dist_prot
    oks = [i for i in oks if i not in set(k_dist)]   # §7: salen de todos los brazos y se listan arriba
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
                # VB2-09: también la posición de cada píxel, no sólo la cuenta y el VRP
                igual = (x.get("npix") == y.get("npix")
                         and abs((x.get("vrp_mw") or 0) - (y.get("vrp_mw") or 0)) < 1e-6
                         and sorted((p[0], p[1]) for p in x.get("pixeles") or [])
                         == sorted((p[0], p[1]) for p in y.get("pixeles") or []))
                cnt[f"{c}_{'igual' if igual else 'DISTINTO'}"] += 1
        censo_ok = bool(cnt) and not any("DISTINTO" in k for k in cnt)
        pr("== control B0 y B1 = censo S159 en pasadas comunes:", dict(cnt), "OK" if censo_ok else "FALLA")
    elif a.censo_omitido_solo_pruebas:
        censo_ok = True
        pr("== control B0 y B1 = censo S159: OMITIDO POR --censo-omitido-solo-pruebas. PRUEBA SINTÉTICA: ESTE VEREDICTO NO "
           "VALE PARA EL RUN")
    else:
        censo_ok = False
        pr("== control B0 y B1 = censo S159: SIN DATO (falta --censo-art y --censo-objetivos): sin él no hay veredicto")
    ctrl_ok = bool(nidx) and c_nulo == 0 and k_ok and cob_ok
    pr("== controles generales (nulo, K = producción, cobertura):", "EN VERDE" if ctrl_ok else "CAÍDOS")

    # ---------------------------------------------------------------- etiquetas (§4, §6; VB-03, VB-08)
    def prot_tabla(o):
        return any(alerta_protegida(f) for f in o.get("mirova") or [] if f.get("source") == "CONS")

    def etiqueta(o, canal):
        """'prot', 'baja' (alerta bajo 1 MW que decide), 'neg' o None. canal: 'tabla' (sólo la tabla de MIROVA),
        'todo' (tabla más OCR) o 'decide' (programa §2: tabla sola en T, tabla más OCR en O)."""
        if canal == "decide":
            canal = "tabla" if o["hora_utc"] < FRONTERA_OCR else "todo"
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

    def p2(b, v, canal, ref="B1", volcanes=None):
        sumas = collections.defaultdict(int)
        for i in oks:
            o = obj[i]
            if volcanes is not None and o["volcan"] not in volcanes:
                continue
            e = etiqueta(o, canal)
            if e not in ("baja", "neg") or not ventana(o, v):
                continue
            err = lambda x: int((e == "baja" and not pub(i, x)) or (e == "neg" and pub(i, x)))
            c = err(b) - err(ref)
            if c:
                sumas[(o["hora_utc"][:10], o["volcan"])] += c
        s = [sumas[k] for k in sorted(sumas)]
        neto = sum(s)
        pr_ = EV.prueba_signos_p2(s, neto)
        return EV.regla_signos_p2(neto, len(s), pr_), neto, len(s), pr_

    # controles del instrumento de la ROI, DENTRO de la compuerta (VB-06; con filo tras VB2-06)
    # negativo: en Cordón Caulle y Tupungatito B4 ES B1 por construcción; el evaluador tiene que dar 0 bloques ahí
    neg_ctrl = p2("B4", "TO", "decide", volcanes=VOL_SENS)
    # positivo: B0 pierde protegidas de Cordón Caulle que B1 sí publica (con el oráculo muerto, B1 no publicaría)
    pcc = [i for i in oks if obj[i]["volcan"] == "PuyehueCordonCaulle"
           and etiqueta(obj[i], "decide") == "prot" and not pub(i, "B0")]
    pcc_b1 = [i for i in pcc if pub(i, "B1")]
    pr("== control negativo P2 (B4 contra B1 en Cordón Caulle y Tupungatito, idénticos por construcción):",
       neg_ctrl[:3], "(tiene que ser SIN SUSTRATO con 0 bloques)")
    pr("== control positivo: protegidas de Cordón Caulle que B0 pierde", len(pcc), "y de ésas B1 publica", len(pcc_b1),
       [obj[i]["hora_utc"] for i in pcc][:10], "(B0 pierde 1 o más y B1 publica 3 o más)")
    ctrl_roi = neg_ctrl[0] == "SIN SUSTRATO" and neg_ctrl[2] == 0 and len(pcc) >= 1 and len(pcc_b1) >= 3
    # VB2-03 y VB2-04: los dos caminos de excepción, marcados en cada línea de veredicto y con su propio código
    # cada bandera cubre sólo lo suyo: la de pruebas, el censo; --leer-con-faltantes, la cobertura y el censo
    aviso, rc_final = "", 0
    faltan = not (cob_ok and censo_ok)
    if faltan and a.leer_con_faltantes:
        aviso, rc_final = f"[LEÍDO CON FALTANTES: {a.leer_con_faltantes}] ", 5
    if a.censo_omitido_solo_pruebas:
        aviso, rc_final = "[SIN CENSO, NO VALE PARA EL RUN] " + aviso, 4
    cob_pasa = cob_ok or bool(a.leer_con_faltantes)
    # VB3-06: la bandera de pruebas sólo reemplaza un censo AUSENTE; un censo que corrió y falló cierra igual
    censo_pedido = bool(a.censo_art and a.censo_objetivos)
    censo_pasa = censo_ok or (a.censo_omitido_solo_pruebas and not censo_pedido) or bool(a.leer_con_faltantes)
    gen_ok = bool(nidx) and c_nulo == 0 and k_ok
    todo_ok = gen_ok and ctrl_roi and cob_pasa and censo_pasa
    pr("== compuerta del veredicto (generales, ROI, cobertura y censo):", "ABIERTA" if todo_ok else "CERRADA",
       aviso.strip())
    if a.solo_controles or not todo_ok:
        pr("== sin veredicto:", "--solo-controles" if a.solo_controles else "controles caídos o SIN DATO")
        return salir(0 if (a.solo_controles and todo_ok) else 3)   # VB3-05: compuerta cerrada = 3 siempre

    # ---------------------------------------------------------------- métricas y regla §6
    ver = {}
    for canal in ("decide", "tabla", "todo"):
        for v in ("T", "O", "TO"):
            pr(f"\n== ventana {v}, canal {canal}")
            for b in BRAZOS:
                m = metricas(b, v, canal)
                linea = (f"   {b:3s} prot {m['n_prot']:4d} P1 {m['P1']:3d} | P1b abajo {m['P1b_abajo']:3d} arriba "
                         f"{m['P1b_arriba']:3d} | E {m['E']:4d} (bajas sin publicar {m['E_baja']} de {m['n_baja']}, "
                         f"neg publicados {m['E_neg']} de {m['n_neg']})")
                reg, neto = None, 0
                if b not in ("B1", "K"):
                    reg, neto, nb, prr = p2(b, v, canal)
                    linea += f" | P2 contra B1: {reg} (neto {neto}, bloques {nb}, p gana {prr['gana']}, pierde {prr['pierde']})"
                ver[(b, v, canal)] = (m["P1"], reg, m["E"], neto)
                pr(linea)
    # §6.1: P1 = 0 en el canal que decide (T con la tabla sola, O con tabla más OCR) y en O también con la tabla sola
    elegibles = [b for b in CANDIDATOS if ver[(b, "TO", "decide")][0] == 0 and ver[(b, "O", "tabla")][0] == 0]
    pr("\n== §6.1 elegibles:", elegibles)
    def no_peor(b, canal):
        """No es peor que B1 en P2: GANA o EMPATE, o SIN SUSTRATO con el neto en 0 o a favor (VB2-02: con 4 bloques o
        menos la prueba no puede rechazar, y un neto en contra no se premia)."""
        _p1, reg, _e, neto = ver[(b, "TO", canal)]
        return reg in ("GANA", "EMPATE") or (reg == "SIN SUSTRATO" and neto <= 0)

    # §6.2: GANA contra B1 en el canal que decide sobre T y O juntos, y no es peor con la tabla sola
    ganan = [b for b in elegibles if b != "B1" and ver[(b, "TO", "decide")][1] == "GANA" and no_peor(b, "tabla")]
    if ganan:
        elegido = min(ganan, key=lambda b: ver[(b, "TO", "decide")][2])
        motivo = f"gana contra B1 (§6.2): {ganan}"
    else:
        # §6.3: sin ganadores, entre B1 y los que no son peores que B1 ni en el canal que decide ni con la tabla sola
        # (VB-01, VB2-01, VB2-02)
        cand = [b for b in PREF if b in elegibles and (b == "B1" or (no_peor(b, "decide") and no_peor(b, "tabla")))]
        elegido = cand[0] if cand else None
        motivo = ("ninguno gana contra B1; orden de cercanía al .m entre los que no pierden (§6.3)" if cand
                  else "NINGÚN BRAZO ELEGIBLE")
    pr(f"== §6 {aviso}ROI elegida: {elegido} ({motivo})")
    if elegido in ("B2", "B4"):
        pr("   §6.5: ROI por volcán; Nicolás confirma que es fidelidad al .m antes de pasarla a V750-A")

    # ---------------------------------------------------------------- descriptivas
    pr("\n== razón brazo/MIROVA en alertas que deciden publicadas (mediana [q1, q3] n)")
    for b in BRAZOS:
        rz = sorted(vrp(i, b) / obj[i]["mirova_vrp"] for i in oks if etiqueta(obj[i], "decide") in ("prot", "baja")
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
                e = etiqueta(obj[i], "decide")
                if e:
                    m[e] += 1
                    m[e + "_pub"] += pub(i, b)
            lin.append(f"{b} prot {m['prot_pub']}/{m['prot']} baja {m['baja_pub']}/{m['baja']} neg {m['neg_pub']}/{m['neg']}")
        pr(f"   {vol}: " + " | ".join(lin))
    pr("\n== por tramo de 10° de cenit: negativos publicados y protegidas perdidas")
    for b in BRAZOS:
        t = collections.Counter()
        for i in oks:
            e = etiqueta(obj[i], "decide")
            z = tramo_z(obj[i].get("z"))
            if e == "neg" and pub(i, b):
                t[(z, "neg")] += 1
            if e == "prot" and not pub(i, b):
                t[(z, "P1")] += 1
        pr(f"   {b}: {dict(sorted(t.items()))}")

    # ---------------------------------------------------------------- V750-C: brazo nativo en S_C, por cenit
    sc = [i for i in oks if obj[i].get("en_sc") and res[i].get("nativo")]
    pr(f"\n== V750-C, brazo nativo (cajas en km): pasadas de S_C con nativo {len(sc)}")

    def en_pixel_k(i, nombre):
        k = res[i]["brazos"]["K"]
        pix = k.get("pc_pix") or []
        r0, c0 = res[i]["nativo_esquina_fila_col"]
        al = [(p[0], p[1]) for p in res[i]["nativo"][nombre]["pixeles"]]
        return any(abs(a - (f - r0)) <= 1 and abs(b - (c - c0)) <= 1 for f, c in pix for a, b in al)

    def zc(i):
        return tramo_z((res[i].get("geometria_centro") or {}).get("sensor_zenith"))

    grupos = {"cumbre0_neg": lambda o: o.get("dc") == "summit" and o.get("pc_vrp") == 0 and o["lab"] == "neg_limpio",
              "cumbre0_pos": lambda o: o.get("dc") == "summit" and o.get("pc_vrp") == 0 and o["lab"] == "pos",
              "neg_sin_K": lambda o: o["lab"] == "neg_limpio" and not o.get("pc_n")}
    for g, f in grupos.items():
        ids = [i for i in sc if f(obj[i])]
        if not ids:
            continue
        for zt in sorted({zc(i) for i in ids}) + ["todo"]:
            sub = [i for i in ids if zt == "todo" or zc(i) == zt]
            lin = [f"{g} cenit {zt} n={len(sub)}"]
            for nombre, grilla in (("N0", "B0"), ("N1", "B1")):
                det_k = sum(en_pixel_k(i, nombre) for i in sub)
                alg = sum(bool(res[i]["nativo"][nombre]["npix"]) for i in sub)
                alg_g = sum(bool(res[i]["oraculo"][grilla]["npix"]) for i in sub)
                lin.append(f"{nombre}: en el píxel de K {det_k}, con algún píxel {alg} (grilla {grilla}: {alg_g})")
            pr("   " + " | ".join(lin))
    if aviso:
        pr(f"== {aviso.strip()}: el veredicto de arriba lleva esta marca")
    return salir(rc_final)


if __name__ == "__main__":
    sys.exit(main())
