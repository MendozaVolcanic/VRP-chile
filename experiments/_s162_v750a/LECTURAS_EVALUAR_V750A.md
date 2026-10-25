# Lecturas tomadas por `evaluar_v750a.py` (S162)

Donde `PREREGISTRO_V750A.md` deja algo abierto, el analizador implementa la lectura más directa y la anota aquí. No se
construyeron las otras. Cada lectura se confirma o se corrige al sellar el pre-registro (DN-4); si se corrige, cambia
el analizador y su prueba en el mismo commit.

| id | dónde | lo que dice el pre-registro | lectura implementada | prueba que la fija |
|---|---|---|---|---|
| L1 | §6.2 y §6.3, P1 | «ninguna protegida que K publica y P no; ninguna protegida de MIROVA que P no publique, fuera de las que K tampoco publica, que se listan» | P1 = protegidas que K publica y P no. Las que ni K ni P publican se listan por nombre y no vetan. Lo mismo en la sombra. | E01, E02, E19 |
| L2 | §6.1 | «5 de 5 mutaciones atrapadas por aserción», pero el §4.1 y `equivalencia_v750a.py` tienen seis | Se exige la salida de la prueba local contra el módulo real con una línea `VERDE:`, ninguna `ROJA`, `mutaciones: TODAS COMO SE ESPERA`, al menos 5 líneas «atrapada por aserción» y el control `control_que_se_cae` como «caída». Sin el archivo, §6.1 no se cumple (SIN DATO). | E10, E11 |
| L3 | §6.2 y §6.3, P2 | censo: «GANA o EMPATE (no PIERDE ni BLOQUEA)»; sombra: «si hay sustrato, P2 no PIERDE» | Censo: pasa sólo GANA o EMPATE; SIN SUSTRATO y BLOQUEA no pasan. Sombra: sólo PIERDE falla; BLOQUEA pasa; SIN SUSTRATO (4 bloques o menos) deja sólo el veto de P1. | E03, E05, E24, E20, E21, E23 |
| L4 | §5, M | «razón brazo/MIROVA en las alertas que publican los dos» | Pares del comparador: alertas que deciden (protegidas y bajas) publicadas por K **y** por P, con VRP de K, de P y de MIROVA mayores que 0. Razón de la regla: protegidas publicadas por P (sin exigir K) con VRP de MIROVA, mediana dentro de [0,9; 1,1] con los bordes incluidos. El VRP de MIROVA es `mirova_vrp` de los objetivos en los dos canales. | E06, E07 |
| L5 | §6.2, «el comparador separa a P de K×1,2» | sin estrato ni modo | Un estrato por ventana (T, O) y canal (tabla, todo), modo «decide», calibración simétrica, `decidir_estrato` de `evaluar_d25.py` con el comparador: M cumple si da MEJORA (d MEJORA, d′ MEJORA calibrado y con dos volcanes). El placebo (d = K × 1,2 sobre los mismos pares) por la misma función con el comparador NO puede dar MEJORA en ninguna ventana y canal (control de §7). Menos de 5 pares o de 3 noches: SIN SUSTRATO (el piso de `evaluar_m`), que no es MEJORA. Los tramos de cenit informan y no deciden. | E07 (y la compuerta con el comparador apagado) |
| L6 | §7, control positivo de la ROI | «P-def pierde al menos una protegida de Cordón Caulle» | Protegidas de Cordón Caulle (canal que decide, T y O juntas) que **P publica** y P-def no: 1 o más. Sin la condición sobre P, un oráculo muerto pasaría el control. | E12 |
| L7 | §3 y §7, placebo | K×1,2 es un brazo del run | Se arma en el analizador desde el record de K (VRP de K por 1,2, el resto igual), como `evaluar_d25.py`; el brazo del run no se lee. Control de publicación: el record de K×1,2 por node publica igual que K en cada pasada. | (por construcción; ver «controles sin escenario» abajo) |
| L8 | §7, nulo | «K contra K da P2 EMPATE o SIN SUSTRATO y M sin separación» | P2 del gemelo contra K (T y O juntas, canal que decide) EMPATE o SIN SUSTRATO, y M de K contra el gemelo NEUTRO o SIN SUSTRATO. | E13 |
| L9 | §4.3, sombra | «se mide con las mismas métricas» | `--fase sombra`: brazos K y P (el record del perfil sombra en `brazos.P.record`); controles que aplican: cobertura, nulo del contador y K = producción; los que necesitan P-def, O, gemelo o placebo no aplican. Canales tabla y todo sobre todas las pasadas. | E18 a E21, E23 |
| L10 | §6, «si 2 falla sólo en P2 por la ventana O y no por la T, se informa por canal antes de decidir» | sin forma del veredicto | Si todas las fallas del censo son de P2 y de la ventana O, el veredicto es «INFORMAR POR CANAL ANTES DE DECIDIR», no «NO CUMPLE». | E04, E03 |
| L11 | §3, P-sinfiltro | «P publicando todo lo que detecta, sin el predicado de distancia» | El record de P con `distance_class = summit` y la distancia del centroide en 0, por el mismo predicado (el resto de sus condiciones se conserva). Informa (P2 contra P). | E00 |
| L12 | §5, S-1 | (a), (b), (c) sin definir la celda decisiva ni el umbral que se compara | El productor del artefacto entrega la celda decisiva del cráter (pase, zona, contraste NTI y ETI) y los umbrales de cada pase. El umbral de la celda es u1 en las zonas 0 y 1 y u2 en la zona 2 (`.m` l. 389-399). «Decidida por la escena»: con la celda quieta, pasar al umbral del otro brazo cambia su alerta (los dos tests a la vez), en cualquiera de las dos direcciones. Pares (P, P-def), (P, O), (P-def, O) sobre todas las pasadas observadas. En la equivalencia (P contra O) la marca se aplica a toda diferencia de máscara o VRP, cambie o no la publicación, y bloquea igual. Diagnóstico ausente: SIN DATO, se lista y no cierra la compuerta. | E00 |
| L13 | §4.1 en el runner | «máscara idéntica y VRP a 1e-6 MW» | Máscara = conjunto de (fila, columna) de los alertados; VRP con diferencia absoluta de 1e-6 MW o menos; sobre todas las pasadas observadas (antes de sacar las de K distinto de producción). La banda de triangulación la marca el artefacto (`banda_triangulacion`). | E08, E09 |
| L14 | §4.2, cobertura | (hereda V750-B) | Una pasada «ok» a la que le falta un brazo requerido es SIN DATO con motivo `falta_brazo` y cuenta en la cobertura. | E17 |
| L15 | §6 y §7, orden | P = O es control (§7) y criterio (§6.1) | Orden: controles y cobertura (salida 3) → §6.1 (salida 6, el censo no se mira) → §6.2 → veredicto. | E08, E12 |
| L16 | §4.2, ventanas | T y O | T = hora UTC anterior al 2026-06-13 (`FRONTERA_OCR` de V750-B), O = desde esa fecha. Los días excluidos y el corte del 2026-11-02 12:59 los aplica el generador de objetivos, como en V750-B. | (todas) |
| L17 | §6, adopción | censo y sombra | El veredicto del censo dice «falta la sombra»; el analizador no combina las dos fases: la propuesta a Nicolás necesita las dos líneas CUMPLE. | E00, E18 |

## Controles sin escenario que los haga caer (dicho en voz alta, A116)

- **Placebo, publicación**: con el predicado del tablero de hoy, multiplicar el VRP por 1,2 no cambia ninguna
  publicación (el predicado sólo mira VRP > 0), así que ningún escenario sintético con el analizador correcto lo hace
  caer. Vigila el predicado, no el analizador.
- **Placebo, M con el comparador**: d′ es 0 por construcción para una ganancia pareja, así que con el analizador correcto
  nunca da MEJORA. Cae sólo si se rompe el comparador, y entonces cierra la compuerta en todos los escenarios (la
  mutación M6 del medidor lo muestra).
