"""F3: la alerta protegida MODIS de Nevados de Chillán del 2026-10-12 (2,18 MW en la referencia) que el
recall K del auto-audit no ve en el cráter. Records nuestros de esa noche (K y sombra C0) y filas MIROVA.
P1/P2: imprime n de records; 0 = SIN DATO."""
import json, os, sys, csv
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for sub in ("mirova_equivalent", "experimental_v2"):
    rs = json.load(open(os.path.join(ROOT, "data", sub, "NevadosDeChillan.json"), encoding="utf-8"))["records"]
    sel = [r for r in rs if r["datetime_utc"].startswith("2026-10-12") and r["sensor"].startswith("MODIS")]
    print(sub, "n", len(sel))
    for r in sel:
        pc = r.get("primary_cluster") or {}
        print("  ", r["datetime_utc"], r["sensor"], "dc", r.get("distance_class"), "pc_vrp", pc.get("vrp_mw"), "pc_dist", pc.get("centroid_dist_km"),
              "npix", pc.get("n_pixels"), "zen", r.get("sensor_zenith_deg"), "sha", ((r.get("regimen") or {}).get("codigo_sha") or "")[:8])
for p in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
    with open(os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot", p), encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if "Chill" in (row.get("Volcan") or "") and (row.get("Fecha_Satelite_UTC") or "").startswith("2026-10-12") and "MODIS" in (row.get("Sensor") or "").upper():
                print(p, {k: row.get(k) for k in ("Fecha_Satelite_UTC", "Sensor", "VRP_MW", "Distancia_km", "Tipo_Registro")})
