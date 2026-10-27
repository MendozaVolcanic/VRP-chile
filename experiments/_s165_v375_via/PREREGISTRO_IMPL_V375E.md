# Pre-registro de implementación V375-E (PD3): la vía «código MIROVA» en VIIRS 375, APAGADA

Escrito el 2026-10-27 (sesión hija de la coordinadora S165), antes de tocar `pipeline/` y antes de correr la vía sobre
ninguna grilla. Base: `experiments/_s162_v375/PREREGISTRO_E.md` con su adenda 1 (§7), el traspaso de la sesión VIIRS 375
(carpeta compartida de S162, `VIIRS375_via_375_traspaso.md`) y los PR que sirven de modelo: #907 (VIIRS 750, merge
`cff07d173`) y #919 (MODIS, merge `d94f25191`). Tag defensivo: `pre-s165-via-375` sobre `d94f25191`. Nada de esto
enciende la vía: el flag entra apagado y encenderlo es otra decisión de Nicolás (A45).

## 1. Qué se implementa

1. **`pipeline/mirova_v750_codigo.py`**: una familia `FAMILIAS["VIIRS375"]` con sólo lo que cambia respecto del `.m` de
   750 (tabla del traspaso): λ MIR 3,74 µm (I4), λ TIR 11,45 µm (I5), coeficiente 1,80e7 x 0,140625 km² / 1e6, grilla de
   134 x 134 celdas de 375 m (la misma regla GEO), bandas `I04`/`I05` leídas en radiancia con las banderas DN ≥ 65528 en
   NaN, y el corte de 5 km al centro de la grilla del probe de 375 (`probe_v375.py`, igual que MODIS). Los umbrales del
   `.m` no cambian. La caja es la de PD1: **C13**, 13 x 13 celdas centradas en la celda más cercana al cráter de
   `volcanoes.yaml`, dentro de la ROI1 física de S159 (±7.875 m alrededor de X0, Y0, 42 x 42 celdas), igual que
   `brazos.caja(..., "C13", ...)`. La ROI1 no cambia la detección (BOX 0 y 1 tienen los mismos umbrales), pero se
   conserva igual al port para que la comparación sea limpia. El lector `leer_radiancia_l1b` acepta las bandas como
   argumento con el default de hoy (M13, M15), así VIIRS 750 no cambia.
2. **`pipeline/profile.py`**: `ENABLE_V375_CODIGO_MIROVA`, leído de `thresholds:` (`enable_v375_codigo_mirova`, default
   False). No se escribe en ningún perfil.
3. **`pipeline/process_viirs.py`**: el mismo bloque que #919 puso en MODIS, al inicio de `calculate_vrp` y sólo si el
   flag está encendido. Si la vía no puede correr (volcán sin grilla de MIROVA), sigue K y el record lleva
   `via_codigo_mirova: "sin_grilla"` (A118). Cada record de la vía lleva `via_codigo_mirova: True`.
4. **Dos cableados que el traspaso no nombra, hallados al leer el camino del record** (SOSPECHA hasta que la prueba roja
   lo muestre):
   - `store.py:609` calcula `f5_core_vrp_mw` para todo record I-band. Los píxeles de la vía no traen `vrp_mw` por píxel,
     así que el núcleo sumaría 0 y el tablero, que prefiere `f5_core_vrp_mw` (`frontend/index.html:1255`), publicaría
     0 MW donde la vía midió la suma de MIROVA. El núcleo F5 es un recorte de K; MIROVA suma todos los alertados (D32).
     Arreglo: no calcular el núcleo para records con `via_codigo_mirova is True`, igual que las otras tres compuertas de
     la era K que `store.py` ya les salta. Con el flag apagado ningún record trae esa marca: el almacén queda igual
     (se repite `experiments/_s162_v750a/bitabit_store.py`).
   - `scripts/run_pipeline.py:318-323` imprime `result['vrp_mir_mw']`, `['vrp_tir_mw']`, `['t_max_i04_k']` y
     `['n_vent_pixels']` después de guardar el record. Un record de la vía no los trae: el `KeyError` saldría como
     «ERROR processing» en el log de un record que sí se guardó. Arreglo: leerlos con `.get`. No cambia nada con el
     flag apagado.

## 2. Pruebas, escritas antes del código (TDD)

En `tests/test_mirova_v375_codigo_s165.py`, con el patrón de `tests/test_mirova_modis_codigo_s164.py`:

1. El flag existe, se lee de `pipeline.profile` bajo `thresholds:` y está apagado en `mirova_equivalent`,
   `experimental` y `experimental_ndc_focus`.
2. Las constantes de la familia son las del port (`mirova_port.SENSORES["VIIRS375"]`) y la grilla de cada volcán es la
   que guardó el lote de B y C (`objetivos_v375_bc.json`, campo `grilla`).
3. La caja de la vía es, celda por celda, la de `brazos.caja(..., "C13", ...)` en los 11 volcanes con grilla.
4. Sobre grillas guardadas del lote, la vía da la misma máscara índice por índice que `brazos.correr_box` con C13 y el
   mismo VRP con el fondo de MATLAB (fixtures pequeñas en `tests/datos_s165_v375/`).
5. Con el flag apagado: el procesador de 375 no toca la vía, y las escenas de 375 del arnés S142 dan bit a bit el texto
   congelado con el código del tag (`tests/datos_s165_v375/v375_k_antes.json`, mismo redondeo que el golden de S142).
   Además, fuera de pytest, un golden **crudo** (cada float por `repr`, sin redondeo) de los tres perfiles, tag contra
   HEAD, como el A1 del verificador de #919.
6. Control de que el bit a bit puede fallar (A116): con el flag encendido el record de 375 del arnés cambia (lleva la
   marca `sin_grilla`), y con la vía forzada devuelve el record de la vía.
7. El almacén no calcula el núcleo F5 para un record de la vía y sí para uno de K.

## 3. Equivalencia con el port (paso 1 de E, adenda §7.3)

Script `experiments/_s165_v375_via/equivalencia_v375e.py`, sobre las grillas guardadas de los lotes S162
(`run_40116289866`) y S162b (`run_40131572769`), y del de S159 si está en disco. Por pasada, la vía
(`procesar_grilla` con la caja del punto 1) contra `brazos.py` brazo C13:

- **Máscara de alertados idéntica índice por índice** (más fuerte que «misma cantidad»).
- **VRP a 1e-3 MW en el 99 % o más**; en las escenas de 1 a 4 píxeles la vara es el fondo de MATLAB
  (`o2_375/matlab_v375.json`), sobre 4 píxeles `brazos.py` tal cual. Si sobre 4 no calza, se mira primero el relleno.
- **Publicación idéntica en el 100 %** y las protegidas idénticas, con el predicado del tablero ejecutado con node
  (`B.correr_node`, el mismo que usa `evaluar.py`).

**Riesgo declarado antes de medir.** La vía mide la distancia del cúmulo 8-conexo de la alertada más radiante al
**cráter** (corrección C-4 del censo, compartida con 750 y MODIS), y `evaluar.py` decide la publicación con la regla
`cercano`: el alertado más cercano a **X0, Y0**, el punto de referencia de la grilla. Son definiciones distintas. Se
informan las dos comparaciones (vía contra `cercano` y vía contra `centroide`) y no se cambia la regla de la vía para
que calce: si la publicación difiere sólo por la regla de distancia, el resultado es **NO EQUIVALENTE POR LA REGLA DE
DISTANCIA**, con las pasadas listadas, y la decisión de qué regla es la de MIROVA vuelve a la coordinadora y a Nicolás.
Una diferencia de máscara o de VRP fuera de tolerancia es **NO EQUIVALENTE** sin más.

## 4. Mutaciones y verificador

Batería de mutaciones sobre la parte nueva (constantes de 375, caja C13, ROI1 física, bandas, flag, marca, núcleo F5 en
el almacén) con control de caída: cuenta como atrapada sólo la que falla por aserción (S156). Verificador con contexto
limpio, de otro modelo, sobre el diff y estos criterios, antes de declarar el PR listo.

## 5. Lo que este PR no hace

No enciende el flag, no crea el perfil de la sombra, no despacha GitHub Actions (el bit a bit de un día de NRT en el
mismo runner lo despacha la coordinadora con `probe-s162-bitabit-nrt.yml`; aquí se deja `comparar_bitabit_nrt.py`
adaptado a 375), no sella `PREREGISTRO_E.md` y no conecta el evaluador común.
