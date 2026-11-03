# -*- coding: utf-8 -*-
"""v01 (verificador V375, S173): pareo POR PASADA propio, sin banco_paridad ni node, K de produccion contra MIROVA en
Nevados de Chillan, VIIRS 375, por tramo de cenit, con Spearman y barajado.

POR QUE: el auditor midio con los helpers del repo (banco_paridad: node para el predicado del tablero, union CONS+OCR,
regla SN). Si esos helpers tuvieran un defecto comun, su s01 y su s03 lo heredarian juntos. Aqui se lee el JSON y los
CSV directamente:
  - pasada nuestra = record VIIRS_SNPP / VIIRS_NOAA20 / VIIRS_NOAA21 (sin sufijo _750; convencion A48) con datetime_utc.
  - fila de MIROVA = fila del CSV con Volcan 'Nevados de Chillan', Sensor 'VIIRS375', a +-TOL s de datetime_utc.
  - alerta de MIROVA = Tipo_Registro empieza por 'ALERTA' y no es ALERTA_SIN_GEOMETRIA_OCR, y VRP_MW > 0,05 (regla SN).
  - magnitud nuestra = f5_core_vrp_mw si > 0, si no primary_cluster.vrp_mw (lo que publica el tablero en banda I, A10
    matiz S132); «publicada» aproximada = distance_class == 'summit' y magnitud > 0 (sin node; se compara con el `disp`
    del auditor para medir cuanto difiere el predicado aproximado del real).
  - cenit = sensor_zenith_deg del record (es el del pixel mas cercano al final_hotspot, scan_geometry.observation_geometry).
Variantes: CONS sola / CONS+OCR; por pasada / por noche (maximo de MIROVA de la noche contra el nuestro de esa pasada);
tolerancia 120 s / 0 s (minuto exacto) / 600 s.
P1 (roto, lo veria): control positivo, razon * cos(z)^2 debe dar Spearman mas negativo y fuera del barajado; razon x2
   dobla la mediana. Control de pareo: con la referencia corrida +1 dia los pares deben caer casi a 0.
P2 (instrumento muerto): si el JSON o el CSV no se leyeran, n_records y n_filas serian 0 (se imprimen); si el cenit no
   estuviera, n_con_cenit seria 0.
Uso: python -I v01_pareo_propio.py <raiz copia_main> <s01_k_pasadas.csv del auditor o mi re-corrida> <salida.json>
"""
import csv, json, math, random, statistics, sys
from datetime import datetime, timedelta

ROOT, KCSV, OUT = sys.argv[1].rstrip("/\\"), sys.argv[2], sys.argv[3]
VOL, VOLM = "NevadosDeChillan", "Nevados de Chillan"
SNAP = ROOT + "/data/mirova_reference/mirova_v1_snapshot/"
INI, FIN = "2026-04-01", "2026-11-02"
SEMILLA, NB, CORTE = 173, 200, 30.0


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
    a, b = rank(x), rank(y)
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return None if den == 0 else num / den


def med(xs):
    return round(statistics.median(xs), 3) if xs else None


def resumen(pares, dentro_plataforma=True):
    """pares: (z, razon, plataforma). Barajado del cenit DENTRO de cada plataforma (la vara dice «dentro del sensor»;
    se imprime tambien el barajado global)."""
    z = [p[0] for p in pares]
    r = [p[1] for p in pares]
    out = {"n": len(pares), "mediana": med(r),
           "z<30": {"n": sum(1 for q in z if q < CORTE), "mediana": med([b for a, b in zip(z, r) if a < CORTE])},
           "z>=30": {"n": sum(1 for q in z if q >= CORTE), "mediana": med([b for a, b in zip(z, r) if a >= CORTE])},
           "z>=50": {"n": sum(1 for q in z if q >= 50), "mediana": med([b for a, b in zip(z, r) if a >= 50])},
           "noches_distintas": None}
    if len(pares) < 8:
        out["spearman"] = "SIN DATO (n < 8)"
        return out
    s = spearman(z, r)
    rnd = random.Random(SEMILLA)
    sb_g, sb_p = [], []
    plats = sorted({p[2] for p in pares})
    for _ in range(NB):
        zz = list(z)
        rnd.shuffle(zz)
        sb_g.append(spearman(zz, r))
        zp = list(z)
        for pl in plats:
            idx = [i for i, p in enumerate(pares) if p[2] == pl]
            vals = [z[i] for i in idx]
            rnd.shuffle(vals)
            for i, v in zip(idx, vals):
                zp[i] = v
        sb_p.append(spearman(zp, r))
    def ic(sb):
        sb = sorted(x for x in sb if x is not None)
        return [round(sb[int(0.025 * len(sb))], 3), round(sb[int(0.975 * len(sb)) - 1], 3), round(statistics.median(sb), 3)]
    g, p = ic(sb_g), ic(sb_p)
    out.update({"spearman": round(s, 3), "barajado_global_[2.5,97.5,mediana]": g, "fuera_global": not (g[0] <= s <= g[1]),
                "barajado_por_plataforma_[2.5,97.5,mediana]": p, "fuera_por_plataforma": not (p[0] <= s <= p[1])})
    return out


# --- referencia
def leer(fn):
    out = []
    for r in csv.DictReader(open(fn, encoding="utf-8", errors="replace")):
        if r["Volcan"] != VOLM or r["Sensor"] != "VIIRS375":
            continue
        try:
            t = datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        if not (INI <= r["Fecha_Satelite_UTC"][:10] <= FIN):
            continue
        out.append({"t": t, "tipo": r["Tipo_Registro"], "vrp": f(r["VRP_MW"]), "dist": f(r["Distancia_km"])})
    return out


cons = leer(SNAP + "registro_vrp_consolidado.csv")
ocr = leer(SNAP + "registro_vrp_ocr.csv")
for x in cons:
    x["src"] = "CONS"
for x in ocr:
    x["src"] = "OCR"
print("filas referencia V375 Chillan en ventana: CONS", len(cons), "OCR", len(ocr))


def es_alerta(x):
    return x["tipo"].startswith("ALERTA") and x["tipo"] != "ALERTA_SIN_GEOMETRIA_OCR" and x["vrp"] is not None and x["vrp"] > 0.05


# --- records
d = json.load(open(ROOT + "/data/mirova_equivalent/" + VOL + ".json", encoding="utf-8"))
recs = []
for r in d["records"]:
    s = r.get("sensor") or ""
    if not s.startswith("VIIRS") or s.endswith("_750"):
        continue
    if not (INI <= r.get("datetime_utc", "")[:10] <= FIN):
        continue
    t = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
    pc = r.get("primary_cluster") or {}
    f5 = f(r.get("f5_core_vrp_mw"))
    mag = f5 if (f5 is not None and f5 > 0) else f(pc.get("vrp_mw"))
    recs.append({"t": t, "dt": r["datetime_utc"], "plat": s, "z": f(r.get("sensor_zenith_deg")), "mag": mag,
                 "dc": r.get("distance_class"), "sol": f(r.get("solar_zenith_deg")),
                 "sha": (r.get("regimen") or {}).get("codigo_sha"), "proc": r.get("processed_utc")})
print("records V375 Chillan en ventana:", len(recs), "| con cenit:", sum(1 for r in recs if r["z"] is not None))

# auditor (para comparar el predicado)
A = {(r["sensor"], r["dt"]): r for r in csv.DictReader(open(KCSV, encoding="utf-8")) if r["b"] == "VIIRS375"}


def parear(ref, t, tol):
    return [x for x in ref if abs((x["t"] - t).total_seconds()) <= tol]


def correr(ref, tol, shift_dias=0, por_noche=False):
    pares, sin_par_alerta, pub_sin_alerta, desacuerdo_pred = [], 0, 0, 0
    for r in recs:
        al = [x for x in parear(ref, r["t"] + timedelta(days=shift_dias), tol) if es_alerta(x)]
        if por_noche:
            noche = (r["t"] - timedelta(hours=12)).strftime("%Y-%m-%d")
            al = [x for x in ref if es_alerta(x) and (x["t"] - timedelta(hours=12)).strftime("%Y-%m-%d") == noche]
        if not al:
            continue
        c = [x for x in al if x["src"] == "CONS"]
        vm = max((c or al), key=lambda x: x["vrp"])["vrp"] if por_noche else (c or al)[0]["vrp"]
        pub = r["dc"] == "summit" and r["mag"] is not None and r["mag"] > 0
        a = A.get((r["plat"], r["dt"]))
        if a is not None and ((a["pub"] == "1") != pub):
            desacuerdo_pred += 1
        if not pub:
            sin_par_alerta += 1
            continue
        if r["z"] is None:
            continue
        pares.append((r["z"], r["mag"] / vm, r["plat"], r["dt"]))
    res = resumen([p[:3] for p in pares])
    res["noches_distintas"] = len({(datetime.strptime(p[3], "%Y-%m-%d %H:%M") - timedelta(hours=12)).strftime("%Y-%m-%d") for p in pares})
    res["alertas_MIROVA_sin_publicacion_nuestra"] = sin_par_alerta
    res["desacuerdo_predicado_aprox_vs_node_auditor"] = desacuerdo_pred
    res["ventana_pares"] = [min(p[3] for p in pares), max(p[3] for p in pares)] if pares else None
    return res, pares


out = {}
out["CONS+OCR_tol120"], P = correr(cons + ocr, 120)
out["CONS_sola_tol120"], _ = correr(cons, 120)
out["CONS+OCR_tol0_minuto_exacto"], _ = correr(cons + ocr, 59)
out["CONS+OCR_tol600"], _ = correr(cons + ocr, 600)
out["CONS+OCR_por_noche"], _ = correr(cons + ocr, 120, por_noche=True)
out["control_neg_ref_+1dia"], _ = correr(cons + ocr, 120, shift_dias=1)
out["control_pos_cos2"] = resumen([(z, q * math.cos(math.radians(z)) ** 2, s) for z, q, s, _ in P])
out["control_pos_x2_mediana"] = med([2 * q for _, q, _, _ in P])
# el mismo conjunto de pares que el auditor (A) : coincidencia pasada a pasada
mios = {(p[2], p[3]) for p in P}
suyos = {k for k, v in A.items() if f(v["vrp_M"]) and f(v["vrp_M"]) > 0 and v["pub"] == "1" and f(v["disp"]) and f(v["disp"]) > 0}
out["pares_mios_vs_auditor"] = {"mios": len(mios), "auditor": len(suyos), "comunes": len(mios & suyos),
                                "solo_mios": sorted(mios - suyos), "solo_auditor": sorted(suyos - mios)}
# razon mia vs disp/vrp_M del auditor en los comunes
dif = []
for z, q, s, dt in P:
    a = A.get((s, dt))
    if a and (s, dt) in suyos:
        dif.append(abs(q - f(a["disp"]) / f(a["vrp_M"])))
out["dif_max_razon_vs_auditor_en_comunes"] = max(dif) if dif else None
# por plataforma y por sha de codigo
out["por_plataforma"] = {pl: resumen([p[:3] for p in P if p[2] == pl]) for pl in sorted({p[2] for p in P})}
shas = {}
for z, q, s, dt in P:
    r = next(x for x in recs if x["plat"] == s and x["dt"] == dt)
    shas.setdefault((r["sha"] or "?")[:9], []).append((z, q, s))
out["por_codigo_sha"] = {k: resumen(v) for k, v in shas.items()}
# influencia de cada par: Spearman sin cada pasada (jackknife), extremos
base = out["CONS+OCR_tol120"]["spearman"]
jk = []
for i in range(len(P)):
    sub = [p for j, p in enumerate(P) if j != i]
    jk.append((round(spearman([p[0] for p in sub], [p[1] for p in sub]), 3), P[i][3], P[i][2]))
jk.sort()
out["jackknife_spearman_min_max"] = {"base": base, "min": jk[0], "max": jk[-1]}
out["detalle_pares"] = [{"dt": dt, "plat": s, "z": round(z, 1), "razon": round(q, 3)} for z, q, s, dt in sorted(P)]
json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in out.items() if k != "detalle_pares"}, indent=1, ensure_ascii=False))
