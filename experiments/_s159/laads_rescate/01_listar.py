# -*- coding: utf-8 -*-
"""S159, frente laads_rescate: lista que gránulos existen en CMR público, LAADS y LANCE
para los días con hueco de CMR, sin credenciales y sin bajar ningún gránulo.

Preguntas del instrumento:
1. Si el depósito no tuviera el gránulo, ¿lo vería? Sí: el listado diario de LAADS y
   LANCE trae todos los archivos del día; un día sano trae ~240 (VIIRS, 6 min) o
   ~288 (MODIS, 5 min). Se imprime el total por día para que un listado vacío o
   truncado se note.
2. ¿Instrumento muerto ≠ «no hay»? Toda consulta guarda el código HTTP; 404, 303 o
   error de red quedan como SIN DATO, nunca como 0. Control positivo: el 2026-10-15
   (día sano) los gránulos de nuestros records deben aparecer en las tres fuentes.
   Control negativo: un día futuro (2026-10-30) debe dar SIN DATO o 0.

Todo se cachea en _cache/ para no repetir consultas a NASA.
"""
import io, json, os, re, subprocess, sys, time, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
CACHE = AQUI / "_cache"; CACHE.mkdir(exist_ok=True)
REPO = Path(r"C:\vrp-trabajo\s159-pruebas")
PAUSA = 1.5

DIAS = ["2026-10-12", "2026-10-15", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20"]
NEG = "2026-10-30"   # control negativo (futuro)

# (short_name std, versión CMR std, colección LAADS, short NRT, versión CMR NRT, colección LANCE)
PROD = {
    "MOD021KM": ("6.1", "61", "MOD021KM", "6.1NRT", "61"),
    "MOD03":    ("6.1", "61", "MOD03", "6.1NRT", "61"),
    "MYD021KM": ("6.1", "61", "MYD021KM", "6.1NRT", "61"),
    "MYD03":    ("6.1", "61", "MYD03", "6.1NRT", "61"),
    "VNP02IMG": ("2", "5200", "VNP02IMG_NRT", "2", "5200"),
    "VNP03IMG": ("2", "5200", "VNP03IMG_NRT", "2", "5200"),
    "VNP02MOD": ("2", "5200", "VNP02MOD_NRT", "2", "5200"),
    "VNP03MOD": ("2", "5200", "VNP03MOD_NRT", "2", "5200"),
    "VJ102IMG": ("2.1", "5201", "VJ102IMG_NRT", "2.1", "5201"),
    "VJ103IMG": ("2.1", "5201", "VJ103IMG_NRT", "2.1", "5201"),
    "VJ102MOD": ("2.1", "5201", "VJ102MOD_NRT", "2.1", "5201"),
    "VJ103MOD": ("2.1", "5201", "VJ103MOD_NRT", "2.1", "5201"),
    "VJ202IMG": ("2.1", "5201", "VJ202IMG_NRT", "2.1", "5201"),
    "VJ203IMG": ("2.1", "5201", "VJ203IMG_NRT", "2.1", "5201"),
    "VJ202MOD": ("2.1", "5201", "VJ202MOD_NRT", "2.1", "5201"),
    "VJ203MOD": ("2.1", "5201", "VJ203MOD_NRT", "2.1", "5201"),
}
CHILE_BBOX = "-76,-56,-66,-17"   # W,S,E,N


def get(url, nombre):
    """Devuelve (status, texto). Cachea. Sin seguir redirecciones a login."""
    f = CACHE / (re.sub(r"[^A-Za-z0-9_.-]", "_", nombre) + ".json")
    if f.exists():
        d = json.loads(f.read_text(encoding="utf-8"))
        return d["status"], d["body"]

    class NoRedir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    op = urllib.request.build_opener(NoRedir)
    try:
        r = op.open(urllib.request.Request(url, headers={"User-Agent": "vrp-chile-audit"}), timeout=120)
        st, body = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        st, body = e.code, ""
    except Exception as e:
        st, body = -1, f"{type(e).__name__}: {e}"
    f.write_text(json.dumps({"url": url, "status": st, "body": body,
                             "t": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    time.sleep(PAUSA)
    return st, body


def doy(dia):
    return datetime.strptime(dia, "%Y-%m-%d").strftime("%j")


RX = re.compile(r"\.A(\d{7})\.(\d{4})\.(\d{3})\.(\d{13})?")


def listado(host, coll, prod, dia):
    """{HHMM: nombre} o None si SIN DATO."""
    url = f"https://{host}/archive/allData/{coll}/{prod}/{dia[:4]}/{doy(dia)}.json"
    st, body = get(url, f"{host.split('.')[0]}_{prod}_{dia}")
    if st != 200:
        return None, st, url
    try:
        cont = json.loads(body)["content"]
    except Exception:
        return None, "json?", url
    out = {}
    for x in cont:
        m = RX.search(x["name"])
        if m and m.group(1) == dia[:4] + doy(dia):
            out[m.group(2)] = x["name"]
    return out, st, url.replace(".json", "/")


def cmr(short, ver, t0, t1, tag):
    url = ("https://cmr.earthdata.nasa.gov/search/granules.json?short_name=" + short +
           "&version=" + urllib.request.quote(ver) + "&bounding_box=" + CHILE_BBOX +
           f"&temporal={t0},{t1}&page_size=2000")
    st, body = get(url, f"cmr_{tag}_{short}_{ver}_{t0[:10]}_{t1[:10]}")
    if st != 200:
        return None, st
    ent = json.loads(body)["feed"]["entry"]
    out = []
    for e in ent:
        ts = e["time_start"]
        polys = []
        for p in e.get("polygons", []):
            nums = [float(v) for v in p[0].split()]
            polys.append(list(zip(nums[1::2], nums[0::2])))  # (lon, lat)
        out.append({"dia": ts[:10], "hhmm": ts[11:13] + ts[14:16],
                    "name": e.get("producer_granule_id") or e.get("title"),
                    "dn": e.get("day_night_flag"), "polys": polys})
    return out, st


def dentro(lon, lat, poly):
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            xi = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
            if lon < xi:
                c = not c
    return c


def tier_a():
    import yaml
    v = yaml.safe_load(open(REPO / "volcanoes.yaml", encoding="utf-8"))
    v = v["volcanoes"] if isinstance(v, dict) else v
    return [(x["name"], x.get("vent_lon", x["lon"]), x.get("vent_lat", x["lat"]))
            for x in v if x.get("radius_km") == 25]


def records(vols):
    out = []
    for nom, _, _ in vols:
        txt = subprocess.run(["git", "-C", str(REPO), "show",
                              f"origin/main:data/mirova_equivalent/{nom}.json"],
                             capture_output=True, check=True).stdout.decode("utf-8")
        for r in json.loads(txt)["records"]:
            d = str(r.get("datetime_utc", ""))[:10]
            if d in DIAS:
                g = r.get("granule") or ""
                out.append({"vol": nom, "dia": d, "hhmm": r["datetime_utc"][11:13] + r["datetime_utc"][14:16],
                            "prod": g.split(".")[0], "granule": g,
                            "pv": r.get("product_version")})
    return out


def main():
    vols = tier_a()
    print("Tier A:", len(vols), [v[0] for v in vols])
    sha = subprocess.run(["git", "-C", str(REPO), "rev-parse", "origin/main"],
                         capture_output=True).stdout.decode().strip()
    recs = records(vols)
    print(f"records origin/main {sha[:9]} en los días: {len(recs)}")

    res = {"sha": sha, "dias": DIAS, "recs": recs, "laads": {}, "lance": {}, "cmr": {}, "cmr_analogo": {}}

    # CMR: una consulta por producto y versión para toda la ventana, y otra para los análogos D-16
    for prod, (ver, coll, nrt, vnrt, colln) in PROD.items():
        for tag, sh, vv in (("std", prod, ver), ("nrt", nrt, vnrt)):
            g, st = cmr(sh, vv, "2026-10-12T00:00:00Z", "2026-10-21T00:00:00Z", tag)
            res["cmr"][f"{prod}|{tag}"] = {"st": st, "g": g}
        if prod[3:5] in ("02",) or prod.endswith("021KM"):
            g, st = cmr(prod, ver, "2026-09-26T00:00:00Z", "2026-10-05T00:00:00Z", "ana")
            res["cmr_analogo"][prod] = {"st": st, "g": g}

    for prod, (ver, coll, nrt, vnrt, colln) in PROD.items():
        for dia in DIAS + [NEG]:
            l, st, u = listado("ladsweb.modaps.eosdis.nasa.gov", coll, prod, dia)
            res["laads"][f"{prod}|{dia}"] = {"st": st, "l": l, "url": u}
            l, st, u = listado("nrt3.modaps.eosdis.nasa.gov", colln, nrt, dia)
            res["lance"][f"{prod}|{dia}"] = {"st": st, "l": l, "url": u}

    (AQUI / "01_listar_resultado.json").write_text(json.dumps(res), encoding="utf-8")
    print("listo")


if __name__ == "__main__":
    main()
