# -*- coding: utf-8 -*-
"""S150 verificador. Conteo B/J/K de MODIS en Lascar, marzo a junio, reimplementado SIN armar_tabla.py
ni modis_lascar_brazos.py. Lo unico reutilizado es el predicado de publicacion del tablero (node, A97:
no se porta a Python) y el inner_radius del HTML.

Etiquetas, escritas aca desde la definicion del banco de paridad:
  pos         alguna fila ALERTA* (tabla u OCR) de Lascar MODIS a +-120 s de la pasada
  neg_limpio  fila RUTINA de la TABLA con VRP 0 a +-120 s, y ninguna fila ALERTA* ni FALSO_POSITIVO*
              de Lascar MODIS en esa fecha UTC (filas nocturnas, elevacion solar <= 0)
Lee los CSV congelados de cada ventana y, aparte, informa si el respaldo del 2026-04-08 cambia algo.

Uso: python modis_lascar_independiente.py <DIR_LASCAR> [--produccion]
  <DIR_LASCAR>/<run>/<perfil>/Lascar.json, extraidos con git show de origin/s146-ab/<run>.
"""
import csv, json, math, sys, io, collections, bisect
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp  # solo correr_node, CAMPOS_JS e inner_desde_html

L = Path(sys.argv[1]); CONG = RAIZ / "experiments" / "_s149_prereg_invierno" / "_congelado"
LAT, LON = -23.37, -67.73   # se sobrescribe con volcanoes.yaml abajo
import yaml
for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]:
    if v["name"] == "Lascar": LAT, LON = v["lat"], v["lon"]

def elev_solar(lat, lon, t):
    # NOAA, aproximacion de Spencer; error < 0,5 grados, de sobra para separar dia de noche.
    d = t.timetuple().tm_yday; h = t.hour + t.minute / 60
    g = 2 * math.pi / 365 * (d - 1 + (h - 12) / 24)
    decl = 0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    tst = h * 60 + eqt + 4 * lon; ha = math.radians(tst / 4 - 180); la = math.radians(lat)
    return math.degrees(math.asin(math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)))

def filas_ref(cons, ocr, respaldo=None):
    out = []
    for path, src in ((cons, "CONS"), (ocr, "OCR")) + (((respaldo, "CONS"),) if respaldo else ()):
        for r in csv.DictReader(open(path, encoding="utf-8")):
            if (r.get("Volcan") or "").strip() != "Lascar" or not (r.get("Sensor") or "").strip().upper().startswith("MODIS"): continue
            t = datetime.strptime(r["Fecha_Satelite_UTC"].strip()[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            if elev_solar(LAT, LON, t) > 0: continue
            try: vrp = float(r.get("VRP_MW") or 0)
            except ValueError: vrp = 0.0
            out.append((t, src, (r.get("Tipo_Registro") or "").strip(), vrp))
    out.sort(); return out

def etiqueta(t, ref):
    ts = [x[0] for x in ref]; i = bisect.bisect_left(ts, t - timedelta(seconds=120)); cerca = []
    while i < len(ref) and ref[i][0] <= t + timedelta(seconds=120): cerca.append(ref[i]); i += 1
    noche = [x for x in ref if x[0].date() == t.date()]
    alerta = [x for x in cerca if x[2].startswith("ALERTA")]
    if alerta: return "pos", max(x[3] for x in alerta)
    if any(x[2].startswith("FALSO_POSITIVO") for x in cerca): return "far_ref", None
    if any(x[1] == "CONS" and x[2] == "RUTINA" and x[3] == 0 for x in cerca) and not any(x[2].startswith(("ALERTA", "FALSO_POSITIVO")) for x in noche):
        return "neg_limpio", None
    return "sin_info", None

INNER = bp.inner_desde_html()["Lascar"]
def cargar(path, desde, hasta):
    d = json.load(open(path, encoding="utf-8")); recs, casos = [], []
    for r in d["records"]:
        if not (r.get("sensor") or "").startswith("MODIS"): continue
        if not (desde <= r["datetime_utc"][:10] <= hasta): continue
        t = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        recs.append({"t": t, "sensor": r["sensor"]})
        slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        if r.get("f5_core_vrp_mw") is None:
            slim["anomaly_pixels"] = [{k: q.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for q in (r.get("anomaly_pixels") or [])]
        casos.append([slim, INNER])
    for rec, q in zip(recs, bp.correr_node(casos) if casos else []): rec["pub"] = int(bool(q[4]))
    claves = collections.Counter(r["t"] for r in recs)
    dup = sum(1 for c in claves.values() if c > 1)
    return {r["t"]: r for r in recs}, dup, len(recs)

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return 100 * (c - r) / d, 100 * (c + r) / d

MESES = {  # mes: (desde, hasta, congelado, (run, perfil) de B, run de J y K)
    "marzo": ("2026-03-01", "2026-03-31", "marzo_lascar", ("35632736532", "_s146_ab_sin_test1"), "35632736532"),
    "abril": ("2026-04-01", "2026-04-30", "abril", ("35639417826", "_s146_ab_sin_test1"), "35648804271"),
    "mayo":  ("2026-05-01", "2026-05-31", "mayo", ("35599902448", "_s146_ab_sin_test1"), "35671459235"),
    "junio": ("2026-06-01", "2026-06-30", "junio", ("35675490175", "_s146_ab_sin_test1"), "35679063864"),
}
PROD = "--produccion" in sys.argv
for con_respaldo in (False, True):
    print("\n######## referencia: CSV congelados%s" % (" + respaldo 2026-04-08" if con_respaldo else ""))
    tot = collections.defaultdict(lambda: [0, 0, 0, 0]); noches = collections.defaultdict(set); perdidas_k = []; ganancias_k = []
    for m, (d, h, cong, (rb, pb), rjk) in MESES.items():
        ref = filas_ref(CONG / cong / "registro_vrp_consolidado.csv", CONG / cong / "registro_vrp_ocr.csv",
                        RAIZ / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv" if con_respaldo else None)
        brazos = {"B": L / rb / pb / "Lascar.json", "J": L / rjk / "_s149_ab_sin_test1_b22" / "Lascar.json", "K": L / rjk / "_s149_ab_sin_test1_b22_max" / "Lascar.json"}
        if PROD: brazos["PROD"] = RAIZ / "data/mirova_equivalent/Lascar.json"
        R = {}; info = []
        for n, p in brazos.items():
            R[n], dup, nrec = cargar(p, d, h); info.append("%s %d rec (%d dup)" % (n, nrec, dup))
        comunes = set.intersection(*(set(x) for x in R.values()))
        fila = {}
        for n in brazos:
            pos = negs = pp = npub = 0
            for t in sorted(comunes):
                lab, vrp = etiqueta(t, ref)
                if lab == "pos": pos += 1; pp += R[n][t]["pub"]; noches["pos"].add(t.date())
                if lab == "neg_limpio": negs += 1; npub += R[n][t]["pub"]; noches["neg"].add(t.date())
            a = tot[n]; a[0] += pos; a[1] += pp; a[2] += negs; a[3] += npub; fila[n] = "pos %d/%d neg %d/%d" % (pp, pos, npub, negs)
        for t in sorted(comunes):
            lab, vrp = etiqueta(t, ref)
            if lab == "pos" and R["J"][t]["pub"] and not R["K"][t]["pub"]: perdidas_k.append((str(t), R["J"][t]["sensor"], vrp))
            if lab == "pos" and R["K"][t]["pub"] and not R["J"][t]["pub"]: ganancias_k.append((str(t), vrp))
        solo = {n: len(set(R[n]) - comunes) for n in brazos}
        print(m, "| comunes %d | fuera de la interseccion %s | %s" % (len(comunes), solo, "; ".join(info)))
        print("   ", fila)
    print("AGREGADO:")
    for n, (pn, pp, nn, np_) in tot.items():
        lp, ln = wilson(pp, pn), wilson(np_, nn)
        print("  %-4s alerta %d/%d = %.1f %% [%.1f, %.1f] | neg limpio %d/%d = %.1f %% [%.1f, %.1f]" % (n, pp, pn, 100 * pp / pn, lp[0], lp[1], np_, nn, 100 * np_ / nn, ln[0], ln[1]))
    print("  noches distintas: positivas %d, negativos limpios %d" % (len(noches["pos"]), len(noches["neg"])))
    print("  K pierde respecto de J:", perdidas_k, "| K gana respecto de J:", ganancias_k)
