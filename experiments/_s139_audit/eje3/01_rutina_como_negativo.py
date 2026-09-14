"""S139 eje 3, medición 01: ¿una noche RUTINA del scraper Mirova-v1 es un negativo limpio?

Pregunta 1 del instrumento: si RUTINA NO fuera un negativo (p.ej. el scraper escribe RUTINA
aunque MIROVA haya publicado otra pasada esa misma noche), ¿esto lo vería? Sí: cuento las
noches volcán con RUTINA que ADEMÁS tienen ALERTA/FP en CONS u OCR (cualquier sensor) y las
noches-sensor con ambas etiquetas.
Pregunta 2: si el loader estuviera muerto (0 filas leídas o columna mal nombrada), el
resultado sería n=0 en todo y el script lo imprime como SIN DATO, no como "0 % contaminado".
Control positivo: las noches ALERTA de Láscar deben existir (>0) y el conteo de Tipo_Registro
debe incluir RUTINA y ALERTA_TERMICA.

Unidad: noche local de volcán = fecha de (UTC - 4 h) -> noche que empieza a las 20 h local
aproximadamente; se reporta también por fecha UTC para ver sensibilidad a la unidad.
Ventana: la del archivo (se imprime min/max). Denominadores impresos.
Sólo noche: se filtran filas con hora UTC entre 11 y 21 (día en Chile) igual que el criterio
night-only aproximado; se reporta con y sin filtro.
Solo lectura. No escribe nada en el repo.
"""
import sys, io
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"
CONS = ROOT + r"\latest_consolidado.csv"
OCR = ROOT + r"\data\mirova_reference\mirova_v1_snapshot\registro_vrp_ocr.csv"

cons = pd.read_csv(CONS)
ocr = pd.read_csv(OCR)
print("CONS filas", len(cons), "OCR filas", len(ocr))
if len(cons) == 0:
    print("SIN DATO"); sys.exit()
print("CONS Tipo_Registro:\n", cons["Tipo_Registro"].value_counts(dropna=False).to_string())
print("CONS Sensor:\n", cons["Sensor"].value_counts(dropna=False).to_string())
print("OCR Tipo_Registro:\n", ocr["Tipo_Registro"].value_counts(dropna=False).to_string())

def norm(v):
    v = str(v).replace("-", "").replace(" ", "").lower()
    return v

for df in (cons, ocr):
    df["t"] = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce")
    df["vol"] = df["Volcan"].map(norm)
    df["noche_local"] = (df["t"] - pd.Timedelta(hours=4) - pd.Timedelta(hours=12)).dt.date
    df["hora"] = df["t"].dt.hour
    df["es_noche"] = ~df["hora"].between(11, 21)

print("CONS ventana", cons["t"].min(), cons["t"].max())
print("OCR ventana", ocr["t"].min(), ocr["t"].max())

# Granularidad: filas RUTINA por (volcán, sensor, timestamp) duplicadas?
r = cons[cons["Tipo_Registro"] == "RUTINA"]
dup = r.duplicated(["vol", "Sensor", "t"]).sum()
print(f"RUTINA filas {len(r)}; duplicadas (vol,sensor,t) {dup}")
print("RUTINA VRP_MW>0:", int((r["VRP_MW"] > 0).sum()))

pos_tipos_cons = {"ALERTA_TERMICA"}
fp_tipos = {"FALSO_POSITIVO"}
pos = pd.concat([
    cons[cons["Tipo_Registro"].isin(pos_tipos_cons)][["vol", "Sensor", "t", "noche_local", "es_noche"]],
    ocr[ocr["Tipo_Registro"].astype(str).str.startswith("ALERTA")][["vol", "Sensor", "t", "noche_local", "es_noche"]],
])
fp = cons[cons["Tipo_Registro"].isin(fp_tipos)]

for filtro_noche in (False, True):
    rr = r[r["es_noche"]] if filtro_noche else r
    pp = pos[pos["es_noche"]] if filtro_noche else pos
    noches_r = set(zip(rr["vol"], rr["noche_local"]))
    noches_p = set(zip(pp["vol"], pp["noche_local"]))
    noches_fp = set(zip(fp["vol"], fp["noche_local"]))
    solo_r = noches_r - noches_p
    print(f"\n== filtro_noche={filtro_noche}")
    print(f"noches-volcán con RUTINA: {len(noches_r)}; con ALERTA (CONS u OCR): {len(noches_p)}")
    print(f"noches RUTINA que también tienen ALERTA: {len(noches_r & noches_p)} "
          f"({100*len(noches_r & noches_p)/max(len(noches_r),1):.1f} % de las noches RUTINA)")
    print(f"noches RUTINA sin ALERTA (candidatas a negativo): {len(solo_r)}; de ellas con FALSO_POSITIVO: {len(solo_r & noches_fp)}")
    # por sensor: noche-sensor con RUTINA y ALERTA del mismo sensor
    ns_r = set(zip(rr["vol"], rr["noche_local"], rr["Sensor"]))
    ns_p = set(zip(pp["vol"], pp["noche_local"], pp["Sensor"]))
    print(f"noches-sensor RUTINA: {len(ns_r)}; con ALERTA mismo sensor: {len(ns_r & ns_p)}")
    # control positivo Láscar
    lp = [n for n in noches_p if n[0] == "lascar"]
    print("control positivo: noches ALERTA Láscar =", len(lp))
    # por volcán: fracción de noches RUTINA que tienen ALERTA
    tab = {}
    for v, n in noches_r:
        tab.setdefault(v, [0, 0])
        tab[v][0] += 1
        if (v, n) in noches_p:
            tab[v][1] += 1
    print("volcán: noches_RUTINA / con_ALERTA")
    for v in sorted(tab):
        print(f"  {v}: {tab[v][0]} / {tab[v][1]}")
