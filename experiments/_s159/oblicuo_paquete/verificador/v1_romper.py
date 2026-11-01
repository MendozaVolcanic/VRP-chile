# -*- coding: utf-8 -*-
"""S159, verificador del frente «el paquete de MIROVA y el déficit oblicuo». Sólo lectura de artefactos ya en disco.

POR QUÉ. El informe afirma que el oráculo (código de MIROVA en su grilla) da 0,996 contra MIROVA sobre 50° de cenit.
Antes de leerlo como «reproducimos el fenómeno» hay que descartar que la coincidencia sea tautológica o de selección.

Pregunta 1 del instrumento (si lo medido estuviera roto, ¿se vería?): el control de barajado empareja el oráculo de
una pasada con el MIROVA de OTRA pasada del mismo volcán (y de la misma noche, A109). Si la coincidencia fuera
«en cualquier caso» (ambos saturan, o el volcán da siempre lo mismo), la razón barajada también daría ~1 y estrecha.
Pregunta 2 (instrumento muerto): cada celda declara su n; n 0 = SIN DATO. Control positivo: K x 1,2 mueve la razón
x1,2; y el barajado de K (que NO reproduce a MIROVA) tiene que dar algo tan disperso como el pareado de K.
Denominador: alertas que deciden (lab pos, decide), VIIRS 750 nocturno, 2026-04-01 a 2026-10-21 sin 18-19 oct, ok.
Uso: python v1_romper.py
"""
from __future__ import annotations

import collections
import csv
import glob
import io
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
N = AQUI.parents[1] / "n"
ROOT = AQUI.parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402

ART = r"D:\vrp-trabajo\temporales\s159_n\run_39682867040"
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


def q(xs):
    if len(xs) == 0:
        return "SIN DATO (n=0)"
    a = np.asarray(xs, float)
    return (f"med {np.median(a):.3f} [{np.quantile(a, .25):.3f}, {np.quantile(a, .75):.3f}] n={len(a)}"
            f" | en [0,9;1,1]: {int(((a >= 0.9) & (a <= 1.1)).sum())}/{len(a)}")


def alerta_o(o, inner):
    if not o or not o.get("npix") or (o.get("vrp_mw") or 0) <= 0:
        return False
    return max(o["pixeles"], key=lambda p: p[4])[3] <= inner


def main():
    obj = {o["id"]: o for o in json.loads((N / "objetivos_n.json").read_text(encoding="utf-8"))}
    tab = {int(r["id"]): r for r in csv.DictReader(open(N / "tabla_por_pasada.csv", encoding="utf-8"))}
    res = {}
    for f in sorted(glob.glob(ART + r"\*\resultados_*.json")):
        for r in json.loads(Path(f).read_text(encoding="utf-8")):
            if r.get("estado") == "ok" or r["id"] not in res:
                res[r["id"]] = r
    inner = B.inner_desde_html()
    pos = [i for i, o in obj.items() if o["lab"] == "pos" and o["decide"] and (res.get(i) or {}).get("estado") == "ok"
           and o["clase"] != "diurna"]
    pr(f"alertas que deciden ok: {len(pos)}")
    Z = {i: res[i]["geometria_centro"]["sensor_zenith"] for i in pos}
    alto = [i for i in pos if Z[i] > 50]
    pr(f"sobre 50°: {len(alto)}; por volcán {collections.Counter(obj[i]['volcan'] for i in alto)}")

    def K(i):  # crudo desde el artefacto, no desde la tabla de N
        rec = (res[i].get("brazos") or {}).get("K", {}).get("record") or {}
        return (rec.get("primary_cluster") or {}).get("vrp_mw")
    kd = [i for i in pos if tab[i]["K_pc"] not in ("", None) and K(i) is not None
          and abs(float(tab[i]["K_pc"]) - K(i)) > 1e-6]
    pr(f"control: K_pc de la tabla de N contra el record crudo del artefacto: {len(kd)} discrepancias")

    def O(i, var="geo_linear"):
        o = res[i]["oraculo"].get(var)
        return o["vrp_mw"] if alerta_o(o, inner[obj[i]["volcan"]]) else None
    Kp = lambda i: tab[i]["K_pub"] == "True"
    Fp = lambda i: tab[i]["F_pub"] == "True"
    M = {i: obj[i]["mirova_vrp"] for i in pos}

    # 1. fuente y precisión del VRP de MIROVA
    pr("\n== 1. fuente del VRP de MIROVA (filas del scraper pareadas a cada alerta)")
    for etq, ss in (("todas", pos), (">50", alto)):
        src = collections.Counter("+".join(sorted({m["source"] for m in obj[i]["mirova"]})) for i in ss)
        nfil = collections.Counter(len(obj[i]["mirova"]) for i in ss)
        dec = collections.Counter(len(repr(float(M[i])).split(".")[1]) if "." in repr(float(M[i])) else 0 for i in ss)
        pr(f"   {etq}: fuente {dict(src)} | filas por alerta {dict(nfil)} | decimales del VRP {dict(dec)}")
    pr("   dt_ref_s >50: " + str(sorted(obj[i]["dt_ref_s"] for i in alto)))

    # 2. mismo subconjunto sobre 50°
    pr("\n== 2. sobre 50°, MISMO subconjunto (K publica, F publica y O detecta)")
    comun = [i for i in alto if Kp(i) and Fp(i) and O(i)]
    for b, f in (("K", lambda i: float(tab[i]["K_pc"])), ("F", lambda i: float(tab[i]["F_pc"])), ("O", O)):
        pr(f"   {b}: {q([f(i) / M[i] for i in comun])}")
    pr("   sin condicionar (no publica / no detecta = 0):")
    for b, ok, f in (("K", Kp, lambda i: float(tab[i]["K_pc"])), ("F", Fp, lambda i: float(tab[i]["F_pc"])),
                     ("O", lambda i: O(i) is not None, O)):
        pr(f"   {b}: {q([(f(i) if ok(i) else 0.0) / M[i] for i in alto])}")
    pr("   Chillán >50 sin condicionar:")
    ch = [i for i in alto if obj[i]["volcan"] == "NevadosDeChillan"]
    for b, ok, f in (("K", Kp, lambda i: float(tab[i]["K_pc"])), ("O", lambda i: O(i) is not None, O)):
        pr(f"   {b}: {q([(f(i) if ok(i) else 0.0) / M[i] for i in ch])}")

    # 3. redondeo de MIROVA a 2 decimales: ¿la dispersión de O cabe en el redondeo?
    pr("\n== 3. dispersión de O/MIROVA contra el error de redondeo de MIROVA (±0,005 MW)")
    od = [i for i in pos if O(i)]
    dentro = sum(abs(O(i) - M[i]) <= 0.005 + 1e-9 for i in od)
    pr(f"   |O - MIROVA| <= 0,005 MW (indistinguible del redondeo): {dentro} de {len(od)}")
    dentro_b = 0
    for i in od:
        b = res[i]["oraculo"]["geo_linear"].get("vrp_banda") or [O(i), O(i)]
        if b[0] - 0.005 - 1e-9 <= M[i] <= b[1] + 0.005 + 1e-9:
            dentro_b += 1
    pr(f"   MIROVA dentro de la banda de triangulación del oráculo (±0,005): {dentro_b} de {len(od)}")
    for etq, ss in (("<=50", [i for i in od if Z[i] <= 50]), (">50", [i for i in od if Z[i] > 50])):
        anch = [(res[i]["oraculo"]["geo_linear"]["vrp_banda"][1] / res[i]["oraculo"]["geo_linear"]["vrp_banda"][0])
                for i in ss if res[i]["oraculo"]["geo_linear"].get("vrp_banda")
                and res[i]["oraculo"]["geo_linear"]["vrp_banda"][0] > 0]
        pr(f"   ancho de la banda del oráculo (max/min, 20 semillas) {etq}: med {np.median(anch):.3f} max {max(anch):.3f} n={len(anch)}")

    # 4. barajado (A110): O de la pasada i contra MIROVA de otra pasada j
    pr("\n== 4. control de barajado: razón brazo(i) / MIROVA(j), j != i")
    rng = np.random.default_rng(159)

    def barajar(ids, f, grupo, reps=200):
        xs = []
        g = collections.defaultdict(list)
        for i in ids:
            g[grupo(i)].append(i)
        for _ in range(reps):
            for k, ss in g.items():
                if len(ss) < 2:
                    continue
                perm = rng.permutation(ss)
                # derangement simple: rotar la permutación una posición
                for a, b in zip(perm, np.roll(perm, 1)):
                    xs.append(f(a) / M[b])
        return xs
    for etq, ids in (("todas", pos), (">50", alto), ("Chillán", [i for i in pos if obj[i]["volcan"] == "NevadosDeChillan"])):
        oid = [i for i in ids if O(i)]
        kid = [i for i in ids if Kp(i)]
        pr(f"   [{etq}] O pareado:                 {q([O(i) / M[i] for i in oid])}")
        pr(f"   [{etq}] O barajado mismo volcán:   {q(barajar(oid, O, lambda i: obj[i]['volcan']))}")
        pr(f"   [{etq}] K pareado:                 {q([float(tab[i]['K_pc']) / M[i] for i in kid])}")
        pr(f"   [{etq}] K barajado mismo volcán:   {q(barajar(kid, lambda i: float(tab[i]['K_pc']), lambda i: obj[i]['volcan']))}")
    # misma noche, otra pasada (A109): fecha local de la noche = fecha UTC (pasadas 04-08 UTC)
    noche = lambda i: (obj[i]["volcan"], obj[i]["hora_utc"][:10])
    oid = [i for i in pos if O(i)]
    pares = []
    g = collections.defaultdict(list)
    for i in oid:
        g[noche(i)].append(i)
    for k, ss in g.items():
        for a in ss:
            for b in ss:
                if a != b:
                    pares.append((a, b))
    pr(f"   O(i)/MIROVA(j) misma noche y volcán, otra pasada (A109): {q([O(a) / M[b] for a, b in pares])}")
    pr(f"   O(i)/MIROVA(i) en esas mismas pasadas:                  {q(sorted({O(a) / M[a] for a, b in pares}))}")
    pr(f"   MIROVA(i)/MIROVA(j) misma noche (variabilidad real del volcán): {q([M[a] / M[b] for a, b in pares])}")

    # 5. invariancia con el cenit (prueba física, no de réplica): pares de la misma noche con cenit distinto
    pr("\n== 5. misma noche y volcán, pasada MÁS oblicua / MENOS oblicua (dif. de cenit >= 15°); n = pares")
    filas = []
    gg = collections.defaultdict(list)
    for i in pos:
        gg[noche(i)].append(i)
    for k, ss in gg.items():
        for a in ss:
            for b in ss:
                if Z[a] - Z[b] >= 15:
                    filas.append((a, b))
    pr(f"   pares: {len(filas)}; volcanes {collections.Counter(obj[a]['volcan'] for a, _ in filas)}")
    rM = [M[a] / M[b] for a, b in filas]
    rK = [float(tab[a]["K_pc"]) / float(tab[b]["K_pc"]) for a, b in filas if Kp(a) and Kp(b) and float(tab[b]["K_pc"]) > 0]
    rO = [O(a) / O(b) for a, b in filas if O(a) and O(b)]
    pr(f"   MIROVA oblicua/menos: {q(rM)}")
    pr(f"   K      oblicua/menos: {q(rK)}")
    pr(f"   O      oblicua/menos: {q(rO)}")
    pr(f"   K/MIROVA de la oblicua dividido por K/MIROVA de la menos oblicua: "
       f"{q([(float(tab[a]['K_pc']) / M[a]) / (float(tab[b]['K_pc']) / M[b]) for a, b in filas if Kp(a) and Kp(b)])}")
    for a, b in filas:
        pr(f"     {obj[a]['volcan'][:10]:10s} {obj[a]['hora_utc']} z{Z[a]:.1f} M{M[a]:.2f} K{tab[a]['K_pc']} O{O(a)}"
           f"  vs  {obj[b]['hora_utc'][11:]} z{Z[b]:.1f} M{M[b]:.2f} K{tab[b]['K_pc']} O{O(b)}")

    # 6. las 36 que el oráculo no detecta
    pr("\n== 6. alertas que el oráculo GEO lineal no detecta")
    nd = [i for i in pos if not O(i)]
    pr(f"   n={len(nd)} por volcán {dict(collections.Counter(obj[i]['volcan'] for i in nd))}")
    mot = collections.Counter()
    for i in nd:
        o = res[i]["oraculo"]["geo_linear"]
        s = res[i]["oraculo"].get("geo_linear_anillo_sensible") or {}
        if not o.get("npix"):
            why = "O sin píxeles"
        else:
            pk = max(o["pixeles"], key=lambda p: p[4])
            why = f"O con píxeles, pico a {pk[3]} km > inner {inner[obj[i]['volcan']]}"
        sdet = alerta_o(s, inner[obj[i]["volcan"]])
        caja = None
        if s.get("npix"):
            pk = max(s["pixeles"], key=lambda p: p[4])
            caja = (pk[2], pk[3])
        mot[(obj[i]["volcan"], why.split(",")[0], "S detecta" if sdet else "S no", None if caja is None else caja[0])] += 1
    for k, v in sorted(mot.items(), key=lambda kv: -kv[1]):
        pr(f"   {v:3d}  {k}  (último campo: valor de caja del píxel pico en S; 1 = anillo, 2 = cumbre)")
    pcc_tup = [i for i in pos if obj[i]["volcan"] in ("PuyehueCordonCaulle", "Tupungatito")]
    pr(f"   PCC+Tupungatito en la población: {len(pcc_tup)}; detectadas por O: {sum(bool(O(i)) for i in pcc_tup)}")
    pr(f"   cenit de las no detectadas: <=25 {sum(Z[i] <= 25 for i in nd)}, 25-40 {sum(25 < Z[i] <= 40 for i in nd)},"
       f" 40-50 {sum(40 < Z[i] <= 50 for i in nd)}, >50 {sum(Z[i] > 50 for i in nd)}")
    pr(f"   cenit de PCC+Tup: <=25 {sum(Z[i] <= 25 for i in pcc_tup)}, 25-40 {sum(25 < Z[i] <= 40 for i in pcc_tup)},"
       f" 40-50 {sum(40 < Z[i] <= 50 for i in pcc_tup)}, >50 {sum(Z[i] > 50 for i in pcc_tup)}")

    # 7. ejemplo 159 desde el artefacto crudo
    pr("\n== 7. ejemplo id 159 desde el artefacto crudo")
    r = res[159]
    pr(f"   {obj[159]['volcan']} {obj[159]['hora_utc']} cenit centro {r['geometria_centro']['sensor_zenith']:.2f}"
       f" record {r['brazos']['K']['record']['sensor_zenith_deg']} | K {K(159)} F "
       f"{r['brazos']['F']['record']['primary_cluster']['vrp_mw']} O {r['oraculo']['geo_linear']['vrp_mw']:.3f}"
       f" banda {r['oraculo']['geo_linear']['vrp_banda']} npix {r['oraculo']['geo_linear']['npix']}"
       f" | MIROVA {obj[159]['mirova']}")

    # 8. firma de conteo: ¿crece con el cenit o con Chillán? y ¿con la magnitud?
    pr("\n== 8. firma de conteo O_n/F_n: por tramo, sin Chillán, y contra la magnitud de MIROVA")
    fil = []
    for i in pos:
        o = res[i]["oraculo"]["geo_linear"]
        if Fp(i) and O(i) and float(tab[i]["F_n"]) > 0 and float(tab[i]["F_pc"]) > 0:
            fil.append((Z[i], obj[i]["volcan"] == "NevadosDeChillan", o["npix"] / float(tab[i]["F_n"]), M[i]))
    zz = np.array([f[0] for f in fil]); rr = np.array([f[2] for f in fil]); mm = np.array([f[3] for f in fil])
    ch = np.array([f[1] for f in fil])
    from scipy.stats import spearmanr
    for etq, s in (("todas", np.ones_like(ch)), ("sin Chillán", ~ch), ("Chillán", ch)):
        s = s.astype(bool)
        pr(f"   {etq}: Spearman(cenit, O_n/F_n) = {spearmanr(zz[s], rr[s])[0]:+.2f} n={s.sum()} ;"
           f" Spearman(MIROVA, O_n/F_n) = {spearmanr(mm[s], rr[s])[0]:+.2f}")
    pr(f"   MIROVA mediana por grupo: Chillán {np.median(mm[ch]):.2f}, resto {np.median(mm[~ch]):.2f}")
    (AQUI / "v1_romper_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
