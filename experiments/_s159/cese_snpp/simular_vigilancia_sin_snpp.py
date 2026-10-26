"""S159 cese SNPP: ¿la vigilancia de frescura de produccion (vigilancia_sombra.avisos_produccion) ve que muere
UNA plataforma? Sin red, con records sinteticos.

Pregunta 1: si avisara por plataforma, el escenario "sin SNPP" daria avisos > 0.
Pregunta 2 / control positivo: el escenario "sin MODIS" (muere un bucket entero) DEBE dar avisos; si no, el
instrumento esta muerto. Escenario base (todo vivo): 0 avisos.
"""
import sys, io
from pathlib import Path
from datetime import date, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ARBOL)); sys.path.insert(0, str(ARBOL / "scripts"))
import vigilancia_sombra as vs  # noqa: E402
import auto_audit_weekly as aa  # noqa: E402

HOY = date(2026, 11, 12)
SENS = {"MODIS": ["MODIS_TERRA", "MODIS_AQUA"], "VIIRS375": ["VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"],
        "VIIRS750": ["VIIRS_SNPP_750", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750"]}


def recs(muere):
    out = []
    for d in range(20):
        dia = HOY - timedelta(days=d)
        for v in aa.VOLS:
            for b, plats in SENS.items():
                for p in plats:
                    corte = date(2026, 11, 2)
                    if muere(p) and dia > corte:
                        continue
                    out.append({"vol": v, "b": b, "noche": dia.isoformat(), "sensor": p})
    return out


for nombre, f in [("todo vivo", lambda p: False), ("sin SNPP desde 2-nov", lambda p: "SNPP" in p),
                  ("sin MODIS desde 2-nov (control positivo)", lambda p: p.startswith("MODIS"))]:
    av = vs.avisos_produccion(recs(f), HOY.isoformat())
    print(f"{nombre}: {len(av)} avisos" + (f" | ej: {av[0]}" if av else ""))
