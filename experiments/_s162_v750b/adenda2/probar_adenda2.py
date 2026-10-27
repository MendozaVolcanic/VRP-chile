# -*- coding: utf-8 -*-
"""Prueba de la adenda 2 de V750-B (S162, relevo VIIRS 750): diagnóstico de posición y lista suplementaria.

POR QUÉ. El lector de posición (`leer_posicion_v750b.py`) reusa el record y las métricas del analizador sellado y
sólo cambia el punto desde donde se mide la distancia. Si eso estuviera mal, el diagnóstico diría que una regla de
posición pierde o salva alertas que no pierde ni salva. Cada escenario arma resultados sintéticos con el formato del
probe y comprueba un solo resultado; la batería sale 1 si alguno no coincide.

Escenas (grilla 67 x 67, celda 0,75 km, cráter en la celda (33, 33), radio interior 5 km = 6,67 celdas):
  LEJANA   un alertado débil junto al cráter (33, 34) y un cúmulo brillante a 13 km (33, 50)-(33, 51):
           radiante y pico lo ponen lejos (calla), cercano junto al cráter (publica).
  BORDE    un cúmulo (33, 37)-(33, 40) con el píxel más brillante en el extremo: centroide a 4,1 km (radiante
           publica), pico a 5,25 km (calla), cercano a 3 km (publica).
  UNO      un solo alertado junto al cráter: los tres brazos coinciden (C1).
Escenarios:
  P1  protegida con LEJANA: radiante y pico la pierden (P1 = 1), cercano no (P1 = 0); y cambia contra radiante.
  P2  protegida con BORDE: pico la pierde, radiante y cercano no.
  P3  negativo limpio con LEJANA: cercano lo publica (E_neg 1), radiante y pico no.
  P4  far_ref con LEJANA y el cráter 2,25 km al W del centro de la grilla (como en los volcanes reales, donde no
      coinciden): cercano publica en la pasada lejana (1), radiante y pico no (0); y la distancia medida desde el
      CENTRO (desde donde mide MIROVA) calza con la de MIROVA para radiante y pico, no para cercano; medida desde el
      cráter no calzaría (15,4 km contra 13,1).
  P5  controles en verde con datos sanos (salida 0); C1 cuenta casos.
  P6  lista suplementaria con el archivo sin gránulo de otra lista: C3 cae, salida 3, NO LEGIBLE.
  P7  analizador distinto del sellado (una línea cambiada): C4 cae, salida 3.
  P8  separar_resultados: el analizador sellado da la MISMA salida (byte a byte) sobre los resultados sin la
      suplementaria que sobre la parte sellada de los resultados con ella.
  P9  el generador cambia el filtro de etiquetas sólo si aparece una vez: con 0 o 2 apariciones se niega.
Uso: python probar_adenda2.py --evaluador <evaluar_d25.py del tag s161-d25-lectura> [--lector <ruta>] [--dest <tmp>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
V750B = AQUI.parent
ANALIZAR = V750B / "analizar_v750b.py"
SENSOR = "VIIRS_SNPP_750"
CAJAS = ("B0", "B1", "B2", "B3", "B5")
COB = {"nan_67": 0, "nan_21": 0, "nan_7": 0, "nan_centro": False, "nan_7_crater": 0, "nan_crater": False}


def caja(pix):
    """pix: [(fila, columna, M13)]. Devuelve la caja del oráculo con el formato del probe."""
    if not pix:
        return {"motivo_vacio": None, "n_abs": 0, "n_p1": 0, "n_p2": 0, "npix": 0, "vrp_mw": None, "pixeles": []}
    return {"motivo_vacio": None, "n_abs": 0, "n_p1": len(pix), "n_p2": 0, "npix": len(pix), "vrp_mw": 0.5,
            "pixeles": [[f, c, 2, round(((f - 33) ** 2 + (c - 33) ** 2) ** 0.5 * 0.75, 2), m] for f, c, m in pix]}


LEJANA = [(33, 34, 0.9), (33, 50, 5.0), (33, 51, 4.0)]
BORDE = [(33, 37, 0.9), (33, 38, 0.9), (33, 39, 0.9), (33, 40, 3.0)]
UNO = [(33, 34, 0.9)]


def k_record():
    return {"primary_cluster": None, "distance_class": None, "vrp_mw": 0.0, "vrp_mir_mw": 0.0,
            "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None, "t_max_k": 290.0,
            "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}


class Pob:
    def __init__(self):
        self.sell, self.supl, self.res = [], [], []

    def pasada(self, hora, lab, pix, vrp_mirova=0.0, volcan="Lascar", dist_mirova=None, crater=(33.0, 33.0)):
        supl = lab == "far_ref"
        lista = self.supl if supl else self.sell
        i = (100000 if supl else 0) + len(lista)
        if lab == "pos":
            filas = [{"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA", "vrp_mw": vrp_mirova,
                      "dist_km": dist_mirova, "source": "CONS"}]
        elif lab == "far_ref":
            filas = [{"fecha_utc": hora + ":00", "tipo": "FALSO_POSITIVO", "vrp_mw": vrp_mirova,
                      "dist_km": dist_mirova, "source": "CONS"}]
        else:
            filas = [{"fecha_utc": hora + ":00", "tipo": "RUTINA", "vrp_mw": 0.0, "dist_km": None, "source": "CONS"}]
        o = {"id": i, "volcan": volcan, "hora_utc": hora, "sensor": SENSOR, "lab": lab,
             "protegida": lab == "pos" and vrp_mirova >= 1.0, "alerta_tabla": lab == "pos", "decide": True,
             "mirova": filas, "mirova_vrp": vrp_mirova, "z": 30.0, "pub_prod": False, "dc": None, "pc_vrp": 0.0,
             "pc_n": None, "granule": f"g{i}", "en_sc": False, "celda_crater": [int(x) for x in crater],
             "pos_crater": list(crater),
             "inner_km": 5.0}
        if supl:
            o["dist_ref"] = dist_mirova
        lista.append(o)
        self.res.append({"id": i, "volcan": volcan, "hora_utc": hora, "estado": "ok", "dayflag": 0, "sunglint": 40.0,
                         "cobertura": COB, "brazos": {"K": {"record": k_record(), "pc_pix": []}},
                         "oraculo": {b: caja(pix) for b in CAJAS}})
        return i

    def escribir(self, d, sg_ajeno=False, con_supl=True):
        (d / "art").mkdir(parents=True, exist_ok=True)
        res = self.res if con_supl else [r for r in self.res if r["id"] < 100000]
        (d / "art" / "resultados_00.json").write_text(json.dumps(res), encoding="utf-8")
        ts = json.dumps(self.sell)
        (d / "objetivos.json").write_text(ts, encoding="utf-8")
        (d / "sin_granulo.json").write_text(json.dumps(
            {"objetivos_sha256": hashlib.sha256(ts.encode("utf-8")).hexdigest(), "pasadas": []}), encoding="utf-8")
        tp = json.dumps(self.supl)
        (d / "supl.json").write_text(tp, encoding="utf-8")
        (d / "sin_granulo_supl.json").write_text(json.dumps(
            {"objetivos_sha256": "0" * 64 if sg_ajeno else hashlib.sha256(tp.encode("utf-8")).hexdigest(),
             "pasadas": []}), encoding="utf-8")


def poblacion():
    p = Pob()
    for n in range(12):                        # negativos limpios sin nada: dan sustrato a los controles
        p.pasada(f"2026-04-{1 + n:02d} 05:00", "neg_limpio", [])
    for n in range(3):                         # alertas sanas, un solo alertado: casos de C1 y de C2
        p.pasada(f"2026-05-{1 + n:02d} 05:00", "pos", UNO, 0.4, dist_mirova=0.8)
    ids = {"P1": p.pasada("2026-07-01 05:00", "pos", LEJANA, 2.0, dist_mirova=0.8),
           "P2": p.pasada("2026-07-02 05:00", "pos", BORDE, 2.0, dist_mirova=4.0),
           "P3": p.pasada("2026-07-03 05:00", "neg_limpio", LEJANA),
           "P4": p.pasada("2026-07-04 05:00", "far_ref", LEJANA, 3.0, dist_mirova=13.1, crater=(33.0, 30.0))}
    return p, ids


def correr(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def lector(ruta, d, ev, analizador=None):
    cmd = [sys.executable, str(ruta), "--art", str(d / "art"), "--objetivos", str(d / "objetivos.json"),
           "--objetivos-supl", str(d / "supl.json"), "--sin-granulo-supl", str(d / "sin_granulo_supl.json"),
           "--evaluador", str(ev), "--salida", str(d / "lector.txt")]
    if analizador:
        cmd += ["--analizador", str(analizador)]
    return correr(cmd)


def linea(out, caja_, brazo):
    m = re.search(rf"^   {caja_} {brazo}\s+prot\s+(\d+) P1\s+(\d+) \| E\s+(\d+) \(bajas sin publicar (\d+) de (\d+), "
                  rf"neg publicados (\d+) de (\d+)\)(.*)$", out, re.M)
    return None if m is None else {"prot": int(m.group(1)), "P1": int(m.group(2)), "E": int(m.group(3)),
                                   "E_neg": int(m.group(6)), "resto": m.group(8)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--evaluador", required=True)
    ap.add_argument("--lector", default=str(AQUI / "leer_posicion_v750b.py"))
    ap.add_argument("--dest", default="")
    a = ap.parse_args()
    dest = Path(a.dest) if a.dest else Path(tempfile.mkdtemp(prefix="adenda2_"))
    filas, fallas, caidas = [], [], []

    def chequear(nombre, cond, detalle):
        filas.append(f"{'OK   ' if cond else 'FALLA'} {nombre}: {detalle}")
        if not cond:
            fallas.append(nombre)

    def esc(nombre):
        d = dest / nombre
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        return d

    # P1 a P5: población sana
    p, ids = poblacion()
    d = esc("sana")
    p.escribir(d)
    rc, out = lector(a.lector, d, a.evaluador)
    if "Traceback" in out:
        caidas.append("sana")
    chequear("P5 controles en verde y salida 0", rc == 0 and "controles C1 a C4: EN VERDE" in out,
             f"salida {rc}: " + (out[-400:].replace("\n", " | ") if rc else ""))
    m1 = re.search(r"C1 cajas con un solo alertado: (\d+); con brazos distintos (\d+)", out)
    chequear("P5 C1 cuenta casos y ninguno distinto", bool(m1) and int(m1.group(1)) >= 3 and m1.group(2) == "0",
             m1.group(0) if m1 else "sin línea C1")
    r, c, k = (linea(out, "B0", b) for b in ("radiante", "cercano", "pico"))
    chequear("P1/P2 líneas de B0", None not in (r, c, k), f"{r} {c} {k}")
    if None not in (r, c, k):
        chequear("P1+P2 radiante pierde sólo LEJANA", r["P1"] == 1, f"radiante P1 {r['P1']}")
        chequear("P1+P2 cercano no pierde ninguna", c["P1"] == 0, f"cercano P1 {c['P1']}")
        chequear("P1+P2 pico pierde LEJANA y BORDE", k["P1"] == 2, f"pico P1 {k['P1']}")
        chequear("P3 cercano publica el negativo LEJANA", c["E_neg"] == 1 and r["E_neg"] == 0 and k["E_neg"] == 0,
                 f"E_neg radiante {r['E_neg']} cercano {c['E_neg']} pico {k['E_neg']}")
        chequear("P1 cambia contra radiante, con la etiqueta", "('prot', 'publica'): 1" in c["resto"]
                 and "('neg', 'publica'): 1" in c["resto"], c["resto"].strip())
        chequear("P2 pico calla la protegida BORDE contra radiante", "('prot', 'calla'): 1" in k["resto"], k["resto"].strip())
    mf = re.search(r"^   B0: radiante publica (\d+) \| cercano publica (\d+) \| pico publica (\d+)", out, re.M)
    chequear("P4 far_ref: sólo cercano publica", bool(mf) and mf.groups() == ("0", "1", "0"),
             mf.group(0).strip() if mf else "sin línea far_ref B0")
    md = re.search(r"far_ref B0: radiante ([\d.]+) km, ([\d.]+), n=1 \| cercano ([\d.]+) km, ([\d.]+), n=1 \| "
                   r"pico ([\d.]+) km, ([\d.]+), n=1", out)
    chequear("P4 distancia desde el centro: radiante y pico calzan con MIROVA, cercano no",
             bool(md) and float(md.group(1)) <= 1 and float(md.group(5)) <= 1 and float(md.group(3)) > 5,
             md.group(0) if md else "sin línea de distancia far_ref")

    # P6: sin gránulo de otra lista
    d = esc("P6")
    p.escribir(d, sg_ajeno=True)
    rc, out = lector(a.lector, d, a.evaluador)
    chequear("P6 C3 cae con el archivo de otra lista", rc == 3 and "NO LEGIBLE" in out and "C3 listas" in out
             and "FALLA" in out.split("C3 listas")[1].splitlines()[0], f"salida {rc}")

    # P7: analizador cambiado
    d = esc("P7")
    p.escribir(d)
    otro = d / "analizar_otro.py"
    src = ANALIZAR.read_text(encoding="utf-8")
    otro.write_text(src.replace("MAX_SIN_DATO = 0.02", "MAX_SIN_DATO = 0.03", 1), encoding="utf-8")
    rc, out = lector(a.lector, d, a.evaluador, analizador=otro)
    chequear("P7 C4 cae con otro analizador", rc == 3 and "DISTINTO DEL TAG" in out, f"salida {rc}")

    # P8: separar no cambia la lectura sellada
    d = esc("P8")
    p.escribir(d, con_supl=False)
    sin_supl = d / "art"
    d2 = esc("P8b")
    p.escribir(d2, con_supl=True)
    rcs, outs = correr([sys.executable, str(AQUI / "separar_resultados_v750b.py"), "--art", str(d2 / "art"),
                        "--dest", str(d2 / "sep")])
    salidas = []
    for art, nom in ((sin_supl, "a"), (d2 / "sep" / "sellado", "b")):
        rc, out = correr([sys.executable, str(ANALIZAR), "--art", str(art), "--objetivos", str(d / "objetivos.json"),
                          "--evaluador", str(a.evaluador), "--sin-granulo", str(d / "sin_granulo.json"),
                          "--solo-controles", "--censo-omitido-solo-pruebas", "--salida", str(d / f"an_{nom}.txt")])
        salidas.append((d / f"an_{nom}.txt").read_bytes() if (d / f"an_{nom}.txt").exists() else None)
    chequear("P8 separar: salida del analizador sellado idéntica", rcs == 0 and salidas[0] is not None
             and salidas[0] == salidas[1], f"separar {rcs}: {outs.strip()[:120]}")
    rcx, _ = correr([sys.executable, str(ANALIZAR), "--art", str(d2 / "art"), "--objetivos", str(d / "objetivos.json"),
                     "--evaluador", str(a.evaluador), "--sin-granulo", str(d / "sin_granulo.json"), "--solo-controles",
                     "--censo-omitido-solo-pruebas", "--salida", str(d / "an_c.txt")])
    sc = (d / "an_c.txt").read_bytes() if (d / "an_c.txt").exists() else b""
    chequear("P8 testigo: sin separar, la salida sellada SÍ cambia (cuenta los resultados de más)",
             salidas[0] is not None and sc != salidas[0], "distinta" if sc != salidas[0] else "igual")

    # P9: el generador se niega si el filtro no aparece exactamente una vez
    sys.path.insert(0, str(AQUI))
    import objetivos_supl_v750b as GEN
    for veces in (0, 1, 2):
        f = dest / f"pob_{veces}.py"
        f.write_text("VENTANA = None\n" + ("def g(r):\n    " + GEN.FILTRO_SELLADO + "\n        return 0\n") * veces,
                     encoding="utf-8")
        try:
            m = GEN.poblacion_con_far_ref(f)
            ok = veces == 1 and GEN.FILTRO_SUPL in f.read_text(encoding="utf-8").replace(GEN.FILTRO_SELLADO, GEN.FILTRO_SUPL)
            chequear(f"P9 filtro {veces} veces", ok and hasattr(m, "g"), "cargó")
        except SystemExit as e:
            chequear(f"P9 filtro {veces} veces", veces != 1, f"se negó: {e}")

    for x in filas:
        print(x)
    if caidas:
        print("CAÍDAS:", caidas)
    print(f"== PRUEBAS: {'TODOS LOS ESCENARIOS COMO SE ESPERA' if not fallas and not caidas else 'FALLAS ' + str(len(fallas))} "
          f"({len(filas)})")
    return 0 if not fallas and not caidas else 1


if __name__ == "__main__":
    sys.exit(main())
