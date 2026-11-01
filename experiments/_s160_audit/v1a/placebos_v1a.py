# -*- coding: utf-8 -*-
"""V1a (verificador de F1a). Placebos PROPIOS, construidos por otro camino que el del auditor, sobre la regla con
que se adopto K (experiments/_s151_prereg_fk_11/evaluar_fk.py, sin tocarlo).

Diferencia con el auditor: el auditor apago triggered_test1 (el disfraz que pide el control de cableado). Ese flag
lo lee el predicado del tablero (isSummitDetection, frontend/index.html:1613 en d516b9d8c) en los records con
vrp_mw 0 y discarded_reason, asi que el disfraz NO es neutro. Aqui el disfraz es NEUTRO: se apaga triggered_test1
y, en exactamente esos records, se borra discarded_reason, con lo que isSummitDetection cae a las mismas ramas de
distance_class que con el flag encendido (la linea 1613 es la unica que mira discarded_reason entre las funciones
que ejecuta banco_paridad.correr_node; isValidDetection solo mira el flag si no hay primary_cluster y vrp_mw 0, y
eso no ocurre en C0 V1: contado en la sesion). Control: el caso `neutro` tiene que dar sumas de P2 IDENTICAS a C0.

Placebos (todos sobre C0 con disfraz neutro, puestos en F y en K a la vez en V1, en K en V2; C0 y G reales):
  neutro        sin cambio de publicacion (nulo del placebo: tiene que dar EMPATE y NO CUMPLE (no gana))
  t1off         disfraz del auditor, sin compensar (replica 161 por otro script)
  x080 / x125   magnitudes por 0,8 y 1,25
  perm_s        permuta, dentro de cada volcan y sensor, el record entero (salvo hora y sensor) entre pasadas al azar
  azar_q_s      apaga la publicacion (distance_class="far") de una fraccion q de los records, al azar, sin mirar
                etiqueta ni publicacion: el placebo SIN INFORMACION por excelencia
Uso: python placebos_v1a.py <ventana V1|V2> <salida_dir> <casos separados por coma> [--semillas N]
"""
import copy, json, random, shutil, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
EVAL = RAIZ / "experiments" / "_s151_prereg_fk_11" / "evaluar_fk.py"
B = {"C0": "_s146_ab_control", "F": "_s147_ab_sin_test1_max", "K": "_s149_ab_sin_test1_b22_max", "G": "_s151_ab_control_gemelo"}
D = Path(r"D:\vrp-trabajo\temporales\s160_audit")
U = {"V1": [D / "f1a" / "v1_union"], "V2": [D / "f1a" / "v2a_union", D / "f1a" / "v2b_union"]}
PROD = D / "main" / "data" / "mirova_equivalent"
V1REP = AQUI.parent / "f1a" / "salidas" / "v1_rep.json"
TRAB = D / "v1a" / "placebos"


def leer(raiz, n):
    out = {}
    for p in sorted((raiz / B[n]).glob("*.json")):
        out[p.stem] = json.load(open(p, encoding="utf-8"))
    return out


def escribir(dst, n, docs):
    (dst / B[n]).mkdir(parents=True, exist_ok=True)
    for v, d in docs.items():
        json.dump(d, open(dst / B[n] / (v + ".json"), "w", encoding="utf-8"))


def disfraz_neutro(r):
    if r.get("triggered_test1"):
        if (r.get("vrp_mw") or 0) == 0 and r.get("discarded_reason"):
            r["discarded_reason"] = None
        r["triggered_test1"] = False
    return r


def escalar(r, g):
    for c in ("vrp_mw", "vrp_mir_mw", "f5_core_vrp_mw", "vrp_vent_mw"):
        if r.get(c):
            r[c] = r[c] * g
    pc = r.get("primary_cluster")
    if pc and pc.get("vrp_mw"):
        pc["vrp_mw"] = pc["vrp_mw"] * g
    for q in r.get("anomaly_pixels") or []:
        if q.get("vrp_mw"):
            q["vrp_mw"] = q["vrp_mw"] * g
    return r


def bucket(s):
    s = s or ""
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else ("VIIRS375" if s.startswith("VIIRS") else "otro"))


def fabricar(docs, caso, semilla):
    rng = random.Random(semilla)
    out = {}
    for v, d in docs.items():
        recs = [copy.deepcopy(r) for r in d["records"]]
        if caso == "t1off":
            for r in recs:
                r["triggered_test1"] = False
        else:
            for r in recs:
                disfraz_neutro(r)
            if caso.startswith("x"):
                g = int(caso[1:]) / 100.0
                for r in recs:
                    escalar(r, g)
            elif caso == "perm":
                grupos = {}
                for i, r in enumerate(recs):
                    grupos.setdefault(bucket(r.get("sensor")), []).append(i)
                nuevos = list(recs)
                for idx in grupos.values():
                    dest = idx[:]; rng.shuffle(dest)
                    for i, j in zip(idx, dest):
                        r = copy.deepcopy(recs[j])
                        r["datetime_utc"] = recs[i].get("datetime_utc"); r["sensor"] = recs[i].get("sensor")
                        r["product_version"] = recs[i].get("product_version")
                        nuevos[i] = r
                recs = nuevos
            elif caso.startswith("azar"):
                q = float(caso.split("_")[1])
                for r in recs:
                    if rng.random() < q:
                        r["distance_class"] = "far"; r["vrp_vent_mw"] = 0.0
            elif caso != "neutro":
                raise SystemExit("caso desconocido " + caso)
        out[v] = {"records": recs}
    return out


def correr(ventana, caso, semilla, salida):
    dst = TRAB / ("%s_%s_%d" % (ventana, caso, semilla)); shutil.rmtree(dst, ignore_errors=True)
    raices = U[ventana]; args = ["--ventana", ventana]
    for i, src in enumerate(raices):
        sub = dst / ("p%d" % i)
        base = {n: leer(src, n) for n in B if (src / B[n]).exists()}
        pl = fabricar(base["C0"], caso, semilla * 7 + i)
        for n in base:
            escribir(sub, n, pl if n in ("F", "K") else base[n])
        shutil.copytree(src / "logs", sub / "logs")
        args += ["--raiz", str(sub)]
    for i in range(len(raices)):
        args += ["--logs", str(dst / ("p%d" % i) / "logs")]
    if ventana == "V2":
        args += ["--ruido-de", str(V1REP)]
    args += ["--out", str(dst / "res.json"), "--tmp", str(dst / "tmp"), "--produccion", str(PROD)]
    o = subprocess.run([sys.executable, str(EVAL)] + args, capture_output=True, text=True, encoding="utf-8")
    log = salida / "logs" / ("%s_%s_%d.log" % (ventana, caso, semilla)); log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(o.stdout + "\n--- stderr\n" + o.stderr[-4000:], encoding="utf-8")
    res = json.loads((dst / "res.json").read_text(encoding="utf-8")) if (dst / "res.json").exists() else {}
    S = ("MODIS", "VIIRS375", "VIIRS750")
    fila = {"ventana": ventana, "caso": caso, "semilla": semilla, "rc": o.returncode,
            "global_K_A": (res.get("global") or {}).get("K", {}).get("A"),
            "controles_ok": res.get("controles_ok"), "cableado_K": (res.get("cableado") or {}).get("K"),
            "P1_A": [res.get("veredicto", {}).get("P1|K|%s|A" % s) for s in S],
            "P2_A": [res.get("veredicto", {}).get("P2|K|%s|A" % s) for s in S],
            "sumaK_A": [res.get("suma", {}).get("K|%s|A" % s, {}).get("decide") for s in S],
            "sumaC0_A": [res.get("suma", {}).get("C0|%s|A" % s, {}).get("decide") for s in S],
            "d9": {k: v for k, v in (res.get("reglas_d9") or {}).items() if isinstance(v, (str, dict))} if False else None}
    shutil.rmtree(dst, ignore_errors=True)   # disco: los logs quedan, los JSON fabricados no
    return fila


def main():
    ventana, salida, casos = sys.argv[1], Path(sys.argv[2]), sys.argv[3].split(",")
    nsem = int(sys.argv[sys.argv.index("--semillas") + 1]) if "--semillas" in sys.argv else 1
    salida.mkdir(parents=True, exist_ok=True)
    jl = salida / ("filas_%s.jsonl" % ventana)
    for caso in casos:
        sems = range(nsem) if (caso.startswith("azar") or caso == "perm") else [0]
        for s in sems:
            f = correr(ventana, caso, s, salida)
            with open(jl, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(f, ensure_ascii=False) + "\n")
            print(json.dumps(f, ensure_ascii=False)); sys.stdout.flush()


if __name__ == "__main__":
    main()
