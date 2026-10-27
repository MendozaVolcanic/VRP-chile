# -*- coding: utf-8 -*-
"""Verificador v3: escenarios sintéticos que la batería sellada NO tiene, corridos contra el analizador v3 tal cual y,
donde corresponde, contra una copia rota a mano (para mostrar que el escenario sí distingue).

POR QUÉ. La batería de 11 escenarios no tiene ningún brazo que GANE con el canal que decide y sea peor con la tabla
sola (§6.2, segunda condición), ninguno peor con el canal que decide pero no peor con la tabla sola (§6.3, primera
condición), ningún empate de E entre dos ganadores (§6.2, desempate) y ningún archivo de pasadas sin gránulo (VB2-07).
Cada escenario de acá predice lo que la regla ESCRITA (PREREGISTRO_V750B.md §6) da y mira lo que el código da.

Pregunta 1: si la regla estuviera rota en ese punto, ¿se ve? Para S1 y S2 se corre además el analizador con la
condición quitada (mutaciones M2 y M3 de mutar_v3.py): si la ROI cambia, el escenario mide ese punto.
Pregunta 2: si el analizador no imprime «ROI elegida», el escenario queda SIN DATO (None), no «ok».

Las poblaciones se arman con las mismas piezas que la batería sellada (copiadas tal cual; la batería ejecuta sus
escenarios al importarse y no se puede importar como módulo). Uso:
  python escenarios_v3.py --arbol <árbol limpio> --dest <tmp>
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
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

    def pasada(self, volcan, hora, lab, pubs, vrp_mirova=None, ocr_vrp=None, tabla=True):
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
            "z": 30.0, "pub_prod": bool(pubs["K"]), "dc": "summit" if pubs["K"] else None,
            "pc_vrp": 0.5 if pubs["K"] else 0.0, "pc_n": 1 if pubs["K"] else None, "granule": f"g{i}",
            "en_sc": False, "celda_crater": CELDA[volcan], "inner_km": INNER[volcan]})
        kb = {"record": k_record(pubs["K"]), "pc_pix": [[10, 10]] if pubs["K"] else []}
        r = {"id": i, "volcan": volcan, "hora_utc": hora, "estado": "ok", "dayflag": 0, "sunglint": 40.0,
             "brazos": {"K": kb}, "cobertura": COB,
             "oraculo": {b: (PUB if pubs.get(b, pubs["B0"]) else NOPUB) for b in ("B0", "B1", "B2", "B3", "B5")}}
        self.res.append(r)

    def escribir(self, d):
        (d / "art").mkdir(parents=True, exist_ok=True)
        (d / "art" / "resultados_00.json").write_text(json.dumps(self.res), encoding="utf-8")
        (d / "objetivos.json").write_text(json.dumps(self.objs), encoding="utf-8")


def todos(k=True, b=True):
    return {"K": k, "B0": b, "B1": b, "B2": b, "B3": b}


def base():
    """La misma población base de la batería sellada v3 (3 protegidas de Cordón Caulle que B0 y B5 pierden)."""
    p = Pob()
    for n in range(3):
        p.pasada("PuyehueCordonCaulle", f"2026-09-0{1 + n} 05:00", "pos",
                 {"K": True, "B0": False, "B1": True, "B2": True, "B3": True, "B5": False}, vrp_mirova=1.2)
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


def correr(nombre, p, analizar=ANALIZAR, extra=(), sin_granulo=None, pruebas=True):
    """pruebas: pasa --censo-omitido-solo-pruebas (como la batería sellada; sin censo la compuerta cierra por el censo y
    el escenario no mide la regla; primera corrida de este script: S1 a S3 salieron rc 3 por eso, SIN DATO)."""
    d = a.dest / nombre
    if d.exists():
        shutil.rmtree(d)
    p.escribir(d)
    cmd = [sys.executable, str(analizar), "--art", str(d / "art"), "--objetivos", str(d / "objetivos.json"),
           "--evaluador", str(EVAL), "--salida", str(d / "salida.txt"), *extra]
    if pruebas and "--censo-omitido-solo-pruebas" not in cmd:
        cmd.append("--censo-omitido-solo-pruebas")
    if sin_granulo is not None:
        (d / "sin_granulo.json").write_text(json.dumps(sin_granulo), encoding="utf-8")
        cmd += ["--sin-granulo", str(d / "sin_granulo.json")]
    o = subprocess.run(cmd, capture_output=True, text=True, cwd=str(A), timeout=600, encoding="utf-8",
                       errors="replace")
    txt = o.stdout + o.stderr
    (d / "stdout.txt").write_text(txt, encoding="utf-8")
    roi = re.search(r"ROI elegida: (\S+) \((.*?)\)", txt)
    comp = re.search(r"compuerta del veredicto.*?: (ABIERTA|CERRADA)(.*)", txt)
    def bloque_p2(cabecera):
        """Sólo las líneas de ESE bloque (hasta el siguiente «== ventana»); la primera versión de este script seguía
        hasta el final y se quedaba con el último bloque, «TO, canal todo», para los dos canales."""
        ini = txt.rfind(cabecera)
        if ini < 0:
            return {}
        fin = txt.find("\n== ventana", ini + 1)
        trozo = txt[ini:fin if fin > 0 else None]
        return {m.group(1): f"{m.group(2).strip()} neto {m.group(3)} B {m.group(4)}" for m in
                re.finditer(r"^\s+(B\d)\s+prot.*?P2 contra B1: ([A-Z ]+?) \(neto (-?\d+), bloques (\d+)", trozo, re.M)}
    p2, p2t = bloque_p2("== ventana TO, canal decide"), bloque_p2("== ventana TO, canal tabla")
    eleg = re.search(r"6\.1 elegibles.*?:\s*(\[.*?\])", txt)
    marcas = re.findall(r"\[(SIN CENSO, NO VALE PARA EL RUN|LEÍDO CON FALTANTES: [^\]]*)\]", txt)
    cob = re.search(r"== cobertura: (SUFICIENTE|INSUFICIENTE)", txt)
    sg = re.search(r"pasadas sin gránulo \(del generador, (.*?)\): (\d+)", txt)
    return {"rc": o.returncode, "roi": roi.group(1) if roi else None, "motivo": roi.group(2) if roi else None,
            "compuerta": comp.group(1) if comp else None, "p2_decide": p2, "p2_tabla": p2t,
            "marcas": sorted(set(marcas)), "cobertura": cob.group(1) if cob else None,
            "elegibles": eleg.group(1) if eleg else None,
            "sin_granulo": (sg.group(1), sg.group(2)) if sg else None}


def mutante(nombre, viejo, nuevo):
    """Copia del analizador con UNA línea cambiada, en la misma carpeta (para que resuelva sus imports igual)."""
    src = ANALIZAR.read_text(encoding="utf-8")
    assert src.count(viejo) == 1, (nombre, src.count(viejo))
    f = ANALIZAR.with_name(f"analizar_v750b_{nombre}.py")
    f.write_text(src.replace(viejo, nuevo), encoding="utf-8")
    return f


OUT = []


def informar(nombre, esperado, r, campos=("rc", "roi", "motivo", "elegibles", "compuerta", "marcas", "cobertura",
                                             "sin_granulo", "p2_decide", "p2_tabla")):
    s = f"\n== {nombre}\n   regla escrita (§6 / §9): {esperado}\n" + "\n".join(f"   {k}: {r[k]}" for k in campos)
    print(s, flush=True)
    OUT.append(s)


# ------------------------------------------------------------------ S1: GANA con el canal que decide, PIERDE con la tabla
# B2 publica 15 bajas que sólo el OCR trae (O) y que B1 no publica (15 bloques a favor, sólo en «todo»), y publica 6
# negativos limpios que B1 no publica (6 bloques en contra, en los dos canales). Con todo: neto -9 en 21 bloques
# (sorteos); con la tabla sola: neto +6 en 6 bloques, p = 1/64: PIERDE. §6.2: B2 NO gana (es peor con la tabla sola);
# §6.3: tampoco entra. ROI esperada: B4 (= B0 = B1 en Láscar en estas pasadas).
p = base()
for n in range(15):
    p.pasada("Lascar", f"2026-09-{1 + n:02d} 05:00", "pos", {**todos(), "B1": False, "B0": False, "B3": False, "B5": False, "B2": True},
             tabla=False, ocr_vrp=0.4)
for n in range(6):
    p.pasada("Lascar", f"2026-09-{20 + n:02d} 05:00", "neg_limpio", {**todos(b=False, k=False), "B2": True})
r = correr("S1", p)
informar("S1 B2 GANA con el canal que decide y PIERDE con la tabla sola",
         "§6.2 exige «no peor con la tabla sola»: B2 no gana ni entra a §6.3; ROI = B4", r)
m2 = mutante("M2", 'ver[(b, "TO", "decide")][1] == "GANA" and no_peor(b, "tabla")]', 'ver[(b, "TO", "decide")][1] == "GANA"]')
informar("S1 con la condición de la tabla quitada de §6.2 (mutación M2)", "si la ROI cambia a B2, S1 mide esa condición",
         correr("S1_M2", p, analizar=m2), campos=("rc", "roi", "motivo"))

# ------------------------------------------------------------------ S2: peor con el canal que decide, no peor con la tabla
# B0 (y por tanto B4 en Láscar) no publica 4 bajas que sólo el OCR trae: con todo, SIN SUSTRATO con neto +4 (en contra);
# con la tabla sola, 0 bloques (neto 0). §6.3 v3: B4 no entra (peor con el canal que decide); el siguiente de PREF que no
# es peor es B2 (= B1 acá). ROI esperada: B2.
p = base()
for n in range(4):
    p.pasada("Lascar", f"2026-09-{1 + n:02d} 05:00", "pos", {**todos(), "B0": False, "B5": False}, tabla=False, ocr_vrp=0.4)
r = correr("S2", p)
informar("S2 B4 (= B0 en Láscar) peor con el canal que decide (SIN SUSTRATO, neto +4) y neto 0 con la tabla sola",
         "§6.3 exige no peor en los dos canales: B4 no entra; ROI = B2", r)
m3 = mutante("M3", '(b == "B1" or (no_peor(b, "decide") and no_peor(b, "tabla")))]', '(b == "B1" or no_peor(b, "tabla"))]')
informar("S2 con la condición del canal que decide quitada de §6.3 (mutación M3)", "si la ROI cambia a B4, S2 mide esa condición",
         correr("S2_M3", p, analizar=m3), campos=("rc", "roi", "motivo"))

# ------------------------------------------------------------------ S3: dos ganadores con el mismo E
# B3 y B0 (B4 en Láscar) apagan los mismos 6 negativos que B1 publica: los dos GANAN (p = 1/64) con E idéntico. §6.2
# dice «si ganan dos o más, el de menor E» y no dice qué pasa a igual E. B0 no es elegible (pierde las 3 de PCC).
p = base()
for n in range(6):
    p.pasada("Lascar", f"2026-09-{1 + n:02d} 05:00", "neg_limpio", {**todos(b=False, k=False), "B1": True, "B2": True, "B5": True})
r = correr("S3", p)
informar("S3 B3 y B4 GANAN con el mismo E (B2 y B5 iguales a B1)",
         "§6.2 no escribe el desempate a igual E; por cercanía al .m (§6.3) sería B4; el código toma min() sobre el orden de CANDIDATOS", r)

# ------------------------------------------------------------------ S4: pasadas sin gránulo (VB2-07)
# La misma base, más un archivo de pasadas sin gránulo con una protegida: §9 dice que una protegida ahí frena la lectura.
p = base()
r = correr("S4a", p, sin_granulo=[{"volcan": "Lascar", "hora_utc": "2026-07-01 05:00", "lab": "pos", "protegida": True}])
informar("S4a archivo de pasadas sin gránulo con UNA protegida", "§9: cobertura INSUFICIENTE, sin veredicto, rc 3", r,
         campos=("rc", "roi", "compuerta", "cobertura", "sin_granulo"))
r = correr("S4b", p, extra=["--sin-granulo", str(a.dest / "no_existe.json"), "--censo-omitido-solo-pruebas"])
informar("S4b la ruta del archivo de pasadas sin gránulo NO existe", "¿qué hace el analizador con un archivo ausente?", r,
         campos=("rc", "roi", "compuerta", "cobertura", "sin_granulo", "marcas"))
# 2 % del denominador: con 41 objetivos, 1 sin gránulo no protegida es el 2,4 %: cobertura INSUFICIENTE; se mira que el
# archivo cuente en el numerador y el denominador (len(sin) + len(sin_g) <= 0,02 * (len(obj) + len(sin_g) - fuera))
r = correr("S4c", p, sin_granulo=[{"volcan": "Lascar", "hora_utc": "2026-07-01 05:00", "lab": "neg_limpio", "protegida": False}])
informar("S4c una pasada sin gránulo NO protegida sobre 41 objetivos (1/42 = 2,4 % > 2 %)", "§9: cobertura INSUFICIENTE, rc 3", r,
         campos=("rc", "roi", "compuerta", "cobertura", "sin_granulo"))

# ------------------------------------------------------------------ S5: las banderas de la compuerta
p = base()
r = correr("S5a", p, extra=["--leer-con-faltantes", "prueba del verificador v3"], pruebas=False)
informar("S5a sin censo, con --leer-con-faltantes (sin la bandera de pruebas)",
         "§9: la bandera cubre «el control del censo no se puede correr»: veredicto marcado LEÍDO CON FALTANTES, rc 5", r,
         campos=("rc", "roi", "compuerta", "marcas"))
r = correr("S5b", p, extra=["--leer-con-faltantes", "prueba", "--censo-omitido-solo-pruebas"])
informar("S5b las dos banderas a la vez (sin censo)", "las dos marcas en la línea de la ROI; rc 4 o 5 (el código elige 4)", r,
         campos=("rc", "roi", "compuerta", "marcas"))
informar("S5c --solo-controles con la compuerta cerrada (sin censo ni banderas que lo cubran)",
         "sin veredicto; ¿qué código de salida?", correr("S5c", p, extra=["--solo-controles"], pruebas=False), campos=("rc", "roi", "compuerta"))
# censo dado pero vacío (ninguna pasada común): censo_ok = bool(cnt) and ... = False: SIN DATO del censo, no OK
r = correr("S5d", p, extra=["--censo-art", str(a.dest / "censo_vacio"), "--censo-objetivos", str(a.dest / "censo_vacio_obj.json")], pruebas=False)
informar("S5d censo con 0 pasadas comunes (carpeta vacía, objetivos vacíos)", "censo FALLA (bool(cnt) exige al menos una), rc 3", r,
         campos=("rc", "roi", "compuerta"))

# ------------------------------------------------------------------ S5e y S5f: lo que --leer-con-faltantes NO debe cubrir
# S5e: oráculo muerto (la población V6 de la batería) con las dos banderas: el control positivo de la ROI tiene que seguir
# cerrando la compuerta (§9 dice que la bandera cubre cobertura y censo, nada más).
p = Pob()
muerto = {"K": True, "B0": False, "B1": False, "B2": False, "B3": False, "B5": False}
for n in range(3):
    p.pasada("PuyehueCordonCaulle", f"2026-09-0{1 + n} 05:00", "pos", muerto, vrp_mirova=1.2)
for n in range(6):
    p.pasada("Lascar", f"2026-07-{10 + n:02d} 05:00", "pos", muerto, vrp_mirova=1.5)
for n in range(10):
    p.pasada("Lascar", f"2026-04-{10 + n:02d} 05:00", "neg_limpio", todos(b=False, k=False))
r = correr("S5e", p, extra=["--leer-con-faltantes", "prueba", "--censo-omitido-solo-pruebas"])
informar("S5e oráculo muerto con las dos banderas", "§9: las banderas no cubren el control de la ROI: CERRADA, rc 3", r,
         campos=("rc", "roi", "compuerta", "marcas"))
# S5f: K distinta de producción en 1 pasada de 41 (2,4 % > 1 %) con las dos banderas: K = producción cierra igual.
p = base()
p.objs[5]["pub_prod"] = False          # producción no publicó esa protegida de Láscar; el brazo K del run sí
r = correr("S5f", p, extra=["--leer-con-faltantes", "prueba", "--censo-omitido-solo-pruebas"])
informar("S5f K distinta de producción en 1 de 41 (y es protegida) con las dos banderas",
         "§7 y §9: K = producción no lo cubre ninguna bandera: CERRADA, rc 3", r, campos=("rc", "roi", "compuerta", "marcas"))

(a.dest / "escenarios_v3_salida.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")
for f in ANALIZAR.parent.glob("analizar_v750b_M*.py"):
    f.unlink()
