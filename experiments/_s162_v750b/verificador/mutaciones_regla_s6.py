# -*- coding: utf-8 -*-
"""Verificador V750-B (VB): bateria de mutaciones sinteticas contra la regla §6 de analizar_v750b.py.

POR QUE. La regla de decision se aplica una sola vez sobre un run de 2 h; si puede dar un veredicto por una razon que no
es la del pre-registro, no se puede corregir despues. Aqui se arman poblaciones sinteticas en el formato exacto que deja
el probe (objetivos + resultados_00.json), con publicacion controlada por brazo, y se corre analizar_v750b.py entero
(predicado del tablero con node incluido). Cada escenario predice lo que la regla ESCRITA deberia dar y mira lo que el
codigo da.

Pregunta 1 (si la regla estuviera rota, se ve?): el escenario E0 es el control positivo del instrumento: un brazo que
pierde una protegida TIENE que salir de los elegibles; si no sale, la bateria no mide nada.
Pregunta 2 (instrumento muerto): si analizar_v750b.py no corre o no imprime la linea ROI elegida, el escenario queda
SIN DATO (campos None), no ok.
Uso: python mutaciones_regla_s6.py --arbol <arbol de origin/main con _s162_v750b y evaluar_d25.py del tag> --dest <tmp>
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--arbol", required=True)
ap.add_argument("--dest", required=True, type=Path)
a = ap.parse_args()
A = Path(a.arbol)
ANALIZAR = A / "experiments/_s162_v750b/analizar_v750b.py"
EVAL = A / "experiments/_s157_prereg_d25/evaluar_d25.py"
SENSOR = "VIIRS_SNPP_750"
PUB = {"motivo_vacio": None, "n_abs": 0, "n_p1": 1, "n_p2": 0, "npix": 1, "vrp_mw": 0.5,
       "pixeles": [[33, 33, 2, 0.0, 0.9]]}
NOPUB = {"motivo_vacio": None, "n_abs": 0, "n_p1": 0, "n_p2": 0, "npix": 0, "vrp_mw": None, "pixeles": []}
COB = {"nan_67": 0, "nan_21": 0, "nan_7": 0, "nan_centro": False}
INNER = {"Lascar": 5.0, "PuyehueCordonCaulle": 20.0, "Tupungatito": 7.0}
CELDA = {"Lascar": [32, 33], "PuyehueCordonCaulle": [23, 30], "Tupungatito": [27, 30]}


def k_record(pub, vrp=0.5):
    if not pub:
        return {"primary_cluster": None, "distance_class": None, "vrp_mw": 0.0, "vrp_mir_mw": 0.0,
                "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None, "t_max_k": 290.0,
                "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}
    return {"primary_cluster": {"vrp_mw": vrp, "n_pixels": 1, "centroid_dist_km": 0.5}, "distance_class": "summit",
            "vrp_mw": vrp, "vrp_mir_mw": vrp, "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None,
            "t_max_k": 300.0, "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}


class Pob:
    def __init__(self):
        self.objs, self.res = [], []

    def pasada(self, volcan, hora, lab, pubs, vrp_mirova=None, ocr_vrp=None, tabla=True, k_error=False,
               grilla_incompleta=False):
        """pubs: dict brazo -> publica (K, B0, B1, B2, B3). Protegida si alguna fila ALERTA tiene 1 MW o mas
        (clase_mirova.alerta_protegida no mira la fuente)."""
        i = len(self.objs)
        filas = []
        if lab == "pos":
            if tabla:
                filas.append({"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA", "vrp_mw": vrp_mirova,
                              "dist_km": 0.5, "source": "CONS"})
            if ocr_vrp is not None:
                filas.append({"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA_OCR", "vrp_mw": ocr_vrp,
                              "dist_km": 0.5, "source": "OCR"})
        else:
            filas.append({"fecha_utc": hora + ":00", "tipo": "RUTINA", "vrp_mw": 0.0, "dist_km": None,
                          "source": "CONS"})
        alertas = [f for f in filas if f["tipo"].startswith("ALERTA")]
        prot = any((f["vrp_mw"] or 0) >= 1.0 for f in alertas)
        self.objs.append({
            "id": i, "volcan": volcan, "hora_utc": hora, "sensor": SENSOR, "lab": lab, "protegida": prot,
            "alerta_tabla": (lab == "pos" and tabla),
            "decide": lab == "neg_limpio" or (lab == "pos" and tabla) or hora >= "2026-06-13",
            "mirova": filas, "mirova_vrp": max([f["vrp_mw"] or 0 for f in alertas], default=0.0),
            "z": 30.0, "pub_prod": bool(pubs["K"]) and not k_error, "dc": "summit" if pubs["K"] else None,
            "pc_vrp": 0.5 if pubs["K"] else 0.0, "pc_n": 1 if pubs["K"] else None, "granule": f"g{i}",
            "en_sc": False, "celda_crater": CELDA[volcan], "inner_km": INNER[volcan]})
        if k_error:
            kb = {"error": "RuntimeError: sintetico", "traza": ""}
        else:
            kb = {"record": k_record(pubs["K"]), "pc_pix": [[10, 10]] if pubs["K"] else []}
        r = {"id": i, "volcan": volcan, "hora_utc": hora, "estado": "ok", "dayflag": 0, "sunglint": 40.0,
             "brazos": {"K": kb}}
        if grilla_incompleta:
            r["oraculo"], r["oraculo_estado"] = {}, "grilla_incompleta"
        else:
            r["cobertura"] = COB
            r["oraculo"] = {b: (PUB if pubs[b] else NOPUB) for b in ("B0", "B1", "B2", "B3")}
        self.res.append(r)

    def escribir(self, d):
        (d / "art").mkdir(parents=True, exist_ok=True)
        (d / "art" / "resultados_00.json").write_text(json.dumps(self.res), encoding="utf-8")
        (d / "objetivos.json").write_text(json.dumps(self.objs), encoding="utf-8")


def todos(k=True, b=True):
    return {"K": k, "B0": b, "B1": b, "B2": b, "B3": b}


def base():
    """Poblacion comun: 4 protegidas y 3 bajas en T, 4 protegidas y 3 bajas en O, todas publicadas por todos; 10
    negativos limpios en T y 10 en O que nadie publica."""
    p = Pob()
    for n in range(4):
        p.pasada("Lascar", f"2026-05-{10 + n:02d} 05:00", "pos", todos(), vrp_mirova=1.5)
        p.pasada("Lascar", f"2026-07-{10 + n:02d} 05:00", "pos", todos(), vrp_mirova=1.5)
    for n in range(3):
        p.pasada("Lascar", f"2026-05-{20 + n:02d} 05:00", "pos", todos(), vrp_mirova=0.3)
        p.pasada("Lascar", f"2026-07-{20 + n:02d} 05:00", "pos", todos(), vrp_mirova=0.3)
    for n in range(10):
        p.pasada("Lascar", f"2026-04-{10 + n:02d} 05:00", "neg_limpio", todos(b=False, k=False))
        p.pasada("Lascar", f"2026-08-{10 + n:02d} 05:00", "neg_limpio", todos(b=False, k=False))
    return p


def correr(nombre, p):
    d = a.dest / nombre
    p.escribir(d)
    o = subprocess.run([sys.executable, str(ANALIZAR), "--art", str(d / "art"), "--objetivos",
                        str(d / "objetivos.json"), "--evaluador", str(EVAL), "--salida", str(d / "salida.txt")],
                       capture_output=True, text=True, cwd=str(A), timeout=600, encoding="utf-8", errors="replace")
    txt = o.stdout + o.stderr
    (d / "stdout.txt").write_text(txt, encoding="utf-8")
    eleg = re.search(r"6\.1 elegibles.*?:\s*(\[.*?\])", txt)
    roi = re.search(r"6 ROI elegida: (\S+) \((.*?)\)", txt)
    cob = re.search(r"ok y observadas: (\d+) \| no observadas \(fuera del denominador\): (\{.*?\}) \| SIN DATO: (\d+)",
                    txt)
    prot_sin = re.search(r"protegidas SIN DATO \(falla de cobertura, no de brazo\): (.*)", txt)
    cpos = re.search(r"control positivo \(B0 pierde protegidas de Cord.n Caulle\): (\d+)", txt)
    p2 = {}
    bloque = txt.rfind("== ventana TO, canal todo")
    if bloque >= 0:
        for m in re.finditer(r"^\s+(B\d)\s+prot.*?P2 contra B1: ([A-Z ]+?) \(", txt[bloque:], re.M):
            p2[m.group(1)] = m.group(2).strip()
    return {"rc": o.returncode, "elegibles": eleg.group(1) if eleg else None, "roi": roi.group(1) if roi else None,
            "motivo": roi.group(2) if roi else None, "cobertura": cob.groups() if cob else None,
            "prot_sin_dato": prot_sin.group(1).strip() if prot_sin else None,
            "control_positivo": cpos.group(1) if cpos else None, "p2_TO_todo": p2}


out = []


def informar(nombre, esperado, r):
    s = (f"\n== {nombre}\n   esperado por la regla escrita: {esperado}\n"
         f"   codigo: rc={r['rc']} elegibles={r['elegibles']} ROI={r['roi']} ({r['motivo']})\n"
         f"   cobertura (ok, no_obs, SIN DATO)={r['cobertura']} protegidas SIN DATO={r['prot_sin_dato']} "
         f"control positivo={r['control_positivo']}\n   P2 contra B1 (TO, todo): {r['p2_TO_todo']}")
    out.append(s)
    print(s, flush=True)


# E0, control positivo del instrumento: B2 y B0 pierden una protegida de PCC en O. B4 = B1 en PCC, asi que B4 sigue.
p = base()
p.pasada("PuyehueCordonCaulle", "2026-07-05 05:30", "pos",
         {"K": True, "B0": False, "B1": True, "B2": False, "B3": True}, vrp_mirova=1.2)
informar("E0 control positivo: B2 y B0 pierden una protegida de PCC",
         "elegibles sin B0 ni B2 (B4 = B1 en PCC, sigue); control positivo del analizador = 1", correr("E0", p))

# E1: nadie pierde protegidas; B0 (y por tanto B2 y B4 en Lascar) publica 8 negativos limpios que B1 no publica, en 8
# noches distintas: B0, B2 y B4 PIERDEN contra B1 (p = 1/256). B3 = B1.
p = base()
for n in range(8):
    p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio",
             {"K": False, "B0": True, "B1": False, "B2": True, "B3": False})
informar("E1 B4, B2 y B0 PIERDEN contra B1 (8 negativos de mas en 8 bloques); B3 = B1",
         "6.2: nadie GANA; 6.3 cubre empates o BLOQUEA, no PIERDE; un brazo que pierde con p = 1/256 no es igual "
         "desempeno: deberia quedar B1 (o B3), nunca B4", correr("E1", p))

# E2: en T (tabla sola decide) una alerta con CONS 0,6 MW y OCR 1,3 MW; B2 no la publica.
p = base()
p.pasada("Lascar", "2026-05-03 05:00", "pos", {"K": True, "B0": True, "B1": True, "B2": False, "B3": True},
         vrp_mirova=0.6, ocr_vrp=1.3)
informar("E2 protegida SOLO por el OCR en T (CONS 0,6 / OCR 1,3); B2 no la publica",
         "programa 2 y A119: en T decide la tabla sola, no es protegida en T; B2 deberia seguir elegible (pierde "
         "una baja, no una protegida)", correr("E2", p))

# E3: una protegida en O con error en el brazo K y otra con grilla incompleta.
p = base()
p.pasada("Lascar", "2026-07-30 05:00", "pos", todos(), vrp_mirova=2.0, k_error=True)
p.pasada("Lascar", "2026-07-31 05:00", "pos", todos(), vrp_mirova=2.0, grilla_incompleta=True)
informar("E3 una protegida con error de K y otra con grilla incompleta",
         "las dos en protegidas SIN DATO y en SIN DATO, no en no observadas", correr("E3", p))

# E4: control positivo del analizador en 0 (ninguna protegida de PCC perdida por B0).
p = base()
informar("E4 control positivo del analizador en 0 (B0 no pierde ninguna de PCC)",
         "7: el instrumento no ve la ROI: no deberia imprimirse veredicto", correr("E4", p))

# E5: B2 y B3 GANAN contra B1 (apagan 6 negativos que B1 publica); B2 ademas pierde 2 bajas (E mayor).
p = base()
for n in range(6):
    p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio",
             {"K": False, "B0": True, "B1": True, "B2": False, "B3": False})
for n in range(2):
    p.pasada("Lascar", f"2026-09-{20 + n:02d} 05:00", "pos",
             {"K": True, "B0": True, "B1": True, "B2": False, "B3": True}, vrp_mirova=0.4)
informar("E5 B2 y B3 GANAN contra B1; B2 con mas E", "6.2: el de menor E en T u O: B3", correr("E5", p))

# E6: B2 GANA en el canal todo pero PIERDE en el canal tabla (los negativos que apaga... no: las bajas que pierde son
# de la tabla y los negativos que apaga son de noches cuya alerta... ). Version simple: B2 apaga 6 negativos de B1
# (gana en los dos canales) y pierde 6 bajas que solo el OCR trae en O (no cuentan en tabla). Que decide el codigo?
p = base()
for n in range(6):
    p.pasada("Lascar", f"2026-09-{10 + n:02d} 05:00", "neg_limpio",
             {"K": False, "B0": True, "B1": True, "B2": False, "B3": True})
for n in range(6):
    p.pasada("Lascar", f"2026-09-{20 + n:02d} 05:00", "pos",
             {"K": True, "B0": True, "B1": True, "B2": False, "B3": True}, tabla=False, ocr_vrp=0.4)
informar("E6 B2 apaga 6 negativos de B1 y pierde 6 bajas que solo el OCR trae (O)",
         "con todo: neto 0 (EMPATE); con la tabla sola: GANA. 6.2 no dice que canal decide", correr("E6", p))

# E7: un negativo limpio cuyo brazo K vino con record None (calculate_vrp devuelve None con ROI vacia,
# process_viirs_mod.py:541-542, o el store no escribe, probe_n.guardar_como_store). En N fue 0 de 510, pero el run tiene
# ~6.900. Que hace el analizador con una sola?
p = base()
p.pasada("Lascar", "2026-08-25 05:00", "neg_limpio", todos(b=False, k=False))
p.res[-1]["brazos"]["K"] = {"record": None, "pc_pix": [], "segundos": 1.0, "contadores": None}
informar("E7 un negativo con record de K = None (ROI vacia o store sin escribir)",
         "la pasada deberia quedar SIN DATO para K y el resto seguir; el analizador no deberia caerse", correr("E7", p))

(a.dest / "mutaciones_salida.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
