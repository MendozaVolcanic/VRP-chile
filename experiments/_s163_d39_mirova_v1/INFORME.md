# S163, D-39: ¿se puede mergear Mirova-v1#26 sin perder ni corromper un dato de la referencia?

- **Hora del servidor:** 2026-10-26 (UTC). `main` de Mirova-v1 medido: `f5fe3b9a64` (2026-10-26 10:33 UTC). PR #26:
  cabeza `fb95c0e790`, base de mezcla `c48d24cad8` (2026-10-22 02:51 UTC), 1.555 commits de `main` desde entonces.
- **Quién:** sesión hija de S163 (Opus 5.5), pedida por la coordinadora `local_8a135e90`. Nicolás aprobó D-39 y pidió
  «investiga bien lo de mirova-v1, no queremos perder datos».
- **Dónde:** clon parcial `--filter=blob:none` en `D:\vrp-trabajo\s163-d39\mirova-v1` (sin imágenes; nunca un pull del
  repo de datos completo). Scripts y salidas en `D:\vrp-trabajo\s163-d39\scripts\`, copia de los `.py` y `.txt` en
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s163_d39_mirova_v1\`. Las simulaciones
  corren sobre copias en `D:\vrp-trabajo\s163-d39\sim\` y `D:\vrp-trabajo\s163-d39\mut\`, nunca sobre el repo vivo.
- **Lo único que escribí fuera de mis carpetas:** la rama `s163/d39-reposicion-y-bucle` de Mirova-v1 (commits
  `2ad6dd8730` y `dd606a65a1`, sobre la cabeza del PR). Nada en `main` de Mirova-v1 ni de VRP Chile. No pausé ningún workflow.

## Veredicto

**Se puede mergear CON CAMBIOS: primero hay que sumar al PR la rama `s163/d39-reposicion-y-bucle`.** El código del PR
no pierde ni corrompe ninguna fila (medido fila a fila, abajo). Pero el PR, tal como está, deja afuera 241 filas que el
consolidado perdió **después** de armado el PR, entre ellas dos alertas protegidas, y no tiene ninguna prueba que vigile
el bucle de push del workflow, que es justo donde nace la pérdida. La rama corrige las dos cosas.

Con la rama sumada, la evidencia cumple el criterio de Nicolás: **0 filas perdidas y 0 filas existentes cambiadas en las dos
direcciones** (consolidado y OCR, fila a fila, con verificador limpio que lo re-midió), 2.351 filas repuestas que existen
todas en la historia, y cero pérdidas no explicadas desde la base del PR en un barrido de las 1.239 versiones. Condiciones
del despliegue (sección 7): tag defensivo, `main.yml` y `ocr_workflow.yml` en pausa sin corridas en vuelo, y regenerar la
reposición contra el `main` ya quieto. Lo único que el PR empeora en apariencia es que ~6 % de las corridas del OCR van a
quedar en rojo en vez de mezclar a ciegas (riesgo 1); no pierde datos y tiene un arreglo aparte.

## 1. Lo que pasó después de abierto el PR: un episodio nuevo el 2026-10-24

El fenómeno: el 24-oct a las 17:44 UTC desaparecieron de golpe 241 pasadas viejas del consolidado, repartidas de enero a
ese mismo día, y nunca volvieron. Entre ellas, dos alertas de 1 MW o más:

| pasada (UTC) | volcán | sensor | VRP | distancia |
|---|---|---|---|---|
| 2026-05-29 19:55 | Villarrica | MODIS | 1,83 MW | 2,0 km |
| 2026-10-24 05:48 | Nevados de Chillán | VIIRS375 | 2,36 MW | 0,84 km |

El mecanismo es el mismo de H-T1, y ahora está trazado en los registros de Actions (script y salida:
`run_40116786605.log`, `run_40117161109.log`):

1. La corrida `40117161109` de `main.yml` se despachó a las 17:40:09, esperó runner 3,7 min, y `actions/checkout`
   trajo el sha **del despacho** (`19d428271f`), no el `main` de ese momento.
2. Entretanto, la corrida anterior (`40116786605`) ya había empujado otro ciclo del scraper (`e47b0d5b60`, 17:40:20).
3. Al empujar, la corrida vieja hizo `git pull --rebase -X ours` sobre ese otro ciclo: mezcló como texto dos órdenes
   distintos del mismo CSV (cada ciclo reescribe unas 22.000 líneas, «22304 insertions(+), 22301 deletions(-)») y dejó
   `53b1e6d3c0` con 241 llaves menos y 1.565 repetidas. El ciclo siguiente borró las repetidas; las perdidas quedaron.

Esto cierra la prueba de campo C1 de la auditoría del 22-oct: la base vieja viene del checkout del sha del despacho más la
espera de runner. El bucle nuevo del PR (fetch y `reset --hard origin/main` en cada intento, antes de correr el scraper)
ataca exactamente ese punto.

**Censo desde la base del PR** (`s04_muestreo_6h.py`, `s04_salida.txt`): la base, una versión cada ~6 h y el padre de cada
commit con firma de mezcla (VolcanoBot que toca el consolidado sin tocar `bitacora_robot.txt`, `s02_firma_sin_bitacora.txt`:
uno solo, `53b1e6d3c0`). Unión de llaves presentes en alguna muestra y ausentes hoy: **241** (232 RUTINA, 4
FALSO_POSITIVO, 5 ALERTA_TERMICA), todas perdidas en `53b1e6d3c0` (las muestras posteriores dan 0 ausentes). Límite: una
fila agregada y perdida entre dos muestras sin firma no se vería.

La alarma de VRP Chile (#896) sí lo vio: la corrida `40125452197` de `sync-mirova-csv.yml` (24-oct 19:28 UTC) quedó en
rojo con «el consolidado de MIROVA perdió llaves de la copia vigente (bajar=241)». Como esa alarma avisa sin rechazar, la
copia de VRP Chile también quedó sin esas 241 filas; vuelven solas cuando Mirova-v1 las reponga.

## 2. Nada se pierde: comparación fila a fila (punto 1)

Método: dos brazos sobre el mismo CSV de partida (el de `main` hoy), con la red simulada (latest.php = la descarga del
2026-10-22; imágenes = 404) y la hora fija. **A** = código de `main` (`scraper.py` y `backfill_horas_utc.py`, como el
`main.yml` de hoy). **B** = `main` + PR mezclado localmente (`reponer_filas.py`, `scraper.py`, `backfill_horas_utc.py`,
`guarda_llaves.py`, como el `main.yml` del PR). La diferencia A contra B es exactamente lo que agrega el PR; la diferencia
original contra A es lo que ya hace hoy cualquier ciclo. Llave: (timestamp, Volcan, Sensor), comparación como texto.

**Consolidado** (`s08_correr_ciclo.py`, `s09_comparar_ab.py` / `s09_salida.txt`; con el archivo de S163,
`s19_comparar_ab_b2.py` / `s19_salida.txt`):

| comparación | llaves que desaparecen | llaves nuevas | filas comunes con algún campo distinto |
|---|---|---|---|
| original contra A (lo que hace un ciclo hoy) | 0 | 0 | 33, sólo `Ultima_Actualizacion` y su UTC (las filas que latest.php vuelve a mostrar) |
| A contra B, archivo del PR | **0** | 2.110, todas del archivo de reposición | **0** |
| A contra B2, archivo de S163 | **0** | 2.351, todas del archivo de reposición | **0** |

- Las nuevas son idénticas al archivo de reposición fuera de las dos columnas UTC (0 diferencias); el backfill llena esas
  columnas desde la hora de Chile (2.348 de 2.351 quedan con las dos; 3 con alguna vacía, como manda el backfill para
  horas ambiguas).
- 0 llaves repetidas en A, B y B2. La guarda de llaves pasa sobre B y B2. B queda en el orden total (timestamp
  descendente, Volcan, Sensor).
- `reponer_filas.py` corrido dos veces seguidas: 2.351 la primera, 0 la segunda.
- Hoy en `main` hay 0 llaves repetidas en el consolidado (42.991 filas) y en el OCR (1.147): la guarda nueva no arranca
  en rojo (`s01_duplicados_main.py` / `s01_salida.txt`).

**OCR** (`s10_ciclo_ocr.py`, `s11_comparar_ocr.py` / `s11_salida.txt`): pasos del `ocr_workflow.yml` que reescriben el
CSV sin red (`guardar_ocr` sin eventos, backfill de horas, reparación del mojibake en B, reconciliación, maestro).

| comparación | desaparecen | nuevas | filas con algún campo distinto |
|---|---|---|---|
| original contra A | 0 | 0 | 1 (`Zenith_Sat_deg` 24 a 24.0 en una fila de Láscar: lo hace el código de hoy, no el PR) |
| A contra B | **0** | 0 | **647, sólo `Nota_Validacion`** |

- Las 647 son las notas en mojibake declaradas (H-O8). En las 647 el esqueleto ASCII queda idéntico (la reparación sólo
  toca tramos no ASCII); 647 tenían mojibake antes, 0 después; en todo el archivo B quedan 0 notas con mojibake.
- Columna nueva `Metodo_Clase` al final, vacía en las 1.147 filas viejas; el orden de las 31 columnas existentes no cambia.
- El brazo B1 (código del PR con el consolidado sin reponer) da el OCR idéntico a B: reponer filas de la tabla no reclasifica
  ninguna fila del OCR.

**Maestro publicable** (`s12_maestro.py` / `s12_salida.txt`), consecuencia esperada, no daño: 76 alertas nuevas (todas del
archivo de reposición), 392 notas con el mojibake reparado, y 26 filas donde la alerta del OCR se reemplaza por la fila de
la tabla que vuelve (la regla del maestro prefiere la tabla; por ejemplo Láscar MODIS 2026-02-14 01:40 pasa de 3,0 MW
leído por OCR a 3,43 MW de latest.php). 0 llaves desaparecen.

## 3. Las filas a reponer son reales (punto 2)

`s05_verificar_reposicion_pr.py` / `s05_salida.txt`, `s05b_que_campos.py` / `s05b_salida.txt`, `s06_chillan_15_16.py`:

- Las **2.110** filas del archivo del PR: 0 están hoy en `main`; 2.110 llaves distintas; misma cabecera que el consolidado.
  2.081 aparecen en el padre de uno de los 16 commits de mezcla de la auditoría y faltan en ese commit; de ellas 787 son
  idénticas campo a campo y 1.294 difieren sólo en `Fecha_Proceso_UTC` y `Ultima_Actualizacion_UTC` (el archivo del PR las
  trae vacías y el backfill las rellena) o, en 2 filas, también en `Ultima_Actualizacion` (otra copia de la misma fila).
  Ninguna difiere en VRP, distancia, tipo, clase ni hora de la pasada.
- Las **29** restantes (abril, 27 RUTINA y 2 ALERTA_TERMICA) están en `9d70bc2d53^` pero no las pierde ese commit sino uno
  posterior de abril que no está en la lista de episodios: son reales (existen en la historia y faltan hoy), sólo su
  atribución de episodio es imprecisa. Contra `9d70bc2d53^`, 260 de las 332 filas de abril del archivo son idénticas fuera
  de las columnas UTC.
- Las **241** de S163 (`s17_verificar_archivo_nuevo.py` / `s17_salida.txt`): las 241 son idénticas campo a campo a su copia
  en `53b1e6d3c0^`, faltan en `53b1e6d3c0` y faltan hoy en `main`. El archivo nuevo empieza con el del PR byte a byte; 2.351
  filas, 2.351 llaves, 20 protegidas.
- **Ninguna fila inventada**: toda fila del archivo existe en un commit anterior de Mirova-v1.

**Lo que R4 no puede reponer.** Las alertas de Chillán del 15 y 16-oct que sólo están en el OCR (las ocho filas de
`ALERTA_SIN_GEOMETRIA_OCR` y `ALERTA_TERMICA_OCR` a las 05:00, 19:00, 06:18, 12:45, 05:42 y 18:42) **nunca tuvieron fila de
tabla**: en 44 versiones horarias del consolidado del 15-oct 04:00 al 17-oct 02:00 no hay ninguna fila de Chillán a las
05:00, 19:00, 06:18 ni 18:42 (`s07_chillan_historia.py` / `s07_salida.txt`). No son pérdida por mezcla. O latest.php
nunca las mostró mientras el scraper corría (H-P2, una pasada visible ~1,4 h), o la hora que lee el OCR no es la de la
pasada (la tabla sí tiene Chillán a las 05:18, 06:00, 05:42 y 19:00:01). Cuál de las dos: SIN DATO. Las de 05:42:02 y
12:45 del 16-oct sí están en la tabla hoy.

## 4. El scraper nuevo no vuelve a perder (punto 3)

- **Suite completa del PR sobre el merge simulado con el `main` de hoy:** 167 pasan, 0 fallan (`s13_suite_merge26.txt`,
  JUnit `s13_suite_merge26.xml`). El PR mezcla sin conflictos: desde la base, `main` sólo tocó datos e imágenes, ningún
  archivo que el PR cambia.
- **Suite con la rama de S163 sobre el merge simulado con el `main` de hoy:** 170 pasan (las 167 y las 3 nuevas), 0 fallan
  (`s18_suite_merge_s163.txt`, JUnit `s18_suite_merge_s163.xml`, árbol `3c85f631e4`).
- **La prueba de la mezcla del PR** (`tests/test_orden_determinista.py::test_rebase_de_dos_ciclos_no_pierde_ni_duplica_filas`)
  falla con el orden viejo y pasa con el nuevo (mutación R1 de la tabla de abajo).
- **Brecha encontrada:** ninguna prueba del PR ejecutaba el bucle de push del workflow. Quitar el `reset --hard origin/main`,
  volver el `pull --rebase -X ours` o sacar la guarda de `main.yml` pasaba en verde. Agregué
  `tests/test_bucle_push_main_yml.py` en la rama: ejecuta el `run:` real del paso de push de `main.yml` en un repo de
  juguete, con un scraper de mentira que escribe en el orden viejo (el peor caso) y que, la primera vez que corre, hace que
  otro ciclo empuje antes que él (lo que pasó el 24-oct). Más dos reglas estructurales (sin `-X ours` en el push de
  `main.yml` ni de `ocr_workflow.yml`, guarda antes del push). Lee los workflows sin PyYAML, que no está en
  `requirements.txt`; comprobé que su lector da los mismos pasos que PyYAML en los dos workflows, en la versión del PR y en
  la de `main`. **Línea base roja:** con el `main.yml` de `main` la prueba falla 3 de 3 veces («el push perdio 1 llaves»);
  con el del PR pasa.
- **Mutaciones** (`s15_mutaciones.py` / `s15_salida.txt`; cuenta como atrapada sólo una falla por aserción en el JUnit, no
  una caída; control sin mutación: 35 de 35 pasan; tras la batería los 7 archivos quedaron idénticos por md5):

| mutación | atrapada por |
|---|---|
| R1 orden viejo (sólo timestamp, empates al azar) | 3 pruebas de `test_orden_determinista.py` |
| R3 la guarda no mira llaves perdidas | `test_perder_una_llave_falla`, `test_linea_de_comandos_sale_en_rojo` |
| R3 la guarda no mira repetidas | `test_llave_repetida_falla` y otra |
| R3 la guarda sale 0 con problemas | `test_linea_de_comandos_sale_en_rojo` |
| R4 reponer pisa filas existentes | `test_agrega_solo_las_llaves_que_faltan`, `test_correrlo_dos_veces_no_cambia_nada` |
| R4 reponer sin filtro de nombres y tipos | 2 pruebas de `test_reponer_filas.py` |
| H-P1 el scraper sale 0 cuando falla | 8 casos de `test_fallo_ruidoso.py` |
| H-O8 mojibake reparado entero y no por tramo | `test_nota_mixta_repara_solo_la_parte_vieja` |
| R2 `main.yml` sin reset a `origin/main` | **sólo la prueba nueva** (2 casos) |
| R2 `main.yml` con `pull --rebase -X ours` de vuelta | **sólo la prueba nueva** (2 casos) |
| R3 `main.yml` sin guarda | **sólo la prueba nueva** |
| R2 `ocr_workflow.yml` con `-X ours` de vuelta | **sólo la prueba nueva** |

12 de 12 atrapadas; las 4 del workflow, sólo con la prueba de la rama.

## 5. R13 en VRP Chile (punto 4): ya está en producción

El arreglo ya se mergeó antes de esta sesión: MendozaVolcanic/VRP-chile#895 (`6547f5315`, S160: «el sync del CSV de MIROVA
reintenta sin rebasar») y #896 (`2ba670463`, la alarma de llaves perdidas). En `origin/main` de VRP Chile,
`.github/workflows/sync-mirova-csv.yml` reintenta con `git fetch` y `git reset --hard origin/main` y vuelve a correr
`scripts/sync_mirova_csv.sh`; no queda ningún `rebase` en el paso de push. Su prueba
`tests/test_sync_mirova_sin_rebase_s160.py` pasa (9 de 9) en este worktree. No hace falta otra rama para R13; la alarma de
#896 funcionó el 24-oct (punto 1).

## 6. Riesgos que quedan con el PR mergeado

1. **El push del OCR ahora aborta en rojo si el rebase choca, y hoy choca en ~6 % de las corridas.** Mi primer
   barrido de los registros (`s14_contar_choques_ocr.py` / `s14_salida.txt`: 191 corridas, 181 rebases, 0 «CONFLICT»,
   0 «Auto-merging») **no sirve para esta pregunta**: con `-X ours` git resuelve el choque sin imprimir nada (lo comprobó
   el verificador en el registro de la mezcla del 24-oct, que tampoco muestra «Auto-merging»). El instrumento era ciego.
   El verificador reconstruyó con git cada push (V5, `verificador/v07_choques_ocr.py`): en 332 pushes de 300 corridas
   (2026-10-20 21:00 a 2026-10-26 12:00 UTC), **18 (5,7 %) tenían el mismo CSV cambiado por los dos lados**, siempre por
   **otra corrida del OCR solapada**: el cron `5 * * * *`, que GitHub ejecuta con 1 a 33 min de atraso, cae encima del
   despacho externo de :00 y :30, y `cancel-in-progress: true` cancela a la vieja cuando ya empujó (V1). Hoy esos choques
   se resuelven a ciegas a favor del remoto (SOSPECHA fuerte de que el OCR pierde filas de esa corrida en silencio); con
   el PR, esas corridas quedan en rojo y no empujan. **No borra nada que ya esté en `main`**; las filas de esa corrida
   las vuelve a leer la siguiente si MIROVA sigue mostrando la pasada. Arreglo recomendado, aparte del PR: sacar el cron
   del OCR de la grilla del despachador (o quitar uno de los dos) y que el OCR parta de `origin/main` al empezar.
2. **El vigilante de dato** (nuevo, cron :07 y :37) se pone en rojo si el consolidado no se actualiza en 60 min: una pausa
   larga durante el merge dispara un correo. Mantener la pausa bajo 30 min o esperar ese rojo.
3. **Una llave repetida que entre a `main` por otro camino** (un commit a mano) deja al scraper en rojo en todos los ciclos
   hasta que alguien la corrija. Hoy hay 0; el vigilante avisaría en una hora.
4. **El primer ciclo reordena el consolidado entero** (un diff del tamaño del archivo, una vez). El sync de VRP Chile reemplaza el
   archivo entero, así que no le afecta; su alarma sólo mira llaves perdidas y aquí sólo se agregan.

## 7. Plan de despliegue con vuelta atrás (punto 5)

Lo ejecuta Nicolás: el 2026-10-26 S164 hizo el paso 1 y el clasificador de permisos le negó el paso 2. **El bloque exacto
para copiar y pegar, con el valor esperado en cada verificación, está en `PASOS_PARA_NICOLAS.md`** (en esta carpeta).
Yo no pausé ni mergeé nada.

1. **Sumar la rama de S163 al PR.** Mergear `s163/d39-reposicion-y-bucle` (`dd606a65a1`) en `fix/referencia-estable`: son dos
   commits sobre su cabeza, avance rápido. Esperar el CI de #26 en verde con conclusión, no «0 checks» (A39, enmienda S142).
2. **Pausar los escritores de datos**, para que nada corra con el código viejo mientras se mergea:
   ```bash
   gh workflow disable main.yml -R MendozaVolcanic/Mirova-v1
   ```
   ```bash
   gh workflow disable ocr_workflow.yml -R MendozaVolcanic/Mirova-v1
   ```
   El despachador externo de cada 5 min seguirá llamando a `main.yml` y recibirá error mientras esté deshabilitado: es lo
   buscado. `graficos_completo.yml` puede seguir (sus merges no cambian datos: 0 de 5.555, auditoría m03). Esperar a que no
   quede ninguna corrida de esos dos en curso:
   ```bash
   gh run list -R MendozaVolcanic/Mirova-v1 --status in_progress --json workflowName,databaseId
   ```
3. **Regenerar la reposición contra el `main` ya quieto**, por si hubo otro episodio entre hoy y el merge (en un clon
   parcial, nunca pull del repo completo):
   ```bash
   python -I D:\vrp-trabajo\s163-d39\scripts\s16_regenerar_reposicion.py <clon> <archivo de la rama> <salida> --hasta origin/main
   ```
   Si dice «nuevas 0», seguir. Si hay nuevas, commitearlas a la rama del PR, actualizar el conteo de
   `tests/test_reponer_filas.py` y esperar el CI otra vez.
4. **Tag defensivo en `main`** (A38, A45) y push del tag:
   ```bash
   gh api repos/MendozaVolcanic/Mirova-v1/git/refs -f ref=refs/tags/pre-pr26-referencia-estable -f sha=$(gh api repos/MendozaVolcanic/Mirova-v1/commits/main --jq .sha)
   ```
5. **Mergear #26** (merge o squash; `main` no tiene protección de rama ni rulesets, consultado hoy por la API). Rehabilitar los dos workflows y disparar un ciclo a mano:
   ```bash
   gh workflow enable main.yml -R MendozaVolcanic/Mirova-v1
   ```
   ```bash
   gh workflow enable ocr_workflow.yml -R MendozaVolcanic/Mirova-v1
   ```
   ```bash
   gh workflow run main.yml -R MendozaVolcanic/Mirova-v1 --ref main
   ```
6. **Verificar la primera corrida de `main.yml`**: verde; en el registro, «reponer_filas: 2351 filas repuestas» (o el número
   del paso 3) y «Guarda de llaves OK». Después, en un clon parcial, comparar el consolidado del tag con el de `main`:
   ```bash
   git show pre-pr26-referencia-estable:monitoreo_satelital/registro_vrp_consolidado.csv > antes.csv
   ```
   ```bash
   python guarda_llaves.py monitoreo_satelital/registro_vrp_consolidado.csv --anterior antes.csv
   ```
   Tiene que dar OK (0 llaves perdidas, 0 repetidas) y el conteo tiene que ser el del tag + 2.351 + las pasadas nuevas.
   La segunda corrida tiene que decir «reponer_filas: 0 filas repuestas».
7. **Verificar la primera corrida del OCR** (minuto :05): verde, «reparar_mojibake: 647 notas reparadas», guarda OK; la
   siguiente, 0 notas. El sync de VRP Chile de la hora siguiente debe quedar verde (sin «perdió llaves»).
8. **Una semana después (C3 de la auditoría):** contar corridas de `main.yml` y del OCR que la guarda o el rebase dejaron en
   rojo; y repetir `s16_regenerar_reposicion.py --hasta origin/main` con la base en el tag: tiene que dar «ausentes hoy 0».

**Vuelta atrás.** El PR sólo agrega filas y cambia código, así que revertir no necesita tocar datos:
`git revert -m 1 <merge>` (o `git revert <squash>`) devuelve el código viejo y deja las filas repuestas, que son reales.
Si algo dañara el consolidado, **no** restaurar el archivo del tag a ciegas (borraría las pasadas nuevas desde el tag):
reponer desde el tag con el mismo `reponer_filas.py`, que sólo agrega llaves que faltan.

## 8. Verificador con contexto limpio

Fable 5.1, esfuerzo high, sin ver mi razonamiento; recibió sólo las diez afirmaciones y dónde se midieron. Informe
completo: `VERIFICADOR_INFORME.md` (copia de `D:\vrp-trabajo\s163-d39\verificador\INFORME.md`), scripts y salidas en
`verificador\`. Ningún REFUTADO.

| afirmación | veredicto | nota |
|---|---|---|
| A1 episodio del 24-oct y nada más perdido desde la base | CONFIRMADO ENTERO | barrido de las 1.239 versiones, una por una: única versión con pérdidas o repetidas `53b1e6d3c0`; 0 pérdidas transitorias |
| A2 mecanismo en los registros | CONFIRMADO | V1: la corrida `40116786605` figura «cancelled» y empujó |
| A3 consolidado, 0 perdidas y 0 cambiadas | CONFIRMADO | re-corrida propia; V8: la simulación no inserta pasadas nuevas (sólo refresca 33) |
| A4 OCR, sólo las 647 notas | CONFIRMADO para filas existentes | V6: el PR baja a «baja» la confianza de las alertas futuras del método de grupo; nadie filtra por eso |
| A5 filas a reponer reales | CONFIRMADO, más fuerte | las 2.351 idénticas campo a campo (UTC incluidas) a la fila de algún padre de los 17 episodios |
| A6 Chillán 15 y 16-oct sin fila de tabla | CONFIRMADO ENTERO | barrido de 562 versiones; SOSPECHA: son las mismas pasadas de la tabla con hora leída gruesa |
| A7 suite 167 y 170 | CONFIRMADO | re-corrida propia; GitHub da #26 MERGEABLE y CLEAN |
| A8 prueba nueva y mutaciones | CONFIRMADO EN PARTE | V2: 2 mutaciones caían por `ValueError` y no por aserción. **Corregido** en `dd606a65a1`; re-medido: las 12 atrapadas, «sin guarda» y «sin reset» ahora por `AssertionError` (`s15b_salida.txt`) |
| A9 R13 en VRP Chile | CONFIRMADO | |
| A10 basta pausar `main.yml` y `ocr_workflow.yml` | CONFIRMADO EN PARTE | V3: `archivar_evidencia.yml` y `graficos_completo.yml` conservan `-X ours` (no tocan CSV); V4: pausar no cancela la corrida en vuelo, hay que esperar a que no quede ninguna (paso 2 del plan) |

Aviso del verificador: una limpieza de procesos suya mató `bash.exe` de más, posiblemente la terminal de otra sesión.

## 9. SEGUIMIENTOS, SIN DATO y lo que no miré

- **SIN DATO:** por qué el scraper nunca guardó las pasadas de Chillán del 15 y 16-oct que el OCR sí tiene (punto 3).
- **SEGUIMIENTO:** el archivo del PR atribuye 29 filas de abril a un episodio que no las pierde; la lista de episodios de
  abril de la auditoría está incompleta. No cambia la reposición (las filas son reales).
- **SEGUIMIENTO:** la corrida `40116786605` aparece «cancelled» aunque empujó (`e47b0d5b60`, V1): con
  `cancel-in-progress: true` una corrida cancelada puede haber escrito. El PR lo pasa a `false` en `main.yml`, pero
  `ocr_workflow.yml` sigue con `true` y con el cron encima del despacho (riesgo 1).
- **SEGUIMIENTO:** `archivar_evidencia.yml` y `graficos_completo.yml` siguen mezclando con `-X ours` (V3). No tocan CSV de
  datos hoy; mismo patrón que el PR erradica.
- **No miré:** las imágenes de MIROVA; la reposición contra pérdidas anteriores a la base del PR más allá de lo que verificó
  la auditoría del 22-oct (sus 2.110); los workflows de otros repos que leen Mirova-v1.
