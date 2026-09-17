# -*- coding: utf-8 -*-
"""S143: elige las pasadas del probe de las 12 noches, ANTES de correrlo, desde los artefactos de S135.

POR QUÉ. El A/B S135 perdió 12 noches que MIROVA publica cuando quitó `keep_peak` y condicionó el
segundo pase (brazo D). El verificador del pre-registro S143 mostró que los brazos nuevos dejan la
compuerta de temperatura puesta justo en la máscara contextual que filtra el camino del Test 1, que es
la ruta de esas pérdidas. Antes de gastar ~160 horas de runner, este probe mide sobre esas mismas
pasadas qué cambio las recupera. Y para no elegir sólo lo que conviene, mide también el costo del
otro lado: pasadas donde MIROVA miró y no vio nada.

QUÉ ELIGE (sin mirar el resultado de ninguna variante nueva):
  * perdida: pasada nocturna VIIRS 375 de una de las 12 noches, con cualquier etiqueta, que el control
    S135 (A) publica y el brazo D no. Predicado del dashboard con node.
  * neg_artefacto: pasada `neg_limpio` que A publica y D no (el artefacto que D quitó). 3 por volcán.
  * neg_quieta: pasada `neg_limpio` que ni A ni D publican (donde quitar la compuerta podría fabricar
    una publicación nueva). 2 por volcán.
  Volcanes: los cuatro con pérdidas (Isluga, Lastarria, Planchón-Peteroa, Tupungatito). Muestreo con
  semilla 143 dentro de cada volcán, para no sesgar por fecha.

Escribe pasadas.json. USO: python experiments/_s143_probe_12_noches/seleccionar.py
"""
import collections
import io
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import banco_paridad as bp  # noqa: E402

VENTANA = ("2026-06-01", "2026-08-31")
ART = ROOT / "experiments" / "_artefactos_ab"
REF = ROOT / "experiments" / "_s143_preregistro" / "_dl_referencia"
RUNS = ("34173711390", "34208191011")
BRAZOS = {"A": "_s135_ab_a_control", "D": "_s135_ab_d_ambos"}
VOLS = ["Isluga", "Lastarria", "PlanchonPeteroa", "Tupungatito"]
PERDIDAS_S135 = {("Isluga", "2026-07-01"), ("Isluga", "2026-07-16"), ("Isluga", "2026-08-19"),
                 ("Lastarria", "2026-07-02"), ("Lastarria", "2026-08-28"),
                 ("PlanchonPeteroa", "2026-06-22"), ("PlanchonPeteroa", "2026-06-26"),
                 ("PlanchonPeteroa", "2026-07-24"), ("PlanchonPeteroa", "2026-08-09"),
                 ("PlanchonPeteroa", "2026-08-24"), ("Tupungatito", "2026-07-07"),
                 ("Tupungatito", "2026-08-01")}
N_ARTEFACTO, N_QUIETA, SEMILLA = 3, 2, 143


def cargar(brazo, vol):
    u = {}
    for run in RUNS:
        p = ART / f"s135ab-{brazo}-{vol}__run{run}" / f"{vol}.json"
        for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
            u[(r["datetime_utc"], r["sensor"])] = r
    return u


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    filas = bp.cargar_referencia_unificada(REF / "registro_vrp_consolidado.csv", REF / "registro_vrp_ocr.csv")
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, VENTANA)
    pub = {}
    etiqueta = {}
    for L, brazo in BRAZOS.items():
        recs, casos = [], []
        for vol in VOLS:
            for (dtu, sensor), r in cargar(brazo, vol).items():
                if bp.bucket(sensor) != "VIIRS375" or not (VENTANA[0] <= dtu[:10] <= VENTANA[1]):
                    continue
                dt = datetime.strptime(dtu, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                if bp.es_pasada_diurna_descartada("VIIRS375", *coords[vol], dt):
                    continue
                recs.append({"vol": vol, "b": "VIIRS375", "dt": dt, "noche": dtu[:10], "clave": (vol, dtu, sensor)})
                slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
                if r.get("f5_core_vrp_mw") is None:
                    slim["anomaly_pixels"] = [{k: q.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                              for q in (r.get("anomaly_pixels") or [])]
                casos.append([slim, inner[vol]])
        for rec, pr in zip(recs, bp.correr_node(casos)):
            pub[(L, rec["clave"])] = pr[4]
        bp.etiquetar(recs, por_vb, ns, nv)
        if L == "A":
            etiqueta = {rec["clave"]: rec for rec in recs}

    rng = random.Random(SEMILLA)
    salida, conteo = [], collections.Counter()
    for vol in VOLS:
        claves = sorted(k for k in etiqueta if k[0] == vol and ("D", k) in pub)
        # Toda pasada de la noche perdida que A publica y D no, con cualquier etiqueta: S135 confirmó la
        # noche con CUALQUIER publicación del control que pase la cota, no sólo la pareada a +-2 min
        # (ensayo del analizador: con sólo `pos`, 2 de las 12 noches quedaban sin su pasada confirmada).
        perdidas = [k for k in claves if (vol, etiqueta[k]["noche"]) in PERDIDAS_S135
                    and pub[("A", k)] and not pub[("D", k)]]
        artef = [k for k in claves if etiqueta[k]["lab"] == "neg_limpio" and pub[("A", k)] and not pub[("D", k)]]
        quietas = [k for k in claves if etiqueta[k]["lab"] == "neg_limpio" and not pub[("A", k)] and not pub[("D", k)]]
        elegidas = ([("perdida", k) for k in perdidas]
                    + [("neg_artefacto", k) for k in rng.sample(artef, min(N_ARTEFACTO, len(artef)))]
                    + [("neg_quieta", k) for k in rng.sample(quietas, min(N_QUIETA, len(quietas)))])
        for clase, (v, dtu, sensor) in elegidas:
            salida.append({"volcan": v, "pasada_utc": dtu, "sensor": sensor, "clase": clase,
                           "noche": dtu[:10], "s135_publica_A": pub[("A", (v, dtu, sensor))],
                           "s135_publica_D": pub[("D", (v, dtu, sensor))]})
            conteo[(vol, clase)] += 1
        conteo[(vol, "disponibles_neg_artefacto")] = len(artef)
        conteo[(vol, "disponibles_neg_quieta")] = len(quietas)
    noches_cubiertas = {(x["volcan"], x["noche"]) for x in salida if x["clase"] == "perdida"}
    faltan = sorted(PERDIDAS_S135 - noches_cubiertas)
    (HERE / "pasadas.json").write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    resumen = {"n_pasadas": len(salida), "noches_perdidas_cubiertas": len(noches_cubiertas),
               "noches_perdidas_sin_pasada": faltan, "por_volcan_y_clase": {f"{a}|{b}": c for (a, b), c in sorted(conteo.items())},
               "semilla": SEMILLA, "referencia": REF.relative_to(ROOT).as_posix(), "runs_s135": RUNS}
    (HERE / "seleccion_resumen.json").write_text(json.dumps(resumen, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumen, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
