"""S159, pre-registro de MxD03: cuantos GeoTIFF MODIS de MIROVA hay, de que fechas, y en que grilla.

Pregunta: ¿sirven los TIF de MIROVA como vara espacial para MODIS?

Las dos preguntas del instrumento:
1. Si no hubiera ningun TIF MODIS, ¿se veria? Si: el conteo por sensor imprime VIIRS375 y VIIRS750 al lado
   (control positivo: A106 y S144 cuentan TIF VIIRS 375 UTM el 14 y 15 de septiembre).
2. Si el indice estuviera vacio o mal leido, ¿se veria distinto? Si: imprime filas totales, columnas y el
   rango de fechas; un cero con el indice vacio dice «0 filas», no «0 MODIS».

Uso: python tif_modis_cobertura.py RUTA_index.csv [--leer-crs N]
  --leer-crs N baja N TIF MODIS chicos (~20 KB) de fechas repartidas y lee su CRS con rasterio.
Denominador: filas del index.csv de MendozaVolcanic/mirova-tif-archive en el sha que se imprime aparte.
"""
import csv
import collections
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    ruta = Path(sys.argv[1])
    n_leer = int(sys.argv[sys.argv.index("--leer-crs") + 1]) if "--leer-crs" in sys.argv else 0
    filas = list(csv.DictReader(ruta.open(encoding="utf-8")))
    print(f"filas totales: {len(filas)}; columnas: {list(filas[0].keys()) if filas else None}")
    por_sensor = collections.Counter(f["sensor"] for f in filas)
    print("por sensor:", dict(por_sensor))
    modis = [f for f in filas if f["sensor"] == "MODIS"]
    con_adq = [f for f in modis if f["acquisition_utc"]]
    print(f"MODIS: {len(modis)} filas; con acquisition_utc: {len(con_adq)}; "
          f"md5 distintos: {len(set(f['md5'] for f in modis))}")
    fechas = sorted(f["captured_at_utc"][:10] for f in modis)
    if fechas:
        print(f"MODIS captured_at: {fechas[0]} a {fechas[-1]}")
    por_mes = collections.Counter(f["captured_at_utc"][:7] for f in modis)
    print("MODIS por mes de captura:", dict(sorted(por_mes.items())))
    # md5 nuevo por mes (imagen distinta, no repeticion; A106)
    vistos, nuevos = set(), collections.Counter()
    for f in sorted(modis, key=lambda f: f["captured_at_utc"]):
        if f["md5"] not in vistos:
            vistos.add(f["md5"])
            nuevos[f["captured_at_utc"][:7]] += 1
    print("MODIS md5 nuevos por mes:", dict(sorted(nuevos.items())))
    # ventana UTM de A106 (VIIRS 375): 2026-09-14 06:36 a 2026-09-15 06:24
    ventana = [f for f in modis if "2026-09-14" <= (f["acquisition_utc"] or f["last_modified_utc"])[:10] <= "2026-09-15"]
    print(f"MODIS con acquisition o last_modified el 14 o 15-sep: {len(ventana)}")
    for f in ventana[:20]:
        print("  ", f["volcano"], f["acquisition_utc"], f["last_modified_utc"], f["md5"][:8], f["tif_path"])
    # ultimo md5 nuevo (congelamiento del 22-sep, memoria S151)
    ult = max((f for f in modis), key=lambda f: f["captured_at_utc"]) if modis else None
    if ult:
        print("ultima fila MODIS:", ult["captured_at_utc"], ult["volcano"], ult["last_modified_utc"], ult["md5"][:8])
    ult_nuevo = None
    vistos = set()
    for f in sorted(modis, key=lambda f: f["captured_at_utc"]):
        if f["md5"] not in vistos:
            vistos.add(f["md5"]); ult_nuevo = f
    if ult_nuevo:
        print("ultimo md5 MODIS nuevo:", ult_nuevo["captured_at_utc"], ult_nuevo["volcano"], ult_nuevo["last_modified_utc"])

    if n_leer:
        import rasterio
        unicos = {}
        for f in sorted(modis, key=lambda f: f["last_modified_utc"]):
            unicos.setdefault(f["md5"], f)
        lista = list(unicos.values())
        paso = max(1, len(lista) // n_leer)
        tmp = Path(tempfile.mkdtemp(prefix="tif_modis_"))
        for f in lista[::paso][:n_leer]:
            destino = tmp / Path(f["tif_path"]).name
            datos = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                                    f"repos/MendozaVolcanic/mirova-tif-archive/contents/{f['tif_path']}"],
                                   capture_output=True, check=True).stdout
            destino.write_bytes(datos)
            with rasterio.open(destino) as r:
                print(f"  CRS {r.crs} res {r.res} tam {r.width}x{r.height} | {f['volcano']} lm={f['last_modified_utc']} "
                      f"adq={f['acquisition_utc'] or '-'}")


if __name__ == "__main__":
    main()
