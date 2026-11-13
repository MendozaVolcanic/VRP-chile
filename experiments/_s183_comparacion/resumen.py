# -*- coding: utf-8 -*-
"""S183: tabla en markdown de salida/via_k_mirova.json (los números salen del JSON, nunca a mano)."""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).parent
d = json.loads((AQUI / "salida" / "via_k_mirova.json").read_text(encoding="utf-8"))
NOMBRE = {"MODIS": "MODIS", "VIIRS375": "VIIRS 375", "VIIRS750": "VIIRS 750"}


def pct(x):
    return "sin dato" if x is None else f"{100 * x:.1f} %".replace(".", ",")


def num(x):
    return "sin dato" if x is None else f"{x:.2f}".replace(".", ",")


print(f"Generado {d['meta']['generado_utc']}; index.html {d['meta']['sha_index_html'][:9]}; tabla "
      f"{d['meta']['sha_cons'][:9]}; OCR {d['meta']['sha_ocr'][:9]}; D-9 {d['meta']['regla_minimas']}.\n")
for ref in ("tabla", "combinado"):
    print(f"\n### Referencia: {'sólo la tabla de MIROVA' if ref == 'tabla' else 'tabla más OCR'}\n")
    print("| Ventana | Sensor | Noches-sat. pareadas | Detector | TP | FN | FP | TN | Recall | Precisión | "
          "Protegidas perdidas | Mediana nuestro/MIROVA (cuartiles) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for clave, r in d["resultados"].items():
        rr, vent, b = clave.split("|")
        if rr != ref:
            continue
        for det in ("via", "k"):
            m = r[det]
            q = m["cuartiles_cociente"]
            cq = f"{num(m['mediana_cociente'])} ({num(q[0])} a {num(q[2])})" if q else num(m["mediana_cociente"])
            print(f"| {vent} | {NOMBRE[b]} | {r['n_pasadas_pareadas']} pasadas | {'vía' if det == 'via' else 'K'} | "
                  f"{m['TP']} | {m['FN']} | {m['FP']} | {m['TN']} | {pct(m['recall'])} | {pct(m['precision'])} | "
                  f"{m['protegidas_perdidas']} de {m['protegidas']} | {cq} |")
print("\n### Alertas de MIROVA escondidas en pasadas sin par (una pérdida que el pareo no ve)\n")
for clave, r in d["resultados"].items():
    sv, sk = r["sin_par_via"], r["sin_par_k"]
    print(f"- {clave}: sólo vía {sv['n']} pasadas ({sv['pos']} con alerta); sólo K {sk['n']} pasadas ({sk['pos']} con alerta)")
print("\n### Alertas protegidas en que vía y K no coinciden\n")
for clave, r in d["resultados"].items():
    for p in r["protegidas_discordantes_pasadas"]:
        quien = "sólo la vía publica" if p["via_pub"] else "sólo K publica"
        print(f"- {clave} | {p['volcan']} {p['satelite']} {p['dt'][:16]}: MIROVA {num(p['vrp_mirova'])} MW, {quien}; "
              f"vía {p['via_dc']} a {p['via_d_mc']} km del centro de MIROVA, K {p['k_dc']} a {p['k_d_mc']} km "
              f"(K muestra {num(p['k_disp'])} MW, vía {num(p['via_disp'])} MW)")
