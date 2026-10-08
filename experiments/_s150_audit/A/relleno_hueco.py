"""S150 frente A: ¿el hueco del apagon (2026-10-02 08:00 a 2026-10-08) quedo rellenado?

Lee cada JSON de los 11 Tier A DESDE EL REMOTO (gh api contents, ref = sha que se pasa o main),
nunca del checkout local. Cuenta pasadas por noche (fecha UTC de datetime_utc) y por familia
(MODIS, V375, V750) y las compara con la mediana de las 7 noches previas (2026-09-25 a 10-01).

Pregunta 1 del instrumento: si el relleno no hubiera ocurrido, las noches 10-03 a 10-08 darian 0
(lo ve). Pregunta 2: si la descarga fallara, el script aborta (no informa ceros falsos); y una
noche con 0 se marca HUECO, distinta de una noche con menos pasadas que la base (PARCIAL).
Control positivo: las 7 noches de base deben tener pasadas en las tres familias.
Denominador: pasadas nocturnas almacenadas por el perfil mirova_equivalent (el store guarda una
fila por pasada con datos, detecte o no). Uso: python relleno_hueco.py [ref]
"""
import json, subprocess, sys, statistics, collections
sys.stdout.reconfigure(encoding="utf-8")
REF = sys.argv[1] if len(sys.argv) > 1 else "main"
TIER_A = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa",
          "Chaiten", "Villarrica", "NevadosDeChillan", "Llaima", "Copahue"]
BASE = [f"2026-09-{d:02d}" for d in range(25, 31)] + ["2026-10-01"]
HUECO = ["2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08"]
fam = lambda s: "MODIS" if "MODIS" in s else ("V750" if s.endswith("_750") else "V375")

def remoto(vol):
    out = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                          f"repos/MendozaVolcanic/VRP-chile/contents/data/mirova_equivalent/{vol}.json?ref={REF}"],
                         capture_output=True)
    if out.returncode != 0 or len(out.stdout) < 1000:
        sys.exit(f"ABORTA: no se pudo leer {vol} del remoto: {out.stderr[:200]!r}")
    return json.loads(out.stdout)["records"]

resumen = collections.Counter()
for v in TIER_A:
    rs = remoto(v)
    c = collections.Counter((r["datetime_utc"][:10], fam(r["sensor"])) for r in rs)
    ultimo = max(r["datetime_utc"] for r in rs)
    print(f"{v}: ultimo={ultimo}  n_total={len(rs)}")
    for f in ("MODIS", "V375", "V750"):
        base = [c[(d, f)] for d in BASE]
        med = statistics.median(base)
        celdas = []
        for d in HUECO:
            n = c[(d, f)]
            if n == 0: est = "HUECO"
            elif n < 0.6 * med: est = "PARCIAL"
            else: est = "ok"
            resumen[(f, d, est)] += 1
            celdas.append(f"{d[5:]}:{n}{'' if est == 'ok' else '(' + est + ')'}")
        print(f"   {f:5s} base(mediana 7 noches)={med:.0f} min_base={min(base)} | " + " ".join(celdas))
print("\nRESUMEN (volcanes por noche y familia):")
for f in ("MODIS", "V375", "V750"):
    print(f"  {f}: " + " ".join(f"{d[5:]} ok={resumen[(f, d, 'ok')]} parcial={resumen[(f, d, 'PARCIAL')]} hueco={resumen[(f, d, 'HUECO')]}"
                         for d in HUECO))
