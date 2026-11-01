"""Mutaciones de scripts/auto_audit_weekly.py: cada una debe hacer fallar alguna prueba S156.
Uso: python mutar.py <raiz_worktree>. Restaura el archivo original al terminar (también si falla)."""
import subprocess
import sys
from pathlib import Path

raiz = Path(sys.argv[1])
p = raiz / "scripts" / "auto_audit_weekly.py"
orig = p.read_text(encoding="utf-8")

MUT = {
    "falsas_mezcla": ('vig = [r for r in recs if r["det"] == vigente]', 'vig = list(recs)'),
    "sin_flags_protegidas": ("flags.extend(flags_protegidas(protegidas, vigente))", "pass"),
    "juzga_c0": ("    ev = por_detector[vigente]", '    ev = por_detector["C0"]'),
    "sin_d9_recall": ("mir, n_diurnas_excluidas = noches_mirova(aplicar_d9(alertas, REGLA_MINIMAS, filas_ref), coords, win)",
                      "mir, n_diurnas_excluidas = noches_mirova(alertas, coords, win)"),
    "ignora_frontera": ('    return "K" if frontera and fecha[:10] >= frontera else "C0"', '    return "K" if frontera else "C0"'),
    "avisos_no_degradan": ('+ [f"detector: {a}" for a in avisos_detector]', ""),
    "sin_chequeo_sha": ("if banco is not None and n_k_nuestros and not any(", "if False and not any("),
    "mezcla_noches": ("            if d_rec != d_noche:\n", "            if False:\n"),
    "protegida_pub_siempre": ('"publicada" if any(r["pub"] for r in cand)', '"publicada" if True'),
    "magnitud_pc_no_publicada": ('ours[key]["pub"].append(core if (b == "VIIRS375"', 'ours[key]["pub"].append(core if (False'),
    "historial_sin_detector": ('"detector": out.get("detector"),', ""),
    "sospecha_apagada": ('"referencia_sospechosa": (fuentes[k] == {"OCR"}', '"referencia_sospechosa": (False and fuentes[k] == {"OCR"}'),
}
tests = ["tests/test_auto_audit_main_s156.py", "tests/test_auto_audit_por_detector_s156.py"]
try:
    for nombre, (a, b) in MUT.items():
        if orig.count(a) != 1:
            print(f"{nombre:28s} NO APLICA (cuenta {orig.count(a)})")
            continue
        p.write_text(orig.replace(a, b), encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, "-m", "pytest", *tests, "-q", "--no-header", "-p", "no:cacheprovider", "-x"],
                           cwd=raiz, capture_output=True, text=True)
        ult = (r.stdout.strip().splitlines() or [""])[-1]
        estado = "ATRAPADA" if r.returncode == 1 and "failed" in ult else f"NO ATRAPADA rc={r.returncode}"
        print(f"{nombre:28s} {estado}  | {ult}")
finally:
    p.write_text(orig, encoding="utf-8", newline="\n")
