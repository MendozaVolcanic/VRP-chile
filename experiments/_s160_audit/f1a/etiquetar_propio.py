# -*- coding: utf-8 -*-
"""F1a, H1b: reimplementacion INDEPENDIENTE del etiquetador de `scripts/banco_paridad.py::etiquetar` (y de la
alerta protegida de `scripts/clase_mirova.py`) y comparacion etiqueta por etiqueta sobre las ventanas de K.

NO importa banco_paridad, clase_mirova, evaluar ni referencia_mirova_unificada. Lee los CSV congelados con csv,
normaliza por su cuenta (los 11 nombres y los 3 sensores de los CSV, leidos en esta sesion), une las cuatro capas
(CONS principal gana, luego OCR, luego historico, luego respaldo; dentro de un archivo gana la Ultima_Actualizacion
mas nueva), parea a +-120 s por (volcan, sensor) y etiqueta con las reglas escritas en banco_paridad.py l. 300-333
(leidas, no copiadas: se reescriben desde la definicion del docstring y de la spec):
  pos          alguna fila de alerta (ALERTA_TERMICA o ALERTA_TERMICA_OCR; ALERTA_SIN_GEOMETRIA_OCR no es alerta)
  far_ref      si no, alguna fila FALSO_POSITIVO*
  neg_limpio   si no, una fila CONS RUTINA con VRP 0 en la pasada Y la noche UTC de ese volcan y sensor sin alerta ni FP
  sin_geometria si no, alguna fila sin geometria y ninguna RUTINA
  sin_info     el resto
  protegida A  alguna fila de alerta con VRP >= 1; B: alguna fila no RUTINA con VRP >= 1
  vrp_ref      VRP de la alerta CONS si la hay, si no de la OCR
El universo de pasadas (nuestras pasadas nocturnas) se toma de la tabla del evaluador (`t_C0_K.json`): el filtro
nocturno NO se reimplementa (queda declarado). Las filas de referencia tampoco se filtran por noche: a +-120 s la
elevacion solar es la misma que la de nuestra pasada.

Las dos preguntas: (1) si banco_paridad etiquetara mal, lo veria: las etiquetas se comparan pasada por pasada y se
listan las distintas; (2) si esta reimplementacion estuviera muerta (por ejemplo, no pareara nada) todo saldria
sin_info y la comparacion lo mostraria. Control positivo: la misma reimplementacion con tolerancia 0 s tiene que
producir diferencias (se imprimen).
Uso: python etiquetar_propio.py <congelado_dir> <t_C0_K.json> <desde> <hasta> <solo_tabla si|no> <prot.json>
  <prot.json> = salida de evaluar_fk.proteccion volcada por quien llama (comparacion de protegidas).
"""
import csv, json, sys, bisect, collections
from datetime import datetime, timedelta
from pathlib import Path

VOL = {"lascar": "Lascar", "lastarria": "Lastarria", "isluga": "Isluga", "tupungatito": "Tupungatito",
       "planchonpeteroa": "PlanchonPeteroa", "planchon-peteroa": "PlanchonPeteroa", "peteroa": "PlanchonPeteroa",
       "nevados de chillan": "NevadosDeChillan", "nevadosdechillan": "NevadosDeChillan", "llaima": "Llaima",
       "villarrica": "Villarrica", "copahue": "Copahue", "puyehue-cordon caulle": "PuyehueCordonCaulle",
       "puyehuecordoncaulle": "PuyehueCordonCaulle", "chaiten": "Chaiten"}
TOL = int(sys.argv[7]) if len(sys.argv) > 7 else 120


def sensor(s):
    s = (s or "").strip().upper()
    if "MODIS" in s: return "MODIS"
    if "375" in s: return "VIIRS375"
    if "VIIRS" in s: return "VIIRS750"
    return s


def f(v):
    try: return float(str(v).strip())
    except (TypeError, ValueError): return None


def leer(path, source):
    por_clave = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        vol = VOL.get((r.get("Volcan") or "").strip().lower())
        fecha = (r.get("Fecha_Satelite_UTC") or "").strip()
        if vol is None or len(fecha) < 16: continue
        tipo = (r.get("Tipo_Registro") or "").strip()
        sin_geo = source == "OCR" and (tipo == "ALERTA_SIN_GEOMETRIA_OCR" or (tipo.startswith("ALERTA") and (
            (r.get("Metodo_Validacion") or "").strip() == "vrp_sin_geometria_propia" or (r.get("Clasificacion Mirova") or "").strip() == "SIN_GEOMETRIA")))
        fila = {"vol": vol, "b": sensor(r.get("Sensor")), "fecha": fecha, "source": source,
                "tipo": "ALERTA_SIN_GEOMETRIA_OCR" if sin_geo else tipo, "vrp": f(r.get("VRP_MW")),
                "upd": (r.get("Ultima_Actualizacion") or "").strip(), "sin_geo": sin_geo}
        k = (vol, fila["b"], fecha[:16], source)
        prev = por_clave.get(k)
        if prev is None or fila["upd"] > prev["upd"]: por_clave[k] = fila
    return por_clave


def referencia(d, solo_tabla):
    d = Path(d)
    filas = leer(d / "registro_vrp_consolidado.csv", "CONS")
    if not solo_tabla:
        for k, v in leer(d / "registro_vrp_ocr.csv", "OCR").items(): filas.setdefault(k, v)
    for nombre in ("consolidado_filas_perdidas.csv", "respaldo_20260408.csv"):
        if (d / nombre).exists():
            for k, v in leer(d / nombre, "CONS").items(): filas.setdefault(k, v)
    return list(filas.values())


def es_alerta(t): return t.startswith("ALERTA") and t != "ALERTA_SIN_GEOMETRIA_OCR"


def main():
    cong, tabla, desde, hasta, solo_tabla, protjson = sys.argv[1:7]
    filas = referencia(cong, solo_tabla == "si")
    por_vb = collections.defaultdict(list); noche = collections.defaultdict(lambda: {"al": False, "fp": False})
    for x in filas:
        dia = x["fecha"][:10]
        if not (desde <= dia <= hasta): continue
        dt = datetime.strptime(x["fecha"][:19], "%Y-%m-%d %H:%M:%S")
        por_vb[(x["vol"], x["b"])].append((dt, x))
        n = noche[(x["vol"], x["b"], dia)]
        n["al"] |= es_alerta(x["tipo"]); n["fp"] |= x["tipo"].startswith("FALSO_POSITIVO")
    for v in por_vb.values(): v.sort(key=lambda z: z[0])
    T = json.load(open(tabla, encoding="utf-8"))["pasadas"]
    prot_ev = json.load(open(protjson, encoding="utf-8"))
    dif = collections.Counter(); ejemplos = []; n = 0; mio_c = collections.Counter(); pd = collections.Counter()
    for k, v in T.items():
        if "control" not in v: continue
        vol, b, t = k.split("|"); dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
        lista = por_vb.get((vol, b), []); ts = [z[0] for z in lista]
        i = bisect.bisect_left(ts, dt - timedelta(seconds=TOL)); ff = []
        while i < len(lista) and lista[i][0] <= dt + timedelta(seconds=TOL): ff.append(lista[i][1]); i += 1
        al = [x for x in ff if es_alerta(x["tipo"])]
        nn = noche.get((vol, b, t[:10]), {"al": False, "fp": False})
        if al: lab = "pos"
        elif any(x["tipo"].startswith("FALSO_POSITIVO") for x in ff): lab = "far_ref"
        elif any(x["tipo"] == "RUTINA" and x["source"] == "CONS" and (x["vrp"] or 0) == 0 for x in ff) and not nn["al"] and not nn["fp"]: lab = "neg_limpio"
        elif any(x["sin_geo"] for x in ff) and not any(x["tipo"] == "RUTINA" for x in ff): lab = "sin_geometria"
        else: lab = "sin_info"
        pa = any(es_alerta(x["tipo"]) and x["tipo"] != "ALERTA_SIN_GEOMETRIA_OCR" and (x["vrp"] or 0) >= 1.0 for x in ff)
        pb = any(x["tipo"] != "RUTINA" and (x["vrp"] or 0) >= 1.0 for x in ff)
        al.sort(key=lambda x: x["source"] != "CONS"); vref = al[0]["vrp"] if al else None
        n += 1; mio_c[lab] += 1
        c = v["control"]
        if lab != c["lab"]:
            dif["lab"] += 1; ejemplos.append((k, "mio", lab, "bp", c["lab"]))
        if (vref != c.get("vrp_ref")) and lab == "pos": dif["vrp_ref"] += 1; ejemplos.append((k, "vrp_ref mio", vref, "bp", c.get("vrp_ref")))
        pe = prot_ev.get(k, {})
        if pa != pe.get("A"): dif["prot_A"] += 1; ejemplos.append((k, "prot_A mio", pa, "ev", pe.get("A")))
        if pb != pe.get("B"): dif["prot_B"] += 1; ejemplos.append((k, "prot_B mio", pb, "ev", pe.get("B")))
        pd["A"] += pa; pd["B"] += pb
    print("pasadas comparadas %d | tolerancia %d s | solo_tabla %s | etiquetas mias %s | protegidas mias A %d B %d" % (n, TOL, solo_tabla, dict(mio_c), pd["A"], pd["B"]))
    print("diferencias:", dict(dif) or "ninguna")
    for e in ejemplos[:15]: print("   ", e)


if __name__ == "__main__":
    main()
