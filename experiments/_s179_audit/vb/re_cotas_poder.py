#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoría S179, frente B. ¿Las cotas selladas de VIIRS (14/17 y 12/2) disparan con la falsa alarma que declaran?

POR QUÉ. La regla dice: la cota es el primer entero con falsa alarma Poisson de 8 % o menos «si la vía rinde como en
la retrospectiva». Esa cuenta toma la tasa estimada como si fuera exacta. Las tasas salen de 1 a 9 casos crudos. Aquí
se mide (1) cuánto cambia la falsa alarma al meter la incertidumbre de la tasa, (2) qué exposición por día ve hoy el
vigilante contra la que usó la calibración, (3) el poder del nulo de la guardia y (4) cuánto dura el plazo de 29
protegidas al ritmo de noviembre.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si lo medido estuviera roto, ¿lo vería? Control: con la tasa puntual, mi Poisson tiene que devolver las falsas
   alarmas que publica la regla (0,059; 0,056; 0,045; 0,053). Si no, mi cuenta no es la de la regla.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Cada conteo va con su denominador y su ventana; un conteo
   con denominador 0 se imprime como SIN DATO.

Base: código main 438a60a1e (instantánea), datos de 438a60a1e extraídos con git show. Referencia: latest_consolidado.csv
y registro_vrp_ocr.csv de 438a60a1e. Números crudos de la calibración: los de las salidas commiteadas
experiments/_s178_cotas_v375/cotas_v375_con_retro_salida.txt y
experiments/_s176_v375e_adopcion/cotas_retrospectiva_v750_salida.txt (438a60a1e).
"""
import json
import math
import os
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
MAIN = Path(r"D:\vrp-trabajo\temporales\s179-audit\main")
DATOS = Path(r"D:\vrp-trabajo\temporales\s179-audit\b\datos")
AQUI = Path(__file__).resolve().parent
os.environ["VRP_PROFILE"] = "mirova_equivalent"
for p in (str(MAIN), str(MAIN / "scripts")):
    sys.path.insert(0, p)
import vigilancia_guardia_viirs as vv  # noqa: E402
import banco_paridad as bp  # noqa: E402
import referencia_mirova_unificada as rmu  # noqa: E402

vg, vs, aa = vv.vg, vv.vs, vv.aa
CONS = MAIN / "latest_consolidado.csv"
OCR = DATOS / "ref" / "registro_vrp_ocr.csv"
RESPALDO = DATOS / "ref" / "registro_vrp_consolidado_respaldo_20260408.csv"
HISTORICO = DATOS / "union" / "consolidado_filas_perdidas.csv"
random.seed(179)


def sf(k, lam):
    if lam <= 0:
        return 0.0
    acc, term = 0.0, math.exp(-lam)
    for i in range(k + 1):
        acc += term
        term *= lam / (i + 1)
    return max(0.0, 1.0 - acc)


def gamma_ic(k, a=0.025):
    """IC exacto (Garwood) de la media de Poisson dado k eventos, por bisección sobre la cola."""
    def cdf(x, lam):
        return 1.0 - sf(x, lam)
    lo, hi = 0.0, 0.0
    if k > 0:
        x0, x1 = 0.0, float(k)
        for _ in range(200):          # P(X >= k | lam) = a
            m = (x0 + x1) / 2
            if sf(k - 1, m) < a:
                x0 = m
            else:
                x1 = m
        lo = (x0 + x1) / 2
    x0, x1 = float(k), float(k) * 5 + 20
    for _ in range(200):              # P(X <= k | lam) = a
        m = (x0 + x1) / 2
        if cdf(k, m) > a:
            x0 = m
        else:
            x1 = m
    hi = (x0 + x1) / 2
    return lo, hi


def parte1():
    print("== 1. Falsa alarma declarada contra falsa alarma con la incertidumbre de la tasa")
    print("   Método: la tasa verdadera de cada estrato ~ Gamma(k + 0,5; 1) (posterior de Jeffreys de un conteo de Poisson"
          " con k casos crudos); se combina igual que la regla; 200.000 sorteos; falsa alarma = E[P(X > cota | lambda)].")
    N = 200000
    casos = []
    # VIIRS 375 (i), C-rad: tasa por pasada = (ponderado O + crudo F26-V) / (464,5 + 139), llevada a 464,5 pasadas en 125
    # días y a 120 días. O: 2 crudos que pesan 9,8 (peso medio 4,9). F26-V radiante: 3 crudos.
    casos.append(("VIIRS 375 (i) Muy Bajo, cota 14", 14, 9.48,
                  lambda g: ((9.8 / 2) * g(2) + g(3)) / (464.5 + 139) * 464.5 * 120 / 125, "2 (peso 4,9) + 3"))
    # VIIRS 375 (ii): O 5 crudos que pesan 10,5 (peso 2,1); F26-V 5 crudos; denominadores 2062,7 y 528.
    casos.append(("VIIRS 375 (ii) sobre-publicación, cota 17", 17, 11.82,
                  lambda g: ((10.5 / 5) * g(5) + g(5)) / (2062.7 + 528) * 2062.7 * 120 / 125, "5 (peso 2,1) + 5"))
    # VIIRS 750 (i): 9 crudos en 143 días. (ii): 1 crudo en 143 días.
    casos.append(("VIIRS 750 (i) Muy Bajo, cota 12", 12, 7.55, lambda g: g(9) * 120 / 143, "9"))
    casos.append(("VIIRS 750 (ii) sobre-publicación, cota 2", 2, 0.84, lambda g: g(1) * 120 / 143, "1"))
    out = []
    for nombre, cota, lam_regla, f, crudos in casos:
        lam_pt = f(lambda k: float(k))
        fa_pt = sf(cota, lam_pt)
        lams = sorted(f(lambda k: random.gammavariate(k + 0.5, 1.0)) for _ in range(N))
        fa = sum(sf(cota, x) for x in lams[::20]) / len(lams[::20])
        q = lambda p: lams[int(p * (N - 1))]
        print(f"   {nombre}: casos crudos {crudos}; lambda de la regla {lam_regla}; mi lambda puntual {lam_pt:.2f} "
              f"(control: falsa alarma puntual {fa_pt:.3f}); lambda 95 % [{q(0.025):.1f}; {q(0.975):.1f}]; "
              f"falsa alarma con incertidumbre {fa:.3f}; P(lambda verdadera > cota) {sum(1 for x in lams if x > cota) / N:.3f}")
        out.append({"cota": nombre, "lambda_regla": lam_regla, "lambda_puntual": round(lam_pt, 2),
                    "falsa_alarma_puntual": round(fa_pt, 4), "lambda_ic95": [round(q(0.025), 2), round(q(0.975), 2)],
                    "falsa_alarma_con_incertidumbre": round(fa, 4)})
    fam = 1.0
    for o in out:
        fam *= 1 - o["falsa_alarma_puntual"]
    print(f"   Las cuatro cotas a la vez, con la tasa puntual: P(al menos una dispara en 120 días) = {1 - fam:.3f}")
    print("   Poder con la tasa puntual (P de disparar si la vía pierde k veces lo de la retrospectiva):")
    for nombre, cota, lam_regla, f, _ in casos:
        print(f"     {nombre}: x1,5 {sf(cota, lam_regla * 1.5):.2f}; x2 {sf(cota, lam_regla * 2):.2f}; x3 {sf(cota, lam_regla * 3):.2f}")
    return out


def parte2(coords, inner, filas):
    print("\n== 2. Exposición por día: lo que el vigilante contaría hoy contra lo que usó la calibración (VIIRS 375)")
    print("   Calibración C-rad: 464,5 pasadas Muy Bajo y 2.062,7 negativos limpios que K calla en los 125 días de la "
          "ventana O (ponderado, NOAA-20 y NOAA-21) = 3,72 y 16,5 por día.")
    out = {}
    for nombre, win, excl in (("ventana O (2026-06-13 a 2026-10-21, sin 6 días)", ("2026-06-13", "2026-10-21"),
                               {"2026-10-12", "2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20"}),
                              ("últimos 20 días (2026-10-22 a 2026-11-10)", ("2026-10-22", "2026-11-10"), set())):
        prod = [r for r in bp.cargar_nuestros(coords, inner, win, data=DATOS / "mirova_equivalent")
                if r["b"] == "VIIRS375" and r["noche"] not in excl]
        bp.etiquetar(prod, *bp.indexar_referencia(filas, coords, win, regla_minimas="SN")[:3])
        pasadas = [p for p in vs.pasadas_de_alerta(filas, prod, [], win, diurna=vs._diurna_por_defecto())
                   if p["sensor"] == "VIIRS375" and p["fecha_utc"][:10] not in excl]
        noches = sorted({r["noche"] for r in prod})
        dias = len(noches)
        for regimen, filtro in (("tres plataformas", lambda s: True), ("NOAA-20 y NOAA-21", lambda s: "SNPP" not in (s or ""))):
            pr = [r for r in prod if filtro(r.get("sensor"))]
            idx = defaultdict(list)
            for r in pr:
                idx[r["vol"]].append(r)
            mb = prot = mb_kpub = prot_vol = 0
            vol_prot = Counter()
            for p in pasadas:
                dt = datetime.strptime(p["instante_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                cerca = [r for r in idx.get(p["volcano"], []) if abs((r["dt"] - dt).total_seconds()) <= vg.TOL_S]
                if not cerca:
                    continue
                if p["protegida"]:
                    prot += 1
                    vol_prot[p["volcano"]] += 1
                elif not p["minima"] and (p["vrp_mirova_mw"] or 0) > 0.05:
                    mb += 1
                    mb_kpub += any(r["pub"] for r in cerca)
            neg = [r for r in pr if r.get("lab") == "neg_limpio"]
            neg_resto = sum(1 for r in neg if not r["pub"])
            print(f"   {nombre} | {regimen}: {dias} noches con datos; pasadas K {len(pr)}; Muy Bajo con record nuestro {mb} "
                  f"({mb / dias:.2f} por día; K publica {mb_kpub}); negativos limpios {len(neg)}, que K calla {neg_resto} "
                  f"({neg_resto / dias:.2f} por día); protegidas con record {prot} ({prot / dias:.2f} por día) {dict(vol_prot)}")
            out[f"{nombre} | {regimen}"] = {"dias": dias, "muy_bajo": mb, "muy_bajo_k_publica": mb_kpub,
                                            "neg_limpio": len(neg), "neg_resto": neg_resto, "protegidas": prot,
                                            "protegidas_por_volcan": dict(vol_prot)}
    return out


def parte3(coords, inner, filas):
    print("\n== 3. El nulo de la guardia (K contra K): qué compara y con cuánto sustrato")
    win = ("2026-10-27", "2026-11-10")
    out = {}
    for sensor in ("VIIRS375", "VIIRS750"):
        prod = [r for r in bp.cargar_nuestros(coords, inner, win, data=DATOS / "mirova_equivalent") if r["b"] == sensor]
        guardia = [r for r in bp.cargar_nuestros(coords, inner, win, data=DATOS / "guardia_k_viirs") if r["b"] == sensor]
        idx = defaultdict(list)
        for r in prod:
            idx[r["vol"]].append(r)
        pares = pub_g = pub_p = dist_pub = dist_disp = sin_par = 0
        vol_pub = Counter()
        max_dif = 0.0
        for g in guardia:
            cerca = [r for r in idx.get(g["vol"], []) if abs((r["dt"] - g["dt"]).total_seconds()) <= vg.TOL_S]
            if not cerca:
                sin_par += 1
                continue
            pares += 1
            pub_g += bool(g["pub"])
            pub_p += any(r["pub"] for r in cerca)
            if g["pub"]:
                vol_pub[g["vol"]] += 1
            if bool(g["pub"]) != any(r["pub"] for r in cerca):
                dist_pub += 1
            d = min(abs((g["disp"] or 0) - (r["disp"] or 0)) for r in cerca)
            max_dif = max(max_dif, d)
            dist_disp += d > 1e-9
        noches = sorted({g["noche"] for g in guardia})
        print(f"   {sensor}: guardia {len(guardia)} records, noches {noches[0]} a {noches[-1]}; pares {pares}; sin par en "
              f"producción {sin_par}; la guardia publica en {pub_g} pares {dict(vol_pub)}; publicación distinta {dist_pub}; "
              f"VRP mostrado distinto {dist_disp} (diferencia máxima {max_dif:.4f} MW)")
        out[sensor] = {"guardia": len(guardia), "pares": pares, "sin_par": sin_par, "guardia_publica": pub_g,
                       "publica_por_volcan": dict(vol_pub), "publicacion_distinta": dist_pub,
                       "vrp_distinto": dist_disp, "dif_max_mw": max_dif}
    return out


def parte4():
    print("\n== 4. Plazo de 29 protegidas al ritmo de noviembre (de re_sim_vigilancia_salida.json, escenario A)")
    with open(AQUI / "re_sim_vigilancia_salida.json", encoding="utf-8") as fh:
        sim = json.load(fh)
    out = {}
    for o in sim:
        if not o["escenario"].startswith("A."):
            continue
        tasa = o["protegidas_vistas_en_guardia"] / o["dias_ventana"]
        dias29 = 29 / tasa if tasa else None
        chillan = o["protegidas_por_volcan"].get("NevadosDeChillan", 0)
        lo, hi = gamma_ic(o["muy_bajo_k"])
        print(f"   {o['sensor']}: {o['protegidas_vistas_en_guardia']} protegidas en {o['dias_ventana']} días "
              f"({tasa:.2f} por día; {chillan} de {o['protegidas_posteriores']} son de Chillán): las 29 se juntan en "
              f"{dias29:.1f} días. Muy Bajo perdidas {o['muy_bajo_k']} de {o['muy_bajo_n']}: IC 95 % del conteo "
              f"[{lo:.2f}; {hi:.2f}] en {o['dias_ventana']} días = [{lo / o['dias_ventana'] * 120:.1f}; "
              f"{hi / o['dias_ventana'] * 120:.1f}] en 120 días")
        out[o["sensor"]] = {"protegidas": o["protegidas_vistas_en_guardia"], "dias": o["dias_ventana"],
                            "dias_para_29": round(dias29, 1) if dias29 else None, "de_chillan": chillan,
                            "muy_bajo_ic95_120d": [round(lo / o["dias_ventana"] * 120, 1),
                                                   round(hi / o["dias_ventana"] * 120, 1)]}
    # P de ver 3 o más Muy Bajo perdidas en 7,79 días si la tasa fuera la de la calibración (9,48 en 120 días)
    lam = 9.48 / 120 * 7.79
    print(f"   VIIRS 375: con la tasa de la calibración se esperan {lam:.2f} Muy Bajo perdidas en 7,79 días; P(3 o más) = "
          f"{sf(2, lam):.4f}. Con la tasa de noviembre (3 en 7,79 días), la cota 14 se supera hacia el día "
          f"{15 / (3 / 7.79):.0f} después del encendido.")
    out["p_3_o_mas_con_tasa_calibrada"] = round(sf(2, lam), 4)
    return out


def main():
    res = {"parte1": parte1()}
    coords = aa._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = rmu.cargar_referencia_unificada(CONS, OCR, respaldo_path=RESPALDO, historico_path=HISTORICO)
    res["parte2"] = parte2(coords, inner, filas)
    res["parte3"] = parte3(coords, inner, filas)
    res["parte4"] = parte4()
    with open(AQUI / "re_cotas_poder_salida.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False, default=str)
    print("\nsalida 0")


if __name__ == "__main__":
    main()
