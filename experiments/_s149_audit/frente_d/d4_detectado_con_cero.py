# -*- coding: utf-8 -*-
"""S149, frente D. En el brazo SIN Test 1: cuantas pasadas tienen cumulo primario summit DETECTADO
pero con magnitud 0 (el exceso sobre el fondo regional se recorta a cero, D25), por etiqueta.
Sirve para saber si la "caida de publicacion" del brazo es de DETECCION o del NUMERO, en positivas y
en negativos por igual (un arreglo del fondo podria devolver las dos).
Instrumento: 1) si estuviera roto veria 0 en todo: control positivo = las 4 positivas de d3 deben
aparecer aca como 'summit con cumulo y vrp 0'. 2) se imprimen todos los n.
Uso: python d4_detectado_con_cero.py DIR_SALIDAS"""
import sys, io, json, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev
bp = ev.bp
D = Path(sys.argv[1]); VENT = ("2026-09-01", "2026-09-20")
CONG = RAIZ / "experiments" / "_s146_ab_sin_test1" / "_congelado"
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = ev.cargar_referencia_unificada(CONG / "registro_vrp_consolidado.csv", CONG / "registro_vrp_ocr.csv")
por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, VENT)
for brazo in ("_s146_ab_control", "_s146_ab_sin_test1"):
    recs = ev.cargar_brazo(D / brazo, coords, inner, VENT); bp.etiquetar(recs, por_vb, ns, nv)
    print("\n==", brazo)
    for S in ("VIIRS375", "VIIRS750"):
        for lab in ("pos", "neg_limpio", "rutina_noche_alerta"):
            if lab == "rutina_noche_alerta":
                sel = [r for r in recs if r["b"] == S and r["lab"] == "sin_info" and r.get("rutina_pasada") and r.get("noche_con_alerta_sensor")]
            else:
                sel = [r for r in recs if r["b"] == S and r["lab"] == lab]
            pub = sum(bool(r["pub"]) for r in sel)
            cero = [r for r in sel if not r["pub"] and r["dc"] == "summit" and r["pc_dist"] is not None and (r["pc_vrp"] or 0) == 0
                    and r["pc_dist"] <= inner[r["vol"]]]
            far = [r for r in sel if not r["pub"] and r["dc"] != "summit" and r["pc_dist"] is not None]
            nada = [r for r in sel if not r["pub"] and r["pc_dist"] is None]
            print("  %-9s %-20s n %4d | publica %4d | NO publica: cumulo summit con VRP 0: %4d | cumulo fuera o far: %4d | sin cumulo: %4d | otro: %d" % (
                S, lab, len(sel), pub, len(cero), len(far), len(nada), len(sel) - pub - len(cero) - len(far) - len(nada)))
