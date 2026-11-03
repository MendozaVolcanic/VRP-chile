# -*- coding: utf-8 -*-
"""Prueba sin red (y sin pyhdf) de los controles del arnés S173. Corre en Windows y en el runner antes de la ablación.

Qué comprueba, y por qué cada cosa puede fallar:
  1. Escena sintética en la grilla de MIROVA de Chillán, con un foco caliente sobre una cumbre más fría que el anillo:
     V0 por procesar_grilla con el patch = vrp_mirova de la vía (el patch no altera nada cuando el brazo es V0);
     X2 dobla el VRP sin mover celdas; FA cambia el VRP y, con el anillo tibio, lo baja; SC = V0 con un solo cúmulo;
     FSH distinto de V0. Si el patch no se aplicara, X2 y FA darían V0 y la prueba falla.
  2. Brazo nativo sobre una escena sintética con la grilla nativa = la de MIROVA (paso 1 km, centros sobre los
     centros de celda): NAT tiene que dar la misma máscara que V0 (mismo detector, mismos píxeles); con píxeles
     nativos de 2 km NAT tiene que dar distinto de V0 (control de que el remuestreo actúa).
  3. Workflow: clave "on" string, sólo workflow_dispatch, sólo EARTHDATA_TOKEN, sin push, grupo de concurrencia propio.
  4. Lista de pasadas: campos, cenit, VRP de MIROVA y gránulo en todas; ninguna repetida.
  5. Si existen en disco (sólo en el computador de Nicolás), grillas capturadas del A/B de MOD-D: V0 = captura.
Sale con código 1 si algo falla.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (RAIZ, RAIZ / "scripts", AQUI):
    sys.path.insert(0, str(_p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np  # noqa: E402
import yaml  # noqa: E402
import piezas as PZ  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline import profile as PF  # noqa: E402

FALLAS = []


def ok(cond, msg):
    print(("OK    " if cond else "FALLA ") + msg, flush=True)
    if not cond:
        FALLAS.append(msg)


VOL = (-36.863, -71.377)
G = MV.grilla_del_volcan("NevadosDeChillan", paso_m=1000.0, clave_roi="roi_modis")
ok(G is not None and G["n"] == 51, "grilla de MIROVA de Chillán (51 x 51, 1 km)")
ok((PF.BG_INNER_KM, PF.BG_OUTER_KM) == (PZ.BG_INNER_KM, PZ.BG_OUTER_KM), "anillo de FA = el de profile.py")


def escena_grilla(rng):
    """MIR y TIR en radiancia: cumbre fría en el centro (radio 4 km), anillo 8 K más tibio, foco de 3 celdas."""
    d = PZ.dist_celdas_km(G, *VOL)
    t = np.where(d < 4, 263.0, 271.0) + rng.normal(0, 0.3, d.shape)
    pos = MV.posicion_de(G, *VOL)
    f, c = int(round(pos[0])), int(round(pos[1]))
    t_mir = t.copy()
    t_mir[f, c] += 14.0
    t_mir[f, c + 1] += 9.0
    t_mir[f + 1, c] += 6.0
    mir = MV.temperatura_a_radiancia(t_mir, PZ.LAM)
    tir = MV.temperatura_a_radiancia(t - 15.0, PZ.FAM["lam_tir"])
    box = MV.caja_roi(G.get("roi", "def"), n=G["n"], celda_crater=MV.celda_de(G, *VOL), inner_km=5.0,
                      lado_sensible=PZ.FAM["lado_sensible"], lado_anillo=PZ.FAM["lado_anillo"], paso_m=G["paso"])
    return mir, tir, box, pos


rng = np.random.default_rng(173)
mir, tir, box, pos = escena_grilla(rng)
mask = MV.detectar_mirova(mir, tir, box, 0, 90.0, lam_mir=PZ.LAM, lam_tir=PZ.FAM["lam_tir"])
v = MV.vrp_mirova(mir, mask, coef=PZ.COEF)
ok(v["npix"] > 0, f"escena sintética: la vía detecta ({v['npix']} celdas)")
r = {b: PZ.correr_en_grilla(b, mir, tir, G, box, 0, 90.0, pos, 5.0, "MODIS_AQUA", VOL) for b in PZ.BRAZOS_GRILLA}
ok(r["V0"]["vrp_mw"] == round(v["VRP_MW"], 3), "V0 con el patch = vrp_mirova de la vía")
ok(abs(r["X2"]["vrp_mw"] - 2 * r["V0"]["vrp_mw"]) <= 0.0015 and
   PZ.resumen(r["X2"])["celdas"] == PZ.resumen(r["V0"])["celdas"], "X2 dobla el VRP sin mover celdas")
ok(r["FA"]["vrp_mw"] < r["V0"]["vrp_mw"], f"FA (anillo tibio) baja el VRP: {r['FA']['vrp_mw']} < {r['V0']['vrp_mw']}")
ok(r["FSH"]["vrp_mw"] != r["V0"]["vrp_mw"], "FSH cambia el VRP")
ok(r["SC"]["vrp_mw"] == r["V0"]["vrp_mw"], "SC = V0 con un solo cúmulo")
ok(MV.vrp_mirova is not None and MV.vrp_mirova is PZ._VRP_VIA, "el patch se deshace al salir (vrp_mirova original)")

# ---------------------------------------------------------------------------- 2. nativo
from pyproj import Transformer  # noqa: E402
n, paso = G["n"], G["paso"]
X, Y = np.meshgrid(G["ul_x"] + paso * (np.arange(n) + 0.5), G["ul_y"] - paso * (np.arange(n) + 0.5))
tinv = Transformer.from_crs(f"EPSG:{G['epsg']}", "EPSG:4326", always_xy=True)
lon_n, lat_n = (np.asarray(a) for a in tinv.transform(X, Y))
rad = {"MIR": mir, "TIR": tir}
nat = PZ.correr_nativo(rad, lat_n, lon_n, G, VOL, 5.0, 0, 90.0)
ok(nat["npix"] == v["npix"] and abs(nat["vrp_mw"] - round(v["VRP_MW"], 3)) <= 0.0015,
   f"NAT sobre píxeles nativos = celdas de la grilla da lo mismo que V0 ({nat['npix']} / {nat['vrp_mw']} contra "
   f"{v['npix']} / {round(v['VRP_MW'], 3)})")
sl = (slice(0, None, 2), slice(0, None, 2))
nat2 = PZ.correr_nativo({"MIR": mir[sl], "TIR": tir[sl]}, lat_n[sl], lon_n[sl], G, VOL, 5.0, 0, 90.0)
ok((nat2["npix"], nat2["vrp_mw"]) != (v["npix"], round(v["VRP_MW"], 3)),
   f"NAT con píxeles de 2 km cambia (control de que el remuestreo actúa): {nat2['npix']} / {nat2['vrp_mw']}")

# ---------------------------------------------------------------------------- 3. workflow
wf_path = RAIZ / ".github/workflows/s173-cenit-modis.yml"
txt = wf_path.read_text(encoding="utf-8")
wf = yaml.safe_load(txt)
ok("on" in wf and True not in wf, 'workflow: la clave "on" es string (A43)')
ok(list(wf["on"].keys()) == ["workflow_dispatch"], "workflow: sólo workflow_dispatch")
ok(wf.get("concurrency", {}).get("group") == "s173-cenit-modis", "workflow: grupo de concurrencia propio")
ok("EARTHDATA_TOKEN" in txt and "EARTHDATA_USERNAME" not in txt and "EARTHDATA_PASSWORD" not in txt,
   "workflow: sólo EARTHDATA_TOKEN (A71)")
ok('if [ -z "$EARTHDATA_TOKEN" ]' in txt, "workflow: falla si el token viene vacío")
ok("git push" not in txt and "contents: write" not in txt, "workflow: sin push y con permiso de sólo lectura")

# ---------------------------------------------------------------------------- 3b. login antes de bajar (VMODIS-01)
# Por AST y no por subcadena (A92): en main() del arnés tiene que haber una llamada a auth() importada de pipeline.fetch,
# precedida por el corte si EARTHDATA_TOKEN viene vacío, y antes de la primera llamada a medir() (que es la que baja).
import ast  # noqa: E402
arbol = ast.parse((AQUI / "ablacion_cenit_modis.py").read_text(encoding="utf-8"))
fmain = next(n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == "main")
def _linea_llamada(nombre):
    ls = [n.lineno for n in ast.walk(fmain) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == nombre]
    return min(ls) if ls else None
l_auth, l_medir = _linea_llamada("auth"), _linea_llamada("medir")
imp_auth = any(isinstance(n, ast.ImportFrom) and n.module == "pipeline.fetch" and any(a.name == "auth" for a in n.names)
               for n in ast.walk(fmain))
l_token = min((n.lineno for n in ast.walk(fmain) if isinstance(n, ast.Constant) and n.value == "EARTHDATA_TOKEN"), default=None)
ok(imp_auth and l_auth is not None and l_medir is not None and l_auth < l_medir,
   f"arnés: auth() de pipeline.fetch antes de medir() (líneas {l_auth} y {l_medir})")
ok(l_token is not None and l_auth is not None and l_token < l_auth, "arnés: corta si EARTHDATA_TOKEN viene vacío antes del login")

# ---------------------------------------------------------------------------- 3c. K y V fijan el flag (VER937)
# Desde #934 el perfil trae enable_modis_codigo_mirova en True: un brazo que no fija el flag es V aunque se llame K.
# Cada llamada a procesar_brazo de medir() tiene que estar dentro de un patch.object(pm, "ENABLE_MODIS_CODIGO_MIROVA", v)
# y entre las dos tienen que estar False (K) y True (V).
fmedir = next(n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == "medir")
def _es_brazo(n):
    return isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "procesar_brazo"
todas = {id(n) for n in ast.walk(fmedir) if _es_brazo(n)}
fijadas, valores = set(), []
for w in (n for n in ast.walk(fmedir) if isinstance(n, ast.With)):
    for it in w.items:
        c = it.context_expr
        # VER937b: el primer argumento tiene que ser `pm` (process_modis, el único lector del flag); un patch sobre
        # pipeline.profile u otro módulo deja a K siendo la vía y antes pasaba en verde.
        if (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "object" and len(c.args) == 3
                and isinstance(c.args[0], ast.Name) and c.args[0].id == "pm"
                and isinstance(c.args[1], ast.Constant) and c.args[1].value == "ENABLE_MODIS_CODIGO_MIROVA"
                and isinstance(c.args[2], ast.Constant)):
            dentro = {id(n) for s in w.body for n in ast.walk(s) if _es_brazo(n)}
            fijadas |= dentro
            valores += [c.args[2].value] * len(dentro)
imp_pm = any(isinstance(n, ast.ImportFrom) and n.module == "pipeline" and any(a.name == "process_modis" and a.asname == "pm"
             for a in n.names) for n in arbol.body)
ok(imp_pm, "arnés: `pm` es pipeline.process_modis")
ok(len(todas) == 2 and fijadas == todas and sorted(valores) == [False, True],
   f"arnés: K y V fijan el flag en memoria (llamadas {len(todas)}, fijadas {len(fijadas)}, valores {valores})")

# ---------------------------------------------------------------------------- 4. lista de pasadas
pas = json.load(open(AQUI / "pasadas_chillan_modis.json", encoding="utf-8"))["pasadas"]
claves = ("dt", "sensor", "z", "vrp_mirova_mw", "granule")
ok(all(all(p.get(k) is not None for k in claves) for p in pas), f"lista: {len(pas)} pasadas con {claves}")
ok(len({(p["dt"], p["sensor"]) for p in pas}) == len(pas), "lista: sin pasadas repetidas")
ok(all(p["granule"].split(".")[0] in ("MOD021KM", "MYD021KM") for p in pas), "lista: gránulos MOD021KM / MYD021KM")

# ---------------------------------------------------------------------------- 5. grillas capturadas (si existen)
patron = os.environ.get("S173_GRILLAS", "D:/vrp-trabajo/temporales/s170_ab*/*/grillas/grilla_NevadosDeChillan_*.npz")
arch = {Path(f).stem.split("_")[-1]: f for f in glob.glob(patron)}
hechas = 0
for p in pas:
    f = arch.get(p["dt"].replace("-", "").replace(" ", "").replace(":", ""))
    if not f:
        continue
    z = np.load(f)
    m = MV.detectar_mirova(z["mir"], z["tir"], z["box"], int(z["dayflag"]), float(z["sunglint"]), lam_mir=PZ.LAM,
                           lam_tir=PZ.FAM["lam_tir"])
    vv = MV.vrp_mirova(z["mir"], m, coef=PZ.COEF)
    ok(np.array_equal(m, z["mascara"]) and abs((vv["VRP_MW"] if vv["npix"] else 0) - float(z["vrp_mw"])) < 1e-3,
       f"grilla capturada {p['dt']}: V0 = captura")
    hechas += 1
print(f"grillas capturadas comprobadas: {hechas} (0 en el runner: no están en el repositorio)")

print(f"\n{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)
