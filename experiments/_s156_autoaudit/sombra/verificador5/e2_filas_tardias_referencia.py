"""Verificador 5 de S156: ¿la referencia de MIROVA agrega filas con instante ANTERIOR a lo ya visto, o pierde filas?
Si pasa con protegidas, el orden «primeras 29» del plazo puede moverse entre corridas.
Compara snapshots versionados del repo (git show) contra la referencia del 2026-10-19.
Uso: python e2_filas_tardias_referencia.py <raiz_worktree> <dir_ref_nueva> <dir_tmp>"""
import os
import subprocess
import sys
from pathlib import Path

raiz, ref_nueva, tmp = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(raiz))
sys.path.insert(0, str(raiz / "scripts"))
import clase_mirova as cm  # noqa: E402
import auto_audit_weekly as aa  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

SNAP = "data/mirova_reference/mirova_v1_snapshot"


def cargar(cons, ocr):
    filas = cargar_referencia_unificada(str(cons), str(ocr))
    alertas = {}
    for f in filas:
        if f.get("tipo") in cm.TIPOS_ALERTA and f["volcano"] in aa.VOLS:
            alertas.setdefault(cm.clave_pasada(f), []).append(f)
    prot = {k for k, fs in alertas.items() if any(cm.alerta_protegida(f) for f in fs)}
    return set(alertas), prot


nueva_all, nueva_prot = cargar(ref_nueva / "registro_vrp_consolidado.csv", ref_nueva / "registro_vrp_ocr.csv")
commits = subprocess.run(["git", "-C", str(raiz), "log", "--format=%h %cs", "-8", "--", f"{SNAP}/registro_vrp_consolidado.csv"],
                         capture_output=True, text=True).stdout.split("\n")
for linea in [c for c in commits if c.strip()]:
    sha, fecha = linea.split()
    d = tmp / sha
    d.mkdir(parents=True, exist_ok=True)
    for nombre in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
        if not (d / nombre).exists():
            with open(d / nombre, "wb") as fh:
                fh.write(subprocess.run(["git", "-C", str(raiz), "show", f"{sha}:{SNAP}/{nombre}"], capture_output=True).stdout)
    vieja_all, vieja_prot = cargar(d / "registro_vrp_consolidado.csv", d / "registro_vrp_ocr.csv")
    maxv = max(k[2] for k in vieja_all)
    # ventana comparable: desde la frontera de K hasta el maximo de la vieja
    nueva_ven = {k for k in nueva_all if "2026-09-18" <= k[2] <= maxv}
    vieja_ven = {k for k in vieja_all if "2026-09-18" <= k[2] <= maxv}
    tardias = nueva_ven - vieja_ven
    perdidas = vieja_ven - nueva_ven
    print(f"snapshot {sha} ({fecha}, max {maxv}) contra ref 2026-10-19, ventana 2026-09-18..{maxv}: "
          f"alertas viejas {len(vieja_ven)}, nuevas {len(nueva_ven)}; tardias {len(tardias)} "
          f"(protegidas {len(tardias & nueva_prot)}); perdidas {len(perdidas)} (protegidas {len(perdidas & vieja_prot)}); "
          f"protegidas que cambian de clase {len((vieja_ven & nueva_ven) & (vieja_prot ^ nueva_prot))}")
    for k in sorted(tardias & nueva_prot)[:5]:
        print("    tardia protegida:", k)
    for k in sorted(perdidas & vieja_prot)[:5]:
        print("    perdida protegida:", k)
