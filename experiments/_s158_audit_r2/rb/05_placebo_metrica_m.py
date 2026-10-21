"""Afirmación 5: ¿la métrica M del evaluador de D25 da MEJORA con un brazo placebo de ganancia constante?
M (experiments/_s157_prereg_d25/evaluar_d25.py:159-160): d = |log10(D/M)| - |log10(K/M)| por par (K y D
publican, MIROVA tiene VRP); regla_m (l. 152-156): mediana de d con bootstrap por bloques noche-volcán
(pesos_bloque, l. 120-129; medianas_ponderadas, l. 138-149), MEJORA si el IC95 queda entero bajo 0.
Calibración 'sellada' (calibrar, l. 163-184): signo de e=|log10(D/K)| al azar por bloque; falsos <= 5 %.
Las cuatro funciones se copian VERBATIM abajo (no se importa evaluar_d25 para no arrastrar evaluar_fk y node).

Brazo placebo: D = g * K sobre pares REALES de PRODUCCIÓN (data/mirova_equivalent) contra la referencia de
MIROVA (latest_consolidado.csv + OCR del snapshot), NUNCA los datos del A/B. Pareo: misma (volcán, bucket) a
+-120 s, pasada nocturna (store._solar_elevation <= 0), alerta de MIROVA con VRP > 0 (tipo ALERTA_TERMICA u
_OCR), record nuestro con primary_cluster.vrp_mw > 0 y distance_class == 'summit' (aproximación al predicado
del tablero; para VIIRS 375 se usa f5_core_vrp_mw si existe, A10). Ventanas V1 y V2 del pre-registro.
Control: g = 1.0 debe dar 'sin cambio' (d = 0 en todos los pares, IC [0, 0]).
Pregunta 1: si M fuera insensible a una ganancia, g=1,2 y g=0,8 darían NEUTRO. Pregunta 2: si el pareo
fallara, n pares = 0 (se imprime) y no habría veredicto."""
import sys, io, os, csv, json, math, bisect, collections
from datetime import datetime, timedelta
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["VRP_PROFILE"] = "mirova_equivalent"
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
from pipeline.store import _solar_elevation
from referencia_mirova_unificada import normalize_sensor, normalize_volcano_name
import yaml

# ---- copia verbatim de evaluar_d25.py l. 68-70, 120-129, 138-149, 152-156, 159-160, 163-184
N_BOOT, SEMILLA = 10000, 157
N_CALIB, MAX_FALSOS_CALIB = 200, 0.05


def pesos_bloque(bloques, n_boot=N_BOOT, semilla=SEMILLA):
    uniq = sorted(set(bloques))
    idx = np.array([uniq.index(b) for b in bloques])
    rng = np.random.default_rng(semilla)
    elegidos = rng.integers(0, len(uniq), size=(n_boot, len(uniq)))
    cuenta = np.zeros((n_boot, len(uniq)), dtype=np.int64)
    np.add.at(cuenta, (np.repeat(np.arange(n_boot), len(uniq)), elegidos.ravel()), 1)
    return cuenta[:, idx]


def medianas_ponderadas(d, W):
    o = np.argsort(d)
    ds, Ws = np.asarray(d, dtype=np.float64)[o], W[:, o]
    cs = np.cumsum(Ws, axis=1)
    tot = cs[:, -1]
    lo_r, hi_r = (tot - 1) // 2, tot // 2
    i_lo = (cs <= lo_r[:, None]).sum(axis=1)
    i_hi = (cs <= hi_r[:, None]).sum(axis=1)
    return (ds[i_lo] + ds[i_hi]) / 2.0


def regla_m(d, W):
    meds = medianas_ponderadas(d, W)
    lo, hi = np.percentile(meds, 2.5), np.percentile(meds, 97.5)
    return ("MEJORA" if hi < 0 else "EMPEORA" if lo > 0 else "NEUTRO"), float(lo), float(hi)


def d_par(k_mw, d_mw, m_mw):
    return abs(math.log10(d_mw / m_mw)) - abs(math.log10(k_mw / m_mw))


def calibrar(pares, W, bloques, n_rep=N_CALIB, semilla=SEMILLA + 1):
    rng = np.random.default_rng(semilla)
    K = np.array([p["k"] for p in pares]); M = np.array([p["m"] for p in pares])
    e = np.abs(np.log10(np.array([p["d"] for p in pares]) / K))
    falsos = collections.Counter()
    bl = list(bloques)
    uniq = sorted(set(bl)); idx = np.array([uniq.index(b) for b in bl])
    for _ in range(n_rep):
        s = rng.choice((-1.0, 1.0), size=len(uniq))[idx]
        dd = np.abs(np.log10(K * 10 ** (s * e) / M)) - np.abs(np.log10(K / M))
        falsos[regla_m(dd, W)[0]] += 1
    hacia = np.sign(np.log10(M / K))
    dd = np.abs(np.log10(K * 10 ** (hacia * np.minimum(e, np.abs(np.log10(M / K)))) / M)) - np.abs(np.log10(K / M))
    poder = regla_m(dd, W)[0] == "MEJORA" if np.any(e > 0) else False
    return falsos["MEJORA"] / n_rep, falsos["EMPEORA"] / n_rep, bool(poder)
# ---- fin de la copia


VOLS = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima", "NevadosDeChillan",
        "PlanchonPeteroa", "PuyehueCordonCaulle", "Tupungatito", "Villarrica"]
coords = {v["name"]: (v["lat"], v["lon"]) for v in yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))["volcanoes"] if "lat" in v}
PROT = ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR")
ref = collections.defaultdict(list)   # (vol, bucket) -> [(dt, vrp)]
for path in ("latest_consolidado.csv", "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"):
    for r in csv.DictReader(open(path, encoding="utf-8")):
        vol = normalize_volcano_name(r.get("Volcan")); f = (r.get("Fecha_Satelite_UTC") or "").strip()
        if vol not in VOLS or len(f) < 16 or r.get("Tipo_Registro") not in PROT:
            continue
        try:
            v = float(r.get("VRP_MW") or 0)
        except ValueError:
            continue
        if v <= 0:
            continue
        ref[(vol, normalize_sensor(r.get("Sensor")))].append((datetime.strptime(f[:16], "%Y-%m-%d %H:%M"), v))
for k in ref:
    ref[k].sort()


def mirova_vrp(vol, b, t, tol=120):
    L = ref.get((vol, b), []); ts = [x[0] for x in L]
    i = bisect.bisect_left(ts, t - timedelta(seconds=tol)); out = []
    while i < len(L) and L[i][0] <= t + timedelta(seconds=tol):
        out.append(L[i][1]); i += 1
    return max(out) if out else None


def bucket_ours(s):
    return "MODIS" if s.startswith("MODIS") else "VIIRS750" if s.endswith("_750") else "VIIRS375"


def pares_ventana(desde, hasta):
    pares = collections.defaultdict(list); keys_geo = set()
    for vol in VOLS:
        recs = json.load(open(f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))
        recs = recs["records"] if isinstance(recs, dict) else recs
        for r in recs:
            t = r.get("datetime_utc") or ""
            if not (desde <= t[:10] <= hasta):
                continue
            b = bucket_ours(r["sensor"])
            if b == "MODIS":
                continue
            dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
            if _solar_elevation(coords[vol][0], coords[vol][1], dt) > 0:
                continue
            pc = r.get("primary_cluster") or {}
            k = pc.get("vrp_mw") or 0
            if b == "VIIRS375" and r.get("f5_core_vrp_mw"):
                k = r["f5_core_vrp_mw"]
            if k <= 0 or r.get("distance_class") != "summit":
                continue
            m = mirova_vrp(vol, b, dt)
            if not m:
                continue
            keys_geo |= {kk for kk in r if "zenith" in kk}
            pares[b].append({"k": k, "m": m, "bloque": f"{vol}|{t[:10]}", "vol": vol})
    return pares, keys_geo


for nombre, desde, hasta in (("V1", "2026-08-29", "2026-10-18"), ("V2", "2026-04-01", "2026-06-12")):
    pares, keys_geo = pares_ventana(desde, hasta)
    print(f"\n==== VENTANA {nombre} {desde}..{hasta}  (campos de cenit vistos: {sorted(keys_geo)})")
    for b in ("VIIRS750", "VIIRS375"):
        P = pares[b]
        if len(P) < 5:
            print(f"  {b}: n={len(P)} SIN SUSTRATO")
            continue
        bl = [p["bloque"] for p in P]; W = pesos_bloque(bl)
        razon = float(np.median([p["k"] / p["m"] for p in P]))
        n_bajo = sum(p["k"] < p["m"] for p in P)
        print(f"  {b}: n pares={len(P)} noches-volcan={len(set(bl))} | razon K/MIROVA mediana={razon:.3f} | pares con K<MIROVA: {n_bajo}")
        for g in (1.0, 1.2, 0.8, 1.5, 0.67, (1.0 / razon if razon > 0 else 1.0)):
            for p in P:
                p["d"] = g * p["k"]
            d = np.array([d_par(p["k"], p["d"], p["m"]) for p in P])
            r, lo, hi = regla_m(d, W)
            f_mej, f_emp, poder = calibrar(P, W, bl)
            calib = "OK" if f_mej + f_emp <= MAX_FALSOS_CALIB else "MAL CALIBRADA"
            print(f"     placebo g={g:.3f}: regla_m -> {r:8s} IC95 [{lo:+.4f}, {hi:+.4f}] d_mediana={float(np.median(d)):+.4f} | nulo sellado: falsos MEJORA {f_mej:.3f} EMPEORA {f_emp:.3f} ({calib}) poder={poder}")
        for p in P:
            p["d"] = 1.2 * p["k"]
        porv = collections.defaultdict(list)
        for p in P:
            porv[p["vol"]].append(d_par(p["k"], p["d"], p["m"]))
        print("     g=1.2 por volcan (n, mediana d):", {v: (len(x), round(float(np.median(x)), 3)) for v, x in sorted(porv.items())})


# ---------------------------------------------------------------- extensión: placebo con jitter y calibración 'simetrica'
# copia verbatim de evaluar_d25.py l. 187-199
def calibrar_simetrico(d, W, bloques, n_rep=N_CALIB, semilla=SEMILLA + 2):
    rng = np.random.default_rng(semilla)
    bl = list(bloques)
    uniq = sorted(set(bl)); idx = np.array([uniq.index(b) for b in bl])
    a = np.abs(np.asarray(d, dtype=np.float64))
    falsos = collections.Counter()
    for _ in range(n_rep):
        falsos[regla_m(rng.choice((-1.0, 1.0), size=len(uniq))[idx] * a, W)[0]] += 1
    poder = regla_m(-a, W)[0] == "MEJORA" if np.any(a > 0) else False
    return falsos["MEJORA"] / n_rep, falsos["EMPEORA"] / n_rep, bool(poder)


print("\n\n==== EXTENSION: placebo g=1.2 con jitter lognormal por par (sigma en log10 = 0.05 y 0.15) y las dos calibraciones")
rng = np.random.default_rng(11)
for nombre, desde, hasta in (("V1", "2026-08-29", "2026-10-18"), ("V2", "2026-04-01", "2026-06-12")):
    pares, _ = pares_ventana(desde, hasta)
    for b in ("VIIRS750", "VIIRS375"):
        P = pares[b]
        if len(P) < 5:
            continue
        bl = [p["bloque"] for p in P]; W = pesos_bloque(bl)
        for sig in (0.0, 0.05, 0.15):
            for p in P:
                p["d"] = 1.2 * p["k"] * 10 ** rng.normal(0, sig)
            d = np.array([d_par(p["k"], p["d"], p["m"]) for p in P])
            r, lo, hi = regla_m(d, W)
            fm, fe, po = calibrar(P, W, bl)
            sm, se, sp = calibrar_simetrico(d, W, bl)
            vols_neg = sum(float(np.median([d_par(p["k"], p["d"], p["m"]) for p in P if p["vol"] == v])) < 0
                           for v in set(p["vol"] for p in P) if sum(p["vol"] == v for p in P) >= 3)
            dec_sell = "INDECIDIBLE" if fm + fe > MAX_FALSOS_CALIB else r
            dec_sim = "INDECIDIBLE" if (sm > MAX_FALSOS_CALIB or se > MAX_FALSOS_CALIB) else ("NEUTRO (menos de 2 volcanes)" if r == "MEJORA" and vols_neg < 2 else r)
            print(f"  {nombre} {b} n={len(P)} g=1.2 jitter={sig:.2f}: regla_m {r:7s} IC [{lo:+.3f},{hi:+.3f}] | sellada falsos M {fm:.3f} E {fe:.3f} -> {dec_sell} | simetrica falsos M {sm:.3f} E {se:.3f} vols_neg={vols_neg} -> {dec_sim}")
