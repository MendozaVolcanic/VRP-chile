# Propuesta para Nicolás: qué hacer con la historia, la reposición y la vigilancia si un sensor vuelve a K (S192)

**Estado: PROPUESTA, no implementada.** Escrita el 2026-11-21 en S192 junto con el PR que hace que el tablero marque
el paso de la vía a K (`frontend/cambio_detector.js`, prueba `tests/test_cambio_detector_retorno_k_s192.py`). Nada de
lo que sigue rige hasta que Nicolás elija. Mientras tanto, la reversión pre-autorizada sigue **suspendida** (decisión
de Nicolás del 2026-11-21, «Sí, suspéndela»; marca S192 de las dos reglas de reversión).

Evidencia: auditoría Codex ronda 2, frente 11, verificación limpia en
`D:\codex-vrp\_salida\ronda2\f11_verificacion\VEREDICTO.md` (fuera del repo; base `785b4c45`, datos al 2026-11-17).
Hallazgos: F11-102 (sin marca de vuelta a K, gravedad 4, lo resuelve el PR del tablero), F11-V201 (la historia),
F11-104 (la reposición del NRT) y F11-101 (la vigilancia ciega a una pasada que la guardia no tiene), los tres de
gravedad 3 y condicionales a una reversión, salvo F11-101, que actúa también sin reversión.

## 1. El fenómeno, antes que el código

Para el volcán no cambia nada: lo que cambia es la regla con que medimos su calor. La vía «código MIROVA» suma la
energía de todos los píxeles que alerta, como MIROVA; K publicaba un grupo de píxeles recortado y, en promedio, cerca de
la mitad de la potencia (ficha v1.25). Por eso cualquier tramo de una serie que pase de un método al otro tiene un
escalón que no es del volcán. Las tres preguntas de esta propuesta son la misma pregunta vista desde tres lados: si un
sensor vuelve a K, ¿qué serie ve el operador, cuánto tarda en quedar pareja y quién avisa si la guardia no estaba
mirando?

## 2. F11-V201: la historia de la vía anterior al encendido

**Qué pasa hoy.** El 2026-11-12 la serie de los 11 Tier A desde el 2025-02-15 se reemplazó por un reproceso con la vía
(ficha v1.25). Un `git revert` del PR de encendido devuelve el flag a K, pero no toca esa historia: la escribió otro
cambio. Ninguna de las dos reglas de reversión dice qué hacer con ella, y la guardia K no la puede reponer, porque
empieza el 2026-10-26 en MODIS y el 2026-11-03 en VIIRS.

**Lo que el verificador no pudo ver (SIN DATO allá, comprobado acá).** La serie K anterior al reemplazo existe y es
recuperable: el tag `pre-s180-reemplazo-historia` (commit `23841347d`, 2026-11-12 21:31:58 UTC) está en el remoto y es
antecesor de `main`, y sus `data/mirova_equivalent/*.json` son de K desde el 2025-02-15 en los tres sensores, con las
pasadas de la vía sólo desde el encendido de cada uno. Comando para comprobarlo en un volcán:

```bash
git show pre-s180-reemplazo-historia:data/mirova_equivalent/Villarrica.json > villarrica_pre_reemplazo.json
```

Las pasadas K que el reemplazo no tenía quedaron en `data/_k_residuales_via/` (ficha v1.25). Entre el encendido y una
reversión, la serie K la tiene la guardia (`data/guardia_k_modis/`, `data/guardia_k_viirs/`).

**Opciones.**

| Opción | Qué hace | A favor | En contra |
|---|---|---|---|
| A. Sólo hacia adelante | El revert apaga el flag; la historia queda de la vía y desde el revert entra K. El tablero marca «vuelve a K» (PR del tablero). | Mismo día, sin tocar datos publicados. | La serie mezcla dos métodos para siempre en ese sensor; el escalón queda marcado pero el promedio de 90 días y la comparación con MIROVA cruzan la marca. |
| B. Historia completa a K | En un PR aparte, con tag defensivo (A38) y sí de Nicolás: los records de la vía de ese sensor se apartan a `data/_via_residuales/`; antes del encendido se reponen desde `pre-s180-reemplazo-historia` (más `data/_k_residuales_via/`), y del encendido al revert desde la guardia. | La serie vuelve a un solo método, sin escalón. | Reescribe datos publicados; la guardia puede tener huecos; es un procedimiento nuevo que hay que probar antes de necesitarlo. |
| C. A el mismo día y B dentro de 7 días | Como la regla D7 de hoy, pero apuntando también a la historia y no sólo a la ventana de 8 días. | El operador ve la marca desde el primer día y la serie queda pareja en una semana. | Dos pasos; mientras tanto la serie mezcla métodos (con marca). |
| D. No volver a K por una alerta | Una protegida callada se investiga como caso y se corrige la vía (o se acepta la pérdida), sin revertir el sensor entero. | Evita cambiar de método toda la serie por una pasada; la vía publica cerca del doble de potencia que K y está más cerca de MIROVA. | Renuncia al resguardo que se pactó al encender; la decisión de cada caso queda en Nicolás. |

**Recomendación: C**, con el procedimiento B escrito y ensayado en seco (sobre una copia, sin publicar) antes de
levantar la suspensión. Razón: A sola deja un escalón permanente aunque marcado, y B sola deja al operador sin aviso el
día del cambio. D es una decisión de política, no técnica: la dejo nombrada porque, con la historia toda de la vía, el
costo de revertir creció y es legítimo preguntarse si el resguardo sigue valiendo su precio.

## 3. F11-104: la reposición con K de la ventana del NRT

**Qué pasa hoy.** El almacén sólo reemplaza un record existente con `--overwrite` o cuando un NRT asciende a producto
estándar (`pipeline/store.py`). En la ventana de 8 días de la base auditada, casi todos los records de la vía ya eran
estándar y seguirían siendo de la vía después del revert (verificador, F11-104). La regla de MODIS (§4.7 punto 1,
«El NRT re-escribe con K las 8 fechas de su ventana») es falsa en eso; la de VIIRS (§4.7) ya lo decía bien. La marca
A113 del 2026-11-07 de la regla de MODIS lo había anotado en la cabecera.

**Opciones.**

| Opción | Qué hace | A favor | En contra |
|---|---|---|---|
| 1. Reproceso con `--overwrite` | Tras el revert, un despacho del NRT de la ventana con `--overwrite` en Actions. | Usa el camino normal del pipeline. | Depende de que NASA siga sirviendo esos gránulos; corre en Actions; hay que vigilar que no choque con el cron. |
| 2. Copiar de la guardia | Los records K de la guardia de esas pasadas reemplazan a los de la vía (misma clave; el verificador midió que casi todas las claves de la guardia están en producción). | No baja nada; es una copia con prueba. | Sólo vale si el nulo de la guardia (§4.4 (c)) dio 0 diferencias; las pasadas que la guardia no tiene quedan de la vía. |
| 3. Dentro de B | La ventana se resuelve en el mismo PR que la historia (sección 2, opción B o C). | Un solo procedimiento, una sola prueba. | Hereda los tiempos de B. |

**Recomendación: 3**, usando 2 como fuente principal y 1 sólo para las pasadas que la guardia no tenga. Y corregir la
frase de la regla de MODIS con una marca A113 cuando se escriba la regla nueva (punto 2 de la suspensión).

## 4. F11-101: la protegida que la guardia no vio

**Qué pasa hoy.** Si MIROVA publica una protegida, la vía la calla y la guardia K **no tiene record** de esa pasada, la
vigilancia sale VERDE: no hay comparación posible y no se abre issue. El verificador mostró que la pérdida deja rastro
(`protegidas_sin_publicar_produccion` en el JSON de la vigilancia, y la auditoría semanal de los lunes la marca como
fuera de banda), pero con hasta 7 días de demora. No ocurrió en los datos (0 calladas en 48 protegidas posteriores a los
encendidos). Actúa con o sin reversión: es la vigilancia de que la vía no pierda alertas.

**Opciones.**

| Opción | Qué hace | A favor | En contra |
|---|---|---|---|
| a. Nuevo disparador de investigación | Protegida que MIROVA publica, la vía calla y la guardia no tiene, pasadas 24 h: issue «investigar» el mismo día (como §4.4 (a), al revés). Cambia `scripts/vigilancia_guardia_modis.py` (lo hereda VIIRS) y sus pruebas; no toca `pipeline/`. | Aviso en el día; no depende de que K haya mirado. | Un disparador más; necesita su prueba de mutación y su control (A110, A116). |
| b. Que «sin guardia» sea vigilancia ciega | La falta de record de la guardia en una protegida pasa a ser aviso de `VIGILANCIA_CIEGA`. | Reusa un veredicto que ya abre issue. | Mezcla «la guardia no corrió» con «la vía perdió algo»; el issue no dice lo segundo. |
| c. Dejarlo en la auditoría semanal | Sin cambios. | Nada que mantener. | Hasta 7 días de demora en la alerta más grave del sistema (un FN de 1 MW o más). |

**Recomendación: a.** Es la que dice el problema con su nombre y lo dice el mismo día. No es reversión: con la
suspensión vigente, todo lo que encuentre se lleva a Nicolás.

## 5. Qué haría falta para levantar la suspensión

1. El PR del tablero que marca «vuelve a K» (S192), mergeado y visto en el tablero publicado.
2. Una regla aprobada por Nicolás que elija entre A, B, C o D de la sección 2 y, si es B o C, el procedimiento escrito y
   ensayado en seco.
3. Opcional pero recomendado: el disparador (a) de la sección 4.

## Decisiones que se le piden a Nicolás

| # | Pregunta | Recomendación |
|---|---|---|
| P1 | Si un sensor vuelve a K, ¿qué pasa con su historia publicada? | C: hacia adelante el mismo día con marca, y la historia a K en un PR aparte dentro de 7 días (desde `pre-s180-reemplazo-historia` y la guardia). |
| P2 | ¿Cómo se repone la ventana del NRT? | Dentro del mismo PR de la historia, con los records de la guardia y reproceso sólo donde la guardia no tenga. |
| P3 | ¿Se agrega el disparador de investigación para la protegida que la guardia no vio? | Sí (opción a). |
| P4 | ¿Se mantiene la idea de revertir un sensor entero por una alerta (o se pasa a investigar caso a caso, opción D)? | Decisión de política; sin recomendación técnica. |
