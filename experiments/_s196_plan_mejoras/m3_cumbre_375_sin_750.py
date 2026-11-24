# -*- coding: utf-8 -*-
"""Medición previa de la mejora 3 del plan S196: cumbres tibias que VIIRS 375 publica y VIIRS 750 calla.

POR QUÉ. Un foco chico (unos cientos de metros) llena una fracción mayor de un píxel de 375 m que de uno de 750 m: el
mismo calor queda diluido a la cuarta parte en el 750 y puede no cruzar su umbral. MIROVA lo vive igual, y la réplica
también. Antes de diseñar nada en el laboratorio hay que saber (1) cuántas pasadas nocturnas de producción tienen esa
forma (el 375 publica y el 750 del mismo satélite y la misma hora no) y (2) si SWIR (NHI-v1, Sentinel 2 y Landsat) ve
más calor esas noches que las noches en que ninguno de los dos publica. Si (2) no se separa del nulo, el 750 no está
callando calor real que SWIR confirme, y la mejora pierde prioridad.

Qué hace, sin reprocesar nada:
- lee `data/mirova_equivalent/` (la vía de producción) con el predicado del tablero de `scripts/banco_paridad.py`
  (`correr_node`, el mismo JavaScript que el navegador), sólo pasadas nocturnas;
- parea cada pasada VIIRS 375 con la VIIRS 750 del mismo satélite a 120 s o menos (`clase_mirova.VENTANA_S`);
- clasifica cada noche (volcán y fecha UTC) en: «solo375» (alguna pasada publica en 375 y su par 750 no, y ninguna
  pasada 750 publica esa noche), «750» (alguna 750 publica), «ninguno» (ninguna VIIRS publica);
- para cada noche con una escena NHI válida a ±1 día (caja usable, `nhi_cajas.json` de S195), toma si alguna de esas
  escenas tiene alerta, y compara la tasa de alerta NHI entre las tres clases, por volcán;
- control del instrumento (A110): el mismo cálculo con las fechas NHI corridas 15 días.

No decide nada: dice si vale la pena el pre-registro. Uso:
  python experiments/_s196_plan_mejoras/m3_cumbre_375_sin_750.py --nhi-dir <carpeta de bajar_nhi.py>
"""
import argparse
import collections
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp  # noqa: E402
from clase_mirova import VENTANA_S  # noqa: E402

CAJAS = ROOT / "experiments" / "_s195_viirs_dia_control" / "nhi_cajas.json"


def cargar(desde, hasta):
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    recs, casos = [], []
    for vol in bp.VOLS:
        for r in json.loads((bp.DATA / ("%s.json" % vol)).read_text(encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor"))
            t = r.get("datetime_utc", "")
            if b not in ("VIIRS375", "VIIRS750") or not (desde <= t[:10] <= hasta):
                continue
            try:
                dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            lat, lon = coords[vol]
            if bp.es_pasada_diurna_descartada(b, lat, lon, dt.replace(tzinfo=__import__("datetime").timezone.utc)):
                continue
            recs.append({"vol": vol, "b": b, "dt": dt, "plat": (r.get("sensor") or "").replace("_750", ""),
                         "npix": r.get("n_anomalous_pixels"), "z": r.get("sensor_zenith_deg")})
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    for rec, p in zip(recs, bp.correr_node(casos)):
        rec["disp"], rec["pub"] = p[3], p[4]
    return recs


def clasificar(recs):
    por_clave = collections.defaultdict(list)
    for r in recs:
        if r["b"] == "VIIRS750":
            por_clave[(r["vol"], r["plat"])].append(r)
    pasadas = collections.Counter()
    noches = collections.defaultdict(lambda: {"solo375": False, "750": False, "algo": False})
    solo = []
    for r in recs:
        n = noches[(r["vol"], r["dt"].date())]
        n["algo"] = True
        if r["b"] == "VIIRS750":
            if r["pub"]:
                n["750"] = True
            continue
        par = [x for x in por_clave[(r["vol"], r["plat"])] if abs((x["dt"] - r["dt"]).total_seconds()) <= VENTANA_S]
        if not par:
            pasadas["375_sin_par_750"] += 1
            continue
        p750 = any(x["pub"] for x in par)
        if r["pub"] and not p750:
            pasadas["solo375"] += 1
            n["solo375"] = True
            solo.append(r)
        elif r["pub"] and p750:
            pasadas["ambos"] += 1
        elif p750:
            pasadas["solo750"] += 1
        else:
            pasadas["ninguno"] += 1
    clase = {}
    for k, n in noches.items():
        clase[k] = "750" if n["750"] else ("solo375" if n["solo375"] else "ninguno")
    return pasadas, clase, solo


def tasas_nhi(clase, nhi, cajas, corrimiento=0):
    out = collections.defaultdict(lambda: collections.Counter())
    for (vol, d0), c in clase.items():
        caja = cajas.get(vol)
        if not caja or not caja["usable"] or vol not in nhi:
            continue
        val = [e for e in nhi[vol] if e.get("alerta") is not None
               and abs((date.fromisoformat(e["fecha"][:10]) + timedelta(days=corrimiento) - d0).days) <= 1]
        if not val:
            continue
        out[vol][(c, "n")] += 1
        if any(e["alerta"] is True for e in val):
            out[vol][(c, "alerta")] += 1
    return out


def imprimir(t, titulo):
    print("\n" + titulo)
    print("%-20s %22s %22s %22s" % ("volcán", "ninguno (alerta/n)", "solo375 (alerta/n)", "750 (alerta/n)"))
    tot = collections.Counter()
    for vol in bp.VOLS:
        if vol not in t:
            continue
        fila = []
        for c in ("ninguno", "solo375", "750"):
            n, a = t[vol][(c, "n")], t[vol][(c, "alerta")]
            tot[(c, "n")] += n
            tot[(c, "alerta")] += a
            fila.append("%d/%d (%s)" % (a, n, ("%.0f %%" % (100.0 * a / n)) if n else "-"))
        print("%-20s %22s %22s %22s" % (vol, *fila))
    fila = ["%d/%d (%s)" % (tot[(c, "alerta")], tot[(c, "n")],
                            ("%.0f %%" % (100.0 * tot[(c, "alerta")] / tot[(c, "n")])) if tot[(c, "n")] else "-")
            for c in ("ninguno", "solo375", "750")]
    print("%-20s %22s %22s %22s" % ("TOTAL (agrupado)", *fila))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nhi-dir", required=True)
    ap.add_argument("--desde", default="2026-03-01")
    ap.add_argument("--hasta", default="2026-11-22")
    a = ap.parse_args()
    import yaml
    vy = {v["name"]: v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    cj = json.loads(CAJAS.read_text(encoding="utf-8"))
    cajas = {}
    for vol, c in cj["volcanes"].items():
        if c.get("en_nhi"):
            dlat = c["buffer_km"] / 111.0
            import math
            dlon = c["buffer_km"] / (111.0 * abs(math.cos(math.radians(c["lat"]))))
            cajas[vol] = dict(c, usable=abs(vy[vol]["lat"] - c["lat"]) <= dlat and abs(vy[vol]["lon"] - c["lon"]) <= dlon)
    nhi = {}
    for vol, c in cajas.items():
        ruta = Path(a.nhi_dir) / c["nombre_nhi"] / "nhi_timeseries.json"
        if ruta.exists():
            nhi[vol] = [e for e in json.loads(ruta.read_text(encoding="utf-8")) if e.get("fecha")]
    commit = (Path(a.nhi_dir) / "COMMIT.txt").read_text(encoding="utf-8").strip()
    print("ventana %s a %s; producción data/mirova_equivalent; NHI-v1 commit %s; cajas %s" % (
        a.desde, a.hasta, commit, cj.get("commit_nhi")))
    print("cajas NHI usables: %s" % sorted(k for k, c in cajas.items() if c["usable"]))
    recs = cargar(a.desde, a.hasta)
    pasadas, clase, solo = clasificar(recs)
    print("\nPASADAS VIIRS 375 nocturnas por clase (par 750 del mismo satélite a <= %d s):" % VENTANA_S)
    for k, n in sorted(pasadas.items()):
        print("  %-18s %d" % (k, n))
    print("\nPASADAS solo375 por volcán, con número de píxeles alertados del 375 y potencia del tablero (MW):")
    pv = collections.defaultdict(list)
    for r in solo:
        pv[r["vol"]].append(r)
    for vol in bp.VOLS:
        L = pv.get(vol, [])
        if not L:
            continue
        mw = sorted(x["disp"] for x in L)
        npx = collections.Counter(min(x["npix"] or 0, 3) for x in L)
        print("  %-20s %4d  mediana %.2f MW, máx %.2f MW; píxeles 1:%d 2:%d 3+:%d" % (
            vol, len(L), mw[len(mw) // 2], mw[-1], npx[1], npx[2], npx[3]))
    cn = collections.Counter(clase.values())
    print("\nNOCHES por clase: %s" % dict(sorted(cn.items())))
    imprimir(tasas_nhi(clase, nhi, cajas), "TASA DE ALERTA NHI a ±1 día por clase de noche (sólo cajas usables)")
    imprimir(tasas_nhi(clase, nhi, cajas, corrimiento=15),
             "CONTROL: fechas NHI corridas +15 días (debería no separar las clases si el instrumento no mide estación)")


if __name__ == "__main__":
    main()
