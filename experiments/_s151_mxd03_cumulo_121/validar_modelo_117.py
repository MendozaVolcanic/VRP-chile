# Tarea 1.21, punto 5 del encargo: el modelo de corrimiento con el termino de la traza, contra lo que
# midio la 1.17 (run 38894508138). Solo lectura de los artefactos del run.
#
# POR QUE. La banda de la 1.17 salio corta en cenit bajo (87 de 470 granulos sobre banda + 1 km) porque
# el modelo de #828 no tenia el corrimiento a lo largo de la traza. Antes de usar el modelo corregido
# hay que comprobar que predice lo medido, con la linea del crater que el probe 1.17 si guardo
# (`desplazamiento.linea`).
#
# Uso: gh run download 38894508138 -D <carpeta>   (una vez)
#      python validar_modelo_117.py <carpeta> [--poblacion ../_s151_mxd03_etiquetas/poblacion.json]
import argparse
import json
import math
import statistics as st
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import modelo_corrimiento as MC  # noqa: E402

BINES = ((0, 20), (20, 35), (35, 50), (50, 91), (0, 30), (0, 91))


def filas_117(carpeta, pob):
    pred = {(v, g["clave"]): g for v, d in pob["volcanes"].items() for g in d["muestra"]}
    out = []
    for p in sorted(Path(carpeta).rglob("*.json")):
        d = json.load(open(p, encoding="utf-8"))
        if not (isinstance(d, dict) and "granulos" in d and "job" in d):
            continue
        for g in d["granulos"]:
            if g.get("estado") != "ok":
                continue
            f = pred[(d["volcan"], g["clave"])]
            z, az, sen = f["sensor_zenith_deg"], f["sensor_azimuth_deg"], f["sensor"]
            if z is None or az is None:
                continue
            lin = g["desplazamiento"]["linea"]
            out.append({"cenit": z, "medido": g["desplazamiento"]["km"],
                        "viejo": MC.S.corrimiento_predicho(z, az, sen),
                        "nuevo": MC.corrimiento_predicho_traza(z, az, sen, lin),
                        "peor": MC.corrimiento_predicho_traza(z, az, sen, None)})
    return out


def _r(xs, ys):
    mx, my = st.mean(xs), st.mean(ys)
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else float("nan")


def tabla(filas, margen=1.0):
    out = []
    for lo, hi in BINES:
        rr = [f for f in filas if lo <= f["cenit"] < hi]
        if not rr:
            continue
        out.append({"cenit": "%d-%d" % (lo, min(hi, 90)), "n": len(rr),
                    "medido_mediana": round(st.median(f["medido"] for f in rr), 3),
                    "viejo_mediana": round(st.median(f["viejo"] for f in rr), 3),
                    "nuevo_mediana": round(st.median(f["nuevo"] for f in rr), 3),
                    "residuo_abs_mediana": round(st.median(abs(f["medido"] - f["nuevo"]) for f in rr), 3),
                    "r_nuevo": round(_r([f["nuevo"] for f in rr], [f["medido"] for f in rr]), 3),
                    "exceden_viejo_mas_1": sum(f["medido"] > f["viejo"] + margen for f in rr),
                    "exceden_nuevo_mas_1": sum(f["medido"] > f["nuevo"] + margen for f in rr),
                    "exceden_peor_mas_1": sum(f["medido"] > f["peor"] + margen for f in rr)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--poblacion", default=str(AQUI.parent / "_s151_mxd03_etiquetas" / "poblacion.json"))
    a = ap.parse_args()
    pob = json.load(open(a.poblacion, encoding="utf-8"))
    filas = filas_117(a.carpeta, pob)
    print("granulos medidos con angulos:", len(filas))
    for t in tabla(filas):
        print(json.dumps(t, ensure_ascii=False))


if __name__ == "__main__":
    main()
