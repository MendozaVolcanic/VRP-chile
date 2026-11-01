# -*- coding: utf-8 -*-
"""Cuando el volcan cae en dos granulos de la misma orbita y MIROVA lista solo uno, cual elige?

Fenomeno: de noche Aqua, Suomi NPP, NOAA-20 y NOAA-21 bajan de norte a sur (el granulo posterior es el
del sur) y Terra sube de sur a norte (el granulo anterior es el del sur). Si MIROVA eligiera el granulo
que contiene el crater, la fraccion del anillo de fondo NUESTRO que cae en su granulo seria casi siempre
mayor que 0,5 y el lado (norte o sur) seria indistinto. Si eligiera siempre el del sur, la fraccion se
repartiria entre 0 y 1.
Pregunta 1: lo veria? Si: separo por plataforma, que invierte la relacion tiempo-latitud.
Pregunta 2: control: las pasadas de dos granulos en que MIROVA lista los DOS no entran (se cuentan aparte).
Denominador: cadenas de dos records nuestros (11 Tier A, toda la historia con referencia) con exactamente un
granulo listado por MIROVA a +-120 s. Fraccion = diag_n_bg_anillo del miembro de MIROVA / suma de los dos.
"""
import collections, json, statistics, sys
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(sys.argv[1])
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
ref = collections.defaultdict(lambda: collections.defaultdict(list))
for f in filas:
    if f["sensor_bucket"] in bp.BUCKETS:
        ref[(f["volcano"], f["sensor_bucket"])][datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M")].append(f)
SUR_ES_POSTERIOR = {"MODIS_TERRA": False}   # Terra sube de noche; el resto baja
res = collections.defaultdict(list)
lados = collections.Counter()
for vol in bp.VOLS:
    recs = json.load(open(RAIZ / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
    por = collections.defaultdict(dict)
    for r in recs:
        por[r["sensor"]][datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")] = r
    for sensor, d in por.items():
        b = bp.bucket(sensor); p = timedelta(minutes=5 if b == "MODIS" else 6)
        plataforma = sensor.replace("_750", "")
        for t, r1 in d.items():
            r2 = d.get(t + p)
            if r2 is None or d.get(t - p) is not None or d.get(t + 2 * p) is not None:
                continue
            m1, m2 = bool(ref[(vol, b)].get(t)), bool(ref[(vol, b)].get(t + p))
            if m1 and m2:
                lados[(b, "MIROVA lista los dos")] += 1; continue
            if not (m1 or m2):
                lados[(b, "MIROVA no lista ninguno")] += 1; continue
            n1, n2 = r1.get("diag_n_bg_anillo") or 0, r2.get("diag_n_bg_anillo") or 0
            if n1 + n2 == 0:
                continue
            frac = (n1 if m1 else n2) / (n1 + n2)
            sur_posterior = SUR_ES_POSTERIOR.get(plataforma, True)
            elige_sur = (m2 and sur_posterior) or (m1 and not sur_posterior)
            lados[(b, plataforma, "elige sur" if elige_sur else "elige norte")] += 1
            tipo = [x["tipo"] for x in ref[(vol, b)].get(t if m1 else t + p)]
            clase = "alerta" if any(bp.es_alerta(x) for x in tipo) else "rutina_u_otro"
            res[(b, clase)].append(frac)
for k in sorted(lados):
    print(k, lados[k])
for k in sorted(res):
    v = res[k]
    print(k, f"n {len(v)} fraccion del anillo en el granulo de MIROVA: mediana {statistics.median(v):.2f}, "
             f"bajo 0,5 en {sum(x < 0.5 for x in v)}, bajo 0,2 en {sum(x < 0.2 for x in v)}")
