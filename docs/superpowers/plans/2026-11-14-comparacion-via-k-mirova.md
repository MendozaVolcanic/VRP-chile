# Comparación vía, K y MIROVA: plan de implementación (S183, fase 3)

> Para agentes: ejecutar tarea por tarea (superpowers:executing-plans). Pasos con casillas `- [ ]`.

**Objetivo:** una pestaña nueva en `frontend/comparacion.html` que muestre, por sensor, volcán y noche, cuánto se parecen a
MIROVA la vía «código MIROVA» y K, con datos que se refrescan solos una vez al día.

**Aprobado por Nicolás el 2026-11-14** («Sí, con refresco diario»: pestaña de `comparacion.html`, refresco diario y la
franja por noche incluida). Propuesta y medida: `experiments/_s183_comparacion/PROPUESTA.md`.

**Arquitectura:** `scripts/comparacion_via_k.py` evalúa con el predicado del tablero (node, `scripts/banco_paridad.py`)
la vía (producción), la guardia K y la historia de K, etiqueta contra MIROVA y escribe
`data/audit_continuous/comparacion_via_k.json`. La historia de K vive en el tag `pre-s180-reemplazo-historia` y no se
puede bajar entera cada día en Actions: se evalúa una vez en local y se guarda en
`data/audit_continuous/comparacion_k_historia_cache.json` con el sha de `index.html` con que se evaluó; si el predicado
cambia, el JSON lleva un aviso visible en la página. La página sólo lee y dibuja; no recalcula métricas.

**Límites:** nada en `pipeline/` ni en los datos de detección; no se tocan `index.html` ni los predicados del tablero; la
línea 1600 de `index.html` sigue siendo `function isValidDetection` (guard existente
`tests/test_guard_declarado_vs_efectivo_s131.py`).

## Archivos

- Crear `scripts/comparacion_via_k.py`: evaluación, etiquetado, métricas y salida (y `--construir-cache-k`).
- Crear `data/audit_continuous/comparacion_k_historia_cache.json` (generado en local, A88: entra en el mismo PR).
- Crear `data/audit_continuous/comparacion_via_k.json` (generado; lo reescribe el workflow).
- Crear `.github/workflows/comparacion-via-k.yml`: corre tras la vigilancia de la guardia de VIIRS (workflow_run), más
  cron de respaldo y dispatch; commitea con el bucle de reintento (`pull --rebase` + `push`), sin `group: push-main`.
- Modificar `frontend/comparacion.html`: pestaña 0 «Vía, K y MIROVA» (tarjetas, grilla, franja por noche, lista de
  desacuerdos, aviso del JSON).
- Crear `tests/test_comparacion_via_k_s183.py`.

## Tareas

### Tarea 1: núcleo de métricas con pruebas que fallan
- [ ] Pruebas sintéticas de `metricas_noches` (TP, FN, FP, TN, recall, precisión, protegidas), de `agregar_noches` (pos
  le gana a neg; far_ref anula neg; publica si alguna pasada publica) y de `comparar` (sólo claves comunes; alertas en
  pasadas sin par; protegidas en desacuerdo).
- [ ] Verlas fallar (módulo inexistente), escribir el módulo, verlas pasar.

### Tarea 2: caché de la historia de K
- [ ] Prueba: con un caché cuyo `sha_index_html` difiere del actual, la salida trae un aviso «predicado cambió»; con el
  mismo sha, ninguno. Prueba: el caché sólo guarda pasadas anteriores a la adopción de cada sensor.
- [ ] Implementar `construir_cache_k(carpeta_tag)` y `cargar_cache_k(path)`; generar el caché en local desde el tag.

### Tarea 3: salida para la página
- [ ] Prueba de punta a punta con node (fixture de 2 records por lado en carpetas temporales): el JSON trae
  `resultados`, `noches` y `meta.avisos`, y una noche con alerta de MIROVA publicada sólo por la vía sale en `noches` con
  `via_pub = 1` y `k_pub = 0`.
- [ ] `noches`: una fila por noche-satélite con algo que mirar (alerta de MIROVA en alguna referencia, o algún detector
  publica), con las dos etiquetas, VRP de MIROVA y de cada detector, y dónde cayó el foco de cada uno.

### Tarea 4: pestaña en `comparacion.html`
- [ ] Prueba estática: la página pide `data/audit_continuous/comparacion_via_k.json`, la pestaña nueva es la activa y lee
  las claves que el script escribe (lista derivada del módulo, no escrita a mano).
- [ ] Construir la pestaña; revisar en navegador real (escritorio y 375 px), consola sin errores.

### Tarea 5: workflow diario
- [ ] Prueba: el yml carga con `"on":` entre comillas (A43), corre el script con referencia fresca y commitea sólo los dos
  archivos de comparación.

### Tarea 6: verificación
- [ ] Suite completa; mutaciones a mano (cambiar FP por TN, quitar la protegida, invertir el sha del caché) atrapadas.
- [ ] Verificador con contexto limpio; PR con merge commit; merge sólo con «mergea #N» de Nicolás.
