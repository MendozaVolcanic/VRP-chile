# -*- coding: utf-8 -*-
"""S173 F2 hallazgo 205: estratificar_magnitud del audit semanal (PR A) cae con ValueError cuando una pasada MODIS de la
vía publica en una noche con alerta de MIROVA. Mínimo, con las funciones reales de scripts/auto_audit_weekly.py del
árbol que se pasa como argumento (sin datos del repo).
Pregunta 1 (si estuviera roto, ¿se vería?): el caso «vía publica en noche con alerta» debe lanzar; el control «misma
  noche sin vía» y «vía que no publica» (el único que cubre la prueba del PR A) no deben lanzar.
Pregunta 2 (instrumento muerto): si la función no se llamara, no habría ni excepción ni resultado: se imprime cada caso."""
import importlib.util, sys
sys.stdout.reconfigure(encoding="utf-8")
raiz = sys.argv[1]
sys.path.insert(0, raiz + "/scripts"); sys.path.insert(0, raiz)
spec = importlib.util.spec_from_file_location("aa", raiz + "/scripts/auto_audit_weekly.py")
aa = importlib.util.module_from_spec(spec); spec.loader.exec_module(aa)
print("REGIMENES =", aa.REGIMENES)
key = ("NevadosDeChillan", "MODIS", "2026-10-30")
mir = {key: 2.0}
def ours_con(pub):
    return {key: {"crater": [pub] if pub else [], "dash": [pub] if pub else [], "pub": [pub] if pub else [],
                  "npix": [1] if pub else [], "z_pub": [20.0] if pub else [], "dt_pub": ["2026-10-30 07:20"] if pub else []}}
casos = [("vía publica 1,5 MW en noche con alerta (frontera de la vía 2026-10-25)", ours_con(1.5), "2026-10-25"),
         ("CONTROL misma noche, sin vía (K)", ours_con(1.5), None),
         ("CONTROL vía que no publica (lo que cubre test_auto_audit_via_modis_s172)", ours_con(0.0), "2026-10-25")]
for nom, ours, via in casos:
    try:
        r = aa.estratificar_magnitud(mir, ours, "2026-09-18", "K", None, via_modis=via)
        print(f"{nom}: OK, por_regimen = {r['por_regimen']}")
    except Exception as e:
        print(f"{nom}: EXCEPCION {type(e).__name__}: {e}")
