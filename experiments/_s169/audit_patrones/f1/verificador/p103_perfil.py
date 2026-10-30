# -*- coding: utf-8 -*-
"""VF P1-03: ¿el filtro nocturno del generador (banco_paridad -> auto_audit_weekly.es_pasada_diurna_descartada, codigo
de main 443da8649) depende de VRP_PROFILE del shell? Corre en un proceso hijo por perfil (el perfil se lee al importar).
Pregunta 1: si el filtro dependiera del perfil, una pasada VIIRS 750 diurna cambiaria de veredicto entre perfiles.
Pregunta 2 / control: la pasada nocturna tiene que salir 'no descartada' en todos; MODIS diurno 'descartada' en todos
(su rama diurna tiene flag propio). Si todo saliera igual, el instrumento podria estar muerto: por eso el control."""
import subprocess, sys, os, json
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = os.path.abspath("main443").replace("\\", "/")
HIJO = r'''
import sys, os, json
sys.path.insert(0, RAIZ); sys.path.insert(0, RAIZ + "/scripts")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from datetime import datetime, timezone
import auto_audit_weekly as A
from pipeline import profile as P
lat, lon = A._coords_por_volcan()["Lascar"]
casos = {"V750 2026-10-15 17:00 UTC (mediodia local)": ("VIIRS750", datetime(2026,10,15,17,0,tzinfo=timezone.utc)),
         "V750 2026-10-15 06:00 UTC (noche)": ("VIIRS750", datetime(2026,10,15,6,0,tzinfo=timezone.utc)),
         "MODIS 2026-10-15 17:00 UTC": ("MODIS", datetime(2026,10,15,17,0,tzinfo=timezone.utc))}
print(json.dumps({"perfil": os.environ["VRP_PROFILE"], "PROFILE_NAME": getattr(P, "PROFILE_NAME", None),
  "ENABLE_DAYTIME_VIIRS": bool(P.ENABLE_DAYTIME_VIIRS),
  **{k: A.es_pasada_diurna_descartada(b, lat, lon, t) for k, (b, t) in casos.items()}}, ensure_ascii=False))
'''.replace("RAIZ", repr(RAIZ))
for perfil in (None, "mirova_equivalent", "_s154_ab_diurno_k_on", "experimental"):
    env = {k: v for k, v in os.environ.items() if k != "VRP_PROFILE"}
    if perfil: env["VRP_PROFILE"] = perfil
    o = subprocess.run([sys.executable, "-I", "-c", HIJO], capture_output=True, text=True, encoding="utf-8", env=env, cwd=RAIZ)
    print(f"VRP_PROFILE={perfil!r}: rc={o.returncode}", o.stdout.strip() or o.stderr.strip()[-600:])
