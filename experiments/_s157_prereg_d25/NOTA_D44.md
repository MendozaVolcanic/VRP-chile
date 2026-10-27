# D-44: lectura de la cuarta adenda y controles antes del tag de lectura de D25

**Decidida por Nicolás el 2026-10-22**, antes del tag de lectura y sin haber abierto V1, V2a, V2b ni el brazo del 17
al 19 de octubre. Respuesta textual, registrada por la sesión dueña del loop: «Sí a D-44: un PIERDE calibrado manda
(NO CUMPLE), acepto que P2 no decida con 4 noches o menos, y corre antes del tag los placebos (a), (b) y simétrico
sobre producción, con verificador.»

1. **`ADENDA_CALIBRACION_P2.md` §2.5 se lee así**: si P2 queda INDECIDIBLE en un sensor y da PIERDE calibrado en el
   otro, la ventana da **NO CUMPLE** (el PIERDE se mira antes que el INDECIDIBLE en `global_ventana`, como manda
   PREREGISTRO §8 d y la H2 de ADENDA_CALIBRACION.md §4). Es lo que hace el código desde `31bb1c371`. Origen de la
   pregunta: verificador `experiments/_s159/instrumentos/verificador_d42/INFORME.md`, V42-03.
2. **Se acepta que P2 no decida con 4 noches discordantes o menos**: con 2^4 = 16 combinaciones de signo, el sorteo
   no puede bajar los falsos de 5 % y la calibración deja INDECIDIBLE. No es un defecto a corregir.
3. **Antes del tag** se corren, sobre brazos armados desde producción (nunca desde artefactos del A/B), los placebos
   que sí pueden fallar (verificador D-42 vuelta 2, V42-10): (a) apagar sólo publicaciones de K en negativos limpios
   (P2 calibrada tiene que dar GANA: control de poder); (b) apagar sólo alertas bajo 1 MW (tiene que dar PIERDE); (c)
   simétrico, apagar y encender la misma fracción en la misma semilla (efecto esperado 0: tasa de falsos de P2
   calibrada sobre datos reales). Con verificador limpio.
