# Caminos por los que cada afirmación podría estar mal (escrito ANTES de leer el diff ni la evidencia)

Hora del servidor (cabecera `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`): Tue, 27 Oct 2026 17:50:13 GMT.
Commit medido: 026b5016d5d63b728d270d00e3cff1322efd8e5b. Tag `pre-s165-via-375` = cfff165443059dfc977e94894e5a880c1e911792.
Disco al empezar: C: 12,56 GB libres, D: 5,36 GB libres.

## A1 (flag apagado = bit a bit con el tag en 3 perfiles)
1. El script bit a bit compara dos corridas del MISMO código (HEAD contra HEAD) y no HEAD contra el tag: la comparación no puede fallar.
2. La copia «de referencia» se tomó de `origin/main` local atrasado, o de un commit distinto del tag.
3. La muestra no contiene el fenómeno: pocas pasadas, sólo un volcán, sin detecciones, sin pasadas diurnas, sin NaN, sin saturación, sin pasadas sin grilla.
4. La comparación ignora campos (lista blanca de claves) o redondea; «bit a bit» es en realidad «aproximadamente».
5. La prueba `test_flag_apagado_bit_a_bit_con_k_de_antes` pasa por construcción: compara contra un golden generado con el código ya cambiado, o monkeypatchea la misma función en los dos brazos.
6. Los perfiles `experimental*` heredan `thresholds` por otra ruta y el flag queda encendido en uno sin que el YAML lo diga.
7. El cambio toca código fuera de `calculate_vrp` (helpers, `store.py`, `run_pipeline.py`) y el bit a bit sólo mide `calculate_vrp`.
8. Orden de evaluación: el código nuevo cambia el estado aleatorio, el orden de un dict o un `argsort` inestable (A/B con dos pipelines, S152) y el bit a bit no lo detecta porque usa una sola máquina.

## A2 (flag leído de `thresholds:` vía `pipeline.profile`; ninguna ruta con el flag apagado)
1. El flag se lee con `.get()` de otra sección (raíz del YAML) en algún sitio, igual que `enable_utm_regrid` en S124 (A89).
2. Un default `True` en `pipeline.profile` o en un `getattr(profile, ..., True)`.
3. Un segundo punto de entrada (`process_viirs.py` tiene más de una función pública; `run_pipeline.py`; scripts de reproceso; el workflow NRT) que importa la vía directamente sin consultar el flag.
4. Un `import` de la vía con efectos secundarios en módulo (por ejemplo cargar grillas, cambiar constantes globales compartidas con V750/MODIS).
5. Nombre del flag distinto entre YAML, `profile.py` y el procesador (subcadena, mayúsculas); el guard busca el nombre de la definición, no el de uso.
6. El flag se evalúa por volcán pero la vía corre por gránulo, o al revés.

## A3 (números del port: 3,74 / 11,45 µm; 1,80e7 x 0,140625 / 1e6; grilla 134 x 134 de 375 m)
1. Los números están en la vía pero el port de referencia mismo tiene otros (hay que leer `SENSORES["VIIRS375"]` hoy, no confiar en la cita).
2. Hay dos copias de las constantes (por ejemplo en `pipeline/mirova_v750_codigo.py` y en `process_viirs.py`) y sólo una coincide.
3. La longitud de onda se usa en µm en un sitio y en m en otro; Planck se evalúa con la banda equivocada (I5 en vez de I4) o con los centros de VIIRS 750 (4,05 / 10,76).
4. El coeficiente 1,80e7 × 0,140625 / 1e6 = 2,53125 debería coincidir con el k = 2.531.250 de CLAUDE.md dividido por 1e6; si la vía lo usa en otra unidad (MW vs W), el VRP sale 1e6 veces distinto.
5. La grilla 134 x 134 define el ROI pero el centro no es el de MIROVA (`mirova_center`) sino el cráter, o la celda central está desplazada en 1 (paridad de 134: no hay celda central exacta).
6. El paso de 375 m es nominal; el port puede remuestrear en UTM y la vía en lat/lon.

## A4 (caja celda por celda igual a `brazos.py::caja(..., "C13", ...)` en los 11 volcanes)
1. La comparación corre sobre la misma función (la vía importa `brazos.py` o al revés): pasa por construcción.
2. Se compara en una sola orientación de la grilla (fila/columna) y la caja es simétrica: una transposición pasaría igual.
3. Sólo se probó con los 11 volcanes que tienen grilla pero la vía puede recibir otro volcán y producir una caja distinta de vacío.
4. La caja «C13» del experimento no es la que decidió el pre-registro §7 (puede haber C11, C13, C15); el autor eligió la que calza.
5. NaN de celdas excluidas: `brazos.py` puede marcar exclusiones (NaN en BOX) que la vía no reproduce, y la comparación convierte NaN en False.

## A5 (vía detecta igual que el port en 2.012 de 2.012; VRP calza con relleno MATLAB; NO EQUIVALENTE con atribución 40 + 8)
1. La muestra de 2.012 no incluye pasadas diurnas, saturadas, con nube, de borde de swath o con sun glint: la equivalencia vale sólo donde no pasa nada.
2. «Misma máscara» se mide después de aplicar a ambos la misma máscara (comparación circular).
3. Las 40 diferencias de VRP se atribuyen al «relleno viejo del port» sin haber corrido el port con el relleno nuevo: atribución por argumento, no por medición.
4. Las 8 de publicación: «regla de posición de la vía» puede ser un cambio de comportamiento que el pre-registro no autorizó; hay que leer §3 y §7 y ver si la regla está pre-registrada o se decidió después de ver el resultado.
5. El JSON de salida se generó con una versión anterior del script o de la vía (comparar mtime y contenido con lo que yo re-corra).
6. El criterio pre-registrado puede estar definido de forma que NO EQUIVALENTE sea inevitable o imposible; comprobar que se evaluó el mismo criterio.
7. Las grillas guardadas de los lotes fueron producidas por el port (mismo gránulo, A109): comparar contra ellas es comparar contra sí mismo para la parte de la grilla; sólo la detección y el VRP son independientes.
8. Los records VRP de la vía pueden calzar con MATLAB sólo en los casos sin NaN en el halo.

## A6 (`store.py` no calcula `f5_core_vrp_mw` cuando `via_codigo_mirova is True`; lo demás igual)
1. El bit a bit del almacén se corrió contra `origin/main` local, que puede ser más viejo o más nuevo que el tag.
2. La comparación del almacén no incluye records con `via_codigo_mirova == "sin_grilla"` ni con `via_codigo_mirova` ausente en records viejos (clave faltante vs `None` vs `False`).
3. `is True` contra un valor que viene de JSON (puede ser `1`, `"True"`) tras un ciclo de serialización.
4. Otro consumidor de `f5_core_vrp_mw` (frontend, `banco_paridad`, scripts de auditoría) hace fallback a `pc.vrp_mw` cuando el campo falta, y para la vía ese fallback es incorrecto o inexistente.
5. Un record de la vía que entra al almacén con un `f5_core_vrp_mw` viejo (auto-upgrade NRT a Standard, `store.py` mergea records) conserva el campo anterior.

## A7 (`via_codigo_mirova: "sin_grilla"` con flag encendido y sin grilla; `True` con la vía corriendo)
1. El campo se escribe en un dict que luego se sobreescribe o se filtra en `store.py` (lista blanca de claves).
2. Mezcla de tipos (`True` booleano y `"sin_grilla"` cadena) rompe un consumidor que hace `if record["via_codigo_mirova"]:` (la cadena es truthy).
3. Cuando el flag está apagado el campo no existe (o es `False`); los tres estados no se distinguen aguas abajo.
4. «Sin grilla» se decide por nombre de volcán con alias (A14): un volcán con grilla bajo otro nombre cae en K.

## A8 (batería de mutaciones atrapa por aserción; controles)
1. Mutaciones «atrapadas» por caída (excepción) y no por aserción (S152); el control de caída debe existir y la batería debe distinguir.
2. Las mutaciones se aplican sobre una copia del árbol que no es HEAD (`copia_mut` puede estar atrasada).
3. La salida que está en el repo puede ser de otra corrida; re-correr yo.
4. Mutaciones cosméticas (cambiar una constante que no se usa) cuentan como atrapadas porque otra prueba falla por otra razón.

## A9 (VIIRS 750 y MODIS no cambian aunque se tocó la vía compartida)
1. Cambios en `mirova_v750_codigo.py` (firmas, defaults, constantes de módulo) alteran V750/MODIS sin que una prueba lo mida; sólo hay bit a bit de V375.
2. Las pruebas de V750 y MODIS existentes comparan contra goldens que se regeneraron en este mismo commit.
3. Un parámetro nuevo con default cambia el orden de argumentos posicionales de un caller de V750/MODIS.
4. Con el flag de V750/MODIS encendido en algún perfil, la vía compartida corre en producción y el cambio llega al NRT aunque el flag de V375 esté apagado.

## Transversales
- El tag `pre-s165-via-375` podría no ser `origin/main` al momento del cambio (comprobar `git merge-base`).
- Copias locales atrasadas de grillas de lotes (mtime, cantidad de archivos).
- Pruebas que pasan por subcadena (A92).
- Suite corrida con el árbol en movimiento (A112): hay otros procesos de solo lectura; comprobar que ninguno escriba.
- Guiones largos, rutas relativas, etc. no son hallazgos de código, pero sí de documentación.
