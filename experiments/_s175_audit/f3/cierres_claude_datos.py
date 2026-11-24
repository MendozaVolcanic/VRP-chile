# -*- coding: utf-8 -*-
"""F3 S175: cierres de CLAUDE.md escritos en S172-S174 que se pueden contrastar con los records de un commit.
A100: «0 de 73.620 records de los 11 Tier A con fuente test1/test1_roi» (main f36a8fb98) y «74 de 74 MODIS desde el
2026-11-02 18 UTC con via_codigo_mirova true». Serie K (#883): todo record de los 11 Tier A desde 2025-02-15 con marca
de regimen y sin C0. Corre sobre f36a8fb98 (control: tiene que reproducir 73.620 y 74) y sobre la base.
P1: si hubiera records test1, el conteo los veria (cuenta por valor de final_hotspot_source). P2: denominador impreso."""
import io, json, subprocess, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
C = sys.argv[1]
T = ["Lascar","Lastarria","Isluga","NevadosDeChillan","Llaima","Villarrica","Chaiten","Tupungatito","PlanchonPeteroa","Copahue","PuyehueCordonCaulle"]
n = 0; src = collections.Counter(); modis_corte = collections.Counter(); sin_reg = collections.Counter(); mind = None; maxd = None
perfil = collections.Counter(); antes_inicio = 0
for v in T:
    d = json.loads(subprocess.run(["git","show",f"{C}:data/mirova_equivalent/{v}.json"],capture_output=True).stdout)
    for r in d["records"]:
        n += 1
        dt = r.get("datetime_utc","")
        mind = dt if mind is None or dt < mind else mind; maxd = dt if maxd is None or dt > maxd else maxd
        if dt < "2025-02-15": antes_inicio += 1
        src[r.get("final_hotspot_source")] += 1
        if str(r.get("sensor","")).startswith("MODIS") and dt >= "2026-11-02T18":
            modis_corte[repr(r.get("via_codigo_mirova"))] += 1
        reg = r.get("regimen")
        if not isinstance(reg, dict): sin_reg[dt[:7]] += 1
        else: perfil[reg.get("perfil")] += 1
print(json.dumps({"commit": C, "n_records_11_tierA": n, "ventana_datetime": [mind, maxd], "antes_2025_02_15": antes_inicio,
  "final_hotspot_source": {str(k): c for k, c in src.most_common()}, "test1_o_test1_roi": src.get("test1",0)+src.get("test1_roi",0),
  "modis_desde_2026_11_02T18_por_via": dict(modis_corte), "records_sin_regimen_por_mes": dict(sorted(sin_reg.items())),
  "regimen_perfil": dict(perfil)}, ensure_ascii=False, indent=1))
