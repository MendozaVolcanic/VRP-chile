# Tarea 1.23, punto 3: por que el Test 1 MODIS de Lascar cruza el umbral con ~0,4 km de corrimiento.
# Medido sobre los artefactos YA GUARDADOS de la 1.21 (runs 39033482528 y 39034846297, tag
# s151-1.21-probe), sin reprocesar ni bajar L1B. Solo lectura.
#
# POR QUE ASI. La 1.21 guardo `test1_k_observed` y `triggered_test1` en los brazos C (posicion de
# produccion), M (MxD03) y R (la misma grilla de produccion trasladada en bloque, el mismo tamano que el
# corrimiento real, rumbo al azar). Si el salto de k entre C y M fuera propio de MxD03, R (que no trae
# informacion de posicion) deberia mover k mucho menos. Si R lo mueve igual, la sensibilidad es del Test 1
# integrado a 1 km, no de MxD03.
#
# El Test 1 (pipeline/test1_integrated.py:348, compute_test1_mir) suma el exceso RECORTADO a cero de los
# pixeles de un disco de 3 km y lo divide por sigma_bg * sqrt(n_roi), con sigma_bg sacado de la MAD del
# anillo de 1 a 3 km. Con pixeles de 1 km el disco tiene unos 28 pixeles y el anillo unos 25 (minimo 20),
# asi que: (1) el ruido puro ya da k ~ 0,399 * sqrt(n_roi) ~ 2,1 (el recorte de S146/D30, sin la
# correccion del nulo, ENABLE_TEST1_NULL_CORRECTED apagado) con desviacion ~0,58, contra un umbral de 3;
# (2) correr la grilla unos cientos de metros cambia que pixeles quedan en el disco y en el anillo, y la
# MAD de 25 pixeles se mueve con eso. Este script mide cuanto se mueve k, no lo deriva.
#
# Uso: python sensibilidad_test1_121.py <carpeta con los <job>.json de la 1.21> [--salida x.txt]
import argparse
import io
import json
import math
import statistics as st
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "_s151_mxd03_cumulo_121"))
sys.path.insert(0, str(AQUI.parent / "_s151_mxd03_etiquetas"))

import modelo_corrimiento as MC  # noqa: E402
import seleccionar_mxd03 as S  # noqa: E402

UMBRAL_K = 3.0              # TEST1_K_SIGMA del perfil mirova_equivalent (leido de pipeline.profile)
ROI_KM, ANILLO_KM, MIN_BG = 3.0, 1.0, 20
BINS = ((0, 10), (10, 20), (20, 30), (30, 50), (50, 90))


def area_pixel_km2(cenit):
    """Area de un pixel MODIS de 1 km en el suelo: ancho a lo largo del barrido (espaciado entre frames,
    modelo de #828) por paso entre lineas (modelo_corrimiento.km_por_linea)."""
    th = MC.angulo_barrido(cenit)
    ancho = S._suelo(th + S.PASO_GRADOS / 2) - S._suelo(th - S.PASO_GRADOS / 2)
    return ancho * MC.km_por_linea(cenit)


def esperado(cenit):
    """n_roi y n_bg geometricos y la k del ruido puro (media 0,399*sqrt(n), sd sqrt(0,3408))."""
    a = area_pixel_km2(cenit)
    n_roi = math.pi * ROI_KM ** 2 / a
    n_bg = math.pi * (ROI_KM ** 2 - ANILLO_KM ** 2) / a
    return {"area_km2": a, "n_roi": n_roi, "n_bg": n_bg, "k_ruido": 0.398942 * math.sqrt(n_roi),
            "sd_k_ruido": math.sqrt(0.5 - 1 / (2 * math.pi))}


def cargar(carpeta):
    filas = []
    for p in sorted(Path(carpeta).rglob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if not (isinstance(d, dict) and "granulos" in d and "brazos" in d):
            continue
        for g in d["granulos"]:
            if g.get("estado") != "ok":
                continue
            b = g["brazos"]
            if not (b.get("C") and b.get("M") and b.get("R")):
                continue
            filas.append({"volcan": d["volcan"], "clave": g["clave"], "cenit": b["C"]["cenit"],
                          "km": g["desplazamiento"]["km"], "prot": None,
                          "k": {x: b[x]["test1_k_observed"] or 0.0 for x in ("C", "M", "R")},
                          "trig": {x: bool(b[x]["triggered_test1"]) for x in ("C", "M", "R")},
                          "fuente": {x: b[x]["final_hotspot_source"] for x in ("C", "M", "R")},
                          "pub": {x: g["pub"][x] for x in ("C", "M", "R")}})
    return filas


def _bin(c):
    for lo, hi in BINS:
        if lo <= c < hi:
            return "%d-%d" % (lo, hi)
    return "?"


def _med(xs):
    return round(st.median(xs), 3) if xs else None


def analizar(filas, poblacion=None):
    prot = {}
    if poblacion:
        for vol, v in poblacion["volcanes"].items():
            for g in v["muestra"]:
                prot[(vol, g["clave"])] = bool(g["prot"])
    for f in filas:
        f["prot"] = prot.get((f["volcan"], f["clave"]))
    out = {"n_granulos": len(filas), "por_cenit": {}, "pares": {}, "cruces": {}, "lascar_protegidas": []}
    # (1) en que cenit el Test 1 llega a calcularse (k > 0) y contra que k de ruido
    for lo, hi in BINS:
        sel = [f for f in filas if lo <= f["cenit"] < hi]
        if not sel:
            continue
        e = esperado((lo + min(hi, 60)) / 2)
        calc = [f for f in sel if f["k"]["C"] > 0]
        out["por_cenit"]["%d-%d" % (lo, hi)] = {
            "n": len(sel), "test1_calculado_en_C": len(calc),
            "k_C_mediana": _med([f["k"]["C"] for f in calc]),
            "n_roi_geometrico": round(e["n_roi"], 1), "n_bg_geometrico": round(e["n_bg"], 1),
            "k_ruido_esperado": round(e["k_ruido"], 2)}
    # (2) cuanto se mueve k: M contra C y R contra C, mismo granulo, mismo tamano de corrimiento en km
    par = [f for f in filas if f["k"]["C"] > 0 and f["k"]["M"] > 0 and f["k"]["R"] > 0]
    for grupo, sel in (("todos", par), ("Lascar", [f for f in par if f["volcan"] == "Lascar"]),
                       ("otros", [f for f in par if f["volcan"] != "Lascar"])):
        if not sel:
            continue
        dm = [abs(f["k"]["M"] - f["k"]["C"]) for f in sel]
        dr = [abs(f["k"]["R"] - f["k"]["C"]) for f in sel]
        out["pares"][grupo] = {
            "n": len(sel), "km_mediana": _med([f["km"] for f in sel]),
            "abs_dk_M_mediana": _med(dm), "abs_dk_R_mediana": _med(dr),
            "abs_dk_M_por_km_mediana": _med([a / f["km"] for a, f in zip(dm, sel) if f["km"] > 0]),
            "abs_dk_R_por_km_mediana": _med([a / f["km"] for a, f in zip(dr, sel) if f["km"] > 0]),
            "M_mueve_mas_que_R": sum(a > b for a, b in zip(dm, dr)),
            "R_mueve_mas_que_M": sum(a < b for a, b in zip(dm, dr)),
            "k_C_mediana": _med([f["k"]["C"] for f in sel]),
            "k_C_entre_2_y_4": sum(2 <= f["k"]["C"] <= 4 for f in sel)}
    # (3) cruces del umbral: cuantas veces el disparo del Test 1 cambia con M y con R
    calc = [f for f in filas if f["k"]["C"] > 0]
    for x in ("M", "R"):
        out["cruces"][x] = {
            "de": len(calc),
            "dispara_C_no_" + x: sum(f["trig"]["C"] and not f["trig"][x] for f in calc),
            "dispara_" + x + "_no_C": sum(f["trig"][x] and not f["trig"]["C"] for f in calc)}
    # (4) las protegidas de Lascar: margen de k sobre el umbral en C y lo que hacen M y R
    for f in sorted(filas, key=lambda f: f["clave"]):
        if f["volcan"] == "Lascar" and f["prot"]:
            out["lascar_protegidas"].append({
                "clave": f["clave"], "cenit": f["cenit"], "km": f["km"],
                "k": f["k"], "trig": f["trig"], "fuente": f["fuente"], "pub": f["pub"]})
    return out


def imprimir(r, fh):
    p = lambda *a: print(*a, file=fh)  # noqa: E731
    p("Granulos con C, M y R medidos: %d" % r["n_granulos"])
    p("\n(1) Donde se calcula el Test 1 (k > 0 en C) y la k del ruido puro esperada por geometria")
    p("  %-6s %4s %10s %10s %8s %8s %10s" % ("cenit", "n", "calculado", "k_C med", "n_roi", "n_bg", "k_ruido"))
    for b, v in r["por_cenit"].items():
        p("  %-6s %4d %10d %10s %8s %8s %10s" % (b, v["n"], v["test1_calculado_en_C"], v["k_C_mediana"],
                                                v["n_roi_geometrico"], v["n_bg_geometrico"], v["k_ruido_esperado"]))
    p("\n(2) Cuanto se mueve k con MxD03 (M) y con el corrimiento al azar del mismo tamano en km (R)")
    for g, v in r["pares"].items():
        p("  %-7s n=%d  km med %.3f | |dk| M %.3f, R %.3f | |dk|/km M %.3f, R %.3f | M>R %d, R>M %d | "
          "k_C med %.2f, k_C entre 2 y 4: %d" % (g, v["n"], v["km_mediana"], v["abs_dk_M_mediana"],
                                                  v["abs_dk_R_mediana"], v["abs_dk_M_por_km_mediana"],
                                                  v["abs_dk_R_por_km_mediana"], v["M_mueve_mas_que_R"],
                                                  v["R_mueve_mas_que_M"], v["k_C_mediana"], v["k_C_entre_2_y_4"]))
    p("\n(3) Cruces del umbral (k = %.1f) respecto de C" % UMBRAL_K)
    for x, v in r["cruces"].items():
        p("  %s: %s" % (x, v))
    p("\n(4) Protegidas de Lascar: k y disparo en C, M y R")
    for f in r["lascar_protegidas"]:
        p("  %s cenit %5.2f corr %.3f km | k C %.2f M %.2f R %.2f | dispara %s | fuente %s | pub %s" % (
            f["clave"], f["cenit"], f["km"], f["k"]["C"], f["k"]["M"], f["k"]["R"],
            "".join("1" if f["trig"][x] else "0" for x in "CMR"), f["fuente"], f["pub"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--poblacion", default=str(AQUI.parent / "_s151_mxd03_etiquetas" / "poblacion.json"))
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    pob = json.loads(Path(a.poblacion).read_text(encoding="utf-8"))
    r = analizar(cargar(a.carpeta), pob)
    buf = io.StringIO()
    imprimir(r, buf)
    texto = buf.getvalue()
    sys.stdout.write(texto)
    if a.salida:
        Path(a.salida).write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    main()
