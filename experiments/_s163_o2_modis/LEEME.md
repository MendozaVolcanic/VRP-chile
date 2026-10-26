# O2 MODIS: el fondo del VRP de MIROVA en MATLAB, sobre escenas MODIS de 1 a 4 píxeles

Pedido de la coordinadora S163 (2026-10-26), después del O2 de VIIRS 750 (`experiments/_s163_o2/RESULTADO_O2.md`, rama
`s163-o2-paquete`): en alertas de un píxel ningún modelo de `fillmissing2` de nuestros ports es el de MATLAB. El port
MODIS usa el mismo fondo, así que su VRP de 1 a 4 píxeles hereda esa ambigüedad. Este paquete le pide a MATLAB el fondo
de cada escena con la máscara de alertas que ya decidió nuestro port.

## Qué contiene

| archivo | qué es | md5 |
|---|---|---|
| `entradas_o2_modis.mat` | `M13` (51 × 51 × 404, radiancia MIR de la grilla UTM que usó el port) y `ALERTAS` (celda de 404, índices lineales de MATLAB, columna primero, base 1) | ver `MD5.txt` |
| `MIROVA_VIIRS750_VRP.m` | copia sin cambios del OSF (licencia MIT en `LICENSE.txt`), igual a la de `s163-o2-paquete` | b0ceebb2b7864cd27c145dc8d41968cc |
| `correr_o2_modis.m` | el script a ejecutar: guarda VRP, NPIX, DL, LHOT, LBK y BK por escena | ver `MD5.txt` |
| `entradas_o2_modis_etiquetas.json` | qué es cada escena (no hace falta subirlo) | ver `MD5.txt` |
| `armar_paquete_o2_modis.py` | cómo se armó, con su control de identidad | |
| `leer_o2_modis.py` | lector del resultado | |

Escenas: 404 de 116 pasadas MODIS nocturnas (350 del lote S159, run 39712862945; 54 del lote de MOD-C, run
40120713181), por número de píxeles 168 / 132 / 77 / 27 (1 a 4), en las cinco variantes del port (`fisica` 96, `sensible`
102, `pixel` 96, `fisica_geo5km` 86, `fisica_b21` 24). Las variantes `sensible` y `pixel` comparten grilla con `fisica`
y a veces también la máscara: son escenas repetidas a propósito (cada una tiene su etiqueta).

Control de identidad del armado (`armar_paquete_o2_modis_salida.txt`): el VRP del port recalculado sobre la grilla y la
máscara empaquetadas da el del lote en 404 de 404 escenas (diferencia relativa máxima 7e-7: las grillas se guardaron en
float32 y el port calculó en float64). Para comparar con MATLAB se usa `vrp_port_recalculado_mw`, el del port sobre la
MISMA grilla float32 que recibe MATLAB. Control negativo: con la máscara corrida una columna, 404 de 404 se alejan más
de 1e-3.

## Pasos (MATLAB Online, igual que el O2 de VIIRS 750)

1. En MATLAB Drive, una carpeta `o2_modis` con `MIROVA_VIIRS750_VRP.m`, `entradas_o2_modis.mat` y `correr_o2_modis.m`
   (se pueden bajar con `websave` desde esta rama, como en S163). Comprobar los md5 dentro de MATLAB contra `MD5.txt`.
2. Con esa carpeta como carpeta actual: `correr_o2_modis`. Imprime la versión y la ruta de `fillmissing2` (tiene que
   ser una carpeta de MATLAB, no `o2_modis`).
3. Bajar `resultado_o2_modis.mat` a esta carpeta y leer:

   ```
   PYTHONIOENCODING=utf-8 python -I leer_o2_modis.py
   ```

   El lector exige que NPIX de MATLAB sea el de cada máscara y compara el delta L de MATLAB, reescalado a MODIS
   (× 1,89e7 × 1,0), con el del port, por número de píxeles.

## Qué no hacer

No poner en la ruta de MATLAB ningún `fillmissing2.m` propio (el del shim de Octave invalida el resultado).
