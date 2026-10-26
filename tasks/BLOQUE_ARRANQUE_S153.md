# Bloque de arranque S153 (cierre de S152, el loop, vueltas 99 a 170)

Escrito el 2026-10-17 a las 20:25 UTC sobre `loop/activo` en `e25f701b` (igual al remoto); `main` en `061b6f59`.
**Se fijó con trabajo en curso** (tabla a, filas «corriendo»): un agente que arregla el PR #847 puede empujar a su
rama después de este cierre, y cuatro runs de GitHub siguen vivos. La bitácora completa está en
`tasks/LOOP_OBJETIVOS.md` de `loop/activo` (§4 tareas, §5 decisiones, §6 bitácora, vueltas 99 a 170). Ante una
discrepancia manda la bitácora y, por encima de ella, el remoto. El bloque S152 queda como histórico.

## a. Todo en una pantalla

| estado | qué | evidencia |
|---|---|---|
| hecho | Mirova-v1 escribe `Distancia_aprox_*` con `Distancia_km` y las otras 24 columnas idénticas byte a byte | vuelta 99, commit `f8a2ee01` de Mirova-v1 |
| hecho | IndexError del probe de saturación arreglado | #839 (`57c70ee5`) |
| hecho | Informe de cambios al paper, verificado (10 FALSA, 19 REBAJADA, 13 DESACTUALIZADA, 13 FALTA); NO se reescribió nada | `experiments/_s152_paper_revision/INFORME_CAMBIOS_PAPER_v2.md` |
| hecho | `unir_intentos.py` con tolerancia (#841) y con la categoría `hotspot_escena` (#843, D-16 a) | `1a6f595b`, `dc0b7e26` |
| hecho | F/K V1 unida (44 de 44) y evaluada: con lectura A, F y K CUMPLEN; verificador PARCIAL; cabeceras de las 11 protegidas sólo OCR Suomi NPP revisadas (Tupungatito lejano) | `experiments/_s151_prereg_fk_11/resultado_v1/` (v1.log, VERIFICADOR.md, CABECERAS_SNPP.md) |
| hecho | F/K V2a unida y pareja (5.876 por brazo) | vuelta 123; uniones en el scratchpad de S152 (se pierden con él: rehacer con `unir_intentos.py`) |
| hecho | Probe 1.21 (MxD03 + etiqueta desde el cúmulo): EMPEORA, verificador CONFIRMADO | `experiments/_s151_mxd03_cumulo_121/resultado/` |
| hecho | Desempate determinista del top-100 MODIS en producción (#844, D-17) y cosmético (#845); tests de `main` verdes | `eed583b4`, `061b6f59`; tag defensivo `pre-s151-desempate-top100` |
| hecho | Pre-registro 1.23 (MxD03 sola) sellado y mergeado | #846 (`eb97779f`), tag `s151-1.23-probe` |
| hecho | Diurno: W2 (salvo D-16 de Copahue, ya resuelta con #843), W3 y W4 completas y parejas | vueltas 114, 127, 128, 134, 136, 148 |
| corriendo | 1.23, medio job suelto `Lascar-2a` para cronometrar | run 39066031570 (tag `s151-1.23-probe`) |
| corriendo | F/K V2b (desde tag `s151-fk-v2-codigo` = `7b74435e`, el pipeline de V1 y V2a) | run 39033530622, 18 de 22 a las 20:25 |
| corriendo | Diurno W5a; W5b pendiente detrás | runs 39032518643 (21 de 22), 39041204976 |
| a medias | G3 del diurno con `comparar()` (#847): falta el arreglo de `borde` (sólo con listas de 100 píxeles) y rehacer las uniones de W2, V1 y V2a | PR #847 (`a278acd2`), verificador en `experiments/_s151_ab_diurno_g3_verif/VERIFICADOR_V1.md`; el agente sigue vivo |
| sin despachar | Diurno W6a (2026-10-01 a 10-07) y W6b (10-08 a 10-14) | despachar con `--ref s151-diurno-codigo` (NO `main`: #844 cambió el pipeline) |
| sin despachar | 1.23, los otros 23 medios jobs | desde el MISMO tag `s151-1.23-probe`, sólo si `Lascar-2a` termina bajo el umbral del README (l. 464) |
| en cola | Tarea 1.23 deriva de los 8 records (más píxeles hoy que los guardados), sin commit identificado | tarea 1.23 en §4 |

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Cadencia del cron externo del NRT (sigue cada 30 min; canceló corridas a las 14:30, 15:00, 15:30 y 20:00 UTC por el grupo `push-main`) | `10 1-12 * * *` UTC · cada hora · dejar | **`10 1-12 * * *` UTC**, en cron-job.org (su cuenta) |
| 2 | Token `vrp-chile-cron-externo` | sin vencimiento hoy (dicho por Nicolás) · regenerar con 90 días | regenerar con 90 días cuando pueda; anotado en `REGISTRO_CREDENCIALES.md` fila 31 |
| 3 | Reproceso acotado de los ~29 records MODIS que el desempate podría cambiar | hacerlo · no | opcional; útil sólo para ver la dirección (SOSPECHA: 9 de lejana a cráter, 2 dejan de publicarse) |
| 4 | Sello de la sonda de tres campos (1.2, PR #776) | sellar · esperar | revisarla en la próxima sesión antes de sellar: lleva días quieta |
| 5 | Cronología OVDAS de Chillán y coordenadas de Cerro Blanco, Pichi-Llaima, Lazufre, El Agrio (1.11) | entregar · esperar | entregarlas: son la vara del perfil experimental |
| 6 | MxD03 en producción | después de la 1.23 | esperar el resultado de la 1.23 |
| 7 | Mirova-v1#23, punto 4 | sin revisar en S152 | leerlo y traer recomendación |

## c. Lo aprendido (destino propuesto)

1. **Un A/B partido en despachos con `--ref main` puede mezclar pipelines**: entre V2a y V2b entraron tres cambios a
   `pipeline/`. Cada ventana se despacha desde un tag fijado en el commit de su primera mitad, y los artefactos guardan
   el commit (1.21). → enmienda de A108 en `CLAUDE.md` del proyecto.
2. **`np.argsort` por defecto no es estable y desempata distinto según la CPU** (AVX-512 contra AVX2): dos corridas del
   mismo commit en runners distintos dieron records distintos (153 de 6.482 pares MODIS, empates exactos de VRP).
   Para un top-k o un máximo que decide algo, usar orden estable con clave determinista. → **regla general del workspace**.
3. **Una mutación que hace caer al evaluador no es una mutación atrapada**: cuatro del G3 contaban así. El contador
   debe distinguir FALLA de caída. → **regla general del workspace** (A110/A116).
4. **«Borde» sólo es empate donde el recorte actúa**: con listas cortas, un píxel distinto es otra detección. Una
   tolerancia de comparación hay que acotarla a la condición física que la justifica. → proyecto (`unir_intentos.py`).
5. **Un re-run de un workflow que publica una rama propia deja el job de recolección en rojo** (la rama ya existe):
   el «rojo conocido» de S147 tenía esa causa. → proyecto (workflows de A/B).
6. **Un cron externo con un grupo de concurrencia compartido desplaza corridas de otros workflows**: GitHub guarda un
   solo pendiente por grupo. → **regla general del workspace** (GitHub Actions).
7. **Windows Update instalando ocupa ~5 GB temporales y se recupera al reiniciar**: el disco bajó de 18 a 3,04 GB y el
   loop se detuvo (§1.5). Ante una caída de disco, mirar `C:\Windows\SoftwareDistribution` antes de borrar nada. →
   **regla general del workspace**.
8. **Pedir la hora al servidor antes de escribir la entrada** (A86): en S152 se estimó mal cinco veces. → sin cambio de regla.
9. **El verificador limpio corrigió afirmaciones del orquestador seis veces en S152** (mecanismo del desempate, «MxD03
   mueve k menos que el azar», «far_ref sin VRP», 50 contra 29 records, el test que no discriminaba el hotspot, el
   `borde` en listas cortas). → refuerza A111; sin cambio.

## d. Problemas abiertos e hipótesis

| | | |
|---|---|---|
| CONFIRMADO | El desempate no estable del top-100 MODIS explica las diferencias entre intentos (empates exactos; `NPY_DISABLE_CPU_FEATURES=X86_V3` cambia el top-100 del `argsort` por defecto) | #844 y su verificador |
| CONFIRMADO | `borde` admite listas cortas en `comparar()` (VIIRS) | `experiments/_s151_ab_diurno_g3_verif/VERIFICADOR_V1.md` |
| CONFIRMADO | P3 de `evaluar_fk.py` no puede fallar en V375 tal como está (51,9 % de pares con d = 0); sin el Test 1 la magnitud queda ~28 % bajo C0 en los pares que cambian | verificador de F/K V1 |
| SOSPECHA | Las 2 protegidas de Tupungatito que F/K dejan son objetos lejanos (distancia propia leída a ojo, 22,6 y 9,6 km) | `CABECERAS_SNPP.md` |
| SOSPECHA | El Test 1 MODIS vive en su piso de ruido (k medio 1,8 a 2,3, ruido 2,1, umbral 3) | medido sobre la 1.21 por el autor de la 1.23, verificado sólo en reproducción |
| SOSPECHA | `diag_mu_deti` y `diag_sd_deti` varían con la CPU por `polyfit` sobre OpenBLAS | #844, sin arreglar |
| SOSPECHA | 8 records salen hoy con más píxeles anómalos que los guardados por una deriva de código | verificador de la 1.21 |
| CONFIRMADO | numpy no está fijado en `requirements.txt` | #844 |

## e. Lo que ya está cerrado (no rehacer)

- La distancia aproximada en Mirova-v1 escribe bien; no hace falta tocar `restore-keys`.
- La etiqueta desde el cúmulo (1.21): EMPEORA, no adoptable.
- El desempate del top-100 (D-16 b, 1.22): en producción desde `eed583b4`.
- `unir_intentos.py` acepta ruido de máquina y el hotspot de escena MODIS con condiciones estrictas (#841, #843).
- F/K V1 cumple con lectura A (verificador PARCIAL): no se reevalúa; se combina con V2.
- El informe del paper está entregado; la reescritura espera el visto bueno de Nicolás.

## f. Prompt para la próxima sesión

```
/loop Sigue tasks/LOOP_OBJETIVOS.md del repo VRP Chile: en cada vuelta lee el archivo entero (desde la rama loop/activo), aplica su protocolo de la sección 2, ejecuta una sola tarea, anota la bitácora y commitea. No adoptes cambios en la réplica de producción (sección 1.1). Detente solo por las condiciones de la sección 1.5.

Antes de la primera vuelta: lee tasks/BLOQUE_ARRANQUE_S153.md y las entradas de la bitácora desde la vuelta 160. Verifica contra el remoto antes de creerle a nada (gh run view, gh api, gh pr view). Pide la hora al servidor antes de escribir cada entrada. Luego, en este orden:
1. PR #847 (G3 del diurno): comprueba si el agente aplicó el arreglo de borde (sólo con listas de 100 píxeles) en comparar() y rehízo las uniones de W2, F/K V1 y V2a; si no, aplícalo tú con tests. Segunda vuelta del verificador limpio, revisa el diff y mergea con el CI verde.
2. 1.23: si el job Lascar-2a (run 39066031570) terminó bajo el umbral del README (l. 464), despacha los otros 23 medios jobs desde el MISMO tag s151-1.23-probe; al terminar, evalúa en local con todos los artefactos juntos y pasa verificador limpio.
3. F/K V2b (run 39033530622): cuenta cobertura; si queda despareja, repite y une (D-13). Evalúa V2 con evaluar_fk.py (--raiz V2a unida y V2b, --ruido-de v1.json de experiments/_s151_prereg_fk_11/resultado_v1/), luego --combinar, y verificador limpio. Informa también la media de d de P3 con su intervalo y la prueba de signos.
4. Diurno: cuando W5b arranque, despacha W6a (10-01 a 10-07) y luego W6b (10-08 a 10-14) con --ref s151-diurno-codigo, nunca main. Con #847 mergeado y W2 a W6 completas y parejas, evalúa con evaluar_diurno.py y verificador limpio.
5. Tarea 1.23 bis: identificar el commit de la deriva de los 8 records MODIS.
Esperan mi decisión: cadencia del cron externo, reproceso de los 29 records, sello de la sonda 1.2 (#776), cronología OVDAS para la 1.11, Mirova-v1#23 punto 4.
Si la sesión no alcanza: commitea la bitácora en loop/activo, deja escrito qué run quedó sin evaluar, y para.
```
