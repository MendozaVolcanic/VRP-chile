# -*- coding: utf-8 -*-
"""Tarea 1.13 (estudio C), pregunta 2: las alertas diurnas protegidas, ¿calor volcanico o reflejo solar?

EL FENOMENO. De dia el canal MIR (3,7 a 4 um) suma a la emision termica la radiacion solar reflejada.
Una nube, un salar o un campo de azufre brillante pueden subir el MIR de unos pocos pixeles sin que
haya nada caliente debajo (A76). Un foco volcanico real, en cambio, no depende de la hora: si a las
14 h locales emite 3 MW, en la noche anterior o la siguiente MIROVA lo ve con una magnitud parecida.

EL CRITERIO (sin umbrales inventados, A115). Para cada alerta protegida se mira la ventana de +-72 h
en el mismo volcan, solo pasadas NOCTURNAS de la referencia (las que la replica si procesa):
  - aislada: MIROVA miro de noche y no publico ninguna alerta en la ventana;
  - desproporcionada: su VRP supera en mas de T veces la alerta nocturna mayor del mismo sensor en la
    ventana, donde T sale de los datos: el percentil 95 de esa misma razon medida sobre las alertas
    protegidas NOCTURNAS contra sus vecinas nocturnas (excluyendo las de su misma noche, +-6 h);
  - consistente: lo demas.
"Sospecha de reflejo" = aislada o desproporcionada.

CONTROLES QUE PUEDEN FALLAR (A110):
  N1  el mismo clasificador sobre las protegidas NOCTURNAS (que no pueden ser reflejo): su tasa de
      sospecha es la tasa de falsa sospecha del instrumento. Si la diurna no la supera claramente, el
      instrumento no separa nada.
  N2  control positivo: Nevados de Chillan en erupcion desde el 2026-09-28 (actividad conocida, OVDAS).
      Sus alertas diurnas de esa fase deben salir consistentes; si salen sospechosas, el criterio
      castiga calor real.
  N3  control negativo: la alerta diurna mayor de la base (>= 100 MW) debe salir sospechosa.
  N4  sensibilidad: ventana de +-36 h en vez de +-72 h.
Salida: real_o_reflejo_salida.txt y real_o_reflejo_filas.json.
"""
from __future__ import annotations

import io
import json
import os
import sys
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from pipeline import profile  # noqa: E402
from pipeline.store import _reject_daytime, _solar_elevation  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
from clase_mirova import alerta_protegida, clave_pasada, TIPOS_ALERTA  # noqa: E402

AQUI = Path(__file__).resolve().parent
BUCKET_SENSOR = {"MODIS": "MODIS_TERRA", "VIIRS375": "VIIRS_SNPP", "VIIRS750": "VIIRS_SNPP_750"}
ERUPCION_NDC = "2026-09-28"


def ts(f):
    return datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M").timestamp() / 3600.0  # horas


def cargar():
    with open(ROOT / "volcanoes.yaml", encoding="utf-8") as fh:
        co = {v["name"]: (v["lat"], v["lon"]) for v in yaml.safe_load(fh)["volcanoes"] if "lat" in v}
    filas = cargar_referencia_unificada()
    for f in filas:
        la, lo = co[f["volcano"]]
        dt = datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M")
        e = _solar_elevation(la, lo, dt)
        f["elev_solar"] = round(e, 2)
        f["dia"] = _reject_daytime(BUCKET_SENSOR[f["sensor_bucket"]], e, profile.ENABLE_DAYTIME_MODIS)
        f["t_h"] = ts(f)
    return filas


def indice_nocturno(filas):
    """Por volcan: lista ordenada de pasadas nocturnas (t, sensor, es_alerta, vrp)."""
    por_pasada = {}
    for f in filas:
        if f["dia"]:
            continue
        k = clave_pasada(f)
        es_al = f["tipo"] in TIPOS_ALERTA
        prev = por_pasada.get(k)
        v = f["vrp_mw"] or 0.0
        if prev is None:
            por_pasada[k] = [f["t_h"], f["sensor_bucket"], es_al, v if es_al else 0.0]
        elif es_al:
            prev[2] = True
            prev[3] = max(prev[3], v)
    idx = defaultdict(list)
    for (vol, _s, _m), x in por_pasada.items():
        idx[vol].append(tuple(x))
    for vol in idx:
        idx[vol].sort()
    return idx


def vecinas(idx, f, ventana_h, excluir_h=6.0):
    L = idx[f["volcano"]]
    tiempos = [x[0] for x in L]
    i0, i1 = bisect_left(tiempos, f["t_h"] - ventana_h), bisect_right(tiempos, f["t_h"] + ventana_h)
    return [x for x in L[i0:i1] if abs(x[0] - f["t_h"]) >= excluir_h]


def medir(idx, f, ventana_h):
    vs = vecinas(idx, f, ventana_h)
    al = [x for x in vs if x[2]]
    mismo = [x[3] for x in al if x[1] == f["sensor_bucket"] and x[3] > 0]
    cualq = [x[3] for x in al if x[3] > 0]
    ref = max(mismo) if mismo else (max(cualq) if cualq else None)
    return {"n_miro": len(vs), "n_alertas": len(al), "ref_mw": ref, "ref_mismo_sensor": bool(mismo),
            "razon": (f["vrp_mw"] / ref) if ref else None}


def clasificar(m, T):
    if m["n_miro"] == 0:
        return "sin_cobertura"
    if m["n_alertas"] == 0 or m["ref_mw"] is None:
        return "aislada"
    if m["razon"] > T:
        return "desproporcionada"
    return "consistente"


def correr(filas, idx, ventana_h, p, detalle=False):
    prot = [f for f in filas if alerta_protegida(f, lectura="A")]
    # un registro por pasada (CONS y OCR de la misma pasada cuentan una vez; gana el VRP mayor)
    unicas = {}
    for f in prot:
        k = clave_pasada(f)
        if k not in unicas or f["vrp_mw"] > unicas[k]["vrp_mw"]:
            unicas[k] = f
    prot = list(unicas.values())
    noct = [f for f in prot if not f["dia"]]
    dia = [f for f in prot if f["dia"]]
    razones_noct = []
    for f in noct:
        f["_m"] = medir(idx, f, ventana_h)
        if f["_m"]["razon"] is not None and f["_m"]["ref_mismo_sensor"]:
            razones_noct.append(f["_m"]["razon"])
    T = float(np.percentile(razones_noct, 95))
    p("\n=== ventana +-%d h ===" % ventana_h)
    p("T (p95 de la razon VRP / alerta nocturna vecina mayor del mismo sensor, sobre %d protegidas nocturnas) = %.2f"
      % (len(razones_noct), T))
    p("   mediana de esa razon nocturna: %.2f" % float(np.median(razones_noct)))
    for f in dia:
        f["_m"] = medir(idx, f, ventana_h)
    for grupo, fs in (("NOCTURNAS (N1, no pueden ser reflejo)", noct), ("DIURNAS", dia)):
        c = Counter(clasificar(f["_m"], T) for f in fs)
        sosp = c["aislada"] + c["desproporcionada"]
        base = len(fs) - c["sin_cobertura"]
        p("%s: %d pasadas protegidas -> %s ; sospecha %d de %d = %.1f %%"
          % (grupo, len(fs), dict(sorted(c.items())), sosp, base, 100.0 * sosp / max(base, 1)))
        for s in ("MODIS", "VIIRS375", "VIIRS750"):
            cs = Counter(clasificar(f["_m"], T) for f in fs if f["sensor_bucket"] == s)
            if cs:
                p("      %-8s %s" % (s, dict(sorted(cs.items()))))
    raz_dia = [f["_m"]["razon"] for f in dia if f["_m"]["razon"] is not None and f["_m"]["ref_mismo_sensor"]]
    p("razon diurna (mismo sensor, n=%d): mediana %.2f, p25 %.2f, p75 %.2f"
      % (len(raz_dia), np.median(raz_dia), np.percentile(raz_dia, 25), np.percentile(raz_dia, 75)))

    # N2 control positivo: NdC en erupcion
    ndc = [f for f in dia if f["volcano"] == "NevadosDeChillan" and f["fecha_utc"] >= ERUPCION_NDC]
    cn = Counter(clasificar(f["_m"], T) for f in ndc)
    p("N2 control positivo (NdC diurnas desde %s, erupcion): %s -> %s" % (
        ERUPCION_NDC, dict(cn), "PASA" if ndc and cn["consistente"] >= 0.5 * len(ndc) else "FALLA"))
    # N3 control negativo
    mayor = max(dia, key=lambda f: f["vrp_mw"])
    cl = clasificar(mayor["_m"], T)
    p("N3 control negativo (diurna mayor: %s %s %s %.1f MW, %s): %s -> %s" % (
        mayor["fecha_utc"], mayor["volcano"], mayor["sensor_bucket"], mayor["vrp_mw"], mayor["source"], cl,
        "PASA" if cl in ("aislada", "desproporcionada") else "FALLA"))

    # Por volcan
    p("Diurnas protegidas por volcan y clase:")
    por = defaultdict(Counter)
    for f in dia:
        por[f["volcano"]][clasificar(f["_m"], T)] += 1
    for v in sorted(por):
        p("   %-20s %s" % (v, dict(sorted(por[v].items()))))
    # elevacion contra razon (si es reflejo, la razon deberia crecer con el Sol)
    pares = [(f["elev_solar"], f["_m"]["razon"]) for f in dia if f["_m"]["razon"] is not None]
    if len(pares) > 5:
        a = np.array(pares)
        ra = np.argsort(np.argsort(a[:, 0]))
        rb = np.argsort(np.argsort(a[:, 1]))
        rho = np.corrcoef(ra, rb)[0, 1]
        p("Spearman(elevacion solar, razon) en diurnas: %.2f (n=%d)" % (rho, len(pares)))
    if detalle:
        p("\nDetalle de las diurnas protegidas (una por pasada):")
        p("   %-16s %-18s %-8s %-4s %6s %5s %6s %6s %7s %s" % ("fecha", "volcan", "sensor", "src", "VRP", "elev",
                                                              "n_miro", "n_al", "ref", "clase"))
        for f in sorted(dia, key=lambda f: f["fecha_utc"]):
            m = f["_m"]
            p("   %-16s %-18s %-8s %-4s %6.2f %5.1f %6d %6d %7s %s" % (
                f["fecha_utc"][:16], f["volcano"], f["sensor_bucket"], f["source"], f["vrp_mw"], f["elev_solar"],
                m["n_miro"], m["n_alertas"], "%.2f" % m["ref_mw"] if m["ref_mw"] else "-", clasificar(m, T)))
    return dia, T


def main():
    out = []
    p = out.append
    filas = cargar()
    idx = indice_nocturno(filas)
    p("Referencia unificada: %d filas, %s a %s" % (len(filas), filas[0]["fecha_utc"], filas[-1]["fecha_utc"]))
    dia, T = correr(filas, idx, 72, p, detalle=True)
    dump = [{k: f[k] for k in ("fecha_utc", "volcano", "sensor_bucket", "source", "tipo", "vrp_mw", "dist_km",
                               "elev_solar")} | {"medida": f["_m"], "clase": clasificar(f["_m"], T)} for f in dia]
    correr(filas, idx, 36, p)
    (AQUI / "real_o_reflejo_salida.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    json.dump(dump, open(AQUI / "real_o_reflejo_filas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("\n".join(out))


if __name__ == "__main__":
    main()
