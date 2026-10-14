# -*- coding: utf-8 -*-
"""Tarea 1.6 del loop. Congela la referencia de MIROVA para el A/B F y K contra produccion en los 11 Tier A,
bajandola del repo Mirova-v1 (la fuente del dueño, feedback S139), no del snapshot local.

Copia de experiments/_s150_ndc/congelar_desde_remoto.py (mismo recorte [desde - 1 dia, hasta + 2 dias], mismo
manifiesto con sha256, filas, hora de descarga y commit de Mirova-v1), con una cosa mas: anota el sha256 de la
capa historica de la union (`data/mirova_reference/union_historica/consolidado_filas_perdidas.csv`), que
`cargar_referencia_unificada` agrega por defecto y que armar_tabla.py no deja fijar por argumento. El evaluador
compara ese sha al correr: si cambio, lo dice (no cambia el veredicto por si solo, porque la capa solo agrega
claves que la copia congelada no trae).

Uso: python congelar.py <nombre> <desde> <hasta>     (escribe _congelado_<nombre>/ en esta carpeta)
"""
import csv, hashlib, io, json, subprocess, sys, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
HISTORICO = RAIZ / "data" / "mirova_reference" / "union_historica" / "consolidado_filas_perdidas.csv"
URL = "https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/monitoreo_satelital/{f}"
nombre, desde, hasta = sys.argv[1:4]


def sha_lf(p):
    """sha256 del contenido con fin de linea LF: git con autocrlf deja los CSV en CRLF en un checkout de Windows,
    y un sha crudo mediria la maquina y no el archivo (leccion S142; el congelado de #796 lo muestra)."""
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


sha = subprocess.run(["gh", "api", "repos/MendozaVolcanic/Mirova-v1/commits/main", "-q", ".sha"],
                     capture_output=True, text=True, check=True).stdout.strip()
a = datetime.strptime(desde, "%Y-%m-%d") - timedelta(days=1)
b = datetime.strptime(hasta, "%Y-%m-%d") + timedelta(days=2)
out = AQUI / ("_congelado_" + nombre); out.mkdir(parents=True, exist_ok=True)
man = {"ventana": [desde, hasta], "fuente": "MendozaVolcanic/Mirova-v1@" + sha,
       "descargado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "archivos": {},
       "historico_sha256": sha_lf(HISTORICO), "sha_con_fin_de_linea": "LF"}
for f in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
    texto = urllib.request.urlopen(URL.format(sha=sha, f=f), timeout=120).read().decode("utf-8-sig")
    rd = csv.DictReader(io.StringIO(texto)); campos = rd.fieldnames
    col = next(c for c in campos if c.startswith("Fecha_Satelite"))
    filas = [r for r in rd if r[col] and a <= datetime.strptime(r[col][:19], "%Y-%m-%d %H:%M:%S") < b]
    with open(out / f, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, lineterminator="\n"); w.writeheader(); w.writerows(filas)
    man["archivos"][f] = {"filas": len(filas), "sha256": sha_lf(out / f)}
(out / "MANIFIESTO.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
print(man["fuente"], {k: v["filas"] for k, v in man["archivos"].items()}, "historico", man["historico_sha256"][:12])
