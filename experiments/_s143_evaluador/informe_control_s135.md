# Evaluación del A/B: _s135_ab_b_nokeeppeak, _s135_ab_d_ambos contra _s135_ab_a_control

> Generado por `experiments/_s143_evaluador/evaluar.py` el 2026-09-17T18:48:57+00:00. Ventana 2026-06-01 a 2026-08-31. Todos los números salen del JSON de resultados.

**Parámetros iguales a los congelados en `parametros.json`: no** (sha 5a7b458af18b10ee743fd35a9eba423d571c461a). Referencia fijada por sha: sí.

## Procedencia

```
{
 "evaluador": {
  "archivo": "experiments/_s143_evaluador/evaluar.py",
  "commit": "a8c3fb92f104fcb5e79f4934b6633c8678516999",
  "modificado_sin_commit": true,
  "blob": "33ffa92c0c88c40e2bb43a0484ed1700c2888d6f"
 },
 "banco_paridad": {
  "archivo": "scripts/banco_paridad.py",
  "commit": "f02ff9a5bff7ded4049886349b5dfda96b10acdd",
  "modificado_sin_commit": false,
  "blob": "029103506f213e10d824567adada9d026a3f7777"
 },
 "sha_index_html": "24fba8a157136bf76509ed647c7d086d3f9f45aa",
 "referencia": {
  "fuente": "remoto MendozaVolcanic/Mirova-v1 por sha",
  "commit_por_archivo": {
   "registro_vrp_consolidado.csv": "92f26b98b49069c2d630530d8c803b2dd61da669",
   "registro_vrp_ocr.csv": "f9805ad397dcaaa291833551e5d09508eda38b09"
  },
  "sha_leido_de": "experiments/_s143_preregistro/denominadores.json",
  "respaldo_20260408_blob": "3bb77309a1f5c9ec061f908436cb2bdd2d3ea303"
 }
}
```

## Cobertura pareja

Volcanes pedidos: Isluga, Lascar, Lastarria, PuyehueCordonCaulle, PlanchonPeteroa, Tupungatito. Evaluados: Isluga, Lascar, Lastarria, PuyehueCordonCaulle, PlanchonPeteroa, Tupungatito.

## Noches confirmadas (criterio 1)

Total: **257**. Por estrato: focal 230, nevado 27.

| volcán | estrato | confirmadas | publicadas sin filtro | aceptadas sin cota calculable | coincidencias de fecha descartadas |
|---|---|---|---|---|---|
| Isluga | focal | 71 | 74 | 0 | 3 |
| Lascar | focal | 52 | 61 | 0 | 9 |
| Lastarria | focal | 48 | 50 | 0 | 2 |
| PlanchonPeteroa | focal | 28 | 28 | 0 | 0 |
| PuyehueCordonCaulle | focal | 31 | 37 | 0 | 6 |
| Tupungatito | nevado | 27 | 29 | 0 | 2 |

## Línea base del control en negativos limpios

n = 535; publica 0,938; artefacto 0,000; previa al display 0,938.

## Brazo _s135_ab_b_nokeeppeak

Cumple los tres criterios: **no**.

### Criterio 1: cero noches perdidas

Pérdidas (misma cota en el brazo): **14**; sin filtro en el brazo: 0; ganancias: 3 (sin filtro 0). Cumple: **no**.

| volcán | confirmadas | pérdidas | pérdidas sin filtro en el brazo | ganancias |
|---|---|---|---|---|
| Isluga | 71 | 1 | 0 | 2 |
| Lascar | 52 | 3 | 0 | 0 |
| Lastarria | 48 | 6 | 0 | 1 |
| PlanchonPeteroa | 28 | 4 | 0 | 0 |
| PuyehueCordonCaulle | 31 | 0 | 0 | 0 |
| Tupungatito | 27 | 0 | 0 | 0 |

Noches perdidas: Isluga 2026-06-16, Lascar 2026-06-02, Lascar 2026-06-09, Lascar 2026-06-13, Lastarria 2026-06-01, Lastarria 2026-06-07, Lastarria 2026-06-13, Lastarria 2026-06-14, Lastarria 2026-06-28, Lastarria 2026-07-25, PlanchonPeteroa 2026-06-15, PlanchonPeteroa 2026-06-23, PlanchonPeteroa 2026-07-24, PlanchonPeteroa 2026-08-24.

### Criterio 2: publicación en negativos limpios (brazo menos control)

Cumple: **sí**.

| ámbito | pasadas | noches | tasa control | tasa brazo | diferencia | IC 95 % | solo brazo | solo control | margen de signo |
|---|---|---|---|---|---|---|---|---|---|
| total | 535 | 208 | 0,938 | 0,581 | -0,357 | [-0,395; -0,318] | 0 | 191 | 191 |
| estrato focal | 413 | 160 | 0,937 | 0,576 | -0,361 | [-0,403; -0,319] | 0 | 149 | 149 |
| estrato nevado | 122 | 48 | 0,943 | 0,598 | -0,344 | [-0,434; -0,256] | 0 | 42 | 42 |
| Isluga | 21 | 8 | 0,905 | 0,429 | -0,476 | [-0,667; -0,263] | 0 | 10 | 10 |
| Lascar | 50 | 22 | 0,820 | 0,300 | -0,520 | [-0,653; -0,392] | 0 | 26 | 26 |
| Lastarria | 52 | 24 | 0,962 | 0,519 | -0,442 | [-0,580; -0,308] | 0 | 23 | 23 |
| PlanchonPeteroa | 144 | 53 | 0,951 | 0,424 | -0,528 | [-0,609; -0,442] | 0 | 76 | 76 |
| PuyehueCordonCaulle | 146 | 53 | 0,959 | 0,863 | -0,096 | [-0,142; -0,053] | 0 | 14 | 14 |
| Tupungatito | 122 | 48 | 0,943 | 0,598 | -0,344 | [-0,434; -0,256] | 0 | 42 | 42 |

Acompañantes: artefacto control 0,000, brazo 0,000 (sube en el brazo: no); previa al display control 0,938, brazo 0,581.

### Criterio 3: magnitud del operador sobre VRP de MIROVA

Cumple: **no**. Volcanes que empeoran más de la tolerancia: Tupungatito.

| ámbito | pos control | pares decisivos | mediana control | mediana brazo | evaluado (n mín.) | informativo control (n, mediana) | informativo brazo (n, mediana) |
|---|---|---|---|---|---|---|---|
| total | 498 | 488 | 0,749 | 0,723 |  | 498, 0,748 | 488, 0,723 |
| estrato focal | 447 | 438 | 0,770 | 0,751 |  | 447, 0,768 | 438, 0,751 |
| estrato nevado | 51 | 50 | 0,556 | 0,494 |  | 51, 0,562 | 50, 0,494 |
| Isluga | 131 | 125 | 0,632 | 0,582 | sí | 131, 0,632 | 125, 0,582 |
| Lascar | 110 | 109 | 0,631 | 0,626 | sí | 110, 0,629 | 109, 0,626 |
| Lastarria | 76 | 74 | 0,965 | 1,012 | sí | 76, 0,960 | 74, 1,012 |
| PlanchonPeteroa | 44 | 44 | 0,956 | 0,997 | sí | 44, 0,956 | 44, 0,997 |
| PuyehueCordonCaulle | 86 | 86 | 1,021 | 1,021 | sí | 86, 1,021 | 86, 1,021 |
| Tupungatito | 51 | 50 | 0,556 | 0,494 | sí | 51, 0,562 | 50, 0,494 |

## Brazo _s135_ab_d_ambos

Cumple los tres criterios: **no**.

### Criterio 1: cero noches perdidas

Pérdidas (misma cota en el brazo): **28**; sin filtro en el brazo: 12; ganancias: 1 (sin filtro 0). Cumple: **no**.

| volcán | confirmadas | pérdidas | pérdidas sin filtro en el brazo | ganancias |
|---|---|---|---|---|
| Isluga | 71 | 4 | 3 | 0 |
| Lascar | 52 | 4 | 0 | 0 |
| Lastarria | 48 | 10 | 2 | 0 |
| PlanchonPeteroa | 28 | 7 | 5 | 0 |
| PuyehueCordonCaulle | 31 | 0 | 0 | 1 |
| Tupungatito | 27 | 3 | 2 | 0 |

Noches perdidas: Isluga 2026-06-16, Isluga 2026-07-01, Isluga 2026-07-16, Isluga 2026-08-19, Lascar 2026-06-02, Lascar 2026-06-09, Lascar 2026-06-13, Lascar 2026-06-25, Lastarria 2026-06-01, Lastarria 2026-06-07, Lastarria 2026-06-13, Lastarria 2026-06-14, Lastarria 2026-06-28, Lastarria 2026-07-02, Lastarria 2026-07-06, Lastarria 2026-07-25, Lastarria 2026-08-02, Lastarria 2026-08-28, PlanchonPeteroa 2026-06-15, PlanchonPeteroa 2026-06-22, PlanchonPeteroa 2026-06-23, PlanchonPeteroa 2026-06-26, PlanchonPeteroa 2026-07-24, PlanchonPeteroa 2026-08-09, PlanchonPeteroa 2026-08-24, Tupungatito 2026-06-03, Tupungatito 2026-07-07, Tupungatito 2026-08-01.

Perdidas sin filtro en el brazo: Isluga 2026-07-01, Isluga 2026-07-16, Isluga 2026-08-19, Lastarria 2026-07-02, Lastarria 2026-08-28, PlanchonPeteroa 2026-06-22, PlanchonPeteroa 2026-06-26, PlanchonPeteroa 2026-07-24, PlanchonPeteroa 2026-08-09, PlanchonPeteroa 2026-08-24, Tupungatito 2026-07-07, Tupungatito 2026-08-01.

### Criterio 2: publicación en negativos limpios (brazo menos control)

Cumple: **sí**.

| ámbito | pasadas | noches | tasa control | tasa brazo | diferencia | IC 95 % | solo brazo | solo control | margen de signo |
|---|---|---|---|---|---|---|---|---|---|
| total | 535 | 208 | 0,938 | 0,430 | -0,508 | [-0,549; -0,466] | 0 | 272 | 272 |
| estrato focal | 413 | 160 | 0,937 | 0,431 | -0,506 | [-0,552; -0,460] | 0 | 209 | 209 |
| estrato nevado | 122 | 48 | 0,943 | 0,426 | -0,516 | [-0,607; -0,425] | 0 | 63 | 63 |
| Isluga | 21 | 8 | 0,905 | 0,286 | -0,619 | [-0,800; -0,421] | 0 | 13 | 13 |
| Lascar | 50 | 22 | 0,820 | 0,140 | -0,680 | [-0,800; -0,548] | 0 | 34 | 34 |
| Lastarria | 52 | 24 | 0,962 | 0,269 | -0,692 | [-0,827; -0,543] | 0 | 36 | 36 |
| PlanchonPeteroa | 144 | 53 | 0,951 | 0,250 | -0,701 | [-0,779; -0,618] | 0 | 101 | 101 |
| PuyehueCordonCaulle | 146 | 53 | 0,959 | 0,788 | -0,171 | [-0,235; -0,111] | 0 | 25 | 25 |
| Tupungatito | 122 | 48 | 0,943 | 0,426 | -0,516 | [-0,607; -0,425] | 0 | 63 | 63 |

Acompañantes: artefacto control 0,000, brazo 0,000 (sube en el brazo: no); previa al display control 0,938, brazo 0,430.

### Criterio 3: magnitud del operador sobre VRP de MIROVA

Cumple: **no**. Volcanes que empeoran más de la tolerancia: ninguno.

| ámbito | pos control | pares decisivos | mediana control | mediana brazo | evaluado (n mín.) | informativo control (n, mediana) | informativo brazo (n, mediana) |
|---|---|---|---|---|---|---|---|
| total | 498 | 425 | 0,730 | 0,720 |  | 498, 0,748 | 425, 0,720 |
| estrato focal | 447 | 386 | 0,750 | 0,745 |  | 447, 0,768 | 386, 0,745 |
| estrato nevado | 51 | 39 | 0,539 | 0,539 |  | 51, 0,562 | 39, 0,539 |
| Isluga | 131 | 106 | 0,614 | 0,614 | sí | 131, 0,632 | 106, 0,614 |
| Lascar | 110 | 104 | 0,629 | 0,629 | sí | 110, 0,629 | 104, 0,629 |
| Lastarria | 76 | 65 | 1,008 | 0,957 | sí | 76, 0,960 | 65, 0,957 |
| PlanchonPeteroa | 44 | 31 | 0,905 | 0,905 | sí | 44, 0,956 | 31, 0,905 |
| PuyehueCordonCaulle | 86 | 80 | 1,021 | 0,993 | sí | 86, 1,021 | 80, 0,993 |
| Tupungatito | 51 | 39 | 0,539 | 0,539 | sí | 51, 0,562 | 39, 0,539 |

## Seguimiento de noches puntuales

Celda: publica con cota / publica sin filtro.

| volcán | fecha | _s135_ab_a_control | _s135_ab_b_nokeeppeak | _s135_ab_d_ambos |
|---|---|---|---|---|
| Isluga | 2026-07-01 | sí / sí | sí / sí | no / no |
| Isluga | 2026-07-16 | sí / sí | sí / sí | no / no |
| Isluga | 2026-08-19 | sí / sí | sí / sí | no / no |
| Lastarria | 2026-07-02 | sí / sí | sí / sí | no / no |
| Lastarria | 2026-08-28 | sí / sí | sí / sí | no / no |
| PlanchonPeteroa | 2026-06-22 | sí / sí | sí / sí | no / no |
| PlanchonPeteroa | 2026-06-26 | sí / sí | sí / sí | no / no |
| PlanchonPeteroa | 2026-07-24 | sí / sí | no / sí | no / no |
| PlanchonPeteroa | 2026-08-09 | sí / sí | sí / sí | no / no |
| PlanchonPeteroa | 2026-08-24 | sí / sí | no / sí | no / no |
| Tupungatito | 2026-07-07 | sí / sí | sí / sí | no / no |
| Tupungatito | 2026-08-01 | sí / sí | sí / sí | no / no |

## Controles del instrumento

```
{
 "identidad_predicado_node": true,
 "control_contra_si_mismo": {
  "perdidas": 0,
  "ganancias": 0,
  "dif_neg_limpio": 0.0
 }
}
```
