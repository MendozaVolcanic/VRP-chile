"""Extrae mirova_center_lat/lon desde KMZ oficiales MIROVA.

S80 — corrección del gap detectado en auditoría post-pérdida-contexto.
Solo 2/11 volcanes Tier A tenían `mirova_center` documentado (PP, Tupungatito).
Los otros 9 usaban el vent como fallback, con riesgo de sesgo 1-5 km en
clasificación summit/scene y R2 manual contra MIROVA web.

Los KMZ son zips conteniendo un .kml con tag <GroundOverlay>/<LatLonBox>
que define el footprint UTM 51×51 km (~0.45° lat × 0.55° lon en Chile).
El centro de ese bbox ES el centro MIROVA.

Uso:
    python scripts/extract_mirova_centers_from_kmz.py [--dry-run]

Output:
    - Stdout: tabla volcán | mirova_center_lat | mirova_center_lon | offset_km vs vent
    - Si no --dry-run: actualiza `volcanoes.yaml` con campos mirova_center_*
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import zipfile
from pathlib import Path

import yaml

# stdout Windows default cp1252 no imprime Unicode (regla encoding del proyecto);
# reconfigure no re-envuelve el stream (patrón S118 analyze.py).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

KMZ_DIR = Path(__file__).resolve().parent.parent / "kmz"
VOLCANOES_YAML = Path(__file__).resolve().parent.parent / "volcanoes.yaml"

# Mapping KMZ filename → key en volcanoes.yaml
# Preferimos VIIRS375 KMZ cuando hay (más resolución); fallback VIIRS750 o MODIS.
KMZ_PRIORITY = ["VIIRS375", "VIIRS750", "MODIS"]

VOLCANO_KMZ_MAP = {
    "Chaiten": ["Chaiten_VIIRS750_Last_GE.kmz"],
    "NevadosDeChillan": ["ChillanNevadosde_VIIRS750_Last_GE.kmz"],
    "Copahue": [
        "Copahue_VIIRS375_Last_GE.kmz",
        "Copahue_VIIRS750_Last_GE.kmz",
        "Copahue_MODIS_Last_GE.kmz",
    ],
    "Isluga": ["Isluga_VIIRS750_Last_GE.kmz"],
    "Lascar": [
        "Lascar_VIIRS375_Last_GE.kmz",
        "Lascar_VIIRS750_Last_GE.kmz",
        "Lascar_MODIS_Last_GE.kmz",
    ],
    "Lastarria": ["Lastarria_VIIRS375_Last_GE.kmz"],
    "Llaima": ["Llaima_VIIRS375_Last_GE.kmz"],
    "PlanchonPeteroa": ["PlanchonPeteroa_VIIRS375_Last_GE.kmz"],
    "PuyehueCordonCaulle": ["PuyehueCordonCaulle_VIIRS375_Last_GE.kmz"],
    "Tupungatito": ["Tupungatito_VIIRS750_Last_GE.kmz"],
    "Villarrica": ["Villarrica_VIIRS750_Last_GE.kmz"],
}


def parse_latlonbox(kml_text: str) -> tuple[float, float, float, float] | None:
    """Extrae north/south/east/west de <LatLonBox> del KML."""
    n = re.search(r"<north>([\-\d\.]+)</north>", kml_text)
    s = re.search(r"<south>([\-\d\.]+)</south>", kml_text)
    e = re.search(r"<east>([\-\d\.]+)</east>", kml_text)
    w = re.search(r"<west>([\-\d\.]+)</west>", kml_text)
    if not all([n, s, e, w]):
        return None
    return float(n.group(1)), float(s.group(1)), float(e.group(1)), float(w.group(1))


def kmz_center(kmz_path: Path) -> tuple[float, float] | None:
    """Lee KMZ, parsea .kml interno, devuelve (lat_center, lon_center)."""
    with zipfile.ZipFile(kmz_path, "r") as z:
        kml_names = [n for n in z.namelist() if n.endswith(".kml")]
        if not kml_names:
            return None
        kml_text = z.read(kml_names[0]).decode("utf-8", errors="replace")
    box = parse_latlonbox(kml_text)
    if not box:
        return None
    n, s, e, w = box
    return (n + s) / 2.0, (e + w) / 2.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Solo imprimir tabla, no escribir yaml")
    args = parser.parse_args()

    with open(VOLCANOES_YAML, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    # Estructura: {volcanoes: [{name, lat, lon, ...}, ...]}
    volcs_list = raw["volcanoes"]
    volcs = {item["name"]: item for item in volcs_list}

    results = []
    for vname, kmz_candidates in VOLCANO_KMZ_MAP.items():
        kmz_path = None
        for cand in kmz_candidates:
            p = KMZ_DIR / cand
            if p.exists():
                kmz_path = p
                break
        if not kmz_path:
            print(f"SKIP {vname}: no KMZ encontrado", file=sys.stderr)
            continue

        center = kmz_center(kmz_path)
        if not center:
            print(f"SKIP {vname}: KMZ sin LatLonBox parseable ({kmz_path.name})", file=sys.stderr)
            continue

        lat_c, lon_c = center
        # vent desde volcanoes.yaml
        vent_lat = volcs[vname]["lat"]
        vent_lon = volcs[vname]["lon"]
        offset_km = haversine_km(vent_lat, vent_lon, lat_c, lon_c)
        # bearing (N=0°, E=90°)
        dlat = lat_c - vent_lat
        dlon = lon_c - vent_lon
        bearing = math.degrees(math.atan2(dlon, dlat)) % 360
        bearing_str = (
            "N" if bearing < 22.5 or bearing >= 337.5 else
            "NE" if bearing < 67.5 else
            "E" if bearing < 112.5 else
            "SE" if bearing < 157.5 else
            "S" if bearing < 202.5 else
            "SW" if bearing < 247.5 else
            "W" if bearing < 292.5 else "NW"
        )

        results.append({
            "volcano": vname,
            "kmz": kmz_path.name,
            "mirova_center_lat": lat_c,
            "mirova_center_lon": lon_c,
            "vent_lat": vent_lat,
            "vent_lon": vent_lon,
            "offset_km": offset_km,
            "bearing": bearing_str,
            "existing_center_lat": volcs[vname].get("mirova_center_lat"),
            "existing_center_lon": volcs[vname].get("mirova_center_lon"),
        })

    # Reporte
    print(f"\n{'Volcán':<22} {'lat_c':>10} {'lon_c':>10} {'offset':>7} {'dir':>3}  KMZ")
    print("-" * 80)
    for r in results:
        existing = ""
        if r["existing_center_lat"] is not None:
            existing = f"  [previo: {r['existing_center_lat']:.4f},{r['existing_center_lon']:.4f}]"
        print(
            f"{r['volcano']:<22} {r['mirova_center_lat']:>10.5f} {r['mirova_center_lon']:>10.5f} "
            f"{r['offset_km']:>6.2f}km {r['bearing']:>3}  {r['kmz']}{existing}"
        )

    if args.dry_run:
        print("\n--dry-run: NO se escribió volcanoes.yaml", file=sys.stderr)
        return 0

    # Update yaml (using Edit pattern via simple in-place file modification of specific keys
    # to avoid yaml.safe_dump destroying comments — convention A en CLAUDE.md proyecto).
    yaml_text = VOLCANOES_YAML.read_text(encoding="utf-8")
    updates_applied = 0
    for r in results:
        vname = r["volcano"]
        lat_c = r["mirova_center_lat"]
        lon_c = r["mirova_center_lon"]
        # Si ya existe campo mirova_center_lat, skip (no sobrescribir manual)
        if r["existing_center_lat"] is not None:
            print(f"  KEEP {vname}: mirova_center_lat ya documentado, NO sobrescribo")
            continue
        # Localizar bloque del volcán (formato yaml lista: `- name: Volcano`).
        # Insertar mirova_center_lat/lon después de la primera línea `  lon: XX`
        # dentro de ese bloque.
        pattern = re.compile(
            r"(- name:\s*" + re.escape(vname) + r"\s*\n(?:\s{2,}.*\n)*?\s+lon:\s+[\-\d\.]+\n)",
            re.MULTILINE,
        )
        match = pattern.search(yaml_text)
        if not match:
            print(f"  WARN {vname}: no se localizó bloque en yaml, skip")
            continue
        # Detectar indentación
        block = match.group(1)
        indent_match = re.search(r"^(\s+)lon:", block, re.MULTILINE)
        indent = indent_match.group(1) if indent_match else "  "
        insertion = (
            f"{indent}# mirova_center extraído de kmz/{r['kmz']} GroundOverlay LatLonBox (S80)\n"
            f"{indent}mirova_center_lat: {lat_c:.5f}\n"
            f"{indent}mirova_center_lon: {lon_c:.5f}\n"
        )
        yaml_text = yaml_text[:match.end()] + insertion + yaml_text[match.end():]
        updates_applied += 1
        print(f"  ADD  {vname}: mirova_center_lat={lat_c:.5f}, lon={lon_c:.5f}")

    if updates_applied > 0:
        VOLCANOES_YAML.write_text(yaml_text, encoding="utf-8")
        print(f"\n{updates_applied} volcanes actualizados en {VOLCANOES_YAML}")
    else:
        print("\nNada que actualizar.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
