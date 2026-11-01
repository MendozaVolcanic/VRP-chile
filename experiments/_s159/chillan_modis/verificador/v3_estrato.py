"""Verificador v3: estrato independiente, leyendo los CSV REMOTOS de Mirova-v1 bajados hoy (no el loader
unificado ni la copia local) y el JSON publicado. Protegida = Tipo_Registro de alerta (ALERTA_TERMICA*) con
VRP >= 1 MW (lectura A). Pasada = (fecha_satelite al minuto). Publicado se aproxima por
primary_cluster.vrp_mw > 0 y distance_class == 'summit' (proxy; el predicado real es node).
Pregunta 1: si no publicaramos nada, lo veria? Si, cuenta pc>0. Pregunta 2: sin record sale 'SIN RECORD'.
Ventana: 2026-09-01 a 2026-10-21 UTC (fecha de satelite)."""
import csv, json, sys
from datetime import datetime, timedelta
tmp, js = sys.argv[1], sys.argv[2]
pas = {}
for fn, src in (("registro_vrp_consolidado.csv","CONS"),("registro_vrp_ocr.csv","OCR")):
    for r in csv.DictReader(open(f"{tmp}/{fn}", encoding="utf-8")):
        v = r["Volcan"].replace(" ","").replace("-","").lower()
        if "chillan" not in v: continue
        if r["Sensor"].strip().upper() != "MODIS": continue
        f = r["Fecha_Satelite_UTC"][:16]
        if not ("2026-09-01" <= f[:10] <= "2026-10-21"): continue
        tipo = r["Tipo_Registro"]
        try: vrp = float(r["VRP_MW"])
        except: vrp = None
        pas.setdefault(f, []).append((src, tipo, vrp))
tipos = {t for f in pas.values() for (_,t,_) in f}
print("tipos vistos:", sorted(tipos))
alerta = lambda t: t.startswith("ALERTA_TERMICA")
prot = {f: x for f, x in pas.items() if any(alerta(t) and v is not None and v >= 1.0 for _,t,v in x)}
noprot_alert = {f: x for f, x in pas.items() if f not in prot and any(alerta(t) for _,t,_ in x)}
print(f"pasadas Chillan MODIS en ventana: {len(pas)}; con alerta: {len(prot)+len(noprot_alert)}; protegidas: {len(prot)}")
recs = [r for r in json.load(open(js, encoding="utf-8"))["records"] if (r.get("sensor") or "").startswith("MODIS")]
for r in recs: r["_dt"] = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
cuenta = {}
for f in sorted(prot):
    t = datetime.strptime(f, "%Y-%m-%d %H:%M")
    c = [r for r in recs if abs(r["_dt"] - t) <= timedelta(minutes=5)]
    hora_local = (t - timedelta(hours=3)).hour
    if not c: est = "SIN RECORD"
    else:
        r = c[0]; pc = r.get("primary_cluster") or {}
        est = "PC>0 summit" if (pc.get("vrp_mw") or 0) > 0 and r.get("distance_class") == "summit" else "NO (pc nulo o 0)"
    cuenta[est] = cuenta.get(est, 0) + 1
    print(f, f"local~{hora_local:02d}h", est, "n_cand", len(c), [ (s,t_,v) for s,t_,v in prot[f]],
          (c[0].get("sensor_zenith_deg") if c else None))
print("RESUMEN", cuenta)
print("alertas no protegidas:", {f: x for f, x in noprot_alert.items()})
