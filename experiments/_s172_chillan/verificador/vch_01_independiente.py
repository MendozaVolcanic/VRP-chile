# -*- coding: utf-8 -*-
"""vch_01 (verificador S172, Chillan): razon de magnitud vs cenit por OTRO camino que el auditor.

POR QUE: el auditor (s02/s03) toma "publica" y la magnitud del predicado del tablero (node, banco_paridad) y la
referencia de la union CONS+OCR. Aqui no uso banco_paridad ni node: leo el JSON del volcan y la tabla CONS sola (la mas
creible, A119/ensenanza S159), parea por plataforma-sensor y hora (+-120 s) y calculo yo la razon, el Spearman, el p
exacto por Monte Carlo y un bootstrap por NOCHES (las pasadas de una misma noche no son independientes).

Dos preguntas del instrumento:
P1 (si lo medido estuviera roto, lo veria): control positivo, "razon" * cenit invertido artificial: si se fabrica una
    razon que cae con el cenit (razon_sint = razon_media * cos(z)) el Spearman debe salir fuerte; y el mismo
    pareo corrido +1 dia (control negativo) debe dar casi 0 pares.
P2 (instrumento muerto): si CONS no se leyera, n = 0 y se imprime SIN DATO, no 0 de correlacion.
Ventana y denominador: se imprimen por volcan y sensor (n pasadas con alerta CONS pareadas con magnitud nuestra > 0).
Uso: python -B vch_01_independiente.py <copia> <ini> <fin> <volcan_json|TODOS> <salida.json>
"""
import bisect, csv, json, math, os, random, statistics, sys
from datetime import datetime, timedelta

ROOT, INI, FIN, VOL, OUT = sys.argv[1:6]
NOM = {"Chaiten": "Chaiten", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Villarrica": "Villarrica",
       "Llaima": "Llaima", "Copahue": "Copahue", "Nevados de Chillan": "NevadosDeChillan",
       "PlanchonPeteroa": "PlanchonPeteroa", "Lascar": "Lascar", "Tupungatito": "Tupungatito",
       "Lastarria": "Lastarria", "Isluga": "Isluga"}
INV = {v: k for k, v in NOM.items()}
vols = [INV[v] for v in NOM.values()] if VOL == "TODOS" else [INV.get(VOL, VOL)]
TOL = 120.0


def bucket_ours(s):
    s = s.upper()
    if "MODIS" in s:
        return "MODIS"
    return "VIIRS750" if s.endswith("_750") else "VIIRS375"


def bucket_ref(s):
    s = s.upper()
    return "MODIS" if "MODIS" in s else ("VIIRS375" if "375" in s else "VIIRS750")


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); rk = [0.0] * len(v); i = 0
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
    a, b = rank(x), rank(y); ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return num / den if den else None


# --- referencia: CONS sola
ref = {}
cons = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot", "registro_vrp_consolidado.csv")
filas = list(csv.DictReader(open(cons, encoding="utf-8")))
for r in filas:
    if r["Volcan"] not in vols or not r["Tipo_Registro"].startswith("ALERTA"):
        continue
    try:
        t = datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S")
        v = float(r["VRP_MW"] or 0)
    except ValueError:
        continue
    b = bucket_ref(r["Sensor"])
    if b == "VIIRS375" and v <= 0.05:   # D-9: V375 de 0,05 MW o menos no cuenta como alerta
        continue
    ref.setdefault((NOM[r["Volcan"]], b), []).append((t, v))
for k in ref:
    ref[k].sort()
print("filas CONS alerta usadas:", sum(len(v) for v in ref.values()), "| SIN DATO si 0")


def parear(lista, t, desplaza=0):
    t = t + timedelta(days=desplaza)
    ts = [x[0] for x in lista]
    i = bisect.bisect_left(ts, t - timedelta(seconds=TOL))
    best = None
    while i < len(lista) and (lista[i][0] - t).total_seconds() <= TOL:
        d = abs((lista[i][0] - t).total_seconds())
        if best is None or d < best[0]:
            best = (d, lista[i][1])
        i += 1
    return best[1] if best else None


filas_out, ctl = [], {"pares_desplazado_1d": 0}
for vk in sorted({NOM[v] for v in vols}):
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vk + ".json"), encoding="utf-8"))
    for r in d["records"]:
        t = datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")
        if not (INI <= r["datetime_utc"][:10] <= FIN):
            continue
        sz = r.get("solar_zenith_deg")
        if sz is None or sz <= 90:        # solo noche (MIR solo nocturno)
            continue
        b = bucket_ours(r["sensor"])
        lista = ref.get((vk, b), [])
        vm = parear(lista, t)
        if parear(lista, t, 1) is not None:
            ctl["pares_desplazado_1d"] += 1
        pc = r.get("primary_cluster") or {}
        f5 = r.get("f5_core_vrp_mw")
        nuestro = f5 if (b == "VIIRS375" and isinstance(f5, (int, float))) else pc.get("vrp_mw")
        filas_out.append({"vol": vk, "b": b, "dt": r["datetime_utc"][:16], "z": r.get("sensor_zenith_deg"),
                          "sensor": r["sensor"], "nuestro": nuestro, "mirova": vm,
                          "noche": (t - timedelta(hours=12)).strftime("%Y-%m-%d")})
par = [x for x in filas_out if x["mirova"] and x["mirova"] > 0 and x["nuestro"] and x["nuestro"] > 0 and x["z"] is not None]
print("pasadas nocturnas leidas:", len(filas_out), "| pares con alerta CONS y magnitud nuestra > 0:", len(par))
rng = random.Random(1721)
res = {"ventana": [INI, FIN], "control_pares_desplazado_1d": ctl["pares_desplazado_1d"], "por": {}}
for vk in sorted({x["vol"] for x in par}):
    for b in ("MODIS", "VIIRS375", "VIIRS750"):
        S = [x for x in par if x["vol"] == vk and x["b"] == b]
        if len(S) < 5:
            continue
        z = [x["z"] for x in S]; rz = [x["nuestro"] / x["mirova"] for x in S]
        sp = spearman(z, rz)
        # permutacion exacta-MC de z
        n_ge = 0; N = 20000
        for _ in range(N):
            zz = z[:]; rng.shuffle(zz); s = spearman(zz, rz)
            if s is not None and abs(s) >= abs(sp):
                n_ge += 1
        p = (n_ge + 1) / (N + 1)
        # bootstrap por noches
        noches = sorted({x["noche"] for x in S}); porn = {n: [x for x in S if x["noche"] == n] for n in noches}
        bs = []
        for _ in range(2000):
            tomo = [rng.choice(noches) for _ in noches]
            T = [x for n in tomo for x in porn[n]]
            s = spearman([x["z"] for x in T], [x["nuestro"] / x["mirova"] for x in T]) if len(T) >= 4 else None
            if s is not None:
                bs.append(s)
        bs.sort()
        # confusor temporal
        fechas = [datetime.strptime(x["dt"], "%Y-%m-%d %H:%M").timestamp() for x in S]
        sp_fz = spearman(fechas, z); sp_fr = spearman(fechas, rz)
        # correlacion parcial (Spearman parcial de rango) razon~z controlando fecha
        def parcial(a, b, c):
            ab, ac, bc = spearman(a, b), spearman(a, c), spearman(b, c)
            return (ab - ac * bc) / math.sqrt((1 - ac ** 2) * (1 - bc ** 2)) if abs(ac) < 1 and abs(bc) < 1 else None
        # efecto fijo noche: restar la media de log(nuestro) y log(mirova) por noche (solo noches con >=2 pares)
        fe = []
        for n, v in porn.items():
            if len(v) >= 2:
                mz = sum(x["z"] for x in v) / len(v)
                mo = sum(math.log(x["nuestro"]) for x in v) / len(v)
                mm = sum(math.log(x["mirova"]) for x in v) / len(v)
                for x in v:
                    fe.append((x["z"] - mz, math.log(x["nuestro"]) - mo, math.log(x["mirova"]) - mm))
        def pendiente(xs, ys):
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            den = sum((a - mx) ** 2 for a in xs)
            return sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / den if den else None
        fe_n = pendiente([f[0] for f in fe], [f[1] for f in fe]) if len(fe) >= 4 else None
        fe_m = pendiente([f[0] for f in fe], [f[2] for f in fe]) if len(fe) >= 4 else None
        # control positivo: razon sintetica = media * cos(z)
        sint = [statistics.mean(rz) * math.cos(math.radians(a)) for a in z]
        res["por"][f"{vk}|{b}"] = {
            "n": len(S), "n_noches": len(noches), "fecha_min": min(x["dt"] for x in S), "fecha_max": max(x["dt"] for x in S),
            "razon_mediana_por_pasada": round(statistics.median(rz), 3),
            "spearman_razon_vs_z": round(sp, 3), "p_perm_dos_colas": round(p, 5),
            "bootstrap_noches_p2.5_p97.5": [round(bs[int(0.025 * len(bs))], 3), round(bs[int(0.975 * len(bs)) - 1], 3)] if bs else None,
            "spearman_z_vs_fecha": round(sp_fz, 3) if sp_fz is not None else None,
            "spearman_razon_vs_fecha": round(sp_fr, 3) if sp_fr is not None else None,
            "spearman_parcial_razon_z_dado_fecha": round(parcial(rz, z, fechas), 3) if parcial(rz, z, fechas) is not None else None,
            "efecto_fijo_noche_n_pares": len(fe),
            "pendiente_log_nuestro_por_grado_dentro_noche": round(fe_n, 4) if fe_n is not None else None,
            "pendiente_log_mirova_por_grado_dentro_noche": round(fe_m, 4) if fe_m is not None else None,
            "control_positivo_spearman_razon_sintetica": round(spearman(z, sint), 3),
            "mediana_razon_por_tramo_z": {k: (round(statistics.median([a / b for a, b in zip(
                [x["nuestro"] for x in S if lo <= x["z"] < hi], [x["mirova"] for x in S if lo <= x["z"] < hi])]), 3), sum(1 for x in S if lo <= x["z"] < hi))
                for k, (lo, hi) in {"<30": (0, 30), "30-50": (30, 50), "50-60": (50, 60), ">=60": (60, 99)}.items()
                if any(lo <= x["z"] < hi for x in S)},
        }
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k, v in res["por"].items():
    print(k, json.dumps(v, ensure_ascii=False))
print("control pares desplazado +1d (debe ser << pares):", ctl["pares_desplazado_1d"])
