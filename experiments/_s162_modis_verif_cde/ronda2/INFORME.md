# Verificador con contexto limpio, S162 MODIS, ronda 2: los arreglos de MOD-C, MOD-E y MOD-D v2

## 1. Encabezado

- **Hora del servidor** (GitHub, header `Date`): `Sat, 24 Oct 2026 16:46:37 GMT` al empezar la ronda.
- **Commits medidos**: `5f40f604d` y `ce71a4ab1` de `claude/s162-modis-774bb0` (HEAD del worktree al medir `9c20c5ae6`,
  que sólo agrega `tasks/LOOP_MODIS.md`); población de MOD-D en `origin/s162-mxd03-codigo` = `34f8ca391`;
  `origin/s159-evaluador-d25` = `ded217af4`.
- **Modelo y esfuerzo**: Claude Fable 5.1, esfuerzo medio, autónomo.
- **CARPETA**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-modis-774bb0\experiments\_s162_modis_verif_cde\ronda2\`
  (`salidas\` con cada corrida; los instrumentos son los de la ronda 1, en la carpeta madre, re-corridos sobre el código nuevo).
- **Qué NO miré**: no leí `tasks/LOOP_MODIS.md`; no corrí red ni HDF; no revisé el arnés ni el evaluador de MOD-B
  (`evaluar_mxd03.py` y compañía) salvo `poblacion.json`, `MANIFIESTO.json` y `chillan_k_mirova.py`; no verifiqué el
  predicado del tablero (vara); no despaché nada.

## 2. En una pantalla

1. **MOD-C se puede despachar tal como está.** Los tres arreglos hacen lo que dicen: la prueba del envoltorio atrapa 8 de 8
   y mis dos mutaciones de ángulos (que en la ronda 1 pasaban) ahora caen por aserción; los 13 controles incluyen las 3
   protegidas de Chillán sobre 50° y el sorteo principal (400 `neg_resto`) es idéntico al de la ronda 1; el blob `2d57443d`
   está en el JSON y en el workflow; el lector trata `sunglint` como no evaluable y el ensayo en seco no cambia. Queda
   texto desactualizado dentro del pre-registro y del yml (VCD-15: «10 pasadas de control», «6 de 6», nombre del paso),
   que no cambia comportamiento.
2. **MOD-E**: la marca al inicio retira la lectura de E-3, cita bien los números y saca PM-sin_dup de los brazos. ARREGLADO.
3. **MOD-D v2 está lista para el sello de reglas, con dos precisiones chicas antes de sellar** (VCD-16): decir que con menos
   de 5 pares la salida «RESUELTO POR EL PAQUETE» es inalcanzable por aritmética (p mínimo 1/16) y qué hace la regla 4 si
   un grupo de cenit queda vacío; y definir el empate exacto en la prueba de signos. Todo lo demás cierra: §6 es exhaustiva y
   con precedencia, cubre las cinco salidas de `regla_signos_p2`; P1b tiene una sola regla; M decide sólo EMPEORA; el
   placebo informa; la población está en `origin` con su manifiesto y reproduce 0,635 (n 7) para Chillán; el costo ya no
   doble-cuenta la descarga. El candado falta y lo dice.

## 3. Veredicto por hallazgo de la ronda 1

| id | veredicto | evidencia de esta ronda |
|---|---|---|
| VCD-01 BLOQUEA sin fila | **ARREGLADO** | `PREREGISTRO.md` (MOD-D v2) §6: seis filas en orden, «primera fila que se cumpla»; cubre GANA, PIERDE, BLOQUEA, EMPATE y SIN SUSTRATO, las cinco salidas de `regla_signos_p2` (`ded217af4` l. 552). Controles rojos antes que P1, P1 antes que P2. |
| VCD-02 Chillán con d′ de dos volcanes | **ARREGLADO** (con la precisión VCD-16) | §5: prueba propia, signos exacta de una cola sobre los pares. Aritmética comprobada (`salidas/`, transcripción): 7 de 7 p = 1/128 = 0,0078; 6 de 7 p = 8/128 = 0,0625; 5 de 5 p = 0,031; 4 de 4 p = 0,0625. Con los 7 pares de hoy es alcanzable; con 4 o menos no. |
| VCD-03 / VCD-04 SIN_DUP (MOD-E) | **ARREGLADO** | Marca al inicio de `experiments/_s162_modis_bowtie/INFORME.md` (l. 9-24): lectura retirada, D28 SIN DATO, números citados coinciden con mi tabla (10,7 %, 19,7 %, 8,9 %, 0,754 n 7, 0 de 11, 0 de 8, 24 de 29). MOD-D v2 §3: PM-sin_dup fuera; costura informativa. Mi script copiado a la carpeta con el mismo blob (`1009410f`). |
| VCD-05 población en rama local | **ARREGLADO** | `origin/s162-mxd03-codigo` = `34f8ca391`; `poblacion.json`: checkout `80b819828`, ventana 2026-03-01 a 10-16, 1.232 gránulos, 5.465 records, labs protegida 50 / bajo1 42 / neg_limpio 5.110 / sin_info 253 / far_ref 10; `MANIFIESTO.json` con sha256 de los dos CSV (`salidas/poblacion_mxd03_conteos.txt`). |
| VCD-06 placebo | **ARREGLADO** | §3 y §8.3: control de cableado, d′ = 0 por construcción, informa (D-28 §2.5); sólo un error de conexión lo pone en rojo y eso sí es un control que vale. |
| VCD-07 E-2 sin estratificar (MOD-E) | **ARREGLADO** | Marca l. 20-22: bajo 1 MW ρ 0,381 n 38, protegidas ρ 0,194 n 40, cenit con fecha ρ −0,515, y la lectura compatible. |
| VCD-08 prueba ciega a los ángulos | **ARREGLADO** | `05_prueba_envoltorio.py`: ángulos que varían con línea y frame (l. 109-114), comparación por píxel (l. 182-184), dos mutaciones nuevas; re-corrida: `PRUEBA OK … 8 de 8` (`salidas/05_prueba_envoltorio_rerun_r2.txt`, 74 s). Mi arnés de la ronda 1, sin cambios: `m7` y `m8` ahora **atrapadas por aserción** (antes NO ATRAPADA), control OK (`salidas/verif_c4_mutacion_extra_r2.txt`). |
| VCD-09 costo doble | **ARREGLADO** | MOD-D v2 §9: 5.465 × 10,8 s = 16,4 h más 0,7 h de arranque, sin sumar la descarga aparte; dice que los 9,1 s la incluyen. |
| VCD-10 controles sólo Láscar | **ARREGLADO** | `01_seleccion.py` l. 188-190; re-corrida: 413 objetivos, blob `2d57443de2f664d670033b84d03f7896155a3d7f` = JSON commiteado = `SHA_OBJETIVOS` del yml; 13 controles con 11 `pos_prot`, 3 de ellos Chillán a 50,5°, 57,6° y 58,2° (ids 141, 65, 147); los 400 `neg_resto` idénticos a la ronda 1 (`salidas/01_comparacion_sorteo.txt`: `sorteo identico: True`). Costo con 413: 1,28 h (`salidas/04_costo_413.txt`; el texto dice 1,27 «dentro del redondeo»). |
| VCD-11 0,485 de Chillán | **ARREGLADO** | `chillan_k_mirova.py` y su salida en la rama; reproducido sobre `poblacion.json`: K publica 7 de 10, razones 0,137 a 0,847, mediana 0,635; pares con cenit > 30°: 0,137, 0,205, 0,209; ≤ 30°: 0,635 a 0,847. El script no corre desde otra carpeta (busca `poblacion.json` al lado, por diseño). |
| VCD-12 `record_port` con corrección inexistente | **ARREGLADO** | §3: `record_port` sin cambios; distancia del alertado más cercano como función nueva e informativa. |
| VCD-13 alcances sin fijar | **ARREGLADO** | §4 P1b una regla (K ≥ 1 y brazo < 1 decide; la otra dirección lista); M sólo EMPEORA decide, en el agregado; §2 `sin_info` y `far_ref` fuera de las pruebas que deciden; §5 regla 4 con corte de 30° y banda; §6 precedencia. |
| VCD-14 `sunglint` evaluable | **ARREGLADO** | `07_leer_lote.py` l. 64-65; ensayo en seco idéntico al commiteado (`salidas/07_ensayo_rerun_r2.txt`). |

## 4. Hallazgos nuevos

### VCD-15. Texto del pre-registro de MOD-C y del yml que quedó con los números viejos
- **ARCHIVO:LÍNEA**: `experiments/_s162_modis_negativos/PREREGISTRO.md:132` («las 10 pasadas de control dan el mismo npix»,
  son 13), `:135` y `:165` («6 de 6 mutaciones», son 8 de 8), `:142` («1,27 h … 413 … lo mismo dentro del redondeo»; con
  413 el script da 1,28); `probe-s162-negmodis.yml:58` (nombre del paso «6 mutaciones»).
- **QUÉ PASA**: el comportamiento es el nuevo; el texto sellado describe el viejo en cuatro lugares. Quien lea el
  pre-registro después del lote va a contar 10 controles y 6 mutaciones y no va a encontrar ni lo uno ni lo otro.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `grep -n '6 de 6\|6 mutaciones\|las 10 pasadas' experiments/_s162_modis_negativos/PREREGISTRO.md experiments/_s162_modis_negativos/probe-s162-negmodis.yml`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1 (no bloquea el despacho; arreglar en la misma adenda).

### VCD-16. La prueba de Chillán (MOD-D v2 §5) deja dos casos sin decir, chicos pero decidibles ahora
- **ARCHIVO:LÍNEA**: `experiments/_s162_modis_paquete/PREREGISTRO.md:99-108`.
- **QUÉ PASA**: (a) la regla 3 dice que «el número exacto de pares lo fija el censo, la regla no cambia», pero con 4 pares
  o menos el p mínimo de la prueba de signos de una cola es 1/16 = 0,0625 y «RESUELTO POR EL PAQUETE» es inalcanzable por
  aritmética; hoy hay 7 pares porque K publica 7 de 10, y si PM deja de publicar 3 de esos, la salida está predeterminada
  sin que el texto lo diga (conviene escribir «con menos de 5 pares, SIN SUSTRATO para la regla 3»). (b) La regla 2 define
  «más cerca» con desigualdad estricta y no dice cómo cuenta un empate exacto en la prueba de signos (razonable: en contra
  de PM, pero hay que escribirlo). (c) La regla 4 compara dos medianas por grupo de cenit; si un grupo queda vacío (por
  ejemplo PM no publica ninguno de los 3 pares sobre 30°), «cualquier otro caso» la manda a SIN RESOLVER por omisión, no
  por regla.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python -c "for n in (4,5,6,7): print(n, 1/2**n, (1+n)/2**n)"` y leer las líneas citadas; los
  pares por grupo de cenit están en `salidas/poblacion_mxd03_conteos.txt`.
- **CONFIANZA**: CONFIRMADO (lectura y aritmética). **GRAVEDAD**: 2 (una salida puede quedar predeterminada sin estar escrito).

### VCD-17. El corte de 30° de cenit se eligió mirando los valores de K en los mismos 7 pares (nota, no defecto)
- **ARCHIVO:LÍNEA**: `experiments/_s162_modis_paquete/PREREGISTRO.md:21,39,104-105`.
- **QUÉ PASA**: el umbral separa el régimen de K (0,64 a 0,85 bajo 24°; 0,14 a 0,21 desde 35°) y se fijó viendo esos
  valores. Respecto de PM (lo que se prueba) es pre-registrado, y es robusto: cualquier corte entre 23,6° y 35,1° da la
  misma partición 4 + 3. Lo dejo escrito para que nadie lo lea como umbral físico.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `salidas/poblacion_mxd03_conteos.txt` (cenit de los 7 pares).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1.

## 5. VERIFICADO LIMPIO (ronda 2)

- `01_seleccion.py` nuevo reproduce el blob `2d57443d`; los 400 `neg_resto` son byte a byte los de la ronda 1; ids únicos
  (`salidas/01_comparacion_sorteo.txt`).
- `05_prueba_envoltorio.py` nuevo: 8 de 8 por aserción; mi arnés externo 4 de 4 extra atrapadas, control OK.
- `07_leer_lote.py` nuevo: ensayo en seco idéntico al commiteado.
- `probe-s162-negmodis.yml`: `SHA_OBJETIVOS` = blob del JSON commiteado; el resto del yml no cambió (diff de una línea).
- MOD-E: la marca cita mis números sin alterarlos y el script copiado tiene mi mismo blob.
- MOD-D v2: funciones importadas existen en `ded217af4` (`pesos_bloque` l. 198, `regla_m` l. 245, `prueba_signos_p2` l. 509,
  `regla_signos_p2` l. 552); `poblacion.json` y `MANIFIESTO.json` en `origin`; Chillán 0,635 reproducido; «43 de 44» y
  «0,485» ya no aparecen; sin guiones largos en los tres documentos.
- Nada escrito fuera de `experiments/_s162_modis_verif_cde/`; `git status` sólo muestra mis carpetas sin seguimiento.

## 6. SIN DATO

El costo del job `prueba` en el runner (sigue SIN DATO, declarado); si la prueba de signos de Chillán tendrá 7 pares (lo
fija el censo).
