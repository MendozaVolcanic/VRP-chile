# Cierre del plazo de la guardia K de MODIS (S198, 2026-11-24)

Informe para Nicolás que pide la §4.6 de `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md` y el punto 1
de «Lo que queda» de la §12.9 de `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md`. Cada número sale de
los archivos de esta carpeta, generados el 2026-11-24 a las 05:02 UTC sobre `origin/main` `9fa086822`, con la referencia
de Mirova-v1 bajada en ese momento (tabla consolidada y OCR, igual que `.github/workflows/vigilancia-guardia-modis.yml`).

## Qué se preguntaba

El 2026-11-02 MODIS pasó a detectar con el código de MIROVA (la vía). Como la vía mira los mismos píxeles con otras
reglas, el riesgo era que callara una anomalía térmica fuerte que el detector anterior (K) sí veía. Por eso K siguió
corriendo aparte, como guardia, y cada día una vigilancia compara las dos contra MIROVA. La pregunta de la guardia es
una sola: ¿hay alguna alerta de MIROVA de 1 MW o más (protegida) que K publica y la vía, con record, calla? El plazo
termina con 29 protegidas nocturnas que la guardia haya mirado, o a los 120 días (2027-03-02), lo que llegue primero.
Con 29, una pérdida de una de cada diez se habría visto con 95 % de probabilidad.

## Resultado

**Plazo cumplido y VERDE.** La vigilancia del workflow lo marcó a las 03:47 UTC; la repetición con la referencia fresca
de las 05:02 UTC da lo mismo (`salida_guardia_cierre.txt`):

| Indicador | Valor | Cota o lectura |
|---|---|---|
| Protegidas vistas por la guardia desde el encendido | 30 | objetivo 29 |
| Candidatas a reversión (K publica, la vía calla) | 0 | dispara con 1 |
| Calladas por un record K de producción | 0 | |
| Protegidas sin record de producción | 0 | |
| Muy bajo (0,05 a 1 MW, K publica y la vía calla) | 0 de 1 | cota 2 |
| Sobrepublicación (la vía publica un negativo limpio que K no) | 1 de 453 (Láscar 2026-11-08 08:00) | cota 3 |
| Nulo antes del encendido (K contra K) | 0 distintas de 167 pares | |
| Pasadas que la guardia registra y producción no (borde 171-01) | 13, ninguna protegida | informativo |

**Las 30 protegidas** (`fuente_y_magnitud.txt`, `protegidas_posteriores_encendido.csv`):

- 29 son de Nevados de Chillán y 1 de Chaitén. Las 30 están en la tabla consolidada de MIROVA (`latest.php`); ninguna
  depende sólo del OCR.
- **La vía publica 29 de 30.** La única que calla es Chaitén 2026-11-19 02:30 UTC (1,07 MW), que K tampoco publica:
  diagnosticada en #1107 (borde doble de la caja sensible y del ETI) y aceptada por Nicolás en #1109.
- **K publica 21 de 30.** Las 8 que K calla y la vía publica son todas de Chillán (entre ellas 2026-11-14 02:30, 18,72
  MW en MIROVA).
- **Magnitud:** en las 29 que la vía publica, la razón entre el VRP del tablero y el de MIROVA tiene mediana 1,043
  (mínimo 0,753, máximo 1,789).

**Una pasada diurna que no cuenta:** Chillán 2026-11-22 20:40 UTC (MIROVA 6,07 MW). Desde el 2026-11-21 (S193)
producción abre el día en MODIS y la publica; la guardia K sólo procesa noche, así que no tiene la pasada y, por la
§4.2 de la regla, no entra al plazo. Es lo esperado, no una falla.

## Qué dice y qué no dice

Dice que, mientras Chillán estuvo activo, la vía no perdió ninguna alerta fuerte que K viera, y que vio 8 que K perdía,
con magnitudes que calzan con las de MIROVA. Es el resultado que se buscaba al adoptar la vía.

No dice casi nada de otros volcanes ni de alertas débiles cerca de 1 MW: 29 de las 30 protegidas son de un solo volcán
en erupción, y la única de otro volcán (Chaitén) la perdieron los dos detectores. El 95 % de potencia vale para el tipo
de anomalía de Chillán; para Láscar, Villarrica o Copahue con alertas cercanas a 1 MW es SIN DATO. Recordar además que
la reversión automática está suspendida desde S192 (2026-11-21): cumplido el plazo, una candidata se informa como
«fuera de plazo» y decide Nicolás, que es el mismo régimen que ya regía.

## Decisión que espera Nicolás

¿Qué se hace con la guardia K de MODIS?

| Opción | Qué implica |
|---|---|
| **A. Dar el plazo por cumplido y mantener la guardia corriendo, informativa, hasta el 2027-03-02** | Sigue la única comparación diaria vía contra K en MODIS; junta protegidas de otros volcanes; cuesta los minutos de Actions de `guardia-k-modis.yml` y su vigilancia |
| B. Apagar la guardia y su vigilancia ya | Ahorra esos minutos; una pérdida futura de la vía en MODIS sólo la vería la auditoría semanal contra MIROVA (sin decir si K la habría visto) |

**Recomendación: A.** El plazo se cumplió con un solo volcán; dejarla hasta su vencimiento original no cambia
producción y da la diversidad que hoy falta. Apagarla es un PR chico cuando se decida.

**Decidido (Nicolás, 2026-11-24, «Sí, mantenla»): opción A.** La guardia K de MODIS y su vigilancia siguen corriendo,
informativas, hasta el 2027-03-02. No hay cambio de código: los workflows siguen como estaban. Una candidata que aparezca
se informa como «fuera de plazo» y la decide Nicolás.
