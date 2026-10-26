# Verificación del cableado de la vía «código MIROVA» (flag apagado), commit 3a02ad28f

- Hora del servidor al inicio: Mon, 26 Oct 2026 12:14:02 GMT (`gh api -i repos/MendozaVolcanic/VRP-chile`).
- Commit verificado: 3a02ad28ff979d5f7c913347819b201a2fad589a (rama s162-via-mirova); base b09a7b321 = origin/main (re-comprobado con `git fetch`, sigue siendo b09a7b321).
- sha256 de la lista previa (escrita antes de abrir el diff): `c26c7486a47559179344fc010da4751d38568efca40c9f4eb6d5e13f5849e135` (`LISTA_CAMINOS_previa.md`, misma carpeta).
- Modelo: Sonnet 5.5, verificador con contexto limpio (no vio la sesión que escribió el cambio).
- NO miré: la corrección numérica de la vía en sí (detector, fillmissing2, remuestreo; eso es la equivalencia contra el oráculo y otro frente); un día real del NRT (no hay gránulos ni token local y el workflow propuesto no se despacha); la suite completa del repo (corrí sólo las pruebas del cableado, del módulo, del almacén, la golden de apagado S142, GR1 y el guard S131); el tablero con records de la vía; la aprobación de Nicolás (la cita el commit, no la vi); el estado de CI de la rama remota.
- Árbol: el worktree no se tocó. Mutaciones y comparaciones con la base se hicieron sobre copias en `C:\vrp-trabajo\vc_tmp\` (fuera del repo).

## En una pantalla

**Veredicto: LISTO CON CAMBIOS (ninguno toca el código A45; la afirmación central se sostiene).**

1. Con el flag apagado el cableado no cambia nada: el AST de `store.py`, `process_viirs_mod.py` y `profile.py` es idéntico al de b09a7b321 una vez quitado lo marcado como nuevo (con control positivo); el arnés sintético S142 da hash idéntico en helpers, V375, V750 y MODIS; y 1.800 records reales pasados por el almacén con la marca en False/None/"sin_grilla"/1/"true"/0 dan lo de hoy en los 45 volcanes.
2. Con el flag encendido, un record con `via_codigo_mirova is True` sale igual que el mismo record sin marca con las tres compuertas desactivadas a mano, en los 45 volcanes (control: con las compuertas activas difiere en 25); un volcán sin grilla corre K y queda con `"sin_grilla"` (probado ejecutando, no sólo leyendo texto).
3. Dos huecos de prueba, sólo con el flag encendido: ninguna prueba del repo atrapa que `is True` pase a truthiness (VC-01) ni que se restaure el filtro de píxeles por distancia. Hoy el código es correcto.
4. Documentación: la ficha SDA v1.13 dice que la conexión NO se incorpora y este commit la incorpora (VC-03); las citas `process_viirs_mod.py:N` de MISSION.md y MIROVA_DIVERGENCES.md quedan corridas 35 líneas (VC-04).
5. No verificado: un día real del NRT (el comparador propuesto puede dar VERDE sin ver un solo record V750, VC-05) y la aprobación de Nicolás que cita el commit (SIN DATO).

## Hallazgos (ordenados por gravedad)

### VC-01 · Dos de las compuertas saltadas y la estrictez de `is True` no tienen prueba que las vigile
- Dónde: `pipeline/store.py:357` (`_via_mirova = record.get("via_codigo_mirova") is True`) y `:362` (filtro de píxeles por distancia). Pruebas: `tests/test_mirova_v750_cableado_s162.py`.
- Qué pasa: mutaciones sobre una copia de 3a02ad28f (ver `mutaciones_vc.md`). M2: cambiar `is True` por `bool(...)` deja 7 de 7 verdes. M4: quitar `and not _via_mirova` del filtro de píxeles deja 7 de 7 verdes. En cambio M3 (geocerca), M5 (tope por cúmulo) y M1 (`if True:` en el procesador) sí caen.
- Cómo se ve: M2 es la grave. Con el flag encendido, todo record K de un volcán sin grilla lleva `via_codigo_mirova: "sin_grilla"`; si alguien "simplifica" a truthiness, esos records K saltarían las tres compuertas y publicarían sin geocerca ni tope, y ninguna prueba lo diría. El código de hoy es correcto: `vc_store_real.py` (c) pasa 1.800 records reales con marcas False/None/"sin_grilla"/1/"true"/0 y dan lo de hoy en 45 de 45 volcanes.
- Cómo reproducir: `mutaciones_vc.md` (sobre copia en `C:\vrp-trabajo\vc_tmp\mut`) y `python experiments/_s162_v750a/verificador_cableado/vc_store_real.py`.
- Confianza 5 · Gravedad 3 (sólo aplica con el flag encendido; hoy inerte). Arreglo sugerido: una prueba parametrizada con marca `"sin_grilla"`/`1` que exija el vrp de K, y una con anomaly_pixels lejanos que exija el filtro aplicado a K y no a la vía.

### VC-02 · La ficha SDA v1.13 contradice al commit que la acompaña
- Dónde: `docs/FICHA_SDA_VRP_CHILE.md:49` (fila v1.13). Dice: «La conexión de la vía al procesador y al almacenamiento queda propuesta aparte y no se incorpora sin la aprobación expresa del responsable»; su columna de trazabilidad lista sólo el módulo, el yaml y las pruebas del módulo.
- Qué pasa: el commit 3a02ad28f sí incorpora la conexión (apagada) en `process_viirs_mod.py`, `store.py` y `profile.py`. La ficha es el documento de transparencia algorítmica (Res. CPLT N°372) y queda diciendo lo contrario de lo que hay en el código.
- Cómo se ve: `git diff --stat b09a7b321 3a02ad28f` muestra los tres archivos A45 modificados; la fila v1.13 no los menciona.
- Confianza 5 · Gravedad 2. Arreglo: reescribir esa frase («incorporada, apagada») y agregar los tres archivos a la trazabilidad.

### VC-03 · El comparador del NRT propuesto puede dar VERDE sin haber visto un solo record de V750
- Dónde: `experiments/_s162_v750a/comparar_bitabit_nrt.py` y `probe-s162-bitabit-nrt.yml`.
- Qué pasa: el comparador imprime totales pero no por sensor, y sólo da SIN DATO si los dos archivos están vacíos. Un día donde falle la descarga de V750 (run_pipeline captura la excepción por gránulo y sigue) deja a las dos ramas con MODIS y V375 y el resultado es VERDE sin haber ejercido el procesador que se cambió. Además `a` y `b` corren una después de la otra: una pasada que NASA pase de NRT a Standard entre las dos daría un ROJO ajeno al código. La marca de régimen no es problema: con `GITHUB_SHA` presente (Actions) los dos árboles escriben el mismo `codigo_sha` (`pipeline/store.py:91-93`).
- Cómo se ve: leído del código, no ejecutado (SOSPECHA parcial).
- Confianza 4 · Gravedad 2. Arreglo: exigir un mínimo de records `*_750` en cada lado, imprimirlos por sensor y salir con 2 si no hay.

### VC-04 · Citas `archivo:línea` a `process_viirs_mod.py` corridas 35 líneas y fuera del guard
- Dónde: `docs/MISSION.md:332` (`process_viirs_mod.py:1069`) y `docs/MIROVA_DIVERGENCES.md` líneas 512 (705/713), 892 (2455), 1012 (2863), 1321 (460), 3238 (640). El bloque nuevo (l. 495-523) y el final (l. 1543-1545) corren todo lo que hay debajo de la l. 493.
- Qué pasa: el autor remapeó sólo las dos citas que vigila el guard S131 (CLAUDE.md, 163 a 164 y 466 a 467). Comprobé tres con `sed`: en la base la l. 1069 es `sorted_indices = orden_vrp_descendente(...)`; en la rama la l. 1069 es un comentario de Wooster y la línea equivalente está en la 1105 (igual con 892 y 1012). Las otras citas, por la misma aritmética (SOSPECHA).
- Confianza 5 (las tres comprobadas) · Gravedad 1 (A101: remapear por contenido con `scripts/remapear_citas.py`).

### VC-05 · El flag sólo vale bajo `thresholds:`; en la raíz del YAML se ignora en silencio
- Dónde: `pipeline/profile.py:902` (`_t.get("enable_v750_codigo_mirova", False)`, con `_t = _cfg["thresholds"]`).
- Qué pasa: probado sobre una copia del cargador (`C:\vrp-trabajo\vc_tmp\prof`): la clave bajo `thresholds:` da True; la misma clave en la raíz da False. Es la trampa A89/S124. Está documentada en el comentario y apagado es el comportamiento seguro, pero quien lo encienda mal creerá que lo encendió.
- Confianza 5 · Gravedad 1. Seguimiento para el día de encenderlo: leer el valor efectivo desde `pipeline.profile`, nunca el YAML.

### VC-06 · El volcán se reconoce por igualdad de coordenadas a 1e-6 grados (sólo flag encendido)
- Dónde: `pipeline/mirova_v750_codigo.py:113-121`, llamado desde `pipeline/process_viirs_mod.py:506`.
- Qué pasa: verificado ejecutando: los 45 volcanes de volcanoes.yaml con coordenadas del yaml envían a la vía exactamente los 11 con grilla y los otros 34 a K; no hay coordenadas duplicadas; hoy ningún perfil sobrescribe `lat`/`lon` (`VOLCANO_OVERRIDES` no los toca). Pero un `np.float32` de las coordenadas de Llaima da `None`, y un perfil que sobrescribiera lat/lon haría que un volcán con grilla corra K con la marca `"sin_grilla"`: no es silencioso (queda marcado), pero sería un volcán que creemos en la vía y no lo está.
- Confianza 5 · Gravedad 1 (hoy inerte y marcado).

### VC-07 · Imprecisión menor en la redacción de la afirmación
- «Lo único que agrega fuera de ese bloque es una variable que queda en False» es casi cierto: fuera del `if` hay además el nombre importado en la cabecera (`process_viirs_mod.py:75`) y un `if _via_sin_grilla:` al final (`:1543`), ambos inertes con el flag apagado. El AST lo confirma: quitando exactamente esos cuatro elementos queda el AST de la base.
- Confianza 5 · Gravedad 1.

## VERIFICADO LIMPIO (contra qué vara)

- **Código de producción con flag apagado = base** (vara: AST de `git show b09a7b321:<archivo>`). `ast_equivalencia.py`: `store.py`, `process_viirs_mod.py` y `profile.py` idénticos tras quitar sólo `_via_mirova` y los `and not _via_mirova`, el import del flag, `_via_sin_grilla = False`, el `if ENABLE_V750_CODIGO_MIROVA:` y el `if _via_sin_grilla:` final. Control positivo: sin quitar el `and not`, da distinto.
- **Efecto extremo a extremo con el arnés S142** (vara: la misma escena sintética corrida con el código de la base extraído por `git archive` a `C:\vrp-trabajo\vc_tmp\base`): `--solo helpers|v375|v750|modis`, los cuatro JSON con el mismo sha256 en base y rama.
- **El golden de apagado ya existente** (`tests/test_apagado_no_cambia_nada_s142.py`, 8 pruebas) pasa en la base y atrapa las mutaciones M6 y M7 (marca "sin_grilla" en todo record), que `cableado_s162` no atrapa: la protección de «ningún record cambia con el flag apagado» existe en la suite.
- **Pruebas**: `test_mirova_v750_cableado_s162.py`, `test_mirova_v750_codigo_s162.py` y `test_guard_declarado_vs_efectivo_s131.py`: 64 de 64 verdes. Aparte, 84 de 84 en golden S142, GR1 y los 9 archivos de pruebas del almacén.
- **Flag**: ningún YAML de `pipeline/profiles/` (incluido `_archive`) contiene `enable_v750_codigo_mirova`; por defecto False; leído bajo `thresholds` (probado con control, VC-05). `ENABLE_V750_CODIGO_MIROVA` es False en `mirova_equivalent` (`vc_flag_salida.txt`, E1).
- **Sin efectos al importar**: tras `import pipeline.process_viirs_mod, pipeline.store`, `pipeline.mirova_v750_codigo` no está en `sys.modules` (E1). El módulo de la vía no importa nada de `pipeline` (sin circularidad); `yaml` y `h5py` se importan dentro de funciones.
- **Nadie más produce la marca**: `grep -rn via_codigo_mirova` sobre el repo (excluyendo docs y esta carpeta) sólo da `mirova_v750_codigo.py:618`, `process_viirs_mod.py:1545` y `store.py:357`; cero apariciones en `data/`, `.github/`, `pipeline/profiles/`, `frontend/`. `store.py` no usa la marca en ningún otro sitio.
- **Alcance de edición**: el diff no toca `run_pipeline.py`, `.github`, perfiles, frontend ni datos; `git diff --check` limpio, sin CRLF añadidos. La firma de `calculate_vrp` (AST) y `test_gr1_viirs_parity` sin cambio.
- **Almacén, flag encendido** (`vc_store_real.py`, 1.800 records reales, 40 por volcán, 45 volcanes): (a) record marcado == mismo record sin marca con filtro de píxeles apagado, `max_hotspot_dist_km=1e9` y `max_cluster_pixels=None`: 45 de 45; (b) control: marcado != hoy en 25 de 45 volcanes (la comparación puede ver el cambio); (c) marcas False/None/"sin_grilla"/1/"true"/0 == hoy: 45 de 45. O sea: salta exactamente esas tres y nada más (el resto del almacén, A46, Regla D, piso, tope sanitario y geo_class, sigue aplicándose).
- **Despacho por volcán, flag encendido** (E2): exactamente los 11 volcanes de `grillas_mirova.yaml` entran a la vía; los 34 restantes llegan al lector de K. Con el flag apagado, 45 de 45 al lector de K y la vía nunca se toca.
- **Volcán sin grilla marcado** (E3): sobre la escena V750 del arnés (coordenadas que no son de ningún volcán), el record con flag encendido difiere del de flag apagado sólo en la clave `via_codigo_mirova = "sin_grilla"`; con flag apagado la clave no existe.
- **Vía de punta a punta en Llaima** (E4, escena sintética con las coordenadas del yaml, lectores parchados): devuelve record con `sensor`, `vrp_mw`, `t_bg_k`, `t_max_k`, `n_anomalous_pixels`, `granule`, `product_version`, `datetime_utc`, que son las claves que `run_pipeline.py` lee después de `append_record`; no hay `KeyError` tardío tras guardar. E5: ese record pasa por el almacén igual que sin marca con las tres compuertas apagadas.
- **A45**: existe el tag `pre-s162-via-mirova` (remoto, apunta a deaf8f59b) y `store.py`, `process_viirs_mod.py` y `profile.py` son idénticos en ese tag y en b09a7b321.

## SIN DATO

- La aprobación explícita de Nicolás para tocar archivos A45: el commit y la docstring de la prueba la citan relayada por S163; no la vi ni podía verla desde aquí.
- El efecto sobre un día real del NRT: sin token ni gránulos locales y el workflow no se despacha. Lo cubren el arnés sintético, los records reales y el AST, no gránulos reales.
- `bitabit_store.py` y su salida (6.143 iguales, control 32 de 45): los leí, no los re-corrí; mi `vc_store_real.py` y el AST dan la misma conclusión por otro camino.
- Cómo se ve un record de la vía en el tablero (`mirovaEqVrp`, `isValidDetection`): fuera de alcance; con el flag apagado no existe tal record.
- El estado de CI de la rama remota.

## SEGUIMIENTOS

1. Antes de encender el flag: las dos pruebas de VC-01 (marca `"sin_grilla"` y filtro de píxeles) y el ajuste del comparador de VC-03; se repite la regla A45 (tag defensivo y confirmación explícita) para encender.
2. Corregir la frase de la ficha v1.13 y su trazabilidad (VC-02) antes de publicar la ficha.
3. Remapear las citas de MISSION.md y MIROVA_DIVERGENCES.md (VC-04) con `scripts/remapear_citas.py`.
4. Cuando se encienda, leer el valor efectivo de `pipeline.profile.ENABLE_V750_CODIGO_MIROVA` y no el YAML (VC-05).
5. Archivos de esta verificación (todos en `C:\vrp-trabajo\s162-via-mirova\experiments\_s162_v750a\verificador_cableado\`): `LISTA_CAMINOS_previa.md`, `ast_equivalencia.py`, `vc_flag.py` y `vc_flag_salida.txt`, `vc_store_real.py` y `vc_store_real_salida.txt`, `mutaciones_vc.md`. Las extracciones de la base y las copias mutadas viven en `C:\vrp-trabajo\vc_tmp\` (fuera del repo); el worktree quedó sin cambios salvo esta carpeta nueva.
