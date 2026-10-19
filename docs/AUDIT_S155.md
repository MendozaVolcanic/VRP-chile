# Auditoría post-K (S155, 2026-10-19)

Auditoría del sistema un día después de que el detector K entró a producción (#850, squash `34cea39e`, 2026-10-18
09:57:30 UTC: Test 1 integrado apagado, conectiva `max` en los Tests 2 y 3, banda 22 primaria en MODIS). Escala
aprobada por Nicolás en el plan de S155 (`tasks/PLAN_S155.md`, rama `loop/activo`): cinco frentes con un auditor cada
uno y un verificador con contexto limpio por frente, todos Opus, cada uno en su worktree sobre `origin/main`
`cb90031a`, sin commits, sin despachos y sin Earthdata local. El verificador recibió sólo los títulos y las ubicaciones
del auditor, no su informe.

**Cómo leer este documento.** Vale el veredicto y la gravedad **del verificador**, no los del auditor. Cada hallazgo
apunta a la carpeta con el informe completo, los scripts y su salida cruda, en `experiments/_s155_audit/`. Lo que pesaba
más de 1 MB (copias de datos de commits viejos, productos intermedios) quedó fuera del repo y está listado en
`experiments/_s155_audit/EXCLUIDOS.md`. Ningún número de este documento se escribió a mano: todos salen de esas salidas.

## 1. Lo que ya quedó arreglado en esta sesión

| | qué | PR |
|---|---|---|
| candado del A/B diurno sobre K | pruebas que atrapan 71 de 72 mutaciones (la restante, equivalente); tag `s154-diurno-k-codigo` en `e66b402c`, sin despachar | #859 (mergeado) |
| marca del cambio de detector | la línea iba en el merge (18-oct) y el escalón de los datos está en la fecha de observación 2026-09-18; ahora va ahí, y una prueba contra los JSON avisa cuando la frontera se mueva | #860 |

## 2. El hallazgo que encontraron cuatro por separado

**La frontera C0/K de los datos es el 2026-09-18, no el 2026-10-18** (gravedad 4, CONFIRMADO por los verificadores de
los frentes 1, 2 y 4, encontrado por los auditores de los frentes 2, 3 y 4). Los 30 días anteriores al merge se
reprocesaron con K, así que desde la fecha de observación 2026-09-18 todos los records son K salvo 26 MODIS Terra que
no se pudieron reprocesar. En `diario.html`, días con barra VIIRS 375 antes y después del 18-sep: Copahue 56 y 0,
Llaima 52 y 0, Villarrica 53 y 2, Chaitén 55 y 3, con datos todos los días (`frente_2_verif/`). La publicación de
VIIRS 375 en negativos limpios pasa de 0,86 el 17-sep a 0,16 el 18-sep (`frente_4_verif/`). Arreglado en #860. **De
esta frontera cuelgan casi todos los demás hallazgos**: cualquier cosa que agregue 90 o 60 días hoy mezcla dos
detectores, y nada en el sistema lee `regimen.codigo_sha` para separarlos (F2-12, F3-09).

## 3. Hallazgos verificados, de más grave a menos

### Gravedad 4

- **F3-02, el auto-audit registra una sobre-publicación que K no tiene.** VIIRS 375 publica en negativos limpios 31,1 %
  (n 940) en la ventana de hoy; separado por régimen, 86,5 % con C0 (n 325) y 1,8 % con K (n 615). El número mezclado va
  a `data/audit_continuous/history.jsonl` y es unas 8 veces la cota del A/B (0,0383) que dispara la reversión. La parte
  C0 sale de la ventana el 17-nov salvo que el histórico la reescriba antes. CONFIRMADO (`frente_3_verif/`).
- **F3-04 y F5-05, alertas protegidas de Chillán que K no detecta y ningún instrumento ve.** MODIS 2026-10-12 07:20 UTC
  (2,18 MW) y 2026-10-15 01:05 (1,72 MW), las dos a unos 58° de cenit: con K, 0 píxeles anómalos; el más tibio a 24 y
  29 km. Por noche no se pierden (VIIRS 375 publicó esas noches). El auto-audit no tiene criterio de alertas protegidas y
  su banda de recall MODIS no puede dispararse desde el 2026-08-03 porque nunca junta 15 noches. CONFIRMADO
  (`frente_3_verif/`, `frente_5_verif/`).
- **F2-02, Chillán en erupción se ve un nivel más abajo que en MIROVA.** Razón mediana entre lo mostrado y MIROVA: 0,573
  VIIRS 375, 0,418 VIIRS 750, 0,240 MODIS (98 pares en el mismo minuto). De 38 pasadas Moderado de MIROVA, el tablero
  muestra 24 como Bajo o Muy Bajo y nunca muestra un nivel mayor. No es propio de K (Láscar con C0 da 0,56) y depende
  del cenit: 0,75 a 0,85 bajo 25°, 0,19 a 0,51 desde 45°. CONFIRMADO (`frente_2_verif/`).
- **F5-01, en VIIRS 750 y MODIS se publica un cúmulo parcial.** Afecta 13 de 37 pasadas VIIRS 750 de Chillán: 11 por el
  modo de un píxel (mediana ×1,17, máximo ×2,21) y 8 por la selección del cúmulo más cercano al cráter (×1,88, máximo
  ×5,98); en logaritmo, 36 % del déficit es del modo y 64 % de la selección. Peor caso: 2026-10-10 06:30 VIIRS 750,
  publicamos 4,33 MW, alertamos 25,89 y MIROVA dio 32,0. El modo de un píxel se activa por fragmento, no por erupción:
  sobre 60° está en modo máximo en 7 de 7 pasadas (V5-04). CONFIRMADO el defecto, PARCIAL la atribución del auditor
  (`frente_5_verif/`).

### Gravedad 3

- **F3-05, el #779 de Tupungatito.** El 0,647 sí es ventana rodante (reproducido desde commits viejos), pero dentro de la
  ventana C0 hay un cambio de nivel: 0,835 (n 8) antes del 12-sep y 0,395 (n 6) después; K solo, 0,364 (n 10).
  CONFIRMADO.
- **F3-06, la magnitud del audit no es la publicada.** Usa `pc.vrp_mw` y junta sensores en una mediana. «K/C0 = 1,0 en las
  mismas pasadas» vale en 7 de 8 volcanes, no en Láscar (0,705, n 18). PARCIAL.
- **F3-08, el recall del audit juzga «cráter», no publicación, y no aplica D-9.** 5 de las 8 pérdidas K de VIIRS 375 son
  de 0,05 MW o menos. Con D-9, K en VIIRS 375 da 96,7 % (n 91), dentro de banda; lo que la mezcla esconde de verdad está
  en VIIRS 750 (22 de 30, todas bajo 0,4 MW) y en MODIS (8 de 12, con la protegida de Chillán) (V3-03). CONFIRMADO.
- **F3-09 y F2-12, nadie lee `regimen.codigo_sha`.** Ni las vistas ni los instrumentos; `latest.json` y `history.jsonl`
  no traen régimen. Cuando se aplique el histórico con K la frontera se moverá otra vez sin que ninguna serie lo
  registre. CONFIRMADO.
- **F2-03, el gráfico de distancia salta en la frontera.** Con C0, entre 17 y 87 % de los puntos en 0,0 km por el ancla
  `test1_roi`; con K, ninguno: parece actividad de flanco. CONFIRMADO.
- **F2-07, la corroboración de la tarjeta cuenta lejanas y C0.** Copahue «nuestras 400»: 143 lejanas y 390 C0; en la
  cumbre con K publica 0. CONFIRMADO.
- **F4-05, el NO ADOPTAR de D22/D25 (H_S143) se midió con Test 1 encendido, `min` y sólo VIIRS 375.** El pre-registro de
  D22 sobre `max` (`experiments/_s150_ab_d22`) está suspendido a propósito, no olvidado. Láscar 2026-10-08 con cúmulo en
  0,0 MW contra 0,29 de MIROVA confirmado; atribuirlo a D25 es SOSPECHA. CONFIRMADO.
- **V4-02, el segundo pase con primer pase vacío (D2) sostiene parte de lo que K publica:** 17 % en VIIRS 375 y 31 % en
  VIIRS 750, 21 pasadas con alerta de MIROVA. Encender `conditioned` las apagaría, y la evidencia de esa decisión es de C0.
- **V2-01, una alerta protegida de Copahue oculta como lejana.** 2026-10-16 06:18 UTC, MIROVA OCR 1,34 MW; el pipeline ve
  un píxel de 1,238 MW a 6,5 km al oeste del cráter, fuera del radio interno de 4 km. Que se oculta: CONFIRMADO. Que sea
  el objeto de MIROVA: SOSPECHA (su imagen era de otra pasada).
- **F5-09 y V5-01, VIIRS 375 cuenta doble en el borde del barrido.** 6 de 51 pasadas de Chillán, todas sobre 50°, inflan
  hasta ×1,88; la «paridad» del 10-10 06:30 VIIRS 375 es doble cuenta (11,82 baja a 6,70 frente a 12,17 de MIROVA).
  Origen inferido sin L1B. CONFIRMADO en VIIRS 375.
- **F5-03, en VIIRS 375 el fondo no explica la caída con el ángulo.** Con fondo cero la razón sigue cayendo (0,89 / 0,68
  / 0,68 / 0,42); con un modelo de área completa la curva queda plana. Que la causa sea D17 sigue SOSPECHA. Es insumo del
  pre-registro de D25 (1.29): gravedad 4 para ese pre-registro.
- **V5-02 (SOSPECHA), sumar todos los fragmentos de VIIRS 750 también contaría doble** si son huellas solapadas: los
  factores de F5-01 son cota superior y un arreglo tiene que deduplicar por huella.

### Gravedad 2

- **F1-04**: D11 sigue cerrado aunque su condición («sólo bajo banda 21») cayó; fuera de Láscar la publicación MODIS en
  negativos limpios bajó de 242 a 18 de 2.173 con K.
- **F1-05, F1-06, F1-07, F1-11, F1-12**: cabecera de `mirova_equivalent.yaml` con el Test 1 encendido; la ficha SDA no
  declara el costo de K en VIIRS 750 (32 a 28 de 42, 95 a 91 de 117) y afirma más que A61; «el laboratorio es idéntico
  al operacional» es falso (corre C0) y su guard sólo compara pisos; cabeceras FICHA que atribuyen el Test 1 a Coppola
  sin decir que está apagado; en `main` el último bloque de arranque es S150.
- **F1-02 y F1-03 (rebajados de 3 a 2)**: el modal «Acerca de» fecha sus métricas (S119) pero no dice que son de C0; los
  encabezados de D21 y D30 dicen «ABIERTA» con la marca S153 en la línea siguiente.
- **F1-01 (PARCIAL, 3)**: `git revert 34cea39e` choca hoy en `frontend/cambio_detector.js` y su test; si se revierte,
  el `<script>` sale de las tres vistas y el js queda huérfano. Ningún texto nombra el commit a revertir.
- **V1-03 y V1-04**: la FICHA de `detection_context.py` describe el criterio sin `max` y dice «mitigado por
  co-validación» con `PATH_D_REQUIRES_COVALIDATION=False`; **la vigilancia de la sombra, disparador de la reversión
  pre-autorizada, no tiene código**.
- **F2-04, F2-05, F2-06, F2-08, F2-10**: la anomalía relativa de la tarjeta usa una base mezclada (Chillán p93 · 110,6×
  contra p82 · 3,4× sólo K); el panel cuenta como FN alertas diurnas y no aplica la regla SN; los encabezados de 90 días
  mezclan detectores; 26 Terra C0 sin marca, 2 publicados en PCC (los dos con RUTINA y VRP 0 de MIROVA); en MODIS el
  marcador `eruption` cae hasta 2,27 km fuera del cúmulo.
- **F3-07, F3-10**: el issue del audit pone la causa «S124» sin medirla, declara una banda que no es la del código y no
  deduplica; el watchdog mide la edad del run, no la del job (#824, 25 comentarios por un reproceso sano).
- **F4-03 a F4-09 (PARCIALES y CONFIRMADOS de 2)**: A98, A103, A117, D9, D10 y otros cierres medidos bajo C0 quedan sin
  respaldo o cambian de razón; las mediciones y los matices están en `frente_4_verif/INFORME.md`. Notable: F4-07 en
  VIIRS 750 quedó REFUTADO en el par (0,418 a 0,418 en las mismas pasadas).
- **V3-01, V5-03**: predecir el auto-audit con la referencia vieja da números falsos (con la fresca, 2 flags y no 3); la
  referencia de MIROVA no está congelada (80 contra 105 pares de Chillán según el snapshot): un pre-registro tiene que
  fijar el CSV por hash.
- **V5-06**: el radio de núcleo de F5' es fijo en 0,75 km y fuera del nadir deja fuera vecinos del cráter (13 de 17 sobre
  60°, hasta ×1,73), en sentido contrario a V5-01.

### Gravedad 1

F1-08, F1-10, F1-13, F1-14, F1-15, F2-09, F2-11, F3-11, F3-12, F4-10 a F4-13, F5-07 (con banda 22 primaria, MODIS
convierte a radiancia con la λ de la banda 21: factor 0,950 a 0,970; V5-05 sospecha lo mismo en el NTI de detección),
F5-08, V3-05, V4-05. Detalle en cada informe.

## 4. Lo que los verificadores corrigieron o refutaron

| hallazgo del auditor | corrección |
|---|---|
| F1-01: si se revierte, el aviso seguiría diciendo K | falso: el revert saca el `<script>` y el aviso desaparece |
| F3-01: el audit del lunes abrirá 3 flags | 2 (Chillán y Tupungatito): el auditor no refrescó la referencia, el cron sí |
| F4-03: A98 «se invirtió» | no: K publica de más en 27 noches negativas y pierde 3 a 4 positivas; cae la premisa de recall saturado |
| F4-07: la mediana VIIRS 750 bajó de 0,60 a 0,42 | REFUTADO en el par (0,418 a 0,418); la baja de VIIRS 375 es en parte de ventana |
| F5-01: factores ×1,46 y ×1,92, VIIRS 375 inmune | no se reproducen; el déficit es 36 % modo y 64 % selección, y VIIRS 375 cuenta doble en el borde |
| F2-09: el núcleo supera al cúmulo en 177 | 157 de 284; los dos cambios de nivel acercan a MIROVA |

## 5. Arreglos propuestos, en orden

1. **Hecho**: marca en la frontera de los datos (#860).
2. **Separar por régimen en el auto-audit y en las vistas** (tarea 1.35, ampliada): leer `regimen.codigo_sha`, informar
   C0 y K por separado, estratificar por sensor dentro del volcán y por cenit, aplicar D-9 y separar cráter de
   publicación. Con esto caen F3-01, F3-02, F3-06, F3-08, F2-04, F2-06 y F2-07. Insumo: la lista de estratos de
   `frente_3/INFORME.md`. No toca `pipeline/`.
3. **Criterio nominal de alertas protegidas en el auto-audit** (F3-04): una lista de cada alerta de 1 MW o más sin
   publicar, sin mínimo de noches.
4. **Código de la vigilancia de la sombra** (V1-04): es el disparador de la reversión pre-autorizada y no existe.
5. **Propagación de K en los textos** (frente 1): tablero, ficha SDA, CLAUDE.md y MISSION, encabezados del catálogo,
   cabeceras de código, INDEX. Orden según dónde se lee primero (A113).
6. **Magnitud en erupción** (F5-01, F5-09, V5-02, F2-02): tocan `pipeline/` (selección `vent_anchored`, modo de un
   píxel, deduplicación de huellas). Primero el pre-registro de D25 sobre K (1.29) con lo que dejó el frente 5, y la
   referencia de MIROVA fijada por hash (V5-03). A45: tag defensivo y sí de Nicolás.
7. **Watchdog por duración de job y deduplicación de issues** (F3-07, F3-10).

## 6. Decisiones para Nicolás

- **Orden de los arreglos 2 a 4** (recomendación: 2 y 3 juntos, antes del próximo auto-audit semanal, porque el del
  lunes va a abrir un issue con dos flags que son mezcla).
- **Qué hacer con los cierres medidos bajo C0** (frente 4): re-medir sobre K los que apagan frentes vivos (D22, D25, D2
  con `conditioned`) o dejarlos SIN EVIDENCIA hasta que se necesiten.
- **El modo de un píxel en erupción** (F5-01, V5-04): describir el mecanismo está hecho; cambiarlo es metodológico y va
  por pre-registro.

## 7. Límites

- Sin L1B: las mediciones que lo necesitan (bow-tie, fondo real de vecinos, huella geolocalizada, agregación de M13, las
  dos FN MODIS de Chillán) quedaron especificadas en `frente_5/granulos_l1b_salida.txt` y no se hicieron.
- El censo de cierres busca por palabras clave y es un piso (frente 4).
- `evaluar_fk.py` y `libro_de_cuentas.py` no se revisaron (frente 3).
- Ventanas C0 y K en estaciones distintas: lo que decide es la comparación pareada sobre el tag
  `pre-s154-reproc-k-datos` (frente 4 verificador).
