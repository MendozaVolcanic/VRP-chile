# -*- coding: utf-8 -*-
"""F1a, fila R7 (plan §11.2b): barajar las ETIQUETAS de MIROVA dentro de cada estrato (volcan, sensor), 1.000 veces,
semilla 160 (sellada en INFORME.md antes de correr), y contar en que fraccion de barajados el criterio de K dice
CUMPLE. Intervalo de Wilson al 95 %. FALLA si el intervalo queda entero sobre 5 %; SIN PODER CONCLUYENTE si lo cruza;
OK si queda entero bajo 5 %.

Que se baraja: por pasada, el paquete de atributos que vienen de la REFERENCIA (etiqueta `lab`, `vrp_ref`, protegida
A y B, `alerta_solo_ocr`, `rutina_pasada`, `noche_con_alerta_sensor`). Las publicaciones (`pub`), magnitudes (`disp`)
y posiciones de C0, F, K y G quedan fijas. Asi un barajado es "la misma salida de los brazos contra una MIROVA que
no sabe nada de esas noches".

Como se calcula el veredicto: se reimplementan aqui las secciones 5 (P1) y 6 (P2) de evaluar_fk.py sobre las tablas
`t_*.json` que el propio evaluador dejo en su --tmp, reutilizando sus funciones `suma_errores`, `errores_por_pasada`
y `global_ventana`. P3 (magnitud) y P4 (movimiento) NO se recalculan: solo agregan un sufijo al CUMPLE ("EN
DETECCION, FALLA EN MAGNITUD" / "auditoria espacial pendiente") y en esta cuenta ambos se tratan como "cumple"
(lo que hace la cuenta MAS propensa a FALLA, nunca menos). Controles: (a) sin barajar, el veredicto reimplementado
tiene que coincidir con el de v1_rep.json y v2_rep.json; (b) un barajado "adverso" construido a mano (todas las
protegidas puestas en pasadas que K no publica y C0 si) tiene que dar NO CUMPLE (veto).
Uso: python barajar_r7.py <tmp_v1> <tmp_v2> <v1_rep.json> <v2_rep.json> <salida.json>
"""
import collections, json, math, random, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ / "experiments" / "_s151_prereg_fk_11"))
import evaluar_fk as E  # noqa: E402

SEMILLA, N = 160, 1000
ATRIB = ("lab", "vrp_ref", "alerta_solo_ocr", "rutina_pasada", "noche_con_alerta_sensor")


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def cargar(tmp, ventana):
    cfg = dict(E.VENTANAS[ventana])
    pares = [("C0", n) for n in cfg["brazos"] if n != "C0"] + ([("F", "K")] if {"F", "K"} <= set(cfg["brazos"]) else [])
    T = {p: json.load(open(Path(tmp) / ("t_%s_%s.json" % p), encoding="utf-8"))["pasadas"] for p in pares}
    todas = set().union(*[set(t) for t in T.values()])
    ref = E.archivos_ref(cfg, Path(tmp))
    prot = E.proteccion(todas, ref, cfg["desde"], cfg["hasta"])
    return cfg, pares, T, prot


def p1(T, prot, cfg, X, lectura, s, ruido_c0, ruido_cand, con_gemelo):
    """Seccion 5 de evaluar_fk.py, tal cual (sin --repeticion)."""
    par = ("C0", X); netas = ruidosas = pendientes = 0; n_pub = 0
    for k, v in T[par].items():
        if len(v) != 2 or k.split("|")[1] != s or not prot[k][lectura] or not E.decide_sensor(k, cfg):
            continue
        c, b = v["control"], v["brazo"]
        if not c["pub"]:
            continue
        n_pub += 1
        if b["pub"]:
            continue
        if lectura == "A" and not cfg["solo_tabla"] and E.ocr_snpp(k, c, prot):
            continue
        if k in ruido_c0 or (s != "MODIS" and k in ruido_cand):
            ruidosas += 1
        elif not con_gemelo:
            pendientes += 1
        else:
            netas += 1
    if netas: return "VETADO"
    if ruidosas: return "INDECIDIBLE"
    if pendientes: return "PENDIENTE DE REPETICION"
    if n_pub == 0: return "SIN SUSTRATO"
    return "CUMPLE"


def veredicto(T, prot, cfg, pares, ruido_frac):
    brazos = cfg["brazos"]; con_gemelo = "G" in brazos
    ruido_c0, ruido_cand = set(), set()
    if con_gemelo:
        for k, v in T[("C0", "G")].items():
            if len(v) == 2 and v["control"]["pub"] != v["brazo"]["pub"]: ruido_c0.add(k)
        for k, v in T[("F", "K")].items():
            if len(v) == 2 and v["control"]["pub"] != v["brazo"]["pub"]: ruido_cand.add(k)
    res = {"controles_ok": True, "cableado": {n: True for n in brazos}, "veredicto": {}}
    excluir = not cfg["solo_tabla"]
    for X in ("F", "K"):
        if X not in brazos: continue
        for lectura in ("A", "B"):
            for s in E.SENS_CANDIDATO[X]:
                res["veredicto"]["P1|%s|%s|%s" % (X, s, lectura)] = p1(T, prot, cfg, X, lectura, s, ruido_c0, ruido_cand, con_gemelo)
    for lectura in ("A", "B"):
        for s in E.SENS:
            sumas = {}
            for n in brazos:
                par = ("C0", n) if n != "C0" else pares[0]; lado = "brazo" if n != "C0" else "control"
                sumas[n] = sum(E.suma_errores(T[par], lado, prot, lectura, cfg, s, excluir)[:2])
            s0 = sumas["C0"]
            if con_gemelo:
                Tg = T[("C0", "G")]
                ruido = len(E.errores_por_pasada(Tg, "control", prot, lectura, cfg, s, excluir) ^ E.errores_por_pasada(Tg, "brazo", prot, lectura, cfg, s, excluir))
            else:
                ruido = ruido_frac.get("%s|%s" % (s, lectura), 0.0) * s0
            for X in ("F", "K"):
                if X not in brazos or s not in E.SENS_CANDIDATO[X]: continue
                sx = sumas[X]
                res["veredicto"]["P2|%s|%s|%s" % (X, s, lectura)] = "GANA" if sx < s0 - ruido else ("PIERDE" if sx > s0 + ruido else "EMPATE")
    for X in ("F", "K"):
        if X in brazos:
            for s in E.SENS_CANDIDATO[X]:
                res["veredicto"]["P3|%s|%s" % (X, s)] = "CUMPLE"   # no recalculado (ver docstring)
    out = {}
    for X in ("F", "K"):
        if X in brazos:
            out[X] = {l: E.global_ventana(res, X, l) for l in ("A", "B")}
    if "F" not in brazos and "K" in brazos:
        out["F"] = {l: E.global_ventana(res, "F", l, fuente="K") for l in ("A", "B")}
    return out, res["veredicto"]


def barajar(T, prot, rnd):
    """Permuta, dentro de cada (volcan, sensor), el paquete de atributos de referencia entre las pasadas."""
    claves = sorted(set().union(*[set(t) for t in T.values()]))
    estratos = collections.defaultdict(list)
    for k in claves:
        estratos[(k.split("|")[0], k.split("|")[1])].append(k)
    T2 = {p: {} for p in T}; prot2 = {}
    for est, ks in estratos.items():
        perm = ks[:]; rnd.shuffle(perm)
        for k, k2 in zip(ks, perm):
            prot2[k] = prot[k2]
            for p in T:
                if k not in T[p]: continue
                origen = next((T[q][k2][lado] for q in T for lado in ("control", "brazo") if k2 in T[q] and lado in T[q][k2]), None)
                nuevo = {}
                for lado, x in T[p][k].items():
                    y = dict(x)
                    for a in ATRIB:
                        y[a] = origen.get(a) if origen else x.get(a)
                    nuevo[lado] = y
                T2[p][k] = nuevo
    return T2, prot2


def adverso(T, prot, cfg):
    """Control (b): las protegidas A se mueven a pasadas VIIRS375 que C0 publica y K no."""
    T2 = {p: {k: {l: dict(x) for l, x in v.items()} for k, v in t.items()} for p, t in T.items()}
    prot2 = {k: dict(v) for k, v in prot.items()}
    ck = T[("C0", "K")]
    objetivo = [k for k, v in ck.items() if len(v) == 2 and v["control"]["pub"] and not v["brazo"]["pub"] and "|VIIRS375|" in k and E.decide_sensor(k, cfg)]
    donantes = [k for k in ck if prot[k]["A"] and "|VIIRS375|" in k and not E.ocr_snpp(k, ck[k].get("control", {}), prot)]
    for k_dest, k_src in zip(objetivo, donantes):
        prot2[k_dest], prot2[k_src] = prot[k_src], prot[k_dest]
        for p in T2:
            for lado in T2[p].get(k_dest, {}):
                for a in ATRIB:
                    T2[p][k_dest][lado][a] = T[p].get(k_src, {}).get(lado, {}).get(a, T[p][k_dest][lado].get(a))
    return T2, prot2, len(list(zip(objetivo, donantes)))


def main():
    tmp1, tmp2, v1json, v2json, salida = sys.argv[1:6]
    rnd = random.Random(SEMILLA)
    v1 = json.load(open(v1json, encoding="utf-8")); v2 = json.load(open(v2json, encoding="utf-8"))
    out = {"semilla": SEMILLA, "n": N}
    datos = {}
    for ventana, tmp, ref in (("V1", tmp1, v1), ("V2", tmp2, v2)):
        cfg, pares, T, prot = cargar(tmp, ventana)
        ruido_frac = v1["ruido_frac"] if ventana == "V2" else {}
        g, det = veredicto(T, prot, cfg, pares, ruido_frac)
        esperado = {X: {l: ref["global"][X][l].split(" | ")[0].replace(" [derivado de K: mismo codigo en VIIRS]", "") for l in ("A", "B")} for X in ref["global"]}
        obtenido = {X: {l: g[X][l].split(" | ")[0] for l in ("A", "B")} for X in g}
        print("%s control (a) sin barajar: reimplementado %s | evaluador %s | %s" % (ventana, obtenido, esperado, "IGUAL" if obtenido == esperado else "DISTINTO"))
        T2, prot2, n_mov = adverso(T, prot, cfg)
        g2, _ = veredicto(T2, prot2, cfg, pares, ruido_frac)
        print("%s control (b) adverso (%d protegidas movidas a pasadas que K calla): K A = %s" % (ventana, n_mov, g2["K"]["A"]))
        out[ventana] = {"control_a_igual": obtenido == esperado, "control_b_adverso": g2["K"]["A"], "n_movidas": n_mov}
        datos[ventana] = (cfg, pares, T, prot, ruido_frac)
    cuenta = collections.Counter(); cumple = {"V1": 0, "V2": 0, "comb": 0}
    orden = ("NO CUMPLE", "INDECIDIBLE", "PENDIENTE DE REPETICION", "CUMPLE EN DETECCION", "CUMPLE")
    for i in range(N):
        estados = {}
        for ventana in ("V1", "V2"):
            cfg, pares, T, prot, ruido_frac = datos[ventana]
            T2, prot2 = barajar(T, prot, rnd)
            g, _ = veredicto(T2, prot2, cfg, pares, ruido_frac)
            estados[ventana] = g["K"]["A"]
            cuenta[(ventana, g["K"]["A"].split(" | ")[0])] += 1
            if g["K"]["A"].startswith("CUMPLE"): cumple[ventana] += 1
        peor = min(estados.values(), key=lambda e: next(j for j, o in enumerate(orden) if e.startswith(o)))
        if peor.startswith("CUMPLE"): cumple["comb"] += 1
        if (i + 1) % 100 == 0:
            print("  barajados %d: cumple V1 %d, V2 %d, combinado %d" % (i + 1, cumple["V1"], cumple["V2"], cumple["comb"])); sys.stdout.flush()
    for key, k in cumple.items():
        lo, hi = wilson(k, N)
        ver = "FALLA" if lo > 0.05 else ("OK" if hi < 0.05 else "SIN PODER CONCLUYENTE")
        print("R7 %-5s cumple en %d de %d barajados (%.3f) | Wilson 95 %% [%.4f, %.4f] -> %s" % (key, k, N, k / N, lo, hi, ver))
        out["R7_" + key] = {"cumple": k, "n": N, "wilson": [lo, hi], "fila": ver}
    out["distribucion"] = {"%s|%s" % k: v for k, v in sorted(cuenta.items())}
    print("distribucion de veredictos K A por ventana:", out["distribucion"])
    Path(salida).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
