# -*- coding: utf-8 -*-
"""v01 (verificador S173 ver_tupun375): pareo POR PASADA propio, sin banco_paridad ni clase_mirova, de K (origin/main,
copia del auditor en ../tupun375/repo, identica a origin/main f20495d374 salvo CRLF) contra la referencia del scraper,
Tupungatito VIIRS 375.

POR QUE: la afirmacion 1 del auditor (168 pares, 0,43 / 0,24, Spearman -0,52) sale de banco_paridad + node. Si el
helper tuviera un defecto (llave, tolerancia, campo de magnitud, regla SN), lo heredaria. Aqui todo se rehace a mano:
  llave      = (volcan, familia VIIRS 375) y |t_ref - t_rec| <= TOL s, con TOL = 120 (la del proyecto) y tambien 60 y 30.
  nocturna   = solar_zenith_deg del record >= 90 (el record lo trae; el helper usa otra funcion: se compara el n).
  alerta     = Tipo_Registro empieza por ALERTA y no es ALERTA_SIN_GEOMETRIA_OCR; VRP_MW > 0; regla SN: si TODAS las
               filas de alerta de esa pasada (+-TOL) tienen VRP <= 0,05, la pasada cuenta como sin alerta.
  VRP MIROVA = fila CONS si hay, si no OCR (como el auditor); variante "cons_sola".
  publicada  = aproximacion del predicado del tablero SIN node: distance_class == "summit" y magnitud > 0, con
               magnitud = f5_core_vrp_mw si es > 0, si no primary_cluster.vrp_mw. Es una aproximacion declarada: el
               control es que el n de pares y las medianas coincidan con las de s01 (node). Si no coinciden, se dice.
  cenit      = sensor_zenith_deg del record.
P1 (roto -> lo veo): razon x cos(z)^2 debe dar Spearman mas negativo; razon x2 debe doblar la mediana.
P2 (instrumento muerto): la referencia corrida +1 dia debe dejar casi sin pares; se imprime.
Ademas: cuantos records parean con MAS de una fila de referencia y cuantas filas con mas de un record (granulo doble),
distribucion de ceros (records con alerta de MIROVA y magnitud 0), y Spearman por plataforma.
Uso: python -B v01_pareo_propio.py <raiz repo> <salida prefijo>
"""
import bisect, csv, json, math, os, random, statistics, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

ROOT, PRE = sys.argv[1], sys.argv[2]
VOL = "Tupungatito"
INI, FIN = "2026-02-14", "2026-11-02"
SEMILLA, NB, CORTE, UMBRAL_SN = 173, 200, 30.0, 0.05
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


def f(x):
    try:
        y = float(x)
        return None if math.isnan(y) else y
    except (TypeError, ValueError):
        return None


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    rk = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            rk[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return rk


def spearman(x, y):
    if len(x) < 4:
        return None
    a, b = rank(x), rank(y)
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return None if den == 0 else num / den


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 3) if xs else None


def resumen(pares):
    z = [p[0] for p in pares]
    r = [p[1] for p in pares]
    out = {"n": len(pares), "mediana": med(r),
           "z<30": {"n": sum(1 for q in z if q < CORTE), "mediana": med([b for a, b in zip(z, r) if a < CORTE])},
           "z>=30": {"n": sum(1 for q in z if q >= CORTE), "mediana": med([b for a, b in zip(z, r) if a >= CORTE])}}
    if len(pares) < 8:
        out["spearman"] = "SIN DATO (n < 8)"
        return out
    s = spearman(z, r)
    rnd = random.Random(SEMILLA)
    sb = []
    for _ in range(NB):
        zz = list(z)
        rnd.shuffle(zz)
        sb.append(spearman(zz, r))
    sb = sorted(x for x in sb if x is not None)
    lo, hi = sb[int(0.025 * len(sb))], sb[int(0.975 * len(sb)) - 1]
    out.update({"spearman": round(s, 3), "barajado_95": [round(lo, 3), round(hi, 3)], "fuera": not (lo <= s <= hi),
                "barajado_mediana": round(statistics.median(sb), 3)})
    return out


def linea(nom, rs):
    sp = rs.get("spearman")
    sps = sp if isinstance(sp, str) else f"{sp:+.3f} [{rs['barajado_95'][0]:+.3f}; {rs['barajado_95'][1]:+.3f}] med_baraj {rs['barajado_mediana']:+.3f} {'FUERA' if rs['fuera'] else 'dentro'}"
    pr(f"  {nom:40s} n {rs['n']:4d} med {rs['mediana']}  z<30 {rs['z<30']['mediana']} ({rs['z<30']['n']})  z>=30 {rs['z>=30']['mediana']} ({rs['z>=30']['n']})  Spearman {sps}")


# ---- referencia
def leer_ref(fn, src):
    out = []
    for r in csv.DictReader(open(os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot", fn), encoding="utf-8")):
        if r["Volcan"].strip() != VOL or r["Sensor"].strip() != "VIIRS375":
            continue
        fe = r["Fecha_Satelite_UTC"].strip()
        if not (INI <= fe[:10] <= FIN):
            continue
        dt = datetime.strptime(fe[:19] if len(fe) >= 19 else fe[:16], "%Y-%m-%d %H:%M:%S" if len(fe) >= 19 else "%Y-%m-%d %H:%M")
        tipo = r["Tipo_Registro"].strip()
        out.append({"dt": dt, "fecha": fe, "tipo": tipo, "vrp": f(r["VRP_MW"]), "dist": f(r["Distancia_km"]), "src": src,
                    "alerta": tipo.startswith("ALERTA") and tipo != "ALERTA_SIN_GEOMETRIA_OCR"})
    return out


ref = leer_ref("registro_vrp_consolidado.csv", "CONS") + leer_ref("registro_vrp_ocr.csv", "OCR")
ref.sort(key=lambda x: x["dt"])
ts = [x["dt"] for x in ref]
pr(f"referencia Tupungatito VIIRS375 {INI}..{FIN}: {len(ref)} filas ({Counter(x['src'] for x in ref)}), alertas {sum(1 for x in ref if x['alerta'])}")


def vecinas(t, tol):
    i = bisect.bisect_left(ts, t - timedelta(seconds=tol))
    out = []
    while i < len(ref) and ref[i]["dt"] <= t + timedelta(seconds=tol):
        out.append(ref[i])
        i += 1
    return out


def vrp_mirova(fs, cons_sola=False):
    """Regla SN propia: alertas de la pasada; si todas tienen VRP <= 0,05 la pasada no cuenta."""
    al = [x for x in fs if x["alerta"] and (x["src"] == "CONS" or not cons_sola)]
    if not al:
        return None, None, False
    # SN se decide con TODAS las alertas de la pasada (CONS y OCR), aunque luego se tome solo CONS
    todas = [x for x in fs if x["alerta"]]
    minima = all(x["vrp"] is not None and x["vrp"] <= UMBRAL_SN + 1e-9 for x in todas)
    if minima:
        return None, None, True
    c = [x for x in al if x["src"] == "CONS"]
    x = (c or al)[0]
    return x["vrp"], x, False


# ---- records
d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", VOL + ".json"), encoding="utf-8"))
recs = []
for r in d["records"]:
    s = r.get("sensor") or ""
    if not s.startswith("VIIRS") or s.endswith("_750"):
        continue
    if not (INI <= r.get("datetime_utc", "")[:10] <= FIN):
        continue
    sz = f(r.get("solar_zenith_deg"))
    if sz is None or sz < 90:
        continue
    pc = r.get("primary_cluster") or {}
    f5 = f(r.get("f5_core_vrp_mw"))
    mag = f5 if (f5 is not None and f5 > 0) else f(pc.get("vrp_mw"))
    recs.append({"dt": datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M"), "sensor": s, "z": f(r.get("sensor_zenith_deg")),
                 "dc": r.get("distance_class"), "mag": mag, "f5": f5, "pc": f(pc.get("vrp_mw")), "pub": (r.get("distance_class") == "summit" and (mag or 0) > 0),
                 "proc": r.get("processed_utc"), "sha": (r.get("regimen") or {}).get("codigo_sha")})
pr(f"records nocturnos VIIRS375 (solar_zenith >= 90): {len(recs)} (s01 dice 1086); publicados (summit y mag > 0): {sum(r['pub'] for r in recs)} (s01 dice 362); sin cenit: {sum(1 for r in recs if r['z'] is None)}")

res = {"ventana": [INI, FIN], "regla_SN_umbral": UMBRAL_SN}
for tol in (120, 60, 30):
    pr(f"== tolerancia +-{tol} s")
    pares, parc, multi_rec, zeros, minimas = [], [], 0, 0, 0
    uso_fila = Counter()
    for r in recs:
        fs = vecinas(r["dt"], tol)
        if len([x for x in fs if x["alerta"]]) > 1:
            multi_rec += 1
        vm, fm, mini = vrp_mirova(fs)
        vmc, _, _ = vrp_mirova(fs, cons_sola=True)
        minimas += mini
        if vm is not None and vm > 0:
            uso_fila[fm["fecha"]] += 1
            if r["pub"] and r["mag"] > 0 and r["z"] is not None:
                pares.append((r["z"], r["mag"] / vm, r, vm, fm))
            else:
                zeros += 1
        if vmc is not None and vmc > 0 and r["pub"] and r["mag"] > 0 and r["z"] is not None:
            parc.append((r["z"], r["mag"] / vmc, r, vmc))
    fila_doble = sum(1 for k, n in uso_fila.items() if n > 1)
    rs = resumen([(z, q) for z, q, *_ in pares])
    rsc = resumen([(z, q) for z, q, *_ in parc])
    pr(f"  records con alerta de MIROVA (SN, VRP > 0): {len(pares) + zeros}; pares (publicada y mag > 0): {len(pares)}; alerta sin publicar: {zeros}; pasadas minimas SN: {minimas}")
    pr(f"  records que parean con >1 fila de alerta: {multi_rec}; filas de referencia usadas por >1 record (granulo doble): {fila_doble}")
    linea("U (CONS+OCR, SN)", rs)
    linea("C (solo tabla)", rsc)
    res[f"tol{tol}"] = {"U": rs, "C": rsc, "alerta_sin_publicar": zeros, "multi_rec": multi_rec, "fila_doble": fila_doble, "minimas_SN": minimas}
    if tol == 120:
        P = pares
        res["tol120"]["por_plataforma"] = {}
        for p in sorted({t[2]["sensor"] for t in P}):
            rp = resumen([(z, q) for z, q, r, *_ in P if r["sensor"] == p])
            res["tol120"]["por_plataforma"][p] = rp
            linea(p, rp)
        # controles
        c1 = resumen([(z, q * math.cos(math.radians(z)) ** 2) for z, q, *_ in P])
        res["tol120"]["control_cos2"] = c1
        linea("control P1 x cos(z)^2", c1)
        pr(f"  control P1 x2: mediana {med([2 * q for _, q, *_ in P])}")
        # P2: referencia corrida un dia
        sh = 0
        for r in recs:
            vm, fm, _ = vrp_mirova(vecinas(r["dt"] + timedelta(days=1), tol))
            if vm and vm > 0 and r["pub"]:
                sh += 1
        res["tol120"]["control_neg_shift1d_pares"] = sh
        pr(f"  control P2 (referencia +1 dia): pares {sh} (de {len(P)})")
        # control: la fila que se tomo como VRP de MIROVA coincide con la de s01?
        s01 = {(x["sensor"], x["dt"]): x for x in csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(PRE)), "r01_k_pasadas.csv"), encoding="utf-8"))}
        dif_m, dif_disp, falta, sobra = 0, 0, 0, 0
        claves_s01 = {k for k, x in s01.items() if x["b"] == "VIIRS375" and x["pub"] == "1" and f(x["disp"]) and f(x["disp"]) > 0 and f(x["vrp_M"]) and f(x["vrp_M"]) > 0}
        claves_mias = set()
        for z, q, r, vm, fm in P:
            k = (r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"))
            claves_mias.add(k)
            x = s01.get(k)
            if x is None:
                sobra += 1
                continue
            if abs(f(x["vrp_M"]) - vm) > 1e-9:
                dif_m += 1
            if abs(f(x["disp"]) - r["mag"]) > 1e-6:
                dif_disp += 1
        falta = len(claves_s01 - claves_mias)
        res["tol120"]["cruce_con_s01"] = {"pares_s01": len(claves_s01), "pares_mios": len(claves_mias), "en_s01_no_mios": falta, "mios_no_en_s01": sobra,
                                           "vrp_M_difiere": dif_m, "disp_vs_mag_difiere": dif_disp,
                                           "en_s01_no_mios_lista": sorted(claves_s01 - claves_mias), "mios_no_en_s01_lista": sorted(claves_mias - claves_s01)}
        pr(f"  cruce con s01: pares s01 {len(claves_s01)} / mios {len(claves_mias)}; en s01 y no mios {falta}; mios y no en s01 {sobra}; VRP MIROVA difiere {dif_m}; disp(node) vs mi magnitud difiere {dif_disp}")
        for k in sorted(claves_s01 - claves_mias):
            x = s01[k]
            pr(f"    s01 y no mio: {k} dc {x['dc']} disp {x['disp']} f5 {x['f5']} pc {x['pc_vrp']} vrp_M {x['vrp_M']}")
        for k in sorted(claves_mias - claves_s01):
            x = s01.get(k)
            pr(f"    mio y no s01: {k} " + (f"dc {x['dc']} pub {x['pub']} disp {x['disp']} vrp_M {x['vrp_M']} lab {x['lab']}" if x else "no esta en s01"))
        res["tol120"]["detalle"] = [{"dt": r["dt"].strftime("%Y-%m-%d %H:%M"), "sensor": r["sensor"], "z": z, "mag": r["mag"], "M": vm, "src_M": fm["src"], "razon": round(q, 4), "sha": r["sha"]} for z, q, r, vm, fm in sorted(P, key=lambda t: t[0])]
        # codigo que escribio los records pareados (A104)
        pr(f"  codigo_sha de los records pareados: {Counter(r['sha'][:9] if r['sha'] else None for _, _, r, *_ in P)}; processed_utc min {min(r['proc'] for _, _, r, *_ in P)} max {max(r['proc'] for _, _, r, *_ in P)}")
        # razon por codigo_sha (A104: si los commits posteriores a K cambiaran algo, se veria aqui)
        for sha in sorted({r["sha"] for _, _, r, *_ in P}):
            rp = resumen([(z, q) for z, q, r, *_ in P if r["sha"] == sha])
            linea(f"sha {sha[:9]}", rp)
        # MIROVA plano: VRP de MIROVA contra cenit en los pares, y en TODAS las alertas (incluidas no publicadas)
        zz = [z for z, *_ in P]
        vm_ = [vm for _, _, _, vm, _ in P]
        pr(f"  VRP MIROVA vs cenit (pares): Spearman {spearman(zz, vm_):+.3f}; mediana z<30 {med([v for z, v in zip(zz, vm_) if z < 30])} z>=30 {med([v for z, v in zip(zz, vm_) if z >= 30])}")
        # magnitud de K vs cenit (sin dividir por MIROVA): si K cae con el cenit por si sola
        mk = [r["mag"] for _, _, r, *_ in P]
        pr(f"  magnitud K vs cenit (pares): Spearman {spearman(zz, mk):+.3f}; mediana z<30 {med([v for z, v in zip(zz, mk) if z < 30])} z>=30 {med([v for z, v in zip(zz, mk) if z >= 30])}")
        # razon de medianas vs mediana de razones (C1.14)
        pr(f"  razon de medianas (med K / med M): z<30 {round(med([v for z, v in zip(zz, mk) if z < 30]) / med([v for z, v in zip(zz, vm_) if z < 30]), 3)}  z>=30 {round(med([v for z, v in zip(zz, mk) if z >= 30]) / med([v for z, v in zip(zz, vm_) if z >= 30]), 3)}")

json.dump(res, open(PRE + "_salida.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
open(PRE + "_salida.txt", "w", encoding="utf-8").write("\n".join(L) + "\n")
