"""R7 (poder) para el evaluador de la corona S126 (experiments/_s126_corona/01_veredicto.py), segun el plan §11.2b.

Semilla sellada antes de correr: 20261022 (escrita en INFORME.md §R7 antes de la primera ejecucion).

Que hace: carga los brazos y la referencia una sola vez con el codigo del evaluador (parte A: hasta la linea
`mir, diurnas = cargar_mirova(VENTANA)`), y despues ejecuta 1.000 veces la parte B (los 7 criterios y el veredicto)
con las ETIQUETAS DE MIROVA BARAJADAS DENTRO DE CADA ESTRATO (volcan x sensor): los valores de VRP de MIROVA de ese
estrato se reparten al azar entre las noches que el control proceso en ese estrato, con el mismo numero de alertas.
Cuenta en cuantos barajados el veredicto es "ADOPTAR" y da el intervalo de Wilson al 95 %.

Pregunta 1: si el instrumento aprobara con etiquetas al azar, se veria? Si: la fraccion de ADOPTAR subiria sobre 5 %.
Pregunta 2: si el barajado no cambiara nada, se veria? Si: se imprime la fraccion de barajados en que `mir` quedo
identico al original (debe ser ~0) y el veredicto real sin barajar (control positivo del harness: debe reproducir
NO ADOPTAR con los criterios 2 y 5 fallando).

Uso: python r7_barajado_s126.py <RAIZ> <brazo_corona> [n]
"""
import io, os, sys, re, random, json, math, copy

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
raiz, brazo = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
SEMILLA = 20261022
ev = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_s126_corona", "01_veredicto.py")
src = open(ev, encoding="utf-8").read()
src = src.replace('sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")',
                  "import _s126_lib as _l; _l.ROOT = %r; ROOT = %r" % (raiz, raiz), 1)
src = re.sub(r'"corona":\s*"[^"]+"', '"corona": "%s"' % brazo, src, count=1)
src = re.sub(r'"ctx_off":\s*"[^"]+"', '"ctx_off": "_no_existe"', src, count=1)
src = re.sub(r'"corona\+ctx_off":\s*"[^"]+"', '"corona+ctx_off": "_no_existe"', src, count=1)
corte = "mir, diurnas = cargar_mirova(VENTANA)"
assert corte in src
a, b = src.split(corte, 1)
a = a + corte + "\n"
# parte B sin la escritura del json
b = re.sub(r'dest = os\.path\.join\([^\n]*\n', "dest = os.devnull\n", b)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(ev)), ".."))
g = {"__name__": "__main__", "__file__": os.path.abspath(ev)}
exec(compile(a, ev, "exec"), g)
mir0 = copy.deepcopy(g["mir"])
nulo = io.StringIO()


def correr(mir):
    g["mir"] = mir
    real = sys.stdout; sys.stdout = nulo
    try:
        exec(compile(b, ev, "exec"), g)
    finally:
        sys.stdout = real
    return g["res"]["veredicto"], list(g["res"]["criterios_que_fallan"])


v0, f0 = correr(copy.deepcopy(mir0))
print("sin barajar (control positivo del harness):", v0, f0)
# noches disponibles por estrato: las del control (datos['control'][vol]) por bucket
from _s126_lib import bucket  # noqa: E402
datos = g["datos"]
rng = random.Random(SEMILLA)
adoptar = 0; identicos = 0; fallas = {}
for it in range(N):
    mir = {}
    for vol, d in mir0.items():
        mir[vol] = {}
        por_b = {}
        for (f, bk), v in d.items():
            por_b.setdefault(bk, []).append(v)
        noches = {}
        for (dt, s) in datos["control"].get(vol, {}):
            noches.setdefault(bucket(s), set()).add(dt[:10])
        for bk, vals in por_b.items():
            uni = sorted(noches.get(bk, set()) | {f for (f, b2) in d if b2 == bk})
            eleg = rng.sample(uni, min(len(vals), len(uni)))
            for f, v in zip(eleg, vals):
                mir[vol][(f, bk)] = v
    if mir == mir0:
        identicos += 1
    v, f = correr(mir)
    if v == "ADOPTAR":
        adoptar += 1
    for k in f:
        fallas[k] = fallas.get(k, 0) + 1
p = adoptar / N
z = 1.96; den = 1 + z * z / N; cen = (p + z * z / (2 * N)) / den; rad = z * math.sqrt(p * (1 - p) / N + z * z / (4 * N * N)) / den
lo, hi = cen - rad, cen + rad
print("semilla %d | barajados %d | ADOPTAR en %d (%.3f) | Wilson 95%% [%.3f, %.3f] | barajados identicos al original: %d" % (SEMILLA, N, adoptar, p, lo, hi, identicos))
print("criterios que fallan (veces de %d):" % N, json.dumps(fallas, ensure_ascii=False))
print("R7:", "FALLA" if lo > 0.05 else ("OK" if hi < 0.05 else "SIN PODER CONCLUYENTE"))
