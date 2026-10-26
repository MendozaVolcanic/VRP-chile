# Verificación limpia de la Adenda 1 (días con hueco de NASA) del pre-registro diurno sobre K

- Hora del servidor al empezar: Mon, 26 Oct 2026 18:49:25 GMT (`gh api -i repos/MendozaVolcanic/VRP-chile`); al cerrar: 19:07:41 GMT.
- Commit medido: `867cb1ec80308338412af1c0c59b28541c271872` (rama `claude/s163-diurno-k-prereg-5c4f44`, en `origin`). Árbol limpio al empezar.
- Modelo: Sonnet 5.5 (`claude-sonnet-5-5`). Esfuerzo declarado: bajo (10, el de esta sesión).
- Lista de caminos escrita ANTES de abrir el script: `CAMINOS.md`, sha256 `4a83599ffeca7baf6a44f6ef1242c6656f5bebe6d25b1e11e02f0083ea67ace2`
  (`head -n 53 CAMINOS.md | sha256sum`; después se le agregó un pie con la hora 18:50:30 GMT). Antes de escribirla leí sólo el texto de la
  adenda (`PREREGISTRO.md` §11, l. 497 a 545). No modifiqué ningún archivo del repo; todo lo mío está en esta carpeta
  (`va_*.py` y sus salidas) o en el temporal de la sesión.
- Para repetir: carpeta `experiments/_s163_diurno_k/verificador_adenda1/`. Temporales: W1 bajado con `git fetch origin
  s151-ab-diurno/40364164845` + `git archive` (1,6 MB), referencia con `congelar_referencia.py --commit 047bd5692` (4 sha256 OK).
  No lancé nada en segundo plano ni terminé ningún proceso.

## Resultado

**Conforme con reservas.** La adenda cumple las siete condiciones de la coordinadora en lo escrito y en lo que hace el script;
las cifras de W1 se reproducen exactas; el evaluador sellado no cambió. Hay 0 hallazgos de gravedad 4 o 5 y 1 de gravedad 3: **el
evaluador sellado no tiene ninguna forma de recibir la lista** (V1), así que "se corre con la lista que decide" necesita un
pegamento que hoy no existe, no está sellado y no está verificado.

| gravedad | hallazgos |
|---|---|
| 3 | V1 |
| 2 | V2, V3, V4, V5 |
| 1 | V6, V7, V8, V9, V10 |

## Hallazgos (ordenados por gravedad)

### V1 · gravedad 3 · CONFIRMADO · No hay camino sellado para pasarle la lista al evaluador
- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:389-390` (`excluir_dias` es parámetro de `evaluar`), `:594-598` (`evaluar_completo` sólo lo usa para la
  variante `sin_W2`), `:620-629` (`main()` tiene 9 argumentos y ninguno es una lista de días), `PREREGISTRO.md:470-471` (el comando del §8 no
  lleva lista), `PREREGISTRO.md:529-530` («se corre con la lista que decide»).
- QUÉ PASA: la condición (4) pide que el evaluador no se toque y que un script aparte entregue `excluir_dias`. El script lo entrega, pero ni
  `main()` ni `evaluar_completo` lo reciben. Para usarla hay que escribir un tercer programa (o filtrar a mano los records y las filas de la
  referencia). Ese pegamento no está en el repo, no está en `objetivos_sha256.txt` y ningún verificador lo ha visto. Tampoco hay en el repo
  ningún script que imprima las líneas «W1 sin excluir … / W1 regla (b) … / W1 regla (a) y (b')» de `w1/dias_excluidos_w1_salida.txt`
  (`grep -rl "W1 sin excluir"` sólo da el propio archivo de salida).
- CÓMO SE VERÍA: con `main()` tal cual, cualquier hueco da INVÁLIDO POR INSTRUMENTO y la lista no se usa. Con un pegamento que sólo toque el
  principal, `veredicto_final` (`:139-142`) compara un principal con lista contra variantes sin lista (INVÁLIDAS por I4): un ADOPTAR o
  NO ADOPTAR saldría DECIDE NICOLÁS (lectura de código, no lo corrí). Con un pegamento mal hecho el error puede ir en cualquier dirección.
- CÓMO REPRODUCIRLO: `grep -n add_argument experiments/_s163_diurno_k/evaluar_diurno_k.py` (9 líneas, ninguna de días).
- MITIGACIÓN MEDIDA: sí existe un pegamento sin tocar el evaluador. `va_glue.py` (salida `va_glue_salida.txt`): sobre W1, Láscar, canal unión,
  filtrar `filas` (por `fecha_utc`) y `recs` (por `dt`) y llamar `evaluar` da el mismo veredicto, las mismas protegidas y los mismos negativos que
  `evaluar(..., excluir_dias=lista)` (`iguales: True`), y `evaluar_completo` con las entradas filtradas corre y aplica la lista a las variantes.
  Falta que la adenda diga que se hace así y que ese código se selle y se verifique.

### V2 · gravedad 2 · CONFIRMADO · Las 18 pruebas no vigilan `main()` ni la consulta a CMR; 10 de 10 mutaciones propias sobreviven
- ARCHIVO:LÍNEA: `dias_excluidos_nasa.py:113-126` (`dias_sin_granulos`), `:141-177` (`main`); `test_dias_excluidos_nasa.py` no los llama.
- QUÉ PASA: las 9 mutaciones del repo (`mutaciones_dias_excluidos.json`) tocan sólo funciones puras. Escribí 10 propias sobre una copia (`va_mut.py`,
  `va_mut_salida.txt`) y las 18 pruebas siguen en verde con todas: M1 `main` decide con la regla (b); M2 sin paginación; M3 día CMR con `[:9]`; M4 caja
  distinta; M5 versión de `VNP02IMG` en "9"; M6 sólo consulta la banda I; M7 `temporal` que pierde el último día; M8 error de CMR leído como 0 gránulos;
  M9 ventanas con W1 incluida; M10 `--control` por defecto = brazo diurno (contaría los records del brazo como del control, y el brazo diurno sí tiene
  records de día).
- CÓMO SE VERÍA: una edición posterior a la adenda en esas líneas cambiaría la lista sin que ninguna prueba falle; M8 y M10 pueden sacar o dejar días
  en cualquier dirección. Hoy el código de `dias_sin_granulos` no trata un error como 0 (un fallo de red tira la excepción: leído, y tira KeyError si
  falta `entry`), y está validado empíricamente (ver Verificado limpio), pero eso no lo guarda.
- CÓMO REPRODUCIRLO: `python -I va_mut.py <copia de git archive 867cb1ec>`.
- Las 9 del repo se reproducen: `va_mut_d.py` da D1 a D9 atrapadas por aserción y C-CAIDA como caída (`va_mut_d_salida.txt`).

### V3 · gravedad 2 · CONFIRMADO · "La regla queda fija" es sólo texto: el script y su prueba no están sellados
- ARCHIVO:LÍNEA: `objetivos_sha256.txt` (29 rutas, commit 15fc6ec2; no incluye `dias_excluidos_nasa.py`, `test_dias_excluidos_nasa.py` ni
  `mutaciones_dias_excluidos.json`); `PREREGISTRO.md:535`.
- QUÉ PASA: la condición (7) dice que la regla queda fija desde el commit. Un cambio posterior al script no lo detecta el `git diff` del §8, que recorre
  esa lista. Además el sha256 sellado de `PREREGISTRO.md` (`4de4b827…`) ya no es el del archivo: en `867cb1ec` es `01aa924d…` (esperable, la
  adenda lo cambió; la lista no se actualizó).
- CÓMO SE VERÍA: una modificación del criterio después de ver datos de W2 a W6 pasaría el control mecánico de sellos.
- CÓMO REPRODUCIRLO: `git show 867cb1ec:experiments/_s163_diurno_k/PREREGISTRO.md | sha256sum`; `grep dias_excluidos objetivos_sha256.txt` (vacío).

### V4 · gravedad 2 · CONFIRMADO · La evidencia que exige la condición (5) no dice qué datos salen con los días excluidos
- ARCHIVO:LÍNEA: `dias_excluidos_nasa.py:129-138` (`armar_salida`), `PREREGISTRO.md:534`.
- QUÉ PASA: se declara por qué sale el día (CMR y control), pero no cuántas pasadas, negativos y alertas de MIROVA, ni cuántas protegidas, salen con él. La
  exclusión es de día entero y de todas las plataformas: saca también pasadas sanas de otras plataformas y de MODIS. En W1 (`va_w1_salida.txt`) salen
  6 pasadas diurnas de VIIRS 375 (5 RUTINA y 1 FALSO_POSITIVO) y 7 de VIIRS 750 (RUTINA), 0 protegidas; los negativos observados de VIIRS 375 pasan de 18
  a 16; de noche salen 2 alertas de MIROVA de VIIRS 375 y 3 de MODIS. De esas 13 diurnas, 6 tenían record del brazo (NOAA-20 y NOAA-21 existían).
- CÓMO SE VERÍA: en W2 a W6, si una exclusión se llevara una protegida, el resultado cambiaría de dirección sin que el informe lo muestre. Hoy no se
  espera ninguna exclusión (V10 y Verificado limpio), por eso gravedad 2 y no más.
- CÓMO REPRODUCIRLO: `python -I va_w1.py <W1> <ref>` (líneas «pasadas de MIROVA que salen» y «records de W1 que salen»).

### V5 · gravedad 2 · CONFIRMADO (lo que no cubre) · La regla ve sólo huecos de día entero y de la caja entera; el resto termina en INVÁLIDO sin remedio
- ARCHIVO:LÍNEA: `dias_excluidos_nasa.py:113-126` (cuenta gránulos del día sobre toda la caja); `w1/REVISION_W1.md` («un hueco parcial … no está
  descartado»).
- QUÉ PASA: un gránulo que falta en un volcán, o un periodo (noche o día) completo de una plataforma, no vuelve `0` el conteo del día. En CMR de hoy hay un
  caso real dentro de W6: `VNP02IMG`/`VNP02MOD` del 2026-10-13 sólo tienen gránulos de día (17:54, 18:00, 19:36, 19:42) y ninguno entre 03 y 09 UTC
  (`va_periodo_salida.txt`, `va_oct_salida.txt`); (a) no se cumple (hay 4). No encontré otro caso así en los 3 productos de banda I de W2 a W6 (los de banda M los revisé sólo por conteo diario, que es igual). La tabla de
  MIROVA de ese día no lista pasadas nocturnas de VIIRS (`va_tabla13_salida.txt`: sólo MODIS de noche el 13), así que no veo que I3 ni I4 fallen por ahí (inferido
  de la tabla, no corrí el evaluador sobre W6). El caso inverso (CMR lista el gránulo, el pipeline no puede bajarlo) tampoco lo toma ninguna regla.
- CÓMO SE VERÍA: si un hueco parcial hace fallar I4 en W2 a W6, el resultado es INVÁLIDO por instrumento (condición 3) y la regla no lo cura; es el
  diseño pedido, pero conviene que el informe del resultado lo diga.
- CÓMO REPRODUCIRLO: `python -I va_periodo.py`.

### V6 · gravedad 1 · CONFIRMADO · "Plataforma P" se implementa por producto, no por plataforma
- ARCHIVO:LÍNEA: `dias_excluidos_nasa.py:86-87`, `:90-94`; adenda `PREREGISTRO.md:513-517`.
- QUÉ PASA: el texto habla de "el producto L1B de P" y de "ningún record de P", listando `VIIRS_SNPP` y `VIIRS_SNPP_750` juntos. El script empareja
  cada producto con su propio `sensor` (banda I con `VIIRS_SNPP`, banda M con `VIIRS_SNPP_750`). Difiere de la lectura "plataforma = I y M" sólo si falta
  una banda y la otra no, algo que no pasa en W1 ni se ve en CMR de hoy. Es más estricto en (b'), más laxo en (a). Sin efecto medido.

### V7 · gravedad 1 · CONFIRMADO · "W2 estaba en cola, sin salidas" es impreciso; no encontré fuga
- Evidencia: run 40379112237 creado 2026-10-26T18:35:43Z (antes del commit de la adenda 18:44:46Z y de la aprobación 18:39), estado `queued`; pero 3 de 22
  jobs estaban `in_progress` desde 18:35:47Z (Láscar control y diurno, Lastarria control) cuando lo miré a las 18:50 y a las 18:55 GMT. No existe la rama
  `s151-ab-diurno/40379112237` (`gh api …/matching-refs/heads/s151-ab-diurno` lista 14 ramas, la última 40364164845). No hay datos publicados de W2 a W6; la
  condición (1) se cumple. La frase debería decir "sin salidas publicadas".

### V8 · gravedad 1 · CONFIRMADO · Parte de la salida de W1 la imprimió código que no está en el repo
- `w1/dias_excluidos_w1_salida.txt` líneas 6 a 13. Las reproduje con `va_w1.py` y salen idénticas (ver Verificado limpio). Va junto con V1.

### V9 · gravedad 1 · CONFIRMADO · La salida del corredor de mutaciones dice «9 de 10»
- `mutaciones_dias_excluidos_salida.txt` última línea: "atrapadas por asercion: 9 de 10" (cuenta el control de caída en el denominador). La adenda dice
  «9 de 9 … y el control de caída como CAÍDA», que es lo que muestra el cuerpo de la salida. Lectura posible equivocada, nada más.

### V10 · gravedad 1 · SOSPECHA · (b') se eligió viendo W1 para que W1 quedara válida
- Es el contenido de la condición (5) y está declarado en la adenda (punto 2). Lo dejo anotado porque el cambio mueve W1 de INVÁLIDA a DECIDE NICOLÁS CON M4
  y se decidió con W1 a la vista. Como (a) y (b') no miran el brazo diurno, no veo un sesgo hacia ninguno de los dos brazos; el efecto sobre
  W2 a W6 hoy es nulo (no hay día vacío en CMR).

## VERIFICADO LIMPIO (contra qué lo comprobé)

1. **Evaluador intacto (condición 4).** `git diff 68687d2d4 867cb1ec -- experiments/_s163_diurno_k/evaluar_diurno_k.py` es vacío (0 bytes);
   `git show 867cb1ec:…/evaluar_diurno_k.py | sha256sum` = `d6eb25b5…`, el de `objetivos_sha256.txt` l. 4. El diff completo 68687d2d4..867cb1ec toca 11 archivos,
   todos nuevos salvo `PREREGISTRO.md` (50 líneas), ninguno sellado salvo ese.
2. **Script = regla escrita (condición 2).** `dias_a_excluir` (`:90-94`) devuelve los días con 0 gránulos CMR de un producto y sin ningún record del control con el `sensor`
   de ese producto; sin lista escrita a mano; `dias_a_excluir_b` (`:56-63`) es la regla (b) y sólo se informa (`:174-176`); la salida trae las dos (`armar_salida`,
   `:135-138`: condición 6). `--control` por defecto es el control (`:146`).
3. **Mapeo `sensor` → producto (A5).** `PRODUCTO_DE_SENSOR` (`:86-87`) contra `pipeline/fetch.py:219-249` y `:1180-1200`: SNPP/NOAA20/NOAA21 × (IMG, MOD) coinciden con
   `VNP02IMG/VJ102IMG/VJ202IMG` y `…MOD`. Valores reales de `sensor`: los 8 de `data/mirova_equivalent/*.json` (6 VIIRS más `MODIS_AQUA` y `MODIS_TERRA`) y los 8 del control de W1;
   no hay ningún valor VIIRS sin mapear (los MODIS se ignoran a propósito).
4. **CMR repetida con código propio** (`va_cmr.py`, 18:52 GMT; `va_cmr_salida.txt`): con y sin el parámetro `version` el resultado es idéntico en los 6 productos y las 6 ventanas
   (`version_id` no viene en la respuesta, pero los conteos coinciden). Días sin gránulos: sólo `VNP02IMG` y `VNP02MOD` el 2026-03-10, 11 y 12 (W1). W2 a W6: ningún día vacío en
   los 6 productos; mínimo por día 4 gránulos de banda I. El script del repo (18:55 y 18:47 GMT) da la misma lista.
   LAADS (listado público, sin credencial): `…/archive/allData/5200/VNP02IMG/2026/069.json` (10-mar) y `…/VNP02MOD/2026/070` y `071` devuelven HTTP 404; `VNP02IMG/2026/068`
   y `072` listan archivos. El hueco existe también en el archivo, no sólo en CMR (para esos días y Suomi NPP).
5. **W1 reproducido.** `va_w1.py` sobre el run 40364164845 con la referencia congelada: sin lista, I4c V375 3 de 37 y V750 4 de 40, INVÁLIDO; con (b) `[10-mar]`, 1 de 34 y 2 de 37, INVÁLIDO;
   con (a) y (b') `[10, 11, 12-mar]`, 0 de 31 y 0 de 33, DECIDE NICOLÁS CON M4, V375 4 de 5 protegidas y 4 de 16 negativos, V750 SIN CAMBIO 0 de 33 (sin lista: 4 de 18 y 0 de 36). Todo igual a
   `PREREGISTRO.md:538-543`. `dias_excluidos_nasa.py --w1` regenera `dias_excluidos_w1.json` igual salvo la hora de la consulta. `revisar_w1.py` regenera `revisar_w1_salida.txt` byte a
   byte (diff vacío). Los 7 faltantes están sólo el 10 a 12 de marzo; fuera, 0 de 64 diurnas y 0 de 46 nocturnas. El log del job confirma `VNP02IMG_NRT … 2026-03-10..2026-03-12 n=0` (y las otras tres).
6. **Pruebas.** `python -m pytest -q -p no:cacheprovider …/test_dias_excluidos_nasa.py` → 18 passed (dos veces, en el árbol y en una copia). Mutaciones del repo: 9 de 9 atrapadas por aserción
   y el control de caída como caída, re-corridas en una copia fuera del worktree (`va_mut_d.py`).
7. **Fecha (condición 1).** Commits de la adenda: 7d0a1dac 15:44:46 -03 (18:44:46 UTC) y 867cb1ec 15:48:47 -03 (18:48:47 UTC), coherentes con «hacia las 18:45 / 18:50»; la consulta a CMR
   de `dias_excluidos_w1.json` es 18:47:32Z; W2 se despachó 18:35:43Z y a las 18:55 sigue sin rama de salidas. El commit está en `origin`.
8. **Condiciones (3) y (5).** El punto 4 de la adenda dice INVÁLIDO si I4 falla tras excluir, y el evaluador lo hace (con lista corta, `invalido` sigue con I4c). El punto 2 dice que (b) se cambió a (b')
   después de ver W1, con el motivo; coincide con el comentario del script (`:18-21`) y con la primera versión (7d0a1dac, que traía (b') sólo informativa).
9. **Camino de W2 a W6 del script (`--raiz` sin `--w1`)** corre sin error: con una raíz sintética (los records de W1 movidos a junio) dio lista vacía (CMR no tiene días vacíos ahí) y la regla (b) informativa
   marcó como «perdidas» casi todas las noches de las cinco ventanas, porque la raíz sintética sólo cubre una parte (humo de que el camino corre, no resultado).
10. **Estilo.** 0 guiones largos y 0 medios en `PREREGISTRO.md`, el script, su prueba y `REVISION_W1.md`.

## SIN DATO
- Si la aprobación D-48 de la coordinadora a las 18:39 UTC existe como registro: no lo vi (el repo menciona D-48 en otros contextos).
- Qué hace el pipeline real de W2 a W6 con los días de D-29 (12, 13 de octubre): la producción local no tiene records del 13-oct para Suomi NPP ni NOAA-21 (`va_prod_salida.txt`: 44 de 5.478
  combinaciones volcán-plataforma-día de W2 a W6, todas del 2026-10-13), mientras CMR hoy sí lista NOAA-21 ese día. No sé si es hueco de entonces o desfase del árbol local; el A/B baja ahora.
- Huecos parciales por volcán dentro de W2 a W6 (un gránulo que falta sobre un solo volcán): no hay datos del A/B para medirlos.
- Que LAADS no tenga archivos que CMR sí indexa, o al revés, para W2 a W6: no probé descargas.
- Mutaciones: no corrí el corredor oficial (`mutar.py` modifica archivos del repo); usé una copia temporal con mi propio corredor.

## QUÉ NO MIRÉ
- El resto del pre-registro (§1 a §10, §12 a §15), el evaluador por dentro (sólo `evaluar`, `evaluar_completo`, `main`, `veredicto_final`), las compuertas I1 a I6 y el nulo.
- Los PDF de Coppola y el código `.m` de MIROVA (fuera del alcance acotado).
- MODIS: la regla excluye también sus pasadas nocturnas del día (V4), pero no medí qué compuerta lee MODIS.
- Si el workflow (`reproc-s151-ab-diurno.yml`) pasa `skip_noaa20` u otra opción que quite plataformas.
- Que las coordenadas, la hora de salida del sol y el resto de lo que define «día» sean las que usará la evaluación final.
