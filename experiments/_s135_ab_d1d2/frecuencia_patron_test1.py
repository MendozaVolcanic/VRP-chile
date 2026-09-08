# -*- coding: utf-8 -*-
"""¿Cuántas veces se repite el patrón de Isluga 01-jul? (S135)

EL PATRÓN, encontrado investigando la única pérdida real del brazo fiel:
el Test 1 integrado DISPARA, el primer pase (Tests 2 ∧ 3, contraste contra los 8 vecinos)
entrega CERO píxeles, y lo único que sostiene la publicación es `keep_peak` o el segundo pase
corriendo suelto. En esa pasada MIROVA publicaba el cráter y nosotros lo habríamos perdido con
el algoritmo literal.

La investigación declaró como limitación que era **una sola pasada**. Esto la cierra: mide la
frecuencia del patrón sobre la serie operacional, y —lo que importa— **con cuánta frecuencia
MIROVA confirma esas noches**. Si MIROVA confirma seguido, la intersección del Test 1 con la
máscara contextual está tapando detecciones reales de forma sistemática, y la pregunta deja de
ser `keep_peak` sí o no.

DEFINICIONES (A90: cada número con su denominador y su ventana)
  universo      = records V375 (VIIRS_* sin sufijo _750) de los 11 Tier A, desde 2026-06-01.
  test1 solo    = `triggered_test1` Y `diag_n_first_pass_pixels == 0`: el Test 1 disparó y el
                  contraste local no marcó nada. Es el patrón.
  publicado     = `distance_class == "summit"` y el cúmulo primario tiene VRP > 0.
  confirmado    = hay alerta MIROVA V375 (CONS ∪ OCR) de una pasada NOCTURNA esa fecha y volcán.
                  Las diurnas se excluyen con `is_nighttime` (A76), igual que en el evaluador.
  mismo objeto  = la cota |dist_nuestra − dist_MIROVA| <= 0,55 km (A93). Una cota inferior:
                  descarta con seguridad lo distinto, no garantiza identidad.

Read-only. Salida: `frecuencia_patron_test1.json`.
"""
import io
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import yaml  # noqa: E402

from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402
from run_pipeline import is_nighttime  # noqa: E402

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
DESDE = "2026-06-01"
COTA_KM = 0.55
TIER_A = ["Villarrica", "Lascar", "Copahue", "Llaima", "NevadosDeChillan", "Isluga",
          "Lastarria", "Chaiten", "PlanchonPeteroa", "PuyehueCordonCaulle", "Tupungatito"]


def es_v375(r):
    s = r.get("sensor", "")
    return s.startswith("VIIRS") and not s.endswith("_750")


def parse_dt(s):
    for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, f)
        except (ValueError, TypeError):
            pass
    return None


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    cfg = yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))
    coord = {v["name"]: (v["lat"], v["lon"]) for v in cfg["volcanoes"]}

    alertas = load_mirova_alertas(cons_path=os.path.join(SNAP, "registro_vrp_consolidado.csv"),
                                  ocr_path=os.path.join(SNAP, "registro_vrp_ocr.csv"))
    noches_mir, dist_mir, n_diurnas = defaultdict(set), defaultdict(list), 0
    fin_gt = ""
    for a in alertas:
        f = a.get("fecha_utc")
        if not f or a["sensor_bucket"] != "VIIRS375":
            continue
        fin_gt = max(fin_gt, f[:10])
        dt = parse_dt(f)
        vol = a["volcano"]
        if dt is not None and vol in coord and not is_nighttime(*coord[vol], dt):
            n_diurnas += 1
            continue
        noches_mir[vol].add(f[:10])
        if a.get("dist_km") is not None:
            dist_mir[(vol, f[:10])].append(float(a["dist_km"]))

    tot = defaultdict(int)
    por_vol = {}
    ejemplos = []
    for vol in TIER_A:
        p = os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json")
        if not os.path.exists(p):
            continue
        recs = [r for r in json.load(open(p, encoding="utf-8"))["records"]
                if es_v375(r) and r.get("datetime_utc", "") >= DESDE
                and r["datetime_utc"][:10] <= fin_gt]
        c = defaultdict(int)
        for r in recs:
            c["universo"] += 1
            patron = bool(r.get("triggered_test1")) and r.get("diag_n_first_pass_pixels") == 0
            if not patron:
                continue
            c["patron"] += 1
            pc = r.get("primary_cluster") or {}
            publicado = (r.get("distance_class") == "summit" and (pc.get("vrp_mw") or 0) > 0)
            if publicado:
                c["patron_publicado"] += 1
            d = r["datetime_utc"][:10]
            if d in noches_mir.get(vol, set()):
                c["patron_con_alerta"] += 1
                nuestra = pc.get("centroid_dist_km")
                dm = dist_mir.get((vol, d)) or []
                if publicado and nuestra is not None and dm:
                    cota = min(abs(nuestra - x) for x in dm)
                    if cota <= COTA_KM:
                        c["patron_mismo_objeto"] += 1
                        if len(ejemplos) < 8:
                            ejemplos.append({"volcan": vol, "pasada": r["datetime_utc"],
                                             "nuestra_km": nuestra, "mirova_km": dm[0],
                                             "cota_km": round(cota, 3),
                                             "fuente": r.get("final_hotspot_source"),
                                             "n_px": pc.get("n_pixels"),
                                             "recaptura_2p": r.get("diag_n_second_pass_recapture")})
        por_vol[vol] = dict(c)
        for k, v in c.items():
            tot[k] += v

    res = {"ventana": [DESDE, fin_gt], "cota_km": COTA_KM,
           "alertas_diurnas_excluidas": n_diurnas,
           "definiciones": __doc__.split("DEFINICIONES")[1].split("Read-only")[0].strip(),
           "total": dict(tot), "por_volcan": por_vol, "ejemplos": ejemplos}

    u, pa = tot["universo"], tot["patron"]
    print(f"Patrón «Test 1 dispara y el primer pase da cero» · V375 · {DESDE} → {fin_gt}\n")
    print(f"  universo (records V375, 11 Tier A)          {u}")
    print(f"  con el patrón                                {pa}  ({100*pa/u:.1f} % del universo)")
    print(f"  de ellos, publicados como summit             {tot['patron_publicado']}"
          f"  ({100*tot['patron_publicado']/max(pa,1):.1f} % del patrón)")
    print(f"  de ellos, con alerta MIROVA esa noche        {tot['patron_con_alerta']}"
          f"  ({100*tot['patron_con_alerta']/max(pa,1):.1f} % del patrón)")
    print(f"  ... y además el MISMO objeto (cota ≤ {COTA_KM}) {tot['patron_mismo_objeto']}"
          f"  ({100*tot['patron_mismo_objeto']/max(pa,1):.1f} % del patrón)")
    print(f"\n  (alertas de pasadas diurnas excluidas del cruce: {n_diurnas})")
    print(f"\n{'volcán':<22}{'universo':>9}{'patrón':>8}{'public.':>9}{'c/alerta':>10}{'mismo obj':>11}")
    for vol in TIER_A:
        c = por_vol.get(vol)
        if not c:
            continue
        print(f"{vol:<22}{c.get('universo',0):>9}{c.get('patron',0):>8}"
              f"{c.get('patron_publicado',0):>9}{c.get('patron_con_alerta',0):>10}"
              f"{c.get('patron_mismo_objeto',0):>11}")
    if ejemplos:
        print("\nEjemplos (patrón + MIROVA confirma + mismo objeto):")
        for e in ejemplos:
            print(f"  {e['volcan']:<20} {e['pasada']}  nuestro {e['nuestra_km']} km vs MIROVA "
                  f"{e['mirova_km']} km (cota {e['cota_km']})  src={e['fuente']} "
                  f"{e['n_px']}px  2p={e['recaptura_2p']}")
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frecuencia_patron_test1.json")
    json.dump(res, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"\n→ {p}")


if __name__ == "__main__":
    main()
