"""Hallazgo: la sombra muerta en UN volcan no se detecta. Chillan sin records de sombra desde el 2026-10-05,
el resto al dia; protegida de Chillan el 2026-10-22 que K no publica. Uso: python ciego_por_volcan.py <copia>"""
import sys
from datetime import datetime, timezone
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[1] + "/scripts")
import scripts.vigilancia_sombra as vs


def rec(vol, b, fecha, hhmm, pub, perfil):
    dt = datetime.strptime(f"{fecha} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return {"vol": vol, "b": b, "dt": dt, "noche": fecha, "pub": pub, "sensor": "MODIS_Aqua", "perfil": perfil,
            "lab": "pos"}


filas = [{"volcano": "NevadosDeChillan", "sensor_bucket": "MODIS", "fecha_utc": "2026-10-22 07:20:00",
          "vrp_mw": 5.0, "tipo": "ALERTA_TERMICA", "source": "CONS"}]
prod = [rec("NevadosDeChillan", "MODIS", "2026-10-22", "07:20", False, "mirova_equivalent")]
sombra = [rec("NevadosDeChillan", "MODIS", "2026-10-05", "07:20", True, "experimental"),
          rec("Villarrica", "MODIS", "2026-10-22", "07:20", False, "experimental")]
vs.cargar_insumos = lambda win: (filas, prod, sombra)
vs.aa.leer_frontera_k = lambda *a: "2026-09-18"
vs.leer_adopcion = lambda *a: "2026-10-18 09:57"
vs._diurna_por_defecto = lambda: (lambda *a: False)
out = vs.evaluar("2026-10-23")
print("veredicto:", out["veredicto"], "| avisos:", out["avisos"])
print("protegidas_sin_publicar_k:", [(p["volcano"], p["fecha_utc"], p["sombra_pub"]) for p in out["protegidas_sin_publicar_k"]])
