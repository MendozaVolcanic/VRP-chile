# -*- coding: utf-8 -*-
"""Para cada pasada cuya etiqueta o publicacion cambia de "hoy" a "orbita" (banco_variantes_0110.json):
fraccion de NUESTRO anillo de fondo que cae en el granulo que MIROVA lista, y si el record que publica es el
del granulo de MIROVA. Pasadas de un solo record nuestro (perdidas reales): anillo / mediana de pasadas
enteras del mismo volcan y plataforma a +-3 grados de cenit (1 = ROI entero en nuestro granulo).
Pregunta 1: si la publicacion extra fuera sobre-publicacion real, la veria? Si: seria en el granulo de MIROVA
con fraccion alta. Pregunta 2: control: fraccion de pasadas enteras = 1 (borde_por_anillo_salida.txt)."""
import collections, json, statistics, sys
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(sys.argv[1])
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
ref = collections.defaultdict(set)
for f in filas:
    ref[(f["volcano"], f["sensor_bucket"])].add(f["fecha_utc"][:16])
recs = {}
for vol in bp.VOLS:
    for r in json.load(open(RAIZ / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]:
        recs[(vol, r["sensor"], r["datetime_utc"][:16])] = r
def ref_z(vol, sensor, z):
    p = timedelta(minutes=5 if sensor.startswith("MODIS") else 6)
    xs = []
    for (v, s, t), r in recs.items():
        if v == vol and s == sensor and r.get("diag_n_bg_anillo") and r.get("sensor_zenith_deg") is not None \
                and abs(r["sensor_zenith_deg"] - z) <= 3:
            tt = datetime.strptime(t, "%Y-%m-%d %H:%M")
            if (v, s, (tt - p).strftime("%Y-%m-%d %H:%M")) not in recs and (v, s, (tt + p).strftime("%Y-%m-%d %H:%M")) not in recs:
                xs.append(r["diag_n_bg_anillo"])
    return statistics.median(xs) if len(xs) >= 5 else None
d = json.load(open(Path(__file__).with_name("banco_variantes_0110.json"), encoding="utf-8"))
resumen = collections.Counter()
for c in d["cambios_hoy_vs_orbita"]:
    m = [recs[(c["vol"], c["sensor"], h)] for h in c["horas"]]
    an = [x.get("diag_n_bg_anillo") or 0 for x in m]
    en_ref = [h in ref[(c["vol"], c["b"])] for h in c["horas"]]
    if len(m) == 2:
        im = en_ref.index(True) if any(en_ref) else None
        frac = an[im] / sum(an) if im is not None and sum(an) else None
        publica_el_de_mirova = (c["pub_por_hora"][im] == 1) if im is not None else None
        tipo = "partida"
    else:
        rz = ref_z(c["vol"], c["sensor"], m[0]["sensor_zenith_deg"])
        frac = round(an[0] / rz, 3) if rz else None     # fraccion del ROI en NUESTRO granulo
        publica_el_de_mirova = None
        tipo = "un_solo_record"
    clave = (c["b"], tipo, f"hoy {c['hoy']} -> orbita {c['orbita']}",
             "MIROVA ciego (frac<0,5)" if (tipo == "partida" and frac is not None and frac < 0.5) else "")
    resumen[clave] += 1
    print(c["b"], c["vol"], c["horas"], "pub", c["pub_por_hora"], "en_ref", en_ref, "anillo", an,
          ("frac_granulo_MIROVA" if tipo == "partida" else "frac_ROI_en_nuestro"), None if frac is None else round(frac, 3),
          "publica_el_de_MIROVA", publica_el_de_mirova, "hoy", c["hoy"], "orbita", c["orbita"])
print()
for k, v in sorted(resumen.items()):
    print(k, v)
