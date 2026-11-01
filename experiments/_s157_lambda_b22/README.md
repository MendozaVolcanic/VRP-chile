# S157: la longitud de onda de la vuelta a radiancia de MODIS con K

Hallazgo lateral de la sesión de magnitud de Chillán (#869): con el detector K, la magnitud MODIS vuelve a
radiancia con la longitud de onda de la banda 21 aunque la temperatura venga de la banda 22. Este directorio
investiga si es un defecto, lo mide contra MIROVA y deja el arreglo detrás de un flag apagado.

**Veredicto: es un defecto.** Con K la magnitud MODIS sale entre 1,053 y 1,075 veces más baja que la que da
la radiancia medida (mediana 1,0575, 24 records). Arreglo listo detrás de `enable_modis_mir_lambda_por_banda`,
apagado; encenderlo es decisión de Nicolás (A45).

## 1. El fenómeno físico

Las bandas 21 y 22 de MODIS miran **la misma ventana espectral** del infrarrojo medio; lo que las separa es la
ganancia. La 22 es la fina (poco ruido, satura a unos 331 K) y la 21 es la gruesa (aguanta hasta ~500 K). Sobre
un mismo píxel las dos reportan la misma radiancia, que es lo que el satélite mide de verdad.

La temperatura de brillo no es una medición sino una traducción de esa radiancia con la ley de Planck, y para
traducir hay que decir a qué longitud de onda. El pipeline traduce a temperatura para trabajar los umbrales
(que están en kelvin) y después vuelve a radiancia para la fórmula de potencia, que es un exceso de radiancia.
Ida y vuelta devuelven la radiancia medida **sólo si las dos usan la misma longitud de onda**. Con K, la ida se
hace con 3,959 µm (la de la banda 22) y la vuelta con 3,929 µm (la de la banda 21): a temperaturas de fondo
nocturno eso devuelve una radiancia ~5 % más baja que la medida, y la potencia hereda ese 5 %.

Bajo C0 (banda 21 primaria) ida y vuelta usaban 3,929 µm y el error no existía. Apareció con la adopción de K
(#850, 2026-10-18) y afecta a todos los records MODIS con K, que en el tablero son los del 2026-09-18 en
adelante.

## 2. Qué dicen los papers (leídos renderizando la página a imagen, A95)

| Fuente | Dónde | Qué dice |
|---|---|---|
| Coppola et al. 2016a, `documentacion/sp426.5.pdf` | p. 3, columna izquierda, lista (iv) y (v) | Radiancia de la banda 21 «centred at 3.959 µm (low-gain MIR channel)» y de la banda 22 «centred at 3.959 µm (high-gain MIR channel)»: **la misma λ para las dos**. |
| ídem | p. 3, columna derecha, primer párrafo | «we built a corrected spectral band centred at 3.959 µm (hereby called band L21ok), by using the L21 or L22 radiance, depending on band 22 saturation (or not)». MIROVA arma una sola banda **con radiancias**, a 3,959 µm. |
| ídem | p. 8, columna derecha, Ec. 6 y 7 | ΔL = L_alerta − L_fondo, ambas «4 µm radiance»; L_fondo es «the arithmetic mean of all the pixels surrounding the active one». RP = 18,9 · A_PIX · ΔL. **El exceso se calcula en radiancia**, sin pasar por temperatura. |
| ídem | p. 5, columna izquierda, Ec. 2 | L_MIR,app = P_MIR(T_app): el NTI aparente usa Planck en la banda MIR (o sea, 3,959 µm). Ver §6. |
| Coppola 2025, cap. 11 Springer | `documentacion/coppola2024_chapter.txt` l. 1034 y 1136 | MODIS «MIR (3.959 µm)» en la Tabla 2 y «MODIS data (λMIR = 3.959 µm)» para la Ec. 17. **Sólo hay el .txt**, no el PDF (el `NO_ES_cap11_...pdf` no es el capítulo): no se pudo renderizar. Los dígitos coinciden con Coppola 2016a. |
| Wooster et al. 2003 | **no está en `documentacion/`** | Sólo existe la nota del Vault `wooster2003fire.md`, marcada `ai_generated: true`: por A35 no sirve como autoridad numérica. No hace falta para la conclusión (ver §3). |

**Respuesta a «qué banda, qué λ y qué coeficiente usa MIROVA en MODIS»**: la banda corregida L21ok (B22, o B21
donde B22 satura), una sola λ de 3,959 µm para las dos, el exceso calculado directamente en radiancia, y
RP = 18,9 · A · ΔL. Nuestro `BAND21_LAMBDA = 3.929` (desde el commit inicial, sin cita) es el **borde inferior**
de la ventana, no su centro: el docstring de `merge_mir_bands` lo dice («misma ventana (3,929-3,989 µm)»).

## 3. Con qué radiancia se calibró el 18,9 de S14

`experiments/21_calibrate_k_viirs375_vs_osf.py` y `experiments/21_results.json` (S14): el método es
«reconstruct coef = VRP / (Tot_Lmir_hot − Tot_Lmir_bk) directly on OSF v2.5 rows». El coeficiente se
reconstruyó **con las columnas de radiancia del propio archivo de MIROVA**, no con nuestra radiancia ni con
nuestra temperatura (n = 13.157 filas MODIS, mediana 18.900.000 con A = 1e6, error 2·10⁻¹⁴ %). O sea que el
18,9 es el coeficiente que MIROVA aplica a **su** radiancia medida de L21ok, y no depende de ninguna λ nuestra.
El arreglo no toca el coeficiente: devuelve a la Ec. 7 la radiancia medida, que es la que el 18,9 espera.

## 4. Traza (A6, A102)

Líneas en el tag `pre-s157-lambda-b22` (= `origin/main` f101d7304, producción) y en la rama.

**De dónde sale `bt_mir`** (`pipeline/process_modis.py`): `calibrate()` l. 253-261 deja NaN todo DN > 32767,
incluida la saturación (65533); l. 552-554: `bt21 = radiance_to_bt(rad21, BAND21_LAMBDA)`,
`bt22 = radiance_to_bt(rad22, BAND22_LAMBDA)`, `bt_mir = merge_mir_bands(bt21, bt22, ENABLE_MODIS_B22_PRIMARY)`
(l. 323-340: con K, B22 donde no es NaN y B21 donde B22 saturó). Después, l. 560-561, el guard de 500 K.

**Sitios donde una BT MIR vuelve a radiancia o entra en Planck MIR:**

| # | tag | rama | Qué | ¿Corre con K? | Con el flag |
|---|---|---|---|---|---|
| 1 | process_modis.py:1036 | :1083 | `L_bg_global`, fondo del anillo | sí | λ de la banda primaria |
| 2 | :1040 | :1087-1088 | `hotpix_rad`, radiancia de cada píxel alertado | sí | λ de la banda de origen del píxel |
| 3 | :1062 | :1110 | `L_bg` del kernel local 3×3 (5 Tier A opt-in) | sí, con `local_kernel_bg` | λ primaria |
| 4 | :1155 → vrp_regimes.py:279-287 | :1203-1204 → vrp_regimes.py | magnitud por corona del cúmulo | no (`ENABLE_LOCAL_CLUSTER_MAGNITUDE` OFF) | λ por píxel (`lambda_grid`), fondo con la primaria |
| 5 | :1253-1254 | :1302-1304 | camino de vent | no (`ENABLE_VENT_PATH_MODIS` OFF) | píxel con su λ, fondo con la primaria |
| 6 | :746 → test1_integrated.py:442 | :793 → test1_integrated.py | Test 1 integrado (detección en radiancia + su `L_bg`) | no (`enable_test1_path: false`, D30) | λ por píxel (`bt_to_radiance_um` acepta un arreglo de λ) |
| 7 | :1367 | :1417 | `effective_L_bg` del recompute Test 1 | no (sólo si `final_hotspot_source == "test1"`) | λ primaria |
| 8 | :1377, :1392 | :1427-1428, :1443-1444 | `t1_rad` del recompute Test 1 | no | λ por píxel |
| 9 | :1528 | :1580 | `diag_L_bg_w_m2_sr_um` (diagnóstico) | sí | λ primaria |
| 10 | :773 y :857 → detection_context.py:625 | sin cambio | `NTI_app`: Planck MIR de la temperatura TIR | sí, :857 en el primer pase | **no se toca**, ver §6 |

Copias en línea buscadas (A102): `process_viirs.py` (I04, una sola banda, `I04_LAMBDA = 3.740`) y
`process_viirs_mod.py` (M13, una sola banda) no mezclan bandas: no tienen el defecto. `f5_core.py` y
`scan_geometry.py` no llaman a Planck. El tablero (`frontend/`) no reconvierte radiancia. Fuera del pipeline,
`scripts/descomponer_magnitud_osf.py:57` (`LAM = {..., 1000: 3.929}`) reconstruye nuestra magnitud MODIS con
la λ de B21: reproduce lo que hace el procesador (correcto para describir producción, no para la radiancia
medida); se deja igual y se anota.

## 5. El efecto medido

Script: `medir_efecto_lambda.py` (salida en `medir_efecto_lambda_salida.json` y `.txt`). Sin L1B: el record
guarda la magnitud del cúmulo, el número de píxeles y el fondo con que se restó, y con eso la cuenta de Planck
se invierte exacta (fórmulas en el docstring). Ventana: desde la frontera de K (`DATOS_K_DESDE_UTC` de
`frontend/cambio_detector.js`, 2026-09-18) hasta el 2026-10-20, 11 Tier A, records con marca de K.

Controles del instrumento: (A) el script reproduce `diag_L_bg_w_m2_sr_um` de 743 records con error relativo
máximo 3,7·10⁻⁴ (el redondeo del campo); (B) reproduce el VRP de 23 píxeles de `anomaly_pixels` con
error mediano 3,5·10⁻⁴ y p95 2,7·10⁻³ (redondeo a 4 decimales); (C) con la λ vieja en los dos lados el método
da F = 1 con error 1,7·10⁻¹⁴.

| Medida | Resultado |
|---|---|
| Records MODIS con K y magnitud de cúmulo | 25 (1 topado por D9, factor 1) |
| Factor F (magnitud corregida / actual) | mín 1,0527 · mediana 1,0575 · máx 1,0753 (n = 24) |
| Sensibilidad a suponer magnitud de un píxel | diferencia máxima de F 0,0036 |
| Records con kernel local de fondo | 10 de 24 (PCC, Villarrica, Planchón) |
| Inversión exacta por píxel (verificador, desde `bt_k` y `vrp_mw` de cada píxel) | F del píxel pico 1,0514 a 1,0753, mediana 1,0575 |
| Píxel representativo saturado (B21) | 0 de 24 |
| Por volcán (mediana F) | Chillán 1,054 (13) · PCC 1,060 (7) · Villarrica 1,071 (2) · Láscar 1,060 (1) · Planchón 1,075 (1) |

F sube cuando el fondo es más frío (la diferencia relativa de Planck entre 3,929 y 3,959 µm crece al bajar la
temperatura), por eso Villarrica y Planchón están arriba.

**Contra MIROVA** (pasadas MODIS con K, alerta de MIROVA, publicadas por el tablero; predicado del tablero
ejecutado con node, A97; consolidado `d742f26a`, OCR `3dbea0cc`): n = **12**, 11 de Chillán y 1 de Láscar.

| | antes | después |
|---|---|---|
| razón nuestra / MIROVA, mediana | 0,362 | 0,382 |
| rango | 0,076 a 0,847 | 0,080 a 0,893 |
| mediana de \|log razón\| | 1,076 | 1,024 |
| Chillán (11) | 0,240 | 0,253 |
| Láscar (1) | 0,488 | 0,517 |

Las 12 razones están bajo 1, así que corregir hacia arriba acerca a MIROVA en las 12. Pero **es un 5 %**: no
cierra la brecha de Chillán (que #869 atribuye al fondo, D25, y a la selección), y 12 pasadas de dos volcanes
no son una muestra para hablar de paridad por volcán. Lo que el arreglo hace es quitar un sesgo conocido y de
signo fijo de la magnitud MODIS, no resolver la magnitud.

El extremo bajo exacto es 1,051 (Chillán 2026-10-16 01:40, dos píxeles fuera del modo de un píxel): la
aproximación del script con el promedio por píxel lo sobreestima en 0,001. En el resto coincide a 4 decimales.

## 6. Lo que NO se tocó, a propósito

1. **`NTI_app` (sitio 10)**. Coppola 2016a p. 5 Ec. 2 lo arma con Planck en la banda MIR, o sea 3,959 µm;
   nosotros usamos 3,929 µm con C0 y con K. Es la misma clase de error pero **mueve la detección** (entra al
   ETI del primer pase), no la magnitud, y la regresión cuadrática de NTI_bk absorbe buena parte de un cambio
   suave de λ. Sin L1B no se puede medir: **SIN MEDIR**. Va como propuesta aparte, con A/B.
2. **`BAND21_LAMBDA = 3.929`**. El paper centra las dos bandas en 3,959 µm. Con K sólo afecta la temperatura
   de los píxeles que saturan B22 (sobre ~331 K), que el arreglo ya devuelve a su radiancia medida porque usa
   la misma λ en la ida y en la vuelta. Cambiar el 3,929 mueve umbrales en kelvin de esos píxeles y de C0;
   queda anotado, no se cambia. Matiz del verificador (H12): con K cae a B21 todo píxel con DN inválido de B22,
   no sólo el saturado (`calibrate()` deja NaN todo DN > 32767), y ese píxel entra a `bt_mir` con un escalón de
   ~1,3 K respecto de sus vecinos de B22 (misma radiancia, otra λ en la inversión). Toca σ y umbrales en
   kelvin, no la magnitud. Cuántos son, sin L1B: SIN MEDIR. Bajo C0 pasaba lo simétrico en los píxeles de
   respaldo de B22, población no medida.
3. **El fondo como temperatura y no como radiancia**. El paper promedia **radiancias** de los vecinos (p. 8);
   el pipeline toma la mediana de temperaturas del anillo y la convierte. Es D25, no este frente.

## 7. El arreglo

- Flag `enable_modis_mir_lambda_por_banda` en `pipeline/profile.py` (raíz o `paths:`), escrito `false` en
  `pipeline/profiles/mirova_equivalent.yaml`. Tag defensivo `pre-s157-lambda-b22` en `origin/main` f101d7304.
- `process_modis.lambda_mir_por_pixel` (λ de la banda de origen de cada píxel, misma regla que
  `merge_mir_bands`), `lambda_mir_fondo` (λ de la banda primaria) y `lambda_en`. Con el flag apagado la λ es el
  **escalar** de siempre: un arreglo float64 cambiaría la aritmética float32 de hoy.
- `vrp_regimes.cluster_vrp_per_pixel_with_bg` acepta `lambda_grid` opcional; sin él, igual que antes.
- Tests: `tests/test_lambda_por_banda_modis_s157.py` (7). RED observado antes del arreglo: el píxel de B22 daba
  8,054 MW contra 8,469 de su radiancia medida (razón 1,0515) y el de B21 saturado 400,24 contra 399,98 (el
  fondo). El guard de la clave del YAML se comprobó con mutación: renombrar la clave en `profile.py` lo hace caer.
- La regla de origen de banda decide con `bt21` y `bt22`, los mismos arreglos con que `merge_mir_bands` arma
  `bt_mir` (verificador H11: con las radiancias diferiría donde la radiancia es negativa).
- Identidad con el flag apagado: `identidad_flag_apagado.py` corre `process_modis.py`, `vrp_regimes.py` y
  `test1_integrated.py` del tag contra los de la rama sobre 96 combinaciones (3 escenas × B22 primaria o no ×
  kernel local × corona × vent × Test 1 integrado): **96 de 96 idénticas**; control con el flag encendido y B22
  primaria, **48 de 48 distintas**; cobertura: encender kernel local, corona, vent o Test 1 cambia el record en
  6 de 6 escenas cada uno. Límite: compara el record serializado, que ya viene redondeado; por lectura, con el
  flag apagado las expresiones son textualmente las del tag con el mismo escalar de Python (verificador H8).
- Suite completa con el árbol quieto: ver el cuerpo del PR (la primera corrida dio 2 fallas causadas por esta
  rama, un guard de texto del fondo persistido y una cita `file:line` de CLAUDE.md que se corrió; las dos se
  actualizaron).

## 8. Verificador con contexto limpio

Informe completo en `verificador/INFORME_VERIFICADOR.md` (Opus, contexto limpio, leyó el paper renderizado,
re-corrió los dos scripts desde copias e hizo tres mediciones propias). Veredicto: partes 1, 2, 3 y 5
**CONFIRMADAS**; la parte 4 era **PARCIAL** porque el Test 1 usaba la λ de B22 también en los píxeles de B21 (H10).
Aplicado en esta rama: H1 (guard de texto que la rama rompía), H10 (Test 1 con λ por píxel), H11 (regla de
origen con las temperaturas), H7 y H9 (números y borde de Chillán en este README), H12 (anotado en §6). H13: el
script escribe sus salidas junto a sí mismo; correrlo de nuevo sobrescribe las commiteadas, que es lo buscado
para reproducir, pero para una verificación conviene correr una copia.

## 9. Si Nicolás decide encenderlo

Es un cambio de magnitud publicada en MODIS (+5 a +7,5 %). La máscara de píxeles alertados no depende de esta
λ, y el signo del exceso tampoco (misma λ en píxel y fondo). El tablero, además de `pc.vrp_mw > 0`, filtra
artefactos por magnitud (10 y 50 MW, `frontend/index.html`): el verificador corrió el predicado del tablero con
node sobre los 743 records MODIS con K escalando la magnitud por 1,05, 1,0753 y 1,20 y **no cambió ninguna
publicación** (control con ×100: 5 cambios). El píxel pico tampoco cambia en ningún record. Hay un borde de
régimen: el modo de un solo píxel se corta en 5 MW. De los 25 records con K, **uno** lo cruza: Chillán
2026-10-01 01:45, 4,804 MW; su segundo píxel tiene VRP 0 con cualquier λ, así que pasa a **5,064 MW** (×1,054,
exactamente su F), sale del modo de un píxel (cambia la etiqueta, no el número) y el tope D9 no actúa porque su
fondo es 271,72 K. Pasos: flip del YAML, reproceso de los records MODIS con K desde el
2026-09-18 (o esperar al NRT y marcar la frontera), FICHA SDA a v-siguiente, y un control a los 7 días de que la
razón MODIS contra MIROVA se movió en la dirección y el tamaño medidos acá. El auto-audit semanal compara
magnitudes contra una banda: revisar que el +5 % no cruce el borde de ningún volcán.
