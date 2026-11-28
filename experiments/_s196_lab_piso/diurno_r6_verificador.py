# -*- coding: utf-8 -*-
"""i03 (R6FN-102 y R6FN-110): causas de la cobertura desigual y efecto del MODIS diurno de producción.
1. Clasifica las noches como la vara (E.clasificar_noches) y, en cada noche desigual, separa la causa: pasadas de
   producción sin par que son de día (elevación > 0), pasadas nocturnas sin par (de cada lado), validez distinta.
2. Re-corre E.veredicto con el MODIS diurno fuera de producción (lo que el almacén del laboratorio rechaza) y compara
   votos, clases, cobertura y persistencia con la corrida tal cual.
3. Lista las pasadas nocturnas sin par por fecha y sensor (residuo)."""
import collections
import io
import json
import os
import pickle
import sys
from pathlib import Path

pass  # la salida utf-8 la fija i02_cargar al importarse
os.environ["PATH"] = r"C:\Program Files\nodejs;" + os.environ.get("PATH", "")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from i02_cargar import cargar_E, INS  # noqa: E402

FIN = "2026-11-26"


def causas(E, lab, prod):
    por = collections.defaultdict(lambda: ([], []))
    for p in lab:
        por[(p["vol"], E._noche(p["dt"]))][0].append(p)
    for p in prod:
        por[(p["vol"], E._noche(p["dt"]))][1].append(p)
    out = collections.Counter()
    sin_par = []
    for k, (l, pr) in por.items():
        pares, sl, sp = E._parear_pasadas(l, pr)
        inval = any(bool(a["invalida"]) != bool(b["invalida"]) for a, b in pares)
        if not (sl or sp or inval):
            continue
        sp_dia = [b for b in sp if b["elev"] > 0]
        sp_noc = [b for b in sp if b["elev"] <= 0]
        tags = []
        if sp_dia:
            tags.append("prod_dia_sin_par")
        if sp_noc:
            tags.append("prod_noche_sin_par")
        if sl:
            tags.append("lab_sin_par")
        if inval:
            tags.append("validez_distinta")
        out["+".join(tags)] += 1
        for b in sp_noc:
            sin_par.append(("prod_sin_lab", b["vol"], b["sensor"], b["dt"].strftime("%Y-%m-%d %H:%M"), b["invalida"]))
        for a in sl:
            sin_par.append(("lab_sin_prod", a["vol"], a["sensor"], a["dt"].strftime("%Y-%m-%d %H:%M"), a["invalida"]))
        for a, b in pares:
            if bool(a["invalida"]) != bool(b["invalida"]):
                sin_par.append(("validez_distinta", a["vol"], a["sensor"], a["dt"].strftime("%Y-%m-%d %H:%M"),
                                "lab=%s prod=%s" % (a["invalida"], b["invalida"])))
    return out, sin_par


def resumen(v):
    return {"veredicto": v["veredicto"], "con_poder": v["volcanes_con_poder"], "con_exceso": v["volcanes_con_exceso"],
            "nhi": {k: (r["n_S"], r["n_N"], r["alertas_S"], r["alertas_N"], r["p"], r["voto"]) for k, r in v["nhi"].items()},
            "control_nulo": v["control"]["nulo"],
            "control_n": {k: d["n_volcanes_exceso"] for k, d in v["control"]["desplazamientos"].items()},
            "persistencia": {k: v["persistencia"][k] for k in ("n_extras", "frac_obs", "frac_sorteo_media", "p", "supera")},
            "cobertura_frac": {k: c["frac"] for k, c in v["cobertura"].items()}}


def main():
    E = cargar_E()
    d = pickle.load(open(AQUI / "i02_pasadas.pkl", "rb"))
    lab, prod = d["lab"], d["prod"]
    nhi = E.cargar_nhi(INS / "nhi")
    anclas = E.anclas_reales()

    c, sin_par = causas(E, lab, prod)
    print("== 1. noches desiguales por causa (todas las noches de los 10 volcanes)")
    for k, n in c.most_common():
        print("  %-45s %d" % (k, n))
    print("  total desiguales:", sum(c.values()))

    base = E.veredicto(E.clasificar_noches(lab, prod), nhi, anclas, fin=FIN)
    prod_noche = [p for p in prod if not (p["sensor"].startswith("MODIS") and p["elev"] > 0)]
    print("\n== 2. producción sin MODIS diurno: quitadas %d pasadas" % (len(prod) - len(prod_noche)))
    corr = E.veredicto(E.clasificar_noches(lab, prod_noche), nhi, anclas, fin=FIN)
    rb, rc = resumen(base), resumen(corr)
    print("tal cual :", json.dumps(rb, ensure_ascii=False))
    print("sin día  :", json.dumps(rc, ensure_ascii=False))
    for k in rb:
        if rb[k] != rc[k]:
            print("  cambia", k)
    c2, sin_par2 = causas(E, lab, prod_noche)
    print("  noches desiguales sin MODIS diurno, por causa:", dict(c2), "total", sum(c2.values()))
    with open(AQUI / "i03_veredicto_sin_dia.json", "w", encoding="utf-8") as fh:
        json.dump(corr, fh, ensure_ascii=False, indent=1, default=str)

    print("\n== 3. residuo nocturno (sin el diurno): pasadas sin par o con validez distinta, por fecha y sensor")
    cnt = collections.Counter((t, s[:10] if False else x[3][:10], x[2]) for x in sin_par2 for t, s in [(x[0], x[3])])
    for (t, f, s), n in sorted(cnt.items()):
        print("  %-17s %s %-16s %d" % (t, f, s, n))
    print("  detalle (primeros 40):")
    for x in sorted(sin_par2, key=lambda x: (x[3], x[1]))[:40]:
        print("   ", x)


if __name__ == "__main__":
    main()
