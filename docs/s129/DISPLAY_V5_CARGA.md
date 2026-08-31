# S129 · V5 — Carga y rendimiento del dashboard

> Medición: `experiments/_s129_display_carga/01_carga.json`. Read-only.
> **Este dominio lo audité yo**, no un agente: el que lo tenía asignado murió por un
> error de conexión, y de paso resultó que **mi propio brief estaba mal** (ver abajo).

## Corrección al brief que yo mismo escribí

Le pasé al agente que `mosaico` cargaba «los once JSON completos en paralelo, un cuarto
de gigabyte por carga de página». **Es falso.** Lo arreglaron en S120 y no lo verifiqué
antes de escribirlo — heredé la afirmación de un informe anterior sin trazarla.

Lo que el código hace de verdad:

| vista | qué pide por defecto | verificado en |
|---|---|---|
| `index.html` | `_recent.json`, con fallback al completo | `:901-909` (`const suffix = full ? "" : "_recent"`) |
| `mosaico.html` | `_recent.json`, con fallback | `:392-397` |
| `diario.html` | `_recent.json`; si falla, el completo | `:180-181` |

Y el liviano **sí se genera**: `pages-deploy.yml:76` corre `build_recent_json.py` sobre
`_site/` en cada deploy, con una ventana de **100 días** (`RECENT_DAYS = 100`, elegida
para cubrir el toggle de 90 con margen). No está en el repo porque es un artefacto de
publicación — buscarlo en `data/` da cero, y ese cero se lee como ausencia. Es A89 otra
vez, y esta vez de mi lado.

## Lo que pesa de verdad

| | JSON completos | `_recent` (100 días) |
|---|---|---|
| **total de los 11 Tier A** | **267,2 MB** | **37,2 MB** |
| records | 57.696 | 11.692 |
| reducción | | **86,1 %** |

Por volcán, el más pesado es PCC: 34,2 MB completo contra 4,5 MB liviano.

*(Nota: 37,2 MB es mi medición filtrando a 100 días. El comentario del deploy dice
«~27 MB»; la diferencia es que el archivo crece con el tiempo y ese número quedó de
cuando se escribió. No es un error, es una cifra sin instrumento — candidata al libro de
cuentas.)*

## El costo que sí queda, y es real

**`index.html:3436-3442`.** Cuando el operador elige un rango de **más de 90 días o
«Todo»**, el dashboard baja los JSON **completos**:

```js
if (!_fullHistoryLoaded && (currentDays === 0 || currentDays > 90)) {
  await Promise.all(VOLCANOES.map(v => loadVolcano(v, { full: true })));
```

Eso es **267 MB en una sola ráfaga**, con `Promise.all` sobre `VOLCANOES` —los 45
configurados, no sólo los once con datos, aunque los 34 sin datos retornan temprano—.

Lo que está **bien resuelto**: se hace una sola vez (`_fullHistoryLoaded`), deshabilita
el selector y pone el cursor en `progress` mientras baja. Alguien pensó en esto.

Lo que **no** está resuelto: no hay indicador de progreso ni de cuánto va a pesar, no
hay timeout, y no hay recuperación si un archivo falla a mitad. En una conexión de
terreno, elegir «Todo» deja el dashboard con el cursor en espera por tiempo
indeterminado y sin forma de saber si avanza o se colgó.

## Recomendación, en orden

**1 · Avisar antes de bajar 267 MB.** Un diálogo de confirmación que diga el peso —«el
histórico completo son ~267 MB, ¿continuar?»— y una barra de progreso. Es el arreglo de
mayor efecto y el más barato, y no toca ninguna métrica.

**2 · Registrar el peso en el libro de cuentas.** Los 267 MB y los 37 MB son números que
van a citarse y hoy no tienen instrumento; el comentario del deploy ya quedó
desactualizado. `scripts/libro_de_cuentas.py` los recalcula solo.

**3 · Considerar una ventana intermedia.** Hoy el salto es de 100 días a todo el
histórico. Un `_recent_1y.json` cubriría el caso común —mirar un año— sin bajar los
cinco años completos. Es más trabajo y sólo vale si el rango largo se usa seguido.

## Lo que NO hace falta arreglar

La carga por defecto está bien: 37 MB para once volcanes con 100 días de historia es
razonable, y las tres vistas live ya usan el liviano con fallback. **El fix de S120
funcionó**; lo que faltaba era medirlo y decirlo, porque la creencia de que seguía roto
sobrevivió al arreglo — que es exactamente el modo de olvido que el libro de cuentas
vino a atacar.
