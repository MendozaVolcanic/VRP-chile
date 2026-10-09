# -*- coding: utf-8 -*-
"""S150, sonda de los tres campos: sello del pre-registro.

POR QUE. El criterio de decision vive en DISENO.md y en evaluar.py, y la lista de pasadas en
pasadas.json y negativos_camino_d22.json. Si cualquiera de esos archivos cambia despues de ver datos, el
resultado deja de ser una prediccion. Pero el resultado tambien lo deciden el codigo que se MIDE
(pipeline/), el predicado del tablero (frontend/index.html, que corre node), su arnes
(scripts/banco_paridad.py), el catalogo y la carga de volcanes (volcanoes.yaml, scripts/run_pipeline.py)
y el propio workflow. Un `workflow_dispatch` corre lo que haya en la rama al despachar, y main cambia casi
a diario (verificador S150, hallazgo 3; verificador D22, H9). Por eso el sello fija el sha256 de TODOS esos
archivos (los de pipeline/ uno por uno, listados con `git ls-files`, asi un archivo agregado o borrado
tambien rompe el sello) con finales LF, para que Windows y Linux den lo mismo. Se eligio la lista de hashes
y no `git diff <sha> HEAD`: no necesita la historia en el runner y sobrevive a un squash merge, que deja el
sha de sellado fuera de la historia de main.

Ademas el sello guarda la PROCEDENCIA: el sha del commit sobre el que se sello (HEAD al sellar), quien
aprobo y contra que informe del verificador. Eso no lo verifica la maquina; queda en la historia de git.

  python sellar.py --aprobo "<nombre>" --informe <ruta del informe del verificador>
        escribe el sello (lo hace quien aprueba el pre-registro, DESPUES del verificador)
  python sellar.py --verificar
        sale con 1 si falta el sello o algun archivo no coincide (lo corre el workflow)
"""
import argparse, hashlib, io, subprocess, sys
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
SELLO = AQUI / "SELLO_PREREGISTRO.txt"
ARCHIVOS = ["DISENO.md", "evaluar.py", "campos.py", "sonda.py", "seleccionar_pasadas.py",
            "pasadas.json", "negativos_camino_d22.json", "plantillas_tif.json", "sellar.py"]
# rutas relativas a la raiz del repo; un directorio se expande con `git ls-files`
PROTEGIDOS = ["pipeline/", "frontend/index.html", "scripts/banco_paridad.py", "scripts/run_pipeline.py",
              "volcanoes.yaml", ".github/workflows/probe-s150-tres-campos.yml"]


def _sha(ruta):
    return hashlib.sha256(Path(ruta).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _git(*args):
    return subprocess.run(["git", "-C", str(RAIZ)] + list(args), capture_output=True, text=True, check=True).stdout


def entradas():
    """{nombre: sha256}. Los de la sonda con su nombre; los protegidos con su ruta desde la raiz."""
    out = {n: _sha(AQUI / n) for n in ARCHIVOS}
    for p in PROTEGIDOS:
        archivos = [l for l in _git("ls-files", "--", p).splitlines() if l.strip()]
        if not archivos:
            raise SystemExit("ruta protegida sin archivos versionados: %s" % p)
        for a in archivos:
            out["raiz:" + a] = _sha(RAIZ / a)
    return out


def texto_sello(aprobo, informe, sha):
    cab = ["# sello del pre-registro S150 (sonda de los tres campos)",
           "# sha_sellado %s" % sha, "# aprobo %s" % aprobo, "# informe %s" % informe]
    return "\n".join(cab) + "\n" + "".join("%s  %s\n" % (h, n) for n, h in sorted(entradas().items()))


def diferencias(texto):
    """Lista de discrepancias entre un texto de sello y el arbol actual (vacia = coincide)."""
    esperado = {}
    for l in texto.splitlines():
        if not l.strip() or l.startswith("#"):
            continue
        h, n = l.split(None, 1)
        esperado[n.strip()] = h
    actual = entradas()
    mal = []
    for n in sorted(set(esperado) | set(actual)):
        if n not in esperado:
            mal.append("%s: NUEVO (no estaba en el sello)" % n)
        elif n not in actual:
            mal.append("%s: FALTA (estaba en el sello)" % n)
        elif esperado[n] != actual[n]:
            mal.append("%s: NO COINCIDE" % n)
    for campo in ("sha_sellado", "aprobo", "informe"):
        if not any(l.startswith("# %s " % campo) and l.split(None, 2)[2].strip() for l in texto.splitlines()):
            mal.append("cabecera sin %s" % campo)
    return mal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--aprobo", help="quien aprueba el pre-registro")
    ap.add_argument("--informe", help="ruta del informe del verificador contra el que se aprueba")
    a = ap.parse_args()
    if not a.verificar:
        if not a.aprobo or not a.informe:
            raise SystemExit("para sellar hacen falta --aprobo y --informe (procedencia del sello)")
        if not (RAIZ / a.informe).exists() and not Path(a.informe).exists():
            raise SystemExit("el informe no existe: %s" % a.informe)
        if _git("status", "--porcelain", "--", *(PROTEGIDOS + [str(AQUI.relative_to(RAIZ))])).strip():
            raise SystemExit("hay cambios sin commitear en lo que se sella: commitealos antes de sellar")
        sha = _git("rev-parse", "HEAD").strip()
        SELLO.write_text(texto_sello(a.aprobo, a.informe, sha), encoding="utf-8")
        print(SELLO.read_text(encoding="utf-8"))
        return
    if not SELLO.exists():
        print("SIN SELLO: el pre-registro no esta aprobado; no se corre")
        sys.exit(1)
    texto = SELLO.read_text(encoding="utf-8")
    for l in texto.splitlines():
        if l.startswith("#"):
            print(l)
    mal = diferencias(texto)
    for m in mal:
        print(m)
    print("SELLO COINCIDE" if not mal else "SELLO ROTO: %d diferencias" % len(mal))
    sys.exit(1 if mal else 0)


if __name__ == "__main__":
    main()
