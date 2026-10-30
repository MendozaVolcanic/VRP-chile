# -*- coding: utf-8 -*-
"""Demostraciones con evaluar_f4.py del arbol (F4_RAIZ apunta a raiz_min, que trae evaluar_d25.py con blob 1dbabf65,
scripts/, pipeline/ y frontend/ copiados del arbol). Predicado sintetico: no se usa node ni red.
Cada demo trae control positivo (el mismo control SI se pone en rojo cuando corresponde): pregunta 1 del instrumento.
Pregunta 2: cada demo imprime el estado devuelto, no un cero por defecto."""
import os, sys, importlib.util, json, tempfile, hashlib
from pathlib import Path

BASE = Path("D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis")
os.environ["F4_RAIZ"] = str(BASE / "raiz_min")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
spec = importlib.util.spec_from_file_location("evaluar_f4_leido", BASE / "arbol/experiments/_s166_modd_f4/evaluar_f4.py")
E = importlib.util.module_from_spec(spec); sys.modules["evaluar_f4_leido"] = E; spec.loader.exec_module(E)
print("evaluar_d25 blob cargado:", E.blob(E.D25_RUTA), "| esperado:", E.D25_BLOB)

REC = {"vrp_mw": 0.0, "primary_cluster": None, "distance_class": None, "t_max_k": None, "sensor": "MODIS_AQUA",
       "triggered_test1": False, "anomaly_pixels": [], "final_hotspot_dist_km": None}
def fila(vol, dt, **k):
    f = {"tipo": "record", "vol": vol, "dt": dt, "noche": dt[:10], "estado": "ok", "motivo": None, "v_marca": True,
         "inner": 5.0, "k_slim": REC, "v_slim": REC, "vcerc_slim": REC, "vpico_slim": REC, "z": 10.0,
         "pub_runner": {"K": 0, "V": 0, "V-cercano": 0, "V-pico": 0}, "k_difiere_de_guardado": False,
         "k_reproducida_en_su_sha": None, "dist": None, "store_descarto": {}}
    f.update(k); return f
pred = lambda casos: [(0, 0.0)] * len(casos)

print("\n== D1 (P-D): control_k_produccion compara pub_runner SOLO para K; V, V-cercano y V-pico nunca")
filas = [fila("Lascar", "2026-03-27 07:10", lab="protegida", pub_runner={"K": 0, "V": 1, "V-cercano": 1, "V-pico": 1})]
for f in filas: f["_evaluable"], f["_motivo"] = E.evaluable(f)
E.armar_tabla(filas, pred)
print("   evaluador publica V =", E._pub(filas[0], "V"), "| el runner dijo V =", filas[0]["pub_runner"]["V"])
print("   control_k_produccion:", E.control_k_produccion(filas)["estado"], "(deberia verse la discrepancia de V; solo mira K)")
filas[0]["pub_runner"]["K"] = 1
print("   control positivo (pub_runner K=1 vs evaluador 0):", E.control_k_produccion(filas)["estado"])

print("\n== D2 (P-D/P-B): control_identidad ignora captura_coherente, box_igual, pos_crater_igual y v_slim_dc_igual")
fl = [fila("Lascar", "2026-03-%02d 07:10" % (i + 1), lab="neg_limpio", grilla_censo="g%d.npz" % i) for i in range(3)]
for f in fl: f["_evaluable"], f["_motivo"] = E.evaluable(f)
base = {"mismo_granulo": True, "misma_mascara": True, "dvrp": 0.0, "misma_clase": True}
malo = dict(base, captura_coherente=False, box_igual=False, pos_crater_igual=False, v_slim_dc_igual=False,
            v_slim_vrp_igual=False, geom_distinta=True, grilla_igual_float32=False, max_dif_radiancia=99.0)
ident = {(f["vol"], f["dt"]): dict(malo, vol=f["vol"], dt=f["dt"]) for f in fl}
print("   con los 8 indicadores informativos en rojo:", E.control_identidad(ident, fl, 3)["estado"])
ident2 = {k: dict(v, misma_clase=False) for k, v in ident.items()}
print("   control positivo (misma_clase False):", E.control_identidad(ident2, fl, 3)["estado"])
print("   el ident no trae procedencia: claves de una entrada =", sorted(next(iter(ident.values()))))

print("\n== D3 (P-F): una fila del runner que no esta en la poblacion (sin 'lab') hace CAER evaluar() en vez de dar INDECIDIBLE")
f = fila("Lascar", "2026-03-27 07:10")   # sin lab ni tramo: lo que main() deja si la poblacion no la trae
try:
    r = E.evaluar([f], [], {}, {}, [], pred, 0)
    print("   veredicto:", r["veredicto"])
except Exception as e:
    print("   CAE con", type(e).__name__, e)
f = fila("Lascar", "2026-03-27 07:10", lab="neg_limpio", tramo="C", grilla_censo=False)
r = E.evaluar([f], [("Lascar", "2026-03-27 07:10")], {}, {}, [], pred, 0)
print("   control positivo (con lab, esperada): veredicto", r["veredicto"], "| cobertura", r["controles"]["cobertura"]["estado"])

print("\n== D4 (P-G): por_tramo informa solo P2; el pre-registro (§6, tras la tabla) pide P2 y P2' por tramo")
print("   claves de res['por_tramo']['C']:", sorted(r["por_tramo"].get("C", {})) if r.get("por_tramo") else r.get("por_tramo"))

print("\n== D5 (P-E): el resultado no registra la version de numpy ni la raiz usada")
print("   claves de primer nivel del resultado:", sorted(r))
print("   'numpy' en el json del resultado:", "numpy" in json.dumps(r, default=str).lower(), "| F4_RAIZ en uso:", E.RAIZ)

print("\n== D6 (P-A): Path.write_text en Windows traduce \n a \r\n; json.dumps compacto (el del ensayo en seco) no tiene \n")
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "x.json"
    p.write_text(json.dumps({"a": [1, 2]}, indent=0), encoding="utf-8")
    ind = p.read_bytes()
    p.write_text(json.dumps({"a": [1, 2]}), encoding="utf-8")
    comp = p.read_bytes()
print("   indent=0 -> CRLF presentes:", ind.count(b"\r\n"), "| compacto -> CRLF presentes:", comp.count(b"\r\n"))
print("   sha256 compacto igual en CRLF y LF:", hashlib.sha256(comp).hexdigest() == hashlib.sha256(comp.replace(b"\r\n", b"\n")).hexdigest(),
      "| sha256 con indent distinto:", hashlib.sha256(ind).hexdigest() != hashlib.sha256(ind.replace(b"\r\n", b"\n")).hexdigest())
