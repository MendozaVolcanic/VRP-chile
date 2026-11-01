# Verificador con contexto limpio de D-42, vuelta 2: cierre de V42-01, V42-02 y V42-04

## 1. Encabezado

- Hora del servidor al empezar: **Thu, 22 Oct 2026 15:30:35 GMT** (`gh api -i repos/MendozaVolcanic/VRP-chile`, header `Date`); al cerrar `caminos.md`, 15:31:23 GMT; al cerrar este informe, Thu, 22 Oct 2026 16:11:27 GMT.
- Commit medido: **452956cf8** (`C:\vrp-trabajo\s159-evaluador`, rama `s159-evaluador-d25`, arbol limpio al empezar). Diff verificado: `git diff 981cceda7 452956cf8` (33 archivos; codigo: `experiments/_s157_prereg_d25/evaluar_d25.py` +9/-7, `tests/test_evaluar_d25_calib_p2_s160.py` +48/-1, `mutar_calib_p2.py` +6, `rojo_calib_p2.py`, `placebo_1pct.py`, `resumir_placebo.py`).
- Modelo y esfuerzo: Claude Fable 5.1, esfuerzo por defecto del agente.
- CARPETA: `C:\vrp-trabajo\s159-evaluador\experiments\_s159\instrumentos\verificador_d42\vuelta2\` (`caminos.md` sellado antes de abrir nada, sha256 del contenido anterior al pie: `head -n -4 caminos.md | sha256sum` = fdaee9eb...; scripts `v10`, `v11`, `v16` con sus salidas; `hallazgos.csv`).
- Disco: C: 14 GB, D: 8,6 GB libres.
- Lo que NO mire: `calib_p2/README.md` (hasta despues de escribir los veredictos; y al final tampoco lo abri); ningun dato del A/B real; las partes del evaluador fuera del diff; los JSONL del placebo los lei solo por sus campos `n`, `neto`, `falsos_gana`, `calibrada`, `sin_calibrar`.

## 2. En una pantalla

1. **V42-02 y V42-04 cerrados**: la prueba nueva corre `contar` sobre 3 noches x 4 pasadas en que solo D se equivoca, exige INDECIDIBLE en `ver["P2|VIIRS375"]` y en `global_ventana`, y guarda su poder (sin calibrar PIERDE, calibrada False); mi mutacion m07 cae por asercion contra las pruebas de hoy (v11) y en el corredor del implementador (re-corrido: m07 y n04 ATRAPADA, control 75 pruebas 0 fallas). `n_sorteos` y `semilla_calibracion` salen ahora de `calibrar_p2` (`int(n_rep), int(semilla)`, l. 487) y quedan None en los dos caminos que no calibran.
2. **Rojas: CONFIRMADO** re-corrido: 26 de 39 por asercion contra 5f986a209 (0 otra, 0 error; las 13 que pasan son los mismos candados de la vuelta 1), y contra b57ecfe62 la de V42-04 roja por asercion y la de V42-02 verde (es candado: b57ecfe62 ya publicaba el veredicto calibrado).
3. **Suite 2.417 y probar 31 de 31: CONFIRMADO EN PARTE**: los numeros se reproducen (mi suite sola: 2.417 verdes; mi probar: 31 de 31), pero «con el arbol quieto» vuelve a no sostenerse en la corrida del implementador: `status_antes_v42` 14:55:21 y `status_despues_v42` 15:29:11 son 33,8 min para 52,2 min de mutaciones + 27,5 de probar + 6,3 de suite (V42-11, gravedad 1, misma observacion que V42-06).
4. **V42-01, la curva**: los conteos se reproducen (`v10`): la calibracion corrio en 0, 29, 50 y 62 % de las celdas en V1 (1, 5, 10, 20 %) y en 10, 58, 98 y 100 % en V2; GANA calibrada 0 en todas; PIERDE en VIIRS 375 75 a 100 % en los puntos que valen. **Pero el control no podia fallar con K**: de las 7.551 pasadas discordantes que el placebo creo en las 8 curvas, **6.471 (85,7 %) son alertas bajo 1 MW que D dejo de publicar** (error nuevo de D) y solo 1.080 (14,3 %) negativos limpios (error que D deja de cometer); en VIIRS 375 los negativos son 8,7 a 19,8 %. Apagar a ciegas publicaciones de K cuesta seis veces mas de lo que rinde, asi que el neto es positivo por construccion y GANA es imposible: el placebo mide la composicion de lo que K publica, no si P2 «premia publicar menos a ciegas» (V42-10, gravedad 3). Propuesta de placebo que si podria fallar, en §5.

## 3. Veredicto por afirmacion

| # | Afirmacion | Veredicto | Gravedad | Evidencia |
|---|---|---|---|---|
| 1 | V42-02: prueba nueva en `contar`, 3 x 4 solo D, INDECIDIBLE en `ver` y ventana; atrapa m07 por asercion; corredor 30 de 30, control 75 | **CONFIRMADO** (30 de 30 lo acepto del artefacto del implementador mas mi re-corrida de las 2 nuevas con su control; las 28 anteriores las re-corri enteras en la vuelta 1 sobre b57ecfe62 y el diff no toca lo que vigilan) | 0 | `tests/test_evaluar_d25_calib_p2_s160.py:180-223`; `v11_mutaciones_propias_v2_salida.txt`; `mutaciones_rerun_v42.txt` |
| 2 | V42-04: `n_sorteos` y `semilla_calibracion` desde lo que `calibrar_p2` uso; None si no corre | **CONFIRMADO** | 0 | `evaluar_d25.py:487` (`return ..., int(n_rep), int(semilla)`), `:505` (None iniciales), `:518-521` (`det.update(... n_sorteos=n_usados, semilla_calibracion=semilla_usada)`), `:1044` (`imprimir` con `%s`); mutacion n04 ATRAPADA; prueba `test_el_detalle_dice_los_sorteos_y_la_semilla_que_la_calibracion_uso` |
| 3 | Rojas 26 de 39 contra 5f986a209; la de V42-04 roja contra b57ecfe62 | **CONFIRMADO** | 0 | `v16_rojo_rerun_5f986a209_salida.txt` (39, 26 asercion, 0 otra, 0 error, 13 pasan); `v16_rojo_rerun_b57ecfe62_salida.txt` (2 seleccionadas, 1 roja por asercion `(1000, 161) == (20, 7)`, 1 verde) |
| 4 | Suite 2.417 y probar 31 de 31 con el arbol quieto | **CONFIRMADO EN PARTE** (numeros si, reproducidos: suite sola 2.417 y probar 31 de 31; «arbol quieto» no en la corrida del implementador, V42-11) | 1 | `suite_rerun_v2.txt`, `probar_rerun_v2.txt`, `status_antes_v42.txt:1`, `status_despues_v42.txt:1`, `mutaciones_salida_v42.txt` |
| 5 | V42-01: curva 1/5/10/20 %, calibracion en la mayoria de las celdas en V1 20 % y V2 5/10/20 %, GANA 0 de 20, PIERDE 75 a 100 % en VIIRS 375 | **CONFIRMADO EN PARTE**: los numeros si; la conclusion de control no, porque el placebo no puede dar GANA con K (V42-10) | 3 | `v10_placebo_curva_salida.txt` |

## 4. Hallazgos

### V42-10
- TITULO: El placebo «apagar al azar el p % de las publicaciones de K» no puede fallar con K: lo apagado es 86 % alertas bajo 1 MW y 14 % negativos limpios, asi que el neto de P2 es positivo por construccion y mide la composicion de K, no si P2 premia publicar menos a ciegas
- SCRIPT:SALIDA: `v10_placebo_curva.py` : `v10_placebo_curva_salida.txt`, sobre `calib_p2/placebo_{1pct,0.05,0.10,0.20}_{V1,V2}.jsonl`; diseño en `calib_p2/placebo_1pct.py:11-13` (criterio: «P2 calibrada no puede dar GANA en mas del 5 % de las semillas») y `:126` (`rng.sample(publicadas, n_apagar)` sobre TODAS las publicaciones de K).
- QUE PASA: una publicacion de K que D apaga aporta a P2 +1 si era una alerta bajo 1 MW (D comete un error nuevo) y -1 si era un negativo limpio (D deja de cometerlo); una protegida o una pasada sin etiqueta no aporta. Reconstruido desde `n` y `neto` de cada celda (alertas = (n + neto)/2, negativos = (n - neto)/2; paridad verificada en las 640 celdas): sobre las 8 curvas, 6.471 alertas contra 1.080 negativos (14,3 %); por sensor y punto, VIIRS 375 entre 8,7 y 19,8 % de negativos, VIIRS 750 entre 12,5 y 52,2 %. Con esa composicion, GANA exige que entre las apagadas haya mas negativos que alertas: con 5 o mas discordantes y p = 0,14 eso casi nunca pasa (celdas con neto < 0: 0 de 40 en VIIRS 375 en los cuatro puntos que valen, y las 14 de 40 de VIIRS 750 en V1 20 % quedaron SIN SUSTRATO, BLOQUEA o EMPATE). El «PIERDE 75 a 100 %» no es que la calibracion vea algo: es que apagar a ciegas a K le quita seis alertas por cada negativo limpio. Lo que la auditoria S160 temia (V1a-01: P2 aprueba un placebo que apaga el 1 %) solo puede ocurrir en un regimen donde mas de la mitad de lo que el brazo publica bajo 1 MW son negativos limpios, y K no es ese regimen (la linea base post #535 publica en negativos limpios 2,5 a 3,7 % de las pasadas de VIIRS 375, A104/A113 del CLAUDE.md del proyecto; lo que aqui se mide es la fraccion entre las publicaciones, 9 a 20 %). El criterio «GANA en 0 de 20 en los puntos que valen» es por eso un cero que no podia ser otra cosa: SIN DATO sobre la pregunta, no CUMPLE.
- COMO SE VE EN EL DASHBOARD: invisible (control del evaluador).
- COMO REPRODUCIRLO: `python experiments/_s159/instrumentos/verificador_d42/vuelta2/v10_placebo_curva.py` (lee los 8 JSONL; nada del A/B).
- CONFIANZA: CONFIRMADO (aritmetica sobre los JSONL; la composicion es la que esos archivos declaran).
- GRAVEDAD: 3 (no toca ninguna regla sellada; tuerce la lectura del control: la curva no prueba que la calibracion rechace un placebo, prueba que con K un placebo asi siempre pierde).

### V42-11
- TITULO: La suite de 2.417 y probar volvieron a correr en paralelo con el corredor de mutaciones (no con el arbol quieto en el sentido de A112)
- ARCHIVO:LINEA: `calib_p2/status_antes_v42.txt:1` (14:55:21 UTC), `status_despues_v42.txt:1` (15:29:11 UTC): 33,8 min; `mutaciones_salida_v42.txt` suma 3.132 s (52,2 min), `probar_salida_v42.txt` `real 27m30s`, `suite_salida_v42.txt` `real 6m18s`.
- QUE PASA: lo mismo que V42-06: los sha de los siete archivos vigilados no cambiaron (parte de A112 que importa), pero la suite corrio mientras existian copias `experiments/_mut_*`. Mi suite sola (abajo) cierra la sospecha.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: sumar los `NNNs)` de `mutaciones_salida_v42.txt` y comparar con las dos marcas de hora.
- CONFIANZA: CONFIRMADO (aritmetica); consecuencia SOSPECHA baja, cerrada por `suite_rerun_v2.txt`.
- GRAVEDAD: 1.

## 5. Juicio sobre el placebo y propuesta (lo pide la tarea; no decido)

**¿Puede este placebo, por construccion, detectar lo que S160 temia?** No con K. P2 cuenta errores (ADENDA_GEMELO §5.2): apagar al azar es bueno para D solo si lo apagado es mayormente ruido. Con K, 86 % de lo apagado es señal (alertas bajo 1 MW), asi que el placebo esta condenado a PIERDE o BLOQUEA antes de correr; «GANA 0 de 20» sale igual con calibracion, sin calibracion o con un P2 que mirara una moneda. El control S160 (tolerancia 0, CUMPLE 16 de 30) fallaba por OTRA razon: el P2 viejo decidia con una sola pasada neta y sin piso; lo que hoy lo neutraliza es el SIN SUSTRATO de D-34 (vuelta 1, V42-01), y lo que le quita todo poder es la composicion de K. Un control que no puede fallar no es un control (A110).

**Placebos que si podrian fallar** (cualquiera se corre con `placebo_1pct.py` cambiando una linea; solo produccion o sinteticos):
1. **Apagar solo publicaciones en negativos limpios** (lo que propone la tarea): D = K menos p % de sus errores de ruido. P2 tiene que dar GANA y, si la calibracion funciona, GANA calibrado. Prueba que P2 ve una mejora real y no la tapa; no prueba el temor de S160 (ahi publicar menos NO es a ciegas, es quitar errores: es lo que P2 debe premiar). Sirve como control positivo de poder sobre produccion, que hoy falta.
2. **El complementario**: apagar solo alertas bajo 1 MW: P2 tiene que dar PIERDE calibrado en todas las semillas. Control de direccion.
3. **El que mide el temor de S160 tal cual** («premia publicar menos a ciegas»): el mismo apagado al azar, pero sobre un brazo base cuya composicion haga rentable el silencio ciego, o sea con mas de la mitad de negativos limpios entre sus publicaciones bajo 1 MW. Dos formas sin tocar el A/B: (a) un K sintetico «ruidoso»: tomar K de produccion y ENCENDER al azar publicaciones en negativos limpios hasta que sean la mayoria (usando `apagar` al reves: `pc.vrp_mw` de 0 a un valor sobre el umbral), y sobre ese brazo base correr el apagado al azar; si P2 calibrada da GANA en mas del 5 % de las semillas, P2 premia el silencio ciego en ese regimen, y la pregunta pasa a Nicolas: ¿es defecto o es lo que la regla debe hacer? (b) el placebo **simetrico**: apagar p % de las publicaciones de K y, en la misma semilla, encender p % de pasadas que K no publica (negativos limpios y alertas en la misma proporcion que las apagadas); bajo ese nulo el neto esperado es 0 y la fraccion de GANA calibrada mide directamente la tasa de falsos de P2 calibrada sobre datos reales, que es la pregunta que la adenda §5 responde hoy solo con sinteticos.
4. **Antes de correr cualquiera**, el diagnostico barato que evita 160 corridas del evaluador: contar en la tabla del nulo (t_K_D.json, que `placebo_1pct.py` ya produce) cuantas publicaciones de K son negativos limpios y cuantas alertas bajo 1 MW; si los negativos no pasan de la mitad, un apagado al azar no puede dar GANA y el placebo no vale la pena.

## 6. SEGUIMIENTOS (fuera de mi eje)

- S1. `resumir_placebo.py:42` declara «VALE» un punto cuando la calibracion corrio en mas de la mitad de las celdas, mezclando los dos sensores: en V1 20 % «vale» (50 de 80) aunque en VIIRS 750 corrio en 5 de 20. El criterio deberia ser por regla y sensor. Gravedad 1, CONFIRMADO leido.
- S2. En V1 20 %, 10 de las 64 apagadas por semilla caen en dias excluidos (`apagadas_en_dias_excluidos`): el p % pedido no es el p % efectivo en la tabla que decide; el script lo informa pero no lo corrige. Gravedad 0.

## 7. VERIFICADO LIMPIO

- La prueba de V42-02 corre `contar` (l. 218) y asserta `ver["P2|VIIRS375"] == "INDECIDIBLE"` (l. 221) y `global_ventana(_completar(ver), True)[0] == "INDECIDIBLE"` (l. 223), con guarda de poder en l. 220 (`resultado_sin_calibrar == "PIERDE" and calibrada is False`): el sintetico son 12 negativos limpios que D publica y K no, en 3 bloques `Lascar|2026-09-0N` (l. 193-209), o sea 12 errores solo de D, el caso en que la calibracion falla (3 bloques: 12,5 % por cola) y el sin calibrar es PIERDE. Vara: V42-02 de la vuelta 1. Comprobado ademas corriendo mi m07 contra estas pruebas (v11).
- La prueba de V42-04 (l. 180-190) reemplaza `calibrar_p2` por una llamada con `n_rep=20, semilla=7` y exige `(20, 7)` en el detalle: fija que los valores vienen de lo que la funcion uso y no de la llamada ni de las constantes. Roja contra b57ecfe62 por asercion (`(1000, 161) == (20, 7)`).
- `_calibracion_forzada` (l. 87) devuelve ahora la tupla de 5 (`N_SORTEOS, SEMILLA_CALIB`), coherente con la nueva firma; las 5 pruebas parametrizadas del tope siguen midiendo el borde.
- Rojo contra 5f986a209: 26 de 39 por asercion, 0 otra excepcion, 0 errores (`v16`, XML `tests="39" failures="26" errors="0"` reproducido); las dos pruebas nuevas estan entre las 26.
- Los dos caminos que no calibran dejan `n_sorteos` y `semilla_calibracion` en None (l. 505 inicializa; l. 507-516 no los tocan) y `imprimir` los imprime con `%s` (l. 1044), asi que no revienta con None: lo ejercita probar (casos con P2 SIN SUSTRATO) y las pruebas de punta a punta.
- Las mutaciones nuevas del corredor son m07 tal cual (misma edicion que la mia, `mutar_calib_p2.py:111-112`) y n04 (vuelve a las constantes, l. 113-115).

## 8. SIN DATO

- Tasa de falsos de P2 calibrada sobre datos REALES de P2: ningun placebo corrido hasta hoy la mide (V42-10); el simetrico de §5.3 b la mediria.

## 9. FUERA DE ALCANCE

- V42-03 (lectura de §2.5): sigue en manos de Nicolas; el diff no lo toca y el repo sigue fijando la lectura L2.
- V42-05 y V42-06 de la vuelta 1: cerrados alli.

## 10. Resultados de los trabajos en segundo plano

- `v11_mutaciones_propias_v2_salida.txt` (m07, m12, m04 contra las pruebas de hoy): TERMINADO. Control sin mutar 55 pruebas, 0 fallas; **m07 ATRAPADA** por asercion, por `test_contar_publica_el_veredicto_calibrado_y_no_el_sin_calibrar` y solo por ella (1 asercion, 0 otra excepcion, 0 errores); m04 (control positivo) atrapada por 3 pruebas, incluida la nueva; m12 sigue NO ATRAPADA (mutante equivalente, como en la vuelta 1).
- `mutaciones_rerun_v42.txt` (corredor del implementador, `--solo m07,n04`, con su control de 75): TERMINADO. Control 75 pruebas, 0 fallas, 0 errores; m07 ATRAPADA (1 asercion, `test_contar_publica_el_veredicto_calibrado_y_no_el_sin_calibrar`) y n04 ATRAPADA (1 asercion, `test_el_detalle_dice_los_sorteos_y_la_semilla_que_la_calibracion_uso`); 0 copias `_mut_*` al terminar. Las 28 restantes no se re-corrieron en esta vuelta (se re-corrieron enteras en la vuelta 1 sobre b57ecfe62, y el diff 981cceda7..452956cf8 no toca las lineas que vigilan, salvo la tupla de 5 de `calibrar_p2` que todas las pruebas ya consumen en verde en el control de 75).
- `probar_rerun_v2.txt`: TERMINADO, `RESUMEN: 31 de 31 casos OK`, 30 min 37 s (tmp dentro de esta carpeta, borrado despues).
- `suite_rerun_v2.txt`: TERMINADO. Suite corrida SOLA (0 directorios `_mut*`, `git status --short` solo con esta carpeta, despues de que terminaran el corredor y probar): **2417 passed, 29 skipped, 1 xfailed**, igual que `calib_p2/suite_salida_v42.txt`. Cierra la SOSPECHA de V42-11.
