# Tarea 1.21: que granulos de la muestra NO existen en el archivo de NASA, consultado ANTES de correr.
#
# POR QUE. El evaluador sale INCOMPLETO si falta un granulo pedido (A108). Pero un granulo que no existe
# en el archivo (la 1.17 encontro uno: Tupungatito MOD021KM.A2026275.0225, sin L1B Standard 6.1) no
# falta por la corrida: falta en el mundo, y repetir el job no lo trae. Se separan las dos cosas
# consultando CMR (publico, sin credenciales) y fijando la lista en archivo_cmr.json junto al
# pre-registro. Un granulo de esa lista no cuenta como pedido; cualquier otro que falte es INCOMPLETO.
#
# Uso: python comprobar_archivo.py   (red a cmr.earthdata.nasa.gov; escribe archivo_cmr.json)
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
POB = AQUI.parent / "_s151_mxd03_etiquetas" / "poblacion.json"
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
VERSION = "6.1"   # la que baja probe_etiquetas._bajar


def inicio(clave):
    """'MOD021KM.A2026275.0225' -> datetime UTC del inicio del granulo."""
    _, a, hhmm = clave.split(".")
    return datetime.strptime(a[1:] + hhmm, "%Y%j%H%M").replace(tzinfo=timezone.utc)


def titulos(short, t0):
    t1 = t0 + timedelta(minutes=4, seconds=59)
    q = urllib.parse.urlencode({"short_name": short, "version": VERSION, "page_size": 20,
                                "temporal": "%s,%s" % (t0.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                                       t1.strftime("%Y-%m-%dT%H:%M:%SZ"))})
    for intento in range(4):
        try:
            with urllib.request.urlopen(CMR + "?" + q, timeout=60) as fh:
                return [e.get("producer_granule_id") or e.get("title", "") for e in json.load(fh)["feed"]["entry"]]
        except Exception:
            if intento == 3:
                raise
            time.sleep(5 * (intento + 1))


def existe(clave):
    prod, a, hhmm = clave.split(".")
    t0 = inicio(clave)
    out = {}
    for short in (prod, prod.replace("021KM", "03")):
        pref = "%s.%s.%s.061." % (short, a, hhmm)
        out[short[:3] + ("L1B" if "021KM" in short else "03")] = any(t.startswith(pref) for t in titulos(short, t0))
    return out


def main():
    pob = json.load(open(POB, encoding="utf-8"))
    ausentes, n = [], 0
    for vol, v in pob["volcanes"].items():
        for g in v["muestra"]:
            n += 1
            e = existe(g["clave"])
            if not all(e.values()):
                ausentes.append({"volcan": vol, "clave": g["clave"], "estrato": g["estrato"], "lab": g["lab"],
                                 "prot": g["prot"], "censo": g["censo"], "existe": e})
                print("AUSENTE", vol, g["clave"], e, flush=True)
    salida = {"consultado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), "cmr": CMR,
              "version": VERSION, "granulos_consultados": n, "ausentes": ausentes}
    (AQUI / "archivo_cmr.json").write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    print("consultados", n, "ausentes", len(ausentes))


if __name__ == "__main__":
    main()
