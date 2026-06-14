"""S108 — Clasificación del destape del FLIP ancla MODIS por cruce CROSS-SENSOR.

El probe_modis_destape mostró ~2476 flips far->summit; ~1600 son pc.vrp<=5 SIN MIROVA.
Pregunta para el veredicto del flip §1: ¿esos ~1600 son señal REAL (cat-b A54) o RUIDO?

Prueba decisiva CROSS-SENSOR: MIROVA casi no publica MODIS (solo Lascar) pero SÍ publica
VIIRS para estos vols. Si en la MISMA noche que el MODIS se destapa far->summit, NUESTRO
VIIRS (375/750) detectó summit (eqVrp-equiv: distance_class=summit, pc.vrp>0) Y MIROVA
publicó VIIRS esa noche -> el foco es REAL (confirmado por el sensor que MIROVA sí ve) ->
el MODIS destapado es cat-b real. Si no hay ni VIIRS-nuestro ni MIROVA-VIIRS -> candidato
a ruido MODIS.

Caveat A18: ancla simulada offline (sobre-estima vs reproc real).

Uso: python experiments/_s107_modis_localmag/classify_destape_modis.py
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Tupungatito",
        "Chaiten", "Copahue", "NevadosDeChillan", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]
INNER = {"Lastarria": 3, "PlanchonPeteroa": 3, "Copahue": 4, "Lascar": 5,
         "Isluga": 5, "NevadosDeChillan": 5, "Llaima": 5, "Villarrica": 5,
         "Chaiten": 5, "Tupungatito": 7, "PuyehueCordonCaulle": 20}


def load(vol):
    obj = json.load(open(ROOT / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))
    return obj.get("records", obj)


def is_modis(r):
    return str(r.get("sensor", "")).startswith("MODIS")


def is_viirs(r):
    return str(r.get("sensor", "")).startswith("VIIRS")


def alert_nights(vol):
    out = set()
    for row in csv.DictReader(open(ROOT / "latest_consolidado.csv", encoding="utf-8", errors="replace")):
        if row.get("Volcan") == vol and str(row.get("Tipo_Registro", "")).startswith("ALERTA_TERMICA"):
            out.add((row.get("Fecha_Satelite_UTC") or "")[:10])
    return out


def main():
    print(f"{'vol':<20}{'destape':>8}{'pcv>5':>7}{'MIROVA':>7}{'VIIRS_ours':>11}"
          f"{'real(cross)':>12}{'ruido?':>8}")
    G = defaultdict(int)
    for vol in VOLS:
        recs = load(vol)
        inner = INNER[vol]
        nights = alert_nights(vol)
        # noches donde NUESTRO VIIRS vio summit (pc.vrp>0, distance_class=summit)
        viirs_summit_nights = set()
        for r in recs:
            if is_viirs(r) and r.get("distance_class") == "summit":
                pc = r.get("primary_cluster") or {}
                if (pc.get("vrp_mw") or 0) > 0:
                    viirs_summit_nights.add((r.get("datetime_utc") or "")[:10])
        destape = pcv5 = mir = vrs = real = ruido = 0
        for r in recs:
            if not is_modis(r):
                continue
            if r.get("distance_class") != "far":
                continue
            pc = r.get("primary_cluster") or {}
            src = r.get("final_hotspot_source")
            if src == "test1" or (r.get("triggered_test1") and not (r.get("anomaly_pixels") or [])):
                nd = 0.0
            elif pc.get("centroid_dist_km") is not None:
                nd = pc["centroid_dist_km"]
            else:
                nd = r.get("final_hotspot_dist_km")
            if nd is None or nd > inner:
                continue  # no se destapa (cluster lejos o sin pos)
            destape += 1
            nightd = (r.get("datetime_utc") or "")[:10]
            pcv = pc.get("vrp_mw") or 0
            has_mir = nightd in nights
            has_vrs = nightd in viirs_summit_nights
            if pcv > 5:
                pcv5 += 1
            if has_mir:
                mir += 1
            if has_vrs:
                vrs += 1
            # "real" = confirmado por el sensor que MIROVA sí ve (VIIRS nuestro summit
            # esa noche) o MIROVA publicó esa noche
            if has_mir or has_vrs:
                real += 1
            elif pcv <= 5:
                ruido += 1  # sin confirmación cross-sensor ni MIROVA, débil
        for k, v in [("destape", destape), ("pcv5", pcv5), ("mir", mir), ("vrs", vrs),
                     ("real", real), ("ruido", ruido)]:
            G[k] += v
        print(f"{vol:<20}{destape:>8}{pcv5:>7}{mir:>7}{vrs:>11}{real:>12}{ruido:>8}")
    print(f"\nTOTAL destape={G['destape']} | pc.vrp>5(landmine §2)={G['pcv5']} | "
          f"MIROVA={G['mir']} | VIIRS_ours_summit={G['vrs']} | "
          f"REAL(cross-confirmado)={G['real']} ({100*G['real']//max(G['destape'],1)}%) | "
          f"candidato-ruido={G['ruido']} ({100*G['ruido']//max(G['destape'],1)}%)")
    print("Lectura: 'real' = el flip recupera señal confirmada por VIIRS/MIROVA (cat-b, "
          "valor A54). 'ruido' = MODIS far->summit sin confirmación cross-sensor (revisar "
          "si el flip §1 los infla). A18: offline sobre-estima el destape.")


if __name__ == "__main__":
    main()
