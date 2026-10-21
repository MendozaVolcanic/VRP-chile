"""V2 / F5-01: cobertura de los tres brazos del A/B de D25 (run 39530508296, salidas del intento 1 en el commit
4b6d7f5f2 de la rama s146-ab/39530508296), leída por `git show` (sin checkout, sin tocar nada).

Qué se prueba: los tres controles de cobertura de evaluar_d25.evaluar() (líneas 504-525), con SUS funciones y SU
umbral, sobre los datos reales del brazo; y aparte, cuántas pasadas faltan contra la referencia de cobertura del
propio evaluador (claves_cobertura: histórico con K antes del 2026-09-18 y producción desde ahí), por día.

Pregunta 1: si al brazo le faltara un día entero, ¿estos controles lo verían? Se responde midiendo: se cuentan las
faltas por día y se aplica la regla del 5 % por volcán y sensor sobre la ventana entera.
Pregunta 2 (instrumento muerto): si los JSON del brazo vinieran vacíos, el total de pasadas sería 0; se imprime.
Control positivo: se le quita al brazo K, en memoria, una semana entera (2026-10-01 a 10-07) y se vuelve a aplicar
la regla del 5 %: tiene que saltar.
Denominador: pasadas VIIRS 375 y 750 (volcán|bucket|minuto), 11 Tier A, ventana V1 2026-08-29 a 2026-10-18.
"""
import sys, io, json, subprocess, collections, os
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "experiments" / "_s157_prereg_d25"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import evaluar_d25 as D  # noqa: E402

bp = D.bp
COMMIT = "4b6d7f5f2"
BASE = "experiments/_s146_ab_sin_test1/salidas/39530508296"
DESDE, HASTA = D.VENTANAS["V1"]["desde"], D.VENTANAS["V1"]["hasta"]
VOLS = list(bp.VOLS)

def brazo(n, v):
    out = subprocess.run(["git", "show", "%s:%s/%s/%s.json" % (COMMIT, BASE, D.BRAZOS[n], v)], cwd=RAIZ,
                         capture_output=True, env=dict(os.environ, MSYS_NO_PATHCONV="1"))
    if out.returncode:
        return None
    recs = json.loads(out.stdout.decode("utf-8"))["records"]
    return {"|".join((v, bp.bucket(r.get("sensor")), r["datetime_utc"][:16])) for r in recs
            if bp.bucket(r.get("sensor")) in D.SENS and DESDE <= r["datetime_utc"][:10] <= HASTA}

claves = {n: set() for n in ("K", "G", "D")}
for n in claves:
    for v in VOLS:
        s = brazo(n, v)
        if s is None:
            print("FALTA ARCHIVO", n, v)
        else:
            claves[n] |= s
print("pasadas VIIRS por brazo:", {n: len(s) for n, s in claves.items()})

# control 1 del evaluador: brazos contra K
for n in ("G", "D"):
    print("control 1 (%s contra K): le faltan %d, sobran %d" % (n, len(claves["K"] - claves[n]), len(claves[n] - claves["K"])))

# control 3 del evaluador: referencia de cobertura con su umbral
cob = D.claves_cobertura([str(RAIZ / "data" / "_s154_reproc_k_historico"), str(RAIZ / "data" / "mirova_equivalent")],
                         VOLS, DESDE, HASTA)
ref = set().union(*cob.values())
print("referencia de cobertura: %d pasadas" % len(ref))

def regla5(K):
    cortos, peor = [], 0.0
    for (v, s), ks in sorted(cob.items()):
        falta = {k for k in ks if k not in K}
        peor = max(peor, len(falta) / len(ks))
        if len(falta) > D.MAX_FALTA_COBERTURA * len(ks):
            cortos.append("%s %s: faltan %d de %d" % (v, s, len(falta), len(ks)))
    return cortos, peor

cortos, peor = regla5(claves["K"])
print("control 3 (regla del 5 %% por volcán y sensor): %d disparos; peor fracción %.3f" % (len(cortos), peor))
falta = ref - claves["K"]
por_dia = collections.Counter(k.split("|")[2][:10] for k in falta)
print("faltan en K contra la referencia: %d de %d (%.2f %%); por día: %s" % (len(falta), len(ref), 100 * len(falta) / len(ref), dict(sorted(por_dia.items()))))
dia18 = {k for k in ref if k.split("|")[2].startswith("2026-10-18")}
print("2026-10-18: referencia %d pasadas, K tiene %d" % (len(dia18), len(dia18 & claves["K"])))
sobra = claves["K"] - ref
print("en K y no en la referencia: %d %s" % (len(sobra), sorted(sobra)[:5]))

# control positivo: quitar una semana entera al brazo K
Kmenos = {k for k in claves["K"] if not ("2026-10-01" <= k.split("|")[2][:10] <= "2026-10-07")}
c2, p2 = regla5(Kmenos)
print("control positivo (sin la semana 10-01 a 10-07): %d disparos; peor fracción %.3f" % (len(c2), p2))
# y un día entero más (el 10-18 ya falta): cuántos días enteros puede faltar sin que salte
for ndias in range(1, 6):
    dias = ["2026-10-%02d" % (17 - i) for i in range(ndias)]
    Kd = {k for k in claves["K"] if k.split("|")[2][:10] not in dias}
    c3, p3 = regla5(Kd)
    print("  quitando además %d día(s) %s: disparos %d, peor fracción %.3f" % (ndias, dias, len(c3), p3))

# las protegidas: ¿cuántas pasadas de la referencia que faltan tienen alerta de MIROVA? (la regla de protegidas sin
# record sólo mira claves que están en algún brazo, por eso no puede verlas)
json.dump(sorted(falta), open(Path(__file__).with_name("f501_faltantes.json"), "w"), indent=0)

# Cuántas de las faltantes son pasadas con alerta de MIROVA (protegida A o cualquier ALERTA), con la referencia
# congelada de V1 y la función de protección del propio evaluador. V1 no es solo_tabla, así que no escribe nada.
cfg = dict(D.VENTANAS["V1"])
ref_f = D.E.archivos_ref(cfg, Path(__file__).parent)
prot = D.E.proteccion(sorted(falta), ref_f, DESDE, HASTA)
pa = sorted(k for k, v in prot.items() if v["A"])
print("faltantes con alerta protegida A (1 MW o más): %d -> %s" % (len(pa), pa))
filas = D.ev.cargar_referencia_unificada(Path(ref_f[0]), Path(ref_f[1]),
                                         **({"historico_path": ref_f[2]["historico"], "respaldo_path": ref_f[2]["respaldo"]} if ref_f[2] else {}))
por_vb, *_ = bp.indexar_referencia(filas, bp._coords_por_volcan(), (DESDE, HASTA))
from datetime import datetime, timezone
al = collections.Counter()
for k in falta:
    v, b, t = k.split("|")
    ff = bp.parear(por_vb.get((v, b), []), datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc))
    if any(bp.es_alerta(f["tipo"]) for f in ff):
        al[(v, b, t[:10])] += 1
print("faltantes con cualquier fila ALERTA de MIROVA a +-2 min: %d -> %s" % (sum(al.values()), dict(sorted(al.items()))))
# control positivo del pareo: sobre las pasadas que SÍ están en K, cuántas tienen ALERTA (tiene que ser > 0)
n_ok = 0
for k in list(claves["K"])[:4610]:
    v, b, t = k.split("|")
    ff = bp.parear(por_vb.get((v, b), []), datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc))
    n_ok += any(bp.es_alerta(f["tipo"]) for f in ff)
print("control positivo del pareo: pasadas de K con ALERTA: %d de %d" % (n_ok, len(claves["K"])))
