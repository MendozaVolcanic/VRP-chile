# Variante «cumbre primero» de la regla de posición: preregistro (S193)

Escrito y commiteado antes de correr ninguna medición de la variante. Rama `claude/angry-banach-969875`, base `origin/main`
`76f52c7ec` (2026-11-21 21:01 UTC). Sólo experimento: no toca `pipeline/`, `frontend/` ni `data/`.

## 1. El fenómeno y la pregunta

En una misma pasada nocturna puede haber un píxel alertado débil sobre el cráter y, lejos, un cúmulo más radiante
(incendio, borde de nube, salar o roca tibia). La vía «código MIROVA» suma todos los alertados para el VRP (D32), pero el
record necesita un lugar. Con la regla vigente, «radiante» (D8', decisión de Nicolás del 2026-11-15,
`pipeline/mirova_v750_codigo.py::_cumulo_del_mas_radiante` y `procesar_grilla`), el lugar es el centroide del cúmulo
8-conexo de la alertada de mayor radiancia MIR. Si ese cúmulo está lejos, la clase queda `far` y la vista por defecto del
tablero («Solo cráter», cerca D13 en `mirovaEqVrp`) no publica, aunque MIROVA publique esa pasada como alerta en la cumbre.
La auditoría Codex ronda 2 (F12-104, F12-V301, verificadas) contó 12 protegidas sólo OCR con ese mecanismo del 2026-03-01 al
2026-11-18, contra 5 declaradas al formalizar la regla.

**Variante «cumbre primero»:** si al menos un alertado del record está a `inner_radius_km` o menos del cráter, la posición
es el centroide del cúmulo 8-conexo (sobre todos los alertados) que contiene a la alertada de mayor radiancia MIR **entre las
que están dentro del inner**; si ninguna lo está, «radiante» como hoy. `distance_class` sale de ese centroide igual que hoy
(`summit` si está a `inner_radius_km` o menos). El VRP no cambia (suma de todos los alertados).

Pregunta: ¿cuántas alertas protegidas de MIROVA recupera la variante en la vista por defecto del tablero, y cuánto cuesta en
publicaciones nuevas donde MIROVA no alertó o ubicó la fuente lejos?

## 2. Población, datos y referencia (fijos antes de medir)

- **Records:** `data/mirova_equivalent/<volcán>.json` de `76f52c7ec`, 11 Tier A, sólo records de la vía
  (`via_codigo_mirova: true`), pasadas nocturnas según `banco_paridad.es_pasada_diurna_descartada` (el mismo corte que la
  comparación diaria), sin escenas sin medir (`diag_codigo_mirova.motivo_vacio`, como `comparacion_via_k`).
- **Ventana principal:** noches del 2026-03-01 al 2026-11-18 (la de Codex, para poder cotejar las 12). Se informa además,
  sin decidir con ella, hasta el 2026-11-20.
- **Referencia de MIROVA:** `cargar_referencia_unificada()` con sus valores por defecto (snapshot del repo más capas
  históricas, el mismo cargador de `scripts/comparacion_via_k.py`), regla de alertas mínimas SN (`MODO_MINIMAS`, D-9),
  pareo de 120 s (`clase_mirova.VENTANA_S`), etiquetas de `banco_paridad.etiquetar` (`pos`, `far_ref`, `neg_limpio`,
  `sin_geometria`, `sin_info`). Dos lecturas, **siempre informadas por separado (A119)**:
  - **tabla:** sólo filas del consolidado (`source == "CONS"`);
  - **combinado (lectura A de MISSION):** tabla y OCR.
  Protegida = pasada `pos` con alguna alerta pareada de 1 MW o más (`clase_mirova.alerta_protegida`), como en
  `comparacion_via_k.etiquetar`.
- **Qué se publica:** el predicado real del tablero, ejecutado con node sobre `frontend/index.html` de `76f52c7ec`
  (`banco_paridad.cargar_nuestros`: `isSummitDetection`, `isValidDetection`, `isThermalArtifact`, `mirovaEqVrpDisplay` con
  `includeFar = false`, que contiene la cerca D13). No se porta ni se aproxima (A97).

## 3. Cómo se aplica la variante sin reprocesar

Los records de la vía guardan todos los alertados (`anomaly_pixels`, con `fila`, `col`, `lat`, `lon`, `dist_km`, `bt_k`;
sonda previa: 3.707 records con alertados desde 2026-03-01, en los 3.707 `n_anomalous_pixels` = largo de la lista y todos con
fila, columna y temperatura). La radiancia MIR de cada alertado no está guardada, pero su temperatura de brillo sí, en la
misma banda, y la relación de Planck es monótona: ordenar por `bt_k` es ordenar por radiancia salvo empates por el redondeo a
0,01 K (5 records con empate en el máximo en la sonda). La posición del cráter en la grilla se calcula con las funciones de
producción (`grilla_del_volcan` y `posicion_de`, ancla `get_detection_anchor`), y el control C2 comprueba que reproduce las
distancias guardadas.

Sólo cambian en el record los campos de posición: `primary_cluster.centroid_lat/lon/dist_km` y `n_pixels`,
`distance_class`, `final_hotspot_*` y `hotspot_*` (pico del cúmulo elegido). `vrp_mw` y `primary_cluster.vrp_mw` quedan
iguales. El record modificado pasa por el mismo node.

## 4. Controles (si uno falla, se informa y el veredicto queda SIN DATO para lo que toque)

- **C1 (reproducción de «radiante»):** recalculando «radiante» con este método, `distance_class` y
  `primary_cluster.centroid_dist_km` (a 0,001 km) iguales a los guardados en el 100 % de los records con alertados; se
  listan las excepciones (se esperan, si acaso, sólo empates de `bt_k`).
- **C2 (posición del cráter):** las distancias de cada alertado recalculadas desde `posicion_de` iguales a `dist_km` guardado
  a 0,006 km en el 100 % de los alertados.
- **C3 (identidad del predicado):** node sobre los records reescritos con «radiante» recalculado da `pub` idéntico al de los
  records originales en el 100 % de las pasadas.
- **C4 (el instrumento puede dar distinto de cero, A116):** un record sintético con un alertado débil en el cráter y un
  cúmulo fuerte a 15 km: con «radiante» el tablero no publica, con la variante sí, ambos por node.
- **C5 (cotejo con Codex):** con «radiante», las protegidas combinadas no publicadas que tienen un alertado dentro del inner
  (ventana principal) se listan y se cotejan con las 12 de F12-V301 (Cordón Caulle 2026-05-09 06:18; Láscar 03-15, 04-25,
  06-12, 10-01; Isluga 03-20, 03-24, 04-07, 06-17, 09-28, 10-03; Lastarria 05-30). Diferencias se explican, no se ajustan.

## 5. Métricas (unidad: pasada; por sensor y por volcán, A114 y S126; y totales)

Para cada lectura (tabla y combinado):

- **G1, protegidas recuperadas:** pasadas `pos` protegidas con `pub` 0 en «radiante» y 1 en la variante.
- **G2, alertas recuperadas** (cualquier VRP): `pos` con `pub` 0 a 1. Informativa.
- **L1, protegidas perdidas por la variante:** `pos` protegidas con `pub` 1 a 0. Posible si otro cúmulo con un alertado más
  brillante dentro del inner tiene su centroide fuera.
- **L2, publicaciones nuevas en negativos limpios (A98):** `neg_limpio` con `pub` 0 a 1 (falsas alarmas nuevas donde MIROVA
  listó la pasada con 0 MW y la noche del sensor no tuvo alerta ni fuera de límite). Se informa también `neg_estricto`.
- **L3, publicaciones nuevas donde MIROVA ubicó la fuente lejos:** `far_ref` con `pub` 0 a 1.
- **L4, concordancia de clase con MIROVA:** pasadas con alertados y etiqueta `pos` (clase MIROVA `summit`) o `far_ref`
  (clase MIROVA `far`); fracción con nuestra `distance_class` igual. «Radiante» contra variante. (D8' cita 98,7 % en 2.037
  pasadas con la tabla sola hasta el 2026-11-15; el instrumento de S185 no está en disco, así que esta definición es propia y
  la cifra de «radiante» aquí es su línea base, no una reproducción.)
- **Informativas:** publicaciones nuevas en `sin_info` y `sin_geometria`; noches-satélite (volcán, satélite, noche) que
  pasan de no publicar a publicar entre las que tienen una protegida (A94); cociente VRP nuestro contra MIROVA en las
  protegidas recuperadas (el número publicado es la suma de todos los alertados, que incluye el cúmulo lejano).

## 6. Corte de decisión (fijado antes de medir)

Con la ventana principal:

1. **Veto:** L1 > 0 en cualquiera de las dos lecturas: NO GANA (la variante callaría una protegida que hoy se publica).
2. **Sin sustrato:** G1 combinado = 0: NO GANA (no recupera nada de lo que motivó medirla).
3. **GANA** si, además de 1 y 2: L2 (tabla) ≤ G1 (combinado), y L4 (tabla) no baja más de 0,5 puntos porcentuales respecto de
   «radiante», y G1 tabla ≥ 0 sin L1 tabla.
4. **DECIDE NICOLÁS** si pasa 1 y 2 pero no 3: se entrega el trade-off con los números (cuántas protegidas sólo OCR se
   recuperan contra cuántas falsas alarmas y cuánta concordancia se pierden), sin recomendar adopción.

Por qué así: el criterio de victoria es no perder protegidas (MISSION, lectura A), así que perder una es veto; el costo que
ya rechazó «cercano» en S185 fue publicar donde MIROVA ve la fuente lejos (114 `far_ref` por 9 `pos`), de ahí L3 y L4; una
falsa alarma por protegida recuperada es el máximo que se acepta sin pasar la decisión a Nicolás. Las protegidas
recuperadas serán, por lo que ya se sabe, sólo OCR (canal de calidad dudosa, A119): se informa y se deja explícito en el
veredicto; no cambia el corte.

## 7. Verificación

Un verificador de contexto limpio (subagente sin este razonamiento) reproduce G1, L1, L2, L3 y L4 por lectura y sensor desde
el script y los datos, y revisa que el script aplique la variante tal como está escrita en §1. Su resultado va al informe.

## 8. Qué no hace este experimento

No reprocesa gránulos ni toca producción. Si la variante gana, el informe describe el cambio A45 que la implementaría
(`pipeline/mirova_v750_codigo.py::procesar_grilla`), sin implementarlo. Adoptarla es decisión de Nicolás.
