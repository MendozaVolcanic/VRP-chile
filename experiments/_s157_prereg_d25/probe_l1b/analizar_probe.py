# -*- coding: utf-8 -*-
"""Lee la salida de probe_chillan.py (artefactos del run) y arma la tabla del probe. ESCRITO ANTES DE VER DATOS.

Por gránulo y brazo: la magnitud que el TABLERO muestra (predicado de frontend/index.html con node, A97: núcleo F5'
en VIIRS 375, cúmulo en VIIRS 750 y MODIS), su razón contra el VRP que MIROVA publicó en esa pasada (referencia
congelada de V1 del pre-registro, ±2 min, consolidado antes que OCR), el factor del brazo sobre el control, el
techo PL-0 del README, y la selección: potencia de los vecinos tibios no alertados (restando el anillo) y qué prueba
los dejó afuera. Imprime también los controles C-P1, C-N, C-A y C-K tal como los dejó el probe.

Uso: python analizar_probe.py <dir con los JSON> [--out resultado.json]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
for _p in (str(RAIZ), str(RAIZ / "scripts"), str(RAIZ / "experiments" / "_s151_prereg_fk_11")):
    sys.path.insert(0, _p)
import banco_paridad as bp  # noqa: E402
import sustrato as fk  # noqa: E402

VOL = "NevadosDeChillan"
REF = AQUI.parent / "_congelado_v1"
# PL-0 (README): techo del factor de D25 sobre S_in con los mismos píxeles = G con fondo 0 / G (a_pasadas_salida.txt, #869)
TECHO = {("VIIRS375", "0506"): 1.26, ("VIIRS375", "0600"): 1.24, ("VIIRS375", "0648"): 1.31,
         ("VIIRS750", "0506"): 1.55, ("VIIRS750", "0542"): 1.37, ("VIIRS750", "0600"): 1.36, ("VIIRS750", "0648"): 3.2,
         ("MODIS", "0120"): 2.8, ("MODIS", "0750"): 1.86}
BRAZOS = {"VIIRS": ("control", "nulo", "d25_h3", "d25_h1"), "MODIS": ("control", "nulo", "kernel3", "d25_rad")}


def s_in(rec, inner):
    """Suma de la potencia de nuestros alertados dentro del inner (lo que #869 llama S_in), desde anomaly_pixels."""
    return sum((p.get("vrp_mw") or 0) for p in (rec.get("anomaly_pixels") or []) if (p.get("dist_km") or 99) <= inner)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--out")
    a = ap.parse_args()
    archivos = sorted(Path(a.dir).rglob("VIIRS_*.json")) + sorted(Path(a.dir).rglob("MODIS_*.json"))
    if not archivos:
        print("sin JSON del probe en", a.dir)
        return 2
    filas = fk.cargar_filas(REF, False)
    coords, inner_all = bp._coords_por_volcan(), bp.inner_desde_html()
    inner = inner_all[VOL]
    por_vb, *_ = bp.indexar_referencia(filas, coords, ("2026-10-17", "2026-10-18"))
    casos, idx = [], []
    pasadas = []
    for f in archivos:
        res = json.loads(f.read_text(encoding="utf-8"))
        b = bp.bucket(res["sensor"])
        hhmm = res["granulo"].split(".")[2]
        fam = "MODIS" if b == "MODIS" else "VIIRS"
        dt = datetime.strptime(res["granulo"].split(".")[1][1:] + hhmm, "%Y%j%H%M").replace(tzinfo=timezone.utc)
        alertas = [x for x in bp.parear(por_vb.get((VOL, b), []), dt) if bp.es_alerta(x["tipo"])]
        alertas.sort(key=lambda x: (x["source"] != "CONS",))
        m = alertas[0]["vrp_mw"] if alertas else None
        p = {"sensor": res["sensor"], "b": b, "hhmm": hhmm, "ok": res.get("ok"), "error": res.get("error"), "M": m,
             "C_P1": res.get("C_P1"), "C_N": res.get("C_N"), "C_A": res.get("C_A"),
             "C_K": (res.get("control") or {}).get("C_K"), "brazos": {}}
        for br in BRAZOS[fam]:
            rec = (res.get(br) or {}).get("record")
            if rec is None:
                continue
            slim = {k: rec.get(k) for k in bp.CAMPOS_JS}
            casos.append([slim, inner])
            idx.append((len(pasadas), br))
            p["brazos"][br] = {"pc": (rec.get("primary_cluster") or {}), "f5": rec.get("f5_core_vrp_mw"),
                               "s_in": s_in(rec, inner), "sel": (res.get(br) or {}).get("seleccion"),
                               "fondo": (res.get(br) or {}).get("fondo_por_pixel")}
        pasadas.append(p)
    pred = bp.correr_node(casos) if casos else []
    for (i, br), q in zip(idx, pred):
        pasadas[i]["brazos"][br]["disp"], pasadas[i]["brazos"][br]["pub"] = q[3], q[4]

    print("Probe L1B Chillán 2026-10-18 | referencia %s | inner %s km\n" % (REF.name, inner))
    print("%-17s %4s %6s | %-8s %6s %5s %5s %6s %6s | %s" % ("sensor", "hhmm", "M", "brazo", "disp", "pub", "R",
                                                              "f_disp", "f_Sin", "controles"))
    for p in pasadas:
        if not p["ok"]:
            print("%-17s %4s  ERROR %s" % (p["sensor"], p["hhmm"], p["error"]))
            continue
        c = p["brazos"].get("control", {})
        for br, x in p["brazos"].items():
            r = (x["disp"] / p["M"]) if (p["M"] and x.get("disp") is not None) else None
            fd = (x["disp"] / c["disp"]) if c.get("disp") else None
            fs = (x["s_in"] / c["s_in"]) if c.get("s_in") else None
            techo = TECHO.get((p["b"], p["hhmm"]))
            marca = ""
            if br in ("d25_h3", "d25_h1", "d25_rad") and fs is not None and techo is not None and fs > techo * 1.01:
                marca = "  <-- PL-0 VIOLADO (techo %.2f)" % techo
            ctrl = ("C-P1 %s C-N %s C-A %s C-K %s" % (p["C_P1"][0] if p["C_P1"] else None, p["C_N"], p["C_A"],
                                                      (p["C_K"] or {}).get("ok"))) if br == "control" else ""
            print("%-17s %4s %6s | %-8s %6.3f %5s %5s %6s %6s | %s%s" % (
                p["sensor"], p["hhmm"], ("%.2f" % p["M"]) if p["M"] else "-", br, x.get("disp") or 0, x.get("pub"),
                ("%.2f" % r) if r is not None else "-", ("%.3f" % fd) if fd else "-", ("%.3f" % fs) if fs else "-",
                ctrl, marca))
    print("\nSELECCIÓN (brazo con fondo por vecinos; potencia de los vecinos tibios no alertados restando el anillo)")
    print("%-17s %4s | %5s %6s | %6s %6s | %s" % ("sensor", "hhmm", "n_cum", "n_vec", "S_vec", "falta", "rechazo (de los vecinos con potencia > 0)"))
    for p in pasadas:
        if not p["ok"]:
            continue
        br = "d25_rad" if p["b"] == "MODIS" else "d25_h3"
        x = p["brazos"].get(br, {})
        sel = x.get("sel") or {}
        if "vecinos" not in sel:
            print("%-17s %4s | sin diagnóstico: %s" % (p["sensor"], p["hhmm"], sel.get("error")))
            continue
        tib = [v for v in sel["vecinos"] if v["vrp_si_se_sumara_anillo_mw"] > 0]
        # Motivo de rechazo en la etapa que decide con K, el segundo pase (verificador H11); sin sus columnas, primer pase.
        motivos = collections.Counter(
            ("2do:" + ("+".join(n for n, ok in (("T2", v["sp_pasa_t2"]), ("T3", v["sp_pasa_t3"])) if not ok) or "pasa"))
            if "sp_pasa_t2" in v else
            ("1ro:" + ("+".join(n for n, ok in (("T2", v["pasa_t2"]), ("T3", v["pasa_t3"]), ("BT", v["pasa_bt"])) if not ok) or "pasa"))
            for v in tib)
        falta = (p["M"] - x["disp"]) if (p["M"] and x.get("disp") is not None) else None
        print("%-17s %4s | %5d %6d | %6.2f %6s | %s" % (p["sensor"], p["hhmm"], sel["n_cumulo"], len(sel["vecinos"]),
                                                       sel["suma_vecinos_tibios_anillo_mw"],
                                                       ("%.2f" % falta) if falta is not None else "-", dict(motivos)))
    if a.out:
        Path(a.out).write_text(json.dumps(pasadas, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
