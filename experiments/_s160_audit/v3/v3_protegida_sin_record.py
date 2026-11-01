"""V3 (hallazgo propio, ligado a 241): una alerta protegida de MIROVA sin ningún record nuestro (estado
sin_record, lo que deja una plataforma callada) ¿genera flag en el auto-audit semanal de SHA_MAIN?
Control positivo: la misma alerta con estado sin_publicar debe dar flag.
Uso: python -I v3_protegida_sin_record.py <arbol_main>"""
import sys, os
sys.path.insert(0, sys.argv[1] + "/scripts"); sys.path.insert(0, sys.argv[1])
import auto_audit_weekly as aw
base = {"volcano": "Lascar", "sensor": "MODIS", "fecha_utc": "2026-11-05T05:00", "vrp_mirova_mw": 2.5,
        "detector": "K", "noche_publicada_otra_pasada": False, "referencia_sospechosa": False}
for est in ("sin_record", "sin_publicar", "publicada"):
    print(est, "->", aw.flags_protegidas([{**base, "estado": est}], "K"))
