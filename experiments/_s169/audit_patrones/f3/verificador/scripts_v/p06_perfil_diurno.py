"""P3-06: ¿VRP_PROFILE ambiental cambia lo que el evaluador lee como pasada diurna?
Pregunta 1 (si lo medido estuviera roto, lo vería): comparo la decisión diurna de es_pasada_diurna_descartada
bajo varios perfiles para la MISMA pasada diurna; si el entorno no influyera, todas darían igual.
Pregunta 2 (instrumento muerto): control positivo con perfil _s154_ab_diurno_k_on (enable_daytime_viirs true):
debe dar False para VIIRS diurno; si da True igual que mirova_equivalent, el instrumento no ve el perfil.
Uso: python -I p06_perfil_diurno.py ARBOL PERFIL   (un proceso por perfil, porque pipeline.profile se lee al importar)
"""
import os, sys, json
from datetime import datetime, timezone
arbol = sys.argv[1]; perfil = sys.argv[2]
if perfil != "-":
    os.environ["VRP_PROFILE"] = perfil
else:
    os.environ.pop("VRP_PROFILE", None)
sys.path.insert(0, arbol); sys.path.insert(0, arbol + "/scripts")
os.chdir(arbol)
import evaluador_comun  # aplica setdefault
import banco_paridad as bp
import pipeline.profile as p
coords = bp._coords_por_volcan()
lat, lon = coords["Lascar"]
# Láscar ~ -23.37, -67.73: 18:00 UTC = mediodía local aprox (día); 06:00 UTC noche.
casos = {"VIIRS375_dia_18utc": ("VIIRS375", datetime(2026, 11, 5, 18, 0, tzinfo=timezone.utc)),
         "VIIRS750_dia_18utc": ("VIIRS750", datetime(2026, 11, 5, 18, 0, tzinfo=timezone.utc)),
         "MODIS_dia_15utc": ("MODIS", datetime(2026, 11, 5, 15, 0, tzinfo=timezone.utc)),
         "VIIRS375_noche_06utc": ("VIIRS375", datetime(2026, 11, 5, 6, 0, tzinfo=timezone.utc))}
out = {"perfil_pedido": perfil, "VRP_PROFILE_efectivo": os.environ.get("VRP_PROFILE"),
       "PROFILE_NAME": getattr(p, "PROFILE_NAME", None),
       "ENABLE_DAYTIME_MODIS": p.ENABLE_DAYTIME_MODIS}
from pipeline.diurno import flag_viirs_diurno
out["flag_viirs_diurno"] = flag_viirs_diurno()
for k, (b, dt) in casos.items():
    out[k + "_descartada"] = bp.es_pasada_diurna_descartada(b, lat, lon, dt)
print(json.dumps(out, ensure_ascii=False))
