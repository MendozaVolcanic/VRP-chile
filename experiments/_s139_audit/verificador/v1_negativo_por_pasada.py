"""S139 VERIFICADOR v1: el negativo mas limpio que existe hoy, POR PASADA, y de que esta hecha
la sobre-publicacion de VIIRS 375.

POR QUE: los ejes 1 a 4 discuten si RUTINA vale como negativo por NOCHE (pasadas omitidas, nube,
borde de barrido). Por pasada el problema de las pasadas omitidas desaparece: si MIROVA listo
ESE granule con VRP 0, proceso ese granule y no informo nada. Si aun asi publicamos ahi, la
divergencia es de ese granule, no de la cobertura de la referencia.

Instrumento.
 P1 (si lo medido estuviera roto, lo veria?): si publicaramos todo, la tasa en negativos por
    pasada iria a 1; si no publicaramos nada, la tasa en positivos iria a 0.
 P2 (instrumento muerto?): (a) el predicado portado a Python se valida contra el predicado que el
    eje 2 ejecuto con node sobre el HTML (acuerdo por noche-sensor); (b) control negativo del
    pareo: corriendo nuestro reloj +3 h el pareo VIIRS debe caer a ~0; (c) SIN_FILA se cuenta
    aparte, nunca como negativo.
 Control positivo: pasadas pareadas con ALERTA_TERMICA deben publicar mucho mas que las RUTINA.
Ventana: 2026-01-10 a 2026-09-07 (fin del OCR snapshot, para que el contexto de noche con alerta
incluya OCR). 11 Tier A. Pasadas nocturnas (angulo solar >= 90, o hora UTC <= 11 si falta).
"""
import csv, json, sys, io, bisect, pathlib, statistics as st
from datetime import datetime, timedelta
from collections import defaultdict, Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R))
from pipeline.mirova_csv_loader import normalize_volcano_name, normalize_sensor  # noqa

INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3, "NevadosDeChillan": 5,
         "Chaiten": 5, "Villarrica": 5, "Llaima": 5, "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
T0, T1 = "2026-01-10", "2026-09-07 23:59"


def bucket(s):
    s = str(s or "").upper()
    if s.startswith("MODIS"):
        return "MODIS"
    return "VIIRS750" if s.endswith("_750") else "VIIRS375"


# ---- port literal de frontend/index.html (mirovaEqVrp 1043-1065, isCirrusArtifact, isDiffuseFieldArtifact,
# ---- isValidDetection 1466-1478, isSummitDetection 1480-1488), _mirova_confirmed = false
def eq(r, inner):
    pc = r.get("primary_cluster")
    if not pc:
        v = r.get("vrp_mw") if r.get("vrp_mw") is not None else (r.get("vrp_mir_mw") or 0)
        v = v or 0
        return 0 if v > 50000 else v
    dc = r.get("distance_class")
    if dc and dc != "summit":
        return 0
    if pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] > inner:
        return 0
    v = pc.get("vrp_mw") or 0
    return 0 if v > 50000 else v


def artefacto(r, inner):
    t = r.get("t_max_k")
    if t is not None and t < 273.15 and eq(r, inner) > 10:
        return True
    pc = r.get("primary_cluster")
    if not pc or t is None or t >= 278.15:
        return False
    npx = pc.get("n_pixels") or 0
    if npx < 100:
        return False
    e = eq(r, inner)
    return e >= 50 and (e / npx) < 1.0


def valida(r):
    if r.get("primary_cluster"):
        return (r["primary_cluster"].get("vrp_mw") or 0) > 0
    if (r.get("vrp_mw") or 0) > 0:
        return True
    return r.get("triggered_test1") is True


def summit(r):
    if (r.get("vrp_mw") or 0) == 0 and r.get("discarded_reason") and not r.get("triggered_test1"):
        return False
    if r.get("distance_class") == "summit":
        return True
    if r.get("distance_class") == "far":
        return False
    return (r.get("vrp_vent_mw") or 0) > 0


def publica(r, inner):
    return summit(r) and valida(r) and not artefacto(r, inner) and eq(r, inner) > 0


# ---- referencia
cons = defaultdict(list)          # (vol,b) -> [(t, tipo, vrp)]
alerta_noche = set()              # (vol, fecha)  ALERTA nocturna CONS u OCR, cualquier sensor
fp_noche = set()
mir_alerta_vrp = defaultdict(list)
for fname, es_ocr in (("latest_consolidado.csv", False),
                      ("data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv", True)):
    for row in csv.DictReader(open(R / fname, encoding="utf-8", errors="replace")):
        vol = normalize_volcano_name(row.get("Volcan"))
        f = (row.get("Fecha_Satelite_UTC") or "")[:19]
        if vol is None or not (T0 <= f <= T1):
            continue
        b = normalize_sensor(row.get("Sensor"))
        t = datetime.strptime(f, "%Y-%m-%d %H:%M:%S")
        tipo = row.get("Tipo_Registro") or ""
        noct = t.hour <= 11
        try:
            v = float(row.get("VRP_MW") or 0)
        except ValueError:
            v = 0
        if es_ocr:
            if tipo == "ALERTA_TERMICA_OCR" and noct:
                alerta_noche.add((vol, f[:10]))
            continue
        cons[(vol, b)].append((t, tipo, v))
        if noct and tipo == "ALERTA_TERMICA":
            alerta_noche.add((vol, f[:10]))
            mir_alerta_vrp[b].append(v)
        if noct and tipo == "FALSO_POSITIVO":
            fp_noche.add((vol, f[:10]))
for k in cons:
    cons[k].sort()


def parear(vol, b, t, tol=120):
    L = cons.get((vol, b), [])
    ts = [x[0] for x in L]
    i = bisect.bisect_left(ts, t - timedelta(seconds=tol))
    best = None
    while i < len(L) and L[i][0] <= t + timedelta(seconds=tol):
        if best is None or abs((L[i][0] - t).total_seconds()) < abs((best[0] - t).total_seconds()):
            best = L[i]
        i += 1
    return best


def zbin(z):
    if z is None:
        return "z?"
    return "z<30" if z < 30 else ("z30-50" if z < 50 else ("z50-60" if z < 60 else "z>=60"))


# ---- nuestros records
filas = []
for vol in INNER:
    for r in json.load(open(R / f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))["records"]:
        d = r["datetime_utc"]
        if not (T0 <= d <= T1):
            continue
        t = datetime.strptime(d, "%Y-%m-%d %H:%M")
        sz = r.get("solar_zenith_deg")
        if (sz is not None and sz < 90) or (sz is None and t.hour > 11):
            continue
        filas.append((vol, bucket(r["sensor"]), t, r))

# ---- validacion del port contra el node del eje 2 (noche-sensor, noche = fecha UTC)
tab = json.load(open(R / "experiments/_s139_audit/eje2/banco_tabla.json", encoding="utf-8"))
node = {(x["vol"], x["b"], x["noche"]): (x["nos"] or {}).get("pub", 0) > 0 for x in tab if x.get("nos")}
mio = defaultdict(bool)
for vol, b, t, r in filas:
    mio[(vol, b, t.strftime("%Y-%m-%d"))] |= publica(r, INNER[vol])
comunes = [k for k in mio if k in node]
acuerdo = sum(mio[k] == node[k] for k in comunes)
print(f"VALIDACION port Python vs node (eje 2): {acuerdo}/{len(comunes)} noches-sensor coinciden")

# ---- control negativo del pareo
for shift in (0, 3):
    c = Counter()
    for vol, b, t, r in filas:
        c[(b, parear(vol, b, t + timedelta(hours=shift)) is not None)] += 1
    print(f"pareo reloj +{shift} h:", {bb: f"{c[(bb, True)]}/{c[(bb, True)] + c[(bb, False)]}"
                                       for bb in ("MODIS", "VIIRS375", "VIIRS750")})

# ---- clasificacion por pasada
res = defaultdict(lambda: [0, 0])
porvol = defaultdict(lambda: [0, 0])
porz = defaultdict(lambda: [0, 0])
sinfila_z = defaultdict(lambda: [0, 0])
mag_neg = defaultdict(list)
comp = defaultdict(Counter)
for vol, b, t, r in filas:
    m = parear(vol, b, t)
    z = r.get("sensor_zenith_deg")
    sinfila_z[(b, zbin(z))][0 if m is None else 1] += 1
    if m is None:
        clase = "SIN_FILA"
    else:
        tipo = m[1]
        k = (vol, t.strftime("%Y-%m-%d"))
        if tipo == "ALERTA_TERMICA":
            clase = "POS_pasada_ALERTA"
        elif tipo == "FALSO_POSITIVO":
            clase = "FP_pasada"
        elif k in alerta_noche:
            clase = "RUTINA_noche_con_alerta"
        elif k in fp_noche:
            clase = "RUTINA_noche_con_FP"
        else:
            clase = "NEG_LIMPIO"
    p = publica(r, INNER[vol])
    res[(b, clase)][0] += p
    res[(b, clase)][1] += 1
    if clase in ("NEG_LIMPIO", "POS_pasada_ALERTA"):
        porz[(b, clase, zbin(z))][0] += p
        porz[(b, clase, zbin(z))][1] += 1
    if clase == "NEG_LIMPIO":
        porvol[(b, vol)][0] += p
        porvol[(b, vol)][1] += 1
    if p and clase in ("NEG_LIMPIO", "POS_pasada_ALERTA"):
        pc = r.get("primary_cluster") or {}
        comp[(b, clase)]["n"] += 1
        comp[(b, clase)]["pc_1px"] += (pc.get("n_pixels") or 0) == 1
        comp[(b, clase)]["first_pass>0"] += (r.get("diag_n_first_pass_pixels") or 0) > 0
        comp[(b, clase)]["recaptura>0"] += (r.get("diag_n_second_pass_recapture") or 0) > 0
        comp[(b, clase)]["triggered_test1"] += bool(r.get("triggered_test1"))
        comp[(b, clase)]["nti_max>-0.8"] += (r.get("nti_max") if r.get("nti_max") is not None else -9) > -0.8
        comp[(b, clase)]["pc_dist>inner/2"] += (pc.get("centroid_dist_km") or 0) > INNER[vol] / 2
        if clase == "NEG_LIMPIO":
            mag_neg[b].append(eq(r, INNER[vol]))

print("\n== tasa de publicacion POR PASADA (publica/total), ventana", T0, "a", T1[:10])
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    print(b, {c: f"{res[(b, c)][0]}/{res[(b, c)][1]} = {res[(b, c)][0] / res[(b, c)][1]:.3f}" if res[(b, c)][1] else "0/0"
              for c in ("POS_pasada_ALERTA", "NEG_LIMPIO", "RUTINA_noche_con_alerta", "RUTINA_noche_con_FP", "FP_pasada", "SIN_FILA")})

print("\n== NEG_LIMPIO por volcan (publica/total)")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    print(b, {v: f"{porvol[(b, v)][0]}/{porvol[(b, v)][1]}" for v in INNER if porvol[(b, v)][1]})

print("\n== por angulo cenital del sensor: publica/total")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    for c in ("POS_pasada_ALERTA", "NEG_LIMPIO"):
        print(b, c, {zb: f"{porz[(b, c, zb)][0]}/{porz[(b, c, zb)][1]}" for zb in ("z<30", "z30-50", "z50-60", "z>=60", "z?") if porz[(b, c, zb)][1]})
    print(b, "fraccion de pasadas nuestras CON fila CONS por cenital:",
          {zb: f"{sinfila_z[(b, zb)][1]}/{sum(sinfila_z[(b, zb)])}" for zb in ("z<30", "z30-50", "z50-60", "z>=60", "z?") if sum(sinfila_z[(b, zb)])})

print("\n== magnitud publicada en NEG_LIMPIO vs VRP de las ALERTAS nocturnas de MIROVA (CONS)")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    xs, ms = sorted(mag_neg[b]), sorted(mir_alerta_vrp[b])
    if not xs or not ms:
        print(b, "SIN DATO", len(xs), len(ms))
        continue
    q = lambda L, p: L[min(len(L) - 1, int(p * len(L)))]
    print(b, f"nuestra n={len(xs)} mediana {st.median(xs):.3f} p90 {q(xs, .9):.3f} | frac <0.05 {sum(x < 0.05 for x in xs) / len(xs):.3f} <0.1 {sum(x < 0.1 for x in xs) / len(xs):.3f}",
          f"|| MIROVA ALERTA n={len(ms)} min {ms[0]:.2f} p5 {q(ms, .05):.2f} p10 {q(ms, .10):.2f} mediana {st.median(ms):.2f}",
          f"|| nuestra NEG bajo el p5 de MIROVA: {sum(x < q(ms, .05) for x in xs)}/{len(xs)}")

print("\n== composicion de las publicaciones (NEG_LIMPIO vs POS)")
for k, c in sorted(comp.items()):
    n = c["n"]
    print(k, {kk: f"{vv}/{n} ({vv / n:.2f})" for kk, vv in c.items() if kk != "n"})
