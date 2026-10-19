# Plan de la sesión S155 (acordado con Nicolás el 2026-10-19)

Nicolás aprobó todo lo propuesto al final de S154: «de acuerdo con todo lo que dices». Este plan lo ordena. El estado
vivo sigue en `tasks/LOOP_OBJETIVOS.md` (rama `loop/activo`) y en el bloque de arranque que deje `/cierre`.

## Por qué este plan

En S154 hubo tres errores, y los tres salieron de cosas que estaban en el repo y no se miraron: atribuir el déficit de
magnitud de Chillán a D25 sin estratificar por cenit, después a D17 citando una lectura de S130 que la tarea 1.14 ya
había retirado, y mostrar una tabla sin script. Las causas: el conocimiento se guarda por número y por sesión, no por
síntoma; las correcciones no se propagan a la fuente que se cita primero (A113); los promedios esconden curvas (A90,
A114); y la sesión se alargó demasiado. En cambio, los verificadores con contexto limpio encontraron algo real las
cuatro veces que se usaron. El plan refuerza lo que funcionó y ataca esas causas.

## Acuerdos de proceso (vinculantes desde S155)

1. **Duración de las sesiones:** cerrar con `/cierre` al llegar a unos 30 intercambios o después de dos hitos grandes,
   lo que ocurra primero. El loop sigue en la sesión nueva con el traspaso.
2. **Ningún número llega a Nicolás sin script commiteado** que lo produzca (A91 extendida a la conversación).
3. **Antes de atribuir un mecanismo:** leer el síntoma en `docs/SINTOMAS.md`, buscar TODAS las fuentes posteriores que
   lo tocan (no sólo la que lo midió primero) y estratificar por cenit, sensor, volcán y régimen (antes y después de
   #535 y de K).
4. **Verificador limpio antes de aceptar cualquier resultado** (ya regla del loop; se mantiene).
5. **Escala de la auditoría post-K aprobada:** 5 frentes más 5 verificadores.

## Orden de trabajo

### Bloque 0: arranque (protocolo `/retomar`)
- Estado real: `git fetch`, remoto, disco, NRT, issues de alerta (#779, #824, #813).
- Leer el informe de la segunda vuelta del verificador del candado
  (`experiments/_s151_ab_diurno/verificador_candado_k_v2/INFORME.md`, worktree `s153-adopcion`, rama
  `loop/diurno-k-candado`) si quedó escrito; si no, relanzarlo.
- Estado del reproceso histórico con K (run 39125546355).

### Bloque 1: auditoría post-K (5 frentes en paralelo, cada uno con su verificador limpio)
Preámbulo canónico de `../../GUIA_MAESTRA_AUDITORIAS.md` §5 pegado entero; cobertura primero; un worktree por agente
(A44); cada hallazgo con archivo:línea y salida cruda; el que verifica no es el que encontró.
1. **Propagación de K** en `docs/MIROVA_DIVERGENCES.md` (D21 sigue «ABIERTA», #850 no aparece), `docs/MISSION.md`,
   `CLAUDE.md`, la ficha SDA y todo documento que trate a C0 como producción (A113; tarea 1.37).
2. **Lo que ve el operador con K**: marcadores, niveles, magnitudes, aviso del cambio y las tres vistas (index, diario,
   mosaico). Ya apareció un defecto (D-24, marcador, arreglado en #853); buscar los demás, con el código real en el
   navegador.
3. **Instrumentos**: auto-audit semanal y evaluadores de A/B. ¿Estratifican por cenit y régimen? ¿Alguno mezcla C0 y
   K sin decirlo? (insumo de 1.35).
4. **Cierres y afirmaciones que K pudo volver falsos**, al estilo del censo S145 (`experiments/_s145_censo_cierres/`).
5. **Magnitud en erupción con Chillán**, pasada por pasada, leyendo el L1B cuando haga falta: separar selección,
   fondo, recorte y saturación (tarea 1.33; tabla de partida `experiments/_s154_chillan/razon_por_cenit.py`). Insumo del
   pre-registro de D25.
Salida: `docs/AUDIT_S155.md` con los hallazgos verificados y la lista de arreglos, cada uno con su dueño en el loop.

### Bloque 2: memoria del proyecto
- **Índice por síntoma** (1.34): revisar el borrador `experiments/_s154_sintomas/SINTOMAS_borrador.md` (9 síntomas;
  trae tres contradicciones entre fuentes y el «SIN ATRIBUIR» del ángulo), pasarlo a `docs/SINTOMAS.md` con
  verificador, y agregar el paso al protocolo §2 del loop.
- **CLAUDE.md del proyecto** (si `/cierre` de S154 no alcanzó): dejar unas 20 reglas vinculantes con su porqué y mover
  el resto a un documento buscable con índice de una línea.
- **Estratificación automática** (1.35) en auto-audit y evaluadores.

### Bloque 3: pruebas en curso (en paralelo con lo anterior, respetando 20 runners y el disco)
- **Reemplazo del histórico con K** (1.24) cuando terminen los 176 trozos: ensayo por volcán, verificador, aplicar en
  un commit entre NRT, `verificar_ventana.py` y R8.
- **A/B diurno sobre K** (1.32): con el candado verificado y el histórico terminado, tag de despacho, `--sha-codigo` con
  `git rev-parse <tag>^{commit}`, diez medias ventanas, una por despacho.
- **Pre-registro de D25 sobre K con Chillán como caso** (1.29, primero; D17 como hipótesis competidora después, 1.36),
  para el sello de Nicolás.
- NOAA-21 del 2026-10-18 (1.27): ya reescritas con K por el NRT; comprobarlo y cerrar la tarea.

## Lo que se necesita de Nicolás
1. **Cronología OVDAS de Chillán**: fases de la erupción y dónde está hoy el foco activo (cráter, flujo, domo), para
   interpretar las distancias de MIROVA de hasta 2,7 km y como referencia del perfil experimental (1.11).
2. **cron-job.org en UTC** (pasos en la respuesta de S154; comprobar con la hora del primer despacho).
3. Rotar el PAT de GitHub; avisar a OVDAS del cambio de detector.
4. Sellos cuando lleguen: pre-registro de D25 sobre K.
