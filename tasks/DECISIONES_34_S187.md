# Hoja de decisiones: los 34 volcanes al tablero (2026-11-16)

Qué es: el estado de hoy de las decisiones D1 a D15 y de las compuertas A y B del plan
`docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md` (§11, l. 598 a 616; sólo existe en la rama `loop/activo`),
comprobado contra el remoto. Referencia: `origin/main` en `c692375b5` (2026-11-16 15:13 UTC). No se tocó el repo.

Resumen: 5 resueltas por los hechos (D2, D3, D4, D8, D9), 3 obsoletas (D6, D7, D12), 3 con otra pregunta (D10, D11,
D14) y 4 siguen abiertas (D1, D5, D13, D15). La Compuerta A quedó resuelta por los hechos; la Compuerta B sigue
abierta. Hay 2 decisiones NUEVAS que bloquean (N1, N2).

## 1. Tabla

| # | decisión | estado hoy | evidencia | recomendación (sólo abiertas) |
|---|---|---|---|---|
| D1 | ¿43 o 45 volcanes? | **DECIDIDA Y EJECUTADA (S190)**: Nicolás eligió los 43 de la RNVV (2026-11-17 ≈00:10 UTC) y aceptó 1a, 2a y 3b (≈00:20 UTC). Retiro de Putana y OlcaParuma mergeado en #1034 (merge `3239a4db8`, 2026-11-17 06:31 UTC): `active: false`, fuera de la sombra y del tablero, JSON de `data/historia_34/` y `data/sombra_34/` borrados; respaldo en `D:rp-trabajo	emporales\s189espaldo_d1_rnvv\`. Lastarria sigue (pregunta 4 de S189 sin respuesta explícita; recomendación: se queda). Centros RNVV en 7 de los 34 por #1031. Texto previo: SIGUE ABIERTA | Plan l. 602. La lista de la RNVV tiene 43 entradas y no trae Lastarria (conteo de hoy de `Volcanologia\WEBRNVV\fichas_nuevas_json\_lista.json`). La historia usa los 34 de la sombra (H1, `experiments/_historia_34/TANDAS.md` l. 23). Olca-Paruma ya está aplicada (`data/historia_34/OlcaParuma.json` en main); Putana va en la tanda 2, Cerro Azul-Quizapu en la 3, Tolhuaca en la 4 (plan de la historia, Tarea 5) | Primero decir qué quisiste decir con «43». Mientras no decidas, rige de hecho la (a): H1 tomó los 34 de la sombra y el tablero muestra 45 tarjetas. Si es la lista de la RNVV: opción (b) del plan, 44 con Lastarria. Decidirlo antes de aplicar las tandas 2, 3 y 4 (Putana va en la 2; Olca-Paruma ya está aplicada y se retiraría con su propio tag) |
| D2 | Detector de los nuevos | **RESUELTA POR LOS HECHOS** | `pipeline/profiles/sombra_34.yaml` extiende `mirova_equivalent` y enciende las tres vías, igual que producción (`mirova_equivalent.yaml` l. 38, 58 y 88). `data/sombra_34/`: 3.505 records, los 3.505 con `via_codigo_mirova: true`, del 2026-11-03 01:55 al 2026-11-15 07:35 (conteo de hoy sobre main) | |
| D3 | Grilla de los nuevos | **RESUELTA POR LOS HECHOS** | `pipeline/grillas_mirova.yaml` l. 41 a 44: bloque S172 con la regla GEO (lat/lon del yaml), 45 entradas; decisión tuya del 2026-11-02 | |
| D4 | Radio de los nuevos | **RESUELTA POR LOS HECHOS** | La vía detecta sobre la grilla de 51 × 51 km y no usa `radius_km` (comentario «GEOMETRÍA» de `sombra_34.yaml`). `volcanoes.yaml` sigue con 5 km en los 34 (conteo: 34 con 5, 11 con 25), lo que sólo pesa si una pasada cae a K (0 de 3.505). El tablero dibuja 25 km (`frontend/index.html` l. 896) | |
| D5 | Radio interno (cumbre) | **SIGUE ABIERTA** | El tablero supone 5 km para los 34 (`index.html` l. 2010 y l. 3481, «supuesto D5»); los records salen con `distance_class: null`. Las detecciones caen casi todas lejos: en el piloto, a 18 a 32 km (`TANDAS.md` l. 16); en S176, 0 de 17 a 5 km o menos (`tasks/LOOP_OBJETIVOS.md` l. 1340, `loop/activo`) | Sin cambio: 5 km de partida, con excepciones tuyas escritas para calderas y campos |
| D6 | Si un sensor no se adopta en los 11 | **OBSOLETA** | Los tres sensores corren la vía en los 11: MODIS desde el 2026-11-02 (ficha v1.18), VIIRS 375 y 750 desde el 2026-11-11 (v1.23, v1.24); K queda de guardia | |
| D7 | Ventanas de la retrospectiva | **OBSOLETA** | La retrospectiva se corrió y se leyó el 2026-11-10 (commit `d5ed709dc`): MODIS y VIIRS 750 «DECIDE NICOLÁS», VIIRS 375 «NO SE CONTRADICE», ninguna alerta protegida perdida | |
| D8 | Rigor de la Compuerta A | **RESUELTA POR LOS HECHOS** | Abriste la sombra el 2026-11-02 sin esperar la retrospectiva: «si está corriendo un código que funciona bien en 11 volcanes esperamos que sea similar para los otros 34, continúa con todo» (`sombra_34.yaml` l. 2 y 3) | |
| D9 | Sombra antes de tener grillas | **RESUELTA POR LOS HECHOS** | No hubo etapa K: las grillas se adelantaron en S172 (`experiments/_s172_sombra34/INFORME.md`) y la sombra corre con la vía desde su primera noche | |
| D10 | Umbral de volumen | **CAMBIÓ LA PREGUNTA** | El umbral se calculaba con la tasa de K (plan l. 529 a 535, H15), pero hoy el detector es la vía. Tasa de la vía en la comparación diaria (`data/audit_continuous/comparacion_via_k.json`, referencia tabla, ventana historia 2026-03-01 a 11-01/11-10; división FP/(FP+TN) hecha para esta hoja): MODIS 5 de 4.900 (0,10 %), VIIRS 375 97 de 3.211 (3,0 %), VIIRS 750 19 de 4.979 (0,38 %). No existen en main `revision_semanal.py` ni un pre-registro de la sombra de los 34 | Binomial 99 % con la tasa de la vía, no la de K; marcar no es excluir. SIN VERIFICAR que el FP de esa comparación sea el mismo «negativo limpio» de H15 |
| D11 | Cómo correr los nuevos | **CAMBIÓ LA PREGUNTA** | El workflow aparte ya existe: `sombra-34.yml`, una vez al día (cron 13:07 UTC, `max-parallel: 8`), y es lo que el tablero muestra. Las últimas 8 corridas partieron entre 18:18 y 22:56 UTC; 4 de 8 fallaron (11-08, 11-11, 11-13, 11-14); el arreglo #1007 entró el 11-14 (`TANDAS.md` l. 37 y 38); a las 15:13 UTC de hoy no había corrida del 11-16 | Nueva pregunta: ¿basta una vez al día o hace falta un NRT aparte cada 2 a 3 h? Si los 34 no alimentan alertas, mantener la diaria y decirlo en el rótulo |
| D12 | Orden en el runner | **OBSOLETA** | Retrospectiva leída (D7) y VIIRS 750 adoptado (D6) | |
| D13 | Reversión de los nuevos | **SIGUE ABIERTA** | No encontré registro de una pre-autorización (búsqueda en `docs/`, `tasks/`, `frontend/`, `scripts/`). Se volvió más urgente porque los 34 ya se ven en el tablero (N1) | Pre-autorizar retirar del tablero un volcán nuevo el mismo día si publica un artefacto de 1 MW o más, sin tocar los 11 |
| D14 | Fecha de publicación | **DECIDIDA (S191)**: Nicolás eligió la opción (b) el 2026-11-20 («Preliminares, rotulados»): los 34 quedan a la vista como preliminares, con «paridad no medida», y la barra «Estado actual» los cuenta aparte de los 11. Implementación en el PR de la rama `s191-preliminares-34`. Texto anterior: **CAMBIÓ LA PREGUNTA** | Desde el 2026-11-12 y 11-13 los 34 están en el tablero principal, mezclados con los 11 (`index.html` l. 892, «todos deben tener la misma funcionalidad»; ficha v1.26). Ver N1 | Se decide con N1 |
| D15 | JSON de abril de los 34 | **SIGUE ABIERTA** (menor) | Siguen en `data/mirova_equivalent/` (Antuco: 85 records de K, 2026-04-17 a 04-24). El tablero no los lee para los 34: lee `data/sombra_34/` (`index.html` l. 1099 a 1102) | Archivar con tag (A38) antes de que algún workflow escriba los 34 en `mirova_equivalent`. Si la publicación sigue leyendo la sombra, no apura |
| A | Compuerta A (abrir la sombra) | **RESUELTA POR LOS HECHOS** | Abierta el 2026-11-02 por tu decisión (D8), antes del «CUMPLE en los tres sensores» que pedía el plan (l. 397 a 401) | |
| B | Compuerta B (publicar) | **SIGUE ABIERTA** | Pedía (plan l. 519 a 523): 14 noches con el detector final, 90 % de noches con dato por volcán, revisión experta de lo de 1 MW o más, umbral de volumen. La sombra lleva noches con la vía desde el 11-03, pero los porcentajes por volcán y sensor están SIN VERIFICAR y el cuaderno de revisión no existe | Se cierra con N1, D10 y tu revisión |
| N1 | **NUEVA**: ¿lo que se ve hoy es la publicación? | **DECIDIDA (S191)**: Nicolás eligió la opción (b) el 2026-11-20 («Preliminares, rotulados»): los 34 quedan a la vista como preliminares, con «paridad no medida», y la barra «Estado actual» los cuenta aparte de los 11. Implementación en el PR de la rama `s191-preliminares-34`. Texto anterior: **SIGUE ABIERTA** | Rótulo actual de la tarjeta: «sin MIROVA · 1 vez al día» (`index.html` l. 2645); el plan pedía una sección aparte con «sin referencia de MIROVA, paridad no medida» (l. 567). `diario.html` y `mosaico.html` no muestran los 34. La ficha dice que esa vista «No alimenta alertas» (v1.26). Aviso al OVDAS: SIN VERIFICAR | Mantenerlos a la vista, agregar «paridad no medida» al rótulo y declararlos preliminares hasta la Compuerta B |
| N2 | **NUEVA**: calor de un volcán de los 11 en la grilla de un nuevo | **SIGUE ABIERTA** | Aprobaste el 2026-11-02 (`tasks/BLOQUE_ARRANQUE_S173.md` §b fila 3, `loop/activo`) marcar en la lectura y poner zona excluida en la grilla (A45) antes de publicar Quetrupillán, Michinmahuida, Antillanca y Callaqui. La marca de lectura existe (`scripts/vecinos_sombra_34.py`); la zona excluida no. El tablero marca «también visto desde X» sólo entre los 34 (`index.html` l. 2070 a 2072) | Primero extender esa marca del tablero a los 11 (no toca la detección); la zona excluida sólo si la marca no basta |

## 2. Lo que sigue abierto, ordenado por lo que bloquea

**1. N1 y D14: ¿qué cuenta como «publicado»?** ⚠️ DECIDIDA el 2026-11-20 (S191): opción (b). Los 34 ya aparecen en la página principal junto a los 11 y un operador
puede leer un punto rojo en un volcán sin referencia como si valiera lo mismo que en Láscar. Elige: (a) ratificarlo
como publicación (ficha nueva, aviso al OVDAS); (b) dejarlos a la vista como preliminares, con «paridad no medida»;
(c) retirarlos hasta la Compuerta B. Recomiendo (b).

**2. D1: la lista.** Con 51 km de grilla, vecinos como Descabezado Grande y Cerro Azul-Quizapu (a 8,2 km) ven la misma
escena y pueden publicar el mismo foco dos veces, y el campo geotermal de Tolhuaca puede dar calor no volcánico. Lo
primero es qué quisiste decir con «43»: la RNVV tiene exactamente 43 y no incluye a Lastarria. Conviene decidir antes
de aplicar las tandas 2, 3 y 4 (Putana va en la 2). Mientras tanto rige de hecho la (a), los 45.

**3. D5: radio de la cumbre.** En calderas y campos (Laguna del Maule, Sollipulli, Hudson, Carrán-Los Venados) el calor
puede estar a varios km del punto nominal, y con 5 km se leería como «lejano». Recomiendo 5 km de partida y una
excepción escrita por cada caldera o campo que tú justifiques.

**4. N2: calor del vecino de los 11.** El lago de lava de Villarrica cae en la grilla de Quetrupillán, el domo de
Chaitén en la de Michinmahuida, el lacolito del Cordón Caulle en la de Antillanca, y Copahue en la de Callaqui. Hoy esa
pasada se ve como anomalía del volcán nuevo, sin marca. Recomiendo extender la marca «también visto desde» a los 11
antes de tocar la grilla.

**5. D13: reversión.** Si un volcán sin referencia publica un artefacto de 1 MW o más, cada hora que siga a la vista es
una falsa alarma posible en un volcán que nadie venía mirando. Recomiendo pre-autorizar retirarlo el mismo día.

**6. D10 y la Compuerta B: revisión experta y umbral.** Sin MIROVA, la única forma de separar fumarola, lago tibio o
nieve es tu ojo de geólogo más un umbral de volumen que diga qué volcán revisar. Recomiendo binomial 99 % con la tasa
de la vía y escribir el cuaderno de revisión antes de la Compuerta B.

**7. D11: cadencia.** La sombra procesa una vez al día y en la práctica corre de tarde, con 4 fallas en 8 días (antes
del arreglo #1007). Si los 34 van a apoyar decisiones de alerta, hace falta un NRT aparte de 2 a 3 h; si no, basta la
diaria con su rótulo.

**8. D15: archivos de abril.** Son de un detector viejo (K, radio 5 km) y hoy nadie los muestra para los 34. Sólo
apuran si la publicación pasa a escribir en `data/mirova_equivalent/`.

## 3. Lo que no pude verificar

- Si el OVDAS sabe que los 34 ya se ven en el tablero.
- Noches con dato por volcán y sensor en la sombra (criterio del 90 % de la Compuerta B).
- Que el FP de `comparacion_via_k.json` sea el mismo «negativo limpio» de H15 (definiciones no cotejadas).
- Tanda 2 (run 43806164818): a la hora de la consulta, 154 jobs en verde, 6 en curso y 6 en cola; la cadena de las
  tandas 3 a 7 la tomo de la bitácora (commits `af217cdfd` y `3ce617fcb`) sin comprobar runs.
