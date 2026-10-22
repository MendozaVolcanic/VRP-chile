#!/usr/bin/env python
"""Verificador V2 de 203 (cumulos summit con 0,0 MW) y efecto de 201 sobre lo publicado.

Camino distinto al auditor: en vez de contar cumulos en el JSON, corro el predicado del tablero con node
(banco_paridad.correr_node via cargar_nuestros) sobre TODOS los sensores, dos ventanas, y cruzo con la
referencia en sus dos versiones (tabla sola y combinado) para ver si MIROVA alerto en esas pasadas.
Pregunta 1: si el recorte no existiera, la cuenta de pc_vrp==0 seria 0; lo veria. Pregunta 2: control
de identidad del predicado (banco_paridad.control_identidad_predicado) debe dar [0,1,1,1,0] y [1,0];
y el total publicado debe ser > 0.
"""
import json, math, os, sys, tempfile
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
SNAP = Path(r"D:\vrp-trabajo\temporales\s160_audit\main")
sys.path.insert(0, str(SNAP / "scripts")); sys.path.insert(0, str(SNAP))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada
import yaml
OUT = Path(__file__).with_name("v_203_cero_salida.txt"); L = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s); L.append(s)
ident = bp.control_identidad_predicado(); p("CONTROL identidad predicado:", ident)
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
vy = {v["name"]: v for v in yaml.safe_load(open(SNAP / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
def hav(a, b, c, d):
    R = 6371.0; p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2-p1)/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2
    return 2*R*math.asin(math.sqrt(x))
# anomaly pixels y n_pixels por (vol, sensor, datetime)
extra = {}
for v in bp.VOLS:
    for r in json.load(open(SNAP/"data"/"mirova_equivalent"/f"{v}.json", encoding="utf-8"))["records"]:
        pc = r.get("primary_cluster") or {}
        extra[(v, r.get("sensor"), r.get("datetime_utc"))] = (pc.get("n_pixels"), r.get("anomaly_pixels") or [], r.get("t_bg_k"), pc.get("single_pixel_mode"))
tmp = Path(tempfile.mkdtemp()); vacio = tmp/"ocr_vacio.csv"
vacio.write_text(open(SNAP/"data"/"mirova_reference"/"mirova_v1_snapshot"/"registro_vrp_ocr.csv", encoding="utf-8").readline(), encoding="utf-8")
REFS = {"tabla_sola": (SNAP/"latest_consolidado.csv", vacio),
        "combinado": (SNAP/"latest_consolidado.csv", SNAP/"data"/"mirova_reference"/"mirova_v1_snapshot"/"registro_vrp_ocr.csv")}
for ventana in [("2026-03-01", "2026-10-21"), ("2026-09-18", "2026-10-21")]:
    recs0 = bp.cargar_nuestros(coords, inner, ventana)
    p(f"\n=== ventana {ventana} records nocturnos {len(recs0)} publicados {sum(r['pub'] for r in recs0)}")
    for refn, (cons, ocr) in REFS.items():
        recs = [dict(r) for r in recs0]
        filas = cargar_referencia_unificada(cons, ocr)
        por_vb, ns, nv, n = bp.indexar_referencia(filas, coords, ventana)
        bp.etiquetar(recs, por_vb, ns, nv)
        c = Counter()
        for r in recs:
            key = (r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"))
            npx, aps, tbg, spm = extra.get(key, (None, [], None, None))
            filas_p = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
            al = [f for f in filas_p if bp.es_alerta(f["tipo"])]
            prot = any((f["vrp_mw"] or 0) >= 1.0 for f in al)
            b = r["b"]
            if r["pc_vrp"] is not None:
                c[(b, "con_cumulo")] += 1
                if r["dc"] == "summit":
                    c[(b, "summit_con_cumulo")] += 1
                    if r["pc_vrp"] == 0:
                        c[(b, "summit_pc0")] += 1
                        c[(b, "summit_pc0_lab_"+r["lab"])] += 1
                        if prot: c[(b, "summit_pc0_PROTEGIDA")] += 1
                        # causa: todos los pixeles bajo t_bg?
                        if tbg is not None and aps and all((a.get("bt_k") or 0) <= tbg for a in aps):
                            c[(b, "summit_pc0_todos_bt<=tbg")] += 1
                        # la noche: otra pasada del mismo sensor publica?
            if r["pub"]:
                c[(b, "publica")] += 1
                vv = vy[r["vol"]]; vl, vo = vv.get("vent_lat", vv["lat"]), vv.get("vent_lon", vv["lon"])
                if any(hav(vl, vo, a["lat"], a["lon"]) > inner[r["vol"]] for a in aps if a.get("lat") is not None):
                    c[(b, "publica_con_pixel_fuera_inner")] += 1
            if r["lab"] == "pos": c[(b, "pos")] += 1
            if r["lab"] == "pos" and r["pub"]: c[(b, "pos_pub")] += 1
        p(f"--- ref {refn} (filas nocturnas en ventana {n})")
        for b in ["MODIS", "VIIRS375", "VIIRS750"]:
            p("  ", b, {k[1]: v for k, v in sorted(c.items()) if k[0] == b})
OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
