"""VX S175: datos de la base 752d348bc para los veredictos 111 y 256, por un camino distinto al de los auditores.

Qué hace:
 1. Extrae con `git show 752d348bc:data/mirova_equivalent/<v>.json` los 11 Tier A a mi temporal y compara su sha256 con la
    copia que usó F0 (C:\\Users\\nmend\\vrp-temporales\\s175_audit\\f0\\base_data). Si no coinciden, F0 midió otra cosa.
 2. (111) Fracción de records MODIS NRT por mes y por día desde 2026-10-25, medida por DOS instrumentos: el campo
    `product_version` (el de F0) y el nombre del gránulo (`.NRT.` en el nombre, independiente del campo). Si los dos
    discrepan, uno de los dos miente. Control positivo: tiene que haber algún record con `.NRT.` en el nombre.
    Pregunta 1 (si el Standard dejara de llegar, ¿lo vería?): sí, la fracción por nombre subiría a 100 %.
    Pregunta 2 (instrumento muerto): la columna `sin_campo`/`sin_granule` lo delataría.
 3. (256) Records MODIS por valor de `via_codigo_mirova` (True / sin_grilla / sin_mxd03 / geo_distinta / ausente), con
    el primer y último `datetime_utc` y `processed_utc` de los True. Control positivo: los records anteriores al PR B
    tienen que salir «ausente» (K no escribe la llave) y los posteriores True.
Denominador: todos los records con sensor MODIS_* de los 11 Tier A en la base; ventana: la que traiga cada archivo.
Salida: vx_datos_base_salida.txt y vx_datos_base_out.json al lado de este script.
"""
import hashlib
import io
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378"
BASE = "752d348bc67190e53b610989877e2405d238a1bc"
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\vx\base_data"
F0 = r"C:\Users\nmend\vrp-temporales\s175_audit\f0\base_data"
AQUI = os.path.dirname(os.path.abspath(__file__))
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
os.makedirs(TMP, exist_ok=True)


def sha(b):
    return hashlib.sha256(b).hexdigest()


out = {"base": BASE, "sha_iguales_f0": {}, "pv_mes": {}, "pv_dia": {}, "nombre_mes": {}, "discrepancias_pv_nombre": [],
       "via": {}, "via_primero": None, "via_ultimo": None, "via_true_processed_min": None, "nrt_viejos": [],
       "llaves_geo": {}}
pv_mes, pv_dia, nom_mes = defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
via = Counter(); via_true = []; llaves = Counter()
tot_modis = 0
for v in VOLS:
    p = subprocess.run(["git", "-C", REPO, "-c", "core.autocrlf=false", "show", f"{BASE}:data/mirova_equivalent/{v}.json"],
                       capture_output=True)
    assert p.returncode == 0, v
    b = p.stdout
    with open(os.path.join(TMP, f"{v}.json"), "wb") as f:
        f.write(b)
    f0p = os.path.join(F0, f"{v}.json")
    igual = os.path.exists(f0p) and sha(open(f0p, "rb").read()) == sha(b)
    out["sha_iguales_f0"][v] = igual
    recs = json.loads(b.decode("utf-8"))["records"]
    for r in recs:
        if not str(r.get("sensor", "")).startswith("MODIS"):
            continue
        tot_modis += 1
        d = r.get("datetime_utc", "")
        pv = r.get("product_version", "sin_campo")
        g = r.get("granule")
        nom = "sin_granule" if not g else ("nrt" if ".NRT." in g else "standard")
        pv_mes[d[:7]][pv] += 1
        nom_mes[d[:7]][nom] += 1
        if d >= "2026-10-25":
            pv_dia[d[:10]][pv] += 1
        if g and nom != pv:
            out["discrepancias_pv_nombre"].append({"volcan": v, "datetime_utc": d, "product_version": pv, "granule": g})
        if pv == "nrt" and d < "2026-11-04":
            out["nrt_viejos"].append({"volcan": v, "datetime_utc": d, "granule": g, "processed_utc": r.get("processed_utc")})
        vc = r.get("via_codigo_mirova", "ausente")
        via[str(vc)] += 1
        if vc is True:
            via_true.append((d, r.get("processed_utc"), v))
        for k in r:
            if "geo" in k.lower() or "mxd03" in k.lower():
                llaves[k] += 1
        dg = r.get("diag_codigo_mirova")
        if isinstance(dg, dict):
            for k in dg:
                if "geo" in k.lower():
                    llaves["diag_codigo_mirova." + k] += 1

out["total_records_modis"] = tot_modis
out["pv_mes"] = {m: dict(c) for m, c in sorted(pv_mes.items())}
out["nombre_mes"] = {m: dict(c) for m, c in sorted(nom_mes.items())}
out["pv_dia"] = {m: dict(c) for m, c in sorted(pv_dia.items())}
out["via"] = dict(via)
out["llaves_geo"] = dict(llaves)
if via_true:
    via_true.sort()
    out["via_primero"] = via_true[0]
    out["via_ultimo"] = via_true[-1]
    out["via_true_processed_min"] = min(x[1] for x in via_true if x[1])
    out["via_true_n"] = len(via_true)

print(f"base {BASE}; records MODIS 11 Tier A = {tot_modis}")
print("sha256 copia F0 == base:", out["sha_iguales_f0"])
print("\n(111) product_version por mes (últimos 8) y por nombre del gránulo:")
for m in sorted(pv_mes)[-8:]:
    t = sum(pv_mes[m].values())
    print(f"  {m} campo={dict(pv_mes[m])} nombre={dict(nom_mes[m])} nrt_campo={100*pv_mes[m].get('nrt',0)/t:.1f}% "
          f"nrt_nombre={100*nom_mes[m].get('nrt',0)/t:.1f}%")
print("  por día desde 2026-10-25:", out["pv_dia"])
print("  discrepancias campo vs nombre:", len(out["discrepancias_pv_nombre"]), out["discrepancias_pv_nombre"][:5])
print("  records nrt con fecha anterior al 2026-11-04 (todavía sin upgrade a Standard):", out["nrt_viejos"])
print("\n(256) via_codigo_mirova:", out["via"])
print("  primer True (datetime_utc, processed_utc, volcán):", out["via_primero"])
print("  último True:", out["via_ultimo"], "; processed_utc mínimo de los True:", out["via_true_processed_min"])
print("  llaves con 'geo' o 'mxd03' en los records MODIS:", out["llaves_geo"])
with open(os.path.join(AQUI, "vx_datos_base_out.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
