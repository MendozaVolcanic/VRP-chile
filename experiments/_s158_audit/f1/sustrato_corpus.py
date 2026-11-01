# -*- coding: utf-8 -*-
"""F1 (S158): sustrato, en los records publicados de VIIRS 750, de cada diferencia con el código de MIROVA.

Entrada: data/mirova_equivalent/<volcán>.json (11 Tier A), pub_v750.json (predicado del tablero con node,
predicado_tablero.js), volcanoes.yaml. Ventana K: datetime_utc >= 2026-09-18 (fecha en que los datos cambian de
detector, CLAUDE.md marca S157) hasta el último record. También se informa el corpus entero cuando la medición no
depende del detector.

Las dos preguntas del instrumento van en el encabezado de cada bloque impreso.
Uso: python -B experiments/_s158_audit/f1/sustrato_corpus.py
"""
import io, json, math, os, sys
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import yaml

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
VOLS = ["Isluga", "Lascar", "Lastarria", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue",
        "Llaima", "Villarrica", "PuyehueCordonCaulle", "Chaiten"]
K_DESDE = "2026-09-18"
C1, C2 = 1.191042e8, 14388.0


def planck(T, lam=4.05):
    return C1 / (lam ** 5 * (math.exp(C2 / (lam * T)) - 1))


def dxdy_km(lat, lon, lat0, lon0):
    dy = (lat - lat0) * 111.32
    dx = (lon - lon0) * 111.32 * math.cos(math.radians(lat0))
    return dx, dy


cfg = {x["name"]: x for x in yaml.safe_load(open(os.path.join(RAIZ, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
pub = {(p["v"], p["t"], p["s"]): p for p in json.load(open(os.path.join(AQUI, "pub_v750.json"), encoding="utf-8"))}

recs = []
for v in VOLS:
    d = json.load(open(os.path.join(RAIZ, "data", "mirova_equivalent", v + ".json"), encoding="utf-8"))
    for r in d["records"]:
        if str(r.get("sensor", "")).endswith("_750"):
            p = pub.get((v, r["datetime_utc"], r["sensor"]))
            recs.append((v, r, p))
print("records V750 cargados:", len(recs), " con predicado:", sum(1 for x in recs if x[2] is not None))
fechas = sorted(r["datetime_utc"] for _, r, _ in recs)
print("ventana del corpus:", fechas[0], "a", fechas[-1])
K = [(v, r, p) for v, r, p in recs if r["datetime_utc"] >= K_DESDE]
print("ventana K (>= %s): %d records, %s a %s" % (K_DESDE, len(K), min(r["datetime_utc"] for _, r, _ in K),
                                                   max(r["datetime_utc"] for _, r, _ in K)))
KP = [(v, r, p) for v, r, p in K if p and p["pub"] > 0]
print("publicados en el tablero (pub > 0) en ventana K:", len(KP))
# control positivo del join: el predicado debe dar algún publicado y algún no publicado
print("CONTROL join: pub>0 %d, pub=0 %d (si alguno es 0, el join o el predicado están muertos)" %
      (len(KP), len(K) - len(KP)))

# ----------------------------------------------------------------------------------------------------------
print("\n== 1. Mínimos fijos de los Tests 2 y 3 (primer pase) contra los del código de MIROVA ==")
print("Instrumento 1: si el mínimo de MIROVA nunca decidiera, la fracción daría 0; si siempre, 1. Se ve.")
print("Instrumento 2: records sin diag_sd_dnti (detector muerto) se cuentan aparte como SIN DATO.")
print("Unidades: nuestro dNTI usa 8 vecinos; el de MIROVA, 9 con el central, = 8/9 del nuestro. Un mínimo F de")
print("MIROVA equivale a 9F/8 en nuestras unidades: NTI fuera 0,0225, ETI fuera 0,01125, cumbre 0,003375.")
for nombre, sel in (("corpus entero", recs), ("ventana K", K), ("publicados K", KP)):
    c = Counter(); sin = 0
    for v, r, p in sel:
        mu, sd, mue, sde = r.get("diag_mu_dnti"), r.get("diag_sd_dnti"), r.get("diag_mu_deti"), r.get("diag_sd_deti")
        if sd is None or mue is None:
            sin += 1; continue
        c["n"] += 1
        s10 = mu + 10 * sd; e10 = mue + 10 * sde; s5 = mu + 5 * sd; e5 = mue + 5 * sde
        c["fuera_NTI_nuestro_min_decide(<0.01)"] += s10 < 0.01
        c["fuera_NTI_MIROVA_min_decide(<0.0225)"] += s10 < 0.0225
        c["fuera_NTI_umbral_sube(MIROVA>nuestro)"] += max(s10, 0.0225) > max(s10, 0.01)
        c["fuera_ETI_MIROVA_min_decide(<0.01125)"] += e10 < 0.01125
        c["cumbre_NTI_MIROVA_min_decide(<0.003375)"] += s5 < 0.003375
        c["cumbre_ETI_MIROVA_min_decide(<0.003375)"] += e5 < 0.003375
        c["razon_fuera_NTI_MIROVA/nuestro>=1.5"] += max(s10, 0.0225) / max(s10, 0.01) >= 1.5
    n = c.pop("n", 0)
    print(f" {nombre}: n={n} (SIN DATO {sin})")
    for k, x in c.items():
        print(f"   {k:45s} {x:6d}  {100 * x / max(n, 1):5.1f} %")
    if sel:
        arr = np.array([r["diag_mu_dnti"] + 10 * r["diag_sd_dnti"] for _, r, _ in sel if r.get("diag_sd_dnti") is not None])
        if arr.size:
            print("   mu+10sd dNTI percentiles 5/50/95:", np.round(np.percentile(arr, [5, 50, 95]), 4))

# ----------------------------------------------------------------------------------------------------------
print("\n== 2. Región sensible: nuestro círculo inner_radius_km (centrado en el cráter) contra la caja 7x7 de MIROVA ==")
print("La caja de MIROVA (BOX==2 en el ejemplo, filas 30-36 y columnas 30-36 de 67) mide ±2,625 km del centro de su")
print("grilla (mirova_center). Fuera de ella rigen 10 sigma y 0,02/0,01; dentro de nuestro círculo rigen 5 sigma y 0,003.")
print("Instrumento 1: la distancia vent a mirova_center se imprime; si todo cayera dentro, la fracción sería 0.")
print("Instrumento 2: records publicados sin anomaly_pixels en el inner se cuentan como SIN DATO.")
tot = Counter(); porvol = defaultdict(Counter)
for v, r, p in KP:
    cf = cfg[v]
    mlat, mlon = cf.get("mirova_center_lat", cf["lat"]), cf.get("mirova_center_lon", cf["lon"])
    vlat, vlon = cf.get("vent_lat", mlat), cf.get("vent_lon", mlon)
    inner = cf["inner_radius_km"]
    px = []
    for q in r.get("anomaly_pixels") or []:
        dxv, dyv = dxdy_km(q["lat"], q["lon"], vlat, vlon)
        if math.hypot(dxv, dyv) <= inner:
            dx, dy = dxdy_km(q["lat"], q["lon"], mlat, mlon)
            px.append((max(abs(dx), abs(dy)), q.get("vrp_mw") or 0))
    if not px:
        tot["sin_dato"] += 1; porvol[v]["sin_dato"] += 1; continue
    tot["n"] += 1; porvol[v]["n"] += 1
    fuera = [x for x in px if x[0] > 2.625]
    tot["px"] += len(px); tot["px_fuera"] += len(fuera)
    porvol[v]["px"] += len(px); porvol[v]["px_fuera"] += len(fuera)
    if len(fuera) == len(px):
        tot["rec_todo_fuera"] += 1; porvol[v]["rec_todo_fuera"] += 1
    pico = max(px, key=lambda x: x[1])
    if pico[0] > 2.625:
        tot["rec_pico_fuera"] += 1; porvol[v]["rec_pico_fuera"] += 1
    tot["mw"] += sum(x[1] for x in px); tot["mw_fuera"] += sum(x[1] for x in fuera)
print(f" publicados K con píxeles en el inner: {tot['n']} (SIN DATO {tot['sin_dato']})")
print(f"   píxeles en el inner: {tot['px']}, fuera de la caja 7x7 de MIROVA: {tot['px_fuera']} ({100*tot['px_fuera']/max(tot['px'],1):.1f} %)")
print(f"   records con TODOS sus píxeles del inner fuera de la caja: {tot['rec_todo_fuera']} ({100*tot['rec_todo_fuera']/max(tot['n'],1):.1f} %)")
print(f"   records con el píxel de más VRP fuera de la caja: {tot['rec_pico_fuera']} ({100*tot['rec_pico_fuera']/max(tot['n'],1):.1f} %)")
print(f"   VRP por píxel (recortado) fuera de la caja: {tot['mw_fuera']:.2f} de {tot['mw']:.2f} MW")
for v in VOLS:
    c = porvol[v]; cf = cfg[v]
    mlat, mlon = cf.get("mirova_center_lat", cf["lat"]), cf.get("mirova_center_lon", cf["lon"])
    dxv, dyv = dxdy_km(cf.get("vent_lat", mlat), cf.get("vent_lon", mlon), mlat, mlon)
    print(f"   {v:20s} inner {cf['inner_radius_km']:>2} km  cráter a {math.hypot(dxv,dyv):4.2f} km del centro de grilla | "
          f"rec {c['n']:4d}  px {c['px']:5d}  px fuera {c['px_fuera']:5d}  rec todo fuera {c['rec_todo_fuera']:4d}  pico fuera {c['rec_pico_fuera']:4d}")

# ----------------------------------------------------------------------------------------------------------
print("\n== 3. Fondo escalar del anillo y recorte a cero (MIROVA: fondo interpolado local, sin recorte) ==")
print("Instrumento 1: si el recorte nunca actuara no habría píxeles con vrp 0 y bt < t_bg; se cuentan.")
print("Instrumento 2: control positivo: el VRP recomputado desde bt_k y t_bg_k debe reproducir el vrp_mw guardado")
print("en los píxeles con vrp > 0 (si no, la fórmula del instrumento es otra que la del pipeline).")
err = []; c3 = Counter()
for v, r, p in K:
    tb = r.get("t_bg_k")
    for q in r.get("anomaly_pixels") or []:
        if tb is None or q.get("bt_k") is None:
            continue
        dl = planck(q["bt_k"]) - planck(tb)
        vr = 562500 * 19.7 * dl / 1e6
        if (q.get("vrp_mw") or 0) > 0.01:
            err.append(abs(vr - q["vrp_mw"]) / q["vrp_mw"])
print(f" control: {len(err)} píxeles con vrp>0,01 MW; error relativo mediano {np.median(err):.2e}, p99 {np.percentile(err,99):.2e}")
for nombre, sel in (("ventana K todos", K), ("ventana K publicados", KP)):
    c3 = Counter()
    for v, r, p in sel:
        tb = r.get("t_bg_k"); cf = cfg[v]
        vlat, vlon = cf.get("vent_lat", cf["lat"]), cf.get("vent_lon", cf["lon"])
        inner_px = []; allpx = r.get("anomaly_pixels") or []
        for q in allpx:
            c3["px"] += 1
            if q.get("bt_k") is None or tb is None:
                continue
            dl = planck(q["bt_k"]) - planck(tb)
            vr = 562500 * 19.7 * dl / 1e6
            if (q.get("vrp_mw") or 0) == 0:
                c3["px_recortados"] += 1
                c3["mw_negativo_quitado"] += vr
            if math.hypot(*dxdy_km(q["lat"], q["lon"], vlat, vlon)) <= cf["inner_radius_km"]:
                inner_px.append(q)
        if inner_px:
            c3["rec_con_px_inner"] += 1
            if all((q.get("vrp_mw") or 0) == 0 for q in inner_px):
                c3["rec_inner_todo_recortado"] += 1
                if not (p and p["pub"] > 0):
                    c3["rec_inner_todo_recortado_NO_publicado"] += 1
            if not (p and p["pub"] > 0):
                c3["rec_con_px_inner_NO_publicado"] += 1
    print(f" {nombre}: píxeles {c3['px']}, recortados a 0 {c3['px_recortados']} ({100*c3['px_recortados']/max(c3['px'],1):.1f} %),"
          f" magnitud negativa que el recorte deja de restar {c3['mw_negativo_quitado']:.2f} MW")
    print(f"   records con píxel detectado dentro del inner: {c3['rec_con_px_inner']}; de ellos con TODOS esos píxeles en 0:"
          f" {c3['rec_inner_todo_recortado']}; y además NO publicados: {c3['rec_inner_todo_recortado_NO_publicado']};"
          f" con píxel en el inner y no publicados por cualquier razón: {c3['rec_con_px_inner_NO_publicado']}")
# t_bg contra la BT del píxel publicado: el fondo del anillo frente al cráter
dif = [q["bt_k"] - r["t_bg_k"] for v, r, p in KP for q in (r.get("anomaly_pixels") or [])[:1] if r.get("t_bg_k")]
print(f" publicados K: BT del píxel de más VRP menos t_bg, percentiles 5/50/95: {np.round(np.percentile(dif,[5,50,95]),2)} K (n={len(dif)})")

# ----------------------------------------------------------------------------------------------------------
print("\n== 4. Lo que se publica: cúmulo vent_anchored + modo de un píxel, contra la suma de todos los alertados ==")
print("Instrumento 1: si publicáramos la unión, la razón publicado/suma daría 1 siempre; se mide su distribución.")
print("Instrumento 2: records con vrp_mw (suma de escena) = 0 se excluyen y se cuentan.")
rz = []; rz_inner = []; c4 = Counter(); spm = Counter()
for v, r, p in KP:
    pc = r.get("primary_cluster") or {}
    if pc.get("single_pixel_mode"):
        spm["single_pixel_mode"] += 1
        if (pc.get("n_pixels") or 0) > 1:
            spm["spm_con_mas_de_1_px"] += 1
    if pc.get("d9_capped"):
        spm["d9_capped"] += 1
    s_all = sum((q.get("vrp_mw") or 0) for q in (r.get("anomaly_pixels") or []) + (r.get("discarded_anomaly_pixels") or []))
    if s_all <= 0:
        c4["suma0"] += 1; continue
    rz.append(p["pub"] / s_all)
print(f" publicados K: {len(KP)}; modo de un píxel activo {spm['single_pixel_mode']} (con >1 px {spm['spm_con_mas_de_1_px']}); tope D9 {spm['d9_capped']}")
print(f"   razón publicado / suma de todos los píxeles guardados (unión, top-100 + descartados): n={len(rz)} (suma 0: {c4['suma0']})")
if rz:
    print("   percentiles 5/25/50/75/95:", np.round(np.percentile(rz, [5, 25, 50, 75, 95]), 3),
          " fracción con razón < 0,9:", round(float(np.mean(np.array(rz) < 0.9)), 3))
nmax = Counter(len(r.get("anomaly_pixels") or []) >= 100 for v, r, p in KP)
print("   records publicados con 100 píxeles guardados (unión truncada, la razón es cota superior):", nmax[True])

# ----------------------------------------------------------------------------------------------------------
print("\n== 5. Escena incompleta (MIROVA rechaza con >= la mitad de NaN en la grilla 67x67) ==")
print("Proxy: diag_n_bg_used_first_pass (píxeles válidos del ROI 50x50 km) contra el p95 de su clase de cenit (5 grados).")
print("Instrumento 1: si no hubiera escenas parciales, ninguna caería bajo 50 % del p95. Instrumento 2: n=0 = SIN DATO.")
porbin = defaultdict(list)
for v, r, p in recs:
    z = r.get("sensor_zenith_deg"); n = r.get("diag_n_bg_used_first_pass")
    if z is None or not n:
        continue
    porbin[(v, int(z // 5))].append(n)
p95 = {k: np.percentile(x, 95) for k, x in porbin.items() if len(x) >= 20}
c5 = Counter()
for nombre, sel in (("ventana K", K), ("publicados K", KP)):
    c5 = Counter()
    for v, r, p in sel:
        z = r.get("sensor_zenith_deg"); n = r.get("diag_n_bg_used_first_pass")
        if z is None or not n:
            c5["sin_dato"] += 1; continue
        ref = p95.get((v, int(z // 5)))
        if ref is None:
            c5["sin_ref"] += 1; continue
        c5["n"] += 1
        if n < 0.5 * ref:
            c5["bajo_50"] += 1
    print(f" {nombre}: n={c5['n']} (SIN DATO {c5['sin_dato']}, sin referencia de cenit {c5['sin_ref']}); bajo 50 % del p95: {c5['bajo_50']}")

# ----------------------------------------------------------------------------------------------------------
print("\n== 6. Test 1 absoluto: K1 -0,7 de MIROVA (alerta directa) contra -0,8 (sólo diagnóstico y predicado D9) ==")
print("nti_max es el máximo de NTI en el ROI de 50 x 50 km. Instrumento 1: si ningún píxel pasara -0,7 la cuenta sería 0.")
c6 = Counter()
for v, r, p in K:
    nm = r.get("nti_max")
    if nm is None:
        c6["sin_dato"] += 1; continue
    c6["n"] += 1
    if nm > -0.7:
        c6["nti_max>-0.7"] += 1
        c6["nti_max>-0.7_y_publicado"] += bool(p and p["pub"] > 0)
    if -0.8 < nm <= -0.7:
        c6["entre_-0.8_y_-0.7"] += 1
print(" ventana K:", dict(c6))

# ----------------------------------------------------------------------------------------------------------
print("\n== 7. Píxel frío (MIROVA anula BT M15 <= 200 K) ==")
tb = np.array([r["t_bg_k"] for v, r, p in recs if r.get("t_bg_k")])
print(" t_bg_k (mediana M13 del anillo, NO es M15) mínimo %.1f K; records con t_bg < 220 K: %d de %d" %
      (tb.min(), int((tb < 220).sum()), tb.size))

# ----------------------------------------------------------------------------------------------------------
print("\n== 8. Tope por tamaño de cúmulo (Villarrica, max_cluster_pixels 12) y su efecto en el tablero ==")
c8 = Counter()
for v, r, p in recs:
    if r.get("discarded_reason") == "cluster_too_large_for_volcano":
        c8["records_tope"] += 1
        c8["con_pub>0_en_tablero"] += bool(p and p["pub"] > 0)
        c8["isValidDetection"] += bool(p and p["valid"])
print(" corpus entero:", dict(c8))

# ----------------------------------------------------------------------------------------------------------
print("\n== 9. Píxeles guardados con BT de M13 cerca del techo (634 K, se anulan antes de detectar) ==")
tm = [r.get("t_max_k") for v, r, p in recs if r.get("t_max_k")]
print(" t_max_k máximo en el corpus V750: %.1f K; records con t_max >= 400 K: %d" % (max(tm), sum(t >= 400 for t in tm)))
