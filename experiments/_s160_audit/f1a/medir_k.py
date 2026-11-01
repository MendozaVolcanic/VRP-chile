# -*- coding: utf-8 -*-
"""F1a, filas R2 y R6 sobre el instrumento de K (`experiments/_s151_prereg_fk_11/evaluar_fk.py`).

Que hace: fabrica brazos K de PLACEBO a partir del control C0 de la union real de V1 (y de V2) y corre el evaluador
ORIGINAL sobre ellos, sin tocarlo. Un placebo no trae informacion nueva: si el evaluador le dice CUMPLE, el
instrumento no podia fallar.
  x110   K := C0 con todas las magnitudes por 1,10 (vrp_mw, pc.vrp_mw, f5_core_vrp_mw, vrp_mir_mw, pixeles)
  x120   K := C0 con todas las magnitudes por 1,20
  shift  K := C0 con la decision de cada pasada DESPLAZADA a la pasada siguiente del mismo volcan y sensor
         (ciclico): mismas pasadas, mismas publicaciones en numero, sin relacion con la noche
  borra_K      K real sin un dia (2026-09-15 en V1): fila R2, un brazo
  borra_todos  los cuatro brazos sin ese dia: informativo (R2 habla de un brazo)
En todos los placebos `triggered_test1` se pone en False (huella que el control de cableado exige a un brazo sin
Test 1); los logs de K se reutilizan tal cual (el placebo se hace pasar por K ante el control de cableado).

Las dos preguntas del instrumento: (1) si el evaluador aceptara placebos, el veredicto de K con placebo saldria
CUMPLE y lo veria; (2) si esta medicion estuviera muerta (el placebo no llegara al evaluador), el veredicto del
placebo seria identico al de K real en TODAS las lineas; se imprime P2 (sumas) para distinguirlo.
Uso: python medir_k.py <D_union_v1> <D_union_v2a> <D_union_v2b> <salida_dir> <produccion> <v1_rep.json>
"""
import copy, json, shutil, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
EVAL = RAIZ / "experiments" / "_s151_prereg_fk_11" / "evaluar_fk.py"
BRAZOS = {"C0": "_s146_ab_control", "F": "_s147_ab_sin_test1_max", "K": "_s149_ab_sin_test1_b22_max", "G": "_s151_ab_control_gemelo"}
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
DIA_BORRADO = "2026-09-15"
CAMPOS_DECISION = ("primary_cluster", "distance_class", "vrp_mw", "vrp_mir_mw", "f5_core_vrp_mw", "anomaly_pixels",
                   "discarded_anomaly_pixels", "discarded_reason", "vrp_vent_mw", "t_max_k", "final_hotspot_source",
                   "n_anomalous_pixels", "hotspot_lat", "hotspot_lon", "final_hotspot_lat", "final_hotspot_lon",
                   "final_hotspot_dist_km", "sensor_zenith_deg")


def bucket(s):
    s = s or ""
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else ("VIIRS375" if s.startswith("VIIRS") else None))


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
    r["triggered_test1"] = False
    return r


def placebo_escala(docs, g):
    return {v: {"records": [escalar(copy.deepcopy(r), g) for r in d["records"]]} for v, d in docs.items()}


def placebo_shift(docs):
    out = {}
    for v, d in docs.items():
        recs = [copy.deepcopy(r) for r in d["records"]]
        grupos = {}
        for i, r in enumerate(recs):
            grupos.setdefault(bucket(r.get("sensor")), []).append(i)
        nuevos = [None] * len(recs)
        for b, idx in grupos.items():
            idx.sort(key=lambda i: recs[i].get("datetime_utc", ""))
            for j, i in enumerate(idx):
                fuente = recs[idx[(j + 1) % len(idx)]]
                r = copy.deepcopy(recs[i])
                for c in CAMPOS_DECISION:
                    if c in fuente:
                        r[c] = copy.deepcopy(fuente[c])
                    elif c in r:
                        del r[c]
                r["triggered_test1"] = False
                nuevos[i] = r
        out[v] = {"records": [x for x in nuevos if x is not None]}
    return out


def sin_dia(docs, dia):
    return {v: {"records": [r for r in d["records"] if r.get("datetime_utc", "")[:10] != dia]} for v, d in docs.items()}


def leer(raiz, n):
    return {v: json.load(open(Path(raiz) / BRAZOS[n] / (v + ".json"), encoding="utf-8")) for v in VOLS}


def escribir(dst, n, docs):
    (dst / BRAZOS[n]).mkdir(parents=True, exist_ok=True)
    for v, d in docs.items():
        json.dump(d, open(dst / BRAZOS[n] / (v + ".json"), "w", encoding="utf-8"))


def correr(caso, args, salida):
    r = subprocess.run([sys.executable, str(EVAL)] + args, capture_output=True, text=True, encoding="utf-8")
    (salida / (caso + ".log")).write_text(r.stdout + "\n--- stderr ---\n" + r.stderr, encoding="utf-8")
    res = {}
    out = [a for i, a in enumerate(args) if args[i - 1] == "--out"][0]
    if Path(out).exists():
        res = json.load(open(out, encoding="utf-8"))
    lineas = [l for l in r.stdout.splitlines() if l.startswith("      P2 K lectura A") or l.startswith("   K lectura A") or "cobertura" in l.lower() and "OK" in l or "DESPAREJA" in l]
    return res, lineas


def main():
    d_v1, d_v2a, d_v2b, salida, prod, v1json = sys.argv[1:7]
    salida = Path(salida); salida.mkdir(parents=True, exist_ok=True)
    work = Path(d_v1).parent / "placebos"; shutil.rmtree(work, ignore_errors=True)
    resumen = {}
    # ---------------- V1
    base = {n: leer(d_v1, n) for n in ("C0", "F", "K", "G")}
    casos = {"x110": ("K", placebo_escala(base["C0"], 1.10)),
             "x120": ("K", placebo_escala(base["C0"], 1.20)),
             "shift": ("K", placebo_shift(base["C0"])),
             "borra_K": ("K", sin_dia(base["K"], DIA_BORRADO)),
             "borra_todos": (None, None)}
    for caso, (brazo, docs) in casos.items():
        dst = work / ("v1_" + caso)
        for n in ("C0", "F", "K", "G"):
            if caso == "borra_todos":
                escribir(dst, n, sin_dia(base[n], DIA_BORRADO))
            elif n == brazo:
                escribir(dst, n, docs)
            else:
                escribir(dst, n, base[n])
        shutil.copytree(Path(d_v1) / "logs", dst / "logs")
        args = ["--ventana", "V1", "--raiz", str(dst), "--logs", str(dst / "logs"), "--out", str(dst / "res.json"),
                "--tmp", str(dst / "tmp"), "--produccion", prod]
        res, lineas = correr("v1_" + caso, args, salida)
        resumen["v1_" + caso] = {"global_K": res.get("global", {}).get("K"), "cobertura_ok": res.get("cobertura_ok"),
                                 "cableado": res.get("cableado"), "determinismo_ok": res.get("determinismo_ok"),
                                 "P1_K_A": {s: res.get("veredicto", {}).get("P1|K|%s|A" % s) for s in ("MODIS", "VIIRS375", "VIIRS750")},
                                 "P2_K_A": {s: res.get("veredicto", {}).get("P2|K|%s|A" % s) for s in ("MODIS", "VIIRS375", "VIIRS750")},
                                 "suma_K_A": {s: res.get("suma", {}).get("K|%s|A" % s, {}).get("decide") for s in ("MODIS", "VIIRS375", "VIIRS750")},
                                 "suma_C0_A": {s: res.get("suma", {}).get("C0|%s|A" % s, {}).get("decide") for s in ("MODIS", "VIIRS375", "VIIRS750")}}
        print("V1", caso, json.dumps(resumen["v1_" + caso], ensure_ascii=False)); sys.stdout.flush()
    # ---------------- V2 (C0 y K; x120 y shift)
    base2 = {n: {"a": leer(d_v2a, n), "b": leer(d_v2b, n)} for n in ("C0", "K")}
    for caso in ("x120", "shift"):
        dst = work / ("v2_" + caso)
        for parte, d_src in (("a", d_v2a), ("b", d_v2b)):
            escribir(dst / parte, "C0", base2["C0"][parte])
            docs = placebo_escala(base2["C0"][parte], 1.20) if caso == "x120" else placebo_shift(base2["C0"][parte])
            escribir(dst / parte, "K", docs)
            shutil.copytree(Path(d_src) / "logs", dst / parte / "logs")
        args = ["--ventana", "V2", "--raiz", str(dst / "a"), "--raiz", str(dst / "b"), "--logs", str(dst / "a" / "logs"),
                "--logs", str(dst / "b" / "logs"), "--ruido-de", v1json, "--out", str(dst / "res.json"), "--tmp", str(dst / "tmp"),
                "--produccion", prod]
        res, lineas = correr("v2_" + caso, args, salida)
        resumen["v2_" + caso] = {"global_K": res.get("global", {}).get("K"), "cobertura_ok": res.get("cobertura_ok"),
                                 "cableado": res.get("cableado"),
                                 "P1_K_A": {s: res.get("veredicto", {}).get("P1|K|%s|A" % s) for s in ("MODIS", "VIIRS375", "VIIRS750")},
                                 "P2_K_A": {s: res.get("veredicto", {}).get("P2|K|%s|A" % s) for s in ("MODIS", "VIIRS375", "VIIRS750")},
                                 "suma_K_A": {s: res.get("suma", {}).get("K|%s|A" % s, {}).get("decide") for s in ("MODIS", "VIIRS375", "VIIRS750")},
                                 "suma_C0_A": {s: res.get("suma", {}).get("C0|%s|A" % s, {}).get("decide") for s in ("MODIS", "VIIRS375", "VIIRS750")}}
        print("V2", caso, json.dumps(resumen["v2_" + caso], ensure_ascii=False)); sys.stdout.flush()
    (salida / "resumen.json").write_text(json.dumps(resumen, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
