# -*- coding: utf-8 -*-
"""S194, laboratorio por áreas, opción A (partición posterior): reparte entre cráter, agua, flanco y resto los
alertados que cada record de la vía «código MIROVA» ya guarda, sin tocar la detección.

Diseño: docs/superpowers/specs/2026-11-22-laboratorio-areas-design.md (rama loop/activo). Áreas:
config/areas_laboratorio.yaml. Informe: experiments/_s194_areas/INFORME.md.

POR QUÉ: cada pasada se publica como un punto (regla «radiante», el cúmulo más radiante), y eso esconde calor
simultáneo en otras zonas de la grilla de 51 x 51 km. Repartir los alertados por área dice, con lo que ya está
publicado, cuántas pasadas tienen calor a la vez en el cráter y fuera de él, y cuánto se alerta sobre agua (control
negativo, A110).

VRP por área. Los records NO guardan VRP por píxel: anomaly_pixels trae lat, lon, dist_km, bt_k, fila y col. El .m
calcula VRP = coef x (L_hot - L_bk) con L_hot = suma de la radiancia MIR de los alertados y L_bk = suma del fondo
interpolado bajo ellos (pipeline/mirova_v750_codigo.py::vrp_mirova), y el record guarda L_hot y L_bk totales en
diag_codigo_mirova. Aquí la radiancia de cada píxel se recupera exacta (salvo el redondeo de bt_k a 0,01 K) invirtiendo
Planck con la misma función del port, y el fondo total se reparte por partes iguales entre los alertados
(L_bk / n). Por construcción la suma de las áreas da el VRP del record (D32); lo que es aproximado es el REPARTO del
fondo entre áreas, porque el fondo real cambia de un píxel a otro (no se guarda por píxel). El control de cierre
comprueba la suma con una tolerancia derivada del redondeo de bt_k, no elegida a ojo.

Uso:
    python experiments/_s194_areas/particion.py [--raiz RUTA_REPO] [--salida DIR_TEMPORAL]
Salidas versionadas: experiments/_s194_areas/resumen.json y particion_salida.txt. Salidas grandes (tabla por pasada
y por píxel) en --salida (por defecto D:/vrp-trabajo/temporales/s194_areas).
"""
from __future__ import annotations

import argparse
import collections
import csv
import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml
from matplotlib.path import Path as MplPath

AQUI = Path(__file__).resolve().parent
RAIZ_DEF = AQUI.parents[1]
sys.path.insert(0, str(RAIZ_DEF))
from pipeline.mirova_v750_codigo import FAMILIAS, temperatura_a_radiancia  # noqa: E402

AREAS = ("crater", "agua", "flanco", "resto")
DESDE = "2025-02-15"
KM_LAT = 110.574          # km por grado de latitud (proyección local equirectangular, sólo para medir bordes en km)
KM_LON_EQ = 111.320       # km por grado de longitud en el ecuador


def familia_de(sensor: str) -> str:
    """MODIS_TERRA/AQUA -> MODIS; VIIRS_*_750 -> VIIRS750; VIIRS_SNPP/NOAA20/NOAA21 -> VIIRS375 (A48)."""
    if sensor.startswith("MODIS"):
        return "MODIS"
    return "VIIRS750" if sensor.endswith("_750") else "VIIRS375"


class Lago:
    """Un polígono de agua (anillo exterior y huecos, las islas) en km locales.

    POR QUÉ sin shapely: shapely no está en requirements.txt, y la prueba de la partición corre en el CI; agregarlo
    cambiaría el entorno de los workflows de producción por un experimento. matplotlib (ya requerido) trae el test de
    punto en polígono; la distancia al borde se calcula a mano sobre los segmentos."""

    def __init__(self, anillos_km):
        self.anillos = [np.asarray(a, float) for a in anillos_km]
        self.ext = MplPath(self.anillos[0])
        self.huecos = [MplPath(a) for a in self.anillos[1:]]
        xs, ys = self.anillos[0][:, 0], self.anillos[0][:, 1]
        self.bbox = (xs.min(), ys.min(), xs.max(), ys.max())

    def contiene(self, x, y):
        b = self.bbox
        if not (b[0] <= x <= b[2] and b[1] <= y <= b[3]):
            return False
        return self.ext.contains_point((x, y)) and not any(h.contains_point((x, y)) for h in self.huecos)

    def contiene_varios(self, xy):
        m = self.ext.contains_points(xy)
        for h in self.huecos:
            m &= ~h.contains_points(xy)
        return m

    @staticmethod
    def _area_anillo(a):
        x, y = a[:, 0], a[:, 1]
        return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

    def area_km2(self):
        return self._area_anillo(self.anillos[0]) - sum(self._area_anillo(a) for a in self.anillos[1:])

    def punto_interior(self, paso=0.05):
        """El punto de una malla fina dentro del polígono más alejado de su borde (posición representativa)."""
        b = self.bbox
        gx, gy = np.meshgrid(np.arange(b[0], b[2] + paso, paso), np.arange(b[1], b[3] + paso, paso))
        xy = np.column_stack([gx.ravel(), gy.ravel()])
        xy = xy[self.contiene_varios(xy)]
        if not len(xy):
            return float(self.anillos[0][0, 0]), float(self.anillos[0][0, 1])
        seg = _segmentos(self.anillos)
        d = np.array([_dist_min(seg, x, y) for x, y in xy])
        i = int(np.argmax(d))
        return float(xy[i, 0]), float(xy[i, 1])


def _segmentos(anillos):
    s = [np.column_stack([a[:-1], a[1:]]) for a in anillos if len(a) > 1]
    return np.vstack(s) if s else np.zeros((0, 4))


def _dist_min(seg, x, y):
    """Distancia mínima (km) del punto (x, y) a un conjunto de segmentos [x1, y1, x2, y2]."""
    if not len(seg):
        return math.inf
    x1, y1, x2, y2 = seg[:, 0], seg[:, 1], seg[:, 2], seg[:, 3]
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = np.clip(np.where(L2 > 0, ((x - x1) * dx + (y - y1) * dy) / np.where(L2 > 0, L2, 1), 0.0), 0.0, 1.0)
    return float(np.sqrt(np.min((x1 + t * dx - x) ** 2 + (y1 + t * dy - y) ** 2)))


class Areas:
    """Geometría de las áreas de un volcán. Coordenadas locales en km (x este, y norte) centradas en el cráter."""

    def __init__(self, volcan: str, raiz: Path, conf: dict, vol_yaml: dict):
        v = vol_yaml
        self.volcan = volcan
        self.inner_km = float(v["inner_radius_km"])
        c = conf["volcanes"][volcan]
        self.flanco_km = float(c.get("radio_flanco_km", conf["radio_flanco_km_defecto"]))
        self.lat0 = float(v.get("vent_lat", v["lat"]))
        self.lon0 = float(v.get("vent_lon", v["lon"]))
        self.kx = KM_LON_EQ * math.cos(math.radians(self.lat0))
        gj = json.loads((raiz / c["agua"]).read_text(encoding="utf-8"))
        self.lagos = []
        for f in gj["features"]:
            g = f["geometry"]
            polis = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]   # MultiPolygon, por si acaso
            for anillos in polis:
                self.lagos.append(Lago([[self.a_km(la, lo) for lo, la in a] for a in anillos]))
        self.agua = bool(self.lagos)
        self._seg = _segmentos([a for L in self.lagos for a in L.anillos])

    def a_km(self, lat, lon):
        return (lon - self.lon0) * self.kx, (lat - self.lat0) * KM_LAT

    def lago_de(self, lat, lon):
        x, y = self.a_km(lat, lon)
        for i, g in enumerate(self.lagos):
            if g.contiene(x, y):
                return i
        return None

    def asignar(self, lat: float, lon: float, dist_km: float, medio_paso_km: float):
        """Devuelve (área, en_borde). Precedencia cráter > agua > flanco > resto (config/areas_laboratorio.yaml).

        POR QUÉ el cráter usa dist_km y no la distancia geográfica: dist_km es la distancia que guarda la vía, medida en
        la grilla desde la posición del cráter, y es la que decide distance_class; así el cráter de la partición es la
        «cumbre» del tablero. en_borde: el píxel está a menos de media celda de un borde que le cambiaría el área (una
        celda de 1 km, 750 m o 375 m no cabe entera en un área; crítica §9.2 del diseño)."""
        if dist_km <= self.inner_km:
            return "crater", abs(dist_km - self.inner_km) < medio_paso_km
        cerca_crater = abs(dist_km - self.inner_km) < medio_paso_km
        if self.lago_de(lat, lon) is not None:
            return "agua", cerca_crater or self._cerca_agua(lat, lon, medio_paso_km)
        cerca_agua = self.agua and self._cerca_agua(lat, lon, medio_paso_km)
        if dist_km <= self.flanco_km:
            return "flanco", cerca_crater or cerca_agua or abs(dist_km - self.flanco_km) < medio_paso_km
        return "resto", cerca_agua or abs(dist_km - self.flanco_km) < medio_paso_km

    def _cerca_agua(self, lat, lon, h):
        x, y = self.a_km(lat, lon)
        s = self._seg
        m = ((np.minimum(s[:, 0], s[:, 2]) - h <= x) & (x <= np.maximum(s[:, 0], s[:, 2]) + h)
             & (np.minimum(s[:, 1], s[:, 3]) - h <= y) & (y <= np.maximum(s[:, 1], s[:, 3]) + h))
        return _dist_min(s[m], x, y) < h


def radiancia_pixel(bt_k: float, fam: str) -> float:
    return float(temperatura_a_radiancia(np.array([bt_k]), FAMILIAS[fam]["lam_mir"])[0])


def tolerancia_cierre(bts, fam: str) -> float:
    """Cota del error de cierre por el redondeo de bt_k a 0,01 K (error <= 0,005 K por píxel) más el redondeo de
    vrp_mw a 0,001 MW. POR QUÉ acotada a su física: |dL/dT| x 0,005 K por píxel, sumado, por el coeficiente."""
    lam = FAMILIAS[fam]["lam_mir"]
    coef = FAMILIAS[fam]["coef"]
    s = 0.0
    for t in bts:
        d = float(temperatura_a_radiancia(np.array([t + 0.005]), lam)[0] - temperatura_a_radiancia(np.array([t - 0.005]), lam)[0])
        s += abs(d) / 2.0
    return coef * s + 0.0005 + 1e-9


def repartir(rec: dict, areas: Areas) -> dict:
    """Reparte un record de la vía entre áreas. Devuelve por área n, vrp_mw y el alertado más fuerte, más el control
    de cierre y los píxeles con su área."""
    fam = familia_de(rec["sensor"])
    coef = FAMILIAS[fam]["coef"]
    medio = FAMILIAS[fam]["paso_m"] / 2000.0
    ap = rec.get("anomaly_pixels") or []
    dg = rec.get("diag_codigo_mirova") or {}
    n = len(ap)
    out = {a: {"n": 0, "vrp_mw": 0.0, "max_bt_k": None, "max_L": None, "max_dist_km": None} for a in AREAS}
    pix = []
    if n == 0:
        return {"areas": out, "pix": pix, "cierre_ok": True, "cierre_err": 0.0, "tol": 0.0, "fam": fam}
    l_bk = float(dg["L_bk"])
    bk_cada = l_bk / n
    suma_l = 0.0
    for q in ap:
        L = radiancia_pixel(q["bt_k"], fam)
        suma_l += L
        area, borde = areas.asignar(q["lat"], q["lon"], q["dist_km"], medio)
        o = out[area]
        o["n"] += 1
        o["vrp_mw"] += coef * (L - bk_cada)
        if o["max_L"] is None or L > o["max_L"]:
            o.update({"max_L": L, "max_bt_k": q["bt_k"], "max_dist_km": q["dist_km"]})
        lago = areas.lago_de(q["lat"], q["lon"]) if area == "agua" else None
        pix.append({"lat": q["lat"], "lon": q["lon"], "dist_km": q["dist_km"], "bt_k": q["bt_k"], "area": area,
                    "borde": borde, "lago": lago, "vrp_px_mw": coef * (L - bk_cada)})
    suma = sum(o["vrp_mw"] for o in out.values())
    tol = tolerancia_cierre([q["bt_k"] for q in ap], fam)
    err = abs(suma - float(rec["vrp_mw"]))
    # vrp_mw del record se lleva a 0 si la suma es negativa (pipeline/store.py, A10 marca S190): no se compara ahí.
    ok = err <= tol or (float(rec["vrp_mw"]) == 0.0 and coef * (suma_l - l_bk) < 0)
    return {"areas": out, "pix": pix, "cierre_ok": ok, "cierre_err": err, "tol": tol, "fam": fam,
            "err_lhot_rel": abs(suma_l - float(dg["L_hot"])) / max(abs(float(dg["L_hot"])), 1e-12)}


def es_nocturna(rec: dict) -> bool:
    """Sólo pasadas nocturnas: dayflag 0 del .m y Sol bajo el horizonte. Excluye las diurnas que entran con #1090."""
    dg = rec.get("diag_codigo_mirova") or {}
    if dg.get("dayflag") not in (0, None):
        return False
    sza = rec.get("solar_zenith_deg")
    return sza is None or sza > 90


def noche_de(dt: str) -> str:
    """Noche local de Chile: una pasada antes de las 12 UTC pertenece a la noche que empezó el día anterior."""
    import datetime as _d
    t = _d.datetime.strptime(dt[:16], "%Y-%m-%d %H:%M")
    return (t - _d.timedelta(hours=12)).strftime("%Y-%m-%d")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=str(RAIZ_DEF))
    ap.add_argument("--salida", default="D:/vrp-trabajo/temporales/s194_areas")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    raiz = Path(args.raiz)
    sal = Path(args.salida)
    sal.mkdir(parents=True, exist_ok=True)
    conf = yaml.safe_load((raiz / "config" / "areas_laboratorio.yaml").read_text(encoding="utf-8"))
    vy = {v["name"]: v for v in yaml.safe_load((raiz / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}

    resumen = {"desde": DESDE, "volcanes": {}, "controles": {}}
    ctl = collections.Counter()
    peor_cierre = []
    f_pasadas = gzip.open(sal / "pasadas.csv.gz", "wt", encoding="utf-8", newline="")
    f_pix = gzip.open(sal / "pixeles.csv.gz", "wt", encoding="utf-8", newline="")
    cols_p = ["volcan", "sensor", "familia", "datetime_utc", "noche", "distance_class", "vrp_mw", "n_alertados"]
    for a in AREAS:
        cols_p += [f"{a}_n", f"{a}_vrp_mw", f"{a}_max_bt_k", f"{a}_max_dist_km"]
    wp = csv.DictWriter(f_pasadas, fieldnames=cols_p)
    wp.writeheader()
    wx = csv.DictWriter(f_pix, fieldnames=["volcan", "sensor", "familia", "datetime_utc", "noche", "distance_class",
                                           "lat", "lon", "dist_km", "bt_k", "area", "borde", "lago", "vrp_px_mw"])
    wx.writeheader()

    for volcan in conf["volcanes"]:
        areas = Areas(volcan, raiz, conf, vy[volcan])
        d = json.loads((raiz / "data" / "mirova_equivalent" / f"{volcan}.json").read_text(encoding="utf-8"))
        porfam = collections.defaultdict(lambda: collections.Counter())
        lagos = collections.defaultdict(lambda: {"pasadas": 0, "noches": set(), "max_bt_k": 0.0, "vrp_mw": 0.0,
                                                  "familias": collections.Counter()})
        vrp_area = collections.defaultdict(lambda: collections.Counter())
        for r in d["records"]:
            if r.get("via_codigo_mirova") is not True or r.get("datetime_utc", "") < DESDE:
                continue
            if not es_nocturna(r):
                ctl["excluidas_diurnas"] += 1
                continue
            fam = familia_de(r["sensor"])
            c = porfam[fam]
            c["pasadas"] += 1
            n = r.get("n_anomalous_pixels") or 0
            apx = r.get("anomaly_pixels") or []
            if n != len(apx):
                ctl["anomaly_pixels_incompleto"] += 1
            if not n:
                continue
            c["con_deteccion"] += 1
            ctl["records_con_alertados"] += 1
            p = repartir(r, areas)
            ctl["cierre_ok" if p["cierre_ok"] else "cierre_falla"] += 1
            ctl["max_err_lhot_rel_x1e6"] = max(ctl["max_err_lhot_rel_x1e6"], int(p["err_lhot_rel"] * 1e6))
            peor_cierre.append((p["cierre_err"] / p["tol"] if p["tol"] else 0.0, volcan, r["datetime_utc"], r["sensor"],
                                p["cierre_err"], p["tol"]))
            noche = noche_de(r["datetime_utc"])
            con = {a for a in AREAS if p["areas"][a]["n"]}
            for a in con:
                c[f"con_{a}"] += 1
                vrp_area[fam][a] += p["areas"][a]["vrp_mw"]
            vrp_area[fam]["total_record"] += float(r["vrp_mw"])
            if "crater" in con and len(con) > 1:
                c["crater_y_otra"] += 1
                for a in con - {"crater"}:
                    c[f"crater_y_{a}"] += 1
                if r.get("distance_class") == "far":
                    c["crater_y_otra_publicada_lejana"] += 1
            if "crater" not in con:
                c["sin_crater"] += 1
            if r.get("distance_class") == "far" and "crater" in con:
                c["lejana_con_crater"] += 1
            if r.get("distance_class") == "far":
                c["lejanas"] += 1
            nb = sum(1 for q in p["pix"] if q["borde"])
            c["pixeles"] += len(p["pix"])
            c["pixeles_borde"] += nb
            if nb:
                c["pasadas_con_pixel_borde"] += 1
            for q in p["pix"]:
                if q["lago"] is not None:
                    L = lagos[q["lago"]]
                    L["noches"].add(noche)
                    L["max_bt_k"] = max(L["max_bt_k"], q["bt_k"])
                    L["familias"][fam] += 1
            for i in {q["lago"] for q in p["pix"] if q["lago"] is not None}:
                lagos[i]["pasadas"] += 1
                lagos[i]["vrp_mw"] += sum(q["vrp_px_mw"] for q in p["pix"] if q["lago"] == i)
            fila = {"volcan": volcan, "sensor": r["sensor"], "familia": fam, "datetime_utc": r["datetime_utc"],
                    "noche": noche, "distance_class": r.get("distance_class"), "vrp_mw": r["vrp_mw"], "n_alertados": n}
            for a in AREAS:
                o = p["areas"][a]
                fila.update({f"{a}_n": o["n"], f"{a}_vrp_mw": round(o["vrp_mw"], 4), f"{a}_max_bt_k": o["max_bt_k"],
                             f"{a}_max_dist_km": o["max_dist_km"]})
            wp.writerow(fila)
            for q in p["pix"]:
                wx.writerow({"volcan": volcan, "sensor": r["sensor"], "familia": fam, "datetime_utc": r["datetime_utc"],
                             "noche": noche, "distance_class": r.get("distance_class"), "lat": q["lat"],
                             "lon": q["lon"], "dist_km": q["dist_km"], "bt_k": q["bt_k"], "area": q["area"],
                             "borde": int(q["borde"]), "lago": "" if q["lago"] is None else q["lago"],
                             "vrp_px_mw": round(q["vrp_px_mw"], 5)})
        lagos_out = []
        for i, L in sorted(lagos.items(), key=lambda kv: -kv[1]["pasadas"]):
            g = areas.lagos[i]
            x, y = g.punto_interior()
            lagos_out.append({"lago": i, "lat": round(areas.lat0 + y / KM_LAT, 4),
                              "lon": round(areas.lon0 + x / areas.kx, 4),
                              "dist_cráter_km": round(math.hypot(x, y), 1), "area_km2": round(g.area_km2(), 3),
                              "pasadas": L["pasadas"], "noches": len(L["noches"]), "max_bt_k": L["max_bt_k"],
                              "vrp_mw_suma": round(L["vrp_mw"], 3), "pixeles_por_familia": dict(L["familias"])})
        resumen["volcanes"][volcan] = {
            "inner_km": areas.inner_km, "flanco_km": areas.flanco_km, "n_lagos": len(areas.lagos),
            "por_familia": {f: dict(c) for f, c in sorted(porfam.items())},
            "vrp_por_area_mw": {f: {k: round(v, 3) for k, v in c.items()} for f, c in sorted(vrp_area.items())},
            "lagos_con_alertas": lagos_out}
    f_pasadas.close()
    f_pix.close()
    peor_cierre.sort(reverse=True)
    resumen["controles"] = dict(ctl)
    resumen["controles"]["peores_cierres_err_sobre_tol"] = [
        {"razon": round(a, 3), "volcan": b, "dt": c, "sensor": s, "err_mw": round(e, 6), "tol_mw": round(t, 6)}
        for a, b, c, s, e, t in peor_cierre[:5]]
    (AQUI / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    imprimir(resumen)


def imprimir(res):
    c = res["controles"]
    print("Controles:", json.dumps({k: v for k, v in c.items() if k != "peores_cierres_err_sobre_tol"}, ensure_ascii=False))
    print("Peores cierres (err/tol):", json.dumps(c["peores_cierres_err_sobre_tol"], ensure_ascii=False))
    print()
    hdr = ("volcan", "familia", "pasadas", "con_det", "crater%", "agua%", "flanco%", "resto%", "crat+otra",
           "lejanas", "lej_con_crat", "px_borde%")
    print("\t".join(hdr))
    for v, dv in res["volcanes"].items():
        for f, c in dv["por_familia"].items():
            cd = c.get("con_deteccion", 0)
            pct = (lambda k: f"{100 * c.get(k, 0) / cd:.1f}" if cd else "-")
            pb = f"{100 * c.get('pixeles_borde', 0) / c['pixeles']:.1f}" if c.get("pixeles") else "-"
            print("\t".join(map(str, (v, f, c.get("pasadas", 0), cd, pct("con_crater"), pct("con_agua"),
                                      pct("con_flanco"), pct("con_resto"), c.get("crater_y_otra", 0),
                                      c.get("lejanas", 0), c.get("lejana_con_crater", 0), pb))))
    print()
    print("Totales por familia (10 volcanes): pasadas con detección; con calor en el cráter y en otra área (y con qué "
          "área); de ésas, publicadas lejanas por la regla «radiante»; publicadas cumbre con calor también fuera; "
          "pasadas sin calor en el cráter; píxeles en borde de área.")
    tot = collections.defaultdict(collections.Counter)
    for dv in res["volcanes"].values():
        for f, c in dv["por_familia"].items():
            tot[f].update(c)
            tot["TODAS"].update(c)
    for f in ("MODIS", "VIIRS375", "VIIRS750", "TODAS"):
        c = tot[f]
        print(f"  {f}\tpasadas {c['pasadas']}\tcon_det {c['con_deteccion']}\tcon_crater {c['con_crater']}\tcon_agua "
              f"{c['con_agua']}\tcon_flanco {c['con_flanco']}\tcon_resto {c['con_resto']}\tcrater_y_otra {c['crater_y_otra']} (agua {c['crater_y_agua']}, "
              f"flanco {c['crater_y_flanco']}, resto {c['crater_y_resto']})\tpublicada_lejana "
              f"{c['crater_y_otra_publicada_lejana']}\tpublicada_cumbre "
              f"{c['crater_y_otra'] - c['crater_y_otra_publicada_lejana']}\tsin_crater {c['sin_crater']}\t"
              f"lejanas {c['lejanas']}\tpixeles_borde {c['pixeles_borde']} de {c['pixeles']}\t"
              f"pasadas_con_pixel_borde {c['pasadas_con_pixel_borde']}")
    print()
    print("Lagos con alertas (pasadas, noches, max BT, VRP sumado):")
    for v, dv in res["volcanes"].items():
        for L in dv["lagos_con_alertas"]:
            print(f"  {v}\tlago {L['lago']}\t{L['dist_cráter_km']} km\t{L['area_km2']} km2\tpasadas {L['pasadas']}"
                  f"\tnoches {L['noches']}\tmaxBT {L['max_bt_k']}\tVRP {L['vrp_mw_suma']}\t{L['pixeles_por_familia']}")


if __name__ == "__main__":
    main()
