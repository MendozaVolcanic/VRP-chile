# -*- coding: utf-8 -*-
"""Revisión de W1 (REVISION_W1.md): cableado, cobertura por día y periodo, compuertas del evaluador y huecos de CMR.

Uso: python -I experiments/_s163_diurno_k/w1/revisar_w1.py <raíz del run 40364164845> <referencia congelada>
La raíz es `experiments/_s151_ab_diurno/salidas/40364164845` de la rama `s151-ab-diurno/40364164845`; la referencia,
la que extrae `congelar_referencia.py --commit 047bd5692`. Consulta el catálogo CMR de NASA (público, sin credencial).
"""
import collections
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

os.environ["VRP_PROFILE"] = "mirova_equivalent"
AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.dirname(AQUI)
ROOT = os.path.dirname(os.path.dirname(CARPETA))
sys.path[:0] = [ROOT, os.path.join(ROOT, "scripts"), CARPETA]
sys.stdout.reconfigure(encoding="utf-8")

import banco_paridad as bp  # noqa: E402
import evaluar_diurno_k as ev  # noqa: E402
import sustrato_k as sk  # noqa: E402

C, B = "_s154_ab_diurno_k_control", "_s154_ab_diurno_k_on"
SHA = "68687d2d4b73bb0527da18a2c886a6dcc241a0ac"
V1 = [("W1", "2026-03-01", "2026-03-20")]
VENTANAS = [w[:3] for w in sk.VENTANAS]
PRODUCTOS = {"VNP02IMG": "2", "VJ102IMG": "2.1", "VJ202IMG": "2.1", "VNP02MOD": "2", "VJ102MOD": "2.1", "VJ202MOD": "2.1"}
CAJA = "-72.5,-39.5,-67.5,-23.0"


def dias_sin_granulos(producto, version, desde, hasta):
    dias, pagina = collections.Counter(), 1
    while True:
        q = urllib.parse.urlencode({"short_name": producto, "version": version, "bounding_box": CAJA, "page_size": 2000,
                                    "temporal": "%sT00:00:00Z,%sT23:59:59Z" % (desde, hasta), "page_num": pagina})
        e = json.load(urllib.request.urlopen("https://cmr.earthdata.nasa.gov/search/granules.json?" + q,
                                             timeout=60))["feed"]["entry"]
        for g in e:
            dias[g["time_start"][:10]] += 1
        if len(e) < 2000:
            break
        pagina += 1
    n = (dt.date.fromisoformat(hasta) - dt.date.fromisoformat(desde)).days + 1
    return [x for x in ((dt.date.fromisoformat(desde) + dt.timedelta(i)).isoformat() for i in range(n)) if not dias[x]]


def main(raiz, ref):
    inner = bp.inner_desde_html()
    recs = {C: ev.cargar_brazo([raiz], C, V1, inner), B: ev.cargar_brazo([raiz], B, V1, inner)}
    for lado, rs in recs.items():
        print(lado, "records", len(rs), "| sha", dict(collections.Counter(r["sha"] for r in rs)),
              "| Test 1", sum(1 for r in rs if r["t1"] or r["fuente_hotspot"] in ("test1", "test1_roi")),
              "| diag_umbrales_diurnos de día / de noche", sum(1 for r in rs if r["diag_dia"] and r["es_dia"]),
              sum(1 for r in rs if r["diag_dia"] and not r["es_dia"]))
    print("logs (FLAGS_BRAZO):", ev.problemas_de_logs([raiz], (C, B), C))
    pas = ev.pasadas_de(sk.cargar_ref(ref), "tabla", V1, ("Lascar",))
    cuenta = collections.Counter()
    for p in pas:
        d = ev.es_dia_vol(p.volcano, p.instante)
        t = p.instante.replace(tzinfo=None)
        lado = recs[B] if d else recs[C]
        hay = any(r["b"] == p.sensor_bucket and abs((r["dt"] - t).total_seconds()) <= 120 for r in lado)
        tramo = "10 a 12 de marzo" if "2026-03-10" <= t.strftime("%Y-%m-%d") <= "2026-03-12" else "resto"
        cuenta[(p.sensor_bucket, "día" if d else "noche", tramo, "con record" if hay else "SIN record")] += 1
    print("pasadas de la tabla de MIROVA (Láscar, W1), día contra el brazo diurno y noche contra el control:")
    for k, v in sorted(cuenta.items()):
        print("  ", k, v)
    sus = json.load(open(os.path.join(CARPETA, "sustrato_k.json"), encoding="utf-8"))
    r = ev.evaluar(pas, recs, C, B, "e-ii", ev.p_sup_de_vara(sus["vara_cobertura_nocturna_produccion"]), SHA, V1)
    print("compuertas, inválido:", r["compuertas"]["invalido"])
    print("compuertas, indecidible:", r["compuertas"]["indecidible"])
    for s, m in r["por_sensor"].items():
        print(s, "P2", m["p2"], "neto", m["neto"], "| protegidas", m["P"], "de", m["P_obs"], "| negativos", m["neg_pub"],
              "de", m["neg_obs"], "| Q_n %.3f (%d)" % (m["Qn"], m["Qn_den"]), "|", m["veredicto"], m["caso"])
    print("catálogo CMR, días sin ningún gránulo sobre la caja %s:" % CAJA)
    for prod, ver in PRODUCTOS.items():
        print("  ", prod, {w: dias_sin_granulos(prod, ver, a, b) for w, a, b in VENTANAS})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
