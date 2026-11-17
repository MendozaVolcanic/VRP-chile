# FICHA (SDA, CPLT 372): lector del A/B de fase de grilla (PREREGISTRO.md §4 a §6). Solo lee JSON; no es detección.
"""Aplica la regla sellada a los resultados de ab_fase.py.

Uso: python experiments/_s190_l1b_ab/leer_ab.py <carpeta con s190_parte*.json> [--salida veredicto.json]
La función `evaluar(items, poblacion)` es la regla; tests/test_ab_fase_s190.py la prueba con resultados sintéticos.
"""
import argparse
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BRAZOS_EVAL = ("A", "B", "C", "Z")
N_CALLA_FUERA = 12          # PREREGISTRO.md §2
N_CALLA_S185 = 6


def alerta(item, b):
    br = (item.get("brazos") or {}).get(b) or {}
    return (br.get("n_pix") or 0) > 0


def evento(item, b):
    """+1 ganancia, -1 daño, 0 nada (PREREGISTRO.md §4)."""
    al, cat = alerta(item, b), item["cat"]
    if cat == "calla":
        return 1 if al else 0
    if cat == "solo_via":
        return 0 if al else 1
    if cat == "ambos":
        return 0 if al else -1
    if cat == "rutina":
        return -1 if al else 0
    raise ValueError(cat)


def margen_publicado(item):
    return ((item.get("ref") or {}).get("publicado_celda_decisiva") or {}).get("margen")


def evaluar(items, poblacion):
    puntua = [i for i in items if i.get("rol") == "puntua"]
    replica = [i for i in items if i.get("rol") == "replica_s185"]
    validas = [i for i in puntua if i.get("ok") and i.get("reproduce")]
    excluidas = [{k: i.get(k) for k in ("volcan", "dt", "cat", "estrato", "error", "nota_granulo")}
                 for i in puntua if not (i.get("ok") and i.get("reproduce"))]
    n_val = Counter(i["estrato"] for i in validas)
    n_tot = Counter(i["estrato"] for i in puntua)
    peso = {e: poblacion[e] / n_val[e] for e in n_val}
    met = {}
    for b in BRAZOS_EVAL:
        G = sum(peso[i["estrato"]] for i in validas if evento(i, b) == 1)
        D = sum(peso[i["estrato"]] for i in validas if evento(i, b) == -1)
        met[b] = {"G": round(G, 2), "D": round(D, 2), "Net": round(G - D, 2),
                  "cambios": sum(1 for i in validas if alerta(i, b) != alerta(i, "A")),
                  "calla_recuperadas": sum(1 for i in validas if i["cat"] == "calla" and alerta(i, b)),
                  "eventos_sin_peso": {e: dict(Counter(evento(i, b) for i in validas if i["estrato"] == e)) for e in sorted(n_val)},
                  "ambos_protegidas_perdidas": [(i["volcan"], i["dt"]) for i in validas if i["cat"] == "ambos" and not alerta(i, b)
                                                and (i["ref"].get("mirova_vrp_mw") or 0) >= 1.0],
                  "rutinas_bajo_06_alertadas": [(i["volcan"], i["dt"], margen_publicado(i)) for i in validas
                                                if i["cat"] == "rutina" and alerta(i, b) and (margen_publicado(i) or 0) < 0.6]}
    rep_ok = [i for i in replica if i.get("ok")]
    rep_calla_B = sum(1 for i in rep_ok if i["cat"] == "calla" and alerta(i, "B"))
    frac = len(validas) / len(puntua) if puntua else 0.0
    v1 = (frac >= 0.90 and all(n_val[e] >= 0.8 * n_tot[e] for e in ("calla", "solo_via") if n_tot[e]))
    v2 = rep_calla_B >= 5
    v3 = met["B"]["cambios"] >= 1
    mB, mZ = met["B"], met["Z"]
    c = {"C1": not mB["ambos_protegidas_perdidas"], "C2": not mB["rutinas_bajo_06_alertadas"],
         "C3": mB["Net"] >= 3 and mB["G"] >= 2 * mB["D"], "C4": mB["calla_recuperadas"] >= 6, "C5": mB["Net"] - mZ["Net"] >= 3}
    if not (v1 and v2):
        veredicto = "SIN DATO"
    elif not v3:
        veredicto = "NO CUMPLE (sin efecto)"
    else:
        veredicto = "CUMPLE" if all(c.values()) else "NO CUMPLE"
    mC = met["C"]
    sospecha_c = (not mC["ambos_protegidas_perdidas"] and not mC["rutinas_bajo_06_alertadas"] and mC["Net"] >= 3
                  and mC["G"] >= 2 * mC["D"] and mC["calla_recuperadas"] >= 6 and mC["Net"] - mZ["Net"] >= 3 and mC["Net"] > mB["Net"])
    ratios = sorted(i["brazos"]["B"]["celda_decisiva"]["margen"] / i["brazos"]["A"]["celda_decisiva"]["margen"]
                    for i in validas if (i["brazos"].get("B") or {}).get("celda_decisiva")
                    and (i["brazos"]["A"].get("celda_decisiva") or {}).get("margen"))
    return {"veredicto": veredicto, "validez": {"V1": v1, "fraccion_valida": round(frac, 3), "V2": v2,
                                                 "replica_calla_B": rep_calla_B, "replica_medidas": len(rep_ok), "V3": v3},
            "criterios_B": c, "sospecha_C": sospecha_c, "metricas": met, "n_puntua": len(puntua), "n_validas": len(validas),
            "validas_por_estrato": dict(n_val), "pesos": {e: round(w, 2) for e, w in peso.items()}, "excluidas": excluidas,
            "replica": [{"dt": i["dt"], "cat": i["cat"], **{b: alerta(i, b) for b in BRAZOS_EVAL},
                         "margen": {b: ((i["brazos"].get(b) or {}).get("celda_decisiva") or {}).get("margen") for b in BRAZOS_EVAL}}
                        for i in rep_ok],
            "cociente_margen_B_A": {"n": len(ratios), "min": ratios[0] if ratios else None,
                                    "mediana": ratios[len(ratios) // 2] if ratios else None, "max": ratios[-1] if ratios else None},
            "por_volcan_B": {v: dict(Counter(evento(i, "B") for i in validas if i["volcan"] == v))
                             for v in sorted({i["volcan"] for i in validas})}}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    items = []
    for f in sorted(glob.glob(str(Path(a.carpeta) / "**" / "s190_parte*.json"), recursive=True)):
        items += json.load(open(f, encoding="utf-8"))
    man = json.load(open(AQUI / "manifiesto_s190.json", encoding="utf-8"))
    vistas = {(i["volcan"], i["l1b"]) for i in items}
    # una pasada del manifiesto que nunca llegó cuenta como no válida en el denominador (no se la puede ignorar callando)
    faltan = [{k: p[k] for k in ("volcan", "dt", "l1b", "cat", "estrato", "rol")} | {"ok": False, "error": "sin resultado"}
              for p in man["pasadas"] if (p["volcan"], p["l1b"]) not in vistas]
    r = evaluar(items + faltan, man["poblacion_por_estrato"])
    r["pasadas_del_manifiesto_sin_resultado"] = len(faltan)
    print(json.dumps(r, indent=1, ensure_ascii=False, default=str))
    if a.salida:
        json.dump(r, open(a.salida, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()
