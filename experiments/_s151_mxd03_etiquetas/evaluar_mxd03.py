# Tarea 1.17: junta los JSON por volcan del probe y aplica el criterio pre-registrado en README.md.
# Corre en el job "agregar" del workflow y tambien en local sobre el artefacto bajado.
#
# Uso: python evaluar_mxd03.py <carpeta con Lascar.json, Lastarria.json, ...> [--salida resumen.json]
import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

# Criterio (README.md, fijado antes de correr)
POCO_PUB = 0.02          # publicaciones movidas estimadas / publicaciones MODIS del tramo
MUCHO_PUB = 0.05
K_MIN_PUB = 3            # "mucho" por publicaciones exige ademas 3 cambios observados (un solo granulo del
                         # estrato B pesa 25 a 50 records: un caso aislado no decide)
POCO_LAB_LO = 0.10       # cota inferior de Wilson de la tasa de cambio de etiqueta en el estrato A
MUCHO_LAB_LO = 0.20
N_MIN_A = 10             # el criterio por volcan solo mira volcanes con al menos 10 granulos A medidos
MAX_FALTAN = 0.20        # mas de 20 % de la muestra de un volcan sin medir -> INCOMPLETO
CONTROL_MAX = 0.10       # mas de 10 % del control cambia de etiqueta -> se anota
BANDA_KM = 3.0           # si mas de 10 % de los granulos se corre mas que la banda, la cifra es cota inferior
BANDA_FRAC = 0.10
BINES_CENIT = ((0, 20), (20, 35), (35, 50), (50, 91))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def _bin(z):
    if z is None:
        return "sin_cenit"
    for a, b in BINES_CENIT:
        if a <= z < b:
            return "%d-%d" % (a, min(b, 90))
    return "sin_cenit"


def evaluar(vols):
    """vols: {volcan: salida de probe_etiquetas.py}. Devuelve el resumen con el veredicto."""
    por_volcan, incompletos = {}, []
    E_pub = E_lab = E_lo = E_hi = 0.0
    K_pub = 0
    P_total = 0
    ctrl_n = ctrl_k = 0
    desp = []
    tabla = defaultdict(lambda: {"n": 0, "etiqueta": 0, "pub": 0, "desp_km": []})
    for vol, v in sorted(vols.items()):
        gr = v["granulos"]
        ok = [g for g in gr if g.get("estado") == "ok"]
        if gr and (len(gr) - len(ok)) / len(gr) > MAX_FALTAN:
            incompletos.append(vol)
        P_total += v.get("n_pub_tramo") or 0
        fila = {"N": v["N"], "n_muestra": len(gr), "n_medidos": len(ok)}
        for e in ("A", "B", "control"):
            s = [g for g in ok if g["estrato"] == e]
            k_lab = sum(g["comparacion"]["etiqueta"] != "igual" for g in s)
            k_pub = sum(g["comparacion"]["pub"] != "igual" for g in s)
            N = v["N"].get(e, 0)
            fila[e] = {"n": len(s), "k_etiqueta": k_lab, "k_pub": k_pub,
                       "wilson_etiqueta": [round(x, 3) for x in wilson(k_lab, len(s))],
                       "est_etiqueta": round(N * k_lab / len(s), 1) if s else None,
                       "est_pub": round(N * k_pub / len(s), 1) if s else None}
            if e in ("A", "B") and s:
                E_pub += N * k_pub / len(s)
                E_lab += N * k_lab / len(s)
                lo, hi = wilson(k_pub, len(s))
                E_lo += N * lo
                E_hi += N * hi
                K_pub += k_pub
            if e == "control":
                ctrl_n += len(s)
                ctrl_k += k_lab
        por_volcan[vol] = fila
        for g in ok:
            d = (g.get("desplazamiento") or {}).get("km")
            if d is not None:
                desp.append(d)
            cen = (g.get("c") or {}).get("cenit") or g.get("sensor_zenith_deg")
            sat = (g.get("sensor") or "?").replace("MODIS_", "")
            for clave in ((vol, sat, _bin(cen)), ("TODOS", sat, _bin(cen))):
                t = tabla[clave]
                t["n"] += 1
                t["etiqueta"] += g["comparacion"]["etiqueta"] != "igual"
                t["pub"] += g["comparacion"]["pub"] != "igual"
                if d is not None:
                    t["desp_km"].append(d)
    tabla_out = []
    for (vol, sat, b), t in sorted(tabla.items()):
        ds = sorted(t["desp_km"])
        tabla_out.append({"volcan": vol, "satelite": sat, "cenit": b, "n": t["n"],
                          "cambia_etiqueta": t["etiqueta"], "cambia_pub": t["pub"],
                          "desp_mediana_km": round(ds[len(ds) // 2], 2) if ds else None,
                          "desp_max_km": round(ds[-1], 2) if ds else None})
    frac_pub = E_pub / P_total if P_total else None
    lab_lo = {vol: f["A"]["wilson_etiqueta"][0] for vol, f in por_volcan.items() if f["A"]["n"] >= N_MIN_A}
    if incompletos:
        ver = "INCOMPLETO"
    elif (frac_pub is not None and frac_pub >= MUCHO_PUB and K_pub >= K_MIN_PUB) or any(x >= MUCHO_LAB_LO for x in lab_lo.values()):
        ver = "CAMBIA MUCHO"
    elif (frac_pub is not None and frac_pub < POCO_PUB) and all(x < POCO_LAB_LO for x in lab_lo.values()):
        ver = "CAMBIA POCO"
    else:
        ver = "INTERMEDIO"
    return {"veredicto": ver, "incompletos": incompletos,
            "publicaciones_movidas_estimadas": round(E_pub, 1),
            "publicaciones_movidas_intervalo_wilson": [round(E_lo, 1), round(E_hi, 1)],
            "publicaciones_movidas_observadas": K_pub,
            "etiquetas_movidas_estimadas": round(E_lab, 1),
            "publicaciones_modis_del_tramo": P_total,
            "fraccion_publicaciones_movidas": None if frac_pub is None else round(frac_pub, 4),
            "wilson_inferior_etiqueta_A": lab_lo,
            "control_cambia": bool(ctrl_n and ctrl_k / ctrl_n > CONTROL_MAX),
            "control": {"n": ctrl_n, "k_etiqueta": ctrl_k},
            "cota_inferior": bool(desp and sum(d > BANDA_KM for d in desp) / len(desp) > BANDA_FRAC),
            "por_volcan": por_volcan, "tabla_volcan_satelite_cenit": tabla_out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--salida", default=None)
    args = ap.parse_args()
    vols = {}
    for p in sorted(Path(args.carpeta).rglob("*.json")):
        d = json.load(open(p, encoding="utf-8"))
        if isinstance(d, dict) and "granulos" in d and "volcan" in d:
            vols[d["volcan"]] = d
    if not vols:
        sys.exit("no encontre salidas del probe en %s" % args.carpeta)
    r = evaluar(vols)
    texto = json.dumps(r, indent=1, ensure_ascii=False)
    if args.salida:
        Path(args.salida).write_text(texto, encoding="utf-8")
    print("VEREDICTO:", r["veredicto"], "| volcanes:", len(vols),
          "| publicaciones movidas estimadas: %s de %s" % (r["publicaciones_movidas_estimadas"],
                                                          r["publicaciones_modis_del_tramo"]),
          "| cota inferior:", r["cota_inferior"], "| control cambia:", r["control_cambia"])


if __name__ == "__main__":
    main()
