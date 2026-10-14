# -*- coding: utf-8 -*-
"""F3 meta-auditoria S150, R1. Re-mide la tabla de recall por tramo de magnitud de
docs/S150_RESULTADO_MESES.md §2 (la que decide el recall de `max` en VIIRS, decision 1b de AUDIT_S150)
con la vara corregida.

POR QUE. `recall_por_magnitud.py` toma `lab == "pos"` del etiquetador de banco_paridad, que marca
positiva cualquier pasada con ALERTA de la tabla O del OCR, sin mirar fecha (banco_paridad.py,
`etiquetar`). A119 dice que antes del 2026-06-13 decide la tabla sola, y S150 (docs/S150_IMAGENES_SNPP.md)
mostro que una alerta "solo OCR" de Suomi NPP puede llevar la clase ALERTA de otra pasada.

Tres varas sobre la MISMA tabla por pasada (armar_tabla.py, referencia congelada del mes):
  L0 completa      : lab == pos (lo publicado). Control de instrumento: tiene que reproducir
                     resultados/recall_por_magnitud_*.txt al numero.
  L1 tabla sola    : pos y no alerta_solo_ocr.
  L2 A119+S150     : antes del 2026-06-13 tabla sola; desde el 2026-06-13 tabla y OCR, salvo las
                     alertas solo-OCR de Suomi NPP.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
  1. Si la vara estuviera rota (p. ej. el OCR metiera positivos falsos), ¿lo veria? Si: L1 y L2 los
     sacan del denominador y el recall por tramo cambia; el conteo de positivos solo-OCR se imprime.
  2. Si el instrumento estuviera muerto, ¿se veria distinto? Si: L0 debe dar EXACTAMENTE los n
     publicados; si no los da, el resto no se lee (se imprime CONTROL L0 OK/FALLA). Control positivo:
     L1 sobre agosto debe quitar positivos (hay alertas solo-OCR en agosto, S150 §3).

Uso: python r1_recall_tramo_vara_corregida.py --tmp <dir fuera del repo>
Solo lectura del repo: git archive de ramas s146-ab ya presentes; nada se escribe en el arbol salvo la
salida de este script en esta carpeta.
"""
import argparse, collections, io, json, shutil, subprocess, sys, tarfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
PRE = RAIZ / "experiments" / "_s149_prereg_invierno"
TRAMOS = [(0, .05), (.05, .1), (.1, .2), (.2, .5), (.5, 1e9)]
CORTE_OCR = "2026-06-13"
# (nombre, desde, hasta, runs en orden: el posterior pisa)  -- de despachos.log y S150_RESULTADO_MESES §1
MESES = [("abril", "2026-04-01", "2026-04-30", ["35639417826", "37823348991"]),
         ("mayo", "2026-05-01", "2026-05-31", ["35599902448"]),
         ("junio", "2026-06-01", "2026-06-30", ["35675490175"]),
         ("julio", "2026-07-01", "2026-07-31", ["35728617326"]),
         ("agosto", "2026-08-01", "2026-08-27", ["35759688167"])]
CONTROL, BRAZO = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"


def extraer(runs, tmp):
    base = tmp / "runs"
    for r in runs:
        ruta = "experiments/_s146_ab_sin_test1/salidas/%s" % r
        tar = subprocess.run(["git", "archive", "origin/s146-ab/%s" % r, ruta], cwd=RAIZ,
                             capture_output=True, check=True).stdout
        tarfile.open(fileobj=io.BytesIO(tar)).extractall(base)
    return base / "experiments" / "_s146_ab_sin_test1" / "salidas"


def unir(salidas, runs, perfil, destino):
    d = destino / perfil
    d.mkdir(parents=True, exist_ok=True)
    for r in runs:
        p = salidas / str(r) / perfil
        if p.exists():
            for f in sorted(p.glob("*.json")):
                shutil.copy(f, d / f.name)
    return d


def tabla_mes(nombre, desde, hasta, runs, tmp):
    t = tmp / nombre
    shutil.rmtree(t, ignore_errors=True)
    t.mkdir(parents=True)
    sal = extraer(runs, t)
    dc, db = unir(sal, runs, CONTROL, t / "u"), unir(sal, runs, BRAZO, t / "u")
    C = PRE / "_congelado" / nombre
    out = t / "tabla.json"
    subprocess.run([sys.executable, str(PRE / "armar_tabla.py"), "--control", str(dc), "--brazo", str(db),
                    "--cons", str(C / "registro_vrp_consolidado.csv"), "--ocr", str(C / "registro_vrp_ocr.csv"),
                    "--desde", desde, "--hasta", hasta, "--out", str(out)], check=True,
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    T = json.loads(out.read_text(encoding="utf-8"))
    # liberar disco: solo se conserva la tabla
    shutil.rmtree(t / "runs", ignore_errors=True)
    shutil.rmtree(t / "u", ignore_errors=True)
    return T


def es_snpp(c):
    return "SNPP" in str(c.get("plataforma") or "").upper()


VARAS = {
    "L0_completa": lambda k, c: c["lab"] == "pos",
    "L1_tabla_sola": lambda k, c: c["lab"] == "pos" and not c["alerta_solo_ocr"],
    "L2_A119_S150": lambda k, c: c["lab"] == "pos" and not (
        c["alerta_solo_ocr"] and (k.split("|")[2][:10] < CORTE_OCR or es_snpp(c))),
}


def informe(nombre, T, acum):
    print("\n== %s  ventana %s" % (nombre, T["ventana"]))
    for sensor in ("VIIRS375", "VIIRS750"):
        filas = [(k, v["control"], v["brazo"]) for k, v in T["pasadas"].items()
                 if k.split("|")[1] == sensor and len(v) == 2 and v["control"]["vrp_ref"]]
        pos0 = [x for x in filas if x[1]["lab"] == "pos"]
        solo = [x for x in pos0 if x[1]["alerta_solo_ocr"]]
        print("  %s | positivos L0 %d | solo-OCR %d (antes de %s: %d; Suomi NPP: %d; SNPP desde %s: %d)" % (
            sensor, len(pos0), len(solo), CORTE_OCR, sum(1 for x in solo if x[0].split("|")[2][:10] < CORTE_OCR),
            sum(1 for x in solo if es_snpp(x[1])), CORTE_OCR,
            sum(1 for x in solo if es_snpp(x[1]) and x[0].split("|")[2][:10] >= CORTE_OCR)))
        for vara, f in VARAS.items():
            pos = [(c, b) for k, c, b in filas if f(k, c)]
            celdas = []
            for a, bnd in TRAMOS:
                s = [(c, b) for c, b in pos if a <= c["vrp_ref"] < bnd]
                nc, nf = sum(c["pub"] for c, b in s), sum(b["pub"] for c, b in s)
                acum[(sensor, vara, a)][0] += len(s); acum[(sensor, vara, a)][1] += nc; acum[(sensor, vara, a)][2] += nf
                celdas.append("%s n%3d B%3d F%3d" % (("<%.2f" % bnd) if bnd < 1e8 else ">=0.5", len(s), nc, nf))
            nc, nf = sum(c["pub"] for c, b in pos), sum(b["pub"] for c, b in pos)
            print("     %-14s TOTAL n%4d B%4d F%4d | %s" % (vara, len(pos), nc, nf, " | ".join(celdas)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmp", required=True)
    ap.add_argument("--meses", nargs="*", default=[m[0] for m in MESES])
    a = ap.parse_args()
    tmp = Path(a.tmp)
    acum = collections.defaultdict(lambda: [0, 0, 0])
    for nombre, desde, hasta, runs in MESES:
        if nombre not in a.meses:
            continue
        cache = tmp / ("tabla_%s.json" % nombre)
        if cache.exists():
            T = json.loads(cache.read_text(encoding="utf-8"))
        else:
            T = tabla_mes(nombre, desde, hasta, runs, tmp)
            cache.write_text(json.dumps(T, ensure_ascii=False), encoding="utf-8")
        informe(nombre, T, acum)
    print("\n== AGREGADO de los meses pedidos, VIIRS375, por tramo (n, B publica, F publica)")
    for vara in VARAS:
        print("  " + vara)
        for a_, bnd in TRAMOS:
            n, nc, nf = acum[("VIIRS375", vara, a_)]
            if n:
                print("     tramo %-6s n %4d | B %4d (%5.1f %%) | F %4d (%5.1f %%)" % (
                    ("<%.2f" % bnd) if bnd < 1e8 else ">=0.5", n, nc, 100 * nc / n, nf, 100 * nf / n))


if __name__ == "__main__":
    main()
