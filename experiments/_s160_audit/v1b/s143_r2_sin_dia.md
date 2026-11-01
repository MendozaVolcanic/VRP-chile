# Evaluación del A/B: _v1b_sin_dia contra _s142_ab_control

> Generado por `experiments/_s143_evaluador/evaluar.py` el 2026-10-22T04:46:46+00:00. Ventana 2026-06-01 a 2026-08-31. Todos los números salen del JSON de resultados.

**Parámetros iguales a los congelados en `parametros.json`: no** (sha 1093f01c78bf41e26bc7e2df3fcf6d5928c14c2c). Referencia fijada por sha: no.

## Procedencia

```
{
 "evaluador": {
  "archivo": "experiments/_s143_evaluador/evaluar.py",
  "commit": "a29d6e028653fda668eabd8fe6abf6345e6f010f",
  "modificado_sin_commit": false,
  "blob": "1af058db80d77580812a163f1e60f1ba4fa859f6"
 },
 "banco_paridad": {
  "archivo": "scripts/banco_paridad.py",
  "commit": "9ac09b163ddd17d1a3e93bf44c5f86dc0de45a4c",
  "modificado_sin_commit": false,
  "blob": "384c1369dc5dc13ae2ad35169d19963c92da3a0c"
 },
 "sha_index_html": "85a0bd8d4f54673ac02fe57446960039c2334bf2",
 "referencia": {
  "fuente": "archivos locales",
  "cons": "D:\\vrp-trabajo\\temporales\\s160_audit\\main\\latest_consolidado.csv",
  "ocr": "D:\\vrp-trabajo\\temporales\\s160_audit\\main\\data\\mirova_reference\\mirova_v1_snapshot\\registro_vrp_ocr.csv",
  "blob_cons": "4029c4b3f3b6cefeda8e7e40ced582df1b6b9b08",
  "blob_ocr": "13b79ea9856c0568c1d31f03c6d156ed8ccdcc35",
  "respaldo_20260408_blob": "3bb77309a1f5c9ec061f908436cb2bdd2d3ea303"
 }
}
```

## Cobertura pareja

Volcanes pedidos: Isluga, Lascar, Lastarria, PlanchonPeteroa, PuyehueCordonCaulle, Tupungatito, Chaiten, Villarrica, NevadosDeChillan. Evaluados: ninguno.

Excluidos del veredicto (cobertura despareja o archivo faltante):
- Isluga: _v1b_sin_dia: solo_control 4, solo_brazo 0, product_version distinto 0
- Lascar: _v1b_sin_dia: solo_control 4, solo_brazo 0, product_version distinto 0
- Lastarria: _v1b_sin_dia: solo_control 4, solo_brazo 0, product_version distinto 0
- PlanchonPeteroa: _v1b_sin_dia: solo_control 5, solo_brazo 0, product_version distinto 0
- PuyehueCordonCaulle: _v1b_sin_dia: solo_control 5, solo_brazo 0, product_version distinto 0
- Tupungatito: _v1b_sin_dia: solo_control 5, solo_brazo 0, product_version distinto 0
- Chaiten: _v1b_sin_dia: solo_control 5, solo_brazo 0, product_version distinto 0
- Villarrica: _v1b_sin_dia: solo_control 6, solo_brazo 0, product_version distinto 0
- NevadosDeChillan: _v1b_sin_dia: solo_control 5, solo_brazo 0, product_version distinto 0

## Noches confirmadas (criterio 1)

Posición del record con que se mide la cota: **final_hotspot_si_test1** (la otra se reporta al lado en cada brazo).

Total: **0**. Por estrato: .

| volcán | estrato | confirmadas | publicadas sin filtro | aceptadas sin cota calculable | coincidencias de fecha descartadas |
|---|---|---|---|---|---|

## Línea base del control en negativos limpios

n = 0; publica sin dato; artefacto sin dato; previa al display sin dato.

## Brazo _v1b_sin_dia

Cumple los tres criterios: **no**.

### Criterio 1: cero noches perdidas

Pérdidas (misma cota en el brazo): **0**; sin filtro en el brazo: 0; ganancias: 0 (sin filtro 0). Cumple: **sí**.

Medido con las dos posiciones del record (decisión abierta; hoy decide **final_hotspot_si_test1**):

| posición | noches confirmadas | pérdidas | pérdidas sin filtro | ganancias | cumple | decide |
|---|---|---|---|---|---|---|
| centroide | 0 | 0 | 0 | 0 | sí | no |
| final_hotspot_si_test1 | 0 | 0 | 0 | 0 | sí | sí |

Por volcán, con el campo que decide:

| volcán | confirmadas | pérdidas | pérdidas sin filtro en el brazo | ganancias |
|---|---|---|---|---|

### Criterio 2: publicación en negativos limpios (brazo menos control)

Cumple: **no**.

| ámbito | pasadas | noches | tasa control | tasa brazo | diferencia | IC 95 % | solo brazo | solo control | margen de signo |
|---|---|---|---|---|---|---|---|---|---|
| total | 0 | 0 | sin dato | sin dato | sin dato | sin dato | 0 | 0 | 0 |

Acompañantes: artefacto control sin dato, brazo sin dato (sube en el brazo: sin dato); previa al display control sin dato, brazo sin dato.

### Criterio 3: magnitud del operador sobre VRP de MIROVA

Cumple: **no**. Volcanes que empeoran más de la tolerancia: ninguno.

| ámbito | pos control | pares decisivos | mediana control | mediana brazo | evaluado (n mín.) | informativo control (n, mediana) | informativo brazo (n, mediana) |
|---|---|---|---|---|---|---|---|
| total | 0 | 0 | sin dato | sin dato |  | 0, sin dato | 0, sin dato |

## Controles del instrumento

```
{
 "identidad_predicado_node": true,
 "control_contra_si_mismo": {
  "perdidas": 0,
  "ganancias": 0,
  "dif_neg_limpio": null
 }
}
```
