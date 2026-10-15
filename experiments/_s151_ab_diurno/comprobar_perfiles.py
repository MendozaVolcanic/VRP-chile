# -*- coding: utf-8 -*-
"""Los dos brazos del A/B diurno LEEN lo que declaran (A89, A118). Salida: comprobar_perfiles_salida.txt.

POR QUÉ. Un flag escrito en la sección equivocada del YAML no da error: arranca apagado y el A/B corre
dos brazos idénticos (S124, `enable_utm_regrid`). Por eso no se mira el YAML sino lo que resuelve
`pipeline.profile` en un proceso limpio por perfil, y además lo que deciden los consumidores del flag
(`pipeline/diurno.py`), que es lo que de verdad abre o cierra las compuertas.

Qué comprueba, en un subproceso por perfil (pipeline.profile lee VRP_PROFILE al importarse):
  1. ENABLE_DAYTIME_VIIRS: True en `_s151_ab_diurno_on`, False en el control y en producción.
  2. Las compuertas a través de diurno.py: el filtro nocturno de fetch y de run_pipeline
     (`aplica_filtro_nocturno(True, plataforma)`) se abre para VIIRS 375 y 750 sólo en el brazo
     diurno y nunca para MODIS; `es_pasada_diurna_descartada` (la regla de store que reusa la
     auditoría) deja de descartar una pasada VIIRS diurna de Láscar sólo en el brazo diurno.
  3. Que cada brazo difiere de `mirova_equivalent` SOLO en lo declarado: se comparan todas las
     constantes en mayúsculas de pipeline.profile.
Sale con error si algo no cuadra.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PERFILES = ("mirova_equivalent", "_s151_ab_diurno_control", "_s151_ab_diurno_on")
SONDA = r"""
import json, sys
from datetime import datetime, timezone
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts')
import pipeline.profile as p
from pipeline import diurno
from auto_audit_weekly import es_pasada_diurna_descartada, _coords_por_volcan
lat, lon = _coords_por_volcan()['Lascar']
dia = datetime(2026, 6, 15, 17, 24, tzinfo=timezone.utc)
noche = datetime(2026, 6, 15, 5, 0, tzinfo=timezone.utc)
cte = {}
for k in dir(p):
    if k.isupper():
        v = getattr(p, k)
        if isinstance(v, (set, frozenset)):
            v = sorted(v)  # un set cambia de orden entre procesos (hash aleatorio)
        try:
            json.dumps(v); cte[k] = v
        except TypeError:
            cte[k] = repr(v)
print(json.dumps({
    'cte': cte,
    'flag_vivo': diurno.flag_viirs_diurno(),
    'filtro_nocturno': {pl: diurno.aplica_filtro_nocturno(True, pl) for pl in
                        ('VIIRS_SNPP', 'VIIRS_NOAA20', 'VIIRS_NOAA21_750', 'MODIS_AQUA', 'MODIS_TERRA')},
    'descarta_dia': {b: es_pasada_diurna_descartada(b, lat, lon, dia) for b in ('VIIRS375', 'VIIRS750', 'MODIS')},
    'descarta_noche': {b: es_pasada_diurna_descartada(b, lat, lon, noche) for b in ('VIIRS375', 'VIIRS750', 'MODIS')},
}))
"""


def sondear(perfil):
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    o = subprocess.run([sys.executable, "-c", SONDA], cwd=str(RAIZ), env=env, capture_output=True,
                       text=True, encoding="utf-8")
    if o.returncode != 0:
        raise SystemExit("la sonda falló con %s:\n%s" % (perfil, o.stderr[-2000:]))
    return json.loads(o.stdout.strip().splitlines()[-1])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    r = {p: sondear(p) for p in PERFILES}
    mal = []
    esperado_flag = {"mirova_equivalent": False, "_s151_ab_diurno_control": False, "_s151_ab_diurno_on": True}
    for p in PERFILES:
        x = r[p]
        print("== %s" % p)
        print("   ENABLE_DAYTIME_VIIRS (pipeline.profile) = %s | diurno.flag_viirs_diurno() = %s | DATA_SUBDIR = %s"
              % (x["cte"]["ENABLE_DAYTIME_VIIRS"], x["flag_vivo"], x["cte"]["DATA_SUBDIR"]))
        print("   filtro nocturno de fetch y run_pipeline (True = se descarta el día): %s" % x["filtro_nocturno"])
        print("   store descarta Láscar 2026-06-15 17:24 UTC (día): %s | 05:00 UTC (noche): %s"
              % (x["descarta_dia"], x["descarta_noche"]))
        on = esperado_flag[p]
        if x["cte"]["ENABLE_DAYTIME_VIIRS"] is not on or x["flag_vivo"] is not on:
            mal.append("%s: flag leído %s, se esperaba %s" % (p, x["cte"]["ENABLE_DAYTIME_VIIRS"], on))
        for pl, v in x["filtro_nocturno"].items():
            esp = not (on and pl.startswith("VIIRS"))
            if v is not esp:
                mal.append("%s: filtro nocturno de %s = %s, se esperaba %s" % (p, pl, v, esp))
        for b, v in x["descarta_dia"].items():
            esp = not (on and b.startswith("VIIRS"))
            if v is not esp:
                mal.append("%s: store descarta el día de %s = %s, se esperaba %s" % (p, b, v, esp))
        if any(x["descarta_noche"].values()):
            mal.append("%s: store descarta una pasada nocturna" % p)
        if p != "mirova_equivalent" and x["cte"]["DATA_SUBDIR"] != p:
            mal.append("%s: escribe en %s, no en su directorio propio (A47)" % (p, x["cte"]["DATA_SUBDIR"]))
    base = r["mirova_equivalent"]["cte"]
    permitidas = {"_s151_ab_diurno_control": {"PROFILE_NAME", "DATA_SUBDIR", "PROFILE_DESCRIPTION"},
                  "_s151_ab_diurno_on": {"PROFILE_NAME", "DATA_SUBDIR", "PROFILE_DESCRIPTION", "ENABLE_DAYTIME_VIIRS"}}
    for p, ok in permitidas.items():
        dif = sorted(k for k in set(base) | set(r[p]["cte"]) if base.get(k) != r[p]["cte"].get(k))
        print("== %s difiere de mirova_equivalent en %d constantes de pipeline.profile: %s" % (p, len(dif), dif))
        extra = [k for k in dif if k not in ok]
        if extra:
            mal.append("%s difiere de producción en algo no declarado: %s" % (p, extra))
    print("\nRESULTADO: %s" % ("OK, cada brazo lee lo que declara" if not mal else "FALLA: " + "; ".join(mal)))
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main())
