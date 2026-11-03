# -*- coding: utf-8 -*-
"""S162 V750-B, adenda 2: diagnóstico de la regla de posición del record (radiante, cercano y pico). NO DECIDE V750-B.

POR QUÉ. Nicolás (2026-10-27, programa §7): «no fijes la regla todavía; mídela como brazo (radiante, cercano y pico)
en los A/B de cada sensor contra lo que publica MIROVA». En VIIRS 750 la regla decide en una sola escena: un píxel
débil cerca del cráter y una fuente más radiante lejos (otro foco, borde de nube, incendio). El analizador sellado
ubica el record en el centroide del cúmulo 8-conexo del alertado más radiante; si ese cúmulo cae fuera del radio
interior, el record es `far` y el tablero calla. Con «cercano» el mismo record queda `summit` y el tablero publica la
suma de todos los alertados, que en esa escena viene sobre todo de la fuente lejana. Con «pico» manda el píxel más
radiante solo, sin promediar su cúmulo.

Qué hace, sobre los MISMOS resultados del run y la MISMA detección de cada caja (sólo cambia el punto desde donde se
mide la distancia del record; el VRP, el cúmulo y todo lo demás quedan como los arma el analizador sellado):
  radiante  record_cumulo del analizador sellado, sin tocar (centroide del cúmulo del alertado más radiante);
  cercano   el alertado más cercano al cráter;
  pico      el alertado de mayor M13 (el mismo que siembra el cúmulo, con el mismo desempate de max()).
Publica = el predicado del tablero, con node (A97). Métricas y prueba de signos: las del analizador sellado (§5),
extraídas con ast de su main() y ejecutadas sin copiar a mano; el analizador se identifica por sha256 (fin de línea
normalizado a LF, porque git en Windows lo convierte).

La vara es lo que publica MIROVA: en las pasadas con alerta o negativo limpio, las etiquetas del sellado; en las
pasadas `far_ref` de la lista suplementaria (MIROVA ubicó el calor lejos del cráter), lo correcto es NO publicar, y
además se compara la distancia que ve cada brazo (medida desde el centro de la grilla, que es desde donde mide
MIROVA) con la que publicó MIROVA. Esa comparación es de RADIOS, no de posiciones (A93): sirve para descartar, no
para afirmar que es el mismo objeto.

Controles (si uno cae, sale 3 y la salida dice DIAGNÓSTICO NO LEGIBLE):
  C1 en las cajas con un solo alertado los tres brazos coinciden (distancia y publicación): 0 diferencias, con al
     menos un caso;
  C2 nulo del predicado: un record radiante publicado, pasado a `far`, deja de publicar (0 que sigan, al menos uno);
  C3 las listas: ids suplementarios desde 100000 sin choque con los sellados, y el archivo de pasadas sin gránulo
     de la suplementaria atado a ella por sha256;
  C4 el analizador sellado es el del tag (sha256).
Uso (rutas absolutas):
  python <repo>/experiments/_s162_v750b/adenda2/leer_posicion_v750b.py --art <artefactos del run>
      --objetivos <...>/objetivos_v750b.json --objetivos-supl <...>/adenda2/objetivos_supl_v750b.json
      --sin-granulo-supl <...>/adenda2/sin_granulo_supl_v750b.json --evaluador <evaluar_d25.py del tag s161-d25-lectura>
"""
from __future__ import annotations

import argparse
import ast
import collections
import copy
import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
V750B = Path(r'C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-2-918174\experiments\_s162_v750b')
ANALIZADOR = V750B / "analizar_v750b.py"
SHA_ANALIZADOR_LF = "83b7159bd0666871b2e88a48c23feba4900ae28c24abd76b6cb3abf7b2593392"   # tag s162-v750b-sellado
BRAZOS_POS = ("radiante", "cercano", "pico")
CAJAS_LECTURA = ("B0", "B1", "B2", "B3", "B4", "B5")
EXTRAER = ("prot_tabla", "etiqueta", "ventana", "metricas", "p2")
ID0 = 100000


def sha_lf(ruta):
    return hashlib.sha256(Path(ruta).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def cargar_analizador(ruta):
    spec = importlib.util.spec_from_file_location("analizar_v750b_sellado", ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def funciones_de_main(ruta, nombres=EXTRAER):
    """Texto literal de las funciones anidadas en main() del analizador sellado (sin copiar a mano)."""
    import textwrap
    src = Path(ruta).read_text(encoding="utf-8")
    arbol = ast.parse(src)
    main = next(n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    piezas = {n.name: textwrap.dedent(ast.get_source_segment(src, n)) for n in main.body
              if isinstance(n, ast.FunctionDef) and n.name in nombres}
    faltan = set(nombres) - set(piezas)
    assert not faltan, f"el analizador sellado no trae {faltan} en main()"
    return [piezas[n] for n in nombres]


def punto(o, brazo, ancla, A):
    """(fila, columna) del punto que ubica el record según el brazo; None si la caja no alertó nada."""
    if not o or not o.get("npix") or o.get("vrp_mw") is None:
        return None
    px = o["pixeles"]
    if brazo == "radiante":
        cu = A.cumulo_del_mas_radiante(px)
        return float(np.mean([a for a, _ in cu])), float(np.mean([b for _, b in cu]))
    if brazo == "cercano":
        p = min(px, key=lambda p: (np.hypot(p[0] - ancla[0], p[1] - ancla[1]), p[0], p[1]))
        return float(p[0]), float(p[1])
    p = max(px, key=lambda p: p[4])
    return float(p[0]), float(p[1])


def record_pos(o, inner, sensor, ancla, brazo, A):
    """El record del analizador sellado, con la distancia (y su clase) medida desde el punto del brazo."""
    rec = A.record_cumulo(o, inner, sensor, ancla)
    if brazo == "radiante" or not rec.get("primary_cluster"):
        return rec
    f, c = punto(o, brazo, ancla, A)
    d = float(np.hypot(f - ancla[0], c - ancla[1]) * 0.75)
    rec = copy.deepcopy(rec)
    rec["distance_class"] = "summit" if d <= inner else "far"
    rec["primary_cluster"]["centroid_dist_km"] = round(d, 3)
    return rec


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True, nargs="+")
    ap.add_argument("--objetivos", required=True)
    ap.add_argument("--objetivos-supl", required=True)
    ap.add_argument("--sin-granulo-supl", required=True)
    ap.add_argument("--evaluador", required=True)
    ap.add_argument("--analizador", default=str(ANALIZADOR), help="sólo para la batería; el run usa el sellado")
    ap.add_argument("--salida", default=str(AQUI / "leer_posicion_v750b_salida.txt"))
    a = ap.parse_args(argv)
    L = []

    def pr(*x):
        s = " ".join(str(y) for y in x)
        print(s, flush=True)
        L.append(s)

    def salir(cod):
        Path(a.salida).write_text("\n".join(L) + "\n", encoding="utf-8")
        return cod

    pr("== DIAGNÓSTICO de posición (adenda 2 de V750-B): no decide V750-B; insumo de V750-A")
    c4 = sha_lf(a.analizador) == SHA_ANALIZADOR_LF
    pr("== C4 analizador sellado (sha256 con fin de línea LF):", "OK" if c4 else "DISTINTO DEL TAG")
    if not c4:   # no se carga un analizador que no es el sellado: ni sus funciones ni sus rutas valen
        pr("== controles C1 a C4: CAÍDOS: DIAGNÓSTICO NO LEGIBLE")
        return salir(3)
    A = cargar_analizador(a.analizador)
    EV = A.cargar_signos(a.evaluador)
    sell = json.loads(Path(a.objetivos).read_text(encoding="utf-8"))
    supl_txt = Path(a.objetivos_supl).read_text(encoding="utf-8")
    supl = json.loads(supl_txt)
    ids_s = {o["id"] for o in sell}
    ids_p = {o["id"] for o in supl}
    dsg = json.loads(Path(a.sin_granulo_supl).read_text(encoding="utf-8"))
    sg_ok = dsg.get("objetivos_sha256") == hashlib.sha256(supl_txt.encode("utf-8")).hexdigest()
    c3 = (all(i >= ID0 for i in ids_p) and all(i < ID0 for i in ids_s) and not (ids_s & ids_p)
          and all(o.get("lab") == "far_ref" for o in supl) and sg_ok)
    pr(f"== C3 listas: selladas {len(sell)}, suplementarias {len(supl)} (todas far_ref, ids desde {ID0}), "
       f"sin gránulo de la suplementaria {len(dsg.get('pasadas', []))} y atado a ella: {sg_ok}:", "OK" if c3 else "FALLA")
    obj = {o["id"]: o for o in sell + supl}
    res = A.cargar(a.art)
    inner = A.B.inner_desde_html()

    part = {i: A.partida(res.get(i) or {}) for i in obj}
    oks = [i for i in obj if part[i] == "observada" and res[i].get("dayflag") == 0
           and set(A.CAJAS) <= set(res[i].get("oraculo") or {})]
    sin = [i for i in obj if i not in oks and part[i] not in ("fuera", "sin_crater")]
    for nombre, ids in (("selladas", ids_s | ids_p), ("suplementarias", ids_p)):
        pr(f"   {nombre}: observadas {sum(i in ids for i in oks)} | no observadas "
           f"{sum(i in ids and part[i] in ('fuera', 'sin_crater') for i in obj)} | SIN DATO {sum(i in ids for i in sin)}")
    pr("   suplementarias SIN DATO por nombre:",
       [(obj[i]["volcan"], obj[i]["hora_utc"], (res.get(i) or {}).get("estado", "sin_resultado")[:30])
        for i in sorted(sin) if i in ids_p] or "ninguna")
    pr("   suplementarias sin gránulo (del generador, SIN DATO declarado):",
       [(x["volcan"], x["hora_utc"]) for x in dsg.get("pasadas", [])] or "ninguna")

    def ancla(i):
        return tuple(obj[i].get("pos_crater") or (A.C, A.C))

    # VAD2-02: como el analizador sellado (§7, l. 291-298), salen de todos los brazos las pasadas en que el K del probe
    # no reproduce la publicación de producción; así la fila «radiante» calza con B0 a B5 del veredicto sellado
    kp = A.B.correr_node([[A.slim((res[i].get("brazos") or {}).get("K", {}).get("record")), inner[obj[i]["volcan"]]]
                          for i in oks]) if oks else []
    k_dist = [i for i, q in zip(oks, kp) if bool(obj[i].get("pub_prod")) != bool(q[4])]
    pr(f"   pasadas con K distinto de producción (salen, como en el sellado): {len(k_dist)} "
       f"{[(obj[i]['volcan'], obj[i]['hora_utc']) for i in k_dist][:20]}")
    oks = [i for i in oks if i not in set(k_dist)]

    casos, idx = [], []
    for i in oks:
        o = obj[i]
        for c in A.CAJAS:
            for b in BRAZOS_POS:
                casos.append([record_pos(res[i]["oraculo"][c], inner[o["volcan"]], o["sensor"], ancla(i), b, A),
                              inner[o["volcan"]]])
                idx.append((i, c, b))
    P = {k: bool(p[4]) for k, p in zip(idx, A.B.correr_node(casos))} if casos else {}

    # C1: un solo alertado -> los tres brazos coinciden
    n1, dif1 = 0, []
    for i in oks:
        for c in A.CAJAS:
            o = res[i]["oraculo"][c]
            if o and o.get("npix") == 1 and o.get("vrp_mw") is not None:
                n1 += 1
                recs = [record_pos(o, inner[obj[i]["volcan"]], obj[i]["sensor"], ancla(i), b, A) for b in BRAZOS_POS]
                if (len({r["distance_class"] for r in recs}) > 1 or len({P[(i, c, b)] for b in BRAZOS_POS}) > 1
                        or len({r["primary_cluster"]["centroid_dist_km"] for r in recs}) > 1):
                    dif1.append((obj[i]["volcan"], obj[i]["hora_utc"], c))
    c1 = n1 > 0 and not dif1
    pr(f"== C1 cajas con un solo alertado: {n1}; con brazos distintos {len(dif1)} {dif1[:10]}:", "OK" if c1 else "FALLA")
    # C2: nulo del predicado sobre la distancia
    nulo = []
    for i in oks:
        for c in A.CAJAS:
            if P[(i, c, "radiante")]:
                r = record_pos(res[i]["oraculo"][c], inner[obj[i]["volcan"]], obj[i]["sensor"], ancla(i), "radiante", A)
                r = copy.deepcopy(r)
                r["distance_class"] = "far"
                nulo.append([r, inner[obj[i]["volcan"]]])
    sigue = sum(bool(p[4]) for p in A.B.correr_node(nulo)) if nulo else 0
    c2 = bool(nulo) and sigue == 0
    pr(f"== C2 nulo del predicado: {len(nulo)} records radiantes publicados pasados a far; siguen publicando {sigue}:",
       "OK" if c2 else "FALLA")

    def pub(i, x):
        c, b = x.split("|")
        return P[(i, A.caja_de(c, obj[i]["volcan"]), b)]

    def vrp(i, x):
        c, _b = x.split("|")
        return res[i]["oraculo"][A.caja_de(c, obj[i]["volcan"])].get("vrp_mw") or 0.0

    ns = {"collections": collections, "alerta_protegida": A.alerta_protegida, "FRONTERA_OCR": A.FRONTERA_OCR,
          "oks": oks, "obj": obj, "pub": pub, "vrp": vrp, "EV": EV}
    for texto in funciones_de_main(a.analizador):
        exec(compile(texto, str(a.analizador), "exec"), ns)
    ctrl = c1 and c2 and c3 and c4
    pr("== controles C1 a C4:", "EN VERDE" if ctrl else "CAÍDOS: DIAGNÓSTICO NO LEGIBLE")
    if not ctrl:
        return salir(3)

    for canal in ("decide", "tabla"):
        pr(f"\n== alertas y negativos limpios (ventana T y O juntas, canal {canal}); P2 contra radiante de la misma caja")
        for c in CAJAS_LECTURA:
            for b in BRAZOS_POS:
                x = f"{c}|{b}"
                m = ns["metricas"](x, "TO", canal)
                lin = (f"   {c} {b:8s} prot {m['n_prot']:4d} P1 {m['P1']:3d} | E {m['E']:4d} (bajas sin publicar "
                       f"{m['E_baja']} de {m['n_baja']}, neg publicados {m['E_neg']} de {m['n_neg']})")
                if b != "radiante":
                    reg, neto, nb, prr = ns["p2"](x, "TO", canal, ref=f"{c}|radiante")
                    camb = collections.Counter(
                        (ns["etiqueta"](obj[i], canal) or "otra", "publica" if pub(i, x) else "calla")
                        for i in oks if obj[i]["id"] < ID0 and pub(i, x) != pub(i, f"{c}|radiante"))
                    lin += f" | P2 {reg} (neto {neto}, bloques {nb}) | cambian contra radiante {dict(camb) or 'ninguna'}"
                pr(lin)
    pr("\n== pasadas que cambian de publicación contra radiante (caja B0 y B1, por nombre)")
    for c in ("B0", "B1"):
        for b in ("cercano", "pico"):
            lst = [(obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["lab"], "publica" if pub(i, f"{c}|{b}") else "calla")
                   for i in oks if pub(i, f"{c}|{b}") != pub(i, f"{c}|radiante")]
            pr(f"   {c} {b}: {len(lst)} {lst[:20]}")

    far = [i for i in oks if i in ids_p]
    pr(f"\n== pasadas far_ref (MIROVA ubicó el calor lejos; lo correcto es no publicar): observadas {len(far)}")
    for c in CAJAS_LECTURA:
        # VAD2-07: un 0 de «publica» sólo dice algo en las pasadas donde la caja alertó algo
        con = sum(bool((res[i]["oraculo"][A.caja_de(c, obj[i]["volcan"])] or {}).get("npix")) for i in far)
        pr("   " + c + f": con algún alertado {con} de {len(far)} | " + " | ".join(
            f"{b} publica {sum(pub(i, f'{c}|{b}') for i in far)}" for b in BRAZOS_POS)
           + " | lista " + str([(obj[i]["volcan"], obj[i]["hora_utc"], "".join(b[0] for b in BRAZOS_POS
                                                                               if pub(i, f"{c}|{b}")))
                                for i in far if any(pub(i, f"{c}|{b}") for b in BRAZOS_POS)][:20]))

    pr("\n== distancia de cada brazo desde la celda central de la grilla (33, 33; el punto de referencia de MIROVA queda "
       "a hasta 0,35 km de ella) contra la de MIROVA (diferencia de RADIOS, A93: cota inferior de la separación; OCR "
       "sólo desde el 2026-06-13; |delta| mediana, fracción a 1 km o menos, n)")
    for grupo, sel in (("alertas con distancia", lambda o: o["lab"] == "pos"), ("far_ref", lambda o: o["lab"] == "far_ref")):
        for c in ("B0", "B1"):
            lin = []
            for b in BRAZOS_POS:
                dd = []
                for i in oks:
                    o = obj[i]
                    if not sel(o):
                        continue
                    # VAD2-05 (A119): la distancia del OCR no vale antes del 2026-06-13; antes de esa fecha, sólo la tabla
                    ref = o.get("dist_ref") if o["lab"] == "far_ref" else next(
                        (f.get("dist_km") for f in o.get("mirova") or [] if f.get("dist_km") is not None
                         and str(f.get("tipo", "")).startswith("ALERTA")
                         and (f.get("source") == "CONS" or o["hora_utc"] >= A.FRONTERA_OCR)), None)
                    pt = punto(res[i]["oraculo"][A.caja_de(c, o["volcan"])], b, ancla(i), A)
                    if ref is None or pt is None:
                        continue
                    dd.append(abs(float(np.hypot(pt[0] - A.C, pt[1] - A.C) * 0.75) - float(ref)))
                lin.append(f"{b} {statistics.median(dd):.2f} km, {sum(x <= 1 for x in dd) / len(dd):.2f}, n={len(dd)}"
                           if dd else f"{b} -")
            pr(f"   {grupo} {c}: " + " | ".join(lin))
    return salir(0)


if __name__ == "__main__":
    sys.exit(main())
