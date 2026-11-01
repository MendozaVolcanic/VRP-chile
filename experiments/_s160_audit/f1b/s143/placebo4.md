# Evaluación del A/B: _pl_id, _pl_x1.10, _pl_x1.2, _pl_desplazada contra _s142_ab_control

> Generado por `experiments/_s143_evaluador/evaluar.py` el 2026-10-22T04:13:04+00:00. Ventana 2026-06-01 a 2026-08-31. Todos los números salen del JSON de resultados.

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

n = 1184; publica 0,915; artefacto 0,000; previa al display 0,915.

## Brazo _pl_id

Cumple los tres criterios: **no**.

### Criterio 1: cero noches perdidas

Pérdidas (misma cota en el brazo): **0**; sin filtro en el brazo: 0; ganancias: 0 (sin filtro 0). Cumple: **sí**.

Medido con las dos posiciones del record (decisión abierta; hoy decide **final_hotspot_si_test1**):

| posición | noches confirmadas | pérdidas | pérdidas sin filtro | ganancias | cumple | decide |
|---|---|---|---|---|---|---|
| centroide | 283 | 0 | 0 | 0 | sí | no |
| final_hotspot_si_test1 | 272 | 0 | 0 | 0 | sí | sí |

Por volcán, con el campo que decide:

| volcán | confirmadas | pérdidas | pérdidas sin filtro en el brazo | ganancias |
|---|---|---|---|---|
| Chaiten | 13 | 0 | 0 | 0 |
| Isluga | 73 | 0 | 0 | 0 |
| Lascar | 50 | 0 | 0 | 0 |
| Lastarria | 42 | 0 | 0 | 0 |
| NevadosDeChillan | 3 | 0 | 0 | 0 |
| PlanchonPeteroa | 24 | 0 | 0 | 0 |
| PuyehueCordonCaulle | 31 | 0 | 0 | 0 |
| Tupungatito | 27 | 0 | 0 | 0 |
| Villarrica | 9 | 0 | 0 | 0 |

### Criterio 2: publicación en negativos limpios (brazo menos control)

Cumple: **no**.

| ámbito | pasadas | noches | tasa control | tasa brazo | diferencia | IC 95 % | solo brazo | solo control | margen de signo |
|---|---|---|---|---|---|---|---|---|---|
| total | 1184 | 436 | 0,915 | 0,915 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| estrato focal | 420 | 161 | 0,936 | 0,936 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| estrato nevado | 764 | 275 | 0,903 | 0,903 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Chaiten | 226 | 77 | 0,920 | 0,920 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Isluga | 21 | 8 | 0,905 | 0,905 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Lascar | 51 | 23 | 0,824 | 0,824 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Lastarria | 53 | 24 | 0,962 | 0,962 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| NevadosDeChillan | 197 | 73 | 0,883 | 0,883 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| PlanchonPeteroa | 144 | 53 | 0,951 | 0,951 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| PuyehueCordonCaulle | 151 | 53 | 0,954 | 0,954 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Tupungatito | 123 | 48 | 0,943 | 0,943 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Villarrica | 218 | 77 | 0,881 | 0,881 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |

Acompañantes: artefacto control 0,000, brazo 0,000 (sube en el brazo: no); previa al display control 0,915, brazo 0,915.

### Criterio 3: magnitud del operador sobre VRP de MIROVA

Cumple: **sí**. Volcanes que empeoran más de la tolerancia: ninguno.

| ámbito | pos control | pares decisivos | mediana control | mediana brazo | evaluado (n mín.) | informativo control (n, mediana) | informativo brazo (n, mediana) |
|---|---|---|---|---|---|---|---|
| total | 532 | 532 | 0,770 | 0,770 |  | 532, 0,770 | 532, 0,770 |
| estrato focal | 447 | 447 | 0,768 | 0,768 |  | 447, 0,768 | 447, 0,768 |
| estrato nevado | 85 | 85 | 0,805 | 0,805 |  | 85, 0,805 | 85, 0,805 |
| Chaiten | 17 | 17 | 1,296 | 1,296 | no | 17, 1,296 | 17, 1,296 |
| Isluga | 131 | 131 | 0,632 | 0,632 | sí | 131, 0,632 | 131, 0,632 |
| Lascar | 110 | 110 | 0,629 | 0,629 | sí | 110, 0,629 | 110, 0,629 |
| Lastarria | 76 | 76 | 0,960 | 0,960 | sí | 76, 0,960 | 76, 0,960 |
| NevadosDeChillan | 6 | 6 | 1,208 | 1,208 | no | 6, 1,208 | 6, 1,208 |
| PlanchonPeteroa | 44 | 44 | 0,956 | 0,956 | sí | 44, 0,956 | 44, 0,956 |
| PuyehueCordonCaulle | 86 | 86 | 1,021 | 1,021 | sí | 86, 1,021 | 86, 1,021 |
| Tupungatito | 51 | 51 | 0,562 | 0,562 | sí | 51, 0,562 | 51, 0,562 |
| Villarrica | 11 | 11 | 0,860 | 0,860 | no | 11, 0,860 | 11, 0,860 |

## Brazo _pl_x1.10

Cumple los tres criterios: **no**.

### Criterio 1: cero noches perdidas

Pérdidas (misma cota en el brazo): **0**; sin filtro en el brazo: 0; ganancias: 0 (sin filtro 0). Cumple: **sí**.

Medido con las dos posiciones del record (decisión abierta; hoy decide **final_hotspot_si_test1**):

| posición | noches confirmadas | pérdidas | pérdidas sin filtro | ganancias | cumple | decide |
|---|---|---|---|---|---|---|
| centroide | 283 | 0 | 0 | 0 | sí | no |
| final_hotspot_si_test1 | 272 | 0 | 0 | 0 | sí | sí |

Por volcán, con el campo que decide:

| volcán | confirmadas | pérdidas | pérdidas sin filtro en el brazo | ganancias |
|---|---|---|---|---|
| Chaiten | 13 | 0 | 0 | 0 |
| Isluga | 73 | 0 | 0 | 0 |
| Lascar | 50 | 0 | 0 | 0 |
| Lastarria | 42 | 0 | 0 | 0 |
| NevadosDeChillan | 3 | 0 | 0 | 0 |
| PlanchonPeteroa | 24 | 0 | 0 | 0 |
| PuyehueCordonCaulle | 31 | 0 | 0 | 0 |
| Tupungatito | 27 | 0 | 0 | 0 |
| Villarrica | 9 | 0 | 0 | 0 |

### Criterio 2: publicación en negativos limpios (brazo menos control)

Cumple: **no**.

| ámbito | pasadas | noches | tasa control | tasa brazo | diferencia | IC 95 % | solo brazo | solo control | margen de signo |
|---|---|---|---|---|---|---|---|---|---|
| total | 1184 | 436 | 0,915 | 0,915 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| estrato focal | 420 | 161 | 0,936 | 0,936 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| estrato nevado | 764 | 275 | 0,903 | 0,903 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Chaiten | 226 | 77 | 0,920 | 0,920 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Isluga | 21 | 8 | 0,905 | 0,905 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Lascar | 51 | 23 | 0,824 | 0,824 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Lastarria | 53 | 24 | 0,962 | 0,962 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| NevadosDeChillan | 197 | 73 | 0,883 | 0,883 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| PlanchonPeteroa | 144 | 53 | 0,951 | 0,951 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| PuyehueCordonCaulle | 151 | 53 | 0,954 | 0,954 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Tupungatito | 123 | 48 | 0,943 | 0,943 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Villarrica | 218 | 77 | 0,881 | 0,881 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |

Acompañantes: artefacto control 0,000, brazo 0,000 (sube en el brazo: no); previa al display control 0,915, brazo 0,915.

### Criterio 3: magnitud del operador sobre VRP de MIROVA

Cumple: **no**. Volcanes que empeoran más de la tolerancia: PuyehueCordonCaulle.

| ámbito | pos control | pares decisivos | mediana control | mediana brazo | evaluado (n mín.) | informativo control (n, mediana) | informativo brazo (n, mediana) |
|---|---|---|---|---|---|---|---|
| total | 532 | 532 | 0,770 | 0,847 |  | 532, 0,770 | 532, 0,847 |
| estrato focal | 447 | 447 | 0,768 | 0,844 |  | 447, 0,768 | 447, 0,844 |
| estrato nevado | 85 | 85 | 0,805 | 0,885 |  | 85, 0,805 | 85, 0,885 |
| Chaiten | 17 | 17 | 1,296 | 1,426 | no | 17, 1,296 | 17, 1,426 |
| Isluga | 131 | 131 | 0,632 | 0,695 | sí | 131, 0,632 | 131, 0,695 |
| Lascar | 110 | 110 | 0,629 | 0,692 | sí | 110, 0,629 | 110, 0,692 |
| Lastarria | 76 | 76 | 0,960 | 1,056 | sí | 76, 0,960 | 76, 1,056 |
| NevadosDeChillan | 6 | 6 | 1,208 | 1,329 | no | 6, 1,208 | 6, 1,329 |
| PlanchonPeteroa | 44 | 44 | 0,956 | 1,051 | sí | 44, 0,956 | 44, 1,051 |
| PuyehueCordonCaulle | 86 | 86 | 1,021 | 1,123 | sí | 86, 1,021 | 86, 1,123 |
| Tupungatito | 51 | 51 | 0,562 | 0,618 | sí | 51, 0,562 | 51, 0,618 |
| Villarrica | 11 | 11 | 0,860 | 0,946 | no | 11, 0,860 | 11, 0,946 |

## Brazo _pl_x1.2

Cumple los tres criterios: **no**.

### Criterio 1: cero noches perdidas

Pérdidas (misma cota en el brazo): **0**; sin filtro en el brazo: 0; ganancias: 0 (sin filtro 0). Cumple: **sí**.

Medido con las dos posiciones del record (decisión abierta; hoy decide **final_hotspot_si_test1**):

| posición | noches confirmadas | pérdidas | pérdidas sin filtro | ganancias | cumple | decide |
|---|---|---|---|---|---|---|
| centroide | 283 | 0 | 0 | 0 | sí | no |
| final_hotspot_si_test1 | 272 | 0 | 0 | 0 | sí | sí |

Por volcán, con el campo que decide:

| volcán | confirmadas | pérdidas | pérdidas sin filtro en el brazo | ganancias |
|---|---|---|---|---|
| Chaiten | 13 | 0 | 0 | 0 |
| Isluga | 73 | 0 | 0 | 0 |
| Lascar | 50 | 0 | 0 | 0 |
| Lastarria | 42 | 0 | 0 | 0 |
| NevadosDeChillan | 3 | 0 | 0 | 0 |
| PlanchonPeteroa | 24 | 0 | 0 | 0 |
| PuyehueCordonCaulle | 31 | 0 | 0 | 0 |
| Tupungatito | 27 | 0 | 0 | 0 |
| Villarrica | 9 | 0 | 0 | 0 |

### Criterio 2: publicación en negativos limpios (brazo menos control)

Cumple: **no**.

| ámbito | pasadas | noches | tasa control | tasa brazo | diferencia | IC 95 % | solo brazo | solo control | margen de signo |
|---|---|---|---|---|---|---|---|---|---|
| total | 1184 | 436 | 0,915 | 0,915 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| estrato focal | 420 | 161 | 0,936 | 0,936 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| estrato nevado | 764 | 275 | 0,903 | 0,903 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Chaiten | 226 | 77 | 0,920 | 0,920 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Isluga | 21 | 8 | 0,905 | 0,905 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Lascar | 51 | 23 | 0,824 | 0,824 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Lastarria | 53 | 24 | 0,962 | 0,962 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| NevadosDeChillan | 197 | 73 | 0,883 | 0,883 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| PlanchonPeteroa | 144 | 53 | 0,951 | 0,951 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| PuyehueCordonCaulle | 151 | 53 | 0,954 | 0,954 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Tupungatito | 123 | 48 | 0,943 | 0,943 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Villarrica | 218 | 77 | 0,881 | 0,881 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |

Acompañantes: artefacto control 0,000, brazo 0,000 (sube en el brazo: no); previa al display control 0,915, brazo 0,915.

### Criterio 3: magnitud del operador sobre VRP de MIROVA

Cumple: **no**. Volcanes que empeoran más de la tolerancia: Lastarria, PlanchonPeteroa, PuyehueCordonCaulle.

| ámbito | pos control | pares decisivos | mediana control | mediana brazo | evaluado (n mín.) | informativo control (n, mediana) | informativo brazo (n, mediana) |
|---|---|---|---|---|---|---|---|
| total | 532 | 532 | 0,770 | 0,924 |  | 532, 0,770 | 532, 0,924 |
| estrato focal | 447 | 447 | 0,768 | 0,921 |  | 447, 0,768 | 447, 0,921 |
| estrato nevado | 85 | 85 | 0,805 | 0,966 |  | 85, 0,805 | 85, 0,966 |
| Chaiten | 17 | 17 | 1,296 | 1,555 | no | 17, 1,296 | 17, 1,555 |
| Isluga | 131 | 131 | 0,632 | 0,758 | sí | 131, 0,632 | 131, 0,758 |
| Lascar | 110 | 110 | 0,629 | 0,754 | sí | 110, 0,629 | 110, 0,754 |
| Lastarria | 76 | 76 | 0,960 | 1,152 | sí | 76, 0,960 | 76, 1,152 |
| NevadosDeChillan | 6 | 6 | 1,208 | 1,450 | no | 6, 1,208 | 6, 1,450 |
| PlanchonPeteroa | 44 | 44 | 0,956 | 1,147 | sí | 44, 0,956 | 44, 1,147 |
| PuyehueCordonCaulle | 86 | 86 | 1,021 | 1,225 | sí | 86, 1,021 | 86, 1,225 |
| Tupungatito | 51 | 51 | 0,562 | 0,674 | sí | 51, 0,562 | 51, 0,674 |
| Villarrica | 11 | 11 | 0,860 | 1,032 | no | 11, 0,860 | 11, 1,032 |

## Brazo _pl_desplazada

Cumple los tres criterios: **no**.

### Criterio 1: cero noches perdidas

Pérdidas (misma cota en el brazo): **0**; sin filtro en el brazo: 0; ganancias: 0 (sin filtro 0). Cumple: **sí**.

Medido con las dos posiciones del record (decisión abierta; hoy decide **final_hotspot_si_test1**):

| posición | noches confirmadas | pérdidas | pérdidas sin filtro | ganancias | cumple | decide |
|---|---|---|---|---|---|---|
| centroide | 283 | 0 | 0 | 0 | sí | no |
| final_hotspot_si_test1 | 272 | 0 | 0 | 0 | sí | sí |

Por volcán, con el campo que decide:

| volcán | confirmadas | pérdidas | pérdidas sin filtro en el brazo | ganancias |
|---|---|---|---|---|
| Chaiten | 13 | 0 | 0 | 0 |
| Isluga | 73 | 0 | 0 | 0 |
| Lascar | 50 | 0 | 0 | 0 |
| Lastarria | 42 | 0 | 0 | 0 |
| NevadosDeChillan | 3 | 0 | 0 | 0 |
| PlanchonPeteroa | 24 | 0 | 0 | 0 |
| PuyehueCordonCaulle | 31 | 0 | 0 | 0 |
| Tupungatito | 27 | 0 | 0 | 0 |
| Villarrica | 9 | 0 | 0 | 0 |

### Criterio 2: publicación en negativos limpios (brazo menos control)

Cumple: **no**.

| ámbito | pasadas | noches | tasa control | tasa brazo | diferencia | IC 95 % | solo brazo | solo control | margen de signo |
|---|---|---|---|---|---|---|---|---|---|
| total | 1184 | 436 | 0,915 | 0,917 | 0,003 | [-0,002; 0,008] | 8 | 5 | 3 |
| estrato focal | 420 | 161 | 0,936 | 0,938 | 0,002 | [0,000; 0,007] | 2 | 1 | 1 |
| estrato nevado | 764 | 275 | 0,903 | 0,906 | 0,003 | [-0,004; 0,011] | 6 | 4 | 2 |
| Chaiten | 226 | 77 | 0,920 | 0,920 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Isluga | 21 | 8 | 0,905 | 0,905 | 0,000 | [0,000; 0,000] | 1 | 1 | 0 |
| Lascar | 51 | 23 | 0,824 | 0,824 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| Lastarria | 53 | 24 | 0,962 | 0,962 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| NevadosDeChillan | 197 | 73 | 0,883 | 0,898 | 0,015 | [-0,010; 0,043] | 5 | 2 | 3 |
| PlanchonPeteroa | 144 | 53 | 0,951 | 0,951 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |
| PuyehueCordonCaulle | 151 | 53 | 0,954 | 0,960 | 0,007 | [0,000; 0,024] | 1 | 0 | 1 |
| Tupungatito | 123 | 48 | 0,943 | 0,935 | -0,008 | [-0,025; 0,000] | 1 | 2 | 1 |
| Villarrica | 218 | 77 | 0,881 | 0,881 | 0,000 | [0,000; 0,000] | 0 | 0 | 0 |

Acompañantes: artefacto control 0,000, brazo 0,000 (sube en el brazo: no); previa al display control 0,915, brazo 0,917.

### Criterio 3: magnitud del operador sobre VRP de MIROVA

Cumple: **no**. Volcanes que empeoran más de la tolerancia: Isluga, Lascar, Lastarria, PlanchonPeteroa, PuyehueCordonCaulle, Tupungatito.

| ámbito | pos control | pares decisivos | mediana control | mediana brazo | evaluado (n mín.) | informativo control (n, mediana) | informativo brazo (n, mediana) |
|---|---|---|---|---|---|---|---|
| total | 532 | 531 | 0,772 | 0,520 |  | 532, 0,770 | 531, 0,520 |
| estrato focal | 447 | 446 | 0,768 | 0,528 |  | 447, 0,768 | 446, 0,528 |
| estrato nevado | 85 | 85 | 0,805 | 0,460 |  | 85, 0,805 | 85, 0,460 |
| Chaiten | 17 | 17 | 1,296 | 1,054 | no | 17, 1,296 | 17, 1,054 |
| Isluga | 131 | 130 | 0,634 | 0,435 | sí | 131, 0,632 | 130, 0,435 |
| Lascar | 110 | 110 | 0,629 | 0,516 | sí | 110, 0,629 | 110, 0,516 |
| Lastarria | 76 | 76 | 0,960 | 0,738 | sí | 76, 0,960 | 76, 0,738 |
| NevadosDeChillan | 6 | 6 | 1,208 | 0,647 | no | 6, 1,208 | 6, 0,647 |
| PlanchonPeteroa | 44 | 44 | 0,956 | 0,535 | sí | 44, 0,956 | 44, 0,535 |
| PuyehueCordonCaulle | 86 | 86 | 1,021 | 0,634 | sí | 86, 1,021 | 86, 0,634 |
| Tupungatito | 51 | 51 | 0,562 | 0,281 | sí | 51, 0,562 | 51, 0,281 |
| Villarrica | 11 | 11 | 0,860 | 0,147 | no | 11, 0,860 | 11, 0,147 |

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
