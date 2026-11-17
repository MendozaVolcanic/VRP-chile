# -*- coding: utf-8 -*-
"""Sustrato y vara de cobertura del A/B diurno sobre la vía «código MIROVA» (S190, adenda V, ADENDA_VIA.md §2 y §3.1).

POR QUÉ. La adenda V agrega MODIS y la ventana W7 al A/B de S163. El evaluador necesita, antes de ver un solo dato de
los brazos, dos cosas medidas sobre la referencia congelada:
  * cuántas pasadas diurnas de cada clase (protegida, alerta bajo 1 MW, negativo, otra) trae cada ventana y sensor, con
    la MISMA clasificación de S163 (`sustrato_k.clasificar`: día por elevación solar de `pipeline.store`, clases por
    periodo, pasadas de `clase_mirova.resumir_pasadas`, regla de mínimas SN);
  * la vara de la compuerta I4 (c): de día el control no tiene records, así que la tasa natural de «MIROVA lista la
    pasada y nosotros no tenemos record» se mide de NOCHE en producción. Es el método de S163
    (`sustrato_k.produccion_nocturna`, PREREGISTRO §5 I4): pasadas nocturnas de MIROVA de las ventanas que deciden sin
    record de producción a ±120 s; cota superior de Clopper-Pearson al 95 % de una cola. Aquí, para los tres sensores
    (§3.1 pide MODIS con el mismo método) y sobre W2 a W7. Producción es la vía en los tres sensores, con toda la
    historia de los 11 Tier A desde 2025-02-15 reemplazada por la vía el 2026-11-12 (ficha v1.25), así que la noche de
    producción es la noche de la vía. Los records se leen del COMMIT dado (git show), no del árbol, para que el número
    se pueda reproducir.

Se importa `sustrato_k` y se reusa lo que no depende de la lista de sensores (clasificar, controles, carga de la
referencia). Lo que en S163 recorría sólo VIIRS (contar y produccion_nocturna) se reescribe con la lista de sensores
como parámetro.

Controles que pueden fallar (A110): C1 la regla día/noche (de S163); C2 la partición es exhaustiva; C3 el pareo con
producción encuentra al menos un record nocturno por sensor; C4 (control de instrumento de la adenda §2) W2 a W6 da 26
protegidas diurnas en VIIRS 375 y 6 en VIIRS 750, las del §3 de S163.

Uso:
  python -I experiments/_s163_diurno_k/congelar_referencia.py --commit <40> --salida <REF> --sin-comprobar
  python -I experiments/_s190_diurno/sustrato_via.py --ref <REF> --commit-ref <40> --commit-produccion <40> \
      > experiments/_s190_diurno/sustrato_via_salida.txt
Salida: sustrato_via.json (cuentas, vara, sha256 de los 4 CSV y commits), que el evaluador exige reproducir.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
S163 = ROOT / "experiments" / "_s163_diurno_k"
for _p in (str(ROOT), str(ROOT / "scripts"), str(S163)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import clase_mirova as cm  # noqa: E402
import sustrato_k as sk  # noqa: E402

# Adenda V §2: las ventanas de S163 que deciden más W7. W1 no se corre.
VENTANAS = [tuple(w) for w in sk.VENTANAS if w[0] in sk.DECIDEN] + [("W7", "2026-10-15", "2026-11-15", None)]
DECIDEN = tuple(w[0] for w in VENTANAS)
SENSORES = ("MODIS", "VIIRS375", "VIIRS750")
ALFA = 0.05
# Adenda V §2, control de instrumento: W2 a W6, canal unión, protegidas diurnas (tabla §3 de S163).
PROTEGIDAS_W2_W6_S163 = {"VIIRS375": 26, "VIIRS750": 6}


def contar(clasif, ventana, vols, sensores=SENSORES):
    """sustrato_k.contar con la lista de sensores como parámetro (en S163 recorría sólo VIIRS)."""
    _, desde, hasta, _ = ventana
    cuenta = {s: collections.Counter() for s in sensores}
    bloques = {s: collections.defaultdict(set) for s in sensores}
    for p, dia, c in clasif:
        d = p.instante.strftime("%Y-%m-%d")
        if not dia or p.sensor_bucket not in sensores or not (desde <= d <= hasta):
            continue
        if vols and p.volcano not in vols:
            continue
        cuenta[p.sensor_bucket][c] += 1
        cuenta[p.sensor_bucket]["diurnas"] += 1
        bloques[p.sensor_bucket][c].add("%s|%s" % (p.volcano, d))
    return ({s: dict(cuenta[s]) for s in sensores},
            {s: {c: len(b) for c, b in bloques[s].items()} for s in sensores})


def records_de_commit(commit, vols):
    """(volcán, sensor) -> instantes ordenados de los records de producción en `commit` (git show)."""
    import banco_paridad as bp
    idx = collections.defaultdict(list)
    for vol in vols:
        r = subprocess.run(["git", "-C", str(ROOT), "show", "%s:data/mirova_equivalent/%s.json" % (commit, vol)],
                           capture_output=True, check=True)
        for rec in json.loads(r.stdout.decode("utf-8"))["records"]:
            b = bp.bucket(rec.get("sensor"))
            try:
                idx[(vol, b)].append(datetime.strptime(rec.get("datetime_utc", ""), "%Y-%m-%d %H:%M"))
            except ValueError:
                continue
    for v in idx.values():
        v.sort()
    return idx


def produccion_nocturna(clasif, idx, ventanas=VENTANAS, sensores=SENSORES):
    """sustrato_k.produccion_nocturna con sensores, ventanas e índice de records como parámetros: pasadas NOCTURNAS de
    MIROVA de las ventanas sin record de producción a ±120 s, por sensor."""
    res = {}
    for s in sensores:
        tot = sin = 0
        ejemplo = None
        for p, dia, _ in clasif:
            d = p.instante.strftime("%Y-%m-%d")
            if dia or p.sensor_bucket != s or not any(w[1] <= d <= w[2] for w in ventanas):
                continue
            ts = idx.get((p.volcano, s), [])
            t = p.instante.replace(tzinfo=None)
            i = bisect.bisect_left(ts, t - timedelta(seconds=cm.VENTANA_S))
            hay = i < len(ts) and ts[i] <= t + timedelta(seconds=cm.VENTANA_S)
            tot += 1
            sin += 0 if hay else 1
            if hay and ejemplo is None:
                ejemplo = (p.volcano, s, t.strftime("%Y-%m-%d %H:%M"))
        res[s] = {"pasadas_nocturnas": tot, "sin_record_produccion": sin, "ejemplo_con_record": ejemplo}
    return res


def p_sup(sin, n):
    """Cota superior de Clopper-Pearson al 95 % (una cola), la fórmula de evaluar_diurno_k.p_sup_de_vara."""
    from scipy.stats import beta
    return float(beta.ppf(1 - ALFA, sin + 1, n - sin))


def umbral_i4c(n, ps):
    """La menor cantidad X de pasadas diurnas sin record con la que I4c falla: P(Bin(n, ps) >= X) < 0,05."""
    from scipy.stats import binom
    for x in range(1, n + 1):
        if binom.sf(x - 1, n, ps) < ALFA:
            return x
    return None


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="carpeta con los 4 CSV extraídos de un commit (congelar_referencia.py)")
    ap.add_argument("--commit-ref", required=True, help="commit del que se extrajo --ref (40 caracteres)")
    ap.add_argument("--commit-produccion", required=True, help="commit del que se leen los records de producción")
    ap.add_argument("--salida", default=str(AQUI / "sustrato_via.json"))
    a = ap.parse_args(argv)
    import banco_paridad as bp
    coords = bp._coords_por_volcan()
    prob = sk.controles(coords)
    ref = Path(a.ref)
    filas = sk.cargar_ref(ref)
    print("referencia: %d filas, %s a %s (commit %s)" % (len(filas), min(f["fecha_utc"] for f in filas),
                                                       max(f["fecha_utc"] for f in filas), a.commit_ref))
    out = {"commit_referencia": a.commit_ref, "commit_produccion": a.commit_produccion,
           "sha256": {n: sk.sha256(ref / n) for n in sk.ARCHIVOS_REF},
           "ventanas_def": [list(w[:3]) for w in VENTANAS], "canales": {}}
    for canal in ("union", "tabla"):
        pas = cm.resumir_pasadas(filas, canal=canal, regla_minimas=cm.MODO_MINIMAS)
        clasif = sk.clasificar(pas, coords)
        print("\n=== canal %s: %d pasadas, %d diurnas (todos los sensores y fechas)"
              % (canal, len(clasif), sum(1 for _, d, _ in clasif if d)))
        vent = {}
        for w in VENTANAS:
            cuenta, bloques = contar(clasif, w, w[3])
            vent[w[0]] = {"desde": w[1], "hasta": w[2], "cuenta": cuenta, "bloques": bloques}
            for s in SENSORES:
                c = cuenta[s]
                if sum(c.get(k, 0) for k in ("protegida", "alerta_mb", "negativo", "otra")) != c.get("diurnas", 0):
                    prob.append("C2: %s %s %s: las clases no suman las diurnas" % (canal, w[0], s))
                print("%s %-8s %s a %s | diurnas %5d | protegidas %3d | alerta_mb %3d | negativos %5d (%4d bloques) "
                      "| otra %4d" % (w[0], s, w[1], w[2], c.get("diurnas", 0), c.get("protegida", 0),
                                      c.get("alerta_mb", 0), c.get("negativo", 0), bloques[s].get("negativo", 0),
                                      c.get("otra", 0)))
        tot = {s: collections.Counter() for s in SENSORES}
        tot26 = {s: collections.Counter() for s in SENSORES}
        for w in DECIDEN:
            for s in SENSORES:
                tot[s].update(vent[w]["cuenta"][s])
                if w != "W7":
                    tot26[s].update(vent[w]["cuenta"][s])
        print("Total W2 a W7:", {s: dict(tot[s]) for s in SENSORES})
        print("Total W2 a W6:", {s: dict(tot26[s]) for s in SENSORES})
        out["canales"][canal] = {"ventanas": vent, "total_que_decide": {s: dict(tot[s]) for s in SENSORES},
                                 "total_W2_W6": {s: dict(tot26[s]) for s in SENSORES}}
        if canal != "union":
            continue
        for s, n in PROTEGIDAS_W2_W6_S163.items():
            if tot26[s].get("protegida", 0) != n:
                prob.append("C4: W2 a W6 %s: %d protegidas diurnas, S163 tenía %d"
                            % (s, tot26[s].get("protegida", 0), n))
        idx = records_de_commit(a.commit_produccion, bp.VOLS)
        vara = produccion_nocturna(clasif, idx)
        vara26 = produccion_nocturna(clasif, idx, ventanas=[w for w in VENTANAS if w[0] != "W7"])
        print()
        for s in SENSORES:
            r = vara[s]
            if r["ejemplo_con_record"] is None:
                prob.append("C3: %s: el pareo con producción no encontró ningún record nocturno" % s)
            r["p_sup"] = p_sup(r["sin_record_produccion"], r["pasadas_nocturnas"])
            n_dia = tot[s].get("diurnas", 0)
            r["pasadas_diurnas_W2_W7"] = n_dia
            r["i4c_falla_desde"] = umbral_i4c(n_dia, r["p_sup"]) if n_dia else None
            print("vara I4c %-8s: %d de %d pasadas nocturnas de MIROVA (W2 a W7) sin record de producción, p_sup %.5f; "
                  "con %d pasadas diurnas, I4c falla desde %s sin record | (W2 a W6: %d de %d)"
                  % (s, r["sin_record_produccion"], r["pasadas_nocturnas"], r["p_sup"], n_dia, r["i4c_falla_desde"],
                     vara26[s]["sin_record_produccion"], vara26[s]["pasadas_nocturnas"]))
        out["vara_cobertura_nocturna_produccion"] = vara
        out["vara_W2_W6_informativa"] = vara26
        out["protegidas_diurnas"] = sorted(
            "%s|%s|%s|%s|%s" % (p.volcano, p.sensor_bucket, p.instante.strftime("%Y-%m-%d %H:%M:%S"), p.fuente,
                                p.vrp_mw)
            for p, dia, c in clasif if dia and c == "protegida" and p.sensor_bucket in SENSORES
            and any(w[1] <= p.instante.strftime("%Y-%m-%d") <= w[2] for w in VENTANAS))
    if prob:
        print("\nCONTROLES FALLIDOS:")
        for x in prob:
            print("  ", x)
        return 1
    print("\ncontroles C1, C2, C3, C4: OK")
    Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
