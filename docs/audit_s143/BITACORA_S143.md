# Bitácora S143: del frente D22/D25 al A/B corriendo

> Registro cronológico de la sesión, con la evidencia de cada paso. Se escribe **mientras** pasa, no
> al cierre: lo que queda sólo en la conversación se pierde. Cada número de acá sale de un archivo
> generado por script o de un comando cuya salida se cita.
>
> Principio que ordena todo el frente (Nicolás, 2026-09-17): **para que nos crean tenemos que tener
> al menos todo lo que MIROVA publica**; lo que mejora la detección y MIROVA no tiene va al perfil
> `experimental`, separado de la serie operacional. Por eso el criterio 1 (cero pérdidas) manda sobre
> la sobre-publicación y sobre la magnitud.

## 0. De dónde venía el frente

- La brecha de paridad en VIIRS 375 no es de recall sino de **sobre-publicación** (A98, S139) y la
  magnitud está en ~0,7 por conteo de píxeles y fondo (A99).
- S135 midió que quitar `keep_peak` y condicionar el segundo pase elimina el artefacto pero **pierde
  12 noches** que MIROVA publica (`experiments/_s135_ab_d1d2/resultado_final.json`).
- S142 dejó escritos y apagados los flags D22 (compuerta de temperatura) y D25 (fondo por vecinos),
  con su plan y su verificador.

## 1. Los brazos del A/B (PR #683)

Seis perfiles aislados `pipeline/profiles/_s142_ab_*.yaml`: control, literal y cuatro ablaciones,
sólo VIIRS 375, `data_subdir` propio, fuera del cron. Los seis tests de lectura de brazos dejaron de
saltarse. D22 y D25 anotados en `docs/MIROVA_DIVERGENCES.md`; `docs/FICHA_SDA_VRP_CHILE.md` v1.6, sin
cambios de lógica. Suite 1500 passed.

## 2. Pre-registro v1 y el hallazgo que frenó la corrida (PR #684)

Escrito antes de correr, con denominadores de script (`experiments/_s143_preregistro/denominadores.json`).
El verificador con contexto limpio dio **CORREGIR ANTES** con 18 hallazgos. El mayor, gravedad 5: en
los seis brazos la compuerta **sigue puesta** en la máscara contextual que filtra el camino del Test 1
(`process_viirs.py:1063-1081` y `:1839-1850`), que es justo la ruta de las 12 pérdidas de S135. Sin
declararlo, un resultado negativo se habría atribuido a una compuerta que nunca se quitó.

Decisión de Nicolás: **opción A**, probe barato antes del A/B.

## 3. El probe de las 12 noches (PR #685, #689, #690)

- **Muestra**: 61 pasadas V375 elegidas desde los artefactos de S135 con el predicado del dashboard
  (41 de las 12 noches, 12 negativos con artefacto, 8 negativos quietos), semilla 143.
- **Seis variantes**, una por proceso, con los parches en el namespace de `pipeline.process_viirs`
  (A75, sólo lectura).
- **Verificador pre corrida**: CORREGIR ANTES, cinco correcciones aplicadas. La mayor: quitar la
  compuerta puede **apagar** el filtro del Test 1 por `only_test1_source`, así que el probe cuenta las
  llamadas al filtro para distinguir las dos causas.
- **Corrida**: piloto Lastarria (run 35257515864) y los otros tres (run 35260023218), 61 de 61
  pasadas en las seis variantes, los cinco controles de instrumento cumplen.

| variante | noches recuperadas (con cota) | neg_artefacto publicados | pasadas con filtro del Test 1 |
|---|---|---|---|
| control | 12 de 12 | 12 de 12 | 50 |
| s135_d | 0 de 12 | 0 de 12 | 53 |
| s135_d_sin_compuerta_ctx | 11 de 12 | 7 de 12 | 53 |
| **literal** | **10 de 12** | 6 de 12 | 47 |
| literal_sin_compuerta_ctx | 11 de 12 | 9 de 12 | 32 |
| literal_t1_sin_filtro | 12 de 12 | 12 de 12 | 0 |

- **Verificador post corrida**: SE SOSTIENE CON MATICES. Reprodujo cada número con su propio cargador
  y su propio corredor de node, sin discrepancias. Habilitado: **D22 y D25 solos recuperan 10 de 12**,
  y ese 10 no cambia con el campo de posición. No habilitado: cambiar los brazos por la diferencia 11
  contra 10 (con `final_hotspot` las tres literales empatan en 10 y el control cae a 10).
- **Consecuencia**: los seis brazos quedan cerrados, sin agregar ninguno y **sin tocar el pipeline**.
  Frente anotado para después: el filtro contextual del Test 1 (S99, D23), que no está en el paper.

## 4. El evaluador (PR #686, #687, #691, #692, #693)

Escrito con TDD antes de ver datos del A/B, en `experiments/_s143_evaluador/`:

- Predicado del dashboard **ejecutado con node**, nunca reconstruido (A97).
- Referencia de MIROVA fijada por sha; informe generado desde el JSON (S91).
- Cobertura simétrica con `product_version`; cota de mismo objeto **también en el brazo**; bootstrap
  estratificado por volcán; magnitud sobre pasadas publicadas por ambos, CONS antes que OCR.
- **Control de instrumento sobre S135**: reproduce las 12 pérdidas del brazo D una a una; 257 noches
  confirmadas contra las 260 publicadas, y la diferencia quedó atribuida y verificada dos veces al
  regex del loader OCR que cambió en #652 (con el anterior vuelven a dar 260).
- **Verificador externo**: CORREGIR ANTES. De 22 mutaciones sobrevivían 9, todas en las reglas de
  decisión. Tras corregir: **25 de 27 muertas**, las 2 vivas justificadas. Parámetros congelados en
  `parametros.json` (ventana, 9 volcanes, brazos, cota 0,55 km, B 10000, semilla 143, n mínimo 30,
  tolerancia 0,05), copiados con su sha en cada salida.
- Dos correcciones de formato que habrían roto la corrida sin avisar: el prefijo de artefacto
  (`s143ab-`, no `s142ab-`) y **un prefijo por tramo**, porque el workflow mete el tramo en el nombre.

## 5. Pre-registro v2 (PR #688, #690)

Corrige los 18 hallazgos. Lo principal: declara lo que los brazos no pueden probar; define pérdida con
la cota también en el brazo; bootstrap estratificado; magnitud sobre pares comunes; acompañantes del
display (A72); control de instrumento sobre la línea base; tramo de confirmación fuera de muestra
(2026-09-01 a 2026-09-15); desviaciones declaradas. Universo de 8 a **9 volcanes**: entra Chaitén
(221 negativos limpios y magnitud 1,35, el contraejemplo de un fondo que sube la magnitud).

## 6. La corrida

- Tag defensivo `pre-s143-ab-d22-d25`; los dos tramos se despachan sobre ese tag para que corran con
  el mismo código.
- **Tramo 1** (2026-06-01 a 2026-07-15): run 35266704955, 54 jobs, 6 en paralelo. Primer job verde en
  71 min, verificado: sólo VIIRS 375, 156 records en la ventana, con `f5_core_vrp_mw` y los
  diagnósticos de D25.
- **Prueba de humo de la cadena** con cuatro brazos de Isluga ya terminados: fusión sin conflictos y
  evaluador de punta a punta (38 noches confirmadas en media ventana). No es resultado: es control de
  formato antes de tener los 108 artefactos.
- **Tramo 2** (2026-07-16 a 2026-08-31): se despacha cuando termine el 1; el pre-registro pide no
  superponerlos, y además comparten cupo de jobs con el cron del NRT.

## 7. Decisiones abiertas de Nicolás

1. **Cota de mismo objeto exigida también al brazo.** Recomendado: sí. Medido sobre S135: el brazo D
   pasa de 12 a 28 pérdidas y el B de 0 a 14.
2. **Campo de posición de la cota.** Recomendado: `final_hotspot` cuando la fuente es `test1_roi`,
   centroide en el resto (A84; los dos campos separan 1,06 km de mediana en esos records).
3. Token de Earthdata: vence **2026-10-03T07:18 UTC**, verificado hoy en el healthcheck (15,6 días).
4. Cron externo y correo a Coppola: siguen pendientes de S142.

## 8. Lo aprendido en esta sesión

1. **Un probe barato antes de un A/B caro cambia el diseño, no sólo lo confirma.** Acá evitó correr
   180 horas de cómputo sobre brazos que no podían responder la pregunta, y además mostró que los
   brazos que ya teníamos sí la responden (10 de 12), o sea ahorró trabajo en las dos direcciones.
2. **Un verificador con contexto limpio antes de correr paga tres veces**: encontró el hallazgo de
   gravedad 5 del pre-registro, las cinco correcciones del probe y los 9 mutantes vivos del
   evaluador, todos antes de gastar la corrida.
3. **El formato de los artefactos es parte del instrumento.** Dos desfases de nombre (prefijo y tramo)
   habrían dejado media ventana afuera **sin error visible**. El patrón es el de A92: lo que falla en
   silencio es peor que lo que falla fuerte.
4. **La métrica "noches recuperadas" crece con cualquier publicación.** La variante que llega a 12 de
   12 publica 54 de 61 pasadas. Sin la cota de mismo objeto y sin el costo en negativos al lado, ese
   12 parece el mejor resultado y es el peor.
