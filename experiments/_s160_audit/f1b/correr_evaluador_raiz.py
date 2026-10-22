"""Corre un evaluador viejo (S125 02_veredicto_ab.py, S126 01_veredicto.py) sobre una raiz falsa con brazos
placebo, sin tocar el evaluador original ni el repo.

Lo que hace: lee el codigo fuente del evaluador, reemplaza (a) la raiz desde donde lee data/<brazo> y la referencia
(ROOT), (b) las entradas de BRAZOS que se pidan, (c) el archivo JSON de salida, y lo ejecuta. Es el mismo codigo del
evaluador; solo cambian sus entradas. Las sustituciones se imprimen y se cuentan: si alguna no aplica, el script
falla (pregunta 2: un evaluador que no lee de la raiz falsa daria el veredicto de siempre y pareceria OK).

Uso: python correr_evaluador_raiz.py <evaluador.py> <RAIZ> <salida.json> clave=brazo [clave=brazo ...]
"""
import io, os, re, sys, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ev, raiz, salida = sys.argv[1:4]
sust = dict(a.split("=", 1) for a in sys.argv[4:])
src = open(ev, encoding="utf-8").read()
n = 0

# (a) raiz
for pat in (r'ROOT = os\.path\.join\(os\.path\.dirname\(__file__\), "\.\.", "\.\."\)',
            r'ROOT = os\.path\.dirname\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)'):
    src, k = re.subn(pat, "ROOT = %r" % raiz, src); n += k
# el evaluador de S126 toma ROOT de _s126_lib: se parchea el modulo
src = src.replace("sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=\"utf-8\")",
                  "import _s126_lib as _l; _l.ROOT = %r; ROOT = %r" % (raiz, raiz), 1) if "_s126_lib" in src else src
# (b) brazos
for k, v in sust.items():
    pat = r'"%s":\s*"[^"]+"' % re.escape(k)
    src, c = re.subn(pat, '"%s": "%s"' % (k, v), src, count=1)
    print("sustitucion %s -> %s: %d" % (k, v, c)); n += c
    if c == 0:
        raise SystemExit("no se pudo sustituir el brazo %s" % k)
# (c) salida
src, c = re.subn(r'dest = os\.path\.join\(os\.path\.dirname\([^\n]*\)', "dest = %r" % salida, src); n += c
print("sustituciones aplicadas:", n, "| salida:", salida)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(ev)), ".."))
g = {"__name__": "__main__", "__file__": os.path.abspath(ev)}
exec(compile(src, ev, "exec"), g)
