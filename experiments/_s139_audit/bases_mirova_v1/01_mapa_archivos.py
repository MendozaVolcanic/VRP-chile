"""01: que es cada CSV de Mirova-v1 y cual deriva de cual.

Verifica contra los DATOS (no contra el codigo) las derivaciones que el codigo
declara: positivos = consolidado[ALERTA_TERMICA] (scraper.py:206),
maestro_publicable = (consolidado + ocr) dedup, solo ALERTA*, VRP>0,
confianza != invalido (merger_maestro.py:94-146), registro_<Volcan>.csv =
maestro_publicable[Volcan] (merger_maestro.py:41-48).
"""
import os
import sys

import pandas as pd

from comun import ARCHIVOS, LLAVE, POR_VOLCAN, dir_remoto, encabezado, leer

D = dir_remoto(sys.argv)
print("carpeta de datos:", D)
if os.path.exists(os.path.join(D, "remoto_meta.txt")):
    print("remoto:", open(os.path.join(D, "remoto_meta.txt")).read().strip())

encabezado(
    "MAPA DE ARCHIVOS",
    "si un archivo no fuera la derivacion declarada, las llaves no coincidirian y se listan las diferencias",
    "un archivo vacio o ilegible da filas=0 y se imprime como tal, no como 'coincide'",
    "se quita una fila a la copia de positivos y se comprueba que la comparacion la detecta",
)

dfs = {}
for f in ARCHIVOS + POR_VOLCAN:
    p = os.path.join(D, f)
    if not os.path.exists(p):
        print(f"{f:45s} NO EXISTE en {D}")
        continue
    df = leer(p)
    dfs[f] = df
    print(f"\n--- {f}: {len(df)} filas, {len(df.columns)} columnas")
    print("    columnas:", list(df.columns[: [i for i, c in enumerate(df.columns)][-1] + 1 - 4]) if False else list(c for c in df.columns if c not in ("dt", "mes", "noche", "noche_id")))
    if "dt" in df:
        print("    rango Fecha_Satelite_UTC:", df["dt"].min(), "->", df["dt"].max())
    if "Tipo_Registro" in df:
        print("    Tipo_Registro:", df["Tipo_Registro"].value_counts().to_dict())
    if "Sensor" in df:
        print("    Sensor:", df["Sensor"].value_counts().to_dict())
    if "Volcan" in df:
        print("    Volcan:", df["Volcan"].value_counts().to_dict())
    dup = df.duplicated(subset=[c for c in LLAVE if c in df.columns]).sum()
    print("    duplicados por (timestamp, Volcan, Sensor):", int(dup))
    for c in ("Origen_Dato", "Confianza_Validacion", "Version_OCR", "Metodo_Validacion",
              "Color_Punto_Dist", "Requiere_Verificacion", "Editado", "Nivel_Anomalia_MIROVA",
              "Confianza_Geometria"):
        if c in df:
            print(f"    {c}:", df[c].value_counts().head(12).to_dict())


def llaves(df):
    return set(zip(df["timestamp"].astype("int64"), df["Volcan"], df["Sensor"]))


cons = dfs["registro_vrp_consolidado.csv"]
pos = dfs["registro_vrp_positivos.csv"]
ocr = dfs["registro_vrp_ocr.csv"]
mae = dfs["registro_vrp_maestro_publicable.csv"]

print("\n=== DERIVACION 1: positivos == consolidado[Tipo_Registro == ALERTA_TERMICA] ?")
a = llaves(cons[cons["Tipo_Registro"] == "ALERTA_TERMICA"])
b = llaves(pos)
print(f"  consolidado ALERTA: {len(a)} | positivos: {len(b)} | solo en cons: {len(a-b)} | solo en positivos: {len(b-a)}")
print("  tipos en positivos:", pos["Tipo_Registro"].value_counts().to_dict())
# control positivo
b_ctrl = set(list(b)[1:])
print(f"  CONTROL: quitando 1 fila a positivos, solo-en-cons pasa a {len(a - b_ctrl)} (esperado 1 mas)")

print("\n=== DERIVACION 2: maestro_publicable == dedup(cons + ocr) filtrado ?")
c2 = cons.copy(); c2["Origen_Dato"] = "latest.php"; c2["Confianza_Validacion"] = "alta"
o2 = ocr.copy(); o2["Origen_Dato"] = "OCR"
m = pd.concat([c2, o2], ignore_index=True)
dupm = m.duplicated(subset=LLAVE, keep="first")
m = m[~dupm]
m = m[m["Tipo_Registro"].isin(["ALERTA_TERMICA", "ALERTA_TERMICA_OCR"])]
m = m[m["VRP_MW"] > 0]
m = m[m["Confianza_Validacion"] != "invalido"]
a = llaves(m); b = llaves(mae)
print(f"  reconstruido: {len(a)} | maestro publicado: {len(b)} | solo reconstruido: {len(a-b)} | solo publicado: {len(b-a)}")
if a - b:
    print("   ejemplos solo reconstruido:", sorted(a - b)[:5])
if b - a:
    print("   ejemplos solo publicado:", sorted(b - a)[:5])
print("  Origen_Dato en maestro:", mae["Origen_Dato"].value_counts().to_dict())
print("  Tipo en maestro:", mae["Tipo_Registro"].value_counts().to_dict())
# Origen 'ambos': ocr y cons con misma llave; que gana? (cons va primero en el concat)
amb = mae[mae["Origen_Dato"] == "ambos"]
print(f"  filas 'ambos': {len(amb)}; de ellas Tipo ALERTA_TERMICA (gano cons): "
      f"{(amb['Tipo_Registro']=='ALERTA_TERMICA').sum()}")

print("\n=== DERIVACION 3: registro_<Volcan>.csv == maestro[Volcan] ?")
mapa = {"registro_Chaiten.csv": "Chaiten", "registro_Copahue.csv": "Copahue",
        "registro_Isluga.csv": "Isluga", "registro_Lascar.csv": "Lascar",
        "registro_Lastarria.csv": "Lastarria", "registro_Llaima.csv": "Llaima",
        "registro_Nevados_de_Chillan.csv": "Nevados de Chillan",
        "registro_PlanchonPeteroa.csv": "PlanchonPeteroa",
        "registro_Puyehue_Cordon_Caulle.csv": "Puyehue-Cordon Caulle",
        "registro_Tupungatito.csv": "Tupungatito", "registro_Villarrica.csv": "Villarrica"}
tot_v = 0
for f, v in mapa.items():
    if f not in dfs:
        continue
    a = llaves(mae[mae["Volcan"] == v]); b = llaves(dfs[f]); tot_v += len(b)
    flag = "OK" if a == b else f"DIFIEREN solo_maestro={len(a-b)} solo_archivo={len(b-a)}"
    print(f"  {f:40s} maestro={len(a):4d} archivo={len(b):4d} {flag}")
print(f"  suma por volcan: {tot_v} vs maestro: {len(mae)}")

print("\n=== OCR: que aporta el OCR que el consolidado no tiene (por tipo) ===")
kc = llaves(cons)
for t, g in ocr.groupby("Tipo_Registro"):
    k = llaves(g)
    en_cons = len(k & kc)
    print(f"  {t:22s} {len(g):4d} filas; con misma llave en consolidado: {en_cons}; solo OCR: {len(k-kc)}")
kca = llaves(cons[cons["Tipo_Registro"] == "ALERTA_TERMICA"])
oa = ocr[ocr["Tipo_Registro"] == "ALERTA_TERMICA_OCR"]
print(f"  ALERTA_TERMICA_OCR con misma llave que una ALERTA del consolidado: {len(llaves(oa) & kca)}")
# dedup a +-60 s (la regla del scraper, ocr_utils DUPLICADO_LATEST) en vez de llave exacta
cs = cons[cons["Tipo_Registro"] == "ALERTA_TERMICA"][["timestamp", "Volcan", "Sensor"]].copy()
n_cerca = 0
for _, r in oa.iterrows():
    m2 = cs[(cs["Volcan"] == r["Volcan"]) & (cs["Sensor"] == r["Sensor"]) &
            ((cs["timestamp"] - r["timestamp"]).abs() <= 60)]
    if len(m2):
        n_cerca += 1
print(f"  ALERTA_TERMICA_OCR con una ALERTA del consolidado a +-60 s (mismo volcan y sensor): {n_cerca}")

print("\n=== Columnas V30 del OCR pobladas (Zenith/Azimut/Nivel banner) ===")
for c in ("Zenith_Sat_deg", "Azimut_Sat_deg", "Nivel_Anomalia_MIROVA", "Confianza_Geometria"):
    if c in ocr:
        print(f"  {c:24s} no vacias: {(ocr[c] != '').sum()} / {len(ocr)}")
if "Nivel_Anomalia_MIROVA" in ocr:
    print("  Nivel_Anomalia_MIROVA por Tipo:", ocr.groupby("Tipo_Registro")["Nivel_Anomalia_MIROVA"]
          .apply(lambda s: s[s != ""].value_counts().to_dict()).to_dict())
