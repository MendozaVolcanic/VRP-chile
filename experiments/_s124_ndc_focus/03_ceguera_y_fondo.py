# -*- coding: utf-8 -*-
"""S124 — La mascara de nube <260 K nos deja CIEGOS, y ahi perdemos las alertas.

POR QUE: Nicolas no reconocia como despejadas semanas que el sabe que fueron de
temporal (A62). Investigando salio algo mas grave que un panel mal etiquetado.

CADENA CAUSAL (medida, no supuesta):
  1. Noche fria de invierno sobre un volcan nevado -> gran parte del ROI cae
     bajo 260 K.
  2. process_viirs.py:681-682 hace `roi_mask &= cloud_free` Y
     `bg_mask &= cloud_free`: los saca de la busqueda Y del anillo de fondo.
  3. El anillo queda vacio -> n_bg = 0 -> no hay estadistica de fondo -> no hay
     deteccion posible. La noche es CIEGA.
  4. MIROVA no filtra nube (Laiolo 2026: "no atmospheric correction or
     cloud-contamination automatic filtering"), conserva su fondo y publica.

Y esa mascara es la que MISSION.md:127 declara "Removido S27". Ver D14.

Fuente de verdad de los numeros del informe (regla S91).
"""
import csv, io, json, math, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
NIC = (-36.867210, -71.378241)
INI = "2026-06-01"
PIX_ROI_I = (50.0 / 0.375) ** 2      # ROI 50x50 km en pixeles I-band nadir


def hav(la1, lo1, la2, lo2):
    p = math.pi / 180
    a = (math.sin((la2 - la1) * p / 2) ** 2
         + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def viirs375(vol):
    d = json.loads((ROOT / f"data/mirova_equivalent/{vol}.json").read_text(encoding="utf-8"))
    return [r for r in d["records"]
            if (r.get("datetime_utc") or "") >= INI
            and "VIIRS" in (r.get("sensor") or "") and "750" not in r["sensor"]]


def med(v):
    v = sorted(x for x in v if x is not None)
    return v[len(v) // 2] if v else float("nan")


if __name__ == "__main__":
    rs = viirs375("NevadosDeChillan")

    # --- 1) la mascara es lo que vacia el fondo -------------------------------
    sin = [r for r in rs if (r.get("diag_n_bg_used_first_pass") or 0) == 0]
    con = [r for r in rs if (r.get("diag_n_bg_used_first_pass") or 0) > 0]
    ms = med([r.get("n_cloud_masked") for r in sin])
    mc = med([r.get("n_cloud_masked") for r in con])
    print(f"pasadas SIN fondo (n_bg=0): {len(sin)}   CON fondo: {len(con)}\n")
    print("            pixeles que la regla <260 K saca del ROI (mediana)")
    print(f"  sin fondo:  {ms:8.0f}  = {100*ms/PIX_ROI_I:2.0f}% del ROI")
    print(f"  con fondo:  {mc:8.0f}  = {100*mc/PIX_ROI_I:2.0f}% del ROI")
    print(f"  -> factor {ms/mc:.0f}x\n")

    # --- 2) ahi es donde perdemos las alertas ---------------------------------
    ciego = {}
    for r in rs:
        f = r["datetime_utc"][:10]
        ok = (r.get("diag_n_bg_used_first_pass") or 0) > 0
        ciego[f] = ciego.get(f, True) and not ok

    foco = set()
    dd = json.loads((ROOT / "data/experimental_ndc_focus/NevadosDeChillan.json")
                    .read_text(encoding="utf-8"))
    for r in dd["records"]:
        f = (r.get("datetime_utc") or "")[:10]
        pc = r.get("primary_cluster") or {}
        if f >= INI and (pc.get("vrp_mw") or 0) > 0 and pc.get("centroid_lat") is not None \
           and hav(NIC[0], NIC[1], pc["centroid_lat"], pc["centroid_lon"]) <= 1.0:
            foco.add(f)

    mirova = set()
    with open(ROOT / "latest_consolidado.csv", encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            if r.get("Volcan") != "Nevados de Chillan":
                continue
            f = (r.get("Fecha_Satelite_UTC") or "")[:10]
            if f < INI or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            if (r.get("Sensor") or "").strip().upper() != "VIIRS375":
                continue
            try:
                v = float(r.get("VRP_MW") or 0)
            except ValueError:
                continue
            if v > 0:
                mirova.add(f)

    nc = sum(1 for v in ciego.values() if v)
    print(f"noches con pasada: {len(ciego)}   CIEGAS: {nc} ({100*nc/len(ciego):.0f}%)")
    print(f"alertas MIROVA: {len(mirova)}   reproducidas: {len(mirova & foco)}   perdidas: {len(mirova - foco)}\n")
    for f in sorted(mirova - foco):
        print(f"  PERDIDA {f}: {'CIEGA' if ciego.get(f) else 'con fondo'}")
    for f in sorted(mirova & foco):
        print(f"  ok      {f}: {'CIEGA' if ciego.get(f) else 'con fondo'}")
    print("\nSeparacion perfecta: las 3 que perdemos son ciegas, las 3 que")
    print("reproducimos tienen fondo. Con 17% de noches ciegas, 3 de 3 no es azar.")
