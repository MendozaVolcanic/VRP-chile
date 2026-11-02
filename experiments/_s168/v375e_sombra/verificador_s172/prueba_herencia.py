# Verificador S172: herencia extends. Q1: si la herencia no existiera, el flag del padre no llegaria al hijo (False) y el
# control positivo (padre con geo true) lo mostraria. Q2: instrumento muerto -> excepcion, o el control positivo da False.
# Ventana: ninguna. Perfiles reales de origin/main (sha en insumos/origin_main_sha.txt); el padre se edita en una copia.
import os, sys
from pathlib import Path
sys.dont_write_bytecode = True
base = Path("D:/vrp-trabajo/temporales/ver_s172_relector/scratch_profile")
sys.path.insert(0, str(base))
ORIG = Path("D:/vrp-trabajo/temporales/ver_s172_relector/insumos/ME_main.yaml").read_text(encoding="utf-8")
def cargar(perfil, cambiar=None):
    txt = ORIG
    if cambiar:
        a, b = cambiar
        assert txt.count(a) == 1, (a, txt.count(a))
        txt = txt.replace(a, b)
    (base / "pipeline/profiles/mirova_equivalent.yaml").write_text(txt, encoding="utf-8")
    os.environ["VRP_PROFILE"] = perfil
    for m in [m for m in sys.modules if m.startswith("pipeline")]: del sys.modules[m]
    import pipeline.profile as P
    return P
GEO = ("enable_modis_geo_mxd03: false", "enable_modis_geo_mxd03: true")
P = cargar("sombra_codigo_mirova")
print("control (sombra tal cual): V750", P.ENABLE_V750_CODIGO_MIROVA, "V375", P.ENABLE_V375_CODIGO_MIROVA, "MODIS", P.ENABLE_MODIS_CODIGO_MIROVA, "geo", P.ENABLE_MODIS_GEO_MXD03)
P = cargar("sombra_codigo_mirova", GEO)
print("padre con enable_modis_geo_mxd03: true -> la sombra hereda geo =", P.ENABLE_MODIS_GEO_MXD03)
ok = not (P.ENABLE_MODIS_GEO_MXD03 or P.ENABLE_MODIS_CRATER_SIN_DATO or P.ENABLE_MODIS_DIST_DESDE_CRATER)
print("la asercion 'assert not (geo or crater_sin_dato or dist_desde_crater)' de la l.110 del workflow pasaria:", ok)
P = cargar("mirova_equivalent", ("enable_modis_geo_mxd03: false", "enable_modis_geo_mxd03: false\n  enable_modis_codigo_mirova: true"))
print("prod con MODIS on: MODIS =", P.ENABLE_MODIS_CODIGO_MIROVA, "| V375 =", P.ENABLE_V375_CODIGO_MIROVA, "| V750 =", P.ENABLE_V750_CODIGO_MIROVA, "| data_subdir =", P.DATA_SUBDIR)
P = cargar("sombra_codigo_mirova", ("enable_modis_geo_mxd03: false", "enable_modis_geo_mxd03: false\n  enable_modis_codigo_mirova: false"))
print("prod con MODIS off explicito: sombra (que declara true) =", P.ENABLE_MODIS_CODIGO_MIROVA)
