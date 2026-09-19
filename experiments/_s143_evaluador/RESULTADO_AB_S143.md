# Evaluación del A/B: _s142_ab_literal, _s142_ab_lit_sin_fondo, _s142_ab_lit_con_compuerta, _s142_ab_lit_sp_suelto, _s142_ab_lit_keep_peak contra _s142_ab_control

> Generado por `experiments/_s143_evaluador/evaluar.py` el 2026-09-19T16:13:43+00:00. Ventana 2026-06-01 a 2026-08-31. Todos los números salen del JSON de resultados.

**Parámetros iguales a los congelados en `parametros.json`: sí** (sha 1093f01c78bf41e26bc7e2df3fcf6d5928c14c2c). Referencia fijada por sha: sí.

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

Volcanes pedidos: Isluga, Lascar, Lastarria, PlanchonPeteroa, PuyehueCordonCaulle, Tupungatito, Chaiten, Villarrica, NevadosDeChillan. Evaluados: Isluga, Lascar, Lastarria, PlanchonPeteroa, PuyehueCordonCaulle, Tupungatito, Chaiten, Villarrica, NevadosDeChillan.

## Noches confirmadas (criterio 1)

Posición del record con que se mide la cota: **final_hotspot_si_test1** (la otra se reporta al lado en cada brazo).

Total: **272**. Por estrato: focal 220, nevado 52.

| volcán | estrato | confirmadas | publicadas sin filtro | aceptadas sin cota calculable | coincidencias de fecha descartadas |
|---|---|---|---|---|---|
| Chaiten | nevado | 13 | 14 | 0 | 1 |
| Isluga | focal | 73 | 74 | 0 | 1 |
| Lascar | focal | 50 | 61 | 0 | 11 |
| Lastarria | focal | 42 | 50 | 0 | 8 |
| NevadosDeChillan | nevado | 3 | 5 | 0 | 2 |
| PlanchonPeteroa | focal | 24 | 28 | 0 | 4 |
| PuyehueCordonCaulle | focal | 31 | 37 | 0 | 6 |
| Tupungatito | nevado | 27 | 29 | 0 | 2 |
| Villarrica | nevado | 9 | 11 | 0 | 2 |

## Línea base del control en negativos limpios

n = 1170; publica 0,917; artefacto 0,000; previa al display 0,917.

## Brazo _s142_ab_literal

Cumple los tres criterios: **no**.

### Criterio 1: cero noches perdidas

Pérdidas (misma cota en el brazo): **5**; sin filtro en el brazo: 0; ganancias: 3 (sin filtro 0). Cumple: **no**.

Medido con las dos posiciones del record (decisión abierta; hoy decide **final_hotspot_si_test1**):

| posición | noches confirmadas | pérdidas | pérdidas sin filtro | ganancias | cumple | decide |
|---|---|---|---|---|---|---|
| centroide | 283 | 15 | 0 | 5 | no | no |
| final_hotspot_si_test1 | 272 | 5 | 0 | 3 | no | sí |

Por volcán, con el campo que decide:

| volcán | confirmadas | pérdidas | pérdidas sin filtro en el brazo | ganancias |
|---|---|---|---|---|
| Chaiten | 13 | 0 | 0 | 1 |
| Isluga | 73 | 1 | 0 | 0 |
| Lascar | 50 | 1 | 0 | 1 |
| Lastarria | 42 | 3 | 0 | 1 |
| NevadosDeChillan | 3 | 0 | 0 | 0 |
| PlanchonPeteroa | 24 | 0 | 0 | 0 |
| PuyehueCordonCaulle | 31 | 0 | 0 | 0 |
| Tupungatito | 27 | 0 | 0 | 0 |
| Villarrica | 9 | 0 | 0 | 0 |

Noches perdidas: Isluga 2026-06-16, Lascar 2026-06-13, Lastarria 2026-06-07, Lastarria 2026-06-14, Lastarria 2026-07-25.

### Criterio 2: publicación en negativos limpios (brazo menos control)

Cumple: **sí**.

| ámbito | pasadas | noches | tasa control | tasa brazo | diferencia | IC 95 % | solo brazo | solo control | margen de signo |
|---|---|---|---|---|---|---|---|---|---|
| total | 1170 | 435 | 0,917 | 0,547 | -0,370 | [-0,397; -0,344] | 9 | 442 | 433 |
| estrato focal | 413 | 160 | 0,937 | 0,610 | -0,327 | [-0,368; -0,286] | 2 | 137 | 135 |
| estrato nevado | 757 | 275 | 0,906 | 0,513 | -0,394 | [-0,428; -0,360] | 7 | 305 | 298 |
| Chaiten | 220 | 77 | 0,932 | 0,627 | -0,305 | [-0,364; -0,248] | 0 | 67 | 67 |
| Isluga | 21 | 8 | 0,905 | 0,667 | -0,238 | [-0,417; -0,056] | 1 | 6 | 5 |
| Lascar | 50 | 22 | 0,820 | 0,480 | -0,340 | [-0,452; -0,239] | 1 | 18 | 17 |
| Lastarria | 52 | 24 | 0,962 | 0,519 | -0,442 | [-0,580; -0,308] | 0 | 23 | 23 |
| NevadosDeChillan | 197 | 73 | 0,883 | 0,421 | -0,462 | [-0,541; -0,380] | 6 | 97 | 91 |
| PlanchonPeteroa | 144 | 53 | 0,951 | 0,424 | -0,528 | [-0,609; -0,442] | 0 | 76 | 76 |
| PuyehueCordonCaulle | 146 | 53 | 0,959 | 0,863 | -0,096 | [-0,142; -0,053] | 0 | 14 | 14 |
| Tupungatito | 122 | 48 | 0,943 | 0,713 | -0,230 | [-0,300; -0,164] | 1 | 29 | 28 |
| Villarrica | 218 | 77 | 0,881 | 0,367 | -0,514 | [-0,574; -0,452] | 0 | 112 | 112 |

Acompañantes: artefacto control 0,000, brazo 0,000 (sube en el brazo: no); previa al display control 0,917, brazo 0,547.

### Criterio 3: magnitud del operador sobre VRP de MIROVA

Cumple: **sí**. Volcanes que empeoran más de la tolerancia: ninguno.

| ámbito | pos control | pares decisivos | mediana control | mediana brazo | evaluado (n mín.) | informativo control (n, mediana) | informativo brazo (n, mediana) |
|---|---|---|---|---|---|---|---|
| total | 532 | 530 | 0,773 | 0,945 |  | 532, 0,770 | 530, 0,945 |
| estrato focal | 447 | 445 | 0,768 | 0,899 |  | 447, 0,768 | 445, 0,899 |
| estrato nevado | 85 | 85 | 0,805 | 1,140 |  | 85, 0,805 | 85, 1,140 |
| Chaiten | 17 | 17 | 1,296 | 1,481 | no | 17, 1,296 | 17, 1,481 |
| Isluga | 131 | 131 | 0,632 | 0,881 | sí | 131, 0,632 | 131, 0,881 |
| Lascar | 110 | 110 | 0,629 | 0,740 | sí | 110, 0,629 | 110, 0,740 |
| Lastarria | 76 | 74 | 0,965 | 0,974 | sí | 76, 0,960 | 74, 0,974 |
| NevadosDeChillan | 6 | 6 | 1,208 | 1,321 | no | 6, 1,208 | 6, 1,321 |
| PlanchonPeteroa | 44 | 44 | 0,956 | 0,995 | sí | 44, 0,956 | 44, 0,995 |
| PuyehueCordonCaulle | 86 | 86 | 1,021 | 1,022 | sí | 86, 1,021 | 86, 1,022 |
| Tupungatito | 51 | 51 | 0,562 | 1,113 | sí | 51, 0,562 | 51, 1,113 |
| Villarrica | 11 | 11 | 0,860 | 0,893 | no | 11, 0,860 | 11, 0,893 |

## Brazo _s142_ab_lit_sin_fondo

Cumple los tres criterios: **no**.

### Criterio 1: cero noches perdidas

Pérdidas (misma cota en el brazo): **8**; sin filtro en el brazo: 3; ganancias: 2 (sin filtro 0). Cumple: **no**.

Medido con las dos posiciones del record (decisión abierta; hoy decide **final_hotspot_si_test1**):

| posición | noches confirmadas | pérdidas | pérdidas sin filtro | ganancias | cumple | decide |
|---|---|---|---|---|---|---|
| centroide | 283 | 18 | 3 | 4 | no | no |
| final_hotspot_si_test1 | 272 | 8 | 3 | 2 | no | sí |

Por volcán, con el campo que decide:

| volcán | confirmadas | pérdidas | pérdidas sin filtro en el brazo | ganancias |
|---|---|---|---|---|
| Chaiten | 13 | 0 | 0 | 1 |
| Isluga | 73 | 1 | 0 | 0 |
| Lascar | 50 | 1 | 0 | 0 |
| Lastarria | 42 | 3 | 0 | 1 |
| NevadosDeChillan | 3 | 3 | 3 | 0 |
| PlanchonPeteroa | 24 | 0 | 0 | 0 |
| PuyehueCordonCaulle | 31 | 0 | 0 | 0 |
| Tupungatito | 27 | 0 | 0 | 0 |
| Villarrica | 9 | 0 | 0 | 0 |

Noches perdidas: Isluga 2026-06-16, Lascar 2026-06-13, Lastarria 2026-06-07, Lastarria 2026-06-14, Lastarria 2026-07-25, NevadosDeChillan 2026-06-16, NevadosDeChillan 2026-08-18, NevadosDeChillan 2026-08-20.

Perdidas sin filtro en el brazo: NevadosDeChillan 2026-06-16, NevadosDeChillan 2026-08-18, NevadosDeChillan 2026-08-20.

### Criterio 2: publicación en negativos limpios (brazo menos control)

Cumple: **sí**.

| ámbito | pasadas | noches | tasa control | tasa brazo | diferencia | IC 95 % | solo brazo | solo control | margen de signo |
|---|---|---|---|---|---|---|---|---|---|
| total | 1170 | 435 | 0,917 | 0,495 | -0,422 | [-0,449; -0,396] | 0 | 494 | 494 |
| estrato focal | 413 | 160 | 0,937 | 0,576 | -0,361 | [-0,403; -0,319] | 0 | 149 | 149 |
| estrato nevado | 757 | 275 | 0,906 | 0,450 | -0,456 | [-0,490; -0,422] | 0 | 345 | 345 |
| Chaiten | 220 | 77 | 0,932 | 0,627 | -0,305 | [-0,364; -0,248] | 0 | 67 | 67 |
| Isluga | 21 | 8 | 0,905 | 0,429 | -0,476 | [-0,667; -0,263] | 0 | 10 | 10 |
| Lascar | 50 | 22 | 0,820 | 0,300 | -0,520 | [-0,653; -0,392] | 0 | 26 | 26 |
| Lastarria | 52 | 24 | 0,962 | 0,519 | -0,442 | [-0,580; -0,308] | 0 | 23 | 23 |
| NevadosDeChillan | 197 | 73 | 0,883 | 0,249 | -0,635 | [-0,704; -0,563] | 0 | 125 | 125 |
| PlanchonPeteroa | 144 | 53 | 0,951 | 0,424 | -0,528 | [-0,609; -0,442] | 0 | 76 | 76 |
| PuyehueCordonCaulle | 146 | 53 | 0,959 | 0,863 | -0,096 | [-0,142; -0,053] | 0 | 14 | 14 |
| Tupungatito | 122 | 48 | 0,943 | 0,607 | -0,336 | [-0,425; -0,252] | 0 | 41 | 41 |
| Villarrica | 218 | 77 | 0,881 | 0,367 | -0,514 | [-0,574; -0,452] | 0 | 112 | 112 |

Acompañantes: artefacto control 0,000, brazo 0,000 (sube en el brazo: no); previa al display control 0,917, brazo 0,495.

### Criterio 3: magnitud del operador sobre VRP de MIROVA

Cumple: **no**. Volcanes que empeoran más de la tolerancia: Tupungatito.

| ámbito | pos control | pares decisivos | mediana control | mediana brazo | evaluado (n mín.) | informativo control (n, mediana) | informativo brazo (n, mediana) |
|---|---|---|---|---|---|---|---|
| total | 532 | 518 | 0,768 | 0,748 |  | 532, 0,770 | 518, 0,748 |
| estrato focal | 447 | 438 | 0,770 | 0,751 |  | 447, 0,768 | 438, 0,751 |
| estrato nevado | 85 | 80 | 0,716 | 0,652 |  | 85, 0,805 | 80, 0,652 |
| Chaiten | 17 | 17 | 1,296 | 1,493 | no | 17, 1,296 | 17, 1,493 |
| Isluga | 131 | 125 | 0,632 | 0,582 | sí | 131, 0,632 | 125, 0,582 |
| Lascar | 110 | 109 | 0,631 | 0,626 | sí | 110, 0,629 | 109, 0,626 |
| Lastarria | 76 | 74 | 0,965 | 1,012 | sí | 76, 0,960 | 74, 1,012 |
| NevadosDeChillan | 6 | 2 | 1,160 | 1,160 | no | 6, 1,208 | 2, 1,160 |
| PlanchonPeteroa | 44 | 44 | 0,956 | 0,997 | sí | 44, 0,956 | 44, 0,997 |
| PuyehueCordonCaulle | 86 | 86 | 1,021 | 1,029 | sí | 86, 1,021 | 86, 1,029 |
| Tupungatito | 51 | 50 | 0,556 | 0,494 | sí | 51, 0,562 | 50, 0,494 |
| Villarrica | 11 | 11 | 0,860 | 0,893 | no | 11, 0,860 | 11, 0,893 |

## Brazo _s142_ab_lit_con_compuerta

Cumple los tres criterios: **no**.

### Criterio 1: cero noches perdidas

Pérdidas (misma cota en el brazo): **25**; sin filtro en el brazo: 16; ganancias: 1 (sin filtro 0). Cumple: **no**.

Medido con las dos posiciones del record (decisión abierta; hoy decide **final_hotspot_si_test1**):

| posición | noches confirmadas | pérdidas | pérdidas sin filtro | ganancias | cumple | decide |
|---|---|---|---|---|---|---|
| centroide | 283 | 36 | 16 | 1 | no | no |
| final_hotspot_si_test1 | 272 | 25 | 16 | 1 | no | sí |

Por volcán, con el campo que decide:

| volcán | confirmadas | pérdidas | pérdidas sin filtro en el brazo | ganancias |
|---|---|---|---|---|
| Chaiten | 13 | 0 | 0 | 0 |
| Isluga | 73 | 6 | 5 | 0 |
| Lascar | 50 | 2 | 0 | 0 |
| Lastarria | 42 | 7 | 2 | 0 |
| NevadosDeChillan | 3 | 3 | 3 | 0 |
| PlanchonPeteroa | 24 | 3 | 3 | 0 |
| PuyehueCordonCaulle | 31 | 0 | 0 | 1 |
| Tupungatito | 27 | 3 | 2 | 0 |
| Villarrica | 9 | 1 | 1 | 0 |

Noches perdidas: Isluga 2026-06-16, Isluga 2026-06-30, Isluga 2026-07-01, Isluga 2026-07-16, Isluga 2026-07-22, Isluga 2026-08-19, Lascar 2026-06-13, Lascar 2026-06-25, Lastarria 2026-06-07, Lastarria 2026-06-14, Lastarria 2026-07-02, Lastarria 2026-07-06, Lastarria 2026-07-25, Lastarria 2026-08-02, Lastarria 2026-08-28, NevadosDeChillan 2026-06-16, NevadosDeChillan 2026-08-18, NevadosDeChillan 2026-08-20, PlanchonPeteroa 2026-06-22, PlanchonPeteroa 2026-06-26, PlanchonPeteroa 2026-08-09, Tupungatito 2026-06-03, Tupungatito 2026-07-07, Tupungatito 2026-08-01, Villarrica 2026-07-20.

Perdidas sin filtro en el brazo: Isluga 2026-06-30, Isluga 2026-07-01, Isluga 2026-07-16, Isluga 2026-07-22, Isluga 2026-08-19, Lastarria 2026-07-02, Lastarria 2026-08-28, NevadosDeChillan 2026-06-16, NevadosDeChillan 2026-08-18, NevadosDeChillan 2026-08-20, PlanchonPeteroa 2026-06-22, PlanchonPeteroa 2026-06-26, PlanchonPeteroa 2026-08-09, Tupungatito 2026-07-07, Tupungatito 2026-08-01, Villarrica 2026-07-20.

### Criterio 2: publicación en negativos limpios (brazo menos control)

Cumple: **sí**.

| ámbito | pasadas | noches | tasa control | tasa brazo | diferencia | IC 95 % | solo brazo | solo control | margen de signo |
|---|---|---|---|---|---|---|---|---|---|
| total | 1170 | 435 | 0,917 | 0,345 | -0,572 | [-0,601; -0,543] | 0 | 669 | 669 |
| estrato focal | 413 | 160 | 0,937 | 0,431 | -0,506 | [-0,552; -0,460] | 0 | 209 | 209 |
| estrato nevado | 757 | 275 | 0,906 | 0,299 | -0,608 | [-0,645; -0,571] | 0 | 460 | 460 |
| Chaiten | 220 | 77 | 0,932 | 0,400 | -0,532 | [-0,606; -0,460] | 0 | 117 | 117 |
| Isluga | 21 | 8 | 0,905 | 0,286 | -0,619 | [-0,800; -0,421] | 0 | 13 | 13 |
| Lascar | 50 | 22 | 0,820 | 0,140 | -0,680 | [-0,800; -0,548] | 0 | 34 | 34 |
| Lastarria | 52 | 24 | 0,962 | 0,269 | -0,692 | [-0,827; -0,543] | 0 | 36 | 36 |
| NevadosDeChillan | 197 | 73 | 0,883 | 0,213 | -0,670 | [-0,738; -0,600] | 0 | 132 | 132 |
| PlanchonPeteroa | 144 | 53 | 0,951 | 0,250 | -0,701 | [-0,779; -0,618] | 0 | 101 | 101 |
| PuyehueCordonCaulle | 146 | 53 | 0,959 | 0,788 | -0,171 | [-0,235; -0,111] | 0 | 25 | 25 |
| Tupungatito | 122 | 48 | 0,943 | 0,426 | -0,516 | [-0,607; -0,425] | 0 | 63 | 63 |
| Villarrica | 218 | 77 | 0,881 | 0,202 | -0,679 | [-0,741; -0,615] | 0 | 148 | 148 |

Acompañantes: artefacto control 0,000, brazo 0,000 (sube en el brazo: no); previa al display control 0,917, brazo 0,345.

### Criterio 3: magnitud del operador sobre VRP de MIROVA

Cumple: **no**. Volcanes que empeoran más de la tolerancia: Lastarria.

| ámbito | pos control | pares decisivos | mediana control | mediana brazo | evaluado (n mín.) | informativo control (n, mediana) | informativo brazo (n, mediana) |
|---|---|---|---|---|---|---|---|
| total | 532 | 450 | 0,750 | 0,880 |  | 532, 0,770 | 450, 0,880 |
| estrato focal | 447 | 386 | 0,750 | 0,847 |  | 447, 0,768 | 386, 0,847 |
| estrato nevado | 85 | 64 | 0,745 | 1,083 |  | 85, 0,805 | 64, 1,083 |
| Chaiten | 17 | 13 | 1,474 | 1,277 | no | 17, 1,296 | 13, 1,277 |
| Isluga | 131 | 106 | 0,614 | 0,859 | sí | 131, 0,632 | 106, 0,859 |
| Lascar | 110 | 104 | 0,629 | 0,740 | sí | 110, 0,629 | 104, 0,740 |
| Lastarria | 76 | 65 | 1,008 | 0,910 | sí | 76, 0,960 | 65, 0,910 |
| NevadosDeChillan | 6 | 2 | 1,160 | 1,425 | no | 6, 1,208 | 2, 1,425 |
| PlanchonPeteroa | 44 | 31 | 0,905 | 0,904 | sí | 44, 0,956 | 31, 0,904 |
| PuyehueCordonCaulle | 86 | 80 | 1,021 | 0,985 | sí | 86, 1,021 | 80, 0,985 |
| Tupungatito | 51 | 39 | 0,539 | 1,075 | sí | 51, 0,562 | 39, 1,075 |
| Villarrica | 11 | 10 | 0,877 | 0,877 | no | 11, 0,860 | 10, 0,877 |

## Brazo _s142_ab_lit_sp_suelto

Cumple los tres criterios: **no**.

### Criterio 1: cero noches perdidas

Pérdidas (misma cota en el brazo): **5**; sin filtro en el brazo: 0; ganancias: 3 (sin filtro 0). Cumple: **no**.

Medido con las dos posiciones del record (decisión abierta; hoy decide **final_hotspot_si_test1**):

| posición | noches confirmadas | pérdidas | pérdidas sin filtro | ganancias | cumple | decide |
|---|---|---|---|---|---|---|
| centroide | 283 | 15 | 0 | 5 | no | no |
| final_hotspot_si_test1 | 272 | 5 | 0 | 3 | no | sí |

Por volcán, con el campo que decide:

| volcán | confirmadas | pérdidas | pérdidas sin filtro en el brazo | ganancias |
|---|---|---|---|---|
| Chaiten | 13 | 0 | 0 | 1 |
| Isluga | 73 | 1 | 0 | 0 |
| Lascar | 50 | 1 | 0 | 1 |
| Lastarria | 42 | 3 | 0 | 1 |
| NevadosDeChillan | 3 | 0 | 0 | 0 |
| PlanchonPeteroa | 24 | 0 | 0 | 0 |
| PuyehueCordonCaulle | 31 | 0 | 0 | 0 |
| Tupungatito | 27 | 0 | 0 | 0 |
| Villarrica | 9 | 0 | 0 | 0 |

Noches perdidas: Isluga 2026-06-16, Lascar 2026-06-13, Lastarria 2026-06-07, Lastarria 2026-06-14, Lastarria 2026-07-25.

### Criterio 2: publicación en negativos limpios (brazo menos control)

Cumple: **sí**.

| ámbito | pasadas | noches | tasa control | tasa brazo | diferencia | IC 95 % | solo brazo | solo control | margen de signo |
|---|---|---|---|---|---|---|---|---|---|
| total | 1170 | 435 | 0,917 | 0,547 | -0,370 | [-0,397; -0,344] | 9 | 442 | 433 |
| estrato focal | 413 | 160 | 0,937 | 0,610 | -0,327 | [-0,368; -0,286] | 2 | 137 | 135 |
| estrato nevado | 757 | 275 | 0,906 | 0,513 | -0,394 | [-0,428; -0,360] | 7 | 305 | 298 |
| Chaiten | 220 | 77 | 0,932 | 0,627 | -0,305 | [-0,364; -0,248] | 0 | 67 | 67 |
| Isluga | 21 | 8 | 0,905 | 0,667 | -0,238 | [-0,417; -0,056] | 1 | 6 | 5 |
| Lascar | 50 | 22 | 0,820 | 0,480 | -0,340 | [-0,452; -0,239] | 1 | 18 | 17 |
| Lastarria | 52 | 24 | 0,962 | 0,519 | -0,442 | [-0,580; -0,308] | 0 | 23 | 23 |
| NevadosDeChillan | 197 | 73 | 0,883 | 0,421 | -0,462 | [-0,541; -0,380] | 6 | 97 | 91 |
| PlanchonPeteroa | 144 | 53 | 0,951 | 0,424 | -0,528 | [-0,609; -0,442] | 0 | 76 | 76 |
| PuyehueCordonCaulle | 146 | 53 | 0,959 | 0,863 | -0,096 | [-0,142; -0,053] | 0 | 14 | 14 |
| Tupungatito | 122 | 48 | 0,943 | 0,713 | -0,230 | [-0,300; -0,164] | 1 | 29 | 28 |
| Villarrica | 218 | 77 | 0,881 | 0,367 | -0,514 | [-0,574; -0,452] | 0 | 112 | 112 |

Acompañantes: artefacto control 0,000, brazo 0,000 (sube en el brazo: no); previa al display control 0,917, brazo 0,547.

### Criterio 3: magnitud del operador sobre VRP de MIROVA

Cumple: **sí**. Volcanes que empeoran más de la tolerancia: ninguno.

| ámbito | pos control | pares decisivos | mediana control | mediana brazo | evaluado (n mín.) | informativo control (n, mediana) | informativo brazo (n, mediana) |
|---|---|---|---|---|---|---|---|
| total | 532 | 530 | 0,773 | 0,945 |  | 532, 0,770 | 530, 0,945 |
| estrato focal | 447 | 445 | 0,768 | 0,899 |  | 447, 0,768 | 445, 0,899 |
| estrato nevado | 85 | 85 | 0,805 | 1,140 |  | 85, 0,805 | 85, 1,140 |
| Chaiten | 17 | 17 | 1,296 | 1,481 | no | 17, 1,296 | 17, 1,481 |
| Isluga | 131 | 131 | 0,632 | 0,881 | sí | 131, 0,632 | 131, 0,881 |
| Lascar | 110 | 110 | 0,629 | 0,740 | sí | 110, 0,629 | 110, 0,740 |
| Lastarria | 76 | 74 | 0,965 | 0,974 | sí | 76, 0,960 | 74, 0,974 |
| NevadosDeChillan | 6 | 6 | 1,208 | 1,321 | no | 6, 1,208 | 6, 1,321 |
| PlanchonPeteroa | 44 | 44 | 0,956 | 0,995 | sí | 44, 0,956 | 44, 0,995 |
| PuyehueCordonCaulle | 86 | 86 | 1,021 | 1,022 | sí | 86, 1,021 | 86, 1,022 |
| Tupungatito | 51 | 51 | 0,562 | 1,113 | sí | 51, 0,562 | 51, 1,113 |
| Villarrica | 11 | 11 | 0,860 | 0,893 | no | 11, 0,860 | 11, 0,893 |

## Brazo _s142_ab_lit_keep_peak

Cumple los tres criterios: **no**.

### Criterio 1: cero noches perdidas

Pérdidas (misma cota en el brazo): **1**; sin filtro en el brazo: 0; ganancias: 0 (sin filtro 0). Cumple: **no**.

Medido con las dos posiciones del record (decisión abierta; hoy decide **final_hotspot_si_test1**):

| posición | noches confirmadas | pérdidas | pérdidas sin filtro | ganancias | cumple | decide |
|---|---|---|---|---|---|---|
| centroide | 283 | 1 | 0 | 0 | no | no |
| final_hotspot_si_test1 | 272 | 1 | 0 | 0 | no | sí |

Por volcán, con el campo que decide:

| volcán | confirmadas | pérdidas | pérdidas sin filtro en el brazo | ganancias |
|---|---|---|---|---|
| Chaiten | 13 | 1 | 0 | 0 |
| Isluga | 73 | 0 | 0 | 0 |
| Lascar | 50 | 0 | 0 | 0 |
| Lastarria | 42 | 0 | 0 | 0 |
| NevadosDeChillan | 3 | 0 | 0 | 0 |
| PlanchonPeteroa | 24 | 0 | 0 | 0 |
| PuyehueCordonCaulle | 31 | 0 | 0 | 0 |
| Tupungatito | 27 | 0 | 0 | 0 |
| Villarrica | 9 | 0 | 0 | 0 |

Noches perdidas: Chaiten 2026-06-16.

### Criterio 2: publicación en negativos limpios (brazo menos control)

Cumple: **no**.

| ámbito | pasadas | noches | tasa control | tasa brazo | diferencia | IC 95 % | solo brazo | solo control | margen de signo |
|---|---|---|---|---|---|---|---|---|---|
| total | 1170 | 435 | 0,917 | 0,920 | 0,003 | [-0,003; 0,009] | 9 | 6 | 3 |
| estrato focal | 413 | 160 | 0,937 | 0,937 | 0,000 | [-0,010; 0,010] | 2 | 2 | 0 |
| estrato nevado | 757 | 275 | 0,906 | 0,910 | 0,004 | [-0,004; 0,013] | 7 | 4 | 3 |
| Chaiten | 220 | 77 | 0,932 | 0,927 | -0,005 | [-0,014; 0,000] | 0 | 1 | 1 |
| Isluga | 21 | 8 | 0,905 | 0,952 | 0,048 | [0,000; 0,143] | 1 | 0 | 1 |
| Lascar | 50 | 22 | 0,820 | 0,820 | 0,000 | [-0,058; 0,058] | 1 | 1 | 0 |
| Lastarria | 52 | 24 | 0,962 | 0,962 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| NevadosDeChillan | 197 | 73 | 0,883 | 0,909 | 0,025 | [0,000; 0,057] | 6 | 1 | 5 |
| PlanchonPeteroa | 144 | 53 | 0,951 | 0,944 | -0,007 | [-0,022; 0,000] | 0 | 1 | 1 |
| PuyehueCordonCaulle | 146 | 53 | 0,959 | 0,959 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Tupungatito | 122 | 48 | 0,943 | 0,943 | 0,000 | [0,000; 0,000] | 1 | 1 | 0 |
| Villarrica | 218 | 77 | 0,881 | 0,876 | -0,005 | [-0,014; 0,000] | 0 | 1 | 1 |

Acompañantes: artefacto control 0,000, brazo 0,000 (sube en el brazo: no); previa al display control 0,917, brazo 0,920.

### Criterio 3: magnitud del operador sobre VRP de MIROVA

Cumple: **sí**. Volcanes que empeoran más de la tolerancia: ninguno.

| ámbito | pos control | pares decisivos | mediana control | mediana brazo | evaluado (n mín.) | informativo control (n, mediana) | informativo brazo (n, mediana) |
|---|---|---|---|---|---|---|---|
| total | 532 | 532 | 0,770 | 0,914 |  | 532, 0,770 | 532, 0,914 |
| estrato focal | 447 | 447 | 0,768 | 0,872 |  | 447, 0,768 | 447, 0,872 |
| estrato nevado | 85 | 85 | 0,805 | 1,113 |  | 85, 0,805 | 85, 1,113 |
| Chaiten | 17 | 17 | 1,296 | 1,277 | no | 17, 1,296 | 17, 1,277 |
| Isluga | 131 | 131 | 0,632 | 0,868 | sí | 131, 0,632 | 131, 0,868 |
| Lascar | 110 | 110 | 0,629 | 0,740 | sí | 110, 0,629 | 110, 0,740 |
| Lastarria | 76 | 76 | 0,960 | 0,922 | sí | 76, 0,960 | 76, 0,922 |
| NevadosDeChillan | 6 | 6 | 1,208 | 1,321 | no | 6, 1,208 | 6, 1,321 |
| PlanchonPeteroa | 44 | 44 | 0,956 | 0,936 | sí | 44, 0,956 | 44, 0,936 |
| PuyehueCordonCaulle | 86 | 86 | 1,021 | 1,022 | sí | 86, 1,021 | 86, 1,022 |
| Tupungatito | 51 | 51 | 0,562 | 1,108 | sí | 51, 0,562 | 51, 1,108 |
| Villarrica | 11 | 11 | 0,860 | 0,893 | no | 11, 0,860 | 11, 0,893 |

## Seguimiento de noches puntuales

Celda: publica con cota / publica sin filtro.

| volcán | fecha | _s142_ab_control | _s142_ab_literal | _s142_ab_lit_sin_fondo | _s142_ab_lit_con_compuerta | _s142_ab_lit_sp_suelto | _s142_ab_lit_keep_peak |
|---|---|---|---|---|---|---|---|
| Isluga | 2026-07-01 | sí / sí | sí / sí | sí / sí | no / no | sí / sí | sí / sí |
| Isluga | 2026-07-16 | sí / sí | sí / sí | sí / sí | no / no | sí / sí | sí / sí |
| Isluga | 2026-08-19 | sí / sí | sí / sí | sí / sí | no / no | sí / sí | sí / sí |
| Lastarria | 2026-07-02 | sí / sí | sí / sí | sí / sí | no / no | sí / sí | sí / sí |
| Lastarria | 2026-08-28 | sí / sí | sí / sí | sí / sí | no / no | sí / sí | sí / sí |
| PlanchonPeteroa | 2026-06-22 | sí / sí | sí / sí | sí / sí | no / no | sí / sí | sí / sí |
| PlanchonPeteroa | 2026-06-26 | sí / sí | sí / sí | sí / sí | no / no | sí / sí | sí / sí |
| PlanchonPeteroa | 2026-07-24 | no / sí | no / sí | no / sí | no / no | no / sí | no / sí |
| PlanchonPeteroa | 2026-08-09 | sí / sí | sí / sí | sí / sí | no / no | sí / sí | sí / sí |
| PlanchonPeteroa | 2026-08-24 | no / sí | no / sí | no / sí | no / no | no / sí | no / sí |
| Tupungatito | 2026-07-07 | sí / sí | sí / sí | sí / sí | no / no | sí / sí | sí / sí |
| Tupungatito | 2026-08-01 | sí / sí | sí / sí | sí / sí | no / no | sí / sí | sí / sí |

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
