# Prueba del control de vida de V375-B2 (2026-10-24)

`fabricar_b2.py` arma dos runs falsos de B2: las 20 pasadas del control (lote CTL) copian los resultados y las grillas
de S162 tal cual («vivo») o con M14 en 0 píxeles («muerto»), y 60 pasadas de la muestra copian una neg_resto real de
S162 del mismo volcán (las otras 1.140 quedan SIN DATO a propósito).

- Vivo (`evaluar_fabricado_vivo_salida.txt`): control 2.2b 20 de 20 iguales a S162, instrumento OK, y el veredicto de B
  sale NO DECIDE por la cobertura del lote que decide (1.140 de 1.200 SIN DATO), como debe.
- Muerto (`evaluar_fabricado_muerto_salida.txt`): control 2.2b 4 de 20 iguales (las 4 en 0), 0 con píxeles; INVALIDO POR
  INSTRUMENTO (control_vida y recálculo).

Uso: `python -I fabricar_b2.py vivo|muerto <carpeta> b2/objetivos_v375_b2.json objetivos_v375_bc.json` desde
`experiments/_s162_v375`, y después `evaluar.py ... --art-extra <carpeta> --deciden S162b --neg-pub-de S162`.
