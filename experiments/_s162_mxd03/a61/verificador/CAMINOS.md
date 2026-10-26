# Caminos por los que cada afirmacion podria estar mal (escrito ANTES de releer)

Hora del servidor (gh api -i repos/MendozaVolcanic/VRP-chile, header Date): Mon, 26 Oct 2026 01:43:52 GMT
Worktree: C:\vrp-trabajo\s162-a61, rama s162-a61-mxd03, commit 56f721d99.

## Generales (valen para todas)
- G1. La copia local de los artefactos (tandas, ref) esta atrasada o no es la del A/B (otro run, otra version).
- G2. El pareo protegida <-> record se hace por hora redondeada o por tolerancia: puede parear la alerta con otro granulo (Terra vs Aqua, pasada siguiente).
- G3. El "criter" contra el que se mide no es el vent de volcanoes.yaml, sino el centro del volcan (lat/lon) o el mirova_center (A46, A3).
- G4. Las salidas guardadas no son las de la version de hoy del script (el script cambio despues de correr).
- G5. Denominador: "48 protegidas" puede no ser el mismo conjunto en cada script (otra definicion de protegida, otra ventana, lectura A vs B).

## E1 (X a 0,15-0,89 km, mediana 0,34; K mediana 1,58, max 3,20; 0 cambios de clase)
- La distancia del cumulo se lee de pc.centroid o de final_hotspot: cual? Si es final_hotspot, es otro objeto.
- Se mide desde vent o desde el centro del volcan.
- "0 cambios de clase" se calcula con distance_class persistida (derivada de final_hotspot) y no con la posicion del cumulo: no mide lo que dice.
- "Mas cerca en 48 de 48" podria ser trivial si X esta siempre corrido hacia el nadir igual que el centro.

## E2 (44 de 48 mismos pixeles: 26 por indice, 18 por residuo<0,3 km; 4 reseleccion)
- El "indice del pixel" puede ser identico por construccion (K y X comparten la grilla del L1B, la fila/columna es la misma siempre que se elija el mismo pixel; si el script compara el indice de pixel pico pero el cumulo tiene varios pixeles, no prueba que el cumulo sea el mismo).
- Si el indice no se persiste, el script podria reconstruirlo desde lat/lon con la geolocalizacion de un solo brazo: tautologico.
- Residuo medido contra el corrimiento del granulo en el pixel del crater, no en el del cumulo: si el cumulo esta a varios km, el corrimiento difiere (gradiente del corrimiento a lo largo del scan) y el umbral 0,3 km puede no discriminar.
- Umbral 0,3 km sin nulo medido: ¿cuanto daria entre pixeles distintos (vecino a 1 km)? Si el corrimiento varia mucho, vecino y mismo pixel podrian caer bajo 0,3.

## E3 (vara VIIRS 375 de otros granulos de la misma noche)
- La vara podria incluir el mismo instante (MODIS y VIIRS no comparten granulo, pero ¿es otra pasada o la misma hora?). Si el VIIRS es de nuestro propio pipeline, la posicion VIIRS no depende de MxD03 (independiente de geolocalizacion MODIS) pero si del detector: el objeto VIIRS lo elige el mismo detector K.
- vara_viirs_mxd03.json: ¿de donde sale? Si se construyo con la posicion X para elegir el objeto VIIRS mas cercano, la vara esta sesgada hacia X (seleccion).
- Si el objeto VIIRS es tambien el crater (siempre cerca del vent), la vara mide "X cerca del crater" otra vez, no una fuente independiente.
- 47 de 48: ¿cual falta y por que?

## E4 (MIROVA Distancia_km 0,0: X <=0,75 km del crater 30/30, K 4/30)
- Distancia_km esta cuantizada a la celda (D15) y no trae acimut (A93): 0,0 significa "misma celda que su referencia", no "en el crater". Comparar contra 0,75 km es arbitrario; el umbral 0,75 podria estar elegido a posteriori.
- La referencia de MIROVA puede no ser el vent de nuestro yaml.
- Es una prueba de radio, no de posicion: no identifica el objeto (A107).

## H1 (relleno -999 da negativo, no sin dato; 2 de 5.465)
- El codigo podria tratar -999 en otra parte (mascara de lat/lon invalidas) que el auditor no vio; leer el caller y el callee.
- 2 de 5.465: ¿como se contaron? ¿se buscaron todos los -999 o solo los que tocan el crater?
- Leer process_modis.py:385-396, :560, :628 en el commit del tag.

## H2 (desfase de indice de _interp_geo, 5i+2)
- El modelo "5i+2" podria ser una suposicion: verificar contra el codigo de _interp_geo y contra la doc MODIS (la grilla de 5 km del MOD021KM se muestrea en el pixel 3 de cada 5, indice 2).
- "dentro de 10 %" sin decir la distribucion; maximo sano 11,45 km.
- Cenit 68-75 grados "imposible para MODIS": MODIS barre +-55 grados de scan, cenit de sensor hasta ~65 grados. Verificar.

## H3 (K pierde mas pixeles de anillo que X donde toca el relleno)
- El signo depende de que brazo se resta.
- Halo de 5 lineas: por el interpolador o por el detector.

## H4 (4 reselecciones; magnitud X/K hasta 27 %)
- 27 % podria ser de otra alerta, no de una de las 4.

## H5 (Lascar 2026-03-12 07:25, 5 de 20 brazos R, A46)
- Verificar que final_hotspot_dist_km se mide desde volcano lat/lon y no desde vent; que el centro esta 0,68 km al sur.
- "5 de 20 brazos R": ¿que son los brazos R y de que salida?

## H6 (control del modulo de R acepta modulo absurdo; tope 20 km marca 1 record)
- Leer evaluar_mxd03.py:324-334.

## H7 (lado al reves en 47 de 906 de crepusculo)
- Depende de la definicion de "lado" (dia/noche por hora local vs angulo solar).

## H8 (vent de Nevados de Chillan = centroide)
- Leer volcanoes.yaml.

## H9 (TIF MIROVA 2026-05-10 01:25 Lascar, maximo en celda del crater)
- A109: el TIF es del MISMO granulo? Si MIROVA geolocaliza con MxD03 su TIF, que coincida con X no es independiente del brazo X sino de la geolocalizacion. n=1.
- CRS del TIF (A106): EPSG:4326 vs UTM; celda de ~375 m o 1 km.
- Si el TIF no esta en disco y no lo puedo bajar: SIN DATO.
sha256 de CAMINOS.md hasta la linea anterior: 9c7d9456a7c0b5c3d38c0d2fd33f492cf6dcc2ca8e0dfbf2b8f2e3cdf4c7059e
