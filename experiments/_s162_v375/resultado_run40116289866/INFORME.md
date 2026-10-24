# V375-B y V375-C (S162): resultado del lote, run 40116289866

2026-10-24. Pre-registros sellados `PREREGISTRO_B.md` y `PREREGISTRO_C.md` (tag `s162-v375-bc-sello`, D-48), adendas 1 y
2 sin cambio de reglas. Disparo `798cac8ea` (tag `s162-v375-disparo-lote`): árbol de `ca034d66e` (`pipeline/` idéntico a
533398f8f, el código que escribió los records del marco) más `experiments/_s162_v375/`. Artefactos en
`C:\vrp-trabajo\temporales\s162_v375\run_40116289866\`. Lectura: `evaluar_salida.txt` y `evaluar.json` (commit
`20719dc8f`). Verificador con contexto limpio (Sonnet): `verificador/INFORME.md`, **CONFIRMADO; ningún hallazgo cambia
un veredicto**.

## En una pantalla

1. **El instrumento está limpio.** 709 de 709 pasadas con resultado: 698 ok y 11 no observadas (el volcán cae fuera
   o en el borde del gránulo; el probe bajó el mismo gránulo que producción). El recálculo sin red da igual que el runner
   en 7.427 de 7.427 pares pasada x brazo. K re-corrido es igual a lo publicado en 847 de 847. La cobertura del marco
   contra MIROVA (evaluador común de #904) da 0 alertas sin record. Nulo, NUNCA y PLACEBO, en verde. El verificador
   reproduce todas las cifras con una implementación propia.
2. **V375-B: NO RESUELTO por la regla, al filo y del lado del silencio.** En las noches en que MIROVA y producción
   callan, el port publica **4 de 389** en el lote nuevo y 4 de 434 en la unión (0,95 % [0,37; 2,38]). La cota de 8,5 %
   que dejó S159 baja a 2,4 %. En todos los negativos limpios, la unión queda bajo producción (2,0 % [1,5; 3,4] contra
   3,85 %). Pero el lote nuevo solo, que es el que decide, llega a 4,10 % y cruza la vara. ENCIENDE DE MÁS queda
   descartado: el piso del intervalo es 1,2 a 1,5 %.
3. **V375-C: la caja de cumbre va centrada en el cráter, no en el centro del TIF de MIROVA.** El brazo global es **C13**
   (13 x 13 celdas de 375 m alrededor del cráter de `volcanoes.yaml`), igual en el lote y en la unión. Con él, el recall
   de las alertas bajo 1 MW sube de 0,69 (M14, la caja de S159) a **0,95 [0,92; 0,98]**, a la par de producción (0,957 en
   el marco entero). Le gana a producción en la suma de errores bajo 1 MW (P2 GANA). Los negativos no suben (2,03 %
   contra 2,01 % de M14) y la magnitud queda en 0,999 de MIROVA (n 265).
4. **La ganancia de C13 está en Cordón Caulle y Tupungatito.** Son los dos volcanes donde el cráter está lejos del
   centro del TIF (7,6 y 4,8 km). Aportan −145,5 y −112,3 de un neto de −253,8; en los otros nueve C13 y M14 son casi
   la misma caja (neto +3,9 en 4 bloques). El compuesto por volcán elegido en abril a junio (C13 en esos dos, M14 en el
   resto) valida en junio a octubre, en el lote y en la unión. C13 no se distingue de C14 ni de SENS_PT: el empate lo
   decide la regla de la caja más chica.
5. **V375-D no hace falta por B ni por C.** Queda un riesgo para V375-E: los diez brazos pierden las mismas 6
   protegidas, todas de Suomi NPP, sólo OCR y del lote de S159, y producción publica 3 de ellas. Ninguna es de la tabla.
   Es el patrón que A119 describe (la fila OCR de Suomi NPP antes del 2026-10-09 puede traer la distancia de otra
   pasada), pero no está demostrado: lo decide la etiqueta de protegida de cráter de V375-A.

## Lo que el verificador agregó (y cómo queda)

| reparo | gravedad | cómo queda |
|---|---|---|
| B en el lote solo depende de tratar neg_pub como muestra (113 de 133); como censo, la cota baja a 3,80 % y B se resolvería | 2 | **No se cambia la regla después de ver el número.** Dentro del lote solo, neg_pub sí es una muestra (las otras 20 son de S159). Es una sensibilidad para Nicolás: con la regla sellada B queda NO RESUELTO; con neg_pub contado como censo, SILENCIO ACOTADO. Las dos lecturas descartan ENCIENDE DE MÁS. |
| «4 de 434» mezcla unión y lote | 2 | Corregido arriba: 4 de 389 en el lote, 4 de 434 en la unión. |
| El ΔE de M14 contra K se rotula «ENCIENDE DE MAS» en el lote, pero sale de alertas débiles perdidas, no de negativos encendidos | 2 | El rótulo viene de la regla de S159 (IC entero sobre 0). Se lee como «M14 empeora contra K». No decide nada: M14 es la referencia, no un candidato. |
| La validación en O es poco independiente: la ganancia es geométrica y sale igual en T, O1 y O2 | 2 | Cierto, y es lo esperable: la caja no cambia con la estación. Valida también por separado en Cordón Caulle (16 bloques) y Tupungatito (13). |
| V375-D no hace falta sólo porque las 6 protegidas perdidas son sólo OCR | 3 | Declarado en el punto 5 y en `PREREGISTRO_E.md` §5.4 (riesgo para el veto de adopción). |
| Una línea del texto sellado de `PREREGISTRO_B.md` («Qué lote decide») se editó después del sello para citar la adenda 1 de C | 1 | Declarado en la adenda 1 de B. |
| El control 2.1 compara runner y evaluador con el mismo `brazos.py`: prueba la grilla guardada, no la geometría | 1 | El verificador comprobó la geometría de C13, C21, M13 y M21 con su propia proyección. |
| `PREREGISTRO_C.md` §3 decía «14 alertas sin record» y la cobertura medida da 0 | 1 | SOSPECHA: el 14 salió de la ventana total del marco de S159, que empieza el 2026-03-01 (VIIRS se mide desde el 04-01) e incluye los días excluidos. No cambia nada: en la ventana del lote no hay ninguna. |

## Qué va a PD1 (para Nicolás y la coordinadora)

- **Caja de VIIRS 375 para el paquete (V375-E): C13**, centrada en el cráter de `volcanoes.yaml`. Alternativa
  equivalente en este lote: C13 sólo en Cordón Caulle y Tupungatito y M14 en el resto (el compuesto). Las dos dan lo
  mismo en los otros nueve volcanes, donde el cráter está a 2,1 km o menos del centro del TIF.
- **V375-D**: no se abre.
- **V375-B**: NO RESUELTO por la regla; con la sensibilidad del censo, a favor del silencio. Si se quiere resolverlo,
  la salida honesta es otra muestra de neg_resto nueva, no reinterpretar ésta.
- **Lo que falta para V375-E**: la vía de proceso en `pipeline/` (PD3), el evaluador común con d′ (#905) y V375-A
  (#903) para las 6 protegidas sólo OCR.
