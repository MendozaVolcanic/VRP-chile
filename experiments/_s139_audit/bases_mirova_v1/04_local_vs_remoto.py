"""04: que copias locales/snapshots estan congeladas y en que difieren del remoto.

Compara: (a) checkout local Mirova-v1/monitoreo_satelital, (b) el backup manual
'registro_vrp_consolidado al 08042026.csv', (c) el snapshot semanal de VRP Chile,
(d) latest_consolidado.csv de VRP Chile, (e) data/mirova_reference/registro_vrp_ocr.csv
(congelado) contra los CSV vigentes del remoto (--remoto DIR).
"""
import os
import sys

import pandas as pd

from comun import LLAVE, LOCAL_MIROVA, REPO, SNAPSHOT, dir_remoto, encabezado, leer

D = dir_remoto(sys.argv)
encabezado(
    "COPIAS LOCALES Y SNAPSHOTS CONTRA EL REMOTO",
    "una copia congelada muestra max fecha vieja y filas de menos; una copia divergente muestra llaves que el remoto no tiene",
    "un archivo ausente se imprime como NO EXISTE; una comparacion de un archivo consigo mismo daria 0 diferencias (control abajo)",
    "el remoto contra si mismo debe dar 0 y 0; el remoto contra su copia sin la ultima fila debe dar 1",
)


def resumen(path):
    if not os.path.exists(path):
        return None
    df = leer(path)
    return df


def comparar(nombre, a, b):
    if a is None or b is None:
        print(f"  {nombre}: NO EXISTE alguno de los dos")
        return
    ka = set(zip(a["timestamp"].astype("int64"), a["Volcan"], a["Sensor"]))
    kb = set(zip(b["timestamp"].astype("int64"), b["Volcan"], b["Sensor"]))
    print(f"  {nombre}: filas {len(a)} vs remoto {len(b)} | max fecha {a['dt'].max()} vs {b['dt'].max()} "
          f"| llaves solo local: {len(ka-kb)} | solo remoto: {len(kb-ka)}")
    comunes = ka & kb
    if comunes and "Tipo_Registro" in a and "Tipo_Registro" in b:
        ia = a.set_index(LLAVE); ib = b.set_index(LLAVE)
        ia = ia[~ia.index.duplicated()]; ib = ib[~ib.index.duplicated()]
        idx = list(comunes)
        dif_tipo = (ia.loc[idx, "Tipo_Registro"] != ib.loc[idx, "Tipo_Registro"]).sum()
        dif_vrp = ((ia.loc[idx, "VRP_MW"] - ib.loc[idx, "VRP_MW"]).abs() > 0.005).sum()
        dif_vol = 0
        print(f"      en las {len(comunes)} llaves comunes: Tipo distinto {int(dif_tipo)}, VRP distinto {int(dif_vrp)}")
        if dif_tipo:
            ej = ia.loc[idx][ia.loc[idx, "Tipo_Registro"] != ib.loc[idx, "Tipo_Registro"]].head(5)
            for k, r in ej.iterrows():
                print(f"        ej {k}: local {r['Tipo_Registro']} / remoto {ib.loc[k, 'Tipo_Registro']}")


rem_cons = resumen(f"{D}/registro_vrp_consolidado.csv")
rem_ocr = resumen(f"{D}/registro_vrp_ocr.csv")
rem_pos = resumen(f"{D}/registro_vrp_positivos.csv")
rem_mae = resumen(f"{D}/registro_vrp_maestro_publicable.csv")
print("remoto consolidado:", len(rem_cons), "filas, max", rem_cons["dt"].max())

print("\n--- (a) checkout local Mirova-v1/monitoreo_satelital")
for f, r in [("registro_vrp_consolidado.csv", rem_cons), ("registro_vrp_ocr.csv", rem_ocr),
             ("registro_vrp_positivos.csv", rem_pos), ("registro_vrp_maestro_publicable.csv", rem_mae)]:
    comparar(f, resumen(os.path.join(LOCAL_MIROVA, f)), r)
pet = resumen(os.path.join(LOCAL_MIROVA, "registro_Peteroa.csv"))
if pet is not None:
    print("  registro_Peteroa.csv (solo local):", len(pet), "filas,", pet["dt"].min(), "->", pet["dt"].max(),
          "| Volcan:", pet["Volcan"].unique().tolist(), "| en remoto:", os.path.exists(f"{D}/registro_Peteroa.csv"))
    # esa fila existe en el remoto bajo PlanchonPeteroa?
    k = set(zip(pet["timestamp"].astype("int64"), pet["Sensor"]))
    rp = rem_cons[rem_cons["Volcan"] == "PlanchonPeteroa"]
    kr = set(zip(rp["timestamp"].astype("int64"), rp["Sensor"]))
    print("    sus (timestamp, Sensor) presentes en el remoto como PlanchonPeteroa:", len(k & kr), "/", len(k))

print("\n--- (b) backup manual 'registro_vrp_consolidado al 08042026.csv'")
b = resumen(os.path.join(LOCAL_MIROVA, "registro_vrp_consolidado al 08042026.csv"))
comparar("al 08042026", b, rem_cons)
if b is not None:
    print("   Volcan en el backup:", b["Volcan"].value_counts().to_dict())
    print("   rango:", b["dt"].min(), "->", b["dt"].max())

print("\n--- (c) snapshot semanal de VRP Chile (data/mirova_reference/mirova_v1_snapshot)")
for f, r in [("registro_vrp_consolidado.csv", rem_cons), ("registro_vrp_ocr.csv", rem_ocr)]:
    comparar(f, resumen(os.path.join(SNAPSHOT, f)), r)
for f in ("registro_Chaiten.csv", "registro_Lascar.csv", "registro_Tupungatito.csv"):
    s = resumen(os.path.join(SNAPSHOT, f))
    rr = resumen(f"{D}/{f}")
    if s is not None:
        print(f"  {f} (snapshot): {len(s)} filas, {s['dt'].min()} -> {s['dt'].max()} | remoto hoy: {len(rr) if rr is not None else 'NO'} filas")

print("\n--- (d) latest_consolidado.csv (raiz de VRP Chile, cron 1 h)")
comparar("latest_consolidado.csv", resumen(os.path.join(REPO, "latest_consolidado.csv")), rem_cons)
print("\n--- (e) data/mirova_reference/registro_vrp_ocr.csv (congelado segun LEEME)")
comparar("registro_vrp_ocr.csv congelado", resumen(os.path.join(REPO, "data", "mirova_reference", "registro_vrp_ocr.csv")), rem_ocr)
print("\n--- (f) 01_05_2026_registro_vrp_consolidado.csv (fallback del frontend)")
comparar("01_05_2026", resumen(os.path.join(REPO, "01_05_2026_registro_vrp_consolidado.csv")), rem_cons)

print("\n--- CONTROLES")
comparar("remoto vs remoto", rem_cons, rem_cons)
comparar("remoto sin la ultima fila vs remoto", rem_cons.iloc[:-1], rem_cons)
