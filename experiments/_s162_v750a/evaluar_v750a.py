# -*- coding: utf-8 -*-
"""S162 V750-A, analizador pre-registrado (PREREGISTRO_V750A.md §4 a §7): el paquete del código de MIROVA (P) contra K
en VIIRS 750.

POR QUÉ. La adopción del paquete se decide midiendo contra MIROVA en las dos direcciones, con la regla escrita antes de
ver los datos (§6): no perder ninguna protegida que K publica (P1), no equivocarse más que K bajo 1 MW (P2, prueba de
signos por bloque noche-volcán, D-45) y medir la magnitud de MIROVA mejor que K y mejor que una ganancia pareja de K
(M con el comparador d′ de D-28/D-30/D-32 y el placebo K×1,2). Los controles (§7) se imprimen primero y, si caen, no
se imprime ningún veredicto; si la vía no reproduce al oráculo (§6.1), el censo no se mira.

QUÉ REUSA, SIN REIMPLEMENTAR NI COPIAR A MANO:
  * de experiments/_s162_v750b/analizar_v750b.py (sellado, tag s162-v750b-sellado): la carga de artefactos, la partida
    de cada pasada (observada / fuera / sin cráter / SIN DATO), el record del cúmulo 8-conexo del píxel alertado más
    radiante con la distancia medida desde el cráter (record_cumulo), el record de K para el predicado (slim), los
    tramos de cenit, la frontera del OCR y la extracción con ast de la prueba de signos de D-45 con el sha256 del
    evaluador fijado (cargar_signos). Las etiquetas, P2 y el nulo del contador viven dentro del main() de ese archivo y
    no se pueden importar: se copian aquí con la misma lógica y se marca cada copia.
  * de experiments/_s157_prereg_d25/evaluar_d25.py del tag s161-d25-lectura (mismo sha256): M entera, extraída con ast
    (decidir_estrato con su bootstrap por bloques, la calibración simétrica, comparar_con_ganancia con d′ y sus
    constantes selladas), sin importar el resto del evaluador de D25.

Brazos (§3): K (producción, control), Kgemelo (K en otro proceso del mismo runner, nulo), K×1,2 (placebo, se arma aquí
desde K como en evaluar_d25.py: VRP de K por 1,2, el resto igual), Kgeo (diagnóstico de V750-D, sólo informa), P, P-def
y O (salidas del .m sobre la grilla GEO: npix, vrp_mw, píxeles y diagnóstico), P-sinfiltro (el record de P con la
distancia neutralizada, publicado por el mismo predicado).

Formato de los artefactos (contrato para el probe o el cálculo local que los produzca):
  objetivos: lista de {id, volcan, hora_utc "AAAA-MM-DD HH:MM", sensor, lab ("pos" | "neg_limpio" | otro), decide,
    alerta_tabla, protegida, mirova [filas], mirova_vrp, pub_prod, pc_vrp, z (cenit del sensor), pos_crater [f, c]}
  resultados_*.json: lista de {id, estado, dayflag, cobertura {nan_7_crater, nan_crater},
    brazos {K, Kgemelo, [Kgeo], [P en la sombra]: {record}}, paquete {P, Pdef, O: salida del .m}, banda_triangulacion}
  salida del .m: {npix, vrp_mw, pixeles [[fila, col, zona, -, M13]], diag {pasada1, pasada2: {sd_nti, sd_eti,
    u_nti1, u_nti2, u_eti1, u_eti2}, celda_decisiva: {pase, zona, c_nti, c_eti}}}
Las lecturas tomadas donde el pre-registro deja algo abierto están en LECTURAS_EVALUAR_V750A.md.

Uso: python evaluar_v750a.py [--fase censo|sombra] --art <carpetas> --objetivos objetivos_v750a.json
     --evaluador <evaluar_d25.py del tag> [--sin-granulo <archivo>] [--equivalencia-local <salida verde + mutaciones>]
     [--leer-con-faltantes MOTIVO] [--solo-controles] [--salida <archivo>]
Salida: 0 con veredicto; 3 compuerta cerrada (controles caídos o SIN DATO); 5 veredicto leído con faltantes (marcado);
        6 §6.1 no se cumple (la vía no reproduce al oráculo: no se mira el censo).
"""
from __future__ import annotations

import argparse
import ast
import collections
import copy
import hashlib
import json
import math
import random
import re
import statistics
import sys
import types
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "experiments/_s158_audit_r2/oraculo"))
sys.path.insert(0, str(RAIZ / "experiments/_s162_v750b"))
import banco_paridad as B  # noqa: E402
from clase_mirova import alerta_protegida  # noqa: E402
import analizar_v750b as AB  # noqa: E402

PAQUETE = ("P", "Pdef", "O")
VENTANAS = ("T", "O")                    # §4.2: T tabla sola hasta el 2026-06-12, O desde el 2026-06-13
CANALES = ("tabla", "todo")              # §6.2: con la tabla sola Y con tabla más OCR
GANANCIA_PLACEBO = 1.2                   # §3, programa §2
TOL_VRP_EQUIV = 1e-6                     # §4.1: VRP a 1e-6 MW en el runner
BANDA_RAZON = (0.9, 1.1)                 # §6.2: mediana de la razón de P en las protegidas
MIN_MUT_LOCAL = 5                        # §6.1: «5 de 5 mutaciones atrapadas por aserción» (LECTURA L2)
MIN_CASOS_LOCAL = (1020, 10)             # §4.1: 510 grillas de N con 2 cajas (E1) y los 10 recortes nativos de R2 (E3)
PARES_S1 = (("P", "Pdef"), ("P", "O"), ("Pdef", "O"))   # §5, S-1: los brazos que comparten la detección del .m
VOL_ROI = "PuyehueCordonCaulle"          # §7, control positivo de la ROI

NOMBRES_M = ("N_BOOT", "SEMILLA", "N_MIN_PARES", "N_MIN_NOCHES", "N_CALIB", "MAX_FALSOS_CALIB",
             "MIN_VOLCANES_MEJORA", "MIN_PARES_VOLCAN", "MIN_PARES_PODER", "PLACEBO_GANANCIAS", "NOTA_COMPARADOR",
             "SEMILLA_CALIB_DPRIMA", "N_CALIB_DPRIMA", "NOTA_CALIB_DPRIMA", "DEC_DPRIMA",
             "pesos_bloque", "medianas_ponderadas", "medianas_ponderadas_filas", "regla_m", "d_par", "calibrar",
             "calibrar_simetrico", "comparar_con_ganancia", "decidir_estrato")


def cargar_m(ruta):
    """Extrae de evaluar_d25.py (tag s161-d25-lectura), con ast y en el orden del archivo, el texto literal de M y de
    sus constantes selladas, y lo ejecuta aparte (como AB.cargar_signos con la prueba de signos). Falla si el archivo no
    es el del tag o si falta alguna pieza."""
    crudo = Path(ruta).read_bytes()
    assert hashlib.sha256(crudo).hexdigest() == AB.SHA_EVALUADOR, "evaluar_d25.py no es el del tag s161-d25-lectura"
    src = crudo.decode("utf-8")
    piezas = []
    for nodo in ast.parse(src).body:
        if isinstance(nodo, ast.FunctionDef):
            nombres = {nodo.name}
        elif isinstance(nodo, ast.Assign):
            nombres = {e.id for t in nodo.targets for e in (t.elts if isinstance(t, ast.Tuple) else [t])
                       if isinstance(e, ast.Name)}
        else:
            continue
        if nombres & set(NOMBRES_M):
            piezas.append((nombres, ast.get_source_segment(src, nodo)))
    faltan = set(NOMBRES_M) - set().union(*(n for n, _ in piezas))
    assert not faltan, f"evaluar_d25.py sin {faltan}"
    m = types.ModuleType("m_d28")
    m.__dict__.update({"collections": collections, "np": np, "math": math})
    exec(compile("\n\n".join(t for _, t in piezas), str(ruta), "exec"), m.__dict__)
    assert (m.N_BOOT, m.SEMILLA, m.SEMILLA_CALIB_DPRIMA, m.N_CALIB_DPRIMA, m.DEC_DPRIMA) == (10000, 157, 160, 1000, 12)
    assert m.PLACEBO_GANANCIAS[0] == GANANCIA_PLACEBO
    return m


# ---------------------------------------------------------------- etiquetas (copia de analizar_v750b.main)
def prot_tabla(o):
    return any(alerta_protegida(f) for f in o.get("mirova") or [] if f.get("source") == "CONS")


def etiqueta(o, canal):
    """'prot', 'baja' (alerta bajo 1 MW que decide), 'neg' o None. Copia literal de la de analizar_v750b.py: canal
    'tabla' (sólo la tabla de MIROVA), 'todo' (tabla más OCR) o 'decide' (tabla sola en T, tabla más OCR en O)."""
    if canal == "decide":
        canal = "tabla" if o["hora_utc"] < AB.FRONTERA_OCR else "todo"
    if o["lab"] == "neg_limpio":
        return "neg"
    if o["lab"] != "pos" or not o.get("decide"):
        return None
    if canal == "tabla" and not o.get("alerta_tabla"):
        return None
    p = prot_tabla(o) if canal == "tabla" else o.get("protegida")
    return "prot" if p else "baja"


def en_ventana(o, v):
    h = o["hora_utc"]
    return v == "TODO" or (v == "T" and h < AB.FRONTERA_OCR) or (v == "O" and h >= AB.FRONTERA_OCR)


# ---------------------------------------------------------------- S-1 (§5, obligatorio, no decide)
def _u(dg, pase, zona, x):
    """Umbral contextual del .m para la celda: zonas 0 y 1 usan u1, la zona 2 usa u2 (.m l. 389-399)."""
    return dg[f"pasada{pase}"][f"u_{x}{2 if zona == 2 else 1}"]


def diag_valido(dg):
    try:
        cd = dg["celda_decisiva"]
        vals = [cd["c_nti"], cd["c_eti"]] + [dg[f"pasada{p}"][k] for p in (1, 2) for k in
                                              ("sd_nti", "sd_eti", "u_nti1", "u_nti2", "u_eti1", "u_eti2")]
        return cd["pase"] in (1, 2) and cd["zona"] in (0, 1, 2) and all(
            v is not None and math.isfinite(v) for v in vals) and all(
            _u(dg, cd["pase"], cd["zona"], x) != 0 for x in ("nti", "eti"))
    except (KeyError, TypeError):
        return False


def margenes(dg):
    """(b) margen de la celda decisiva del cráter contra su umbral: c / u en NTI y en ETI."""
    cd = dg["celda_decisiva"]
    return tuple(cd[f"c_{x}"] / _u(dg, cd["pase"], cd["zona"], x) for x in ("nti", "eti"))


def alerta_celda(dg_celda, dg_umbral):
    """¿La celda decisiva de un brazo alerta con los umbrales de otro? El .m exige los dos tests a la vez (l. 389-399)."""
    cd = dg_celda["celda_decisiva"]
    return all(cd[f"c_{x}"] > _u(dg_umbral, cd["pase"], cd["zona"], x) for x in ("nti", "eti"))


def decidida_por_escena(dA, dB):
    """(c) Con la celda decisiva del cráter QUIETA, el solo cambio de umbral entre los dos brazos (que viene de la media
    y la sd de toda la grilla) cambia su alerta, en una dirección o en la otra."""
    return alerta_celda(dA, dA) != alerta_celda(dA, dB) or alerta_celda(dB, dB) != alerta_celda(dB, dA)


def delta_sd(dA, dB):
    """(a) cambio de sd del contraste NTI y ETI en el primer y el segundo pase, del brazo A al B."""
    return {f"{x}{p}": dB[f"pasada{p}"][f"sd_{x}"] - dA[f"pasada{p}"][f"sd_{x}"] for x in ("nti", "eti") for p in (1, 2)}


def leer_equivalencia_local(ruta):
    """§6.1, parte local: la salida de equivalencia_v750a.py contra el módulo real (VERDE) y su corrida --mutaciones."""
    if not ruta or not Path(ruta).exists():
        return False, "salida de la prueba local AUSENTE (SIN DATO)"
    lin = Path(ruta).read_text(encoding="utf-8").splitlines()
    casos = [tuple(int(n) for n in re.findall(r"E1 (\d+) casos, E3 (\d+) recortes", x)[0])
             for x in lin if x.startswith("VERDE:") and re.search(r"E1 \d+ casos, E3 \d+ recortes", x)]
    verde = (any(c[0] >= MIN_CASOS_LOCAL[0] and c[1] >= MIN_CASOS_LOCAL[1] for c in casos)
             and not any(x.startswith("ROJA") for x in lin))
    todas = any(x.strip() == "mutaciones: TODAS COMO SE ESPERA" for x in lin)
    n_atr = sum("atrapada por aserción" in x for x in lin)
    caida = any("control_que_se_cae" in x and "caída" in x for x in lin)
    ok = verde and todas and n_atr >= MIN_MUT_LOCAL and caida
    return ok, (f"prueba local: verde con los casos del §4.1 {verde} {casos}, mutaciones todas como se espera {todas}, atrapadas {n_atr} "
                f"(mínimo {MIN_MUT_LOCAL}), control caído {caida}")


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--fase", choices=("censo", "sombra"), default="censo")
    ap.add_argument("--art", required=True, nargs="+")
    ap.add_argument("--objetivos", required=True)
    ap.add_argument("--evaluador", required=True, help="evaluar_d25.py del tag s161-d25-lectura (sha256 fijado)")
    ap.add_argument("--sin-granulo", default=str(AQUI / "sin_granulo_v750a.json"))
    ap.add_argument("--equivalencia-local", default="",
                    help="salida de equivalencia_v750a.py contra el módulo real y con --mutaciones (§6.1)")
    ap.add_argument("--leer-con-faltantes", default="",
                    help="MOTIVO de la decisión de leer con cobertura insuficiente; veredicto marcado y salida 5")
    ap.add_argument("--solo-controles", action="store_true")
    ap.add_argument("--salida", default=str(AQUI / "evaluar_v750a_salida.txt"))
    a = ap.parse_args(argv)
    EV = AB.cargar_signos(a.evaluador)
    EM = cargar_m(a.evaluador)
    censo = a.fase == "censo"
    obj = {o["id"]: o for o in json.loads(Path(a.objetivos).read_text(encoding="utf-8"))}
    res = AB.cargar(a.art)
    inner = B.inner_desde_html()
    L = []

    def pr(*x):
        s = " ".join(str(y) for y in x)
        print(s, flush=True)
        L.append(s)

    def salir(cod):
        Path(a.salida).write_text("\n".join(L) + "\n", encoding="utf-8")
        return cod

    def nombre(i):
        return f"{obj[i]['volcan']} {obj[i]['hora_utc']}"

    pr(f"== V750-A, fase {a.fase}")
    # ---------------------------------------------------------------- cobertura (copia de analizar_v750b, §4.2)
    req_brazos = ("K", "Kgemelo") if censo else ("K", "P")

    def falta_brazo(r):
        br = r.get("brazos") or {}
        if any(not isinstance(br.get(x), dict) or "record" not in br[x] for x in req_brazos):
            return True
        return censo and not set(PAQUETE) <= set(r.get("paquete") or {})

    part = {i: AB.partida(res.get(i) or {}) for i in obj}
    motivo_sin = {}
    for i in obj:
        r = res.get(i) or {}
        if part[i] is None:
            motivo_sin[i] = str(r.get("estado") or "sin_estado")[:40]
        elif part[i] == "observada" and r.get("dayflag") != 0:
            motivo_sin[i] = "diurna"
        elif part[i] == "observada" and falta_brazo(r):
            motivo_sin[i] = "falta_brazo"      # una pasada «ok» incompleta es SIN DATO, no desaparece en silencio
    sin = list(motivo_sin)
    no_obs = collections.Counter(part[i] for i in obj if part[i] in ("fuera", "sin_crater"))
    oks0 = [i for i in obj if part[i] == "observada" and i not in motivo_sin]
    pr("== cobertura: objetivos", len(obj), "con resultado", len(res))
    pr(f"   observadas: {len(oks0)} | no observadas (fuera del denominador): {dict(no_obs)} | SIN DATO: {len(sin)}")
    pr("   SIN DATO por motivo:", dict(collections.Counter(motivo_sin.values())))
    prot_sin = [nombre(i) for i in sin if obj[i].get("protegida")]
    sg = Path(a.sin_granulo)
    sha_obj = hashlib.sha256(Path(a.objetivos).read_bytes()).hexdigest()
    sg_ok, sin_g = False, []
    if sg.exists():
        dsg = json.loads(sg.read_text(encoding="utf-8"))
        sg_ok = isinstance(dsg, dict) and dsg.get("objetivos_sha256") == sha_obj
        sin_g = dsg.get("pasadas", []) if sg_ok else []
    pr(f"   pasadas sin gránulo (del generador): {len(sin_g)}"
       + ("" if sg_ok else f" | ARCHIVO {'AUSENTE' if not sg.exists() else 'DE OTRA LISTA DE OBJETIVOS'}: SIN DATO"))
    prot_sin += [f"{x['volcan']} {x['hora_utc']}" for x in sin_g if x.get("protegida")]
    pr("   protegidas no observadas (fuera del denominador):",
       [nombre(i) for i in obj if part[i] in ("fuera", "sin_crater") and obj[i].get("protegida")] or "ninguna")
    pr("   protegidas SIN DATO (falla de cobertura, no de brazo):", prot_sin or "ninguna")
    den_cob = max(1, len(obj) + len(sin_g) - no_obs["fuera"] - no_obs["sin_crater"])
    cob_ok = sg_ok and len(sin) + len(sin_g) <= AB.MAX_SIN_DATO * den_cob and not prot_sin
    pr("== cobertura:", "SUFICIENTE" if cob_ok else
       f"INSUFICIENTE (más de {AB.MAX_SIN_DATO:.0%} sin procesar o una protegida): relanzar con SOLO las faltantes")

    # ---------------------------------------------------------------- publicación con node (A97)
    def anc(i):
        return tuple(obj[i].get("pos_crater") or (AB.C, AB.C))

    def rec_k(i, b):
        return AB.slim(res[i]["brazos"][b]["record"])

    def rec_paq(i, b):
        return AB.record_cumulo(res[i]["paquete"][b], inner[obj[i]["volcan"]], obj[i]["sensor"], anc(i))

    def rec_p(i):
        return rec_paq(i, "P") if censo else rec_k(i, "P")

    def rec_sinfiltro(i):
        """P-sinfiltro (§3): el record de P con la distancia neutralizada; el resto del predicado, igual."""
        r = rec_paq(i, "P")
        if r.get("primary_cluster"):
            r["distance_class"] = "summit"
            r["primary_cluster"]["centroid_dist_km"] = 0.0
        return r

    def rec_kx12(i):
        """Placebo (§3, como evaluar_d25.py): K con su VRP multiplicado por 1,2; la publicación no tendría que cambiar."""
        r = copy.deepcopy(rec_k(i, "K"))
        for k in ("vrp_mw", "vrp_mir_mw", "f5_core_vrp_mw"):
            if r.get(k) is not None:
                r[k] = r[k] * GANANCIA_PLACEBO
        if r.get("primary_cluster") and r["primary_cluster"].get("vrp_mw") is not None:
            r["primary_cluster"]["vrp_mw"] = r["primary_cluster"]["vrp_mw"] * GANANCIA_PLACEBO
        return r

    casos, idx = [], []

    def caso(i, b, r):
        casos.append([r, inner[obj[i]["volcan"]]])
        idx.append((i, b))

    for i in oks0:
        caso(i, "K", rec_k(i, "K"))
        caso(i, "P", rec_p(i))
        if censo:
            caso(i, "Kgemelo", rec_k(i, "Kgemelo"))
            caso(i, "Kx12", rec_kx12(i))
            caso(i, "Pdef", rec_paq(i, "Pdef"))
            caso(i, "O", rec_paq(i, "O"))
            caso(i, "Psinfiltro", rec_sinfiltro(i))
            if isinstance((res[i].get("brazos") or {}).get("Kgeo"), dict) and "record" in res[i]["brazos"]["Kgeo"]:
                caso(i, "Kgeo", rec_k(i, "Kgeo"))
    PUB = {k: bool(p[4]) for k, p in zip(idx, B.correr_node(casos))} if casos else {}

    def pub(i, b):
        return PUB.get((i, b), False)

    def vrp(i, b):
        if b in ("K", "Kgemelo", "Kgeo") or (b == "P" and not censo):
            rec = res[i]["brazos"][b]["record"] or {}
            return (rec.get("primary_cluster") or {}).get("vrp_mw") or 0.0
        if b == "Kx12":
            return GANANCIA_PLACEBO * vrp(i, "K")
        return res[i]["paquete"]["P" if b == "Psinfiltro" else b].get("vrp_mw") or 0.0

    # ---------------------------------------------------------------- controles (§7)
    # nulo del contador (copia de analizar_v750b): perturbar records publicados de P y publicar un negativo
    nulo, nidx = [], []
    for i in oks0:
        if pub(i, "P"):
            base = rec_p(i)
            a0 = copy.deepcopy(base)
            if a0.get("primary_cluster"):
                a0["primary_cluster"]["vrp_mw"] = 0.0
            a0["vrp_mw"] = 0.0
            b0 = copy.deepcopy(base)
            b0["distance_class"] = "far"
            for rr in (a0, b0):
                nulo.append([rr, inner[obj[i]["volcan"]]])
                nidx.append(False)
    rng = random.Random(162)
    neg_no = [i for i in oks0 if obj[i]["lab"] == "neg_limpio" and not pub(i, "P")]
    for i in rng.sample(neg_no, min(50, len(neg_no))):
        rr = {"sensor": obj[i]["sensor"], "vrp_mw": 0.3, "t_max_k": 290.0, "triggered_test1": False,
              "distance_class": "summit", "primary_cluster": {"vrp_mw": 0.3, "n_pixels": 1, "centroid_dist_km": 0.5}}
        nulo.append([rr, inner[obj[i]["volcan"]]])
        nidx.append(True)
    NP = [bool(p[4]) for p in B.correr_node(nulo)] if nulo else []
    c_nulo = sum(1 for esperado, p in zip(nidx, NP) if p != esperado)
    nulo_ok = bool(nidx) and c_nulo == 0
    pr(f"== control nulo del contador: {len(nidx)} perturbaciones; las que no dan lo esperado: {c_nulo} "
       f"(tiene que ser 0, con al menos una perturbación): {'OK' if nulo_ok else 'FALLA'}")
    # K = producción (copia de analizar_v750b)
    k_dist = sorted({i for i in oks0 if bool(obj[i].get("pub_prod")) != pub(i, "K")}
                    | {i for i in oks0 if abs((vrp(i, "K") or 0) - (obj[i].get("pc_vrp") or 0)) > 0.001})
    k_dist_prot = [nombre(i) for i in k_dist if obj[i].get("protegida")]
    k_ok = not k_dist                      # §7: «en todas las pasadas ok» (L18; V750-B toleraba 1 %)
    pr(f"== control K = producción: distintas {len(k_dist)} de {len(oks0)} (protegidas {k_dist_prot or 'ninguna'}): "
       f"{'OK' if k_ok else 'FALLA'}; lista {[nombre(i) for i in k_dist]}")
    oks = list(oks0)                       # con K distinto la compuerta ya está cerrada

    def p2(b, ref, v, canal):
        """Copia de analizar_v750b.p2: e = 1 si la pasada es un error bajo 1 MW; c = e(b) - e(ref) por bloque
        (noche UTC, volcán); prueba de signos de D-45."""
        sumas = collections.defaultdict(int)
        for i in oks:
            o = obj[i]
            e = etiqueta(o, canal)
            if e not in ("baja", "neg") or not en_ventana(o, v):
                continue
            err = lambda x: int((e == "baja" and not pub(i, x)) or (e == "neg" and pub(i, x)))  # noqa: E731
            c = err(b) - err(ref)
            if c:
                sumas[(o["hora_utc"][:10], o["volcan"])] += c
        s = [sumas[k] for k in sorted(sumas)]
        neto = sum(s)
        prr = EV.prueba_signos_p2(s, neto)
        return EV.regla_signos_p2(neto, len(s), prr), neto, len(s), prr

    def m_pares(b, v, canal):
        """M (§5): alertas que deciden publicadas por K y por el brazo, con VRP de los dos y de MIROVA (LECTURA L4)."""
        out = []
        for i in oks:
            o = obj[i]
            if etiqueta(o, canal) not in ("prot", "baja") or not en_ventana(o, v):
                continue
            if not (pub(i, "K") and pub(i, b)):
                continue
            k, d, m = vrp(i, "K"), vrp(i, b), o.get("mirova_vrp") or 0.0
            if k > 0 and d > 0 and m > 0:
                out.append({"k": k, "d": d, "m": m, "clave": f"{o['volcan']}|{o['hora_utc']}",
                            "bloque": f"{o['hora_utc'][:10]}|{o['volcan']}"})
        return out

    def decidir_m(P_, comparador=True):
        """decidir_estrato de evaluar_d25.py con el mismo piso de sustrato que su evaluar_m."""
        if len(P_) < EM.N_MIN_PARES or len({p["bloque"] for p in P_}) < EM.N_MIN_NOCHES:
            return "SIN SUSTRATO", {"n": len(P_)}
        return EM.decidir_estrato(P_, "decide", "simetrica", True, comparador=comparador)

    ctrl = {"nulo del contador": nulo_ok, "K = producción": k_ok}
    if censo:
        # placebo, publicación: el predicado no mira la magnitud salvo VRP > 0
        pl_dist = [nombre(i) for i in oks if pub(i, "Kx12") != pub(i, "K")]
        ctrl["placebo (publicación)"] = not pl_dist
        pr(f"== control placebo K×1,2 (publicación): distintas de K {len(pl_dist)} de {len(oks)} "
           f"{pl_dist[:10]}: {'OK' if not pl_dist else 'FALLA'}"
           + ("" if not pl_dist else " (el predicado del tablero sí mira la magnitud en sus filtros de artefacto: "
                                     "isCirrusArtifact e isDiffuseFieldArtifact; ver L7)"))
        # placebo, M con el comparador: d′ es 0 para una ganancia pareja, así que M no lo puede dar por mejor
        pl_m = {}
        for v in VENTANAS:
            for canal in CANALES:
                pl_m[f"{v}/{canal}"] = decidir_m([dict(p, d=p["k"] * GANANCIA_PLACEBO)
                                                  for p in m_pares("P", v, canal)])[0]
        ctrl["placebo (M con comparador)"] = all(r != "MEJORA" for r in pl_m.values())
        pr(f"== control placebo K×1,2 (M con comparador, tiene que no dar MEJORA): {pl_m}: "
           f"{'OK' if ctrl['placebo (M con comparador)'] else 'FALLA'}")
        # nulo: K contra su gemelo
        g_reg, g_neto, g_nb, _ = p2("Kgemelo", "K", "TODO", "decide")
        g_m = decidir_m(m_pares("Kgemelo", "TODO", "decide"))[0]
        ctrl["nulo K contra K gemelo"] = g_reg in ("EMPATE", "SIN SUSTRATO") and g_m in ("NEUTRO", "SIN SUSTRATO")
        pr(f"== control nulo K contra K gemelo: P2 {g_reg} (neto {g_neto}, bloques {g_nb}), M {g_m} (tiene que ser "
           f"P2 EMPATE o SIN SUSTRATO y M sin separación): {'OK' if ctrl['nulo K contra K gemelo'] else 'FALLA'}")
        # control positivo de la ROI: P-def pierde una protegida de Cordón Caulle que P publica (LECTURA L6)
        roi = [nombre(i) for i in oks if obj[i]["volcan"] == VOL_ROI and etiqueta(obj[i], "decide") == "prot"
               and pub(i, "P") and not pub(i, "Pdef")]
        ctrl["positivo de la ROI"] = len(roi) >= 1
        pr(f"== control positivo de la ROI: protegidas de Cordón Caulle que P publica y P-def pierde {len(roi)} {roi[:10]} "
           f"(1 o más): {'OK' if roi else 'FALLA'}")
    else:
        pr("== fase sombra: los controles que necesitan P-def, O, el gemelo o el placebo no aplican (LECTURA L9)")
    aviso, rc_final = "", 0
    if not cob_ok and a.leer_con_faltantes:
        aviso, rc_final = f"[LEÍDO CON FALTANTES: {a.leer_con_faltantes}]", 5
    todo_ok = all(ctrl.values()) and (cob_ok or bool(a.leer_con_faltantes))
    pr("== compuerta del veredicto (controles de §7 y cobertura):", "ABIERTA" if todo_ok else "CERRADA",
       {k: v for k, v in ctrl.items() if not v} or "", aviso)
    if a.solo_controles or not todo_ok:
        pr("== sin veredicto:", "--solo-controles" if a.solo_controles else "controles caídos o SIN DATO")
        return salir(0 if (a.solo_controles and todo_ok) else 3)

    # ---------------------------------------------------------------- §6.1 equivalencia (censo)
    if censo:
        dist, banda = [], []
        for i in oks0:
            p, o_ = res[i]["paquete"]["P"], res[i]["paquete"]["O"]
            mp = sorted((x[0], x[1]) for x in p.get("pixeles") or [])
            mo = sorted((x[0], x[1]) for x in o_.get("pixeles") or [])
            if mp != mo or abs((p.get("vrp_mw") or 0.0) - (o_.get("vrp_mw") or 0.0)) > TOL_VRP_EQUIV:
                (banda if res[i].get("banda_triangulacion") else dist).append(i)

        def etq_eq(i):
            dP, dO = res[i]["paquete"]["P"].get("diag"), res[i]["paquete"]["O"].get("diag")
            if not (diag_valido(dP) and diag_valido(dO)):
                return nombre(i) + " (S-1 SIN DATO)"
            return nombre(i) + (" (decidida por la escena, no por el cráter: bloquea igual)"
                                if decidida_por_escena(dP, dO) else "")
        local_ok, local_txt = leer_equivalencia_local(a.equivalencia_local)
        pr("   P distinto de O dentro de la banda de triangulación (se listan aparte):", [nombre(i) for i in banda]
           or "ninguna")
        if dist or not local_ok:
            pr(f"== §6.1 equivalencia: NO SE CUMPLE (runner: {len(dist)} pasadas distintas fuera de la banda "
               f"{[etq_eq(i) for i in dist][:20]}; local: {local_txt}): se arregla la vía y se repite §4.1; "
               "el censo no se mira")
            return salir(6)
        pr(f"== §6.1 equivalencia: CUMPLE (runner: 0 pasadas distintas fuera de la banda de {len(oks0)}; {local_txt})")

    # ---------------------------------------------------------------- S-1, diagnóstico de la sigma de escena
    s1_prot, s1_sin_diag_prot, s1_filas = set(), set(), []
    if censo:
        for A, Bb in PARES_S1:
            con, sd_ = [], []
            for i in oks0:
                dA, dB = res[i]["paquete"][A].get("diag"), res[i]["paquete"][Bb].get("diag")
                if diag_valido(dA) and diag_valido(dB):
                    con.append(i)
                    sd_.append(delta_sd(dA, dB))
            for i in con:
                dA, dB = res[i]["paquete"][A]["diag"], res[i]["paquete"][Bb]["diag"]
                s1_filas.append({"par": f"{A}|{Bb}", "pasada": nombre(i), "id": i, "volcan": obj[i]["volcan"],
                                 "cenit": AB.tramo_z(obj[i].get("z")), "protegida": etiqueta(obj[i], "decide") == "prot",
                                 "delta_sd": delta_sd(dA, dB), "margen_A_nti_eti": list(margenes(dA)),
                                 "margen_B_nti_eti": list(margenes(dB)), "publica": [pub(i, A), pub(i, Bb)],
                                 "decidida_por_escena": decidida_por_escena(dA, dB)})
            cambia = [i for i in oks0 if pub(i, A) != pub(i, Bb)]
            esc = [i for i in cambia if i in set(con) and decidida_por_escena(res[i]["paquete"][A]["diag"],
                                                                             res[i]["paquete"][Bb]["diag"])]
            for i in cambia:
                if etiqueta(obj[i], "decide") == "prot":
                    if i in esc:
                        s1_prot.add(nombre(i))
                    elif i not in set(con):
                        s1_sin_diag_prot.add(nombre(i))
            partes = []
            for k in ("nti1", "eti1", "nti2", "eti2"):
                vals = [x[k] for x in sd_]
                partes.append(f"Δsd {k} mediana {statistics.median(vals):.4f} máx {max(abs(v) for v in vals):.4f}"
                              if vals else f"Δsd {k} SIN DATO")

            def entrada(i):
                mA = margenes(res[i]["paquete"][A]["diag"])
                mB = margenes(res[i]["paquete"][Bb]["diag"])
                return f"{nombre(i)} ({A} c/u {mA[0]:.2f}/{mA[1]:.2f}, {Bb} c/u {mB[0]:.2f}/{mB[1]:.2f})"
            pr(f"== S-1 par ({A}, {Bb}): pasadas con diagnóstico {len(con)} (SIN DATO {len(oks0) - len(con)}) | "
               + " | ".join(partes) + f" | publicación distinta {len(cambia)} | decididas por la escena {len(esc)}: "
               + str([entrada(i) for i in esc]))
            pr(f"   S-1 ({A}, {Bb}) decididas por la escena, por volcán "
               f"{dict(collections.Counter(obj[i]['volcan'] for i in esc))} y por cenit "
               f"{dict(collections.Counter(AB.tramo_z(obj[i].get('z')) for i in esc))}")

        f_s1 = Path(a.salida).with_name(Path(a.salida).stem + "_s1_por_pasada.json")
        f_s1.write_text(json.dumps(s1_filas, ensure_ascii=False, indent=1), encoding="utf-8")
        pr(f"== S-1 por pasada (a), (b) y (c) de §5: {len(s1_filas)} filas en {f_s1}")

    # ---------------------------------------------------------------- métricas por ventana y canal
    def metricas(b, v, canal):
        """P1 (§6.2): protegidas que K publica y el brazo no; P1_nadie: las que ni K ni el brazo publican (se
        listan). P1b y E como analizar_v750b."""
        m = collections.Counter()
        nadie = []
        for i in oks:
            o = obj[i]
            e = etiqueta(o, canal)
            if e is None or not en_ventana(o, v):
                continue
            pb, vb = pub(i, b), vrp(i, b)
            m[f"n_{e}"] += 1
            if e == "prot" and not pb and pub(i, "K"):
                m["P1"] += 1
            if e == "prot" and not pb and not pub(i, "K"):
                nadie.append(nombre(i))
            if e == "prot" and pb and vb < 1.0:
                m["P1b_abajo"] += 1
            if e in ("baja", "neg") and pb and vb >= 1.0:
                m["P1b_arriba"] += 1
            if e == "baja" and not pb:
                m["E_baja"] += 1
            if e == "neg" and pb:
                m["E_neg"] += 1
        m["E"] = m["E_baja"] + m["E_neg"]
        return m, nadie

    def razon_prot(b, v, canal, exigir_k=True):
        """§6.2 sobre el conjunto de §5 (L4): protegidas que publican K y el brazo, con VRP de los dos y de MIROVA.
        exigir_k=False sólo informa (las protegidas que publica el brazo, aunque K no)."""
        rz = sorted(vrp(i, b) / obj[i]["mirova_vrp"] for i in oks
                    if etiqueta(obj[i], canal) == "prot" and en_ventana(obj[i], v) and pub(i, b)
                    and (pub(i, "K") and vrp(i, "K") > 0 or not exigir_k)
                    and obj[i].get("mirova_vrp") and vrp(i, b) > 0)
        return (statistics.median(rz) if rz else None), len(rz)

    if censo:
        fallas, nadie_tot = [], set()
        for v in VENTANAS:
            for canal in CANALES:
                m, nadie = metricas("P", v, canal)
                nadie_tot.update(nadie)
                reg, neto, nb, prr = p2("P", "K", v, canal)
                rz, nrz = razon_prot("P", v, canal)
                Pm = m_pares("P", v, canal)
                rm, det = decidir_m(Pm)
                motivos = []
                if m["P1"]:
                    motivos.append(f"P1 {m['P1']}")
                if reg not in ("GANA", "EMPATE"):
                    motivos.append(f"P2 {reg}")
                if rz is None or not (BANDA_RAZON[0] <= rz <= BANDA_RAZON[1]):
                    motivos.append(f"M razón {'sin protegidas' if rz is None else f'{rz:.3f}'}")
                if rm != "MEJORA":
                    motivos.append(f"M comparador {rm}")
                fallas += [(v, canal, x) for x in motivos]
                rz_txt = "-" if rz is None else f"{rz:.3f}"
                pr(f"== §6.2 ventana {v}, canal {canal}: P1 {m['P1']} (de {m['n_prot']} protegidas) | P1b abajo "
                   f"{m['P1b_abajo']} arriba {m['P1b_arriba']} | P2 contra K {reg} (neto {neto}, bloques {nb}, p gana "
                   f"{prr['gana']}, pierde {prr['pierde']}) | M razón en protegidas {rz_txt} (n {nrz}) | M comparador "
                   f"{rm} (pares {len(Pm)}, ĝ {det.get('g_hat_factor', '-')}, d′ {det.get('regla_dprima', '-')}, "
                   f"nota «{det.get('nota', '')}») -> {'cumple' if not motivos else 'no cumple: ' + '; '.join(motivos)}")
                rz2, n2 = razon_prot("P", v, canal, exigir_k=False)
                pr(f"   razón en protegidas que publica P aunque K no (informa, no decide): "
                   f"{'-' if rz2 is None else f'{rz2:.3f}'} (n {n2})")
                pl = decidir_m([dict(p, d=p["k"] * GANANCIA_PLACEBO) for p in Pm], comparador=False)[0]
                pr(f"   placebo K×1,2 SIN comparador (informa, como evaluar_d25.py): {pl}")
        pr("   protegidas que ni K ni P publican (se listan, no vetan):", sorted(nadie_tot) or "ninguna")
        if not fallas:
            ver = ("== §6 censo: CUMPLE §6.1, §6.2 y §6.4 en T y O, con la tabla sola y con tabla más OCR; falta la "
                   "sombra (§6.3) para proponer P a Nicolás (A45)")
        elif all(v == "O" and x.startswith("P2") for v, _c, x in fallas):
            ver = ("== §6 censo: INFORMAR POR CANAL ANTES DE DECIDIR (falla sólo P2 en la ventana O: "
                   + "; ".join(f"{v}/{c}: {x}" for v, c, x in fallas) + ")")
        else:
            ver = "== §6 censo: NO CUMPLE (" + "; ".join(f"{v}/{c}: {x}" for v, c, x in fallas) + ")"
        pr(ver + (" " + aviso if aviso else ""))
        pr("   S-1 al lado del veredicto: protegidas decididas por la escena, no por el cráter:",
           sorted(s1_prot) or "ninguna", "| protegidas con publicación distinta y S-1 SIN DATO:",
           sorted(s1_sin_diag_prot) or "ninguna")
    else:
        motivos, regs, sin_sus, n_prot = [], {}, True, 0
        for canal in CANALES:
            m, nadie = metricas("P", "TODO", canal)
            reg, neto, nb, _ = p2("P", "K", "TODO", canal)
            regs[canal] = reg
            n_prot += m["n_prot"]
            sin_sus = sin_sus and reg == "SIN SUSTRATO"
            if m["P1"]:
                motivos.append(f"{canal}: P1 {m['P1']}")
            if reg == "PIERDE":
                motivos.append(f"{canal}: P2 PIERDE (neto {neto}, bloques {nb})")
            pr(f"== §6.3 canal {canal}: P1 {m['P1']} (de {m['n_prot']}) | P2 contra K {reg} (neto {neto}, bloques {nb}) "
               f"| protegidas que ni K ni P publican {nadie or 'ninguna'}")
        if motivos:
            pr("== §6.3 sombra: NO CUMPLE (" + "; ".join(motivos) + ")" + (" " + aviso if aviso else ""))
        else:
            pr(f"== §6.3 sombra: CUMPLE (P1 = 0; P2 tabla {regs['tabla']}, todo {regs['todo']}"
               + ("; con 4 bloques o menos la sombra sólo veta" if sin_sus else "")
               + ("; SIN PROTEGIDAS: P1 no pudo vetar" if not n_prot else "") + ")" + (" " + aviso if aviso else ""))

    # ---------------------------------------------------------------- informativo
    brazos_inf = ("K", "P") + (("Pdef", "Psinfiltro", "Kgeo") if censo else ())
    pr("\n== brazos, ventana T y O juntas, canal que decide (informa)")
    for b in brazos_inf:
        if not any((i, b) in PUB for i in oks):
            pr(f"   {b}: sin datos")
            continue
        m, _ = metricas(b, "TODO", "decide")
        lin = (f"   {b:10s} prot {m['n_prot']} P1 {m['P1']} | E {m['E']} (bajas sin publicar {m['E_baja']} de "
               f"{m['n_baja']}, neg publicados {m['E_neg']} de {m['n_neg']})")
        if b != "K":
            reg, neto, nb, _ = p2(b, "K", "TODO", "decide")
            lin += f" | P2 contra K {reg} (neto {neto}, bloques {nb})"
        pr(lin)
    if censo:
        reg, neto, nb, _ = p2("Psinfiltro", "P", "TODO", "decide")
        pr(f"== P-sinfiltro contra P (§9.5 del programa, informa; predicción §8: empata o pierde): P2 {reg} "
           f"(neto {neto}, bloques {nb})")
    pr("\n== razón brazo/MIROVA en alertas que deciden publicadas (mediana [q1, q3] n)")
    for b in brazos_inf:
        rz = sorted(vrp(i, b) / obj[i]["mirova_vrp"] for i in oks if etiqueta(obj[i], "decide") in ("prot", "baja")
                    and pub(i, b) and obj[i].get("mirova_vrp") and vrp(i, b) > 0)
        n = len(rz)
        pr(f"   {b}: " + (f"{statistics.median(rz):.3f} [{rz[n // 4]:.3f}, {rz[(3 * n) // 4]:.3f}] n={n}" if n else "-"))
    pr("== curva por cenit: VRP más oblicua sobre menos oblicua de la misma noche y volcán (mediana, n; MIROVA al lado)")
    for b in brazos_inf:
        por = collections.defaultdict(list)
        for i in oks:
            o = obj[i]
            if (etiqueta(o, "decide") in ("prot", "baja") and pub(i, b) and vrp(i, b) > 0 and o.get("mirova_vrp")
                    and o.get("z") is not None):
                por[(o["hora_utc"][:10], o["volcan"])].append(i)
        rb, rm_ = [], []
        for ids in por.values():
            hi, lo = max(ids, key=lambda i: obj[i]["z"]), min(ids, key=lambda i: obj[i]["z"])
            if obj[hi]["z"] > obj[lo]["z"]:
                rb.append(vrp(hi, b) / vrp(lo, b))
                rm_.append(obj[hi]["mirova_vrp"] / obj[lo]["mirova_vrp"])
        pr(f"   {b}: " + (f"brazo {statistics.median(rb):.3f} | MIROVA {statistics.median(rm_):.3f} | n {len(rb)}"
                          if rb else "-"))
    pr("== por volcán y por tramo de 10° de cenit, canal que decide: protegidas publicadas, bajas publicadas, "
       "negativos publicados")
    for clave, f in (("volcán", lambda o: o["volcan"]), ("cenit", lambda o: AB.tramo_z(o.get("z")))):
        for b in brazos_inf:
            t = collections.Counter()
            for i in oks:
                e = etiqueta(obj[i], "decide")
                if e and (i, b) in PUB:
                    g = f(obj[i])
                    t[(g, e)] += 1
                    t[(g, e + "_pub")] += pub(i, b)
            grupos = sorted({g for g, _ in t})
            pr(f"   {clave} {b}: " + " | ".join(
                f"{g} prot {t[(g, 'prot_pub')]}/{t[(g, 'prot')]} baja {t[(g, 'baja_pub')]}/{t[(g, 'baja')]} "
                f"neg {t[(g, 'neg_pub')]}/{t[(g, 'neg')]}" for g in grupos))
    if aviso:
        pr(f"== {aviso}: el veredicto de arriba lleva esta marca")
    return salir(rc_final)


if __name__ == "__main__":
    sys.exit(main())
