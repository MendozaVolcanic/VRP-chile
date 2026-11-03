"""S172: grillas de MIROVA para los 34 volcanes de volcanoes.yaml que no están en el NRT (sombra de los 34).

POR QUÉ. Las tres vías «código MIROVA» (pipeline/mirova_v750_codigo.py) interpolan cada gránulo a la grilla UTM fija
que MIROVA usa para el volcán; sin grilla la vía no corre y el procesador cae a K (`via_codigo_mirova: "sin_grilla"`).
Para los 11 Tier A la grilla salió de los GeoTIFF UTM de MIROVA (14 y 15 de septiembre de 2026). Para los 34 no hay
TIF: MIROVA no los vigila en su NRT (plan docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md, H2). Decisión de
Nicolás (2026-11-02, chat de la coordinadora S172): adelantar la sombra de los 34 con las vías encendidas.

LA REGLA (cabecera de pipeline/grillas_mirova.yaml, regla GEO de S159): centros de celda en X0 - 25000 : paso :
X0 + 25000, con (X0, Y0) el punto de referencia del volcán en UTM. En 8 de los 11 ese punto es el lat/lon de
volcanoes.yaml (a ~1 m, redondeo del TIF); en Lascar, PlanchonPeteroa y Tupungatito MIROVA usa otro punto, de
coordenadas redondas, a 233, 1.885 y 2.787 m del yaml (INFORME GEO de S159, punto 2). Esos tres puntos no se pueden
adivinar para un volcán sin TIF (no hay una regla que los produzca: no son el mirova_center del KML, que también
difiere), así que para los 34 se usa la regla de la mayoría: (X0, Y0) = UTM del lat/lon del yaml. Si algún día MIROVA
publica un TIF de uno de los 34, su punto real reemplaza a éste (A5: el dato de MIROVA manda).

  - Zona UTM: la estándar por longitud (zona 18 al oeste de 72° O, 19 al este), hemisferio sur: EPSG 32718 o 32719.
    Es la que usan los 11 (Chaiten y PuyehueCordonCaulle, al oeste de 72° O, en 32718; los demás en 32719).
  - X0, Y0 redondeados a 0,1 m, como los 11.
  - centro_lat, centro_lon: en los 11 es el centro en grados que trae el TIF (a ~60 m del yaml) y sólo se usa para el
    recorte de 45 km antes de interpolar y para el corte de 5 km al centro de MODIS y VIIRS 375. Sin TIF, el lat/lon
    del yaml a 5 decimales.
  - roi_v750: "def", como los 11 hasta que V750-B decida otra cosa.

CONTROL (se imprime y lo repite tests/test_sombra_34_s172.py): aplicada a los 8 Tier A cuyo punto es el del yaml, la
regla reproduce sus (X0, Y0) de grillas_mirova.yaml a menos de 1,5 m.

Uso:
  python experiments/_s172_sombra34/generar_grillas_34.py              # imprime el bloque y el control
  python experiments/_s172_sombra34/generar_grillas_34.py --escribir   # además lo agrega al final de la grilla
--escribir se niega si alguno de los 34 ya está en el archivo y nunca reescribe lo que había: sólo agrega al final.
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import yaml
from pyproj import Transformer

REPO = Path(__file__).resolve().parents[2]
VOLCANES_YAML = REPO / "volcanoes.yaml"
GRILLAS_YAML = REPO / "pipeline" / "grillas_mirova.yaml"
# Los tres de los 11 cuyo punto de MIROVA no es el del yaml (cabecera de grillas_mirova.yaml)
REFERENCIA_DISTINTA = ("Lascar", "PlanchonPeteroa", "Tupungatito")
TOL_CONTROL_M = 1.5

CABECERA_BLOQUE = """\
# S172, sombra de los 34 (experiments/_s172_sombra34/generar_grillas_34.py; decisión de Nicolás del 2026-11-02).
# Estos 34 NO tienen TIF de MIROVA: (X0, Y0) es el UTM del lat/lon de volcanoes.yaml (la regla de 8 de los 11),
# zona estándar por longitud; centro_lat/lon es el mismo lat/lon del yaml. Si MIROVA llegara a publicar un TIF de
# alguno, su punto real reemplaza a éste (A5).
"""


def zona_epsg(lon):
    """EPSG UTM sur por la zona estándar de la longitud (6° por zona, la 1 empieza en 180° O)."""
    zona = int((float(lon) + 180.0) // 6.0) + 1
    return 32700 + zona


def punto_utm(lat, lon, epsg):
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    x, y = t.transform(float(lon), float(lat))
    return x, y


def entrada(v):
    epsg = zona_epsg(v["lon"])
    x, y = punto_utm(v["lat"], v["lon"], epsg)
    return {"epsg": epsg, "x0": round(x, 1), "y0": round(y, 1),
            "centro_lat": round(float(v["lat"]), 5), "centro_lon": round(float(v["lon"]), 5), "roi_v750": "def"}


def linea(nombre, e):
    return (f"  {nombre + ':':<20s} {{epsg: {e['epsg']}, x0: {e['x0']:.1f}, y0: {e['y0']:.1f}, "
            f"centro_lat: {e['centro_lat']:.5f}, centro_lon: {e['centro_lon']:.5f}, roi_v750: {e['roi_v750']}}}")


def los_34(volcanes, grillas):
    """Los volcanes activos de volcanoes.yaml sin grilla, en el orden del yaml."""
    return [v for v in volcanes if v.get("active", True) and v["name"] not in grillas]


def control_8(volcanes, grillas):
    """Para los Tier A cuyo punto es el del yaml: (nombre, dx, dy, epsg_igual) de la regla contra el archivo."""
    porn = {v["name"]: v for v in volcanes}
    out = []
    for nombre, r in grillas.items():
        if nombre in REFERENCIA_DISTINTA:
            continue
        e = entrada(porn[nombre])
        out.append((nombre, e["x0"] - float(r["x0"]), e["y0"] - float(r["y0"]), e["epsg"] == int(r["epsg"])))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--escribir", action="store_true")
    a = ap.parse_args(argv)
    volcanes = yaml.safe_load(VOLCANES_YAML.read_text(encoding="utf-8"))["volcanoes"]
    texto = GRILLAS_YAML.read_text(encoding="utf-8")
    grillas = yaml.safe_load(texto)["volcanes"]

    print(f"volcanoes.yaml: {len(volcanes)} volcanes; con grilla: {len(grillas)}")
    ctl = control_8(volcanes, grillas)
    print(f"\nControl: la regla aplicada a los {len(ctl)} Tier A con punto del yaml (tolerancia {TOL_CONTROL_M} m)")
    ok = True
    for nombre, dx, dy, eq in ctl:
        bien = eq and abs(dx) <= TOL_CONTROL_M and abs(dy) <= TOL_CONTROL_M
        ok &= bien
        print(f"  {nombre:20s} dx={dx:+6.1f} m  dy={dy:+6.1f} m  epsg {'igual' if eq else 'DISTINTO'}  "
              f"{'OK' if bien else 'FALLA'}")
    if len(ctl) != 8 or not ok:
        print("CONTROL FALLA: la regla no reproduce a los 8; no se genera nada", file=sys.stderr)
        return 1

    nuevos = los_34(volcanes, grillas)
    print(f"\nVolcanes sin grilla: {len(nuevos)}")
    if len(nuevos) != 34:
        print(f"ERROR: se esperaban 34 y son {len(nuevos)}", file=sys.stderr)
        return 1
    zonas = {}
    lineas = []
    for v in nuevos:
        e = entrada(v)
        zonas[e["epsg"]] = zonas.get(e["epsg"], 0) + 1
        lineas.append(linea(v["name"], e))
    print("Por zona: " + ", ".join(f"EPSG {k}: {n}" for k, n in sorted(zonas.items())))
    bloque = CABECERA_BLOQUE + "\n".join(lineas) + "\n"
    print("\nBloque:\n" + bloque)

    if a.escribir:
        presentes = [v["name"] for v in nuevos if f"\n  {v['name']}:" in texto]
        if presentes:
            print(f"ERROR: ya están en el archivo: {presentes}", file=sys.stderr)
            return 1
        if not texto.endswith("\n"):
            print("ERROR: el archivo no termina en salto de línea; no se agrega nada", file=sys.stderr)
            return 1
        nuevo = texto + bloque
        assert nuevo.startswith(texto)
        chequeo = yaml.safe_load(nuevo)["volcanes"]
        assert len(chequeo) == len(grillas) + 34
        assert all(chequeo[k] == grillas[k] for k in grillas)
        with open(GRILLAS_YAML, "w", encoding="utf-8", newline="\n") as f:
            f.write(nuevo)
        print(f"Agregadas {len(nuevos)} entradas al final de {GRILLAS_YAML}")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main())
