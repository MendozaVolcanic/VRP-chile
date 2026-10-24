# -*- coding: utf-8 -*-
"""S157: elige las pasadas del probe de saturación de Nevados de Chillán. ESCRITO ANTES DE CORRER EL PROBE.

POR QUÉ. El probe del PR #871 dejó un resto del déficit oblicuo que ni el fondo (D25) ni la selección cierran, y lo
mandó a D17 (área, remuestreo) o a saturación. Para separar las dos hay que mirar las pasadas donde el déficit vive:
el sensor oblicuo (cenit de 50° o más) en las noches en que MIROVA sí alertó. Este script las saca del corpus
persistido y de la referencia CONGELADA del pre-registro (la misma que lee `analizar_probe.py` de #871, ventana
2026-08-29 a 2026-10-18), sin elegir a mano.

Qué entra:
  A. Los 10 gránulos del 2026-10-18 de #871 (fijos, para comparar con ese probe).
  B. Pasadas nocturnas de Chillán con `sensor_zenith_deg >= 50` y una ALERTA de MIROVA pareada (±120 s,
     `banco_paridad.parear`, consolidado antes que OCR) en la misma familia de sensor.
  C. Control: una pasada casi a nadir (cenit < 15°) por familia, con el `t_max_k` más bajo de la ventana entre las
     que tienen L1B estándar o NRT y sin alerta de MIROVA. Sin calor no puede haber saturación: debe dar 0.

Salida: `pasadas.json` (sensor, gránulo, cenit, VRP nuestro publicado, VRP de MIROVA, grupo A/B/C).
Uso: python experiments/_s157_saturacion/seleccionar_pasadas.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (str(RAIZ), str(RAIZ / "scripts"), str(RAIZ / "experiments" / "_s151_prereg_fk_11")):
    sys.path.insert(0, _p)
import banco_paridad as bp  # noqa: E402
import sustrato as fk  # noqa: E402

VOL = "NevadosDeChillan"
REF = RAIZ / "experiments" / "_s157_prereg_d25" / "_congelado_v1"
VENTANA = ("2026-08-29", "2026-10-18")
CENIT_OBLICUO = 50.0
CENIT_NADIR = 15.0
FIJOS_871 = [  # experiments/_s157_prereg_d25/probe_l1b/probe_chillan.py, PASADAS
    ("VIIRS_NOAA21", "VJ202IMG.A2026291.0506.021.2026291103813.nc"),
    ("VIIRS_NOAA21_750", "VJ202MOD.A2026291.0506.021.2026291103813.nc"),
    ("VIIRS_SNPP", "VNP02IMG.A2026291.0542.002.2026291121847.nc"),
    ("VIIRS_SNPP_750", "VNP02MOD.A2026291.0542.002.2026291121847.nc"),
    ("VIIRS_NOAA20", "VJ102IMG.A2026291.0600.021.2026291123439.nc"),
    ("VIIRS_NOAA20_750", "VJ102MOD.A2026291.0600.021.2026291123439.nc"),
    ("VIIRS_NOAA21", "VJ202IMG.A2026291.0648.021.2026291130237.nc"),
    ("VIIRS_NOAA21_750", "VJ202MOD.A2026291.0648.021.2026291130237.nc"),
    ("MODIS_TERRA", "MOD021KM.A2026291.0120.061.2026291131348.hdf"),
    ("MODIS_AQUA", "MYD021KM.A2026291.0750.061.2026292011058.hdf"),
]


def dt_rec(r):
    t = r["datetime_utc"].replace("T", " ")[:16]   # el corpus guarda "AAAA-MM-DD HH:MM"
    return datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def main():
    recs = json.loads((RAIZ / "data" / "mirova_equivalent" / ("%s.json" % VOL)).read_text(encoding="utf-8"))["records"]
    filas = fk.cargar_filas(REF, False)
    por_vb, *_ = bp.indexar_referencia(filas, bp._coords_por_volcan(), VENTANA)
    por_gran = {r.get("granule"): r for r in recs}
    salida, vistos = [], set()

    def fila(r, grupo):
        b = bp.bucket(r["sensor"])
        al = [x for x in bp.parear(por_vb.get((VOL, b), []), dt_rec(r)) if bp.es_alerta(x["tipo"])]
        al.sort(key=lambda x: (x["source"] != "CONS",))
        pc = r.get("primary_cluster") or {}
        return {"grupo": grupo, "sensor": r["sensor"], "granulo": r["granule"], "datetime_utc": r["datetime_utc"],
                "cenit": r.get("sensor_zenith_deg"), "t_max_k": r.get("t_max_k"), "pc_vrp_mw": pc.get("vrp_mw"),
                "f5_core_vrp_mw": r.get("f5_core_vrp_mw"), "mirova_mw": al[0]["vrp_mw"] if al else None,
                "mirova_tipo": al[0]["tipo"] if al else None, "mirova_fuente": al[0]["source"] if al else None}

    for s, g in FIJOS_871:
        r = por_gran.get(g)
        salida.append(fila(r, "A") if r else {"grupo": "A", "sensor": s, "granulo": g, "error": "sin record"})
        vistos.add(g)
    oblicuas = []
    for r in recs:
        if not (VENTANA[0] <= r["datetime_utc"][:10] <= VENTANA[1]) or r.get("granule") in vistos:
            continue
        if (r.get("sensor_zenith_deg") or 0) < CENIT_OBLICUO:
            continue
        f = fila(r, "B")
        if f["mirova_mw"] is not None and bp.es_alerta(f["mirova_tipo"] or ""):
            oblicuas.append(f)
    oblicuas.sort(key=lambda f: f["datetime_utc"])
    salida += oblicuas
    for fam in ("VIIRS", "MODIS"):
        cand = [r for r in recs if VENTANA[0] <= r["datetime_utc"][:10] <= VENTANA[1]
                and (r.get("sensor") or "").startswith(fam) and (r.get("sensor_zenith_deg") or 99) < CENIT_NADIR
                and r.get("t_max_k") is not None and not (r.get("sensor") or "").endswith("_750")]
        cand = [fila(r, "C") for r in cand]
        cand = [c for c in cand if c["mirova_mw"] is None]
        cand.sort(key=lambda c: c["t_max_k"])
        if cand:
            salida.append(cand[0])
            if fam == "VIIRS":   # el par M-band del mismo gránulo
                g750 = cand[0]["granulo"].replace("02IMG", "02MOD")
                r750 = por_gran.get(g750)
                if r750:
                    salida.append(fila(r750, "C"))
    (AQUI / "pasadas.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in salida:
        print("%s %-17s %-48s cenit %5s tmax %6s pc %7s f5 %7s | MIROVA %s %s" % (
            f["grupo"], f["sensor"], f["granulo"], f.get("cenit"), f.get("t_max_k"), f.get("pc_vrp_mw"),
            f.get("f5_core_vrp_mw"), f.get("mirova_mw"), f.get("mirova_tipo")))
    print("A %d | B %d | C %d" % tuple(sum(1 for f in salida if f["grupo"] == g) for g in "ABC"))


if __name__ == "__main__":
    main()
