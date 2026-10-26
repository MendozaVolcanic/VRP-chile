# Verificador 2 con contexto limpio: vigilancia de la sombra de K (commit 1eb2e6b75, PR #863)

Worktree de sólo lectura `D:\vrp-trabajo\worktrees\s156-sombra-verif` (HEAD 1eb2e6b75; `git status --short` vacío al
terminar). Referencia de MIROVA del 2026-10-19 en `D:\vrp-trabajo\temporales\s156_sombra\ref\` (sin tocar). Todos mis
scripts y salidas están en `D:\vrp-trabajo\temporales\s156_sombra\verificador2\`. Las mutaciones y las corridas que
escriben se hicieron en una copia sacada con `git archive 1eb2e6b75` a
`D:\vrp-trabajo\temporales\s156_sombra\verificador2\copia\` (488 MB, se puede borrar). Python 3.12 local; el CI usa
3.11 (ver C4).

Leí el informe del verificador anterior después de formar mi opinión; al final hay una sección que dice qué quedó
arreglado de lo suyo.

## Veredicto por afirmación

| | Afirmación | Veredicto | Evidencia (script y salida) |
|---|---|---|---|
| C1 | La marca del paso 9 describe lo que hace el código | **PARCIAL** | Coinciden: unidad = pasada (`clase_mirova.clave_pasada`, volcán, sensor y minuto); corte en `CAMBIO_DETECTOR_UTC` leído del JS; lo anterior no dispara y no suma a la duración (`disparadores`, l. 186 a 224); plazo de 120 días contado desde la adopción (`vence` 2027-02-15); todo en UTC (`fecha_utc` de la referencia tiene la forma `YYYY-MM-DD HH:MM:SS` en las 44.283 filas, sin `T`, `sonda_datos.py` → salida en consola, así que la comparación de cadenas con el corte es válida). **Contradicción**: la marca dice que «una pérdida retrospectiva va a investigación con issue». Ni el script ni el workflow lo hacen: con PCC en el retrospectivo el veredicto es VERDE y el workflow, en VERDE, imprime «sin issue» (`probar_workflow.out`, escenario `verde`). Además, al 2026-10-19 no hay ningún issue del caso: la búsqueda pública de issues del repo creados desde el 2026-10-15 con «sombra», «reversion», «Puyehue» o «PCC» da 0. **Borde**: el corte se trunca al minuto (`09:57`), así que una pasada entre 09:57:00 y 09:57:29 cuenta como posterior aunque la adopción fue a las 09:57:30; la prueba `test_lo_anterior_a_la_adopcion...` fija ese comportamiento (W a las 09:57 cuenta como posterior). Sin efecto práctico, pero la marca dice 09:57:30. **Lo que la marca no dice**: el texto original pide contar «cada semana» y el código evalúa cada día, con efecto en las falsas alarmas de (i) (ver hallazgo 3); y la cota de (iii) sale de la etiqueta original del A/B mientras la vigilancia etiqueta con SN (hallazgo 6) |
| C2 | VERDE, PCC en el retrospectivo, 0 vistas desde la adopción, 61 en el retrospectivo | **CONFIRMADO** | `correr.py` (envoltorio propio: `experiments/_s156_autoaudit/correr_sombra.py` ya no corre, ver hallazgo 9) → `out_runner/stdout.txt`: VERDE, retrospectivo 61 vistas, 1 que la sombra publica y K calla (PCC VIIRS750 2026-10-10 05:54, 1,19 MW), duración 0 de 29, 5 Muy Bajo retrospectivas. El JSON sale idéntico al del autor (`sombra_latest_2026-10-19_lectura_decidida.json`) salvo `generated_utc`. Instrumento propio que no importa `vigilancia_sombra`, `clase_mirova` ni `referencia_mirova_unificada` (lee los dos CSV con `csv`, normaliza nombres a mano, elevación solar con fórmula propia, pareo a ±120 s; del repo sólo usa el predicado del tablero de `banco_paridad`): `instrumento_propio.py` → `instrumento_propio.out`: retrospectivo 82 protegidas nocturnas, 61 con record de sombra, 1 que la sombra publica y K calla (la misma de PCC), 0 en que producción no tenga record; tramo posterior a la adopción: 0 protegidas. `muy_bajo_retro.out`: 3 Muy Bajo diferenciales en V375 y 2 en V750 = las 5 del script. La pasada de PCC: K la publica en VIIRS 375 (cúmulo 0,283 MW) y calla en VIIRS 750, la sombra publica 1,886 MW en VIIRS 750 (consulta directa a `cargar_nuestros`, en consola). El «0 desde la adopción» es trivial hoy: la sombra llega hasta el 2026-10-18 07:50 en los 11 volcanes, antes de la adopción |
| C3 | La cota de Muy Bajo sólo en V375 se sostiene en los logs; ¿problema con V2? | **CONFIRMADO** (con dos salvedades que van a hallazgos) | `v1.log` l. 89 y 91: C0 pierde 0 de 194, K 16 de 194; `v2.log` l. 147 y 148: C0 0 de 388, K 26 de 388. En los dos tramos la pérdida de K es la diferencial, así que usar V2 no tiene problema de definición. Y no cambia nada: Wilson superior de V1 = 0,1298, de V2 = 0,0964, el código toma la mayor (`muy_bajo_retro.out`, primera línea). En MODIS y VIIRS 750 C0 sí perdía (4 de 4, 10 de 30 en V1; 25 de 26, 22 de 75 en V2), así que no hay cota diferencial y la decisión de no disparar es correcta. En datos vivos el denominador es comparable al del A/B: la sombra publica 67 de 67 Muy Bajo de V375 con record en ambos (`muy_bajo_retro.out`). Salvedades: (a) la cota es de la etiqueta original y la vigilancia aplica SN (hallazgo 6); (b) con evaluación diaria acumulada por volcán, una sola pérdida temprana dispara (hallazgo 3) |
| C4 | El workflow hace lo que dice | **PARCIAL** | `probar_workflow.py` → `probar_workflow.out`: el YAML parsea con la clave `on` como texto; `workflow_run.workflows` = `Experimental diario (laboratorio congelado, 11 Tier A)`, idéntico al `name:` de `experimental-diario.yml`; `bash -n` del paso de issues da 0; con un `gh` falso los siete escenarios hacen lo esperado (falla del script → issue «el script fallo»; REVERSION_CANDIDATA → issue con el detalle; ya abierto → no duplica; INVESTIGAR y VIGILANCIA_CIEGA → su issue; VERDE → nada); el `printf` con `%`, barra invertida, comillas y `$HOME` en el detalle sale intacto. Corrida de `main` en la copia: escribe sólo `sombra_latest.json` y `sombra_history.jsonl` (`find -newer`, en consola), y esos dos no están en `.gitignore`. Python 3.11: ningún f-string exige 3.12 (`fstring_311.py`, con control positivo `ctrl_fs.py` que sí lo marca). Fallas encontradas: deduplicación por bolsa de palabras (hallazgo 4), el issue de reversión depende de que el commit haya funcionado (hallazgo 2), sin vigía si el disparador deja de existir (hallazgo 7), y `gh issue list` caído deja el paso en rojo sin issue (`gh_list_falla`, rc=1). Si `experimental-diario` termina en falla, la vigilancia corre igual (`types: [completed]`, sin filtro de conclusión). Si corre dos veces el mismo día, el grupo de concurrencia las pone en fila, la segunda hace checkout después del push de la primera y la deduplicación evita el segundo issue (latencia del índice de búsqueda: SIN VERIFICAR) |
| C5 | Las 25 pruebas atrapan lo que importa; 21 de 21 mutaciones del autor | **PARCIAL** | Las 21 del autor: **21 de 21 atrapadas por aserción, ninguna sólo por excepción** (`mutar_propio.py copia autor ...` → `mutar_autor_reclasif.out`; dos que mi clasificador no leyó las revisé a mano y son `AssertionError`). Mis 13 nuevas (`mutar_propio.py` → `mutar_propio.out`): **12 sobreviven** con las 25 pruebas en verde; sólo M13 cae por aserción. Efecto de las sobrevivientes sobre la corrida real (`mutar_real.py` → `mutar_real.out`): **M1 (parear sin mirar el sensor) borra el caso de PCC del retrospectivo**, porque K publicó la misma pasada en VIIRS 375; M5 (umbral de protegida en 0,5 MW) sube las vistas de 61 a 72; M9 (lat y lon cambiadas en el filtro diurno) baja las pasadas de 229 a 210; M10 (meter `ALERTA_SIN_GEOMETRIA_OCR` en la lectura A) las sube a 257; M2 (frescura de la sombra medida sobre producción) no cambia nada hoy, pero apaga el aviso de sombra detenida. M6 (cargar la sombra desde la carpeta de producción) sobrevive a las pruebas pero la atrapa en la corrida real el aviso de perfiles: VIGILANCIA_CIEGA con «3672 records de la sombra traen el perfil mirova_equivalent». La causa común: `cargar_insumos` y `_diurna_por_defecto` se reemplazan en todas las pruebas, y los casos sintéticos tienen siempre un solo sensor por volcán y fechas iguales en producción y sombra |
| C6 | `banco_paridad` (campo `perfil`, parámetro `data`) no cambia etiquetas ni resultados | **CONFIRMADO** | `c6_banco.py` → `c6_banco.out`: el `banco_paridad.py` de `origin/main` (aa2c03d70) contra el de 1eb2e6b75, mismos datos y referencia. Ventana 2026-09-18 a 2026-10-19: 3.698 records; 2026-06-01 a 2026-09-17: 12.697. En las dos, el único campo nuevo es `perfil`, 0 records distintos fuera de él, y 0 etiquetas o `pub` distintos con SN y con la regla original. `sha` y `sensor` ya estaban en `origin/main` (aparecen en la línea `-` del diff), así que en este PR sólo entran `perfil` y `data`. Las 19 suites que importan `banco_paridad`, `auto_audit_weekly` o `vigilancia_sombra`: 278 aprobadas, 7 omitidas (`tests_rel.out`, corridas en la copia con `.github`, `experiments`, `docs` y `latest_consolidado.csv`; antes de agregarlos fallaban por archivos ausentes, no por el cambio) |

## Hallazgos propios, por gravedad

1. **(Media alta) La sombra muerta en UN volcán no se detecta, y la vigilancia da VERDE.** `avisos_sombra` mira la
   última noche de la sombra sumando los 11 volcanes (`evaluar`, l. 301). Si el job de `experimental-diario` de un
   volcán falla (la matriz tiene `fail-fast: false`, los otros diez siguen empujando), las alertas de ese volcán
   quedan con `sombra_pub = None` y no cuentan para nada. `ciego_por_volcan.py` → `ciego_por_volcan.out`: Chillán sin
   sombra desde el 2026-10-05, el resto al día, protegida de 5 MW de Chillán que K no publica: **VERDE, sin avisos**
   (sólo aparece en `protegidas_sin_publicar_k` con «sin record», que no abre issue). Es exactamente la clase
   «vigilancia ciega que da VERDE» que el docstring dice evitar, y Chillán es el volcán en erupción. Arreglo chico: la
   frescura por volcán, con el mismo umbral de 3 días.
2. **(Media) Si el push falla, no se abre el issue de reversión.** El paso «Open issue» no tiene `if:`, así que hereda
   `success()`: si «Commit results» termina con `exit 1` tras los 5 intentos, el paso de issues no corre y una
   REVERSION_CANDIDATA queda sólo en un run rojo. El commit y el aviso no dependen uno del otro; el issue debería ir
   antes del commit o con `if: always()`. (Por lectura de la semántica de pasos de GitHub Actions; no lo corrí en
   Actions.)
3. **(Media) El disparador (i) salta con la primera pérdida de un volcán.** Con un solo pase, Wilson inferior de 1 de 1
   = 0,2065, por encima de la cota 0,1298. Lo comprobé con la función real: una Muy Bajo de V375 que la sombra publica
   y K calla, primera del volcán desde la adopción → **INVESTIGAR**; con 1 de 5 → VERDE; control 0 de 4 → VERDE
   (`un_pase_dispara.py` → `un_pase_dispara.out`). El nulo medido por simulación (`sim_falsa_alarma_i.py` → `sim_falsa_alarma_i.out`, frecuencia
   de Muy Bajo por volcán tomada del retrospectivo, evaluación diaria acumulada, 2.000 repeticiones): si K pierde
   exactamente lo mismo que en el A/B (16 de 194), **(i) dispara en algún volcán antes de 120 días con probabilidad
   0,57**; con la tasa del retrospectivo (3 de 67), 0,31. Control: con tasa 0 el inferior de Wilson es 0 y no dispara
   nunca. El disparador sigue la letra de la regla, pero la letra pensada para «cada semana» y por volcán, con una cota
   agregada, mide sobre todo ruido de n chico. No revierte nada (es investigación), pero el primer issue llegará casi
   seguro y enseñará a ignorarlos. Para (iii) el mismo nulo da 0,046 con la tasa SN del retrospectivo
   (`sim_falsa_alarma_iii.out`): ahí no hay problema. Sugerencia: un n mínimo por volcán antes de evaluar (i), dicho en
   la marca.
4. **(Media) La deduplicación de issues es por bolsa de palabras, no por título.** Medido contra la búsqueda pública
   de GitHub (la que usa `gh issue list --search`): `in:title "corrida fallida reproc"` (orden cambiado) y
   `in:title "Reproc: colgada"` (palabras no contiguas) encuentran el #824 «Reproc: corrida fallida o colgada»; las
   tildes se ignoran («dia» encuentra «día»). Los cuatro títulos automáticos no se pisan entre sí, pero cualquier issue
   abierto a mano con las palabras «sombra», «K» e «investigar» (justo el que la marca pide abrir para la pérdida
   retrospectiva de PCC) **se traga todos los INVESTIGAR automáticos mientras siga abierto**, y uno con «sombra», «K»,
   «candidata» y «reversión» se tragaría las reversiones. Además, con un issue de reversión abierto, un segundo caso
   distinto no deja rastro en GitHub (no se comenta el issue existente). Sugerencia: un marcador único en el título o
   una etiqueta, y comentar el issue abierto con el detalle nuevo.
5. **(Media) Las pruebas no protegen el pareo por sensor ni la lectura A.** De las 12 mutaciones sobrevivientes
   (C5), tres tocan justo lo que decide una reversión: M1 (parear por volcán sin sensor) hace desaparecer el único
   caso real que la vigilancia encontró; M5 (umbral de protegida) y M10 (tipos de la lectura A) cambian qué cuenta como
   protegida. Faltan casos con dos sensores en la misma pasada (el caso de PCC sirve tal cual) y una prueba de
   `pasadas_de_alerta` con 0,5 MW y con `ALERTA_SIN_GEOMETRIA_OCR`.
6. **(Baja media) La cota de (iii) es de la etiqueta original y la vigilancia mide con SN.** La sección 6 del A/B usa
   la etiqueta original (el pre-registro decide con ella; `v1.log` l. 196). Sobre producción K del retrospectivo,
   VIIRS 375: original 12 de 580 publicados en negativos limpios, Wilson [0,0119; 0,0358]; **SN 21 de 611, [0,0226;
   0,0520]** contra la cota 0,0501 (`negativos_sn.py` → `negativos_sn.out`). SN casi duplica la tasa porque convierte
   en negativos pasadas donde MIROVA sí vio algo de 0,05 MW o menos. Hoy no dispara (el nulo da 0,046 en 120 días),
   pero el sesgo va hacia falsa alarma y no está escrito. En (i) el efecto es el contrario (SN saca de las Muy Bajo
   justo las mínimas, que K pierde más): conservador.
7. **(Baja media) Nadie vigila al vigilante.** El workflow sólo se dispara con `workflow_run` de `experimental-diario`.
   Si ese workflow se renombra o se desactiva, la vigilancia deja de correr sin aviso: no hay `schedule` de respaldo,
   ninguna prueba amarra los dos nombres, y `nrt-monitor.yml` vigila sólo `nrt.yml`. Sugerencia: un `schedule` de
   respaldo o que el auto-audit del lunes avise si `sombra_latest.json` tiene más de 2 días.
8. **(Baja) `runs-on: ubuntu-latest`**, cuando el resto de los workflows nuevos se fijó en `ubuntu-24.04` porque
   `ubuntu-latest` migra a 26.04 desde el 2026-10-19. Este workflow no usa pyhdf, pero sí `setup-python` 3.11 y node
   sobre una imagen nueva. SIN VERIFICAR que fallen; fijarlo cuesta una línea.
9. **(Baja) Herramientas de la evidencia.** `experiments/_s156_autoaudit/correr_sombra.py` ya no corre contra el
   script final: `main()` parsea `sys.argv` y rechaza los tres argumentos posicionales («unrecognized arguments»).
   Y `mutar_vigilancia.py` restaura el archivo con `newline="\n"`, que en un checkout con CRLF deja el worktree con
   diferencias de fin de línea.
10. **(Informativo) `prod_pub = None` no dispara.** Una protegida que la sombra publica y para la que producción no
   tiene record (corrida del NRT perdida) no cuenta como pérdida de K. Es correcto para atribuir al detector, pero el
   operador igual no la vio. En el retrospectivo no hay ninguna (`instrumento_propio.out`, `prod_sin_record` 0).

## Qué quedó de los hallazgos del verificador anterior

1. Duración cumplida el primer día: **arreglado** (cuenta desde la adopción; la mutación `duracion_cuenta_retro` la
   atrapa una aserción).
2. `main()` sin prueba: **arreglado en parte**. Sigue sin prueba de punta a punta de `cargar_insumos`, pero el aviso de
   perfiles atrapa en la corrida real la sombra leída de producción (mi M6 → VIGILANCIA_CIEGA).
3. Disparador (i) y cotas: **arreglado** para (i) (sólo V375, que es la única cota diferencial). La parte de (iii)
   (cota original, medición SN) **sigue igual y sin escribir**; ahora medida (hallazgo 6).
4. La pérdida es de sensor: recogido en la marca («misma pasada publicada por K en VIIRS 375»), y lo confirmé.
5. Casos fuera de la lectura A (sin geometría): sin cambio, por diseño. Revisé el más grande de la ventana (Chillán
   VIIRS 375, 2026-10-18 05:42, 11,03 MW, sin geometría): K lo publica (cúmulo de 7,0 MW a 0,6 km), así que no es
   pérdida.
6. Tupungatito sin marca A119: **arreglado** (sale «referencia sospechosa (A119)»).
7. Sombra sin marca de régimen en ~75 %: sin cambio; el aviso de perfiles lo declara.

## ¿Algo debería impedir mergear?

Nada cambia el veredicto de hoy (VERDE, con PCC en el retrospectivo, reproducido por dos instrumentos), y el cambio en
`banco_paridad` es inocuo. Pero este workflow es el disparador de una reversión pre-autorizada, y dos defectos lo dejan
callado justo cuando importa: el hallazgo 1 (un volcán sin sombra da VERDE; Chillán en erupción es el caso típico) y el
hallazgo 2 (un push fallido se come el issue de reversión). Los dos son arreglos de pocas líneas y recomiendo que
entren antes del merge, junto con una prueba de dos sensores en la misma pasada (hallazgo 5). Lo del issue retrospectivo
prometido en la marca (C1) se resuelve abriéndolo a mano para PCC o corrigiendo la frase. Los hallazgos 3, 4 y 6
pueden ir después, pero el 3 va a producir un issue de investigación casi seguro en las primeras semanas, y conviene
que Nicolás lo sepa antes.

## Lo que no verifiqué

- El comportamiento real en GitHub Actions (latencia del índice de búsqueda, semántica de pasos tras una falla,
  disponibilidad de Python 3.11 en `ubuntu-latest` nuevo): razonado o simulado con un `gh` falso, no corrido.
- La identidad del objeto de PCC más allá del radio (tema del agente a61).
