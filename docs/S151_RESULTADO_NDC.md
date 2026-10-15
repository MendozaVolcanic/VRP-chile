# La réplica frente a una erupción: resultado de la prueba de Nevados de Chillán

> Escrito 2026-10-14 por el loop autónomo (tarea 1.1 de `tasks/LOOP_OBJETIVOS.md`). Pre-registro aprobado:
> `experiments/_s150_ndc/PREREGISTRO_NDC.md` (versión 3). Run 38560317428 (10 brazos, Nevados de Chillán,
> 2026-09-14 a 2026-10-07). Salida del evaluador: `experiments/_s150_ndc/resultado_38560317428/`. Verificador con
> contexto limpio: `experiments/_s150_ndc/resultado_38560317428/verificador/INFORME.md` (PARCIAL: veredictos bien
> calculados, dos de ellos se leen como algo que no dicen; ver §3).

## 1. Qué se probó y por qué

Todo lo que el proyecto midió de marzo a septiembre fue en volcanes en reposo, con señales de 0,05 a 0,5 MW.
Desde el 2026-09-28 Nevados de Chillán está en erupción y MIROVA publica alertas de 2 a 10 MW en los tres
sensores: muchos píxeles calientes, cúmulos extendidos y magnitudes que cruzan el tope de 5 MW pensado para el
reposo. La prueba es de estrés con veto: un candidato que en la erupción pierde una alerta de 1 MW o más que hoy
publicamos queda vetado. **No adopta nada**: lo que pasa sigue a una corrida de los 11 volcanes con su propio
pre-registro.

## 2. Resultado

**Controles, todos en orden.** Los 10 brazos tienen las mismas 259 pasadas (el job `recolectar` salió en rojo
sólo porque su chequeo espera 11 volcanes), con la misma versión de producto. El cableado de cada brazo, leído
de la línea `FLAGS_BRAZO` de su log, coincide con lo declarado. El gemelo decide igual que B en el 100 % de las
pasadas de los tres sensores. El verificador reprodujo la salida idéntica y recalculó por su cuenta, desde los
JSON crudos y sin el código del evaluador, las decisiones que siguen.

**Alertas fuertes (1 MW o más), lo que decide el veto:**
- **VIIRS**: ningún brazo pierde ninguna. 13 de 13 en VIIRS 375 y 11 de 11 en VIIRS 750, en los 10 brazos.
- **MODIS**: de 3 alertas en la erupción, producción (C0) publica 2 y pierde la del 2026-10-01 08:35 (MIROVA 5,18
  MW), igual que anticipaba el pre-registro. Los brazos con banda 22 y `max` (K, KE, KET) publican las 3, y
  también F y J. Pero la recuperación es frágil: K publica **1,08 MW** donde MIROVA da 5,18.

**Lo débil (bajo 1 MW) y la suma de errores** del criterio de victoria (`docs/MISSION.md`), con las etiquetas
del evaluador y contando los tres sensores, reposo y actividad (`verificador/suma.py`):

| brazo | qué es | publicaciones en negativos limpios | suma de errores bajo 1 MW |
|---|---|---|---|
| C0 | producción | 50 (mediana 0,052 MW) | 52 |
| B | sin Test 1 | 12 | 17 |
| J | B con banda 22 | (no informado por el verificador) | 23 |
| F, K, KE, KET | con `max` | 1 | 7 |

Las alertas débiles que se pierden: en VIIRS 375, tres (2026-10-05 04:48 de 0,04 MW, y en reposo 09-14 05:42 y
09-18 05:24), que también pierden B y J, así que las causa quitar el Test 1 y no `max`; en VIIRS 750, una
(2026-09-28 04:42, 0,23 MW), que sí es de `max`. La lectura B del criterio (D-4, #782) no cambia nada aquí: no
hay ninguna fila FALSO_POSITIVO nocturna de 1 MW o más en la ventana.

**Antes de la primera alerta** (26 y 27 de septiembre), producción publica 7 pasadas de 0,02 a 0,09 MW cerca del
cráter; 6 caen sobre pasadas que MIROVA registró como RUTINA y una no tiene fila de MIROVA. Los brazos con `max`
no publican ninguna.

**Magnitud**: en la erupción subestimamos. La razón mediana contra MIROVA va de 0,39 a 0,68 según brazo y sensor
(con la mediana corregida para n par, C0 en MODIS da 0,63 y no 0,68 como imprime el evaluador).

## 3. Lo que el resultado NO dice

- **El tope D9 quedó sin probar en el candidato.** P5 de T0 dice CUMPLE porque ninguna de las 11 pasadas MODIS que
  producción topa en 5 MW (sin tope llegaban hasta 122,8 MW) cambia su decisión. Pero eso es vacuo: el tope no
  toca la etiqueta `far`, que sale del píxel más caliente de la escena, así que no podía cambiar nada. En la
  familia K ninguna pasada MODIS llega a 5 MW (máximo 4,80), KET da igual que KE y P5 de KET queda SIN DATO. El
  verificador sospecha (SIN VERIFICAR) que con la etiqueta desde el cúmulo y sin tope, el filtro de cirrus
  ocultaría unas 6 pasadas topadas de E de 10 a 61 MW: en ese régimen el tope sí actuaría como compuerta.
- **P4 no prueba la etiqueta desde el cúmulo.** KE decide igual que K en todas las pasadas: la alerta del
  1-oct la recupera K sin ese flag.
- Es un volcán y diez días de actividad, con 3 alertas MODIS: son casos, no tasas.
- Quedan fuera de la suma 76 pasadas sin fila de MIROVA (`sin_info`); producción publica 36 de ellas en VIIRS 375.

## 4. Qué sigue

- Ningún candidato queda vetado por la erupción. La familia "sin Test 1 + `max`" (F, K) pasa el veto en VIIRS y
  recupera la alerta MODIS fuerte que producción pierde, con la menor suma de errores. Eso la habilita para una
  corrida de los 11 volcanes con su propio pre-registro, que es lo que dice el pre-registro de esta prueba.
- Arreglos del evaluador que pidió el verificador, para la próxima vez que se use (no cambian este resultado):
  P5 debe imprimir SIN SUSTRATO cuando ninguna pasada topada puede cambiar de etiqueta; imprimir el costo en
  VIIRS y el recall en reposo; corregir la mediana para n par; agregar un control positivo para P3.
- El tope D9 en un régimen donde actúe (etiqueta desde el cúmulo, cirrus) queda como pregunta abierta.
