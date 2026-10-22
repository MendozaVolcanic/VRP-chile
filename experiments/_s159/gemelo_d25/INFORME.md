# Gemelo de D25: cuánto ruido mide K' cuando corre en el mismo job que K (S159, 2026-10-21)

Auditoría de sólo lectura. No se tocó `pipeline/`, `data/` ni `frontend/`. No se abrió, cargó ni contó nada del brazo D
(`_s157_ab_d25_k_on`): de la rama de salida de V1 se extrajeron sólo las rutas de K y K' con `git show` por ruta, y no
se abrieron `cobertura*.json` ni `cobertura.txt` de la corrida, que traen los tres brazos juntos.

Datos (fuera del repo):
- V1 de D25, run 39530508296, rama `origin/s146-ab/39530508296` (commit de código `66961f65d`, tag
  `s157-d25-k-codigo`): `D:\vrp-trabajo\temporales\s159_gemelo\v1\K\`, `...\v1\Kp\`, `...\v1\logs\` (sólo logs de K y K').
- F/K V1, run 38639658446, rama `origin/s146-ab/38639658446` (commit `402447f33`): control C0 (`_s146_ab_control`) y su
  gemelo (`_s151_ab_control_gemelo`, 10 volcanes, sin Villarrica): `D:\vrp-trabajo\temporales\s159_gemelo\fk_v1\`.

Instrumento: `C:\vrp-trabajo\s159-pruebas\experiments\_s159\gemelo_d25\discordancia_gemelo.py`. Parea por (volcán,
sensor, gránulo), aplica el filtro nocturno del evaluador (`banco_paridad`), ejecuta el predicado del tablero con node
(`banco_paridad.correr_node`: `isSummitDetection`, `isValidDetection`, `isThermalArtifact`, `mirovaEqVrpDisplay` de
`frontend/index.html`, A97) y cuenta por estrato: publicación distinta, `pc.vrp_mw` distinto, magnitud del tablero
distinta y record distinto en cualquier campo salvo `processed_utc`, `first_processed_utc` y `regimen`.

**Las dos preguntas del instrumento.** (1) Si la publicación de K' estuviera cambiada, ¿lo vería? Sí: el control de
mutación (abajo) cambia un número conocido de records y el instrumento devuelve exactamente ese número, en los dos
sensores. (2) Si el instrumento estuviera muerto, ¿el cero se vería distinto? Sí: el denominador es 4.524 pasadas
pareadas (no cero), la mutación da conteos exactos y un par de brazos con detector distinto da 1.576 discordancias.
El cero de K contra K' es por lo tanto un dato, no un «no medí».

## 1. Cómo corren los brazos en V1 (leído en el commit de la corrida)

- `.github/workflows/reproc-s146-ab-sin-test1.yml` en `66961f65d`, l. 73 a 77: «los brazos de un A/B comparten volcan y
  ventana, asi que corren en el MISMO job». l. 115 a 116: la matrix es `job` (volcán por trozo), no volcán por brazo.
  l. 184 a 191: un solo paso llama `scripts/reproc_brazos.py --perfiles "$PERFILES"` con todos los brazos.
- `scripts/plan_trozos_ab.py` l. 24 (mismo commit): cada job es `{"vol", "idx", "start", "end"}`, sin brazo.
- `scripts/reproc_brazos.py` l. 80 a 89: día por fuera, brazo por dentro; **un proceso `run_pipeline.py` aparte por
  brazo y día, en serie, en la misma máquina**. l. 74 a 78: todos los procesos comparten `VRP_CACHE_BUSQUEDA_DIR` (la
  respuesta de CMR que dejó el primero) y `VRP_TMP_DIR` con `VRP_CONSERVAR_GRANULOS=1` (los gránulos que bajó el primer
  brazo; los siguientes los leen del disco). l. 98: el día se borra recién después de correr todos los brazos.
- Comprobado en los logs de la corrida: los 11 logs de K y los 11 de K' traen 4 líneas `FLAGS_BRAZO` (4 trozos por
  volcán), idénticas entre K y K' salvo nombre y directorio (md5 `b0fa37a9` en los 11). Los 4.610 records de cada
  brazo llevan `codigo_sha` `66961f65d`.

Conclusión: **K y K' corren en el mismo job, en procesos distintos pero en serie sobre la misma CPU, con los mismos
bytes de entrada.** Para comparar: en F/K (antes de #877, workflow del commit `402447f33`, l. 78 a 80) la matrix era
`volcano × profile`, un brazo por job, o sea máquina virtual distinta para el gemelo (que la CPU fuera distinta no está
verificado: no se consultó la API).

## 2. Discordancia K contra K' en V1 (2026-08-29 a 2026-10-18)

Salida: `v1_K_Kp_sin_dias_cmr.txt` y `.json`. Sin los días de D-29 (13, 17 y 18 de octubre enteros; el 13 se excluye
entero, no sólo la parte que CMR no sirvió). Los records de V1 llegan hasta el 2026-10-17; no hay ninguno del 18.

| estrato | pasadas pareadas | K publica | K' publica | publicación distinta | `pc.vrp_mw` distinto | record distinto |
|---|---|---|---|---|---|---|
| VIIRS 375, cenit ≤ 40 | 828 | 252 | 252 | **0** | 0 | 0 |
| VIIRS 375, cenit > 40 | 1.443 | 198 | 198 | **0** | 0 | 0 |
| VIIRS 750, cenit ≤ 40 | 824 | 52 | 52 | **0** | 0 | 0 |
| VIIRS 750, cenit > 40 | 1.429 | 27 | 27 | **0** | 0 | 0 |
| total | 4.524 | 529 | 529 | **0** | 0 | 0 |

Pasadas no pareadas (en un brazo y no en el otro): 0 y 0. Con los días de D-29 (`v1_K_Kp_con_dias_cmr.txt`): 4.610
pasadas, 545 publicadas en cada brazo, **0** en todas las columnas. `campos_distintos_v1_K_Kp.txt`: en 4.610 pares no
difiere ningún campo fuera de las marcas de hora. K' es una copia bit a bit de K.

Ojo con el alcance: esto cuenta **todas** las pasadas nocturnas, no sólo las que el evaluador etiqueta como error de
P2. Como el ruido de P2 es la diferencia simétrica de un subconjunto de estas pasadas, con cero aquí el ruido de P2
en V1 es cero a fortiori, en los dos sensores, con las dos reglas (original y SN) y con o sin los días de D-29.

## 3. Controles

**Control de mutación** (`control_mutacion.txt`, `control_mutacion_60.txt`): sobre una copia de K se ponen en `far` n
records publicados y se suben en 0,5 MW los cúmulos de otros n records no publicados.
- n = 7: el instrumento da 8 publicaciones distintas (7 apagadas + 1 encendida), 7 `pc.vrp_mw` distintos y 14 records
  distintos. La encendida es Nevados de Chillán, NOAA-21, `VJ202IMG.A2026256.0600`: un cúmulo `summit` en 0,0 MW que con
  0,5 MW pasa a publicarse, que es justo el tipo de caso que D25 puede encender (pre-registro §3).
- n = 60: 76 publicaciones distintas (60 apagadas + 16 encendidas; 529 − 60 + 16 = 485, el conteo de K' mutado), 60
  `pc.vrp_mw`, 120 records; 16 de las distintas son de VIIRS 750. El instrumento ve los dos sensores.

**Control positivo real** (`control_positivo_K_contra_C0.txt`): K de D25 contra C0 de F/K (detector anterior, con el
Test 1), 2026-08-29 a 2026-10-08, 10 volcanes: 1.576 publicaciones distintas en 3.444 pasadas pareadas (1.193 en VIIRS
375, 383 en VIIRS 750). Un par de brazos que sí difiere da discordancia grande.

## 4. El ruido entre máquinas sí está medido, y también da cero

`fk_v1_C0_C0p_jobs_distintos.txt`: C0 contra su gemelo de F/K V1 (run 38639658446, un brazo por job), 2026-08-29 a
2026-10-08, 10 volcanes (el gemelo no tiene Villarrica).

| estrato | pasadas pareadas | publicación distinta | `pc.vrp_mw` distinto | record distinto |
|---|---|---|---|---|
| VIIRS 375 (≤ 40 / > 40) | 1.724 (648 / 1.076) | **0** | 0 | 832 |
| VIIRS 750 (≤ 40 / > 40) | 1.696 (642 / 1.054) | **0** | 0 | 832 |
| MODIS | 841 | 0 | 0 | 421 |

Los records difieren, pero sólo en el redondeo (`campos_distintos_fk_C0_C0p.txt`, `tamano_deti_fk_C0_C0p.txt`): en
VIIRS sólo cambian `diag_mu_deti` y `diag_sd_deti`, con diferencia absoluta máxima de 1,8e-16 (VIIRS 375) y 1,2e-15
(VIIRS 750); en MODIS además cambian `anomaly_pixels`, `vrp_mir_mw` y el hotspot de escena (el desempate de S152; el
run es del 2026-10-14, anterior a #844). Ninguna de esas diferencias movió una publicación ni un cúmulo. Es decir: el
ruido de CPU **existe** entre máquinas (se ve en los decimales), y en este caso **no alcanzó** ninguna decisión.

Además, entre jobs distintos hubo 95 pasadas no pareadas (29 sólo en C0, 66 sólo en el gemelo; cada job bajó sus
propios gránulos y CMR no sirvió lo mismo). En el diseño de #877 ese ruido de cobertura también es cero por
construcción, porque todos los brazos leen los gránulos que bajó el primero.

## 5. Hallazgos

### H1. El ruido de P2 en V1 es cero por construcción, no medido
- ARCHIVO:LÍNEA: `scripts/reproc_brazos.py:74-89` y `.github/workflows/reproc-s146-ab-sin-test1.yml:73-77,115-116,188`
  (commit `66961f65d`); pre-registro `experiments/_s157_prereg_d25/PREREGISTRO.md` §5, fila P2 («Ruido = pasadas
  discordantes entre K y K'») y §2 (K' «ruido del runner... desempates que dependen de la CPU, S152»).
- QUÉ PASA: el desempate que depende de la CPU sólo aparece si dos brazos corren en máquinas distintas. Con K y K' en
  el mismo job, misma CPU y mismos gránulos, salen idénticos bit a bit (0 de 4.524). El ruido de P2 vale 0 y P2 decide
  GANA o PIERDE con una sola pasada neta.
- CÓMO SE VE EN EL DASHBOARD: invisible. Sólo cambia cómo se lee el veredicto del A/B.
- CÓMO REPRODUCIRLO: `python discordancia_gemelo.py --a D:/vrp-trabajo/temporales/s159_gemelo/v1/K --b
  D:/vrp-trabajo/temporales/s159_gemelo/v1/Kp --desde 2026-08-29 --hasta 2026-10-18 --excluir
  2026-10-13,2026-10-17,2026-10-18`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2. Matiz que la rebaja: D también corre en el mismo job que K, así que la comparación K contra D tampoco
  tiene ruido de CPU ni de cobertura. El cero describe bien la comparación que se hace. Lo que no dice es si el
  veredicto se repetiría en otra CPU, y eso decide si una victoria o derrota por una o dos pasadas es reproducible.

### H2. El control 4 del §7 (determinismo, 98 de cada 100 o más) no puede fallar
- ARCHIVO:LÍNEA: `PREREGISTRO.md` §7, punto 4.
- QUÉ PASA: con el gemelo en el mismo job, el determinismo da 100 % por construcción. Es un nulo que no tiene camino
  para dar rojo (A110, A116), igual que el nulo de M que el verificador ya reemplazó (H3 del pre-registro).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: el mismo comando de H1 (columna «publicación distinta» = 0 en todos los estratos).
- CONFIANZA: CONFIRMADO (el 100 % lo medí; que no pueda fallar se sigue del diseño leído en H1, salvo que el pipeline
  tuviera azar dentro de un mismo proceso, cosa que este resultado descarta para V1).
- GRAVEDAD: 2.

### H3. La medición entre máquinas que el gemelo debía hacer ya existe y da cero, pero con otro detector
- SCRIPT:SALIDA: `fk_v1_C0_C0p_jobs_distintos.txt`.
- QUÉ PASA: entre jobs distintos, 0 publicaciones distintas en 1.724 pasadas VIIRS 375 y 1.696 VIIRS 750 (y 0 en 841
  MODIS). Pero es el detector C0 (con el Test 1, sin la conectiva `max`), sin Villarrica, y del commit `402447f33`.
  Que el mismo cero valga para K es SOSPECHA razonable (el redondeo es del mismo tamaño, 1e-16, y no depende del
  perfil), no medición.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO el número; SOSPECHA su traspaso a K.
- GRAVEDAD: 1 (es la pieza que permite corregir H1 sin despachar).

## 6. Recomendación para una adenda (no implementada)

1. Declarar que en V1 el gemelo corrió en el mismo job que K y D, y que por eso mide sólo el determinismo dentro de una
   máquina (0 de 4.524 pasadas, 0 campos distintos), no el ruido entre CPU. Retirar el control 4 del §7 como control,
   o reescribirlo como prueba de determinismo con su alcance dicho.
2. Para el ruido entre máquinas, citar la medición que sí existe sin despachar nada: F/K V1, run 38639658446, C0 contra
   gemelo en jobs distintos, **0 de 1.724** (VIIRS 375) y **0 de 1.696** (VIIRS 750), con su salvedad de detector. La
   fracción de S152 (153 de 6.482 pares MODIS) no sirve: es MODIS, que D25 no toca, y es anterior a #844.
3. Con ruido 0 bien fundado, P2 decide por una pasada neta. Decisión para Nicolás, antes del tag de lectura: (a)
   aceptarlo así y decirlo en la primera línea del veredicto, o (b) tratar un GANA o PIERDE de una o dos pasadas netas
   como «se listan y se diagnostican por pasada» (cabecera de la imagen de MIROVA, A61) antes de declararlo. La opción
   cara, repetir el job de K en otra máquina para un par de volcanes, sí mide el ruido de K con su propio detector,
   pero obliga a despachar.
4. V2 no tiene gemelo y toma el ruido de V1 (`--ruido-de v1.json`): heredará este mismo 0. Como V2a y V2b también corren
   K y D en el mismo job (mismo workflow, mismo tag, `d25.log`), el 0 es coherente allí, con la misma salvedad.

## VERIFICADO LIMPIO

- K y K' leen los mismos flags salvo nombre y directorio, en los 11 volcanes y los 4 trozos: `grep '^FLAGS_BRAZO'` de
  `D:\vrp-trabajo\temporales\s159_gemelo\v1\logs\*` con el nombre normalizado da el mismo md5 (`b0fa37a9`) en los 22.
- Los dos brazos son del mismo código: 4.610 de 4.610 records con `regimen.codigo_sha` `66961f65d`, que es el commit del
  tag `s157-d25-k-codigo` (`git rev-parse 's157-d25-k-codigo^{commit}'`).
- Cobertura K contra K' en V1: 0 pasadas sin par en cada lado (salida de `discordancia_gemelo.py`).
- Ni K ni K' tienen records MODIS en V1 (los sensores del `Counter` son sólo VIIRS), como pide el §2.
- No hay records duplicados por (volcán, sensor, gránulo) en ninguno de los cuatro directorios (`duplicados: [0, 0]`).
- No se miró: el brazo D, la cobertura conjunta de la corrida, ni por qué el run 39530508296 terminó en `failure`
  (`D:\vrp-trabajo\temporales\s158\d25.log`); eso último queda SIN DATO para este frente.
