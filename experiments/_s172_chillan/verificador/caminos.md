# Caminos por los que cada afirmación podría estar mal (escrito antes de abrir ningún archivo citado)

Verificador de la sesión S172, Chillán. Sólo conozco título, dónde y gravedad de cada afirmación.

## CH172-01: razón de magnitud de Chillán cae con el cenit (MODIS, V375, V750)

1. El instrumento mide otra cosa: la «razón» puede estar calculada con un campo que no es el de la vara (por ejemplo primary_cluster.vrp_mw en V375 en vez de f5_core_vrp_mw con fallback; o record.vrp_mw que trae el tope D9 y la suma de escena).
2. Pareo con MIROVA: la tolerancia TOL_S de banco_paridad puede estar distinta, o el pareo puede ser por noche y no por pasada; con n 12 / 53 / 39 un pareo laxo mezcla pasadas distintas y el cenit del sensor no es el de la pasada de MIROVA.
3. Confusor: el cenit se correlaciona con otras cosas (cantidad de píxeles alertados, hora de la noche, estación, régimen anterior/posterior a #535 y a K, fecha de reproceso). Un Spearman global puede ser Simpson (el sensor/satélite NOAA-20 vs SNPP tienen órbitas distintas) o una deriva temporal de la actividad del volcán que coincide con la geometría orbital. La actividad real de Chillán cambió en el tiempo (erupción 2026), y el cenit cíclico de 16 días puede coincidir por azar.
4. n pequeño y muchas ventanas: Spearman -0,87 con n 12 es significativo pero frágil; «fuera del rango barajado» depende de cuántas permutaciones, de la semilla, y de si se barajó respetando la estructura (autocorrelación de pasadas del mismo día).
5. Pasadas repetidas del mismo día/noche cuentan como independientes (pseudo-replicación).
6. La ventana de datos puede mezclar detectores (antes y después de K, #850, 2026-09-18 por observación; antes y después de #883 reproceso; #535 máscara de nube; A104). Un cambio de régimen en la ventana fabrica una correlación con cualquier variable temporal; el cenit de una órbita repetitiva tiene periodicidad, pero un régimen escalonado sí correlaciona con él si el muestreo es desbalanceado.
7. El ángulo cenital «del sensor» puede estar sacado de un campo que es el cenit solar, o el ángulo de barrido, o el cenit de la geometría MxD03; y MODIS tiene el offset de geolocalización (_interp_geo) que afecta justo off-nadir.
8. MIROVA a su vez tiene su propio sesgo con el ángulo (remuestreo a 1 km): la razón puede caer porque MIROVA sube y no porque nosotros bajemos. Es decir, correlación con cenit no atribuye el lado.
9. La copia local del corpus está atrasada o es la de otro commit (data/mirova_equivalent/Chillán): la afirmación se midió sobre un corpus que ya cambió (A90).
10. Los 3 sensores comparten pasadas; no son tres confirmaciones independientes si la causa es de la misma noche.
11. El volcán: «Nevados de Chillán» tiene varias variantes de nombre en el CSV (A14: «Nevados de Chillan», «NevadosdeChillan»); pareo con alias perdido da n distinto.
12. D-9: alertas de V375 con VRP ≤0,05 MW no cuentan; si el auditor las incluyó o excluyó cambia n y la razón.

## CH172-02: las 3 alertas protegidas MODIS de Chillán que K pierde están a 57,6-58,2° de cenit y MOD-D las publica

1. «Protegida» = alerta de MIROVA ≥1 MW; ¿las 3 son de Chillán o de otro volcán? ¿son las únicas, o hay otras perdidas a otros cenit que el auditor omite? Un rango de 57,6 a 58,2 en 3 casos es una muestra mínima: casi cualquier 3 pasadas de la misma órbita repetida dan cenit parecido (la órbita se repite cada 16 días, mismo cenit); la concentración puede ser por muestreo, no por causa.
2. Falta la tasa base: ¿qué fracción de TODAS las pasadas MODIS de Chillán está a 57-59°? Si la mayoría de las pasadas están ahí, el 57,6-58,2 no distingue.
3. «K pierde» depende del campo con que se define «publica»: predicado del tablero (node) vs reconstruido. Y de la versión del corpus (K reprocesado #883).
4. La rama claude/s170-modd-f4-procedencia puede haber cambiado o ser de otra ventana; el resultado_f4.json es un artefacto de un brazo A/B (MOD-D) con su propia ventana y su propia definición de «publica». MOD-D «las publica» puede ser por mecanismo ajeno (p. ej. dejar de exigir una compuerta, o publicar todo lo que haya) y no por corregir el cenit.
5. Cenit leído de dónde: campo del record, o recomputado; el valor del cenit MODIS en el record puede ser el de un píxel distinto al del cúmulo.
6. Fecha de la alerta de MIROVA vs pasada: pareo con TOL_S.
7. D-9 y la lectura A/B de alertas.

## CH172-03 (SOSPECHA): V750, el fondo de anillo solo baja el port de MIROVA a 0,684 de MIROVA en Chillán (n 22), leído de V750-C

1. «Port de MIROVA» es el código MATLAB de MIROVA (OSF zm62w) portado a Python; «el fondo de anillo solo» es un brazo de ablación (S162: brazo que no hace lo que dice). ¿El brazo de verdad cambia sólo el fondo? 
2. La salida de V750-C puede ser de otra ventana, otro volcán, o el n 22 de otro conjunto; el 0,684 puede ser mediana por pasada vs por noche; puede venir con el Test 1 encendido o con K.
3. La salida pudo haberse leído de un archivo regenerado o de una corrida parcial.
4. La razón 0,684 vs ¿qué cuenta como 1,0 sin fondo-solo? Sin el brazo de control (port completo) no se atribuye al fondo. 
5. Si la vara en V750 fuese primary_cluster.vrp_mw o el suma-de-píxeles del port, cambia.
6. Que sea SOSPECHA del auditor ya dice que no lo reprodujo.

## CH172-04: la métrica de noche del auto-audit semanal subestima el déficit por pasada (0,56/0,66/0,68 vs 0,36/0,57/0,42)

1. «Mediana por noche» vs «por pasada»: dos medianas de agrupaciones distintas no son comparables sin decir los n y la ventana; que difieran no implica que una subestime; hay que ver cuál mide lo que importa (A93, A94: la noche es la unidad del operador).
2. Misma ventana, mismo pareo, mismos volcanes? ¿«0,36/0,57/0,42» es de Chillán solamente y «0,56/0,66/0,68» de todos los Tier A (cambio de estrato)? Si es así, la diferencia es de volcán, no de agregación.
3. Pareo «misma pasada» con TOL_S puede dejar pasadas sin pareo que sesgan.
4. La mediana de una noche (de varias pasadas) vs el mínimo/peor: en una noche con 4 pasadas y cenits distintos la mediana de noche es robusta; el déficit por pasada en las pasadas de borde es mayor, pero eso es por diseño del estadístico, no un defecto del auto-audit.
5. El auto-audit semanal puede haber cambiado de definición desde la fecha del script del auditor (la copia local del script atrasada).
6. Orden de los 3 números: ¿sensor MODIS/V375/V750 en el mismo orden en ambos tríos?

## CH172-07 (de quien orquesta): novedad frente a S154 y 1.14, y contradicción con curva real, mecanismo SIN ATRIBUIR, D25 y D17

1. Hay que leer S154 (experiments/_s154_chillan/), experiments/_s151_presupuesto_magnitud/README.md §3.2 y docs/SINTOMAS.md en origin/main; el «ya lo tenía medido» puede estar en otro documento (A89: el nombre en el punto de uso no es el de la definición).
2. «Curva real» de la razón vs cenit: el proyecto puede ya tener medida la curva con más n y otros estratos y la nueva afirmación solo reproduce una versión peor.
3. Mecanismo SIN ATRIBUIR: la afirmación puede estar sugiriendo un mecanismo (cenit) que el proyecto retiró (S154: lo atribuí a D25 y luego a D17 citando una lectura que 1.14 ya había retirado). La correlación con cenit no es un mecanismo: D17 (remuestreo/bow tie) y D25 son mecanismos candidatos y no se distinguen con un Spearman.
4. Marca: documentos vigentes en main vs. en la rama loop/activo (el árbol compartido está en loop/activo; main puede estar atrasado respecto a lo que S171/S172 sabían).

## Caminos transversales

- El instrumento no tiene control positivo ni nulo medido (A110, A116): ¿cuál es la correlación esperada en un volcán donde NO se sospecha efecto de cenit (p. ej. Villarrica, Láscar)? Si todos los volcanes muestran Spearman negativo con cenit, Chillán no es especial, es un efecto sistemático de geometría (que sería D17) o de pareo.
- Estratificar por satélite (SNPP / NOAA-20 / NOAA-21; Terra / Aqua) y por año/régimen.
- Corpus vivo (A90): numerador, denominador, ventana.
- Una correlación de rango con n ≤ 12 y múltiples comparaciones (3 sensores × varios cortes) sin corrección.
- La copia de la referencia (CSV de MIROVA) puede haber cambiado de sha256 entre la corrida del auditor y hoy (sync cada 1 h).
- Dependencias entre afirmaciones: CH172-01 y 02 comparten datos (las 3 alertas MODIS son parte de los n=12), no son independientes.

---
sha256 del contenido anterior a esta nota: 3615e45881123e6c54cd356a60a60e7221e1735c4ce3159f0ff209a3a4618bca
Hora del servidor al cerrar: 2026-11-01 23:58:57 UTC (no se vuelve a editar)
