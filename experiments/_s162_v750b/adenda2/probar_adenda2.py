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
  P9  el generador cambia el filtro de etiquetas sólo si aparece una vez (con 0 o 2 apariciones se niega), y con el
      cambio far_ref pasa el filtro, pos también y sin_info sigue afuera.
Salida: 0 todo como se espera; 1 alguna falla por aserción; 2 el lector se cayó (traceback).
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
PICOCERCA = [(33, 34, 5.0), (33, 50, 0.9), (33, 51, 0.9)]


def k_record():
    return {"primary_cluster": None, "distance_class": None, "vrp_mw": 0.0, "vrp_mir_mw": 0.0,
            "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None, "t_max_k": 290.0,
            "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}


class Pob:
    def __init__(self):
        self.sell, self.supl, self.res = [], [], []

    def pasada(self, hora, lab, pix, vrp_mirova=0.0, volcan="Lascar", dist_mirova=None, crater=(33.0, 33.0),
               dayflag=0, pub_prod=False, fuente="CONS", id_forzado=None, pc_vrp=0.0):
        supl = lab == "far_ref"
        lista = self.supl if supl else self.sell
        i = id_forzado if id_forzado is not None else (100000 if supl else 0) + len(lista)
        if lab == "pos":
            filas = [{"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA", "vrp_mw": vrp_mirova,
                      "dist_km": dist_mirova, "source": fuente}]
        elif lab == "far_ref":
            filas = [{"fecha_utc": hora + ":00", "tipo": "FALSO_POSITIVO", "vrp_mw": vrp_mirova,
                      "dist_km": dist_mirova, "source": "CONS"}]
        else:
            filas = [{"fecha_utc": hora + ":00", "tipo": "RUTINA", "vrp_mw": 0.0, "dist_km": None, "source": "CONS"}]
        o = {"id": i, "volcan": volcan, "hora_utc": hora, "sensor": SENSOR, "lab": lab,
             "protegida": lab == "pos" and vrp_mirova >= 1.0, "alerta_tabla": lab == "pos" and fuente == "CONS",
             "decide": True, "mirova": filas, "mirova_vrp": vrp_mirova, "z": 30.0, "pub_prod": pub_prod, "dc": None,
             "pc_vrp": pc_vrp,
             "pc_n": None, "granule": f"g{i}", "en_sc": False, "celda_crater": [int(x) for x in crater],
             "pos_crater": list(crater),
             "inner_km": 5.0}
        if supl:
            o["dist_ref"] = dist_mirova
        lista.append(o)
        self.res.append({"id": i, "volcan": volcan, "hora_utc": hora, "estado": "ok", "dayflag": dayflag, "sunglint": 40.0,
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
           "P4": p.pasada("2026-07-04 05:00", "far_ref", LEJANA, 3.0, dist_mirova=13.1, crater=(33.0, 30.0)),
           # VAD2-04: cráter 7,5 km al W del centro y el alertado junto al cráter: sólo anclado al cráter es cumbre
           "P10": p.pasada("2026-07-05 05:00", "pos", [(33, 24, 0.9)], 2.0, dist_mirova=6.8, crater=(33.0, 23.0)),
           # VAD2-04: el más radiante junto al cráter y un cúmulo más débil lejos: los tres brazos publican
           "P11": p.pasada("2026-07-06 05:00", "pos", PICOCERCA, 2.0, dist_mirova=0.8),
           # VAD2-02: K del probe distinto de producción (producción publicó, K no): sale de todos los brazos
           "P12": p.pasada("2026-07-07 05:00", "pos", LEJANA, 2.0, dist_mirova=0.8, pub_prod=True),
           # VAD2-04: diurna: no entra
           "P13": p.pasada("2026-07-08 05:00", "pos", LEJANA, 2.0, dist_mirova=0.8, dayflag=1),
           # VAD2-04: protegida sólo del OCR (después del 2026-06-13): decide con tabla más OCR, no con la tabla sola;
           # y su distancia sí entra a la vara 3 (desde el 13-jun el OCR la trae medida)
           "P14": p.pasada("2026-07-09 05:00", "pos", LEJANA, 2.0, dist_mirova=0.8, fuente="OCR"),
           # VAD2-05: alerta sólo del OCR ANTES del 2026-06-13 con distancia: no entra a la vara 3
           "P15": p.pasada("2026-05-20 05:00", "pos", UNO, 0.4, dist_mirova=20.0, fuente="OCR"),
           # N1 (verificador corto): K del probe en 0 MW y producción con 0,5 MW (misma publicación): sale igual
           "P19": p.pasada("2026-07-10 05:00", "neg_limpio", LEJANA, pc_vrp=0.5),
           # VAD2-07: pasada lejana sin ningún alertado: cuenta en las observadas, no en «con algún alertado»
           "P20": p.pasada("2026-07-11 05:00", "far_ref", [], 3.0, dist_mirova=20.0)}
    return p, ids


def correr(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


CAIDAS = []


def lector(ruta, d, ev, analizador=None):
    cmd = [sys.executable, str(ruta), "--art", str(d / "art"), "--objetivos", str(d / "objetivos.json"),
           "--objetivos-supl", str(d / "supl.json"), "--sin-granulo-supl", str(d / "sin_granulo_supl.json"),
           "--evaluador", str(ev), "--salida", str(d / "lector.txt")]
    if analizador:
        cmd += ["--analizador", str(analizador)]
    rc, out = correr(cmd)
    if "Traceback" in out:
        CAIDAS.append(d.name)
    return rc, out


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
    ap.add_argument("--separar", default=str(AQUI / "separar_resultados_v750b.py"))
    ap.add_argument("--generador", default=str(AQUI / "objetivos_supl_v750b.py"))
    ap.add_argument("--dest", default="")
    a = ap.parse_args()
    dest = Path(a.dest) if a.dest else Path(tempfile.mkdtemp(prefix="adenda2_"))
    filas, fallas = [], []

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
    chequear("P5 controles en verde y salida 0", rc == 0 and "controles C1 a C4: EN VERDE" in out,
             f"salida {rc}: " + (out[-400:].replace("\n", " | ") if rc else ""))
    m1 = re.search(r"C1 cajas con un solo alertado: (\d+); con brazos distintos (\d+)", out)
    chequear("P5 C1 cuenta casos y ninguno distinto", bool(m1) and int(m1.group(1)) >= 3 and m1.group(2) == "0",
             m1.group(0) if m1 else "sin línea C1")
    dec, tab = out.split("canal decide", 1)[-1].split("canal tabla", 1) if "canal tabla" in out else (out, "")
    mk = re.search(r"K distinto de producci\S+ \(salen, como en el sellado\): (\d+)", out)
    chequear("P12 y P19 las pasadas con K distinto (en publicación o en magnitud) salen", bool(mk) and mk.group(1) == "2",
             mk.group(0) if mk else "sin línea de K distinto")
    r, c, k = (linea(dec, "B0", b) for b in ("radiante", "cercano", "pico"))
    chequear("P1/P2 líneas de B0 (canal decide)", None not in (r, c, k), f"{r} {c} {k}")
    if None not in (r, c, k):
        # canal decide: protegidas P1 (LEJANA), P2 (BORDE), P10 (cráter corrido), P11 (PICOCERCA), P14 (OCR, LEJANA);
        # P12 sale por K distinto y P13 por diurna
        chequear("P1 a P14 protegidas contadas", r["prot"] == 5 and c["prot"] == 5 and k["prot"] == 5,
                 f"prot {r['prot']} {c['prot']} {k['prot']}")
        chequear("radiante pierde LEJANA y la del OCR, no la del cráter corrido", r["P1"] == 2, f"radiante P1 {r['P1']}")
        chequear("cercano no pierde ninguna", c["P1"] == 0, f"cercano P1 {c['P1']}")
        chequear("pico pierde LEJANA, la del OCR y BORDE, no PICOCERCA", k["P1"] == 3, f"pico P1 {k['P1']}")
        chequear("P3 cercano publica el negativo LEJANA", c["E_neg"] == 1 and r["E_neg"] == 0 and k["E_neg"] == 0,
                 f"E_neg radiante {r['E_neg']} cercano {c['E_neg']} pico {k['E_neg']}")
        chequear("cambian contra radiante (cercano), exacto y sin las suplementarias",
                 "cambian contra radiante {('prot', 'publica'): 2, ('neg', 'publica'): 1}" in c["resto"], c["resto"].strip())
        chequear("cambian contra radiante (pico), exacto", "cambian contra radiante {('prot', 'calla'): 1}" in k["resto"],
                 k["resto"].strip())
        chequear("P2 de cercano contra radiante", "P2 SIN SUSTRATO (neto 1, bloques 1)" in c["resto"], c["resto"].strip())
    r, c, k = (linea(tab, "B0", b) for b in ("radiante", "cercano", "pico"))
    chequear("canal tabla: la protegida sólo del OCR no cuenta", None not in (r, c, k) and r["prot"] == 4
             and (r["P1"], c["P1"], k["P1"]) == (1, 0, 2), f"{r} {c} {k}")
    mf = re.search(r"^   B0: con alg\S+ alertado (\d+) de (\d+) \| radiante publica (\d+) \| cercano publica (\d+) \| "
                   r"pico publica (\d+)", out, re.M)
    chequear("P4 far_ref: sólo cercano publica, con alertado 1 de 2", bool(mf) and mf.groups() == ("1", "2", "0", "1", "0"),
             mf.group(0).strip() if mf else "sin línea far_ref B0")
    md = re.search(r"far_ref B0: radiante ([\d.]+) km, ([\d.]+), n=1 \| cercano ([\d.]+) km, ([\d.]+), n=1 \| "
                   r"pico ([\d.]+) km, ([\d.]+), n=1", out)
    chequear("P4 distancia desde el centro: radiante y pico calzan con MIROVA, cercano no",
             bool(md) and float(md.group(1)) <= 1 and float(md.group(5)) <= 1 and float(md.group(3)) > 5,
             md.group(0) if md else "sin línea de distancia far_ref")
    ma = re.search(r"alertas con distancia B0: radiante ([\d.]+) km, ([\d.]+), n=(\d+) \|", out)
    chequear("P15 la alerta OCR de antes del 13-jun no entra a la vara 3 (8 alertas, no 9)", bool(ma) and ma.group(3) == "8",
             ma.group(0) if ma else "sin línea de distancia de alertas")

    # P6: sin gránulo de otra lista
    d = esc("P6")
    p.escribir(d, sg_ajeno=True)
    rc, out = lector(a.lector, d, a.evaluador)
    chequear("P6 C3 cae con el archivo de otra lista", rc == 3 and "NO LEGIBLE" in out and "C3 listas" in out
             and "FALLA" in out.split("C3 listas")[1].splitlines()[0], f"salida {rc}")

    # P7: analizador cambiado
    d = esc("P7")
    p.escribir(d)
    # la copia va al lado del sellado (sus rutas son relativas a su carpeta): si el lector la aceptara, correría
    # sin caerse y la falla sería por aserción, no por caída; temporal que se borra en el acto
    otro = V750B / "_p7_analizar_otro.py"
    src = ANALIZAR.read_text(encoding="utf-8")
    otro.write_text(src.replace("MAX_SIN_DATO = 0.02", "MAX_SIN_DATO = 0.03", 1), encoding="utf-8")
    try:
        rc, out = lector(a.lector, d, a.evaluador, analizador=otro)
    finally:
        otro.unlink()
    chequear("P7 C4 cae con otro analizador", rc == 3 and "DISTINTO DEL TAG" in out, f"salida {rc}")

    # P8: separar no cambia la lectura sellada
    d = esc("P8")
    p.escribir(d, con_supl=False)
    sin_supl = d / "art"
    d2 = esc("P8b")
    p.escribir(d2, con_supl=True)
    rcs, outs = correr([sys.executable, str(a.separar), "--art", str(d2 / "art"),
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
    import importlib.util
    spec = importlib.util.spec_from_file_location("gen_supl", a.generador)
    GEN = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(GEN)
    sello = 'if r["lab"] not in ("pos", "neg_limpio"):'
    for veces in (0, 1, 2):
        f = dest / f"pob_{veces}.py"
        f.write_text("".join(f"def g{n}(r):\n    {sello}\n        return 0\n    return 1\n" for n in range(veces)),
                     encoding="utf-8")
        try:
            m = GEN.poblacion_con_far_ref(f)
            pasa = [getattr(m, f"g{n}")({"lab": lab}) for n in range(veces) for lab in ("far_ref", "pos", "sin_info")]
            chequear(f"P9 filtro {veces} veces", veces == 1 and pasa == [1, 1, 0],
                     f"cargó; far_ref, pos y sin_info pasan el filtro: {pasa}")
        except SystemExit as e:
            chequear(f"P9 filtro {veces} veces", veces != 1, f"se negó: {e}")

    # P6b (VAD2-04, M9/M10): una suplementaria con id de la lista sellada: C3 cae
    p2_, _ = poblacion()
    p2_.pasada("2026-07-20 05:00", "far_ref", LEJANA, 3.0, dist_mirova=13.1, id_forzado=3)
    d = esc("P6b")
    p2_.escribir(d)
    rc, out = lector(a.lector, d, a.evaluador)
    chequear("P6b C3 cae con un id suplementario que choca con la sellada", rc == 3 and "NO LEGIBLE" in out, f"salida {rc}")

    # P8c (VAD2-01, VAD2-04 S2 a S4): el separador reparte cada id una sola vez, no pisa carpetas del mismo nombre y
    # no escribe en una carpeta con algo adentro
    d = esc("P8c")
    for sub, filas_ in (("uno/artefactos", [{"id": 0, "estado": "ok"}, {"id": 100000, "estado": "ok"}]),
                        ("dos/artefactos", [{"id": 1, "estado": "ok"}, {"id": 100001, "estado": "error: x"}])):
        q = d / sub / "chunk-3"
        q.mkdir(parents=True)
        (q / "resultados_03.json").write_text(json.dumps(filas_), encoding="utf-8")
    rcs, outs = correr([sys.executable, str(a.separar), "--art", str(d / "uno/artefactos"), str(d / "dos/artefactos"),
                        "--dest", str(d / "sep")])
    ids = {parte: sorted(r["id"] for q in (d / "sep" / parte).rglob("resultados_*.json")
                         for r in json.loads(q.read_text(encoding="utf-8"))) for parte in ("sellado", "supl")}
    chequear("P8c separar: carpetas del mismo nombre no se pisan y cada id va a su parte",
             rcs == 0 and ids == {"sellado": [0, 1], "supl": [100000, 100001]}, f"salida {rcs}, {ids}")
    rcs2, _ = correr([sys.executable, str(a.separar), "--art", str(d / "uno/artefactos"), "--dest", str(d / "sep")])
    chequear("P8c separar: no escribe en una carpeta con algo adentro", rcs2 == 2, f"salida {rcs2}")

    # P16 (VAD2-04, G3 a G9): las funciones del generador, con datos sintéticos
    def pp(h, lab, **kw):
        base_ = {"volcan": "Lascar", "hora_utc": h, "granule": "g" + h, "lab": lab, "protegida": False,
                 "alerta_tabla": False, "decide": True, "mirova": []}
        base_.update(kw)
        return base_
    pob = [pp("2026-05-01 05:00", "pos", protegida=True, alerta_tabla=True), pp("2026-05-02 05:00", "neg_limpio"),
           pp("2026-10-12 05:00", "far_ref"), pp("2026-11-02 13:30", "far_ref"),
           pp("2026-06-01 05:00", "far_ref", mirova=[{"tipo": "ALERTA_TERMICA", "dist_km": 1.0},
                                                       {"tipo": "FALSO_POSITIVO", "dist_km": 14.0}]),
           pp("2026-05-03 05:00", "far_ref", granule=None), pp("2026-05-04 05:00", "sin_info")]
    rec = GEN.recortar(pob, ("2026-10-12",), "2026-11-02 13:00")
    chequear("P16 recortar saca el día excluido y lo posterior al cese de Suomi NPP",
             sorted(x["hora_utc"] for x in rec) == ["2026-05-01 05:00", "2026-05-02 05:00", "2026-05-03 05:00",
                                                    "2026-05-04 05:00", "2026-06-01 05:00"], str([x["hora_utc"] for x in rec]))
    sellado_ok = [dict(pob[0]), dict(pob[1])]
    sellado_mal = [dict(pob[0], protegida=False), dict(pob[1])]
    chequear("P16 comparar: igual con la misma población, distinta si cambia una protegida",
             GEN.comparar(rec, sellado_ok)[0] and not GEN.comparar(rec, sellado_mal)[0], "comparar")
    far, sin_g = GEN.seleccionar_far(rec)
    chequear("P16 seleccionar_far: sólo far_ref, sin gránulo aparte, distancia de la fila FALSO_POSITIVO, sin S_C",
             [x["hora_utc"] for x in far] == ["2026-06-01 05:00"] and far[0]["dist_ref"] == 14.0
             and far[0]["en_sc"] is False and [x[1] for x in sin_g] == ["2026-05-03 05:00"],
             f"{[(x['hora_utc'], x.get('dist_ref'), x.get('en_sc')) for x in far]} {sin_g}")
    nn = GEN.numerar([pp("2026-07-02 05:00", "far_ref", granule="b"), pp("2026-07-01 05:00", "far_ref", granule="a")])
    chequear("P16 numerar: ids desde 100000 en orden de gránulo",
             [(x["granule"], x["id"]) for x in nn] == [("a", 100000), ("b", 100001)], str([(x["granule"], x["id"]) for x in nn]))

    chequear("P16 lista_run: la sellada primero, sin tocar, y la suplementaria después",
             [x["id"] for x in GEN.lista_run([{"id": 0}, {"id": 1}], [{"id": 100000}])] == [0, 1, 100000], "lista_run")

    # P5b (VAD2-04, M13): sin ninguna caja de un solo alertado, C1 no tiene casos y cae
    p3_ = Pob()
    for n in range(4):
        p3_.pasada(f"2026-04-{1 + n:02d} 05:00", "neg_limpio", [])
    p3_.pasada("2026-07-01 05:00", "pos", LEJANA, 2.0, dist_mirova=0.8)
    p3_.pasada("2026-07-04 05:00", "far_ref", LEJANA, 3.0, dist_mirova=13.1)
    d = esc("P5b")
    p3_.escribir(d)
    rc, out = lector(a.lector, d, a.evaluador)
    m1 = re.search(r"C1 cajas con un solo alertado: (\d+);.*?: (OK|FALLA)", out)
    chequear("P5b C1 sin casos cae", rc == 3 and bool(m1) and m1.groups() == ("0", "FALLA"), m1.group(0) if m1 else f"salida {rc}")

    # P6c (VAD2-04, M9): una sellada con id de la suplementaria: C3 cae
    p4_, _ = poblacion()
    p4_.pasada("2026-07-21 05:00", "neg_limpio", [], id_forzado=100050)
    d = esc("P6c")
    p4_.escribir(d)
    rc, out = lector(a.lector, d, a.evaluador)
    chequear("P6c C3 cae con un id sellado de 100000 o más", rc == 3 and "NO LEGIBLE" in out, f"salida {rc}")

    # P17 (VAD2-04, M14 y M18): la vara 3 informa B0 y B1; el SIN DATO se cuenta en su lista
    p5_, _ = poblacion()
    j = p5_.pasada("2026-07-22 05:00", "far_ref", LEJANA, 3.0, dist_mirova=13.1)
    next(r for r in p5_.res if r["id"] == j)["estado"] = "error: sintetico"
    d = esc("P17")
    p5_.escribir(d)
    rc, out = lector(a.lector, d, a.evaluador)
    ms = re.search(r"selladas: observadas \d+ \| no observadas \d+ \| SIN DATO (\d+)", out)
    mp = re.search(r"suplementarias: observadas (\d+) \| no observadas \d+ \| SIN DATO (\d+)", out)
    chequear("P17 SIN DATO de la suplementaria en su lista, no en la sellada",
             bool(ms and mp) and ms.group(1) == "1" and mp.groups() == ("2", "1"),   # la sellada: sólo la diurna P13
             f"{ms.group(0) if ms else '-'} / {mp.group(0) if mp else '-'}")
    chequear("P17 la vara 3 informa B0 y B1", "alertas con distancia B1:" in out and "far_ref B1:" in out, "vara 3")

    # P18 (N2 y N3 del verificador corto): generar() entero, con dependencias sintéticas y una carpeta «sellada» de
    # mentira (la real nunca se toca: si una guarda fallara, escribiría en un temporal)
    def dep_sint(pasadas, llamadas):
        def poblar(dest_, hasta, data, ref_dest):
            llamadas.append(str(dest_))
            (Path(dest_) / "poblacion_completa.json").write_text(json.dumps({"pasadas": pasadas}), encoding="utf-8")

        def completar(far_):
            for x in far_:
                x["celda_crater"], x["pos_crater"], x["inner_km"] = [33, 33], [33.0, 33.0], 5.0
        return {"excluidos": ("2026-10-12",), "corte": "2026-11-02 13:00", "poblar": poblar, "completar": completar}

    pas = [pp("2026-05-01 05:00", "pos", protegida=True, alerta_tabla=True), pp("2026-05-02 05:00", "neg_limpio"),
           pp("2026-06-01 05:00", "far_ref", mirova=[{"tipo": "FALSO_POSITIVO", "dist_km": 14.0}]),
           pp("2026-10-12 05:00", "far_ref")]
    sell = [dict(pas[0], id=0), dict(pas[1], id=1)]
    fs = dest / "P18_sellado.json"
    fs.write_text(json.dumps(sell), encoding="utf-8")
    fsm = dest / "P18_sellado_mal.json"
    fsm.write_text(json.dumps([dict(pas[0], id=0, protegida=False), dict(pas[1], id=1)]), encoding="utf-8")
    falsa = esc("P18_sellada_falsa")
    import contextlib
    import io

    def gen(d_, sellado_, llamadas):
        # una excepción de generar() es una salida equivocada (se esperaba 0, 1 o 2), no una caída de la batería: queda
        # como rc y la aserción de cada escenario la ve (G12 y G13 del nulo revientan con FileExistsError en Windows)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc_ = GEN.generar(d_, "2026-11-02", "-", "-", sellado_, dep_sint(pas, llamadas), sellada=falsa)
        except Exception as e:  # noqa: BLE001
            rc_ = f"excepción {type(e).__name__}"
        return rc_, buf.getvalue()

    d = esc("P18a")
    ll = []
    rc, out = gen(d, fs, ll)
    run = json.loads((d / "objetivos_run_v750b.json").read_text(encoding="utf-8")) if rc == 0 else []
    supl_ = json.loads((d / "objetivos_supl_v750b.json").read_text(encoding="utf-8")) if rc == 0 else []
    chequear("P18a generar() con el control bien: escribe las listas, la sellada primero y sin tocar",
             rc == 0 and [x["id"] for x in run] == [0, 1, 100000] and run[:2] == sell
             and [x["hora_utc"] for x in supl_] == ["2026-06-01 05:00"] and "sha256 lista del run" in out,
             f"salida {rc}: {out.strip()[-160:]}")
    rc, out = gen(d, fs, ll)
    chequear("P18d generar() se niega con salidas previas en la carpeta", rc == 2 and len(ll) == 1, f"salida {rc}, poblar {len(ll)}")
    d = esc("P18b")
    ll = []
    rc, out = gen(d, fsm, ll)
    chequear("P18b generar() con el control caído: sale 1, ninguna lista, la población aparte",
             rc == 1 and not (d / "objetivos_run_v750b.json").exists() and not (d / "objetivos_supl_v750b.json").exists()
             and (d / "poblacion_supl_CONTROL_FALLIDO.json").exists(), f"salida {rc}")
    rc, out = gen(d, fsm, ll)
    chequear("P18b N2: un segundo intento fallido en la misma carpeta se niega (salida 2), no revienta",
             rc == 2 and len(ll) == 1, f"salida {rc}, poblar {len(ll)}")
    ll = []
    rc, out = gen(falsa, fs, ll)
    chequear("P18c generar() se niega en la carpeta sellada, antes de poblar", rc == 2 and not ll
             and not any(falsa.iterdir()), f"salida {rc}, poblar {len(ll)}")

    for x in filas:
        print(x)
    if CAIDAS:
        print("== CAÍDA DEL LECTOR en:", CAIDAS)
        return 2
    print(f"== PRUEBAS: {'TODOS LOS ESCENARIOS COMO SE ESPERA' if not fallas else 'FALLAS ' + str(len(fallas))} "
          f"({len(filas)})" + (f": {fallas}" if fallas else ""))
    return 0 if not fallas else 1


if __name__ == "__main__":
    sys.exit(main())
