# Pregunta 1: si lo que mido estuviera roto, ¿se vería? Cuenta dias (UTC) sin ningun record por sensor en
# data/mirova_equivalent (NO data/sombra_codigo_mirova), ventana 2026-03-01..2026-10-14, para estimar con que frecuencia
# un dia no tiene pasada nocturna por sensor. Pregunta 2: control positivo = Lascar VIIRS375 (debe tener casi todos los dias).
# Denominador: dias de la ventana (228). Ventana de los datos declarada en la salida.
import json, sys, datetime as dt
sys.path.insert(0, "D:/vrp-trabajo/temporales/s169_ver_vigilancia_r3/arbol")
from scripts.revisar_sombra import familia
R = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_equivalent/"
A, B = dt.date(2026,3,1), dt.date(2026,10,14)
N = (B-A).days+1
for v in ["Isluga","Lascar","Lastarria","Tupungatito","PlanchonPeteroa","Chaiten","Villarrica","Llaima","Copahue","NevadosDeChillan","PuyehueCordonCaulle"]:
    d = json.load(open(R+v+".json", encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) else d
    dias = {s:set() for s in ("MODIS","VIIRS750","VIIRS375")}
    for r in recs:
        x = str(r.get("datetime_utc") or "")[:10]
        try: x = dt.date.fromisoformat(x)
        except Exception: continue
        if A <= x <= B:
            f = familia(r.get("sensor"))
            if f in dias: dias[f].add(x)
    print(v, {s: f"{N-len(dias[s])} dias sin record de {N}" for s in dias})
