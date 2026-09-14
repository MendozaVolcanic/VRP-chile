"""Utilidades compartidas de la auditoria S139 tanda 2 (mapa de bases Mirova-v1).

Solo lectura. Los CSV del remoto se bajan con 00_descargar_remoto.py a una carpeta
que se pasa por --remoto; por defecto se usa el snapshot semanal del repo.
"""
import io
import os
import sys
from datetime import timedelta

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
SNAPSHOT = os.path.join(REPO, "data", "mirova_reference", "mirova_v1_snapshot")
LOCAL_MIROVA = (r"C:\Users\nmend\OneDrive\Escritorio\claude\Automatizacion web"
                r"\Automatizacion web\Mirova-v1\monitoreo_satelital")

ARCHIVOS = [
    "registro_vrp_consolidado.csv", "registro_vrp_positivos.csv",
    "registro_vrp_ocr.csv", "registro_vrp_maestro_publicable.csv",
]
POR_VOLCAN = [
    "registro_Chaiten.csv", "registro_Copahue.csv", "registro_Isluga.csv",
    "registro_Lascar.csv", "registro_Lastarria.csv", "registro_Llaima.csv",
    "registro_Nevados_de_Chillan.csv", "registro_PlanchonPeteroa.csv",
    "registro_Puyehue_Cordon_Caulle.csv", "registro_Tupungatito.csv",
    "registro_Villarrica.csv",
]
LLAVE = ["timestamp", "Volcan", "Sensor"]


def dir_remoto(argv):
    """--remoto DIR o variable S139_REMOTO; si no, el snapshot del repo."""
    if "--remoto" in argv:
        return argv[argv.index("--remoto") + 1]
    return os.environ.get("S139_REMOTO", SNAPSHOT)


def leer(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    for c in ("timestamp",):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    for c in ("VRP_MW", "Distancia_km"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "Fecha_Satelite_UTC" in df.columns:
        df["dt"] = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce")
        df["mes"] = df["dt"].dt.strftime("%Y-%m")
        # Noche de volcan: hora solar aproximada de Chile (lon ~ -70.5 -> UTC-4.7 h).
        # noche = hora solar < 6 o >= 18, o sea UTC < 10.7 o UTC >= 22.7.
        h = df["dt"].dt.hour + df["dt"].dt.minute / 60.0
        df["noche"] = (h < 10.7) | (h >= 22.7)
        # id de noche: sumar 1 h 18 min deja toda la noche (22:42 a 10:42 UTC)
        # en la misma fecha calendario.
        df["noche_id"] = (df["dt"] + timedelta(hours=1, minutes=18)).dt.date
    return df


def encabezado(titulo, pregunta1, pregunta2, control):
    print("=" * 96)
    print(titulo)
    print("  P1 (si estuviera roto, lo veria?): " + pregunta1)
    print("  P2 (si el instrumento estuviera muerto, se veria distinto?): " + pregunta2)
    print("  Control positivo: " + control)
    print("=" * 96)
