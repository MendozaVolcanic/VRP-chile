# Pre-registro S150: la réplica frente a una erupción (Nevados de Chillán, 2026-09-14 a 2026-10-07)

> **Estado: BORRADOR, sin verificador y SIN APROBAR.** No se despacha nada hasta que (1) un verificador con
> contexto limpio lo revise y (2) Nicolás escriba "sí" (el candado `preregistro_aprobado` del workflow es suyo).
> Escrito y commiteado ANTES de correr ningún brazo sobre esta ventana.

## 1. Por qué esta prueba, y qué no puede decidir

**El fenómeno.** Desde el 2026-09-28 Nevados de Chillán tiene actividad fuerte: MIROVA publica alertas de 2 a
10 MW en los tres sensores. Todo lo que el proyecto midió de marzo a septiembre fue en volcanes en reposo,
con señales de 0,05 a 0,5 MW y uno o pocos píxeles. Una erupción es otro régimen: muchos píxeles calientes,
un cúmulo extendido, un fondo que la propia anomalía puede calentar, y focos secundarios en la escena. Un
cambio que mejora la réplica en reposo puede romperla en erupción, y al revés. Esta es la primera vez que hay
con qué probarlo fuera de Láscar.

**Lo que ya se vio en producción** (cruce del 2026-09-26 al 10-02, mismo predicado del tablero): VIIRS 375
publica las 13 alertas de MIROVA; VIIRS 750, 7 de 8; **MODIS, 1 de 3**, y la que pierde es la del
2026-10-01 08:35 (MIROVA 5,18 MW): nuestro cúmulo estaba a 0,9 km del cráter con 2,29 MW, pero la etiqueta
`far` se derivó del píxel más caliente de la escena (32,8 km) y el tablero la ocultó (A46/A81). Existe el flag
`ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER` (S132), apagado.

**Lo que NO puede decidir.** Es un volcán y diez días de actividad: 4 alertas MODIS, 21 de VIIRS 375 y 14 de
VIIRS 750 (§3). No adopta nada por sí sola. Sirve como **prueba de estrés con veto**: un candidato que en la
erupción pierde una alerta fuerte que hoy publicamos queda vetado, y lo que sale bien se lleva a una corrida
de los 11 volcanes con su propio pre-registro.

## 2. Brazos (perfiles verificados: `diff_perfiles_ndc_salida.txt`, cada uno difiere sólo en lo declarado)

| brazo | perfil | qué es |
|---|---|---|
| C0 | `_s146_ab_control` | producción tal cual (difiere de `mirova_equivalent` sólo en el directorio) |
| E | `_s150_etiqueta_cumulo` | C0 con la etiqueta MODIS desde el cúmulo |
| B | `_s146_ab_sin_test1` | C0 sin el Test 1 integrado |
| F | `_s147_ab_sin_test1_max` | B con la conectiva `max` |
| J | `_s149_ab_sin_test1_b22` | B con banda 22 primaria en MODIS |
| K | `_s149_ab_sin_test1_b22_max` | J con `max` |
| KE | `_s150_k_etiqueta` | K con la etiqueta MODIS desde el cúmulo |
| G | `_s149_ab_sin_test1_gemelo` | gemelo de B, control de determinismo |

Despacho: un solo run, `vols=["NevadosDeChillan"]`, `start=2026-09-14`, `end=2026-10-07`, los ocho brazos,
`control=_s146_ab_control`. Ocho jobs de un volcán y 24 días: del orden de una hora cada uno.

## 3. Ventana, referencia y sustrato

- **Ventana**: 2026-09-14 a 2026-10-07. Reposo del 14 al 27 de septiembre; actividad del 28 en adelante. No
  cruza el 2026-08-28 23:00 UTC (#535). Es posterior al 2026-06-13, así que **decide la etiqueta con tabla y
  OCR** (A119).
- **Referencia congelada** desde el repo del dueño, no desde el snapshot local (que el 2026-10-08 tenía su
  última sincronización el 2026-10-05): `_congelado_ndc/`, Mirova-v1 en el commit `83aba69`, con sha256 en
  `MANIFIESTO.json` (`congelar_desde_remoto.py`).
- **Sustrato**, pasadas únicas (`sustrato_ndc_salida.txt`):

| sensor | reposo: alertas / listadas sin alerta | actividad: alertas (1 MW o más, sólo OCR) / listadas sin alerta |
|---|---|---|
| MODIS | 0 / 60 | 4 (3, 0) / 38 |
| VIIRS 375 | 3 / 91 | 21 (14, 7) / 47 |
| VIIRS 750 | 0 / 90 | 14 (12, 3) / 47 |

## 4. Controles, antes de mirar ningún resultado

1. **Cobertura pareja** entre todos los brazos (A108), contada con `evaluar_ventana.py`. Si falla, se repite el
   job corto con el mismo código; no se interpreta.
2. **Determinismo**: G contra B, misma decisión de publicar en 98 de cada 100 pasadas o más, en los tres
   sensores (`--control-gemelo _s146_ab_sin_test1`).
3. **Control positivo del flag de etiqueta** (A116, A118): en E la pasada MODIS del 2026-10-01 08:35 tiene que
   salir `summit` y publicada. Ensayado offline sobre el record de producción con `derivar_distance_class`:
   `far` con el flag apagado, `summit` encendido (inner 5 km, centroide a 0,883 km). Si en el run E no la
   publica, el cableado está roto: **INDECIDIBLE**, se traza por etapa, no se concluye "no sirve".
4. **Identidad del predicado del tablero**: el de node, como en S147 a S149 (`armar_tabla.py`).

## 5. Predicciones y reglas

Cada brazo se compara con su control natural (E y B contra C0; F contra B; J contra B; K contra J; KE contra K)
con `armar_tabla.py` y la referencia congelada, pasada por pasada.

| # | qué | regla | si falla |
|---|---|---|---|
| **P1** (veto VIIRS) | F no pierde ninguna alerta de MIROVA de **1 MW o más** que B publique, en VIIRS 375 ni en VIIRS 750 | cero pérdidas | `max` queda **vetado en régimen de erupción** hasta entender la pérdida |
| **P2** (veto VIIRS) | B no pierde ninguna alerta de 1 MW o más que C0 publique, en VIIRS 375 ni VIIRS 750 | cero pérdidas | quitar el Test 1 queda vetado en erupción |
| **P3** (MODIS, etiqueta) | E publica la pasada del 2026-10-01 08:35 y no publica menos alertas MODIS que C0 | las dos | ver control 3 |
| **P4** (MODIS, banda 22) | K y KE publican las 3 alertas MODIS de 1 MW o más; K no pierde ninguna que J publique | las dos | la banda 22 no generaliza a una erupción fuera de Láscar |
| **P5** (costo, informativa) | publicaciones de E, J, K y KE en las pasadas MODIS listadas sin alerta, en reposo y en actividad, contra C0 | se informa; la tasa base de alerta MODIS de MIROVA es 0,5 % de las pasadas (AUDIT_S149 §5) | no decide: el costo en falsos se mide en la corrida de 11 volcanes |
| P6 (informativa) | VIIRS: recall por tramo de magnitud de cada brazo en actividad, y publicaciones en las pasadas listadas sin alerta en reposo | se informa | |
| P7 (informativa) | magnitud pareada en actividad, por brazo y sensor: mediana y dispersión de la razón contra MIROVA, con `pc.vrp_mw` y `f5_core_vrp_mw` | se informa | |
| P8 (informativa) | lo que cada brazo publica el 26 y 27 de septiembre, antes de la primera alerta de MIROVA, con posición y magnitud | se informa: sólo la cronología de OVDAS o un SWIR de alta resolución dirían si era calor real | |

**Veredicto por brazo**: VETADO si falla su P1, P2, P3 o P4 (con los controles en verde); SIGUE A 11 VOLCANES
si las cumple. Nada se adopta con esta prueba.

## 6. Lo que queda fuera

La suma de píxeles alertados como magnitud (no hay brazo que la implemente; P7 sólo informa), la caja de
5 × 5 km (D18), y el experimental (no tiene perfil propio todavía; P8 es su insumo).

## 7. Costo y riesgo

Ocho jobs de un volcán; no toca `data/mirova_equivalent/` ni el NRT. Autentica sólo con `EARTHDATA_TOKEN`
(rotado el 2026-10-08, vence el 2026-12-07). MODIS sólo corre en GitHub Actions (pyhdf), así que no hay ensayo
local de los brazos completos.
