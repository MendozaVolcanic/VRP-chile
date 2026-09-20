# Verificador con contexto limpio de H-A01 (S147)

> **Encargo**: verificar el hallazgo *"La adopción del Test 1 integrado se justificó con un recall
> que nunca se volvió a medir, y el acierto se contaba con el disparo del propio Test 1, o sea
> circular"* (`docs/audit_s146/FRENTE_H_HIPOTESIS_Y_AB.md:179` y `:231`). El verificador recibió
> sólo el título y la ruta, con el preámbulo anti-fabricación entero, y no participó de la
> auditoría S146.

## Veredicto

**El hallazgo se confirma en su conclusión y se equivoca en su prueba.** La circularidad es real,
pero el predicado que H-A01 cita (`pc.vrp > 0 O triggered_test1`) no es el instrumento de la
adopción de S27: existe, pero aparece 17 días después, en S48. Lo que pasa en S27 es peor y
distinto: **el número no tiene ningún script**.

Las tres respuestas del encargo: (1) circular sí, pero por la etiqueta, no por la disyunción;
(2) el reemplazo del camino comparado está confirmado y **re-medición nunca hubo**; (3) el
universo eran 507 registros de alerta, 10 volcanes, **cero negativos limpios** habiendo 11.680
disponibles en el mismo archivo.

## Hallazgos

### H1. El "50 a 80 %" no tiene instrumento (gravedad 5, CONFIRMADO)
Commit `a7b567f00fb57632b69067fc17e3bb7e5bb1c014` (2026-04-30), `docs/MIROVA_DIVERGENCES.md:855-870`.
El commit que declara "H_S27_1 CONFIRMADA" y fija el recall 50 a 80 % (406 de 507) cambia **un
solo archivo, el catálogo**, con 46 líneas insertadas. En el árbol completo de ese commit no
existe ningún script de recall sobre 11 volcanes ni sobre 507 registros: `triggered_test1` sólo
aparece en dos scripts forenses de 6 refs de Villarrica y en el campo del record. El único script
de recall commiteado de la época, `experiments/56_mirova_literal_ab/delta_report.py`, cubre 4
volcanes y 14 días, y su veredicto fue **NO APROBADO**.

**Consecuencia**: el número que hoy frena la Fase 2 no es reproducible ni auditable. No se puede
corregir ni defender, sólo volver a medir.

### H2. La circularidad entra por la etiqueta: el Test 1 escribe los dos lados del predicado (gravedad 5, CONFIRMADO)
`pipeline/process_viirs.py:721-744` en el commit `a7b567f00`; hoy
`pipeline/process_modis.py:296-317` (`derivar_distance_class`); commit `4d69ec14d`.
El bloque "Regla D Test 1-priority" fija `final_hotspot_dist_km = test1_hotspot_dist_km` y
`final_hotspot_source = "test1"` cuando el Test 1 dispara dentro del radio interno, y el mismo
commit agrega el recómputo de VRP para ese camino. `derivar_distance_class` devuelve `summit` si
la distancia cae dentro del radio interno. O sea: con el Test 1 encendido, **su disparo determina
por construcción las dos condiciones del predicado de acierto** (`distance_class == summit` y
`vrp_mw > 0`). No hace falta ninguna disyunción para que la medición sea circular: el brazo
tratado escribe la hoja de respuestas.

El commit de S26 lo dice en voz alta: el Test 1 **ya disparaba** antes (15 de 19 gránulos sobre 5
refs) y el recall era 0 de 6 **sólo porque la etiqueta salía `far`**. La regla que se agregó no
cambió la sensibilidad, cambió la etiqueta.

### H3. El único A/B limpio del Test 1 encendido contra apagado dio 6 contra 6 (gravedad 5, CONFIRMADO)
`experiments/54_test1_ab/REFS_FORENSE.md:15-18`; perfiles `_archive/_test1_enabled.yaml` y
`_test1_disabled.yaml`; workflow `_archive/reproc-ab-test1.yml`.
En S25 se corrió un A/B de una sola variable. Refs con el Test 1 disparando en el brazo
encendido: **6 de 6**. Refs detectadas por los caminos existentes en el brazo apagado: **6 de 6**.
El Test 1 no agregó ninguna ref. Los "+30 puntos" aparecen recién en S27, **después** de agregar
la regla que fuerza la etiqueta summit (H2). Muestra chica (6 refs, un volcán), así que no cierra
el asunto, pero apunta en contra del temor declarado.

### H4. Nunca hubo re-medición (gravedad 4, CONFIRMADO)
Resolviendo `extends` sobre los 165 perfiles del repo, sólo 11 tienen el Test 1 efectivamente
apagado, y diez son anteriores a S27. El único posterior es `_s146_ab_sin_test1.yaml`, o sea el
A/B que está listo y sin despachar. Entre el 2026-05-01 y el 2026-09-20 ningún commit toca
`enable_test1_path` en un perfil o workflow.

**El verificador declara haber evitado la trampa del cero (A89)**: lo comprobó resolviendo la
herencia y contando ausencia de clave, no buscando el literal `false`, que da una sola
coincidencia y engañaría.

### H5. El predicado acusado existe y es circular, pero es de S48 (gravedad 4, CONFIRMADO)
`experiments/88_audit_s47_fps_distribution.py:90-117`; `docs/HYPOTHESIS_LOG.md:912-934`.
`is_detected()` devuelve `vrp_mirovaEq(rec, inner) > 0 or is_test1_summit_detection(rec, inner)`,
y el segundo término exige `final_hotspot_source == "test1"` más `distance_class == "summit"`, o
sea está determinado por el camino que se evalúa. **Eso es exactamente lo que H-A01 describe, y es
circular.** Pero el log lo fecha en S48 (2026-05-17) y cuantifica su efecto: TP de 329 a **352**,
FN de 21 a **10**, recall de 94,0 a **97,2 %**. O sea **23 de 352 aciertos son registros con
magnitud publicada cero, acreditados sólo porque el Test 1 disparó**.

**Frente nuevo que abre**: toda métrica de recall citada entre S48 y hoy que use ese script
arrastra los +3,2 puntos circulares.

### H6. Cero negativos limpios, habiendo 11.680 en el mismo archivo (gravedad 4, CONFIRMADO)
El universo del instrumento de la época era `Tipo_Registro == "ALERTA_TERMICA"` y nada más. En la
ventana declarada de S27 (2026-01-29 a 2026-04-29) el CSV de referencia contiene **516 filas
ALERTA_TERMICA, 233 FALSO_POSITIVO y 11.680 RUTINA**. Los negativos limpios estaban ahí, en
proporción 22,6 a 1, y no se usaron. Sin ellos, una tasa sin tasa base no dice nada sobre
discriminación: la adopción se decidió sobre una métrica que por construcción sólo podía subir.

### H7. El reemplazo del camino comparado está confirmado, y son 15 días (gravedad 3, CONFIRMADO)
`pipeline/process_viirs.py:1236-1237` dice textualmente que el primer pase "reemplaza
`hot_mask_2d`" y que "paths legacy se calcularon arriba (diag) pero no contribuyen cuando ON".
`ENABLE_FIRST_PASS_TESTS_2_AND_3` está en True hoy. Entre la sincronización del perfil
operacional de S29 y la adopción de drift234 hay **15 días**. El camino contextual contra el que
el Test 1 mostró los "+30 puntos" ya no aporta píxeles.

### H8. El catálogo contradice al hallazgo dentro de la misma sesión (gravedad 3, CONFIRMADO)
`docs/MIROVA_DIVERGENCES.md:2762` dice "el resultado empírico de S27 (recall 50 a 80 %) no se
toca", mientras H-A01, de la misma sesión, dice que ese resultado es circular. Y
`docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md:214-216` lo nombra como el riesgo a considerar antes de
apagar el Test 1. El número sigue vivo además en `docs/SESSION_INDEX_CONSOLIDATED_S80.md:53`,
`docs/MIROVA_DIVERGENCES.md:2652` y `docs/LIBRO_DE_PRUEBAS.md:45`.

**Es el caso de manual de A113**: la rebaja se anotó en el informe del frente y no bajó a los
lugares donde se lee primero.

### H9. Los dos brazos de la tabla de 90 días no tuvieron el mismo universo (gravedad 3)
`docs/MIROVA_DIVERGENCES.md:867`: la fila de Nevados de Chillán dice `33% (1/3)` en un brazo y
`25% (1/4)` en el otro. El denominador es el conteo de alertas de MIROVA y **no puede cambiar
entre brazos**. Que cambie significa que no vieron el mismo conjunto de pasadas. CONFIRMADO en la
contradicción interna; SOSPECHA en la causa.

### H10. El "pre-Test 1" era un brazo mutilado, no el sistema en producción (gravedad 3)
El brazo de comparación era `_mirova_literal` **sin** Test 1, o sea con `vent_path` apagado,
`exclude_zones` apagado y el tope de 7 K removido. El A/B de 14 días contra el sistema real de
entonces dio recall **0,868 en el legacy contra 0,592 en el literal**, y el Test 1 lo subió a
0,80: **no recuperó la paridad con el sistema previo**. El encuadre "50 a 80" oculta que el punto
de partida operacional era ~87 %. CONFIRMADO para los números de cada tabla; **SOSPECHA** para la
comparación entre ellas, que son ventanas y universos distintos.

### H11. Dos citas de H-A01 apuntan a líneas equivocadas (gravedad 1, CONFIRMADO)
La frase de la disyunción está en `DIVERGENCES:887`, no en `:884-885`. El temor del plan está en
`PLAN_PARIDAD_POST_AUDITORIA_S146.md:214-216`, no en `:163-166`. A101 pide remapeo por contenido.

## Verificado limpio

- El reemplazo de S46 es real y está en producción (`ENABLE_FIRST_PASS_TESTS_2_AND_3 = True` y
  `ENABLE_TEST1_PATH = True`, leídos de `pipeline.profile`, no del YAML).
- Los números que H-A01 toma de la Fase 1 se verifican y dicen lo que dice.
- El predicado del A/B de 14 días **no** es circular: usa `vrp_mw > 0 and distance_class ==
  "summit"`, sin disyunción. Su defecto es otro.
- El predicado canónico posterior (`pipeline/audit_metrics.py`, S33) tampoco lleva la disyunción.
- La ausencia de Llaima en la tabla no es omisión: tiene 0 alertas en la ventana.
- El perfil archivado del relleno de noviembre 2025 no contaminó el corpus operacional.

## Lo que no se pudo cerrar

- **De dónde salió el 406 de 507.** Buscado por commit, por contenido, por directorio y por árbol
  completo. No está. Queda **SIN EVIDENCIA, no refutado**.
- **La reconciliación del denominador**: 516 alertas hoy contra 507 declaradas. Compatible con que
  el corpus de referencia cambió (A90), sin verificar contra un snapshot de abril.

## Recomendación del verificador

Despachar el A/B. No es redundante: sería la primera medición del aporte del Test 1 con negativos
limpios y con el pipeline actual, y la única vez que se midió limpio no encontró ganancia. Antes
de correrlo, corregir H5 y H11 en el hallazgo y propagar la rebaja al catálogo y al plan, que es
donde el número sigue apagando trabajo.
