# Adenda post hoc al pre-registro (escrita después de ver la serie T, antes de correr la variante)

**Qué se vio.** El parche de Chillán de la serie T es el exceso de M13 y M15 sobre el fondo que el .m interpola, en las
45 celdas del halo quitado. Sólo 11 de esas 45 celdas tienen exceso positivo de M13; las otras 34 son negativas, porque
la cumbre de Chillán es más fría que el fondo interpolado desde los bordes del halo (suma positiva de M13 1,22, negativa
-0,36 W m-2 sr-1 um-1; mínimo de M15 -0,40; `diag_parche_salida.txt`). Al escalar el parche por 10 también se escala ese
déficit frío: quedan celdas con M13 de cero o menos (de 2 a 21 por escena) y BT15 de hasta 143 K. Eso no es física: es
el déficit topográfico de otro volcán multiplicado por diez. En la escala 3 pasa en una escena (Tupungatito
2026-08-21, 3 celdas). Por eso los resultados de la escala 10 de la serie T, tal como se pre-registró, son un artefacto
del método y no se usan para concluir; se reportan igual.

**Variante T+ (post hoc, declarada).** El trasplante lleva sólo la parte caliente: max(exceso, 0) en M13 y en M15 por
separado, a escala 1, 3, 10 y 30. Escalar sólo el exceso positivo es multiplicar el área caliente a la misma
temperatura; el déficit frío de Chillán no viaja. Todo lo demás (puntos, barrido, criterio de alerta, criterio de
relevancia de la §7 del pre-registro, brazo T-sin) es igual. La escala 30 se agrega para ver la tendencia hacia un evento
de cientos de MW; con 30 veces el exceso máximo de M13 (0,73) la BT M13 de la celda más caliente queda bajo el techo de
634 K. Se marca como post hoc en el informe.
