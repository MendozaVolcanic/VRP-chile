# Cuarta adenda al pre-registro de D25 sobre K: P2 se calibra como M

**SELLADA por Nicolás el 2026-10-22 (D-42).** Respuesta textual, registrada por la sesión dueña del loop (S160
nocturna), a la propuesta de calibrar P2 como M: «Sí a D-42 opción (a): calibra P2 como M en una cuarta adenda sellada,
con los candados de V34-03 y V29-01 y verificador limpio antes del tag.» Escrita **antes** de leer el veredicto de V1,
V2a y V2b, que siguen sin leer, y antes de abrir el brazo de sensibilidad del 17 al 19 de octubre (D-35, run
39756261926). Todo lo que esta adenda no toca rige como está en `PREREGISTRO.md`, `ADENDA_CALIBRACION.md` (D-27),
`ADENDA_PLACEBO.md` (D-28, D-30, D-32), `ADENDA_GEMELO.md` (D-34) y la exclusión de días de D-29.

## 1. Qué falla

`ADENDA_GEMELO.md` §5 decide P2 con un intervalo bootstrap al 95 % por bloques noche-volcán, pero sin calibración. El
verificador con contexto limpio de D-34 (`experiments/_s159/instrumentos/verificador_d34/INFORME.md`, V34-01, commit
`786bfb288`) midió con la función real sobre datos sintéticos (n = 2.000 por escenario) cuánto decide en falso esa regla
cuando no hay efecto: con 3 noches discordantes de signo común por noche, **24,8 %**; con 4, 13,0 %; con 5, 6,5 %; con
8, 7,0 %; con 12, 4,0 %; con un nulo sin correlación, 6,5 a 8,7 %. El mecanismo: con pocas noches, todas del mismo lado
con probabilidad 2^(1−B), ningún remuestreo de bloques puede cruzar 0. La auditoría S160 llegó a lo mismo por otro
camino (`docs/AUDIT_S160.md` §5.2, V1a-01, rama `s160-auditoria`: con tolerancia 0, P2 aprueba un placebo que apaga al
azar el 1 % de las publicaciones). M no tiene ese problema porque su regla se calibra sobre sus propios pares y queda
INDECIDIBLE si la calibración falla (D-27).

## 2. La regla nueva: calibración de P2

Se agrega a `ADENDA_GEMELO.md` §5, por sensor, después del SIN SUSTRATO (§5.6) y sólo con los controles generales OK:

1. **El nulo**: sobre las mismas contribuciones de P2 (cada pasada discordante con +1 si el error es sólo de D y −1 si
   es sólo de K), se sortea al azar el signo de cada **bloque noche-volcán** entero: todas las contribuciones de un
   bloque se multiplican por el mismo +1 o −1. POR QUÉ: bajo el nulo, D y K son intercambiables dentro de una noche, y
   cambiar los brazos de una noche invierte todas sus contribuciones a la vez. Es el mismo sorteo por bloque que calibra
   M (D-27, `calibrar_simetrico`), aplicado al neto de P2.
2. **La réplica**: a cada sorteo se le aplica la misma regla de `ADENDA_GEMELO.md` §5.3 y §5.4 (el intervalo por
   bloques con `pesos_bloque`, 10.000 remuestreos y semilla 157, y GANA o PIERDE según el lado del intervalo).
3. **El número**: **1.000 sorteos** con semilla fija **161** (`SEMILLA + 4`), como D-32 fijó 1.000 para d′.
4. **El tope**: falsos GANA **5 % o menos** y falsos PIERDE **5 % o menos**, cada cola por separado (tope 50 de 1.000
   por cola), como las colas de M en los estratos que deciden (D-27 §2).
5. **Si falla**: P2 de ese sensor queda **INDECIDIBLE**, sea cual sea su resultado sin calibrar, que se informa al lado.
   Como hoy con un M INDECIDIBLE, la ventana queda INDECIDIBLE (`global_ventana`), salvo un VETADO de P1, que manda antes.
   Un PIERDE sin calibrar tampoco cuenta: con la calibración fallida no se distingue de un nulo.
6. **BLOQUEA no se calibra**: Nicolás eligió la variante en D-34 a sabiendas de su costo, y el verificador midió que
   bajo el nulo bloquea CUMPLE en 37 a 48 % de los conjuntos (V34-02). Con la calibración OK, BLOQUEA sigue como está;
   la fracción de sorteos que dan BLOQUEA se informa y no decide.
7. **Se informa siempre**, en el detalle de P2 del JSON: falsos GANA, falsos PIERDE y falsos BLOQUEA de la calibración,
   el número de sorteos, la semilla, si quedó calibrada y el resultado sin calibrar.

## 3. Los candados (antes del tag de lectura)

- **V34-03**: las siete mutaciones que hoy pasan en verde tienen que fallar por aserción: semilla del intervalo de P2,
  número de remuestreos, nivel del 95 %, borde de PIERDE (`lo >= 0` en vez de `lo > 0`), tope del 5 % de d′ en la
  comparación, INDECIDIBLE por d′ sin que d dé MEJORA, y la marca «NO VALE PARA DECIDIR» en el estado de la ventana.
- **V29-01**: las cinco mutaciones de D-29 que hoy pasan tienen que fallar por aserción, con un caso de punta a punta
  sobre brazos sintéticos (como `experiments/_s159/instrumentos/verificador_d29/cobertura_sintetica.py`): filtro de los
  crudos descartado, días vacíos en la tabla, días vacíos en la cobertura, fecha en hora de Chile y cabecera de V1
  callada.
- **La calibración nueva**: mutaciones de su semilla, de su número de sorteos, de su tope, de una cola sola en vez de
  las dos, del sorteo por pasada en vez de por bloque, y de un fallo que no deja INDECIDIBLE.
- Cada mutación cuenta como atrapada sólo si alguna prueba falla por aserción y ninguna por otra excepción (S156),
  leyendo el tipo de falla del XML de JUnit, con una copia sin mutar como control.

## 4. Lo que esta adenda no toca

- La regla de P2 de `ADENDA_GEMELO.md` §5 (unidad, signo, intervalo, BLOQUEA, SIN SUSTRATO, lista e informes), salvo
  agregarle la calibración.
- P1, P1b, M y su comparador, P4 y P5, y la exclusión de días de D-29.
- El brazo de sensibilidad del 17 al 19 de octubre (D-35) se evalúa aparte con la misma regla y no entra al veredicto.

## 5. Lo que se mide antes del tag, sin datos reales

Con datos sintéticos, y declarado en el informe del verificador: la tasa de falsos de P2 calibrada en los escenarios de
V34-01 (tiene que quedar en 5 % o menos por cola en todos, o salir INDECIDIBLE), y su poder en los escenarios de efecto
del mismo informe (efecto grande a favor y en contra, moderado, por noche). Una regla que nunca decide también es un
defecto: si el poder cae a casi 0 en el efecto grande, se dice antes del tag.
