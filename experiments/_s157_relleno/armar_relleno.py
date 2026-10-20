# -*- coding: utf-8 -*-
"""Plan de relleno del historico con K: que pasadas faltan, si NASA las tiene, y que despachar.

POR QUE (S157): el ensayo del reemplazo (PR #866, experiments/_s154_reproc_k/ensayo_s157/) encontro 89
pasadas que la serie operacional tiene y el historico con K (run 39125546355, perfil
_s154_reproc_k_historico) no trajo. Si se reemplaza asi, esas pasadas quedan con el detector viejo (C0).
Antes de relanzar trozos hay que saber dos cosas por pasada:
  1. que version tiene el record operacional (`standard` = el granulo estandar existia cuando se
     proceso; `nrt` = se proceso con LANCE y quiza el estandar no exista);
  2. si HOY el producto estandar (L1B y geolocalizacion) esta en CMR, que es donde lo busca fetch.py.
Sin (2), relanzar un trozo puede salir verde y no traer nada (A108).

Que hace:
  - lee cobertura.json del ensayo y el record operacional de cada pasada faltante
    (data/mirova_equivalent/<Vol>.json), con su `granule` y `product_version`;
  - consulta CMR (API publica, sin credenciales) por el L1B y la geolocalizacion estandar de cada
    pasada, con los mismos short_name y versiones que pipeline/fetch.py::PRODUCTS, y tambien por el
    NRT (LANCE) para comparar;
  - arma las ventanas minimas (volcan, inicio, fin) agrupando dias contiguos, solo con pasadas cuyo
    estandar existe, y los comandos `gh workflow run` (NO los ejecuta).

Salida: cmr_por_pasada.json, plan_relleno.json y PLAN_RELLENO.md al lado de este script.
Uso: python experiments/_s157_relleno/armar_relleno.py
"""
import io
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
ENSAYO = RAIZ / "experiments" / "_s154_reproc_k" / "ensayo_s157"
sys.path.insert(0, str(RAIZ))
from pipeline.fetch import PRODUCTS  # noqa: E402  (mismos short_name/versiones que el pipeline)

CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
PERFIL = "_s154_reproc_k_historico"

# sensor del record -> (clave L1B, clave GEO) de PRODUCTS
SENSOR_A_PRODUCTO = {
    "VIIRS_SNPP": ("VIIRS_SNPP_L1B", "VIIRS_SNPP_GEO"),
    "VIIRS_SNPP_750": ("VIIRS_SNPP_MOD_L1B", "VIIRS_SNPP_MOD_GEO"),
    "VIIRS_NOAA20": ("VIIRS_NOAA20_L1B", "VIIRS_NOAA20_GEO"),
    "VIIRS_NOAA20_750": ("VIIRS_NOAA20_MOD_L1B", "VIIRS_NOAA20_MOD_GEO"),
    "VIIRS_NOAA21": ("VIIRS_NOAA21_L1B", "VIIRS_NOAA21_GEO"),
    "VIIRS_NOAA21_750": ("VIIRS_NOAA21_MOD_L1B", "VIIRS_NOAA21_MOD_GEO"),
    "MODIS_TERRA": ("MODIS_TERRA_L1B", "MODIS_TERRA_GEO"),
    "MODIS_AQUA": ("MODIS_AQUA_L1B", "MODIS_AQUA_GEO"),
}


def _versiones(p: dict) -> list[str]:
    return p["versions"] if isinstance(p.get("versions"), list) else [p["version"]]


_CMR_CAIDO = {"motivo": None}


def _cmr(short_name: str, version: str, t0: datetime, t1: datetime) -> list[str]:
    # cortacircuito (como A64 en fetch.py): si CMR ya fallo entero en esta corrida, no se
    # vuelve a esperar los reintentos en cada una de las cerca de 270 consultas
    if _CMR_CAIDO["motivo"]:
        raise RuntimeError(f"CMR caido en esta corrida: {_CMR_CAIDO['motivo']}")
    q = urllib.parse.urlencode({
        "short_name": short_name, "version": version, "page_size": 50,
        "temporal": f"{t0:%Y-%m-%dT%H:%M:%SZ},{t1:%Y-%m-%dT%H:%M:%SZ}"})
    for intento in range(4):
        try:
            with urllib.request.urlopen(f"{CMR}?{q}", timeout=60) as r:
                entradas = json.load(r)["feed"]["entry"]
            return [e.get("producer_granule_id") or e.get("title") for e in entradas]
        except Exception as e:  # noqa: BLE001  CMR da 500 a ratos (S157)
            if intento == 3:
                _CMR_CAIDO["motivo"] = f"{short_name} v{version}: {e}"
                raise RuntimeError(f"CMR fallo para {short_name} v{version}: {e}") from e
            time.sleep(5 * (intento + 1))
    return []


def _hhmm(granulo: str) -> str:
    # VJ102IMG.A2025291.0500.021...nc / MYD021KM.A2025291.0500.061...hdf -> "0500"
    return granulo.split(".")[2]


def _buscar(clave: str, t: datetime, nrt: bool) -> dict:
    """Granulo que empieza en t (minuto exacto) para la clave de PRODUCTS.

    Si CMR no responde devuelve {"error": ...}: SIN DATO, nunca "no existe"."""
    p = PRODUCTS[clave]["nrt"] if nrt else PRODUCTS[clave]
    # ventana de un minuto alrededor del inicio: los granulos VIIRS duran 6 min y MODIS 5,
    # asi que basta con el inicio, y se confirma por la hora del nombre
    t0, t1 = t - timedelta(seconds=30), t + timedelta(seconds=30)
    try:
        for ver in _versiones(p):
            hallados = [g for g in _cmr(p["short_name"], ver, t0, t1) if _hhmm(g) == f"{t:%H%M}"]
            if hallados:
                return {"short_name": p["short_name"], "version": ver, "granulos": hallados}
    except RuntimeError as e:
        return {"short_name": p["short_name"], "version": "/".join(_versiones(p)), "error": str(e)}
    return {"short_name": p["short_name"], "version": "/".join(_versiones(p)), "granulos": []}


# Archivo de LAADS DAAC (listado publico, sin credenciales), donde se baja el estandar.
# Coleccion por version: VIIRS v2 -> 5200, v2.1 -> 5201, MODIS 6.1 -> 61.
LAADS = "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData"
COLECCION = {"2": "5200", "2.1": "5201", "6.1": "61"}
_cache_laads: dict = {}


def _laads_dia(col: str, short_name: str, t: datetime):
    """Nombres de archivo del dia, [] si el dia no existe (404), None si falla la consulta."""
    k = (col, short_name, t.year, t.timetuple().tm_yday)
    if k in _cache_laads:
        return _cache_laads[k]
    url = f"{LAADS}/{col}/{short_name}/{t.year}/{t.timetuple().tm_yday:03d}.json"
    res = None
    for intento in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                res = [x["name"] for x in json.load(r)["content"]]
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                res = []
                break
            time.sleep(5 * (intento + 1))
        except Exception:  # noqa: BLE001
            time.sleep(5 * (intento + 1))
    _cache_laads[k] = res
    return res


def _buscar_laads(clave: str, t: datetime) -> dict:
    p = PRODUCTS[clave]
    pref = f"{p['short_name']}.A{t.year}{t.timetuple().tm_yday:03d}.{t:%H%M}."
    sin_dato = []
    for ver in _versiones(p):
        col = COLECCION.get(ver)
        if col is None:
            continue
        nombres = _laads_dia(col, p["short_name"], t)
        if nombres is None:
            sin_dato.append(ver)
            continue
        hallados = [n for n in nombres if n.startswith(pref)]
        if hallados:
            return {"short_name": p["short_name"], "version": ver, "coleccion": col, "granulos": hallados}
    if sin_dato:
        return {"short_name": p["short_name"], "error": f"LAADS no respondio para v{sin_dato}"}
    return {"short_name": p["short_name"], "version": "/".join(_versiones(p)), "granulos": []}


def _ventanas(dias: list[str]) -> list[tuple[str, str]]:
    ds = sorted({date.fromisoformat(d) for d in dias})
    out, ini, prev = [], None, None
    for d in ds:
        if ini is None:
            ini = prev = d
        elif d - prev == timedelta(days=1):
            prev = d
        else:
            out.append((ini.isoformat(), prev.isoformat()))
            ini = prev = d
    if ini is not None:
        out.append((ini.isoformat(), prev.isoformat()))
    return out


def _estado(l1b: dict, geo: dict) -> str:
    """existe (L1B y GEO), no_existe (las dos consultas respondieron y falta alguno) o sin_dato."""
    if l1b.get("granulos") and geo.get("granulos"):
        return "existe"
    if "error" in l1b or "error" in geo:
        return "sin_dato"
    return "no_existe"


def _escribir_md(consultado, pasadas, resumen, ventanas, despachos):
    L = ["# Plan de relleno del historico con K (S157)", "",
         f"Generado por `armar_relleno.py`; CMR y LAADS consultados el {consultado} (APIs publicas, sin credenciales).",
         "NO despachado: lo lanza la sesion duena del loop.", "",
         "## Antes de despachar", "",
         "1. **El PR del merge que conserva la base tiene que estar mergeado.** Con el merge anterior, relanzar",
         "   unos pocos dias de un volcan escribe su JSON SOLO con esos dias y borra el resto del historico en main.",
         "2. **En serie, uno a la vez**, esperando que termine cada run (incluido su job `merge`): todos usan el",
         f"   perfil `{PERFIL}`, que es el grupo de concurrencia `reproc-chunked-{PERFIL}`, el mismo de los",
         "   relanzamientos de NevadosDeChillan. GitHub guarda UN solo run pendiente por grupo: un tercero",
         "   despachado mientras otro espera lo EXPULSA.",
         "3. Despues de cada run, contar las pasadas del volcan en la ventana contra la serie operacional (A108):",
         "   un run verde con un corte de CMR puede volver a no traerlas.", "",
         "## Resumen por version del record operacional", "",
         "Decision por pasada: CMR si respondio (es donde busca `fetch.py`); si CMR no dio dato, el listado",
         "publico del archivo LAADS DAAC (donde se baja el estandar). `existe` exige L1B **y** geolocalizacion.", "",
         "| product_version | decision (fuente) | pasadas |", "|---|---|---|"]
    for k, v in sorted(resumen.items()):
        for dec, n in sorted(v.items()):
            L.append(f"| `{k}` | {dec} | {n} |")
    n_cmr = sum(1 for p in pasadas if p["estado_cmr"] == "sin_dato")
    if n_cmr:
        L += ["", f"**CMR no respondio en {n_cmr} de {len(pasadas)} pasadas** (HTTP 500 en la busqueda de",
              "granulos). Esas decisiones salen de LAADS: antes de despachar, volver a correr este script y",
              "confirmar con CMR, porque un archivo en LAADS que CMR no indexa no lo encontraria el pipeline."]
    L += ["", "## Despachos (en este orden, uno a la vez)", ""]
    for i, d in enumerate(despachos, 1):
        L += [f"{i}. {', '.join(d['volcanes'])}, {d['inicio']} a {d['fin']} ({d['dias']} dias)", "",
              "```bash", d["comando"], "```", ""]
    if not despachos:
        L += ["Ninguno: no hay pasada faltante con producto estandar en CMR.", ""]
    sin = [p for p in pasadas if p["decision"] == "no_existe"]
    if sin:
        L += ["## Pasadas sin producto estandar (repetir el trozo no las traeria)", ""]
        for p in sorted(sin, key=lambda x: (x["volcan"], x["datetime_utc"], x["sensor"])):
            L.append(f"- {p['volcan']} {p['datetime_utc']} {p['sensor']} (record `{p['product_version']}`, "
                     f"{p['fuente_decision']})")
        L.append("")
    L += ["## Pasadas faltantes", "",
          "| Volcan | Pasada | Sensor | Trozo | Record | Decision | CMR L1B / GEO | LAADS L1B / GEO | CMR NRT L1B |",
          "|---|---|---|---|---|---|---|---|---|"]

    def _g(c):
        if "error" in c:
            return "sin dato"
        return c["granulos"][0] if c["granulos"] else "no"
    for p in sorted(pasadas, key=lambda x: (x["volcan"], x["datetime_utc"], x["sensor"])):
        L.append(f"| {p['volcan']} | {p['datetime_utc']} | {p['sensor']} | {p['trozo']} | "
                 f"`{p['product_version']}` | {p['decision']} ({p['fuente_decision']}) | "
                 f"{_g(p['cmr_estandar_l1b'])} / {_g(p['cmr_estandar_geo'])} | "
                 f"{_g(p['laads_estandar_l1b'])} / {_g(p['laads_estandar_geo'])} | {_g(p['cmr_nrt_l1b'])} |")
    (AQUI / "PLAN_RELLENO.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> int:
    cob = json.loads((ENSAYO / "cobertura.json").read_text(encoding="utf-8"))
    pasadas = []
    for vol, info in sorted(cob["volcanes"].items()):
        op = json.loads((RAIZ / "data" / "mirova_equivalent" / f"{vol}.json").read_text(encoding="utf-8"))
        por_clave = {(r["datetime_utc"], r["sensor"]): r for r in op["records"]}
        informe = json.loads((ENSAYO / f"informe_{vol}.json").read_text(encoding="utf-8"))
        claves_informe = {tuple(k) for k in informe["solo_operacional_claves"]}
        claves_cob = set()
        for d in info["dias_con_deficit"]:
            for dt in d["faltan"]:
                claves_cob.add((dt, d["sensor"]))
                rec = por_clave.get((dt, d["sensor"]))
                pasadas.append({
                    "volcan": vol, "dia": d["dia"], "datetime_utc": dt, "sensor": d["sensor"],
                    "trozo": d["trozo"],
                    "product_version": rec.get("product_version") if rec else None,
                    "granulo_operacional": rec.get("granule") if rec else None,
                })
        if claves_cob != claves_informe:
            print(f"AVISO {vol}: cobertura.json y informe no coinciden "
                  f"({len(claves_cob)} contra {len(claves_informe)})")

    print(f"{len(pasadas)} pasadas faltantes; consultando CMR y LAADS...")
    for i, p in enumerate(pasadas, 1):
        t = datetime.strptime(p["datetime_utc"][:16].replace("T", " "), "%Y-%m-%d %H:%M")
        l1b, geo = SENSOR_A_PRODUCTO[p["sensor"]]
        p["cmr_estandar_l1b"] = _buscar(l1b, t, nrt=False)
        p["cmr_estandar_geo"] = _buscar(geo, t, nrt=False)
        p["cmr_nrt_l1b"] = _buscar(l1b, t, nrt=True)
        p["laads_estandar_l1b"] = _buscar_laads(l1b, t)
        p["laads_estandar_geo"] = _buscar_laads(geo, t)
        p["estado_cmr"] = _estado(p["cmr_estandar_l1b"], p["cmr_estandar_geo"])
        p["estado_laads"] = _estado(p["laads_estandar_l1b"], p["laads_estandar_geo"])
        # POR QUE CMR primero: fetch.py busca por CMR (earthaccess); un archivo en LAADS que
        # CMR no indexa no lo encontraria. LAADS decide sólo si CMR no dio dato.
        if p["estado_cmr"] != "sin_dato":
            p["decision"], p["fuente_decision"] = p["estado_cmr"], "CMR"
        else:
            p["decision"], p["fuente_decision"] = p["estado_laads"], "LAADS (CMR sin dato)"
        p["estandar_existe"] = p["decision"] == "existe"
        if i % 10 == 0:
            print(f"  {i}/{len(pasadas)}", flush=True)
    consultado = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ventanas minimas: solo dias con al menos una pasada cuyo estandar existe hoy
    dias_por_vol = defaultdict(list)
    for p in pasadas:
        if p["estandar_existe"]:
            dias_por_vol[p["volcan"]].append(p["dia"])
    ventanas = [{"volcan": v, "inicio": a, "fin": b}
                for v in sorted(dias_por_vol) for a, b in _ventanas(dias_por_vol[v])]
    # un despacho por ventana distinta, con todos los volcanes que la comparten
    por_ventana = defaultdict(list)
    for w in ventanas:
        por_ventana[(w["inicio"], w["fin"])].append(w["volcan"])
    despachos = []
    for (a, b), vols in sorted(por_ventana.items()):
        dias = (date.fromisoformat(b) - date.fromisoformat(a)).days + 1
        despachos.append({
            "inicio": a, "fin": b, "volcanes": vols, "dias": dias,
            "comando": (f"gh workflow run reproc-chunked.yml --repo MendozaVolcanic/VRP-chile --ref main "
                        f"-f profile={PERFIL} -f volcanoes={','.join(vols)} "
                        f"-f start={a} -f end={b} -f max_days={max(dias, 1)}"),
        })

    resumen = defaultdict(lambda: defaultdict(int))
    for p in pasadas:
        resumen[p["product_version"] or "sin_record"][f"{p['decision']} ({p['fuente_decision']})"] += 1
    (AQUI / "cmr_por_pasada.json").write_text(json.dumps(
        {"consultado_utc": consultado, "cmr": CMR, "pasadas": pasadas}, indent=2, ensure_ascii=False),
        encoding="utf-8")
    (AQUI / "plan_relleno.json").write_text(json.dumps(
        {"consultado_utc": consultado, "perfil": PERFIL,
         "resumen": {k: dict(v) for k, v in resumen.items()},
         "ventanas": ventanas, "despachos": despachos}, indent=2, ensure_ascii=False), encoding="utf-8")
    _escribir_md(consultado, pasadas, resumen, ventanas, despachos)
    print(json.dumps({k: dict(v) for k, v in resumen.items()}, indent=2))
    for d in despachos:
        print(d["comando"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
