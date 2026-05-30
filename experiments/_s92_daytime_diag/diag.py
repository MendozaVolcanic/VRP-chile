"""S92 — Diagnóstico bug #2.1: ¿por qué NdC no tiene escenas MODIS diurnas en el A/B?

Reproducible. Fuente de verdad de los números del FINDINGS S92 (regla §0.5).

Distingue 3 hipótesis:
  H1: las pasadas MODIS diurnas no se descargaron/procesaron (no hay granule diurno).
  H2: _scene_is_day clasifica mal (parse del granule falla -> False).
  H3: el record diurno se procesó pero el gate de store lo rechazó (no está en JSON).

Usa el campo `granule` persistido para reproducir EXACTAMENTE _scene_is_day del
pipeline (parsea nombre del granule + elevación solar con coords del volcán).
"""
import json
import sys
import hashlib
from pathlib import Path

# importable: reusar el código real del pipeline, no reimplementar
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.process_modis import _parse_datetime, _scene_is_day  # noqa: E402

ENABLED = ROOT / "data/_daytime_modis_enabled/NevadosDeChillan.json"
DISABLED = ROOT / "data/_daytime_modis_disabled/NevadosDeChillan.json"

# coords NdC (volcanoes.yaml) — _scene_is_day usa volcano_lat/lon, no las del record
NDC_LAT, NDC_LON = -36.868, -71.378  # se sobreescribe abajo desde volcanoes.yaml


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def load(p):
    return json.load(open(p, encoding="utf-8"))["records"]


def is_modis(r):
    return str(r.get("sensor", "")).startswith("MODIS")


def main():
    # coords reales del volcán desde volcanoes.yaml
    import yaml
    vy = yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))
    vols = vy["volcanoes"] if isinstance(vy, dict) and "volcanoes" in vy else vy
    ndc = next(v for v in (vols.values() if isinstance(vols, dict) else vols)
               if v.get("name", v.get("id", "")).replace(" ", "").lower().startswith("nevadosdechillan")
               or v.get("id", "") == "NevadosDeChillan")
    lat = ndc.get("mirova_center_lat", ndc["lat"])
    lon = ndc.get("mirova_center_lon", ndc["lon"])
    print(f"[coords] NdC lat={lat} lon={lon}")

    print(f"[md5] enabled  = {md5(ENABLED)}")
    print(f"[md5] disabled = {md5(DISABLED)}")
    print(f"[md5] identical = {md5(ENABLED) == md5(DISABLED)}")

    for label, path in [("disabled", DISABLED), ("enabled", ENABLED)]:
        recs = load(path)
        modis = [r for r in recs if is_modis(r)]
        # rango del A/B: 2026-03-01..2026-04-30
        modis_ab = [r for r in modis
                    if "2026-03-01" <= str(r.get("datetime_utc", "")) <= "2026-04-30 23:59"]
        # clasificar por _scene_is_day usando el granule persistido
        day = []
        night = []
        unparsed = []
        for r in modis_ab:
            g = r.get("granule", "")
            iso = _parse_datetime(g)
            if iso == "unknown":
                unparsed.append(r)
                continue
            if _scene_is_day(g, lat, lon):
                day.append(r)
            else:
                night.append(r)
        # distribución de hora UTC de los granules MODIS
        from collections import Counter
        hours = Counter()
        for r in modis_ab:
            iso = _parse_datetime(r.get("granule", ""))
            if iso != "unknown":
                hours[iso[11:13]] += 1
        print(f"\n[{label}] MODIS total={len(modis)} | en rango AB={len(modis_ab)}")
        print(f"[{label}]   _scene_is_day -> day={len(day)} night={len(night)} unparsed={len(unparsed)}")
        print(f"[{label}]   horas UTC granules MODIS (count): {dict(sorted(hours.items()))}")
        # records cerca del evento motivante 2026-03-17
        ev = [r for r in modis_ab if str(r.get("datetime_utc", "")).startswith("2026-03-17")]
        print(f"[{label}]   records MODIS del 2026-03-17: {len(ev)}")
        for r in ev:
            print(f"       {r['datetime_utc']} granule={r.get('granule','')} "
                  f"is_day={_scene_is_day(r.get('granule',''),lat,lon)}")


if __name__ == "__main__":
    main()
