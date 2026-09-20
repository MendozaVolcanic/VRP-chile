"""S145 - Vigencia en el codigo de HOY de D23, D24, D26 y D29.

POR QUE: el catalogo cita file:line, y en este repo las lineas se mueven con cada
merge (A101). Este script localiza cada mecanismo por CONTENIDO (la expresion
literal que hace el trabajo) y reporta la linea de hoy. Si una expresion no
aparece, el mecanismo dejo de existir y la divergencia hay que revisarla.

Read-only: no toca pipeline/, solo lo lee e importa el perfil efectivo.
Salida: 01_vigencia.json
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "01_vigencia.json"
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, str(ROOT))


def buscar(archivo, patron, regex=False):
    """Devuelve [(linea, texto)] de cada match del patron en el archivo."""
    p = ROOT / archivo
    if not p.exists():
        return {"archivo": archivo, "existe": False, "matches": []}
    out = []
    for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        hit = re.search(patron, ln) if regex else (patron in ln)
        if hit:
            out.append({"linea": i, "texto": ln.strip()})
    return {"archivo": archivo, "existe": True, "n_matches": len(out), "matches": out}


PROC = ["pipeline/process_modis.py", "pipeline/process_viirs.py",
        "pipeline/process_viirs_mod.py"]

checks = {}

# --- D23: el Test 1 K1 no es camino de deteccion --------------------------
checks["D23"] = {
    "pregunta": "El hot_mask que sale de combine_hot_paths (con nti_path_hot) "
                "es pisado por fp_hot, la salida del primer pase?",
    "k1_se_calcula": [buscar(f, "nti > NTI_K1_NIGHT", regex=False) for f in PROC],
    "k1_entra_a_combine": [buscar(f, "nti_path_hot=nti_path_hot") for f in PROC],
    "hot_mask_pisado_por_fp_hot": [buscar(f, "hot_mask_2d = fp_hot") for f in PROC],
    "test1_mask_al_primer_pase": [buscar(f, "test1_mask=") for f in PROC],
    "definicion_test1_mask_for_fp": [
        buscar(f, "_test1_mask_for_fp = ") for f in PROC],
}

# --- D24: saturacion MODIS DN 65533 ---------------------------------------
checks["D24"] = {
    "pregunta": "Los DN > 32767 (incluido 65533 = detector saturado) se "
                "convierten en NaN, y hay un segundo guard sobre BT?",
    "umbral_invalid_si": buscar("pipeline/process_modis.py",
                                "INVALID_SI_THRESHOLD ="),
    "nan_por_dn": buscar("pipeline/process_modis.py",
                         "rad[dn > INVALID_SI_THRESHOLD] = np.nan"),
    "guard_bt_secundario": buscar("pipeline/process_modis.py",
                                  "bt_mir > BT_SAT_MIR_K_MODIS"),
    "merge_mir_bands": buscar("pipeline/process_modis.py",
                              "np.where(np.isnan(rad2", regex=False),
}

# --- D26: pool mu/sigma del segundo pase sin filtros de no-aptos ----------
checks["D26"] = {
    "pregunta": "El segundo pase arma su bg_mask sin los filtros de no-aptos "
                "que el primer pase si aplica, y con que conectiva se combina?",
    "bg_mask_segundo_pase": buscar(
        "pipeline/detection_context.py",
        "bg_mask = (~active_mask) & np.isfinite(dnti) & np.isfinite(deti)"),
    "filtros_no_aptos_primer_pase": buscar(
        "pipeline/detection_context.py", "def build_unsuitable_mask"),
    "uso_no_aptos_primer_pase": buscar(
        "pipeline/detection_context.py", "build_unsuitable_mask("),
    "conectiva": buscar("pipeline/detection_context.py",
                        "combinar = max if use_prose_branch else min"),
    "hay_gate_bt_en_segundo_pase": buscar(
        "pipeline/detection_context.py", "sigma_summit = min(", regex=False),
}

# --- D29: refit iterativo a 3 sigma en la regresion cuadratica ------------
checks["D29"] = {
    "pregunta": "El refit iterativo existe, esta encendido por defecto y "
                "algun caller lo apaga?",
    "parametro": buscar("pipeline/detection_context.py",
                        "iterative_refit: bool = True"),
    "bloque_refit": buscar("pipeline/detection_context.py", "if iterative_refit:"),
    "criterio_outlier": buscar("pipeline/detection_context.py",
                               "np.abs(residuals) <= outlier_sigma * sigma"),
    "callers_que_lo_pasan": [
        buscar(f, "iterative_refit") for f in
        PROC + ["pipeline/detection_context.py"]],
    "callers_de_la_funcion": [
        buscar(f, "compute_eti_scene_quadratic(") for f in PROC],
}

# --- flags efectivos del perfil operacional -------------------------------
import pipeline.profile as prof  # noqa: E402

FLAGS = [
    "ENABLE_TESTS_23_PROSE_BRANCH", "ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK",
    "ENABLE_FIRST_PASS_TESTS_2_AND_3", "ENABLE_SECOND_PASS_ADJACENT",
    "ENABLE_SECOND_PASS_CONDITIONED", "ENABLE_UNSUITABLE_FILTERS_267_273",
    "ENABLE_MODIS_B22_PRIMARY", "ENABLE_BT_SAT_SECONDARY_GUARD",
    "ENABLE_DUAL_ROI_BT", "ENABLE_DNTI_DUAL_ROI",
]
PARAMS = [
    "NTI_K1_NIGHT", "NTI_BT_SANITY_K", "BT_SAT_MIR_K_MODIS",
    "DNTI_CONTEXTUAL_C1_SUMMIT", "DNTI_CONTEXTUAL_C1_SCENE",
    "C2_DNTI_SUMMIT_NIGHT", "C2_DNTI_SCENE_NIGHT",
    "C2_DETI_SUMMIT_NIGHT", "C2_DETI_SCENE_NIGHT",
    "C1_SUMMIT_OVERRIDE", "C2_SUMMIT_OVERRIDE", "VIIRS_C2_OVERRIDE_NIGHT",
]
res = {
    "perfil": os.environ["VRP_PROFILE"],
    "flags_efectivos": {k: getattr(prof, k, "<NO EXISTE>") for k in FLAGS},
    "parametros_efectivos": {k: getattr(prof, k, "<NO EXISTE>") for k in PARAMS},
    "checks": checks,
}
OUT.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
print("escrito", OUT)
for d, c in checks.items():
    print("\n===", d)
    for k, v in c.items():
        if k == "pregunta":
            continue
        vs = v if isinstance(v, list) else [v]
        for item in vs:
            n = item.get("n_matches", 0)
            lin = ",".join(str(m["linea"]) for m in item["matches"][:6])
            print(f"  {k:38s} {item['archivo']:32s} n={n} lineas={lin}")
