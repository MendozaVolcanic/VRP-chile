# -*- coding: utf-8 -*-
"""VB2: escenarios sinteticos propios contra analizar_v750b.py (v2), que la bateria del autor no cubre.

Preguntas del instrumento. (1) Si la regla §6, la compuerta o los controles estuvieran rotos en el modo que cada escenario
describe, se veria? Cada escenario declara lo que la regla ESCRITA (PREREGISTRO_V750B.md §4 a §7) deberia dar y se compara
con lo que el codigo da; el control positivo del instrumento es el escenario C0 (un brazo que pierde una protegida sale de
los elegibles). (2) Si el analizador no corriera, los campos quedan en None (SIN DATO), no «ok».
Formato de las pasadas: el que deja el probe (copia del generador de mutaciones_regla_s6_v2.py, sin su argparse).
Uso: python escenarios_v2.py --arbol <arbol> --dest <tmp>
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--arbol", required=True)
ap.add_argument("--dest", required=True, type=Path)
a = ap.parse_args()
A = Path(a.arbol).resolve()
a.dest = a.dest.resolve()
ANALIZAR = A / "experiments/_s162_v750b/analizar_v750b.py"
EVAL = A / "experiments/_s157_prereg_d25/evaluar_d25.py"
SENSOR = "VIIRS_SNPP_750"
PUB = {"motivo_vacio": None, "n_abs": 0, "n_p1": 1, "n_p2": 0, "npix": 1, "vrp_mw": 0.5, "pixeles": [[33, 33, 2, 0.0, 0.9]]}
NOPUB = {"motivo_vacio": None, "n_abs": 0, "n_p1": 0, "n_p2": 0, "npix": 0, "vrp_mw": None, "pixeles": []}
COB = {"nan_67": 0, "nan_21": 0, "nan_7": 0, "nan_centro": False, "nan_7_crater": 0, "nan_crater": False}
INNER = {"Lascar": 5.0, "PuyehueCordonCaulle": 20.0, "Tupungatito": 7.0}
CELDA = {"Lascar": [32, 33], "PuyehueCordonCaulle": [23, 30], "Tupungatito": [27, 30]}
BR = ("B0", "B1", "B2", "B3", "B5")


def k_record(pub, vrp=0.5):
    if not pub:
        return {"primary_cluster": None, "distance_class": None, "vrp_mw": 0.0, "vrp_mir_mw": 0.0, "discarded_reason": None,
                "triggered_test1": False, "vrp_vent_mw": None, "t_max_k": 290.0, "sensor": SENSOR, "f5_core_vrp_mw": None,
                "anomaly_pixels": []}
    return {"primary_cluster": {"vrp_mw": vrp, "n_pixels": 1, "centroid_dist_km": 0.5}, "distance_class": "summit",
            "vrp_mw": vrp, "vrp_mir_mw": vrp, "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None,
            "t_max_k": 300.0, "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}


class Pob:
    def __init__(self):
        self.objs, self.res = [], []

    def pasada(self, volcan, hora, lab, pubs, vrp_mirova=None, ocr_vrp=None, tabla=True, k_prod=None, k_rec=True,
               sin_crater=False):
        """pubs: brazo -> publica. k_prod: lo que produccion publico (por defecto = pubs['K']). k_rec=False deja el
        record de K en None."""
        i = len(self.objs)
        filas = []
        if lab == "pos":
            if tabla:
                filas.append({"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA", "vrp_mw": vrp_mirova, "dist_km": 0.5,
                              "source": "CONS"})
            if ocr_vrp is not None:
                filas.append({"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA_OCR", "vrp_mw": ocr_vrp, "dist_km": 0.5,
                              "source": "OCR"})
        else:
            filas.append({"fecha_utc": hora + ":00", "tipo": "RUTINA", "vrp_mw": 0.0, "dist_km": None, "source": "CONS"})
        alertas = [f for f in filas if f["tipo"].startswith("ALERTA")]
        prot = any((f["vrp_mw"] or 0) >= 1.0 for f in alertas)
        kp = pubs["K"] if k_prod is None else k_prod
        self.objs.append({
            "id": i, "volcan": volcan, "hora_utc": hora, "sensor": SENSOR, "lab": lab, "protegida": prot,
            "alerta_tabla": (lab == "pos" and tabla),
            "decide": lab == "neg_limpio" or (lab == "pos" and tabla) or hora >= "2026-06-13",
            "mirova": filas, "mirova_vrp": max([f["vrp_mw"] or 0 for f in alertas], default=0.0), "z": 30.0,
            "pub_prod": bool(kp), "dc": "summit" if kp else None, "pc_vrp": 0.5 if kp else 0.0,
            "pc_n": 1 if kp else None, "granule": f"g{i}", "en_sc": False, "celda_crater": CELDA[volcan],
            "pos_crater": [float(CELDA[volcan][0]), float(CELDA[volcan][1])], "inner_km": INNER[volcan]})
        kb = {"record": k_record(pubs["K"]) if k_rec else None, "pc_pix": [[10, 10]] if pubs["K"] else []}
        cob = dict(COB)
        if sin_crater:
            cob["nan_7_crater"] = 3
        r = {"id": i, "volcan": volcan, "hora_utc": hora, "estado": "ok", "dayflag": 0, "sunglint": 40.0,
             "brazos": {"K": kb}, "cobertura": cob,
             "oraculo": {b: (PUB if pubs.get(b, pubs["B0"]) else NOPUB) for b in BR}}
        self.res.append(r)

    def escribir(self, d):
        (d / "art").mkdir(parents=True, exist_ok=True)
        (d / "art" / "resultados_00.json").write_text(json.dumps(self.res), encoding="utf-8")
        (d / "objetivos.json").write_text(json.dumps(self.objs), encoding="utf-8")


def todos(k=True, b=True):
    return {"K": k, "B0": b, "B1": b, "B2": b, "B3": b, "B5": b}


def base(n_prot=4, n_baja=3, n_neg=10, con_pcc=True):
    p = Pob()
    if con_pcc:
        p.pasada("PuyehueCordonCaulle", "2026-09-01 05:00", "pos", {**todos(), "B0": False, "B5": False}, vrp_mirova=1.2)
    for n in range(n_prot):
        p.pasada("Lascar", f"2026-05-{10 + n:02d} 05:00", "pos", todos(), vrp_mirova=1.5)
        p.pasada("Lascar", f"2026-07-{10 + n:02d} 05:00", "pos", todos(), vrp_mirova=1.5)
    for n in range(n_baja):
        p.pasada("Lascar", f"2026-05-{20 + n:02d} 05:00", "pos", todos(), vrp_mirova=0.3)
        p.pasada("Lascar", f"2026-07-{20 + n:02d} 05:00", "pos", todos(), vrp_mirova=0.3)
    for n in range(n_neg):
        p.pasada("Lascar", f"2026-04-{10 + n:02d} 05:00", "neg_limpio", todos(b=False, k=False))
        p.pasada("Lascar", f"2026-08-{10 + n:02d} 05:00", "neg_limpio", todos(b=False, k=False))
    return p


def correr(nombre, p, bandera=True, extra=()):
    d = a.dest / nombre
    p.escribir(d)
    cmd = [sys.executable, str(ANALIZAR), "--art", str(d / "art"), "--objetivos", str(d / "objetivos.json"),
           "--evaluador", str(EVAL), "--salida", str(d / "salida.txt")] + list(extra)
    if bandera:
        cmd.append("--censo-omitido-solo-pruebas")
    o = subprocess.run(cmd, capture_output=True, text=True, cwd=str(A), timeout=600, encoding="utf-8", errors="replace")
    txt = o.stdout + o.stderr
    (d / "stdout.txt").write_text(txt, encoding="utf-8")

    def g(pat):
        m = re.search(pat, txt)
        return m.group(1) if m else None

    def p2de(titulo):
        out = {}
        bl = txt.rfind(titulo)
        if bl >= 0:
            fin = txt.find("\n== ", bl + 5)
            seg = txt[bl:fin if fin > 0 else len(txt)]
            for m in re.finditer(r"^\s+(B\d)\s+prot.*?P2 contra B1: ([A-Z ]+?) \(neto (-?\d+), bloques (\d+)", seg, re.M):
                out[m.group(1)] = f"{m.group(2).strip()}(neto {m.group(3)}, bl {m.group(4)})"
        return out

    return {"rc": o.returncode, "elegibles": g(r"6\.1 elegibles.*?:\s*(\[.*?\])"), "roi": g(r"6 ROI elegida: (\S+)"),
            "compuerta": g(r"compuerta del veredicto.*?: (\w+)"), "p2_decide": p2de("== ventana TO, canal decide"),
            "p2_tabla": p2de("== ventana TO, canal tabla"), "txt": txt}


def informar(nombre, esperado, r, extra_lineas=()):
    print(f"\n== {nombre}\n   esperado por la regla escrita: {esperado}\n   codigo: rc={r['rc']} compuerta={r['compuerta']} "
          f"elegibles={r['elegibles']} ROI={r['roi']}\n   P2 TO decide: {r['p2_decide']}\n   P2 TO tabla : {r['p2_tabla']}",
          flush=True)
    for pat in extra_lineas:
        for ln in r["txt"].splitlines():
            if pat in ln:
                print("   |", ln[:260], flush=True)


# C0 control positivo del instrumento: B2 pierde una protegida de PCC y tiene que salir de los elegibles.
p = base()
p.pasada("PuyehueCordonCaulle", "2026-07-05 05:30", "pos", {**todos(), "B2": False, "B0": False}, vrp_mirova=1.2)
informar("C0 control positivo: B2 pierde una protegida", "B2 fuera de los elegibles", correr("C0", p))

# V1: B2 EMPATA en el canal que decide (T tabla, O todo) pero PIERDE en la tabla sola. B0 pierde en los dos canales.
p = base()
for n in range(6):
    p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio", {**todos(b=False, k=False), "B0": True, "B2": True})
    p.pasada("Lascar", f"2026-09-{20 + n:02d} 05:00", "pos",
             {**todos(), "B1": False, "B3": False, "B0": False, "B5": False, "B2": True}, tabla=False, ocr_vrp=0.4)
informar("V1 B2 EMPATA con todo pero PIERDE con la tabla sola",
         "§6.3 «nunca uno que PIERDE o BLOQUEA»: ¿cuenta la tabla sola? el §6.2 si la exige para ganar", correr("V1", p))

# V2: B1 pierde una protegida (no elegible); B3 tambien; B2 y B4 no.
p = base()
p.pasada("Lascar", "2026-07-05 05:30", "pos", {**todos(), "B1": False, "B3": False}, vrp_mirova=1.2)
informar("V2 B1 pierde una protegida (B1 no elegible)",
         "§6.3: «si B1 tampoco es elegible y nadie mas lo es: NINGUN»; si otros lo son, ¿contra quien se comparan?",
         correr("V2", p))

# V3: SIN SUSTRATO admite un brazo peor en todos los bloques: B2 publica 4 negativos de mas en 4 noches.
p = base()
for n in range(4):
    p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio", {**todos(b=False, k=False), "B2": True, "B0": True})
informar("V3 B2 y B4 publican 4 negativos de mas en 4 noches (neto +4, 4 bloques)",
         "D-45: con 4 bloques o menos SIN SUSTRATO; ¿se elige por fidelidad un brazo estrictamente peor?", correr("V3", p))

# V4: sin ninguna bandera de censo (corrida real sin --censo-art): la compuerta tiene que cerrarse.
informar("V4 sin censo y sin bandera", "compuerta CERRADA, rc 3, sin veredicto", correr("V4", base(), bandera=False))

# V5: con la bandera de pruebas en una corrida «real»: ¿la linea del veredicto avisa?
r5 = correr("V5", base())
informar("V5 bandera --censo-omitido-solo-pruebas puesta en una corrida con datos",
         "el veredicto no deberia poder confundirse con uno valido: ¿la linea ROI elegida lo dice?", r5,
         extra_lineas=("OMITIDO", "ROI elegida", "compuerta"))

# V6: oraculo muerto (ningun brazo publica nada, produccion si): ¿el control positivo lo ve?
p = Pob()
muerto = {"K": True, "B0": False, "B1": False, "B2": False, "B3": False, "B5": False}
p.pasada("PuyehueCordonCaulle", "2026-09-01 05:00", "pos", muerto, vrp_mirova=1.2)
for n in range(6):
    p.pasada("Lascar", f"2026-07-{10 + n:02d} 05:00", "pos", muerto, vrp_mirova=1.5)
for n in range(10):
    p.pasada("Lascar", f"2026-04-{10 + n:02d} 05:00", "neg_limpio", todos(b=False, k=False))
informar("V6 oraculo muerto: B0 a B5 no publican nada (produccion si)",
         "el control positivo deberia exigir que B1 SI publique lo que B0 pierde; con oraculo muerto deberia caer",
         correr("V6", p), extra_lineas=("control positivo",))

# V7: una protegida con K distinto de produccion (K no publica) en un run grande.
p = base(n_neg=40)
p.pasada("Lascar", "2026-07-30 05:00", "pos", {**todos(), "K": False}, vrp_mirova=2.0, k_prod=True)
informar("V7 una protegida donde K no publica y produccion si", "§7: «hay una protegida: se detiene» (compuerta CERRADA)",
         correr("V7", p), extra_lineas=("control K",))

# V8: K distinto en 1 de ~120 pasadas, no protegida (<1 %): sale de los brazos y se lista.
p = base(n_neg=50)
p.pasada("Lascar", "2026-07-31 05:00", "neg_limpio", {**todos(b=False), "K": True}, k_prod=False)
informar("V8 K distinto en una pasada no protegida (<1 %)", "sale de los brazos, se lista, compuerta ABIERTA", correr("V8", p),
         extra_lineas=("control K",))

# V9: record de K en None donde produccion SI publico una protegida.
p = base()
p.pasada("Lascar", "2026-07-29 05:00", "pos", todos(), vrp_mirova=2.0, k_rec=False)
informar("V9 record de K = None donde produccion publico una protegida", "K distinto de produccion en una protegida: CERRADA",
         correr("V9", p), extra_lineas=("control K",))

# V10: protegida con 7 x 7 del cráter con NaN (sin_crater): ¿se lista por nombre?
p = base()
p.pasada("PuyehueCordonCaulle", "2026-07-02 05:00", "pos", {**todos(), "B0": False, "B2": False, "B3": False}, vrp_mirova=3.0,
         sin_crater=True)
informar("V10 protegida con celdas sin dato en el 7 x 7 del crater",
         "contada aparte y fuera del denominador; ¿listada por nombre?", correr("V10", p),
         extra_lineas=("observadas", "protegidas SIN DATO"))

# V11: dos brazos ganan; el de menor E en T u O; se prueba que el desempate por E usa E, no el orden de PREF.
p = base()
for n in range(7):
    p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio",
             {**todos(b=False, k=False), "B1": True, "B0": True, "B5": True, "B2": False, "B3": False})
for n in range(2):
    p.pasada("Lascar", f"2026-09-{20 + n:02d} 05:00", "pos", {**todos(), "B2": False}, vrp_mirova=0.4)
informar("V11 B2 y B3 ganan; B3 tiene menor E", "ROI = B3", correr("V11", p))


# V12: la seccion del brazo nativo (V750-C) del analizador nunca corre en la bateria del autor (en_sc = False en todas las
# pasadas). Aqui se marcan 3 pasadas como S_C con ventana nativa, para ver que esa seccion corre sin caerse y cuenta bien.
p = base()
ids = [k for k, o in enumerate(p.objs) if o["lab"] == "neg_limpio"][:3]
for k in ids:
    p.objs[k]["en_sc"] = True
    p.objs[k]["dc"] = "summit"
    p.objs[k]["pc_vrp"] = 0.0
    p.res[k]["geometria_centro"] = {"sensor_zenith": 47.0}
    p.res[k]["nativo_esquina_fila_col"] = [100, 100]
    p.res[k]["brazos"]["K"]["pc_pix"] = [[133, 133]]
    p.res[k]["nativo"] = {"N0": {"npix": 1, "pixeles": [[33, 33, 2, 0.0, 0.9]]},
                          "N1": {"npix": 0, "pixeles": []}}
r12 = correr("V12", p)
informar("V12 seccion nativa con 3 pasadas S_C", "N0 detecta en el pixel de K en 3 de 3 (cenit 40-50), N1 en 0; sin caida",
         r12, extra_lineas=("V750-C", "cumbre0_neg"))
print("   rc", r12["rc"], "| ultimas lineas:", r12["txt"].strip().splitlines()[-3:])
