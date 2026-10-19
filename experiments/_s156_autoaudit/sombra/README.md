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

## Lo que cambió en el script después del verificador

Separación prospectivo y retrospectivo; la cota de Muy Bajo sólo en VIIRS 375 (en MODIS y VIIRS 750 el A/B no guardó
la pérdida diferencial); marca A119 de Suomi NPP; aviso si la «sombra» trae records de producción; prueba de
`evaluar()` y `main()` de punta a punta. `mutar_vigilancia.py`: 21 mutaciones, las 21 caen por fallo de prueba.
