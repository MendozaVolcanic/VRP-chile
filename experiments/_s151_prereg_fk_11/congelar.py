# -*- coding: utf-8 -*-
"""Tarea 1.6 del loop. Congela la referencia de MIROVA para el A/B F y K contra produccion en los 11 Tier A,
bajandola del repo Mirova-v1 (la fuente del dueño, feedback S139), no del snapshot local.

Copia de experiments/_s150_ndc/congelar_desde_remoto.py (mismo recorte [desde - 1 dia, hasta + 2 dias], mismo
manifiesto con sha256, filas, hora de descarga y commit de Mirova-v1), con dos cosas mas:

1. Congela TAMBIEN las dos capas que `cargar_referencia_unificada` agrega por defecto y que no viven en el
   remoto: la historica de la union (`data/mirova_reference/union_historica/consolidado_filas_perdidas.csv`, que
   `audit-weekly.yml` reescribe cada semana) y el respaldo del 2026-04-08. Sin congelarlas, la referencia de V2
   no era la congelada: aportan 4 de 39 protegidas MODIS, 3 de 42 de VIIRS 750 y 73 negativos MODIS
   (verificador del PR #797, punto 2). Van recortadas a la misma ventana, con su sha256 en el manifiesto, y el
   evaluador y sustrato.py se las pasan EXPLICITAS al cargador (`historico_path=`, `respaldo_path=`).
2. sha256 con fin de linea LF: autocrlf deja los CSV en CRLF en un checkout de Windows.

Uso:
  python congelar.py <nombre> <desde> <hasta>   baja el remoto y congela todo en _congelado_<nombre>/
  python congelar.py capas <nombre>             agrega solo las dos capas a un congelado existente, sin volver a
                                                bajar el remoto (asi se congelaron V1 y V2, cuyos CSV principales
                                                son del 2026-10-14 14:30 UTC)
"""
import csv, hashlib, io, json, subprocess, sys, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
HISTORICO = RAIZ / "data" / "mirova_reference" / "union_historica" / "consolidado_filas_perdidas.csv"
RESPALDO = RAIZ / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado_respaldo_20260408.csv"
# nombre del archivo dentro del congelado -> fuente en el repo
CAPAS = {"consolidado_filas_perdidas.csv": HISTORICO, "respaldo_20260408.csv": RESPALDO}
URL = "https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/monitoreo_satelital/{f}"


def sha_lf(p):
    """sha256 del contenido con fin de linea LF: git con autocrlf deja los CSV en CRLF en un checkout de Windows,
    y un sha crudo mediria la maquina y no el archivo (leccion S142; el congelado de #796 lo muestra)."""
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def limites(desde, hasta):
    return datetime.strptime(desde, "%Y-%m-%d") - timedelta(days=1), datetime.strptime(hasta, "%Y-%m-%d") + timedelta(days=2)


def recortar_y_escribir(texto, destino, a, b):
    rd = csv.DictReader(io.StringIO(texto)); campos = rd.fieldnames
    col = next(c for c in campos if c.startswith("Fecha_Satelite"))
    filas = [r for r in rd if r[col] and a <= datetime.strptime(r[col][:19], "%Y-%m-%d %H:%M:%S") < b]
    with open(destino, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, lineterminator="\n"); w.writeheader(); w.writerows(filas)
    return len(filas)


def congelar_capas(out, man):
    a, b = limites(*man["ventana"])
    man["capas"] = {}
    for f, fuente in CAPAS.items():
        n = recortar_y_escribir(fuente.read_text(encoding="utf-8-sig"), out / f, a, b)
        man["capas"][f] = {"filas": n, "sha256": sha_lf(out / f), "fuente": str(fuente.relative_to(RAIZ)).replace("\\", "/"),
                           "sha256_fuente_entera": sha_lf(fuente)}
    man.pop("historico_sha256", None)
    man["capas_congeladas_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    if sys.argv[1] == "capas":
        out = AQUI / ("_congelado_" + sys.argv[2])
        man = json.loads((out / "MANIFIESTO.json").read_text(encoding="utf-8"))
    else:
        nombre, desde, hasta = sys.argv[1:4]
        sha = subprocess.run(["gh", "api", "repos/MendozaVolcanic/Mirova-v1/commits/main", "-q", ".sha"],
                             capture_output=True, text=True, check=True).stdout.strip()
        out = AQUI / ("_congelado_" + nombre); out.mkdir(parents=True, exist_ok=True)
        man = {"ventana": [desde, hasta], "fuente": "MendozaVolcanic/Mirova-v1@" + sha,
               "descargado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "archivos": {},
               "sha_con_fin_de_linea": "LF"}
        a, b = limites(desde, hasta)
        for f in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
            texto = urllib.request.urlopen(URL.format(sha=sha, f=f), timeout=120).read().decode("utf-8-sig")
            man["archivos"][f] = {"filas": recortar_y_escribir(texto, out / f, a, b), "sha256": sha_lf(out / f)}
    congelar_capas(out, man)
    (out / "MANIFIESTO.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(out.name, man["fuente"], {k: v["filas"] for k, v in man["archivos"].items()}, {k: v["filas"] for k, v in man["capas"].items()})


if __name__ == "__main__":
    main()
