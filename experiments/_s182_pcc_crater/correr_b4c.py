# S182 (Nicolás: «Probar la del cráter»). Lectura DESCRIPTIVA, post hoc, NO sellada: corre el analizador sellado de
# V750-B sin modificar su archivo, cambiando en memoria sólo caja_de() para que el brazo B4 sea «B4c»: crater (B2) en
# Cordón Caulle, sens (B1) en Tupungatito y def (B0) en los otros nueve. Los demás brazos quedan igual, así que la
# salida trae B4c en la fila «B4» y B2 / B1 / B0 sellados al lado para comparar. Mismos artefactos y argumentos que la
# lectura del 2026-11-03 (lectura_argumentos.txt), salvo la salida y sin el lector N-3 (que rechaza analizadores
# distintos del sellado; en la lectura real la N-3 no cambió la elección).
import importlib.util, sys, io, glob, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ARBOL = r"D:\vrp-trabajo\temporales\v750b_r4_20261103\arbol"
AN = ARBOL + r"\experiments\_s162_v750b\analizar_v750b.py"
print("sha256 analizador (LF)", hashlib.sha256(open(AN, 'rb').read().replace(b"\r\n", b"\n")).hexdigest()[:16])
spec = importlib.util.spec_from_file_location("analizar_v750b", AN)
an = importlib.util.module_from_spec(spec); sys.modules["analizar_v750b"] = an; spec.loader.exec_module(an)

def caja_de_b4c(brazo, volcan):
    if brazo == "B4":
        if volcan == "PuyehueCordonCaulle":
            return "B2"
        return "B1" if volcan == "Tupungatito" else "B0"
    return brazo

an.caja_de = caja_de_b4c
# El control negativo sellado compara B4 con B1 donde son idénticos por construcción. Con B4c eso sigue siendo cierto
# sólo en Tupungatito (en Cordón Caulle B4c es crater), así que el control se restringe a Tupungatito; VOL_SENS no se
# usa en ningún otro lugar del analizador (grep: l. 51, 145 y 393).
an.VOL_SENS = ("Tupungatito",)
arts = sorted(glob.glob(r"D:/vrp-trabajo/temporales/v750b_r4_20261103/sep/sellado/*"))
sys.argv = ["analizar_v750b.py", "--art", *arts,
            "--objetivos", ARBOL + r"\experiments\_s162_v750b\objetivos_v750b.json",
            "--sin-granulo", ARBOL + r"\experiments\_s162_v750b\sin_granulo_v750b.json",
            "--evaluador", r"D:/vrp-trabajo/temporales/evaluar_d25_s161.py",
            "--censo-art", r"D:/vrp-trabajo/temporales/s159_oraculo/censo_39713438252",
            "--censo-objetivos", r"D:/vrp-trabajo/temporales/v750b_r4_20261103/objetivos_censo_s159.json",
            "--salida", r"D:/vrp-trabajo/temporales/s182_pcc/13_b4c/veredicto_b4c.txt"]
an.main()
