"""Lee los flags de K desde pipeline.profile (A89).
P1: si el perfil no cargara K, los tres valores darian distinto de lo esperado (lo veria).
P2: si el loader estuviera muerto, atributo inexistente => AttributeError, no un False silencioso.
Control: se lee tambien con el perfil experimental para ver que el loader distingue perfiles."""
import os, sys, importlib
names = ["ENABLE_TEST1_PATH","ENABLE_TESTS_23_PROSE_BRANCH","ENABLE_MODIS_B22_PRIMARY",
         "ENABLE_BT_PATH_HOT","ENABLE_TEST1_NTI_INTEGRAL","ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK",
         "ENABLE_ROI1_BOX_PAPER","ENABLE_UTM_REGRID","ENABLE_DUAL_ROI_BT","ENABLE_DNTI_DUAL_ROI"]
import pipeline.profile as p
print("PROFILE env =", os.environ.get("VRP_PROFILE"))
for n in names:
    print(n, "=", getattr(p, n, "<NO EXISTE>"))
