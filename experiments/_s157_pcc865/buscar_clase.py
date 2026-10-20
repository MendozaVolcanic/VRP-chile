# -*- coding: utf-8 -*-
"""S157 issue #865: ¿la pérdida de PCC VIIRS 750 del 2026-10-10 05:54 es un caso aislado o una clase?

POR QUÉ. En esa pasada K (producción desde #850) no publica una alerta protegida de MIROVA (1,19 MW) que C0
publicaba. El A/B de K (experiments/_s153_fk_v2/) no vio ninguna protegida perdida en VIIRS 750, pero sólo
cubrió V1 (2026-08-29 a 10-08) y V2 (03-01 a 06-12). Acá se busca en TODA la historia con referencia.

QUÉ COMPARA (por pasada de alerta de MIROVA, mismo volcán y sensor, ±120 s, predicado del tablero con node, A97):
  K  = data/_s154_reproc_k_historico/ (K reprocesado, hasta 2026-09-17) ∪ records con `regimen` de
       data/mirova_equivalent/ (K desde 2026-09-18).
  C0 = data/mirova_equivalent/ en el tag pre-s153-adopcion-k (C0 hasta el 2026-10-18 01:01 UTC) ∪
       data/experimental_v2/ (la sombra C0, después del tag).
Protegida = lectura A (alerta del scraper de 1 MW o más, scripts/clase_mirova.alerta_protegida).

Para cada protegida VIIRS 750 que K no publica, lee del record de K los diagnósticos del primer pase y calcula los
umbrales de los Tests 2 y 3 en la cumbre con las dos conectivas: K usa max(C1, mu + C2·sigma), C0 min(...).

Uso: python buscar_clase.py <dir_temporal>   (escribe ahí las uniones; sólo lectura sobre data/)
"""
import io
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import auto_audit_weekly as aa  # noqa: E402
import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
import vigilancia_sombra as vs  # noqa: E402

TAG_C0 = "pre-s153-adopcion-k"
C1_SUM, C2_SUM = 0.003, 5.0   # pipeline.profile DNTI_CONTEXTUAL_C1_SUMMIT, C2_DNTI_SUMMIT_NIGHT (iguales en K y C0)
VENTANA = ("2026-01-10", "2026-10-19")


def uniones(tmp):
    dk, dc = tmp / "k_union", tmp / "c0_union"
    dk.mkdir(parents=True, exist_ok=True)
    dc.mkdir(parents=True, exist_ok=True)
    for vol in bp.VOLS:
        hist = json.load(open(ROOT / "data/_s154_reproc_k_historico" / f"{vol}.json", encoding="utf-8"))["records"]
        prod = json.load(open(ROOT / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
        k_prod = [r for r in prod if (r.get("regimen") or {}).get("codigo_sha")]
        corte = min(r["datetime_utc"] for r in k_prod)
        k = [r for r in hist if r["datetime_utc"] < corte] + k_prod
        json.dump({"records": k}, open(dk / f"{vol}.json", "w", encoding="utf-8"))
        tag = subprocess.run(["git", "-C", str(ROOT), "show", f"{TAG_C0}:data/mirova_equivalent/{vol}.json"],
                             capture_output=True, check=True).stdout
        c0 = [r for r in json.loads(tag)["records"] if not (r.get("regimen") or {}).get("codigo_sha")]
        fin = max(r["datetime_utc"] for r in c0)
        sombra = json.load(open(ROOT / "data/experimental_v2" / f"{vol}.json", encoding="utf-8"))["records"]
        c0 += [r for r in sombra if r["datetime_utc"] > fin]
        json.dump({"records": c0}, open(dc / f"{vol}.json", "w", encoding="utf-8"))
        print(f"  {vol:20s} K {len(k):5d} (corte {corte}) | C0 {len(c0):5d} (tag hasta {fin})", flush=True)
    return dk, dc


def indice(d):
    out = {}
    for vol in bp.VOLS:
        for r in json.load(open(d / f"{vol}.json", encoding="utf-8"))["records"]:
            out[(vol, r.get("sensor"), r["datetime_utc"])] = r
    return out


def umbrales(r):
    mu_n, sd_n, mu_e, sd_e = (r.get(c) for c in ("diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti", "diag_sd_deti"))
    if None in (mu_n, sd_n, mu_e, sd_e):
        return None
    cn, ce = mu_n + C2_SUM * sd_n, mu_e + C2_SUM * sd_e
    return {"dnti_K": max(C1_SUM, cn), "dnti_C0": min(C1_SUM, cn), "deti_K": max(C1_SUM, ce),
            "deti_C0": min(C1_SUM, ce), "contraste_gobierna_dnti": cn > C1_SUM, "contraste_gobierna_deti": ce > C1_SUM}


def main():
    tmp = Path(sys.argv[1])
    print("Uniones:")
    dk, dc = uniones(tmp)
    coords, inner = aa._coords_por_volcan(), bp.inner_desde_html()
    filas = cargar_referencia_unificada(aa.CONS, aa.OCR)
    K = bp.cargar_nuestros(coords, inner, VENTANA, data=dk)
    C0 = bp.cargar_nuestros(coords, inner, VENTANA, data=dc)
    pas = vs.pasadas_de_alerta(filas, K, C0, VENTANA)
    ik, ic = indice(dk), indice(dc)
    print(f"\nVentana {VENTANA[0]} a {VENTANA[1]} (A119: VIIRS por pasada se compara desde abril)")
    for b in ("VIIRS750", "VIIRS375", "MODIS"):
        prot = [p for p in pas if p["sensor"] == b and p["protegida"]]
        c = Counter((p["prod_pub"], p["sombra_pub"]) for p in prot)
        print(f"  {b:8s} protegidas A {len(prot):4d} | (K publica, C0 publica): " +
              ", ".join(f"{k}: {v}" for k, v in sorted(c.items(), key=str)))
    perdidas = [p for p in pas if p["sensor"] == "VIIRS750" and p["protegida"] and p["prod_pub"] is False]
    print(f"\nProtegidas VIIRS 750 que K NO publica: {len(perdidas)}")
    salida = []
    for p in perdidas:
        t = datetime.fromisoformat(p["instante_utc"]).replace(tzinfo=timezone.utc)
        cand = [r for r in K if r["vol"] == p["volcano"] and r["b"] == "VIIRS750"
                and abs((r["dt"] - t).total_seconds()) <= bp.TOL_S]
        for rk in cand:
            key = (p["volcano"], rk["sensor"], rk["dt"].strftime("%Y-%m-%d %H:%M"))
            k, c0 = ik.get(key), ic.get(key)
            u = umbrales(k) if k else None
            c0_pub = next((r["pub"] for r in C0 if r["vol"] == p["volcano"] and r["sensor"] == key[1]
                           and r["dt"] == rk["dt"]), None)
            fila = {**p, "record": key[1:], "K_pub_record": rk["pub"], "C0_pub_record": c0_pub,
                    "K": {c: (k or {}).get(c) for c in (
                        "n_anomalous_pixels", "diag_n_first_pass_pixels", "diag_n_second_pass_recapture", "nti_max",
                        "t_max_k", "t_bg_k", "sensor_zenith_deg", "distance_class")},
                    "K_pc": (k or {}).get("primary_cluster"), "umbrales_cumbre": u,
                    "C0": None if c0 is None else {c: c0.get(c) for c in (
                        "n_anomalous_pixels", "diag_n_first_pass_pixels", "diag_n_second_pass_recapture",
                        "triggered_test1", "test1_k_observed", "final_hotspot_source", "distance_class")},
                    "C0_pc": None if c0 is None else c0.get("primary_cluster")}
            salida.append(fila)
            pc = fila["K_pc"] or {}
            kk, cc = fila["K"], fila["C0"] or {}
            print(f"  {p['volcano']:20s} {key[1]:17s} {key[2]} MIROVA {p['vrp_mirova_mw']} MW"
                  f" | K: px {kk['n_anomalous_pixels']} 1er {kk['diag_n_first_pass_pixels']}"
                  f" 2do {kk['diag_n_second_pass_recapture']} pc {pc.get('vrp_mw')} MW a {pc.get('centroid_dist_km')} km"
                  f" clase {kk['distance_class']} pub {rk['pub']}"
                  f" | C0: pub {c0_pub} 1er {cc.get('diag_n_first_pass_pixels')} 2do {cc.get('diag_n_second_pass_recapture')}"
                  f" T1 {cc.get('triggered_test1')} fuente {cc.get('final_hotspot_source')}"
                  f" pc {(fila['C0_pc'] or {}).get('vrp_mw')}")
            if u:
                print(f"      umbral cumbre dNTI K {u['dnti_K']:.5f} / C0 {u['dnti_C0']:.5f} | dETI K {u['deti_K']:.5f}"
                      f" / C0 {u['deti_C0']:.5f} | NTI max {kk['nti_max']} | cenit {kk['sensor_zenith_deg']}")
        if not cand:
            salida.append({**p, "record": None})
            print(f"  {p['volcano']:20s} {p['fecha_utc']} sin record K a +-120 s")
    (HERE / "buscar_clase_resultado.json").write_text(json.dumps(salida, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
