# -*- coding: utf-8 -*-
"""Verificador S175 F2, A1 a A3. Script propio; usa la vara (banco_paridad, clase_mirova) del arbol base.

Uso: python v_a1_a3.py <arbol_base> <salida_json>
"""
import collections
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2])
sys.path.insert(0, str(ARBOL))
sys.path.insert(0, str(ARBOL / "scripts"))

import banco_paridad as bp  # noqa: E402
import clase_mirova as cm  # noqa: E402
import referencia_mirova_unificada as rmu  # noqa: E402
from pipeline.diurno import flag_viirs_diurno  # noqa: E402

VENT = ("2026-03-01", "2026-11-07")
assert Path(bp.__file__).resolve().parents[1] == ARBOL, bp.__file__
print("banco_paridad desde", bp.__file__, "| HTML", bp.HTML, "| DATA", bp.DATA)
print("flag_viirs_diurno =", flag_viirs_diurno())

coords = bp._coords_por_volcan()
inner = bp.inner_desde_html()
print("inner", inner)
ident = bp.control_identidad_predicado()
print("control identidad predicado (valid 5 casos, publica 2 casos):", ident)

filas = rmu.cargar_referencia_unificada(rmu.SNAP_CONS, rmu.SNAP_OCR)
print("filas referencia unificada", len(filas), "| ultima fecha V375:",
      max((f["fecha_utc"] for f in filas if f["sensor_bucket"] == "VIIRS375"), default=None))
por_vb, ns, nv, n = bp.indexar_referencia(filas, coords, VENT, regla_minimas="SN")
recs = bp.cargar_nuestros(coords, inner, VENT)
bp.etiquetar(recs, por_vb, ns, nv)
v = [r for r in recs if r["b"] == "VIIRS375"]
print("records nocturnos totales", len(recs), "| VIIRS375", len(v),
      "| sensores", collections.Counter(r["sensor"] for r in v))


def prot_filas(r, umbral=cm.UMBRAL_PROTEGIDA_MW):
    fs = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
    return [f for f in fs if cm.alerta_protegida(f, umbral=umbral)], fs


# ---------------- A1
prot = []
for r in v:
    pf, fs = prot_filas(r)
    if pf:
        r["_pf"] = pf
        r["_fs"] = fs
        prot.append(r)
claves = collections.Counter((r["vol"], r["sensor"], r["dt"]) for r in prot)
print("\nA1 protegidas con record:", len(prot), "| claves unicas (vol,sensor,dt):", len(claves),
      "| duplicadas:", sum(1 for c in claves.values() if c > 1))
print("   etiquetas de las protegidas:", collections.Counter(r["lab"] for r in prot))
pub = [r for r in prot if r["pub"]]
nopub = [r for r in prot if not r["pub"]]
print("   publicadas", len(pub), "no publicadas", len(nopub))
for r in sorted(nopub, key=lambda r: (r["vol"], r["dt"])):
    print("   NO PUB", r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"), "z", r["z"], "dc", r["dc"],
          "pc_dist", r["pc_dist"], "disp", r["disp"],
          "| filas MIROVA:", [(f["source"], f["tipo"], f["vrp_mw"], f.get("dist_km"), f["fecha_utc"]) for f in r["_fs"]])
# control: umbral 0 (toda alerta) debe subir el conteo; umbral 1e9 debe dar 0
n0 = sum(1 for r in v if prot_filas(r, 0.0)[0])
n9 = sum(1 for r in v if prot_filas(r, 1e9)[0])
print("   control umbral 0 ->", n0, "| umbral 1e9 ->", n9)

# por noche (volcan, fecha)
noches_prot = sorted({(r["vol"], r["noche"]) for r in prot})
pub_v375 = {(r["vol"], r["noche"]) for r in v if r["pub"]}
pub_any = {(r["vol"], r["noche"]) for r in recs if r["pub"]}
sin_v375 = [k for k in noches_prot if k not in pub_v375]
sin_any = [k for k in noches_prot if k not in pub_any]
print("   noches con protegida:", len(noches_prot), "| sin publicacion V375 esa noche:", sin_v375,
      "| sin publicacion de ningun sensor:", sin_any)
for r in nopub:
    k = (r["vol"], r["noche"])
    otras = [(x["sensor"], x["dt"].strftime("%H:%M"), x["pub"], x["lab"]) for x in recs
             if (x["vol"], x["noche"]) == k and x["pub"]]
    print("   noche", k, "publicadas esa noche:", otras)

# ---------------- A2
def zb(z):
    return None if z is None else (z >= 50)
cz = collections.Counter((zb(r["z"]), bool(r["pub"])) for r in prot)
print("\nA2 (z>=50?, publica) ->", dict(cz))
print("   z None en protegidas:", sum(1 for r in prot if r["z"] is None))
print("   z de las no publicadas:", [r["z"] for r in nopub])
# borde: z exactamente 50 o casi
print("   protegidas con z en [49.5, 50.5]:", [(r["vol"], r["z"]) for r in prot if r["z"] is not None and 49.5 <= r["z"] <= 50.5])

# ---------------- A3
neg = [r for r in v if r["lab"] == "neg_limpio"]
print("\nA3 negativos limpios V375:", len(neg), "publicados", sum(r["pub"] for r in neg))
pv = collections.defaultdict(lambda: [0, 0])
for r in neg:
    pv[r["vol"]][0] += r["pub"]
    pv[r["vol"]][1] += 1
for k in sorted(pv):
    print("   ", k, pv[k])
dmax = max((r["disp"] for r in neg if r["pub"]), default=None)
print("   display maximo en neg publicados:", dmax, "| con disp>=1:", sum(1 for r in neg if r["pub"] and r["disp"] >= 1))
print("   top 5 disp neg publicados:", sorted(((round(r["disp"], 3), r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M"))
                                             for r in neg if r["pub"]), reverse=True)[:5])
# control: el disp de las protegidas publicadas debe tener valores >=1 (instrumento vivo)
print("   control: protegidas publicadas con disp>=1:", sum(1 for r in pub if r["disp"] >= 1), "de", len(pub))
# control: etiquetas en V375
print("   etiquetas V375:", collections.Counter(r["lab"] for r in v))
print("   neg limpios por fecha max:", max((r["noche"] for r in neg), default=None))

OUT.write_text(json.dumps({
    "prot": [{"vol": r["vol"], "sensor": r["sensor"], "dt": r["dt"].isoformat(), "pub": r["pub"], "z": r["z"],
              "disp": r["disp"]} for r in prot],
    "v375": [{"vol": r["vol"], "sensor": r["sensor"], "dt": r["dt"].isoformat(), "pub": r["pub"], "lab": r["lab"],
              "disp": r["disp"]} for r in v]}, ensure_ascii=False), encoding="utf-8")
print("listo ->", OUT)
