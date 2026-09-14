"""S139 VERIFICADOR v3: (a) cuanto de la publicacion V375/V750 en negativos es el objeto D19
(keep_peak: cumulo de 1 pixel del Test 1 publicado por el ancla como `test1_roi`); (b) proxy offline
de "sin ese objeto" por pasada y por noche; (c) cuanto del pareo 71-77 % del eje 3 depende de la
tolerancia de 20 min.

Instrumento.
 P1: si el objeto D19 no tuviera nada que ver con la sobre-publicacion, su fraccion seria igual en
     negativos y en positivos; se imprimen lado a lado.
 P2: el marcador se lee de campos persistidos (`final_hotspot_source`, `primary_cluster.single_pixel_mode`);
     se imprime cuantos records NO tienen esos campos (SIN DATO), para no confundir ausencia con falso.
 ADVERTENCIA A18: (b) es un filtro sobre records ya seleccionados, NO predice lo que haria un reproceso
     con keep_peak OFF (el cumulo podria cambiar). La evidencia real es el brazo B de S135 (reproceso).
Control del pareo: +3 h da 0 (ya medido en v1). Ventana 2026-01-10 a 2026-09-07, noche, 11 Tier A.
Predicado del dashboard: port de v1, validado 7377/7377 noches-sensor contra el node del eje 2.
"""
import csv, json, sys, io, bisect, pathlib
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
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")


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


def objeto_d19(r):
    pc = r.get("primary_cluster") or {}
    return r.get("final_hotspot_source") == "test1_roi" and pc.get("single_pixel_mode") is True


cons = defaultdict(list)
alerta_noche, fp_noche = set(), set()
for fname, es_ocr in (("latest_consolidado.csv", False),
                      ("data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv", True)):
    for row in csv.DictReader(open(R / fname, encoding="utf-8", errors="replace")):
        vol = normalize_volcano_name(row.get("Volcan"))
        f = (row.get("Fecha_Satelite_UTC") or "")[:19]
        if vol is None or not (T0 <= f <= T1):
            continue
        t = datetime.strptime(f, "%Y-%m-%d %H:%M:%S")
        tipo = row.get("Tipo_Registro") or ""
        noct = t.hour <= 11
        if es_ocr:
            if tipo == "ALERTA_TERMICA_OCR" and noct:
                alerta_noche.add((vol, f[:10]))
            continue
        cons[(vol, normalize_sensor(row.get("Sensor")))].append((t, tipo))
        if noct and tipo == "ALERTA_TERMICA":
            alerta_noche.add((vol, f[:10]))
        if noct and tipo == "FALSO_POSITIVO":
            fp_noche.add((vol, f[:10]))
for k in cons:
    cons[k].sort()


def cercano(vol, b, t, tol):
    L = cons.get((vol, b), [])
    ts = [x[0] for x in L]
    i = bisect.bisect_left(ts, t - timedelta(seconds=tol))
    best = None
    while i < len(L) and L[i][0] <= t + timedelta(seconds=tol):
        if best is None or abs((L[i][0] - t).total_seconds()) < abs((best[0] - t).total_seconds()):
            best = L[i]
        i += 1
    return best


sin_campo = Counter()
tabla = defaultdict(lambda: [0, 0, 0])   # (b, clase) -> [n, publica, publica_sin_d19]
d19_en_pub = defaultdict(lambda: [0, 0])  # (b, clase) -> [pub d19, pub]
desfase = defaultdict(Counter)
noche_pub = defaultdict(lambda: [False, False])  # (vol,b,fecha) -> [pub, pub_sin_d19]
for vol in INNER:
    for r in json.load(open(R / f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))["records"]:
        d = r["datetime_utc"]
        if not (T0 <= d <= T1):
            continue
        t = datetime.strptime(d, "%Y-%m-%d %H:%M")
        sz = r.get("solar_zenith_deg")
        if (sz is not None and sz < 90) or (sz is None and t.hour > 11):
            continue
        b = bucket(r["sensor"])
        if "final_hotspot_source" not in r:
            sin_campo[b] += 1
        m20 = cercano(vol, b, t, 1200)
        if m20 is None:
            desfase[b][">20min"] += 1
        else:
            s = abs((m20[0] - t).total_seconds())
            desfase[b]["<=2min" if s <= 120 else ("2-10min" if s <= 600 else "10-20min")] += 1
        m = cercano(vol, b, t, 120)
        k = (vol, d[:10])
        if m is None:
            clase = "SIN_FILA"
        elif m[1] == "ALERTA_TERMICA":
            clase = "POS"
        elif m[1] == "FALSO_POSITIVO":
            clase = "FP"
        elif k in alerta_noche:
            clase = "RUT_noche_alerta"
        elif k in fp_noche:
            clase = "RUT_noche_FP"
        else:
            clase = "NEG_LIMPIO"
        p = publica(r, INNER[vol])
        p2 = p and not objeto_d19(r)
        tabla[(b, clase)][0] += 1
        tabla[(b, clase)][1] += p
        tabla[(b, clase)][2] += p2
        if p:
            d19_en_pub[(b, clase)][0] += objeto_d19(r)
            d19_en_pub[(b, clase)][1] += 1
        nk = (vol, b, d[:10])
        noche_pub[nk][0] |= p
        noche_pub[nk][1] |= p2

print("records sin campo final_hotspot_source (SIN DATO del marcador):", dict(sin_campo))
print("\n== (c) desfase a la fila CONS mas cercana del mismo volcan y sensor")
for b, c in desfase.items():
    n = sum(c.values())
    print(b, {k: f"{v} ({v / n:.3f})" for k, v in c.items()}, "| pareo <=20 min:", f"{(n - c['>20min']) / n:.3f}")

print("\n== (a) objeto D19 dentro de lo publicado, y (b) proxy por pasada sin el objeto")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    for clase in ("POS", "NEG_LIMPIO", "RUT_noche_alerta", "SIN_FILA"):
        n, p, p2 = tabla[(b, clase)]
        dd, pp = d19_en_pub[(b, clase)]
        if n:
            print(f"{b:9s} {clase:17s} n={n:5d} publica {p / n:.3f} | D19 en lo publicado {dd}/{pp} | proxy sin D19 {p2 / n:.3f}")

print("\n== (b) proxy por NOCHE-sensor con las etiquetas del eje 2 (cons_ocr|pipeline|rutina_estricta)")
tab = json.load(open(R / "experiments/_s139_audit/eje2/banco_tabla.json", encoding="utf-8"))
print("valores de etiqueta del eje 2:", Counter(x["etq_rutina_estricta"] for x in tab).most_common())
agg = defaultdict(lambda: [0, 0, 0])
perdidas = Counter()
for x in tab:
    k = (x["vol"], x["b"], x["noche"])
    if k not in noche_pub or not x.get("nos"):
        continue
    e = x["etq_rutina_estricta"]
    p, p2 = noche_pub[k]
    agg[(x["b"], e)][0] += 1
    agg[(x["b"], e)][1] += p
    agg[(x["b"], e)][2] += p2
    if p and not p2 and e not in ("neg", "negativo", "sin_fila"):
        perdidas[(x["b"], e, x["vol"])] += 1
for (b, e), (n, p, p2) in sorted(agg.items()):
    print(f"{b:9s} {e:14s} n={n:5d} publica {p}/{n} ({p / n:.3f}) -> proxy sin D19 {p2}/{n} ({p2 / n:.3f})")
print("noches no negativas que el proxy dejaria sin publicar, por volcan:", dict(perdidas))
