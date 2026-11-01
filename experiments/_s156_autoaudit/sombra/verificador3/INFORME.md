# Verificador 3 (contexto limpio): vigilancia de la sombra de K

Worktree `D:\vrp-trabajo\worktrees\s156-sombra-verif` (detached en 0b8d4bc52), sin tocar: las corridas que escriben se
hicieron con el runner (salida desviada) o en una copia parcial sacada con `git archive 0b8d4bc52 scripts tests frontend
.github pipeline volcanoes.yaml` y los dos logs del A/B, en `D:\vrp-trabajo\temporales\s156_sombra\verificador3\copia\`
(7 MB). La única corrida en el worktree fue pytest con `PYTHONDONTWRITEBYTECODE=1` y `-p no:cacheprovider`
(`git status --short` vacío después). Referencia: `D:\vrp-trabajo\temporales\s156_sombra\ref\` (sin tocar). Scripts en
`D:\vrp-trabajo\temporales\s156_sombra\verificador3\scripts\`, salidas en la misma carpeta. Python 3.12 local; revisé
aparte que el script, la prueba y el runner no usan f-strings que rompan en 3.11 (tokenizador, 0 casos) y que la
cadena de imports sólo necesita `yaml` fuera de la biblioteca estándar (lo que instala el workflow).

Primero leí el código y armé mi lista de caminos de falla; los informes de los verificadores 1 y 2 los leí al final,
para marcar qué es nuevo.

## Veredicto por afirmación

| | Afirmación | Veredicto | Evidencia |
|---|---|---|---|
| D1 | Cada hallazgo del verificador 2 quedó arreglado y nada se rompió | **CONFIRMADO, con brechas de prueba** | Ítem por ítem abajo. Todos hacen lo que dicen. Ninguno rompió otra cosa: 350 pruebas de los 24 archivos que leen workflows, la regla o la vigilancia pasan en el worktree (5 saltadas), y la corrida real da lo mismo que el autor. Pero dos arreglos no quedaron amarrados por prueba (corte al segundo, N3 y N5 sobreviven) y el arreglo de frescura por volcán deja abierta la misma clase de falla por sensor (hallazgo 1) |
| D2 | Es correcto usar la etiqueta original en (i) y (iii) y D-9 SN en reversión y persistencia | **PARCIAL** | Es coherente con cómo se midieron las cotas (sección 6 de `v1.log` decide con la etiqueta original; `evaluar_fk.py::suma_errores` cuenta `lab == "pos"` sin D-9). SN en la reversión es vacío: una pasada protegida (1 MW o más) nunca es mínima por construcción (`aplicar_regla_minimas` exige que TODAS sus alertas sean de 0,05 o menos). Pero (i) queda en tensión con la regla y con D-9, y no es teórico: ver hallazgo 2 (en el A/B, 9 de las 16 Muy Bajo que K perdió en V1 eran mínimas; en datos reales el único disparo de (i) habría sido una pasada de 0,01 MW que MIROVA llama NONE) |
| D3 | La corrida real da VERDE, con PCC VIIRS 750 2026-10-10 05:54 en el retrospectivo, igual al JSON del autor | **CONFIRMADO** | `correr_sombra.py` (el runner del autor, que ahora sí corre) → `d3\stdout.txt`, `d3\sombra_latest.json`. `scripts\cmp_d3.py` contra `sombra_latest_2026-10-19_lectura_decidida.json` → `d3\cmp.txt`: 18 campos de primer nivel en los dos, una sola diferencia en todo el árbol, `generated_utc`. VERDE, avisos vacíos, 250 pasadas de alerta (146 con sombra), retrospectivo 247 pasadas, 61 protegidas vistas, 1 que la sombra publica y K calla (PCC VIIRS750 2026-10-10 05:54, 1,19 MW), negativos V375 0 de 9 desde la adopción |
| D4 | `mutar_vigilancia.py` da 37 de 37 atrapadas por fallo de prueba | **CONFIRMADO (las 37); cobertura PARCIAL** | En la copia → `d4_autor.txt`: 37 de 37. Reclasificadas por tipo de falla con mi `scripts\mutar3.py` (JUnit XML, «atrapada» sólo si al menos una prueba falla por `AssertionError`) → `d4_autor_clasificado.txt`: 36 por aserción y 1 (`cargar_insumos_sin_original`) por `KeyError` dentro de la propia prueba al leer `rec_k["lab_original"]`. Esa no es caída del script (en producción el script seguiría y (iii) quedaría ciego en silencio, porque usa `r.get(...)`); la prueba la detecta legítimamente. Mis 18 nuevas → `d4_nuevas.txt`: 5 atrapadas por aserción, 1 sólo por excepción, **12 sobreviven** (detalle abajo). El archivo quedó restaurado byte a byte en la copia (`diff` contra `git show 0b8d4bc52:...` vacío) |
| D5 | El workflow haría lo esperado en (a) a (g) | **CONFIRMADO, con tres matices** | Simulación con los `run:` extraídos del YAML y ejecutados como Actions (`bash --noprofile --norc -eo pipefail`), con `gh`, `git`, `curl` y `sleep` falsos: `wf\correr_job.sh` → `d5_simulacion.txt`, logs en `wf\sandbox_*\`. El `--jq` con `env.PREFIJO` lo probé con el `gh` real (2.92.0) contra el repo, sólo lectura: devuelve el número cuando el prefijo calza y vacío cuando no; sin la variable cae con `startswith(null)`, o sea que `env` sí se lee. Casos abajo |

### D1, ítem por ítem

| Ítem | Hace lo que dice | Rompió algo / quedó suelto |
|---|---|---|
| Frescura por volcán | Sí. `avisos_sombra` recorre `aa.VOLS` (11 Tier A, los mismos de la matriz de `experimental-diario.yml`) y avisa por volcán sin records o con más de 3 días | Mi N7 (recorrer sólo los volcanes vistos) la atrapa una aserción. **Queda la misma clase por sensor**: sin MODIS en la sombra, 0 avisos y 13 protegidas MODIS de la ventana quedan sin mirar (`scripts\sensor_muerto.py` → `sensor_muerto.txt`). Hallazgo 1 |
| Issue con `if: always()` | Sí. Escenario (e): cinco intentos de push fallidos, el paso de commit sale con 1 y el issue de reversión igual se crea | El cuerpo del issue apunta a `data/audit_continuous/sombra_latest.json`, que en ese caso no llegó al remoto (baja) |
| Dedupe por prefijo exacto con `env.PREFIJO` y comentario | Sí. Escenarios (b), (c), (d2): crea si no hay, comenta en el número correcto si hay | Un issue abierto a mano cuyo título empiece exactamente con `Sombra de K: candidata a reversion` (sin tilde) se sigue tragando las reversiones como comentario (escenario m). Mucho menos probable que con la búsqueda por palabras; con tilde ya no calza. Baja |
| Cron de respaldo | Sí, `40 23 * * *`, y la prueba amarra el nombre del workflow de la sombra y la existencia del `schedule` | Con `experimental-diario` caído, el aviso llega recién al cuarto día (tolerancia de 3); coherente con que `run_pipeline.py` reprocesa por defecto los últimos 7 días, así que un día fallido se recupera solo |
| Runner 24.04 | Sí | Nada |
| (i) y (iii) con la etiqueta original; reversión y persistencia con D-9 SN | Sí, en código: `lab_original` para (iii), las mínimas entran a (i) y salen de (ii) | Conceptualmente ver D2 y hallazgo 2. En la corrida real la etiqueta SN de producción (`lab`) difiere de la original en 43 de 3.672 records y **ningún disparador la usa**: el segundo `etiquetar` es cómputo muerto (informativo) |
| Corte al segundo | Sí: `leer_adopcion` devuelve `2026-10-18 09:57:30`, `instante_utc` lleva segundos y (iii) compara con `_instante` | **Sin prueba que lo amarre por donde importa**: N3 (`instante_utc` truncado a `:00`) y N5 ((iii) desde la medianoche del día de adopción) sobreviven. Hoy no cambia nada (el corte es pasado) |
| Prueba del cableado de `cargar_insumos` | Sí: atrapa invertir el orden (mi N29), quitar la copia y cargar la sombra desde producción | Con datos reales el cableado produce etiquetas distintas (43 de 3.672), así que no es un doble que pasa por casualidad |

### D4, mutaciones nuevas (18)

| Mutación | Resultado | Qué significa |
|---|---|---|
| N1 umbral de mínima 0,04 en vez de 0,05 | sobrevive | ninguna prueba usa una mínima de 0,05 exacto |
| N2 pasadas armadas con las filas SN (volver al código anterior) | atrapada | |
| N3 `instante_utc` sin segundos | sobrevive | corte al segundo no amarrado en `pasadas_de_alerta` |
| N5 negativos desde la medianoche del día de adopción | sobrevive | corte al segundo no amarrado en (iii) |
| N6 frescura con `>=` | atrapada | |
| N7 frescura sólo de los volcanes vistos | atrapada | |
| N9 (i) sin exigir record de la sombra | sobrevive | el denominador de (i) puede crecer con pasadas que la sombra no miró |
| N12 retrospectivo de persistencia con mínimas | sobrevive | informativo (no dispara) |
| N18 cualquier aviso convierte en VIGILANCIA_CIEGA, también una REVERSION | sobrevive | nada impide que un aviso tape una reversión |
| N19 `hoy` = ayer | sobrevive | baja |
| N22 tolerancia del pareo 61 s en vez de 120 | sobrevive | las pruebas usan 60 s y 10 min, nunca 90 |
| N23 sospecha A119 si ALGUNA protegida es OCR | sobrevive | baja (antes del hito; no afecta lo prospectivo) |
| N24 la persistencia ya no lleva a INVESTIGAR | **sobrevive** | la prueba de persistencia mira la lista, nunca el veredicto |
| N25 pasada justo en el segundo de adopción en los dos lados | sobrevive | borde sin efecto práctico |
| N26 sin `continue` tras volcán sin records | sólo excepción (`ValueError`) | en producción también cae, abre «el script falló»: no es silenciosa |
| N27 sin adopción todo es prospectivo | sobrevive | equivalente en la práctica (`evaluar` corta antes con VIGILANCIA_CIEGA) |
| N28 Wilson con z = 1,64 | atrapada | |
| N29 copiar `lab_original` después de etiquetar con SN | atrapada | |

Las del workflow (cambiar `startswith` por `contains`, `OUTCOME` desde `.conclusion`, sacar `continue-on-error`) no
las ve ninguna prueba: `test_el_workflow_escucha_al_workflow_de_la_sombra` sólo mira el nombre, el `schedule` y el
`if` del paso del issue. Las revisé con la simulación de D5, no con mutación.

### D5, escenarios simulados

| Caso | Resultado |
|---|---|
| (a) VERDE | push 1 intento, «sin issue» |
| (b) REVERSION sin issue abierto | `gh issue create` con título `Sombra de K: candidata a reversion: 2026-10-19` y el detalle de la pasada |
| (c) REVERSION con issue de esa clase abierto (#41) | `gh issue comment 41` con «Corrida del ...» y el detalle; un issue ajeno abierto no interfiere |
| (d) el script cae | commit saltado, issue «Vigilancia de la sombra de K: el script fallo» con el enlace al run; con uno abierto (d2), comenta |
| (e) push falla 5 veces | paso de commit sale con 1 tras 5 intentos (con `sleep` falso); el issue de reversión igual se crea |
| (f) dos corridas el mismo día | la segunda comenta el issue que abrió la primera; el historial suma dos líneas con la misma fecha (nadie más lee `sombra_history.jsonl`, `grep` en el repo) |
| (g) `experimental-diario` termina en falla | `workflow_run` con `types: [completed]` y sin filtro de conclusión: la vigilancia corre igual; un día perdido lo recupera la siguiente corrida de la sombra (7 días hacia atrás por defecto) |
| (k) `curl` de la referencia falla | vigilancia `skipped`, se abre «el script fallo» (el texto dice «no terminó», algo impreciso pero visible) |
| (l) `gh issue list` falla | con `-e` el paso del issue sale con 1 y no hay issue: el job queda rojo (falla ruidosa por la vía de GitHub, no por issue) |
| (j) avisos con comillas, `$`, acentos y `%s` | el cuerpo llega intacto; `printf` usa formatos fijos y el contenido va como argumento |

Comillas, `set -e` y `pipefail`: sin fallas encontradas. Permisos (`contents: write`, `issues: write`) alcanzan para
push, crear y comentar. Si fallara el `checkout`, `gh` no tendría repo de contexto (no se fija `GH_REPO`): baja.

## Hallazgos propios, por gravedad

1. **(Media alta) Tres maneras de quedar ciega que siguen dando VERDE.** El docstring dice «Una vigilancia ciega no
   da error: da VERDE. Por eso cada caso tiene su veredicto», y el arreglo por volcán cubrió una. Medido con datos
   reales (`scripts\ciega.py` → `ciega\salida.txt`, `scripts\sensor_muerto.py` → `sensor_muerto.txt`):
   - **referencia muerta**: con la referencia cortada al 2026-09-30 (scraper caído 19 días) da VERDE sin avisos; con
     los CSV vacíos (sólo encabezados, un `curl` con 200 y archivo truncado) da VERDE con 0 pasadas. El auto-audit del
     lunes tiene `gt_stale_dias` (`auto_audit_weekly.py:805`), pero es semanal y la regla pide avisar el mismo día;
   - **producción sin records de K**: con producción vacía, o muerta en los 11 volcanes desde el 2026-10-05, da VERDE.
     Como `prod` se filtra por `regimen.codigo_sha`, un cambio en la marca de régimen deja a producción vacía y la
     vigilancia verde para siempre. El NRT tiene otros vigilantes; este filtro no;
   - **un sensor de la sombra muerto**: la frescura es por volcán, no por sensor. Sin MODIS en la sombra no hay aviso
     y las 13 protegidas MODIS de la ventana quedan con `sombra_pub = None`, que nunca dispara. MODIS es el sensor que
     depende de pyhdf en el runner, y es donde están hoy las protegidas de Chillán.
   Arreglo barato: avisar si la referencia no tiene filas en los últimos 2 días, si producción no tiene records de K
   recientes por volcán, y medir la frescura de la sombra por (volcán, sensor).

2. **(Media) El disparador (i) con la etiqueta original dispara sobre lo que D-9 dice que MIROVA no vio.** La línea SE
   de `v1.json` (`reglas_d9.SE.suma["K|VIIRS375|A"]` = 28 contra 37 de la original) y los negativos que SE no toca
   (21) dan que **K perdió 7 Muy Bajo no mínimas y 9 mínimas** de sus 16 en V1. Y con los datos reales, si la vigilancia
   hubiera empezado el 2026-10-02 (`scripts\retro_como_prospectivo.py` → `retro_como_prospectivo.txt`), el único
   disparo de (i) en 17 días habría sido **Llaima VIIRS 375, 2026-10-03 07:06, 0,01 MW, una mínima, con n = 1**
   (Wilson 1 de 1 = [0,2065; 1] sobre la cota 0,1298). Con SN, nada dispara; de las 6 pérdidas de V375, 3 son mínimas
   (0,01, 0,04 y 0,05 MW). La regla habla de «alertas Muy Bajo que MIROVA publica», y D-9 dice que esas pasadas son
   NONE en el banner. Usar la original es coherente con la cota, pero hay una versión coherente con D-9 que el A/B ya
   midió: contar con SE (sin mínimas) y tomar la cota de SE (7 pérdidas; el denominador, 194 menos las mínimas del
   brazo K, lo deduzco en unas 161 si las 33 de `cambian` son todas de ese brazo: SIN VERIFICAR). Es decisión de
   Nicolás, junto con lo de n = 1 que el autor ya dejó para decidir.

3. **(Media) El veredicto es pegajoso y no se apaga.** La reversión se acumula desde la adopción: una pasada del
   2026-10-20 sigue dando REVERSION_CANDIDATA el 2026-11-15 y el 2027-02-14 (`acumulativo.txt`). No hay cómo marcar un
   caso como revisado: si la cabecera no confirma y Nicolás cierra el issue, la corrida siguiente abre otro, y con dos
   corridas al día comenta dos veces diarias durante 120 días. Mientras tanto la reversión tapa los veredictos
   INVESTIGAR y VIGILANCIA_CIEGA (sus líneas quedan enterradas en el comentario). Además, **la duración cumplida no
   apaga nada**: con 31 protegidas vistas, o en el día 134, una pérdida nueva sigue dando REVERSION_CANDIDATA y el
   issue sigue diciendo que la regla «pre-autoriza revertir» (`duracion_no_apaga.txt`), cuando la regla limita la
   vigilancia a 29 protegidas o 120 días.

4. **(Media baja) Brechas de prueba en lo que decide.** 12 de mis 18 mutaciones sobreviven (tabla de D4). Las que
   tocan el veredicto: N24 (la persistencia deja de llevar a INVESTIGAR y ninguna prueba lo nota) y N18 (un aviso puede
   tapar una reversión). Las que tocan los arreglos de esta vuelta: N3 y N5 (corte al segundo). Y N22 (tolerancia del
   pareo) y N9 (denominador de (i)).

5. **(Baja) El issue retrospectivo de PCC sigue sin abrirse.** La marca dice que una pérdida retrospectiva va a
   investigación «con un issue que se abre a mano» y que PCC es el primer caso; `gh issue list --state all` no trae
   ninguno con «sombra», «PCC» o «reversi» (consulta de sólo lectura). Si se abre con un título que empiece igual que
   el automático, ver D1 (dedupe).

6. **(Baja) Detalles del workflow.** Con `gh` caído el paso del issue sale con 1 y no hay issue (sólo job rojo); sin
   `GH_REPO`, un `checkout` fallido deja a `gh` sin repo; en el caso de push fallido el issue apunta a un archivo que
   no llegó al remoto.

## ¿Algo debería impedir mergear?

Nada cambia el veredicto de hoy, y los arreglos del verificador 2 están bien hechos. Pero el hallazgo 1 es de la misma
clase que el que el verificador 2 pidió arreglar antes del merge (un volcán ciego daba VERDE): un sensor de la sombra
ciego, una referencia muerta o una producción sin records de K también dan VERDE. Recomiendo que la frescura por
sensor y los dos avisos (referencia y producción) entren antes del merge; son pocas líneas y cada uno con su prueba.
Los hallazgos 2 y 3 son decisiones de Nicolás que conviene tomar antes de que llegue el primer issue: el 2 casi seguro
produce un INVESTIGAR sobre una mínima en las primeras semanas, y el 3 hace que un caso no confirmado no se pueda
cerrar.

## Lo que no verifiqué

- Actions de verdad: simulé los `run:` con bash y `gh` falso; la semántica de `outcome`, `continue-on-error` y
  `always()` la emulé según la documentación, no la corrí.
- El denominador exacto de la cota SE del hallazgo 2.
- La probabilidad de falsa alarma de (i) en 120 días (el 57 % es del verificador 2; no lo recalculé).
