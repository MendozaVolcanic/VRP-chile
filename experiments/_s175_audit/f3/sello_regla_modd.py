# -*- coding: utf-8 -*-
"""F3 S175: el texto sellado de la regla MOD-D (sha256 LF 7f300a14 segun la cabecera) sigue igual en la base?
Compara el archivo en 3a3b5e495 (ronda 5, antes del sello) con el de la base sin la cabecera de sello y con el del tag.
P1: un cambio de un byte en el cuerpo cambiaria el sha256 (lo veria). P2: si git show falla, imprime SIN DATO.
Control positivo: el sha de 3a3b5e495 tiene que empezar con 7f300a14 (lo dice la cabecera)."""
import hashlib, subprocess, sys, io, difflib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
P = "experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md"
def get(c):
    r = subprocess.run(["git", "show", f"{c}:{P}"], capture_output=True)
    return r.stdout.replace(b"\r\n", b"\n") if r.returncode == 0 else None
pre = get("3a3b5e495"); base = get("752d348bc"); tag = get("s173-regla-modd-sellada")
for n, t in (("3a3b5e495", pre), ("752d348bc", base), ("tag s173-regla-modd-sellada", tag)):
    print(n, "SIN DATO" if t is None else hashlib.sha256(t).hexdigest()[:16], None if t is None else len(t))
if pre and base:
    a = pre.decode("utf-8").split("\n"); b = base.decode("utf-8").split("\n")
    d = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
    print("lineas distintas entre ronda 5 y base:", len(d))
    for l in d[:30]: print("  ", l[:200])
if tag and base: print("tag == base:", tag == base)
