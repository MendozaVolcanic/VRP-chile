# Tercera adenda al pre-registro de D25 sobre K: el gemelo mide determinismo, y P2 se decide con ruido de muestreo

**SELLADA por Nicolás el 2026-10-21 (D-34).** Respuesta textual, registrada por la sesión dueña del loop (S159), a la
propuesta de decidir P2 con un intervalo por bloques noche-volcán (opción c, con la variante de que un neto en contra
bloquee): «si, has lo que nos entregue mayor informacion o la mejor metodologia para lograr nuestro trabajo, tenemos
tokens  tiempo y podemos probarlo todo». D-34 reemplaza a D-33 (listar y diagnosticar a mano todo GANA o PIERDE de una
o dos pasadas netas), que nunca se implementó: usaba un corte arbitrario de dos pasadas y un diagnóstico hecho después
de mirar. Escrita **antes** de leer el veredicto de V1, V2a y V2b, que siguen sin leer. Todo lo que esta adenda no toca
rige como está en `PREREGISTRO.md`, `ADENDA_CALIBRACION.md` (D-27) y `ADENDA_PLACEBO.md` (D-28, D-30 y D-32).

## 1. Qué falla

El pre-registro (§5, fila P2) decide P2 comparando la suma de errores de D con la de K **más o menos el ruido**, y
define el ruido como las pasadas en que K y su gemelo K' publican distinto. La idea era que K' corriera en otra máquina
y midiera cuánto cambia la publicación por desempates que dependen de la CPU (S152).

En V1 eso no pasó. Informe: `C:\vrp-trabajo\s159-pruebas\experiments\_s159\gemelo_d25\INFORME.md` (rama `s159-pruebas`,
commit `d5b6839b2`), auditoría de sólo lectura que no abrió nada del brazo D. Los tres brazos corren en el **mismo
job**, en procesos en serie sobre la misma CPU y con los mismos gránulos en disco (`scripts/reproc_brazos.py` l. 74 a 89
y el workflow l. 73 a 77 en el commit de la corrida, `66961f65d`). Resultado: **K' es copia bit a bit de K**, con 0 de
4.610 pasadas con publicación o `pc.vrp_mw` distintos, y ningún campo distinto salvo las marcas de hora. El ruido de P2
vale 0 por construcción, y P2 decide GANA o PIERDE con **una sola pasada neta**.

## 2. Qué mide K'

**Determinismo dentro de una máquina**, y nada más: que un mismo código, con los mismos bytes de entrada y en la misma
CPU, publica lo mismo. En V1 lo cumple (0 de 4.610). No mide el ruido entre máquinas ni el de muestreo. El control 4
del §7 del pre-registro (determinismo de 98 de cada 100 o más) sigue como está, leído con ese alcance.

## 3. El ruido entre máquinas que sí está medido, con su salvedad

En F/K V1 (run 38639658446, un brazo por job, o sea máquina virtual distinta para el gemelo), el control C0 contra su
gemelo dio **0 de 1.724** pasadas con publicación distinta en VIIRS 375 y **0 de 1.696** en VIIRS 750 (2026-08-29 a
2026-10-08), mismo informe, §4. Las diferencias que sí hubo están en el redondeo (1e-16 a 1e-15 en `diag_mu_deti` y
`diag_sd_deti`) y ninguna movió una publicación.

**Salvedad:** es el detector C0 (con el Test 1 integrado y sin la conectiva `max`), sin Villarrica (el gemelo de F/K no
lo tiene) y de otro commit (`402447f33`). Que el mismo cero valga para K es una sospecha razonable, no una medición.

## 4. Lo que importa no es el ruido de la máquina sino el de muestreo

Aunque el ruido de máquina valga cero, P2 tiene que preguntar si D publica mejor que K **en general** o sólo **en estas
noches**. Las pasadas de una misma noche comparten el estado del volcán y de la atmósfera (la razón por la que M usa
bloques noche-volcán, H9 del pre-registro): ocho pasadas discordantes de una sola noche son una noche, no ocho pruebas.

## 5. La regla nueva de P2

Reemplaza a «ruido = pasadas discordantes entre K y K'» del §5 del pre-registro. Por sensor, como hoy, con las mismas
pasadas que P2 ya cuenta (lectura A, reglas original y SN, manda la más estricta, y en V1 sin las pasadas sólo OCR de
Suomi NPP).

1. **La unidad**: las pasadas en que K y D difieren en la suma de P2 (una cuenta como error en un brazo y no en el
   otro). Las pasadas en que los dos aciertan o los dos se equivocan no entran.
2. **El estadístico y su signo**: P2 cuenta **errores** (§5 del pre-registro: alertas Muy Bajo que el brazo no publica,
   más publicaciones en negativos limpios). El neto es **errores de D menos errores de K**, y es igual a la suma de D
   menos la suma de K. Cada pasada discordante aporta +1 si el error es sólo de D y -1 si es sólo de K. O sea: una alerta
   bajo 1 MW que D publica y K no **resta** (D comete un error menos), una que K publica y D no **suma**, una publicación
   de D en un negativo limpio que K no tiene **suma**, y una de K que D no tiene **resta**. **Positivo es malo para D.**
3. **El intervalo**: bootstrap al 95 % del neto por bloques noche-volcán, con la misma maquinaria y la misma semilla que
   M (`pesos_bloque`, 10.000 remuestreos, semilla 157, D-27): cada réplica remuestrea bloques con reposición y suma las
   contribuciones con el peso de su bloque.
4. **El veredicto**: **GANA** si el intervalo queda entero bajo 0; **PIERDE** si queda entero sobre 0; **EMPATE** si
   cruza 0.
5. **La variante**: un neto en contra de D (estimación puntual sobre 0) que no alcance PIERDE da **BLOQUEA**: bloquea
   CUMPLE, igual que un EMPEORA en un estrato de M que sólo bloquea. La ventana queda en DECIDE NICOLAS con el motivo.
6. **Sin sustrato**: con menos de 5 pasadas discordantes o menos de 3 noches-volcán (los mínimos de M), P2 da
   **SIN SUSTRATO** y no decide ni bloquea.
7. **La lista de pasadas discordantes se informa siempre** y no decide: volcán, sensor, hora, si publica K y si publica
   D, clase de MIROVA (etiqueta del pareo) y su VRP, `pc.vrp_mw` de cada brazo, de quién es el error y su contribución.
8. **Lo que habrían dado las otras reglas se informa en el JSON, sin decidir**: (a) la regla anterior (suma de D contra
   la de K más o menos el ruido del gemelo, o en V2 la fracción medida en V1) y (b) la de D-33 (la anterior, pero un GANA
   o PIERDE de una o dos pasadas netas queda pendiente de diagnóstico). Así se ve si la elección de regla cambia el
   veredicto.

## 6. Lo que esta adenda no toca

- P1, P1b, M y su comparador, P4 y P5.
- El informe de P2 por noche-volcán (A94), que sigue al lado.
- Los días que CMR no sirve, que se deciden aparte.
