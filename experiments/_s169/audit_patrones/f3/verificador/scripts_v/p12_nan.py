"""P3-12: ¿VRP nan cuenta como protegida?
P1: si la guarda estuviera rota (nan pasa), alerta_protegida(nan) da True; control positivo 5.0 -> True, control negativo 0.5 -> False.
P2: además mido cuántas filas de la referencia congelada (cc3887290) dan nan/inf al parsear VRP_MW, para saber si el defecto tiene sustrato.
"""
import sys, os, csv, math, json
arbol, refdir = sys.argv[1], sys.argv[2]
sys.path.insert(0, arbol); sys.path.insert(0, arbol + "/scripts")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import clase_mirova as cm
import referencia_mirova_unificada as rmu
tipo = sorted(cm.TIPOS_ALERTA)[0]
res = {"tipo_usado": tipo}
for v in (5.0, 0.5, float("nan"), float("inf"), None):
    res["alerta_protegida(%r)" % v] = cm.alerta_protegida({"vrp_mw": v, "tipo": tipo})
# es_protegida sobre PasadaMirova construida con resumir_pasadas
filas = [{"volcano": "Lascar", "sensor_bucket": "VIIRS375", "fecha_utc": "2026-11-05 06:00:00", "source": "CONS",
          "origen": "principal", "tipo": tipo, "vrp_mw": float("nan"), "dist_km": 1.0, "clasificacion": "",
          "ultima_actualizacion": "", "sin_geometria": False}]
try:
    ps = cm.resumir_pasadas(filas, canal="union", regla_minimas=cm.MODO_MINIMAS)
    res["resumir_pasadas_nan"] = [(p.estado, repr(p.vrp_mw), cm.es_protegida(p)) for p in ps]
except Exception as e:
    res["resumir_pasadas_nan_error"] = repr(e)
# sustrato: VRP_MW no finito en la referencia
sus = {}
for n in sorted(os.listdir(refdir)):
    if not n.endswith(".csv"): continue
    c = {"filas": 0, "no_finito": 0, "vacio": 0, "ejemplos": []}
    with open(os.path.join(refdir, n), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            c["filas"] += 1
            v = rmu._float(r.get("VRP_MW"))
            if v is None: c["vacio"] += 1
            elif not math.isfinite(v):
                c["no_finito"] += 1
                if len(c["ejemplos"]) < 3: c["ejemplos"].append((r.get("Volcan"), r.get("Fecha_Satelite_UTC"), r.get("VRP_MW"), r.get("Tipo_Registro")))
    sus[n] = c
res["sustrato_referencia_cc3887290"] = sus
print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
