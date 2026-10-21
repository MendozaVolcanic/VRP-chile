"""Verificador S159 MxD03: re-corre sustrato_mirova_modis.py (copia sin tocar, salida en esta carpeta)
con la referencia FIJADA a los shas que declara el borrador (c110787a / 4ddd5481), sobre los JSON de un commit.
Pregunta 1: si el etiquetado estuviera roto, los totales por etiqueta no coincidirian con el borrador.
Pregunta 2: con referencia vacia todo saldria sin_info; el script imprime n filas indexadas.
Uso: python correr_sustrato_fijo.py DIR_JSON DIR_DL"""
import sys, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import referencia_mirova_unificada as rmu
SHAS = {"registro_vrp_consolidado.csv": "c110787a2650e792a72db9bf571edd6ddd6a3aa6",
        "registro_vrp_ocr.csv": "4ddd54810fe343ab28d5242ba25f53e2343850e7"}
def bajar_fijo(dest):
    dest.mkdir(parents=True, exist_ok=True); info = {}
    for n, sha in SHAS.items():
        d = dest / n
        if not d.exists():
            urllib.request.urlretrieve(rmu.URL_RAW.format(sha=sha, nombre=n), d)
        info[n] = {"sha": sha, "path": str(d)}
    return info
import sustrato_copia as s
s.bajar_remoto = bajar_fijo
sys.argv = ["x", "--data", sys.argv[1], "--dl", sys.argv[2], "--desde", "2026-03-01", "--hasta", "2026-10-16"]
s.main()
