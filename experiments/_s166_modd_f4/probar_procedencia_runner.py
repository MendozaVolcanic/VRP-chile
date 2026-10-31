# -*- coding: utf-8 -*-
"""S170: pruebas de procedencia_runner.py y de la aceptación del tag del runner en externos_f4.procedencia.
Parte A (regla, con un repositorio git sintético): verde si la lectura sólo cambia lo que el arnés no alcanza; rojo si
cambia un archivo del runner, una definición alcanzable, una sentencia de nivel de módulo, o si la lectura no desciende
del runner. Parte B (control, cabeceras sintéticas): verde con todas las cabeceras en el runner compatible; rojo si la
regla no da ok, si una cabecera trae otro commit, otro sha de probe_f4 u otro evaluar_f4 que el del runner, o si las
cabeceras mezclan los dos tags. Parte C (caso real, si el repo trae los tags): d65fd231d contra a7bd7562e es compatible.
Uso: python probar_procedencia_runner.py [--dir DIR_CON_COPIAS] [--tmp DIR_TEMPORAL]  (código 1 si falla una aserción,
2 si cae)
"""
import argparse
import importlib
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = Path(__import__("os").environ.get("F4_RAIZ") or AQUI.parents[1])   # el medidor corre una copia


def chk(cond, msg):
    if not cond:
        raise AssertionError(msg)


def git(d, *a):
    subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "x", "GIT_AUTHOR_EMAIL": "x@x", "GIT_COMMITTER_NAME": "x",
                        "GIT_COMMITTER_EMAIL": "x@x", "PATH": __import__("os").environ["PATH"]})
    return subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


EV = '''import os
X = 1


def ayuda(a):
    return a + 1


def distancias(a):
    return ayuda(a)


def otra(a):
    return a * 2


if __name__ == "__main__":
    print(otra(1))
'''


def escribir(d, rel, txt):
    p = Path(d) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(txt, encoding="utf-8")


def repo(tmp):
    Path(tmp).mkdir(parents=True, exist_ok=True)
    d = Path(tempfile.mkdtemp(prefix="repo_", dir=tmp))   # carpeta nueva: en Windows .git/objects no se deja borrar
    git(d, "init", "-q")
    escribir(d, "pipeline/a.py", "A = 1\n")
    c0 = None
    escribir(d, "experiments/_s166_modd_f4/probe_f4.py", "import evaluar_f4 as E\nE.distancias\n")
    escribir(d, "experiments/_s166_modd_f4/evaluar_f4.py", EV)
    git(d, "add", "-A")
    c0 = git(d, "commit", "-q", "-m", "base")
    escribir(d, "pipeline/b.py", "B = 1\n")
    git(d, "add", "-A")
    cr = git(d, "commit", "-q", "-m", "runner")
    return d, c0, cr


def lectura(d, cr, rel, viejo, nuevo, desde=None):
    git(d, "checkout", "-q", "-B", "l", desde or cr)
    p = d / rel
    t = p.read_text(encoding="utf-8")
    chk(t.count(viejo) == 1, "el caso de prueba no aplica: %s" % viejo)
    p.write_text(t.replace(viejo, nuevo), encoding="utf-8")
    git(d, "add", "-A")
    return git(d, "commit", "-q", "-m", "lectura")


def parte_a(PR, tmp):
    d, c0, cr = repo(tmp)
    ev = "experiments/_s166_modd_f4/evaluar_f4.py"
    casos = [
        ("sólo cambia una def que el arnés no alcanza", ev, "return a * 2", "return a * 3", None, True),
        ("sólo cambia el bloque __main__", ev, "print(otra(1))", "print(otra(2))", None, True),
        ("cambia un archivo del runner (pipeline/)", "pipeline/a.py", "A = 1", "A = 2", None, False),
        ("cambia el arnés", "experiments/_s166_modd_f4/probe_f4.py", "E.distancias", "E.distancias\nE.otra", None,
         False),
        ("cambia una def alcanzable por cierre (ayuda)", ev, "return a + 1", "return a + 2", None, False),
        ("cambia la def nombrada (distancias)", ev, "return ayuda(a)", "return ayuda(a) * 1", None, False),
        ("cambia una sentencia de nivel de módulo", ev, "X = 1", "X = 2", None, False),
    ]
    malas = 0
    for nombre, rel, v, n, desde, espera in casos:
        cl = lectura(d, cr, rel, v, n, desde)
        r = PR.compatible(d, cr, cl)
        ok = r["ok"] is espera
        malas += not ok
        print("%s  A %-48s ok=%s (espera %s) %s" % ("OK   " if ok else "FALLA", nombre, r["ok"], espera,
                                                    {k: r[k] for k in ("desciende", "cambiados", "evaluar_distinto")}))
    # no desciende: rama hermana desde la base con los mismos archivos del runner (pipeline/b.py igual), así el único
    # motivo de rojo es la ascendencia
    git(d, "checkout", "-q", "-B", "h", c0)
    escribir(d, "pipeline/b.py", "B = 1" + chr(10))
    git(d, "add", "-A")
    ch =git(d, "commit", "-q", "-m", "hermana")
    r = PR.compatible(d, cr, ch)
    ok = r["ok"] is False and r["cambiados"] == [] and r["evaluar_distinto"] == []
    malas += not ok
    print("%s  A %-48s ok=%s (espera False) %s" % ("OK   " if ok else "FALLA", "la lectura no desciende del runner",
                                                   r["ok"], {k: r[k] for k in ("desciende", "cambiados")}))
    chk(not malas, "parte A: %d casos fallan" % malas)


def cab(parte, commit, tag, se, sp, de=4):
    return {"parte": parte, "de": de, "modo": "completo", "commit": commit, "tag": tag, "sha256_evaluar_f4": se,
            "sha256_probe_f4": sp}


def parte_b(X, tmp):
    CT, CR = "a" * 40, "b" * 40
    SE_L, SE_R, SP = "e_lectura", "e_runner", "p_igual"
    Path(tmp).mkdir(parents=True, exist_ok=True)
    art = Path(tempfile.mkdtemp(prefix="art_", dir=tmp))

    def correr(cabs, compat_ok=True, runner=True, txt=CR):
        for p in art.glob("procedencia_*.txt"):
            p.unlink()
        (art / "procedencia_0.txt").write_text("commit %s ref x\n" % txt, encoding="utf-8")
        rn = {"commit": CR, "tag": "tag_runner", "sha_evaluar": SE_R, "compat": {"ok": compat_ok}} if runner else None
        return X.procedencia(cabs, art, CT, "tag_lectura", SE_L, SP, runner=rn)

    todas_r = [cab(i, CR, "tag_runner", SE_R, SP) for i in range(4)]
    casos = [
        ("todas en el runner compatible", todas_r, {}, "OK"),
        ("la regla de compatibilidad no da ok", todas_r, {"compat_ok": False}, "INDECIDIBLE"),
        ("sin runner, todas en el runner", todas_r, {"runner": False}, "INDECIDIBLE"),
        ("una cabecera con otro commit", todas_r[:3] + [cab(3, "c" * 40, "tag_runner", SE_R, SP)], {}, "INDECIDIBLE"),
        ("una cabecera con otro sha de probe_f4", todas_r[:3] + [cab(3, CR, "tag_runner", SE_R, "otro")], {},
         "INDECIDIBLE"),
        ("una cabecera con el evaluar_f4 de la lectura", todas_r[:3] + [cab(3, CR, "tag_runner", SE_L, SP)], {},
         "INDECIDIBLE"),
        ("una cabecera con otro nombre de tag", todas_r[:3] + [cab(3, CR, "otro_tag", SE_R, SP)], {}, "INDECIDIBLE"),
        ("cabeceras que mezclan los dos tags", todas_r[:2] + [cab(i, CT, "tag_lectura", SE_L, SP) for i in (2, 3)],
         {}, "INDECIDIBLE"),
        ("un procedencia_N.txt con otro commit", todas_r, {"txt": "c" * 40}, "INDECIDIBLE"),
        ("todas en el tag de la lectura, sin runner", [cab(i, CT, "tag_lectura", SE_L, SP) for i in range(4)],
         {"runner": False, "txt": CT}, "OK"),
        ("todas en el tag de la lectura, con runner compatible", [cab(i, CT, "tag_lectura", SE_L, SP)
                                                                  for i in range(4)], {"txt": CT}, "OK"),
    ]
    malas = 0
    for nombre, cabs, kw, espera in casos:
        r = correr(cabs, **kw)
        ok = r["estado"] == espera
        malas += not ok
        print("%s  B %-48s %s (espera %s), malos %s" % ("OK   " if ok else "FALLA", nombre, r["estado"], espera,
                                                       r.get("n_malos")))
    chk(not malas, "parte B: %d casos fallan" % malas)


def parte_c(PR):
    try:
        cr = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", "s170-modd-f4-candado^{commit}"], capture_output=True,
                            text=True, check=True).stdout.strip()
        cl = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", "s170-modd-f4-candado-n01^{commit}"],
                            capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError:
        print("C  sin los tags en este checkout: no se prueba")
        return
    r = PR.compatible(RAIZ, cr, cl)
    print("%s  C caso real %s contra %s: ok=%s %s" % ("OK   " if r["ok"] else "FALLA", cr[:9], cl[:9], r["ok"],
                                                     {k: r[k] for k in ("cambiados", "evaluar_distinto")}))
    chk(r["ok"], "el caso real tiene que ser compatible")


def parte_d(X):
    """datos_runner sobre el repo real: el runner compatible da ok y el evaluar_f4 del commit del runner; un commit de
    lectura que no desciende del runner da ok falso."""
    try:
        cl = X.git("rev-parse", "s170-modd-f4-candado-n01^{commit}", raiz=RAIZ).strip()
        viejo = X.git("rev-parse", "314cec809^{commit}", raiz=RAIZ).strip()
    except Exception:  # noqa: BLE001
        print("D  sin los tags en este checkout: no se prueba")
        return
    r = X.datos_runner("s170-modd-f4-candado", cl, raiz=RAIZ)
    sha = X.sha256_lf(X.git("show", r["commit"] + ":" + X.REL_EVALUAR, raiz=RAIZ, binario=True))
    chk(r["compat"]["ok"] is True and r["sha_evaluar"] == sha and r["tag"] == "s170-modd-f4-candado",
        "datos_runner del caso real: %s" % {k: r[k] for k in ("commit", "tag", "sha_evaluar")})
    chk(X.datos_runner("s170-modd-f4-candado", viejo, raiz=RAIZ)["compat"]["ok"] is False,
        "datos_runner con una lectura que no desciende: tiene que dar ok falso")
    chk(X.datos_runner(None, cl, raiz=RAIZ) is None, "sin tag del runner no hay runner")
    print("OK     D datos_runner sobre el repo real")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(AQUI))
    ap.add_argument("--tmp", default=None)
    a = ap.parse_args()
    sys.path.insert(0, a.dir)
    tmp = a.tmp or tempfile.mkdtemp(prefix="proc_runner_")
    asercion = cae = 0
    try:
        PR = importlib.import_module("procedencia_runner")
        X = importlib.import_module("externos_f4")
    except Exception as e:  # noqa: BLE001
        print("NO CARGA", type(e).__name__, e)
        sys.exit(3)
    for nombre, f in (("parte_a", lambda: parte_a(PR, tmp)), ("parte_b", lambda: parte_b(X, tmp)),
                      ("parte_c", lambda: parte_c(PR)), ("parte_d", lambda: parte_d(X))):
        try:
            f()
            print("OK              ", nombre)
        except AssertionError as e:
            asercion += 1
            print("FALLA ASERCION  ", nombre, "|", e)
        except Exception as e:  # noqa: BLE001
            cae += 1
            print("CAE             ", nombre, "|", type(e).__name__, str(e)[:200])
    print("RESUMEN: 4 partes, %d fallan por aserción, %d caen" % (asercion, cae))
    sys.exit(0 if not (asercion or cae) else 1 if asercion else 2)


if __name__ == "__main__":
    main()
