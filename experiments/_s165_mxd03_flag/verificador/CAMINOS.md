# Caminos por los que cada afirmación podría estar mal (escrito ANTES de leer el PR)

Hora del servidor (gh api, header Date): Tue, 27 Oct 2026 17:27:09 GMT
Commit a medir: 4164d4547 (rama claude/s165-mxd03-flags); base d94f25191; tag pre-s165-mxd03-modis = 9e61eecfed398bce35a3de75b4b6e993ebf3ea58 (OJO: el tag NO apunta a d94f25191 segun `git rev-parse`; comprobar si es tag anotado y a que commit apunta).

## A1 (apagado bit a bit con el tag)
1. El golden `apagado_antes.json` se generó con código ya tocado (o desde el commit 7a806ffae, que ya pudo incluir cambios), no desde el tag.
2. El arnés sintético no ejerce los caminos que el PR tocó (por ejemplo, nunca entra a la rama donde el cráter cae fuera del gránulo, nunca usa `_interp_geo` con offset, nunca calcula `dist_km` de etiqueta).
3. «bit a bit» se mide con tolerancia (`approx`, redondeo, `round(…, 6)`) o sobre un subconjunto de claves del record, no sobre el record completo.
4. El test compara el golden contra la salida actual pero el golden se regenera automáticamente si falta (test que escribe su propia referencia).
5. Las «escenas S142» pueden estar cacheadas o ser un fixture que no pasa por `calculate_vrp` completo (por ejemplo, llaman a una función interna).
6. Determinismo: campos como `processed_utc`, rutas o versión de código se excluyen; hay que ver qué se excluye y si entre lo excluido hay algo que el PR cambia.
7. El test corre con el perfil por defecto y los flags leídos de `pipeline.profile` al momento del import; si el módulo se importó antes con otro perfil, mide otra cosa.
8. Tag anotado vs commit: «código del tag» podría ser el commit anterior al merge #919 u otro; verificar con `git rev-parse pre-s165-mxd03-modis^{commit}`.

## A2 (flags leídos de thresholds:, apagados en ambos perfiles)
1. `profile.py` lee la clave de la raíz o con `.get()` encadenado que acepta ambas secciones (A89 forma 2: la clave se lee de otra sección).
2. Los nombres en el YAML difieren de los nombres en `profile.py` (prefijo, sufijo, mayúsculas) y por eso «están apagados» por defecto y no porque el YAML lo diga.
3. `experimental.yaml` hereda del operacional por `extends` o similar y no se verifica que el valor efectivo sea False (A117: perfil derivado).
4. El guard verifica el YAML por texto (subcadena, A92) y no el valor efectivo de `pipeline.profile`.
5. Hay más perfiles (`experimental_ndc_focus`, `_f46_*`) que no se verifican.
6. El default en `profile.py` es True y el YAML lo apaga: si alguien borra la línea, se enciende.

## A3 (cada flag encendido hace lo que debe, llega a todos los consumidores)
1. Flag 1 (MxD03): `leer_mxd03` se llama pero `posicion_de_calculo` sigue usando `_interp_geo` en algún camino (segundo consumidor: el anillo de fondo, el cluster, el `final_hotspot`, el `vent_hotspot`, el second pass, el keep_peak focal, la vía código MIROVA).
2. Flag 1: el MxD03 se lee pero no se alinea con el gránulo (dimensiones distintas, bow tie, `_FillValue` -999 no tratado).
3. Flag 2 (sin dato): `sin_dato_de_geolocalizacion` devuelve True pero `calculate_vrp` igual escribe record (el caller ignora el retorno; o `store.append_record` escribe el None).
4. Flag 2: la regla «cráter sin posición» se evalúa con la posición interpolada vieja y no con MxD03 cuando el flag 1 está apagado (dependencia entre flags no declarada).
5. Flag 3 (distancia): `dist_de_etiqueta` cambia la distancia de `distance_class` pero `store.py` o el frontend leen otro campo (`final_hotspot_dist_km`, `hotspot_dist_km`, `vent_hotspot_dist_km`, `primary_cluster.dist_km`) y la etiqueta publicada sigue saliendo del viejo.
6. Flag 3: el anillo de fondo SÍ cambia porque la misma distancia alimenta `is_summit`/ROI1 o `inner_radius` mask (A118: un flag de geometría que no llega a todos los consumidores, o que llega a uno que no debía).
7. Los flags se leen una vez a nivel de módulo (`from pipeline.profile import X`) y los tests que «encienden» por monkeypatch de `pipeline.profile` no cambian nada (A89 forma 3).
8. El caller transforma el argumento (A6): `run_pipeline.py` pasa el ancla resuelta `get_detection_anchor()` y el flag 3 «desde el cráter» mide desde el mismo punto que antes en 10 de 11 volcanes (efecto nulo salvo Tupun/PCC/PP).
9. Los helpers de VIIRS (`process_viirs.py`, `process_viirs_mod.py`) no se tocan: ¿la etiqueta MODIS y la VIIRS quedan definidas desde puntos distintos?

## A4 (vía código MIROVA no cambia)
1. Las funciones nuevas se insertaron entre funciones existentes y comieron un `return` (A49).
2. La vía código MIROVA importa posiciones de `_interp_geo` directamente y, con flag 1 encendido, recibe posiciones distintas sin que nadie lo haya previsto.
3. No hay test que ejerza la vía con `enable_modis_codigo_mirova: true` + flags S165 apagados contra golden previo.

## A5 (mutaciones 22/22)
1. Mutación «atrapada» por caída (ImportError, SyntaxError, TypeError) y no por aserción (S152, S156): revisar la salida por tipo de excepción.
2. El control «viva» corre sobre árbol ya mutado o no restaurado.
3. El control de caída «caida» es trivial (sintaxis rota) y no prueba que el detector distinga caída de aserción.
4. Las mutaciones se aplican por reemplazo de texto y alguna no se aplicó (texto no encontrado, 0 reemplazos contados como mutación).
5. La batería edita `pipeline/` en el worktree y el `mutaciones_salida.txt` se generó con un árbol sucio o con la suite leída a medias (A112).
6. «1 declarada no cubierta» puede esconder más no cubiertas si la lista de mutaciones es corta frente a las ramas nuevas.
7. Las 22 están todas sobre un solo archivo o una sola función (cobertura desigual).

## A6 (223 de 5.465 sin dato)
1. El censo MOD-D es de otro commit o detector; la regla se midió sobre un dato que no es el de hoy.
2. «ninguna que K publicara» usa el predicado del evaluador y no el del dashboard (A97).
3. «1 alerta bajo 1 MW» depende de la referencia (CSV) de una fecha; el CSV local puede estar atrasado (A17).
4. 221 borde + 2 relleno: la clasificación borde/relleno se hace por un proxy (índice de columna) y no por el valor de MxD03.
5. El denominador 5.465 incluye pasadas diurnas o de 34 volcanes fuera del cron.
6. El script lee de D:\ y si falta un archivo, cuenta 0 sin error (A89).

## A7 (5 publicaciones cambian, todas PCC)
1. El script recomputa la etiqueta con el predicado del dashboard replicado en Python, no con el JS (A97).
2. «control de identidad 180 de 180» mide la identidad del instrumento sobre sí mismo (A110) y no que pueda dar distinto de cero.
3. La distancia «desde el cráter» se recomputa con `vent_lat/lon` de `volcanoes.yaml` de hoy, que puede diferir del usado al escribir el record.
4. La ventana 2026-03-01 a 2026-10-27 cruza la frontera K (A104) pero #883 reprocesó todo, así que vale; verificar.
5. «negativos limpios» exige el CSV de referencia: ventana de calidad A119.
6. Solo mira `data/mirova_equivalent/`: el copy local puede estar atrasado respecto a origin/main (A25).

## A8 (equivalencia con MOD-B)
1. El brazo X de MOD-B no es «MxD03 por píxel» sino otra cosa (por ejemplo, offset +2 en la interpolación).
2. La referencia extraída de los artefactos t1/t2/t3 mezcla brazos o toma la primera pasada del día.
3. El workflow usa credenciales de usuario y clave vencidas en vez de `EARTHDATA_TOKEN` (regla S146).
4. El workflow no cita `"on":` (A43) o no tiene `workflow_dispatch` en main.
5. El script compara con tolerancia pero el criterio dice «bit a bit».
6. La comparación apagado vs K no es contra el mismo gránulo (NRT vs Standard).

## A9 (suite 0 fallas)
1. Corrida con árbol en movimiento (A112) o con caché de pytest.
2. Tests que dependen de archivos fuera de git (D:\) y que se saltan en silencio (skip contado como OK).
3. Tests que fallan en Windows por pyhdf y se marcan skip: la suite «0 fallas» no ejercita MODIS real.

## Transversal
- La copia local del worktree puede no ser 4164d4547 (verificado arriba: sí lo es).
- El tag `pre-s165-mxd03-modis` resuelve a 9e61eecf, no a d94f25191: ver si es anotado.
