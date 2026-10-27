# CAMINOS: por donde podria estar mal cada afirmacion (escrito ANTES de abrir el codigo)

Verificador con contexto limpio. Commit medido: c4efdc78c. Base: tag pre-s16x-modis-codigo-mirova.
Hora del servidor al escribir esto: Tue, 27 Oct 2026 12:11:33 GMT (gh api -i repos/MendozaVolcanic/VRP-chile).

## A1. Flag apagado = bit a bit lo mismo que antes en process_modis.py

1. El golden `modis_k_antes.json` se genero con el codigo NUEVO, no con el tag base: la prueba pasa por construccion.
2. La fixture del golden no ejerce el camino alterado (p. ej. solo un record sin hot pixels, o un unico sensor/plataforma).
3. El flag se lee de otro lado que el que la prueba apaga (YAML raiz vs `thresholds:`; `pipeline.profile` vs `os.environ`), de modo que "apagado" en la prueba no es "apagado" en produccion.
4. Hay un segundo punto de entrada (store.py, run_pipeline.py, process_viirs_mod.py) que cambio con el flag apagado y la prueba solo mira process_modis.py.
5. El diff toca lineas fuera del bloque condicionado (imports con efectos, cambio de orden de evaluacion, redondeos, claves nuevas del record) y la comparacion bit a bit excluye claves o tolera floats.
6. "bit a bit" se compara con `==` sobre dicts con NaN (NaN != NaN) o con tolerancia; o se comparan solo unos campos.
7. `test_flag_apagado_no_toca_la_via` verifica que no se LLAMA la via con un mock, pero la via podria ejecutarse por un camino que el mock no intercepta (import directo, alias).
8. La prueba apaga el flag en un perfil y el default en OTRO perfil (experimental, ndc_focus) esta encendido.

## A2. Parametrizacion por sensor de mirova_v750_codigo.py no cambia VIIRS 750

1. La tabla FAMILIAS cambia un valor por defecto de la familia V750 (lambda, coeficiente, caja) respecto al valor literal anterior.
2. process_viirs_mod.py importa un nombre que ahora resuelve distinto (alias, firma con nuevo parametro con default distinto, orden de argumentos posicionales).
3. Hay un golden V750 que pasa por construccion (regenerado) o no existe golden para V750 y se afirma sin medir.
4. El cambio de firma rompe un `functools.partial` o un `**kwargs` en el caller sin que un test lo cubra.
5. Las pruebas de V750 existentes tienen el flag de V750 apagado, asi que no ejercen la via.

## A3. 5 grillas del censo: mismos pixeles, mismos numeros por pase, mismo VRP con relleno fillmissing2

1. Los "esperados" en esperado.json se calcularon con la misma via (circular) y no con el port del censo.
2. Las 5 grillas son todas del mismo volcan o todas sin alerta: el camino de alertas no se ejerce en varias.
3. Comparacion con tolerancia amplia, no igualdad.
4. La regla de fillmissing2 implementada no es la de MATLAB (desempate, vecinos diagonales, orden de relleno): 1,1124 vs 0,9731 sale de un cambio que no se valido contra Octave/MATLAB.
5. El "port con su propio desempate" tambien podria haber estado mal; la via nueva lo cambio y nadie comprobo cual es el correcto contra MATLAB.
6. Las grillas .npz de las fixtures no son las del censo (se regeneraron) o se recortaron.

## A4. Constantes MODIS son las del paper, produccion y port

1. lambda 3,959 es banda 22; el pipeline de produccion usa 21/22 y la via solo 22 (o viceversa) sin que la afirmacion lo diga.
2. 11,03 um para TIR: MODIS banda 31 nominal es 11,03; produccion podria usar otro valor (11,0 u 11,017).
3. Coeficiente 18,9 x 1e6 /1e6: el orden de magnitud o las unidades (W vs MW) se pierden en la conversion.
4. Caja 5x5 y 15x15 en celdas de 1 km: el paper habla de km o de pixeles; la caja del codigo V750 original es en celdas de 750 m y la tabla podria copiar celdas sin convertir.
5. El paper (sp426_5.txt) corrupto en la capa de texto: la cita hay que leerla con cuidado (A95).

## A5. Lectura y armado de la via = los del probe del censo

1. La funcion de lectura del probe y la de pipeline/ divergen en detalles (orden de bandas, escala/offset, tratamiento de sentinel 65533, mascara de validez).
2. Recorte de 45 km y corte de 5 km al centro: distinto centro (vent vs grid center vs mirova_center), distinta metrica (haversine vs plana).
3. dayflag/sunglint del pixel mas cercano: criterio de "mas cercano" distinto (indice de grilla vs distancia).
4. Remuestreo lineal: griddata vs LinearNDInterpolator, distintas tolerancias o rescale.
5. El probe leia MxD03 de un archivo y la via del NRT lo busca por otra ruta/producto (MOD03 vs MYD03, colecciones 6.1 vs 6.1NRT).
6. Sin HDF real en Windows no se puede ejecutar la lectura: la igualdad solo se puede comprobar por lectura de codigo o comparando con las salidas del censo en D:.

## A6. Fallback a K con motivo; store.py exime solo via_codigo_mirova is True

1. El record con la via fallida lleva via_codigo_mirova = False (o None) y store.py compara con `if record.get("via_codigo_mirova")` (truthy) o `is not None`, exonerando de mas.
2. El motivo no se persiste o se persiste con texto distinto segun el camino.
3. Alguno de los tres motivos (sin grilla, sin MxD03, forma distinta) lanza excepcion en vez de caer a K.
4. "corre K" significa que K produce un record; pero si K devuelve None la via podria devolver otra cosa.
5. store.py exime de "las compuertas de K": cuales exactamente; podria haber una compuerta en otro archivo (run_pipeline.py, frontend) no exenta ni documentada.
6. El record con via True sigue pasando por compuertas que no deberia (o viceversa) y no hay prueba.

## A7. Mutaciones 25/25 atrapadas; clasificador

1. El clasificador cuenta como "atrapada" cualquier salida no cero de pytest (incluida una excepcion de import o una caida) y no solo AssertionError.
2. Los controles (mutacion nula, mutacion que deberia escapar) no existen o estan en orden invertido.
3. Las mutaciones solo tocan constantes y no la logica de fallback, la exencion de store.py ni el remuestreo.
4. La salida en mutaciones_salida.txt no se reproduce al correr hoy.
5. Las mutaciones se aplican al archivo en el repo (no a una copia) y dejan residuo.

## A8. Fixtures del censo sin alterar; esperados por codigo independiente

1. armar_fixtures.py recorta, redondea o re-serializa (float32 vs float64) las grillas.
2. "Codigo independiente" importa funciones de la via (misma implementacion con otro nombre).
3. El md5/sha de las fixtures no se compara contra el censo en D:.
4. esperado.json se escribio a mano o con un script que ya no esta.

## A9. Suite 2640 passed, 29 skipped, 2 xfailed; CI de #919 verde

1. La cuenta cambia si se corre hoy (tests que leen docs, A112).
2. El CI de #919 corrio sobre otro commit que c4efdc78c.
3. Hay tests marcados skip que son justo los de la via (pyhdf), de modo que el verde no cubre la via.
