"""Reproduce los numeros de la decision 9 de docs/AUDIT_S175.md (truncado del VRP: OCR vs tabla).

Insumos (solo lectura):
  latest_consolidado_base.csv  (copia del orquestador, sha256 dee76837..., fuera del repo)
  ocr_base.csv                 (git show 752d348bc:data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv)
Afirmaciones a reproducir:
  tabla: 141 de 142 alertas MODIS traen decimales
  OCR:   48 alertas MODIS y 95 VIIRS 750 enteras; VIIRS 375 896 de 897 con decimales
  Chillan MODIS 2026-10-30 08:55: tabla 14,39, OCR 14,0; 2026-10-30 07:15 (1,0 MW) solo en el OCR
"""
import csv, sys, collections

LATEST = r"C:\Users\nmend\vrp-temporales\s175_audit\insumos\latest_consolidado_base.csv"
OCR = r"C:\Users\nmend\vrp-temporales\s175_verpr\955\ocr_base.csv"


def leer(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def vrp(row):
    s = (row.get("VRP_MW") or "").strip().replace(",", ".")
    try:
        return float(s), s
    except ValueError:
        return None, s


def tiene_decimales(s):
    s = s.replace(",", ".")
    return "." in s and not s.endswith(".0") and s.split(".")[1].strip("0") != ""


def sensor_clase(sensor):
    # Convencion del scraper Mirova-v1: "VIIRS" = banda M (750 m); "VIIRS375" = banda I (375 m)
    s = (sensor or "").strip().upper()
    if s == "MODIS":
        return "MODIS"
    if s == "VIIRS":
        return "VIIRS750"
    if s == "VIIRS375":
        return "VIIRS375"
    return "OTRO:" + s


TIER_A = ("lascar", "lastarria", "isluga", "chill", "llaima", "villarrica", "chaiten", "tupungatito",
          "planch", "copahue", "puyehue")


def contar(rows, filtro, etiqueta):
    por_sensor = collections.defaultdict(lambda: [0, 0])  # [con decimales, total]
    for r in rows:
        if not filtro(r):
            continue
        v, s = vrp(r)
        if v is None or v <= 0:
            continue
        sc = sensor_clase(r.get("Sensor"))
        por_sensor[sc][1] += 1
        por_sensor[sc][0] += tiene_decimales(s)
    print(f"  [{etiqueta}] con decimales / total (enteras):")
    for k in sorted(por_sensor):
        d, t = por_sensor[k]
        print(f"    {k:10s} {d:5d} / {t:5d}   enteras {t-d}")


for nombre, path in (("TABLA latest_consolidado", LATEST), ("OCR registro_vrp_ocr", OCR)):
    rows = leer(path)
    print(f"\n=== {nombre}: {len(rows)} filas")
    print("  Tipo_Registro:", collections.Counter(r.get("Tipo_Registro") for r in rows).most_common(8))
    print("  Sensor:", collections.Counter(r.get("Sensor") for r in rows).most_common(12))
    contar(rows, lambda r: True, "VRP_MW > 0, sin filtro")
    contar(rows, lambda r: (r.get("Tipo_Registro") or "").startswith("ALERTA_TERMICA"),
           "Tipo_Registro ALERTA_TERMICA*")
    for desde in ("2026-03-01", "2026-06-11", "2026-09-01"):
        contar(rows, lambda r, d=desde: (r.get("Tipo_Registro") or "").startswith("ALERTA_TERMICA")
               and (r.get("Fecha_Satelite_UTC") or "") >= d, f"ALERTA_TERMICA* y fecha >= {desde}")
    contar(rows, lambda r: (r.get("Tipo_Registro") or "").startswith("ALERTA_TERMICA")
           and any(t in (r.get("Volcan") or "").lower() for t in TIER_A), "ALERTA_TERMICA* y 11 Tier A")
    contar(rows, lambda r: (r.get("Tipo_Registro") or "").startswith("ALERTA_TERMICA")
           and any(t in (r.get("Volcan") or "").lower() for t in TIER_A)
           and (r.get("Fecha_Satelite_UTC") or "") >= "2026-03-01", "ALERTA_TERMICA*, Tier A, >= 2026-03-01")
    contar(rows, lambda r: (r.get("Tipo_Registro") or "").startswith("ALERTA_TERMICA")
           and (r.get("Fecha_Satelite_UTC") or "")[11:13] in ("00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11"),
           "ALERTA_TERMICA* y hora UTC < 12 (nocturnas aprox.)")
    # caso Chillan MODIS 2026-10-30
    print("  Chillan MODIS 2026-10-30:")
    for r in rows:
        if "chill" in (r.get("Volcan") or "").lower() and "MODIS" in (r.get("Sensor") or "").upper() \
                and (r.get("Fecha_Satelite_UTC") or "").startswith("2026-10-30"):
            print("   ", r.get("Fecha_Satelite_UTC"), r.get("Sensor"), "VRP_MW=", r.get("VRP_MW"),
                  "Clas=", r.get("Clasificacion Mirova"), "Tipo=", r.get("Tipo_Registro"))
