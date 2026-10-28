# -*- coding: utf-8 -*-
"""Contaminación de lo existente (camino E1/E2 de la lista previa): compara la salida COMPLETA del analizador anterior
(699e2d04f) con la del nuevo (8b9156476) sobre (a) la población base y (b) la base con 3 far_ref que K publica y que no
tienen alertados en el paquete. Las líneas que cambian se imprimen; las esperables son sólo las de §6 bis, el rótulo
«(posición ...)» y el sufijo del veredicto, más los conteos de cobertura/controles que ahora incluyen las far_ref.
Uso: python diff_contaminacion.py --dest <dir> --evaluador <evaluar_d25.py del tag>
"""
import argparse
import difflib
import subprocess
import sys
from pathlib import Path

AQ = Path(__file__).resolve().parent
sys.path.insert(0, str(AQ.parent))
import probar_evaluar_v750a as PR  # noqa: E402

RAIZ_VIEJO, RAIZ_NUEVO = "RAIZ = AQUI.parents[1]", "RAIZ = AQUI.parents[2]"


def antiguo():
    src = subprocess.run(["git", "show", "699e2d04f:experiments/_s162_v750a/evaluar_v750a.py"], capture_output=True,
                         cwd=str(AQ), check=True).stdout.decode("utf-8")
    p = AQ / "_old_evaluar.py"
    p.write_text(src.replace(RAIZ_VIEJO, RAIZ_NUEVO), encoding="utf-8")
    return p


def correr(analizador, pob, d, evaluador):
    pob.escribir(d, verde=PR.VERDE)
    cmd = [sys.executable, str(analizador), "--fase", "censo", "--art", str(d / "art"), "--objetivos",
           str(d / "objetivos.json"), "--evaluador", str(evaluador), "--sin-granulo", str(d / "sin_granulo.json"),
           "--salida", str(d / "salida.txt"), "--equivalencia-local", str(d / "equivalencia_local.txt")]
    o = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return o.returncode, o.stdout.splitlines()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--evaluador", required=True)
    a = ap.parse_args()
    viejo = antiguo()
    try:
        casos = {
            "base": lambda: PR.base(),
            "base+3far_ref(K publica, sin alertados)": lambda: PR.base(extra=PR._escena(
                "Lascar", (1, 2, 3), "far_ref", None, hora="05:00", K=0.2, P=None)),
        }
        for nom, f in casos.items():
            print(f"\n######## {nom}")
            rc_v, lv = correr(viejo, f(), a.dest / (nom[:6] + "_viejo"), a.evaluador)
            rc_n, ln = correr(AQ.parent / "evaluar_v750a.py", f(), a.dest / (nom[:6] + "_nuevo"), a.evaluador)
            print(f"rc viejo {rc_v}, rc nuevo {rc_n}; líneas viejo {len(lv)}, nuevo {len(ln)}")
            for l in difflib.unified_diff(lv, ln, "viejo", "nuevo", lineterm="", n=0):
                if not l.startswith(("---", "+++", "@@")):
                    print(l[:420])
    finally:
        viejo.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
