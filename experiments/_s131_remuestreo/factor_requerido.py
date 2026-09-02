# -*- coding: utf-8 -*-
"""S131 - Cuanto crecimiento de area haria falta para aplanar el gradiente cenital.

POR QUE. S130 dejo probado que el ratio nuestro/MIROVA cae con el angulo y que
MIROVA es plano, y lo atribuyo al remuestreo de Coppola 2014 2.2. Pero atribuir no
es explicar: falta saber si el mecanismo alcanza CUANTITATIVAMENTE. Este script no
asume ninguna ley de area — la DESPEJA de los datos.

LA PREGUNTA, sin supuestos: si el unico problema fuera que integramos sobre un pixel
de area nominal cuando el pixel real es mas grande, entonces el ratio de cada bin,
multiplicado por el crecimiento de area de ese bin, deberia volver al valor del bin
de nadir. El factor requerido es entonces

    f_req(bin) = ratio(bin de nadir) / ratio(bin)

y se contrasta despues contra el crecimiento FISICO disponible segun el sensor. Si
el requerido excede lo fisicamente posible, hay un segundo mecanismo. Si sobra, el
area explica de mas y algo compensa.

ADVERTENCIA (auditoria S131, MAGNITUD 2.7): `cargar_mirova` colapsa MIROVA por (fecha,
bucket) = MAXIMO DE LA NOCHE, asi que cada record nuestro se compara contra la mejor
pasada de MIROVA de esa noche, no contra la misma pasada. Eso INFLA el gradiente
(f_req 2,93 aqui vs 1,72 pasada a pasada). La version corregida es
`experiments/_s131_audit/magnitud/03_pares_por_pasada.py`. Se conserva este script
como esta porque `docs/s131/REMUESTREO_LEY_DE_AREA.md` cita sus numeros por historia.

DEFINICIONES, dentro de la afirmacion (A90): identicas a
`experiments/_s130_cenital/medir_gradiente_cenital.py` — un par por (volcan, fecha,
bucket), maximo de cada lado, `pc.vrp_mw` (A10), loader CONS union OCR (A11), solo
nocturnas, ventana 2026, 11 Tier A, angulo = |sensor_zenith_deg|. Se agrega la
mediana del angulo dentro de cada bin, que es lo que permite evaluar la ley fisica
en el punto correcto y no en el borde del bin.
"""
import io
import json
import os
import statistics as st
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments"))

from _s126_lib import bucket, cargar_mirova                      # noqa: E402

OUT = os.path.join(HERE, "factor_requerido.json")
VOLS = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima",
        "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "Tupungatito", "Villarrica"]
BINS = ["0-15", "15-25", "25-35", "35-50", "50+"]
MIN_N = 15


def bin_de(sz):
    a = abs(sz)
    if a < 15:
        return "0-15"
    if a < 25:
        return "15-25"
    if a < 35:
        return "25-35"
    if a < 50:
        return "35-50"
    return "50+"


def main():
    mir, _ = cargar_mirova(("2026-01-01", "2026-12-31"))
    ratios = defaultdict(list)
    zen = defaultdict(list)

    for v in VOLS:
        p = os.path.join(ROOT, "data", "mirova_equivalent", v + ".json")
        if not os.path.exists(p):
            continue
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            bk = bucket(r.get("sensor"))
            if bk is None:
                continue
            sol = r.get("solar_zenith_deg")
            if sol is not None and sol < 90:
                continue
            sen = r.get("sensor_zenith_deg")
            pcv = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
            if sen is None or pcv <= 0:
                continue
            m = (mir.get(v) or {}).get((r.get("datetime_utc", "")[:10], bk))
            if not m or m <= 0:
                continue
            k = (bk, bin_de(sen))
            ratios[k].append(pcv / m)
            zen[k].append(abs(sen))

    res = {"definicion": (
        "f_req(bin) = ratio(0-15) / ratio(bin), con ratio = mediana de "
        "pc.vrp_mw nuestro / VRP MIROVA por par (volcan, fecha, bucket), maximo "
        "de cada lado, nocturnas, 2026, 11 Tier A, n >= 15. zen_mediano = mediana "
        "de |sensor_zenith_deg| dentro del bin."), "por_sensor": {}}

    print("CUANTO CRECIMIENTO DE AREA HARIA FALTA PARA APLANAR EL GRADIENTE")
    for bk, nom in (("v375", "VIIRS375"), ("v750", "VIIRS750"), ("modis", "MODIS")):
        base = ratios.get((bk, "0-15"), [])
        if len(base) < MIN_N:
            continue
        r0 = st.median(base)
        res["por_sensor"][bk] = {}
        print(f"\n  {nom}  (ratio del bin de nadir = {r0:.3f})")
        print(f"    {'bin':10s} {'n':>6s} {'zen_med':>9s} {'ratio':>8s} {'f_req':>8s}")
        for b in BINS:
            xs = ratios.get((bk, b), [])
            if len(xs) < MIN_N:
                continue
            rb = st.median(xs)
            zb = st.median(zen[(bk, b)])
            f = r0 / rb
            res["por_sensor"][bk][b] = {
                "n": len(xs), "zen_mediano_deg": round(zb, 1),
                "ratio": round(rb, 3), "f_requerido": round(f, 2)}
            print(f"    {b:10s} {len(xs):6d} {zb:9.1f} {rb:8.3f} {f:8.2f}")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
