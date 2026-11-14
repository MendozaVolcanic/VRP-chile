#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V1 (S175), afirmaciones 156 y 157: corre scripts/auto_audit_weekly.py::main de root_base dos veces, con la salida
redirigida a la carpeta temporal de V1 (no escribe en root_base):
  A) tal cual (la vía tiene records: VIA_MODIS decide MODIS);
  B) contrafactual: frontera_via_modis devuelve None (como si la vía no existiera; MODIS lo decide K).
Pregunta 1: si el audit dejara de dar flag por protegidas MODIS de K al existir la vía, A tendría menos flags que B
en MODIS y el veredicto cambiaría. Pregunta 2 (control): B tiene que reproducir el comportamiento previo, con flags
de las protegidas MODIS de K; si B también diera 0 flags, el contrafactual no mide nada.
Uso: python audit_con_y_sin_via.py <root_base> <carpeta_salida>
"""
import json, os, sys, io, contextlib
root, out = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "scripts")); sys.path.insert(0, root)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import auto_audit_weekly as aa
res = {}
for nombre in ("A_tal_cual", "B_sin_via"):
    d = os.path.join(out, nombre); os.makedirs(d, exist_ok=True)
    aa.OUTDIR = d
    if nombre == "B_sin_via":
        aa.frontera_via_modis = lambda recs: None
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        aa.main()
    with open(os.path.join(d, "stdout.txt"), "w", encoding="utf-8") as fh:
        fh.write(buf.getvalue())
    j = json.load(open(os.path.join(d, "latest.json"), encoding="utf-8"))
    res[nombre] = {"veredicto": j.get("veredicto"), "flags": j.get("flags"),
                   "recall_sin_juzgar": {k: v.get("aviso") for k, v in (j.get("recall_sin_juzgar") or {}).items()}
                   if isinstance(j.get("recall_sin_juzgar"), dict) else j.get("recall_sin_juzgar"),
                   "claves": sorted(j.keys())}
print(json.dumps(res, indent=1, ensure_ascii=False))
