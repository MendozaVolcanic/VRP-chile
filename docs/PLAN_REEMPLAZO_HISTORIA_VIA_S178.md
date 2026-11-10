# Plan: reemplazar la historia de los 11 Tier A con records de la vía «código MIROVA» (S178, P6)

Estado: PLAN, no aplicado. Nada de este documento toca `data/`, `pipeline/` ni `frontend/`. Cada paso que escribe en la
serie publicada pide el «sí» de Nicolás y un tag defensivo (A45). Fecha: 2026-11-10 (hora del servidor 08:11 UTC).

Alcance de lo medido: sólo COBERTURA (qué pasadas hay, con qué marca). No se leyó ningún veredicto ni se comparó la vía
con K o con MIROVA: eso es la prueba retrospectiva con candado (`experiments/_s172_retro_paquete/leer_retro.py`).

## 0. Por qué

Desde el 2026-11-02 MODIS de producción corre la vía «código MIROVA» (`enable_modis_codigo_mirova: true`,
`pipeline/profiles/mirova_equivalent.yaml:38`), pero la historia de los 11 Tier A antes de esa fecha sigue escrita con
K. El operador ve en la serie de MODIS un escalón que no es del volcán, y el tablero lo advierte con un aviso naranja
(`frontend/cambio_detector.js:148-156`). Cuando se encienda la vía en VIIRS 375 y 750 (#974 y #975, borradores) pasará
lo mismo en cada VIIRS. Reemplazar la historia con records de la vía hace que la serie entera sea de un solo detector,
como hizo #883 con K, y el aviso deja de tener escalón que marcar.

Los records de la vía ya existen como artefactos de `.github/workflows/reproc-retro-paquete.yml` (perfil
`_s172_retro_paquete`, las TRES vías encendidas, `pipeline/profiles/_s172_retro_paquete.yaml:20-23`), así que un mismo
juego de artefactos sirve para MODIS ahora y para VIIRS después.

## 1. Cómo se aplicó #883 y qué se reusa

#883 (merge `8471add46`, 2026-10-21, aprobado por Nicolás ese día) reemplazó 2025-02-15..2026-09-17 de los 11 Tier A
con el reproceso de K. Las piezas:

| Pieza de #883 | Qué hace | ¿Se reusa? |
|---|---|---|
| `data/_s154_reproc_k_historico/<V>.json` (159 MB, commiteado) | el reproceso unido, en carpeta aislada, ANTES del reemplazo | Sí, el patrón: la unión de la vía tiene que vivir en el repo (ver 2.6) |
| `scripts/reemplazar_ventana_reproceso.py` | reemplaza por clave `(datetime_utc, sensor)` (`:39-40`) dentro de `[desde, hasta]` (`:43-44`); hereda `first_processed_utc` (`:73-76`); exige `regimen.perfil` del reproceso (`:59-61`); CONSERVA la pasada operacional sin par (`:79-81`) y rehúsa si pasan del 2 % (`:106-107`, `:118-128`); ensayo por defecto, `--aplicar` escribe (`:108`, `:129-132`) | Sí, con dos cambios (ver abajo) |
| `experiments/_s158_reemplazo/ensayo_11.py` | ensayo de los 11 sin escribir, con sha256 antes y después (`:55-63`) y resumen | Sí, copiado a una carpeta S178 |
| `experiments/_s158_reemplazo/apartar_c0.py` + `data/_c0_residuales/` | aparta (no borra) los 90 records C0 que NASA no deja reprocesar | Sí, el patrón (residuos K de la vía, ver 2.3) |
| `experiments/_s158_reemplazo/aplicar_11.sh` | bucle de los 11 con `--aplicar`, se detiene al primer rehúso (`:6`, `:12-17`) | Sí, como plantilla del script de aplicación |
| `.github/workflows/aplicar-reemplazo.yml` (#884, posterior) | en cada intento vuelve a `origin/main`, regenera con el script, corre las pruebas y empuja; exige `confirmacion: si` y crea el tag (`:51-57`, `:83-97`) | Sí, tal cual: así no hay choque con el NRT |
| `tests/test_guard_serie_k_pura_s158.py` | exige 100 % de records con `regimen.codigo_sha` desde `DATOS_K_DESDE_UTC` | Hay que revisarlo: los records de la vía también traen `codigo_sha` (ver 4.2) |

Los dos cambios que necesita `reemplazar_ventana_reproceso.py`:

1. **Filtro por familia de sensor.** Hoy reemplaza TODOS los sensores de la ventana (`:55-62`, `:65-81` no miran el
   sensor). Para MODIS ahora y VIIRS después hace falta `--familia MODIS|VIIRS375|VIIRS750` (la convención de
   `frontend/cambio_detector.js:192-197`, A48) y que fuera de la familia no se toque nada.
2. **Regla para la pasada operacional sin par** (2.3). Hoy se conserva y, sobre el 2 %, el script se niega. Con la vía
   la fracción es de 1,4 a 6,4 % y no es un corte de NASA, así que el tope rehusaría casi todo: hace falta
   `--apartar-sin-par <archivo>` que las mueva a un residuo, con el mismo informe.

Los dos cambios son código bajo `scripts/` con sus pruebas, en un PR previo al de datos (como pide
`aplicar-reemplazo.yml:16-17`).

## 2. Cómo unir D2, D4 y P4

### 2.1 Qué hay

| Despacho | Run | Ventanas | Estado (2026-11-10 08 UTC) |
|---|---|---|---|
| D2 | 42507820590 | F26 2026-02-01..03-31 y DM 2026-10-01..10-16 | terminado, verde; bajado en `C:\Users\nmend\vrp-temporales\s177_d2\` |
| D4 | 42601379627 | R25 2025-02-15..12-31, 10 volcanes (sin Tupungatito) | terminado, verde; bajado en `C:\Users\nmend\vrp-temporales\s177_d4\` |
| P4 | 42749607584 | 2026-01, 2026-04..09 y 2026-10-17..11-09 | EN CURSO: 70 jobs verdes, 6 corriendo y 89 en cola |

Los tres corren el mismo código: `regimen.codigo_sha = a7a6ae360` en los 42.389 records de D2 y D4, y el `headSha` de
P4 es el mismo. Entre `a7a6ae360` y `origin/main` (`e7cfbaf54`) sólo cambian `pipeline/fetch.py` (#966, manejo del
token) y `pipeline/profiles/guardia_k_viirs.yaml`: nada de la detección.

Unión de calendario por volcán: R25 + 2026-01 + F26 + 2026-04..09 + DM + 2026-10-17..11-09 = 2025-02-15..2026-11-09
sin huecos ni solapes (el planificador rehúsa ventanas solapadas, `plan_trozos.py:104-108`). Excepción: Tupungatito
empieza el 2026-02-23 (sección 3).

### 2.2 Cobertura medida con D2 y D4 (P4 SIN DATO)

Script: `D:\vrp-trabajo\temporales\s178_plan\contar_cobertura.py` (salida
`D:\vrp-trabajo\temporales\s178_plan\cobertura_d2_d4.json`). Cuenta claves `(datetime_utc, sensor)` de cada trozo
(el intento más alto) dentro de su ventana, contra la serie operacional de `origin/main` `e7cfbaf54`.

- Trozos: todos presentes, ninguno con dos intentos subidos, 0 claves repetidas entre trozos, 0 records fuera de su
  ventana. D2: 4 trozos por volcán (8 en Chillán, 3 en Tupungatito); D4: 16 por volcán (32 en Chillán).
- Días: 395 por volcán (53 en Tupungatito). Días sin ningún record de la vía: 0 en VIIRS; en MODIS, Isluga 8, Láscar
  2 y Lastarria 2. De esos, sólo 2 (Isluga) y 1 (Láscar) tienen record K, y son pasadas de borde (2.3); el resto
  tampoco tiene K: NASA no dio gránulo.
- Marcas: los 42.389 records de la vía traen `via_codigo_mirova: true`; ninguno trae caída a K (`sin_grilla`,
  `sin_mxd03`, `geo_distinta`).

Pasadas por familia (vía / operacional K / sin par en la vía / sólo en la vía):

| Volcán | MODIS | VIIRS 375 | VIIRS 750 |
|---|---|---|---|
| Chaiten | 938 / 958 / 20 (2,1 %) / 0 | 1853 / 1879 / 28 (1,5 %) / 2 | 1898 / 1874 / 0 / 24 |
| Copahue | 860 / 890 / 30 (3,4 %) / 0 | 1707 / 1764 / 59 (3,3 %) / 2 | 1775 / 1751 / 0 / 24 |
| Isluga | 694 / 718 / 24 (3,3 %) / 0 | 1412 / 1447 / 37 (2,6 %) / 2 | 1456 / 1441 / 0 / 15 |
| Lascar | 731 / 743 / 12 (1,6 %) / 0 | 1410 / 1472 / 64 (4,3 %) / 2 | 1492 / 1460 / 0 / 32 |
| Lastarria | 726 / 740 / 14 (1,9 %) / 0 | 1418 / 1512 / 96 (6,4 %) / 2 | 1550 / 1486 / 0 / 64 |
| Llaima | 856 / 876 / 20 (2,3 %) / 0 | 1754 / 1817 / 65 (3,6 %) / 2 | 1820 / 1806 / 0 / 14 |
| NevadosDeChillan | 851 / 873 / 22 (2,5 %) / 0 | 1659 / 1754 / 97 (5,5 %) / 2 | 1777 / 1724 / 0 / 53 |
| PlanchonPeteroa | 853 / 876 / 23 (2,6 %) / 0 | 1643 / 1677 / 36 (2,1 %) / 2 | 1688 / 1658 / 0 / 30 |
| PuyehueCordonCaulle | 896 / 927 / 31 (3,3 %) / 0 | 1785 / 1865 / 84 (4,5 %) / 4 | 1884 / 1841 / 0 / 43 |
| Tupungatito (desde 02-23) | 106 / 110 / 4 (3,6 %) / 0 | 209 / 217 / 10 (4,6 %) / 2 | 219 / 215 / 0 / 4 |
| Villarrica | 869 / 886 / 17 (1,9 %) / 0 | 1785 / 1808 / 25 (1,4 %) / 2 | 1815 / 1804 / 0 / 11 |

Todas las pasadas sin par son `standard` y nocturnas. Con P4 completo hay que correr el mismo script sobre los tres
despachos antes de cualquier ensayo.

### 2.3 Pasadas que la vía descarta (regla de cobertura)

Fenómeno: un gránulo que roza el volcán por el borde de la franja. K escribe un record por gránulo que toque la caja;
la vía exige ver el volcán como lo ve MIROVA y descarta el gránulo si dentro de 45 km hay menos de 100 píxeles o, en
MODIS y VIIRS 375, si el píxel más cercano al centro está a más de 5 km (`pipeline/mirova_v750_codigo.py:803-808`,
`RADIO_RECORTE_KM` en `:94`, `dist_max_centro_km` en `:109-117`). El procesador entonces devuelve `None` y no hay
record (`pipeline/process_modis.py:636-658`, el `return None` en `:657`; `pipeline/process_viirs.py:779-782`).

- MODIS: VERIFICADO. Las 217 pasadas MODIS sin par de D2 y D4 aparecen las 217 en el log de su trozo como «sin record
  (vía encendida: descarte de borde de la vía, 171-01, o volcán fuera del gránulo)» (`scripts/run_pipeline.py:416-424`;
  script `D:\vrp-trabajo\temporales\s178_plan\modis_borde.py`).
- VIIRS: SIN VERIFICAR por gránulo, porque VIIRS no escribe esa línea. Indicio: en Lastarria 42 de las 110 sin par
  tienen otra pasada de la vía del mismo satélite a 15 minutos o menos (el gránulo vecino de la misma órbita).
- La producción actual de MODIS hace lo mismo: desde el 2026-11-02 el NRT con la vía no escribe esas pasadas.

Regla propuesta (decide Nicolás):

- **A (recomendada): apartar.** La pasada K sin par, en un día cuyo trozo terminó verde y cuya cobertura no registra
  falla de esa plataforma, se mueve a `data/_k_residuales_via/<V>.json` con su motivo («borde»). No se borra nada
  (mismo criterio que los residuos C0 de #883, decisión de Nicolás del 2026-10-21). Así la serie queda como la escribe
  hoy la producción y no queda K mezclado que mantenga el aviso.
- B: conservarlas como K. Mantiene el aviso de MODIS en todos los volcanes (4.1) y la serie sigue mezclada.
- C: conservarlas con una marca de texto nueva (por ejemplo `"borde_k"`). El tablero ya trata la marca de texto como
  «ni vía ni K» para el aviso (`frontend/cambio_detector.js:186-189`, `:208`), pero es una marca nueva con
  consumidores que hay que auditar (A118) y publica detecciones de K que la producción ya no publica.

Si el trozo de ese día falló o la plataforma figura con falla en `cobertura/*.json`, la pasada no es de borde: se
relanza el trozo (A64, A108) y, si NASA no tiene el gránulo, se aparta con motivo «sin_granulo».

Pasadas sólo en la vía (VIIRS 750: 4 a 64 por volcán; VIIRS 375: 2 a 4; MODIS: 0): se agregan, como los «agregados»
de #883 (`reemplazar_ventana_reproceso.py:82-83`).

### 2.4 Caídas a K (`sin_grilla`, `sin_mxd03`, `geo_distinta`)

Son K que corrió con la vía encendida y lo dice en el record (`pipeline/process_modis.py:636-650`;
`pipeline/process_viirs.py:785-787` y `:2284-2285`; `pipeline/process_viirs_mod.py:1544-1545`). En D2 y D4 hay 0. Regla
propuesta: se conservan tal cual, igual que las escribe el NRT de producción, y el ensayo las cuenta por volcán y
sensor. No mantienen el aviso: `primeraVia` no las cuenta ni como vía ni como K (`frontend/cambio_detector.js:207-210`).
Si P4 trae muchas en un volcán, es un hallazgo para Nicolás antes de aplicar, no algo que se resuelva en el script.

### 2.5 Ventanas y frontera por sensor

- MODIS: `desde = 2025-02-15`, `hasta = 2026-11-02`, y sólo se tocan records SIN `via_codigo_mirova` (K). Un record
  de producción con `via_codigo_mirova: true` nunca se pisa: lo escribió el NRT con la vía y es la fuente. Hoy la
  frontera en los datos es el 2026-11-02 01:15-01:20 UTC en los 11; el último K es del 2026-11-01 08:25-08:30, salvo
  PlanchonPeteroa, con un K el 2026-11-02 01:15 junto a una pasada de la vía a las 01:20 (gránulo vecino: con P4 se
  sabrá si es borde). Los records de P4 del 2026-11-02 al 11-09 que no estén en producción NO se agregan: en ese tramo
  manda el NRT.
- VIIRS: `hasta` = día anterior al encendido de cada VIIRS. P4 llega al 2026-11-09; del 2026-11-10 al encendido hace
  falta otro despacho (o el reproceso de 30 días del NRT después del encendido, SIN VERIFICAR qué cubre).

### 2.6 Dónde vive la unión

Los artefactos vencen a los 30 días (`reproc-retro-paquete.yml:152` y `:161`): D2 hacia el 2026-12-08, D4 hacia el
12-09 y P4 hacia el 12-10. `aplicar-reemplazo.yml` corre en un checkout limpio de `main` (`:58-61`), así que la unión
tiene que estar commiteada antes, como `data/_s154_reproc_k_historico/` en #883. Propuesta: un script local
(`experiments/_s178_reemplazo_via/unir_trozos.py`) que, en un solo proceso (A47), une los tres despachos en
`data/_s178_historia_via/<V>.json` con las reglas de 2.2 (intento más alto, sólo dentro de la ventana del trozo,
rehúsa claves repetidas), y un PR de datos aislado sin consumidores. Tamaño estimado: D2 y D4 pesan 118 MB sobre 395
días; los ~633 días completos, del orden de 190 MB. Para VIIRS conviene esa misma carpeta: el encendido puede caer
después del vencimiento.

## 3. Tupungatito antes del 2026-02-23

Nadie lo cubre: el planificador sellado lo recorta (`plan_trozos.py:10-11`, `:112-117`) porque la tabla de MIROVA no
lo tiene antes del 02-14, el scraper lo rotulaba con 5 km hasta el 02-23 y en 2025 no tiene filas en el OSF. Esa razón
es de la REFERENCIA de la prueba retrospectiva, no de la vía: la vía corre en Tupungatito desde el 02-23 con su grilla.
En la serie operacional hay, antes del 02-23, 787 records K de MODIS, 1.574 de VIIRS 375 y 1.563 de VIIRS 750.
Opciones, sin regla inventada:

| Opción | Qué queda | Costo |
|---|---|---|
| 1. Despacho aparte de la vía para Tupungatito 2025-02-15..2026-02-22 | serie de un solo detector | ~373 días = 19 trozos de 20 días; con la tasa del workflow (`reproc-retro-paquete.yml:17-19`, ~4,4 min por día por 1,25) unas 34 horas-job de Actions y descargas a NASA. El planificador sellado lo rehúsa: hace falta un perfil o un workflow que no sea `_s172_retro_*`, o una enmienda del sellado que decide Nicolás |
| 2. Dejar K en Tupungatito antes del 02-23 | serie mezclada en un volcán | el aviso naranja de MODIS sigue en TODAS las vistas: `notarRecords` guarda la fecha más temprana de todos los volcanes (`frontend/cambio_detector.js:262-278`) y Tupungatito tiene K antes de la vía. Quitarlo exigiría tocar `frontend/` (aviso por volcán) |
| 3. Apartar esos K a `data/_k_residuales_via/Tupungatito.json` | Tupungatito sin MODIS antes del 02-23 | un hueco de 373 días en la serie de MODIS que el operador ve como «sin pasadas»; VIIRS sigue con K hasta su paso |
| 4. Recortar toda la serie de Tupungatito al 02-23 | sin historia antes del 02-23 en ningún sensor | pierde VIIRS K que hoy no molesta; poco sentido antes del paso de VIIRS |

## 4. Aviso del tablero y pruebas que se rompen

### 4.1 Cuándo desaparece el aviso de MODIS

`primeraVia` (`frontend/cambio_detector.js:200-215`) busca, por familia, la primera pasada con `via_codigo_mirova ===
true` que tenga ANTES una pasada K (clave `undefined` o `null`, `:208`). Sin K previa devuelve `null` y no hay aviso
ni línea (`:212`). Las marcas de texto no cuentan como K (`:207-208`). `notarRecords` (`:262-278`) toma la fecha más
temprana de todos los volcanes que la vista cargue (las tres vistas lo llaman: `frontend/index.html:1008`,
`frontend/diario.html:965`, `frontend/mosaico.html:521`).

Consecuencias que el plan tiene que comprobar:

- Basta UN record K de MODIS anterior a la vía en UN volcán cargado para que el aviso siga en todas las vistas. Por eso
  las pasadas sin par (2.3) y Tupungatito (3) deciden si el aviso se va.
- Los 34 volcanes fuera de los 11 tienen K de MODIS del 2026-04-17 al 04-24 y 0 records de la vía: hoy no generan
  aviso, pero si el NRT de los 34 corre la vía sobre esos archivos, el aviso vuelve con su fecha.
- Las vistas por defecto cargan `<V>_recent.json` (100 días, `scripts/build_recent_json.py:34`). Hacia el 2027-02-10
  la ventana de 100 días ya no tendrá K de MODIS y el aviso se irá solo ahí; el reemplazo importa para la serie completa.

Comprobación propuesta (prueba nueva, en el PR de datos, con node como las de `tests/test_cambio_detector_*`): correr
`primeraVia(records, "MODIS")` del módulo real sobre cada `data/mirova_equivalent/<V>.json` de los 45 y sobre el
`_recent` armado con `build_recent_json.py`, y exigir `null` en todos; control que puede fallar: insertar un record K de
MODIS anterior a la vía en una copia y exigir que la fecha vuelva (A110). La misma prueba, por familia, sirve para cada
VIIRS. Después, R8 en el tablero publicado (las tres vistas sin `#aviso-cambio-via-modis`).

Medido en una simulación local y desechable (ver 4.2): con los K de MODIS de los 11 reemplazados o quitados,
`primeraVia(records, "MODIS")` da `null` en los 45 JSON. Con los datos de hoy da la fecha del 2026-11-02 (hay K antes).

### 4.2 Pruebas y guards que se rompen

Método: en el worktree del plan (`D:\vrp-trabajo\worktrees\s178-plan`, `e7cfbaf54`) se corrió la suite completa
(3.540 pruebas) tres veces: sobre los datos de `main` (línea base, árbol quieto), con una simulación MODIS y con una
simulación de los tres sensores (`D:\vrp-trabajo\temporales\s178_plan\simular.py`). La simulación pone los records de
la vía de D2 y D4 en sus ventanas, aparta las pasadas sin par y BORRA el K de la familia fuera de esas ventanas (lo que
cubrirá P4 y Tupungatito antes del 02-23). Después se restauró con `git checkout -- data/mirova_equivalent` (0
diferencias contra `HEAD`); nada se commiteó. Como faltan los tramos de P4, la simulación deja huecos que el reemplazo
real no tendrá: por eso cada falla se clasifica.

Línea base sobre `main`: 3 rojas. `tests/test_guard_regla_c_s134.py::test_p5_diag_nti_max_persistido_en_modis` ya está
roja hoy (los records MODIS de la vía desde el 2026-11-02 no traen `diag_nti_max`; lo atiende #978, borrador). Las dos
de `tests/test_guard_libro_de_pruebas_s146.py` (g1d, g2c) fallan por el disco del worktree (`ValueError: path is on
mount 'C:', start on mount 'D:'`), no por los datos.

**Paso MODIS** (rojas nuevas: 2):

| Prueba | Por qué | Clase |
|---|---|---|
| `tests/test_vigilar_plataformas_s159.py::test_nulo_en_los_datos_reales_ninguna_plataforma_viva_habria_alarmado` y `::test_control_positivo_en_los_datos_reales_quitar_noaa21_alarma` | Terra y Aqua «mueren» 187 días: la simulación borró MODIS de 2026-04..09 | Hueco de la simulación. Con P4 no debería fallar, y es justo el guard que caza un hueco de la unión: correrlo en el ensayo |
| `tests/test_guard_regla_c_s134.py::test_p5_diag_nti_max_persistido_en_modis` | `diag_nti_max` es un campo de K; ya rojo en `main` | Estructural. Se resuelve con #978 (mirar sólo K de MODIS); después del reemplazo esa prueba quedará sin K que mirar y tiene que decir SIN DATO o retirarse, no pasar en vacío |

Todo lo demás pasa con MODIS reemplazado: `tests/test_guard_serie_k_pura_s158.py`,
`tests/test_cambio_detector_frontera_s155.py`, `tests/test_golden_records.py`, `tests/test_banco_paridad_s139.py`.

**Paso VIIRS** (simulación de los tres sensores; rojas nuevas además de las de MODIS: 13):

| Prueba | Por qué | Clase |
|---|---|---|
| `tests/test_guard_regla_c_s134.py::test_p10_cap_path_d_activo_en_perfil_operacional` | ningún record de PCC trae `primary_cluster.d9_capped` (path D, campo de K) | Estructural |
| `tests/test_marcador_mapa_ctx_cluster_s154.py::test_datos_reales_de_lascar_el_primer_marcador_es_el_cumulo` | no quedan records con `final_hotspot_source == "ctx_cluster"` (fuente de K) | Estructural |
| `tests/test_banco_paridad_s139.py::test_linea_base_reproduce_s139` y `::test_por_volcan_y_far_ref` | la línea base es la de K (2,59 %, re-anclada en #883) y los conteos mínimos caen (608 contra 1.000; 46 contra 50) | Estructural (la línea base) más hueco de la simulación (los conteos). Re-anclarla es medir contra MIROVA: es la prueba con candado, no este plan |
| `tests/test_golden_records.py::test_golden_record_present[...]` (4: Láscar y Lastarria 2026-04-08 y 04-12, Villarrica 2026-05-09) | las pasadas golden caen en el tramo de P4 | Hueco de la simulación para la presencia; SIN DATO para `test_golden_record_values`, que mira valores de K y casi seguro cambia |
| `tests/test_guard_anillo_s134.py::test_control_positivo_lascar_cumulo_en_el_crater` | pocos V375 de Láscar desde el 2026-06-01 (n = 12) | Hueco de la simulación; SIN DATO con P4 |
| `tests/test_clasificacion_referencia_s146.py` (3) | su ventana fija es 2026-09-01..09-20 | Hueco de la simulación; SIN DATO con P4 |
| `tests/test_cambio_detector_frontera_s155.py::test_la_frontera_declarada_es_la_de_los_datos` | la simulación borró todo Tupungatito antes del 02-23 y la primera pasada con `codigo_sha` se corrió | Depende de la decisión de Tupungatito (opciones 3 y 4 la ponen roja) |

Dos guards no se rompen pero dejan de decir la verdad, y el plan tiene que tratarlos:

- `tests/test_guard_serie_k_pura_s158.py` y `tests/test_cambio_detector_frontera_s155.py` reconocen K por
  `regimen.codigo_sha`, que los records de la vía TAMBIÉN traen (`codigo_sha: a7a6ae360` en todos los de la
  retrospectiva). Pasan en verde con una serie entera de la vía y el aviso amarillo seguiría diciendo «los datos desde
  el 15 feb 2025 son del detector K» (`frontend/cambio_detector.js:61-70`). #976 (borrador, «el aviso del detector K
  sale de los datos») toca esto; el PR de cada paso tiene que dejar ese aviso y esos dos guards contando K como K (sin
  `via_codigo_mirova`), no «cualquier record con sha».
- Pruebas con records sintéticos que mencionan la vía (`tests/test_cambio_detector_via_modis_s172.py`,
  `tests/test_auto_audit_via_modis_s172.py` y sus pares de VIIRS) no leen `data/` y no cambian.

## 5. Pasos (A45: tag defensivo y «sí» de Nicolás en cada paso que escribe la serie)

Común (antes de MODIS, sin tocar la serie publicada):

1. Esperar el fin de P4 (run 42749607584; a las 09:52 UTC del 2026-11-10: 93 jobs verdes, 6 corriendo, 66 en cola).
   Relanzar los trozos que fallen (`gh run rerun --failed`), una vez, como pide el workflow (`:153-155`).
2. Bajar P4 a `C:\Users\nmend\vrp-temporales\s178_p4\` y correr `contar_cobertura.py` sobre D2, D4 y P4 juntos: 0
   claves repetidas, 0 días del calendario sin record de la vía que tengan K, caídas a K contadas. Llevar el script al
   repo bajo `experiments/_s178_reemplazo_via/`.
3. Decisión de Nicolás: regla de las pasadas sin par (2.3, A, B o C) y Tupungatito (3, opciones 1 a 4).
4. PR de código: `--familia` y `--apartar-sin-par` en `scripts/reemplazar_ventana_reproceso.py` con pruebas
   (sintéticas, con control que puede fallar: una pasada de otra familia no se toca; una sin par se aparta y no se
   borra), `unir_trozos.py`, `ensayo_via.py` (copia de `ensayo_11.py` con sha256 antes y después) y
   `aplicar_modis.sh`. Antes de ese PR: #978 (P5) y #976 (aviso K) resueltos o integrados.
5. PR de datos aislado: `data/_s178_historia_via/<V>.json` (unión de los tres despachos), sin consumidores. Antes del
   2026-12-08, cuando vence D2.

MODIS (ya encendido en producción):

6. Ensayo de los 11 con `--familia MODIS --desde 2025-02-15 --hasta 2026-11-02` sobre `main` fresco: informe por
   volcán (reemplazados, apartados por motivo, caídas a K, agregados, sha256 intacto). Prueba nueva del aviso (4.1)
   corrida sobre el resultado del ensayo en una copia.
7. Pedir el «sí» de Nicolás con los números del ensayo en el mensaje (A45).
8. `aplicar-reemplazo.yml` con `confirmacion: si`, `script: experiments/_s178_reemplazo_via/aplicar_modis.sh`,
   `tag: pre-s178-reemplazo-via-modis` y las pruebas de 4.2 (más la nueva del aviso) en `pruebas`.
9. Después del merge: R8 en el tablero publicado (las tres vistas sin `#aviso-cambio-via-modis` en la serie completa),
   `tests/test_vigilar_plataformas_s159.py` verde, y la regla de publicación en el tablero del `CLAUDE.md` del
   proyecto. Reversión: `git revert` del commit de datos o volver al tag.

VIIRS (cada familia por separado y SÓLO después de su encendido, #974 para 375 y #975 para 750):

10. Fecha de encendido de la familia en los datos: primera pasada con `via_codigo_mirova: true`.
11. Cubrir del 2026-11-10 al día anterior al encendido con otro despacho de la vía (P4 llega al 11-09) y sumarlo a
    `data/_s178_historia_via/`.
12. Antes del ensayo, resolver las pruebas estructurales del paso VIIRS (p10, marcador `ctx_cluster`, línea base del
    banco, golden de VIIRS): cada una se re-ancla a la vía o se retira en un PR propio, con su razón; la línea base del
    banco y los goldens se re-anclan midiendo, que es trabajo de la prueba con candado.
13. Ensayo con `--familia VIIRS375` (o `VIIRS750`), «sí» de Nicolás, `aplicar-reemplazo.yml` con
    `tag: pre-s178-reemplazo-via-v375` (o `-v750`), R8 del aviso de esa familia.

## 6. Lo que queda SIN DATO

- P4 entero: cobertura, pasadas sin par, caídas a K y huecos de enero, abril a septiembre y 2026-10-17..11-09.
- Si las pasadas VIIRS sin par son todas descarte de borde (VIIRS no deja línea en el log; indicio: 42 de 110 en
  Lastarria son el gránulo vecino de la misma órbita).
- Si el K de PlanchonPeteroa del 2026-11-02 01:15 es borde.
- Qué cubre el reproceso de 30 días del NRT de VIIRS después de su encendido.
- Si `test_golden_record_values`, `test_guard_anillo_s134` y `test_clasificacion_referencia_s146` pasan con P4: la
  simulación no lo puede decir.
- Tupungatito: 787 records K de MODIS, 1.574 de VIIRS 375 y 1.563 de VIIRS 750 antes del 2026-02-23, sin vía.

## Verificación limpia (S178, 2026-11-10): CON ERRORES, pendiente de corregir antes de aplicar

Verificador de otro modelo (Sonnet), contra `origin/main` `d7a655a7f`. Confirmó con scripts propios las cifras (42.389 records de D2 y D4, sin repetidos; tablas por volcán y familia; las 217 pasadas MODIS sin par en los logs; Tupungatito antes del 2026-02-23 con 787 MODIS, 1.574 VIIRS 375 y 1.563 VIIRS 750, todos K) y las citas del script de #883. Única cifra corregida: Lastarria VIIRS 375 es 96 de 1.512 (6,3 %). Hallazgos que el plan tiene que resolver:

1. **Falta una tercera regla en el script.** El §2.5 dice que un record con `via_codigo_mirova` true nunca se pisa y que los de P4 desde el 11-02 no se agregan, pero con `--hasta 2026-11-02` el script actual pisaría los records de producción del 11-02 y agregaría los de P4 que falten. Hay que sumarla a `--familia` y `--apartar-sin-par`.
2. **El plan quedó desfasado de main.** #976 y #978 ya están mergeados. Con el reemplazo de MODIS no quedan records K y `tests/test_guard_regla_c_s134.py::test_p5_diag_nti_max_persistido_en_modis` cae por su piso de 20 (lo anuncia su docstring); ningún paso del §5 la reasigna antes de MODIS. La frase del §4.2 sobre el aviso «desde el 15 feb 2025» quedó vieja con #976 (hoy el aviso K sólo sale con records anteriores a esa fecha). Los guards con `codigo_sha` (`test_guard_serie_k_pura_s158.py:34`, `test_cambio_detector_frontera_s155.py:41`) siguen como dice el plan.
3. **GitHub Pages (límite de 1 GB).** `pages-deploy.yml:77` copia `data/` entera al sitio y se dispara con `data/**`. Sumando blobs de main, `data/` pesa unos 784 MB; con imágenes, `_recent` y los ~190 MB de `data/_s178_historia_via/` el sitio llegaría a unos 1.010 MB (aritmética sobre blobs, no medición). La unión tiene que vivir fuera de `data/` o quedar excluida del despliegue (con su prueba).

SIN VERIFICAR por el verificador: la suite completa de las simulaciones del §4.2, que las pasadas VIIRS sin par sean de borde, todo lo de P4 (en curso).
