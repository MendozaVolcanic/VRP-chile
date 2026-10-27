# -*- coding: utf-8 -*-
"""Verificador S164, A7: mutaciones que el PR NO incluyo, corridas sobre la COPIA de HEAD en el scratchpad (nunca sobre
el repo). Reusa el clasificador de experiments/_s164_modis_codigo/mutaciones.py de esa copia (atrapada solo por
AssertionError; caida = solo excepciones; viva = todo pasa).

Pregunta: hay mutaciones obvias del codigo nuevo que ninguna prueba vigila?
Uso: python mutaciones_extra.py <raiz_de_la_copia>
"""
import importlib.util
import sys
from pathlib import Path

COPIA = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("mut", COPIA / "experiments/_s164_modis_codigo/mutaciones.py")
mut = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mut)
assert mut.REPO == COPIA, (mut.REPO, COPIA)
MOD, PM = mut.MOD, mut.PM
STORE = "pipeline/store.py"

EXTRA = [
    ("control_sin_mutacion", None, None, None, "viva"),
    ("pm_via_none_cae_a_k_en_silencio", PM,
     "                if _rec is None:\n                    return None\n                _rec.update({\"granule\": hdf_path.name,",
     "                if _rec is None:\n                    pass\n                else:\n                  _rec.update({\"granule\": hdf_path.name,",
     "?"),
    ("dayflag_invertido", MOD, '    dayflag = 0 if geom.get("solar_zenith", 180.0) > 90 else 1',
     '    dayflag = 1 if geom.get("solar_zenith", 180.0) > 90 else 0', "?"),
    ("radio_recorte_30_km", MOD, "RADIO_RECORTE_KM = 45.0", "RADIO_RECORTE_KM = 30.0", "?"),
    ("remuestreo_nearest", MOD, 'method="linear"))', 'method="nearest"))', "?"),
    ("minimo_100_pixeles_roto", MOD, "    if sel.sum() < 100:", "    if sel.sum() < 100000:", "?"),
    ("coef_v750_en_procesar_grilla", MOD, '    coef = cfg["coef"] if coef is None else coef',
     "    coef = COEF_VRP_V750 if coef is None else coef", "?"),
    ("store_truthy_en_vez_de_is_true", STORE, '    _via_mirova = record.get("via_codigo_mirova") is True',
     '    _via_mirova = bool(record.get("via_codigo_mirova"))', "?"),
    ("sensor_terra_aqua_invertido", PM, '    return "MODIS_TERRA" if "MOD0" in filename else "MODIS_AQUA"',
     '    return "MODIS_AQUA" if "MOD0" in filename else "MODIS_TERRA"', "?"),
    ("sunglint_sin_azimut", MOD, "    sg = sunglint_deg(geom.get(\"sensor_zenith\", 0.0), geom.get(\"solar_zenith\", 0.0),\n                      geom.get(\"sensor_azimuth\", 0.0), geom.get(\"solar_azimuth\", 0.0))",
     "    sg = sunglint_deg(geom.get(\"sensor_zenith\", 0.0), geom.get(\"solar_zenith\", 0.0), 0.0, 0.0)", "?"),
    ("distance_class_siempre_summit", MOD, '    dc = None if inner_km is None else ("summit" if dcen <= inner_km else "far")',
     '    dc = None if inner_km is None else "summit"', "?"),
]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    archivos = sorted({a for _, a, _, _, _ in EXTRA if a})
    originales = {a: (COPIA / a).read_bytes() for a in archivos}
    try:
        for nombre, arch, a, b, esperado in EXTRA:
            if arch is not None:
                s = originales[arch].decode("utf-8")
                if s.count(a) != 1:
                    print(f"{nombre:34s} TEXTO ORIGINAL aparece {s.count(a)} veces: mutacion no aplicable", flush=True)
                    continue
                (COPIA / arch).write_bytes(s.replace(a, b).encode("utf-8"))
            try:
                clase, asc, exc = mut.correr(nombre)
            finally:
                for k, v in originales.items():
                    (COPIA / k).write_bytes(v)
            print(f"{nombre:34s} esperado={esperado:5s} resultado={clase:9s}", flush=True)
            for q in (asc[:3] + exc[:2]):
                print("    ", q, flush=True)
    finally:
        for k, v in originales.items():
            (COPIA / k).write_bytes(v)


if __name__ == "__main__":
    main()
