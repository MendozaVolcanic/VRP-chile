# -*- coding: utf-8 -*-
"""S161, D-45 (experiments/_s157_prereg_d25/ADENDA_SIGNOS_P2.md §6): los placebos de D-44 con la regla nueva de P2
(prueba de signos por bloque), copia de experiments/_s159/instrumentos/placebos_d44/placebo_d44.py con dos cambios:

  1. (c) SORTEA POR NOCHE (V42-21): se eligen noches-volcán tocadas y todas las pasadas tocadas de una misma noche
     reciben el mismo signo, de modo que el nulo del placebo sea el de §2.3 (cada bloque entero cambia de signo con
     probabilidad 1/2, independiente de los demás). Para que eso valga exacto, el TAMAÑO de lo que se toca en una noche
     se fija ANTES de tirar la moneda y tiene que poder salir con los dos signos: por sensor, una noche es elegible si
     tiene pasadas de los dos lados (lado +1: alertas bajo 1 MW que K publica, a apagar, y negativos limpios que K no
     publica, a encender; lado -1: negativos limpios que K publica, a apagar, y alertas bajo 1 MW que K no publica, a
     encender); las noches elegibles se recorren en orden al azar; en cada una se tocan t = min(lado +1, lado -1,
     lo que falta para el objetivo) pasadas, todas del lado que salga en la moneda de esa noche. El objetivo de
     pasadas tocadas es el de D-44, n = round(2 p M) con M el tamaño del lado -1. Si se acaban las noches elegibles
     antes del objetivo, se registra en «faltaron». LECTURA (README de signos_p2): la adenda dice «(todas se apagan o
     todas se encienden)»; lo que fija el nulo es el SIGNO común, y una noche con signo +1 puede apagar una alerta y
     encender un negativo a la vez; se sigue el signo.
  2. Cada fila guarda el detalle de P2 de D-45 (B, neto, sumas de bloque, valores-p, método) y lo que informa (D-34,
     D-42), para que se pueda re-decidir sin volver a correr.
El número de semillas se fija antes de correr (§6, V42-22): 40 por punto en (c), sin ampliar; (a) y (b) con las mismas
20 semillas de D-44 (0 a 19). Sin parada opcional: no hay --desde-semilla.

Texto de D-44 (lo demás no cambia):
S160, D-44 (experiments/_s157_prereg_d25/NOTA_D44.md, punto 3): los placebos de P2 que SÍ pueden fallar, sobre brazos
armados desde PRODUCCIÓN (sustrato_k.unir_k: histórico con K antes del 2026-09-18, producción desde ahí), nunca desde
artefactos del A/B, con el evaluador entero y la regla de P2 calibrada tal como está hoy (D-34 + D-42).

POR QUÉ. El verificador de D-42, vuelta 2 (verificador_d42/vuelta2/INFORME.md, V42-10), mostró que apagar al azar
publicaciones de K no puede dar GANA: el 85,7 % de lo apagado eran alertas bajo 1 MW, así que el neto de P2 era
positivo por construcción y «GANA 0 de 20» no medía nada. Estos tres sí pueden fallar:
  (a) poder:     D = K con una fracción f de sus publicaciones en NEGATIVOS LIMPIOS apagada. D comete menos errores:
                 P2 calibrada tiene que dar GANA donde haya sustrato.
  (b) dirección: D = K con una fracción f de sus publicaciones en ALERTAS BAJO 1 MW apagada. D comete más errores:
                 tiene que dar PIERDE donde haya sustrato.
  (c) simétrico: en la misma semilla se apagan publicaciones de K y se encienden pasadas que K no publica, de modo que
                 cada pasada tocada aporte a P2 +1 o -1 con probabilidad 1/2 exacta. Las que aportan +1 (D comete un
                 error que K no) son las alertas bajo 1 MW que K publica, apagadas, y los negativos limpios que K no
                 publica, encendidos; las que aportan -1 son los negativos limpios que K publica, apagados, y las alertas
                 bajo 1 MW que K no publica, encendidas. Por sensor: n = round(2 p M) eventos, con M el tamaño del lado
                 -1 (el escaso con K); cada evento tira una moneda justa para su signo y toma, sin reposición, una pasada
                 al azar del lado que salió. Así el neto esperado es 0 por construcción y su distribución es simétrica.
                 Por qué no la receta literal («apagar el p % de las publicaciones y encender el p % de las no
                 publicadas en la proporción de la población»): con K casi no hay alertas bajo 1 MW sin publicar (3 en
                 VIIRS 375 de la ventana tipo V1), así que lo encendido no puede compensar lo apagado y el esperado no
                 es 0 (medido en la primera prueba de este script: se pidieron 18 encendidas en VIIRS 375 y sólo había
                 pozo para 7). Si la moneda pide más de un lado de lo que hay, se toma lo que hay y se registra
                 («faltaron»). Se mide: la media del neto de P2 sobre las semillas.

Clases (las mismas definiciones que errores_por_pasada de evaluar_fk.py): alerta bajo 1 MW = etiqueta «pos» y no
protegida en la lectura A; negativo limpio = etiqueta «neg_limpio». Para que el placebo tenga la misma dirección en las
dos reglas de etiquetas (original y SN, D-9), se toma sólo una pasada con la MISMA clase en las dos, con el mismo
cálculo de etiquetas que evaluar_d25.evaluar. Fuera de las clases: los días excluidos de la ventana (D-29) y, en V1, las
alertas que descansan sólo en el OCR de Suomi NPP (no cuentan en P2).

Apagar = pc.vrp_mw y f5_core_vrp_mw a 0,0 (el tablero no publica nada con 0 MW). Encender = cúmulo de cumbre con
0,3 MW dentro del radio interno (distance_class summit, primary_cluster con vrp_mw 0,3 y centroid_dist_km 0,5; si el
record no tenía cúmulo se le crea con el centroide en el cráter). Cada semilla cuenta cuántas apagadas y encendidas
llegaron a la tabla del evaluador (pregunta 1 del instrumento: si el placebo no tocara nada, se vería).

Uso: python placebo_d44.py <tmp> <ventana V1|V2> <placebo a|b|c> <fracciones separadas por coma> <n semillas> <salida.jsonl>
     [--entero]   por defecto corre evaluar_sin_m.py (el evaluador sin M, ver su docstring y comparar_sin_m.py);
                  con --entero, evaluar_d25.py tal cual.
"""
import collections
import copy
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
EVD = RAIZ / "experiments" / "_s157_prereg_d25"
sys.path.insert(0, str(EVD))
import evaluar_d25 as X  # noqa: E402
import sustrato_k as S  # noqa: E402

E = X.E
VOLS = ["Lascar", "Isluga", "NevadosDeChillan", "Lastarria", "Villarrica", "PuyehueCordonCaulle", "Tupungatito"]
VENT = {"V1": ("2026-09-18", "2026-10-18", ("K", "G", "D"), VOLS),
        "V2": ("2026-04-01", "2026-06-12", ("K", "D"), [v for v in VOLS if v != "NevadosDeChillan"])}
VRP_ENCENDIDO = 0.3
EVALUADOR = EVD / "evaluar_d25.py" if "--entero" in sys.argv else AQUI / "evaluar_sin_m.py"


def cargar(datos, vols, desde, hasta):
    out = {}
    for v in vols:
        p = Path(datos) / (v + ".json")
        recs = json.load(open(p, encoding="utf-8"))["records"] if p.exists() else []
        out[v] = [r for r in recs if desde <= r["datetime_utc"][:10] <= hasta and X.bp.bucket(r.get("sensor")) in X.SENS]
    return out


def con_huella(recs):
    out = copy.deepcopy(recs)
    for v in out.values():
        for r in v:
            if r.get("primary_cluster"):
                r["diag_bg_vecinos_n_sin_vecinos"] = 0
    return out


def apagar(r):
    pc = r.get("primary_cluster") or {}
    if pc.get("vrp_mw") is not None:
        pc["vrp_mw"] = 0.0
    if r.get("f5_core_vrp_mw") is not None:
        r["f5_core_vrp_mw"] = 0.0


def encender(r, vent):
    pc = r.get("primary_cluster")
    if not pc:
        pc = {"centroid_lat": vent[0], "centroid_lon": vent[1], "n_pixels": 1}
        r["primary_cluster"] = pc
    pc["vrp_mw"] = VRP_ENCENDIDO
    pc["centroid_dist_km"] = 0.5
    pc.pop("d9_capped", None)
    r["distance_class"] = "summit"
    r["discarded_reason"] = None
    if not r.get("vrp_mw"):
        r["vrp_mw"] = VRP_ENCENDIDO
    if r.get("f5_core_vrp_mw") is not None:
        r["f5_core_vrp_mw"] = VRP_ENCENDIDO


def noche(clave):
    """El bloque de P2: volcán y fecha UTC de la pasada (la clave de contribuciones_p2)."""
    return "%s|%s" % (clave.split("|")[0], clave.split("|")[2][:10])


def buscar(recs, clave):
    vol, b, t = clave.split("|")
    return [r for r in recs[vol] if r["datetime_utc"][:16] == t and X.bp.bucket(r.get("sensor")) == b]


def escribir(raiz, arms):
    if raiz.exists():
        shutil.rmtree(raiz)
    (raiz / "logs").mkdir(parents=True)
    for n, recs in arms.items():
        (raiz / X.BRAZOS[n]).mkdir()
        for v, rr in recs.items():
            json.dump({"records": rr}, open(raiz / X.BRAZOS[n] / (v + ".json"), "w", encoding="utf-8"))
            fl = dict(X.DECLARADO[n], PROFILE_NAME=X.BRAZOS[n], DATA_SUBDIR=X.BRAZOS[n])
            (raiz / "logs" / ("%s_%s.log" % (X.BRAZOS[n], v))).write_text("FLAGS_BRAZO " + json.dumps(fl) + "\n",
                                                                          encoding="utf-8")


def correr(tmp, ventana, desde, hasta, vols, raiz):
    out = tmp / "out.json"
    cmd = [sys.executable, str(EVALUADOR), "--ventana", ventana, "--raiz", str(raiz), "--logs",
           str(raiz / "logs"), "--out", str(out), "--tmp", str(tmp / "t"), "--vols", ",".join(vols), "--desde", desde,
           "--hasta", hasta]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0 or not out.exists():
        return None, p.stderr[-1500:]
    return json.load(open(out, encoding="utf-8")), json.load(open(tmp / "t" / "t_K_D.json", encoding="utf-8"))["pasadas"]


def clases(t0, ventana, desde, hasta, tmp):
    """Clase de cada pasada VIIRS de la tabla del nulo, con las dos reglas de etiquetas, como en evaluar_d25.evaluar."""
    cfg = dict(X.VENTANAS[ventana], desde=desde, hasta=hasta)
    ref = E.archivos_ref(cfg, tmp)
    excl = set(X.DIAS_EXCLUIDOS.get(ventana, ()))
    T = {k: v for k, v in t0.items() if k.split("|")[1] in X.SENS and k.split("|")[2][:10] not in excl and len(v) == 2}
    todas = set(T)
    prot = E.proteccion(todas, ref, desde, hasta)
    base = E.etiquetas_regla(sorted(todas), ref, desde, hasta, "original")
    sn = E.etiquetas_regla(sorted(todas), ref, desde, hasta, "SN", X.cm.UMBRAL_MINIMA_MW)
    tabla_lab = {k: v["control"]["lab"] for k, v in T.items()}
    excluir = not cfg["solo_tabla"]
    out = {}
    for k, v in T.items():
        c = v["control"]
        labs = []
        for labs_r in (base, sn):
            lab = labs_r[k] if labs_r[k] != base[k] else tabla_lab.get(k, base[k])
            if lab == "pos" and not prot[k]["A"] and not (excluir and E.ocr_snpp(k, c, prot)):
                labs.append("alerta")
            elif lab == "neg_limpio":
                labs.append("negativo")
            else:
                labs.append("otra")
        out[k] = {"pub": bool(c["pub"]), "clase": labs[0] if labs[0] == labs[1] else "distinta"}
    return out


def main():
    tmp, ventana, placebo = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
    fracs = [float(x) for x in sys.argv[4].split(",")]
    nsem, jl = int(sys.argv[5]), Path(sys.argv[6])
    desde, hasta, brazos, vols = VENT[ventana]
    tmp.mkdir(parents=True, exist_ok=True)
    datos, _ = S.unir_k(tmp / "k")
    K = cargar(datos, vols, desde, hasta)
    vents = {v: X.bp._coords_por_volcan()[v] for v in vols}
    arms = {"K": K, "G": copy.deepcopy(K), "D": con_huella(K)}
    escribir(tmp / "raiz", {n: arms[n] for n in brazos})
    res0, t0 = correr(tmp / "nulo", ventana, desde, hasta, vols, tmp / "raiz")
    if res0 is None:
        raise SystemExit("el evaluador cayó en el nulo: %s" % t0)
    cl = clases(t0, ventana, desde, hasta, tmp / "nulo" / "t")
    por = collections.defaultdict(list)
    for k, x in sorted(cl.items()):
        por[(k.split("|")[1], x["pub"], x["clase"])].append(k)
    comp = {}
    for s in X.SENS:
        pubs = sum(len(por[(s, True, c)]) for c in ("alerta", "negativo", "otra", "distinta"))
        comp[s] = {"publicadas_K": pubs, "pub_alerta": len(por[(s, True, "alerta")]),
                   "pub_negativo": len(por[(s, True, "negativo")]), "pub_otra": len(por[(s, True, "otra")]),
                   "pub_distinta": len(por[(s, True, "distinta")]),
                   "nopub_alerta": len(por[(s, False, "alerta")]), "nopub_negativo": len(por[(s, False, "negativo")]),
                   "frac_negativos_entre_publicadas": len(por[(s, True, "negativo")]) / pubs if pubs else None,
                   "frac_negativos_entre_alertas_y_negativos_publicados": (
                       len(por[(s, True, "negativo")]) / (len(por[(s, True, "negativo")]) + len(por[(s, True, "alerta")]))
                       if por[(s, True, "negativo")] or por[(s, True, "alerta")] else None)}
    print("ventana %s %s a %s | brazos %s | %d volcanes | placebo %s | evaluador %s | nulo: %s" % (
        ventana, desde, hasta, brazos, len(vols), placebo, EVALUADOR.name, res0["estado"]), flush=True)
    print("composición (tabla del nulo, sin días excluidos): %s" % json.dumps(comp, ensure_ascii=False), flush=True)
    with open(jl, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"composicion": comp, "ventana": ventana, "placebo": placebo}, ensure_ascii=False) + "\n")
    for f in fracs:
        for s_ in range(nsem):
            rng = random.Random(10000 * int(round(f * 1000)) + s_)
            apagadas, encendidas = [], []
            faltaron, pedidos = collections.Counter(), collections.Counter()
            noches_tocadas = []
            for s in X.SENS:
                if placebo in ("a", "b"):
                    pool = por[(s, True, "alerta" if placebo == "b" else "negativo")]
                    n = min(len(pool), max(1, round(f * len(pool)))) if pool else 0
                    apagadas += rng.sample(pool, n)
                else:
                    mas = por[(s, True, "alerta")] + por[(s, False, "negativo")]      # aportan +1
                    menos = por[(s, True, "negativo")] + por[(s, False, "alerta")]    # aportan -1
                    n = round(2 * f * len(menos))                                     # objetivo de pasadas, como D-44
                    lados = collections.defaultdict(lambda: {"+": [], "-": []})
                    for pool, signo in ((mas, "+"), (menos, "-")):
                        for k in pool:
                            lados[noche(k)][signo].append(k)
                    elegibles = sorted(nk for nk, d in lados.items() if d["+"] and d["-"])
                    rng.shuffle(elegibles)
                    tocadas = 0
                    for nk in elegibles:
                        t = min(len(lados[nk]["+"]), len(lados[nk]["-"]), n - tocadas)   # tamaño ANTES de la moneda
                        if t <= 0:
                            break
                        signo = "+" if rng.random() < 0.5 else "-"
                        tomar = rng.sample(sorted(lados[nk][signo]), t)
                        pedidos[signo] += t
                        noches_tocadas.append({"sensor": s, "noche": nk, "signo": signo, "t": t})
                        tocadas += t
                        for k in tomar:
                            (apagadas if cl[k]["pub"] else encendidas).append(k)
                    faltaron[s] += n - tocadas
            D = copy.deepcopy(K)
            for k in apagadas:
                for r in buscar(D, k):
                    apagar(r)
            for k in encendidas:
                for r in buscar(D, k):
                    encender(r, vents[k.split("|")[0]])
            arms = {"K": K, "G": copy.deepcopy(K), "D": con_huella(D)}
            escribir(tmp / "raiz", {n: arms[n] for n in brazos})
            res, t = correr(tmp / "s", ventana, desde, hasta, vols, tmp / "raiz")
            fila = {"ventana": ventana, "placebo": placebo, "fraccion": f, "semilla": s_,
                    "apagadas_pedidas": len(apagadas), "encendidas_pedidas": len(encendidas),
                    "apagadas_por_clase": dict(collections.Counter(cl[k]["clase"] for k in apagadas)),
                    "encendidas_por_clase": dict(collections.Counter(cl[k]["clase"] for k in encendidas)),
                    "simetrico_pedidos": dict(pedidos), "simetrico_faltaron": dict(faltaron),
                    "simetrico_noches": noches_tocadas}
            if res is None:
                fila["caido"] = t
            else:
                fila["apagadas_en_tabla"] = sum(1 for k in apagadas if len(t.get(k, {})) == 2
                                                and t[k]["control"]["pub"] and not t[k]["brazo"]["pub"])
                fila["encendidas_en_tabla"] = sum(1 for k in encendidas if len(t.get(k, {})) == 2
                                                  and not t[k]["control"]["pub"] and t[k]["brazo"]["pub"])
                fila["otras_diferencias_en_tabla"] = sum(
                    1 for k, v in t.items() if len(v) == 2 and v["control"]["pub"] != v["brazo"]["pub"]
                    and k not in set(apagadas) | set(encendidas))
                fila["estado"] = res["estado"]
                fila["controles_ok"] = res["controles_ok"] and all(res["cableado"].values())
                for regla in res["por_regla"]:
                    for sen in X.SENS:
                        i = res["por_regla"][regla]["info"]["P2|%s" % sen]
                        fila["P2|%s|%s" % (regla, sen)] = {
                            "veredicto": res["por_regla"][regla]["veredicto"]["P2|%s" % sen], "neto": i["neto"],
                            "n": i["n_discordantes"], "B": i["B"], "sumas_bloque": i["sumas_bloque"],
                            "p_gana": i["p_gana_fraccion"], "p_pierde": i["p_pierde_fraccion"],
                            "p_dos_colas": i["p_dos_colas_fraccion"], "metodo": i["metodo"],
                            "semilla_signos": i["semilla_signos"], "n_sorteos_signos": i["n_sorteos_signos"],
                            "d34": i["resultado_sin_calibrar"], "ic95": i["ic95"], "d42": i["resultado_d42"],
                            "calibrada_d42": i["calibrada"], "falsos_gana": i["falsos_gana"],
                            "falsos_pierde": i["falsos_pierde"]}
            with open(jl, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(fila, ensure_ascii=False) + "\n")
            print(json.dumps(fila, ensure_ascii=False)[:400], flush=True)
            shutil.rmtree(tmp / "s", ignore_errors=True)
            if placebo in ("a", "b") and f >= 1.0:
                break           # con el 100 % todas las semillas apagan lo mismo: una sola corrida
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
