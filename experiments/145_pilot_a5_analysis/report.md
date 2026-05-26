# F31 A5 piloto — análisis post-corrida

Generado: 2026-05-24T18:24:01.989571Z

Cruza `vrptir_aveni_mw` por volcán contra ground truth físico publicado.
Ground truth ESTRICTO: Aguilera 2021 (PP), bandas literatura para los demás.

## Resumen por volcán

| Volcán | N records | N válidos | Mediana MW | Banda GT | Verdict |
|---|---|---|---|---|---|
| PlanchonPeteroa | 0 | 0 | — |  | sin_data |
| Lastarria | 0 | 0 | — |  | sin_data |
| Copahue | 0 | 0 | — |  | sin_data |

## Detalle por volcán

### PlanchonPeteroa

**Estado**: sin data válida.

Ningún record en la ventana tiene vrptir_aveni_mw > 0 + n_pixels > 0. Posibles causas: (a) ENABLE_VRPTIR_AVENI no estaba activo, (b) no hubo pixels en rango 300-600K, (c) reproc no se ejecutó. Verificar pipeline/profiles/experimental_lowT.yaml.

### Lastarria

**Estado**: sin data válida.

Ningún record en la ventana tiene vrptir_aveni_mw > 0 + n_pixels > 0. Posibles causas: (a) ENABLE_VRPTIR_AVENI no estaba activo, (b) no hubo pixels en rango 300-600K, (c) reproc no se ejecutó. Verificar pipeline/profiles/experimental_lowT.yaml.

### Copahue

**Estado**: sin data válida.

Ningún record en la ventana tiene vrptir_aveni_mw > 0 + n_pixels > 0. Posibles causas: (a) ENABLE_VRPTIR_AVENI no estaba activo, (b) no hubo pixels en rango 300-600K, (c) reproc no se ejecutó. Verificar pipeline/profiles/experimental_lowT.yaml.


## Recomendación final

PP no tiene data válida — no se puede tomar decisión sobre flip operacional. Verificar que el piloto haya corrido con `enable_vrptir_aveni: true`.

