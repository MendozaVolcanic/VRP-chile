# -*- coding: utf-8 -*-
"""Verificador del evaluador de D25 (S157). Casos de punta a punta sembrados por el verificador, con la MISMA
maquinaria de probar_evaluar_d25.py (se importa, no se copia) y el evaluador real o una copia mutada en
D:\\vrp-trabajo\\temporales\\verif_eval\\ (con AQUI fijado a la carpeta del repo, para que RAIZ y la referencia
congelada sean las de verdad). No toca ningún archivo del repo.

  A corte_mut   el caso "corte" de las pruebas con CORTE_CENIT = 50 (defecto contrario sembrado): ¿cambia?
  B masc        D mejora VIIRS 750 a mitad de camino Y publica en 30 negativos de VIIRS 375; calibración sellada
                ("ambos") y "mejora": ¿P2 PIERDE da NO CUMPLE o queda INDECIDIBLE?
  C cob         a K, K' y D les falta el 20 % de las pasadas VIIRS 375 de Lascar (por igual): ¿la cobertura contra
                histórico y producción lo ve?
  D version     una protegida A de D con product_version distinta: ¿version_ok cae?
  E snpp        cuántas protegidas sólo OCR de Suomi NPP publicadas hay en la ventana de prueba (la prueba "snpp"
                necesita al menos una o falla en la línea base)
  F calib_par   la prueba de unidad de calibración con el signo POR PAR (como antes del cambio): ¿la prueba la ve?
  G snpp_mut    el caso "snpp" con la exclusión de Suomi NPP quitada del evaluador: ¿veta?
  H bloq_mut    el caso "bloq_mejora" con el bloqueo quitado: ¿el caso falla?

Uso: python v2_casos.py D:\\vrp-trabajo\\temporales\\verif_eval\\v2  > v2_salida.txt
"""
import copy
import json
import shutil
import sys
from pathlib import Path

import numpy as np

REPO = Path(r"D:\vrp-trabajo\s157-prereg-d25")
CARPETA = REPO / "experiments" / "_s157_prereg_d25"
sys.path.insert(0, str(CARPETA))
import probar_evaluar_d25 as PR  # noqa: E402  (lee sys.argv[1] como TMP)

X = PR.X
TMP = PR.TMP
ORIG = PR.AQUI


def copia_mutada(nombre, a, b):
    d = TMP / "evalcopias" / nombre
    d.mkdir(parents=True, exist_ok=True)
    src = (CARPETA / "evaluar_d25.py").read_text(encoding="utf-8")
    src = src.replace("AQUI = Path(__file__).resolve().parent", "AQUI = Path(r\"%s\")" % CARPETA)
    if a is not None:
        assert src.count(a) == 1, (nombre, src.count(a))
        src = src.replace(a, b)
    (d / "evaluar_d25.py").write_text(src, encoding="utf-8")
    return d


def con(dirx, fn):
    PR.AQUI = dirx
    try:
        return fn()
    finally:
        PR.AQUI = ORIG


def mv(res, r="SN"):
    return {k: v for k, v in res["por_regla"][r]["veredicto"].items() if k.startswith("M|")}


def main():
    datos = PR.base_k()
    base = PR.cargar(datos, PR.VOLS, *PR.V1)
    D0 = PR.con_huella(base)
    arms0 = {"K": base, "G": copy.deepcopy(base), "D": D0}
    mej = ["--calibracion", "mejora"]
    res = PR.correr("nulo", PR.escribir("nulo", arms0), "V1", *PR.V1)
    t = PR.tabla_kd("nulo")
    print("nulo: estado %s cobertura_ok %s" % (res["estado"], res["cobertura_ok"]), flush=True)

    # ---- A corte_mut
    sk = lambda k, c: "|VIIRS375|" in k and k.split("|")[0] not in X.KERNEL  # noqa: E731
    sel = PR.pares(t, lambda k, c: sk(k, c) and 40 < (c["z"] or 0) <= 50)
    arms = dict(arms0, D=PR.con_huella(PR.mover(base, sel, "mitad")))
    dmut = copia_mutada("corte50", "CORTE_CENIT = 40.0", "CORTE_CENIT = 50.0")
    r_m = con(dmut, lambda: PR.correr("corte_mut", PR.escribir("corte_mut", arms), "V1", *PR.V1, extra=mej))
    i = r_m["por_regla"]["SN"]["info"]["M|VIIRS375|sin_kernel|z<=40"]
    print("A corte_mut (CORTE 50): estado %s | M sin_kernel z<=40 %s (n %d, d mediana %+.4f, ic %s) | n movidos 40-50° %d"
          % (r_m["estado"], mv(r_m)["M|VIIRS375|sin_kernel|z<=40"], i["n"], i.get("d_mediana", float("nan")), i.get("ic95"), len(sel)), flush=True)
    paso = r_m["estado"].startswith("SIN EFECTO") and mv(r_m)["M|VIIRS375|sin_kernel|z<=40"] != "MEJORA"
    print("   el caso 'corte' de las pruebas %s con la mutación" % ("PASA (no la ve)" if paso else "FALLA (la ve)"), flush=True)

    # ---- B masc
    sel750 = PR.pares(t, lambda k, c: "|VIIRS750|" in k)
    Dp = PR.con_huella(PR.mover(base, sel750, "mitad"))
    negs = [k for k, v in t.items() if "|VIIRS375|" in k and len(v) == 2 and v["control"]["lab"] == "neg_limpio" and not v["control"]["pub"]][:30]
    for k in negs:
        r = PR.buscar(Dp, k)
        r["distance_class"] = "summit"
        r["primary_cluster"] = {"n_pixels": 1, "vrp_mw": 0.5, "centroid_lat": r.get("volcano_lat"), "centroid_lon": r.get("volcano_lon"),
                                "centroid_dist_km": 0.5}
        r["f5_core_vrp_mw"] = 0.5
        r["diag_bg_vecinos_n_sin_vecinos"] = 0
    raices = PR.escribir("masc", dict(arms0, D=Dp))
    r_s = PR.correr("masc_sellada", raices, "V1", *PR.V1)
    r_e = PR.correr("masc_mejora", raices, "V1", *PR.V1, extra=mej)
    for nom, rr in (("sellada (ambos)", r_s), ("mejora", r_e)):
        print("B masc %s: P2 V375 %s | M V750 %s | estado %s" % (nom, rr["por_regla"]["SN"]["veredicto"]["P2|VIIRS375"],
              {k: v for k, v in mv(rr).items() if "750" in k}, rr["estado"]), flush=True)

    # ---- C cob
    arms = copy.deepcopy(arms0)
    las = [r for r in arms["K"]["Lascar"] if X.bp.bucket(r.get("sensor")) == "VIIRS375"]
    quitar = {r["datetime_utc"] for r in las[::5]}
    for n in ("K", "G", "D"):
        arms[n]["Lascar"] = [r for r in arms[n]["Lascar"] if not (X.bp.bucket(r.get("sensor")) == "VIIRS375" and r["datetime_utc"] in quitar)]
    r_c = PR.correr("cob", PR.escribir("cob", arms), "V1", *PR.V1)
    print("C cob: quitadas %d de %d pasadas VIIRS 375 de Lascar en los tres brazos -> cobertura_ok %s, estado %s"
          % (len(quitar), len(las), r_c["cobertura_ok"], r_c["estado"]), flush=True)

    # ---- D version (y E snpp)
    import evaluar_fk as E
    cfg = dict(X.VENTANAS["V1"], desde=PR.V1[0], hasta=PR.V1[1])
    prot = E.proteccion(set(t), E.archivos_ref(cfg, TMP / "nulo" / "tmp"), *PR.V1)
    publ = [(k, v["control"]) for k, v in t.items() if len(v) == 2 and v["control"]["pub"] and prot[k]["A"]]
    snpp = [k for k, c in publ if E.ocr_snpp(k, c, prot)]
    print("E snpp: protegidas A publicadas por K en la ventana de prueba %d, de ellas sólo OCR de Suomi NPP %d (%s)"
          % (len(publ), len(snpp), snpp[:3]), flush=True)
    k0 = [k for k, c in publ if not E.ocr_snpp(k, c, prot)][0]
    Dv = copy.deepcopy(D0)
    rv = PR.buscar(Dv, k0)
    rv["product_version"] = "nrt" if rv.get("product_version") != "nrt" else "standard"
    r_v = PR.correr("version", PR.escribir("version", dict(arms0, D=Dv)), "V1", *PR.V1)
    print("D version: %s cambiada en D -> version_ok %s, estado %s" % (k0, r_v["version_ok"], r_v["estado"]), flush=True)

    # ---- G snpp_mut
    if snpp:
        dmut = copia_mutada("snpp", 'if excluir and E.ocr_snpp(k, c, prot):\n                snpp.append(k); continue',
                            'if False:\n                snpp.append(k); continue')
        Ds = PR.con_huella(base); PR.apagar(PR.buscar(Ds, snpp[0]))
        r_g = con(dmut, lambda: PR.correr("snpp_mut", PR.escribir("snpp_mut", dict(arms0, D=Ds)), "V1", *PR.V1))
        r_g0 = PR.correr("snpp_orig", PR.escribir("snpp_orig", dict(arms0, D=Ds)), "V1", *PR.V1)
        print("G snpp: original P1 V375 %s | sin la exclusión P1 V375 %s (clave %s)" % (
            r_g0["por_regla"]["SN"]["veredicto"]["P1|VIIRS375"], r_g["por_regla"]["SN"]["veredicto"]["P1|VIIRS375"], snpp[0]), flush=True)

    # ---- H bloq_mut
    sel = PR.pares(t, lambda k, c: sk(k, c) and (c["z"] or 0) > 40)
    dmut = copia_mutada("bloq", 'elif modo == "bloquea" and r == "MEJORA":', "elif False:")
    r_h = con(dmut, lambda: PR.correr("bloq_mut", PR.escribir("bloq_mut", dict(arms0, D=PR.con_huella(PR.mover(base, sel, "mitad")))), "V1", *PR.V1, extra=mej))
    print("H bloq_mut: M sin_kernel z>40 %s, estado %s (el caso bloq_mejora exige NEUTRO y SIN EFECTO)" % (
        mv(r_h)["M|VIIRS375|sin_kernel|z>40"], r_h["estado"]), flush=True)

    # ---- F calib_par (unidad, como en probar_evaluar_d25.py pero con signo por par)
    rng = np.random.default_rng(7)
    P, bloques = [], []
    for noche in range(15):
        e = abs(rng.normal(0, 0.05))
        for _ in range(10):
            P.append({"k": 1.0, "m": 3.0, "d": 10 ** e}); bloques.append(noche)
    Wp, Wb = X.pesos_pasada(len(P)), X.pesos_bloque(bloques)
    fm_p, _, _ = X.calibrar(P, Wp)            # signo por par
    fm_b, _, _ = X.calibrar(P, Wb)            # signo por par, bootstrap por bloques
    fm_pb, _, _ = X.calibrar(P, Wp, bloques=bloques)
    fm_bb, _, _ = X.calibrar(P, Wb, bloques=bloques)
    print("F calib: falsos MEJORA | signo por par: boot por pasada %.3f, por bloques %.3f | signo por bloque: por pasada %.3f, por bloques %.3f"
          % (fm_p, fm_b, fm_pb, fm_bb), flush=True)


if __name__ == "__main__":
    main()
