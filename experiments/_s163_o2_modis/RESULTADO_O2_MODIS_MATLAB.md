# O2 MODIS en MATLAB: la regla de `fillmissing2` es la de MATLAB también en MODIS (2026-10-26)

> ⚠️ **Verificado con contexto limpio el 2026-10-26 (Sonnet, `verificador_matlab/INFORME.md`).** La afirmación central
> **se sostiene**: la regla coincide con el fondo de MATLAB en 404 de 404 filas y 191 de 191 escenas distintas, con
> diferencia máxima 5,55e-17 en todas las celdas finitas del hueco, y la alternativa más cercana (el port o el marco
> cambiado) está a 1,06e-4: la tolerancia separa por 12 órdenes de magnitud. El resultado es de este paquete (md5,
> LHOT y DL recalculados, cabecera GLNXA64). Lo que **corrige o acota** del texto de abajo, que se conserva:
> - **Alcance (VM-01, VM-05)**: los bloques 2 × 2 son sólo 6 escenas distintas, todas de Láscar y centradas; de las 191
>   escenas, 161 son de Láscar; todas tienen hueco de 3 × 3 (4 píxeles o menos) y ninguna alerta cerca del borde. Es una
>   equivalencia medida en una versión de MATLAB (R2026b), no un mecanismo probado; y el `.m` es el de VIIRS 750 sobre
>   grillas MODIS remuestreadas y alertas decididas por nuestro port.
> - **«La matriz de fondo completa dentro del hueco»** vale para las celdas finitas: MATLAB deja sin rellenar 159 celdas
>   del hueco en 10 escenas (no extrapola fuera de la envolvente) y la regla las rellena con el vecino más cercano;
>   ninguna es celda de alerta, así que el VRP no cambia (VM-02). SOSPECHA: con una alerta fuera de la envolvente MATLAB
>   y la regla sí discreparían.
> - **«Con 2 y 3 píxeles casi siempre da lo mismo»** omite que el port también falla en pares diagonales (3 de 3), un
>   trío 8-conexo y 4 píxeles dispersos (VM-04). **«Sin sesgo»** vale en mediana y en conteo (67 sobre, 72 bajo), no en
>   media (1,072; VM-07).
> - Lo que **no** es medición sino decisión: que la columna de M con la regla «deje de ser preliminar» en MOD-D y que una
>   vía «código MIROVA» en `pipeline/` tenga que usar esta regla (VM-05). La corrida en MATLAB Online y la comprobación de
>   los md5 dentro de MATLAB las informa la coordinadora (no están en el material; VM-06).

**Verificado (ver la marca de arriba).**

## Qué se corrió

La coordinadora S163 corrió `correr_o2_modis.m` en MATLAB Online (R2026b, `fillmissing2` de la carpeta de MATLAB) sobre
el paquete de esta carpeta (entradas comprobadas por md5 dentro de MATLAB). Resultado: `resultado_o2_modis.mat` (md5
d20cf7ddd3b6ba015c7b474afe627085) y `salida_matlab_modis.txt` (da9e409f9958c4e4e40fda7142e27ec9). 404 escenas en 2,0 s.

## Qué dice

`regla_contra_matlab_modis.py` → `regla_contra_matlab_modis_salida.txt` y `.json`. NPIX de MATLAB igual a la máscara en
404 de 404.

| forma | escenas distintas | regla = MATLAB (VRP a 1e-9 y fondo en el hueco a 1e-9) | port = MATLAB | port difiere más de 1 % |
|---|---|---|---|---|
| 1 píxel | 87 | 87 | 24 | 59 |
| 2 píxeles | 57 | 57 | 54 | 2 |
| 3 píxeles | 37 | 37 | 36 | 1 |
| 4 píxeles en otra forma | 4 | 4 | 3 | 1 |
| 4 píxeles en bloque 2 × 2 | 6 | 6 | 0 | 4 |

(Sobre las 404 filas, que repiten escenas entre variantes, los números son proporcionales: regla = MATLAB en 404 de 404.)

1. **La regla de `fillmissing2` que identificó la rama `s163-o2-alternativa` es la de MATLAB también en MODIS**, en la
   grilla de 51 × 51, en las 191 escenas distintas, incluidos los **bloques 2 × 2** que la vara preliminar dejó como
   SOSPECHA (VV-03 del verificador de la vara): coinciden el VRP y la matriz de fondo completa dentro del hueco. La
   diferencia máxima en el VRP es 1,6e-15 (redondeo).
2. **Nuestro port no es MATLAB en las alertas de 1 píxel y de bloque 2 × 2**: en 1 píxel coincide en 24 de 87 escenas y
   difiere más de 1 % en 59; en los bloques 2 × 2 no coincide en ninguna (difiere más de 1 % en 4 de 6). Con 2 y 3
   píxeles casi siempre da lo mismo. Las cifras de la vara preliminar (ruido de 9 % típico en 1 píxel, sin sesgo; casos
   como Llaima 2026-07-24 01:05, 0,43 MW con el port contra 0,11 MW con MATLAB) quedan ahora medidas contra MATLAB.

## Lo que sigue sin dato

- Que MIROVA, para MODIS, use el mismo `.m` de fondo que publica para VIIRS 750 (el código MODIS no está publicado).
  Lo que esto prueba es que, SI usa ese `.m`, su fondo es el de la regla y no el de nuestro port.

## Consecuencia (para decidir, no decidido)

Para la magnitud de alertas de 1 píxel y de bloques 2 × 2, la vara es MATLAB (o la regla, que lo reproduce), no nuestro
port. La adenda 4 de MOD-D ya informa M también con la regla, fuera de línea; con este resultado esa columna deja de
ser preliminar. Cualquier vía «código MIROVA» en `pipeline/` (fase 3) tendría que rellenar el fondo con esta regla y no
con la de scipy.
