# V1a: verificación de los hallazgos de F1a sobre la regla con que se adoptó K

## 1. Encabezado

- Hora: inicio 2026-10-22 03:48 UTC (`date -u`); servidor de GitHub a mitad de la sesión: `Date: Thu, 22 Oct 2026
  04:18:53 GMT` (`gh api -i rate_limit`); cierre de mediciones 04:23:52 UTC.
- Commit medido: código y datos de `d516b9d8c` (instantánea `D:\vrp-trabajo\temporales\s160_audit\main\`). En el
  worktree `C:\vrp-trabajo\s159-pruebas` (HEAD `2b50c8a4a`), `experiments/_s151_prereg_fk_11`, `experiments/_s153_fk_v2`,
  `scripts/banco_paridad.py`, `scripts/clase_mirova.py` y `frontend/index.html` son idénticos a `d516b9d8c`
  (`git diff --stat d516b9d8c -- <esas rutas>` vacío); el `index.html` que ejecuta el evaluador tiene el mismo sha256
  que el de la instantánea (`f711c61dfb96555b...`). Producción para el control de cobertura: `main\data\mirova_equivalent`.
- Datos de los brazos: las uniones que armó F1a en `D:\vrp-trabajo\temporales\s160_audit\f1a\` (v1_union, v2a_union,
  v2b_union), sólo lectura. La de V1 la verifiqué contra el `v1.json` del repo (sección 5, VERIFICADO LIMPIO).
- Modelo y esfuerzo: Opus 5.5, esfuerzo bajo según el entorno de esta sesión (la tarea pedía `high`; lo dejo dicho).
- CARPETA: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\v1a\`. Datos fabricados en
  `D:\vrp-trabajo\temporales\s160_audit\v1a\` (139 MB; los JSON de cada placebo se borran tras evaluarlo, quedan los logs
  en `salidas\placebos\logs\`).
- `caminos.md` escrito y sellado antes de abrir archivos citados: sha256
  `6dfb9c71c2d88095c652211f32298a542ba8482329f5d05a2e820eed3006fbde`, 03:48:40 UTC.
- Criterio sin cambios desde el sello: `git -C C:\vrp-trabajo\s159-pruebas diff 60762a939 -- docs/PLAN_AUDITORIA_S160.md`
  da 0 líneas (no es hallazgo).
- Qué NO miré: el informe y la matriz de F1a (a propósito; sí leí al final dos salidas crudas que la lista cita,
  `medir_k2_resumen.txt` y `mecanismo_t1off.txt`, para comparar); el veredicto y los resultados de D25 (#890; leí sólo
  el código de `evaluar_d25.py`, no sus salidas); ninguna imagen de MIROVA (no rendericé nada: lo de Lastarria del
  18-abr se apoya en los records y en el informe del segundo lector de S153, que NO re-verifiqué contra la imagen);
  R7 (no está en mi lista); la regla SN de D-9 más allá de ver que su veredicto de K coincide con el original en V1 y V2.
- Llamadas a la API de GitHub: 3 de 5 (artefactos del run 38639658446, el run, la hora).

## 2. En una pantalla

1. 161, primera mitad: CONFIRMADA por otro camino y más fuerte. Un placebo SIN información (apagar al azar la
   publicación del 1 % de los records de C0, sin mirar etiqueta) sale CUMPLE en 16 de 30 semillas en V1 (53 %, Wilson
   [36, 70]) y 5 de 10 en V2. La causa es P2 con tolerancia 0 (el gemelo G es idéntico a C0 en 4.820 de 4.820 pasadas).
   El placebo del auditor (`triggered_test1` en False) NO es sin información: apaga exactamente 21 publicaciones que C0
   hace sólo por el rescate del Test 1 (`index.html:1613`), las 21 fuera de alerta.
2. 161, segunda mitad: CONFIRMADA. K deja de publicar 69 a 94 % de lo que C0 publica y conserva todas las protegidas
   que deciden; un apagado al azar del mismo tamaño haría eso con probabilidad 3e-4 (MODIS V1) a 6e-39. La adopción de
   K no se explica por la debilidad del instrumento. Gravedad mía 3, no 5: no tuerce la decisión de producción, pero
   la misma P2 está en el evaluador de D25 (`evaluar_d25.py:347-354`), que es un A/B pendiente.
3. 162: CONFIRMADA EN PARTE (gravedad 2). Con OCR, V2 queda PENDIENTE por Lastarria V375 2026-04-18 04:42, pero el
   pre-registro fijó tabla sola para V2, la regla dice que el OCR se mira y no decide, y S153 sí la miró: K ve el objeto
   que MIROVA ve (19,6 km, `far`) y C0 publicaba otro (0,055 MW a 2,77 km por el Test 1).
4. 163: CONFIRMADA (gravedad 2-3), salvo «el intento 2 no está en ninguna parte», que queda SIN DATO.
5. Celdas: R6 FALLA CONFIRMADA (con placebo propio); R11 FALLA CONFIRMADA EN PARTE (sólo por P3, que no puede fallar;
   su regla sustituta se cumple: 0 protegidas cruzan 1 MW hacia abajo); R17 FALLA REFUTADA como defecto heredado que
   toque el veredicto (el cruce de canales de `alerta_protegida` da 0 casos en V1 y V2).

## 3. Hallazgos (orden por gravedad)

### V1a-01 (verifica 161, primera mitad; funde con R6)
- TÍTULO: La regla con que se adoptó K da CUMPLE a un placebo sin información: apagar al azar el 1 % de las
  publicaciones de C0 cumple en la mitad de las semillas, porque P2 tiene tolerancia 0.
- SCRIPT:SALIDA: `placebos_v1a.py` → `salidas\placebos\filas_V1.jsonl`, `filas_V2.jsonl`, `resumen.txt`
  (`resumir_placebos_v1a.py`); mecanismo en `experiments\_s151_prereg_fk_11\evaluar_fk.py:613-641` (P2: `ruido =
  len(e0 ^ eg)`, GANA si `sx < s0 - ruido`) y `salidas\v1_base.log` l. 29-31 (G contra C0: 944/944, 1.944/1.944,
  1.932/1.932 pasadas con la misma decisión) y l. 88-100 (`ruido 0.0` en las seis sumas de lectura A).
- QUÉ PASA: un evento volcánico no cambia nada en el placebo; sólo se le quita al tablero, al azar, una de cada cien
  pasadas publicadas. Como C0 publica en 88 % de los negativos limpios de VIIRS 375, quitar al azar casi siempre quita
  más negativos que alertas Muy Bajo, y P2 declara GANA con una diferencia de 1 pasada (rango medido de la reducción:
  -2 a 10 en VIIRS 375), porque el «ruido» es el desacuerdo entre C0 y un gemelo que corre el mismo código determinista
  y por eso vale 0. El único freno es P1, y con 36 protegidas en V1 un apagado chico las esquiva a menudo.
  Resultados (veredicto global de K, lectura A, regla original):
  | placebo | V1 | V2 |
  |---|---|---|
  | neutro (disfraz compensado, sin cambio de publicación) | NO CUMPLE (no gana) | NO CUMPLE (no gana) |
  | ganancia ×0,8 y ×1,25 | NO CUMPLE (no gana), 2 de 2 | no corrido |
  | permutar records entre pasadas del mismo volcán y sensor | 0 de 12 CUMPLE (12 vetos) | 0 de 4 (PENDIENTE, P2 pierde) |
  | azar 1 % | **16 de 30 CUMPLE** (53 %, [36, 70]) | **5 de 10** (50 %, [24, 76]) |
  | azar 3 % | 3 de 12 (25 %, [9, 53]) | no corrido |
  | azar 10 % | 2 de 12 (17 %, [5, 45]) | 0 de 4 |
  | `triggered_test1` en False sin compensar (el del auditor) | CUMPLE | CUMPLE |
- CÓMO SE VE EN EL DASHBOARD: invisible. Es un defecto del instrumento de decisión, no del tablero.
- CÓMO REPRODUCIRLO: `python C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\v1a\placebos_v1a.py V1 <salida> azar_0.01 --semillas 30`
  (semillas 0 a 29; V1 2026-08-29 a 2026-10-08, referencia congelada con OCR del instrumento; V2 2026-03-01 a 2026-06-12,
  tabla sola).
- CONFIANZA: CONFIRMADO (medido; el nulo neutro y la permutación muestran que el instrumento sí puede decir no).
- GRAVEDAD: 3. Sostuvo una decisión de producción, pero V1a-02 muestra que esa decisión no depende de la debilidad. La
  misma P2 la hereda el evaluador de D25 (`experiments\_s157_prereg_d25\evaluar_d25.py:347-354`: `ruido` del gemelo y
  GANA si `sd < sk - ruido`), que es un A/B pendiente con un efecto esperado chico: ahí sí puede torcer. Sobre la
  gravedad 5 del auditor: vale si se mira sólo la etiqueta CUMPLE; no vale para la decisión de K.

### V1a-02 (verifica 161, segunda mitad)
- TÍTULO: K supera por órdenes de magnitud a un placebo de su mismo tamaño: deja de publicar 69 a 94 % de lo que C0
  publica y no pierde ninguna protegida que decida.
- SCRIPT:SALIDA: `margen_k_v1a.py` → `salidas\margen_k.txt` (desde las tablas por pasada `t_C0_K.json` que el
  evaluador original arma con el predicado ejecutado con node).
- QUÉ PASA: si K fuera un apagado al azar, conservar todas las protegidas sería un milagro. Probabilidad hipergeométrica
  de que un apagado al azar del mismo tamaño no toque ninguna protegida: V1 MODIS 3,4e-4 (106 de 115, 3 protegidas);
  V1 VIIRS 375 6,0e-15 (1.363 de 1.736, 21); V1 VIIRS 750 1,7e-12 (424 de 479, 12); V2 tabla sola MODIS 2,0e-8,
  VIIRS 375 3,3e-20 (2.088 de 3.032, 38), VIIRS 750 6,1e-29 (658 de 857, 42). En sumas de P2, K baja VIIRS 375 de 734 a
  37 (V1) y de 863 a 63 (V2), contra un máximo de 10 y 13 del placebo de 1 %. Mi conteo aproximado de protegidas
  (etiqueta `pos` con `vrp_ref` de 1 MW o más) coincide con el del evaluador (21, 12, 3 en V1; 38, 42, 6 en V2); las 2
  que K «pierde» en V1 VIIRS 375 son las 2 de Suomi NPP sólo OCR que el pre-registro saca de la decisión.
- CÓMO SE VE EN EL DASHBOARD: no aplica.
- CÓMO REPRODUCIRLO: `python ...\v1a\margen_k_v1a.py` (requiere haber corrido el evaluador con `--tmp` en
  `D:\vrp-trabajo\temporales\s160_audit\v1a\base_v1\tmp`, `tmp_v2_si`, `tmp_v2_no`; comandos en `salidas\v1_base.log`
  y sección 5).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1 (es la confirmación de que la decisión se sostiene; no es un defecto).

### V1a-03 (verifica 161, matiz del placebo del auditor; funde con R17)
- TÍTULO: El placebo del auditor (`triggered_test1` en False) no es sin información: es una versión mínima del
  tratamiento, que apaga las 21 publicaciones de C0 que existen sólo por el rescate del Test 1, todas fuera de alerta.
- ARCHIVO:LÍNEA: `frontend/index.html:1613` en `d516b9d8c` (el auditor cita 1612, que es la línea del comentario):
  `if ((r.vrp_mw ?? 0) === 0 && r.discarded_reason && !r.triggered_test1) return false;`. Salida:
  `salidas\placebos\logs\V1_t1off_0.log` (MODIS 110 de 893 negativos publicados → 106; VIIRS 750 321 → 308).
- QUÉ PASA: en 22 records de C0 en V1 el pipeline descartó el cúmulo (`vrp_mw` 0 con `discarded_reason`) pero el
  Test 1 disparó, y el tablero los publica igual por esa línea. Apagar el flag los calla: 4 pasadas MODIS y 17 VIIRS 750
  (13 negativos limpios en V750, 4 en MODIS, 4 sin información; 0 alertas, coincide con `mecanismo_t1off.txt` del
  auditor). Callar publicaciones que caen todas fuera de alerta es justo lo que la regla debe premiar; por eso no es un
  placebo, y el disfraz compensado (borrar `discarded_reason` en esos mismos records) da exactamente las sumas de C0 y
  NO CUMPLE. La conclusión de 161 no cae por esto, porque V1a-01 la sostiene con un placebo de verdad. Con K en
  producción `triggered_test1` es siempre False, así que la rama del flag en la línea 1613 queda muerta (SOSPECHA: no lo
  medí sobre los datos de producción).
- CÓMO SE VE EN EL DASHBOARD: con C0 (antes de K) se veían 21 pasadas en 41 días como detección en el cráter cuando el
  pipeline había descartado el cúmulo; con K, invisible.
- CÓMO REPRODUCIRLO: `python ...\v1a\placebos_v1a.py V1 <salida> t1off,neutro`; ejemplo `Villarrica|VIIRS750|2026-08-29 06:18`.
- CONFIANZA: CONFIRMADO (en V1 y V2); la parte de producción, SOSPECHA.
- GRAVEDAD: 1 (atribución del placebo; no cambia ningún veredicto).

### V1a-04 (celda R11)
- TÍTULO: P3 no puede fallar en VIIRS (mediana de d exactamente 0 con intervalo [0, 0]) mientras la razón con MIROVA
  empeora; la regla sustituta del §5 sí se cumple.
- SCRIPT:SALIDA: `salidas\v1_base.log` y `salidas\v2_solotabla_si.log`, sección 7; `cruce_1mw_v1a.py` →
  `salidas\cruce_1mw.txt`.
- QUÉ PASA: más de la mitad de las alertas no cambia de magnitud entre C0 y K, así que la mediana de la diferencia es 0
  y su intervalo no puede quedar sobre 0: en unidades del veredicto, esa masa en cero es una tolerancia mayor que el
  efecto. Medido: razón mediana VIIRS 375 C0 0,748 → K 0,620 (V1, n 239) y 0,762 → 0,669 (V2, n 400), P3 CUMPLE en las
  dos. La regla de adopción lo reconoce (`REGLA_ADOPCION.md` §5, TEXTO: «P3 está anulado por construcción en VIIRS
  375») y pone en su lugar que ninguna protegida que C0 muestra sobre 1 MW quede bajo 1 MW con K: medí 0 en V1, en V2
  con tabla sola y en V2 con OCR (control: con umbral 0,1 MW aparecen 23, 25 y 43 cruces). Las otras tolerancias del
  instrumento no fallan R11: el ruido de P2 es 0 (V1a-01 es el problema opuesto), el control de cobertura tolera 5 % de
  pasadas faltantes y faltan 0 de 4.820 (V1) y 0 de 12.023 (V2) en los 11 Tier A (`faltantes_v1a.py` →
  `salidas\faltantes.txt`, con control positivo), y el de determinismo tolera 2 % y el gemelo difiere en 0.
- CÓMO SE VE EN EL DASHBOARD: la magnitud de VIIRS 375 con K se lee entre 12 y 17 % más baja (razones 0,620/0,748 y 0,669/0,762) que con C0 en las alertas
  comunes; ninguna protegida baja de Bajo a Muy Bajo.
- CÓMO REPRODUCIRLO: `python ...\v1a\cruce_1mw_v1a.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (la regla sustituta cubre el caso que importa al operador).

### V1a-05 (verifica 163)
- TÍTULO: Los datos con que se adoptó K no están en el repo: la rama del run de V1 trae un intento con cobertura
  despareja, las uniones de S153 vivían en un temporal que ya no existe y el artefacto vence el 2027-01-14; la unión
  rehecha reproduce `v1.json` exacto.
- SCRIPT:SALIDA: `git show origin/s146-ab/38639658446:experiments/_s146_ab_sin_test1/salidas/38639658446/cobertura.txt`
  (gemelo sin Villarrica, 493 pasadas faltantes; «COBERTURA DESPAREJA»); `git ls-tree` de esa rama: 11, 11, 11 y 10
  JSON por brazo; `ls C:\Users\nmend\AppData\Local\Temp\claude\v1_38639658446` (y v2a, v2b): no existen;
  `experiments\_s153_fk_v2\README.md:4-6` dice que las uniones estaban en ese temporal; API: artefacto `s146ab-todo`
  del run 38639658446 con `expires_at` 2027-01-14T11:38:26Z, run en `run_attempt` 3; `salidas\comparar_v1_repo.txt`:
  veredictos y 24 de 24 sumas iguales a `experiments\_s153_fk_v2\v1.json` (con un `index.html` distinto al de S153,
  sha 4014103e… entonces y f711c6… hoy).
- QUÉ PASA: la evidencia de una decisión de un SDA en producción se puede rehacer hoy, pero sólo combinando la rama con
  un artefacto que expira en menos de tres meses. «El intento 2 no está en ninguna parte»: SIN DATO (no pagué la lista
  de artefactos por intento).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: los comandos de arriba; evaluador sobre la unión de F1a en `salidas\v1_base.log`.
- CONFIANZA: CONFIRMADO (salvo lo del intento 2).
- GRAVEDAD: 2 (no tuerce ninguna alerta; es trazabilidad, que pesa por la Resolución CPLT N°372; el auditor dio 3 y no
  lo discuto fuerte).

### V1a-06 (verifica 162)
- TÍTULO: Con tabla y OCR el veredicto de K en V2 pasa de CUMPLE a PENDIENTE DE REPETICIÓN por una sola pasada sólo
  OCR, pero la regla la excluyó antes de ver datos y S153 la resolvió como otro objeto.
- SCRIPT:SALIDA: `salidas\v2_solotabla_si.log` (K lectura A CUMPLE) y `salidas\v2_solotabla_no.log` l. 73-74
  («perdida PENDIENTE DE REPETICION ... Lastarria|VIIRS375|2026-04-18 04:42 | MIROVA 1.29 MW | VIIRS_NOAA20»);
  `evaluar_fk.py:59-62` (V2 `solo_tabla: True`); records: C0 `summit`, `triggered_test1` True, 0,055 MW, cúmulo a
  2,769 km, `final_hotspot_source` `test1_roi`; K `far`, 0,531 MW a 19,632 km, `ctx_cluster`.
- QUÉ PASA: el OCR trae para esa pasada una alerta de 1,29 MW con `Distancia_km` 0,0 (antes del 2026-06-13 el OCR no
  medía distancia, A119), y la tabla no tiene fila VIIRS 375 de esa hora. `experiments\_s153_fk_v2\lector2\INFORME.md`
  l. 48, TEXTO: «**20,0 km** (estrella verde de la imagen propia, y = 146-147)» y veredicto «**LEJANO**», y K pone su
  cúmulo a 19,6 km: K calla un objeto lejano que MIROVA también ve lejano, y C0 publicaba otro objeto más débil cerca
  del cráter. La repetición que la regla prevé no se corrió, pero la pérdida no decide (`REGLA_ADOPCION.md` §4.2,
  TEXTO: «No deciden, pero se miran») y ya se miró (`experiments\_s153_fk_v2\verificador\VERIFICADOR.md` l. 86-91).
  No re-verifiqué la imagen.
- CÓMO SE VE EN EL DASHBOARD: invisible para K.
- CÓMO REPRODUCIRLO: `python experiments\_s151_prereg_fk_11\evaluar_fk.py --ventana V2 --raiz <v2a_union> --raiz
  <v2b_union> --logs <v2a>\logs --logs <v2b>\logs --solo-tabla no --ruido-de <base_v1\res.json> --out ... --produccion
  D:\vrp-trabajo\temporales\s160_audit\main\data\mirova_equivalent`.
- CONFIANZA: CONFIRMADO EN PARTE (el cambio de veredicto, sí; que sea un defecto que deje la decisión sin respaldo, no).
- GRAVEDAD: 2.

## 4. Veredictos por afirmación de la lista

| ítem | veredicto | mi gravedad | evidencia |
|---|---|---|---|
| 161 (placebo cumple; K supera el margen) | CONFIRMADO en sus dos mitades, con matiz: el placebo del auditor no es sin información (V1a-03), pero uno sin información también cumple (V1a-01) | 3 | V1a-01, V1a-02, V1a-03 |
| 162 (veredicto cambia con la referencia) | CONFIRMADO EN PARTE | 2 | V1a-06 |
| 163 (datos de la adopción fuera del repo) | CONFIRMADO; «intento 2» SIN DATO | 2 | V1a-05 |
| celda R6 FALLA | CONFIRMADO (placebo propio de azar 1 %); con los placebos literales de R6 (ganancia y desplazamiento) la regla dice NO | 3 | V1a-01 |
| celda R11 FALLA | CONFIRMADO EN PARTE: sólo por P3; P2, cobertura y determinismo no | 2 | V1a-04 |
| celda R17 FALLA | REFUTADO como defecto heredado que toque el veredicto: el predicado lee el flag por diseño (V1a-03) y el cruce de canales de `clase_mirova.alerta_protegida` da 0 pasadas | 1 | `cruce_canales_v1a.py` → `salidas\cruce_canales.txt` |

## 5. SEGUIMIENTOS (fuera de mi eje)

- S-1. La fila OCR de Lastarria VIIRS 375 2026-04-18 04:42:01 sigue en `d516b9d8c` como `ALERTA_TERMICA_OCR`, 1,29 MW,
  Distancia 0.0 (`data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` l. 815), y comparte el mismo archivo
  `data/png/Lastarria/20260513_014035_VIIRS375_Dist.png` con las filas de 06:06 y 06:24 (l. 811 y 813). Si el segundo
  lector de S153 tiene razón (20 km), es un FALSO_POSITIVO_OCR y cualquier evaluación futura con el combinado lo
  contará como protegida. Para `experiments/_s159/referencia_estable/` o la auditoría de Mirova-v1. CONFIRMADO lo de las
  filas; SOSPECHA lo de la clase.
- S-2. `experiments\_s157_prereg_d25\evaluar_d25.py:347-354` hereda P2 con el ruido del gemelo y GANA con cualquier
  reducción neta (V1a-01). No abrí resultados de D25. SOSPECHA de efecto.
- S-3. La tabla de `d516b9d8c` (`latest_consolidado.csv`) trae 7.077 filas en la ventana de V1 contra 7.262 del
  congelado del instrumento (`salidas\cruce_canales.txt`): pérdida de filas conocida de la tabla. El instrumento lee su
  copia congelada, así que no le afecta; cualquier re-evaluación con la referencia de `d516b9d8c` en lugar del
  congelado verá otro sustrato.
- S-4. `evaluar_fk.py` dice en la sección 10 que «DECIDE la original», y `REGLA_ADOPCION.md` §3 manda calcular original
  y SN y quedarse con la más estricta. En V1 y V2 las dos dan CUMPLE para K lectura A (`salidas\v1_base.log` l. 207-251;
  `v2_solotabla_si.log` l. 246-305), así que hoy no cambia nada. De forma.

## 6. VERIFICADO LIMPIO

- La unión V1 rehecha por F1a reproduce `experiments\_s153_fk_v2\v1.json`: veredictos iguales, 24 de 24 sumas
  iguales, mismos controles (`salidas\comparar_v1_repo.txt`). Vara: el `v1.json` con que se decidió.
- El instrumento sí puede decir NO a un nulo: disfraz neutro da EMPATE en las seis sumas y NO CUMPLE (V1 y V2); ganancias
  ×0,8 y ×1,25 dan NO CUMPLE; la permutación da veto 12 de 12 en V1. Vara: el veredicto global del propio evaluador.
- Cobertura de C0 contra producción: 0 pasadas de producción faltan en C0 en V1 (4.820) y en V2 (12.023), 11 Tier A,
  con control positivo inyectado que sí se detecta (`salidas\faltantes.txt`). Nota: la primera versión del script
  mezclaba los 34 volcanes no Tier A y daba 2.843 faltantes; corregido y anotado en el script.
- Cruce de canales (§11.1.2 del plan): 0 pasadas con alerta OCR de 1 MW o más y FALSO_POSITIVO en la tabla en el
  congelado de V1 (28 alertas OCR), de V2 (194) y en la referencia de `d516b9d8c` en la ventana V1 (28), con control
  sintético que sí se cuenta (`salidas\cruce_canales.txt`). Implementación propia que no importa `banco_paridad` ni
  `clase_mirova`.
- Protegidas que cruzan 1 MW hacia abajo con K: 0 en V1, V2 tabla y V2 combinado (`salidas\cruce_1mw.txt`).
- Hashes de la referencia de `d516b9d8c`: `latest_consolidado.csv` bc1522c24c924cb5, `registro_vrp_ocr.csv`
  94679246acbd0db5 (coinciden con el preámbulo). El instrumento usa además su propio congelado
  (`_congelado_v2`: consolidado a4a411a6b88d8fc3, OCR bf56d5abe6ec463a, sha con LF).

## 7. SIN DATO

- Si los artefactos del intento 2 del run 38639658446 existen: no listé por intento (tope de llamadas a la API).
- La imagen propia de MIROVA de Lastarria 2026-04-18 04:42: no la rendericé; me apoyo en `lector2\INFORME.md`.
- Si con K en producción algún record conserva `triggered_test1` True (V1a-03): no lo medí sobre `data/mirova_equivalent`.

## 8. FUERA DE ALCANCE

- R7 (barajado) y los demás hallazgos de F1a que no están en `LISTA.md`.
- Proponer el arreglo de P2 (por ejemplo una tolerancia de muestreo del orden de la raíz de la suma): lo decide quien
  orquesta.

## Las dos preguntas del instrumento, por medición

- Placebos (`placebos_v1a.py`): (1) si la regla aceptara placebos, el azar daría CUMPLE y lo da; (2) si el placebo no
  llegara al evaluador, las sumas serían las de C0 en todos los casos: no lo son (azar y t1off cambian, neutro no).
- Margen (`margen_k_v1a.py`): (1) si K fuera azar, p0 sería grande; (2) si las tablas estuvieran vacías, N sería 0.
- Cruce 1 MW, faltantes, cruce de canales: cada uno con control positivo que sí aparece en la salida.
