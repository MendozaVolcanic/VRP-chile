# -*- coding: utf-8 -*-
"""F1a, controles positivos del barrido (plan §F1): con instrumento PROPIO hay que volver a encontrar
 (a) R6: la metrica M del evaluador de D25 da MEJORA a un placebo de ganancia constante (AUDIT_S158_R2 §1 fila 9);
 (b) R5: el gemelo de D25 (K' corrido en el mismo job que K) es identidad (experiments/_s159/gemelo_d25/).

(a) Implementacion propia de M (leida en evaluar_d25.py l. 120-160 y rb/05_placebo_metrica_m.py, no copiada): por
par, d = |log10(D/M)| - |log10(K/M)|; mediana de d con bootstrap por bloques (noche, volcan), 2.000 remuestreos,
MEJORA si el intervalo 95 % queda entero bajo 0, EMPEORA si entero sobre 0. Pares: la tabla t_C0_K.json de V1 de F/K
(lado control = C0, `disp` publicado y `vrp_ref` de MIROVA; pasadas `pos` que C0 publica), por sensor. D = g * K.
Control: g = 1,0 da d = 0 exacto en todos los pares (NEUTRO con [0, 0]). Pregunta 2: n pares se imprime.
(b) Instrumento propio: parea los records de K y K' de la rama de V1 de D25 (run 39530508296) por (volcan, sensor,
datetime_utc) y compara TODO el record salvo processed_utc, first_processed_utc, regimen, updated; cuenta pasadas no
pareadas y records distintos, por sensor. Control positivo: la misma comparacion entre C0 y su gemelo de F/K V1
(jobs distintos) tiene que dar records distintos (la geometria de borde cambia entre maquinas, A96 y unir_intentos).
Uso: python controles_d25.py <t_C0_K_v1.json> <d25_v1_dir> <fk_v1_union_dir> <salida.json>
"""
import json, math, random, statistics, sys, collections
from pathlib import Path

PROCESO = {"processed_utc", "first_processed_utc", "regimen", "updated"}
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]


def bucket(s):
    s = s or ""
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else ("VIIRS375" if s.startswith("VIIRS") else None))


def metrica_m(pares, g, n_boot=2000, semilla=160):
    """pares: lista de (bloque, K, M). Devuelve (veredicto, lo, hi, n, mediana)."""
    d = [abs(math.log10(g * k / m)) - abs(math.log10(k / m)) for _, k, m in pares]
    bloques = sorted({b for b, _, _ in pares}); idx = collections.defaultdict(list)
    for i, (b, _, _) in enumerate(pares): idx[b].append(i)
    rnd = random.Random(semilla); meds = []
    for _ in range(n_boot):
        muestra = []
        for _ in bloques:
            muestra.extend(d[i] for i in idx[rnd.choice(bloques)])
        meds.append(statistics.median(muestra))
    meds.sort(); lo, hi = meds[int(0.025 * n_boot)], meds[int(0.975 * n_boot) - 1]
    return ("MEJORA" if hi < 0 else "EMPEORA" if lo > 0 else "NEUTRO"), lo, hi, len(d), statistics.median(d)


def control_a(tabla, salida):
    T = json.load(open(tabla, encoding="utf-8"))["pasadas"]
    out = {}
    for s in ("MODIS", "VIIRS375", "VIIRS750"):
        pares = []
        for k, v in T.items():
            c = v.get("control")
            if not c or k.split("|")[1] != s or c["lab"] != "pos" or not c["pub"] or not c["vrp_ref"] or not c["disp"]: continue
            pares.append((k.split("|")[0] + "|" + k.split("|")[2][:10], c["disp"], c["vrp_ref"]))
        if len(pares) < 5:
            print("(a) %-8s n %d: sin sustrato" % (s, len(pares))); out[s] = {"n": len(pares)}; continue
        razon = statistics.median(k / m for _, k, m in pares)
        res = {}
        for g in (1.0, 1.1, 1.2, 0.8):
            ver, lo, hi, n, md = metrica_m(pares, g)
            res["g=%.1f" % g] = {"veredicto": ver, "ic": [round(lo, 4), round(hi, 4)], "mediana_d": round(md, 4)}
            print("(a) %-8s n %3d razon mediana K/M %.3f | g=%.1f -> %-7s mediana d %+.4f IC95 [%+.4f, %+.4f]" % (s, n, razon, g, ver, md, lo, hi))
        out[s] = {"n": len(pares), "razon_mediana": round(razon, 3), **res}
    salida["control_a_metrica_m"] = out


def cargar(d, arm):
    out = {}
    for v in VOLS:
        p = Path(d) / arm / (v + ".json")
        if not p.exists(): continue
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            out[(v, bucket(r.get("sensor")), r.get("datetime_utc", "")[:16], r.get("sensor"))] = r
    return out


def comparar(A, B, nombre, salida, mutar=None):
    ka, kb = set(A), set(B); comunes = ka & kb
    c = collections.Counter()
    for k in comunes:
        a = {x: y for x, y in A[k].items() if x not in PROCESO}; b = {x: y for x, y in B[k].items() if x not in PROCESO}
        if mutar: b = mutar(k, b)
        c[(k[1], "pareadas")] += 1
        if a != b:
            c[(k[1], "record_distinto")] += 1
            dif = [x for x in set(a) | set(b) if a.get(x) != b.get(x)]
            c[(k[1], "pub_relevante_distinto")] += int(any(x in ("primary_cluster", "distance_class", "vrp_mw", "triggered_test1", "f5_core_vrp_mw", "discarded_reason", "t_max_k") for x in dif))
    res = {"%s|%s" % k: v for k, v in sorted(c.items())}
    res["solo_A"] = len(ka - kb); res["solo_B"] = len(kb - ka)
    print("(b) %s: %s" % (nombre, res))
    salida["control_b_" + nombre] = res


def main():
    tabla, d25, fk, out = sys.argv[1:5]
    salida = {}
    control_a(tabla, salida)
    K, Kp = cargar(d25, "_s157_ab_d25_k_control"), cargar(d25, "_s157_ab_d25_k_gemelo")
    comparar(K, Kp, "d25_K_vs_Kprima", salida)
    # control positivo del instrumento (b): C0 contra su gemelo de F/K V1, jobs distintos
    C0, G = cargar(fk, "_s146_ab_control"), cargar(fk, "_s151_ab_control_gemelo")
    comparar(C0, G, "fk_v1_C0_vs_gemelo", salida)
    # control de mutacion: K' con 37 records mutados tiene que dar exactamente 37 distintos
    objetivo = sorted(Kp)[:37]
    comparar(K, Kp, "d25_mutacion_37", salida, mutar=lambda k, b: dict(b, vrp_mw=(b.get("vrp_mw") or 0) + 1.0) if k in objetivo else b)
    Path(out).write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
