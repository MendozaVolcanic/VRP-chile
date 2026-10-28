# Caminos por los que la adenda 2 de V375-E y su lector podrian estar mal

Escrito ANTES de abrir cualquier archivo de e_adenda2/ y la seccion 8. Verificador con contexto limpio.

C1. Instrumento mide otra cosa: el lector de posicion llama al predicado del tablero con un record cuyo
    campo (final_hotspot_*, distance_class, pc_lat/pc_lon) no es el que el tablero lee; el cambio de brazo
    no cambia la publicacion, o cambia otras cosas ademas de la posicion (magnitud, clase).
C2. Punto de medida distinto: la distancia de los brazos se mide desde un punto (vent, centro de grilla,
    ancla de deteccion) distinto del que usa la via de #921 o el tablero; frontera <= vs < en inner_radius.
C3. Los tres brazos no son los del programa: "radiante" definido como el pixel mas radiante y no como el
    centroide del cumulo de la alertada mas radiante; "cercano" medido a un cluster y no al pixel; "pico"
    por BT en vez de radiancia (MIR vs TIR, I04 vs I05).
C4. La ventana no contiene el fenomeno: la lista de lejanas (far_ref) solo trae tabla u OCR sin distancia
    antes de 2026-06-13 (A119); lejanas de T no se pueden juzgar por OCR; tramos O1/O2 mezclados (A104).
C5. La regla se lee de otro lado: el lector toma el flag/umbral de YAML y no de pipeline.profile (A89);
    inner_radius_km del tablero vs el del yaml; el caller transforma el argumento (A6).
C6. Segundo camino no cubierto: la via tiene mas de un sitio donde se fija la posicion (store.py,
    process_viirs.py, fallback cluster_rescue/final_hotspot_source); la bateria cubre uno.
C7. Copia local atrasada: los JSON/los records locales de 533398f8f o la referencia no coinciden con los commits
    fijos; la lista de objetivos se genero con otra copia; sha256 no reproducibles.
C8. La vara es otra: "far_ref" definido con etiquetar() vs reimplementado; far_tabla/far_ocr mal separados;
    pasadas lejanas con alerta en otra pasada de la misma noche; regla D-9 SN aplicada o no.
C9. Control que no puede fallar: batería con aserciones tautologicas; nulo de mutaciones donde el control
    CAIDA "atrapa" por excepcion y no por aserción; identidad (mutacion nula) no distingue.
C10. Regla de decision (§8.5) con huecos: combinaciones de veredictos no cubiertas (dos brazos empatan,
    un brazo cumple pero viola el veto, denominador cero, negativos ponderados vs lejanas), umbrales
    acomodables despues de ver datos, veto de §5.4 heredado en unidades distintas.
C11. Lectura retrospectiva anticipada: algun camino por el que el lector/probar/mutar lee artefactos reales
    de S159/S162/S162b (rutas por defecto, glob), o la lista se genera mirando la publicacion.
C12. Workflow: autenticacion por usuario/clave en vez de EARTHDATA_TOKEN, on: sin comillas (A43),
    concurrency/push, lista run con granulos que no existen, "sin_granulo" mal tratada, timeout.
C13. Cifras de la adenda (330, 329, 1, 122, 10.087, tramos, sha256, 8 pasadas, 4 protegidas, 40 de 329) que no
    salen de una salida del repo o que son de otro corpus vivo (A90).
C14. Descripcion de la via (§8.3) envejecida: lineas/flags de #921 citados que ya no coinciden con main.
C15. Peso de las lejanas: un denominador con 329 lejanas frente a negativos ponderados puede dar a las
    lejanas un peso que domina o es irrelevante; la vara 3 usada para decidir en vez de descartar (A93).

---
sha256 (calculado antes de esta linea): bcf60fd0ee03907e69715405da49eaa910832aa206041e6d44cb727c2be8bcf9
hora del servidor: 2026-10-28 04:52:14 UTC. No se vuelve a editar.
