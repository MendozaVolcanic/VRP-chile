# -*- coding: utf-8 -*-
"""Verificador S159 N, paso 3: estimador alternativo de los negativos que F enciende, por censo de elegibles.

POR QUE: F no toca la deteccion (mismo hot_mask que K), solo el fondo y la suma. Entonces F solo puede encender un
negativo donde K ya tiene un cumulo de cumbre que no publica (0,0 MW). Ese conjunto se cuenta en la poblacion
entera (records de produccion), sin muestreo. Si los 6 eventos son un subconjunto de esos elegibles, la tasa de
encendido entre elegibles muestreados por la cantidad de elegibles en la poblacion es un estimador mas firme que
el peso por volcan y cenit.
P1: si F encendiera algo fuera de los elegibles (deteccion distinta), se cuenta y la premisa cae. P2: si no hubiera
elegibles en la poblacion, el estimador daria 0 y no 152: un cero distinguible.
Ventana: VIIRS 750 nocturnas 2026-04-01 a 2026-10-21, sin 10-18/10-19.
"""
import collections, io, json, sys
from pathlib import Path
from scipy.stats import beta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; N = AQUI.parent
obj = {o["id"]: o for o in json.loads((N / "objetivos_n.json").read_text(encoding="utf-8"))}
V = json.load(open(AQUI / "v1_pub.json")); P = {(int(k.split("|")[0]), k.split("|")[1]): v for k, v in V["P"].items()}
ok = set(V["ok"]); pub = lambda i, b: P.get((i, b), False)
res = {}
for f in sorted((N / "run_39682867040").glob("*resultados_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r.get("estado") == "ok" or r["id"] not in res:
            res[r["id"]] = r
pob = [p for p in json.loads((N / "poblacion_completa.json").read_text(encoding="utf-8"))["pasadas"]
       if p["hora_utc"][:10] not in ("2026-10-18", "2026-10-19")]
eleg = lambda p: p["lab"] == "neg_limpio" and not p["pub_prod"] and p.get("dc") == "summit" and p.get("pc_vrp") == 0.0
negs = [p for p in pob if p["lab"] == "neg_limpio"]
print("negativos limpios en la poblacion:", len(negs), "| publicados por produccion:", sum(p["pub_prod"] for p in negs))
print("dc y pc_vrp de los no publicados:", collections.Counter((p.get("dc"), p.get("pc_vrp") == 0.0 if p.get("pc_vrp") is not None else None)
                                                            for p in negs if not p["pub_prod"]))
E = [p for p in pob if eleg(p)]
print("ELEGIBLES (neg no publicado, cumbre, pc 0,0 MW):", len(E), "por volcan y cenit:",
      dict(sorted(collections.Counter((p["volcan"], p["estrato_z"]) for p in E).items())))
# en la muestra
mues = [i for i in ok if obj[i]["clase"] == "neg_resto" and obj[i]["peso"] > 0]
me = [i for i in mues if eleg(obj[i])]
ev = [i for i in mues if pub(i, "F") and not pub(i, "K")]
print("muestra neg_resto ok:", len(mues), "| elegibles en la muestra:", len(me), "| eventos:", len(ev),
      "| eventos fuera de elegibles:", [i for i in ev if i not in me])
print("elegibles muestreados por volcan y cenit (n, encendidos):",
      {k: (sum(1 for i in me if (obj[i]['volcan'], obj[i]['estrato_z']) == k), sum(1 for i in ev if (obj[i]['volcan'], obj[i]['estrato_z']) == k))
       for k in sorted({(obj[i]['volcan'], obj[i]['estrato_z']) for i in me})})
# misma deteccion: F y K mismo numero de pixeles y mismo cumulo en todas las pasadas
dd = [i for i in ok if (((res[i]["brazos"]["F"]["record"] or {}).get("primary_cluster") or {}).get("n_pixels")
                        != ((res[i]["brazos"]["K"]["record"] or {}).get("primary_cluster") or {}).get("n_pixels"))
      or res[i]["brazos"]["F"].get("n_hot") != res[i]["brazos"]["K"].get("n_hot")]
print("pasadas donde F cambia la deteccion (n_hot o n_pixels del cumulo):", len(dd))
k, n = len(ev), len(me)
lo, hi = (beta.ppf(0.025, k, n - k + 1) if k else 0.0), beta.ppf(0.975, k + 1, n - k)
print(f"tasa entre elegibles {k}/{n} = {k/n:.3f}, Clopper-Pearson 95 % [{lo:.3f}, {hi:.3f}]")
print(f"encendidos estimados = {k/n*len(E):.1f} [{lo*len(E):.1f}, {hi*len(E):.1f}] (dE = encendidos - 48)")
# por estrato de cenit: elegibles z<=40 vs z>40
for z in ("z<=40", "z>40"):
    Ez = [p for p in E if p["estrato_z"] == z]; mz = [i for i in me if obj[i]["estrato_z"] == z]; ez = [i for i in ev if obj[i]["estrato_z"] == z]
    kz, nz = len(ez), len(mz)
    if nz:
        lo, hi = (beta.ppf(0.025, kz, nz - kz + 1) if kz else 0.0), beta.ppf(0.975, kz + 1, nz - kz)
        print(f"  {z}: elegibles pob {len(Ez)}, muestra {nz}, eventos {kz} -> {kz/nz*len(Ez):.1f} [{lo*len(Ez):.1f}, {hi*len(Ez):.1f}]")
# todos los K en 0,0 MW de la muestra (cualquier clase) y cuantos publica F
z0 = [i for i in ok if ((res[i]["brazos"]["K"]["record"] or {}).get("primary_cluster") or {}).get("vrp_mw") == 0.0]
print("pasadas con K en 0,0 MW:", len(z0), "por clase:", collections.Counter(obj[i]["clase"] for i in z0),
      "| F publica:", collections.Counter((obj[i]["clase"], pub(i, "F")) for i in z0))
