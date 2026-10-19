# Verificador S156: efecto, sobre los datos reales, de mutaciones de main() que la suite no ejerce (main no
# tiene prueba). Se parchea en memoria el modulo del worktree (no se edita ningun archivo) y la salida va a un
# directorio propio. Uso: python v6_mutaciones_main.py <worktree> <dir_ref> <dir_out>
import io, json, os, sys, contextlib
W, REF, OUT = sys.argv[1:4]
sys.path.insert(0, W); sys.path.insert(0, os.path.join(W, "scripts"))
import scripts.vigilancia_sombra as vs
import banco_paridad as bp
vs.aa.CONS = os.path.join(REF, "registro_vrp_consolidado.csv")
vs.aa.OCR = os.path.join(REF, "registro_vrp_ocr.csv")
ORIG_CARGAR = bp.cargar_nuestros


def correr(nombre):
    d = os.path.join(OUT, nombre)
    os.makedirs(d, exist_ok=True)
    vs.OUTDIR = d
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        vs.main()
    j = json.load(open(os.path.join(d, "sombra_latest.json"), encoding="utf-8"))
    print("%-34s veredicto=%s reversion=%s vistas=%s negs=%s" % (
        nombre, j["veredicto"], [(r["volcano"], r["sensor"], r["fecha_utc"]) for r in j.get("reversion", [])],
        j["duracion"]["protegidas_vistas_en_sombra"], (j["negativos_VIIRS375"]["k"], j["negativos_VIIRS375"]["n"])))


correr("A_sin_mutacion")
# B: la sombra se lee de produccion (olvidar data=SOMBRA): la vigilancia compara K consigo mismo
vs_sombra = vs.SOMBRA
vs.SOMBRA = None
correr("B_sombra_desde_produccion")
vs.SOMBRA = vs_sombra
# C: produccion sin filtro de sha (incluye records C0 sin marca)
src_main = vs.main


def cargar_con_sha_falso(coords, inner, win, data=None):
    recs = ORIG_CARGAR(coords, inner, win, data=data)
    if data is None:
        for r in recs:
            r["sha"] = r.get("sha") or "C0_SIN_MARCA"
    return recs


bp.cargar_nuestros = cargar_con_sha_falso
correr("C_produccion_incluye_sin_sha")
bp.cargar_nuestros = ORIG_CARGAR
# D: tolerancia de pareo 3600 s (sobrevive a la suite)
vs.TOL_S = 3600
correr("D_tolerancia_3600")
vs.TOL_S = 120
# E: tolerancia 30 s
vs.TOL_S = 30
correr("E_tolerancia_30")
vs.TOL_S = 120
