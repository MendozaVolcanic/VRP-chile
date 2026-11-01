# Bloque de arranque S165 (cierre de S164, coordinadora, 2026-10-26 12:38 a 22:55 UTC)

Escrito el 2026-10-26 a las 22:55 UTC (servidor) sobre `loop/activo`; el commit de este cierre se anota en la bitácora
(`tasks/LOOP_OBJETIVOS.md` §6). **El estado se fijó con trabajo en curso**: W2 del A/B diurno corre en GitHub y la
sesión `modd-fase3` está abierta (ver §a, filas «en vuelo»). El bloque anterior (`tasks/BLOQUE_ARRANQUE_S164.md`) queda
como historia. El detalle de cada paso está en la bitácora, vueltas 1 a 23 de S164.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| PR mergeados en S164 | **#907** (cableado de la vía «código MIROVA» V750, flag APAGADO; tag `pre-s164-merge-907`), **#914** (placebos D-44, tarea 1.35, causa de huecos), **#916** (pre-registro diurno sellado), **#917** (adenda 1 del diurno) | `git log origin/main`; CI verde en cada uno; bitácora vueltas 3, 5, 17, 22 |
| Integrado a `loop/activo` | rama de `loop-viirs375` (`461a77be4` y `e9dac40d4`: V375-B2, V375-C, O2-375, adenda 1 de V375-E con PD1) | bitácora vueltas 4 y 5 |
| `loop/activo` a `main` | **pendiente**: ~85 commits desde #908 (bitácora de S163 y S164, evidencia de V375 de 64 MB). Al integrar, el `evaluar.py` de V375 gana el add/add con #911 (aviso de la hija). Con merge commit, no squash | `git log origin/main..origin/loop/activo` |
| Censo MOD-D | **terminado**: 5.465 de 5.465 pasadas (t1 40336655402, t2 40344051900, t3 40349358358), DECIDE NICOLÁS verificado (Fable alto). **Nicolás lo aprobó como CANDIDATO** y la fase 3 (vía en `pipeline/` con la regla de MATLAB, flag apagado) | rama `claude/s162-modis-2-0dd578` `9ea9a1786`; bitácora vueltas 13, 14, 16 |
| **En vuelo: fase 3 de MOD-D** | sesión `modd-fase3` (`local_1860a1d4-d339-4319-b89f-7ebab9735b7f`, worktree `.claude/worktrees/funny-kepler-68f0ef`); arrancó en el segundo intento; su primer paso es confirmar el sí de Nicolás en su propio chat; recibió la parada por disco | traspaso en `tasks/LOOP_MODIS.md` §b2 de `claude/s162-modis-2-0dd578` `e15e50153` |
| A/B diurno sobre K (D-10) | **SELLADO por Nicolás** («Sello el pre-registro diurno 68687d2d4 con las seis recomendaciones (e-ii en el caso e)»), tag `s163-diurno-k-sellado`. Tag del código `s163-diurno-k-codigo` **sobre el commit sellado** (no sobre `main`: #907 y #914 cambiaron 3 de los 29 archivos sellados). Adenda 1 (días con hueco de NASA, condición (b')) fijada en `867cb1ec` antes de los datos de W2 a W6 | #916, #917; bitácora vueltas 17, 20, 22 |
| W1 del diurno | **terminada** (run 40364164845): control 31 min, diurno 88 min, cobertura nocturna pareja; con la adenda, veredicto informativo DECIDE NICOLÁS CON M4 | rama `s151-ab-diurno/40364164845` |
| **En vuelo: W2 del diurno** | run **40379112237** (2026-06-13 a 06-30, 11 Tier A, 22 jobs, `max-parallel: 3`); a las 22:50 UTC, 12 de 22 jobs en verde | `gh run view 40379112237` |
| W3 a W6 | **pendientes**, una por despacho, enteras (regla del §8: 88 × 1,45 × 1,3 = 166 min ≤ 300), cada una cuando la anterior termine | comandos en §f |
| Humo y tandas de MOD-D | despachados y aceptados (humo 40333783937, tres tandas) | bitácora vueltas 6, 7, 9, 11 |
| D-39 (Mirova-v1#26) | **listo para mergear, sin ejecutar**: 0 filas perdidas en las dos direcciones (verificado también por la coordinadora), 2.351 filas a reponer, PR en `dd606a65a` con CI verde. El **clasificador de permisos niega `gh workflow disable`** aun con el permiso de Nicolás en el chat | `PASOS_PARA_NICOLAS.md` en `claude/s163-d39-mirova-v1-710f72` `c10cad031`; bitácora vueltas 2 y 18 |
| PD1 (caja de VIIRS 375) | decidida con D-48: C13 en todos los volcanes | bitácora vuelta 4 |
| V375-E | espera llevar la vía de #907 a 375 (`process_viirs.py`, A45; sesión nueva) | traspaso `VIIRS375_via_375_traspaso.md` en la carpeta compartida de S162 |
| V750-A (medidor) | detenido por disco: 58 de 62 atrapadas por aserción en la corrida principal; faltan M34 y M36 con `--solo M34,M36 --hilos 1` | `tasks/LOOP_VIIRS750.md` de `claude/s162-viirs750-2-918174` |
| V750-B | despacho el 2026-11-03: `objetivos_v750b.json` se genera con `--hasta 2026-11-02` y se commitea con su sha256 ese día (ensayado hoy: 5.781 objetivos, 279 alertas, 103 protegidas) | bitácora vuelta 4 (mensaje de `loop-viirs750-2`) |
| Auto-audit | #864 cerrado apuntando a **#915** (2026-10-26): recall MODIS 62,5 %, VIIRS 750 74 %, Chillán bajo 0,7× en los tres sensores, 6 protegidas sin publicar (3 de Chillán MODIS) | bitácora vuelta 15 |
| Disco | C: 4,2 GB, D: 7,8 GB a las 22:50. **11 worktrees terminados en la papelera** (sin vaciar), 4 sesiones archivadas. Parada por disco vigente para las sesiones que escriben mucho | bitácora vueltas 21 y 23 |

## b. Decisiones que espera el dueño

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Vaciar la papelera de Windows (11 worktrees ya integrados, varios GB) | vaciar; no | **vaciar**: C: está en 4,2 GB, cerca de la parada |
| 2 | D-39: cómo ejecutar los pasos 2 a 6 en Mirova-v1 | correrlos tú con `PASOS_PARA_NICOLAS.md`; agregar una regla de permiso para `gh workflow` con `/permissions` desde un terminal `claude` interactivo; esperar | **correrlos tú** (es media hora y el plan está probado); si no, la regla de permiso |
| 3 | Confirmar en el chat de `modd-fase3` el sí a la fase 3 | confirmar; no | **confirmar** (ya lo aprobaste aquí; la sesión lo pide por la regla S157) |
| 4 | Abrir la sesión que lleve la vía de #907 a VIIRS 375 (V375-E) | ahora; después de vaciar la papelera | **después de vaciar la papelera** (un worktree pide 5,4 GB) |
| 5 | Mazos del congreso, revista y licencia del paper (de S163) | ver `tasks/BLOQUE_ARRANQUE_S164.md` §b, filas 3 a 5 | sin cambio |
| 6 | Correo a Coppola | enviar; esperar | **esperar** (decisión vigente) |

## c. Lo aprendido

Reglas generales del workspace (memoria `feedback_s164_lecciones.md`):
- **El clasificador de permisos del modo auto no acepta un permiso dado en el chat** para acciones que interfieren con
  trabajo de otro repositorio (`gh workflow disable`): negó dos veces. No se salta; el dueño corre los comandos o agrega
  una regla de permiso. Preparar siempre el bloque de comandos para que lo pegue.
- **Un repack automático de git en un repositorio grande ocupa casi el doble mientras corre** (aquí 9,7 GB de paquetes, uno
  nuevo de 6,4 GB): con el disco justo deja la máquina bajo la parada sin que aparezca ningún archivo grande nuevo fuera de
  `.git`. Mirar `.git/objects/pack` antes de culpar a otra cosa.
- **Un worktree de una sesión abierta, aunque terminada, no se puede mover** («usado por otro proceso»): hay que archivar la
  sesión primero.
- **Las horas de la bitácora se toman de `date -u` o del commit, nunca a ojo**: cuatro entradas salieron con 10 a 30 min de
  error.
- **Texto con barras invertidas va con Edit, no con un heredoc de Python**: `\v` se volvió tabulador vertical dos veces.
- **Los verificadores matan procesos de otras sesiones** si los terminan por nombre o línea de comandos (pasó dos veces
  hoy): sólo por el PID que lanzaron.

Del proyecto (en la bitácora; rutear al catálogo cuando `loop/activo` entre a `main`):
- **Un pre-registro sellado sobre un commit viejo no se taggea en `main` si `main` cambió archivos sellados**: el tag del
  código va sobre el commit sellado, y se declara como desviación operativa antes de ver datos.
- **Una condición de exclusión tiene que medir si el dato existió, no lo que la referencia listó**: (b) dependía de lo que
  MIROVA listó de noche; (b') pregunta si el control tiene records de esa plataforma.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO**: el scraper Mirova-v1 perdió 241 filas el 2026-10-24 (dos protegidas); el arreglo está listo en #26.
- **CONFIRMADO**: Suomi NPP no tiene gránulos en NASA el 10, 11 y 12 de marzo de 2026 (CMR, VNP02IMG y VNP02MOD).
- **CONFIRMADO**: #915 marca tres alertas protegidas MODIS de Chillán sin publicar (12, 15 y 25 de octubre).
- **SOSPECHA**: esas pérdidas de MODIS en Chillán son el síntoma que ataca MOD-D (20 protegidas que pasan de K < 1 a PM
  ≥ 1 MW en el censo); no medido sobre esas tres pasadas.
- **SOSPECHA**: la caída de C: de 15 a 4,7 GB entre 13 y 16 UTC fue el repack de git; no se midió cuándo empezó.
- **SOSPECHA**: M34 del medidor de V750-A cae por memoria (había 3,3 GB de RAM libre).
- **SIN DATO**: que MIROVA use el `.m` de VIIRS 750 para el fondo de MODIS y de VIIRS 375.

## e. Lo que ya está cerrado y no hay que rehacer

- Censo MOD-D (no re-correr las tandas); veredicto verificado y aprobado como CANDIDATO.
- Pre-registro diurno sellado y su adenda 1; W1 corrida y revisada; la regla operativa (W2 a W6 enteras).
- #907, #914, #916, #917 mergeados; PD1 decidida; #864 cerrado.
- La verificación de D-39 (0 filas perdidas): sólo falta ejecutar.

## f. Prompt para la próxima sesión

```text
Retoma VRP Chile como sesión coordinadora S165 (relevo de S164, cierre del 2026-10-26 ~22:55 UTC). Antes de creerle a nada:

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (loop/activo, en el commit del cierre o más nuevo); hora del servidor con gh api -i repos/MendozaVolcanic/VRP-chile |
   grep -i date (A86); df -h /c /d (parada bajo 3 GB).
2. Lee CLAUDE.md del proyecto, tasks/BLOQUE_ARRANQUE_S165.md, tasks/LOOP_OBJETIVOS.md §6 (vueltas de S164) y
   docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md.
3. Mira las sesiones vivas con mcp__ccd_session_mgmt__list_sessions y avísales que la coordinadora ahora eres tú:
   modd-fase3 local_1860a1d4-d339-4319-b89f-7ebab9735b7f, loop-modis-2 local_0af7e1d8-7bde-4a4d-b8a3-6cf256a36c67,
   loop-viirs750-2 local_94f4be0d-2b32-4570-b711-3a6f14cc8a0a, d39-mirova-v1 local_57b44db2-3006-49fb-a00c-0228be793b29,
   diurno-k-prereg local_bd4d68e7-100e-412a-9456-3f89c7beb7e4. Si el disco ya tiene aire, levanta la parada.

Trabajo, en orden:
- A/B diurno: cuando termine W2 (run 40379112237), lee su cobertura.txt y despacha la siguiente, una a la vez:
  V='["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]'
  gh workflow run reproc-s151-ab-diurno.yml --ref s163-diurno-k-codigo -f preregistro_aprobado=si -f start=<inicio> -f end=<fin>
    -f vols="$V" -f brazos='["_s154_ab_diurno_k_control","_s154_ab_diurno_k_on"]' -f control=_s154_ab_diurno_k_control
  W3 2026-07-20 a 07-31; W4 08-13 a 08-31; W5 09-01 a 09-20; W6 10-01 a 10-14. Pasa siempre las entradas de K.
  Al terminar W6, diurno-k-prereg lee con dias_excluidos_nasa.py y evaluar_con_exclusion.py (--opcion-e e-ii) desde un
  git archive del commit sellado, con verificador limpio; el veredicto va a Nicolás.
- Fase 3 de MOD-D: recibir el PR en borrador de modd-fase3 y mergearlo sólo con producción bit a bit igual con el flag
  apagado (y control que cambia), suite con árbol quieto en 0 fallas, CI verde y verificador limpio de otro modelo; tag
  defensivo antes. Encender el flag no está aprobado.
- D-39: si Nicolás corre los pasos de PASOS_PARA_NICOLAS.md, verificar con s20_verificar_post_merge.py.
- V375-E: abrir la sesión que lleve la vía de #907 a VIIRS 375 cuando haya disco (traspaso VIIRS375_via_375_traspaso.md).
- V750-A: que loop-viirs750-2 retome M34 y M36 con --hilos 1 cuando haya disco.
- 2026-11-03: despacho de V750-B (objetivos generados con --hasta 2026-11-02, commiteados con sha256, tag, jobs) y la
  consulta C-06 del cese de Suomi NPP contra CMR.
- Integrar loop/activo a main con merge commit (no squash); el evaluar.py de V375 gana el add/add con #911.
- Recordar a Nicolás las decisiones de §b.
- Correr como loop propio con la skill loop en modo dinámico sobre tasks/LOOP_OBJETIVOS.md; anotar cada vuelta con la hora
  de date -u y commitear en loop/activo.

Reglas duras: nada en pipeline/, data/ ni frontend/ sin tag y el sí explícito de Nicolás (A45); sólo EARTHDATA_TOKEN
(A71); despachos uno a la vez dentro del cupo de 20 jobs (NRT usa 11), desde tags; verificador limpio de otro modelo
antes de aceptar un resultado; git add por archivo; nunca git stash; las ramas de las hijas tienen que estar en el
remoto; disco justo (parada bajo 3 GB); Claude no borra de forma permanente (papelera de Windows); el clasificador niega
gh workflow disable en Mirova-v1 aunque Nicolás lo permita en el chat: no saltarlo; texto con barras invertidas con Edit,
no con heredoc; español de Chile sin voseo ni guiones largos; rutas absolutas. Si la sesión no alcanza: commitea, anota
en la bitácora qué quedó corriendo y cierra con /cierre.
```
