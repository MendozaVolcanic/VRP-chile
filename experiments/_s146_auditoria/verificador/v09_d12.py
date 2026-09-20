# -*- coding: utf-8 -*-
"""V-09: las 76 noches 'FN recuperadas' de D12/S121 (Lascar MODIS, 2025-02-15..05-15).
(1) Si roto fallaria? control: imprime n de records MODIS en ventana (debe ser >0) y n OSF en ventana.
(2) Instrumento muerto? la busqueda OSF por IDvolc=355100 da 10028 filas (por nombre 'ascar' daba 0: trampa A89)."""
import io, sys, pandas as pd
from vlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = cargar(); LO, HI = "2025-02-15", "2025-05-15"
rs = [r for r in D["Lascar"] if bucket(r["sensor"]) == "modis" and LO <= r["datetime_utc"][:10] <= HI]
cand = [r for r in rs if r.get("distance_class") == "far" and (r.get("primary_cluster") or {}).get("centroid_dist_km") is not None
        and r["primary_cluster"]["centroid_dist_km"] <= 5 and (r["primary_cluster"].get("vrp_mw") or 0) > 0]
noches_cand = {r["datetime_utc"][:10] for r in cand}
summit = {r["datetime_utc"][:10] for r in rs if r.get("distance_class") == "summit" and ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 0}
print("records MODIS Lascar en ventana:", len(rs), "| far con cumulo<=5km:", len(cand), "| noches:", len(noches_cand), "| noches ya summit:", len(summit), "| noches candidatas no cubiertas:", len(noches_cand - summit))
ref = referencia(); print("ref NRT (CONS+OCR) Lascar en ventana:", sum(1 for f in ref if f["vol"] == "Lascar" and LO <= f["fecha"] <= HI))
o = pd.read_csv(os.path.join(ROOT, "data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv"), usecols=["timeUTC", "IDvolc", "Resolution", "Dayflag"])
o = o[(o.IDvolc == 355100) & (o.Resolution == 1000)].copy(); o["t"] = pd.to_datetime(o.timeUTC, format="%d/%m/%Y %H:%M")
o = o[(o.t >= LO) & (o.t < "2025-05-16")]; osf = {str(x) for x in o.t.dt.date}
print("OSF v2.5 MODIS Lascar en ventana: filas", len(o), "noches", len(osf), "Dayflag", o.Dayflag.value_counts().to_dict())
nc = noches_cand - summit
print("candidatas no cubiertas con noche OSF:", len(nc & osf), "de", len(nc), "| noches OSF ya publicadas summit:", len(osf & summit), "| noches OSF sin ninguna de las dos:", len(osf - summit - noches_cand))
