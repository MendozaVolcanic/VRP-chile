# -*- coding: utf-8 -*-
"""v01 (verificador S173, cenit V750): pareo por pasada PROPIO, sin los helpers del auditor ni banco_paridad.

Pregunta 1 (si estuviera roto, lo veria): el pareo se hace al minuto desde los records de main y los CSV del
scraper; si la razon K/MIROVA NO cayera con el cenit en Chillan, el Spearman quedaria dentro del barajado.
Pregunta 2 (instrumento muerto): placebos: referencia corrida +1 dia, +50 min y -50 min (otra plataforma),
y VRP de MIROVA barajado entre las alertas (semilla 173). Control positivo: razon multiplicada por una
funcion decreciente del cenit tiene que dar Spearman mas negativo que el real.

Denominador: records VIIRS 750 nocturnos de Chillan en repo/data/mirova_equivalent (main 5de08ebf).
Vara: CSV consolidado (primero) y OCR (si no hay fila CONS de alerta) de repo/data/mirova_reference/mirova_v1_snapshot.
Regla SN: solo aplica a VIIRS 375 (clase_mirova.SENSORES_MINIMA), asi que aqui no cambia nada; se informa cuantas
alertas de <= 0,05 MW hay igual.
"""
from __future__ import annotations

import csv
import io
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
REPO = AQUI / "repo"
REF = REPO / "data" / "mirova_reference" / "mirova_v1_snapshot"
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    rk = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            rk[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return rk


def spearman(x, y):
    if len(x) < 4:
        return None
    a, b = rank(x), rank(y)
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return num / den if den else None


def barajado(z, r, n=200, semilla=173):
    rng = random.Random(semilla)
    out = []
    for _ in range(n):
        zz = list(z)
        rng.shuffle(zz)
        s = spearman(zz, r)
        if s is not None:
            out.append(s)
    out.sort()
    return (out[int(0.025 * len(out))], out[int(0.975 * len(out)) - 1]) if out else (None, None)


def q(v):
    if not v:
        return "sin datos"
    v = sorted(v)
    n = len(v)
    return f"{statistics.median(v):.3f} n={n} rango [{v[0]:.3f}, {v[-1]:.3f}]"


def linea(nombre, pares):
    z = [a for a, _ in pares]
    r = [b for _, b in pares]
    lo = [b for a, b in pares if a < 30]
    hi = [b for a, b in pares if a >= 30]
    sp = spearman(z, r)
    bj = barajado(z, r)
    fuera = sp is not None and bj[0] is not None and (sp < bj[0] or sp > bj[1])
    pr(f"{nombre:34s} z<30 {q(lo)} | z>=30 {q(hi)}"
       + (f" | Spearman {sp:+.3f} barajado [{bj[0]:+.3f}, {bj[1]:+.3f}] {'FUERA' if fuera else 'dentro'}"
          if sp is not None else " | n insuficiente"))
    return sp, bj


def dt(s):
    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def cargar_ref():
    out = []
    for nombre, src in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR")):
        with open(REF / nombre, encoding="utf-8-sig", newline="") as fh:
            for f in csv.DictReader(fh):
                if f["Volcan"] != "Nevados de Chillan" or f["Sensor"] != "VIIRS":
                    continue
                try:
                    v = float(f["VRP_MW"]) if f["VRP_MW"] not in ("", None) else None
                except ValueError:
                    v = None
                try:
                    zs = float(f.get("Zenith_Sat_deg") or "nan")
                except ValueError:
                    zs = float("nan")
                out.append({"t": dt(f["Fecha_Satelite_UTC"]), "fecha": f["Fecha_Satelite_UTC"], "src": src,
                            "tipo": f["Tipo_Registro"], "vrp": v, "z_ocr": zs, "dist": f.get("Distancia_km")})
    out.sort(key=lambda x: x["t"])
    return out


def es_alerta(tipo):
    return tipo.startswith("ALERTA") and tipo != "ALERTA_SIN_GEOMETRIA_OCR"


def parear(ref, t, tol_s, desplaz=timedelta(0)):
    tt = t + desplaz
    return [f for f in ref if abs((f["t"] - tt).total_seconds()) <= tol_s]


def vrp_mirova(fs):
    al = [f for f in fs if es_alerta(f["tipo"])]
    if not al:
        return None, None
    c = [f for f in al if f["src"] == "CONS"]
    f = (c or al)[0]
    return f["vrp"], f


def main():
    ref = cargar_ref()
    pr("== VARA: filas de Chillan sensor VIIRS (=750) en los CSV:", len(ref),
       "| CONS", sum(f["src"] == "CONS" for f in ref), "| OCR", sum(f["src"] == "OCR" for f in ref))
    pr("tipos:", dict(Counter(f["tipo"] for f in ref)))
    pr("ultima fila:", max(f["fecha"] for f in ref))
    d = json.load(open(REPO / "data" / "mirova_equivalent" / "NevadosDeChillan.json", encoding="utf-8"))
    recs = [r for r in d["records"] if (r.get("sensor") or "").endswith("_750")]
    pr("records VIIRS 750 de Chillan en main:", len(recs))
    noche = [r for r in recs if (r.get("solar_zenith_deg") or 0) > 90]
    pr("de noche (solar_zenith_deg > 90):", len(noche), "| sin solar_zenith:",
       sum(1 for r in recs if r.get("solar_zenith_deg") is None))

    for ventana in (("2026-04-01", "2026-10-31"), ("2026-09-28", "2026-10-17")):
        pr(f"\n==== VENTANA {ventana[0]} a {ventana[1]}")
        R = [r for r in noche if ventana[0] <= r["datetime_utc"][:10] <= ventana[1]]
        refw = [f for f in ref if ventana[0] <= f["fecha"][:10] <= ventana[1]]
        al_min = sorted({f["fecha"][:16] for f in refw if es_alerta(f["tipo"])})
        al_min_noche = [m for m in al_min if 0 <= int(m[11:13]) <= 11]
        pr("records nocturnos:", len(R), "| minutos con alerta MIROVA V750 (CONS u OCR):", len(al_min),
           "| de ellos entre 00 y 11 UTC:", len(al_min_noche))
        pr("alertas <= 0,05 MW (regla SN no aplica a V750 pero se informa):",
           sum(1 for f in refw if es_alerta(f["tipo"]) and f["vrp"] is not None and f["vrp"] <= 0.05))
        P = []
        c = Counter()
        for r in R:
            t = dt(r["datetime_utc"])
            fs = parear(refw, t, 120)
            vm, fm = vrp_mirova(fs)
            n60 = vrp_mirova(parear(refw, t, 60))[0]
            n300 = vrp_mirova(parear(refw, t, 300))[0]
            pc = r.get("primary_cluster") or {}
            x = {"t": r["datetime_utc"], "sensor": r["sensor"], "z": r.get("sensor_zenith_deg"),
                 "vM": vm, "srcM": (fm or {}).get("src"), "z_ocr": (fm or {}).get("z_ocr"),
                 "pc": pc.get("vrp_mw"), "dc": r.get("distance_class"), "scene": r.get("vrp_mw"),
                 "n_filas": len(fs), "n_alertas": sum(es_alerta(f["tipo"]) for f in fs)}
            c["par120" if vm else "sin120"] += 1
            c["par60"] += bool(n60)
            c["par300"] += bool(n300)
            c["dos_alertas_en_120s"] += x["n_alertas"] > 1
            for nom, dd in (("+1d", timedelta(days=1)), ("+50min", timedelta(minutes=50)),
                            ("-50min", timedelta(minutes=-50))):
                c[f"placebo{nom}"] += bool(vrp_mirova(parear(refw, t, 120, dd))[0])
            P.append(x)
        pos = [x for x in P if x["vM"] and x["vM"] > 0]
        pr("pareo +-120 s: con alerta", c["par120"], "| sin", c["sin120"], "| +-60 s:", c["par60"],
           "| +-300 s:", c["par300"], "| pasadas con 2+ filas de alerta a +-120 s:", c["dos_alertas_en_120s"])
        pr("P2 placebos (pares con alerta): +1 dia", c["placebo+1d"], "| +50 min", c["placebo+50min"],
           "| -50 min", c["placebo-50min"])
        # alertas de MIROVA sin record nuestro (cobertura)
        rec_min = {x["t"] for x in P}
        sin_rec = [m for m in al_min_noche if not any(abs((dt(m) - dt(t)).total_seconds()) <= 120 for t in rec_min)]
        pr("minutos de alerta nocturna de MIROVA SIN record nuestro a +-120 s:", len(sin_rec), sin_rec[:12])
        pr("positivos (record con alerta pareada):", len(pos), "| fuente:", dict(Counter(x["srcM"] for x in pos)),
           "| plataformas:", dict(Counter(x["sensor"] for x in pos)))
        if not pos:
            continue
        pr("ventana de los positivos:", min(x["t"] for x in pos), "a", max(x["t"] for x in pos),
           "| noches:", len({x["t"][:10] for x in pos}))
        zs = sorted(x["z"] for x in pos)
        pr("cenit:", [round(z, 1) for z in zs], "| n<30", sum(z < 30 for z in zs), "n>=30", sum(z >= 30 for z in zs))
        zo = [(x["z"], x["z_ocr"]) for x in pos if x["z_ocr"] is not None and not math.isnan(x["z_ocr"])]
        pr("cenit del record vs Zenith_Sat_deg del OCR (filas OCR pareadas):", len(zo),
           [(round(a, 1), round(b, 1)) for a, b in zo])
        pr("pc.vrp_mw None en positivos:", sum(1 for x in pos if x["pc"] is None),
           "| distance_class:", dict(Counter(x["dc"] for x in pos)),
           "| pc.vrp_mw == 0:", sum(1 for x in pos if x["pc"] == 0))
        pr("\n-- razon pc.vrp_mw / MIROVA, CON ceros (pc None o <= 0 cuenta 0), n =", len(pos))
        rz0 = [(x["z"], max(x["pc"] or 0, 0) / x["vM"]) for x in pos]
        sp0, bj0 = linea("K pc con ceros", rz0)
        rzs = [(x["z"], max(x["scene"] or 0, 0) / x["vM"]) for x in pos]
        linea("K escena (record.vrp_mw) con ceros", rzs)
        pr("-- razon SIN ceros (solo pc > 0)")
        rz1 = [(x["z"], x["pc"] / x["vM"]) for x in pos if (x["pc"] or 0) > 0]
        linea("K pc sin ceros", rz1)
        pr("-- solo summit (proxy del predicado del tablero), con ceros")
        rzsum = [(x["z"], (max(x["pc"] or 0, 0) / x["vM"]) if x["dc"] == "summit" else 0.0) for x in pos]
        linea("K pc summit con ceros", rzsum)
        pr("-- solo filas CONS (A119)")
        linea("K pc con ceros, CONS", [(x["z"], max(x["pc"] or 0, 0) / x["vM"]) for x in pos if x["srcM"] == "CONS"])
        pr("-- log10 de la razon sin ceros")
        linea("log10 K pc", [(z, math.log10(r)) for z, r in rz1])
        # placebo: VRP de MIROVA barajado entre positivos
        rng = random.Random(173)
        vm = [x["vM"] for x in pos]
        rng.shuffle(vm)
        linea("PLACEBO MIROVA barajado", [(x["z"], max(x["pc"] or 0, 0) / v) for x, v in zip(pos, vm)])
        # control positivo: multiplicar la razon por (1 - z/90)
        linea("CONTROL+ razon*(1-z/90)", [(z, r * (1 - z / 90)) for z, r in rz0])
        linea("CONTROL+ razon*(1+z/90)", [(z, r * (1 + z / 90)) for z, r in rz0])
        # jackknife por noche
        noches = sorted({x["t"][:10] for x in pos})
        sps = []
        for n in noches:
            S = [(x["z"], max(x["pc"] or 0, 0) / x["vM"]) for x in pos if x["t"][:10] != n]
            sps.append(spearman([a for a, _ in S], [b for _, b in S]))
        pr(f"jackknife por noche ({len(noches)} replicas), Spearman K pc con ceros: min {min(sps):+.3f} max {max(sps):+.3f}")
        # por plataforma
        for s in sorted({x["sensor"] for x in pos}):
            linea(f"K pc con ceros, {s}", [(x["z"], max(x["pc"] or 0, 0) / x["vM"]) for x in pos if x["sensor"] == s])
        # cenit alternativo: tramos por el cenit del OCR cuando existe
        pr("\n-- DETALLE positivos (orden de cenit)")
        pr("t                 sensor            z     vM    pc     razon  dc      src  nfilas")
        for x in sorted(pos, key=lambda y: y["z"]):
            pcv = x["pc"]
            pr(f"{x['t']} {x['sensor']:17s} {x['z']:5.1f} {x['vM']:6.2f} {pcv if pcv is None else round(pcv, 3)!s:>6} "
               f"{(max(pcv or 0, 0) / x['vM']):6.3f} {x['dc']!s:7s} {x['srcM']:4s} {x['n_filas']}")
        if ventana[0] == "2026-09-28":
            json.dump(pos, open(AQUI / "v01_positivos_0928_1017.json", "w", encoding="utf-8"), indent=1,
                      ensure_ascii=False, default=str)
    (AQUI / "v01_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
