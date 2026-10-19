# S156: vigilancia de la sombra de K y el caso de Puyehue-Cordón Caulle del 2026-10-10

Arreglo 4 de `docs/AUDIT_S155.md` §5 (V1-04): el paso 9 de `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md` existía
y no tenía código. Ahora lo implementa `scripts/vigilancia_sombra.py`, que corre a diario por
`.github/workflows/vigilancia-sombra.yml` al terminar `experimental-diario`.

## El caso

La primera corrida (`sombra_latest_2026-10-19.json`, versión sin la lectura decidida) dio REVERSION_CANDIDATA:
Puyehue-Cordón Caulle, VIIRS 750 (NOAA-21), 2026-10-10 05:54 UTC. MIROVA publica en su tabla una alerta de 1,19 MW;
la sombra (C0) la publica con un cúmulo de 1,886 MW (Test 1 integrado disparado, 4,8 K, 26 píxeles); producción (K)
no tiene ningún píxel. Señal débil: NTI máximo −0,906, BT máxima 277,7 contra 271,85 K de fondo.

- Cabecera de MIROVA confirmada: `20261010_083116_VIIRS750_Latest10NTI.png` y `20261010_083105_VIIRS750_VRP.png`
  (mirova-tif-archive): «Last Update 10-Oct-2026 05:54:02», «Thermal anomaly: LOW», «VRP = 1 MW», cenit 23°.
- Auditoría espacial A61 (`a61/INFORME.md`, scripts en `a61/scripts/`): MISMO OBJETO, firmeza alta. Ancla y centro de
  la grilla de MIROVA a 7,56 km; el píxel más energético de la sombra a 0,17 km de la celda que MIROVA marca cada vez
  que reporta 7,83 km en VIIRS 750; control sobre 216 pasadas de PCC.
- Verificador limpio (`verificador/INFORME.md`): candidata reproducida con instrumento propio; ninguna otra protegida
  en que la sombra publique y K calle; la misma pasada la publica K en VIIRS 375 y esa noche PCC se publicó 5 veces.
- Fuera de las ventanas del A/B (V1 2026-08-29 a 10-08; V2 03-01 a 06-12) y anterior a la adopción (2026-10-18 09:57).

## La decisión

Nicolás eligió la recomendación B («lo que recomiendes»): no revertir; la unidad es la pasada; la vigilancia cuenta
desde la adopción y lo anterior se informa como retrospectivo, sin disparar. Escrito al inicio del paso 9 de la regla,
diciendo que se decidió viendo este caso. Con esa lectura, `sombra_latest_2026-10-19_lectura_decidida.json` da VERDE y
el caso queda en el bloque `retrospectivo`, con su issue de investigación.

## Lo que cambió después de cada verificador

Verificador 1 (`verificador/INFORME.md`): separación prospectivo y retrospectivo; la cota de Muy Bajo sólo en VIIRS
375 (en MODIS y VIIRS 750 el A/B no guardó la pérdida diferencial); marca A119 de Suomi NPP; aviso si la «sombra»
trae records de producción; prueba de `evaluar()` y `main()`.

Verificador 2 (`verificador2/INFORME.md`): frescura de la
sombra POR VOLCÁN (si muere en uno solo, sumar los once la dejaba verde); el issue se abre aunque falle el push
(`if: always()`); deduplicación por prefijo exacto del título y comentario en el issue abierto (la búsqueda de GitHub
es por bolsa de palabras); cron de respaldo y runner fijo en 24.04; (i) y (iii) con la etiqueta ORIGINAL, como las
cotas del A/B, y reversión y persistencia con D-9 SN; corte de la adopción al segundo; prueba del cableado de
`cargar_insumos` sin node. `mutar_vigilancia.py`: 37 mutaciones (las del autor y las 13 del verificador 2), las 37 caen
por fallo de prueba (`mutar_vigilancia_salida.txt`).

Verificador 3 (`verificador3/INFORME.md`): confirmó los arreglos del 2 y la corrida de hoy campo por campo. Arreglado:
tres maneras de quedar ciega que daban VERDE (referencia de MIROVA vacía o detenida, producción sin records de K,
sombra sin un sensor): la frescura pasa a ser por volcán Y sensor en la sombra y en producción, y la referencia se mide
como en el auto-audit (`MAX_GT_STALE_DAYS`). Un aviso nunca tapa una reversión. 12 mutaciones suyas sobrevivían; hoy
`mutar_vigilancia.py` corre 56 y las 56 caen por fallo de prueba. `huecos_por_volcan_sensor.py`: desde el 2026-08-01
ningún volcán y sensor pasó más de 2 días sin records, ni en producción ni en la sombra, así que el umbral de 3 días
no habría dado ninguna falsa «vigilancia ciega».

Queda para decidir (no se tocó, es la letra de la regla): con evaluación diaria, la primera Muy Bajo de VIIRS 375 que
la sombra publica y K calla en un volcán ya dispara INVESTIGAR (Wilson inferior de 1 de 1 = 0,2065 sobre la cota
0,1298); el verificador 2 estimó 57 % de probabilidad de al menos una falsa alarma en 120 días si K pierde igual que en
el A/B.
