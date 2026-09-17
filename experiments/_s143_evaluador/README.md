# Evaluador del A/B D22/D25 (VIIRS 375), S143

Instrumento que aplica los criterios de `docs/PREREGISTRO_AB_D22_D25_S143.md` **antes** de que el
A/B corra. El verificador con contexto limpio (hallazgo 3) mostró que no existía: los scripts de
S135 reconstruían el predicado a mano, tenían radios para seis volcanes, otra partición focal y
nevado, y la referencia de un snapshot local. Escribirlo después de ver resultados deja grados de
libertad que el pre-registro dice no tener.

## Qué hay acá

| archivo | qué hace |
|---|---|
| `parametros.json` | los parámetros de la corrida, congelados y versionados: ventana, ocho volcanes, brazos, control, prefijo, cota, B, semilla, n mínimo y tolerancia |
| `fusionar.py` | une los artefactos de N tramos por `(datetime_utc, sensor)`; prefijo, brazos, volcanes y tramos por argumento; avisa si una clave aparece en dos tramos con contenido distinto |
| `evaluar.py` | aplica los criterios 1, 2 y 3 y escribe JSON con procedencia más un informe Markdown generado desde ese JSON |
| `control_s135.py` | control de instrumento sobre los artefactos reales de S135 (ver `CONTROL_S135.md`) |
| `CONTROL_S135.md` | resultado de ese control, con todos sus números generados por script |
| `control_s135.json`, `informe_control_s135.md` | salidas del control |
| `mutaciones.py` + `MUTACIONES.md` | batería de mutaciones: qué vigilan de verdad los tests |
| `tests/test_evaluador_ab_s143.py` (en el repo) | los tests, escritos antes del código |

## Los parámetros están congelados, no en este README

Ventana, volcanes, brazos, control, prefijo, cota (0,55 km), B, semilla, n mínimo y tolerancia viven
en `parametros.json`, que es lo que el evaluador lee por defecto. La salida JSON copia ese archivo
entero con su sha de git (`meta.parametros_congelados`), guarda lo que la corrida usó de verdad
(`meta.parametros_efectivos`) y marca si coinciden (`meta.parametros_igual_a_los_congelados`); el
informe lo dice en su primera línea. `tests/test_evaluador_ab_s143.py` comprueba valor por valor que
sigan siendo los del pre-registro. Cambiar uno es un cambio de pre-registro, no una opción de la
línea de comandos.

## Cómo se usa cuando lleguen los artefactos del A/B

```bash
python experiments/_s143_evaluador/fusionar.py --prefijo s142ab- \
    --brazos _s142_ab_control _s142_ab_literal _s142_ab_lit_sin_fondo _s142_ab_lit_con_compuerta \
             _s142_ab_lit_sp_suelto _s142_ab_lit_keep_peak \
    --volcanes Isluga Lascar Lastarria PlanchonPeteroa PuyehueCordonCaulle Tupungatito \
               Villarrica NevadosDeChillan \
    --tramo <dir tramo 1> --tramo <dir tramo 2> --out <dir fusionado> --estricto

# brazos, control, volcanes, ventana, prefijo, cota, B, semilla, n mínimo y tolerancia salen de
# parametros.json: no hace falta (ni conviene) pasarlos a mano
python experiments/_s143_evaluador/evaluar.py --dir <dir fusionado> \
    --seguimiento experiments/_s143_evaluador/_seguimiento_s135.json \
    --out-json experiments/_s143_evaluador/resultado_ab_s143.json \
    --out-md experiments/_s143_evaluador/RESULTADO_AB_S143.md
```

Necesita **node** (el predicado del dashboard se ejecuta, no se reescribe) y red la primera vez
(baja CONS y OCR por sha a `_dl_referencia/`, que está fuera de git). Sin red se puede pasar
`--ref-cons` y `--ref-ocr`, y el JSON anota el blob de cada archivo.

## Cómo cumple cada requisito del verificador

| hallazgo | cómo |
|---|---|
| 2 | pérdida = noche confirmada en que el brazo no publica un objeto que pase la **misma** cota; se reporta aparte la versión sin filtro |
| 3 | este evaluador, con tests y control de instrumento sobre S135 |
| 4 | magnitud decisiva sobre pasadas publicadas por ambos; n mínimo sobre las `pos` del control; una fila MIROVA por pasada, CONS antes que OCR |
| 7 | toda pérdida cuenta; no hay reclasificación posterior |
| 10 | tasa de `art` y tasa previa al display en negativos limpios, por brazo |
| 11 | referencia bajada por los sha de `denominadores.json` |
| 14 | bootstrap estratificado por volcán con semilla y B por argumento, más el margen de pasadas que decide el signo |
| 15 | cobertura simétrica por `(datetime_utc, sensor)` y `product_version` |
| 16 | el JSON trae la línea base del control en negativos limpios para contrastarla con el régimen esperado |

## Qué vigilan los tests (batería de mutaciones)

`python experiments/_s143_evaluador/mutaciones.py` aplica una por una 23 mutaciones del evaluador y
de la fusión, corre la suite y anota si mueren. La tabla vive en `MUTACIONES.md` con sus números
generados por el script. El verificador externo del PR #686 (H3) encontró que las reglas de veredicto
no tenían fusible: sobrevivían las mutaciones del extremo del intervalo del criterio 2, la dirección
de la desigualdad del criterio 3, el umbral 0 del criterio 1, la exclusión por cobertura despareja,
el castigo al brazo sin pares decisivos y los valores por defecto de la cota y la tolerancia. Hoy
todas mueren. Las dos que siguen vivas son a propósito: una cambia un comentario (control de que la
batería no se engaña sola) y la otra es equivalente (filtrar los negativos limpios por la etiqueta
del brazo o la del control da el mismo conjunto, porque la etiqueta la fija la referencia).

## Decisiones abiertas (lectura conservadora, para que Nicolás las revise)

1. **Noche con alerta pero sin distancia de MIROVA.** La cota no se puede calcular, así que la
   noche se acepta, igual que en S135, y se cuenta aparte en `aceptadas_sin_cota_calculable`. La
   lectura estricta sería sacarla del universo; se prefirió no achicar el universo del criterio 1.
2. **Qué fila de MIROVA da el VRP de una pasada.** Sólo filas ALERTA con VRP mayor que 0: CONS si
   existe, si no OCR, y entre varias de la misma fuente la más cercana en tiempo. Una fila RUTINA
   con VRP 0 no entra aunque sea CONS: no da razón de magnitud.
3. **n mínimo del criterio 3.** Se cuenta sobre las pasadas `pos` del control (la etiqueta), no
   sobre los pares. Un volcán evaluado que se quede sin pares decisivos cuenta como que empeora:
   dejar de publicar no puede ser una forma de escapar al chequeo.
4. **Cobertura.** Se compara sobre **todos** los sensores presentes en el artefacto, no sólo
   VIIRS 375, y un volcán desparejo se excluye para todos los brazos. Es más estricto que mirar
   sólo el sensor del A/B.
5. **Criterio 2, "cumple".** Intervalo total entero bajo cero y diferencia puntual no positiva en
   cada estrato con datos, sin tolerancia, como está escrito el pre-registro. El margen de signo se
   reporta para que se vea cuántas pasadas lo deciden.
6. **Ganancias.** Se calculan y se reportan, pero no deciden ningún criterio.
7. **Partición focal y nevado.** La de `scripts/build_c2ab_windows.py:41-42` (la que manda el
   spec), distinta de la que usó S135; por eso siempre va además el desglose por volcán.
8. **`inner_radius_km`.** El del dashboard (`frontend/index.html`), que es el que usa el predicado.
   El del `volcanoes.yaml` se anota al lado en `meta.radios` para que se vea si difieren.
9. **Contador `descartadas`.** Cuenta noches en que **ningún** objeto publicado pasa la cota. El de
   S135 anotaba la noche si **algún** objeto quedaba fuera, así que sus números son mucho mayores y
   no son comparables.
10. **Criterio 1 secundario ("la misma medida con cualquier sensor").** NO está implementado: el
    evaluador mide sólo VIIRS 375, que es más estricto. Si se quiere el secundario, hay que ampliar
    `buckets` en `construir_pasadas` y el universo de noches con alerta.
11. **Umbral de la cota.** 0,55 km, el de S135, congelado en `parametros.json` (se puede mover con
    `--cota-km`, y entonces la salida marca que los parámetros ya no son los congelados). Es una
    cota inferior de la separación real (A93) y la distancia de MIROVA viene cuantizada a su celda
    (D15): los casos al borde del umbral son sensibles y en `CONTROL_S135.md` se cuentan aparte.
12. **Exigirle la cota al brazo cambia el criterio 1 respecto de S135.** Con la definición floja el
    brazo D de S135 perdía 12 noches y el B ninguna; con la cota en el brazo, 28 y 14. La decisión
    de "cero pérdidas" que Nicolás tomó el 2026-09-07 se tomó sobre la definición floja: la
    implementación se deja como está (los dos conteos van lado a lado en el JSON y en el informe) y
    ratificar cuál manda le corresponde a Nicolás en la v2 del pre-registro (H2 del verificador
    externo).
