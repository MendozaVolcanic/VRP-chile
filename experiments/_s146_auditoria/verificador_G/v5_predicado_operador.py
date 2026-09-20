# -*- coding: utf-8 -*-
"""V5 (verificador G, item 5) - que se PUBLICA de verdad, con el predicado del dashboard
EJECUTADO con node desde frontend/index.html. No se porta a mano (A97): se reusa el arnes
`correr_node` de scripts/banco_paridad.py, que extrae las funciones reales del HTML y las evalua.

(1) Si lo que mide estuviera roto, ¿fallaria?
    Si el predicado no se estuviera ejecutando, `correr_node` tirarìa excepcion al no encontrar
    alguna funcion en el HTML (extrae por nombre y falla duro). Ademas se imprime el sha del
    index.html usado, asi que la salida queda atada a una version concreta del archivo.
(2) Si el instrumento estuviera muerto, ¿se veria distinto?
    Si: se corre el control de identidad del propio banco (`control_identidad_predicado`), que
    compara el predicado contra casos de referencia conocidos; y se imprimen los dos extremos
    (records que publican y que no) sobre el mismo denominador, cuya suma debe dar el total.

Tambien mide, por camino propio, si el tope de Villarrica llega o no al operador, y si
frontend/diario.html define los dos predicados.

Ventana 2026-09-01 en adelante. Solo lectura.
"""
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import os
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as BP  # noqa: E402

DATA = ROOT / "data" / "mirova_equivalent"
OUT = Path(__file__).with_suffix(".json")
INICIO = "2026-09-01"


def main():
    inner = BP.inner_desde_html()
    recs, casos = [], []
    for vol in BP.VOLS:
        for r in json.load(open(DATA / f"{vol}.json", encoding="utf-8"))["records"]:
            if r.get("datetime_utc", "") < INICIO or not r.get("sensor"):
                continue
            b = BP.bucket(r["sensor"])
            if b is None:
                continue
            recs.append({"vol": vol, "b": b, "dt": r["datetime_utc"],
                         "dr": r.get("discarded_reason"),
                         "pc_vrp": (r.get("primary_cluster") or {}).get("vrp_mw"),
                         "pc_n": (r.get("primary_cluster") or {}).get("n_pixels"),
                         "trig": r.get("triggered_test1"),
                         "dc": r.get("distance_class")})
            slim = {k: r.get(k) for k in BP.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])

    pred = BP.correr_node(casos)
    for rec, p in zip(recs, pred):
        rec["summit"], rec["valid"], rec["art"], rec["disp"], rec["pub"] = p

    out = {"ventana_desde": INICIO, "n": len(recs),
           "sha_index_html": BP.sha_git(BP.HTML),
           "control_identidad_predicado": BP.control_identidad_predicado(),
           "publican": sum(r["pub"] for r in recs),
           "no_publican": sum(1 - r["pub"] for r in recs)}

    top = [r for r in recs if r["dr"] == "cluster_too_large_for_volcano"]
    out["item5a_tope_villarrica"] = {
        "topados": len(top),
        "publican": sum(r["pub"] for r in top),
        "de_los_que_publican_con_trigger_test1": sum(1 for r in top if r["pub"] and r["trig"]),
        "de_los_que_publican_SIN_trigger_test1": sum(1 for r in top if r["pub"] and not r["trig"]),
        "isValidDetection_verdadero": sum(r["valid"] for r in top),
        "isSummitDetection_verdadero": sum(r["summit"] for r in top),
        "artefacto": sum(r["art"] for r in top),
        "detalle": [{"dt": r["dt"], "b": r["b"], "pc_n": r["pc_n"], "pc_vrp": r["pc_vrp"],
                     "trig": r["trig"], "dc": r["dc"], "valid": r["valid"],
                     "summit": r["summit"], "art": r["art"], "disp": r["disp"],
                     "pub": r["pub"]} for r in top],
    }

    dr = [r for r in recs if r["dr"]]
    out["item5b_discarded_reason"] = {
        "con_discarded_reason": len(dr),
        "publican": sum(r["pub"] for r in dr),
        "por_razon": {k: {"n": sum(1 for r in dr if r["dr"] == k),
                          "publican": sum(r["pub"] for r in dr if r["dr"] == k)}
                      for k in sorted({r["dr"] for r in dr})},
    }

    diario = (ROOT / "frontend" / "diario.html").read_text(encoding="utf-8")
    idx = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    out["item5c_diario"] = {
        f: {"diario.html": len(re.findall(r"(?<![A-Za-z0-9_])" + f + r"\s*\(", diario)),
            "index.html": len(re.findall(r"(?<![A-Za-z0-9_])" + f + r"\s*\(", idx))}
        for f in ("isValidDetection", "isSummitDetection", "mirovaEqVrp", "isThermalArtifact")}

    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "item5a_tope_villarrica"},
                     indent=1, ensure_ascii=False))
    print("\nitem5a detalle:")
    for d in out["item5a_tope_villarrica"]["detalle"]:
        print("  ", d)
    print("\nitem5a resumen:", {k: v for k, v in out["item5a_tope_villarrica"].items() if k != "detalle"})
    print("\nJSON:", OUT)


if __name__ == "__main__":
    main()
