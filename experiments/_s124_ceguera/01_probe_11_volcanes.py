# -*- coding: utf-8 -*-
"""S124 — ¿La máscara de nube <260 K nos ciega, y ahí perdemos alertas de MIROVA?

READ-ONLY. No toca pipeline ni datos (A45): solo lee los JSON ya persistidos y
el consolidado de MIROVA.

EL FENÓMENO
-----------
El pipeline marca "nube" todo píxel cuyo TIR irradie bajo 260 K (−13 °C) y lo
saca de dos lugares (`process_viirs.py:681-682`):

    roi_mask = roi_mask & cloud_free     # de donde se buscan anomalías
    bg_mask  = bg_mask  & cloud_free     # y del anillo que fija el umbral

En un volcán nevado, una noche fría de invierno tiene buena parte del ROI bajo
esa temperatura — no porque haya nube, sino porque **es nieve**. Cuando la
máscara se lleva el anillo entero, el pipeline se queda sin estadística de
fondo (`n_bg = 0`) y no puede detectar nada. La noche queda ciega.

MIROVA no filtra nube. Laiolo 2026, textual: *"no atmospheric correction or
cloud-contamination automatic filtering"*. Conserva su fondo y publica.

Y esa máscara es la que `MISSION.md:127` declara **"Removido S27"** (ver D14).

LO QUE ESTE PROBE MIDE (sobre los 11 Tier A, no solo NdC)
---------------------------------------------------------
  1. Qué fracción de las pasadas queda sin fondo, por volcán.
  2. Si la máscara es lo que las deja sin fondo (comparar cuánto enmascara en
     las pasadas con fondo vs sin fondo).
  3. Cuántas alertas de MIROVA caen en noches ciegas — o sea, cuánto recall nos
     está costando.

Si el patrón de NdC (3 de 3 alertas perdidas en noches ciegas) se repite en la
flota, el caso para el A/B de la máscara está hecho.

Fuente de verdad de los números del informe (regla S91).
"""
import collections
import csv
import io
import json
import math
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

INI = "2026-06-01"
PIX_ROI_I = (50.0 / 0.375) ** 2      # ROI 50x50 km en píxeles I-band nadir

VOLS = ["Lascar", "Isluga", "Lastarria", "Llaima", "Copahue", "Tupungatito",
        "NevadosDeChillan", "Villarrica", "Chaiten", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]

# A14: el scraper normaliza algunos nombres — siempre verificar variantes.
ALIAS = {
    "NevadosDeChillan": ["Nevados de Chillan"],
    "PlanchonPeteroa": ["PlanchonPeteroa", "Planchon-Peteroa", "Planchón-Peteroa"],
    "PuyehueCordonCaulle": ["Puyehue-Cordon Caulle", "PuyehueCordonCaulle"],
}


def med(v):
    v = sorted(x for x in v if x is not None)
    return v[len(v) // 2] if v else float("nan")


def pasadas_viirs375(vol):
    """Las pasadas VIIRS I-band, que es donde vive la máscara."""
    p = ROOT / f"data/mirova_equivalent/{vol}.json"
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    return [r for r in d["records"]
            if (r.get("datetime_utc") or "") >= INI
            and "VIIRS" in (r.get("sensor") or "") and "750" not in r["sensor"]]


def alertas_mirova():
    """Noches con ALERTA VIIRS375 publicada, por volcán (nombre del scraper)."""
    gt = collections.defaultdict(set)
    with open(ROOT / "latest_consolidado.csv", encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            v = r.get("Volcan")
            f = (r.get("Fecha_Satelite_UTC") or "")[:10]
            if not v or f < INI:
                continue
            if "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            if (r.get("Sensor") or "").strip().upper() != "VIIRS375":
                continue
            try:
                x = float(r.get("VRP_MW") or 0)
            except ValueError:
                continue
            if x > 0:
                gt[v].add(f)
    return gt


if __name__ == "__main__":
    gt = alertas_mirova()

    print("1) ¿Cuántas pasadas quedan SIN fondo, y enmascara más la regla ahí?\n")
    print(f"{'volcán':22s} {'pasadas':>8s} {'sin fondo':>10s} "
          f"{'<260K sin fondo':>16s} {'con fondo':>10s} {'factor':>7s}")
    print("-" * 80)
    total = collections.Counter()
    for v in VOLS:
        rs = pasadas_viirs375(v)
        if not rs:
            continue
        sin = [r for r in rs if (r.get("diag_n_bg_used_first_pass") or 0) == 0]
        con = [r for r in rs if (r.get("diag_n_bg_used_first_pass") or 0) > 0]
        ms = med([r.get("n_cloud_masked") for r in sin])
        mc = med([r.get("n_cloud_masked") for r in con])
        fac = (ms / mc) if (mc and mc > 0 and ms == ms) else float("nan")
        total["pasadas"] += len(rs)
        total["sin"] += len(sin)
        print(f"{v:22s} {len(rs):8d} {len(sin):6d} ({100*len(sin)/len(rs):3.0f}%) "
              f"{100*ms/PIX_ROI_I if ms == ms else float('nan'):14.0f}% "
              f"{100*mc/PIX_ROI_I if mc == mc else float('nan'):9.0f}% {fac:6.0f}x")
    print(f"\n   TOTAL: {total['sin']} de {total['pasadas']} pasadas sin fondo "
          f"({100*total['sin']/total['pasadas']:.0f}%)")

    print("\n\n2) ¿Cuánto recall nos cuesta? Alertas de MIROVA en noches ciegas\n")
    print(f"{'volcán':22s} {'alertas':>8s} {'en noche ciega':>15s} {'%':>6s}")
    print("-" * 56)
    ta = tc = 0
    for v in VOLS:
        rs = pasadas_viirs375(v)
        if not rs:
            continue
        ciego = {}
        for r in rs:
            f = r["datetime_utc"][:10]
            ok = (r.get("diag_n_bg_used_first_pass") or 0) > 0
            ciego[f] = ciego.get(f, True) and not ok
        noches = set()
        for nom in ALIAS.get(v, [v]):
            noches |= gt.get(nom, set())
        # solo las noches que además tuvieron pasada nuestra
        noches = {f for f in noches if f in ciego}
        if not noches:
            continue
        cieg = sum(1 for f in noches if ciego[f])
        ta += len(noches)
        tc += cieg
        print(f"{v:22s} {len(noches):8d} {cieg:15d} {100*cieg/len(noches):5.0f}%")
    if ta:
        print(f"\n   TOTAL: {tc} de {ta} alertas de MIROVA cayeron en noches en que")
        print(f"   no pudimos establecer fondo ({100*tc/ta:.0f}%).")
        print("\n   Comparar contra la tasa base de noches ciegas de arriba: si el")
        print("   porcentaje de alertas-en-noche-ciega es MAYOR que la tasa base,")
        print("   la máscara nos está costando recall de forma sistemática.")

# ─────────────────────────────────────────────────────────────────────────────
# RESULTADO (corrida del 2026-08-27, ventana desde 2026-06-01)
# ─────────────────────────────────────────────────────────────────────────────
#
# PARTE 1 — el mecanismo EXISTE y es de flota, no de un volcán:
#   915 de 4015 pasadas (23 %) quedan sin fondo. En esas, la regla <260 K saca
#   57-69 % del ROI; en las que sí tienen fondo, 2-55 %. El factor va de 1x
#   (Lastarria, Tupungatito: la máscara es agresiva SIEMPRE) hasta 28x (Chaitén).
#   Peor caso: Tupungatito, 41 % de sus pasadas sin fondo.
#
# PARTE 2 — pero NO cuesta el recall que yo predije. REFUTA la generalización:
#   solo 6 de 276 alertas de MIROVA (2 %) caen en noches ciegas, contra una tasa
#   base de ceguera del 23 %. Es DIEZ VECES MENOR que el azar, no mayor.
#
#   Lectura física: las noches que nos ciegan son, en general, noches en que
#   MIROVA tampoco publica — o porque tampoco ve, o porque no hay anomalía.
#   NdC (3 de 6 = 50 %) es la EXCEPCIÓN, y con n=6 esa fracción es frágil.
#
# QUÉ SIGNIFICA PARA LA DECISIÓN
#   La máscara sigue siendo un drift documentado (D14: MISSION.md la declara
#   removida y está activa) y sigue midiendo la cosa equivocada (confunde nieve
#   con nube). Eso no cambió. Lo que se cae es el argumento de que sea CAMINO
#   CRÍTICO por recall: no lo es. Vuelve a ser deuda a pagar después de F70,
#   que era el orden original.
#
#   Lo que sí queda en pie como pendiente concreto: los 6 casos perdidos (3 de
#   ellos en NdC, el volcán que Nicolás está mirando) y el 41 % de ceguera de
#   Tupungatito, que merece su propia mirada.
