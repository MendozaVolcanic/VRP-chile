# -*- coding: utf-8 -*-
"""S131 - El crecimiento de area que el sensor REALMENTE tiene, segun su ATBD.

POR QUE. `factor_requerido.py` despejo de los datos cuanto crecimiento de area haria
falta para aplanar el gradiente cenital. Falta la otra mitad: cuanto crecimiento hay
DISPONIBLE fisicamente. Si el requerido excede lo disponible, el area no alcanza y
hay un segundo mecanismo; si entra comodo, el area es explicacion suficiente.

FUENTE, en el tope de la jerarquia A35 (ATBD del sensor, no paper ni nota): VIIRS
Geolocation ATBD 423-ATBD-002, Tabla 2.2-1 "Spatial Attributes of VIIRS Bands",
Horizontal Sampling Interval en km (along-track x along-scan), nadir y end of scan.
PDF local en `documentacion/VIIRS_Geolocation_ATBD_2014.pdf`.

EL MATIZ QUE IMPORTA, y que es donde nuestro codigo se equivoco: el mismo ATBD dice
que "the pixel growth multiplier is limited to approximately 2 both along track and
along scan". Ese 2 es POR EJE. El area es el producto de los dos ejes, asi que el
crecimiento de AREA es ~4, no ~2. El docstring de `pipeline/scan_geometry.py`
`viirs_pixel_areas` leyo ese 2 como si fuera el area y de ahi salio su tope de 2.0x.

Nota sobre M13 (nuestra banda MIR de 750 m): es de doble ganancia y la tabla marca
que NO se agrega a bordo, con HSI nadir 0.742 x 0.259. La nota al pie 4 del ATBD
aclara que su agregacion along-scan se hace en procesamiento de tierra para igualar
a las bandas de ganancia simple, asi que el pixel entregado en L1B corresponde a la
fila de las M agregadas (M6/M8: 0.742 x 0.776).
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "ley_atbd.json")
REQ = os.path.join(HERE, "factor_requerido.json")

# Tabla 2.2-1 del ATBD, transcrita con su cita. (along_track_km, along_scan_km)
HSI = {
    "v375": {"banda": "I4 (3.74 um)", "fila_atbd": "I4",
             "nadir": (0.371, 0.388), "end_of_scan": (0.80, 0.789)},
    "v750": {"banda": "M13 (4.05 um), agregada en tierra -> fila M6/M8",
             "fila_atbd": "M6/M8", "nadir": (0.742, 0.776),
             "end_of_scan": (1.60, 1.58)},
}
SCAN_MAX_DEG = 56.28        # ATBD: fin de scan
ZEN_MAX_DEG = 70.3          # cenital en tierra correspondiente (R=6371, H=829)


def main():
    req = json.load(open(REQ, encoding="utf-8")) if os.path.exists(REQ) else {}
    res = {"fuente": ("VIIRS Geolocation ATBD 423-ATBD-002 Tabla 2.2-1, HSI km "
                      "(along-track x along-scan), nadir y end of scan (scan angle "
                      f"{SCAN_MAX_DEG} deg, cenital en tierra ~{ZEN_MAX_DEG} deg)"),
           "por_sensor": {}}

    print("CRECIMIENTO DE AREA DISPONIBLE vs REQUERIDO")
    print()
    print(f"{'sensor':9s} {'nadir km2':>10s} {'borde km2':>10s} {'x eje-tr':>9s} "
          f"{'x eje-sc':>9s} {'x AREA':>8s}")
    for bk, d in HSI.items():
        a0 = d["nadir"][0] * d["nadir"][1]
        a1 = d["end_of_scan"][0] * d["end_of_scan"][1]
        g_tr = d["end_of_scan"][0] / d["nadir"][0]
        g_sc = d["end_of_scan"][1] / d["nadir"][1]
        res["por_sensor"][bk] = {
            "banda": d["banda"], "fila_atbd": d["fila_atbd"],
            "area_nadir_km2": round(a0, 4), "area_borde_km2": round(a1, 4),
            "crecimiento_eje_track": round(g_tr, 2),
            "crecimiento_eje_scan": round(g_sc, 2),
            "crecimiento_AREA": round(a1 / a0, 2),
        }
        print(f"{bk:9s} {a0:10.4f} {a1:10.4f} {g_tr:9.2f} {g_sc:9.2f} {a1/a0:8.2f}")

    print()
    print("Contraste con lo que los datos piden (factor_requerido.json):")
    print(f"  {'sensor':9s} {'bin':8s} {'zen_med':>8s} {'requerido':>10s} "
          f"{'disponible al borde':>20s}")
    for bk in ("v375", "v750"):
        bins = (req.get("por_sensor") or {}).get(bk) or {}
        if not bins:
            continue
        disp = res["por_sensor"][bk]["crecimiento_AREA"]
        peor = max(bins.items(), key=lambda kv: kv[1]["f_requerido"])
        for b, d in bins.items():
            marca = "  <-- el mas exigente" if b == peor[0] else ""
            print(f"  {bk:9s} {b:8s} {d['zen_mediano_deg']:8.1f} "
                  f"{d['f_requerido']:10.2f} {disp:20.2f}{marca}")
        res["por_sensor"][bk]["requerido_maximo"] = {
            "bin": peor[0], "zen_mediano_deg": peor[1]["zen_mediano_deg"],
            "f_requerido": peor[1]["f_requerido"],
            "cabe_en_lo_disponible": peor[1]["f_requerido"] <= disp}

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print()
    print("El requerido se evalua en el cenital MEDIANO del bin; el disponible es el")
    print("del BORDE del swath (cenital ~70 deg). Que el requerido entre por debajo")
    print("del disponible es condicion necesaria, no prueba: la ley por angulo tiene")
    print("los saltos de las zonas de agregacion (3x1 -> 2x1 en 31.589 deg de scan,")
    print("2x1 -> 1x1 en 44.680 deg) y hay que tomarla del ATBD, no interpolarla.")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
