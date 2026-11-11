# -*- coding: utf-8 -*-
"""Escribe hallazgos.csv con el modulo csv (una fila por hallazgo del INFORME.md)."""
import csv, os
H = os.path.dirname(os.path.abspath(__file__))
def r(nombre): return os.path.join(H, nombre)
py = lambda n: 'python "' + r(n) + '"'
filas = [
 (401, "El plazo de la reversion pre-autorizada de MODIS se agota hacia el 20 de noviembre y solo con alertas de Chillan",
  "scripts/vigilancia_guardia_modis.py:226-237 y 520-521; experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md:308-314 (438a60a1e)",
  "CONFIRMADO el conteo (11 de 29, todas de Chillan); SOSPECHA la fecha (proyeccion lineal)", 3, "vigilancia con un umbral que se agota",
  py("02_vigilancia_en_la_base.py") + " ; " + py("03_proyeccion_plazo.py"), r("03_proyeccion_plazo.txt")),
 (402, "La vigilancia de la guardia da VERDE cuando la via pierde una protegida que K tampoco publica o que la guardia no miro (3 de 11 desde el encendido)",
  "scripts/vigilancia_guardia_modis.py:239-249, 317-319 y 538 (438a60a1e)", "CONFIRMADO", 3, "vigilancia ciega",
  py("04_mutaciones_vigilancia.py") + " ; " + py("09_audit_semanal_con_mutaciones.py"), r("04_mutaciones_vigilancia.txt")),
 (403, "La reversion por git revert del PR B ya choca: 6 archivos sobre main y 11 despues de encender VIIRS; el flag se revierte limpio",
  "merge 499935c37 contra 438a60a1e, origin/claude/s177-b1-v375 y origin/claude/s178-b2-sobre-b1", "CONFIRMADO", 3, "red de seguridad",
  'bash "' + r("10_revert_simulado.sh") + '"', r("10_revert_simulado.txt")),
 (404, "Las dos pasadas MODIS que la via descarto por borde estan en la tabla de MIROVA como RUTINA y el log no dice por que se descartaron",
  "pipeline/mirova_v750_codigo.py:802-808; scripts/run_pipeline.py:414-427 (438a60a1e)", "CONFIRMADO el hecho; SOSPECHA la causa", 2, "cobertura",
  py("07_descarte_de_borde.py") + " ; " + py("08_alertas_modis_por_cenit.py"), r("07_descarte_de_borde.txt")),
 (405, "El reemplazo de la historia (#981) dejaria la vigilancia de la guardia en VIGILANCIA_CIEGA todos los dias (nulo sin pares) y el plan no lo trata",
  "scripts/vigilancia_guardia_modis.py:296-313 y 374-379 (438a60a1e); docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md (62ccb8830)", "CONFIRMADO el mecanismo; el silencio del plan, por busqueda de texto", 2, "plan abierto",
  py("04_mutaciones_vigilancia.py") + " (caso M14)", r("04_mutaciones_vigilancia.txt")),
 (406, "El DECIDE NICOLAS de MODIS en la retrospectiva no esta en la lista de decisiones del bloque S179",
  "tasks/BLOQUE_ARRANQUE_S179.md:19 y 34-45 (0472cd95e); experiments/_s178_lectura/lectura.json (ff8a39972)", "CONFIRMADO", 2, "decision pendiente sin dueno",
  "git show origin/claude/s178-retro-lectura:experiments/_s178_lectura/lectura.json", r("16_poblacion_ab_por_volcan.txt")),
 (407, "La evidencia de que la via de MODIS no pierde alertas viene de Chillan y de Lascar; en 7 de 11 volcanes no hay ninguna alerta MODIS con que probarlo",
  "experiments/_s166_modd_f4/poblacion_f4.json y experiments/_s168/modd_f4_candado/lectura_ab2/resultado_f4.json (25e3cc3ba); lectura.json (ff8a39972)", "CONFIRMADO", 2, "alcance de la evidencia",
  py("13_ab_modd_discordantes.py"), r("16_poblacion_ab_por_volcan.txt")),
 (408, "La ficha publica dice que sin geolocalizacion la pasada MODIS se procesa con el metodo anterior; el NRT la salta sin record",
  "docs/FICHA_SDA_VRP_CHILE.md:25; scripts/run_pipeline.py:248-250; pipeline/process_modis.py:644-645 (438a60a1e)", "CONFIRMADO por lectura", 2, "documento publico contra codigo",
  "leer las lineas citadas en D:/vrp-trabajo/temporales/s179-audit/main/", r("INFORME.md")),
 (409, "59 de 105 perfiles corren hoy la via en MODIS sin decirlo, entre ellos 9 con K en el nombre y el del A/B diurno",
  "pipeline/profiles/*.yaml (438a60a1e); .github/workflows/reproc-s151-ab-diurno.yml", "CONFIRMADO", 2, "diferencia entre el nombre y lo que corre",
  py("11_censo_perfiles_via_modis.py"), r("11_censo_perfiles_via_modis.txt")),
 (410, "El unico control de que MODIS sigue vivo volcan por volcan esta dentro de la vigilancia de la guardia",
  "scripts/vigilancia_guardia_modis.py:354-355; scripts/auto_audit_weekly.py:346-361; scripts/vigilar_plataformas.py:8-11 (438a60a1e)", "CONFIRMADO para la guardia (mutacion); audit y vigilante de plataformas solo leidos", 2, "vigilancia",
  py("04_mutaciones_vigilancia.py") + " (casos M11 y M12)", r("04_mutaciones_vigilancia.txt")),
 (411, "La via publico 1 vez donde MIROVA dio 0 en 8 noches (Lascar 2026-11-08 08:00, 0,246 MW, margen 1 %)",
  "data/mirova_equivalent/Lascar.json, MODIS_AQUA 2026-11-08 08:00 (438a60a1e)", "CONFIRMADO el caso; SOSPECHA la tendencia", 1, "sobre-publicacion",
  py("02_vigilancia_en_la_base.py"), r("02_vigilancia_en_la_base.txt")),
 (412, "La regla sellada no registra los cambios que S175 le hizo a su instrumento (#959)",
  "experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md:8; scripts/vigilancia_guardia_modis.py:47-60 (438a60a1e)", "CONFIRMADO", 1, "documento",
  "git diff s173-regla-modd-sellada 438a60a1e -- experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md", r("INFORME.md")),
 (413, "MISSION.md y la ficha citan el tag pre-s171-adopcion-modd, 58 commits antes del main previo al merge (pre-s173-adopcion-modd)",
  "docs/MISSION.md:26; docs/FICHA_SDA_VRP_CHILE.md (438a60a1e)", "CONFIRMADO", 1, "documento",
  "git log --oneline pre-s171-adopcion-modd..499935c37^1 | wc -l", r("INFORME.md")),
 (414, "#937 esta en main sin que la bitacora registre el merge ni la frase",
  "tasks/LOOP_OBJETIVOS.md:1399-1406 (0472cd95e); commit f4ec1061d", "CONFIRMADO", 1, "registro de decisiones",
  "git log -1 --format='%h %ci %an %s' f4ec1061d", r("INFORME.md")),
 (415, "16 archivos de main citan docs/AUDIT_S175.md, que no existe en main (PR #955 en borrador)",
  "scripts/vigilancia_guardia_modis.py:47; scripts/run_pipeline.py:415; docs/MISSION.md:7 y otros (438a60a1e)", "CONFIRMADO", 1, "documento",
  "git ls-tree --name-only 438a60a1e docs/ | grep -c AUDIT_S175", r("INFORME.md")),
 (416, "Queda un record MODIS de K en producto NRT dentro del tramo de la via: Planchon-Peteroa 2026-11-02 01:15 UTC",
  "data/mirova_equivalent/PlanchonPeteroa.json, MODIS_TERRA 2026-11-02 01:15 (438a60a1e)", "CONFIRMADO el record; SIN DATO la causa", 1, "datos",
  py("05_cobertura_guardia_y_censo_via.py"), r("05_cobertura_guardia_y_censo_via.txt")),
]
with open(r("hallazgos.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    w.writerows(filas)
# control: releer y contar columnas
with open(r("hallazgos.csv"), encoding="utf-8", newline="") as f:
    filas2 = list(csv.reader(f))
print("filas (con cabecera):", len(filas2), "| columnas por fila:", sorted({len(x) for x in filas2}))
print("salidas crudas que existen:", sum(1 for x in filas2[1:] if os.path.exists(x[7])), "de", len(filas2) - 1)
