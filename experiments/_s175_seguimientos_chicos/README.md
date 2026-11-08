# Seguimientos chicos de S175: re-mediciones que respaldan el PR

Los números salen de los `*_salida.txt` de esta carpeta, generados por el script del mismo nombre sobre `origin/main`
`cc32ab1fc` (2026-11-08). Nada de aquí corre en CI: necesitan el CSV del OSF o el archivo de TIF, que no están en git.

## 1. Descomposición de magnitud de S139 tras el reproceso con K (HALLAZGO, sin arreglar)

Qué pasó físicamente: S139 midió, pasada contra pasada con el OSF, que nuestra magnitud VIIRS 375 queda bajo la de MIROVA
sobre todo porque integramos menos píxeles, y que al contar los mismos píxeles la razón era casi 1. #883 reemplazó esos
records por los del detector K, así que el test que congela S139 ahora mide otro detector.

Instrumento: `comparar_magnitud_post_883.py`. Su control pasa: los records del padre de #883 dan exactamente lo que el
test congela, de modo que la causa es #883.

| VIIRS 375 | antes de #883 (S139) | hoy, con K |
|---|---|---|
| pares | 1.499 | 1.579 |
| R_gm | 0,659 | 0,693 |
| F_n (selección) | 0,553 | 0,535 |
| F_ex (exceso por píxel) | 1,192 | 1,294 |
| igual conteo: n | 342 | 358 |
| igual conteo: R | 0,995 | 1,052 |
| igual conteo: F_hot por F_bg | 1,140 por 0,873 | 1,133 por 0,929 |

No cambió sólo el denominador. En los 1.422 pares comunes R_gm pasa de 0,675 a 0,692, y sólo 333 tienen el mismo VRP y el
mismo conteo publicados. También pesa la composición: los 77 pares que salieron tenían R_gm 0,417.

Qué se sostiene y qué no:

- Se sostiene: el déficit sigue siendo de selección (F_n 0,535, en los pares comunes 0,545 a 0,536).
- No se reproduce: el 0,995 a igual conteo, ahora 1,052, fuera de la tolerancia de 0,01 del test. Por volcán va de 0,39 a
  1,59, con cambios grandes contra S139 (Isluga 0,943 a 0,614; Lastarria 0,841 a 1,332). A99 ya estaba rebajada por esta
  misma compensación entre volcanes; esta medición no la levanta.

Por eso `tests/test_descomponer_magnitud_s139.py` conserva sus números y sigue fallando donde está el OSF; sólo cambió su
docstring y su mensaje, que apuntan aquí. Pendiente de decisión: re-congelarlo con los números de K, o dejar S139 como
medición histórica y sacarlo de la suite.

## 2. Casos de `tests/test_r2_pixel_level.py` bajo K

Instrumento: `casos_r2_contra_tabla.py`. Villarrica y Llaima (VIIRS 375, 2026-05-09 06:36) e Isluga MODIS (2026-05-10
07:15) no tienen detección con K, y la tabla de MIROVA da 0,0 MW en esas pasadas: no son FN. Antes de #883 Villarrica y
Llaima tenían sólo 0,043 y 0,032 MW (fuente `test1_roi`, del Test 1 integrado que K retiró), e Isluga MODIS 5,0 MW con 61
píxeles y clase `far`. La
prueba ahora salta esos casos con motivo, y falla si MIROVA hubiera alertado.

Limitación que queda escrita en la prueba: el centroide ponderado del TIF cae a menos de 2,1 km del centro de la escena en
los 7 casos, porque el TIF es un campo continuo (D6). Los casos que pasan dicen poco sobre el píxel que alertó MIROVA.

## 3. Marcas de la vía MODIS (respuesta parcial a C-05)

`marcas_via_modis.py` cuenta los records MODIS con `via_codigo_mirova`. Ver la nota de C-05 en `docs/COLA_CAMPO.md`.
