# Auto-audit por detector y alertas protegidas: plan de implementación (S156)

> Para ejecutar en esta misma sesión, con pruebas primero. Arreglos 2 y 3 de `docs/AUDIT_S155.md` §5.

**Objetivo:** que el auto-audit semanal deje de juzgar una mezcla de dos detectores (C0 y K) y que liste por
nombre cada alerta protegida de MIROVA (1 MW o más, lectura A) que el tablero no publicó.

**Por qué:** desde el 2026-09-18 (fecha de observación) los records son de K y antes de C0. La ventana rodante de
60 días junta las dos mitades: la publicación de VIIRS 375 en negativos limpios sale 31 a 33 % cuando C0 da 86,5 %
y K 1,8 a 2,0 % (F3-02), y el recall de K en VIIRS 375 queda tapado por el de C0 (F3-01). Y el criterio de victoria
de la réplica (ninguna alerta protegida perdida) no tiene instrumento: dos protegidas MODIS de Chillán se perdieron
sin que nada avisara (F3-04).

**Arquitectura:** todo en `scripts/auto_audit_weekly.py` más un campo aditivo en `scripts/banco_paridad.py`
(el `codigo_sha` de cada record). No toca `pipeline/`. La frontera de datos se lee de `frontend/cambio_detector.js`
(`DATOS_K_DESDE_UTC`), que ya vigila `tests/test_cambio_detector_frontera_s155.py`: una sola fuente.

## Decisiones de diseño (y lo que queda fuera)

1. **Detector de un record**: K si trae `regimen.codigo_sha`; si no lo trae, C0 cuando su fecha es anterior a la
   frontera y `sin_marca` cuando no (los 26 MODIS Terra de F2-08). Se dice «detector» y no «régimen» porque
   `REGIMEN` ya nombra focal y nevado en este script.
2. **Detector de una noche**: por su fecha contra la frontera. Una noche se evalúa sólo con records de su mismo
   detector; los demás se cuentan aparte (`records_fuera_de_detector`). Si aparecen records K antes de la frontera,
   un aviso dice que hay que mover `DATOS_K_DESDE_UTC` (pasa al aplicar el histórico).
3. **Sólo el detector vigente decide flags** (K si hay frontera). C0 se informa entero en `por_detector`.
4. **D-9**: decide la regla SN (`clase_mirova`); la original se informa al lado, en recall y en falsas.
5. **Recall**: el flag sigue sobre «cráter», porque las bandas (`RECALL_MIN`) se calibraron sobre cráter en S119 y
   no hay bandas para publicación (A115: no inventar un umbral). La publicación se informa y la protege el punto 7.
6. **Magnitud**: el flag pasa a juzgar la magnitud **publicada** (núcleo F5 en VIIRS 375, `pc.vrp_mw` en los otros
   dos) por **volcán y sensor**, con la misma banda de mediana (0,7 a 1,4) y el mismo mínimo de noches. La mediana
   por volcán con `pc.vrp_mw` queda como información. Se agrega la mediana de pasadas publicadas por noche.
   El texto del flag sub-banda ya no atribuye la causa a S124: la nombra como antecedente (F3-07).
7. **Alertas protegidas**: cada pasada nocturna de la ventana con una fila protegida (lectura A) se lista con su
   estado: publicada, sin publicar, sin record nuestro. Flag por cada una **sin publicar** del detector vigente, sin
   mínimo de n, y dice si la noche del volcán se publicó en otra pasada. Las sin record no son flag (no miramos no es
   no vimos, S150) pero se listan.
8. **Falsas**: por detector, con D-9 SN, y VIIRS 375 por cenit (el `zbin` del banco). Siguen sin alarma (S140).
9. **Historial**: `falsas_pub_pct` y `recall` pasan a ser del detector vigente y la línea dice cuál
   (`detector`), con la regla D-9 usada. Las líneas viejas no traen esa clave: eran mezcla.
10. **Workflow**: el cuerpo del issue declara las bandas reales y que sólo juzga el detector vigente.

Fuera de este plan: las vistas del tablero (parte de la tarea 1.35), deduplicar issues y el watchdog (arreglo 7),
la vigilancia de la sombra (arreglo 4).

## Tareas

1. Pruebas que fallan en `tests/test_auto_audit_por_detector_s156.py`: frontera leída del JS; detector de record y
   de noche; recall separado por detector y flag sólo del vigente; D-9 SN quita una noche mínima; magnitud por
   volcán y sensor con el núcleo F5; protegidas sin publicar dan flag y las sin record no; la línea del historial
   dice el detector.
2. Implementar en `scripts/auto_audit_weekly.py` hasta verde; `codigo_sha` y `z` en los recs del banco.
3. Suite de los tests del audit y del banco en verde sobre árbol quieto (A112).
4. Correr el audit local con la referencia fresca de Mirova-v1 y `OUTDIR` desviado; comparar contra
   `experiments/_s155_audit/frente_3/` (C0 86,5 % y K 1,8 a 2,0 % en falsas V375; recall V375 K 91,5 %).
5. Verificador con contexto limpio.
6. PR, CI con conclusión, merge antes del lunes 2026-10-20 09:00 UTC.
