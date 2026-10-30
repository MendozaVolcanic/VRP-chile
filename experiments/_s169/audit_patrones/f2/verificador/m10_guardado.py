"""P2-10. Mide cuántas pasadas de la población NO tienen record guardado en data/mirova_equivalent del commit 743e89c48
con la llave que usa probe_f4.registro_guardado: (datetime_utc, sensor). Pregunta 1: si la llave nunca coincidiera
(formatos distintos), ¿se vería? Sí: n_con_record sería 0. Pregunta 2: si no leyera data/, n_con_record = 0 y se nota
porque el control positivo (formato de datetime_utc impreso) lo delata. Denominador: 5.709 pasadas de poblacion_f4.json.
Sensor: se deriva del nombre del L1B como pm._sensor_modis (MOD -> MODIS_TERRA, MYD -> MODIS_AQUA): SOSPECHA de
equivalencia, se imprime el conjunto de sensores de data/ para contrastar."""
import json, subprocess, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
C = "D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis/arbol/experiments/_s166_modd_f4/"
pob = json.load(open(C + "poblacion_f4.json", encoding="utf-8"))
pas = pob["pasadas"]
print("claves de una pasada:", sorted(pas[0].keys()))
print("ejemplo:", {k: pas[0][k] for k in ("vol", "dt", "l1b") if k in pas[0]})
def sensor_de(l1b):
    s = str(l1b)
    return "MODIS_TERRA" if s.startswith("MOD") else "MODIS_AQUA" if s.startswith("MYD") else "?"
porvol = collections.defaultdict(list)
for p in pas: porvol[p["vol"]].append(p)
tot = sin = 0; sin_por_tramo = collections.Counter(); sin_lab = collections.Counter(); ej = []
for vol, lst in sorted(porvol.items()):
    r = subprocess.run(["git", "-C", REPO, "show", f"743e89c48:data/mirova_equivalent/{vol}.json"], capture_output=True)
    recs = json.loads(r.stdout)["records"] if r.returncode == 0 else []
    keys = {(x.get("datetime_utc"), x.get("sensor")) for x in recs}
    sens = collections.Counter(x.get("sensor") for x in recs if str(x.get("sensor", "")).startswith("MODIS"))
    fmt = next((x.get("datetime_utc") for x in recs if str(x.get("sensor", "")).startswith("MODIS")), None)
    n_sin = 0
    for p in lst:
        tot += 1
        if (p["dt"], sensor_de(p.get("l1b"))) not in keys:
            sin += 1; n_sin += 1; sin_por_tramo[p.get("tramo")] += 1; sin_lab[p.get("lab")] += 1
            if len(ej) < 8: ej.append((vol, p["dt"], p.get("tramo"), p.get("lab")))
    print(f"{vol:22s} pasadas {len(lst):5d} sin record {n_sin:5d} | sensores data {dict(sens)} | fmt {fmt!r}")
print("TOTAL", tot, "sin record guardado", sin, "por tramo", dict(sin_por_tramo), "por lab", dict(sin_lab))
print("ejemplos", ej)
