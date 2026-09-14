"""06: tres mediciones que salieron de 04 y de la bitacora.

(A) Filas que copias VIEJAS del consolidado tienen y el remoto de hoy NO
    (04 dio 241 en el checkout del 28-mar, 308 en el backup del 08-abr, 234 en
    la copia del 01-may). Si son ALERTAS, el ground truth perdio filas.
(B) Las dos ventanas en que scraper.py abortaba el ciclo entero por
    float('2,178.53') / float('1,357.39') (bitacora 2026-06-15 17:05-18:45 y
    2026-07-08 17:05-18:15 hora Chile): que pasadas de esas horas existen solo
    en el OCR o en ningun lado.
(C) De las 327 ALERTA_TERMICA_OCR que comparten llave exacta con una ALERTA del
    consolidado: quien escribio primero (el OCR o latest.php).
(D) Que son las filas OCR con Editado = SI.
"""
import os
import sys

import pandas as pd

from comun import LLAVE, LOCAL_MIROVA, REPO, dir_remoto, encabezado, leer

D = dir_remoto(sys.argv)
cons = leer(f"{D}/registro_vrp_consolidado.csv")
ocr = leer(f"{D}/registro_vrp_ocr.csv")
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 300); pd.set_option("display.max_colwidth", 120)

encabezado(
    "PERDIDAS DE FILAS, VENTANAS DE ERROR Y CARRERAS ENTRE CANALES",
    "si el remoto no hubiera perdido nada, 'solo en copia vieja' seria 0 salvo renombres; si el error float no hubiera costado filas, la ventana tendria pasadas en el consolidado",
    "cada bloque imprime n y ventana; 'solo copia vieja' se desglosa por tipo para que un 0 en ALERTA no se confunda con 'no medi'",
    "renombrar 'Peteroa' a 'PlanchonPeteroa' en la copia vieja debe bajar las diferencias exactamente en las filas Peteroa",
)


def llaves(df):
    return set(zip(df["timestamp"].astype("int64"), df["Volcan"], df["Sensor"]))


kr = llaves(cons)
print("\n(A) llaves de copias viejas ausentes en el remoto de hoy (por Tipo y por mes)")
copias = [("checkout local 2026-03-28", os.path.join(LOCAL_MIROVA, "registro_vrp_consolidado.csv")),
          ("backup 'al 08042026'", os.path.join(LOCAL_MIROVA, "registro_vrp_consolidado al 08042026.csv")),
          ("01_05_2026 (VRP Chile)", os.path.join(REPO, "01_05_2026_registro_vrp_consolidado.csv")),
          ("snapshot 2026-09-07 (VRP Chile)", os.path.join(REPO, "data", "mirova_reference", "mirova_v1_snapshot", "registro_vrp_consolidado.csv"))]
for nombre, p in copias:
    if not os.path.exists(p):
        print(f"  {nombre}: NO EXISTE"); continue
    v = leer(p)
    v2 = v.copy(); v2.loc[v2["Volcan"] == "Peteroa", "Volcan"] = "PlanchonPeteroa"
    solo = v2[[k not in kr for k in zip(v2["timestamp"].astype("int64"), v2["Volcan"], v2["Sensor"])]]
    n_pet = int((v["Volcan"] == "Peteroa").sum())
    print(f"  {nombre}: filas {len(v)}, rango {v['dt'].min()} -> {v['dt'].max()}; Peteroa renombradas {n_pet}; "
          f"ausentes en remoto tras renombrar: {len(solo)}")
    if len(solo):
        print("     por Tipo:", solo["Tipo_Registro"].value_counts().to_dict())
        print("     por mes:", solo["mes"].value_counts().sort_index().to_dict())
        print("     por sensor:", solo["Sensor"].value_counts().to_dict())
        print("     por volcan:", solo["Volcan"].value_counts().to_dict())
        # las mismas llaves con otro timestamp (+-60 s) en el remoto? (deduplicacion o cambio de segundo)
        cerca = 0
        for _, r in solo.iterrows():
            m = cons[(cons["Volcan"] == r["Volcan"]) & (cons["Sensor"] == r["Sensor"]) &
                     ((cons["timestamp"] - r["timestamp"]).abs() <= 120)]
            if len(m):
                cerca += 1
        print(f"     de ellas, con una fila del remoto a +-120 s (mismo volcan y sensor): {cerca}")
        al = solo[solo["Tipo_Registro"] == "ALERTA_TERMICA"]
        if len(al):
            print("     ALERTAS perdidas (primeras 15):")
            print(al[["Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "Distancia_km"]].head(15).to_string(index=False))
    # control: sin renombrar, las Peteroa deben sumarse a las ausentes
    solo_sin = v[[k not in kr for k in zip(v["timestamp"].astype("int64"), v["Volcan"], v["Sensor"])]]
    print(f"     CONTROL sin renombrar Peteroa: ausentes = {len(solo_sin)} (esperado {len(solo)} + {n_pet} = {len(solo) + n_pet})")

print("\n(B) ventanas del error float en scraper.py:140 (hora Chile -> UTC = +4 h en jun/jul)")
ventanas = [("2026-06-15 21:05", "2026-06-15 22:46", "2,178.53"), ("2026-07-08 21:05", "2026-07-08 22:16", "1,357.39")]
for a, b, val in ventanas:
    a, b = pd.Timestamp(a), pd.Timestamp(b)
    # las filas que latest.php mostraba en esa ventana tienen hora de satelite ~3-10 h antes (latencia H113)
    c = cons[(cons["dt"] >= a - pd.Timedelta(hours=12)) & (cons["dt"] <= b)]
    proc = pd.to_datetime(cons["Fecha_Proceso_GitHub"], errors="coerce")
    # Fecha_Proceso_GitHub esta en hora Chile: se compara en hora Chile
    a_cl, b_cl = a - pd.Timedelta(hours=4), b - pd.Timedelta(hours=4)
    en_ventana = cons[(proc >= a_cl) & (proc <= b_cl)]
    antes = cons[(proc >= a_cl - pd.Timedelta(hours=2)) & (proc < a_cl)]
    despues = cons[(proc > b_cl) & (proc <= b_cl + pd.Timedelta(hours=2))]
    print(f"  ventana {val}: filas del consolidado cuya PRIMERA visita cayo dentro: {len(en_ventana)} | en las 2 h previas: {len(antes)} | en las 2 h siguientes: {len(despues)}")
    o = ocr[(ocr["dt"] >= a - pd.Timedelta(hours=12)) & (ocr["dt"] <= b)]
    ko = llaves(o)
    print(f"     filas OCR con hora de satelite en las 12 h previas al cierre de la ventana: {len(o)}; de ellas sin llave en el consolidado: {len(ko - kr)}")
    if len(o):
        print(o[["Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "Distancia_km", "Tipo_Registro", "Fecha_Proceso_GitHub"]].to_string(index=False))
    print("     filas del consolidado con VRP >= 1000 en toda la historia:", int((cons["VRP_MW"] >= 1000).sum()))

print("\n(C) en las llaves compartidas ALERTA_TERMICA_OCR / ALERTA_TERMICA: quien escribio primero")
oa = ocr[ocr["Tipo_Registro"] == "ALERTA_TERMICA_OCR"].set_index(LLAVE)
ca = cons[cons["Tipo_Registro"] == "ALERTA_TERMICA"].set_index(LLAVE)
comunes = oa.index.intersection(ca.index)
po = pd.to_datetime(oa.loc[comunes, "Fecha_Proceso_GitHub"], errors="coerce")
pc = pd.to_datetime(ca.loc[comunes, "Fecha_Proceso_GitHub"], errors="coerce")
d = (pc - po).dt.total_seconds() / 3600
print(f"  llaves comunes: {len(comunes)} | OCR antes que latest.php: {(d > 0).sum()} | latest.php antes: {(d < 0).sum()} | mismo minuto: {(d == 0).sum()}")
print(f"  horas de ventaja del OCR (latest - ocr): mediana {d.median():.2f}, p90 {d.quantile(.9):.2f}, min {d.min():.2f}, max {d.max():.2f}")
print("  Version_OCR de esas filas:", oa.loc[comunes, "Version_OCR"].value_counts().to_dict())
print("  por mes del satelite:", oa.loc[comunes, "mes"].value_counts().sort_index().to_dict())
print("  VRP OCR vs VRP latest.php: |dif| > 0.05 MW en", int(((oa.loc[comunes, "VRP_MW"] - ca.loc[comunes, "VRP_MW"]).abs() > 0.05).sum()), "de", len(comunes),
      "| por sensor:", oa.loc[comunes].assign(dif=(oa.loc[comunes, "VRP_MW"] - ca.loc[comunes, "VRP_MW"]).abs() > 0.05).groupby("Sensor")["dif"].sum().to_dict())

print("\n(D) filas OCR con Editado = SI")
e = ocr[ocr["Editado"] == "SI"]
print("  n =", len(e), "| Tipo:", e["Tipo_Registro"].value_counts().to_dict(), "| mes:", e["mes"].value_counts().sort_index().to_dict())
print("  Version_OCR:", e["Version_OCR"].value_counts().to_dict(), "| Confianza:", e["Confianza_Validacion"].value_counts().to_dict())
print("  notas (primeras 6):")
for n in e["Nota_Validacion"].head(6):
    print("    -", str(n)[:220])
