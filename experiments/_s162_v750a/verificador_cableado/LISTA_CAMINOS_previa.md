# Lista previa de caminos por los que la afirmacion podria estar mal

Escrita ANTES de abrir el diff. Hora del servidor (gh api -i): Mon, 26 Oct 2026 12:14:02 GMT.
Commit del worktree: 3a02ad28ff979d5f7c913347819b201a2fad589a.

Afirmacion: con ENABLE_V750_CODIGO_MIROVA apagado el cableado no cambia ningun record ni decision del NRT.

## Caminos
- C01. Algun efecto fuera del bloque `if ENABLE_V750_CODIGO_MIROVA:` en process_viirs_mod.py (variables reasignadas, orden de evaluacion, mutacion de arrays, cambio de nombre/valor de algo usado despues).
- C02. Import nuevo (top-level) en process_viirs_mod.py, store.py, run_pipeline.py o profile.py que falle, tenga efectos al importar, o importe yaml/volcanoes.yaml/matlab al cargar.
- C03. Flag leido de otra seccion o con otro nombre: perfil con la clave en la raiz vs thresholds (A89, S124), o algun perfil que lo tenga en true; valor por defecto si falta la clave; perfil experimental.
- C04. Algun procesador o script (process_modis, process_viirs, scripts, experiments) que ya produzca `via_codigo_mirova`, o un record historico en data/ que lo traiga en true.
- C05. store.py usa `_via_mirova` o una variable equivalente en otro lugar no cubierto; el salto de compuertas cambia el flujo (continue/return) o la semantica de otras ramas.
- C06. La prueba bit a bit (bitabit_store.py) mide otra cosa: records que ya vienen de disco, sin los campos que cambian en NRT; comparacion con tolerancia; comparar solo JSON y no el efecto en el estado (orden, upgrade NRT->standard).
- C07. volcan_por_coordenadas reconoce mal un volcan (tolerancia, volcanes cercanos como Planchon-Peteroa/Descabezado), o lee volcanoes.yaml de otra ruta (cwd), o orden de volcanes.
- C08. Diferencias de tipo en comparacion de coordenadas (float vs str, numpy float32 vs float, None/NaN).
- C09. Cosas del NRT despues del almacen (merge de jobs, dashboards, auditores) que lean campos nuevos o que el record gane una clave nueva incluso con flag apagado (p.ej. `via_codigo_mirova: False` en el JSON cambia el record).
- C10. Firma de calculate_vrp o de funciones llamadas por otros (tests, scripts) cambia (argumento nuevo con default; retorno con mas elementos).
- C11. Con flag encendido: la via salta MAS de las tres compuertas, o menos; un record con via True sortea otra validacion (p.ej. geofencing, tope D9, piso de magnitud).
- C12. Volcan sin grilla de MIROVA: no corre K o no queda marcado; fallback silencioso a la via MIROVA.
- C13. Las pruebas existentes (test_mirova_v750_*) pasan por la razon equivocada (A92 subcadena, mocks, lectura de texto fuente).
- C14. Guards existentes de la suite (tests/test_guard_*) que leen process_viirs_mod.py como texto o lineas citadas (A101) y quedan rotos o falso verde.
- C15. Archivo(s) A45 modificados que el material no lista (pipeline/profiles/*.yaml, workflows, otros procesadores).
- C16. Efectos de import circular (mirova_v750_codigo importando process_viirs_mod).
- C17. Encoding/CRLF o archivos con cambios no intencionales (whitespace) en el diff.
