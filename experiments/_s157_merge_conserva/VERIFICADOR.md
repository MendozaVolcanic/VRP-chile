# Verificador con contexto limpio: el merge de reproc-chunked conserva lo que main ya tiene

Afirmación revisada: "El merge de reproc-chunked.yml ahora conserva lo que data/<perfil>/<Vol>.json ya tiene
en main fuera de las ventanas de la corrida, y lee esa base de main al momento de unir, no del checkout del
despacho."

Worktree `D:\vrp-trabajo\s157-merge-conserva`, rama `s157-merge-conserva`, commit `44d25628d` (PR #873).
No edité nada fuera de este archivo. Todo lo temporal quedó en `D:\vrp-trabajo\tmp\`.

## Veredicto: CONFIRMADO

Las dos partes de la afirmación se sostienen con las pruebas que corrí y con la lectura del código. Encontré
un defecto de razonamiento escrito (comentario del script y README) que no cambia el comportamiento que la
afirmación describe, y dos fragilidades menores. Lo grave que encontré ya existía antes del cambio.

## Caminos revisados

### 1. Las pruebas del cambio pasan

`python -m pytest tests/test_merge_chunk_stores.py tests/test_reproc_chunked_merge_conserva_s157.py -q`
dio `28 passed in 82.66s`. Suite completa con el árbol quieto (no edité nada mientras corría, A112):
`2244 passed, 28 skipped, 2 xfailed in 245.78s`, igual al número del README.

### 2. Las pruebas del yml corren lo mismo que GitHub

- El test extrae el `run:` del paso con `yaml.safe_load` y lo corre con `bash -e`. Comprobé que el bloque no
  tiene expresiones `${{` (que GitHub sustituiría antes y el test no) y que no hay `shell:` ni `defaults`
  en el paso, el job ni el workflow: salida `expr en run: False`, `shell: None None None`. Para un `run:`
  sin `shell:` en Linux GitHub usa `bash -e {0}`, así que el `set +e` del paso es necesario y está.
- Diferencia real con GitHub: el test clona el origen completo por ruta local, y `actions/checkout` hace
  un clon superficial. Repetí las pruebas de relanzar, base de main y main que se mueve (las dos variantes)
  con el despacho clonado `--depth 1` por `file://` y una semilla de 4 commits, comprobando que existe
  `.git/shallow`: `4 passed`. El `fetch --depth=1` sobre un clon superficial y el `push` desde él funcionan
  contra un receptor git local. **SIN VERIFICAR contra GitHub real** (no despaché nada).
- `git checkout -f -B reproc-merge FETCH_HEAD` con `chunks/` sin seguimiento: `git ls-tree -r --name-only
  origin/main | grep -c "^chunks/"` da `0`, así que el checkout no tiene nada que pisar ahí. `-f` sólo
  descarta cambios de archivos con seguimiento.
- `git add -f` con glob sin coincidencias (perfil nuevo sin trozos): la prueba
  `test_perfil_nuevo_sin_ningun_trozo_no_falla` lo cubre y pasa; la mutación Y6 (quitar `set +e`) la hace
  caer, que es justo lo que muestra que el `set +e` hace falta.
- `permissions: contents: write` está a nivel de workflow (línea 40 del yml).

### 3. La base sale de main en cada intento, no del despacho

Cada vuelta del bucle hace `fetch` de main, `checkout -f -B` a `FETCH_HEAD`, copia la base a
`$RUNNER_TEMP`, une y empuja sin `-f`. Si el push se rechaza, la vuelta siguiente vuelve a hacer checkout de
la punta nueva (y descarta el commit local rechazado) antes de releer. Lo cubren
`test_la_base_sale_de_main_y_no_del_checkout_del_despacho` y las dos variantes de
`test_si_main_se_mueve_antes_del_push_se_relee_la_base`, que pasan también con clon superficial (camino 2).
Un push que llegó al servidor pero dio error al cliente se resuelve solo: la vuelta siguiente une contra la
base que ya trae el resultado, sale idéntico y termina en `no changes`.

### 4. Trozo caído, volcán sin trozos, perfil nuevo

- Trozo caído: el paso `Guardar el trozo` no tiene `if: always()`, así que un job fallido no sube artefacto;
  su ventana no entra en `VENT` y la base de ese tramo se conserva. En el script, una ventana declarada con
  archivo inexistente también se quita (`ventanas` se filtra por `existe`). Prueba
  `test_base_trozo_caido_no_borra_su_ventana`: pasa.
- Volcán sin trozos: `continue` sin tocar el archivo; `test_volcan_sin_trozos_deja_main_intacto` pasa.
- Perfil o volcán sin archivo en main: `--base` apunta a un archivo inexistente, el script avisa y une sin
  base; `test_perfil_sin_archivo_en_main_se_crea_como_antes` pasa.

### 5. La comparación por los primeros 10 caracteres coincide con cómo se asignan las pasadas

- `datetime_utc` sale del nombre del gránulo (hora de inicio) en `pipeline/process_viirs.py:2284` y
  `pipeline/process_modis.py:1580`, con formato `%Y-%m-%d %H:%M` en UTC: `[:10]` es la fecha UTC.
- `run_pipeline.py` itera fechas UTC y `fetch.py:512` busca con `temporal=(date_str, date_str)`. La
  documentación de earthaccess instalada dice que un `date_to` sin hora cubre el día entero hasta
  `23:59:59`. CMR devuelve gránulos que SE SOLAPAN con el día, así que buscar el primer día D de una
  ventana puede traer el gránulo que empieza en D-1 a las 23:5x y cruza la medianoche (en Chile es de
  noche). Ese record sale con fecha D-1: el filtro del trozo lo descarta (como antes del cambio) y la base
  conserva su versión. Es coherente con "fuera de las ventanas no se toca" y no hay un record que caiga
  entre dos sillas.
- `scripts/split_date_window.py` arma trozos contiguos, disjuntos y cerrados en los dos extremos, en ISO;
  el filtro del script también es cerrado. Comparación lexicográfica válida.

### 6. Parseo del nombre del artefacto

Los nombres de `volcanoes.yaml` que pueden ir en `volcanoes` no tienen guiones ni dígitos (los con espacio,
como "Lago Villarrica", son zonas). `sed "s/^chunk-$VOL-[0-9]*-//"` deja `AAAA-MM-DD_AAAA-MM-DD` y
`${W%%_*}` / `${W##*_}` lo parten bien. Ningún volcán es prefijo de otro seguido de guion, y el archivo
interior tiene que llamarse `$VOL.json`, así que el glob no mezcla volcanes. La mutación Y4 (ventana
invertida) se atrapa.

### 7. Los records conservados quedan idénticos byte a byte

Prueba sobre un archivo real, `data/_s154_reproc_k_historico/Lascar.json` (5.390 records, 0 claves
duplicadas, 2.136 instantes con más de un record por tener varios sensores a la misma hora), con un trozo
realista (el archivo completo con un record cambiado dentro de una ventana de 21 días). Salida:
`base: 5194 records conservados fuera de las ventanas, 196 dentro`, `fuera identicos (texto, orden): True
5194`, y con un trozo sin cambios `sin cambios byte a byte: True 14453522`. `pipeline/store.py:255` escribe
con `json.dump(store, f, indent=2)`, igual que el script, sin salto final en ninguno de los dos.

Condiciones en que NO quedan idénticos: (a) la base tiene dos records con la misma clave (el dict deja uno;
el store deduplica, así que no debería pasar, y en Lascar hay 0); (b) el campo `updated` del archivo cambia
siempre que entra un trozo más reciente (es de nivel superior, no de un record).

### 8. La batería de mutaciones clasifica bien en lo que corrió

Leí `resultado_mutaciones.json`: control sin mutación limpio sobre 28 pruebas; 13 ATRAPADAS, 2 CAIDAS
(control y Y6), 2 SOBREVIVEN declaradas equivalentes (S7, S10). Coincide con el README.

- Y2 (unir contra el checkout del despacho) se rotula ATRAPADA, y está bien: con la mutación, el push se
  rechaza, la vuelta 2 vuelve a unir sobre el árbol ya commiteado, sale `no changes` y el paso termina en 0
  sin haber subido nada. La prueba lo atrapa por aserción sobre main. Es justo el modo de falla que importa
  (verde sin datos).
- Dos huecos teóricos del clasificador, que no afectan a estos 17 resultados: una prueba del tipo
  `assert main(...) == 0` donde `main` atrapa un `ValueError` y devuelve 1 se contaría como ATRAPADA aunque
  sea una caída del código; y un `pytest.raises` que no se cumple ("Failed: DID NOT RAISE") se contaría
  como CAIDA aunque sea aserción. `grep pytest.raises` en los dos archivos de prueba no da nada, así que hoy
  no aplica.
- No hay mutación para `rm -f "$BASE"` ni para el `cp` de la base. Ver hallazgo 2.

### 9. Otros consumidores del script y del paso

`grep -rn merge_chunk_stores` fuera de los archivos del cambio: sólo
`.github/workflows/reproc-s124-villarrica-op-ab.yml:141`, que no pasa `--base` y conserva el comportamiento
de antes (único cambio sin base: la clave de orden pasa a `r.get("datetime_utc") or ""`, que sólo difiere
cuando el campo es `None`, caso que antes lanzaba `TypeError`). El guard
`test_g4_pusher_a_main_tiene_push_main_o_retry` (regex del bucle de reintento) y las pruebas que leen
`reproc-chunked.yml` (`test_reproceso_historico_k_s154`, watchdogs S133 y S157) pasan: `59 passed`.
`scripts/reemplazar_ventana_reproceso.py` reemplaza por ventana, así que los records que ahora se conservan
fuera de la ventana del perfil aislado no le llegan.

## Hallazgos, por gravedad

### Defectos del cambio

1. **Menor (razonamiento escrito falso, el comportamiento no cambia).** El comentario de
   `scripts/merge_chunk_stores.py` ("una pasada que ya no sale es parte de su resultado") y el README
   ("aunque el trozo no traiga una pasada que la base sí tenía (es el resultado del reproceso)") suponen que
   el JSON del trozo contiene sólo lo que el reproceso produjo dentro de su ventana. No es así:
   `store.append_record` nunca borra (`pipeline/store.py:650-694`, con `--overwrite` sólo reemplaza por
   clave), y el trozo parte del checkout del despacho. Una pasada que el reproceso no volvió a producir (por
   ejemplo, un corte de CMR en un trozo verde) sigue en el trozo con su versión del checkout. Lo que de
   verdad se descarta dentro de las ventanas son sólo los records que main ganó DESPUÉS del despacho, que es
   el caso que "Lo que NO cubre" ya declara. La prueba `test_base_conserva_las_ventanas_que_la_corrida_no_toca`
   modela un trozo que "pierde" una pasada, situación que un trozo real no produce. Conviene corregir la
   frase para que nadie la use para concluir que el merge limpia pasadas viejas.
2. **Menor (fragilidad).** Bajo `set +e`, si el `cp` de la base fallara, el script recibiría una base
   inexistente, avisaría y uniría sin base: el archivo saldría sólo con las ventanas, que es el borrado que
   el cambio vino a evitar. Lo mismo si main perdiera el archivo por otra razón. Probabilidad baja; se
   cerraría con `cp ... || return 1` y sin mutación que lo vigile hoy.
3. **Información.** El push desde clon superficial está verificado contra un receptor git local por
   `file://`, no contra GitHub (SIN VERIFICAR en GitHub).

### Ya existía antes del cambio (no es defecto de este PR)

4. **Perfil cuyo directorio no se llama como el perfil.** `experimental` escribe en `experimental_v2`
   (verificado leyendo `output.data_subdir` de todos los perfiles: `experimental -> experimental_v2`), y
   `data/experimental/` existe en el repo. Despachado con ese perfil, el reproceso escribe en
   `experimental_v2`, el artefacto sube el `data/experimental/<Vol>.json` viejo sin error
   (`if-no-files-found` no se activa) y el merge termina en `no changes`: corrida verde que no produce nada.
   La guarda del plan sólo exige un directorio aislado, no que se llame como el perfil.
5. **Dentro de las ventanas viajan records del detector anterior.** Por la misma razón del hallazgo 1, una
   pasada que el reproceso perdió queda con la versión del checkout, que puede ser de otro detector. El
   cambio no lo empeora ni lo arregla.
6. **El gránulo que cruza la medianoche al inicio de una ventana** se reprocesa y se descarta; queda su
   versión vieja (ahora, de la base). Coherente con la regla, pero esa pasada no se renueva en esa corrida.
