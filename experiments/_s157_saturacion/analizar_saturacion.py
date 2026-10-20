# -*- coding: utf-8 -*-
"""Lee la salida de probe_saturacion.py (artefactos del run) y arma la tabla. ESCRITO ANTES DE VER DATOS.

Por pasada: cenit, VRP de MIROVA (de pasadas.json), lo que publicamos (control del probe: núcleo F5' en VIIRS 375 con
respaldo en el cúmulo, cúmulo en VIIRS 750 y MODIS), la falta, los conteos de saturación en la banda MIR y la TIR
(ventana = inner 5 km del ancla más los 8 vecinos del cúmulo), los perdidos por el lector del pipeline, la cota
inferior de energía y el veredicto con la regla del README (descartada / cierra / indeterminada). Imprime los
controles C-P1, C-IDX, C-0 y C-POS, y verifica en los atributos del archivo que el bit 4 se llama Saturation.

Uso: python analizar_saturacion.py <dir con los JSON> [--out resumen.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
C1, C2 = 1.191042e8, 14388.0


def bt_de_radiancia(L, lam):
    return C2 / (lam * np.log(1.0 + C1 / (lam ** 5 * L)))


def bandas(sensor):
    if sensor.startswith("MODIS"):
        return "B22", "B31", "B21"
    return ("M13", "M15", None) if sensor.endswith("_750") else ("I04", "I05", None)


def bit4_es_saturation(attrs):
    if not attrs:
        return None
    masks = attrs.get("flag_masks")
    means = attrs.get("flag_meanings")
    if masks is None or means is None:
        return None
    means = means.split() if isinstance(means, str) else list(means)
    masks = list(masks) if isinstance(masks, (list, tuple)) else [masks]
    return dict(zip([int(m) for m in masks], means)).get(4)


def veredicto(r, mir, tir, falta):
    c = r["conteos"]
    perd = r.get("n_perdidos_ventana", 0)
    cum_sat = sum(c[b]["cumulo"].get("bit4_sat", 0) + c[b]["cumulo"].get("tope_lut", 0)
                  for b in (mir, tir) if b in c and "bit4_sat" in c[b]["cumulo"])
    if perd == 0 and cum_sat == 0:
        return "descartada"
    cota = r.get("cota_inferior_mw")
    if falta is not None and cota is not None and cota >= falta:
        return "cierra"
    return "indeterminada"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--out")
    a = ap.parse_args()
    archivos = sorted(Path(a.dir).rglob("*.json"))
    archivos = [f for f in archivos if f.name != "resumen.json"]
    print("Techo de reporte (VIIRS L1B UserGuide Aug 2021, Tabla C.3, Reported Range, W m-2 sr-1 um-1 -> K):")
    for b, L, lam in (("I4", 4.65933, 3.74), ("I5", 22.8356, 11.45), ("M13", 605.770, 4.05), ("M15", 25.5611, 10.763)):
        print("   %-4s %9.4f -> %.1f K" % (b, L, bt_de_radiancia(L, lam)))
    filas, malos = [], []
    print("\n%-4s %-17s %-14s %5s %6s %6s %6s | %-34s | %-34s | %4s %7s | %s" % (
        "grp", "sensor", "pasada", "cenit", "M", "pub", "falta", "MIR: bit4 bit2 tope perd (cum b4/tope)",
        "TIR: bit4 bit2 tope perd (cum b4/tope)", "perd", "cota", "veredicto / controles"))
    for f in archivos:
        r = json.loads(f.read_text(encoding="utf-8"))
        p = r.get("pasada") or {}
        if not r.get("ok"):
            malos.append((f.name, r.get("error")))
            continue
        if p.get("grupo") == "POS":
            cpos = r.get("C_POS") or {}
            print("POS  %-17s %-14s C-POS %s" % (p["sensor"], p["granulo"][9:22], json.dumps(cpos)))
            filas.append({"grupo": "POS", "granulo": p["granulo"], "C_POS": cpos,
                          "C_POS_ok": any(v["si_65533_25km"] > 0 for v in cpos.values())})
            continue
        mir, tir, _ = bandas(p["sensor"])
        ctrl = r.get("control") or {}
        pc = ctrl.get("primary_cluster") or {}
        es375 = p["sensor"].startswith("VIIRS") and not p["sensor"].endswith("_750")
        pub = (ctrl.get("f5_core_vrp_mw") if es375 and ctrl.get("f5_core_vrp_mw") is not None else pc.get("vrp_mw")) or 0.0
        M = p.get("mirova_mw")
        falta = None if M is None else M - pub
        c = r["conteos"]

        def txt(b):
            d = c.get(b) or {}
            v, cu = d.get("ventana", {}), d.get("cumulo", {})
            if "bit4_sat" in v:
                return "%4d %4d %4d %4d (%d/%d)" % (v["bit4_sat"], v["bit2_oor"], v["tope_lut"], v["perdidos_pipeline"],
                                                    cu["bit4_sat"], cu["tope_lut"])
            return "65533 %d inval %d (cum %d)" % (v.get("si_65533_sat", 0), v.get("si_invalido", 0), cu.get("si_invalido", 0))
        if p["sensor"].startswith("MODIS"):
            ver = "descartada" if r.get("n_perdidos_ventana", 0) == 0 and all(
                # B22 inválida en el cúmulo no es pérdida (con K entra la B21, D21); B22 en 32767 sí entra recortada.
                (c[b]["cumulo"]["si_invalido"] == 0 or b == "B22") and c[b]["cumulo"]["tope_32767"] == 0
                for b in ("B21", "B22", "B31")) else (
                "cierra" if (falta is not None and (r.get("cota_inferior_mw") or 0) >= falta) else "indeterminada")
        else:
            ver = veredicto(r, mir, tir, falta)
        cidx = r.get("C_IDX") or {}
        cidx_ok = cidx.get("cumulo_en_anomalos") == cidx.get("n_cumulo") and cidx.get("shape_cumulos") == cidx.get("shape_geo")
        cp1 = (r.get("C_P1") or [None])[0]
        bit = bit4_es_saturation((c.get(mir) or {}).get("qf_attrs")) if not p["sensor"].startswith("MODIS") else "n/a"
        print("%-4s %-17s %-14s %5.1f %6s %6.2f %6s | %-34s | %-34s | %4d %7s | %s C-P1 %s C-IDX %s bit4=%s" % (
            p["grupo"], p["sensor"], p["granulo"][9:22] if not p["sensor"].startswith("MODIS") else p["granulo"][9:22],
            ctrl.get("sensor_zenith_deg") or p.get("cenit") or 0, "-" if M is None else "%.2f" % M, pub,
            "-" if falta is None else "%.2f" % falta, txt(mir), txt(tir), r.get("n_perdidos_ventana", 0),
            "-" if r.get("cota_inferior_mw") is None else "%.3f" % r["cota_inferior_mw"], ver, cp1, cidx_ok, bit))
        filas.append({"grupo": p["grupo"], "sensor": p["sensor"], "granulo": p["granulo"],
                      "cenit": ctrl.get("sensor_zenith_deg") or p.get("cenit"), "mirova_mw": M, "publicado_mw": pub,
                      "falta_mw": falta, "n_perdidos_ventana": r.get("n_perdidos_ventana"),
                      "cota_inferior_mw": r.get("cota_inferior_mw"), "veredicto": ver, "C_P1": cp1, "C_IDX": cidx_ok,
                      "bit4": bit, "conteos": c, "perdidos": r.get("perdidos"),
                      "bt_cruda_max_ventana": r.get("bt_cruda_max_ventana"),
                      "bt_pipeline_max_ventana": r.get("bt_pipeline_max_ventana")})
    print("\nFALLIDAS: %s" % malos if malos else "\nFALLIDAS: ninguna")
    # Enmienda post hoc (run 39512756808): un job se cayó al ESCRIBIR el JSON de una pasada que sí se midió; su
    # resultado quedó sólo en el log (línea «cota ... | C-P1 ... | {conteos de la ventana}»). Se lee de ahí, marcado.
    con_json = {f["granulo"] for f in filas if "granulo" in f}
    for lg in sorted(Path(a.dir).rglob("probe_*.log")):
        actual = None
        for linea in lg.read_text(encoding="utf-8", errors="replace").splitlines():
            if linea.startswith("== "):
                actual = linea.split()[1:4]
            elif linea.startswith("   cota ") and actual and actual[2] not in con_json:
                cota = linea.split()[1]
                cp1 = "(True" in linea.split("|")[1]
                try:
                    cont = json.loads(linea.split("|", 2)[2].strip())
                except ValueError:
                    cont = "truncado"
                pas = {x["granulo"]: x for x in json.loads((Path(__file__).resolve().parent / "pasadas.json")
                                                           .read_text(encoding="utf-8"))}.get(actual[2], {})
                es375 = actual[1].startswith("VIIRS") and not actual[1].endswith("_750")
                pub = (pas.get("f5_core_vrp_mw") if es375 and pas.get("f5_core_vrp_mw") is not None
                       else pas.get("pc_vrp_mw")) or 0.0   # persistido; C-P1 en verde dice que el control lo reproduce
                M = pas.get("mirova_mw")
                print("SOLO LOG %s %s %s | cenit %s | M %s pub %.3f falta %s | cota %s MW | C-P1 %s | ventana %s" % (
                    actual[0], actual[1], actual[2], pas.get("cenit"), M, pub,
                    "-" if M is None else "%.3f" % (M - pub), cota, cp1, json.dumps(cont)))
                filas.append({"grupo": actual[0], "sensor": actual[1], "granulo": actual[2], "solo_log": True,
                              "cota_inferior_mw": None if cota == "None" else float(cota), "C_P1": cp1,
                              "ventana": cont})
    print("\nCONTROLES")
    c0 = [f for f in filas if f["grupo"] == "C"]
    print("   C-0  (grupo C sin perdidos ni bit 4): %s" % [
        (f["sensor"], f["n_perdidos_ventana"], f["veredicto"]) for f in c0])
    pos = [f for f in filas if f["grupo"] == "POS"]
    print("   C-POS (65533 > 0 en Planchón Peteroa): %s" % [f["C_POS_ok"] for f in pos])
    nint = [f for f in filas if f["grupo"] in "AB" and not (f["C_P1"] and f.get("C_IDX"))]
    print("   pasadas que fallan C-P1 o C-IDX (no se interpretan): %s" % [(f["sensor"], f["granulo"][9:22]) for f in nint])
    print("\nAGREGADO (grupos A y B con alerta de MIROVA, controles en verde)")
    ok = [f for f in filas if f["grupo"] in "AB" and f.get("mirova_mw") is not None and f["C_P1"] and f.get("C_IDX")]
    for nombre, sel in (("oblicuas (cenit >= 50)", [f for f in ok if (f["cenit"] or 0) >= 50]),
                        ("no oblicuas (cenit < 50)", [f for f in ok if (f["cenit"] or 0) < 50])):
        for fam in ("VIIRS375", "VIIRS750", "MODIS"):
            s = [f for f in sel if (fam == "MODIS" and f["sensor"].startswith("MODIS"))
                 or (fam == "VIIRS750" and f["sensor"].endswith("_750"))
                 or (fam == "VIIRS375" and f["sensor"].startswith("VIIRS") and not f["sensor"].endswith("_750"))]
            if not s:
                continue
            ver = {v: sum(1 for f in s if f["veredicto"] == v) for v in ("descartada", "cierra", "indeterminada")}
            falta = sum(max(f["falta_mw"], 0) for f in s)
            cota = sum(f["cota_inferior_mw"] or 0 for f in s)
            print("   %-24s %-8s n %2d | %s | falta total %.2f MW | cota de saturación %.3f MW (%.1f %%)" % (
                nombre, fam, len(s), ver, falta, cota, 100 * cota / falta if falta else 0))
    if a.out:
        Path(a.out).write_text(json.dumps(filas, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
